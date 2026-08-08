//! Immagine di prova generata dal server.
//!
//! Serve alla fase 1 del piano: dimostrare che un client RDP si collega, che la
//! negoziazione va a buon fine e che i fotogrammi arrivano a schermo. Non c'e'
//! ancora nessuna cattura del desktop.
//!
//! L'immagine e' costruita per essere DIAGNOSTICA, non decorativa:
//!
//!   - le barre di colore in alto rivelano subito un eventuale scambio fra i
//!     canali rosso e blu, che e' l'errore piu' comune quando si sbaglia il
//!     formato dei pixel;
//!   - la risoluzione stampata al centro dice quale dimensione il server ha
//!     davvero negoziato, che non sempre coincide con quella richiesta;
//!   - il contatore e il quadrato che avanza dimostrano che i fotogrammi
//!     continuano ad arrivare, distinguendo un flusso vivo da un'immagine
//!     rimasta congelata.

use core::num::{NonZeroU16, NonZeroUsize};

use bytes::Bytes;
use ironrdp_server::{BitmapUpdate, DesktopSize, PixelFormat};

/// Formato dei pixel usato internamente.
///
/// `BgrA32` dispone i byte in memoria nell'ordine B, G, R, A. E' lo stesso
/// ordine che produce PipeWire, quindi adottarlo fin da ora evita una
/// conversione quando arrivera' la cattura vera.
const FORMAT: PixelFormat = PixelFormat::BgrA32;
const BPP: usize = 4;

/// Colore a 8 bit per canale.
#[derive(Clone, Copy)]
struct Rgb(u8, u8, u8);

const SFONDO_ALTO: Rgb = Rgb(0x0b, 0x12, 0x20);
const SFONDO_BASSO: Rgb = Rgb(0x1b, 0x2a, 0x44);
const GRIGLIA: Rgb = Rgb(0x22, 0x30, 0x4a);
const BORDO: Rgb = Rgb(0x4a, 0x90, 0xd9);
const TESTO: Rgb = Rgb(0xff, 0xff, 0xff);
const TESTO_TENUE: Rgb = Rgb(0x9f, 0xb4, 0xd0);
const CURSORE: Rgb = Rgb(0xff, 0xd0, 0x30);

/// Barre di colore, con l'etichetta che ne dichiara il contenuto atteso.
/// Se una barra non corrisponde alla propria etichetta, i canali sono scambiati.
const BARRE: [(Rgb, &str); 8] = [
    (Rgb(0xff, 0xff, 0xff), "W"),
    (Rgb(0xff, 0xff, 0x00), "Y"),
    (Rgb(0x00, 0xff, 0xff), "C"),
    (Rgb(0x00, 0xff, 0x00), "G"),
    (Rgb(0xff, 0x00, 0xff), "M"),
    (Rgb(0xff, 0x00, 0x00), "R"),
    (Rgb(0x00, 0x00, 0xff), "B"),
    (Rgb(0x20, 0x20, 0x20), "K"),
];

/// Tela su cui si disegna, poi convertita in aggiornamento per il client.
struct Tela {
    larghezza: usize,
    altezza: usize,
    dati: Vec<u8>,
}

impl Tela {
    fn nuova(larghezza: usize, altezza: usize) -> Self {
        Self {
            larghezza,
            altezza,
            dati: vec![0; larghezza * altezza * BPP],
        }
    }

    #[inline]
    fn punto(&mut self, x: usize, y: usize, c: Rgb) {
        if x >= self.larghezza || y >= self.altezza {
            return;
        }
        let i = (y * self.larghezza + x) * BPP;
        // ordine in memoria per BgrA32
        self.dati[i] = c.2;
        self.dati[i + 1] = c.1;
        self.dati[i + 2] = c.0;
        self.dati[i + 3] = 0xff;
    }

    fn rettangolo(&mut self, x: usize, y: usize, w: usize, h: usize, c: Rgb) {
        for yy in y..(y + h).min(self.altezza) {
            for xx in x..(x + w).min(self.larghezza) {
                self.punto(xx, yy, c);
            }
        }
    }

    /// Cornice di spessore `s`.
    fn cornice(&mut self, s: usize, c: Rgb) {
        let (w, h) = (self.larghezza, self.altezza);
        self.rettangolo(0, 0, w, s, c);
        self.rettangolo(0, h.saturating_sub(s), w, s, c);
        self.rettangolo(0, 0, s, h, c);
        self.rettangolo(w.saturating_sub(s), 0, s, h, c);
    }

    /// Scrive `testo` con il minuscolo carattere a matrice, ingrandito `scala` volte.
    /// Restituisce la larghezza occupata, utile per centrare.
    fn testo(&mut self, x: usize, y: usize, scala: usize, c: Rgb, testo: &str) -> usize {
        let mut penna = x;
        for ch in testo.chars() {
            let glifo = glifo(ch);
            for (riga, bits) in glifo.iter().enumerate() {
                for col in 0..LARGHEZZA_GLIFO {
                    // il bit piu' significativo e' la colonna di sinistra
                    if bits & (1 << (LARGHEZZA_GLIFO - 1 - col)) != 0 {
                        self.rettangolo(
                            penna + col * scala,
                            y + riga * scala,
                            scala,
                            scala,
                            c,
                        );
                    }
                }
            }
            penna += (LARGHEZZA_GLIFO + 1) * scala;
        }
        penna.saturating_sub(x + scala)
    }
}

