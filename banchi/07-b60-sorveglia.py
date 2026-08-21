#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b60 — SORVEGLIA UNA SESSIONE VERA, tutti gli anelli sulla stessa riga.

⛔ Nasce da un difetto sentito dall'utente e da nessun banco: «su Windows,
   a un certo punto l'audio e' a scatti» (21 agosto 2026, sera).

⚠ Perche' non basta il registro del server:
   · l'anello di CHI ASCOLTA c'e' gia' — la pagina manda `/diario` ogni 5 s, ed
     e' la lezione di LEZIONI.md §2.7;
   · ⛔⭐ E QUI L'INTESTAZIONE DI QUESTO FILE DICEVA IL FALSO, corretta subito
     dopo il primo giro: «l'anello di chi produce non ha un contatore vivo».
     ⚠ Ce l'ha — il figlio scrive «audio: N blocchi spediti, 0 persi, X
     fotogrammi in attesa nell'anello» **ogni secondo** — e l'avevo dedotto da
     un `grep` su `suono_conti()` invece di guardare il registro di una
     sessione viva.  ⇒ La lezione e' quella di sempre, applicata a me: si
     guarda la sessione, non il codice che si crede di ricordare.
   · ⛔ Quel che davvero MANCA e' il tempo dei THREAD, e li' stanno i due
     sospetti dell'audio a scatti:
       1. il `data-loop` di PipeWire che NON ottiene SCHED_FIFO (R26 di v1: con
          `RLIMIT_RTPRIO` a zero la richiesta viene negata **in silenzio**);
       2. il codificatore video che si prende un core mentre il thread audio
          aspetta un quanto di pochi millisecondi.
   ⇒ Tutt'e due si vedono SOLO guardando i thread vivi, uno per uno.

⛔ E non si tocca il prodotto mentre l'utente misura: questa sonda LEGGE
   `/proc` e il registro, non inietta niente e non riavvia niente.

⭐ CHE COSA HA TROVATO, il primo giro — 21 agosto 2026, Chrome su Windows, ~4 minuti:
   · l'audio a scatti NON si e' ripresentato, e l'utente l'ha attribuito al suo
     PC: la sorveglianza e' servita a ESCLUDERE REMOTIX con i numeri;
   · produttore 50 blocchi/s, 0 persi · pagina 10 621 ricevuti, 10 617 suonati,
     4 buchi tutti dell'avvio · video 5 334 → 5 334, zero tardivi · zero errori
     UDP del kernel;
   · ⛔ e la coda della pagina sta a **239-270 ms**, cioe' esattamente
     `AUDIO_CUSCINO_MS`: e' li' che nascono i 400 ms fra quel che si vede e
     quel che si sente, ed e' il difetto aperto della fase 7 (§8).

⛔⭐ E R26 ADESSO HA UNA RISPOSTA -- 21 agosto 2026, sera, banchi 07-b64:

   1. NESSUN thread del percorso audio ha SCHED_FIFO, ne' nei demoni della
      sessione ne' dentro il figlio -- e nemmeno un `nice` negativo: sono tutti
      `normale`, `nice 0`.  Questa sonda lo diceva gia'.
   2. Ma il MOTIVO non era quello scritto qui sotto.  `LimitRTPRIO=20`
      nell'unita' ARRIVA: il figlio ha `RLIMIT_RTPRIO = 20`.  Non basta lo
      stesso, per due ragioni indipendenti, tutt'e due misurate:
        a. su questo kernel (7.0, NIC-OS) `SCHED_FIFO` e' rifiutato a
           QUALUNQUE processo che stia in un cgroup diverso dalla radice --
           cioe' a ogni processo che systemd governa.  `chrt -f 10 /bin/true`
           fallisce DA ROOT in una slice e riesce nella radice: e'
           `CONFIG_RT_GROUP_SCHED` con cgroup v2 unificato;
        b. e comunque `rtkit-daemon` e' spento e il gruppo `pipewire` e' vuoto,
           quindi i demoni della sessione (`RLIMIT_RTPRIO = 0`) non potrebbero
           chiederlo in nessun caso.
   3. Percio' la riga che il prodotto scrive -- "priorita' di tempo reale
      concessa dall'unita': RLIMIT_RTPRIO = 20 (R26)" -- e' vera del rlimit e
      FALSA dell'effetto: nessuno la usa e nessuno potrebbe.
   4. Che differenza fa: su venti core, NESSUNA (il `data-loop` aspetta 6 us su
      un quanto di 5,33 ms).  Su un core solo col codificatore -- che e' la
      frase di R26 alla lettera -- ~10,5 scoppiettii al secondo, e la cortesia
      li toglie: `nice -11` -> ~2,9/s, `nice -20` -> 0,27/s e purezza 1,000.

