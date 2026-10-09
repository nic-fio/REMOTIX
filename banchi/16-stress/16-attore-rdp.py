#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-attore-rdp — UN UTENTE SIMULATO DAVANTI A xrdp (fasi/20-le-prestazioni.md §7)

    python3 16-attore-rdp.py --scatola gnome|kde|xfce|lxqt --utente N --display :2NN \\
        --dir DIR --seme S [--largo 3840 --alto 2160] [--video FILE]
    python3 16-attore-rdp.py --controllo --scatola xfce --display :200 --dir DIRLIV ...
    python3 16-attore-rdp.py --certifica

E' il gemello di 16-attore.py per il confronto con xrdp: STESSO ritmo (Ritmo, stessi semi),
STESSI quattro lavori (16-lavori.py), STESSO schema di stato.jsonl / nascita.json /
eventi.jsonl, cosi' 16-classifica.py --sistema xrdp li legge.  Cambia il cliente:

  scatola   rete11-<desktop>-xrdp (Contenitore.xrdp): xrdp di Debian 13 com'e', il
            desktop su X11
  cliente   xfreerdp3 /gfx a tutto schermo nell'Xvfb di questo utente
            (16-compositori-rdp.sh), /sound:sys:fake: l'audio viaggia e non si suona
  mani      XTEST sull'Xvfb (python-xlib): l'input passa DAL CANALE RDP, come quello
            di una persona davanti a FreeRDP
  foto      l'Xvfb intero (get_image), 1:1 col desktop remoto
  dipinti   XDamage sulla finestra di FreeRDP: l'ora di ogni disegno, raggruppati in
            «raffiche» separate da piu' di 5 ms.  ⭐ E' la misura dal lato di chi guarda.
            ⚠ Due condizioni misurate il 9 ott: `damage_query_version()` prima di
            tutto (senza, ZERO eventi e nessun errore), e il danno sulla finestra di
            FreeRDP, non sulla radice.

stato.jsonl, ogni 5 s: conti {"dipinti": raffiche CUMULATIVE}, dipinti_s, input [{ok,
latenza_ms, azione}], blocco_max_ms (impulso → primo disegno dopo, o il fermo del video),
ritardi_ms (gli stessi, uno per impulso chiuso nell'intervallo), ritardi_eco_ms (solo i
tasti battuti dove l'eco e' immediata), lavoro, caduta (xfreerdp uscito o la finestra
sparita), errori, eventi.  ⛔ NON ci sono consegnati, salt, buchi, audio: xrdp non manda i
fotogrammi che non puo' (FreeRDP li riscontra), e non ha contatori nella pagina (§7.3).

nascita.json: accesso_ms = l'avvio di xfreerdp (utente e parola sulla riga: niente
schermata d'accesso); primo_fotogramma_ms = il primo istante in cui la sessione X
dell'inquilino esiste E la foto non e' degenere (almeno 40 colori distinti, la regola di
`desktop_scuro_ma_vivo`); degenere se a 15 s dall'accesso ancora no (§9).

--controllo: il controllo corto ridotto di §7.3 — una sessione in piu' (utente 99,
profilo C), che entra, apre il terminale, batte due comandi e li trova nella storia di
bash, ed esce.  Scrive DIR/controllo-corto.json nello schema di 16-controllo-corto.py
(esiti RDP-accesso, RDP-schermo, RDP-tastiera; nascita).

Codice d'uscita come 16-attore.py: 0 fermato dopo aver lavorato · 1 accesso o avvio non
riusciti · 2 errore del banco.
"""
import argparse
import importlib.util as _iu
import json
import os
import re
import secrets
import select
import signal
import subprocess
import sys
import threading
import time
import traceback

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)
DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A16 = _carica("attore16", os.path.join(QUI, "16-attore.py"))
L = A16.L
Ritmo, Fine = A16.Ritmo, A16.Fine
attese_impulsi, pausa_piu_lunga = A16.attese_impulsi, A16.pausa_piu_lunga
esito_nascita, lavora_dopo_nascita = A16.esito_nascita, A16.lavora_dopo_nascita
TETTO_DEGENERE_S = A16.TETTO_DEGENERE_S
RAFFICA_S = 0.005             # due disegni a meno di 5 ms sono lo stesso fotogramma (§7.3)
COLORI_VIVO = 40              # la regola di desktop_scuro_ma_vivo (12-c20-veri.py)


def _preferenze_firefox():
    """Le preferenze del Firefox interno: le stesse di 11-c21 (PREFERENZE), lette dal
    file e non importate (quel modulo si tira dietro le guide dei browser)."""
    try:
        s = open(os.path.join(BANCHI, "11-scatole", "11-c21-sul-bordo-la-forma-cambia.py"),
                 encoding="utf-8").read()
        m = re.search(r'^PREFERENZE = """(.*?)"""', s, re.S | re.M)
        if m:
            return m.group(1)
    except OSError:
        pass
    return 'user_pref("browser.shell.checkDefaultBrowser", false);\n'


def _parola_sudo():
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


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE (certificate)
# ═══════════════════════════════════════════════════════════════════════════
class Raffiche:
    """⭐ I disegni XDamage ⇒ «raffiche» (un fotogramma di FreeRDP arriva come piu'
    rettangoli): un disegno a piu' di RAFFICA_S dal precedente apre una raffica nuova."""

    def __init__(self, soglia=RAFFICA_S):
        self.soglia, self.ultimo, self.n, self.t = soglia, None, 0, []

    def disegno(self, t):
        nuova = self.ultimo is None or t - self.ultimo > self.soglia
        if nuova:
            self.n += 1
            self.t.append(t)
            if len(self.t) > 20000:
                del self.t[:5000]
        self.ultimo = t
        return nuova


