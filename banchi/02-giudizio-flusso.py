#!/usr/bin/env python3
"""02-giudizio-flusso.py — costruisce il FLUSSO CHE LA SONDA DA' DA DECODIFICARE.

    python3 banchi/02-giudizio-flusso.py <giro>        scrive flusso-<giro>.json
    python3 banchi/02-giudizio-flusso.py --elenca      dice che cosa c'e' gia'

===========================================================================
⛔ PERCHE' ESISTE — il difetto D16, pagato con dieci minuti dell'utente

Il 12 agosto 2026, ore 19.58, l'utente ha aperto la sonda **dal telefono in
Samsung DeX**, ha premuto i bottoni 1 e 2, e ha visto «tutti esiti negativi».
Il registro del raccoglitore dice un'altra cosa:

    192.168.0.24  "GET /02-giudizio-pagina.html?giro=20260812-1958"  200
    192.168.0.24  "POST /esito"                                      200
    192.168.0.24  "GET /flusso-20260812-1958.json"                   404   ⛔
    192.168.0.24  "POST /esito"                                      200

⇒ Il telefono **non ha fallito**: la sonda non aveva niente in mano.  Nessuno
  costruiva `flusso-<giro>.json`, e `serve` accendeva il sito lo stesso.

⛔ E' la forma d'errore **E8** (`REVIEWER.md` §2): *«il dispositivo non e'
   arrivato»* e *«il dispositivo e' arrivato e non aveva niente da
   decodificare»* avevano la stessa faccia.  ⛔ E sarebbe stato **peggio** con
   un riconoscimento del dispositivo funzionante: la sonda avrebbe scritto
   «il telefono non decodifica» — un `[M]` falso contro un componente
   innocente, cioe' la cosa che questo progetto paga piu' cara di una misura
   mancante.

===========================================================================
⛔ LE SEQUENZE NON SI INVENTANO QUI — si prendono da F2.5

`banchi/02-pagina-sequenze/` esiste gia' e contiene diciannove sequenze
costruite con `libx265` e `libaom`, con **il livello e il profilo LETTI dal
flusso** (`ffprobe`) invece che indovinati — rilievo O12 di `RCP.md` §4.3: un
livello dichiarato piu' basso del vero **fa rifiutare la configurazione**, e il
sintomo e' «il browser non apre il flusso», cioe' un rosso contro il browser.

⇒ Questo programma **non codifica niente**: sceglie quattro sequenze gia'
  certificate e le impacchetta in un file solo, perche' il telefono le prenda
  con **una richiesta** invece che con nove (una scheda in primo piano su una
  rete di casa e' il posto dove ogni richiesta in piu' e' un modo di fallire).

⛔ E se le sequenze non ci sono, questo programma **si ferma** e stampa il
   comando da dare.  Non le ricostruisce da solo: `02-pagina-sequenze.py` e'
   di F2.5, un altro agente ci lavora nello stesso deposito, e riscrivergli i
   file sotto le mani e' il modo di rompere il banco di qualcun altro.

===========================================================================
⛔ QUALI QUATTRO, E PERCHE' PROPRIO QUELLE — quattro caselle, non una

| sequenza            | codec | bit | che domanda chiude                        |
|---------------------|-------|-----|-------------------------------------------|
| `A-10bit-annexb`    | HEVC  | 10  | ⭐ **il bersaglio**: `SPECIFICHE.md` §3.1  |
| `A-8bit-annexb`     | HEVC  |  8  | la controprova sulla PROFONDITA'          |
| `A-av1-10bitvero`   | AV1   | 10  | il ripiego negoziato, `DECISIONI.md` §1.13|
| `A-av1-8bit`        | AV1   |  8  | la controprova sul ripiego                |

⭐ **Le quattro caselle sono lo strumento, non un lusso.**  Con la sola casella
   in alto a sinistra, «non dipinge» ha tre cause che si somigliano: HEVC non
   c'e', i 10 bit non ci sono, o il flusso e' storto.  Con quattro:

     HEVC 10 no · HEVC 8 si'   ⇒ e' la **profondita'**, non il codec
     HEVC 10 no · HEVC 8 no · AV1 si'  ⇒ e' **HEVC**, e il ripiego regge
     tutte e quattro no        ⇒ ⛔ non e' il dispositivo: guarda il flusso

⚠ E sono tutte **pattern A**: il confronto dei pixel di F2.6 vuole una scena
  sola.  Il pattern B serve a F2.5 per la prova dello scambio, non qui.

===========================================================================
⛔ CHE COSA QUESTO FILE **NON** E'

Non e' la sequenza **4K60 Main10** su cui si misura la portata (bottone 3):
quella la produce F2.3 e **non c'e' ancora**.  Il banco la dichiara assente e
non la sostituisce con una piu' facile — una sequenza piu' facile non misura
«un po' meno», misura un'altra cosa.  A 640x480 si chiude la meta' (a) — i
pixel — e **non** la domanda sull'hardware.
===========================================================================
"""
import datetime
import json
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
# ⚠ `SEQUENZE` si puo' sovrascrivere, e serve a UNA cosa sola: innestare il
#   guasto di D16 in `02-giudizio-telefono.sh certifica` — puntare a una
#   cartella vuota e verificare che `serve` **si rifiuti di servire**.  ⛔ Non
#   e' un modo di dare al banco un flusso diverso: le sequenze sono quelle
#   certificate da F2.5, e una piu' facile misurerebbe un'altra cosa.
SEQUENZE = os.environ.get("SEQUENZE") or os.path.join(QUI, "02-pagina-sequenze")

