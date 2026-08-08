//! La sessione grafica: REMOTIX la avvia, non si limita a trovarla.
//!
//! # Perché
//!
//! Perché altrimenti dopo un «Esci» non c'è più niente da mostrare. È il difetto
//! segnalato il 3 agosto: l'utente esce dal menu di sistema, `gnome-session`
//! termina come deve, e da quel momento chi si collega trova il server in
//! ascolto e **nessun desktop** — perché la sessione la avviava una shell SSH, a
//! mano, e nessuno la riavvia.
//!
//! Vale anche al primo avvio della macchina: non c'è alcun gestore di accesso
//! grafico installato (e non deve esserci, aprirebbe una sessione locale che
//! confliggerebbe con le regole di §3.4), quindi finché REMOTIX non avvia la
//! sessione, sessione non ce n'è.
//!
//! # L'ambiente si compone, non si eredita
//!
//! È la lezione più cara di questa fase, e qui è codificata: **chi avvia la
//! sessione le regala tutto il proprio ambiente**. Una `LC_ALL=C` arrivata per
//! sbaglio da una shell SSH è finita nel gestore systemd dell'utente e ha
//! impedito a *tutte* le applicazioni di aprirsi (§5.9-bis). Quindi si parte da
//! zero e si dichiara una variabile per volta, sapendo perché.
//!
//! # Come si accerta che sia viva
//!
//! Chiamando un metodo che il compositore implementa **davvero**. `Ping` e
//! `Introspect` rispondono anche a ciclo principale fermo, perché li serve la
//! libreria D-Bus per conto proprio: sembrano la prova che il processo sia vivo
//! e non lo sono (§5.6).

use core::time::Duration;

use std::process::Stdio;

use anyhow::{Context as _, Result, bail};
use tracing::{debug, info, warn};
use zbus::Connection;

/// Come si avvia una sessione GNOME senza monitor.
///
/// La Shell senza schermo la si ottiene sovrascrivendo l'`ExecStart` della sua
/// unità — configurazione della macchina, che sta in `provision-vm.sh` e
/// apparterrà al confezionamento della fase 11 (§5.9-bis).
pub const COMANDO_PREDEFINITO: &str = "exec gnome-session --session=gnome";

/// Quanto si aspetta che il compositore risponda dopo averlo avviato.
///
/// Su questa VM, senza accelerazione grafica, la sessione impiega una decina di
/// secondi; il margine serve per le macchine più lente.
const ATTESA_AVVIO: Duration = Duration::from_secs(40);

/// Ogni quanto si richiede al compositore se è pronto.
const CADENZA_CONTROLLO: Duration = Duration::from_millis(500);

/// Quanto si aspetta una singola risposta prima di considerarla non arrivata.
const ATTESA_RISPOSTA: Duration = Duration::from_secs(5);

/// Vero se c'è un compositore che risponde.
///
/// Non si interpreta la risposta, si guarda solo **che arrivi**: `GetCurrentState`
/// restituisce l'intera configurazione degli schermi, una struttura annidata che
/// cambia forma fra le versioni di Mutter. Dichiararne il tipo significherebbe
/// che un domani la vitalità della sessione dipenderebbe dall'esattezza di
/// quella dichiarazione — e infatti la prima stesura falliva così: la sessione
/// era partita e REMOTIX la dava per morta, perché la risposta non si
/// deserializzava nel tipo che avevo scritto.
pub async fn viva() -> bool {
    let Ok(connessione) = Connection::session().await else {
        return false;
    };
    let Ok(mutter) = zbus::Proxy::new(
        &connessione,
        "org.gnome.Mutter.DisplayConfig",
        "/org/gnome/Mutter/DisplayConfig",
        "org.gnome.Mutter.DisplayConfig",
    )
    .await
    else {
        return false;
    };
    matches!(
        tokio::time::timeout(ATTESA_RISPOSTA, mutter.call_method("GetCurrentState", &())).await,
        Ok(Ok(_))
    )
}

/// Si assicura che ci sia una sessione grafica, avviandola se manca.
///
/// Restituisce `true` se l'ha dovuta avviare.
pub async fn assicura(comando: &str) -> Result<bool> {
    if viva().await {
        return Ok(false);
    }

    info!("nessuna sessione grafica: la avvio");
    avvia(comando)?;

    let scadenza = tokio::time::Instant::now() + ATTESA_AVVIO;
    while tokio::time::Instant::now() < scadenza {
        tokio::time::sleep(CADENZA_CONTROLLO).await;
        if viva().await {
            info!("sessione grafica pronta");
            return Ok(true);
        }
    }
    bail!("la sessione grafica non ha risposto entro {ATTESA_AVVIO:?}")
}

