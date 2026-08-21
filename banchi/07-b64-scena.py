#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-scena — UN GIRO DI R26, sulla macchina di prova, DA ROOT.

⛔ Che cosa misura, e perche' non basta guardare le politiche dei thread:
   R26 dice che il `data-loop` di PipeWire, senza `SCHED_FIFO`, «raccoglie i
   campioni a priorita' normale mentre nello stesso processo il codificatore
   video si prende un core».  ⚠ La politica del thread e' meta' della frase:
   l'altra meta' e' **quanto quel thread ha aspettato la CPU**, e sta in
   `/proc/<pid>/task/<tid>/schedstat`, secondo campo — nanosecondi passati in
   coda di esecuzione (`run_delay`).  ⇒ Qui si leggono tutt'e due, ogni secondo.

⛔ E il verdetto NON lo da' questo file: lui allestisce la scena e raccoglie.
   Il giudizio e' di `07-b64-orecchio.py`, che ASCOLTA i campioni (regola (a)
   di `07-b43`: si ascolta, non si contano i blocchi).

⭐ L'ARBITRO INDIPENDENTE: dentro la sessione gira anche un `pw-record` sul
   monitor dello stesso sink.  Se un buco compare in tutt'e due le prese, e'
   nato **prima** di REMOTIX (nel lettore o nel grafo); se compare solo nella
   nostra, e' nostro.  ⚠ Non e' un arbitro perfetto — `pw-record` ha un suo
   `data-loop`, soggetto allo stesso difetto — ma distingue i due imputati piu'
   grossi, e senza di lui non si distinguono affatto.

Uso (da root, sulla macchina di prova):
    python3 07-b64-scena.py giro --nome 1-fermo --carico no  --rt come-sta
    python3 07-b64-scena.py giro --nome 2-lavora --carico si --rt come-sta
    python3 07-b64-scena.py giro --nome 3-lavora-rt --carico si --rt si
    python3 07-b64-scena.py fotografia        # solo i thread, senza scena
