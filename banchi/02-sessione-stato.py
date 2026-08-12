#!/usr/bin/env python3
"""02-sessione-stato.py — lo strumento di F2.1: dice in che stato e' la sessione
grafica, e lo dice con un numero d'uscita diverso per ogni stato.

  python3 02-sessione-stato.py --attesa 1920x1080 --dal-bus
  python3 02-sessione-stato.py --attesa 1920x1080 --da-scena scene/nera.json
  python3 02-sessione-stato.py --attesa 1920x1080 --dal-bus --registra scene/x.json

===========================================================================
⛔ PERCHE' ESISTE — il difetto che questo strumento impedisce
===========================================================================

Una sessione GNOME headless senza `--virtual-monitor` parte **viva, completa e
nera** (`gnome.md` §3.1: in headless `needs_outputs=false`).  Viva vuol dire
proprio viva: `IsSessionRunning` risponde `true`, il bus ha cinquanta nomi,
Nautilus e il Terminale ci sono.  Manca una cosa sola — un monitor — e siccome
manca in silenzio, chi misura la CATTURA su quella sessione legge zero
fotogrammi e va a cercare il difetto dentro PipeWire.  `PIANO.md` fase 2: *«si
cerca per mezza giornata dalla parte sbagliata»*.

⭐ Non e' un timore: il 12 agosto 2026, aprendo questo giro, la sessione GNOME
   viva su NIC-OS da due giorni era **esattamente quella** — `GetCurrentState`
   rispondeva con zero monitor e zero monitor logici.  `[M]`

===========================================================================
⛔ LE QUATTRO DOMANDE, E CIASCUNA COL SUO CASO OPPOSTO
===========================================================================

| la domanda                          | il caso opposto, scritto prima          |
|-------------------------------------|-----------------------------------------|
| la sessione e' viva?                | c'e' il processo ma il bus non risponde |
| ha il monitor della misura CHIESTA? | ne ha uno che si e' scelto da se' (E2)  |
| e' viva e nera?                     | ha un monitor, e allora nera non e'     |
| la SHELL e' vuota?                  | gnome-session e' ripartito in una shell |

===========================================================================
⛔ I NUMERI D'USCITA, SCRITTI PRIMA DEL GIRO (`PIANO.md` §0.3 punto 4)
===========================================================================

  0  SANA                  un monitor solo, prodotto «MetaVirtualMonitor»,
                           della misura chiesta, e la riga di comando la chiede
  1  NERA: ZERO MONITOR    viva, e zero monitor: e' il guasto di M9
  2  MISURA SBAGLIATA      un monitor, ma non della misura chiesta
  3  MONITOR SCELTO DA SE  prodotto «Virtual remote monitor» (creato da Mutter
                           per uno ScreenCast), oppure piu' di uno       ← E2
  4  SESSIONE MORTA        nessun gnome-shell, o il bus non risponde
  5  LETTURA IGNOTA        non ho potuto leggere: negata, o illeggibile  ← E8
  6  DISACCORDO            la riga di comando e il bus non dicono lo stesso ← E1
  7  SHELL NON VUOTA       gnome-session si e' ri-eseguito in una shell di login

⛔ La precedenza, dichiarata perche' due stati possono valere insieme:

       5 > 4 > 7 > 3 > 2 > 1 > 6 > 0

   · «Non ho potuto leggere» (5) vince su tutto: se lo strumento e' cieco non
     ha diritto di dare un verdetto sul soggetto;
   · ⛔ **il DISACCORDO (6) sta in fondo, ed e' una correzione pagata**.  Nella
     prima stesura stava in alto, subito sotto 7 — e il 12 agosto 2026 la
     certificazione sulle scene ha mostrato che cosi' **due verdetti su otto
     non si potevano raggiungere mai**: una misura sbagliata (2) e un monitor
     che Mutter si e' scelto da se' (3) fanno *anche* discordare la riga di
     comando dal bus, quindi uscivano tutt'e due come 6.  ⇒ Il disaccordo e'
     il verdetto **residuo**: si da' solo quando nessuna spiegazione piu'
     precisa regge.  Se non l'avesse trovato la certificazione, la forma E2 —
     il monitor scelto da se', che e' proprio quel che questo banco esiste per
     vedere — sarebbe stata invisibile sotto un'etichetta generica.

===========================================================================
⛔ ZERO E FALLIMENTO SONO DUE COSE DIVERSE  (`REVIEWER.md` §1 punto 4)
===========================================================================

Niente `2>/dev/null` e niente `gdbus | grep`.  Si chiama D-Bus da `Gio` e si
prendono i dati TIPATI: «la risposta e' una lista vuota» e «la chiamata e'
fallita» arrivano per due strade diverse e finiscono in due codici diversi
(1 e 5).  ⛔ Il 12 agosto 2026 la differenza si e' pagata subito: sulla stessa
sessione `org.gnome.Shell.Introspect.GetWindows` e `Shell.Screenshot` rispondono
**AccessDenied** a un chiamante qualunque `[M]` — un banco che avesse letto
«zero finestre» avrebbe scritto «sessione vuota» dove il vero fatto era «non mi
hanno fatto guardare».

===========================================================================
⛔ E LA RIGA DI COMANDO NON BASTA, E NEMMENO IL BUS DA SOLO
===========================================================================

Che l'opzione sia SCRITTA non e' che sia IN VIGORE (E1: necessario preso per
sufficiente).  Quindi si leggono tutt'e due — `/proc/<pid>/cmdline` e
`GetCurrentState` — e **il disaccordo e' un verdetto suo** (6), non un
arrotondamento verso l'uno o verso l'altro.

===========================================================================
⭐ IL CONTROLLO POSITIVO, IN CODA A OGNI ESECUZIONE
===========================================================================

Due, e servono a due cose diverse:

  1. **il parser sa leggere**: nella risposta di `GetCurrentState` ci dev'essere
     la proprieta' `layout-mode`, che c'e' SEMPRE (`meta-monitor-manager.c`).
     Se manca, e' rotto il parser, non la sessione — e lo strumento lo dice
     invece di stampare «zero monitor»;
  2. **il filo col compositore e' vivo adesso**: `IdleMonitor.GetIdletime`
     chiamato due volte a distanza deve dare due numeri DIVERSI e crescenti.
     Uno strumento che legge una risposta congelata darebbe lo stesso numero.

⛔ Se un controllo positivo fallisce, l'uscita diventa 5 qualunque cosa dicesse
   il verdetto: e' la regola «uno strumento che non ha mai trovato niente non e'
   pulito, e' non certificato» applicata a se stesso.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

# Il prodotto che Mutter mette al monitor persistente chiesto con
# `--virtual-monitor` (`meta-context-main.c:592-597`, letto il 12 ago 2026 [R]).
PRODOTTO_CHIESTO = "MetaVirtualMonitor"
# E quello che si mette da se' quando uno ScreenCast virtuale ne vuole uno
# (`meta-screen-cast-virtual-stream-src.c:606-609` [R]).  Sono DUE stringhe
# diverse, ed e' l'unica cosa che distingue «il mio» da «il suo»: la misura no,
# perche' puo' coincidere.
PRODOTTO_DA_SE = "Virtual remote monitor"

MARCHE = {
    0: "SANA",
    1: "NERA: ZERO MONITOR",
    2: "MISURA SBAGLIATA",
    3: "MONITOR SCELTO DA SE",
    4: "SESSIONE MORTA",
    5: "LETTURA IGNOTA",
    6: "DISACCORDO",
    7: "SHELL NON VUOTA",
}
# Dal piu' forte al piu' debole.  ⛔ Il 6 sta in fondo apposta: vedi in testa.
PRECEDENZA = [5, 4, 7, 3, 2, 1, 6, 0]

VERDE = "\033[1;32m"
ROSSO = "\033[1;31m"
GIALLO = "\033[1;33m"
FINE = "\033[0m"


def ok(t):
    print(f"    {VERDE}OK{FINE}  {t}")


def no(t):
    print(f"    {ROSSO}NO{FINE}  {t}")


def inf(t):
    print(f"    --  {t}")


def att(t):
    print(f"    {GIALLO}⚠{FINE}   {t}")


def titolo(t):
    print(f"\n\033[1m== {t}{FINE}")


# ---------------------------------------------------------------------------
# La raccolta dei fatti.  Ogni fatto ha tre esiti possibili — c'e', non c'e',
# non l'ho potuto leggere — e il terzo non si confonde col secondo.
# ---------------------------------------------------------------------------
class Ignota(Exception):
    """Non ho potuto leggere.  ⛔ Non e' «non c'e'»."""


