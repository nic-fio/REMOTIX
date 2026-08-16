#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04-b29 — la sonda delle scorciatoie che il browser si tiene.  ⭐ Misura **S3**.

⛔⛔ LA DOMANDA NON E' «ARRIVA?» MA «ARRIVA **E BASTA**?»

    Gli stati sono TRE, non due (`SPECIFICHE.md` §7.3-bis, `STUDI.md` §web §8-bis O8):

      consegnata              arriva alla sessione remota, e basta
      consegnata E RISERVATA  arriva ALLA PAGINA **e** il browser esegue anche
                              il proprio comando  ⇒ ⛔ IL CASO PEGGIORE
      non consegnata          il browser (o il compositore) se la tiene

    Una prova che guarda solo il lato della sessione **dichiara verde proprio il
    caso peggiore**.  Percio' questa sonda ha DUE colonne, mai una sola, e le
    domande sono due:

      1. la pagina ha visto il `keydown` con quel codice e quei modificatori?
      2. il browser ha fatto anche il suo comando?  — che si legge da: la scheda
         che muore, il documento che rinasce, il fuoco perso, la scheda che si
         nasconde, lo schermo intero che cambia, la stampa che si apre, la
         geometria che salta (i DevTools), e — su Chrome — il conto dei bersagli
         del protocollo di debug, che e' un SECONDO strumento indipendente.

