//! L'input: dal client al compositore.
//!
//! # La via scelta
//!
//! Si usa `org.gnome.Mutter.RemoteDesktop`, l'interfaccia D-Bus diretta del
//! compositore, per gli stessi motivi per cui `screencast.rs` usa quella della
//! cattura: il portale presuppone un utente seduto davanti allo schermo che
//! conceda il permesso, e in una sessione senza monitor quell'interazione non
//! puo' avvenire.
//!
//! `gnome-remote-desktop` e' passato a **libei** per la stessa cosa. Non lo si
//! e' seguito: libei serve a chi deve chiedere il permesso e negoziare quali
//! dispositivi emulare, mentre qui la sessione la avvia REMOTIX e i dispositivi
//! li decide REMOTIX. I metodi `Notify*` fanno esattamente cio' che serve, con
//! una dipendenza in meno.
//!
//! # La regola che governa il collegamento fra input e immagine
//!
//! Il puntatore si muove in **coordinate assolute dentro un flusso**, e il
//! flusso e' quello della cattura: `NotifyPointerMotionAbsolute` vuole il
//! percorso D-Bus dello *stream* di ScreenCast. Perche' Mutter accetti di
//! collegarli, la sessione di cattura va creata **dichiarando l'identificativo
//! della sessione di controllo**, nella proprieta' `remote-desktop-session-id`.
//!
//! Ne discende un ordine che non e' negoziabile, e che **non e' quello che
//! verrebbe naturale**:
//!
//!   1. si crea la sessione di controllo e se ne legge `SessionId`,
//!      **senza avviarla**;
//!   2. si crea la sessione di cattura dichiarando quell'identificativo;
//!   3. **adesso** si avvia la sessione di controllo;
//!   4. si registra il monitor virtuale e si avvia il **flusso**, non la
//!      sessione di cattura;
//!   5. si dice al controllo qual e' il flusso su cui muovere il puntatore.
//!
//! Due paletti tengono ferma questa sequenza, e ciascuno e' costato un
//! tentativo:
//!
//!   - il controllo non si puo' avviare prima del punto 2, perche' Mutter
//!     registra la cattura solo su una sessione non ancora partita: risponde
//!     `Remote desktop session already started`;
//!   - la cattura associata a un controllo **non si avvia con
//!     `Session.Start`** — Mutter risponde `Must be started from remote desktop
//!     session` — ma un flusso per volta, con `Stream.Start`. Senza controllo
//!     vale invece la via di prima, e la cattura si avvia dalla sessione.
//!
//! La sequenza vive tutta dentro `screencast.rs`, che e' l'unico punto da cui si
//! vedono insieme i pezzi che vanno ordinati.
//!
//! # Perche' le due sessioni nascono e muoiono insieme
//!
//! Da quel vincolo discende il resto: siccome la cattura si rifa' a ogni
//! ridimensionamento — la misura del monitor virtuale si concorda una volta
//! sola, nella negoziazione PipeWire — e siccome una cattura nuova non si puo'
//! registrare su un controllo gia' avviato, **anche il controllo si rifa'**.
//! Sono una coppia, non due cose indipendenti.
//!
//! Il prezzo: un tasto tenuto premuto mentre il client ridimensiona non risulta
//! piu' premuto dopo, perche' la tastiera virtuale e' un'altra. Il client non
//! rimanda la pressione, quindi il tasto si perde. Costa poco e si nota
//! raramente; toglierlo del tutto vuol dire ridimensionare senza rifare la
//! cattura, che e' materia della fase 6.
//!
//! # Perche' la connessione D-Bus e' una sola, condivisa con la cattura
//!
//! Mutter verifica che le chiamate `Notify*` arrivino **dallo stesso peer** che
//! ha creato la sessione di controllo. Non verifica il peer nell'associare la
//! cattura, ma tenerle sulla stessa connessione toglie di mezzo la questione ed
//! e' cio' che fa anche `gnome-remote-desktop`.
//!
//! Il prezzo si paga in `screencast.rs`: la connessione non muore piu' insieme
//! alla singola cattura, quindi le sessioni di cattura vanno chiuse
//! esplicitamente invece di lasciarle cadere.
//!
//! # Perche' l'input passa per un canale invece di partire subito
//!
//! I metodi di `RdpServerInputHandler` sono sincroni e IronRDP li chiama
//! **dentro il proprio ciclo asincrono**, tenendo un lucchetto. Una chiamata
//! D-Bus li' dentro fermerebbe un thread del runtime e con esso tutte le
//! connessioni affidate a quel thread: e' la regola 7 di `SPECIFICA.md` §5.7.
//! Qui si accoda e basta — operazione che non attende nulla — e un compito
//! separato svuota la coda parlando con Mutter.

use std::collections::HashSet;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};

use anyhow::{Context as _, Result};
use ironrdp_pdu::input::fast_path::SynchronizeFlags;
use ironrdp_server::{DesktopSize, KeyboardEvent, MouseEvent, RdpServerInputHandler};
use tokio::sync::{mpsc, watch};
use tracing::{debug, info, trace, warn};
use zbus::zvariant::OwnedObjectPath;
use zbus::{Connection, proxy};

use crate::tastiera;