/// Quanto si aspetta che la sessione se ne vada dopo averglielo chiesto con
/// garbo, prima di insistere.
const ATTESA_USCITA: Duration = Duration::from_secs(10);

/// Termina la sessione grafica.
///
/// Restituisce `true` se c'era una sessione e ora non c'e' piu'.
///
/// # Perche' esiste
///
/// Perche' «la sessione locale vince» (§3.4) non significa soltanto staccare il
/// client: se il compositore remoto restasse in piedi, l'utente che si siede
/// davanti alla macchina avrebbe **due sessioni grafiche a proprio nome** sullo
/// stesso `$XDG_RUNTIME_DIR`, e la seconda troverebbe il nome D-Bus
/// `org.gnome.Shell` gia' occupato. Deciso dall'utente il 3 agosto: si chiude.
///
/// # Prima si chiede, poi si insiste
///
/// `Logout(1)` e' l'uscita ordinata senza domande: le applicazioni ricevono
/// l'avviso e possono salvare. Ma puo' anche non succedere nulla — un programma
/// con modifiche non salvate ha il diritto di **inibire** l'uscita — e a quel
/// punto resteremmo con le due sessioni che stiamo cercando di evitare. Se dopo
/// dieci secondi la sessione e' ancora li' si passa a `Logout(2)`, che non
/// accetta obiezioni, e lo si dichiara nel registro: e' una perdita possibile di
/// lavoro non salvato, e chi legge deve poterla ricostruire.
pub async fn termina() -> Result<bool> {
    if !viva().await {
        return Ok(false);
    }

    esci(1).await.context("richiesta di uscita alla sessione")?;

    let scadenza = tokio::time::Instant::now() + ATTESA_USCITA;
    while tokio::time::Instant::now() < scadenza {
        tokio::time::sleep(CADENZA_CONTROLLO).await;
        if !viva().await {
            info!("la sessione grafica e' uscita");
            return Ok(true);
        }
    }

    warn!("la sessione non esce: la chiudo a forza, cio' che non e' salvato va perduto");
    esci(2).await.context("uscita forzata")?;

    let scadenza = tokio::time::Instant::now() + ATTESA_USCITA;
    while tokio::time::Instant::now() < scadenza {
        tokio::time::sleep(CADENZA_CONTROLLO).await;
        if !viva().await {
            return Ok(true);
        }
    }
    bail!("la sessione grafica non e' uscita nemmeno a forza")
}

/// `org.gnome.SessionManager.Logout`: 0 chiede conferma, 1 no, 2 forza.
async fn esci(modo: u32) -> Result<()> {
    let connessione = Connection::session()
        .await
        .context("connessione al bus di sessione")?;
    let gestore = zbus::Proxy::new(
        &connessione,
        "org.gnome.SessionManager",
        "/org/gnome/SessionManager",
        "org.gnome.SessionManager",
    )
    .await
    .context("org.gnome.SessionManager non risponde")?;
    gestore
        .call_method("Logout", &(modo))
        .await
        .context("chiamata a Logout")?;
    Ok(())
}

// ---------------------------------------------------------------------------
// La disposizione della tastiera
// ---------------------------------------------------------------------------

/// L'impostazione di GNOME che tiene le disposizioni attive.
const CHIAVE_DISPOSIZIONI: (&str, &str) = ("org.gnome.desktop.input-sources", "sources");

