#!/usr/bin/env python3
"""06-b42-verdetto.py — ⭐⭐ IL VERDETTO DELLA 6.3 SOTTO CONTESA DI COMPOSITORI,
e ⛔ soprattutto **il rifiuto di darlo** quando la scena non ha morso.

    python3 06-b42-verdetto.py <cartella> --giri 18 \\
            --certificato <file> --vitalita <file>
    python3 06-b42-verdetto.py --controllo    ⭐ il controllo positivo dello
                                              STRUMENTO, su misure finte

===========================================================================
⛔⛔ IL PUNTO NON E' CONTARE I ROTTI
===========================================================================

Quello lo sa fare anche il blocco `sweep` di `06-b35-lancia.sh`.  Il punto e'
che questo programma **si rifiuta** di stampare un verdetto se non gli si
dimostra, con **quattro numeri distinti**, che la scena era quella dichiarata:

  1. ⭐ **il certificato della scena** — la sonda del compositore
     (`06-b42-sonda-compositore.py`) deve aver visto il ciclo principale di
     Mutter **dilatarsi** con i contendenti accesi.  Senza certificato non si
     misura: e' `fasi/06 §5.8`, la regola che ha salvato la finestra di ieri
     notte;
  2. ⭐ **la vitalita' dei contendenti** — ogni sessione di contesa deve aver
     **consumato CPU** per tutta la meta' «sotto contesa».  ⛔ Una
     `gnome-shell --headless` senza nessuno attaccato **non compone niente**:
     starebbe li' ferma, `pgrep` la conterebbe, e «cinque compositori»
     sarebbero cinque processi immobili.  E' la forma **E1**;
  3. ⭐ **il testimone del fotogramma** — il ritmo visto dal *client*.  Se
     sotto contesa i fotogrammi non si diradano, la contesa **non e' arrivata
     al prodotto**, e uno `0 su 18` con l'etichetta «sotto contesa» sarebbe un
     **verde per costruzione**.  E' la stessa regola di `06-b41-verdetto.py`,
     ripresa identica apposta;
  4. ⭐ **il denominatore** — un giro che non ha lasciato il suo file non e' un
     giro «ok»: sparirebbe dal conto e il risultato migliorerebbe da solo.

⚠ E i quattro sono **congiunti**: basta che uno manchi e non esce nessun
  numero con un'etichetta addosso.  ⛔ Un'etichetta senza la cosa e' peggio di
  nessuna misura, perche' sopravvive nei documenti.

===========================================================================
⛔ CHE COSA QUESTO BANCO NON PUO' DIRE
===========================================================================

Se il 4/18 **non** torna, la conclusione onesta e' *«nemmeno cinque sessioni
grafiche bastano»*, ⛔ **non** *«la scena del 16 agosto era innocua»*.  Quel
giorno c'erano cinque banchi che facevano ciascuno una cosa diversa: qui ce ne
sono cinque che fanno tutti la stessa.

⚠ Il ferro: **Intel UHD 730 integrata**, 20 core.  Ogni numero col carico
  accanto.
"""
import argparse
import json
import os
import statistics
import sys

# La tela finale attesa: chi trascina un bordo si aspetta l'ULTIMA richiesta.
# ⚠ Identica a `06-b35-lancia.sh sweep` e a `06-b41-verdetto.py`: se cambiasse
#   qui, tre banchi direbbero cose diverse con lo stesso nome (forma E2).
TELA_ATTESA = (1024, 640)