# ⛔ L'ordine conta: la prima e' il bersaglio, le altre tre servono a dire
#    DOVE si e' rotto se il bersaglio non dipinge.
SCELTE = [
    ("A-10bit-annexb", "bersaglio",
     "HEVC Main10 Annex-B — il desiderato di SPECIFICHE.md §3.1"),
    ("A-8bit-annexb", "controprova-profondita",
     "HEVC Main 8 bit — se questa dipinge e la prima no, il difetto e' la "
     "PROFONDITA' e non il codec"),
    ("A-av1-10bitvero", "ripiego",
     "AV1 10 bit — il ripiego negoziato di DECISIONI.md §1.13"),
    ("A-av1-8bit", "controprova-ripiego",
     "AV1 8 bit — se questa dipinge e quella a 10 no, il difetto e' la "
     "PROFONDITA' anche sul ripiego"),
]


def errore(testo):
    sys.stderr.write("    \033[1;31mNO\033[0m  %s\n" % testo)


def nota(testo):
    sys.stderr.write("    --  %s\n" % testo)


def carica(nome):
    percorso = os.path.join(SEQUENZE, nome + ".json")
    if not os.path.isfile(percorso):
        return None, percorso
    with open(percorso, encoding="utf-8") as f:
        return json.load(f), percorso


def costruisci(giro):
    sequenze = []
    mancanti = []
    for nome, ruolo, perche in SCELTE:
        d, percorso = carica(nome)
        if d is None:
            mancanti.append(percorso)
            continue
        # ⛔ Non ci si fida del nome del file: si guarda che cosa DICE il JSON.
        #    Una sequenza a 8 bit spacciata per 10 renderebbe la domanda ?2
        #    una domanda a cui si e' gia' risposto male.
        d["ruolo_sonda"] = ruolo
        d["perche"] = perche
        d["ordine"] = len(sequenze)
        sequenze.append(d)
    if mancanti:
        errore("mancano %d sequenze su %d:" % (len(mancanti), len(SCELTE)))
        for m in mancanti:
            nota(m)
        errore("⛔ NON le ricostruisco da qui: `02-pagina-sequenze.py` e' di")
        errore("   F2.5 e un altro agente ci lavora.  Il comando e':")
        nota("python3 banchi/02-pagina-sequenze.py")
        return None

    # ⛔ E un controllo che il file appena scritto sia quel che dice di essere:
    #    due sequenze a 8 bit e nessuna a 10 farebbero una sonda che non puo'
    #    rispondere alla domanda per cui esiste.
    prof = sorted({s["profondita"] for s in sequenze})
    codec = sorted({s["codec"].split(".")[0] for s in sequenze})
    if prof != [8, 10]:
        errore("le profondita' nel pacchetto sono %s: ne servono 8 E 10" % prof)
        return None
    if len(codec) < 2:
        errore("un codec solo (%s): serve HEVC E AV1, o il ripiego non e' "
               "misurato" % codec)
        return None

    return {
        "giro": giro,
        "prodotto_il": datetime.datetime.now().isoformat(timespec="seconds"),
        "prodotto_da": "02-giudizio-flusso.py",
        "sorgente": "banchi/02-pagina-sequenze (F2.5) — non inventate qui",
        "larghezza": sequenze[0]["larghezza"],
        "altezza": sequenze[0]["altezza"],
        "profondita_presenti": prof,
        "codec_presenti": codec,
        "⛔ che cosa NON c'e'": "la sequenza 4K60 Main10 della portata: la "
                               "produce F2.3, e il banco la DICHIARA assente "
                               "invece di sostituirla con una piu' facile",
        "sequenze": sequenze,
    }


def principale():
    argomenti = sys.argv[1:]
    if not argomenti or argomenti[0] in ("-h", "--aiuto"):
        print(__doc__)
        return 2

    if argomenti[0] == "--elenca":
        trovati = sorted(f for f in os.listdir(QUI)
                         if f.startswith("flusso-") and f.endswith(".json"))
        if not trovati:
            nota("nessun flusso costruito")
            return 1
        for f in trovati:
            p = os.path.join(QUI, f)
            with open(p, encoding="utf-8") as g:
                d = json.load(g)
            print("    --  %-34s %d sequenze · %s · %d byte"
                  % (f, len(d.get("sequenze", [])), d.get("prodotto_il", "?"),
                     os.path.getsize(p)))
        return 0

    giro = argomenti[0]
    pacco = costruisci(giro)
    if pacco is None:
        return 2
    fuori = os.path.join(QUI, "flusso-%s.json" % giro)
    with open(fuori, "w", encoding="utf-8") as f:
        json.dump(pacco, f, ensure_ascii=False)
    # ⛔ Si rilegge quel che si e' scritto: un JSON troncato da un disco pieno
    #    darebbe sul telefono lo stesso identico sintomo del 404 di stasera.
    with open(fuori, encoding="utf-8") as f:
        riletto = json.load(f)
    if len(riletto["sequenze"]) != len(SCELTE):
        errore("il file riletto ha %d sequenze invece di %d"
               % (len(riletto["sequenze"]), len(SCELTE)))
        return 2
    print("    \033[1;32mOK\033[0m  flusso-%s.json — %d sequenze, %d byte"
          % (giro, len(riletto["sequenze"]), os.path.getsize(fuori)))
    for s in riletto["sequenze"]:
        print("    --  %-20s %-16s %2d bit  %d pezzi  %s"
              % (s["nome"], s["codec"], s["profondita"], len(s["pezzi"]),
                 s["ruolo_sonda"]))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
