#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-attore — A SIMULATED USER of phase 16 (fasi/16-stress-e-capacita.md §4, §5, §7)

    python3 16-attore.py --scatola gnome|kde|xfce|lxqt --utente N (1..16) \\
        --wayland wayland-K --dir DIR --seme S \\
        [--largo 3840 --alto 2160] [--porte-base P] [--video URL] [--host 192.168.0.2]
    python3 16-attore.py --certifica

Runs ON THE SERVER as nicfio (it is nicfio who sets up the environment of the 15 benches: labwc
`--wayland`, local `sudo podman exec`).  One process = one person:

  browser   odd N Firefox (Marionette, port P), even N Chrome (CDP, port P+1)
  profile   N%4: 1 A browsing · 2 B file manager · 3 C terminal · 0 D 4K video
  tenant    c16<NNN>u<N> (e.g. c16001u1), random password, created here and CLEARED
            always on exit (normal end, SIGTERM, SIGINT, exception).
            ⛔ One single access attempt, with the right password: never a ban.

  1. creates the tenant, turns on the browser in its labwc, prepares the home;
  2. ENTERS: measures access (submit → «Admitted») and first frame (submit →
     `dipinti > 0`), then checks that the desktop is not degenerate ⇒ nascita.json;
  3. launches the profile's application INSIDE the session (16-lavori.py);
  4. works in a loop until SIGTERM, with REAL input from the browser and the rhythm
     drawn from random.Random(«seed:user») — repeatable across campaigns.

  DIR/utente-NN/stato.jsonl   ONLY state rows, every 5 s, in the schema of
                              16-classifica.py: t, profilo, inquilino, conti
                              (cumulative: consegnati dipinti salt buchi tard
                              ricevuti suonati BUCHI mancati), diario (the page's
                              «audio: …» line AS IT IS), giro
                              (REMOTIX.giro: visti, campioni), input
                              [{ok, latenza_ms, azione}], blocco_max_ms, lavoro,
                              caduta, errori; and also diario_letto, delta,
                              azioni, verifiche, dettagli_lavoro, eventi
  DIR/utente-NN/eventi.jsonl  inizio, nascita, applicazione, foto, errore, fine
  DIR/utente-NN/nascita.json  {accesso_ms, primo_fotogramma_ms (times in ms
                              from the epoch), nascita_ms (the duration), esito "ok"|…}
  SIGUSR1                     full photo of the canvas in DIR/utente-NN/foto-<t>.png
  on exit                     console-<browser>.txt and registro-pagina.txt

Exit code: 0 stopped by SIGTERM/SIGINT after having worked · 1 the access or
the start did not succeed · 2 bench error.
"""
import argparse
import importlib.util as _iu
import io
import json
import math
import os
import random
import re
import secrets
import signal
import sys
import time
import traceback

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)
SUITE = os.path.join(BANCHI, "15-suite")
DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


L = _carica("lavori16", os.path.join(QUI, "16-lavori.py"))


# ═══════════════════════════════════════════════════════════════════════════
#  THE RHYTHM — one person, repeatable (pure function)
# ═══════════════════════════════════════════════════════════════════════════
class Ritmo:
    """Pauses, choices and typing speed of ONE person.  ⭐ Everything from
    `random.Random("remotix16:<seme>:<utente>")`: the same climb redone
    (Intel/Radeon) has the same choices in the same order; different users
    have different rhythms even with the same seed."""

    def __init__(self, seme, utente, sorgente=None):
        self.r = sorgente or random.Random("remotix16:%s:%d" % (seme, utente))
        self.base_ms = self.r.uniform(110, 240)        # the person's mean keystroke
        self.lentezza = self.r.uniform(0.7, 1.5)       # scale of their pauses

    def battuta_ms(self):
        v = self.r.lognormvariate(math.log(self.base_ms), 0.35)
        if self.r.random() < 0.04:
            v += self.r.uniform(300, 900)              # a hesitation
        return max(40.0, min(1500.0, v))

    def tenuta_ms(self):
        return self.r.uniform(35, 95)

    def pausa_s(self, tipo="breve"):
        if tipo == "gesto":
            v = self.r.uniform(0.15, 0.6)
        elif tipo == "leggere":
            v = self.r.uniform(5.0, 18.0) * self.lentezza
        else:
            v = self.r.lognormvariate(math.log(2.0), 0.5) * self.lentezza
        return max(0.1, min(30.0, v))

    def scegli(self, voci, pesi=None):
        return self.r.choices(list(voci), pesi)[0]

    def intero(self, a, b):
        return self.r.randint(a, b)

    def uniforme(self, a, b):
        return self.r.uniform(a, b)

    def probabile(self, p):
        return self.r.random() < p

    def cifre(self, n):
        return "".join(str(self.r.randint(0, 9)) for _ in range(n))


def impronta(ritmo, n=300):
    """The sequence of `n` draws of all kinds (for the certification)."""
    out = []
    for i in range(n):
        out += [round(ritmo.battuta_ms(), 6), round(ritmo.pausa_s(("gesto", "breve", "leggere")[i % 3]), 6),
                ritmo.scegli("abcd", (1, 2, 3, 4)), ritmo.intero(1, 99), ritmo.cifre(2)]
    return out


def ripetibile(fabbrica, n=300):
    """⭐ Do two rhythms from the same factory give the same sequence?"""
    return impronta(fabbrica(), n) == impronta(fabbrica(), n)


# ═══════════════════════════════════════════════════════════════════════════
#  THE PAGE'S DIARY — the «audio: …» line the page sends every 5 s
#  (src/pagina.html ~6970), read as it is (pure function)
# ═══════════════════════════════════════════════════════════════════════════
# names of the audio half (before « | ») and of the page half (after)
_AUDIO = {"ricevuti": "ricevuti", "suonati": "suonati", "BUCHI": "BUCHI", "vecchi": "vecchi",
          "tardivi": "tardivi", "fuori": "audio_fuori_ordine", "rec": "recuperati",
          "dop": "doppioni", "pieni": "pieni", "errori": "audio_errori", "mancati": "mancati",
          "volte": "mancati_volte", "usciti": "audio_usciti", "tagliati": "tagliati",
          "sospesi": "sospesi", "salti": "salti_suono", "risv": "risvegli", "coda": "coda_ms"}
_PAGINA = {"tasti": "tasti", "dipinti": "dipinti", "fuori": "video_fuori", "dentro": "video_dentro",
           "coda_dec": "coda_dec", "bmp": "bmp", "salt": "salt", "buchi": "buchi", "ord": "ord",
           "mis": "mis", "tard": "tard", "err": "err", "voff": "voff", "AV": "AV_ms"}


def _intero(t):
    m = re.match(r"^([+-]?\d+)", t or "")
    return int(m.group(1)) if m else None


def leggi_riga_diario(riga):
    """⭐ The diary line ⇒ dict.  A field that is not there stays None («not
    read»), NEVER zero: an invented zero is a false green."""
    if not riga or not riga.startswith("audio: "):
        return None
    audio, _, pagina = riga[len("audio: "):].partition(" | ")
    d = {v: None for v in list(_AUDIO.values()) + list(_PAGINA.values())}
    d.update({"video_consegnati": None, "video_dipinti": None, "schermo": None, "fuoco": None,
              "classico": None, "ctx": None})
    for parte, tabella in ((audio, _AUDIO), (pagina, _PAGINA)):
        p = parte.split()
        for i in range(len(p) - 1):
            if p[i] in tabella and d[tabella[p[i]]] is None:
                d[tabella[p[i]]] = _intero(p[i + 1])
    p = pagina.split()
    for i in range(len(p) - 1):
        if p[i] == "video" and "→" in p[i + 1]:
            a, _, b = p[i + 1].partition("→")
            d["video_consegnati"], d["video_dipinti"] = _intero(a), _intero(b)
        elif p[i] in ("schermo", "fuoco", "classico"):
            d[p[i]] = p[i + 1]
    pa = audio.split()
    for i in range(len(pa) - 1):
        if pa[i] == "ctx":
            d["ctx"] = pa[i + 1]
    return d


def differenze(prima, dopo, nomi):
    """The growths of the counters between two readings.  ⚠ A counter that DROPS (the
    page reloaded, the session reborn) is not a negative growth: it is
    «reset», and its delta is None."""
    out, azzerati = {}, []
    for n in nomi:
        a, b = (prima or {}).get(n), (dopo or {}).get(n)
        if a is None or b is None:
            out[n] = None
        elif b < a:
            out[n] = None
            azzerati.append(n)
        else:
            out[n] = b - a
    return out, azzerati


JS_DIARIO = r"""
const da = arguments[0] || 0;
const R = window.REMOTIX, s = R && R.schermo, reg = document.getElementById('registro');
const t = reg ? reg.textContent : '';
const i = t.lastIndexOf('audio: ricevuti');
let riga = null;
if (i >= 0) { const j = t.indexOf('\n', i); riga = j < 0 ? t.slice(i) : t.slice(i, j); }
const nuove = (da <= t.length ? t.slice(da) : t).split('\n')
  .filter(r => r.indexOf('⛔') >= 0 || r.indexOf('MISURA') === 0).slice(-20).map(r => r.slice(0, 300));
