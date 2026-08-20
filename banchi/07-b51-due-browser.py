#!/usr/bin/env python3
"""07-b51 — LA PROVA SU TUTT'E DUE I BROWSER, e la fa il banco, non l'utente.

    python3 banchi/07-b51-due-browser.py [--porta 7730] [--solo chrome|firefox]

⛔ PERCHE' ESISTE — 20 agosto 2026, e la ragione e' una frase dell'utente:
   *«non voglio fare piu' test: hai il controllo del PC, sistema tutto e fai le
   prove su chrome e firefox»*.

⛔⛔ E LA RAGIONE TECNICA E' PIU' FORTE DELLA COMODITA': la cura di
    `DECISIONI.md` §5.4 e' stata misurata su **Firefox soltanto**, e su Chrome
    ha prodotto un difetto che su Firefox non esisteva —
    `transferFromImageBitmap` porta la tela alla misura dell'immagine su
    Firefox e **non** su Chrome (`[M]`, `prima=[16,16] dopo=[16,16]`).
    ⇒ Un solo motore non e' una prova: e' meta' prova.

Che cosa guarda, per ogni browser, e ognuna e' una domanda diversa:

  1. la MISURA della tela   `t.width x t.height` deve valere la tela in vigore.
                            ⛔ E' il difetto di Chrome: un buffer di 16x16
                            stirato dal CSS sembra «immagine sfocata» e rompe
                            l'input, che sono due sintomi di UNA causa.
  2. i CONTATORI            `dipinti == consegnati`, e zero tardive/errori.
  3. l'INPUT, dal capo che RICEVE — si clicca un punto NOTO del desktop e si
                            legge nel registro del SERVER dove e' arrivato.
                            ⭐ E' l'unico controllo che attraversa la
                            conversione delle coordinate: la pagina puo'
                            raccontare quel che vuole, il server dice dove ha
                            premuto davvero (`LEZIONI.md` §1.7).
  4. l'IMMAGINE             la tela in PNG, per l'occhio — l'unico strumento
                            che vede il tratto dopo il magazzino (§1.16).

⚠ E QUEL CHE QUESTO BANCO NON DICE: gira **headless**, cioe' senza GPU.  Su
  Chrome senza GPU HEVC non arriva al pixel, quindi il codec negoziato puo'
  NON essere quello della sessione vera dell'utente.  ⇒ Il difetto degli
  artefatti (§1.16) questo banco non lo vede e non lo cerca.
"""
import argparse, base64, importlib.util as iu, json, os, re, shutil, signal
import subprocess, sys, tempfile, time

QUI = os.path.dirname(os.path.abspath(__file__))
MACCHINA = "192.168.0.2"


def _mod(nome, file):
    s = iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = iu.module_from_spec(s); s.loader.exec_module(m); return m


M = _mod("marionette", "07-b46-marionette.py")
CDP = _mod("cdp", "02-pagina-misura-cdp.py")

a = argparse.ArgumentParser()
a.add_argument("--porta", type=int, default=7730)
a.add_argument("--lavoro", default="/media/REMOTIX/tmp/07-appunti")
a.add_argument("--utente", default="prova")
a.add_argument("--parola", default="prova2026")
a.add_argument("--larghezza", type=int, default=1600)
a.add_argument("--altezza", type=int, default=1000)
a.add_argument("--solo", default="", choices=["", "chrome", "firefox"])
a.add_argument("--fuori", default="/tmp/07-b51")
o = a.parse_args()
os.makedirs(o.fuori, exist_ok=True)
URL = "https://%s:%d/" % (MACCHINA, o.porta)

# ⭐ Il punto del desktop su cui si clicca: l'angolo in alto a sinistra, dove
#   GNOME tiene «Attivita'».  ⛔ Non e' scelto a caso: e' il punto in cui
#   finivano TUTTI i clic quando la conversione era rotta, quindi un clic che
#   ci arriva per caso non distinguerebbe niente — per questo si guarda il
#   punto ARRIVATO, non l'effetto.
BERSAGLI = [(40, 12), None]   # il secondo si calcola: il CENTRO della tela
# ⛔ DUE bersagli, e il secondo e' il controllo positivo del banco
#    (`PIANO.md` §0.3.4).  Col solo angolo, una conversione che collassasse
#    TUTTO nell'angolo — che e' esattamente il difetto del 20 agosto — darebbe
#    verde.  Il centro no: se la conversione e' rotta, il clic al centro
#    arriva lo stesso vicino a (0,0) e il banco lo dice.

