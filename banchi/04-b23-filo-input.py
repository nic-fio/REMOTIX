#!/usr/bin/env python3
"""04-b23-filo-input.py — ⛔ B23: il GIUDICE del canale di input (`RCP.md` §7.3).

    ./04-b23-filo-input            (compila, gira e giudica)
    python3 04-b23-filo-input.py --traccia 04-b23-traccia.jsonl
    python3 04-b23-filo-input.py --elenco     (le previsioni, senza misurare)

===========================================================================
⛔ PERCHE' QUESTO FILE E' SEPARATO DA `04-b23-filo-input.c`

Quello manda i byte e scrive che cosa e' uscito.  Questo tiene le PREVISIONI e
dice se tornano.  ⛔ Sono due programmi in due linguaggi, e nessuno dei due
importa l'altro: se i due lettori tornassero a essere uno, la fase 4 comprerebbe
un arbitro per poi buttarlo (`RCP.md` §0, e la forma del difetto muto che P18 ha
pagato — «il server e la pagina andavano d'accordo perche' li ha scritti la
stessa mano»).

===========================================================================
⛔⭐ LE SEI COSE CHE OGNI VIOLAZIONE DEVE SODDISFARE

  1. ⛔ **SU QUALE BYTE**.  L'indice e' scritto qui sotto PRIMA di misurare, e
     la traccia lo porta perche' il cliente consegna i byte **uno alla volta**.
     ⚠ «La violazione e' stata accusata» e' una misura debole: un server che
     accumula un megabyte e poi si accorge che la lunghezza non torna la accusa
     anche lui — e ha gia' regalato il megabyte che §6.1 gli vieta di regalare.
     ⭐ Questa colonna e' l'unica che distingue i due;
  2. **il motivo giusto**, letto DAL LATO CHE RICEVE — dai byte del `CONGEDO`
     usciti sul canale di controllo, non dal registro del server (`CODER.md`
     §3.8, `RCP.md` §8.1);
  3. ⛔ **in quale MESSAGGIO**: `ERRORE_PROTOCOLLO` viaggia in `CONGEDO` (§11).
     Nessuna violazione di §7.3 viaggia in `RESPINTO`: quello e' il congedo
     dell'autenticazione, e siamo molto oltre;
  4. ⛔ **§3.1 punto 3** — il motivo dentro il codice di chiusura della
     sessione, che e' un DEVE **incondizionato** e che §3.1 chiama «quello che
     salva le diagnosi».  Si conta, con il suo denominatore;
  5. **che la sessione sia davvero finita** dopo;
  6. ⛔ **e che una connessione NUOVA arrivi a `ECCOMI`**.  Un server che resta
     rotto dopo un rifiuto e' un difetto che il conteggio delle violazioni non
     vede — ed e' la meta' del banco che nessuno scrive.

===========================================================================
⭐ E I CASI CHE DEVONO PASSARE VALGONO QUANTO LE VIOLAZIONI

Senza di loro «il server chiude su tutto» darebbe verde su tutto.  ⛔ E non
basta che la sessione regga: si guarda **che cosa e' stato iniettato**, valore
per valore.  Un server che accettasse ogni messaggio e non iniettasse mai niente
passerebbe un banco che guarda la sola sopravvivenza — ed e' `CODER.md` §4.6, il
verde che non e' vero.

⛔ **E QUANTI SONO NON STA SCRITTO IN NESSUN COMMENTO**: i due numeri li calcola
`conta()` dalle previsioni, e la riga finale li stampa ciascuno col proprio
denominatore.  Un numero scritto a mano e' il numero che nessuno ricalcola
(rilievo R7.14: tre su tre non tornavano).
"""
import argparse
import json
import os
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))

ERRORE_PROTOCOLLO = 0x0B
CHIUSO_DALL_UTENTE = 0x01

VERDE, ROSSO, GIALLO, GRIGIO = "\033[32m", "\033[31m", "\033[33m", "\033[0m"

# ⛔ LA TELA DELLA SCENA, dichiarata: il cliente attacca a 1920×1080, e su quella
#    tela l'angolo in basso a destra e' (1919, 1079) — `RCP.md` §7.3.
TELA_L, TELA_A = 1920, 1080

# ===========================================================================
# ⛔ LE PREVISIONI.  Ogni riga e' scritta PRIMA di misurare (`LEZIONI.md` §1.11)
#    e porta il paragrafo che la impone.
#
#    violazione: (byte_atteso, motivo_atteso, "perche'")
#    ⭐ verde:    None al posto del motivo, piu' quel che DEVE essere iniettato
# ===========================================================================

# I sei byte dell'intestazione di §6.1: quando il guasto sta li' dentro, il
# server ha tutto quel che gli serve per giudicare al byte 5 — e non uno di piu'.
INTESTAZIONE = 5

# I cinque corpi di §7.3, e da qui gli indici dell'ultimo byte del messaggio.
#   u32 id + u64 istante = 12 comuni
LUNG = {"puntatore": 20, "pulsante": 15, "rotella": 20, "lettera": 16,
        "posizione": 15}
FINE = {k: 6 + v - 1 for k, v in LUNG.items()}   # 25 · 20 · 25 · 21 · 20

