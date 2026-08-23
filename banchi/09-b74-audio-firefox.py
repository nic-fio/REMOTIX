#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b74 — ⛔⭐⭐ LA CURA DELL'AUDIO, col **FIREFOX VERO**, perche' il banco di
         stamattina non poteva vederla.

═══ PERCHE' ESISTE, e non e' un doppione di `07-b64-rete.py` ════════════════
`fasi/09` §3.16: la cura 4 vive **tutta dentro `pagina.html`**
(`audio_posto_passato()`, `:5882`) e **non tocca un byte del binario**.  Il
cliente di prova (`01-b3-cliente.py`) non carica quel file: ha **la sua copia
della regola vecchia** (`istante <= self.a_ultimo_istante`, `:743`), identica
nei due alberi.  ⇒ ⛔ **Qualunque giro fatto con quel cliente misura se
stesso**, e la previsione «0,175 → ≥ 0,95» e' uscita 0,1149 → 0,1235: non
smentiva la cura, smentiva il banco.

⭐⭐ E NON SERVE NEMMENO CAMBIARE IL METRO.  La strada (ii) di §3.16: la pagina
   manda **da sola** i suoi conti al server ogni 5 secondi
   (`pagina.html:6304`, `fetch("/diario?" + riga)`), e il server li scrive nel
   registro.  ⇒ **il registro del prodotto e' il verbale**, e non c'e' nessuno
   strumento nuovo da fidarsi.

═══ ⛔ E IL «PRIMA» E IL «DOPO» SONO DUE FILE, NON DUE BINARI ════════════════
`main.c` legge la pagina **da disco** all'avvio (`pagina.c:627`).  ⇒ lo stesso
identico server serve ora l'una ora l'altra, e **l'unica variabile e' la
pagina**:

  · PRIMA  `/media/REMOTIX/src/09-src/src/pagina.html`  — `:6341`,
           `istante <= a.ultimo_istante` ⇒ `scartati_vecchi++`
  · DOPO   `/media/REMOTIX/src/09c-src/src/pagina.html` — `audio_posto_passato()`,
           e tre contatori al posto di uno: `vecchi` · `tardivi` · `fuori`

═══ ⛔⛔ E NON E' UNO SPECCHIO — la coppia di sessioni, dichiarata ═══════════
Firefox gira nella sessione di **`prova`** (uid 1001) e si collega come
**`prova2`** (uid 1002), che e' la sessione catturata dalla 7920.  ⇒ il
browser guarda un desktop **che non e' il suo**: niente anello su se stesso.
⚠ Se girasse dentro la sessione che sta guardando, ogni suo pixel rientrerebbe
  nella cattura e la misura non varrebbe niente.

═══ ⭐ IL CONTROLLO POSITIVO — come so che il banco sa vedere il difetto ═════
E' il braccio **PRIMA** stesso: con la pagina vecchia e `netem delay 20ms 2ms`
la purezza deve **crollare**.  ⛔ Se il PRIMA esce pulito, lo stimolo non
stimola e il DOPO non dimostra niente — gli imputati tornano a essere due.

Uso (dal portatile):
    python3 banchi/09-b74-audio-firefox.py prima --secondi 60
    python3 banchi/09-b74-audio-firefox.py dopo  --secondi 60
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time, urllib.parse

QUI = os.path.dirname(os.path.abspath(__file__))
def _m(n, f):
    s = importlib.util.spec_from_file_location(n, os.path.join(QUI, f))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
b68 = _m("b68", "09-b68-ritmo.py")
b71 = _m("b71", "09-b71-risveglio.py")
b64 = _m("b64", "07-b64-rete.py")   # ⭐ il tono: gia' scritto, non si riscrive

root, rem = b68.root, b68.rem
LAV = b68.LAV
UID_FF = int(os.environ.get("UID_FF", "1001"))       # dove gira il browser
UT_FF = os.environ.get("UT_FF", "prova")
UT_SESS = os.environ.get("UT_SESS", "prova2")        # chi si collega
PAROLA = os.environ.get("PAROLA_UTENTE", "prova2026")
PAG_PRIMA = os.environ.get("PAG_PRIMA", "/media/REMOTIX/src/09-src/src/pagina.html")
PAG_DOPO = os.environ.get("PAG_DOPO", "/media/REMOTIX/src/09c-src/src/pagina.html")
FUORI = os.environ.get("FUORI", "/tmp/09-b74")

