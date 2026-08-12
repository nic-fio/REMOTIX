#!/usr/bin/env python3
"""02-figlio-prova.py — il banco di `DECISIONI.md` §1.10-bis: **un figlio per utente**.

    python3 02-figlio-prova.py --previsione
    python3 02-figlio-prova.py --caso nasce --porta 7571 \\
        --pid-server 12345 --registro /srv/remotix/tmp/02-figlio/registro.log \\
        --utente nicfio --parola-file /srv/src/tmp/02-figlio-parola

⛔ GIRA DENTRO IL CONTENITORE E DA ROOT.  Dentro perche' `aioquic` sta li'; da
   root perche' meta' delle letture sono su `/proc` di un processo di root — e
   ⛔ **«non ho potuto leggere» non e' «non c'era»** (`LEZIONI.md` §1.9), quindi
   un banco che non puo' leggere esce **2** invece di stampare un verde.

⚠ `/proc` dentro il contenitore E' quello dell'host (`enter.sh` lo monta), quindi
  i processi che si guardano sono quelli veri del server.

---------------------------------------------------------------------------
⛔ CHE COSA PROVA, E PERCHE' NON BASTA GUARDARE IL REGISTRO

Il prodotto scrive nel registro *«sono il figlio di «nicfio»: uid 1000»*.  ⛔ Un
banco che si accontentasse di quella riga **non proverebbe niente**: e' il
processo che si dichiara, ed e' esattamente la cosa che §1.10-bis dice di non
credere — *«un figlio che gira come l'utente sbagliato e' I3 violata in modo
invisibile»*.

⇒ Qui l'identita' si CHIEDE AL NUCLEO, in due modi indipendenti:

  · `/proc/<pid>/status`, campo `Uid:`, che porta **quattro** numeri — reale,
    effettivo, salvato, filesystem.  ⛔ Si guardano tutti e quattro: un
    processo con `Uid: 1000 1000 0 1000` e' un processo che **puo' tornare
    root**, e sarebbe verde per chi ne legge uno solo;
  · le credenziali che il nucleo timbra su ogni messaggio (`SO_PASSCRED`), che
    il PADRE confronta a ogni messaggio — e che questo banco mette alla prova
    col guasto `cieco`, dove sono l'unico muro rimasto.

---------------------------------------------------------------------------
⛔ LE SEI PROVE, E IL CASO OPPOSTO DI CIASCUNA

  | caso          | che cosa deve succedere            | il caso opposto        |
  |---------------|------------------------------------|------------------------|
  | `nasce`       | un figlio, uid dell'utente, col bus| nessun figlio, o il bus|
  |               | e SENZA la porta del server        | del padre              |
  | `due`         | due connessioni, UN figlio (I2)    | due figli              |
  | `distacco`    | il cliente se ne va, il figlio VIVE| il figlio muore col    |
  |               | con lo STESSO pid (I4)             | distacco               |
  | `muore`       | ucciso il figlio, il padre lo       | uno zombie che ha la   |
  |               | RACCOGLIE e lo dice                 | stessa faccia di un    |
  |               |                                     | processo vivo          |
  | `senza-palco` | utente senza `/run/user/<uid>`:    | il figlio prende il    |
  |               | il figlio nasce, LO DICE, e non ha  | palco di qualcun altro |
  |               | palco                               |                        |
  | `guasto-uid`  | il figlio non scende: se ne accorge | gira come root e       |
  |               | DA SE' e muore (uscita 42)          | consegna pixel         |
  | `guasto-cieco`| il figlio non scende e non se ne    | il padre si fida e     |
  |               | accorge: lo abbatte IL PADRE, sulle | consegna i pixel di    |
  |               | credenziali del nucleo              | root a chi e' entrato  |

---------------------------------------------------------------------------
⛔ LE REGOLE DI B0 CHE QUESTO BANCO DEVE

  B0.1 lo stato iniziale si dichiara **e si verifica**: il pid del server, chi
       lo possiede, quanti figli ci sono gia', e il registro da che offset;
  B0.3 questo banco autentica, quindi **banna**: il file dei ban e' suo, e i
       tentativi falliti si contano.  ⚠ Qui non se ne fanno di proposito;
  B0.4 l'atteso lo confronta il banco: **0** tutto come atteso · **1** almeno
       una prova ha dato altro · **2** non si e' potuto misurare;
  B0.7 marcatori, non `sleep`: il registro si legge da un **offset** preso
       prima di ogni prova, cosi' quel che si conta e' di questo giro.
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ L'atteso si scrive PRIMA del giro, e si stampa con `--previsione`: un atteso
#    scritto dopo aver visto il numero non e' un atteso.
PREVISIONE = """
⛔ L'ATTESO, scritto prima del giro — `DECISIONI.md` §1.10-bis

 1. `nasce`  ⭐ dopo che «nicfio» e' AMMESSO esiste **un** processo figlio del
    server, e:
      · `/proc/<pid>/status` dice `Uid: 1000 1000 1000 1000` — tutti e quattro,
        perche' un saved-uid a 0 e' un processo che puo' tornare root;
      · la sua riga di comando comincia con `remotix-figlio --figlio-interno`;
      · ⛔ ha **4 descrittori** (0,1,2 e il socket verso il padre) e NON ha
        nessun socket in comune col padre oltre a quello: la porta 7571 non
        se l'e' portata dietro;
      · nel registro c'e' «IL BUS DI SESSIONE E' MIO», e il padre non ha mai
        scritto niente del genere.
 2. `due`  ⭐ due connessioni dello stesso utente ⇒ **un figlio solo**, lo
    stesso pid, e nel registro «NON ne nasce un secondo — invariante I2».
 3. `distacco`  ⭐ il cliente chiude, e dopo 5 s il figlio e' **ancora vivo**,
    stesso pid, stato NON `Z`.  ⛔ Se morisse, I4 sarebbe rotta.
 4. `muore`  ⭐ `SIGKILL` al figlio ⇒ il padre lo raccoglie (il pid **sparisce**
    da /proc, non resta `Z`), scrive «se ne va», e una connessione nuova fa
    nascere un figlio con un pid **diverso**.
 5. `senza-palco`  ⭐ «prova» (uid 1001, senza /run/user/1001) entra: il figlio
    NASCE come uid 1001 e scrive «NON ho il bus di sessione».  ⛔ E non vede il
    desktop di nessun altro.
 6. `guasto-uid`  ⛔ col `setuid` tolto, il figlio esce **42** e nel registro
    c'e' «NON SONO CHI DOVREI ESSERE».  Nessun fotogramma.
 7. `guasto-cieco`  ⛔ col `setuid` tolto E il controllo del figlio tolto,
    e' il PADRE ad abbattere: «MESSAGGIO RIFIUTATO», con dentro «il nucleo dice
    uid 0».  ⛔ Se questo caso fosse verde senza quella riga, vorrebbe dire che
    il padre si fida di quel che il figlio dichiara.

