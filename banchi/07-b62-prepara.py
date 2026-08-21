#!/usr/bin/env python3
"""07-b62-prepara.py — la SCENA DI VERITÀ e le strade da confrontare.

    python3 banchi/07-b62-prepara.py [--dati /tmp/07-b62-dati] [--misura 1280x720]

⛔ CHE COSA CHIUDE, e perché non basta `07-b48`.

`DECISIONI.md` §1.13-ter porta una `[?]`: *«il decodificatore H.264 in hardware
converte con una scala di colore diversa da ffmpeg: **+8 livelli sulle zone
chiare**, liscio e uniforme (peggio 30,3 livelli)»*.  Quella riga viene da
`07-b48`, che misura **la media della luma di un superblocco** ricostruita
dall'RGB con i coefficienti BT.709.  ⛔ Un metro così **non sa dire di chi è lo
scarto**: una matrice sbagliata, un intervallo sbagliato e un blocco rovinato
danno tutti e tre «la media non torna».

⭐ Questo banco cambia il metro in tre modi, ed è il motivo per cui esiste:

  1. **la verità è in YUV, non in RGB**.  La scena si fabbrica scrivendo a mano
     i piani Y/U/V ⇒ per ogni campione si sa il numero esatto che il
     codificatore riceve, e `l'RGB che ne deve uscire` è una **formula**, non
     un'altra misura.  Chi confronta due misure non sa mai chi delle due sbaglia.
  2. **per canale e per livello**: R, G e B separati, su una rampa che copre
     tutti e 256 i valori di Y ⇒ lo scarto si dice *dove* sta (ombre,
     mezzitoni, luci) invece che in media.
  3. **le barre di colore separano la MATRICE dall'INTERVALLO**.  Sul grigio
     (U=V=128) le due matrici 601 e 709 danno lo **stesso** RGB: un grigio non
     può accusare la matrice.  Le barre sature sì, e di decine di livelli.

⚠ E la domanda «è nostro o del decodificatore?» si decide con le VARIANTI: lo
  stesso quadro, gli stessi campioni YUV, codificato con la VUI **dichiarata**
  come fa il prodotto (`src/codificatore.c`: BT.709, intervallo limitato) e
  **taciuta**.  Se lo scarto compare solo quando si tace, è nostro; se compare
  anche quando si dichiara, è del decodificatore.

Che cosa lascia in `--dati`:
    verita.json      i campioni YUV di ogni riquadro e l'RGB che ne deve uscire
    scena.png        lo stesso quadro in RGB, per l'occhio e per la catena vera
    <variante>.264   il flusso Annex-B
    <variante>.json  l'indice dei pezzi (offset, lunghezza, chiave)
    riferimento.json quel che `ffmpeg` legge dagli stessi byte
    index.html       la pagina del banco, copiata qui accanto ai dati
"""
import argparse, json, os, shutil, struct, subprocess, sys, zlib

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ I coefficienti si scrivono per esteso e si dichiara la fonte: BT.709
#    (Rec. ITU-R BT.709-6 §3) e BT.601 (BT.601-7 §2.5.1), intervallo
#    limitato — Y in 16-235, croma in 16-240.  ⚠ Sono la FORMULA, non una
#    misura: è quel che i byte VOGLIONO DIRE.
MATRICI = {
    # nome: (Kr, Kb)
    "bt709": (0.2126, 0.0722),
    "bt601": (0.299, 0.114),
}


def yuv_da_rgb(r, g, b, matrice="bt709", pieno=False):
    """RGB 0-255 → Y/U/V interi.  ⚠ Serve solo a FABBRICARE le barre: la
    verità del banco resta il YUV, non l'RGB da cui è nato."""
    kr, kb = MATRICI[matrice]
    kg = 1.0 - kr - kb
    y = kr * r + kg * g + kb * b
    u = (b - y) / (2 * (1 - kb))
    v = (r - y) / (2 * (1 - kr))
    if pieno:
        return (round(y), round(u + 128), round(v + 128))
    return (round(16 + y * 219 / 255),
            round(128 + u * 224 / 255),
            round(128 + v * 224 / 255))


