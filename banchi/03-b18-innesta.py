#!/usr/bin/env python3
"""03-b18-innesta.py — ⛔ L'AGO NEL PRODOTTO, E SOLO NELLA COPIA.

  python3 03-b18-innesta.py --albero /srv/src/03-b18-src --elenco
  python3 03-b18-innesta.py --albero /srv/src/03-b18-src --ago fatale
  python3 03-b18-innesta.py --albero /srv/src/03-b18-src --togli

===========================================================================
⛔⭐ PERCHE' ESISTE — «UN CASO CHE PASSA E NON SA PIU' BOCCIARE E' ADDORMENTATO»

Il 13 agosto 2026 il caso «credito» di `03-b15-movimento.py` e' stato curato:
il credito si annuncia PRIMA della stretta di mano invece che dopo, e P6 e'
tornato verde.  ⛔ Ma un verde ottenuto togliendo la condizione invece di
reggerla non e' una cura, e un controllo che passa senza saper piu' bocciare
non e' curato: e' addormentato.  ⇒ Serve la prova che P6 e C3 e C6 sanno ancora
ARROSSIRE davanti a un prodotto che viola davvero la loro riga.

⛔ E il guasto si innesta in una COPIA dell'albero, MAI nel prodotto di casa:
   `--albero` e' un albero di lavoro del banco, e questo file rifiuta di
   toccare un albero che non porta la marca di una copia.

===========================================================================
⛔ IL METODO DI CASA: TRE GIRI, NON DUE

    sano  →  guasto  →  risanato

Il terzo e' quello che ci si dimentica, ed e' l'unico che ATTRIBUISCE il rosso
all'ago: con due soli giri un rosso venuto da qualunque altra differenza fra le
due costruzioni sembrerebbe l'ago.  ⚠ E vale la regola della marca in DUE
META': il giro guasto deve portare la marca **e il giro sano non la doveva gia'
portare**.
"""
import argparse
import os
import sys

# ⛔ I due gemelli: `rcp.c` sta in due cartelle dello stesso albero (rilievo
#    R12.3) e il `Makefile` FERMA la costruzione se divergono.  ⇒ L'ago si
#    pianta in tutt'e due, o il guasto non si compila nemmeno — e «non si
#    compila» e «non fa il danno» sono due fatti che non vanno confusi.
GEMELLI = ("src/rcp.c", "banchi/rcp/rcp.c")

MARCA = "/* ⛔ AGO DEL BANCO 03-b18 — NON E' IL PRODOTTO"


# --------------------------------------------------------------------------
# ⛔ GLI AGHI.  Ciascuno: che regola fa violare, chi lo deve vedere, e le due
#    stringhe — quel che c'e' e quel che ci va — testuali e ANCORATE.
#
# ⚠ Si sostituisce un testo ESATTO e si conta quante volte compare: se non e'
#   una sola volta, non si tocca niente.  Un `sed` che non trova niente esce 0
#   e lascia l'albero sano, e il banco misurerebbe il prodotto buono
#   credendo di misurare quello guasto — e' il difetto B11 del 10 agosto.

AGHI = {
    "fatale": {
        "regola": "RCP.md §2.3",
        "viola": ("«il server DEVE reggere il rifiuto di aprire uno stream "
                  "invece di considerarlo un errore fatale»"),
        "chi_lo_vede": "03-b15 P6-credito · 03-b18 C3-regge",
        "file": "src/rcp.c",
        "cerca": (
            "\t    s->video_numero, (unsigned long long)restano);\n"
        ),
        "mette": (
            "\t    s->video_numero, (unsigned long long)restano);\n"
            "\t" + MARCA + ", e viola §2.3 apposta: il\n"
            "\t *    rifiuto di aprire uno stream diventa un errore FATALE e la\n"
            "\t *    sessione si chiude.  Serve a far vedere che P6 e C3 sanno\n"
            "\t *    ancora bocciare. */\n"
            "\tcongeda(s, RCP_SESSIONE_NON_SERVIBILE,\n"
            "\t        \"il credito di stream e' finito\");\n"
            "\treturn;\n"
        ),
    },
    "b18": {
        "regola": "RCP.md §5.2",
        "viola": ("«quando il server abbandona un delta DEVE mandare un "
                  "fotogramma chiave appena puo', senza aspettare che il "
                  "client lo chieda»"),
        "chi_lo_vede": ("03-b18 C6-cura — e NESSUN ALTRO: la sessione regge, "
                        "il registro dice tutto, nessuna chiave viene "
                        "buttata, e intanto al decodificatore manca un delta "
                        "che non tornera' mai"),
        "file": "src/rcp.c",
        "cerca": (
            "\ts->serve_chiave = true;\n"
            "\ts->serve_chiave_perche = \"un delta e' stato saltato per mancanza di posto \"\n"
            "\t                         \"(§2.3), e nei numeri non resta nessun buco\";\n"
        ),
        "mette": (
            "\t" + MARCA + ": qui il debito di chiave NON si\n"
            "\t *    accende, ed e' il difetto B-18 come stava prima della cura del\n"
            "\t *    13 agosto 2026.  Un solo delta saltato e l'immagine resta\n"
            "\t *    sfasciata per sempre e in silenzio. */\n"
        ),
    },
}


