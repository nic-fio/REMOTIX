#!/usr/bin/env python3
"""04-b20-desktop-vero.py — ⛔ IL BANCO DI A1: nel fotogramma che ARRIVA AL
CLIENT c'e' la SHELL, o uno schermo vuoto?

  python3 04-b20-desktop-vero.py --certifica --lavoro DIR
  python3 04-b20-desktop-vero.py --registrazione X.rcpreg --lavoro DIR \\
          --etichetta con-monitor --esiti 04-b20-esiti.jsonl

⚠ Gira DENTRO il contenitore: ci vuole `ffmpeg`, che sta li'.  ⛔ E NON ci
  vogliono ne' `numpy` ne' `PIL`, che li' non ci sono (`[M]` 14 agosto 2026):
  i conti si fanno a mano su un `rgb24` grezzo, e ffmpeg fa la scala.

===========================================================================
⛔ LA DOMANDA, UNA SOLA, E DAL LATO CHE RICEVE
===========================================================================

`fasi/rapporti/F5-desktop-vero.md`: il prodotto **aggiunge** un monitor alla
sessione e cattura QUELLO.  GNOME ci mette lo sfondo — e basta.  ⇒ La domanda
non e' «arrivano fotogrammi» e non e' «quanti monitor ci sono»: e'

    **nel fotogramma che il client ha decodificato c'e' la SHELL?**

⛔ E IL CONTEGGIO DEI MONITOR NON E' LA MISURA.  `GetCurrentState` dice quanti
   schermi ci sono, non su quale sta la barra: il 12 e il 13 agosto ce n'erano
   due IDENTICI su misura e nome del fornitore, e chi li contava non distingueva
   niente (`src/sessione.h` §«il monitor si sceglie per nome»).  Qui il conteggio
   sta accanto al verdetto come **controllo**, e non entra nel verdetto.

===========================================================================
⛔⛔ «C'E' LO SFONDO» NON E' «C'E' IL DESKTOP» — ed e' l'errore che ha
     nascosto questo difetto per DUE FASI
===========================================================================

Il giudizio della fase 2 si chiuse su *«e' lo sfondo GNOME, e' OK»*: uno
schermo vuoto preso per un successo.  ⇒ ⛔ **Lo sfondo GNOME va su TUTTI i
monitor; la barra e la dock NO.**  Un giudice che guardasse «l'immagine non e'
nera» direbbe VERDE sul difetto vivo.

⭐ COME QUESTO BANCO LI DISTINGUE — e i numeri sono stati CALIBRATI su due
   immagini vere prima di scrivere le soglie (`[M]` 14 agosto 2026, dalla prova
   dell'utente `fasi/rapporti/F3-verbali/desktop-vero-14ago.png`: il desktop
   vero, e lo sfondo Debian da solo ritagliato dalla stessa immagine):

  | # | indicatore | che cosa misura | shell | sfondo |
  |---|---|---|---|---|
  | **B** | IL BORDO DELLA BARRA | il **salto** di luminanza fra due righe vicine, cercato fra la riga 20 e la 48: la barra di GNOME finisce di netto, uno sfondo no | **11,8** | **0,07** |
  | **T** | L'OROLOGIO | quanti **fronti** orizzontali forti ci sono nel terzo centrale della fascia alta: e' il testo dell'ora | **565** | **0** |
  | **D** | LA DOCK | il dettaglio in basso al centro contro le stesse righe a sinistra e a destra | corroborazione |

  ⛔ **Il verdetto lo danno B e T insieme**, e sono due fatti di natura diversa:
     B e' **geometrico** (un bordo netto dove nessuno sfondo ne ha uno), T e'
     di **contenuto** (c'e' scritto qualcosa).  ⚠ **D non entra nel verdetto** e
     si stampa lo stesso: sulla calibrazione ha dato 0,069 contro 0,082 — cioe'
     **non distingue**, e un indicatore che non distingue non si tiene per buono
     solo perche' sarebbe piaciuto (⇒ si dichiara, non si nasconde).

  ⛔ E LA PRIMA STESURA DI **B** ERA SBAGLIATA, e l'ha smentita la calibrazione:
     cercava un **gradino** fra la barra e lo sfondo sotto (barra scura, sfondo
     chiaro).  ⚠ Su una sessione appena aperta GNOME e' in **panoramica**, e
     sotto la barra c'e' grigio scuro, non lo sfondo: il gradino misurato vale
     **7**, sotto la soglia — cioe' il banco avrebbe detto VUOTO **sul desktop
     vero**.  ⇒ La soglia non si e' allargata: si e' cambiata la grandezza.

===========================================================================
⛔ ZERO E FALLIMENTO NON HANNO LO STESSO ASPETTO — `CODER.md` §3.10
===========================================================================

Le uscite sono distinte, e «non ho potuto guardare» non si travestira' mai da
«non c'era la shell»:

    0  SHELL      c'e' il desktop vero: il bordo della barra E l'orologio
    1  VUOTO      il fotogramma e' arrivato, e la shell NON c'e'
    2  NON GIUDICABILE   il decodificatore non ha reso un'immagine da byte che
                         c'erano: ⛔ e' lo strumento, non il prodotto
    3  MEZZO      uno dei due indicatori e non l'altro: non decido
    4  USO SBAGLIATO
    5  NESSUN FOTOGRAMMA  ⛔ al client non e' arrivato NIENTE

⛔⛔ E IL **5** NON E' UN «NON HO POTUTO GUARDARE»: e' un rosso, ed e' la
    faccia PEGGIORE dello stesso difetto.  `[M]` 14 agosto 2026, 07:02: con
    `--virtual-monitor` in vigore il palco si prende (monitor «Meta-1», 1 prima
    e 2 dopo), il client apre il canale video e in 12 s riceve **zero
    fotogrammi**, chiedendo dodici volte una chiave che non arriva —
    *«48 attese a vuoto (scena ferma: Mutter consegna solo quando qualcosa
    cambia)»*.  ⇒ **Sullo schermo in piu' non cambia MAI niente**: non c'e'
    l'orologio che scatta, non c'e' la dock che si anima, non c'e' niente.
    ⚠ Lo zero si distingue dal guasto dello strumento con il **controllo
      positivo**: lo stesso banco, lo stesso minuto, sulla sessione curata
      riceve fotogrammi e li giudica.

⭐ E il controllo positivo dello STRUMENTO sta in `--certifica`: due immagini
   fabbricate qui, senza il prodotto e senza GNOME — una con la barra, il testo
   e le icone, una col solo sfondo — che il giudice deve chiamare SHELL e VUOTO.
   ⛔ Un giudice che non sa dire di si' su un caso costruito non ha il diritto di
   dire di no sul caso vero.
"""
import argparse
import json
import os
import struct
import subprocess
import sys
import time

