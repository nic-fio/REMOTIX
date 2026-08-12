#!/usr/bin/env python3
"""02-codifica-immagine.py — l'immagine nota di F2.3, e gli strumenti che la giudicano.

    python3 02-codifica-immagine.py --genera <cartella>
    python3 02-codifica-immagine.py --livelli <file.yuv> [--riga N]
    python3 02-codifica-immagine.py --confronta <a.yuv> <b.yuv>
    python3 02-codifica-immagine.py --autoprova <cartella>   ⛔ il controllo positivo

===========================================================================
⛔ PERCHE' ESISTE — e non e' «serviva un'immagine di prova»

La sotto-fase F2.3 deve dimostrare che dal fotogramma catturato esce un flusso
HEVC **Main10** che un browser sa decodificare.  ⚠ E la trappola vera dei 10
bit e' che **nessuno se ne accorge guardando i pixel**:

  ⛔ *se il codificatore accetta 10 bit ma la catena gliene consegna 8, il
     fotogramma decodificato viene BENE lo stesso.*  Le strisce sulle sfumature
     ci sono, ma sono le stesse strisce che un occhio attribuirebbe al bitrate.

E' esattamente la forma **E1** di `REVIEWER.md` §2 — necessario scambiato per
sufficiente — applicata al colore: «`ffprobe` dice Main 10» e' **necessario**
perche' i 10 bit ci siano, e non e' affatto **sufficiente**.  Un'etichetta la
scrive il codificatore leggendo i propri argomenti; i **valori dei pixel** no.

⭐ Da cui l'immagine che questo file genera non e' decorativa: e' costruita
   perche' un solo numero, letto sui pixel decodificati, distingua
   **«10 bit veri»** da **«10 bit dichiarati»**.

===========================================================================
⛔ IL NUMERO CHE DISTINGUE, E IL CASO OPPOSTO SCRITTO PRIMA

`LEZIONI.md` §1.11 regola 1: *per ogni prova indiretta si scrive cosa
mostrerebbe il caso opposto.  Se non si sa dire come apparirebbe il contrario,
la prova non distingue e va cambiata.*

La **rampa** occupa le prime 256 righe: la luminanza sale di **esattamente 1
LSB a 10 bit** ogni volta che l'ascissa avanza abbastanza, da 64 a 940 (i due
estremi del range limitato a 10 bit).  Su 1920 colonne si toccano **tutti e 877
i livelli interi**, nessuno escluso.

    | grandezza, letta sulla riga 128 del piano Y | 10 bit veri | 8 bit travestiti |
    |---|---|---|
    | livelli distinti                            | **877**     | **220**          |
    | frazione di valori multipli di 4            | **~0,251**  | **1,000**        |

⭐ Il perche' della seconda riga: un campione a 8 bit promosso a 10 vale
   `v << 2`, cioe' e' **sempre** un multiplo di 4.  Su una rampa a 10 bit veri i
   multipli di 4 capitano invece per caso, uno ogni quattro.  ⛔ **1,000 contro
   0,251 non e' una sfumatura: e' un interruttore**, e non ha bisogno di un
   occhio per essere letto.

⚠ E il caso opposto non e' un ragionamento: questo file lo **produce**.
`sorgente-8in10.yuv` e' la stessa identica immagine passata per 8 bit e
rimessa in un contenitore a 10 (`(v >> 2) << 2`).  Se il banco non sa
distinguere quel file dal vero, il banco **non sta misurando i 10 bit** — e
allora il verde di tutto il giro non vale niente (`REVIEWER.md` §1 punto 3).

===========================================================================
⛔ PERCHE' LA PROVA DEI BIT SI FA IN LOSSLESS, E NON AL BITRATE VERO

A un bitrate realistico HEVC **distrugge una rampa a 1 LSB** per costruzione:
e' l'ultimo bit di un dettaglio che nessuno vede, ed e' il primo che il
quantizzatore butta.  Un banco che misurasse i livelli distinti a CRF 20
troverebbe pochi livelli **anche su una catena a 10 bit perfetta**, e il rosso
non distinguerebbe *«la catena e' a 8 bit»* da *«il bitrate era basso»* — due
diagnosi opposte sotto la stessa etichetta, cioe' **E2**.

⇒ Due giri, dichiarati e separati:

  **giro A — la catena** (`lossless=1`): deve tornare **identica byte per
  byte**.  Qui i 10 bit si misurano senza ambiguita', perche' non c'e' nessuna
  perdita a cui dare la colpa.
  **giro B — la resa** (CRF vero): qui si misura *quanto* si perde.  Le strisce
  che si vedono qui sono del bitrate, non della profondita', ed e' il giro A a
  permettere di dirlo.

===========================================================================
CHE COSA C'E' NELL'IMMAGINE, E CHE DIFETTO SMASCHERA CIASCUN PEZZO

    righe    0- 255  ⭐ la rampa a 1 LSB, grigia          → i 10 bit, e le strisce
    righe  256- 511  sfumature morbide a colori           → le strisce, per l'occhio
    righe  512- 767  ⭐ testo rosso saturo su blu saturo   → il testo sfrangiato (4:2:0)
    righe  768-1023  scacchiere e barre da 1, 2, 3 px     → il taglio del croma
    righe 1024-1079  toppe piatte di riferimento          → il rumore su fondo fermo

⚠ Il testo e' disegnato con un font 5x7 **scritto qui dentro**, non preso dal
  sistema: un font di sistema e' una dipendenza che cambia da macchina a
  macchina, e due giri con due font diversi non si confrontano.

⚠ **E la sfrangiatura del testo NON e' colpa del codificatore.** Nasce prima,
  quando il croma a piena risoluzione viene ridotto a 4:2:0 — che e' la scelta
  di `DECISIONI.md` §2.3.  Il giro A lossless serve anche a questo: dimostra
  che il codificatore e' **trasparente**, e quindi che tutto lo sfrangiamento
  misurato e' il prezzo del 4:2:0.  ⭐ E' un numero regalato a chi un giorno
  riaprira' la `[?]` del 4:4:4.

===========================================================================
IL COLORE, DICHIARATO

BT.709, **range limitato**, 10 bit: Y in [64, 940], croma in [64, 960] attorno
a 512.  Non e' un dettaglio: chi confronta i pixel deve sapere quale sia il
nero, o `LEZIONI.md` §1.9 diventa «il banco ha misurato un'altra cosa».
"""

