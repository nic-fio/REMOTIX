#!/usr/bin/env python3
"""06-b39-verdetto.py — il verdetto delle richieste incatenate, SOTTO CONTESA
GPU e a riposo, letti insieme.

    python3 06-b39-verdetto.py <cartella di lavoro> [--giri 18]
    python3 06-b39-verdetto.py --controllo      ⭐ il controllo positivo dello
                                                STRUMENTO, su misure finte

⛔⛔ IL PUNTO DI QUESTO PROGRAMMA NON E' CONTARE I ROTTI: quello lo sapeva fare
    anche il blocco dentro `06-b35-lancia.sh sweep`.  Il punto e' che
    **rifiuta di dare un verdetto se la contesa non ha toccato il prodotto**.

    `fasi/06 §4.8`: le richieste incatenate danno 0/18 a macchina ferma, ⛔ ma
    il controllo positivo non rende — togliendo la cura escono ancora 0/18.
    ⇒ Non si sa che cosa tenga quella scena.  L'ipotesi rimasta e' la contesa
    sulla GPU.  ⚠ Ma **«ho acceso cinque codificatori» non e' «il prodotto ha
    rallentato»**: e' la forma **E1** del catalogo (`REVIEWER.md` §2), una
    condizione necessaria usata come se fosse sufficiente.

    ⇒ Qui il testimone e' il **ritmo dei fotogrammi visto dal client**: se
      sotto contesa i fotogrammi non si diradano, la contesa non e' arrivata
      al codificatore del prodotto, e un `0/18` con l'etichetta «sotto contesa
      GPU» sarebbe **un verde per costruzione**.

⚠ Il ferro: **Intel UHD 730 integrata**, non una scheda potente.  Ogni numero
  va letto col carico accanto (`06-b39-contesa.sh stato`).
"""
import argparse
import json
import os
import statistics
import sys

# La tela finale attesa: chi trascina un bordo si aspetta l'ULTIMA richiesta.
# ⚠ E' la stessa regola del blocco `sweep` di `06-b35-lancia.sh`, ripresa
#   apposta identica: se cambiasse qui, i due banchi direbbero cose diverse
#   con lo stesso nome.
TELA_ATTESA = (1024, 640)


def leggi(percorso):
    with open(percorso, encoding="utf-8") as f:
        return json.load(f)


def giudica_uno(d):
    """(rotto, tela_finale, esiti) — la regola di `06-b35-lancia.sh sweep`."""
    tele = [v for v in d["controllo_dopo_sessione"] if v["tipo"] == "TELA"]
    due = tele[1:3]                 # la prima risponde alla tela di PARTENZA
    fin = (due[-1]["tela_l"], due[-1]["tela_a"]) if due else None
    esiti = [(v["esito"], v["motivo"]) for v in due]
    return (fin != TELA_ATTESA), fin, esiti


def ritmo(d):
    """La mediana dell'intervallo fra fotogrammi, in ms — il TESTIMONE.

    ⛔ Si scartano i primi tre: `LEZIONI.md` §1.4 / forma E9 — la
       distribuzione dell'avvio non e' quella del regime, e qui l'avvio porta
       dentro l'apertura del codificatore.
    """
    t = [f["t"] for f in d.get("fotogrammi", []) if f.get("t") is not None]
    t = t[3:]
    if len(t) < 5:
        return None, len(t)
    d_ms = [(b - a) * 1000.0 for a, b in zip(t, t[1:])]
    return statistics.median(d_ms), len(d_ms)


def raccogli(lavoro, prefisso, giri):
    rotti = tot = 0
    ritmi = []
    mancanti = []
    righe = []
    for r in range(1, giri + 1):
        p = os.path.join(lavoro, f"{prefisso}-r{r}.json")
        if not os.path.exists(p):
            mancanti.append(r)
            continue
        d = leggi(p)
        rotto, fin, esiti = giudica_uno(d)
        m, n = ritmo(d)
        if m is not None:
            ritmi.append(m)
        tot += 1
        rotti += 1 if rotto else 0
        righe.append(f"      r{r:<3d} {'ROTTO' if rotto else 'ok   '} "
                     f"tela finale {fin} · {esiti} · "
                     f"fuori misura {len(d.get('fotogrammi_fuori_misura', []))} · "
                     f"ritmo {('%.1f ms' % m) if m else '⛔ pochi fotogrammi'} "
                     f"su {n} intervalli")
    return {"rotti": rotti, "tot": tot, "ritmi": ritmi,
            "mancanti": mancanti, "righe": righe}