VIOLAZIONI = {
    # ── §2.5: il canale, riconosciuto dal byte alto del `tipo` ──────────────
    "canale-controllo-su-input": (
        INTESTAZIONE, "§2.5: il controllo vive solo sul primo stream "
        "bidirezionale, e uno 0x00 su uno stream unidirezionale e' "
        "ERRORE_PROTOCOLLO"),
    "canale-appunti-su-input": (
        INTESTAZIONE, "§2.5: gli appunti vogliono uno stream loro per "
        "trasferimento, non lo stream riservato all'input"),
    "canale-video-su-input": (
        INTESTAZIONE, "§2.5: «un canale usato nel verso sbagliato — un 0x03 che "
        "arriva dal client — e' ERRORE_PROTOCOLLO»"),
    "canale-audio-su-input": (
        INTESTAZIONE, "§2.5, §6.3: l'audio vive solo sui datagram; su uno "
        "stream e' ERRORE_PROTOCOLLO"),
    "canale-sconosciuto": (
        INTESTAZIONE, "§2.5: «un byte alto diverso da questi cinque e' "
        "ERRORE_PROTOCOLLO»"),

    # ── §7.3: i cinque tipi, e nessun altro ────────────────────────────────
    "tipo-0x0100": (
        INTESTAZIONE, "§7.3 numera da 0x0101 a 0x0105; §3 vieta di ignorare un "
        "tipo che non si conosce"),
    "tipo-0x0106": (
        INTESTAZIONE, "uno oltre l'ultimo: il confine si prova dai due lati"),

    # ── §6.1: la lunghezza che non torna ───────────────────────────────────
    "lunghezza-in-piu": (
        INTESTAZIONE, "§6.1: «un ricevente che legge una lunghezza incoerente "
        "con quel che il tipo prevede DEVE chiudere».  ⛔ E al byte 5: la "
        "lunghezza dei cinque tipi si sa dal solo `tipo`"),
    "lunghezza-in-meno": (
        INTESTAZIONE, "dall'altro lato dello stesso confine"),
    "pulsante-allineato-a-16": (
        INTESTAZIONE, "⛔ §6.0: il PULSANTE occupa QUINDICI byte.  «Un byte in "
        "piu' che fa tornare i conti in una struttura C» e' la forma esatta del "
        "difetto corretto in §6.2 il 9 agosto 2026"),
    "lunghezza-1mib": (
        INTESTAZIONE, "⛔⭐ §6.1: «la lunghezza si controlla PRIMA di allocare.  "
        "Un ricevente che alloca `lunghezza` byte e poi verifica ha gia' "
        "regalato un megabyte a chiunque sappia scrivere sei byte».  ⚠ Qui il "
        "corpo non si manda affatto: un server che aspettasse i byte non "
        "accuserebbe MAI"),
    "lunghezza-4gib": (
        INTESTAZIONE, "§6.1, e un server ucciso dal nucleo «fa cadere la "
        "connessione» esattamente come uno che congeda — portandosi via le "
        "sessioni di tutti gli altri"),

    # ── §7.3: l'identificatore ─────────────────────────────────────────────
    "id-zero": (
        FINE["puntatore"], "§7.3: «⛔ 0 e' riservato e vuol dire nessun input».  "
        "E' il valore che §6.2 mette nel campo `input` dei fotogrammi quando non "
        "c'e' stato niente"),
    "id-ripetuto": (
        FINE["puntatore"], "§7.3: «cresce di ALMENO UNO a ogni messaggio»; "
        "ripetersi non e' crescere"),
    "id-indietro": (
        FINE["puntatore"], "idem, dall'altra parte: 4 dopo 9"),
    "id-per-tipo-invece-che-per-canale": (
        FINE["puntatore"], "⛔⭐ §7.3: «su TUTTO il canale di input — non uno "
        "per tipo».  Con cinque contatori separati questo PUNTATORE(4) dopo un "
        "PULSANTE(9) e' un legittimo «primo PUNTATORE» e PASSA: e' il caso che "
        "distingue le due implementazioni, e senza di lui il banco non le "
        "distingue"),

    # ── §7.3: le coordinate, e il rilievo R1.16 ────────────────────────────
    "x-1920-su-tela-1920": (
        FINE["puntatore"], f"§7.3: «0 <= x < {TELA_L}».  Su una tela {TELA_L} il "
        f"pixel {TELA_L} non esiste"),
    "y-1080-su-tela-1080": (
        FINE["puntatore"], f"idem sull'altro asse: 0 <= y < {TELA_A}"),
    "x-enorme": (
        FINE["puntatore"], "0xFFFFFFFF: il caso grossolano, che deve cadere "
        "come quello sottile"),
    "grazia-scaduta": (
        FINE["puntatore"], "§7.1: «passato quel secondo, sono "
        "ERRORE_PROTOCOLLO».  Qui sono passati 1501 ms"),
    "grazia-non-copre-le-coordinate-sbagliate": (
        FINE["puntatore"], "⛔ la grazia di §7.1 copre le coordinate valide "
        "sulla tela PRECEDENTE, non le coordinate sbagliate: (5000,5000) non e' "
        "mai stata valida su nessuna delle due"),

    # ── §7.3: premuto ──────────────────────────────────────────────────────
    "pulsante-premuto-2": (
        FINE["pulsante"], "§7.3: «1 = premuto, 0 = rilasciato», e §3 chiude su "
        "«un campo fuori intervallo».  ⚠ Un 2 letto come «vero» e' il parser "
        "indulgente che §3 esiste per togliere"),
    "posizione-premuto-255": (
        FINE["posizione"], "lo stesso campo sull'altro messaggio"),

    # ── §7.3: il carattere ─────────────────────────────────────────────────
    "lettera-oltre-10ffff": (
        FINE["lettera"], "§7.3: «da 0 a 0x10FFFF».  0x110000 e' uno oltre"),
    "lettera-surrogato-d800": (
        FINE["lettera"], "⛔ §7.3: «esclusi i surrogati 0xD800-0xDFFF».  ⚠ E' il "
        "caso che una pagina produce da sola: JavaScript conta in UTF-16, e "
        "`charCodeAt` su un'emoji restituisce META' COPPIA SURROGATA.  Un "
        "controllo fermo a `> 0x10FFFF` lo lascerebbe passare"),
    "lettera-surrogato-dfff": (
        FINE["lettera"], "l'altro estremo dello stesso intervallo"),
    "lettera-ffffffff": (
        FINE["lettera"], "tutti i bit a uno"),

    # ── §2.5: lo stato e lo stream ─────────────────────────────────────────
    "input-prima-di-sessione": (
        0, "⛔ §2.5: lo stream di input si apre DOPO aver ricevuto `SESSIONE`.  "
        "⭐ E il giudizio e' legittimo perche' il server misura una cosa che ha "
        "fatto LUI — se `SESSIONE` e' partita — non l'ordine di arrivo fra due "
        "stream (che e' la trappola di P20).  ⇒ Al byte 0: non serve leggere "
        "niente"),
    "secondo-stream-di-input": (
        0, "§2.5: lo stream di input e' **uno solo**, e tenuto aperto"),
}

