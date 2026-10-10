#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f014c — THE CLIPBOARD AS A PERSON USES IT: WITH THE COMPUTER, NOT WITH THE BENCH

    python3 15-f014c-appunti-dal-computer.py --scatola gnome --browser chrome [--guasto]
    python3 15-f014c-appunti-dal-computer.py --certifica

WHY IT EXISTS (2 Oct 2026, the user's manual test: «Ctrl+C / Ctrl+V do not
work, or not always», Firefox AND Chrome, all the desktops).  `15-f014` is
green but does not see what the person sees: it makes courtesy clicks, reads the
clipboard from the page with `readText()`, GIVES Chrome the permission, never reuses
a text and never copies OUTSIDE the browser.  This test does as the person does:

  - the COMPUTER's clipboard (not the page's) is written and read with
    `wl-copy` / `wl-paste` in the browser's Wayland session (the desktop's
    headless labwc, the one of 15-compositori.sh: the same WAYLAND_DISPLAY
    the round gives the browser);
  - NO courtesy click: only the click the person really makes (one on the
    canvas before pasting);
  - Chrome WITHOUT the clipboard permission (no `Browser.grantPermissions`);
  - one `Ctrl+V` at a time, never typed again: the first is the one that counts.

The scene and the gestures are those of `15-f014` (imported, not copied): a
`firefox-esr --kiosk` in the session with an always-focused <textarea>, which
writes down every value; the judgment is the FIELD VALUE of the session's
application, or the text in the computer's clipboard.

F-015C  (P1) session → computer, without recent gestures.  The text in the scene's
        field, selected; 6 s still (no click: the browser's activation
        expires); REAL `Ctrl+C` on the page ⇒ within 3 s `wl-paste` must be
        EXACTLY that text.
F-014C  (P2, the main one) the text copied OUTSIDE the browser.  `Ctrl+C` in the
        scene (text Z: now the session's clipboard belongs to a remote
        application), then `wl-copy X` outside the browser, ONE click on the canvas, ONE
        `Ctrl+V` ⇒ the scene's field must be X.  Five times, new texts
        each time; green only if all five.
F-014D  (P1b) the SAME text copied twice.  `wl-copy X`, click, `Ctrl+V` ⇒
        X; then a copy in the session (text W), then `wl-copy X` again
        (identical), click, `Ctrl+V` ⇒ X.

FAULT (same session, after the healthy pass):
  F-015C  «copy not made»: the text in the field, 6 s, NO `Ctrl+C` ⇒
          `wl-paste` does not see it ⇒ RED.  And the healthy value judged against
          the same text without accents ⇒ RED.
  F-014C  «outside copy not made»: `Ctrl+C` in the scene, NO `wl-copy X`,
          click, `Ctrl+V` ⇒ the field is not X ⇒ RED.  And the expectation without accents.
  F-014D  «the second copy is another text»: the second `wl-copy` puts Y,
          the expectation stays X ⇒ RED.  And the expectation without accents.

