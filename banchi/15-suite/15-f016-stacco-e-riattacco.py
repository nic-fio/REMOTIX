#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f016 — F-016 DETACH · F-017 REATTACH AT THE SAME SIZE · paths P-A and P-F

    python3 15-f016-stacco-e-riattacco.py --scatola kde --browser chrome [--guasto]

The scene (15-g6-comune): in the session a firefox-esr with a cyan background, a
text field and the STRIP that shows in colours what is written in it; the
program writes down every 2 s its state (token, value, screen) in a file.

  P-A/P-F  creation → desktop → application open → REAL INPUT (click on the
           scene and letters written by the browser) → DETACH (the browser closes,
           with its farewell) → WAIT 35 s (beyond the silence clock, §5.3)
           → REATTACH (new browser, same user and password) → STATE → INPUT.

F-016  expected: after the detach and the wait the session stays and the programs stay.
       fields: the PID of the scene's firefox-esr and that of the compositor are
       the SAME as before; the logind session is there; the scene keeps
       beating (new lines in the notebook AFTER the wait, with the SAME token and
       the same text); the server log does not say the session dies.
F-017  expected: coming back in ⇒ admitted, and the STATE is found again — from the PHOTO: the
       cyan window is there and the strip reads the text written before; from the
       FIELD: same token (the page was not reborn), same value.
       ⚠ The page's sentence («Admitted, new|resumed session») is looked at:
       `RCP.md` §4 (`SESSIONE`, state 1 = NEW, 2 = RESUMED).
P-A    expected: the input AFTER the reattach arrives too (new letters read in the photo).
P-F    expected: F-016 and F-017 together (application open, wait, state).

FAULT (real, in the scene): we detach again and during the detach we KILL the
       scene's program (kill -9 of the tenant's firefox-esr) — that is
       «the programs do not stay».  The same tests must give RED: F-016
       (PID gone, beats stopped), F-017 (neither window nor text), P-A, P-F.
