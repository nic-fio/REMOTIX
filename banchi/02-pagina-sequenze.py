#!/usr/bin/env python3
"""02-pagina-sequenze.py — costruisce i FLUSSI NOTI che la pagina di prova decodifica.

    python3 banchi/02-pagina-sequenze.py            costruisce tutte le sequenze
    python3 banchi/02-pagina-sequenze.py --elenca   dice solo che cosa c'e' gia'

===========================================================================
⛔ PERCHE' ESISTE, E CHE DIFETTO IMPEDISCE

F2.5 misura *«dal byte che arriva sul filo al pixel dipinto nella scheda del
browser»*.  Una misura del genere ha un imputato ovvio — il browser — e un
imputato che nessuno guarda: **il flusso che gli si da' in pasto**.  Se il
flusso e' storto, la pagina non dipinge, e il banco scrive «Firefox non
decodifica HEVC»: un `[M]` falso, contro un componente innocente.  E' la forma
d'errore **E10** al contrario — non «la prova verde sul client sbagliato», ma
la prova ROSSA con l'ingresso sbagliato.

⇒ Il flusso lo costruisce QUESTO programma, con `libx265`, e ne dichiara ogni
  proprieta' **leggendola** (`ffprobe`) invece di darla per scontata:

  ⛔ **il livello e il profilo si LEGGONO dal flusso, non si indovinano.**
     `RCP.md` §4.3, rilievo **O12**: un livello dichiarato piu' basso del vero
     non da' un errore di rete — **fa rifiutare la configurazione dal
     decodificatore**, e il sintomo e' «il browser non apre il flusso».  Qui la
     stringa di codec (`hev1.2.4.L120.B0`) viene composta con i numeri che
     `ffprobe` legge nel flusso appena prodotto.  ⚠ Ed e' anche il guasto che
     `02-pagina-certifica.sh` innesta apposta, per vedere che aspetto ha.

===========================================================================
⛔ LE DUE FORME, E NON SONO INTERCAMBIABILI — la cucitura con F2.3

`web.md` §4.2 dice che la strada e' **Annex-B senza `description`**: e' legale,
e' quel che `hevc_vaapi` gia' produce, e in Chromium risparmia un'allocazione e
una copia per fotogramma `[R]`.  E avverte che la strada dell'`hvcC` ha una
trappola: Chromium riparsa l'SPS e **rifiuta la configurazione** se i byte di
prevenzione dell'emulazione cadono nel campo sbagliato `[R]`.

⛔ Ma «Annex-B e' meglio» non e' «hvcC non serve»: la scelta la fa **F2.3**, e
   questo banco deve saper misurare **tutt'e due**, o il giorno in cui F2.3
   consegnasse un `hvcC` il banco non saprebbe dire se il difetto e' del
   flusso o della pagina.  Quindi ogni pattern esce in DUE sequenze:

   `-annexb`  NALU separate da start code `00 00 00 01`, **senza** description
   `-hvcc`    NALU con prefisso di lunghezza a 4 byte, **con** la description
              `hvcC` costruita qui dai VPS/SPS/PPS

   ⛔ E la coppia e' anche una prova: dare un flusso Annex-B a un
      decodificatore configurato con la `description` (o viceversa) e' lo
      scambio che a valle si scoprirebbe come «immagine verde» o «niente».
      `02-pagina-prova.html` ha una prova apposta che fa proprio lo scambio.

===========================================================================
⛔ I PIXEL SONO NOTI PRIMA, E SONO OTTO — perche' il banco possa DISTINGUERE

Il motivo di `LEZIONI.md` §1.11: *per ogni prova indiretta si scrive che
aspetto avrebbe il caso opposto, o la prova non distingue*.

Il pattern e' una griglia 4x2 di otto tinte piatte **molto distanti fra loro**
(oltre 100 di distanza in RGB).  Cosi' la classificazione «quale delle otto
tinte e' questa cella» **non dipende dalla resa del colore**: la conversione
YUV->RGB del browser, la gamma, il flag di intervallo (limitato o pieno) e la
perdita di x265 spostano un canale di qualche decina — non di cento.

⛔ E ci sono DUE pattern, non uno: `A` e `B` hanno le stesse otto tinte in
   ordine diverso.  Un banco che dipinge sempre lo stesso grigio, o che
   riusa il fotogramma precedente, o che «vede quel che si aspetta», da' la
   STESSA risposta sui due — e allora non sta misurando niente.  Questa e' la
   prova P4 della pagina, ed e' quella che dice **no**.

⚠ La striscia di sfumatura in fondo NON serve al banco: serve all'occhio
  dell'utente (`LEZIONI.md` §2.4 — il metro e' quel che si vede), perche' i
  10 bit dal browser **non sono leggibili** (`web.md` §1.2 A) e la prova
  finale su quelli e' guardare una sfumatura.  Qui c'e' perche' sia gia' nel
  fotogramma quando la fase 2 arrivera' a farla guardare.

===========================================================================
⛔ ZERO E FALLIMENTO — `LEZIONI.md` §1.9

Nessun `2>/dev/null`, nessuno stato d'uscita buttato.  Se `ffmpeg` non c'e', o
non ha `libx265`, o non sa fare i 10 bit, questo programma **si ferma dicendo
quale delle tre**, invece di produrre meno sequenze e lasciare che la pagina
scriva «HEVC non supportato».
"""
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
DOVE = QUI / "02-pagina-sequenze"

LARGHEZZA = 640
ALTEZZA = 480
QUANTI = 6            # fotogrammi per sequenza: la fase 2 ne vuole UNO, gli
                      # altri cinque servono a distinguere «ha decodificato»
                      # da «ha decodificato il primo e si e' fermato».
RITMO = 30

# ⛔ Le otto tinte, in ordine di cella (4 colonne x 2 righe).  Sono il DATO del
#    banco: la pagina le riceve nel JSON e ci classifica sopra i pixel letti.
#    ⚠ Scelte lontane da 0 e da 255: un canale in saturazione non distingue piu'
#      «il colore giusto» da «il colore un po' sbagliato ma tagliato uguale».
TINTE = [
    ("rosso",   (220,  32,  32)),
    ("verde",   ( 32, 200,  64)),
    ("blu",     ( 48,  64, 220)),
    ("giallo",  (224, 208,  48)),
    ("ciano",   ( 48, 208, 216)),
    ("magenta", (208,  56, 200)),
    ("chiaro",  (200, 200, 200)),
    ("scuro",   ( 40,  40,  40)),
]

# Il pattern B: le stesse tinte, ruotate di tre celle.  ⛔ Ruotate e non
# rimescolate a caso: un ordine riproducibile e' un ordine che si puo' rifare
# fra sei mesi e confrontare con oggi.
PATTERN = {
    "A": list(range(8)),
    "B": [(i + 3) % 8 for i in range(8)],
}

COLONNE, RIGHE = 4, 2
ALTEZZA_SFUMATURA = 64      # la striscia in fondo, per l'occhio


def errore(testo, dettaglio=None):
    print(f"\n\033[1;31mNO\033[0m  {testo}", file=sys.stderr)
    if dettaglio:
        for r in str(dettaglio).splitlines():
            print(f"        {r}", file=sys.stderr)
    sys.exit(2)


