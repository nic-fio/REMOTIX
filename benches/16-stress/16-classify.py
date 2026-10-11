#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-classify — THE JUDGEMENT OF A LEVEL, WITH THE THRESHOLDS OF §9 (phase 16)

    python3 16-classify.py --level-dir DIR/level-NN [--fps-video 30]
                             [--window-s 120] [--log benches/16-stress/registro.jsonl]
                             [--campaign intel-4k-kde] [--level N] [--dry-run]
    python3 16-classify.py --certify

⛔ The thresholds are those of `phases/16-stress-and-capacity.md` §9, APPROVED
   by the user on 25 Sep 2026 and FROZEN: they live in the THRESHOLDS table below,
   one row per row of §9, and no parameter changes them.  Only `f` (the
   frame rate of the chosen video, --fps-video) and the check window
   (--window-s, the last 2 minutes of the level) are parameters.

Writes at the end of the log (appends only) ONE row for the level and ONE for
each session (§10), and prints the readable judgement.  --dry-run: does not write.

WHAT IT READS, in the level folder
----------------------------------------------------------------------------
  level.json        (optional, written by whoever runs the climb) the fields
                      of §10 that are not measured: campagna, livello, desktop,
                      scheda, driver, misura, commit, binario, pagina, nucleo,
                      inizio, durata_s, fps_video, tetto_sessioni,
                      utenti:[{utente, profilo, browser, versione, nuovo}]
  resources.jsonl       from 16-resources.py (one row per second)
  user-NN/state.jsonl   one row every 5 s, written by the actor:
      {"t": <epoch s>, "user": 3, "profile": "C", "browser": "firefox",
       "version": "Firefox 140…", "tenant": "c16u03",
       "counts": {"delivered","painted","skip","holes","overtaken",
                 "received","played","HOLES","missed"}   ← CUMULATIVE, from the
                 page (or "diary": the page's «audio: received … painted …
                 video X→Y … skip … holes …» line, and it is read from here)
       "round_trip": {"seen": n, "samples": [ms, …]}   ← the page's `window.REMOTIX.round_trip`
                 (the last 200 command → frame delays);
                 or "giro_ms": [only the NEW samples since the last row]
       "input": [{"ok": true, "latency_ms": 180, "action": "cartella"}, …]
                 the actions of the interval, with the effect VERIFIED (photo)
       "block_max_ms": 420   ← the longest freeze of the image in the 5 s
                 with work in progress (the actor watches the canvas: from here a
                 5 s granularity cannot see below 5 s)
       "work": true,  "drop": false,  "errors": ["…"]}
  user-NN/birth.json  {"access_ms": <epoch ms>, "first_frame_ms":
                      <epoch ms>, "outcome": "ok"|"refusal"|"…"} (or "birth_ms")
  short-check.json    {"user": N, "outcomes": {"F-004": "PASS", …}}
  server.log          the extract of the server log cut on the level