⛔ E QUEL CHE QUESTA SONDA NON VEDEVA: i contatori restano TUTTI VERDI
   mentre l'audio e' rotto -- 0 persi, 0 traboccati, resa dei campioni 1,000.
   Il difetto sta nei CAMPIONI, e lo sente solo `07-b64-orecchio.py`.

Uso (dal portatile):  python3 banchi/07-b60-sorveglia.py [--porta 7730] [--secondi 300]
"""
import argparse, os, re, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA = os.environ.get("PAROLA", "nicfio")

# ── il sorvegliante gira SULLA MACCHINA DI PROVA: /proc e' li' ──────────────
REMOTO = r'''
import os, sys, time, glob, re

PORTA = int(sys.argv[1]); LAV = sys.argv[2]; SECONDI = int(sys.argv[3])
HZ = os.sysconf("SC_CLK_TCK")
OUT = open("/tmp/07-b60-sorveglianza.log", "w", buffering=1)
def dico(s):
    OUT.write(s + "\n")

def pid_unita():
    for r in os.popen("systemctl show -p MainPID --value remotix-%d.service" % PORTA):
        r = r.strip()
        if r.isdigit() and r != "0":
            return int(r)
    return 0

def albero(radice):
    """il server e TUTTI i suoi discendenti: il figlio della sessione sta li'."""
    vivi, davanti = [], [radice]
    while davanti:
        p = davanti.pop()
        vivi.append(p)
        try:
            for f in open("/proc/%d/task/%d/children" % (p, p)).read().split():
                davanti.append(int(f))
        except Exception:
            pass
        # ⚠ i figli veri stanno in tutti i task, non solo nel primo
        try:
            for t in os.listdir("/proc/%d/task" % p):
                try:
                    for f in open("/proc/%d/task/%s/children" % (p, t)).read().split():
                        if int(f) not in vivi and int(f) not in davanti:
                            davanti.append(int(f))
                except Exception:
                    pass
        except Exception:
            pass
    return vivi

def processi_utente(uid):
    """⛔ E NON BASTA L'ALBERO DEL SERVER: il demone PipeWire della sessione sta
       sotto `user@%d.service`, non sotto di noi — e il `data-loop` che raccoglie
       i campioni e' proprio li' dentro.  ⇒ Si prendono anche tutti i processi
       dell'utente della sessione."""
    fuori = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            if os.stat("/proc/" + d).st_uid == uid:
                fuori.append(int(d))
        except Exception:
            pass
    return fuori

def thread_stat(pid, tid):
    """(nome, utime+stime, rt_priority, policy, ATTESA IN CODA, quanti).

    ⭐ L'ATTESA IN CODA e' l'aggiunta del 21 agosto sera, e senza di lei
       questa sonda diceva soltanto CHE COSA e' un thread, non SE ha avuto la
       CPU quando gli serviva.  Sta in `schedstat`, secondo campo, in
       nanosecondi: e' il tempo passato pronto-ma-non-in-esecuzione.  Diviso
       per i quanti da' l'unico numero confrontabile col quanto di PipeWire
       (5,33 ms a 256 fotogrammi)."""
    try:
        d = open("/proc/%d/task/%d/stat" % (pid, tid)).read()
    except Exception:
        return None
    # ⛔ il nome sta fra parentesi e PUO' contenere spazi: si taglia sull'ultima
    a = d.index("("); b = d.rindex(")")
    nome = d[a+1:b]
    campi = d[b+2:].split()
    # campi[0] e' `state`, cioe' il 3o del formato: utime=14 → indice 11
    utime = int(campi[11]); stime = int(campi[12])
    nice = int(campi[16])
    rtprio = int(campi[37]); policy = int(campi[38])
    attesa = quanti = 0
    try:
        sc = open("/proc/%d/task/%d/schedstat" % (pid, tid)).read().split()
        attesa, quanti = int(sc[1]), int(sc[2])
    except Exception:
        pass
    return nome, utime + stime, rtprio, policy, attesa, quanti, nice