"""
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g6", os.path.join(S.QUI, "15-g6-comune.py"))
FUNZIONI = ("F-016", "F-017", "P-A", "P-F")
ATTESA_S = 35          # beyond the 30 s of silence (§5.3): the session must stay
# ⛔ the log lines that would mean «the session died with the client»
# ⚠ (10 Oct 2026) «la sessione e' morta» was removed: the product never wrote it
#   in a log line (only in a comment of figlio.c); the death of the graphical
#   session reaches the log as «the graphical session is over» (main.c, §7.6).
MORTE = ("a NEW one will be born", "the graphical session is over", "SESSIONE_TERMINATA")


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure)
# ═══════════════════════════════════════════════════════════════════════════
def giudica_stacco(prima, dopo, q_dopo, t_fine_attesa_ms, testo, registro):
    """F-016.  prima/dopo: {name: [pid]} (G.processi); q_dopo: notebook;
    returns (outcome, reason)."""
    probl = []
    pf0, pf1 = G.pid_scena(prima), G.pid_scena(dopo)
    if pf0 is None:
        return S.BLOCKED, "before the detach the scene was not there: nothing to compare"
    if pf1 != pf0:
        probl.append("the scene's program (firefox-esr %s) after the detach %s"
                     % (pf0, "IS NO LONGER THERE" if pf1 is None else "is ANOTHER one (%s)" % pf1))
    for comp in ("gnome-shell", "kwin_wayland", "labwc"):
        if prima.get(comp):
            if sorted(prima[comp]) != sorted(dopo.get(comp) or []):
                probl.append("the compositor %s was %s, after %s"
                             % (comp, prima[comp], dopo.get(comp)))
    if prima.get("sessione") and not dopo.get("sessione"):
        probl.append("the logind session %s is no longer there" % prima["sessione"])
    battiti = [r for r in q_dopo if r.get("t", 0) >= t_fine_attesa_ms]
    g0 = None
    for r in q_dopo:
        if r.get("t", 0) < t_fine_attesa_ms and r.get("v") == testo:
            g0 = r.get("g")
    if not battiti:
        probl.append("the scene no longer beats after the wait (no new line in the notebook)")
    elif g0 and any(r.get("g") != g0 for r in battiti):
        probl.append("the scene has a NEW token: the page was reborn")
    elif battiti[-1].get("v") != testo:
        probl.append("the scene's text is «%s», not «%s»" % (battiti[-1].get("v"), testo))
    morte = [r for r in registro if any(m in r for m in MORTE)]
    vive = [r for r in registro if "(I4)" in r or "invariant I4" in r]
    if not vive:
        probl.append("the server log (%d lines since the detach) does not say the stage "
                     "stays (no «I4» line)" % len(registro))
    if morte:
        probl.append("the server log says the session ends: «%s»" % morte[0][-200:])
    if probl:
        return S.FAIL, "; ".join(probl)
    return S.PASS, ("log: «%s» · after %d s detached: firefox-esr %s and compositor alive, same PIDs; "
                    "session %s; the scene still beats (%d lines after the wait, same "
                    "token, text «%s»)" % (vive[0].split("] ", 1)[-1][:90], ATTESA_S, pf0, (dopo.get("sessione") or ["?"])[0],
                                              len(battiti), testo))


def giudica_ritrovo(testo, vista, stato_dopo, gettone_prima):
    """F-017 (the state).  vista: G.guarda_la_scena; stato_dopo: last line of the
    notebook.  Returns (outcome, reason)."""
    probl = []
    cieco = vista.get("png") is None and "finestra" in vista and vista.get("foto") is not None
    if cieco:
        pass                     # the photo could not be taken: the fields decide, or BLOCKED
    elif not vista.get("finestra"):
        probl.append("in the photo the scene's window is NOT there (%s)" % vista.get("perche"))
    elif vista.get("letto") != testo:
        probl.append("in the photo the strip says «%s» (raw %s), written before «%s»"
                     % (vista.get("letto"), vista.get("crudo"), testo))
    if not stato_dopo:
        probl.append("the scene no longer writes its state")
    else:
        if gettone_prima and stato_dopo.get("g") != gettone_prima:
            probl.append("the scene's token changed (%s → %s): it was reborn"
                         % (gettone_prima, stato_dopo.get("g")))
        if stato_dopo.get("v") != testo:
            probl.append("the scene's field is «%s», not «%s»" % (stato_dopo.get("v"), testo))
    if probl:
        return S.FAIL, "; ".join(probl) + (" (the photo could not be taken: %s)"
                                           % vista.get("perche") if cieco else "")
    if cieco:
        return S.BLOCKED, "the fields add up, but the photo could not be taken: %s" % vista.get("perche")
    return S.PASS, ("found again: window in the photo, strip «%s», token %s unchanged"
                    % (testo, gettone_prima))


def giudica_frase(esito):
    """The sentence the user reads at reattach (RCP §4: 2 = RESUMED)."""
    e = esito or ""
    if "resumed session" in e:
        return True, "the page says «%s»" % e
    return False, ("the page says «%s» to a RESUMED session (RCP.md §4: state 2 = "
                   "RESUMED; src/rcp.c always sends 1 = NEW)" % e)


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    pr = {"firefox-esr": ["100", "120"], "labwc": ["90"], "sessione": ["c7"]}
    q = [{"g": "x", "v": "abc", "t": 1000}, {"g": "x", "v": "abc", "t": 5000}]
    I4 = ["x figlio [u] the stage stays up (I4)"]
    e, m = giudica_stacco(pr, pr, q, 3000, "abc", I4)
    prova("healthy detach ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = giudica_stacco(pr, pr, q, 3000, "abc", [])
    prova("log without I4 ⇒ FAIL", e == S.FAIL)
    e, m = giudica_stacco(pr, {"labwc": ["90"], "sessione": ["c7"]}, q[:1], 3000, "abc", I4)
    prova("program killed ⇒ FAIL (%s)" % m[:60], e == S.FAIL)
    e, _ = giudica_stacco(pr, pr, q + [{"g": "y", "v": "", "t": 6000}], 3000, "abc", I4)
    prova("page reborn ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_stacco(pr, pr, q, 3000, "abc", I4 + ["... a NEW one will be born"])
    prova("death log ⇒ FAIL", e == S.FAIL)
    # the photo: a synthetic scene with «abc» in the strip
    png = scena_finta("abc")
    v = G.guarda_la_scena(_Finta(png), "x")
    prova("fake photo: strip read «%s»" % v.get("letto"), v.get("letto") == "abc")
    e, _ = giudica_ritrovo("abc", v, {"g": "x", "v": "abc"}, "x")
    prova("healthy finding again ⇒ PASS", e == S.PASS)
    v2 = G.guarda_la_scena(_Finta(scena_finta(None)), "x")
    e, _ = giudica_ritrovo("abc", v2, None, "x")
    prova("without window ⇒ FAIL", e == S.FAIL)
    v3 = {"finestra": None, "letto": None, "foto": "", "perche": "timed out", "png": None}
    e, _ = giudica_ritrovo("abc", v3, {"g": "x", "v": "abc"}, "x")
    prova("photo failed, good fields ⇒ BLOCKED", e == S.BLOCKED)
    prova("sentence «new» ⇒ no", not giudica_frase("Admitted, new session, canvas")[0])
    return 0 if ok else 1


def scena_finta(testo, w=1920, h=1080):
    """A dark grey desktop with the scene's window (for --certifica)."""
    import io
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), (40, 40, 60))
    d = ImageDraw.Draw(im)
    if testo is not None:
        x0, y0, x1, y1 = 100, 120, 1300, 900
        d.rectangle([x0, y0, x1, y1], fill=G.CIANO)
        W, H = x1 - x0 + 1, y1 - y0 + 1
        passo = (G.STR_X1 - G.STR_X0) / G.CASELLE
        for i in range(G.CASELLE):
            c = G.TAVOLOZZA[testo[i]] if i < len(testo) else G.VUOTO
            a = x0 + W * (G.STR_X0 + i * passo)
            b = a + W * passo - W * 0.014
            d.rectangle([a, y0 + H * G.STR_Y0, b, y0 + H * G.STR_Y1], fill=c)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


