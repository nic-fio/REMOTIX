#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b65 — QUANDO IL TUBO E' STRETTO, CHI PAGA: L'AUDIO O IL VIDEO?

⛔ Da dove nasce.  `[M]` di A1, da una sessione vera: **2 200 datagram scartati
   dal server**, la pagina ha perso **684 blocchi = 13,7 s di audio (9,43 %)**,
   e in una finestra di 25 s il **47 %**.  ⛔⛔ Nella STESSA sessione gli stream
   del video non hanno perso niente: 5 334 consegnati, 5 334 dipinti.
   ⇒ La sproporzione non e' la rete: e' **come trattiamo i datagram rispetto
   agli stream** dentro il nostro trasporto.

⭐⭐ E LA PRIMA COSA CHE QUESTO BANCO HA DOVUTO IMPARARE E' CHE IL DIFETTO NON
    SI RIPRODUCE SU UN TUBO LARGO.  `[M]` 21 agosto 2026, loopback, video vero
    (1 279 fotogrammi 1920x1080 in 40 s) e audio PCM a 1,56 Mbit/s:
    **8 006 spediti, 0 buttati, 0 rifiutati, 0 rimandati**.  ⇒ Su un tubo senza
    fondo il pacer non chiude mai e nessuno cede.  Il difetto vive **solo dove
    la banda non basta**, ed e' li' che bisogna andare a costruirlo.

⛔ LE QUATTRO PORTE DA CUI UN DATAGRAM PUO' NON USCIRE, in ordine, e ognuna ha
   un contatore suo (`src/webtransport.c`):

   | # | dove | contatore | chi decide |
   |---|---|---|---|
   | 1 | `dgram_accoda`, coda piena (8 posti) | `audio_buttati` | **noi**: il piu' vecchio esce per far posto al nuovo |
   | 2 | `dgram_scrivi_uno`, `dgram_rimando_ts == ts` | — | **noi**: un solo tentativo per passata |
   | 3 | `writev_datagram` torna 0 | `audio_rimandati` | **il pacer / la finestra di ngtcp2** |
   | 4 | 4096 rimandi di fila | `audio_rifiutati` | **noi**, per non tenerlo in eterno |

⛔⛔ E L'ASIMMETRIA STA NELLA FORMA, non in una politica scritta da nessuna
    parte: il video viaggia su **stream** — se non passa adesso, ngtcp2 lo
    tiene, lo divide e lo ritrasmette, quindi puo' solo arrivare **tardi**;
    l'audio viaggia su **datagram**, che §6.3 vieta di ritrasmettere e che
    hanno una coda di otto posti che si sovrascrive.  ⇒ Ogni scarsita' di
    occasioni di trasmissione la paga **per intero l'audio**, e nessuno l'ha
    mai deciso: e' quel che succede se non si decide.

⭐ Questo banco costruisce la scarsita' con `tc netem rate` (piu' un ritardo,
   o la finestra di congestione non ha modo di contare) e misura, a ogni
   gradino: quanto audio parte, quanto se ne butta e **per quale delle quattro
   porte**, quanti fotogrammi arrivano lo stesso, e come SUONA quel che resta.

