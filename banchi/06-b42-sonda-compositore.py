#!/usr/bin/env python3
"""06-b42-sonda-compositore.py — ⭐⭐ QUANTO E' PRONTO IL COMPOSITORE, misurato
DA FUORI DAL PRODOTTO.

    python3 06-b42-sonda-compositore.py --campioni 400 --passo 0.02 \\
            --uscita /media/REMOTIX/tmp/06-c/sonda-solo.json --etichetta solo

    python3 06-b42-sonda-compositore.py --controllo     ⭐ il controllo positivo
                                                        dello STRUMENTO (niente bus)

⛔ Gira **dentro la sessione dell'utente** (serve `DBUS_SESSION_BUS_ADDRESS`),
   sul server NIC-OS, **fuori** dal contenitore: `gi` sta li'.

===========================================================================
⛔⛔ PERCHE' ESISTE — e perche' NON puo' essere il prodotto a dirlo
===========================================================================

`fasi/06 §5.8`, 21 agosto 2026: la contesa sull'**iGPU** e' stata ricreata e
**certificata** (un codificatore da solo 382 fotogrammi/s, cinque insieme 184
ciascuno, **2,08×**) ⛔ ma il prodotto **non se n'e' accorto**, perche' a 18
fotogrammi/s di 1280x800 chiede all'iGPU circa **un cinquantesimo** di quel che
chiedono cinque codificatori a 1920x1080.  ⇒ Una causa **esclusa con la
misura**.

⭐ Dove il segnale c'era: la latenza **«Mutter»** — dalla richiesta al
produttore alla risposta — aveva **13 e 17 campioni oltre il tetto** su ~57, in
**tutt'e due** le meta'.  Un quarto delle richieste al compositore senza
risposta entro un secondo.  ⇒ L'imputato che resta e' il **compositore**, e la
scena da costruire e' **cinque sessioni grafiche**, non cinque codificatori.

⛔ Ma «ho acceso cinque sessioni» **non e'** «il compositore ha rallentato»: e'
   la forma **E1** del catalogo (`REVIEWER.md` §2), la condizione necessaria
   usata come se fosse sufficiente — ed e' esattamente l'errore che §5.8 ha
   evitato solo perche' aveva scritto un testimone.  ⇒ Serve un numero, preso
   **fuori dal prodotto**: se lo desse il prodotto, il banco si assolverebbe da
   solo (`LEZIONI.md` §1.2).

===========================================================================
⛔ CHE COSA MISURA DAVVERO — e che cosa NON misura
===========================================================================

Il tempo di andata e ritorno di una chiamata D-Bus **servita dal ciclo
principale di Mutter**:

  · `org.gnome.Mutter.IdleMonitor.GetIdletime` — la piu' magra che ci sia: non
    fa quasi lavoro, quindi quel che si legge e' **quanto il ciclo principale
    era occupato prima di arrivarci**.  ⭐ E' la sonda che conta;
  · `org.gnome.Mutter.DisplayConfig.GetCurrentState` — piu' grassa, tocca il
    gestore dei monitor.  Si prende come secondo parere.

⛔ **Quel che NON misura, e va scritto**: la latenza del *fotogramma*.  Un ciclo
   principale pronto non garantisce che lo screencast consegni in tempo.  ⇒ Il
   testimone del fotogramma resta quello del client (`06-b42-verdetto.py`), e
   sono **due misure diverse con due nomi diversi** — forma E2 se le si
   confondesse.

⛔ **E la connessione al bus si apre UNA VOLTA SOLA**: aprirla per campione
   misurerebbe `dbus-daemon` e il costo di connessione, non il compositore.
   ⚠ E i primi campioni si buttano (`LEZIONI.md` §1.4, forma E9): il primo
   viaggio porta dentro la risoluzione del nome sul bus.

⛔ **Un errore NON e' uno zero**: una chiamata fallita si conta a parte, e se
   ne fallisce piu' di una su venti la sonda esce ROSSA.  Un campione perduto
   in silenzio abbasserebbe la mediana proprio quando il compositore soffre —
   cioe' mentirebbe nella direzione che rassicura.

⚠ Il ferro: **Intel UHD 730 integrata**, 20 core.  Ogni numero va letto col
  carico accanto.
"""
import argparse
import json
import os
import statistics
import sys
import time


