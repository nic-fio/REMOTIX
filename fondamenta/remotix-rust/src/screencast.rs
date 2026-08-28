//! Sessione di cattura verso Mutter (`org.gnome.Mutter.ScreenCast`).
//!
//! # Perche' l'interfaccia diretta e non il portale
//!
//! La specifica di REMOTIX sceglie le interfacce D-Bus dirette del compositore
//! invece di `xdg-desktop-portal`: il portale e' pensato per le applicazioni
//! che chiedono il permesso a un utente gia' seduto davanti allo schermo, e
//! richiede un'interazione che in una sessione senza monitor non puo'
//! avvenire. REMOTIX avvia lui stesso la sessione: e' il caso d'uso di
//! `gnome-remote-desktop`, che infatti usa la stessa via.
//!
//! # La regola che governa tutto
//!
//! La sessione vive quanto la connessione D-Bus di chi l'ha creata. Se il
//! processo si disconnette dal bus, Mutter chiude la sessione e il flusso
//! PipeWire muore senza preavviso. Per questo la `Connection` e' conservata
//! dentro la struttura e non va lasciata cadere: e' l'unico motivo per cui il
//! campo esiste.
//!
//! # Il collegamento con l'input, e cio' che ha cambiato
//!
//! Perche' il puntatore possa muoversi dentro questa cattura, la sessione va
//! creata dichiarando l'identificativo della sessione di controllo — vedere
//! `controllo.rs` — e sulla **stessa connessione D-Bus** di quella, che Mutter
//! verifica quando riceve gli eventi.
//!
//! Quella connessione vive quanto il server, non quanto la singola cattura.
//! Ne discende che **non ci si puo' piu' affidare alla caduta della connessione
//! per chiudere le catture**: senza una chiusura esplicita, ogni
//! ridimensionamento lascerebbe a Mutter un monitor virtuale in piu'. Di qui il
//! `Drop` in fondo, che manda la chiusura senza attenderla.
//!
//! Senza controllo — quando la sessione di input non si e' potuta aprire — si
//! torna al comportamento di prima: connessione propria, che chiude tutto
//! cadendo.

use std::collections::HashMap;

use anyhow::{Context as _, Result};
use futures_util::StreamExt as _;
use tracing::info;
use zbus::zvariant::{OwnedObjectPath, Value};
use zbus::{Connection, proxy};

use crate::controllo::Contesto;

/// Come Mutter deve trattare il puntatore del mouse.
///
/// I valori sono quelli di `MetaScreenCastCursorMode`.
#[derive(Clone, Copy, Debug)]
pub enum Cursore {
    /// Non compare affatto.
    Nascosto = 0,
    /// Disegnato dentro l'immagine catturata.
    ///
    /// **Non piu' usato dalla fase 4.** Costava un fotogramma H.264 intero per
    /// ogni singolo movimento del mouse, ed e' stato la ragione principale per
    /// cui lo scorrimento sembrava quello di xrdp. Resta qui perche' e' la
    /// scelta giusta per chi cattura senza avere un client a cui delegare il
    /// disegno del puntatore — per esempio `prova-cattura`.
    Incorporato = 1,
    /// Inviato a parte come metadato, senza toccare l'immagine.
    ///
    /// E' la scelta di REMOTIX dalla fase 4: il video cambia solo quando cambia
    /// il desktop, e il puntatore lo disegna il client — all'istante, senza
    /// aspettare un giro sulla rete.
    ///
    /// **Il metadato non viene ancora letto**: al client si dice di usare la
    /// propria freccia predefinita, quindi la forma non cambia sopra il testo o
    /// sui bordi delle finestre. Leggerlo richiede le associazioni grezze di
    /// PipeWire, perche' il pacchetto Rust non espone i metadati del buffer.
    Metadato = 2,
}

#[proxy(
    interface = "org.gnome.Mutter.ScreenCast",
    default_service = "org.gnome.Mutter.ScreenCast",
    default_path = "/org/gnome/Mutter/ScreenCast"
)]
trait ScreenCast {
    fn create_session(&self, proprieta: HashMap<&str, Value<'_>>) -> zbus::Result<OwnedObjectPath>;

    #[zbus(property)]
    fn version(&self) -> zbus::Result<i32>;
}

#[proxy(
    interface = "org.gnome.Mutter.ScreenCast.Session",
    default_service = "org.gnome.Mutter.ScreenCast"
)]
trait Sessione {
    fn record_monitor(
        &self,
        connettore: &str,
        proprieta: HashMap<&str, Value<'_>>,
    ) -> zbus::Result<OwnedObjectPath>;

    fn record_virtual(
        &self,
        proprieta: HashMap<&str, Value<'_>>,
    ) -> zbus::Result<OwnedObjectPath>;

    fn start(&self) -> zbus::Result<()>;
    fn stop(&self) -> zbus::Result<()>;
}