// --- codici evdev dei bottoni del mouse ------------------------------------
//
// Da `linux/input-event-codes.h`. Sono quelli che Mutter si aspetta.
const BTN_LEFT: i32 = 0x110;
const BTN_RIGHT: i32 = 0x111;
const BTN_MIDDLE: i32 = 0x112;
const BTN_SIDE: i32 = 0x113;
const BTN_EXTRA: i32 = 0x114;

/// Flag `source_wheel` di `NotifyPointerAxis`.
///
/// Dichiarare la provenienza conta: GNOME accelera e arrotonda in modo diverso
/// lo scorrimento di una rotella e quello di un dito su un trackpad.
const ASSE_ROTELLA: u32 = 2;

/// Quanto vale un passo di rotella per `NotifyPointerAxis`.
///
/// Lo dichiara l'interfaccia: 10.0 e' uno scatto discreto.
const PASSO_ASSE: f64 = 10.0;

/// Quanti "wheel rotation units" fanno uno scatto di rotella in RDP.
///
/// E' la convenzione di Windows, che RDP eredita.
const UNITA_PER_SCATTO: f64 = 120.0;

/// Il fattore con cui il canale di input avanzato conta la rotella.
///
/// Quel canale — un'estensione di FreeRDP, non parte di RDP — porta le stesse
/// unita' moltiplicate per 0x10000, per poter descrivere anche le rotelle ad
/// alta risoluzione che si muovono di frazioni di scatto. Uno scatto arriva
/// quindi come 7 864 320, e preso alla lettera manderebbe il puntatore a
/// scorrere per mezzo chilometro: e' il difetto che si e' visto in prova, dove
/// la rotella non muoveva nulla perche' Mutter scartava un valore assurdo.
const RISOLUZIONE_AINPUT: f64 = 65536.0;

/// Quanti eventi si accorpano al massimo in un giro del compito.
///
/// Serve solo a mettere un tetto: senza, un client impazzito terrebbe il
/// compito dentro il ciclo di svuotamento a tempo indeterminato.
const ACCORPAMENTO_MASSIMO: usize = 512;

#[proxy(
    interface = "org.gnome.Mutter.RemoteDesktop",
    default_service = "org.gnome.Mutter.RemoteDesktop",
    default_path = "/org/gnome/Mutter/RemoteDesktop"
)]
trait RemoteDesktop {
    fn create_session(&self) -> zbus::Result<OwnedObjectPath>;

    #[zbus(property)]
    fn version(&self) -> zbus::Result<i32>;
}

#[proxy(
    interface = "org.gnome.Mutter.RemoteDesktop.Session",
    default_service = "org.gnome.Mutter.RemoteDesktop"
)]
trait SessioneRemota {
    fn start(&self) -> zbus::Result<()>;
    fn stop(&self) -> zbus::Result<()>;

    fn notify_keyboard_keycode(&self, keycode: u32, state: bool) -> zbus::Result<()>;
    fn notify_keyboard_keysym(&self, keysym: u32, state: bool) -> zbus::Result<()>;
    fn notify_pointer_button(&self, button: i32, state: bool) -> zbus::Result<()>;
    fn notify_pointer_axis(&self, dx: f64, dy: f64, flags: u32) -> zbus::Result<()>;
    fn notify_pointer_motion_relative(&self, dx: f64, dy: f64) -> zbus::Result<()>;
    fn notify_pointer_motion_absolute(&self, stream: &str, x: f64, y: f64) -> zbus::Result<()>;

    #[zbus(property)]
    fn session_id(&self) -> zbus::Result<String>;

    #[zbus(signal)]
    fn closed(&self) -> zbus::Result<()>;
}

/// Cio' che la cattura deve sapere per farsi associare alla sessione di
/// controllo, e per avviarla al momento giusto.
#[derive(Clone)]
pub struct Contesto {
    /// La connessione su cui creare anche la sessione di cattura.
    pub connessione: Connection,
    /// Il valore da mettere in `remote-desktop-session-id`.
    pub id_sessione: String,
    sessione: Arc<SessioneControllo>,
}

impl Contesto {
    /// Avvia la sessione di controllo.
    ///
    /// Il momento e' vincolato da due lati e lo decide `screencast.rs`: dopo
    /// che la cattura si e' registrata, prima che il flusso parta.
    pub(crate) async fn avvia_controllo(&self) -> Result<()> {
        self.sessione.avvia().await
    }
}

impl core::fmt::Debug for Contesto {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.debug_struct("Contesto")
            .field("id_sessione", &self.id_sessione)
            .finish_non_exhaustive()
    }
}

/// Dove il puntatore si muove: il flusso della cattura e la sua misura.
#[derive(Clone, Debug)]
struct Bersaglio {
    /// Percorso D-Bus del flusso di ScreenCast.
    flusso: String,
    size: DesktopSize,
}

