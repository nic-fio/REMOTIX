//! REMOTIX — server RDP per Linux.
//!
//! Accetta una connessione RDP cifrata, completa la negoziazione, mostra il
//! desktop della sessione grafica locale — catturato da PipeWire e codificato
//! in H.264 sulla pipeline EGFX — e ne inoltra tastiera e mouse al
//! compositore.
//!
//! Va eseguito **dentro l'ambiente della sessione grafica**, perche' deve
//! parlare con lo stesso bus del compositore.
//!
//! Configurazione tramite variabili d'ambiente, per non trascinarsi dietro un
//! analizzatore di riga di comando finche' non serve davvero:
//!
//!   REMOTIX_BIND      indirizzo di ascolto      (default 0.0.0.0:3389)
//!   REMOTIX_WIDTH     larghezza iniziale        (default 1920)
//!   REMOTIX_HEIGHT    altezza iniziale          (default 1080)
//!   REMOTIX_SORGENTE  "prova" per l'immagine di prova invece del desktop
//!   REMOTIX_TLS_DIR   cartella del certificato  (default ./tls)
//!   REMOTIX_CODECS    codec dichiarati          (default "remotefx:off")
//!   REMOTIX_TASTIERA  disposizione XKB della sessione, es. "it" o "it,us"
//!                     (default: non si tocca quella dell'utente)
//!   REMOTIX_LOG       livello di registro       (default info)

use remotix::{
    autenticazione, controllo, desktop, egfx, h264, palco, portiere, sentinella, sessione, testcard,
    tls, uscita,
};

use core::net::SocketAddr;
use std::path::PathBuf;
use std::time::Duration;

use anyhow::{Context as _, Result};
use ironrdp_pdu::rdp::capability_sets::server_codecs_capabilities;
use ironrdp_server::{
    DesktopSize, DisplayUpdate, RdpServer, RdpServerDisplay, RdpServerDisplayUpdates,
};
use tokio::sync::watch;
use tracing::{debug, info, warn};

const BIND_PREDEFINITO: &str = "0.0.0.0:3389";
const LARGHEZZA_PREDEFINITA: u16 = 1920;
const ALTEZZA_PREDEFINITA: u16 = 1080;

/// Codec dichiarati al client per il percorso legacy.
///
/// Riguarda solo i fotogrammi inviati prima che EGFX sia negoziato, e i client
/// che EGFX non lo hanno affatto. RemoteFX e' attivo per impostazione
/// predefinita in IronRDP, ma mstsc si e' mostrato piu' esigente di FreeRDP su
/// quel percorso: si preferisce il semplice invio di bitmap, che tutti i
/// client gestiscono. Il valore e' configurabile per poter confrontare i due
/// comportamenti senza ricompilare.
const CODEC_PREDEFINITI: &str = "remotefx:off";

/// Cadenza di aggiornamento dell'immagine di prova.
///
/// Un fotogramma al secondo basta: l'immagine e' quasi ferma e l'unico scopo e'
/// dimostrare che il flusso e' vivo. La cadenza vera arrivera' con la cattura.
const CADENZA: Duration = Duration::from_secs(1);