#[proxy(
    interface = "org.gnome.Mutter.ScreenCast.Stream",
    default_service = "org.gnome.Mutter.ScreenCast"
)]
trait Flusso {
    fn start(&self) -> zbus::Result<()>;

    #[zbus(signal)]
    fn pipe_wire_stream_added(&self, nodo: u32) -> zbus::Result<()>;
}

/// Sessione di cattura aperta, con il nodo PipeWire da cui leggere.
pub struct SessioneCattura {
    /// Tiene viva la connessione: se cade, Mutter chiude la sessione.
    _connessione: Connection,
    sessione: SessioneProxy<'static>,
    /// Nodo PipeWire da cui arrivano i fotogrammi.
    pub nodo: u32,
    /// Percorso D-Bus del flusso.
    ///
    /// E' l'indirizzo a cui il puntatore si muove: `NotifyPointerMotionAbsolute`
    /// vuole proprio questo, non il nodo PipeWire.
    pub percorso_flusso: String,
    /// Vero quando la chiusura e' gia' stata chiesta esplicitamente.
    chiusa: bool,
    /// Vero quando la cattura e' associata a una sessione di controllo.
    ///
    /// Cambia chi la ferma, esattamente come cambia chi la avvia: una cattura
    /// legata rifiuta `Session.Stop` con `Must be stopped from remote desktop
    /// session`, e si chiude fermando il controllo.
    legata: bool,
}

/// Che cosa si riprende.
#[derive(Clone, Debug)]
pub enum Sorgente {
    /// Un monitor gia' esistente, indicato dal suo connettore.
    ///
    /// In una sessione senza schermo il monitor virtuale creato da
    /// `gnome-shell --virtual-monitor` si chiama `Meta-0`.
    Monitor(String),
    /// Un monitor virtuale creato da Mutter apposta per noi.
    ///
    /// E' la forma che REMOTIX usa davvero, per due motivi indipendenti che
    /// puntano nella stessa direzione:
    ///
    ///   - **la risoluzione la decide chi guarda.** La dimensione si concorda
    ///     nella negoziazione PipeWire, quindi il desktop puo' adattarsi alla
    ///     finestra del client invece di imporgli una misura fissa;
    ///   - **evita di bloccare Xwayland.** Un monitor virtuale chiesto sulla
    ///     riga di comando di `gnome-shell` impedisce a Xwayland di completare
    ///     l'avvio, e il compositore resta appeso (vedi SPECIFICA.md §5.6).
    ///     Chiedendolo a compositore gia' avviato, il problema non si presenta.
    Virtuale,
}

impl SessioneCattura {
    /// Apre una sessione di cattura su un monitor virtuale creato al momento.
    ///
    /// Con un `Contesto` la cattura viene associata alla sessione di controllo,
    /// che e' la condizione perche' il puntatore possa muovercisi dentro. Senza,
    /// si ottiene una cattura di sola visione.
    pub async fn virtuale(cursore: Cursore, controllo: Option<&Contesto>) -> Result<Self> {
        Self::apri(Sorgente::Virtuale, cursore, controllo).await
    }

    /// Apre una sessione che riprende un monitor esistente.
    pub async fn su_monitor(
        connettore: &str,
        cursore: Cursore,
        controllo: Option<&Contesto>,
    ) -> Result<Self> {
        Self::apri(Sorgente::Monitor(connettore.to_owned()), cursore, controllo).await
    }

