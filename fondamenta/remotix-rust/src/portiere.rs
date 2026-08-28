//! Chi decide chi entra: accettazione delle connessioni e regola della sessione unica.
//!
//! # Perche' non basta il ciclo di IronRDP
//!
//! `RdpServer::run()` accetta una connessione e **ne attende la fine** prima di
//! guardare la successiva (SPECIFICA.md §5.9). Chi arriva nel frattempo resta
//! nella coda TCP senza ricevere risposta: non un rifiuto, un silenzio, che dopo
//! un po' il client traduce in un errore di rete che non spiega nulla.
//!
//! Il gancio `ConnectionHandler::on_accept` sembrava la soluzione a costo zero,
//! ed e' quanto si era annotato in §5.9 — ma non lo e': vive **dentro** quel
//! ciclo, quindi viene chiamato solo quando la connessione precedente e' gia'
//! finita, cioe' quando non c'e' piu' niente da rifiutare.
//!
//! Qui il ciclo di accettazione e' nostro. Resta sempre in ascolto, e il rifiuto
//! arriva subito.
//!
//! # Una sessione per volta, e la seconda si rifiuta
//!
//! Deciso il 2 agosto (SPECIFICA.md §3.4): chi e' dentro non viene disturbato.
//! La conseguenza, gia' prevista dalla specifica, e' che il server **deve
//! accorgersi in fretta quando il client se ne va senza dirlo** — altrimenti
//! dopo una caduta di rete l'utente resta chiuso fuori dalla propria sessione,
//! con nessuno dentro e la porta sbarrata.
//!
//! Per questo ogni connessione nasce con i keepalive stretti: i valori
//! predefiniti del sistema aspettano **due ore** prima della prima sonda.
//!
//! # E chi e' davanti alla macchina ha la precedenza
//!
//! L'altra regola di §3.4: la sessione grafica **locale** vince. Qui si applica
//! nei due momenti in cui puo' servire — al momento di accettare, rifiutando, e
//! durante la sessione, lasciando cadere l'RDP se la locale compare dopo. Chi
//! le vede comparire e' la `Sentinella`; qui si decide cosa farne.

use core::net::SocketAddr;
use core::sync::atomic::{AtomicBool, Ordering};
use core::time::Duration;
use std::sync::Arc;

use anyhow::{Context as _, Result};
use ironrdp_server::RdpServer;
use tokio::net::{TcpListener, TcpStream};
use tracing::{info, warn};

use crate::sentinella::Sentinella;
use crate::uscita::Uscita;

/// Dopo quanto silenzio si comincia a sondare il client.
const KEEPALIVE_ATTESA: Duration = Duration::from_secs(10);
/// Ogni quanto si ripete la sonda.
const KEEPALIVE_INTERVALLO: Duration = Duration::from_secs(5);
/// Quante sonde senza risposta prima di dichiarare morto il client.
///
/// Dieci piu' tre volte cinque: un client sparito lo si sa in venticinque
/// secondi, invece delle due ore che aspetterebbe il sistema.
const KEEPALIVE_TENTATIVI: u32 = 3;

/// Per quanto si insiste con dati che il client non riscontra.
///
/// # Perche' il keepalive **da solo non basta** — misurato il 3 agosto
///
/// Perche' il keepalive vale solo per un socket **inattivo**: e' fatto per
/// scoprire chi se n'e' andato mentre non si aveva niente da dirgli. Se invece
/// ci sono dati in volo non riscontrati — e un server RDP ne ha quasi sempre,
/// fosse anche l'ultimo pezzo di fotogramma — comanda il timer di
/// ritrasmissione, che raddoppia l'attesa a ogni tentativo e con i valori
/// predefiniti insiste per **un quarto d'ora**.
///
/// Non e' una deduzione: staccando la rete a un client collegato, dopo un
/// minuto il server non se n'era ancora accorto, e il socket diceva
/// `timer:(on,27sec,8) rto:52224 backoff:8` — cioe' ritrasmissione all'ottavo
/// raddoppio, con cinquantadue secondi fino al tentativo successivo. Il
/// keepalive non era nemmeno partito, ed era giusto cosi': il socket aveva da
/// scrivere.
///
/// `TCP_USER_TIMEOUT` mette un tetto assoluto: passato questo tempo senza che i
/// dati vengano riscontrati, il kernel chiude e basta. Trenta secondi — un po'
/// piu' larghi dei venticinque del keepalive, perche' qui si conta anche il
/// tempo che serve a scoprire di doversi preoccupare.
const ATTESA_SENZA_RISCONTRO: Duration = Duration::from_secs(30);

