#!/usr/bin/env python3
"""12-c20-veri — C20 WITH REAL BROWSERS: after "Log out" and a new login from
the same page, the screen does not flicker.

    python3 banchi/12-c20-veri.py --scatola gnome [--browser firefox,chrome]
        [--visibile] [--salva DIR] [--attesa-rientro 3]

⛔ WHY IT EXISTS.  `11-c20-…py` (the network mesh) uses the Python client,
   and on 23 Sep 2026, evening, on gnome it gave "I could not look": the
   second login is ADMITTED and one second later it is the CLIENT that closes
   the connection (in the server log the closing is silent, that is, in
   draining: the other side asked for it).  Then the mesh, giving up, runs
   `loginctl terminate-user` — and that is the signal 15 that was read in the
   journal.  ⇒ The Python client can point where to look, ⛔ but it cannot
   certify nor clear: the user, 23 Sep 2026, *"tests must be done with
   real browsers, not with emulators"*.

⭐ WHAT IT DOES, for each browser (Firefox with Marionette, Chrome with CDP, the
   drivers are those of `12-client-veri.py`, ⛔ not a copy):
     1  opens the page, logs in, waits for the first non-degenerate frame
     2  inside the session, the "Log out" gesture OF THE MENU (C20's table)
     3  waits for the product to declare the session over (C20's two
        forms) and looks at what the PAGE does: back to the form? with which sentence?
     4  after `--attesa-rientro` seconds it logs in again FROM THE SAME PAGE, as
        the user does — and if the form is not there, it reloads (and says so)
     5  first frame, then it starts C20's scene in the session (constant
        light, scrolling bands) and photographs the canvas for `--guarda-s`
     6  judges the luminances with C20's judge (⛔ the same one, imported):
        a flicker between desktop, logout screen and black is RED
   Outcomes: 0 green · 1 red · 3 I could not look, with the reason.

⚠ The box is entered with `fondamenta/strumenti/sshpw.py` and `sudo podman
  exec rete11-<scatola>`: it is the same route as `11-gancio.sh remoto`.
⚠ The tenant is `c20u7<n>`, inside the network's namespace: if this bench
  died halfway, the hook clears it out and C19 sees it.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import random
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
SSHPW = os.path.join(RADICE, "fondamenta", "strumenti", "sshpw.py")
REGISTRO = "/var/lib/rete11/registro.log"
SCENA_DENTRO = "/opt/remotix/11-c20-scena.html"
PORTE = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


VERI = _carica("client_veri", os.path.join(QUI, "12-client-veri.py"))
C20 = _carica("c20", os.path.join(QUI, "11-scatole",
                                  "11-c20-la-rinascita-non-porta-fantasmi.py"))
VERDE, ROSSO, CIECO = VERI.VERDE, VERI.ROSSO, VERI.CIECO


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE BOX
# ═══════════════════════════════════════════════════════════════════════════
class Scatola:
    def __init__(self, nome):
        self.nome = nome
        self.contenitore = "rete11-%s" % nome

    def dentro(self, riga, secondi=90):
        """(code, output) of `riga` run as root in the box.

        ⚠ The line travels in base64: no quote to escape across three
          shells (tablet → ssh → sudo → podman → sh)."""
        b = base64.b64encode(riga.encode()).decode()
        remoto = ("sudo -S -p 'Password sudo: ' podman exec %s sh -c "
                  "\"$(echo %s | base64 -d)\"; echo \"@@codice=$?\""
                  % (self.contenitore, b))
        try:
            r = subprocess.run([sys.executable, SSHPW, remoto], capture_output=True,
                               text=True, errors="replace", timeout=secondi)
        except subprocess.TimeoutExpired:
            return None, "(no answer in %d s)" % secondi
        testo = "\n".join(x for x in r.stdout.splitlines()
                          if not x.startswith("tput:") and "Password sudo" not in x)
        codice = None
        if "@@codice=" in testo:
            testo, _, c = testo.rpartition("@@codice=")
            try:
                codice = int(c.strip())
            except ValueError:
                codice = None
        return codice, testo.strip()

    def righe_registro(self):
        c, t = self.dentro("wc -l < %s" % REGISTRO, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError):
            return None

    def registro_da(self, segno, chi):
        _c, t = self.dentro("tail -n +%d %s | grep -a -- '%s'" % (segno + 1, REGISTRO, chi),
                            60)
        return t.splitlines()

    def gesto_esci(self):
        """(desktop, gesture) — the same question as C20, asked inside."""
        for nome, ci_vuole, non_ci_vuole, gesto in C20.DESKTOP_E_GESTO:
            c, _ = self.dentro("command -v %s >/dev/null 2>&1" % ci_vuole, 30)
            if c != 0:
                continue
            if non_ci_vuole:
                c2, _ = self.dentro("command -v %s >/dev/null 2>&1" % non_ci_vuole, 30)
                if c2 == 0:
                    continue
            return nome, gesto
        return None, None

    def come_utente(self, chi, comando, secondi=60):
        return self.dentro(
            "u=$(id -u %s) && runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus %s 2>&1"
            % (chi, chi, comando), secondi)

    def accendi_scena(self, chi):
        c, t = self.dentro(
            "u=$(id -u %s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
            "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
            "[ -f %s ] || { echo 'missing %s'; exit 2; }; "
            "setsid runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
            "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
            "firefox-esr --kiosk file://%s < /dev/null > /home/%s/.c20v-scena.log 2>&1 & "
            "for i in $(seq 1 40); do pgrep -u %s -f firefox-esr >/dev/null && "
            "{ echo started; exit 0; }; sleep 0.25; done; echo 'it was not seen'; exit 1"
            % (chi, SCENA_DENTRO, SCENA_DENTRO, chi, chi, SCENA_DENTRO, chi, chi), 60)
        return c == 0, t

    def crea(self, chi, parola):
        return self.dentro(
            "useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
            % (chi, chi, parola), 60)

    def sgombera(self, chi):
        # ⛔ `[c]20u7…`: `pkill -f` would catch the shell that runs it.
        self.dentro("loginctl terminate-user %s >/dev/null 2>&1; "
                    "pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null; "
                    "pkill -KILL -u %s >/dev/null 2>&1; sleep 0.5; "
                    "userdel -r %s >/dev/null 2>&1 || userdel %s >/dev/null 2>&1; "
                    "rm -rf /home/%s"
                    % (chi, chi[0], chi[1:], chi, chi, chi, chi), 90)


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def luminanza(png):
    """The mean luminance of the canvas photograph, or None."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("L").resize(
            (C20.LARGHEZZA, C20.ALTEZZA))
        px = list(im.getdata())
        return sum(px) // len(px)
    except Exception:                            # noqa: BLE001
        return None


