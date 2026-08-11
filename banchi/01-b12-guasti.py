#!/usr/bin/env python3
"""01-b12-guasti.py — ⛔ B12: un guasto costruito a mano PER OGNI BANCO.

    python3 01-b12-guasti.py --elenco               i dodici guasti
    python3 01-b12-guasti.py --verifica B7          l'appiglio c'e' ed e' unico?
    python3 01-b12-guasti.py --applica  B7          innesta il guasto
    python3 01-b12-guasti.py --togli    B7          lo toglie, e lo VERIFICA
    python3 01-b12-guasti.py --giudica  esiti.jsonl il verdetto, e il registro
    python3 01-b12-guasti.py --registro             chi e' certificato, e quando
    python3 01-b12-guasti.py --impronte B7          i file su cui poggia B7, oggi

⚠ `--applica`, `--togli` e `--verifica` girano DENTRO il contenitore: toccano
  le copie che stanno in `examples/`.  `--giudica` e `--registro` girano
  dovunque.  L'orchestratore e' `01-b12-lancia.sh`.

===========================================================================
⛔ PERCHE' ESISTE, E NON E' UNA FORMALITA'

`PIANO.md` §0.3 regola 4, e `LEZIONI.md` §1.2: **il banco si certifica prima di
essere creduto.**

  ⛔ *«Un banco che non e' mai diventato rosso non e' pulito: e' NON
     CERTIFICATO.»*

`fasi/01-filo-nudo.md` B12-C1: ⛔ **un guasto costruito a mano PER OGNI BANCO, e
sono dodici.**  *La prima stesura ne costruiva quattro per dodici banchi, e i
due scoperti erano i banchi dei due difetti piu' cari di v1* (R3.7, R4.6).

===========================================================================
⛔ LE QUATTRO TRAPPOLE DI UN BANCO CHE CERTIFICA ALTRI BANCHI

  1. **il rosso per la ragione sbagliata.**  Un guasto che rompe la
     compilazione fa diventare rosso QUALUNQUE banco, e certifica **zero**.
     ⛔ Da cui: ogni guasto dichiara la **marca** che deve comparire nell'uscita
     del banco rosso, e senza quella marca la certificazione **non vale**;
     ⛔ **e la marca ha DUE meta', e la seconda e' quella che si dimentica**:
     l'uscita rossa la deve dire **e il giro SANO NON la deve gia' dire**.
     Una marca che compare in tutt'e due i giri non e' una marca, e' un modo
     di certificare senza guardare — la nota del guasto C2 lo scriveva gia',
     e `giudica()` non lo verificava.  *Rilievo R12-A.3, 11 agosto 2026: la
     seconda meta' era gia' scritta la stessa notte in
     `01-b8-cronometro.py:1571` (`gia = frase in testo_sano`), e il criterio
     piu' debole era proprio nel banco che certifica gli altri undici.*
     ⛔ Da cui, qui: `giudica()` pretende `guasto.marca_vista` **e**
     `not sano.marca_vista`, e un guasto **senza marca non certifica niente**
     invece di saltare il controllo;
  2. **il guasto che non e' stato innestato.**  Un appiglio che non si trova
     lascia il codice sano, il banco resta verde, e chi legge conclude *«il
     banco non vede il guasto»* — cioe' l'accusa esattamente opposta.  ⛔ Da
     cui: l'appiglio si conta **prima**, e dev'essere **esattamente uno**;
  3. **il guasto che sopravvive.**  Un interruttore che fa mentire il server e
     resta acceso avvelena ogni misura successiva, e nessuno sapra' che c'era.
     ⛔ Da cui: `--togli` **riverifica il file byte per byte** contro
     l'impronta di prima, e non si fida di aver tolto;
  4. **il verde di partenza mai guardato.**  «E' diventato rosso» non vuol dire
     niente se non era verde prima.  ⛔ Da cui il giro e' **sano → guasto →
     sano**, e sono tre esecuzioni, non una.

===========================================================================
⛔ CHE COSA VUOL DIRE «CERTIFICATO», QUI DENTRO

Un banco e' certificato quando, **nello stesso giro**:

  · sano   ha dato l'esito che si aspettava da un server sano;
  · guasto ha dato un esito DIVERSO, **e la sua uscita porta la marca** che
           dice che ha visto proprio quel guasto;
  · sano   ci e' tornato: il guasto e' stato tolto e il banco e' tornato verde.

⛔ Due su tre non bastano, e il piu' insidioso da perdere e' il terzo: senza,
   «il banco vede il guasto» e «il banco e' rimasto rotto» hanno lo stesso
   aspetto.

⭐ E la certificazione **si scrive su file, con la data**: `01-b12-registro.jsonl`.
   Un banco certificato tre giorni fa su un codice che nel frattempo e'
   cambiato **non e' certificato oggi**, e il registro porta anche l'impronta
   dei file su cui la certificazione e' stata fatta.

===========================================================================
⛔ IL REGISTRO CONSERVA LA STORIA, NON LA SOVRASCRIVE

*Rilievo R12-A.4, 11 agosto 2026.*  Il campo si chiamava `mai_provati` ed era
calcolato **per giro**: `set(GUASTI) - set(per_sigla)`.  Cosi' B13, che alle
21:19 era `non_certificati` — cioe' **provato e non riuscito** — alle 23:01 era
`mai_provati`; e B7 e C2, certificati alle 21:19, alle 23:01 erano
`mai_provati`.  Sullo **stesso** codice.

  ⛔ *«Provato e non riuscito» e «mai provato» hanno due cure diverse, e il
     registro le fondeva nella piu' innocente.  Chi legge l'ultima riga — che
     e' quel che fa chiunque legga un registro — sapeva MENO di quel che il
     progetto sapeva due ore prima.*

Da cui tre cose, tutte qui sotto:

  · il campo si chiama `non_provati_in_questo_giro`, che e' quel che e';
  · `mostra_registro()` legge **tutte** le righe, le ordina per data (⚠ e
    l'ordine di scrittura NON e' l'ordine del tempo: nel file di stasera la
    riga piu' vecchia sta sotto quella piu' nuova) e ricostruisce **lo stato
    corrente di ogni banco** dall'ultima riga che ne dice qualcosa.  La parola
    *«mai»* si usa solo quando **nessun** giro l'ha mai provato;
  · e lo stato corrente si confronta con le **impronte di oggi**: una
    certificazione fatta su file che nel frattempo sono cambiati si stampa
    **scaduta**, che non e' «certificato» e non e' «mai provato».
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import socket
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
ESEMPI = os.path.join(QUI, "b2", "ngtcp2", "examples")
# ⛔ Il nome comincia con `01-b12-` come tutto il resto di questo banco: i
#    file di questa fase hanno il proprietario scritto nel nome, e un
#    registro chiamato altrimenti sarebbe di nessuno.
REGISTRO = os.path.join(QUI, "01-b12-registro.jsonl")

# ⛔ LA CARTELLA DELLE COPIE, E PERCHE' NON SI GUASTA MAI UN ORIGINALE.
#
#    Tre dei guasti sono su programmi Python di altri banchi.  Guastarli in
#    casa loro vorrebbe dire due cose che il mandato vieta: toccare file di
#    altri, e — peggio — lasciare un banco guasto se questo programma morisse a
#    meta'.  ⭐ Qui si copiano **per intero** i banchi che servono in
#    `01-b12-copie/`, si guasta la COPIA, e si lancia la copia.
#
# ⚠ E la copia dev'essere INTERA, non del solo file guastato: `01-b4-lancia.py`
#   cerca il validatore accanto a se stesso, e una copia parziale girerebbe
#   contro il validatore SANO — stampando un verde e certificando niente.
COPIE = os.path.join(QUI, "01-b12-copie")

# ⛔ E DOVE SI TIENE L'ORIGINALE DI UN FILE CHE NON SI PUO' RICOSTRUIRE.
#
#    Un guasto di tipo `copia-di-file` (oggi: B13) non sostituisce una stringa
#    dentro un sorgente — **sovrascrive un file intero**.  Li' `--togli` non
#    puo' rifare l'operazione all'incontrario: deve rimettere i byte di prima,
#    e per rimetterli deve averli.  ⭐ Qui si tiene la copia dell'originale
#    **con la sua impronta accanto**, e `--togli` non si dichiara riuscito
#    finche' l'impronta non torna quella.
ORIGINALI = os.path.join(COPIE, "originali")

# La cartella dei certificati.  ⚠ E' un percorso di ESECUZIONE, non del sorgente:
# vive dentro il contenitore, e chi lancia lo puo' cambiare con `--certificati`.
CERT_PREDEFINITA = "/media/REMOTIX/b2-certificati"

# Che cosa serve a ciascun banco per girare da solo dentro `01-b12-copie/`.
CORREDO = {
    "B4": ["01-b4-lancia.py", "01-b4-validatore.py", "01-b4-registrazioni.py"],
    "B9": ["01-b9-letture.py", "01-b3-cliente.py"],
    "C2": ["01-c2-diagnosi.py", "01-b3-cliente.py"],
}

# ===========================================================================
# ⛔ SU CHE COSA POGGIA DAVVERO LA CERTIFICAZIONE DI OGNI BANCO — rilievo R12-A.5
#
# Il registro annotava una sola impronta, `sha256(banchi/rcp/rcp.c)`, per tutti
# e dodici.  Ma i tre guasti che sono stati davvero eseguiti si innestano su
# `01-b4-validatore.py`, `01-b3-cliente.py` e `01-c2-diagnosi.py`, e i banchi
# che devono diventare rossi sono `01-b4-lancia.py`, `01-b9-letture.py`,
# `01-c2-diagnosi.py`: ⛔ **nessuno di quei file entrava nell'impronta**, e
# `rcp.c` non partecipa alla certificazione di B4 e di B9 in nessun modo.
#
#   ⛔ *Un denominatore che promette una cosa e ne misura un'altra e' PEGGIO di
#      nessun denominatore, perche' da' alla riga l'aria di essere gia' stata
#      controllata: si riscrive `01-b4-validatore.py` da capo, `rcp.c` non si
#      tocca, e la riga «B4 certificato, impronta d839839f…» resta valida a
#      vista mentre il banco certificato non esiste piu'.*
#
# ⭐ Da cui: ogni guasto dichiara **i file su cui la sua certificazione poggia**
#    — quello guastato E quello che deve diventare rosso — e il registro porta
#    l'impronta di ciascuno.  `--registro` le ricalcola oggi e dice quali
#    certificazioni sono **scadute**.
#
# ⚠ E un file che non si legge da qui (i documenti non stanno sulla macchina di
#   prova, i banchi di B4 non stanno nel contenitore) vale `None`, e due `None`
#   NON sono uguali: «non ho potuto guardare» non e' «non e' cambiato».
FILE_CHE_CONTANO = {
    "B2":  ["01-b2-sonda-trasporto.py", "01-b2-ngtcp2-wt-innesta.py"],
    "B3":  ["01-b3-cliente.py", "01-b3-rcp-innesta.py", "rcp/rcp.c"],
    "B4":  ["01-b4-lancia.py", "01-b4-validatore.py", "01-b4-registrazioni.py"],
    "B5":  ["01-b5-violazioni.py", "rcp/rcp.c"],
    "B6":  ["01-b6-tetti.py", "rcp/rcp.c"],
    "B7":  ["01-b7-congedo.py", "rcp/rcp.c"],
    "B8":  ["01-b8-cronometro.py", "rcp/rcp.c"],
    "B9":  ["01-b9-letture.py", "01-b3-cliente.py", "../RCP.md"],
    "B10": ["rcp/autenticazione.c"],
    "B11": ["01-b11-guasto-innesta.py", "01-b11-pagina.html"],
    "B13": ["01-b13-proprieta.py", "rcp/rcp.c"],
    "C2":  ["01-c2-diagnosi.py"],
}

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

MARCA = "REMOTIX B12 GUASTO"


# ===========================================================================
# IL CATALOGO.  ⛔ Dodici guasti, uno per banco, e ciascuno dice:
#
#   dove       il file da guastare — ⛔ SEMPRE una COPIA, mai l'originale;
#   appiglio   la stringa da sostituire, che dev'essere UNICA nel file;
#   guasto     con che cosa si sostituisce;
#   dimostra   che cosa il banco starebbe per non vedere;
#   marca      la stringa che l'uscita del banco rosso DEVE contenere, o il
#              rosso e' di un'altra causa;
#   costa      «leggero» = si applica e si gira · «ricostruisce» = fra
#              l'innesto e il giro ci va una compilazione ·
#              «copia-di-file» = si sovrascrive un file intero e si tiene
#              l'originale da parte · «gia-fatto» = il guasto vive nel banco.
# ===========================================================================
GUASTI = {}


def guasto(sigla, banco, titolo, dove, appiglio, sostituto, dimostra, marca,
           costa, riferimento, nota="", atteso_sano=0, sostituisci_con=""):
    # ⛔ `atteso_sano` non e' sempre 0, e darlo per scontato sarebbe la forma
    #    B0.4 al contrario: **B13 sul codice sano esce 3**, perche' due delle
    #    sei proprieta' non hanno un imputato da misurare.  Un giudice che
    #    pretendesse lo zero direbbe «il banco era gia' rosso» di un banco che
    #    sta facendo esattamente quel che deve — e non certificherebbe mai
    #    nessun banco che dichiara delle `[?]`.
    GUASTI[sigla] = {
        "sigla": sigla, "banco": banco, "titolo": titolo, "dove": dove,
        "appiglio": appiglio, "sostituto": sostituto, "dimostra": dimostra,
        "marca": marca, "costa": costa, "riferimento": riferimento,
        "nota": nota, "atteso_sano": atteso_sano,
        "sostituisci_con": sostituisci_con,
        "file_che_contano": FILE_CHE_CONTANO.get(sigla, []),
    }


# ── B7 — ⛔ IL GUASTO CHE `fasi/01-filo-nudo.md` NOMINA PER PRIMO ───────────
guasto(
    "B7", "B7", "si toglie la spedizione del CONGEDO e si LASCIA il codice "
                "nella chiusura",
    os.path.join(ESEMPI, "rcp.c"),
    "\tmanda_messaggio(s, T_CONGEDO, corpo, w.len);\n",
    "\t/* " + MARCA + " B7 — la spedizione del CONGEDO tolta, e il codice\n"
    "\t * nella chiusura della sessione LASCIATO al suo posto (§3.1 punto 3).\n"
    "\t * Se B7 resta verde sta facendo una || dove serve una &&. */\n",
    "⛔ §3.1 vuole DUE strade e B7 le deve pretendere **tutt'e due**: il "
    "`CONGEDO` sul canale di controllo E il codice del motivo nella chiusura "
    "della sessione.  Con questo guasto ne resta una sola.  ⭐ Un banco che le "
    "contasse in `or` — «almeno una delle due e' arrivata» — resterebbe VERDE, "
    "e sarebbe **nato per non accorgersene**: il motivo continuerebbe ad "
    "arrivare, e la strada che salva le diagnosi quando lo stream e' rotto "
    "sarebbe sparita in silenzio",
    # ⛔ LA MARCA ERA «CONGEDO», E NON ERA UNA MARCA — rilievo R12-A.3.
    #    `01-b7-congedo.py` nomina `CONGEDO` **37 volte**: e' il soggetto del
    #    banco, e compare nel giro SANO a ogni riga.  Con quella marca, B7
    #    rosso per una compilazione fallita — cioe' la trappola n.1 che questo
    #    file dichiara di chiudere — avrebbe avuto `marca_vista = true` lo
    #    stesso, e la certificazione del 10 agosto 2026 alle 21:19 e' stata
    #    esattamente questo.
    # ⭐ La marca giusta e' la riga che B7 stampa SOLO quando la strada 2 non e'
    #    arrivata: `esigenze()` mette `«assente»` in `es.motivo is None`, e la
    #    riga rossa la stampa (righe 1281-1283).  Nel giro sano tutti i casi
    #    `server→client` hanno «congedo» fra le strade esigibili e il motivo
    #    arriva, quindi quella riga non c'e'.
    "il motivo nel CONGEDO sul canale: assente",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §3.1, §8.1",
)

# ── B4 — il validatore che legge `lunghezza` come u16 ──────────────────────
guasto(
    "B4", "B4", "il validatore legge `lunghezza` come u16 invece che u32",
    os.path.join(COPIE, "01-b4-validatore.py"),
    'lung_msg = le.u32("la lunghezza")',
    'lung_msg = le.u16("la lunghezza")  # ' + MARCA + ' B4',
    "§6.1 mette `u16 tipo` e `u32 lunghezza`.  Letta come `u16`, la lunghezza "
    "vale sempre i **due byte alti** — cioe' quasi sempre zero — e il "
    "validatore trova ogni corpo «piu' lungo di quel che dichiara».  ⛔ Il "
    "banco di B4 deve accorgersene, e il modo in cui deve accorgersene e' "
    "**il byte accusato**: senza il confronto del byte, un validatore che "
    "sbaglia dappertutto darebbe lo stesso «non conforme» su tutte le "
    "registrazioni che devono essere non conformi, cioe' il numero giusto "
    "per la ragione sbagliata",
    # ⛔ LA MARCA ERA VUOTA, E B4 E' STATO CERTIFICATO LO STESSO — R12-A.3.
    #    Il campo vuoto faceva saltare a `giudica()` l'intero controllo (`if
    #    g.get("marca") and …`), cioe' **la trappola n.1 disinnescata dal
    #    proprio guardiano**: la riga «B4 certificato» del 10 agosto 2026 alle
    #    23:01 non distingue il rosso del guasto dal rosso di un file che non
    #    si apre.
    # ⭐ La marca e' la riga che il catalogo stesso indica due frasi piu' su —
    #    **il byte accusato** — e con `u16` il validatore accusa sempre il
    #    byte 36 invece del byte vero.  Misurata l'11 agosto 2026: 0 volte nel
    #    giro sano, 7 nel giro col guasto.
    "⛔ atteso il byte",
    "leggero",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §6.1",
    nota="⛔ Il file guastato e' la COPIA in `01-b12-copie/`, e il banco di B4 "
         "va lanciato contro la copia: `01-b4-validatore.py` non si tocca.",
)

# ── B3 — non si libera la struttura per connessione (il difetto di v1) ─────
guasto(
    "B3", "B3", "non si libera la struttura per connessione — il difetto che "
                "uccise v1 alla SECONDA connessione",
    os.path.join(ESEMPI, "http3_server_proto_codec.cc"),
    "  rcp_libera(rcp_);\n  rcp_ = nullptr;\n",
    "  /* " + MARCA + " B3 — la struttura per connessione NON si libera.\n"
    "   * E' il difetto di v1: la prima connessione passa, la seconda no. */\n",
    "`LEZIONI.md` §2.1: in v1 un certificato condiviso uccideva il server "
    "**alla seconda** connessione, e una prova a collegamento singolo **resta "
    "verde per sempre**.  ⛔ B3 esiste per questo, e questo guasto e' la forma "
    "esatta del difetto che B3 e' nato per trovare: se B3 resta verde, la "
    "seconda connessione non la sta guardando nessuno",
    "",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · LEZIONI.md §2.1 · RCP.md §11",
    nota="⚠ L'appiglio sta nell'ospite, non in `rcp.c`: `rcp_libera()` in "
         "`rcp.c` non ha chiamanti — li innesta `01-b3-rcp-innesta.py` nel "
         "`.cc`.  Se l'appiglio compare piu' di una volta il guasto NON si "
         "applica: toglierne uno solo lascerebbe il posto liberato altrove e "
         "il guasto sarebbe a meta'.\n"
         "       ⛔ **Senza marca, e quindi non certificabile** (R12-A.3): la "
         "riga che B3 stampa alla seconda connessione va misurata su un giro "
         "vero prima di poterla scrivere qui.  Finche' questo campo e' vuoto "
         "`--giudica` rifiuta di certificare B3, invece di saltare il "
         "controllo come faceva.",
)

# ── B5 — una violazione che il server smette di punire ─────────────────────
guasto(
    "B5", "B5", "una capacita' RIPETUTA nel `CIAO` non e' piu' "
                "`ERRORE_PROTOCOLLO`: il controllo dei duplicati SPENTO",
    os.path.join(ESEMPI, "rcp.c"),
    # ⛔⭐ IL GUASTO E' STATO RIFATTO L'11 AGOSTO 2026 — rilievo R12-A.37.
    #
    # L'appiglio era `"nome ripetuto"`, cioe' una stringa di COMMENTO, e il
    # sostituto ci appiccicava accanto la marca.  ⛔ Quel guasto **non rompeva
    # niente**: il codice compilato restava identico byte per byte, il server
    # continuava a congedare con `ERRORE_PROTOCOLLO`, e B5 sarebbe rimasto
    # verde nel passo 2/3 — cioe' avrebbe dichiarato «il banco non vede il
    # guasto» su un banco sano e un guasto che non c'era.
    # ⭐ Il guasto vero e' il RAMO: `if (ripetuto)` spento, `congeda()` mai
    #    chiamato.  Il `0 &&` lascia la condizione sotto gli occhi del
    #    compilatore, quindi niente avvisi su variabile non usata, e il
    #    `--togli` torna a un testo identico all'originale.
    "if (ripetuto) {",
    "if (0 && ripetuto) { /* " + MARCA + " B5 — il controllo dei duplicati\n"
    "\t\t                    * di §4.3 SPENTO: la ripetizione passa. */",
    "§4.3: *«un nome ripetuto due volte e' `ERRORE_PROTOCOLLO`. «Vince "
    "l'ultimo» e «vince il primo» sono due implementazioni diverse dello "
    "stesso documento»*.  ⛔ E' una violazione che **non produce nessun "
    "sintomo**: la connessione prosegue e la negoziazione riesce.  Se B5 non "
    "la vede, non la vedra' piu' nessuno",
    # ⛔ LA MARCA E' MISURATA, NON SCELTA — 11 agosto 2026.
    #    Innestato il guasto, `01-b5-violazioni.py` stampa due righe nuove:
    #      «NO  capacita-ripetuta   chiusura-wt=(assente)  sessione VIVA»
    #      «NO      §3.1 punto 3 su «capacita-ripetuta»: la chiusura della
    #               sessione porta assente, atteso 0x0b»
    # ⭐ E si prende la SECONDA.  Il nome del caso da solo — «capacita-ripetuta»
    #    — compare anche nel giro sano, in verde: sarebbe la stessa trappola
    #    gia' pagata su B6 con «ciao-presto» e su B7 con «CONGEDO».  La frase
    #    scelta esiste solo quando quel caso CADE.
    "§3.1 punto 3 su «capacita-ripetuta»",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §4.3",
    nota="⭐ ESEGUIBILE dall'11 agosto 2026 (R12-A.37).  ⚠ E la marca qui "
         "sotto NON e' stata scelta a tavolino: e' stata **misurata** "
         "innestando il guasto e leggendo che cosa il banco stampa, poi "
         "verificata assente dal giro sano.  Una marca dedotta e' la forma E5 "
         "— un fatto che era una deduzione mai riverificata.",
)

# ── B6 — il tetto che scatta PRIMA ─────────────────────────────────────────
guasto(
    "B6", "B6", "`TETTO_CIAO` da 5000 a 500 ms: il tetto scatta PRIMA",
    os.path.join(ESEMPI, "rcp.c"),
    "#define TETTO_CIAO 5000",
    "#define TETTO_CIAO 500 /* " + MARCA + " B6 */",
    "⛔ La meta' del requisito che nessuno scrive e' **«non prima»**.  Un "
    "server che congedasse subito con `TEMPO_SCADUTO` darebbe "
    "`TEMPO_SCADUTO` in tutt'e tre i casi, e un banco che guarda **solo il "
    "motivo** lo promuoverebbe a pieni voti.  Con questo guasto il caso "
    "`ciao-presto` — che tace il 70 % del tetto e poi manda `CIAO` — deve "
    "vedersi rifiutare un messaggio che §4.6 obbliga a servire",
    # ⛔ LA MARCA ERA «ciao-presto», CHE E' IL NOME DI UN CASO — R12-A.3.
    #    `01-b6-tetti.py:1177` lo stampa con `riga(ok, c["nome"], …)` a **ogni**
    #    giro, sano compreso: una marca che compare in tutt'e due i giri non e'
    #    una marca.
    # ⭐ La riga che solo il giro rosso puo' produrre e' quella dell'atteso del
    #    controllo che dice NO (`01-b6-tetti.py:1096`), stampata soltanto
    #    quando un caso `-presto` cade — cioe' quando il tetto scatta PRIMA,
    #    che e' esattamente quel che questo guasto costruisce.
    "⭐ nessuna caduta",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §4.6",
    nota="⚠ Catalogato e non eseguito: `01-b12-lancia.sh` non ha una riga di "
         "comando per B6, e il guasto va innestato in `rcp/rcp.c` e non nella "
         "copia di `examples/` — `01-b6-lancia.sh` ricopia il sorgente a ogni "
         "giro e cancellerebbe il guasto, e il confronto fra i due `#define` "
         "che B6 fa al passo 2 lo vedrebbe comunque.  ⛔ Finche' non e' "
         "eseguito B6 resta NON CERTIFICATO, e non «pulito».",
)

# ── B8 — il secondo fisso che sparisce ─────────────────────────────────────
guasto(
    "B8", "B8", "il ritardo fisso di un secondo prima di rispondere a "
                "`CREDENZIALI` viene tolto",
    os.path.join(ESEMPI, "rcp.c"),
    # ⛔⭐ E QUESTO APPIGLIO NON ESISTEVA — rilievo R12-A.38, 11 agosto 2026.
    #
    # Era `RITARDO_CREDENZIALI`, e in `rcp.c` quel nome **non compare nemmeno
    # una volta**: la costante si chiama `RITARDO_FISSO` (riga 70).  ⇒ Il
    # guasto non si sarebbe innestato nemmeno volendo, e la voce
    # «catalogata e non eseguita» nascondeva questo, non solo il ban.
    # ⚠ E come per B5, il sostituto era un COMMENTO accanto al nome: anche col
    #   nome giusto non avrebbe tolto nessun ritardo.
    # ⭐ Il guasto vero e' il NUMERO: il secondo fisso di §4.4-bis portato a
    #    zero.  Da li' «utente inesistente» risponde in un millisecondo e
    #    «parola sbagliata» in cinquanta — e il TEMPISMO torna a essere un
    #    canale, che e' precisamente cio' che B8 esiste per vedere.
    "#define RITARDO_FISSO 1000",
    "#define RITARDO_FISSO 0 /* " + MARCA + " B8 */",
    "§4.4-bis: *«il secondo fisso toglie il TEMPISMO come canale — senza, "
    "«utente inesistente» risponde in un millisecondo e «parola sbagliata» in "
    "cinquanta»*.  ⛔ E' una proprieta' di **sicurezza che nessun altro banco "
    "vede**, e una regressione che la togliesse non farebbe fallire niente",
    "",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 · RCP.md §4.4-bis",
    nota="⭐ IL GUASTO E' VERO E INNESTABILE dall'11 agosto 2026 (R12-A.38), "
         "e la sua efficacia e' MISURATA: col ritardo a zero, sull'innesto, "
         "«giusta» risponde in **58 ms** e «inesistente» in **2959** — il "
         "tempismo torna a essere un canale spalancato.\n"
         "       ⛔ MA B8 NON SI PUO' ANCORA CERTIFICARE, e il motivo non e' "
         "piu' il ban: e' che **il suo giro sano non e' verde sotto B12**. "
         "`[M]` 11 agosto: 8 punti su 8 non passano, e sono tutti pezzi che "
         "questo orchestratore non gli da'.\n"
         "       ⭐ Quel che oggi c'e' (e prima no): B12 lancia B8 come un "
         "CICLO — scaldata, sei blocchi corti, **sblocco fra un blocco e "
         "l'altro** — col server acceso su `0.0.0.0` e col suo "
         "`--comando-socket`, e gli passa il registro del server.  Con questo "
         "B8 arriva a **39 tentativi, 14 sblocchi**, e le mediane le giudica "
         "davvero.  ⚠ Un blocco solo dava n=2, e a n<10 il verdetto sulle "
         "mediane e' **SOSPESO**: il guasto non sarebbe stato giudicato "
         "affatto.  ⛔ E alzare `--per-caso` non e' la strada: B8 controlla il "
         "proprio piano PRIMA di partire e si rifiuta se sfora la soglia di "
         "§4.4-bis — *«un piano che sfora misurerebbe il ban credendo di "
         "misurare PAM»*.\n"
         "       ⛔ CHE COSA MANCA ANCORA, in ordine di costo:\n"
         "         · **due vite del server**: la persistenza del ban (I7) si "
         "prova con un RIAVVIO, e `gira()` accende una volta sola;\n"
         "         · **la lettura della pagina**: il punto 1 di §4.4-bis vuole "
         "che l'utente bannato veda una pagina, e qui non se ne legge nessuna;\n"
         "         · **lo sblocco su un ban VERO**: oggi si sblocca sempre, e "
         "«tolto» e «non c'era» non si distinguono.\n"
         "       ⇒ Sono, in sostanza, la sequenza intera di "
         "`01-b8-lancia.sh`.  ⭐ La strada onesta e' insegnarla a `gira()` "
         "**o** certificare B8 dal suo lanciatore; ⛔ la strada disonesta "
         "sarebbe allargare l'atteso finche' torna, che e' esattamente quel "
         "che B13 ha insegnato a non fare.\n"
         "       ⚠ E UN FATTO NUOVO, raccolto per strada: col registro del "
         "server in mano B8 nomina l'imputato delle mediane, e sull'innesto "
         "dice **«PAM»** — lo stesso che diceva sul prodotto.  Il ⚠ delle "
         "mediane separate non e' del nostro codice, e adesso lo si sa su "
         "tutt'e due i bersagli."
)

# ── B9 — ⛔ il cliente di prova che ha letto il C ───────────────────────────
guasto(
    "B9", "B9", "⛔ si cancella dal cliente di prova la riga che il censimento "
                "cita alla voce L4",
    os.path.join(COPIE, "01-b3-cliente.py"),
    "            corpo = bytes(self.arrivati[6:6 + lung])\n",
    "            grezzo = bytes(self.arrivati[6:6 + lung])\n"
    "            # " + MARCA + " B9 — «ha letto il C»: la coda in piu' si\n"
    "            # taglia invece di essere consegnata, cioe' la lettura A di\n"
    "            # §6.1 — quella che ha scelto il validatore.  ⛔ L'appiglio\n"
    "            # che `01-b9-letture.py` cita nella voce L4 SPARISCE, ed e'\n"
    "            # il punto: il censimento non descrive piu' questo cliente.\n"
    "            corpo = grezzo\n",
    "⛔ Il valore di B9 non e' che il cliente di prova funzioni: e' che sia "
    "**un secondo lettore indipendente**.  Se chi lo scrive guarda il C, le "
    "sue scelte diventano quelle del server e la concordanza fra i due non "
    "vale piu' niente — e ⭐ **nessun altro banco puo' accorgersene**, perche' "
    "tutti gli altri diventerebbero piu' verdi, non meno.  Questo guasto "
    "cambia una delle scelte censite: `01-b9-letture.py` deve accorgersi che "
    "il testo del cliente non e' piu' quello che ha censito, e **rifiutarsi "
    "di dare il verde**",
    "il testo e' cambiato sotto il banco",
    "leggero",
    "fasi/01-filo-nudo.md B12-C1 e B9 · PIANO.md §1.1",
    nota="⛔ CHE COSA QUESTA CERTIFICAZIONE DICE, E CHE COSA NON DICE — "
         "rilievo R12-A.8, e il titolo di questa voce e' stato corretto per "
         "questo.\n"
         "       Il guasto **cancella la citazione** che la voce L4 porta "
         "(`corpo = bytes(self.arrivati[6:6 + lung])`), e B9 diventa rosso "
         "perche' il testo che ha censito non c'e' piu'.  ⭐ E' una cosa vera "
         "e vale la pena averla misurata: e' la difesa contro il censimento "
         "che invecchia in silenzio, ed e' quel che B9 dichiara di saper fare "
         "(righe 45-46 del suo file).\n"
         "       ⚠ **Non e' pero' «B9 vede un secondo lettore che si e' "
         "allineato al primo»**, che e' la frase piu' grossa.  Caso concreto, "
         "costruito dal revisore e verificato: si cambia la lettura A→B "
         "**lasciando intatta, riga per riga, la stringa citata** e "
         "aggiungendo il troncamento nelle righe successive → B9 esce **0, 12 "
         "su 12**, e continua a stampare «⭐ SCELTO … passa il corpo cosi' "
         "com'e' (lettura B, tollerante)», che a quel punto e' falso.\n"
         "       ⛔ Il guasto che coprirebbe QUELLA frase e' un secondo guasto "
         "— cambiare il comportamento senza toccare la citazione — e va "
         "costruito contro `01-b9-letture.py`, che non e' di questo mandato. "
         "Qui si dichiara invece di lasciarlo credere.",
)

# ── B10 — la guardia ereditata da v1 ───────────────────────────────────────
guasto(
    "B10", "B10", "si rimette la guardia che rifiuta chi non possiede il "
                  "processo",
    os.path.join(ESEMPI, "autenticazione.c"),
    "autenticazione_utente_atteso",
    "autenticazione_utente_atteso /* " + MARCA + " B10 */",
    "`SPECIFICHE.md` §5.5 vuole il multi-tenant; v1 aveva una guardia che "
    "rifiutava chiunque non fosse il proprietario del processo.  ⛔ B10 esiste "
    "per vederla, e *«non entra» ha quattro cause* (R3.26): se B10 resta "
    "verde con la guardia rimessa, sta guardando la causa sbagliata",
    "",
    "ricostruisce",
    "fasi/01-filo-nudo.md B12-C1 e B10 · SPECIFICHE.md §5.5",
    nota="⚠ Catalogato e non eseguito: B10 non e' ancora scritto, e un guasto "
         "senza il banco che lo deve vedere non certifica niente.  ⛔ E senza "
         "marca — che qui e' una conseguenza, non una dimenticanza: la marca "
         "e' una riga dell'uscita di un banco che non esiste (R12-A.3).",
)

# ── B11 — la pagina che non applica §3 ─────────────────────────────────────
guasto(
    "B11", "B11", "il server guasto di B11 esiste gia': "
                  "`01-b11-guasto-innesta.py`",
    os.path.join(ESEMPI, "rcp.c"),
    "", "",
    "⭐ B11 e' l'unico banco che nasce **con il proprio guasto dentro**: "
    "`01-b11-guasto-innesta.py` costruisce un server che sbaglia apposta in "
    "dodici modi, e `01-b11-lancia.sh` gira la pagina **prima contro il "
    "server sano** — dove i casi che si aspettano un congedo devono cadere "
    "tutti — e poi contro quello guasto.  ⛔ E' la forma che B12 chiede, gia' "
    "in casa: qui si dichiara, non si rifa'",
    "",
    "gia-fatto",
    "fasi/01-filo-nudo.md B11 · banchi/01-b11-guasto-innesta.py",
)

# ── B13 — un certificato solo, in due file ─────────────────────────────────
guasto(
    "B13", "B13", "i due certificati diventano UNO: `pagina.pem` viene "
                  "sostituito con `sessione.pem`",
    "{CERT}/pagina.pem",
    "", "",
    "⛔ §4.1-bis: *«un server che ne genera uno solo a scadenza breve passa "
    "tutti i banchi — e l'avviso ricompare quattordici giorni dopo, quando "
    "nessuno collegherebbe le due cose»*.  ⭐ Questo guasto non tocca una riga "
    "di codice: fa diventare **uno** i due certificati che devono essere due, "
    "e B13.1 deve vedere **due impronte uguali**",
    "LE IMPRONTE COMBACIANO",
    "copia-di-file",
    "fasi/01-filo-nudo.md B13.1 · RCP.md §4.1-bis",
    atteso_sano=3,
    sostituisci_con="{CERT}/sessione.pem",
    nota="⛔ IL GUASTO E' STATO RIFATTO L'11 AGOSTO 2026 — rilievi R12-A.1 e "
         "R12-A.2, e le due cose erano diverse.\n"
         "       ⛔ **A.1 — non era innestabile.**  Era di tipo "
         "`riga-di-comando`; `applica()` chiama `verifica()`, che per quel "
         "tipo usciva **subito con 0**, e `0 != 1` cadeva nel ramo «l'appiglio "
         "non e' unico — il guasto NON si innesta».  In "
         "`01-b12-lancia.sh` l'uscita ≠ 0 faceva `continue`: **i passi 2/3 e "
         "3/3 di B13 non si sono mai eseguiti**, e il ramo di `gira()` che "
         "commutava `base=pagina` era codice morto.\n"
         "       ⛔ **A.2 — e non era il guasto giusto.**  Accendere il server "
         "con `pagina.pem` cambia il certificato **presentato sul filo**, "
         "mentre `proprieta_1` legge le impronte dei **due file su disco** "
         "(`impronta_der(pagina.pem)` contro `impronta_der(sessione.pem)`): "
         "la riga di comando non tocca nessuno dei due, `imp_p == imp_s` "
         "restava falso e la marca «LE IMPRONTE COMBACIANO» non si sarebbe "
         "stampata mai.  A vedere quel guasto e' `proprieta_3` — un'altra "
         "proprieta' e un altro difetto — e `giudica()` avrebbe scritto «il "
         "banco e' rosso ma la sua uscita non nomina la marca» su un guasto "
         "che aveva funzionato.\n"
         "       ⭐ Il difetto che B13.1 esiste per trovare — *un server che "
         "genera UN certificato solo* — si costruisce dove B13.1 guarda: "
         "**sui due file**.  Da cui il tipo `copia-di-file`, l'originale "
         "tenuto in `01-b12-copie/originali/` con la sua impronta accanto, e "
         "un `--togli` che non si dichiara riuscito finche' i byte non sono "
         "tornati quelli.\n"
         "       ⚠ `atteso_sano = 3`: sul codice sano B13 dovrebbe uscire 3 e non 0, "
         "perche' B13.3 e B13.4 dichiarano di non avere un imputato (la pagina "
         "in TCP non esiste, e nessun codice genera certificati).  ⛔ E' un "
         "esito dichiarato, non un rosso — e va scritto qui, o la "
         "certificazione leggerebbe «era gia' rosso».\n"
         "       ⛔ `[M]` 10 agosto 2026, 23:30: **B13 sul codice sano esce 1**, "
         "non 3, perche' B13.2 ha trovato la parola d'ordine dentro un "
         "registro vero — `/srv/src/sonda/racc.log`.  ⭐ Da cui una regola che "
         "vale per tutto B12: **un banco il cui soggetto e' davvero rotto non "
         "si puo' certificare**, e la cosa giusta e' lasciarlo NON CERTIFICATO "
         "invece di allargare l'atteso finche' torna.  Si certifica il giorno "
         "in cui quel registro non contiene piu' la parola.",
)

# ── C2 — il diagnosta cieco su una delle due sonde ─────────────────────────
guasto(
    "C2", "C2", "⛔ al diagnosta si toglie la sonda TCP: resta con una sonda "
                "sola",
    os.path.join(COPIE, "01-c2-diagnosi.py"),
    "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    "    s.settimeout(attesa)\n",
    "    return \"silenzio\"  # " + MARCA + " C2: la sonda TCP accecata\n"
    "    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    "    s.settimeout(attesa)\n",
    "⛔ **E' il difetto storico**: R3.17 racconta che il primo controllo "
    "positivo del progetto era cieco proprio perche' guardava un trasporto "
    "solo.  Con la sonda TCP che dice sempre «silenzio», la scena «UDP "
    "filtrato col TCP che risponde» diventa indistinguibile da «la macchina "
    "non c'e'», e C2 **deve** cadere su quella scena.  ⭐ Se non cadesse, C2 "
    "starebbe distinguendo le tre diagnosi con qualcosa che non e' la coppia "
    "di sonde",
    "IRRAGGIUNGIBILE",
    "leggero",
    "fasi/01-filo-nudo.md B12-C2, rilievo R3.17",
    nota="⭐ La marca e' `IRRAGGIUNGIBILE`, ed e' scelta apposta: e' il nome che "
         "C2 puo' produrre SOLO quando gli manca una delle due sonde.  ⛔ Una "
         "marca come «udp-filtrato» sarebbe comparsa anche nel giro sano — e "
         "una marca che compare in tutt'e due i giri non e' una marca, e' un "
         "modo di certificare senza guardare.",
)

# ── B2 — il credito degli stream che sparisce dai parametri ────────────────
guasto(
    "B2", "B2", "si toglie il credito di 16 stream unidirezionali dai "
                "parametri di trasporto",
    os.path.join(ESEMPI, "..", "examples", "server.cc"),
    "params.initial_max_streams_uni = 16;",
    "/* " + MARCA + " B2 */",
    "§2.3 obbliga il server a concedere **almeno 16** stream unidirezionali. "
    "L'esempio di ngtcp2 ne concede tre di suo, e l'innesto B2 li porta a "
    "sedici.  ⛔ Tolta quella riga, il credito torna a tre e **niente si rompe "
    "adesso**: il sintomo arriverebbe alla fase 4, come «il desktop non "
    "risponde».  La sonda del trasporto di B2 — e B13.5 — devono vederlo qui",
    # ⛔ LA MARCA ERA «initial_max_streams_uni» — R12-A.3: e' il nome del
    #    parametro, e `01-b2-sonda-trasporto.py:169` lo STAMPA sempre, con il
    #    numero accanto, anche quando il numero e' giusto.
    # ⭐ La riga che solo il rosso produce e' il verdetto del controllo, che la
    #    sonda scrive con `NO ` davanti al nome (righe 186-190).
    "NO  credito INIZIALE stream unidirezionali",
    "ricostruisce",
    "fasi/01-filo-nudo.md B13.5 · RCP.md §2.3",
    nota="⚠ Catalogato e non eseguito in questo giro: costa una ricostruzione "
         "intera del server d'esempio, e il banco che lo vede (la sonda del "
         "trasporto) e' di B2, non di questo mandato.",
)


# ===========================================================================
# ⛔ La cartella dei certificati e' un percorso di esecuzione, e chi lancia la
#    puo' cambiare: si tiene in UN posto solo, e le voci del catalogo la
#    nominano con `{CERT}` invece di scriverla due volte.  Due verita' sullo
#    stesso percorso e' la forma con cui i guasti si perdono per strada.
CERT = CERT_PREDEFINITA


def risolvi(p):
    """`{CERT}/pagina.pem` → il percorso vero, con la cartella di oggi."""
    return p.replace("{CERT}", CERT) if p else p


def impronta_file(p):
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def provabile(sigla):
    """⛔ Si puo' certificare `sigla` SU QUESTA MACCHINA?

    Stampa una riga `MANCA <nome>` per ogni file su cui la certificazione
    poggia e che qui non c'e'; esce 0 se non ne manca nessuno, 1 altrimenti.

    ⛔ RILIEVO R12-A.31, 11 agosto 2026.  «Non posso provarlo qui» e «l'ho
    provato e non passa» erano la stessa riga di registro.  `[M]`: B9 lanciato
    sul server e' uscito 4 — `RCP.md` **li' non esiste**, perche' su quella
    macchina arrivano i banchi e non i documenti — e il verdetto ha scritto
    «B9 NON certificato».  Un banco sano marchiato rosso manda a cercare un
    difetto che non c'e', e il registro se lo porta dietro con una data.
    ⭐ E' la forma opposta del falso verde.  Costa uguale, e si vede meno.

    ⚠ Guarda `file_che_contano`, non `dove`: `dove` e' il posto in cui il
      guasto si innesta, mentre la certificazione poggia sui file che il banco
      **legge** — ed e' uno di quelli a mancare, non l'appiglio.
    """
    g = GUASTI.get(sigla)
    if not g:
        print(f"MANCA il-guasto-{sigla}-non-e-in-catalogo")
        return 1
    mancanti = 0
    for nome in g.get("file_che_contano", []):
        if not os.path.exists(os.path.join(QUI, nome)):
            print(f"MANCA {nome}")
            mancanti += 1
    return 1 if mancanti else 0


def impronte_di(sigla):
    """{nome del file: sha256 | None}.  ⛔ `None` = non si e' potuto guardare.

    ⚠ E due `None` non sono uguali: il confronto fra due giri si fa solo sui
      file che si sono potuti leggere da tutt'e due le parti, e sugli altri si
      dice «non si sa», che non e' «non e' cambiato» (`LEZIONI.md` §1.9).
    """
    fuori = {}
    for nome in GUASTI.get(sigla, {}).get("file_che_contano", []):
        fuori[nome] = impronta_file(os.path.join(QUI, nome))
    return fuori


def confronta_impronte(vecchie, nuove):
    """(verdetto, spiegazione).  verdetto: «uguali» · «cambiate» · «non-si-sa»"""
    if not vecchie:
        return "non-si-sa", "la certificazione non porta nessuna impronta"
    cambiati, ciechi = [], []
    for nome, vecchia in sorted(vecchie.items()):
        nuova = nuove.get(nome)
        if vecchia is None or nuova is None:
            ciechi.append(nome)
        elif vecchia != nuova:
            cambiati.append(nome)
    if cambiati:
        return "cambiate", "cambiati da allora: " + ", ".join(cambiati)
    if ciechi:
        return "non-si-sa", ("non si sono potuti confrontare: "
                             + ", ".join(ciechi))
    return "uguali", f"{len(vecchie)} file, tutti identici alla certificazione"


def conta(p, ago):
    """Quante volte l'appiglio compare.  ⛔ (None) = non ho potuto guardare."""
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read().count(ago)
    except OSError:
        return None


