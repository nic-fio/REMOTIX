//! Chi guarda se c'e' qualcuno **davanti alla macchina**.
//!
//! # La regola, e perche' esiste
//!
//! Una sola sessione grafica per utente (SPECIFICA.md §3.4). Se l'utente ha
//! gia' una sessione grafica **locale**, la connessione RDP si rifiuta; se la
//! sessione locale compare mentre l'RDP e' in corso, **la locale vince** e
//! l'RDP cade.
//!
//! Non e' una regola di comodo: due sessioni grafiche dello stesso utente sullo
//! stesso `$XDG_RUNTIME_DIR` si contendono il gestore systemd dell'utente, il
//! bus di sessione, l'agente delle chiavi e i portali — cioe' proprio le cose
//! che nella fase 5 si e' faticato a far funzionare una volta sola. Il guasto
//! che ne segue non si presenta come «due sessioni»: si presenta come
//! applicazioni che non si aprono e impostazioni che tornano indietro.
//!
//! Le sessioni **testuali** convivono liberamente, ed e' importante che sia
//! cosi': REMOTIX stesso oggi gira dentro una sessione SSH.
//!
//! # Cosa conta come «grafica locale»
//!
//! Quattro condizioni insieme, lette da `systemd-logind`:
//!
//! | proprieta' | valore | perche' |
//! |---|---|---|
//! | `User`  | il nostro uid   | le sessioni di altri utenti non ci riguardano |
//! | `Seat`  | non vuoto       | un seat e' hardware vero: schermo e tastiera attaccati |
//! | `Type`  | `wayland`/`x11`/`mir` | `tty` e' testuale, e deve poter convivere |
//! | `Class` | `user`          | esclude `greeter`, `lock-screen`, `manager`, `background` |
//!
//! `Remote` deve inoltre essere falso: una sessione X11 inoltrata da lontano
//! non e' qualcuno davanti alla macchina.
//!
//! Misurato nella VM il 3 agosto: la sessione SSH in cui girano REMOTIX **e la
//! sessione GNOME che REMOTIX avvia** e' una sola, `Type=tty`, senza seat.
//! `gnome-session` non ne crea una propria — sta nel cgroup di chi lo ha
//! avviato — quindi la sessione remota non si conta da sola. Per prudenza la si
//! esclude comunque per identificatore: se un domani REMOTIX venisse avviato
//! dentro una sessione registrata come grafica, senza quell'esclusione si
//! sfratterebbe da solo, e il sintomo — «rifiuta sempre tutti» — non farebbe
//! sospettare la causa.
//!
//! # Perche' un segnale **e** un ripasso
//!
//! §3.4 lo dice: interrogare logind alla connessione non basta, perche' la
//! sessione locale puo' comparire dopo. Ci si sottoscrive quindi a
//! `SessionNew`/`SessionRemoved`.
//!
//! Il ripasso periodico non e' ridondanza inutile: il `Type` di una sessione
//! **cambia dopo la nascita** — `gdm` la registra e poi la promuove — quindi un
//! `SessionNew` visto troppo presto la mostrerebbe ancora testuale. Ogni due
//! secondi si riguarda; e' una manciata di chiamate D-Bus al minuto.
//!
//! # Se logind non c'e'
//!
//! Si prosegue **senza** la regola, dichiarandolo nel registro. E' una scelta:
//! l'alternativa — rifiutare tutti — trasformerebbe un bus non raggiungibile in
//! un server inaccessibile senza spiegazione. Chi non ha logind non ha nemmeno
//! il modo di aprire la sessione locale che stiamo temendo.

use core::time::Duration;
use std::sync::Arc;

use anyhow::{Context as _, Result};
use futures_util::StreamExt as _;
use tokio::sync::watch;
use tracing::{debug, info, warn};
use zbus::zvariant::OwnedObjectPath;
use zbus::{Connection, Proxy};

/// Ogni quanto si riguarda l'elenco anche senza segnali.
const RIPASSO: Duration = Duration::from_secs(2);

/// I tipi di sessione che occupano lo schermo.
const TIPI_GRAFICI: [&str; 3] = ["wayland", "x11", "mir"];

/// Una sessione grafica locale trovata, nella forma in cui si racconta.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SessioneLocale {
    pub id: String,
    pub tipo: String,
    pub seat: String,
}

impl core::fmt::Display for SessioneLocale {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "sessione {} ({} su {})", self.id, self.tipo, self.seat)
    }
}

/// Sorveglia la comparsa e la scomparsa della sessione grafica locale.
///
/// Chi la interroga non fa I/O: lo stato lo tiene aggiornato un compito a
/// parte. Serve perche' la risposta va data **nell'istante** in cui arriva una
/// connessione — interrogare D-Bus li' significherebbe far aspettare il client
/// per una risposta che quasi sempre e' «no».
pub struct Sentinella {
    stato: watch::Sender<Option<SessioneLocale>>,
}