# --- il formato §11.1, letto da `banchi/02-filo-cliente.py` (non riscritto) ---
#
# ⭐ `RCPREG 0x00 0x03` dal **21 agosto 2026**: il blocco porta `istante_ms` e
#    passa da 17 a 21 byte, l'intestazione dichiara `orologio`.
# ⛔ E questo file era il terzo dell'ISOLA `0x02` — con `02-filo-cliente.py` che
#    scriveva e `02-filo-validatore.py` che leggeva.  I tre andavano d'accordo
#    fra loro mentre `01-b3`/`01-b4` erano gia' a `0x03`: ⚠ **nessuno dei tre
#    era rotto da solo**, e la miccia era posata — `04-b20-lancia.sh:105` copia
#    `01-b3-cliente.py` nello stesso albero, quindi bastava che qualcuno
#    passasse di qui una traccia di B3.  E' la forma del difetto del 12 agosto.
MAGIA = b"RCPREG\x00\x03"
MAGIA_V1 = b"RCPREG\x00\x01"
MAGIA_V2 = b"RCPREG\x00\x02"
BLOCCO = "!BBBIQIH"
BLOCCO_BYTE = struct.calcsize(BLOCCO)
CANALE_VIDEO = 0x03
INTESTAZIONE = 28          # §6.2, «28 byte esatti, senza riempimento»
CHIAVE, DELTA = 0x0301, 0x0302

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# --- le soglie, SCRITTE PRIMA DEL GIRO -------------------------------------
# ⛔ Si scrivono qui, in cima, e non sparse nel codice: una soglia che si trova
#    solo leggendo il conto e' una soglia che si puo' spostare dopo aver visto
#    il risultato, e allora il banco non giudica piu' niente.
ALTEZZA_BARRA = 28         # righe che la barra di GNOME occupa di sicuro
FASCIA_ALTA = 60           # quante righe si ritagliano per cercare il bordo
BORDO_DA, BORDO_A = 20, 48  # dove puo' stare il bordo basso della barra
SALTO = 4.0                # |dY| fra due righe vicine che fa «bordo netto»
                           # ⭐ calibrato: 11,8 sulla shell, 0,07 sullo sfondo
