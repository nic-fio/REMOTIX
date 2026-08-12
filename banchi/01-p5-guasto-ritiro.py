#!/usr/bin/env python3
"""01-p5-guasto-ritiro.py — ⛔ IL GUASTO DI P5 CHE COLPISCE **IL RITIRO**.

    python3 01-p5-guasto-ritiro.py stato   --pagina <percorso di pagina.html>
    python3 01-p5-guasto-ritiro.py innesta --pagina <percorso di pagina.html>
    python3 01-p5-guasto-ritiro.py togli   --pagina <percorso di pagina.html>

  0  fatto (o: e' gia' cosi')      1  non fatto      3  non ho potuto guardare

===========================================================================
⛔ PERCHE' ESISTE — IL GUASTO DI CATALOGO COPRIVA MENO DI QUEL CHE PROMETTEVA

Difetto **D11**, `fasi/rapporti/DIFETTI-12-agosto.md`.

Il guasto di P5 in `01-b12-guasti.py` mette nella pagina servita un'impronta
**ben formata e sbagliata** (`"AAAA…="` al posto di `p->cert->impronta`), e nel
suo titolo dichiara di coprire il rilievo **R1.14** di `RCP.md` §4.1-bis:

  > se l'impronta scritta nella pagina e quella del certificato di sessione
  > divergono, **la sessione WebTransport non si apre e nessun errore nomina
  > l'impronta**.

⛔ **Ma su questo prodotto quel guasto non uccide niente**, ed e' misurato: la
notte fra l'11 e il 12 agosto 2026 il giro col guasto e' uscito rosso con le
gambe `p-sessione` **CONFORMI** — la sessione si e' aperta lo stesso.  La
ragione e' del prodotto ed e' §4.1-bis applicato: `src/pagina.html` **ritira
`/impronta` prima di ogni tentativo** e usa quella, tenendo l'impronta servita
con la pagina solo come ripiego dichiarato.

⇒ Il guasto del valore fa virare il banco per la ragione **piu' debole**: prova
  che P5 vede la divergenza fra due stringhe, non che il difetto R1.14 sia
  coperto.  ⛔ E lascia scoperta la cosa che conta davvero: **un prodotto che
  smettesse di ritirare** — cioe' R1.14 vivo — sarebbe passato VERDE.

===========================================================================
⭐ CHE COSA FA QUESTO GUASTO, E PERCHE' UNA RIGA SOLA

Si toglie **il ritiro**, e si lascia il valore dov'e':

    const b64 = await impronta();      →   const b64 = IMPRONTA_SERVITA;

`impronta()` e' l'unico posto della pagina che chiede `/impronta` (`[R]`
`src/pagina.html`, funzione `impronta()`, e nessun altro `fetch` in tutto il
file).  Tolta quella chiamata, la pagina usa per sempre l'impronta che il
server le ha scritto dentro mentre la serviva — che e' precisamente il
prodotto che R1.14 descrive.

⛔ E IL GUASTO E' **PICCOLO APPOSTA**, cioe' un solo controllo si muove.  E' la
   lezione scritta accanto al guasto di P1 nel catalogo: un guasto che fa
   diventare rosso mezzo banco non prova che il banco veda *quella* cosa —
   prova solo che il giro e' andato male.  Qui:

     · la sessione WebTransport **si apre lo stesso**, perche' il server e'
       stato riacceso adesso e l'impronta servita e' fresca;
     · `pagina-servita`, `canale-controllo`, `credenziali`, `PAM`, `sessione`,
       il posto e il congedo restano tutti **verdi**;
     · l'unico controllo che vira e' `impronta-ritirata`, il passo nuovo di
       `01-p5-registro.py`, che conta `GET /impronta` nel segmento della gamba.

⭐ E che cosa questa certificazione DICE: che P5 vede sparire **la cura** con
   cui §4.1-bis chiude R1.14.  ⛔ Che cosa NON dice: non prova che la divergenza
   uccida la sessione — quello lo prova gia' l'altra gamba di P5, la **N1**,
   dove la sonda apre WebTransport con un'impronta storpiata di un byte e la
   sessione **fallisce**, su tutt'e due i motori.
   ⇒ Le due gambe insieme coprono R1.14 per intero: N1 dice *«un'impronta
     divergente uccide la sessione»*, questo passo dice *«e la pagina ne ritira
     una fresca prima di ogni tentativo»*.  Una sola delle due non basta, ed e'
     il difetto D11 detto in positivo.

===========================================================================
⛔ DOVE SI INNESTA — MAI NEL PRODOTTO

Nella **copia** che fa da bersaglio, e mai in `/media/REMOTIX/src/remotix/`:
riaccendere il prodotto di casa con un guasto dentro lo metterebbe sotto i
piedi di chiunque altro lo usasse, ed e' la stessa ragione scritta nella voce
P5 del catalogo dei guasti.

⭐ E COSTA UN RIACCENDIMENTO, NON UNA RICOSTRUZIONE — e la differenza e' letta,
   non stimata: `src/pagina.c:590` fa `p->html = leggi_file(file_html, …)`
   **una volta sola, all'accensione**, e poi serve quella copia in memoria.
   ⇒ `pagina.html` non entra in nessun binario: fra l'innesto e il giro ci va
   il **riavvio del bersaglio**, e NON `costruisci.sh`.
   ⚠ Chiamarlo «leggero» — cioe' «non serve niente in mezzo» — farebbe girare
     P5 contro la pagina di prima con l'aria di aver innestato, che e' il
     difetto n.2 del catalogo dei guasti.

⛔ E L'ORIGINALE SI METTE DA PARTE PRIMA, CON LA SUA IMPRONTA ACCANTO, e
   `togli` non si dichiara riuscito finche' l'impronta non e' tornata quella.
   E' la regola di `01-b12-guasti.py`: un `togli` che rimettesse un file senza
   sapere che impronta doveva avere non e' un ripristino, e' una speranza.

===========================================================================
⛔ E CHE IL GUASTO SIA ARRIVATO **SUL FILO** NON SI DEDUCE DAL FILE SU DISCO

Per i guasti di P1 e P5 il catalogo prova l'innesto con l'**impronta del
binario**, che cambia fra un passo e l'altro.  ⭐ Qui c'e' di meglio, ed e' piu'
diretto: la pagina si **chiede al server** e si guarda la riga.

    curl -sk https://192.168.0.2:<porta>/ | grep 'const b64'

  sano      `  const b64 = await impronta();`
  guasto    `  const b64 = IMPRONTA_SERVITA; /* [GUASTO-B12] P5-ritiro … */`

⚠ E si guarda DOPO aver riacceso: la riga giusta sul disco e la riga giusta sul
  filo sono due fatti diversi finche' il server non ha riletto il file, ed e'
  esattamente il difetto n.2 del catalogo (il guasto non innestato, con l'aria
  di esserlo).

===========================================================================
⭐⭐ LA CERTIFICAZIONE — `[M]` 12 agosto 2026, tre giri veri, `0 → 4 → 0`

Bersaglio: una COPIA del prodotto sulla **7522**, accesa apposta con prefisso,
ban e socket propri (`01-p5-copia-7522`, `PREFISSO=p5r-7522`).  ⛔ La 7501 non
e' stata toccata: e' il bersaglio gia' acceso di un altro giro, e spegnerla per
fare il proprio sarebbe stato togliere il banco da sotto i piedi a qualcun
altro.  Browser su CHUWI, schermo `:80`, Chrome 151 e Firefox 140.13.0esr.

  giro        uscita   n1 (×4)   gambe dalla pagina (×4)   la marca compare
  ─────────────────────────────────────────────────────────────────────────
  sano          0      ok ×4     CONFORME ×4                    0 volte
  guasto        1      ok ×4     NON-CONFORME ×4                4 volte
  risanato      0      ok ×4     CONFORME ×4                    0 volte

⭐ E IL ROSSO E' DI UN CONTROLLO SOLO, contato nel giro col guasto: la gamba
   `p-sessione` di Chrome fa **16 controlli, 1 guasto**; la `n2` **12 e 1**.
   Tutto il resto della stretta di mano resta verde — pagina servita, canale di
   controllo, negoziato, `CREDENZIALI`, PAM, `ammesso`, posto preso, `SESSIONE`,
   congedo per tutt'e due le strade, posto lasciato a zero.

⛔⭐ E LA COSA CHE VALE PIU' DEI COLORI: nel giro col guasto il controllo
    **vecchio** — *«la pagina pubblica la stessa impronta dell'endpoint»* — e'
    rimasto **VERDE**, perche' il valore non e' toccato.  ⇒ Il guasto del valore
    e questo guardano due cose diverse, e il vecchio e' **cieco** su un prodotto
    che smette di ritirare.  E' il difetto D11, dimostrato invece che raccontato.

⭐ Che il guasto sia entrato e poi uscito non e' dedotto dal colore del
   verdetto: lo dice la **pagina chiesta al server**, `sha256` del corpo servito
   — `a2cda27c…` → `3b0080b1…` → `a2cda27c…`, cioe' tornata identica byte per
   byte.  ⚠ Ed e' anche la prova che il certificato di sessione non ha ruotato
   fra un giro e l'altro: se avesse ruotato, la pagina servita sarebbe cambiata.

⛔ E CHE COSA QUESTA CERTIFICAZIONE **NON** DICE.  Col guasto dentro, la
   sessione WebTransport **si apre lo stesso** (`sessione` trovate=1, posto
   preso e lasciato): il server e' stato riacceso adesso, quindi l'impronta
   servita con la pagina e' fresca e coincide.  ⇒ Questo guasto prova che P5
   vede sparire **la cura**, non che la sessione muoia.  ⭐ Che la sessione
   muoia con un'impronta divergente lo prova la gamba **N1**, `[M]` gli stessi
   tre giri, quattro volte su quattro: impronta giusta APERTA, impronta
   storpiata di un byte NON-APERTA, su Chrome e su Firefox.
   ⇒ Le due gambe insieme fanno R1.14; nessuna delle due da sola.

⚠ La `[?]` che resta, scritta come non saputa: **la rotazione vera** non e'
  stata misurata.  Il prodotto che R1.14 descrive e' una scheda aperta da due
  settimane su un certificato ruotato, e per vederlo servirebbe far ruotare il
  certificato di sessione sotto una pagina gia' caricata.  ⛔ Non e' stato fatto,
  e questa nota non lo spaccia per fatto.

===========================================================================
⭐ LA VOCE PER `01-b12-guasti.py` — DA INCOLLARE, NON DA RISCRIVERE

⛔ Questo file non tocca il catalogo: `01-b12-guasti.py` e' del mandato **D10**
   (il registro unito a mano), e due agenti sullo stesso file si sovrascrivono.
   La voce sta qui perche' viaggi con l'attrezzo che la esegue.

    guasto(
        "P5R", "P5", "⛔ la pagina non RITIRA piu' l'impronta prima del "
                     "tentativo — la cura di §4.1-bis tolta, non il valore",
        "01-p5-copia-7522/pagina.html",   # ⚠ la COPIA bersaglio, mai il prodotto
        "  const b64 = await impronta();",
        "  const b64 = IMPRONTA_SERVITA; /* [GUASTO-B12] P5-ritiro — … */",
        "⛔ §4.1-bis, R1.14 …",
        # la marca — misurata, non scelta:
        "NESSUN RITIRO DI /impronta IN QUESTA GAMBA",
        "riaccendi",   # ⚠ vedi qui sotto
        "fasi/rapporti/DIFETTI-12-agosto.md D11 · RCP.md §4.1-bis (R1.14)",
    )

⚠ **`costa` vuole un genere nuovo**: `pagina.html` non entra in nessun binario,
  quindi «ricostruisce» fa compilare per niente, e «leggero» — che vuol dire
  «si applica e si gira» — farebbe misurare la pagina di prima.  ⭐ Il genere
  onesto e' **`riaccendi`**: fra l'innesto e il giro ci va il riavvio del
  bersaglio e nient'altro.  ⛔ Finche' non esiste, si metta `"ricostruisce"`:
  e' un SOVRAINSIEME (compila e riaccende), quindi sbaglia per eccesso — mai
  per difetto, che e' il verso in cui un guasto si perde.
"""
import argparse
import hashlib
import os
import shutil
import sys