LETTURA = """
  const s = (window.REMOTIX && REMOTIX.schermo) || null;
  const t = document.getElementById('schermo');
  if (!s || !t) return null;
  const r = t.getBoundingClientRect();
  return { buffer: [t.width, t.height], tela: [s.tela_l, s.tela_a],
           stile: [t.style.width, t.style.height],
           vetro: [Math.round(r.left), Math.round(r.top),
                   Math.round(r.width), Math.round(r.height)],
           conti: s.conti, formato: s.formato, dipinta: s.dipinta,
           strada: s.bm ? 'bitmaprenderer' : (s.pennello ? 'tela 2D' : 'NESSUNA'),
           errori: s.errori.slice(-4) };
"""


def registro_coda(n=60):
    """Le ultime righe del registro del SERVER — l'altro capo (§1.7)."""
    c = ("printf 'nicfio\\n' | sudo -S -p '' tail -n %d %s/registro.log" %
         (n, o.lavoro))
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                       capture_output=True, text=True)
    return r.stdout


def righe_nuove(prima, dopo):
    """Le righe che nel registro NON c'erano prima.

    ⛔⛔ E la prima stesura di questo banco confrontava invece il NUMERO
        D'ORDINE dell'input (§7.3) — ed era sbagliata, il 20 agosto 2026: quel
        numero riparte da **1 a ogni sessione**, quindi il numero della
        sessione appena aperta e' PIU' PICCOLO di quello lasciato dal browser
        di prima.  ⇒ Il banco diceva «nessun input nuovo» mentre il registro
        del server portava il clic **arrivato giusto**: un rosso del banco
        addosso a un prodotto sano, che e' il modo piu' caro di sbagliare
        (`LEZIONI.md` §1.2).
    ⚠ Il confronto e' per riga INTERA, e le righe portano l'ora: due clic
      identici in istanti diversi restano due righe diverse."""
    viste = set(prima.splitlines())
    return [r for r in dopo.splitlines() if r not in viste]


def ultimo_puntatore(testo):
    """L'ultimo punto ARRIVATO al server, e da quale messaggio."""
    ultimo = None
    for riga in testo.splitlines():
        m = re.search(r"(PUNTATORE|PULSANTE) \((\d+),(\d+)\)", riga)
        if m:
            ultimo = (m.group(1), int(m.group(2)), int(m.group(3)))
    return ultimo


def palco_libero(quanto=60):
    """⛔ Aspetta che la sessione di «prova» sia DAVVERO finita prima di
    aprirne un'altra.

    ⚠ §5.1 ne ammette una sola per utente, e un browser UCCISO non chiude la
      sessione: il server se ne accorge allo scadere del tempo morto di QUIC —
      `[M]` 20 agosto 2026, **oltre 20 secondi**.  ⇒ Il secondo browser
      trovava il palco occupato e il banco diceva «buffer 16x16, tela 0x0»,
      cioe' accusava la PAGINA di un difetto del BANCO."""
    t0 = time.time()
    while time.time() - t0 < quanto:
        coda = registro_coda(120)
        if "ne restano 0" in coda or "l'ultima sessione di" in coda:
            time.sleep(2)
            return True
        time.sleep(2)
    return False