const c = s && s.conti;
const e = document.getElementById('esito');
const G = R && R.giro;
const giro = G && G.campioni ? { visti: G.visti, campioni: G.campioni.map(x => Math.round(x * 10) / 10) } : null;
const dt = window.__C16 ? window.__C16.t.splice(0) : null;
const gt = window.__C16 && window.__C16.g ? window.__C16.g.splice(0) : null;
return { riga: riga, lung: t.length, giro: giro, dipinti_t: dt, gesti_t: gt, nuove: nuove, sessione: !!(s && s.sessione),
  schermo: document.body ? (document.body.dataset.schermo || null) : null,
  fuoco: document.hasFocus(), visibile: document.visibilityState,
  esito: e ? e.textContent.slice(0, 200) : null, esito_classe: e ? e.className : null,
  conti: c ? { dipinti: c.dipinti, consegnati: c.consegnati, saltati_coda: c.saltati_coda,
               buchi: c.buchi, chiavi_chieste: c.chiavi_chieste, tardive: c.tardive,
               scartati_ordine: c.scartati_ordine, scartati_misura: c.scartati_misura,
               usciti: c.usciti } : null };
"""
CONTI_DELTA = ("consegnati", "dipinti", "salt", "buchi", "tard", "chiavi_chieste",
               "ricevuti", "suonati", "BUCHI", "mancati")

# ⭐ The paint probe: in the REAL page, every 10 ms it looks at `conti.dipinti`
#   and notes the time (Date.now: the same clock as the actor, same machine)
#   of every change.  JS_DIARIO takes them and empties them every 5 s.
SONDA_DIPINTI = r"""
(function () {
  if (window.__C16) return;
  const C = window.__C16 = { t: [], g: [], ultimo: null };
  /* ⭐ The time of the GESTURES as the page receives them (same clock as the paints):
     `ore_dei_tasti` rebuilt it from the return of Marionette, and a held-back
     chain put the key AFTER its own echo (fasi/20 §3-bis.2).
     In capture on window: it arrives before any handler of the page. */
  const g = function (tipo) {
    return function (e) {
      C.g.push([Date.now(), tipo, tipo === 'k' ? String(e.key) : '']);
      if (C.g.length > 20000) C.g.splice(0, 5000);
    };
  };
  window.addEventListener('keydown', g('k'), true);
  window.addEventListener('pointerdown', g('p'), true);
  window.addEventListener('wheel', g('w'), { capture: true, passive: true });
  setInterval(function () {
    const s = window.REMOTIX && window.REMOTIX.schermo;
    const d = s && s.conti ? s.conti.dipinti : null;
    if (d === null || d === C.ultimo) return;
    if (C.ultimo !== null) { C.t.push(Date.now()); if (C.t.length > 20000) C.t.splice(0, 5000); }
    C.ultimo = d;
  }, 10);
})();
"""


def conti_classifica(c, diario):
    """⭐ The CUMULATIVE counters with the names 16-classifica.py reads: from the
    page (`REMOTIX.schermo.conti`) and, for the audio, from the diary line.
    Only those that are there: a None here would make the classifier believe
    it had read it."""
    out = {}
    c = c or {}
    for mio, suo in (("consegnati", "consegnati"), ("dipinti", "dipinti"), ("salt", "saltati_coda"),
                     ("buchi", "buchi"), ("tard", "tardive"), ("chiavi_chieste", "chiavi_chieste")):
        if c.get(suo) is not None:
            out[mio] = c[suo]
    d = diario or {}
    for k in ("ricevuti", "suonati", "BUCHI", "mancati"):
        if d.get(k) is not None:
            out[k] = d[k]
    for mio, suo in (("consegnati", "video_consegnati"), ("dipinti", "video_dipinti"),
                     ("salt", "salt"), ("buchi", "buchi"), ("tard", "tard")):
        if mio not in out and d.get(suo) is not None:
            out[mio] = d[suo]
    return out


JS_GIRO = r"""
const G = window.REMOTIX && window.REMOTIX.giro;
return G && G.campioni ? { visti: G.visti, campioni: G.campioni.map(x => Math.round(x * 10) / 10) } : null;
"""


def campioni_nuovi(prima, dopo):
    """⭐ The ROUND samples arrived between two readings of `REMOTIX.giro`
    ({visti, campioni: the last 200}): the last `dopo.visti − prima.visti`.
    Taken ONLY around typing with immediate echo, they are the delay of the
    PRODUCT (the character appears at once), without the reaction time
    of the application (a page loading, a window opening).
    ⚠ If more arrived than the list holds, those
    that are there are taken; a missed reading ⇒ no sample (never invented)."""
    if not prima or not dopo or dopo.get("campioni") is None:
        return []
    n = (dopo.get("visti") or 0) - (prima.get("visti") or 0)
    if n <= 0:
        return []
    return list(dopo["campioni"])[-n:]


def attese_impulsi(impulsi, dipinti_t, ora, tetto_s=5.0):
    """⭐ For every impulse (an input that MUST change the image), the wait
    until the first paint AFTER it.  ⇒ (waits in s, impulses still open).
    An impulse without a paint for more than `tetto_s` is closed with the wait so
    far (it is a freeze, it is not thrown away)."""
    attese, aperti = [], []
    pt = sorted(dipinti_t)
    for e in sorted(impulsi):
        dopo = next((x for x in pt if x > e), None)
        if dopo is not None:
            attese.append(dopo - e)
        elif ora - e > tetto_s:
            attese.append(ora - e)
        else:
            aperti.append(e)
    return attese, aperti


def pausa_piu_lunga(dipinti_t, da, a):
    """⭐ The longest still of the image in [da, a] (video: it must always
    change), edges included: from the last paint before `da`, up to `a`."""
    pt = sorted(dipinti_t)
    prima = [x for x in pt if x <= da]
    punti = ([prima[-1]] if prima else [da]) + [x for x in pt if da < x <= a] + [a]
    return max((y - x for x, y in zip(punti, punti[1:])), default=a - da)


TETTO_DEGENERE_S = 15      # §9: the desktop not degenerate within 15 s of access (FAIL beyond)


def esito_nascita(verde, rosso):
    """(outcome, note) of nascita.json from the judgement of the desktop.  ⭐ Only a RED
    (still degenerate at the cap) is «degenere»; a judgement that could not be
    given (blind photo) is NOT a defect of the product: «ok», with the note."""
    if verde:
        return "ok", None
    if rosso:
        return "degenere", None
    return "ok", "desktop not measured (the photo could not be judged)"


def lavora_dopo_nascita(nascita):
    """⭐ The actor works if it has the first frame (the session is there), even
    with a degenerate or unchecked desktop: the load is not removed."""
    return bool(nascita.get("primo_fotogramma_ms")) and "rifiut" not in str(nascita.get("esito"))


def ore_dei_tasti(t_ritorno, durate_ms):
    """⭐ The time of every key of a Marionette chain, derived from the RETURN of
    `PerformActions` (which returns when the last pause is over): key i was
    pressed `sum(durate[i:])` before.  ⛔ With the time taken BEFORE the
    call, Marionette's delay under load ended up in the «freeze»."""
    out, resto = [], sum(durate_ms) / 1000.0
    for d in durate_ms:
        out.append(t_ritorno - resto)
        resto -= d / 1000.0
    return out


def gesto_combacia(atteso, ricevuto):
    """The gesture typed by the actor and the one received by the page are the
    same kind; for a printable character also the same key (an Enter,
    a Tab, a special key: the kind is enough, the names change between engines)."""
    tipo, tasto = atteso
    if ricevuto[1] != tipo:
        return False
    stampabile = lambda t: len(t) == 1 and t.isprintable() and not t.isspace()  # noqa: E731
    if tipo == "k" and tasto and stampabile(tasto):
        return ricevuto[2] == tasto
    if tipo == "k":
        # a special key is not confused with a letter typed without a wait before it
        return not stampabile(ricevuto[2] or "")
    return True