# ===========================================================================
# ⭐ I CASI CHE DEVONO PASSARE.
#
#    (iniezioni_attese, ultimo_iniettato_atteso, campo_input_atteso, "perche'")
#    · iniezioni_attese: la lista esatta, in ordine, di quel che i ganci di
#      `input.h` devono aver ricevuto.  ⛔ La LISTA, non il conteggio: un server
#      che iniettasse la coordinata sbagliata avrebbe lo stesso conteggio;
#    · campo_input_atteso: `None` = nessun fotogramma in questo caso.
# ===========================================================================
VERDI = {
    "ok-puntatore-0-0": (
        [("puntatore", 0, 0)], 1, None, "l'angolo in alto a sinistra"),
    "ok-puntatore-al-bordo-1919-1079": (
        [("puntatore", TELA_L - 1, TELA_A - 1)], 1, None,
        "⛔⭐ IL BORDO, e ha gia' un rilievo scritto contro di se' (R1.16): su "
        "una tela 1920×1080 «l'angolo in basso a destra e' 1919, 1079».  Un "
        "controllo scritto con `>` invece di `>=` lo rifiuta, e il sintomo e' "
        "una colonna di pixel a destra che non si puo' cliccare.  ⚠ E chiudere "
        "la sessione per un arrotondamento e' quel che `SPECIFICHE.md` §8.3 "
        "vieta — «mai staccare»"),
    "ok-pulsante-premuto": (
        [("pulsante", 0x110, 1)], 1, None,
        "§7.3: i codici sono quelli di evdev, `BTN_LEFT` = 0x110"),
    "ok-pulsante-rilasciato": (
        [("pulsante", 0x110, 0)], 1, None, "e il rilascio e' 0, non l'assenza"),
    "ok-posizione-key-a": (
        [("posizione", 30, 1)], 1, None, "§7.3: `KEY_A` = 30, in evdev"),
    "ok-rotella-uno-scatto-su": (
        [("rotella", 0, 120)], 1, None,
        "⛔⛔ +120 DEVE arrivare al gancio come +120.  §7.3 e `src/input.h` "
        "dicono che l'inversione dell'asse verticale si fa DENTRO "
        "`input_rotella()`, «una volta sola, in un posto solo»: se la facesse "
        "anche `rcp.c` le due si annullerebbero, e la rotella andrebbe al "
        "contrario per OGNI utente (forma d'errore E11)"),
    "ok-rotella-uno-scatto-giu": (
        [("rotella", 0, -120)], 1, None,
        "⛔ il segno opposto, e si misura IL SEGNO — non «che qualcosa si "
        "muove».  E' il controllo che il riquadro di §7.3 pretende"),
    "ok-rotella-mezzo-scatto": (
        [("rotella", 0, 60)], 1, None,
        "⚠ §7.3: «i mezzi scatti esistono: 60 e' mezzo scatto e NON DEVE essere "
        "arrotondato a zero»"),
    "ok-rotella-orizzontale": (
        [("rotella", -120, 0)], 1, None, "l'altro asse, e non si tocca nemmeno lui"),
    "ok-rotella-zero": (
        [("rotella", 0, 0)], 1, None,
        "⛔ zero non e' un valore fuori intervallo: §7.3 non lo vieta, e "
        "inventare un divieto sarebbe inventare una regola"),
    "ok-lettera-a": ([("lettera", 0x61, 0)], 1, None, "una lettera qualunque"),
    "ok-lettera-accentata": (
        [("lettera", 0xE8, 0)], 1, None, "«è», che su una tastiera italiana c'e'"),
    "ok-lettera-fuori-dal-bmp": (
        [("lettera", 0x1F600, 0)], 1, None,
        "⭐ un valore scalare fuori dal BMP: e' proprio quel che una coppia "
        "surrogata rappresenta male, e qui arriva intero"),
    "ok-lettera-zero": (
        [("lettera", 0, 0)], 1, None,
        "⛔ §7.3 dice «da 0»: U+0000 e' un valore scalare Unicode valido.  ⚠ Non "
        "e' la regola dell'`id`, dove lo zero e' riservato — due campi, due "
        "regole, e ricopiare la prima sulla seconda rifiuterebbe un carattere "
        "che l'arbitro ammette"),
    "ok-lettera-10ffff": (
        [("lettera", 0x10FFFF, 0)], 1, None,
        "il limite superiore ESATTO passa; 0x110000 no.  I confini si provano "
        "dai due lati"),
    "ok-id-che-salta": (
        [("puntatore", 10, 10), ("puntatore", 11, 11)], 100, None,
        "§7.3: «cresce di ALMENO uno» — i salti sono leciti, e un client che "
        "scarta un evento suo non deve mentire sul numero"),
    "ok-tre-messaggi-in-un-pezzo": (
        [("puntatore", 10, 10), ("pulsante", 0x110, 1), ("lettera", 0x61, 0)],
        3, None,
        "tre tipi diversi in fila, con l'id che cresce SUL CANALE: e' il verso "
        "positivo del caso `id-per-tipo`"),
    "ok-grazia-satura": (
        [("puntatore", 1279, 719)], 1, None,
        "⭐ §7.1, terza eccezione dichiarata a §3: dentro il secondo, una "
        "coordinata valida sulla tela PRECEDENTE si SATURA all'ultimo pixel "
        "valido invece di chiudere.  ⛔ E si guarda il VALORE saturato "
        "(1279,719), non che sia passata: saturare al posto sbagliato e' un "
        "difetto che il solo «la sessione regge» non vede"),
    "ok-grazia-al-millesimo-1000": (
        [("puntatore", 1279, 719)], 1, None,
        "«per un secondo» comprende il millesimo 1000: il confine, dal lato che "
        "passa"),
    "ok-campo-input-torna-indietro": (
        [("puntatore", 10, 10), ("pulsante", 0x110, 1), ("lettera", 0x61, 0),
         ("posizione", 30, 1)], 9, 9,
        "⛔⭐ §6.2: «il campo `input` porta l'identificatore dell'ultimo input "
        "iniettato prima della cattura».  Quattro input con id 1, 2, 5, 9 e il "
        "fotogramma DEVE portare 9 — letto dai 28 byte veri, all'offset 24"),
    "ok-campo-input-zero-senza-input": (
        [], 0, 0,
        "§6.2: «0 se nessuno», ed e' il significato DICHIARATO dello zero — non "
        "un sentinella implicito (§6.0)"),
    "ok-campo-input-non-avanza-se-non-iniettato": (
        [("puntatore", 10, 10)], 0, 0,
        "⛔⭐ «INIETTATO», non «ricevuto».  Il gancio ha risposto -1: l'id 7 e' "
        "stato accettato dal protocollo e NON e' entrato nel campo `input`, "
        "perche' di un input non iniettato non c'e' nessun effetto da vedere "
        "nella scena.  ⚠ E la sessione REGGE: il client non ha sbagliato niente"),
    "ok-lettera-non-producibile": (
        [("lettera", 0x1E9, 0)], 0, 0,
        "§7.3: «se una LETTERA non e' producibile nella disposizione della "
        "sessione, il server DEVE scriverlo nel registro e NON DEVE mandare un "
        "carattere diverso ne' tacere».  ⇒ La sessione regge, e il campo "
        "`input` non avanza"),
    "ok-senza-ganci-la-sessione-regge": (
        [], 0, None,
        "⛔ «Non ho un canale di input» e «il client ha sbagliato» sono due "
        "fatti diversi (`LEZIONI.md` §1.9 regola 1).  Il messaggio era valido in "
        "ogni sua parte: chiudere qui punirebbe chi non ha sbagliato niente"),
    "ok-rilascio-al-distacco-una-volta-sola": (
        [("pulsante", 0x110, 1)], 1, None,
        "⭐ §7.3, ultimo capoverso — `RCP.md` §11 la chiama «la regola col "
        "rapporto danno/costo piu' alto del documento».  ⛔ E UNA VOLTA SOLA: "
        "il congedo e la liberazione si susseguono, e due chiamate scriverebbero "
        "due righe che dicono cose diverse sullo stesso fatto"),
}

