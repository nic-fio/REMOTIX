//! Il palco: cattura e controllo restano montati anche quando non guarda nessuno.
//!
//! # Il difetto che questo modulo esiste per togliere
//!
//! Fino alla fase 4 la coppia cattura+controllo apparteneva alla **connessione**:
//! nasceva con lei e moriva con lei. Alla disconnessione Mutter scriveva
//! `Removed virtual monitor Meta-0` e restava **con zero schermi**, e da lì:
//!
//! ```text
//! meta_monitor_manager_get_logical_monitor_from_number: assertion failed
//! meta_workspace_get_work_area_for_monitor: assertion 'logical_monitor != NULL' failed
//! ```
//!
//! Le applicazioni aperte perdono il riferimento al monitor, quelle nuove non
//! hanno dove aprirsi, e alla riconnessione — soprattutto se il client chiede
//! una misura diversa dalla precedente — la sessione si ritrova con la
//! geometria calcolata su uno schermo che non esiste più. È la questione aperta
//! n.5 di `SPECIFICA.md`, colta sul fatto il 3 agosto: un desktop che copriva il
//! 75% dello schermo, cioè esattamente il rapporto fra la misura vecchia e
//! quella nuova.
//!
//! # La regola
//!
//! **Il monitor virtuale esiste finché esiste la sessione grafica, non finché
//! dura una connessione.** Chi si collega trova un palco già montato; chi se ne
//! va non lo smonta.
//!
//! # Perché si può fare senza sprecare nulla
//!
//! Perché la cattura, quando nessuno legge i fotogrammi, non blocca niente: il
//! thread di PipeWire li consegna con `try_send` su un canale da due posti e,
//! trovandolo pieno, li scarta. Su un desktop fermo — che è il caso normale
//! quando non c'è nessuno collegato — Mutter non ne manda affatto (§5.6).
//!
//! # Cosa resta della vecchia sequenza
//!
//! I quattro passi di §5.8 non cambiano di una virgola: il controllo si crea per
//! primo e si avvia per terzo, perché Mutter registra la cattura solo su un
//! controllo non ancora partito. Cambia **quando** si eseguono: non più a ogni
//! connessione, ma solo quando il palco non c'è o è della misura sbagliata.

use core::time::Duration;
use std::sync::Arc;

use anyhow::{Context as _, Result};
use ironrdp_server::DesktopSize;
use tokio::sync::Mutex;
use tracing::{debug, info};

use crate::cattura::{Cattura, Fotogramma};
use crate::controllo::Controllo;
use crate::screencast::{Cursore, SessioneCattura};

/// Quanto si aspetta un fotogramma prima di lasciar perdere per quel giro.
///
/// Serve solo a non restare appesi per sempre su un desktop immobile: chi
/// chiama deve poter tornare al proprio ciclo e riprovare.
const ATTESA_FOTOGRAMMA: Duration = Duration::from_millis(250);

/// Quanto silenzio basta per dire che il desktop ha finito di ridisegnarsi.
const QUIETE_RIDISEGNO: Duration = Duration::from_millis(300);

/// Quanti fotogrammi servono prima di fidarsi del silenzio.
///
/// **Misurato**, non supposto: catturando in PNG fuori da RDP si vede che dopo
/// un cambio di misura Mutter ne manda due — il primo con il solo colore di
/// fondo, senza sfondo ne' finestre, il secondo completo. Fermarsi al primo
/// silenzio significa spedire quello vuoto, e su un desktop fermo resta li'.
const FOTOGRAMMI_PRIMA_DI_FIDARSI: u32 = 2;

/// E quanto si e' disposti ad aspettare in tutto, perche' un desktop che cambia
/// di continuo non tenga fermo il primo fotogramma all'infinito.
const ATTESA_RIDISEGNO: Duration = Duration::from_millis(2500);

/// Cosa e' arrivato dal palco.
pub enum Arrivo {
    /// Un fotogramma da disegnare.
    Fotogramma(Fotogramma),
    /// Niente per ora: il desktop e' fermo, ed e' la condizione normale.
    Niente,
    /// La cattura si e' chiusa. O la sessione grafica e' terminata — un «Esci»
    /// dal menu di sistema — oppure Mutter l'ha fermata per conto suo. In
    /// entrambi i casi non basta aspettare: bisogna decidere che farne.
    Finita,
}

pub struct Palco {
    interno: Mutex<Interno>,
}

