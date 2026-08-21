#!/usr/bin/env python3
"""07-b53 — LA CORSA DEGLI APPUNTI, sui due browser.

    python3 banchi/07-b53-appunti-corsa.py [--solo chrome|firefox]

⛔ PERCHE' ESISTE — 20 agosto 2026, difetto riferito dall'utente: *«si e'
   bloccato Firefox con la clipboard: dal client al server»*.

   ⚠ E non era un blocco del browser: era la PAGINA che mandava
   `ERRORE_PROTOCOLLO` e chiudeva la sessione — da fuori si vede come
   un'immagine che si ferma.  `[M]` Il registro del server, 19:04:06: la
   sessione ha annunciato **due volte in un millisecondo** lo stesso testo
   (trasferimenti 3 e 4), la pagina ha chiesto il 3, il server l'ha servito
   **col testo attuale** — che e' quel che `RCP.md` §7.4 gli ordina di fare — e
   la pagina l'ha chiamato errore.

⛔⛔ E LO STESSO SBAGLIO ERA SCRITTO NEI DUE CAPI: `rcp.c` chiudeva la sessione
    nel caso speculare (il client che serve una richiesta superata).  ⇒ Questo
    banco esercita la corsa e pretende che la sessione **sopravviva**.

Che cosa fa, per browser:
  1. entra e aspetta il primo fotogramma;
  2. ⭐ annuncia DUE testi diversi a raffica — e' la corsa: la domanda del
     server per il primo arriva quando il secondo e' gia' annunciato;
  3. guarda che la sessione sia ancora viva (fotogrammi che salgono, nessun
     congedo nel registro del server) e che nessuno abbia chiamato
     `ERRORE_PROTOCOLLO`.

⭐ IL CONTROLLO POSITIVO: il banco cerca nel registro del server la riga
   dell'eccezione — «e' la corsa normale fra due che copiano» — perche' un giro
   in cui la corsa NON si e' prodotta sarebbe verde senza aver provato niente.
"""
import argparse, importlib.util as iu, json, os, shutil, signal, subprocess
import sys, tempfile, time

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
a.add_argument("--utente", default="prova",
               help="⛔ l'utente della sessione. Il predefinito «prova» e' quello "
                    "dell'UTENTE: con la sua sessione viva, due server che "
                    "aprono un desktop per lo stesso utente si contendono "
                    "/run/user e il posto e' UNO. ⇒ Da un banco in parallelo "
                    "si passa un utente proprio, come per la porta e il socket.")
a.add_argument("--parola", default="prova2026")
a.add_argument("--solo", default="", choices=["", "chrome", "firefox"])
# ⛔⛔ E L'UTENTE DELLA SESSIONE ATTRAVERSA ANCHE IL LATO SESSIONE — 21 ago 2026.
#
#     Questo banco era parametrico da un lato (l'accesso dal browser) e FISSO
#     su «prova» dall'altro (`id -u prova`, `runuser -u prova`).  ⚠ Il sintomo
#     non era un errore del banco: era **«il desktop remoto ha "Failed to
#     connect to a Wayland server" invece del testo»**, cioe' un VERDETTO
#     ROSSO CONTRO IL PRODOTTO, per un difetto del banco.
#     ⇒ `[M]` 21 agosto: girato con `--utente provai6`, i due versi davano
#       rossi su tutt'e due i motori, e `XDG_RUNTIME_DIR` puntava a
#       `/run/user/1001`, cioe' all'utente dell'UTENTE.
#     ⭐ Un banco parametrico a meta' e' peggio di uno fisso: quello fisso
#       almeno rifiuta di partire.
o = a.parse_args()
URL = "https://%s:%d/" % (MACCHINA, o.porta)

# ⚠ Due testi DIVERSI e di lunghezza diversa: se il difetto della lunghezza
#   tornasse (la misura pretesa su un trasferimento superato), due testi uguali
#   non lo vedrebbero.
UNO = "REMOTIX corsa appunti — primo testo " + "a" * 40
DUE = "REMOTIX corsa appunti — SECONDO testo, piu' lungo " + "b" * 120


def registro(n=250):
    c = ("printf 'nicfio\\n' | sudo -S -p '' tail -n %d %s/registro.log" %
         (n, o.lavoro))
    return subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                          capture_output=True, text=True).stdout