def desktop_scuro_ma_vivo(e, m, s):
    """⭐ (outcome, reason) of the first frame, with the 4K tolerance.

    ⛔ `[M]` 23 Sep 2026, xfce in 4K: the box's background is BLACK, and at
       3840x2160 panel, icons and clock cover 2.7 % ⇒ the judge of
       `12-client-veri` (dominant >= 97 %) called it "degenerate" — but the
       photograph showed the real desktop.  ⇒ Here a desktop with painted
       frames and AT LEAST 40 distinct colours is alive: the real judgement of
       this bench is the scene started afterwards, not the first frame."""
    if e == VERDE:
        return e, m
    import re
    c = re.search(r"distinct colours (\d+)", m or "")
    if (s or {}).get("dipinti") and c and int(c.group(1)) >= 40:
        return VERDE, "dark but alive desktop (%s distinct colours): %s" % (c.group(1), m)
    return e, m


def aspetta_riga(sc, segno, chi, forme, tetto):
    fine = time.time() + tetto
    while time.time() < fine:
        for r in sc.registro_da(segno, chi):
            for f in forme:
                if f in r:
                    return f, r
        time.sleep(2)
    return None, None


def dimensiona(g, nome, largo, alto):
    """⭐ The window at the size of the specification (4K), and it is READ BACK.

    ⚠ The drivers of `12-client-veri.py` are born at 1400x1000; here the size is
      asked afterwards, and what counts is `innerWidth` read from the page."""
    try:
        if nome == "firefox":
            g.m.chiama("WebDriver:SetWindowRect",
                       {"x": 0, "y": 0, "width": largo, "height": alto})
        elif nome == "chrome":
            # ⚠ `[M]` 23 Sep 2026, inside labwc: the size asked with numbers
            #   Chrome ignores (it stayed 1376x888); the "maximised" state is
            #   honoured by the compositor.  That is asked first, then the numbers.
            w = g.cdp.chiama("Browser.getWindowForTarget")
            wid = w.get("windowId") if isinstance(w, dict) else None
            if wid is None and isinstance(w, dict):
                wid = (w.get("result") or {}).get("windowId")
            g.cdp.chiama("Browser.setWindowBounds", windowId=wid,
                         bounds={"windowState": "maximized"})
    except Exception as e:                       # noqa: BLE001
        return "⚠ size not changed: %s" % str(e)[:120]
    time.sleep(1)
    try:
        return "window %sx%s (dpr %s)" % tuple(g.js(
            "return [innerWidth, innerHeight, devicePixelRatio]"))
    except Exception as e:                       # noqa: BLE001
        return "⚠ size not read back: %s" % str(e)[:120]


