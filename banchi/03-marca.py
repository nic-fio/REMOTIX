#!/usr/bin/env python3
"""03-marca.py — IL LETTORE DELLA MARCA della scena della fase 3.

    python3 03-marca.py leggi  fotogramma.rgb24 --larghezza 1280 --altezza 720
    python3 03-marca.py leggi  fotogramma.png
    python3 03-marca.py dipingi fuori.png --disegno 41 --istante-us 123456 --giro g1
    python3 03-marca.py conta  --shm remotix-scena

===========================================================================
⛔ CHE COSA DEVE SAPER DIRE, E LA META' CHE SI DIMENTICA

Il mandato: *«il lettore della marca: la funzione che, dato un fotogramma
decodificato, restituisce il numero del disegno e l'istante — e ⛔ che sa
anche dire "la marca non c'e'".  Un rilevatore che dice sempre si' misura zero
ed e' felice a torto»* (`STUDI.md` §web §6.3, controllo **P3**).

⇒ `leggi_marca()` ha DUE uscite, non una:

    {"c_e": True,  "disegno": 41, "istante_us": 987654321, "giro": 0x…, …}
    {"c_e": False, "perche": "il CRC non torna …", "contrasto": 0.31, …}

⛔ E `c_e: False` porta SEMPRE il perche', perche' «non c'e' la marca», «il
   fotogramma e' piu' piccolo del blocco» e «il contrasto e' troppo basso»
   sono tre diagnosi diverse che mandano a cercare in tre posti diversi.
   `LEZIONI.md` §1.9: una lettura negata non e' una lettura che dice zero.

===========================================================================
⛔ I TRE SETACCI, E QUANTO VALGONO

Perche' un rumore qualunque non passi per una marca, ci sono tre filtri in
fila.  I numeri non sono a sentimento:

  1. **contrasto**  la differenza fra il 90° e il 10° percentile delle 144
     celle dev'essere ≥ 0,25 (su 0..1).  ⚠ Da sola non basta e non e' pensata
     per bastare: mezzo desktop ha piu' contrasto di cosi'.  Serve a dire
     «qui non c'e' segnale binario» invece di decidere a caso una soglia fra
     due valori quasi uguali;
  2. **sync**  gli 8 bit di testa devono valere esattamente 0xB2.  Un blocco
     di rumore ci azzecca 1 volta su 256;
  3. **CRC-16**  sui 15 byte del corpo.  Ci azzecca 1 volta su 65 536.

  ⇒ falso positivo per posizione provata ≈ 1 / 16 700 000.  ⛔ E il numero
    delle posizioni provate NON e' uno: la ricerca prova (2·R+1)² scorrimenti
    (25 di riposo), quindi il conto vero e' ≈ 1 / 670 000.  Sta scritto qui
    perche' il controllo negativo della certificazione lo METTE ALLA PROVA su
    migliaia di fotogrammi di rumore, invece di fidarsi di questo calcolo.

===========================================================================
⛔ PERCHE' LA LETTURA REGGE LA CODIFICA CON PERDITA

Il mandato lo chiede e vieta di darlo per scontato.  Le difese, e ciascuna
contro un difetto preciso della codifica:

  · **si legge il CENTRO della cella**, non la cella intera: il quadrato
    centrale al 50 % del lato (12 px su 24).  Il *ringing* di HEVC vive sui
    bordi del blocco, e i bordi qui non si guardano;
  · **si legge la LUMINANZA**, e i due livelli sono bianco pieno e nero
    pieno: 255 livelli di escursione.  Il 4:2:0 tocca la crominanza, e la
    marca nella crominanza non ci sta;
  · **la soglia e' RELATIVA** — la mediana fra il 10° e il 90° percentile
    delle celle di QUESTO fotogramma — invece che a 128.  Cosi' regge un
    guadagno o uno scarto (gamma limitata letta come piena, per esempio) che
    sposterebbe una soglia fissa;
  · **si scorre di ±R pixel** cercando la posizione che passa i tre setacci:
    una tela che sposta l'immagine di un pixel non fa sparire la marca.

⛔ E «regge» non e' un'opinione: `03-scena-certifica.sh` codifica la marca
   con x265 Main10 a QP crescente e dice **fino a che QP** si rilegge.  Se un
   giorno il codificatore cambia, quel numero cambia e si vede.
"""
import argparse
import hashlib
import json
import mmap
import os
import struct
import sys
import time

# ⛔⭐ NUMPY SI CARICA QUANDO SERVE, NON ALL'IMPORT — 13 agosto 2026.
#
# Il coordinatore riporta che su NIC-OS **numpy non c'e'**.  Con
# `import numpy` in testa, `03-marca.py conta` — che numpy non lo usa affatto,
# perche' legge un blocco di memoria condivisa con `struct` — moriva su
# NIC-OS con un ImportError che parla di una libreria, non del problema.
#
# ⇒ il tappo sta DENTRO questo file e non fuori: `conta` funziona ovunque, e
#   chi chiede `leggi` o `dipingi` senza numpy riceve una frase che dice **che
#   cosa fare**, non il nome di un modulo mancante.
# ⚠ E `nome` e `conta` restano usabili da NIC-OS, che e' dove i banchi girano.
_np = None


