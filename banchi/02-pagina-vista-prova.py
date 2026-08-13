#!/usr/bin/env python3
"""02-pagina-vista-prova.py — ⭐⭐ IL BANCO CHE MISURA **QUANTO GRANDE** VIENE
   DIPINTO IL FOTOGRAMMA, invece di contare **se** arriva.

   Lo lancia `02-pagina-vista-lancia.sh`, che apparecchia la scena.  Qui c'e'
   il giro, la misura e il VERDETTO, con l'atteso scritto prima.

===========================================================================
⛔ PERCHE' NESSUN BANCO L'AVEVA PRESO — 13 agosto 2026

`[M]` Dall'utente in persona, sulla 7561: *«adesso vedo un'immagine piccola
dello sfondo del desktop»*.  Il registro della sua stessa schermata:

    ATTACCA: tela 1920×1080, vista 2560×857
    video · decodificatore configurato per 1920×1080 (riconfigurazione n. 1)

⇒ ⛔ **La catena era intera e il metro era verde.**  Il fotogramma arrivava, si
  decodificava, si dipingeva; `02-pagina-misura-prova.py` pretendeva *«almeno
  un fotogramma dipinto, e la tela NON uniforme»* — e tutt'e due le pretese
  erano onorate mentre l'utente guardava un francobollo largo 425 px dentro
  una finestra da 2560.

⛔ **I banchi guardavano SE i pixel arrivano, non QUANTO GRANDI sono dipinti.**
   E la misura che mancava non e' una raffinatezza: `RCP.md` §6.2 la impone —
   *«il client riscala alla **vista**, non alla tela»* — ed e' la ragione per
   cui la tela NON insegue la finestra (§7.1).  Un client che non riscala
   rende falsa la meta' del protocollo che si e' scritta apposta.

===========================================================================
⛔⭐ LE DUE MISURE CHE SI CHIAMANO TUTT'E DUE «LARGHEZZA DELLA TELA»

    `canvas.width`        il BUFFER: quanti pixel si dipingono
    `canvas.style.width`  la CORNICE: quanto e' grande sul vetro

Il difetto dell'utente aveva il buffer GIUSTO (2560, cioe' la vista) e la
cornice SBAGLIATA (una colonna di testo da 34rem).  ⚠ Un banco che guardasse
solo `canvas.width` sarebbe stato verde su quella schermata — e infatti lo era.
⇒ Qui si misurano tutt'e tre: il buffer, la cornice, e **i pixel accesi dentro
  il buffer**.  La terza e' l'unica che nessuno puo' dichiarare al posto suo.

===========================================================================
⛔ E IL GUASTO SI INNESTA NELLA COPIA SERVITA, NON NEL PRODOTTO

`--prepara` scrive in una cartella temporanea la pagina **sana** o una delle
due **guaste**, e il sorgente in `src/` non si tocca mai.  I due guasti sono i
due modi in cui questa cura puo' morire:

  `cornice-fissa`  la cornice torna `width: 100%` dentro `main` — **il difetto
                   del 13 agosto, letteralmente**.  Buffer giusto, immagine
                   piccola.
  `uno-a-uno`      la cornice e' giusta e il riscalamento no: il fotogramma si
                   dipinge 1:1 dentro una vista diversa.  E' il caso che il
                   mandato nomina.

⛔ Se un guasto NON diventasse rosso, il banco non direbbe niente quando e'
   verde (`CODER.md` §4.6).  Per questo l'innesto e' verificato: una sostituzione
   che non trovasse il suo testo ferma il banco invece di servire una pagina
   sana chiamandola guasta — che sarebbe misurare il sano e crederlo il guasto.
"""
import argparse
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_s = importlib.util.spec_from_file_location(
    "cdp", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "02-pagina-misura-cdp.py"))
cdp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(cdp)

VERDE = "\033[1;32m"; ROSSO = "\033[1;31m"; GIALLO = "\033[1;33m"; GRIGIO = "\033[0m"