/// Per quanto la porta resta chiusa dopo che l'utente e' uscito.
///
/// # Perche' esiste, e perche' non e' una furbizia
///
/// Perche' il client Android, ricevuto il RST, **si ricollega da solo con le
/// credenziali salvate**: misurato il 3 agosto, **174 millisecondi** dopo la
/// troncatura, con REMOTIX che gli apriva una sessione nuova di zecca. Da fuori
/// sembrava che il logout non funzionasse; in realta' funzionava e veniva
/// annullato subito dopo.
///
/// E' la conseguenza di come lo salutiamo: un RST e' indistinguibile da una
/// rete che cade, ed e' *esattamente* il caso per cui la riconnessione
/// automatica esiste. Finche' non possiamo dire «l'utente e' uscito»
/// (`LogoffByUser`, che IronRDP 0.13 non lascia spedire) il client non ha modo
/// di sapere che non c'e' niente da recuperare.
///
/// L'argomento di specifica e' pero' piu' forte del rimedio tecnico: §3.3-bis
/// vuole che dopo un «Esci» si debba **riautenticarsi**, e un client che rientra
/// da solo con le credenziali salvate quella decisione la aggira.
///
/// Cinque secondi perche' i client provano a raffica e poi si arrendono: quando
/// il telefono aveva il nome utente sbagliato ha fatto **tre tentativi in 0,6
/// secondi** e ha smesso. Cinque secondi coprono la raffica con margine, e sono
/// pochi abbastanza da non dare fastidio a chi vuole rientrare davvero.
const PORTA_CHIUSA_DOPO_USCITA: Duration = Duration::from_secs(5);