FRONTE = 34.0              # |dY| orizzontale che conta come fronte (testo)
FRONTI_MINIMI = 40         # ⭐ calibrato: 565 sulla shell, 0 sullo sfondo
BORDO_PICCOLO = 18.0       # |dY| che conta come dettaglio nell'immagine ridotta


def dimmi(*a):
    print(*a, flush=True)


# ===========================================================================
def blocchi_video(percorso):
    """I blocchi video della registrazione, in ordine, raggruppati per stream.

    ⛔ Se il file non c'e' o non ha la magia giusta si ALZA: «non ho potuto
       leggere» esce 2, e non diventa «non c'era la shell»."""
    with open(percorso, "rb") as f:
        d = f.read()
    # ⛔ E LE VERSIONI VECCHIE SI NOMINANO, invece di finire in «magia strana».
    #    §11.1: *«un validatore vecchio deve RIFIUTARE il formato nuovo, non
    #    leggerlo di traverso»*, e vale nei due versi.  ⚠ «Non e' una
    #    registrazione» manda a cercare chi ha rotto il file; «e' di
    #    un'altra versione» manda a rigenerarlo.  Sono due cure diverse.
    if len(d) >= 8 and d[:8] in (MAGIA_V1, MAGIA_V2):
        raise ValueError(
            f"«{percorso}» e' una registrazione di una versione VECCHIA di "
            f"§11.1 ({d[:8]!r}): il blocco misura "
            f"{16 if d[:8] == MAGIA_V1 else 17} byte invece di 21.  ⛔ Non si "
            f"legge di traverso — ogni blocco scivolerebbe — e non e' un file "
            f"rotto: si RIGENERA con `02-filo-cliente.py`")
    if len(d) < 16 or d[:8] != MAGIA:
        raise ValueError(f"«{percorso}» non e' una registrazione §11.1 "
                         f"(magia: {d[:8]!r})")
    n, orologio, r1, r2, r3 = struct.unpack("!IBBBB", d[8:16])
    if (r1, r2, r3) != (0, 0, 0) or orologio not in (1, 2):
        raise ValueError(
            f"«{percorso}»: intestazione §11.1 malformata — orologio "
            f"{orologio} (attesi 1 o 2), riservati {r1},{r2},{r3} (attesi 0)")
    p, flussi, ordine = 16, {}, []
    for _ in range(n):
        if p + BLOCCO_BYTE > len(d):
            raise ValueError("registrazione troncata nell'intestazione di un blocco")
        verso, canale, fine, istante, stream, lung, nosc = struct.unpack(
            BLOCCO, d[p:p + BLOCCO_BYTE])
        p += BLOCCO_BYTE
        for _ in range(nosc):
            _, qua = struct.unpack("!II", d[p:p + 8])
            p += 8 + 32
        carico = d[p:p + lung]
        p += lung
        if canale != CANALE_VIDEO:
            continue
        if stream not in flussi:
            flussi[stream] = bytearray()
            ordine.append(stream)
        flussi[stream] += carico
    return [(s, bytes(flussi[s])) for s in ordine]