⛔ LA RETE SI TOCCA CON LA STESSA DISCIPLINA DI `07-b64-rete.py`:
   solo `lo`, solo la porta 7801, `enp7s0` (ssh e 7730 dell'utente) mai; e un
   guardiano staccato rimette la disciplina anche se questo copione muore.

⛔⛔⛔ CHE COSA HA TROVATO — 21 agosto 2026, sera, e la causa NON e' quella che
      il mandato sospettava.  La scena e' sempre la stessa: sessione di
      `provar7` sulla 7801, tono 440 Hz nel sink, `04-b30-scena` sul monitor
      catturato, cliente di prova dentro il contenitore, `netem` su `lo`
      ristretto alla sola porta 7801.  Trenta secondi per gradino.

  1 · IL TUBO LARGO NON PERDE NIENTE.  Senza limite e a 15 Mbit/s:
      **8 006 / 6 002 blocchi spediti, 0 buttati, 0 rifiutati**, purezza 1,000.
      ⇒ Il difetto non esiste finche' la banda avanza.

  2 · ⛔ A 3 Mbit/s CON IL DESKTOP CHE SI MUOVE l'audio e' distrutto:
      **397 blocchi spediti su ~6 000, 6 061 rifiutati** (PCM), purezza 0,18.

  3 · ⭐⭐ MA A 3 Mbit/s CON IL DESKTOP FERMO l'audio e' PERFETTO:
      **6 009 spediti, 3 rifiutati, 0 buttati**, resa 0,9995, purezza **1,000**,
      e sul filo passano 1,82 Mbit/s su 3 disponibili.
      ⇒ **Non e' la banda: e' il video.**  Stessa banda, stesso audio, due
        esiti opposti — e a cambiare c'e' una cosa sola.

  4 · ⭐⭐ E NON E' NEMMENO QUANTO COSTA L'AUDIO.  Stesso gradino, stesso
      desktop che si muove, ma **Opus** al posto del PCM — cioe' **1/32** della
      banda (48 kbit/s contro 1,56 Mbit/s): **624 blocchi su 1 500, 896
      rifiutati, il 58 % perso lo stesso**.  ⇒ Ridurre quel che l'audio chiede
      non lo salva: il posto non c'e' comunque.

  5 · ⛔⛔⛔ LA CAUSA, ED E' UNA SPIRALE CHE IL CODICE AVEVA GIA' NOMINATO.
      In tutti i giri stretti il video consegna **solo fotogrammi CHIAVE**
      (144/144, 148/148, 107/107, 138/138, 149/149) contro 2 chiavi su 1 019 a
      15 Mbit.  Il registro conta **806 richieste di chiave (§5.2)** e **173
      righe «la CHIAVE N tiene ancora ~60 000 byte in coda e §5.2 vieta di
      abbandonarla: si ASPETTA»**.
        · una chiave da 60 KB su un tubo da 3 Mbit occupa la finestra per
          **160 ms**;
        · `WT_CHIAVE_RICHIESTA_MS` ne concede una **ogni 150 ms**;
        · in quei 160 ms nascono 32 blocchi PCM (8 di Opus) e ognuno trova
          `cwnd_left = 0`.
      ⇒ Non e' una politica che fa cedere l'audio al video: e' che il video,
        quando la banda manca, **chiede di piu'** (§5.2), e il datagram — che
        non si spezza, non si ritrasmette e non puo' aspettare — e' l'unico che
        puo' pagare.  ⚠ Il commento di `webtransport.c` alla riga ~728 la
        chiamava «la spirale di §5.2» come ipotesi: qui e' misurata.

  6 · ⛔ E QUATTRO VARIANTI DEL TRASPORTO NON CAMBIANO NIENTE, provate una per
      una sul solo albero di costruzione, allo stesso gradino (blocchi
      spediti): **base 397 · senza il ritorno anticipato per passata 278 ·
      senza `PADDING` 406 · senza `MORE` (pacchetto suo) 514 · con la RISERVA
      (il video cede la passata quando ci sono datagram in coda) 371**.
      ⇒ ⭐ Il perche' e' la parte che vale: **la finestra non e' contesa, e'
        gia' piena** di byte di video in volo.  Rinunciare a scrivere altro
        video non libera quel che e' gia' partito e non e' ancora stato
        riscontrato.  Nessuna furbizia nell'ordine di scrittura puo' fabbricare
        posto che non c'e'.

Uso (dal portatile):
    python3 banchi/07-b65-datagram.py sonda            # i gradini, uno per uno
    python3 banchi/07-b65-datagram.py sonda --scena no # ⭐ il controllo del punto 3
    python3 banchi/07-b65-datagram.py rimetti          # ⛔ e si verifica
"""
import argparse, json, os, re, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7801"))
UTENTE = os.environ.get("UTENTE", "provar7")
UID_B = int(os.environ.get("UID_B", "1018"))
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/07-r-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/07-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/07-r")
QUI = os.path.dirname(os.path.abspath(__file__))
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
                                "84687524-93d6-4003-8cd1-1ed07aa63454/scratchpad/r7")

VIETATA = "enp7s0"   # ci passano l'ssh e la 7730 dell'utente
DEV = "lo"

# ⭐ I gradini.  La scena costa `[M]` 1,56 Mbit/s di audio PCM + ~0,5 di video:
#    il primo gradino sta sopra la somma, l'ultimo molto sotto.  ⛔ E c'e'
#    sempre un ritardo: senza RTT la finestra di congestione non ha modo di
#    riempirsi, e il pacer non si accorge di niente.
GRADINI = [
    ("g0-largo",   [],                                    "nessun limite: il denominatore"),
    ("g1-15mbit",  ["delay", "15ms", "rate", "15mbit"],   "banda tripla del bisogno: non deve cedere nessuno"),
    ("g2-3mbit",   ["delay", "15ms", "rate", "3mbit"],    "poco sopra la somma (2,1): il primo gradino stretto"),
    ("g3-2mbit",   ["delay", "15ms", "rate", "2mbit"],    "sotto la somma: qualcuno DEVE cedere, e si guarda chi"),
    ("g4-1mbit",   ["delay", "15ms", "rate", "1mbit"],    "meta della somma"),
    ("g5-500kbit", ["delay", "15ms", "rate", "500kbit"],  "un terzo del solo audio: il caso disperato"),
]


def rem(comando, tetto=300):
    """⛔ Niente redirezione ATTORNO a ssh: la richiesta di sudo va sullo stderr."""
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=300):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando), tetto)


def qdisc():
    return root("/usr/sbin/tc qdisc show dev %s" % DEV)[1].strip()


def rimetti(dillo=True):
    root("pkill -f 'tc qdisc del dev %s root'; true" % DEV)
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q and "tbf" not in q
    if dillo:
        print("   %s «%s» adesso e': %s" % ("OK " if ok else "NO ", DEV, q or "(nessuna)"))
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s" % VIETATA)[1].split("\n")[0]))
    return ok


def stringi(regole):
    if not regole:
        root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
        return True, "(nessun limite)"
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem %s"
        % (DEV, " ".join(regole)),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4" % (DEV, PORTA),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4" % (DEV, PORTA),
    ]
    for c in passi:
        rc, _, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc ha rifiutato: %s" % err[:200]
    return True, qdisc()


# ── ⛔ PRIMA DI TUTTO SI APRE UNA SESSIONE, o non c e niente da suonare ────
#
# `[M]` 21 agosto 2026, e il banco si e' fermato da solo dicendolo: il sink
# «remotix» lo crea il FIGLIO, e il figlio nasce quando un cliente entra.  Su un
# server appena riacceso il sink non esiste, `pw-play --target remotix` non si
# lega a niente e il tono tace.  ⇒ Si apre una sessione corta apposta: il palco
# e il sink le sopravvivono (invariante I4), e da li' in poi c e' dove suonare.
# ⚠ Serve anche alla SCENA, che vuole il nome del monitor dal registro.
def innesca_sessione(secondi=8):
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--adatta 1920x1080 --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 180)
    return "SESSIONE" in (out + err)


# ── il tono, che deve suonare per TUTTO il giro ────────────────────────────
def tono_fabbrica(hz=440, secondi=70, ampiezza=0.5):
    """⛔ Il tono si fabbrica QUI se manca, e l'ampiezza e' NOTA: l'RMS atteso
       e' un conto (A/sqrt2), non una stima.  ⚠ E il file dev'essere leggibile
       dall'utente della sessione, che non e' root."""
    f = "%s/tono-%d.wav" % (LAV, hz)
    rc, out, _ = root("test -s %s && stat -c %%s %s || echo 0" % (f, f))
    if out.strip().isdigit() and int(out.strip()) > 48000 * secondi * 2:
        return f
    root("mkdir -p %s && chmod 755 %s" % (LAV, LAV))
    copione = (
        "import math,struct,wave;"
        "w=wave.open('%s','wb');w.setnchannels(2);w.setsampwidth(2);"
        "w.setframerate(48000);d=bytearray();"
        "[d.extend(struct.pack('<hh',v,v)) for v in "
        "[int(%f*math.sin(2*math.pi*%d*n/48000)*32767) for n in range(48000*%d)]];"
        "w.writeframes(bytes(d));w.close()" % (f, ampiezza, hz, secondi))
    root("python3 -c \"%s\" && chmod 644 %s" % (copione, f), 300)
    return f


def tono_accendi():
    tono_fabbrica()
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus "
         "sh -c 'while :; do pw-play --target remotix %s/tono-440.wav; done' "
         ">/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, UID_B, LAV))
    for _ in range(30):
        time.sleep(0.4)
        if legami() > 0:
            return True
    return False


def legami():
    rc, out, _ = root("env UTENTE=%s UID_B=%d LAV=%s python3 %s/banchi/"
                      "07-b64-scena.py grafo" % (UTENTE, UID_B, LAV, ALB))
    try:
        return json.loads(out).get("legami_in_ingresso", 0)
    except Exception:
        return -1


def tono_spegni():
    root("pkill -u %d -f 'while :; do pw-play'; pkill -u %d -x pw-play; true"
         % (UID_B, UID_B))


# ── la scena che fa lavorare il codificatore ───────────────────────────────
def scena_accendi():
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -1" % LAV)
    m = re.findall("monitor «([^»]*)»", out)
    usc = m[-1] if m and m[-1] else None
    if not usc:
        return None
    root("setsid nohup setpriv --reuid=%d --regid=%d --init-groups env -i "
         "HOME=/home/%s USER=%s LANG=C.UTF-8 PATH=/usr/local/bin:/usr/bin:/bin "
         "XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=wayland-0 "
         "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena --uscita %s "
         "--movimento barra --shm /07-b65 --giro b65 >/dev/null 2>&1 & echo acceso"
         % (UID_B, UID_B, UTENTE, UTENTE, UID_B, usc))
    time.sleep(1.5)
    rc, out, _ = root("pgrep -u %d -f '04-b30-scena --uscita' | head -1" % UID_B)
    return usc if out.strip() else None


def scena_spegni():
    root("pkill -u %d -f 04-b30-scena; true" % UID_B)


# ── ⭐ I BYTE VERI SUL FILO, che sono l altra meta della domanda ───────────
#
# ⛔ Il carico utile di un blocco PCM e' 972 byte, ma il pacchetto che lo porta
#    puo' essere molto piu' grosso: `dgram_scrivi_uno` chiede
#    `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING`, e il padding riempie il pacchetto
#    fino alla misura piena.  ⇒ Se il datagram NON riesce a dividere il
#    pacchetto col video, ogni blocco d audio costa 1452 byte invece di 972:
#    il 49 % di banda in piu' di quel che il suono contiene.
#
# ⚠ Non si deduce: si contano i byte che escono, e il contatore ce l ha gia'
#   il qdisc `netem` che questo banco installa.
def byte_sul_filo():
    rc, out, _ = root("/usr/sbin/tc -s qdisc show dev %s" % DEV)
    import re as _re
    blocchi = out.split("qdisc netem 40:")
    if len(blocchi) < 2:
        return None
    m = _re.search(r"Sent (\d+) bytes (\d+) pkt", blocchi[1])
    return (int(m.group(1)), int(m.group(2))) if m else None


# ── un giro: il cliente dentro il contenitore, audio + video ───────────────
def giro(nome, codec, secondi):
    root("rm -f %s/%s.jsonl %s/%s.265; true" % (LAV, nome, LAV, nome))
    # ⛔ Si prende il numero di righe del registro PRIMA, cosi' il «conto
    #    finale» che si legge dopo e' di QUESTA sessione e non di quella prima.
    rc, out, _ = root("wc -l < %s/registro.log" % LAV)
    try:
        riga0 = int(out.strip())
    except Exception:
        riga0 = 0
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec %s "
              "--audio-scrivi %s/%s.jsonl --adatta 1920x1080 "
              "--video-scrivi %s/%s.265 --resta %d"
              # ⛔ `opus` DA SOLO NON BASTA, e il server ha ragione a
              #   rifiutarlo: RCP §4.3 fa del PCM la base obbligatoria ai due
              #   capi, e un CIAO che dichiara solo Opus prende
              #   CONGEDO(NIENTE_IN_COMUNE 0x09).  Il banco lo aveva preso per
              #   un guasto per due giri.
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV,
                 "opus,pcm" if codec == "opus" else codec,
                 DENTRO_LAV, nome, DENTRO_LAV, nome, secondi))
    prima_filo = byte_sul_filo()
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 240)
    dopo_filo = byte_sul_filo()
    testo = out + err
    r = {"cliente": {}}
    for x in testo.splitlines():
        if "[audio] ricevuti" in x:
            r["cliente"]["audio"] = x.strip()
        if "[audio] scartati" in x:
            r["cliente"]["scartati"] = x.strip()
        if "[vid]" in x:
            r["cliente"]["video"] = x.strip()
    # ⛔ Il conto del SERVER, e solo le righe nate in questo giro.
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -aE 'conto finale|cwnd_left' "
                      "| tail -4" % (riga0 + 1, LAV))
    r["server"] = [x.strip() for x in out.splitlines()]
    if prima_filo and dopo_filo:
        b = dopo_filo[0] - prima_filo[0]
        pk = dopo_filo[1] - prima_filo[1]
        r["filo"] = {"byte": b, "pacchetti": pk,
                     "byte_per_pacchetto": round(b / pk, 1) if pk else None,
                     "mbit_s": round(b * 8 / secondi / 1e6, 3)}
    return r


def giudica(nome, codec):
    """⛔ Con Opus non si ascolta: il giudice non lo decodifica, e dirlo e'
       meglio che far finta (`CODER.md` §3.10)."""
    j = os.path.join(FUORI, nome + ".jsonl")
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/%s.jsonl\" > %s" % (MACCHINA, PAROLA_SUDO, LAV, nome, j),
                   shell=True)
    if codec != "pcm":
        return {"esito": "NON GIUDICATO — Opus: il giudice non lo decodifica, "
                         "qui si conta il trasporto"}
    if not os.path.exists(j) or os.path.getsize(j) == 0:
        return {"esito": "NIENTE DA GIUDICARE — nessun blocco"}
    p = subprocess.run(["python3", os.path.join(QUI, "07-b64-orecchio.py"), j,
                        "--hz", "440"], capture_output=True)
    try:
        d = json.loads(p.stdout.decode())["nostro"]
    except Exception as e:
        return {"esito": "il giudice non ha risposto: %s" % e}
    return {"blocchi": d["blocchi"], "resa_campioni": d.get("resa_campioni"),
            "scoppiettii_al_s": d["scoppiettii"]["al_secondo"], "tono": d["tono"]}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["sonda", "rimetti", "stato"])
    p.add_argument("--secondi", type=int, default=30)
    p.add_argument("--codec", default="pcm", choices=["pcm", "opus"])
    p.add_argument("--solo", default="")
    p.add_argument("--scena", default="si", choices=["si", "no"],
                   help="il desktop che si muove (e quindi il video che pesa)")
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    if a.passo in ("rimetti", "stato"):
        return 0 if rimetti() else 2

    print("== 07-b65 · chi paga quando il tubo e' stretto — porta %d, dev «%s»"
          % (PORTA, DEV))
    print("   ⛔ «%s» (ssh + 7730 dell utente) NON si tocca" % VIETATA)
    print("   --  «%s» prima: %s" % (DEV, qdisc() or "(nessuna)"))
    totale = (a.secondi + 150) * len(GRADINI) + 300
    root("pkill -f 'tc qdisc del dev %s root'; true" % DEV)
    root("setsid nohup sh -c 'sleep %d; /usr/sbin/tc qdisc del dev %s root' "
         ">/dev/null 2>&1 & echo guardiano" % (totale, DEV))
    print("   OK  guardiano armato per %d s" % totale)

    esiti = []
    try:
        print("   --  apro una sessione corta per far nascere il palco e il sink")
        if not innesca_sessione():
            print("   NO  la sessione non si apre: non misuro"); return 2
        if not tono_accendi():
            print("   NO  il tono non suona: non misuro"); return 2
        usc = scena_accendi() if a.scena == "si" else None
        # ⭐ `--scena no` e' il CONTROLLO che separa i due imputati: con il
        #    desktop fermo il video chiede pochissimo, e se in quella
        #    condizione l audio passa, allora non e' «l audio cede sempre» —
        #    e' «il video si mangia la finestra».
        print("   %s scena sul monitor %s" % ("OK " if usc else "-- ", usc))
        for nome, regole, atteso in GRADINI:
            if a.solo and a.solo not in nome:
                continue
            print("\n-- %s · %s" % (nome, atteso))
            ok, q = stringi(regole)
            if not ok:
                print("   ", q); break
            print("    tc: %s" % " ".join(q.split("\n")[:2])[:150])
            leg = legami()
            print("    M3: legami in ingresso al sink = %s" % leg)
            if leg <= 0:
                print("   NO  il tono tace: NON giudico questo gradino")
                esiti.append({"gradino": nome, "esito": "il tono taceva"})
                continue
            r = giro(nome, a.codec, a.secondi)
            for k in ("audio", "scartati", "video"):
                if k in r["cliente"]:
                    print("    %s" % r["cliente"][k])
            if "filo" in r:
                print("    FILO %s" % json.dumps(r["filo"], ensure_ascii=False))
            for x in r["server"]:
                print("    SERVER %s" % x[:190])
            g = giudica(nome, a.codec)
            print("    orecchio: %s" % json.dumps(g, ensure_ascii=False))
            esiti.append({"gradino": nome, "regole": regole, "atteso": atteso,
                          "cliente": r["cliente"], "server": r["server"],
                          "orecchio": g})
    finally:
        scena_spegni()
        tono_spegni()
        print("\n== ⛔ LA RETE SI RIMETTE COM'ERA")
        rimetti()
    json.dump(esiti, open(os.path.join(FUORI, "b65-esiti.json"), "w"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
