#!/usr/bin/env python3
"""03-marca.py — THE MARK READER of the phase 3 scene.

    python3 03-marca.py read  fotogramma.rgb24 --width 1280 --height 720
    python3 03-marca.py read  fotogramma.png
    python3 03-marca.py paint fuori.png --draw 41 --time-us 123456 --round g1
    python3 03-marca.py count  --shm remotix-scena

===========================================================================
⛔ WHAT IT MUST BE ABLE TO SAY, AND THE HALF THAT GETS FORGOTTEN

The mandate: *«the mark reader: the function that, given a decoded
frame, returns the drawing number and the instant — and ⛔ that can
also say "the mark is not there".  A detector that always says yes measures zero
and is wrongly happy»* (`STUDI.md` §web §6.3, check **P3**).

⇒ `leggi_marca()` has TWO outputs, not one:

    {"c_e": True,  "draw": 41, "istante_us": 987654321, "round": 0x…, …}
    {"c_e": False, "why": "the CRC does not match …", "contrasto": 0.31, …}

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
# `import numpy` at the top, `03-marca.py count` — which does not use numpy at all,
# because it reads a shared memory block with `struct` — died on
# NIC-OS with an ImportError that talks about a library, not about the problem.
#
# ⇒ the plug is INSIDE this file and not outside: `count` works everywhere, and
#   whoever asks for `read` or `paint` without numpy gets a sentence that says **what
#   to do**, not the name of a missing module.
# ⚠ And `name` and `count` stay usable from NIC-OS, which is where the benches run.
_np = None


def np_or_die(desc):
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
                "   ⭐ What works HERE without numpy: «03-marca.py count» (the "
                "client's drawings, read from the shared block) and «03-marca.py "
                "name» (the 32-bit number of a round).\n"
                "   ⇒ either copy the frame to where numpy is, or install "
                "python3-numpy." % desc)
        _np = numpy
    return _np

# ───────────────────────────────────────────────────────────────────────────
# THE GEOMETRY — ⛔ must match `03-scena.c`.  Whoever changes a number
# here and not there breaks the reading, and the certification (check P6)
# notices instead of leaving it to be discovered by a wrong measurement.
# ───────────────────────────────────────────────────────────────────────────
SYNC      = 0xB2
VERSION  = 0x01
COLS   = 18
RIGHE     = 8
BIT       = COLS * RIGHE          # 144
CELL     = 24
HEADROOM   = 32
QUIET    = 12

MIN_CONTRAST = 0.25              # see §«the three sieves»
SEARCH          = 2                 # ± px

# BT.709, which is the matrix F2.3 chooses and that the rest of the chain
# declares.  ⚠ Here it only serves to make ONE number out of three channels: white and black
# give the same result with any sensible matrix.
LUMA_WEIGHTS = (0.2126, 0.7152, 0.0722)


class MarkGeometry:
    def __init__(self, cell=CELL, margin=HEADROOM, quiet=QUIET,
                 columns=COLS, lines=RIGHE):
        self.cell, self.margin, self.quiet = int(cell), int(margin), int(quiet)
        self.columns, self.lines = int(columns), int(lines)
        self.bit = self.columns * self.lines

    def block(self):
        return (self.margin, self.margin,
                self.columns * self.cell, self.lines * self.cell)

    def __repr__(self):
        return ("MarkGeometry(cella=%d, margine=%d, quiete=%d, %dx%d)"
                % (self.cell, self.margin, self.quiet, self.columns, self.lines))


GEOMETRY = MarkGeometry()


# ───────────────────────────────────────────────────────────────────────────
def fnv1a32(s):
    """The same short name that `03-scena.c` puts in the mark."""
    h = 2166136261
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def crc16(data):
    """CRC-16/CCITT-FALSE — poly 0x1021, init 0xFFFF, no reflection."""
    c = 0xFFFF
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def compose_load(draw, instant_us, round_number):
    """The 18 bytes of the mark, in the order in which they end up in the cells."""
    body = struct.pack(">BII", VERSION, round_number & 0xFFFFFFFF,
                        draw & 0xFFFFFFFF)
    t = instant_us & 0xFFFFFFFFFFFF                     # 48 bit
    body += bytes(((t >> 40) & 0xFF, (t >> 32) & 0xFF, (t >> 24) & 0xFF,
                    (t >> 16) & 0xFF, (t >> 8) & 0xFF, t & 0xFF))
    assert len(body) == 15
    return bytes([SYNC]) + body + struct.pack(">H", crc16(body))


def load_in_bit(overall, amount):
    np = np_or_die("carico_in_bit")
    b = np.zeros(amount, dtype=np.uint8)
    for i in range(amount):
        b[i] = (overall[i >> 3] >> (7 - (i & 7))) & 1
    return b


# ───────────────────────────────────────────────────────────────────────────
# THE PAINTER.  ⛔ It serves the POSITIVE CONTROL and nothing else: the real scene is
# painted by `03-scena.c`.  That the two paint the same thing is not assumed —
# `03-scena-certifica.sh` (P6) reads with this reader a frame painted
# by the C and compares with what the C declared.
# ───────────────────────────────────────────────────────────────────────────
def paint_mark(img, draw, instant_us, round_number, geo=GEOMETRY):
    """Paints the mark INTO `img` (uint8 [h,w,3]).  Returns `img`."""
    np_or_die("dipingi_marca")
    overall = compose_load(draw, instant_us, round_number)
    bit = load_in_bit(overall, geo.bit)
    x0, y0, w, h = geo.block()
    H, W = img.shape[:2]
    if y0 + h + geo.quiet > H or x0 + w + geo.quiet > W:
        raise ValueError("⛔ the mark does not fit: it needs at least %dx%d, the image "
                         "is %dx%d" % (x0 + w + geo.quiet, y0 + h + geo.quiet, W, H))
    img[max(0, y0 - geo.quiet):y0 + h + geo.quiet,
        max(0, x0 - geo.quiet):x0 + w + geo.quiet] = 0
    for i in range(geo.bit):
        if not bit[i]:
            continue
        r, c = divmod(i, geo.columns)
        img[y0 + r * geo.cell:y0 + (r + 1) * geo.cell,
            x0 + c * geo.cell:x0 + (c + 1) * geo.cell] = 255
    return img


# ───────────────────────────────────────────────────────────────────────────
# ⭐⛔ THE READER
# ───────────────────────────────────────────────────────────────────────────
def _luma(img):
    np = np_or_die("leggi_marca")
    a = np.asarray(img)
    weights = np.array(LUMA_WEIGHTS, dtype=np.float64)
    if a.ndim == 2:
        return a.astype(np.float64) / 255.0
    if a.ndim == 3 and a.shape[2] >= 3:
        return (a[:, :, :3].astype(np.float64) @ weights) / 255.0
    raise ValueError("the image is neither grey nor three-channel: %s" % (a.shape,))


def _cells(y, geo, dx, dy):
    """The mean luminance of the CENTRE of each cell, in bit order."""
    x0, y0, _, _ = geo.block()
    x0 += dx
    y0 += dy
    np = np_or_die("leggi_marca")
    c = geo.cell
    inside = max(2, c // 4)              # the central square at 50 % is read
    val = np.empty(geo.bit, dtype=np.float64)
    for i in range(geo.bit):
        r, k = divmod(i, geo.columns)
        ya = y0 + r * c + inside
        xa = x0 + k * c + inside
        val[i] = y[ya:ya + c - 2 * inside, xa:xa + c - 2 * inside].mean()
    return val


def _try_position(y, geo, dx, dy):
    np = np_or_die("leggi_marca")
    val = _cells(y, geo, dx, dy)
    alto = float(np.percentile(val, 90))
    low = float(np.percentile(val, 10))
    contrast = alto - low
    outcome = {"contrast": round(contrast, 4), "scorrimento_provato": [dx, dy]}
    if contrast < MIN_CONTRAST:
        outcome["why"] = ("the contrast between the cells is %.3f, below the minimum "
                           "%.2f: there is no two-level signal here"
                           % (contrast, MIN_CONTRAST))
        return None, outcome
    threshold = (alto + low) / 2.0
    bit = (val > threshold).astype(np.uint8)

    byte = bytearray(len(bit) // 8)
    for i, b in enumerate(bit):
        if b:
            byte[i >> 3] |= 1 << (7 - (i & 7))
    byte = bytes(byte)

    if byte[0] != SYNC:
        outcome["why"] = ("the first 8 bits are 0x%02X instead of the sync 0x%02X"
                           % (byte[0], SYNC))
        return None, outcome
    body, crc_read = byte[1:16], struct.unpack(">H", byte[16:18])[0]
    expected_crc = crc16(body)
    if crc_read != expected_crc:
        outcome["why"] = ("the sync is there but the CRC does not match: read 0x%04X, "
                           "computed 0x%04X ⇒ the mark was there and broke, "
                           "or it is chance" % (crc_read, expected_crc))
        return None, outcome

    version = body[0]
    round_id = struct.unpack(">I", body[1:5])[0]
    draw = struct.unpack(">I", body[5:9])[0]
    instant = int.from_bytes(body[9:15], "big")
    if version != VERSION:
        # ⛔ A CRC that matches with a version we do not know is NOT
        #    «mark absent»: it is a mark from another draft, and reading it with
        #    our layout would give wrong numbers that look right.
        outcome["why"] = ("mark of version %d, this reader reads version %d: "
                           "the fields are not in the same place and reading it "
                           "would give plausible and false numbers" % (version, VERSION))
        outcome["versione_marca"] = version
        return None, outcome

    good = {"c_e": True, "version": version, "round": round_id,
             "draw": draw, "istante_us": instant,
             "contrast": round(contrast, 4), "threshold": round(threshold, 4),
             "scorrimento_provato": [dx, dy]}
    return good, outcome


def read_image_mark(img, geo=GEOMETRY, search=SEARCH):
    """⭐ Given a frame, says whether the mark is there and what it says.

    Returns a dictionary that ALWAYS has the key `c_e`:
      c_e = True   → `draw`, `instant_us`, `round_id`, `contrast`,
                     `scorrimento_provato`
      c_e = False  → `perche` (⛔ never absent), plus whatever could be seen
    """
    y = _luma(img)
    H, W = y.shape
    x0, y0, w, h = geo.block()
    needs_w, needs_h = x0 + w + search, y0 + h + search
    if W < needs_w or H < needs_h:
        return {"c_e": False,
                "why": ("⛔ I could not LOOK: the frame is %dx%d and the "
                           "mark block ends at %dx%d.  ⚠ It is not «the mark "
                           "is not there»: it is «the mark would not fit»"
                           % (W, H, needs_w, needs_h)),
                "size": [W, H], "serve": [needs_w, needs_h]}

    # ⛔ THE ORDER OF THE POSITIONS IS NOT IRRELEVANT, and the first draft
    #    got it wrong — found by running, 13 Aug 2026.  Scanning from
    #    (−2,−2) upwards, a PERFECTLY aligned frame was read correctly
    #    but declared `scroll: [-2,-2]`: the cell is 24 px wide and is
    #    read at the centre, so two pixels of offset pass anyway.  The
    #    payload came out right and the number beside it was false — and it is the kind of
    #    number that ends up in a document as a measurement.
    # ⇒ (0,0) is tried first and then at increasing radius: whoever declares an
    #   offset really has it.
    order = sorted(
        ((dx, dy) for dy in range(-search, search + 1)
                  for dx in range(-search, search + 1)),
        key=lambda p: (max(abs(p[0]), abs(p[1])), abs(p[0]) + abs(p[1]), p))
    best = None
    for dx, dy in order:
        if y0 + dy < 0 or x0 + dx < 0:
            continue
        good, outcome = _try_position(y, geo, dx, dy)
        if good is not None:
            good["posizioni_provate"] = (2 * search + 1) ** 2
            return good
        if best is None or outcome["contrasto"] > best["contrasto"]:
            best = outcome
    report = {"c_e": False, "posizioni_provate": (2 * search + 1) ** 2}
    report.update(best or {"why": "no position tried"})
    report["why"] = ("the mark is NOT there in any of the %d offsets tried "
                       "(± %d px).  The best one said: %s"
                       % (report["posizioni_provate"], search, report.get("why")))
    return report


# ───────────────────────────────────────────────────────────────────────────
# THE COUNT OF THE CLIENT'S DRAWINGS — read from outside, from the shared block.
#
# ⛔ §1.1: «alongside, count how much the client draws: it is the check that
#    says whether the ceiling belongs to the compositor or to the scene».
# ───────────────────────────────────────────────────────────────────────────
STATE_MAGIC = 0x524D5853
STATE_VERSION = 2
# ⛔ Must match `struct stato_condiviso` of `03-scena.c`.  `magic` and
#    `version` exist so that a misalignment gives a REFUSAL instead of
#    random numbers.
STATE_FORMAT = "<4I Q 5Q 5Q 10I i 3I 64s 32s 64s 64s 4Q 4I"


def read_count(shm_name="remotix-scena"):
    """Returns the client's counts, or `{"c_e": False, "why": …}`."""
    fpath = "/dev/shm/" + shm_name
    if not os.path.exists(fpath):
        return {"c_e": False,
                "why": ("⛔ «%s» does not exist: the scene never started, "
                           "or it has another name (--shm).  ⚠ It is not «it "
                           "drew zero times»" % fpath)}
    trim = struct.calcsize(STATE_FORMAT)
    with open(fpath, "rb") as f:
        with mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ) as m:
            if len(m) < trim:
                return {"c_e": False,
                        "why": "«%s» is %d bytes, %d are needed: the structure "
                                  "is not that one" % (fpath, len(m), trim)}
            # ⛔ Seqlock: read twice and demand `seq` even and equal.
            #    Without it, one can take a new `draw` with an old
            #    `instant` and believe in a delay that never existed.
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
            #   returns to the main loop**, so it ignores `--seconds`
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
            samples = 0
            first_seq = struct.unpack(STATE_FORMAT, m[:trim])[4]
            last_seq = first_seq
            consistent = None
            for _ in range(400):
                a = struct.unpack(STATE_FORMAT, m[:trim])
                samples += 1
                last_seq = a[4]
                if a[4] % 2 == 0:
                    b = struct.unpack(STATE_FORMAT, m[:trim])
                    if b[4] == a[4]:
                        consistent = a
                        break
                time.sleep(0.0002)
            if consistent is None:
                stopped = (last_seq == first_seq)
                stale_pid = struct.unpack(STATE_FORMAT, m[:trim])[25]
                wreck_alive = os.path.exists("/proc/%d" % stale_pid)
                if stopped:
                    why = (
                        "⛔ «%s» is a WRECK: `seq` is %d — odd — and has NOT "
                        "changed in %d attempts.  A write was left "
                        "open, i.e. the scene died (or is stuck) halfway.  "
                        "⚠ Process %d %s.  ⛔ No number of attempts will ever "
                        "find it even: do not wait, restart the scene "
                        "(the block is reset at startup)."
                        % (fpath, last_seq, samples, stale_pid,
                           "is still alive — so it is STUCK, not dead"
                           if wreck_alive else "no longer exists"))
                else:
                    why = (
                        "⛔ `seq` changes (%d → %d in %d attempts) and I never "
                        "caught it even: this really is contention.  ⚠ It was never "
                        "observed, not even with a scene at 1034 "
                        "drawings/s — if you see it, report it."
                        % (first_seq, last_seq, samples))
                return {"c_e": False, "fidato": False, "samples": samples,
                        "seq": int(last_seq), "relitto": bool(stopped),
                        "why": why}
            a = consistent
    (magic, version, dim, _r0, seq,
     drawings, commit, presented, waits, discards,
     startup_mono, startup_real, last_drawing, last_pres, last_real_pres,
     round_number, width, height, cell, columns, lines, margin, quiet,
     motion, damage, pid, pres_avail, fullscreen, _r1,
     round_name, scene_version, confirmed_output, requested_output,
     reentries, idle_runs, draws_without_callback, skipped_without_buffer,
     callback_in_flight, max_callbacks_in_flight, refresh_mhz, trusted) = a

    if magic != STATE_MAGIC:
        return {"c_e": False,
                "why": "«%s» is not a 03-scena block (magic 0x%08X)"
                          % (fpath, magic)}
    if version != STATE_VERSION:
        return {"c_e": False,
                "why": ("⛔ block of version %d, this reader reads version %d: "
                           "the fields are not in the same place"
                           % (version, STATE_VERSION))}
    alive = os.path.exists("/proc/%d" % pid)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⭐ THE VERDICT ON THE NUMBER, NOT ONLY THE NUMBER.
    #
    # Asked by the coordinator on 13 Aug 2026: *«a count of 540/s on a
    # 60 Hz monitor is an observable fact: it must be FLAGGED, not handed over.
    # Until that detector exists, every cell measured with your scene by
    # someone else's bench is `[?]`, not `[M]`.»*
    #
    # ⇒ `read_count()` no longer returns only counts: it returns
    #   `trusted` and, when it is false, **the list of reasons**.  A bench that
    #   reads these numbers and does not look at `trusted` is deliberately doing what
    #   §2.2 forbids.
    #
    # ⚠ And the reasons are of TWO kinds, kept separate:
    #     · those the scene measured on itself (re-entries, callbacks in
    #       flight) — they are causes, and hold at any frequency;
    #     · those the reader computes from outside (rate against refresh, stale
    #       block, dead writer) — they are symptoms, and needs to catch the
    #       cases where the scene could not notice by itself (for example
    #       a scene killed halfway).
    # ═══════════════════════════════════════════════════════════════════════
    why = []
    if reentries:
        why.append("⛔ %d RE-ENTRIES: `disegna()` was called inside "
                      "itself — an event handler drew" % reentries)
    if max_callbacks_in_flight > 1:
        why.append("⛔ up to %d `wl_surface.frame` IN FLIGHT together (1 is "
                      "allowed): the scene draws without being invited, and "
                      "the rate is multiplied by that number"
                      % max_callbacks_in_flight)
    if idle_runs:
        why.append("⛔ %d BUSY-LOOP rounds" % idle_runs)

    # the mean rate since startup, against the refresh declared by the output
    rate = None
    duration = (last_drawing - startup_mono) / 1e6 if last_drawing > startup_mono else 0
    if duration > 0.5:
        rate = drawings / duration
        if refresh_mhz > 0 and rate > 1.5 * (refresh_mhz / 1000.0):
            why.append("⛔ %.0f drawings/s on a %.1f Hz monitor: more than "
                          "one and a half times the refresh is not a rate, it is "
                          "a busy loop"
                          % (rate, refresh_mhz / 1000.0))
    if not alive:
        # ⚠ It is NOT «the numbers are wrong»: they are the LAST snapshot of a
        #   scene that is no longer there.  Handing them over as current would be
        #   yesterday's measurement passed off as today's.
        why.append("⚠ process %d that wrote this block is NO "
                      "longer alive: these are its last numbers, not the "
                      "numbers of now" % pid)

    return {
        "c_e": True, "alive": alive, "pid": int(pid), "seq": int(seq),
        # ⭐ the verdict, and it comes BEFORE the numbers because it governs them
        "fidato": (not why),
        "perche_non_fidato": why,
        "reentries": int(reentries), "idle_runs": int(idle_runs),
        "draws_without_callback": int(draws_without_callback),
        "skipped_without_buffer": int(skipped_without_buffer),
        "callback_in_flight": int(callback_in_flight),
        "max_callbacks_in_flight": int(max_callbacks_in_flight),
        "refresh_hz": (refresh_mhz / 1000.0) if refresh_mhz else None,
        "disegni_al_secondo": round(rate, 2) if rate is not None else None,
        "drawings": int(drawings), "commit": int(commit),
        "presented": int(presented), "waits": int(waits),
        "scarti_presentazione": int(discards),
        # ⛔ The field that tells «zero presented» from «presented not
        #    measurable on this compositor» (`LEZIONI.md` §1.9).
        "presentazione_disponibile": bool(pres_avail),
        "avvio_monotonico_us": int(startup_mono), "avvio_reale_us": int(startup_real),
        "ultimo_disegno_us": int(last_drawing),
        "ultimo_presentato_us": int(last_pres),
        "ultimo_presentato_reale_us": int(last_real_pres),
        "round": round_name.split(b"\0")[0].decode("utf-8", "replace"),
        "round_number": int(round_number),
        "width": int(width), "height": int(height),
        "cell": int(cell), "columns": int(columns), "lines": int(lines),
        "margin": int(margin), "quiet": int(quiet),
        "motion": ["mark", "barra", "pieno"][int(motion)] if motion < 3 else int(motion),
        "damage": ["preciso", "pieno"][int(damage)] if damage < 2 else int(damage),
        "fullscreen": bool(fullscreen),
        "scene_version": scene_version.split(b"\0")[0].decode("utf-8", "replace"),
        # ⛔ «asked_size» (requested) is our intention; «confermata» (confirmed) is what the
        #    COMPOSITOR said with `wl_surface.enter`.  Empty does NOT mean
        #    «on none»: it means «no enter has arrived yet», and the two
        #    cases send you looking in two different places (`LEZIONI.md` §1.9).
        "requested_output": requested_output.split(b"\0")[0].decode("utf-8", "replace") or None,
        "confirmed_output": (confirmed_output.split(b"\0")[0]
                              .decode("utf-8", "replace") or None),
    }


