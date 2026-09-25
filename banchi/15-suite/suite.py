#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
15-suite — LA BASE COMUNE DELLE PROVE DELLA SUITE FUNZIONALE (fase 15)
===========================================================================

Ogni prova della suite e' uno script `15-fNNN-<nome>.py` in questa cartella.
Puo' guardare UNA funzione o un gruppo (una sessione, piu' funzioni in fila,
come un utente vero).  Tutte parlano la stessa lingua:

  riga di comando (`argomenti()`):
      --scatola gnome|kde|xfce|lxqt   --browser firefox|chrome   (UNO solo)
      --guasto        dopo la passata sana, la passata col GUASTO INNESTATO
                      nella stessa sessione (esito al rovescio: visto = bene)
      --certifica     solo le funzioni pure (niente scatola, niente browser)
      --evidenze DIR  dove mettere foto, console, registro (la crea)
      --porte-base N  porte di debug dei browser (Firefox N, Chrome N+1):
                      ⛔ diverse per ogni desktop che gira in parallelo
      --host, --largo, --alto (4K di default: le specifiche sono 4K)

  uscita: una riga per funzione guardata, che il giro raccoglie nel registro

      SUITE {"funzione": "F-004", "passata": "sana"|"guasto",
             "esito": "PASS"|"FAIL"|"BLOCKED", "ragione": "...",
             "atteso": "...", "osservato": "...", "guasto_visto": true|false|null,
             "evidenze": ["percorso", ...], "versione": "Firefox 140.x"}

  codice d'uscita: 0 tutte PASS (e i guasti visti) · 1 almeno un FAIL
                   (o un guasto NON visto) · 3 almeno un BLOCKED e nessun FAIL

⛔ LE REGOLE DELLA SUITE (fasi/15-suite-funzionale.md):
  - BROWSER VERI (Firefox con Marionette, Chrome con CDP), finestre vere nel
    labwc senza schermo del server a 3840x2160; il cliente Python non certifica;
  - il giudizio viene dalla FOTOGRAFIA o dal valore di un CAMPO, mai da un
    contatore («un fotogramma sbagliato conta come uno giusto»);
  - BLOCKED = non ho potuto guardare, CON LA RAGIONE: un BLOCKED non e' un PASS;
  - ogni prova ha il suo GUASTO INNESTATO: una prova che non ha mai dato rosso
    non e' una prova;
  - ogni prova < 10 minuti;
  - l'inquilino si chiama `c15<nnn>u<n>` (C19 e lo sgombero lo riconoscono:
    `^c[0-9]+b?u[0-9]+$`) e si sgombera SEMPRE, anche se la prova cade.

Si appoggia (importati, non copiati) a `12-client-veri.py` (le guide dei
browser, `Prova`: apri/entra/primo_fotogramma), `12-c20-veri.py` (`Scatola`:
comandi dentro la scatola, registro del server, crea/sgombera inquilini) e
`11-c21-…` (foto a piena risoluzione, finestra nota, conversioni di coordinate).
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


# ⭐ SUL SERVER i comandi dentro le scatole vanno con `sudo podman exec` LOCALE,
#   non per ssh verso il server stesso: `[M]` 24 set 2026, dieci agenti insieme,
#   sshd ne troncava una parte («Connection closed … port 22») ⇒ inquilini non
#   creati, BLOCKED che non erano del prodotto (rilievo del gruppo G7).
def _dentro_locale(self, riga, secondi=90):
    import subprocess
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.contenitore,
                            "sh", "-c", riga], input="nicfio\n", capture_output=True,
                           text=True, errors="replace", timeout=secondi)
    except subprocess.TimeoutExpired:
        return None, "(nessuna risposta in %d s)" % secondi
    return r.returncode, (r.stdout + r.stderr).strip()


if os.environ.get("REMOTIX_SUL_SERVER") == "1":
    C20V.Scatola.dentro = _dentro_locale
DESKTOP = ("gnome", "kde", "xfce", "lxqt")
MODELLO_INQUILINO = re.compile(r"^c15[0-9]{3}u[0-9]+$")
PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
DA_CODICE = {VERDE: PASS, ROSSO: FAIL, CIECO: BLOCKED}