def gemelli(albero):
    return [os.path.join(albero, g) for g in GEMELLI]


def e_una_copia(albero):
    """⛔ Si rifiuta di toccare un albero che non e' dichiaratamente di lavoro.

    ⚠ Il prodotto di casa sta in `<repo>/src` e in `/srv/src/remotix`: se un
      giorno un percorso sbagliato arrivasse qui, questo controllo e' l'unica
      cosa fra l'ago e il prodotto che sta per essere certificato.
    """
    n = os.path.basename(os.path.normpath(albero))
    return n.endswith("-src") and n.startswith("03-b18")


def stato(albero, ago=None):
    """Se i gemelli portano l'ago.  ⛔ Si CONTA, non si crede.

    ⛔⭐ E SI GUARDA **QUESTO** AGO, non «una marca qualunque» — difetto trovato
        al primo giro di questo file, e sarebbe stato caro.  La marca `MARCA` e'
        la stessa per tutti gli aghi: chiedendo solo di lei, togliere il primo
        di due aghi innestati rispondeva «c'e' ancora» e lo script si fermava
        credendo di non aver tolto niente.  ⚠ E' la forma «vuoto e proibito
        hanno la stessa faccia» applicata a due aghi diversi.
    """
    conto = []
    for p in gemelli(albero):
        try:
            with open(p, encoding="utf-8") as f:
                testo = f.read()
        except OSError:
            conto.append(None)
            continue
        conto.append(MARCA in testo if ago is None
                     else AGHI[ago]["mette"] in testo)
    return conto


def applica(albero, ago, togli):
    a = AGHI[ago]
    fatti = 0
    for p in gemelli(albero):
        try:
            with open(p, encoding="utf-8") as f:
                testo = f.read()
        except OSError as e:
            print(f"    ⛔ non ho letto {p}: {e}")
            return 2
        cerca, mette = (a["mette"], a["cerca"]) if togli else (a["cerca"], a["mette"])
        n = testo.count(cerca)
        if n != 1:
            print(f"    ⛔ in {p} il testo da sostituire compare {n} volte e non "
                  f"1: NON tocco niente.")
            print("       ⚠ «il sed non ha trovato niente» e «il guasto e'"
                  " innestato» hanno la stessa faccia, e questo controllo e'"
                  " l'unica cosa che li separa.")
            return 3
        with open(p, "w", encoding="utf-8") as f:
            f.write(testo.replace(cerca, mette))
        fatti += 1
        print(f"    OK  {p}")
    return 0 if fatti == len(GEMELLI) else 3


def principale():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--albero", default="/srv/src/03-b18-src",
                   help="⛔ l'albero di LAVORO, una copia: mai il prodotto di casa")
    p.add_argument("--ago", choices=sorted(AGHI), default="")
    p.add_argument("--togli", action="store_true",
                   help="⭐ il TERZO giro: si toglie l'ago e si ricostruisce")
    p.add_argument("--stato", action="store_true")
    p.add_argument("--elenco", action="store_true")
    a = p.parse_args()

    if a.elenco:
        print(__doc__)
        for nome, x in sorted(AGHI.items()):
            print(f"\n  {nome}")
            print(f"      viola     {x['regola']}: {x['viola']}")
            print(f"      lo vede   {x['chi_lo_vede']}")
        return 0

    if not e_una_copia(a.albero):
        print(f"⛔ «{a.albero}» non ha il nome di un albero di lavoro di questo "
              f"banco (03-b18…-src).")
        print("   ⚠ Il guasto si innesta nella COPIA, mai nel prodotto di casa: "
              "non tocco niente.")
        return 2

    if a.stato or not a.ago:
        for g, v in zip(GEMELLI, stato(a.albero)):
            dice = {True: "porta ALMENO un ago", False: "e' SANO",
                    None: "⛔ non l'ho potuto leggere"}[v]
            print(f"    --  {g}: {dice}")
        for nome in sorted(AGHI):
            s = stato(a.albero, nome)
            print(f"    --  ago «{nome}»: "
                  f"{'INNESTATO' if all(s) else 'non innestato'} "
                  f"({sum(1 for x in s if x)}/{len(GEMELLI)} gemelli)")
        if not a.ago:
            return 0

    print(f"\n{'TOLGO' if a.togli else 'INNESTO'} l'ago «{a.ago}» in {a.albero}")
    print(f"    --  viola {AGHI[a.ago]['regola']}: {AGHI[a.ago]['viola']}")
    e = applica(a.albero, a.ago, a.togli)
    if e:
        return e
    # ⛔ E si RILEGGE: «l'ho scritto» e «c'e' dentro» sono due fatti diversi.
    s = stato(a.albero, a.ago)
    atteso = not a.togli
    if all(x is atteso for x in s):
        print(f"    OK  riletto: tutti i gemelli "
              f"{'portano' if atteso else 'NON portano piu'''} la marca")
        return 0
    print("    ⛔ riletto: i gemelli NON sono nello stato che dovevano avere")
    return 3


if __name__ == "__main__":
    sys.exit(principale())