def prima_chiave(flussi):
    """Il primo fotogramma CHIAVE completo, con la sua intestazione letta.

    ⚠ La scena e' FERMA di proposito — un desktop GNOME appena aperto — e con
      `framerate 0/1` (`cattura.h`) su una scena ferma non arriva quasi nulla.
      ⛔ Quel che arriva SEMPRE e' il primo fotogramma dopo `SESSIONE`, che §5.2
      impone sia una chiave: e' quello l'oggetto di questa misura, dichiarato.
    """
    for sid, dati in flussi:
        if len(dati) <= INTESTAZIONE:
            continue
        tipo, codec, lar, alt, num, ist, inp = struct.unpack(
            "!HHIIIQI", dati[:INTESTAZIONE])
        if tipo != CHIAVE:
            continue
        return {"stream": sid, "tipo": tipo, "codec": codec, "larghezza": lar,
                "altezza": alt, "numero": num, "istante": ist,
                "byte": len(dati) - INTESTAZIONE,
                "carico": dati[INTESTAZIONE:]}
    return None


# ===========================================================================
def ffmpeg(argomenti, dove):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
                       + argomenti, capture_output=True)
    if r.returncode != 0:
        dimmi(f"   ⛔ ffmpeg({dove}) e' uscito {r.returncode}: "
              f"{r.stderr.decode(errors='replace')[:400]}")
        return False
    return True


def rendi(sorgente, lavoro, etichetta, codec):
    """Dal carico codificato ai tre file su cui si conta.

    ⛔ Il PNG non serve al giudizio: serve a chi vorra' guardare con gli occhi
       quel che il banco ha giudicato (I8 — il metro e' quel che l'utente vede).
    """
    demux = "hevc" if codec == 1 else ("av1" if codec == 2 else None)
    if demux is None:
        return None, f"codec {codec} sconosciuto a questo banco"
    png = os.path.join(lavoro, f"{etichetta}-fotogramma.png")
    piccolo = os.path.join(lavoro, f"{etichetta}-piccolo.rgb")
    barra = os.path.join(lavoro, f"{etichetta}-barra.rgb")
    comune = ["-f", demux, "-i", sorgente, "-frames:v", "1"]
    if not ffmpeg(comune + [png], "png"):
        return None, "il decodificatore non ha reso nessuna immagine"
    # ⚠ 480x270: la barra (28 righe su 1080) resterebbe 7 righe, e il suo bordo
    #   basso — che e' tutto il punto di **B** — sparirebbe nella scala.  ⇒ La
    #   fascia alta si guarda a PIENA RISOLUZIONE, in un ritaglio suo; la dock,
    #   che e' larga, si guarda in piccolo.  Due misure, due scale, dichiarate.
    if not ffmpeg(comune + ["-vf", "scale=480:270", "-pix_fmt", "rgb24",
                            "-f", "rawvideo", piccolo], "piccolo"):
        return None, "la scala 480x270 non e' riuscita"
    if not ffmpeg(comune + ["-vf", f"crop=iw:{FASCIA_ALTA}:0:0",
                            "-pix_fmt", "rgb24", "-f", "rawvideo", barra],
                  "barra"):
        return None, "il ritaglio della fascia alta non e' riuscito"
    return {"png": png, "piccolo": piccolo, "barra": barra}, None


def leggi_rgb(percorso, larghezza, altezza):
    with open(percorso, "rb") as f:
        d = f.read()
    atteso = larghezza * altezza * 3
    if len(d) != atteso:
        raise ValueError(f"«{percorso}»: {len(d)} byte invece di {atteso}")
    return d


def luma(d, i):
    return 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2]