def colori_distinti(im, fattore=8):
    """Quanti colori distinti nella foto ridotta di `fattore` (None se illeggibile)."""
    w, h = im.size
    p = im.resize((max(1, w // fattore), max(1, h // fattore)))
    c = p.getcolors(maxcolors=1 << 20)
    return len(c) if c else None


def tasto_x(c):
    """Il nome del keysym di un carattere battuto (per XK.string_to_keysym)."""
    return NOMI_TASTI.get(c, c)


NOMI_TASTI = {" ": "space", "-": "minus", "~": "asciitilde", "/": "slash", "|": "bar",
              "*": "asterisk", ".": "period", "'": "apostrophe", "#": "numbersign",
              "_": "underscore", ",": "comma", "=": "equal", ":": "colon", ">": "greater",
              "<": "less", '"': "quotedbl", "(": "parenleft", ")": "parenright", "$": "dollar",
              "@": "at", "!": "exclam", "?": "question", "+": "plus", "&": "ampersand",
              ";": "semicolon", "\n": "Return", "\t": "Tab", "\\": "backslash",
              "[": "bracketleft", "]": "bracketright", "{": "braceleft", "}": "braceright",
              "%": "percent", "^": "asciicircum", "`": "grave",
              "Enter": "Return", "PageDown": "Next", "PageUp": "Prior", "Escape": "Escape",
              "Delete": "Delete", "Home": "Home", "Control": "Control_L", "Shift": "Shift_L",
              "Alt": "Alt_L"}


def caduta_da_registro(testo):
    """Il registro di xfreerdp dice che la connessione e' caduta?  (frase o None)"""
    for rx in (r"ERRCONNECT_\w+", r"ERRINFO_\w+", r"connection (?:lost|closed|failure)",
               r"Network disconnect", r"freerdp_check_fds\(\) failed"):
        m = re.search(rx, testo or "", re.I)
        if m:
            return m.group(0)
    return None


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)

    print("── le raffiche")
    r = Raffiche()
    for t in (1.000, 1.001, 1.004, 1.040, 1.041, 1.080):
        r.disegno(t)
    prova("6 disegni in 3 gruppi ⇒ 3 raffiche", r.n == 3 and r.t == [1.000, 1.040, 1.080], str(r.t))
    r = Raffiche()
    for k in range(300):
        r.disegno(10 + k / 30.0)
    prova("un video a 30 al secondo ⇒ 30 raffiche al secondo", r.n == 300)
    # ⛔ GUASTO: una soglia di 50 ms (troppo larga) fonde i fotogrammi del video
    r = Raffiche(soglia=0.05)
    for k in range(300):
        r.disegno(10 + k / 30.0)
    prova("GUASTO visto: soglia di 50 ms ⇒ il video a 30/s diventa UNA raffica", r.n == 1, str(r.n))
    at, ap = attese_impulsi([10.0, 12.0], [10.03, 12.4], 13.0)
    prova("impulso → primo disegno dopo: 30 e 400 ms", [round(x, 3) for x in at] == [0.03, 0.4]
          and not ap, str(at))

    print("── i tasti")
    prova("spazio, trattino, tilde, barra, asterisco", [tasto_x(c) for c in " -~/*"] ==
          ["space", "minus", "asciitilde", "slash", "asterisk"])
    prova("lettere e cifre restano se stesse", tasto_x("a") == "a" and tasto_x("7") == "7")
    prova("Invio, PagGiu', PagSu' coi nomi di X", tasto_x("Enter") == "Return"
          and tasto_x("PageDown") == "Next" and tasto_x("PageUp") == "Prior")
    # ⛔ GUASTO: ogni carattere dei comandi dei lavori ha un nome conosciuto
    from Xlib import XK
    tutti = set("".join(c for c, _p in L.COMANDI_C) + " #k0123456789" + "".join(L.PAROLE_NOTA)
                + "/home/c16001u1/prova16/nuove")
    ignoti = sorted(c for c in tutti if XK.string_to_keysym(tasto_x(c)) == 0)
    prova("ogni carattere dei comandi C ha un keysym", not ignoti, str(ignoti))
    prova("GUASTO visto: un nome sbagliato ⇒ keysym 0", XK.string_to_keysym("trattino") == 0)

    print("── la foto")
    try:
        from PIL import Image, ImageDraw
        nero = Image.new("RGB", (800, 600), (0, 0, 0))
        prova("tutto nero ⇒ 1 colore (degenere)", colori_distinti(nero) == 1)
        viva = nero.copy()
        dr = ImageDraw.Draw(viva)
        for i in range(60):
            dr.rectangle([i * 13, 0, i * 13 + 12, 20], fill=(i * 4, 255 - i * 4, (i * 37) % 255))
        prova("un pannello di 60 colori ⇒ vivo", (colori_distinti(viva) or 0) >= COLORI_VIVO,
              str(colori_distinti(viva)))
    except ImportError:
        prova("PIL c'e'", False)

    print("── la caduta dal registro di FreeRDP")
    prova("ERRCONNECT_CONNECT_TRANSPORT_FAILED vista",
          caduta_da_registro("[ERROR] ... ERRCONNECT_CONNECT_TRANSPORT_FAILED [0x0002000D]")
          == "ERRCONNECT_CONNECT_TRANSPORT_FAILED")
    prova("un registro pulito ⇒ nessuna caduta",
          caduta_da_registro("[WARN][com.freerdp.core.license] - license binary blob") is None)
    print("── l'inquilino e le porte")
    prova("inquilino come 16-attore (c16001u1, il controllo c16099u99)",
          L.inquilino_di(1) == "c16001u1" and L.inquilino_di(99) == "c16099u99")
    print("⛔ CERTIFICAZIONE FALLITA (%d)" % len(guai) if guai else "⭐ CERTIFICATO")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  LA SCATOLA E LA SESSIONE X DELL'INQUILINO
# ═══════════════════════════════════════════════════════════════════════════
class Scatola:
    """Comandi da root nella scatola, LOCALI (sudo podman exec), come suite.py sul server."""

    def __init__(self, desktop):
        self.nome = desktop
        self.contenitore = "rete11-%s-xrdp" % desktop

    def dentro(self, riga, secondi=90):
        try:
            r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.contenitore,
                                "sh", "-c", riga], input=_parola_sudo(), capture_output=True,
                               text=True, errors="replace", timeout=secondi)
        except subprocess.TimeoutExpired:
            return None, "(nessuna risposta in %d s)" % secondi
        return r.returncode, (r.stdout + r.stderr).strip()

    def crea(self, chi, parola):
        return self.dentro("useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
                           % (chi, chi, parola), 60)

    def sgombera(self, chi):
        self.dentro("loginctl terminate-user %s >/dev/null 2>&1; "
                    "pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null; "
                    "pkill -KILL -u %s >/dev/null 2>&1; sleep 0.5; "
                    "userdel -r %s >/dev/null 2>&1 || userdel %s >/dev/null 2>&1; "
                    "rm -rf /home/%s" % (chi, chi[0], chi[1:], chi, chi, chi, chi), 90)