/// Accetta connessioni, una sessione per volta, e serve ciascuna con un server
/// costruito per lei.
///
/// `costruisci` produce un `RdpServer` nuovo a ogni connessione: lo stato
/// grafico appartiene alla connessione e non al server (§5.7 regola 6), quindi
/// riusarne uno solo sarebbe il difetto che quella regola descrive.
///
/// # Perche' il lavoro e' diviso in due
///
/// Il futuro di `run_connection` **non e' `Send`**: dentro usa `Rc`, quindi non
/// si puo' affidare a `tokio::spawn` e va eseguito sul compito che lo ha
/// chiamato. Se pero' si accettasse e si servisse nello stesso ciclo, mentre una
/// sessione dura non si guarderebbe piu' la porta — che e' esattamente il
/// difetto di §5.9 che stiamo togliendo.
///
/// Quindi: **accetta** un compito a parte, che e' `Send` perche' maneggia solo
/// socket, e **serve** questo, che non lo e'. I due si parlano con un canale.
/// `a_fine_connessione` viene eseguito quando la sessione finisce, comunque
/// finisca. Non e' una comodita': ci vive il rilascio di cio' che era rimasto
/// premuto, e un modificatore lasciato giu' rende il desktop inutilizzabile
/// anche da vicino (§5.8 regola 4). IronRDP avrebbe un gancio per questo,
/// `ConnectionHandler`, ma lo chiama il **suo** ciclo di accettazione, che qui
/// non si usa piu': tenerlo sarebbe stato peggio che non averlo, perche' il
/// codice resta li' e sembra fare qualcosa.
pub async fn servi<F, G>(
    bind: SocketAddr,
    mut costruisci: F,
    mut a_fine_connessione: G,
    sentinella: Arc<Sentinella>,
    uscita: Arc<Uscita>,
) -> Result<()>
where
    F: FnMut() -> Result<RdpServer>,
    G: FnMut(),
{
    let ascolto = TcpListener::bind(bind)
        .await
        .with_context(|| format!("ascolto su {bind}"))?;

    let occupato = Arc::new(AtomicBool::new(false));
    // Fino a quando la porta resta chiusa perche' qualcuno e' appena uscito.
    let serratura: Arc<std::sync::Mutex<Option<tokio::time::Instant>>> =
        Arc::new(std::sync::Mutex::new(None));
    let (consegna, mut ritiro) = tokio::sync::mpsc::channel::<(TcpStream, SocketAddr)>(1);

    let guardia = Arc::clone(&occupato);
    let vigile = Arc::clone(&sentinella);
    let chiavistello = Arc::clone(&serratura);
    tokio::spawn(async move {
        loop {
            let (flusso, peer) = match ascolto.accept().await {
                Ok(coppia) => coppia,
                Err(errore) => {
                    // Un rifiuto sul singolo accept non e' motivo per smettere
                    // di servire: capita per esaurimento temporaneo di
                    // descrittori, o per un client che se ne va fra la SYN e
                    // l'accept.
                    warn!(errore = %errore, "accettazione fallita, si prosegue");
                    continue;
                }
            };

            // Chi e' davanti alla macchina ha la precedenza, e lo si guarda
            // **prima** del posto libero: una sessione locale in corso non
            // deve nemmeno far sembrare occupata la sessione RDP a chi legge
            // il registro.
            if let Some(locale) = vigile.presente() {
                warn!(%peer, %locale, "connessione rifiutata: c'e' una sessione grafica locale");
                drop(flusso);
                continue;
            }

            // Chi e' appena uscito non rientra da solo. Si guarda prima del
            // posto libero: il posto **e'** libero — l'abbiamo appena liberato
            // noi — ed e' proprio questo che rende la riconnessione automatica
            // capace di annullare il logout.
            let residuo = chiavistello
                .lock()
                .map(|serratura| {
                    serratura.and_then(|fino_a| fino_a.checked_duration_since(tokio::time::Instant::now()))
                })
                // Un lock avvelenato non deve chiudere il servizio: si prosegue
                // come se la porta fosse aperta, che e' il comportamento di
                // prima e non lascia nessuno fuori.
                .unwrap_or(None);
            if let Some(residuo) = residuo {
                warn!(
                    %peer,
                    millisecondi = residuo.as_millis(),
                    "connessione rifiutata: l'utente e' appena uscito, si deve riautenticare"
                );
                drop(flusso);
                continue;
            }

            // `compare_exchange` e non «leggi, poi scrivi»: due client che
            // arrivano nello stesso istante devono trovare una porta sola
            // aperta, ed e' proprio il caso che alcuni client producono da
            // soli, aprendo la seconda connessione prima di chiudere la prima.
            if guardia
                .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
                .is_err()
            {
                // La chiusura immediata e' meno di quel che vorremmo — il
                // client dice «connessione chiusa», non «c'e' gia' qualcuno» —
                // ma e' incomparabilmente meglio del silenzio: arriva subito, e
                // chi e' dentro non si accorge di nulla. Il messaggio esplicito
                // resta a debito: RDP non ha un codice di rifiuto che voglia
                // dire «occupato».
                warn!(%peer, "connessione rifiutata: c'e' gia' una sessione in corso");
                drop(flusso);
                continue;
            }

            if let Err(errore) = prepara(&flusso) {
                warn!(%peer, errore = %format!("{errore:#}"), "opzioni del socket non impostate");
            }

            if consegna.send((flusso, peer)).await.is_err() {
                break; // chi serve se n'e' andato: non c'e' piu' nulla da accettare
            }
        }
    });

    while let Some((flusso, peer)) = ritiro.recv().await {
        info!(%peer, "connessione accettata");
        match costruisci() {
            Ok(mut server) => {
                let inizio = tokio::time::Instant::now();

                // Una maniglia sul socket che sopravvive alla consegna a
                // IronRDP, che se lo prende per valore. Serve solo per il caso
                // dell'uscita, qui sotto: senza, quando scopriamo che la
                // sessione se ne va non avremmo piu' modo di toccare le opzioni
                // del socket. `SO_LINGER` sta sul socket, non sul descrittore,
                // quindi impostarlo da qui vale anche per il descrittore che ha
                // in mano IronRDP.
                let doppione = socket2::SockRef::from(&flusso).try_clone().ok();
                if doppione.is_none() {
                    warn!(%peer, "socket non duplicato: all'uscita la chiusura sara' educata invece che netta");
                }

                let mut per_uscita = false;
                // La sessione locale non si chiede al client il permesso di
                // interromperla: si abbandona il futuro che serve la
                // connessione, e con esso cade il socket. IronRDP non ha un
                // modo di dire «chiudi adesso» dall'esterno, e non serve —
                // lasciar cadere il futuro chiude tutto cio' che ha aperto.
                let esito = tokio::select! {
                    esito = server.run_connection(flusso) => Some(esito),
                    locale = sentinella.attendi_comparsa() => {
                        warn!(%peer, %locale, "sessione RDP terminata: chi e' davanti alla macchina ha la precedenza");
                        None
                    }

                    // L'utente e' uscito dalla sessione. Lo sappiamo entro una
                    // ventina di millisecondi perche' siamo registrati con
                    // gnome-session (`uscita.rs`), non fra cinque secondi come
                    // quando lo si scopriva dalla morte della cattura.
                    //
                    // Si tronca **di netto**: `SO_LINGER` a zero fa partire un
                    // RST invece della chiusura educata. Non e' brutalita' fine
                    // a se stessa — e' l'unica cosa che nessun client puo'
                    // ignorare. Con la chiusura educata xfreerdp esce e il
                    // client Android resta fermo sull'ultimo fotogramma, che
                    // senza finestre aperte e' uno sfondo pulito: identico a un
                    // desktop vivo. Il congedo dichiarato (`LogoffByUser`)
                    // sarebbe meglio, ma IronRDP 0.13 non ha modo di spedirlo:
                    // finche' non c'e', meglio un errore onesto e immediato di
                    // un'immagine che mente.
                    () = uscita.attendi_annuncio() => {
                        // Si arma la serratura **prima** di troncare: fra il
                        // RST e la riconnessione automatica sono passati 174
                        // millisecondi, e in quella finestra non ci deve essere
                        // un istante in cui la porta e' aperta.
                        if let Ok(mut serratura) = serratura.lock() {
                            *serratura = Some(tokio::time::Instant::now() + PORTA_CHIUSA_DOPO_USCITA);
                        } else {
                            warn!(%peer, "serratura non armata: un client con la riconnessione automatica potrebbe rientrare da solo");
                        }

                        if let Some(socket) = &doppione
                            && let Err(errore) = socket.set_linger(Some(Duration::ZERO))
                        {
                            warn!(%peer, errore = %errore, "SO_LINGER non impostato: la chiusura sara' educata");
                        }
                        per_uscita = true;
                        None
                    }
                };
                // Ora che il futuro di IronRDP e' caduto — e con esso il suo
                // descrittore — si lascia andare anche il nostro. Il RST parte
                // alla chiusura dell'**ultimo** descrittore, quindi tenerlo
                // aperto un istante di piu' significherebbe non mandarlo.
                drop(doppione);

                let secondi = inizio.elapsed().as_secs();
                match esito {
                    None if per_uscita => {
                        info!(%peer, secondi, "connessione troncata: l'utente e' uscito dalla sessione")
                    }
                    Some(Ok(())) => info!(%peer, secondi, "connessione conclusa"),
                    // Un «not enough bytes» e' quasi sempre il client che ha
                    // chiuso, non un messaggio incomprensibile: IronRDP segnala
                    // le due cose allo stesso modo.
                    Some(Err(errore)) => info!(%peer, secondi, errore = %errore, "connessione conclusa"),
                    None => info!(%peer, secondi, "connessione interrotta dalla sessione locale"),
                }
            }
            Err(errore) => {
                warn!(%peer, errore = %format!("{errore:#}"), "server non costruito");
            }
        }
        a_fine_connessione();

        // Da qui la porta e' di nuovo aperta. Va fatto **sempre**, compreso il
        // caso in cui il server non si sia costruito: dimenticarlo lascerebbe il
        // servizio vivo e inaccessibile per sempre, senza un errore da nessuna
        // parte.
        occupato.store(false, Ordering::SeqCst);
    }
    Ok(())
}