# ===========================================================================
def indicatori(png_larghezza, png_altezza, file_barra, file_piccolo):
    """I tre numeri, calcolati e restituiti TUTTI — anche D, che non entra nel
    verdetto: un indicatore che non distingue si dichiara, non si nasconde."""
    m = {}
    L = png_larghezza

    # ---- il profilo delle righe della fascia alta, a piena risoluzione ----
    # ⛔ Si campiona una colonna ogni 8: la barra e' larga quanto lo schermo, e
    #    1920 colonne per 60 righe in Python puro non aggiungono niente.  Il
    #    passo si DICHIARA, perche' entra nei numeri.
    passo = 8
    d = leggi_rgb(file_barra, L, FASCIA_ALTA)
    colonne = list(range(0, L, passo))
    prof = []
    for y in range(FASCIA_ALTA):
        riga = y * L
        prof.append(sum(luma(d, (riga + x) * 3) for x in colonne) / len(colonne))

    # ---- B: IL BORDO BASSO DELLA BARRA -----------------------------------
    # ⛔ Non un GRADINO fra barra e sfondo (la prima stesura, smentita dalla
    #    calibrazione: in panoramica sotto la barra c'e' grigio scuro), ma un
    #    **bordo netto**: la barra finisce in una riga, uno sfondo no.
    salto, dove = 0.0, -1
    for y in range(BORDO_DA, min(BORDO_A, FASCIA_ALTA - 1)):
        v = abs(prof[y + 1] - prof[y])
        if v > salto:
            salto, dove = v, y + 1
    m["barra_luminanza"] = round(sum(prof[:ALTEZZA_BARRA]) / ALTEZZA_BARRA, 2)
    m["salto_bordo"] = round(salto, 2)
    m["riga_del_bordo"] = dove
    m["B"] = bool(salto > SALTO)

    # ---- T: L'OROLOGIO — i fronti dentro la barra ------------------------
    # ⚠ Nel terzo CENTRALE: l'orologio di GNOME sta al centro della barra.  Gli
    #   indicatori a destra restano fuori apposta, perche' su una sessione
    #   appena aperta non e' detto quali ci siano.
    x0, x1 = L // 3, 2 * L // 3
    fronti = 0
    for y in range(4, ALTEZZA_BARRA - 4):
        riga = y * L
        prec = luma(d, (riga + x0) * 3)
        for x in range(x0 + 1, x1):
            v = luma(d, (riga + x) * 3)
            if abs(v - prec) > FRONTE:
                fronti += 1
            prec = v
    m["fronti_nella_barra"] = fronti
    m["T"] = bool(fronti >= FRONTI_MINIMI)

    # ---- D: LA DOCK — corroborazione, NON verdetto -----------------------
    # ⚠ Si confronta il centro in basso con le STESSE righe a sinistra e a
    #   destra: cosi' il paragone non dipende dallo sfondo che c'e' quel giorno.
    #   ⛔ E in calibrazione NON ha distinto (0,069 shell contro 0,082 sfondo):
    #      resta qui come numero da guardare, e non decide niente.
    PL, PA = 480, 270
    p = leggi_rgb(file_piccolo, PL, PA)

    def dettaglio(xa, xb, ya, yb):
        c = t = 0
        for y in range(ya, yb):
            riga = y * PL
            prec = luma(p, (riga + xa) * 3)
            for x in range(xa + 1, xb):
                v = luma(p, (riga + x) * 3)
                if abs(v - prec) > BORDO_PICCOLO:
                    c += 1
                prec = v
                t += 1
        return round(c / t, 4) if t else 0.0

    ya, yb = int(PA * 0.90), int(PA * 0.99)
    m["dock_centro"] = dettaglio(int(PL * 0.32), int(PL * 0.68), ya, yb)
    m["dock_sinistra"] = dettaglio(int(PL * 0.02), int(PL * 0.24), ya, yb)
    m["dock_destra"] = dettaglio(int(PL * 0.76), int(PL * 0.98), ya, yb)
    m["D"] = bool(m["dock_centro"] > 0.01
                  and m["dock_centro"] > 3 * max(m["dock_sinistra"],
                                                 m["dock_destra"], 0.002))
    return m


def verdetto(m):
    """⛔ B **e** T, e sono due fatti di natura diversa: uno geometrico (un bordo
    netto dove nessuno sfondo ne ha uno), uno di contenuto (c'e' scritto
    qualcosa).  ⚠ D non entra: in calibrazione non distingueva."""
    if m["B"] and m["T"]:
        return 0, "SHELL"
    if m["B"] or m["T"]:
        return 3, "MEZZO"
    return 1, "VUOTO"


# ===========================================================================
def giudica_immagine(png, lavoro, etichetta, larghezza, altezza):
    """Il giudizio a partire da un'immagine gia' resa (serve a `--certifica`)."""
    piccolo = os.path.join(lavoro, f"{etichetta}-piccolo.rgb")
    barra = os.path.join(lavoro, f"{etichetta}-barra.rgb")
    if not ffmpeg(["-i", png, "-vf", "scale=480:270", "-pix_fmt", "rgb24",
                   "-f", "rawvideo", piccolo], "piccolo"):
        return None
    if not ffmpeg(["-i", png, "-vf", f"crop=iw:{FASCIA_ALTA}:0:0",
                   "-pix_fmt", "rgb24", "-f", "rawvideo", barra], "barra"):
        return None
    return indicatori(larghezza, altezza, barra, piccolo)