AMBIENTE_X = (r"(DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_[A-Z_]+|LANG|LC_[A-Z]+|PATH|"
              r"DESKTOP_SESSION|KDE_[A-Z_]+|GTK_[A-Z_]+|QT_[A-Z_]+|GNOME_[A-Z_]+|SESSION_MANAGER)")


class SessioneX:
    """`nella_sessione` di suite.Sessione, per una sessione X portata da xrdp: l'ambiente
    (DISPLAY dell'Xorg dell'inquilino, XAUTHORITY, il bus) si legge da un processo
    della sessione (/proc/<pid>/environ), senza MOZ_ENABLE_WAYLAND."""

    def __init__(self, sc, chi):
        self.sc, self.chi = sc, chi

    def _amb(self):
        return ("u=$(id -u %(c)s) || exit 2; p=''; for q in $(pgrep -u $u); do "
                "tr '\\0' '\\n' < /proc/$q/environ 2>/dev/null | grep -q '^DISPLAY=' && p=$q; done; "
                "[ -n \"$p\" ] || { echo 'nessuna sessione X'; exit 2; }; "
                "amb=$(tr '\\0' '\\n' < /proc/$p/environ | grep -E '^%(r)s=' | tr '\\n' ' '); "
                % {"c": self.chi, "r": AMBIENTE_X})

    def pronta(self):
        """La sessione X dell'inquilino c'e' (un suo processo ha DISPLAY)?"""
        c, t = self.sc.dentro(self._amb() + "echo \"$amb\" | grep -o 'DISPLAY=[^ ]*'", 30)
        return c == 0, (t or "").strip()

    def nella_sessione(self, comando, secondi=60, fondo=True):
        corpo = ("runuser -u %(c)s -- env -i $amb HOME=/home/%(c)s USER=%(c)s LOGNAME=%(c)s "
                 "SHELL=/bin/bash sh -c %(q)s" % {"c": self.chi, "q": _q(comando)})
        if fondo:
            corpo = "setsid %s < /dev/null > /home/%s/.c16-%s.log 2>&1 & echo lanciato" % (
                corpo, self.chi, re.sub(r"\W", "", comando.split()[0])[:20])
        return self.sc.dentro(self._amb() + corpo, secondi)

    def come_utente(self, comando, secondi=60):
        return self.sc.dentro("runuser -u %s -- %s 2>&1" % (self.chi, comando), secondi)


# ═══════════════════════════════════════════════════════════════════════════
#  LA SONDA XDamage (un filo suo, una connessione sua)
# ═══════════════════════════════════════════════════════════════════════════
class Sonda(threading.Thread):
    def __init__(self, nome_display, finestra):
        super().__init__(daemon=True)
        from Xlib import display
        from Xlib.ext import damage
        self.d = display.Display(nome_display)
        self.d.damage_query_version()                      # ⛔ senza, ZERO eventi
        w = self.d.create_resource_object("window", finestra)
        self.dmg = w.damage_create(damage.DamageReportNonEmpty)
        self.d.flush()
        self.r = Raffiche()
        self.serratura = threading.Lock()
        self.vivo = True
        self.errore = None

    def run(self):
        fd = self.d.fileno()
        try:
            while self.vivo:
                select.select([fd], [], [], 0.5)
                n = 0
                while self.d.pending_events():
                    self.d.next_event()
                    n += 1
                if n:
                    t = time.time()
                    with self.serratura:
                        self.r.disegno(t)
                    # NonEmpty: si svuota il danno, cosi' il prossimo disegno avvisa di nuovo
                    self.d.damage_subtract(self.dmg, 0, 0)
                    self.d.flush()
        except Exception as e:                               # noqa: BLE001
            self.errore = repr(e)

    def leggi(self):
        with self.serratura:
            return self.r.n, list(self.r.t)

    def ferma(self):
        self.vivo = False


