//! L'autenticazione: PAM.
//!
//! # Perche' PAM e non un elenco di password nostro
//!
//! Perche' e' il meccanismo con cui la macchina decide **gia'** chi puo'
//! entrare: la stessa password del terminale, le stesse regole di scadenza, gli
//! stessi blocchi dopo troppi tentativi. Scrivere un controllo nostro
//! significherebbe mantenere per sempre una seconda politica di accesso,
//! destinata a divergere da quella vera nel momento peggiore.
//!
//! # Dove si aggancia
//!
//! IronRDP 0.13 espone `CredentialValidator`: viene chiamato quando il client
//! consegna le credenziali nel `ClientInfoPdu`, prima che la sessione sia
//! stabilita. Se si rifiuta, la libreria manda al client un errore esplicito —
//! non una connessione che cade e basta — e chiude.
//!
//! # Il servizio PAM
//!
//! PAM sceglie le regole in base al **nome del servizio**, che e' un file in
//! `/etc/pam.d/`. REMOTIX usa `remotix`; il file lo installa il confezionamento
//! della fase 11, e per ora `provision-vm.sh`.
//!
//! Se quel file manca, PAM ricade su `/etc/pam.d/other`, che su Debian e Ubuntu
//! **nega tutto**. Il risultato sarebbe un server che rifiuta chiunque senza
//! dire perche', quindi all'avvio se ne verifica l'esistenza e lo si dichiara.
//!
//! # Cosa non fa (ancora)
//!
//! Solo `authenticate` e `acct_mgmt`: «la credenziale e' buona» e «l'account e'
//! utilizzabile» — scadenze e blocchi compresi. **Non** apre una sessione PAM:
//! quella serve quando REMOTIX avviera' la sessione grafica, perche' e' cio' che
//! fa comparire la sessione in `logind`, e va tenuta aperta quanto la sessione
//! stessa.

use core::sync::atomic::{AtomicBool, Ordering};
use std::path::Path;
use std::sync::Arc;

use anyhow::{Context as _, Result};
use ironrdp_server::{CredentialDecision, CredentialValidationError, CredentialValidator, Credentials};
use pam_client2::conv_mock::Conversation;
use pam_client2::{Context as ContestoPam, Flag};
use tracing::{debug, info, warn};

/// Nome predefinito del servizio PAM, cioe' del file in `/etc/pam.d/`.
pub const SERVIZIO_PREDEFINITO: &str = "remotix";


/// Chi ha superato l'autenticazione, e chi no.
///
/// # Perche' non basta il validatore
///
/// Perche' IronRDP 0.13 lo interpella **solo se il client ha mandato delle
/// credenziali**: se il `ClientInfoPdu` non ne porta, la libreria scrive
/// `Skipping credential validation` e **lascia proseguire la connessione**
/// (`server.rs`, funzione `client_accepted`). Un client che non dichiara nulla
/// entra quindi senza che PAM venga mai chiamato — segnalato dall'utente il
/// 3 agosto, ed e' un buco di sicurezza vero, non teorico.
///
/// La guardia rovescia la regola: si parte da **negato** a ogni connessione, e
/// solo il validatore, accettando, concede. Chi non passa di li' non entra.
pub struct Guardia {
    concesso: AtomicBool,
    /// Vero quando l'autenticazione e' stata disattivata di proposito.
    aperta: bool,
}

impl Guardia {
    pub fn nuova(aperta: bool) -> Arc<Self> {
        Arc::new(Self {
            concesso: AtomicBool::new(false),
            aperta,
        })
    }

    /// Da chiamare **all'inizio di ogni connessione**: nessuno eredita
    /// l'autenticazione di chi lo ha preceduto.
    pub fn azzera(&self) {
        self.concesso.store(false, Ordering::SeqCst);
    }

    fn concedi(&self) {
        self.concesso.store(true, Ordering::SeqCst);
    }

    pub fn concesso(&self) -> bool {
        self.aperta || self.concesso.load(Ordering::SeqCst)
    }
}

