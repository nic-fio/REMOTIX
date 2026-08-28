//! Codifica H.264 per la pipeline EGFX.
//!
//! # Perche' serve
//!
//! Il client Microsoft non rende i fotogrammi EGFX non compressi. Lo si e'
//! accertato leggendo `gnome-remote-desktop`, che via EGFX invia soltanto
//! RemoteFX Progressive, AVC420 e AVC444, e mai il formato non compresso.
//! AVC420 e' quindi la via obbligata verso mstsc.
//!
//! # Vincoli imposti da MS-RDPEGFX al flusso H.264
//!
//! Sono stringenti e sbagliarne uno solo produce uno schermo nero senza alcun
//! messaggio d'errore:
//!
//!   - profilo **Constrained Baseline**: niente CABAC, niente fette B,
//!     niente trasformata 8x8;
//!   - formato **Annex B**, con start code e non con prefisso di lunghezza;
//!   - **SPS e PPS presenti prima di ogni fotogramma chiave**, perche' il
//!     decodificatore del client non ha altro modo di inizializzarsi;
//!   - il **primo fotogramma deve essere un IDR**;
//!   - le dimensioni dedotte dal flusso devono corrispondere a quelle
//!     dichiarate nei metadati della regione.
//!
//! # Scelta della libreria
//!
//! Si usa OpenH264, che produce Constrained Baseline e si porta dietro la
//! propria implementazione: nessuna dipendenza di sistema da soddisfare.
//!
//! La specifica prevede `libavcodec` come strato di astrazione, per poter
//! scegliere il codificatore a runtime fra software e acceleratori delle varie
//! GPU. Quel passaggio appartiene alla fase 9; qui serve solo dimostrare che
//! con AVC420 il client Microsoft disegna. OpenH264 e' comunque uno dei
//! codificatori che `libavcodec` potrebbe scegliere, quindi non e' lavoro
//! buttato.

use anyhow::{Context as _, Result};
use openh264::encoder::{
    BitRate, Encoder, EncoderConfig, FrameRate, IntraFramePeriod, Profile, RateControlMode,
    SpsPpsStrategy, UsageType,
};
use tracing::info;

use crate::colore::Piani;

/// Codificatore H.264 legato a una risoluzione.
///
/// OpenH264 non cambia risoluzione a caldo: se lo schermo cambia dimensione si
/// costruisce un codificatore nuovo, che ricomincia da un fotogramma chiave.
/// Allinea per eccesso ai vincoli del codificatore.
///
/// Larghezza multipla di 16, altezza multipla di 64: sono i valori usati da
/// `gnome-remote-desktop`, unica fonte attendibile in materia. L'altezza a 64
/// non compare nella specifica ed e' un vincolo pratico dei codificatori.
///
/// Si arrotonda per ECCESSO e si riempie il bordo, invece di ridurre lo
/// schermo: cosi' il desktop resta esattamente della dimensione chiesta dal
/// client, senza bande nere ne' disallineamenti.
/// Quanti thread dare al codificatore.
///
/// **Sui quattro core della VM di prova non ha cambiato nulla**: misurato, da
/// due a quattro thread la codifica resta sui dodici millisecondi. OpenH264
/// spartisce il lavoro per fette, e su contenuto da desktop — dove quasi tutte
/// le fette sono quasi vuote — non c'e' granche' da spartire.
///
/// Si lascia adattivo lo stesso, perche' la macchina di prova ha quattro core e
/// quella vera ne avra' venti, ma **non lo si consideri un margine acquisito**:
/// va rimisurato li'. La voce cara e' rimasta la codifica, e la via per
/// abbatterla e' l'accelerazione hardware della fase 9, non i thread.
fn thread_codifica() -> u16 {
    std::thread::available_parallelism()
        .map(|n| u16::try_from(n.get()).unwrap_or(4))
        .unwrap_or(2)
        .clamp(1, 8)
}

fn allinea_su(v: u16, a: u16) -> u16 {
    v.div_ceil(a).max(1) * a
}

pub struct Codificatore {
    encoder: Encoder,
    /// Piani YUV allineati, riusati a ogni giro.
    ///
    /// La conversione che li riempie sta in `colore.rs` e non e' quella di
    /// openh264: misurata a 2560x1080 dentro la VM, quella costava 26 ms contro
    /// gli 11 della codifica vera e propria, perche' scorre l'immagine per
    /// colonne e passa da `f32` un pixel alla volta.
    piani: Piani,
    larghezza: u16,
    altezza: u16,
    /// Copia del flusso prodotto, per poterlo esaminare.
    ///
    /// Si attiva con REMOTIX_DUMP_H264=<percorso>. Verificare cosa si produce
    /// e' il primo passo quando il client non disegna: senza, si finisce a
    /// dare la colpa al client per un difetto proprio.
    dump: Option<std::fs::File>,
}