# ═══════════════════════════════════════════════════════════════════════════
#  LE MANI — XTEST sull'Xvfb (l'input passa dal canale RDP)
# ═══════════════════════════════════════════════════════════════════════════
class Mani:
    def __init__(self, att):
        from Xlib import X, XK, display
        from Xlib.ext import xtest
        self.a, self.X, self.XK, self.xtest = att, X, XK, xtest
        self.d = display.Display(att.o.display)
        self.pos = None
        self.pausa_ms = 40

    def _kc(self, nome):
        ks = self.XK.string_to_keysym(tasto_x(nome))
        if not ks and len(nome) == 1:
            ks = ord(nome)
        kc = self.d.keysym_to_keycode(ks) if ks else 0
        if not kc:
            raise RuntimeError("nessun tasto per %r" % nome)
        maiusc = self.d.keycode_to_keysym(kc, 0) != ks
        return kc, maiusc

    def _giu(self, kc):
        self.xtest.fake_input(self.d, self.X.KeyPress, kc)
        self.d.sync()
        return time.time()

    def _su(self, kc):
        self.xtest.fake_input(self.d, self.X.KeyRelease, kc)
        self.d.sync()

    def _sposta(self, x, y):
        self.xtest.fake_input(self.d, self.X.MotionNotify, x=int(x), y=int(y))
        self.d.sync()

    def _limita(self, X, Y):
        tl, ta = self.a.desktop
        return max(1, min(tl - 2, X)), max(1, min(ta - 2, Y))

    def muovi(self, X, Y):
        X, Y = self._limita(X, Y)
        R = self.a.ritmo
        if self.pos:
            n = R.intero(3, 8)
            for i in range(1, n):
                f = i / float(n)
                self._sposta(self.pos[0] + (X - self.pos[0]) * f, self.pos[1] + (Y - self.pos[1]) * f)
                time.sleep(R.intero(12, 30) / 1000.0)
        self._sposta(X, Y)
        time.sleep(R.intero(60, 180) / 1000.0)
        self.pos = (X, Y)
        return time.time()

    def clic(self, X, Y, bottone=0, atteso=False):
        self.muovi(X, Y)
        b = {0: 1, 1: 2, 2: 3}.get(bottone, 1)
        self.xtest.fake_input(self.d, self.X.ButtonPress, b)
        self.d.sync()
        t = time.time()
        time.sleep(self.a.ritmo.intero(50, 120) / 1000.0)
        self.xtest.fake_input(self.d, self.X.ButtonRelease, b)
        self.d.sync()
        if atteso:
            self.a.impulso(t)
        self.a.conta("clic_mouse")
        return t

    def rotella(self, X, Y, tacche, atteso=False):
        """`tacche` > 0 in giu' (bottone 5), < 0 in su' (bottone 4)."""
        self.muovi(X, Y)
        b = 5 if tacche > 0 else 4
        t = None
        for _ in range(abs(tacche)):
            self.xtest.fake_input(self.d, self.X.ButtonPress, b)
            self.xtest.fake_input(self.d, self.X.ButtonRelease, b)
            self.d.sync()
            t = t or time.time()
            time.sleep(self.a.ritmo.intero(40, 160) / 1000.0)
        t = t or time.time()
        if atteso:
            self.a.impulso(t)
        self.a.conta("tacche")
        return t

    def premi(self, nome, atteso=False):
        kc, maiusc = self._kc(nome)
        sh = self._kc("Shift")[0] if maiusc else None
        if sh:
            self._giu(sh)
        t = self._giu(kc)
        time.sleep(self.pausa_ms / 1000.0)
        self._su(kc)
        if sh:
            self._su(sh)
        time.sleep(self.pausa_ms / 1000.0)
        if atteso:
            self.a.impulso(t)
        return t

    def combo(self, mod, tasto):
        mods = [self._kc(m)[0] for m in mod]
        kc, _m = self._kc(tasto.lower() if len(tasto) == 1 else tasto)
        for m in mods:
            self._giu(m)
            time.sleep(0.02)
        t = self._giu(kc)
        time.sleep(self.pausa_ms / 1000.0)
        self._su(kc)
        for m in reversed(mods):
            time.sleep(0.02)
            self._su(m)
        return t

    def batti(self, testo, atteso=True, eco=False):
        """Ogni carattere un tasto vero, col ritmo della persona; ogni ~1,5 s il cuore
        (la riga di stato e i segnali).  `eco`: il carattere compare subito ⇒ il suo
        impulso conta anche fra i ritardi «a eco»."""
        R = self.a.ritmo
        dur = 0.0
        sh = self._kc("Shift")[0]
        for c in testo:
            ten, bat = R.tenuta_ms(), R.battuta_ms()
            kc, maiusc = self._kc(c)
            if maiusc:
                self._giu(sh)
            t = self._giu(kc)
            if atteso:
                self.a.impulso(t, eco=eco)
            time.sleep(ten / 1000.0)
            self._su(kc)
            if maiusc:
                self._su(sh)
            time.sleep(max(0.0, bat - ten) / 1000.0)
            dur += bat / 1000.0
            if dur >= 1.5:
                dur = 0.0
                self.a.cuore()
        self.a.conta("tasti")
        return time.time()


