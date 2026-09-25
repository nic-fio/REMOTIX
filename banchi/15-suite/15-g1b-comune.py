#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g1b-comune — gli attrezzi del gruppo G1b («il desktop si comporta da desktop
remoto»: F-010, F-029, F-030).  Importato, non eseguito.

  · clic e tasti VERI dati al browser (CDP `Input.dispatch*` su Chrome, azioni
    W3C di Marionette su Firefox), in coordinate del DESKTOP;
  · l'OCR della fotografia (tesseract, se c'e': vedi `TESSERACT`);
  · la lettura di un campo DENTRO la sessione dell'inquilino.
"""
import io
import os
import re
import subprocess
import tempfile
import time

# ⭐ tesseract NON e' installato nel sistema del server (rootfs in RAM, e le
#   prove non installano pacchetti): e' ESTRATTO dai .deb di Trixie
#   (tesseract-ocr 5.5.0, libtesseract5, libleptonica6, dati eng/ita/osd) in
#   una cartella del disco persistente, senza root.  Si rifa' con:
#     cd /tmp && apt-get download tesseract-ocr libtesseract5 libleptonica6 \
#        tesseract-ocr-eng tesseract-ocr-osd tesseract-ocr-ita && \
#     for f in *.deb; do dpkg-deb -x $f /media/REMOTIX/strumenti/tesseract; done
TESSERACT = os.environ.get("REMOTIX_TESSERACT", "/media/REMOTIX/strumenti/tesseract")


def ocr_disponibile():
    return os.path.exists(os.path.join(TESSERACT, "usr", "bin", "tesseract"))


def ocr(png, riquadro=None, ingrandisci=2, psm=11, soglia=None):
    """Le parole lette nella foto: [(testo, x, y, w, h, fiducia)] in pixel
    della FOTO (non del ritaglio).  None se tesseract non c'e'.
    `soglia`: il ritaglio si porta a testo SCURO su fondo chiaro (si inverte
    se e' scuro in media) e si binarizza — `[M]` 24 set 2026: il menu scuro di
    GNOME in grigio non si legge, binarizzato a 110 si'."""
    if not ocr_disponibile():
        return None
    from PIL import Image, ImageOps, ImageStat
    im = Image.open(io.BytesIO(png)).convert("L")
    ox, oy = 0, 0
    if riquadro:
        x0, y0, x1, y1 = [int(v) for v in riquadro]
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(im.size[0], x1), min(im.size[1], y1)
        im = im.crop((x0, y0, x1, y1))
        ox, oy = x0, y0
    if ingrandisci != 1:
        im = im.resize((im.size[0] * ingrandisci, im.size[1] * ingrandisci), Image.LANCZOS)
    if soglia is not None:
        if ImageStat.Stat(im).mean[0] < 128:
            im = ImageOps.invert(im)
        im = im.point(lambda v: 0 if v < soglia else 255)
    amb = dict(os.environ,
               LD_LIBRARY_PATH=os.path.join(TESSERACT, "usr", "lib", "x86_64-linux-gnu"),
               TESSDATA_PREFIX=os.path.join(TESSERACT, "usr", "share", "tesseract-ocr", "5",
                                            "tessdata"),
               OMP_THREAD_LIMIT="2")
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "in.png")
        im.save(f)
        r = subprocess.run([os.path.join(TESSERACT, "usr", "bin", "tesseract"), f, "stdout",
                            "-l", "eng+ita", "--psm", str(psm), "tsv"],
                           capture_output=True, text=True, env=amb, timeout=120)
    parole = []
    for riga in r.stdout.splitlines()[1:]:
        c = riga.split("\t")
        if len(c) < 12 or not c[11].strip():
            continue
        try:
            conf = float(c[10])
        except ValueError:
            conf = -1
        x, y, w, h = [int(v) / ingrandisci for v in c[6:10]]
        parole.append((c[11].strip(), ox + x, oy + y, w, h, conf))
    return parole


def testo_di(parole):
    return " ".join(p[0] for p in parole or [])


def cerca_parola(parole, modello):
    """La prima parola (testo, x, y, w, h, conf) che corrisponde a `modello`
    (regex, senza maiuscole/minuscole)."""
    rx = re.compile(modello, re.I)
    for p in parole or []:
        if rx.search(p[0]):
            return p
    return None