#[tokio::main]
async fn main() -> Result<()> {
    inizializza_registro();

    let bind: SocketAddr = variabile("REMOTIX_BIND")
        .unwrap_or_else(|| BIND_PREDEFINITO.to_owned())
        .parse()
        .context("REMOTIX_BIND non e' un indirizzo valido")?;

    let size = DesktopSize {
        width: numero("REMOTIX_WIDTH", LARGHEZZA_PREDEFINITA)?,
        height: numero("REMOTIX_HEIGHT", ALTEZZA_PREDEFINITA)?,
    };

    let cartella_tls: PathBuf = variabile("REMOTIX_TLS_DIR")
        .unwrap_or_else(|| "tls".to_owned())
        .into();

    let identita = tls::Identita::in_cartella(&cartella_tls);
    let accettatore = identita.accettatore()?;

    // Codec: elenco separato da virgole, es. "remotefx:off" oppure "remotefx:on"
    let codec_conf = variabile("REMOTIX_CODECS").unwrap_or_else(|| CODEC_PREDEFINITI.to_owned());
    let voci: Vec<&str> = codec_conf
        .split(',')
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .collect();
    // Si convalida qui, all'avvio, per fallire subito su una configurazione
    // sbagliata invece che alla prima connessione; l'elenco vero lo ricostruisce
    // il costruttore, perche' ogni server vuole il suo.
    server_codecs_capabilities(&voci)
        .map_err(|e| anyhow::anyhow!("REMOTIX_CODECS non valido: {e}"))?;

    info!(
        %bind,
        larghezza = size.width,
        altezza = size.height,
        codec = %codec_conf,
        certificato = %identita.certificato.display(),
        "REMOTIX in ascolto"
    );


    let registro = egfx::RegistroGfx::nuovo();

    // L'autenticazione si spegne **dichiarandolo**, non dimenticandosene: e' la
    // differenza fra una prova che sa di essere senza chiave e un server messo
    // in rete che non la chiede a nessuno. Il registro lo dice a caratteri
    // grossi a ogni avvio.
    let senza_autenticazione = variabile("REMOTIX_SENZA_AUTENTICAZIONE").is_some();

    // La guardia dice, per la connessione in corso, se qualcuno ha davvero
    // superato PAM. Serve perche' IronRDP salta il validatore quando il client
    // non manda credenziali: senza, si entra senza password. Vedere
    // `autenticazione::Guardia`.
    let guardia = autenticazione::Guardia::nuova(senza_autenticazione);

    // Di chi e' la sessione che stiamo servendo. Si stabilisce **all'avvio** e
    // si fallisce se non si riesce: un server che non lo sa non puo' decidere
    // chi far entrare, e la porta non va aperta lo stesso.
    let utente = autenticazione::utente_del_processo()
        .context("determinazione dell'utente che esegue REMOTIX")?;
    info!(%utente, "la sessione servita e' di questo utente, e solo lui puo' entrare");

    let validatore: Option<std::sync::Arc<dyn ironrdp_server::CredentialValidator>> =
        if senza_autenticazione {
            warn!("AUTENTICAZIONE DISATTIVATA: chiunque raggiunga la porta entra");
            None
        } else {
            let servizio = variabile("REMOTIX_PAM_SERVIZIO")
                .unwrap_or_else(|| autenticazione::SERVIZIO_PREDEFINITO.to_owned());
            Some(std::sync::Arc::new(autenticazione::Autenticatore::nuovo(
                servizio,
                utente.clone(),
                std::sync::Arc::clone(&guardia),
            )))
        };

    // L'immagine di prova non serve piu' a mostrare il prodotto, ma resta il
    // modo piu' rapido per capire se un guasto stia nella catena RDP o nella
    // cattura: mostra qualcosa senza dipendere dalla sessione grafica.
    let sorgente_di_prova = variabile("REMOTIX_SORGENTE").as_deref() == Some("prova");
    if sorgente_di_prova {
        // Nessun input con l'immagine di prova: il puntatore andrebbe a
        // comandare un desktop che il client non vede, il che confonderebbe
        // proprio la prova che questa modalita' serve a fare.
        info!("sorgente: immagine di prova (senza input)");
    } else {
        info!("sorgente: desktop della sessione grafica");
    }

    // Il controllo non tocca ancora D-Bus: la sessione si apre alla prima
    // connessione, cosi' il server puo' partire anche prima del compositore. Se
    // non riesce, si resta di sola visione. Vive **fuori** dal costruttore
    // perche' e' lo stato del compositore, che le connessioni si passano; lo
    // stato grafico invece nasce e muore con ciascuna (§5.7 regola 6).
    let controllo = controllo::Controllo::nuovo();
    let controllo_a_fine = std::sync::Arc::clone(&controllo);

    // Il palco vive quanto il server, non quanto la connessione: cattura,
    // controllo e monitor virtuale restano in piedi anche quando non c'e'
    // nessuno collegato. Senza, alla disconnessione Mutter resta con zero
    // schermi e la sessione diventa inutilizzabile (vedere `palco.rs`).
    let palco = palco::Palco::nuovo();

    // Come si avvia la sessione grafica quando non ce n'e' una — dopo un
    // «Esci», o al primo avvio della macchina, dove non c'e' alcun gestore di
    // accesso grafico ad avviarla. Configurabile perche' il comando cambia con
    // il desktop: alla fase 10 arriveranno KDE e gli altri.
    let comando_sessione = variabile("REMOTIX_SESSIONE")
        .unwrap_or_else(|| sessione::COMANDO_PREDEFINITO.to_owned());
    info!(comando = %comando_sessione, "comando della sessione grafica");

    // La disposizione della tastiera della sessione remota. RDP manda posizioni
    // fisiche, e la lettera che ne esce la decide questa (§5.8): se il client ha
    // una tastiera italiana e la sessione e' americana, i segni di
    // interpunzione non corrispondono. Va dichiarata perche' il client la
    // dichiara a IronRDP e IronRDP non la consegna a noi; senza dichiararla non
    // si tocca nulla, perche' e' una preferenza dell'utente.
    let disposizione = variabile("REMOTIX_TASTIERA");
    match &disposizione {
        Some(voluta) => info!(disposizione = %voluta, "disposizione della tastiera per la sessione"),
        None => debug!("nessuna disposizione dichiarata: si lascia quella della sessione"),
    }

    // Chi guarda se qualcuno si siede davanti alla macchina. Il primo controllo
    // lo fa qui, prima che la porta si apra: se una sessione grafica locale
    // c'e' gia', non deve esistere l'istante in cui si entra lo stesso.
    let sentinella = sentinella::Sentinella::avvia().await;

    // E chi si accorge che la sessione se ne va. Non attende: quando REMOTIX
    // parte una sessione non c'e' ancora, e la registrazione con gnome-session
    // la si fa quando ci sara' — e daccapo a ogni sessione nuova.
    let uscita = uscita::Uscita::avvia();

    // E chi sgombera. Vive a parte dal portiere perche' il caso piu' frequente
    // e' proprio quello in cui non c'e' nessuna connessione da chiudere:
    // l'utente si siede davanti alla macchina quando da remoto non c'e'
    // nessuno, e la sessione grafica remota — avviata da REMOTIX e rimasta in
    // piedi — va tolta di mezzo lo stesso.
    tokio::spawn(sgombera(
        std::sync::Arc::clone(&sentinella),
        std::sync::Arc::clone(&palco),
        std::sync::Arc::clone(&controllo),
    ));

    // Un server nuovo per ogni connessione. La misura vive in un canale di
    // osservazione che si crea qui dentro: e' una trattativa fra questo client e
    // noi, e non deve sopravvivergli.
    let costruisci = move || -> Result<RdpServer> {
        // Nessuno eredita l'autenticazione di chi lo ha preceduto: si riparte
        // da negato a ogni connessione.
        guardia.azzera();

        let (tx, rx) = watch::channel(size);
        let fabbrica = egfx::FabbricaGfx::nuova(std::sync::Arc::clone(&registro));
        let voci: Vec<&str> = codec_conf
            .split(',')
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .collect();
        let codecs = server_codecs_capabilities(&voci)
            .map_err(|e| anyhow::anyhow!("REMOTIX_CODECS non valido: {e}"))?;
        let comune = RdpServer::builder()
            .with_addr(bind)
            .with_tls(accettatore.clone());

        let server = if sorgente_di_prova {
            comune
                .with_no_input()
                .with_display_handler(SchermataDiProva {
                    size: tx,
                    rx,
                    registro: std::sync::Arc::clone(&registro),
                })
                .with_bitmap_codecs(codecs)
                .with_gfx_factory(Some(Box::new(fabbrica)))
                .with_credential_validator(validatore.clone())
                .build()
        } else {
            comune
                .with_input_handler(controllo::GestoreInput::nuovo(
                    std::sync::Arc::clone(&controllo),
                    std::sync::Arc::clone(&guardia),
                ))
                .with_display_handler(desktop::Desktop::nuovo(
                    tx,
                    rx,
                    std::sync::Arc::clone(&registro),
                    std::sync::Arc::clone(&controllo),
                    std::sync::Arc::clone(&palco),
                    comando_sessione.clone(),
                    disposizione.clone(),
                    std::sync::Arc::clone(&guardia),
                ))
                .with_bitmap_codecs(codecs)
                .with_gfx_factory(Some(Box::new(fabbrica)))
                .with_credential_validator(validatore.clone())
                .build()
        };
        Ok(server)
    };

    // Il rilascio di cio' che era premuto vale **anche** quando non c'e' piu'
    // una sessione a cui parlare: il suo effetto principale e' dimenticare cio'
    // che crediamo premuto, e quel ricordo sopravvive alla connessione
    // (§5.8 regola 4).
    portiere::servi(
        bind,
        costruisci,
        move || {
            controllo_a_fine.rilascia_tutto();
        },
        sentinella,
        uscita,
    )
    .await
    .context("esecuzione del server")
}

