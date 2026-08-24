#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b86-predefiniti — LE CINQUE CURE SI ACCENDONO NEL PRODOTTO, E LO SI PROVA.

    porta 7980 · utente `provanr11` (uid 1080)
    albero `/media/REMOTIX/src/09nr11-src` · lavoro `/media/REMOTIX/tmp/09nr11`
    unita' `remotix-7980` · ban-file e socket suoi

═══════════════════════════════════════════════════════════════════════════════
⛔ DA DOVE NASCE — e non e' una misura nuova, e' una CONSEGNA
═══════════════════════════════════════════════════════════════════════════════

Il 24 agosto 2026 l'utente ha deciso: *«il prodotto cambia in meglio; questa
fase era per rendere piu' solido il funzionamento di remotix su reti degradate,
senza pretendere di fare miracoli»*.  ⇒ Le **cinque** cure della fase 9 si
accendono nel prodotto, e ognuna resta spegnibile.

⛔ **PERCHE' PRIMA ERANO SPENTE**: l'invariante I6 — *cio' che cambia quel che
   l'utente vede resta dietro un interruttore spento finche' non l'ha guardato*.
   ⚠ In v1 una fase intera fu AZZERATA per aver consegnato miglioramenti che il
   regista non aveva mai visto.  ⭐ Adesso il presupposto e' soddisfatto: ha
   guardato (§19.6, §20.3) e ha deciso.  ⇒ I6 non e' aggirata, e' stata
   percorsa fino in fondo — l'interruttore c'e' ancora, e' girato dall'altra
   parte.

Le cinque, e il loro CONTRATTO (i nomi sono quel che i banchi batteranno):

| cura                    | predefinito nuovo      | come si spegne            |
|---|---|---|
| soglia sulla coda video | **100 ms**             | `--sgombra-soglia-ms 0`   |
| regolatore del ritmo    | **acceso**             | `--niente-ritmo-adattivo` |
| linea morta             | **accesa** (5000 · 10) | `--niente-linea-morta`    |
| sfratto del fantasma    | **15 000 ms**          | `--sfratto-ms 0`          |
| silenzio dell'audio     | **acceso**             | `--niente-audio-silenzio` |