def prepara_copia(g):
    """Rifa' da zero la copia intera del banco che questo guasto tocca.

    ⛔ Si rifa' SEMPRE, anche se la cartella c'e' gia': una copia rimasta da un
       giro precedente potrebbe portarsi dietro il guasto di quel giro, e il
       banco partirebbe **gia' rosso** — cioe' il verde di partenza, che e' la
       meta' della certificazione, sarebbe perso senza che nessuno lo veda.
    """
    corredo = CORREDO.get(g["sigla"])
    if not corredo:
        return True, ""
    os.makedirs(COPIE, exist_ok=True)
    fatti = []
    for nome in corredo:
        orig = os.path.join(QUI, nome)
        if not os.path.exists(orig):
            return False, f"⛔ l'originale non c'e': {orig}"
        shutil.copy2(orig, os.path.join(COPIE, nome))
        fatti.append(nome)
    # ⛔ E si guarda l'ESITO del costruttore, non la presenza del file: qui
    #    l'esito e' che le impronte della copia e dell'originale combacino.
    for nome in corredo:
        a = impronta_file(os.path.join(QUI, nome))
        b = impronta_file(os.path.join(COPIE, nome))
        if a is None or a != b:
            return False, f"⛔ la copia di {nome} non e' identica all'originale"
    # le registrazioni di B4 stanno in una cartella accanto
    if g["sigla"] == "B4":
        sorgente = os.path.join(QUI, "b4-registrazioni")
        if os.path.isdir(sorgente):
            dest = os.path.join(COPIE, "b4-registrazioni")
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(sorgente, dest)
    return True, "copia intera: " + ", ".join(fatti)