/// Verifica le credenziali contro PAM.
pub struct Autenticatore {
    servizio: String,
    /// L'unico utente che puo' entrare: quello di cui REMOTIX serve il desktop.
    ///
    /// # Perche' non basta che PAM dica di si'
    ///
    /// Perche' PAM risponde a una domanda diversa da quella che ci interessa:
    /// dice «questa credenziale e' buona», non «questa persona ha diritto a
    /// **questa** sessione». REMOTIX oggi ne serve una sola — quella dell'utente
    /// che lo esegue — quindi chiunque altro, con la propria password vera, si
    /// troverebbe dentro il desktop di un altro. Non e' un dettaglio di
    /// scrupolo: e' accesso ai dati altrui, ed e' peggio della doppia sessione
    /// che §3.4 vieta.
    ///
    /// Segnalato dall'utente il 3 agosto, come violazione della specifica. Lo
    /// era.
    utente: String,
    guardia: Arc<Guardia>,
}

impl Autenticatore {
    /// Prepara l'autenticatore e **dichiara** se il servizio PAM esiste.
    ///
    /// L'avviso non e' pignoleria: senza quel file nessuno entra, e il sintomo
    /// — ogni credenziale rifiutata, comprese quelle giuste — porta a cercare
    /// il guasto nella password invece che nella configurazione.
    pub fn nuovo(servizio: impl Into<String>, utente: impl Into<String>, guardia: Arc<Guardia>) -> Self {
        let servizio = servizio.into();
        let utente = utente.into();
        let file = Path::new("/etc/pam.d").join(&servizio);
        if file.exists() {
            info!(servizio = %servizio, utente = %utente, "autenticazione PAM attiva");
        } else {
            warn!(
                servizio = %servizio,
                file = %file.display(),
                "il servizio PAM non esiste: PAM ricadra' su «other», che nega tutto"
            );
        }
        Self {
            servizio,
            utente,
            guardia,
        }
    }
}

/// Il nome dell'utente che sta eseguendo REMOTIX.
///
/// Si ricava dall'uid effettivo — l'identita' con cui il sistema ci vede —
/// leggendo `/etc/passwd`, e non da `$USER`, che e' solo una convenzione: chi
/// avvia il server con `sudo -u` o da un'unita' systemd puo' facilmente
/// ritrovarsi una `$USER` che parla di qualcun altro. Se `/etc/passwd` non
/// bastasse — utenti che arrivano da LDAP o da altre fonti NSS — si ripiega su
/// `$USER`, e se nemmeno quella c'e' si fallisce **all'avvio**: un server che
/// non sa di chi sia la sessione che serve non deve aprire la porta.
pub fn utente_del_processo() -> Result<String> {
    let uid = uid_effettivo()?;
    let passwd = std::fs::read_to_string("/etc/passwd").unwrap_or_default();
    for riga in passwd.lines() {
        let mut campi = riga.split(':');
        let (Some(nome), Some(_), Some(numero)) = (campi.next(), campi.next(), campi.next()) else {
            continue;
        };
        if numero.parse::<u32>() == Ok(uid) {
            return Ok(nome.to_owned());
        }
    }
    if let Ok(nome) = std::env::var("USER") {
        if !nome.is_empty() {
            warn!(uid, %nome, "utente non trovato in /etc/passwd: si usa $USER");
            return Ok(nome);
        }
    }
    anyhow::bail!("non riesco a stabilire quale utente sta eseguendo REMOTIX (uid {uid})")
}

/// L'uid effettivo, letto da `/proc`.
fn uid_effettivo() -> Result<u32> {
    let stato = std::fs::read_to_string("/proc/self/status").context("/proc/self/status")?;
    for riga in stato.lines() {
        if let Some(valori) = riga.strip_prefix("Uid:") {
            if let Some(effettivo) = valori.split_whitespace().nth(1) {
                return effettivo.parse().context("uid non numerico");
            }
        }
    }
    anyhow::bail!("nessuna riga «Uid:» in /proc/self/status")
}