def allinea_impulsi(pendenti, gesti, tolleranza_s=0.25, indietro_s=10.0):
    """⭐ The TRUE time of the impulses: for every impulse of the actor (estimated time,
    gesture), in order, the first still-free gesture of the same kind that the
    page received no later than `tolleranza_s` after the estimate.  ⇒ the times to
    use (the page's, or the estimate if the page did not see it: a
    gesture that does not arrive stays an impulse, and if the image does not change it is a
    real freeze).  `gesti`: [[ms, kind, key], …] from the probe.
    ⚠ The estimate of `ore_dei_tasti` is never BEFORE the real gesture: a chain
    held back by Marionette moves FORWARD all the keys typed before
    the stop, until beyond their echo, and the wait became that of the
    next paint (the blinking cursor: ~1.1 s, fasi/20 §3-bis.2)."""
    gs = sorted(((g[0] / 1000.0, g[1], g[2] if len(g) > 2 else "") for g in (gesti or [])),
                key=lambda g: g[0])
    out, j = [], 0
    for stima, gesto in pendenti:
        k = j
        while k < len(gs) and not (stima - indietro_s <= gs[k][0] <= stima + tolleranza_s
                                   and gesto_combacia(gesto, gs[k])):
            if gs[k][0] > stima + tolleranza_s:
                k = len(gs)
                break
            k += 1
        if gesto is not None and k < len(gs):
            out.append(gs[k][0])
            j = k + 1
        else:
            out.append(stima)
    return out