# ---------------------------------------------------------------------------
# ⛔ IL GUASTO CHE SOSTITUISCE UN FILE INTERO (oggi: B13).
#
#    Non c'e' nessuna stringa da contare: quel che qui prende il posto
#    dell'«appiglio unico» e' **che i due file siano diversi**.  Se fossero gia'
#    uguali il guasto non costruirebbe niente, il banco sarebbe gia' rosso, e
#    la certificazione leggerebbe «era gia' rosso» — la trappola n.4.
# ---------------------------------------------------------------------------
def _originale(dove):
    return os.path.join(ORIGINALI, os.path.basename(dove))


def verifica_copia(sigla, silenzioso=False):
    g = GUASTI[sigla]
    dove, da = risolvi(g["dove"]), risolvi(g["sostituisci_con"])
    a, b = impronta_file(dove), impronta_file(da)
    if a is None or b is None:
        if not silenzioso:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ non si leggono i due file:")
            print(f"        {dove}: {'letto' if a else '⛔ NO'}")
            print(f"        {da}: {'letto' if b else '⛔ NO'}")
            print("        Non e' «sono uguali»: e' che non si e' potuto "
                  "guardare.")
        return -1
    if a == b:
        if not silenzioso:
            print(f"    {ROSSO}NO{GRIGIO}  «{sigla}»: i due file sono GIA' "
                  f"identici ({a[:16]}…)")
            print("        ⛔ Il guasto non costruirebbe niente e il banco "
                  "sarebbe gia' rosso:")
            print("           «e' diventato rosso» non vuol dire niente senza "
                  "il verde di partenza.")
            print("        ⚠ E puo' voler dire che un giro precedente e' morto "
                  "col guasto addosso:")
            print(f"           l'originale, se c'e', sta in {_originale(dove)}")
        return 0
    if not silenzioso:
        print(f"    {VERDE}OK{GRIGIO}  «{sigla}»: i due file sono DIVERSI, "
              f"come devono essere")
        print(f"        {os.path.basename(dove)} {a[:16]}…  "
              f"{os.path.basename(da)} {b[:16]}…")
    return 1