def ok(t):  print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):  print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t): print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t): print(f"    --  {t}")
def log(t): print(f"\n\033[1m== {t}\033[0m")


# ===========================================================================
# ⛔ LE SCENE.  L'atteso e' scritto QUI, prima del giro.
#
# ⚠ `fotogramma` e' anche la TELA che il banco fa negoziare: §6.2 vuole che la
#   misura del fotogramma sia la tela in vigore, e un banco che le facesse
#   diverse misurerebbe la regola della tolleranza invece del riscalamento.
SCENE = {
    # la finestra dell'utente: piu' larga che alta rispetto al 16:9 della tela
    # ⇒ l'altezza riempie, e restano due bande VERTICALI.
    "vista-piu-larga":   {"css": (2560, 900),  "dpr": 1, "fotogramma": (1920, 1080)},
    # ⭐ IL CASO OPPOSTO: la vista e' piu' grande della tela in TUTT'E DUE i
    #    versi ⇒ il fotogramma va INGRANDITO, non lasciato piccolo in un angolo.
    "vista-piu-grande":  {"css": (2400, 1400), "dpr": 1, "fotogramma": (640, 480)},
    # la vista piu' PICCOLA della tela in tutt'e due i versi ⇒ si rimpicciolisce
    # tutto intero, con le bande sopra e sotto.
    "vista-piu-piccola": {"css": (800, 600),   "dpr": 1, "fotogramma": (1920, 1080)},
    # ⛔ Il telefono: pixel logici e pixel fisici sono due unita' diverse, e la
    #    vista di §4.5 e' in FISICI.  Un fattore 2 sbagliato qui dipinge meta'
    #    finestra e non da' nessun errore.
    "fattore-2":         {"css": (800, 600),   "dpr": 2, "fotogramma": (1920, 1080)},
    # ⭐ E QUANDO LA VISTA CAMBIA, il riscalamento segue — senza che arrivi
    #    nessun fotogramma nuovo.
    "ridimensiona":      {"css": (1400, 900),  "dpr": 1, "fotogramma": (1920, 1080),
                          "poi": (900, 700)},
}

# ===========================================================================
# ⛔ I DUE GUASTI, INNESTATI NELLA COPIA SERVITA
GUASTI = {
    "cornice-fissa": [
        # 1. la cornice torna a essere quella del foglio: `width: 100%` di una
        #    colonna da 34rem — il difetto del 13 agosto, letteralmente.
        ("</style>",
         '#schermo { width: 100% !important; height: auto !important; }\n'
         'body[data-schermo="acceso"] { padding: 2rem !important;'
         ' display: flex !important; }\n'
         'body[data-schermo="acceso"] main { max-width: 34rem !important; }\n'
         '</style>'),
        # 2. e JavaScript smette di mettere la misura: senza questo, l'`!important`
        #    del foglio perderebbe comunque contro lo stile in linea.
        ('this.tela.style.width = (l / r) + "px";', 'void (l / r);'),
        ('this.tela.style.height = (a / r) + "px";', 'void (a / r);'),
    ],
    "uno-a-uno": [
        # ⛔ La cornice resta giusta e muore SOLO il riscalamento: il fotogramma
        #    si dipinge 1:1 dentro una vista che non e' la sua misura.
        ("const s = Math.min(cl / fl, ca / fa);", "const s = 1;"),
    ],
}

SEGNAPOSTO = {"__IMPRONTA__": "", "__AVVISO__": "", "__BANNATO__": "no",
              "__RESTANO_MS__": "0"}