def cerca_frase(parole, modello):
    """Come `cerca_parola` ma su righe ricostruite: torna (frase, x, y) del
    primo gruppo di parole vicine (stessa riga) che corrisponde."""
    rx = re.compile(modello, re.I)
    righe = []
    for p in sorted(parole or [], key=lambda q: (round(q[2] / 12), q[1])):
        if righe and abs(righe[-1][-1][2] - p[2]) < 10 and \
                p[1] - (righe[-1][-1][1] + righe[-1][-1][3]) < 40:
            righe[-1].append(p)
        else:
            righe.append([p])
    for r in righe:
        frase = " ".join(q[0] for q in r)
        if rx.search(frase):
            return frase, r[0][1], r[0][2] + r[0][4] / 2
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  IL MOUSE E I TASTI, VERI
# ═══════════════════════════════════════════════════════════════════════════
def dal_desktop_al_vetro(geo, X, Y):
    return (geo["left"] + (geo["bx0"] + X * geo["sx"]) * geo["vx"],
            geo["top"] + (geo["by0"] + Y * geo["sy"]) * geo["vy"])


def dalla_foto_al_desktop(geo, pw, ph, px, py):
    return ((px * geo["bw"] / pw - geo["bx0"]) / geo["sx"],
            (py * geo["bh"] / ph - geo["by0"]) / geo["sy"])


def clic_desktop(s, geo, X, Y, bottone=0):
    """Un clic vero nel punto (X, Y) del desktop.  bottone 0 sinistro, 2 destro."""
    g = s.g
    x, y = dal_desktop_al_vetro(geo, X, Y)
    if hasattr(g, "cdp"):
        nome = {0: "left", 1: "middle", 2: "right"}[bottone]
        try:
            g.cdp.chiama("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
        except RuntimeError:
            # ⚠ `[M]` 24 set 2026, server a carico 40: «Internal error» sul
            #   primo evento; il secondo passa
            time.sleep(1.5)
            g.cdp.chiama("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
        time.sleep(0.15)
        g.cdp.chiama("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y,
                     button=nome, clickCount=1)
        time.sleep(0.08)
        g.cdp.chiama("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y,
                     button=nome, clickCount=1)
        return
    g._azioni([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                             "origin": "viewport", "duration": 0},
                            {"type": "pause", "duration": 150},
                            {"type": "pointerDown", "button": bottone},
                            {"type": "pause", "duration": 80},
                            {"type": "pointerUp", "button": bottone}]}])


def muovi_desktop(s, geo, X, Y):
    x, y = dal_desktop_al_vetro(geo, X, Y)
    s.g.muovi(x, y)


#  nome: (key, code, vk, WebDriver, bit dei modificatori CDP)
TASTI = {
    "Alt": ("Alt", "AltLeft", 18, "", 1),
    "Control": ("Control", "ControlLeft", 17, "", 2),
    "Ctrl": ("Control", "ControlLeft", 17, "", 2),
    "Super": ("Meta", "MetaLeft", 91, "", 4),
    "Meta": ("Meta", "MetaLeft", 91, "", 4),
    "Shift": ("Shift", "ShiftLeft", 16, "", 8),
    "Tab": ("Tab", "Tab", 9, "", 0),
    "Escape": ("Escape", "Escape", 27, "", 0),
    "Esc": ("Escape", "Escape", 27, "", 0),
    "Enter": ("Enter", "Enter", 13, "", 0),
    "Space": (" ", "Space", 32, " ", 0),
    "F1": ("F1", "F1", 112, "", 0),
    "F2": ("F2", "F2", 113, "", 0),
    "Delete": ("Delete", "Delete", 46, "", 0),
}


def _tasto(nome):
    if nome in TASTI:
        return TASTI[nome]
    if len(nome) == 1 and nome.isalnum():
        c = nome.lower()
        code = ("Key" + c.upper()) if c.isalpha() else ("Digit" + c)
        return (c, code, ord(c.upper()), c, 0)
    raise KeyError(nome)


