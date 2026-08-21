#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-rete — IL DATAGRAM QUANDO LA RETE NON E' IDEALE.

⛔ Che cosa era aperto (`fasi/07-audio-e-appunti.md` §8): *«1024/1214 byte sono
   presi **su cavo**; il giudizio dell'utente e' su **rete di casa**, e vale per
   quella»*.

⭐ Qui ci sono due misure, e sono diverse:

   1. **`casa`** — il cliente di prova gira SUL PORTATILE, che sta in **WiFi**
      (`wlo1`, 192.168.0.3), e il server e' sulla macchina di prova, in cavo.
      ⇒ Il datagram attraversa davvero l'aria: e' la «rete di casa», non una
      simulazione.  ⛔ Nessun `tc`, nessuna regola: si guarda e basta.

   2. **`netem`** — la rete si guasta APPOSTA, a gradini, per trovare il punto
      in cui l'esperienza si rompe.  ⛔ E qui c'e' un vincolo che vale piu' della
      misura: **la regola non deve toccare ne' la sessione ssh ne' la 7730
      dell'utente**.
      ⇒ Il guasto si mette su **`lo`** della macchina di prova (il cliente gira
        dentro il contenitore, quindi il suo traffico passa di li'), con un
        `prio` a quattro bande e **due filtri `u32` sulla sola porta 7801**:
        tutto il resto del traffico locale resta nelle bande predefinite.
        ⛔ `enp7s0` — che porta l'ssh e la 7730 — **non si tocca mai**.
      ⚠ E si dichiara il prezzo di questa scelta: su `lo` la MTU e' 65536, ⇒
        **questa meta' NON rimisura «quanti byte porta un datagram»**.  Quella
        domanda la puo' chiudere solo un cliente vero su una rete vera, ed e' la
        misura 1.

⛔ IL DISINNESCO E' AUTOMATICO: prima di applicare qualunque regola si lancia un
   guardiano staccato che, dopo N secondi, toglie la disciplina **anche se
   questo copione muore o l'ssh cade**.  Una macchina lasciata con `netem` su
   `lo` e' un guasto che il prossimo banco attribuirebbe al prodotto.

Uso (dal portatile):
    python3 banchi/07-b64-rete.py casa   [--secondi 30]
    python3 banchi/07-b64-rete.py netem  [--secondi 25]
    python3 banchi/07-b64-rete.py rimetti          # ⛔ e si verifica
"""
import argparse, json, os, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7801"))
UTENTE = os.environ.get("UTENTE", "provar7")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/07-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/07-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/07-r-src")
UID_B = int(os.environ.get("UID_B", "1018"))
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
                                "84687524-93d6-4003-8cd1-1ed07aa63454/scratchpad/r7")

# ⛔ L'interfaccia che NON si tocca, scritta qui perche' si veda:
VIETATA = "enp7s0"          # ci passano l'ssh e la 7730 dell'utente
DEV = "lo"                  # ci passa solo il traffico locale, cioe' il mio

# I gradini, dal piu' mite al piu' cattivo.  ⭐ L'atteso e' scritto PRIMA.
PROFILI = [
    ("0-liscio", [], "nessun guasto: e' il denominatore, e deve essere pulito"),
    ("1-ritardo-30", ["delay", "30ms"],
     "30 ms fissi, senza jitter: arrivano tardi ma in ordine -- non deve cambiare niente"),
    ("2-jitter-2", ["delay", "20ms", "2ms", "distribution", "normal"],
     "jitter 2 ms, meno di un blocco PCM (5 ms): i sorpassi devono essere pochi"),
    ("3-jitter-5", ["delay", "20ms", "5ms", "distribution", "normal"],
     "jitter 5 ms = un blocco: e' il gradino in cui i sorpassi cominciano"),
    ("4-jitter-10", ["delay", "20ms", "10ms", "distribution", "normal"],
     "jitter 10 ms = due blocchi"),
    ("5-jitter-15", ["delay", "30ms", "15ms", "distribution", "normal"],
     "jitter 15 ms = tre blocchi: qui l ascolto deve essere gia' rotto"),
    ("6-perdita-1", ["loss", "1%"], "1 datagram su 100 perso: ~2 buchi al secondo"),
    ("7-perdita-10", ["loss", "10%"], "10 %: ~20 buchi al secondo"),
    ("8-casa-cattiva", ["delay", "40ms", "20ms", "distribution", "normal",
                        "loss", "2%"],
     "il misto che somiglia a una casa col WiFi lontano"),
]


def rem(comando, tetto=120):
    """⛔ Niente redirezione ATTORNO a ssh: la richiesta di sudo va sullo stderr
       e un redirect la mangerebbe — il comando resterebbe appeso in silenzio."""
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=120):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando), tetto)


def qdisc():
    return root("/usr/sbin/tc qdisc show dev %s" % DEV)[1].strip()


def rimetti(dillo=True):
    """⛔ E si VERIFICA: «ho tolto» e «non c'e' piu'» sono due fatti diversi."""
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q
    if dillo:
        print("   %s la disciplina di «%s» adesso e': %s"
              % ("OK " if ok else "NO ", DEV, q or "(nessuna)"))
        # ⛔ E si dichiara che l'interfaccia vietata non e' MAI stata toccata.
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s" % VIETATA)[1].split("\n")[0]))
    return ok


def guasta(regole):
    """Il guasto, e SOLO sul mio traffico."""
    if not regole:
        rimetti(False)
        return True, "(nessun guasto)"
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem %s"
        % (DEV, " ".join(regole)),
        # ⛔ DUE filtri, e la porta e' la MIA: uno per i datagram che scendono
        #    (sport 7801) e uno per quel che risale (dport 7801).
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4" % (DEV, PORTA),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4" % (DEV, PORTA),
    ]
    # (il guardiano si arma UNA volta sola, in `principale`: vedi la nota li')
    for c in passi:
        rc, out, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc ha rifiutato «%s»: %s" % (c[-60:], err[:200])
    return True, qdisc()