THE MEASURES, and where they come from (§7 → §9)
----------------------------------------------------------------------------
  delay     (26 Sep, from the coordinator) p95, over the window, of the PER-SECOND p95s
            of the child's «⭐ NOSTRO nel secondo (copia → byte fuori, §3.2)» rows
            (today «⭐ OURS in the second (copy → byte out, §3.2)»; commit ebc9dcd:
            only the frames of that second, without the compositor's
            «producer») + 9 ms (constructive cap of the input
            stretch, the child's 8 ms poll): the PRODUCT's piece.  The
            per-second max is recorded.  The «TRATTO cattura → byte fuori» rows
            («STRETCH capture → byte out») are only RECORDED (their `max` is from
            the rolling sample of 512 frames, and the producer is inside it).
            ⚠ On the wlroots path the row counts the «copy» twice (~4 ms
            more): NOT corrected, on the cautious side.  No rows ⇒ not measured.
            The page's ROUND (below) is recorded as EXPERIENCE: `giro_eco`
            (typing only) and the whole `giro`, which do not classify.
            The ROUND is the measure
            the PRODUCT takes (`page.html`, `ROUND.depart` on the input,
            `ROUND.arrive` when the frame that carries that input arrives in the
            28 bytes of RCP §6.2; the server stamps the id in the child, at the instant
            of capture).  ⚠ It does not include decoding and drawing: it is a LOWER
            bound of what the eye sees (the page itself says so).  The
            server does NOT write an input→frame delay in the log (it writes
            «TRATTO cattura → byte fuori», recorded as `tratto_server`
            but not classifying).  The latency of the input VERIFIED by the actor
            (gesture → effect in the photo) is recorded (`input_latenza_p95`) but
            does not classify: the photo is inside it.  «Input lost» (an action with
            ok=false) ⇒ FAIL, as §9 says.  Profile D (video only, no
            input): the entry does not apply, unless samples are present.
            ⚠ A false «video_avanza» check (profile D: the time of the video
            in the scene does not advance) is NOT a lost input: it goes to the
            video entry (significant DEGRADED: stuck in the scene, cause to look at).
  skipped   (Δconsegnati − Δdipinti) / Δconsegnati — the page's `video X→Y`:
            everything the wire brought that did not reach the glass
            (saltati_coda, late, discarded, lost in the decoder).  It is the
            AWKWARD direction: `salt` alone (saltati_coda) is recorded separately.
  freeze    the maximum of `blocco_max_ms`.  Without it, from the counters: 5 s with
            work and no frame painted ⇒ freeze >= 5 s (FAIL); the
            whole window without frames ⇒ «still image» (FAIL); if
            nothing is seen below 5 s ⇒ «not measured» (the granularity is not enough).
  holes     Δbuchi per minute (keyframes requested by the page).
  video     (profile D) Δdipinti / Δt against f = --fps-video.
  audio     (profile D) Δsuonati / (Δricevuti + Δmancati): what the server
            sent and was heard.  No block while the video plays ⇒ 0 %.
  birth     primo_fotogramma_ms − accesso_ms; «rifiuto» ⇒ FAIL.  Only for the
            users born in the level: `nuovo` in level.json (its absence is
            «not measured»); if the list is not there, only if `accesso_ms` falls
            inside the level.  The other birth.json are from an earlier
            rung (the actor's folder carries over): they are RECORDED
            (`nascita_precedente`) and do not classify.
  short     short-check.json: a FAIL ⇒ FAIL; a BLOCKED ⇒ not measured.
  drop      `caduta` in the state, page counters restarted from zero
            (page reloaded or reattached), and in the server log for
            that tenant: «the session is over», «the stage … has
            gone», «the child … is leaving», protocol error (and the old Italian
            forms of the same lines) — ⚠ in the WHOLE
            level, not only in the window: a drop at minute 3 is a
            drop.  The server restart (an «avvio REMOTIX» row, or the pid
            of the parent changing in resources.jsonl) ⇒ FAIL for all.
  memory    (level) PSS of the `remotix` and `sessioni` enclosures over ALL the work
            of the level, not over the window (§6: the last rung lasts 30 min
            precisely to see leaks): from start of work + 60 s of
            settling (start of work = end − durata_lavoro_s of
            level.json; otherwise inizio_t; otherwise the first row; and anyway after
            the last birth of a new user that is known) to the start of the
            short check (end − controllo_min: session 99 is born there and
            weighs on the `sessioni` enclosure), otherwise to the end.
            growth = (mean of the last 30 s − mean of the first 30 s) / first.
            «And keeps going» = the least-squares line over the SECOND HALF of the
            stretch rises (a) more than 2 % per hour of the mean and (b) by more than a
            third of the total growth along the half (slope × half duration).
            A linear growth gives 1/2 ⇒ keeps going; a step in the first
            half and then flat ⇒ stopped.  §9 thresholds unchanged: > 15 % and stopped ⇒
            significant DEGRADED.
            The `browser` enclosure is recorded and does NOT classify (§9).

«NOT MEASURED» — never green by absence
----------------------------------------------------------------------------
An entry that applies and has no data is DEGRADED with the `non_misurato` mark,
and counts as SIGNIFICANT DEGRADED (nobody knows by how much): the climb stops
and the setup is looked at, instead of climbing on a number that is not there.

--system xrdp (phases/20 §7.3, 9 Oct 2026): the series of 16-actor-rdp.py.  Same thresholds, and
            the entries are read like this:
  delay     p95 of the rows' `ritardi_ms` (impulse → first XDamage draw after it, from the
            VIEWER'S SIDE: key, click, notch), over the window; with fewer than 5
            samples in the window, over the whole level (said in the note).  ⚠ It is not
            REMOTIX's «OURS + 9 ms» (server side): it is compared with the page's
            ROUND.  Profile D without impulses: the entry does not apply.  «Input lost» ⇒
            FAIL as always.
  skipped, holes, audio  ⛔ NOT MEASURED BY CONSTRUCTION: xrdp does not send the frames
            it cannot, has no counters in the page, and the audio travels without being
            played.  They do not enter the class (they are in `misure.non_misurati_per_costruzione`).
  drop      from the actor (xfreerdp exited, the window gone); the xrdp log
            does not have the time in the form of ours and is not read for drops.
  log       the rows go into register-xrdp.jsonl, with the `sistema` field.

THE LEVEL (§9): GREEN if all the sessions (and the level entries) are
GREEN; DEGRADED if at least one is DEGRADED and none FAIL; FAIL if at least one is
FAIL.  SIGNIFICANT DEGRADED = more than a quarter of the ACTORS' sessions
DEGRADED (the check, user 99, does not count; k·4 > n, exact), or a measure
beyond HALF of the DEGRADED band (column `meta` of THRESHOLDS).
⛔ ENTERED: if the actors present (user-NN folders, and those of the
`utenti` list of level.json without a folder count as absent) are fewer than the
declared level (--level, otherwise level.json) ⇒ level entry
`entrati` FAIL «entered K of N»: a rung not reached is not a rung passed.
"""
import argparse
import datetime as _dt
import glob
import json
import math
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHOSEN_VIDEO_FPS = 30          # the video of profile D (from the coordinator, 26 Sep 2026)
LOG = os.path.join(HERE, "registro.jsonl")
ORDER = {"GREEN": 0, "DEGRADED": 1, "FAIL": 2}

# ── the levels of the campaigns before the English rename (DECISIONI §10.38) keep the Italian
#    words: misure/ is never rewritten (16-reclassify.py re-judges them with this classifier).
#    The first tuple is protected (english-migration/protetti.tsv), the second is renamed with
#    the code: after the rename OLD_SPELLING maps every old word to the code's own, before it
#    is empty.  Same order in both, one word per position.  They are the keys and the values
#    read from level.json, user-NN/state.jsonl, birth.json, short-check.json,
#    resources.jsonl, journal-err.jsonl and the `quic-net` rows of server.log.
_OLD_WORDS = (
    "utenti", "utente", "nuovo", "controllo_min", "livello", "campagna", "scheda", "misura", "binario",
    "pagina", "nucleo", "tetto_sessioni", "inizio", "durata_s", "profilo", "versione", "inquilino",
    "conti", "consegnati", "dipinti", "buchi", "ricevuti", "suonati", "BUCHI", "mancati", "diario",
    "giro", "visti", "campioni", "azione", "video_avanza", "lavoro", "caduta", "errori",
    "accesso_ms", "esito", "rifiuto", "nascita", "ragione", "esiti", "funzione",
    "tipo", "campione", "macchina", "carico", "sessioni", "altro_scatola", "labwc_cliente", "processi",
    "per_inquilino", "avvisi", "disegno", "REMOTIX_INQUILINO",
    "persi", "byte_persi", "spediti", "byte_spediti", "scartati", "dgram_persi", "dgram_falsi",
    "ammissione_s", "blocco_max_ms", "categorie", "durata_lavoro_s", "fine", "freq_att_mhz", "giro_eco",
    "inizio_finestra_t", "inizio_t", "latenza_ms", "mem_totale_mb", "mem_usata_mb", "nascita_ms",
    "nascita_s", "occupata_pct", "potenza_w", "primo_fotogramma_ms", "primo_non_degenere_s", "recinti",
    "ritardi_eco_ms", "ritardi_ms", "salt", "sessioni_durante", "vram_usata_mb", "tard",
    "utente-",
)  # end of the old words
_WORDS_NOW = (
    "users", "user", "new", "check_min", "level", "campaign", "card", "size", "binary",
    "page", "kernel", "session_cap", "started", "duration_s", "profile", "version", "tenant",
    "counts", "delivered", "painted", "holes", "received", "played", "HOLES", "missed", "diary",
    "round_trip", "seen", "samples", "action", "video_advances", "work", "drop", "errors",
    "access_ms", "outcome", "refusal", "birth", "rationale", "outcomes", "function",
    "type", "sample", "machine", "load", "sessions", "other_box", "labwc_client", "processes",
    "per_tenant", "warnings", "draw", "REMOTIX_TENANT",
    "lost", "bytes_lost", "sent", "bytes_sent", "discarded", "dgram_lost", "dgram_spurious",
    "admission_s", "block_max_ms", "categories", "work_duration_s", "end", "freq_cur_mhz", "echo_round",
    "window_start_t", "start_t", "latency_ms", "mem_total_mb", "mem_used_mb", "birth_ms",
    "birth_s", "busy_pct", "power_w", "first_frame_ms", "first_non_degenerate_s", "enclosures",
    "echo_delays_ms", "delays_ms", "skip", "sessions_during", "vram_used_mb", "overtaken",
    "user-",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old level in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


def spellings(word):
    """The word and its old spellings, for names on disk (folder prefixes)."""
    return (word,) + tuple(a for a, b in OLD_SPELLING.items() if b == word)


def dirs_users(cart):
    """The user-NN folders of a level, in the code's spelling and in the old one."""
    return sorted(p for w in spellings("user-") for p in glob.glob(os.path.join(cart, w + "*")))

# ⛔ §9, FROZEN.  (direction, green, degraded, half, unit).
#   direction "su": the good value is low (GREEN if <= green; DEGRADED if <= degraded)
#   direction "down": the good value is high (GREEN if >= green; DEGRADED if >= degraded)
#   The video bands are in fractions of f.
THRESHOLDS = {
    "delay_p95_ms":  ("su", 50.0, 150.0, 100.0, "ms"),
    "skipped_pct":     ("su", 2.0, 10.0, 6.0, "%"),
    "block_max_s":    ("su", 1.0, 3.0, 2.0, "s"),
    "holes_per_min":    ("su", 0.0, 1.0, 0.5, "/min"),
    "video_fraction_f": ("giu", 0.8, 0.4, 0.6, "·f"),
    "audio_audible_pct": ("giu", 99.0, 95.0, 97.0, "%"),
    "birth_s":       ("su", 5.0, 15.0, 10.0, "s"),
    "memoria_crescita_pct": ("su", 5.0, 15.0, 10.0, "%"),
}
ENTRY_NAMES = {
    "delay_p95_ms": "input → frame delay (p95)",
    "skipped_pct": "skipped frames",
    "block_max_s": "longest freeze of the image",
    "holes_per_min": "holes in the video chain",
    "video_fraction_f": "video: painted per second",
    "audio_audible_pct": "audible audio",
    "birth_s": "birth (access → first frame)",
    "short_check": "short functional check",
    "drop": "drop, restart, error that disconnects",
    "memoria_crescita_pct": "memory growth",
}

# the server log rows that say «this session has dropped»
# ⚠ BOTH forms: the logs of the running campaign are written by the OLD (Italian)
#   binary, the new binary writes them in English (english-migration/strings).
DROPS = [
    (re.compile(r"\[(c[0-9a-z]+)\].*la sessione e' finita"), "the session is over (§4.2)"),
    (re.compile(r"\[(c[0-9a-z]+)\].*the session is over"), "the session is over (§4.2)"),
    (re.compile(r"il palco di «(c[0-9a-z]+)».*se n'e' andato"), "the stage has gone"),
    (re.compile(r"the stage of «(c[0-9a-z]+)».*has gone"), "the stage has gone"),
    (re.compile(r"il figlio di «(c[0-9a-z]+)».*se ne va"), "the child is leaving"),
    (re.compile(r"the child of «(c[0-9a-z]+)».*is leaving"), "the child is leaving"),
    (re.compile(r"\[(c[0-9a-z]+)\].*(?:ERRORE_PROTOCOLLO|PROTOCOL_ERROR|errore di protocollo|protocol error)", re.I),
     "protocol error"),
    (re.compile(r"\[(c[0-9a-z]+)\].*(?:SFRATTO per silenzio|EVICTION for silence)"), "eviction for silence (§5.3)"),
]
RESTART = re.compile(r"^\d\d:\d\d:\d\d(?:\.\d+)?\s+(?:avvio|startup)\s+REMOTIX\b")  # old and new area name
# ⚠ not just «rifiut»: `[M]` 25 Sep the child writes «FIFO NON OTTENUTO … rifiut…» at
#   every birth, and it is not a refusal of access.  They are the three doors of rcp.c/webtransport.c
#   (old Italian form and new English form).
REFUSAL = re.compile(r"(?:\[(c[0-9a-z]+)\]|«(c[0-9a-z]+)»).*(?:posto NEGATO|attacco NEGATO|"
                     r"sessione WebTransport RIFIUTATA|slot DENIED|attach DENIED|WebTransport session REFUSED)")
OURS = re.compile(r"\[(c[0-9a-z]+)\] ⭐ (?:NOSTRO nel secondo|OURS in the second) \([^)]*\): p95 ([\d.]+) ms · "
                    r"max ([\d.]+) · (?:mediana|median) ([\d.]+) · (\d+) (?:fotogrammi|frames)")
PRODUCER = re.compile(r"(?:produttore|producer) ([\d.]+) \(max ([\d.]+)\)")
NETWORK = re.compile(r"\[(c[0-9a-z]+)\] (?:rete-quic|quic-net) (\S+) (.*)$")   # old and new binary
STRETCH = re.compile(r"\[(c[0-9a-z]+)\] ⭐ (?:TRATTO cattura → byte fuori|STRETCH capture → byte out): "
                    r"(?:mediana|median) ([\d.]+) ms \(max ([\d.]+)\)")


# ─────────────────────────────── judgement of an entry ─────────────────────
def judge(entry, value, f=None):
    """→ (class, significant).  `value` None does not get here."""
    which_way, g, d, meta, _ = THRESHOLDS[entry]
    if entry == "video_fraction_f":
        value = value                        # already in fractions of f
    if which_way == "su":
        if value <= g:
            return "GREEN", False
        if value <= d:
            return "DEGRADED", value > meta
        return "FAIL", True
    if value >= g:
        return "GREEN", False
    if value >= d:
        return "DEGRADED", value < meta
    return "FAIL", True


def measured_entry(entry, value, note="", extra=None):
    c, s = judge(entry, value)
    v = {"value": _round(value), "class": c, "significant": s, "note": note}
    v.update(extra or {})
    return v


def not_measured(why):
    return {"value": None, "class": "DEGRADED", "significant": True,
            "not_measured": True, "note": "NOT MEASURED: " + why}


def failed(value, why):
    return {"value": value, "class": "FAIL", "significant": True, "note": why}


def green(value, note):
    return {"value": value, "class": "GREEN", "significant": False, "note": note}


def _round(x):
    return round(x, 3) if isinstance(x, float) else x


def p95(v):
    if not v:
        return None
    a = sorted(v)
    return a[max(0, math.ceil(0.95 * len(a)) - 1)]


# ─────────────────────────────── reading ───────────────────────────────────
# the files of a level before the English rename (misure/ is never rewritten): their old names
_OLD_FILES = {"state.jsonl": "stato.jsonl", "birth.json": "nascita.json", "level.json": "livello.json",
              "resources.jsonl": "risorse.jsonl", "short-check.json": "controllo-corto.json"}


def on_disk(p):
    """`p`, or the same file under its old name when only that one is on disk."""
    old = _OLD_FILES.get(os.path.basename(p))
    q = os.path.join(os.path.dirname(p), old) if old else p
    return q if old and not os.path.exists(p) and os.path.exists(q) else p


def jsonl(p):
    p = on_disk(p)
    out = []
    if not os.path.exists(p):
        return out
    for x in open(p, encoding="utf-8", errors="replace"):
        x = x.strip()
        if x:
            try:
                out.append(current_spelling(json.loads(x)))
            except ValueError:
                pass
    return out


def jfile(p):
    try:
        with open(on_disk(p), encoding="utf-8") as f:
            return current_spelling(json.load(f))
    except (OSError, ValueError):
        return None


# the page's diary line: ⚠ BOTH forms, the old (Italian) page of the recorded campaigns and the new one
_DIARY_RX = (
    r"audio: (?:ricevuti|got_n|received) (\d+)", r"\b(?:suonati|played) (\d+)", r"\b(?:BUCHI|HOLES) (\d+)",
    r"\b(?:mancati|missed) (\d+)", r"\b(?:dipinti|painted) (\d+)", r"\b(?:salt|skip) (\d+)",
    r"\b(?:buchi|holes) (\d+)", r"\b(?:tard|overtaken) (\d+)",
)  # end of the diary forms
DIARY = dict(zip(("received", "played", "HOLES", "missed", "painted", "skip", "holes", "overtaken"), _DIARY_RX))


def counts_of(line):
    c = dict(line.get("counts") or {})
    d = line.get("diary")
    if d:
        for k, rx in DIARY.items():
            if k not in c:
                m = re.search(rx, d)
                if m:
                    c[k] = int(m.group(1))
        m = re.search(r"\bvideo (\d+)→(\d+)", d)
        if m and "delivered" not in c:
            c["delivered"] = int(m.group(1))
            c.setdefault("painted", int(m.group(2)))
    return c


def round_samples(fin, key, key_list):
    """The NEW samples in the window: `key` = {visti, campioni} (the last
    200 of the page: the new ones are the last `visti − visti_prima`), or
    `key_list` = [only the new samples since the last row]."""
    camp, pv = [], None
    for r in fin:
        g = r.get(key)
        if isinstance(g, dict) and g.get("samples") is not None:
            vi = g.get("seen", 0)
            if pv is not None and r is not fin[0]:
                newcomers = max(0, vi - pv)
                camp += list(g["samples"])[-newcomers:] if newcomers else []
            pv = vi
        elif isinstance(g, list) and r is not fin[0]:
            camp += list(g)
        elif r.get(key_list) is not None and r is not fin[0]:
            camp += list(r[key_list])
    return camp


def delta(lines, key):
    """Growth of a cumulative counter along the rows; those restarted from zero
    are summed piecewise and COUNTED (restarts)."""
    tot, restarts, before, observed = 0, 0, None, False
    for r in lines:
        v = r["_c"].get(key)
        if v is None:
            continue
        observed = True
        if before is not None:
            if v >= before:
                tot += v - before
            else:
                restarts += 1
                tot += v
        before = v
    return (tot if observed else None), restarts


# ─────────────────────────────── one session ───────────────────────────────
NOT_MEASURED_XRDP = ("skipped_pct", "holes_per_min", "audio_audible_pct")


def xrdp_delay_entry(inside, lines, prof, measures, t_liv=None):
    """xrdp: the delay from the viewer's side (impulse → first XDamage draw).
    → entry, or None if the entry does not apply (profile D without impulses)."""
    camp = [x for r in inside for x in (r.get("delays_ms") or [])]
    echo = [x for r in inside for x in (r.get("echo_delays_ms") or [])]
    dove = "window"
    if len(camp) < 5:
        all_of = [r for r in lines if t_liv is None or t_liv[0] - 1 <= r.get("t", 0) <= t_liv[1] + 1]
        camp2 = [x for r in all_of for x in (r.get("delays_ms") or [])]
        if len(camp2) > len(camp):
            camp, dove = camp2, "the whole level (%d samples in the window)" % len(camp)
            echo = [x for r in all_of for x in (r.get("echo_delays_ms") or [])]
    measures["xrdp_ritardi"] = {"samples": len(camp), "p95_ms": _round(p95(camp)) if camp else None,
                              "median_ms": _round(sorted(camp)[len(camp) // 2]) if camp else None,
                              "eco_campioni": len(echo), "eco_p95_ms": _round(p95(echo)) if echo else None,
                              "su": dove}
    if not camp:
        if prof == "D":
            measures["ritardo_non_si_applica"] = "profile D: no impulse"
            return None
        return not_measured("no impulse closed by an XDamage draw (empty `ritardi_ms` rows)")
    v = p95(camp)
    measures["delay_p95_ms"] = _round(v)
    return measured_entry("delay_p95_ms", v, "xrdp, VIEWER'S SIDE: p95 of %d waits impulse → first "
                         "XDamage draw (%s); echo %s ms over %d" % (
                             len(camp), dove, _round(p95(echo)) if echo else "—", len(echo)))


def session(dir_u, w0, w1, f_video, meta_u, new, corto, log_events, tratto, network=None, stretches=None,
             desktop=None, t_liv=None, system=None):
    """`new`: True/False from the list of level.json; None if the list is not
    there (then the birth is judged only if `access_ms` falls in `t_liv`)."""
    lines = jsonl(os.path.join(dir_u, "state.jsonl"))
    for r in lines:
        r["_c"] = counts_of(r)
    num = int(re.sub(r"\D", "", os.path.basename(dir_u)) or 0)
    prof = (meta_u or {}).get("profile") or next((r.get("profile") for r in lines if r.get("profile")), None)
    info = {"user": num, "profile": prof,
            "browser": (meta_u or {}).get("browser") or next((r.get("browser") for r in lines if r.get("browser")), None),
            "version": (meta_u or {}).get("version") or next((r.get("version") for r in lines if r.get("version")), None),
            "tenant": next((r.get("tenant") for r in lines if r.get("tenant")), (meta_u or {}).get("tenant"))}
    entries, measures = {}, {}
    # the window: the base row is the last one before w0 (the counters are cumulative)
    before = [r for r in lines if r.get("t", 0) <= w0]
    inside = [r for r in lines if w0 < r.get("t", 0) <= w1]
    fin = ([before[-1]] if before else []) + inside
    d_video = prof == "D"
    if len(fin) < 2:
        why = "no state row in the window (the actor does not write, or is dead)"
        for v in ("delay_p95_ms", "skipped_pct", "block_max_s", "holes_per_min"):
            entries[v] = not_measured(why)
        if d_video:
            entries["video_fraction_f"] = not_measured(why)
            entries["audio_audible_pct"] = not_measured(why)
        if system == "xrdp" and prof == "D":
            entries.pop("delay_p95_ms", None)
    else:
        dt = fin[-1]["t"] - fin[0]["t"]
        measures["window_s"] = round(dt, 1)
        cons, r1 = delta(fin, "delivered")
        dip, r2 = delta(fin, "painted")
        restarts = max(r1, r2)
        # ── input → frame delay: the PRODUCT's piece ──
        # ⛔ 26 Sep 2026, from the coordinator, on a measured diagnosis (fase16/
        #   diagnosi-eco): giro_eco = ours (input ~5–9 ms + frame in
        #   hand → page ~14 ms) + NOT ours (the app that draws the echo, the
        #   compositor).  §9 classifies «(product, p95)», §7 «what the
        #   product measures from its side» ⇒ CLASSIFIES: p95 of the `max` of the child's
        #   STRETCH rows in the window + 9 ms (the constructive cap of the
        #   input stretch).  giro_eco and the whole round_trip are recorded as
        #   EXPERIENCE and do not classify.
        all_items = round_samples(fin, "round_trip", "giro_ms")
        echo = round_samples(fin, "echo_round", "giro_eco_ms")
        measures["esperienza"] = {
            "echo_round_p95_ms": _round(p95(echo)) if echo else None, "echo_round_samples": len(echo),
            "all_round_p95_ms": _round(p95(all_items)) if all_items else None, "all_round_samples": len(all_items)}
        all_ver = [x for r in inside for x in (r.get("input") or [])]
        # ⚠ «video_avanza» (profile D) is not an input: the video in the scene
        #   stuck goes to the video entry, not to the delay
        vid_stopped = [x for x in all_ver if x.get("action") == "video_advances" and x.get("ok") is False]
        inp = [x for x in all_ver if x.get("action") != "video_advances"]
        lost = [x for x in inp if x.get("ok") is False]
        measures["video_not_advancing"] = len(vid_stopped)
        lat = [x["latency_ms"] for x in inp if x.get("ok") and x.get("latency_ms") is not None]
        measures["input_actions"] = len(inp)
        measures["input_lost"] = len(lost)
        measures["input_latency_p95_ms"] = _round(p95(lat)) if lat else None
        if system == "xrdp":
            vr = xrdp_delay_entry(inside, lines, prof, measures, t_liv)
        else:
            vr = delay_entry(info["tenant"], stretches, desktop, measures)
        delay = vr["value"] if vr else None
        if lost:
            entries["delay_p95_ms"] = failed(_round(delay), "input LOST: %d actions of %d without effect (%s)"
                                             % (len(lost), len(inp),
                                                ", ".join(str(x.get("action")) for x in lost[:3])))
        elif vr:
            entries["delay_p95_ms"] = vr
        elif system == "xrdp":
            pass                               # profile D without impulses: does not apply
        else:
            entries["delay_p95_ms"] = not_measured("no «OURS in the second» row of the child for %s in the "
                                                  "window (binary before ebc9dcd? the STRETCH rows are "
                                                  "recorded and do not classify)"
                                                  % (info["tenant"] or "the unknown tenant"))
        # ── skipped ──
        if cons is None or dip is None:
            entries["skipped_pct"] = not_measured("the page did not give `video X→Y`")
        elif cons == 0:
            entries["skipped_pct"] = not_measured("no frame delivered in the window")
        else:
            v = max(0.0, 100.0 * (cons - dip) / cons)
            sa, _ = delta(fin, "skip")
            measures.update(delivered=cons, painted=dip, salt=sa, skipped_pct=_round(v))
            entries["skipped_pct"] = measured_entry("skipped_pct", v, "%d delivered, %d painted (salt %s)"
                                                % (cons, dip, sa))
        # ── freeze ──
        # ⚠ `work: false` (for D: before the video starts) does NOT count, neither here
        #   nor for the painted per second: only the work intervals are looked at.
        bm = [r["block_max_ms"] for r in inside
              if r.get("block_max_ms") is not None and r.get("work", True) is not False]
        stills, dip_lav, dt_lav = 0, 0, 0.0
        for a, b in zip(fin, fin[1:]):
            da, db = a["_c"].get("painted"), b["_c"].get("painted")
            lav = b.get("work", True) is not False
            if da is not None and db is not None and lav:
                dip_lav += max(0, db - da) if db >= da else db
                dt_lav += b["t"] - a["t"]
                if db == da:
                    stills += 1
        measures["work_s"] = round(dt_lav, 1)
        if dip_lav == 0 and dt_lav > 0 and dip is not None:
            entries["block_max_s"] = failed(round(dt_lav, 1), "STILL IMAGE: no frame painted "
                                           "in %.0f s of work" % dt_lav)
        elif bm:
            v = max(bm) / 1000.0
            measures["block_max_s"] = _round(v)
            entries["block_max_s"] = measured_entry("block_max_s", v, "from the actor (%d rows)" % len(bm))
            if stills:
                entries["block_max_s"] = failed(max(v, 5.0), "%d intervals of 5 s without frames "
                                               "with work in progress" % stills)
        elif stills:
            entries["block_max_s"] = failed(5.0, "%d intervals of 5 s without any frame "
                                           "painted with work in progress ⇒ freeze >= 5 s" % stills)
        else:
            entries["block_max_s"] = not_measured("`blocco_max_ms` is missing and the 5 s counters do not "
                                                "see below 5 s")
        # ── holes ──
        bu, _ = delta(fin, "holes")
        if bu is None:
            entries["holes_per_min"] = not_measured("the page did not give `holes`")
        else:
            v = bu / (dt / 60.0) if dt > 0 else 0.0
            measures["holes"] = bu
            entries["holes_per_min"] = measured_entry("holes_per_min", v, "%d holes in %.0f s" % (bu, dt))
        # ── video and audio (profile D) ──
        if d_video:
            if dip is None:
                entries["video_fraction_f"] = not_measured("the page did not give `painted`")
            elif not f_video:
                entries["video_fraction_f"] = not_measured("f, the frame rate of the video, is missing (--fps-video)")
            elif dt_lav <= 0:
                entries["video_fraction_f"] = not_measured("no work interval in the window "
                                                        "(did the video not start?)")
            else:
                fps = dip_lav / dt_lav
                measures["video_fps"] = _round(fps)
                entries["video_fraction_f"] = measured_entry("video_fraction_f", fps / f_video,
                                                         "%.1f painted/s in %.0f s of video, f = %s"
                                                         % (fps, dt_lav, f_video))
            su, _ = delta(fin, "played")
            ri, _ = delta(fin, "received")
            ma, _ = delta(fin, "missed")
            if su is None or ri is None:
                entries["audio_audible_pct"] = not_measured("the page did not give `played`/`received`")
            else:
                den = ri + (ma or 0)
                v = 100.0 * su / den if den else 0.0
                measures["audio_audible_pct"] = _round(v)
                entries["audio_audible_pct"] = measured_entry(
                    "audio_audible_pct", min(v, 100.0),
                    "%d played of %d sent (%d received + %d missed)" % (su, den, ri, ma or 0)
                    if den else "NO audio block in the window while the video plays")
            if vid_stopped:
                vv = entries.get("video_fraction_f")
                if not vv or vv["class"] == "GREEN":
                    entries["video_fraction_f"] = {
                        "value": (vv or {}).get("value"), "class": "DEGRADED", "significant": True,
                        "note": "the VIDEO IN THE SCENE does not advance in %d checks of %d (%s): stuck or paused, "
                                "cause to look at%s" % (
                                    len(vid_stopped), sum(1 for x in all_ver if x.get("action") == "video_advances"),
                                    (vid_stopped[0].get("det") or "")[:80],
                                    (" · " + vv["note"]) if vv else "")}
                else:
                    vv["note"] += " · the video in the scene does not advance in %d checks" % len(vid_stopped)
        # ── drop: the state ──
        cad = [r for r in lines if r.get("drop")]
        if cad:
            entries["drop"] = failed(True, "the actor says DROP at %s: %s" % (
                _now(cad[0]["t"]), "; ".join(cad[0].get("errors") or [])[:200]))
        elif restarts:
            entries["drop"] = failed(True, "the page counters restarted from zero %d times: "
                                     "page reloaded or session reattached" % restarts)
    # the product's delay does not need the actor: without state rows
    #   it is taken anyway from the child's STRETCH rows
    if len(fin) < 2 and system != "xrdp":
        vr = delay_entry(info["tenant"], stretches, desktop, measures)
        if vr:
            entries["delay_p95_ms"] = vr
    if system == "xrdp":
        removed = [v for v in NOT_MEASURED_XRDP if v in entries]
        for v in removed:
            entries.pop(v)
        measures["non_misurati_per_costruzione"] = removed
    # ── drop: the server log (the whole level) ──
    tnt = info["tenant"]
    ev = [e for e in log_events if e["tenant"] == tnt or e["tenant"] == "*"] if tnt else \
        [e for e in log_events if e["tenant"] == "*"]
    if ev and entries.get("drop", {}).get("class") != "FAIL":
        entries["drop"] = failed(True, "server log: " + "; ".join(
            "%s %s" % (e["time"], e["what"]) for e in ev[:3]))
    elif "drop" not in entries:
        entries["drop"] = green(False, "no drop, restart or error that disconnects"
                               + ("" if tnt else " (⚠ unknown tenant: only the restart is looked at)"))
    # the network (§7), from the server log: RECORDED, does not classify
    measures["network"] = (network or {}).get(tnt) if tnt else None
    if tnt and tratto.get(tnt):
        measures["stretch_server_ms"] = tratto[tnt]
    # ── birth ──
    na = jfile(os.path.join(dir_u, "birth.json"))
    if na is not None and new is not True:
        # ⛔ born in this level?  With the list: only if `new`.  Without:
        #   only if the access falls inside the level.
        acc = na.get("access_ms")
        inside_level = (new is None and acc is not None and t_liv is not None
                      and t_liv[0] - 1 <= acc / 1000.0 <= t_liv[1])
        if not inside_level:
            measures["nascita_precedente"] = {
                "birth_s": round(na["birth_ms"] / 1000.0, 2) if na.get("birth_ms") is not None else
                (round((na["first_frame_ms"] - acc) / 1000.0, 2)
                 if acc is not None and na.get("first_frame_ms") is not None else None),
                "outcome": na.get("outcome"),
                "note": "birth from an earlier rung: recorded, does not classify"}
            na = None
    if na is not None:
        es = str(na.get("outcome", "ok")).lower()
        ms = na.get("birth_ms")
        if ms is None and na.get("access_ms") is not None and na.get("first_frame_ms") is not None:
            ms = na["first_frame_ms"] - na["access_ms"]
        if "rifiut" in es or "refus" in es:     # the old outcome «refusal», and the new one
            entries["birth_s"] = failed(None, "REFUSAL at access")
        elif ms is None:
            entries["birth_s"] = failed(None, "no first frame (outcome %s)" % es) if es != "ok" \
                else not_measured("birth.json without times")
        else:
            measures["birth_s"] = round(ms / 1000.0, 2)
            entries["birth_s"] = measured_entry("birth_s", ms / 1000.0, "access → first frame")
            if es not in ("ok", "pass"):
                entries["birth_s"] = failed(measures["birth_s"], "outcome %s" % es)
    elif new:
        entries["birth_s"] = not_measured("user born in the level without birth.json")
    ref = [e for e in log_events if e.get("refusal") and e["tenant"] == tnt] if tnt else []
    if ref:
        entries["birth_s"] = failed(None, "refusal in the server log: " + ref[0]["line"][:160])
    # ── short check ──
    if corto and int(corto.get("user", -1)) == num:
        entries["short_check"] = entry_short(corto)
    return info, measures, entries


def entry_birth_check(na):
    """`birth` of short-check.json: {pagina_s, ammissione_s, nascita_s
    (access → first frame painted), primo_non_degenere_s, rifiuto, esito,
    ragione}.  §9: <= 5 s GREEN, 5–15 DEGRADED, > 15 or refusal FAIL."""
    if not na:
        return not_measured("short-check.json without `birth`")
    if na.get("refusal"):
        return failed(None, "REFUSAL at access: %s" % (na.get("rationale") or "")[:160])
    if na.get("birth_s") is None:
        if str(na.get("outcome", "")).upper() == "FAIL":
            return failed(None, "the check session was not born: %s" % (na.get("rationale") or "")[:160])
        return not_measured("`birth` without nascita_s")
    v = measured_entry("birth_s", float(na["birth_s"]), "access → first frame painted, at full load"
                      + (" (not degenerate at %s s)" % na["first_non_degenerate_s"]
                         if na.get("first_non_degenerate_s") is not None else ""))
    if str(na.get("outcome", "PASS")).upper() == "FAIL":
        v = failed(v["value"], "the first frame: %s" % (na.get("rationale") or "")[:160])
    return v


def session_check(cart, corto, log_events):
    tnt = corto.get("tenant")
    info = {"user": int(corto.get("user", 99)), "profile": "check", "browser": corto.get("browser"),
            "version": corto.get("version"), "tenant": tnt}
    na = corto.get("birth") or {}
    measures = {"birth_s": na.get("birth_s"), "admission_s": na.get("admission_s"),
              "first_non_degenerate_s": na.get("first_non_degenerate_s"),
              "sessions_during": corto.get("sessions_during")}
    entries = {"birth_s": entry_birth_check(na), "short_check": entry_short(corto)}
    ref = [e for e in log_events if e.get("refusal") and tnt and e["tenant"] == tnt]
    if ref:
        entries["birth_s"] = failed(None, "refusal in the server log: " + ref[0]["line"][:160])
    return (os.path.join(cart, "short-check"), info, measures, entries)


def entry_short(corto):
    es = corto.get("outcomes") or {}
    if isinstance(es, list):
        es = {x.get("function"): x.get("outcome") for x in es}
    if not es:
        return not_measured("short-check.json without outcomes")
    f = [k for k, v in es.items() if v == "FAIL"]
    b = [k for k, v in es.items() if v not in ("PASS", "FAIL")]
    if f:
        return failed(es, "FAIL: " + ", ".join(f))
    if b:
        r = not_measured("not looked at: " + ", ".join(b))
        r["value"] = es
        return r
    return green(es, "all PASS (%s)" % ", ".join(sorted(es)))


def _now(t):
    return _dt.datetime.fromtimestamp(t).strftime("%H:%M:%S")


def class_of(entries):
    c = "GREEN"
    for v in entries.values():
        if ORDER[v["class"]] > ORDER[c]:
            c = v["class"]
    return c


def reason_of(entries):
    ugly = sorted(((k, v) for k, v in entries.items() if v["class"] != "GREEN"),
                    key=lambda kv: -ORDER[kv[1]["class"]])
    if not ugly:
        return "all entries GREEN"
    return " · ".join("%s %s: %s%s" % (v["class"], ENTRY_NAMES.get(k, k),
                                        "" if v.get("value") is None or isinstance(v["value"], (dict, bool))
                                        else "%s — " % v["value"], v.get("note", ""))
                      for k, v in ugly)


# ─────────────────────────────── the server log ────────────────────────────
def epoch_log(time, t_ref, merged):
    """«HH:MM:SS.mmm» of the log (server time, `merged` hours from UTC; the
    box is in UTC) → epoch, with the day nearest to `t_ref`."""
    m = re.match(r"(\d\d):(\d\d):(\d\d(?:\.\d+)?)", time)
    if not m or not t_ref:
        return None
    base = _dt.datetime.fromtimestamp(t_ref, _dt.timezone.utc) + _dt.timedelta(hours=merged)
    t = base.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
    t = t.timestamp() - merged * 3600 + float(m.group(3))
    for g in (-86400, 86400):
        if abs(t + g - t_ref) < abs(t - t_ref):
            t += g
    return t


def events_log(p, t_ref, merged=0.0):
    """The rows that matter, with the time.  ⚠ Those AFTER the end of the level
    (`t_ref`) do not count: the end-of-level clean-up closes the sessions, and
    «the session is over» there is the farewell, not a drop."""
    ev, tratto = [], {}
    if not p or not os.path.exists(p):
        return ev, tratto, False
    for line in open(p, encoding="utf-8", errors="replace"):
        line = line.rstrip("\n")
        time = line[:12]
        te = epoch_log(time, t_ref, merged)
        if te is not None and te > t_ref + 2:
            continue
        if RESTART.search(line):
            ev.append({"tenant": "*", "time": time, "what": "server RESTART (avvio REMOTIX)", "line": line})
            continue
        for rx, what in DROPS:
            m = rx.search(line)
            if m:
                ev.append({"tenant": m.group(1), "time": time, "what": what, "line": line})
                break
        m = REFUSAL.search(line)
        if m and "refusal" not in (e.get("what") for e in ev[-1:]):
            ev.append({"tenant": m.group(1) or m.group(2), "time": time, "what": "refusal",
                       "refusal": True, "line": line})
        m = STRETCH.search(line)
        if m:
            tratto[m.group(1)] = {"median": float(m.group(2)), "max": float(m.group(3)), "time": time}
    return ev, tratto, True


CAP_INGRESS_MS = 9.0   # the input stretch: the child's 8 ms poll (child.c:3794) + 1


def stretches_log(p, w0, w1, merged=0.0):
    """Two series of the child in the window, per tenant:
    `our`  «⭐ OURS in the second (copy → byte out, §3.2): p95 X ms · max Y ·
              median Z · N frames» (commit ebc9dcd; old form «⭐ NOSTRO nel secondo …»):
              ONLY the frames of that second, WITHOUT the compositor's «producer» ⇒ CLASSIFIES;
    `tratto`  «⭐ STRETCH capture → byte out: median X (max Y) …» (old form «⭐ TRATTO
              cattura → byte fuori …»): ⚠ the `max`
              is from the ROLLING SAMPLE of 512 frames (not of the second) and the
              producer is inside it ⇒ only RECORDED (it serves to explain)."""
    out = {"ours": {}, "stretch": {}}
    if not p or not os.path.exists(p):
        return out
    for line in open(p, encoding="utf-8", errors="replace"):
        if ("NOSTRO nel secondo" not in line and "TRATTO cattura" not in line
                and "OURS in the second" not in line and "STRETCH capture" not in line):
            continue
        te = epoch_log(line[:12], w1, merged)
        if te is None or te <= w0 or te > w1 + 2:
            continue
        m = OURS.search(line)
        if m:
            out["ours"].setdefault(m.group(1), []).append(
                (te, float(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(5))))
            continue
        m = STRETCH.search(line)
        if m:
            pr = PRODUCER.search(line)
            out["stretch"].setdefault(m.group(1), []).append(
                (te, float(m.group(2)), float(m.group(3)), float(pr.group(1)) if pr else None))
    return out


def delay_entry(tnt, stretches, desktop, measures):
    """The entry of the PRODUCT's delay and the recorded measures.  → entry or None."""
    stretches = stretches or {"ours": {}, "stretch": {}}
    no = stretches["ours"].get(tnt) or [] if tnt else []
    tr = stretches["stretch"].get(tnt) or [] if tnt else []
    if tr:
        pm = [x[3] for x in tr if x[3] is not None]
        measures["stretch"] = {"lines": len(tr), "median_p95_ms": _round(p95([x[1] for x in tr])),
                            "max_sample_p95_ms": _round(p95([x[2] for x in tr])),
                            "producer_median_ms": _round(sorted(pm)[len(pm) // 2]) if pm else None}
    if not no:
        return None
    p95s = [x[1] for x in no]
    delay = p95(p95s) + CAP_INGRESS_MS
    measures["delay_p95_ms"] = _round(delay)
    measures["ours"] = {"lines": len(no), "p95_of_p95_ms": _round(p95(p95s)),
                        "max_per_second_max_ms": _round(max(x[2] for x in no)),
                        "max_per_second_p95_ms": _round(p95([x[2] for x in no])),
                        "median_ms": _round(sorted(x[3] for x in no)[len(no) // 2]),
                        "frames": sum(x[4] for x in no)}
    note = ("p95 of the per-second p95s of «OURS» (copy → byte out, %d rows of the child) %.1f ms + %.0f ms "
            "of input (constructive cap: 8 ms poll)" % (len(no), p95(p95s), CAP_INGRESS_MS))
    if (desktop or "").lower() in ("xfce", "lxqt"):
        note += (" · ⚠ wlroots path: the «copy» is counted twice (~4 ms more, capture.c:2309 / "
                 "child.c:5191) — NOT corrected, it is on the cautious side")
    return measured_entry("delay_p95_ms", delay, note)


NETWORK_CUM = ("lost", "bytes_lost", "sent", "bytes_sent", "received", "discarded",
            "dgram_lost", "dgram_ok", "dgram_spurious")


def network_log(p, w0, w1, merged=0.0):
    """§7, the network per session: the server's `quic-net` rows (one per second per
    connection, CUMULATIVE counters of the connection) in the window ⇒ per
    tenant the Δs (summed over the connections: a re-entry opens a new
    connection and the counters restart), the loss %, the rate, and srtt/pto.
    ⚠ QUIC does not write a «retransmissions» counter: the `persi` packets are
    those that ngtcp2 declared lost, and their content is retransmitted ⇒
    `persi`/`bytes_lost` ARE the measure of retransmissions.  Recorded, does not
    classify."""
    if not p or not os.path.exists(p):
        return {}
    conn = {}                                  # (inq, address) → [first, last, srtt[], pto[]]
    for line in open(p, encoding="utf-8", errors="replace"):
        if "rete-quic" not in line and "quic-net" not in line:      # old and new binary
            continue
        m = NETWORK.search(line.rstrip("\n"))
        if not m:
            continue
        te = epoch_log(line[:12], w1, merged)
        if te is None or te <= w0 or te > w1 + 2:
            continue
        kv = {}
        for k, v in re.findall(r"(\w+)=(-?\d+)", m.group(3)):
            # the old binary's counters in the code's spelling (`lost_d`: the stem, then `_d`)
            k = current_spelling(k[:-2]) + "_d" if k.endswith("_d") else current_spelling(k)
            kv[k] = int(v)
        c = conn.setdefault((m.group(1), m.group(2)), [kv, kv, [], [], te, te])
        c[1] = kv
        c[5] = te
        if "srtt_us" in kv:
            c[2].append(kv["srtt_us"] / 1000.0)
        if "pto_us" in kv:
            c[3].append(kv["pto_us"] / 1000.0)
    out = {}
    for (tnt, _), (a, b, srtt, pto, t0, t1) in conn.items():
        r = out.setdefault(tnt, {k: 0 for k in NETWORK_CUM})
        r.setdefault("connections", 0)
        r["connections"] += 1
        r.setdefault("_srtt", []).extend(srtt)
        r.setdefault("_pto", []).extend(pto)
        r["_s"] = r.get("_s", 0) + max(0.0, t1 - t0) + 1.0   # the first row already covers since_ms
        for k in NETWORK_CUM:
            # the first row of the window is the base, but its `_d` are inside
            base = a.get(k, 0) - a.get(k + "_d", 0) if (k + "_d") in a else a.get(k, 0)
            r[k] += max(0, b.get(k, 0) - base)
    for tnt, r in out.items():
        sr, pt, dur = r.pop("_srtt"), r.pop("_pto"), r.pop("_s")
        r["loss_pct"] = round(100.0 * r["lost"] / r["sent"], 3) if r["sent"] else None
        r["mbit_s"] = round(r["bytes_sent"] * 8 / 1e6 / dur, 2) if dur else None
        r["srtt_ms"] = {"median": round(sorted(sr)[len(sr) // 2], 2), "max": round(max(sr), 2)} if sr else None
        r["pto_ms_max"] = round(max(pt), 1) if pt else None
        r["seconds"] = round(dur)
    return out


def journal_err(cart, t0, t1, box=None):
    """The rows at priority <= 3 (err) of the box's journal in the level — since
    `--journal` exists (26 Sep 2026) the product sends the EVENTS there, with
    REMOTIX_TENANT.  Source: `journal-err.jsonl` in the level folder
    (the output of `journalctl -t remotix -p err -o json`), or, with --box-journal,
    it is asked of the box now (needs root).  RECORDED, does not classify.
    ⚠ The complete log stays registro.log: it is the source of the classifier."""
    p = os.path.join(cart, "journal-err.jsonl")
    lines, source = None, None
    if os.path.exists(p):
        lines, source = open(p, encoding="utf-8", errors="replace").read().splitlines(), p
    elif box:
        import subprocess
        cmd = ["podman", "exec", "rete11-" + box, "journalctl", "-t", "remotix", "-p", "err",
               "--since", "@%d" % int(t0), "--until", "@%d" % int(t1 + 1), "-o", "json", "--no-pager"]
        try:
            o = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            lines, source = o.stdout.splitlines(), " ".join(cmd)
            with open(p, "w", encoding="utf-8") as f:      # the evidence stays in the level
                f.write(o.stdout)
        except (OSError, subprocess.SubprocessError) as e:
            return {"lines": None, "note": "journal not read: %s" % e}
    if lines is None:
        return None
    per, examples, n = {}, [], 0
    for x in lines:
        x = x.strip()
        if not x:
            continue
        try:
            j = current_spelling(json.loads(x))
            msg, tnt, pr = j.get("MESSAGE"), j.get("REMOTIX_TENANT"), j.get("PRIORITY")
            if pr is not None and int(pr) > 3:
                continue
            if isinstance(msg, list):                       # journalctl: non-UTF-8 bytes
                msg = bytes(msg).decode("utf-8", "replace")
        except ValueError:
            msg, tnt = x, None                              # `-o cat`: one row, no fields
            m = re.search(r"\[(c[0-9a-z]+)\]", x)
            tnt = m.group(1) if m else None
        n += 1
        if tnt:
            per[tnt] = per.get(tnt, 0) + 1
        if len(examples) < 5:
            examples.append(str(msg)[:200])
    return {"lines": n, "per_tenant": per, "examples": examples, "source": source}


# ─────────────────────────────── the resources ─────────────────────────────
def resources(p, w0, w1):
    lines = [r for r in jsonl(p) if r.get("type") == "sample"]
    all_of = lines
    fin = [r for r in lines if w0 < r.get("t", 0) <= w1]
    if not fin:
        return None, all_of

    def serial(f):
        out = []
        for r in fin:
            try:
                v = f(r)
            except (KeyError, TypeError):
                v = None
            if v is not None:
                out.append(v)
        return out

    def sum_of(v):
        if not v:
            return None
        return {"mean": round(sum(v) / len(v), 2), "p95": round(p95(v), 2), "max": round(max(v), 2)}
    s = {"samples": len(fin),
         "cpu_machine_pct": sum_of(serial(lambda r: r["machine"]["cpu_pct"])),
         "load_1m": sum_of(serial(lambda r: r["machine"]["load"][0])),
         "mem_used_mb": sum_of(serial(lambda r: r["machine"]["mem_used_mb"])),
         "mem_total_mb": fin[-1]["machine"].get("mem_total_mb"),
         "thread": sum_of(serial(lambda r: r["machine"]["thread"])),
         "misuratore_cpu_s": sum_of(serial(lambda r: r["misuratore"]["cpu_s"])),
         "enclosures": {}, "gpu": {}}
    for rc in ("remotix", "sessions", "browser", "other_box", "labwc_client"):
        s["enclosures"][rc] = {
            "cpu_core": sum_of(serial(lambda r: r["enclosures"][rc]["cpu_core"])),
            "pss_mb": sum_of(serial(lambda r: r["enclosures"][rc]["pss_mb"])),
            "processes": sum_of(serial(lambda r: r["enclosures"][rc]["processes"])),
            "gpu": {c: sum_of(serial(lambda r: r["enclosures"][rc]["gpu"].get(c)))
                    for c in sorted({c for r in fin for c in r["enclosures"][rc].get("gpu", {})})},
        }
    for pdev in sorted({p for r in fin for p in r.get("gpu", {})}):
        gg = {"card": fin[-1]["gpu"].get(pdev, {}).get("card"),
              "driver": fin[-1]["gpu"].get(pdev, {}).get("driver")}
        for c in sorted({c for r in fin for c in r["gpu"].get(pdev, {}).get("categories", {})}):
            gg[c] = sum_of(serial(lambda r: r["gpu"][pdev]["categories"].get(c)))
        for k in ("freq_cur_mhz", "freq_mhz", "temp_c", "power_w", "vram_used_mb", "busy_pct"):
            gg[k] = sum_of(serial(lambda r: r["gpu"][pdev].get(k)))
        throttle = {}
        for r in fin:
            for x in r["gpu"].get(pdev, {}).get("strozzatura") or []:
                throttle[x] = throttle.get(x, 0) + 1
        gg["throttling_fraction"] = {k: round(v / len(fin), 2) for k, v in throttle.items()}
        s["gpu"][pdev] = gg
    s["warnings"] = sorted({a for r in fin for a in r.get("warnings") or []})[:10]
    return s, all_of


SETTLING_S = 60.0     # after the start of work, before measuring the memory
CONTINUE_PCT_HOUR = 2.0    # «and keeps going»: slope of the second half beyond 2 %/hour of the mean...
CONTINUE_FRAC = 1.0 / 3   # ...and growth along the second half beyond 1/3 of the total


def slope(pts):
    """The least-squares slope of [(t, v)], per second."""
    n = len(pts)
    mt = sum(t for t, _ in pts) / n
    mv = sum(v for _, v in pts) / n
    den = sum((t - mt) ** 2 for t, _ in pts)
    return sum((t - mt) * (v - mv) for t, v in pts) / den if den else 0.0


def level_entries(all_results, w0, w1, m0=None, m1=None):
    """`m0`–`m1`: the memory stretch (the work of the level, see above);
    None ⇒ from the first row of resources to the last."""
    entries = {}
    fin = [r for r in all_results if (m0 is None or r.get("t", 0) >= m0) and (m1 is None or r.get("t", 0) <= m1)]
    if not fin:
        return {"remotix_memory": not_measured("no resources.jsonl row in the work of the level"),
                "sessions_memory": not_measured("no resources.jsonl row in the work of the level")}
    for rc in ("remotix", "sessions"):
        pts = [(r["t"], r["enclosures"][rc]["pss_mb"]) for r in fin
               if r.get("enclosures", {}).get(rc, {}).get("processes")]
        if len(pts) < 20 or pts[-1][0] - pts[0][0] < 60:
            entries[rc + "_memory"] = not_measured("memory series of %s too short (%d points)"
                                                 % (rc, len(pts)))
            continue
        t0, t1 = pts[0][0], pts[-1][0]
        a = [v for t, v in pts if t <= t0 + 30]
        b = [v for t, v in pts if t >= t1 - 30]
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        growth = 100.0 * (mb - ma) / ma if ma > 0 else 0.0
        tm = (t0 + t1) / 2.0
        second = [(t, v) for t, v in pts if t >= tm]
        media = sum(v for _, v in pts) / len(pts)
        k = slope(second) if len(second) >= 10 else 0.0
        k_now = 100.0 * k * 3600.0 / media if media > 0 else 0.0
        su_meta = k * (t1 - tm)
        ongoing = k_now > CONTINUE_PCT_HOUR and (mb - ma) > 0 and su_meta > CONTINUE_FRAC * (mb - ma)
        note = ("PSS %.0f → %.0f MB in %.0f s of work (%s–%s); second half %+.1f %%/hour, %+.0f MB of "
                "%+.0f%s" % (ma, mb, t1 - t0, _now(t0), _now(t1), k_now, su_meta, mb - ma,
                             " and KEEPS rising" if ongoing else ""))
        v = measured_entry("memoria_crescita_pct", growth, note,
                          {"ongoing": ongoing, "slope_pct_per_hour": _round(k_now), "stretch_s": round(t1 - t0)})
        if v["class"] == "FAIL" and not ongoing:
            # §9: FAIL is «> 15 % AND keeps going»; beyond 15 % but stopped: it is reported
            v.update(**{"class": "DEGRADED"}, significant=True,
                     note=note + " — beyond 15 % but STOPPED: reported (§9)")
        entries[rc + "_memory"] = v
    # the restart seen from the resources: the parent's pid changes (in the WHOLE level)
    pids = [r.get("remotix_pid") for r in all_results if r.get("remotix_pid")]
    empty = [r for r in all_results if r.get("enclosures", {}).get("remotix", {}).get("processes") == 0]
    if len(set(pids)) > 1:
        entries["server_restart"] = failed(sorted(set(pids)), "the pid of the remotix parent CHANGED in the "
                                         "level: %s" % " → ".join(str(p) for p in _without_repeats(pids)))
    elif empty:
        entries["server_restart"] = failed(len(empty), "remotix enclosure EMPTY in %d samples" % len(empty))
    else:
        entries["server_restart"] = green(pids[0] if pids else None, "the remotix parent is the same for "
                                       "the whole level")
    return entries


def _without_repeats(v):
    out = []
    for x in v:
        if not out or out[-1] != x:
            out.append(x)
    return out


# ─────────────────────────────── the level ─────────────────────────────────
def ranking(cart, fps_video=None, window_s=120.0, campaign=None, level=None, merged_log=0.0,
               box_journal=None, system=None):
    meta = jfile(os.path.join(cart, "level.json")) or {}
    # f: --fps-video, then level.json, then the video chosen in the plan (30 frames/s)
    fps_video = fps_video or meta.get("fps_video") or CHOSEN_VIDEO_FPS
    users_meta = {int(u["user"]): u for u in meta.get("users") or [] if "user" in u}
    dirs = dirs_users(cart)
    # the end of the level: the last row of any series
    ts = []
    for d in dirs:
        ts += [r.get("t", 0) for r in jsonl(os.path.join(d, "state.jsonl"))]
    result_p = os.path.join(cart, "resources.jsonl")
    ts_r = [r.get("t", 0) for r in jsonl(result_p) if r.get("type") == "sample"]
    w1 = meta.get("end") or max(ts + ts_r or [0])
    w0 = w1 - window_s
    result, all_results = resources(result_p, w0, w1)
    ev, tratto, c_log = events_log(os.path.join(cart, "server.log"), w1, merged_log)
    stretches = stretches_log(os.path.join(cart, "server.log"), w0, w1, merged_log)
    network = network_log(os.path.join(cart, "server.log"), w0, w1, merged_log)
    t_start = meta.get("start_t") or min(ts + ts_r or [w0])
    journal = journal_err(cart, t_start, w1, box_journal)
    corto = jfile(os.path.join(cart, "short-check.json"))
    has_list = bool(users_meta)
    sess = []
    for d in dirs:
        n = int(re.sub(r"\D", "", os.path.basename(d)) or 0)
        mu = users_meta.get(n)
        new = bool(mu.get("new")) if mu else (False if has_list else None)
        info, measures, entries = session(d, w0, w1, fps_video, mu, new,
                                      corto, ev, tratto, network, stretches, meta.get("desktop"), (t_start, w1),
                                      system)
        if journal and info.get("tenant"):
            measures["journal_err"] = journal["per_tenant"].get(info["tenant"], 0)
        sess.append((d, info, measures, entries))
    # the memory stretch: the WORK of the level (+ settling), up to the short check
    if meta.get("work_duration_s") is not None and meta.get("end"):
        m0, da = meta["end"] - meta["work_duration_s"], "start of work"
    elif meta.get("start_t"):
        m0, da = meta["start_t"], "start of the level"
    else:
        m0, da = min(ts_r or [t_start]), "first row of resources"
    born = []
    for d in dirs:
        n = int(re.sub(r"\D", "", os.path.basename(d)) or 0)
        if (users_meta.get(n) or {}).get("new"):
            na = jfile(os.path.join(d, "birth.json")) or {}
            if na.get("first_frame_ms") is not None and na["first_frame_ms"] / 1000.0 <= w1:
                born.append(na["first_frame_ms"] / 1000.0)
    if born and max(born) > m0:
        m0, da = max(born), "last birth"
    m0 += SETTLING_S
    m1 = w1
    if corto is not None and meta.get("check_min") and meta.get("end"):
        m1 = min(w1, meta["end"] - float(meta["check_min"]) * 60.0)
    # ⛔ [M] 26 Sep 00:56 (intel-4k-xfce level-01): the short check lasted 156 s and not
    #    120, the «end − controllo_min» fell 28 s AFTER the birth of session u99 ⇒
    #    +25 MB of a new tenant read as a leak (false FAIL).  The memory
    #    stretch ends before the check appears in the resources, whatever the
    #    duration of the check; and never after the start of the window declared by the climb.
    if meta.get("window_start_t"):
        m1 = min(m1, float(meta["window_start_t"]))
    for r in all_results:
        t_r = r.get("t")
        if t_r is None or t_r < m0:
            continue
        chi = set()
        for rec in (r.get("enclosures") or {}).values():
            if isinstance(rec, dict):
                chi.update((rec.get("per_tenant") or {}).keys())
        if any(str(c).endswith("u99") for c in chi):
            m1 = min(m1, t_r - 5.0)
            break
    lv = level_entries(all_results, w0, w1, m0, m1)
    for k in ("remotix_memory", "sessions_memory"):
        if not lv[k].get("not_measured"):
            lv[k]["note"] += " · from: %s + %.0f s" % (da, SETTLING_S)
    # ⛔ a rung not reached is not a rung passed
    n_declared = level if level is not None else meta.get("level")
    present = {int(re.sub(r"\D", "", os.path.basename(d)) or 0) for d in dirs}
    without_dir = sorted(set(users_meta) - present)
    if n_declared is not None:
        k_ent = len(present)
        if k_ent < int(n_declared):
            lv["entered"] = failed(k_ent, "entered %d of %d%s" % (
                k_ent, int(n_declared), (" (in the list without a folder: %s)" % without_dir) if without_dir else ""))
        else:
            lv["entered"] = green(k_ent, "entered %d of %d" % (k_ent, int(n_declared)))
    if not c_log:
        lv["server_log"] = not_measured("server.log is missing: server drops and errors not looked at")
    if corto is None:
        lv["short_check"] = not_measured("short-check.json is missing")
    elif not any("short_check" in s[3] for s in sess):
        # ⭐ the short check is a NEW SESSION of its own (16-short-check.py,
        #   user 99): it is classified as a separate session, profile «check»,
        #   with its birth at full load (§9 «birth of a new user»)
        sess.append(session_check(cart, corto, ev))
    if not sess:
        lv["sessions"] = not_measured("no user-NN folder")
    classes = [class_of(v) for _, _, _, v in sess]
    c_liv = class_of(lv)
    for c in classes:
        if ORDER[c] > ORDER[c_liv]:
            c_liv = c
    # ⚠ the quarter is counted on the ACTORS: the check (user 99) has nothing to do with it
    expect = [class_of(v) for _, i, _, v in sess if i.get("profile") != "check"]
    n_expected = len(expect)
    n_deg = sum(1 for c in expect if c == "DEGRADED")
    sig_entries = [(os.path.basename(d), k) for d, _, _, v in sess for k, x in v.items()
                if x["class"] == "DEGRADED" and x.get("significant")]
    sig_entries += [("level", k) for k, x in lv.items() if x["class"] == "DEGRADED" and x.get("significant")]
    significant = c_liv == "FAIL" or (c_liv == "DEGRADED" and (
        (n_expected and n_deg * 4 > n_expected) or bool(sig_entries)))
    return {"meta": meta, "w0": w0, "w1": w1, "fps_video": fps_video, "sessions": sess, "journal": journal,
            "voci_livello": lv, "resources": result, "class": c_liv, "significant": significant,
            "n_degradate": n_deg, "n_attori": n_expected, "sig_entries": sig_entries, "campaign": campaign or meta.get("campaign"),
            "level": level if level is not None else meta.get("level", len(sess)),
            "cart": cart, "system": system or "remotix"}


BASE = ("desktop", "card", "driver", "size", "commit", "binary", "page", "kernel",
        "session_cap", "started", "duration_s")


def log_line_list(g):
    m = g["meta"]
    base = {"campaign": g["campaign"], "level": g["level"], "system": g.get("system", "remotix")}
    for k in BASE:
        base[k] = m.get(k)
    base["window"] = [_now(g["w0"]), _now(g["w1"])] if g["w1"] else None
    base["fps_video"] = g["fps_video"]
    out = []
    counts = {"GREEN": 0, "DEGRADED": 0, "FAIL": 0}
    for d, info, measures, entries in g["sessions"]:
        c = class_of(entries)
        counts[c] += 1
        r = dict(base, type="session", **info)
        r.update(measurements=measures, entries=entries, **{"class": c}, rationale=reason_of(entries),
                 unmeasured=sorted(k for k, v in entries.items() if v.get("not_measured")),
                 evidence=[d])
        out.append(r)
    lvr = dict(base, type="level", users=len(g["sessions"]), sessions=counts,
               journal_err=g.get("journal"),
               entries=g["voci_livello"], resources=g["resources"], **{"class": g["class"]},
               significant=g["significant"],
               rationale=_level_reason(g, counts), evidence=[g["cart"]])
    return [lvr] + out


def _level_reason(g, counts):
    p = ["%d GREEN · %d DEGRADED · %d FAIL" % (counts["GREEN"], counts["DEGRADED"], counts["FAIL"])]
    ugly = [k for k, v in g["voci_livello"].items() if v["class"] != "GREEN"]
    if ugly:
        p.append("level: " + reason_of({k: g["voci_livello"][k] for k in ugly}))
    if g["class"] == "DEGRADED":
        if g["significant"]:
            why = []
            if g["n_attori"] and g["n_degradate"] * 4 > g["n_attori"]:
                why.append("more than a quarter of the actors DEGRADED (%d of %d)"
                              % (g["n_degradate"], g["n_attori"]))
            if g["sig_entries"]:
                why.append("beyond half band or not measured: " + ", ".join(
                    "%s/%s" % x for x in g["sig_entries"][:6]))
            p.append("⛔ SIGNIFICANT DEGRADED (" + "; ".join(why) + "): no climbing")
        else:
            p.append("DEGRADED not significant")
    return " · ".join(p)


def show(g):
    print("LEVEL %s · %s · window %s–%s · %s%s" % (
        g["level"], g["campaign"] or "?", _now(g["w0"]), _now(g["w1"]), g["class"],
        " (SIGNIFICANT)" if g["class"] == "DEGRADED" and g["significant"] else ""))
    for d, info, measures, entries in g["sessions"]:
        print("  user %-3s %-2s %-8s %-14s %s" % (info["user"], info["profile"] or "?",
                                                 info["browser"] or "?", info["tenant"] or "?",
                                                 class_of(entries)))
        for k, v in entries.items():
            val = v.get("value")
            print("      %-8s %-40s %s%s" % (v["class"], ENTRY_NAMES.get(k, k),
                                            "" if val is None or isinstance(val, (dict, bool)) else "%s — " % val,
                                            v.get("note", "")))
    for k, v in g["voci_livello"].items():
        print("  level    %-8s %-30s %s" % (v["class"], k, v.get("note", "")))
    r = g["resources"]
    if r:
        print("  resources: machine cpu %s %% (mean) · mem used %s MB · %s" % (
            (r["cpu_machine_pct"] or {}).get("mean"), (r["mem_used_mb"] or {}).get("max"),
            " · ".join("%s %s" % (g2.get("card"), ", ".join("%s %s%%" % (c, (g2[c] or {}).get("mean"))
                                                               for c in ("draw", "video", "video_enhance")
                                                               if g2.get(c)))
                       for g2 in r["gpu"].values())))


# ─────────────────────────────── certify ───────────────────────────────────
def certify():
    outcomes = []

    def look(name, ok, detail=""):
        outcomes.append(ok)
        print("  %s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail else ""))

    print("16-classify --certify")
    print(" 1. every row of §9 at the edges")
    cases = [
        ("delay_p95_ms", 50.0, "GREEN"), ("delay_p95_ms", 50.1, "DEGRADED"),
        ("delay_p95_ms", 150.0, "DEGRADED"), ("delay_p95_ms", 150.1, "FAIL"),
        ("skipped_pct", 2.0, "GREEN"), ("skipped_pct", 2.01, "DEGRADED"),
        ("skipped_pct", 10.0, "DEGRADED"), ("skipped_pct", 10.01, "FAIL"),
        ("block_max_s", 1.0, "GREEN"), ("block_max_s", 1.01, "DEGRADED"),
        ("block_max_s", 3.0, "DEGRADED"), ("block_max_s", 3.01, "FAIL"),
        ("holes_per_min", 0.0, "GREEN"), ("holes_per_min", 0.2, "DEGRADED"),
        ("holes_per_min", 1.0, "DEGRADED"), ("holes_per_min", 1.05, "FAIL"),
        ("video_fraction_f", 0.8, "GREEN"), ("video_fraction_f", 0.79, "DEGRADED"),
        ("video_fraction_f", 0.4, "DEGRADED"), ("video_fraction_f", 0.39, "FAIL"),
        ("audio_audible_pct", 99.0, "GREEN"), ("audio_audible_pct", 98.9, "DEGRADED"),
        ("audio_audible_pct", 95.0, "DEGRADED"), ("audio_audible_pct", 94.9, "FAIL"),
        ("birth_s", 5.0, "GREEN"), ("birth_s", 5.01, "DEGRADED"),
        ("birth_s", 15.0, "DEGRADED"), ("birth_s", 15.01, "FAIL"),
        ("memoria_crescita_pct", 5.0, "GREEN"), ("memoria_crescita_pct", 5.1, "DEGRADED"),
        ("memoria_crescita_pct", 15.0, "DEGRADED"), ("memoria_crescita_pct", 15.1, "FAIL"),
    ]
    wrong = [(v, x, a, judge(v, x)[0]) for v, x, a in cases if judge(v, x)[0] != a]
    look("%d cases at the edges" % len(cases), not wrong, "; ".join("%s %s: expected %s, given %s" % s
                                                                         for s in wrong))
    meta = [("delay_p95_ms", 100.0, False), ("delay_p95_ms", 100.5, True),
            ("video_fraction_f", 0.6, False), ("video_fraction_f", 0.59, True),
            ("audio_audible_pct", 97.0, False), ("audio_audible_pct", 96.9, True)]
    sb = [m for m in meta if judge(m[0], m[1])[1] != m[2]]
    look("beyond half of the DEGRADED band ⇒ significant", not sb, str(sb))

    print(" 2. synthetic levels, from the folders")
    tmp = tempfile.mkdtemp(prefix="16-classifica-cert-")
    T0 = 1_790_000_000.0
    try:
        def level(name, users, log="", result=True, mem=lambda t: 1000.0, corto=None, pid=lambda t: 111,
                    fps=30, tratto=None, listing=True):
            c = os.path.join(tmp, name)
            os.makedirs(c)
            lj = {"campaign": "cert", "level": len(users), "desktop": "kde", "card": "intel",
                  "fps_video": fps,
                  "users": [{"user": i + 1, "profile": u["profile"], "browser": "firefox",
                              "new": u.get("new", False)} for i, u in enumerate(users)]}
            if not listing:
                del lj["users"]
            json.dump(lj, open(os.path.join(c, "level.json"), "w"))
            for i, u in enumerate(users):
                d = os.path.join(c, "user-%02d" % (i + 1))
                os.makedirs(d)
                with open(os.path.join(d, "state.jsonl"), "w") as f:
                    for k in range(0, 601, 5):
                        f.write(json.dumps(u["line"](T0 + k, k)) + "\n")
                if u.get("birth") is not None:
                    json.dump(u["birth"], open(os.path.join(d, "birth.json"), "w"))
            with open(os.path.join(c, "server.log"), "w") as f:
                f.write(log)
                # the child's STRETCH rows, one per second per tenant: max 30 ms
                #   unless `tratto` = {tenant: max, or None for NO row}
                #   (BOTH forms: odd tenants in the OLD Italian form of the logs of the
                #   running campaign, even tenants in the new English form)
                for i, u in enumerate(users):
                    tnt = "c16u%02d" % (i + 1)
                    mx = (tratto or {}).get(tnt, 30.0)
                    if mx is None:
                        continue
                    for k in range(470, 601):
                        o = _dt.datetime.fromtimestamp(T0 + k, _dt.timezone.utc).strftime("%H:%M:%S.000")
                        if i % 2 == 0:
                            f.write("%s figlio  [%s] ⭐ TRATTO cattura → byte fuori: mediana %.2f ms (max %.2f) su "
                                    "512 fotogrammi del campione, 9000 in tutto — produttore 24.00 (max 60.00)\n"
                                    % (o, tnt, 43.0, 6339.0))
                        else:
                            f.write("%s child  [%s] ⭐ STRETCH capture → byte out: median %.2f ms (max %.2f) over "
                                    "512 frames of the sample, 9000 in all — producer 24.00 (max 60.00)\n"
                                    % (o, tnt, 43.0, 6339.0))
                        if mx != "solo-tratto" and i % 2 == 0:
                            f.write("%s figlio  [%s] ⭐ NOSTRO nel secondo (copia → byte fuori, §3.2): p95 %.2f "
                                    "ms · max %.2f · mediana %.2f · 30 fotogrammi\n" % (o, tnt, mx, mx * 1.5,
                                                                                         mx * 0.6))
                        elif mx != "solo-tratto":
                            f.write("%s child  [%s] ⭐ OURS in the second (copy → byte out, §3.2): p95 %.2f "
                                    "ms · max %.2f · median %.2f · 30 frames\n" % (o, tnt, mx, mx * 1.5,
                                                                                    mx * 0.6))
            json.dump(corto or {"user": 1, "outcomes": {"F-003": "PASS", "F-004": "PASS",
                                                       "F-007": "PASS", "F-014": "PASS"}},
                      open(os.path.join(c, "short-check.json"), "w"))
            if result:
                with open(os.path.join(c, "resources.jsonl"), "w") as f:
                    for k in range(0, 601):
                        t = T0 + k
                        f.write(json.dumps({"type": "sample", "t": t, "remotix_pid": pid(k),
                                            "machine": {"cpu_pct": 30, "load": [2, 2, 2],
                                                         "mem_used_mb": 9000, "mem_total_mb": 32000,
                                                         "thread": 900},
                                            "misuratore": {"cpu_s": 0.01},
                                            "enclosures": {rc: {"cpu_core": 1, "pss_mb": mem(k) if rc != "browser"
                                                             else 500 + k, "processes": 5, "gpu": {}}
                                                        for rc in ("remotix", "sessions", "browser",
                                                                   "other_box", "labwc_client")},
                                            "gpu": {}}) + "\n")
            return c

        def healthy(prof, tnt, page_fps=30.0, stalled_for=None, salt_pct=0.0, holes_min=0.0, round_trip=20.0,
                 block=300, audio_pct=100.0, lost=False, drop_at=None, diary=False, echo=True,
                 slow_round=None, video_da=None, video_stopped=False):
            def line(t, k):
                n = k * page_fps
                if stalled_for is not None and k > stalled_for:
                    n = stalled_for * page_fps
                cons = int(k * page_fps / (1 - salt_pct / 100.0)) if salt_pct else int(n)
                r = {"t": t, "user": int(tnt[-2:]), "profile": prof, "browser": "firefox",
                     "tenant": tnt, "work": True, "block_max_ms": block,
                     "round_trip": {"seen": k, "samples": [slow_round or round_trip] * min(200, k)}}
                if echo:
                    r["echo_round"] = {"seen": k, "samples": [round_trip] * min(200, k)}
                if video_da is not None:
                    r["work"] = k > video_da
                    n = max(0, k - video_da) * page_fps
                counts = {"delivered": cons, "painted": int(n), "skip": 0,
                         "holes": int(k / 60.0 * holes_min),
                         "received": k * 50, "played": int(k * 50 * audio_pct / 100.0), "missed": 0}
                if diary:
                    r["diary"] = ("audio: received %(received)d played %(played)d HOLES 0 stale 0 "
                                   "missed %(missed)d times 0 | keys 3 painted %(painted)d video "
                                   "%(delivered)d→%(painted)d out 1 inside 0 dec_queue 0 bmp 0 skip "
                                   "%(skip)d holes %(holes)d ord 0" % counts)
                else:
                    r["counts"] = counts
                if prof != "D":
                    r["input"] = [{"ok": not lost or k < 550, "latency_ms": 150, "action": "click"}]
                elif video_stopped:
                    r["input"] = [{"ok": k < 550, "latency_ms": None, "action": "video_advances",
                                   "det": "t 12.0→12.0"}]
                if drop_at is not None and k >= drop_at:
                    r["drop"] = True
                    r["errors"] = ["the canvas is black"]
                return r
            return {"profile": prof, "line": line}

        four = [healthy("A", "c16u01"), healthy("B", "c16u02", diary=True), healthy("C", "c16u03"),
                   healthy("D", "c16u04")]
        g = ranking(level("green", four))
        look("healthy level ⇒ GREEN", g["class"] == "GREEN", _level_reason(g, _counts(g)))

        u = list(four)
        u[1] = healthy("B", "c16u02", stalled_for=400)
        g = ranking(level("still", u))
        s2 = g["sessions"][1][3]
        look("⛔ FAULT: a stuck session ⇒ level FAIL",
               g["class"] == "FAIL" and s2["block_max_s"]["class"] == "FAIL",
               s2["block_max_s"]["note"])

        u = list(four)
        u[3] = healthy("D", "c16u04", page_fps=20.0)       # 20/30 = 0.67 f: DEGRADED, below half band
        g = ranking(level("video-deg", u))
        look("video at 0.67·f ⇒ DEGRADED, not significant (1 of 4)",
               g["class"] == "DEGRADED" and not g["significant"], g["sessions"][3][3]["video_fraction_f"]["note"])
        u[3] = healthy("D", "c16u04", page_fps=15.0)       # 0.5 f: beyond half band
        g = ranking(level("video-sig", u))
        look("video at 0.5·f ⇒ SIGNIFICANT DEGRADED", g["class"] == "DEGRADED" and g["significant"])
        g = ranking(level("due-deg", four, tratto={"c16u01": 60.0, "c16u02": 60.0}))
        look("2 sessions of 4 DEGRADED (delay 60 ms) ⇒ significant (> a quarter)",
               g["class"] == "DEGRADED" and g["significant"], _level_reason(g, _counts(g)))
        u = [healthy("A", "c16u01", salt_pct=5.0), healthy("B", "c16u02"), healthy("C", "c16u03"),
             healthy("D", "c16u04", audio_pct=96.0)]
        g = ranking(level("salt-audio", u))
        s1, s4 = g["sessions"][0][3], g["sessions"][3][3]
        look("skipped 5 % ⇒ DEGRADED; audio 96 % ⇒ DEGRADED beyond half band",
               s1["skipped_pct"]["class"] == "DEGRADED" and s4["audio_audible_pct"]["class"] == "DEGRADED"
               and s4["audio_audible_pct"]["significant"],
               "%s · %s" % (s1["skipped_pct"]["value"], s4["audio_audible_pct"]["value"]))
        u = [healthy("A", "c16u01", holes_min=2.0), healthy("B", "c16u02", lost=True), healthy("C", "c16u03"),
             healthy("D", "c16u04")]
        g = ranking(level("buchi-persi", u))
        look("2 holes per minute ⇒ FAIL; input lost ⇒ FAIL",
               g["sessions"][0][3]["holes_per_min"]["class"] == "FAIL"
               and g["sessions"][1][3]["delay_p95_ms"]["class"] == "FAIL")
        u = list(four)
        u[2] = healthy("C", "c16u03", block=None)
        u[2]["birth"] = None
        g = ranking(level("non-misurato", u))
        s3 = g["sessions"][2][3]
        look("⛔ MISSING measure ⇒ never GREEN: «not measured», significant",
               s3["block_max_s"].get("not_measured") and g["class"] == "DEGRADED" and g["significant"],
               s3["block_max_s"]["note"])
        u = [dict(healthy("A", "c16u01"), birth={"access_ms": 0, "first_frame_ms": 4800}, new=True),
             dict(healthy("B", "c16u02"), birth={"access_ms": 0, "first_frame_ms": 16000}, new=True),
             dict(healthy("C", "c16u03"), birth={"outcome": "refusal"}, new=True),
             dict(healthy("D", "c16u04"), new=True)]
        g = ranking(level("nascite", u))
        cl = [g["sessions"][i][3].get("birth_s", {}).get("class") for i in range(4)]
        look("births 4.8 s / 16 s / refusal / absent ⇒ GREEN, FAIL, FAIL, not measured",
               cl == ["GREEN", "FAIL", "FAIL", "DEGRADED"] and g["sessions"][3][3]["birth_s"].get("not_measured"),
               str(cl))
        # ⛔ FAULT (review 26 Sep): the birth.json of an earlier rung
        #   (the actor's folder stays) was re-judged at every level
        u = list(four)
        u[1] = dict(healthy("B", "c16u02"), birth={"access_ms": 0, "first_frame_ms": 7000})
        g = ranking(level("nascita-vecchia", u))
        s2 = g["sessions"][1]
        nsa = (T0 + 100) * 1000
        u2 = [dict(healthy("A", "c16u01"), birth={"access_ms": 0, "first_frame_ms": 7000}),
              dict(healthy("B", "c16u02"), birth={"access_ms": nsa, "first_frame_ms": nsa + 7000}),
              healthy("C", "c16u03"), healthy("D", "c16u04")]
        g2 = ranking(level("nascita-senza-elenco", u2, listing=False))
        look("⛔ FAULT: birth from an earlier rung (not `new`, or access outside the level) ⇒ "
               "recorded, does NOT classify; access inside the level ⇒ classifies",
               "birth_s" not in s2[3] and s2[2].get("nascita_precedente", {}).get("birth_s") == 7.0
               and g["class"] == "GREEN"
               and "birth_s" not in g2["sessions"][0][3]
               and g2["sessions"][1][3].get("birth_s", {}).get("class") == "DEGRADED",
               json.dumps(s2[2].get("nascita_precedente"), ensure_ascii=False))
        hh = _dt.datetime.fromtimestamp(T0 + 300, _dt.timezone.utc).strftime("%H:%M:%S.000")
        after = _dt.datetime.fromtimestamp(T0 + 900, _dt.timezone.utc).strftime("%H:%M:%S.000")
        log = ("%s rcp     [c16u03] ⛔ FIN del CLIENT sul canale di controllo (stream 4): §4.2, "
               "la sessione e' finita\n" % hh)
        log += ("%s rcp     [c16u01] ⛔ FIN del CLIENT sul canale di controllo (stream 4): §4.2, "
                "la sessione e' finita\n" % after)
        log += ("%s figlio  [c16u02] ⛔⛔ FIFO **NON** OTTENUTO: politica NORMALE, rifiutato\n" % hh)
        g = ranking(level("caduta-log", four, log=log))
        look("log: the session is over ⇒ FAIL; after the end of the level and any «rifiut» ⇒ no",
               [class_of(s[3]) for s in g["sessions"]] == ["GREEN", "GREEN", "FAIL", "GREEN"])
        # the same in the new English form of the product (english-migration/strings)
        log = ("%s rcp     [c16u03] ⛔ CLIENT FIN on the control channel (stream 4): §4.2, "
               "the session is over\n" % hh)
        log += ("%s rcp     [c16u01] ⛔ CLIENT FIN on the control channel (stream 4): §4.2, "
                "the session is over\n" % after)
        log += ("%s main    ⛔ the stage of «c16u02» (uid 4002) has gone: from now on their sessions "
                "no longer receive frames\n" % hh)
        g = ranking(level("caduta-log-en", four, log=log))
        look("log, English form: the session is over / the stage has gone ⇒ FAIL; after the end ⇒ no",
               [class_of(s[3]) for s in g["sessions"]] == ["GREEN", "FAIL", "FAIL", "GREEN"])
        # the network and the journal: recorded, they do not classify
        rq = ""
        for k in range(0, 31):
            o = _dt.datetime.fromtimestamp(T0 + 540 + k, _dt.timezone.utc).strftime("%H:%M:%S.000")
            rq += ("%s wt      [c16u01] quic-net [192.168.0.2]:4000 since_ms=1000 lost=%d lost_d=1 "
                   "bytes_lost=%d bytes_lost_d=1200 sent=%d sent_d=100 bytes_sent=%d "
                   "received=%d received_d=50 srtt_us=%d pto_us=20000 judgement=--\n"
                   % (o, 10 + k, 12000 + 1200 * k, 1000 + 100 * k, 125000 * (10 + k), 500 + 50 * k,
                      1000 + 100 * k))
        cr = level("network", four, log=rq)
        with open(os.path.join(cr, "journal-err.jsonl"), "w") as f:
            f.write(json.dumps({"MESSAGE": "⛔ something", "PRIORITY": "3", "REMOTIX_TENANT": "c16u01"}) + "\n")
            f.write(json.dumps({"MESSAGE": "⚠ warning", "PRIORITY": "4", "REMOTIX_TENANT": "c16u01"}) + "\n")
        g = ranking(cr)
        rt = g["sessions"][0][2].get("network") or {}
        look("network per session from the log: 31 rows ⇒ lost 31, sent 3100, 1 % (does not classify)",
               rt.get("lost") == 31 and rt.get("sent") == 3100 and rt.get("loss_pct") == 1.0
               and g["class"] == "GREEN" and g["sessions"][1][2].get("network") is None,
               json.dumps(rt))
        look("journal: 1 row at priority <= 3 (the 4 does not), per tenant, does not classify",
               g["journal"]["lines"] == 1 and g["sessions"][0][2].get("journal_err") == 1
               and g["class"] == "GREEN", json.dumps(g["journal"], ensure_ascii=False)[:160])
        # ⭐ a level of a campaign BEFORE the English rename (misure/ is never rewritten): Italian keys
        #   and values, user-NN folders, the old page's diary, the old binary's rete-quic rows ⇒ the
        #   same judgement as the same level written today (before the rename the two are the same)
        NETWORK_OLD = ("%s wt      [c16u01] rete-quic [192.168.0.2]:4000 da_ms=1000 persi=%d persi_d=1 "
                        "byte_persi=%d byte_persi_d=1200 spediti=%d spediti_d=100 byte_spediti=%d "
                        "ricevuti=%d ricevuti_d=50 srtt_us=%d pto_us=20000 giudizio=--\n")
        DIARY_OLD = ("audio: ricevuti %(ricevuti)d suonati %(suonati)d BUCHI 0 vecchi 0 "
                          "mancati %(mancati)d volte 0 | tasti 3 dipinti %(dipinti)d video "
                          "%(consegnati)d→%(dipinti)d fuori 1 dentro 0 coda_dec 0 bmp 0 salt "
                          "%(salt)d buchi %(buchi)d ord 0")  # end of the old fixture rows
        antica = {b: a for a, b in OLD_SPELLING.items()}

        def all_antica(x):
            if isinstance(x, dict):
                return {antica.get(k, k): all_antica(v) for k, v in x.items()}
            if isinstance(x, list):
                return [all_antica(v) for v in x]
            return antica.get(x, x) if isinstance(x, str) else x

        def old(c):
            """The level `c` as a campaign before the rename wrote it."""
            for root, _, file in os.walk(c):
                for name in file:
                    p = os.path.join(root, name)
                    if name.endswith(".jsonl"):
                        lines = [json.loads(x) for x in open(p) if x.strip()]
                        with open(p, "w") as h:
                            for r in lines:
                                if "counts" in r and r.get("user") == 2:       # user 2: the old page's diary
                                    r["diary"] = DIARY_OLD % all_antica(r.pop("counts"))
                                h.write(json.dumps(all_antica(r), ensure_ascii=False) + "\n")
                    elif name.endswith(".json"):
                        d = all_antica(json.load(open(p)))
                        json.dump(d, open(p, "w"), ensure_ascii=False)
            for d in os.listdir(c):
                if d.startswith("user-"):
                    os.rename(os.path.join(c, d), os.path.join(c, spellings("user-")[-1] + d.split("-", 1)[1]))
            return c

        def twin(name, log):
            u = [dict(healthy("A", "c16u01"), birth={"access_ms": nsa, "first_frame_ms": nsa + 4800},
                      new=True),
                 healthy("B", "c16u02"), dict(healthy("C", "c16u03"), birth={"outcome": "refusal"}, new=True),
                 healthy("D", "c16u04")]
            c = level(name, u, log=log, corto={"user": 4, "outcomes": [{"function": "F-003", "outcome": "PASS"},
                                                                         {"function": "F-014", "outcome": "PASS"}]})
            with open(os.path.join(c, "journal-err.jsonl"), "w") as f:
                f.write(json.dumps({"MESSAGE": "⛔ something", "PRIORITY": "3", "REMOTIX_TENANT": "c16u01"}) + "\n")
            return c

        def digest(g):
            return ([(class_of(s[3]), s[2].get("delivered"), s[2].get("painted"), s[2].get("birth_s"),
                      (s[2].get("network") or {}).get("lost"), s[2].get("journal_err"),
                      (s[3].get("short_check") or {}).get("class")) for s in g["sessions"]],
                    sorted((k, v["class"]) for k, v in g["voci_livello"].items()), g["class"])
        rq_old = ""
        for k in range(0, 31):
            o = _dt.datetime.fromtimestamp(T0 + 540 + k, _dt.timezone.utc).strftime("%H:%M:%S.000")
            rq_old += NETWORK_OLD % (o, 10 + k, 12000 + 1200 * k, 1000 + 100 * k, 125000 * (10 + k),
                                          500 + 50 * k, 1000 + 100 * k)
        g_today = ranking(twin("oggi", rq))
        g_ieri = ranking(old(twin("ieri", rq_old)))
        so, yes = digest(g_today), digest(g_ieri)
        look("an OLD level (Italian keys, user-NN, old diary and quic-net rows) ⇒ the same judgement as today's",
               yes == so and [x[0] for x in yes[0]] == ["GREEN", "GREEN", "FAIL", "GREEN"]
               and yes[0][0][3] == 4.8 and yes[0][0][4] == 31 and yes[0][0][5] == 1 and yes[0][1][1]
               and yes[0][3][6] == "GREEN" and len(yes[0]) == 4,
               "old %s · today %s" % (json.dumps(yes)[:300], json.dumps(so)[:300]) if yes != so else "")
        g = ranking(level("riavvio-log", four, log="%s avvio   REMOTIX — fase 1\n" % hh))
        look("restart in the log ⇒ all FAIL", all(class_of(s[3]) == "FAIL" for s in g["sessions"]))
        g = ranking(level("rifiuto-log", four, log="%s rcp     [c16u04] ⛔ posto NEGATO a c16u04 da "
                                                           "x: il registro delle sessioni e' PIENO\n" % hh))
        look("posto NEGATO in the log ⇒ birth FAIL",
               g["sessions"][3][3].get("birth_s", {}).get("class") == "FAIL")
        g = ranking(level("rifiuto-log-en", four, log="%s rcp     [c16u04] ⛔ slot DENIED to c16u04 from "
                                                              "x: the session registry of this server is FULL\n" % hh))
        look("slot DENIED (English form) in the log ⇒ birth FAIL",
               g["sessions"][3][3].get("birth_s", {}).get("class") == "FAIL")
        g = ranking(level("riavvio-pid", four, pid=lambda k: 111 if k < 300 else 222))
        look("parent's pid changed in resources ⇒ level FAIL",
               g["class"] == "FAIL" and g["voci_livello"]["server_restart"]["class"] == "FAIL")
        u = list(four)
        u[0] = healthy("A", "c16u01", drop_at=590)
        g = ranking(level("caduta-stato", u))
        look("the actor says drop ⇒ FAIL", class_of(g["sessions"][0][3]) == "FAIL")
        g = ranking(level("corto-fail", four, corto={"user": 2, "outcomes": {"F-003": "PASS",
                                                                                   "F-014": "FAIL"}}))
        look("short check with a FAIL ⇒ its session FAIL",
               class_of(g["sessions"][1][3]) == "FAIL" and class_of(g["sessions"][0][3]) == "GREEN")
        cc = {"user": 99, "tenant": "c1604u99", "browser": "chrome",
              "outcomes": {"F-003": "PASS", "F-004": "PASS", "F-007": "PASS", "F-014": "PASS"},
              "birth": {"page_s": 0.8, "admission_s": 0.4, "birth_s": 7.2,
                          "first_non_degenerate_s": 7.9, "outcome": "PASS", "rationale": "ok"}}
        g = ranking(level("corto-99", four, corto=cc))
        s99 = [x for x in g["sessions"] if x[1]["user"] == 99]
        v = s99[0][3]["birth_s"] if s99 else {}
        look("short check = session 99 «controllo»: birth 7.2 s at full load ⇒ DEGRADED",
               len(g["sessions"]) == 5 and s99 and s99[0][1]["profile"] == "check"
               and v.get("class") == "DEGRADED" and g["class"] == "DEGRADED"
               and "short_check" not in g["voci_livello"], v.get("note", ""))
        cc["birth"] = {"admission_s": 1.0, "refusal": True, "outcome": "FAIL", "rationale": "the access: refused"}
        g = ranking(level("corto-rifiuto", four, corto=cc))
        look("short check refused ⇒ FAIL", g["class"] == "FAIL")
        # ⛔ FAULT (review 26 Sep): the quarter also counted the check
        cc["birth"] = {"birth_s": 7.2, "outcome": "PASS"}
        g = ranking(level("quarto-attori", four, corto=cc, tratto={"c16u01": 60.0}))
        look("⛔ FAULT: 1 actor of 4 DEGRADED + the check DEGRADED ⇒ NOT significant "
               "(the quarter is of the actors, 1·4 > 4 is false)",
               g["class"] == "DEGRADED" and not g["significant"],
               _level_reason(g, _counts(g)))
        u = list(four)
        u[0] = healthy("A", "c16u01", round_trip=200, slow_round=900)
        g = ranking(level("tratto-30", u))
        v30 = g["sessions"][0][3]["delay_p95_ms"]
        es = g["sessions"][0][2]["esperienza"]
        g2 = ranking(level("tratto-60", u, tratto={"c16u01": 60.0}))
        v60 = g2["sessions"][0][3]["delay_p95_ms"]
        look("delay of the PRODUCT: OURS p95 30 ⇒ 39 ms GREEN, 60 ⇒ 69 ms DEGRADED (the STRETCH rows with "
               "max 6339 do NOT count); giro_eco (200) and whole giro (900) only EXPERIENCE",
               v30["class"] == "GREEN" and abs(v30["value"] - 39.0) < 1e-6
               and v60["class"] == "DEGRADED" and abs(v60["value"] - 69.0) < 1e-6
               and es["echo_round_p95_ms"] == 200 and es["all_round_p95_ms"] == 900, v30["note"])
        g3 = ranking(level("solo-tratto", u, tratto={"c16u01": "solo-tratto"}))
        v = g3["sessions"][0][3]["delay_p95_ms"]
        look("⛔ FAULT: only STRETCH rows (no OURS) ⇒ not measured, and the STRETCH recorded",
               v.get("not_measured") and g3["class"] == "DEGRADED"
               and g3["sessions"][0][2]["stretch"]["producer_median_ms"] == 24.0, v["note"])
        u = list(four)
        u[3] = healthy("D", "c16u04", video_da=540)       # the video starts at 540 s: 60 s of work out of 120
        g = ranking(level("d-lavoro", u))
        s4 = g["sessions"][3]
        look("profile D: `lavoro: false` before the video does not count (fps 30 over 60 s, no freeze)",
               s4[3]["video_fraction_f"]["class"] == "GREEN" and s4[3]["block_max_s"]["class"] == "GREEN"
               and abs(s4[2]["video_fps"] - 30.0) < 0.6, s4[3]["video_fraction_f"]["note"])
        g = ranking(level("mem-perdita", four, mem=lambda k: 1000.0 * (1 + 0.004 * max(0, k - 480))))
        v = g["voci_livello"]["sessions_memory"]
        look("memory +48 % and keeps going ⇒ FAIL", v["class"] == "FAIL", v["note"])
        g = ranking(level("mem-scalino", four,
                               mem=lambda k: 1000.0 if k < 200 else 1200.0))
        v = g["voci_livello"]["sessions_memory"]
        look("memory +20 % but STOPPED ⇒ significant DEGRADED (not FAIL)",
               v["class"] == "DEGRADED" and v["significant"], v["note"])
        # ⛔ FAULT (review 26 Sep): a slow and steady leak (+20 % over the
        #   level) in the 120 s window makes +3 %: it was green
        g = ranking(level("mem-lenta", four, mem=lambda k: 1000.0 * (1 + 0.20 * k / 600.0)))
        v = g["voci_livello"]["sessions_memory"]
        look("⛔ FAULT: memory +20 % linear over the whole level ⇒ FAIL (growth from the start of work, "
               "slope of the second half)", v["class"] == "FAIL" and v["ongoing"], v["note"])
        # ⛔ FAULT (review 26 Sep): with fewer actors than the level only those present were judged
        g = ranking(level("pochi", four), level=6)
        v = g["voci_livello"].get("entered", {})
        look("⛔ FAULT: level 6 declared with 4 actors ⇒ FAIL «entered 4 of 6»",
               g["class"] == "FAIL" and v.get("class") == "FAIL" and v.get("value") == 4, v.get("note", ""))
        # ⛔ FAULT (review 26 Sep): a false «video_avanza» counted as input LOST
        u = list(four)
        u[3] = healthy("D", "c16u04", video_stopped=True)
        g = ranking(level("video-avanza", u))
        s4 = g["sessions"][3][3]
        look("⛔ FAULT: the video in the scene does not advance (profile D) ⇒ video entry significant "
               "DEGRADED, NOT «input lost» on the delay",
               s4["delay_p95_ms"]["class"] == "GREEN" and s4["video_fraction_f"]["class"] == "DEGRADED"
               and s4["video_fraction_f"]["significant"], s4["video_fraction_f"]["note"])
        g = ranking(level("mem-browser", four, mem=lambda k: 1000.0))
        look("the growing browser enclosure does NOT classify", g["class"] == "GREEN")
        g = ranking(level("senza-risorse", four, result=False))
        look("without resources.jsonl ⇒ memory not measured", g["voci_livello"]["remotix_memory"].get("not_measured")
               and g["class"] == "DEGRADED")
        # the log: one row per level and one per session, at the end
        reg = os.path.join(tmp, "registro.jsonl")
        g = ranking(level("log", four))
        lines = log_line_list(g)
        with open(reg, "a") as f:
            for r in lines:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        rr = jsonl(reg)
        look("log: 1 level + 4 sessions, with the fields of §10",
               len(rr) == 5 and rr[0]["type"] == "level" and all(
                   k in rr[1] for k in ("campaign", "level", "user", "profile", "browser", "desktop",
                                        "card", "size", "commit", "class", "rationale", "evidence")))

        print(" 3. --system xrdp (phases/20 §7.3)")

        def rdp(prof, tnt, delay=30.0, lost=False):
            def line(t, k):
                r = {"t": t, "user": int(tnt[-2:]), "profile": prof, "browser": "freerdp",
                     "tenant": tnt, "system": "xrdp", "counts": {"painted": int(k * 30)},
                     "work": True, "block_max_ms": int(delay) if prof != "D" else 40}
                if prof != "D":
                    r["delays_ms"] = [delay, delay]
                    r["input"] = [{"ok": not lost or k < 550, "latency_ms": 150, "action": "keys"}]
                return r
            return {"profile": prof, "line": line}
        xq = [rdp("A", "c16u01"), rdp("B", "c16u02"), rdp("C", "c16u03"), rdp("D", "c16u04")]
        g = ranking(level("xrdp-verde", xq), system="xrdp")
        s1, s4 = g["sessions"][0][3], g["sessions"][3][3]
        look("healthy xrdp ⇒ GREEN, without skipped/holes/audio, delay from the viewer's side",
               g["class"] == "GREEN" and "skipped_pct" not in s1 and "audio_audible_pct" not in s4
               and s1["delay_p95_ms"]["value"] == 30.0 and "delay_p95_ms" not in s4,
               _level_reason(g, _counts(g)))
        # ⛔ FAULT: the same level read as REMOTIX (without --system) is NOT MEASURED
        g = ranking(level("xrdp-come-remotix", xq))
        look("⛔ FAULT: the xrdp series read without --system xrdp ⇒ not measured (DEGRADED)",
               g["class"] == "DEGRADED" and g["significant"])
        u = list(xq)
        u[2] = rdp("C", "c16u03", delay=200.0)
        g = ranking(level("xrdp-lento", u), system="xrdp")
        look("⛔ FAULT: xrdp with 200 ms impulse → draw ⇒ FAIL", g["class"] == "FAIL"
               and g["sessions"][2][3]["delay_p95_ms"]["class"] == "FAIL")
        u = list(xq)
        u[1] = rdp("B", "c16u02", lost=True)
        g = ranking(level("xrdp-perso", u), system="xrdp")
        look("⛔ FAULT: xrdp with input lost ⇒ FAIL", g["class"] == "FAIL")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n, ok = len(outcomes), sum(outcomes)
    print("CERTIFICA %s — %d of %d" % ("PASS" if ok == n else "FAIL", ok, n))
    return 0 if ok == n else 1


def _counts(g):
    c = {"GREEN": 0, "DEGRADED": 0, "FAIL": 0}
    for s in g["sessions"]:
        c[class_of(s[3])] += 1
    return c


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--level-dir")
    a.add_argument("--fps-video", type=float, default=None)
    a.add_argument("--window-s", type=float, default=120.0)
    a.add_argument("--log", default=LOG)
    a.add_argument("--campaign", default=None)
    a.add_argument("--level", type=int, default=None)
    a.add_argument("--log-tz", type=float, default=0.0,
                   help="hours from UTC of the server log's clock (the box: UTC)")
    a.add_argument("--box-journal", choices=("gnome", "kde", "xfce", "lxqt"), default=None,
                   help="if journal-err.jsonl is missing in the level, asks the box for it (root)")
    a.add_argument("--dry-run", action="store_true", help="does not write to the log")
    a.add_argument("--system", choices=("remotix", "xrdp"), default="remotix",
                   help="xrdp: the series of 16-actor-rdp.py (phases/20 §7.3); register-xrdp.jsonl")
    a.add_argument("--json", action="store_true", help="also prints the log rows")
    a.add_argument("--certify", action="store_true")
    o = a.parse_args()
    if o.certify:
        return certify()
    if not o.level_dir:
        a.error("--level-dir is needed (or --certify)")
    if o.system == "xrdp" and o.log == LOG:
        o.log = os.path.join(HERE, "register-xrdp.jsonl")
    g = ranking(o.level_dir, o.fps_video, o.window_s, o.campaign, o.level, o.log_tz,
                   o.box_journal, o.system)
    show(g)
    lines = log_line_list(g)
    if o.json:
        for r in lines:
            print(json.dumps(r, ensure_ascii=False))
    if not o.dry_run:
        with open(o.log, "a", encoding="utf-8") as f:
            for r in lines:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("→ %d rows in %s" % (len(lines), o.log))
    return {"GREEN": 0, "DEGRADED": 3, "FAIL": 1}[g["class"]]


if __name__ == "__main__":
    sys.exit(main())