⛔ IL CASO OPPOSTO DI TUTTO IL BANCO — che aspetto avrebbe un prodotto che NON
   fa quel che §1.10-bis chiede: un figlio con `Uid: 0 0 0 0` che consegna
   fotogrammi lo stesso, e un registro pieno di ⭐.  ⇒ Per questo il banco legge
   `/proc` e non il registro.
"""


def dico(t=""):
    print(t, flush=True)


def ok(t):
    dico(f"    \033[1;32mOK\033[0m  {t}")


def ko(t):
    dico(f"    \033[1;31mNO\033[0m  {t}")


def inf(t):
    dico(f"    --  {t}")


def titolo(t):
    dico(f"\n\033[1m== {t}\033[0m")


# ---------------------------------------------------------------------------
# Le letture dal NUCLEO.  ⛔ Ciascuna distingue «non c'e'» da «non ho potuto
#    leggere», e la seconda e' un `None` che il chiamante deve trattare come un
#    «non ho misurato» — mai come uno zero.


def leggi(percorso):
    try:
        with open(percorso, "rb") as f:
            return f.read()
    except FileNotFoundError:
        return b""          # non c'e'
    except PermissionError:
        return None         # ⛔ NON ho potuto leggere: e' un fatto diverso
    except OSError:
        return None


def stato_proc(pid):
    """I quattro uid, i quattro gid e lo stato, chiesti al nucleo."""
    b = leggi(f"/proc/{pid}/status")
    if b is None:
        return None
    if not b:
        return {}
    fuori = {}
    for riga in b.decode("utf-8", "replace").splitlines():
        if riga.startswith("Uid:"):
            fuori["uid"] = [int(x) for x in riga.split()[1:5]]
        elif riga.startswith("Gid:"):
            fuori["gid"] = [int(x) for x in riga.split()[1:5]]
        elif riga.startswith("State:"):
            fuori["stato"] = riga.split()[1]
        elif riga.startswith("PPid:"):
            fuori["ppid"] = int(riga.split()[1])
    return fuori


def cmdline(pid):
    b = leggi(f"/proc/{pid}/cmdline")
    if b is None:
        return None
    return b.replace(b"\x00", b" ").decode("utf-8", "replace").strip()


def descrittori(pid):
    """{fd: bersaglio}.  ⛔ `None` = non ho potuto guardare."""
    try:
        elenco = os.listdir(f"/proc/{pid}/fd")
    except (PermissionError, OSError):
        return None
    fuori = {}
    for n in elenco:
        try:
            fuori[int(n)] = os.readlink(f"/proc/{pid}/fd/{n}")
        except OSError:
            fuori[int(n)] = "(sparito mentre guardavo)"
    return fuori


def figli_di(pid_padre):
    """I figli «--figlio-interno» del server, chiesti a /proc.

    ⛔ NON si usa `pgrep remotix`: prenderebbe anche i server degli altri
       banchi (7448, 7501, 7561), e un banco che conta i processi di qualcun
       altro misura la macchina e non il prodotto.
    """
    fuori = []
    for n in os.listdir("/proc"):
        if not n.isdigit():
            continue
        s = stato_proc(n)
        if not s or s.get("ppid") != int(pid_padre):
            continue
        riga = cmdline(n)
        if not riga or "--figlio-interno" not in riga:
            continue
        pezzi = riga.split()
        fuori.append({
            "pid": int(n),
            "argv": riga,
            "utente": pezzi[2] if len(pezzi) > 2 else "?",
            "uid": s.get("uid"),
            "gid": s.get("gid"),
            "stato": s.get("stato"),
            "fd": descrittori(n),
        })
    return fuori


class Registro:
    """Il registro del server, letto da un OFFSET — B0.7.

    ⛔ Leggerlo dall'inizio conterebbe le righe di ieri.  E `dimensione()` si
       prende PRIMA di ogni prova, non dopo.
    """

    def __init__(self, percorso):
        self.percorso = percorso
        self.leggibile = os.path.exists(percorso)

    def offset(self):
        try:
            return os.path.getsize(self.percorso)
        except OSError:
            return None

    def da(self, off):
        if off is None:
            return None
        try:
            with open(self.percorso, "rb") as f:
                f.seek(off)
                return f.read().decode("utf-8", "replace")
        except OSError:
            return None


def aspetta(cond, secondi=15.0, passo=0.2):
    """Marcatori, non `sleep`: si aspetta una CONDIZIONE, e si dice quanto."""
    t0 = time.time()
    while time.time() - t0 < secondi:
        v = cond()
        if v:
            return v, time.time() - t0
        time.sleep(passo)
    return None, time.time() - t0


def cliente(a, attesa=6.0, utente=None, parola=None):
    """Un giro del cliente RCP indipendente (`02-filo-cliente.py`).

    ⭐ Non si riscrive un client: quello e' gia' un arbitro certificato di F2.4,
       e usarlo qui vuol dire che «la sessione arriva a SESSIONE» lo dice un
       programma che non e' questo banco.
    """
    parola_file = None
    if parola is not None:
        # ⛔ D12: la parola non passa mai da `argv`.
        parola_file = os.path.join(a.lavoro, "parola-caso")
        vecchia = os.umask(0o077)
        try:
            with open(parola_file, "w") as f:
                f.write(parola)
        finally:
            os.umask(vecchia)
    cmd = [sys.executable, os.path.join(QUI, "02-filo-cliente.py"),
           "--indirizzo", a.indirizzo, "--porta", str(a.porta),
           "--utente", utente or a.utente,
           "--parola-file", parola_file or a.parola_file,
           # ⛔ `--codec 1`, e non 2: quel numero dice al giudice **che cosa
           #    aspettarsi**, e la negoziazione di §4.3 la fa il `CIAO` di
           #    `01-b3-cliente.py`, che di codec ne dichiara due e si sente
           #    rispondere HEVC.  ⚠ `[M]` 12 agosto 2026, primo giro: con
           #    `--codec 2` il cliente ha detto «ERRORE_PROTOCOLLO: codec 1, ma
           #    si era negoziato 2» — cioe' un rosso puntato sul SERVER per una
           #    riga di questo banco.  E' la seconda volta che questo cliente
           #    accusa il server (`P2-6-montaggio.md` §5.2), e la seconda volta
           #    che aveva torto.
           "--codec", "1", "--attesa", str(attesa)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=attesa + 90)
    if parola_file:
        try:
            os.unlink(parola_file)
        except OSError:
            pass
    return p


# ---------------------------------------------------------------------------
# I casi


def caso_nasce(a, reg, guai):
    titolo("1. `nasce` — un figlio, che gira COME L'UTENTE (chiesto al nucleo)")
    off = reg.offset()
    prima = figli_di(a.pid_server)
    inf(f"figli prima: {len(prima)}")
    # ⛔ LA SCENA DI QUESTO CASO E' «UN SERVER APPENA ACCESO», e si VERIFICA
    #    invece di sperarci: con un figlio gia' vivo, I2 fa la cosa giusta —
    #    non ne nasce un secondo — e questo caso non vedrebbe ne' la
    #    presentazione ne' la riga del bus.  ⚠ Sarebbe un ROSSO su un prodotto
    #    sano, ed e' il difetto che il banco puo' fare a se stesso.
    if prima:
        ko(f"⛔ c'e' gia' {len(prima)} figlio vivo: questo caso vuole un server "
           f"APPENA ACCESO.  Non misuro, e non stampo un verde — si rifa' "
           f"«riaccendi» e poi «misura nasce».")
        guai.append("nasce: scena sbagliata (un figlio c'era gia')")
        return

    p = cliente(a)
    inf(f"il cliente e' uscito {p.returncode}")
    for r in p.stdout.splitlines():
        if "SESSIONE" in r or "fotogrammi" in r or "ACCETTATO" in r:
            inf(r.strip())

    dopo, quanto = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not dopo:
        ko("⛔ NESSUN figlio dopo un accesso ammesso: §1.10-bis non e' viva")
        guai.append("nasce: nessun figlio")
        return
    ok(f"{len(dopo)} figlio dopo {quanto:.1f} s")

    g = dopo[0]
    atteso = int(a.uid_atteso)
    if g["uid"] is None:
        ko("⛔ non ho POTUTO leggere gli uid del figlio: non e' un verde e non")
        ko("   e' un rosso — e' «non ho misurato».  Serve root.")
        guai.append("nasce: uid non leggibili")
        return
    if g["uid"] == [atteso] * 4:
        ok(f"⭐ il nucleo dice Uid: {g['uid']} — reale, effettivo, SALVATO e fs, "
           f"tutti e quattro a {atteso}")
    else:
        ko(f"⛔ Uid: {g['uid']}, atteso [{atteso}]*4.  ⚠ Un saved-uid diverso e' "
           f"un processo che puo' tornare root")
        guai.append(f"nasce: uid {g['uid']}")
    if g["gid"] == [int(a.gid_atteso)] * 4:
        ok(f"⭐ e Gid: {g['gid']}")
    else:
        ko(f"⛔ Gid: {g['gid']}, atteso [{a.gid_atteso}]*4")
        guai.append(f"nasce: gid {g['gid']}")

    if g["argv"].split()[0].endswith("remotix-figlio"):
        ok(f"la riga di comando lo dichiara: «{g['argv'][:90]}»")
    else:
        ko(f"⛔ argv[0] inatteso: «{g['argv'][:90]}»")
        guai.append("nasce: argv")

    # ⛔ LA PORTA NON SE L'E' PORTATA DIETRO — e non e' una deduzione.
    fdp = descrittori(a.pid_server)
    if g["fd"] is None or fdp is None:
        ko("⛔ non ho potuto leggere i descrittori: non dico che la porta non "
           "c'e'.  ⚠ «non ho guardato» non e' «non c'era» (LEZIONI.md §1.9)")
        guai.append("nasce: fd non leggibili")
    else:
        inf(f"il padre ha {len(fdp)} descrittori, il figlio {len(g['fd'])} "
            f"(⚠ ADESSO: dopo che ha aperto il palco)")
        for n, t in sorted(g["fd"].items())[:6]:
            inf(f"    fd {n} → {t}")
        comuni = set(g["fd"].values()) & set(fdp.values())
        # ⚠ 0,1,2 sono lo stesso registro apposta: e' quel che rende leggibile
        #   «chi ha detto che cosa».  Quel che NON deve esserci e' un socket
        #   del padre — la porta, o il socket del comando di sblocco.
        socket_comuni = {v for v in comuni if v.startswith("socket:")}
        if not socket_comuni:
            ok(f"⭐ ZERO socket in comune col padre: la porta {a.porta} NON se "
               f"l'e' portata dietro")
        else:
            ko(f"⛔ {len(socket_comuni)} socket in comune col padre: "
               f"{sorted(socket_comuni)}")
            guai.append("nasce: socket ereditati dal padre")
        # ⛔⭐ E IL NUMERO CHE CONTA E' QUELLO ALLA NASCITA, NON QUELLO DI ADESSO
        #     — difetto di QUESTO BANCO, trovato al primo giro, 12 agosto 2026.
        #
        #     La prima stesura pretendeva «≤ 4 descrittori» e ha dato un rosso a
        #     un prodotto sano: `[M]` il figlio ne aveva **34**, e i trenta in
        #     piu' erano PipeWire, il bus, gli eventfd e i memfd di
        #     `mutter-screen-cast` — cioe' **il palco**, cioe' esattamente la
        #     cosa che questo mandato esiste per fargli avere.
        #
        # ⇒ La grandezza vera e' *«quanti ne aveva quando e' nato»*, e il
        #   prodotto la CONTA da se' subito dopo l'`exec`, prima di aprire
        #   qualunque cosa: la riga «N descrittori aperti» del messaggio con cui
        #   si presenta.  ⚠ E' `LEZIONI.md` §1.13: si nomina la grandezza vera
        #   del fenomeno, non quella che gli somiglia.
        m = re.search(r"si presenta:.*?(\d+) descrittori aperti",
                      reg.da(off) or "")
        if not m:
            ko("⛔ il figlio non ha detto quanti descrittori aveva alla nascita: "
               "senza quel numero «non si e' portato dietro la porta» resta "
               "una speranza")
            guai.append("nasce: nessun conto dei descrittori alla nascita")
        elif int(m.group(1)) == 4:
            ok("⭐ e ALLA NASCITA ne aveva 4: 0, 1, 2 e il socket verso il "
               "padre.  ⛔ Il padre ne ha "
               f"{len(fdp)} — nessuno dei suoi e' passato di la'")
        else:
            ko(f"⛔ alla nascita ne aveva {m.group(1)}, non 4: qualcosa del "
               f"padre e' arrivato al figlio")
            guai.append(f"nasce: {m.group(1)} descrittori alla nascita")

    testo = reg.da(off) or ""
    if "IL BUS DI SESSIONE E' MIO" in testo:
        ok("⭐ e nel registro: «IL BUS DI SESSIONE E' MIO» — la cosa che root "
           "non puo' fare")
    else:
        ko("⛔ il figlio NON ha detto di avere il bus.  Le righe «figlio»:")
        for r in testo.splitlines():
            if " figlio " in r:
                inf(r.strip()[:160])
        guai.append("nasce: nessun bus")
    if "fotogramma completo da" in testo:
        ok("⭐ e un fotogramma e' arrivato dal figlio al padre")
    else:
        inf("⚠ nessun fotogramma dal figlio in questa finestra: guarda le righe "
            "«figlio»/«video» qui sopra per il perche'")


def caso_due(a, reg, guai):
    titolo("2. `due` — due connessioni dello stesso utente, UN figlio solo (I2)")
    off = reg.offset()
    prima = figli_di(a.pid_server)
    if not prima:
        cliente(a)
        prima, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not prima:
        ko("⛔ non c'e' nemmeno il primo figlio: non ho potuto misurare")
        guai.append("due: nessun primo figlio")
        return
    pid1 = prima[0]["pid"]
    inf(f"il figlio di adesso e' il pid {pid1}")

    p = cliente(a)
    inf(f"seconda connessione: il cliente e' uscito {p.returncode}")
    time.sleep(1.0)
    dopo = figli_di(a.pid_server)
    if len(dopo) == 1 and dopo[0]["pid"] == pid1:
        ok(f"⭐ un figlio solo, e lo STESSO pid {pid1}: I2 regge, e il palco e' "
           f"lo stesso perche' e' della sessione (I4)")
    else:
        ko(f"⛔ dopo la seconda connessione i figli sono {len(dopo)}: "
           f"{[x['pid'] for x in dopo]}")
        guai.append("due: piu' di un figlio")
    testo = reg.da(off) or ""
    if "NON ne nasce un secondo" in testo:
        ok("⭐ e il prodotto lo dice: «NON ne nasce un secondo — invariante I2»")
    else:
        ko("⛔ il prodotto non ha scritto la riga di I2: il comportamento "
           "giusto senza la riga e' un comportamento che nessuno puo' verificare")
        guai.append("due: riga I2 mancante")


def caso_distacco(a, reg, guai):
    titolo("3. `distacco` — il cliente se ne va, il palco RESTA (I4)")
    prima = figli_di(a.pid_server)
    if not prima:
        cliente(a)
        prima, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not prima:
        ko("⛔ nessun figlio: non ho potuto misurare")
        guai.append("distacco: nessun figlio")
        return
    pid1 = prima[0]["pid"]
    inf(f"il figlio e' il pid {pid1}; il cliente si e' gia' scollegato "
        f"(il suo processo e' finito)")
    inf("aspetto 6 s con NESSUNA connessione viva…")
    time.sleep(6.0)
    s = stato_proc(pid1)
    if s is None:
        ko("⛔ non ho potuto leggere lo stato del figlio")
        guai.append("distacco: stato non leggibile")
        return
    if not s:
        ko(f"⛔ il figlio {pid1} NON C'E' PIU' dopo il distacco: l'invariante I4 "
           f"e' rotta — il palco apparteneva alla connessione")
        guai.append("distacco: il figlio e' morto")
        return
    if s.get("stato") == "Z":
        ko(f"⛔ il figlio {pid1} e' uno ZOMBIE: «vivo» e «morto» hanno la stessa "
           f"faccia in /proc, ed e' il difetto gia' pagato con l'aiutante")
        guai.append("distacco: zombie")
        return
    ok(f"⭐ il figlio {pid1} e' ancora vivo (stato {s['stato']}), uid {s['uid']}: "
       f"il palco appartiene alla SESSIONE, non alla connessione (I4)")


def caso_muore(a, reg, guai):
    titolo("4. `muore` — ucciso il figlio, il padre lo RACCOGLIE e lo dice")
    off = reg.offset()
    prima = figli_di(a.pid_server)
    if not prima:
        cliente(a)
        prima, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not prima:
        ko("⛔ nessun figlio: non ho potuto misurare")
        guai.append("muore: nessun figlio")
        return
    pid1 = prima[0]["pid"]
    inf(f"ammazzo il figlio {pid1} con SIGKILL — cosi' non puo' salutare "
        f"nessuno e nessun gestore puo' rispondere al posto suo")
    try:
        os.kill(pid1, signal.SIGKILL)
    except OSError as e:
        ko(f"⛔ non ho potuto ucciderlo: {e}")
        guai.append("muore: kill fallito")
        return

    def sparito():
        s = stato_proc(pid1)
        if s is None:
            return None
        if not s:
            return "sparito"
        if s.get("stato") == "Z":
            return None      # ⛔ zombie: NON e' «raccolto»
        return None

    v, quanto = aspetta(sparito, 15)
    if v:
        ok(f"⭐ il pid {pid1} e' sparito da /proc dopo {quanto:.1f} s: il padre "
           f"l'ha RACCOLTO, e «morto» non ha piu' la stessa faccia di «vivo»")
    else:
        s = stato_proc(pid1) or {}
        ko(f"⛔ dopo {quanto:.1f} s il pid {pid1} c'e' ancora, stato "
           f"{s.get('stato')}: se e' `Z` e' uno zombie non raccolto")
        guai.append("muore: non raccolto")

    testo = reg.da(off) or ""
    if "se ne va" in testo and "l'ha ucciso il segnale 9" in testo:
        ok("⭐ e il registro lo dice con la causa: «l'ha ucciso il segnale 9»")
    else:
        ko("⛔ il registro non nomina la causa della morte")
        guai.append("muore: causa non scritta")
    if "SVUOTATO" in testo:
        ok("⭐ e il deposito del video e' stato SVUOTATO: l'immagine di un "
           "utente non resta in casa dopo che il suo palco e' morto")
    else:
        inf("⚠ nessun «SVUOTATO»: o il deposito non era suo, o non c'era")

    off2 = reg.offset()
    p = cliente(a)
    inf(f"connessione nuova: il cliente e' uscito {p.returncode}")
    nuovi, _ = aspetta(lambda: figli_di(a.pid_server) or None, 20)
    if not nuovi:
        ko("⛔ dopo la morte del figlio NON ne rinasce uno: la casella e' "
           "rimasta occupata da un morto")
        guai.append("muore: non rinasce")
    elif nuovi[0]["pid"] != pid1:
        ok(f"⭐ ne e' nato uno nuovo, pid {nuovi[0]['pid']} ≠ {pid1}")
    else:
        ko("⛔ il pid e' lo stesso: qualcosa non torna")
        guai.append("muore: stesso pid")


def caso_senza_palco(a, reg, guai):
    titolo("5. `senza-palco` — un utente che il bus NON ce l'ha")
    off = reg.offset()
    p = cliente(a, utente=a.utente2, parola=a.parola2)
    inf(f"il cliente di «{a.utente2}» e' uscito {p.returncode}")
    for r in p.stdout.splitlines():
        if "SESSIONE" in r or "fotogrammi" in r or "AMMESSO" in r:
            inf(r.strip())
    # ⛔⭐ LA PROVA CHE CONTA DI QUESTO CASO, e la prima stesura NON la faceva:
    #     «prova» non deve vedere **niente**.  `[M]` 12 agosto 2026, primo giro:
    #     ne vedeva UNO, conforme — ed era il desktop di «nicfio», servito dal
    #     deposito di PROCESSO di `webtransport.c`.  ⛔ Non «non ricevi niente»:
    #     **ricevi il desktop di un altro**, che e' I3 violata in modo
    #     invisibile.  ⇒ Questa riga e' la sola che lo puo' vedere.
    visti = 0
    for r in p.stdout.splitlines():
        m = re.search(r"(\d+) fotogrammi, tutti conformi", r)
        if m:
            visti = int(m.group(1))
    if visti == 0:
        ok(f"⭐⭐ «{a.utente2}» ha visto ZERO fotogrammi: NON gli e' arrivato il "
           f"desktop di «{a.utente}»")
    else:
        ko(f"⛔⛔ «{a.utente2}» ha ricevuto {visti} fotogrammi, e il suo palco "
           f"non ne ha prodotto nemmeno uno ⇒ sono di un ALTRO utente.  "
           f"Invariante I3 violata in modo invisibile.")
        guai.append("senza-palco: FUGA DI PIXEL fra utenti")
    dopo, _ = aspetta(
        lambda: [x for x in figli_di(a.pid_server) if x["utente"] == a.utente2]
        or None, 20)
    if not dopo:
        ko(f"⛔ nessun figlio per «{a.utente2}»: la sessione e' stata ammessa e "
           f"il palco non e' stato nemmeno TENTATO")
        guai.append("senza-palco: nessun figlio")
        return
    g = dopo[0]
    ok(f"⭐ il figlio di «{a.utente2}» c'e': pid {g['pid']}, Uid: {g['uid']}")
    if g["uid"] and g["uid"][0] != int(a.uid_atteso):
        ok(f"⭐ e NON e' l'uid di «{a.utente}» ({a.uid_atteso}): due utenti, due "
           f"identita' — che e' tutto il mandato")
    else:
        ko("⛔ i due utenti hanno lo stesso uid: questo banco non prova niente")
        guai.append("senza-palco: stesso uid")
    testo = reg.da(off) or ""
    if "NON ho il bus di sessione" in testo:
        ok("⭐ e il figlio DICE che non ha il bus, invece di tacere: «non ho "
           "potuto guardare» non e' «non c'e' la sessione»")
    else:
        ko("⛔ il figlio non ha dichiarato l'assenza del bus")
        guai.append("senza-palco: assenza non dichiarata")
    if "NON entra in deposito" in testo:
        ok("⭐ e se avesse consegnato, il deposito di un altro l'avrebbe "
           "rifiutato (la guardia di `main.c`)")


def caso_guasto(a, reg, guai, cieco):
    nome = "guasto-cieco" if cieco else "guasto-uid"
    titolo(f"{'7' if cieco else '6'}. `{nome}` — un figlio che gira come "
           f"l'utente SBAGLIATO")
    off = reg.offset()
    p = cliente(a)
    inf(f"il cliente e' uscito {p.returncode}")
    time.sleep(3.0)
    vivi = figli_di(a.pid_server)
    testo = reg.da(off) or ""

    if vivi:
        s = vivi[0]["uid"]
        ko(f"⛔⛔ c'e' un figlio VIVO con Uid: {s} mentre il guasto e' innestato: "
           f"nessuno dei due muri ha morso")
        guai.append(f"{nome}: figlio vivo")
    else:
        ok("⭐ nessun figlio vivo: il guasto e' stato fermato")

    if cieco:
        if "MESSAGGIO RIFIUTATO" in testo and "il nucleo dice uid 0" in testo:
            ok("⭐⭐ e a fermarlo e' stato IL PADRE, sulle credenziali timbrate "
               "dal nucleo: «MESSAGGIO RIFIUTATO … il nucleo dice uid 0»")
        else:
            ko("⛔ il padre NON ha rifiutato sul timbro del nucleo: la verifica "
               "a ogni messaggio non ha morso, e questo caso e' l'unico che la "
               "puo' vedere")
            guai.append("guasto-cieco: nessun rifiuto del padre")
    else:
        # ⛔ I MURI DEL FIGLIO SONO DUE, e il banco li accetta tutt'e due: lo
        #    stesso controllo — `getresuid()` — sta PRIMA dell'`exec` (uscita
        #    35) e DOPO (uscita 42).  `[M]` 12 agosto 2026: a mordere e' stato
        #    il primo, e il banco pretendeva le parole del secondo.  ⚠ Quel che
        #    conta non e' QUALE muro: e' che la causa sia NOMINATA — «e' uscito
        #    con 35» non e' una diagnosi, «NON E' SCESO all'utente» si'.
        if "NON E' SCESO all'utente" in testo or "NON E' CHI DOVREBBE" in testo:
            ok("⭐ e a fermarlo e' stato il figlio stesso, rileggendo i propri "
               "uid dal nucleo — e il padre ne ha scritto la CAUSA, non il "
               "numero")
        else:
            ko("⛔ il figlio non si e' accorto di non essere sceso, o il padre "
               "non ha nominato la causa")
            guai.append("guasto-uid: nessun controllo del figlio")
    for r in testo.splitlines():
        if " figlio " in r and ("⛔" in r or "NON" in r):
            inf(r.strip()[:170])


CASI = {
    "nasce": caso_nasce,
    "due": caso_due,
    "distacco": caso_distacco,
    "muore": caso_muore,
    "senza-palco": caso_senza_palco,
    "guasto-uid": lambda a, r, g: caso_guasto(a, r, g, False),
    "guasto-cieco": lambda a, r, g: caso_guasto(a, r, g, True),
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--previsione", action="store_true")
    p.add_argument("--caso", default="nasce")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7571)
    p.add_argument("--pid-server", type=int, default=0)
    # ⛔ IL PID SI LEGGE DAL FILE, NON DA UNA SOSTITUZIONE DI SHELL.
    #    ⚠ `p=$(cat …)` dentro `ssh → enter.sh → bash -lc` attraversa TRE
    #    livelli di virgolette e muore in mezzo: `[M]` 12 agosto 2026, questo
    #    banco, primo giro — il `$(…)` e' arrivato vuoto e `argparse` ha detto
    #    «expected one argument».  E' la stessa forma che ha gia' fatto girare
    #    un caso «l'aiutante e' morto» su un aiutante VIVO
    #    (`PAM-filo-unico.md` §6).  ⇒ Un file non ha livelli di virgolette.
    p.add_argument("--pid-file", default="")
    p.add_argument("--registro", default="")
    p.add_argument("--utente", default="nicfio")
    p.add_argument("--uid-atteso", default="1000")
    p.add_argument("--gid-atteso", default="1000")
    p.add_argument("--parola-file", default="")
    p.add_argument("--utente2", default="prova")
    p.add_argument("--parola2", default="parola-di-prova")
    p.add_argument("--lavoro", default="/srv/src/tmp")
    p.add_argument("--uscita", default="")
    a = p.parse_args()

    if a.previsione:
        dico(PREVISIONE)
        return 0

    if a.pid_file:
        try:
            with open(a.pid_file) as f:
                a.pid_server = int(f.read().strip())
        except (OSError, ValueError) as e:
            ko(f"⛔ il file del pid «{a.pid_file}» non si legge: {e}.  ⚠ Non e' "
               f"«il server non c'e'»: e' «non ho potuto guardare», e senza il "
               f"pid ogni lettura di /proc sarebbe di un processo a caso.")
            return 2

    titolo("0. Lo stato iniziale, dichiarato E verificato (B0.1)")
    if os.geteuid() != 0:
        ko("⛔ questo banco vuole root: meta' delle letture sono su /proc di un "
           "processo di root, e «non ho potuto leggere» non e' «non c'era».")
        return 2
    s = stato_proc(a.pid_server)
    if not s:
        ko(f"⛔ il pid {a.pid_server} non esiste: non c'e' niente da misurare")
        return 2
    inf(f"il server e' il pid {a.pid_server}, Uid: {s.get('uid')}")
    if s.get("uid", [1])[1] != 0:
        ko("⛔ il server NON gira da root: allora non puo' ne' verificare la "
           "parola di un altro ne' far scendere un figlio.  ⚠ Questo banco "
           "sarebbe verde per costruzione, quindi esce 2 (vacuita').")
        return 2
    ok("⭐ il server e' root: e' il regime di §1.10-bis")
    inf(f"riga: {(cmdline(a.pid_server) or '')[:150]}")
    reg = Registro(a.registro)
    if not reg.leggibile:
        ko(f"⛔ il registro «{a.registro}» non c'e': senza, meta' delle prove "
           f"non ha dove guardare")
        return 2
    ok(f"registro: {a.registro} ({reg.offset()} byte finora)")
    prima = figli_di(a.pid_server)
    inf(f"figli gia' vivi: {len(prima)} {[x['pid'] for x in prima]}")

    guai = []
    casi = list(CASI) if a.caso == "tutti" else [a.caso]
    for c in casi:
        if c not in CASI:
            ko(f"caso ignoto: {c}")
            return 2
        CASI[c](a, reg, guai)

    titolo("Il verdetto")
    if not guai:
        dico("    \033[1;32m⭐ tutto come l'atteso\033[0m")
        esito = 0
    else:
        dico(f"    \033[1;31m⛔ {len(guai)} prove hanno dato altro\033[0m")
        for g in guai:
            ko(g)
        esito = 1

    if a.uscita:
        try:
            with open(a.uscita, "a") as f:
                f.write(json.dumps({
                    "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "banco": "02-figlio",
                    "casi": casi,
                    "porta": a.porta,
                    "pid_server": a.pid_server,
                    "utente": a.utente,
                    "guai": guai,
                    "esito": esito,
                }, ensure_ascii=False) + "\n")
        except OSError as e:
            ko(f"⚠ l'esito non si e' scritto in {a.uscita}: {e}")
    return esito


if __name__ == "__main__":
    sys.exit(main())