def percentile(v, p):
    """Il p-esimo percentile, per interpolazione lineare.

    ⛔ Non si usa `statistics.quantiles`: con pochi campioni sceglie un metodo
       che qui sorprenderebbe, e un numero che non si sa ricalcolare a mano non
       e' verificabile da nessuno.
    """
    if not v:
        return None
    s = sorted(v)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p / 100.0
    i = int(k)
    f = k - i
    if i + 1 >= len(s):
        return s[-1]
    return s[i] + (s[i + 1] - s[i]) * f


def riassunto(campioni):
    """Le cinque cifre che descrivono una coda, non solo un centro."""
    if not campioni:
        return {"n": 0}
    return {
        "n": len(campioni),
        "mediana_ms": round(statistics.median(campioni), 3),
        "p95_ms": round(percentile(campioni, 95), 3),
        "p99_ms": round(percentile(campioni, 99), 3),
        "peggiore_ms": round(max(campioni), 3),
        "oltre_50ms": sum(1 for x in campioni if x > 50.0),
        "oltre_200ms": sum(1 for x in campioni if x > 200.0),
    }


# ===========================================================================
def misura(campioni, passo, scarta):
    import gi
    gi.require_version("Gio", "2.0")
    from gi.repository import Gio, GLib

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def chiama(nome, oggetto, interfaccia, metodo):
        t0 = time.perf_counter()
        bus.call_sync(nome, oggetto, interfaccia, metodo, None, None,
                      Gio.DBusCallFlags.NONE, 5000, None)
        return (time.perf_counter() - t0) * 1000.0

    magra, grassa = [], []
    errori_magra = errori_grassa = 0
    ultimo_errore = ""
    t_inizio = time.time()
    for i in range(campioni + scarta):
        try:
            m = chiama("org.gnome.Mutter.IdleMonitor",
                       "/org/gnome/Mutter/IdleMonitor/Core",
                       "org.gnome.Mutter.IdleMonitor", "GetIdletime")
            if i >= scarta:
                magra.append(m)
        except GLib.Error as e:
            errori_magra += 1
            ultimo_errore = str(e)
        # ⚠ La grassa costa: una ogni dieci, o la sonda diventa essa stessa il
        #   carico che dice di misurare.
        if i % 10 == 0:
            try:
                g = chiama("org.gnome.Mutter.DisplayConfig",
                           "/org/gnome/Mutter/DisplayConfig",
                           "org.gnome.Mutter.DisplayConfig", "GetCurrentState")
                if i >= scarta:
                    grassa.append(g)
            except GLib.Error as e:
                errori_grassa += 1
                ultimo_errore = str(e)
        if passo > 0:
            time.sleep(passo)
    return {
        "magra": riassunto(magra),
        "grassa": riassunto(grassa),
        "errori_magra": errori_magra,
        "errori_grassa": errori_grassa,
        "ultimo_errore": ultimo_errore[:300],
        "durata_s": round(time.time() - t_inizio, 2),
        "campioni_grezzi_magra": [round(x, 3) for x in magra],
    }


# ===========================================================================
# ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO — su numeri noti, senza bus
# ===========================================================================
def controllo():
    print("⭐ CONTROLLO POSITIVO DELLA SONDA — numeri noti, risposta nota\n")
    guai = []

    def prova(nome, atteso, avuto):
        segno = "OK " if avuto == atteso else "⛔ "
        print(f"    {segno} {nome}: atteso {atteso} · avuto {avuto}")
        if avuto != atteso:
            guai.append(nome)

    # 1 · le cifre si sanno ricalcolare a mano
    v = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 100.0]
    r = riassunto(v)
    prova("mediana di 1..9,100", 5.5, r["mediana_ms"])
    prova("p95 (interpolato fra 9 e 100)", 59.05, r["p95_ms"])
    prova("peggiore", 100.0, r["peggiore_ms"])
    prova("oltre 50 ms", 1, r["oltre_50ms"])
    prova("n", 10, r["n"])

    # 2 · ⛔ IL VELENO: una coda che si allunga NON deve muovere la mediana, e
    #     la sonda deve dirlo lo stesso.  E' il difetto del 16 agosto — «due
    #     casi a 3 000 ms» con la mediana a 22 — e una sonda che guardasse solo
    #     il centro non lo vedrebbe.
    piatta = [10.0] * 100
    codata = [10.0] * 98 + [3000.0, 3000.0]
    a, b = riassunto(piatta), riassunto(codata)
    prova("veleno · la mediana NON si muove", (10.0, 10.0),
          (a["mediana_ms"], b["mediana_ms"]))
    prova("veleno · ma il peggiore SI'", (10.0, 3000.0),
          (a["peggiore_ms"], b["peggiore_ms"]))
    prova("veleno · e «oltre 200 ms» conta i due", (0, 2),
          (a["oltre_200ms"], b["oltre_200ms"]))

    # 3 · lo zero si distingue dal vuoto
    prova("nessun campione ⇒ n=0, non una mediana finta", {"n": 0}, riassunto([]))

    print()
    if guai:
        print(f"⛔ CONTROLLO POSITIVO FALLITO su {len(guai)}: {guai}")
        return 1
    print("⭐ CONTROLLO POSITIVO SUPERATO: la sonda sa contare, e vede la CODA\n"
          "   anche quando il centro non si muove.")
    return 0