def applica_copia(sigla):
    g = GUASTI[sigla]
    dove, da = risolvi(g["dove"]), risolvi(g["sostituisci_con"])
    prima = impronta_file(dove)
    os.makedirs(ORIGINALI, exist_ok=True)
    orig = _originale(dove)
    # ⛔ L'originale si mette da parte PRIMA, e con la sua impronta accanto: un
    #    `--togli` che rimettesse un file senza sapere che impronta doveva
    #    avere si dichiarerebbe riuscito su qualunque cosa.
    shutil.copy2(dove, orig)
    if impronta_file(orig) != prima:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ la copia dell'originale non e' "
              f"identica all'originale: il guasto NON si innesta")
        return 2
    with open(orig + ".sha256", "w", encoding="utf-8") as f:
        f.write(prima + "\n")
    shutil.copy2(da, dove)
    dopo = impronta_file(dove)
    atteso = impronta_file(da)
    if dopo != atteso:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ dopo la copia {dove} non ha "
              f"l'impronta di {da}: il guasto non e' stato innestato")
        return 2
    if dopo == prima:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il file non e' cambiato: il guasto "
              f"non e' stato innestato")
        return 2
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» innestato: "
          f"{os.path.basename(dove)} adesso E' {os.path.basename(da)}")
    print(f"        prima {prima[:16]}…  dopo {dopo[:16]}…")
    print(f"        l'originale e' in {orig} (impronta accanto)")
    print(f"        ⛔ e adesso il banco «{g['banco']}» DEVE diventare rosso")
    return 0