def un_browser(nome, o, sc, chi, gesto):
    print("\n══ %s ══════════════════════════════" % nome.upper(), flush=True)
    esito = {"browser": nome}
    g = VERI.accendi_guida(nome, o)
    try:
        print("   stage: %s" % g.palco(), flush=True)
        if o.largo:
            esito["finestra"] = dimensiona(g, nome, o.largo, o.alto)
            print("   %s" % esito["finestra"], flush=True)
        pr = VERI.Prova(g, o, o.url, o.parola)

        # ── 1. the first login ─────────────────────────────────────────────
        ok, m = pr.apri()
        if not ok:
            return dict(esito, esito=CIECO, perche="the page does not open: " + m)
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            return dict(esito, esito=CIECO, perche="first login: " + m)
        e, m, s = pr.primo_fotogramma()
        e, m = desktop_scuro_ma_vivo(e, m, s)
        print("   ⭐ first login: %s" % m, flush=True)
        if e != VERDE:
            return dict(esito, esito=CIECO, perche="first login without image: " + m)
        time.sleep(o.primo_s)

        # ── 2. "Log out", the menu gesture ───────────────────────────────
        segno = sc.righe_registro()
        if segno is None:
            return dict(esito, esito=CIECO, perche="I cannot read the server log")
        c, t = sc.come_utente(chi, gesto)
        if c != 0:
            return dict(esito, esito=CIECO, perche="the «Log out» gesture did not answer "
                        "(code %s): %s" % (c, t[-300:]))
        t_esci = time.time()
        forma, riga = aspetta_riga(sc, segno, chi, [p for p, _d in C20.RIGHE_FINITA],
                                   o.attesa_uscita)
        if not forma:
            return dict(esito, esito=CIECO, perche="%d s after «Log out» the product has not "
                        "declared the session over" % o.attesa_uscita)
        print("   ⭐ «Log out»: after %.1f s the product says «%s»"
              % (time.time() - t_esci, forma), flush=True)

        # ── 3. what the PAGE does ──────────────────────────────────────────
        modulo, pagina = False, {}
        fine = time.time() + 30
        while time.time() < fine:
            try:
                mm = g.js(VERI.JS_MODULO)
                if mm and mm.get("modulo") and mm.get("visibile"):
                    modulo = True
                    break
            except Exception:                    # noqa: BLE001
                pass
            time.sleep(0.5)
        pagina = pr.stato()
        print("   %s the page after «Log out»: form %s · outcome «%s»"
              % ("⭐" if modulo else "⚠", "VISIBLE" if modulo else "NOT visible",
                 (pagina.get("esito") or "")[:120]), flush=True)
        esito["pagina_dopo_esci"] = {"modulo": modulo, "esito": pagina.get("esito")}

        # ── 4. the new login, FROM THE SAME PAGE ───────────────────────────
        time.sleep(o.attesa_rientro)
        segno2 = sc.righe_registro() or segno
        if not modulo:
            print("   ⚠ the form is not there: reloading, as the user would", flush=True)
            g.ricarica()
            ok, m = pr.apri_dopo_ricarica()
            if not ok:
                return dict(esito, esito=CIECO, perche="after the reload: " + m)
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            # ⛔ Here the red is the PRODUCT's: after "Log out" the user cannot get back in.
            coda = [x for x in (s or {}).get("registro", "").splitlines() if x.strip()][-6:]
            return dict(esito, esito=ROSSO, perche="after «Log out» it does NOT GET BACK IN: %s" % m,
                        pagina=coda, server=sc.registro_da(segno2, chi)[-25:])
        e, m, s = pr.primo_fotogramma()
        e, m = desktop_scuro_ma_vivo(e, m, s)
        print("   %s second login: %s" % ("⭐" if e == VERDE else "⛔", m), flush=True)
        if e != VERDE:
            return dict(esito, esito=ROSSO if e == ROSSO else CIECO,
                        perche="second login without image: " + m,
                        server=sc.registro_da(segno2, chi)[-25:])

        # ── 5. the scene, and the canvas photographed ──────────────────────
        accesa, t = sc.accendi_scena(chi)
        if not accesa:
            return dict(esito, esito=CIECO, perche="the scene does not start: %s" % t[-160:])
        print("   ⭐ scene started (%s)" % os.path.basename(SCENA_DENTRO), flush=True)
        lum, d0 = [], (pr.stato().get("dipinti") or 0)
        fine = time.time() + o.guarda_s
        while time.time() < fine:
            try:
                png, _p = g.fotografa_tela()
            except Exception:                    # noqa: BLE001
                png = None
            if png:
                v = luminanza(png)
                if v is not None:
                    lum.append(v)
                if o.salva and len(lum) % 10 == 1:
                    with open(os.path.join(o.salva, "%s-%03d.png" % (nome, len(lum))),
                              "wb") as f:
                        f.write(png)
            time.sleep(o.passo_s)
        s = pr.stato()
        d1 = s.get("dipinti") or 0
        print("   luminances (%d photographs, %d frames painted): %s"
              % (len(lum), d1 - d0, " ".join(str(x) for x in lum[:80])), flush=True)
        ep, salti, perche = C20.giudica_i_pixel(lum)
        server = sc.registro_da(segno2, chi)
        interessanti = [r for r in server if any(k in r for k in (
            "child spawned", "REAPED", "IS OVER", "has gone", "throwing away",
            "RESTARTING THE CAPTURE", "farewell", "closed"))]
        return dict(esito, esito=ep, perche=perche, salti=salti, fotografie=len(lum),
                    dipinti=d1 - d0, server=interessanti[-20:])
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", default="gnome", choices=sorted(PORTE))
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true")
    a.add_argument("--salva", default="")
    a.add_argument("--primo-s", type=float, default=5.0,
                   help="how long the first login stays before «Log out»")
    a.add_argument("--attesa-uscita", type=float, default=120.0)
    a.add_argument("--attesa-rientro", type=float, default=3.0,
                   help="seconds between the session ending and the new login")
    a.add_argument("--guarda-s", type=float, default=30.0)
    a.add_argument("--passo-s", type=float, default=0.2)
    a.add_argument("--tetto-s", type=int, default=45)
    a.add_argument("--porte-base", type=int, default=2951)
    # ⭐ The specification is 4K (the user, 23 Sep 2026): the window is brought to
    #   3840x2160.  `--largo 0` leaves the drivers' size (1400x1000).
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    o = a.parse_args()
    # ⚠ the fields that the drivers and `Prova` of 12-client-veri expect
    o.url = "https://%s:%d/" % (o.host, PORTE[o.scatola])
    o.parola = C20.PAROLA
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = Scatola(o.scatola)
    desktop, gesto = sc.gesto_esci()
    if not gesto:
        print("⛔ I do not know how to say «Log out» in %s ⇒ 3" % sc.contenitore)
        return 3
    chi = "c20u7%02d" % random.randint(0, 99)
    o.utente = chi
    print("⭐ 12-c20-veri · %s (%s) · %s · tenant %s · browser %s · %s"
          % (sc.contenitore, desktop, o.url, chi, o.browser,
             "real windows" if o.visibile else "HEADLESS"))
    print("   «Log out» is said: %s" % gesto)
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = un_browser(b, o, sc, chi, gesto)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "esito": CIECO, "perche": "the bench fell over: %r" % e}
        finally:
            sc.sgombera(chi)
        print("   ▶ %s: %s — %s" % (b, {0: "VERDE", 1: "ROSSO", 3: "I COULD NOT LOOK"}
                                   .get(r["esito"], r["esito"]), r.get("perche")))
        for x in r.get("server") or []:
            print("      server: %s" % x[:200])
        print("RIGA " + json.dumps(r, ensure_ascii=False), flush=True)
        righe.append(r)
    v = [r["esito"] for r in righe]
    return 1 if 1 in v else (3 if 3 in v else 0)


if __name__ == "__main__":
    sys.exit(main())
