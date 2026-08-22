#!/usr/bin/env python3
"""06-b37-numeri.py — ⛔ LE TRE `[?]` DI `SPECIFICHE.md` §6.1-bis, MISURATE.

    python3 banchi/06-b37-numeri.py <porta> <display> <pid-browser> <nome> <esiti.jsonl>

Gira dentro `06-b37-lancia.sh`, che gli prepara lo schermo finto, il
raccoglitore e il browser.  ⚠ Qui non si accende niente: si misura e si giudica.

═══════════════════════════════════════════════════════════════════════════
⛔ L'ATTESO, DICHIARATO PRIMA DI GIRARE (`LEZIONI.md` §1.9)

  A1  la TELA che la pagina chiede per la stessa finestra fisica e' LA STESSA ai
      tre zoom (100 · 150 · 50 %), entro 2 px.  ⭐ E' l'ipotesi che il mandato mi
      chiede di REFUTARE: «da quando la tela e' la finestra, lo zoom non falsa
      piu' niente».
  A2  ⛔⭐ **RISCRITTA IL 22 AGOSTO 2026** — la VISTA che la pagina dichiara e'
      la larghezza VERA del contenuto in pixel del dispositivo, **letta sui
      PIXEL** (le strisce di calibrazione di `06-b37-comune.py`), entro 1 px, e
      il confronto e' BIDIREZIONALE.
      ⛔ Prima diceva: «`innerWidth × dpr` + bordo = xwininfo entro 1 px», con
      `bordo` **calibrato come la moda di `xwininfo − innerWidth × dpr`**.  ⇒ La
      misura di `xwininfo` si semplificava via e restava un'identita': A2 non
      poteva fallire per nessun difetto del prodotto, perche' i due membri erano
      due numeri del BROWSER, non uno del browser e uno della pagina.
  A3  la TELA chiesta e' sempre PARI su tutt'e due i lati e dentro
      320..7680 × 240..4320 (`RCP.md` §4.5).
  A4  la VISTA puo' uscire DISPARI — ed e' legale (`RCP.md` §7.1: «qualunque
      misura da 1×1 in su, dispari compresa»).  Si conta quante volte succede.
  A5  ⛔⭐ **BIDIREZIONALE DAL 22 AGOSTO 2026.**  La TELA chiesta sta a `0` o `1`
      pixel per lato SOTTO la vista: `tela = vista − (vista mod 2)`, quindi
      `0 ≤ vista − tela ≤ 1`, e **non c'e' nessun altro valore legale**.
      ⛔ Prima si guardava solo `tela > vista`: una tela **30 px piu' stretta**
      della finestra — banda nera permanente, 30 colonne di desktop perse —
      lasciava dodici combinazioni su dodici VERDI.  ⚠ L'eccezione resta il
      minimo di §4.5, dove il codice arrotonda IN SU a 320×240 e lo dichiara.

  A6  ⛔⭐⭐ **LA DOMANDA VERA, e dal 22 agosto 2026 ha una VERITA' ESTERNA.**
      La tela chiesta sta dentro la finestra che esiste, e non le lascia dentro
      una banda nera.  Detta con i numeri, e la banda e' DERIVATA, non scelta:
      con `W` = larghezza vera del contenuto in pixel del dispositivo (letta
      sui pixel) e `r` = `devicePixelRatio`,

          W − ceil(r) ≤ tela ≤ W

      perche' `cw` e' un intero di pixel CSS ⇒ `vista = floor(cw·r) ∈ (W−r, W]`
      e la parita' toglie al massimo un altro pixel.
      ⛔ Prima il membro destro era `xwininfo − BORDO − barra` con `BORDO`
      calibrato sulle stesse righe che poi giudicava: si semplificava in
      `round(iw·r) − round(barra·r) ≈ round(cw·r)`, cioe' **l'ingresso di
      `misura_vista()` confrontato con l'uscita di `tela_da_chiedere()`**.
      ⚠ E si vede quanto costava: col `Math.round` che questa fase ha CURATO in
      `misura_vista()`, quel confronto restava verde — il difetto vero, quello
      che l'utente aveva giudicato il 14 agosto, passava sotto A6 senza toccarlo.
      ⛔ E QUEL CHE A6 NON PUO' DECIDERE, dichiarato invece che nascosto: il
      **tetto** e' largo `ceil(dpr)` perche' a dpr non intero il riquadro di
      impaginazione del motore e' piu' grande dell'area DIPINTA (misura in
      fondo al blocco di A6).  ⇒ Uno sforamento di UN pixel a dpr 1,5 questa
      scena non lo distingue, e a deciderlo sono i PIXEL: `06-b37-sfora.py`,
      dove il guasto **G3** e' rosso («TAGLIATO») e il prodotto sano e' verde.

⛔ IL CONTROLLO POSITIVO (`CODER.md` §3.3, §3.10): lo zoom DEVE essere entrato
   in vigore davvero, e lo dice `devicePixelRatio`, non il tasto premuto.  Se
   non ci arriva, il giro di quello zoom non e' un esito e non si registra come
   tale — «i due numeri sono uguali» sarebbe vero anche non avendo toccato
   niente (`banchi/01-s5-tela.sh`, rilievo R3.10).

⛔ E IL BANCO SI CERTIFICA: `banchi/06-b37-guasti.sh` innesta in una copia di
   `src/pagina.html` i guasti G1 (tela 30 px piu' stretta) e G3 (il `Math.round`
   di prima della cura), e pretende che A5 e A6 diventino ROSSI.
"""
import json
import math
import os
import subprocess
import sys
import time
import urllib.request

