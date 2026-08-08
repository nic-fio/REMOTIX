//! Strumento di prova della fase 5: apre una **vera** sessione grafica locale.
//!
//! # A cosa serve
//!
//! La regola di §3.4 — la sessione locale vince — non si puo' provare a parole:
//! serve una sessione che `logind` consideri grafica e attaccata a un seat.
//! Nella VM non c'e' nessuno che si sieda davanti allo schermo, quindi la si
//! apre da qui.
//!
//! Non e' una simulazione: la sessione e' registrata in `logind` come tutte le
//! altre, con `Type=wayland`, `Seat=seat0`, `Class=user`. `loginctl` la elenca,
//! REMOTIX la vede. L'unica cosa che manca e' un compositore che ci giri dentro,
//! e a questa prova non serve.
//!
//! # Come
//!
//! Aprendo una sessione PAM. E' cio' che fanno `login`, `sshd` e i gestori di
//! accesso grafico: `pam_systemd` legge dall'**ambiente PAM** — non da quello
//! del processo — il tipo di sessione, il seat e il terminale virtuale, e
//! registra la sessione in logind. Finche' la sessione PAM resta aperta, la
//! sessione logind resta viva.
//!
//! # ⚠ Va avviato **fuori da ogni sessione**, o non fa nulla
//!
//! Costato mezz'ora il 3 agosto: lanciato da una shell SSH, `pam_unix` apriva
//! la sessione e `pam_systemd` **non registrava niente**, in silenzio. Il
//! motivo: `pam_systemd` non crea una sessione dentro un'altra sessione — vede
//! che il processo chiamante sta gia' in `session-NNN.scope` e si ferma li'.
//!
//! Il rimedio e' avviarlo come unita' transitoria, che nasce in `system.slice`
//! e non appartiene a nessuna sessione:
//!
//! ```bash
//! sudo systemd-run --collect --quiet --unit=remotix-finta-locale \
//!      /home/nicfio/finta-sessione-locale nicfio
//! # ... la prova ...
//! sudo systemctl stop remotix-finta-locale       # la sessione si chiude
//! ```
//!
//! Serve `root`: logind lascia creare sessioni per conto d'altri solo a lui, e
//! il servizio PAM di prova lo riconosce con `pam_rootok`. A chi root non e' —
//! caso che qui non capita, ma il file PAM resta sulla macchina — viene chiesta
//! la password vera, che si legge dalla prima riga dello **standard input** per
//! non farla comparire nell'elenco dei processi.
//!
//! # ⚠ Solo nella VM di prova
//!
//! Aprire una sessione grafica dove nessuno e' seduto e' un'operazione che ha
//! senso solo per provare il rifiuto. Su una macchina vera terrebbe fuori
//! l'utente legittimo dal proprio RDP, e il sintomo — «rifiuta sempre» — non
//! farebbe pensare a un processo dimenticato in secondo piano.

use std::io::BufRead as _;

use anyhow::{Context as _, Result, bail};
use pam_client2::conv_mock::Conversation;
use pam_client2::{Context as ContestoPam, Flag};

/// Il servizio PAM di prova: `auth`/`account` veri, e `pam_systemd` nella
/// sezione `session`, che e' cio' che qui interessa. Lo installa
/// `provision-vm.sh`.
const SERVIZIO: &str = "remotix-prova-locale";

/// Il terminale virtuale che si dichiara.
///
/// Uno alto, per non contendersi con nulla quello della console: il numero non
/// deve corrispondere a un VT davvero in uso, perche' nessuno ci disegnera'
/// sopra.
const VT: &str = "7";

#[tokio::main]
async fn main() -> Result<()> {
    let utente = std::env::args().nth(1).unwrap_or_else(|| "nicfio".to_owned());

    // Se non arriva nulla — standard input chiuso, che e' il caso quando lo
    // avvia `systemd-run` — si prosegue con la password vuota: da root basta
    // `pam_rootok`.
    let mut password = String::new();
    std::io::stdin()
        .lock()
        .read_line(&mut password)
        .context("lettura della password dallo standard input")?;
    let password = password.trim_end_matches('\n').to_owned();

    let mut contesto = ContestoPam::new(
        SERVIZIO,
        Some(&utente),
        Conversation::with_credentials(&utente, &password),
    )
    .context("apertura del contesto PAM")?;

    contesto
        .authenticate(Flag::NONE)
        .context("autenticazione fallita")?;
    contesto
        .acct_mgmt(Flag::NONE)
        .context("account non utilizzabile")?;

    // Queste tre righe sono tutta la prova: sono l'unica differenza fra una
    // sessione testuale e una che occupa lo schermo. `pam_systemd` le legge
    // dall'ambiente PAM, che e' un'altra cosa dall'ambiente del processo — non
    // basterebbe esportarle nella shell.
    contesto
        .putenv("XDG_SESSION_TYPE=wayland")
        .context("XDG_SESSION_TYPE")?;
    contesto.putenv("XDG_SEAT=seat0").context("XDG_SEAT")?;
    contesto
        .putenv(format!("XDG_VTNR={VT}"))
        .context("XDG_VTNR")?;
    // Esplicita, benche' sia il valore predefinito: `greeter` e `lock-screen`
    // sono classi che REMOTIX ignora di proposito, e qui vogliamo la classe che
    // conta davvero.
    contesto
        .putenv("XDG_SESSION_CLASS=user")
        .context("XDG_SESSION_CLASS")?;

    let sessione = contesto
        .open_session(Flag::NONE)
        .context("apertura della sessione PAM (serve root?)")?;

    let id = sessione
        .envlist()
        .iter()
        .find_map(|voce| {
            let voce = voce.to_string();
            voce.strip_prefix("XDG_SESSION_ID=").map(str::to_owned)
        })
        .unwrap_or_else(|| "?".to_owned());

    // Su una riga sola e subito: chi lancia questo strumento da uno script
    // aspetta questa riga per sapere che puo' proseguire.
    println!("sessione {id} aperta (wayland su seat0, utente {utente})");
    usa_stdout()?;

    // Si resta vivi finche' non ci si dice di smettere: la sessione logind vive
    // quanto questo processo. Alla chiusura ordinata la si chiude come si deve;
    // se invece arriva un segnale piu' brusco, logind se ne accorge lo stesso
    // perche' il processo leader e' questo.
    let mut termina = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
        .context("attesa di SIGTERM")?;
    tokio::select! {
        _ = tokio::signal::ctrl_c() => {}
        _ = termina.recv() => {}
    }

    drop(sessione);
    println!("sessione chiusa");
    usa_stdout()?;
    Ok(())
}

/// Svuota lo standard output.
///
/// Serve perche' questo processo viene quasi sempre avviato con l'uscita
/// rediretta su un file e letto da uno script che aspetta quella riga: senza
/// svuotare, la riga resterebbe nel tampone fino alla fine del processo — cioe'
/// fino a dopo la prova, che nel frattempo sarebbe rimasta ad aspettarla.
fn usa_stdout() -> Result<()> {
    use std::io::Write as _;
    if std::io::stdout().flush().is_err() {
        bail!("standard output non scrivibile");
    }
    Ok(())
}