/// Un evento di input in attesa di essere consegnato al compositore.
#[derive(Debug)]
enum Evento {
    Tasto { evdev: u16, premuto: bool },
    Carattere { keysym: u32, premuto: bool },
    Blocchi(SynchronizeFlags),
    Muovi { x: u16, y: u16 },
    MuoviRelativo { dx: i32, dy: i32 },
    Bottone { codice: i32, premuto: bool },
    Asse { dx: f64, dy: f64, rotella: bool },
    /// Rilascia tutto cio' che risulta ancora premuto.
    Rilascia,
    /// Fa esistere la tastiera virtuale prima che serva.
    ///
    /// Mutter la crea **pigramente, alla prima pressione**:
    ///
    /// ```c
    /// if (pressed)
    ///     ensure_virtual_device (session, CLUTTER_KEYBOARD_DEVICE);
    /// ```
    ///
    /// Quando il dispositivo compare sul seat, Wayland deve annunciare ai
    /// client la capacita' tastiera e ricalcolare a chi spetta il fuoco. La
    /// battuta che ha innescato tutto questo arriva prima che il fuoco sia
    /// stabilito, e va a vuoto: l'utente apre una finestra, scrive, e la prima
    /// lettera non compare — poi tutto funziona.
    ///
    /// Si manda quindi un colpo a vuoto appena la sessione parte, quando
    /// nessuno sta ancora scrivendo. Il codice **0** e' `KEY_RESERVED`: nessuna
    /// disposizione di tastiera gli associa un simbolo, quindi non scrive nulla
    /// da nessuna parte — ma fa esistere il dispositivo, che e' tutto cio' che
    /// serve.
    Innesca,
}

impl Evento {
    /// Il genere dell'evento, senza il suo contenuto.
    ///
    /// Serve al registro: dice che cos'e' andato storto senza dire quale tasto
    /// fosse.
    fn genere(&self) -> &'static str {
        match self {
            Self::Tasto { .. } => "tasto",
            Self::Carattere { .. } => "carattere",
            Self::Blocchi(_) => "blocchi",
            Self::Muovi { .. } => "movimento",
            Self::MuoviRelativo { .. } => "movimento relativo",
            Self::Bottone { .. } => "bottone",
            Self::Asse { .. } => "asse",
            Self::Rilascia => "rilascio",
            Self::Innesca => "innesco",
        }
    }
}

// ---------------------------------------------------------------------------
// La sessione di controllo
// ---------------------------------------------------------------------------

struct SessioneControllo {
    connessione: Connection,
    sessione: SessioneRemotaProxy<'static>,
    id: String,
    viva: Arc<AtomicBool>,
    /// Vero quando la chiusura l'abbiamo chiesta noi.
    ///
    /// Distingue le due chiusure che arrivano dallo stesso segnale: quella che
    /// segue un ridimensionamento — normale, e frequente — e quella con cui
    /// Mutter ci dice che qualcosa e' andato storto. Senza distinguerle, ogni
    /// trascinamento del bordo della finestra lascerebbe nel registro un
    /// avviso che non segnala nulla.
    congedata: Arc<AtomicBool>,
}

impl SessioneControllo {
    /// Crea la sessione **senza avviarla**.
    ///
    /// Fra questa e `avvia` ci sta la creazione della cattura, che e' l'unico
    /// momento in cui Mutter accetta di registrarla.
    async fn crea() -> Result<Self> {
        let connessione = Connection::session()
            .await
            .context("connessione al bus di sessione")?;

        let remoto = RemoteDesktopProxy::new(&connessione)
            .await
            .context("Mutter non espone RemoteDesktop: la sessione grafica e' avviata?")?;

        // L'attesa va tenuta fuori dalla macro di registro: dentro, il valore
        // temporaneo resterebbe vivo attraverso l'attesa.
        let versione = remoto.version().await.unwrap_or(-1);

        let percorso = remoto
            .create_session()
            .await
            .context("creazione della sessione RemoteDesktop")?;

        let sessione = SessioneRemotaProxy::builder(&connessione)
            .path(percorso.clone())?
            .build()
            .await?;

        let id = sessione
            .session_id()
            .await
            .context("lettura di SessionId")?;

        // Ci si mette in ascolto della chiusura **prima** di avviare: e' la
        // stessa cautela della cattura, dove un segnale emesso durante l'avvio
        // andrebbe perduto se lo si aspettasse dopo.
        let mut chiusure = sessione.receive_closed().await?;

        // Mutter chiude la sessione da se' quando il compositore se ne va o
        // quando qualcosa non gli torna. Se non lo si sapesse, si continuerebbe
        // a spedire eventi a un oggetto che non c'e' piu': la spia qui sotto
        // permette alla connessione successiva di rifarla invece di ereditarla
        // morta.
        let viva = Arc::new(AtomicBool::new(true));
        let congedata = Arc::new(AtomicBool::new(false));
        let spia = Arc::clone(&viva);
        let per_spia = Arc::clone(&congedata);
        tokio::spawn(async move {
            use futures_util::StreamExt as _;
            let _ = chiusure.next().await;
            spia.store(false, Ordering::Release);
            if per_spia.load(Ordering::Acquire) {
                debug!("la sessione di controllo si e' chiusa come chiesto");
            } else {
                warn!("Mutter ha chiuso la sessione di controllo");
            }
        });

        info!(versione, sessione = %percorso, id = %id, "controllo preparato");

        Ok(Self {
            connessione,
            sessione,
            id,
            viva,
            congedata,
        })
    }

