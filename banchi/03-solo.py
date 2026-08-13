#!/usr/bin/env python3
"""⛔⛔ L'ARBITRO DELLA FINESTRA ESCLUSIVA — «sono solo, o sto misurando la contesa?»

⭐ Nasce il 13 agosto 2026 sera, e non da un'idea: da **due giri di griglia interi
buttati** perche' il prodotto dell'utente stava ciclando accanto, e da un giro
dell'anello in cui **un altro banco girava al 74 % di CPU con load 3,8** e il
numero non lo diceva.

Il piano della sessione lo pretende in §0-bis, con queste parole:

    Il banco che misura un tempo controlla di essere solo, e lo scrive accanto
    al numero: carico della macchina, quali altre sessioni grafiche sono vive,
    quali altre porte :76xx rispondono, quanti processi del prodotto girano.
    ⭐ E se non e' solo, RIFIUTA di misurare invece di consegnare un numero.
    Un numero preso con un vicino che cicla ha lo stesso aspetto di uno buono.

⛔ Era scritto in un piano e **non esisteva da nessuna parte**: ogni banco se lo
sarebbe riscritto a modo suo, e «solo» avrebbe voluto dire cinque cose diverse.

## Come si usa

    import importlib.util, os
    _s = importlib.util.spec_from_file_location(
        "solo", os.path.join(os.path.dirname(__file__), "03-solo.py"))
    solo = importlib.util.module_from_spec(_s); _s.loader.exec_module(solo)

    scena = solo.guarda()                  # il dizionario da scrivere ACCANTO al numero
    solo.pretendi(scena)                   # ⛔ alza RuntimeError se non sei solo

Da riga di comando:

    python3 banchi/03-solo.py             # stampa la scena, esce 1 se non sei solo
    python3 banchi/03-solo.py --json      # la stessa cosa, da mettere nel verbale
    python3 banchi/03-solo.py --prova      # ⭐ la CERTIFICAZIONE: sa dire di no?

⚠ **QUEL CHE QUESTO ARBITRO NON PUO' FARE, detto qui e non in fondo:**

  1. ⛔ **Guarda UNA macchina sola: la sua.** L'anello del ritardo attraversa
     NIC-OS *e* CHUWI ⇒ chi lo misura deve girarlo **da tutt'e due le parti** e
     unire le due scene. Un giro «solo» su CHUWI mentre il server e' carico e'
     un numero contaminato che si dichiara pulito.
  2. ⚠ **Il carico e' una fotografia**, non una sorveglianza: un vicino che si
     accende a meta' misura non lo vede nessuno. ⇒ Si guarda **PRIMA e DOPO**,
     e `pretendi()` da solo non basta: c'e' `confronta()` apposta.
  3. ⛔ **Non sa distinguere il proprio rumore da quello d'altri**: se il banco
     stesso ha gia' acceso il suo browser, quella CPU e' sua e conta lo stesso.
     ⇒ Si chiama **prima** di accendere la propria scena.
  4. ⚠ **Gli schermi X altrui li REGISTRA ma non li GIUDICA**, ed e' una scelta:
     un `Xvfb` acceso e fermo non costa niente, e bocciare su di lui vorrebbe
     dire non misurare mai. ⛔ Ma uno schermo su cui un altro banco **disegna**
     costa, e li' a dirlo e' il carico, non l'elenco. ⇒ Chi legge il verbale
     l'elenco ce l'ha; chi vuole la severita' piena guarda `carico` **e**
     `schermi_x` insieme.
"""
import json
import os
import re
import subprocess
import sys
import time

# ⛔ Le tre porte dell'utente. Si LEGGONO e non si toccano — e si contano prima
#    e dopo ogni passo, che e' quel che ha permesso di dire «non le ho toccate»
#    invece di crederlo.
PROTETTE = (7448, 7501, 7561)