⛔ I CONTROLLI, che sono quel che rende credibile tutto il resto:

    positivo    `Ctrl+Alt+G`  ⇒ DEVE risultare **consegnata e non riservata**.
                Se non arriva, la catena di iniezione e' rotta e la sonda tace.
    negativo    `Super`       ⇒ DEVE risultare **non consegnata**, perche' il
                compositore GNOME se lo tiene sopra la testa del browser — e
                nello stesso colpo **si vede l'effetto** (la panoramica si apre,
                la pagina perde il fuoco), che e' la prova che l'iniezione
                E' ARRIVATA anche quando la pagina non ha visto niente.
                ⭐ Senza questa seconda meta', «non consegnata» e «la mia
                iniezione non e' partita» avrebbero lo stesso aspetto
                (`CODER.md` §3.10: lo zero non e' il fallimento).
    negativo 2  `Ctrl+W` in finestra ⇒ DEVE risultare **non consegnata**, e la
                scheda **deve morire**.  E' il negativo di livello *browser*,
                mentre `Super` e' quello di livello *compositore*.

    ⛔ E ogni riga porta anche `modificatori_visti`: se la pagina ha visto il
       `keydown` di Control ma non quello di W, l'iniezione e' arrivata fin
       dentro la pagina e a fermarsi e' stata la COMBINAZIONE.  E' il controllo
       positivo per-combinazione, gratis.

⛔ IL PALCO SI SCRIVE IN OGNI RIGA — motore, versione, piattaforma delle
   finestre, stato dello schermo intero (nessuno / API / F11), forma della lock
   chiesta e se e' stata concessa.  Un numero senza il palco che l'ha prodotto
   non si ricontrolla (`LEZIONI.md`, e il rilievo A30 della fase 1).

L'INIEZIONE non passa da CDP e non passa da `xdotool`: passa da
`org.gnome.Mutter.RemoteDesktop`, cioe' **dalla stessa porta da cui entra una
tastiera vera**.  ⛔ E' la sola scelta difendibile: un tasto iniettato dentro il
processo di rendering salterebbe a pie' pari lo strato che questa sonda deve
misurare — gli acceleratori del browser — e darebbe «consegnata» a tutto.

⚠ PORTE 7681-7685 (le mie).  ⛔ 7448 · 7501 · 7561 · 7571 non si toccano.
"""

import argparse
import http.server
import json
import os
import random
import shutil
import signal
import socketserver
import string
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone

import gi
from gi.repository import Gio, GLib

QUI = os.path.dirname(os.path.abspath(__file__))

# ── i codici evdev, che sono POSIZIONI e non lettere ────────────────────────
# ⚠ Si iniettano posizioni perche' una tastiera vera manda posizioni
#    (`SPECIFICHE.md` §7.3).  Il browser ce li restituisce come `event.code`,
#    che e' la grandezza giusta da confrontare: le scorciatoie sono posizioni.
K = {
    'Escape': 1, 'Digit1': 2, 'Digit2': 3, 'Digit3': 4, 'Digit4': 5, 'Digit5': 6,
    'Digit6': 7, 'Digit7': 8, 'Digit8': 9, 'Digit9': 10, 'Digit0': 11,
    'Minus': 12, 'Equal': 13, 'Backspace': 14, 'Tab': 15,
    'KeyQ': 16, 'KeyW': 17, 'KeyE': 18, 'KeyR': 19, 'KeyT': 20, 'KeyY': 21,
    'KeyU': 22, 'KeyI': 23, 'KeyO': 24, 'KeyP': 25,
    'BracketLeft': 26, 'BracketRight': 27, 'Enter': 28, 'ControlLeft': 29,
    'KeyA': 30, 'KeyS': 31, 'KeyD': 32, 'KeyF': 33, 'KeyG': 34, 'KeyH': 35,
    'KeyJ': 36, 'KeyK': 37, 'KeyL': 38, 'Semicolon': 39, 'Quote': 40,
    'Backquote': 41, 'ShiftLeft': 42, 'Backslash': 43,
    'KeyZ': 44, 'KeyX': 45, 'KeyC': 46, 'KeyV': 47, 'KeyB': 48, 'KeyN': 49,
    'KeyM': 50, 'Comma': 51, 'Period': 52, 'Slash': 53, 'ShiftRight': 54,
    'AltLeft': 56, 'Space': 57, 'CapsLock': 58,
    'F1': 59, 'F2': 60, 'F3': 61, 'F4': 62, 'F5': 63, 'F6': 64, 'F7': 65,
    'F8': 66, 'F9': 67, 'F10': 68, 'F11': 87, 'F12': 88,
    'ControlRight': 97, 'AltRight': 100,
    'Home': 102, 'ArrowUp': 103, 'PageUp': 104, 'ArrowLeft': 105,
    'ArrowRight': 106, 'End': 107, 'ArrowDown': 108, 'PageDown': 109,
    'Insert': 110, 'Delete': 111, 'MetaLeft': 125, 'MetaRight': 126,
}
BTN_SINISTRO = 0x110


# ═══════════════════════════════════════════════════════════════════════════
#  L'INIETTORE — la porta da cui entra una tastiera vera
# ═══════════════════════════════════════════════════════════════════════════
def sveglia_e_trattieni(bus):
    """⛔ IL SALVASCHERMO FERMA IL BANCO, e non con un errore che lo dica.

    `[M]` 14 agosto 2026: dopo dieci minuti di inattivita' GNOME annerisce lo
    schermo, e da quel momento `RemoteDesktop.CreateSession` risponde
    **«Session creation inhibited (0)»**.  ⚠ Il banco muore all'avvio, e il
    messaggio non nomina ne' il salvaschermo ne' l'inattivita': chi lo legge
    cerca il difetto nei permessi.

    ⇒ Si sveglia lo schermo e si TRATTIENE l'inattivita' per la durata della
      campagna.  ⛔ Con un inibitore, **non** riscrivendo `idle-delay`: una
      preferenza dell'utente riscritta da un banco e' esattamente l'invariante
      I7 al contrario — una configurazione che si puo' perdere.  L'inibitore si
      libera da solo quando il processo se ne va.
    """
    esito = {}
    try:
        ss = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
                                    "org.gnome.ScreenSaver", "/org/gnome/ScreenSaver",
                                    "org.gnome.ScreenSaver", None)
        attivo = ss.call_sync("GetActive", None, 0, -1, None).unpack()[0]
        esito['salvaschermo_era_attivo'] = attivo
        if attivo:
            ss.call_sync("SetActive", GLib.Variant("(b)", (False,)), 0, -1, None)
            time.sleep(1.5)
            esito['risvegliato'] = not ss.call_sync("GetActive", None, 0, -1, None).unpack()[0]
    except Exception as e:
        esito['salvaschermo'] = 'non raggiungibile: %s' % e
    try:
        sm = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
                                    "org.gnome.SessionManager", "/org/gnome/SessionManager",
                                    "org.gnome.SessionManager", None)
        # 8 = inibisci l'inattivita'.  ⚠ Si tiene il numero: senza `Uninhibit`
        #    resta finche' il processo vive, che e' quel che si vuole.
        esito['inibitore'] = sm.call_sync(
            "Inhibit", GLib.Variant("(susu)", ("04-b29", 0, "misura delle scorciatoie", 8)),
            0, -1, None).unpack()[0]
    except Exception as e:
        esito['inibitore'] = 'non ottenuto: %s' % e
    return esito


class Iniettore:
    """Tastiera e puntatore virtuali via `org.gnome.Mutter.RemoteDesktop`.

    ⛔ La sessione VIVE finche' vive questo oggetto: Mutter la distrugge quando
       il proprietario del nome D-Bus se ne va.  Chi la creasse in una funzione
       e uscisse iniettterebbe nel vuoto — ed e' successo, la prima sera.
    """

    def __init__(self):
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        rd = Gio.DBusProxy.new_sync(
            self.bus, Gio.DBusProxyFlags.NONE, None,
            "org.gnome.Mutter.RemoteDesktop", "/org/gnome/Mutter/RemoteDesktop",
            "org.gnome.Mutter.RemoteDesktop", None)
        self.percorso = rd.call_sync("CreateSession", None, 0, -1, None).unpack()[0]
        self.s = Gio.DBusProxy.new_sync(
            self.bus, Gio.DBusProxyFlags.NONE, None,
            "org.gnome.Mutter.RemoteDesktop", self.percorso,
            "org.gnome.Mutter.RemoteDesktop.Session", None)
        self.s.call_sync("Start", None, 0, -1, None)
        self.premuti = set()
        time.sleep(0.3)

    def tasto(self, codice, giu):
        self.s.call_sync("NotifyKeyboardKeycode",
                         GLib.Variant("(ub)", (codice, giu)), 0, -1, None)
        if giu:
            self.premuti.add(codice)
        else:
            self.premuti.discard(codice)

    def combinazione(self, tasti, pausa=0.04):
        """Preme in ordine, rilascia in ordine inverso — come una mano vera."""
        for t in tasti:
            self.tasto(K[t], True)
            time.sleep(pausa)
        time.sleep(pausa)
        for t in reversed(tasti):
            self.tasto(K[t], False)
            time.sleep(pausa)

    def rilascia_tutto(self):
        """⛔ La cura del modificatore rimasto giu' (`STUDI.md` §web §5.4 punto 1).
        Qui non e' un vezzo: un Ctrl rimasto premuto fra due prove trasforma
        ogni misura successiva in una misura di un'altra combinazione."""
        for c in list(self.premuti):
            try:
                self.tasto(c, False)
            except Exception:
                pass
        self.premuti.clear()

    def punta_e_clicca(self, x, y, schermo=(1920, 1080)):
        """Porta il puntatore a (x, y) e clicca.

        ⚠ Si usa il moto RELATIVO, non l'assoluto: l'assoluto pretende un flusso
          ScreenCast, che monterebbe un indicatore di condivisione sullo schermo
          dell'utente per niente.  Si va prima a sbattere nell'angolo — Mutter
          tronca ai bordi — e poi si conta da li'.

        ⛔⛔ E L'ANGOLO E' QUELLO IN BASSO A DESTRA, NON IN ALTO A SINISTRA.
            In alto a sinistra GNOME ha l'**angolo caldo**: il puntatore che ci
            arriva apre la panoramica delle Attivita', che si prende il fuoco —
            e la prova successiva risultava «non misurata, senza fuoco».  ⚠ Il
            banco se l'e' fatto da solo, e per un palco intero: e' la trappola
            n. 1 di `LEZIONI.md` §1.1 — la scena non era dove si guardava."""
        self.s.call_sync("NotifyPointerMotionRelative",
                         GLib.Variant("(dd)", (float(schermo[0] * 2), float(schermo[1] * 2))),
                         0, -1, None)
        time.sleep(0.05)
        self.s.call_sync("NotifyPointerMotionRelative",
                         GLib.Variant("(dd)", (float(x - schermo[0]), float(y - schermo[1]))),
                         0, -1, None)
        time.sleep(0.1)
        self.s.call_sync("NotifyPointerButton",
                         GLib.Variant("(ib)", (BTN_SINISTRO, True)), 0, -1, None)
        time.sleep(0.06)
        self.s.call_sync("NotifyPointerButton",
                         GLib.Variant("(ib)", (BTN_SINISTRO, False)), 0, -1, None)
        time.sleep(0.15)

    def chiudi(self):
        try:
            self.rilascia_tutto()
            self.s.call_sync("Stop", None, 0, -1, None)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  IL SERVITORE — serve la pagina, raccoglie gli eventi, detta gli ordini
# ═══════════════════════════════════════════════════════════════════════════
class Stato:
    def __init__(self):
        self.lock = threading.Lock()
        self.eventi = []
        self.ordine = {'seq': 0, 'azione': 'nulla'}
        self.richieste = 0


STATO = Stato()


class Manico(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _corpo(self, dati, tipo='application/json'):
        self.send_response(200)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(dati)))
        self.send_header('Cache-Control', 'no-store')
        # ⚠ L'isolamento fra origini di `SPECIFICHE.md` §11.5: qui non serve ai
        #   cronometri, ma il palco si tiene uguale a quello del prodotto.
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.end_headers()
        self.wfile.write(dati)

    def do_GET(self):
        if self.path.startswith('/ordine'):
            with STATO.lock:
                o = dict(STATO.ordine)
                STATO.richieste += 1
            self._corpo(json.dumps(o).encode())
        elif self.path in ('/', '/index.html', '/pagina.html'):
            with open(os.path.join(QUI, '04-b29-pagina.html'), 'rb') as f:
                self._corpo(f.read(), 'text/html; charset=utf-8')
        else:
            self.send_response(404)
            self.send_header('Content-Length', '0')
            self.end_headers()

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        grezzo = self.rfile.read(n) if n else b'{}'
        try:
            ev = json.loads(grezzo.decode('utf-8', 'replace'))
        except Exception:
            ev = {'t': 'illeggibile', 'grezzo': grezzo[:200].decode('utf-8', 'replace')}
        ev['_ricevuto'] = time.time()
        with STATO.lock:
            STATO.eventi.append(ev)
        self.send_response(204)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def log_message(self, *a):
        pass