def combinazione(g, nomi, tieni_ms=120):
    """Preme i tasti in ordine, li tiene, li rilascia al contrario (una
    combinazione vera: Alt giu', Tab giu', Tab su, Alt su)."""
    tasti = [_tasto(n) for n in nomi]
    if hasattr(g, "cdp"):
        mod = 0
        for key, code, vk, _w, bit in tasti:
            mod |= bit
            p = dict(type="rawKeyDown", key=key, code=code, windowsVirtualKeyCode=vk,
                     modifiers=mod)
            g.cdp.chiama("Input.dispatchKeyEvent", **p)
            time.sleep(0.06)
        time.sleep(tieni_ms / 1000.0)
        for key, code, vk, _w, bit in reversed(tasti):
            mod &= ~bit
            g.cdp.chiama("Input.dispatchKeyEvent", type="keyUp", key=key, code=code,
                         windowsVirtualKeyCode=vk, modifiers=mod)
            time.sleep(0.06)
        return
    az = []
    for t in tasti:
        az += [{"type": "keyDown", "value": t[3]}, {"type": "pause", "duration": 60}]
    az.append({"type": "pause", "duration": tieni_ms})
    for t in reversed(tasti):
        az += [{"type": "keyUp", "value": t[3]}, {"type": "pause", "duration": 60}]
    g.m.chiama("WebDriver:PerformActions",
               {"actions": [{"type": "key", "id": "tastiera", "actions": az}]})
    g.m.chiama("WebDriver:ReleaseActions")


def fuoco_sulla_tela(s, geo):
    """Toglie il fuoco dal modulo e porta il puntatore sulla tela, come fa
    l'utente prima di scrivere (senza cliccare: un clic cadrebbe nel desktop)."""
    try:
        s.g.js("if (document.activeElement && document.activeElement.blur) "
               "document.activeElement.blur(); "
               "const t=document.getElementById('schermo'); if (t && t.focus) t.focus(); "
               "return 1;")
    except Exception:                            # noqa: BLE001
        pass
    muovi_desktop(s, geo, geo["tl"] * 0.5, geo["ta"] * 0.6)
    time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════════════════
#  LE FOTO
# ═══════════════════════════════════════════════════════════════════════════
def immagine(png):
    from PIL import Image
    return Image.open(io.BytesIO(png)).convert("RGB")


def differenza(png_a, png_b, riquadro=None, passo=4, soglia=40):
    """La frazione dei pixel campionati che cambia fra due foto (0..1)."""
    a, b = immagine(png_a), immagine(png_b)
    if a.size != b.size:
        return 1.0
    if riquadro:
        a, b = a.crop(riquadro), b.crop(riquadro)
    pa, pb = a.load(), b.load()
    n = cambiati = 0
    for y in range(0, a.size[1], passo):
        for x in range(0, a.size[0], passo):
            n += 1
            p, q = pa[x, y], pb[x, y]
            if abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > soglia:
                cambiati += 1
    return cambiati / max(1, n)


def luminanza_media(png, passo=8):
    im = immagine(png)
    px = im.load()
    t = n = 0
    for y in range(0, im.size[1], passo):
        for x in range(0, im.size[0], passo):
            r, g, b = px[x, y]
            t += 0.299 * r + 0.587 * g + 0.114 * b
            n += 1
    return t / max(1, n)