/// Impone alla sessione la disposizione di tastiera dichiarata, se serve.
///
/// Restituisce `true` se l'ha cambiata.
///
/// # Perche' esiste
///
/// RDP manda **posizioni**, non lettere: la lettera che ne esce la decide la
/// disposizione configurata dentro la sessione remota (§5.8). Se il client ha
/// una tastiera italiana e la sessione e' americana, i simboli non
/// corrispondono — e il modo in cui non corrispondono e' il peggiore possibile,
/// perche' le lettere sono giuste e sbagliano solo i segni di interpunzione.
///
/// # Perche' si dichiara invece di indovinarla
///
/// Perche' il client la dichiara, ma non a noi: il suo identificatore di
/// disposizione (KLID) viaggia nel Client Core Data, e IronRDP 0.13 lo tiene
/// per se' — l'ha in `ConnectionResult`, ma nessun gancio del server lo
/// consegna a chi lo usa. Finche' non lo espone — contributo a monte, come per
/// il bottone centrale del mouse — la disposizione la si dichiara qui.
///
/// # Se non e' dichiarata non si tocca nulla
///
/// Questa e' una **preferenza dell'utente**, e sta nel suo dconf: cambiarla di
/// nostra iniziativa significherebbe che ogni connessione RDP riscrive le
/// impostazioni del suo desktop. Si scrive solo se REMOTIX_TASTIERA e' stata
/// dichiarata, e solo se il valore e' diverso da quello che c'e' gia'.
pub async fn disposizione(valore: &str) -> Result<bool> {
    let voluta = gvariant_disposizioni(valore)?;

    let attuale = leggi_impostazione().await?;
    if attuale.trim() == voluta {
        debug!(disposizione = %valore, "la sessione ha gia' la disposizione voluta");
        return Ok(false);
    }

    scrivi_impostazione(&voluta).await?;
    info!(disposizione = %valore, prima = %attuale.trim(), "disposizione della tastiera impostata");
    Ok(true)
}

/// Costruisce il valore che GNOME si aspetta, convalidando cio' che si e' letto.
///
/// La convalida non e' cerimonia: il valore finisce dentro una stringa fra
/// apici, e un apice nel mezzo scriverebbe nel dconf dell'utente qualcosa di
/// diverso da cio' che si voleva. Si ammette solo cio' che i nomi XKB usano
/// davvero — `it`, `us`, `it+nodeadkeys`, `us(intl)` — e nient'altro.
fn gvariant_disposizioni(valore: &str) -> Result<String> {
    let mut voci = Vec::new();
    for disposizione in valore.split(',').map(str::trim).filter(|v| !v.is_empty()) {
        let ammessa = disposizione
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '+' | '-' | '_' | '(' | ')'));
        if !ammessa {
            bail!("disposizione «{disposizione}» non valida: ammessi lettere, cifre e + - _ ( )");
        }
        voci.push(format!("('xkb', '{disposizione}')"));
    }
    if voci.is_empty() {
        bail!("nessuna disposizione da impostare");
    }
    Ok(format!("[{}]", voci.join(", ")))
}

async fn leggi_impostazione() -> Result<String> {
    let (schema, chiave) = CHIAVE_DISPOSIZIONI;
    let uscita = tokio::process::Command::new("gsettings")
        .args(["get", schema, chiave])
        .output()
        .await
        .context("gsettings get: non installato?")?;
    if !uscita.status.success() {
        bail!(
            "gsettings get {schema} {chiave}: {}",
            String::from_utf8_lossy(&uscita.stderr).trim()
        );
    }
    Ok(String::from_utf8_lossy(&uscita.stdout).into_owned())
}

async fn scrivi_impostazione(valore: &str) -> Result<()> {
    let (schema, chiave) = CHIAVE_DISPOSIZIONI;
    let uscita = tokio::process::Command::new("gsettings")
        .args(["set", schema, chiave, valore])
        .output()
        .await
        .context("gsettings set")?;
    if !uscita.status.success() {
        bail!(
            "gsettings set {schema} {chiave}: {}",
            String::from_utf8_lossy(&uscita.stderr).trim()
        );
    }
    Ok(())
}