/// Le tre opzioni che rendono la connessione pronta e mortale al punto giusto.
///
/// Servono a cose diverse e vanno tutte e tre:
///
/// - **keepalive stretti**, per il client sparito mentre il desktop era fermo e
///   non c'era nulla da mandargli: venticinque secondi invece di due ore;
/// - **`TCP_USER_TIMEOUT`**, per il client sparito mentre gli si stava
///   scrivendo — il caso piu' comune, e quello che il keepalive **non copre**:
///   trenta secondi invece di un quarto d'ora (vedere la costante);
/// - **`TCP_NODELAY`**, che toglie i quaranta millisecondi che Nagle metterebbe
///   fra un tasto e la sua eco.
///
/// I primi due insieme sono cio' che, con la sessione unica, fa la differenza
/// fra rientrare nella propria sessione e restarne chiusi fuori.
fn prepara(flusso: &TcpStream) -> Result<()> {
    flusso.set_nodelay(true).context("TCP_NODELAY")?;

    let socket = socket2::SockRef::from(flusso);
    let keepalive = socket2::TcpKeepalive::new()
        .with_time(KEEPALIVE_ATTESA)
        .with_interval(KEEPALIVE_INTERVALLO)
        .with_retries(KEEPALIVE_TENTATIVI);
    socket.set_tcp_keepalive(&keepalive).context("keepalive")?;
    socket
        .set_tcp_user_timeout(Some(ATTESA_SENZA_RISCONTRO))
        .context("TCP_USER_TIMEOUT")?;
    Ok(())
}