def processi_shell():
    """I pid di gnome-shell.  ⛔ `pgrep -x`: `comm` e' troncato a 15 caratteri
    (`fasi/00-ambiente.md` B3.1), e «gnome-shell» ne ha 11 — ci sta.  Ma lo
    stato d'uscita si guarda: 0 trovato, 1 nessuno, 2+ ERRORE."""
    e = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "gnome-shell"],
                       capture_output=True, text=True)
    if e.returncode == 0:
        return [int(r) for r in e.stdout.split()]
    if e.returncode == 1:
        return []
    raise Ignota(f"pgrep e' uscito con {e.returncode}: {e.stderr.strip()!r}")


def riga_comando(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return [a.decode("utf-8", "replace")
                    for a in f.read().split(b"\0") if a]
    except OSError as err:
        raise Ignota(f"non leggo /proc/{pid}/cmdline: {err}")


def ambiente_di(pid):
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            grezzo = f.read()
    except OSError as err:
        raise Ignota(f"non leggo /proc/{pid}/environ: {err}")
    amb = {}
    for voce in grezzo.split(b"\0"):
        if b"=" in voce:
            k, _, v = voce.partition(b"=")
            amb[k.decode("utf-8", "replace")] = v.decode("utf-8", "replace")
    return amb


def pid_gnome_session():
    e = subprocess.run(["pgrep", "-u", str(os.getuid()), "-f",
                        "gnome-session-binary"], capture_output=True, text=True)
    if e.returncode == 0:
        return int(e.stdout.split()[0])
    if e.returncode == 1:
        return None
    raise Ignota(f"pgrep gnome-session-binary e' uscito con {e.returncode}")


def bus():
    try:
        return Gio.bus_get_sync(Gio.BusType.SESSION, None)
    except GLib.Error as err:
        raise Ignota(f"non mi collego al bus di sessione: {err.message}")


def chiama(conn, dest, path, iface, metodo, args=None, tetto=15000):
    """Ritorna (valore, None) oppure (None, messaggio d'errore).

    ⛔ L'errore NON si perde e NON diventa un valore vuoto: chi chiama decide
       se e' «non c'e'» o «non ho potuto guardare», e i due casi finiscono in
       due codici d'uscita diversi."""
    try:
        r = conn.call_sync(dest, path, iface, metodo, args, None,
                           Gio.DBusCallFlags.NONE, tetto, None)
        return r, None
    except GLib.Error as err:
        return None, err.message


def leggi_monitor(conn):
    """I monitor secondo `org.gnome.Mutter.DisplayConfig.GetCurrentState`.

    La firma della risposta e'
      (u serial, a((ssss) a(siiddada{sv}) a{sv}) monitors,
                 a(iiduba(ssss)a{sv}) logical, a{sv} props)
    dove `(ssss)` e' (connector, vendor, product, serial)
    e ogni modo e' (id, larghezza, altezza, refresh, scala-preferita,
                    scale-supportate, proprieta') — e il modo IN USO porta
    `is-current` fra le proprieta'."""
    r, errore = chiama(conn, "org.gnome.Mutter.DisplayConfig",
                       "/org/gnome/Mutter/DisplayConfig",
                       "org.gnome.Mutter.DisplayConfig", "GetCurrentState")
    if errore is not None:
        raise Ignota(f"GetCurrentState: {errore}")
    serial, monitors, logical, props = r.unpack()
    elenco = []
    for (connettore, fornitore, prodotto, seriale), modi, mprops in monitors:
        corrente = None
        for m in modi:
            mid, larg, alt, refresh, scala, scale, mp = m
            if mp.get("is-current"):
                corrente = {"id": mid, "larghezza": larg, "altezza": alt,
                            "refresh": round(refresh, 3)}
        elenco.append({"connettore": connettore, "fornitore": fornitore,
                       "prodotto": prodotto, "seriale": seriale,
                       "modo_corrente": corrente, "modi": len(modi)})
    return {"serial": serial, "monitor": elenco, "logici": len(logical),
            "proprieta": {k: str(v) for k, v in props.items()}}


# ---------------------------------------------------------------------------
def raccogli_dal_bus():
    """Compone la SCENA: tutti i fatti grezzi, senza giudicarli.

    ⭐ Separare la raccolta dal giudizio non e' eleganza: e' la sola cosa che
       permette di certificare il giudizio su scene REGISTRATE, senza dover
       rompere una macchina vera per ogni caso opposto."""
    scena = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
             "macchina": os.uname().nodename, "ignote": []}

    try:
        pids = processi_shell()
        scena["shell_pid"] = pids
        scena["shell_riga"] = riga_comando(pids[0]) if pids else None
    except Ignota as e:
        scena["shell_pid"] = None
        scena["shell_riga"] = None
        scena["ignote"].append(str(e))

    try:
        p = pid_gnome_session()
        scena["gnome_session_pid"] = p
        if p:
            amb = ambiente_di(p)
            # ⛔ La trappola di `gnome.md` §3.1: `gnome-session.in:3-14` si
            #    ri-esegue dentro una shell di LOGIN se `$SHELL` sta in
            #    /etc/shells.  Il controllo vero e' `[ -n "$SHELL" ]`, quindi
            #    ASSENTE e VUOTA vanno tutt'e due bene: si registrano distinte
            #    per non far credere che siano la stessa cosa.
            scena["shell_var"] = amb.get("SHELL", None)
            scena["shell_var_presente"] = "SHELL" in amb
            scena["xdg_session_type"] = amb.get("XDG_SESSION_TYPE")
        else:
            scena["shell_var"] = None
            scena["shell_var_presente"] = None
            scena["xdg_session_type"] = None
    except Ignota as e:
        scena["gnome_session_pid"] = None
        scena["shell_var_presente"] = None
        scena["ignote"].append(str(e))

    try:
        conn = bus()
    except Ignota as e:
        scena["ignote"].append(str(e))
        scena["sessione_gira"] = None
        scena["display"] = None
        scena["controllo_positivo"] = {"esito": False, "perche": str(e)}
        return scena

    r, errore = chiama(conn, "org.gnome.SessionManager", "/org/gnome/SessionManager",
                       "org.gnome.SessionManager", "IsSessionRunning")
    # ⛔ `ServiceUnknown` = la sessione non c'e' (fatto sul soggetto);
    #    qualunque altro errore = non ho potuto guardare (fatto sullo strumento).
    if errore is None:
        scena["sessione_gira"] = bool(r.unpack()[0])
        scena["sessione_errore"] = None
    elif "ServiceUnknown" in errore or "was not provided by any" in errore:
        scena["sessione_gira"] = False
        scena["sessione_errore"] = errore
    else:
        scena["sessione_gira"] = None
        scena["sessione_errore"] = errore
        scena["ignote"].append(f"IsSessionRunning: {errore}")

    try:
        scena["display"] = leggi_monitor(conn)
    except Ignota as e:
        scena["display"] = None
        scena["ignote"].append(str(e))

    scena["controllo_positivo"] = controllo_positivo(conn, scena)
    return scena


