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
  A2  `innerWidth × devicePixelRatio` = la larghezza VERA della finestra in
      pixel del dispositivo, letta FUORI dal browser con `xwininfo`, entro 1 px.
      ⛔ E' il controllo esterno: senza, A1 direbbe solo che la pagina e'
      coerente con se' stessa.
  A3  la TELA chiesta e' sempre PARI su tutt'e due i lati e dentro
      320..7680 × 240..4320 (`RCP.md` §4.5).
  A4  la VISTA puo' uscire DISPARI — ed e' legale (`RCP.md` §7.1: «qualunque
      misura da 1×1 in su, dispari compresa»).  Si conta quante volte succede.
  A5  la TELA chiesta non e' MAI piu' grande della vista, ⚠ tranne sotto il
      minimo di §4.5, dove il codice arrotonda IN SU a 320×240 e lo dichiara
      (`src/pagina.html:1437`).  ⇒ li' l'avanzo torna come banda: e' l'unico
      caso in cui la scala NON puo' valere 1.

⛔ IL CONTROLLO POSITIVO (`CODER.md` §3.3, §3.10): lo zoom DEVE essere entrato
   in vigore davvero, e lo dice `devicePixelRatio`, non il tasto premuto.  Se
   non ci arriva, il giro di quello zoom non e' un esito e non si registra come
   tale — «i due numeri sono uguali» sarebbe vero anche non avendo toccato
   niente (`banchi/01-s5-tela.sh`, rilievo R3.10).
"""
import json
import subprocess
import sys
import time
import urllib.request

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
    d["iniezione"] = "no"
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


def scegli_finestra():
    """⛔ Un browser apre piu' finestre X (Chrome ne ha di invisibili da 1×1):
       si prende la piu' grande, e si DICE quale."""
    migliore, area = None, -1
    for w in finestre():
        g = geometria(w)
        if not g:
            continue
        if g["l"] * g["a"] > area:
            migliore, area = (w, g), g["l"] * g["a"]
    return migliore


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
    print("        %-9s %-9s %-7s %-11s %-11s %-6s %s"
          % ("fin.X", "cw×ch", "barra", "vista", "tela", "pari", "nota"),
          flush=True)
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
        nota = []
        if vista[0] % 2:
            nota.append("vista L DISPARI")
        if tela[0] > vista[0] or tela[1] > vista[1]:
            nota.append("tela > vista")
        r = {"tipo": "numeri", "zoom": etichetta, "dpr": s["dpr"],
             "finestra_x": [g["l"], g["a"]], "cw": s["cw"], "ch": s["ch"],
             "iw": s["iw"], "ih": s["ih"], "barra": s["barra"],
             "barra_fisica": barra_fis,
             "vista": vista, "tela": tela, "screen": [s["sw"], s["sh"]],
             "fisica_da_iw": fisica, "chiesta": L}
        righe.append(r)
        scrivi(r)
        print("        %-9s %-9s %-7s %-11s %-11s %-6s %s"
              % ("%dx%d" % (g["l"], g["a"]), "%dx%d" % (s["cw"], s["ch"]),
                 s["barra"], "%dx%d" % tuple(vista), "%dx%d" % tuple(tela),
                 "si" if pari else "⛔NO", " · ".join(nota)), flush=True)

# ---------------------------------------------------------------------------
print("\n== 06-b37 · %s — il verdetto" % NOME, flush=True)
guasti = 0
per_zoom = {}
for r in righe:
    per_zoom.setdefault(r["zoom"], {})[r["chiesta"]] = r

# A1 — la tela chiesta non cambia con lo zoom, a finestra FISICA uguale.
zoom_visti = [e for _, e in ZOOM if e in per_zoom]
if len(zoom_visti) < 2:
    print("    NO  meno di due zoom misurati: A1 non si puo' giudicare",
          flush=True)
    guasti += 1