    /// Avvia la sessione, dopo che la cattura vi si e' registrata.
    async fn avvia(&self) -> Result<()> {
        self.sessione
            .start()
            .await
            .context("avvio della sessione RemoteDesktop")
    }

    fn viva(&self) -> bool {
        self.viva.load(Ordering::Acquire)
    }

    /// Marca la sessione da rifare quando l'errore dice che non c'e' piu'.
    ///
    /// Un errore di metodo — «flusso inesistente», per esempio, che capita
    /// normalmente subito dopo un ridimensionamento — non significa che la
    /// sessione sia morta: si segnala e si prosegue. Un errore di trasporto, o
    /// un oggetto che il bus non conosce piu', significa invece che va rifatta.
    fn valuta(&self, errore: &zbus::Error) {
        let irrimediabile = match errore {
            zbus::Error::MethodError(nome, _, _) => {
                let nome = nome.as_str();
                nome.ends_with("UnknownObject")
                    || nome.ends_with("ServiceUnknown")
                    || nome.ends_with("UnknownInterface")
            }
            zbus::Error::InputOutput(_) | zbus::Error::Unsupported => true,
            _ => false,
        };
        if irrimediabile {
            self.viva.store(false, Ordering::Release);
        }
    }
}

impl Drop for SessioneControllo {
    /// Chiude la sessione senza attendere.
    ///
    /// Attendere qui fermerebbe il thread che lascia cadere l'oggetto — la
    /// regola 7 di `SPECIFICA.md` §5.7 vale anche per le attese nascoste dentro
    /// un `Drop`. Si manda la chiusura e si prosegue: se non arriva, la sessione
    /// muore comunque con il processo.
    fn drop(&mut self) {
        // Si dichiara prima di chiedere, cosi' la spia trova gia' la risposta
        // quando il segnale di chiusura le arriva.
        self.congedata.store(true, Ordering::Release);
        // `tokio::spawn` va in panico senza un runtime in esecuzione, e un
        // panico dentro un `Drop` abortisce il processo: si verifica prima.
        // Alla chiusura del server non c'e' comunque nulla da chiudere.
        if let Ok(runtime) = tokio::runtime::Handle::try_current() {
            let sessione = self.sessione.clone();
            runtime.spawn(async move {
                let _ = sessione.stop().await;
            });
        }
    }
}

// ---------------------------------------------------------------------------
// Il controllo, visto da fuori
// ---------------------------------------------------------------------------

/// Una sessione di controllo creata e non ancora avviata.
///
/// Esiste solo per rendere impossibile sbagliare l'ordine: da qui si puo' solo
/// leggere il contesto — cio' che serve alla cattura per registrarsi — e la
/// sessione si avvia passandola a [`Controllo::attiva`], che e' l'ultimo dei
/// quattro passi.
pub struct Preparazione {
    sessione: Arc<SessioneControllo>,
}

impl Preparazione {
    /// Cio' che la cattura deve dichiarare per farsi registrare, e con cui
    /// avviera' il controllo al momento giusto.
    pub fn contesto(&self) -> Contesto {
        Contesto {
            connessione: self.sessione.connessione.clone(),
            id_sessione: self.sessione.id.clone(),
            sessione: Arc::clone(&self.sessione),
        }
    }
}

/// Il punto d'ingresso dell'input, condiviso fra il server e la sorgente.
pub struct Controllo {
    eventi: mpsc::UnboundedSender<Evento>,
    sessione_tx: watch::Sender<Option<Arc<SessioneControllo>>>,
    bersaglio_tx: watch::Sender<Option<Bersaglio>>,
}

impl Controllo {
    /// Prepara il controllo e avvia il compito che parla con il compositore.
    ///
    /// Non tocca ancora D-Bus: la sessione si apre alla prima connessione, cosi'
    /// il server puo' partire anche prima della sessione grafica.
    pub fn nuovo() -> Arc<Self> {
        let (eventi_tx, eventi_rx) = mpsc::unbounded_channel();
        let (sessione_tx, sessione_rx) = watch::channel(None);
        let (bersaglio_tx, bersaglio_rx) = watch::channel(None);

        tokio::spawn(consegna(eventi_rx, sessione_rx, bersaglio_rx));

        Arc::new(Self {
            eventi: eventi_tx,
            sessione_tx,
            bersaglio_tx,
        })
    }

    /// Primo passo: crea la sessione di controllo, senza avviarla.
    ///
    /// Un fallimento non e' fatale: si restituisce `None` e la cattura procede
    /// per conto suo. Vedere il desktop senza poterlo comandare e' meglio che
    /// non vedere nulla, e il registro dice perche'.
    pub async fn prepara(&self) -> Option<Preparazione> {
        match SessioneControllo::crea().await {
            Ok(sessione) => Some(Preparazione {
                sessione: Arc::new(sessione),
            }),
            Err(errore) => {
                warn!(
                    errore = %format!("{errore:#}"),
                    "controllo non disponibile: la sessione sara' di sola visione"
                );
                None
            }
        }
    }