def controllo_positivo(conn, scena):
    """⭐ «Questo strumento sa trovare qualcosa che c'e' di sicuro?»"""
    esito = {"layout_mode": None, "idletime_1": None, "idletime_2": None,
             "esito": False, "perche": ""}

    d = scena.get("display")
    if d is not None:
        esito["layout_mode"] = d["proprieta"].get("layout-mode")

    for chiave in ("idletime_1", "idletime_2"):
        r, errore = chiama(conn, "org.gnome.Mutter.IdleMonitor",
                           "/org/gnome/Mutter/IdleMonitor/Core",
                           "org.gnome.Mutter.IdleMonitor", "GetIdletime")
        esito[chiave] = r.unpack()[0] if errore is None else None
        if errore is not None:
            esito["perche"] = f"GetIdletime: {errore}"
            return esito
        time.sleep(0.35)

    if esito["layout_mode"] is None:
        esito["perche"] = ("nella risposta di GetCurrentState non c'e' «layout-mode», "
                           "che c'e' sempre: e' rotto il parser, non la sessione")
        return esito
    if esito["idletime_2"] is None or esito["idletime_1"] is None:
        esito["perche"] = "IdleMonitor non ha risposto"
        return esito
    if esito["idletime_2"] <= esito["idletime_1"]:
        esito["perche"] = (f"l'inattivita' non cresce ({esito['idletime_1']} → "
                           f"{esito['idletime_2']}): sto leggendo una risposta ferma")
        return esito
    esito["esito"] = True
    return esito