"""
import argparse, json, os, signal, subprocess, sys, time

UTENTE = os.environ.get("UTENTE", "provar7")
UID_B = int(os.environ.get("UID_B", "1018"))
PORTA = int(os.environ.get("PORTA", "7801"))
IND = os.environ.get("IND", "192.168.0.2")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/07-r-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/07-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/07-r")
SINK = os.environ.get("SINK", "remotix")
SCENA_BIN = os.environ.get("SCENA_BIN", "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")

POLITICA = {0: "normale", 1: "FIFO", 2: "RR", 3: "batch", 5: "idle", 6: "deadline"}
HZ_TICK = os.sysconf("SC_CLK_TCK")


# ── l'ambiente della sessione, composto da zero (CODER.md §4.5) ────────────
def come_utente(cmd, **kw):
    base = ["setpriv", "--reuid=%d" % UID_B, "--regid=%d" % UID_B, "--init-groups",
            "env", "-i",
            "HOME=/home/%s" % UTENTE, "USER=%s" % UTENTE, "LANG=C.UTF-8",
            "PATH=/usr/local/bin:/usr/bin:/bin",
            "XDG_RUNTIME_DIR=/run/user/%d" % UID_B,
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus" % UID_B,
            "XDG_CURRENT_DESKTOP=GNOME", "XDG_SESSION_DESKTOP=gnome",
            "XDG_SESSION_TYPE=wayland"]
    return base + cmd


def esegui(cmd, tetto=20):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=tetto)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, "", "⛔ scaduto dopo %d s" % tetto


# ── /proc: la politica, la priorita' e L'ATTESA IN CODA ────────────────────
def thread_stat(pid, tid):
    try:
        d = open("/proc/%d/task/%d/stat" % (pid, tid)).read()
    except Exception:
        return None
    a = d.index("("); b = d.rindex(")")
    nome = d[a + 1:b]
    c = d[b + 2:].split()
    utime, stime = int(c[11]), int(c[12])
    rtprio, policy = int(c[37]), int(c[38])
    # ⭐ schedstat: [tempo sulla CPU ns, ATTESA IN CODA ns, quanti quanti]
    attesa = eseguiti = 0
    try:
        s = open("/proc/%d/task/%d/schedstat" % (pid, tid)).read().split()
        attesa, eseguiti = int(s[1]), int(s[2])
    except Exception:
        pass
    return {"nome": nome, "tid": tid, "cpu_tick": utime + stime,
            "rtprio": rtprio, "policy": policy,
            "politica": POLITICA.get(policy, str(policy)),
            "attesa_ns": attesa, "quanti": eseguiti}


def limite_rt(pid):
    try:
        for r in open("/proc/%d/limits" % pid):
            if "realtime priority" in r.lower():
                return r.split()[3]
    except Exception:
        pass
    return "?"


def processi_interessanti():
    """Il figlio della sessione, i demoni di PipeWire dell'utente, il lettore e
       l'arbitro.  ⛔ E il SERVER, che e' quello che porta il rlimit."""
    fuori = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        p = int(d)
        try:
            uid = os.stat("/proc/%d" % p).st_uid
            comm = open("/proc/%d/comm" % p).read().strip()
            cmd = open("/proc/%d/cmdline" % p).read().replace("\0", " ")
        except Exception:
            continue
        mio = (uid == UID_B) or ("remotix" in comm and (str(PORTA) in cmd or UTENTE in cmd))
        if mio:
            fuori.append((p, uid, comm, cmd[:120]))
    return fuori


def fotografia():
    """Chi ha il tempo reale e chi no — la fotografia di R26, per intero."""
    r = []
    for p, uid, comm, cmd in sorted(processi_interessanti()):
        v = {"pid": p, "uid": uid, "comm": comm, "cmdline": cmd,
             "rlimit_rtprio": limite_rt(p), "thread": []}
        try:
            tids = sorted(int(t) for t in os.listdir("/proc/%d/task" % p))
        except Exception:
            tids = []
        for t in tids:
            s = thread_stat(p, t)
            if s:
                v["thread"].append(s)
        r.append(v)
    return r


# ── il grafo di PipeWire, letto DENTRO la sessione ─────────────────────────
def grafo():
    rc, out, err = esegui(come_utente(["pw-dump"]), 25)
    if rc != 0 or not out.strip():
        return {"errore": "pw-dump non ha prodotto niente (rc %d): %s" % (rc, err[:200])}
    try:
        d = json.loads(out)
    except Exception as e:
        return {"errore": "pw-dump illeggibile: %s" % e}
    r = {"sink_id": None, "legami_in_ingresso": 0, "sink_presenti": []}
    for o in d:
        info = o.get("info") or {}
        p = info.get("props") or {}
        if p.get("media.class") == "Audio/Sink":
            r["sink_presenti"].append(p.get("node.name"))
        if p.get("node.name") == SINK and p.get("media.class") == "Audio/Sink":
            r["sink_id"] = o["id"]
            r["monitor_channel_volumes"] = p.get("monitor.channel-volumes")
    for o in d:
        if str(o.get("type", "")).endswith("Link"):
            p = (o.get("info") or {}).get("props") or {}
            if r["sink_id"] is not None and p.get("link.input.node") == r["sink_id"]:
                r["legami_in_ingresso"] += 1
    return r


# ── il tono, scritto qui cosi' l'ampiezza e' NOTA ──────────────────────────
def tono(hz, secondi, ampiezza=0.5):
    import math, struct, wave
    f = os.path.join(LAV, "tono-%d.wav" % hz)
    if os.path.exists(f) and os.path.getsize(f) >= 48000 * secondi * 4:
        return f
    w = wave.open(f, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
    d = bytearray()
    for n in range(48000 * secondi):
        v = int(ampiezza * math.sin(2 * math.pi * hz * n / 48000) * 32767)
        d += struct.pack("<hh", v, v)
    w.writeframes(bytes(d)); w.close()
    os.chmod(f, 0o644)
    return f


# ── il carico: il desktop che LAVORA ───────────────────────────────────────
def monitor_catturato():
    """⛔ Il nome del monitor NON si scrive a mano: lo dice il registro del MIO
       prodotto.  Una scena accesa «da qualche parte» non carica il palco."""
    try:
        testo = open(os.path.join(LAV, "registro.log"), errors="replace").read()
    except Exception:
        return None
    # ⛔ La forma e' quella di `04-b32-terreno.sh`, e non si reinventa: il
    #    registro scrive `monitor «Meta-0»`.  ⚠ La prima stesura cercava una
    #    parola qualsiasi con un trattino e un numero e non trovava niente: il
    #    giro «il desktop lavora» girava SENZA la scena, e lo diceva soltanto in
    #    un campo del JSON che nessuno guardava.
    import re
    m = [x for x in re.findall(r"monitor \u00ab([^\u00bb]*)\u00bb", testo) if x]
    return m[-1] if m else None


def monitor_atteso(tetto_s=25.0):
    """⛔ IL NOME DEL MONITOR SI ASPETTA — e la prima stesura no.

       `[M]` 21 agosto 2026: il registro scrive «monitor «Meta-0»» ~2,9 s dopo
       l apertura della sessione, e M3 (il tono che suona) arriva prima.  ⇒ Chi
       legge il registro a M3 non trova il nome, la scena non parte, e il giro
       si chiama lo stesso «il desktop lavora».  ⚠ Nei giri di ieri il difetto
       NON si vedeva perche' il registro conteneva ancora la riga della sessione
       precedente: cioe' funzionava per un motivo sbagliato, ed e' la forma
       peggiore — un banco che smette di funzionare quando lo si pulisce."""
    fine = time.time() + tetto_s
    while time.time() < fine:
        u = monitor_catturato()
        if u:
            return u
        time.sleep(0.5)
    return None


def carico_accendi(quanti):
    """⛔ Due carichi, e sono due cose diverse:
         · la SCENA, che fa lavorare la cattura e il codificatore del figlio —
           e' quella che R26 nomina;
         · i BRUCIATORI, che tolgono la CPU a tutti — e' la condizione in cui
           una priorita' serve a qualcosa.
       ⚠ Si dichiara quale dei due e' partito: se la scena non parte, il giro
         resta valido ma NON e' piu' «il desktop lavora», ed e' un'altra cosa."""
    stato = {"scena": None, "bruciatori": 0, "scena_perche_no": None}
    usc = monitor_atteso()
    if os.access(SCENA_BIN, os.X_OK) and usc:
        log = open(os.path.join(LAV, "scena.log"), "ab")
        p = subprocess.Popen(
            come_utente(["env", "WAYLAND_DISPLAY=wayland-0", SCENA_BIN,
                         "--uscita", usc, "--movimento", "barra",
                         "--shm", "/07-b64-scena", "--giro", "b64"]),
            stdout=log, stderr=log)
        time.sleep(1.0)
        vivo = subprocess.run(["pgrep", "-u", str(UID_B), "-f", "04-b30-scena --uscita"],
                              capture_output=True).stdout.decode().split()
        stato["scena"] = usc if vivo else None
        if not vivo:
            stato["scena_perche_no"] = "la scena e' partita e morta subito (vedi scena.log)"
        stato["_p"] = p
    else:
        stato["scena_perche_no"] = ("il binario %s non e' eseguibile" % SCENA_BIN
                                    if not os.access(SCENA_BIN, os.X_OK)
                                    else "non so quale monitor cattura il mio figlio")
    bruc = []
    for _ in range(quanti):
        bruc.append(subprocess.Popen(
            come_utente(["python3", "-c", "\nwhile True: pass\n"]),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    stato["bruciatori"] = len(bruc)
    stato["_bruc"] = bruc
    return stato


def carico_spegni(stato):
    for p in stato.get("_bruc", []):
        try: p.kill()
        except Exception: pass
    subprocess.run(["pkill", "-u", str(UID_B), "-f", "while True: pass"],
                   capture_output=True)
    subprocess.run(["pkill", "-u", str(UID_B), "-f", "04-b30-scena"], capture_output=True)


# ── ⭐⭐ IL COLLO DI BOTTIGLIA VERO DI R26: UN SOLO CORE ────────────────────
#
# R26 dice, parola per parola: «il suo `data-loop` resta a priorita' normale
# **mentre nello stesso processo il codificatore video si prende un core per
# decine di millisecondi**».  ⛔ Su venti core quella frase non ha modo di
# avverarsi: il thread audio trova sempre un core libero, e infatti a carico 25
# la sua attesa in coda e' di 6 us su un quanto di 5,33 ms.
#
# ⇒ Per misurare R26 bisogna **costruire** la condizione che descrive: si
#   stringe tutto il percorso audio (il figlio col suo codificatore, i demoni
#   di PipeWire, il lettore e l'arbitro) su **un core solo**.
#
# ⭐ E ha un secondo pregio, che non e' secondario: sulla macchina lavorano
#   altri nove banchi.  Un carico che satura venti core falserebbe le loro
#   misure di tempo; questo ne occupa **uno**.
def stringi_su_un_core(cpu):
    fatti = []
    for v in fotografia():
        if v["comm"] in ("remotix", "pipewire", "pipewire-pulse", "wireplumber",
                         "pw-play", "pw-record", "04-b30-scena") and v["uid"] != 0:
            rc, _, err = esegui(["taskset", "-acp", str(cpu), str(v["pid"])], 5)
            fatti.append("%s[%d] rc=%d" % (v["comm"], v["pid"], rc))
    return fatti


def allarga(cpu_tutti):
    fatti = []
    for v in fotografia():
        if v["uid"] != 0:
            esegui(["taskset", "-acp", cpu_tutti, str(v["pid"])], 5)
            fatti.append(v["comm"])
    return fatti


# ── il tempo reale, dato a mano — ⭐ e' l'A/B di R26 ───────────────────────
def rt_applica(prio):
    """⛔ Non si «configura PipeWire»: si sposta la politica dei thread VIVI con
       `chrt`, cosi' fra i due giri cambia UNA cosa sola.  ⚠ E si registra chi
       e' stato spostato e chi ha rifiutato."""
    fatti, falliti = [], []
    for v in fotografia():
        for t in v["thread"]:
            if "data-loop" in t["nome"] or "pw-data" in t["nome"]:
                rc, _, err = esegui(["chrt", "-f", "-p", str(prio), str(t["tid"])], 5)
                (fatti if rc == 0 else falliti).append(
                    "%s/%s[%d]%s" % (v["comm"], t["nome"], t["tid"],
                                     "" if rc == 0 else " ⛔ " + err.strip()[:60]))
    return {"promossi": fatti, "falliti": falliti, "prio": prio}


