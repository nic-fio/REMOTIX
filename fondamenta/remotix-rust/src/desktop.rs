//! Il desktop vero, catturato e spedito al client.
//!
//! Unisce le due metà costruite finora: la cattura da PipeWire (fase 2) e la
//! pipeline EGFX con codifica H.264 (fase 1).
//!
//! # Come si incastra con il ridimensionamento
//!
//! La risoluzione la decide il client: quella che propone alla connessione
//! diventa la dimensione del monitor virtuale che chiediamo a Mutter. Quando il
//! client la cambia, la cattura va **rifatta da capo** — sessione compresa —
//! perché la dimensione del monitor virtuale si concorda una volta sola, nella
//! negoziazione PipeWire.
//!
//! Rifare tutto costa un istante di nero, ed è il motivo per cui non lo si fa a
//! ogni singolo evento: il client ne manda a raffica mentre si trascina il
//! bordo della finestra.

use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

use anyhow::Result;
use ironrdp_server::{
    DesktopSize, DisplayUpdate, RdpServerDisplay, RdpServerDisplayUpdates,
};
use tokio::sync::watch;
use tracing::{debug, info, warn};

use crate::controllo::Controllo;
use crate::egfx::{RegistroGfx, StatoGfx};
use crate::h264;
use crate::palco::{Arrivo, Palco};
use crate::autenticazione::Guardia;
use crate::sessione;

/// Sorgente che mostra il desktop della sessione grafica locale.
pub struct Desktop {
    size: watch::Sender<DesktopSize>,
    rx: watch::Receiver<DesktopSize>,
    registro: Arc<RegistroGfx>,
    /// L'input. Va interpellato **prima** di aprire la cattura: e' da li' che
    /// esce l'identificativo con cui le due sessioni si riconoscono.
    controllo: Arc<Controllo>,
    /// Stato grafico su cui disegnava la sorgente precedente.
    ///
    /// Serve a distinguere due situazioni che dall'esterno si somigliano: una
    /// **connessione nuova**, che porta con se' uno stato nuovo, e una
    /// **riattivazione** della stessa connessione, che riusa lo stato di prima
    /// dopo che il client ha azzerato il proprio. Solo nel secondo caso
    /// bisogna dimenticare quello che si credeva di sapere.
    stato_precedente: Option<Arc<StatoGfx>>,
    /// Numero d'ordine dell'ultima cattura aperta.
    ///
    /// Serve perche' **la pipeline grafica e' una sola** mentre le connessioni
    /// possono sovrapporsi: alcuni client — fra questi quello Android — ne
    /// aprono una seconda prima di chiudere la prima.
    ///
    /// Se due catture restano attive insieme, due codificatori H.264
    /// indipendenti, ciascuno con i propri fotogrammi chiave, scrivono sulla
    /// stessa superficie. Il decodificatore del client riceve due flussi
    /// mescolati e non ricostruisce nulla: schermo nero. Chi resta indietro di
    /// numero si fa da parte.
    generazione: Arc<AtomicU64>,
    /// Il palco, condiviso con tutte le connessioni: vedere `palco.rs`.
    palco: Arc<Palco>,
    /// Come si avvia la sessione grafica, quando non ce n'e' una.
    comando_sessione: String,
    /// La disposizione di tastiera da imporre alla sessione, se dichiarata.
    ///
    /// `None` significa «non toccare le impostazioni dell'utente», ed e' il
    /// comportamento predefinito: vedere `sessione::disposizione`.
    disposizione: Option<String>,
    /// Chi ha superato PAM. Senza, non si consegna alcun desktop.
    guardia: Arc<Guardia>,
}

impl Desktop {
    pub fn nuovo(
        size: watch::Sender<DesktopSize>,
        rx: watch::Receiver<DesktopSize>,
        registro: Arc<RegistroGfx>,
        controllo: Arc<Controllo>,
        palco: Arc<Palco>,
        comando_sessione: String,
        disposizione: Option<String>,
        guardia: Arc<Guardia>,
    ) -> Self {
        Self {
            size,
            rx,
            registro,
            controllo,
            stato_precedente: None,
            generazione: Arc::new(AtomicU64::new(0)),
            palco,
            comando_sessione,
            disposizione,
            guardia,
        }
    }
}