def stampa(nome, r, dettaglio):
    print(f"\n    {nome}")
    if r["mancanti"]:
        # ⛔ Un giro che non ha lasciato il suo file NON e' un giro «ok»:
        #    sparirebbe dal denominatore e il conto migliorerebbe da solo.
        print(f"      ⛔ MANCANO i giri {r['mancanti']}: il denominatore non e'"
              f" quello dichiarato")
    if r["tot"] == 0:
        print("      ⛔ NESSUNA MISURA — e «nessuna» non e' «zero rotti»")
        return
    if dettaglio:
        for x in r["righe"]:
            print(x)
    rit = r["ritmi"]
    print(f"      ⇒ ROTTI {r['rotti']} su {r['tot']}"
          + (f"  ·  ritmo mediano dei fotogrammi "
             f"{statistics.median(rit):.1f} ms (n={len(rit)} giri)"
             if rit else "  ·  ⛔ nessun ritmo misurabile"))


def confronta(c, s):
    """Il verdetto, e il rifiuto di darlo quando la contesa non ha morso."""
    print("\n" + "=" * 74)
    if c["tot"] == 0 or s["tot"] == 0:
        print("⛔ Manca una delle due meta': non c'e' paragone da fare.")
        return 3
    if not c["ritmi"] or not s["ritmi"]:
        print("⛔ Senza il ritmo dei fotogrammi non si sa se la contesa e'"
              " arrivata al prodotto: NIENTE VERDETTO.")
        return 3
    rc = statistics.median(c["ritmi"])
    rs = statistics.median(s["ritmi"])
    print(f"⭐ IL TESTIMONE — il ritmo dei fotogrammi visto dal client:")
    print(f"      a riposo        {rs:.1f} ms")
    print(f"      sotto contesa   {rc:.1f} ms   ({rc / rs:.2f}×)")
    # ⛔ La soglia si dichiara PRIMA e larga: serve a smascherare una contesa
    #    che NON ha morso, non a misurare quanto ha morso.
    if rc < rs * 1.15:
        print("\n⛔⛔ LA CONTESA NON HA TOCCATO IL PRODOTTO (meno del 15 % di")
        print("    dilatazione).  ⇒ NIENTE VERDETTO: un «0 su 18» con")
        print("    l'etichetta «sotto contesa GPU» sarebbe un verde per")
        print("    costruzione, e §5.2 racconta di sei banchi finiti cosi'.")
        print("    ⚠ Che cosa guardare: l'utente della sessione e' nel gruppo")
        print("      `render`?  I codificatori del carico erano vivi per tutto")
        print("      il giro (`06-b39-contesa.sh stato`)?")
        return 4
    print(f"\n⭐ La contesa E' arrivata al prodotto: i fotogrammi si sono"
          f" diradati di {(rc / rs - 1) * 100:.0f} %.")
    print(f"\n   IL VERDETTO")
    print(f"      sotto contesa GPU : ROTTI {c['rotti']} su {c['tot']}")
    print(f"      a riposo          : ROTTI {s['rotti']} su {s['tot']}")
    if c["rotti"] > s["rotti"]:
        print(f"\n⭐⭐ LA CONTESA RIPRODUCE IL DIFETTO: {c['rotti']} contro"
              f" {s['rotti']}.  ⇒ Il 4/18 del 16 agosto aveva la sua causa"
              f" qui, e il verde del 17 vale «a macchina ferma».")
        return 0
    if c["rotti"] == 0 and s["rotti"] == 0:
        print("\n⛔ ZERO ROTTI ANCHE SOTTO CONTESA — e la contesa c'era, misurata.")
        print("   ⇒ Quel che il 16 agosto ruppe le richieste incatenate NON e'")
        print("     la sola contesa sulla GPU.  ⚠ Quel che questa scena non")
        print("     ricrea resta in piedi: cinque compositori, cinque PipeWire,")
        print("     cinque sessioni.  ⛔ E il 4/18 resta NON RIPRODOTTO: non si")
        print("     promuove a «curato».")
        return 0
    print("\n⚠ I rotti non aumentano sotto contesa: la contesa GPU non e' la"
          " variabile.")
    return 0


# ===========================================================================
# ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO
# ===========================================================================
def _finta(tela, passo_ms, n=40):
    return {
        "controllo_dopo_sessione": [
            {"tipo": "TELA", "esito": "ADATTATA", "motivo": 0,
             "tela_l": 1280, "tela_a": 800},
            {"tipo": "TELA", "esito": "RIFIUTATA", "motivo": 3,
             "tela_l": 1280, "tela_a": 800},
            {"tipo": "TELA", "esito": "ADATTATA", "motivo": 0,
             "tela_l": tela[0], "tela_a": tela[1]},
        ],
        "fotogrammi": [{"n": i, "t": i * passo_ms / 1000.0} for i in range(n)],
        "fotogrammi_fuori_misura": [],
    }


