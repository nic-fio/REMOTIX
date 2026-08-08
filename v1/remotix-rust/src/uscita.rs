//! Chi si accorge che la sessione **se ne sta andando**, e lo sa subito.
//!
//! # Il difetto che questo modulo toglie
//!
//! Fino al 3 agosto REMOTIX veniva a sapere di un «Esci» per ultimo: se ne
//! accorgeva quando moriva il flusso di cattura, cioe' quando GNOME aveva
//! **finito** di smontare la sessione. Misurato dal telefono: fra il tocco su
//! «Log Out» e quel momento passavano **5,1 secondi**, e in tutti e cinque il
//! client restava fermo sull'ultimo fotogramma — che, non avendo piu' finestre
//! aperte, era uno sfondo pulito, cioe' *indistinguibile da un desktop vivo*.
//!
//! Da qui il difetto segnalato dall'utente: «la connessione sembra restare
//! viva». Non era un'impressione: era esattamente cio' che il client aveva
//! motivo di credere.
//!
//! # Perche' non basta chiudere e basta
//!
//! Perche' chiudere lo facevamo gia'. IronRDP, quando il flusso di
//! aggiornamenti finisce, arriva a `RunState::Disconnect`, che restituisce il
//! socket e **non manda niente al client**: ne' un codice d'errore, ne' un
//! congedo. Letto sul codice di `ironrdp-server` 0.13, non dedotto. Il client
//! riceve solo una chiusura di socket, e ognuno ne fa quel che vuole: xfreerdp
//! esce, il client Android resta li'.
//!
//! Il congedo dichiarato — `LogoffByUser`, che nel protocollo esiste — richiede
//! un contributo a monte a IronRDP, perche' dall'API pubblica non c'e' modo di
//! spedirlo. Nell'attesa si fa la cosa che **nessun client puo' ignorare**:
//! `SO_LINGER` a zero, cioe' un RST invece di una chiusura educata. Non e' bello
//! quanto un congedo — il client dira' «connessione persa» invece di «sei
//! uscito» — ma arriva mentre l'utente ha ancora il dito sul pulsante che ha
//! appena premuto, e un errore che arriva quando te lo aspetti non e' un guasto:
//! e' una conferma.
//!
//! # Come si sa in tempo
//!
//! Registrandosi con `gnome-session` come fa una qualunque applicazione
//! (`RegisterClient`). Da quel momento il gestore di sessione manda **a noi**,
//! di persona, i tre segnali dell'uscita. Misurato nella VM:
//!
//! | | |
//! |---|---|
//! | logout richiesto | |
//! | `QueryEndSession` | +9 ms — la **domanda**: qualcuno si oppone? |
//! | `EndSession` | +16 ms — la **decisione**: si esce |
//! | `Stop` | +20 ms |
//! | il flusso di cattura muore | +324 ms *(qui ce ne accorgevamo prima)* |
//!
//! Ci si aggancia a `EndSession`, **non** a `QueryEndSession`: la prima e' una
//! decisione, la seconda una domanda a cui qualcuno puo' ancora rispondere di
//! no, e in quel caso GNOME annulla l'uscita. Agganciandosi alla domanda si
//! butterebbe fuori l'utente per un logout che poi non avviene.
//!
//! # La regola dell'ostaggio
//!
//! **Si risponde sempre, e si risponde per primo.** Un client registrato che
//! non riscontra i segnali **blocca l'uscita dell'utente**: gnome-session
//! aspetta lui, e la sessione resta in piedi senza che niente, sullo schermo,
//! spieghi perche'. Non e' un timore: e' successo durante la prova, con una
//! spia che rispondeva alla domanda ma non alla decisione — la sessione e'
//! rimasta in ostaggio finche' la spia non e' scaduta, mezzo minuto dopo.
//!
//! Per questo la risposta parte **prima** di qualsiasi altra cosa, e da un
//! percorso che non puo' fermarsi ad aspettare nient'altro. Tutto il resto —
//! avvisare chi serve la connessione, smontare — viene dopo.
//!
//! # E se gnome-session non ci vuole
//!
//! Si prosegue senza, dichiarandolo nel registro, e si resta con il
//! comportamento di prima: ce ne accorgeremo alla morte del flusso di cattura,
//! cinque secondi dopo. E' peggio, ma e' cio' che c'era, e non e' un motivo per
//! non servire nessuno.

use core::time::Duration;
use std::sync::Arc;

use anyhow::{Context as _, Result};
use futures_util::StreamExt as _;
use tokio::sync::watch;
use tracing::{debug, info, warn};
use zbus::zvariant::OwnedObjectPath;
use zbus::{Connection, Proxy};

use crate::sessione;

/// Ogni quanto si riprova a registrarsi quando non c'e' una sessione.
const ATTESA_SESSIONE: Duration = Duration::from_millis(500);

/// Il nome con cui ci presentiamo a gnome-session.
const NOME: &str = "remotix";

/// Sa dire quando la sessione grafica ha cominciato ad andarsene.
///
/// Chi ascolta non fa I/O: lo stato lo tiene aggiornato un compito a parte.
/// Serve perche' la reazione deve essere **immediata** — e' tutto il punto del
/// modulo — e una chiamata D-Bus nel percorso della reazione rimetterebbe
/// esattamente il ritardo che stiamo togliendo.
pub struct Uscita {
    /// Si incrementa a ogni annuncio. Un contatore e non un booleano perche'
    /// gli annunci sono ripetibili: dopo un logout ne nasce un'altra sessione,
    /// che a sua volta un giorno uscira'.
    annunci: watch::Sender<u64>,
}