#[async_trait::async_trait]
impl RdpServerDisplay for Desktop {
    async fn size(&mut self) -> DesktopSize {
        *self.size.borrow()
    }

    /// Si accetta la dimensione proposta dal client: sarà quella del monitor
    /// virtuale che Mutter creerà per noi.
    async fn request_initial_size(&mut self, client_size: DesktopSize) -> DesktopSize {
        if client_size.width > 0 && client_size.height > 0 {
            info!(
                larghezza = client_size.width,
                altezza = client_size.height,
                "dimensione proposta dal client, accettata"
            );
            let _ = self.size.send(client_size);
        }
        *self.size.borrow()
    }

    fn request_layout(&mut self, layout: ironrdp_displaycontrol::pdu::DisplayControlMonitorLayout) {
        // Si registra **tutto** quello che il client dichiara, non solo cio' che
        // usiamo. Di questo messaggio finora leggevamo la sola misura, e la
        // posizione, la scala e il numero di monitor le buttavamo via senza
        // nemmeno saperlo: se un client si comporta in modo che non torna, il
        // primo posto dove guardare e' cosa aveva chiesto davvero.
        for (indice, m) in layout.monitors().iter().enumerate() {
            let (w, h) = m.dimensions();
            info!(
                indice,
                di = layout.monitors().len(),
                larghezza = w,
                altezza = h,
                posizione = ?m.position(),
                primario = m.is_primary(),
                scala_desktop = ?m.desktop_scale_factor(),
                scala_dispositivo = ?m.device_scale_factor(),
                misure_fisiche = ?m.physical_dimensions(),
                orientamento = ?m.orientation(),
                "il client dichiara uno schermo"
            );
        }

        // I casi che non sappiamo trattare vanno detti, non subiti in silenzio:
        // sono le prime cose da escludere quando l'immagine finisce dove non
        // deve. Con piu' schermi prendiamo solo il primario (il multi-monitor e'
        // fuori scope, §3.1); una scala diversa da 100 la ignoriamo, e il client
        // potrebbe disegnare a una misura diversa da quella che gli mandiamo.
        if layout.monitors().len() > 1 {
            warn!(
                monitor = layout.monitors().len(),
                "il client dichiara piu' schermi: si usa solo il primario"
            );
        }

        let Some(monitor) = layout
            .monitors()
            .iter()
            .find(|m| m.is_primary())
            .or_else(|| layout.monitors().first())
        else {
            return;
        };

        if let Some(scala) = monitor.desktop_scale_factor().filter(|s| *s != 100) {
            warn!(scala, "il client dichiara una scala del desktop diversa da 100, ignorata");
        }
        if let Some((sinistra, alto)) = monitor.position().filter(|p| *p != (0, 0)) {
            warn!(sinistra, alto, "il monitor primario del client non e' all'origine");
        }

        let (w, h) = monitor.dimensions();
        let (Ok(width), Ok(height)) = (u16::try_from(w), u16::try_from(h)) else {
            return;
        };
        if width == 0 || height == 0 {
            return;
        }
        let nuova = DesktopSize { width, height };
        if nuova != *self.size.borrow() {
            info!(larghezza = width, altezza = height, "il client chiede un ridimensionamento");
            let _ = self.size.send(nuova);
        }
    }