⚠ Only Firefox and Chrome on the server (the phone has no `wl-copy`: BLOCKED).
"""
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNZIONI = ("F-015C", "F-014C", "F-014D")

# ⭐ the scene, the gestures and the judge of 15-f014 (its local `dentro` too)
F14 = S._carica("f014", os.path.join(S.QUI, "15-f014-appunti.py"))

GIRI_P2 = 5
FERMO_P1_S = 6.0          # no gestures: the transient activation (5 s) expires
TETTO_P1_S = 3.0          # within how long the text must be in the computer's clipboard
ATTESA_CAMPO_S = 12.0


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def giudica_giri(giri, quanti):
    """(outcome, why) on the P2 rounds: [{"atteso", "visto", "gesto"}].
    The rounds without the Ctrl+V keydown do not count (it is the keyboard)."""
    validi = [g for g in giri if g.get("gesto")]
    sbagliati = [g for g in validi if g.get("visto") != g.get("atteso")]
    if sbagliati:
        vecchi = sum(1 for g in sbagliati if g.get("visto") and g.get("visto") == g.get("remoto"))
        return S.FAIL, ("%d rounds of %d: at the first Ctrl+V the field is NOT the text copied "
                        "outside the browser (%d times it is the OLD text copied in the "
                        "session)" % (len(sbagliati), len(validi), vecchi))
    if len(validi) < quanti:
        return S.BLOCKED, ("only %d valid rounds of %d: the Ctrl+V did not reach "
                           "the application in the others" % (len(validi), quanti))
    return S.PASS, "%d rounds of %d: the field is the text copied outside" % (len(validi), quanti)


def certifica():
    t = F14.testo_unico("X")
    z = F14.testo_unico("Z")
    giri_ok = [{"atteso": t, "visto": t, "gesto": True}] * GIRI_P2
    casi = [
        ("f014's judge: identical ⇒ PASS", F14.giudica_testo(t, t)[0] == S.PASS),
        ("without accents ⇒ FAIL", F14.giudica_testo(t, F14.senza_accenti(t))[0] == S.FAIL),
        ("five right rounds ⇒ PASS", giudica_giri(giri_ok, GIRI_P2)[0] == S.PASS),
        ("one round with the old text ⇒ FAIL", giudica_giri(
            giri_ok[:4] + [{"atteso": t, "visto": z, "remoto": z, "gesto": True}],
            GIRI_P2)[0] == S.FAIL),
        ("the old text is counted", "1 times" in giudica_giri(
            [{"atteso": t, "visto": z, "remoto": z, "gesto": True}], 1)[1]),
        ("one wrong round is enough even with few valid ones", giudica_giri(
            [{"atteso": t, "visto": None, "gesto": True},
             {"atteso": t, "visto": None, "gesto": False}], GIRI_P2)[0] == S.FAIL),
        ("rounds without gesture ⇒ BLOCKED", giudica_giri(
            [{"atteso": t, "visto": None, "gesto": False}] * GIRI_P2, GIRI_P2)[0] == S.BLOCKED),
        ("four valid right out of five ⇒ BLOCKED", giudica_giri(
            giri_ok[:4], GIRI_P2)[0] == S.BLOCKED),
    ]
    ok = True
    for nome, vero in casi:
        print("%s %s" % ("⭐" if vero else "⛔", nome))
        ok = ok and vero
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE COMPUTER'S CLIPBOARD (the browser's Wayland session)
# ═══════════════════════════════════════════════════════════════════════════
def wl_copia(testo):
    """`wl-copy` as another application of the computer would do it.  ⚠ wl-copy
    stays alive in the background serving the text: the outputs do NOT go into a pipe."""
    r = subprocess.run(["wl-copy"], input=testo.encode("utf-8"), stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
    return r.returncode == 0


def wl_leggi():
    """The text in the computer's clipboard, or None."""
    try:
        r = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def fuoco_al_browser():
    """The compositor's KEYBOARD focus to the browser.  ⚠ `[M]` 2 Oct 2026,
    round `cure-intel-2`: the keys of `wtype` reached nobody — the bench's
    browser receives clicks and keys from Marionette/CDP, which do not go through the
    compositor, so labwc never gave it the focus.  The person gives the focus
    by clicking on the window; here it is requested with `wlrctl` (wlroots'
    foreign-toplevel protocol).  Returns the focused app_id, or None."""
    if not shutil.which("wlrctl"):
        return None
    try:
        r = subprocess.run(["wlrctl", "toplevel", "list"], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return None
    for riga in r.stdout.decode("utf-8", "replace").splitlines():
        app = riga.split(":", 1)[0].strip()
        if "firefox" in app.lower() or "chrom" in app.lower():
            subprocess.run(["wlrctl", "toplevel", "focus", "app_id:" + app],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            time.sleep(0.2)
            return app
    return None


def ctrl_dal_sistema(g, lettera):
    """`Ctrl+<letter>` typed BY THE GRAPHICAL SYSTEM (`wtype`, Wayland's virtual
    keyboard), not injected into the browser.  ⛔ Why it is needed: `[M]` 2 Oct 2026, round
    `f014c-prima` — with the injected `Ctrl+C` (Marionette / `Input.dispatchKeyEvent`)
    Firefox AND Chrome say they wrote to the clipboard (`scritti` 1, nothing
    pending) and `wl-paste` sees nothing: a Wayland client takes the selection
    only with the serial number of a REAL input event of the compositor, and a
    key injected into the browser has none.  The person types the keys on the
    keyboard: this is the road that resembles it.  Without `wtype` we go back to the
    injected key, and it is declared."""
    # ⛔ But the combination is NOT typed with `wtype`: `[M]` round `cure-intel-3`,
    #   BLOCKED — `wtype` loads a key map of ITS OWN, with invented codes, and
    #   the page sends the desktop the POSITION (`KeyboardEvent.code`): the
    #   Ctrl+C arrived as another key.  ⇒ Only a Shift goes through the graphical system
    #   (the page does not send it: «on their own they are not sent»), which gives the
    #   browser the keyboard focus and a fresh serial number; the
    #   combination stays injected, with the right positions.
    via = "injected"
    if shutil.which("wtype") and fuoco_al_browser():
        r = subprocess.run(["wtype", "-k", "Shift_L"], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10)
        if r.returncode == 0:
            via = "serial from the system + injected"
            time.sleep(0.1)
    F14.ctrl(g, lettera)
    return via


def wl_svuota():
    try:
        subprocess.run(["wl-copy", "--clear"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10)
    except Exception:                            # noqa: BLE001
        pass


def stato(g):
    try:
        return g.js(F14.STATO_APPUNTI) or {}
    except Exception as e:                       # noqa: BLE001
        return {"errore": str(e)[:200]}


def conti(st):
    return dict((st or {}).get("conti") or {})


# ═══════════════════════════════════════════════════════════════════════════
#  THE PERSON'S GESTURES
# ═══════════════════════════════════════════════════════════════════════════
def punto_campo(geo):
    return S.C21.dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.3)


def copia_nella_sessione(g, scena, testo, copia=True):
    """The text in the scene's field, selected, and REAL `Ctrl+C` on the page.
    No click.  Returns the details (gesture arrived or not)."""
    q = scena.comanda(metti=testo)
    if F14.ultimo_valore(q) != testo:
        raise S.Bloccata("the scene did not take the text to copy: %r" % (F14.ultimo_valore(q),))
    det = {"copia_fatta": copia, "stato_prima": stato(g)}
    da = len(q)
    if copia:
        det["tasto"] = ctrl_dal_sistema(g, "c")
        fine = time.time() + 5
        while time.time() < fine and not F14.tasto_visto(scena.quaderno()[da:], "c"):
            time.sleep(0.5)
        det["gesto_arrivato"] = F14.tasto_visto(scena.quaderno()[da:], "c")
    return det, da


def incolla_una_volta(g, scena, geo, atteso):
    """ONE click on the canvas (on the remote field), ONE Ctrl+V.  Never typed again.
    Returns (value of the field, details)."""
    da = len(scena.quaderno())
    x, y = punto_campo(geo)
    det = {}
    g.clic(x, y)
    time.sleep(1.0)
    det["computer_al_ctrl_v"] = wl_leggi()
    det["stato_prima"] = stato(g)
    det["tasto"] = ctrl_dal_sistema(g, "v")
    visto, q = scena.aspetta_valore(atteso, da, ATTESA_CAMPO_S)
    det["gesto_arrivato"] = F14.tasto_visto(q, "v")
    det["incollato_dalla_scena"] = [v for t, v in q if t == "P"]
    det["quaderno"] = q[-10:]
    det["stato_dopo"] = stato(g)
    det["annunci"] = conti(det["stato_dopo"]).get("annunciati", 0) - \
        conti(det["stato_prima"]).get("annunciati", 0)
    det["computer_dopo"] = wl_leggi()
    return visto, det


# ═══════════════════════════════════════════════════════════════════════════
#  THE THREE TESTS
# ═══════════════════════════════════════════════════════════════════════════
def p1(g, scena, testo, copia=True):
    """F-015C: returns (text in the computer's clipboard within 3 s, details)."""
    wl_copia("prima-di-P1 " + F14.testo_unico("S"))
    q = scena.comanda(metti=testo)
    if F14.ultimo_valore(q) != testo:
        raise S.Bloccata("the scene did not take the text: %r" % (F14.ultimo_valore(q),))
    time.sleep(FERMO_P1_S)                       # ⭐ still: no recent gesture
    det = {"copia_fatta": copia, "stato_prima": stato(g)}
    da = len(scena.quaderno())
    if copia:
        det["tasto"] = ctrl_dal_sistema(g, "c")
    t0 = time.time()
    letto, letture = None, []
    while time.time() - t0 < TETTO_P1_S:
        letto = wl_leggi()
        letture.append((round(time.time() - t0, 2), (letto or "")[:60]))
        if letto == testo:
            break
        time.sleep(0.2)
    det["entro_s"] = round(time.time() - t0, 2) if letto == testo else None
    det["letture"] = letture[-6:]
    det["gesto_arrivato"] = F14.tasto_visto(scena.quaderno()[da:], "c") if copia else None
    det["stato_dopo"] = stato(g)
    det["computer_dopo_5s"] = None
    if letto != testo:
        time.sleep(2.0)
        det["computer_dopo_5s"] = wl_leggi()      # diagnosis: is it only late?
        det["stato_dopo_5s"] = stato(g)
    det["diario"] = g.js(F14.DIARIO)
    return letto, det


def p2_giro(g, scena, geo, sigla, copia_fuori=True):
    """F-014C, one round.  Returns {"atteso", "visto", "remoto", "gesto", ...}."""
    z = F14.testo_unico(sigla + "Z")
    x = F14.testo_unico(sigla + "X")
    dc, _da = copia_nella_sessione(g, scena, z)
    time.sleep(2.0)                              # the person switches to another window
    st_copia = stato(g)
    scena.comanda(pulisci=True)
    if copia_fuori:
        wl_copia(x)
    fuori = wl_leggi()
    time.sleep(1.0)                              # and comes back to the browser
    visto, di = incolla_una_volta(g, scena, geo, x)
    r = {"atteso": x, "visto": visto, "remoto": z, "copia_fuori": copia_fuori,
         "gesto": di["gesto_arrivato"], "ctrl_c_arrivato": dc.get("gesto_arrivato"),
         "computer_dopo_wl_copy": fuori, "stato_dopo_copia": st_copia}
    r.update(di)
    return r


def p1b(g, scena, geo, x, seconda):
    """F-014D: (first value, second value, details)."""
    det = {}
    scena.comanda(pulisci=True)
    wl_copia(x)
    time.sleep(1.0)
    v1, det["primo"] = incolla_una_volta(g, scena, geo, x)
    w = F14.testo_unico("P1bW")
    det["copia_remota"], _ = copia_nella_sessione(g, scena, w)
    time.sleep(2.0)
    det["stato_dopo_copia_remota"] = stato(g)
    scena.comanda(pulisci=True)
    wl_copia(seconda)
    det["computer_seconda"] = wl_leggi()
    time.sleep(1.0)
    v2, det["secondo"] = incolla_una_volta(g, scena, geo, x)
    det["remoto"] = w
    det["diario"] = g.js(F14.DIARIO)
    return v1, v2, det


def giudica_p1b(x, v1, v2, det):
    e1, p1_ = F14.giudica_testo(x, v1)
    e2, p2_ = F14.giudica_testo(x, v2)
    if e1 == S.PASS and e2 == S.PASS:
        return S.PASS, "both times the field is the copied text (even the second, identical one)"
    parti = []
    if e1 != S.PASS:
        parti.append("first time: " + p1_)
    if e2 != S.PASS:
        quale = "the text of the REMOTE copy" if v2 == det.get("remoto") else p2_
        parti.append("second time (same text copied again): %s · announcements sent at the "
                     "Ctrl+V: %s" % (quale, det.get("secondo", {}).get("annunci")))
    gesti = [det.get(k, {}).get("gesto_arrivato") for k in ("primo", "secondo")]
    if not all(gesti):
        return S.BLOCKED, ("the Ctrl+V did not reach the application (%s): it is the keyboard "
                           "— " % gesti) + " · ".join(parti)
    return S.FAIL, " · ".join(parti)


# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    if o.browser == "telefono":
        raise S.Bloccata("the phone has no `wl-copy`: the computer's clipboard is looked at "
                         "only on the server")
    wd = os.environ.get("WAYLAND_DISPLAY", "")
    rd = os.environ.get("XDG_RUNTIME_DIR", "")
    if not wd or not os.path.exists(os.path.join(rd, wd)):
        raise S.Bloccata("no Wayland session of the browser (WAYLAND_DISPLAY=%r, "
                         "XDG_RUNTIME_DIR=%r): it is launched from the round or from 15-una.sh" % (wd, rd))
    prova = F14.testo_unico("WL")
    if not wl_copia(prova) or wl_leggi() != prova:
        raise S.Bloccata("the computer's clipboard cannot be written/read with wl-copy/"
                         "wl-paste on %s" % wd)
    print("   computer's clipboard: %s (wl-copy/wl-paste)" % wd, flush=True)
    porta_scena = o.porte_base + 6
    try:
        with S.Sessione(o, "914", E) as s:
            # ⛔ NO clipboard permission to Chrome: like the user who has
            #   never clicked «Allow»
            dentro(o, E, s, porta_scena)
    finally:
        wl_svuota()


def dentro(o, E, s, porta_scena):
    g = s.g
    segno = s.segno_registro()
    ok, m = s.entra()
    if not ok:
        raise S.Bloccata(m)
    geo = s.geometria()
    if not geo:
        raise S.Bloccata("the canvas geometry is not there")
    st = stato(g)
    print("   page clipboard: %s" % json.dumps(st, ensure_ascii=False), flush=True)
    if not st or not st.get("acceso"):
        for f in FUNZIONI:
            E.metti(f, S.FAIL, "the page's clipboard is not on: %s" % st)
        return
    print("   wake-up: %s" % S.C21.sveglia(g, geo), flush=True)
    scena = F14.Scena(s, porta_scena)
    try:
        la_scena(o, E, s, g, geo, scena)
    finally:
        try:
            s.salva_testo("server-f014c.txt", s.registro_da(segno) if segno is not None else [])
            s.salva_console()
        finally:
            scena.spegni()


def la_scena(o, E, s, g, geo, scena):
    ok, t = scena.accendi()
    print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
    if not ok:
        print(t, flush=True)
        s.foto("scena-non-accesa")
        raise S.Bloccata("the scene does not start: %s" % (t or "")[-300:])
    time.sleep(3)
    # ⛔ poor man's check: does the keyboard reach the remote field?
    x, y = punto_campo(geo)
    g.clic(x, y)
    time.sleep(1.0)
    scena.comanda(pulisci=True)
    da = len(scena.quaderno())
    F14.lettera(g, "q")
    v, _q = scena.aspetta_valore("q", da, 8)
    if v != "q":
        raise S.Bloccata("the keyboard does not reach the scene's field (a «q» typed ⇒ %r)"
                         % (v,))
    scena.comanda(pulisci=True)
    salva = lambda nome, d: s.salva_testo(nome, json.dumps(d, ensure_ascii=False, indent=1))  # noqa: E731

    # ── P1 · F-015C ────────────────────────────────────────────────────────
    t1 = F14.testo_unico("P1")
    letto1, d1 = p1(g, scena, t1)
    ev1 = [salva("p1-sana.json", d1)]
    e, perche = F14.giudica_testo(t1, letto1)
    if e == S.PASS:
        perche += " · in the computer's clipboard after %.2f s" % d1["entro_s"]
    else:
        perche = "within %.0f s of the Ctrl+C (still for %.0f s, no click) the computer's " \
                 "clipboard does not have the text: %s" % (TETTO_P1_S, FERMO_P1_S, perche)
        if d1.get("computer_dopo_5s") == t1:
            perche += " · it arrives AFTER the 3 s"
        if (d1.get("stato_dopo") or {}).get("in_attesa"):
            perche += " · the page keeps it «waiting for a gesture»"
        if not d1.get("gesto_arrivato"):
            e, perche = S.BLOCKED, ("the Ctrl+C did not reach the session's "
                                    "application: it is the keyboard — " + perche)
    E.metti("F-015C", e, perche, atteso=t1, osservato=letto1, evidenze=ev1)

    # ── P2 · F-014C ────────────────────────────────────────────────────────
    giri = []
    for i in range(GIRI_P2 + 3):
        if sum(1 for r in giri if r["gesto"]) >= GIRI_P2:
            break
        r = p2_giro(g, scena, geo, "P2%d" % i)
        giri.append(r)
        print("   P2 round %d: %s (Ctrl+V %s, announcements %s)" % (
            i + 1, "right" if r["visto"] == r["atteso"] else
            ("OLD TEXT of the session" if r["visto"] == r["remoto"] else
             "wrong: %r" % (r["visto"] or "")[:40]),
            "arrived" if r["gesto"] else "NOT arrived", r.get("annunci")), flush=True)
        if r["visto"] != r["atteso"] and not any(x.get("foto") for x in giri):
            r["foto"] = s.foto("p2-giro%d-sbagliato" % (i + 1))[1]
    _png, foto2 = s.foto("p2-fine")
    ev2 = [salva("p2-sana.json", {"giri": giri, "diario": g.js(F14.DIARIO)})]
    ev2 += [x for x in [foto2] + [r.get("foto") for r in giri] if x]
    e, perche = giudica_giri(giri, GIRI_P2)
    E.metti("F-014C", e, perche, atteso=" | ".join(r["atteso"] for r in giri),
            osservato=" | ".join(repr(r["visto"]) for r in giri), evidenze=ev2)

    # ── P1b · F-014D ───────────────────────────────────────────────────────
    xb = F14.testo_unico("P1b")
    v1, v2, db = p1b(g, scena, geo, xb, xb)
    evb = [salva("p1b-sana.json", db)]
    e, perche = giudica_p1b(xb, v1, v2, db)
    E.metti("F-014D", e, perche, atteso=xb, osservato="%r | %r" % (v1, v2), evidenze=evb)

    if not o.guasto:
        return
    # ── THE FAULTS ─────────────────────────────────────────────────────────
    ad1 = F14.giudica_testo(F14.senza_accenti(t1), letto1)[0] == S.FAIL
    g1 = F14.testo_unico("P1G")
    lg1, dg1 = p1(g, scena, g1, copia=False)
    salva("p1-guasto.json", dg1)
    r1 = F14.giudica_testo(g1, lg1)[0] == S.FAIL
    E.guasto("F-015C", r1 and ad1,
             "Ctrl+C not made ⇒ the computer's clipboard is %r (%s); expected without "
             "accents ⇒ %s" % ((lg1 or "")[:50], "ROSSO" if r1 else "VERDE",
                               "ROSSO" if ad1 else "VERDE"), atteso=g1, osservato=lg1)

    ad2 = all(F14.giudica_testo(F14.senza_accenti(r["atteso"]), r["visto"])[0] == S.FAIL
              for r in giri)
    rg = p2_giro(g, scena, geo, "P2G", copia_fuori=False)
    salva("p2-guasto.json", rg)
    r2 = rg["visto"] != rg["atteso"]
    E.guasto("F-014C", (r2 and ad2) if rg["gesto"] else None,
             "wl-copy not made ⇒ the field is %r (%s); expected without accents ⇒ %s"
             % ((rg["visto"] or "")[:50], "ROSSO" if r2 else "VERDE",
                "ROSSO" if ad2 else "VERDE"), atteso=rg["atteso"], osservato=rg["visto"])

    adb = F14.giudica_testo(F14.senza_accenti(xb), v2)[0] == S.FAIL
    xg = F14.testo_unico("P1bG")
    yg = F14.testo_unico("P1bY")
    gv1, gv2, dgb = p1b(g, scena, geo, xg, yg)
    salva("p1b-guasto.json", dgb)
    rb = giudica_p1b(xg, gv1, gv2, dgb)[0] != S.PASS
    gesti = dgb["primo"]["gesto_arrivato"] and dgb["secondo"]["gesto_arrivato"]
    E.guasto("F-014D", (rb and adb) if gesti else None,
             "the second copy is another text ⇒ the field is %r (%s); expected without "
             "accents ⇒ %s" % ((gv2 or "")[:50], "ROSSO" if rb else "VERDE",
                               "ROSSO" if adb else "VERDE"), atteso=xg, osservato=gv2)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