# ═══════════════════════════════════════════════════════════════════════════
#  L'ATTORE
# ═══════════════════════════════════════════════════════════════════════════
class Attore:
    def __init__(self, o):
        self.o = o
        self.n = o.utente
        self.profilo = "C" if o.controllo else L.profilo_di(self.n)
        self.browser = "freerdp"
        self.chi = L.inquilino_di(self.n)
        if o.controllo:
            # ⛔ [M] 9 ott, prova a 2K: con lo STESSO nome a ogni livello xrdp-sesman ritrovava
            #   la sessione del livello prima (ancora in chiusura) e ci si riattaccava ⇒
            #   ERRINFO_LOGOFF_BY_USER dopo 1,5 s.  Un nome per livello, sempre «…u99»
            #   (16-classifica riconosce il controllo dalla coda del nome).
            k = int(re.sub(r"\D", "", str(o.livello)) or 0)
            self.chi = "c16%03du99" % (900 + k % 100)
        self.parola = "c16-" + secrets.token_hex(8)
        self.porta_interna = L.porta_interna(o.scatola, self.n)
        self.ritmo = Ritmo(o.seme, self.n)
        self.cartella = os.path.join(o.dir, "controllo-corto" if o.controllo else "utente-%02d" % self.n)
        os.makedirs(self.cartella, exist_ok=True)
        self.f_stato = open(os.path.join(self.cartella, "stato.jsonl"), "a", buffering=1)
        self.f_eventi = open(os.path.join(self.cartella, "eventi.jsonl"), "a", buffering=1)
        self.sc = Scatola(o.scatola)
        self.s = SessioneX(self.sc, self.chi)
        self.versione = "?"
        self.eventi_finestra, self.errori_finestra = [], []
        self.impulsi, self.impulsi_eco = [], []
        self.entrato = False
        self.desktop = (o.largo, o.alto)
        self.mani = self.sonda = self.lavoro = self.rdp = None
        self.finestra = None
        self.voglio_foto = self.fermati = False
        self.prossimo_stato = 0.0
        self.azioni, self.fatte_finestra = {}, 0
        self.verifiche, self.ver_finestra = {"ok": 0, "ko": 0}, []
        self.prec = None
        self.foto_size = None
        self.x = None                          # connessione X per le foto
        self.creato = False

    # -- le righe -------------------------------------------------------------
    def _testa(self, evento):
        return {"t": round(time.time(), 3), "utente": self.n, "profilo": self.profilo,
                "browser": self.browser, "versione": self.versione, "inquilino": self.chi,
                "evento": evento}

    def riga(self, **campi):
        r = self._testa("stato")
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
            print("   [%02d %s] ⚠ input NON verificato: %s" % (self.n, self.profilo, v), flush=True)

    def impulso(self, t, eco=False):
        self.impulsi.append(t)
        if eco:
            self.impulsi_eco.append(t)

    # -- il cuore -------------------------------------------------------------
    def cuore(self):
        if self.fermati:
            raise Fine("segnale")
        if self.voglio_foto:
            self.voglio_foto = False
            self.scatta()
        if time.time() >= self.prossimo_stato:
            self.in_ritardo = time.time() - self.prossimo_stato if self.prossimo_stato else 0.0
            self.scrivi_stato()
            self.prossimo_stato = time.time() + 5.0

    def dorme(self, secondi):
        fine = time.time() + max(0.0, secondi)
        while True:
            self.cuore()
            resto = fine - time.time()
            if resto <= 0:
                return
            time.sleep(min(0.25, resto))

    def rdp_vivo(self):
        return self.rdp is not None and self.rdp.poll() is None

    def registro_rdp(self):
        try:
            return open(os.path.join(self.cartella, "xfreerdp.log"), errors="replace").read()[-20000:]
        except OSError:
            return ""

    def scrivi_stato(self):
        if self.sonda is None:
            return
        ora = time.time()
        n, dt_lista = self.sonda.leggi()
        errori = list(self.errori_finestra)
        if self.sonda.errore:
            errori.append("la sonda XDamage e' ferma: %s" % self.sonda.errore)
        caduta = False
        if self.entrato and not self.rdp_vivo():
            caduta = True
            errori.append("xfreerdp e' uscito (codice %s): %s" % (
                self.rdp.returncode if self.rdp else None,
                caduta_da_registro(self.registro_rdp()) or "nessuna riga d'errore"))
        blocco, lavoro, ritardi, eco = None, False, [], []
        if self.profilo == "D":
            if self.video_in_corso():
                blocco = pausa_piu_lunga(dt_lista, self.prec[0] if self.prec else ora - 5, ora)
                lavoro = True
        else:
            ritardi, self.impulsi = attese_impulsi(self.impulsi, dt_lista, ora)
            eco, self.impulsi_eco = attese_impulsi(self.impulsi_eco, dt_lista, ora)
            if ritardi:
                blocco, lavoro = max(ritardi), True
        conti = {"dipinti": n}
        campi = {"conti": conti, "input": self.ver_finestra,
                 "blocco_max_ms": None if blocco is None else round(blocco * 1000),
                 "ritardi_ms": [round(x * 1000, 1) for x in ritardi],
                 "ritardi_eco_ms": [round(x * 1000, 1) for x in eco],
                 "lavoro": lavoro, "caduta": caduta, "errori": errori,
                 "sessione": self.rdp_vivo(), "sistema": "xrdp"}
        if self.prec:
            dt = ora - self.prec[0]
            campi["delta"] = {"dipinti": n - self.prec[1], "s": round(dt, 2)}
            if dt > 0:
                campi["dipinti_s"] = round((n - self.prec[1]) / dt, 2)
        self.prec = (ora, n)
        campi["in_ritardo_s"] = round(getattr(self, "in_ritardo", 0.0), 2)
        campi.update({"azioni": dict(self.azioni), "azioni_finestra": self.fatte_finestra,
                      "verifiche": dict(self.verifiche)})
        if self.lavoro is not None:
            try:
                campi["dettagli_lavoro"] = self.lavoro.extra()
            except Exception as e:                  # noqa: BLE001
                campi["dettagli_lavoro"] = {"errore": str(e)[:200]}
        if self.eventi_finestra:
            campi["eventi"] = self.eventi_finestra
        self.fatte_finestra = 0
        self.ver_finestra, self.errori_finestra, self.eventi_finestra = [], [], []
        self.riga(**campi)

    def video_in_corso(self):
        v = getattr(self.lavoro, "ultimo_video", None) or {}
        return self.entrato and v.get("stato") == 1

    # -- le foto --------------------------------------------------------------
    def foto_pil(self):
        from PIL import Image
        from Xlib import X, display
        try:
            if self.x is None:
                self.x = display.Display(self.o.display)
            r = self.x.screen().root
            g = r.get_geometry()
            img = r.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xffffffff)
            im = Image.frombytes("RGB", (g.width, g.height), img.data, "raw", "BGRX")
        except Exception:                            # noqa: BLE001
            return None
        self.foto_size = im.size
        return im

    def scatta(self):
        t = time.time()
        im = self.foto_pil()
        if im is None:
            self.evento("foto", ok=False, perche="l'Xvfb non si fotografa")
            return
        f = os.path.join(self.cartella, "foto-%d.png" % int(t * 1000))
        im.save(f)
        self.evento("foto", ok=True, file=f, ms=round((time.time() - t) * 1000))

    def foto_al_desktop(self, r):
        """⭐ La foto e' l'Xvfb, e FreeRDP e' a tutto schermo: 1:1 col desktop remoto."""
        if not r:
            return None
        tl, ta = self.desktop
        return (max(0, r[0]), max(0, r[1]), min(tl, r[2]), min(ta, r[3]))

    def preferenze_interne(self):
        return _preferenze_firefox()

    # -- il cliente -----------------------------------------------------------
    def cerca_finestra(self):
        from Xlib import display
        if self.x is None:
            self.x = display.Display(self.o.display)
        for w in self.x.screen().root.query_tree().children:
            try:
                cl = w.get_wm_class() or ()
            except Exception:                        # noqa: BLE001
                continue
            if any("remotix-rdp" in (c or "") for c in cl):
                return w.id
        return None

    def accendi_rdp(self):
        cmd = ["xfreerdp3", "/v:127.0.0.1", "/u:%s" % self.chi, "/p:%s" % self.parola,
               "/cert:ignore", "/gfx", "/f", "/sound:sys:fake",
               "/wm-class:remotix-rdp-%02d" % self.n]
        amb = dict(os.environ, DISPLAY=self.o.display)
        amb.pop("WAYLAND_DISPLAY", None)
        log = open(os.path.join(self.cartella, "xfreerdp.log"), "a")
        log.write("=== %s\n" % time.strftime("%F %T"))
        log.flush()

        def oom():
            try:
                open("/proc/self/oom_score_adj", "w").write("800")
            except OSError:
                pass
        self.rdp = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=amb,
                                    stdin=subprocess.DEVNULL, start_new_session=True,
                                    preexec_fn=oom)

    def entra(self):
        o = self.o
        n = {"inquilino": self.chi, "browser": self.browser, "versione": self.versione,
             "scatola": o.scatola, "sistema": "xrdp", "misura": [o.largo, o.alto]}
        t0 = time.time()
        self.accendi_rdp()
        n["accesso_ms"] = round(t0 * 1000)
        # la finestra di FreeRDP, poi la sonda
        while time.time() < t0 + o.tetto_s and self.finestra is None:
            if not self.rdp_vivo():
                c = caduta_da_registro(self.registro_rdp())
                n.update(esito="rifiuto" if c and "AUTH" in c.upper() else "nessun_fotogramma",
                         motivo="xfreerdp e' uscito prima della finestra: %s" % c)
                return n
            self.finestra = self.cerca_finestra()
            if self.fermati:
                raise Fine("segnale")
            time.sleep(0.1)
        if self.finestra is None:
            n.update(esito="nessun_fotogramma", motivo="nessuna finestra di FreeRDP in %d s" % o.tetto_s)
            return n
        self.sonda = Sonda(o.display, self.finestra)
        self.sonda.start()
        # il desktop vivo: la sessione X dell'inquilino c'e', e la foto non e' degenere
        primo, sessione, colori, ultimo_ctl = None, False, None, 0.0
        while time.time() < t0 + o.tetto_s:
            if self.fermati:
                raise Fine("segnale")
            if not self.rdp_vivo():
                n.update(esito="nessun_fotogramma", motivo="xfreerdp e' uscito durante l'accesso: %s"
                         % caduta_da_registro(self.registro_rdp()))
                return n
            if not sessione and time.time() - ultimo_ctl > 1.0:
                ultimo_ctl = time.time()
                sessione, _d = self.s.pronta()
            im = self.foto_pil()
            colori = colori_distinti(im) if im is not None else None
            if sessione and colori is not None and colori >= COLORI_VIVO:
                primo = time.time()
                break
            time.sleep(0.25)
        n["primo_fotogramma_ms"] = round(primo * 1000) if primo else None
        n["nascita_ms"] = round((primo - t0) * 1000) if primo else None
        n["colori_distinti"] = colori
        n["sessione_x"] = sessione
        n["prima_raffica_ms"] = round(self.sonda.leggi()[1][0] * 1000) if self.sonda.leggi()[1] else None
        if not primo:
            if sessione:
                # la sessione c'e' ma il desktop resta degenere: si lavora lo stesso
                n["primo_fotogramma_ms"] = n["prima_raffica_ms"]
                n["nascita_ms"] = (n["prima_raffica_ms"] - n["accesso_ms"]) if n["prima_raffica_ms"] else None
                n.update(esito="degenere", motivo="desktop degenere (%s colori) a %d s" % (colori, o.tetto_s))
            else:
                n.update(esito="nessun_fotogramma", motivo="nessuna sessione X in %d s" % o.tetto_s)
            return n
        verde = primo - t0 <= TETTO_DEGENERE_S
        n["esito"], nota = esito_nascita(verde, not verde)
        if not verde:
            n["esito"] = "degenere"
            n["motivo"] = "il desktop e' vivo solo a %.1f s dall'accesso (tetto %d s)" % (
                primo - t0, TETTO_DEGENERE_S)
        else:
            n["motivo"] = "sessione X e %s colori distinti a %.1f s" % (colori, primo - t0)
        if nota:
            n["nota"] = nota
        return n

    def prepara_inquilino(self):
        self.sc.sgombera(self.chi)
        c, t = self.sc.crea(self.chi, self.parola)
        if c != 0:
            raise RuntimeError("non ho potuto creare l'inquilino %s: %s" % (self.chi, (t or "")[-200:]))
        self.creato = True
        self.sc.dentro("h=/home/%s; [ -L $h/.cache ] && rm -f $h/.cache; "
                       "install -d -o %s -g %s -m 700 $h/.cache" % (self.chi, self.chi, self.chi), 30)
        # ⭐ ~/.xsession arriva dallo scheletro (Contenitore.xrdp): si GUARDA che ci sia
        c, t = self.sc.dentro("cat /home/%s/.xsession" % self.chi, 30)
        if c != 0 or "exec " not in (t or ""):
            self.evento("errore", testo="~/.xsession dell'inquilino manca: la sessione non sarebbe "
                                        "il desktop (%s)" % (t or "")[:120])
            raise RuntimeError("~/.xsession assente nell'inquilino %s" % self.chi)
        self.evento("xsession", testo=(t or "").strip().splitlines()[-1][:120])

    # -- tutto ------------------------------------------------------------------
    def corri(self):
        o = self.o
        self.versione = (subprocess.run(["xfreerdp3", "/version"], capture_output=True, text=True)
                         .stdout.strip().splitlines() or ["?"])[0][:80]
        self.evento("inizio", inquilino=self.chi, scatola=o.scatola, display=o.display, seme=o.seme,
                    porta_interna=self.porta_interna, misura=[o.largo, o.alto], video=o.video or None,
                    pid=os.getpid(), sistema="xrdp")
        codice = 2
        try:
            self.prepara_inquilino()
            self.lavoro = L.LAVORI[self.profilo](self)
            self.lavoro.prepara()
            nascita = self.entra()
            with open(os.path.join(self.cartella, "nascita.json"), "w") as f:
                json.dump(nascita, f, ensure_ascii=False, indent=1)
            self.evento("nascita", **nascita)
            if not lavora_dopo_nascita(nascita):
                codice = 1
                self.salva_diagnosi()
                if o.controllo:
                    return codice
                self.aspetta_la_fine("accesso non riuscito")
                return codice
            self.entrato = True
            self.mani = Mani(self)
            # il fuoco della tastiera sulla finestra di FreeRDP (nell'Xvfb non c'e' un
            # gestore di finestre), poi un clic su un punto vuoto del desktop
            try:
                from Xlib import X
                self.mani.d.create_resource_object("window", self.finestra).set_input_focus(
                    X.RevertToParent, X.CurrentTime)
                self.mani.d.sync()
            except Exception as e:                   # noqa: BLE001
                self.evento("errore", testo="fuoco sulla finestra di FreeRDP: %r" % e)
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
                if o.controllo:
                    self.esiti_controllo = {"applicazione": False}
                    return codice
                self.aspetta_la_fine("l'applicazione non parte")
                return codice
            if o.controllo:
                ok = self.lavoro.comando("uname -a")
                self.esiti_controllo = {"applicazione": True, "comando": ok}
                return 0 if ok else 1
            errori = 0
            while True:
                try:
                    self.lavoro.passo()
                    errori = 0
                except Fine:
                    raise
                except Exception as e:               # noqa: BLE001
                    errori += 1
                    self.errori_finestra.append("%r" % e)
                    self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-600:],
                                di_fila=errori)
                    self.dorme(min(30, 2 * errori))
        except Fine:
            pass
        except Exception as e:                       # noqa: BLE001
            self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-800:], fatale=True)
            codice = 2
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.chiudi()
        return codice

    def salva_diagnosi(self):
        """Una nascita fallita: ~/.xsession-errors e il registro di Xorg dell'inquilino
        nella cartella, PRIMA che lo sgombero li cancelli."""
        c, t = self.sc.dentro("for f in /home/%s/.xsession-errors /home/%s/.xorgxrdp.*.log; do "
                              "echo \"== $f\"; tail -n 60 \"$f\" 2>/dev/null; done" % (self.chi, self.chi), 60)
        with open(os.path.join(self.cartella, "diagnosi-sessione.txt"), "w") as f:
            f.write(t or "")

    def aspetta_la_fine(self, perche):
        self.evento("in_attesa", perche=perche)
        while True:
            self.dorme(5)

    def chiudi(self):
        try:
            try:
                self.scrivi_stato()
            except Exception:                        # noqa: BLE001
                pass
            if self.sonda is not None:
                self.sonda.ferma()
            if self.rdp is not None and self.rdp.poll() is None:
                try:
                    os.killpg(self.rdp.pid, signal.SIGTERM)
                    self.rdp.wait(timeout=10)
                except Exception:                    # noqa: BLE001
                    try:
                        os.killpg(self.rdp.pid, signal.SIGKILL)
                    except OSError:
                        pass
        finally:
            if self.creato:
                try:
                    self.sc.sgombera(self.chi)
                except Exception as e:               # noqa: BLE001
                    print("   ⚠ uscita: %s" % e, flush=True)
            _c, t = self.sc.dentro("id %s >/dev/null 2>&1 && echo RESTA || echo via" % self.chi, 30)
            self.evento("fine", sgomberato=(t or "").strip().endswith("via"), azioni=self.azioni,
                        verifiche=self.verifiche)
            self.f_stato.close()
            self.f_eventi.close()