def togli_copia(sigla):
    g = GUASTI[sigla]
    dove, da = risolvi(g["dove"]), risolvi(g["sostituisci_con"])
    orig = _originale(dove)
    atteso = None
    try:
        with open(orig + ".sha256", encoding="utf-8") as f:
            atteso = f.read().strip()
    except OSError:
        pass
    if atteso is None or not os.path.exists(orig):
        # ⛔ E QUESTO NON E' «niente da togliere».  Se i due file sono uguali e
        #    l'originale non c'e', il guasto e' addosso al codice e nessuno ha
        #    piu' i byte per toglierlo: e' la trappola n.3 al suo peggio, e si
        #    urla invece di uscire 0.
        if impronta_file(dove) is not None and \
                impronta_file(dove) == impronta_file(da):
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ i due file sono IDENTICI e "
                  f"l'originale di {os.path.basename(dove)} NON c'e'")
            print(f"        Il guasto «{sigla}» e' addosso al sistema e da qui "
                  f"non si puo' togliere:")
            print("        va rigenerato il certificato della pagina, e finche' "
                  "non lo e' ogni")
            print("        misura di B13 e di C2 su questa macchina e' "
                  "avvelenata.")
            return 5
        print(f"    --  «{sigla}»: nessun originale da rimettere, e i due file "
              f"sono gia' diversi")
        return 0
    shutil.copy2(orig, dove)
    adesso = impronta_file(dove)
    if adesso != atteso:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ dopo il ripristino l'impronta e' "
              f"{str(adesso)[:16]}… e doveva essere {atteso[:16]}…")
        return 5
    if adesso == impronta_file(da):
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ rimesso l'originale, i due "
              f"certificati sono ANCORA identici: non era il file giusto")
        return 5
    for p in (orig, orig + ".sha256"):
        try:
            os.remove(p)
        except OSError:
            pass
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» tolto, e verificato: "
          f"{os.path.basename(dove)} e' tornato {atteso[:16]}… e i due "
          f"certificati sono di nuovo DUE")
    return 0