    /// Ultimo passo: dichiara dove muovere il puntatore e apre le porte agli
    /// eventi.
    ///
    /// Da chiamare **dopo** che la cattura si e' registrata e il flusso e'
    /// partito. Il flusso cambia a ogni ridimensionamento, quindi anche questa
    /// chiamata si ripete.
    pub fn attiva(&self, pronta: Preparazione, flusso: String, size: DesktopSize) {
        debug!(%flusso, larghezza = size.width, altezza = size.height, "bersaglio del puntatore");
        // Prima il bersaglio, poi la sessione: cosi' non esiste un istante in
        // cui il puntatore ha una sessione a cui parlare ma non un flusso in cui
        // muoversi.
        let _ = self.bersaglio_tx.send(Some(Bersaglio { flusso, size }));
        let _ = self.sessione_tx.send(Some(pronta.sessione));

        // Subito dopo, il colpo a vuoto che fa esistere la tastiera virtuale:
        // vedere `Evento::Innesca`. Va fatto adesso, mentre nessuno sta ancora
        // scrivendo, non quando la prima lettera dell'utente lo scoprirebbe a
        // proprie spese.
        let _ = self.eventi.send(Evento::Innesca);
    }

    /// Vero se c'e' una sessione di controllo viva, con il suo bersaglio.
    ///
    /// Serve al palco per decidere se rimontare la coppia o riusarla: la
    /// cattura da sola non basta a dire che l'input funzioni, perche' le due
    /// cose vivono e muoiono insieme (§5.8 regola 1) e una sessione che Mutter
    /// ha chiuso per conto suo lascerebbe un palco a meta'.
    pub fn attivo(&self) -> bool {
        self.sessione_tx
            .borrow()
            .as_ref()
            .is_some_and(|s| s.viva())
            && self.bersaglio_tx.borrow().is_some()
    }

    /// Lascia cadere la sessione di controllo e il suo bersaglio.
    ///
    /// Da chiamare prima di rifare la coppia: la sessione vecchia si chiude da
    /// se' quando l'ultimo riferimento cade.
    pub fn stacca(&self) {
        let _ = self.bersaglio_tx.send(None);
        let _ = self.sessione_tx.send(None);
    }

    /// Rilascia tutto cio' che risulta premuto.
    ///
    /// Da chiamare quando una connessione finisce: senza, un modificatore
    /// tenuto giu' al momento dello stacco resta premuto nella sessione per
    /// sempre, e il desktop diventa inutilizzabile anche da vicino.
    pub fn rilascia_tutto(&self) {
        let _ = self.eventi.send(Evento::Rilascia);
    }

    fn accoda(&self, evento: Evento) {
        // L'invio su un canale non limitato non attende mai: e' il requisito
        // che permette di chiamarlo da dentro il ciclo di IronRDP.
        let _ = self.eventi.send(evento);
    }
}

// ---------------------------------------------------------------------------
// Il gestore che IronRDP chiama
// ---------------------------------------------------------------------------

/// Traduce gli eventi di IronRDP e li accoda. Non attende nulla.
pub struct GestoreInput {
    controllo: Arc<Controllo>,
    /// Chi ha superato PAM. Senza, gli eventi non si inoltrano.
    ///
    /// Difesa in profondita': la connessione non autenticata viene gia' chiusa
    /// dal display, ma fra l'arrivo degli eventi e quella chiusura passa un
    /// istante — e in quell'istante nessuno deve poter comandare il desktop di
    /// qualcun altro.
    guardia: Arc<crate::autenticazione::Guardia>,
}

impl GestoreInput {
    pub fn nuovo(controllo: Arc<Controllo>, guardia: Arc<crate::autenticazione::Guardia>) -> Self {
        Self { controllo, guardia }
    }
}

impl GestoreInput {
    /// Vero se questa connessione ha superato PAM.
    ///
    /// Gli eventi di chi non e' autenticato non si inoltrano **e non si
    /// registrano**: sono comunque battute di tastiera, e il registro non e' il
    /// posto dove finirle.
    fn ammesso(&self) -> bool {
        if self.guardia.concesso() {
            return true;
        }
        trace!("evento da una connessione non autenticata, scartato");
        false
    }
}

impl RdpServerInputHandler for GestoreInput {
    fn keyboard(&mut self, evento: KeyboardEvent) {
        if !self.ammesso() {
            return;
        }
        match evento {
            KeyboardEvent::Pressed { code, extended } => {
                self.premi(code, extended, true);
            }
            KeyboardEvent::Released { code, extended } => {
                self.premi(code, extended, false);
            }
            KeyboardEvent::UnicodePressed(unita) => self.carattere(unita, true),
            KeyboardEvent::UnicodeReleased(unita) => self.carattere(unita, false),
            KeyboardEvent::Synchronize(flag) => {
                self.controllo.accoda(Evento::Blocchi(flag));
            }
        }
    }