def tono_accendi():
    """⛔ Il tono deve suonare DENTRO la sessione, o il giudice misura silenzio
       e il banco riferisce «rms 0» come se fosse un guasto della rete.
       ⚠ E' successo al primo giro di «casa»: 5993 datagram perfetti e rms 0,0.
       ⭐ E «acceso» non e' «suona»: si controlla che il grafo abbia i legami."""
    # ⛔ IL TONO SI RIPETE IN UN CICLO, e la prima stesura no.
    #   Il file dura ~55 s; il giro dei profili ne dura trecento.  Dal secondo
    #   profilo in poi il giudice leggeva rms 0,0 e purezza nulla -- cioe'
    #   "silenzio" -- accanto a contatori di trasporto perfetti.  Il numero
    #   della RETE restava buono, ma la meta' che ASCOLTA era sparita senza
    #   dirlo, che e' precisamente la trappola 1 di questa fase.
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus "
         "sh -c 'while :; do pw-play --target remotix %s/tono-440.wav; done' "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, UID_B, LAV))
    for _ in range(25):
        time.sleep(0.4)
        rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/07-b64-scena.py grafo"
                          % (UTENTE, UID_B, LAV, ALB))
        try:
            if json.loads(out).get("legami_in_ingresso", 0) > 0:
                return True
        except Exception:
            pass
    return False


def tono_spegni():
    # ⛔ si uccide anche il CICLO, non solo il lettore: uccidere pw-play
    #   dentro un `while :` lo fa ripartire subito, ed e' la stessa forma del
    #   difetto di 07-b43 (`kill` sull'involucro invece che sul lettore).
    root("pkill -u %d -f 'while :; do pw-play'; pkill -u %d -x pw-play; true"
         % (UID_B, UID_B))


def cliente(nome, dove, secondi):
    """dove = 'portatile' (WiFi vero) oppure 'contenitore' (loopback + netem)."""
    j = os.path.join(FUORI, nome + ".jsonl")
    t = os.path.join(FUORI, nome + ".txt")
    for f in (j, t, os.path.join(FUORI, nome + ".segnale")):
        try: os.remove(f)
        except Exception: pass
    if dove == "portatile":
        pf = os.path.join(FUORI, ".parola")
        if not os.path.exists(pf):
            print("⛔ manca %s (0600, con la parola di %s): NON la metto in argv (D12)"
                  % (pf, UTENTE))
            return None
        cmd = [os.environ.get("PY", "python3"), "-u",
               os.path.join(QUI, "01-b3-cliente.py"),
               "--indirizzo", IND, "--porta", str(PORTA), "--utente", UTENTE,
               "--parola-file", pf, "--audio-codec", "pcm",
               "--audio-scrivi", j, "--segnale", os.path.join(FUORI, nome + ".segnale"),
               "--resta", str(secondi)]
        p = subprocess.run(cmd, capture_output=True, timeout=secondi + 120)
        uscita = p.stdout.decode("utf-8", "replace")
        open(t, "w").write(uscita + p.stderr.decode("utf-8", "replace"))
    else:
        dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
                  "--utente %s --parola-file %s/parola --audio-codec pcm "
                  "--audio-scrivi %s/rete-%s.jsonl --resta %d"
                  % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, DENTRO_LAV,
                     nome, secondi))
        rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                            secondi + 180)
        uscita = out + err
        open(t, "w").write(uscita)
        # si riporta il JSONL
        subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                       "cat %s/rete-%s.jsonl\" > %s"
                       % (MACCHINA, PAROLA_SUDO, LAV, nome, j), shell=True)
    conti = {}
    for r in uscita.splitlines():
        if "[audio] ricevuti" in r or "[audio] scartati" in r:
            conti[r.strip()[:9]] = r.strip()
    return {"uscita_coda": uscita[-1200:], "conti": conti,
            "jsonl": j, "byte_jsonl": os.path.getsize(j) if os.path.exists(j) else 0}