else:
    peggio, dove = 0, None
    for L in LARGHEZZE:
        tele = []
        for z in zoom_visti:
            r = per_zoom[z].get(L)
            # ⛔ Si confrontano solo le righe in cui la FINESTRA VERA e' la
            #    stessa: se il gestore delle finestre ha dato misure diverse,
            #    confrontare le tele sarebbe confrontare due scene.
            if r:
                tele.append((z, tuple(r["finestra_x"]), tuple(r["tela"])))
        base = [t for t in tele if t[1] == tele[0][1]] if tele else []
        if len(base) < 2:
            continue
        for _, _, t in base[1:]:
            d = max(abs(t[0] - base[0][2][0]), abs(t[1] - base[0][2][1]))
            if d > peggio:
                peggio, dove = d, (L, base)
    if peggio <= 2:
        print("    OK  A1: la tela chiesta NON cambia con lo zoom "
              "(scarto peggiore %d px, su %d larghezze)" % (peggio, len(LARGHEZZE)),
              flush=True)
    else:
        print("    NO  A1: la tela cambia con lo zoom di %d px — %s"
              % (peggio, dove), flush=True)
        guasti += 1

# ---------------------------------------------------------------------------
# ⛔ IL BORDO DEL MOTORE, CALIBRATO a zoom 100 % — e si pretende costante.
# ⛔ Il bordo si calibra sul giro a dpr 1 se c'e'; con un FATTORE forzato non
#    c'e', e allora si calibra sull'unico giro — il conto e' fra numeri con la
#    virgola e lo scarto ammesso resta 1 px.
cento = [r for r in righe if r["zoom"] == "100 %"] or righe
conta = {}
for r in cento:
    b = r["finestra_x"][0] - r["fisica_da_iw"]
    conta[b] = conta.get(b, 0) + 1
if conta:
    # ⛔ Il bordo e' il valore PIU' FREQUENTE, non l'unico: le finestre che il
    #    motore ha rifiutato di stringere danno ciascuna un «bordo» diverso e
    #    falso (su Firefox: −49, −120, −200…).  ⚠ Pretendere l'unicita' faceva
    #    scegliere −120 e mandava a monte tutto il resto del verdetto — un
    #    banco che si autoavvelena con le righe che dovrebbe scartare.
    BORDO = max(conta, key=lambda k: conta[k])
    quota = conta[BORDO] / len(cento)
    print("    --  bordo del motore, calibrato a zoom 100 %% su %d larghezze: "
          "%d px (concorde nel %.0f %% delle righe) · barra di scorrimento "
          "%d px fisici" % (len(cento), BORDO, 100 * quota,
                            cento[0]["barra_fisica"]), flush=True)
    if quota < 0.6:
        print("    NO  il bordo non e' stabile (%s): A6 non si puo' giudicare"
              % conta, flush=True)
        guasti += 1
else:
    BORDO = 0
    print("    NO  nessuna riga a zoom 100 %: il bordo non si puo' calibrare",
          flush=True)
    guasti += 1

for r in righe:
    r["bordo"] = BORDO
    r["contenuto_fisico_l"] = r["finestra_x"][0] - BORDO - r["barra_fisica"]
    # ⛔ Il motore puo' RIFIUTARE di stringere la finestra sotto un suo minimo:
    #    la finestra X si stringe, il contenuto no, e si misurerebbe una scena
    #    che non esiste.  Si riconosce cosi', e si dichiara.
    r["rifiutata"] = abs(r["fisica_da_iw"] + BORDO - r["finestra_x"][0]) > 2

buone = [r for r in righe if not r["rifiutata"]]
rifiutate = [r for r in righe if r["rifiutata"]]
if rifiutate:
    print("    ⚠   %d righe SCARTATE: il motore non ha stretto la finestra "
          "(minimo suo, es. X=%d ma contenuto %d px) — non sono un esito"
          % (len(rifiutate), rifiutate[0]["finestra_x"][0],
             rifiutate[0]["fisica_da_iw"]), flush=True)

# A2 — il controllo esterno: il conto della pagina SEGUE la finestra vera.
fuori = [r for r in buone
         if abs(r["fisica_da_iw"] + BORDO - r["finestra_x"][0]) > 1]
peggiore = max((abs(r["fisica_da_iw"] + BORDO - r["finestra_x"][0])
                for r in buone), default=0)
if not fuori:
    print("    OK  A2: `innerWidth × dpr` + bordo = la finestra letta con "
          "xwininfo entro 1 px, in tutte le %d righe (scarto peggiore %d px)"
          % (len(buone), peggiore), flush=True)
