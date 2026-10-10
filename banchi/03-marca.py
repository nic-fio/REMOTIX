#!/usr/bin/env python3
"""03-marca.py — THE MARK READER of the phase 3 scene.

    python3 03-marca.py leggi  fotogramma.rgb24 --larghezza 1280 --altezza 720
    python3 03-marca.py leggi  fotogramma.png
    python3 03-marca.py dipingi fuori.png --disegno 41 --istante-us 123456 --giro g1
    python3 03-marca.py conta  --shm remotix-scena

===========================================================================
⛔ WHAT IT MUST BE ABLE TO SAY, AND THE HALF THAT GETS FORGOTTEN

The mandate: *«the mark reader: the function that, given a decoded
frame, returns the drawing number and the instant — and ⛔ that can
also say "the mark is not there".  A detector that always says yes measures zero
and is wrongly happy»* (`STUDI.md` §web §6.3, check **P3**).

⇒ `leggi_marca()` has TWO outputs, not one:

    {"c_e": True,  "disegno": 41, "istante_us": 987654321, "giro": 0x…, …}
    {"c_e": False, "perche": "the CRC does not match …", "contrasto": 0.31, …}

⛔ And `c_e: False` ALWAYS carries the why, because «the mark is not there», «the
   frame is smaller than the block» and «the contrast is too low»
   are three different diagnoses that send you looking in three different places.
   `LEZIONI.md` §1.9: a denied read is not a read that says zero.

===========================================================================
⛔ THE THREE SIEVES, AND WHAT THEY ARE WORTH

So that any noise does not pass for a mark, there are three filters in
a row.  The numbers are not guesswork:

  1. **contrast**  the difference between the 90th and 10th percentile of the 144
     cells must be ≥ 0.25 (on 0..1).  ⚠ On its own it is not enough and is not meant
     to be: half a desktop has more contrast than that.  It serves to say
     «there is no binary signal here» instead of picking a threshold at random between
     two nearly equal values;
  2. **sync**  the 8 leading bits must be exactly 0xB2.  A block
     of noise hits it 1 time in 256;
  3. **CRC-16**  over the 15 body bytes.  It hits it 1 time in 65,536.

  ⇒ false positive per position tried ≈ 1 / 16,700,000.  ⛔ And the number
    of positions tried is NOT one: the search tries (2·R+1)² offsets
    (25 by default), so the true count is ≈ 1 / 670,000.  It is written here
    because the negative control of the certification PUTS IT TO THE TEST on
    thousands of noise frames, instead of trusting this calculation.

===========================================================================
⛔ WHY THE READING SURVIVES LOSSY ENCODING

The mandate asks for it and forbids taking it for granted.  The defences, each
against a specific defect of the encoding:

  · **the CENTRE of the cell is read**, not the whole cell: the central
    square at 50 % of the side (12 px out of 24).  HEVC *ringing* lives on the
    block edges, and the edges are not looked at here;
  · **the LUMINANCE is read**, and the two levels are full white and full
    black: 255 levels of swing.  4:2:0 touches the chrominance, and the
    mark does not live in the chrominance;
  · **the threshold is RELATIVE** — the midpoint between the 10th and 90th percentile
    of the cells of THIS frame — instead of 128.  This way it survives a
    gain or an offset (limited range read as full, for example) that
    would move a fixed threshold;
  · **it shifts by ±R pixels** looking for the position that passes the three sieves:
    a canvas that moves the image by one pixel does not make the mark disappear.

⛔ And «survives» is not an opinion: `03-scena-certifica.sh` encodes the mark
   with x265 Main10 at increasing QP and says **up to which QP** it reads back.  If one
   day the encoder changes, that number changes and it shows.
"""
import argparse
import hashlib
import json
import mmap
import os
import struct
import sys
import time

# ⛔⭐ NUMPY IS LOADED WHEN NEEDED, NOT AT IMPORT — 13 Aug 2026.
#
# The coordinator reports that on NIC-OS **numpy is not there**.  With
# `import numpy` at the top, `03-marca.py conta` — which does not use numpy at all,
# because it reads a shared memory block with `struct` — died on
# NIC-OS with an ImportError that talks about a library, not about the problem.
#
# ⇒ the plug is INSIDE this file and not outside: `conta` works everywhere, and
#   whoever asks for `leggi` or `dipingi` without numpy gets a sentence that says **what
#   to do**, not the name of a missing module.
# ⚠ And `nome` and `conta` stay usable from NIC-OS, which is where the benches run.
_np = None