    async fn updates(&mut self) -> Result<Box<dyn RdpServerDisplayUpdates>> {
        // Prima ancora: che chi chiede il desktop si sia autenticato.
        //
        // Non e' una ridondanza del validatore PAM: IronRDP lo interpella solo
        // se il client ha mandato delle credenziali, e chi non ne manda
        // affatto arriva fin qui senza che PAM sia mai stato chiamato. Rifiutare
        // qui chiude la connessione prima che si veda un solo pixel.
        if !self.guardia.concesso() {
            warn!("richiesta di desktop senza autenticazione: connessione rifiutata");
            anyhow::bail!("connessione non autenticata");
        }

        // Poi: che ci sia un desktop da mostrare.
        //
        // Dopo un «Esci» la sessione non c'e' piu', ed e' giusto cosi': la si
        // riavvia adesso, che e' il momento in cui qualcuno la vuole. Senza,
        // chi si collega trova il server in ascolto e lo schermo vuoto, senza
        // che nulla spieghi perche' — il difetto segnalato il 3 agosto.
        match sessione::assicura(&self.comando_sessione).await {
            Ok(true) => info!("sessione grafica avviata per questa connessione"),
            Ok(false) => {}
            // Si prosegue lo stesso: se il compositore c'e' ma ha risposto
            // tardi, la cattura potrebbe riuscire comunque, e un errore qui
            // negherebbe l'accesso a un desktop magari funzionante.
            Err(errore) => warn!(errore = %format!("{errore:#}"), "avvio della sessione grafica fallito"),
        }

        // E che la tastiera scriva le lettere che il client si aspetta. Va qui,
        // a sessione viva e prima del primo fotogramma: la si vuole a posto
        // dalla prima battuta, non dalla seconda connessione.
        if let Some(voluta) = &self.disposizione {
            match sessione::disposizione(voluta).await {
                Ok(_) => {}
                // Non e' motivo per negare il desktop: una disposizione
                // sbagliata rende scomodo scrivere, non impossibile — e chi si
                // collega magari voleva solo guardare qualcosa.
                Err(errore) => warn!(
                    errore = %format!("{errore:#}"),
                    "disposizione della tastiera non impostata"
                ),
            }
        }

        let mut rx = self.rx.clone();
        rx.mark_unchanged();
        let size = *rx.borrow();

        let mia = self.generazione.fetch_add(1, Ordering::AcqRel) + 1;

        let gfx = match self.registro.corrente() {
            Some(stato) => stato,
            None => {
                // Non dovrebbe capitare: la connessione grafica si costruisce
                // prima che venga chiesta una sorgente. Se capita si disegna
                // col percorso di ripiego invece di rifiutare la connessione.
                warn!("nessuna connessione grafica registrata: si disegnera' senza EGFX");
                StatoGfx::nuovo()
            }
        };

        // Stesso stato della sorgente precedente significa che la connessione
        // non e' cambiata: siamo dentro una riattivazione, e il client ha
        // buttato via il proprio stato grafico. Va buttato anche il nostro.
        let riattivazione = self
            .stato_precedente
            .as_ref()
            .is_some_and(|prec| Arc::ptr_eq(prec, &gfx));
        if riattivazione {
            gfx.azzera();
        }
        self.stato_precedente = Some(Arc::clone(&gfx));

        info!(generazione = mia, riattivazione, "nuova sorgente per il desktop");

        // Un client che si riaggancia non ha piu' premuto nulla, ma noi
        // potremmo credere il contrario se la connessione precedente e' morta
        // male. Si azzera prima di ricominciare.
        self.controllo.rilascia_tutto();

        let mut aggiornamenti = AggiornamentiDesktop {
            rx,
            gfx,
            controllo: Arc::clone(&self.controllo),
            generazione: Arc::clone(&self.generazione),
            mia,
            avvio: Instant::now(),
            codificatore: None,
            serve_chiave: false,
            puntatore_annunciato: false,
            palco: Arc::clone(&self.palco),
            ultimo: None,
            gia_inviato: false,
            ripresa: tokio::time::interval(std::time::Duration::from_millis(250)),
            resize_atteso: None,
            in_invio: None,
            riga: 0,
        };
        aggiornamenti.riavvia_cattura(size).await?;
        Ok(Box::new(aggiornamenti))
    }
}