POLITICA = {0: "normale", 1: "FIFO", 2: "RR", 3: "batch", 5: "idle", 6: "deadline"}

def udp_snmp():
    for r in open("/proc/net/snmp"):
        if r.startswith("Udp:") and not r.split()[1].isdigit():
            testa = r.split()[1:]
        elif r.startswith("Udp:"):
            return dict(zip(testa, [int(x) for x in r.split()[1:]]))
    return {}

prima = {}
prima_udp = udp_snmp()
prima_t = time.time()
inizio = prima_t
pid = pid_unita()
dico("# sorveglianza avviata — server pid %d, porta %d" % (pid, PORTA))
sessione_vista = False

while time.time() - inizio < SECONDI:
    time.sleep(1.0)
    ora = time.strftime("%H:%M:%S")
    adesso = time.time()
    dt = adesso - prima_t
    if pid == 0 or not os.path.exists("/proc/%d" % pid):
        pid = pid_unita()
        if pid == 0:
            dico("%s ⛔ IL SERVER NON C'E' PIU'" % ora); prima_t = adesso; continue
    caldi, audiofili, rt_negati, dopo = [], [], [], {}
    procs = albero(pid)
    for q in processi_utente(1001):
        if q not in procs:
            procs.append(q)
    for p in procs:
        try:
            tids = os.listdir("/proc/%d/task" % p)
        except Exception:
            continue
        try:
            comm = open("/proc/%d/comm" % p).read().strip()
        except Exception:
            comm = "?"
        for t in tids:
            t = int(t)
            s = thread_stat(p, t)
            if not s:
                continue
            nome, tick, rtprio, policy, attesa, quanti, nice = s
            dopo[(p, t)] = (tick, attesa, quanti)
            v = prima.get((p, t))
            if v is None:
                continue
            uso = (tick - v[0]) / HZ / dt * 100.0
            att_ms = (attesa - v[1]) / 1e6
            qn = quanti - v[2]
            etichetta = "%s/%s[%d]" % (comm, nome, t)
            # ⛔ I thread del percorso audio si scrivono SEMPRE, anche a
            #   zero: sono quelli di cui parla R26, e con la sola soglia
            #   sparivano proprio quando erano tranquilli -- cioe' nel caso che
            #   serve come confronto (`CODER.md` 3.10).
            audio = ("data-loop" in nome or "remotix-suono" in nome
                     or comm in ("pipewire", "pipewire-pulse", "wireplumber"))
            if uso >= 8.0 or (audio and "data-loop" in nome):
                riga = ("%s %.0f%% att %.1fms/%d=%.0fus%s"
                        % (etichetta, uso, att_ms, qn,
                           att_ms * 1000.0 / qn if qn else 0.0,
                           "" if policy == 0 else " " + POLITICA.get(policy, str(policy))
                           + str(rtprio)))
                # I `data-loop` stanno in una lista LORO: mescolati agli altri
                # e tagliati a sei, il taglio li buttava fuori proprio quando
                # erano tranquilli — e sono la ragione per cui questa sonda
                # esiste.
                (audiofili if ("data-loop" in nome) else caldi).append(riga)
            # ⛔ R26: il thread dei dati di PipeWire DEVE essere in tempo reale
            if ("pw-data" in nome or "data-loop" in nome or "pw-rt" in nome) and policy == 0:
                rt_negati.append(etichetta)
    prima = dopo
    prima_t = adesso
    u = udp_snmp()
    d_udp = []
    for k in ("InErrors", "RcvbufErrors", "SndbufErrors", "NoPorts", "InCsumErrors"):
        if k in u and u[k] - prima_udp.get(k, 0) > 0:
            d_udp.append("%s +%d" % (k, u[k] - prima_udp.get(k, 0)))
    prima_udp = u
    carico = open("/proc/loadavg").read().split()[0]
    figli = len([p for p in procs if p != pid])
    if figli and not sessione_vista:
        sessione_vista = True
        dico("%s ⭐ SESSIONE APERTA — %d processi sotto il server" % (ora, figli))
        # ⛔ La fotografia di R26, presa UNA VOLTA e per intero: chi ha chiesto
        #    il tempo reale e chi non ce l'ha.  ⚠ Un `data-loop` a politica
        #    «normale» non da' un errore: da' audio a scatti quando il desktop
        #    lavora, e a desktop fermo non si riproduce.
        for p in procs:
            try:
                comm = open("/proc/%d/comm" % p).read().strip()
                tids = os.listdir("/proc/%d/task" % p)
            except Exception:
                continue
            for t in tids:
                s2 = thread_stat(p, int(t))
                if not s2:
                    continue
                nome, _, rtprio, policy, _a, _q, nice2 = s2
                if ("pw-" in nome or "data-loop" in nome or "audio" in nome.lower()
                        or "opus" in nome.lower() or "pipewire" in comm):
                    dico("%s   R26 %s/%s[%s] → %s%d nice %d" % (ora, comm, nome, t,
                         POLITICA.get(policy, str(policy)), rtprio, nice2))
        try:
            lim = open("/proc/%d/limits" % pid).read()
            for r in lim.splitlines():
                if "realtime priority" in r.lower() or "nice" in r.lower():
                    dico("%s   LIMITE %s" % (ora, " ".join(r.split())))
        except Exception:
            pass
    if not figli and sessione_vista:
        sessione_vista = False
        dico("%s ⛔ SESSIONE CHIUSA" % ora)
    pezzi = ["CPU carico %s" % carico]
    if audiofili:
        pezzi.append("AUDIO " + " · ".join(sorted(audiofili)))
    if caldi:
        pezzi.append("· ".join(sorted(caldi, reverse=True)[:6]))
    if d_udp:
        pezzi.append("⛔ UDP " + " ".join(d_udp))
    if rt_negati:
        # ⚠ La frase e' cambiata il 21 agosto sera: NON e' "manca
        #   LimitRTPRIO nell'unita'".  Il rlimit c'e'; e' il kernel che rifiuta
        #   SCHED_FIFO fuori dal cgroup radice (07-b64).  Chi legge questa riga
        #   non deve andare a cercare una riga di unita' che c'e' gia'.
        pezzi.append("SENZA TEMPO REALE (atteso su questo kernel — vedi 07-b64): "
                     + " ".join(sorted(set(rt_negati))))
    dico("%s CPU %s" % (ora, "  ".join(pezzi[1:]) if len(pezzi) > 1 else "carico " + carico))