def verifica(sigla, silenzioso=False):
    g = GUASTI[sigla]
    if g["costa"] == "copia-di-file":
        return verifica_copia(sigla, silenzioso)
    if g["costa"] in ("gia-fatto", "riga-di-comando"):
        if not silenzioso:
            print(f"    {GIALLO}[?]{GRIGIO} «{sigla}» non ha un appiglio: "
                  f"e' un guasto di tipo «{g['costa']}»")
        return 0
    ok, testo = prepara_copia(g)
    if not ok:
        print(f"    {ROSSO}NO{GRIGIO}  {testo}")
        return -1
    n = conta(g["dove"], g["appiglio"])
    if n is None:
        if not silenzioso:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ non si legge: {g['dove']}")
            print("        Non e' «l'appiglio non c'e'»: e' che non si e' "
                  "potuto guardare.")
        return -1
    if not silenzioso:
        col = VERDE if n == 1 else ROSSO
        print(f"    {col}{'OK' if n == 1 else 'NO'}{GRIGIO}  «{sigla}»: "
              f"l'appiglio compare {n} volta/e in "
              f"{os.path.basename(g['dove'])}")
        if n == 0:
            print("        ⛔ Il guasto NON si potrebbe innestare, e il banco "
                  "resterebbe verde:")
            print("           chi legge concluderebbe «il banco non vede il "
                  "guasto», che e' l'accusa opposta.")
        elif n > 1:
            print("        ⛔ Sostituirne uno solo lascerebbe il guasto a "
                  "meta': non si applica.")
    return n


def applica(sigla):
    g = GUASTI[sigla]
    # ⛔ E IL MOTIVO DEL RIFIUTO DEV'ESSERE QUELLO VERO — rilievo R12-A.1.
    #    Qui c'era una riga sola, «l'appiglio non e' unico», stampata anche
    #    quando il guasto non ha nessun appiglio per costruzione: e' la forma
    #    del rosso puntato sull'imputato sbagliato, dentro lo strumento che
    #    esiste per non puntarlo sbagliato.
    if g["costa"] in ("gia-fatto", "riga-di-comando"):
        print(f"    {GIALLO}[?]{GRIGIO} «{sigla}»: guasto di tipo "
              f"«{g['costa']}» — da qui non si innesta, e non e' un errore")
        print("        ⛔ Ma non e' nemmeno una certificazione: chi lo lancia "
              "deve saperlo,")
        print("           e `--giudica` lo conta fra i NON CERTIFICATI.")
        return 4
    if verifica(sigla, silenzioso=True) != 1:
        print(f"    {ROSSO}NO{GRIGIO}  «{sigla}»: lo stato di partenza non e' "
              f"quello che il guasto vuole — NON si innesta")
        verifica(sigla)
        return 2
    if g["costa"] == "copia-di-file":
        return applica_copia(sigla)
    prima = impronta_file(g["dove"])
    with open(g["dove"], encoding="utf-8") as f:
        t = f.read()
    t = t.replace(g["appiglio"], g["sostituto"], 1)
    with open(g["dove"], "w", encoding="utf-8") as f:
        f.write(t)
    dopo = impronta_file(g["dove"])
    # ⛔ E si guarda l'ESITO del costruttore, non la presenza del file: un file
    #    che c'era gia' e non e' cambiato darebbe la stessa faccia.
    if prima == dopo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il file non e' cambiato: il guasto "
              f"non e' stato innestato")
        return 2
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» innestato in "
          f"{os.path.basename(g['dove'])}")
    print(f"        prima {prima[:16]}…  dopo {dopo[:16]}…")
    print(f"        ⛔ e adesso il banco «{g['banco']}» DEVE diventare rosso")
    return 0


def togli(sigla):
    g = GUASTI[sigla]
    if g["costa"] == "copia-di-file":
        return togli_copia(sigla)
    if g["costa"] in ("gia-fatto", "riga-di-comando"):
        print(f"    --  «{sigla}»: niente da togliere")
        return 0
    if not os.path.exists(g["dove"]):
        print(f"    --  «{sigla}»: {g['dove']} non c'e' — niente da togliere")
        return 0
    with open(g["dove"], encoding="utf-8") as f:
        t = f.read()
    if g["sostituto"] and g["sostituto"] in t:
        t = t.replace(g["sostituto"], g["appiglio"], 1)
        with open(g["dove"], "w", encoding="utf-8") as f:
            f.write(t)
    # ⛔ E POI SI VERIFICA, invece di fidarsi.  Un `--togli` che non toglie e' il
    #    difetto noto n.1 degli innesti di questa fase.
    resta = conta(g["dove"], MARCA)
    if resta:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ RESTANO {resta} marche «{MARCA}» in "
              f"{os.path.basename(g['dove'])}")
        print("        Un interruttore che fa mentire il codice non deve")
        print("        sopravvivere al giro: qui sopravvive.")
        return 5
    n = conta(g["dove"], g["appiglio"])
    if n != 1:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ dopo il ripristino l'appiglio compare "
              f"{n} volte, non 1: il file non e' quello di prima")
        return 5
    print(f"    {VERDE}OK{GRIGIO}  «{sigla}» tolto, e verificato: nessuna "
          f"marca residua, appiglio al suo posto")
    return 0


