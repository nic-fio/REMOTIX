#!/usr/bin/env python3
"""01-p5-guasto-catalogo.py — il guasto **del catalogo** in una copia DICHIARATA.

    python3 01-p5-guasto-catalogo.py stato   --sigla P5 --dove <file> [--catalogo <01-b12-guasti.py>]
    python3 01-p5-guasto-catalogo.py innesta --sigla P5 --dove <file>
    python3 01-p5-guasto-catalogo.py togli   --sigla P5 --dove <file>

  0  fatto (o: e' gia' cosi')   ·   1  non fatto   ·   3  non ho potuto guardare

===========================================================================
⛔ PERCHE' ESISTE — IL CATALOGO NOMINA UN ALBERO CHE E' DI UN SERVER VIVO

`01-b12-guasti.py` scrive il bersaglio del guasto **P5** in chiaro:

    dove = 01-b12-copie/p5-remotix/pagina.c

⛔ E quell'albero, il 12 agosto 2026, e' l'albero del server acceso sulla
**7501** — il bersaglio di P5 di una sessione precedente, che il mandato di
oggi dice di non toccare.  Innestarci dentro un guasto e ricostruirlo vorrebbe
dire cambiare i byte sotto i piedi di un server che qualcun altro ha lasciato
acceso apposta: e' esattamente la ragione per cui la voce P5 del catalogo dice
gia' *«il guasto va in una COPIA, mai nel prodotto»* — solo che qui la copia
del catalogo e' diventata a sua volta un server vivo.

⇒ Serve poter innestare **lo stesso guasto** in **un'altra copia**.

===========================================================================
⛔ E LE STRINGHE NON SI RICOPIANO: SI LEGGONO DAL CATALOGO

Questa e' la meta' che conta.  ⛔ Un innesto «a mano» che ricopia l'appiglio e
il sostituto crea **due verita' sullo stesso guasto**, ed e' la forma **E2** di
`REVIEWER.md` §2 — due comportamenti sotto la stessa etichetta.  E' gia'
successo, oggi, in questa stessa area: `01-p5-guasto-ritiro.py` era nato con
`MARCA = "[GUASTO-B12]"` mentre il catalogo usa `"REMOTIX B12 GUASTO"`, e il
`--togli` dell'uno **non riconosceva** l'innesto dell'altro — cioe' avrebbe
detto «tolto» su un file ancora guasto.

⭐ Qui `appiglio`, `sostituto` e `marca` arrivano da `GUASTI[sigla]` del
   catalogo, importato come modulo.  ⇒ Se il catalogo cambia una virgola, questo
   attrezzo cambia con lui **senza che nessuno se ne ricordi**, e il `--togli`
   del catalogo riconosce l'innesto di qui.
⚠ Quel che questo attrezzo cambia rispetto a `--applica` e' **una cosa sola**:
  il percorso.  Tutto il resto e' del catalogo.

===========================================================================
⛔ CHE COSA QUESTA DIFFERENZA COSTA, DETTO INVECE CHE TACIUTO

La certificazione che ne esce dice *«il banco P5 vede il guasto P5 del
catalogo»*, ⛔ e **non** dice *«…innestato dove il catalogo lo scrive»*.  Sono
due frasi diverse e la seconda e' piu' forte.  ⇒ La scena va dichiarata a
`--giudica --scena`, che e' il posto in cui il difetto **D6** ha messo apposta
questa informazione.

⭐ E che i due bersagli portino gli stessi byte non e' dedotto: `[M]` 12 agosto
   2026, `sha256(pagina.c)` = `930b611a906e8051…` su tutt'e tre le copie —
   quella del catalogo (`01-b12-copie/p5-remotix/`), quella usata qui
   (`01-p5-copia-7522/`) e il prodotto (`remotix/`).  ⚠ Ed e' questo attrezzo
   a riverificarlo: `stato` stampa l'impronta del file su cui sta per lavorare,
   e chi legge la puo' confrontare invece di crederci.

===========================================================================
⛔ IL PRODOTTO DI CASA NON SI TOCCA — e non e' un commento, e' un rifiuto

Come in `01-p5-guasto-ritiro.py`: l'elenco dei percorsi vietati sta **nel
programma** (invariante **I7** — la protezione di un difetto noto sta nel
programma, non in una riga che si puo' perdere).  ⛔ E ci sta dentro anche
l'albero del catalogo, per la ragione scritta in cima: oggi e' un server vivo,
e chi volesse innestarci deve usare `01-b12-guasti.py --applica`, che e' lo
strumento di chi quel server lo possiede.
"""
import argparse
import hashlib
import importlib.util
import os
import shutil
import sys

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ I percorsi su cui questo attrezzo si RIFIUTA di lavorare.  ⚠ Si confronta
#    il percorso REALE (`realpath`), non quello scritto: un collegamento
#    simbolico che punta al prodotto arriverebbe qui con un altro nome.
VIETATI = (
    # il prodotto di casa, dalle due macchine
    "/media/REMOTIX/src/remotix/pagina.c",
    "/srv/src/remotix/pagina.c",
    "/media/REMOTIX/src/remotix/pagina.html",
    "/srv/src/remotix/pagina.html",
    # ⛔ e l'albero del catalogo: il 12 agosto 2026 e' il server della 7501
    "/media/REMOTIX/src/01-b12-copie/p5-remotix/pagina.c",
    "/srv/src/01-b12-copie/p5-remotix/pagina.c",
)