# ⛔ Le soglie si dichiarano PRIMA, e sono LARGHE apposta: servono a smascherare
#    una contesa **assente**, non a misurarne la grandezza.
DILATAZIONE_MINIMA = 1.15        # il ritmo dei fotogrammi visto dal client
QUOTA_CPU_MINIMA = 0.05          # ogni contendente: >= 5 % di un core


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
    """La mediana dell'intervallo fra fotogrammi, in ms — IL TESTIMONE.

    ⛔ Si scartano i primi tre (`LEZIONI.md` §1.4, forma E9): la distribuzione
       dell'avvio non e' quella del regime, e l'avvio porta dentro l'apertura
       del codificatore.
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


# ===========================================================================
# I TRE CANCELLI, prima del verdetto
# ===========================================================================
def cancello_certificato(cert):
    """⭐ 1 · la sonda del compositore ha visto la dilatazione?"""
    print("\n  CANCELLO 1 — la scena e' certificata?")
    if cert is None:
        print("      ⛔ NESSUN CERTIFICATO: non e' stato dimostrato che cinque")
        print("        sessioni rallentino il compositore.  ⇒ NIENTE VERDETTO.")
        return False
    if not cert.get("certificata"):
        print(f"      ⛔ CERTIFICATO NEGATIVO: {cert.get('motivo', '(senza motivo)')}")
        print("        ⇒ NIENTE VERDETTO: la scena non contende quel che dice.")
        return False
    print(f"      OK  {cert.get('motivo', '')}")
    return True


def cancello_vitalita(vit):
    """⭐ 2 · i contendenti hanno LAVORATO, o erano solo accesi?"""
    print("\n  CANCELLO 2 — i contendenti hanno composto davvero?")
    if vit is None:
        print("      ⛔ NESSUNA MISURA DI VITALITA': cinque processi accesi non")
        print("        sono cinque compositori al lavoro (forma E1).")
        return False
    sess = vit.get("sessioni", [])
    if not sess:
        print("      ⛔ ZERO contendenti nella misura di vitalita'.")
        return False
    guai = []
    for s in sess:
        q_shell = s.get("quota_shell", 0.0)
        q_figlio = s.get("quota_figlio", 0.0)
        segno = "OK " if (q_shell >= QUOTA_CPU_MINIMA
                          and q_figlio >= QUOTA_CPU_MINIMA) else "⛔ "
        print(f"      {segno} {s.get('utente')}: gnome-shell"
              f" {q_shell * 100:.1f} % di un core · figlio"
              f" {q_figlio * 100:.1f} %")
        if q_shell < QUOTA_CPU_MINIMA or q_figlio < QUOTA_CPU_MINIMA:
            guai.append(s.get("utente"))
    if guai:
        print(f"      ⛔ {len(guai)} contendenti sotto il {QUOTA_CPU_MINIMA * 100:.0f} %"
              f" di un core: {guai}")
        print("        ⇒ Erano ACCESI, non al lavoro.  NIENTE VERDETTO.")
        return False
    print(f"      ⇒ tutti e {len(sess)} sopra la soglia dichiarata")
    return True


def cancello_testimone(c, s):
    """⭐ 3 · la contesa e' arrivata FINO AL PRODOTTO?"""
    print("\n  CANCELLO 3 — la contesa e' arrivata al prodotto?")
    if not c["ritmi"] or not s["ritmi"]:
        print("      ⛔ senza il ritmo dei fotogrammi non si sa: NIENTE VERDETTO.")
        return False, None, None
    rc = statistics.median(c["ritmi"])
    rs = statistics.median(s["ritmi"])
    print(f"      il ritmo dei fotogrammi visto dal client:")
    print(f"          a riposo        {rs:.1f} ms")
    print(f"          sotto contesa   {rc:.1f} ms   ({rc / rs:.2f}×)")
    if rc < rs * DILATAZIONE_MINIMA:
        print(f"      ⛔⛔ MENO DEL {(DILATAZIONE_MINIMA - 1) * 100:.0f} % DI"
              " DILATAZIONE: la contesa non ha toccato il prodotto.")
        print("        ⇒ NIENTE VERDETTO — un «0 su 18» con l'etichetta «sotto")
        print("          contesa» sarebbe un verde per costruzione, e §5.2")
        print("          racconta di sei banchi finiti cosi'.")
        return False, rc, rs
    print(f"      OK  i fotogrammi si sono diradati del {(rc / rs - 1) * 100:.0f} %")
    return True, rc, rs


def cancello_denominatore(c, s, giri):
    """⭐ 4 · il conto e' confrontabile col 4 su 18 del 16 agosto?

    ⛔ Un «0 su 4» non si confronta con un «4 su 18»: se meno di due terzi dei
       giri hanno lasciato il loro file, la meta' non e' quella dichiarata e il
       denominatore migliorerebbe da solo.  ⚠ E i giri persi non sono neutri:
       un giro che non parte e' spesso proprio quello in cui qualcosa e' andato
       storto.
    """
    print("\n  CANCELLO 4 — il denominatore e' quello dichiarato?")
    minimo = (giri * 2 + 2) // 3
    esito = True
    for nome, r in (("sotto contesa", c), ("a riposo", s)):
        segno = "OK " if r["tot"] >= minimo else "⛔ "
        print(f"      {segno} {nome}: {r['tot']} giri su {giri} dichiarati"
              f" (minimo {minimo})")
        if r["tot"] < minimo:
            esito = False
    if not esito:
        print("      ⛔ Una meta' ha perso troppi giri: NIENTE VERDETTO.")
    return esito