struct AggiornamentiDesktop {
    rx: watch::Receiver<DesktopSize>,
    gfx: Arc<StatoGfx>,
    controllo: Arc<Controllo>,
    /// Numero d'ordine dell'ultima cattura aperta, condiviso.
    generazione: Arc<AtomicU64>,
    /// Il proprio numero: se non e' piu' l'ultimo, ci si ritira.
    mia: u64,
    avvio: Instant,
    codificatore: Option<h264::Codificatore>,
    /// Vero quando il prossimo fotogramma deve essere un fotogramma chiave.
    ///
    /// Si accende quando si sospetta che il client abbia perso qualcosa e le due
    /// ricostruzioni possano essere divergenti.
    serve_chiave: bool,
    /// Vero dopo aver detto al client di disegnarsi il puntatore da se'.
    ///
    /// Va detto esplicitamente: il puntatore non e' piu' nell'immagine, e senza
    /// istruzioni un client potrebbe non mostrarne alcuno.
    puntatore_annunciato: bool,
    /// Cattura e controllo, che **non** appartengono a questa connessione.
    ///
    /// Restano montati fra una connessione e l'altra: se sparissero, Mutter
    /// resterebbe con zero schermi e la sessione diventerebbe inutilizzabile
    /// dopo il primo stacco. Vedere `palco.rs`.
    palco: Arc<Palco>,
    /// L'ultimo fotogramma ricevuto, gia' pronto da codificare.
    ///
    /// Mutter ne manda uno **solo quando qualcosa cambia**: su un desktop
    /// fermo, dopo i primi istanti, non arriva piu' nulla. Se in quel momento
    /// la pipeline grafica non era ancora stata negoziata, i fotogrammi
    /// arrivati sono stati buttati e il client resta a fissare uno schermo nero
    /// a tempo indeterminato — finche' qualcuno non muove qualcosa sul
    /// desktop. Conservarne una copia permette di disegnare qualcosa appena
    /// c'e' dove disegnarlo.
    ultimo: Option<(DesktopSize, Vec<u8>)>,
    /// Vero quando `ultimo` e' gia' stato spedito al client.
    gia_inviato: bool,
    /// Ricontrolla se ci sia un fotogramma da recuperare.
    ripresa: tokio::time::Interval,
    /// Ridimensionamento chiesto dal client e non ancora applicato.
    ///
    /// Alcuni client lo chiedono **prima di aver negoziato EGFX** — quello
    /// Android lo fa entro un decimo di secondo dalla connessione. Applicarlo
    /// subito costringerebbe alla riattivazione della sessione, dopo la quale
    /// quel client non negozia piu' la pipeline grafica e resta per sempre sul
    /// percorso di ripiego. Rinviandolo di poco, la pipeline fa in tempo a
    /// negoziarsi e la misura nuova passa per la tela grafica.
    resize_atteso: Option<(DesktopSize, Instant)>,
    /// Fotogramma in corso di invio col percorso di ripiego, banda per banda.
    in_invio: Option<ironrdp_server::BitmapUpdate>,
    /// Prima riga non ancora inviata del fotogramma di ripiego.
    riga: u16,
}

/// Dimensione massima di una singola banda del percorso di ripiego.
///
/// Un fotogramma intero non compresso supera il buffer di riassemblaggio
/// dichiarato da alcuni client, che ne ricompongono solo una parte e mostrano
/// l'immagine a riquadri sparsi. Suddividerlo lo rende digeribile da tutti.
const BANDA_MASSIMA_BYTE: usize = 512 * 1024;

impl AggiornamentiDesktop {
    /// Apre — o riapre — la cattura alla dimensione indicata, con il controllo.
    ///
    /// I quattro passi vanno in quest'ordine e non in un altro: Mutter registra
    /// la cattura sulla sessione di controllo **solo finche' questa non e'
    /// partita**, quindi il controllo si crea per primo e si avvia per ultimo.
    /// Il perche' per esteso sta in `controllo.rs`.
    /// Chiede al palco una cattura della misura voluta.
    ///
    /// Il palco la rifà solo se serve: al riaggancio di un client che chiede la
    /// stessa misura non si tocca nulla, e il desktop ricompare com'era. I
    /// quattro passi di §5.8, e il perché del loro ordine, stanno in
    /// `palco.rs`.
    async fn riavvia_cattura(&mut self, size: DesktopSize) -> Result<()> {
        let rimontato = self.palco.assicura(size, &self.controllo).await?;

        // I fotogrammi rimasti in coda da prima non valgono più nulla se il
        // palco è stato rifatto — hanno la misura vecchia — mentre se lo si è
        // riusato il più recente è oro: su un desktop immobile è l'unica
        // immagine che si avrà finché qualcuno non muove qualcosa (§5.7
        // regola 3), e permette di disegnare subito invece di restare neri.
        let recuperato = if rimontato {
            // Il palco e' nuovo: il desktop si sta ridisegnando alla misura
            // appena chiesta, e il primo fotogramma puo' essere ancora quello di
            // prima. Si aspetta che finisca (vedere `Palco::stabilizza`).
            self.palco.stabilizza().await
        } else {
            // Riaggancio: il piu' recente e' oro, su un desktop fermo e' l'unica
            // immagine che si avra' finche' qualcuno non muove qualcosa.
            self.palco.scarta_arretrati().await
        };

        if let Some(fotogramma) = recuperato {
            // **La misura la dichiara il fotogramma, non chi lo ha chiesto.**
            //
            // Etichettarlo con la misura richiesta e' un errore che non da'
            // alcun errore: se il compositore consegna ancora un fotogramma
            // della misura vecchia — 1920 di larghezza — e lo si spedisce come
            // se fosse 2560, il codificatore legge righe piu' corte di quelle
            // dichiarate e il client disegna un'immagine che copre solo la
            // parte sinistra dello schermo. E' esattamente l'aspetto dello
            // «sfondo grigio a destra».
            let (Ok(larghezza), Ok(altezza)) = (
                u16::try_from(fotogramma.larghezza),
                u16::try_from(fotogramma.altezza),
            ) else {
                return Ok(());
            };
            let misura_vera = DesktopSize { width: larghezza, height: altezza };

            if misura_vera == size {
                self.ultimo = Some((misura_vera, fotogramma.dati));
                self.gia_inviato = false;
            } else {
                // Non lo si spedisce: si aspetta il prossimo, che avra' la
                // misura giusta. Un fotogramma in meno costa un istante di
                // attesa; uno sbagliato resta sullo schermo finche' l'utente
                // non muove qualcosa.
                warn!(
                    fotogramma = %format!("{larghezza}x{altezza}"),
                    chiesta = %format!("{}x{}", size.width, size.height),
                    "fotogramma di misura diversa da quella richiesta, scartato"
                );
            }
        }
        Ok(())
    }