impl Codificatore {
    pub fn nuovo(larghezza: u16, altezza: u16) -> Result<Self> {
        // La misura arriva dal client, quindi non e' fidata: si rifiuta qui,
        // con un errore che chiude la sola connessione, invece di lasciarla
        // arrivare piu' in basso dove diventerebbe un panico.
        anyhow::ensure!(
            larghezza > 0 && altezza > 0,
            "misura impossibile per il codificatore: {larghezza}x{altezza}"
        );

        let config = EncoderConfig::new()
            // Contenuto da desktop, non da telecamera: cambia le euristiche
            // dell'encoder in modo sostanziale.
            .usage_type(UsageType::ScreenContentRealTime)
            // Constrained Baseline: e' il profilo che MS-RDPEGFX ammette.
            .profile(Profile::Baseline)
            // SPS e PPS ripetuti a ogni fotogramma chiave. Senza, il
            // decodificatore del client non riesce a inizializzarsi e resta
            // nero: e' l'errore piu' insidioso di tutta la catena.
            .sps_pps_strategy(SpsPpsStrategy::ConstantId)
            .rate_control_mode(RateControlMode::Bitrate)
            .bitrate(BitRate::from_bps(10_000_000))
            .max_frame_rate(FrameRate::from_hz(30.0))
            // Un fotogramma chiave ogni due secondi: permette a un client che
            // si aggancia a meta' flusso di ripartire in tempi ragionevoli.
            .intra_frame_period(IntraFramePeriod::from_num_frames(60))
            // Le fette saltate creerebbero buchi in un'immagine di prova quasi
            // ferma, dove vogliamo vedere ogni fotogramma.
            .skip_frames(false)
            // Tanti thread quanti sono i core, non due: la conversione di
            // colore e la codifica non girano mai insieme — l'una finisce prima
            // che l'altra cominci — quindi non si contendono nulla.
            .num_threads(thread_codifica());

        let encoder = Encoder::with_api_config(openh264::OpenH264API::from_source(), config)
            .context("creazione del codificatore H.264")?;

        let larghezza_cod = allinea_su(larghezza, 16);
        let altezza_cod = allinea_su(altezza, 64);

        info!(
            larghezza,
            altezza,
            larghezza_cod,
            altezza_cod,
            "codificatore H.264 pronto (Constrained Baseline)"
        );

        let dump = std::env::var("REMOTIX_DUMP_H264")
            .ok()
            .filter(|p| !p.is_empty())
            .and_then(|p| match std::fs::File::create(&p) {
                Ok(f) => {
                    info!(percorso = %p, "salvo il flusso H.264 per analisi");
                    Some(f)
                }
                Err(e) => {
                    tracing::warn!(percorso = %p, errore = %e, "impossibile salvare il flusso");
                    None
                }
            });

        Ok(Self {
            encoder,
            piani: Piani::nuovi(usize::from(larghezza_cod), usize::from(altezza_cod)),
            larghezza,
            altezza,
            dump,
        })
    }

    /// Fa sì che il prossimo fotogramma sia un fotogramma chiave.
    ///
    /// Serve a rimettere d'accordo le due ricostruzioni quando si sospetta che
    /// il client non abbia ricevuto qualcosa: un fotogramma chiave non dipende
    /// da nulla di precedente, quindi ricuce la divergenza qualunque ne sia
    /// stata la causa. Costa molti più byte di un fotogramma normale, e per
    /// questo lo si chiede solo quando serve davvero.
    pub fn forza_chiave(&mut self) {
        self.encoder.force_intra_frame();
    }

    pub fn dimensione(&self) -> (u16, u16) {
        (self.larghezza, self.altezza)
    }

    /// Converte un fotogramma BGRA e lo codifica, restituendo un flusso Annex B.
    ///
    /// `bgra` deve contenere esattamente `larghezza * altezza * 4` byte, con i
    /// canali in ordine B, G, R, A — lo stesso che produce l'immagine di prova
    /// e che produrra' la cattura da PipeWire.
    pub fn codifica(&mut self, bgra: &[u8]) -> Result<Vec<u8>> {
        let attesi = usize::from(self.larghezza) * usize::from(self.altezza) * 4;
        anyhow::ensure!(
            bgra.len() == attesi,
            "fotogramma di {} byte invece dei {attesi} attesi",
            bgra.len()
        );

        let inizio = std::time::Instant::now();

        let (w, h) = (usize::from(self.larghezza), usize::from(self.altezza));

        // Conversione e riempimento del bordo in un passaggio solo: leggere
        // due volte undici megabyte per poi convertirli era meta' del costo.
        crate::colore::bgra_in_yuv(bgra, w * 4, w, h, &mut self.piani);
        let dopo_yuv = std::time::Instant::now();

        let flusso = self
            .encoder
            .encode(&self.piani.come_sorgente())
            .context("codifica del fotogramma")?;

        let mut uscita = Vec::new();
        flusso.write_vec(&mut uscita);
        let dopo_h264 = std::time::Instant::now();

        // Le tre fasi si misurano separate perche' costano in modo molto
        // diverso e si ottimizzano in modo molto diverso: senza distinguerle si
        // finisce a limare quella che non pesa.
        tracing::debug!(
            ms_yuv = dopo_yuv.duration_since(inizio).as_secs_f64() * 1e3,
            ms_h264 = dopo_h264.duration_since(dopo_yuv).as_secs_f64() * 1e3,
            byte = uscita.len(),
            "tempi di codifica"
        );

        if let Some(f) = self.dump.as_mut() {
            use std::io::Write as _;
            let _ = f.write_all(&uscita);
        }

        Ok(uscita)
    }
}