class Fine(Exception):
    """SIGTERM / SIGINT: work stops and the tenant is cleared."""


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION — the pure functions, with INJECTED FAULTS
# ═══════════════════════════════════════════════════════════════════════════
RIGA_ESEMPIO = ("audio: ricevuti 1200 suonati 1188 BUCHI 2 vecchi 3 tardivi 0 fuori 5 rec 1 "
                "dop 0 pieni 0 errori 0 mancati 7 volte 3 usciti 1180 tagliati 0 sospesi 0 "
                "salti 0 risv 1 coda 270ms dec wasm 55/210us usc 12ms aoff 40 ctx running"
                " | tasti 88 ultimo KeyA classico si schermo acceso dipinti 5000 video "
                "5210→5000 fuori 5100 dentro 110 coda_dec 2 bmp 0 salt 90 buchi 1 ord 0 mis 0 "
                "tard 0 err 0 voff 33 AV +7ms fuoco si")


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)

    print("── the rhythm")
    prova("same seed and user ⇒ same sequence", ripetibile(lambda: Ritmo("s1", 3)))
    prova("different users ⇒ different sequences",
          impronta(Ritmo("s1", 3)) != impronta(Ritmo("s1", 4)))
    prova("different seeds ⇒ different sequences",
          impronta(Ritmo("s1", 3)) != impronta(Ritmo("s2", 3)))
    # ⛔ FAULT: a rhythm without a seed (from the clock) must turn out NOT repeatable
    prova("FAULT seen: rhythm without seed ⇒ not repeatable",
          not ripetibile(lambda: Ritmo("s1", 3, sorgente=random.Random())))
    r = Ritmo("s1", 5)
    b = [r.battuta_ms() for _ in range(3000)]
    media = sum(b) / len(b)
    prova("keystrokes between 40 and 1500 ms, human mean (80-400 ms)",
          min(b) >= 40 and max(b) <= 1500 and 80 <= media <= 400, "mean %.0f ms" % media)
    pp = {k: [r.pausa_s(k) for _ in range(500)] for k in ("gesto", "breve", "leggere")}
    prova("pauses: gesto < breve < leggere (on average)",
          sum(pp["gesto"]) < sum(pp["breve"]) < sum(pp["leggere"]),
          " ".join("%s %.1f s" % (k, sum(v) / len(v)) for k, v in pp.items()))
    basi = {round(Ritmo("s1", n).base_ms) for n in range(1, 17)}
    prova("16 people, 16 different speeds", len(basi) == 16, str(sorted(basi)))

    print("── the page's diary")
    d = leggi_riga_diario(RIGA_ESEMPIO)
    prova("sample line read", d is not None)
    atteso = {"ricevuti": 1200, "suonati": 1188, "BUCHI": 2, "mancati": 7, "mancati_volte": 3,
              "audio_fuori_ordine": 5, "video_fuori": 5100, "video_consegnati": 5210,
              "video_dipinti": 5000, "salt": 90, "buchi": 1, "dipinti": 5000, "coda_ms": 270,
              "tasti": 88, "AV_ms": 7, "fuoco": "si", "schermo": "acceso", "ctx": "running"}
    storti = {k: (d or {}).get(k) for k, v in atteso.items() if (d or {}).get(k) != v}
    prova("every field at its value (the two «fuori» NOT confused)", not storti, str(storti))
    # ⛔ FAULT: the line without BUCHI ⇒ BUCHI None (not read), never 0
    g = leggi_riga_diario(RIGA_ESEMPIO.replace(" BUCHI 2", ""))
    prova("FAULT seen: BUCHI removed from the line ⇒ None, not zero", g and g["BUCHI"] is None,
          "BUCHI=%r" % (g or {}).get("BUCHI"))
    # ⛔ FAULT: BUCHI changed ⇒ the value read changes
    g = leggi_riga_diario(RIGA_ESEMPIO.replace(" BUCHI 2", " BUCHI 41"))
    prova("FAULT seen: BUCHI 41 ⇒ read 41", g and g["BUCHI"] == 41)
    g = leggi_riga_diario(RIGA_ESEMPIO.split(" | ")[0])
    prova("FAULT seen: without the page half ⇒ video None", g and g["video_dipinti"] is None
          and g["salt"] is None)
    prova("a line about something else ⇒ None", leggi_riga_diario("MISURA something") is None)
    dd, az = differenze({"dipinti": 100, "buchi": 1}, {"dipinti": 160, "buchi": 1},
                        ("dipinti", "buchi", "salt"))
    prova("differences: growth and missing field", dd == {"dipinti": 60, "buchi": 0, "salt": None}
          and not az, str(dd))
    # ⛔ FAULT: the reloaded page resets the counters ⇒ «reset», not a negative delta
    dd, az = differenze({"dipinti": 900}, {"dipinti": 12}, ("dipinti",))
    prova("FAULT seen: counter that drops ⇒ reset, delta None",
          dd["dipinti"] is None and az == ["dipinti"])

    print("── the counters for the classifier")
    cc = conti_classifica({"consegnati": 10, "dipinti": 9, "saltati_coda": 1, "buchi": 0,
                           "tardive": 0, "chiavi_chieste": 2}, d)
    prova("classifier names, audio from the diary", cc == {
        "consegnati": 10, "dipinti": 9, "salt": 1, "buchi": 0, "tard": 0, "chiavi_chieste": 2,
        "ricevuti": 1200, "suonati": 1188, "BUCHI": 2, "mancati": 7}, str(cc))
    cc = conti_classifica(None, None)
    prova("FAULT seen: no page ⇒ no counter (not zeros)", cc == {}, str(cc))
    cc = conti_classifica(None, d)
    prova("without direct counters ⇒ from the diary (video X→Y)", cc.get("consegnati") == 5210
          and cc.get("dipinti") == 5000, str(cc))

    print("── the echo round (typing only)")
    g0 = {"visti": 10, "campioni": [30.0] * 10}
    g1 = {"visti": 11, "campioni": [30.0] * 10 + [1136.0]}            # a click that loads a page
    g2 = {"visti": 16, "campioni": [30.0] * 10 + [1136.0] + [41.0, 38.5, 44.0, 40.2, 39.9]}
    eco = campioni_nuovi(g1, g2)                                      # around the typing only
    prova("the 5 samples of the typing, and only those", eco == [41.0, 38.5, 44.0, 40.2, 39.9],
          str(eco))
    # ⛔ FAULT: the difference taken from the start (before the click) carries in the 1136
    tutto = campioni_nuovi(g0, g2)
    prova("FAULT seen: without the reading before the typing the loading click gets in",
          1136.0 in tutto and 1136.0 not in eco, str(tutto))
    prova("missed reading ⇒ no sample", campioni_nuovi(None, g2) == []
          and campioni_nuovi(g2, g2) == [])
    g3 = {"visti": 500, "campioni": [float(i) for i in range(200)]}
    prova("more samples than the list ⇒ those that are there", len(campioni_nuovi(g0, g3)) == 200)

    print("── the freeze of the image")
    at, ap = attese_impulsi([10.0, 12.0, 19.5], [10.2, 10.25, 13.5], 20.0)
    prova("waits: 0.2 s and 1.5 s, the last still open",
          [round(x, 2) for x in at] == [0.2, 1.5] and ap == [19.5], "%s %s" % (at, ap))
    # ⛔ FAULT: the image no longer changes after the input ⇒ the wait becomes a freeze
    at, ap = attese_impulsi([10.0], [9.0], 16.0)
    prova("FAULT seen: no paint after the input ⇒ freeze of 6 s", at == [6.0] and not ap,
          str(at))
    pl = pausa_piu_lunga([x / 30.0 for x in range(0, 300)], 2.0, 9.9)
    prova("video at 30 per second ⇒ still of ~33 ms", 0.03 <= pl <= 0.04, "%.3f s" % pl)
    buco = [x / 30.0 for x in range(0, 300) if not 150 <= x < 210]
    pl = pausa_piu_lunga(buco, 2.0, 9.9)
    # ⛔ FAULT: 2 s without frames in the middle of the video ⇒ seen
    prova("FAULT seen: 2 s without frames ⇒ still of 2 s", 1.9 <= pl <= 2.1, "%.3f s" % pl)
    pl = pausa_piu_lunga([1.0, 1.1], 2.0, 7.0)
    prova("FAULT seen: video stuck since before the window ⇒ whole still", pl >= 5.9,
          "%.1f s" % pl)

    print("── the input checks")
    st = "ls -la ~/prova16 #k3\nfind /usr/share -name '*.png' | head -n 60 #k4\n"
    prova("history: the exact line is there", L.storia_contiene(st, "ls -la ~/prova16 #k3"))
    # ⛔ FAULT seen on 27 Sep (LXQt): Del + Enter never deleted — the
    #   pcmanfm-qt dialog has «No» as default.  ⇒ Shift+Del and «y».
    pc = {s: L.piano_cancella(s) for s in ("gnome", "kde", "xfce", "lxqt")}
    prova("FAULT seen: on LXQt deletion is Shift+Del and the answer «y», never Enter",
          pc["lxqt"][:3] == (["Shift"], "Delete", "y") and pc["lxqt"][4] is True, str(pc["lxqt"]))
    prova("on the other desktops Del, and Enter only if needed",
          all(pc[s] == ([], "Delete", "Enter", 2.5, False) for s in ("gnome", "kde", "xfce")))
    # ⛔ FAULT: a character lost on the way ⇒ KO
    prova("FAULT seen: a lost character ⇒ KO",
          not L.storia_contiene(st, "ls -la ~/prova16 #k4")
          and not L.storia_contiene("ls -la ~/prova1 #k3\n", "ls -la ~/prova16 #k3"))
    # ⛔ FAULT seen on 27 Sep (LXQt): qterminal without SHELL opened dash ⇒ the
    #   bash history was never written, «first line NOT arrived» three times
    ps = ("263 255 lxqt-session\n900 263 qterminal\n905 900 dash\n910 263 pcmanfm-qt\n"
          "1000 263 gnome-terminal-\n1001 1000 bash\n")
    prova("FAULT seen: under qterminal there is dash, and it shows",
          L.shell_sotto(ps, "qterminal") == ["dash"], str(L.shell_sotto(ps, "qterminal")))
    prova("under gnome-terminal-server (name cut at 15) there is bash",
          L.shell_sotto(ps, "gnome-terminal") == ["bash"])
    prova("terminal absent ⇒ no shell, not an error",
          L.shell_sotto(ps, "konsole") == [] and L.shell_sotto("", "qterminal") == []
          and L.shell_sotto("crooked line\n", "qterminal") == [])
    prova("on LXQt qterminal is launched with explicit bash",
          L.APP["lxqt"]["term"][0] == "qterminal -e bash")
    q = L.leggi_quaderno("1727.500 carica testo 0 9000\n1727.900 scroll testo 1200 9000\n"
                         "rotta\n1728.1 video yt t=12.40 stato=1 q=hd2160 livelli=hd2160,hd1440\n")
    prova("notebook: three good lines, the broken one discarded", len(q) == 3 and q[1][1] == "scroll"
          and q[1][2] == ["testo", "1200", "9000"], str(q))
    v = L.leggi_video(q[2][2])
    prova("video: t, state, quality", v.get("t") == 12.4 and v.get("stato") == 1
          and v.get("q") == "hd2160", str(v))
    prova("video source: YouTube and file", L.fonte_video("https://www.youtube.com/watch?v=LXb3EKWsInQ")
          == ("yt", "LXb3EKWsInQ") and L.fonte_video("file:///rete11/v.mp4") == ("file", "/rete11/v.mp4")
          and L.fonte_video("ftp://x")[0] is None)

    print("── the text field of the local page (A)")
    pag = L.pagine_a()
    prova("the A pages do not take the focus away from the field by themselves",
          not any(L.campo_lascia_da_solo(h) for h in pag.values()))
    prova("the field is left with Esc and it says so («lascia»)",
          all("'Escape'" in pag[n + ".html"] and "manda('lascia '" in pag[n + ".html"]
              for n in L.PAGINE_A))
    # ⛔ FAULT: the earlier page (blur at 1.5 s from the last key) ⇒ seen
    vecchia = pag["testo.html"].replace(
        "tN = setTimeout(", "tB = setTimeout(() => nota.blur(), 1500); tN = setTimeout(")
    prova("FAULT seen: the timed blur in the page ⇒ recognised",
          L.campo_lascia_da_solo(vecchia))
    e_ok = (1727.5, "testo", ["testo", "alfa", "rete", "server"])
    prova("typed phrase = phrase in the field ⇒ ok", L.frase_nel_campo(e_ok, "alfa rete server"))
    # ⛔ FAULT: the letters after a long pause ended up outside the field ⇒ KO
    e_ko = (1727.5, "testo", ["testo", "alfa", "re"])
    prova("FAULT seen: lost letters ⇒ KO", not L.frase_nel_campo(e_ko, "alfa rete server"))

    print("── the time of the gestures (from the return of the call)")
    ore = ore_dei_tasti(100.0, [200, 300, 500])
    prova("three keys of 200/300/500 ms returned at 100 s ⇒ 99.0 / 99.2 / 99.5",
          [round(x, 3) for x in ore] == [99.0, 99.2, 99.5], str(ore))
    # ⛔ FAULT: Marionette 2 s late: the paint of the key arrives at
    #   100.05 s; with the time SCHEDULED from the departure (97.0) the freeze is ~3 s,
    #   with the time from the return it is ~0.55 s
    programmate = [97.0, 97.2, 97.5]
    at_vecchie, _ = attese_impulsi(programmate[:1], [100.05], 101.0)
    at_nuove, _ = attese_impulsi(ore[:1], [100.05], 101.0)
    prova("FAULT seen: Marionette's delay does NOT end up in the freeze",
          at_vecchie[0] > 2.5 and at_nuove[0] < 1.2,
          "before %.2f s, now %.2f s" % (at_vecchie[0], at_nuove[0]))

    print("── the time of the gestures (from the page)")
    # ⛔ FAULT seen on 7 Oct (fasi/20 §3-bis.2, intel-f20-fhd-xfce): Marionette holds back
    #   the chain 1.0 s AFTER the last key.  Real keys at 100.0/100.2/100.5, echo painted
    #   30 ms after each, the blinking cursor at 102.0; the chain returns at 102.0
    #   instead of 101.0 ⇒ the estimate puts every key 1 s after its echo.
    veri = [100.0, 100.2, 100.5]
    dipinti = [100.03, 100.23, 100.53, 102.0]
    stime = ore_dei_tasti(102.0, [200, 300, 500])
    at_stime, _ = attese_impulsi(stime, dipinti, 103.0)
    gesti = [[int(x * 1000), "k", c] for x, c in zip(veri, "abc")]
    allineate = allinea_impulsi([(t, ("k", c)) for t, c in zip(stime, "abc")], gesti)
    at_pagina, _ = attese_impulsi(allineate, dipinti, 103.0)
    prova("FAULT seen: with the held-back Marionette estimate the freeze is ~1 s",
          max(at_stime) > 0.9, "%.2f s" % max(at_stime))
    prova("with the page's time Marionette's delay does NOT become a freeze",
          max(at_pagina) < 0.05 and [round(x, 3) for x in allineate] == veri,
          "%.3f s, times %s" % (max(at_pagina), allineate))
    # a key the page never received stays an impulse (at the estimated time) ⇒ real freeze
    persi = allinea_impulsi([(t, ("k", c)) for t, c in zip(stime, "abc")], gesti[:2])
    at_persi, ap_persi = attese_impulsi(persi, dipinti[:2], 108.0)
    prova("FAULT seen: a key that never reached the page stays a freeze",
          persi[2] == stime[2] and max(at_persi) > 5.0, "%s %s" % (at_persi, ap_persi))
    al = allinea_impulsi([(10.0, ("k", "x")), (10.3, ("k", "")), (10.6, ("p", "")), (10.9, ("w", ""))],
                         [[9800, "k", "y"], [9850, "k", "x"], [10100, "k", "Enter"],
                          [10400, "p", ""], [10700, "w", ""], [10750, "w", ""]])
    prova("every gesture with its kind and, for a character, with its key",
          [round(x, 2) for x in al] == [9.85, 10.1, 10.4, 10.7], str(al))
    prova("no probe ⇒ the earlier estimates", allinea_impulsi([(5.0, ("k", "a"))], None) == [5.0])
    prova("an expected Enter does not take the letters typed without a wait before it",
          allinea_impulsi([(10.5, ("k", ""))], [[10000, "k", "l"], [10100, "k", "s"],
                                                [10200, "k", "Enter"]]) == [10.2])
    prova("a gesture from well BEFORE the estimate is not its own",
          allinea_impulsi([(50.0, ("k", "a"))], [[20000, "k", "a"]]) == [50.0])
    prova("a gesture well AFTER the estimate is not its own",
          allinea_impulsi([(5.0, ("k", "a"))], [[9000, "k", "a"]]) == [5.0])

    print("── the birth")
    prova("green desktop ⇒ ok", esito_nascita(True, False) == ("ok", None))
    prova("degenerate at the cap ⇒ «degenere»", esito_nascita(False, True)[0] == "degenere")
    es, nota = esito_nascita(False, False)
    prova("not checked ⇒ ok with the note «not measured»", es == "ok" and "not measured" in nota)
    prova("the degenerate cap is the FAIL threshold of §9 (15 s)", TETTO_DEGENERE_S == 15)
    prova("with the first frame the actor WORKS (even degenerate)",
          lavora_dopo_nascita({"primo_fotogramma_ms": 1, "esito": "degenere"})
          and lavora_dopo_nascita({"primo_fotogramma_ms": 1, "esito": "ok"}))
    # ⛔ FAULT: without first frame, or refused ⇒ does not work (it is not in session)
    prova("FAULT seen: no frame or refusal ⇒ does not work",
          not lavora_dopo_nascita({"primo_fotogramma_ms": None, "esito": "nessun_fotogramma"})
          and not lavora_dopo_nascita({"esito": "rifiuto"}))

    print("── the window in the photo")
    try:
        from PIL import Image, ImageDraw
        a = Image.new("RGB", (960, 540), (0, 0, 0))
        ImageDraw.Draw(a).rectangle([880, 0, 930, 12], fill=(200, 200, 200))    # clock
        b = a.copy()
        dr = ImageDraw.Draw(b)
        dr.rectangle([880, 0, 930, 12], fill=(90, 90, 90))                       # the clock changes
        dr.rectangle([200, 100, 700, 420], outline=(220, 220, 220), width=3)     # dark window
        dr.rectangle([200, 100, 700, 130], fill=(60, 60, 200))                   # its title bar
        dr.text((220, 200), "user@host:~$ ls", fill=(200, 200, 200))
        r = L.rett_finestra(a, b)
        prova("dark window on black background found (%s)" % (r,), r is not None and
              abs(r[0] - 200) <= 16 and abs(r[1] - 100) <= 16 and abs(r[2] - 700) <= 16
              and abs(r[3] - 420) <= 16)
        c = a.copy()
        ImageDraw.Draw(c).rectangle([880, 0, 930, 12], fill=(90, 90, 90))
        # ⛔ FAULT: only the clock changes ⇒ no window
        prova("FAULT seen: only the clock changes ⇒ no window",
              L.rett_finestra(a, c) is None)
    except ImportError:
        prova("PIL is there", False)

    print("── users, profiles, browsers")
    prof = "".join(L.profilo_di(n) for n in range(1, 17))
    prova("profiles 1..16 = ABCD×4", prof == "ABCD" * 4, prof)
    br = [L.browser_di(n) for n in range(1, 17)]
    prova("odd Firefox, even Chrome", all(b == ("firefox" if n % 2 else "chrome")
                                             for n, b in zip(range(1, 17), br)))
    sg = re.compile(r"^c[0-9]+b?u[0-9]+$")
    nomi = [L.inquilino_di(n) for n in range(1, 17)]
    prova("tenants recognised by the clean-up and all different",
          all(sg.match(x) for x in nomi) and len(set(nomi)) == 16, "%s … %s" % (nomi[0], nomi[-1]))
    porte = {L.porta_interna(d, n) for d in DESKTOP for n in range(1, 17)}
    prova("internal ports all different (4 desktops × 16)", len(porte) == 64)
    print("⛔ CERTIFICATION FAILED (%d)" % len(guai) if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE ENVIRONMENT — before importing the suite (it reads REMOTIX_SUL_SERVER at import)
# ═══════════════════════════════════════════════════════════════════════════
def ambiente(o):
    u = os.getuid()
    os.environ.update({
        "XDG_RUNTIME_DIR": "/run/user/%d" % u,
        "WAYLAND_DISPLAY": o.wayland,
        "REMOTIX_SCHERMO_ANNIDATO": "1",
        "REMOTIX_SUL_SERVER": "1",
        "MOZ_ENABLE_WAYLAND": "1",
        "REMOTIX_CHROME_OPZIONI": "--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                                  "--disable-renderer-backgrounding --disable-background-timer-throttling "
                                  # ⭐ the extra options of the climb (e.g. --render-node-override)
                                  + os.environ.get("REMOTIX_16_CHROME_IN_PIU", ""),
    })
    os.environ["REMOTIX_CHROME_OPZIONI"] = os.environ["REMOTIX_CHROME_OPZIONI"].strip()
    os.environ.pop("DISPLAY", None)


def argomenti():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--scatola", choices=DESKTOP)
    a.add_argument("--utente", type=int)
    a.add_argument("--wayland", help="the socket of this user's labwc (wayland-K)")
    a.add_argument("--dir", help="the folder of the climb's evidence")
    a.add_argument("--seme", default="0")
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    a.add_argument("--porte-base", type=int, default=0,
                   help="Firefox P, Chrome P+1 (by default 9700 + 4·N)")
    a.add_argument("--video", default="",
                   help="D users: YouTube URL, or a file (path INSIDE the box, /rete11/…)")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--tetto-s", type=int, default=60, help="cap of the access and of the first frame")
    o = a.parse_args()
    if o.certifica:
        return o
    for k in ("scatola", "utente", "wayland", "dir"):
        if getattr(o, k) in (None, ""):
            a.error("--%s is needed" % k)
    if not 1 <= o.utente <= 99:
        a.error("--utente between 1 and 16 (up to 99 for overload)")
    if not o.porte_base:
        o.porte_base = 9700 + 4 * o.utente
    return o


# ═══════════════════════════════════════════════════════════════════════════
#  THE ACTOR
# ═══════════════════════════════════════════════════════════════════════════
class Attore:
    def __init__(self, o, S, G2):
        self.o, self.S, self.G2 = o, S, G2
        self.C21 = S.C21
        self.n = o.utente
        self.profilo = L.profilo_di(self.n)
        self.browser = L.browser_di(self.n)
        self.chi = L.inquilino_di(self.n)
        self.parola = "c16-" + secrets.token_hex(8)
        self.porta_interna = L.porta_interna(o.scatola, self.n)
        self.ritmo = Ritmo(o.seme, self.n)
        self.cartella = os.path.join(o.dir, "utente-%02d" % self.n)
        os.makedirs(self.cartella, exist_ok=True)
        self.f_stato = open(os.path.join(self.cartella, "stato.jsonl"), "a", buffering=1)
        self.f_eventi = open(os.path.join(self.cartella, "eventi.jsonl"), "a", buffering=1)
        self.eventi_finestra = []
        self.errori_finestra = []
        self.giro_eco_finestra = []
        self.impulsi = []
        self.impulsi_pendenti = []       # (estimated time, gesture): the page tells the true time
        self.dipinti_t = []
        self.entrato = False
        self.muti = 0
        self.s = self.sc = self.g = None
        self.geo = None
        self.desktop = (o.largo, o.alto)
        self.mani = None
        self.lavoro = None
        self.voglio_foto = False
        self.fermati = False
        self.prossimo_stato = 0.0
        self.azioni = {}
        self.fatte_finestra = 0
        self.verifiche = {"ok": 0, "ko": 0}
        self.ver_finestra = []
        self.reg_da = 0
        self.prec = None                   # (time, counters, diary) of the previous row
        self.foto_size = None

    # -- the rows --------------------------------------------------------------
    #  stato.jsonl: ONLY the state rows (every 5 s), in the schema that
    #  16-classifica.py reads; the events go into eventi.jsonl AND into the next state
    #  row (field `eventi`), so they are not lost and do not dirty the windows.
    def _testa(self, evento):
        return {"t": round(time.time(), 3), "utente": self.n, "profilo": self.profilo,
                "browser": self.browser, "versione": getattr(self, "esiti", None)
                and self.esiti.versione, "inquilino": self.chi, "evento": evento}

    def riga(self, evento, **campi):
        r = self._testa(evento)
        r.pop("evento")
        r.update(campi)
        self.f_stato.write(json.dumps(r, ensure_ascii=False) + "\n")

    def evento(self, tipo, **campi):
        r = self._testa(tipo)
        r.update(campi)
        self.f_eventi.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.eventi_finestra.append(r)
        print("   [%02d %s] %s %s" % (self.n, self.profilo, tipo,
                                    json.dumps(campi, ensure_ascii=False)[:240]), flush=True)

    def conta(self, azione):
        self.azioni[azione] = self.azioni.get(azione, 0) + 1
        self.fatte_finestra += 1

    def verifica(self, azione, ok, lat_ms, det=""):
        self.conta(azione)
        self.verifiche["ok" if ok else "ko"] += 1
        v = {"azione": azione, "ok": bool(ok),
             "latenza_ms": None if lat_ms is None else round(lat_ms), "det": det}
        self.ver_finestra.append(v)
        if not ok:
            print("   [%02d %s] ⚠ input NOT verified: %s" % (self.n, self.profilo, v), flush=True)

    def impulso(self, t, gesto=None):
        """An input that MUST change the image (a typed character, an Enter
        in the terminal, a click on a link, a notch that scrolls).
        `gesto` (kind, key): ("k", character), ("p", "") click, ("w", "") notch;
        with it the page decides the time (`allinea_impulsi`), `t` is the estimate."""
        self.impulsi_pendenti.append((t, gesto))

    # -- the heart: signals, photos, state ------------------------------------
    def cuore(self):
        """⭐ The SAFE point: here (and only here) the SIGTERM becomes `Fine`.
        ⛔ `[M]` 25 Sep 2026: interrupted in the middle of a call, Marionette
        was left with the pending answer and the next call read that one —
        the page's log on exit was no longer saved."""
        if self.fermati:
            raise Fine("signal")
        if self.voglio_foto:
            self.voglio_foto = False
            self.scatta()
        if time.time() >= self.prossimo_stato:
            self.in_ritardo = time.time() - self.prossimo_stato if self.prossimo_stato else 0.0
            self.scrivi_stato()
            # ⚠ the next one in 5 s FROM NOW, not on the grid: after a late
            #   row, a second one 0.7 s apart would be for the
            #   classifier «5 s without frames» (`[M]` 25 Sep, user D)
            self.prossimo_stato = time.time() + 5.0

    def dorme(self, secondi):
        fine = time.time() + max(0.0, secondi)
        while True:
            self.cuore()
            resto = fine - time.time()
            if resto <= 0:
                return
            time.sleep(min(0.25, resto))

    def arma_sonda(self):
        """The paint probe in the page (every 10 ms: the time of every change)."""
        try:
            with self.G2.tetto(20, "the probe"):
                self.g.js(self.S.VERI._inietta(SONDA_DIPINTI))
            return True
        except Exception as e:                   # noqa: BLE001
            self.evento("errore", testo="paint probe not armed: %s" % str(e)[:200])
            return False

    def scrivi_stato(self):
        if self.g is None:
            return
        try:
            with self.G2.tetto(20, "the diary"):
                p = self.g.js(JS_DIARIO, self.reg_da) or {}
        except Exception as e:                   # noqa: BLE001
            p = {"errore": str(e)[:200]}
        ora = time.time()
        riga_d = p.get("riga")
        diario = leggi_riga_diario(riga_d)
        conti = conti_classifica(p.get("conti"), diario)
        errori = []
        if p.get("errore"):
            errori.append("the page does not answer the bench: " + p["errore"])
            self.muti += 1
        else:
            self.muti = 0
        # ⭐ the drop: after entry the page is no longer in session
        caduta = bool(self.entrato and not p.get("errore") and not p.get("sessione"))
        if caduta:
            errori.append("the page is no longer in session (screen %s, outcome «%s»)"
                          % (p.get("schermo"), p.get("esito")))
        # ⭐ the longest freeze: from the paint times and the impulses
        pt = [x / 1000.0 for x in (p.get("dipinti_t") or [])]
        self.dipinti_t = [x for x in self.dipinti_t if x > ora - 30] + pt
        # ⭐ the impulses at the time the PAGE received the gesture
        allineati = allinea_impulsi(self.impulsi_pendenti, p.get("gesti_t"))
        dalla_pagina = sum(1 for a, (st, _g) in zip(allineati, self.impulsi_pendenti) if a != st)
        tot_impulsi = len(self.impulsi_pendenti)
        self.impulsi += allineati
        self.impulsi_pendenti = []
        blocco, lavoro = None, False
        if self.profilo == "D":
            if self.video_in_corso():
                blocco = pausa_piu_lunga(self.dipinti_t, self.prec[0] if self.prec else ora - 5, ora)
                lavoro = True
        else:
            attese, self.impulsi = attese_impulsi(self.impulsi, self.dipinti_t, ora)
            if attese:
                blocco, lavoro = max(attese), True
        campi = {"conti": conti, "diario": riga_d, "diario_letto": diario,
                 "giro": p.get("giro"), "giro_eco": self.giro_eco_finestra,
                 "input": self.ver_finestra,
                 "blocco_max_ms": None if blocco is None else round(blocco * 1000),
                 "lavoro": lavoro, "impulsi_pagina": [dalla_pagina, tot_impulsi],
                 "caduta": caduta, "errori": errori + self.errori_finestra,
                 "sessione": p.get("sessione"), "schermo": p.get("schermo"),
                 "fuoco": p.get("fuoco"), "visibile": p.get("visibile")}
        if self.prec:
            dt = ora - self.prec[0]
            dc, az = differenze(self.prec[1], conti, CONTI_DELTA)
            campi["delta"] = dict(dc, s=round(dt, 2))
            if dc.get("dipinti") is not None and dt > 0:
                campi["dipinti_s"] = round(dc["dipinti"] / dt, 2)
            if az:
                campi["azzerati"] = az
        self.prec = (ora, conti)
        if p.get("nuove"):
            campi["pagina"] = p["nuove"]
        if isinstance(p.get("lung"), int):
            self.reg_da = p["lung"]
        # ⚠ how late this row arrived (a long gesture holds it back)
        campi["in_ritardo_s"] = round(getattr(self, "in_ritardo", 0.0), 2)
        campi.update({"azioni": dict(self.azioni), "azioni_finestra": self.fatte_finestra,
                      "verifiche": dict(self.verifiche)})
        if self.lavoro is not None:
            try:
                campi["dettagli_lavoro"] = self.lavoro.extra()
            except Exception as e:               # noqa: BLE001
                campi["dettagli_lavoro"] = {"errore": str(e)[:200]}
        if self.eventi_finestra:
            campi["eventi"] = self.eventi_finestra
        self.fatte_finestra = 0
        self.ver_finestra = []
        self.errori_finestra = []
        self.eventi_finestra = []
        self.giro_eco_finestra = []
        self.riga("stato", **campi)

    def video_in_corso(self):
        v = getattr(self.lavoro, "ultimo_video", None) or {}
        return self.entrato and v.get("stato") == 1

    # -- the photos -------------------------------------------------------------
    def png(self):
        self.G2.davanti(self.g)
        with self.G2.tetto(30, "the photo"):
            return self.C21.foto_piena(self.g)

    def scatta(self):
        t = time.time()
        try:
            png = self.png()
        except Exception as e:                   # noqa: BLE001
            self.evento("foto", ok=False, perche=str(e)[:200])
            return
        if not png:
            self.evento("foto", ok=False, perche="the canvas cannot be photographed")
            return
        f = os.path.join(self.cartella, "foto-%d.png" % int(t * 1000))
        with open(f, "wb") as h:
            h.write(png)
        self.evento("foto", ok=True, file=f, ms=round((time.time() - t) * 1000))

    def foto_pil(self):
        from PIL import Image
        try:
            png = self.png()
        except Exception:                        # noqa: BLE001
            return None
        if not png:
            return None
        im = Image.open(io.BytesIO(png)).convert("RGB")
        self.foto_size = im.size
        return im

    def foto_al_desktop(self, r):
        if not r or not self.foto_size or not self.geo:
            return None
        pw, ph = self.foto_size
        x0, y0 = self.C21.dalla_foto_al_desktop(self.geo, pw, ph, r[0], r[1])
        x1, y1 = self.C21.dalla_foto_al_desktop(self.geo, pw, ph, r[2], r[3])
        tl, ta = self.desktop
        return (max(0, x0), max(0, y0), min(tl, x1), min(ta, y1))

    def preferenze_interne(self):
        return self.C21.PREFERENZE

    # -- the access ------------------------------------------------------------
    def entra(self):
        s, VERI = self.s, self.S.VERI
        n = {"inquilino": self.chi, "browser": self.browser, "versione": self.esiti.versione,
             "scatola": self.o.scatola, "misura": [self.o.largo, self.o.alto]}
        ok, m = s.pr.apri()
        if not ok:
            n.update(esito="pagina_non_aperta", motivo="the page does not open: " + m)
            return n
        t0 = time.time()
        r = s.g.js(VERI.JS_ENTRA, self.chi, self.parola)
        if r != "mandato":
            n.update(esito="modulo_non_compilato", motivo="the form cannot be filled in: %s" % r)
            return n
        ammesso = primo = None
        st = {}
        while time.time() < t0 + self.o.tetto_s:
            st = s.pr.stato()
            ora = time.time()
            # ⚠ both forms of the page's outcome: the old (Italian) page of the running
            #   campaign and the new (English) one
            if ammesso is None and st.get("sessione") and st.get("esito_classe") == "bene" \
                    and (st.get("esito") or "").startswith(("Ammesso", "Admitted")):
                ammesso = ora
            if st.get("esito_classe") == "male" and st.get("esito"):
                n.update(esito="rifiuto", motivo="refusal: «%s»" % st["esito"],
                         accesso_ms=round(t0 * 1000))
                return n
            if (st.get("dipinti") or 0) > 0:
                primo = ora
                ammesso = ammesso or ora
                break
            if self.fermati:
                raise Fine("signal")
            time.sleep(0.1)
        # ⭐ in the schema of 16-classifica: times in ms from the epoch, and the duration separately
        n["accesso_ms"] = round(t0 * 1000)
        n["ammesso_ms"] = round(ammesso * 1000) if ammesso else None
        n["primo_fotogramma_ms"] = round(primo * 1000) if primo else None
        n["nascita_ms"] = round((primo - t0) * 1000) if primo else None
        n["ammissione_ms"] = round((ammesso - t0) * 1000) if ammesso else None
        if not primo:
            n.update(esito="nessun_fotogramma", motivo="no frame in %d s (outcome «%s»)"
                     % (self.o.tetto_s, st.get("esito")))
            return n
        # ⚠ the «not degenerate» judgement photographs up to the cap: `[M]` 25 Sep,
        #   xfce has a BLACK background and waited 60 s for it ⇒ short cap, and the
        #   dark but alive desktop is recognised by `desktop_scuro_ma_vivo`.
        # ⛔ The cap is the FAIL threshold of §9: «degenere» only if it STILL is at
        #   15 s from ACCESS (not 8 s from the first frame: under load the
        #   Plasma splash lasts longer, and it is not a broken desktop).  If the
        #   first frame arrives already beyond, one last look of 3 s.
        tetto, self.o.tetto_s = self.o.tetto_s, max(3, int(math.ceil(
            t0 + TETTO_DEGENERE_S - time.time())))
        try:
            e, m, st2 = s.pr.primo_fotogramma()
        finally:
            self.o.tetto_s = tetto
        e, m = self.S.C20V.desktop_scuro_ma_vivo(e, m, st2)
        n["desktop_vivo_ms"] = round((time.time() - t0) * 1000)
        n["esito"], nota = esito_nascita(e == self.S.VERDE, e == self.S.ROSSO)
        if nota:
            n["nota"] = nota
        n["motivo"] = m
        return n

    # -- everything -------------------------------------------------------------
    def corri(self):
        o, S = self.o, self.S
        self.esiti = S.Esiti(o)
        S.MODELLO_INQUILINO = re.compile(r"^c16[0-9]{3}u[0-9]+$")
        self.s = S.Sessione(o, "%03d" % self.n, self.esiti, chi=self.chi, parola=self.parola)
        self.sc = self.s.sc
        self.evento("inizio", inquilino=self.chi, scatola=o.scatola, wayland=o.wayland,
                    porte_base=o.porte_base, seme=o.seme, porta_interna=self.porta_interna,
                    misura=[o.largo, o.alto], video=o.video or None, pid=os.getpid())
        codice = 2
        try:
            self.s.__enter__()                   # creates the tenant, turns on the browser
            self.g = self.s.g
            self.lavoro = L.LAVORI[self.profilo](self)
            self.lavoro.prepara()
            nascita = self.entra()
            with open(os.path.join(self.cartella, "nascita.json"), "w") as f:
                json.dump(nascita, f, ensure_ascii=False, indent=1)
            self.evento("nascita", **nascita)
            if not lavora_dopo_nascita(nascita):
                codice = 1
                self.aspetta_la_fine("access failed")
                return codice
            # ⭐ a «degenerate» or unchecked desktop does have the frames: the
            #   session is there and the actor WORKS — the load is not removed (the
            #   birth is judged by the classification, from nascita.json)
            self.entrato = True
            self.arma_sonda()
            self.geo = self.s.geometria()
            self.desktop = (self.geo["tl"], self.geo["ta"])
            self.mani = Mani(self)
            print("   [%02d] wake-up: %s" % (self.n, self.C21.sveglia(self.g, self.geo)), flush=True)
            # ⭐ THE WELCOME CLICK, on an empty spot of the desktop, before any
            #   application: it is the user gesture that wakes up the page's
            #   audio.  ⛔ `[M]` 25 Sep, user D without it: 6090 blocks received,
            #   0 played, `ctx suspended` (the access is a form filled in by the
            #   bench, not a gesture; the wake-up's ESC does not activate).
            self.dorme(1.0)
            self.mani.clic(self.desktop[0] * 0.55, self.desktop[1] * 0.55)
            self.dorme(1.0)
            codice = 0
            for prova in range(3):
                ok, m = self.lavoro.avvia()
                self.evento("applicazione", ok=ok, testo=m, tentativo=prova + 1)
                if ok:
                    break
                self.dorme(10)
            else:
                codice = 1
                self.aspetta_la_fine("the application does not start")
                return codice
            errori = 0
            while True:
                try:
                    t_passo = time.time()
                    self.lavoro.passo()
                    if time.time() - t_passo > 45 and self.profilo != "D":
                        print("   [%02d] ⚠ a step of %.0f s" % (self.n, time.time() - t_passo),
                              flush=True)
                    errori = 0
                except Fine:
                    raise
                except Exception as e:           # noqa: BLE001
                    errori += 1
                    self.errori_finestra.append("%r" % e)
                    self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-600:],
                                di_fila=errori)
                    self.dorme(min(30, 2 * errori))
        except Fine:
            pass
        except Exception as e:                   # noqa: BLE001
            self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-800:], fatale=True)
            codice = 2
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.chiudi()
        return codice

    def aspetta_la_fine(self, perche):
        """⚠ A user that did not manage to enter stays available
        (state, photo) until the orchestrator stops it: it does not disappear."""
        self.evento("in_attesa", perche=perche)
        while True:
            self.dorme(5)

    def chiudi(self):
        try:
            if self.g is not None:
                try:
                    self.scrivi_stato()
                except Exception:                # noqa: BLE001
                    pass
                try:
                    with self.G2.tetto(20, "the page's log"):
                        reg = self.g.js("const r=document.getElementById('registro');"
                                        "return r ? r.textContent : '';") or ""
                    with open(os.path.join(self.cartella, "registro-pagina.txt"), "w") as f:
                        f.write(reg)
                except Exception:                # noqa: BLE001
                    pass
                try:
                    self.s.salva_console()
                except Exception:                # noqa: BLE001
                    pass
        finally:
            try:
                self.s.__exit__(None, None, None)     # closes the browser and CLEARS
            except Exception as e:               # noqa: BLE001
                print("   ⚠ exit: %s" % e, flush=True)
            _c, t = self.sc.dentro("id %s >/dev/null 2>&1 && echo RESTA || echo via" % self.chi, 30)
            self.evento("fine", sgomberato=(t or "").strip().endswith("via"), azioni=self.azioni,
                        verifiche=self.verifiche)
            self.f_stato.close()
            self.f_eventi.close()