def esegui(comando, entrata=None):
    """⛔ Nessun `2>/dev/null` e nessuno stato d'uscita buttato: chi chiama
       riceve stdout, stderr E il codice, e decide lui."""
    p = subprocess.run(comando, input=entrata, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    return p.returncode, p.stdout, p.stderr


def disegna(ordine):
    """Il fotogramma, in RGB24 crudo.  Ritorna (byte, celle) dove `celle` dice
       dove sta ciascuna cella — la pagina legge i pixel proprio li'."""
    dati = bytearray(LARGHEZZA * ALTEZZA * 3)
    utile = ALTEZZA - ALTEZZA_SFUMATURA
    larghezza_cella = LARGHEZZA // COLONNE
    altezza_cella = utile // RIGHE
    celle = []
    for indice, tinta in enumerate(ordine):
        nome, (r, g, b) = TINTE[tinta]
        cx = (indice % COLONNE) * larghezza_cella
        cy = (indice // COLONNE) * altezza_cella
        for y in range(cy, cy + altezza_cella):
            base = (y * LARGHEZZA + cx) * 3
            for x in range(larghezza_cella):
                dati[base + x * 3] = r
                dati[base + x * 3 + 1] = g
                dati[base + x * 3 + 2] = b
        celle.append({
            "indice": indice, "tinta": nome, "rgb": [r, g, b],
            "x": cx, "y": cy, "l": larghezza_cella, "a": altezza_cella,
        })
    # ⚠ La sfumatura: 640 passi su 640 colonne.  A 8 bit ne sopravvivono 256,
    #   e le strisce si vedono; a 10 bit no.  Non e' misurabile da JavaScript
    #   (`web.md` §1.2 A): e' li' per l'occhio.
    for y in range(utile, ALTEZZA):
        base = y * LARGHEZZA * 3
        for x in range(LARGHEZZA):
            v = 16 + (x * 219) // (LARGHEZZA - 1)
            dati[base + x * 3] = v
            dati[base + x * 3 + 1] = v
            dati[base + x * 3 + 2] = v
    return bytes(dati), celle


def disegna10(ordine):
    """Lo stesso pattern, ma con **10 bit veri** — in RGB a 16 bit per canale.

    ⛔⭐ ESISTE PER UNA CUCITURA ARRIVATA DA F2.2, E CORREGGE UN DIFETTO DI
        QUESTO STESSO BANCO.

    F2.2 ha misurato che **la sorgente da' OTTO bit**: Mutter consegna solo
    BGRx/BGRA, 8 bit per canale, contati sulla scena `[M]`.  ⇒ In fase 2 il
    flusso che arriva alla pagina e' **Main10 con dentro 8 bit promossi**.

    ⛔ E la stessa cosa valeva per le sequenze di questo banco senza che me ne
       fossi accorto: `disegna()` produce **RGB24**, cioe' 8 bit per canale, e
       le sequenze `*-10bit-*` sono **Main10 con contenuto a 8 bit promosso**.
       ⚠ Da cui il difetto: il confronto *«il flusso Main10 e quello Main
       dipingono pixel identici»* **non dimostrava** che il browser riporti
       l'uscita a 8 bit — dimostrava che **la nostra sorgente era gia' a 8**.
       Due cause diverse con lo stesso aspetto, cioe' la forma **E1** applicata
       a me: avevo preso una condizione necessaria (i pixel coincidono) per la
       prova di una tesi che non reggeva.

    ⇒ Qui la sfumatura ha **877 livelli possibili** (da 64 a 940, l'intervallo
      video a 10 bit), che a 8 bit **non sono rappresentabili**.  E la firma
      che li distingue e' quella che usa F2.3: un contenuto a 8 bit promosso ha
      tutti i campioni **multipli di 4** (il valore a 8 bit spostato di due
      bit), uno a 10 bit veri no.

    ⚠ E va detto forte quel che questa sequenza **non** e': non e' il flusso
      che la catena vera produrra' in fase 2.  E' un **caso di banco**, fatto
      apposta per porre al browser una domanda che la catena vera non puo'
      porre — perche' a 8 bit ci arriva da sola.
    """
    utile = ALTEZZA - ALTEZZA_SFUMATURA
    larghezza_cella = LARGHEZZA // COLONNE
    altezza_cella = utile // RIGHE
    dati = bytearray(LARGHEZZA * ALTEZZA * 6)   # 3 canali x 2 byte
    celle = []

    def metti(base, r16, g16, b16):
        dati[base] = r16 & 0xFF;      dati[base + 1] = (r16 >> 8) & 0xFF
        dati[base + 2] = g16 & 0xFF;  dati[base + 3] = (g16 >> 8) & 0xFF
        dati[base + 4] = b16 & 0xFF;  dati[base + 5] = (b16 >> 8) & 0xFF

    for indice, tinta in enumerate(ordine):
        nome, (r, g, b) = TINTE[tinta]
        cx = (indice % COLONNE) * larghezza_cella
        cy = (indice // COLONNE) * altezza_cella
        # Le tinte restano le stesse a 8 bit (il banco ci classifica sopra):
        # si portano a 16 bit replicando il byte, che e' la scala esatta.
        r16, g16, b16 = r * 257, g * 257, b * 257
        for y in range(cy, cy + altezza_cella):
            base = (y * LARGHEZZA + cx) * 6
            for x in range(larghezza_cella):
                metti(base + x * 6, r16, g16, b16)
        celle.append({
            "indice": indice, "tinta": nome, "rgb": [r, g, b],
            "x": cx, "y": cy, "l": larghezza_cella, "a": altezza_cella,
        })

    # ⛔ LA SFUMATURA A 10 BIT VERI: 640 colonne, 877 livelli possibili.
    #    Il valore a 10 bit si porta a 16 spostandolo di 6 — ⚠ e NON si
    #    replicano i bit alti in coda, o si reintrodurrebbe una struttura
    #    periodica proprio nella statistica che deve distinguere.
    for y in range(utile, ALTEZZA):
        base = y * LARGHEZZA * 6
        for x in range(LARGHEZZA):
            v10 = 64 + (x * 876) // (LARGHEZZA - 1)
            v16 = v10 << 6
            metti(base + x * 6, v16, v16, v16)
    return bytes(dati), celle


def conta_livelli_sorgente(grezzo, sorgente10, da_riga):
    """La stessa statistica, ma sulla SORGENTE, prima di x265.

    ⛔⭐ ESISTE PERCHE' LA MISURA SUL FLUSSO DECODIFICATO NON BASTA, E L'HO
        SCOPERTO MISURANDO — `[M]` 12 agosto 2026.

    La firma dei «multipli di 4» distingue benissimo un contenuto a 8 bit
    promosso da uno a 10 bit veri... **finche' non ci passa sopra una codifica
    con perdita**.  A CRF 16 la frazione di multipli di 4 misurata sul flusso
    ridecodificato e' **0,2488 per la sorgente a 8 bit** e **0,2524 per quella
    a 10 bit veri**: due numeri indistinguibili, perche' il rumore di
    quantizzazione ha riempito gli spazi fra i multipli di 4.

    ⇒ Sul flusso lossy la firma **non c'e' piu'**.  Misurarla li' e concluderne
      «il contenuto e' a 10 bit veri» sarebbe stato un `[M]` falso su un dato
      che non c'e', e la sorgente e' l'unico posto dove la domanda ha una
      risposta pulita.

    ⚠ E la conseguenza va oltre il banco: vuol dire che **nessuno, a valle
      della codifica, puo' sapere se il contenuto fosse a 8 o a 10 bit** — ne'
      il browser, ne' F2.6, ne' noi.  Quel che F2.2 ha misurato alla sorgente
      resta l'unica risposta.
    """
    passo = 6 if sorgente10 else 3
    livelli = {}
    for y in range(da_riga, ALTEZZA):
        riga = y * LARGHEZZA * passo
        for x in range(LARGHEZZA):
            i = riga + x * passo
            if sorgente10:
                v = ((grezzo[i] | (grezzo[i + 1] << 8)) >> 6)
            else:
                v = grezzo[i] << 2      # 8 bit promosso a 10: sempre × 4
            livelli[v] = livelli.get(v, 0) + 1
    quanti = sum(livelli.values())
    multipli = sum(n for v, n in livelli.items() if v % 4 == 0)
    return {
        "livelli_distinti": len(livelli),
        "campioni": quanti,
        "frazione_multipli_di_4": round(multipli / quanti, 4) if quanti else None,
    }


def conta_livelli(flusso, profondita, da_riga):
    """Quanti livelli distinti ha il luma nella striscia di sfumatura, e quanti
       sono multipli di 4.

    ⛔⭐ E' LA MISURA CHE DICE SE UN FLUSSO E' A 10 BIT **VERI** O PROMOSSI, e
        si fa **sul flusso codificato**, ridecodificandolo — non sull'intenzione
        di chi l'ha scritto.  `LEZIONI.md` §1.11: una prova indiretta prova quel
        che prova, e «gliel'ho dato a 10 bit» non e' «ci sono 10 bit dentro».

    La firma, ed e' quella che usa F2.3 (numeri suoi: **877 livelli distinti e
    0,25 di multipli di 4** su 10 bit veri, contro **220 e 1,000** su 8 bit):

      | contenuto            | livelli distinti | frazione multipli di 4 |
      |----------------------|------------------|------------------------|
      | 8 bit promosso a 10  | ≤ 256            | **1,000** — ogni campione e' `v8 << 2` |
      | 10 bit veri          | fino a 877       | **≈ 0,25** |

    ⚠ Il contatore e' scritto qui, e non importato da F2.3: due letture
      indipendenti della stessa grandezza valgono piu' di una sola riusata due
      volte (`PIANO.md` §0.4).  Se i due non tornassero, quello e' il regalo.
    """
    comando = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
               "-f", "hevc", "-i", "pipe:0",
               "-pix_fmt", "yuv420p10le" if profondita == 10 else "yuv420p",
               "-frames:v", "1", "-f", "rawvideo", "pipe:1"]
    codice, uscita, errori = esegui(comando, entrata=flusso)
    if codice != 0 or not uscita:
        errore("il flusso appena prodotto non si ridecodifica: senza, la "
               "profondita' vera non e' misurabile",
               errori.decode("utf-8", "replace"))
    passo = 2 if profondita == 10 else 1
    atteso = LARGHEZZA * ALTEZZA * passo
    if len(uscita) < atteso:
        errore(f"il piano di luma e' di {len(uscita)} byte, ne servono {atteso}")
    livelli = {}
    for y in range(da_riga, ALTEZZA):
        riga = y * LARGHEZZA * passo
        for x in range(LARGHEZZA):
            i = riga + x * passo
            v = uscita[i] if passo == 1 else (uscita[i] | (uscita[i + 1] << 8))
            livelli[v] = livelli.get(v, 0) + 1
    quanti = sum(livelli.values())
    multipli = sum(n for v, n in livelli.items() if v % 4 == 0)
    return {
        "livelli_distinti": len(livelli),
        "campioni": quanti,
        "frazione_multipli_di_4": round(multipli / quanti, 4) if quanti else None,
        "minimo": min(livelli) if livelli else None,
        "massimo": max(livelli) if livelli else None,
    }


def codifica(grezzo, profondita, sorgente10=False, lossless=False):
    """UNA chiave in testa, cinque delta dietro, nessun fotogramma B.

    ⛔⭐ E LA PRIMA STESURA CHIEDEVA `keyint=1`, CHE ERA SBAGLIATO — `[M]` 12
        agosto 2026.  Tutto-intra sembrava la scelta piu' fedele alla fase 2
        («un'immagine ferma»), ma x265 in tutto-intra emette il profilo
        **`Main 10 Intra`**, che nel flusso e' `profile_idc = 4` (**Rext**) e
        non 2: la stringa di codec sarebbe uscita `hev1.4.…` — cioe' una
        domanda al browser su un profilo che ne' `SPECIFICHE.md` ne' `RCP.md`
        nominano, e un `[M]` che non avrebbe risposto alla domanda posta.
        ⚠ Con `keyint=6` lo stesso ingresso esce **Main 10**, `profile_idc = 2`.

    ⭐ E la forma nuova e' anche piu' vicina al prodotto: `RCP.md` §6.2 ha due
       tipi di fotogramma, `0x0301` chiave e `0x0302` delta, e la pagina deve
       saper trattare tutt'e due.  Il primo pezzo resta la chiave da sola —
       che e' il fotogramma della fase 2 — e gli altri cinque servono a
       distinguere «ha decodificato» da «ha decodificato il primo e si e'
       fermato».

    ⛔ `bframes=0`: un fotogramma B esce dal codificatore in un ordine diverso
       da quello di presentazione, e un banco che accoppia il fotogramma
       decodificato con l'immagine attesa **per posizione** accoppierebbe
       immagini diverse.  E' anche quel che fara' il prodotto: un desktop
       remoto non ha fotogrammi B, perche' costerebbero un fotogramma di
       ritardo (`CODER.md` §1-bis)."""
    pix = "yuv420p10le" if profondita == 10 else "yuv420p"
    # ⛔⭐ IL PROFILO SI CHIEDE PER NOME, E POI SI VERIFICA CHE SIA STATO DATO.
    #    `[M]` 12 agosto 2026, primo giro: lasciato scegliere a x265, un
    #    ingresso a 10 bit 4:2:0 usciva in profilo **Rext** (`profile_idc` 4),
    #    non Main10 — e la stringa di codec sarebbe stata `hev1.4.…`, cioe' una
    #    domanda su un profilo che ne' `SPECIFICHE.md` ne' `RCP.md` nominano.
    #    E' `LEZIONI.md` §1.8: un componente che decide da se' produce due
    #    misure diverse sotto la stessa etichetta.  Si dice il nome, e sotto si
    #    controlla che abbia obbedito (`profilo_ffprobe`).
    profilo = "main10" if profondita == 10 else "main"
    # ⛔ `lossless=1` NON e' un lusso: senza, la firma dei «multipli di 4»
    #    che distingue 8 bit promossi da 10 bit veri viene cancellata dal
    #    rumore di quantizzazione (vedi `conta_livelli_sorgente()`), e il
    #    flusso arriva al browser senza portare piu' la domanda che deve porre.
    qualita = "lossless=1" if lossless else "crf=16"
    parametri = (f"keyint={QUANTI}:min-keyint={QUANTI}:scenecut=0"
                 ":repeat-headers=1:no-open-gop=1:bframes=0"
                 f":log-level=error:{qualita}")
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        # ⛔ La sorgente a 16 bit per canale serve per i 10 bit VERI: entrando
        #    in `rgb24` la sfumatura sarebbe gia' a 8 bit prima di toccare
        #    x265, e il flusso uscirebbe Main10 con dentro 8 bit **promossi** —
        #    che e' precisamente quel che F2.2 ha misurato sulla catena vera.
        "-f", "rawvideo", "-pix_fmt", "rgb48le" if sorgente10 else "rgb24",
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-framerate", str(RITMO),
        "-i", "pipe:0",
        "-c:v", "libx265", "-pix_fmt", pix, "-profile:v", profilo,
        "-x265-params", parametri,
        # ⚠ BT.709, e dichiarato nel flusso: `web.md` O3 — l'HDR non si
        #   promette, si codifica BT.709, ed e' una scelta del SERVER.  Qui il
        #   server e' questo script.
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-f", "hevc", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=grezzo)
    if codice != 0 or not uscita:
        errore(f"libx265 non ha prodotto il flusso a {profondita} bit "
               f"(uscita {codice}, {len(uscita)} byte)", errori.decode("utf-8", "replace"))
    return uscita


def sonda(flusso):
    """⛔ Profilo e livello si LEGGONO, non si scrivono a memoria (`RCP.md`
       §4.3, rilievo O12).  E se `ffprobe` non risponde, ci si ferma: una
       stringa di codec indovinata e' esattamente il difetto che si vuole
       evitare."""
    comando = ["ffprobe", "-hide_banner", "-v", "error", "-of", "json",
               "-show_streams", "-select_streams", "v:0",
               "-f", "hevc", "pipe:0"]
    codice, uscita, errori = esegui(comando, entrata=flusso)
    if codice != 0:
        errore("ffprobe non ha saputo leggere il flusso appena prodotto",
               errori.decode("utf-8", "replace"))
    try:
        d = json.loads(uscita)["streams"][0]
    except Exception as e:
        errore(f"ffprobe ha risposto qualcosa che non e' uno stream: {e}", uscita[:400])
    return d


def spezza_nalu(annexb):
    """Annex-B -> elenco di NALU (senza start code).  ⛔ Si accettano start
       code di 3 e di 4 byte: x265 usa il primo dentro l'unita' d'accesso e il
       secondo davanti a VPS/SPS/PPS, e un lettore che ne conosce uno solo
       taglia le NALU nel posto sbagliato."""
    nalu = []
    i, n = 0, len(annexb)
    inizio = None
    while i < n - 2:
        if annexb[i] == 0 and annexb[i + 1] == 0 and annexb[i + 2] == 1:
            if inizio is not None:
                fine = i
                # toglie lo zero di un eventuale start code a 4 byte
                if fine > inizio and annexb[fine - 1] == 0:
                    fine -= 1
                nalu.append(annexb[inizio:fine])
            inizio = i + 3
            i += 3
            continue
        i += 1
    if inizio is not None:
        nalu.append(annexb[inizio:])
    return nalu


def tipo_nalu(u):
    return (u[0] >> 1) & 0x3F


def sguscia(u):
    """Toglie i byte di prevenzione dell'emulazione (`00 00 03` -> `00 00`).

    ⛔⭐ QUESTA FUNZIONE E' NATA DA UN DIFETTO MISURATO, il 12 agosto 2026, al
        primo giro di questo stesso programma.  Senza di lei la stringa di
        codec usciva **`hev1.4.C0000010.L0.00.9D…`**: profilo 4, livello 0.
        L'SPS che x265 produce contiene `00 00 03 00` proprio dentro i flag di
        compatibilita' e dentro i flag di vincolo, e leggere quei byte cosi'
        come stanno sposta di uno tutto quel che viene dopo — **compreso il
        livello**, che finiva a 0.

    ⚠ E il livello a 0 non da' un errore di rete: `RCP.md` §4.3 rilievo O12 —
      **fa rifiutare la configurazione dal decodificatore**, e il sintomo
      sarebbe stato «Chrome non apre il flusso», cioe' un `[M]` falso contro
      il browser.  ⭐ E' letteralmente la trappola che `web.md` §4.2 attribuisce
      all'`hvcC` — *«Chromium riparsa l'SPS e rifiuta la configurazione se i
      byte di prevenzione dell'emulazione cadono nel campo sbagliato»* — solo
      che qui a caderci era **il nostro lettore**, non il loro.

    ⛔ Da cui la regola per F2.3: i byte di parametro NON si leggono come byte.
    """
    fuori = bytearray()
    zeri = 0
    for b in u:
        if zeri >= 2 and b == 3:
            zeri = 0
            continue
        fuori.append(b)
        zeri = zeri + 1 if b == 0 else 0
    return bytes(fuori)


def unita_daccesso(nalu):
    """Raggruppa le NALU in unita' d'accesso — una unita' = un fotogramma.

    ⛔ La regola NON e' «una nuova unita' comincia col VPS»: quella vale solo
       se ogni fotogramma e' una chiave, ed e' la scorciatoia che la prima
       stesura aveva preso.  Con le chiavi ogni sei fotogrammi il VPS compare
       una volta su sei, e tutte e sei le immagini finivano in **un unico
       pezzo**: il decodificatore ne avrebbe ricevuto uno solo e il banco
       avrebbe letto «cinque fotogrammi persi» su un flusso intero.

    La regola giusta: una nuova unita' comincia quando arriva una NALU che sta
    **prima** delle fette (VPS 32, SPS 33, PPS 34, SEI di prefisso 39) oppure
    una NALU di fetta (tipo < 32) **e nell'unita' corrente una fetta c'e'
    gia'**.  E' il caso semplice — nessuna immagine spezzata in piu' fette,
    perche' x265 con queste opzioni non ne produce, e il controllo qui sotto
    verifica che le unita' siano esattamente `QUANTI`."""
    unita, corrente = [], []
    fetta_vista = False
    for u in nalu:
        t = tipo_nalu(u)
        prima_delle_fette = t in (32, 33, 34, 39)
        e_fetta = t < 32
        if fetta_vista and (prima_delle_fette or e_fetta):
            unita.append(corrente)
            corrente = []
            fetta_vista = False
        corrente.append(u)
        if e_fetta:
            fetta_vista = True
    if corrente:
        unita.append(corrente)
    return unita


def e_chiave(unita):
    """⛔ `RCP.md` §6.2 distingue `0x0301` chiave da `0x0302` delta, e
       WebCodecs pretende lo stesso in `EncodedVideoChunk.type`.  Un delta
       dichiarato chiave non da' un errore: fa decodificare un'immagine
       sbagliata, che e' peggio.  I tipi IRAP sono da 16 a 23."""
    return any(16 <= tipo_nalu(u) <= 23 for u in unita)


def leggi_ptl(sps):
    """I 12 byte del `profile_tier_level`, presi dall'SPS SGUSCIATO.

    SPS: 2 byte d'intestazione NALU, poi un byte con
    `sps_video_parameter_set_id`(4) + `sps_max_sub_layers_minus1`(3) +
    `sps_temporal_id_nesting_flag`(1); poi il `profile_tier_level`, che con
    `max_sub_layers_minus1 = 0` e' lungo esattamente 12 byte."""
    nudo = sguscia(sps)
    ptl = nudo[3:15]
    if len(ptl) < 12:
        errore("SPS troppo corto per contenere un profile_tier_level")
    return ptl


def costruisci_hvcc(parametri):
    """La `description` del formato `hvcC` (ISO/IEC 14496-15 §8.3.3.1).

    ⛔ Si costruisce dai byte VERI dell'SPS appena prodotto: i campi di
       profilo, tier e livello dell'`hvcC` sono **gli stessi 12 byte** del
       `profile_tier_level` dell'SPS, e ricopiarli da li' e' l'unico modo di
       non avere due verita' sullo stesso flusso.  ⚠ E' anche la ragione per
       cui `web.md` §4.2 sconsiglia questa strada: sono byte che qualcuno deve
       ricopiare giusti, e Chromium riparsa l'SPS e rifiuta se non tornano."""
    sps = next((u for u in parametri if tipo_nalu(u) == 33), None)
    if sps is None:
        errore("nessun SPS nel flusso: l'hvcC non si puo' costruire")

    ptl = leggi_ptl(sps)
    profilo_spazio_tier_idc = ptl[0]
    compat = ptl[1:5]
    vincoli = ptl[5:11]
    livello = ptl[11]

    # ⛔ Gli indici sono commentati uno per uno, e non e' pedanteria: la prima
    #    stesura scriveva la profondita' di bit agli indici 19 e 20 — che sono
    #    `avgFrameRate` — lasciando a 8 la profondita' di un flusso a 10 bit.
    #    `[M]` 12 agosto 2026, visto rileggendo l'esadecimale dell'hvcC
    #    prodotto.  ⚠ Un decodificatore indulgente non se ne sarebbe accorto
    #    (i bit veri stanno nell'SPS), e il banco avrebbe misurato i 10 bit
    #    con una descrizione che ne dichiara 8: due verita' sullo stesso
    #    flusso, cioe' la forma d'errore E2 dentro il banco.
    b = bytearray()
    b.append(1)                                  # [0]     configurationVersion
    b.append(profilo_spazio_tier_idc)            # [1]     spazio+tier+profile_idc
    b += compat                                  # [2..5]  profile_compatibility
    b += vincoli                                 # [6..11] constraint_indicator
    b.append(livello)                            # [12]    general_level_idc
    b += b"\xf0\x00"                             # [13,14] min_spatial_segmentation
    b.append(0xFC)                               # [15]    parallelismType
    b.append(0xFC | 1)                           # [16]    chromaFormat 4:2:0
    b.append(0xF8)                               # [17]    bitDepthLumaMinus8
    b.append(0xF8)                               # [18]    bitDepthChromaMinus8
    b += b"\x00\x00"                             # [19,20] avgFrameRate
    # [21] constantFrameRate(2) numTemporalLayers(3) temporalIdNested(1)
    #      lengthSizeMinusOne(2) = 3, cioe' prefissi di lunghezza a 4 byte
    b.append((0 << 6) | (1 << 3) | (1 << 2) | 3)

    per_tipo = {}
    for u in parametri:
        per_tipo.setdefault(tipo_nalu(u), []).append(u)
    tipi = [t for t in (32, 33, 34) if t in per_tipo]
    b.append(len(tipi))
    for t in tipi:
        b.append(0x80 | t)                       # array_completeness=1
        b += len(per_tipo[t]).to_bytes(2, "big")
        for u in per_tipo[t]:
            b += len(u).to_bytes(2, "big") + u
    return bytes(b)


def sistema_profondita(hvcc, luma, croma):
    """La profondita' di bit nell'hvcC: indici **17 e 18**, non 19 e 20."""
    b = bytearray(hvcc)
    b[17] = 0xF8 | ((luma - 8) & 7)
    b[18] = 0xF8 | ((croma - 8) & 7)
    return bytes(b)


def stringa_codec(dati_ffprobe, ptl):
    """`hev1.<spazio><profilo>.<compat>.<tier><livello>.<vincoli>` — la forma
       che WebCodecs vuole (RFC 6381 per HEVC).

    ⛔ I numeri arrivano dal flusso, non dalla memoria.  L'inversione dei bit
       del campo di compatibilita' e' la parte che si sbaglia sempre: si
       scrive in esadecimale, con i bit invertiti bit a bit, e senza gli zeri
       davanti."""
    profilo_idc = ptl[0] & 0x1F
    tier = (ptl[0] >> 5) & 1
    compat = int.from_bytes(ptl[1:5], "big")
    invertito = int(f"{compat:032b}"[::-1], 2)
    vincoli = ptl[5:11]
    livello = ptl[11]
    coda = ""
    for byte in reversed(vincoli):
        if byte or coda:
            coda = f".{byte:02X}" + coda
    if not coda:
        coda = ".B0" if vincoli[0] == 0xB0 else ""
    pezzi = [f"hev1.{profilo_idc}", f"{invertito:X}",
             f"{'H' if tier else 'L'}{livello}"]
    return ".".join(pezzi) + coda, {
        "profilo_idc": profilo_idc, "tier": "high" if tier else "main",
        "livello_idc": livello, "livello": livello / 30.0,
        "compatibilita": f"0x{compat:08X}",
    }


def intestazione_rcp(tipo_chiave, numero, istante_us, larghezza, altezza):
    """I 28 byte di `RCP.md` §6.2, scritti QUI, LEGGENDO LA SPECIFICA.

    ⛔⭐ E QUESTA FUNZIONE E' SCRITTA APPOSTA SENZA GUARDARE F2.4.

    Il coordinatore ha posto un divieto che vale piu' del codice che regola:
    *«`intestazione()` di `banchi/02-filo-fotogramma.py` e' importabile senza
    server, ma la pagina non deve ricopiarne il giudizio — se il lettore della
    pagina e' una copia di quello del filo, i due lettori indipendenti tornano
    a essere uno solo, e con essi sparisce il pezzo di arbitro che il progetto
    ha comprato apposta»*.

    `PIANO.md` §0.4 lo dice in generale: buttando RDP il progetto ha perso
    **mstsc**, l'arbitro che protestava gratis quando sbagliavamo a leggere la
    specifica, e *«due programmi scritti dalla stessa mano che vanno d'accordo
    non confermano niente»*.  Le tre cose che lo sostituiscono sono `RCP.md`,
    il validatore del filo e la revisione — e **due implementazioni
    indipendenti della stessa tabella sono la quarta**, quella che si ottiene
    gratis se nessuno copia.

    ⇒ Questi byte li scrive F2.5, dalla tabella di `RCP.md` §6.2 e da nessun
      altro posto.  Se un giorno il lettore di F2.4 e questo scrittore non
      andranno d'accordo, **quel disaccordo e' il regalo**: e' un
      fraintendimento della specifica trovato da due letture separate, invece
      che da un utente.

    ```
     0        2        4        8        12       16       24       28
     │ tipo   │ codec  │ largh. │ altezza│ numero │ istante│ input  │
     │ u16    │ u16    │ u32    │ u32    │ u32    │ u64    │ u32    │
    ```
    ⛔ 28 byte esatti, big-endian, **nessun riempimento**: la nota di §6.2
       racconta che il disegno diceva 32 e che quattro byte non dichiarati
       sono «il difetto muto contro cui quel documento e' stato scritto».
    """
    b = bytearray()
    b += (0x0301 if tipo_chiave else 0x0302).to_bytes(2, "big")   # tipo
    b += (1).to_bytes(2, "big")                                   # codec: HEVC
    b += int(larghezza).to_bytes(4, "big")
    b += int(altezza).to_bytes(4, "big")
    b += int(numero).to_bytes(4, "big")
    b += int(istante_us).to_bytes(8, "big")
    # ⚠ `input`: l'identificatore dell'ultimo input iniettato prima della
    #   cattura, **0** se nessuno.  Alla fase 2 non c'e' input: e' 0, ed e' il
    #   valore che la specifica prescrive — non un riempimento.
    b += (0).to_bytes(4, "big")
    if len(b) != 28:
        errore(f"l'intestazione e' di {len(b)} byte invece di 28")
    return bytes(b)


def costruisci(nome_pattern, profondita, sorgente10=False, lossless=False):
    ordine = PATTERN[nome_pattern]
    if sorgente10:
        grezzo, celle = disegna10(ordine)
    else:
        grezzo, celle = disegna(ordine)
    unico = grezzo * QUANTI
    flusso = codifica(unico, profondita, sorgente10=sorgente10,
                      lossless=lossless)
    info = sonda(flusso)

    nalu = spezza_nalu(flusso)
    unita = unita_daccesso(nalu)
    if len(unita) != QUANTI:
        errore(f"attese {QUANTI} unita' d'accesso, il flusso ne ha {len(unita)}: "
               "il taglio delle NALU o `keyint=1` non hanno fatto quel che dicono")

    parametri = [u for u in unita[0] if tipo_nalu(u) in (32, 33, 34)]
    if not parametri:
        errore("la prima unita' d'accesso non porta VPS/SPS/PPS: "
               "`repeat-headers=1` non ha avuto effetto")
    if not e_chiave(unita[0]):
        errore("la prima unita' d'accesso non e' una chiave: la fase 2 consegna "
               "UN fotogramma chiave, e un banco che comincia da un delta "
               "misura una cosa che il prodotto non fa")
    sps = next(u for u in parametri if tipo_nalu(u) == 33)
    ptl = leggi_ptl(sps)
    codec, dettagli = stringa_codec(info, ptl)

    # ⛔ Il livello letto nell'SPS e quello che dice `ffprobe` devono coincidere.
    #    Due strumenti sullo stesso fatto: e' `LEZIONI.md` §1.9 regola 2, e
    #    stanotte ha gia' pagato — senza questo controllo la prima stesura
    #    scriveva `L0` e nessuno se ne sarebbe accorto fino al rifiuto di Chrome.
    if info.get("level") not in (None, -99) and int(info["level"]) != ptl[11]:
        errore(f"il livello letto nell'SPS ({ptl[11]}) non e' quello che dice "
               f"ffprobe ({info.get('level')}): uno dei due lettori sbaglia, e "
               "finche' non si sa quale la stringa di codec non vale niente")

    # ⛔ La profondita' si RILEGGE dal flusso prodotto: `ffprobe` dice il
    #    formato dei pixel, e se non e' quello chiesto ci si ferma qui invece
    #    di porre al browser una domanda sui 10 bit sopra un flusso a 8.
    pix = info.get("pix_fmt", "")
    attesa = "yuv420p10le" if profondita == 10 else "yuv420p"
    if pix != attesa:
        errore(f"il flusso e' {pix}, non {attesa}: la domanda sui "
               f"{profondita} bit non si puo' porre su questo flusso")
    atteso_profilo = "Main 10" if profondita == 10 else "Main"
    if info.get("profile") != atteso_profilo:
        errore(f"il profilo del flusso e' «{info.get('profile')}», non "
               f"«{atteso_profilo}»: x265 ha scelto da se' (LEZIONI.md §1.8), e "
               "misurare Main10 dando in pasto un altro profilo e' misurare "
               "un'altra cosa")
    atteso_idc = 2 if profondita == 10 else 1
    if dettagli["profilo_idc"] != atteso_idc:
        errore(f"l'SPS dichiara profile_idc {dettagli['profilo_idc']}, atteso "
               f"{atteso_idc}: il lettore dell'SPS e ffprobe non concordano")

    hvcc = sistema_profondita(costruisci_hvcc(parametri), profondita, profondita)

    # ⛔ CHE COSA C'E' DAVVERO DENTRO, misurato ridecodificando il flusso.
    #    Non «gliel'ho dato a 10 bit»: quanti livelli distinti ha la sfumatura,
    #    e quanti campioni sono multipli di 4.  Vedi `conta_livelli()`.
    livelli = conta_livelli(flusso, profondita, ALTEZZA - ALTEZZA_SFUMATURA)
    livelli_sorgente = conta_livelli_sorgente(grezzo, sorgente10,
                                              ALTEZZA - ALTEZZA_SFUMATURA)

    def pezzi_annexb():
        """⛔ LA FORMA CHE F2.3 HA DECISO, e va scritta com'e' arrivata:

           `[00 00 00 01] VPS · SPS · PPS · SEI · IDR`, portati cosi' come
           sono, **senza `description`**.  Primo fotogramma sempre chiave, con
           i parameter set dentro.  Le ragioni sono di F2.3 e sono misurate:
           e' quel che `libavcodec` gia' produce; in Chromium l'hvcC costa
           un'allocazione e una copia per fotogramma perche' converte comunque
           ad Annex-B; e l'hvcC ha una trappola sul profile-tier-level che fa
           **rifiutare** `isConfigSupported()`.

           ⭐ E la trappola non e' un'ipotesi: questo stesso programma ci e'
              caduto dentro il 12 agosto (vedi `sguscia()`), da un'altra porta.

           ⚠ Start code a **4 byte davanti a ogni NALU**, SEI compresa: e' la
             forma che F2.3 consegna, e un banco che ne usasse una diversa
             misurerebbe un flusso che il prodotto non produrra' mai."""
        fuori = []
        for i, u in enumerate(unita):
            corpo = b"".join(b"\x00\x00\x00\x01" + x for x in u)
            chiave = e_chiave(u)
            istante = round(i * 1e6 / RITMO)
            fuori.append({"tipo": "key" if chiave else "delta",
                          "istante": istante,
                          "nalu": [tipo_nalu(x) for x in u],
                          # ⛔ I 28 byte di RCP §6.2, scritti da NOI dalla
                          #    specifica: vedi `intestazione_rcp()`.
                          "intestazione_rcp": base64.b64encode(
                              intestazione_rcp(chiave, i, istante,
                                               LARGHEZZA, ALTEZZA)).decode(),
                          "dati": base64.b64encode(corpo).decode()})
        return fuori

    def pezzi_hvcc():
        fuori = []
        for i, u in enumerate(unita):
            # ⛔ Nel formato hvcC le NALU di parametro stanno nella
            #    `description`, non nel pezzo: metterle in tutt'e due i posti e'
            #    legale ma confonde chi legge il registro.  Qui il pezzo porta
            #    solo le NALU di fetta.
            fette = [x for x in u if tipo_nalu(x) not in (32, 33, 34)]
            corpo = b"".join(len(x).to_bytes(4, "big") + x for x in fette)
            fuori.append({"tipo": "key" if e_chiave(u) else "delta",
                          "istante": round(i * 1e6 / RITMO),
                          "dati": base64.b64encode(corpo).decode()})
        return fuori

    # ⛔ F2.3 consegna la stringa nella forma `hev1.…`, e lascia aperta una
    #    `[?]`: *«non e' verificato che Chromium accetti il prefisso `hev1.` in
    #    Annex-B»*.  Qui si porta accanto anche la forma `hvc1.…`, perche' la
    #    pagina possa provarle tutt'e due sullo STESSO flusso e chiudere quella
    #    `[?]` con una misura invece che con una lettura.
    codec_hvc1 = "hvc1" + codec[4:]
    comune = {
        "pattern": nome_pattern,
        "profondita": profondita,
        "codec": codec,
        "codec_hvc1": codec_hvc1,
        "codec_dettagli": dettagli,
        "larghezza": LARGHEZZA,
        "altezza": ALTEZZA,
        "ritmo": RITMO,
        "fotogrammi": QUANTI,
        "pix_fmt": pix,
        # ⛔ `profondita` e' quel che il CONTENITORE dichiara; `sorgente10` e
        #    `livelli` dicono che cosa c'e' DENTRO.  Tenerli distinti e' quel
        #    che impedisce di leggere «Main10» come «10 bit».
        "sorgente10": sorgente10,
        "lossless": lossless,
        "livelli": livelli,
        "livelli_sorgente": livelli_sorgente,
        "profilo_ffprobe": info.get("profile"),
        "livello_ffprobe": info.get("level"),
        "celle": celle,
        "tinte": [{"nome": n, "rgb": list(c)} for n, c in TINTE],
        "sfumatura_da_y": ALTEZZA - ALTEZZA_SFUMATURA,
        "byte_flusso": len(flusso),
    }
    uscite = []
    for forma, pezzi, descrizione in (
            ("annexb", pezzi_annexb(), None),
            ("hvcc", pezzi_hvcc(), base64.b64encode(hvcc).decode())):
        d = dict(comune)
        d["forma"] = forma
        d["descrizione"] = descrizione
        d["pezzi"] = pezzi
        etichetta = f"{profondita}bitvero" if sorgente10 else f"{profondita}bit"
        if lossless:
            etichetta += "-lossless"
        nome = f"{nome_pattern}-{etichetta}-{forma}"
        d["nome"] = nome
        uscite.append((nome, d))
    return uscite


def costruisci_vp9(nome_pattern):
    """⛔⭐ IL CONTROLLO POSITIVO DEL BANCO, E SENZA DI LUI NON C'E' VERDETTO.

    La domanda di F2.5 e' *«questo browser porta un byte HEVC fino al pixel
    dipinto?»*.  Se la risposta e' **no**, ci sono due letture opposte e
    identiche a vedersi:

        a) questo browser non decodifica HEVC;
        b) questa pagina non porta **nessun** flusso fino al pixel — il
           decodificatore, la tela, la rilettura o la classificazione sono
           rotti, e HEVC non c'entra.

    ⛔ Senza un flusso che questo browser decodifica **di sicuro**, il banco non
       puo' distinguerle, e scriverebbe «Firefox non decodifica HEVC» avendo
       misurato il proprio difetto.  E' `LEZIONI.md` §1.9 regola 2 — *«questo
       strumento sa trovare qualcosa che c'e' di sicuro?»* — e la stessa forma
       che `web.md` §3.3 racconta come il rilievo piu' grave della revisione R2.

    VP9 e' il flusso scelto perche' e' l'unico codec video che **tutti e tre**
    i motori decodificano senza brevetti di mezzo, e perche' e' gia' il
    controllo che S2 §4.4 usa per la stessa ragione.  ⚠ Qui NON serve a
    distinguere hardware da software (quello e' S2, sul telefono): serve a
    dimostrare che **la catena esiste**.

    ⛔ E arriva da `ffmpeg`, non da `VideoEncoder` nella pagina come faceva S2:
       un controllo che dipende da una seconda API del browser sparisce
       proprio sul motore dove serve di piu' — quello che di WebCodecs ha
       poco."""
    ordine = PATTERN[nome_pattern]
    grezzo, celle = disegna(ordine)
    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-framerate", str(RITMO),
        "-i", "pipe:0",
        "-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p",
        "-g", str(QUANTI), "-keyint_min", str(QUANTI),
        "-crf", "20", "-b:v", "0", "-deadline", "good", "-cpu-used", "5",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-f", "ivf", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=grezzo * QUANTI)
    if codice != 0 or len(uscita) < 32:
        errore("libvpx-vp9 non ha prodotto il flusso di controllo: senza di lui "
               "un «no» su HEVC non si distingue da un banco rotto",
               errori.decode("utf-8", "replace"))

    pezzi = spoglia_ivf(uscita, QUANTI)

    return {
        "nome": f"{nome_pattern}-vp9",
        "pattern": nome_pattern,
        "ruolo": "controllo",
        "profondita": 8,
        # ⚠ Le tre stringhe si provano nell'ordine: il livello di VP9 e' un
        #   campo che i motori trattano con severita' diversa, e provarne una
        #   sola farebbe cadere il CONTROLLO per una ragione che non c'entra
        #   con quel che deve controllare.  Quella che passa si scrive
        #   nell'esito.
        "codec": "vp09.00.41.08",
        "codec_alternativi": ["vp09.00.31.08", "vp09.00.10.08"],
        "forma": "grezza",
        "descrizione": None,
        "larghezza": LARGHEZZA, "altezza": ALTEZZA, "ritmo": RITMO,
        "fotogrammi": QUANTI, "pix_fmt": "yuv420p",
        "celle": celle,
        "tinte": [{"nome": n_, "rgb": list(c)} for n_, c in TINTE],
        "sfumatura_da_y": ALTEZZA - ALTEZZA_SFUMATURA,
        "byte_flusso": len(uscita),
        "pezzi": pezzi,
    }


def spoglia_ivf(uscita, quanti):
    """IVF → elenco di pezzi.  32 byte d'intestazione di file, poi per ogni
       fotogramma 12 byte (4 di lunghezza, 8 di istante) e i byte del
       fotogramma.  ⛔ Estratta da `costruisci_vp9()` quando e' servita anche
       ad AV1: due copie della stessa aritmetica sono due posti dove sbagliare
       l'offset, e qui un offset sbagliato non da' un errore — da' un flusso
       che il browser rifiuta, cioe' un `[M]` falso contro il browser."""
    if uscita[:4] != b"DKIF":
        errore("il flusso non comincia con DKIF: non e' un IVF")
    pezzi = []
    i, n = 32, 0
    while i + 12 <= len(uscita):
        lung = int.from_bytes(uscita[i:i + 4], "little")
        corpo = uscita[i + 12:i + 12 + lung]
        if len(corpo) != lung:
            errore("un fotogramma IVF e' troncato: il lettore o il file sbagliano")
        pezzi.append({"tipo": "key" if n == 0 else "delta",
                      "istante": round(n * 1e6 / RITMO),
                      "dati": base64.b64encode(corpo).decode()})
        i += 12 + lung
        n += 1
    if len(pezzi) != quanti:
        errore(f"il flusso ha {len(pezzi)} fotogrammi invece di {quanti}")
    return pezzi


def costruisci_av1(nome_pattern, sorgente10):
    """⛔⭐ AV1 — E NON E' UN CODEC IN PIU': E' IL RIPIEGO NEGOZIATO.

    L'utente ha deciso HEVC **con un ripiego negoziato**, invece di dichiarare
    un requisito «Chrome con VA-API».  Il candidato naturale era il VP9 di
    questo banco (8 celle su 8 in tutte e quattro le caselle) — ⛔ ma `RCP.md`
    ha gia' la negoziazione, e in RCP/1 i valori ammessi di `video.codec` sono
    **`hevc` e `av1`**: `vp9` compare in §4.3 come **l'esempio canonico di
    valore che un'implementazione RCP/1 deve IGNORARE**, e §9 ha chiuso la
    finestra dei valori nuovi il 10 agosto.

    ⇒ Mettere VP9 in RCP/1 vorrebbe dire aprire **RCP/2** o dichiarare
      un'eccezione a §9.  **AV1 non costa niente**: e' gia' normativo, e ha
      gia' il suo `codec = 2` in `RCP.md` §6.2.

    ⚠ E `web.md` **O2** dichiarava AV1 *«un vicolo cieco da entrambi i lati»* —
      il nostro ferro non lo codifica in hardware `[M]`, e in decodifica non
      aggiunge niente che HEVC non dia.  ⛔ Quella riga vale per il codec
      **principale**; qui la domanda e' un'altra: **regge come ripiego, dove
      HEVC non c'e'?**  Il vicolo cieco resta tale finche' qualcuno non misura
      il ramo che non era stato percorso.

    ⛔ La codifica e' **in software** (`libaom-av1`), ed e' un fatto da
       dichiarare, non un ripiego di comodo: `[M]` 9 agosto, il nostro ferro
       AV1 non lo codifica in hardware.  Alla fase 2 la codifica e' software
       comunque, di proposito (`PIANO.md` fase 2).
    """
    if sorgente10:
        grezzo, celle = disegna10(nome_pattern and PATTERN[nome_pattern])
        pix, sorgente = "yuv420p10le", "rgb48le"
    else:
        grezzo, celle = disegna(PATTERN[nome_pattern])
        pix, sorgente = "yuv420p", "rgb24"

    comando = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "rawvideo", "-pix_fmt", sorgente,
        "-s", f"{LARGHEZZA}x{ALTEZZA}", "-framerate", str(RITMO),
        "-i", "pipe:0",
        "-c:v", "libaom-av1", "-pix_fmt", pix,
        # ⛔ Una chiave in testa e cinque delta, come per HEVC: la stessa forma,
        #    o il confronto fra i due codec confronterebbe anche la struttura.
        "-g", str(QUANTI), "-keyint_min", str(QUANTI),
        "-crf", "20", "-b:v", "0", "-cpu-used", "8",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-f", "ivf", "pipe:1",
    ]
    codice, uscita, errori = esegui(comando, entrata=grezzo * QUANTI)
    if codice != 0 or len(uscita) < 32:
        errore(f"libaom-av1 non ha prodotto il flusso ({pix})",
               errori.decode("utf-8", "replace"))

    info = sonda_ivf(uscita)
    if info.get("pix_fmt") != pix:
        errore(f"il flusso AV1 e' {info.get('pix_fmt')}, non {pix}: la domanda "
               "sulla profondita' non si puo' porre su questo flusso")

    # ⛔ La stringa si compone dai numeri LETTI nel flusso, come per HEVC:
    #    `av01.<profilo>.<seq_level_idx a 2 cifre><tier>.<profondita' a 2 cifre>`.
    #    ⚠ `seq_level_idx` NON e' il livello in chiaro: 4 vuol dire 3.0.  Si
    #      scrive l'indice, che e' quel che la stringa vuole.
    profili = {"Main": 0, "High": 1, "Professional": 2}
    profilo = profili.get(info.get("profile"), 0)
    livello = int(info.get("level") or 4)
    bit = 10 if sorgente10 else 8
    codec = f"av01.{profilo}.{livello:02d}M.{bit:02d}"

    livelli = conta_livelli_ivf(uscita, bit, ALTEZZA - ALTEZZA_SFUMATURA)
    livelli_sorgente = conta_livelli_sorgente(grezzo, sorgente10,
                                              ALTEZZA - ALTEZZA_SFUMATURA)
    etichetta = "10bitvero" if sorgente10 else "8bit"
    return {
        "nome": f"{nome_pattern}-av1-{etichetta}",
        "pattern": nome_pattern,
        "ruolo": "bersaglio",
        "codec": codec,
        # ⚠ Le alternative servono se `seq_level_idx` non fosse quel che
        #   pensiamo: la pagina le prova, e SCRIVE quale ha usato.  ⛔ Non e'
        #   indovinare — e' dichiarare che il campo ha un'incertezza, invece di
        #   far cadere la misura su di essa.
        "codec_alternativi": [f"av01.{profilo}.{l:02d}M.{bit:02d}"
                              for l in (4, 8, 0) if l != livello],
        "profondita": bit,
        "sorgente10": sorgente10,
        "lossless": False,
        "forma": "grezza",
        "descrizione": None,
        "larghezza": LARGHEZZA, "altezza": ALTEZZA, "ritmo": RITMO,
        "fotogrammi": QUANTI, "pix_fmt": pix,
        "profilo_ffprobe": info.get("profile"),
        "livello_ffprobe": info.get("level"),
        "celle": celle,
        "tinte": [{"nome": n_, "rgb": list(c)} for n_, c in TINTE],
        "sfumatura_da_y": ALTEZZA - ALTEZZA_SFUMATURA,
        "byte_flusso": len(uscita),
        "livelli": livelli,
        "livelli_sorgente": livelli_sorgente,
        "pezzi": spoglia_ivf(uscita, QUANTI),
    }


def sonda_ivf(flusso):
    """Come `sonda()`, ma su un IVF invece che su un Annex-B nudo."""
    comando = ["ffprobe", "-hide_banner", "-v", "error", "-of", "json",
               "-show_streams", "-select_streams", "v:0", "-i", "pipe:0"]
    codice, uscita, errori = esegui(comando, entrata=flusso)
    if codice != 0:
        errore("ffprobe non ha saputo leggere il flusso IVF appena prodotto",
               errori.decode("utf-8", "replace"))
    try:
        return json.loads(uscita)["streams"][0]
    except Exception as e:
        errore(f"ffprobe ha risposto qualcosa che non e' uno stream: {e}",
               uscita[:400])


def conta_livelli_ivf(flusso, profondita, da_riga):
    """`conta_livelli()` per un IVF: ridecodifica e conta i livelli veri."""
    comando = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error",
               "-i", "pipe:0",
               "-pix_fmt", "yuv420p10le" if profondita == 10 else "yuv420p",
               "-frames:v", "1", "-f", "rawvideo", "pipe:1"]
    codice, uscita, errori = esegui(comando, entrata=flusso)
    if codice != 0 or not uscita:
        errore("il flusso AV1 non si ridecodifica: senza, la profondita' vera "
               "non e' misurabile", errori.decode("utf-8", "replace"))
    passo = 2 if profondita == 10 else 1
    livelli = {}
    for y in range(da_riga, ALTEZZA):
        riga = y * LARGHEZZA * passo
        for x in range(LARGHEZZA):
            i = riga + x * passo
            v = uscita[i] if passo == 1 else (uscita[i] | (uscita[i + 1] << 8))
            livelli[v] = livelli.get(v, 0) + 1
    quanti = sum(livelli.values())
    multipli = sum(n for v, n in livelli.items() if v % 4 == 0)
    return {
        "livelli_distinti": len(livelli), "campioni": quanti,
        "frazione_multipli_di_4": round(multipli / quanti, 4) if quanti else None,
        "minimo": min(livelli) if livelli else None,
        "massimo": max(livelli) if livelli else None,
    }