def prepara(sorgente, dentro, guasto):
    """Scrive la pagina servita.  ⛔ Il prodotto non si tocca."""
    testo = open(sorgente, encoding="utf-8").read()
    for k, v in SEGNAPOSTO.items():
        testo = testo.replace(k, v)
    if guasto and guasto != "sano":
        if guasto not in GUASTI:
            raise SystemExit(f"⛔ guasto sconosciuto: {guasto}")
        for cerca, metti in GUASTI[guasto]:
            n = testo.count(cerca)
            if n != 1:
                # ⛔ Ferma tutto: servire la pagina SANA chiamandola guasta
                #    misurerebbe il sano e lo direbbe del guasto.
                raise SystemExit(
                    f"⛔ l'innesto «{guasto}» non ha trovato il suo testo "
                    f"({n} occorrenze di {cerca[:60]!r}): il prodotto e' "
                    f"cambiato e questo guasto va riscritto.")
            testo = testo.replace(cerca, metti)
    os.makedirs(dentro, exist_ok=True)
    fuori = os.path.join(dentro, "index.html")
    with open(fuori, "w", encoding="utf-8") as f:
        f.write(testo)
    return fuori


# ===========================================================================
# ⛔ IL FOTOGRAMMA SI COSTRUISCE QUI, dai 28 byte di `RCP.md` §6.2 — e i numeri
#    del codec (1 = HEVC, 2 = AV1) sono quelli della tabella, non un'importazione
#    dal prodotto: due letture indipendenti degli stessi 28 byte sono quel che
#    `PIANO.md` §0.4 dice di aver comprato.
#
# ⚠ I DATI del fotogramma invece vengono dal prodotto (`REMOTIX.sonde_misura`),
#   e non e' un imbroglio: sono fotogrammi chiave veri, generati da
#   `02-pagina-sonda-misura.py`, e rifarli qui sarebbe un secondo codificatore
#   da certificare per misurare una cosa che non c'entra.
DIPINGI = """
(async function () {
  const R = window.REMOTIX;
  if (!R) return { guaio: "REMOTIX assente" };
  const s = await R.sondaggio;
  const nomi = Object.keys(s.codec).filter((n) =>
    s.codec[n][8] && s.codec[n][8].arriva);
  if (!nomi.length) return { guaio: "nessun codec arriva al pixel a 8 bit" };
  const nome = nomi[0];
  const NUMERO = { hevc: 1, av1: 2 };            /* RCP.md §6.2 */
  const stringa = s.codec[nome][8].stringa;
  const L = %d, A = %d;
  const g = (R.sonde_misura[nome] || []).find((x) => x.l === L && x.a === A);
  if (!g) return { guaio: "nessuna sonda " + nome + " a " + L + "x" + A };

  /* i 28 byte di §6.2: u16 tipo · u16 codec · u32 largh · u32 alt ·
     u32 numero · u64 istante · u32 input */
  const testa = new Uint8Array(28);
  const v = new DataView(testa.buffer);
  v.setUint16(0, 0x0301);                        /* CHIAVE */
  v.setUint16(2, NUMERO[nome]);
  v.setUint32(4, L); v.setUint32(8, A);
  v.setUint32(12, 1);                            /* numero: lo 0 e' riservato */
  v.setBigUint64(16, 0n); v.setUint32(24, 0);
  const b64 = atob(g.dati);
  const corpo = new Uint8Array(b64.length);
  for (let i = 0; i < b64.length; i++) corpo[i] = b64.charCodeAt(i);
  const byte = new Uint8Array(28 + corpo.length);
  byte.set(testa); byte.set(corpo, 28);

  /* ⛔ Si guida l'oggetto DEL PRODOTTO — `Schermo` — e non una copia che gli
     somigli: un banco che misurasse una copia della catena misurerebbe la
     copia (forma E10 di `REVIEWER.md`). */
  const sc = R.schermo;
  sc.riparti();
  sc.negozia(NUMERO[nome], 8, stringa, L, A);
  sc.adatta_vista();
  sc.stream_video(byte, true);
  return { codec: nome, stringa: stringa, fotogramma: [L, A] };
})()
"""