/// La verifica vera, sincrona: PAM e' una libreria che blocca.
fn verifica(servizio: &str, utente: &str, password: &str) -> Result<bool> {
    // La conversazione serve a rispondere alle domande dei moduli. Qui non c'e'
    // nessuno davanti a un terminale: si risponde con le credenziali che il
    // client ha gia' mandato, e alle altre domande non si risponde.
    let mut contesto = ContestoPam::new(
        servizio,
        Some(utente),
        Conversation::with_credentials(utente, password),
    )
    .context("apertura del contesto PAM")?;

    // `authenticate` dice se la credenziale e' buona; `acct_mgmt` se l'account
    // e' utilizzabile — password scaduta, utente bloccato, orari consentiti.
    // Servono entrambe: la prima da sola lascerebbe entrare un account
    // disabilitato.
    if let Err(errore) = contesto.authenticate(Flag::NONE) {
        debug!(utente, errore = %errore, "credenziale rifiutata da PAM");
        return Ok(false);
    }
    if let Err(errore) = contesto.acct_mgmt(Flag::NONE) {
        debug!(utente, errore = %errore, "account non utilizzabile secondo PAM");
        return Ok(false);
    }
    Ok(true)
}

#[async_trait::async_trait]
impl CredentialValidator for Autenticatore {
    async fn validate(
        &self,
        credenziali: &Credentials,
    ) -> Result<CredentialDecision, CredentialValidationError> {
        let utente = credenziali.username.clone();
        let password = credenziali.password.clone();
        let servizio = self.servizio.clone();

        // Un nome vuoto non lo si sottopone nemmeno a PAM: alcuni client
        // aprono la connessione senza credenziali per vedere cosa risponde il
        // server, e ogni tentativo costerebbe i due secondi di ritardo che
        // `pam_unix` impone ai fallimenti.
        if utente.is_empty() {
            warn!("connessione senza nome utente, rifiutata");
            return Ok(CredentialDecision::Reject);
        }

        // **Prima** di PAM: la sessione che REMOTIX serve e' una sola, e
        // appartiene a un utente preciso. A chi non e' lui non si chiede nemmeno
        // la password — non perche' non l'avrebbe, ma perche' non c'e' niente
        // che possiamo dargli senza dargli la sessione di un altro.
        //
        // Il registro dice tutti e due i nomi: il caso «ho sbagliato utente» e
        // il caso «qualcuno prova a entrare» si distinguono solo cosi'.
        if utente != self.utente {
            warn!(
                arrivato = %utente,
                atteso = %self.utente,
                "connessione rifiutata: REMOTIX serve la sessione di un altro utente"
            );
            return Ok(CredentialDecision::Reject);
        }

        // PAM blocca — di proposito, sui fallimenti — e va tenuto fuori dal
        // ciclo asincrono: e' la regola 7 di SPECIFICA.md §5.7 applicata qui.
        let esito = tokio::task::spawn_blocking(move || {
            verifica(&servizio, &utente, &password)
        })
        .await;

        match esito {
            Ok(Ok(true)) => {
                info!(utente = %credenziali.username, "autenticato");
                // **Solo qui** si concede: e' l'unico punto del programma che
                // sa che PAM ha detto di si'.
                self.guardia.concedi();
                Ok(CredentialDecision::Accept)
            }
            Ok(Ok(false)) => {
                // Il nome utente si registra, la password no: questo registro
                // finisce nei file, e una password rifiutata e' quasi sempre
                // quella giusta di qualcun altro, o la propria con un refuso
                // che la rende ancora riconoscibile.
                warn!(utente = %credenziali.username, "credenziali rifiutate");
                Ok(CredentialDecision::Reject)
            }
            // Il guasto del meccanismo e' cosa diversa dal rifiuto, e va
            // distinto: qui non si e' potuto decidere, e la libreria chiude la
            // connessione dichiarandolo.
            Ok(Err(errore)) => Err(CredentialValidationError::new(ErrorePam(format!("{errore:#}")))),
            Err(errore) => Err(CredentialValidationError::new(ErrorePam(errore.to_string()))),
        }
    }
}

/// Guasto del meccanismo di autenticazione, non credenziale sbagliata.
#[derive(Debug)]
struct ErrorePam(String);

impl core::fmt::Display for ErrorePam {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        write!(f, "PAM: {}", self.0)
    }
}

impl core::error::Error for ErrorePam {}