/// Chiude la sessione grafica remota quando ne compare una locale.
///
/// # Perche' non basta staccare il client
///
/// Perche' la regola di §3.4 e' «una sola sessione grafica per utente», e il
/// collegamento e' un'altra cosa dalla sessione. Se restasse in piedi il
/// compositore remoto, chi si siede davanti alla macchina avrebbe due sessioni
/// grafiche a proprio nome sullo stesso `$XDG_RUNTIME_DIR`: la seconda
/// troverebbe occupato `org.gnome.Shell` e non partirebbe. Deciso dall'utente
/// il 3 agosto: si chiude del tutto.
///
/// Il palco si smonta **dopo**, e va smontato: cattura e monitor virtuale sono
/// oggetti di un compositore che non esiste piu', e chi si ricollegasse alla
/// stessa misura li troverebbe «gia' montati» e resterebbe davanti a uno
/// schermo nero.
async fn sgombera(
    sentinella: std::sync::Arc<sentinella::Sentinella>,
    palco: std::sync::Arc<palco::Palco>,
    controllo: std::sync::Arc<controllo::Controllo>,
) {
    loop {
        let locale = sentinella.attendi_comparsa().await;
        match sessione::termina().await {
            Ok(true) => info!(%locale, "sessione grafica remota chiusa: la locale ha la precedenza"),
            Ok(false) => debug!(%locale, "nessuna sessione grafica remota da chiudere"),
            // Si prosegue: il palco va smontato comunque, e il registro dice
            // cosa non ha funzionato. L'alternativa — riprovare all'infinito —
            // riempirebbe il registro senza cambiare l'esito.
            Err(errore) => warn!(
                errore = %format!("{errore:#}"),
                "la sessione grafica remota non si e' chiusa"
            ),
        }
        palco.smonta(&controllo).await;

        // Si aspetta che l'utente locale se ne vada, altrimenti si
        // richiuderebbe una sessione per volta all'infinito: finche' lui e' li',
        // sessione remota non ce n'e' e non deve essercene.
        sentinella.attendi_scomparsa().await;
    }
}