# ⛔ Il caso qui sopra e' l'unico verde che chiude la sessione APPOSTA, e con un
#    motivo che non e' ERRORE_PROTOCOLLO: si dichiara qui invece di infilare un
#    `if` nel giudizio.
CHIUDE_APPOSTA = {"ok-rilascio-al-distacco-una-volta-sola": CHIUSO_DALL_UTENTE}

# ⛔ E il rilascio di §7.3 si conta a parte, col suo denominatore: e' una regola
#    che non ha niente a che vedere col messaggio, e metterla nello stesso conto
#    la nasconderebbe.
RILASCIO_ATTESO = 1  # esattamente UNA chiamata per sessione, non zero e non due


# ===========================================================================
# ⭐ §7.2 — `CURSORE_FORMA`, E LA LUNGHEZZA CHE IL SERVER NON DEVE SBAGLIARE
#
# ⛔ Terzo conto, e terzo denominatore: questi non sono violazioni del client ne'
#    verdi del client — sono prove di **autocontrollo del server**.  §7.2 fa
#    rilevare la lunghezza sbagliata a CHI RICEVE, quindi un messaggio storto
#    spedito da qui fa cadere la sessione **alla pagina**, e il registro del
#    server non ne saprebbe niente.  ⇒ La regola e' «nel dubbio non si manda».
#
# ⚠ I limiti di §5.5 — 256 per lato, il punto attivo dentro l'immagine, `0x0`
#   con `0,0` per il nascosto — NON si provano qui: li fa rispettare
#   `src/cursore.c`, e a provarli e' A6 in `04-b26-cursore`.  Pretenderli anche
#   qui vorrebbe dire avere la stessa regola in due posti, e il giorno in cui una
#   delle due cambiasse diventerebbero due regole.
#
#   (spedito?, lunghezza_attesa, l, a, ax, ay, "perche'")
#   · spedito False ⇒ ⛔ NESSUN byte di `CURSORE_FORMA` deve uscire
CURSORI = {
    "ok-cursore-16x16-sul-filo": (
        True, 8 + 16 * 16 * 4, 16, 16, 3, 4,
        "§7.2: `8 + larghezza x altezza x 4`, e i campi tornano indietro come "
        "sono stati dati.  ⛔ E l'immagine si ricontrolla BYTE PER BYTE contro il "
        "disegno noto: con un riempimento di zeri, «memoria altrui» e "
        "«l'immagine giusta» avrebbero lo stesso aspetto"),
    "ok-cursore-256x256-il-massimo-di-5.5": (
        True, 8 + 256 * 256 * 4, 256, 256, 0, 0,
        "⛔ IL MASSIMO CHE §5.5 CONCEDE: 262 152 byte di corpo, 262 158 sul filo. "
        "⭐ DEVE passare — un tetto di §6.1 messo male qui ucciderebbe il cursore "
        "piu' grande che l'arbitro ammette, e il sintomo sarebbe «certi cursori "
        "non si vedono»"),
    "ok-cursore-nascosto-otto-byte": (
        True, 8, 0, 0, 0, 0,
        "§5.5: `0x0` con punto attivo `0,0` e' il cursore NASCOSTO, e sono otto "
        "byte di corpo esatti — nessun byte d'immagine"),
    # ⛔⭐ LA COPPIA DI §5.5, e vale solo intera.
    #
    #    `ok-cursore-nascosto-otto-byte` (0x0) DEVE passare; questi due no.
    #    ⚠ Col solo `0x0` un controllo che rifiutasse **tutti** gli zeri sarebbe
    #      verde, e farebbe sparire per sempre il cursore nascosto — il sintomo
    #      «il puntatore resta fermo quando entro in un campo di testo».
    #      Coi soli `0x5`/`5x0` non si vedrebbe il contrario.  ⇒ Nessuno dei tre
    #      casi, da solo, distingue le due implementazioni.
    "cursore-una-sola-a-zero-0x5": (
        False, 0, 0, 0, 0, 0,
        "⛔⭐ §5.5: «una sola delle due a zero e' ERRORE_PROTOCOLLO».  ⚠ E' "
        "L'UNICO caso in cui il controllo di lunghezza — che e' giusto — NON "
        "BASTA: `0x5` da' zero byte d'immagine, cioe' un messaggio di otto byte "
        "la cui lunghezza **TORNA**, e il valore malformato passa proprio il "
        "controllo che dovrebbe fermarlo.  ⛔ Il controllo sta in `rcp.c` ANCHE "
        "se sta in `cursore.c`, e non e' un doppione: la' si decide **che cos'e'** "
        "quel cursore, qui che non si EMETTE un messaggio che la specifica vieta "
        "— mai, da nessuna strada"),
    "cursore-una-sola-a-zero-5x0": (
        False, 0, 0, 0, 0, 0,
        "l'altro verso della stessa regola: i confini si provano dai due lati, e "
        "un controllo scritto su una sola delle due misure passerebbe questo"),
    "cursore-lunghezza-non-torna-in-meno": (
        False, 0, 0, 0, 0, 0,
        "⛔⭐ IL CASO PER CUI §7.2 SCRIVE LA REGOLA: si dichiara 16x16 e si "
        "portano 924 byte invece di 1024.  «Leggo quel che c'e' e vado avanti» "
        "confezionerebbe **un cursore fatto di memoria altrui** e lo "
        "spedirebbe"),
    "cursore-lunghezza-non-torna-in-piu": (
        False, 0, 0, 0, 0, 0,
        "l'altro lato dello stesso confine: meno pericoloso e ugualmente "
        "sbagliato, perche' §7.2 vuole la lunghezza ESATTA e il client chiude "
        "comunque"),
    "cursore-immagine-nulla-con-misura": (
        False, 0, 0, 0, 0, 0,
        "⛔ una misura addosso e nessuna immagine: leggerla non sarebbe un "
        "messaggio storto, sarebbe la fine del processo"),
    "cursore-oltre-1mib": (
        False, 0, 0, 0, 0, 0,
        "§6.1: «nessun messaggio DEVE superare 1 MiB», inquadratura compresa.  "
        "⚠ 512 e' gia' oltre §5.5 e `cursore.c` non lo farebbe passare: quel che "
        "si prova qui NON e' il limite di §5.5, e' che il tetto del MESSAGGIO — "
        "che e' di `rcp.c` — tiene anche se quello di §5.5 fosse spento"),
    "cursore-prima-di-sessione": (
        False, 0, 0, 0, 0, 0,
        "§5: il cursore vive sul canale di controllo, e prima di `SESSIONE` non "
        "c'e' nessuno che lo disegni.  ⚠ Non e' l'errore di nessuno: la cattura "
        "comincia prima che il client si attacchi"),
}