def righe_nuove(prima, dopo):
    viste = set(prima.splitlines())
    return [r for r in dopo.splitlines() if r not in viste]


def giudica(nome, nuove, conti_prima, conti_dopo, vivo, righe_pagina=""):
    guai = []
    # ⭐ La riga dell'eccezione puo' uscire dai DUE capi: dal server quando
    #   serve un trasferimento superato, e dalla pagina quando ne riceve uno.
    corsa = [r for r in nuove if "corsa normale fra due che copiano" in r]
    corsa += [r for r in (righe_pagina or "").splitlines()
              if "corsa normale fra due che copiano" in r]
    congedi = [r for r in nuove
               if "si congeda" in r or "ERRORE_PROTOCOLLO" in r or "viola" in r]
    if congedi:
        guai.append("⛔ la sessione e' stata chiusa: " + congedi[0][:220])
    if not vivo:
        guai.append("⛔ la pagina non e' piu' collegata dopo la corsa")
    if conti_dopo is not None and conti_prima is not None \
       and conti_dopo["consegnati"] < conti_prima["consegnati"]:
        guai.append("⛔ i fotogrammi consegnati sono TORNATI INDIETRO: "
                    "%s → %s" % (conti_prima, conti_dopo))
    if not corsa:
        guai.append("⚠ CONTROLLO POSITIVO MANCATO: nel registro non c'e' la "
                    "riga dell'eccezione di §7.4 — la corsa non si e' prodotta, "
                    "e questo giro NON prova niente")
    return {"browser": nome, "guai": guai,
            "righe_corsa": [r[:160] for r in corsa][:3],
            "conti_prima": conti_prima, "conti_dopo": conti_dopo}


def palco_libero(quanto=60):
    t0 = time.time()
    while time.time() - t0 < quanto:
        if "ne restano 0" in registro(120) or "l'ultima sessione di" in registro(120):
            time.sleep(2)
            return True
        time.sleep(2)
    return False


LEGGI = """
  const s = (window.REMOTIX && REMOTIX.schermo) || null;
  if (!s) return null;
  return { consegnati: s.conti.consegnati, dipinti: s.conti.dipinti,
           errori: s.errori.slice(-3),
           appunti: (window.REMOTIX.appunti_conti ? window.REMOTIX.appunti_conti() : null) };
"""


def copia_due_volte_nella_sessione(uno, due):
    """⭐⭐ LA CORSA VERA, ed e' quella che ha morso l'utente: la SESSIONE
    annuncia due volte a raffica.

    ⛔ `[M]` 20 agosto 2026, registro del server alle 19:04:06: due annunci
    nello stesso millisecondo (trasferimenti 3 e 4), la pagina chiede il 3, il
    server lo serve **col testo attuale** (§7.4 glielo ordina) e la pagina
    chiama errore ⇒ sessione chiusa, e l'utente vede «Firefox si e' bloccato».

    ⇒ Qui si copia DUE VOLTE dentro la sessione Wayland di «prova», a pochi
      millisecondi di distanza: la domanda della pagina per il primo annuncio
      arriva quando il secondo e' gia' in vigore.

    ⚠ Il copione si SPEDISCE invece di comporlo dentro le virgolette di `ssh`:
      tre livelli di citazione (ssh, sudo, sh) sono il posto in cui un banco
      smette di misurare quel che crede."""
    copione = (
        "#!/bin/sh\n"
        "U=$(id -u " + o.utente + ")\n"
        "export XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0\n"
        # ⛔ `wl-copy` RESTA VIVO per servire la selezione: e' il suo mestiere.
        #    ⚠ Lasciandolo attaccato al canale di `ssh`, `ssh` aspetta che
        #    chiuda — cioe' per sempre, e il banco moriva di timeout su un
        #    prodotto sano.  ⇒ Si stacca (`setsid`, uscite chiuse) e si legge
        #    dopo il file di registro.
        # ⚠ Le uscite si chiudono, ma il processo NON si stacca con `&`:
        #    `wl-copy` legge tutto lo stdin, poi si biforca da se' per servire
        #    la selezione.  ⛔ Mandandolo in fondo con `&` moriva prima di
        #    leggere, e la sessione annunciava una clipboard VUOTA — che il
        #    server dichiarava correttamente, e il banco scambiava per «la
        #    corsa non si e' prodotta».
        # ⛔ SEI copie a 15 ms, non due: la finestra della corsa e' la lettura
        #    della clipboard dalla sessione — millisecondi — e due copie
        #    distanti 50 ms non si sovrappongono quasi mai.  ⚠ E il banco lo
        #    dichiara invece di far finta: se la riga dell'eccezione non esce,
        #    il verdetto dice «questo giro NON prova niente».
        "for i in 1 2 3; do\n"
        "  printf '%s-%s' \"$1\" \"$i\" | wl-copy >/dev/null 2>&1\n"
        "  sleep 0.015\n"
        "  printf '%s-%s' \"$2\" \"$i\" | wl-copy >/dev/null 2>&1\n"
        "  sleep 0.015\n"
        "done\n"
        "sleep 0.3\n"
        "echo fatto\n")
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                    "cat > /tmp/b53-copia.sh && chmod +x /tmp/b53-copia.sh"],
                   input=copione, text=True, capture_output=True)
    # ⛔ `runuser` e non un secondo `sudo`: la parola d'ordine e' gia' stata
    #    consumata dal primo, e il secondo la chiedeva di nuovo leggendo
    #    /dev/null — «sudo: a password is required» dentro un banco che
    #    sembrava misurare.
    c = ("printf 'nicfio\\n' | sudo -S -p '' runuser -u " + o.utente + " -- "
         "/tmp/b53-copia.sh %s %s > /tmp/b53.log 2>&1; cat /tmp/b53.log"
         % (json.dumps(uno), json.dumps(due)))
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                       capture_output=True, text=True, timeout=60)
    return (r.stdout or "") + (r.stderr or "")