def certifica(lavoro):
    """⭐ IL CONTROLLO DELLO STRUMENTO, senza il prodotto e senza GNOME.

    Due immagini fabbricate con `ffmpeg` e basta:

      · `finta-vuota`  — solo lo sfondo, con un disegno colorato che occupa
        tutto: ⛔ e' il caso CATTIVO per un giudice ingenuo, perche' «non e'
        nera» e «ha dei colori» sono tutti e due veri.  Deve dire **VUOTO**;
      · `finta-shell`  — la stessa cosa, piu' una barra nera in alto con del
        testo bianco e tre riquadri colorati in basso al centro.  Deve dire
        **SHELL**.

    ⛔ Se il giudice sbaglia uno dei due, non ha il diritto di giudicare il
       caso vero, e questo esce 2.
    """
    os.makedirs(lavoro, exist_ok=True)
    vuota = os.path.join(lavoro, "finta-vuota.png")
    shell = os.path.join(lavoro, "finta-shell.png")
    sfondo = ("testsrc2=size=1920x1080:duration=1:rate=1,"
              "boxblur=20:2,eq=brightness=0.05")
    if not ffmpeg(["-f", "lavfi", "-i", sfondo, "-frames:v", "1", vuota],
                  "finta-vuota"):
        return 2
    filtro = (
        "drawbox=x=0:y=0:w=1920:h=32:color=black@1.0:t=fill,"
        "drawtext=text='14\\:32':x=930:y=6:fontsize=20:fontcolor=white,"
        "drawbox=x=830:y=990:w=60:h=60:color=orange@1.0:t=fill,"
        "drawbox=x=910:y=990:w=60:h=60:color=blue@1.0:t=fill,"
        "drawbox=x=990:y=990:w=60:h=60:color=green@1.0:t=fill")
    if not ffmpeg(["-i", vuota, "-vf", filtro, "-frames:v", "1", shell],
                  "finta-shell"):
        return 2

    esito = 0
    for nome, png, atteso in (("finta-vuota", vuota, "VUOTO"),
                              ("finta-shell", shell, "SHELL")):
        m = giudica_immagine(png, lavoro, nome, 1920, 1080)
        if m is None:
            dimmi(f"   ⛔ {nome}: non ho potuto misurare")
            return 2
        cod, parola = verdetto(m)
        segno = VERDE + "OK" + GRIGIO if parola == atteso else ROSSO + "NO" + GRIGIO
        dimmi(f"   {segno}  {nome}: il giudice dice {parola}, atteso {atteso}")
        dimmi(f"        B={m['B']} (salto {m['salto_bordo']} alla riga "
              f"{m['riga_del_bordo']})  T={m['T']} "
              f"({m['fronti_nella_barra']} fronti)  D={m['D']} "
              f"(centro {m['dock_centro']}, lati {m['dock_sinistra']}/"
              f"{m['dock_destra']})")
        if parola != atteso:
            esito = 2
    if esito == 0:
        dimmi(f"   {VERDE}⭐ lo strumento sa dire tutt'e due le cose{GRIGIO}")
    else:
        dimmi(f"   {ROSSO}⛔ lo strumento NON distingue: non giudica niente"
              f"{GRIGIO}")
    return esito


