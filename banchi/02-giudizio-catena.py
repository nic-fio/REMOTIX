#!/usr/bin/env python3
"""02-giudizio-catena.py — ⭐⭐ I PIXEL DELLA TELA DEL PRODOTTO, PORTATI FUORI
   DAL BROWSER.  E' l'altra meta' di `P2-6-montaggio.md` §7 punto 1.

   Lo lancia `02-giudizio-catena.sh`, che apparecchia la scena e poi punta il
   metro di F2.6 sui file che questo programma scrive.

===========================================================================
⛔ CHE COSA MANCAVA, DETTO CON LE PAROLE DI CHI L'HA DICHIARATO

`P2-6` §7 punto 1: *«il metro a due piani sulla catena vera: serve
`getImageData` **dalla pagina** e un canale che riporti i pixel al banco.»*
`02-pagina-misura-prova.py` ne ha fatto meta' il 13 agosto — legge la tela con
`getImageData` e ne ricava **tre numeri** (campioni, scarto, frazione nera),
che bastano a dire *«ha dipinto qualcosa»* e ⛔ **non bastano a dire che cosa**.

⇒ Qui si porta fuori **l'immagine intera**, byte per byte, perche' il metro
  possa confrontarla con la decodifica di riferimento di `ffmpeg`.

===========================================================================
⛔⭐ IL CANALE, E PERCHE' E' QUESTO E NON UN'ALTRA COSA

`src/pagina.html` **non ha e non deve avere** un modo di consegnare i propri
pixel a un banco — e' la decisione di `P2-6` §7 punto 1, e il mandato di oggi
la conferma vietando di toccare `src/`.  ⇒ Il canale e' **CDP**, cioe' lo
stesso `Runtime.evaluate` con cui si guarda una pagina qualunque da fuori: il
prodotto gira **identico** che questo file ci sia o no, e non c'e' nessuna
riga di banco dentro il prodotto.

⚠ E i pixel non si leggono in una volta sola: 1920×1080 RGB sono 6 220 800
  byte, e in base64 sono 8,3 MB dentro **un** messaggio WebSocket.  Si
  impacchettano una volta in `window.__CATENA__` e si leggono a fette, e ogni
  fetta porta la propria lunghezza: cosi' un troncamento si vede invece di
  diventare un'immagine piu' corta — che il metro leggerebbe come «il file non
  e' della misura dichiarata» invece che come «il canale ha perso dei byte».

===========================================================================
⛔⛔ LA VISTA DEV'ESSERE ESATTAMENTE LA TELA, O NON SI MISURA LA DECODIFICA

Dal 13 agosto la pagina **riscala alla vista** (`SPECIFICHE.md` §6.1-bis,
`RCP.md` §6.2), e la tela e' il **buffer della vista**, non del fotogramma.
⇒ Su una finestra qualunque `getImageData` restituisce il fotogramma
**ricampionato dal browser**, con le bande nere intorno: confrontarlo con la
decodifica di `ffmpeg` misurerebbe **il ricampionamento di Chrome**, non la
decodifica.

⚠ E il metro lo dice gia' da parte sua: *«la tela non si ridimensiona: il
  metro rifiuta di scalare un ingresso, perche' ridimensionare significa
  confrontare due immagini che nessuno ha prodotto»* (`F2-6` §«Le cuciture»).
  ⇒ Qui la vista si porta a essere **esattamente** la tela, e poi lo si
  **verifica sui pixel** — buffer, misura dipinta, origine e scala — prima di
  leggere un solo byte.  Se non torna, si esce **2 (non misurato)**: non si
  consegna al metro un ingresso che nessuno ha prodotto.
"""
import argparse
import base64
import importlib.util
import json
import os
import sys
import time

_QUI = os.path.dirname(os.path.abspath(__file__))
_s = importlib.util.spec_from_file_location(
    "cdp", os.path.join(_QUI, "02-pagina-misura-cdp.py"))
cdp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(cdp)