    fn mouse(&mut self, evento: MouseEvent) {
        if !self.ammesso() {
            return;
        }
        // L'evento com'e' arrivato, prima di qualunque nostra elaborazione.
        // Serve a distinguere cio' che il client manda da cio' che noi
        // consegniamo: senza, un puntatore che arriva in ritardo sembra un
        // difetto nostro tanto quanto uno del client, e i due si correggono in
        // posti diversi.
        trace!(?evento, "evento del mouse in arrivo");
        let evento = match evento {
            MouseEvent::Move { x, y } => Evento::Muovi { x, y },
            MouseEvent::RelMove { x, y } => Evento::MuoviRelativo { dx: x, dy: y },
            MouseEvent::LeftPressed => bottone(BTN_LEFT, true),
            MouseEvent::LeftReleased => bottone(BTN_LEFT, false),
            MouseEvent::RightPressed => bottone(BTN_RIGHT, true),
            MouseEvent::RightReleased => bottone(BTN_RIGHT, false),
            MouseEvent::MiddlePressed => bottone(BTN_MIDDLE, true),
            MouseEvent::MiddleReleased => bottone(BTN_MIDDLE, false),
            MouseEvent::Button4Pressed => bottone(BTN_SIDE, true),
            MouseEvent::Button4Released => bottone(BTN_SIDE, false),
            MouseEvent::Button5Pressed => bottone(BTN_EXTRA, true),
            MouseEvent::Button5Released => bottone(BTN_EXTRA, false),

            // La rotella per la via ordinaria di RDP.
            MouseEvent::VerticalScroll { value } => asse(0.0, f64::from(value)),

            // La rotella per il canale di input avanzato, che i client di
            // FreeRDP preferiscono quando c'e': stesse unita', moltiplicate.
            // Di qui passa anche lo scorrimento orizzontale, che per la via
            // ordinaria IronRDP non consegna affatto.
            MouseEvent::Scroll { x, y } => asse(
                f64::from(x) / RISOLUZIONE_AINPUT,
                f64::from(y) / RISOLUZIONE_AINPUT,
            ),
        };
        self.controllo.accoda(evento);
    }
}

impl GestoreInput {
    fn premi(&mut self, codice: u8, esteso: bool, premuto: bool) {
        match tastiera::evdev_da_scancode(codice, esteso) {
            Some(evdev) => self.controllo.accoda(Evento::Tasto { evdev, premuto }),
            None => debug!(codice, esteso, "posizione di tastiera sconosciuta, ignorata"),
        }
    }

    fn carattere(&mut self, unita: u16, premuto: bool) {
        match tastiera::keysym_da_unicode(unita) {
            Some(keysym) => self.controllo.accoda(Evento::Carattere { keysym, premuto }),
            None => debug!(unita, "carattere senza keysym, ignorato"),
        }
    }
}

fn bottone(codice: i32, premuto: bool) -> Evento {
    Evento::Bottone { codice, premuto }
}

/// Converte le unita' di rotella di RDP nei passi che Mutter si aspetta.
///
/// I due assi non si comportano allo stesso modo, e non e' una svista:
///
///   - **verticale**: RDP conta positivo verso l'alto, Wayland verso il basso,
///     quindi il segno si inverte;
///   - **orizzontale**: entrambi contano positivo verso destra, e il segno
///     resta.
///
/// Lo stesso fa `gnome-remote-desktop`, che e' dove si e' andati a controllare
/// invece di tirare a indovinare su quale dei due assi vada girato.
fn asse(unita_x: f64, unita_y: f64) -> Evento {
    Evento::Asse {
        dx: unita_x / UNITA_PER_SCATTO * PASSO_ASSE,
        dy: -unita_y / UNITA_PER_SCATTO * PASSO_ASSE,
        rotella: true,
    }
}

// Qui viveva `GestoreConnessioni`, che implementava `ConnectionHandler` di
// IronRDP per rilasciare i tasti a fine connessione. E' stato tolto quando
// l'accettazione e' passata a `portiere.rs`: quel gancio lo chiama il ciclo
// `RdpServer::run()`, che non usiamo piu', quindi sarebbe rimasto li' a
// **sembrare** attivo. Il rilascio ora lo esegue il portiere, che e' chi sa
// davvero quando una connessione e' finita.

// ---------------------------------------------------------------------------
// Il compito che consegna al compositore
// ---------------------------------------------------------------------------

/// Cio' che risulta premuto, per poterlo rilasciare a fine connessione.
struct Premuti {
    tasti: HashSet<u16>,
    caratteri: HashSet<u32>,
    bottoni: HashSet<i32>,
    /// Stato dei tasti a scatto come lo crediamo dentro la sessione.
    ///
    /// La sessione grafica la avvia REMOTIX, quindi al principio i tre sono
    /// spenti: e' l'unico momento in cui lo si sa con certezza, e da li' si
    /// tiene il conto.
    blocchi: SynchronizeFlags,
}

impl Default for Premuti {
    fn default() -> Self {
        Self {
            tasti: HashSet::new(),
            caratteri: HashSet::new(),
            bottoni: HashSet::new(),
            blocchi: SynchronizeFlags::empty(),
        }
    }
}

