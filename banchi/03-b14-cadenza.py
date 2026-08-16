#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03-b14-cadenza.py — ⭐ IL BANCO DELLA MISURA **M3**: la cadenza disaccoppiata.

    python3 banchi/03-b14-cadenza.py                 (da CHUWI: costruisce, copia, gira su NIC-OS)
    python3 03-b14-cadenza.py --qui                  (sul server, dove ci sono D-Bus e PipeWire)
    python3 banchi/03-b14-cadenza.py --alta 144      cambia la cadenza «alta»
    python3 banchi/03-b14-cadenza.py --secondi 45    allunga ogni cella

===========================================================================
⛔ L'IPOTESI, E CHE COSA LA FAREBBE CADERE
===========================================================================

`STUDI.md` §gnome §8.2, `[R]` 9 agosto 2026: `maxFramerate` fa **due mestieri
insieme** — e' il freno della cattura **ed e'** la frequenza del monitor
virtuale (`meta-screen-cast-virtual-stream-src.c:603`, `create_virtual_monitor`
calcola `refresh_rate` dal `max_framerate` negoziato).  Stesso numero da
tutt'e due le parti ⇒ battimento ⇒ **sei decimi**, cioe' i 37 fotogrammi su 60
che v1 ha preso per un muro.

E `ensure_virtual_monitor` **esce prima se la misura non cambia**:

    if (mode_info->width  == video_format->size.width &&
        mode_info->height == video_format->size.height)
      return;                       ← `meta-screen-cast-virtual-stream-src.c:632`

⇒ **negoziare alto e poi rinegoziare la sola cadenza, a misura identica,
  dovrebbe lasciare il monitor dov'e' e muovere solo il freno.**

⛔ E' una `[?]`, non una `[R]` applicata.  Una spiegazione che torna non e' una
   cura che funziona (`LEZIONI.md` §1.11): sapere PERCHE' una cosa succede non
   dimostra di saperla fermare.  I due esiti valgono uguale, e il banco e'
   scritto per non tirare verso nessuno dei due.

===========================================================================
⛔ LE TRE CELLE, E PERCHE' SONO TRE
===========================================================================

  A  «bassa»              sessione nuova, negoziata a 60      → monitor 60 Hz, freno 60
  B  «alta»               sessione nuova, negoziata a 120     → monitor 120 Hz, freno 120
  C  ⭐ «alta rinegoziata» LA STESSA sessione di B, rinegoziata a 60
                                                              → monitor 120 Hz, freno 60

C usa la sessione di B e non una nuova: e' l'unico modo in cui «a monitor
fermo» vuol dire qualcosa.  Fra B e C cambia **un numero solo**, e la scena, il
monitor, il flusso e il consumatore sono gli stessi oggetti.

===========================================================================
⛔ LA CERTIFICAZIONE DEL BANCO (§1.2), CHE VIENE PRIMA DELLA MISURA
===========================================================================

Un banco che dice sempre si' misura zero.  Quindi, sulla stessa sessione:

  · **controllo POSITIVO** — si rinegozia a **10**.  Il numero DEVE crollare a
    ~10.  Se resta dove sta, questo strumento non sa vedere il freno, e allora
    NESSUNA delle tre celle sopra vuol dire niente.
  · **controllo NEGATIVO** — si rinegozia **da 60 a 60**, lo stesso valore.  Il
    numero DEVE restare fermo.  Se si muove, quel che C guadagna e' l'ATTO di
    rinegoziare (un flusso che riparte, una coda che si svuota) e non la
    cadenza disaccoppiata — cioe' l'esperimento proverebbe un'altra cosa.
  · **controllo di RITORNO** — si rinegozia da 10 a 120: si deve tornare a B.
    Serve a escludere che il crollo del controllo positivo sia un guasto.

⛔ E il controllo che vale piu' di tutti: **il monitor non si e' ricreato**.
   Si guarda in due posti indipendenti, prima e dopo OGNI rinegoziazione:

     1. `DisplayConfig.GetCurrentState` — il **numero di serie** del monitor
        (`create_virtual_monitor` lo incrementa a ogni creazione: `0x%.6x`) e
        la **frequenza del modo corrente**;
     2. `mutter.log` — le righe «Added/Removed virtual monitor Meta-N», che e'
        Mutter stesso a dire (`LEZIONI.md` §1.6: non si deduce, si chiede).

   Se il monitor si ricrea, l'esperimento non ha provato quel che dice di
   provare, e va scritto cosi'.

===========================================================================
⛔ LA SCENA SI DICHIARA (§1.1), E SI CONTA QUANTO DISEGNA
===========================================================================

`weston-simple-egl` **non e' installato** ne' su NIC-OS ne' su CHUWI.  La scena
e' `03-b14-scena.c`, che e' la stessa forma scritta a mano — schermo intero,
opaca, un ridisegno per ogni `wl_surface.frame`, colore che ruota — piu' la
cosa che qui serve e che weston non fa: **sceglie il monitor**, e verifica su
quale e' finita leggendo `wl_surface.enter`.

⭐ E i suoi disegni si contano accanto ai fotogrammi consegnati.  E' il
   controllo che dice se il tetto e' del compositore o della scena: senza, un
   37 non si sa da dove venga.

===========================================================================
⚠ QUEL CHE QUESTO BANCO **NON** FA, e va detto prima dei numeri
===========================================================================

⛔ **Non accende una sessione GNOME sua.**  Su NIC-OS la sessione headless
   c'e' gia' (`gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`) e
   sotto ci girano i tre server 7448, 7501 e **7561 — quella che apre
   l'utente**.  Fermarla per un banco significherebbe spegnere il prodotto
   dell'utente.  ⇒ La sessione si **verifica** (viva, headless, tela
   1920x1080) e si riusa; se non c'e', ALLORA si accende con
   `00-sessione-gnome.sh avvia`.  E non si ferma mai.

⚠ **I buffer sono MemFd, non DMA-BUF.**  Non si offrono modificatori, quindi
   Mutter propone solo la forma senza (`meta-screen-cast-stream-src.c`,
   secondo ciclo di `build_format_params`).  Il freno sotto esame sta in
   `maybe_record_frame_with_timestamp`, cioe' PRIMA della scelta del buffer —
   ma la copia in memoria costa a Mutter, e se il tetto fosse li' invece che
   sul freno lo direbbe il conto dei disegni della scena.

⚠ **Il monitor del banco e' il terzo sullo stage**, accanto a quello della
   sessione (Meta-0) e a quello del server dell'utente (Meta-1).  Si aggiunge e
   si toglie; non si tocca nessuno degli altri due.  Le tre porte si contano
   prima e dopo.