def esamina(nome, leggi, clicca, tela_png):
    """Le quattro domande, per un browser.  Torna il verdetto."""
    v = {"browser": nome, "guai": []}
    r = leggi()
    if not r:
        v["guai"].append("la pagina non espone REMOTIX.schermo")
        return v
    v.update(r)

    # 1. la MISURA
    if r["buffer"] != r["tela"]:
        v["guai"].append("⛔ il buffer %s NON e' la tela %s: l'immagine e' "
                         "rimpicciolita e l'input si converte sbagliato"
                         % (r["buffer"], r["tela"]))
    # 2. i CONTATORI
    c = r["conti"]
    if c["dipinti"] != c["consegnati"]:
        v["guai"].append("⛔ dipinti %d != consegnati %d"
                         % (c["dipinti"], c["consegnati"]))
    for k in ("tardive", "scartati_ordine", "scartati_misura", "buchi"):
        if c.get(k):
            v["guai"].append("⛔ %s = %d (atteso 0)" % (k, c[k]))
    if r["errori"]:
        v["guai"].append("⛔ errori della pagina: %s" % r["errori"])

    # 3. l'INPUT, letto dal capo che riceve
    vx, vy, vl, va = r["vetro"]
    tl, ta = r["tela"]
    v["clic"] = []
    for bersaglio in BERSAGLI:
        bx, by = bersaglio if bersaglio else (tl // 2, ta // 2)
        coda_prima = registro_coda(400)
        # dal punto del DESKTOP al punto della PAGINA, con la geometria di adesso
        px = vx + bx * vl / float(tl or 1)
        py = vy + by * va / float(ta or 1)
        clicca(px, py)
        time.sleep(2.5)
        nuove = righe_nuove(coda_prima, registro_coda(600))
        # ⛔ «e' arrivato» non e' «c'e' una riga giusta nel registro»: una riga
        #    VECCHIA sarebbe identica.  ⇒ Si guarda SOLO fra le righe nuove.
        dopo = ultimo_puntatore("\n".join(nuove))
        c1 = {"desktop_voluto": [bx, by], "pagina": [round(px), round(py)],
              "arrivato": dopo, "righe_nuove": len(nuove)}
        v["clic"].append(c1)
        if not dopo:
            v["guai"].append("⛔ nessun punto NUOVO al server per il bersaglio "
                             "(%d,%d): il clic non e' arrivato" % (bx, by))
            continue
        dx, dy = abs(dopo[1] - bx), abs(dopo[2] - by)
        c1["scarto"] = [dx, dy]
        if dx > 3 or dy > 3:
            v["guai"].append("⛔ il clic e' arrivato in (%d,%d) invece che in "
                             "(%d,%d): la conversione delle coordinate sbaglia "
                             "di (%d,%d)" % (dopo[1], dopo[2], bx, by, dx, dy))
    # 4. l'IMMAGINE
    d = tela_png()
    if d and d.startswith("data:image/png;base64,"):
        with open(os.path.join(o.fuori, "tela-%s.png" % nome), "wb") as f:
            f.write(base64.b64decode(d.split(",", 1)[1]))
        v["png"] = os.path.join(o.fuori, "tela-%s.png" % nome)
    else:
        v["guai"].append("⛔ la tela non si e' potuta leggere")
    return v


# ── FIREFOX, col protocollo Marionette ────────────────────────────────────
def firefox():
    p, m, prof = M.accendi(porta=2861, headless=True,
                           largo=o.larghezza, alto=o.altezza)
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(o.larghezza, o.altezza)
        m.vai(URL)
        m.js("""document.getElementById('utente').value = arguments[0];
                document.getElementById('parola').value = arguments[1];
                document.getElementById('vai').click(); return true;""",
             [o.utente, o.parola])
        t0 = time.time()
        acceso = False
        while time.time() - t0 < 40:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                acceso = True
                break
            time.sleep(0.5)
        if not acceso:
            # ⛔ Un banco che non entra DEVE dire perche': il registro della
            #    pagina porta gia' la frase del server.
            raise RuntimeError("⛔ lo schermo non si e' acceso in 40 s — ultime "
                               "righe della pagina: " + (m.js(
                "return document.getElementById('registro').innerText.slice(-500)"
            )["value"] or "(registro vuoto)"))
        time.sleep(4)

        def clicca(x, y):
            m.chiama("WebDriver:PerformActions", {"actions": [{
                "type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
                "actions": [{"type": "pointerMove", "duration": 60,
                             "x": int(x), "y": int(y)},
                            {"type": "pointerDown", "button": 0},
                            {"type": "pause", "duration": 80},
                            {"type": "pointerUp", "button": 0}]}]})

        return esamina("firefox",
                       lambda: m.js(LETTURA)["value"],
                       clicca,
                       lambda: m.js("const t=document.getElementById('schermo');"
                                    "try { return t.toDataURL('image/png'); }"
                                    "catch (e) { return 'ERRORE ' + e; }")["value"])
    finally:
        M.spegni(p, prof)


# ── CHROME, col protocollo di diagnosi (CDP) ──────────────────────────────
def chrome():
    t = tempfile.mkdtemp(prefix="b51-")
    br = subprocess.Popen(
        ["google-chrome", "--headless=new", "--no-sandbox",
         "--user-data-dir=%s/profilo" % t, "--no-first-run",
         "--no-default-browser-check", "--disable-sync",
         "--remote-debugging-port=9711",
         "--remote-allow-origins=*",
         "--window-size=%d,%d" % (o.larghezza, o.altezza), "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        b = CDP.pagina(9711, attesa=40)
        c = CDP.Cdp(b["webSocketDebuggerUrl"], timeout=180)
        c.chiama("Page.enable"); c.chiama("Runtime.enable")
        c.chiama("Network.enable")
        c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        c.chiama("Page.navigate", url=URL)
        time.sleep(4)
        # ⛔ L'interstiziale del certificato si BATTE, non si aggira con un
        #   flag: e' la stessa scelta di `02-pagina-misura-prova.py`, e toglie
        #   dalla misura una cosa in meno rispetto a `--ignore-certificate-errors`.
        if c.valuta("!!document.getElementById('proceed-link')", attendi=False) \
           or "Privacy" in (c.valuta("document.title", attendi=False) or ""):
            for ch in "thisisunsafe":
                for tipo in ("keyDown", "char", "keyUp"):
                    p = {"type": tipo, "text": ch} if tipo == "char" \
                        else {"type": tipo, "key": ch}
                    c.chiama("Input.dispatchKeyEvent", **p)
                time.sleep(0.03)
            time.sleep(5)
        # ⛔ E il modulo si ASPETTA invece di darlo per arrivato: riempire un
        #   campo che non c'e' non lancia, e il banco direbbe «entrato» di una
        #   pagina mai caricata (`LEZIONI.md` §1.9).
        t0 = time.time()
        while time.time() - t0 < 25:
            if c.valuta("!!document.getElementById('utente')", attendi=False):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("⛔ il modulo d'accesso non e' comparso in 25 s: "
                               "titolo «%s»" % c.valuta("document.title",
                                                        attendi=False))
        c.valuta("""document.getElementById('utente').value = %s;
                    document.getElementById('parola').value = %s;
                    document.getElementById('vai').click();"""
                 % (json.dumps(o.utente), json.dumps(o.parola)), attendi=False)
        t0 = time.time()
        acceso = False
        while time.time() - t0 < 40:
            if c.valuta("document.body.dataset.schermo || ''",
                        attendi=False) == "acceso":
                acceso = True
                break
            time.sleep(0.5)
        if not acceso:
            raise RuntimeError("⛔ lo schermo non si e' acceso in 40 s — ultime "
                               "righe della pagina: " + str(c.valuta(
                "document.getElementById('registro').innerText.slice(-500)",
                attendi=False)))
        time.sleep(4)

        def clicca(x, y):
            for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
                p = {"type": tipo, "x": int(x), "y": int(y), "button": "left",
                     "clickCount": 1}
                if tipo == "mouseMoved":
                    p.pop("button"); p.pop("clickCount")
                c.chiama("Input.dispatchMouseEvent", **p)
                time.sleep(0.08)

        return esamina("chrome",
                       lambda: c.valuta("(function () {%s})()" % LETTURA,
                                        attendi=False),
                       clicca,
                       lambda: c.valuta(
                           "(function(){const t=document.getElementById('schermo');"
                           "try{return t.toDataURL('image/png');}"
                           "catch(e){return 'ERRORE '+e;}})()", attendi=False))
    finally:
        try: br.send_signal(signal.SIGTERM); br.wait(timeout=8)
        except Exception:
            try: br.kill()
            except Exception: pass
        shutil.rmtree(t, ignore_errors=True)


esiti = []
for nome, f in (("firefox", firefox), ("chrome", chrome)):
    if o.solo and o.solo != nome:
        continue
    print("\n═══ %s ═══" % nome.upper())
    try:
        v = f()
    except Exception as e:
        v = {"browser": nome, "guai": ["⛔ il banco stesso e' caduto: %r" % e]}
    esiti.append(v)
    print(json.dumps({k: v[k] for k in v if k != "conti"}, indent=1,
                     ensure_ascii=False)[:1600])
    if "conti" in v:
        print(" conti:", {k: x for k, x in v["conti"].items() if x})
    # ⛔ Una sessione per volta: §5.1 ne ammette UNA per utente, e il browser
    #   ucciso non la chiude — la chiude il tempo morto di QUIC.
    if not palco_libero():
        print("   ⚠ il palco non risulta libero dopo 60 s: il giro seguente "
              "potrebbe trovarlo occupato, e si vedra' nel suo verdetto")

with open(os.path.join(o.fuori, "esiti.json"), "w") as f:
    json.dump(esiti, f, indent=1, ensure_ascii=False)
print("\n══════════ VERDETTO ══════════")
for v in esiti:
    if v["guai"]:
        print("⛔ %s: %d guai" % (v["browser"], len(v["guai"])))
        for g in v["guai"]:
            print("   ", g)
    else:
        print("⭐ %s: 4 controlli su 4, e il clic e' arrivato dove doveva"
              % v["browser"])
sys.exit(1 if any(v["guai"] for v in esiti) else 0)