# ===========================================================================
# ⛔⭐ LA MISURA, E SONO TRE PIANI.
#
#   1. il BUFFER      `canvas.width` — quanti pixel si dipingono
#   2. la CORNICE     `getBoundingClientRect()` — quanto e' grande sul vetro
#   3. ⭐ I PIXEL     il rettangolo dei pixel ACCESI dentro il buffer
#
# ⚠ Il terzo e' l'unico che nessuno puo' dichiarare al posto suo, ed e' quello
#   che distingue «riscalato» da «disegnato piccolo in mezzo al nero»: le bande
#   sono nere per costruzione (`componi()` le riempie di `#000`) e la sonda e'
#   meta' rossa e meta' blu, quindi il rettangolo acceso E' l'immagine.
#
# ⛔ E la vista il banco se la calcola DA SOLO, con la stessa regola di §4.5 —
#    `documentElement.clientWidth × devicePixelRatio` — invece di leggerla dalla
#    pagina.  Leggerla dalla pagina vorrebbe dire confrontare il numero della
#    pagina col numero della pagina: sarebbe verde anche se fosse sbagliato.
MISURA = """
(function () {
  const t = document.getElementById("schermo");
  const R = window.REMOTIX, sc = R && R.schermo;
  const d = document.documentElement;
  const dpr = devicePixelRatio || 1;
  const fuori = {
    dpr: dpr,
    vista: [Math.max(1, Math.round(d.clientWidth * dpr)),
            Math.max(1, Math.round(d.clientHeight * dpr))],
    conti: sc ? sc.conti : null,
    errori: sc ? sc.errori : null,
    dichiarata: sc ? sc.dipinta : null,
    acceso: document.body.dataset.schermo || "",
  };
  if (!t) { fuori.guaio = "niente tela"; return fuori; }
  const r = t.getBoundingClientRect();
  fuori.buffer = [t.width, t.height];
  fuori.cornice = [Math.round(r.width * 100) / 100,
                   Math.round(r.height * 100) / 100];
  if (t.width < 32 || t.height < 32) { fuori.guaio = "tela ancora al minimo"; return fuori; }
  try {
    const p = t.getContext("2d", { willReadFrequently: true });
    const im = p.getImageData(0, 0, t.width, t.height).data;
    /* ⚠ Una riga (o colonna) conta come accesa solo con almeno 4 pixel accesi:
       il sottocampionamento della crominanza sporca il bordo, e un pixel solo
       non e' un'immagine. */
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
    if (x1 < 0 || y1 < 0) { fuori.dipinta = null; fuori.perche = "nessun pixel acceso"; }
    else {
      const dl = x1 - x0 + 1, da = y1 - y0 + 1;
      fuori.dipinta = [dl, da];
      fuori.origine = [x0, y0];
      /* la stessa misura in pixel del VETRO: e' quel che l'utente guarda */
      const k = t.width ? r.width / t.width : 0;
      fuori.dipinta_css = [Math.round(dl * k * 10) / 10, Math.round(da * k * 10) / 10];
    }
  } catch (e) { fuori.guaio = "getImageData: " + String(e); }
  return fuori;
})()
"""


def aspetta(c, espressione, quanto, pronto, passo=0.4):
    fine = time.time() + quanto
    ultimo = None
    while time.time() < fine:
        ultimo = c.valuta(espressione, attendi=False)
        if ultimo and pronto(ultimo):
            return ultimo
        time.sleep(passo)
    return ultimo