def giudica(nome):
    j = os.path.join(FUORI, nome + ".jsonl")
    if not os.path.exists(j) or os.path.getsize(j) == 0:
        return {"esito": "NIENTE DA GIUDICARE — nessun blocco"}
    p = subprocess.run(["python3", os.path.join(QUI, "07-b64-orecchio.py"), j,
                        "--hz", "440"], capture_output=True)
    try:
        d = json.loads(p.stdout.decode())["nostro"]
    except Exception as e:
        return {"esito": "il giudice non ha risposto: %s" % e}
    s = d["scoppiettii"]
    return {"blocchi": d["blocchi"], "resa_campioni": d.get("resa_campioni"),
            "buchi_istante": d["buchi_istante"], "scoppiettii": s["scoppiettii"],
            "scoppiettii_al_s": s["al_secondo"], "tono": d["tono"]}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["casa", "netem", "rimetti", "stato"])
    p.add_argument("--secondi", type=int, default=25)
    p.add_argument("--solo", default="", help="un profilo solo, per nome")
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    if a.passo in ("rimetti", "stato"):
        print("== la rete della macchina di prova")
        return 0 if rimetti() else 2

    if a.passo == "casa":
        print("== 1 · LA RETE DI CASA VERA — il cliente gira sul portatile, in WiFi")
        print("   --  portatile 192.168.0.3 (wlo1) → server %s:%d (cavo)" % (IND, PORTA))
        print("   ⛔ nessuna regola di tc: non si simula niente")
        if not tono_accendi():
            print("   NO  il tono NON sta suonando dentro la sessione: mi fermo,"
                  " invece di misurare silenzio e chiamarlo rete")
            tono_spegni(); return 2
        print("   OK  il tono suona: il grafo ha i legami in ingresso al sink")
        try:
            c = cliente("casa", "portatile", a.secondi)
        finally:
            tono_spegni()
        if c is None:
            return 2
        for r in c["conti"].values():
            print("   ", r)
        print("   ", json.dumps(giudica("casa"), ensure_ascii=False))
        return 0

    print("== 2 · LA RETE GUASTATA APPOSTA — netem su «%s», solo porta %d" % (DEV, PORTA))
    print("   ⛔ «%s» (ssh + 7730 dell utente) NON si tocca" % VIETATA)
    prima = qdisc()
    print("   --  «%s» prima: %s" % (DEV, prima or "(nessuna)"))
    # ⛔⛔ IL GUARDIANO SI ARMA UNA VOLTA SOLA, E PER TUTTO IL GIRO.
    #
    #     La prima stesura ne armava uno **per profilo**, ciascuno con la sua
    #     attesa: il guardiano del primo profilo sarebbe scattato **in mezzo al
    #     terzo**, togliendo il netem senza dirlo.  ⇒ Avrei misurato una rete
    #     sana credendola guasta, e scritto «il 10 % di perdita non si sente».
    #     ⚠ E' la forma peggiore di difetto di banco: fa apparire buono il
    #     prodotto.  Trovato rileggendo, prima di girare.
    totale = (a.secondi + 120) * len(PROFILI) + 300
    root("pkill -f 'tc qdisc del dev %s root'; true" % DEV)
    root("setsid nohup sh -c 'sleep %d; /usr/sbin/tc qdisc del dev %s root' "
         ">/dev/null 2>&1 & echo guardiano-acceso-per-%ds" % (totale, DEV, totale))
    print("   OK  guardiano armato: fra %d s la rete torna com era ANCHE se muoio" % totale)
    esiti = []
    if not tono_accendi():
        print("   NO  il tono non suona: non misuro")
        tono_spegni(); rimetti(); return 2
    print("   OK  il tono suona dentro la sessione")
    try:
        for nome, regole, atteso in PROFILI:
            if a.solo and a.solo not in nome:
                continue
            print("\n-- %s · %s" % (nome, atteso))
            ok, q = guasta(regole)
            if not ok:
                print("   ", q); break
            # ⛔ M3 si riverifica a OGNI profilo.  "Il tono suonava
            #   all'inizio" non e' "il tono sta suonando adesso".
            rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/"
                              "07-b64-scena.py grafo" % (UTENTE, UID_B, LAV, ALB))
            try:
                leg = json.loads(out).get("legami_in_ingresso", 0)
            except Exception:
                leg = -1
            print("    M3: legami in ingresso al sink = %s" % leg)
            if leg <= 0:
                print("   NO  il tono non suona piu': NON giudico questo profilo")
                esiti.append({"profilo": nome, "esito": "NIENTE DA GIUDICARE, il tono taceva"})
                continue
            print("    tc:", " ".join(q.split("\n")[:2])[:160])
            c = cliente(nome, "contenitore", a.secondi)
            g = giudica(nome)
            for r in (c or {}).get("conti", {}).values():
                print("   ", r)
            print("    giudizio:", json.dumps(g, ensure_ascii=False))
            esiti.append({"profilo": nome, "regole": regole, "atteso": atteso,
                          "conti": (c or {}).get("conti"), "giudizio": g})
    finally:
        tono_spegni()
        print("\n== ⛔ LA RETE SI RIMETTE COM'ERA")
        root("pkill -f 'tc qdisc del dev %s root'; true" % DEV)
        rimetti()
    json.dump(esiti, open(os.path.join(FUORI, "rete-esiti.json"), "w"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
