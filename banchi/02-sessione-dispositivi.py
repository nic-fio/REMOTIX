#!/usr/bin/env python3
"""02-sessione-dispositivi.py — QUANDO nasce il puntatore virtuale, e chi se ne
accorge.

  python3 02-sessione-dispositivi.py --traccia /run/user/1000/f21-seat.log

===========================================================================
⛔ PERCHE' ESISTE — la domanda che `PIANO.md` porta dentro la fase 2
===========================================================================

`[M]` 10 agosto 2026, sonda S7 (`web/rapporti/S-esiti-sonda.md` §8, voce S.4):
in una sessione GNOME senza dispositivi di input fisici, se il client parte
**prima** che il puntatore virtuale esista non riceve nulla — ne' rotella, ne'
bottoni, **ne' il movimento**.  Se parte **dopo**, riceve tutto.  E' l'ORDINE a
essere misurato; la CAUSA e' `[?]`.

⇒ ⛔ Il banco della fase 2 deve aprire l'applicazione DOPO, o misura una scena
  che il prodotto non avra' mai.

===========================================================================
⭐ E LEGGENDO MUTTER 48.7 LA REGOLA E' PIU' STRETTA DI COME IL PIANO LA SCRIVE
===========================================================================

`ensure_virtual_device()` e' chiamata dai gestori di `NotifyPointerMotion*` e
`NotifyPointerButton(pressed)`, **non** da `Start()`
(`meta-remote-desktop-session.c:290-321`, `:780-800`, `:940-960` — letto il
12 agosto 2026 `[R]`).

⇒ Il puntatore **non nasce quando la sessione RemoteDesktop parte: nasce al
  PRIMO MOVIMENTO INIETTATO.**  Un banco che aprisse l'applicazione dopo
  `Start()` ma prima del primo movimento crederebbe di aver rispettato l'ordine
  e misurerebbe la scena sbagliata.

===========================================================================
⛔ IL DIFETTO DI BANCO CHE QUESTO FILE ESISTE PER NON RIFARE — 12 ago 2026
===========================================================================

La prima stesura faceva i tre passi con tre `gdbus call` di fila.  ⛔ Non
funziona, e **non funziona in silenzio**: la sessione di `org.gnome.Mutter.
RemoteDesktop` e' legata alla CONNESSIONE che l'ha creata, e `gdbus` apre una
connessione nuova a ogni invocazione e la chiude uscendo.  Risultato misurato:

    CreateSession → '/org/gnome/Mutter/RemoteDesktop/Session/u1'   (uscita 0)
    Start         → UnknownMethod: Object does not exist at path   (uscita 1)

⇒ Il puntatore non nasceva **mai**, e il passo dopo — «il client partito prima
  ha ricevuto un secondo annuncio?» — rispondeva NO e sembrava una conferma
  della spiegazione del piano.  ⭐ Era un rosso su una scena mai avvenuta: la
  forma d'errore piu' cara, perche' **conferma** quel che ci si aspettava.
  Se ne e' accorto solo perche' lo stato d'uscita di ogni `gdbus` era guardato
  (`REVIEWER.md` §1 punto 4).

⇒ Qui la connessione al bus e' **una sola** e resta viva per tutta la misura.

===========================================================================
⭐ IL CONTROLLO POSITIVO DEL PASSO CHE CONTA
===========================================================================

«Ho iniettato un movimento» non e' «Mutter l'ha ricevuto».  Il controllo e'
`org.gnome.Mutter.IdleMonitor.GetIdletime`, che **crolla** quando un evento
arriva davvero — l'input che iniettiamo non e' marcato SYNTHETIC
(`gnome.md` §7, `core/events.c:126-138`).  Se l'inattivita' non crolla, il
movimento non e' arrivato e **tutto quel che segue non vale**: l'esito diventa
`[?] scena mai avvenuta`, non un no.

===========================================================================
GLI ATTESI, SCRITTI PRIMA DEL GIRO
===========================================================================

  passo 1  un client Wayland vivo vede  wl_seat.capabilities(0)   — niente
           puntatore, niente tastiera.  `[M]` gia' visto il 12 ago 2026
  passo 2  dopo il primo movimento iniettato l'inattivita' crolla sotto i 5 s
  passo 3  quel MEDESIMO client riceve — o non riceve — un secondo
           `wl_seat.capabilities` con il bit del puntatore:
             · NON lo riceve ⇒ la spiegazione del piano regge, e la `[?]`
               diventa `[M]`
             · lo riceve     ⇒ la spiegazione e' sbagliata, la causa e' altrove
                               e va cercata nel client, non nel compositore
  passo 4  un client NUOVO, nato dopo, vede capabilities col puntatore — e' il
           caso opposto, e senza di lui il passo 3 non distingue «non gliel'ha
           detto» da «lo strumento non sa leggere le capacita'»

  uscita 0  misurato, e il client di prima NON riceve niente (piano confermato)
  uscita 1  misurato, e il client di prima RICEVE (piano da riscrivere)
  uscita 2  ⛔ scena mai avvenuta: il puntatore non e' nato, non giudico
  uscita 3  ⛔ lo strumento e' cieco: nemmeno il client nuovo vede il puntatore
"""