def rgb_da_yuv(y, u, v, matrice="bt709", pieno=False):
    """⭐ LA FORMULA, ed è il metro di questo banco.  Nessun ffmpeg, nessun
    browser: quel che i tre numeri Y/U/V significano, secondo la matrice e
    l'intervallo DICHIARATI nel flusso."""
    kr, kb = MATRICI[matrice]
    kg = 1.0 - kr - kb
    if pieno:
        yy, uu, vv = float(y), u - 128.0, v - 128.0
    else:
        yy = (y - 16.0) * 255.0 / 219.0
        uu = (u - 128.0) * 255.0 / 224.0
        vv = (v - 128.0) * 255.0 / 224.0
    r = yy + 2 * (1 - kr) * vv
    b = yy + 2 * (1 - kb) * uu
    g = (yy - kr * r - kb * b) / kg
    tag = lambda x: max(0.0, min(255.0, x))
    return (tag(r), tag(g), tag(b))


# ---------------------------------------------------------------------------
# la scena
# ---------------------------------------------------------------------------
def costruisci_scena(L, A):
    """Ritorna (piano_y, piano_u, piano_v, riquadri).

    ⛔ Le misure dei riquadri sono tutte multiple di 8 e i campioni si leggono
       dall'INTERNO con un margine: 4:2:0 dimezza il croma, e un riquadro letto
       fino al bordo misurerebbe la media col vicino invece del suo colore.
    """
    Y = bytearray([16]) * (L * A)
    U = bytearray([128]) * (L // 2 * A // 2)
    V = bytearray([128]) * (L // 2 * A // 2)
    riquadri = []

    def dipingi(x, y, w, h, yy, uu, vv):
        for r in range(y, y + h):
            base = r * L
            for c in range(x, x + w):
                Y[base + c] = yy
        for r in range(y // 2, (y + h) // 2):
            base = r * (L // 2)
            for c in range(x // 2, (x + w) // 2):
                U[base + c] = uu
                V[base + c] = vv

    def riquadro(nome, banda, x, y, w, h, yy, uu, vv, margine=8):
        dipingi(x, y, w, h, yy, uu, vv)
        riquadri.append({
            "nome": nome, "banda": banda,
            "x": x + margine, "y": y + margine,
            "w": w - 2 * margine, "h": h - 2 * margine,
            "Y": yy, "U": uu, "V": vv,
        })

    # ⛔ Le bande si calcolano dall'ALTEZZA, non si scrivono a mano: la scena
    #    serve anche a 480p — è il MINIMO di `DECISIONI.md` §2.1 — e lì la
    #    domanda «quale matrice indovina un decodificatore?» ha una risposta
    #    che può essere diversa (sotto le 576 righe il difetto storico è 601).
    #    ⚠ Con le coordinate scritte a mano quella prova non si potrebbe fare,
    #      e la si dichiarerebbe «non misurata» per un difetto del banco.
    NB = 6
    H = ((A - 16) // NB) // 8 * 8          # multiplo di 8, per il 4:2:0
    def banda(i):
        return 8 + i * H, H - 8

    # --- banda 0 · la rampa di grigio, TUTTI e 256 i livelli di Y ------------
    # ⭐ 256 gradini: U=V=128 ⇒ il croma è piatto e il 4:2:0 non c'entra, si
    #    misura la sola scala della luma, livello per livello.
    y0, h = banda(0)
    passo = L // 256
    for i in range(256):
        riquadro("rampa-Y%03d" % i, "rampa", i * passo, y0, passo, h,
                 i, 128, 128, margine=0)
        riquadri[-1]["x"] = i * passo + 1
        riquadri[-1]["w"] = max(1, passo - 2)
        riquadri[-1]["y"] = y0 + 8
        riquadri[-1]["h"] = h - 16

    # --- banda 1 · i valori limite ------------------------------------------
    # ⛔ 0 e 255 stanno FUORI dall'intervallo limitato: servono a vedere se il
    #    decodificatore taglia (come deve) o li stira (cioè legge «pieno»).
    y0, h = banda(1)
    for i, yy in enumerate([0, 16, 64, 128, 180, 235, 255]):
        w = L // 7
        riquadro("limite-Y%03d" % yy, "limiti", i * w, y0, w, h, yy, 128, 128)

    # --- banda 2 · le barre 100 %, ED È QUI CHE SI VEDE LA MATRICE -----------
    # ⚠ I campioni YUV si fabbricano con BT.709: un decodificatore che usasse
    #   BT.601 sugli stessi byte darebbe un RGB DIVERSO, e di decine di livelli.
    barre = [("bianco", 255, 255, 255), ("giallo", 255, 255, 0),
             ("ciano", 0, 255, 255), ("verde", 0, 255, 0),
             ("magenta", 255, 0, 255), ("rosso", 255, 0, 0),
             ("blu", 0, 0, 255), ("nero", 0, 0, 0)]
    w = L // 8
    y0, h = banda(2)
    for i, (nome, r, g, b) in enumerate(barre):
        yy, uu, vv = yuv_da_rgb(r, g, b, "bt709")
        riquadro("barra100-" + nome, "barre100", i * w, y0, w, h, yy, uu, vv)

    # --- banda 3 · le stesse barre al 75 % ----------------------------------
    # ⭐ Servono perché al 100 % quasi ogni canale è APPOGGIATO a 0 o a 255, e
    #    un canale tagliato non può accusare nessuna conversione.
    y0, h = banda(3)
    for i, (nome, r, g, b) in enumerate(barre):
        yy, uu, vv = yuv_da_rgb(r * 0.75, g * 0.75, b * 0.75, "bt709")
        riquadro("barra75-" + nome, "barre75", i * w, y0, w, h, yy, uu, vv)

    # --- banda 4 · le rampe di croma ----------------------------------------
    # Y fermo a 128: quel che si muove è solo U (a sinistra) o solo V (a destra).
    y0, h = banda(4)
    n = 32
    pu = ((L // 2) // n) // 2 * 2
    for i in range(n):
        uu = round(16 + i * (240 - 16) / (n - 1))
        riquadro("rampaU-%03d" % uu, "rampaU", i * pu, y0, pu, h,
                 128, uu, 128, margine=4)
    for i in range(n):
        vv = round(16 + i * (240 - 16) / (n - 1))
        riquadro("rampaV-%03d" % vv, "rampaV", L // 2 + i * pu, y0, pu, h,
                 128, 128, vv, margine=4)

    # --- banda 5 · i bordi netti --------------------------------------------
    # ⛔ NON si misura come riquadro: serve all'occhio e alla nitidezza.  Il
    #    4:2:0 sfrangia il bordo rosso/blu e lascia intatto il bianco/nero.
    y0, h = banda(5)
    meta = y0 + (h // 2) // 2 * 2
    for c in range(L):
        acceso = (c // 4) % 2 == 0
        for r in range(y0, meta):
            Y[r * L + c] = 235 if acceso else 16
    yr = yuv_da_rgb(255, 0, 0, "bt709")
    yb = yuv_da_rgb(0, 0, 255, "bt709")
    for c in range(L):
        s = yr if (c // 4) % 2 == 0 else yb
        for r in range(meta, y0 + h):
            Y[r * L + c] = s[0]
    for c in range(L // 2):
        s = yr if (c // 2) % 2 == 0 else yb
        for r in range(meta // 2, (y0 + h) // 2):
            U[r * (L // 2) + c] = s[1]
            V[r * (L // 2) + c] = s[2]

    return bytes(Y), bytes(U), bytes(V), riquadri


# ---------------------------------------------------------------------------
# il PNG (per l'occhio e per la catena vera)
# ---------------------------------------------------------------------------
def scrivi_png(percorso, L, A, righe_rgb):
    grezzo = b"".join(b"\x00" + r for r in righe_rgb)

    def pezzo(tipo, dati):
        return (struct.pack(">I", len(dati)) + tipo + dati
                + struct.pack(">I", zlib.crc32(tipo + dati) & 0xFFFFFFFF))

    with open(percorso, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(pezzo(b"IHDR", struct.pack(">IIBBBBB", L, A, 8, 2, 0, 0, 0)))
        f.write(pezzo(b"IDAT", zlib.compress(grezzo, 6)))
        f.write(pezzo(b"IEND", b""))


# ---------------------------------------------------------------------------
# i flussi
# ---------------------------------------------------------------------------
# ⛔⛔ LE VARIANTI SI FANNO RISCRIVENDO LA VUI, NON RICODIFICANDO.
#
#     Ricodificando cambierebbero anche i CAMPIONI — la compressione non è
#     senza perdite — e allora «lo scarto cambia fra dichiarato e taciuto»
#     avrebbe due spiegazioni invece di una.  ⭐ Con `h264_metadata` i byte dei
#     campioni sono gli STESSI bit: l'unica cosa che si muove sono i quattro
#     numeri della VUI, che è precisamente la leva dell'esperimento.
#
# I numeri vengono dalle tabelle E-1/E-2/E-3 di H.264: 1 = BT.709,
# 2 = **unspecified**, 6 = SMPTE 170M (cioè BT.601).
VARIANTI = {
    # come fa il prodotto oggi (`src/codificatore.c:1415-1418`)
    "dichiarato": None,
    # ⛔ la VUI che dice «non lo so»: è il caso in cui il decodificatore INDOVINA
    "taciuto": "colour_primaries=2:transfer_characteristics=2:"
               "matrix_coefficients=2:video_full_range_flag=0",
    # l'intervallo pieno dichiarato: si guarda se il decodificatore lo onora
    "pieno-dichiarato": "video_full_range_flag=1",
    # ⚠ la matrice DIVERSA dichiarata: è il controllo che dimostra che il
    #   decodificatore la VUI la legge davvero.  Se qui non cambia niente,
    #   allora la VUI non la guarda, e ogni discorso su «basta dichiararlo» cade.
    "601-dichiarato": "colour_primaries=6:transfer_characteristics=6:"
                      "matrix_coefficients=6:video_full_range_flag=0",
}


def codifica(dati, nome, grezzo, L, A, quanti, motore):
    """Il flusso di partenza: la VUI la dichiara come il prodotto."""
    uscita = os.path.join(dati, nome + ".264")
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if motore == "vaapi":
        cmd += ["-vaapi_device", "/dev/dri/renderD128"]
    cmd += ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "%dx%d" % (L, A),
            "-framerate", "30", "-stream_loop", str(quanti - 1), "-i", grezzo]
    # ⛔⛔ `setparams` E NON `-color_range tv` SULL'USCITA, e la differenza è
    #     costata un giro: un rawvideo non porta etichette, e chiedendo `tv`
    #     in uscita ffmpeg infila uno `scale` che **taglia** i campioni fuori
    #     dall'intervallo legale.  `[M]` Y=0 usciva 16 e Y=255 usciva 235 ⇒ i
    #     due valori limite che questo banco esiste per misurare sparivano
    #     PRIMA del codificatore, e la tabella li avrebbe dichiarati «giusti».
    #     `setparams` ETICHETTA e basta: non tocca un campione.
    marca = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"
    if motore == "vaapi":
        # ⛔ `format=nv12` PRIMA di `hwupload`, o swscale converte per conto suo
        #    e ci mette del suo dentro alla misura del colore.
        cmd += ["-vf", marca + ",format=nv12,hwupload", "-c:v", "h264_vaapi",
                "-profile:v", "high", "-qp", "10", "-low_power", "1"]
    else:
        # ⚠ `-qp 4` e non 0: `-qp 0` porta x264 su High 4:4:4 Predictive, cioè
        #   un profilo che `avc1.640032` NON dichiara — misureremmo un flusso
        #   che il prodotto non produrrebbe mai.
        cmd += ["-vf", marca, "-c:v", "libx264", "-profile:v", "high", "-qp", "4",
                "-x264-params", "keyint=30:min-keyint=30", "-pix_fmt", "yuv420p"]
    cmd += ["-f", "h264", uscita]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return None, (p.stderr or "").strip()[-400:]
    return uscita, None


def riscrivi_vui(base, uscita, opzioni):
    p = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base,
                        "-c:v", "copy", "-bsf:v", "h264_metadata=" + opzioni,
                        "-f", "h264", uscita], capture_output=True, text=True)
    return None if p.returncode else uscita, (p.stderr or "").strip()[-300:]


def indice_annexb(percorso):
    """Divide il flusso Annex-B in unità d'accesso.  ⛔ Un chunk per FOTOGRAMMA,
    coi parameter set attaccati al primo: in Annex-B il pezzo `key` deve
    portarseli dietro (`S2-decodifica.md` §3.5)."""
    d = open(percorso, "rb").read()
    inizi = []
    i = 0
    while True:
        j = d.find(b"\x00\x00\x01", i)
        if j < 0:
            break
        avvio = j - 1 if j > 0 and d[j - 1] == 0 else j
        inizi.append((avvio, j + 3))
        i = j + 3
    nal = []
    for k, (avvio, corpo) in enumerate(inizi):
        fine = inizi[k + 1][0] if k + 1 < len(inizi) else len(d)
        nal.append((avvio, fine, d[corpo] & 0x1F, (d[corpo + 1] & 0x80) != 0))
    pezzi, chiave = [], []
    apri = None
    for avvio, fine, tipo, primo in nal:
        if tipo in (1, 5):
            if apri is None:
                apri = avvio
            pezzi.append([apri, fine - apri])
            chiave.append(tipo == 5)
            apri = None
        elif tipo in (7, 8, 6, 9):
            if apri is None:
                apri = avvio
        else:
            if apri is None:
                apri = avvio
    return {"pezzi": pezzi, "chiave": chiave, "byte": len(d)}


def ffprobe_colore(percorso):
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries",
                        "stream=color_space,color_range,color_primaries,color_transfer,profile,level,pix_fmt",
                        "-of", "json", percorso], capture_output=True, text=True)
    try:
        return json.loads(p.stdout)["streams"][0]
    except Exception:
        return {"errore": (p.stderr or "")[:200]}


def ffmpeg_in_rgb(percorso, L, A, filtro=None):
    """⭐ IL RIFERIMENTO: gli STESSI byte, letti da ffmpeg.  ⚠ Non è «la
    verità»: è una seconda opinione, e serve a dire se il browser si scosta
    dalla formula da solo o in compagnia.

    ⛔ `filtro=None` è ffmpeg COME LO SI CHIAMA NORMALMENTE — ed è un caso da
       misurare, non da evitare: se il difetto predefinito di swscale non è la
       matrice dichiarata nel flusso, ogni «verità» costruita così è storta, e
       il banco che la usa accuserebbe il browser dello sbaglio di ffmpeg.
    """
    cmd = ["ffmpeg", "-v", "error", "-i", percorso, "-frames:v", "1"]
    if filtro:
        cmd += ["-vf", filtro]
    cmd += ["-pix_fmt", "rgb24", "-f", "rawvideo", "-"]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0 or len(p.stdout) < L * A * 3:
        return None
    return p.stdout[:L * A * 3]


def ffmpeg_in_yuv(percorso, L, A):
    """⛔⭐ I CAMPIONI COME IL CODIFICATORE LI HA LASCIATI, e serve a togliere
    di mezzo una variabile intera.

    Il codificatore non è senza perdite: `[M]` con x264 a `-qp 4` il piano V si
    scosta di un livello, e un livello di V sposta il ROSSO di ~1,8 livelli.
    ⇒ Confrontando il browser con la formula applicata ai campioni di PARTENZA
    si attribuirebbe al colore uno scarto che è della compressione.
    ⭐ Applicando la formula ai campioni **decodificati** resta solo la
    conversione di colore, che è quel che si sta misurando."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", percorso,
                        "-frames:v", "1", "-pix_fmt", "yuv420p",
                        "-f", "rawvideo", "-"], capture_output=True)
    n = L * A * 3 // 2
    if p.returncode != 0 or len(p.stdout) < n:
        return None
    d = p.stdout[:n]
    return d[:L * A], d[L * A:L * A + L * A // 4], d[L * A + L * A // 4:n]


def medie(rgb, L, riquadri):
    out = {}
    for q in riquadri:
        sr = sg = sb = 0
        n = q["w"] * q["h"]
        for r in range(q["y"], q["y"] + q["h"]):
            base = (r * L + q["x"]) * 3
            for c in range(q["w"]):
                sr += rgb[base]; sg += rgb[base + 1]; sb += rgb[base + 2]
                base += 3
        out[q["nome"]] = [sr / n, sg / n, sb / n]
    return out


def medie_yuv(piani, L, riquadri):
    """La media di Y, U e V dentro ogni riquadro.  ⚠ Il croma è a metà misura:
    i riquadri hanno bordi pari apposta."""
    Y, U, V = piani
    out = {}
    for q in riquadri:
        sy = 0
        for r in range(q["y"], q["y"] + q["h"]):
            base = r * L + q["x"]
            sy += sum(Y[base:base + q["w"]])
        ny = q["w"] * q["h"]
        x0, x1 = q["x"] // 2, max(q["x"] // 2 + 1, (q["x"] + q["w"]) // 2)
        y0, y1 = q["y"] // 2, max(q["y"] // 2 + 1, (q["y"] + q["h"]) // 2)
        su = sv = 0
        for r in range(y0, y1):
            base = r * (L // 2)
            su += sum(U[base + x0:base + x1])
            sv += sum(V[base + x0:base + x1])
        nc = (x1 - x0) * (y1 - y0)
        out[q["nome"]] = [sy / ny, su / nc, sv / nc]
    return out


def conversione_nostra(dati, L, A, riquadri):
    """⛔⭐ L'ALTRA METÀ DELLA DOMANDA «È NOSTRO O DEL DECODIFICATORE?».

    Il decodificatore lo si guarda dal browser; ma prima del decodificatore
    c'è un passo **nostro** che nessuno aveva misurato: `src/codificatore.c`
    (righe 1630-1636) converte i pixel della cattura — BGRx, intervallo pieno —
    in YUV con `sws_setColorspaceDetails(ITU709, sorgente PIENA, uscita
    LIMITATA)`.  Se quella riga fosse sbagliata, il colore sarebbe storto **a
    monte**, e nessuna misura sul browser lo direbbe: si accuserebbe il
    decodificatore di uno sbaglio nostro.

    Qui si rifà lo stesso passo con ffmpeg e si chiude il giro: RGB → YUV deve
    riportare ai campioni YUV da cui l'RGB è nato.

    ⚠ Si giudicano solo i riquadri il cui RGB non è appoggiato a 0 o a 255: il
      quadro di mezzo è un PNG a 8 bit, e un canale tagliato lì non può tornare
      indietro — contarlo accuserebbe la conversione di una perdita del
      formato di appoggio.
    ⛔ E il controllo negativo sta sull'USCITA, non sull'ingresso: per una
      sorgente RGB swscale ignora `in_range` (l'RGB è pieno per definizione), e
      un controllo messo lì non muove un livello — cioè non è un controllo."""
    dentro = [q for q in riquadri if all(0.5 < v < 254.5 for v in q["rgb_709tv"])]

    def giro(filtro):
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(dati, "scena.png"),
                            "-vf", filtro, "-f", "rawvideo", "-"], capture_output=True)
        n = L * A * 3 // 2
        if p.returncode or len(p.stdout) < n:
            return None
        d = p.stdout[:n]
        return medie_yuv((d[:L * A], d[L * A:L * A + L * A // 4],
                          d[L * A + L * A // 4:n]), L, riquadri)

    giusta = giro("scale=in_range=full:out_range=limited:out_color_matrix=bt709,format=yuv420p")
    storta = giro("scale=out_range=full:out_color_matrix=bt709,format=yuv420p")
    if not giusta or not storta:
        return {"errore": "ffmpeg non ha convertito"}
    fuori = {"riquadri": len(dentro)}
    for k, nome in enumerate("YUV"):
        e = [abs(giusta[q["nome"]][k] - q[nome]) for q in dentro]
        fuori[nome] = {"medio": sum(e) / len(e), "peggio": max(e)}
    pg = max(abs(storta[q["nome"]][0] - q["Y"]) for q in dentro)
    fuori["controllo_negativo_peggio_Y"] = pg
    fuori["il_controllo_vede"] = pg > 5
    return fuori


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--dati", default="/tmp/07-b62-dati")
    a.add_argument("--misura", default="1280x720")
    a.add_argument("--fotogrammi", type=int, default=30)
    o = a.parse_args()
    L, A = (int(x) for x in o.misura.split("x"))
    if L % 256 or A % 8:
        print("⛔ la rampa vuole una larghezza multipla di 256 e un'altezza di 8")
        return 2
    os.makedirs(o.dati, exist_ok=True)

    print("⏳ 1/5 · fabbrico la scena %dx%d in YUV" % (L, A))
    Y, U, V, riquadri = costruisci_scena(L, A)
    grezzo = os.path.join(o.dati, "scena.yuv")
    with open(grezzo, "wb") as f:
        f.write(Y); f.write(U); f.write(V)

    # ⭐ L'RGB atteso è la FORMULA applicata ai campioni, non una conversione.
    for q in riquadri:
        q["rgb_709tv"] = [round(x, 3) for x in rgb_da_yuv(q["Y"], q["U"], q["V"], "bt709", False)]
        q["rgb_601tv"] = [round(x, 3) for x in rgb_da_yuv(q["Y"], q["U"], q["V"], "bt601", False)]
        q["rgb_709pc"] = [round(x, 3) for x in rgb_da_yuv(q["Y"], q["U"], q["V"], "bt709", True)]

    print("⏳ 2/5 · il PNG della stessa scena (per l'occhio e per la catena vera)")
    righe = []
    for r in range(A):
        riga = bytearray()
        for c in range(L):
            rr, gg, bb = rgb_da_yuv(Y[r * L + c],
                                    U[(r // 2) * (L // 2) + c // 2],
                                    V[(r // 2) * (L // 2) + c // 2], "bt709", False)
            riga += bytes((round(rr), round(gg), round(bb)))
        righe.append(bytes(riga))
    scrivi_png(os.path.join(o.dati, "scena.png"), L, A, righe)

    print("⏳ 3/5 · codifico UNA volta per motore, poi riscrivo la sola VUI")
    fatte = {}
    for motore in ("vaapi", "x264"):
        v = "%s-dichiarato" % motore
        f, err = codifica(o.dati, v, grezzo, L, A, o.fotogrammi, motore)
        if not f:
            print("   ⛔ %-28s NON codificata: %s" % (v, err))
            continue
        fatte[v] = f
        print("   ⭐ %-28s %8d byte" % (v, os.path.getsize(f)))
        for nome, opz in VARIANTI.items():
            if opz is None:
                continue
            w = "%s-%s" % (motore, nome)
            u = os.path.join(o.dati, w + ".264")
            fatto, err = riscrivi_vui(f, u, opz)
            if not fatto:
                print("   ⛔ %-28s: %s" % (w, err))
                continue
            fatte[w] = u
            # ⛔ E si CONTROLLA che i campioni non siano cambiati: se la
            #    riscrittura toccasse più della VUI, l'esperimento avrebbe due
            #    variabili e nessuno se ne accorgerebbe.
            d0 = os.path.getsize(f)
            d1 = os.path.getsize(u)
            print("   ⭐ %-28s %8d byte (VUI riscritta, %+d byte sul flusso)"
                  % (w, d1, d1 - d0))

    print("⏳ 4/5 · l'indice dei pezzi e quel che ffprobe legge")
    riferimento = {}
    # ⚠ Il «dichiarato» per primo: è il metro con cui si confrontano gli altri.
    for v, f in sorted(fatte.items(),
                       key=lambda t: (t[0].split("-")[0],
                                      0 if t[0].endswith("-dichiarato")
                                      and t[0].count("-") == 1 else 1, t[0])):
        ind = indice_annexb(f)
        json.dump(ind, open(os.path.join(o.dati, v + ".json"), "w"))
        col = ffprobe_colore(f)
        rgb = ffmpeg_in_rgb(f, L, A)
        # ⛔ E la stessa lettura CHIEDENDO la matrice per nome: la differenza
        #    fra le due righe dice se il difetto di swscale è la matrice del
        #    flusso o un'altra.
        rgb709 = ffmpeg_in_rgb(f, L, A,
                               "scale=in_color_matrix=bt709:in_range=tv:"
                               "out_range=full:flags=full_chroma_int+accurate_rnd")
        piani = ffmpeg_in_yuv(f, L, A)
        myuv = medie_yuv(piani, L, riquadri) if piani else None
        atteso = None
        if myuv:
            # ⭐ L'ATTESO DI QUESTA VARIANTE: la formula applicata ai campioni
            #    DECODIFICATI ⇒ la perdita del codificatore esce dal conto, e
            #    resta solo la conversione di colore.
            atteso = {n: {"yuv": [round(x, 3) for x in m],
                          "709tv": [round(x, 3) for x in rgb_da_yuv(m[0], m[1], m[2], "bt709", False)],
                          "601tv": [round(x, 3) for x in rgb_da_yuv(m[0], m[1], m[2], "bt601", False)],
                          "709pc": [round(x, 3) for x in rgb_da_yuv(m[0], m[1], m[2], "bt709", True)]}
                      for n, m in myuv.items()}
        riferimento[v] = {
            "pezzi": len(ind["pezzi"]), "chiavi": sum(ind["chiave"]),
            "ffprobe": col,
            "atteso_dai_campioni_decodificati": atteso,
            "ffmpeg_rgb": medie(rgb, L, riquadri) if rgb else None,
            "ffmpeg_rgb_709_chiesta": medie(rgb709, L, riquadri) if rgb709 else None,
        }
        # ⛔⭐ LA PROVA CHE LA VARIABILE È UNA SOLA: i campioni decodificati
        #     delle varianti devono essere IDENTICI a quelli del «dichiarato»
        #     dello stesso motore.  Se non lo sono, l'esperimento ne ha due.
        gemello = v.split("-")[0] + "-dichiarato"
        stessi = "—"
        if myuv and gemello in riferimento and riferimento[gemello].get(
                "atteso_dai_campioni_decodificati"):
            g = riferimento[gemello]["atteso_dai_campioni_decodificati"]
            peggio = max(abs(myuv[n][k] - g[n]["yuv"][k])
                         for n in myuv for k in range(3))
            # ⚠ La tolleranza è 0,001 e non 0 perché il gemello è riletto da
            #   JSON con tre decimali: un `== 0` qui accuserebbe l'arrotondamento
            #   della scrittura e direbbe «campioni diversi» di byte identici.
            stessi = "campioni identici al «dichiarato»" if peggio <= 0.001 \
                else "⛔ campioni DIVERSI: fino a %.3f" % peggio
        print("   %-28s %3d pezzi (%d chiavi) · ffprobe: %s / %s · %s"
              % (v, len(ind["pezzi"]), sum(ind["chiave"]),
                 col.get("color_space", "—"), col.get("color_range", "—"), stessi))

    print("⏳ 5/5 · il pezzo NOSTRO: BGRx pieno → YUV 709 limitato, e verita.json")
    cn = conversione_nostra(o.dati, L, A, riquadri)
    riferimento["conversione_del_prodotto"] = cn
    if "errore" not in cn:
        print("   %d riquadri: Y medio %.3f/peggio %.3f · U %.3f/%.3f · V %.3f/%.3f"
              % (cn["riquadri"], cn["Y"]["medio"], cn["Y"]["peggio"],
                 cn["U"]["medio"], cn["U"]["peggio"], cn["V"]["medio"], cn["V"]["peggio"]))
        print("   controllo negativo (uscita dichiarata PIENA per sbaglio): "
              "peggio su Y %.1f ⇒ il confronto %s"
              % (cn["controllo_negativo_peggio_Y"],
                 "sa vedere il difetto" if cn["il_controllo_vede"] else "⛔ È CIECO"))
    json.dump(riferimento, open(os.path.join(o.dati, "riferimento.json"), "w"))
    json.dump({"l": L, "a": A, "riquadri": riquadri,
               "varianti": sorted(fatte)},
              open(os.path.join(o.dati, "verita.json"), "w"))
    json.dump(riferimento, open(os.path.join(o.dati, "riferimento.json"), "w"))
    for n in ("07-b62-colore.html",):
        shutil.copy(os.path.join(QUI, n), os.path.join(o.dati, "index.html"))
    print("⭐ pronto in %s — %d riquadri, %d varianti"
          % (o.dati, len(riquadri), len(fatte)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