# ⛔⛔ E IL TEMPO REALE, SU QUESTA MACCHINA, NON SI PUO' AVERE AFFATTO.
#
#     `[M]` 21 agosto 2026: `chrt -f 10 /bin/true` **fallisce da root** in
#     qualunque cgroup che non sia la radice, e riesce nella radice.  Il
#     kernel (7.0, NIC-OS) ha `CONFIG_RT_GROUP_SCHED` con cgroup v2 unificato:
#     ogni processo che systemd mette in una slice o in uno scope — cioe' ogni
#     processo della macchina — non puo' ottenere `SCHED_FIFO`, e il rifiuto
#     arriva PRIMA che il kernel guardi `RLIMIT_RTPRIO`.
#
# Percio' l'A/B di R26 si fa con la LEVA CHE FUNZIONA, la cortesia (`nice`):
#   e' l'altra meta' di quel che l'unita' concede (`LimitNICE=-11`), e nessuno
#   la usa — `[M]` tutti i thread del percorso audio stanno a `nice 0`.
def nice_applica(livello):
    fatti, falliti = [], []
    for v in fotografia():
        if v["uid"] == 0:
            continue
        for t in v["thread"]:
            if ("data-loop" in t["nome"] or v["comm"] in ("pw-play", "pw-record")
                    or (v["comm"] in ("pipewire", "pipewire-pulse", "wireplumber")
                        and t["tid"] == v["pid"])):
                rc, _, err = esegui(["renice", "-n", str(livello), "-p", str(t["tid"])], 5)
                (fatti if rc == 0 else falliti).append(
                    "%s/%s[%d]%s" % (v["comm"], t["nome"], t["tid"],
                                     "" if rc == 0 else " NO " + err.strip()[:50]))
    return {"livello": livello, "fatti": fatti, "falliti": falliti}