import argparse
import os
import re
import subprocess
import sys
import time

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

RD = "org.gnome.Mutter.RemoteDesktop"
IDLE = "org.gnome.Mutter.IdleMonitor"

VERDE, ROSSO, GIALLO, FINE = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def ok(t):
    print(f"    {VERDE}OK{FINE}  {t}")


def no(t):
    print(f"    {ROSSO}NO{FINE}  {t}")


def att(t):
    print(f"    {GIALLO}⚠{FINE}   {t}")


def inf(t):
    print(f"    --  {t}")


def titolo(t):
    print(f"\n\033[1m== {t}{FINE}")


def capacita(traccia):
    """Le righe `wl_seat#N.capabilities(X)` viste finora nella traccia.

    ⛔ Ritorna la LISTA, non il conteggio: due eventi con lo stesso valore e un
       evento solo sono due fatti diversi, e un conteggio li confonderebbe."""
    try:
        with open(traccia) as f:
            testo = f.read()
    except OSError as err:
        raise RuntimeError(f"non leggo la traccia {traccia}: {err}")
    return re.findall(r"wl_seat#\d+\.capabilities\((\d+)\)", testo)


def idletime(conn):
    r = conn.call_sync(IDLE, "/org/gnome/Mutter/IdleMonitor/Core", IDLE,
                       "GetIdletime", None, None, Gio.DBusCallFlags.NONE,
                       10000, None)
    return r.unpack()[0]


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--traccia", required=True,
                   help="la traccia WAYLAND_DEBUG del client tenuto vivo")
    p.add_argument("--attesa-crollo", type=int, default=5000,
                   help="sotto quanti ms deve cadere l'inattivita' (atteso, "
                        "scritto prima)")
    p.add_argument("--esiti", default=None)
    a = p.parse_args()
    fatti = {"traccia": a.traccia}

    titolo("Gli attesi, SCRITTI PRIMA")
    inf("passo 1: il client vivo vede capabilities(0) — niente puntatore")
    inf(f"passo 2: dopo il primo movimento l'inattivita' scende sotto "
        f"{a.attesa_crollo} ms")
    inf("passo 3: e il MEDESIMO client riceve, o non riceve, un secondo annuncio")

    titolo("1. Che cosa ha visto finora il client partito PRIMA")
    try:
        prima = capacita(a.traccia)
    except RuntimeError as err:
        no(f"⛔ {err}")
        scrivi_esito(a, fatti, 3, '[?] strumento cieco')
        return 3
    inf(f"annunci wl_seat.capabilities finora: {prima}")
    fatti["capacita_prima"] = prima
    if not prima:
        no("⛔ ZERO annunci nella traccia.  ⛔ Non e' «capacita' zero»: e' «non ho")
        no("   letto niente».  Lo strumento e' cieco, non giudico.")
        scrivi_esito(a, fatti, 3, '[?] strumento cieco')
        return 3
    if prima[-1] != "0":
        att(f"⚠ l'ultimo annuncio dice {prima[-1]}, non 0: in questa sessione un "
            "puntatore c'e' gia', e la scena non e' quella che volevo")

    titolo("2. Faccio nascere il puntatore — UNA connessione sola, dal principio alla fine")
    conn = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    inf(f"la mia connessione: {conn.get_unique_name()}  ⛔ e resta viva fino in fondo")

    r = conn.call_sync(RD, "/org/gnome/Mutter/RemoteDesktop", RD,
                       "CreateSession", None, None, Gio.DBusCallFlags.NONE,
                       15000, None)
    percorso = r.unpack()[0]
    ok(f"CreateSession → {percorso}")

    conn.call_sync(RD, percorso, RD + ".Session", "Start", None, None,
                   Gio.DBusCallFlags.NONE, 15000, None)
    ok("Start riuscita")

    # ⛔ E QUI, e non prima, nasce il puntatore: `ensure_virtual_device()` sta
    #    dentro il gestore di NotifyPointerMotionRelative.
    idle_prima = idletime(conn)
    inf(f"inattivita' prima del movimento: {idle_prima} ms")
    conn.call_sync(RD, percorso, RD + ".Session", "NotifyPointerMotionRelative",
                   GLib.Variant("(dd)", (7.0, 5.0)), None,
                   Gio.DBusCallFlags.NONE, 15000, None)
    ok("NotifyPointerMotionRelative(7,5) accettata")
    time.sleep(1.0)
    idle_dopo = idletime(conn)
    inf(f"inattivita' dopo il movimento:  {idle_dopo} ms")
    fatti["idle_prima_ms"] = idle_prima
    fatti["idle_dopo_ms"] = idle_dopo

    esito = 0
    if idle_dopo >= a.attesa_crollo:
        no(f"⛔ l'inattivita' NON e' crollata ({idle_dopo} ms ≥ {a.attesa_crollo}):")
        no("   il movimento non e' arrivato a Mutter, quindi il puntatore non e'")
        no("   nato e la scena che volevo misurare NON E' MAI AVVENUTA.")
        no("   ⛔ Non giudico: un no su una scena mai avvenuta e' peggio di niente.")
        esito = 2
    else:
        ok(f"⭐ controllo positivo passato: {idle_prima} → {idle_dopo} ms.  Mutter")
        ok("   il movimento l'ha ricevuto davvero, quindi il puntatore c'e'.")

    time.sleep(3.0)

    titolo("3. Lo stesso client di prima: gli e' arrivato un secondo annuncio?")
    dopo = capacita(a.traccia)
    inf(f"annunci ora: {dopo} (erano {prima})")
    fatti["capacita_dopo"] = dopo
    riceve = len(dopo) > len(prima)
    if esito == 2:
        att("⚠ la scena non e' avvenuta: quel che segue non e' un verdetto")
    elif riceve:
        ok(f"⭐ IL CLIENT PARTITO PRIMA RICEVE l'annuncio: {prima[-1]} → {dopo[-1]}")
        ok("   ⇒ la spiegazione del piano — «non si iscrive mai» — NON regge,")
        ok("     e la causa di S.4 va cercata altrove.")
        esito = 1
    else:
        no("⛔ NIENTE di nuovo: il client partito prima non viene informato che")
        no("   adesso c'e' un puntatore.  ⇒ La spiegazione del piano regge, e la")
        no("   `[?]` sulla causa diventa `[M]`.")

    titolo("4. Il caso opposto: un client NUOVO, nato DOPO il puntatore")
    traccia2 = a.traccia + ".dopo"
    with open(traccia2, "w") as f:
        amb = dict(os.environ, WAYLAND_DEBUG="1", WAYLAND_DISPLAY="wayland-0")
        subprocess.run(["timeout", "25", "foot", "-e", "sleep", "6"],
                       stdout=f, stderr=subprocess.STDOUT, env=amb)
    nuovo = capacita(traccia2)
    inf(f"annunci del client nuovo: {nuovo}")
    fatti["capacita_client_nuovo"] = nuovo
    if not nuovo:
        no("⛔ zero annunci anche per il client nuovo: lo strumento non vede il")
        no("   seat, e il confronto del passo 3 non distingue niente.")
        scrivi_esito(a, fatti, 3, '[?] strumento cieco')
        return 3
    if nuovo[-1] == "0":
        no(f"⛔ anche il client NUOVO vede capabilities({nuovo[-1]}): allora non")
        no("   e' l'ordine — il puntatore non compare nel seat di Wayland affatto.")
        no("   ⇒ Il confronto del passo 3 non e' un confronto: non giudico.")
        scrivi_esito(a, fatti, 3, '[?] strumento cieco')
        return 3
    ok(f"⭐ il client nuovo vede capabilities({nuovo[-1]}): il puntatore nel seat")
    ok("   c'e', e quindi il passo 3 sta confrontando due cose vere")

    # ⛔ La sessione RemoteDesktop si chiude qui, sulla connessione che l'ha
    #    creata: lasciarla addosso alla sessione grafica cambierebbe lo stato
    #    per chi misura dopo.
    conn.call_sync(RD, percorso, RD + ".Session", "Stop", None, None,
                   Gio.DBusCallFlags.NONE, 10000, None)
    inf("sessione RemoteDesktop chiusa")

    titolo("Il verdetto")
    frase = {0: "il client partito PRIMA non riceve niente — il piano regge",
             1: "il client partito PRIMA riceve — il piano va riscritto",
             2: "[?] scena mai avvenuta",
             3: "[?] strumento cieco"}[esito]
    inf(frase)
    scrivi_esito(a, fatti, esito, frase)
    return esito


def scrivi_esito(a, fatti, esito, frase):
    if not a.esiti:
        return
    import json
    with open(a.esiti, "a") as f:
        f.write(json.dumps({
            "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "banco": "F2.1", "scena": "dispositivi-ordine",
            "uscita": esito, "marca": frase, **fatti,
        }, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    sys.exit(principale())