VERDE, ROSSO, GIALLO, GRIGIO = ("\033[1;32m", "\033[1;31m", "\033[1;33m",
                                "\033[0m")


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


ENTRA = """
(function () {
  const u = document.getElementById("utente");
  const p = document.getElementById("parola");
  if (!u || !p) return "⛔ il modulo non c'e'";
  u.value = %s; p.value = %s;
  document.getElementById("modulo").requestSubmit();
  return "inviato";
})()
"""

# ⛔ La vista si LEGGE con la regola di §4.5 — `clientWidth × devicePixelRatio`
#    — invece di chiederla alla pagina: leggerla dalla pagina vorrebbe dire
#    confrontare il numero della pagina col numero della pagina.
STATO = """
(function () {
  const R = window.REMOTIX, sc = R && R.schermo;
  const d = document.documentElement, dpr = devicePixelRatio || 1;
  const t = document.getElementById("schermo");
  const f = { dpr: dpr,
              cliente: [d.clientWidth, d.clientHeight],
              vista: [Math.max(1, Math.round(d.clientWidth * dpr)),
                      Math.max(1, Math.round(d.clientHeight * dpr))],
              conti: sc ? sc.conti : null,
              errori: sc ? sc.errori : null,
              dichiarata: sc ? sc.dipinta : null,
              registro: (document.getElementById("registro") || {}).textContent,
              dichiarazione: (document.getElementById("dichiarazione") || {}).textContent };
  if (t) f.buffer = [t.width, t.height];
  return f;
})()
"""

# ⛔ Il rettangolo dei pixel ACCESI: e' l'unica misura che nessuno puo'
#    dichiarare al posto suo, e distingue «dipinto 1:1» da «dipinto piccolo in
#    mezzo al nero».  ⚠ Le bande sono nere per costruzione (`componi()` le
#    riempie di #000).
DIPINTA = """
(function () {
  const t = document.getElementById("schermo");
  if (!t || t.width < 32) return { guaio: "tela al minimo" };
  const p = t.getContext("2d", { willReadFrequently: true });
  const im = p.getImageData(0, 0, t.width, t.height).data;
  const SOGLIA = 60, MINIMI = 4;
  let x0 = -1, x1 = -1, y0 = -1, y1 = -1;
  const colonne = new Int32Array(t.width);
  for (let y = 0; y < t.height; y++) {
    let n = 0;
    for (let x = 0; x < t.width; x++) {
      const i = (y * t.width + x) * 4;
      if (im[i] + im[i + 1] + im[i + 2] > SOGLIA) { n++; colonne[x]++; }
    }
    if (n >= MINIMI) { if (y0 < 0) y0 = y; y1 = y; }
  }
  for (let x = 0; x < t.width; x++)
    if (colonne[x] >= MINIMI) { if (x0 < 0) x0 = x; x1 = x; }
  if (x1 < 0 || y1 < 0) return { guaio: "nessun pixel acceso" };
  return { dipinta: [x1 - x0 + 1, y1 - y0 + 1], origine: [x0, y0],
           buffer: [t.width, t.height] };
})()
"""

# ⛔ L'impacchettamento: da RGBA a RGB24, UNA volta, e poi si legge a fette.
#    ⚠ Si torna anche la lunghezza attesa, cosi' «il canale ha perso dei byte»
#      e «l'immagine e' di un'altra misura» non hanno la stessa faccia.
IMPACCHETTA = """
(function () {
  const t = document.getElementById("schermo");
  const p = t.getContext("2d", { willReadFrequently: true });
  const im = p.getImageData(0, 0, t.width, t.height).data;
  const n = t.width * t.height;
  const rgb = new Uint8Array(n * 3);
  for (let i = 0, j = 0; i < n; i++, j += 3) {
    const k = i * 4;
    rgb[j] = im[k]; rgb[j + 1] = im[k + 1]; rgb[j + 2] = im[k + 2];
  }
  window.__CATENA__ = rgb;
  return { byte: rgb.length, larghezza: t.width, altezza: t.height };
})()
"""