# ───────────────────────────────────────────────────────────────────────────
def load(fpath, width=None, height=None):
    """raw .rgb24 (needs the dimensions), .png / .ppm via Pillow."""
    est = os.path.splitext(fpath)[1].lower()
    if est in (".rgb24", ".rgb", ".raw"):
        if not width or not height:
            raise SystemExit("⛔ «%s» is raw: without --width and --height I do not "
                             "know its shape, and guessing it would mean "
                             "reading the mark in the wrong place" % fpath)
        data = open(fpath, "rb").read()
        expected = width * height * 3
        if len(data) < expected:
            raise SystemExit("⛔ «%s»: %d bytes, %d were needed for %dx%d rgb24"
                             % (fpath, len(data), expected, width, height))
        np = np_or_die("carica")
        return np.frombuffer(data[:expected], np.uint8).reshape(height, width, 3)
    np = np_or_die("carica")
    from PIL import Image
    return np.asarray(Image.open(fpath).convert("RGB"))


def main():
    p = argparse.ArgumentParser(description="the scene's mark reader")
    s = p.add_subparsers(dest="what", required=True)

    q = s.add_parser("read", help="given a frame, says whether the mark is there")
    q.add_argument("file")
    q.add_argument("--width", type=int)
    q.add_argument("--height", type=int)
    q.add_argument("--cell", type=int, default=CELL)
    q.add_argument("--margin", type=int, default=HEADROOM)
    q.add_argument("--quiet", type=int, default=QUIET)
    q.add_argument("--search", type=int, default=SEARCH)

    d = s.add_parser("paint", help="⚠ only for the positive control")
    d.add_argument("file")
    d.add_argument("--width", type=int, default=1280)
    d.add_argument("--height", type=int, default=720)
    d.add_argument("--draw", type=int, required=True)
    d.add_argument("--time-us", type=int, required=True)
    d.add_argument("--round", default="senza-nome")
    d.add_argument("--cell", type=int, default=CELL)
    d.add_argument("--background", default="gray", choices=("gray", "black", "noise"))

    c = s.add_parser("count", help="the client's drawings, read from outside")
    c.add_argument("--shm", default="remotix-scena")

    n = s.add_parser("name", help="the 32-bit number of a round name")
    n.add_argument("round")

    # ⭐⛔ THE REOPENING OF M8'S `round_id` CHECK.
    #
    # `fasi/rapporti/F2-6-giudizio.md`, 13 Aug 2026: M8's `round_id` check
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
    # ⛔ And if the mark is NOT there, `round_id` comes out **null**: M8 declares the check
    #   NOT RUN.  Writing the current round into it would be the constant
    #   that made it pass, i.e. the false green of 13 August.
    idn = s.add_parser("identity",
                       help="⭐ builds M8's --identita-pagina by reading the "
                            "round FROM THE PIXELS")
    idn.add_argument("file")
    idn.add_argument("--width", type=int)
    idn.add_argument("--height", type=int)
    idn.add_argument("--rounds", required=True,
                     help="the names of the known rounds, comma-separated: it is "
                          "the list used to invert the mark's number")
    idn.add_argument("--out", required=True)
    idn.add_argument("--painted-after-reset", choices=("yes", "no"),
                     help="⚠ if you do not declare it, M8 does NOT pretend to have looked")
    idn.add_argument("--fin-received", choices=("yes", "no"))
    idn.add_argument("--painted", choices=("yes", "no"))
    idn.add_argument("--counts", help="the JSON of the page's counts")

    a = p.parse_args()

    if a.che == "read":
        geo = MarkGeometry(a.cell, a.margin, a.quiet)
        img = load(a.file, a.width, a.height)
        r = read_image_mark(img, geo, a.search)
        r["file"] = a.file
        r["impronta"] = hashlib.sha256(open(a.file, "rb").read()).hexdigest()[:16]
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["c_e"] else 1

    if a.che == "paint":
        np = np_or_die("paint")
        if a.background == "black":
            img = np.zeros((a.height, a.width, 3), np.uint8)
        elif a.background == "noise":
            img = np.random.RandomState(7).randint(0, 256, (a.height, a.width, 3),
                                                   dtype=np.uint8)
        else:
            yy = np.linspace(0, 1, a.height)[:, None]
            xx = np.linspace(0, 1, a.width)[None, :]
            f = ((yy + xx) / 2 * 200 + 30).astype(np.uint8)
            img = np.repeat(f[:, :, None], 3, axis=2)
        paint_mark(img, a.draw, a.time_us, fnv1a32(a.round),
                      MarkGeometry(a.cell))
        est = os.path.splitext(a.file)[1].lower()
        if est in (".rgb24", ".rgb", ".raw"):
            img.tofile(a.file)
        else:
            from PIL import Image
            Image.fromarray(img).save(a.file)
        print(json.dumps({"file": a.file, "draw": a.draw,
                          "time_us": a.time_us, "round": a.round,
                          "giro_numero": fnv1a32(a.round)}, ensure_ascii=False))
        return 0

    if a.che == "count":
        r = read_count(a.shm)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        # ⛔⭐ THE EXIT STATUS CARRIES THE VERDICT, not only readability.
        #    0 = numbers readable AND trusted · 1 = not readable · ⭐ 2 = readable
        #    but NOT TRUSTED.  A script doing `count | jq .drawings` without
        #    looking at `trusted` would still get a number: with 2, `set -e`
        #    stops it.  ⚠ Three states and not two, because «I could not read» and
        #    «I read but I do not believe it» send you looking in two different places.
        if not r.get("c_e"):
            return 1
        return 0 if r.get("fidato") else 2

    if a.che == "name":
        print(json.dumps({"round": a.round, "number": fnv1a32(a.round)}))
        return 0

    if a.che == "identity":
        img = load(a.file, a.width, a.height)
        r = read_image_mark(img)
        known = {fnv1a32(g.strip()): g.strip() for g in a.rounds.split(",") if g.strip()}
        d = {"da": "03-marca.py identity",
             "sorgente": os.path.abspath(a.file),
             "come": ("⭐ the round is READ FROM THE PIXELS of the painted frame, not "
                      "declared by the product: the mark carries it inside the "
                      "scene and the product carries the mark without knowing"),
             "giri_noti": {str(k): v for k, v in known.items()}}
        if not r["c_e"]:
            # ⛔ Mark absent ⇒ `round_id: None`.  M8 declares the check NOT
            #    RUN instead of counting it as passed.
            d["round"] = None
            d["mark"] = {"c_e": False, "why": r.get("why")}
            d["non_applicabile"] = {
                "round": ("⛔ the mark is NOT in the pixels of the painted frame: "
                         "%s.  ⚠ Here we do not guess the current round — it would be "
                         "the constant that makes it pass" % (r.get("why") or "")[:160])}
        else:
            d["mark"] = {"c_e": True, "draw": r["draw"],
                          "istante_us": r["istante_us"], "giro_numero": r["round"],
                          "contrasto": r["contrasto"]}
            d["round"] = known.get(r["round"], "numero-ignoto-0x%08X" % r["round"])
            d["draw"] = r["draw"]
            d["istante_us"] = r["istante_us"]
        for key, value in (("painted_after_reset", a.painted_after_reset),
                               ("fin_received", a.fin_received),
                               ("painted", a.painted)):
            if value is not None:
                d[key] = (value == "yes")
        if a.counts:
            d["counts"] = json.load(open(a.counts))
        with open(a.out, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(json.dumps({"out": a.out, "round": d["round"],
                          "draw": d.get("draw")}, ensure_ascii=False))
        return 0 if r["c_e"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
