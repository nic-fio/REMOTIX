//! Prova della fase 2: cattura il desktop e ne salva alcuni fotogrammi.
//!
//! Nessun RDP. Serve a dimostrare che una sessione GNOME senza monitor puo'
//! essere ripresa, e che i fotogrammi arrivano leggibili. Si verifica
//! aprendo i PNG prodotti: se dentro c'e' il desktop, la fase e' superata.
//!
//! Va eseguito **dentro l'ambiente della sessione grafica**, perche' deve
//! parlare con lo stesso bus di Mutter:
//!
//!   XDG_RUNTIME_DIR=/run/user/1000 \
//!   DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
//!   prova-cattura
//!
//! Configurazione tramite variabili d'ambiente:
//!
//!   REMOTIX_MONITOR      connettore da riprendere   (default: monitor virtuale)
//!   REMOTIX_WIDTH        larghezza del virtuale     (default 1280)
//!   REMOTIX_HEIGHT       altezza del virtuale       (default 720)
//!   REMOTIX_FOTOGRAMMI   quanti salvarne            (default 5)
//!   REMOTIX_USCITA       cartella di destinazione   (default ./cattura)
//!   REMOTIX_LOG          livello di registro        (default info)

use std::path::PathBuf;
use std::time::Duration;

use anyhow::{Context as _, Result};
use remotix::cattura::{Cattura, Fotogramma};
use remotix::screencast::{Cursore, SessioneCattura};
use tracing::{info, warn};

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::new(
            std::env::var("REMOTIX_LOG").unwrap_or_else(|_| "info".to_owned()),
        ))
        .with_target(false)
        .init();

    let numero = |nome: &str, predefinito: u32| -> u32 {
        std::env::var(nome).ok().and_then(|v| v.parse().ok()).unwrap_or(predefinito)
    };
    let dimensione = (numero("REMOTIX_WIDTH", 1280), numero("REMOTIX_HEIGHT", 720));
    let monitor = std::env::var("REMOTIX_MONITOR").ok().filter(|v| !v.is_empty());
    let quanti: usize = std::env::var("REMOTIX_FOTOGRAMMI")
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(5);
    let uscita: PathBuf = std::env::var("REMOTIX_USCITA")
        .unwrap_or_else(|_| "cattura".to_owned())
        .into();
    std::fs::create_dir_all(&uscita)
        .with_context(|| format!("creazione di {}", uscita.display()))?;

    // Senza REMOTIX_MONITOR si chiede a Mutter un monitor virtuale della
    // dimensione voluta: e' il modo in cui lavorera' il server vero.
    let (sessione, misura) = match &monitor {
        Some(connettore) => (
            SessioneCattura::su_monitor(connettore, Cursore::Incorporato, None).await?,
            None,
        ),
        None => (
            SessioneCattura::virtuale(Cursore::Incorporato, None).await?,
            Some(dimensione),
        ),
    };
    let (_cattura, fotogrammi) = Cattura::avvia(sessione.nodo, misura).await?;

    let mut fotogrammi = fotogrammi;
    let mut salvati = 0usize;
    for indice in 0..quanti {
        let atteso = tokio::time::timeout(Duration::from_secs(15), fotogrammi.recv()).await;
        let Ok(Some(f)) = atteso else {
            warn!(indice, "nessun fotogramma entro 15 secondi");
            break;
        };
        let percorso = uscita.join(format!("fotogramma-{indice:02}.png"));
        match salva_png(&f, &percorso) {
            Ok(()) => {
                info!(
                    file = %percorso.display(),
                    larghezza = f.larghezza,
                    altezza = f.altezza,
                    stride = f.stride,
                    "salvato"
                );
                salvati += 1;
            }
            Err(e) => warn!(errore = %format!("{e:#}"), "salvataggio fallito"),
        }
    }

    sessione.chiudi().await;

    if salvati == 0 {
        anyhow::bail!("nessun fotogramma catturato");
    }
    info!(salvati, cartella = %uscita.display(), "cattura conclusa");
    Ok(())
}

/// Scrive il fotogramma in PNG.
///
/// La cattura consegna i canali in ordine B, G, R, A; il PNG li vuole in
/// ordine R, G, B, A. Scambiare i due estremi basta — ed e' anche la prova
/// che l'ordine dichiarato sia quello vero: se fosse sbagliato, l'immagine
/// uscirebbe con il rosso e il blu invertiti, cosa che si nota a colpo
/// d'occhio.
fn salva_png(f: &Fotogramma, percorso: &std::path::Path) -> Result<()> {
    let compatto = f.compatto();
    let mut rgba = compatto.into_owned();
    for pixel in rgba.chunks_exact_mut(4) {
        pixel.swap(0, 2);
    }

    let file = std::fs::File::create(percorso)?;
    let mut codificatore = png::Encoder::new(
        std::io::BufWriter::new(file),
        f.larghezza,
        f.altezza,
    );
    codificatore.set_color(png::ColorType::Rgba);
    codificatore.set_depth(png::BitDepth::Eight);
    codificatore
        .write_header()?
        .write_image_data(&rgba)
        .context("scrittura dei pixel")?;
    Ok(())
}
