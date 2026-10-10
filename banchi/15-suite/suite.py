#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
15-suite — THE COMMON BASE OF THE FUNCTIONAL SUITE TESTS (phase 15)
===========================================================================

Each test of the suite is a script `15-fNNN-<name>.py` in this folder.
It can look at ONE function or a group (one session, several functions in a row,
like a real user).  They all speak the same language:

  command line (`argomenti()`):
      --scatola gnome|kde|xfce|lxqt   --browser firefox|chrome   (ONE only)
      --guasto        after the healthy pass, the pass with the INJECTED FAULT
                      in the same session (outcome reversed: seen = good)
      --certifica     only the pure functions (no box, no browser)
      --evidenze DIR  where to put photos, console, log (creates it)
      --porte-base N  debug ports of the browsers (Firefox N, Chrome N+1):
                      ⛔ different for each desktop running in parallel
      --host, --largo, --alto (4K by default: the specifications are 4K)

  output: one line per function looked at, which the round collects in the register

      SUITE {"funzione": "F-004", "passata": "sana"|"guasto",
             "esito": "PASS"|"FAIL"|"BLOCKED", "ragione": "...",
             "atteso": "...", "osservato": "...", "guasto_visto": true|false|null,
             "evidenze": ["percorso", ...], "versione": "Firefox 140.x"}

  exit code: 0 all PASS (and the faults seen) · 1 at least one FAIL
                   (or a fault NOT seen) · 3 at least one BLOCKED and no FAIL

⛔ THE RULES OF THE SUITE (fasi/15-suite-funzionale.md):
  - REAL BROWSERS (Firefox with Marionette, Chrome with CDP), real windows in
    the server's screenless labwc at 3840x2160; the Python client does not certify;
  - the judgment comes from the PHOTO or from the value of a FIELD, never from a
    counter («a wrong frame counts as a right one»);
  - BLOCKED = I could not look, WITH THE REASON: a BLOCKED is not a PASS;
  - every test has its INJECTED FAULT: a test that has never given red
    is not a test;
  - every test < 10 minutes;
  - the tenant is named `c15<nnn>u<n>` (C19 and the clear-out recognise it:
    `^c[0-9]+b?u[0-9]+$`) and is ALWAYS cleared out, even if the test falls over.

