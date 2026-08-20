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
  /* ⛔ Dal 17 agosto 2026 la tela del prodotto e' `bitmaprenderer`
     (`DECISIONI.md` §5.4): il contesto 2D non c'e' piu' e `getContext("2d")`
     torna **null**.  ⇒ Si ricopia in una tela del BANCO — `drawImage` di una
     tela in un'altra funziona qualunque sia il contesto di partenza — e si
     rilegge di la'.
     ⚠ E quel che si rilegge resta il MAGAZZINO, non lo schermo
       (`LEZIONI.md` §1.16): questa lettura vede la geometria, non gli
       artefatti — e non ha mai visto altro. */
  const cp = document.createElement("canvas");
  cp.width = t.width; cp.height = t.height;
  const p = cp.getContext("2d", { willReadFrequently: true });
  p.drawImage(t, 0, 0);
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
  /* ⛔ Dal 17 agosto 2026 la tela del prodotto e' `bitmaprenderer`
     (`DECISIONI.md` §5.4): il contesto 2D non c'e' piu' e `getContext("2d")`
     torna **null**.  ⇒ Si ricopia in una tela del BANCO — `drawImage` di una
     tela in un'altra funziona qualunque sia il contesto di partenza — e si
     rilegge di la'.
     ⚠ E quel che si rilegge resta il MAGAZZINO, non lo schermo
       (`LEZIONI.md` §1.16): questa lettura vede la geometria, non gli
       artefatti — e non ha mai visto altro. */
  const cp = document.createElement("canvas");
  cp.width = t.width; cp.height = t.height;
  const p = cp.getContext("2d", { willReadFrequently: true });
  p.drawImage(t, 0, 0);
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


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⭐ LA CUCITURA DI F2.4 — E IL FALSO VERDE CHE C'ERA QUI DENTRO
#
# Fino al 13 agosto 2026 questo pezzo scriveva **tre costanti**:
#
#     {"giro": None, "fin_ricevuto": True,
#      "reset_ricevuto": bool(conti.get("reset", 0)), "dipinto": True}
#
# e i tre controlli di M8 (`02-giudizio-metro.py`) leggevano proprio quelle.
# ⛔ Nessuno dei tre poteva scattare: `giro` era None (il confronto e' saltato
#    per costruzione), `fin_ricevuto` era True (il controllo cerca il False), e
#    `conti["reset"]` **non esiste** — la pagina quel contatore lo chiama
#    `azzerati` (`src/pagina.html` §`stream_video`), quindi `.get("reset", 0)`
#    valeva 0 a ogni giro di ogni scena.
# ⇒ M8 usciva `ok: True` qualunque cosa facesse il prodotto, e siccome il metro
#   conta vivo ogni strumento con `ok is not None`, il «12 guasti su 12» della
#   catena vera erano **undici strumenti e un verde vuoto**.
#
# ⚠ Ed e' la STESSA FORMA del difetto curato la mattina stessa alle 08:56
#   (`dc2f6a9`, «due grandezze che si chiamano tutt'e due larghezza della
#   tela»): due nomi per una cosa sola.  E' rinata dodici ore dopo in un altro
#   file, il che dice che la cura non era il nome ma la regola — **il nome
#   della grandezza si legge da chi la produce**, non si ricorda a memoria.
#
# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ E `conti.azzerati` **NON E'** LA GRANDEZZA CHE M8 CERCA — verificato sui
#     pixel del prodotto, non creduto sulla parola.
#
# `src/pagina.html` §`stream_video`, ramo `!completo`:
#
#     this.conti.azzerati++;
#     this.riga("stream azzerato (RESET_STREAM) … buttato, NON consegnato al
#               decodificatore (§6.2)");
#     this.buco(…); return;
#
# ⇒ `azzerati` conta gli stream che la pagina ha **buttato bene**: e' il
#   prodotto che si comporta come F2.4 pretende.  Scrivere
#   `reset_ricevuto = bool(azzerati)` accanto a `dipinto = True` avrebbe reso
#   M8 **rosso la prima volta che il server azzera uno stream**, su una catena
#   sana — un FALSO ROSSO, che e' l'altro modo di rompere un metro, e sarebbe
#   stato peggio del falso verde perche' avrebbe accusato il prodotto.
#
# ⭐ LA GRANDEZZA VERA E' L'INVARIANTE, e sta in **due** contatori.  Nella
#   pagina ogni `consegnati++` e' a valle di un `completi++` della **stessa**
#   chiamata, e il ramo azzerato esce PRIMA di consegnare.  ⇒
#
#       consegnati > completi
#
#   vuol dire — e puo' voler dire solo — «un fotogramma e' stato consegnato al
#   decodificatore senza che il suo stream fosse completo», cioe' **esattamente
#   il guasto `dopo-reset`**.  E' una grandezza che il prodotto produce da se',
#   che parte da 0 su una catena sana, e che **puo' diventare vera**: le tre
#   cose che alla riga di prima mancavano tutte.
#
# ⚠ IL LIMITE, DICHIARATO: e' una domanda di SESSIONE, non di fotogramma.  Un
#   prodotto che consegnasse dopo un RESET incrementando **anche** `completi`
#   passerebbe di qui — ma M8 e' un anello debole per costruzione (crede a chi
#   e' sotto esame) e questo non lo cambia: lo dichiara.
# ═══════════════════════════════════════════════════════════════════════════
def identita_dalla_pagina(conti, errori=None):
    """La cucitura di F2.4 costruita dai contatori VERI della pagina.

    ⛔ Vive in una funzione, e non in linea dentro `giro()`, per una ragione
    sola: **cosi' la certificazione puo' chiamare questa e non una copia**.
    `02-giudizio-confronto.sh` costruisce con questa funzione tanto il giro
    sano quanto il guasto `dopo-reset`, e quel che certifica e' quindi la
    derivazione che gira sulla catena vera — non una riga gemella scritta a
    mano in uno shell, che e' il modo in cui una certificazione smette di
    riguardare il codice che poi lavora.
    """
    conti = dict(conti or {})
    completi = conti.get("completi")
    consegnati = conti.get("consegnati")
    dipinti = conti.get("dipinti")
    d = {"conti": conti, "errori_pagina": list(errori or [])}
    perche = {}

    # ── 1. IL GIRO ────────────────────────────────────────────────────────
    # ⛔ NON APPLICABILE, e non «non ancora»: **per costruzione**.
    d["giro"] = None
    perche["giro"] = (
        "⛔ NON APPLICABILE dalla catena vera, e non per una mancanza che si "
        "possa colmare: «giro» in M8 e' il nome del giro DEL BANCO (p.es. "
        "«mira-cat2-20260813-095007»), che il banco si e' dato da se'.  Il "
        "prodotto non lo conosce — nessuno glielo dice, il protocollo non ha "
        "un campo per dirglielo, e `src/` non si tocca.  ⚠ Scriverci `None` "
        "era una COSTANTE CHE FA PASSARE: il controllo di M8 e' «se il giro "
        "c'e' ed e' diverso», e con None non c'era mai.  Qui e' un buco "
        "DICHIARATO.  ⇒ Il guasto «il fotogramma e' di un altro giro» non "
        "resta scoperto: lo prende M6 (freschezza), che lo misura sui pixel "
        "invece di chiederlo all'imputato.")

    # ── 2. IL FIN ─────────────────────────────────────────────────────────
    # ⭐ Questa e' misurabile davvero, e la grandezza vera e' `conti.completi`:
    #    la pagina lo incrementa **solo** sul ramo `completo` di
    #    `stream_video`, cioe' solo quando il FIN e' arrivato.
    # ⚠ E' una domanda di sessione: dice «almeno un FIN l'ha visto», non «quel
    #   fotogramma li' aveva il suo».  La forma forte della stessa domanda e'
    #   il punto 3 qui sotto, e le due stanno insieme.
    if completi is None or dipinti is None:
        d["fin_ricevuto"] = None
        perche["fin_ricevuto"] = (
            "⛔ NON MISURATA: la pagina non ha consegnato i contatori "
            "`completi` / `dipinti` in questo giro.  ⚠ Un contatore assente "
            "non vale 0: valesse 0 direbbe «non ha mai visto un FIN», che e' "
            "un rosso inventato.")
    else:
        d["fin_ricevuto"] = completi > 0

    # ── 3. IL FOTOGRAMMA DIPINTO DOPO UN RESET ────────────────────────────
    # ⭐ La grandezza vera, quella di cui sopra: `consegnati > completi`.
    # ⛔ E il nome del campo dice la RISPOSTA, non l'ingrediente: si chiamava
    #    `reset_ricevuto`, che e' `azzerati > 0`, che e' **un'altra cosa** —
    #    ed e' proprio da li' che il falso verde e' nato.
    if completi is None or consegnati is None:
        d["dipinto_dopo_reset"] = None
        perche["dipinto_dopo_reset"] = (
            "⛔ NON MISURATA: mancano `conti.completi` o `conti.consegnati`, "
            "e l'invariante di F2.4 si legge in due contatori o in nessuno.  "
            "⚠ Un contatore assente letto come 0 darebbe `0 > 0` = falso, "
            "cioe' un VERDE su una misura che non e' stata fatta.")
    else:
        d["dipinto_dopo_reset"] = consegnati > completi

    d["dipinto"] = bool(dipinti) if dipinti is not None else None
    if perche:
        d["non_applicabile"] = perche
    d["nota"] = (
        "⛔ Anello DEBOLE per costruzione (F2.6): sono i contatori DELLA "
        "PAGINA, cioe' di chi e' sotto esame, letti via CDP.  Valgono insieme "
        "al registro del filo (F2.4), non al posto suo.  ⭐ Ma sono grandezze "
        "che il prodotto produce e che possono diventare vere: non sono piu' "
        "le tre costanti che rendevano M8 verde per costruzione.")
    return d


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

        # ⚠ La cucitura di F2.4 — e i suoi conti VERI, non tre costanti.
        #   Il perche' di ogni campo sta in `identita_dalla_pagina()`.
        fuori["identita"] = identita_dalla_pagina(conti, s.get("errori"))
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