/// Larghezza di `testo` senza disegnarlo, per poterlo centrare.
fn larghezza_testo(testo: &str, scala: usize) -> usize {
    let n = testo.chars().count();
    if n == 0 {
        0
    } else {
        n * (LARGHEZZA_GLIFO + 1) * scala - scala
    }
}

/// Disegna l'immagine di prova completa.
///
/// `fotogramma` fa avanzare gli elementi mobili, cosi' si distingue un flusso
/// vivo da un'immagine congelata.
pub fn disegna(size: DesktopSize, fotogramma: u64) -> Option<BitmapUpdate> {
    let w = usize::from(size.width);
    let h = usize::from(size.height);
    if w == 0 || h == 0 {
        return None;
    }

    let mut tela = Tela::nuova(w, h);

    // --- sfondo a sfumatura verticale ---------------------------------------
    for y in 0..h {
        let t = y as u32 * 255 / h.max(1) as u32;
        let misc = |a: u8, b: u8| -> u8 {
            (u32::from(a) + (u32::from(b) - u32::from(a).min(u32::from(b))) * t / 255)
                .min(255) as u8
        };
        let c = Rgb(
            misc(SFONDO_ALTO.0, SFONDO_BASSO.0),
            misc(SFONDO_ALTO.1, SFONDO_BASSO.1),
            misc(SFONDO_ALTO.2, SFONDO_BASSO.2),
        );
        tela.rettangolo(0, y, w, 1, c);
    }

    // --- griglia di riferimento ogni 100 pixel -------------------------------
    let passo = 100;
    let mut x = passo;
    while x < w {
        tela.rettangolo(x, 0, 1, h, GRIGLIA);
        x += passo;
    }
    let mut y = passo;
    while y < h {
        tela.rettangolo(0, y, w, 1, GRIGLIA);
        y += passo;
    }

    // --- barre di colore in alto --------------------------------------------
    let alt_barre = (h / 10).clamp(40, 160);
    let larg_barra = w / BARRE.len();
    let scala_etichetta = (alt_barre / 24).max(2);
    for (i, (colore, etichetta)) in BARRE.iter().enumerate() {
        let bx = i * larg_barra;
        let bw = if i == BARRE.len() - 1 { w - bx } else { larg_barra };
        tela.rettangolo(bx, 0, bw, alt_barre, *colore);
        // etichetta in nero o bianco secondo la luminosita' della barra
        let luminosita = u32::from(colore.0) * 30 + u32::from(colore.1) * 59 + u32::from(colore.2) * 11;
        let c_etichetta = if luminosita > 12_000 {
            Rgb(0, 0, 0)
        } else {
            Rgb(0xff, 0xff, 0xff)
        };
        let lt = larghezza_testo(etichetta, scala_etichetta);
        tela.testo(
            bx + bw / 2 - lt / 2,
            alt_barre - ALTEZZA_GLIFO * scala_etichetta - scala_etichetta * 2,
            scala_etichetta,
            c_etichetta,
            etichetta,
        );
    }

    // --- blocco centrale ----------------------------------------------------
    let centro_y = h / 2;

    let scala_titolo = (w / 240).max(3);
    let titolo = "REMOTIX";
    let lt = larghezza_testo(titolo, scala_titolo);
    tela.testo(
        w / 2 - lt / 2,
        centro_y - ALTEZZA_GLIFO * scala_titolo,
        scala_titolo,
        TESTO,
        titolo,
    );

    let scala_ris = (w / 520).max(2);
    let risoluzione = format!("{}X{}", size.width, size.height);
    let lt = larghezza_testo(&risoluzione, scala_ris);
    tela.testo(
        w / 2 - lt / 2,
        centro_y + ALTEZZA_GLIFO * scala_titolo / 2,
        scala_ris,
        TESTO_TENUE,
        &risoluzione,
    );

    let scala_cont = (w / 700).max(2);
    let contatore = format!("FOTOGRAMMA {fotogramma}");
    let lt = larghezza_testo(&contatore, scala_cont);
    tela.testo(
        w / 2 - lt / 2,
        centro_y + ALTEZZA_GLIFO * scala_titolo / 2 + ALTEZZA_GLIFO * scala_ris * 2,
        scala_cont,
        TESTO_TENUE,
        &contatore,
    );

    // --- quadrato mobile: prova che i fotogrammi continuano ad arrivare ------
    let lato = (h / 20).clamp(20, 60);
    let corsa = w.saturating_sub(lato * 2).max(1);
    let pos = (fotogramma as usize * lato) % corsa;
    tela.rettangolo(lato / 2 + pos, h - lato * 2, lato, lato, CURSORE);

    // --- cornice ------------------------------------------------------------
    tela.cornice((h / 300).max(2), BORDO);

    let width = NonZeroU16::new(size.width)?;
    let height = NonZeroU16::new(size.height)?;
    let stride = NonZeroUsize::new(w * BPP)?;

    Some(BitmapUpdate {
        x: 0,
        y: 0,
        width,
        height,
        format: FORMAT,
        data: Bytes::from(tela.dati),
        stride,
    })
}