// ---------------------------------------------------------------------------
// Display che mostra l'immagine di prova
// ---------------------------------------------------------------------------

/// La dimensione corrente vive in un canale di osservazione.
///
/// Serve perche' le due meta' del display sono oggetti distinti: la richiesta
/// di ridimensionamento arriva qui, ma chi produce i fotogrammi e' il flusso di
/// aggiornamenti, creato separatamente. Il canale li tiene allineati.
struct SchermataDiProva {
    size: watch::Sender<DesktopSize>,
    rx: watch::Receiver<DesktopSize>,
    registro: std::sync::Arc<egfx::RegistroGfx>,
}

#[async_trait::async_trait]
impl RdpServerDisplay for SchermataDiProva {
    async fn size(&mut self) -> DesktopSize {
        *self.size.borrow()
    }

    /// Il client propone la propria dimensione alla connessione.
    ///
    /// La accettiamo: cosi' l'immagine di prova mostra la risoluzione davvero
    /// negoziata, che e' proprio l'informazione che vogliamo verificare.
    async fn request_initial_size(&mut self, client_size: DesktopSize) -> DesktopSize {
        // Con REMOTIX_FORZA_DIMENSIONE si ignora la proposta del client e si
        // usa quella configurata. Serve a riprodurre da qui le risoluzioni di
        // client che non ho a disposizione.
        if variabile("REMOTIX_FORZA_DIMENSIONE").is_some() {
            let attuale = *self.size.borrow();
            info!(larghezza = attuale.width, altezza = attuale.height, "dimensione forzata");
            return attuale;
        }
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

    /// Il client chiede una nuova dimensione a sessione avviata.
    ///
    /// Accade sui client che adattano la risoluzione alla finestra: senza
    /// gestirla, il server continuerebbe a disegnare alla dimensione iniziale e
    /// il client mostrerebbe solo la porzione in alto a sinistra, tagliando il
    /// resto. E' l'anticipo minimo della fase 6 del piano.
    fn request_layout(&mut self, layout: ironrdp_displaycontrol::pdu::DisplayControlMonitorLayout) {
        let Some(monitor) = layout
            .monitors()
            .iter()
            .find(|m| m.is_primary())
            .or_else(|| layout.monitors().first())
        else {
            warn!("richiesta di ridimensionamento senza monitor, ignorata");
            return;
        };

        let (w, h) = monitor.dimensions();
        let (Ok(width), Ok(height)) = (u16::try_from(w), u16::try_from(h)) else {
            warn!(w, h, "dimensione richiesta fuori intervallo, ignorata");
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
        let mut rx = self.rx.clone();
        rx.mark_unchanged();
        // Lo stato grafico appartiene alla connessione: lo si chiede al
        // registro adesso, non lo si tiene da parte.
        let gfx = self
            .registro
            .corrente()
            .unwrap_or_else(egfx::StatoGfx::nuovo);
        Ok(Box::new(AggiornamentiDiProva {
            rx,
            gfx,
            avvio: std::time::Instant::now(),
            fotogramma: 0,
            cadenza: tokio::time::interval(CADENZA),
            codificatore: None,
            serve_chiave: false,
            in_invio: None,
            riga: 0,
        }))
    }
}

/// Dimensione massima di un singolo aggiornamento inviato al client.
///
/// Un fotogramma a 1920x1080 non compresso pesa 8,3 MB. Inviato in un unico
/// aggiornamento, supera il buffer di riassemblaggio dichiarato da alcuni
/// client — mstsc fra questi — che riescono a ricomporne solo una parte e
/// mostrano l'immagine a riquadri sparsi. Suddividere in bande piu' piccole
/// rende l'invio digeribile da tutti.
///
/// E' anche la forma che avra' la cattura vera: regioni modificate, non
/// schermate intere.
const BANDA_MASSIMA_BYTE: usize = 512 * 1024;

struct AggiornamentiDiProva {
    rx: watch::Receiver<DesktopSize>,
    gfx: std::sync::Arc<egfx::StatoGfx>,
    avvio: std::time::Instant,
    fotogramma: u64,
    cadenza: tokio::time::Interval,
    /// Codificatore H.264, creato alla prima necessita' e rifatto se cambia
    /// la risoluzione: OpenH264 non la cambia a caldo.
    codificatore: Option<h264::Codificatore>,
    /// Vero quando il prossimo fotogramma deve essere un fotogramma chiave.
    serve_chiave: bool,
    /// Fotogramma disegnato e in corso di invio, banda per banda.
    /// Usato solo dal percorso di compatibilita', quando EGFX non c'e'.
    in_invio: Option<ironrdp_server::BitmapUpdate>,
    /// Prima riga non ancora inviata del fotogramma corrente.
    riga: u16,
}

impl AggiornamentiDiProva {
    /// Codifica il fotogramma in H.264 e lo consegna alla pipeline EGFX.
    ///
    /// Il codificatore viene creato alla prima chiamata e ricostruito quando
    /// cambia la risoluzione, perche' OpenH264 non la cambia a caldo. Alla
    /// ricostruzione riparte da un fotogramma chiave, che e' proprio cio' che
    /// serve al client per riagganciarsi dopo un ridimensionamento.
    fn invia_avc420(
        &mut self,
        size: DesktopSize,
        bgra: &[u8],
        istante_ms: u32,
    ) -> Result<bool> {
        // Si chiede il permesso prima di codificare: vedere
        // `StatoGfx::puo_inviare`. Qui i fotogrammi sono uno al secondo e la
        // pipeline non si satura mai, ma il difetto sarebbe lo stesso e questa
        // sorgente serve proprio a distinguere i guasti della catena RDP da
        // quelli della cattura: deve comportarsi come quella vera.
        if !self.gfx.puo_inviare() {
            return Ok(false);
        }

        let serve_nuovo = match &self.codificatore {
            Some(c) => c.dimensione() != (size.width, size.height),
            None => true,
        };
        if serve_nuovo {
            self.codificatore = Some(h264::Codificatore::nuovo(size.width, size.height)?);
            self.serve_chiave = false;
        }
        let codificatore = self.codificatore.as_mut().expect("appena creato");

        if self.serve_chiave {
            codificatore.forza_chiave();
            self.serve_chiave = false;
        }

        let flusso = codificatore.codifica(bgra)?;
        let inviato = self.gfx.invia_avc420(size, &flusso, istante_ms)?;
        if !inviato {
            self.serve_chiave = true;
        }
        Ok(inviato)
    }

    /// Estrae la banda successiva del fotogramma in corso di invio.
    ///
    /// Restituisce `None` quando il fotogramma e' stato inviato per intero.
    fn prossima_banda(&mut self) -> Option<ironrdp_server::BitmapUpdate> {
        let intero = self.in_invio.as_ref()?;
        let altezza_totale = intero.height.get();
        if self.riga >= altezza_totale {
            self.in_invio = None;
            self.riga = 0;
            return None;
        }

        // quante righe stanno nel limite, almeno una
        let byte_per_riga = intero.stride.get().max(1);
        let righe = (BANDA_MASSIMA_BYTE / byte_per_riga).clamp(1, usize::from(u16::MAX));
        let righe = u16::try_from(righe).unwrap_or(1);
        let righe = righe.min(altezza_totale - self.riga);

        let altezza = core::num::NonZeroU16::new(righe)?;
        let banda = intero.sub(0, self.riga, intero.width, altezza)?;
        self.riga += righe;
        Some(banda)
    }
}

#[async_trait::async_trait]
impl RdpServerDisplayUpdates for AggiornamentiDiProva {
    /// # Sicurezza rispetto all'annullamento
    ///
    /// Il contratto di IronRDP richiede che questo metodo sia annullabile senza
    /// perdita di dati, perche' viene usato dentro una `select!`. Entrambi i
    /// rami lo sono: `Interval::tick` e `Receiver::changed` riprendono da dove
    /// erano. Il disegno non ha stato da preservare: se la chiamata viene
    /// interrotta, al giro successivo si ridisegna da capo.
    async fn next_update(&mut self) -> Result<Option<DisplayUpdate>> {
        loop {
            // Percorso di compatibilita': se un fotogramma e' gia' disegnato si
            // prosegue con la banda successiva senza attendere, perche' le bande
            // di uno stesso fotogramma vanno inviate di seguito.
            if let Some(banda) = self.prossima_banda() {
                return Ok(Some(DisplayUpdate::Bitmap(banda)));
            }

            tokio::select! {
                // Un ridimensionamento ha la precedenza: va comunicato al client
                // prima di inviargli fotogrammi della nuova dimensione.
                esito = self.rx.changed() => {
                    if esito.is_err() {
                        return Ok(None); // il server sta chiudendo
                    }
                    let size = *self.rx.borrow_and_update();
                    info!(larghezza = size.width, altezza = size.height, "ridimensiono lo schermo");
                    // il fotogramma in corso non vale piu': ha la vecchia dimensione
                    self.in_invio = None;
                    self.riga = 0;
                    self.gfx.invalida_superficie();
                    return Ok(Some(DisplayUpdate::Resize(size)));
                }

                _ = self.cadenza.tick() => {
                    let size = *self.rx.borrow();
                    let Some(immagine) = testcard::disegna(size, self.fotogramma) else {
                        return Ok(None);
                    };
                    self.fotogramma = self.fotogramma.wrapping_add(1);

                    // --- percorso principale: EGFX -----------------------------
                    if self.gfx.pronto() {
                        let ms = u32::try_from(self.avvio.elapsed().as_millis()).unwrap_or(u32::MAX);
                        match self.invia_avc420(size, &immagine.data, ms) {
                            Ok(inviato) => debug!(
                                fotogramma = self.fotogramma,
                                inviato,
                                larghezza = size.width,
                                altezza = size.height,
                                "fotogramma AVC420"
                            ),
                            Err(errore) => warn!(errore = %format!("{errore:#}"), "invio AVC420 fallito"),
                        }
                        // I fotogrammi EGFX non passano di qui: si torna in attesa.
                        continue;
                    }

                    // --- percorso di compatibilita': bitmap a bande -------------
                    debug!(
                        fotogramma = self.fotogramma,
                        larghezza = size.width,
                        altezza = size.height,
                        "fotogramma bitmap"
                    );
                    self.in_invio = Some(immagine);
                    self.riga = 0;
                    return Ok(self.prossima_banda().map(DisplayUpdate::Bitmap));
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Utilita' di configurazione
// ---------------------------------------------------------------------------

fn variabile(nome: &str) -> Option<String> {
    std::env::var(nome).ok().filter(|v| !v.is_empty())
}

fn numero(nome: &str, predefinito: u16) -> Result<u16> {
    match variabile(nome) {
        None => Ok(predefinito),
        Some(v) => v.parse().with_context(|| format!("{nome} non e' un numero valido")),
    }
}

fn inizializza_registro() {
    let livello = variabile("REMOTIX_LOG").unwrap_or_else(|| "info".to_owned());
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_new(&livello)
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .with_target(false)
        .init();
}
