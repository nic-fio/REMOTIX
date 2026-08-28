//! Conversione da BGRA a YUV 4:2:0, che è il passaggio più caro della catena.
//!
//! # Perché non si usa quella di openh264
//!
//! Misurato sul campo il 2 agosto, a 2560×1080 dentro la VM: la conversione di
//! openh264 costa **26 millisecondi**, contro gli 11 della codifica H.264 vera e
//! propria. Il passaggio che tutti darebbero per accessorio pesava più del
//! doppio di quello che sembra il lavoro pesante.
//!
//! Il motivo si legge nel suo codice: scorre l'immagine **per colonne**
//! (`for i in 0..width/2 { for j in 0..height/2 }`), che su un fotogramma da
//! undici megabyte significa un salto in memoria a ogni pixel. In più passa da
//! `f32` e chiama un tratto per ogni singolo pixel.
//!
//! Qui si fa la stessa cosa per righe, in aritmetica intera e su tutti i core
//! disponibili.
//!
//! # I coefficienti sono gli stessi
//!
//! Sono i BT.601 a gamma ridotta, presi dalla versione di openh264 perché i
//! colori devono restare identici a prima: i valori in virgola di quel codice
//! — 0,2578125 e compagnia — sono esattamente 66/256, 129/256 e 25/256, quindi
//! si possono scrivere come interi senza cambiare un solo pixel.
//!
//! # Il bordo si assorbe qui
//!
//! Il codificatore vuole misure allineate (larghezza multipla di 16, altezza di
//! 64) e il desktop non lo è quasi mai. Invece di copiare il fotogramma in un
//! riquadro più grande e poi convertirlo — due passaggi su undici megabyte — si
//! legge direttamente dalla sorgente e si **replica l'ultima riga e l'ultima
//! colonna** mentre si converte. Replicare invece di annerire evita che il
//! codificatore spenda bit su un salto netto di colore lungo il margine.

use std::num::NonZeroUsize;

/// Massimo numero di thread su cui distribuire la conversione.
///
/// La VM ne ha quattro. Prenderli tutti va bene: la conversione dura pochi
/// millisecondi e non c'è nient'altro che stia girando nel frattempo, perché il
/// fotogramma successivo non arriva finché questo non è partito.
const THREAD_MASSIMI: usize = 8;

/// Quante righe di sorgente servono almeno per giustificare un thread in più.
///
/// Sotto questa soglia il costo di avviare il thread supera il lavoro che gli si
/// darebbe.
const RIGHE_MINIME_PER_THREAD: usize = 64;

/// Piani YUV 4:2:0 di un fotogramma allineato.
pub struct Piani {
    pub y: Vec<u8>,
    pub u: Vec<u8>,
    pub v: Vec<u8>,
    larghezza: usize,
    altezza: usize,
}

impl Piani {
    /// Alloca i piani per un fotogramma della misura **allineata** indicata.
    pub fn nuovi(larghezza: usize, altezza: usize) -> Self {
        assert!(
            larghezza.is_multiple_of(2) && altezza.is_multiple_of(2),
            "misure dispari"
        );
        Self {
            y: vec![0; larghezza * altezza],
            u: vec![128; larghezza / 2 * (altezza / 2)],
            v: vec![128; larghezza / 2 * (altezza / 2)],
            larghezza,
            altezza,
        }
    }

    pub fn dimensione(&self) -> (usize, usize) {
        (self.larghezza, self.altezza)
    }

    /// Vista sui piani nella forma che il codificatore si aspetta.
    pub fn come_sorgente(&self) -> openh264::formats::YUVSlices<'_> {
        openh264::formats::YUVSlices::new(
            (&self.y, &self.u, &self.v),
            (self.larghezza, self.altezza),
            (self.larghezza, self.larghezza / 2, self.larghezza / 2),
        )
    }
}