def np_o_muori(che):
    """numpy, or a sentence that says where the reading is done."""
    global _np
    if _np is None:
        try:
            import numpy
        except ImportError:
            raise SystemExit(
                "⛔ «%s» needs numpy, and this machine does not have it.\n"
                "   ⚠ It is not a defect of the mark: the PIXEL READING "
                "is done where numpy is (on CHUWI).\n"
                "   ⭐ What works HERE without numpy: «03-marca.py conta» (the "
                "client's drawings, read from the shared block) and «03-marca.py "
                "nome» (the 32-bit number of a round).\n"
                "   ⇒ either copy the frame to where numpy is, or install "
                "python3-numpy." % che)
        _np = numpy
    return _np

# ───────────────────────────────────────────────────────────────────────────
# THE GEOMETRY — ⛔ must match `03-scena.c`.  Whoever changes a number
# here and not there breaks the reading, and the certification (check P6)
# notices instead of leaving it to be discovered by a wrong measurement.
# ───────────────────────────────────────────────────────────────────────────
SYNC      = 0xB2
VERSIONE  = 0x01
COLONNE   = 18
RIGHE     = 8
BIT       = COLONNE * RIGHE          # 144
CELLA     = 24
MARGINE   = 32
QUIETE    = 12

CONTRASTO_MINIMO = 0.25              # see §«the three sieves»
RICERCA          = 2                 # ± px

# BT.709, which is the matrix F2.3 chooses and that the rest of the chain
# declares.  ⚠ Here it only serves to make ONE number out of three channels: white and black
# give the same result with any sensible matrix.
PESI_LUMA = (0.2126, 0.7152, 0.0722)


class MarcaGeometria:
    def __init__(self, cella=CELLA, margine=MARGINE, quiete=QUIETE,
                 colonne=COLONNE, righe=RIGHE):
        self.cella, self.margine, self.quiete = int(cella), int(margine), int(quiete)
        self.colonne, self.righe = int(colonne), int(righe)
        self.bit = self.colonne * self.righe

    def blocco(self):
        return (self.margine, self.margine,
                self.colonne * self.cella, self.righe * self.cella)

    def __repr__(self):
        return ("MarcaGeometria(cella=%d, margine=%d, quiete=%d, %dx%d)"
                % (self.cella, self.margine, self.quiete, self.colonne, self.righe))


GEOMETRIA = MarcaGeometria()


# ───────────────────────────────────────────────────────────────────────────
def fnv1a32(s):
    """The same short name that `03-scena.c` puts in the mark."""
    h = 2166136261
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def crc16(dati):
    """CRC-16/CCITT-FALSE — poly 0x1021, init 0xFFFF, no reflection."""
    c = 0xFFFF
    for b in dati:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def componi_carico(disegno, istante_us, giro_numero):
    """The 18 bytes of the mark, in the order in which they end up in the cells."""
    corpo = struct.pack(">BII", VERSIONE, giro_numero & 0xFFFFFFFF,
                        disegno & 0xFFFFFFFF)
    t = istante_us & 0xFFFFFFFFFFFF                     # 48 bit
    corpo += bytes(((t >> 40) & 0xFF, (t >> 32) & 0xFF, (t >> 24) & 0xFF,
                    (t >> 16) & 0xFF, (t >> 8) & 0xFF, t & 0xFF))
    assert len(corpo) == 15
    return bytes([SYNC]) + corpo + struct.pack(">H", crc16(corpo))


def carico_in_bit(tutto, quanti):
    np = np_o_muori("carico_in_bit")
    b = np.zeros(quanti, dtype=np.uint8)
    for i in range(quanti):
        b[i] = (tutto[i >> 3] >> (7 - (i & 7))) & 1
    return b


# ───────────────────────────────────────────────────────────────────────────
# THE PAINTER.  ⛔ It serves the POSITIVE CONTROL and nothing else: the real scene is
# painted by `03-scena.c`.  That the two paint the same thing is not assumed —
# `03-scena-certifica.sh` (P6) reads with this reader a frame painted
# by the C and compares with what the C declared.
# ───────────────────────────────────────────────────────────────────────────
def dipingi_marca(img, disegno, istante_us, giro_numero, geo=GEOMETRIA):
    """Paints the mark INTO `img` (uint8 [h,w,3]).  Returns `img`."""
    np_o_muori("dipingi_marca")
    tutto = componi_carico(disegno, istante_us, giro_numero)
    bit = carico_in_bit(tutto, geo.bit)
    x0, y0, w, h = geo.blocco()
    H, W = img.shape[:2]
    if y0 + h + geo.quiete > H or x0 + w + geo.quiete > W:
        raise ValueError("⛔ the mark does not fit: it needs at least %dx%d, the image "
                         "is %dx%d" % (x0 + w + geo.quiete, y0 + h + geo.quiete, W, H))
    img[max(0, y0 - geo.quiete):y0 + h + geo.quiete,
        max(0, x0 - geo.quiete):x0 + w + geo.quiete] = 0
    for i in range(geo.bit):
        if not bit[i]:
            continue
        r, c = divmod(i, geo.colonne)
        img[y0 + r * geo.cella:y0 + (r + 1) * geo.cella,
            x0 + c * geo.cella:x0 + (c + 1) * geo.cella] = 255
    return img