def np_o_muori(che):
    """numpy, oppure una frase che dice dove si fa la lettura."""
    global _np
    if _np is None:
        try:
            import numpy
        except ImportError:
            raise SystemExit(
                "⛔ «%s» ha bisogno di numpy, e su questa macchina non c'e'.\n"
                "   ⚠ Non e' un difetto della marca: e' che la LETTURA DEI PIXEL "
                "si fa dove numpy c'e' (su CHUWI).\n"
                "   ⭐ Quel che funziona QUI senza numpy: «03-marca.py conta» (i "
                "disegni del client, letti dal blocco condiviso) e «03-marca.py "
                "nome» (il numero a 32 bit di un giro).\n"
                "   ⇒ o si copia il fotogramma dove numpy c'e', o si installa "
                "python3-numpy." % che)
        _np = numpy
    return _np

# ───────────────────────────────────────────────────────────────────────────
# LA GEOMETRIA — ⛔ deve coincidere con `03-scena.c`.  Chi cambia un numero
# qui e non la' rompe la lettura, e la certificazione (controllo P6) se ne
# accorge invece di lasciarlo scoprire a una misura sbagliata.
# ───────────────────────────────────────────────────────────────────────────
SYNC      = 0xB2
VERSIONE  = 0x01
COLONNE   = 18
RIGHE     = 8
BIT       = COLONNE * RIGHE          # 144
CELLA     = 24
MARGINE   = 32
QUIETE    = 12

CONTRASTO_MINIMO = 0.25              # vedi §«i tre setacci»
RICERCA          = 2                 # ± px

# BT.709, che e' la matrice che F2.3 sceglie e che il resto della catena
# dichiara.  ⚠ Qui serve solo a fare UN numero da tre canali: bianco e nero
# danno lo stesso risultato con qualunque matrice sensata.
PESI_LUMA = (0.2126, 0.7152, 0.0722)


class MarcaGeometria:
    def __init__(self, cella=CELLA, margine=MARGINE, quiete=QUIETE,
                 colonne=COLONNE, righe=RIGHE):
        self.cella, self.margine, self.quiete = int(cella), int(margine), int(quiete)
        self.colonne, self.righe = int(colonne), int(righe)
        self.bit = self.colonne * self.righe

    def blocco(self):
        return (self.margine, self.margine,
                self.colonne * self.cella, self.righe * self.cella)

    def __repr__(self):
        return ("MarcaGeometria(cella=%d, margine=%d, quiete=%d, %dx%d)"
                % (self.cella, self.margine, self.quiete, self.colonne, self.righe))


GEOMETRIA = MarcaGeometria()


# ───────────────────────────────────────────────────────────────────────────
def fnv1a32(s):
    """Lo stesso nome corto che `03-scena.c` mette nella marca."""
    h = 2166136261
    for b in s.encode("utf-8"):
        h ^= b
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def crc16(dati):
    """CRC-16/CCITT-FALSE — poly 0x1021, init 0xFFFF, senza riflessioni."""
    c = 0xFFFF
    for b in dati:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def componi_carico(disegno, istante_us, giro_numero):
    """I 18 byte della marca, nell'ordine in cui finiscono nelle celle."""
    corpo = struct.pack(">BII", VERSIONE, giro_numero & 0xFFFFFFFF,
                        disegno & 0xFFFFFFFF)
    t = istante_us & 0xFFFFFFFFFFFF                     # 48 bit
    corpo += bytes(((t >> 40) & 0xFF, (t >> 32) & 0xFF, (t >> 24) & 0xFF,
                    (t >> 16) & 0xFF, (t >> 8) & 0xFF, t & 0xFF))
    assert len(corpo) == 15
    return bytes([SYNC]) + corpo + struct.pack(">H", crc16(corpo))


def carico_in_bit(tutto, quanti):
    np = np_o_muori("carico_in_bit")
    b = np.zeros(quanti, dtype=np.uint8)
    for i in range(quanti):
        b[i] = (tutto[i >> 3] >> (7 - (i & 7))) & 1
    return b


# ───────────────────────────────────────────────────────────────────────────
# IL PITTORE.  ⛔ Serve al CONTROLLO POSITIVO e basta: la scena vera la
# dipinge `03-scena.c`.  Che i due dipingano la stessa cosa non si assume —
# `03-scena-certifica.sh` (P6) legge con questo lettore un fotogramma dipinto
# dalla C e confronta con quel che la C ha dichiarato.
# ───────────────────────────────────────────────────────────────────────────
def dipingi_marca(img, disegno, istante_us, giro_numero, geo=GEOMETRIA):
    """Dipinge la marca DENTRO `img` (uint8 [h,w,3]).  Ritorna `img`."""
    np_o_muori("dipingi_marca")
    tutto = componi_carico(disegno, istante_us, giro_numero)
    bit = carico_in_bit(tutto, geo.bit)
    x0, y0, w, h = geo.blocco()
    H, W = img.shape[:2]
    if y0 + h + geo.quiete > H or x0 + w + geo.quiete > W:
        raise ValueError("⛔ la marca non ci sta: serve almeno %dx%d, l'immagine "
                         "e' %dx%d" % (x0 + w + geo.quiete, y0 + h + geo.quiete, W, H))
    img[max(0, y0 - geo.quiete):y0 + h + geo.quiete,
        max(0, x0 - geo.quiete):x0 + w + geo.quiete] = 0
    for i in range(geo.bit):
        if not bit[i]:
            continue
        r, c = divmod(i, geo.colonne)
        img[y0 + r * geo.cella:y0 + (r + 1) * geo.cella,
            x0 + c * geo.cella:x0 + (c + 1) * geo.cella] = 255
    return img