"""

import argparse
import json
import os
import shlex
import shutil
import socket
import statistics
import subprocess
import sys
import threading
import time

# ---------------------------------------------------------------------------
# ⛔ La porta di questo banco e' la 7601, e qui NON si apre nessuna porta.
#    La riga esiste lo stesso: un banco che non nomina la propria porta e' un
#    banco che un giorno ne prende una d'altri.  7448, 7501 e 7561 sono di
#    altri e si CONTANO, prima e dopo.
# ---------------------------------------------------------------------------
PORTA_DI_QUESTO_BANCO = 7601
PORTE_ALTRUI = (7448, 7501, 7561)

SERVER = os.environ.get("IND", "192.168.0.2")
UTENTE_SERVER = os.environ.get("UTENTE", "nicfio")
REMOTA = "/media/REMOTIX/src"
QUI = os.path.dirname(os.path.abspath(__file__))

VERDE, ROSSO, GIALLO, FINE = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
# ⛔ L'ESITO STA NEL CODICE D'USCITA, NON NELLA PROSA — cura del 13 agosto 2026
#
# Fino a stasera `ko()` si limitava a STAMPARE e `esegui()` finiva con
# `return 0`.  ⇒ Con un guasto dentro, il rosso restava **soltanto nel testo**
# e `01-b12-guasti.py --giudica` avrebbe scritto «col guasto ha dato lo stesso
# esito del sano»: cioe' esattamente il difetto che il catalogo B12 esiste per
# trovare, **dentro** il banco che ha prodotto la legge della griglia.
#
# ⭐ La forma non e' inventata qui: e' quella dei banchi gia' certificati —
#    `03-b15-movimento.py` chiude con `return 1 if conto["rosso"] else 0`,
#    `03-b18-credito.py` con `return 1 if rossi else 0`, `03-b16-dipinti.py`
#    mette `esito = 1` accanto a ogni rosso.  L'ultimo `return` vale **1** se
#    c'e' stato un rosso e **0** se no; il **2** (versioni diverse, compilatore,
#    `scp`) e il **3** (sessione GNOME assente) restano quel che erano, cioe'
#    attrezzatura che manca — non una misura.
#
# ⛔ E il conto sta DENTRO `ko()` invece che accanto a ognuna delle 29 chiamate
#    perche' qui i rossi escono anche da `cella()`, che **ritorna presto** in
#    sei punti: un `esito = 1` scritto a mano ne avrebbe persi per strada, e un
#    rosso perso e' precisamente il difetto che si sta curando.
# ⚠ E non tocca **nessuna** misura: `ko()` stampa la stessa riga di prima, e
#   per di qua non passa nessun numero.
# ===========================================================================
ROSSI = 0


def ok(t):
    print("    %sOK%s  %s" % (VERDE, FINE, t), flush=True)


def ko(t):
    global ROSSI
    ROSSI += 1
    print("    %sNO%s  %s" % (ROSSO, FINE, t), flush=True)


def att(t):
    print("    %s??%s  %s" % (GIALLO, FINE, t), flush=True)


def inf(t):
    print("    --  %s" % t, flush=True)


def log(t):
    print("\n\033[1m== %s\033[0m" % t, flush=True)


def ora_us():
    return int(time.monotonic() * 1_000_000)


def nome_esiti(o):
    """⛔ Un file per forma di giro: un secondo giro non deve cancellare il primo."""
    if o.griglia:
        return "03-b14-esiti-griglia.jsonl"
    if o.scena2:
        return "03-b14-esiti-scena2.jsonl"
    return "03-b14-esiti.jsonl"


# ===========================================================================
#  Il lato CHUWI: costruisce, copia, e fa girare la' dove c'e' la sessione
# ===========================================================================
def costruisci_e_spedisci(lavoro):
    """Costruisce i due binari QUI e li porta la'.

    ⛔ Si costruisce su CHUWI perche' NIC-OS non ha ne' `gcc` ne' `pkg-config`
       fuori dal contenitore, e il contenitore vuole la parola di `sudo`.
       ⚠ E' lecito solo perche' le due macchine hanno **le stesse versioni**:
       glibc 2.41-12+deb13u3, libpipewire 1.4.2-1, libwayland-client 1.23.1-3,
       libegl1 1.7.0-1+b2 — verificato il 13 agosto 2026, ed e' una
       precondizione che questo banco **controlla** invece di sperarla.
    """
    os.makedirs(lavoro, exist_ok=True)
    proto = "/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml"

    log("0. Le due macchine hanno le stesse librerie? (precondizione, non speranza)")
    pacchetti = ("libpipewire-0.3-0t64", "libwayland-client0", "libegl1", "libgles2")
    qui_v = versioni_pacchetti(pacchetti, None)
    la_v = versioni_pacchetti(pacchetti, (UTENTE_SERVER, SERVER))
    qui_glibc = subprocess.run(["ldd", "--version"], capture_output=True, text=True).stdout.split("\n")[0]
    la_glibc = ssh("ldd --version | head -1").strip()
    diverse = [p for p in pacchetti if qui_v.get(p) != la_v.get(p)]
    for p in pacchetti:
        (ok if qui_v.get(p) == la_v.get(p) else ko)(
            "%-24s CHUWI %s · NIC-OS %s" % (p, qui_v.get(p), la_v.get(p)))
    (ok if qui_glibc.split()[-1] == la_glibc.split()[-1] else ko)(
        "glibc                    CHUWI %s · NIC-OS %s" % (qui_glibc.split()[-1], la_glibc.split()[-1]))
    if diverse or qui_glibc.split()[-1] != la_glibc.split()[-1]:
        ko("⛔ le versioni non coincidono: un binario costruito qui potrebbe non "
           "essere lo stesso programma la'.  NON costruisco.")
        sys.exit(2)

    log("1. Costruzione dei due strumenti (e si guarda l'esito del compilatore)")
    for cmd, nome in (
        (["wayland-scanner", "client-header", proto, os.path.join(lavoro, "xdg-shell-client-protocol.h")],
         "xdg-shell-client-protocol.h"),
        (["wayland-scanner", "private-code", proto, os.path.join(lavoro, "xdg-shell-protocol.c")],
         "xdg-shell-protocol.c"),
    ):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            ko("⛔ wayland-scanner: %s" % r.stderr.strip())
            sys.exit(2)
        ok(nome)

    def pkg(*nomi):
        return subprocess.run(["pkg-config", "--cflags", "--libs"] + list(nomi),
                              capture_output=True, text=True).stdout.split()

    build = [
        (["gcc", "-std=gnu11", "-Wall", "-Wextra", "-O2", "-I" + lavoro,
          os.path.join(QUI, "03-b14-scena.c"), os.path.join(lavoro, "xdg-shell-protocol.c")]
         + pkg("wayland-client", "wayland-egl", "egl", "glesv2")
         + ["-o", os.path.join(lavoro, "03-b14-scena")], "03-b14-scena"),
        (["gcc", "-std=gnu11", "-Wall", "-Wextra", "-O2", os.path.join(QUI, "03-b14-metro.c")]
         + pkg("libpipewire-0.3") + ["-lm", "-o", os.path.join(lavoro, "03-b14-metro")],
         "03-b14-metro"),
    ]
    # ⛔ La scena dello step 2 si COSTRUISCE, non si riscrive — e il sorgente
    #    non si tocca (e' di un altro gruppo).  Le si da' solo un binario e un
    #    `/dev/shm` nostri, che e' la regola dei banchi in parallelo.
    #
    # ⛔ E IL BINARIO SI CHIAMA `03-b14-scena2`, NON `03-scena`.  Provato col
    #    nome loro il 13 agosto 2026: `scp` risponde «dest open … Failure»,
    #    perche' su NIC-OS quel binario e' in uso da un altro banco.  Scrivere
    #    sopra il binario di un altro gruppo mentre gira e' esattamente il
    #    difetto che la regola dei banchi in parallelo vieta — e qui il sistema
    #    ci ha fermati; la prossima volta potrebbe non farlo.
    pres = "/usr/share/wayland-protocols/stable/presentation-time/presentation-time.xml"
    if os.path.exists(os.path.join(QUI, "03-scena.c")) and os.path.exists(pres):
        for cmd in (["wayland-scanner", "client-header", pres,
                     os.path.join(lavoro, "presentation-time-client-protocol.h")],
                    ["wayland-scanner", "private-code", pres,
                     os.path.join(lavoro, "presentation-time-protocol.c")]):
            subprocess.run(cmd, check=False)
        build.append((
            ["gcc", "-O2", "-Wall", "-Wextra", "-I" + lavoro,
             os.path.join(QUI, "03-scena.c"), os.path.join(lavoro, "xdg-shell-protocol.c"),
             os.path.join(lavoro, "presentation-time-protocol.c"),
             "-lwayland-client", "-lrt", "-lm", "-o", os.path.join(lavoro, "03-b14-scena2")],
            "03-b14-scena2"))

    for cmd, nome in build:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            ko("⛔ gcc %s:\n%s" % (nome, r.stderr))
            sys.exit(2)
        ok("%s costruito (%d byte)" % (nome, os.path.getsize(os.path.join(lavoro, nome))))

    log("2. Copia su NIC-OS")
    files = [os.path.join(lavoro, "03-b14-scena"), os.path.join(lavoro, "03-b14-metro"),
             os.path.join(QUI, "03-b14-cadenza.py"), os.path.join(QUI, "03-marca.py")]
    if os.path.exists(os.path.join(lavoro, "03-b14-scena2")):
        files.append(os.path.join(lavoro, "03-b14-scena2"))
    r = subprocess.run(["scp", "-q"] + files + ["%s@%s:%s/" % (UTENTE_SERVER, SERVER, REMOTA)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        ko("⛔ scp: %s" % r.stderr.strip())
        sys.exit(2)
    ok("scena, metro e orchestratore copiati in %s" % REMOTA)


def versioni_pacchetti(pacchetti, remoto):
    cmd = "dpkg-query -W -f='${Package} ${Version}\\n' " + " ".join(pacchetti) + " 2>/dev/null"
    if remoto:
        uscita = ssh(cmd)
    else:
        uscita = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True).stdout
    d = {}
    for r in uscita.splitlines():
        p = r.split()
        if len(p) == 2:
            d[p[0]] = p[1]
    return d


def ssh(comando, timeout=60):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        "%s@%s" % (UTENTE_SERVER, SERVER), comando],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout


def gira_la(argomenti):
    amb = ("export XDG_RUNTIME_DIR=/run/user/1000 "
           "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus; ")
    cmd = amb + "python3 %s/03-b14-cadenza.py --qui %s" % (REMOTA, " ".join(shlex.quote(a) for a in argomenti))
    p = subprocess.Popen(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                          "%s@%s" % (UTENTE_SERVER, SERVER), cmd],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for r in p.stdout:
        sys.stdout.write(r)
        sys.stdout.flush()
    p.wait()
    return p.returncode


# ===========================================================================
#  Il lato NIC-OS: la misura vera
# ===========================================================================
class Lettore(threading.Thread):
    """Legge le righe di un sottoprocesso senza bloccare nessuno.

    ⛔ Ogni riga porta gia' i propri microsecondi monotoni, scritti dal
       processo che l'ha prodotta: non si usa MAI l'ora in cui questo thread
       l'ha letta.  Le due sono diverse di quanto pesa uno scheduler, e la
       differenza e' proprio dell'ordine di grandezza che stiamo misurando.
    """

    def __init__(self, flusso, nome):
        super().__init__(daemon=True)
        self.flusso = flusso
        self.nome = nome
        self.righe = []
        self.lucchetto = threading.Lock()

    def run(self):
        for r in self.flusso:
            r = r.rstrip("\n")
            with self.lucchetto:
                self.righe.append(r)

    def copia(self):
        with self.lucchetto:
            return list(self.righe)


def statistiche(valori):
    """Distribuzione, non campione (`LEZIONI.md` §1.4): mediana e code."""
    if not valori:
        return None
    v = sorted(valori)
    def q(p):
        i = min(len(v) - 1, max(0, int(round(p * (len(v) - 1)))))
        return v[i]
    return {
        "quanti": len(v),
        "minimo": v[0],
        "p5": q(0.05), "p25": q(0.25),
        "mediana": statistics.median(v),
        "p75": q(0.75), "p95": q(0.95), "p99": q(0.99),
        "massimo": v[-1],
        "media": statistics.fmean(v),
    }


class Banco:
    def __init__(self, opzioni):
        self.o = opzioni
        self.esiti = []
        self.percorso_esiti = os.path.join(QUI, nome_esiti(opzioni))
        self.registro_mutter = "/run/user/1000/mutter.log"
        self.mutter_offset = 0
        from gi.repository import Gio, GLib  # noqa
        self.Gio, self.GLib = Gio, GLib
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.ctx = GLib.MainContext.default()

    # -- D-Bus ------------------------------------------------------------
    def stato_monitor(self):
        v = self.bus.call_sync("org.gnome.Mutter.DisplayConfig",
                               "/org/gnome/Mutter/DisplayConfig",
                               "org.gnome.Mutter.DisplayConfig", "GetCurrentState",
                               None, None, self.Gio.DBusCallFlags.NONE, 15000, None)
        seriale_stato, monitor, logici, _ = v.unpack()
        fuori = {}
        for (connettore, marca, prodotto, seriale), modi, _p in monitor:
            corrente = None
            for m in modi:
                if m[6].get("is-current"):
                    corrente = {"larghezza": m[1], "altezza": m[2], "refresh": round(m[3], 3)}
            fuori[connettore] = {"connettore": connettore, "prodotto": prodotto,
                                 "seriale": seriale, "modo": corrente, "posizione": None}
        for x, y, _s, _t, _pri, mons, _p in logici:
            for (connettore, _v, _pr, _se) in mons:
                if connettore in fuori:
                    fuori[connettore]["posizione"] = [x, y]
        return {"seriale_stato": seriale_stato, "monitor": fuori}

    # -- mutter.log -------------------------------------------------------
    def mutter_segna(self):
        try:
            self.mutter_offset = os.path.getsize(self.registro_mutter)
        except OSError:
            self.mutter_offset = 0

    def mutter_nuove(self):
        """⛔ «vuoto» e «proibito» non devono avere lo stesso aspetto (§1.9)."""
        try:
            with open(self.registro_mutter, "rb") as f:
                f.seek(self.mutter_offset)
                dati = f.read()
            self.mutter_offset += len(dati)
            righe = [r for r in dati.decode("utf-8", "replace").splitlines() if r.strip()]
            return {"leggibile": True, "righe": righe}
        except OSError as e:
            return {"leggibile": False, "errore": str(e), "righe": []}

    # -- la sessione ------------------------------------------------------
    def verifica_sessione(self):
        log("1. La sessione GNOME: si dichiara E si verifica (§1.2), e NON si tocca")
        pid = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "gnome-shell"],
                             capture_output=True, text=True).stdout.split()
        if not pid:
            att("nessun gnome-shell: la accendo con 00-sessione-gnome.sh")
            r = subprocess.run(["bash", os.path.join(QUI, "00-sessione-gnome.sh"), "avvia"],
                               capture_output=True, text=True)
            print(r.stdout)
            pid = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "gnome-shell"],
                                 capture_output=True, text=True).stdout.split()
            if not pid:
                ko("⛔ la sessione non parte: mi fermo")
                sys.exit(3)
        try:
            with open("/proc/%s/cmdline" % pid[0], "rb") as f:
                riga = f.read().replace(b"\0", b" ").decode()
        except OSError as e:
            ko("⛔ non leggo /proc/%s/cmdline: %s — lettura NEGATA, non vuota (§1.9)" % (pid[0], e))
            sys.exit(3)
        ok("gnome-shell pid %s: %s" % (pid[0], riga.strip()))
        headless = "--headless" in riga
        (ok if headless else att)("headless: %s" % ("SI, ed e' CHIESTO" if headless else
                                                    "non chiesto sulla riga di comando"))
        tela = "1920x1080" in riga
        (ok if tela else att)("tela della sessione 1920x1080: %s" % ("si" if tela else "NO"))
        return {"pid": pid[0], "riga": riga.strip(), "headless": headless, "tela_1920x1080": tela}

    def porte_altrui(self):
        u = subprocess.run(["ss", "-tuln"], capture_output=True, text=True).stdout
        return {p: u.count(":%d " % p) for p in PORTE_ALTRUI}

    # -- una sessione di cattura -----------------------------------------
    def apri_cattura(self, cadenza):
        """CreateSession + RecordVirtual + Start, e si aspetta il node id."""
        v = self.bus.call_sync("org.gnome.Mutter.ScreenCast", "/org/gnome/Mutter/ScreenCast",
                               "org.gnome.Mutter.ScreenCast", "CreateSession",
                               self.GLib.Variant("(a{sv})", ({},)), None,
                               self.Gio.DBusCallFlags.NONE, 15000, None)
        sessione = v.unpack()[0]
        v = self.bus.call_sync("org.gnome.Mutter.ScreenCast", sessione,
                               "org.gnome.Mutter.ScreenCast.Session", "RecordVirtual",
                               self.GLib.Variant("(a{sv})", ({"cursor-mode": self.GLib.Variant("u", 0)},)),
                               None, self.Gio.DBusCallFlags.NONE, 15000, None)
        flusso = v.unpack()[0]

        nodo = {}

        def su_segnale(_c, _m, _p, _i, _s, parametri):
            nodo["id"] = parametri.unpack()[0]

        iscrizione = self.bus.signal_subscribe(
            None, "org.gnome.Mutter.ScreenCast.Stream", "PipeWireStreamAdded", flusso,
            None, self.Gio.DBusSignalFlags.NONE, su_segnale)

        self.bus.call_sync("org.gnome.Mutter.ScreenCast", sessione,
                           "org.gnome.Mutter.ScreenCast.Session", "Start", None, None,
                           self.Gio.DBusCallFlags.NONE, 15000, None)
        scadenza = time.monotonic() + 10
        while "id" not in nodo and time.monotonic() < scadenza:
            self.ctx.iteration(False)
            time.sleep(0.01)
        self.bus.signal_unsubscribe(iscrizione)
        if "id" not in nodo:
            ko("⛔ nessun PipeWireStreamAdded entro 10 s")
            self.chiudi_cattura(sessione)
            return None
        ok("sessione %s · flusso %s · nodo PipeWire %d" % (sessione.split("/")[-1],
                                                          flusso.split("/")[-1], nodo["id"]))
        return {"sessione": sessione, "flusso": flusso, "nodo": nodo["id"], "cadenza": cadenza}

    def chiudi_cattura(self, sessione):
        try:
            self.bus.call_sync("org.gnome.Mutter.ScreenCast", sessione,
                               "org.gnome.Mutter.ScreenCast.Session", "Stop", None, None,
                               self.Gio.DBusCallFlags.NONE, 10000, None)
        except Exception:
            pass


# ---------------------------------------------------------------------------
#  Lettura delle righe dei due strumenti
# ---------------------------------------------------------------------------
def fotogrammi(righe):
    """Le righe `f <us> <seq> <cambiato>` del metro."""
    fuori = []
    for r in righe:
        p = r.split()
        if len(p) >= 4 and p[0] == "f":
            fuori.append((int(p[1]), int(p[2]), int(p[3])))
    return fuori


def disegni(righe):
    """Le righe `D <us>` della scena."""
    return [int(r.split()[1]) for r in righe if r.startswith("D ")]


def formati(righe):
    """Le righe `n <us> LxA max=n/d ...` del metro: che cosa e' stato FISSATO."""
    fuori = []
    for r in righe:
        p = r.split()
        if len(p) >= 4 and p[0] == "n":
            massimo = p[3].split("=")[1]
            num, den = massimo.split("/")
            fuori.append({"us": int(p[1]), "misura": p[2],
                          "max_framerate": (int(num) / int(den)) if int(den) else 0.0,
                          "riga": r})
    return fuori