    /// Codifica un fotogramma e lo consegna alla pipeline EGFX.
    ///
    /// **Si chiede il permesso prima di codificare, non dopo.** Vedere
    /// `StatoGfx::puo_inviare` per il perché: un fotogramma codificato e poi
    /// scartato lascia il codificatore avanti rispetto al client, e da lì in poi
    /// l'immagine non si ricuce più da sola.
    fn invia(&mut self, size: DesktopSize, bgra: &[u8]) -> Result<bool> {
        if !self.gfx.puo_inviare() {
            debug!("pipeline satura: non si codifica nemmeno");
            return Ok(false);
        }

        let serve_nuovo = match &self.codificatore {
            Some(c) => c.dimensione() != (size.width, size.height),
            None => true,
        };
        if serve_nuovo {
            self.codificatore = Some(h264::Codificatore::nuovo(size.width, size.height)?);
            // Un codificatore nuovo parte gia' da un fotogramma chiave.
            self.serve_chiave = false;
        }
        let codificatore = self.codificatore.as_mut().expect("appena creato");

        if self.serve_chiave {
            debug!("fotogramma chiave per rimettere d'accordo il client");
            codificatore.forza_chiave();
            self.serve_chiave = false;
        }

        let flusso = codificatore.codifica(bgra)?;
        let ms = u32::try_from(self.avvio.elapsed().as_millis()).unwrap_or(u32::MAX);
        let inviato = self.gfx.invia_avc420(size, &flusso, ms)?;

        if !inviato {
            // Il permesso c'era e l'invio e' fallito lo stesso: fra la domanda e
            // la risposta il client puo' aver ripreso a chiedere i riscontri.
            // Succede di rado, ma quando succede il codificatore e' avanti di un
            // fotogramma e va ricucito.
            warn!("fotogramma codificato ma non inviato: il prossimo sara' un fotogramma chiave");
            self.serve_chiave = true;
        }
        Ok(inviato)
    }

    /// Riporta tutto alla nuova misura: superficie, fotogramma, cattura.
    async fn applica_ridimensionamento(&mut self, size: DesktopSize) -> Result<()> {
        self.gfx.invalida_superficie();
        // Il fotogramma conservato ha la vecchia misura: non vale piu' nulla.
        self.ultimo = None;
        self.gia_inviato = false;
        self.in_invio = None;
        self.riga = 0;
        self.riavvia_cattura(size).await
    }