#[derive(Default)]
struct Interno {
    /// Va tenuta viva: se cade, Mutter chiude la sessione di cattura e con essa
    /// il monitor virtuale.
    sessione: Option<SessioneCattura>,
    /// Va tenuta viva: se cade, il ciclo di PipeWire si ferma.
    cattura: Option<Cattura>,
    fotogrammi: Option<tokio::sync::mpsc::Receiver<Fotogramma>>,
    /// La misura del palco attualmente montato.
    misura: Option<DesktopSize>,
}

impl Palco {
    pub fn nuovo() -> Arc<Self> {
        Arc::new(Self {
            interno: Mutex::new(Interno::default()),
        })
    }

    /// Assicura che esista una cattura della misura chiesta.
    ///
    /// Se il palco è già montato della misura giusta **non tocca nulla**: è il
    /// caso del client che si riaggancia, e non rifacendo la coppia il desktop
    /// ricompare all'istante, con le finestre dov'erano.
    ///
    /// Restituisce `true` se il palco è stato rimontato, `false` se si è
    /// riusato quello che c'era.
    pub async fn assicura(&self, size: DesktopSize, controllo: &Controllo) -> Result<bool> {
        let mut interno = self.interno.lock().await;

        if interno.misura == Some(size) && interno.sessione.is_some() && controllo.attivo() {
            debug!(
                larghezza = size.width,
                altezza = size.height,
                "palco gia' montato della misura giusta: si riusa"
            );
            return Ok(false);
        }

        // Si smonta prima la coppia vecchia: due monitor virtuali insieme
        // farebbero credere a GNOME di avere due schermi — che è precisamente
        // l'aspetto del difetto segnalato — e il controllo vecchio resterebbe
        // legato a un flusso che non esiste più.
        interno.cattura = None;
        interno.fotogrammi = None;
        interno.misura = None;
        controllo.stacca();
        if let Some(vecchia) = interno.sessione.take() {
            vecchia.chiudi().await;
        }

        // 1. il controllo, creato e **non** avviato
        let pronta = controllo.prepara().await;

        // 2. e 3. la cattura, che si registra su di esso e lo fa partire
        let contesto = pronta.as_ref().map(|p| p.contesto());
        // Il puntatore non va disegnato dentro l'immagine: come metadato il
        // video cambia solo quando cambia il desktop, e il puntatore lo muove
        // il client senza aspettare un giro sulla rete.
        let sessione = SessioneCattura::virtuale(Cursore::Metadato, contesto.as_ref())
            .await
            .context("apertura della sessione di cattura")?;
        let (cattura, fotogrammi) = Cattura::avvia(
            sessione.nodo,
            Some((u32::from(size.width), u32::from(size.height))),
        )
        .await?;

        info!(
            larghezza = size.width,
            altezza = size.height,
            controllo = pronta.is_some(),
            "palco montato: cattura del desktop avviata"
        );

        // 4. il controllo riceve il flusso su cui muovere il puntatore
        if let Some(pronta) = pronta {
            controllo.attiva(pronta, sessione.percorso_flusso.clone(), size);
        }

        interno.sessione = Some(sessione);
        interno.cattura = Some(cattura);
        interno.fotogrammi = Some(fotogrammi);
        interno.misura = Some(size);
        Ok(true)
    }

    /// Il prossimo fotogramma, se ne arriva uno entro un quarto di secondo.
    ///
    /// L'attesa limitata non è pigrizia: su un desktop fermo Mutter non manda
    /// nulla (§5.6), e chi chiama deve poter tornare al proprio ciclo — dove
    /// aspettano il ridimensionamento, il ripiego e il rinvio della misura.
    ///
    /// # Sicurezza rispetto all'annullamento
    ///
    /// Annullare questa attesa non perde fotogrammi: quello eventualmente
    /// pronto resta nel canale, che è il posto da cui si legge la volta dopo.
    pub async fn prossimo(&self) -> Arrivo {
        let mut interno = self.interno.lock().await;
        let Some(canale) = interno.fotogrammi.as_mut() else {
            return Arrivo::Finita;
        };
        let mut fotogramma = match tokio::time::timeout(ATTESA_FOTOGRAMMA, canale.recv()).await {
            Ok(Some(fotogramma)) => fotogramma,
            // **I due casi non vanno confusi**, e confonderli e' costato il
            // difetto del logout: il canale chiuso vuol dire che la cattura e'
            // finita — la sessione grafica non c'e' piu' — mentre il timeout
            // vuol dire soltanto che il desktop e' fermo, che e' la condizione
            // normale (§5.6). Trattandoli allo stesso modo, chi usciva dal menu
            // di sistema restava con il client appeso su un'immagine congelata,
            // e nel registro non compariva nulla.
            Ok(None) => return Arrivo::Finita,
            Err(_) => return Arrivo::Niente,
        };

        // Si tiene solo l'ultimo arrivato.
        //
        // Il canale ha profondita' due, e chi cattura non puo' togliere dalla
        // coda: quando la trova piena butta il fotogramma **nuovo** e conserva i
        // vecchi, che e' l'opposto di quel che serve. Svuotandola qui, la
        // profondita' torna a essere una rete di sicurezza invece che ritardo
        // accumulato.
        let mut scartati = 0u32;
        while let Ok(piu_recente) = canale.try_recv() {
            fotogramma = piu_recente;
            scartati += 1;
        }
        if scartati > 0 {
            debug!(scartati, "fotogrammi sorpassati, si disegna il piu' recente");
        }
        Arrivo::Fotogramma(fotogramma)
    }