# ═══════════════════════════════════════════════════════════════════════════
#  LA RIGA DI COMANDO
# ═══════════════════════════════════════════════════════════════════════════
def argomenti(doc, extra=None):
    """Le opzioni comuni.  `extra(a)` aggiunge quelle della prova."""
    a = argparse.ArgumentParser(description=doc,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=DESKTOP)
    a.add_argument("--browser", choices=("firefox", "chrome"), default="firefox")
    a.add_argument("--guasto", action="store_true",
                   help="anche la passata col guasto innestato, nella stessa sessione")
    a.add_argument("--certifica", action="store_true",
                   help="solo le funzioni pure: niente scatola, niente browser")
    a.add_argument("--evidenze", default="")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--porta", type=int, default=0,
                   help="un server diverso da quello della scatola (orologi corti, ban)")
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
        a.error("serve --scatola (o --certifica)")
    if not o.porte_base:
        # ⛔ una coppia di porte per desktop: i quattro girano insieme
        o.porte_base = 3100 + 10 * DESKTOP.index(o.scatola or "gnome")
    if o.evidenze:
        os.makedirs(o.evidenze, exist_ok=True)
    # i campi che le guide e `Prova` di 12-client-veri si aspettano
    o.url = "https://%s:%d/" % (o.host, o.porta or PORTE.get(o.scatola or "gnome"))
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    o.salva = ""
    return o


# ═══════════════════════════════════════════════════════════════════════════
#  GLI ESITI
# ═══════════════════════════════════════════════════════════════════════════
class Esiti:
    """Raccoglie e stampa le righe SUITE; da' il codice d'uscita."""

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
            ragione = "(nessuna ragione data: difetto del banco)"
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
        """⭐ La passata col guasto: `visto` True = la prova ha dato rosso sul
        guasto (bene) ⇒ PASS; False ⇒ FAIL (la prova non sa dare rosso);
        None ⇒ BLOCKED (non si e' potuto innestare o guardare)."""
        esito = BLOCKED if visto is None else (PASS if visto else FAIL)
        return self.metti(funzione, esito, ragione, passata="guasto",
                          guasto_visto=visto, **k)

    def bloccate(self, funzioni, ragione, passata="sana"):
        """Tutte le funzioni non ancora giudicate diventano BLOCKED."""
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
#  LA SESSIONE: inquilino, browser, accesso, primo fotogramma
# ═══════════════════════════════════════════════════════════════════════════
class Sessione:
    """
        with Sessione(o, "004", esiti) as s:      # crea c15004u<n>, accende il browser
            ok, perche = s.entra()                # pagina, modulo, ammissione, 1a immagine
            ...  s.g (guida), s.pr (Prova), s.sc (Scatola), s.chi, s.parola
    All'uscita chiude il browser e SGOMBERA l'inquilino (anche se la prova cade).
    `inquilino=False` non crea nessuno (prove negative: utente inesistente).
    """

    def __init__(self, o, nnn, esiti, inquilino=True, chi=None, parola=None):
        self.o, self.nnn, self.esiti = o, nnn, esiti
        self.sc = C20V.Scatola(o.scatola)
        self.chi = chi or "c15%su%d" % (nnn, random.randint(100, 999))
        assert MODELLO_INQUILINO.match(self.chi), self.chi
        self.parola = parola or "c15-" + secrets.token_hex(6)
        self.crea_inquilino = inquilino
        self.g = None
        self.pr = None
        self._foto = 0

    # -- ciclo di vita --------------------------------------------------------
    def __enter__(self):
        self.o.utente = self.chi
        if self.crea_inquilino:
            self.sc.sgombera(self.chi)
            c, t = self.sc.crea(self.chi, self.parola)
            if c != 0:
                raise Bloccata("non ho potuto creare l'inquilino %s: %s" % (self.chi, t[-200:]))
            # ⛔ la `~/.cache` VERA (src/provisiona.sh, 25 ago 2026): nella scatola
            #   gnome `/etc/skel/.cache` punta a /tmp, e il primo inquilino che apre
            #   firefox-esr si prende /tmp/mozilla a modo 0700 ⇒ per gli altri
            #   «Your Firefox profile cannot be loaded» (rilievo G5, 25 set 2026)
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
                print("   ⚠ sgombero di %s: %s" % (self.chi, e))
        return False

    def accendi_browser(self):
        try:
            self.g = VERI.accendi_guida(self.o.browser, self.o)
        except Exception as e:                   # noqa: BLE001
            raise Bloccata("il browser non si e' acceso: %s" % str(e)[:300])
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
                print("   ⚠ chiusura del browser: %s" % e)
            self.g = None

    # -- l'accesso ------------------------------------------------------------
    def entra(self, parola=None, apri=True):
        """(True, motivo) se: pagina aperta, modulo, ammesso, primo fotogramma
        non degenere.  Altrimenti (False, motivo)."""
        if apri:
            ok, m = self.pr.apri()
            if not ok:
                return False, "la pagina non si apre: " + m
        e, m, _s = self.pr.entra(parola or self.parola)
        if e != VERDE:
            return False, "l'accesso: " + m
        e, m, s = self.pr.primo_fotogramma()
        e, m = C20V.desktop_scuro_ma_vivo(e, m, s)
        if e != VERDE:
            return False, "il primo fotogramma: " + m
        return True, m

    def stato(self):
        return self.pr.stato()

    # -- le fotografie --------------------------------------------------------
    def foto(self, nome):
        """⭐ La tela a PIENA risoluzione: (png | None, percorso | motivo).
        Salvata nelle evidenze se ce ne sono."""
        try:
            png = C21.foto_piena(self.g)
        except Exception as e:                   # noqa: BLE001
            return None, "fotografia fallita: %s" % str(e)[:200]
        if not png:
            return None, "la tela non c'e' o non ha area visibile"
        self._foto += 1
        percorso = ""
        if self.o.evidenze:
            percorso = os.path.join(self.o.evidenze, "%02d-%s.png" % (self._foto, nome))
            with open(percorso, "wb") as f:
                f.write(png)
        return png, percorso

    def geometria(self):
        """La geometria della tela nel vetro (C21.JS_GEOMETRIA)."""
        return self.g.js(C21.JS_GEOMETRIA)

    # -- il server ------------------------------------------------------------
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
        """Gli errori JS e di rete del browser, nelle evidenze."""
        try:
            js, rete, _ = self.g.errori_fuori()
        except Exception as e:                   # noqa: BLE001
            js, rete = ["(non letti: %s)" % e], []
        return self.salva_testo("console-%s.txt" % self.o.browser, js + rete)

    def come_utente(self, comando, secondi=60):
        return self.sc.come_utente(self.chi, comando, secondi)

    def nella_sessione(self, comando, secondi=60, fondo=True):
        """Lancia `comando` come l'inquilino DENTRO la sua sessione grafica
        (WAYLAND_DISPLAY del suo compositore, bus di sessione).  `fondo` lo
        stacca (setsid … &) e torna subito."""
        amb = ("u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
               "| head -1); [ -n \"$d\" ] || { echo 'nessun socket wayland'; exit 2; }; "
               % {"c": self.chi})
        corpo = ("runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
                 "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
                 "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s sh -c %(q)s"
                 % {"c": self.chi, "q": _q(comando)})
        if fondo:
            corpo = "setsid %s < /dev/null > /home/%s/.c15-%s.log 2>&1 & echo lanciato" % (
                corpo, self.chi, re.sub(r"\W", "", comando.split()[0])[:20])
        return self.sc.dentro(amb + corpo, secondi)