# ⭐ La riga che la pagina manda al server ogni 5 s.  ⚠ Il PRIMA ne ha meno
#   campi del DOPO: si leggono quelli che ci sono, e si dichiara.
R_DIARIO = re.compile(r"audio: ricevuti (\d+) suonati (\d+) BUCHI (\d+) vecchi (\d+)"
                      r"(?: tardivi (\d+) fuori (\d+))?")


def accendi(pagina, extra=""):
    rc, out, err = root("env ALBERO=/media/REMOTIX/src/09c-src PAGINA=%s "
                        "sh %s/09-riavvia-7920.sh %s" % (pagina, LAV, extra), 300)
    for r in (out + err).splitlines():
        if r.startswith(("albero:", "md5", "pagina:", "server ")) or "VERIFICATO" in r:
            print("   %s" % r)
    return "fuori da ogni sessione utente" in out


def firefox(url):
    """⛔ Da root, e si SCENDE all'uid di chi possiede il compositore: solo lui
       puo' parlare col suo Wayland.  E' la disciplina di `09-b72-video.sh`."""
    root("pkill -u %d -f firefox 2>/dev/null; true" % UID_FF); time.sleep(1)
    prof = "/tmp/b74-ff"
    # ⛔⛔ E IL `bash -c` NON E' UN VEZZO — secondo inciampo della stessa
    #    famiglia, 23 ago 12:49.  `root()` mette `sudo` davanti al comando: con
    #    `a; b; c` **solo `a` gira da root**, `b` e `c` li fa `nicfio`.  ⇒ la
    #    cartella del profilo restava di `nicfio`, Firefox (che gira come
    #    `prova`) non poteva scriverci `prefs.js`, e non apriva Marionette.
    #    ⚠ Il sintomo era «Marionette non ha aperto la porta»: di nuovo un
    #      difetto MIO travestito da difetto del browser.
    root("bash -c 'rm -rf %s && mkdir -p %s && chown %d:%d %s'"
         % (prof, prof, UID_FF, UID_FF, prof))
    # ⛔ `acceptInsecureCerts` di Marionette non basta da solo per un
    #    certificato che non e' mai stato visto: si dichiara ANCHE qui.
    prefs = "\n".join([
        'user_pref("marionette.port", 2829);',
        'user_pref("browser.shell.checkDefaultBrowser", false);',
        'user_pref("browser.startup.homepage_override.mstone", "ignore");',
        'user_pref("browser.aboutwelcome.enabled", false);',
        'user_pref("datareporting.policy.dataSubmissionEnabled", false);',
        'user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);',
        'user_pref("media.autoplay.default", 0);',
        'user_pref("media.autoplay.blocking_policy", 0);',
        'user_pref("full-screen-api.allow-trusted-requests-only", false);',
    ])
    # ⛔⛔ NIENTE HEREDOC DENTRO `root()` — pagato il 23 agosto 2026, 12:47.
    #    `root()` e' `printf 'parola' | sudo -S <comando>`: lo standard input e'
    #    GIA' preso dalla parola di sudo, e il corpo dell'heredoc non arriva
    #    mai.  ⇒ `user.js` e' uscito di ZERO byte, Marionette ha aperto la sua
    #    porta di serie invece della mia, e il banco ha detto «Marionette non
    #    ha aperto la porta» — cioe' ha accusato Firefox di un difetto mio.
    #    ⚠ E' la forma peggiore: un file VUOTO ha la faccia di un file scritto.
    loc = "/tmp/b74-user.js"
    with open(loc, "w") as f:
        f.write(prefs + "\n")
    subprocess.run(["scp", "-q", "-o", "BatchMode=yes", loc,
                    "%s:/tmp/b74-user.js" % b68.MACCHINA], check=True)
    root("install -m 644 -o %d -g %d /tmp/b74-user.js %s/user.js"
         % (UID_FF, UID_FF, prof))
    rc, out, _ = root("wc -c %s/user.js" % prof)
    if not out.strip().startswith(tuple("123456789")):
        raise SystemExit("⛔ user.js e' vuoto: %s" % out.strip())
    print("   profilo: %s" % out.strip())
    root("bash -c \"setsid nohup setpriv --reuid=%d --regid=%d --init-groups "
         "env -i HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 MOZ_ENABLE_WAYLAND=1 "
         "GDK_BACKEND=wayland MOZ_MARIONETTE=1 firefox-esr --profile %s --marionette '%s' "
         ">>%s/b74-ff.log 2>&1 &\"" % (UID_FF, UID_FF, UT_FF, UT_FF, UID_FF, prof, url, LAV))
    for _ in range(40):
        rc, out, _ = root("ss -tln | grep ':2829 ' || true")
        if out.strip():
            return True
        time.sleep(1)
    return False