# ⛔⭐ LA MARCA E LA RIGA SONO **QUELLE DEL CATALOGO**, byte per byte — cura del
#     12 agosto 2026, e nasce da un difetto trovato mentre si rifaceva la
#     certificazione per registrarla come si deve.
#
# Qui c'era `MARCA = "[GUASTO-B12]"`, inventata da questo file; il catalogo usa
# `MARCA = "REMOTIX B12 GUASTO"` (`01-b12-guasti.py:210`).  ⛔ Erano **due
# innesti diversi per lo stesso guasto**, ed e' la forma **E2** di
# `REVIEWER.md` — due comportamenti sotto la stessa etichetta:
#
#   · il `--togli` del catalogo conta le marche `REMOTIX B12 GUASTO` residue,
#     e sul mio innesto ne avrebbe contate **zero**: avrebbe detto «tolto» su
#     un file ancora guasto;
#   · e chi certificasse «a mano» e chi certificasse «dal catalogo» avrebbero
#     misurato due file diversi, chiamandoli con lo stesso nome.
#
# ⭐ Adesso la riga innestata da qui e quella che innesterebbe `--innesta P5R`
#    sono la **stessa stringa**, e il `togli` dell'uno riconosce l'innesto
#    dell'altro.  ⛔ Se il catalogo la cambia, questa va cambiata con lui: sono
#    una cosa sola in due posti, ed e' dichiarato qui perche' si veda.
MARCA = "REMOTIX B12 GUASTO"