class Servitore(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


# ═══════════════════════════════════════════════════════════════════════════
#  I MOTORI
# ═══════════════════════════════════════════════════════════════════════════
class Motore:
    def __init__(self, nome, porta_pagina, porta_debug, base):
        self.nome = nome
        self.porta_pagina = porta_pagina
        self.porta_debug = porta_debug
        self.base = base
        self.proc = None
        self.versione = self._versione()

    def _versione(self):
        exe = {'chrome': 'google-chrome', 'chrome-app': 'google-chrome',
               'firefox': 'firefox'}[self.nome]
        try:
            return subprocess.run([exe, '--version'], capture_output=True, text=True,
                                  timeout=20).stdout.strip()
        except Exception as e:
            return 'ignota: %s' % e

    def profilo(self):
        return os.path.join(self.base, 'profilo-' + self.nome)

    def avvia(self, pulisci=False):
        url = 'http://127.0.0.1:%d/' % self.porta_pagina
        prof = self.profilo()
        # ⛔ SI AMMAZZANO PRIMA I RESTI DEL GIRO PRECEDENTE, e non e' igiene:
        #    un banco interrotto (`timeout`, Ctrl-C) lascia in piedi una
        #    finestra **a schermo intero e in cima a tutto**.  Il giro dopo apre
        #    la sua dietro quella, il clic di messa a fuoco finisce nella
        #    finestra vecchia, e il banco dichiara «il browser non prende il
        #    fuoco» su un browser sanissimo.  ⚠ Si ammazza per PROFILO, che e'
        #    solo nostro: `pkill chrome` spegnerebbe quello dell'utente.
        subprocess.run(['pkill', '-f', 'user-data-dir=' + prof],
                       capture_output=True)
        subprocess.run(['pkill', '-f', '-profile ' + prof], capture_output=True)
        subprocess.run(['pkill', '-f', prof], capture_output=True)
        time.sleep(1.0)
        if pulisci and os.path.isdir(prof):
            shutil.rmtree(prof, ignore_errors=True)
        os.makedirs(prof, exist_ok=True)
        reg = open(os.path.join(self.base, 'registro-%s.log' % self.nome), 'ab')
        if self.nome in ('chrome', 'chrome-app'):
            cmd = ['google-chrome',
                   '--user-data-dir=' + prof,
                   '--no-first-run', '--no-default-browser-check',
                   '--disable-features=Translate,MediaRouter',
                   '--remote-debugging-port=%d' % self.porta_debug,
                   '--remote-allow-origins=*',
                   '--start-maximized']
            if self.nome == 'chrome-app':
                # ⭐ LA MISURA CHE PORTA UNA `[R]` A `[M]` SENZA UN TELEFONO.
                #    `STUDI.md` §web §5.1 legge nel codice di Chromium
                #    «// In Apps mode, no keys are reserved» e ne ricava che in
                #    una **PWA installata** la lista riservata e' VUOTA.  ⛔ Quel
                #    ramo del codice non e' di Android: e' della **finestra
                #    d'applicazione**, e `--app=` la apre su desktop.  ⇒ La tesi
                #    si prova qui, oggi, su questo ferro.
                #    ⚠ E resta `[?]` la META' che riguarda Android: una finestra
                #      d'applicazione su Linux non e' una PWA su Chrome per
                #      Android, e non si deduce.
                cmd.append('--app=' + url)
            else:
                cmd += ['--new-window', url]
        else:
            # ⚠ `--remote-debugging-port` su Firefox 140 apre l'agente remoto:
            #    si prova a leggerlo, e se non risponde si DICHIARA che il
            #    secondo strumento su questo motore non c'e'.
            cmd = ['firefox', '--profile', prof, '--no-remote',
                   '--remote-debugging-port', str(self.porta_debug),
                   '--new-window', url]
        self.proc = subprocess.Popen(cmd, stdout=reg, stderr=reg,
                                     start_new_session=True)
        return self.proc

    def ferma(self):
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
            except Exception:
                self.proc.terminate()
            for _ in range(50):
                if self.proc.poll() is not None:
                    break
                time.sleep(0.1)
            if self.proc.poll() is None:
                try:
                    os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
                except Exception:
                    self.proc.kill()
        self.proc = None

    # ── il SECONDO strumento: il protocollo di debug ───────────────────────
    def bersagli(self):
        """Ritorna la lista dei bersagli, o None se lo strumento non c'e'.

        ⛔ None e [] non sono la stessa cosa: `LEZIONI.md`/`CODER.md` §3.10.
           None = «non lo so»; [] = «ho guardato e non c'era niente»."""
        try:
            with urllib.request.urlopen(
                    'http://127.0.0.1:%d/json/list' % self.porta_debug, timeout=2) as r:
                return json.loads(r.read().decode())
        except Exception:
            return None

    def ritratto_bersagli(self):
        b = self.bersagli()
        if b is None:
            return None
        pagine = [t for t in b if t.get('type') == 'page'
                  and not t.get('url', '').startswith('chrome-extension')]
        return {
            'n_pagine': len(pagine),
            'url': sorted(t.get('url', '')[:90] for t in pagine),
            'devtools': sum(1 for t in b if 'devtools://' in t.get('url', '')),
        }


# ═══════════════════════════════════════════════════════════════════════════
#  IL PILOTA
# ═══════════════════════════════════════════════════════════════════════════
def adesso():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


class Pilota:
    previeni = False   # il secondo giro: la pagina chiama `preventDefault()`

    def __init__(self, motore, iniettore, esiti, schermo, giro_id):
        self.m = motore
        self.i = iniettore
        self.esiti = esiti
        self.schermo = schermo
        self.giro = giro_id
        self.seq = 0
        self.palco = {}

    # ── il filo con la pagina ──────────────────────────────────────────────
    def ordina(self, azione, **kw):
        self.seq += 1
        o = {'seq': self.seq, 'azione': azione}
        o.update(kw)
        with STATO.lock:
            STATO.ordine = o
        return self.seq

    def dal(self, t0, tipi=None, prova=None):
        with STATO.lock:
            ev = list(STATO.eventi)
        fuori = []
        for e in ev:
            if e.get('_ricevuto', 0) < t0:
                continue
            if tipi and e.get('t') not in tipi:
                continue
            if prova is not None and e.get('prova') != prova:
                continue
            fuori.append(e)
        return fuori

    def aspetta(self, condizione, secondi=8.0, passo=0.1):
        fine = time.time() + secondi
        while time.time() < fine:
            r = condizione()
            if r:
                return r
            time.sleep(passo)
        return None

    def battito(self, entro=1.6):
        """L'ultimo battito della pagina, o None se la pagina tace."""
        t0 = time.time() - entro
        b = self.dal(t0, tipi=('battito',))
        return b[-1] if b else None

    def viva(self):
        return self.battito() is not None

    def carico(self):
        b = self.battito()
        return b.get('carico') if b else None

    # ── il palco ───────────────────────────────────────────────────────────
    def apri_browser(self, pulisci=False):
        self.m.ferma()
        time.sleep(0.5)
        self.m.avvia(pulisci=pulisci)
        ok = self.aspetta(lambda: self.viva(), secondi=45)
        if not ok:
            return False
        # ⛔ Il `preventDefault` si rimette a OGNI apertura: il browser che si
        #    riavvia dopo una combinazione distruttiva ricomincia da una pagina
        #    nuova, che non sa niente del giro in corso.  Chi lo desse per
        #    scontato pubblicherebbe meta' giro con la cura e meta' senza, sotto
        #    la stessa etichetta.
        if self.previeni:
            t0 = time.time()
            self.ordina('previeni', valore=True)
            self.aspetta(lambda: self.dal(t0, tipi=('previeni',)), 6)
        return self.prendi_fuoco()

    def prendi_fuoco(self, tentativi=4):
        """⛔ SENZA QUESTO LA SONDA E' UN GENERATORE DI ZERI.

        La prima sera questa sonda ha dato «non consegnata» a **tutto**, e il
        motivo non era il browser: la finestra non aveva il fuoco della
        tastiera.  Un banco che non verifica il fuoco prima di ogni battuta
        misura la scrivania, non il motore (`LEZIONI.md` §1.1: la scena non era
        dove si guardava)."""
        for n in range(tentativi):
            b = self.battito()
            if b and b.get('fuoco'):
                return True
            self.i.rilascia_tutto()
            if n:
                # ⚠ Al secondo tentativo si chiude prima quel che si e' aperto —
                #   la panoramica di GNOME, un menu, una finestrella — perche'
                #   un clic sopra a quello finirebbe li' dentro.
                self.i.combinazione(['Escape'])
                time.sleep(0.4)
            self.i.punta_e_clicca(self.schermo[0] // 2, int(self.schermo[1] * 0.62),
                                  self.schermo)
            time.sleep(0.6)
        b = self.battito()
        return bool(b and b.get('fuoco'))

    def verifica_tastiera(self, tentativi=3):
        """⛔⛔ IL CANCELLO VERO, e il primo non bastava.

        `document.hasFocus()` **non e' un testimone attendibile**: `[M]` 14
        agosto 2026, su **Firefox 140 ESR / Wayland** la pagina ha continuato a
        dichiarare `fuoco: true` mentre la panoramica di GNOME si era presa la
        tastiera.  ⇒ Un giro intero di Firefox e' uscito «non consegnata» su
        **tutto**, compreso `Ctrl+C`: numeri perfettamente verosimili e
        interamente falsi.

        ⭐ Il banco se n'e' accorto da solo, e vale la pena scrivere COME: ogni
        riga porta `modificatori_visti`, e li' c'era scritto **«nemmeno i
        modificatori sono arrivati»** — che e' la firma dell'iniezione che non
        entra, non della scorciatoia riservata.  Senza quel campo, quel giro
        sarebbe stato pubblicato.

        ⇒ Da qui in poi non si chiede alla pagina se **crede** di avere il
          fuoco: le si chiede di **dimostrare che riceve i tasti**, adesso, con
          un tasto innocuo.  Un cancello che si prova invece di fidarsi."""
        for n in range(tentativi):
            t0 = time.time()
            self.i.rilascia_tutto()
            self.i.combinazione(['F9'])
            visto = self.aspetta(
                lambda: [e for e in self.dal(t0, tipi=('keydown',))
                         if e.get('code') == 'F9'], 1.5)
            if visto:
                return True
            # ⚠ Il recupero: si chiude quel che si e' aperto e si riclicca.
            #   ⛔ E l'`Escape` puo' far cadere lo schermo intero da API: e' un
            #   prezzo, e si paga solo quando il cancello e' gia' chiuso.
            self.i.combinazione(['Escape'])
            time.sleep(0.4)
            self.prendi_fuoco(tentativi=2)
        return False

    def chiedi_capacita(self):
        t0 = time.time()
        self.ordina('capacita')
        c = self.aspetta(lambda: (self.dal(t0, tipi=('capacita',)) or [None])[-1], 6)
        return c or {}

    def gesto(self, azione, **kw):
        """Un'azione che pretende un gesto dell'utente: si arma la pagina e si
        manda un tasto innocuo (F9) che faccia da gesto.

        ⚠ F9 e' innocuo su Chrome e su Firefox in Linux; se un giorno non lo
          fosse, il registro lo direbbe (la riga `gesto` porta il ritratto)."""
        # ⛔ Il gesto si manda solo se la tastiera arriva davvero: un `F9` che
        #    non entra lascia il palco non montato, e il pilota lo scriverebbe
        #    come «il motore non sa andare a schermo intero» — che e' un'accusa
        #    al motore per un difetto del banco.
        tastiera = self.verifica_tastiera()
        t0 = time.time()
        self.ordina('gesto', chiede=azione, **kw)
        armato = self.aspetta(lambda: self.dal(t0, tipi=('gesto_armato',)), 5)
        # ⛔ Il gesto si manda PIU' DI UNA VOLTA se serve: un solo `F9` che si
        #    perde lascia il palco non montato, e il pilota lo scriverebbe come
        #    un difetto del motore.  ⚠ E ogni tentativo si conta, perche' «al
        #    primo colpo» e «al terzo» non sono la stessa misura.
        g, colpi = None, 0
        for _ in range(3):
            colpi += 1
            self.i.combinazione(['F9'])
            g = self.aspetta(lambda: (self.dal(t0, tipi=('gesto',)) or [None])[-1], 4)
            if g:
                break
            self.prendi_fuoco(tentativi=2)
        if not g:
            print('     ⚠ il gesto «%s» NON e stato eseguito dalla pagina '
                  '(tastiera=%s, armato=%s, %d colpi): il palco NON si monta, '
                  'e lo scrivo invece di dedurlo' % (azione, tastiera, bool(armato), colpi))
        time.sleep(0.6)
        d = dict(g or {})
        d['_colpi'] = colpi
        d['_tastiera_provata'] = tastiera
        d['_armato'] = bool(armato)
        return d

    def monta_palco(self, palco):
        """Mette la pagina nel palco chiesto e RIFERISCE quel che ha ottenuto —
        che non e' sempre quel che ha chiesto (`CODER.md` §3.9)."""
        # si riparte sempre da terra
        self.gesto('sblocca')
        time.sleep(0.4)
        self.prendi_fuoco()
        # ⛔ E lo schermo intero entrato con F11 NON si chiude con
        #    `exitFullscreen()`: non e' schermo intero dell'API, e l'API non lo
        #    vede.  Si riconosce dalla geometria — piena — con
        #    `fullscreenElement` a null, ed e' la stessa firma della trappola
        #    O10.  Chi non lo togliesse si porterebbe il palco vecchio dentro
        #    quello nuovo.
        b = self.battito() or {}
        if b.get('ff_geom') and not b.get('schermo_intero'):
            self.i.combinazione(['F11'])
            time.sleep(1.2)
            self.prendi_fuoco()
        d = {'palco': palco, 'chiesto': palco}
        if palco == 'finestra':
            d['lock_chiesta'] = False
        elif palco == 'schermo-intero-api':
            g = self.gesto('schermo_intero')
            d.update({'lock_chiesta': False, 'gesto': g})
        elif palco == 'schermo-intero-api+lock-vecchia':
            g = self.gesto('schermo_intero', lock='vecchia')
            d.update({'lock_chiesta': True, 'forma_lock': 'navigator.keyboard.lock()',
                      'lock_concessa': bool(g.get('lock_chiesta')),
                      'lock_motivo': g.get('lock_motivo'), 'gesto': g})
        elif palco == 'schermo-intero-api+lock-nuova':
            g = self.gesto('schermo_intero', lock='nuova')
            d.update({'lock_chiesta': True,
                      'forma_lock': "requestFullscreen({keyboardLock:'browser'})",
                      'opzione_letta': g.get('opzione_letta'),
                      # ⛔ «concessa» vuol dire che il motore ha LETTO l'opzione,
                      #    non che lo schermo intero e' riuscito: un motore che
                      #    non la conosce riesce lo stesso, e senza la lock.
                      'lock_concessa': bool(g.get('riuscita')) and bool(g.get('opzione_letta')),
                      'lock_errore': g.get('errore'), 'gesto': g})
        elif palco == 'schermo-intero-F11+lock':
            # ⛔ LA TRAPPOLA O10.1: la lock **non esiste** se lo schermo intero e'
            #    stato aperto con F11 — e non lo dice.  Qui si entra con F11 e
            #    POI si chiede la lock, che e' esattamente il caso che morde.
            self.i.combinazione(['F11'])
            time.sleep(1.2)
            g = self.gesto('solo_lock')
            d.update({'lock_chiesta': True, 'forma_lock': 'navigator.keyboard.lock() dopo F11',
                      'lock_concessa': bool(g.get('lock_chiesta')),
                      'lock_errore': g.get('errore'), 'gesto': g})
        else:
            raise ValueError(palco)
        time.sleep(0.5)
        self.prendi_fuoco()
        b = self.battito() or {}
        d['ottenuto_fullscreenElement'] = b.get('schermo_intero')
        d['ottenuto_geometria_piena'] = b.get('ff_geom')
        d['ih'] = b.get('ih')
        d['ow'] = b.get('ow')
        d['oh'] = b.get('oh')
        d['fuoco'] = b.get('fuoco')
        self.palco = d
        return d

    def palco_intatto(self):
        b = self.battito()
        if not b or not b.get('fuoco'):
            return False
        if self.palco.get('palco') == 'finestra':
            return not b.get('ff_geom')
        return bool(b.get('schermo_intero') or b.get('ff_geom'))

    # ── LA MISURA ──────────────────────────────────────────────────────────
    def prova(self, nome, tasti, attesa=1.6, note=''):
        """Una combinazione, e le DUE domande."""
        self.i.rilascia_tutto()
        # ⛔⛔ IL CANCELLO DEL FUOCO, e non e' prudenza: e' la condizione della
        #     misura.  Senza fuoco ogni combinazione risulterebbe «non
        #     consegnata» — cioe' la sonda stamperebbe una tavola intera di
        #     numeri falsi e verosimili.  E c'e' la seconda meta', che e'
        #     peggio: la battuta finirebbe **nella finestra di qualcun altro**,
        #     e `Ctrl+W` chiuderebbe una scheda dell'utente.
        #     ⇒ Se il fuoco non c'e', non si inietta e si SCRIVE il rifiuto.
        if not (self.prendi_fuoco(tentativi=3) and self.verifica_tastiera()):
            riga = {
                'giro': self.giro, 'ora': adesso(), 'banco': '04-b29',
                'combinazione': nome, 'codici': tasti,
                'motore': self.m.nome, 'versione': self.m.versione,
                'palco': self.palco.get('palco'),
                'schermo_intero_API': self.palco.get('ottenuto_fullscreenElement'),
                'schermo_intero_geometria': self.palco.get('ottenuto_geometria_piena'),
                'lock_chiesta': self.palco.get('lock_chiesta'),
                'lock_concessa': self.palco.get('lock_concessa'),
                'fuoco_prima': False, 'fuoco_dopo': False,
                'consegnata_alla_pagina': None, 'browser_ha_agito': None,
                'stato': 'NON-MISURATA',
                'dubbio': '⛔ la pagina non riceveva i tasti (cancello F9 chiuso): '
                          'non ho iniettato niente.  Non e un esito, e un '
                          'rifiuto di misurare.',
                'note': note,
            }
            self.esiti.write(json.dumps(riga, ensure_ascii=False) + '\n')
            self.esiti.flush()
            print('   %-22s  \033[35mNON MISURATA\033[0m — senza fuoco, non inietto' % nome)
            return riga
        ricompra = self.ricompra_lock()
        # ⚠ E SI ASPETTA UN BATTITO **NUOVO**: il battito arriva ogni 500 ms, e
        #   quello gia' in mano puo' essere stato scritto PRIMA della ricompra —
        #   nel qual caso `lock_viva_alla_battuta` direbbe «no» su una lock viva.
        #   ⛔ Non e' un dettaglio di comodo: e' un campo del registro che
        #   mentirebbe, e mentirebbe **verso il pessimismo**, che e' il verso in
        #   cui gli errori non si notano.
        if ricompra:
            t_fresco = time.time()
            self.aspetta(lambda: [b for b in self.dal(t_fresco, tipi=('battito',))], 2.0)
        carico_prima = self.carico()
        b_prima = self.battito() or {}
        bers_prima = self.m.ritratto_bersagli()
        pid = '%s-%s-%d' % (self.giro, nome.replace('+', '_'), int(time.time() * 1000) % 100000)
        t0 = time.time()
        self.ordina('arma', prova=pid, combinazione=nome)
        armata = self.aspetta(lambda: (self.dal(t0, tipi=('armata',)) or [None])[-1], 4)
        t_arm = time.time()
        principale = tasti[-1]
        modificatori = tasti[:-1]

        self.i.combinazione(tasti)
        time.sleep(attesa)

        ev = self.dal(t_arm)
        bers_dopo = self.m.ritratto_bersagli()
        carico_dopo = self.carico()

        # ── domanda 1: e' arrivata ALLA PAGINA? ────────────────────────────
        vuole_ctrl = any(m.startswith('Control') for m in modificatori)
        vuole_alt = any(m.startswith('Alt') for m in modificatori)
        vuole_shift = any(m.startswith('Shift') for m in modificatori)
        vuole_meta = any(m.startswith('Meta') for m in modificatori)
        consegnata = False
        keydown_visti = []
        for e in ev:
            if e.get('t') != 'keydown':
                continue
            keydown_visti.append(e.get('code'))
            if (e.get('code') == principale and bool(e.get('ctrl')) == vuole_ctrl
                    and bool(e.get('alt')) == vuole_alt
                    and bool(e.get('shift')) == vuole_shift
                    and bool(e.get('meta')) == vuole_meta):
                consegnata = True
        modificatori_visti = [c for c in keydown_visti if c in modificatori]

        # ── domanda 2: il BROWSER ha fatto anche il suo? ───────────────────
        segnali = {}
        segnali['morta'] = any(e.get('t') == 'muoio' for e in ev)
        segnali['rinata'] = bool(carico_dopo and carico_prima and carico_dopo != carico_prima)
        segnali['tace'] = carico_dopo is None
        segnali['fuoco_perso'] = any(e.get('t') == 'blur' for e in ev)
        segnali['nascosta'] = any(e.get('t') == 'visibilita' and e.get('visibile') == 'hidden'
                                  for e in ev)
        segnali['schermo_intero_cambiato'] = any(e.get('t') == 'schermo_intero' for e in ev)
        segnali['stampa'] = any(e.get('t') == 'stampa' for e in ev)
        segnali['menu_contesto'] = any(e.get('t') == 'menu_contesto' for e in ev)
        ih_prima, ih_dopo = b_prima.get('ih'), (self.battito() or {}).get('ih')
        segnali['geometria_cambiata'] = bool(
            ih_prima and ih_dopo and abs(ih_prima - ih_dopo) > 20)
        segnali['ih_prima'] = ih_prima
        segnali['ih_dopo'] = ih_dopo
        if bers_prima is not None and bers_dopo is not None:
            segnali['bersagli_prima'] = bers_prima
            segnali['bersagli_dopo'] = bers_dopo
            segnali['schede_cambiate'] = bers_prima['n_pagine'] != bers_dopo['n_pagine']
            segnali['devtools_cambiati'] = bers_prima['devtools'] != bers_dopo['devtools']
        else:
            segnali['bersagli'] = None  # ⛔ non lo so, non «non e' successo»

        agito = any(bool(segnali.get(k)) for k in (
            'morta', 'rinata', 'tace', 'fuoco_perso', 'nascosta',
            'schermo_intero_cambiato', 'stampa', 'geometria_cambiata',
            'schede_cambiate', 'devtools_cambiati'))

        # ── i TRE stati ────────────────────────────────────────────────────
        if consegnata and agito:
            stato = 'consegnata-E-RISERVATA'
        elif consegnata:
            stato = 'consegnata'
        elif agito:
            stato = 'non-consegnata'
        else:
            stato = 'non-consegnata'
        # ⚠ E la quarta casella, che non e' uno stato ma un DUBBIO: niente e'
        #   arrivato alla pagina e niente si e' mosso.  Puo' voler dire «il
        #   browser se l'e' tenuta e non fa niente di visibile», oppure «la mia
        #   iniezione non e' partita».  I `modificatori_visti` separano i due
        #   casi, e se non separano si scrive il dubbio invece di sceglierlo.
        dubbio = None
        if not consegnata and not agito:
            if modificatori_visti:
                dubbio = ('nulla-di-visibile: i modificatori sono arrivati alla pagina, '
                          'la combinazione no ⇒ la tiene il browser, senza effetto visibile')
            elif modificatori:
                dubbio = ('⛔ NEMMENO i modificatori sono arrivati: non si distingue '
                          '«se la tiene il compositore» da «l iniezione non e partita»')
            else:
                dubbio = ('⛔ tasto singolo non arrivato e nessun effetto: non si distingue '
                          '«riservato in silenzio» da «iniezione non partita»')

        b_dopo = self.battito() or {}
        riga = {
            'giro': self.giro,
            'ora': adesso(),
            'banco': '04-b29',
            # ⭐ IL SECONDO GIRO, e la differenza fra i due e' la risposta che
            #    serve al prodotto: quali «consegnata E RISERVATA» si curano
            #    chiamando `preventDefault()` nella pagina, e quali no.
            'preventDefault': bool(b_prima.get('previeni')),
            'combinazione': nome,
            'tasti_evdev': [K[t] for t in tasti],
            'codici': tasti,
            # ── il palco, in OGNI riga ─────────────────────────────────────
            'motore': self.m.nome,
            'versione': self.m.versione,
            'piattaforma_finestre': self.palco.get('piattaforma_finestre'),
            'palco': self.palco.get('palco'),
            # ⛔ LO SCHERMO INTERO SI LEGGE **ALLA BATTUTA**, non da come il
            #    palco era stato montato: fra il montaggio e questa riga puo'
            #    esserci passata una combinazione che l'ha fatto cadere, e una
            #    riga che dichiarasse il palco montato invece di quello vero
            #    sarebbe un numero con il palco sbagliato accanto — cioe' un
            #    numero che non si ricontrolla.
            'schermo_intero_API': b_prima.get('schermo_intero'),
            'schermo_intero_geometria': b_prima.get('ff_geom'),
            'schermo_intero_montato': self.palco.get('ottenuto_fullscreenElement'),
            'palco_scaduto': (self.palco.get('palco') != 'finestra'
                              and not (b_prima.get('schermo_intero')
                                       or b_prima.get('ff_geom'))),
            'lock_chiesta': self.palco.get('lock_chiesta'),
            'forma_lock': self.palco.get('forma_lock'),
            'lock_concessa': self.palco.get('lock_concessa'),
            # ⛔ e la lock era VIVA nell'istante dell'iniezione?  E' una
            #    grandezza per riga, non per palco: si spegne al primo blur.
            'lock_viva_alla_battuta': b_prima.get('lock_concessa'),
            'lock_ricomprata': ricompra,
            'lock_perse_dal_fuoco': b_prima.get('lock_persa_dal_fuoco'),
            'compositore': self.palco.get('compositore'),
            'schermo': list(self.schermo),
            # ── le DUE colonne ─────────────────────────────────────────────
            'consegnata_alla_pagina': consegnata,
            'browser_ha_agito': agito,
            'stato': stato,
            'dubbio': dubbio,
            # ── le prove ───────────────────────────────────────────────────
            'keydown_visti': keydown_visti,
            'modificatori_visti': modificatori_visti,
            'segnali': segnali,
            'fuoco_prima': b_prima.get('fuoco'),
            'fuoco_dopo': b_dopo.get('fuoco'),
            'armata': bool(armata),
            'note': note,
        }
        self.esiti.write(json.dumps(riga, ensure_ascii=False) + '\n')
        self.esiti.flush()
        stampa_riga(riga)
        return riga

    # ── il recupero fra una prova e l'altra ────────────────────────────────
    def rimetti_a_posto(self, palco):
        """⛔ Deterministico e stupido: si prova a riprendere il fuoco; se il
        palco non e' quello che deve essere, si ributta giu' tutto e si
        ricomincia.  Un recupero furbo lascerebbe stati misti fra due prove, e
        due misure diverse sotto la stessa etichetta (`CODER.md` §3.9)."""
        self.i.rilascia_tutto()
        # ⛔ L'`Escape` NON si manda a occhi chiusi: a schermo intero da API
        #    `Escape` **esce dallo schermo intero**, cioe' il ripristino
        #    distruggerebbe il palco che deve ripristinare — e ogni prova
        #    successiva misurerebbe un palco diverso da quello dichiarato in
        #    riga.  ⇒ Prima si guarda; si tocca solo se e' rotto.
        if self.viva() and self.palco_intatto():
            return True
        self.prendi_fuoco(tentativi=2)
        if self.viva() and self.palco_intatto():
            return True
        self.i.combinazione(['Escape'])
        time.sleep(0.4)
        self.prendi_fuoco(tentativi=2)
        if self.viva() and self.palco_intatto():
            return True
        if not self.apri_browser():
            return False
        self.monta_palco(palco)
        return self.palco_intatto()

    def ricompra_lock(self):
        """⛔ La lock e' MORTA appena la pagina ha perso il fuoco (O10), e la
        pagina perde il fuoco a ogni combinazione che apre qualcosa.  ⇒ In un
        palco «con lock» si ricompra PRIMA di ogni prova, e si SCRIVE se ci si
        e' riusciti: altrimenti meta' delle righe direbbero «con lock» avendo
        misurato senza."""
        if not self.palco.get('lock_chiesta'):
            return None
        if self.palco.get('forma_lock', '').startswith('requestFullscreen'):
            # non si ricompra senza uscire e rientrare: si dichiara e basta
            b = self.battito() or {}
            return {'ok': bool(b.get('lock_concessa')), 'forma': 'nuova',
                    'nota': 'la forma nuova non si ricompra senza uscire e rientrare'}
        t0 = time.time()
        self.ordina('rilock')
        r = self.aspetta(lambda: (self.dal(t0, tipi=('rilock',)) or [None])[-1], 5)
        return {'ok': bool(r and r.get('ok')), 'forma': 'vecchia',
                'errore': (r or {}).get('errore')}


def stampa_riga(r):
    simbolo = {'consegnata': '\033[32mconsegnata\033[0m',
               'consegnata-E-RISERVATA': '\033[31mconsegnata E RISERVATA\033[0m',
               'non-consegnata': '\033[33mnon consegnata\033[0m'}[r['stato']]
    print('   %-22s  %-24s  pagina=%-5s browser=%-5s  %s'
          % (r['combinazione'], simbolo, r['consegnata_alla_pagina'],
             r['browser_ha_agito'], (r['dubbio'] or '')[:60]))


# ═══════════════════════════════════════════════════════════════════════════
#  LE COMBINAZIONI
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ `Ctrl+Alt+Canc` NON si inietta, e non e' pigrizia: su GNOME e' legato alla
#    finestra di disconnessione, che dopo 60 s **disconnette la sessione
#    dell'utente**.  Un banco non spegne la macchina su cui gira.  ⇒ Resta
#    dichiarato, e la sua sorte si legge dal caso `Super`: quel che il
#    compositore prende, il browser non lo vede mai.  E' proprio la ragione per
#    cui O7 chiede un **bottone a schermo** invece di una scorciatoia.
COMBINAZIONI = [
    # (nome, tasti, gruppo, nota)
    ('CONTROLLO+ Ctrl+Alt+G', ['ControlLeft', 'AltLeft', 'KeyG'], 'controllo',
     'positivo: deve arrivare e non fare niente'),
    ('CONTROLLO- Super',      ['MetaLeft'], 'controllo',
     'negativo di compositore: GNOME se lo tiene, e si VEDE'),

    ('Ctrl+T',        ['ControlLeft', 'KeyT'], 'schede', 'nuova scheda'),
    ('Ctrl+Tab',      ['ControlLeft', 'Tab'], 'schede', 'O8: il caso di Firefox'),
    ('Ctrl+Shift+Tab', ['ControlLeft', 'ShiftLeft', 'Tab'], 'schede', ''),
    ('Ctrl+PageDown', ['ControlLeft', 'PageDown'], 'schede', ''),
    ('Ctrl+PageUp',   ['ControlLeft', 'PageUp'], 'schede', ''),
    ('Ctrl+1',        ['ControlLeft', 'Digit1'], 'schede', ''),
    ('Ctrl+9',        ['ControlLeft', 'Digit9'], 'schede', ''),

    ('Ctrl+L',        ['ControlLeft', 'KeyL'], 'barra', 'barra degli indirizzi'),
    ('Alt+D',         ['AltLeft', 'KeyD'], 'barra', ''),
    ('Ctrl+F',        ['ControlLeft', 'KeyF'], 'barra', 'barra di ricerca'),
    ('Ctrl+E',        ['ControlLeft', 'KeyE'], 'barra', ''),

    ('F5',            ['F5'], 'ricarica', ''),
    ('Ctrl+R',        ['ControlLeft', 'KeyR'], 'ricarica', ''),
    ('Alt+ArrowLeft', ['AltLeft', 'ArrowLeft'], 'storia', 'indietro'),
    ('Alt+ArrowRight', ['AltLeft', 'ArrowRight'], 'storia', 'avanti'),
    ('Alt+Home',      ['AltLeft', 'Home'], 'storia', ''),

    ('F12',           ['F12'], 'strumenti', 'DevTools'),
    ('Ctrl+Shift+I',  ['ControlLeft', 'ShiftLeft', 'KeyI'], 'strumenti', 'DevTools'),
    ('Ctrl+Shift+J',  ['ControlLeft', 'ShiftLeft', 'KeyJ'], 'strumenti', ''),
    ('Ctrl+U',        ['ControlLeft', 'KeyU'], 'strumenti', 'sorgente'),

    ('Ctrl+P',        ['ControlLeft', 'KeyP'], 'finestrelle', 'stampa'),
    ('Ctrl+S',        ['ControlLeft', 'KeyS'], 'finestrelle', 'salva'),
    ('Ctrl+O',        ['ControlLeft', 'KeyO'], 'finestrelle', 'apri'),
    ('Ctrl+H',        ['ControlLeft', 'KeyH'], 'finestrelle', 'cronologia'),
    ('Ctrl+D',        ['ControlLeft', 'KeyD'], 'finestrelle', 'segnalibro'),
    ('Ctrl+J',        ['ControlLeft', 'KeyJ'], 'finestrelle', 'scaricati'),

    ('F11',           ['F11'], 'schermo', "l'unica via di fuga dell'utente"),
    ('Escape',        ['Escape'], 'schermo', ''),

    ('Ctrl+C',        ['ControlLeft', 'KeyC'], 'appunti', 'deve arrivare: e un comando del desktop remoto'),
    ('Ctrl+V',        ['ControlLeft', 'KeyV'], 'appunti', ''),
    ('Ctrl+A',        ['ControlLeft', 'KeyA'], 'appunti', ''),
    ('Ctrl+Z',        ['ControlLeft', 'KeyZ'], 'appunti', ''),

    ('Super+KeyD',    ['MetaLeft', 'KeyD'], 'compositore', 'GNOME'),
    ('Alt+Tab',       ['AltLeft', 'Tab'], 'compositore', 'GNOME cambia finestra'),
    ('Alt+F2',        ['AltLeft', 'F2'], 'compositore', ''),

    # ⛔ le distruttive vanno IN FONDO: chiudono la scheda o la finestra, e ogni
    #    prova che segue pagherebbe un riavvio.
    ('Ctrl+W',        ['ControlLeft', 'KeyW'], 'distruttive', 'chiude la scheda'),
    ('Ctrl+N',        ['ControlLeft', 'KeyN'], 'distruttive', 'nuova finestra'),
    ('Ctrl+Shift+N',  ['ControlLeft', 'ShiftLeft', 'KeyN'], 'distruttive', ''),
    ('Ctrl+Q',        ['ControlLeft', 'KeyQ'], 'distruttive', 'chiude il browser'),
    ('Alt+F4',        ['AltLeft', 'F4'], 'distruttive', 'chiude la finestra (compositore)'),
]

PALCHI = ['finestra', 'schermo-intero-api',
          'schermo-intero-api+lock-vecchia', 'schermo-intero-api+lock-nuova',
          'schermo-intero-F11+lock']


def misura_schermo():
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        dc = Gio.DBusProxy.new_sync(bus, Gio.DBusProxyFlags.NONE, None,
                                    "org.gnome.Mutter.DisplayConfig",
                                    "/org/gnome/Mutter/DisplayConfig",
                                    "org.gnome.Mutter.DisplayConfig", None)
        st = dc.call_sync("GetCurrentState", None, 0, -1, None).unpack()
        # ⚠ La misura NON sta nel monitor logico — li' l'indice 2 e' la SCALA e
        #   il 3 la trasformazione, e chi li legge come larghezza e altezza
        #   ottiene «1x0» senza nessun errore.  E' successo: la prima stesura
        #   stampava 1x0 e il banco girava lo stesso, perche' un numero
        #   sbagliato non si annuncia (`CODER.md` §3.10).
        for monitor in st[1]:
            for modo in monitor[1]:
                proprieta = modo[6] if len(modo) > 6 else {}
                if proprieta.get('is-current'):
                    return (int(modo[1]), int(modo[2]))
    except Exception:
        pass
    return (1920, 1080)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument('motori', nargs='*', default=['chrome', 'firefox'])
    p.add_argument('--porta', type=int, default=7681)
    p.add_argument('--palchi', default=','.join(PALCHI))
    p.add_argument('--gruppi', default='')
    p.add_argument('--esiti', default=os.path.join(QUI, '04-b29-esiti.jsonl'))
    p.add_argument('--base', default='/var/tmp/b29')
    p.add_argument('--solo-certifica', action='store_true',
                   help='gira solo i controlli, e dice se il banco e un banco')
    p.add_argument('--previeni', action='store_true',
                   help='il SECONDO giro: la pagina chiama preventDefault() su '
                        'ogni keydown, come fara il prodotto')
    a = p.parse_args()
    Pilota.previeni = a.previeni
    motori = a.motori or ['chrome', 'firefox']
    palchi = [x for x in a.palchi.split(',') if x]
    gruppi = set(x for x in a.gruppi.split(',') if x)

    os.makedirs(a.base, exist_ok=True)
    srv = Servitore(('127.0.0.1', a.porta), Manico)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print('== 04-b29 · sonda delle scorciatoie · pagina su 127.0.0.1:%d' % a.porta)

    schermo = misura_schermo()
    print('   schermo logico %dx%d · sessione %s · desktop %s'
          % (schermo[0], schermo[1], os.environ.get('XDG_SESSION_TYPE'),
             os.environ.get('XDG_CURRENT_DESKTOP')))

    # ⛔ PRIMA di creare la sessione di iniezione, non dopo: se lo schermo e'
    #    annerito, `CreateSession` fallisce e il banco muore all'avvio.
    sveglia = sveglia_e_trattieni(Gio.bus_get_sync(Gio.BusType.SESSION, None))
    print('   salvaschermo: %s' % sveglia)

    iniettore = Iniettore()
    print('   iniettore: org.gnome.Mutter.RemoteDesktop %s' % iniettore.percorso)

    giro_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    esiti = open(a.esiti, 'a')
    sommario = []

    try:
        for nome_m in motori:
            m = Motore(nome_m, a.porta,
                       {'chrome': 7682, 'firefox': 7683, 'chrome-app': 7684}[nome_m],
                       a.base)
            print('\n═════ %s — %s' % (nome_m, m.versione))
            pil = Pilota(m, iniettore, esiti, schermo, giro_id)
            if not pil.apri_browser(pulisci=True):
                print('   ⛔ il browser non ha aperto la pagina o non prende il fuoco: '
                      'NON MISURO NIENTE su questo motore')
                sommario.append((nome_m, None, 'non aperto'))
                m.ferma()
                continue
            cap = pil.chiedi_capacita()
            piatt = 'wayland' if 'wayland' in (os.environ.get('XDG_SESSION_TYPE') or '') else '?'
            print('   capacita: lock vecchia=%s · opzione keyboardLock letta=%s · fullscreenEnabled=%s'
                  % (cap.get('lock_vecchia'), cap.get('lock_nuova_opzione_letta'),
                     cap.get('fs_abilitato')))
            print('   UA: %s' % (cap.get('ua') or '')[:120])
            bers = m.ritratto_bersagli()
            print('   secondo strumento (debug remoto): %s'
                  % ('ASSENTE — su questo motore si misura con la sola pagina'
                     if bers is None else 'presente, %d pagine' % bers['n_pagine']))
            esiti.write(json.dumps({
                'giro': giro_id, 'ora': adesso(), 'banco': '04-b29', 'tipo': 'palco',
                'motore': nome_m, 'versione': m.versione,
                'ua': cap.get('ua'), 'lock_vecchia_presente': cap.get('lock_vecchia'),
                'opzione_keyboardLock_letta': cap.get('lock_nuova_opzione_letta'),
                'fullscreenEnabled': cap.get('fs_abilitato'),
                'secondo_strumento': bers is not None,
                'sessione': os.environ.get('XDG_SESSION_TYPE'),
                'desktop': os.environ.get('XDG_CURRENT_DESKTOP'),
                'schermo': list(schermo),
            }, ensure_ascii=False) + '\n')
            esiti.flush()

            for palco in palchi:
                print('\n  ── palco: %s' % palco)
                d = pil.monta_palco(palco)
                d['compositore'] = 'mutter/GNOME'
                d['piattaforma_finestre'] = piatt
                pil.palco = d
                print('     ottenuto: fullscreenElement=%s geometria_piena=%s lock_concessa=%s %s'
                      % (d.get('ottenuto_fullscreenElement'), d.get('ottenuto_geometria_piena'),
                         d.get('lock_concessa'), d.get('lock_motivo') or d.get('lock_errore') or ''))
                if palco != 'finestra' and not (d.get('ottenuto_fullscreenElement')
                                                or d.get('ottenuto_geometria_piena')):
                    print('     ⛔ lo schermo intero NON e stato ottenuto: il palco non e '
                          'quello dichiarato, salto (e lo scrivo)')
                    esiti.write(json.dumps({'giro': giro_id, 'ora': adesso(), 'banco': '04-b29',
                                            'tipo': 'palco-fallito', 'motore': nome_m,
                                            'palco': palco, 'dettaglio': d},
                                           ensure_ascii=False, default=str) + '\n')
                    esiti.flush()
                    continue

                # ⛔ I CONTROLLI PRIMA, e se non passano il palco non si crede.
                pos = pil.prova(*COMBINAZIONI[0][:2], note=COMBINAZIONI[0][3])
                pil.rimetti_a_posto(palco)
                neg = pil.prova(*COMBINAZIONI[1][:2], note=COMBINAZIONI[1][3])
                pil.rimetti_a_posto(palco)
                certificato = (pos['consegnata_alla_pagina'] and not pos['browser_ha_agito']
                               and not neg['consegnata_alla_pagina'])
                print('     controlli: positivo %s · negativo %s ⇒ banco %s'
                      % ('OK' if (pos['consegnata_alla_pagina'] and not pos['browser_ha_agito']) else 'FALLITO',
                         'OK' if not neg['consegnata_alla_pagina'] else 'FALLITO',
                         'CERTIFICATO' if certificato else '⛔ NON CERTIFICATO'))
                esiti.write(json.dumps({'giro': giro_id, 'ora': adesso(), 'banco': '04-b29',
                                        'tipo': 'certificazione', 'motore': nome_m,
                                        'palco': palco, 'certificato': certificato,
                                        'positivo': pos['stato'], 'negativo': neg['stato']},
                                       ensure_ascii=False) + '\n')
                esiti.flush()
                sommario.append((nome_m, palco, 'certificato' if certificato else 'NON certificato'))
                if a.solo_certifica:
                    continue
                if not certificato:
                    print('     ⛔ NON CERTIFICATO: le righe che seguono sarebbero '
                          'numeri senza banco.  Salto il palco.')
                    continue

                for nome, tasti, gruppo, nota in COMBINAZIONI[2:]:
                    if gruppi and gruppo not in gruppi:
                        continue
                    if not pil.rimetti_a_posto(palco):
                        print('     ⛔ non riesco a rimettere il palco: fermo qui il palco')
                        break
                    pil.prova(nome, tasti, note=nota)
                pil.rimetti_a_posto(palco)
            m.ferma()
    finally:
        iniettore.chiudi()
        esiti.close()
        srv.shutdown()

    print('\n== sommario dei palchi')
    for r in sommario:
        print('   %-9s %-34s %s' % r)


if __name__ == '__main__':
    principale()