// ---------------------------------------------------------------------------
// Carattere a matrice 5x7
//
// Minimo indispensabile per scrivere sull'immagine di prova senza trascinarsi
// dietro una libreria di font. Ogni glifo e' alto 7 righe; di ogni riga si
// usano i 5 bit meno significativi, con il bit piu' alto a sinistra.
// ---------------------------------------------------------------------------

const LARGHEZZA_GLIFO: usize = 5;
const ALTEZZA_GLIFO: usize = 7;

#[rustfmt::skip]
fn glifo(ch: char) -> [u8; ALTEZZA_GLIFO] {
    match ch.to_ascii_uppercase() {
        '0' => [0b01110,0b10001,0b10011,0b10101,0b11001,0b10001,0b01110],
        '1' => [0b00100,0b01100,0b00100,0b00100,0b00100,0b00100,0b01110],
        '2' => [0b01110,0b10001,0b00001,0b00010,0b00100,0b01000,0b11111],
        '3' => [0b11111,0b00010,0b00100,0b00010,0b00001,0b10001,0b01110],
        '4' => [0b00010,0b00110,0b01010,0b10010,0b11111,0b00010,0b00010],
        '5' => [0b11111,0b10000,0b11110,0b00001,0b00001,0b10001,0b01110],
        '6' => [0b00110,0b01000,0b10000,0b11110,0b10001,0b10001,0b01110],
        '7' => [0b11111,0b00001,0b00010,0b00100,0b01000,0b01000,0b01000],
        '8' => [0b01110,0b10001,0b10001,0b01110,0b10001,0b10001,0b01110],
        '9' => [0b01110,0b10001,0b10001,0b01111,0b00001,0b00010,0b01100],
        'A' => [0b01110,0b10001,0b10001,0b11111,0b10001,0b10001,0b10001],
        'B' => [0b11110,0b10001,0b10001,0b11110,0b10001,0b10001,0b11110],
        'C' => [0b01110,0b10001,0b10000,0b10000,0b10000,0b10001,0b01110],
        'D' => [0b11100,0b10010,0b10001,0b10001,0b10001,0b10010,0b11100],
        'E' => [0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b11111],
        'F' => [0b11111,0b10000,0b10000,0b11110,0b10000,0b10000,0b10000],
        'G' => [0b01110,0b10001,0b10000,0b10111,0b10001,0b10001,0b01111],
        'H' => [0b10001,0b10001,0b10001,0b11111,0b10001,0b10001,0b10001],
        'I' => [0b01110,0b00100,0b00100,0b00100,0b00100,0b00100,0b01110],
        'J' => [0b00111,0b00010,0b00010,0b00010,0b00010,0b10010,0b01100],
        'K' => [0b10001,0b10010,0b10100,0b11000,0b10100,0b10010,0b10001],
        'L' => [0b10000,0b10000,0b10000,0b10000,0b10000,0b10000,0b11111],
        'M' => [0b10001,0b11011,0b10101,0b10101,0b10001,0b10001,0b10001],
        'N' => [0b10001,0b11001,0b10101,0b10011,0b10001,0b10001,0b10001],
        'O' => [0b01110,0b10001,0b10001,0b10001,0b10001,0b10001,0b01110],
        'P' => [0b11110,0b10001,0b10001,0b11110,0b10000,0b10000,0b10000],
        'Q' => [0b01110,0b10001,0b10001,0b10001,0b10101,0b10010,0b01101],
        'R' => [0b11110,0b10001,0b10001,0b11110,0b10100,0b10010,0b10001],
        'S' => [0b01111,0b10000,0b10000,0b01110,0b00001,0b00001,0b11110],
        'T' => [0b11111,0b00100,0b00100,0b00100,0b00100,0b00100,0b00100],
        'U' => [0b10001,0b10001,0b10001,0b10001,0b10001,0b10001,0b01110],
        'V' => [0b10001,0b10001,0b10001,0b10001,0b10001,0b01010,0b00100],
        'W' => [0b10001,0b10001,0b10001,0b10101,0b10101,0b11011,0b10001],
        'X' => [0b10001,0b10001,0b01010,0b00100,0b01010,0b10001,0b10001],
        'Y' => [0b10001,0b10001,0b01010,0b00100,0b00100,0b00100,0b00100],
        'Z' => [0b11111,0b00001,0b00010,0b00100,0b01000,0b10000,0b11111],
        '.' => [0b00000,0b00000,0b00000,0b00000,0b00000,0b01100,0b01100],
        ':' => [0b00000,0b01100,0b01100,0b00000,0b01100,0b01100,0b00000],
        '-' => [0b00000,0b00000,0b00000,0b11111,0b00000,0b00000,0b00000],
        _   => [0b00000,0b00000,0b00000,0b00000,0b00000,0b00000,0b00000],
    }
}