def marionette(passi):
    """⛔ Marionette ascolta su 127.0.0.1 DELLA MACCHINA: il copione ci va
       sopra, non lo si guida da qui."""
    src = open(os.path.join(QUI, "07-b46-marionette.py")).read()
    prog = src + "\n\n" + passi
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", b68.MACCHINA,
                        "python3 -c \"$(cat)\""],
                       input=prog.encode(), capture_output=True, timeout=400)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def entra():
    """⛔ I nomi dei campi si leggono da `pagina.html:414-418`, non si indovinano:
       il modulo e' `#modulo`, l'utente `#utente`, la parola `#parola`."""
    passi = """
import time as _t
m = Marionette(porta=2829)
m.sessione(insicuri=True)
_t.sleep(3)
print("TITOLO", m.chiama("WebDriver:GetTitle"))
JS = '''
  var u = document.getElementById("utente"), p = document.getElementById("parola");
  if (!u || !p) return "NIENTE MODULO: " + (document.body ? document.body.innerText.slice(0,200) : "?");
  u.value = arguments[0]; u.dispatchEvent(new Event("input", {bubbles:true}));
  p.value = arguments[1]; p.dispatchEvent(new Event("input", {bubbles:true}));
  var f = document.getElementById("modulo");
  if (f.requestSubmit) f.requestSubmit(); else f.submit();
  return "MANDATO";
'''
print("ESITO", m.chiama("WebDriver:ExecuteScript",
      {"script": JS, "args": [%r, %r]}))
_t.sleep(5)
print("DOPO", m.chiama("WebDriver:GetTitle"))
""" % (UT_SESS, PAROLA)
    return marionette(passi)


def diario(riga0):
    # ⛔ La riga la scrive `pagina.c:334` come «📄 la pagina di … dice: …», e il
    #    testo arriva URL-CODIFICATO (`encodeURIComponent`): gli spazi sono
    #    `%20`.  ⚠ Cercare gli spazi qui darebbe ZERO righe e la faccia di «la
    #    pagina non ha mandato niente» — che e' un'altra cosa.
    rc, reg, _ = root("tail -n +%d %s/registro.log | grep -a 'la pagina di' || true"
                      % (riga0 + 1, LAV), 300)
    reg = urllib.parse.unquote(reg)
    fuori = []
    for m in R_DIARIO.finditer(reg):
        fuori.append({"ricevuti": int(m.group(1)), "suonati": int(m.group(2)),
                      "buchi": int(m.group(3)), "vecchi": int(m.group(4)),
                      "tardivi": int(m.group(5)) if m.group(5) else None,
                      "fuori_ordine": int(m.group(6)) if m.group(6) else None})
    return fuori, reg