import argparse
import json
import os
import sys

# ── La geometria, dichiarata una volta sola ────────────────────────────────
LARGHEZZA = 1920
ALTEZZA = 1080

# Le fasce, in righe.  Sono estremi INCLUSIVI a sinistra ed ESCLUSIVI a destra.
FASCIA_RAMPA = (0, 256)
FASCIA_SFUMATURE = (256, 512)
FASCIA_TESTO = (512, 768)
FASCIA_FINE = (768, 1024)
FASCIA_TOPPE = (1024, 1080)

# ⛔ La riga su cui si legge la prova dei 10 bit.  E' dentro la rampa, ed e'
#    dichiarata qui perche' il banco e il rapporto devono citare LA STESSA.
RIGA_RAMPA = 128

# Il range limitato a 10 bit.
Y_MIN, Y_MAX = 64, 940
CROMA_ZERO = 512

# Gli attesi, scritti PRIMA del giro (PIANO.md §0.3 regola 4).
ATTESO_LIVELLI_VERI = 877          # 940 - 64 + 1
ATTESO_LIVELLI_8IN10 = 220         # da 64 a 940 di 4 in 4
ATTESO_M4_8IN10 = 1.0
SOGLIA_M4_VERI = 0.50              # ⛔ sopra questa soglia si grida «8 bit travestiti»