impl Sentinella {
    /// Prepara la sentinella e fa **subito** il primo controllo.
    ///
    /// Il primo controllo e' atteso di proposito: se la macchina ha gia' una
    /// sessione grafica locale all'avvio di REMOTIX, non deve esistere una
    /// finestra iniziale in cui si entra lo stesso.
    pub async fn avvia() -> Arc<Self> {
        let (stato, _) = watch::channel(None);
        let sentinella = Arc::new(Self { stato });

        match Logind::apri().await {
            Ok(logind) => {
                let iniziale = logind.cerca().await;
                match &iniziale {
                    Some(sessione) => warn!(%sessione, "c'e' gia' una sessione grafica locale: le connessioni saranno rifiutate"),
                    None => info!("nessuna sessione grafica locale: si puo' entrare"),
                }
                sentinella.stato.send_replace(iniziale);
                tokio::spawn(sorveglia(Arc::clone(&sentinella), logind));
            }
            Err(errore) => {
                // Non si nasconde dietro un `debug`: significa che una delle
                // regole di §3.4 non e' in vigore, e chi legge il registro deve
                // poterlo sapere senza andarlo a cercare.
                warn!(
                    errore = %format!("{errore:#}"),
                    "logind non raggiungibile: la regola della sessione locale non e' applicata"
                );
            }
        }
        sentinella
    }

    /// La sessione grafica locale in corso, se c'e'.
    pub fn presente(&self) -> Option<SessioneLocale> {
        self.stato.borrow().clone()
    }

    /// Si risolve quando c'e' una sessione grafica locale — subito, se c'e' gia'.
    ///
    /// # Sicurezza rispetto all'annullamento
    ///
    /// Vive dentro la `select!` che serve la connessione, quindi va potuto
    /// abbandonare a meta' senza conseguenze: un `watch::Receiver` non consuma
    /// nulla quando lo si molla, e il valore resta li' per chi lo riprende.
    ///
    /// Se il compito di sorveglianza non c'e' — logind assente — questo futuro
    /// non si risolve mai, che e' esattamente il comportamento voluto: la
    /// connessione prosegue senza la regola.
    pub async fn attendi_comparsa(&self) -> SessioneLocale {
        let mut ricevitore = self.stato.subscribe();
        loop {
            if let Some(sessione) = ricevitore.borrow_and_update().clone() {
                return sessione;
            }
            if ricevitore.changed().await.is_err() {
                core::future::pending::<()>().await;
            }
        }
    }

    /// Si risolve quando la sessione grafica locale non c'e' piu' — subito, se
    /// non c'era.
    ///
    /// Serve a chi agisce sulla comparsa: senza un modo di aspettare che finisca
    /// ripeterebbe l'azione a ogni giro, perche' «c'e' una sessione locale»
    /// resta vero finche' quella dura.
    pub async fn attendi_scomparsa(&self) {
        let mut ricevitore = self.stato.subscribe();
        loop {
            if ricevitore.borrow_and_update().is_none() {
                return;
            }
            if ricevitore.changed().await.is_err() {
                core::future::pending::<()>().await;
            }
        }
    }
}

/// Il ciclo che tiene aggiornato lo stato.
async fn sorveglia(sentinella: Arc<Sentinella>, logind: Logind) {
    let nascite = logind.manager.receive_signal("SessionNew").await;
    let morti = logind.manager.receive_signal("SessionRemoved").await;
    let (Ok(mut nascite), Ok(mut morti)) = (nascite, morti) else {
        warn!("segnali di logind non sottoscritti: resta il solo ripasso periodico");
        ripassa_e_basta(&sentinella, &logind).await;
        return;
    };

    loop {
        // Il ripasso e i segnali fanno la stessa cosa; i segnali la fanno
        // presto, il ripasso la fa comunque.
        tokio::select! {
            _ = nascite.next() => {}
            _ = morti.next() => {}
            () = tokio::time::sleep(RIPASSO) => {}
        }
        aggiorna(&sentinella, &logind).await;
    }
}

async fn ripassa_e_basta(sentinella: &Sentinella, logind: &Logind) {
    loop {
        tokio::time::sleep(RIPASSO).await;
        aggiorna(sentinella, logind).await;
    }
}

/// Rilegge l'elenco e pubblica il risultato solo se e' cambiato.
async fn aggiorna(sentinella: &Sentinella, logind: &Logind) {
    let trovata = logind.cerca().await;
    let cambiato = *sentinella.stato.borrow() != trovata;
    if !cambiato {
        return;
    }
    match &trovata {
        Some(sessione) => warn!(%sessione, "e' comparsa una sessione grafica locale"),
        None => info!("la sessione grafica locale e' finita: si puo' entrare"),
    }
    sentinella.stato.send_replace(trovata);
}

// ---------------------------------------------------------------------------
// Il dialogo con logind
// ---------------------------------------------------------------------------

/// Quanto serve per interrogare logind, preparato una volta sola.
struct Logind {
    connessione: Connection,
    manager: Proxy<'static>,
    /// L'uid di cui ci importa: il nostro.
    uid: u32,
    /// La sessione dentro cui gira REMOTIX, da non contare mai.
    nostra: Option<String>,
}