OUT.write("# fine\n")
'''

def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=7730)
    p.add_argument("--lav", default="/media/REMOTIX/tmp/07-appunti")
    p.add_argument("--secondi", type=int, default=420)
    a = p.parse_args()

    # ⛔ SI ACCENDE PRIMA di dire «vai»: un difetto che dura trenta secondi non
    #    si riprende (LEZIONI.md §2.7).
    copione = "/tmp/07-b60-remoto.py"
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                    "cat > %s" % copione], input=REMOTO.encode(), check=True)
    # ⛔⛔ NIENTE `</dev/null`, ed e' la trappola gia' pagata due volte in
    #    `07-b41`: quel redirect vale per `sudo`, che allora NON legge piu' la
    #    parola d'ordine dal `printf` — «sudo: no password was provided», e il
    #    sorvegliante non parte.  ⚠ La faccia del difetto e' «acceso» stampato
    #    da un comando che non ha acceso niente.
    comando = ("printf '%%s\\n' '%s' | sudo -S -p '' setsid python3 %s %d %s %d "
               ">/tmp/07-b60-avvio.log 2>&1 & echo acceso"
               % (PAROLA, copione, a.porta, a.lav, a.secondi))
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando], check=True)
    print("⭐ sorveglianza accesa su %s — /tmp/07-b60-sorveglianza.log" % MACCHINA)

if __name__ == "__main__":
    principale()
