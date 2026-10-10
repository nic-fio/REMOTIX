#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-classifica — THE JUDGEMENT OF A LEVEL, WITH THE THRESHOLDS OF §9 (phase 16)

    python3 16-classifica.py --livello-dir DIR/livello-NN [--fps-video 30]
                             [--finestra-s 120] [--registro banchi/16-stress/registro.jsonl]
                             [--campagna intel-4k-kde] [--livello N] [--secco]
    python3 16-classifica.py --certifica

⛔ The thresholds are those of `fasi/16-stress-e-capacita.md` §9, APPROVED
   by the user on 25 Sep 2026 and FROZEN: they live in the SOGLIE table below,
   one row per row of §9, and no parameter changes them.  Only `f` (the
   frame rate of the chosen video, --fps-video) and the check window
   (--finestra-s, the last 2 minutes of the level) are parameters.

Writes at the end of the log (appends only) ONE row for the level and ONE for
each session (§10), and prints the readable judgement.  --secco: does not write.

WHAT IT READS, in the level folder
----------------------------------------------------------------------------
  livello.json        (optional, written by whoever runs the climb) the fields
                      of §10 that are not measured: campagna, livello, desktop,
                      scheda, driver, misura, commit, binario, pagina, nucleo,
                      inizio, durata_s, fps_video, tetto_sessioni,
                      utenti:[{utente, profilo, browser, versione, nuovo}]
  risorse.jsonl       from 16-risorse.py (one row per second)
  utente-NN/stato.jsonl   one row every 5 s, written by the actor:
      {"t": <epoch s>, "utente": 3, "profilo": "C", "browser": "firefox",
       "versione": "Firefox 140…", "inquilino": "c16u03",
       "conti": {"consegnati","dipinti","salt","buchi","tard",
                 "ricevuti","suonati","BUCHI","mancati"}   ← CUMULATIVE, from the
                 page (or "diario": the page's «audio: ricevuti … dipinti …
                 video X→Y … salt … buchi …» line, and it is read from here)
       "giro": {"visti": n, "campioni": [ms, …]}   ← the page's `window.REMOTIX.giro`
                 (the last 200 command → frame delays);
                 or "giro_ms": [only the NEW samples since the last row]
       "input": [{"ok": true, "latenza_ms": 180, "azione": "cartella"}, …]
                 the actions of the interval, with the effect VERIFIED (photo)
       "blocco_max_ms": 420   ← the longest freeze of the image in the 5 s
                 with work in progress (the actor watches the canvas: from here a
                 5 s granularity cannot see below 5 s)
       "lavoro": true,  "caduta": false,  "errori": ["…"]}
  utente-NN/nascita.json  {"accesso_ms": <epoch ms>, "primo_fotogramma_ms":
                      <epoch ms>, "esito": "ok"|"rifiuto"|"…"} (or "nascita_ms")
  controllo-corto.json    {"utente": N, "esiti": {"F-004": "PASS", …}}
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
            the PRODUCT takes (`pagina.html`, `GIRO.parte` on the input,
            `GIRO.torna` when the frame that carries that input arrives in the
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
            users born in the level: `nuovo` in livello.json (its absence is
            «not measured»); if the list is not there, only if `accesso_ms` falls
            inside the level.  The other nascita.json are from an earlier
            rung (the actor's folder carries over): they are RECORDED
            (`nascita_precedente`) and do not classify.
  short     controllo-corto.json: a FAIL ⇒ FAIL; a BLOCKED ⇒ not measured.
  drop      `caduta` in the state, page counters restarted from zero
            (page reloaded or reattached), and in the server log for
            that tenant: «the session is over», «the stage … has
            gone», «the child … is leaving», protocol error (and the old Italian
            forms of the same lines) — ⚠ in the WHOLE
            level, not only in the window: a drop at minute 3 is a
            drop.  The server restart (an «avvio REMOTIX» row, or the pid
            of the parent changing in risorse.jsonl) ⇒ FAIL for all.
  memory    (level) PSS of the `remotix` and `sessioni` enclosures over ALL the work
            of the level, not over the window (§6: the last rung lasts 30 min
            precisely to see leaks): from start of work + 60 s of
            settling (start of work = end − durata_lavoro_s of
            livello.json; otherwise inizio_t; otherwise the first row; and anyway after
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

--sistema xrdp (fasi/20 §7.3, 9 Oct 2026): the series of 16-attore-rdp.py.  Same thresholds, and
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
  log       the rows go into registro-xrdp.jsonl, with the `sistema` field.

THE LEVEL (§9): GREEN if all the sessions (and the level entries) are
GREEN; DEGRADED if at least one is DEGRADED and none FAIL; FAIL if at least one is
FAIL.  SIGNIFICANT DEGRADED = more than a quarter of the ACTORS' sessions
DEGRADED (the check, user 99, does not count; k·4 > n, exact), or a measure
beyond HALF of the DEGRADED band (column `meta` of SOGLIE).
⛔ ENTERED: if the actors present (utente-NN folders, and those of the
`utenti` list of livello.json without a folder count as absent) are fewer than the
declared level (--livello, otherwise livello.json) ⇒ level entry
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

QUI = os.path.dirname(os.path.abspath(__file__))
FPS_VIDEO_SCELTO = 30          # the video of profile D (from the coordinator, 26 Sep 2026)
REGISTRO = os.path.join(QUI, "registro.jsonl")
ORDINE = {"GREEN": 0, "DEGRADED": 1, "FAIL": 2}

# ⛔ §9, FROZEN.  (direction, green, degraded, half, unit).
#   direction "su": the good value is low (GREEN if <= green; DEGRADED if <= degraded)
#   direction "giu": the good value is high (GREEN if >= green; DEGRADED if >= degraded)
#   The video bands are in fractions of f.
SOGLIE = {
    "ritardo_p95_ms":  ("su", 50.0, 150.0, 100.0, "ms"),
    "saltati_pct":     ("su", 2.0, 10.0, 6.0, "%"),
    "blocco_max_s":    ("su", 1.0, 3.0, 2.0, "s"),
    "buchi_al_min":    ("su", 0.0, 1.0, 0.5, "/min"),
    "video_frazione_f": ("giu", 0.8, 0.4, 0.6, "·f"),
    "audio_udibile_pct": ("giu", 99.0, 95.0, 97.0, "%"),
    "nascita_s":       ("su", 5.0, 15.0, 10.0, "s"),
    "memoria_crescita_pct": ("su", 5.0, 15.0, 10.0, "%"),
}
NOMI_VOCI = {
    "ritardo_p95_ms": "input → frame delay (p95)",
    "saltati_pct": "skipped frames",
    "blocco_max_s": "longest freeze of the image",
    "buchi_al_min": "holes in the video chain",
    "video_frazione_f": "video: painted per second",
    "audio_udibile_pct": "audible audio",
    "nascita_s": "birth (access → first frame)",
    "controllo_corto": "short functional check",
    "caduta": "drop, restart, error that disconnects",
    "memoria_crescita_pct": "memory growth",
}

# the server log rows that say «this session has dropped»
# ⚠ BOTH forms: the logs of the running campaign are written by the OLD (Italian)
#   binary, the new binary writes them in English (english-migration/strings).
CADUTE = [
    (re.compile(r"\[(c[0-9a-z]+)\].*la sessione e' finita"), "the session is over (§4.2)"),
    (re.compile(r"\[(c[0-9a-z]+)\].*the session is over"), "the session is over (§4.2)"),
    (re.compile(r"il palco di «(c[0-9a-z]+)».*se n'e' andato"), "the stage has gone"),
    (re.compile(r"the stage of «(c[0-9a-z]+)».*has gone"), "the stage has gone"),
    (re.compile(r"il figlio di «(c[0-9a-z]+)».*se ne va"), "the child is leaving"),
    (re.compile(r"the child of «(c[0-9a-z]+)».*is leaving"), "the child is leaving"),
    (re.compile(r"\[(c[0-9a-z]+)\].*(?:ERRORE_PROTOCOLLO|errore di protocollo|protocol error)", re.I),
     "protocol error"),
    (re.compile(r"\[(c[0-9a-z]+)\].*(?:SFRATTO per silenzio|EVICTION for silence)"), "eviction for silence (§5.3)"),
]
RIAVVIO = re.compile(r"^\d\d:\d\d:\d\d(?:\.\d+)?\s+avvio\s+REMOTIX\b")
# ⚠ not just «rifiut»: `[M]` 25 Sep the child writes «FIFO NON OTTENUTO … rifiut…» at
#   every birth, and it is not a refusal of access.  They are the three doors of rcp.c/webtransport.c
#   (old Italian form and new English form).
RIFIUTO = re.compile(r"(?:\[(c[0-9a-z]+)\]|«(c[0-9a-z]+)»).*(?:posto NEGATO|attacco NEGATO|"
                     r"sessione WebTransport RIFIUTATA|slot DENIED|attach DENIED|WebTransport session REFUSED)")
NOSTRO = re.compile(r"\[(c[0-9a-z]+)\] ⭐ (?:NOSTRO nel secondo|OURS in the second) \([^)]*\): p95 ([\d.]+) ms · "
                    r"max ([\d.]+) · (?:mediana|median) ([\d.]+) · (\d+) (?:fotogrammi|frames)")
PRODUTTORE = re.compile(r"(?:produttore|producer) ([\d.]+) \(max ([\d.]+)\)")
RETE = re.compile(r"\[(c[0-9a-z]+)\] rete-quic (\S+) (.*)$")
TRATTO = re.compile(r"\[(c[0-9a-z]+)\] ⭐ (?:TRATTO cattura → byte fuori|STRETCH capture → byte out): "
                    r"(?:mediana|median) ([\d.]+) ms \(max ([\d.]+)\)")


# ─────────────────────────────── judgement of an entry ─────────────────────
def giudica(voce, valore, f=None):
    """→ (class, significant).  `valore` None does not get here."""
    verso, g, d, meta, _ = SOGLIE[voce]
    if voce == "video_frazione_f":
        valore = valore                        # already in fractions of f
    if verso == "su":
        if valore <= g:
            return "GREEN", False
        if valore <= d:
            return "DEGRADED", valore > meta
        return "FAIL", True
    if valore >= g:
        return "GREEN", False
    if valore >= d:
        return "DEGRADED", valore < meta
    return "FAIL", True


def voce_misurata(voce, valore, nota="", extra=None):
    c, s = giudica(voce, valore)
    v = {"valore": _tondo(valore), "classe": c, "significativo": s, "nota": nota}
    v.update(extra or {})
    return v


def non_misurato(perche):
    return {"valore": None, "classe": "DEGRADED", "significativo": True,
            "non_misurato": True, "nota": "NOT MEASURED: " + perche}


def fallita(valore, perche):
    return {"valore": valore, "classe": "FAIL", "significativo": True, "nota": perche}


def verde(valore, nota):
    return {"valore": valore, "classe": "GREEN", "significativo": False, "nota": nota}


def _tondo(x):
    return round(x, 3) if isinstance(x, float) else x


def p95(v):
    if not v:
        return None
    a = sorted(v)
    return a[max(0, math.ceil(0.95 * len(a)) - 1)]


# ─────────────────────────────── reading ───────────────────────────────────
def jsonl(p):
    out = []
    if not os.path.exists(p):
        return out
    for x in open(p, encoding="utf-8", errors="replace"):
        x = x.strip()
        if x:
            try:
                out.append(json.loads(x))
            except ValueError:
                pass
    return out


def jfile(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


DIARIO = {
    "ricevuti": r"audio: ricevuti (\d+)", "suonati": r"\bsuonati (\d+)",
    "BUCHI": r"\bBUCHI (\d+)", "mancati": r"\bmancati (\d+)", "dipinti": r"\bdipinti (\d+)",
    "salt": r"\bsalt (\d+)", "buchi": r"\bbuchi (\d+)", "tard": r"\btard (\d+)",
}


def conti_di(riga):
    c = dict(riga.get("conti") or {})
    d = riga.get("diario")
    if d:
        for k, rx in DIARIO.items():
            if k not in c:
                m = re.search(rx, d)
                if m:
                    c[k] = int(m.group(1))
        m = re.search(r"\bvideo (\d+)→(\d+)", d)
        if m and "consegnati" not in c:
            c["consegnati"] = int(m.group(1))
            c.setdefault("dipinti", int(m.group(2)))
    return c


def campioni_giro(fin, chiave, chiave_lista):
    """The NEW samples in the window: `chiave` = {visti, campioni} (the last
    200 of the page: the new ones are the last `visti − visti_prima`), or
    `chiave_lista` = [only the new samples since the last row]."""
    camp, pv = [], None
    for r in fin:
        g = r.get(chiave)
        if isinstance(g, dict) and g.get("campioni") is not None:
            vi = g.get("visti", 0)
            if pv is not None and r is not fin[0]:
                nuovi = max(0, vi - pv)
                camp += list(g["campioni"])[-nuovi:] if nuovi else []
            pv = vi
        elif isinstance(g, list) and r is not fin[0]:
            camp += list(g)
        elif r.get(chiave_lista) is not None and r is not fin[0]:
            camp += list(r[chiave_lista])
    return camp


def delta(righe, chiave):
    """Growth of a cumulative counter along the rows; those restarted from zero
    are summed piecewise and COUNTED (restarts)."""
    tot, ripartenze, prima, visto = 0, 0, None, False
    for r in righe:
        v = r["_c"].get(chiave)
        if v is None:
            continue
        visto = True
        if prima is not None:
            if v >= prima:
                tot += v - prima
            else:
                ripartenze += 1
                tot += v
        prima = v
    return (tot if visto else None), ripartenze


# ─────────────────────────────── one session ───────────────────────────────
NON_MISURATI_XRDP = ("saltati_pct", "buchi_al_min", "audio_udibile_pct")


def voce_ritardo_xrdp(dentro, righe, prof, misure, t_liv=None):
    """xrdp: the delay from the viewer's side (impulse → first XDamage draw).
    → entry, or None if the entry does not apply (profile D without impulses)."""
    camp = [x for r in dentro for x in (r.get("ritardi_ms") or [])]
    eco = [x for r in dentro for x in (r.get("ritardi_eco_ms") or [])]
    dove = "window"
    if len(camp) < 5:
        tutte = [r for r in righe if t_liv is None or t_liv[0] - 1 <= r.get("t", 0) <= t_liv[1] + 1]
        camp2 = [x for r in tutte for x in (r.get("ritardi_ms") or [])]
        if len(camp2) > len(camp):
            camp, dove = camp2, "the whole level (%d samples in the window)" % len(camp)
            eco = [x for r in tutte for x in (r.get("ritardi_eco_ms") or [])]
    misure["xrdp_ritardi"] = {"campioni": len(camp), "p95_ms": _tondo(p95(camp)) if camp else None,
                              "mediana_ms": _tondo(sorted(camp)[len(camp) // 2]) if camp else None,
                              "eco_campioni": len(eco), "eco_p95_ms": _tondo(p95(eco)) if eco else None,
                              "su": dove}
    if not camp:
        if prof == "D":
            misure["ritardo_non_si_applica"] = "profile D: no impulse"
            return None
        return non_misurato("no impulse closed by an XDamage draw (empty `ritardi_ms` rows)")
    v = p95(camp)
    misure["ritardo_p95_ms"] = _tondo(v)
    return voce_misurata("ritardo_p95_ms", v, "xrdp, VIEWER'S SIDE: p95 of %d waits impulse → first "
                         "XDamage draw (%s); echo %s ms over %d" % (
                             len(camp), dove, _tondo(p95(eco)) if eco else "—", len(eco)))


def sessione(dir_u, w0, w1, f_video, meta_u, nuovo, corto, log_eventi, tratto, rete=None, tratti=None,
             desktop=None, t_liv=None, sistema=None):
    """`nuovo`: True/False from the list of livello.json; None if the list is not
    there (then the birth is judged only if `accesso_ms` falls in `t_liv`)."""
    righe = jsonl(os.path.join(dir_u, "stato.jsonl"))
    for r in righe:
        r["_c"] = conti_di(r)
    num = int(re.sub(r"\D", "", os.path.basename(dir_u)) or 0)
    prof = (meta_u or {}).get("profilo") or next((r.get("profilo") for r in righe if r.get("profilo")), None)
    info = {"utente": num, "profilo": prof,
            "browser": (meta_u or {}).get("browser") or next((r.get("browser") for r in righe if r.get("browser")), None),
            "versione": (meta_u or {}).get("versione") or next((r.get("versione") for r in righe if r.get("versione")), None),
            "inquilino": next((r.get("inquilino") for r in righe if r.get("inquilino")), (meta_u or {}).get("inquilino"))}
    voci, misure = {}, {}
    # the window: the base row is the last one before w0 (the counters are cumulative)
    prima = [r for r in righe if r.get("t", 0) <= w0]
    dentro = [r for r in righe if w0 < r.get("t", 0) <= w1]
    fin = ([prima[-1]] if prima else []) + dentro
    d_video = prof == "D"
    if len(fin) < 2:
        perche = "no state row in the window (the actor does not write, or is dead)"
        for v in ("ritardo_p95_ms", "saltati_pct", "blocco_max_s", "buchi_al_min"):
            voci[v] = non_misurato(perche)
        if d_video:
            voci["video_frazione_f"] = non_misurato(perche)
            voci["audio_udibile_pct"] = non_misurato(perche)
        if sistema == "xrdp" and prof == "D":
            voci.pop("ritardo_p95_ms", None)
    else:
        dt = fin[-1]["t"] - fin[0]["t"]
        misure["finestra_s"] = round(dt, 1)
        cons, r1 = delta(fin, "consegnati")
        dip, r2 = delta(fin, "dipinti")
        ripartenze = max(r1, r2)
        # ── input → frame delay: the PRODUCT's piece ──
        # ⛔ 26 Sep 2026, from the coordinator, on a measured diagnosis (fase16/
        #   diagnosi-eco): giro_eco = ours (input ~5–9 ms + frame in
        #   hand → page ~14 ms) + NOT ours (the app that draws the echo, the
        #   compositor).  §9 classifies «(product, p95)», §7 «what the
        #   product measures from its side» ⇒ CLASSIFIES: p95 of the `max` of the child's
        #   TRATTO rows in the window + 9 ms (the constructive cap of the
        #   input stretch).  giro_eco and the whole giro are recorded as
        #   EXPERIENCE and do not classify.
        tutti = campioni_giro(fin, "giro", "giro_ms")
        eco = campioni_giro(fin, "giro_eco", "giro_eco_ms")
        misure["esperienza"] = {
            "giro_eco_p95_ms": _tondo(p95(eco)) if eco else None, "giro_eco_campioni": len(eco),
            "giro_tutti_p95_ms": _tondo(p95(tutti)) if tutti else None, "giro_tutti_campioni": len(tutti)}
        tutte_ver = [x for r in dentro for x in (r.get("input") or [])]
        # ⚠ «video_avanza» (profile D) is not an input: the video in the scene
        #   stuck goes to the video entry, not to the delay
        vid_fermo = [x for x in tutte_ver if x.get("azione") == "video_avanza" and x.get("ok") is False]
        inp = [x for x in tutte_ver if x.get("azione") != "video_avanza"]
        persi = [x for x in inp if x.get("ok") is False]
        misure["video_non_avanza"] = len(vid_fermo)
        lat = [x["latenza_ms"] for x in inp if x.get("ok") and x.get("latenza_ms") is not None]
        misure["input_azioni"] = len(inp)
        misure["input_persi"] = len(persi)
        misure["input_latenza_p95_ms"] = _tondo(p95(lat)) if lat else None
        if sistema == "xrdp":
            vr = voce_ritardo_xrdp(dentro, righe, prof, misure, t_liv)
        else:
            vr = voce_ritardo(info["inquilino"], tratti, desktop, misure)
        rit = vr["valore"] if vr else None
        if persi:
            voci["ritardo_p95_ms"] = fallita(_tondo(rit), "input LOST: %d actions of %d without effect (%s)"
                                             % (len(persi), len(inp),
                                                ", ".join(str(x.get("azione")) for x in persi[:3])))
        elif vr:
            voci["ritardo_p95_ms"] = vr
        elif sistema == "xrdp":
            pass                               # profile D without impulses: does not apply
        else:
            voci["ritardo_p95_ms"] = non_misurato("no «OURS in the second» row of the child for %s in the "
                                                  "window (binary before ebc9dcd? the TRATTO rows are "
                                                  "recorded and do not classify)"
                                                  % (info["inquilino"] or "the unknown tenant"))
        # ── skipped ──
        if cons is None or dip is None:
            voci["saltati_pct"] = non_misurato("the page did not give `video X→Y`")
        elif cons == 0:
            voci["saltati_pct"] = non_misurato("no frame delivered in the window")
        else:
            v = max(0.0, 100.0 * (cons - dip) / cons)
            sa, _ = delta(fin, "salt")
            misure.update(consegnati=cons, dipinti=dip, salt=sa, saltati_pct=_tondo(v))
            voci["saltati_pct"] = voce_misurata("saltati_pct", v, "%d delivered, %d painted (salt %s)"
                                                % (cons, dip, sa))
        # ── freeze ──
        # ⚠ `lavoro: false` (for D: before the video starts) does NOT count, neither here
        #   nor for the painted per second: only the work intervals are looked at.
        bm = [r["blocco_max_ms"] for r in dentro
              if r.get("blocco_max_ms") is not None and r.get("lavoro", True) is not False]
        fermi, dip_lav, dt_lav = 0, 0, 0.0
        for a, b in zip(fin, fin[1:]):
            da, db = a["_c"].get("dipinti"), b["_c"].get("dipinti")
            lav = b.get("lavoro", True) is not False
            if da is not None and db is not None and lav:
                dip_lav += max(0, db - da) if db >= da else db
                dt_lav += b["t"] - a["t"]
                if db == da:
                    fermi += 1
        misure["lavoro_s"] = round(dt_lav, 1)
        if dip_lav == 0 and dt_lav > 0 and dip is not None:
            voci["blocco_max_s"] = fallita(round(dt_lav, 1), "STILL IMAGE: no frame painted "
                                           "in %.0f s of work" % dt_lav)
        elif bm:
            v = max(bm) / 1000.0
            misure["blocco_max_s"] = _tondo(v)
            voci["blocco_max_s"] = voce_misurata("blocco_max_s", v, "from the actor (%d rows)" % len(bm))
            if fermi:
                voci["blocco_max_s"] = fallita(max(v, 5.0), "%d intervals of 5 s without frames "
                                               "with work in progress" % fermi)
        elif fermi:
            voci["blocco_max_s"] = fallita(5.0, "%d intervals of 5 s without any frame "
                                           "painted with work in progress ⇒ freeze >= 5 s" % fermi)
        else:
            voci["blocco_max_s"] = non_misurato("`blocco_max_ms` is missing and the 5 s counters do not "
                                                "see below 5 s")
        # ── holes ──
        bu, _ = delta(fin, "buchi")
        if bu is None:
            voci["buchi_al_min"] = non_misurato("the page did not give `buchi`")
        else:
            v = bu / (dt / 60.0) if dt > 0 else 0.0
            misure["buchi"] = bu
            voci["buchi_al_min"] = voce_misurata("buchi_al_min", v, "%d holes in %.0f s" % (bu, dt))
        # ── video and audio (profile D) ──
        if d_video:
            if dip is None:
                voci["video_frazione_f"] = non_misurato("the page did not give `dipinti`")
            elif not f_video:
                voci["video_frazione_f"] = non_misurato("f, the frame rate of the video, is missing (--fps-video)")
            elif dt_lav <= 0:
                voci["video_frazione_f"] = non_misurato("no work interval in the window "
                                                        "(did the video not start?)")
            else:
                fps = dip_lav / dt_lav
                misure["video_fps"] = _tondo(fps)
                voci["video_frazione_f"] = voce_misurata("video_frazione_f", fps / f_video,
                                                         "%.1f painted/s in %.0f s of video, f = %s"
                                                         % (fps, dt_lav, f_video))
            su, _ = delta(fin, "suonati")
            ri, _ = delta(fin, "ricevuti")
            ma, _ = delta(fin, "mancati")
            if su is None or ri is None:
                voci["audio_udibile_pct"] = non_misurato("the page did not give `suonati`/`ricevuti`")
            else:
                den = ri + (ma or 0)
                v = 100.0 * su / den if den else 0.0
                misure["audio_udibile_pct"] = _tondo(v)
                voci["audio_udibile_pct"] = voce_misurata(
                    "audio_udibile_pct", min(v, 100.0),
                    "%d played of %d sent (%d received + %d missed)" % (su, den, ri, ma or 0)
                    if den else "NO audio block in the window while the video plays")
            if vid_fermo:
                vv = voci.get("video_frazione_f")
                if not vv or vv["classe"] == "GREEN":
                    voci["video_frazione_f"] = {
                        "valore": (vv or {}).get("valore"), "classe": "DEGRADED", "significativo": True,
                        "nota": "the VIDEO IN THE SCENE does not advance in %d checks of %d (%s): stuck or paused, "
                                "cause to look at%s" % (
                                    len(vid_fermo), sum(1 for x in tutte_ver if x.get("azione") == "video_avanza"),
                                    (vid_fermo[0].get("det") or "")[:80],
                                    (" · " + vv["nota"]) if vv else "")}
                else:
                    vv["nota"] += " · the video in the scene does not advance in %d checks" % len(vid_fermo)
        # ── drop: the state ──
        cad = [r for r in righe if r.get("caduta")]
        if cad:
            voci["caduta"] = fallita(True, "the actor says DROP at %s: %s" % (
                _ora(cad[0]["t"]), "; ".join(cad[0].get("errori") or [])[:200]))
        elif ripartenze:
            voci["caduta"] = fallita(True, "the page counters restarted from zero %d times: "
                                     "page reloaded or session reattached" % ripartenze)
    # the product's delay does not need the actor: without state rows
    #   it is taken anyway from the child's TRATTO rows
    if len(fin) < 2 and sistema != "xrdp":
        vr = voce_ritardo(info["inquilino"], tratti, desktop, misure)
        if vr:
            voci["ritardo_p95_ms"] = vr
    if sistema == "xrdp":
        tolte = [v for v in NON_MISURATI_XRDP if v in voci]
        for v in tolte:
            voci.pop(v)
        misure["non_misurati_per_costruzione"] = tolte
    # ── drop: the server log (the whole level) ──
    inq = info["inquilino"]
    ev = [e for e in log_eventi if e["inquilino"] == inq or e["inquilino"] == "*"] if inq else \
        [e for e in log_eventi if e["inquilino"] == "*"]
    if ev and voci.get("caduta", {}).get("classe") != "FAIL":
        voci["caduta"] = fallita(True, "server log: " + "; ".join(
            "%s %s" % (e["ora"], e["cosa"]) for e in ev[:3]))
    elif "caduta" not in voci:
        voci["caduta"] = verde(False, "no drop, restart or error that disconnects"
                               + ("" if inq else " (⚠ unknown tenant: only the restart is looked at)"))
    # the network (§7), from the server log: RECORDED, does not classify
    misure["rete"] = (rete or {}).get(inq) if inq else None
    if inq and tratto.get(inq):
        misure["tratto_server_ms"] = tratto[inq]
    # ── birth ──
    na = jfile(os.path.join(dir_u, "nascita.json"))
    if na is not None and nuovo is not True:
        # ⛔ born in this level?  With the list: only if `nuovo`.  Without:
        #   only if the access falls inside the level.
        acc = na.get("accesso_ms")
        dentro_liv = (nuovo is None and acc is not None and t_liv is not None
                      and t_liv[0] - 1 <= acc / 1000.0 <= t_liv[1])
        if not dentro_liv:
            misure["nascita_precedente"] = {
                "nascita_s": round(na["nascita_ms"] / 1000.0, 2) if na.get("nascita_ms") is not None else
                (round((na["primo_fotogramma_ms"] - acc) / 1000.0, 2)
                 if acc is not None and na.get("primo_fotogramma_ms") is not None else None),
                "esito": na.get("esito"),
                "nota": "birth from an earlier rung: recorded, does not classify"}
            na = None
    if na is not None:
        es = str(na.get("esito", "ok")).lower()
        ms = na.get("nascita_ms")
        if ms is None and na.get("accesso_ms") is not None and na.get("primo_fotogramma_ms") is not None:
            ms = na["primo_fotogramma_ms"] - na["accesso_ms"]
        if "rifiut" in es:
            voci["nascita_s"] = fallita(None, "REFUSAL at access")
        elif ms is None:
            voci["nascita_s"] = fallita(None, "no first frame (outcome %s)" % es) if es != "ok" \
                else non_misurato("nascita.json without times")
        else:
            misure["nascita_s"] = round(ms / 1000.0, 2)
            voci["nascita_s"] = voce_misurata("nascita_s", ms / 1000.0, "access → first frame")
            if es not in ("ok", "pass"):
                voci["nascita_s"] = fallita(misure["nascita_s"], "outcome %s" % es)
    elif nuovo:
        voci["nascita_s"] = non_misurato("user born in the level without nascita.json")
    rif = [e for e in log_eventi if e.get("rifiuto") and e["inquilino"] == inq] if inq else []
    if rif:
        voci["nascita_s"] = fallita(None, "refusal in the server log: " + rif[0]["riga"][:160])
    # ── short check ──
    if corto and int(corto.get("utente", -1)) == num:
        voci["controllo_corto"] = voce_corto(corto)
    return info, misure, voci


def voce_nascita_controllo(na):
    """`nascita` of controllo-corto.json: {pagina_s, ammissione_s, nascita_s
    (access → first frame painted), primo_non_degenere_s, rifiuto, esito,
    ragione}.  §9: <= 5 s GREEN, 5–15 DEGRADED, > 15 or refusal FAIL."""
    if not na:
        return non_misurato("controllo-corto.json without `nascita`")
    if na.get("rifiuto"):
        return fallita(None, "REFUSAL at access: %s" % (na.get("ragione") or "")[:160])
    if na.get("nascita_s") is None:
        if str(na.get("esito", "")).upper() == "FAIL":
            return fallita(None, "the check session was not born: %s" % (na.get("ragione") or "")[:160])
        return non_misurato("`nascita` without nascita_s")
    v = voce_misurata("nascita_s", float(na["nascita_s"]), "access → first frame painted, at full load"
                      + (" (not degenerate at %s s)" % na["primo_non_degenere_s"]
                         if na.get("primo_non_degenere_s") is not None else ""))
    if str(na.get("esito", "PASS")).upper() == "FAIL":
        v = fallita(v["valore"], "the first frame: %s" % (na.get("ragione") or "")[:160])
    return v


def sessione_controllo(cart, corto, log_eventi):
    inq = corto.get("inquilino")
    info = {"utente": int(corto.get("utente", 99)), "profilo": "controllo", "browser": corto.get("browser"),
            "versione": corto.get("versione"), "inquilino": inq}
    na = corto.get("nascita") or {}
    misure = {"nascita_s": na.get("nascita_s"), "ammissione_s": na.get("ammissione_s"),
              "primo_non_degenere_s": na.get("primo_non_degenere_s"),
              "sessioni_durante": corto.get("sessioni_durante")}
    voci = {"nascita_s": voce_nascita_controllo(na), "controllo_corto": voce_corto(corto)}
    rif = [e for e in log_eventi if e.get("rifiuto") and inq and e["inquilino"] == inq]
    if rif:
        voci["nascita_s"] = fallita(None, "refusal in the server log: " + rif[0]["riga"][:160])
    return (os.path.join(cart, "controllo-corto"), info, misure, voci)


def voce_corto(corto):
    es = corto.get("esiti") or {}
    if isinstance(es, list):
        es = {x.get("funzione"): x.get("esito") for x in es}
    if not es:
        return non_misurato("controllo-corto.json without outcomes")
    f = [k for k, v in es.items() if v == "FAIL"]
    b = [k for k, v in es.items() if v not in ("PASS", "FAIL")]
    if f:
        return fallita(es, "FAIL: " + ", ".join(f))
    if b:
        r = non_misurato("not looked at: " + ", ".join(b))
        r["valore"] = es
        return r
    return verde(es, "all PASS (%s)" % ", ".join(sorted(es)))


def _ora(t):
    return _dt.datetime.fromtimestamp(t).strftime("%H:%M:%S")


def classe_di(voci):
    c = "GREEN"
    for v in voci.values():
        if ORDINE[v["classe"]] > ORDINE[c]:
            c = v["classe"]
    return c


def ragione_di(voci):
    brutte = sorted(((k, v) for k, v in voci.items() if v["classe"] != "GREEN"),
                    key=lambda kv: -ORDINE[kv[1]["classe"]])
    if not brutte:
        return "all entries GREEN"
    return " · ".join("%s %s: %s%s" % (v["classe"], NOMI_VOCI.get(k, k),
                                        "" if v.get("valore") is None or isinstance(v["valore"], (dict, bool))
                                        else "%s — " % v["valore"], v.get("nota", ""))
                      for k, v in brutte)


# ─────────────────────────────── the server log ────────────────────────────
def epoca_log(ora, t_rif, fuso):
    """«HH:MM:SS.mmm» of the log (server time, `fuso` hours from UTC; the
    box is in UTC) → epoch, with the day nearest to `t_rif`."""
    m = re.match(r"(\d\d):(\d\d):(\d\d(?:\.\d+)?)", ora)
    if not m or not t_rif:
        return None
    base = _dt.datetime.fromtimestamp(t_rif, _dt.timezone.utc) + _dt.timedelta(hours=fuso)
    t = base.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
    t = t.timestamp() - fuso * 3600 + float(m.group(3))
    for g in (-86400, 86400):
        if abs(t + g - t_rif) < abs(t - t_rif):
            t += g
    return t


def eventi_log(p, t_rif, fuso=0.0):
    """The rows that matter, with the time.  ⚠ Those AFTER the end of the level
    (`t_rif`) do not count: the end-of-level clean-up closes the sessions, and
    «the session is over» there is the farewell, not a drop."""
    ev, tratto = [], {}
    if not p or not os.path.exists(p):
        return ev, tratto, False
    for riga in open(p, encoding="utf-8", errors="replace"):
        riga = riga.rstrip("\n")
        ora = riga[:12]
        te = epoca_log(ora, t_rif, fuso)
        if te is not None and te > t_rif + 2:
            continue
        if RIAVVIO.search(riga):
            ev.append({"inquilino": "*", "ora": ora, "cosa": "server RESTART (avvio REMOTIX)", "riga": riga})
            continue
        for rx, cosa in CADUTE:
            m = rx.search(riga)
            if m:
                ev.append({"inquilino": m.group(1), "ora": ora, "cosa": cosa, "riga": riga})
                break
        m = RIFIUTO.search(riga)
        if m and "rifiuto" not in (e.get("cosa") for e in ev[-1:]):
            ev.append({"inquilino": m.group(1) or m.group(2), "ora": ora, "cosa": "rifiuto",
                       "rifiuto": True, "riga": riga})
        m = TRATTO.search(riga)
        if m:
            tratto[m.group(1)] = {"mediana": float(m.group(2)), "max": float(m.group(3)), "ora": ora}
    return ev, tratto, True


TETTO_INGRESSO_MS = 9.0   # the input stretch: the child's 8 ms poll (figlio.c:3794) + 1


def tratti_log(p, w0, w1, fuso=0.0):
    """Two series of the child in the window, per tenant:
    `nostro`  «⭐ OURS in the second (copy → byte out, §3.2): p95 X ms · max Y ·
              median Z · N frames» (commit ebc9dcd; old form «⭐ NOSTRO nel secondo …»):
              ONLY the frames of that second, WITHOUT the compositor's «producer» ⇒ CLASSIFIES;
    `tratto`  «⭐ STRETCH capture → byte out: median X (max Y) …» (old form «⭐ TRATTO
              cattura → byte fuori …»): ⚠ the `max`
              is from the ROLLING SAMPLE of 512 frames (not of the second) and the
              producer is inside it ⇒ only RECORDED (it serves to explain)."""
    out = {"nostro": {}, "tratto": {}}
    if not p or not os.path.exists(p):
        return out
    for riga in open(p, encoding="utf-8", errors="replace"):
        if ("NOSTRO nel secondo" not in riga and "TRATTO cattura" not in riga
                and "OURS in the second" not in riga and "STRETCH capture" not in riga):
            continue
        te = epoca_log(riga[:12], w1, fuso)
        if te is None or te <= w0 or te > w1 + 2:
            continue
        m = NOSTRO.search(riga)
        if m:
            out["nostro"].setdefault(m.group(1), []).append(
                (te, float(m.group(2)), float(m.group(3)), float(m.group(4)), int(m.group(5))))
            continue
        m = TRATTO.search(riga)
        if m:
            pr = PRODUTTORE.search(riga)
            out["tratto"].setdefault(m.group(1), []).append(
                (te, float(m.group(2)), float(m.group(3)), float(pr.group(1)) if pr else None))
    return out


def voce_ritardo(inq, tratti, desktop, misure):
    """The entry of the PRODUCT's delay and the recorded measures.  → entry or None."""
    tratti = tratti or {"nostro": {}, "tratto": {}}
    no = tratti["nostro"].get(inq) or [] if inq else []
    tr = tratti["tratto"].get(inq) or [] if inq else []
    if tr:
        pm = [x[3] for x in tr if x[3] is not None]
        misure["tratto"] = {"righe": len(tr), "mediana_p95_ms": _tondo(p95([x[1] for x in tr])),
                            "max_campione_p95_ms": _tondo(p95([x[2] for x in tr])),
                            "produttore_mediana_ms": _tondo(sorted(pm)[len(pm) // 2]) if pm else None}
    if not no:
        return None
    p95s = [x[1] for x in no]
    rit = p95(p95s) + TETTO_INGRESSO_MS
    misure["ritardo_p95_ms"] = _tondo(rit)
    misure["nostro"] = {"righe": len(no), "p95_dei_p95_ms": _tondo(p95(p95s)),
                        "max_al_secondo_max_ms": _tondo(max(x[2] for x in no)),
                        "max_al_secondo_p95_ms": _tondo(p95([x[2] for x in no])),
                        "mediana_ms": _tondo(sorted(x[3] for x in no)[len(no) // 2]),
                        "fotogrammi": sum(x[4] for x in no)}
    nota = ("p95 of the per-second p95s of «OURS» (copy → byte out, %d rows of the child) %.1f ms + %.0f ms "
            "of input (constructive cap: 8 ms poll)" % (len(no), p95(p95s), TETTO_INGRESSO_MS))
    if (desktop or "").lower() in ("xfce", "lxqt"):
        nota += (" · ⚠ wlroots path: the «copy» is counted twice (~4 ms more, cattura.c:2309 / "
                 "figlio.c:5191) — NOT corrected, it is on the cautious side")
    return voce_misurata("ritardo_p95_ms", rit, nota)


RETE_CUM = ("persi", "byte_persi", "spediti", "byte_spediti", "ricevuti", "scartati",
            "dgram_persi", "dgram_ok", "dgram_falsi")


def rete_log(p, w0, w1, fuso=0.0):
    """§7, the network per session: the server's `rete-quic` rows (one per second per
    connection, CUMULATIVE counters of the connection) in the window ⇒ per
    tenant the Δs (summed over the connections: a re-entry opens a new
    connection and the counters restart), the loss %, the rate, and srtt/pto.
    ⚠ QUIC does not write a «retransmissions» counter: the `persi` packets are
    those that ngtcp2 declared lost, and their content is retransmitted ⇒
    `persi`/`byte_persi` ARE the measure of retransmissions.  Recorded, does not
    classify."""
    if not p or not os.path.exists(p):
        return {}
    conn = {}                                  # (inq, address) → [first, last, srtt[], pto[]]
    for riga in open(p, encoding="utf-8", errors="replace"):
        if "rete-quic" not in riga:
            continue
        m = RETE.search(riga.rstrip("\n"))
        if not m:
            continue
        te = epoca_log(riga[:12], w1, fuso)
        if te is None or te <= w0 or te > w1 + 2:
            continue
        kv = {}
        for k, v in re.findall(r"(\w+)=(-?\d+)", m.group(3)):
            kv[k] = int(v)
        c = conn.setdefault((m.group(1), m.group(2)), [kv, kv, [], [], te, te])
        c[1] = kv
        c[5] = te
        if "srtt_us" in kv:
            c[2].append(kv["srtt_us"] / 1000.0)
        if "pto_us" in kv:
            c[3].append(kv["pto_us"] / 1000.0)
    out = {}
    for (inq, _), (a, b, srtt, pto, t0, t1) in conn.items():
        r = out.setdefault(inq, {k: 0 for k in RETE_CUM})
        r.setdefault("connessioni", 0)
        r["connessioni"] += 1
        r.setdefault("_srtt", []).extend(srtt)
        r.setdefault("_pto", []).extend(pto)
        r["_s"] = r.get("_s", 0) + max(0.0, t1 - t0) + 1.0   # the first row already covers da_ms
        for k in RETE_CUM:
            # the first row of the window is the base, but its `_d` are inside
            base = a.get(k, 0) - a.get(k + "_d", 0) if (k + "_d") in a else a.get(k, 0)
            r[k] += max(0, b.get(k, 0) - base)
    for inq, r in out.items():
        sr, pt, dur = r.pop("_srtt"), r.pop("_pto"), r.pop("_s")
        r["perdita_pct"] = round(100.0 * r["persi"] / r["spediti"], 3) if r["spediti"] else None
        r["mbit_s"] = round(r["byte_spediti"] * 8 / 1e6 / dur, 2) if dur else None
        r["srtt_ms"] = {"mediana": round(sorted(sr)[len(sr) // 2], 2), "max": round(max(sr), 2)} if sr else None
        r["pto_ms_max"] = round(max(pt), 1) if pt else None
        r["secondi"] = round(dur)
    return out


def journal_err(cart, t0, t1, scatola=None):
    """The rows at priority <= 3 (err) of the box's journal in the level — since
    `--journal` exists (26 Sep 2026) the product sends the EVENTS there, with
    REMOTIX_INQUILINO.  Source: `journal-err.jsonl` in the level folder
    (the output of `journalctl -t remotix -p err -o json`), or, with --journal-scatola,
    it is asked of the box now (needs root).  RECORDED, does not classify.
    ⚠ The complete log stays registro.log: it is the source of the classifier."""
    p = os.path.join(cart, "journal-err.jsonl")
    righe, fonte = None, None
    if os.path.exists(p):
        righe, fonte = open(p, encoding="utf-8", errors="replace").read().splitlines(), p
    elif scatola:
        import subprocess
        cmd = ["podman", "exec", "rete11-" + scatola, "journalctl", "-t", "remotix", "-p", "err",
               "--since", "@%d" % int(t0), "--until", "@%d" % int(t1 + 1), "-o", "json", "--no-pager"]
        try:
            o = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            righe, fonte = o.stdout.splitlines(), " ".join(cmd)
            with open(p, "w", encoding="utf-8") as f:      # the evidence stays in the level
                f.write(o.stdout)
        except (OSError, subprocess.SubprocessError) as e:
            return {"righe": None, "nota": "journal not read: %s" % e}
    if righe is None:
        return None
    per, esempi, n = {}, [], 0
    for x in righe:
        x = x.strip()
        if not x:
            continue
        try:
            j = json.loads(x)
            msg, inq, pr = j.get("MESSAGE"), j.get("REMOTIX_INQUILINO"), j.get("PRIORITY")
            if pr is not None and int(pr) > 3:
                continue
            if isinstance(msg, list):                       # journalctl: non-UTF-8 bytes
                msg = bytes(msg).decode("utf-8", "replace")
        except ValueError:
            msg, inq = x, None                              # `-o cat`: one row, no fields
            m = re.search(r"\[(c[0-9a-z]+)\]", x)
            inq = m.group(1) if m else None
        n += 1
        if inq:
            per[inq] = per.get(inq, 0) + 1
        if len(esempi) < 5:
            esempi.append(str(msg)[:200])
    return {"righe": n, "per_inquilino": per, "esempi": esempi, "fonte": fonte}


# ─────────────────────────────── the resources ─────────────────────────────
def risorse(p, w0, w1):
    righe = [r for r in jsonl(p) if r.get("tipo") == "campione"]
    tutte = righe
    fin = [r for r in righe if w0 < r.get("t", 0) <= w1]
    if not fin:
        return None, tutte

    def serie(f):
        out = []
        for r in fin:
            try:
                v = f(r)
            except (KeyError, TypeError):
                v = None
            if v is not None:
                out.append(v)
        return out

    def som(v):
        if not v:
            return None
        return {"media": round(sum(v) / len(v), 2), "p95": round(p95(v), 2), "max": round(max(v), 2)}
    s = {"campioni": len(fin),
         "cpu_macchina_pct": som(serie(lambda r: r["macchina"]["cpu_pct"])),
         "carico_1m": som(serie(lambda r: r["macchina"]["carico"][0])),
         "mem_usata_mb": som(serie(lambda r: r["macchina"]["mem_usata_mb"])),
         "mem_totale_mb": fin[-1]["macchina"].get("mem_totale_mb"),
         "thread": som(serie(lambda r: r["macchina"]["thread"])),
         "misuratore_cpu_s": som(serie(lambda r: r["misuratore"]["cpu_s"])),
         "recinti": {}, "gpu": {}}
    for rc in ("remotix", "sessioni", "browser", "altro_scatola", "labwc_cliente"):
        s["recinti"][rc] = {
            "cpu_core": som(serie(lambda r: r["recinti"][rc]["cpu_core"])),
            "pss_mb": som(serie(lambda r: r["recinti"][rc]["pss_mb"])),
            "processi": som(serie(lambda r: r["recinti"][rc]["processi"])),
            "gpu": {c: som(serie(lambda r: r["recinti"][rc]["gpu"].get(c)))
                    for c in sorted({c for r in fin for c in r["recinti"][rc].get("gpu", {})})},
        }
    for pdev in sorted({p for r in fin for p in r.get("gpu", {})}):
        gg = {"scheda": fin[-1]["gpu"].get(pdev, {}).get("scheda"),
              "driver": fin[-1]["gpu"].get(pdev, {}).get("driver")}
        for c in sorted({c for r in fin for c in r["gpu"].get(pdev, {}).get("categorie", {})}):
            gg[c] = som(serie(lambda r: r["gpu"][pdev]["categorie"].get(c)))
        for k in ("freq_att_mhz", "freq_mhz", "temp_c", "potenza_w", "vram_usata_mb", "occupata_pct"):
            gg[k] = som(serie(lambda r: r["gpu"][pdev].get(k)))
        stroz = {}
        for r in fin:
            for x in r["gpu"].get(pdev, {}).get("strozzatura") or []:
                stroz[x] = stroz.get(x, 0) + 1
        gg["strozzatura_frazione"] = {k: round(v / len(fin), 2) for k, v in stroz.items()}
        s["gpu"][pdev] = gg
    s["avvisi"] = sorted({a for r in fin for a in r.get("avvisi") or []})[:10]
    return s, tutte


ASSESTAMENTO_S = 60.0     # after the start of work, before measuring the memory
CONTINUA_PCT_ORA = 2.0    # «and keeps going»: slope of the second half beyond 2 %/hour of the mean...
CONTINUA_FRAZ = 1.0 / 3   # ...and growth along the second half beyond 1/3 of the total


def pendenza(pts):
    """The least-squares slope of [(t, v)], per second."""
    n = len(pts)
    mt = sum(t for t, _ in pts) / n
    mv = sum(v for _, v in pts) / n
    den = sum((t - mt) ** 2 for t, _ in pts)
    return sum((t - mt) * (v - mv) for t, v in pts) / den if den else 0.0


def voci_livello(ris_tutte, w0, w1, m0=None, m1=None):
    """`m0`–`m1`: the memory stretch (the work of the level, see above);
    None ⇒ from the first row of resources to the last."""
    voci = {}
    fin = [r for r in ris_tutte if (m0 is None or r.get("t", 0) >= m0) and (m1 is None or r.get("t", 0) <= m1)]
    if not fin:
        return {"memoria_remotix": non_misurato("no risorse.jsonl row in the work of the level"),
                "memoria_sessioni": non_misurato("no risorse.jsonl row in the work of the level")}
    for rc in ("remotix", "sessioni"):
        pts = [(r["t"], r["recinti"][rc]["pss_mb"]) for r in fin
               if r.get("recinti", {}).get(rc, {}).get("processi")]
        if len(pts) < 20 or pts[-1][0] - pts[0][0] < 60:
            voci["memoria_" + rc] = non_misurato("memory series of %s too short (%d points)"
                                                 % (rc, len(pts)))
            continue
        t0, t1 = pts[0][0], pts[-1][0]
        a = [v for t, v in pts if t <= t0 + 30]
        b = [v for t, v in pts if t >= t1 - 30]
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        cresc = 100.0 * (mb - ma) / ma if ma > 0 else 0.0
        tm = (t0 + t1) / 2.0
        seconda = [(t, v) for t, v in pts if t >= tm]
        media = sum(v for _, v in pts) / len(pts)
        k = pendenza(seconda) if len(seconda) >= 10 else 0.0
        k_ora = 100.0 * k * 3600.0 / media if media > 0 else 0.0
        su_meta = k * (t1 - tm)
        continua = k_ora > CONTINUA_PCT_ORA and (mb - ma) > 0 and su_meta > CONTINUA_FRAZ * (mb - ma)
        nota = ("PSS %.0f → %.0f MB in %.0f s of work (%s–%s); second half %+.1f %%/hour, %+.0f MB of "
                "%+.0f%s" % (ma, mb, t1 - t0, _ora(t0), _ora(t1), k_ora, su_meta, mb - ma,
                             " and KEEPS rising" if continua else ""))
        v = voce_misurata("memoria_crescita_pct", cresc, nota,
                          {"continua": continua, "pendenza_pct_ora": _tondo(k_ora), "tratto_s": round(t1 - t0)})
        if v["classe"] == "FAIL" and not continua:
            # §9: FAIL is «> 15 % AND keeps going»; beyond 15 % but stopped: it is reported
            v.update(classe="DEGRADED", significativo=True,
                     nota=nota + " — beyond 15 % but STOPPED: reported (§9)")
        voci["memoria_" + rc] = v
    # the restart seen from the resources: the parent's pid changes (in the WHOLE level)
    pids = [r.get("remotix_pid") for r in ris_tutte if r.get("remotix_pid")]
    vuoti = [r for r in ris_tutte if r.get("recinti", {}).get("remotix", {}).get("processi") == 0]
    if len(set(pids)) > 1:
        voci["riavvio_server"] = fallita(sorted(set(pids)), "the pid of the remotix parent CHANGED in the "
                                         "level: %s" % " → ".join(str(p) for p in _senza_ripetuti(pids)))
    elif vuoti:
        voci["riavvio_server"] = fallita(len(vuoti), "remotix enclosure EMPTY in %d samples" % len(vuoti))
    else:
        voci["riavvio_server"] = verde(pids[0] if pids else None, "the remotix parent is the same for "
                                       "the whole level")
    return voci


def _senza_ripetuti(v):
    out = []
    for x in v:
        if not out or out[-1] != x:
            out.append(x)
    return out


# ─────────────────────────────── the level ─────────────────────────────────
def classifica(cart, fps_video=None, finestra_s=120.0, campagna=None, livello=None, fuso_log=0.0,
               journal_scatola=None, sistema=None):
    meta = jfile(os.path.join(cart, "livello.json")) or {}
    # f: --fps-video, then livello.json, then the video chosen in the plan (30 frames/s)
    fps_video = fps_video or meta.get("fps_video") or FPS_VIDEO_SCELTO
    utenti_meta = {int(u["utente"]): u for u in meta.get("utenti") or [] if "utente" in u}
    dirs = sorted(glob.glob(os.path.join(cart, "utente-*")))
    # the end of the level: the last row of any series
    ts = []
    for d in dirs:
        ts += [r.get("t", 0) for r in jsonl(os.path.join(d, "stato.jsonl"))]
    ris_p = os.path.join(cart, "risorse.jsonl")
    ts_r = [r.get("t", 0) for r in jsonl(ris_p) if r.get("tipo") == "campione"]
    w1 = meta.get("fine") or max(ts + ts_r or [0])
    w0 = w1 - finestra_s
    ris, ris_tutte = risorse(ris_p, w0, w1)
    ev, tratto, c_log = eventi_log(os.path.join(cart, "server.log"), w1, fuso_log)
    tratti = tratti_log(os.path.join(cart, "server.log"), w0, w1, fuso_log)
    rete = rete_log(os.path.join(cart, "server.log"), w0, w1, fuso_log)
    t_inizio = meta.get("inizio_t") or min(ts + ts_r or [w0])
    journal = journal_err(cart, t_inizio, w1, journal_scatola)
    corto = jfile(os.path.join(cart, "controllo-corto.json"))
    ha_elenco = bool(utenti_meta)
    sess = []
    for d in dirs:
        n = int(re.sub(r"\D", "", os.path.basename(d)) or 0)
        mu = utenti_meta.get(n)
        nuovo = bool(mu.get("nuovo")) if mu else (False if ha_elenco else None)
        info, misure, voci = sessione(d, w0, w1, fps_video, mu, nuovo,
                                      corto, ev, tratto, rete, tratti, meta.get("desktop"), (t_inizio, w1),
                                      sistema)
        if journal and info.get("inquilino"):
            misure["journal_err"] = journal["per_inquilino"].get(info["inquilino"], 0)
        sess.append((d, info, misure, voci))
    # the memory stretch: the WORK of the level (+ settling), up to the short check
    if meta.get("durata_lavoro_s") is not None and meta.get("fine"):
        m0, da = meta["fine"] - meta["durata_lavoro_s"], "start of work"
    elif meta.get("inizio_t"):
        m0, da = meta["inizio_t"], "start of the level"
    else:
        m0, da = min(ts_r or [t_inizio]), "first row of resources"
    nate = []
    for d in dirs:
        n = int(re.sub(r"\D", "", os.path.basename(d)) or 0)
        if (utenti_meta.get(n) or {}).get("nuovo"):
            na = jfile(os.path.join(d, "nascita.json")) or {}
            if na.get("primo_fotogramma_ms") is not None and na["primo_fotogramma_ms"] / 1000.0 <= w1:
                nate.append(na["primo_fotogramma_ms"] / 1000.0)
    if nate and max(nate) > m0:
        m0, da = max(nate), "last birth"
    m0 += ASSESTAMENTO_S
    m1 = w1
    if corto is not None and meta.get("controllo_min") and meta.get("fine"):
        m1 = min(w1, meta["fine"] - float(meta["controllo_min"]) * 60.0)
    # ⛔ [M] 26 Sep 00:56 (intel-4k-xfce livello-01): the short check lasted 156 s and not
    #    120, the «end − controllo_min» fell 28 s AFTER the birth of session u99 ⇒
    #    +25 MB of a new tenant read as a leak (false FAIL).  The memory
    #    stretch ends before the check appears in the resources, whatever the
    #    duration of the check; and never after the start of the window declared by the climb.
    if meta.get("inizio_finestra_t"):
        m1 = min(m1, float(meta["inizio_finestra_t"]))
    for r in ris_tutte:
        t_r = r.get("t")
        if t_r is None or t_r < m0:
            continue
        chi = set()
        for rec in (r.get("recinti") or {}).values():
            if isinstance(rec, dict):
                chi.update((rec.get("per_inquilino") or {}).keys())
        if any(str(c).endswith("u99") for c in chi):
            m1 = min(m1, t_r - 5.0)
            break
    lv = voci_livello(ris_tutte, w0, w1, m0, m1)
    for k in ("memoria_remotix", "memoria_sessioni"):
        if not lv[k].get("non_misurato"):
            lv[k]["nota"] += " · from: %s + %.0f s" % (da, ASSESTAMENTO_S)
    # ⛔ a rung not reached is not a rung passed
    n_dich = livello if livello is not None else meta.get("livello")
    presenti = {int(re.sub(r"\D", "", os.path.basename(d)) or 0) for d in dirs}
    senza_cart = sorted(set(utenti_meta) - presenti)
    if n_dich is not None:
        k_ent = len(presenti)
        if k_ent < int(n_dich):
            lv["entrati"] = fallita(k_ent, "entered %d of %d%s" % (
                k_ent, int(n_dich), (" (in the list without a folder: %s)" % senza_cart) if senza_cart else ""))
        else:
            lv["entrati"] = verde(k_ent, "entered %d of %d" % (k_ent, int(n_dich)))
    if not c_log:
        lv["registro_server"] = non_misurato("server.log is missing: server drops and errors not looked at")
    if corto is None:
        lv["controllo_corto"] = non_misurato("controllo-corto.json is missing")
    elif not any("controllo_corto" in s[3] for s in sess):
        # ⭐ the short check is a NEW SESSION of its own (16-controllo-corto.py,
        #   user 99): it is classified as a separate session, profile «controllo»,
        #   with its birth at full load (§9 «birth of a new user»)
        sess.append(sessione_controllo(cart, corto, ev))
    if not sess:
        lv["sessioni"] = non_misurato("no utente-NN folder")
    classi = [classe_di(v) for _, _, _, v in sess]
    c_liv = classe_di(lv)
    for c in classi:
        if ORDINE[c] > ORDINE[c_liv]:
            c_liv = c
    # ⚠ the quarter is counted on the ACTORS: the check (user 99) has nothing to do with it
    att = [classe_di(v) for _, i, _, v in sess if i.get("profilo") != "controllo"]
    n_att = len(att)
    n_deg = sum(1 for c in att if c == "DEGRADED")
    sig_voci = [(os.path.basename(d), k) for d, _, _, v in sess for k, x in v.items()
                if x["classe"] == "DEGRADED" and x.get("significativo")]
    sig_voci += [("livello", k) for k, x in lv.items() if x["classe"] == "DEGRADED" and x.get("significativo")]
    significativo = c_liv == "FAIL" or (c_liv == "DEGRADED" and (
        (n_att and n_deg * 4 > n_att) or bool(sig_voci)))
    return {"meta": meta, "w0": w0, "w1": w1, "fps_video": fps_video, "sessioni": sess, "journal": journal,
            "voci_livello": lv, "risorse": ris, "classe": c_liv, "significativo": significativo,
            "n_degradate": n_deg, "n_attori": n_att, "sig_voci": sig_voci, "campagna": campagna or meta.get("campagna"),
            "livello": livello if livello is not None else meta.get("livello", len(sess)),
            "cart": cart, "sistema": sistema or "remotix"}


BASE = ("desktop", "scheda", "driver", "misura", "commit", "binario", "pagina", "nucleo",
        "tetto_sessioni", "inizio", "durata_s")


def righe_registro(g):
    m = g["meta"]
    base = {"campagna": g["campagna"], "livello": g["livello"], "sistema": g.get("sistema", "remotix")}
    for k in BASE:
        base[k] = m.get(k)
    base["finestra"] = [_ora(g["w0"]), _ora(g["w1"])] if g["w1"] else None
    base["fps_video"] = g["fps_video"]
    out = []
    conti = {"GREEN": 0, "DEGRADED": 0, "FAIL": 0}
    for d, info, misure, voci in g["sessioni"]:
        c = classe_di(voci)
        conti[c] += 1
        r = dict(base, tipo="sessione", **info)
        r.update(misure=misure, voci=voci, classe=c, ragione=ragione_di(voci),
                 non_misurate=sorted(k for k, v in voci.items() if v.get("non_misurato")),
                 evidenze=[d])
        out.append(r)
    lvr = dict(base, tipo="livello", utenti=len(g["sessioni"]), sessioni=conti,
               journal_err=g.get("journal"),
               voci=g["voci_livello"], risorse=g["risorse"], classe=g["classe"],
               significativo=g["significativo"],
               ragione=_ragione_livello(g, conti), evidenze=[g["cart"]])
    return [lvr] + out


def _ragione_livello(g, conti):
    p = ["%d GREEN · %d DEGRADED · %d FAIL" % (conti["GREEN"], conti["DEGRADED"], conti["FAIL"])]
    brutte = [k for k, v in g["voci_livello"].items() if v["classe"] != "GREEN"]
    if brutte:
        p.append("level: " + ragione_di({k: g["voci_livello"][k] for k in brutte}))
    if g["classe"] == "DEGRADED":
        if g["significativo"]:
            perche = []
            if g["n_attori"] and g["n_degradate"] * 4 > g["n_attori"]:
                perche.append("more than a quarter of the actors DEGRADED (%d of %d)"
                              % (g["n_degradate"], g["n_attori"]))
            if g["sig_voci"]:
                perche.append("beyond half band or not measured: " + ", ".join(
                    "%s/%s" % x for x in g["sig_voci"][:6]))
            p.append("⛔ SIGNIFICANT DEGRADED (" + "; ".join(perche) + "): no climbing")
        else:
            p.append("DEGRADED not significant")
    return " · ".join(p)


def stampa(g):
    print("LEVEL %s · %s · window %s–%s · %s%s" % (
        g["livello"], g["campagna"] or "?", _ora(g["w0"]), _ora(g["w1"]), g["classe"],
        " (SIGNIFICANT)" if g["classe"] == "DEGRADED" and g["significativo"] else ""))
    for d, info, misure, voci in g["sessioni"]:
        print("  user %-3s %-2s %-8s %-14s %s" % (info["utente"], info["profilo"] or "?",
                                                 info["browser"] or "?", info["inquilino"] or "?",
                                                 classe_di(voci)))
        for k, v in voci.items():
            val = v.get("valore")
            print("      %-8s %-40s %s%s" % (v["classe"], NOMI_VOCI.get(k, k),
                                            "" if val is None or isinstance(val, (dict, bool)) else "%s — " % val,
                                            v.get("nota", "")))
    for k, v in g["voci_livello"].items():
        print("  level    %-8s %-30s %s" % (v["classe"], k, v.get("nota", "")))
    r = g["risorse"]
    if r:
        print("  resources: machine cpu %s %% (mean) · mem used %s MB · %s" % (
            (r["cpu_macchina_pct"] or {}).get("media"), (r["mem_usata_mb"] or {}).get("max"),
            " · ".join("%s %s" % (g2.get("scheda"), ", ".join("%s %s%%" % (c, (g2[c] or {}).get("media"))
                                                               for c in ("disegno", "video", "video_enhance")
                                                               if g2.get(c)))
                       for g2 in r["gpu"].values())))


# ─────────────────────────────── certify ───────────────────────────────────
def certifica():
    esiti = []

    def guarda(nome, ok, dettaglio=""):
        esiti.append(ok)
        print("  %s %s%s" % ("PASS" if ok else "FAIL", nome, (" — " + dettaglio) if dettaglio else ""))

    print("16-classifica --certifica")
    print(" 1. every row of §9 at the edges")
    casi = [
        ("ritardo_p95_ms", 50.0, "GREEN"), ("ritardo_p95_ms", 50.1, "DEGRADED"),
        ("ritardo_p95_ms", 150.0, "DEGRADED"), ("ritardo_p95_ms", 150.1, "FAIL"),
        ("saltati_pct", 2.0, "GREEN"), ("saltati_pct", 2.01, "DEGRADED"),
        ("saltati_pct", 10.0, "DEGRADED"), ("saltati_pct", 10.01, "FAIL"),
        ("blocco_max_s", 1.0, "GREEN"), ("blocco_max_s", 1.01, "DEGRADED"),
        ("blocco_max_s", 3.0, "DEGRADED"), ("blocco_max_s", 3.01, "FAIL"),
        ("buchi_al_min", 0.0, "GREEN"), ("buchi_al_min", 0.2, "DEGRADED"),
        ("buchi_al_min", 1.0, "DEGRADED"), ("buchi_al_min", 1.05, "FAIL"),
        ("video_frazione_f", 0.8, "GREEN"), ("video_frazione_f", 0.79, "DEGRADED"),
        ("video_frazione_f", 0.4, "DEGRADED"), ("video_frazione_f", 0.39, "FAIL"),
        ("audio_udibile_pct", 99.0, "GREEN"), ("audio_udibile_pct", 98.9, "DEGRADED"),
        ("audio_udibile_pct", 95.0, "DEGRADED"), ("audio_udibile_pct", 94.9, "FAIL"),
        ("nascita_s", 5.0, "GREEN"), ("nascita_s", 5.01, "DEGRADED"),
        ("nascita_s", 15.0, "DEGRADED"), ("nascita_s", 15.01, "FAIL"),
        ("memoria_crescita_pct", 5.0, "GREEN"), ("memoria_crescita_pct", 5.1, "DEGRADED"),
        ("memoria_crescita_pct", 15.0, "DEGRADED"), ("memoria_crescita_pct", 15.1, "FAIL"),
    ]
    sbagliati = [(v, x, a, giudica(v, x)[0]) for v, x, a in casi if giudica(v, x)[0] != a]
    guarda("%d cases at the edges" % len(casi), not sbagliati, "; ".join("%s %s: expected %s, given %s" % s
                                                                         for s in sbagliati))
    meta = [("ritardo_p95_ms", 100.0, False), ("ritardo_p95_ms", 100.5, True),
            ("video_frazione_f", 0.6, False), ("video_frazione_f", 0.59, True),
            ("audio_udibile_pct", 97.0, False), ("audio_udibile_pct", 96.9, True)]
    sb = [m for m in meta if giudica(m[0], m[1])[1] != m[2]]
    guarda("beyond half of the DEGRADED band ⇒ significant", not sb, str(sb))

    print(" 2. synthetic levels, from the folders")
    tmp = tempfile.mkdtemp(prefix="16-classifica-cert-")
    T0 = 1_790_000_000.0
    try:
        def livello(nome, utenti, log="", ris=True, mem=lambda t: 1000.0, corto=None, pid=lambda t: 111,
                    fps=30, tratto=None, elenco=True):
            c = os.path.join(tmp, nome)
            os.makedirs(c)
            lj = {"campagna": "cert", "livello": len(utenti), "desktop": "kde", "scheda": "intel",
                  "fps_video": fps,
                  "utenti": [{"utente": i + 1, "profilo": u["profilo"], "browser": "firefox",
                              "nuovo": u.get("nuovo", False)} for i, u in enumerate(utenti)]}
            if not elenco:
                del lj["utenti"]
            json.dump(lj, open(os.path.join(c, "livello.json"), "w"))
            for i, u in enumerate(utenti):
                d = os.path.join(c, "utente-%02d" % (i + 1))
                os.makedirs(d)
                with open(os.path.join(d, "stato.jsonl"), "w") as f:
                    for k in range(0, 601, 5):
                        f.write(json.dumps(u["riga"](T0 + k, k)) + "\n")
                if u.get("nascita") is not None:
                    json.dump(u["nascita"], open(os.path.join(d, "nascita.json"), "w"))
            with open(os.path.join(c, "server.log"), "w") as f:
                f.write(log)
                # the child's TRATTO rows, one per second per tenant: max 30 ms
                #   unless `tratto` = {tenant: max, or None for NO row}
                #   (in the OLD Italian form: the logs of the running campaign)
                for i, u in enumerate(utenti):
                    inq = "c16u%02d" % (i + 1)
                    mx = (tratto or {}).get(inq, 30.0)
                    if mx is None:
                        continue
                    for k in range(470, 601):
                        o = _dt.datetime.fromtimestamp(T0 + k, _dt.timezone.utc).strftime("%H:%M:%S.000")
                        f.write("%s figlio  [%s] ⭐ TRATTO cattura → byte fuori: mediana %.2f ms (max %.2f) su "
                                "512 fotogrammi del campione, 9000 in tutto — produttore 24.00 (max 60.00)\n"
                                % (o, inq, 43.0, 6339.0))
                        if mx != "solo-tratto":
                            f.write("%s figlio  [%s] ⭐ NOSTRO nel secondo (copia → byte fuori, §3.2): p95 %.2f "
                                    "ms · max %.2f · mediana %.2f · 30 fotogrammi\n" % (o, inq, mx, mx * 1.5,
                                                                                         mx * 0.6))
            json.dump(corto or {"utente": 1, "esiti": {"F-003": "PASS", "F-004": "PASS",
                                                       "F-007": "PASS", "F-014": "PASS"}},
                      open(os.path.join(c, "controllo-corto.json"), "w"))
            if ris:
                with open(os.path.join(c, "risorse.jsonl"), "w") as f:
                    for k in range(0, 601):
                        t = T0 + k
                        f.write(json.dumps({"tipo": "campione", "t": t, "remotix_pid": pid(k),
                                            "macchina": {"cpu_pct": 30, "carico": [2, 2, 2],
                                                         "mem_usata_mb": 9000, "mem_totale_mb": 32000,
                                                         "thread": 900},
                                            "misuratore": {"cpu_s": 0.01},
                                            "recinti": {rc: {"cpu_core": 1, "pss_mb": mem(k) if rc != "browser"
                                                             else 500 + k, "processi": 5, "gpu": {}}
                                                        for rc in ("remotix", "sessioni", "browser",
                                                                   "altro_scatola", "labwc_cliente")},
                                            "gpu": {}}) + "\n")
            return c

        def sano(prof, inq, fps_pag=30.0, fermo_da=None, salt_pct=0.0, buchi_min=0.0, giro=20.0,
                 blocco=300, audio_pct=100.0, persi=False, caduta_a=None, diario=False, eco=True,
                 giro_lento=None, video_da=None, video_fermo=False):
            def riga(t, k):
                n = k * fps_pag
                if fermo_da is not None and k > fermo_da:
                    n = fermo_da * fps_pag
                cons = int(k * fps_pag / (1 - salt_pct / 100.0)) if salt_pct else int(n)
                r = {"t": t, "utente": int(inq[-2:]), "profilo": prof, "browser": "firefox",
                     "inquilino": inq, "lavoro": True, "blocco_max_ms": blocco,
                     "giro": {"visti": k, "campioni": [giro_lento or giro] * min(200, k)}}
                if eco:
                    r["giro_eco"] = {"visti": k, "campioni": [giro] * min(200, k)}
                if video_da is not None:
                    r["lavoro"] = k > video_da
                    n = max(0, k - video_da) * fps_pag
                conti = {"consegnati": cons, "dipinti": int(n), "salt": 0,
                         "buchi": int(k / 60.0 * buchi_min),
                         "ricevuti": k * 50, "suonati": int(k * 50 * audio_pct / 100.0), "mancati": 0}
                if diario:
                    r["diario"] = ("audio: ricevuti %(ricevuti)d suonati %(suonati)d BUCHI 0 vecchi 0 "
                                   "mancati %(mancati)d volte 0 | tasti 3 dipinti %(dipinti)d video "
                                   "%(consegnati)d→%(dipinti)d fuori 1 dentro 0 coda_dec 0 bmp 0 salt "
                                   "%(salt)d buchi %(buchi)d ord 0" % conti)
                else:
                    r["conti"] = conti
                if prof != "D":
                    r["input"] = [{"ok": not persi or k < 550, "latenza_ms": 150, "azione": "clic"}]
                elif video_fermo:
                    r["input"] = [{"ok": k < 550, "latenza_ms": None, "azione": "video_avanza",
                                   "det": "t 12.0→12.0"}]
                if caduta_a is not None and k >= caduta_a:
                    r["caduta"] = True
                    r["errori"] = ["the canvas is black"]
                return r
            return {"profilo": prof, "riga": riga}

        quattro = [sano("A", "c16u01"), sano("B", "c16u02", diario=True), sano("C", "c16u03"),
                   sano("D", "c16u04")]
        g = classifica(livello("verde", quattro))
        guarda("healthy level ⇒ GREEN", g["classe"] == "GREEN", _ragione_livello(g, _conti(g)))

        u = list(quattro)
        u[1] = sano("B", "c16u02", fermo_da=400)
        g = classifica(livello("fermo", u))
        s2 = g["sessioni"][1][3]
        guarda("⛔ FAULT: a stuck session ⇒ level FAIL",
               g["classe"] == "FAIL" and s2["blocco_max_s"]["classe"] == "FAIL",
               s2["blocco_max_s"]["nota"])

        u = list(quattro)
        u[3] = sano("D", "c16u04", fps_pag=20.0)       # 20/30 = 0.67 f: DEGRADED, below half band
        g = classifica(livello("video-deg", u))
        guarda("video at 0.67·f ⇒ DEGRADED, not significant (1 of 4)",
               g["classe"] == "DEGRADED" and not g["significativo"], g["sessioni"][3][3]["video_frazione_f"]["nota"])
        u[3] = sano("D", "c16u04", fps_pag=15.0)       # 0.5 f: beyond half band
        g = classifica(livello("video-sig", u))
        guarda("video at 0.5·f ⇒ SIGNIFICANT DEGRADED", g["classe"] == "DEGRADED" and g["significativo"])
        g = classifica(livello("due-deg", quattro, tratto={"c16u01": 60.0, "c16u02": 60.0}))
        guarda("2 sessions of 4 DEGRADED (delay 60 ms) ⇒ significant (> a quarter)",
               g["classe"] == "DEGRADED" and g["significativo"], _ragione_livello(g, _conti(g)))
        u = [sano("A", "c16u01", salt_pct=5.0), sano("B", "c16u02"), sano("C", "c16u03"),
             sano("D", "c16u04", audio_pct=96.0)]
        g = classifica(livello("salt-audio", u))
        s1, s4 = g["sessioni"][0][3], g["sessioni"][3][3]
        guarda("skipped 5 % ⇒ DEGRADED; audio 96 % ⇒ DEGRADED beyond half band",
               s1["saltati_pct"]["classe"] == "DEGRADED" and s4["audio_udibile_pct"]["classe"] == "DEGRADED"
               and s4["audio_udibile_pct"]["significativo"],
               "%s · %s" % (s1["saltati_pct"]["valore"], s4["audio_udibile_pct"]["valore"]))
        u = [sano("A", "c16u01", buchi_min=2.0), sano("B", "c16u02", persi=True), sano("C", "c16u03"),
             sano("D", "c16u04")]
        g = classifica(livello("buchi-persi", u))
        guarda("2 holes per minute ⇒ FAIL; input lost ⇒ FAIL",
               g["sessioni"][0][3]["buchi_al_min"]["classe"] == "FAIL"
               and g["sessioni"][1][3]["ritardo_p95_ms"]["classe"] == "FAIL")
        u = list(quattro)
        u[2] = sano("C", "c16u03", blocco=None)
        u[2]["nascita"] = None
        g = classifica(livello("non-misurato", u))
        s3 = g["sessioni"][2][3]
        guarda("⛔ MISSING measure ⇒ never GREEN: «not measured», significant",
               s3["blocco_max_s"].get("non_misurato") and g["classe"] == "DEGRADED" and g["significativo"],
               s3["blocco_max_s"]["nota"])
        u = [dict(sano("A", "c16u01"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 4800}, nuovo=True),
             dict(sano("B", "c16u02"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 16000}, nuovo=True),
             dict(sano("C", "c16u03"), nascita={"esito": "rifiuto"}, nuovo=True),
             dict(sano("D", "c16u04"), nuovo=True)]
        g = classifica(livello("nascite", u))
        cl = [g["sessioni"][i][3].get("nascita_s", {}).get("classe") for i in range(4)]
        guarda("births 4.8 s / 16 s / refusal / absent ⇒ GREEN, FAIL, FAIL, not measured",
               cl == ["GREEN", "FAIL", "FAIL", "DEGRADED"] and g["sessioni"][3][3]["nascita_s"].get("non_misurato"),
               str(cl))
        # ⛔ FAULT (review 26 Sep): the nascita.json of an earlier rung
        #   (the actor's folder stays) was re-judged at every level
        u = list(quattro)
        u[1] = dict(sano("B", "c16u02"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 7000})
        g = classifica(livello("nascita-vecchia", u))
        s2 = g["sessioni"][1]
        nsa = (T0 + 100) * 1000
        u2 = [dict(sano("A", "c16u01"), nascita={"accesso_ms": 0, "primo_fotogramma_ms": 7000}),
              dict(sano("B", "c16u02"), nascita={"accesso_ms": nsa, "primo_fotogramma_ms": nsa + 7000}),
              sano("C", "c16u03"), sano("D", "c16u04")]
        g2 = classifica(livello("nascita-senza-elenco", u2, elenco=False))
        guarda("⛔ FAULT: birth from an earlier rung (not `nuovo`, or access outside the level) ⇒ "
               "recorded, does NOT classify; access inside the level ⇒ classifies",
               "nascita_s" not in s2[3] and s2[2].get("nascita_precedente", {}).get("nascita_s") == 7.0
               and g["classe"] == "GREEN"
               and "nascita_s" not in g2["sessioni"][0][3]
               and g2["sessioni"][1][3].get("nascita_s", {}).get("classe") == "DEGRADED",
               json.dumps(s2[2].get("nascita_precedente"), ensure_ascii=False))
        hh = _dt.datetime.fromtimestamp(T0 + 300, _dt.timezone.utc).strftime("%H:%M:%S.000")
        dopo = _dt.datetime.fromtimestamp(T0 + 900, _dt.timezone.utc).strftime("%H:%M:%S.000")
        log = ("%s rcp     [c16u03] ⛔ FIN del CLIENT sul canale di controllo (stream 4): §4.2, "
               "la sessione e' finita\n" % hh)
        log += ("%s rcp     [c16u01] ⛔ FIN del CLIENT sul canale di controllo (stream 4): §4.2, "
                "la sessione e' finita\n" % dopo)
        log += ("%s figlio  [c16u02] ⛔⛔ FIFO **NON** OTTENUTO: politica NORMALE, rifiutato\n" % hh)
        g = classifica(livello("caduta-log", quattro, log=log))
        guarda("log: the session is over ⇒ FAIL; after the end of the level and any «rifiut» ⇒ no",
               [classe_di(s[3]) for s in g["sessioni"]] == ["GREEN", "GREEN", "FAIL", "GREEN"])
        # the network and the journal: recorded, they do not classify
        rq = ""
        for k in range(0, 31):
            o = _dt.datetime.fromtimestamp(T0 + 540 + k, _dt.timezone.utc).strftime("%H:%M:%S.000")
            rq += ("%s wt      [c16u01] rete-quic [192.168.0.2]:4000 da_ms=1000 persi=%d persi_d=1 "
                   "byte_persi=%d byte_persi_d=1200 spediti=%d spediti_d=100 byte_spediti=%d "
                   "ricevuti=%d ricevuti_d=50 srtt_us=%d pto_us=20000 giudizio=--\n"
                   % (o, 10 + k, 12000 + 1200 * k, 1000 + 100 * k, 125000 * (10 + k), 500 + 50 * k,
                      1000 + 100 * k))
        cr = livello("rete", quattro, log=rq)
        with open(os.path.join(cr, "journal-err.jsonl"), "w") as f:
            f.write(json.dumps({"MESSAGE": "⛔ something", "PRIORITY": "3", "REMOTIX_INQUILINO": "c16u01"}) + "\n")
            f.write(json.dumps({"MESSAGE": "⚠ warning", "PRIORITY": "4", "REMOTIX_INQUILINO": "c16u01"}) + "\n")
        g = classifica(cr)
        rt = g["sessioni"][0][2].get("rete") or {}
        guarda("network per session from the log: 31 rows ⇒ lost 31, sent 3100, 1 % (does not classify)",
               rt.get("persi") == 31 and rt.get("spediti") == 3100 and rt.get("perdita_pct") == 1.0
               and g["classe"] == "GREEN" and g["sessioni"][1][2].get("rete") is None,
               json.dumps(rt))
        guarda("journal: 1 row at priority <= 3 (the 4 does not), per tenant, does not classify",
               g["journal"]["righe"] == 1 and g["sessioni"][0][2].get("journal_err") == 1
               and g["classe"] == "GREEN", json.dumps(g["journal"], ensure_ascii=False)[:160])
        g = classifica(livello("riavvio-log", quattro, log="%s avvio   REMOTIX — fase 1\n" % hh))
        guarda("restart in the log ⇒ all FAIL", all(classe_di(s[3]) == "FAIL" for s in g["sessioni"]))
        g = classifica(livello("rifiuto-log", quattro, log="%s rcp     [c16u04] ⛔ posto NEGATO a c16u04 da "
                                                           "x: il registro delle sessioni e' PIENO\n" % hh))
        guarda("posto NEGATO in the log ⇒ birth FAIL",
               g["sessioni"][3][3].get("nascita_s", {}).get("classe") == "FAIL")
        g = classifica(livello("riavvio-pid", quattro, pid=lambda k: 111 if k < 300 else 222))
        guarda("parent's pid changed in resources ⇒ level FAIL",
               g["classe"] == "FAIL" and g["voci_livello"]["riavvio_server"]["classe"] == "FAIL")
        u = list(quattro)
        u[0] = sano("A", "c16u01", caduta_a=590)
        g = classifica(livello("caduta-stato", u))
        guarda("the actor says drop ⇒ FAIL", classe_di(g["sessioni"][0][3]) == "FAIL")
        g = classifica(livello("corto-fail", quattro, corto={"utente": 2, "esiti": {"F-003": "PASS",
                                                                                   "F-014": "FAIL"}}))
        guarda("short check with a FAIL ⇒ its session FAIL",
               classe_di(g["sessioni"][1][3]) == "FAIL" and classe_di(g["sessioni"][0][3]) == "GREEN")
        cc = {"utente": 99, "inquilino": "c1604u99", "browser": "chrome",
              "esiti": {"F-003": "PASS", "F-004": "PASS", "F-007": "PASS", "F-014": "PASS"},
              "nascita": {"pagina_s": 0.8, "ammissione_s": 0.4, "nascita_s": 7.2,
                          "primo_non_degenere_s": 7.9, "esito": "PASS", "ragione": "ok"}}
        g = classifica(livello("corto-99", quattro, corto=cc))
        s99 = [x for x in g["sessioni"] if x[1]["utente"] == 99]
        v = s99[0][3]["nascita_s"] if s99 else {}
        guarda("short check = session 99 «controllo»: birth 7.2 s at full load ⇒ DEGRADED",
               len(g["sessioni"]) == 5 and s99 and s99[0][1]["profilo"] == "controllo"
               and v.get("classe") == "DEGRADED" and g["classe"] == "DEGRADED"
               and "controllo_corto" not in g["voci_livello"], v.get("nota", ""))
        cc["nascita"] = {"ammissione_s": 1.0, "rifiuto": True, "esito": "FAIL", "ragione": "the access: refused"}
        g = classifica(livello("corto-rifiuto", quattro, corto=cc))
        guarda("short check refused ⇒ FAIL", g["classe"] == "FAIL")
        # ⛔ FAULT (review 26 Sep): the quarter also counted the check
        cc["nascita"] = {"nascita_s": 7.2, "esito": "PASS"}
        g = classifica(livello("quarto-attori", quattro, corto=cc, tratto={"c16u01": 60.0}))
        guarda("⛔ FAULT: 1 actor of 4 DEGRADED + the check DEGRADED ⇒ NOT significant "
               "(the quarter is of the actors, 1·4 > 4 is false)",
               g["classe"] == "DEGRADED" and not g["significativo"],
               _ragione_livello(g, _conti(g)))
        u = list(quattro)
        u[0] = sano("A", "c16u01", giro=200, giro_lento=900)
        g = classifica(livello("tratto-30", u))
        v30 = g["sessioni"][0][3]["ritardo_p95_ms"]
        es = g["sessioni"][0][2]["esperienza"]
        g2 = classifica(livello("tratto-60", u, tratto={"c16u01": 60.0}))
        v60 = g2["sessioni"][0][3]["ritardo_p95_ms"]
        guarda("delay of the PRODUCT: OURS p95 30 ⇒ 39 ms GREEN, 60 ⇒ 69 ms DEGRADED (the TRATTO rows with "
               "max 6339 do NOT count); giro_eco (200) and whole giro (900) only EXPERIENCE",
               v30["classe"] == "GREEN" and abs(v30["valore"] - 39.0) < 1e-6
               and v60["classe"] == "DEGRADED" and abs(v60["valore"] - 69.0) < 1e-6
               and es["giro_eco_p95_ms"] == 200 and es["giro_tutti_p95_ms"] == 900, v30["nota"])
        g3 = classifica(livello("solo-tratto", u, tratto={"c16u01": "solo-tratto"}))
        v = g3["sessioni"][0][3]["ritardo_p95_ms"]
        guarda("⛔ FAULT: only TRATTO rows (no OURS) ⇒ not measured, and the TRATTO recorded",
               v.get("non_misurato") and g3["classe"] == "DEGRADED"
               and g3["sessioni"][0][2]["tratto"]["produttore_mediana_ms"] == 24.0, v["nota"])
        u = list(quattro)
        u[3] = sano("D", "c16u04", video_da=540)       # the video starts at 540 s: 60 s of work out of 120
        g = classifica(livello("d-lavoro", u))
        s4 = g["sessioni"][3]
        guarda("profile D: `lavoro: false` before the video does not count (fps 30 over 60 s, no freeze)",
               s4[3]["video_frazione_f"]["classe"] == "GREEN" and s4[3]["blocco_max_s"]["classe"] == "GREEN"
               and abs(s4[2]["video_fps"] - 30.0) < 0.6, s4[3]["video_frazione_f"]["nota"])
        g = classifica(livello("mem-perdita", quattro, mem=lambda k: 1000.0 * (1 + 0.004 * max(0, k - 480))))
        v = g["voci_livello"]["memoria_sessioni"]
        guarda("memory +48 % and keeps going ⇒ FAIL", v["classe"] == "FAIL", v["nota"])
        g = classifica(livello("mem-scalino", quattro,
                               mem=lambda k: 1000.0 if k < 200 else 1200.0))
        v = g["voci_livello"]["memoria_sessioni"]
        guarda("memory +20 % but STOPPED ⇒ significant DEGRADED (not FAIL)",
               v["classe"] == "DEGRADED" and v["significativo"], v["nota"])
        # ⛔ FAULT (review 26 Sep): a slow and steady leak (+20 % over the
        #   level) in the 120 s window makes +3 %: it was green
        g = classifica(livello("mem-lenta", quattro, mem=lambda k: 1000.0 * (1 + 0.20 * k / 600.0)))
        v = g["voci_livello"]["memoria_sessioni"]
        guarda("⛔ FAULT: memory +20 % linear over the whole level ⇒ FAIL (growth from the start of work, "
               "slope of the second half)", v["classe"] == "FAIL" and v["continua"], v["nota"])
        # ⛔ FAULT (review 26 Sep): with fewer actors than the level only those present were judged
        g = classifica(livello("pochi", quattro), livello=6)
        v = g["voci_livello"].get("entrati", {})
        guarda("⛔ FAULT: level 6 declared with 4 actors ⇒ FAIL «entered 4 of 6»",
               g["classe"] == "FAIL" and v.get("classe") == "FAIL" and v.get("valore") == 4, v.get("nota", ""))
        # ⛔ FAULT (review 26 Sep): a false «video_avanza» counted as input LOST
        u = list(quattro)
        u[3] = sano("D", "c16u04", video_fermo=True)
        g = classifica(livello("video-avanza", u))
        s4 = g["sessioni"][3][3]
        guarda("⛔ FAULT: the video in the scene does not advance (profile D) ⇒ video entry significant "
               "DEGRADED, NOT «input lost» on the delay",
               s4["ritardo_p95_ms"]["classe"] == "GREEN" and s4["video_frazione_f"]["classe"] == "DEGRADED"
               and s4["video_frazione_f"]["significativo"], s4["video_frazione_f"]["nota"])
        g = classifica(livello("mem-browser", quattro, mem=lambda k: 1000.0))
        guarda("the growing browser enclosure does NOT classify", g["classe"] == "GREEN")
        g = classifica(livello("senza-risorse", quattro, ris=False))
        guarda("without risorse.jsonl ⇒ memory not measured", g["voci_livello"]["memoria_remotix"].get("non_misurato")
               and g["classe"] == "DEGRADED")
        # the log: one row per level and one per session, at the end
        reg = os.path.join(tmp, "registro.jsonl")
        g = classifica(livello("registro", quattro))
        righe = righe_registro(g)
        with open(reg, "a") as f:
            for r in righe:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        rr = jsonl(reg)
        guarda("log: 1 level + 4 sessions, with the fields of §10",
               len(rr) == 5 and rr[0]["tipo"] == "livello" and all(
                   k in rr[1] for k in ("campagna", "livello", "utente", "profilo", "browser", "desktop",
                                        "scheda", "misura", "commit", "classe", "ragione", "evidenze")))

        print(" 3. --sistema xrdp (fasi/20 §7.3)")

        def rdp(prof, inq, rit=30.0, persi=False):
            def riga(t, k):
                r = {"t": t, "utente": int(inq[-2:]), "profilo": prof, "browser": "freerdp",
                     "inquilino": inq, "sistema": "xrdp", "conti": {"dipinti": int(k * 30)},
                     "lavoro": True, "blocco_max_ms": int(rit) if prof != "D" else 40}
                if prof != "D":
                    r["ritardi_ms"] = [rit, rit]
                    r["input"] = [{"ok": not persi or k < 550, "latenza_ms": 150, "azione": "tasti"}]
                return r
            return {"profilo": prof, "riga": riga}
        xq = [rdp("A", "c16u01"), rdp("B", "c16u02"), rdp("C", "c16u03"), rdp("D", "c16u04")]
        g = classifica(livello("xrdp-verde", xq), sistema="xrdp")
        s1, s4 = g["sessioni"][0][3], g["sessioni"][3][3]
        guarda("healthy xrdp ⇒ GREEN, without skipped/holes/audio, delay from the viewer's side",
               g["classe"] == "GREEN" and "saltati_pct" not in s1 and "audio_udibile_pct" not in s4
               and s1["ritardo_p95_ms"]["valore"] == 30.0 and "ritardo_p95_ms" not in s4,
               _ragione_livello(g, _conti(g)))
        # ⛔ FAULT: the same level read as REMOTIX (without --sistema) is NOT MEASURED
        g = classifica(livello("xrdp-come-remotix", xq))
        guarda("⛔ FAULT: the xrdp series read without --sistema xrdp ⇒ not measured (DEGRADED)",
               g["classe"] == "DEGRADED" and g["significativo"])
        u = list(xq)
        u[2] = rdp("C", "c16u03", rit=200.0)
        g = classifica(livello("xrdp-lento", u), sistema="xrdp")
        guarda("⛔ FAULT: xrdp with 200 ms impulse → draw ⇒ FAIL", g["classe"] == "FAIL"
               and g["sessioni"][2][3]["ritardo_p95_ms"]["classe"] == "FAIL")
        u = list(xq)
        u[1] = rdp("B", "c16u02", persi=True)
        g = classifica(livello("xrdp-perso", u), sistema="xrdp")
        guarda("⛔ FAULT: xrdp with input lost ⇒ FAIL", g["classe"] == "FAIL")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n, ok = len(esiti), sum(esiti)
    print("CERTIFICA %s — %d of %d" % ("PASS" if ok == n else "FAIL", ok, n))
    return 0 if ok == n else 1


def _conti(g):
    c = {"GREEN": 0, "DEGRADED": 0, "FAIL": 0}
    for s in g["sessioni"]:
        c[classe_di(s[3])] += 1
    return c


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--livello-dir")
    a.add_argument("--fps-video", type=float, default=None)
    a.add_argument("--finestra-s", type=float, default=120.0)
    a.add_argument("--registro", default=REGISTRO)
    a.add_argument("--campagna", default=None)
    a.add_argument("--livello", type=int, default=None)
    a.add_argument("--fuso-log", type=float, default=0.0,
                   help="hours from UTC of the server log's clock (the box: UTC)")
    a.add_argument("--journal-scatola", choices=("gnome", "kde", "xfce", "lxqt"), default=None,
                   help="if journal-err.jsonl is missing in the level, asks the box for it (root)")
    a.add_argument("--secco", action="store_true", help="does not write to the log")
    a.add_argument("--sistema", choices=("remotix", "xrdp"), default="remotix",
                   help="xrdp: the series of 16-attore-rdp.py (fasi/20 §7.3); registro-xrdp.jsonl")
    a.add_argument("--json", action="store_true", help="also prints the log rows")
    a.add_argument("--certifica", action="store_true")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.livello_dir:
        a.error("--livello-dir is needed (or --certifica)")
    if o.sistema == "xrdp" and o.registro == REGISTRO:
        o.registro = os.path.join(QUI, "registro-xrdp.jsonl")
    g = classifica(o.livello_dir, o.fps_video, o.finestra_s, o.campagna, o.livello, o.fuso_log,
                   o.journal_scatola, o.sistema)
    stampa(g)
    righe = righe_registro(g)
    if o.json:
        for r in righe:
            print(json.dumps(r, ensure_ascii=False))
    if not o.secco:
        with open(o.registro, "a", encoding="utf-8") as f:
            for r in righe:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("→ %d rows in %s" % (len(righe), o.registro))
    return {"GREEN": 0, "DEGRADED": 3, "FAIL": 1}[g["classe"]]


if __name__ == "__main__":
    sys.exit(main())