def png_nero(w, h):
    import struct
    import zlib
    riga = b"\x00" + b"\x00\x00\x00" * w
    dati = zlib.compress(riga * h, 9)

    def pezzo(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n" + pezzo(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + pezzo(b"IDAT", dati) + pezzo(b"IEND", b""))


def misura_png(png):
    import struct
    return struct.unpack(">II", png[16:24])


# ═══════════════════════════════════════════════════════════════════════════
#  DENTRO LA SESSIONE
# ═══════════════════════════════════════════════════════════════════════════
def nella_sessione(s, comando, secondi=60):
    """(codice, uscita) di `comando` eseguito come l'inquilino, con
    l'ambiente della sua sessione grafica (e l'XDG_CONFIG_DIRS del suo
    compositore, che su KDE porta il KIOSK di REMOTIX)."""
    return s.nella_sessione(comando, secondi, fondo=False)


def ambiente_di(s, processo):
    """Una variabile d'ambiente per nome, letta da /proc/<pid>/environ del
    primo processo dell'inquilino che si chiama `processo`: {nome: valore}."""
    c, t = s.sc.dentro(
        "p=$(pgrep -u %s -x %s | head -1); [ -n \"$p\" ] || exit 4; "
        "tr '\\0' '\\n' < /proc/$p/environ" % (s.chi, processo), 30)
    if c != 0:
        return {}
    amb = {}
    for riga in t.splitlines():
        k, _, v = riga.partition("=")
        if k:
            amb[k] = v
    return amb


def riquadro_cambiato(png_a, png_b, cella=8, soglia=60, margine=24, minimo=3, vicino=None):
    """⭐ Dove si e' aperto qualcosa: il riquadro (x0, y0, x1, y1) della MACCHIA
    PIU' GRANDE di celle cambiate fra due foto (celle di `cella` px, un pixel
    per cella, 8-vicini con un passo di tolleranza).  Serve a ritagliare il
    menu aperto per l'OCR: tesseract su un ritaglio largo di sfondo sbaglia la
    soglia e non legge niente (`[M]` 24 set 2026, GNOME: «Log Out…» letto nel
    ritaglio stretto, perso in quello largo).  None se non cambia niente."""
    a, b = immagine(png_a), immagine(png_b)
    if a.size != b.size:
        return None
    pa, pb = a.load(), b.load()
    W, H = a.size
    cw, ch = W // cella, H // cella
    acceso = set()
    for j in range(ch):
        y = j * cella + cella // 2
        for i in range(cw):
            x = i * cella + cella // 2
            if vicino and (x - vicino[0]) ** 2 + (y - vicino[1]) ** 2 > vicino[2] ** 2:
                continue
            p, q = pa[x, y], pb[x, y]
            if abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > soglia:
                acceso.add((i, j))
    visti, migliore = set(), None
    for c in acceso:
        if c in visti:
            continue
        pila, blob = [c], []
        visti.add(c)
        while pila:
            i, j = pila.pop()
            blob.append((i, j))
            for di in (-2, -1, 0, 1, 2):
                for dj in (-2, -1, 0, 1, 2):
                    v = (i + di, j + dj)
                    if v in acceso and v not in visti:
                        visti.add(v)
                        pila.append(v)
        if migliore is None or len(blob) > len(migliore):
            migliore = blob
    if not migliore or len(migliore) < minimo:
        return None
    xs = [c[0] for c in migliore]
    ys = [c[1] for c in migliore]
    return (max(0, min(xs) * cella - margine), max(0, min(ys) * cella - margine),
            min(W, (max(xs) + 1) * cella + margine), min(H, (max(ys) + 1) * cella + margine))


def leggi_riquadro(png, riquadro, ingrandisci=3):
    """OCR del riquadro in tre letture (grigio psm 11; binarizzato a 110 psm 6;
    a 150 psm 11).  Torna (righe, testo): le RIGHE di ogni lettura, messe
    insieme — una voce letta da una sola delle tre conta (per le vietate si
    vuole il piu' sensibile).  (None, motivo) se tesseract non c'e'."""
    if not ocr_disponibile():
        return None, "tesseract non c'e' in %s" % TESSERACT
    tutte = []
    for psm, soglia in ((11, None), (6, 110), (11, 150)):
        p = ocr(png, riquadro, ingrandisci=ingrandisci, psm=psm, soglia=soglia) or []
        tutte += righe_di(p)
        leggi_riquadro.parole = getattr(leggi_riquadro, "parole", []) + p
    return tutte, " | ".join(r[0] for r in tutte)


def parole_lette():
    """Le parole (con la posizione) delle letture fatte da `leggi_riquadro`
    dall'ultima `azzera_parole()`."""
    return list(getattr(leggi_riquadro, "parole", []))


def azzera_parole():
    leggi_riquadro.parole = []


def righe_di(parole, passo_y=14):
    """Le parole rimesse in righe: [(frase, x, y)] ordinate dall'alto.  Una
    riga = le parole col centro alla stessa altezza (±passo_y), in ordine di x.
    Le tre letture danno doppioni: dentro una riga si tolgono le parole che
    si sovrappongono a una gia' presa, e si tolgono le righe uguali vicine.
    ⚠ Due menu affiancati alla stessa altezza finiscono nella stessa riga: per
      il giudizio va bene (si cercano parole, non si contano voci)."""
    righe = []
    for p in sorted(parole or [], key=lambda q: q[2] + q[4] / 2):
        cy = p[2] + p[4] / 2
        for r in righe:
            if abs(r["y"] - cy) < passo_y:
                r["p"].append(p)
                break
        else:
            righe.append({"y": cy, "p": [p]})
    fuori = []
    for r in sorted(righe, key=lambda r: r["y"]):
        prese = []
        for p in sorted(r["p"], key=lambda q: (-q[5], q[1])):
            if any(p[1] < q[1] + q[3] and q[1] < p[1] + p[3] for q in prese):
                continue
            prese.append(p)
        prese.sort(key=lambda q: q[1])
        fuori.append((" ".join(q[0] for q in prese), prese[0][1], r["y"]))
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
#  LE FINESTRE NOTE (GTK4: c'e' in tutte e quattro le scatole)
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ Una finestra PIENA di un colore puro, con un app_id suo: su GNOME Alt+Tab
#   passa fra APPLICAZIONI, e due finestre dello stesso programma sarebbero
#   una sola voce.  `[M]` 24 set 2026: GTK3 c'e' solo nella scatola gnome,
#   GTK4 in tutte.
FINESTRA_GTK = r'''
import sys
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
import time
from gi.repository import GLib
nome, colore, largo, alto = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
# opzionale: un secondo colore e un periodo — la finestra cambia colore da sola
# (colore se (ora // periodo) e' pari, altro se dispari), SENZA input: e' la
# prova che l'immagine e' viva e non un fotogramma congelato
altro = sys.argv[5] if len(sys.argv) > 5 else None
periodo = int(sys.argv[6]) if len(sys.argv) > 6 else 30
app = Gtk.Application(application_id="org.remotix.c15" + nome)
def regola(c):
    return ("window, window.background, headerbar, .titlebar { background: %s; "
            "background-image: none; }" % c)
def carica(css, testo):
    try:
        css.load_from_string(testo)
    except AttributeError:
        css.load_from_data(testo, -1)
def attiva(a):
    css = Gtk.CssProvider()
    carica(css, regola(colore))
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, 800)
    w = Gtk.ApplicationWindow(application=a, title="c15-" + nome)
    w.set_default_size(largo, alto)
    w.present()
    if altro:
        def gira():
            carica(css, regola(colore if int(time.time() // periodo) % 2 == 0 else altro))
            w.queue_draw()
            return True
        GLib.timeout_add(500, gira)
app.connect("activate", attiva)
app.run([])
'''


def metti_finestra(s):
    """Scrive il programma della finestra nella casa dell'inquilino."""
    import base64
    b = base64.b64encode(FINESTRA_GTK.encode()).decode()
    return s.sc.dentro("echo %s | base64 -d > /home/%s/.c15-finestra.py && chown %s: "
                       "/home/%s/.c15-finestra.py && echo scritta"
                       % (b, s.chi, s.chi, s.chi), 60)


def apri_finestra(s, nome, colore, largo, alto, altro=None, periodo=30):
    coda = " '%s' %d" % (altro, periodo) if altro else ""
    return s.nella_sessione("python3 /home/%s/.c15-finestra.py %s '%s' %d %d%s"
                            % (s.chi, nome, colore, largo, alto, coda), 60, fondo=True)


CIANO = (0, 255, 255)
MAGENTA = (255, 0, 255)


def conta_colori(png, colori, passo=6, toll=50):
    """{colore: frazione dei pixel campionati vicini a quel colore}."""
    im = immagine(png)
    px = im.load()
    n = 0
    conti = {c: 0 for c in colori}
    for y in range(0, im.size[1], passo):
        for x in range(0, im.size[0], passo):
            p = px[x, y]
            n += 1
            for c in colori:
                if abs(p[0] - c[0]) + abs(p[1] - c[1]) + abs(p[2] - c[2]) < toll:
                    conti[c] += 1
                    break
    return {c: v / max(1, n) for c, v in conti.items()}


def vivi(png, passo=6, soglia=24):
    """La frazione dei pixel NON quasi neri: uno schermo spento e' tutto nero,
    anche dove il desktop era gia' scuro (XFCE nasce con lo sfondo nero)."""
    im = immagine(png)
    px = im.load()
    n = v = 0
    for y in range(0, im.size[1], passo):
        for x in range(0, im.size[0], passo):
            r, g, b = px[x, y]
            n += 1
            v += (0.299 * r + 0.587 * g + 0.114 * b) > soglia
    return v / max(1, n)


def aspetta_apertura(s, png_prima, nome, vicino, tetto_s=10.0, lato_min=120):
    """Fotografa finche' vicino al clic si apre qualcosa di almeno
    `lato_min` x `lato_min` px (un menu, non l'evidenza di un pulsante).
    Torna (png, percorso, riquadro | None)."""
    fine = time.time() + tetto_s
    png, dove, r = None, "", None
    while True:
        time.sleep(1.5)
        png, dove = foto(s, nome)
        if png:
            r = riquadro_cambiato(png_prima, png, vicino=vicino)
            if r and r[2] - r[0] >= lato_min and r[3] - r[1] >= lato_min:
                return png, dove, r
        if time.time() > fine:
            return png, dove, r


# ⭐ `[M]` 24 set 2026: su una tela FERMA (il desktop non cambia, REMOTIX non
#   manda fotogrammi) `Page.captureScreenshot` di Chrome nel labwc senza schermo
#   impiega ~60 s — aspetta un fotogramma che nessuno disegna.  Un puntino di
#   1 px che cambia colore a ogni foto da' al compositore del browser un danno
#   da disegnare, e la foto torna subito.  Sta nell'angolo in alto a sinistra
#   della PAGINA, fuori dalla tela? No: la tela copre tutto — sta SOPRA, 1 px,
#   e cambia fra due grigi quasi uguali; nei giudizi pesa 1 pixel su 8 milioni.
JS_PUNGOLO = r"""
let p = document.getElementById('c15-pungolo');
if (!p) { p = document.createElement('div'); p.id = 'c15-pungolo';
  p.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;z-index:2147483647;pointer-events:none';
  document.body.appendChild(p); }
p.style.background = p.style.background === 'rgb(1, 1, 1)' ? 'rgb(2, 2, 2)' : 'rgb(1, 1, 1)';
return 1;
"""


def pungola(s):
    try:
        s.g.js(JS_PUNGOLO)
    except Exception:                            # noqa: BLE001
        pass


def foto(s, nome, scala=1.0, tentativi=3):
    """La foto della tela, RITENTATA (`[M]` 24 set 2026: col server a carico
    25-50 la cattura a 4K di Chrome scade).  `scala` < 1 solo su Chrome (CDP
    la sa ridurre; Marionette no): per i giudizi sui colori basta la meta',
    per l'OCR serve la scala 1.  Torna (png | None, percorso | motivo)."""
    import base64
    ultimo = ""
    for _ in range(tentativi):
        pungola(s)
        if scala < 1 and hasattr(s.g, "cdp"):
            try:
                r = s.g.js("const t=document.getElementById('schermo');"
                           "if(!t) return null; const b=t.getBoundingClientRect();"
                           "return [b.left, b.top, b.width, b.height];")
                if not r:
                    ultimo = "la tela non c'e'"
                    time.sleep(2)
                    continue
                c = s.g.cdp.chiama("Page.captureScreenshot", format="png",
                                   clip={"x": r[0], "y": r[1], "width": r[2],
                                         "height": r[3], "scale": scala})
                png = base64.b64decode(c["data"])
                s._foto += 1
                dove = ""
                if s.o.evidenze:
                    dove = os.path.join(s.o.evidenze, "%02d-%s.png" % (s._foto, nome))
                    with open(dove, "wb") as f:
                        f.write(png)
                return png, dove
            except Exception as e:               # noqa: BLE001
                ultimo = "fotografia fallita: %s" % str(e)[:200]
                passo("⚠ foto %s: %s" % (nome, ultimo))
        else:
            png, dove = s.foto(nome)
            if png:
                return png, dove
            ultimo = dove
            passo("⚠ foto %s: %s" % (nome, ultimo))
        time.sleep(3)
    return None, ultimo


_T0 = time.time()


def passo(testo):
    """Una riga col tempo trascorso dall'avvio: dove va il tempo della prova."""
    print("   [%5.0f s] %s" % (time.time() - _T0, testo), flush=True)