def incolla_nella_sessione():
    """⭐ QUALCUNO NELLA SESSIONE INCOLLA — ed e' il pezzo che mancava.

    ⛔ Il server chiede il testo al client **solo** quando qualcuno di la'
    incolla (§7.4: gli appunti si tirano).  Due annunci a raffica, da soli, non
    producono nessuna corsa: la domanda non parte proprio.
    ⇒ Qui si incolla davvero, con `wl-paste` dentro la sessione Wayland di
      «prova» — e il ritorno e' il testo che il desktop remoto ha ricevuto,
      cioe' il controllo che la catena abbia funzionato e non solo retto."""
    c = ("printf 'nicfio\\n' | sudo -S -p '' bash -c '"
         "U=$(id -u " + o.utente + "); "
         "sudo -u " + o.utente + " XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0 "
         "timeout 8 wl-paste -n 2>&1'")
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                       capture_output=True, text=True)
    return (r.stdout or "").strip()


# ⛔⭐⭐ LA CORSA SI RIPRODUCE COME STATO, NON COME COINCIDENZA — e va detto.
#
# ⚠ La finestra vera dura quanto la lettura della clipboard dalla sessione:
#   `[M]` sotto il millisecondo su rete locale.  Sei copie a raffica non
#   l'hanno aperta nemmeno una volta, e un banco che aspettasse la coincidenza
#   sarebbe verde per fortuna, non per merito.
#
# ⇒ Qui si mette la pagina ESATTAMENTE nello stato che ha chiuso la sessione
#   dell'utente: si chiede un trasferimento e si fa arrivare — prima della
#   risposta — un annuncio piu' nuovo.  La risposta del server portera' il
#   numero vecchio, che e' il caso di §7.4 «servito col testo attuale».
#
# ⛔ E' bianco: tocca `APPUNTI.suo_id`, che e' roba interna della pagina.  Si
#    dichiara invece di far credere che sia una corsa vera — e quel che
#    verifica e' la REGOLA, non il tempismo.
CORSA = """
  const A = window.REMOTIX.appunti;
  const vecchio = A.suo_id;
  if (!vecchio) return { guaio: "nessun annuncio vivo da chiedere" };
  const c = new Uint8Array(4);
  new DataView(c.buffer).setUint32(0, vecchio);
  window.REMOTIX.appunti_manda(window.REMOTIX.appunti_tipi.CHIEDI, c);
  A.chiesti.add(vecchio);
  /* l'annuncio piu' nuovo, che nella realta' arriva dal filo */
  A.suo_id = vecchio + 1;
  A.suo_len = 999999;
  return { chiesto: vecchio, ora_vivo: A.suo_id };
"""


