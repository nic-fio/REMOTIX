#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-d006 — LA MISURA PULITA DI D-006: i buchi dell'audio contati dalla PAGINA, senza orecchio

    python3 15-d006-misura.py --scatola lxqt --browser firefox --quale f013 [--video-worker]
                              [--finestra-s 60] [--guasto] [--evidenze DIR]
    python3 15-d006-misura.py --certifica

PERCHE' ESISTE.  D-006 (Firefox + video: buchi di suono) e' stato visto SOLO con
l'«orecchio» di `15-g4-comune.py`, che sostituisce `AudioContext` e
`AudioNode.prototype.connect`, mette un `AnalyserNode` (FFT 8192) nel percorso
e lo legge ogni 100 ms dal thread principale.  L'utente dice che nell'uso vero
l'audio non ha mai dato problemi ⇒ prima di curare il prodotto si misura SENZA
toccare niente della pagina.

LA MISURA.  Niente orecchio, niente nodi sostituiti, niente timer iniettati.
  Si leggono i conti che la pagina tiene DA SE' (`audio_conti()`, due letture:
  inizio e fine della finestra, una riga di script ciascuna) e se ne fanno le
  differenze:
    · riarmi   ⭐ la metrica: ogni riarmo e' un buco di ALMENO 250 ms (il cuscino
               si rimette da capo, `suona()` in src/pagina.html);
    · tirate, tagliati, scartati_pieno, scartati_tardivi, mancati: accanto;
    · udibile_stima = Δusciti × 20 ms / durata.  ⚠ LIMITE INFERIORE su Firefox:
      `tagliati`/`usciti` si giudicano con `currentTime`, che li' e' stantio, e
      un blocco finito da solo puo' contare come tagliato.
  E la CPU del SERVER nella stessa finestra (`/proc/stat` ogni secondo, tutte le
  cpu: media, p95, il core piu' carico), e — se il banco gira sul server — i
  processi piu' voraci a meta' finestra.  E' il dato per l'ipotesi (b): contesa
  di CPU fra il browser e la sessione che fa video.

LE COMBINAZIONI (una alla volta: ognuna e' un lancio):
    --quale f012   il tono di F-012 (pw-play, 440 Hz), NESSUN video
    --quale f013   il video di F-013 (ffplay 1280x720, 660 Hz), SENZA foto
    --video-worker la pagina con `#video=worker`: decodifica e disegno del video
                   nel worker (interruttore gia' nel prodotto, spento di serie).
                   Il banco VERIFICA dentro la pagina che il worker sia acceso.

GIUDIZIO (per il registro della suite; e' una misura, la tabella conta di piu'):
    PASS  Δriarmi = 0 e Δscartati_pieno = 0 nella finestra
    FAIL  almeno un riarmo (= almeno un buco da 250 ms)
    BLOCKED  contesto audio mai «running», worker chiesto e non acceso, ecc.

GUASTO (--guasto, stessa sessione): si ferma il thread principale della PAGINA
  per 400 ms ogni 2 s (un ciclo occupato iniettato: piu' del cuscino) per 20 s
  ⇒ la stessa misura deve contare riarmi (>= 3).  Se non li conta, la misura e'
  cieca e il sano non vale niente.

USCITA: oltre alle righe SUITE, una riga `MISURA {...}` con tutti i numeri
(scatola, browser, scena, worker, delta, cpu), che si incolla nella tabella.
"""
import importlib.util as _iu
import json
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

QUI = os.path.dirname(os.path.abspath(__file__))


def _modulo(nome, file):
    s = _iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


G4 = _modulo("g4", "15-g4-comune.py")
F12 = _modulo("f012", "15-f012-audio.py")
F13 = _modulo("f013", "15-f013-video.py")

FUNZIONI = ("D-006",)
BLOCCO_S = 0.020           # un blocco audio = 20 ms (RCP §6.3)
CUSCINO_S = 0.250          # AUDIO_CUSCINO_MS: il buco minimo di un riarmo
CONTI = ("ricevuti", "suonati", "riarmi", "tirate", "tagliati", "usciti", "sospesi",
         "scartati_pieno", "scartati_tardivi", "scartati_vecchi", "mancati", "salti_suono")
GUASTO_S = 20.0


def extra(a):
    a.add_argument("--quale", choices=("f012", "f013"), default="f013",
                   help="la scena: f012 tono senza video, f013 video (⚠ non `--scena`: suite.py la riscrive)")
    a.add_argument("--video-worker", action="store_true")
    a.add_argument("--pcm", action="store_true",
                   help="audio in PCM invece di Opus: il banco fa dire alla pagina che il motore "
                        "non decodifica Opus (niente AudioDecoder nel percorso dell'audio)")
    a.add_argument("--nnn", default="906",
                   help="le tre cifre dell'inquilino c15<nnn>u<n> (agenti in parallelo: diverse)")
    a.add_argument("--finestra-s", type=float, default=60.0)
    a.add_argument("--assesta-s", type=float, default=5.0,
                   help="attesa dopo il risveglio, prima della finestra")


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def delta(c0, c1, ms0, ms1, blocco_s=BLOCCO_S):
    """I conti della finestra: differenze + stime.  `ms` = performance.now().
    ⚠ `blocco_s`: 20 ms per Opus, 5 ms per PCM (`[M]` 200 blocchi/s)."""
    d = {k: (c1.get(k) or 0) - (c0.get(k) or 0) for k in CONTI}
    durata = max(1e-3, (ms1 - ms0) / 1000.0)
    d["durata_s"] = round(durata, 1)
    d["udibile_stima_pct"] = round(min(100.0, 100.0 * d["usciti"] * blocco_s / durata), 1)
    d["silenzio_minimo_s"] = round(d["riarmi"] * CUSCINO_S, 2)
    d["contesto"] = c1.get("contesto")
    d["orologio_stantio_ms"] = c1.get("orologio_stantio_ms")   # solo se la pagina lo porta
    return d


def cpu_da_stat(righe):
    """Dalle letture di `grep ^cpu /proc/stat` (blocchi separati da '---'):
    {media, p95, max} del totale e il core piu' carico (media), in %."""
    blocchi, cur = [], {}
    for r in righe:
        r = r.strip()
        if r == "---":
            if cur:
                blocchi.append(cur)
            cur = {}
            continue
        p = r.split()
        if not p or not p[0].startswith("cpu"):
            continue
        v = [int(x) for x in p[1:]]
        idle = v[3] + (v[4] if len(v) > 4 else 0)
        cur[p[0]] = (sum(v[:8]), idle)
    if cur:
        blocchi.append(cur)
    if len(blocchi) < 2:
        return None
    tot, core = [], {}
    for a, b in zip(blocchi, blocchi[1:]):
        for nome in b:
            if nome not in a:
                continue
            dt = b[nome][0] - a[nome][0]
            di = b[nome][1] - a[nome][1]
            if dt <= 0:
                continue
            busy = 100.0 * (dt - di) / dt
            if nome == "cpu":
                tot.append(busy)
            else:
                core.setdefault(nome, []).append(busy)
    if not tot:
        return None
    s = sorted(tot)
    medie = {k: sum(v) / len(v) for k, v in core.items() if v}
    caldo = max(medie.items(), key=lambda kv: kv[1]) if medie else (None, None)
    return {"campioni": len(tot), "media": round(sum(tot) / len(tot), 1),
            "p95": round(s[min(len(s) - 1, int(0.95 * len(s)))], 1), "max": round(s[-1], 1),
            "core_piu_carico": caldo[0], "core_piu_carico_media": round(caldo[1] or 0, 1),
            "core": len(medie)}


def giudica(d):
    if d.get("contesto") != "running":
        return "BLOCKED", "il contesto audio non e' «running» a fine finestra (%s)" % d.get("contesto")
    if d["ricevuti"] <= 0:
        return "BLOCKED", "nessun blocco audio ricevuto nella finestra"
    if d["riarmi"] == 0 and d["scartati_pieno"] == 0:
        return "PASS", ("nessun buco: riarmi 0 in %.0f s (tirate %d, tagliati %d, udibile stimato "
                        ">= %.1f%%)" % (d["durata_s"], d["tirate"], d["tagliati"],
                                        d["udibile_stima_pct"]))
    return "FAIL", ("%d riarmi in %.0f s = almeno %.2f s di silenzio (tirate %d, tagliati %d, "
                    "pieni %d, udibile stimato >= %.1f%%)"
                    % (d["riarmi"], d["durata_s"], d["silenzio_minimo_s"], d["tirate"],
                       d["tagliati"], d["scartati_pieno"], d["udibile_stima_pct"]))


def certifica():
    ok = True

    def chk(nome, cond):
        nonlocal ok
        print("   %s %s" % ("⭐" if cond else "⛔", nome))
        ok = ok and cond
    c0 = {k: 0 for k in CONTI}
    c0.update(ricevuti=100, suonati=90, usciti=80, contesto="running")
    sano = dict(c0, ricevuti=3100, suonati=3090, usciti=3080, contesto="running")
    d = delta(c0, sano, 1000.0, 61000.0)
    e, _ = giudica(d)
    chk("sano: 60 s, 3000 blocchi usciti, 0 riarmi ⇒ PASS, udibile 100%", e == "PASS"
        and d["udibile_stima_pct"] == 100.0 and d["durata_s"] == 60.0)
    rotto = dict(sano, riarmi=7, tirate=90, tagliati=200, usciti=2700)
    d = delta(c0, rotto, 1000.0, 61000.0)
    e, r = giudica(d)
    chk("7 riarmi ⇒ FAIL, silenzio minimo 1,75 s (%s)" % r, e == "FAIL"
        and d["silenzio_minimo_s"] == 1.75)
    pieno = dict(sano, scartati_pieno=1)
    chk("un traboccamento senza riarmi ⇒ FAIL", giudica(delta(c0, pieno, 0, 60000))[0] == "FAIL")
    muto = dict(sano, contesto="suspended")
    chk("contesto sospeso ⇒ BLOCKED", giudica(delta(c0, muto, 0, 60000))[0] == "BLOCKED")
    vuoto = dict(c0)
    chk("nessun blocco ⇒ BLOCKED", giudica(delta(c0, vuoto, 0, 60000))[0] == "BLOCKED")
    # la CPU: due core, tre letture a 1 s; cpu0 al 100 %, cpu1 al 0 %
    st = ["cpu  0 0 0 0 0 0 0 0", "cpu0 0 0 0 0 0 0 0 0", "cpu1 0 0 0 0 0 0 0 0", "---",
          "cpu  100 0 0 100 0 0 0 0", "cpu0 100 0 0 0 0 0 0 0", "cpu1 0 0 0 100 0 0 0 0", "---",
          "cpu  200 0 0 200 0 0 0 0", "cpu0 200 0 0 0 0 0 0 0", "cpu1 0 0 0 200 0 0 0 0"]
    c = cpu_da_stat(st)
    chk("cpu: media 50%%, core piu' carico cpu0 al 100%% (%s)" % c,
        c and c["media"] == 50.0 and c["core_piu_carico"] == "cpu0"
        and c["core_piu_carico_media"] == 100.0 and c["campioni"] == 2)
    chk("cpu: una lettura sola ⇒ nessun numero", cpu_da_stat(st[:3]) is None)
    print("⭐ certificata" if ok else "⛔ NON certificata")
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA CPU DEL SERVER, durante la finestra
# ═══════════════════════════════════════════════════════════════════════════
SUL_SERVER = os.environ.get("REMOTIX_SUL_SERVER") == "1"


class Cpu:
    """`grep ^cpu /proc/stat` ogni secondo.  ⭐ Sul server si legge LOCALE (il
    browser gira li'); altrimenti dentro la scatola, dove `/proc/stat` e' quello
    dell'ospite (podman non lo isola)."""

    def __init__(self, sc, secondi):
        self.sc, self.secondi, self.righe, self.ps = sc, secondi, [], ""
        self._t = None

    def _locale(self):
        fine = time.time() + self.secondi
        meta = time.time() + self.secondi / 2
        while time.time() < fine:
            try:
                with open("/proc/stat") as f:
                    self.righe += [r for r in f if r.startswith("cpu")] + ["---"]
            except OSError:
                return
            if self.ps == "" and time.time() >= meta:
                try:
                    self.ps = subprocess.run(
                        ["ps", "-eo", "pcpu,rss,comm", "--sort=-pcpu"], capture_output=True,
                        text=True, timeout=10).stdout.splitlines()[:15]
                except Exception as e:           # noqa: BLE001
                    self.ps = ["(ps: %s)" % e]
            time.sleep(1.0)

    def _scatola(self):
        n = int(self.secondi)
        _c, t = self.sc.dentro("for i in $(seq %d); do grep ^cpu /proc/stat; echo ---; sleep 1; "
                               "done" % n, n + 60)
        self.righe = (t or "").splitlines()

    def accendi(self):
        self._t = threading.Thread(target=self._locale if SUL_SERVER else self._scatola,
                                   daemon=True)
        self._t.start()

    def leggi(self):
        if self._t:
            self._t.join(timeout=90)
        return cpu_da_stat(self.righe), self.ps


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def conti_pagina(g):
    return G4.in_pagina(g, "(function(){ return { ora: performance.now(),"
                           " conti: (typeof audio_conti === 'function') ? audio_conti() : null,"
                           " worker: (typeof VW !== 'undefined') && VW !== null }; })()")


def aspetta(g, cond, tetto_s):
    fine = time.time() + tetto_s
    r = None
    while time.time() < fine:
        r = conti_pagina(g)
        if r and cond(r):
            return True, r
        time.sleep(0.5)
    return False, r


def finestra(s, o, secondi):
    blocco = 0.005 if getattr(o, "pcm", False) else BLOCCO_S
    """(delta, cpu, ps) su `secondi`, due letture di `audio_conti()`."""
    cpu = Cpu(s.sc, secondi)
    r0 = conti_pagina(s.g)
    cpu.accendi()
    time.sleep(secondi)
    r1 = conti_pagina(s.g)
    c, ps = cpu.leggi()
    if not r0 or not r1 or not r0.get("conti") or not r1.get("conti"):
        raise S.Bloccata("audio_conti() non si legge dalla pagina (%r / %r)" % (r0, r1))
    return delta(r0["conti"], r1["conti"], r0["ora"], r1["ora"], blocco), c, ps, r1


# ⛔ Il guasto: un ciclo occupato NELLA PAGINA, 400 ms ogni 2 s — il thread
#   principale fermo oltre il cuscino.  Solo il banco lo mette, solo nel guasto.
JS_GUASTO = ("window.__c15d006 = setInterval(function(){ const f = performance.now() + 400;"
             " while (performance.now() < f) {} }, 2000);")
JS_GUASTO_VIA = "clearInterval(window.__c15d006);"


def corpo(o, E):
    if o.video_worker:
        o.url = o.url.split("#")[0] + "#video=worker"
    sess = S.Sessione(o, o.nnn, E)
    G4.robusta(sess.sc)
    with sess as s:
        ok, m = s.pr.apri()
        if not ok:
            raise S.Bloccata("la pagina non si apre: " + m)
        if o.pcm:
            # ⚠ SOLO BANCO: prima dell'accesso (la negoziazione e' al collegamento),
            #   `isConfigSupported` dice «no» a Opus ⇒ la pagina dichiara «pcm» e il
            #   server manda PCM.  Toglie `AudioDecoder` dal percorso dell'audio.
            #   ⭐ D-006 cura: e anche il decodificatore wasm della pagina non deve
            #   partire (WebAssembly.instantiate rifiuta), o la pagina dichiara Opus.
            s.g.js(G4._inietta("if (window.AudioDecoder) AudioDecoder.isConfigSupported ="
                               " async function () { return { supported: false }; };"
                               " if (window.WebAssembly) WebAssembly.instantiate ="
                               " function () { return Promise.reject(new Error('banco: PCM')); };"))
        ok, m = s.entra(apri=False)            # ⭐ SENZA orecchio
        if not ok:
            raise S.Bloccata(m)
        r = conti_pagina(s.g) or {}
        if o.video_worker and not r.get("worker"):
            raise S.Bloccata("chiesto #video=worker ma nella pagina il worker e' spento (%r)" % r)
        if o.quale == "f012":
            ok, m = F12.prepara_tono_ffmpeg(s)
            if not ok:
                raise S.Bloccata("il tono non si prepara: " + m)
            c, t = F12.suona(s)
            if c != 0:
                raise S.Bloccata("pw-play non parte: " + t[-200:])
            punto = (0.62, 0.55)
        else:
            ok, m = F13.prepara_video(s)
            if not ok:
                raise S.Bloccata("il video non si genera: " + m)
            c, t = F13.accendi_video(s)
            if c != 0:
                raise S.Bloccata("ffplay non parte: " + t[-200:])
            punto = (0.97, 0.5)                # bordo destro: fuori dalla finestra del video
        note = ["scena %s%s%s" % (o.quale, " · #video=worker (acceso)" if o.video_worker else "",
                                  " · PCM" if o.pcm else "")]
        ok, r = aspetta(s.g, lambda x: (x.get("conti") or {}).get("contesto") not in
                        (None, "(nessuno)"), 30)
        if not ok:
            raise S.Bloccata("la pagina non ha creato un AudioContext in 30 s (%r)" % r)
        note.append(G4.clic_vero(s, *punto))
        ok, r = aspetta(s.g, lambda x: (x.get("conti") or {}).get("contesto") == "running", 10)
        if not ok:
            raise S.Bloccata("il contesto audio non si sveglia al clic (%r)" % (r or {}).get("conti"))
        if o.pcm and (r.get("conti") or {}).get("codec") != 2:
            raise S.Bloccata("chiesto PCM ma la pagina riceve il codec %r"
                             % (r.get("conti") or {}).get("codec"))
        time.sleep(o.assesta_s)
        segno = s.segno_registro()
        d, cpu, ps, r1 = finestra(s, o, o.finestra_s)
        e, ragione = giudica(d)
        cf = r1.get("conti") or {}
        #   ⭐ chi decodifica l'Opus (wasm dalla cura di D-006, AudioDecoder prima)
        note.append("decodificatore %s (%s/%s us medio/max)" % (
            cf.get("decodificatore", "(pagina vecchia: AudioDecoder)"),
            cf.get("dec_us_medio"), cf.get("dec_us_max")))
        misura = {"scatola": o.scatola, "browser": o.browser, "versione": E.versione,
                  "scena": o.quale, "worker": bool(o.video_worker), "pcm": bool(o.pcm), "delta": d, "cpu": cpu,
                  "conti_fine": r1.get("conti")}
        print("MISURA " + json.dumps(misura, ensure_ascii=False), flush=True)
        ev = [G4.salva_json(o, "d006-misura-%s-%s-%s%s.json" % (
            o.scatola, o.browser, o.quale, ("-worker" if o.video_worker else "") + ("-pcm" if o.pcm else "")),
            dict(misura, ps=ps)),
              s.salva_testo("server-d006.txt", s.registro_da(segno) if segno else []),
              s.salva_console()]
        E.metti("D-006", e, ragione,
                atteso="riarmi 0 in %.0f s, senza orecchio (conti della pagina)" % o.finestra_s,
                osservato="; ".join(note) + " · cpu %s" % cpu, evidenze=[p for p in ev if p],
                numeri=misura)

        if o.guasto:
            s.g.js(G4._inietta(JS_GUASTO))
            try:
                dg, _c, _p, _r = finestra(s, o, GUASTO_S)
            finally:
                s.g.js(G4._inietta(JS_GUASTO_VIA))
            visto = dg["riarmi"] >= 3
            E.guasto("D-006", visto, "thread principale della pagina fermo 400 ms ogni 2 s per "
                     "%.0f s ⇒ riarmi %d (attesi >= 3), tirate %d"
                     % (GUASTO_S, dg["riarmi"], dg["tirate"]), numeri={"delta": dg})


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra))