⛔ **UNA STRADA SOLA PER CIASCUNA.**  I due nomi vecchi — `--ritmo-adattivo` e
   `--linea-morta` — volevano dire «accendi»: col predefinito acceso non
   vogliono piu' dire niente, e un'opzione che non fa niente e' peggio di
   un'opzione che non c'e' (chi la batte crede di aver tarato qualcosa).  ⇒ Sono
   stati TOLTI, e chi li batte riceve un messaggio e un'uscita **2**.  E il `-D`
   `AUDIO_SILENZIO_PREDEFINITO` e' sparito con loro: due strade per la stessa
   cura sono due numeri che divergono, ed e' la ragione per cui il ponte via
   ambiente e' gia' stato tolto una volta (23 agosto 2026).

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⛔ LE TRE COSE CHE QUESTO BANCO PROVA — e la trappola in cui e' gia' caduto
═══════════════════════════════════════════════════════════════════════════════

 **a. ACCESO DI SUO.**  Il server si lancia **senza nessuna opzione delle cure**
    e le cinque risultano attive.

    ⛔⛔ **E LO SI LEGGE DALLE RIGHE D'AVVIO DEL PRODOTTO, NON DALLA RIGA DI
        COMANDO.**  E' la trappola che ha gia' morso: verificare che «non ho
        passato `--sgombra-soglia-ms`» dimostra soltanto che **io** non l'ho
        passata — non dimostra niente su che cosa il prodotto abbia in vigore.
        Un predefinito scritto e non arrivato ha esattamente quella faccia, ed e'
        la forma E1 di `LEZIONI.md` («scritto non e' in vigore»).
        ⇒ La riga di comando si guarda lo stesso, ma per una domanda DIVERSA e
          piu' debole: e' la PREMESSA («ho davvero lanciato senza opzioni?»).
          Il verdetto viene dal registro.

 **b. OGNUNA SI SPEGNE ANCORA**, una per una: cinque riavvii, ognuno con una
    sola opzione, e la riga d'avvio del prodotto lo dichiara — quella spenta
    spenta, le altre quattro ancora accese.  ⚠ E' la meta' che rende onesta la
    (a): un predefinito che non si potesse piu' spegnere sarebbe una decisione
    presa AL POSTO dell'utente, non per lui.
    ⛔ Piu' i due nomi vecchi, che devono essere RIFIUTATI: e' quel che rende
       vera la frase «una strada sola».

 **c. E IL PRODOTTO FUNZIONA ACCESO.**  Un giro vero su linea pulita —
    fotogrammi/s, quota di chiavi, deriva — appaiato con lo stesso giro a cure
    SPENTE, e confrontato con `[M]` il denominatore di §17.6: **39,85
    fotogrammi/s, zero chiavi, deriva finale 0,1 ms**.
    ⛔⛔ Se acceso di suo la linea sana peggiora, **e' un rosso e va detto
        forte**: sarebbe la ferita di v1 ripetuta, cioe' aver consegnato un
        peggioramento chiamandolo miglioramento.

═══════════════════════════════════════════════════════════════════════════════
⚠ QUEL CHE QUESTO BANCO **NON** MISURA, dichiarato prima
═══════════════════════════════════════════════════════════════════════════════

 1. ⛔ **Non tocca nessuna rete.**  `enp7s0` mai; e nemmeno `lo`, che qui non e'
    mio: sulla macchina girano ADESSO altri banchi (7940, 7950, 7960, 7971,
    7973) e la 7900/7910/**7920** dell'utente, e un `netem` su `lo` e' del
    DISPOSITIVO — cioe' di tutti.  ⇒ Il giro (c) e' sulla linea **com'e'**, e il
    `qdisc` si legge e si dichiara accanto al numero.
 2. ⚠ **Il denominatore di §17.6 e' stato preso su `ritardo-30`** (netem, 30 ms
    di giro), il mio giro no.  ⇒ Il giudizio PRIMARIO e' l'appaiamento
    **misurato oggi** (cure spente contro predefiniti, stessa macchina, stessi
    minuti, stesso binario); il 39,85 e' un'ANCORA, e come tale si stampa.
 3. ⚠ **Il silenzio dell'audio non si rimisura qui**: l'ha misurato `09-b84`
    (102,1 volte meno traffico a schermo fermo).  Qui si prova soltanto che
    l'interruttore **e' arrivato dove serve** — cioe' che il padre dichiara di
    passarlo al figlio, che e' il posto dove vive il codificatore.
"""

import argparse, importlib.util, json, os, re, subprocess, sys, time

# ═══════════════════════════════════════════════════════════════════════════
# L'AMBIENTE — ⛔ il mio, e nessun altro
# ═══════════════════════════════════════════════════════════════════════════
MIO = {
    "PORTA": "7980",
    "UTENTE": "provanr11",
    "UID_B": "1080",
    "IND": "192.168.0.2",
    "MACCHINA": "nicfio@192.168.0.2",
    "PAROLA_SUDO": "nicfio",
    "ALBERO": "/media/REMOTIX/src/09nr11-src",
    "LAV": "/media/REMOTIX/tmp/09nr11",
    "DENTRO_ALB": "/srv/src/09nr11-src",
    "DENTRO_LAV": "/srv/remotix/tmp/09nr11",
    "UNITA": "remotix-7980",
    "FUORI": "/tmp/09-b86",
}
for _k, _v in MIO.items():
    os.environ.setdefault(_k, _v)

QUI = os.path.dirname(os.path.abspath(__file__))
PORTA = int(os.environ["PORTA"])
LAV = os.environ["LAV"]
ALB = os.environ["ALBERO"]
UNITA = os.environ["UNITA"]
FUORI = os.environ["FUORI"]

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
def _ok(t):  print("    %sOK%s  %s" % (VERDE, GRIGIO, t), flush=True)
def _ko(t):  print("    %sNO%s  %s" % (ROSSO, GRIGIO, t), flush=True)
def _dub(t): print("    %s??%s  %s" % (GIALLO, GRIGIO, t), flush=True)
def _inf(t): print("    --  %s" % t, flush=True)
def _log(t): print("\n\033[1m== %s\033[0m" % t, flush=True)


def _carica(nome, percorso):
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔ La macchineria del GIRO non si riscrive: `09-b70-ritmo.py` porta il lettore
#    della traccia §11.1, la riduzione ai cinque numeri, la scena e il cliente.
#    Due copie della stessa riduzione in due file sono due riduzioni che
#    divergono.
B70 = None


def importa():
    global B70
    B70 = _carica("b70ritmo", os.path.join(QUI, "09-b70-ritmo.py"))
    # ⛔⛔ E POI SI CONTROLLA CHE ABBIA PRESO IL MIO AMBIENTE, non il suo: un
    #     modulo che misurasse sulla porta di un altro banco darebbe numeri
    #     plausibili invece di un errore (`LEZIONI.md` §1.26).
    guai = []
    for nome, mio, suo in (("porta", PORTA, B70.PORTA), ("lavoro", LAV, B70.LAV),
                           ("albero", ALB, B70.ALB),
                           ("utente", os.environ["UTENTE"], B70.UTENTE),
                           ("uid", int(os.environ["UID_B"]), B70.UID_B)):
        if str(mio) != str(suo):
            guai.append("%s: il modulo ha «%s», il mio e' «%s»" % (nome, suo, mio))
    if guai:
        raise SystemExit("⛔ NON MISURO: l'import non ha preso il mio ambiente — "
                         + " · ".join(guai))
    B70.RETE = B70._importa_rete()
    if B70.RETE.PORTA != PORTA or B70.RETE.DEV != "lo" or B70.RETE.VIETATA != "enp7s0":
        raise SystemExit("⛔ NON MISURO: il modulo della rete ha porta %d, dev "
                         "«%s», vietata «%s»"
                         % (B70.RETE.PORTA, B70.RETE.DEV, B70.RETE.VIETATA))


def root(comando, tetto=300):
    """⛔ La catena CURATA di `09-b70`: **un** `sudo`, e la catena intera dentro
       la SUA `bash -c`.  ⚠ `RETE.root` copre il solo primo anello, e un `<`
       in coda ruba lo stdin a `sudo -S` — due difetti gia' pagati (⇒ il
       riquadro sopra `catena_root()` in `09-b70-ritmo.py`)."""
    return B70.root(comando, tetto)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ IL CONTRATTO: LE CINQUE CURE, E LE RIGHE D'AVVIO CHE LE DICHIARANO
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Ogni riquadro qui sotto e' UNA riga che il prodotto scrive all'avvio,
#    SEMPRE — accesa e spenta.  Sono il solo posto da cui questo banco legge lo
#    stato: la riga di comando dice quel che ho CHIESTO, il registro quel che il
#    prodotto ha IN VIGORE, e la fase 9 esiste perche' quei due fatti hanno la
#    stessa faccia quando divergono.
#
# ⚠ E la riga del silenzio dell'audio e' quella del PADRE («che cosa PASSERO' a
#   ogni figlio»), non quella del figlio: il codificatore audio vive dall'altra
#   parte dell'`execve`, e la sua riga «in vigore» arriva solo col primo
#   codificatore, cioe' con la prima sessione.  ⇒ La riga del padre e' l'unica
#   che esista **all'avvio**, ed e' la sola che questa prova possa leggere.
#   ⛔ La terna intera (padre PASSERA' · figlio RICEVUTO · audio.c IN VIGORE) si
#      rilegge nel giro (c), dove una sessione c'e'.
RE = {
    "soglia": re.compile(r"soglia della coda video \(§5\.1\): (\d+) ms — "
                         r"(ACCESA|SPENTA)"),
    "ritmo": re.compile(r"il regolatore del ritmo e' (ACCESO|SPENTO)"),
    "linea_morta": re.compile(r"la LINEA MORTA e' (ACCESA|SPENTA)"),
    "sfratto": re.compile(r"sfratto del fantasma: soglia (\d+) ms, (ACCESO|SPENTO)"),
    "audio": re.compile(r"il silenzio dell'audio che il padre PASSERA' a ogni "
                        r"figlio: (?:⛔ )?(ACCESO|SPENTO)"),
}

# (chiave · nome umano · l'opzione che la SPEGNE · il numero atteso di suo)
CURE = [
    ("soglia",      "soglia sulla coda video", "--sgombra-soglia-ms 0",   100),
    ("ritmo",       "regolatore del ritmo",    "--niente-ritmo-adattivo",  None),
    ("linea_morta", "linea morta",             "--niente-linea-morta",     None),
    ("sfratto",     "sfratto del fantasma",    "--sfratto-ms 0",         15000),
    ("audio",       "silenzio dell'audio",     "--niente-audio-silenzio",  None),
]
CHIAVI = [c[0] for c in CURE]
NOME = {c[0]: c[1] for c in CURE}
SPEGNE = {c[0]: c[2] for c in CURE}
NUMERO_ATTESO = {c[0]: c[3] for c in CURE}

# ⛔ TUTTE SPENTE, cioe' il prodotto fino al 23 agosto 2026 byte per byte.  E'
#    il braccio di paragone del giro (c), e si rimisura OGGI: riprenderlo da una
#    tabella vecchia sarebbe confrontare due binari e due ore diverse e chiamarlo
#    appaiamento (`LEZIONI.md` §1.26).
TUTTE_SPENTE = " ".join(SPEGNE[k] for k in CHIAVI)

# ⛔ I due nomi TOLTI.  Devono far uscire il server con **2**: un'opzione che
#    sopravvive a non fare niente e' la seconda strada, ed e' quel che questa
#    fase ha eliminato.
NOMI_TOLTI = ["--ritmo-adattivo", "--linea-morta"]


def stato_dalle_righe(testo):
    """⛔ Il VERDETTO, e viene da qui e da nessun altro posto: dal registro del
       prodotto.

    Torna `{chiave: {"stato": "acceso"|"spento"|None, "numero": int|None,
                     "riga": str|None}}`.
    ⚠ `None` vuol dire **«non l'ho letto»**, che non e' «spento»: la riga
      manca, e una riga che manca su una cura che chiude sessioni e' peggio di
      una cura spenta (`CODER.md` §3.10).
    """
    fuori = {}
    for chiave in CHIAVI:
        m = RE[chiave].search(testo)
        if not m:
            fuori[chiave] = {"stato": None, "numero": None, "riga": None}
            continue
        gruppi = m.groups()
        numero = int(gruppi[0]) if gruppi[0].isdigit() else None
        parola = gruppi[-1]
        # ⚠ ACCESA/ACCESO e SPENTA/SPENTO: il genere cambia con la cura, il
        #   fatto no.
        stato = "acceso" if parola.startswith("ACCES") else "spento"
        riga = None
        for x in testo.splitlines():
            if RE[chiave].search(x):
                riga = x.strip()
                break
        fuori[chiave] = {"stato": stato, "numero": numero, "riga": riga}
    return fuori


def righe_avvio(tetto=25.0):
    """Le righe d'avvio delle cinque cure, dal registro del server.

    ⛔ Si ASPETTA che ci siano invece di leggere quel che capita: il server e'
       appena partito, e leggere troppo presto darebbe «la riga non c'e'» —
       cioe' un rosso sul prodotto per una corsa del banco.
    """
    scade = time.time() + tetto
    testo = ""
    while time.time() < scade:
        rc, out, _e = root("grep -a 'soglia della coda video\\|regolatore del "
                           "ritmo\\|LINEA MORTA\\|sfratto del fantasma\\|silenzio "
                           "dell.audio che il padre' %s/registro.log" % LAV)
        testo = out
        if len(stato_dalle_righe(testo)) and all(
                stato_dalle_righe(testo)[k]["stato"] for k in CHIAVI):
            return testo
        time.sleep(0.5)
    return testo


def riga_di_comando():
    """⚠ LA PREMESSA, NON IL VERDETTO — e la distinzione e' tutto il punto (a).

    Dice con che cosa il server e' stato LANCIATO, cioe' se l'esperimento e'
    quello che credo di aver fatto.  ⛔ Non dice niente su che cosa il prodotto
    abbia in vigore: un predefinito scritto e non arrivato passerebbe questo
    controllo a pieni voti.
    """
    rc, out, _ = root("tr '\\0' ' ' < /proc/$(systemctl show -p MainPID --value "
                      "%s.service)/cmdline" % UNITA)
    return out.strip()


def ascolta():
    """⛔ Quanti ascoltatori UDP ci sono sulla MIA porta — e non su un'altra.

    ⚠ `None` = non l'ho letto, che non e' zero.
    """
    rc, out, _ = root("ss -uln 2>/dev/null | grep -c ':%d ' || true" % PORTA)
    t = out.strip()
    return int(t) if t.isdigit() else None


def coda_registro(quante=8):
    """Le ultime righe del registro del server.  ⭐ Il registro si azzera a ogni
       `accendi` (`07-b64-terreno.sh:106`), quindi quel che c'e' qui e' di
       QUESTO tentativo e non del precedente."""
    rc, out, _ = root("tail -n %d %s/registro.log 2>/dev/null || true"
                      % (quante, LAV))
    return out


def riavvia(opzioni):
    """Riaccende il server con `opzioni`, e torna `(partito, testo)`.

    ⛔⛔ E «PARTITO» SI CHIEDE ALLA PORTA, NON AL LANCIATORE — `[M]` 24 agosto
        2026, primo giro di questo banco, ed e' un falso rosso che il banco ha
        dato a codice giusto.  `systemd-run` pubblica un `MainPID` **prima**
        che il processo decida di vivere: un server che rifiuta un'opzione ed
        esce **2** ha gia' un pid quando il lanciatore lo cerca, e il lanciatore
        stampa «server 1234 sulla porta 7980» di un processo morto.
        ⇒ La domanda giusta non e' «c'e' un pid?» ma **«c'e' qualcuno che
          ascolta?»**, ed e' l'unica che distingua i due casi.
    ⚠ Si riprova per qualche decimo: fra l'`exec` e la `bind` passa un attimo, e
      leggere troppo presto darebbe «non e' partito» a un server che sta
      partendo — cioe' lo stesso difetto girato dall'altra parte.
    """
    amb = " ".join("%s=%s" % (k, os.environ[k]) for k in
                   ("PORTA", "IND", "UTENTE", "UID_B", "ALBERO", "LAV",
                    "DENTRO_ALB", "DENTRO_LAV", "UNITA", "MACCHINA",
                    "PAROLA_SUDO"))
    p = subprocess.run(
        "%s OPZIONI_SERVER=%s bash %s/09-b86-terreno.sh accendi"
        % (amb, json.dumps(opzioni), QUI),
        shell=True, capture_output=True, timeout=300)
    testo = (p.stdout + p.stderr).decode("utf-8", "replace")
    partito = False
    for _ in range(20):
        n = ascolta()
        if n:
            partito = True
            break
        time.sleep(0.5)
    return partito, testo + "\n--- coda del registro ---\n" + coda_registro()


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I PREDICATI — scritti PRIMA, e ognuno sa dare rosso
# ═══════════════════════════════════════════════════════════════════════════
def _si(p):   return (True, p)
def _no(p):   return (False, p)
def _muto(p): return (None, p)

# ⛔ IL DENOMINATORE DI §17.6 — `[M]` 23 agosto 2026, `09-b79-cure.py`, braccio A
#    su `ritardo-30` (la linea SANA della griglia).  ⚠ E' un'ANCORA, non
#    l'arbitro: quella linea aveva un `netem` da 30 ms di giro e la mia no.
ANCORA_FPS = 39.85
ANCORA_CHIAVI = 0
ANCORA_DERIVA_MS = 0.1

# ⚠ Il rumore fra due giri, stimato da `09-b70` e usato da `09-b79`: 5 %.  ⛔ Il
#   predicato del giro (c) non chiede «uguale», chiede «non peggiora piu' del
#   rumore» — chiedere l'uguaglianza a due giri veri e' chiedere un rosso.
RUMORE = 0.05
# ⭐ La deriva tollerata e' **la soglia stessa**: la cura TIENE un delta fino a
#    100 ms invece di buttarlo, quindi fino a 100 ms di deriva in piu' e' il
#    prezzo dichiarato e non un difetto.  Oltre, la coda e' scappata.
DERIVA_TOLLERATA_MS = 100.0
QUOTA_DELTA_MINIMA = 0.90   # §3.3, la stessa di `09-b70`


def p_tutte_accese(stato):
    """(a) — le cinque cure risultano ATTIVE, lette dalle righe d'avvio."""
    mute = [NOME[k] for k in CHIAVI if stato[k]["stato"] is None]
    if mute:
        return _muto("NON HO NIENTE DA GIUDICARE — la riga d'avvio non c'e' per: "
                     + ", ".join(mute) + ".  ⛔ Una riga che manca non e' «spento»")
    spente = [NOME[k] for k in CHIAVI if stato[k]["stato"] != "acceso"]
    if spente:
        return _no("⛔⛔ NON sono accese di suo: %s.  E' la consegna del 24 agosto "
                   "2026 che non e' arrivata nel prodotto" % ", ".join(spente))
    guai = []
    for k in CHIAVI:
        atteso = NUMERO_ATTESO[k]
        if atteso is not None and stato[k]["numero"] != atteso:
            guai.append("%s: il numero in vigore e' %s, il predefinito deciso e' %d"
                        % (NOME[k], stato[k]["numero"], atteso))
    if guai:
        return _no("⛔ accese si', ma coi numeri sbagliati — " + " · ".join(guai))
    return _si("tutt'e cinque ACCESE senza nessuna opzione, e coi numeri decisi "
               "(soglia %s ms · sfratto %s ms)"
               % (stato["soglia"]["numero"], stato["sfratto"]["numero"]))


def p_una_spenta(stato, chiave):
    """(b) — quella si spegne, e le altre quattro restano accese."""
    if stato[chiave]["stato"] is None:
        return _muto("NON HO NIENTE DA GIUDICARE — la riga d'avvio di «%s» non "
                     "c'e'" % NOME[chiave])
    if stato[chiave]["stato"] != "spento":
        return _no("⛔ `%s` NON l'ha spenta: la riga d'avvio dice ancora «%s»"
                   % (SPEGNE[chiave], stato[chiave]["stato"]))
    # ⛔ E le altre quattro devono essere rimaste ACCESE: un'opzione che ne
    #    spegne due e' un interruttore che mente sul suo nome.
    trascinate = [NOME[k] for k in CHIAVI
                  if k != chiave and stato[k]["stato"] != "acceso"]
    if trascinate:
        return _no("⛔⛔ `%s` ha spento anche: %s — un interruttore che ne spegne "
                   "due e' un interruttore che mente sul suo nome"
                   % (SPEGNE[chiave], ", ".join(trascinate)))
    if chiave == "soglia" and stato["soglia"]["numero"] != 0:
        return _no("⛔ la soglia dice «spenta» ma il numero e' %s, non 0"
                   % stato["soglia"]["numero"])
    if chiave == "sfratto" and stato["sfratto"]["numero"] != 0:
        return _no("⛔ lo sfratto dice «spento» ma il numero e' %s, non 0"
                   % stato["sfratto"]["numero"])
    return _si("`%s` la spegne, e la riga d'avvio lo DICHIARA; le altre quattro "
               "restano accese" % SPEGNE[chiave])


def p_nome_tolto(partito, testo):
    """(b-bis) — «una strada sola»: il nome vecchio non parte.

    ⚠ `partito` viene dalla PORTA, non dal lanciatore: ⇒ il riquadro sopra
      `riavvia()`, che e' il falso rosso che questo banco si e' gia' dato una
      volta.
    """
    if partito:
        return _no("⛔⛔ il server E' PARTITO con un nome che doveva essere tolto: "
                   "e' la SECONDA strada per la stessa cura, cioe' due numeri che "
                   "un giorno divergono")
    spiega = ("non esiste piu'" in testo)
    if not spiega:
        return _muto("il server non e' partito, ma non ho letto il messaggio che "
                     "spiega il cambio: potrebbe non essere partito per altro")
    return _si("rifiutato, e con un messaggio che spiega il cambio invece di un "
               "aiuto generico")


def _q(n, chiave, difetto=None):
    v = (n or {}).get(chiave)
    return difetto if v is None else v


def p_linea_sana(acceso, spento):
    """(c) — ⛔⛔ IL PREDICATO CHE PUO' AZZERARE LA CONSEGNA.

    Se coi predefiniti la linea SANA peggiora, la fase ha consegnato un
    peggioramento chiamandolo miglioramento: e' la ferita di v1 ripetuta, e va
    detto forte.

    ⭐ Tre gambe, e ognuna e' un numero che l'utente vedrebbe:
      1. i **fotogrammi/s** non calano piu' del rumore dichiarato (5 %);
      2. le **chiavi** non compaiono — §17.6 ne conta zero nei tre bracci, e una
         quota di chiavi che sale e' la spirale che questa fase e' venuta a
         spegnere;
      3. la **deriva finale** non cresce piu' della soglia stessa (100 ms), che
         e' il prezzo dichiarato della cura e non un difetto.
    """
    if (acceso or {}).get("esito") != "misurato":
        return _muto("NON HO NIENTE DA GIUDICARE — il giro coi predefiniti non "
                     "ha misurato: %s" % _q(acceso, "esito", "manca del tutto"))
    if (spento or {}).get("esito") != "misurato":
        return _muto("NON HO NIENTE DA GIUDICARE — il giro a cure spente non ha "
                     "misurato: %s" % _q(spento, "esito", "manca del tutto"))
    fa, fs = acceso["fps"], spento["fps"]
    ka, ks = acceso["chiavi"], spento["chiavi"]
    da, ds = abs(acceso["deriva_fine_ms"]), abs(spento["deriva_fine_ms"])
    guai = []
    if fa < fs * (1.0 - RUMORE):
        guai.append("i fotogrammi/s CALANO: %.2f coi predefiniti contro %.2f a "
                    "cure spente, cioe' il %.1f %% in meno — piu' del rumore "
                    "dichiarato del %.0f %%"
                    % (fa, fs, 100.0 * (fs - fa) / fs, 100 * RUMORE))
    if ka > ks:
        guai.append("compaiono CHIAVI che a cure spente non c'erano: %d contro %d"
                    % (ka, ks))
    if acceso["quota_delta"] < QUOTA_DELTA_MINIMA:
        guai.append("la quota di delta e' %.4f, sotto il %.2f di §3.3"
                    % (acceso["quota_delta"], QUOTA_DELTA_MINIMA))
    if da > ds + DERIVA_TOLLERATA_MS:
        guai.append("la deriva finale cresce di %.0f ms, piu' della soglia stessa "
                    "(%.0f ms): la coda e' scappata"
                    % (da - ds, DERIVA_TOLLERATA_MS))
    if guai:
        return _no("⛔⛔ SULLA LINEA SANA I PREDEFINITI PEGGIORANO IL PRODOTTO — "
                   + " · ".join(guai))
    return _si("la linea sana non paga niente: %.2f fotogrammi/s coi predefiniti "
               "contro %.2f a cure spente (ancora §17.6: %.2f) · chiavi %d contro "
               "%d (ancora: %d) · deriva finale %.1f ms contro %.1f (ancora: %.1f)"
               % (fa, fs, ANCORA_FPS, ka, ks, ANCORA_CHIAVI, acceso["deriva_fine_ms"],
                  spento["deriva_fine_ms"], ANCORA_DERIVA_MS))


def p_ancora_17_6(acceso):
    """(c-bis) — ⚠ IL CONFRONTO CON `[M]` §17.6, e si giudica MORBIDO apposta.

    ⛔ Quel 39,85 e' stato preso su `ritardo-30`, con un `netem` da 30 ms di
       giro; questo giro e' sulla linea nuda.  ⇒ Chiedere l'uguaglianza sarebbe
       chiedere un rosso a due esperimenti diversi.  Si chiede che il giro di
       oggi **non sia sotto** l'ancora piu' del rumore, e si stampa la differenza
       perche' la legga chi rilegge.
    """
    if (acceso or {}).get("esito") != "misurato":
        return _muto("NON HO NIENTE DA GIUDICARE — il giro non ha misurato")
    fa = acceso["fps"]
    if fa < ANCORA_FPS * (1.0 - RUMORE):
        return _no("⛔ %.2f fotogrammi/s coi predefiniti, contro i %.2f di §17.6: "
                   "il %.1f %% in meno, piu' del rumore del %.0f %%"
                   % (fa, ANCORA_FPS, 100.0 * (ANCORA_FPS - fa) / ANCORA_FPS,
                      100 * RUMORE))
    return _si("%.2f fotogrammi/s contro i %.2f di §17.6 (%+.1f %%), chiavi %d "
               "contro %d, deriva finale %.1f ms contro %.1f"
               % (fa, ANCORA_FPS, 100.0 * (fa - ANCORA_FPS) / ANCORA_FPS,
                  acceso["chiavi"], ANCORA_CHIAVI, acceso["deriva_fine_ms"],
                  ANCORA_DERIVA_MS))


def p_nessuno_buttato_fuori(scatti):
    """(c-ter) — ⛔ LA CURA CHE CHIUDE UNA SESSIONE NON DEVE AVER CHIUSO NIENTE.

    Su una linea sana la linea morta e lo sfratto sono PARAPETTI, e il loro
    comportamento corretto e' non fare niente.  ⚠ Uno scatto qui non sarebbe una
    misura interessante: sarebbe la dimostrazione che i predefiniti buttano
    fuori chi lavora.
    """
    if scatti is None:
        return _muto("NON HO NIENTE DA GIUDICARE — il registro non si e' letto")
    if scatti.get("linea_morta") or scatti.get("sfratti"):
        return _no("⛔⛔ SU LINEA SANA HANNO SCATTATO: %d righe `linea-morta` e %d "
                   "sfratti.  E' la cura che butta fuori chi lavora"
                   % (scatti.get("linea_morta", 0), scatti.get("sfratti", 0)))
    return _si("zero scatti della linea morta e zero sfratti: i due parapetti non "
               "hanno toccato una sessione sana")


def p_terna_audio(terna):
    """(c-quater) — ⭐ LA TERNA DEL SILENZIO DELL'AUDIO, e serve a separare due
       fatti che hanno la stessa faccia.

    `figlio.c` scrive «che cosa PASSERO'», il figlio scrive «che cosa mi e'
    ARRIVATO», `audio.c` scrive «che cosa e' IN VIGORE».  ⛔ Un'opzione caduta
    nel passaggio padre → figlio somiglia in tutto a una cura che non funziona:
    se le tre non concordano, il punto in cui si perde sta fra le due che
    divergono, e non c'e' da indovinare (forma D5).
    """
    mancano = [k for k, v in terna.items() if v is None]
    if mancano:
        return _muto("NON HO NIENTE DA GIUDICARE — mancano le righe: %s.  ⚠ La "
                     "riga «in vigore» esce solo se la sessione ha aperto un "
                     "codificatore audio" % ", ".join(mancano))
    if not all(terna.values()):
        return _no("⛔ la terna NON concorda — padre %s · figlio %s · in vigore "
                   "%s: l'opzione si e' persa fra le due che divergono"
                   % (terna["padre"], terna["figlio"], terna["in_vigore"]))
    return _si("la terna concorda: il padre lo PASSA, il figlio l'ha RICEVUTO, e "
               "`audio.c` lo dichiara IN VIGORE")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL CONTROLLO POSITIVO — `--certifica`: il banco sa dare ROSSO?
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Non tocca la macchina di prova.  Fabbrica le righe d'avvio e i giri, e
#    controlla che ogni predicato dica quel che deve — verde dove c'e' da dirlo,
#    ROSSO dove il difetto c'e', e MUTO dove non ha letto.  ⚠ Un banco che sa
#    solo dire «tutto bene» non ha mai dimostrato di saper vedere.
R_ACCESE = (
    "avvio ⭐ fase 9 — sfratto del fantasma: soglia 15000 ms, ACCESO.  ecc\n"
    "avvio ⭐ FASE 9, soglia della coda video (§5.1): 100 ms — ACCESA: ecc\n"
    "avvio ⭐ FASE 9: il regolatore del ritmo e' ACCESO — ecc\n"
    "avvio ⛔⭐ FASE 9: la LINEA MORTA e' ACCESA — ecc\n"
    "figlio ⭐ FASE 9, il silenzio dell'audio che il padre PASSERA' a ogni "
    "figlio: ACCESO, ed e' il PREDEFINITO ecc\n"
)


def _righe(soglia=100, ritmo="ACCESO", lm="ACCESA", sfratto=15000, audio="ACCESO",
           salta=()):
    r = []
    if "sfratto" not in salta:
        r.append("avvio ⭐ fase 9 — sfratto del fantasma: soglia %d ms, %s."
                 % (sfratto, sfratto and "ACCESO" or "SPENTO"))
    if "soglia" not in salta:
        r.append("avvio ⭐ FASE 9, soglia della coda video (§5.1): %d ms — %s:"
                 % (soglia, "ACCESA" if soglia else "SPENTA"))
    if "ritmo" not in salta:
        r.append("avvio FASE 9: il regolatore del ritmo e' %s —" % ritmo)
    if "linea_morta" not in salta:
        r.append("avvio FASE 9: la LINEA MORTA e' %s —" % lm)
    if "audio" not in salta:
        marca = "" if audio == "ACCESO" else "⛔ "
        r.append("figlio ⭐ FASE 9, il silenzio dell'audio che il padre PASSERA' "
                 "a ogni figlio: %s%s," % (marca, audio))
    return "\n".join(r) + "\n"


def _g(fps, chiavi=0, deriva=0.1, quota=1.0):
    return {"esito": "misurato", "fps": fps, "chiavi": chiavi,
            "deriva_fine_ms": deriva, "quota_delta": quota}


def certifica():
    _log("⭐ CONTROLLO POSITIVO — il banco sa vedere i difetti che cerca?")
    casi = []

    def caso(nome, atteso, esito):
        passa, perche = esito
        casi.append((nome, atteso, passa, perche))

    # ── (a) acceso di suo ──────────────────────────────────────────────────
    caso("a · tutte accese coi numeri giusti", True,
         p_tutte_accese(stato_dalle_righe(_righe())))
    caso("a · una nasce SPENTA (la consegna non e' arrivata)", False,
         p_tutte_accese(stato_dalle_righe(_righe(ritmo="SPENTO"))))
    caso("a · tutte accese ma la soglia e' 50, non 100", False,
         p_tutte_accese(stato_dalle_righe(_righe(soglia=50))))
    caso("a · lo sfratto e' acceso a 3000, non a 15000", False,
         p_tutte_accese(stato_dalle_righe(_righe(sfratto=3000))))
    caso("a · manca la riga della linea morta ⇒ MUTO, non rosso", None,
         p_tutte_accese(stato_dalle_righe(_righe(salta=("linea_morta",)))))
    caso("a · manca la riga dell'audio ⇒ MUTO", None,
         p_tutte_accese(stato_dalle_righe(_righe(salta=("audio",)))))

    # ── (b) ognuna si spegne ──────────────────────────────────────────────
    caso("b · il regolatore si spegne, gli altri restano", True,
         p_una_spenta(stato_dalle_righe(_righe(ritmo="SPENTO")), "ritmo"))
    caso("b · l'opzione NON l'ha spento", False,
         p_una_spenta(stato_dalle_righe(_righe()), "ritmo"))
    caso("b · l'opzione ne spegne DUE (mente sul suo nome)", False,
         p_una_spenta(stato_dalle_righe(_righe(ritmo="SPENTO", lm="SPENTA")),
                      "ritmo"))
    caso("b · la soglia dice «spenta» ma il numero non e' 0", False,
         p_una_spenta(stato_dalle_righe(
             _righe().replace("100 ms — ACCESA", "100 ms — SPENTA")), "soglia"))
    caso("b · lo sfratto si spegne davvero (0 ms)", True,
         p_una_spenta(stato_dalle_righe(_righe(sfratto=0)), "sfratto"))
    caso("b · la riga non c'e' ⇒ MUTO", None,
         p_una_spenta(stato_dalle_righe(_righe(salta=("sfratto",))), "sfratto"))

    # ── (b-bis) i nomi tolti ──────────────────────────────────────────────
    caso("b-bis · il nome tolto e' rifiutato, e spiegato", True,
         p_nome_tolto(False, "⛔ --ritmo-adattivo non esiste piu': ..."))
    caso("b-bis · il nome tolto FA PARTIRE il server (seconda strada)", False,
         p_nome_tolto(True, "server 123 sulla porta 7980"))
    caso("b-bis · non parte ma senza spiegare ⇒ MUTO", None,
         p_nome_tolto(False, "systemd-run ha rifiutato"))

    # ── (c) la linea sana ─────────────────────────────────────────────────
    caso("c · la linea sana non paga niente", True,
         p_linea_sana(_g(39.9), _g(39.85)))
    caso("c · i fotogrammi/s CALANO del 20 %", False,
         p_linea_sana(_g(32.0), _g(40.0)))
    caso("c · compaiono chiavi che prima non c'erano", False,
         p_linea_sana(_g(39.9, chiavi=12, quota=0.7), _g(39.85)))
    caso("c · la deriva scappa di 400 ms", False,
         p_linea_sana(_g(39.9, deriva=402.0), _g(39.85, deriva=0.5)))
    caso("c · un calo dentro il rumore del 5 % NON e' un rosso", True,
         p_linea_sana(_g(38.5), _g(39.85)))
    caso("c · il giro non ha misurato ⇒ MUTO", None,
         p_linea_sana({"esito": "NON HO NIENTE DA GIUDICARE"}, _g(39.85)))
    caso("c-bis · l'ancora di §17.6 regge", True, p_ancora_17_6(_g(39.9)))
    caso("c-bis · sotto l'ancora piu' del rumore", False, p_ancora_17_6(_g(30.0)))
    caso("c-ter · zero scatti sui parapetti", True,
         p_nessuno_buttato_fuori({"linea_morta": 0, "sfratti": 0}))
    caso("c-ter · la linea morta ha buttato fuori una sessione sana", False,
         p_nessuno_buttato_fuori({"linea_morta": 1, "sfratti": 0}))
    caso("c-ter · il registro non si e' letto ⇒ MUTO", None,
         p_nessuno_buttato_fuori(None))
    caso("c-quater · la terna dell'audio concorda", True,
         p_terna_audio({"padre": True, "figlio": True, "in_vigore": True}))
    caso("c-quater · l'opzione si perde fra padre e figlio", False,
         p_terna_audio({"padre": True, "figlio": False, "in_vigore": False}))
    caso("c-quater · la riga «in vigore» non c'e' ⇒ MUTO", None,
         p_terna_audio({"padre": True, "figlio": True, "in_vigore": None}))

    rossi = 0
    for nome, atteso, passa, perche in casi:
        if passa == atteso:
            _ok("%-58s → %s" % (nome, passa))
        else:
            rossi += 1
            _ko("%-58s → %s, ATTESO %s  (%s)" % (nome, passa, atteso, perche[:90]))
    print()
    if rossi:
        _ko("⛔ %d casi su %d NON si comportano come scritto: il banco non e' "
            "pronto a misurare" % (rossi, len(casi)))
        return 2
    _ok("⭐ %d casi su %d: il banco sa dare verde, ROSSO e muto dove deve"
        % (len(casi), len(casi)))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# LA MISURA VERA
# ═══════════════════════════════════════════════════════════════════════════
def stampa_stato(stato):
    for k in CHIAVI:
        v = stato[k]
        s = v["stato"] or "⛔ NON LETTO"
        n = "" if v["numero"] is None else " (%d)" % v["numero"]
        _inf("%-26s %s%s" % (NOME[k], s, n))


def conta_scatti(riga0):
    """Le righe `linea-morta` e gli sfratti scritti DA `riga0` in poi.

    ⛔ `None` = non ho letto, che non e' zero (`LEZIONI.md` §1.9).
    """
    if not riga0:
        return None
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -ac 'linea-morta' "
                      "|| true" % (riga0, LAV))
    a = out.strip()
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -ac 'SFRATTATO\\|"
                      "sfratto per silenzio' || true" % (riga0, LAV))
    b = out.strip()
    if not a.isdigit() or not b.isdigit():
        return None
    return {"linea_morta": int(a), "sfratti": int(b)}


def terna_audio():
    """Le tre righe del silenzio dell'audio, dopo che una sessione c'e' stata.

    ⛔⛔ E SI LEGGE IL REGISTRO INTERO, non da `riga0` in poi — `[M]` 24 agosto
        2026, e il banco si e' gia' dato un MUTO per questo.  Due delle tre
        righe sono **prima** del giro: quella del padre esce all'avvio del
        server, quella del figlio quando il figlio nasce, cioe' con la sessione
        d'innesco.  ⇒ Una finestra che comincia col giro le taglia fuori tutt'e
        due, e «non le ho lette» finisce per somigliare a «non ci sono».
    ⚠ E leggere tutto e' lecito **solo** perche' `07-b64-terreno.sh:106` fa
      `: > registro.log` a ogni `accendi`, e questo banco riaccende il server a
      ogni braccio: quel che c'e' nel file e' di QUESTO braccio e di nessun
      altro.  ⛔ Chi cambiasse quella riga romperebbe questa funzione in
      silenzio.
    """
    fuori = {"padre": None, "figlio": None, "in_vigore": None}
    rc, out, _ = root("grep -a \"silenzio "
                      "dell'audio che il padre\\|silenzio dell'audio ACCESO\\|"
                      "silenzio dell'audio SPENTO\\|cura del silenzio digitale\" "
                      "%s/registro.log || true" % LAV)
    testo = out
    m = RE["audio"].search(testo)
    if m:
        fuori["padre"] = (m.group(1) == "ACCESO")
    m = re.search(r"silenzio dell'audio (ACCESO|SPENTO)", testo)
    if m:
        fuori["figlio"] = (m.group(1) == "ACCESO")
    m = re.search(r"cura del silenzio digitale: (⭐ ACCESA|⛔ SPENTA)", testo)
    if m:
        fuori["in_vigore"] = m.group(1).endswith("ACCESA")
    return fuori


# ⛔⛔ LA SCENA SI ACCENDE QUI, E NON CON `B70.scena_accendi()` — due ragioni,
#     e tutt'e due sono ISOLAMENTO, non gusto:
#
#   1. ⛔ `09-b70` usa la memoria condivisa **`/09-b70`**, sempre, per qualunque
#      banco la importi.  Sulla macchina girano ADESSO altri banchi che
#      importano lo stesso file: due scene con lo stesso nome di `shm` sono due
#      banchi che si scrivono addosso, e il numero che ne esce e' plausibile.
#      ⇒ Qui la `shm` e' **`/09-b86`**, come la porta e l'utente.
#   2. ⚠ `09-b70` aspetta **1,5 s fissi** e poi guarda una volta sola.  `[M]`
#      24 agosto 2026, primo giro di questo banco: la scena era partita e il
#      `pgrep` non l'ha vista — «la scena non parte» su una scena che parte.
#      ⇒ Qui si riprova per otto secondi, e se non parte davvero **si dice
#        perche'**: l'uscita della scena finisce in un file invece che in
#        `/dev/null`, o «non e' partita» resta senza causa.
#
# ⛔ E il monitor si aspetta: nasce col PRIMO cliente, e la riga «monitor «»»
#    (vuota) e' quella del palco che non ha ancora la tela.  Leggerla come nome
#    darebbe una scena lanciata su un'uscita che non esiste.
def scena_accendi(movimento="barra", tetto=10.0):
    B70.scena_spegni()
    root("pkill -u %s -f 04-b30-scena; true" % os.environ["UID_B"])
    usc, scade = None, time.time() + tetto
    while time.time() < scade:
        rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1"
                          % LAV)
        m = re.findall("monitor «([^»]*)»", out)
        if m and m[-1]:
            usc = m[-1]
            break
        time.sleep(0.5)
    if not usc:
        _ko("⛔ il registro non porta ancora il nome di un monitor: il palco non "
            "ha la tela, e non saprei dove disegnare")
        return None
    root("setsid nohup setpriv --reuid=%s --regid=%s --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%s WAYLAND_DISPLAY=wayland-0 "
         "%s --uscita %s --movimento %s --shm /09-b86 --giro b86 "
         "> %s/scena.log 2>&1 & echo acceso"
         % (os.environ["UID_B"], os.environ["UID_B"], os.environ["UTENTE"],
            os.environ["UTENTE"], os.environ["UID_B"], B70.SCENA_BIN, usc,
            movimento, LAV))
    scade = time.time() + 8.0
    while time.time() < scade:
        rc, out, _ = root("pgrep -u %s -f '04-b30-scena --uscita' | head -1"
                          % os.environ["UID_B"])
        if out.strip():
            return usc
        time.sleep(0.5)
    rc, out, _ = root("tail -5 %s/scena.log 2>/dev/null || true" % LAV)
    _ko("⛔ la scena NON e' partita in 8 s.  La sua uscita: %s"
        % (out.strip()[:300] or "(vuota)"))
    return None


def un_giro(etichetta, secondi):
    """Un giro vero: scena mossa, tela piena, e i cinque numeri di `09-b70`."""
    usc = scena_accendi("barra")
    if not usc:
        return {"esito": "NON HO NIENTE DA GIUDICARE — la scena non e' partita"}, None
    _inf("scena «barra» sul monitor %s" % usc)
    riga0 = B70.righe_registro()
    n = B70.giro("b86-%s" % etichetta, "barra", B70.TELA_PIENA, secondi)
    B70.scena_spegni()
    return n, riga0


def stampa_giro_corto(nome, n):
    if (n or {}).get("esito") != "misurato":
        _dub("%s: %s" % (nome, _q(n, "esito", "niente")))
        return
    _inf("%s: %.2f fotogrammi/s (minimo su finestra %.2f) · %d fotogrammi · "
         "chiavi %d (quota delta %.4f) · deriva finale %.1f ms (max %.1f) · "
         "%.3f Mbit/s di carico · buchi %d"
         % (nome, n["fps"], n.get("fps_finestra_min") or -1, n["fotogrammi"],
            n["chiavi"], n["quota_delta"], n["deriva_fine_ms"],
            n["deriva_max_ms"], n["mbit_s_carico"], n["buchi_numero"]))


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: prova che il banco sa vedere "
                        "i difetti che cerca.  Non tocca la macchina di prova")
    p.add_argument("--secondi", type=int, default=25,
                   help="la durata del giro (c); 25 come §17.6")
    p.add_argument("--salta-giro", action="store_true",
                   help="⚠ solo (a) e (b): il giro (c) costa due riavvii e due "
                        "minuti")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    os.makedirs(FUORI, exist_ok=True)
    importa()

    _log("09-b86 · I CINQUE PREDEFINITI RIBALTATI — porta %d · unita' %s"
         % (PORTA, UNITA))
    print("   ⛔ «enp7s0» non si tocca, e nemmeno «lo»: questo banco non "
          "installa nessun netem")
    print("   ⛔ 7900 · 7910 · 7920 non sono mie (la 7920 e' la sessione VIVA "
          "dell'utente)")
    _inf("qdisc di «lo» adesso: %s" % (B70.RETE.qdisc() or "(nessuna)").strip())
    rc, out, _ = root("md5sum %s/src/remotix" % ALB)
    md5 = out.strip().split()[0] if out.strip() else "?"
    _inf("⭐ md5 del binario che misuro: %s" % md5)

    esiti, rossi, muti = [], [], []

    def segna(marca, esito):
        passa, perche = esito
        (_ok if passa else (_dub if passa is None else _ko))("%s: %s"
                                                             % (marca, perche))
        esiti.append({"prova": marca, "passa": passa, "perche": perche})
        if passa is False:
            rossi.append(marca)
        elif passa is None:
            muti.append(marca)

    # ═══ (a) ACCESO DI SUO ═════════════════════════════════════════════════
    _log("(a) ⭐ ACCESO DI SUO — server lanciato SENZA nessuna opzione")
    partito, testo = riavvia("")
    if not partito:
        _ko("⛔ il server non e' partito: %s" % testo[-400:])
        return 2
    cmdline = riga_di_comando()
    _inf("premessa · la riga di comando del server: %s" % cmdline)
    sporche = [o for o in ("--sgombra-soglia-ms", "--sfratto-ms", "--niente-",
                           "--ritmo-adattivo", "--linea-morta")
               if o in cmdline]
    if sporche:
        _ko("⛔ LA PREMESSA NON REGGE: la riga di comando porta %s — non sto "
            "misurando i predefiniti" % sporche)
        return 2
    _ok("premessa: nessuna opzione delle cure sulla riga di comando")
    testo_righe = righe_avvio()
    stato = stato_dalle_righe(testo_righe)
    stampa_stato(stato)
    print()
    for k in CHIAVI:
        if stato[k]["riga"]:
            print("      %s" % stato[k]["riga"][:240])
    print()
    segna("a · le cinque accese di suo", p_tutte_accese(stato))

    # ═══ (b) OGNUNA SI SPEGNE ANCORA ═══════════════════════════════════════
    _log("(b) ⛔ OGNUNA SI SPEGNE ANCORA — una per una, cinque riavvii")
    for chiave in CHIAVI:
        opz = SPEGNE[chiave]
        _inf("── %s · «%s»" % (NOME[chiave], opz))
        partito, testo = riavvia(opz)
        if not partito:
            segna("b · %s" % NOME[chiave],
                  _no("⛔ il server NON e' partito con «%s»: %s"
                      % (opz, testo[-200:])))
            continue
        st = stato_dalle_righe(righe_avvio())
        segna("b · %s" % NOME[chiave], p_una_spenta(st, chiave))
        if st[chiave]["riga"]:
            print("      %s" % st[chiave]["riga"][:240])

    _log("(b-bis) ⛔ UNA STRADA SOLA — i due nomi vecchi devono essere RIFIUTATI")
    for nome in NOMI_TOLTI:
        partito, testo = riavvia(nome)
        segna("b-bis · %s" % nome, p_nome_tolto(partito, testo))
        if not partito:
            for x in testo.splitlines():
                if "non esiste piu'" in x:
                    print("      %s" % x.strip()[:200])

    if a.salta_giro:
        _dub("⚠ --salta-giro: il giro (c) NON e' stato fatto, e senza di lui "
             "questo banco non dice niente sul prodotto acceso")
    else:
        # ═══ (c) IL PRODOTTO FUNZIONA ACCESO ═══════════════════════════════
        _log("(c) ⭐ IL PRODOTTO FUNZIONA ACCESO — due giri appaiati su linea "
             "pulita")
        print("   ⛔ appaiato vuol dire UNA COSA SOLA CAMBIATA: stesso binario, "
              "stessa scena, stessa tela, stessi minuti — a cambiare ci sono i "
              "soli interruttori")
        giri = {}
        for etichetta, opz in (("spente", TUTTE_SPENTE), ("predefiniti", "")):
            _inf("── braccio «%s» · opzioni: %s"
                 % (etichetta, opz if opz else "(nessuna, i predefiniti)"))
            partito, testo = riavvia(opz)
            if not partito:
                _ko("⛔ il server non e' partito: %s" % testo[-200:])
                giri[etichetta] = ({"esito": "NON HO NIENTE DA GIUDICARE — il "
                                             "server non e' partito"}, None)
                continue
            st = stato_dalle_righe(righe_avvio())
            stampa_stato(st)
            atteso = "spento" if etichetta == "spente" else "acceso"
            sbagliate = [NOME[k] for k in CHIAVI if st[k]["stato"] != atteso]
            if sbagliate:
                _ko("⛔ il braccio non e' quello che credo — non «%s»: %s"
                    % (atteso, ", ".join(sbagliate)))
                giri[etichetta] = ({"esito": "NON HO NIENTE DA GIUDICARE — il "
                                             "braccio non e' quello che credo"},
                                   None)
                continue
            if not B70.terreno_controlla():
                _ko("il terreno non e' pronto: NON misuro")
                giri[etichetta] = ({"esito": "NON HO NIENTE DA GIUDICARE — "
                                             "terreno"}, None)
                continue
            if not B70.innesca_sessione():
                _ko("la sessione d'innesco non si apre: il palco non nasce")
                giri[etichetta] = ({"esito": "NON HO NIENTE DA GIUDICARE — "
                                             "innesco"}, None)
                continue
            giri[etichetta] = un_giro(etichetta, a.secondi)
            stampa_giro_corto(etichetta, giri[etichetta][0])

        acceso, riga0_acceso = giri.get("predefiniti", (None, None))
        spento, _r = giri.get("spente", (None, None))
        segna("c · la linea sana coi predefiniti", p_linea_sana(acceso, spento))
        segna("c-bis · l'ancora di §17.6", p_ancora_17_6(acceso))
        segna("c-ter · i due parapetti", p_nessuno_buttato_fuori(
            conta_scatti(riga0_acceso)))
        segna("c-quater · la terna del silenzio dell'audio",
              p_terna_audio(terna_audio()))
        if acceso and acceso.get("esito") == "misurato":
            print()
            _inf("| braccio | fotogrammi/s | chiavi | quota delta | deriva "
                 "finale ms | Mbit/s carico |")
            for et in ("spente", "predefiniti"):
                n = giri.get(et, ({}, None))[0]
                if n.get("esito") == "misurato":
                    _inf("| %-12s | %12.2f | %6d | %11.4f | %16.1f | %13.3f |"
                         % (et, n["fps"], n["chiavi"], n["quota_delta"],
                            n["deriva_fine_ms"], n["mbit_s_carico"]))
            _inf("| %-12s | %12.2f | %6d | %11s | %16.1f | %13s |  ⚠ `[M]` §17.6"
                 % ("ancora", ANCORA_FPS, ANCORA_CHIAVI, "—", ANCORA_DERIVA_MS,
                    "—"))

    # ═══ IL VERBALE ════════════════════════════════════════════════════════
    _log("IL VERBALE")
    fuori = os.path.join(FUORI, "09-b86-esiti.json")
    with open(fuori, "w", encoding="utf-8") as f:
        json.dump({"md5": md5, "porta": PORTA, "esiti": esiti,
                   "quando": time.strftime("%Y-%m-%d %H:%M:%S")}, f,
                  ensure_ascii=False, indent=1)
    _inf("gli esiti in %s" % fuori)
    if rossi:
        _ko("⛔ ROSSO — %d prove: %s" % (len(rossi), " · ".join(rossi)))
    if muti:
        _dub("⚠ %d prove non hanno giudicato: %s" % (len(muti), " · ".join(muti)))
    if not rossi and not muti:
        _ok("⭐ tutte le prove verdi: i cinque predefiniti sono accesi, ognuno si "
            "spegne ancora, e sulla linea sana il prodotto non peggiora")
    return 2 if rossi else 0


if __name__ == "__main__":
    sys.exit(principale())