# ---------------------------------------------------------------------------
# Il giudizio: dalla scena al numero.  Nessuna lettura qui dentro — cosi' si
# puo' far girare su una scena registrata, ed e' quel che rende certificabile
# lo strumento senza rompere una macchina vera per ogni caso opposto.
# ---------------------------------------------------------------------------
def giudica(scena, attesa_l, attesa_a):
    stati = set()
    detto = []

    def dice(t):
        detto.append(t)

    if scena.get("ignote"):
        stati.add(5)
        for i in scena["ignote"]:
            dice(f"⛔ IGNOTA: {i}")
    cp = scena.get("controllo_positivo") or {}
    if not cp.get("esito"):
        stati.add(5)
        dice(f"⛔ il controllo positivo NON e' passato: {cp.get('perche', 'ignoto')}")

    pids = scena.get("shell_pid")
    if not pids:
        stati.add(4)
        dice("nessun processo gnome-shell")
    if scena.get("sessione_gira") is False:
        stati.add(4)
        dice("IsSessionRunning risponde no (o il nome non c'e' sul bus)")

    # ⛔ La SHELL, e i due modi giusti di averla: assente o vuota.
    if scena.get("gnome_session_pid"):
        if scena.get("shell_var_presente") and scena.get("shell_var"):
            stati.add(7)
            dice(f"⛔ SHELL={scena['shell_var']!r} nell'ambiente di gnome-session: "
                 "si e' ri-eseguito dentro una shell di login (gnome.md §3.1)")
        else:
            dice("SHELL " + ("vuota" if scena.get("shell_var_presente") else "assente")
                 + " nell'ambiente di gnome-session: la trappola §3.1 non ha morso")

    # Quel che la RIGA DI COMANDO chiede.
    riga = scena.get("shell_riga") or []
    chiesto = None
    chiesto_headless = "--headless" in riga
    for i, a in enumerate(riga):
        m = re.match(r"^--virtual-monitor=(.+)$", a)
        if m:
            chiesto = m.group(1)
        elif a == "--virtual-monitor" and i + 1 < len(riga):
            chiesto = riga[i + 1]
    chiesto_wh = None
    if chiesto:
        m = re.match(r"^(\d+)x(\d+)", chiesto)
        if m:
            chiesto_wh = (int(m.group(1)), int(m.group(2)))

    # Quel che il BUS dice.
    d = scena.get("display")
    monitor = d["monitor"] if d else None

    if monitor is not None:
        dice(f"il bus dichiara {len(monitor)} monitor e {d['logici']} monitor logici")
        if len(monitor) == 0:
            stati.add(1)
            dice("⛔ ZERO monitor: la sessione puo' essere viva e completa, e "
                 "non c'e' NIENTE da disegnare (gnome.md §3.1)")
        elif len(monitor) > 1:
            stati.add(3)
            dice(f"⛔ {len(monitor)} monitor: ne era stato chiesto uno solo")
            # ⛔ E SI DICE CHI SONO, uno per uno.  La prima stesura si fermava
            #    al conteggio, e il 12 agosto 2026 ha visto due monitor su una
            #    sessione che ne aveva chiesto uno — senza poter dire QUALE
            #    fosse quello di troppo, perche' il nome non l'aveva stampato.
            #    Un banco che conta e non nomina manda a indovinare.
            for i, m in enumerate(monitor):
                dice(f"⛔   [{i}] connettore={m['connettore']!r} "
                     f"prodotto={m['prodotto']!r} seriale={m['seriale']!r} "
                     f"modo={m['modo_corrente']}")
        else:
            m0 = monitor[0]
            dice(f"monitor: connettore={m0['connettore']!r} fornitore={m0['fornitore']!r} "
                 f"prodotto={m0['prodotto']!r} seriale={m0['seriale']!r}")
            if m0["prodotto"] == PRODOTTO_DA_SE:
                stati.add(3)
                dice(f"⛔ il prodotto e' «{PRODOTTO_DA_SE}»: questo monitor se l'e' "
                     "creato Mutter per uno ScreenCast, non l'abbiamo chiesto noi "
                     "(E2 — un componente che decide da se')")
            elif m0["prodotto"] != PRODOTTO_CHIESTO:
                stati.add(3)
                dice(f"⛔ prodotto inatteso {m0['prodotto']!r}: non e' ne' il nostro "
                     f"«{PRODOTTO_CHIESTO}» ne' quello di ScreenCast")
            mc = m0["modo_corrente"]
            if mc is None:
                stati.add(2)
                dice("⛔ il monitor non ha nessun modo corrente")
            elif (mc["larghezza"], mc["altezza"]) != (attesa_l, attesa_a):
                stati.add(2)
                dice(f"⛔ misura {mc['larghezza']}x{mc['altezza']}, attesa "
                     f"{attesa_l}x{attesa_a}")
            else:
                dice(f"misura {mc['larghezza']}x{mc['altezza']} a {mc['refresh']} Hz: "
                     "e' quella chiesta")

    # ⛔ IL DISACCORDO FRA LE DUE LETTURE — E1.
    if riga and monitor is not None:
        nostro = [m for m in monitor if m["prodotto"] == PRODOTTO_CHIESTO]
        if chiesto_wh and not nostro:
            dice(f"⚠ la riga di comando chiede --virtual-monitor {chiesto} e sul bus "
                 f"un monitor «{PRODOTTO_CHIESTO}» non c'e'")
            stati.add(6)
        if not chiesto_wh and nostro:
            dice(f"⚠ sul bus c'e' un «{PRODOTTO_CHIESTO}» e la riga di comando NON lo "
                 "chiede: qualcuno l'ha messo per un'altra strada")
            stati.add(6)
        if chiesto_wh and nostro and nostro[0]["modo_corrente"]:
            mc = nostro[0]["modo_corrente"]
            if (mc["larghezza"], mc["altezza"]) != chiesto_wh:
                dice(f"⚠ la riga chiede {chiesto_wh[0]}x{chiesto_wh[1]} e il bus dice "
                     f"{mc['larghezza']}x{mc['altezza']}")
                stati.add(6)
        if not chiesto_headless:
            dice("⚠ --headless NON e' sulla riga di comando: se l'headless c'e' e' "
                 "per accidente (gnome.md §1.2, DECISIONI.md §4.3-bis)")

    if not stati:
        stati.add(0)
    for c in PRECEDENZA:
        if c in stati:
            return c, sorted(stati), detto
    return 0, [], detto