def confronta(c, s, cert, vit, giri=None):
    print("\n" + "=" * 74)
    if c["tot"] == 0 or s["tot"] == 0:
        print("⛔ Manca una delle due meta': non c'e' paragone da fare.")
        return 3
    if giri is None:
        giri = max(c["tot"] + len(c["mancanti"]), s["tot"] + len(s["mancanti"]))
    buoni = 0
    buoni += 1 if cancello_certificato(cert) else 0
    buoni += 1 if cancello_vitalita(vit) else 0
    ok3, rc, rs = cancello_testimone(c, s)
    buoni += 1 if ok3 else 0
    buoni += 1 if cancello_denominatore(c, s, giri) else 0
    if buoni < 4:
        print("\n" + "=" * 74)
        print(f"⛔⛔ {4 - buoni} CANCELLI SU 4 NON PASSATI: **NIENTE VERDETTO**.")
        print("    Non scrivo «N su 18 sotto contesa di compositori»: sarebbe")
        print("    l'etichetta senza la cosa.")
        return 4

    print("\n" + "=" * 74)
    print("   IL VERDETTO")
    print(f"      sotto contesa (5 sessioni grafiche) : ROTTI {c['rotti']} su {c['tot']}")
    print(f"      a riposo (1 sessione, stessa ora)   : ROTTI {s['rotti']} su {s['tot']}")
    if c["rotti"] > s["rotti"]:
        print(f"\n⭐⭐ LA CONTESA RIPRODUCE IL DIFETTO: {c['rotti']} contro"
              f" {s['rotti']}.\n   ⇒ Il 4/18 del 16 agosto ha la sua causa nella"
              f" contesa fra sessioni\n     grafiche, e il verde del 17 vale «a"
              f" macchina ferma».")
        return 0
    if c["rotti"] == 0 and s["rotti"] == 0:
        print("\n⛔ ZERO ROTTI ANCHE SOTTO CONTESA — e la contesa c'era,"
              " certificata su tre\n   numeri distinti.")
        print("   ⇒ **Nemmeno cinque sessioni grafiche riproducono il 4/18.**"
              "  E' la SECONDA\n     causa esclusa con la misura, dopo l'iGPU"
              " (§5.8).")
        print("   ⛔ E il 4/18 resta NON RIPRODOTTO: non si promuove a «curato»")
        print("     ne' a «spiegato».  ⚠ Quel che questa scena NON ricrea:"
              " cinque banchi\n     che fanno cinque cose DIVERSE, e i loro"
              " client dal browser.")
        return 0
    print("\n⚠ I rotti non aumentano sotto contesa: la contesa fra sessioni"
          " grafiche non\n  e' la variabile che li muove.")
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


CERT_BUONO = {"certificata": True, "motivo": "p95 del ciclo di Mutter 3,1×"}
CERT_CATTIVO = {"certificata": False, "motivo": "p95 fermo (1,01×)"}
VIT_BUONA = {"sessioni": [{"utente": f"provac{i}", "quota_shell": 0.40,
                           "quota_figlio": 0.55} for i in range(2, 6)]}
VIT_MORTA = {"sessioni": [{"utente": "provac2", "quota_shell": 0.001,
                           "quota_figlio": 0.0}] +
                         [{"utente": f"provac{i}", "quota_shell": 0.40,
                           "quota_figlio": 0.55} for i in range(3, 6)]}


def _scena(d, tele_contesa, passo_contesa, passo_riposo, n=6):
    for r in range(1, n + 1):
        tela = tele_contesa(r)
        json.dump(_finta(tela, passo_contesa),
                  open(os.path.join(d, f"06-b42-contesa-r{r}.json"), "w"))
        json.dump(_finta(TELA_ATTESA, passo_riposo),
                  open(os.path.join(d, f"06-b42-riposo-r{r}.json"), "w"))
    return raccogli(d, "06-b42-contesa", n), raccogli(d, "06-b42-riposo", n)