def fotografa(c, dove):
    """⛔⭐ LA FOTOGRAFIA SI PRENDE DALLA SCHEDA, E NEL MOMENTO DELLA MISURA.

    `[M]` 13 agosto 2026, primo giro di questo banco: le sette fotografie erano
    **lo stesso file, byte per byte, 23354 byte l'una** — `about:blank`.  Il
    palco le prendeva con `import -window root` DOPO che questo programma aveva
    navigato via per lasciare il posto, e nessuno le aveva guardate.

    ⚠ E' lo stesso difetto che il mandato di stasera nomina, ripetuto: *«l'ho
      scritto nel rapporto» e «è nel file» sono due cose diverse*.  ⇒ Adesso lo
      scatto lo fa `Page.captureScreenshot` sulla scheda misurata, subito dopo la
      misura, e chi la cita ha davanti quel che il banco ha appena contato."""
    try:
        r = c.chiama("Page.captureScreenshot", format="png",
                     captureBeyondViewport=False)
        import base64 as _b
        os.makedirs(os.path.dirname(dove), exist_ok=True)
        with open(dove, "wb") as f:
            f.write(_b.b64decode(r["data"]))
        return os.path.getsize(dove)
    except Exception as e:                       # noqa: BLE001
        dub(f"⚠ la fotografia non e' riuscita: {e}")
        return 0


def viewport(c, css, dpr):
    """⛔ La finestra si cambia con `Emulation.setDeviceMetricsOverride` e non
    con `--window-size`: e' l'unico modo di cambiarla **a pagina viva**, cioe'
    di provare il ridimensionamento invece di ripartire da zero.  ⚠ Ed e' anche
    l'unico che regga il fattore di scala 2 senza un telefono."""
    c.chiama("Emulation.setDeviceMetricsOverride", width=css[0], height=css[1],
             deviceScaleFactor=dpr, mobile=False)


def giro(nome, args):
    scena = SCENE[nome]
    log(f"Il giro «{nome}» — pagina «{args.guasto}» · finestra "
        f"{scena['css'][0]}×{scena['css'][1]} CSS a fattore {scena['dpr']} · "
        f"fotogramma {scena['fotogramma'][0]}×{scena['fotogramma'][1]}")
    b = cdp.pagina(args.diagnosi)
    c = cdp.Cdp(b["webSocketDebuggerUrl"])
    fuori = {"giro": nome, "guasto": args.guasto, "scena": scena}
    try:
        c.chiama("Page.enable")
        c.chiama("Runtime.enable")
        # ⛔ LA CACHE SI SPEGNE — `[M]` 13 agosto 2026, primo giro di questo
        #    banco: le due pagine guaste hanno prodotto numeri IDENTICI alla
        #    sana, cifra per cifra, perche' Chrome le aveva servite dalla
        #    propria cache.  ⚠ Il banco ha detto «il guasto e' verde» di un
        #    guasto che al browser non era mai arrivato — cioe' ha accusato se
        #    stesso di un difetto che non aveva.
        c.chiama("Network.enable")
        c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        viewport(c, scena["css"], scena["dpr"])
        c.chiama("Page.navigate", url=args.url)
        time.sleep(1.5)
        pronta = aspetta(c, "!!(window.REMOTIX && window.REMOTIX.schermo)",
                         args.attesa_sonda, lambda x: x is True)
        if pronta is not True:
            ko(f"⛔ la pagina non ha esposto REMOTIX: {pronta}")
            fuori["guaio"] = "REMOTIX assente"
            return fuori
        d = c.valuta(DIPINGI % scena["fotogramma"])
        if not isinstance(d, dict) or d.get("guaio"):
            ko(f"⛔ il fotogramma non e' partito: {d}")
            fuori["guaio"] = str(d)
            return fuori
        inf(f"codec {d['codec']} («{d['stringa']}»), fotogramma consegnato al "
            f"percorso del prodotto")
        m = aspetta(c, MISURA, args.attesa_video,
                    lambda x: (x.get("conti") or {}).get("dipinti", 0) > 0)
        fuori["misura"] = m
        if args.copia:
            n = fotografa(c, args.copia)
            if n:
                fuori["copia"] = args.copia
                inf(f"copia della SCHEDA MISURATA: {args.copia} ({n} byte)")
        if not m or (m.get("conti") or {}).get("dipinti", 0) < 1:
            ko(f"⛔ nessun fotogramma dipinto: {json.dumps(m)[:400]}")
            fuori["guaio"] = "niente dipinto"
            return fuori

        if scena.get("poi"):
            # ⭐ IL RIDIMENSIONAMENTO: la finestra cambia e NON arriva nessun
            #    fotogramma nuovo.  Quel che si ridipinge e' il deposito.
            inf(f"⭐ la finestra cambia a {scena['poi'][0]}×{scena['poi'][1]} "
                f"CSS — e nessun fotogramma nuovo arriva")
            viewport(c, scena["poi"], scena["dpr"])
            time.sleep(1.5)
            fuori["dopo"] = c.valuta(MISURA, attendi=False)
            if args.copia:
                dopo = args.copia.replace(".png", "-dopo.png")
                n = fotografa(c, dopo)
                if n:
                    fuori["copia_dopo"] = dopo
                    inf(f"copia dopo il ridimensionamento: {dopo} ({n} byte)")
        return fuori
    finally:
        try:
            c.chiama("Page.navigate", url="about:blank")
            time.sleep(0.5)
        except Exception:                        # noqa: BLE001
            pass
        c.chiudi()