FETTA = """
(function () {
  const a = window.__CATENA__;
  if (!a) return null;
  const da = %d, quanti = Math.min(%d, a.length - %d);
  if (quanti <= 0) return { base64: "", byte: 0 };
  let s = "";
  const P = 8192;
  for (let i = da; i < da + quanti; i += P)
    s += String.fromCharCode.apply(null, a.subarray(i, Math.min(i + P, da + quanti)));
  return { base64: btoa(s), byte: quanti };
})()
"""


def aspetta(c, espressione, quanto, pronto, passo=0.5):
    fine = time.time() + quanto
    ultimo = None
    while time.time() < fine:
        ultimo = c.valuta(espressione, attendi=False)
        if ultimo and pronto(ultimo):
            return ultimo
        time.sleep(passo)
    return ultimo


def batti(c, testo):
    """⛔ «thisisunsafe» si BATTE, non si aggira con un flag: il certificato del
    prodotto e' il suo, e togliere l'interstiziale toglierebbe dalla misura
    proprio la cosa che l'utente fa la prima volta."""
    for ch in testo:
        for tipo in ("keyDown", "char", "keyUp"):
            p = {"type": tipo, "text": ch} if tipo == "char" else {"type": tipo}
            if tipo != "char":
                p["key"] = ch
            c.chiama("Input.dispatchKeyEvent", **p)
        time.sleep(0.03)


def viewport(c, l, a, dpr=1):
    c.chiama("Emulation.setDeviceMetricsOverride", width=l, height=a,
             deviceScaleFactor=dpr, mobile=False)