def controllo():
    import tempfile
    print("⭐ CONTROLLO POSITIVO DELLO STRUMENTO — misure finte, risposta nota\n")
    guai = []

    def prova(nome, atteso, funzione):
        avuto = funzione()
        segno = "OK " if avuto == atteso else "⛔ "
        print(f"\n[{segno}] {nome}: atteso {atteso} · avuto {avuto}")
        if avuto != atteso:
            guai.append(nome)

    # A · tutto in regola, la contesa morde e rompe 3 giri su 6 ⇒ il verdetto ESCE
    with tempfile.TemporaryDirectory() as d:
        c, s = _scena(d, lambda r: (1600, 900) if r <= 3 else TELA_ATTESA, 40.0, 16.7)
        prova("A · rotti sotto contesa", 3, lambda: c["rotti"])
        prova("A · il verdetto ESCE (0)", 0, lambda: confronta(c, s, CERT_BUONO, VIT_BUONA))

    # B · ⛔ IL VELENO PRINCIPALE: la contesa NON morde (stesso ritmo) e tutto
    #     sembra verde.  Lo strumento deve RIFIUTARSI.
    with tempfile.TemporaryDirectory() as d:
        c, s = _scena(d, lambda r: TELA_ATTESA, 16.7, 16.7)
        prova("B · rotti (tutto verde in apparenza)", 0, lambda: c["rotti"])
        prova("B · ⭐ RIFIUTATO per il testimone (4)", 4,
              lambda: confronta(c, s, CERT_BUONO, VIT_BUONA))

    # C · ⛔ il certificato manca: rifiuto anche se il ritmo si e' dilatato
    with tempfile.TemporaryDirectory() as d:
        c, s = _scena(d, lambda r: TELA_ATTESA, 40.0, 16.7)
        prova("C · ⭐ RIFIUTATO senza certificato (4)", 4,
              lambda: confronta(c, s, None, VIT_BUONA))
        prova("C-bis · ⭐ RIFIUTATO col certificato NEGATIVO (4)", 4,
              lambda: confronta(c, s, CERT_CATTIVO, VIT_BUONA))

    # D · ⛔ un contendente era acceso ma fermo: rifiuto.  ⚠ E' la forma E1, ed
    #     e' l'unico cancello che nessun altro banco del progetto ha.
    with tempfile.TemporaryDirectory() as d:
        c, s = _scena(d, lambda r: TELA_ATTESA, 40.0, 16.7)
        prova("D · ⭐ RIFIUTATO con un contendente FERMO (4)", 4,
              lambda: confronta(c, s, CERT_BUONO, VIT_MORTA))
        prova("D-bis · ⭐ RIFIUTATO senza misura di vitalita' (4)", 4,
              lambda: confronta(c, s, CERT_BUONO, None))

    # E · ⛔ un giro senza file: il denominatore lo deve dire
    with tempfile.TemporaryDirectory() as d:
        for r in range(1, 6):
            json.dump(_finta(TELA_ATTESA, 16.7),
                      open(os.path.join(d, f"06-b42-contesa-r{r}.json"), "w"))
        c = raccogli(d, "06-b42-contesa", 6)
        prova("E · giri mancanti dichiarati", [6], lambda: c["mancanti"])
        prova("E · denominatore vero", 5, lambda: c["tot"])

    # F · ⛔ zero giri raccolti: «nessuna misura» non e' «zero rotti»
    with tempfile.TemporaryDirectory() as d:
        c = raccogli(d, "06-b42-contesa", 6)
        s = raccogli(d, "06-b42-riposo", 6)
        prova("F · ⭐ nessuna meta' ⇒ nessun paragone (3)", 3,
              lambda: confronta(c, s, CERT_BUONO, VIT_BUONA))

    # G · ⛔ il denominatore franato: 3 giri su 18 non si confrontano col 4/18
    with tempfile.TemporaryDirectory() as d:
        for r in range(1, 4):
            json.dump(_finta(TELA_ATTESA, 40.0),
                      open(os.path.join(d, f"06-b42-contesa-r{r}.json"), "w"))
        for r in range(1, 19):
            json.dump(_finta(TELA_ATTESA, 16.7),
                      open(os.path.join(d, f"06-b42-riposo-r{r}.json"), "w"))
        c = raccogli(d, "06-b42-contesa", 18)
        s = raccogli(d, "06-b42-riposo", 18)
        prova("G · ⭐ RIFIUTATO con 3 giri su 18 (4)", 4,
              lambda: confronta(c, s, CERT_BUONO, VIT_BUONA, 18))

    print("\n" + "=" * 74)
    if guai:
        print(f"⛔ CONTROLLO POSITIVO FALLITO su {len(guai)}: {guai}")
        return 1
    print("⭐ CONTROLLO POSITIVO SUPERATO: lo strumento vede il difetto quando"
          " c'e',\n   e RIFIUTA il verde per tutti e tre i motivi per cui una"
          " scena puo' essere\n   finta — non certificata, contendenti fermi,"
          " contesa che non arriva.")
    return 0


def main():
    p = argparse.ArgumentParser(description="06-b42 — il verdetto sotto contesa di compositori")
    p.add_argument("lavoro", nargs="?")
    p.add_argument("--giri", type=int, default=18)
    p.add_argument("--certificato", default="")
    p.add_argument("--vitalita", default="")
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
    cert = leggi(a.certificato) if a.certificato and os.path.exists(a.certificato) else None
    vit = leggi(a.vitalita) if a.vitalita and os.path.exists(a.vitalita) else None
    c = raccogli(a.lavoro, "06-b42-contesa", a.giri)
    s = raccogli(a.lavoro, "06-b42-riposo", a.giri)
    stampa("SOTTO CONTESA (5 sessioni grafiche: gnome-shell + PipeWire + scena)", c, a.dettaglio)
    stampa("A RIPOSO (la sola sessione misurata, stessa ora)", s, a.dettaglio)
    return confronta(c, s, cert, vit, a.giri)


if __name__ == "__main__":
    sys.exit(main())