It relies on (imported, not copied) `12-client-veri.py` (the browser
drivers, `Prova`: apri/entra/primo_fotogramma), `12-c20-veri.py` (`Scatola`:
commands inside the box, server log, create/clear out tenants) and
`11-c21-…` (full-resolution photo, known window, coordinate conversions).
"""
import argparse
import importlib.util as _iu
import json
import os
import random
import re
import secrets
import sys
import time
import traceback

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


C21 = _carica("c21", os.path.join(BANCHI, "11-scatole", "11-c21-sul-bordo-la-forma-cambia.py"))
C20V, VERI = C21.C20V, C21.VERI
VERDE, ROSSO, CIECO = C21.VERDE, C21.ROSSO, C21.CIECO
PORTE = dict(C20V.PORTE)


# ⭐ ON THE SERVER the commands inside the boxes go with LOCAL `sudo podman exec`,
#   not over ssh to the server itself: `[M]` 24 Sep 2026, ten agents together,
#   sshd cut off some of them («Connection closed … port 22») ⇒ tenants not
#   created, BLOCKED that were not the product's (finding of group G7).
def _dentro_locale(self, riga, secondi=90):
    import subprocess
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.contenitore,
                            "sh", "-c", riga], input=_parola_sudo(), capture_output=True,
                           text=True, errors="replace", timeout=secondi)
    except subprocess.TimeoutExpired:
        return None, "(no answer in %d s)" % secondi
    return r.returncode, (r.stdout + r.stderr).strip()


if os.environ.get("REMOTIX_SUL_SERVER") == "1":
    C20V.Scatola.dentro = _dentro_locale
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
MODELLO_INQUILINO = re.compile(r"^c15[0-9]{3}u[0-9]+$")
PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
DA_CODICE = {VERDE: PASS, ROSSO: FAIL, CIECO: BLOCKED}


def _parola_sudo():
    """The server's sudo password: from REMOTIX_PAROLA_SUDO, or from the «pass:» line of
    ~/SERVER.ssh (the same file as fondamenta/strumenti/sshpw.py). ⛔ Never written
    in the benches: they are in the repository."""
    p = os.environ.get("REMOTIX_PAROLA_SUDO")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"


# ═══════════════════════════════════════════════════════════════════════════
#  THE COMMAND LINE
# ═══════════════════════════════════════════════════════════════════════════
def argomenti(doc, extra=None):
    """The common options.  `extra(a)` adds those of the test."""
    a = argparse.ArgumentParser(description=doc,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=DESKTOP)
    # ⭐ «telefono» = Chrome on the user's REAL phone (phase 19 §5), driven from the
    #   laptop: `banchi/19-android/` (the driver is `telefono.py`)
    a.add_argument("--browser", choices=("firefox", "chrome", "telefono"), default="firefox")
    a.add_argument("--guasto", action="store_true",
                   help="also the pass with the injected fault, in the same session")
    a.add_argument("--certifica", action="store_true",
                   help="only the pure functions: no box, no browser")
    a.add_argument("--evidenze", default="")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--porta", type=int, default=0,
                   help="a server other than the box's (short clocks, ban)")
    a.add_argument("--porte-base", type=int, default=0)
    a.add_argument("--visibile", action="store_true", default=True)
    a.add_argument("--headless", dest="visibile", action="store_false")
    a.add_argument("--tetto-s", type=int, default=45)
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    if extra:
        extra(a)
    o = a.parse_args()
    if not o.certifica and not o.scatola:
        a.error("--scatola is needed (or --certifica)")
    if not o.porte_base:
        # ⛔ one pair of ports per desktop: the four run together
        o.porte_base = 3100 + 10 * DESKTOP.index(o.scatola or "gnome")
    if o.evidenze:
        os.makedirs(o.evidenze, exist_ok=True)
    # the fields that the drivers and `Prova` of 12-client-veri expect
    o.url = "https://%s:%d/" % (o.host, o.porta or PORTE.get(o.scatola or "gnome"))
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    o.salva = ""
    if o.browser == "telefono":
        o.largo = 0          # the phone does the sizing: no window to size
    return o


# ═══════════════════════════════════════════════════════════════════════════
#  THE OUTCOMES
# ═══════════════════════════════════════════════════════════════════════════
class Esiti:
    """Collects and prints the SUITE lines; gives the exit code."""

    def __init__(self, o):
        self.o = o
        self.righe = []
        self.versione = ""

    def metti(self, funzione, esito, ragione, atteso="", osservato="",
              evidenze=None, passata="sana", guasto_visto=None, **altro):
        if esito in DA_CODICE:
            esito = DA_CODICE[esito]
        assert esito in (PASS, FAIL, BLOCKED), esito
        if esito in (FAIL, BLOCKED) and not ragione:
            ragione = "(no reason given: bench defect)"
        r = {"funzione": funzione, "passata": passata, "esito": esito,
             "ragione": ragione, "atteso": atteso, "osservato": osservato,
             "guasto_visto": guasto_visto, "evidenze": list(evidenze or []),
             "versione": self.versione}
        r.update(altro)
        self.righe.append(r)
        segno = {PASS: "⭐ PASS", FAIL: "⛔ FAIL", BLOCKED: "⚠ BLOCKED"}[esito]
        print("   %s %s [%s] %s" % (funzione, segno, passata, ragione), flush=True)
        print("SUITE " + json.dumps(r, ensure_ascii=False), flush=True)
        return r

    def guasto(self, funzione, visto, ragione, **k):
        """⭐ The fault pass: `visto` True = the test gave red on the
        fault (good) ⇒ PASS; False ⇒ FAIL (the test cannot give red);
        None ⇒ BLOCKED (it could not be injected or looked at)."""
        esito = BLOCKED if visto is None else (PASS if visto else FAIL)
        return self.metti(funzione, esito, ragione, passata="guasto",
                          guasto_visto=visto, **k)

    def bloccate(self, funzioni, ragione, passata="sana"):
        """All the functions not yet judged become BLOCKED."""
        fatte = {(r["funzione"], r["passata"]) for r in self.righe}
        for f in funzioni:
            if (f, passata) not in fatte:
                self.metti(f, BLOCKED, ragione, passata=passata)

    def codice(self):
        e = [r["esito"] for r in self.righe]
        if not e:
            return 3
        return 1 if FAIL in e else (3 if BLOCKED in e else 0)


# ═══════════════════════════════════════════════════════════════════════════
#  THE SESSION: tenant, browser, login, first frame
# ═══════════════════════════════════════════════════════════════════════════
class Sessione:
    """
        with Sessione(o, "004", esiti) as s:      # creates c15004u<n>, starts the browser
            ok, perche = s.entra()                # page, form, admission, 1st image
            ...  s.g (driver), s.pr (Prova), s.sc (Scatola), s.chi, s.parola
    On exit it closes the browser and CLEARS OUT the tenant (even if the test falls over).
    `inquilino=False` creates nobody (negative tests: nonexistent user).
    """

    def __init__(self, o, nnn, esiti, inquilino=True, chi=None, parola=None):
        # ⚠ REMOTIX_NNN: the tenant's three digits imposed from outside, for the
        #   agents running in parallel on the same box (c15<nnn>u<n>).
        nnn = os.environ.get("REMOTIX_NNN") or nnn
        self.o, self.nnn, self.esiti = o, nnn, esiti
        self.sc = C20V.Scatola(o.scatola)
        self.chi = chi or "c15%su%d" % (nnn, random.randint(100, 999))
        assert MODELLO_INQUILINO.match(self.chi), self.chi
        self.parola = parola or "c15-" + secrets.token_hex(6)
        self.crea_inquilino = inquilino
        self.g = None
        self.pr = None
        self._foto = 0

    # -- life cycle -----------------------------------------------------------
    def __enter__(self):
        self.o.utente = self.chi
        if self.crea_inquilino:
            self.sc.sgombera(self.chi)
            c, t = self.sc.crea(self.chi, self.parola)
            if c != 0:
                raise Bloccata("I could not create the tenant %s: %s" % (self.chi, t[-200:]))
            # ⛔ the REAL `~/.cache` (src/provisiona.sh, 25 Aug 2026): in the gnome
            #   box `/etc/skel/.cache` points to /tmp, and the first tenant that opens
            #   firefox-esr takes /tmp/mozilla with mode 0700 ⇒ for the others
            #   «Your Firefox profile cannot be loaded» (finding G5, 25 Sep 2026)
            self.sc.dentro("h=/home/%s; [ -L $h/.cache ] && rm -f $h/.cache; "
                           "install -d -o %s -g %s -m 700 $h/.cache" % (
                               self.chi, self.chi, self.chi), 30)
        self.accendi_browser()
        return self

    def __exit__(self, tipo, val, tb):
        self.spegni_browser()
        if self.crea_inquilino:
            try:
                self.sc.sgombera(self.chi)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ clear-out of %s: %s" % (self.chi, e))
        return False

    def accendi_browser(self):
        try:
            if self.o.browser == "telefono":
                self.g = telefono().GuidaTelefono(self.o)
            else:
                self.g = VERI.accendi_guida(self.o.browser, self.o)
        except Exception as e:                   # noqa: BLE001
            raise Bloccata("the browser did not start: %s" % str(e)[:300])
        try:
            self.esiti.versione = self.g.palco()
        except Exception:                        # noqa: BLE001
            self.esiti.versione = self.o.browser
        if self.o.largo:
            try:
                print("   %s" % C20V.dimensiona(self.g, self.o.browser, self.o.largo,
                                               self.o.alto), flush=True)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ dimensiona: %s" % e)
        self.pr = VERI.Prova(self.g, self.o, self.o.url, self.parola)

    def spegni_browser(self):
        if self.g is not None:
            try:
                self.g.chiudi()
            except Exception as e:               # noqa: BLE001
                print("   ⚠ closing the browser: %s" % e)
            self.g = None

    # -- the login ------------------------------------------------------------
    def entra(self, parola=None, apri=True):
        """(True, reason) if: page open, form, admitted, first frame
        not degenerate.  Otherwise (False, reason)."""
        if apri:
            ok, m = self.pr.apri()
            if not ok:
                return False, "the page does not open: " + m
        e, m, _s = self.pr.entra(parola or self.parola)
        if e != VERDE:
            return False, "the login: " + m
        e, m, s = self.pr.primo_fotogramma()
        e, m = C20V.desktop_scuro_ma_vivo(e, m, s)
        if e != VERDE:
            return False, "the first frame: " + m
        return True, m

    def stato(self):
        return self.pr.stato()

    # -- the photos -----------------------------------------------------------
    def foto(self, nome):
        """⭐ The canvas at FULL resolution: (png | None, path | reason).
        Saved in the evidence if there is any."""
        try:
            png = C21.foto_piena(self.g)
        except Exception as e:                   # noqa: BLE001
            return None, "photo failed: %s" % str(e)[:200]
        if not png:
            return None, "the canvas is not there or has no visible area"
        self._foto += 1
        percorso = ""
        if self.o.evidenze:
            percorso = os.path.join(self.o.evidenze, "%02d-%s.png" % (self._foto, nome))
            with open(percorso, "wb") as f:
                f.write(png)
        return png, percorso

    def geometria(self):
        """The geometry of the canvas in the glass (C21.JS_GEOMETRIA)."""
        return self.g.js(C21.JS_GEOMETRIA)

    # -- the server -----------------------------------------------------------
    def segno_registro(self):
        return self.sc.righe_registro()

    def registro_da(self, segno):
        return self.sc.registro_da(segno or 0, self.chi)

    def salva_testo(self, nome, righe):
        if not self.o.evidenze:
            return ""
        p = os.path.join(self.o.evidenze, nome)
        with open(p, "w") as f:
            f.write("\n".join(righe) if isinstance(righe, (list, tuple)) else str(righe))
        return p

    def salva_console(self):
        """The browser's JS and network errors, in the evidence."""
        try:
            js, rete, _ = self.g.errori_fuori()
        except Exception as e:                   # noqa: BLE001
            js, rete = ["(not read: %s)" % e], []
        return self.salva_testo("console-%s.txt" % self.o.browser, js + rete)

    def come_utente(self, comando, secondi=60):
        return self.sc.come_utente(self.chi, comando, secondi)

    def nella_sessione(self, comando, secondi=60, fondo=True):
        """Runs `comando` as the tenant INSIDE their graphical session
        (WAYLAND_DISPLAY of their compositor, session bus).  `fondo` detaches
        it (setsid … &) and returns at once."""
        amb = ("u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
               "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
               % {"c": self.chi})
        corpo = ("runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
                 "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
                 "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s sh -c %(q)s"
                 % {"c": self.chi, "q": _q(comando)})
        if fondo:
            corpo = "setsid %s < /dev/null > /home/%s/.c15-%s.log 2>&1 & echo launched" % (
                corpo, self.chi, re.sub(r"\W", "", comando.split()[0])[:20])
        return self.sc.dentro(amb + corpo, secondi)