def conta():
    """⛔ I due numeri, CALCOLATI dalle previsioni.  Nessun commento li riscrive
    a mano: e' il rilievo R7.14 — tre numeri scritti a mano, e nessuno dei tre
    tornava con il file."""
    return len(VIOLAZIONI), len(VERDI), len(CURSORI)


def riga(ok, nome, testo):
    c = VERDE if ok else ROSSO
    print(f"  {c}{'✅' if ok else '⛔'}{GRIGIO} {nome:44s} {testo}")


# ⛔ Il verdetto CASO PER CASO, per chi certifica il banco (`04-b23-guasti.py`).
#    ⚠ Si riempie qui dentro e non si ricalcola altrove: una seconda funzione che
#      rifacesse il giudizio potrebbe darne uno diverso, e allora la
#      certificazione certificherebbe se stessa.
ESITI = {}


def giudica(traccia, filtro=""):
    ESITI.clear()
    per_nome = {}
    doppi = []
    for d in traccia:
        if d["caso"] in per_nome:
            doppi.append(d["caso"])
        per_nome[d["caso"]] = d

    guasti = 0

    # ⛔⭐ PRIMA DI TUTTO: I CASI DICHIARATI CI SONO TUTTI?
    #
    #    Un caso tolto dal cliente in C sparirebbe dalla traccia, e un giudice
    #    che scorresse la traccia direbbe «tutto verde» su una prova non fatta.
    #    ⚠ E' la forma R7.15 — «zero casi non e' tutti passati» — spostata sul
    #      confine fra i due programmi, dove non la guarda nessuno dei due.
    attesi = set(VIOLAZIONI) | set(VERDI) | set(CURSORI)
    visti = set(per_nome)
    mancanti = sorted(attesi - visti)
    intrusi = sorted(visti - attesi)
    if mancanti:
        print(f"\n{ROSSO}⛔ {len(mancanti)} casi DICHIARATI e mai misurati: "
              f"{', '.join(mancanti)}{GRIGIO}")
        print("   Questo NON e' un verde: sono prove non fatte, non prove "
              "fallite.")
        guasti += len(mancanti)
    if intrusi:
        print(f"\n{GIALLO}⚠ {len(intrusi)} casi nella traccia e non fra le "
              f"previsioni: {', '.join(intrusi)}{GRIGIO}")
        print("   Il cliente misura qualcosa che nessuno ha previsto: o si "
              "prevede, o si toglie.")
        guasti += len(intrusi)
    if doppi:
        print(f"\n{ROSSO}⛔ casi ripetuti nella traccia: {', '.join(doppi)}"
              f"{GRIGIO}")
        guasti += len(doppi)

    # ⛔ OGNI CONTEGGIO CON IL SUO DENOMINATORE, e i denominatori sono diversi
    #    perche' le proprieta' misurate sono diverse.
    conti = {
        "violazioni accusate SUL BYTE DICHIARATO": [0, 0],
        "violazioni col motivo giusto in CONGEDO (§11)": [0, 0],
        "§3.1 punto 3 — motivo nella chiusura della sessione": [0, 0],
        "⭐ verdi attesi, sessione VIVA": [0, 0],
        "⭐ verdi attesi, iniettato ESATTAMENTE quel che si doveva": [0, 0],
        "⭐ §6.2 — il campo `input` del fotogramma": [0, 0],
        "⛔ dopo ciascuno, una connessione NUOVA fino a ECCOMI": [0, 0],
        "§7.3 — rilascio al distacco, UNA volta per sessione": [0, 0],
        "⭐ §7.2 — CURSORE_FORMA: la lunghezza che il server non sbaglia": [0, 0],
    }

    print("\n== ⛔ LE VIOLAZIONI — ciascuna sul byte dichiarato PRIMA")
    for nome in VIOLAZIONI:
        if filtro and filtro not in nome:
            continue
        d = per_nome.get(nome)
        if d is None:
            continue
        atteso_byte, perche = VIOLAZIONI[nome]

        conti["violazioni accusate SUL BYTE DICHIARATO"][1] += 1
        ok_byte = d["accusato_al_byte"] == atteso_byte
        conti["violazioni accusate SUL BYTE DICHIARATO"][0] += int(ok_byte)

        conti["violazioni col motivo giusto in CONGEDO (§11)"][1] += 1
        ok_mot = d["congedo"] and d["motivo"] == ERRORE_PROTOCOLLO
        conti["violazioni col motivo giusto in CONGEDO (§11)"][0] += int(ok_mot)

        conti["§3.1 punto 3 — motivo nella chiusura della sessione"][1] += 1
        ok_wt = d["codice_chiusura"] == ERRORE_PROTOCOLLO
        conti["§3.1 punto 3 — motivo nella chiusura della sessione"][0] += int(ok_wt)

        ok = ok_byte and ok_mot and ok_wt and d["finita"]
        visto = ("MAI ACCUSATA" if d["accusato_al_byte"] < 0
                 else f"byte {d['accusato_al_byte']}")
        testo = (f"{visto} (atteso {atteso_byte})  motivo="
                 f"{'-' if d['motivo'] is None else hex(d['motivo'])} in "
                 f"{'CONGEDO' if d['congedo'] else '(nessun messaggio)'}  "
                 f"chiusura="
                 f"{'-' if d['codice_chiusura'] is None else hex(d['codice_chiusura'])}")
        ESITI[nome] = bool(ok)
        riga(ok, nome, testo)
        if not ok:
            guasti += 1
            print(f"        {perche}")
            if not d["finita"]:
                print(f"        {ROSSO}⛔ e la sessione e' rimasta VIVA: la "
                      f"violazione non e' stata accusata affatto{GRIGIO}")
        if d["dettaglio"]:
            # §3.1 punto 1: si scrive CHE COSA non si e' capito.  ⚠ Qui non si
            # giudica il testo — sarebbe giudicare la stessa mano che l'ha
            # scritto — ma si STAMPA, perche' chi legge il banco possa vedere
            # se la diagnosi manderebbe a cercare nel posto giusto.
            print(f"        dal corpo del CONGEDO: «{d['dettaglio']}»")

    print("\n== ⭐ I CASI CHE DEVONO PASSARE — e non basta che la sessione regga")
    for nome in VERDI:
        if filtro and filtro not in nome:
            continue
        d = per_nome.get(nome)
        if d is None:
            continue
        inj_attese, ult_atteso, campo_atteso, perche = VERDI[nome]

        chiude = CHIUDE_APPOSTA.get(nome)
        conti["⭐ verdi attesi, sessione VIVA"][1] += 1
        if chiude is None:
            ok_viva = (not d["finita"] and d["motivo"] is None
                       and d["codice_chiusura"] is None)
        else:
            # ⛔ Chiude apposta, e col motivo dichiarato — non con
            #    ERRORE_PROTOCOLLO.
            ok_viva = d["motivo"] == chiude and d["codice_chiusura"] == chiude
        conti["⭐ verdi attesi, sessione VIVA"][0] += int(ok_viva)

        viste = [(i["quale"], i["a"], i["b"]) for i in d["iniezioni"]]
        conti["⭐ verdi attesi, iniettato ESATTAMENTE quel che si doveva"][1] += 1
        ok_inj = viste == [tuple(x) for x in inj_attese]
        conti["⭐ verdi attesi, iniettato ESATTAMENTE quel che si doveva"][0] += int(ok_inj)

        ok_ult = d["ultimo_iniettato"] == ult_atteso

        ok_campo = True
        if campo_atteso is not None:
            conti["⭐ §6.2 — il campo `input` del fotogramma"][1] += 1
            testa = d["testa_video"]
            # §6.2: 28 byte, e il campo `input` e' un u32 all'offset 24.
            if not testa or len(testa) != 56:
                ok_campo = False
                letto = "(nessun fotogramma)"
            else:
                letto_n = int(testa[48:56], 16)
                ok_campo = letto_n == campo_atteso
                letto = str(letto_n)
            conti["⭐ §6.2 — il campo `input` del fotogramma"][0] += int(ok_campo)
        else:
            letto = "-"

        ok = ok_viva and ok_inj and ok_ult and ok_campo
        testo = (f"{'la sessione regge' if ok_viva else '⛔ CADUTA'}  "
                 f"iniettato={viste}  ultimo_iniettato={d['ultimo_iniettato']} "
                 f"(atteso {ult_atteso})")
        if campo_atteso is not None:
            testo += f"  campo input={letto} (atteso {campo_atteso})"
        ESITI[nome] = bool(ok)
        riga(ok, nome, testo)
        if not ok:
            guasti += 1
            print(f"        atteso: iniettato {inj_attese}")
            print(f"        {perche}")
            if d["motivo"] is not None and chiude is None:
                print(f"        {ROSSO}⛔ e' arrivato un CONGEDO con motivo "
                      f"{hex(d['motivo'])}: «{d['dettaglio']}»{GRIGIO}")

    print("\n== ⭐ §7.2 — `CURSORE_FORMA`: nel dubbio NON si manda")
    for nome in CURSORI:
        if filtro and filtro not in nome:
            continue
        d = per_nome.get(nome)
        if d is None:
            continue
        spedito, lung, l, a, ax, ay, perche = CURSORI[nome]
        conti["⭐ §7.2 — CURSORE_FORMA: la lunghezza che il server non sbaglia"][1] += 1

        if spedito:
            # ⛔ Si giudica sui BYTE USCITI, non sul valore di ritorno: quello e'
            #    il registro di chi manda (`CODER.md` §3.8).  E il conto di §7.2
            #    lo rifa' il cliente sui campi ARRIVATI.
            ok = (d["cursori_sul_filo"] == 1
                  and d["cursore_lunghezza"] == lung
                  and d["cursore_lunghezza_torna"]
                  and d["cursore_immagine_intatta"]
                  and (d["cursore_l"], d["cursore_a"]) == (l, a)
                  and (d["cursore_ax"], d["cursore_ay"]) == (ax, ay))
            testo = (f"{d['cursori_sul_filo']} sul filo, lunghezza "
                     f"{d['cursore_lunghezza']} (attesa {lung}), "
                     f"{d['cursore_l']}x{d['cursore_a']} attivo="
                     f"({d['cursore_ax']},{d['cursore_ay']}), "
                     f"8+lxax4 {'torna' if d['cursore_lunghezza_torna'] else '⛔ NON torna'}, "
                     f"immagine {'intatta' if d['cursore_immagine_intatta'] else '⛔ ALTERATA'}")
        else:
            # ⛔ «Non spedito» vuol dire ZERO byte di quel tipo sul filo — non
            #    «la funzione ha detto -1»: un server che rispondesse -1 e
            #    spedisse lo stesso passerebbe il controllo sbagliato.
            ok = d["cursori_sul_filo"] == 0 and d["cursore_esito"] == -1
            testo = (f"{d['cursori_sul_filo']} byte di CURSORE_FORMA sul filo "
                     f"(attesi 0), la funzione ha risposto {d['cursore_esito']}")
        # ⚠ E in nessuno di questi casi la sessione deve cadere: rifiutare di
        #   mandare un cursore non e' un motivo per congedare nessuno.
        ok = ok and not d["finita"]
        conti["⭐ §7.2 — CURSORE_FORMA: la lunghezza che il server non sbaglia"][0] += int(ok)
        ESITI[nome] = bool(ok)
        riga(ok, nome, testo)
        if not ok:
            guasti += 1
            print(f"        {perche}")
            if d["finita"]:
                print(f"        {ROSSO}⛔ e la sessione e' CADUTA: un cursore "
                      f"rifiutato non e' un motivo per congedare{GRIGIO}")

    # ── ⛔ E il server dopo?  Su TUTTI i casi, non solo sulle violazioni ────
    print("\n== ⛔ DOPO CIASCUNO, UNA CONNESSIONE NUOVA FINO A `ECCOMI`")
    caduti = []
    for nome, d in per_nome.items():
        if filtro and filtro not in nome:
            continue
        if nome not in attesi:
            continue
        conti["⛔ dopo ciascuno, una connessione NUOVA fino a ECCOMI"][1] += 1
        if d["ripresa_fino_a_eccomi"]:
            conti["⛔ dopo ciascuno, una connessione NUOVA fino a ECCOMI"][0] += 1
        else:
            caduti.append(nome)
    if caduti:
        guasti += len(caduti)
        riga(False, "ripresa", f"⛔ dopo {len(caduti)} casi una connessione "
                               f"nuova NON arriva a ECCOMI: {', '.join(caduti)}")
    else:
        riga(True, "ripresa",
             f"{conti['⛔ dopo ciascuno, una connessione NUOVA fino a ECCOMI'][1]} "
             f"connessioni nuove, tutte fino a `ECCOMI` — ⭐ e si guarda che i "
             f"byte dell'`ECCOMI` siano usciti, non che nessuno abbia protestato")

    # ── §7.3: il rilascio al distacco ──────────────────────────────────────
    print("\n== ⭐ §7.3 — IL RILASCIO AL DISTACCO, e UNA VOLTA SOLA")
    sbagliati = []
    for nome, d in per_nome.items():
        if filtro and filtro not in nome:
            continue
        if nome not in attesi or not d["ganci"]:
            continue
        conti["§7.3 — rilascio al distacco, UNA volta per sessione"][1] += 1
        if d["rilasci_dopo"] == RILASCIO_ATTESO:
            conti["§7.3 — rilascio al distacco, UNA volta per sessione"][0] += 1
        else:
            sbagliati.append(f"{nome}={d['rilasci_dopo']}")
    if sbagliati:
        guasti += len(sbagliati)
        riga(False, "rilascio", f"⛔ chiamate diverse da {RILASCIO_ATTESO}: "
                                f"{', '.join(sbagliati[:6])}")
    else:
        n = conti["§7.3 — rilascio al distacco, UNA volta per sessione"][1]
        riga(True, "rilascio", f"{n} sessioni con i ganci collegati, e in "
                               f"ciascuna il rilascio e' stato chiesto "
                               f"ESATTAMENTE una volta — ⚠ zero sarebbe un Ctrl "
                               f"rimasto giu', due sarebbero due verita' sullo "
                               f"stesso fatto")

    # ── il verdetto ────────────────────────────────────────────────────────
    print("\n== I NUMERI, ciascuno col suo denominatore")
    for k, (a, b) in conti.items():
        c = VERDE if (b and a == b) else (ROSSO if b else GIALLO)
        print(f"   {c}{a:3d} / {b:<3d}{GRIGIO}  {k}")
    return guasti


