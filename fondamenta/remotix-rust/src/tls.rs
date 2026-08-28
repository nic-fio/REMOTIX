//! Identita' TLS del server.
//!
//! REMOTIX accetta soltanto connessioni cifrate: e' una delle decisioni fissate
//! nella specifica, e non e' prevista alcuna modalita' in chiaro.
//!
//! Al primo avvio, se non trova un certificato, se ne genera uno autofirmato e
//! lo conserva. E' il comportamento sensato per un servizio personale: senza,
//! l'utente dovrebbe procurarsi un certificato prima ancora di poter provare il
//! programma. Il client mostrera' un avviso perche' il certificato non e'
//! firmato da un'autorita' riconosciuta, ed e' corretto che lo faccia.

use std::path::{Path, PathBuf};

use anyhow::{Context as _, Result};
use ironrdp_server::TlsIdentityCtx;
use ironrdp_server::tokio_rustls::TlsAcceptor;
use tracing::info;

/// Percorsi del certificato e della chiave privata.
pub struct Identita {
    pub certificato: PathBuf,
    pub chiave: PathBuf,
}

impl Identita {
    pub fn in_cartella(cartella: &Path) -> Self {
        Self {
            certificato: cartella.join("remotix-cert.pem"),
            chiave: cartella.join("remotix-key.pem"),
        }
    }

    /// Genera il certificato autofirmato se manca, poi costruisce l'accettatore TLS.
    pub fn accettatore(&self) -> Result<TlsAcceptor> {
        if !self.certificato.exists() || !self.chiave.exists() {
            self.genera_autofirmato()
                .context("generazione del certificato autofirmato")?;
        }

        let identita = TlsIdentityCtx::init_from_paths(&self.certificato, &self.chiave)
            .context("lettura di certificato e chiave")?;

        identita.make_acceptor().context("costruzione dell'accettatore TLS")
    }

    fn genera_autofirmato(&self) -> Result<()> {
        use rcgen::{CertificateParams, DistinguishedName, DnType, KeyPair};

        if let Some(cartella) = self.certificato.parent() {
            std::fs::create_dir_all(cartella)
                .with_context(|| format!("creazione di {}", cartella.display()))?;
        }

        let nome_host = hostname().unwrap_or_else(|| "remotix".to_owned());

        let mut nome = DistinguishedName::new();
        nome.push(DnType::CommonName, nome_host.clone());
        nome.push(DnType::OrganizationName, "REMOTIX");

        let mut parametri = CertificateParams::new(vec![nome_host.clone(), "localhost".to_owned()])
            .context("parametri del certificato")?;
        parametri.distinguished_name = nome;

        let coppia = KeyPair::generate().context("generazione della chiave")?;
        let certificato = parametri
            .self_signed(&coppia)
            .context("autofirma del certificato")?;

        std::fs::write(&self.certificato, certificato.pem())
            .with_context(|| format!("scrittura di {}", self.certificato.display()))?;

        // La chiave privata nasce gia' con i permessi giusti, non li riceve
        // dopo.
        //
        // Scriverla e poi correggere i permessi lascia una finestra — breve ma
        // reale — in cui la chiave sta su disco leggibile da chiunque, secondo
        // la umask di chi ha avviato il servizio. Su una macchina multiutente,
        // che e' esattamente il caso d'uso di REMOTIX, quella finestra basta.
        // Si crea quindi il file gia' a 0600 e la si scrive dentro.
        {
            use std::io::Write as _;
            let mut apertura = std::fs::OpenOptions::new();
            apertura.write(true).create(true).truncate(true);
            #[cfg(unix)]
            {
                use std::os::unix::fs::OpenOptionsExt as _;
                apertura.mode(0o600);
            }
            let mut file = apertura
                .open(&self.chiave)
                .with_context(|| format!("creazione di {}", self.chiave.display()))?;
            file.write_all(coppia.serialize_pem().as_bytes())
                .with_context(|| format!("scrittura di {}", self.chiave.display()))?;
        }

        // Un file preesistente conserva i propri permessi anche se lo si
        // ritronca: si insiste, per il caso di una chiave lasciata la' da una
        // versione precedente.
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt as _;
            std::fs::set_permissions(&self.chiave, std::fs::Permissions::from_mode(0o600))
                .context("permessi della chiave privata")?;
        }

        info!(
            certificato = %self.certificato.display(),
            "generato un certificato autofirmato per {nome_host}"
        );
        Ok(())
    }
}

fn hostname() -> Option<String> {
    std::fs::read_to_string("/etc/hostname")
        .ok()
        .map(|s| s.trim().to_owned())
        .filter(|s| !s.is_empty())
}