def main():
    p = argparse.ArgumentParser(description="la prontezza del compositore, da fuori")
    p.add_argument("--campioni", type=int, default=400)
    p.add_argument("--passo", type=float, default=0.02, help="s fra un campione e l'altro")
    p.add_argument("--scarta", type=int, default=10,
                   help="⛔ i primi N si buttano: l'avvio non e' il regime (E9)")
    p.add_argument("--uscita", default="")
    p.add_argument("--etichetta", default="senza-etichetta")
    p.add_argument("--controllo", action="store_true")
    a = p.parse_args()

    if a.controllo:
        return controllo()

    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        print("⛔ nessun DBUS_SESSION_BUS_ADDRESS: questa sonda va lanciata"
              " DENTRO la sessione dell'utente, o misurerebbe il nulla")
        return 3

    d = misura(a.campioni, a.passo, a.scarta)
    d["etichetta"] = a.etichetta
    d["ora"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    d["carico"] = open("/proc/loadavg").read().split()[:3]
    d["ferro"] = "Intel UHD 730 integrata, 20 core"

    m = d["magra"]
    if m["n"] == 0:
        print("⛔ ZERO campioni buoni — e «zero» non e' «veloce»:"
              f" errori {d['errori_magra']}, ultimo: {d['ultimo_errore']}")
        return 4
    # ⛔ Un errore non e' uno zero.  Se ne fallisce piu' di uno su venti, la
    #    mediana e' calcolata su quel che e' RIUSCITO, cioe' sui campioni
    #    buoni — e sarebbe piu' bassa del vero proprio quando il compositore
    #    soffre.
    tot = m["n"] + d["errori_magra"]
    if d["errori_magra"] * 20 > tot:
        print(f"⛔ {d['errori_magra']} chiamate fallite su {tot}: la mediana"
              " sarebbe presa sui soli campioni riusciti, cioe' mentirebbe"
              " nella direzione che rassicura.  ⇒ Sonda ROSSA.")
        print(f"   ultimo errore: {d['ultimo_errore']}")
        if a.uscita:
            json.dump(d, open(a.uscita, "w"), indent=1)
        return 4

    print(f"SONDA «{a.etichetta}» · carico {' '.join(d['carico'])} · Intel UHD 730")
    print(f"  ciclo principale di Mutter (GetIdletime), n={m['n']}:")
    print(f"      mediana {m['mediana_ms']:.2f} ms · p95 {m['p95_ms']:.2f}"
          f" · p99 {m['p99_ms']:.2f} · peggiore {m['peggiore_ms']:.2f}")
    print(f"      oltre 50 ms: {m['oltre_50ms']} · oltre 200 ms: {m['oltre_200ms']}")
    g = d["grassa"]
    if g["n"]:
        print(f"  gestore dei monitor (GetCurrentState), n={g['n']}:"
              f" mediana {g['mediana_ms']:.2f} ms · p95 {g['p95_ms']:.2f}")
    print(f"  errori: magra {d['errori_magra']} · grassa {d['errori_grassa']}")
    if a.uscita:
        json.dump(d, open(a.uscita, "w"), indent=1)
        print(f"  scritto {a.uscita}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