# ═══════════════════════════════════════════════════════════════════════════
#  THE HANDS — REAL input from the browser, coordinates of the remote DESKTOP
# ═══════════════════════════════════════════════════════════════════════════
class Mani:
    def __init__(self, att):
        self.a = att
        self.G2 = att.G2
        self.pos = None

    @property
    def g(self):
        return self.a.g

    def vetro(self, X, Y):
        tl, ta = self.a.desktop
        X, Y = max(1, min(tl - 2, X)), max(1, min(ta - 2, Y))
        return self.a.C21.dal_desktop_al_vetro(self.a.geo, X, Y)

    def _cammino(self, X, Y):
        """The pointer gets there in steps, not all at once."""
        vx, vy = self.vetro(X, Y)
        R = self.a.ritmo
        passi = []
        if self.pos:
            n = R.intero(3, 8)
            for i in range(1, n):
                f = i / float(n)
                passi += [("muovi", self.pos[0] + (vx - self.pos[0]) * f,
                           self.pos[1] + (vy - self.pos[1]) * f), ("pausa", R.intero(12, 30))]
        passi += [("muovi", vx, vy), ("pausa", R.intero(60, 180))]
        self.pos = (vx, vy)
        return passi

    def muovi(self, X, Y):
        self.G2.mouse(self.g, self._cammino(X, Y))
        return time.time()

    # ⭐ Every gesture returns the time of the decisive event (the press, the first
    #   notch, the key), derived from the RETURN of the call to the browser minus the
    #   pauses scheduled AFTER it.  ⛔ `[M]` 25 Sep: the time after the
    #   call, without removing the pauses, put the bash history 200 ms
    #   «before» the Enter; ⛔ review 25 Sep: the time BEFORE the call
    #   put Marionette/CDP's delay under load (and the bringToFront)
    #   in the product's «freeze».
    def _wd(self, azioni):
        """Marionette: PerformActions ⇒ the time of its RETURN (before the
        ReleaseActions, which has nothing to do with the gesture)."""
        self.g.m.chiama("WebDriver:PerformActions", {"actions": azioni})
        t = time.time()
        self.g.m.chiama("WebDriver:ReleaseActions")
        return t

    def clic(self, X, Y, bottone=0, atteso=False):
        R = self.a.ritmo
        self.G2.mouse(self.g, self._cammino(X, Y))
        pausa = R.intero(50, 120)
        if hasattr(self.g, "cdp"):
            self.G2.mouse(self.g, [("muovi",) + tuple(self.pos), ("giu", bottone, 1),
                                   ("pausa", pausa), ("su", bottone, 1)])
            t = time.time() - pausa / 1000.0
        else:
            x, y = int(round(self.pos[0])), int(round(self.pos[1]))
            t = self._wd([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                           "actions": [{"type": "pointerMove", "x": x, "y": y, "origin": "viewport",
                                        "duration": 0},
                                       {"type": "pointerDown", "button": bottone},
                                       {"type": "pause", "duration": pausa},
                                       {"type": "pointerUp", "button": bottone}]}])
            t -= pausa / 1000.0
        if atteso:
            self.a.impulso(t, ("p", ""))
        self.a.conta("clic_mouse")
        return t

    def rotella(self, X, Y, tacche, atteso=False):
        """`tacche` > 0 down, < 0 up; one notch = 120 (a real wheel)."""
        self.muovi(X, Y)
        vx, vy = self.pos
        R = self.a.ritmo
        dy = 120 if tacche > 0 else -120
        t = None
        if hasattr(self.g, "cdp"):
            self.G2.davanti(self.g)
            with self.G2.tetto(60, "the wheel"):
                for _ in range(abs(tacche)):
                    self.g.cdp.chiama("Input.dispatchMouseEvent", type="mouseWheel", x=vx, y=vy,
                                      deltaX=0, deltaY=dy)
                    t = t or time.time()             # the first notch, at the return
                    time.sleep(R.intero(40, 160) / 1000.0)
        else:
            az, pause = [], 0
            for _ in range(abs(tacche)):
                p = R.intero(40, 160)
                pause += p
                az += [{"type": "scroll", "x": int(vx), "y": int(vy), "deltaX": 0, "deltaY": dy,
                        "origin": "viewport", "duration": 0},
                       {"type": "pause", "duration": p}]
            t = self._wd([{"type": "wheel", "id": "rotella", "actions": az}]) - pause / 1000.0
        t = t or time.time()
        if atteso:
            self.a.impulso(t, ("w", ""))
        self.a.conta("tacche")
        return t

    def premi(self, nome, atteso=False):
        """One key: down, pause, up, pause (like `G2.tasti`)."""
        P = self.G2.PAUSA_MS
        v = self.G2.SPECIALI[nome][3] if nome in self.G2.SPECIALI else nome
        if hasattr(self.g, "cdp") or v is None:
            self.G2.tasti(self.g, self.G2.premi(nome))
            t = time.time() - 2 * P / 1000.0
        else:
            t = self._wd([{"type": "key", "id": "tastiera", "actions": [
                {"type": "keyDown", "value": v}, {"type": "pause", "duration": P},
                {"type": "keyUp", "value": v}, {"type": "pause", "duration": P}]}]) - 2 * P / 1000.0
        if atteso:
            self.a.impulso(t, ("k", ""))
        return t

    def combo(self, mod, tasto):
        passi = self.G2.premi(tasto)
        for m in reversed(mod):
            passi = self.G2.col(m, passi)
        t = time.time()
        self.G2.tasti(self.g, passi)
        return t

    def giro(self):
        try:
            with self.G2.tetto(15, "the round"):
                return self.g.js(JS_GIRO)
        except Exception:                        # noqa: BLE001
            return None

    def batti(self, testo, atteso=True, eco=False):
        """Every character a real key, with the person's rhythm.  `atteso`: every
        character must appear (echo) ⇒ it is an impulse for the freeze.  `eco`:
        the character appears AT ONCE (terminal, text field) ⇒ the round samples
        arrived during the typing go into `giro_eco`."""
        g_prima = self.giro() if eco else None
        self._batti(testo, atteso)
        fine = time.time()
        if eco:
            time.sleep(0.4)                      # the echo of the last characters
            self.a.giro_eco_finestra += campioni_nuovi(g_prima, self.giro())
        return fine

    def _batti(self, testo, atteso):
        R = self.a.ritmo
        tempi = [(R.tenuta_ms(), R.battuta_ms()) for _ in testo]
        # ⚠ in pieces of ~1.5 s, with the heart in between: a long line typed in a
        #   single chain held back the state row up to 10 s (`[M]` 25 Sep)
        pezzi, pezzo, dur = [], [], 0.0
        for c, tb in zip(testo, tempi):
            pezzo.append((c, tb))
            dur += max(tb) / 1000.0
            if dur >= 1.5:
                pezzi.append(pezzo)
                pezzo, dur = [], 0.0
        if pezzo:
            pezzi.append(pezzo)
        for i, pz in enumerate(pezzi):
            if i:
                self.a.cuore()
            if hasattr(self.g, "cdp"):
                self.G2.davanti(self.g)
                with self.G2.tetto(30, "the typing"):
                    for c, (ten, bat) in pz:
                        cd, vk = self.G2.codice_di(c)
                        self.g.cdp.chiama("Input.dispatchKeyEvent", type="keyDown", key=c, code=cd,
                                          windowsVirtualKeyCode=vk, text=c, unmodifiedText=c)
                        if atteso:
                            self.a.impulso(time.time(), ("k", c))     # estimate: at the RETURN of the keyDown
                        time.sleep(ten / 1000.0)
                        self.g.cdp.chiama("Input.dispatchKeyEvent", type="keyUp", key=c, code=cd,
                                          windowsVirtualKeyCode=vk)
                        time.sleep(max(0.0, bat - ten) / 1000.0)
            else:
                az, durate = [], []
                for c, (ten, bat) in pz:
                    az += [{"type": "keyDown", "value": c}, {"type": "pause", "duration": int(ten)},
                           {"type": "keyUp", "value": c},
                           {"type": "pause", "duration": int(max(0, bat - ten))}]
                    durate.append(int(ten) + int(max(0, bat - ten)))
                # ⭐ the time of every key from the RETURN of the chain (ore_dei_tasti), not
                #   scheduled from the departure: Marionette's delay is not a freeze
                t_ret = self._wd([{"type": "key", "id": "tastiera", "actions": az}])
                if atteso:
                    for k, (c, _tb) in zip(ore_dei_tasti(t_ret, durate), pz):
                        self.a.impulso(k, ("k", c))
        self.a.conta("tasti")
        return time.time()