class Bloccata(Exception):
    """The test could not look: it becomes BLOCKED with this reason."""


_TELEFONO = []


def telefono():
    """The module of the real phone's driver (`banchi/19-android/telefono.py`),
    loaded only once and only by whoever uses it."""
    if not _TELEFONO:
        _TELEFONO.append(_carica("telefono", os.path.join(BANCHI, "19-android", "telefono.py")))
    return _TELEFONO[0]


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


# ═══════════════════════════════════════════════════════════════════════════
#  THE BODY OF EVERY TEST
# ═══════════════════════════════════════════════════════════════════════════
def esegui(doc, funzioni, corpo, certifica=None, extra=None):
    """The `main` of every test.

    funzioni   the F-NNN the test looks at (for the automatic BLOCKEDs)
    corpo(o, esiti)       the real test: puts the outcomes with `esiti.metti`
    certifica()           the pure functions: returns 0 if all right
    """
    o = argomenti(doc, extra)
    if o.certifica:
        if not certifica:
            print("⚠ this test has no pure functions to certify")
            return 0
        return certifica()
    esiti = Esiti(o)
    t0 = time.time()
    print("⭐ %s · %s · %s · %s%s" % (os.path.basename(sys.argv[0]), o.scatola, o.browser,
                                      o.url, " · + GUASTO" if o.guasto else ""), flush=True)
    try:
        corpo(o, esiti)
    except Bloccata as b:
        esiti.bloccate(funzioni, str(b))
        if o.guasto:
            esiti.bloccate(funzioni, str(b), passata="guasto")
    except Exception as e:                       # noqa: BLE001
        tb = traceback.format_exc()
        print(tb)
        esiti.bloccate(funzioni, "the bench fell over: %r" % e)
        if o.guasto:
            esiti.bloccate(funzioni, "the bench fell over: %r" % e, passata="guasto")
    esiti.bloccate(funzioni, "the test gave no judgment (bench defect)")
    if o.guasto:
        esiti.bloccate(funzioni, "the fault pass gave no judgment",
                       passata="guasto")
    print("⏱ %.0f s · codice %d" % (time.time() - t0, esiti.codice()), flush=True)
    return esiti.codice()