    /// Prepara l'invio del fotogramma conservato col percorso di ripiego.
    ///
    /// Serve ai client che **non hanno ancora negoziato EGFX**. Alcuni — il
    /// client Android fra questi — aprono la connessione, restano in attesa di
    /// un aggiornamento grafico qualsiasi e, non ricevendone, si arrendono
    /// dopo una decina di secondi e riprovano. Senza questo ripiego il primo
    /// tentativo di connessione non produce nulla, e l'utente vede uno schermo
    /// nero per tutta la durata dei tentativi a vuoto.
    fn prepara_ripiego(&mut self) {
        if self.in_invio.is_some() || self.gfx.pronto() {
            return;
        }
        // Con un ridimensionamento in sospeso il fotogramma conservato ha una
        // misura che sta per cambiare: disegnarlo sarebbe fatica sprecata.
        if self.resize_atteso.is_some() {
            return;
        }
        // Si concede al client il tempo di negoziare EGFX prima di ripiegare.
        //
        // Senza questa pausa il ripiego fa in tempo a disegnare qualche banda
        // di pixel grezzi, e l'utente vede comparire una schermata a strisce
        // che solo dopo viene completata da H.264. I client di riferimento
        // negoziano in un decimo di secondo, quindi non incontrano mai il
        // ripiego; chi non negozia affatto lo incontra dopo un secondo, ben
        // prima dei dieci che impiega ad arrendersi.
        if self.avvio.elapsed() < std::time::Duration::from_secs(1) {
            return;
        }
        let Some((size, pixel)) = self.ultimo.as_ref() else {
            return;
        };
        let (Some(width), Some(height)) = (
            core::num::NonZeroU16::new(size.width),
            core::num::NonZeroU16::new(size.height),
        ) else {
            return;
        };
        let Some(stride) = core::num::NonZeroUsize::new(usize::from(size.width) * 4) else {
            return;
        };

        self.in_invio = Some(ironrdp_server::BitmapUpdate {
            x: 0,
            y: 0,
            width,
            height,
            format: ironrdp_server::PixelFormat::BgrA32,
            data: bytes::Bytes::from(pixel.clone()),
            stride,
        });
        self.riga = 0;
    }

    /// Estrae la banda successiva del fotogramma di ripiego.
    fn prossima_banda(&mut self) -> Option<ironrdp_server::BitmapUpdate> {
        let intero = self.in_invio.as_ref()?;
        let altezza_totale = intero.height.get();
        if self.riga >= altezza_totale {
            self.in_invio = None;
            self.riga = 0;
            return None;
        }

        let byte_per_riga = intero.stride.get().max(1);
        let righe = (BANDA_MASSIMA_BYTE / byte_per_riga).clamp(1, usize::from(u16::MAX));
        let righe = u16::try_from(righe).unwrap_or(1).min(altezza_totale - self.riga);

        let altezza = core::num::NonZeroU16::new(righe)?;
        let banda = intero.sub(0, self.riga, intero.width, altezza)?;
        self.riga += righe;
        Some(banda)
    }

    /// Manda al client l'ultimo fotogramma conservato, se serve e si puo'.
    ///
    /// Restituisce `true` quando il client ha davvero ricevuto qualcosa.
    fn manda_ultimo(&mut self) -> bool {
        if self.gia_inviato || !self.gfx.pronto() {
            return false;
        }
        let Some((size, pixel)) = self.ultimo.take() else {
            return false;
        };
        let esito = self.invia(size, &pixel);
        self.ultimo = Some((size, pixel));
        match esito {
            Ok(inviato) => {
                // Un fotogramma rifiutato perche' il client e' indietro non e'
                // perduto: si riprova al giro successivo.
                self.gia_inviato = inviato;
                inviato
            }
            Err(errore) => {
                warn!(errore = %format!("{errore:#}"), "invio del fotogramma fallito");
                false
            }
        }
    }
}

// Qui viveva un `Drop` che staccava il controllo a fine connessione, insieme
// alla cattura. Non c'e' piu', ed e' il punto di tutta la modifica: **cattura e
// controllo non appartengono alla connessione**, ma alla sessione grafica.
// Smontandoli allo stacco, Mutter restava con zero schermi e la sessione
// diventava inutilizzabile — vedere `palco.rs` per il difetto per esteso.
//
// Cio' che va comunque fatto a fine connessione — rilasciare i tasti rimasti
// premuti (§5.8 regola 4) — lo fa il portiere, che e' chi sa davvero quando una
// connessione e' finita.