# ═══════════════════════════════════════════════════════════════════════════
def main():
    o = argomenti()
    if o.certifica:
        return certifica()
    ambiente(o)
    sys.path.insert(0, SUITE)
    import suite as S                                                 # noqa: E402
    G2 = S._carica("g2scena", os.path.join(SUITE, "15-g2-scena.py"))
    # ⭐ the keys the jobs need and that G2's table lacks
    G2.SPECIALI.setdefault("Delete", ("Delete", "Delete", 46, "", 0))
    G2.SPECIALI.setdefault("Home", ("Home", "Home", 36, "", 0))
    G2.SPECIALI.setdefault("PageDown", ("PageDown", "PageDown", 34, "", 0))
    G2.SPECIALI.setdefault("PageUp", ("PageUp", "PageUp", 33, "", 0))
    # the fields that `Sessione` and the guides of 12-client-veri expect
    o.browser = L.browser_di(o.utente)
    o.guasto = False
    o.visibile = True
    o.porta = 0
    o.evidenze = os.path.join(o.dir, "utente-%02d" % o.utente)
    o.url = "https://%s:%d/" % (o.host, S.PORTE[o.scatola])
    # ⭐ to measure a route of the page (e.g. «?tela=gl», anomaly A1): it is appended
    #   to the address, and declared in the state; empty = the default page
    if os.environ.get("REMOTIX_16_URL_EXTRA"):
        o.url += os.environ["REMOTIX_16_URL_EXTRA"]
    o.scena, o.continuita_s, o.registro_cmd, o.lascia_acceso, o.salva = "viva", 8, "", False, ""
    att = Attore(o, S, G2)

    def _fine(_n, _f):
        att.fermati = True

    def _foto(_n, _f):
        att.voglio_foto = True
    signal.signal(signal.SIGTERM, _fine)
    signal.signal(signal.SIGINT, _fine)
    signal.signal(signal.SIGUSR1, _foto)
    print("⭐ actor %02d · %s · profile %s · %s · %s · %s" % (
        o.utente, o.scatola, att.profilo, o.browser, o.wayland, att.chi), flush=True)
    return att.corri()


if __name__ == "__main__":
    sys.exit(main())