# ===========================================================================
def principale(a):
    os.makedirs(a.lavoro, exist_ok=True)
    if a.certifica:
        dimmi("== 04-b20 — la certificazione dello STRUMENTO (senza il prodotto)")
        return certifica(a.lavoro)

    if a.grezzo:
        # ⭐ IL FOTOGRAMMA GREZZO, senza decodificatore in mezzo: e' quel che la
        #    cattura ha consegnato al figlio.  ⚠ E' il lato che MANDA — si
        #    dichiara — ma toglie di mezzo una domanda per volta: se qui la
        #    shell non c'e', non c'e' nel PIXEL, e non e' colpa della codifica.
        dimmi(f"== 04-b20 — «{a.etichetta}» ⚠ dal lato che MANDA, GREZZO")
        riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "banco": "04-b20-desktop-vero", "etichetta": a.etichetta,
                "lato": "manda-grezzo", "scena": a.scena}
        png = os.path.join(a.lavoro, f"{a.etichetta}-fotogramma.png")
        if not ffmpeg(["-f", "rawvideo", "-pix_fmt", "bgra", "-s",
                       f"{a.larghezza}x{a.altezza}", "-i", a.grezzo,
                       "-frames:v", "1", png], "grezzo"):
            dimmi(f"   {ROSSO}⛔ NON GIUDICABILE: il grezzo non si legge{GRIGIO}")
            riga.update(verdetto="NON GIUDICABILE")
            scrivi(a, riga)
            return 2
        m = giudica_immagine(png, a.lavoro, a.etichetta, a.larghezza, a.altezza)
        if m is None:
            riga.update(verdetto="NON GIUDICABILE")
            scrivi(a, riga)
            return 2
        cod, parola = verdetto(m)
        stampa(m, {"png": png}, cod, parola, a)
        riga.update(verdetto=parola, uscita=cod, **m)
        scrivi(a, riga)
        return cod

    if a.flusso:
        # ⚠ E' il lato che MANDA, e si dichiara: e' il rilievo che il figlio
        #   scrive quando prende il palco.  ⛔ Non sostituisce la verifica dal
        #   lato che riceve (`CODER.md` §3.8): la affianca quando dall'altra
        #   parte non arriva niente, per poter dire **che cosa** non arrivava.
        dimmi(f"== 04-b20 — «{a.etichetta}» ⚠ dal lato che MANDA (rilievo)")
        riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "banco": "04-b20-desktop-vero", "etichetta": a.etichetta,
                "lato": "manda", "scena": a.scena}
        resi, perche = rendi(a.flusso, a.lavoro, a.etichetta, a.codec)
        if resi is None:
            dimmi(f"   {ROSSO}⛔ NON GIUDICABILE: {perche}{GRIGIO}")
            riga.update(verdetto="NON GIUDICABILE", perche=perche)
            scrivi(a, riga)
            return 2
        m = indicatori(a.larghezza, a.altezza, resi["barra"], resi["piccolo"])
        cod, parola = verdetto(m)
        stampa(m, resi, cod, parola, a)
        riga.update(verdetto=parola, uscita=cod, **m)
        scrivi(a, riga)
        return cod

    if not a.registrazione:
        dimmi("⛔ serve --registrazione X.rcpreg, --flusso X.265 o --certifica")
        return 4

    dimmi(f"== 04-b20 — «{a.etichetta}»")
    dimmi(f"   registrazione: {a.registrazione}")
    riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "banco": "04-b20-desktop-vero", "etichetta": a.etichetta,
            "scena": a.scena, "monitor_prima": a.monitor_prima,
            "monitor_dopo": a.monitor_dopo}
    try:
        flussi = blocchi_video(a.registrazione)
    except (OSError, ValueError) as e:
        dimmi(f"   ⛔ NON GIUDICABILE: {e}")
        riga.update(verdetto="NON GIUDICABILE", perche=str(e))
        scrivi(a, riga)
        return 2

    dimmi(f"   flussi video nella registrazione: {len(flussi)}")
    if not flussi:
        dimmi(f"\n   {ROSSO}⇒ NESSUN FOTOGRAMMA{GRIGIO}")
        dimmi("      ⛔ Al client non e' arrivato NIENTE, e non e' «non ho "
              "potuto guardare»:")
        dimmi("         sullo schermo che si cattura non cambia MAI niente, "
              "quindi Mutter")
        dimmi("         non consegna un solo fotogramma.  E' la faccia "
              "peggiore del difetto.")
        riga.update(verdetto="NESSUN FOTOGRAMMA", uscita=5, flussi=0)
        scrivi(a, riga)
        return 5
    ch = prima_chiave(flussi)
    if ch is None:
        dimmi(f"   {ROSSO}⛔ NON GIUDICABILE: nessun fotogramma CHIAVE completo"
              f"{GRIGIO}")
        dimmi("      ⚠ Non e' «la shell non c'e'»: e' l'assenza dell'oggetto "
              "del giudizio.")
        riga.update(verdetto="NON GIUDICABILE", flussi=len(flussi),
                    perche="nessuna chiave")
        scrivi(a, riga)
        return 2

    dimmi(f"   chiave n. {ch['numero']}: {ch['larghezza']}x{ch['altezza']}, "
          f"codec {ch['codec']}, {ch['byte']} byte di carico")
    sorgente = os.path.join(a.lavoro, f"{a.etichetta}-chiave."
                            + ("265" if ch["codec"] == 1 else "obu"))
    with open(sorgente, "wb") as f:
        f.write(ch["carico"])

    resi, perche = rendi(sorgente, a.lavoro, a.etichetta, ch["codec"])
    if resi is None:
        dimmi(f"   {ROSSO}⛔ NON GIUDICABILE: {perche}{GRIGIO}")
        riga.update(verdetto="NON GIUDICABILE", perche=perche,
                    misura=[ch["larghezza"], ch["altezza"]])
        scrivi(a, riga)
        return 2

    m = indicatori(ch["larghezza"], ch["altezza"], resi["barra"], resi["piccolo"])
    cod, parola = verdetto(m)
    stampa(m, resi, cod, parola, a)
    riga.update(verdetto=parola, uscita=cod, flussi=len(flussi),
                misura=[ch["larghezza"], ch["altezza"]], codec=ch["codec"],
                byte=ch["byte"], **m)
    scrivi(a, riga)
    return cod