    /// Aspetta che il desktop **si sia ridisegnato** alla misura nuova.
    ///
    /// Serve dopo un rimontaggio, ed e' il difetto dello «sfondo grigio a
    /// destra»: quando il monitor virtuale cambia misura, Mutter manda un
    /// fotogramma **subito**, prima che GNOME abbia ridisegnato — quindi con lo
    /// sfondo della misura vecchia e il resto vuoto. Siccome su un desktop
    /// fermo non ne arrivano altri (§5.6), quell'immagine parziale resta finche'
    /// l'utente non tocca qualcosa: alla prima connessione si vede sbagliata,
    /// alla seconda giusta.
    ///
    /// Si raccolgono quindi i fotogrammi finche' non smettono di arrivare, e si
    /// tiene l'ultimo: quando il ridisegno e' finito, il silenzio torna.
    pub async fn stabilizza(&self) -> Option<Fotogramma> {
        let scadenza = tokio::time::Instant::now() + ATTESA_RIDISEGNO;
        let mut ultimo = None;
        let mut raccolti = 0u32;

        let mut interno = self.interno.lock().await;
        let canale = interno.fotogrammi.as_mut()?;
        while tokio::time::Instant::now() < scadenza {
            match tokio::time::timeout(QUIETE_RIDISEGNO, canale.recv()).await {
                Ok(Some(fotogramma)) => {
                    ultimo = Some(fotogramma);
                    raccolti += 1;
                }
                // La cattura e' caduta: non ne arriveranno altri.
                Ok(None) => break,
                // Silenzio. Ci si ferma solo se ne sono gia' arrivati
                // abbastanza da poterci credere: il primo fotogramma dopo un
                // cambio di misura e' quello **vuoto**, e il silenzio fra lui e
                // quello buono e' proprio dove cadeva la versione precedente.
                Err(_) if raccolti >= FOTOGRAMMI_PRIMA_DI_FIDARSI => break,
                Err(_) => continue,
            }
        }
        if raccolti > 0 {
            debug!(raccolti, "atteso il ridisegno alla misura nuova");
        }
        ultimo
    }

    /// Butta i fotogrammi rimasti in coda da prima.
    ///
    /// Serve a chi si collega: fra una connessione e l'altra il palco resta
    /// acceso, e nel canale possono essere fermi fotogrammi di minuti fa. Il
    /// **più recente** però va tenuto, perché su un desktop immobile è l'unica
    /// immagine che si avrà per un tempo indeterminato (§5.7 regola 3).
    pub async fn scarta_arretrati(&self) -> Option<Fotogramma> {
        let mut interno = self.interno.lock().await;
        let canale = interno.fotogrammi.as_mut()?;
        let mut ultimo = None;
        while let Ok(fotogramma) = canale.try_recv() {
            ultimo = Some(fotogramma);
        }
        ultimo
    }

    /// Smonta il palco. Si usa allo spegnimento, non alla disconnessione.
    pub async fn smonta(&self, controllo: &Controllo) {
        let mut interno = self.interno.lock().await;
        interno.cattura = None;
        interno.fotogrammi = None;
        interno.misura = None;
        controllo.stacca();
        if let Some(sessione) = interno.sessione.take() {
            sessione.chiudi().await;
        }
        info!("palco smontato");
    }
}