# ---------------------------------------------------------------------------
def principale():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--attesa", default="1920x1080",
                   help="la misura CHIESTA, scritta prima del giro")
    p.add_argument("--dal-bus", action="store_true")
    p.add_argument("--da-scena", metavar="FILE")
    p.add_argument("--registra", metavar="FILE")
    p.add_argument("--esiti", metavar="FILE", default=None)
    p.add_argument("--etichetta", default="senza-nome",
                   help="la SCENA dichiarata, che va accanto al numero")
    a = p.parse_args()

    m = re.match(r"^(\d+)x(\d+)$", a.attesa)
    if not m:
        print(f"⛔ --attesa {a.attesa!r} non e' nella forma LARGHEZZAxALTEZZA")
        return 2
    attesa_l, attesa_a = int(m.group(1)), int(m.group(2))

    if a.da_scena and a.dal_bus:
        print("⛔ o --dal-bus o --da-scena, non tutt'e due")
        return 2

    titolo(f"L'atteso, SCRITTO PRIMA di guardare — scena «{a.etichetta}»")
    inf(f"misura chiesta: {attesa_l}x{attesa_a}")
    inf(f"prodotto atteso del monitor: «{PRODOTTO_CHIESTO}»")
    inf(f"e quello che vorrebbe dire E2: «{PRODOTTO_DA_SE}»")

    if a.da_scena:
        titolo(f"La scena, letta da {a.da_scena}")
        try:
            with open(a.da_scena) as f:
                scena = json.load(f)
        except OSError as err:
            no(f"⛔ non leggo la scena: {err}")
            return 5
        inf(f"registrata il {scena.get('quando')} su {scena.get('macchina')}")
    else:
        titolo("La scena, letta dal bus vivo")
        scena = raccogli_dal_bus()

    if a.registra:
        os.makedirs(os.path.dirname(os.path.abspath(a.registra)), exist_ok=True)
        with open(a.registra, "w") as f:
            json.dump(scena, f, indent=1, ensure_ascii=False)
        inf(f"scena registrata in {a.registra}")

    titolo("I fatti, e il verdetto")
    codice, tutti, detto = giudica(scena, attesa_l, attesa_a)
    for r in detto:
        (no if r.startswith("⛔") else att if r.startswith("⚠") else inf)(r)

    cp = scena.get("controllo_positivo") or {}
    titolo("⭐ Il controllo positivo, in coda come vuole la casa")
    # ⚠ Su una scena REGISTRATA il controllo positivo e' quello di quando la
    #   scena fu presa, non di adesso: dirlo «vivo adesso» sarebbe una misura
    #   scritta come se fosse stata fatta ora.  Si distingue.
    quando = ("e' vivo adesso" if not a.da_scena
              else f"era vivo quando la scena fu presa ({scena.get('quando')})")
    if cp.get("esito"):
        ok(f"il parser trova «layout-mode» = {cp.get('layout_mode')}")
        ok(f"e il filo col compositore {quando}: inattivita' "
           f"{cp.get('idletime_1')} → {cp.get('idletime_2')} ms, cresce")
        if a.da_scena:
            att("⚠ scena registrata: questo controllo positivo NON dice che il "
                "compositore risponda in questo momento")
    else:
        no(f"⛔ NON passato: {cp.get('perche', 'ignoto')}")
        no("   ⇒ qualunque verdetto qui sopra vale come «non ho potuto leggere»")

    titolo("Il verdetto")
    inf(f"stati riconosciuti: {[MARCHE[c] for c in tutti]}")
    riga = f"uscita {codice} — {MARCHE[codice]}"
    print(f"    {VERDE if codice == 0 else ROSSO}{riga}{FINE}")

    if a.esiti:
        with open(a.esiti, "a") as f:
            f.write(json.dumps({
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "banco": "F2.1", "scena": a.etichetta,
                "attesa": f"{attesa_l}x{attesa_a}",
                "uscita": codice, "marca": MARCHE[codice],
                "stati": [MARCHE[c] for c in tutti],
                "fonte": "scena:" + a.da_scena if a.da_scena else "bus",
                "controllo_positivo": bool(cp.get("esito")),
                "monitor": (scena.get("display") or {}).get("monitor"),
                "shell_riga": scena.get("shell_riga"),
            }, ensure_ascii=False) + "\n")
    return codice


if __name__ == "__main__":
    sys.exit(principale())