def stampa(m, resi, cod, parola, a):
    dimmi(f"   immagine: {resi['png']}")
    dimmi(f"   B  bordo:    salto {m['salto_bordo']} (> {SALTO}) alla riga "
          f"{m['riga_del_bordo']}, luminanza della fascia "
          f"{m['barra_luminanza']}  ⇒ {m['B']}")
    dimmi(f"   T  orologio: {m['fronti_nella_barra']} fronti nel terzo centrale "
          f"(>= {FRONTI_MINIMI})  ⇒ {m['T']}")
    dimmi(f"   D  dock:     centro {m['dock_centro']} contro sinistra "
          f"{m['dock_sinistra']} e destra {m['dock_destra']}  ⇒ {m['D']} "
          f"⚠ NON entra nel verdetto")
    if a.monitor_prima is not None:
        dimmi(f"   ⚠ controllo (NON e' la misura): monitor "
              f"{a.monitor_prima} prima, {a.monitor_dopo} durante la cattura")
    colore = {0: VERDE, 1: ROSSO, 3: GIALLO}.get(cod, GIALLO)
    dimmi(f"\n   {colore}⇒ {parola}{GRIGIO}")
    if cod == 1:
        dimmi("      ⛔ l'immagine e' arrivata e la SHELL NON C'E': e' lo "
              "schermo in piu', vuoto.")
        dimmi("      ⚠ «c'e' lo sfondo» non e' «c'e' il desktop».")


def scrivi(a, riga):
    if a.esiti:
        with open(a.esiti, "a") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="04-b20 — la shell c'e' o no")
    p.add_argument("--registrazione", help="il .rcpreg di 02-filo-cliente.py")
    p.add_argument("--grezzo", help="⚠ un fotogramma BGRX del lato che MANDA")
    p.add_argument("--flusso", help="⚠ un flusso codificato del lato che MANDA "
                                    "(il rilievo del figlio)")
    p.add_argument("--codec", type=int, default=1, help="1 HEVC · 2 AV1")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--lavoro", default="/tmp/04-b20")
    p.add_argument("--etichetta", default="senza-nome")
    p.add_argument("--scena", default="", help="⛔ la scena, DICHIARATA")
    p.add_argument("--monitor-prima", type=int, default=None)
    p.add_argument("--monitor-dopo", type=int, default=None)
    p.add_argument("--esiti", default="")
    p.add_argument("--certifica", action="store_true")
    sys.exit(principale(p.parse_args()))