else:
    print("    NO  A2: %d righe su %d in cui il conto della pagina si scosta "
          "di piu' di 1 px dalla finestra vera:" % (len(fuori), len(buone)),
          flush=True)
    for r in fuori[:6]:
        print("        zoom %s finestra %d → iw=%d dpr=%s ⇒ %d + bordo %d"
              % (r["zoom"], r["finestra_x"][0], r["iw"], r["dpr"],
                 r["fisica_da_iw"], BORDO), flush=True)
    guasti += 1

# A3 — parita' e limiti.
male = [r for r in buone if r["tela"][0] % 2 or r["tela"][1] % 2
        or not (320 <= r["tela"][0] <= 7680) or not (240 <= r["tela"][1] <= 4320)]
if not male:
    print("    OK  A3: la tela chiesta e' sempre pari e dentro i limiti di §4.5",
          flush=True)
else:
    print("    NO  A3: %d tele fuori regola, es. %s" % (len(male), male[0]["tela"]),
          flush=True)
    guasti += 1

# A4 — le viste dispari, che sono legali: si CONTANO.
disp = [r for r in buone if r["vista"][0] % 2 or r["vista"][1] % 2]
print("    --  A4: viste con un lato DISPARI: %d su %d (legale, §7.1) — "
      "e sono le righe in cui la tela perde un pixel per la parita'"
      % (len(disp), len(buone)), flush=True)

# A5 — tela > vista solo sotto il minimo.
oltre = [r for r in buone if r["tela"][0] > r["vista"][0]
         or r["tela"][1] > r["vista"][1]]
sotto_minimo = [r for r in oltre if r["vista"][0] < 320 or r["vista"][1] < 240]
if len(oltre) == len(sotto_minimo):
    print("    OK  A5: la tela supera la vista SOLO sotto il minimo di §4.5 "
          "(%d righe) — li' l'avanzo e' banda, e la scala non puo' valere 1"
          % len(oltre), flush=True)
else:
    print("    NO  A5: %d righe con tela > vista SOPRA il minimo:"
          % (len(oltre) - len(sotto_minimo)), flush=True)
    for r in oltre:
        if r not in sotto_minimo:
            print("        zoom %s vista %s tela %s"
                  % (r["zoom"], r["vista"], r["tela"]), flush=True)
    guasti += 1

# ⛔⭐ A6 — LA DOMANDA VERA, e non passa da nessun numero del browser: la TELA
#    che la pagina chiede sta DENTRO la finestra che esiste?  Una tela piu'
#    larga della finestra e' `scala < 1` ⇒ niente `pixelated` ⇒ testo
#    interpolato: e' il difetto che l'utente ha giudicato il 14 agosto 2026.
sfora = [r for r in buone
         if r["tela"][0] > r["contenuto_fisico_l"] and r["vista"][0] >= 320]
if not sfora:
    print("    OK  A6: la tela chiesta sta SEMPRE dentro la finestra vera "
          "(%d righe, verita' esterna: xwininfo − bordo %d − barra)"
          % (len(buone), BORDO), flush=True)
else:
    print("    NO  A6: ⛔⛔ %d righe in cui la pagina CHIEDE UNA TELA PIU' LARGA "
          "DELLA FINESTRA CHE ESISTE:" % len(sfora), flush=True)
    for r in sfora:
        print("        zoom %-6s finestra X %d − barra %d = %d fisici · "
              "cw=%d dpr=%s ⇒ vista %d ⇒ tela %d  (%+d)"
              % (r["zoom"], r["finestra_x"][0], r["barra_fisica"],
                 r["contenuto_fisico_l"], r["cw"], r["dpr"], r["vista"][0],
                 r["tela"][0], r["tela"][0] - r["contenuto_fisico_l"]),
              flush=True)
    guasti += 1

if saltati:
    print("    ⚠   zoom NON raggiunti, e dichiarati: %s" % ", ".join(saltati),
          flush=True)
    guasti += 1
if not righe:
    print("    NO  nessuna riga misurata: non e' un verde, e' un banco vuoto",
          flush=True)
    sys.exit(1)
sys.exit(1 if guasti else 0)