def finestra(campioni, da_us, a_us):
    return [c for c in campioni if da_us <= c <= a_us]


# ---------------------------------------------------------------------------
#  La scena dello step 2, letta dal suo blocco condiviso
# ---------------------------------------------------------------------------
# ⛔ NON si reimplementa il lettore: si importa quello dello step 2
#    (`03-marca.py`), che sa la struttura e fa il seqlock.  Riscriverlo qui
#    vorrebbe dire due lettori della stessa struttura, e quello che invecchia
#    sbaglia in silenzio (`CODER.md` §4.1: dipendere, non riscrivere).
# ⛔ E il blocco ha un NOME NOSTRO: due banchi in parallelo sullo stesso
#    `/dev/shm` si leggono i conti a vicenda.
NOME_SHM = "remotix-scena-b14-7601"


_marca_step2 = None


def carica_marca_step2():
    """Importa `03-marca.py` dello step 2, UNA volta.

    ⛔ `03-marca.py` importa `numpy` a livello di modulo — gli serve per LEGGERE
       LA MARCA dai pixel, che a noi non serve: noi usiamo solo
       `leggi_conteggio`, che fa `mmap` e `struct`.  E su NIC-OS numpy non c'e'.

    ⇒ Si mette un TAPPO al posto di numpy invece di toccare il file di un altro
      gruppo.  ⚠ E il tappo si dichiara: da qui in poi, in questo processo,
      `03-marca.py` puo' contare ma **non puo' leggere la marca**.  Se qualcuno
      ci provasse, il tappo lo fa fallire con un errore chiaro invece di
      restituire numeri finti.
    """
    global _marca_step2
    if _marca_step2 is not None:
        return _marca_step2
    import importlib.util
    percorso = os.path.join(QUI, "03-marca.py")
    if not os.path.exists(percorso):
        return None
    try:
        import numpy  # noqa: F401
    except ImportError:
        import types

        class _Tappo:
            def __getattr__(self, nome):
                raise RuntimeError(
                    "⛔ numpy non c'e' su questa macchina: `03-marca.py` puo' CONTARE "
                    "(leggi_conteggio) ma non puo' leggere la marca dai pixel.  "
                    "Chiesto «numpy.%s»." % nome)

            def array(self, *a, **k):
                return None

            float64 = uint8 = staticmethod(lambda *a, **k: None)

        finto = types.ModuleType("numpy")
        finto.__dict__.update({k: getattr(_Tappo(), k, None)
                               for k in ("array", "float64", "uint8")})
        finto.array = lambda *a, **k: None
        finto.float64 = float
        finto.uint8 = int
        sys.modules["numpy"] = finto
        att("⚠ numpy assente: 03-marca.py caricato col tappo — conta si', legge la marca no")
    spec = importlib.util.spec_from_file_location("marca_step2", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    _marca_step2 = modulo
    return modulo


def leggi_conteggio_step2():
    modulo = carica_marca_step2()
    if modulo is None:
        return {"c_e": False,
                "perche": "⛔ manca %s: non e' «zero disegni», e' «non lo so»"
                          % os.path.join(QUI, "03-marca.py")}
    return modulo.leggi_conteggio(NOME_SHM)


def delta_step2(prima, dopo, durata_s):
    """I quattro conti dello step 2, presi per differenza sulla finestra."""
    if not (prima and dopo and prima.get("c_e") and dopo.get("c_e")):
        return {"step2": {"c_e": False,
                          "perche": (dopo or prima or {}).get("perche", "conteggio assente")}}
    d = {k: dopo[k] - prima[k] for k in ("disegni", "commit", "presentati", "attese",
                                         "scarti_presentazione")}
    # ⛔ UN CONTATORE CHE TORNA INDIETRO NON E' UNA MISURA NEGATIVA: e' una
    #    scena RIPARTITA, che ha azzerato il blocco condiviso sotto di noi.
    #    Visto il 13 agosto 2026: `disegni -151`.  Senza questo controllo, un
    #    -151 sarebbe entrato in tabella come «−6 fotogrammi al secondo».
    if any(v < 0 for v in d.values()) or dopo.get("pid") != prima.get("pid"):
        return {"step2": {"c_e": False,
                          "perche": "⛔ il contatore e' tornato indietro (%s) o il pid e' "
                                    "cambiato (%s→%s): la scena e' ripartita dentro la "
                                    "finestra, e questa cella non si spende"
                                    % (d, prima.get("pid"), dopo.get("pid"))},
                "scena_ripartita": True}
    fuori = {"step2": {"c_e": True, "movimento": dopo.get("movimento"),
                       "danno": dopo.get("danno"),
                       "presentazione_disponibile": dopo["presentazione_disponibile"],
                       "uscita_confermata": dopo.get("uscita_confermata")}}
    fuori["step2"].update(d)
    if durata_s > 0:
        for k in ("disegni", "commit", "presentati"):
            fuori["step2"][k + "_fps"] = round(d[k] / durata_s, 2)
    # ⛔ I disegni della scena, per il confronto con la mia, vengono da QUI
    #    quando la scena e' quella dello step 2.
    fuori["disegni_scena"] = d["disegni"]
    fuori["disegni_scena_fps"] = round(d["disegni"] / durata_s, 2) if durata_s > 0 else None
    return fuori


def analizza(metro_righe, scena_righe, da_us, a_us):
    f = [c for c in fotogrammi(metro_righe) if da_us <= c[0] <= a_us]
    d = finestra(disegni(scena_righe), da_us, a_us)
    durata = (a_us - da_us) / 1e6
    intervalli = [(f[i][0] - f[i - 1][0]) / 1000.0 for i in range(1, len(f))]   # ms
    intervalli_d = [(d[i] - d[i - 1]) / 1000.0 for i in range(1, len(d))]
    cambiati = sum(1 for c in f if c[2] == 1)
    uguali = sum(1 for c in f if c[2] == 0)
    return {
        "durata_s": round(durata, 3),
        "consegnati": len(f),
        "consegnati_fps": round(len(f) / durata, 2) if durata > 0 else None,
        "consegnati_fps_da_mediana": round(1000.0 / statistics.median(intervalli), 2)
                                     if intervalli else None,
        "intervalli_ms": {k: round(v, 3) for k, v in statistiche(intervalli).items()}
                         if intervalli else None,
        "fotogrammi_diversi_dal_precedente": cambiati,
        "fotogrammi_uguali_al_precedente": uguali,
        "disegni_scena": len(d),
        "disegni_scena_fps": round(len(d) / durata, 2) if durata > 0 else None,
        "disegni_intervalli_ms": {k: round(v, 3) for k, v in statistiche(intervalli_d).items()}
                                 if intervalli_d else None,
    }


# ---------------------------------------------------------------------------
#  Il giro
# ---------------------------------------------------------------------------
def esegui(o):
    banco = Banco(o)
    sessione = banco.verifica_sessione()
    porte_prima = banco.porte_altrui()
    inf("porte altrui prima: " + " · ".join("%d:%d" % (k, v) for k, v in porte_prima.items()))

    base = banco.stato_monitor()
    inf("monitor gia' sullo stage: " + ", ".join(
        "%s(%s)@%s" % (c, m["seriale"], m["modo"]["refresh"] if m["modo"] else "?")
        for c, m in base["monitor"].items()))

    banco.esiti.append({"tipo": "terreno", "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "sessione": sessione, "porte_prima": porte_prima,
                        "monitor_prima": base["monitor"],
                        "scena": "03-b14-scena (forma di weston-simple-egl -f -o, §1.1); "
                                 "weston NON e' installato su questa macchina",
                        "buffer": "MemFd (nessun modificatore offerto)",
                        "tela": "%dx%d" % (o.larghezza, o.altezza),
                        "secondi_per_cella": o.secondi, "riscaldamento_s": o.riscaldamento})

    scarti = []
    if o.griglia:
        # ===================================================================
        # ⭐⭐ LA GRIGLIA: la legge del freno, misurata punto per punto.
        #
        # Le celle A/B/C/D dicono che il freno NON e' un tetto continuo.  Il
        # codice dice perche' `[R]`: `maybe_record_frame_with_timestamp`
        # confronta `g_get_monotonic_time()` — l'ora VERA di fine pittura,
        # jitter compreso — con `min_interval_us = 10^6 / maxFramerate`, e
        # scarta il fotogramma se e' arrivato anche di un microsecondo troppo
        # presto.  Il seguente arriva un tick INTERO dopo.
        #
        # ⇒ Previsione: con il monitor a M Hz e il freno a F, si consegnano
        #   M/N fotogrammi, dove N e' il numero INTERO di tick necessari a
        #   superare 10^6/F.  E i valori di F che cadono ESATTAMENTE su un
        #   confine (F=M/N tondo) perdono, perche' il jitter li butta di la'.
        #
        # ⛔ Una previsione scritta prima della misura: cosi' la griglia puo'
        #    smentirla.  Se ne uscisse una curva liscia, la legge sarebbe falsa.
        # ===================================================================
        tick_us = 1_000_000.0 / o.alta
        passi = []
        for f in [int(x) for x in o.griglia.split(",")]:
            minimo = 1_000_000 // f
            n = 1
            while n * tick_us < minimo:
                n += 1
            passi.append(("griglia-freno-%d" % f, f,
                          "freno %d ⇒ intervallo minimo %d µs ⇒ %d tick da %.1f µs ⇒ "
                          "previsti %.1f fps%s"
                          % (f, minimo, n, tick_us, o.alta / n,
                             "  ⚠ SUL CONFINE (%d·%.1f = %.0f ≈ %d): il jitter decide"
                             % (n, tick_us, n * tick_us, minimo)
                             if abs(n * tick_us - minimo) < 30 else "")))
        # ⛔ La cella d'apertura negozia `--alta` e NON il primo punto: il
        #    monitor deve nascere a %d Hz e restarci per TUTTA la griglia, o si
        #    misurerebbe un monitor diverso a ogni punto.
        try:
            cella(banco, base, o, "griglia-apertura-%d" % o.alta, o.alta, passi, scarti,
                  "apre il monitor a %d Hz; da qui in poi cambia solo il freno" % o.alta)
        finally:
            for s in scarti:
                banco.chiudi_cattura(s)
        scrivi_esiti(banco)
        verdetto_griglia(banco.esiti, o)
        # ⛔ L'esito nel codice d'uscita: vedi il riquadro sopra `ko()`.
        return 1 if ROSSI else 0

    try:
        # ---------------- CELLA A: negoziata bassa ----------------
        cella(banco, base, o, "A-bassa", o.bassa, [], scarti,
              "sessione nuova negoziata a %d: monitor %d Hz, freno %d — lo stato di fatto di v1"
              % (o.bassa, o.bassa, o.bassa))

        # ------- CELLE B, C e i controlli: UNA SOLA sessione -------
        passi = [
            ("B-alta", None, "la sessione nasce a %d: monitor %d Hz, freno %d" % (o.alta, o.alta, o.alta)),
            ("C-alta-rinegoziata-bassa", o.bassa,
             "⭐ L'IPOTESI: rinegoziata la SOLA cadenza a %d, misura identica, monitor fermo a %d Hz"
             % (o.bassa, o.alta)),
            ("controllo-NEGATIVO-stesso-valore", o.bassa,
             "si rinegozia %d→%d, lo stesso valore: il numero DEVE restare fermo su C"
             % (o.bassa, o.bassa)),
            ("controllo-POSITIVO-crollo", o.crollo,
             "si rinegozia a %d: il numero DEVE crollare a ~%d, o questo banco non vede il freno"
             % (o.crollo, o.crollo)),
            ("controllo-RITORNO", o.alta,
             "si rinegozia a %d: si DEVE tornare su B, o il crollo era un guasto" % o.alta),
            ("D-alta-freno-intermedio", o.intermedia,
             "⭐⭐ freno a %d con monitor a %d Hz: se il freno QUANTIZZA sui tick del monitor "
             "(e la cella C dice che lo fa), un freno strettamente fra %d e %d cade su DUE tick "
             "netti, cioe' su %d fotogrammi esatti, con margine invece che sul filo"
             % (o.intermedia, o.alta, o.bassa, o.alta, o.alta // 2)),
        ]
        cella(banco, base, o, passi[0][0], o.alta, passi[1:], scarti, passi[0][2])
    finally:
        for s in scarti:
            banco.chiudi_cattura(s)
        time.sleep(1.0)

    porte_dopo = banco.porte_altrui()
    dopo = banco.stato_monitor()
    log("Fine giro: i vicini si contano, non si sperano")
    for p in PORTE_ALTRUI:
        (ok if porte_prima[p] == porte_dopo[p] else ko)(
            "porta %d: prima %d · dopo %d" % (p, porte_prima[p], porte_dopo[p]))
    rimasti = set(dopo["monitor"]) - set(base["monitor"])
    (ok if not rimasti else ko)("monitor lasciati addosso alla macchina: %s"
                                % (", ".join(rimasti) if rimasti else "nessuno"))
    banco.esiti.append({"tipo": "chiusura", "porte_dopo": porte_dopo,
                        "monitor_dopo": dopo["monitor"], "monitor_rimasti": sorted(rimasti)})

    scrivi_esiti(banco)
    verdetto(banco.esiti, o)
    # ⛔ L'esito nel codice d'uscita: vedi il riquadro sopra `ko()`.
    return 1 if ROSSI else 0


def scrivi_esiti(banco):
    with open(banco.percorso_esiti, "w") as f:
        for e in banco.esiti:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    inf("esiti in %s" % banco.percorso_esiti)


def verdetto_griglia(esiti, o):
    """⛔ La previsione era scritta PRIMA: qui si guarda se ha retto, e dove no."""
    log("La legge del freno, punto per punto — previsto contro consegnato")
    tick_us = 1_000_000.0 / o.alta
    print("    %-8s %-12s %-6s %-10s %-10s %-8s" %
          ("freno", "min_int µs", "tick", "previsti", "consegnati", "scena"))
    giusti = sbagliati = confini = tetti = sporche = 0
    for e in esiti:
        if e.get("tipo") != "cella" or not e["cella"].startswith("griglia-freno-"):
            continue
        f = e["cadenza_chiesta"]
        minimo = 1_000_000 // f
        n = 1
        while n * tick_us < minimo:
            n += 1
        previsti = o.alta / n
        avuti = e["misura"]["consegnati_fps"]
        scena = e["misura"]["disegni_scena_fps"]
        confine = abs(n * tick_us - minimo) < 30
        vicino = avuti is not None and abs(avuti - previsti) <= max(2.0, previsti * 0.05)
        # ⛔⭐ IL PUNTO NON E' UNA PROVA DEL FRENO SE LA SCENA E' CADUTA CON LUI.
        #
        #    Quando i disegni della scena scendono sotto la cadenza del monitor,
        #    il tetto di quel punto e' del COMPOSITORE — comporre e copiare
        #    1920x1080 costa, e sopra una certa cadenza consegnata non ce la fa
        #    piu'.  Contare quei punti come «la legge sbaglia» sarebbe attribuire
        #    al freno un tetto che e' della macchina: e' la forma d'errore E1 di
        #    §1.11, e il conto dei disegni di §1.1 esiste per vederla.
        tetto_compositore = scena is not None and scena < o.alta * 0.95
        # ⛔ Sul confine la previsione NON e' verificabile: il jitter decide, e
        #    dichiararla «giusta» o «sbagliata» sarebbe barare in tutt'e due i
        #    versi.  Si conta a parte.
        if e["misura"]["consegnati"] == 0 and e["misura"]["disegni_scena"] > 0:
            segno = "⛔ CONSEGNA FERMA (zero consegnati con la scena viva: non e' un freno)"
            sporche += 1
        elif not e.get("scena_sul_mio_monitor", True):
            segno = "⛔ SCENA ALTROVE (finita su %s)" % e.get("scena_uscita_confermata")
            sporche += 1
        elif not e.get("palco_stabile", True):
            segno = "⛔ CONTAMINATA (il palco e' cambiato sotto: %s → %s)" % (
                e.get("palco_prima"), e.get("palco_dopo"))
            sporche += 1
        elif tetto_compositore:
            segno = "TETTO-COMPOSITORE (scena caduta a %.0f)" % scena
            tetti += 1
        elif confine:
            segno = "≈CONFINE (il jitter decide)"
            confini += 1
        elif vicino:
            segno = "OK"
            giusti += 1
        else:
            segno = "⛔ NO"
            sbagliati += 1
        print("    %-8d %-12d %-6d %-10.1f %-10s %-8s  %s"
              % (f, minimo, n, previsti, avuti, scena, segno))
    inf("%d punti provano la legge · %d sul confine · %d col tetto del compositore · "
        "%d contaminati · %d smentiscono" % (giusti, confini, tetti, sporche, sbagliati))
    if sbagliati == 0 and giusti > 0:
        ok("⭐⭐ LA LEGGE REGGE `[M]` su %d punti fuori dai confini: il freno di Mutter passa "
           "un fotogramma ogni N TICK INTERI del monitor, con N il piu' piccolo intero per cui "
           "N·(1/monitor) ≥ 1/freno.  Non e' un tetto, e' una griglia." % giusti)
        ok("⇒ LA REGOLA PER IL PRODOTTO: per avere T fotogrammi si nega il monitor a un multiplo "
           "di T e si chiede un freno **strettamente in mezzo** fra T e il monitor — mai T tondo, "
           "che cade sul confine e ne fa perdere un terzo.")
    else:
        ko("⛔ la legge NON regge su %d punti su %d: la spiegazione della quantizzazione va "
           "riscritta" % (sbagliati, giusti + sbagliati))
    if tetti:
        att("⚠ E %d punti non parlano del freno affatto: li' la scena e' caduta insieme ai "
            "consegnati, cioe' il tetto e' del compositore.  ⇒ su questa macchina, a 1920x1080 "
            "e con i buffer in memoria, GNOME non regge una consegna molto oltre i ~75 "
            "fotogrammi, e questo e' un tetto DIVERSO e per ora `[M]` solo su MemFd." % tetti)


def cella(banco, base, o, nome, cadenza, passi_dopo, scarti, descrizione):
    """Apre una cattura, ci mette la scena sopra, misura, e poi eventualmente
    rinegozia una o piu' volte SULLA STESSA sessione."""
    log("Cella %s — %s" % (nome, descrizione))
    banco.mutter_segna()
    # ⛔ La fotografia dei monitor si prende ADESSO, non all'inizio del giro: sul
    #    banco gira anche il prodotto dell'utente (7561), che monta e smonta
    #    monitor virtuali per conto suo.  Confrontare con una fotografia vecchia
    #    farebbe passare un monitor d'altri per il nostro.
    prima_di_aprire = banco.stato_monitor()["monitor"]
    cattura = banco.apri_cattura(cadenza)
    if not cattura:
        return
    scarti.append(cattura["sessione"])

    metro_p = subprocess.Popen(
        [os.path.join(QUI, "03-b14-metro"), "--nodo", str(cattura["nodo"]),
         "--misura", "%dx%d" % (o.larghezza, o.altezza), "--cadenza", str(cadenza)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, bufsize=1)
    metro = Lettore(metro_p.stdout, "metro")
    metro.start()

    # ⛔ Il monitor virtuale NASCE alla negoziazione, non alla Start: e'
    #    `notify_params_updated` a chiamare `ensure_virtual_monitor`.  Quindi si
    #    aspetta la riga `n` PRIMA di andare a cercare il monitor.
    scadenza = time.monotonic() + 15
    while not formati(metro.copia()) and time.monotonic() < scadenza:
        time.sleep(0.05)
    fs = formati(metro.copia())
    if not fs:
        ko("⛔ nessun formato negoziato entro 15 s: la cella non si misura")
        metro_p.kill()
        return
    ok("formato fissato: %s" % fs[-1]["riga"])
    if abs(fs[-1]["max_framerate"] - cadenza) > 0.01:
        ko("⛔ chiesto maxFramerate %d, FISSATO %.3f — il numero che segue NON e' "
           "la misura di %d (§1.8)" % (cadenza, fs[-1]["max_framerate"], cadenza))

    time.sleep(0.6)
    stato = banco.stato_monitor()
    nuovi = [c for c in stato["monitor"] if c not in prima_di_aprire]
    if len(nuovi) != 1:
        ko("⛔ mi aspettavo UN monitor nuovo, ne trovo %d (%s): non so su quale "
           "mettere la scena, e non lo indovino" % (len(nuovi), nuovi))
        metro_p.kill()
        return
    mio = stato["monitor"][nuovi[0]]
    ok("il MIO monitor: %s serial=%s %s posizione=%s"
       % (mio["connettore"], mio["seriale"], mio["modo"], mio["posizione"]))
    inf("mutter dice: " + " | ".join(banco.mutter_nuove()["righe"][-3:]))

    # ⭐ DUE SCENE, E SI CONFRONTANO INVECE DI SOMMARSI.
    #
    #    `03-b14-scena` (mia, EGL) e `03-scena` (dello step 2, wl_shm) misurano
    #    la stessa cosa per strade diverse.  Se danno lo stesso numero,
    #    l'attribuzione «il tetto e' di Mutter» e' solida; se danno numeri
    #    diversi, la differenza vale piu' di tutt'e due i numeri.
    #    ⛔ E la seconda tiene un conto che la mia NON tiene: le ATTESE, cioe'
    #       quante volte il tetto e' stato NOSTRO.  Senza quel conto, «Mutter
    #       non consegna» e «la mia scena non disegna» hanno lo stesso aspetto.
    if o.scena2:
        comando_scena = [os.path.join(QUI, "03-b14-scena2"), "--uscita", mio["connettore"],
                         "--shm", NOME_SHM, "--giro", "b14-%s" % nome]
    else:
        comando_scena = [os.path.join(QUI, "03-b14-scena"), "--uscita", mio["connettore"],
                         "--misura", "%dx%d" % (o.larghezza, o.altezza)]
    if mio["posizione"] and not o.scena2:
        # La posizione e' il ripiego per quando `wl_output` sta sotto la versione
        # 4 e non manda l'evento `name`: allora il monitor si riconosce da dove
        # sta.  Se non c'e' nemmeno quella, resta il nome — e se non basta la
        # scena esce ROSSO invece di mettersi sul primo monitor che trova.
        comando_scena += ["--posizione", "%d,%d" % (mio["posizione"][0], mio["posizione"][1])]
    scena_p = subprocess.Popen(
        comando_scena,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    scena = Lettore(scena_p.stdout, "scena")
    scena.start()
    scena_err = Lettore(scena_p.stderr, "scena-err")
    scena_err.start()

    scadenza = time.monotonic() + 15
    while time.monotonic() < scadenza:
        if o.scena2:
            c = leggi_conteggio_step2()
            if c.get("c_e") and c.get("uscita_confermata"):
                break
        elif any(r.startswith("E ") for r in scena.copia()):
            break
        if scena_p.poll() is not None:
            break
        time.sleep(0.05)

    if o.scena2:
        c = leggi_conteggio_step2()
        if not c.get("c_e") or not c.get("uscita_confermata"):
            ko("⛔ la scena dello step 2 non conferma nessuna uscita: %s | %s"
               % (c.get("perche", ""), " | ".join(scena_err.copia()[-4:])))
            scena_p.kill(); metro_p.kill()
            return
        ok("la scena (step 2, wl_shm) e' su: %s  (lo dice wl_surface.enter) · "
           "presentazione %s" % (c["uscita_confermata"],
                                 "disponibile" if c["presentazione_disponibile"]
                                 else "NON misurabile"))
    else:
        entrate = [r for r in scena.copia() if r.startswith("E ")]
        if not entrate:
            ko("⛔ la scena non e' entrata su nessun monitor: %s"
               % " | ".join(scena_err.copia()[-4:]))
            scena_p.kill(); metro_p.kill()
            return
        ok("la scena (mia, EGL) e' su: %s  (lo dice wl_surface.enter, non la nostra intenzione)"
           % entrate[-1])
        disp = [r for r in scena.copia() if r.startswith("R ")]
        if disp:
            inf("chi disegna la scena: %s" % disp[-1])

    misura = [(nome, cadenza, None)] + [(n, c, c) for n, c, _d in passi_dopo]
    descrizioni = {nome: descrizione}
    for n, _c, d in passi_dopo:
        descrizioni[n] = d

    monitor_precedente = dict(mio)
    for etichetta, cad, rinegozia_a in misura:
        rinegoziazione = None
        if rinegozia_a is not None:
            log("Cella %s — %s" % (etichetta, descrizioni[etichetta]))
            banco.mutter_segna()
            prima = banco.stato_monitor()["monitor"].get(mio["connettore"])
            metro_p.stdin.write("R %d\n" % rinegozia_a)
            metro_p.stdin.flush()
            quanti_formati = len(formati(metro.copia()))
            scadenza = time.monotonic() + 10
            while len(formati(metro.copia())) == quanti_formati and time.monotonic() < scadenza:
                time.sleep(0.05)
            fs = formati(metro.copia())
            if len(fs) == quanti_formati:
                ko("⛔ `pw_stream_update_params` NON ha prodotto una rinegoziazione entro 10 s: "
                   "ripiego su stacca-e-riattacca, e lo dichiaro")
                metro_p.stdin.write("C %d\n" % rinegozia_a)
                metro_p.stdin.flush()
                scadenza = time.monotonic() + 10
                while len(formati(metro.copia())) == quanti_formati and time.monotonic() < scadenza:
                    time.sleep(0.05)
                fs = formati(metro.copia())
                if len(fs) == quanti_formati:
                    ko("⛔ nemmeno stacca-e-riattacca rinegozia: cella saltata")
                    continue
            ok("formato rifissato: %s" % fs[-1]["riga"])
            if abs(fs[-1]["max_framerate"] - rinegozia_a) > 0.01:
                ko("⛔ chiesto %d, FISSATO %.3f: il numero che segue non e' quel che dice"
                   % (rinegozia_a, fs[-1]["max_framerate"]))
            time.sleep(0.6)
            dopo = banco.stato_monitor()["monitor"].get(mio["connettore"])
            righe_mutter = banco.mutter_nuove()
            fermo = (dopo is not None and prima is not None
                     and dopo["seriale"] == prima["seriale"]
                     and dopo["modo"] == prima["modo"])
            sporche = [r for r in righe_mutter["righe"]
                       if "virtual monitor" in r.lower()]
            (ok if fermo else ko)(
                "⭐ il monitor NON si e' ricreato: serial %s→%s, modo %s→%s"
                % (prima["seriale"] if prima else "?", dopo["seriale"] if dopo else "SPARITO",
                   prima["modo"] if prima else "?", dopo["modo"] if dopo else "?"))
            (ok if not sporche else ko)(
                "mutter.log durante la rinegoziazione: %s"
                % (" | ".join(sporche) if sporche else "nessuna riga su monitor virtuali"))
            if not righe_mutter["leggibile"]:
                att("⚠ mutter.log NON leggibile (%s): «vuoto» e «proibito» non sono la stessa "
                    "cosa (§1.9), quindi questa mezza prova NON conta"
                    % righe_mutter.get("errore"))
            rinegoziazione = {
                "da": monitor_precedente["modo"], "a_cadenza": rinegozia_a,
                "monitor_prima": prima, "monitor_dopo": dopo,
                "monitor_fermo": fermo,
                "mutter_log_leggibile": righe_mutter["leggibile"],
                "mutter_log_righe": righe_mutter["righe"],
                "mutter_log_righe_su_monitor_virtuali": sporche,
                "formato_fissato": fs[-1]["riga"],
                "max_framerate_fissato": fs[-1]["max_framerate"],
            }
            cad = rinegozia_a

        inf("riscaldamento %ds, poi %ds a regime (§1.4: un campione all'avvio non dice "
            "niente del regime)" % (o.riscaldamento, o.secondi))
        time.sleep(o.riscaldamento)
        # ⛔⭐ IL PALCO SI FOTOGRAFA PRIMA E DOPO LA FINESTRA.
        #
        #    Su questa macchina gira anche il prodotto dell'utente (7561), che
        #    monta e smonta monitor virtuali suoi quando gli pare.  Il 13 agosto
        #    2026 un «Added virtual monitor Meta-3» comparso a meta' finestra ha
        #    azzerato i fotogrammi di due punti della griglia, e senza questo
        #    controllo sarebbero entrati nella tabella come se fossero una
        #    misura del freno.  Un numero preso mentre il palco cambia sotto non
        #    e' una misura: e' un incidente con un'etichetta addosso.
        # ⛔⛔ E NON BASTA CONFRONTARE I DUE ESTREMI.
        #
        #    Il 13 agosto 2026, alle 09:42:01, il prodotto dell'utente ha
        #    SMONTATO e RIMONTATO il proprio Meta-3 dentro una nostra finestra.
        #    Agli estremi l'elenco dei monitor era identico — e la nostra
        #    consegna era andata a ZERO senza un solo errore.  Un confronto fra
        #    due fotografie non vede quel che succede fra le due: per quello
        #    ci vuole il registro, cioe' CHIEDERE a Mutter (§1.6).
        banco.mutter_nuove()                       # si allinea: si butta il pregresso
        palco_prima = {c: m["seriale"] for c, m in banco.stato_monitor()["monitor"].items()}
        conteggio_prima = leggi_conteggio_step2() if o.scena2 else None
        metro_p.stdin.write("M inizio-%s\n" % etichetta)
        metro_p.stdin.flush()
        da_us = ora_us()
        time.sleep(o.secondi)
        metro_p.stdin.write("M fine-%s\n" % etichetta)
        metro_p.stdin.flush()
        a_us = ora_us()
        conteggio_dopo = leggi_conteggio_step2() if o.scena2 else None
        # ⛔ §1.9 di nuovo: «zero disegni» e «la scena e' morta» hanno lo stesso
        #    aspetto nel conteggio.  Si guarda lo stato d'uscita e lo stderr —
        #    cioe' si CHIEDE al processo perche' non c'e' piu'.
        uscita_scena = scena_p.poll()
        if uscita_scena is not None:
            ko("⛔ LA SCENA E' MORTA durante la cella (uscita %d).  Ultimo stderr: %s"
               % (uscita_scena, " | ".join(scena_err.copia()[-6:]) or "(niente)"))
        palco_dopo = {c: m["seriale"] for c, m in banco.stato_monitor()["monitor"].items()}
        mutter_finestra = banco.mutter_nuove()
        mosse = [r for r in mutter_finestra["righe"] if "virtual monitor" in r.lower()]
        palco_stabile = (palco_prima == palco_dopo and not mosse
                         and mutter_finestra["leggibile"])
        if not palco_stabile:
            ko("⛔ IL PALCO E' CAMBIATO SOTTO LA MISURA — questa cella NON e' una misura del "
               "freno.  Estremi: %s → %s.  Registro di Mutter durante la finestra: %s"
               % (palco_prima, palco_dopo, " | ".join(mosse) if mosse
                  else ("NON LEGGIBILE: " + str(mutter_finestra.get("errore")))))

        # ⛔ Gli estremi si prendono dai MARCATORI del metro, non dall'ora di
        #    questo processo: il metro e la scena scrivono nello stesso
        #    CLOCK_MONOTONIC, e questo processo pure — ma i marcatori sono
        #    dentro il ciclo che consegna i fotogrammi, e sono quelli buoni.
        marcatori = {}
        for r in metro.copia():
            p = r.split()
            if len(p) >= 3 and p[0] == "m" and p[2].startswith(("inizio-", "fine-")):
                marcatori[p[2]] = int(p[1])
        da_us = marcatori.get("inizio-%s" % etichetta, da_us)
        a_us = marcatori.get("fine-%s" % etichetta, a_us)

        righe_metro = metro.copia()
        righe_scena = scena.copia()
        # ⛔⭐ DOV'E' LA SCENA ADESSO — non dov'era quando e' partita.
        #
        #    Quando il palco cambia, Mutter puo' SPOSTARE la finestra a schermo
        #    intero su un altro monitor.  Il nostro resta fermo, e un monitor
        #    fermo non consegna niente: zero fotogrammi, nessun errore, e la
        #    scena che continua tranquillamente a disegnare — sull'altro.
        #    ⛔ E' la forma peggiore del difetto, perche' ogni singolo pezzo
        #       sembra sano.  `wl_surface.enter`/`leave` lo dicono (§1.7), e
        #       vanno letti a OGNI cella, non solo all'avvio.
        entrate_scena = [r for r in righe_scena if r[:1] in ("E", "L")]
        ultima_entrata = None
        if o.scena2:
            ultima_entrata = (conteggio_dopo or {}).get("uscita_confermata")
        else:
            for r in entrate_scena:
                p = r.split()
                if p[0] == "E" and int(p[1]) <= a_us and len(p) > 2:
                    ultima_entrata = p[2]
        scena_sul_mio = (ultima_entrata == mio["connettore"])
        if not scena_sul_mio:
            ko("⛔ LA SCENA NON E' PIU' SUL MIO MONITOR: l'ultimo wl_surface.enter dice «%s», "
               "il mio e' «%s».  Un monitor senza scena non consegna: questa cella NON e' una "
               "misura del freno." % (ultima_entrata, mio["connettore"]))
        risultato = analizza(righe_metro, righe_scena, da_us, a_us)
        if o.scena2:
            risultato["scena"] = "03-scena (step 2, wl_shm + presentation-time)"
            risultato.update(delta_step2(conteggio_prima, conteggio_dopo, risultato["durata_s"]))
        else:
            risultato["scena"] = "03-b14-scena (mia, EGL + frame callback)"
        stampa_cella(etichetta, cad, risultato, mio)
        # I cambi di stato e gli errori del flusso, dentro la finestra: quando un
        # numero viene zero, questi dicono se e' «zero» o «guasto» (§1.9).
        notevoli = [r for r in righe_metro
                    if r[:1] in ("s", "e") and len(r.split()) > 1
                    and r.split()[1].isdigit() and da_us <= int(r.split()[1]) <= a_us]
        banco.esiti.append({
            "tipo": "cella", "cella": etichetta, "descrizione": descrizioni[etichetta],
            "cadenza_chiesta": cad, "marca": "[M]",
            "monitor": mio, "monitor_refresh_durante": (
                banco.stato_monitor()["monitor"].get(mio["connettore"], {}).get("modo")),
            "rinegoziazione": rinegoziazione,
            "finestra_us": [da_us, a_us],
            "palco_prima": palco_prima, "palco_dopo": palco_dopo,
            "palco_stabile": palco_stabile,
            "scena_viva": uscita_scena is None,
            "scena_uscita": uscita_scena,
            "scena_stderr": scena_err.copia()[-10:],
            "scena_sul_mio_monitor": scena_sul_mio,
            "scena_uscita_confermata": ultima_entrata,
            "scena_entrate_e_uscite": entrate_scena,
            "mutter_log_nella_finestra": mutter_finestra["righe"],
            "righe_metro_notevoli": notevoli,
            "misura": risultato,
        })
        monitor_precedente = dict(mio)

    try:
        metro_p.stdin.write("Q\n")
        metro_p.stdin.flush()
    except Exception:
        pass
    scena_p.terminate()
    try:
        metro_p.wait(timeout=5)
    except Exception:
        metro_p.kill()
    try:
        scena_p.wait(timeout=5)
    except Exception:
        scena_p.kill()
    banco.chiudi_cattura(cattura["sessione"])
    if cattura["sessione"] in scarti:
        scarti.remove(cattura["sessione"])
    time.sleep(0.8)


def stampa_cella(nome, cadenza, r, monitor):
    i = r["intervalli_ms"]
    print("    ┌─ %s — chiesti %s fps, monitor %s Hz" % (
        nome, cadenza, monitor["modo"]["refresh"] if monitor["modo"] else "?"))
    print("    │  CONSEGNATI  %d in %.1f s = %s fps  (dalla mediana: %s fps)" % (
        r["consegnati"], r["durata_s"], r["consegnati_fps"], r["consegnati_fps_da_mediana"]))
    if i:
        print("    │  intervalli  mediana %.2f ms · p5 %.2f · p25 %.2f · p75 %.2f · p95 %.2f · "
              "p99 %.2f · max %.2f" % (i["mediana"], i["p5"], i["p25"], i["p75"], i["p95"],
                                       i["p99"], i["massimo"]))
    # ⚠ L'impronta e' a CAMPIONE (64 punti sparsi): con una scena a danno
    #   piccolo — la barra dello step 2 — puo' non toccare mai il pixel che
    #   cambia, e allora dice «uguale» a fotogrammi che uguali non sono.
    #   ⇒ Il numero e' un indizio sulla scena a schermo pieno, NON una prova
    #     che il fotogramma sia stantio.  Con `--scena2` non si legge affatto.
    print("    │  diversi dal precedente: %d · uguali: %d%s"
          % (r["fotogrammi_diversi_dal_precedente"], r["fotogrammi_uguali_al_precedente"],
             "   ⚠ impronta a campione: con una scena a danno piccolo non fa fede"
             if r.get("step2") else ""))
    print("    └─ DISEGNI DELLA SCENA %d = %s fps  ⇐ il controllo di §1.1  [%s]"
          % (r["disegni_scena"], r["disegni_scena_fps"], r.get("scena", "?")))
    s2 = r.get("step2")
    if s2 and s2.get("c_e"):
        # ⭐ Il conto che la mia scena NON tiene: le ATTESE dicono quante volte
        #    il tetto e' stato NOSTRO invece che di Mutter.
        print("       step 2: disegni %s · commit %s · presentati %s · ⭐ ATTESE %s · "
              "scarti %s  (movimento %s, danno %s)"
              % (s2["disegni"], s2["commit"],
                 s2["presentati"] if s2["presentazione_disponibile"] else "NON MISURABILI",
                 s2["attese"], s2["scarti_presentazione"], s2.get("movimento"),
                 s2.get("danno")))
        if s2["attese"] == 0:
            ok("⭐ ZERO attese: in questa cella il tetto NON e' mai stato della scena. "
               "Quel che manca ai fotogrammi consegnati e' di Mutter.")
        else:
            att("⚠ %d attese: %d volte il tetto e' stato NOSTRO, non di Mutter — e allora "
                "questo numero non e' tutto suo." % (s2["attese"], s2["attese"]))
    # ⛔ §1.9: una misura che puo' dire «zero» deve distinguere lo zero dal
    #    guasto.  Zero fotogrammi mentre la scena disegna NON e' «il freno vale
    #    zero»: e' un flusso che ha smesso di consegnare, e va detto forte.
    if r["consegnati"] == 0 and r["disegni_scena"] > 0:
        ko("⛔ ZERO fotogrammi consegnati mentre la scena ne disegnava %d: questo non e' un "
           "freno a zero, e' una consegna che si e' fermata.  La cella NON si spende."
           % r["disegni_scena"])


def verdetto(esiti, o):
    log("Verdetto — e i due esiti valgono uguale")
    celle = {e["cella"]: e for e in esiti if e.get("tipo") == "cella"}

    def fps(n):
        return celle[n]["misura"]["consegnati_fps"] if n in celle else None

    a = fps("A-bassa")
    b = fps("B-alta")
    c = fps("C-alta-rinegoziata-bassa")
    d = fps("D-alta-freno-intermedio")
    neg = fps("controllo-NEGATIVO-stesso-valore")
    pos = fps("controllo-POSITIVO-crollo")
    rit = fps("controllo-RITORNO")

    def disegni_di(n):
        return celle[n]["misura"]["disegni_scena_fps"] if n in celle else None

    inf("A  monitor %3d Hz · freno %3d = %s fps consegnati  (scena %s)"
        % (o.bassa, o.bassa, a, disegni_di("A-bassa")))
    inf("B  monitor %3d Hz · freno %3d = %s fps consegnati  (scena %s)"
        % (o.alta, o.alta, b, disegni_di("B-alta")))
    inf("C  monitor %3d Hz · freno %3d = %s fps consegnati  (scena %s)   ⭐ l'ipotesi"
        % (o.alta, o.bassa, c, disegni_di("C-alta-rinegoziata-bassa")))
    inf("D  monitor %3d Hz · freno %3d = %s fps consegnati  (scena %s)   ⭐⭐ la quantizzazione"
        % (o.alta, o.intermedia, d, disegni_di("D-alta-freno-intermedio")))
    inf("controllo positivo (→%d) = %s fps" % (o.crollo, pos))
    inf("controllo negativo (%d→%d) = %s fps" % (o.bassa, o.bassa, neg))
    inf("controllo di ritorno (→%d) = %s fps" % (o.alta, rit))

    banco_valido = True
    if pos is None or abs(pos - o.crollo) > max(2.0, o.crollo * 0.25):
        ko("⛔ CONTROLLO POSITIVO FALLITO: chiesti %d, consegnati %s. Questo strumento non "
           "vede il freno, quindi NESSUNA delle tre celle vuol dire qualcosa." % (o.crollo, pos))
        banco_valido = False
    else:
        ok("controllo positivo: il numero si muove quando deve (%s ≈ %d)" % (pos, o.crollo))
    if c is not None and neg is not None:
        if abs(neg - c) > max(2.0, c * 0.08):
            ko("⛔ CONTROLLO NEGATIVO FALLITO: rinegoziare %d→%d ha spostato il numero da %s a "
               "%s. Allora quel che C guadagna e' l'ATTO di rinegoziare, non la cadenza "
               "disaccoppiata." % (o.bassa, o.bassa, c, neg))
            banco_valido = False
        else:
            ok("controllo negativo: rinegoziare a vuoto NON muove il numero (%s vs %s)" % (c, neg))
    fermi = [e["rinegoziazione"]["monitor_fermo"] for e in esiti
             if e.get("tipo") == "cella" and e.get("rinegoziazione")]
    if fermi and all(fermi):
        ok("⭐ il monitor virtuale non si e' MAI ricreato in %d rinegoziazioni" % len(fermi))
    elif fermi:
        ko("⛔ il monitor si e' mosso in %d rinegoziazioni su %d: l'esperimento non ha provato "
           "quel che dice di provare" % (sum(1 for f in fermi if not f), len(fermi)))
        banco_valido = False

    if not banco_valido:
        ko("⛔ IL BANCO NON E' CERTIFICATO (§1.2): i numeri sopra NON si spendono.")
        return

    if c is None or a is None:
        ko("⛔ celle mancanti: nessun verdetto")
        return

    # 1. L'ipotesi come e' scritta nei documenti: negoziare alto, rinegoziare
    #    la sola cadenza AL VALORE VOLUTO.
    if c >= o.bassa * 0.95:
        ok("✅ L'IPOTESI REGGE COSI' COM'E' SCRITTA `[M]`: negoziando %d e rinegoziando la sola "
           "cadenza a %d, GNOME consegna %s fps invece dei %s di prima (%.2f volte)."
           % (o.alta, o.bassa, c, a, c / a if a else 0))
    elif c > a * 1.15:
        att("⚠ L'IPOTESI MUOVE IL NUMERO MA NON ARRIVA, COSI' COM'E' SCRITTA `[M]`: da %s a %s "
            "fps (%.2f volte), e il traguardo era %d.  Il monitor sta fermo, il freno si muove — "
            "ma chiedere esattamente %d NON da' %d." % (a, c, c / a if a else 0, o.bassa,
                                                        o.bassa, o.bassa))
    else:
        ko("⛔ L'IPOTESI NON REGGE `[M]`: rinegoziare la sola cadenza a monitor fermo lascia il "
           "numero a %s fps contro i %s di partenza." % (c, a))

    # 2. ⭐⭐ Quel che le celle dicono OLTRE l'ipotesi: il freno non e' un
    #    limite continuo, e' una GRIGLIA sui tick del monitor.
    if d is not None:
        if d >= o.bassa * 0.97:
            ok("⭐⭐ E LA CURA C'E' `[M]`, ma non e' quella scritta: il freno NON e' un tetto "
               "continuo, e' una griglia — passa un fotogramma ogni N tick interi del monitor. "
               "Chiedere %d con il monitor a %d cade SUL FILO del secondo tick; chiedere %d cade "
               "in MEZZO, e allora ne arrivano %s, cioe' %d netti. ⇒ GNOME entra nei %d "
               "fotogrammi." % (o.bassa, o.alta, o.intermedia, d, o.alta // 2, o.bassa))
        else:
            ko("⛔ nemmeno il freno intermedio (%d con monitor %d) porta ai %d: %s fps `[M]`"
               % (o.intermedia, o.alta, o.bassa, d))

    # 3. Il tetto della cella B non e' il freno: se la scena e i consegnati
    #    scendono INSIEME, il tetto e' del compositore (§1.1).
    if b is not None and "B-alta" in celle:
        sb = celle["B-alta"]["misura"]["disegni_scena_fps"]
        if sb is not None and abs(sb - b) < max(3.0, b * 0.05) and b < o.alta * 0.9:
            att("⚠ E la cella B non misura il freno: scena %s e consegnati %s scendono INSIEME "
                "sotto i %d chiesti ⇒ il tetto li' e' del COMPOSITORE (comporre + copiare "
                "1920x1080 in MemFd), non della cadenza.  E' esattamente il controllo di §1.1: "
                "senza il conto dei disegni si sarebbe scritto «il freno si ferma a %s»."
                % (sb, b, o.alta, b))


def main():
    p = argparse.ArgumentParser(description="B14 — la cadenza disaccoppiata (misura M3)")
    p.add_argument("--qui", action="store_true", help="gira su questa macchina (il server)")
    p.add_argument("--bassa", type=int, default=60, help="la cadenza «bassa» (default 60)")
    p.add_argument("--alta", type=int, default=120, help="la cadenza «alta» (default 120)")
    p.add_argument("--crollo", type=int, default=10, help="il controllo positivo (default 10)")
    p.add_argument("--intermedia", type=int, default=0,
                   help="il freno della cella D: strettamente fra bassa e alta "
                        "(default: tre quarti di --alta)")
    p.add_argument("--scena2", action="store_true",
                   help="usa `03-scena` dello step 2 (wl_shm, presentation-time, conta le "
                        "ATTESE) invece della mia: e' il confronto fra due scene indipendenti")
    p.add_argument("--griglia", type=str, default="",
                   help="invece delle celle, spazza questi freni (separati da virgola) su un "
                        "monitor fisso a --alta: e' la prova della LEGGE del freno")
    p.add_argument("--secondi", type=int, default=30, help="secondi a regime per cella")
    p.add_argument("--riscaldamento", type=int, default=6, help="secondi buttati prima di misurare")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    o = p.parse_args()
    if not o.intermedia:
        o.intermedia = o.alta * 3 // 4

    if o.qui:
        return esegui(o)

    if socket.gethostname() == "NIC-OS":
        return esegui(o)

    lavoro = os.path.join(os.environ.get("TMPDIR", "/tmp"), "b14-costruzione")
    costruisci_e_spedisci(lavoro)
    argomenti = ["--bassa", str(o.bassa), "--alta", str(o.alta), "--crollo", str(o.crollo),
                 "--intermedia", str(o.intermedia), "--griglia", o.griglia] \
                + (["--scena2"] if o.scena2 else []) + [
                 "--secondi", str(o.secondi), "--riscaldamento", str(o.riscaldamento),
                 "--larghezza", str(o.larghezza), "--altezza", str(o.altezza)]
    rc = gira_la(argomenti)
    nome = nome_esiti(o)
    r = subprocess.run(["scp", "-q", "%s@%s:%s/%s" % (UTENTE_SERVER, SERVER, REMOTA, nome),
                        os.path.join(QUI, nome)], capture_output=True, text=True)
    if r.returncode == 0:
        inf("esiti riportati in %s" % os.path.join(QUI, nome))
    else:
        ko("⛔ non riesco a riportare gli esiti: %s" % r.stderr.strip())
    # ⛔ Il codice di LA' non si arrotonda: se il giro su NIC-OS e' uscito 2 o 3
    #    (attrezzatura), quel numero deve arrivare intero a chi legge.  L'1 si
    #    aggiunge solo per i rossi di QUA — oggi uno solo, lo `scp` che non
    #    riporta gli esiti — e solo quando di la' era andato tutto bene.
    #    ⚠ «Gli esiti non sono tornati» non e' «il giro e' andato»: sono due
    #      cose, e schiacciarle su 0 e' la forma E8.
    return rc if rc else (1 if ROSSI else 0)


if __name__ == "__main__":
    sys.exit(main())