# ───────────────────────────────────────────────────────────────────────────
# ⭐⛔ IL LETTORE
# ───────────────────────────────────────────────────────────────────────────
def _luma(img):
    np = np_o_muori("leggi_marca")
    a = np.asarray(img)
    pesi = np.array(PESI_LUMA, dtype=np.float64)
    if a.ndim == 2:
        return a.astype(np.float64) / 255.0
    if a.ndim == 3 and a.shape[2] >= 3:
        return (a[:, :, :3].astype(np.float64) @ pesi) / 255.0
    raise ValueError("l'immagine non e' ne' grigia ne' a tre canali: %s" % (a.shape,))


def _celle(y, geo, dx, dy):
    """La luminanza media del CENTRO di ciascuna cella, in ordine di bit."""
    x0, y0, _, _ = geo.blocco()
    x0 += dx
    y0 += dy
    np = np_o_muori("leggi_marca")
    c = geo.cella
    dentro = max(2, c // 4)              # si legge il quadrato centrale al 50 %
    val = np.empty(geo.bit, dtype=np.float64)
    for i in range(geo.bit):
        r, k = divmod(i, geo.colonne)
        ya = y0 + r * c + dentro
        xa = x0 + k * c + dentro
        val[i] = y[ya:ya + c - 2 * dentro, xa:xa + c - 2 * dentro].mean()
    return val


def _prova_posizione(y, geo, dx, dy):
    np = np_o_muori("leggi_marca")
    val = _celle(y, geo, dx, dy)
    alto = float(np.percentile(val, 90))
    basso = float(np.percentile(val, 10))
    contrasto = alto - basso
    esito = {"contrasto": round(contrasto, 4), "scorrimento_provato": [dx, dy]}
    if contrasto < CONTRASTO_MINIMO:
        esito["perche"] = ("il contrasto fra le celle e' %.3f, sotto il minimo "
                           "%.2f: qui non c'e' un segnale a due livelli"
                           % (contrasto, CONTRASTO_MINIMO))
        return None, esito
    soglia = (alto + basso) / 2.0
    bit = (val > soglia).astype(np.uint8)

    byte = bytearray(len(bit) // 8)
    for i, b in enumerate(bit):
        if b:
            byte[i >> 3] |= 1 << (7 - (i & 7))
    byte = bytes(byte)

    if byte[0] != SYNC:
        esito["perche"] = ("i primi 8 bit valgono 0x%02X invece del sync 0x%02X"
                           % (byte[0], SYNC))
        return None, esito
    corpo, crc_letto = byte[1:16], struct.unpack(">H", byte[16:18])[0]
    crc_atteso = crc16(corpo)
    if crc_letto != crc_atteso:
        esito["perche"] = ("il sync c'e' ma il CRC non torna: letto 0x%04X, "
                           "calcolato 0x%04X ⇒ la marca c'era e si e' rotta, "
                           "oppure e' un caso" % (crc_letto, crc_atteso))
        return None, esito

    versione = corpo[0]
    giro = struct.unpack(">I", corpo[1:5])[0]
    disegno = struct.unpack(">I", corpo[5:9])[0]
    istante = int.from_bytes(corpo[9:15], "big")
    if versione != VERSIONE:
        # ⛔ Un CRC che torna con una versione che non conosciamo NON e'
        #    «marca assente»: e' una marca di un'altra stesura, e leggerla con
        #    il nostro schema darebbe numeri sbagliati che sembrano giusti.
        esito["perche"] = ("marca della versione %d, questo lettore legge la %d: "
                           "i campi non stanno nello stesso posto e leggerla "
                           "darebbe numeri plausibili e falsi" % (versione, VERSIONE))
        esito["versione_marca"] = versione
        return None, esito

    buono = {"c_e": True, "versione": versione, "giro": giro,
             "disegno": disegno, "istante_us": istante,
             "contrasto": round(contrasto, 4), "soglia": round(soglia, 4),
             "scorrimento_provato": [dx, dy]}
    return buono, esito


def leggi_marca(img, geo=GEOMETRIA, ricerca=RICERCA):
    """⭐ Dato un fotogramma, dice se la marca c'e' e che cosa dice.

    Ritorna un dizionario con SEMPRE la chiave `c_e`:
      c_e = True   → `disegno`, `istante_us`, `giro`, `contrasto`,
                     `scorrimento_provato`
      c_e = False  → `perche` (⛔ mai assente), piu' quel che si e' potuto vedere
    """
    y = _luma(img)
    H, W = y.shape
    x0, y0, w, h = geo.blocco()
    serve_w, serve_h = x0 + w + ricerca, y0 + h + ricerca
    if W < serve_w or H < serve_h:
        return {"c_e": False,
                "perche": ("⛔ non ho potuto GUARDARE: il fotogramma e' %dx%d e il "
                           "blocco della marca finisce a %dx%d.  ⚠ Non e' «la marca "
                           "non c'e'»: e' «la marca non ci starebbe»"
                           % (W, H, serve_w, serve_h)),
                "misura": [W, H], "serve": [serve_w, serve_h]}

    # ⛔ L'ORDINE DELLE POSIZIONE NON E' INDIFFERENTE, e la prima stesura lo
    #    faceva sbagliare — trovato girando, 13 agosto 2026.  Scorrendo da
    #    (−2,−2) in su, un fotogramma PERFETTAMENTE allineato veniva letto bene
    #    ma dichiarava `scorrimento: [-2,-2]`: la cella e' larga 24 px e si
    #    legge al centro, quindi due pixel di scarto passano lo stesso.  Il
    #    carico usciva giusto e il numero accanto era falso — ed e' il tipo di
    #    numero che finisce in un documento come misura.
    # ⇒ si prova (0,0) per primo e poi a raggio crescente: chi dichiara uno
    #   scorrimento lo ha davvero.
    ordine = sorted(
        ((dx, dy) for dy in range(-ricerca, ricerca + 1)
                  for dx in range(-ricerca, ricerca + 1)),
        key=lambda p: (max(abs(p[0]), abs(p[1])), abs(p[0]) + abs(p[1]), p))
    migliore = None
    for dx, dy in ordine:
        if y0 + dy < 0 or x0 + dx < 0:
            continue
        buono, esito = _prova_posizione(y, geo, dx, dy)
        if buono is not None:
            buono["posizioni_provate"] = (2 * ricerca + 1) ** 2
            return buono
        if migliore is None or esito["contrasto"] > migliore["contrasto"]:
            migliore = esito
    fuori = {"c_e": False, "posizioni_provate": (2 * ricerca + 1) ** 2}
    fuori.update(migliore or {"perche": "nessuna posizione provata"})
    fuori["perche"] = ("la marca NON c'e' in nessuno dei %d scorrimenti provati "
                       "(± %d px).  Il migliore diceva: %s"
                       % (fuori["posizioni_provate"], ricerca, fuori.get("perche")))
    return fuori


# ───────────────────────────────────────────────────────────────────────────
# IL CONTEGGIO DEI DISEGNI DEL CLIENT — letto da fuori, dal blocco condiviso.
#
# ⛔ §1.1: «accanto va contato quanto disegna il client: e' il controllo che
#    dice se il tetto e' del compositore o della scena».
# ───────────────────────────────────────────────────────────────────────────
STATO_MAGIA = 0x524D5853
STATO_VERSIONE = 2
# ⛔ Deve corrispondere a `struct stato_condiviso` di `03-scena.c`.  `magia` e
#    `versione` esistono perche' un disallineamento dia un RIFIUTO invece di
#    numeri a caso.
FORMATO_STATO = "<4I Q 5Q 5Q 10I i 3I 64s 32s 64s 64s 4Q 4I"


def leggi_conteggio(nome_shm="remotix-scena"):
    """Ritorna i conti del client, o `{"c_e": False, "perche": …}`."""
    percorso = "/dev/shm/" + nome_shm
    if not os.path.exists(percorso):
        return {"c_e": False,
                "perche": ("⛔ «%s» non esiste: la scena non e' mai partita, "
                           "oppure ha un altro nome (--shm).  ⚠ Non e' «ha "
                           "disegnato zero volte»" % percorso)}
    taglia = struct.calcsize(FORMATO_STATO)
    with open(percorso, "rb") as f:
        with mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ) as m:
            if len(m) < taglia:
                return {"c_e": False,
                        "perche": "«%s» e' %d byte, ne servono %d: la struttura "
                                  "non e' quella" % (percorso, len(m), taglia)}
            # ⛔ Seqlock: si legge due volte e si pretende `seq` pari e uguale.
            #    Senza, si puo' prendere un `disegno` nuovo con un `istante`
            #    vecchio e credere a un ritardo mai esistito.
            # ⛔⭐ IL SEQLOCK, E IL DIFETTO CHE CI STAVA DENTRO — 13 agosto 2026.
            #
            # La prima stesura provava 50 volte **di fila, senza respiro**.  Con
            # una scena sana (60 disegni/s = 120 tocchi di `seq` al secondo) non
            # falliva mai.  Con una scena in CORSA A VUOTO (misurato: 1034
            # disegni/s, piu' altrettanti richiami di presentazione ⇒ oltre
            # 4000 tocchi al secondo) 50 tentativi stretti si perdono la corsa,
            # e il lettore rispondeva *«il blocco non si e' mai fermato»*.
            #
            # ⭐ ED E' LA DIAGNOSI SBAGLIATA: il blocco non e' rotto, e' il
            #   SCRITTORE che sta correndo a vuoto.  Chi leggeva quella frase
            #   andava a cercare un difetto della memoria condivisa — che e'
            #   esattamente dove il difetto NON era.
            #
            # ⇒ due cure, e la seconda vale piu' della prima:
            #   1. si riprova piu' a lungo e con una pausa, cosi' la finestra
            #      fra due scritture si trova;
            #   2. ⛔ se anche cosi' non si trova, si NOMINA il sospetto giusto
            #      invece di accusare il blocco.
            # ⛔⭐⭐ IL SEQLOCK, E LA DIAGNOSI CHE HO SBAGLIATO DUE VOLTE
            #      PRIMA DI MISURARLA — 13 agosto 2026.
            #
            # Il sintomo riportato dallo step 1 era *«il blocco condiviso smette
            # di rispondere»*.  Il coordinatore sospettava contesa del seqlock;
            # io ho sospettato lo stesso e ho allargato i tentativi.  ⛔ **Tutti
            # e due sbagliati, e misurato**: col lettore di prima (50 tentativi
            # stretti, senza pausa) puntato su una scena in corsa a vuoto —
            # 1034 disegni/s, oltre 4000 tocchi di `seq` al secondo — le letture
            # riuscite sono state **200 su 200**.  La contesa non c'entra.
            #
            # ⭐ LA CAUSA VERA, e si riproduce ogni volta invece che a caso:
            #   un blocco lasciato da una scena morta **a meta' scrittura** ha
            #   `seq` **DISPARI PER SEMPRE**.  Nessun numero di tentativi lo
            #   trovera' mai pari: il lettore vecchio falliva **3 volte su 3**,
            #   e non «ogni tanto».
            #
            # ⭐⭐ E LE DUE COSE SONO LO STESSO DIFETTO, per una strada che
            #   nessuno dei due aveva visto: una scena in corsa a vuoto **non
            #   torna piu' al ciclo principale**, quindi ignora `--secondi`
            #   (misurato: 6 s chiesti, 146 s vissuti) ⇒ il banco la **uccide**
            #   ⇒ la morte cade a meta' scrittura ⇒ `seq` resta dispari.
            #   **Una causa sola, due sintomi, cuciti dal colpo che la ferma.**
            #
            # ⇒ da cui i tre esiti che questo ciclo deve saper distinguere, e
            #   che mandano a cercare in tre posti diversi:
            #     · `seq` pari e stabile           → si legge
            #     · `seq` NON e' mai cambiato ed e' dispari → lo scrittore e'
            #       morto o fermo con la scrittura aperta.  ⛔ NON e' «troppo
            #       veloce»: e' un relitto
            #     · `seq` cambia in continuazione ma non si azzecca mai pari →
            #       quello si' sarebbe contesa (mai osservato)
            campioni = 0
            primo_seq = struct.unpack(FORMATO_STATO, m[:taglia])[4]
            ultimo_seq = primo_seq
            coerente = None
            for _ in range(400):
                a = struct.unpack(FORMATO_STATO, m[:taglia])
                campioni += 1
                ultimo_seq = a[4]
                if a[4] % 2 == 0:
                    b = struct.unpack(FORMATO_STATO, m[:taglia])
                    if b[4] == a[4]:
                        coerente = a
                        break
                time.sleep(0.0002)
            if coerente is None:
                fermo = (ultimo_seq == primo_seq)
                pid_relitto = struct.unpack(FORMATO_STATO, m[:taglia])[25]
                vivo_relitto = os.path.exists("/proc/%d" % pid_relitto)
                if fermo:
                    perche = (
                        "⛔ «%s» e' un RELITTO: `seq` vale %d — dispari — e NON "
                        "e' cambiato in %d tentativi.  Una scrittura e' rimasta "
                        "aperta, cioe' la scena e' morta (o e' ferma) a meta'.  "
                        "⚠ Il processo %d %s.  ⛔ Nessun numero di tentativi lo "
                        "trovera' mai pari: non si aspetta, si riparte la scena "
                        "(il blocco si riazzera all'avvio)."
                        % (percorso, ultimo_seq, campioni, pid_relitto,
                           "e' ancora vivo — allora e' BLOCCATO, non morto"
                           if vivo_relitto else "non esiste piu'"))
                else:
                    perche = (
                        "⛔ `seq` cambia (%d → %d in %d tentativi) e non l'ho "
                        "mai preso pari: questa si' e' contesa.  ⚠ Non e' mai "
                        "stata osservata nemmeno con una scena a 1034 "
                        "disegni/s — se la vedi, riportala."
                        % (primo_seq, ultimo_seq, campioni))
                return {"c_e": False, "fidato": False, "campioni": campioni,
                        "seq": int(ultimo_seq), "relitto": bool(fermo),
                        "perche": perche}
            a = coerente
    (magia, versione, dim, _r0, seq,
     disegni, commit, presentati, attese, scarti,
     avvio_mono, avvio_reale, ultimo_disegno, ultimo_pres, ultimo_pres_reale,
     giro_numero, larghezza, altezza, cella, colonne, righe, margine, quiete,
     movimento, danno, pid, pres_disp, schermo_intero, _r1,
     nome_giro, versione_scena, uscita_confermata, uscita_chiesta,
     rientri, corse_a_vuoto, disegni_senza_callback, saltati_senza_buffer,
     callback_in_volo, callback_in_volo_massimo, refresh_mhz, fidato) = a

    if magia != STATO_MAGIA:
        return {"c_e": False,
                "perche": "«%s» non e' un blocco di 03-scena (magia 0x%08X)"
                          % (percorso, magia)}
    if versione != STATO_VERSIONE:
        return {"c_e": False,
                "perche": ("⛔ blocco di versione %d, questo lettore legge la %d: "
                           "i campi non stanno nello stesso posto"
                           % (versione, STATO_VERSIONE))}
    vivo = os.path.exists("/proc/%d" % pid)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⭐ IL VERDETTO SUL NUMERO, NON SOLO IL NUMERO.
    #
    # Chiesto dal coordinatore il 13 agosto 2026: *«un conto di 540/s su un
    # monitor a 60 Hz e' un fatto osservabile: va ACCUSATO, non consegnato.
    # Finche' non c'e' quel rilevatore, ogni cella misurata con la tua scena da
    # un banco d'altri e' `[?]`, non `[M]`.»*
    #
    # ⇒ `leggi_conteggio()` non restituisce piu' soltanto dei conti: restituisce
    #   `fidato` e, quando e' falso, **l'elenco delle ragioni**.  Un banco che
    #   legge questi numeri e non guarda `fidato` sta facendo apposta quel che
    #   §2.2 vieta.
    #
    # ⚠ E le ragioni sono di DUE specie, tenute separate:
    #     · quelle che la scena ha misurato su sé stessa (rientri, callback in
    #       volo) — sono cause, e valgono a qualunque frequenza;
    #     · quelle che il lettore calcola da fuori (ritmo contro refresh, blocco
    #       stantio, scrittore morto) — sono sintomi, e servono a prendere i
    #       casi in cui la scena non ha potuto accorgersene da sé (per esempio
    #       una scena uccisa a meta').
    # ═══════════════════════════════════════════════════════════════════════
    perche = []
    if rientri:
        perche.append("⛔ %d RIENTRI: `disegna()` e' stata chiamata dentro sé "
                      "stessa — un gestore di eventi ha disegnato" % rientri)
    if callback_in_volo_massimo > 1:
        perche.append("⛔ fino a %d `wl_surface.frame` IN VOLO insieme (ne e' "
                      "ammesso 1): la scena disegna senza essere invitata, e "
                      "il ritmo si moltiplica per quel numero"
                      % callback_in_volo_massimo)
    if corse_a_vuoto:
        perche.append("⛔ %d giri di CORSA A VUOTO" % corse_a_vuoto)

    # il ritmo medio dall'avvio, contro il refresh dichiarato dall'uscita
    ritmo = None
    durata = (ultimo_disegno - avvio_mono) / 1e6 if ultimo_disegno > avvio_mono else 0
    if durata > 0.5:
        ritmo = disegni / durata
        if refresh_mhz > 0 and ritmo > 1.5 * (refresh_mhz / 1000.0):
            perche.append("⛔ %.0f disegni/s su un monitor a %.1f Hz: piu' di "
                          "una volta e mezza il refresh non e' un ritmo, e' "
                          "una corsa a vuoto"
                          % (ritmo, refresh_mhz / 1000.0))
    if not vivo:
        # ⚠ NON e' «i numeri sono sbagliati»: sono l'ULTIMA fotografia di una
        #   scena che non c'e' piu'.  Consegnarli come correnti sarebbe la
        #   misura di ieri spacciata per quella di oggi.
        perche.append("⚠ il processo %d che ha scritto questo blocco NON e' "
                      "piu' vivo: questi sono i suoi ultimi numeri, non i "
                      "numeri di adesso" % pid)

    return {
        "c_e": True, "vivo": vivo, "pid": int(pid), "seq": int(seq),
        # ⭐ il verdetto, e viene PRIMA dei numeri perche' li governa
        "fidato": (not perche),
        "perche_non_fidato": perche,
        "rientri": int(rientri), "corse_a_vuoto": int(corse_a_vuoto),
        "disegni_senza_callback": int(disegni_senza_callback),
        "saltati_senza_buffer": int(saltati_senza_buffer),
        "callback_in_volo": int(callback_in_volo),
        "callback_in_volo_massimo": int(callback_in_volo_massimo),
        "refresh_hz": (refresh_mhz / 1000.0) if refresh_mhz else None,
        "disegni_al_secondo": round(ritmo, 2) if ritmo is not None else None,
        "disegni": int(disegni), "commit": int(commit),
        "presentati": int(presentati), "attese": int(attese),
        "scarti_presentazione": int(scarti),
        # ⛔ Il campo che distingue «zero presentati» da «presentati non
        #    misurabili su questo compositore» (`LEZIONI.md` §1.9).
        "presentazione_disponibile": bool(pres_disp),
        "avvio_monotonico_us": int(avvio_mono), "avvio_reale_us": int(avvio_reale),
        "ultimo_disegno_us": int(ultimo_disegno),
        "ultimo_presentato_us": int(ultimo_pres),
        "ultimo_presentato_reale_us": int(ultimo_pres_reale),
        "giro": nome_giro.split(b"\0")[0].decode("utf-8", "replace"),
        "giro_numero": int(giro_numero),
        "larghezza": int(larghezza), "altezza": int(altezza),
        "cella": int(cella), "colonne": int(colonne), "righe": int(righe),
        "margine": int(margine), "quiete": int(quiete),
        "movimento": ["marca", "barra", "pieno"][int(movimento)] if movimento < 3 else int(movimento),
        "danno": ["preciso", "pieno"][int(danno)] if danno < 2 else int(danno),
        "schermo_intero": bool(schermo_intero),
        "versione_scena": versione_scena.split(b"\0")[0].decode("utf-8", "replace"),
        # ⛔ «chiesta» e' la nostra intenzione; «confermata» e' quel che il
        #    COMPOSITORE ha detto con `wl_surface.enter`.  Vuota NON vuol dire
        #    «su nessuna»: vuol dire «nessun enter ancora arrivato», e i due
        #    casi mandano a cercare in due posti diversi (`LEZIONI.md` §1.9).
        "uscita_chiesta": uscita_chiesta.split(b"\0")[0].decode("utf-8", "replace") or None,
        "uscita_confermata": (uscita_confermata.split(b"\0")[0]
                              .decode("utf-8", "replace") or None),
    }


# ───────────────────────────────────────────────────────────────────────────
def carica(percorso, larghezza=None, altezza=None):
    """.rgb24 grezzo (vuole le misure), .png / .ppm via Pillow."""
    est = os.path.splitext(percorso)[1].lower()
    if est in (".rgb24", ".rgb", ".raw"):
        if not larghezza or not altezza:
            raise SystemExit("⛔ «%s» e' grezzo: senza --larghezza e --altezza non "
                             "so che forma abbia, e indovinarla vorrebbe dire "
                             "leggere la marca nel posto sbagliato" % percorso)
        dati = open(percorso, "rb").read()
        atteso = larghezza * altezza * 3
        if len(dati) < atteso:
            raise SystemExit("⛔ «%s»: %d byte, ne servivano %d per %dx%d rgb24"
                             % (percorso, len(dati), atteso, larghezza, altezza))
        np = np_o_muori("carica")
        return np.frombuffer(dati[:atteso], np.uint8).reshape(altezza, larghezza, 3)
    np = np_o_muori("carica")
    from PIL import Image
    return np.asarray(Image.open(percorso).convert("RGB"))


def main():
    p = argparse.ArgumentParser(description="il lettore della marca della scena")
    s = p.add_subparsers(dest="che", required=True)

    q = s.add_parser("leggi", help="dato un fotogramma, dice se la marca c'e'")
    q.add_argument("file")
    q.add_argument("--larghezza", type=int)
    q.add_argument("--altezza", type=int)
    q.add_argument("--cella", type=int, default=CELLA)
    q.add_argument("--margine", type=int, default=MARGINE)
    q.add_argument("--quiete", type=int, default=QUIETE)
    q.add_argument("--ricerca", type=int, default=RICERCA)

    d = s.add_parser("dipingi", help="⚠ solo per il controllo positivo")
    d.add_argument("file")
    d.add_argument("--larghezza", type=int, default=1280)
    d.add_argument("--altezza", type=int, default=720)
    d.add_argument("--disegno", type=int, required=True)
    d.add_argument("--istante-us", type=int, required=True)
    d.add_argument("--giro", default="senza-nome")
    d.add_argument("--cella", type=int, default=CELLA)
    d.add_argument("--fondo", default="grigio", choices=("grigio", "nero", "rumore"))

    c = s.add_parser("conta", help="i disegni del client, letti da fuori")
    c.add_argument("--shm", default="remotix-scena")

    n = s.add_parser("nome", help="il numero a 32 bit di un nome di giro")
    n.add_argument("giro")

    # ⭐⛔ LA RIAPERTURA DEL CONTROLLO `giro` DI M8.
    #
    # `fasi/rapporti/F2-6-giudizio.md`, 13 agosto 2026: il controllo `giro` di
    # M8 e' **NON APPLICABILE per costruzione**, perche' *«e' il nome del giro
    # DEL BANCO, il prodotto non lo conosce e il protocollo non ha un campo per
    # dirglielo»*.
    #
    # ⇒ Con la marca il nome del giro viaggia **dentro i pixel**: il banco lo
    #   dipinge nella scena, il prodotto lo trasporta senza saperlo, e il banco
    #   se lo rilegge dal fotogramma dipinto.  ⭐ E' meglio del controllo che
    #   M8 non poteva fare, perche' non chiede niente all'imputato: glielo
    #   LEGGE ADDOSSO.
    #
    # ⛔ E l'inversione e' un ELENCO, non un'indovinata: la marca porta 32 bit
    #   di FNV-1a, che non si invertono.  Chi chiama dichiara i giri che ha
    #   fatto girare; se il numero letto non e' nessuno di quelli, si scrive il
    #   numero grezzo — e M8 diventa rosso, che e' l'esito giusto.
    # ⛔ E se la marca NON c'e', `giro` esce **null**: M8 dichiara il controllo
    #   NON ESEGUITO.  Scriverci dentro il giro in corso sarebbe la costante
    #   che faceva passare, cioe' il falso verde del 13 agosto.
    idn = s.add_parser("identita",
                       help="⭐ costruisce l'--identita-pagina di M8 leggendo il "
                            "giro DAI PIXEL")
    idn.add_argument("file")
    idn.add_argument("--larghezza", type=int)
    idn.add_argument("--altezza", type=int)
    idn.add_argument("--giri", required=True,
                     help="i nomi dei giri noti, separati da virgola: e' "
                          "l'elenco con cui si inverte il numero della marca")
    idn.add_argument("--fuori", required=True)
    idn.add_argument("--dipinto-dopo-reset", choices=("si", "no"),
                     help="⚠ se non lo dichiari, M8 NON finge di averlo guardato")
    idn.add_argument("--fin-ricevuto", choices=("si", "no"))
    idn.add_argument("--dipinto", choices=("si", "no"))
    idn.add_argument("--conti", help="il JSON dei conti della pagina")

    a = p.parse_args()

    if a.che == "leggi":
        geo = MarcaGeometria(a.cella, a.margine, a.quiete)
        img = carica(a.file, a.larghezza, a.altezza)
        r = leggi_marca(img, geo, a.ricerca)
        r["file"] = a.file
        r["impronta"] = hashlib.sha256(open(a.file, "rb").read()).hexdigest()[:16]
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["c_e"] else 1

    if a.che == "dipingi":
        np = np_o_muori("dipingi")
        if a.fondo == "nero":
            img = np.zeros((a.altezza, a.larghezza, 3), np.uint8)
        elif a.fondo == "rumore":
            img = np.random.RandomState(7).randint(0, 256, (a.altezza, a.larghezza, 3),
                                                   dtype=np.uint8)
        else:
            yy = np.linspace(0, 1, a.altezza)[:, None]
            xx = np.linspace(0, 1, a.larghezza)[None, :]
            f = ((yy + xx) / 2 * 200 + 30).astype(np.uint8)
            img = np.repeat(f[:, :, None], 3, axis=2)
        dipingi_marca(img, a.disegno, a.istante_us, fnv1a32(a.giro),
                      MarcaGeometria(a.cella))
        est = os.path.splitext(a.file)[1].lower()
        if est in (".rgb24", ".rgb", ".raw"):
            img.tofile(a.file)
        else:
            from PIL import Image
            Image.fromarray(img).save(a.file)
        print(json.dumps({"file": a.file, "disegno": a.disegno,
                          "istante_us": a.istante_us, "giro": a.giro,
                          "giro_numero": fnv1a32(a.giro)}, ensure_ascii=False))
        return 0

    if a.che == "conta":
        r = leggi_conteggio(a.shm)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        # ⛔⭐ LO STATO D'USCITA PORTA IL VERDETTO, non solo la leggibilita'.
        #    0 = numeri leggibili E fidati · 1 = non leggibile · ⭐ 2 = leggibili
        #    ma NON FIDATI.  Uno script che facesse `conta | jq .disegni` senza
        #    guardare `fidato` prenderebbe lo stesso un numero: con il 2, `set -e`
        #    lo ferma.  ⚠ Tre stati e non due, perche' «non ho potuto leggere» e
        #    «ho letto ma non ci credo» mandano a cercare in due posti diversi.
        if not r.get("c_e"):
            return 1
        return 0 if r.get("fidato") else 2

    if a.che == "nome":
        print(json.dumps({"giro": a.giro, "numero": fnv1a32(a.giro)}))
        return 0

    if a.che == "identita":
        img = carica(a.file, a.larghezza, a.altezza)
        r = leggi_marca(img)
        noti = {fnv1a32(g.strip()): g.strip() for g in a.giri.split(",") if g.strip()}
        d = {"da": "03-marca.py identita",
             "sorgente": os.path.abspath(a.file),
             "come": ("⭐ il giro e' LETTO DAI PIXEL del fotogramma dipinto, non "
                      "dichiarato dal prodotto: la marca lo porta dentro la "
                      "scena e il prodotto la trasporta senza saperlo"),
             "giri_noti": {str(k): v for k, v in noti.items()}}
        if not r["c_e"]:
            # ⛔ Marca assente ⇒ `giro: None`.  M8 dichiara il controllo NON
            #    ESEGUITO invece di darlo per passato.
            d["giro"] = None
            d["marca"] = {"c_e": False, "perche": r.get("perche")}
            d["non_applicabile"] = {
                "giro": ("⛔ la marca NON e' nei pixel del fotogramma dipinto: "
                         "%s.  ⚠ Qui non si indovina il giro in corso — sarebbe "
                         "la costante che fa passare" % (r.get("perche") or "")[:160])}
        else:
            d["marca"] = {"c_e": True, "disegno": r["disegno"],
                          "istante_us": r["istante_us"], "giro_numero": r["giro"],
                          "contrasto": r["contrasto"]}
            d["giro"] = noti.get(r["giro"], "numero-ignoto-0x%08X" % r["giro"])
            d["disegno"] = r["disegno"]
            d["istante_us"] = r["istante_us"]
        for chiave, valore in (("dipinto_dopo_reset", a.dipinto_dopo_reset),
                               ("fin_ricevuto", a.fin_ricevuto),
                               ("dipinto", a.dipinto)):
            if valore is not None:
                d[chiave] = (valore == "si")
        if a.conti:
            d["conti"] = json.load(open(a.conti))
        with open(a.fuori, "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        print(json.dumps({"fuori": a.fuori, "giro": d["giro"],
                          "disegno": d.get("disegno")}, ensure_ascii=False))
        return 0 if r["c_e"] else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