impl Logind {
    async fn apri() -> Result<Self> {
        // Il bus di **sistema**: logind non sta su quello di sessione.
        let connessione = Connection::system()
            .await
            .context("connessione al bus di sistema")?;
        let manager = Proxy::new(
            &connessione,
            "org.freedesktop.login1",
            "/org/freedesktop/login1",
            "org.freedesktop.login1.Manager",
        )
        .await
        .context("org.freedesktop.login1 non risponde")?;

        let uid = uid_nostro().context("lettura del proprio uid")?;
        let nostra = sessione_nostra(&manager).await;
        debug!(uid, sessione = ?nostra, "sentinella pronta");
        Ok(Self {
            connessione,
            manager,
            uid,
            nostra,
        })
    }

    /// La prima sessione grafica locale del nostro utente, se c'e'.
    async fn cerca(&self) -> Option<SessioneLocale> {
        // `ListSessions` restituisce gia' uid e seat: le due condizioni che
        // scartano quasi tutto si applicano senza aprire un proxy per sessione.
        let elenco: Vec<(String, u32, String, String, OwnedObjectPath)> =
            match self.manager.call("ListSessions", &()).await {
                Ok(elenco) => elenco,
                Err(errore) => {
                    // Si prosegue senza la regola invece di chiudere fuori
                    // tutti: vedere la nota in testa al modulo.
                    warn!(errore = %errore, "elenco delle sessioni non ottenuto");
                    return None;
                }
            };

        for (id, uid, _utente, seat, percorso) in elenco {
            if uid != self.uid || seat.is_empty() {
                continue;
            }
            if self.nostra.as_deref() == Some(id.as_str()) {
                continue;
            }
            if let Some(tipo) = self.tipo_grafico(&percorso).await {
                return Some(SessioneLocale { id, tipo, seat });
            }
        }
        None
    }

    /// Il tipo della sessione, se e' grafica, dell'utente, e non sta chiudendo.
    async fn tipo_grafico(&self, percorso: &OwnedObjectPath) -> Option<String> {
        let sessione = Proxy::new(
            &self.connessione,
            "org.freedesktop.login1",
            percorso.clone(),
            "org.freedesktop.login1.Session",
        )
        .await
        .ok()?;

        // Una sessione puo' sparire fra l'elenco e queste domande: e' la
        // condizione di corsa normale di logind, non un guasto.
        let tipo: String = sessione.get_property("Type").await.ok()?;
        if !TIPI_GRAFICI.contains(&tipo.as_str()) {
            return None;
        }
        let classe: String = sessione.get_property("Class").await.ok()?;
        if classe != "user" {
            return None;
        }
        if sessione.get_property::<bool>("Remote").await.ok()? {
            return None;
        }
        // `closing` e' la sessione che se ne sta andando: contarla terrebbe
        // fuori chi si ricollega proprio mentre quella locale finisce.
        let stato: String = sessione.get_property("State").await.ok()?;
        if stato == "closing" {
            return None;
        }
        Some(tipo)
    }
}

/// L'identificatore della sessione logind dentro cui giriamo, se ce n'e' una.
///
/// Puo' non essercene: se REMOTIX viene avviato da un'unita' systemd, il suo
/// cgroup non appartiene ad alcuna sessione. In quel caso non c'e' nulla da
/// escludere, e va bene cosi'.
async fn sessione_nostra(manager: &Proxy<'static>) -> Option<String> {
    let percorso: OwnedObjectPath = manager
        .call("GetSessionByPID", &(std::process::id()))
        .await
        .ok()?;
    // L'ultimo pezzo del percorso e' l'identificatore, ma lo si chiede a logind
    // invece di ricavarlo dalla stringa: il percorso e' codificato (`session_3`
    // per la sessione `3`) e la decodifica a mano sbaglierebbe sui nomi con
    // trattini.
    let percorso = percorso.as_str().to_owned();
    let sessione = Proxy::new(
        manager.connection(),
        "org.freedesktop.login1",
        percorso,
        "org.freedesktop.login1.Session",
    )
    .await
    .ok()?;
    sessione.get_property::<String>("Id").await.ok()
}

/// Il proprio uid, letto da `/proc`.
///
/// Si legge da li' per non aggiungere una dipendenza da `libc` per una riga
/// sola. La quarta parola di `Uid:` e' quello effettivo — che e' l'uid con cui
/// logind ci vede — ma qui il processo non cambia identita', quindi il primo
/// basterebbe: si prende comunque l'effettivo, per non dover ricordare la
/// differenza il giorno in cui cambiasse.
fn uid_nostro() -> Result<u32> {
    let stato = std::fs::read_to_string("/proc/self/status").context("/proc/self/status")?;
    for riga in stato.lines() {
        if let Some(valori) = riga.strip_prefix("Uid:") {
            let campi: Vec<&str> = valori.split_whitespace().collect();
            if let Some(effettivo) = campi.get(1) {
                return effettivo.parse().context("uid non numerico");
            }
        }
    }
    anyhow::bail!("nessuna riga «Uid:» in /proc/self/status")
}