# ===========================================================================
def giudica(percorso):
    """Legge gli esiti dei tre passi e dice CHI e' certificato.

    Ogni riga del file e' `{"sigla":…, "passo":"sano|guasto|risano|saltato",
    "uscita":N, "marca_vista":bool}`.

    ⛔ E `marca_vista` si legge su TUTT'E TRE i passi, non solo sul guasto: la
       seconda meta' del criterio e' che il giro **sano** non dicesse gia' la
       marca (R12-A.3).
    """
    try:
        with open(percorso, encoding="utf-8") as f:
            righe = [json.loads(r) for r in f if r.strip()]
    except (OSError, ValueError) as e:
        print(f"    {ROSSO}⛔ gli esiti non si leggono ({e}): non c'e' niente "
              f"da giudicare{GRIGIO}")
        return 2

    per_sigla = {}
    for r in righe:
        per_sigla.setdefault(r["sigla"], {})[r["passo"]] = r

    print("== ⛔ Chi e' CERTIFICATO, e chi no")
    print("   (certificato = verde prima · rosso col guasto, con una marca che")
    print("    il giro SANO non diceva gia' · verde dopo)\n")
    certificati, no, saltati = [], [], []
    for sigla in sorted(per_sigla):
        p = per_sigla[sigla]
        g = GUASTI.get(sigla, {"banco": sigla, "marca": ""})
        sano = p.get("sano")
        rotto = p.get("guasto")
        risano = p.get("risano")
        motivi = []
        # ⛔ IL BANCO CHE NON SI E' NEMMENO POTUTO LANCIARE — e non e' «mai
        #    provato»: e' provato e non riuscito, per una ragione che ha un
        #    nome.  Tenerli separati e' il rilievo R12-A.4 applicato al giro.
        if p.get("saltato"):
            saltati.append(sigla)
            print(f"  {GIALLO}--{GRIGIO}  {sigla}  NON certificato — non "
                  f"lanciato in questo giro")
            print(f"        {p['saltato'].get('perche', 'ragione non detta')}")
            print(f"        guasto: {g.get('titolo', '?')}")
            continue
        # ⛔ LA TRAPPOLA N.1, CHIUSA DAL SUO GUARDIANO — rilievo R12-A.3.
        #    Qui c'era `if g.get("marca") and not rotto.get("marca_vista")`:
        #    con il campo VUOTO l'intero controllo saltava, e sei guasti su
        #    dodici hanno un campo vuoto.  B4 e' stato certificato cosi'.
        if not g.get("marca"):
            motivi.append("⛔ il guasto non dichiara nessuna MARCA: «il banco "
                          "e' diventato rosso» non si puo' attribuire a questo "
                          "guasto, e una compilazione fallita rende rosso "
                          "qualunque banco (trappola n.1)")
        if sano is None:
            motivi.append("il giro SANO non e' stato fatto: «e' diventato "
                          "rosso» non vuol dire niente senza il verde di "
                          "partenza")
        else:
            if sano["uscita"] != g.get("atteso_sano", 0):
                motivi.append(f"il giro SANO esce {sano['uscita']} e ne era "
                              f"atteso {g.get('atteso_sano', 0)}: il banco non "
                              f"partiva dallo stato che il catalogo dichiara, e "
                              f"il guasto non dimostra niente")
            # ⛔ LA SECONDA META' DEL CRITERIO — rilievo R12-A.3.
            #    La stessa riga esiste, scritta la stessa notte, in
            #    `01-b8-cronometro.py:1571`: `gia = frase in testo_sano` … «⛔ ma
            #    il giro SANO lo diceva gia': non prova niente».  Qui non c'era,
            #    e la marca di B7 («CONGEDO», 37 volte nel giro sano) e quella
            #    di B6 («ciao-presto», il nome di un caso) passavano lo stesso.
            if g.get("marca") and sano.get("marca_vista"):
                motivi.append(f"⛔ IL GIRO SANO DICEVA GIA' «{g['marca']}»: "
                              f"una marca che compare in tutt'e due i giri non "
                              f"e' una marca, e' un modo di certificare senza "
                              f"guardare — vederla nel rosso non prova niente")
        if rotto is None:
            motivi.append("il giro col GUASTO non e' stato fatto")
        else:
            if rotto["uscita"] == g.get("atteso_sano", 0):
                motivi.append(f"⛔ COL GUASTO IL BANCO HA DATO LO STESSO ESITO "
                              f"DEL SANO ({rotto['uscita']}): e' il difetto "
                              f"che B12 esiste per trovare")
            if g.get("marca") and not rotto.get("marca_vista"):
                motivi.append(f"⛔ il banco e' rosso ma la sua uscita non "
                              f"nomina «{g['marca']}»: puo' essere rosso per "
                              f"un'altra causa (una compilazione fallita "
                              f"rende rosso qualunque banco)")
        if risano is None:
            motivi.append("il ritorno al SANO non e' stato verificato: «vede "
                          "il guasto» e «e' rimasto rotto» hanno lo stesso "
                          "aspetto")
        elif risano["uscita"] != g.get("atteso_sano", 0):
            # ⛔ E LE DUE RAGIONI NON SONO LA STESSA — difetto trovato l'11
            #    agosto 2026 curando questo file, sul primo giro vero di B13.
            #
            #    «Il banco non e' tornato verde» ha due cause opposte: il
            #    guasto e' rimasto addosso al codice, oppure il banco era gia'
            #    rosso in partenza e ci e' tornato esattamente.  Stampare
            #    «qualcosa e' rimasto addosso al codice» sul secondo caso e'
            #    il rosso puntato sull'imputato sbagliato, e manda a cercare
            #    un guasto residuo che non c'e' — dentro lo strumento che
            #    esiste per non mandare nessuno a cercare nel posto sbagliato.
            if sano is not None and risano["uscita"] == sano["uscita"]:
                motivi.append(f"il banco e' tornato ESATTAMENTE dov'era "
                              f"({risano['uscita']}), ⭐ quindi il guasto non "
                              f"e' rimasto addosso al codice — ma quel punto "
                              f"di partenza non era quello dichiarato, e la "
                              f"certificazione non si puo' dare lo stesso")
            else:
                motivi.append(f"⛔ dopo aver tolto il guasto il banco esce "
                              f"{risano['uscita']} e prima usciva "
                              f"{sano['uscita'] if sano else '?'}: qualcosa "
                              f"e' rimasto addosso al codice")
        if motivi:
            no.append((sigla, motivi))
            print(f"  {ROSSO}NO{GRIGIO}  {sigla}  NON certificato")
            for m in motivi:
                print(f"        {m}")
        else:
            certificati.append(sigla)
            print(f"  {VERDE}OK{GRIGIO}  {sigla}  ⭐ certificato: "
                  f"{sano['uscita']} → {rotto['uscita']} → "
                  f"{risano['uscita']}")
            print(f"        marca «{g['marca']}»: vista nel rosso, e il giro "
                  f"sano NON la diceva")
        print(f"        guasto: {g.get('titolo', '?')}")

    # ── IL DENOMINATORE, E QUI E' LA COSA CHE CONTA ────────────────────────
    non_toccati = sorted(set(GUASTI) - set(per_sigla))
    print()
    print("    == quel che questo giro ha davvero certificato")
    print(f"    --  guasti nel catalogo:            {len(GUASTI)}")
    print(f"    --  guasti provati in questo giro:  {len(per_sigla)}")
    print(f"    {VERDE}{len(certificati):3d}{GRIGIO}  banchi CERTIFICATI: "
          f"{', '.join(certificati) or '—'}")
    print(f"    {ROSSO}{len(no):3d}{GRIGIO}  banchi provati e NON certificati: "
          f"{', '.join(s for s, _ in no) or '—'}")
    print(f"    {GIALLO}{len(saltati):3d}{GRIGIO}  banchi non lanciabili da "
          f"qui: {', '.join(saltati) or '—'}")
    # ⛔ E LA PAROLA E' «NON PROVATI IN QUESTO GIRO», NON «MAI» — R12-A.4.
    #    Il conto e' `set(GUASTI) - set(per_sigla)`, che e' un conto **per
    #    giro**: chiamarlo «mai provati» ha fatto scrivere `mai_provati` su
    #    B7 e C2 due ore dopo averli certificati, e su B13 dopo averlo provato
    #    e bocciato.  Chi legge il registro ha diritto a sapere quel che il
    #    progetto sa, non quel che l'ultimo giro ha toccato.
    print(f"    {GIALLO}{len(non_toccati):3d}{GRIGIO}  banchi NON PROVATI IN "
          f"QUESTO GIRO: {', '.join(non_toccati) or '—'}")
    print("        ⚠ «non provati in questo giro» non e' «mai provati»: quel")
    print("          che si sa di loro sta nelle righe di prima, e lo mette")
    print("          insieme `--registro`.")
    print("        ⛔ E nessuno di questi e' «pulito»: fuori da una "
          "certificazione valida sono NON CERTIFICATI.")

    # ⛔ Il registro, con la data e le impronte dei file che contano davvero.
    sorgente = os.path.join(QUI, "rcp", "rcp.c")
    riga = {
        "quando": datetime.datetime.now().isoformat(timespec="seconds"),
        # ⛔ E DA QUALE MACCHINA, perche' non e' un dettaglio: questo registro
        #    ha lo stesso nome in due posti — sulla macchina dei documenti e su
        #    quella di prova — e le righe finiscono nello stesso file.  ⚠ E'
        #    anche la ragione per cui l'ordine di scrittura non e' l'ordine del
        #    tempo (R12-A.4), e per cui B4 e B9 si possono certificare solo di
        #    qua e C2 e B13 solo di la': i file dei banchi non stanno tutti
        #    sulla stessa macchina.  Una riga senza questo campo non dice se
        #    «non provato» voglia dire «non provabile da li'».
        "macchina": socket.gethostname(),
        "certificati": certificati,
        "non_certificati": [s for s, _ in no],
        "saltati": saltati,
        "non_provati_in_questo_giro": non_toccati,
        # ⛔ L'impronta PER BANCO, sui file che quella certificazione ha
        #    davvero usato (R12-A.5).  `impronta_rcp_c` resta per continuita'
        #    con le due righe del 10 agosto, ⚠ ma non e' piu' il denominatore:
        #    `rcp.c` non partecipa alla certificazione di B4 e di B9.
        "impronte": {s: impronte_di(s) for s in sorted(per_sigla)},
        "impronta_rcp_c": (impronta_file(sorgente) or "?")[:32],
    }
    try:
        with open(REGISTRO, "a", encoding="utf-8") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
        print(f"\n    --  scritto in {REGISTRO}")
        print("        ⚠ La certificazione ha una DATA e l'impronta dei file")
        print("          che ha usato: un banco certificato su file che nel")
        print("          frattempo sono cambiati non e' certificato oggi, e")
        print("          `--registro` lo dice invece di lasciarlo credere.")
    except OSError as e:
        print(f"\n    {GIALLO}[?] il registro non si e' scritto: {e}{GRIGIO}")

    # ⛔ ZERO BANCHI PROVATI NON E' «TUTTO A POSTO».
    if not per_sigla:
        print(f"\n    {ROSSO}⛔ B12 non ha provato NESSUN banco: non e' un "
              f"verde{GRIGIO}")
        return 2
    if no or saltati:
        return 1
    if non_toccati:
        return 3
    return 0


# ===========================================================================
# ⛔ IL REGISTRO LETTO COME UNA STORIA, NON COME UN'ULTIMA RIGA — R12-A.4
# ===========================================================================
def _normalizza(r):
    """Una riga vecchia e una nuova, lette con lo stesso metro."""
    return {
        "quando": r.get("quando", "?"),
        "macchina": r.get("macchina", "?"),
        "certificati": r.get("certificati", []),
        "non_certificati": r.get("non_certificati", []),
        "saltati": r.get("saltati", []),
        # ⚠ Le righe scritte prima dell'11 agosto 2026 chiamavano questo campo
        #   `mai_provati`, e la parola era falsa: qui si legge col nome vero.
        "non_provati": r.get("non_provati_in_questo_giro",
                             r.get("mai_provati", [])),
        "impronte": r.get("impronte", {}),
        "impronta_rcp_c": r.get("impronta_rcp_c", "?"),
        "vecchio_nome": "mai_provati" in r,
    }