/// Converte un fotogramma BGRA nei piani YUV, riempiendo il bordo.
///
/// `bgra` è la sorgente, larga `larghezza` pixel utili con righe distanti
/// `stride` byte — lo stride autorevole è quello dichiarato dal produttore, mai
/// dedotto da `larghezza * 4` (vedi `SPECIFICA.md` §5.6).
///
/// I piani possono essere più grandi della sorgente: la parte eccedente viene
/// riempita replicando l'ultima riga e l'ultima colonna.
pub fn bgra_in_yuv(
    bgra: &[u8],
    stride: usize,
    larghezza: usize,
    altezza: usize,
    piani: &mut Piani,
) {
    let (wc, hc) = (piani.larghezza, piani.altezza);
    // Questi controlli sono raggiungibili da misure che decide il **client**:
    // sono quindi una via per farci cadere, non solo una rete per gli errori di
    // programmazione. Vanno tenuti larghi quanto basta a coprire ogni misura
    // sensata — un desktop largo un pixel e' assurdo ma non deve far cadere la
    // connessione — e chi chiama deve rifiutare prima le misure impossibili.
    assert!(larghezza <= wc && altezza <= hc, "sorgente più grande dei piani");
    assert!(larghezza >= 1 && altezza >= 1, "sorgente vuota");
    assert!(bgra.len() >= (altezza - 1) * stride + larghezza * 4, "sorgente corta");

    let coppie = hc / 2; // ogni giro tratta due righe, che condividono un croma
    let thread = numero_thread(coppie);

    let mezza = wc / 2;
    // Le bande sono disgiunte: ogni thread scrive righe Y e righe croma che
    // nessun altro tocca, quindi si possono spartire le fette senza lucchetti.
    let coppie_per_banda = coppie.div_ceil(thread);
    let righe_y_per_banda = coppie_per_banda * 2;

    let bande_y = piani.y.chunks_mut(righe_y_per_banda * wc);
    let bande_u = piani.u.chunks_mut(coppie_per_banda * mezza);
    let bande_v = piani.v.chunks_mut(coppie_per_banda * mezza);

    std::thread::scope(|ambito| {
        for (indice, ((by, bu), bv)) in bande_y.zip(bande_u).zip(bande_v).enumerate() {
            let prima_coppia = indice * coppie_per_banda;
            ambito.spawn(move || {
                banda(bgra, stride, larghezza, altezza, wc, mezza, prima_coppia, by, bu, bv);
            });
        }
    });
}

/// Converte una banda di righe. Gira su un thread suo.
#[expect(clippy::too_many_arguments, reason = "è una funzione interna, non un'interfaccia")]
fn banda(
    bgra: &[u8],
    stride: usize,
    larghezza: usize,
    altezza: usize,
    wc: usize,
    mezza: usize,
    prima_coppia: usize,
    y_banda: &mut [u8],
    u_banda: &mut [u8],
    v_banda: &mut [u8],
) {
    let ultima_colonna = (larghezza - 1) * 4;

    for (locale, coppia) in (prima_coppia..).take(u_banda.len() / mezza).enumerate() {
        let riga_alta = coppia * 2;
        let riga_bassa = riga_alta + 1;

        // Oltre il fondo della sorgente si replica l'ultima riga.
        let sorgente_alta = &bgra[riga_alta.min(altezza - 1) * stride..];
        let sorgente_bassa = &bgra[riga_bassa.min(altezza - 1) * stride..];

        let (y_alta, y_bassa) = {
            let inizio = locale * 2 * wc;
            let (a, resto) = y_banda[inizio..].split_at_mut(wc);
            (a, &mut resto[..wc])
        };
        let u_riga = &mut u_banda[locale * mezza..(locale + 1) * mezza];
        let v_riga = &mut v_banda[locale * mezza..(locale + 1) * mezza];

        for colonna in 0..mezza {
            // Oltre il bordo destro si replica l'ultima colonna.
            let sx = (colonna * 2 * 4).min(ultima_colonna);
            let dx = (colonna * 2 * 4 + 4).min(ultima_colonna);

            let p00 = pixel(sorgente_alta, sx);
            let p01 = pixel(sorgente_alta, dx);
            let p10 = pixel(sorgente_bassa, sx);
            let p11 = pixel(sorgente_bassa, dx);

            y_alta[colonna * 2] = luma(p00);
            y_alta[colonna * 2 + 1] = luma(p01);
            y_bassa[colonna * 2] = luma(p10);
            y_bassa[colonna * 2 + 1] = luma(p11);

            // Il croma è uno solo per quadretto di quattro pixel: si fa la
            // media, come nella versione di riferimento.
            let r = (p00.0 + p01.0 + p10.0 + p11.0) / 4;
            let g = (p00.1 + p01.1 + p10.1 + p11.1) / 4;
            let b = (p00.2 + p01.2 + p10.2 + p11.2) / 4;
            u_riga[colonna] = croma_u((r, g, b));
            v_riga[colonna] = croma_v((r, g, b));
        }
    }
}

/// Legge un pixel BGRA come terna (R, G, B).
#[inline(always)]
fn pixel(riga: &[u8], offset: usize) -> (i32, i32, i32) {
    (
        i32::from(riga[offset + 2]),
        i32::from(riga[offset + 1]),
        i32::from(riga[offset]),
    )
}

// I tre coefficienti sono quelli di openh264 scritti come interi su 256:
// 0,2578125 = 66/256, 0,50390625 = 129/256, 0,09765625 = 25/256, e così via.
// Cambiarli sposterebbe i colori rispetto a prima.

#[inline(always)]
fn luma((r, g, b): (i32, i32, i32)) -> u8 {
    (((66 * r + 129 * g + 25 * b) >> 8) + 16) as u8
}

#[inline(always)]
fn croma_u((r, g, b): (i32, i32, i32)) -> u8 {
    (((-38 * r - 74 * g + 112 * b) >> 8) + 128).clamp(0, 255) as u8
}