    async fn apri(
        sorgente: Sorgente,
        cursore: Cursore,
        controllo: Option<&Contesto>,
    ) -> Result<Self> {
        // Con il controllo si riusa la sua connessione, perche' Mutter pretende
        // che gli eventi di input arrivino dallo stesso peer che ha creato la
        // sessione di controllo; senza, se ne apre una propria, che chiudendosi
        // porta con se' la cattura.
        let connessione = match controllo {
            Some(contesto) => contesto.connessione.clone(),
            None => Connection::session()
                .await
                .context("connessione al bus di sessione")?,
        };

        let screencast = ScreenCastProxy::new(&connessione)
            .await
            .context("Mutter non espone ScreenCast: la sessione grafica e' avviata?")?;

        // L'attesa va tenuta fuori dalla macro: dentro, il valore temporaneo
        // che costruisce resterebbe vivo attraverso l'attesa e renderebbe
        // l'intera funzione non trasferibile fra thread.
        let versione = screencast.version().await.unwrap_or(-1);
        info!(versione, "ScreenCast di Mutter");

        let mut proprieta_sessione = HashMap::new();
        if let Some(contesto) = controllo {
            proprieta_sessione.insert(
                "remote-desktop-session-id",
                Value::from(contesto.id_sessione.as_str()),
            );
        }
        let percorso_sessione = screencast
            .create_session(proprieta_sessione)
            .await
            .context("creazione della sessione ScreenCast")?;

        let sessione = SessioneProxy::builder(&connessione)
            .path(percorso_sessione.clone())?
            .build()
            .await?;

        // Il controllo si avvia qui, in mezzo: dopo che la cattura si e'
        // registrata su di esso — a controllo gia' avviato Mutter la
        // rifiuterebbe — e prima che il flusso parta, perche' e' l'avvio del
        // controllo a mettere in moto la sessione di cattura associata.
        if let Some(contesto) = controllo {
            contesto.avvia_controllo().await?;
        }

        let mut proprieta = HashMap::new();
        proprieta.insert("cursor-mode", Value::from(cursore as u32));
        let percorso_flusso = match &sorgente {
            Sorgente::Monitor(connettore) => sessione
                .record_monitor(connettore, proprieta)
                .await
                .with_context(|| format!("nessun monitor chiamato '{connettore}'"))?,
            Sorgente::Virtuale => sessione
                .record_virtual(proprieta)
                .await
                .context("creazione del monitor virtuale")?,
        };

        let flusso = FlussoProxy::builder(&connessione)
            .path(percorso_flusso.clone())?
            .build()
            .await?;

        // Il nodo arriva con un segnale che Mutter emette durante l'avvio:
        // ci si mette in ascolto PRIMA, altrimenti si perde e si resta ad
        // aspettare per sempre un annuncio gia' passato.
        let mut annunci = flusso.receive_pipe_wire_stream_added().await?;

        // Chi avvia dipende da chi comanda. Una cattura legata a un controllo
        // rifiuta `Session.Start` con `Must be started from remote desktop
        // session`: li' la sessione l'ha gia' messa in moto l'avvio del
        // controllo, e resta da far partire il singolo flusso. Senza controllo
        // vale la via di sempre.
        match controllo {
            Some(_) => flusso.start().await.context("avvio del flusso ScreenCast")?,
            None => sessione
                .start()
                .await
                .context("avvio della sessione ScreenCast")?,
        }

        let annuncio = tokio::time::timeout(std::time::Duration::from_secs(10), annunci.next())
            .await
            .context("Mutter non ha annunciato il nodo PipeWire entro 10 secondi")?
            .context("il flusso e' stato chiuso prima di annunciare il nodo")?;
        let nodo = annuncio.args()?.nodo;

        info!(
            nodo,
            ?sorgente,
            controllo = controllo.is_some(),
            sessione = %percorso_sessione,
            flusso = %percorso_flusso,
            "cattura avviata"
        );

        Ok(Self {
            _connessione: connessione,
            sessione,
            nodo,
            percorso_flusso: percorso_flusso.as_str().to_owned(),
            chiusa: false,
            legata: controllo.is_some(),
        })
    }

    /// Chiude la sessione in modo ordinato.
    ///
    /// Senza controllo questa chiamata **non e' facoltativa**: la connessione
    /// e' quella condivisa, che vive quanto il server, quindi nessuno
    /// chiuderebbe la sessione al posto nostro e a ogni ridimensionamento
    /// resterebbe a Mutter un monitor virtuale in piu'.
    ///
    /// Con il controllo, invece, non c'e' nulla da chiudere qui: se ne occupa
    /// la chiusura del controllo, ed e' l'unica che Mutter accetti.
    pub async fn chiudi(mut self) {
        self.chiusa = true;
        if self.legata {
            return;
        }
        if let Err(e) = self.sessione.stop().await {
            tracing::warn!(errore = %e, "chiusura della sessione ScreenCast fallita");
        }
    }
}

impl Drop for SessioneCattura {
    /// Rete di sicurezza per le vie che non passano da `chiudi`.
    ///
    /// Una connessione che muore male lascia cadere gli aggiornamenti senza
    /// passare da nessuna chiusura ordinata. Attendere qui non si puo' — e' la
    /// regola 7 di `SPECIFICA.md` §5.7, che vale anche per le attese nascoste
    /// dentro un `Drop` — quindi si manda la chiusura a un compito e si
    /// prosegue.
    fn drop(&mut self) {
        if self.chiusa || self.legata {
            return;
        }
        // `tokio::spawn` **va in panico** se chiamato quando non c'e' un runtime
        // in esecuzione, e un panico dentro un `Drop` durante lo srotolamento
        // abortisce il processo. Questo oggetto puo' benissimo essere lasciato
        // cadere alla chiusura del server, quando il runtime se n'e' gia'
        // andato: si verifica prima invece di darlo per scontato. Se il runtime
        // non c'e' piu', non c'e' nemmeno nulla da chiudere — il processo sta
        // finendo, e con lui la connessione D-Bus.
        if let Ok(runtime) = tokio::runtime::Handle::try_current() {
            let sessione = self.sessione.clone();
            runtime.spawn(async move {
                let _ = sessione.stop().await;
            });
        }
    }
}