async fn consegna(
    mut eventi: mpsc::UnboundedReceiver<Evento>,
    sessione: watch::Receiver<Option<Arc<SessioneControllo>>>,
    bersaglio: watch::Receiver<Option<Bersaglio>>,
) {
    let mut premuti = Premuti::default();
    let mut lotto: Vec<Evento> = Vec::with_capacity(ACCORPAMENTO_MASSIMO);

    while let Some(primo) = eventi.recv().await {
        lotto.push(primo);
        while lotto.len() < ACCORPAMENTO_MASSIMO {
            match eventi.try_recv() {
                Ok(altro) => lotto.push(altro),
                Err(_) => break,
            }
        }

        for indice in 0..lotto.len() {
            // Uno spostamento subito seguito da un altro non serve a nessuno:
            // conta dove il puntatore arriva, non la strada che ha fatto. I
            // client ne mandano a raffica, e ciascuno costerebbe un giro sul
            // bus. Si scarta solo quando il successivo e' ancora uno
            // spostamento: se in mezzo c'e' un clic, la posizione conta eccome.
            if matches!(lotto[indice], Evento::Muovi { .. })
                && matches!(lotto.get(indice + 1), Some(Evento::Muovi { .. }))
            {
                continue;
            }

            let corrente = sessione.borrow().clone();
            let mira = bersaglio.borrow().clone();
            applica(
                corrente.as_deref(),
                mira.as_ref(),
                &lotto[indice],
                &mut premuti,
            )
            .await;
        }

        lotto.clear();
    }
}

async fn applica(
    sessione: Option<&SessioneControllo>,
    bersaglio: Option<&Bersaglio>,
    evento: &Evento,
    premuti: &mut Premuti,
) {
    // Il rilascio si applica **sempre**, anche quando non c'e' piu' una
    // sessione a cui parlare: il suo effetto principale e' dimenticare cio' che
    // crediamo premuto, e quel ricordo sopravvive alla connessione.
    //
    // Trattarlo come gli altri eventi — buttandolo in mancanza di sessione — e'
    // il difetto che si e' trovato in prova: a connessione finita la sessione e'
    // gia' staccata, quindi il rilascio non avveniva mai e lo stato restava
    // sporco. Alla connessione successiva il primo colpo su un tasto che
    // risultava ancora premuto veniva ingoiato, e la lettera non compariva.
    if matches!(evento, Evento::Rilascia) {
        rilascia_tutto(sessione, premuti).await;
        return;
    }

    // Fuori dal rilascio, senza sessione non c'e' nulla da fare: gli eventi si
    // buttano. Vale anche per una sessione che Mutter ha gia' chiuso, che li
    // rifiuterebbe uno per uno con lo stesso errore.
    let Some(sessione) = sessione.filter(|s| s.viva()) else {
        return;
    };

    let esito = match evento {
        Evento::Tasto { evdev, premuto } => {
            // Mutter rifiuta con `Invalid key event` sia il rilascio di un tasto
            // che non risulta premuto, sia la pressione di uno che lo e' gia'.
            // I client mandano regolarmente l'uno e l'altra: il rilascio quando
            // riprendono il fuoco — l'utente ha alzato il dito altrove, e loro
            // lo dicono per non lasciarlo appeso — e la pressione ripetuta
            // finche' il tasto resta giu'. Nessuna delle due va inoltrata: la
            // ripetizione la genera il compositore per conto suo.
            // A `trace` e non a `debug`, e non e' pignoleria: l'elenco dei
            // tasti premuti **e' cio' che l'utente sta scrivendo**, password
            // comprese. Chi lo accende deve farlo apposta, sapendo che sta
            // registrando le battute; a `debug` se lo troverebbe addosso
            // chiedendo tutt'altro.
            if *premuto == premuti.tasti.contains(evdev) {
                trace!(evdev, premuto, "tasto gia' in quello stato, ignorato");
                return;
            }
            trace!(evdev, premuto, "tasto");
            if *premuto {
                premuti.tasti.insert(*evdev);
            } else {
                premuti.tasti.remove(evdev);
            }
            // Il tasto a scatto cambia stato a ogni pressione: si tiene il
            // conto, altrimenti la sincronizzazione successiva lo invertirebbe.
            if *premuto
                && let Some(flag) = flag_di_blocco(*evdev)
            {
                premuti.blocchi ^= flag;
            }
            sessione
                .sessione
                .notify_keyboard_keycode(u32::from(*evdev), *premuto)
                .await
        }

        Evento::Carattere { keysym, premuto } => {
            if *premuto == premuti.caratteri.contains(keysym) {
                return;
            }
            if *premuto {
                premuti.caratteri.insert(*keysym);
            } else {
                premuti.caratteri.remove(keysym);
            }
            sessione
                .sessione
                .notify_keyboard_keysym(*keysym, *premuto)
                .await
        }

        Evento::Blocchi(voluti) => {
            return sincronizza_blocchi(sessione, *voluti, premuti).await;
        }

        Evento::Muovi { x, y } => {
            let Some(bersaglio) = bersaglio else {
                // La cattura non e' ancora aperta: non c'e' dove muoversi.
                return;
            };
            // Il client puo' mandare coordinate della misura precedente nei
            // millisecondi che seguono un ridimensionamento: si riportano
            // dentro il bordo invece di lasciare che Mutter le rifiuti.
            let x = f64::from((*x).min(bersaglio.size.width.saturating_sub(1)));
            let y = f64::from((*y).min(bersaglio.size.height.saturating_sub(1)));
            // Tracciare la coordinata consegnata e' l'unico modo di distinguere
            // un puntatore che va dove deve da un client che manda coordinate
            // sue: il puntatore disegnato nell'immagine e' l'esito di entrambe
            // le cose insieme.
            debug!(x, y, "puntatore");
            sessione
                .sessione
                .notify_pointer_motion_absolute(&bersaglio.flusso, x, y)
                .await
        }

        Evento::MuoviRelativo { dx, dy } => {
            sessione
                .sessione
                .notify_pointer_motion_relative(f64::from(*dx), f64::from(*dy))
                .await
        }

        Evento::Bottone { codice, premuto } => {
            if *premuto {
                premuti.bottoni.insert(*codice);
            } else {
                premuti.bottoni.remove(codice);
            }
            debug!(codice, premuto, "bottone");
            sessione
                .sessione
                .notify_pointer_button(*codice, *premuto)
                .await
        }

        Evento::Asse { dx, dy, rotella } => {
            let flag = if *rotella { ASSE_ROTELLA } else { 0 };
            debug!(dx, dy, rotella, "asse");
            sessione.sessione.notify_pointer_axis(*dx, *dy, flag).await
        }

        Evento::Innesca => {
            // Non passa dal conto dei tasti premuti: non e' una battuta
            // dell'utente, e non deve finire fra le cose da rilasciare.
            debug!("innesco della tastiera virtuale");
            match sessione.sessione.notify_keyboard_keycode(0, true).await {
                Ok(()) => sessione.sessione.notify_keyboard_keycode(0, false).await,
                Err(e) => Err(e),
            }
        }

        // Trattato in cima, prima ancora di verificare che una sessione ci sia.
        Evento::Rilascia => return,
    };

    if let Err(errore) = esito {
        // Si nomina il genere dell'evento, non il suo contenuto: se la sessione
        // si rompe mentre qualcuno scrive, un `?evento` riverserebbe nel
        // registro tasto per tasto quello che sta scrivendo.
        warn!(errore = %errore, evento = evento.genere(), "consegna dell'evento fallita");
        sessione.valuta(&errore);
    }
}