SANO = "  const b64 = await impronta();"
GUASTO = ("  const b64 = IMPRONTA_SERVITA; /* " + MARCA + " P5-ritiro — "
          "RCP.md §4.1-bis: il RITIRO tolto, non il valore.  La pagina non "
          "chiede piu' /impronta e usa per sempre quella servita. */")


def impronta_file(p):
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def leggi(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError as sbaglio:
        print(f"NO  ⛔ «{p}» non si legge: {sbaglio}")
        print("    Non e' «il guasto non c'e'»: e' «non ho potuto guardare».")
        return None


def stato(percorso):
    """Che cosa c'e' adesso in quel file.  Ritorna 'sano', 'guasto' o None."""
    testo = leggi(percorso)
    if testo is None:
        return None
    c_sano, c_guasto = testo.count(SANO), testo.count(MARCA + " P5-ritiro")
    print(f"--  {percorso}")
    print(f"--  sha256: {impronta_file(percorso)}")
    print(f"--  la riga sana compare {c_sano} volta/e, la marca del guasto {c_guasto}")
    # ⛔ I due conteggi si stampano tutt'e due, sempre: «zero righe sane» e
    #    «una riga guasta» sono due fatti, e un file che non avesse ne' l'una
    #    ne' l'altra e' un TERZO caso — la pagina e' cambiata sotto di noi, e
    #    allora questo attrezzo non sa piu' dove innestare.
    if c_sano == 1 and c_guasto == 0:
        print("OK  SANO")
        return "sano"
    if c_sano == 0 and c_guasto == 1:
        print("OK  GUASTO innestato")
        return "guasto"
    print("NO  ⛔ NE' L'UNO NE' L'ALTRO: questa pagina non e' quella su cui")
    print("    questo guasto e' stato scritto.  ⛔ Non innesto e non tolgo:")
    print("    un innesto «riuscito senza fare niente» e' la settima veste di")
    print("    LEZIONI.md §1.9, e questo attrezzo esiste per non farla.")
    return None


def a_parte(percorso):
    return percorso + ".p5-ritiro-originale"


def innesta(percorso):
    if stato(percorso) != "sano":
        return 1
    orig = a_parte(percorso)
    prima = impronta_file(percorso)
    shutil.copy2(percorso, orig)
    if impronta_file(orig) != prima:
        print("NO  ⛔ la copia messa da parte non ha l'impronta dell'originale")
        return 3
    with open(percorso, encoding="utf-8") as f:
        testo = f.read()
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(testo.replace(SANO, GUASTO, 1))
    dopo = impronta_file(percorso)
    if dopo == prima:
        print("NO  ⛔ il file non e' cambiato: l'innesto non e' avvenuto")
        return 1
    print(f"OK  innestato   {prima[:16]}… → {dopo[:16]}…")
    print(f"--  l'originale sta in {orig}")
    print("⛔  ADESSO CI VA IL RIAVVIO DEL BERSAGLIO: il server legge pagina.html")
    print("    una volta sola, all'accensione (src/pagina.c:590).  Senza, il giro")
    print("    misura la pagina di prima con l'aria di aver innestato.")
    return 0


def togli(percorso):
    orig = a_parte(percorso)
    if not os.path.exists(orig):
        print(f"NO  ⛔ non c'e' nessun originale da parte ({orig}): non rimetto a")
        print("    posto per deduzione.  Se il guasto c'e', va tolto a mano e")
        print("    riverificato con «stato».")
        return 3
    voluta = impronta_file(orig)
    shutil.copy2(orig, percorso)
    dopo = impronta_file(percorso)
    if dopo != voluta:
        print(f"NO  ⛔ rimesso ma l'impronta non torna: {dopo} invece di {voluta}")
        return 1
    if stato(percorso) != "sano":
        print("NO  ⛔ l'impronta torna ma il file non e' sano: due cose che non")
        print("    possono essere vere insieme.  Non dichiaro riuscito niente.")
        return 1
    os.remove(orig)
    print(f"OK  tolto e riverificato: sha256 {dopo}")
    print("⛔  E anche qui ci va il RIAVVIO del bersaglio, per la stessa ragione.")
    return 0


def principale():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("comando", choices=("stato", "innesta", "togli"))
    p.add_argument("--pagina", required=True,
                   help="il pagina.html della COPIA bersaglio — mai quello del prodotto")
    a = p.parse_args()
    # ⛔ IL PRODOTTO NON SI TOCCA, e non e' una raccomandazione nel commento:
    #    e' un rifiuto nel programma (invariante I7 — la protezione di un
    #    difetto noto sta nel programma, non in una riga che si puo' perdere).
    vero = os.path.realpath(a.pagina)
    for vietato in ("/media/REMOTIX/src/remotix/pagina.html",
                    "/srv/src/remotix/pagina.html"):
        if vero == vietato:
            print(f"NO  ⛔ «{vero}» E' LA PAGINA DEL PRODOTTO DI CASA.")
            print("    P5 vuole il server riacceso fra un passo e l'altro, e")
            print("    riaccendere il prodotto con un guasto dentro lo mette")
            print("    sotto i piedi di chiunque altro.  Il guasto va in una")
            print("    COPIA.  Non faccio niente.")
            return 2
    if a.comando == "stato":
        return 0 if stato(a.pagina) else 1
    if a.comando == "innesta":
        return innesta(a.pagina)
    return togli(a.pagina)


if __name__ == "__main__":
    sys.exit(principale())