def controllo():
    import tempfile
    print("⭐ CONTROLLO POSITIVO DELLO STRUMENTO — misure finte, risposta nota\n")
    guai = []

    def prova(nome, atteso, funzione):
        avuto = funzione()
        segno = "OK " if avuto == atteso else "⛔ "
        print(f"    {segno} {nome}: atteso {atteso} · avuto {avuto}")
        if avuto != atteso:
            guai.append(nome)

    with tempfile.TemporaryDirectory() as d:
        # scena A · la contesa morde (ritmo 16,7 → 40 ms) e rompe 3 giri su 6
        for r in range(1, 7):
            tela = (1600, 900) if r <= 3 else TELA_ATTESA
            json.dump(_finta(tela, 40.0),
                      open(os.path.join(d, f"06-b39-contesa-r{r}.json"), "w"))
            json.dump(_finta(TELA_ATTESA, 16.7),
                      open(os.path.join(d, f"06-b39-riposo-r{r}.json"), "w"))
        c = raccogli(d, "06-b39-contesa", 6)
        s = raccogli(d, "06-b39-riposo", 6)
        prova("A · rotti sotto contesa", 3, lambda: c["rotti"])
        prova("A · rotti a riposo", 0, lambda: s["rotti"])
        prova("A · ritmo sotto contesa (ms)", 40.0,
              lambda: round(statistics.median(c["ritmi"]), 1))
        prova("A · il verdetto ESCE (0 = detto)", 0, lambda: confronta(c, s))

    with tempfile.TemporaryDirectory() as d:
        # scena B · ⛔ IL VELENO: la contesa NON morde (stesso ritmo), e lo
        #           strumento deve RIFIUTARSI di dare il verdetto — anche se i
        #           rotti sono zero e tutto sembra verde.
        for r in range(1, 7):
            json.dump(_finta(TELA_ATTESA, 16.7),
                      open(os.path.join(d, f"06-b39-contesa-r{r}.json"), "w"))
            json.dump(_finta(TELA_ATTESA, 16.7),
                      open(os.path.join(d, f"06-b39-riposo-r{r}.json"), "w"))
        c = raccogli(d, "06-b39-contesa", 6)
        s = raccogli(d, "06-b39-riposo", 6)
        prova("B · rotti (tutto verde in apparenza)", 0, lambda: c["rotti"])
        prova("B · ⭐ il verdetto viene RIFIUTATO (4)", 4, lambda: confronta(c, s))

    with tempfile.TemporaryDirectory() as d:
        # scena C · ⛔ un giro che non ha lasciato il file: il denominatore
        #           deve dirlo, non migliorare da solo.
        for r in range(1, 6):
            json.dump(_finta(TELA_ATTESA, 16.7),
                      open(os.path.join(d, f"06-b39-contesa-r{r}.json"), "w"))
        c = raccogli(d, "06-b39-contesa", 6)
        prova("C · giri mancanti dichiarati", [6], lambda: c["mancanti"])
        prova("C · denominatore vero", 5, lambda: c["tot"])

    print()
    if guai:
        print(f"⛔ CONTROLLO POSITIVO FALLITO su {len(guai)}: {guai}")
        return 1
    print("⭐ CONTROLLO POSITIVO SUPERATO: lo strumento vede il difetto quando"
          " c'e',\n   e RIFIUTA il verde quando la contesa non ha morso.")
    return 0


def main():
    p = argparse.ArgumentParser(description="06-b39 — il verdetto sotto contesa")
    p.add_argument("lavoro", nargs="?", help="la cartella con i .json")
    p.add_argument("--giri", type=int, default=18)
    p.add_argument("--dettaglio", action="store_true", default=True)
    p.add_argument("--controllo", action="store_true")
    a = p.parse_args()
    if a.controllo:
        return controllo()
    if not a.lavoro:
        p.error("serve la cartella di lavoro, oppure --controllo")
    if not os.path.isdir(a.lavoro):
        print(f"⛔ «{a.lavoro}» non e' una cartella")
        return 3
    c = raccogli(a.lavoro, "06-b39-contesa", a.giri)
    s = raccogli(a.lavoro, "06-b39-riposo", a.giri)
    stampa("SOTTO CONTESA GPU (5 codificatori sullo stesso iGPU)", c, a.dettaglio)
    stampa("A RIPOSO (stessa ora, stesso albero)", s, a.dettaglio)
    return confronta(c, s)


if __name__ == "__main__":
    sys.exit(main())