def giro(quale, secondi, ritardo):
    os.makedirs(FUORI, exist_ok=True)
    pagina = PAG_PRIMA if quale == "prima" else PAG_DOPO
    print("== 09-b74 · l'audio col Firefox VERO — braccio «%s»" % quale)
    d = b71.pulizia()
    if not d["pulita"]:
        return {"guasto": "⛔ non si misura in due sulla stessa macchina"}

    print("\n== il server, con la pagina del «%s»" % quale)
    root("pkill -f '01-b3-cliente[.]py'; true"); time.sleep(2)
    root("pkill -u %d -f firefox; true" % UID_FF); time.sleep(1)
    root("rm -f %s/registro.log; true" % LAV)
    if not accendi(pagina):
        return {"guasto": "il server non e' partito"}

    # ⛔⛔ E PRIMA SERVE UN MONITOR PER IL BROWSER — pagato subito, 23 ago 12:45.
    #    La sessione headless di `prova` c'e' e ha il suo socket Wayland, ma
    #    **nessun monitor**: il monitor lo crea il `remotix-figlio` quando un
    #    client si attacca (I4), e senza di lui Firefox muore su
    #    `gdk_monitor_get_workarea: assertion 'GDK_IS_MONITOR (monitor)' failed`
    #    e Marionette non apre mai la sua porta.
    # ⭐ Quindi il cliente di prova serve ancora — ma per un ALTRO mestiere:
    #    non misura niente, fa da **fabbrica di monitor** per la sessione che
    #    ospita il browser.  ⚠ E gira sullo STESSO server (7920), non su una
    #    porta in piu': un server serve piu' utenti, e due porte sarebbero due
    #    banchi.
    print("\n== il monitor per il browser: una sessione «%s» sulla stessa 7920"
          % UT_FF)
    if not b71.sessione_apri("b74-monitor", 3600, utente=UT_FF, tela="1600x900"):
        return {"guasto": "la sessione «%s» (quella che regge il browser) non si e' aperta" % UT_FF}
    for _ in range(30):
        rc, o, _ = root("pgrep -u %d -f 'remotix-figlio --figlio-intern[o]' | head -1" % UID_FF)
        if o.strip():
            break
        time.sleep(1)
    else:
        return {"guasto": "nessun figlio per «%s»: il monitor non e' nato" % UT_FF}
    time.sleep(4)

    print("\n== Firefox nella sessione di «%s» (uid %d), collegato come «%s»"
          % (UT_FF, UID_FF, UT_SESS))
    if not firefox("https://192.168.0.2:7920/"):
        rc, log, _ = root("tail -20 %s/b74-ff.log" % LAV)
        return {"guasto": "Marionette non ha aperto la porta 2829: %s" % log[-500:]}
    rc, out, err = entra()
    print("   %s" % (out + err).strip()[:600])

    # ⛔ «Si e' collegato» lo dice il PRODOTTO, non il browser.
    acceso = False
    for _ in range(40):
        rc, o, _ = root("grep -ac 'canale video ACCESO' %s/registro.log" % LAV)
        if o.strip().isdigit() and int(o.strip()) > 0:
            acceso = True; break
        time.sleep(2)
    if not acceso:
        rc, log, _ = root("tail -30 %s/registro.log" % LAV)
        return {"guasto": "nessun «canale video ACCESO» in 80 s:\n%s" % log[-900:]}
    print("   ⭐ il canale video e' acceso: e' il PRODOTTO a dirlo")
    time.sleep(6)

    # ⛔ E SENZA SUONO NON C'E' NIENTE DA RIORDINARE: il tono va suonato dentro
    #    la sessione GUARDATA (`prova2`), non dentro quella del browser.
    print("\n== il tono a 440 Hz dentro la sessione di «%s»" % UT_SESS)
    if not b64.tono_accendi():
        return {"guasto": "⛔ il tono NON suona nella sessione: si misurerebbe silenzio"}
    print("   ⭐ il grafo ha i legami: il tono suona davvero")
    time.sleep(4)

    riga0 = b68.righe_registro()
    print("\n== ⛔ la rete: netem %s sulla 7920 di `lo`, guardiano armato" % ritardo)
    b68.guardiano_arma(secondi + 180)
    ok, q = b68.stringi(ritardo.split())
    if not ok:
        b68.rimetti(); return {"guasto": q}
    print("   %s" % q.replace("\n", " | ")[:200])
    time.sleep(secondi)
    b68.rimetti()

    righe, reg = diario(riga0)
    with open(os.path.join(FUORI, "diario-%s.log" % quale), "w") as f:
        f.write(reg)
    if len(righe) < 2:
        return {"guasto": "⛔ la pagina non ha mandato abbastanza righe «/diario» "
                          "(%d): senza, non c'e' verbale" % len(righe)}
    a, b = righe[0], righe[-1]
    dr = b["ricevuti"] - a["ricevuti"]
    ds = b["suonati"] - a["suonati"]
    e = {"quale": quale, "pagina": pagina, "righe": len(righe),
         "ricevuti": dr, "suonati": ds,
         "purezza": round(ds / dr, 4) if dr else None,
         "vecchi": b["vecchi"] - a["vecchi"], "buchi": b["buchi"] - a["buchi"]}
    if b["tardivi"] is not None:
        e["tardivi"] = b["tardivi"] - a["tardivi"]
        e["fuori_ordine"] = b["fuori_ordine"] - a["fuori_ordine"]
    print("\n== ⭐ %s: ricevuti %d, suonati %d ⇒ PUREZZA %s · vecchi %d · buchi %d%s"
          % (quale, dr, ds, e["purezza"], e["vecchi"], e["buchi"],
             (" · tardivi %d · fuori %d" % (e["tardivi"], e["fuori_ordine"]))
             if "tardivi" in e else ""))
    b64.tono_spegni()
    root("pkill -u %d -f firefox; true" % UID_FF)
    b71.sessione_chiudi()
    with open(os.path.join(FUORI, "esito-%s.json" % quale), "w") as f:
        json.dump(e, f, indent=1, ensure_ascii=False)
    return e


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["prima", "dopo"])
    p.add_argument("--secondi", type=int, default=60)
    p.add_argument("--ritardo", default="delay 20ms 2ms")
    a = p.parse_args()
    print(json.dumps(giro(a.passo, a.secondi, a.ritardo), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    principale()