def impronta_file(p):
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def catalogo(percorso):
    """(modulo, errore).  ⛔ Uno dei due e' sempre None."""
    try:
        spec = importlib.util.spec_from_file_location("b12catalogo", percorso)
        if spec is None or spec.loader is None:
            return None, f"⛔ «{percorso}» non si e' potuto caricare"
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m, None
    except Exception as sbaglio:  # noqa: BLE001 — il tipo dell'errore E' la misura
        return None, f"⛔ {type(sbaglio).__name__}: {sbaglio}"


def leggi(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError as sbaglio:
        print(f"NO  ⛔ «{p}» non si legge: {sbaglio}")
        print("    Non e' «il guasto non c'e'»: e' «non ho potuto guardare».")
        return None


def stato(g, marca, dove):
    """'sano' · 'guasto' · None (e None e' il terzo caso, non un no)."""
    testo = leggi(dove)
    if testo is None:
        return None
    c_sano = testo.count(g["appiglio"])
    c_guasto = testo.count(g["sostituto"])
    residue = testo.count(marca)
    print(f"--  {dove}")
    print(f"--  sha256: {impronta_file(dove)}")
    print(f"--  appiglio del catalogo: {c_sano} volta/e · sostituto: {c_guasto} "
          f"volta/e · marche «{marca}» residue: {residue}")
    # ⛔ I conteggi si stampano tutt'e tre, sempre: un file che non avesse ne'
    #    l'uno ne' l'altro e' un TERZO caso — la copia non e' quella su cui
    #    questo guasto e' scritto — e allora non si innesta e non si toglie.
    if c_sano == 1 and c_guasto == 0 and residue == 0:
        print("OK  SANO")
        return "sano"
    if c_sano == 0 and c_guasto == 1 and residue == 1:
        print("OK  GUASTO innestato")
        return "guasto"
    print("NO  ⛔ NE' L'UNO NE' L'ALTRO: questa copia non e' quella su cui il")
    print("    guasto del catalogo e' scritto.  ⛔ Non innesto e non tolgo: un")
    print("    innesto «riuscito senza fare niente» e' la settima veste di")
    print("    LEZIONI.md §1.9, e questo attrezzo esiste per non farla.")
    return None


def a_parte(dove, sigla):
    return f"{dove}.guasto-{sigla}-originale"


def innesta(g, marca, dove, sigla):
    if stato(g, marca, dove) != "sano":
        return 1
    orig = a_parte(dove, sigla)
    prima = impronta_file(dove)
    shutil.copy2(dove, orig)
    if impronta_file(orig) != prima:
        print("NO  ⛔ la copia messa da parte non ha l'impronta dell'originale")
        return 3
    with open(dove, encoding="utf-8") as f:
        testo = f.read()
    with open(dove, "w", encoding="utf-8") as f:
        f.write(testo.replace(g["appiglio"], g["sostituto"], 1))
    dopo = impronta_file(dove)
    if dopo == prima:
        print("NO  ⛔ il file non e' cambiato: l'innesto non e' avvenuto")
        return 1
    print(f"OK  innestato «{sigla}»   {prima[:16]}… → {dopo[:16]}…")
    print(f"--  l'originale sta in {orig}")
    print(f"⛔  E ADESSO CI VA QUEL CHE IL CATALOGO DICHIARA: costa «{g['costa']}»")
    print("    — per «ricostruisce» ci vanno costruisci.sh E il riavvio del")
    print("    bersaglio, o il giro misura il binario di prima con l'aria di")
    print("    aver innestato (il difetto n.2 del catalogo dei guasti).")
    return 0


def togli(g, marca, dove, sigla):
    orig = a_parte(dove, sigla)
    if not os.path.exists(orig):
        print(f"NO  ⛔ non c'e' nessun originale da parte ({orig}): non rimetto")
        print("    a posto per deduzione.  Se il guasto c'e', va tolto a mano e")
        print("    riverificato con «stato».")
        return 3
    voluta = impronta_file(orig)
    shutil.copy2(orig, dove)
    dopo = impronta_file(dove)
    if dopo != voluta:
        print(f"NO  ⛔ rimesso ma l'impronta non torna: {dopo} invece di {voluta}")
        return 1
    if stato(g, marca, dove) != "sano":
        print("NO  ⛔ l'impronta torna ma il file non e' sano: due cose che non")
        print("    possono essere vere insieme.  Non dichiaro riuscito niente.")
        return 1
    os.remove(orig)
    print(f"OK  tolto e riverificato: sha256 {dopo}")
    print("⛔  E anche qui ci va quel che «costa» dichiara, per la stessa ragione.")
    return 0


def principale():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("comando", choices=("stato", "innesta", "togli"))
    p.add_argument("--sigla", required=True,
                   help="la sigla nel catalogo di 01-b12-guasti.py (es. P5)")
    p.add_argument("--dove", required=True,
                   help="il file della COPIA bersaglio — mai il prodotto, mai "
                        "l'albero che il catalogo nomina")
    p.add_argument("--catalogo",
                   default=os.path.join(QUI, "01-b12-guasti.py"))
    a = p.parse_args()

    vero = os.path.realpath(a.dove)
    for vietato in VIETATI:
        if vero == vietato:
            print(f"NO  ⛔ «{vero}» E' UN ALBERO CHE NON SI TOCCA DA QUI.")
            print("    O e' il prodotto di casa, o e' l'albero che il catalogo")
            print("    nomina e che oggi porta un server acceso.  ⇒ Chi lo")
            print("    possiede usa «01-b12-guasti.py --applica»; questo")
            print("    attrezzo serve a innestare ALTROVE.  Non faccio niente.")
            return 2

    m, sbaglio = catalogo(a.catalogo)
    if m is None:
        print(f"NO  {sbaglio}")
        print("    ⛔ Senza il catalogo non ho le stringhe del guasto, e")
        print("       ricopiarle a mano sarebbe la seconda verita' che questo")
        print("       attrezzo esiste per non creare.")
        return 3
    g = getattr(m, "GUASTI", {}).get(a.sigla)
    if not g:
        print(f"NO  ⛔ sigla sconosciuta al catalogo: {a.sigla}")
        return 3
    marca = getattr(m, "MARCA", "REMOTIX B12 GUASTO")
    if not g.get("appiglio") or not g.get("sostituto"):
        print(f"NO  ⛔ «{a.sigla}» non ha appiglio e sostituto: e' un guasto di")
        print(f"    tipo «{g.get('costa')}», e da qui non si innesta.")
        return 3
    print(f"--  catalogo : {a.catalogo}")
    print(f"--  sigla    : {a.sigla} · costa «{g['costa']}»")
    print(f"--  dove il catalogo lo scriverebbe: {g['dove']}")
    print(f"--  dove lo innesto io            : {vero}")
    print(f"--  marca del guasto rosso        : «{g['marca']}»")

    if a.comando == "stato":
        return 0 if stato(g, marca, a.dove) else 1
    if a.comando == "innesta":
        return innesta(g, marca, a.dove, a.sigla)
    return togli(g, marca, a.dove, a.sigla)


if __name__ == "__main__":
    sys.exit(principale())