def rt_rimetti():
    fatti = []
    for v in fotografia():
        for t in v["thread"]:
            if t["policy"] != 0 and ("data-loop" in t["nome"] or "pw-data" in t["nome"]):
                rc, _, _ = esegui(["chrt", "-o", "-p", "0", str(t["tid"])], 5)
                fatti.append("%s[%d] rc=%d" % (t["nome"], t["tid"], rc))
    return fatti


# ═══════════════════════════════════════════════════════════════════════════
def giro(a):
    esiti = {"nome": a.nome, "porta": PORTA, "utente": UTENTE,
             "ora_macchina": time.strftime("%Y-%m-%d %H:%M:%S"),
             "carico_chiesto": a.carico, "rt_chiesto": a.rt}
    base = os.path.join(LAV, a.nome)
    # ⚠ Quel che resta dal giro prima si SVUOTA (LEZIONI.md §2.3-quinquies).
    for e in (".jsonl", ".segnale", ".txt", ".rif.wav", ".esito.json"):
        try: os.remove(base + e)
        except Exception: pass

    esiti["carico_prima"] = open("/proc/loadavg").read().split()[:3]

    # ── il cliente parte per primo: e' lui che apre la sessione ────────────
    # ⭐ `--codec opus` serve al mandato sui datagram: l Opus e' quel che gira
    #    nelle sessioni vere, e costa 1/13 della banda del PCM.  ⚠ Il giudice
    #    dell orecchio non lo sa decodificare — con Opus si conta il TRASPORTO,
    #    e lo si dichiara invece di far finta di aver ascoltato.
    cmd = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
           "--utente %s --parola-file %s/parola --audio-codec %s "
           "--audio-scrivi %s/%s.jsonl --segnale %s/%s.segnale "
           "%s --resta %d"
           % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, a.codec,
              DENTRO_LAV, a.nome, DENTRO_LAV, a.nome,
              # ⛔ SENZA `--adatta` IL VIDEO NON PARTE, e il giro misurerebbe
              #    l audio da solo chiamandolo «audio contro video».  §6.6: il
              #    server manda fotogrammi dopo l `ADATTA_TELA`, che la pagina
              #    manda da se e il cliente di prova no.
              ("--adatta %s --video-scrivi %s/%s.265" % (a.tela, DENTRO_LAV, a.nome)
               if a.video == "si" else ""),
              a.secondi))
    fcli = open(base + ".txt", "wb")
    cli = subprocess.Popen(["bash", "/media/REMOTIX/enter.sh", "--root", cmd],
                           stdout=fcli, stderr=fcli)
    t0 = time.time()

    # M1 · il cliente ha aperto la sessione (un file scritto e chiuso e' un fatto)
    while time.time() - t0 < 90 and not os.path.exists(base + ".segnale"):
        if cli.poll() is not None:
            break
        time.sleep(0.2)
    esiti["M1_sessione_aperta"] = os.path.exists(base + ".segnale")
    esiti["M1_dopo_s"] = round(time.time() - t0, 2)
    if not esiti["M1_sessione_aperta"]:
        esiti["errore"] = ("⛔ M1 non e' arrivato: il cliente non ha aperto la "
                           "sessione.  ⚠ NON e' «l'audio non arriva»: e' «la "
                           "scena non e' stata allestita»")
        try: cli.kill()
        except Exception: pass
        cli.wait()
        fcli.close()
        esiti["cliente_coda"] = open(base + ".txt", errors="replace").read()[-1500:]
        json.dump(esiti, open(base + ".esito.json", "w"), ensure_ascii=False, indent=1)
        print(json.dumps(esiti, ensure_ascii=False, indent=1))
        return 2

    # M2 · il sink esiste nel grafo
    g = {}
    for _ in range(60):
        g = grafo()
        if g.get("sink_id"):
            break
        time.sleep(0.4)
    esiti["M2_grafo"] = g

    # ── l'arbitro indipendente: una seconda presa dello stesso monitor ─────
    rif = None
    # ⛔ La cartella dell arbitro e SUA: `pw-record` gira come l utente della
    #    sessione, e su $LAV (root 755) non puo creare niente.  ⚠ Il sintomo era
    #    "Permission denied" dentro un file di stderr che nessuno guardava, e il
    #    giro restava senza arbitro senza dirlo.
    dir_rif = os.path.join(LAV, "rif")
    os.makedirs(dir_rif, exist_ok=True)
    os.chown(dir_rif, UID_B, UID_B)
    rifwav = os.path.join(dir_rif, a.nome + ".rif.wav")
    if g.get("sink_id"):
        rif = subprocess.Popen(
            come_utente(["pw-record", "--target", str(g["sink_id"]),
                         "--rate", "48000", "--channels", "2", "--format", "s16",
                         rifwav]),
            stdout=subprocess.DEVNULL, stderr=open(base + ".rif.txt", "wb"))

    # M3 · il tono suona DAVVERO dentro il sink (lo dice il grafo, non pw-play)
    f = tono(a.hz, a.secondi + 30)
    play = subprocess.Popen(come_utente(["pw-play", "--target", SINK, f]),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    leg = 0
    for _ in range(50):
        gg = grafo()
        leg = gg.get("legami_in_ingresso", 0)
        if leg > 0:
            break
        time.sleep(0.3)
    esiti["M3_legami_in_ingresso"] = leg
    esiti["M3_il_tono_suona"] = leg > 0

    # ── il tempo reale, e i thread PRIMA ───────────────────────────────────
    esiti["fotografia_prima"] = fotografia()
    if a.nice is not None:
        esiti["nice_applicato"] = nice_applica(a.nice)
    if a.rt == "si":
        esiti["rt_applicato"] = rt_applica(a.prio)
    elif a.rt == "no":
        esiti["rt_applicato"] = {"nota": "rimessi a politica normale"}
        rt_rimetti()

    # ── il carico ──────────────────────────────────────────────────────────
    car = {"scena": None, "bruciatori": 0}
    if a.carico == "si":
        car = carico_accendi(a.bruciatori)
    esiti["carico"] = {k: v for k, v in car.items() if not k.startswith("_")}
    if a.cpu >= 0:
        time.sleep(1.0)
        esiti["stretti_su_core"] = {"cpu": a.cpu, "chi": stringi_su_un_core(a.cpu)}

    # ── il campionamento, un secondo per volta ─────────────────────────────
    campioni = []
    prima = {}
    tprima = time.time()
    while cli.poll() is None and time.time() - t0 < a.secondi + 40:
        time.sleep(1.0)
        adesso = time.time()
        dt = adesso - tprima
        riga = {"t": round(adesso - t0, 1), "carico": open("/proc/loadavg").read().split()[0],
                "thread": []}
        dopo = {}
        for v in fotografia():
            for t in v["thread"]:
                k = (v["pid"], t["tid"])
                dopo[k] = (t["cpu_tick"], t["attesa_ns"], t["quanti"])
                p = prima.get(k)
                if p is None:
                    continue
                cpu = (t["cpu_tick"] - p[0]) / HZ_TICK / dt * 100.0
                att = (t["attesa_ns"] - p[1]) / 1e6           # ms attesi in coda
                qua = t["quanti"] - p[2]
                # ⛔ I thread del PERCORSO AUDIO si scrivono SEMPRE, anche a
                #    zero: sono quelli di cui parla R26, e con la sola soglia
                #    sparivano proprio quando erano tranquilli — cioe' il caso
                #    che serve come confronto (`CODER.md` §3.10).
                sempre = any(k in t["nome"] for k in
                             ("data-loop", "pw-data", "remotix-suono", "module-rt")) \
                    or v["comm"] in ("remotix", "pipewire", "pipewire-pulse",
                                     "wireplumber", "pw-play", "pw-record")
                if sempre or cpu >= 3.0 or att >= 1.0:
                    riga["thread"].append({
                        "chi": "%s/%s[%d]" % (v["comm"], t["nome"], t["tid"]),
                        "cpu_pc": round(cpu, 1), "attesa_ms": round(att, 2),
                        "quanti": qua, "politica": t["politica"], "prio": t["rtprio"],
                        "attesa_per_quanto_us": round(att * 1000.0 / qua, 1) if qua else None})
        prima = dopo
        tprima = adesso
        campioni.append(riga)
    esiti["campioni"] = campioni
    esiti["fotografia_dopo"] = fotografia()
    esiti["carico_dopo"] = open("/proc/loadavg").read().split()[:3]

    # ── si smonta tutto, e si VERIFICA che la scena sia zitta ──────────────
    try: cli.wait(timeout=30)
    except Exception:
        cli.kill(); cli.wait()
    fcli.close()
    esiti["cliente_uscita"] = cli.returncode
    for p in (play, rif):
        if p is not None:
            try:
                p.send_signal(signal.SIGINT); p.wait(timeout=5)
            except Exception:
                try: p.kill()
                except Exception: pass
    subprocess.run(["pkill", "-u", str(UID_B), "-x", "pw-play"], capture_output=True)
    subprocess.run(["pkill", "-u", str(UID_B), "-x", "pw-record"], capture_output=True)
    carico_spegni(car)
    if a.cpu >= 0:
        # ⛔ SI RIMETTE COM'ERA, e si dichiara: una sessione lasciata su un core
        #    solo sarebbe uno stato invisibile ereditato dal giro dopo.
        esiti["allargati_di_nuovo"] = allarga(a.cpu_tutti)
    if a.nice is not None:
        esiti["nice_rimesso"] = nice_applica(0)
    if a.rt == "si":
        esiti["rt_rimesso"] = rt_rimetti()
    # ⛔ «Ho ucciso» non e' «non suona piu' nessuno»: lo dice il grafo.
    for _ in range(20):
        gg = grafo()
        if gg.get("legami_in_ingresso", 1) == 0:
            break
        time.sleep(0.3)
    esiti["scena_zittita"] = gg.get("legami_in_ingresso", None) == 0

    esiti["cliente_coda"] = open(base + ".txt", errors="replace").read()[-2500:]
    try:
        esiti["registro_audio"] = [r.strip() for r in
                                   open(os.path.join(LAV, "registro.log"), errors="replace")
                                   if "audio" in r or "R26" in r or "RTPRIO" in r
                                   or "traboccat" in r or "datagram" in r
                                   or "cwnd_left" in r][-40:]
    except Exception:
        pass
    json.dump(esiti, open(base + ".esito.json", "w"), ensure_ascii=False, indent=1)
    print("⭐ giro «%s» finito — %s.esito.json · %s blocchi nel JSONL"
          % (a.nome, base,
             sum(1 for _ in open(base + ".jsonl")) if os.path.exists(base + ".jsonl") else 0))
    return 0


def principale():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="passo", required=True)
    g = s.add_parser("giro")
    g.add_argument("--nome", required=True)
    g.add_argument("--carico", choices=["si", "no"], default="no")
    g.add_argument("--rt", choices=["si", "no", "come-sta"], default="come-sta")
    g.add_argument("--prio", type=int, default=20)
    g.add_argument("--bruciatori", type=int, default=int(os.environ.get("BRUCIATORI", "20")))
    g.add_argument("--hz", type=int, default=440)
    g.add_argument("--secondi", type=int, default=30)
    g.add_argument("--video", default="si", choices=["si", "no"],
                   help="il cliente chiede la tela, cosi il video FLUISCE")
    g.add_argument("--tela", default="1920x1080")
    g.add_argument("--codec", default="pcm", choices=["pcm", "opus"],
                   help="che cosa il cliente dichiara in audio.codec")
    g.add_argument("--nice", type=int, default=None,
                   help="rende il percorso audio piu cortese o meno (renice)")
    g.add_argument("--cpu", type=int, default=-1,
                   help="stringe tutto il percorso audio su QUESTO core (-1 = no)")
    g.add_argument("--cpu-tutti", default="0-%d" % (os.cpu_count() - 1),
                   help="a che cosa si rimette l affinita alla fine")
    s.add_parser("fotografia")
    s.add_parser("grafo")
    a = p.parse_args()
    if os.geteuid() != 0:
        print("⛔ va eseguito DA ROOT", file=sys.stderr); return 2
    os.makedirs(LAV, exist_ok=True)
    if a.passo == "fotografia":
        print(json.dumps(fotografia(), ensure_ascii=False, indent=1)); return 0
    if a.passo == "grafo":
        print(json.dumps(grafo(), ensure_ascii=False, indent=1)); return 0
    return giro(a)


if __name__ == "__main__":
    sys.exit(principale())