# ---------------------------------------------------------------------------
def pretese(nome, m, scena, guai, etichetta=""):
    """⛔ LE PRETESE SUL RISCALAMENTO, e valgono per ogni scena e ogni misura.
    L'atteso e' scritto qui, prima del giro."""
    def pretesa(vero, testo):
        (ok if vero else ko)(testo)
        if not vero:
            guai.append(f"{nome}{etichetta}: {testo}")

    vista = m.get("vista") or [0, 0]
    buf = m.get("buffer") or [0, 0]
    cor = m.get("cornice") or [0, 0]
    dip = m.get("dipinta") or [0, 0]
    dcss = m.get("dipinta_css") or [0, 0]
    fl, fa = scena["fotogramma"]
    dpr = m.get("dpr") or 1

    # 1. il buffer E' la vista: e' la meta' che gia' funzionava, e resta.
    pretesa(buf == vista,
            f"il buffer della tela ({buf[0]}×{buf[1]}) e' la vista "
            f"({vista[0]}×{vista[1]}): §6.2, si dipinge alla vista")

    # 2. ⭐⭐ LA CORNICE E' LA VISTA — la meta' che mancava, e il difetto
    #    dell'utente sta tutto qui.
    atteso_cor = (vista[0] / dpr, vista[1] / dpr)
    vicino = (abs(cor[0] - atteso_cor[0]) <= 1.5 and
              abs(cor[1] - atteso_cor[1]) <= 1.5)
    pretesa(vicino,
            f"⭐ e la CORNICE sul vetro ({cor[0]}×{cor[1]} CSS) e' la stessa "
            f"vista ({atteso_cor[0]:.0f}×{atteso_cor[1]:.0f} CSS): un buffer "
            f"grande dentro una cornice piccola da' l'immagine piccola")

    if not dip[0]:
        pretesa(False, "⛔ nessun pixel acceso nella tela: non c'e' niente da "
                       "misurare")
        return

    # 3. ⭐ LA MISURA DIPINTA RIEMPIE LA VISTA in almeno un verso.
    riempie = max(dip[0] / vista[0], dip[1] / vista[1])
    pretesa(riempie >= 0.985,
            f"⭐ l'immagine RIEMPIE la vista in un verso (il verso lungo copre "
            f"il {100 * riempie:.1f} %): dipinta {dip[0]}×{dip[1]} dentro "
            f"{vista[0]}×{vista[1]}")

    # 4. e non deborda: le bande sono dentro, non fuori.
    pretesa(dip[0] <= vista[0] + 1 and dip[1] <= vista[1] + 1,
            f"e non deborda dalla vista ({dip[0]}×{dip[1]} ≤ "
            f"{vista[0]}×{vista[1]})")

    # 5. ⛔ LE PROPORZIONI SI CONSERVANO: si impagina, non si stira
    #    (`SPECIFICHE.md` §6.2).
    p_f = fl / fa
    p_d = dip[0] / dip[1]
    pretesa(abs(p_d - p_f) / p_f <= 0.02,
            f"⛔ e le PROPORZIONI restano quelle del fotogramma "
            f"({p_d:.3f} contro {p_f:.3f}): si impagina con le bande, non si "
            f"stira (SPECIFICHE.md §6.2)")

    # 6. ⭐⭐ E NON E' 1:1 — la pretesa che il mandato nomina.
    scala = dip[0] / fl
    diversa = abs(vista[0] - fl) > 2 or abs(vista[1] - fa) > 2
    if diversa:
        pretesa(abs(scala - 1.0) > 0.02,
                f"⭐⭐ e NON e' dipinta 1:1: la vista ({vista[0]}×{vista[1]}) "
                f"non e' il fotogramma ({fl}×{fa}), e la scala applicata e' "
                f"{scala:.3f}")
    else:
        inf(f"la vista coincide col fotogramma: qui 1:1 e' la risposta giusta "
            f"(scala {scala:.3f})")

    # 7. il verso: ingrandita o rimpicciolita, secondo la scena.
    if vista[0] > fl and vista[1] > fa:
        pretesa(dip[0] > fl and dip[1] > fa,
                f"⭐ IL CASO OPPOSTO: la vista e' piu' GRANDE della tela in "
                f"tutt'e due i versi, e l'immagine e' INGRANDITA "
                f"({dip[0]}×{dip[1]} da {fl}×{fa}) — non lasciata piccola in "
                f"un angolo")
    if vista[0] < fl and vista[1] < fa:
        pretesa(dip[0] < fl and dip[1] < fa,
                f"⭐ e con la vista piu' PICCOLA in tutt'e due i versi "
                f"l'immagine e' rimpicciolita tutta intera "
                f"({dip[0]}×{dip[1]} da {fl}×{fa}), non tagliata")

    inf(f"sul vetro l'utente vede {dcss[0]}×{dcss[1]} pixel CSS "
        f"(finestra {vista[0] / dpr:.0f}×{vista[1] / dpr:.0f} CSS)")
    if m.get("dichiarata"):
        d = m["dichiarata"]
        # ⚠ Quel che la pagina DICHIARA si confronta con quel che si e' MISURATO
        #   sui pixel: se divergono, il registro della pagina mente a chi
        #   diagnostica — ed e' la forma E1 dentro il prodotto.
        pretesa(abs(d["l"] - dip[0]) <= 2 and abs(d["a"] - dip[1]) <= 2,
                f"e quel che la pagina scrive nel registro ({d['l']}×{d['a']}, "
                f"scala {d['scala']}) e' quel che si legge nei pixel "
                f"({dip[0]}×{dip[1]})")