import importlib.util

_QUI = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "b37comune", os.path.join(_QUI, "06-b37-comune.py"))
_m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m)

PORTA, DISPLAY, PIDBR, NOME, ESITI = sys.argv[1:6]
PORTA = int(PORTA)
BASE = "http://127.0.0.1:%d" % PORTA


def x(*a):
    return subprocess.run(a, capture_output=True, text=True,
                          env={"DISPLAY": DISPLAY, "PATH": "/usr/bin:/bin"})


def com(js, attesa=20):
    """Un comando alla pagina, e la risposta.  ⛔ Uno scaduto NON e' un vuoto."""
    r = urllib.request.Request(BASE + "/comanda", data=js.encode("utf-8"),
                               headers={"X-Attesa": str(attesa)})
    with urllib.request.urlopen(r, timeout=attesa + 10) as f:
        return json.loads(f.read().decode("utf-8"))


def stato(attesa=20):
    d = com("JSON.stringify(stato())", attesa)
    if not d.get("ok"):
        return None
    return json.loads(d["valore"])


def scrivi(d):
    d["banco"] = "06-b37"
    d["motore"] = NOME
    # ⚠ «calibrazione» e non «no»: da oggi la scena appende due strisce a
    #   posizione fissa per leggere la vista sui PIXEL.  Non toccano la
    #   geometria (e la calibrazione lo VERIFICA: `cw`/`ch` prima e dopo), ⛔ ma
    #   una riga di esito deve dire tutto quel che e' stato messo nella pagina.
    d["iniezione"] = "calibrazione"
    _m.marca(d)
    with open(ESITI, "a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# La finestra del browser, e la sua misura letta FUORI dal browser.
def finestre():
    r = x("xdotool", "search", "--onlyvisible", "--pid", PIDBR)
    return [i for i in r.stdout.split() if i.strip()]


def geometria(wid):
    r = x("xwininfo", "-id", wid)
    g = {}
    for riga in r.stdout.splitlines():
        riga = riga.strip()
        for chiave, etichetta in (("l", "Width:"), ("a", "Height:"),
                                  ("x", "Absolute upper-left X:"),
                                  ("y", "Absolute upper-left Y:")):
            if riga.startswith(etichetta):
                g[chiave] = int(riga.split()[-1])
    return g if len(g) == 4 else None


def scegli_finestra(secondi=30):
    """⛔ Un browser apre piu' finestre X (Chrome ne ha di invisibili da 1×1):
       si prende la piu' grande, e si DICE quale.  ⚠ E SI ASPETTA che compaia
       (22 agosto 2026): dalla seconda scena in poi qui si moriva con «nessuna
       finestra X per il pid …» perche' il browser stava ancora aprendosi."""
    scadenza = time.time() + secondi
    while True:
        migliore, area = None, -1
        for w in finestre():
            g = geometria(w)
            if not g:
                continue
            if g["l"] * g["a"] > area:
                migliore, area = (w, g), g["l"] * g["a"]
        if migliore and area > 10000:
            return migliore
        if time.time() >= scadenza:
            return migliore
        time.sleep(0.5)


def ridimensiona(wid, l, a):
    x("xdotool", "windowsize", wid, str(l), str(a))


def fuoco(wid):
    x("xdotool", "windowactivate", "--sync", wid)
    x("xdotool", "windowfocus", "--sync", wid)


def tasto(wid, k):
    fuoco(wid)
    x("xdotool", "key", "--clearmodifiers", k)


def attendi_misura(wid, atteso_l, giri=40):
    """Aspetta che la pagina abbia VISTO il ridimensionamento.  ⛔ Non si dorme
       un tempo fisso: si guarda finche' `innerWidth × dpr` non combacia con la
       finestra vera, o finche' non si e' fermo per tre letture."""
    prec, fermo = None, 0
    for _ in range(giri):
        s = stato(5)
        g = geometria(wid)
        if s and g:
            fisica = round(s["iw"] * s["dpr"])
            if fisica == g["l"]:
                return s, g
            chiave = (s["cw"], s["ch"], s["dpr"], g["l"])
            if chiave == prec:
                fermo += 1
                if fermo >= 3:
                    return s, g
            else:
                prec, fermo = chiave, 0
        time.sleep(0.15)
    return (stato(5), geometria(wid))


# ---------------------------------------------------------------------------
# ⛔ Lo zoom: si preme, e si VERIFICA che sia entrato in vigore.
def porta_zoom(wid, bersaglio):
    tasto(wid, "ctrl+0")
    time.sleep(0.4)
    if abs((stato(5) or {"dpr": 0})["dpr"] - bersaglio) < 0.001:
        return True
    k = "ctrl+plus" if bersaglio > 1 else "ctrl+minus"
    for _ in range(8):
        tasto(wid, k)
        time.sleep(0.5)
        s = stato(5)
        if s and abs(s["dpr"] - bersaglio) < 0.001:
            return True
    return False


# ---------------------------------------------------------------------------
import os
# ⛔ Con un FATTORE forzato non si tocca lo zoom di pagina: il dpr e' gia' quello
#    del dispositivo, e premere `Ctrl +` misurerebbe le due cose insieme.
FATTORE = os.environ.get("FATTORE") or ""
LARGHEZZE = [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009,
             1010, 1011, 1200, 1201, 700, 701, 400, 401, 330, 300, 250]
ALTEZZA = 760
ZOOM = ([(float(FATTORE), "dispositivo %s×" % FATTORE)] if FATTORE
        else [(1.0, "100 %"), (1.5, "150 %"), (0.5, "50 %")])

print("== 06-b37 · %s — i numeri del browser" % NOME, flush=True)

for i in range(60):
    try:
        with urllib.request.urlopen(BASE + "/b37/stato", timeout=2) as f:
            if json.loads(f.read())["carichi"] > 0:
                break
    except Exception:
        pass
    time.sleep(0.5)
else:
    print("    NO  la pagina non si e' mai annunciata: nessuna misura", flush=True)
    sys.exit(3)

scelta = scegli_finestra()
if not scelta:
    print("    NO  nessuna finestra X per il pid %s" % PIDBR, flush=True)
    sys.exit(3)
WID, g0 = scelta
print("    --  finestra X %s, %d×%d (letta con xwininfo, FUORI dal browser)"
      % (WID, g0["l"], g0["a"]), flush=True)

# ⛔⭐ LO STRUMENTO ESTERNO, e prima di usarlo si guarda se funziona.
B = _m.Banco(PORTA, DISPLAY, PIDBR, NOME, ESITI)
B.wid = WID
CARTELLA = os.environ.get("PIXEL_DIR", "/tmp/06-b37-pixel")
os.makedirs(CARTELLA, exist_ok=True)

righe = []
saltati = []
for dpr_atteso, etichetta in ZOOM:
    # ⛔ Lo zoom si porta a una finestra di misura NOTA e si verifica.
    ridimensiona(WID, 1200, ALTEZZA)
    time.sleep(0.6)
    if FATTORE:
        # ⛔ IL CONTROLLO POSITIVO: il fattore chiesto DEVE essere entrato in
        #    vigore.  Un banco che misura a dpr 1 credendo di misurare a 1,25 e'
        #    peggio di un banco che non misura.
        s0 = stato(10) or {}
        if abs((s0.get("dpr") or 0) - dpr_atteso) > 0.001:
            print("    NO  il fattore %s NON e' in vigore (dpr=%s): giro SALTATO"
                  % (FATTORE, s0.get("dpr")), flush=True)
            saltati.append(etichetta)
            continue
    elif not porta_zoom(WID, dpr_atteso):
        s = stato(5) or {}
        print("    NO  zoom %s NON raggiunto (dpr fermo a %s): il giro si SALTA,"
              " e non si registra come esito" % (etichetta, s.get("dpr")),
              flush=True)
        saltati.append(etichetta)
        continue
    print("\n    --  zoom %s: dpr=%.3f — verificato sulla pagina, non sul tasto"
          % (etichetta, dpr_atteso), flush=True)
    print("        %-9s %-9s %-7s %-11s %-11s %-11s %-6s %s"
          % ("fin.X", "cw×ch", "barra", "vista", "tela", "PIXEL(W×H)", "pari",
             "nota"), flush=True)
    for L in LARGHEZZE:
        ridimensiona(WID, L, ALTEZZA)
        time.sleep(0.35)
        s, g = attendi_misura(WID, L)
        if not s or not g:
            print("        %-9s  ⛔ nessuna lettura" % L, flush=True)
            continue
        vista, tela = s["vista"], s["tela"]
        pari = (tela[0] % 2 == 0 and tela[1] % 2 == 0)
        fisica = round(s["iw"] * s["dpr"])
        # ⛔⭐ LA VERITA' ESTERNA SULLA LARGHEZZA DEL CONTENUTO — e il BORDO del
        #    motore NON si presume: si CALIBRA a zoom 100 %, dove `dpr` vale 1 e
        #    il conto e' fra interi.  ⚠ Chrome disegna la sua cornice dentro la
        #    finestra X (bordo 0, barra 15); Firefox si tiene **10 px** di
        #    maniglia di ridimensionamento (bordo 10, barra 0, perche' ha le
        #    barre sovrapposte).  Sottrarre 15 a tutt'e due — che e' quel che
        #    faceva la prima stesura di questo banco — avrebbe dato 63 righe
        #    rosse su un motore sano: la forma d'errore 3.11, il sospetto va
        #    prima sulla misura.
        barra_fis = round(s["barra"] * s["dpr"])
        # ⛔⭐ LA VERITA' ESTERNA, RIGA PER RIGA: la vista letta SUI PIXEL dello
        #    schermo X.  ⚠ Non passa da `dpr`, da `innerWidth`, da `clientWidth`
        #    ne' da nessuna riga del prodotto.
        cal = B.calibra(os.path.join(
            CARTELLA, "06-b37-cal-%s-%s-%d.rgb24"
            % (NOME, etichetta.replace(" ", "").replace("%", "pc"), L)))
        nota = []
        if vista[0] % 2:
            nota.append("vista L DISPARI")
        if tela[0] > vista[0] or tela[1] > vista[1]:
            nota.append("tela > vista")
        r = {"tipo": "numeri", "zoom": etichetta, "dpr": s["dpr"],
             "finestra_x": [g["l"], g["a"]],
             "finestra_x_pos": [g["x"], g["y"]], "cw": s["cw"], "ch": s["ch"],
             "iw": s["iw"], "ih": s["ih"], "barra": s["barra"],
             "barra_fisica": barra_fis,
             "vista": vista, "tela": tela, "screen": [s["sw"], s["sh"]],
             "fisica_da_iw": fisica, "chiesta": L,
             "vista_pixel": ([cal["l"], cal["a"]] if cal else None),
             "vista_pixel_max": ([cal["l_max"], cal["a_max"]] if cal else None),
             "origine_pixel": ([cal["ox"], cal["oy"]] if cal else None)}
        righe.append(r)
        scrivi(r)
        print("        %-9s %-9s %-7s %-11s %-11s %-11s %-6s %s"
              % ("%dx%d" % (g["l"], g["a"]), "%dx%d" % (s["cw"], s["ch"]),
                 s["barra"], "%dx%d" % tuple(vista), "%dx%d" % tuple(tela),
                 ("%dx%d" % (cal["l"], cal["a"])) if cal else "⛔ niente",
                 "si" if pari else "⛔NO", " · ".join(nota)), flush=True)

# ---------------------------------------------------------------------------
print("\n== 06-b37 · %s — il verdetto" % NOME, flush=True)
guasti = 0
per_zoom = {}
for r in righe:
    per_zoom.setdefault(r["zoom"], {})[r["chiesta"]] = r
# ---------------------------------------------------------------------------
# ⛔⭐ LE RIGHE CHE NON SONO UN ESITO — e si riconoscono DA FUORI, non da un
#    bordo calibrato.  Due motivi, distinti perche' vogliono cure diverse:
#
#      · la FINESTRA X non si e' stretta (il gestore o il motore ha rifiutato):
#        `xwininfo` non da' la misura chiesta;
#      · il CONTENUTO non ci sta nella finestra: le strisce di calibrazione
#        cadono FUORI dal rettangolo della finestra letto con `xwininfo`.  E'
#        il minimo del motore, ⚠ e su Chrome succede sotto ~500 px.
#
# ⛔ Prima questo si deduceva da `|fisica_da_iw + BORDO − finestra_x| > 2`, cioe'
#    dallo stesso conto che poi assolveva A2: le righe si scartavano col metro
#    che dovevano mettere alla prova.
for r in righe:
    r["senza_pixel"] = r["vista_pixel"] is None
    r["finestra_non_stretta"] = abs(r["finestra_x"][0] - r["chiesta"]) > 1
    if r["vista_pixel"]:
        ox, oy = r["origine_pixel"]
        gx, gy = r["finestra_x_pos"]
        r["contenuto_fuori"] = (
            ox < gx - 1
            or ox + r["vista_pixel"][0] > gx + r["finestra_x"][0] + 1)
        # ⛔⭐ E IL TERZO MOTIVO, che si e' visto solo su Gecko — 22 agosto 2026.
        #    Sotto il suo minimo **Firefox non stringe il riquadro di
        #    impaginazione**: `clientWidth` resta grande, la finestra X si
        #    stringe lo stesso, e quel che c'e' dentro viene **TAGLIATO dal
        #    bordo della finestra**.  ⇒ La striscia fotografata esce fino a
        #    **210 px** piu' corta di `clientWidth × dpr`.
        #    ⚠ Non e' una scena: e' un motore che dipinge meno di quel che
        #      impagina.  E il confronto e' fra DUE NUMERI DEL BROWSER
        #      (`clientWidth × dpr` e i pixel), non fra il banco e il prodotto:
        #      ⛔ nessun difetto della pagina puo' nascondersi qui, perche'
        #      `misura_vista()` non entra in nessuno dei due membri.
        amm = int(math.ceil(r["dpr"])) + 1
        r["motore_taglia"] = (
            abs(r["vista_pixel"][0] - r["cw"] * r["dpr"]) > amm
            or abs(r["vista_pixel"][1] - r["ch"] * r["dpr"]) > amm)
    else:
        r["contenuto_fuori"] = False
        r["motore_taglia"] = False
    r["rifiutata"] = (r["senza_pixel"] or r["finestra_non_stretta"]
                      or r["contenuto_fuori"] or r["motore_taglia"])

buone = [r for r in righe if not r["rifiutata"]]
senza = [r for r in righe if r["senza_pixel"]]
non_strette = [r for r in righe
               if r["finestra_non_stretta"] and not r["senza_pixel"]]
fuori_fin = [r for r in righe if r["contenuto_fuori"] and not r["senza_pixel"]]
tagliate = [r for r in righe if r["motore_taglia"] and not r["senza_pixel"]]
print("    --  righe: %d misurate · %d giudicabili · %d senza calibrazione · "
      "%d finestra non stretta · %d contenuto fuori dalla finestra · %d in cui "
      "il MOTORE impagina piu' grande di quel che dipinge (e taglia)"
      % (len(righe), len(buone), len(senza), len(non_strette), len(fuori_fin),
         len(tagliate)), flush=True)
if tagliate:
    print("    ⚠   e le %d righe tagliate sono queste, dichiarate invece che "
          "scartate in silenzio: %s"
          % (len(tagliate),
             [(r["chiesta"], r["cw"], r["vista_pixel"][0]) for r in tagliate]),
          flush=True)
if senza:
    print("    NO  ⛔ %d righe SENZA la lettura sui pixel: non sono zeri, sono "
          "buchi, e con loro A2/A5/A6 avrebbero un denominatore piu' piccolo "
          "di quello dichiarato" % len(senza), flush=True)
    guasti += 1
if not buone:
    print("    NO  nessuna riga giudicabile: non e' un verde, e' un banco vuoto",
          flush=True)
    sys.exit(1)

# ---------------------------------------------------------------------------
# ⛔ LO STRUMENTO SI MISURA PRIMA DI USARLO (`REVIEWER.md` §1 punto 2).  A dpr 1
#    la striscia `width: 100 %` deve valere ESATTAMENTE `clientWidth` pixel: se
#    non li vale, a sbagliare e' il rasterizzatore o la fotografia, e tutti i
#    numeri che seguono ereditano quell'errore.  ⇒ Si misura e si dichiara.
uno = [r for r in buone if abs(r["dpr"] - 1.0) < 1e-9]
if uno:
    scarti = [r["vista_pixel"][0] - r["cw"] for r in uno]
    larghi = [r["vista_pixel_max"][0] - r["vista_pixel"][0] for r in uno]
    peggio_str = max(abs(v) for v in scarti)
    print("    --  lo STRUMENTO, a dpr 1 su %d righe: striscia fotografata − "
          "`clientWidth` = %s px (peggiore |%d|) · larghezza dell'intervallo "
          "stretta→permissiva: %s px"
          % (len(uno), sorted(set(scarti)), peggio_str, sorted(set(larghi))),
          flush=True)
    if peggio_str > 1:
        print("    NO  ⛔ la calibrazione sui pixel sbaglia di %d px a dpr 1: "
              "non e' una verita' esterna, e i verdetti che la usano NON si "
              "danno" % peggio_str, flush=True)
        guasti += 1
else:
    print("    --  nessuna riga a dpr 1: lo strumento non si e' potuto "
          "verificare in questo giro, E SI DICE", flush=True)

# ---------------------------------------------------------------------------
# A1 — la tela chiesta non cambia con lo zoom, a CONTENUTO FISICO uguale.
# ⛔⭐ E LA TOLLERANZA E' DERIVATA, NON SCELTA — 22 agosto 2026.  Prima era `2`,
#    e lo scarto peggiore misurato era **esattamente 2**: cioe' la `[?]` «lo
#    zoom falsa la tela» veniva chiusa da un numero che la sfiorava.
#    ⇒ Con `W` pixel veri di contenuto e zoom `r`: `cw` e' un intero di pixel
#      CSS, quindi `vista = floor(cw·r) ∈ (W − r, W]` e `tela = vista − (vista
#      mod 2) ∈ [W − ceil(r), W]`.  Fra due zoom `r1`, `r2` lo scarto massimo
#      LEGALE e' `max(ceil(r1), ceil(r2))`.  ⚠ A 100 % contro 150 % fa 2, ed e'
#      un 2 DERIVATO: se lo scarto fosse 3 sarebbe rosso, e prima no.
per_zoom = {}
for r in buone:
    per_zoom.setdefault(r["zoom"], {})[r["chiesta"]] = r
zoom_visti = [e for _, e in ZOOM if e in per_zoom]
if len(ZOOM) < 2:
    # ⛔⭐ 22 agosto 2026: con un FATTORE del dispositivo forzato c'e' UN solo
    #    zoom per costruzione, e A1 — che confronta due zoom — non e' una
    #    domanda che si possa porre.  ⚠ Qui c'era `guasti += 1`, cioe' `numeri`
    #    era ROSSO PER SEMPRE a fattore forzato, e per questo non l'ha mai
    #    lanciato nessuno cosi'.  Una domanda non posta non e' una risposta
    #    sbagliata: si DICHIARA (`CODER.md` §3.10).
    print("    --  A1 NON POSTA: con un fattore del dispositivo forzato (%s) "
          "c'e' un solo zoom, e A1 confronta due zoom.  ⚠ Non e' un verde e "
          "non e' un rosso: e' una domanda che questo giro non fa" % FATTORE,
          flush=True)
elif len(zoom_visti) < 2:
    print("    NO  meno di due zoom giudicabili su %d chiesti: A1 non si puo' "
          "giudicare" % len(ZOOM), flush=True)
    guasti += 1
else:
    confronti, sforati = 0, []
    peggio, ammesso_peggio = 0, 0
    for L in LARGHEZZE:
        tele = []
        for z in zoom_visti:
            r = per_zoom[z].get(L)
            # ⛔ Si confrontano solo le righe in cui il CONTENUTO VERO in pixel
            #    e' lo stesso: due zoom su due contenuti diversi sono due scene.
            if r:
                tele.append((z, tuple(r["vista_pixel"]), tuple(r["tela"]),
                             r["dpr"]))
        base = [t for t in tele if t[1] == tele[0][1]] if tele else []
        if len(base) < 2:
            continue
        for z, _, t, dpr in base[1:]:
            confronti += 1
            d = max(abs(t[0] - base[0][2][0]), abs(t[1] - base[0][2][1]))
            ammesso = max(math.ceil(dpr), math.ceil(base[0][3]))
            if d > peggio:
                peggio, ammesso_peggio = d, ammesso
            if d > ammesso:
                sforati.append((L, base[0][0], base[0][2], z, t, ammesso))
    if confronti == 0:
        print("    NO  A1: nessuna coppia di zoom sullo STESSO contenuto "
              "fisico: la domanda non e' stata posta", flush=True)
        guasti += 1
    elif not sforati:
        print("    OK  A1: la tela chiesta NON cambia con lo zoom oltre il "
              "consentito (scarto peggiore %d px, massimo DERIVATO %d, su %d "
              "confronti a contenuto fisico uguale)"
              % (peggio, ammesso_peggio, confronti), flush=True)
    else:
        print("    NO  A1: ⛔ %d confronti su %d in cui la tela cambia con lo "
              "zoom oltre il massimo derivato:" % (len(sforati), confronti),
              flush=True)
        for L, z0, t0, z1, t1, amm in sforati[:8]:
            print("        finestra X %d · zoom %s tela %s contro zoom %s tela "
                  "%s (massimo legale %d)" % (L, z0, t0, z1, t1, amm),
                  flush=True)
        guasti += 1

# ---------------------------------------------------------------------------
# ⚠ IL BORDO DEL MOTORE resta, ma SOLO come diagnostica: non giudica piu'
#   niente.  ⛔ Era la «verita' esterna» di A2 e A6, ed era una moda calibrata
#   sulle righe che poi giudicava — `xwininfo` si semplificava via.
conta = {}
for r in buone:
    b = r["finestra_x"][0] - r["fisica_da_iw"]
    conta[b] = conta.get(b, 0) + 1
BORDO = max(conta, key=lambda k: conta[k]) if conta else 0
print("    --  (diagnostica) bordo del motore, moda su %d righe: %d px %s · "
      "barra di scorrimento %d px fisici — ⛔ NON e' piu' una verita' esterna "
      "e non giudica niente"
      % (len(buone), BORDO, conta, buone[0]["barra_fisica"]), flush=True)

# ---------------------------------------------------------------------------
# A2 — il controllo esterno VERO: la vista che la pagina dichiara e' quella che
#      il rasterizzatore ha davvero disegnato.  ⛔ BIDIREZIONALE.
fuori = []
peggiore = 0
for r in buone:
    # ⛔ Lo scarto e' rispetto all'INTERVALLO [stretta, permissiva]: dentro
    #    l'intervallo vale zero, fuori vale la distanza dal bordo piu' vicino.
    def _fuori(v, lo, hi):
        return 0 if lo <= v <= hi else (v - hi if v > hi else v - lo)
    dl = _fuori(r["vista"][0], r["vista_pixel"][0], r["vista_pixel_max"][0])
    da = _fuori(r["vista"][1], r["vista_pixel"][1], r["vista_pixel_max"][1])
    r["scarto_vista"] = [dl, da]
    peggiore = max(peggiore, abs(dl), abs(da))
    if abs(dl) > 1 or abs(da) > 1:
        fuori.append(r)
if not fuori:
    print("    OK  A2: la VISTA dichiarata dalla pagina combacia con quella "
          "letta SUI PIXEL entro 1 px, in tutte le %d righe (scarto peggiore "
          "%d px, e il confronto e' nei due versi)" % (len(buone), peggiore),
          flush=True)
else:
    print("    NO  A2: ⛔ %d righe su %d in cui la vista dichiarata si scosta "
          "di piu' di 1 px da quella VERA:" % (len(fuori), len(buone)),
          flush=True)
    for r in fuori[:6]:
        print("        zoom %-6s finestra X %d · cw=%d dpr=%s ⇒ vista "
              "dichiarata %s · vista sui PIXEL %s ⇒ scarto %s"
              % (r["zoom"], r["finestra_x"][0], r["cw"], r["dpr"], r["vista"],
                 r["vista_pixel"], r["scarto_vista"]), flush=True)
    guasti += 1

# A3 — parita' e limiti.
male = [r for r in buone if r["tela"][0] % 2 or r["tela"][1] % 2
        or not (320 <= r["tela"][0] <= 7680)
        or not (240 <= r["tela"][1] <= 4320)]
if not male:
    print("    OK  A3: la tela chiesta e' sempre pari e dentro i limiti di §4.5 "
          "(%d righe)" % len(buone), flush=True)
else:
    print("    NO  A3: %d tele fuori regola, es. %s"
          % (len(male), male[0]["tela"]), flush=True)
    guasti += 1

# A4 — le viste dispari, che sono legali: si CONTANO, ed e' meta' della risposta
#      alla `[?]` 3 di `SPECIFICHE.md` §6.1-bis («l'arrotondamento puo' produrre
#      un lato dispari, che `RCP.md` §4.5 rifiuta»).  ⛔ L'altra meta' e' che il
#      banco sappia VEDERE una tela dispari, e quella la prova il guasto G5.
disp_v = [r for r in buone if r["vista"][0] % 2 or r["vista"][1] % 2]
disp_t = [r for r in buone if r["tela"][0] % 2 or r["tela"][1] % 2]
print("    --  A4: VISTE con un lato dispari %d su %d (legale, §7.1) · TELE con "
      "un lato dispari %d su %d (§4.5 le rifiuta) — ⛔ il lato dispari della "
      "tela e' reso impossibile dal `n − (n %% 2)` della pagina: che questo "
      "banco sappia vederlo lo prova il guasto **G5** di `06-b37-guasti.py`, "
      "non questa riga"
      % (len(disp_v), len(buone), len(disp_t), len(buone)), flush=True)

# ---------------------------------------------------------------------------
# A5 — ⛔ BIDIREZIONALE: `tela = vista − (vista mod 2)`, quindi lo scarto per
#      lato vale 0 o 1 e nient'altro.  Sotto il minimo di §4.5 si arrotonda IN
#      SU, ed e' l'unica eccezione.
sopra = [r for r in buone if r["vista"][0] >= 320 and r["vista"][1] >= 240]
sotto = [r for r in buone if not (r["vista"][0] >= 320 and r["vista"][1] >= 240)]
male5 = []
for r in sopra:
    dl = r["vista"][0] - r["tela"][0]
    da = r["vista"][1] - r["tela"][1]
    r["manca"] = [dl, da]
    if not (0 <= dl <= 1 and 0 <= da <= 1):
        male5.append(r)
if not male5:
    peggio5 = max((max(r["manca"]) for r in sopra), default=0)
    print("    OK  A5: la tela sta 0 o 1 px sotto la vista, su TUTT'E DUE i "
          "lati e nei DUE versi (%d righe sopra il minimo, mancanza peggiore "
          "%d px) · %d righe sotto il minimo di §4.5, dove si arrotonda IN SU"
          % (len(sopra), peggio5, len(sotto)), flush=True)
else:
    print("    NO  A5: ⛔⛔ %d righe su %d in cui la tela NON e' la vista "
          "troncata al pari:" % (len(male5), len(sopra)), flush=True)
    for r in male5[:8]:
        print("        zoom %-6s finestra X %d · vista %s · tela %s ⇒ manca "
              "%s px  %s"
              % (r["zoom"], r["finestra_x"][0], r["vista"], r["tela"],
                 r["manca"],
                 "(BANDA NERA, colonne di desktop perse)"
                 if max(r["manca"]) > 1 else "(TELA PIU' GRANDE DELLA VISTA)"),
              flush=True)
    guasti += 1
for r in sotto:
    if r["tela"][0] < 320 or r["tela"][1] < 240:
        print("    NO  A5: sotto il minimo la tela dovrebbe essere almeno "
              "320×240 e vale %s" % r["tela"], flush=True)
        guasti += 1
        break

# ---------------------------------------------------------------------------
# A6 — ⛔⭐⭐ LA DOMANDA VERA, con la verita' ESTERNA e nei DUE VERSI.
#      `W − ceil(r) ≤ tela ≤ W`, con `W` letto sui pixel.
# ⚠ E i due membri escono dall'INTERVALLO della calibrazione, non da un punto:
#   il tetto e' la maschera PERMISSIVA, il pavimento la STRETTA.
#
# ⛔⭐ E IL TETTO E' `+ceil(dpr)` E NON `+0` — misurato il 22 agosto 2026, e la
#    ragione NON e' il prodotto:
#
#      `[M]` Chrome 151, `--force-device-scale-factor=1.25`, finestra X
#      1000×760 all'origine dello schermo: le strisce di calibrazione dicono che
#      l'area DIPINTA e' alta **651** pixel del dispositivo (origine y=109,
#      finestra alta 760), e `documentElement.clientHeight` vale **522** — cioe'
#      **652,5** pixel del dispositivo.  ⇒ Il RIQUADRO DI IMPAGINAZIONE del
#      motore e' piu' alto dell'area dipinta di quasi due pixel, e **nessuna API
#      lo dice alla pagina**.  Stesso segno a 1,5 (629 dipinti, 630 impaginati),
#      zero a dpr 1.
#
#    ⇒ Una tela che sfora di `ceil(dpr)` NON e' un difetto della pagina: e' il
#      motore che impagina piu' grande di quel che dipinge.  ⚠ Il prezzo, che si
#      dichiara invece di nasconderlo, e' **una riga di desktop sotto il bordo**
#      a dpr non intero; il conto sta due righe piu' giu' e non e' zero.
oltre, sotto6 = [], []
sforo = []
for r in sopra:
    W, H = r["vista_pixel"]
    Wx, Hx = r["vista_pixel_max"]
    amm = math.ceil(r["dpr"])
    r["fuori_pixel"] = [r["tela"][0] - W, r["tela"][1] - H]
    if max(r["fuori_pixel"]) > 0:
        sforo.append(r)
    if r["tela"][0] > Wx + amm or r["tela"][1] > Hx + amm:
        oltre.append(r)
    elif r["tela"][0] < W - amm or r["tela"][1] < H - amm:
        sotto6.append(r)
if not oltre and not sotto6:
    print("    OK  A6: la tela chiesta sta dentro la finestra VERA e non le "
          "lascia dentro una banda: %d righe, `W − ceil(dpr) ≤ tela ≤ W + "
          "ceil(dpr)` con W letto SUI PIXEL (scarti visti: %s)"
          % (len(sopra),
             sorted(set(tuple(r["fuori_pixel"]) for r in sopra))), flush=True)
else:
    if oltre:
        print("    NO  A6: ⛔⛔ %d righe in cui la pagina CHIEDE UNA TELA PIU' "
              "GRANDE DEL CONTENUTO CHE ESISTE (barra di scorrimento, disegno "
              "tagliato, scala ≠ 1 ⇒ testo interpolato):" % len(oltre),
              flush=True)
        for r in oltre[:8]:
            print("        zoom %-6s contenuto VERO %dx%d px · cw=%d dpr=%s ⇒ "
                  "vista %s ⇒ tela %s  (%+d,%+d)"
                  % (r["zoom"], r["vista_pixel"][0], r["vista_pixel"][1],
                     r["cw"], r["dpr"], r["vista"], r["tela"],
                     r["fuori_pixel"][0], r["fuori_pixel"][1]), flush=True)
    if sotto6:
        print("    NO  A6: ⛔⛔ %d righe in cui la tela e' PIU' PICCOLA del "
              "contenuto oltre il consentito ⇒ banda nera permanente e colonne "
              "di desktop perse:" % len(sotto6), flush=True)
        for r in sotto6[:8]:
            print("        zoom %-6s contenuto VERO %dx%d px · vista %s ⇒ tela "
                  "%s  (%+d,%+d) · massimo legale −%d"
                  % (r["zoom"], r["vista_pixel"][0], r["vista_pixel"][1],
                     r["vista"], r["tela"], r["fuori_pixel"][0],
                     r["fuori_pixel"][1], math.ceil(r["dpr"])), flush=True)
    guasti += 1

# ⛔⭐ E IL CONTO CHE NON DEVE RESTARE MUTO: quante righe chiedono una tela piu'
#    grande dell'area DIPINTA, e di quanto.  ⚠ Non e' un rosso (sopra si dice
#    perche'), ⛔ ma e' il prezzo del riquadro di impaginazione piu' grande del
#    dipinto, e vale una `[?]`: a dpr non intero l'ultima riga del desktop cade
#    sotto il bordo della finestra.
if sforo:
    print("    ⚠   A6-bis: %d righe su %d in cui la tela supera l'area DIPINTA "
          "(di %s px) — ⛔ non e' della pagina, e' il riquadro di impaginazione "
          "del motore che e' piu' grande del dipinto.  ⚠ Il prezzo e' UNA RIGA "
          "di desktop sotto il bordo, e resta `[?]`"
          % (len(sforo), len(sopra),
             sorted(set(max(r["fuori_pixel"]) for r in sforo))), flush=True)
else:
    print("    --  A6-bis: nessuna riga in cui la tela superi l'area dipinta "
          "(%d righe)" % len(sopra), flush=True)

# ---------------------------------------------------------------------------
if saltati:
    print("    ⚠   zoom NON raggiunti, e dichiarati: %s" % ", ".join(saltati),
          flush=True)
    guasti += 1
scrivi({"tipo": "numeri-verdetto", "righe": len(righe),
        "giudicabili": len(buone), "senza_pixel": len(senza),
        "guasti": guasti, "zoom_saltati": saltati,
        "viste_dispari": len(disp_v), "tele_dispari": len(disp_t),
        "tela_oltre_il_dipinto": len(sforo), "sopra_il_minimo": len(sopra)})
if not righe:
    print("    NO  nessuna riga misurata: non e' un verde, e' un banco vuoto",
          flush=True)
    sys.exit(1)
sys.exit(1 if guasti else 0)