#[inline(always)]
fn croma_v((r, g, b): (i32, i32, i32)) -> u8 {
    (((112 * r - 94 * g - 18 * b) >> 8) + 128).clamp(0, 255) as u8
}

fn numero_thread(coppie: usize) -> usize {
    let disponibili = std::thread::available_parallelism()
        .map(NonZeroUsize::get)
        .unwrap_or(1)
        .min(THREAD_MASSIMI);
    let utili = (coppie * 2).div_ceil(RIGHE_MINIME_PER_THREAD).max(1);
    disponibili.min(utili).max(1)
}

#[cfg(test)]
mod prove {
    use super::*;

    /// Costruisce una sorgente BGRA con uno stride più largo dei pixel utili,
    /// come quelle che manda davvero il compositore.
    fn sorgente(larghezza: usize, altezza: usize, stride: usize) -> Vec<u8> {
        let mut v = vec![0u8; altezza * stride];
        for y in 0..altezza {
            for x in 0..larghezza {
                let o = y * stride + x * 4;
                v[o] = (x % 256) as u8; // B
                v[o + 1] = (y % 256) as u8; // G
                v[o + 2] = ((x + y) % 256) as u8; // R
                v[o + 3] = 255;
            }
        }
        v
    }

    #[test]
    fn i_grigi_restano_grigi() {
        // Su un grigio pieno le due componenti di croma devono restare al
        // centro: e' il controllo che smaschera i coefficienti scambiati.
        let (w, h) = (16, 16);
        let bgra = vec![128u8; w * h * 4];
        let mut piani = Piani::nuovi(w, h);
        bgra_in_yuv(&bgra, w * 4, w, h, &mut piani);

        assert!(piani.u.iter().all(|&c| (127..=129).contains(&c)), "croma U spostato");
        assert!(piani.v.iter().all(|&c| (127..=129).contains(&c)), "croma V spostato");
        // 128 grigio -> luma intorno a 126 con la scala ridotta di BT.601
        assert!(piani.y.iter().all(|&l| (120..=132).contains(&l)), "luma fuori scala");
    }

    #[test]
    fn il_bordo_replica_invece_di_annerire() {
        // Sorgente 6x6 dentro piani 16x64: tutto il bordo aggiunto deve
        // ripetere l'ultima riga e l'ultima colonna, non restare nero.
        let (w, h) = (6, 6);
        let bgra = sorgente(w, h, w * 4);
        let mut piani = Piani::nuovi(16, 64);
        bgra_in_yuv(&bgra, w * 4, w, h, &mut piani);

        // l'ultima riga utile e quella subito sotto devono coincidere
        let riga = |n: usize| piani.y[n * 16..n * 16 + 16].to_vec();
        assert_eq!(riga(5), riga(6), "la riga di bordo non replica l'ultima utile");
        assert_eq!(riga(5), riga(63), "il fondo non replica l'ultima riga utile");

        // nessun pixel del bordo deve essere il nero di partenza
        assert!(piani.y.iter().all(|&l| l >= 16), "bordo rimasto nero");
    }

    #[test]
    fn lo_stride_non_si_deduce() {
        // Stride piu' largo dei pixel utili: se lo si deducesse da larghezza*4
        // l'immagine uscirebbe obliqua. Le due conversioni devono coincidere.
        let (w, h) = (8, 8);
        let stretto = sorgente(w, h, w * 4);
        let largo = sorgente(w, h, w * 4 + 32);

        let mut a = Piani::nuovi(w, h);
        let mut b = Piani::nuovi(w, h);
        bgra_in_yuv(&stretto, w * 4, w, h, &mut a);
        bgra_in_yuv(&largo, w * 4 + 32, w, h, &mut b);

        assert_eq!(a.y, b.y);
        assert_eq!(a.u, b.u);
        assert_eq!(a.v, b.v);
    }

    #[test]
    fn spartire_in_bande_non_cambia_il_risultato() {
        // La parallelizzazione e' corretta solo se il risultato non dipende da
        // quanti thread la calcolano.
        let (w, h) = (64, 128);
        let bgra = sorgente(w, h, w * 4);

        let mut riferimento = Piani::nuovi(w, h);
        {
            // una banda sola: si converte tutto in sequenza
            let mezza = w / 2;
            banda(
                &bgra, w * 4, w, h, w, mezza, 0,
                &mut riferimento.y, &mut riferimento.u, &mut riferimento.v,
            );
        }

        let mut parallelo = Piani::nuovi(w, h);
        bgra_in_yuv(&bgra, w * 4, w, h, &mut parallelo);

        assert_eq!(riferimento.y, parallelo.y);
        assert_eq!(riferimento.u, parallelo.u);
        assert_eq!(riferimento.v, parallelo.v);
    }
}