impl Uscita {
    /// Comincia a sorvegliare. Non attende: se la sessione non c'e' ancora, la
    /// registrazione avverra' quando ci sara'.
    pub fn avvia() -> Arc<Self> {
        let (annunci, _) = watch::channel(0);
        let uscita = Arc::new(Self { annunci });
        tokio::spawn(sorveglia(Arc::clone(&uscita)));
        uscita
    }

    /// Si risolve al **prossimo** annuncio di uscita.
    ///
    /// «Prossimo» e non «se ce n'e' stato uno»: chi chiama sta servendo una
    /// connessione, e gli annunci delle sessioni precedenti non la riguardano.
    pub async fn attendi_annuncio(&self) {
        let mut ricevitore = self.annunci.subscribe();
        if ricevitore.changed().await.is_err() {
            // Il sorvegliante e' morto: non arrivera' mai nessun annuncio, e
            // restare in attesa per sempre e' la cosa giusta — l'alternativa,
            // risolversi, farebbe cadere la connessione senza motivo.
            core::future::pending::<()>().await;
        }
    }
}

/// Il ciclo che tiene viva la registrazione.
///
/// Si rifa' a ogni sessione: `RegisterClient` vale per la sessione in cui si
/// chiama, e dopo un «Esci» ne nasce una nuova, con un gestore nuovo che di noi
/// non sa niente.
async fn sorveglia(uscita: Arc<Uscita>) {
    loop {
        // Registrarsi senza sessione non ha senso: il gestore non c'e'.
        while !sessione::viva().await {
            tokio::time::sleep(ATTESA_SESSIONE).await;
        }

        match registra().await {
            Ok(cliente) => {
                info!(percorso = %cliente.path(), "registrati con gnome-session: l'uscita si sapra' subito");
                servi_segnali(&cliente, &uscita).await;
                debug!("registrazione finita: la sessione non c'e' piu'");
            }
            Err(errore) => {
                warn!(
                    errore = %format!("{errore:#}"),
                    "registrazione con gnome-session fallita: dell'uscita ci si accorgera' tardi, alla morte della cattura"
                );
                // Non si ritenta a raffica: se il gestore rifiuta, rifiutera'
                // anche fra mezzo secondo, e il registro non deve riempirsi.
                tokio::time::sleep(Duration::from_secs(5)).await;
            }
        }

        // Si aspetta che la sessione se ne vada davvero prima di riprovare,
        // altrimenti ci si riregistrerebbe a raffica su quella morente.
        while sessione::viva().await {
            tokio::time::sleep(ATTESA_SESSIONE).await;
        }
    }
}

/// Si presenta a gnome-session e restituisce l'oggetto che ci rappresenta.
async fn registra() -> Result<Proxy<'static>> {
    let connessione = Connection::session()
        .await
        .context("connessione al bus di sessione")?;

    let gestore = Proxy::new(
        &connessione,
        "org.gnome.SessionManager",
        "/org/gnome/SessionManager",
        "org.gnome.SessionManager",
    )
    .await
    .context("gestore di sessione")?;

    // Il secondo argomento e' l'identificatore di avvio, che si usa per
    // riagganciare un'applicazione ripristinata da una sessione salvata. Non
    // e' il nostro caso: si manda vuoto, come fa qualunque programma avviato a
    // mano.
    let percorso: OwnedObjectPath = gestore
        .call("RegisterClient", &(NOME, ""))
        .await
        .context("RegisterClient")?;

    Proxy::new(
        &connessione,
        "org.gnome.SessionManager",
        percorso,
        "org.gnome.SessionManager.ClientPrivate",
    )
    .await
    .context("oggetto del client di sessione")
}

/// Ascolta i tre segnali finche' la sessione c'e'.
async fn servi_segnali(cliente: &Proxy<'static>, uscita: &Uscita) {
    let domande = cliente.receive_signal("QueryEndSession").await;
    let decisioni = cliente.receive_signal("EndSession").await;
    let arresti = cliente.receive_signal("Stop").await;

    let (Ok(mut domande), Ok(mut decisioni), Ok(mut arresti)) = (domande, decisioni, arresti)
    else {
        warn!("segnali di gnome-session non sottoscritti: dell'uscita ci si accorgera' tardi");
        return;
    };

    loop {
        tokio::select! {
            // La domanda: «qualcuno si oppone?». Si risponde di no e **non si
            // fa altro**. Chi si aggancia qui butta fuori l'utente per un
            // logout che un'applicazione puo' ancora annullare.
            Some(_) = domande.next() => {
                debug!("gnome-session chiede se si puo' uscire");
                riscontra(cliente).await;
            }

            // La decisione. Prima si risponde — la regola dell'ostaggio — e
            // **poi** si avvisa chi sta servendo la connessione.
            Some(_) = decisioni.next() => {
                riscontra(cliente).await;
                info!("la sessione grafica sta uscendo: lo si sa subito, non fra cinque secondi");
                uscita.annunci.send_modify(|n| *n += 1);
            }

            Some(_) = arresti.next() => {
                debug!("gnome-session ci dice di fermarci");
                return;
            }

            else => return,
        }
    }
}

/// Riscontra all'istante, e non lascia che un errore diventi un ostaggio.
///
/// Se la risposta non parte, gnome-session ci aspetta. Non c'e' niente di utile
/// da fare in quel caso se non dirlo forte nel registro: e' il difetto che
/// lascerebbe l'utente senza la possibilita' di sloggarsi, e chi legge deve
/// poterlo riconoscere subito.
async fn riscontra(cliente: &Proxy<'static>) {
    match cliente
        .call::<_, _, ()>("EndSessionResponse", &(true, ""))
        .await
    {
        Ok(()) => debug!("riscontrato a gnome-session: per noi si puo' uscire"),
        Err(errore) => warn!(
            errore = %errore,
            "riscontro a gnome-session fallito: l'uscita dell'utente potrebbe restare bloccata"
        ),
    }
}