def principale():
    if "--elenca" in sys.argv:
        if not DOVE.is_dir():
            print(f"⛔ {DOVE} non esiste: le sequenze non sono mai state costruite")
            return 1
        trovate = sorted(DOVE.glob("*.json"))
        print(f"-- {len(trovate)} sequenze in {DOVE}")
        for f in trovate:
            d = json.loads(f.read_text())
            print(f"   {d['nome']:28s} {d['codec']:22s} {d['pix_fmt']:12s} "
                  f"{len(d['pezzi'])} pezzi · descrizione: "
                  f"{'SI' if d['descrizione'] else 'no'}")
        return 0 if trovate else 1

    for attrezzo in ("ffmpeg", "ffprobe"):
        if not shutil.which(attrezzo):
            errore(f"{attrezzo} non c'e' su questa macchina: le sequenze non si "
                   "costruiscono, e senza sequenze il banco non misura niente")
    codice, uscita, errori = esegui(["ffmpeg", "-hide_banner", "-encoders"])
    if codice != 0:
        errore("`ffmpeg -encoders` e' fallito", errori.decode("utf-8", "replace"))
    if b"libx265" not in uscita:
        errore("questo ffmpeg non ha libx265: HEVC non si codifica")
    if b"libaom-av1" not in uscita:
        errore("questo ffmpeg non ha libaom-av1: il RIPIEGO negoziato non si "
               "puo' misurare, e senza misura non si decide fra AV1 e RCP/2")
    if b"libvpx-vp9" not in uscita:
        errore("questo ffmpeg non ha libvpx-vp9: senza il flusso di CONTROLLO "
               "un «no» su HEVC non si distingue da un banco rotto, e il banco "
               "non ha il diritto di pubblicare verdetti")

    DOVE.mkdir(exist_ok=True)
    fatte = []
    for nome_pattern in ("A", "B"):
        for profondita in (10, 8):
            for nome, d in costruisci(nome_pattern, profondita):
                d["ruolo"] = "bersaglio"
                (DOVE / f"{nome}.json").write_text(
                    json.dumps(d, ensure_ascii=False), encoding="utf-8")
                fatte.append(d)
                print(f"   \033[1;32mOK\033[0m  {nome:28s} {d['codec']:22s} "
                      f"{d['pix_fmt']:12s} {d['byte_flusso']:7d} byte  "
                      f"descrizione: {'SI' if d['descrizione'] else 'no':2s}  "
                      f"livelli {d['livelli']['livelli_distinti']:4d}  "
                      f"×4 {d['livelli']['frazione_multipli_di_4']}")

    # ⛔ LA SEQUENZA A 10 BIT VERI — il caso di banco che F2.2 ha reso
    #    necessario: la catena vera arriva a 8 bit da sola, quindi la domanda
    #    «il browser torna a 8 bit senza dirlo?» con quel flusso non e'
    #    ponibile.  Questo flusso la pone.
    # ⛔ E LE DUE LOSSLESS SONO LA COPPIA CHE DECIDE.  Sul flusso lossy la firma
    #    dei «multipli di 4» e' cancellata dal rumore di quantizzazione (0,2488
    #    contro 0,2524: indistinguibili).  Senza perdita la firma sopravvive
    #    fino al decodificatore, e le due sequenze pongono al browser una
    #    domanda a cui, sul flusso lossy, non si potrebbe nemmeno arrivare.
    for sorgente10, quale in ((False, "8 bit PROMOSSI"), (True, "10 BIT VERI")):
        for nome, d in costruisci("A", 10, sorgente10=sorgente10, lossless=True):
            d["ruolo"] = "bersaglio"
            (DOVE / f"{nome}.json").write_text(
                json.dumps(d, ensure_ascii=False), encoding="utf-8")
            fatte.append(d)
            print(f"   \033[1;32mOK\033[0m  {nome:32s} {d['pix_fmt']:12s} "
                  f"{d['byte_flusso']:8d} byte  ⭐ {quale:15s} "
                  f"sorgente: {d['livelli_sorgente']['livelli_distinti']:4d} liv, "
                  f"×4 {d['livelli_sorgente']['frazione_multipli_di_4']}  ·  "
                  f"decodificato: {d['livelli']['livelli_distinti']:4d} liv, "
                  f"×4 {d['livelli']['frazione_multipli_di_4']}")

    for nome_pattern in ("A",):
        for nome, d in costruisci(nome_pattern, 10, sorgente10=True):
            d["ruolo"] = "bersaglio"
            (DOVE / f"{nome}.json").write_text(
                json.dumps(d, ensure_ascii=False), encoding="utf-8")
            fatte.append(d)
            print(f"   \033[1;32mOK\033[0m  {nome:28s} {d['codec']:22s} "
                  f"{d['pix_fmt']:12s} {d['byte_flusso']:7d} byte  "
                  f"⭐ 10 BIT VERI  "
                  f"livelli {d['livelli']['livelli_distinti']:4d}  "
                  f"×4 {d['livelli']['frazione_multipli_di_4']}")
    # ⛔ AV1 — il RIPIEGO negoziato, non un codec in piu'.  Tre sequenze:
    #    A e B a 8 bit (servono anche a P3/P5, la distinzione), e A a 10 bit
    #    veri, perche' «la profondita' e' meta' del motivo per cui questo
    #    progetto ha scelto HEVC».
    for nome_pattern, sorgente10 in (("A", False), ("B", False), ("A", True)):
        d = costruisci_av1(nome_pattern, sorgente10)
        (DOVE / f"{d['nome']}.json").write_text(
            json.dumps(d, ensure_ascii=False), encoding="utf-8")
        fatte.append(d)
        print(f"   \033[1;32mOK\033[0m  {d['nome']:32s} {d['codec']:18s} "
              f"{d['pix_fmt']:12s} {d['byte_flusso']:8d} byte  ⭐ RIPIEGO  "
              f"sorgente {d['livelli_sorgente']['livelli_distinti']:4d} liv · "
              f"flusso {d['livelli']['livelli_distinti']:4d} liv")

    for nome_pattern in ("A", "B"):
        d = costruisci_vp9(nome_pattern)
        (DOVE / f"{d['nome']}.json").write_text(
            json.dumps(d, ensure_ascii=False), encoding="utf-8")
        fatte.append(d)
        print(f"   \033[1;32mOK\033[0m  {d['nome']:28s} {d['codec']:22s} "
              f"{d['pix_fmt']:12s} {d['byte_flusso']:7d} byte  "
              f"⭐ CONTROLLO")

    # ⛔ Il controllo positivo di QUESTO programma: le sequenze a 10 e a 8 bit
    #    devono avere stringhe di codec DIVERSE.  Se fossero uguali, tutte le
    #    misure sui 10 bit poggerebbero su una configurazione che non li chiede
    #    nemmeno — e il banco direbbe «il browser decodifica Main10» avendogli
    #    dato del Main.  E' `LEZIONI.md` §1.2 applicata allo strumento.
    bersagli = [d for d in fatte if d["ruolo"] == "bersaglio"]
    dieci = {d["codec"] for d in bersagli if d["profondita"] == 10}
    otto = {d["codec"] for d in bersagli if d["profondita"] == 8}
    print()
    if dieci & otto:
        print("\033[1;31mNO\033[0m  10 bit e 8 bit hanno la STESSA stringa di codec "
              f"({dieci & otto}): il banco non potrebbe distinguerli", file=sys.stderr)
        return 1
    print(f"    \033[1;32mOK\033[0m  controllo positivo: Main10 -> {sorted(dieci)} "
          f"e Main -> {sorted(otto)} sono stringhe diverse")
    print(f"    -- {len(fatte)} sequenze in {DOVE}")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