# ── Il font 5x7, scritto qui perche' non cambi da una macchina all'altra ───
FONT = {
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#..#", "..##."),
    ":": (".....", "..#..", "..#..", ".....", "..#..", "..#..", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}
FRASE = "REMOTIX 10 bit 4:2:0"


def rgb_a_ycbcr(r, g, b):
    """BT.709, range limitato, 10 bit.  r/g/b in [0,1].  Restituisce interi."""
    yf = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cb = (b - yf) / 1.8556
    cr = (r - yf) / 1.5748
    y = int(round(64 + 876 * yf))
    u = int(round(CROMA_ZERO + 896 * cb))
    v = int(round(CROMA_ZERO + 896 * cr))
    limita = lambda x: max(4, min(1019, x))
    return limita(y), limita(u), limita(v)


def costruisci():
    """L'immagine, in tre piani a piena risoluzione (il croma si sottocampiona dopo).

    Si lavora a 4:4:4 e si riduce a 4:2:0 in fondo, con la media del blocco 2x2.
    ⚠ E' quella media a produrre la sfrangiatura del testo: la si fa qui, in
      chiaro, invece di lasciarla fare a uno strumento — cosi' chi legge sa
      esattamente dove nasce il difetto che poi misura.
    """
    Y = [[0] * LARGHEZZA for _ in range(ALTEZZA)]
    U = [[CROMA_ZERO] * LARGHEZZA for _ in range(ALTEZZA)]
    V = [[CROMA_ZERO] * LARGHEZZA for _ in range(ALTEZZA)]

    # ── la rampa a 1 LSB ───────────────────────────────────────────────────
    riga_rampa = [Y_MIN + (c * (Y_MAX - Y_MIN)) // (LARGHEZZA - 1)
                  for c in range(LARGHEZZA)]
    for r in range(*FASCIA_RAMPA):
        Y[r] = list(riga_rampa)

    # ── sfumature morbide a colori: blu → ciano, e verde → giallo ──────────
    a, b_ = FASCIA_SFUMATURE
    meta = (a + b_) // 2
    for r in range(a, b_):
        verso_giallo = r >= meta
        for c in range(LARGHEZZA):
            t = c / (LARGHEZZA - 1)
            if verso_giallo:
                y, u, v = rgb_a_ycbcr(t * 0.85, 0.85, 0.05)
            else:
                y, u, v = rgb_a_ycbcr(0.05, t * 0.85, 0.85)
            Y[r][c], U[r][c], V[r][c] = y, u, v

    # ── il testo: rosso saturo su blu saturo, a tre ingrandimenti ──────────
    a, b_ = FASCIA_TESTO
    fondo = rgb_a_ycbcr(0.05, 0.05, 0.90)
    inchiostro = rgb_a_ycbcr(0.90, 0.06, 0.06)
    for r in range(a, b_):
        for c in range(LARGHEZZA):
            Y[r][c], U[r][c], V[r][c] = fondo
    riga = a + 8
    for scala in (1, 2, 3, 4):
        disegna_frase(Y, U, V, FRASE, 8, riga, scala, inchiostro)
        riga += 7 * scala + 10

    # ── il dettaglio fine: scacchiere e barre da 1, 2, 3 px ───────────────
    a, b_ = FASCIA_FINE
    nero = rgb_a_ycbcr(0.02, 0.02, 0.02)
    bianco = rgb_a_ycbcr(0.95, 0.95, 0.95)
    rosso = rgb_a_ycbcr(0.90, 0.05, 0.05)
    blu = rgb_a_ycbcr(0.05, 0.05, 0.90)
    quarto = (b_ - a) // 4
    for r in range(a, b_):
        i = (r - a) // quarto
        for c in range(LARGHEZZA):
            if i == 0:                       # scacchiera 1px bianco/nero
                p = bianco if (r + c) % 2 == 0 else nero
            elif i == 1:                     # scacchiera 1px rosso/blu ⭐
                p = rosso if (r + c) % 2 == 0 else blu
            elif i == 2:                     # barre verticali 1,2,3 px
                per = 12
                x = c % per
                p = rosso if x in (0, 2, 3, 5, 6, 7) else blu
            else:                            # barre orizzontali 1,2,3 px
                per = 12
                x = (r - a) % per
                p = bianco if x in (0, 2, 3, 5, 6, 7) else nero
            Y[r][c], U[r][c], V[r][c] = p

    # ── le toppe piatte di riferimento ────────────────────────────────────
    a, b_ = FASCIA_TOPPE
    toppe = [rgb_a_ycbcr(x, x, x) for x in (0.0, 0.18, 0.5, 0.75, 1.0)]
    largo = LARGHEZZA // len(toppe)
    for r in range(a, b_):
        for c in range(LARGHEZZA):
            Y[r][c], U[r][c], V[r][c] = toppe[min(c // largo, len(toppe) - 1)]

    return Y, U, V


def disegna_frase(Y, U, V, frase, x0, y0, scala, colore):
    for k, ch in enumerate(frase):
        g = FONT.get(ch)
        if g is None:
            continue
        bx = x0 + k * 6 * scala
        for gy in range(7):
            for gx in range(5):
                if g[gy][gx] != "#":
                    continue
                for dy in range(scala):
                    for dx in range(scala):
                        y, x = y0 + gy * scala + dy, bx + gx * scala + dx
                        if 0 <= y < ALTEZZA and 0 <= x < LARGHEZZA:
                            Y[y][x], U[y][x], V[y][x] = colore


def sottocampiona(P):
    """4:4:4 → 4:2:0 con la media del blocco 2x2.  ⚠ Qui nasce lo sfrangiamento."""
    fuori = []
    for r in range(0, ALTEZZA, 2):
        riga = []
        for c in range(0, LARGHEZZA, 2):
            riga.append((P[r][c] + P[r][c + 1] + P[r + 1][c] + P[r + 1][c + 1] + 2) // 4)
        fuori.append(riga)
    return fuori


def in_byte(piano):
    b = bytearray()
    for riga in piano:
        for v in riga:
            b += int(v).to_bytes(2, "little")
    return bytes(b)


def scrivi_yuv(percorso, Y, U, V):
    with open(percorso, "wb") as f:
        f.write(in_byte(Y))
        f.write(in_byte(U))
        f.write(in_byte(V))


def a_8_bit(dati):
    """(v >> 2) << 2 su ogni campione a 16 bit little endian.

    ⛔ E' il CASO OPPOSTO, prodotto e non ragionato: la stessa immagine passata
       da 8 bit e rimessa in un contenitore a 10.  Un occhio non la distingue.
    """
    fuori = bytearray(dati)
    for i in range(0, len(fuori), 2):
        v = fuori[i] | (fuori[i + 1] << 8)
        v = (v >> 2) << 2
        fuori[i] = v & 0xFF
        fuori[i + 1] = (v >> 8) & 0xFF
    return bytes(fuori)


# ── Gli strumenti di giudizio ──────────────────────────────────────────────

def leggi_riga_y(percorso, riga):
    """La riga `riga` del piano Y.  ⛔ Controlla la DIMENSIONE del file prima.

    Un file corto letto con `seek` non da' errore: da' byte di un'altra riga, o
    niente.  «Vuoto» e «proibito» hanno lo stesso aspetto (`LEZIONI.md` §1.9).
    """
    atteso = LARGHEZZA * ALTEZZA * 2 + 2 * (LARGHEZZA // 2) * (ALTEZZA // 2) * 2
    vero = os.path.getsize(percorso)
    if vero != atteso:
        raise SystemExit(
            f"⛔ {percorso} misura {vero} byte e ne doveva misurare {atteso}: "
            f"non e' un fotogramma yuv420p10le {LARGHEZZA}x{ALTEZZA}")
    with open(percorso, "rb") as f:
        f.seek(riga * LARGHEZZA * 2)
        crudo = f.read(LARGHEZZA * 2)
    if len(crudo) != LARGHEZZA * 2:
        raise SystemExit(f"⛔ lettura corta su {percorso}: {len(crudo)} byte")
    return [crudo[i] | (crudo[i + 1] << 8) for i in range(0, len(crudo), 2)]


def misura_bit(percorso, riga):
    valori = leggi_riga_y(percorso, riga)
    livelli = len(set(valori))
    m4 = sum(1 for v in valori if v % 4 == 0) / len(valori)
    verdetto = "8-bit-travestiti" if m4 > SOGLIA_M4_VERI else "10-bit-veri"
    return {
        "file": os.path.basename(percorso), "riga": riga,
        "livelli_distinti": livelli, "frazione_multipli_4": round(m4, 4),
        "minimo": min(valori), "massimo": max(valori), "verdetto": verdetto,
    }


def confronta(a, b):
    """Il confronto sui PIXEL, piano per piano.  Non «i file sono uguali»: dove."""
    da, db = open(a, "rb").read(), open(b, "rb").read()
    if len(da) != len(db):
        return {"confrontabili": False, "byte_a": len(da), "byte_b": len(db),
                "identici": False}
    ny = LARGHEZZA * ALTEZZA * 2
    nc = (LARGHEZZA // 2) * (ALTEZZA // 2) * 2
    tagli = {"Y": (0, ny), "U": (ny, ny + nc), "V": (ny + nc, ny + 2 * nc)}
    esito = {"confrontabili": True, "byte_totali": len(da), "identici": da == db}
    for nome, (i0, i1) in tagli.items():
        pa, pb = da[i0:i1], db[i0:i1]
        diversi = 0
        massimo = 0
        somma2 = 0
        for i in range(0, len(pa), 2):
            va = pa[i] | (pa[i + 1] << 8)
            vb = pb[i] | (pb[i + 1] << 8)
            d = abs(va - vb)
            if d:
                diversi += 1
                if d > massimo:
                    massimo = d
            somma2 += d * d
        n = len(pa) // 2
        esito[nome] = {"campioni": n, "campioni_diversi": diversi,
                       "differenza_massima": massimo,
                       "errore_quadratico_medio": round(somma2 / n, 4)}
    return esito


# ── ⛔ Il controllo positivo degli strumenti stessi ────────────────────────

def autoprova(cartella):
    """«Questo strumento sa trovare qualcosa che c'e' di sicuro?» (`CODER.md` §3.10)

    Tre domande, e sono le tre in cui uno strumento di misura mente in silenzio:

      1. il **comparatore** sa dire DIVERSE?  Gli si da' il sorgente e una copia
         con **un solo byte girato**.  Un comparatore che rispondesse «uguali»
         renderebbe verde ogni giro futuro, per sempre;
      2. il **misuratore dei bit** sa dire «10 bit veri» sul file vero?
      3. ⛔ e sa dire «8 bit travestiti» sul caso opposto?  E' la meta' che si
         dimentica: uno strumento che dice sempre «10 bit» passerebbe la 2 e
         non misurerebbe niente.
    """
    vero = os.path.join(cartella, "sorgente-10bit.yuv")
    finto = os.path.join(cartella, "sorgente-8in10.yuv")
    for p in (vero, finto):
        if not os.path.exists(p):
            raise SystemExit(f"⛔ manca {p}: si genera prima, con --genera")

    guasti = []

    # 1 — il comparatore
    graffiato = os.path.join(cartella, "autoprova-graffiato.yuv")
    dati = bytearray(open(vero, "rb").read())
    dove = LARGHEZZA * 2 * RIGA_RAMPA + 100
    dati[dove] ^= 0xFF
    open(graffiato, "wb").write(bytes(dati))
    c1 = confronta(vero, graffiato)
    ok1 = (not c1["identici"]) and c1["Y"]["campioni_diversi"] >= 1
    if not ok1:
        guasti.append("⛔ il comparatore non vede un byte girato: non confronta niente")

    c0 = confronta(vero, vero)
    ok0 = c0["identici"] and c0["Y"]["campioni_diversi"] == 0
    if not ok0:
        guasti.append("⛔ il comparatore dice DIVERSO un file contro se stesso")

    # 2 e 3 — il misuratore dei bit, nei due versi
    m_vero = misura_bit(vero, RIGA_RAMPA)
    m_finto = misura_bit(finto, RIGA_RAMPA)
    ok2 = m_vero["verdetto"] == "10-bit-veri" and m_vero["livelli_distinti"] == ATTESO_LIVELLI_VERI
    ok3 = m_finto["verdetto"] == "8-bit-travestiti" and m_finto["livelli_distinti"] == ATTESO_LIVELLI_8IN10
    if not ok2:
        guasti.append(f"⛔ sul sorgente VERO il misuratore dice {m_vero}")
    if not ok3:
        guasti.append(f"⛔ 10 BIT NON DISTINGUIBILI DA 8: sul caso opposto il "
                      f"misuratore dice {m_finto}")

    os.remove(graffiato)
    esito = {"controllo_positivo": ok0 and ok1 and ok2 and ok3,
             "comparatore_identita": ok0, "comparatore_un_byte": ok1,
             "misura_vero": m_vero, "misura_opposto": m_finto,
             "guasti": guasti}
    print(json.dumps(esito, ensure_ascii=False, indent=2))
    return 0 if esito["controllo_positivo"] else 1


def genera(cartella):
    os.makedirs(cartella, exist_ok=True)
    Y, U, V = costruisci()
    Us, Vs = sottocampiona(U), sottocampiona(V)
    vero = os.path.join(cartella, "sorgente-10bit.yuv")
    scrivi_yuv(vero, Y, Us, Vs)
    crudo = open(vero, "rb").read()
    open(os.path.join(cartella, "sorgente-8in10.yuv"), "wb").write(a_8_bit(crudo))

    scheda = {
        "larghezza": LARGHEZZA, "altezza": ALTEZZA,
        "formato": "yuv420p10le", "colore": "BT.709 range limitato",
        "riga_della_rampa": RIGA_RAMPA,
        "atteso_livelli_veri": ATTESO_LIVELLI_VERI,
        "atteso_livelli_8in10": ATTESO_LIVELLI_8IN10,
        "atteso_m4_8in10": ATTESO_M4_8IN10,
        "soglia_m4_veri": SOGLIA_M4_VERI,
        "fasce": {"rampa": FASCIA_RAMPA, "sfumature": FASCIA_SFUMATURE,
                  "testo": FASCIA_TESTO, "fine": FASCIA_FINE,
                  "toppe": FASCIA_TOPPE},
        "byte_per_fotogramma": len(crudo),
    }
    with open(os.path.join(cartella, "sorgente.json"), "w") as f:
        json.dump(scheda, f, ensure_ascii=False, indent=2)
    print(json.dumps(scheda, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--genera", metavar="CARTELLA")
    p.add_argument("--autoprova", metavar="CARTELLA")
    p.add_argument("--livelli", metavar="FILE")
    p.add_argument("--riga", type=int, default=RIGA_RAMPA)
    p.add_argument("--confronta", nargs=2, metavar=("A", "B"))
    a = p.parse_args()

    if a.genera:
        return genera(a.genera)
    if a.autoprova:
        return autoprova(a.autoprova)
    if a.livelli:
        print(json.dumps(misura_bit(a.livelli, a.riga), ensure_ascii=False))
        return 0
    if a.confronta:
        print(json.dumps(confronta(*a.confronta), ensure_ascii=False))
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