#[async_trait::async_trait]
impl RdpServerDisplayUpdates for AggiornamentiDesktop {
    /// # Sicurezza rispetto all'annullamento
    ///
    /// Entrambi i rami della `select!` sono annullabili senza perdita: la
    /// ricezione dal canale e l'attesa sul canale di osservazione riprendono da
    /// dove erano. Un fotogramma già estratto viene consumato subito, dentro lo
    /// stesso giro, quindi non resta mai a metà.
    async fn next_update(&mut self) -> Result<Option<DisplayUpdate>> {
        loop {
            // Una connessione piu' recente ha preso il posto di questa: si
            // chiude, invece di contendersi la pipeline grafica.
            if self.generazione.load(Ordering::Acquire) != self.mia {
                // Ci si limita a farsi da parte: il palco **non** si smonta.
                // Appartiene alla sessione grafica, e chi ha preso il posto di
                // questa sorgente ci sta gia' disegnando sopra.
                info!(generazione = self.mia, "sorgente superata da una connessione piu' recente");
                return Ok(None);
            }

            // Il puntatore non e' piu' dentro l'immagine: lo disegna il client,
            // con la propria freccia e senza aspettare la rete. Glielo si dice
            // una volta sola, all'inizio.
            if !self.puntatore_annunciato {
                self.puntatore_annunciato = true;
                return Ok(Some(DisplayUpdate::DefaultPointer));
            }

            // Le bande di uno stesso fotogramma vanno inviate di seguito,
            // senza attendere: si prosegue finche' il fotogramma e' completo.
            if let Some(banda) = self.prossima_banda() {
                return Ok(Some(DisplayUpdate::Bitmap(banda)));
            }

            // Si clona il riferimento al palco prima della `select!`: dentro,
            // l'altro ramo prende `self` in prestito mutabile.
            let palco = Arc::clone(&self.palco);

            tokio::select! {
                // Il ridimensionamento ha la precedenza: vanno annunciati al
                // client prima di mandargli fotogrammi della nuova misura.
                esito = self.rx.changed() => {
                    if esito.is_err() {
                        return Ok(None); // il server sta chiudendo
                    }
                    let size = *self.rx.borrow_and_update();

                    // Con EGFX la misura nuova si comunica **ridichiarando la
                    // tela grafica**, cosa che avviene da se' alla creazione
                    // della prossima superficie.
                    //
                    // Annunciarla invece come ridimensionamento della sessione
                    // costringe RDP alla sequenza di riattivazione: il client
                    // rifa' lo scambio delle capacita', azzera il proprio stato
                    // grafico e — verificato sul client Android — **non
                    // rinegozia piu' EGFX**. Da li' in poi resta il solo
                    // percorso di ripiego, che manda pixel non compressi: si
                    // vede, ma la schermata si forma lentissimamente.
                    if self.gfx.pronto() {
                        info!(larghezza = size.width, altezza = size.height, "ridimensiono la tela grafica");
                        if let Err(e) = self.applica_ridimensionamento(size).await {
                            warn!(errore = %format!("{e:#}"), "riavvio della cattura fallito");
                            return Ok(None);
                        }
                        continue;
                    }

                    info!(
                        larghezza = size.width,
                        altezza = size.height,
                        "ridimensionamento rinviato: la pipeline grafica non e' ancora negoziata"
                    );
                    self.resize_atteso = Some((size, Instant::now()));
                    continue;
                }

                ricevuto = palco.prossimo() => {
                    let fotogramma = match ricevuto {
                        Arrivo::Fotogramma(fotogramma) => fotogramma,

                        // Nessun fotogramma non e' un errore: su un desktop
                        // immobile Mutter non ne manda affatto (§5.6). Si torna
                        // al ciclo, dove aspettano il ridimensionamento, il
                        // ripiego e il recupero dell'ultimo fotogramma.
                        Arrivo::Niente => continue,

                        // La cattura si e' chiusa. Se la sessione grafica non
                        // c'e' piu' — l'utente ha scelto «Esci» — la cosa
                        // giusta e' **chiudere la connessione**: e' quello che
                        // fa un desktop remoto quando si esce, e obbliga a
                        // riautenticarsi per entrare nella sessione successiva.
                        // Lasciare il client attaccato a un'immagine congelata,
                        // come faceva la prima stesura del palco, e' il
                        // peggiore dei due mondi: sembra tutto vivo e non
                        // risponde niente.
                        Arrivo::Finita => {
                            let size = *self.rx.borrow();
                            self.palco.smonta(&self.controllo).await;

                            if sessione::viva().await {
                                // La sessione c'e' ancora: e' caduta solo la
                                // cattura. Si rimonta e si prosegue.
                                warn!("la cattura si e' fermata ma la sessione e' viva: rimonto");
                                if let Err(errore) = self.riavvia_cattura(size).await {
                                    warn!(errore = %format!("{errore:#}"), "rimontaggio fallito");
                                    return Ok(None);
                                }
                                continue;
                            }

                            info!("la sessione grafica e' terminata: chiudo la connessione");
                            return Ok(None);
                        }
                    };

                    // Le misure arrivano dal compositore come interi a 32 bit,
                    // ma RDP ne ammette solo 16: si verifica invece di
                    // troncare in silenzio, che darebbe un'immagine assurda
                    // senza dire perche'.
                    let (Ok(width), Ok(height)) = (
                        u16::try_from(fotogramma.larghezza),
                        u16::try_from(fotogramma.altezza),
                    ) else {
                        warn!(
                            larghezza = fotogramma.larghezza,
                            altezza = fotogramma.altezza,
                            "il compositore ha prodotto una misura fuori dai limiti di RDP"
                        );
                        continue;
                    };
                    let size = DesktopSize { width, height };
                    let pixel = fotogramma.compatto();

                    // Un fotogramma identico al precedente non si codifica.
                    //
                    // Mutter manda un buffer anche quando a cambiare e' stato
                    // solo il puntatore, che ora vive nei metadati e non
                    // nell'immagine. Ricodificarlo costerebbe un fotogramma
                    // intero per non mostrare nulla di nuovo. Il confronto su
                    // undici megabyte costa un millesimo di secondo contro le
                    // decine che costa la codifica, ed e' lo stesso rimedio che
                    // usa `gnome-remote-desktop`.
                    if self
                        .ultimo
                        .as_ref()
                        .is_some_and(|(s, p)| *s == size && p.as_slice() == pixel.as_ref())
                    {
                        continue;
                    }

                    // Si conserva **prima** di provare a spedire: se la
                    // pipeline non e' pronta, questo potrebbe essere l'ultimo
                    // fotogramma che Mutter manda per un pezzo.
                    self.ultimo = Some((size, pixel.into_owned()));
                    self.gia_inviato = false;

                    let inviato = self.manda_ultimo();
                    debug!(inviato, larghezza = size.width, altezza = size.height, "fotogramma del desktop");
                    // Finche' EGFX non c'e', si disegna col percorso di ripiego.
                    self.prepara_ripiego();
                    // I fotogrammi EGFX non passano di qui: si torna in attesa.
                    continue;
                }

                // Rete di sicurezza: recupera il fotogramma che non si e'
                // potuto spedire, tipicamente perche' la pipeline grafica non
                // era ancora stata negoziata quando e' arrivato.
                _ = self.ripresa.tick() => {
                    // Il ridimensionamento rinviato si applica appena la
                    // pipeline grafica c'e'. Se non arriva entro un secondo e
                    // mezzo il client evidentemente non la vuole, e allora si
                    // ricorre al ridimensionamento della sessione — con la
                    // riattivazione che comporta.
                    if let Some((size, da)) = self.resize_atteso {
                        let pronta = self.gfx.pronto();
                        let scaduta = da.elapsed() > std::time::Duration::from_millis(1500);
                        if pronta || scaduta {
                            self.resize_atteso = None;
                            info!(
                                larghezza = size.width,
                                altezza = size.height,
                                con_egfx = pronta,
                                "applico il ridimensionamento rinviato"
                            );
                            if let Err(e) = self.applica_ridimensionamento(size).await {
                                warn!(errore = %format!("{e:#}"), "riavvio della cattura fallito");
                                return Ok(None);
                            }
                            if !pronta {
                                return Ok(Some(DisplayUpdate::Resize(size)));
                            }
                            continue;
                        }
                    }

                    if self.manda_ultimo() {
                        debug!("fotogramma recuperato");
                    }
                    self.prepara_ripiego();
                    continue;
                }
            }
        }
    }
}