def firefox():
    p, m, prof = M.accendi(porta=2895, headless=True, largo=1400, alto=900)
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(1400, 900); m.vai(URL)
        m.js(f"""document.getElementById('utente').value='{o.utente}';
                document.getElementById('parola').value='{o.parola}';
                document.getElementById('vai').click(); return true;""")
        t0 = time.time()
        while time.time() - t0 < 40:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                break
            time.sleep(0.5)
        time.sleep(3)
        prima = registro(300)
        c1 = m.js(LEGGI)["value"]
        copia_due_volte_nella_sessione(UNO, DUE)
        time.sleep(2)
        print("   corsa:", m.js(CORSA)["value"])
        time.sleep(3)
        c2 = m.js(LEGGI)["value"]
        vivo = bool(m.js("return !!(window.REMOTIX && REMOTIX.schermo) && "
                         "!!REMOTIX.schermo.sessione")["value"])
        righe = m.js("return document.getElementById('registro').innerText.slice(-1200)")["value"]
        return giudica("firefox", righe_nuove(prima, registro(500)), c1, c2, vivo, righe)
    finally:
        M.spegni(p, prof)


def chrome():
    t = tempfile.mkdtemp(prefix="b53-")
    br = subprocess.Popen(
        ["google-chrome", "--headless=new", "--no-sandbox",
         "--user-data-dir=%s/p" % t, "--no-first-run",
         "--no-default-browser-check", "--remote-debugging-port=9715",
         "--remote-allow-origins=*", "--window-size=1400,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        b = CDP.pagina(9715, attesa=40)
        c = CDP.Cdp(b["webSocketDebuggerUrl"], timeout=180)
        for x in ("Page.enable", "Runtime.enable", "Network.enable"):
            c.chiama(x)
        c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        c.chiama("Page.navigate", url=URL)
        time.sleep(4)
        if c.valuta("!!document.getElementById('proceed-link')", attendi=False) \
           or "Privacy" in (c.valuta("document.title", attendi=False) or ""):
            for ch in "thisisunsafe":
                for tipo in ("keyDown", "char", "keyUp"):
                    pp = {"type": tipo, "text": ch} if tipo == "char" \
                         else {"type": tipo, "key": ch}
                    c.chiama("Input.dispatchKeyEvent", **pp)
                time.sleep(0.03)
            time.sleep(5)
        t0 = time.time()
        while time.time() - t0 < 25 and not c.valuta(
                "!!document.getElementById('utente')", attendi=False):
            time.sleep(0.5)
        c.valuta(f"""document.getElementById('utente').value='{o.utente}';
                    document.getElementById('parola').value='{o.parola}';
                    document.getElementById('vai').click();""", attendi=False)
        t0 = time.time()
        while time.time() - t0 < 40:
            if c.valuta("document.body.dataset.schermo || ''", attendi=False) == "acceso":
                break
            time.sleep(0.5)
        time.sleep(3)
        prima = registro(300)
        c1 = c.valuta("(function(){%s})()" % LEGGI, attendi=False)
        copia_due_volte_nella_sessione(UNO, DUE)
        time.sleep(2)
        print("   corsa:", c.valuta("(function(){%s})()" % CORSA, attendi=False))
        time.sleep(3)
        c2 = c.valuta("(function(){%s})()" % LEGGI, attendi=False)
        vivo = bool(c.valuta("!!(window.REMOTIX && REMOTIX.schermo) && "
                             "!!REMOTIX.schermo.sessione", attendi=False))
        righe = c.valuta("document.getElementById('registro').innerText.slice(-1200)",
                         attendi=False)
        return giudica("chrome", righe_nuove(prima, registro(500)), c1, c2, vivo, righe)
    finally:
        try: br.send_signal(signal.SIGTERM); br.wait(timeout=8)
        except Exception: br.kill()
        shutil.rmtree(t, ignore_errors=True)


if not palco_libero(30):
    print("⚠ il palco non risulta libero: il primo giro potrebbe trovarlo occupato")

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
    print(json.dumps(v, indent=1, ensure_ascii=False)[:1200])
    palco_libero()

print("\n══════════ VERDETTO ══════════")
for v in esiti:
    if v["guai"]:
        print("⛔ %s:" % v["browser"])
        for g in v["guai"]:
            print("   ", g)
    else:
        print("⭐ %s: la corsa si e' prodotta e la sessione e' SOPRAVVISSUTA"
              % v["browser"])
sys.exit(1 if any(v["guai"] for v in esiti) else 0)