/// Lancia la sessione con un ambiente costruito da zero.
fn avvia(comando: &str) -> Result<()> {
    // Le due che il compositore non può indovinare: dove vive il runtime
    // dell'utente e su quale bus parlare. Le prendiamo dal nostro ambiente
    // perché siamo lo stesso utente, ma se mancassero non avrebbe senso
    // proseguire.
    let runtime = std::env::var("XDG_RUNTIME_DIR")
        .context("XDG_RUNTIME_DIR non impostata: non so dove vive la sessione")?;
    let bus = std::env::var("DBUS_SESSION_BUS_ADDRESS")
        .context("DBUS_SESSION_BUS_ADDRESS non impostata: non so su quale bus parlare")?;

    let registro = std::path::Path::new(&runtime).join("remotix-sessione.log");
    let uscita = std::fs::File::create(&registro)
        .with_context(|| format!("creazione di {}", registro.display()))?;
    let errori = uscita.try_clone().context("duplicazione del registro")?;

    let mut sessione = std::process::Command::new("setsid");
    sessione
        .arg("--fork")
        .arg("sh")
        .arg("-c")
        .arg(comando)
        // Da zero: quello che non serve non passa. In particolare **non** passa
        // `LC_ALL`, che se non fosse UTF-8 impedirebbe alle applicazioni di
        // partire (§5.9-bis) — ed è arrivata fin qui per sbaglio una volta.
        .env_clear()
        .env("XDG_RUNTIME_DIR", &runtime)
        .env("DBUS_SESSION_BUS_ADDRESS", &bus)
        // La sessione deve dichiararsi, o le applicazioni di GNOME non si
        // riconoscono a casa propria e si fermano da sole (§5.6).
        .env("XDG_CURRENT_DESKTOP", "GNOME")
        .env("XDG_SESSION_DESKTOP", "gnome")
        // Qui **serve**: l'unità della Shell porta
        // `ConditionEnvironment=XDG_SESSION_TYPE=wayland`, e senza il
        // compositore non viene avviato affatto (§5.9-bis).
        .env("XDG_SESSION_TYPE", "wayland")
        .env("LANG", locale_utf8())
        .env("HOME", std::env::var("HOME").unwrap_or_else(|_| "/root".to_owned()))
        .env("USER", std::env::var("USER").unwrap_or_default())
        .env("PATH", std::env::var("PATH").unwrap_or_else(|_| "/usr/bin:/bin".to_owned()))
        .stdin(Stdio::null())
        .stdout(Stdio::from(uscita))
        .stderr(Stdio::from(errori));

    debug!(%comando, registro = %registro.display(), "avvio la sessione grafica");
    // `setsid --fork` stacca la sessione dal nostro gruppo di processi: se
    // REMOTIX viene riavviato, il desktop dell'utente non se ne accorge.
    let esito = sessione.status().context("avvio della sessione grafica")?;
    if !esito.success() {
        bail!("l'avvio della sessione e' uscito con {esito}");
    }
    Ok(())
}

/// Una locale UTF-8, sempre.
///
/// Se quella dell'ambiente non lo è — o non c'è — si ripiega su `C.UTF-8`, che
/// esiste ovunque. Non è pignoleria: `gnome-terminal-server` si rifiuta di
/// partire con una locale non UTF-8, e l'utente si ritrova un desktop in cui i
/// programmi semplicemente non si aprono, senza un errore da nessuna parte.
fn locale_utf8() -> String {
    match std::env::var("LANG") {
        Ok(lingua) if lingua.to_ascii_uppercase().contains("UTF-8") => lingua,
        Ok(lingua) => {
            warn!(%lingua, "la locale dell'ambiente non e' UTF-8: la sessione partira' con C.UTF-8");
            "C.UTF-8".to_owned()
        }
        Err(_) => "C.UTF-8".to_owned(),
    }
}

#[cfg(test)]
mod prove {
    use super::*;

    #[test]
    fn le_disposizioni_diventano_il_valore_di_gnome() {
        assert_eq!(
            gvariant_disposizioni("it").unwrap(),
            "[('xkb', 'it')]"
        );
        // Piu' d'una: la prima e' quella attiva, le altre restano a portata di
        // scorciatoia — com'e' per chi scrive in due lingue.
        assert_eq!(
            gvariant_disposizioni("it, us").unwrap(),
            "[('xkb', 'it'), ('xkb', 'us')]"
        );
        // Le varianti si scrivono come XKB le scrive.
        assert_eq!(
            gvariant_disposizioni("it+nodeadkeys").unwrap(),
            "[('xkb', 'it+nodeadkeys')]"
        );
    }

    #[test]
    fn cio_che_scriverebbe_altro_nel_dconf_viene_rifiutato() {
        // L'apice chiuderebbe la stringa e il resto finirebbe nelle
        // impostazioni dell'utente come valore diverso da quello voluto.
        assert!(gvariant_disposizioni("it'), ('xkb', 'ru").is_err());
        assert!(gvariant_disposizioni("it; rm -rf").is_err());
        assert!(gvariant_disposizioni("").is_err());
        assert!(gvariant_disposizioni(" , ").is_err());
    }
}