def fotografa(c, dove):
    """⛔ La fotografia si prende DALLA SCHEDA e NEL MOMENTO della misura: le
    sette fotografie identiche del 13 agosto erano `about:blank`, prese dopo
    che il programma era navigato via."""
    try:
        r = c.chiama("Page.captureScreenshot", format="png",
                     captureBeyondViewport=False)
        os.makedirs(os.path.dirname(dove) or ".", exist_ok=True)
        with open(dove, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        return os.path.getsize(dove)
    except Exception as e:                           # noqa: BLE001
        dub(f"⚠ la fotografia non e' riuscita: {e}")
        return 0


def giro(args):
    L, A = (int(x) for x in args.tela.split("x"))
    b = cdp.pagina(args.diagnosi)
    c = cdp.Cdp(b["webSocketDebuggerUrl"], timeout=120)
    fuori = {"tela_chiesta": [L, A], "url": args.url}
    try:
        c.chiama("Page.enable")
        c.chiama("Runtime.enable")
        c.chiama("Network.enable")
        c.chiama("Network.setCacheDisabled", cacheDisabled=True)

        log("1. La finestra, portata alla misura della tela")
        # ⚠ Si parte da un di piu' per la barra di scorrimento, e poi si
        #   CORREGGE su quel che il documento dichiara: indovinare 15 px
        #   funziona finche' il tema non cambia.
        larg, alt = L + 15, A
        viewport(c, larg, alt)
        c.chiama("Page.navigate", url=args.url)
        time.sleep(3)
        titolo = c.valuta("document.title", attendi=False)
        if (isinstance(titolo, str) and "Privacy" in titolo) or \
                c.valuta("!!document.getElementById('proceed-link')", attendi=False):
            inf("interstiziale del certificato: batto «thisisunsafe»")
            batti(c, "thisisunsafe")
            time.sleep(5)
        pronta = aspetta(c, "!!(window.REMOTIX && window.REMOTIX.schermo)",
                         args.attesa_sonda, lambda x: x is True)
        if pronta is not True:
            ko(f"⛔ la pagina non ha esposto REMOTIX: {pronta}")
            fuori["guaio"] = "REMOTIX assente"
            return fuori
        ok("la pagina del prodotto e' viva e ha esposto REMOTIX")

        for tentativo in range(4):
            s = c.valuta(STATO, attendi=False)
            v = s.get("vista") or [0, 0]
            if v == [L, A]:
                break
            larg += L - v[0]
            alt += A - v[1]
            inf(f"vista {v[0]}×{v[1]}, correggo la finestra a {larg}×{alt} CSS")
            viewport(c, larg, alt)
            time.sleep(0.8)
        s = c.valuta(STATO, attendi=False)
        fuori["stato_prima"] = s
        if (s.get("vista") or []) != [L, A]:
            ko(f"⛔ la vista e' {s.get('vista')} e non {L}×{A}: non porto fuori "
               f"pixel ricampionati")
            fuori["guaio"] = "vista diversa dalla tela"
            return fuori
        ok(f"⭐ vista = {L}×{A} = la tela: il fotogramma si dipingera' 1:1")

        log("2. Entro come l'utente, e aspetto il fotogramma")
        with open(args.parola_file) as f:
            parola = f.read().strip()
        c.valuta(ENTRA % (json.dumps(args.utente), json.dumps(parola)),
                 attendi=False)
        del parola
        inf(f"credenziali inviate per «{args.utente}» (mai da argv)")
        s = aspetta(c, STATO, args.attesa_video,
                    lambda x: (x.get("conti") or {}).get("dipinti", 0) > 0)
        fuori["stato"] = s
        conti = (s or {}).get("conti") or {}
        if conti.get("dipinti", 0) < 1:
            ko(f"⛔ nessun fotogramma dipinto in {args.attesa_video} s")
            inf(f"riquadro: {str((s or {}).get('dichiarazione'))[:300]}")
            inf(f"registro: {str((s or {}).get('registro'))[-600:]}")
            fuori["guaio"] = "niente dipinto"
            return fuori
        ok(f"⭐ fotogrammi dipinti: {conti.get('dipinti')} · "
           f"ricomposizioni: {conti.get('ricomposizioni')}")
        if s.get("dichiarata"):
            inf(f"la pagina dichiara di aver dipinto {s['dichiarata']}")

        if args.copia:
            n = fotografa(c, args.copia)
            if n:
                fuori["copia"] = args.copia
                inf(f"copia della SCHEDA MISURATA: {args.copia} ({n} byte)")

        log("3. ⛔ La verifica 1:1 — SUI PIXEL, prima di portarne fuori uno")
        d = c.valuta(DIPINTA, attendi=False)
        fuori["dipinta"] = d
        if not isinstance(d, dict) or d.get("guaio"):
            ko(f"⛔ non ho potuto misurare i pixel accesi: {d}")
            fuori["guaio"] = "pixel accesi non misurabili"
            return fuori
        guai = []
        if d["buffer"] != [L, A]:
            guai.append(f"il buffer della tela e' {d['buffer']} e non [{L}, {A}]")
        if d["dipinta"] != [L, A]:
            guai.append(f"l'immagine dipinta e' {d['dipinta']} e non [{L}, {A}]: "
                        f"il browser l'ha ricampionata, e un ingresso "
                        f"ricampionato misurerebbe il ricampionamento")
        if d["origine"] != [0, 0]:
            guai.append(f"l'immagine parte da {d['origine']} e non da [0, 0]")
        if guai:
            for g in guai:
                ko("⛔ " + g)
            fuori["guaio"] = "; ".join(guai)
            return fuori
        ok(f"⭐ buffer {d['buffer']}, dipinta {d['dipinta']} da {d['origine']}: "
           f"1:1, nessuna banda, nessun ricampionamento")

        log("4. I pixel, portati fuori dal browser")
        p = c.valuta(IMPACCHETTA, attendi=False)
        if not isinstance(p, dict) or not p.get("byte"):
            ko(f"⛔ l'impacchettamento non e' riuscito: {p}")
            fuori["guaio"] = "impacchettamento fallito"
            return fuori
        atteso = L * A * 3
        if p["byte"] != atteso:
            ko(f"⛔ la pagina ha impacchettato {p['byte']} byte, ne servivano "
               f"{atteso}")
            fuori["guaio"] = "misura sbagliata"
            return fuori
        inf(f"{p['byte']} byte da leggere, a fette di {args.fetta}")
        pezzi, letti = [], 0
        t0 = time.time()
        while letti < atteso:
            f = c.valuta(FETTA % (letti, args.fetta, letti), attendi=False)
            if not isinstance(f, dict) or not f.get("byte"):
                ko(f"⛔ la fetta a {letti} non e' arrivata: {f}")
                fuori["guaio"] = "fetta persa"
                return fuori
            crudo = base64.b64decode(f["base64"])
            # ⛔ Ogni fetta porta la propria lunghezza, e la si CONTROLLA: senza,
            #    un troncamento diventerebbe un'immagine piu' corta, e il metro
            #    direbbe «non e' della misura dichiarata» invece di «il canale
            #    ha perso dei byte».
            if len(crudo) != f["byte"]:
                ko(f"⛔ la fetta a {letti} dichiara {f['byte']} byte e ne porta "
                   f"{len(crudo)}")
                fuori["guaio"] = "fetta troncata"
                return fuori
            pezzi.append(crudo)
            letti += len(crudo)
        dati = b"".join(pezzi)
        with open(args.fuori_pixel, "wb") as f:
            f.write(dati)
        ok(f"⭐ {len(dati)} byte scritti in {args.fuori_pixel} in "
           f"{time.time() - t0:.1f} s ({len(pezzi)} fette)")
        fuori["pixel"] = {"file": args.fuori_pixel, "byte": len(dati),
                          "fette": len(pezzi)}

        # ⚠ La cucitura di F2.4: quel che la pagina DICHIARA di aver dipinto.
        #   Anello debole per costruzione — crede a chi e' sotto esame — e vale
        #   solo insieme al registro del filo.
        errori = (s.get("errori") or [])
        fuori["identita"] = {
            "giro": None, "fin_ricevuto": True,
            "reset_ricevuto": bool(conti.get("reset", 0)),
            "dipinto": True,
            "nota": ("dichiarata dalla pagina via CDP; M8 e' un anello debole "
                     "per costruzione (F2.6): crede a chi e' sotto esame"),
            "errori_pagina": errori}
        return fuori
    finally:
        # ⛔ IL POSTO SI LASCIA: il server lo libera dopo trenta secondi di
        #    silenzio (§4.4-bis), e un `kill` del browser non manda nessun
        #    CONGEDO.  Navigare via fa partire il congedo che la pagina ha gia'.
        try:
            c.chiama("Page.navigate", url="about:blank")
            time.sleep(1.5)
        except Exception:                            # noqa: BLE001
            pass
        c.chiudi()


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True)
    a.add_argument("--diagnosi", type=int, required=True)
    a.add_argument("--utente", default="nicfio")
    a.add_argument("--parola-file", required=True)
    a.add_argument("--tela", default="1920x1080")
    a.add_argument("--fuori-pixel", required=True)
    a.add_argument("--fuori-json", required=True)
    a.add_argument("--copia", default="")
    a.add_argument("--fetta", type=int, default=2 * 1024 * 1024)
    a.add_argument("--attesa-sonda", type=int, default=120)
    a.add_argument("--attesa-video", type=int, default=60)
    args = a.parse_args()

    r = giro(args)
    with open(args.fuori_json, "w") as f:
        json.dump(r, f, ensure_ascii=False, indent=1, default=str)
    print()
    if r.get("guaio"):
        print(f"    {ROSSO}⛔ i pixel NON sono usciti: {r['guaio']}{GRIGIO}")
        print(f"    ⛔ stato 2: NON MISURATO.  Non e' un bocciato del prodotto —")
        print(f"       e' il banco che non ha potuto guardare.")
        sys.exit(2)
    print(f"    {VERDE}⭐ i pixel della tela del prodotto sono fuori dal "
          f"browser{GRIGIO}")
    sys.exit(0)