/// Porta i tasti a scatto nello stato dichiarato dal client.
///
/// RDP annuncia lo stato di Bloc Maiusc, Bloc Num e Bloc Scorr all'aggancio e
/// ogni volta che il client riprende il fuoco. Non esiste un modo di *imporlo*:
/// si preme il tasto quando lo stato che crediamo non corrisponde.
async fn sincronizza_blocchi(
    sessione: &SessioneControllo,
    voluti: SynchronizeFlags,
    premuti: &mut Premuti,
) {
    let scatti = [
        (SynchronizeFlags::CAPS_LOCK, tastiera::EVDEV_BLOC_MAIUSC),
        (SynchronizeFlags::NUM_LOCK, tastiera::EVDEV_BLOC_NUM),
        (SynchronizeFlags::SCROLL_LOCK, tastiera::EVDEV_BLOC_SCORR),
    ];

    for (flag, evdev) in scatti {
        if voluti.contains(flag) == premuti.blocchi.contains(flag) {
            continue;
        }
        debug!(evdev, acceso = voluti.contains(flag), "allineo un tasto a scatto");
        for premuto in [true, false] {
            if let Err(errore) = sessione
                .sessione
                .notify_keyboard_keycode(u32::from(evdev), premuto)
                .await
            {
                warn!(errore = %errore, "sincronizzazione dei blocchi fallita");
                sessione.valuta(&errore);
                return;
            }
        }
        premuti.blocchi ^= flag;
    }
}

async fn rilascia_tutto(sessione: Option<&SessioneControllo>, premuti: &mut Premuti) {
    let tasti: Vec<u16> = premuti.tasti.drain().collect();
    let caratteri: Vec<u32> = premuti.caratteri.drain().collect();
    let bottoni: Vec<i32> = premuti.bottoni.drain().collect();

    if tasti.is_empty() && caratteri.is_empty() && bottoni.is_empty() {
        return;
    }
    info!(
        tasti = tasti.len(),
        caratteri = caratteri.len(),
        bottoni = bottoni.len(),
        sessione = sessione.is_some(),
        "rilascio quel che era rimasto premuto"
    );

    // Senza sessione basta aver dimenticato: la tastiera virtuale se n'e'
    // andata insieme a essa, quindi non c'e' nessun tasto da alzare.
    let Some(sessione) = sessione else {
        return;
    };

    for evdev in tasti {
        let _ = sessione
            .sessione
            .notify_keyboard_keycode(u32::from(evdev), false)
            .await;
    }
    for keysym in caratteri {
        let _ = sessione
            .sessione
            .notify_keyboard_keysym(keysym, false)
            .await;
    }
    for codice in bottoni {
        let _ = sessione.sessione.notify_pointer_button(codice, false).await;
    }
}

fn flag_di_blocco(evdev: u16) -> Option<SynchronizeFlags> {
    match evdev {
        tastiera::EVDEV_BLOC_MAIUSC => Some(SynchronizeFlags::CAPS_LOCK),
        tastiera::EVDEV_BLOC_NUM => Some(SynchronizeFlags::NUM_LOCK),
        tastiera::EVDEV_BLOC_SCORR => Some(SynchronizeFlags::SCROLL_LOCK),
        _ => None,
    }
}