class _Finta:
    """A fake Sessione that «photographs» a given png."""
    def __init__(self, png):
        self.png = png

    def foto(self, nome):
        return self.png, ""


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def testo_a_caso(n):
    """DIFFERENT letters: a strip «bbbb» would say little about the order."""
    return "".join(random.sample(G.ALFABETO, n))


def trova_scena(s, tetto=30.0):
    fine = time.time() + tetto
    v = {}
    while time.time() < fine:
        v = G.guarda_la_scena(s, "scena")
        if v.get("finestra"):
            return v
        time.sleep(2)
    return v


def un_giro(o, E, s, testo, passata, guasto=False):
    """Detach → wait → reattach → state → input.  Puts F-016, F-017, P-A, P-F."""
    metti = (lambda f, e, r, **k: E.guasto(f, e == S.FAIL, "fault (scene killed): " + r, **k)) \
        if guasto else (lambda f, e, r, **k: E.metti(f, e, r, passata=passata, **k))
    q0 = G.quaderno(s)
    gettone = next((r.get("g") for r in reversed(q0) if r.get("v") == testo), None)
    prima = G.processi(s)
    segno = s.segno_registro()
    print("   before the detach: %s · token %s" % (prima, gettone), flush=True)
    # ── DETACH: the browser closes (the driver navigates to about:blank ⇒ farewell, then exits)
    s.spegni_browser()
    t_stacco = time.time()
    if guasto:
        c, t = s.sc.dentro("pkill -KILL -u %s -x firefox-esr; sleep 1; pgrep -u %s -x "
                           "firefox-esr || echo uccisa" % (s.chi, s.chi), 30)
        print("   ⛔ FAULT: the scene killed during the detach: %s" % t.strip()[-80:], flush=True)
    time.sleep(max(0, ATTESA_S - (time.time() - t_stacco)))
    t_fine = time.time()
    time.sleep(3)                                 # at least one beat after the wait
    dopo = G.processi(s)
    q1 = G.quaderno(s)
    reg = s.registro_da(segno) if segno is not None else []
    ev = [s.salva_testo("server-%s-stacco.txt" % passata, reg)]
    e16, r16 = giudica_stacco(prima, dopo, q1, int(t_fine * 1000), testo, reg)
    metti("F-016", e16, r16, atteso="after %d s detached: same PIDs, session alive, the scene "
          "beats with its text" % ATTESA_S,
          osservato="before %s · after %s · %d notebook lines" % (prima, dopo, len(q1)),
          evidenze=ev)

    # ── REATTACH: a new browser, same user and password
    segno = s.segno_registro()
    s.accendi_browser()
    ok, m, rifiuti, sec = G.entra_con_riprova(s, tetto_s=40)
    reg = s.registro_da(segno) if segno is not None else []
    ev = [s.salva_testo("server-%s-riattacco.txt" % passata, reg)]
    if not ok:
        for f in ("F-017", "P-A", "P-F"):
            metti(f, S.FAIL, "the reattach does not get in in %.0f s: %s (refusals: %s)"
                  % (sec, m, rifiuti), evidenze=ev)
        return
    ob = G.osserva_tela(s)
    frase_ok, frase = giudica_frase(ob.get("esito"))
    v = G.aspetta_testo(s, testo, "riattacco-%s" % passata, tetto=12)
    st = G.ultimo_stato(s)
    e17, r17 = giudica_ritrovo(testo, v, st, gettone)
    e17_stato = e17                  # the paths look at the STATE, not at the sentence
    if e17 == S.PASS and not frase_ok and not guasto:
        e17, r17 = S.FAIL, "state found again (%s) BUT %s" % (r17, frase)
    ev17 = ev + [v.get("foto")]
    metti("F-017", e17, r17, atteso="admitted with «resumed session»; photo: window and "
          "strip «%s»; field: same token and value" % testo,
          osservato="%s · %s · back in after %.1f s (%d refusals) · state %s"
          % (frase, v.get("crudo"), sec, len(rifiuti), st), evidenze=ev17)

    # ── INPUT AFTER THE REATTACH (P-A)
    agg = testo_a_caso(2)
    if v.get("finestra"):
        cl = G.clic_sulla_scena(s, v)
        G.scrivi(s, agg)
        v2 = G.aspetta_testo(s, testo + agg, "input-dopo-%s" % passata, tetto=10)
        in_ok = v2.get("letto") == testo + agg
        r_in = "written «%s» after the reattach (%s): the photo reads «%s»" % (
            agg, cl, v2.get("letto"))
        ev_in = [v2.get("foto")]
    else:
        in_ok, r_in, ev_in = False, "no window to write on after the reattach", []
    ea = S.PASS if (e16 == S.PASS and e17_stato == S.PASS and in_ok) else S.FAIL
    metti("P-A", ea, "detach %s · state at reattach %s · input after: %s" % (e16, e17_stato, r_in),
          atteso="creation→desktop→input→detach→reattach→input, all seen",
          osservato=r_in, evidenze=ev17 + ev_in)
    ef = S.PASS if (e16 == S.PASS and e17_stato == S.PASS) else S.FAIL
    metti("P-F", ef, "application open, detach, %d s, reattach: F-016 %s · state %s"
          % (ATTESA_S, e16, e17_stato), atteso="the application's state found again",
          osservato="%s | %s" % (r16[:200], r17[:200]), evidenze=ev17)
    return testo + agg if in_ok else None


def corpo(o, E):
    with S.Sessione(o, "016", E) as s:
        try:
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("without login there is nothing to detach: " + m)
            ok, t = G.accendi_scena(s)
            if not ok:
                raise S.Bloccata("the scene does not start in the session: " + t[-200:])
            G.sveglia(s)
            v = trova_scena(s)
            if not v.get("finestra"):
                raise S.Bloccata("the scene's window is not seen in the photo: %s"
                                 % v.get("perche"))
            testo = testo_a_caso(4)
            v, note = G.scrivi_la_base(s, v, testo)
            if v.get("letto") != testo:
                raise S.Bloccata("the PREPARATION input does not reach the scene (it is F-004/F-007, "
                                 "not this function): %s" % " | ".join(note))
            print("   written «%s» and read in the photo" % testo, flush=True)
            nuovo = un_giro(o, E, s, testo, "sana")
            if o.guasto:
                if s.g is None:
                    s.accendi_browser()
                un_giro(o, E, s, nuovo or testo, "guasto", guasto=True)
        finally:
            s.salva_console() if s.g else None
            G.spegni_servitore(s)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