def controllo(o, att):
    """Il controllo corto ridotto (§7.3): entra, schermo, tastiera ⇒ controllo-corto.json."""
    t = time.time()
    codice = att.corri()
    try:
        na = json.load(open(os.path.join(att.cartella, "nascita.json")))
    except (OSError, ValueError):
        na = {}
    es_ctl = getattr(att, "esiti_controllo", {}) or {}
    acc = bool(na.get("primo_fotogramma_ms") or na.get("prima_raffica_ms"))
    esiti = {"RDP-accesso": "PASS" if acc else "FAIL",
             "RDP-schermo": "PASS" if na.get("esito") == "ok" else ("FAIL" if acc else "BLOCKED"),
             "RDP-tastiera": ("PASS" if es_ctl.get("applicazione") and es_ctl.get("comando") else
                              ("FAIL" if es_ctl else "BLOCKED"))}
    nas = {"nascita_s": round(na["nascita_ms"] / 1000.0, 2) if na.get("nascita_ms") is not None else None,
           "primo_non_degenere_s": round(na["nascita_ms"] / 1000.0, 2)
           if na.get("esito") == "ok" and na.get("nascita_ms") is not None else None,
           "rifiuto": na.get("esito") == "rifiuto", "esito": "PASS" if na.get("esito") == "ok" else "FAIL",
           "ragione": na.get("motivo")}
    out = {"utente": 99, "inquilino": att.chi, "browser": "freerdp", "versione": att.versione,
           "sistema": "xrdp", "esiti": esiti, "nascita": nas, "codice": codice,
           "esito": "FAIL" if "FAIL" in esiti.values() else ("PASS" if all(
               v == "PASS" for v in esiti.values()) else "BLOCKED"),
           "durata_s": round(time.time() - t, 1),
           "nota": "controllo corto RIDOTTO (fasi/20 §7.3): accesso, schermo, tastiera — le funzioni "
                   "F-0xx della pagina di REMOTIX non esistono in xrdp"}
    with open(os.path.join(o.dir, "controllo-corto.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("controllo corto xrdp: %s %s" % (out["esito"], esiti), flush=True)
    return 0 if out["esito"] == "PASS" else 1


def argomenti():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--controllo", action="store_true", help="il controllo corto ridotto (utente 99)")
    a.add_argument("--scatola", choices=DESKTOP)
    a.add_argument("--utente", type=int)
    a.add_argument("--display", help="l'Xvfb di questo utente (:2NN)")
    a.add_argument("--dir")
    a.add_argument("--seme", default="0")
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    a.add_argument("--video", default="")
    a.add_argument("--tetto-s", type=int, default=60)
    # accettati e ignorati: la salita li passa uguali a tutti e due gli attori
    a.add_argument("--porte-base", type=int, default=0)
    a.add_argument("--livello", default="")
    a.add_argument("--browser", default="")
    o = a.parse_args()
    if o.certifica:
        return o
    if o.controllo:
        o.utente = 99
        o.seme = o.seme if o.seme != "0" else "controllo"
    for k in ("scatola", "utente", "display", "dir"):
        if getattr(o, k) in (None, ""):
            a.error("serve --%s" % k)
    return o


def main():
    o = argomenti()
    if o.certifica:
        return certifica()
    try:
        open("/proc/self/oom_score_adj", "w").write("800")      # §7.7: i clienti muoiono prima
    except OSError:
        pass
    os.environ.pop("WAYLAND_DISPLAY", None)
    att = Attore(o)

    def _fine(_n, _f):
        att.fermati = True

    def _foto(_n, _f):
        att.voglio_foto = True
    signal.signal(signal.SIGTERM, _fine)
    signal.signal(signal.SIGINT, _fine)
    signal.signal(signal.SIGUSR1, _foto)
    print("⭐ attore xrdp %02d · %s · profilo %s · %s · %s" % (
        o.utente, o.scatola, att.profilo, o.display, att.chi), flush=True)
    if o.controllo:
        return controllo(o, att)
    return att.corri()


if __name__ == "__main__":
    sys.exit(main())