# ⚠ Le soglie sono dichiarate qui, in un posto solo, e non sono «sicure»:
#    sono quelle sotto cui i numeri del 13 agosto sono stati presi buoni.
#    Chi le cambia cambia il significato della parola «solo», e deve dirlo.
CARICO_MASSIMO = 1.0      # load average a 1 minuto
CPU_VICINO_MAX = 20.0     # % di un singolo processo che non sia mio
TMP_LIBERO_MIN = 300      # MB liberi su /tmp: sotto, Chrome non apre il profilo


def _uscita(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def guarda(mie_porte=(), miei_pid=()):
    """La scena di QUESTA macchina, adesso.

    `mie_porte` e `miei_pid` sono quel che il banco riconosce come **suo**:
    senza, l'arbitro accuserebbe il banco di essere il vicino di se' stesso.
    """
    miei_pid = set(int(p) for p in miei_pid) | {os.getpid()}
    scena = {"macchina": os.uname().nodename, "ora": time.strftime("%FT%T%z")}

    # ⛔ Il carico: la prima cosa, ed e' quella che ha buttato i due giri.
    try:
        with open("/proc/loadavg") as f:
            c = f.read().split()
        scena["carico"] = [float(c[0]), float(c[1]), float(c[2])]
        scena["processi_attivi"] = c[3]
    except (OSError, ValueError, IndexError):
        scena["carico"] = None

    # ⚠ Le porte :76xx che rispondono, meno le mie e meno le protette.
    porte = set()
    for riga in _uscita(["ss", "-ltn"]).splitlines()[1:]:
        for m in re.finditer(r":(7[0-9]{3})\b", riga):
            porte.add(int(m.group(1)))
    scena["porte_protette_vive"] = sorted(p for p in porte if p in PROTETTE)
    scena["porte_altrui"] = sorted(p for p in porte
                                   if p not in PROTETTE and p not in mie_porte)
    scena["porte_mie"] = sorted(p for p in porte if p in mie_porte)

    # ⛔ I vicini affamati: chiunque mangi CPU e non sia mio.
    vicini = []
    for riga in _uscita(["ps", "-eo", "pcpu,pid,comm",
                         "--sort=-pcpu"]).splitlines()[1:12]:
        pezzi = riga.split(None, 2)
        if len(pezzi) < 3:
            continue
        try:
            pcpu, pid = float(pezzi[0]), int(pezzi[1])
        except ValueError:
            continue
        # ⚠ `ps` stesso e' sempre in testa al proprio elenco: non e' un vicino.
        if pid in miei_pid or pezzi[2].strip() == "ps":
            continue
        if pcpu >= CPU_VICINO_MAX:
            vicini.append({"pcpu": pcpu, "pid": pid, "chi": pezzi[2].strip()})
    scena["vicini_affamati"] = vicini

    # ⚠ Le sessioni grafiche vive, che su questo palco sono la contesa vera.
    schermi = sorted(f for f in os.listdir("/tmp/.X11-unix")) \
        if os.path.isdir("/tmp/.X11-unix") else []
    scena["schermi_x"] = schermi
    scena["processi_del_prodotto"] = len(
        [r for r in _uscita(["ps", "-eo", "comm"]).splitlines()
         if r.strip() == "remotix"])

    # ⚠ `/tmp` e' una risorsa condivisa: quando si riempie, Chrome non apre il
    #   profilo e il banco fallisce con un errore che ACCUSA LA PAGINA.
    try:
        s = os.statvfs("/tmp")
        scena["tmp_liberi_mb"] = int(s.f_bavail * s.f_frsize / 1024 / 1024)
    except OSError:
        scena["tmp_liberi_mb"] = None

    scena["solo"], scena["perche"] = _giudica(scena)
    return scena


def _giudica(s):
    guai = []
    if s.get("carico") and s["carico"][0] > CARICO_MASSIMO:
        guai.append("carico a 1 minuto %.2f (massimo %.2f)"
                    % (s["carico"][0], CARICO_MASSIMO))
    for v in s.get("vicini_affamati", []):
        guai.append("un vicino mangia CPU: %s (pid %d) al %.1f %%"
                    % (v["chi"], v["pid"], v["pcpu"]))
    if s.get("porte_altrui"):
        guai.append("porte :76xx che non sono mie ne' protette: %s"
                    % ", ".join(str(p) for p in s["porte_altrui"]))
    if s.get("tmp_liberi_mb") is not None and \
            s["tmp_liberi_mb"] < TMP_LIBERO_MIN:
        guai.append("/tmp ha %d MB liberi (minimo %d): un browser puo' non "
                    "aprire il profilo, e il sintomo accusera' la pagina"
                    % (s["tmp_liberi_mb"], TMP_LIBERO_MIN))
    return (not guai), guai


def pretendi(scena):
    """⛔ Alza `RuntimeError` se la scena non e' esclusiva.

    ⚠ Si alza un'eccezione APPOSTA invece di tornare False: un `if` si dimentica,
      un'eccezione no. E il messaggio porta dentro **la ragione**, perche' chi
      legge il verbale non debba indovinare che cosa c'era intorno."""
    if not scena.get("solo"):
        raise RuntimeError(
            "⛔ NON SONO SOLO — mi RIFIUTO di misurare un tempo:\n    · "
            + "\n    · ".join(scena.get("perche") or ["ragione non registrata"])
            + "\n  ⇒ Un numero preso con un vicino che cicla ha lo stesso "
              "aspetto di uno buono.")


def confronta(prima, dopo):
    """⛔ La scena si legge PRIMA e DOPO: il carico e' una fotografia.

    ⚠ Una guardia che confronta solo i due estremi **non vede un vicino acceso e
      spento nel mezzo** — e' gia' successo, con due punti entrati in tabella
      come se fossero misure. ⇒ Questa funzione dice quel che sa, e **dichiara
      quel che non sa**."""
    guai = []
    if not dopo.get("solo"):
        guai.append("alla fine non ero solo: " + "; ".join(dopo.get("perche", [])))
    p = set(prima.get("porte_altrui", []))
    d = set(dopo.get("porte_altrui", []))
    if d - p:
        guai.append("porte altrui APPARSE durante la misura: %s"
                    % ", ".join(str(x) for x in sorted(d - p)))
    if p - d:
        guai.append("porte altrui SPARITE durante la misura: %s"
                    % ", ".join(str(x) for x in sorted(p - d)))
    return {"regge": not guai, "guai": guai,
            "⚠ quel che questa guardia NON vede":
                "un vicino acceso e spento FRA i due estremi"}


def prova():
    """⭐ LA CERTIFICAZIONE DELL'ARBITRO: sa dire di no?

    ⛔ Un arbitro che dicesse sempre «sei solo» avrebbe lo stesso aspetto di uno
    che funziona, e sarebbe la quinta voce della famiglia «i banchi che si
    autoingannano». ⇒ Qui si fa il ciclo **sano → guasto → risanato**, col
    guasto **vero**: un processo che mangia CPU per davvero.
    """
    print("== 1. SANO — la macchina com'e' adesso")
    a = guarda()
    print("   solo: %s%s" % (a["solo"],
                             "" if a["solo"] else "  ⇒ " + "; ".join(a["perche"])))

    print("\n== 2. GUASTO — accendo io un vicino che cicla, e pretendo un NO")
    # ⚠ Il guasto e' un processo VERO, non una scena finta: se l'arbitro si
    #   lasciasse ingannare da un mock, la certificazione proverebbe il mock.
    vicino = subprocess.Popen(
        [sys.executable, "-c", "\nwhile True: pass\n"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(4)          # ⚠ `pcpu` di `ps` e' una media dalla nascita
        b = guarda()
        visto = any(v["pid"] == vicino.pid for v in b["vicini_affamati"])
        print("   il vicino (pid %d) e' stato visto: %s" % (vicino.pid, visto))
        print("   solo: %s%s" % (b["solo"],
                                 "" if b["solo"] else "  ⇒ " + "; ".join(b["perche"])))
        try:
            pretendi(b)
            alzato = False
        except RuntimeError:
            alzato = True
        print("   `pretendi` ha alzato l'eccezione: %s" % alzato)
    finally:
        vicino.kill()
        vicino.wait()

    print("\n== 3. RISANATO — spento il vicino")
    time.sleep(3)
    c = guarda()
    print("   solo: %s%s" % (c["solo"],
                             "" if c["solo"] else "  ⇒ " + "; ".join(c["perche"])))

    # ⛔ IL VERDETTO, e sta nel CODICE D'USCITA, non nella prosa: tre banchi che
    #    uscivano sempre 0 sono gia' costati una giornata.
    print("\n== IL VERDETTO")
    # ⛔⛔ E L'ORDINE DI QUESTI DUE CONTROLLI E' STATO CORRETTO IL 13 AGOSTO
    #    SERA, DOPO CHE HA SBAGLIATO IN FACCIA A CHI L'AVEVA SCRITTO.
    #
    #    Prima veniva `not visto or not alzato` ⇒ BOCCIATO, e solo dopo la
    #    scena sporca ⇒ NON GIUDICABILE.  Girato su una macchina con cinque
    #    agenti addosso, ha stampato **BOCCIATO** un arbitro sano: su una
    #    macchina gia' contesa il vicino finto puo' non emergere fra i primi,
    #    e il banco lo leggeva come «l'arbitro non sa vedere».
    #
    #    ⇒ **La scena sporca viene PRIMA del verdetto**, sempre: se al passo 1
    #    la macchina non era libera, nessuna delle due risposte del passo 2 e'
    #    interpretabile.  E' la stessa forma di `LEZIONI.md` §2.0 applicata a
    #    se' stesso — *«non c'e'» e «non ho potuto guardare» hanno lo stesso
    #    aspetto* — e questa volta a cascarci e' stato il banco scritto per
    #    dirlo agli altri.
    if not a["solo"]:
        print("   ⚠ NON GIUDICABILE: la macchina non era libera nemmeno al passo "
              "sano ⇒ NESSUNA delle due risposte del passo 2 e' interpretabile.")
        print("      ⇒ " + "; ".join(a["perche"]))
        print("      ⭐ Non e' un rosso dell'arbitro: e' una scena sporca, e si "
              "rifa' quando la macchina e' ferma.")
        return 2
    if not visto or not alzato:
        print("   ⛔ BOCCIATO: col vicino acceso l'arbitro NON ha detto di no")
        return 1
    if c["solo"]:
        print("   ⭐ PROMOSSO: sano SI', guasto NO, risanato SI'.")
        return 0
    print("   ⛔ BOCCIATO: dopo aver spento il vicino l'arbitro dice ancora di no")
    print("      ⇒ " + "; ".join(c["perche"]))
    return 1


if __name__ == "__main__":
    if "--prova" in sys.argv:
        sys.exit(prova())
    s = guarda()
    if "--json" in sys.argv:
        print(json.dumps(s, ensure_ascii=False))
    else:
        print("== LA SCENA di %s alle %s" % (s["macchina"], s["ora"]))
        for k, v in s.items():
            if k not in ("macchina", "ora", "solo", "perche"):
                print("   %-24s %s" % (k, v))
        if s["solo"]:
            print("\n   ⭐ SOLO: un tempo misurato adesso e' un tempo, non una contesa")
        else:
            print("\n   ⛔ NON SOLO — chi misura un tempo adesso misura la contesa:")
            for g in s["perche"]:
                print("      · %s" % g)
    sys.exit(0 if s["solo"] else 1)