def principale(a):
    tot_v, tot_verdi, tot_cur = conta()
    if a.elenco:
        print(f"== B23: {tot_v + tot_verdi + tot_cur} casi — {tot_v} violazioni, "
              f"{tot_verdi} ⭐ verdi attesi e {tot_cur} §7.2 sul cursore.  "
              f"Ogni riga e' una PREVISIONE\n")
        print("  ⛔ LE VIOLAZIONI — nome, byte su cui deve essere accusata")
        for nome, (b, perche) in VIOLAZIONI.items():
            print(f"    {nome:44s} byte {b:>3}   ERRORE_PROTOCOLLO (0x0b)")
            print(f"    {'':44s}   {perche}")
        print("\n  ⭐ I CASI CHE DEVONO PASSARE")
        for nome, (inj, ult, campo, perche) in VERDI.items():
            print(f"    {nome:44s} iniezioni {inj}")
            print(f"    {'':44s}   {perche}")
        print("\n  ⭐ §7.2 — CURSORE_FORMA")
        for nome, (sp, lung, l, a_, ax, ay, perche) in CURSORI.items():
            print(f"    {nome:44s} "
                  + (f"spedito, lunghezza {lung}" if sp else "⛔ NON spedito"))
            print(f"    {'':44s}   {perche}")
        return 0

    percorso = a.traccia
    if not percorso:
        # ⛔ Si compila e si gira: cosi' la traccia e' di QUESTO sorgente, e non
        #    di un file rimasto da un giro precedente.  ⚠ Una traccia vecchia
        #    letta per nuova e' la forma R7.15 travestita.
        eseguibile = os.path.join(a.uscita, "04-b23-filo-input")
        os.makedirs(a.uscita, exist_ok=True)
        cc = subprocess.run(
            ["cc", "-std=gnu11", "-D_GNU_SOURCE", "-O1", "-g", "-Wall",
             "-Wextra", "-Wno-unused-parameter", "-o", eseguibile,
             os.path.join(QUI, "04-b23-filo-input.c")],
            capture_output=True, text=True, cwd=QUI)
        if cc.returncode != 0:
            print(f"{ROSSO}⛔ il cliente non compila{GRIGIO}\n{cc.stderr}")
            return 2
        girato = subprocess.run([eseguibile], capture_output=True, text=True,
                                cwd=QUI)
        if girato.returncode != 0:
            print(f"{ROSSO}⛔ il cliente e' uscito con "
                  f"{girato.returncode}{GRIGIO}\n{girato.stderr[:2000]}")
            return 2
        percorso = os.path.join(a.uscita, "04-b23-traccia.jsonl")
        with open(percorso, "w") as f:
            f.write(girato.stdout)

    with open(percorso) as f:
        traccia = [json.loads(r) for r in f if r.strip()]

    # ⛔ ZERO RIGHE NON E' «TUTTO PASSATO» — rilievo R7.15.
    if not traccia:
        print(f"{ROSSO}⛔ la traccia e' VUOTA: non c'e' niente da misurare, e "
              f"questo NON e' un verde{GRIGIO}")
        return 2

    print("== B23 — il canale di input di `RCP.md` §7.3, provato violandolo")
    print(f"   ⛔ BERSAGLIO: `banchi/rcp/rcp.c` compilato in processo — lo "
          f"stesso sorgente di `src/rcp.c`,")
    print(f"      confrontato byte per byte dal `Makefile` (GEMELLATI).")
    print(f"   ⚠ NON gira sul filo: `src/webtransport.c` oggi i byte del canale "
          f"di input li SCARTA")
    print(f"     (`G_UNI_OK`), e quel file non e' di questo anello.  La cucitura "
          f"e' chiesta nel rapporto.")
    print(f"   la traccia di questo giro: {percorso}")
    print(f"   {tot_v} violazioni, {tot_verdi} ⭐ verdi attesi e {tot_cur} §7.2 "
          f"sul cursore — {tot_v + tot_verdi + tot_cur} casi in tutto")
    print(f"   ⛔ i byte si consegnano UNO ALLA VOLTA: «su quale byte» e' una "
          f"misura, non un modo di dire")

    guasti = giudica(traccia, a.solo)
    if a.json_esiti:
        # ⛔ Il verdetto caso per caso, per chi certifica il banco.  Va su un
        #    FILE e non su stdout: stdout e' la relazione che legge una persona,
        #    e mescolarli renderebbe illeggibile l'una e fragile l'altro.
        with open(a.json_esiti, "w") as f:
            json.dump({"esiti": ESITI, "guasti": guasti}, f)
    if guasti:
        print(f"\n    {ROSSO}⛔ B23 NON passa: {guasti} guasti{GRIGIO}")
        return 1
    if a.solo:
        print(f"\n    {VERDE}⭐ i casi selezionati passano{GRIGIO} — ⚠ e questo "
              f"NON e' «B23 passa»: il giro era parziale")
        return 0
    print(f"\n    {VERDE}⭐ B23 passa{GRIGIO} — e i numeri qui sopra dicono su "
          f"che cosa")
    print(f"    ⚠ e non e' «l'input funziona»: qui si prova il FILO.  Che il "
          f"desktop si muova")
    print(f"      e' `04-b24-iniezione` (A4), e il metro resta l'utente (I8).")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="B23 — il giudice del canale di input")
    p.add_argument("--traccia", default="",
                   help="una traccia gia' prodotta; senza, si compila e si gira")
    p.add_argument("--uscita", default="/tmp/b23",
                   help="dove mettere l'eseguibile e la traccia")
    p.add_argument("--solo", default="",
                   help="giudica solo i casi che contengono questo")
    p.add_argument("--elenco", action="store_true",
                   help="stampa le previsioni senza misurare")
    p.add_argument("--json-esiti", dest="json_esiti", default="",
                   help="scrive il verdetto caso per caso in un file JSON "
                        "(lo usa 04-b23-guasti.py per certificare il banco)")
    sys.exit(principale(p.parse_args()))