# ───────────────────────────────────────────────────────────────────────────
# ⭐⛔ THE READER
# ───────────────────────────────────────────────────────────────────────────
def _luma(img):
    np = np_o_muori("leggi_marca")
    a = np.asarray(img)
    pesi = np.array(PESI_LUMA, dtype=np.float64)
    if a.ndim == 2:
        return a.astype(np.float64) / 255.0
    if a.ndim == 3 and a.shape[2] >= 3:
        return (a[:, :, :3].astype(np.float64) @ pesi) / 255.0
    raise ValueError("the image is neither grey nor three-channel: %s" % (a.shape,))


def _celle(y, geo, dx, dy):
    """The mean luminance of the CENTRE of each cell, in bit order."""
    x0, y0, _, _ = geo.blocco()
    x0 += dx
    y0 += dy
    np = np_o_muori("leggi_marca")
    c = geo.cella
    dentro = max(2, c // 4)              # the central square at 50 % is read
    val = np.empty(geo.bit, dtype=np.float64)
    for i in range(geo.bit):
        r, k = divmod(i, geo.colonne)
        ya = y0 + r * c + dentro
        xa = x0 + k * c + dentro
        val[i] = y[ya:ya + c - 2 * dentro, xa:xa + c - 2 * dentro].mean()
    return val


def _prova_posizione(y, geo, dx, dy):
    np = np_o_muori("leggi_marca")
    val = _celle(y, geo, dx, dy)
    alto = float(np.percentile(val, 90))
    basso = float(np.percentile(val, 10))
    contrasto = alto - basso
    esito = {"contrasto": round(contrasto, 4), "scorrimento_provato": [dx, dy]}
    if contrasto < CONTRASTO_MINIMO:
        esito["perche"] = ("the contrast between the cells is %.3f, below the minimum "
                           "%.2f: there is no two-level signal here"
                           % (contrasto, CONTRASTO_MINIMO))
        return None, esito
    soglia = (alto + basso) / 2.0
    bit = (val > soglia).astype(np.uint8)

    byte = bytearray(len(bit) // 8)
    for i, b in enumerate(bit):
        if b:
            byte[i >> 3] |= 1 << (7 - (i & 7))
    byte = bytes(byte)

    if byte[0] != SYNC:
        esito["perche"] = ("the first 8 bits are 0x%02X instead of the sync 0x%02X"
                           % (byte[0], SYNC))
        return None, esito
    corpo, crc_letto = byte[1:16], struct.unpack(">H", byte[16:18])[0]
    crc_atteso = crc16(corpo)
    if crc_letto != crc_atteso:
        esito["perche"] = ("the sync is there but the CRC does not match: read 0x%04X, "
                           "computed 0x%04X ⇒ the mark was there and broke, "
                           "or it is chance" % (crc_letto, crc_atteso))
        return None, esito

    versione = corpo[0]
    giro = struct.unpack(">I", corpo[1:5])[0]
    disegno = struct.unpack(">I", corpo[5:9])[0]
    istante = int.from_bytes(corpo[9:15], "big")
    if versione != VERSIONE:
        # ⛔ A CRC that matches with a version we do not know is NOT
        #    «mark absent»: it is a mark from another draft, and reading it with
        #    our layout would give wrong numbers that look right.
        esito["perche"] = ("mark of version %d, this reader reads version %d: "
                           "the fields are not in the same place and reading it "
                           "would give plausible and false numbers" % (versione, VERSIONE))
        esito["versione_marca"] = versione
        return None, esito

    buono = {"c_e": True, "versione": versione, "giro": giro,
             "disegno": disegno, "istante_us": istante,
             "contrasto": round(contrasto, 4), "soglia": round(soglia, 4),
             "scorrimento_provato": [dx, dy]}
    return buono, esito


def leggi_marca(img, geo=GEOMETRIA, ricerca=RICERCA):
    """⭐ Given a frame, says whether the mark is there and what it says.

    Returns a dictionary that ALWAYS has the key `c_e`:
      c_e = True   → `disegno`, `istante_us`, `giro`, `contrasto`,
                     `scorrimento_provato`
      c_e = False  → `perche` (⛔ never absent), plus whatever could be seen
    """
    y = _luma(img)
    H, W = y.shape
    x0, y0, w, h = geo.blocco()
    serve_w, serve_h = x0 + w + ricerca, y0 + h + ricerca
    if W < serve_w or H < serve_h:
        return {"c_e": False,
                "perche": ("⛔ I could not LOOK: the frame is %dx%d and the "
                           "mark block ends at %dx%d.  ⚠ It is not «the mark "
                           "is not there»: it is «the mark would not fit»"
                           % (W, H, serve_w, serve_h)),
                "misura": [W, H], "serve": [serve_w, serve_h]}

    # ⛔ THE ORDER OF THE POSITIONS IS NOT IRRELEVANT, and the first draft
    #    got it wrong — found by running, 13 Aug 2026.  Scanning from
    #    (−2,−2) upwards, a PERFECTLY aligned frame was read correctly
    #    but declared `scorrimento: [-2,-2]`: the cell is 24 px wide and is
    #    read at the centre, so two pixels of offset pass anyway.  The
    #    payload came out right and the number beside it was false — and it is the kind of
    #    number that ends up in a document as a measurement.
    # ⇒ (0,0) is tried first and then at increasing radius: whoever declares an
    #   offset really has it.
    ordine = sorted(
        ((dx, dy) for dy in range(-ricerca, ricerca + 1)
                  for dx in range(-ricerca, ricerca + 1)),
        key=lambda p: (max(abs(p[0]), abs(p[1])), abs(p[0]) + abs(p[1]), p))
    migliore = None
    for dx, dy in ordine:
        if y0 + dy < 0 or x0 + dx < 0:
            continue
        buono, esito = _prova_posizione(y, geo, dx, dy)
        if buono is not None:
            buono["posizioni_provate"] = (2 * ricerca + 1) ** 2
            return buono
        if migliore is None or esito["contrasto"] > migliore["contrasto"]:
            migliore = esito
    fuori = {"c_e": False, "posizioni_provate": (2 * ricerca + 1) ** 2}
    fuori.update(migliore or {"perche": "no position tried"})
    fuori["perche"] = ("the mark is NOT there in any of the %d offsets tried "
                       "(± %d px).  The best one said: %s"
                       % (fuori["posizioni_provate"], ricerca, fuori.get("perche")))
    return fuori


# ───────────────────────────────────────────────────────────────────────────
# THE COUNT OF THE CLIENT'S DRAWINGS — read from outside, from the shared block.
#
# ⛔ §1.1: «alongside, count how much the client draws: it is the check that
#    says whether the ceiling belongs to the compositor or to the scene».
# ───────────────────────────────────────────────────────────────────────────
STATO_MAGIA = 0x524D5853
STATO_VERSIONE = 2
# ⛔ Must match `struct stato_condiviso` of `03-scena.c`.  `magia` and
#    `versione` exist so that a misalignment gives a REFUSAL instead of
#    random numbers.
FORMATO_STATO = "<4I Q 5Q 5Q 10I i 3I 64s 32s 64s 64s 4Q 4I"


def leggi_conteggio(nome_shm="remotix-scena"):
    """Returns the client's counts, or `{"c_e": False, "perche": …}`."""
    percorso = "/dev/shm/" + nome_shm
    if not os.path.exists(percorso):
        return {"c_e": False,
                "perche": ("⛔ «%s» does not exist: the scene never started, "
                           "or it has another name (--shm).  ⚠ It is not «it "
                           "drew zero times»" % percorso)}
    taglia = struct.calcsize(FORMATO_STATO)
    with open(percorso, "rb") as f:
        with mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ) as m:
            if len(m) < taglia:
                return {"c_e": False,
                        "perche": "«%s» is %d bytes, %d are needed: the structure "
                                  "is not that one" % (percorso, len(m), taglia)}
            # ⛔ Seqlock: read twice and demand `seq` even and equal.
            #    Without it, one can take a new `disegno` with an old
            #    `istante` and believe in a delay that never existed.
            # ⛔⭐ THE SEQLOCK, AND THE DEFECT THAT WAS INSIDE IT — 13 Aug 2026.
            #
            # The first draft tried 50 times **in a row, without a breath**.  With
            # a healthy scene (60 drawings/s = 120 touches of `seq` per second) it
            # never failed.  With a scene in a BUSY LOOP (measured: 1034
            # drawings/s, plus as many presentation callbacks ⇒ over
            # 4000 touches per second) 50 tight attempts lose the race,
            # and the reader answered *«the block never stood still»*.
            #
            # ⭐ AND IT IS THE WRONG DIAGNOSIS: the block is not broken, it is the
            #   WRITER that is spinning in a busy loop.  Whoever read that sentence
            #   went looking for a defect in the shared memory — which is
            #   exactly where the defect was NOT.
            #
            # ⇒ two cures, and the second is worth more than the first:
            #   1. retry for longer and with a pause, so the window
            #      between two writes is found;
            #   2. ⛔ if even so it is not found, NAME the right suspect
            #      instead of blaming the block.
            # ⛔⭐⭐ THE SEQLOCK, AND THE DIAGNOSIS I GOT WRONG TWICE
            #      BEFORE MEASURING IT — 13 Aug 2026.
            #
            # The symptom reported by step 1 was *«the shared block stops
            # answering»*.  The coordinator suspected seqlock contention;
            # I suspected the same and widened the attempts.  ⛔ **Both
            # wrong, and measured**: with the old reader (50 tight attempts,
            # no pause) pointed at a scene in a busy loop —
            # 1034 drawings/s, over 4000 touches of `seq` per second — the successful
            # reads were **200 out of 200**.  Contention has nothing to do with it.
            #
            # ⭐ THE REAL CAUSE, and it reproduces every time instead of at random:
            #   a block left by a scene that died **mid-write** has
            #   `seq` **ODD FOREVER**.  No number of attempts will ever
            #   find it even: the old reader failed **3 times out of 3**,
            #   not «now and then».
            #
            # ⭐⭐ AND THE TWO THINGS ARE THE SAME DEFECT, by a path that
            #   neither of us had seen: a scene in a busy loop **never
            #   returns to the main loop**, so it ignores `--secondi`
            #   (measured: 6 s asked, 146 s lived) ⇒ the bench **kills** it
            #   ⇒ the death falls mid-write ⇒ `seq` stays odd.
            #   **One cause only, two symptoms, stitched together by the blow that stops it.**
            #
            # ⇒ hence the three outcomes this loop must be able to tell apart,
            #   which send you looking in three different places:
            #     · `seq` even and stable           → it is read
            #     · `seq` NEVER changed and is odd → the writer is
            #       dead or stopped with the write open.  ⛔ It is NOT «too
            #       fast»: it is a wreck
            #     · `seq` changes continuously but is never caught even →
            #       that really would be contention (never observed)
            campioni = 0
            primo_seq = struct.unpack(FORMATO_STATO, m[:taglia])[4]
            ultimo_seq = primo_seq
            coerente = None
            for _ in range(400):
                a = struct.unpack(FORMATO_STATO, m[:taglia])
                campioni += 1
                ultimo_seq = a[4]
                if a[4] % 2 == 0:
                    b = struct.unpack(FORMATO_STATO, m[:taglia])
                    if b[4] == a[4]:
                        coerente = a
                        break
                time.sleep(0.0002)
            if coerente is None:
                fermo = (ultimo_seq == primo_seq)
                pid_relitto = struct.unpack(FORMATO_STATO, m[:taglia])[25]
                vivo_relitto = os.path.exists("/proc/%d" % pid_relitto)
                if fermo:
                    perche = (
                        "⛔ «%s» is a WRECK: `seq` is %d — odd — and has NOT "
                        "changed in %d attempts.  A write was left "
                        "open, i.e. the scene died (or is stuck) halfway.  "
                        "⚠ Process %d %s.  ⛔ No number of attempts will ever "
                        "find it even: do not wait, restart the scene "
                        "(the block is reset at startup)."
                        % (percorso, ultimo_seq, campioni, pid_relitto,
                           "is still alive — so it is STUCK, not dead"
                           if vivo_relitto else "no longer exists"))
                else:
                    perche = (
                        "⛔ `seq` changes (%d → %d in %d attempts) and I never "
                        "caught it even: this really is contention.  ⚠ It was never "
                        "observed, not even with a scene at 1034 "
                        "drawings/s — if you see it, report it."
                        % (primo_seq, ultimo_seq, campioni))
                return {"c_e": False, "fidato": False, "campioni": campioni,
                        "seq": int(ultimo_seq), "relitto": bool(fermo),
                        "perche": perche}
            a = coerente
    (magia, versione, dim, _r0, seq,
     disegni, commit, presentati, attese, scarti,
     avvio_mono, avvio_reale, ultimo_disegno, ultimo_pres, ultimo_pres_reale,
     giro_numero, larghezza, altezza, cella, colonne, righe, margine, quiete,
     movimento, danno, pid, pres_disp, schermo_intero, _r1,
     nome_giro, versione_scena, uscita_confermata, uscita_chiesta,
     rientri, corse_a_vuoto, disegni_senza_callback, saltati_senza_buffer,
     callback_in_volo, callback_in_volo_massimo, refresh_mhz, fidato) = a

    if magia != STATO_MAGIA:
        return {"c_e": False,
                "perche": "«%s» is not a 03-scena block (magic 0x%08X)"
                          % (percorso, magia)}
    if versione != STATO_VERSIONE:
        return {"c_e": False,
                "perche": ("⛔ block of version %d, this reader reads version %d: "
                           "the fields are not in the same place"
                           % (versione, STATO_VERSIONE))}
    vivo = os.path.exists("/proc/%d" % pid)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⭐ THE VERDICT ON THE NUMBER, NOT ONLY THE NUMBER.
    #
    # Asked by the coordinator on 13 Aug 2026: *«a count of 540/s on a
    # 60 Hz monitor is an observable fact: it must be FLAGGED, not handed over.
    # Until that detector exists, every cell measured with your scene by
    # someone else's bench is `[?]`, not `[M]`.»*
    #
    # ⇒ `leggi_conteggio()` no longer returns only counts: it returns
    #   `fidato` and, when it is false, **the list of reasons**.  A bench that
    #   reads these numbers and does not look at `fidato` is deliberately doing what
    #   §2.2 forbids.
    #
    # ⚠ And the reasons are of TWO kinds, kept separate:
    #     · those the scene measured on itself (re-entries, callbacks in
    #       flight) — they are causes, and hold at any frequency;
    #     · those the reader computes from outside (rate against refresh, stale
    #       block, dead writer) — they are symptoms, and serve to catch the
    #       cases where the scene could not notice by itself (for example
    #       a scene killed halfway).
    # ═══════════════════════════════════════════════════════════════════════
    perche = []
    if rientri:
        perche.append("⛔ %d RE-ENTRIES: `disegna()` was called inside "
                      "itself — an event handler drew" % rientri)
    if callback_in_volo_massimo > 1:
        perche.append("⛔ up to %d `wl_surface.frame` IN FLIGHT together (1 is "
                      "allowed): the scene draws without being invited, and "
                      "the rate is multiplied by that number"
                      % callback_in_volo_massimo)
    if corse_a_vuoto:
        perche.append("⛔ %d BUSY-LOOP rounds" % corse_a_vuoto)

    # the mean rate since startup, against the refresh declared by the output
    ritmo = None
    durata = (ultimo_disegno - avvio_mono) / 1e6 if ultimo_disegno > avvio_mono else 0
    if durata > 0.5:
        ritmo = disegni / durata
        if refresh_mhz > 0 and ritmo > 1.5 * (refresh_mhz / 1000.0):
            perche.append("⛔ %.0f drawings/s on a %.1f Hz monitor: more than "
                          "one and a half times the refresh is not a rate, it is "
                          "a busy loop"
                          % (ritmo, refresh_mhz / 1000.0))
    if not vivo:
        # ⚠ It is NOT «the numbers are wrong»: they are the LAST snapshot of a
        #   scene that is no longer there.  Handing them over as current would be
        #   yesterday's measurement passed off as today's.
        perche.append("⚠ process %d that wrote this block is NO "
                      "longer alive: these are its last numbers, not the "
                      "numbers of now" % pid)

    return {
        "c_e": True, "vivo": vivo, "pid": int(pid), "seq": int(seq),
        # ⭐ the verdict, and it comes BEFORE the numbers because it governs them
        "fidato": (not perche),
        "perche_non_fidato": perche,
        "rientri": int(rientri), "corse_a_vuoto": int(corse_a_vuoto),
        "disegni_senza_callback": int(disegni_senza_callback),
        "saltati_senza_buffer": int(saltati_senza_buffer),
        "callback_in_volo": int(callback_in_volo),
        "callback_in_volo_massimo": int(callback_in_volo_massimo),
        "refresh_hz": (refresh_mhz / 1000.0) if refresh_mhz else None,
        "disegni_al_secondo": round(ritmo, 2) if ritmo is not None else None,
        "disegni": int(disegni), "commit": int(commit),
        "presentati": int(presentati), "attese": int(attese),
        "scarti_presentazione": int(scarti),
        # ⛔ The field that tells «zero presented» from «presented not
        #    measurable on this compositor» (`LEZIONI.md` §1.9).
        "presentazione_disponibile": bool(pres_disp),
        "avvio_monotonico_us": int(avvio_mono), "avvio_reale_us": int(avvio_reale),
        "ultimo_disegno_us": int(ultimo_disegno),
        "ultimo_presentato_us": int(ultimo_pres),
        "ultimo_presentato_reale_us": int(ultimo_pres_reale),
        "giro": nome_giro.split(b"\0")[0].decode("utf-8", "replace"),
        "giro_numero": int(giro_numero),
        "larghezza": int(larghezza), "altezza": int(altezza),
        "cella": int(cella), "colonne": int(colonne), "righe": int(righe),
        "margine": int(margine), "quiete": int(quiete),
        "movimento": ["marca", "barra", "pieno"][int(movimento)] if movimento < 3 else int(movimento),
        "danno": ["preciso", "pieno"][int(danno)] if danno < 2 else int(danno),
        "schermo_intero": bool(schermo_intero),
        "versione_scena": versione_scena.split(b"\0")[0].decode("utf-8", "replace"),
        # ⛔ «chiesta» (requested) is our intention; «confermata» (confirmed) is what the
        #    COMPOSITOR said with `wl_surface.enter`.  Empty does NOT mean
        #    «on none»: it means «no enter has arrived yet», and the two
        #    cases send you looking in two different places (`LEZIONI.md` §1.9).
        "uscita_chiesta": uscita_chiesta.split(b"\0")[0].decode("utf-8", "replace") or None,
        "uscita_confermata": (uscita_confermata.split(b"\0")[0]
                              .decode("utf-8", "replace") or None),
    }


# ───────────────────────────────────────────────────────────────────────────
def carica(percorso, larghezza=None, altezza=None):
    """raw .rgb24 (needs the dimensions), .png / .ppm via Pillow."""
    est = os.path.splitext(percorso)[1].lower()
    if est in (".rgb24", ".rgb", ".raw"):
        if not larghezza or not altezza:
            raise SystemExit("⛔ «%s» is raw: without --larghezza and --altezza I do not "
                             "know its shape, and guessing it would mean "
                             "reading the mark in the wrong place" % percorso)
        dati = open(percorso, "rb").read()
        atteso = larghezza * altezza * 3
        if len(dati) < atteso:
            raise SystemExit("⛔ «%s»: %d bytes, %d were needed for %dx%d rgb24"
                             % (percorso, len(dati), atteso, larghezza, altezza))
        np = np_o_muori("carica")
        return np.frombuffer(dati[:atteso], np.uint8).reshape(altezza, larghezza, 3)
    np = np_o_muori("carica")
    from PIL import Image
    return np.asarray(Image.open(percorso).convert("RGB"))


def main():
    p = argparse.ArgumentParser(description="the scene's mark reader")
    s = p.add_subparsers(dest="che", required=True)

    q = s.add_parser("leggi", help="given a frame, says whether the mark is there")
    q.add_argument("file")
    q.add_argument("--larghezza", type=int)
    q.add_argument("--altezza", type=int)
    q.add_argument("--cella", type=int, default=CELLA)
    q.add_argument("--margine", type=int, default=MARGINE)
    q.add_argument("--quiete", type=int, default=QUIETE)
    q.add_argument("--ricerca", type=int, default=RICERCA)

    d = s.add_parser("dipingi", help="⚠ only for the positive control")
    d.add_argument("file")
    d.add_argument("--larghezza", type=int, default=1280)
    d.add_argument("--altezza", type=int, default=720)
    d.add_argument("--disegno", type=int, required=True)
    d.add_argument("--istante-us", type=int, required=True)
    d.add_argument("--giro", default="senza-nome")
    d.add_argument("--cella", type=int, default=CELLA)
    d.add_argument("--fondo", default="grigio", choices=("grigio", "nero", "rumore"))

    c = s.add_parser("conta", help="the client's drawings, read from outside")
    c.add_argument("--shm", default="remotix-scena")

    n = s.add_parser("nome", help="the 32-bit number of a round name")
    n.add_argument("giro")

    # ⭐⛔ THE REOPENING OF M8'S `giro` CHECK.
    #
    # `fasi/rapporti/F2-6-giudizio.md`, 13 Aug 2026: M8's `giro` check
    # is **NOT APPLICABLE by construction**, because *«it is the name of the round
    # OF THE BENCH, the product does not know it and the protocol has no field to
    # tell it»*.
    #
    # ⇒ With the mark the round name travels **inside the pixels**: the bench
    #   paints it into the scene, the product carries it without knowing, and the bench
    #   reads it back from the painted frame.  ⭐ It is better than the check
    #   M8 could not do, because it asks nothing of the accused: it
    #   READS IT OFF THEM.
    #
    # ⛔ And the inversion is a LIST, not a guess: the mark carries 32 bits
    #   of FNV-1a, which cannot be inverted.  The caller declares the rounds it
    #   ran; if the number read is none of those, the raw number is
    #   written — and M8 turns red, which is the right outcome.
    # ⛔ And if the mark is NOT there, `giro` comes out **null**: M8 declares the check
    #   NOT RUN.  Writing the current round into it would be the constant
    #   that made it pass, i.e. the false green of 13 August.
    idn = s.add_parser("identita",
                       help="⭐ builds M8's --identita-pagina by reading the "
                            "round FROM THE PIXELS")
    idn.add_argument("file")
    idn.add_argument("--larghezza", type=int)
    idn.add_argument("--altezza", type=int)
    idn.add_argument("--giri", required=True,
                     help="the names of the known rounds, comma-separated: it is "
                          "the list used to invert the mark's number")
    idn.add_argument("--fuori", required=True)
    idn.add_argument("--dipinto-dopo-reset", choices=("si", "no"),
                     help="⚠ if you do not declare it, M8 does NOT pretend to have looked")
    idn.add_argument("--fin-ricevuto", choices=("si", "no"))
    idn.add_argument("--dipinto", choices=("si", "no"))
    idn.add_argument("--conti", help="the JSON of the page's counts")

    a = p.parse_args()

    if a.che == "leggi":
        geo = MarcaGeometria(a.cella, a.margine, a.quiete)
        img = carica(a.file, a.larghezza, a.altezza)
        r = leggi_marca(img, geo, a.ricerca)
        r["file"] = a.file
        r["impronta"] = hashlib.sha256(open(a.file, "rb").read()).hexdigest()[:16]
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["c_e"] else 1

    if a.che == "dipingi":
        np = np_o_muori("dipingi")
        if a.fondo == "nero":
            img = np.zeros((a.altezza, a.larghezza, 3), np.uint8)
        elif a.fondo == "rumore":
            img = np.random.RandomState(7).randint(0, 256, (a.altezza, a.larghezza, 3),
                                                   dtype=np.uint8)
        else:
            yy = np.linspace(0, 1, a.altezza)[:, None]
            xx = np.linspace(0, 1, a.larghezza)[None, :]
            f = ((yy + xx) / 2 * 200 + 30).astype(np.uint8)
            img = np.repeat(f[:, :, None], 3, axis=2)
        dipingi_marca(img, a.disegno, a.istante_us, fnv1a32(a.giro),
                      MarcaGeometria(a.cella))
        est = os.path.splitext(a.file)[1].lower()
        if est in (".rgb24", ".rgb", ".raw"):
            img.tofile(a.file)
        else:
            from PIL import Image
            Image.fromarray(img).save(a.file)
        print(json.dumps({"file": a.file, "disegno": a.disegno,
                          "istante_us": a.istante_us, "giro": a.giro,
                          "giro_numero": fnv1a32(a.giro)}, ensure_ascii=False))
        return 0

    if a.che == "conta":
        r = leggi_conteggio(a.shm)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        # ⛔⭐ THE EXIT STATUS CARRIES THE VERDICT, not only readability.
        #    0 = numbers readable AND trusted · 1 = not readable · ⭐ 2 = readable
        #    but NOT TRUSTED.  A script doing `conta | jq .disegni` without
        #    looking at `fidato` would still get a number: with 2, `set -e`
        #    stops it.  ⚠ Three states and not two, because «I could not read» and
        #    «I read but I do not believe it» send you looking in two different places.
        if not r.get("c_e"):
            return 1
        return 0 if r.get("fidato") else 2

    if a.che == "nome":
        print(json.dumps({"giro": a.giro, "numero": fnv1a32(a.giro)}))
        return 0

    if a.che == "identita":
        img = carica(a.file, a.larghezza, a.altezza)
        r = leggi_marca(img)
        noti = {fnv1a32(g.strip()): g.strip() for g in a.giri.split(",") if g.strip()}
        d = {"da": "03-marca.py identita",
             "sorgente": os.path.abspath(a.file),
             "come": ("⭐ the round is READ FROM THE PIXELS of the painted frame, not "
                      "declared by the product: the mark carries it inside the "
                      "scene and the product carries the mark without knowing"),
             "giri_noti": {str(k): v for k, v in noti.items()}}
        if not r["c_e"]:
            # ⛔ Mark absent ⇒ `giro: None`.  M8 declares the check NOT
            #    RUN instead of counting it as passed.
            d["giro"] = None
            d["marca"] = {"c_e": False, "perche": r.get("perche")}
            d["non_applicabile"] = {
                "giro": ("⛔ the mark is NOT in the pixels of the painted frame: "
                         "%s.  ⚠ Here we do not guess the current round — it would be "
                         "the constant that makes it pass" % (r.get("perche") or "")[:160])}
        else:
            d["marca"] = {"c_e": True, "disegno": r["disegno"],
                          "istante_us": r["istante_us"], "giro_numero": r["giro"],
                          "contrasto": r["contrasto"]}
            d["giro"] = noti.get(r["giro"], "numero-ignoto-0x%08X" % r["giro"])
            d["disegno"] = r["disegno"]
            d["istante_us"] = r["istante_us"]
        for chiave, valore in (("dipinto_dopo_reset", a.dipinto_dopo_reset),
                               ("fin_ricevuto", a.fin_ricevuto),
                               ("dipinto", a.dipinto)):
            if valore is not None:
                d[chiave] = (valore == "si")
        if a.conti:
            d["conti"] = json.load(open(a.conti))
        with open(a.fuori, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(json.dumps({"fuori": a.fuori, "giro": d["giro"],
                          "disegno": d.get("disegno")}, ensure_ascii=False))
        return 0 if r["c_e"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