def verdetto(r, args):
    nome = r["giro"]
    scena = r["scena"]
    guai = []
    log(f"Il verdetto del giro «{nome}» (pagina «{args.guasto}») — l'atteso "
        f"era scritto prima")
    if r.get("guaio"):
        ko(f"⛔ il giro non e' arrivato alla misura: {r['guaio']}")
        return [r["guaio"]]
    pretese(nome, r["misura"], scena, guai)

    if scena.get("poi"):
        log(f"⭐ E DOPO IL RIDIMENSIONAMENTO — {scena['poi'][0]}×"
            f"{scena['poi'][1]} CSS, senza nessun fotogramma nuovo")
        d = r.get("dopo") or {}
        prima = r["misura"]
        if not d or not d.get("buffer"):
            ko("⛔ non ho misurato niente dopo il ridimensionamento")
            return guai + ["niente dopo il ridimensionamento"]
        pretese(nome, d, scena, guai, etichetta=" (dopo)")

        def pretesa(vero, testo):
            (ok if vero else ko)(testo)
            if not vero:
                guai.append(f"{nome} (dopo): {testo}")

        cp = (prima.get("conti") or {}).get("dipinti", 0)
        cd = (d.get("conti") or {}).get("dipinti", 0)
        rp = (prima.get("conti") or {}).get("ricomposizioni", 0)
        rd = (d.get("conti") or {}).get("ricomposizioni", 0)
        # ⛔ E' la riga che distingue «segue la vista» da «e' arrivato un altro
        #    fotogramma»: qui non ne arriva nessuno, e l'immagine cambia lo
        #    stesso misura.
        pretesa(cd == cp,
                f"⛔ e NON e' arrivato nessun fotogramma nuovo (dipinti: "
                f"{cp} → {cd}): quel che si e' ridipinto e' il DEPOSITO")
        pretesa(rd > rp,
                f"ma la tela e' stata RICOMPOSTA ({rp} → {rd}): il "
                f"riscalamento ha seguito la finestra")
        pretesa(d.get("dipinta") and prima.get("dipinta") and
                d["dipinta"] != prima["dipinta"],
                f"e la misura dipinta e' CAMBIATA: "
                f"{prima.get('dipinta')} → {d.get('dipinta')}")
        # ⚠ e non e' diventata nera: `canvas.width` svuota la tela, e senza il
        #   deposito il ridimensionamento la lascerebbe vuota per sempre —
        #   alla fase 2 non arriva nessun secondo fotogramma.
        pretesa(bool(d.get("dipinta")),
                "⛔ e la tela NON e' rimasta vuota: scrivere `canvas.width` la "
                "svuota, e alla fase 2 non arriva nessun secondo fotogramma")
    return guai


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--prepara", default="")
    a.add_argument("--sorgente", default="")
    a.add_argument("--dentro", default="")
    a.add_argument("--giro", default="", choices=[""] + list(SCENE))
    a.add_argument("--guasto", default="sano")
    a.add_argument("--url", default="")
    a.add_argument("--diagnosi", type=int, default=0)
    a.add_argument("--attesa-sonda", type=int, default=90)
    a.add_argument("--attesa-video", type=int, default=30)
    a.add_argument("--rosso-atteso", action="store_true",
                   help="⛔ il giro DEVE essere rosso: e' un guasto innestato")
    a.add_argument("--copia", default="",
                   help="dove scrivere la fotografia della scheda misurata")
    a.add_argument("--uscita", default="")
    args = a.parse_args()

    if args.prepara:
        f = prepara(args.sorgente, args.dentro, args.prepara)
        print(f)
        sys.exit(0)

    if not args.giro:
        raise SystemExit("⛔ serve --giro")
    r = giro(args.giro, args)
    guai = verdetto(r, args)
    r["guai"] = guai
    if args.uscita:
        with open(args.uscita, "a") as f:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print()
    if args.rosso_atteso:
        # ⛔ Il guasto DEVE essere rosso.  Un guasto verde vuol dire che il
        #    banco non guarda quel che dice di guardare (`CODER.md` §4.6).
        if guai:
            print(f"    {VERDE}⭐ il guasto «{args.guasto}» e' ROSSO come "
                  f"doveva ({len(guai)} pretese cadute): il banco sa "
                  f"diventare rosso{GRIGIO}")
            sys.exit(0)
        print(f"    {ROSSO}⛔ il guasto «{args.guasto}» e' VERDE: il banco non "
              f"guarda quel che dice di guardare{GRIGIO}")
        sys.exit(1)
    if guai:
        print(f"    {ROSSO}⛔ il giro «{args.giro}»: {len(guai)} pretese non "
              f"onorate{GRIGIO}")
        sys.exit(1)
    print(f"    {VERDE}⭐ il giro «{args.giro}»: tutte le pretese "
          f"onorate{GRIGIO}")
    sys.exit(0)