class Bloccata(Exception):
    """La prova non ha potuto guardare: diventa BLOCKED con questa ragione."""


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


# ═══════════════════════════════════════════════════════════════════════════
#  IL CORPO DI OGNI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def esegui(doc, funzioni, corpo, certifica=None, extra=None):
    """Il `main` di ogni prova.

    funzioni   le F-NNN che la prova guarda (per i BLOCKED d'ufficio)
    corpo(o, esiti)       la prova vera: mette gli esiti con `esiti.metti`
    certifica()           le funzioni pure: torna 0 se tutte giuste
    """
    o = argomenti(doc, extra)
    if o.certifica:
        if not certifica:
            print("⚠ questa prova non ha funzioni pure da certificare")
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
        esiti.bloccate(funzioni, "il banco e' caduto: %r" % e)
        if o.guasto:
            esiti.bloccate(funzioni, "il banco e' caduto: %r" % e, passata="guasto")
    esiti.bloccate(funzioni, "la prova non ha dato un giudizio (difetto del banco)")
    if o.guasto:
        esiti.bloccate(funzioni, "la passata col guasto non ha dato un giudizio",
                       passata="guasto")
    print("⏱ %.0f s · codice %d" % (time.time() - t0, esiti.codice()), flush=True)
    return esiti.codice()