def mostra_registro():
    if not os.path.exists(REGISTRO):
        print(f"    {GIALLO}[?]{GRIGIO} nessun registro in {REGISTRO}: "
              f"⛔ nessun banco di questa fase e' mai stato certificato")
        return 3
    with open(REGISTRO, encoding="utf-8") as f:
        grezze = [json.loads(r) for r in f if r.strip()]
    if not grezze:
        print(f"    {GIALLO}[?]{GRIGIO} il registro e' vuoto: ⛔ nessun banco "
              f"e' mai stato certificato")
        return 3
    righe = [_normalizza(r) for r in grezze]

    # ⛔ E L'ORDINE DI SCRITTURA NON E' L'ORDINE DEL TEMPO.  Nel file del
    #    10 agosto 2026 la riga delle 21:19 sta **sotto** quella delle 23:01,
    #    perche' le due macchine scrivono nello stesso file in momenti diversi.
    #    Chi legge «l'ultima riga» legge la piu' vecchia e non se ne accorge.
    ordinate = sorted(righe, key=lambda r: r["quando"])
    if [r["quando"] for r in ordinate] != [r["quando"] for r in righe]:
        print(f"    {GIALLO}⚠ ATTENZIONE{GRIGIO}: nel file l'ordine di "
              f"scrittura NON e' l'ordine del tempo —")
        print("      la riga in fondo non e' la piu' recente.  Qui sotto sono "
              "ordinate per data.")
        macchine = sorted({r["macchina"] for r in righe})
        if len(macchine) > 1:
            print(f"      ⛔ E LE DATE VENGONO DA {len(macchine)} OROLOGI "
                  f"DIVERSI ({', '.join(macchine)}): l'11 agosto 2026 la")
            print("        macchina di prova era indietro di circa due ore "
                  "sulla macchina dei")
            print("        documenti.  ⚠ Quindi nemmeno l'ordine per data e' "
                  "l'ordine del tempo vero,")
            print("        e due righe di macchine diverse non si possono "
                  "mettere in fila fra loro.")
            print("        Il campo «macchina» e' li' per questo: si legge "
                  "PRIMA della data.")
        print()

    print("== I giri, dal piu' vecchio al piu' recente")
    for r in ordinate:
        print(f"  {r['quando']}  su «{r['macchina']}»  "
              f"rcp.c {r['impronta_rcp_c'][:16]}…")
        print(f"      certificati            : "
              f"{', '.join(r['certificati']) or '—'}")
        print(f"      NON certificati        : "
              f"{', '.join(r['non_certificati']) or '—'}")
        if r["saltati"]:
            print(f"      non lanciabili da li'  : {', '.join(r['saltati'])}")
        print(f"      non provati IN QUEL GIRO: "
              f"{', '.join(r['non_provati']) or '—'}")
        if r["vecchio_nome"]:
            print(f"      {GIALLO}⚠ riga scritta col vecchio campo "
                  f"«mai_provati»{GRIGIO}: la parola era falsa — quei banchi")
            print("        possono essere stati provati in un altro giro, e "
                  "sotto si vede.")

    # ── ⛔ CHE COSA SI SA OGGI DI OGNI BANCO ────────────────────────────────
    print()
    print("== ⛔ Che cosa si sa OGGI di ciascun banco")
    print("   (dall'ultima riga che ne dice qualcosa — non dall'ultima riga "
          "del file)")
    print()
    # ⛔ E «SCADUTA» E «NON VERIFICABILE» SONO DUE COSE DIVERSE, come «provato e
    #    non riuscito» e «mai provato»: la prima dice che i file sono cambiati,
    #    la seconda che la riga non porta nessuna impronta e quindi non si puo'
    #    nemmeno dire se siano cambiati.  Fonderle sarebbe rifare, in piccolo,
    #    l'arrotondamento del rilievo R12-A.4.
    certi_oggi, scaduti, ciechi, non_certi, mai = [], [], [], [], []
    for sigla in sorted(GUASTI):
        ultimo = None
        for r in ordinate:
            if sigla in r["certificati"]:
                ultimo = (r, "certificato")
            elif sigla in r["non_certificati"]:
                ultimo = (r, "non certificato")
            elif sigla in r["saltati"]:
                ultimo = (r, "non lanciabile da li'")
        if ultimo is None:
            # ⭐ E SOLO QUI la parola «mai» e' vera.
            mai.append(sigla)
            print(f"  {GIALLO}[?]{GRIGIO} {sigla:4s} MAI PROVATO — nessun giro "
                  f"del registro lo nomina")
            continue
        r, stato = ultimo
        if stato != "certificato":
            non_certi.append(sigla)
            print(f"  {ROSSO}NO {GRIGIO} {sigla:4s} {stato.upper()} il "
                  f"{r['quando']} (su «{r['macchina']}»)")
            continue
        verdetto, perche = confronta_impronte(r["impronte"].get(sigla),
                                              impronte_di(sigla))
        if verdetto == "uguali":
            certi_oggi.append(sigla)
            print(f"  {VERDE}OK {GRIGIO} {sigla:4s} CERTIFICATO il "
                  f"{r['quando']} su «{r['macchina']}» — e vale oggi "
                  f"({perche})")
        elif verdetto == "cambiate":
            scaduti.append(sigla)
            print(f"  {ROSSO}NO {GRIGIO} {sigla:4s} certificato il "
                  f"{r['quando']} su «{r['macchina']}», ⛔ MA NON OGGI")
            print(f"        {perche}")
            print("        ⛔ Un banco certificato su file che nel frattempo "
                  "sono cambiati non e'")
            print("           certificato: la riga vale per quei byte, non per "
                  "questi.")
        else:
            ciechi.append(sigla)
            print(f"  {ROSSO}NO {GRIGIO} {sigla:4s} certificato il "
                  f"{r['quando']} su «{r['macchina']}», ⛔ MA NON SI PUO' DIRE "
                  f"SE VALGA OGGI")
            print(f"        {perche}")
            print("        ⚠ E «non si sa» non si arrotonda a «certificato»: "
                  "una certificazione")
            print("          che non si puo' riverificare non e' una "
                  "certificazione (LEZIONI.md §1.9).")

    # ── ⛔ IL CONTO, E IL SUO DENOMINATORE ──────────────────────────────────
    print()
    print("    == il conto onesto")
    print(f"    --  banchi nel catalogo:                     {len(GUASTI)}")
    print(f"    {VERDE}{len(certi_oggi):3d}{GRIGIO}  CERTIFICATI OGGI: "
          f"{', '.join(certi_oggi) or '—'}")
    print(f"    {ROSSO}{len(scaduti):3d}{GRIGIO}  certificazione SCADUTA "
          f"(i file sono cambiati): {', '.join(scaduti) or '—'}")
    print(f"    {ROSSO}{len(ciechi):3d}{GRIGIO}  certificazione NON "
          f"RIVERIFICABILE (la riga non porta impronte): "
          f"{', '.join(ciechi) or '—'}")
    print(f"    {ROSSO}{len(non_certi):3d}{GRIGIO}  provati e NON certificati: "
          f"{', '.join(non_certi) or '—'}")
    print(f"    {GIALLO}{len(mai):3d}{GRIGIO}  MAI PROVATI: "
          f"{', '.join(mai) or '—'}")
    print()
    # ⛔ E UN VERDETTO CHE NON DICE QUANTE COSE HA APPROVATO NON E' UN VERDETTO
    #    (`LEZIONI.md` §1.9 regola 6).  Zero certificati non e' un verde.
    if not certi_oggi:
        print(f"    {ROSSO}⛔ NESSUN banco e' certificato oggi: non e' un "
              f"verde, e non e' «tutto pulito»{GRIGIO}")
        return 3
    print(f"    {VERDE}⭐ {len(certi_oggi)} banchi su {len(GUASTI)} hanno una "
          f"certificazione che regge oggi{GRIGIO}")
    if scaduti or ciechi or non_certi or mai:
        print(f"    {ROSSO}⛔ e gli altri {len(GUASTI) - len(certi_oggi)} NON "
              f"sono «puliti»: sono NON CERTIFICATI{GRIGIO}")
        return 3
    return 0


def mostra_impronte(sigla):
    """I file su cui la certificazione di un banco poggia, e la loro impronta."""
    g = GUASTI[sigla]
    print(f"== {sigla} — i file su cui la certificazione poggia")
    print(f"   guasto: {g['titolo']}\n")
    imp = impronte_di(sigla)
    if not imp:
        print(f"    {GIALLO}[?]{GRIGIO} nessun file dichiarato: la "
              f"certificazione di {sigla} non ha denominatore")
        return 3
    ciechi = 0
    for nome, sha in sorted(imp.items()):
        if sha is None:
            ciechi += 1
            print(f"    {GIALLO}[?]{GRIGIO} {nome:34s} ⛔ non si legge da qui "
                  f"— «non ho guardato» non e' «non e' cambiato»")
        else:
            print(f"    --  {nome:34s} {sha[:32]}…")
    print(f"\n    --  {len(imp)} file, {len(imp) - ciechi} letti, "
          f"{ciechi} non leggibili da questa macchina")
    return 0 if ciechi == 0 else 3


def elenco():
    print("== ⛔ B12 — un guasto costruito a mano PER OGNI BANCO")
    print(f"   {len(GUASTI)} guasti nel catalogo.\n")
    senza_marca = []
    for sigla in sorted(GUASTI):
        g = GUASTI[sigla]
        print(f"  {sigla:4s} [{g['costa']:15s}] {g['titolo']}")
        print(f"       dove:     {risolvi(g['dove'])}")
        if g["sostituisci_con"]:
            print(f"       con:      {risolvi(g['sostituisci_con'])}")
        print(f"       dimostra: {g['dimostra'][:400]}")
        if g["marca"]:
            print(f"       ⛔ marca che l'uscita rossa DEVE contenere, e che il "
                  f"giro SANO non deve dire: «{g['marca']}»")
        else:
            senza_marca.append(sigla)
            print("       ⛔ NESSUNA MARCA: questo guasto NON PUO' CERTIFICARE. "
                  "Il rosso non si")
            print("          attribuirebbe a lui, e `--giudica` lo rifiuta "
                  "invece di saltare il controllo.")
        print(f"       file su cui la certificazione poggia: "
              f"{', '.join(g['file_che_contano']) or '⛔ nessuno dichiarato'}")
        if g["nota"]:
            print(f"       {g['nota']}")
        print(f"       {g['riferimento']}")
        print()
    leggeri = [s for s, g in GUASTI.items()
               if g["costa"] in ("leggero", "copia-di-file")]
    print(f"  ⭐ I guasti che non vogliono una ricostruzione — "
          f"{', '.join(sorted(leggeri))} —")
    print("     sono quelli che si possono certificare in minuti.")
    # ⛔ E IL DENOMINATORE DEL CATALOGO, che e' la cosa che il catalogo taceva.
    print(f"\n  {ROSSO}⛔ {len(senza_marca)} guasti su {len(GUASTI)} non hanno "
          f"una marca{GRIGIO}: {', '.join(senza_marca) or '—'}")
    print("     Nessuno di questi puo' certificare il proprio banco, e finche' "
          "il campo e'")
    print("     vuoto il banco resta NON CERTIFICATO — non «pulito».")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B12 — un guasto costruito a mano per ogni banco")
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--verifica", metavar="SIGLA")
    p.add_argument("--applica", metavar="SIGLA")
    p.add_argument("--togli", metavar="SIGLA")
    p.add_argument("--giudica", metavar="ESITI")
    p.add_argument("--registro", action="store_true")
    # ⛔ Due domande che l'orchestratore deve poter fare senza rileggersi
    #    questo file da dentro una shell: chi le pone da fuori con `exec()` si
    #    costruisce una seconda verita' sul catalogo, e il giorno in cui le due
    #    divergono nessuno se ne accorge.
    p.add_argument("--marca", metavar="SIGLA",
                   help="la stringa che l'uscita del banco rosso DEVE contenere")
    p.add_argument("--costa", metavar="SIGLA",
                   help="leggero | ricostruisce | copia-di-file | gia-fatto")
    p.add_argument("--impronte", metavar="SIGLA",
                   help="i file su cui la certificazione di quel banco poggia")
    p.add_argument("--provabile", metavar="SIGLA",
                   help="i file su cui la certificazione poggia ci sono, su "
                        "questa macchina?  Stampa «MANCA <nome>» per ognuno "
                        "che non c'e' (R12-A.31)")
    p.add_argument("--certificati", default=CERT_PREDEFINITA,
                   help="la cartella dei certificati (per i guasti «{CERT}»)")
    a = p.parse_args()
    CERT = a.certificati
    if a.impronte:
        if a.impronte not in GUASTI:
            print(f"⛔ sigla sconosciuta: {a.impronte}")
            sys.exit(2)
        sys.exit(mostra_impronte(a.impronte))
    if a.elenco:
        sys.exit(elenco())
    if a.registro:
        sys.exit(mostra_registro())
    if a.giudica:
        sys.exit(giudica(a.giudica))
    if a.provabile:
        sys.exit(provabile(a.provabile))
    for campo in ("marca", "costa"):
        sigla = getattr(a, campo)
        if sigla:
            if sigla not in GUASTI:
                print("")
                sys.exit(2)
            print(GUASTI[sigla][campo])
            sys.exit(0)
    for azione, f in (("verifica", verifica), ("applica", applica),
                      ("togli", togli)):
        sigla = getattr(a, azione)
        if sigla:
            if sigla not in GUASTI:
                print(f"⛔ sigla sconosciuta: {sigla}.  Le sigle: "
                      f"{', '.join(sorted(GUASTI))}")
                sys.exit(2)
            r = f(sigla)
            sys.exit(0 if (azione == "verifica" and r == 1) or
                     (azione != "verifica" and r == 0) else 1)
    p.print_help()
    sys.exit(2)
