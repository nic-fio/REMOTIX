#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b68 — ⭐ LA PRIMA MISURA DELLA FASE 9: L'INVARIANTE I1.

   `SPECIFICHE.md` §8.2: *«Il ritmo non cala mai per prudenza, per risparmio o
   perche' la scena e' ferma.  Cala solo quando la misura dimostra che la linea
   non porta, e ogni discesa e' dichiarata nel registro.»*

⛔ LA DOMANDA, UNA SOLA: su linea larga — nessuna strozzatura, il caso in cui
   I1 non ha nessuna scusa — **il ritmo cala quando la scena e' ferma?**

⭐ IL CONTROLLO CHE DECIDE, e va guardato PRIMA dei numeri (`CODER.md` §3.3):
   se «ferma» e «mossa» danno lo stesso ritmo, o se tutti i contatori sono a
   zero, il banco **non ha misurato niente** e lo dice invece di riportare.
   ⇒ Qui il controllo positivo e' la scena `pieno`: se nemmeno bande a schermo
     intero muovono i numeri, e' il banco a essere cieco, non il prodotto.

---------------------------------------------------------------------------
⛔ IL MESTIERE E' QUELLO DI `07-b65-datagram.py`, non una strada nuova:

   · la sessione la apre `banchi/01-b3-cliente.py` DENTRO il contenitore
     (`enter.sh --root`), perche' li' c'e' `aioquic` e fuori no;
   · ⛔ **mai una redirezione ATTORNO a `ssh`**: la richiesta di `sudo` va
     sullo stderr e una redirezione la mangia;
   · la scena e' `04-b30-scena`, gia' costruita in
     `/media/REMOTIX/src/04-b30-scena-lav/`, e vuole il monitor PER NOME —
     il nome lo dice il registro (`monitor «Meta-0»`);
   · ⛔ il palco nasce col PRIMO cliente e sopravvive al distacco (I4):
     senza una sessione aperta prima, `--uscita` non trova nessun monitor.

⭐ E I BYTE SUL FILO SI CONTANO SU `lo`, NON SI DEDUCONO.
   `[M]` 23 agosto 2026: `lo` a riposo su questa macchina fa **0 byte in 5 s**
   (l'ssh passa da `enp7s0`, il resto e' su socket unix) ⇒ `/proc/net/dev` e'
   un contatore pulito, e NON serve toccare `tc`.  ⚠ E' un vantaggio del
   momento, non una legge: si rimisura il riposo a ogni giro e si dichiara.

⛔ I byte del filo NON sono i byte dei fotogrammi: la riga «SPEDITO» conta il
   carico utile, `lo` conta anche QUIC, l'audio PCM e i riscontri.  Si riportano
   tutt'e due, e la differenza e' un fatto, non un errore.

Uso (dal portatile):
    python3 banchi/09-b68-ritmo.py giro --scena ferma  --secondi 30
    python3 banchi/09-b68-ritmo.py giro --scena barra  --secondi 30
    python3 banchi/09-b68-ritmo.py giro --scena pieno  --secondi 30
    python3 banchi/09-b68-ritmo.py tutto --secondi 30   # i tre di fila
    python3 banchi/09-b68-ritmo.py stato
"""
import argparse, json, os, re, subprocess, sys, time

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7900"))
UTENTE = os.environ.get("UTENTE", "prova")
UID_B = int(os.environ.get("UID_B", "1001"))
# ⛔⭐ ALBERO, LAVORO E PORTA SI PRENDONO DALL'AMBIENTE — 23 agosto 2026, sera.
#     I difetti sono ESATTAMENTE quelli di stamattina (7900, `tmp/09`, `09-src`)
#     ⇒ ogni giro gia' fatto si rifa' identico senza scrivere niente.
# ⚠ Servono al confronto APPAIATO fra il **prima** (7900, albero `09-src`) e il
#   **dopo** (7910, albero `09b-src`): due alberi, due cartelle di lavoro, due
#   unita' — perche' `LEZIONI.md` §1.26 vieta di misurare in due sulla stessa
#   macchina, e riusare la cartella dell'uno per l'altro e' lo stesso difetto
#   con un altro nome (registri mescolati, e nessun rosso).
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09")
# Il nome dell'albero come si vede in `pgrep`, per riconoscere I MIEI processi
# e non quelli del gemello.
ALB_NOME = os.environ.get("ALB_NOME", "09-src")
SCENA = "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena"
FUORI = os.environ.get("FUORI", "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX-V2/"
                                "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/b68")


def rem(comando, tetto=600):
    """⛔ Niente redirezione ATTORNO a ssh: la richiesta di sudo va sullo stderr."""
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=600):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando), tetto)


# ── il filo: `lo`, letto due volte ─────────────────────────────────────────
def filo():
    rc, out, _ = rem("grep ' lo:' /proc/net/dev")
    c = out.split(":")[1].split()
    return int(c[8]), int(c[9])          # byte trasmessi, pacchetti trasmessi


# ── ⛔ LA RETE, SOLO PER IL CONTROLLO POSITIVO DI §5.1 ─────────────────────
#
# ⚠ NON e' la misura: la misura di questa fase e' su LINEA LARGA.  Serve a una
#   cosa sola — sapere se «abbandoni §5.1 = 0» e' una risposta o una cecita'.
#
# ⛔ La disciplina e' quella di `07-b64-rete.py` / `07-b65-datagram.py`, riga
#    per riga: solo `lo`, solo la porta di questo banco, `enp7s0` (ci passano
#    l'ssh e la 7730 dell'utente) MAI, e un guardiano staccato che rimette la
#    rete anche se questo copione muore a meta'.
DEV = "lo"
VIETATA = "enp7s0"
GUARDIANO = LAV + "/.b68-guardiano.pid"


def qdisc():
    return root("/usr/sbin/tc qdisc show dev %s" % DEV)[1].strip()


def guardiano_arma(secondi):
    """⛔ Il `&` e l'`echo $!` girano DENTRO la shell di root, o il redirect
       verso `$LAV` (di root) fallisce e il pid non si scrive: un guardiano
       che non si puo' disarmare per pid e' la cura senza la sua meta'."""
    guardiano_disarma()
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (secondi, DEV, GUARDIANO))


def guardiano_disarma():
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIANO)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIANO)


def rimetti(dillo=True):
    guardiano_disarma()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q and "tbf" not in q
    if dillo:
        print("   %s «%s» adesso e': %s" % ("OK " if ok else "⛔ ", DEV, q or "(nessuna)"))
        print("   --  %s (ssh + la 7730 dell'utente), mai toccata: %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s" % VIETATA)[1].split("\n")[0]))
    return ok


def stringi(regole):
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem %s" % (DEV, " ".join(regole)),
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


def righe_registro():
    """⛔ `wc -l < file` NO: il `<` lo apre la shell di `nicfio`, che il
       registro (di root, 0644 ma in una cartella 0755... e comunque il primo
       giro ha dato VUOTO) non lo legge ⇒ riga0 = 0 ⇒ lo spoglio si prende
       ANCHE le sessioni di prima e il banco riporta i numeri di due giri
       sommati.  ⚠ `[M]` 23 ago 2026: il primo giro di prova contava 413
       fotogrammi dove il server ne dichiarava 398.
       ⇒ Il file lo apre `wc`, che gira da root."""
    rc, out, _ = root("wc -l %s/registro.log" % LAV)
    m = re.match(r"\s*(\d+)", out)
    if not m:
        raise SystemExit("⛔ non so quante righe ha il registro: «%s»" % out.strip())
    return int(m.group(1))


# ── il palco: nasce col primo cliente e sopravvive al distacco (I4) ────────
def monitor():
    rc, out, _ = root("grep -ao 'monitor «[^»]*»' %s/registro.log | tail -20" % LAV)
    nomi = [x for x in re.findall("monitor «([^»]*)»", out) if x]
    return nomi[-1] if nomi else None


def palco_vivo():
    rc, out, _ = root("pgrep -u %d -f 'remotix-figlio --figlio-interno' | head -1" % UID_B)
    return bool(out.strip())


def innesca(secondi=8):
    """⛔ Senza una sessione aperta almeno una volta non esiste nessun monitor,
       e `04-b30-scena --uscita` fallisce dicendo che il nome non c'e'."""
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--adatta 1920x1080 --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro, secondi + 240)
    return "SESSIONE" in (out + err)


def scena_accendi(movimento):
    """⛔ Passa da uno SCRIPT, non da `ssh -> sudo -> setsid ... > file`: il
       redirect lo farebbe la shell di `nicfio`, che in `/media/REMOTIX/tmp/09`
       (di root) non puo' scrivere — `[M]` 23 ago, la scena moriva e il suo
       registro era VUOTO."""
    usc = monitor()
    if not usc:
        return None, "nessun monitor nel registro: il palco non e' mai nato"
    rc, out, err = root("env LAV=%s sh %s/09-b68-scena.sh %s %s"
                        % (LAV, LAV, usc, movimento), 120)
    if "SCENA ACCESA" not in out:
        return None, "la scena non e' partita: %s" % (out + err).strip()[:500]
    return usc, None


def scena_spegni():
    root("env LAV=%s sh %s/09-b68-scena.sh -- spegni; true" % (LAV, LAV))
    time.sleep(0.5)


# ── ⭐ LO SPOGLIO DEL REGISTRO — solo le righe NATE IN QUESTO GIRO ─────────
# ⛔⛔ L'IDENTITA' FRA L'AREA E IL CORPO — 25 agosto 2026, cura C4 della fase 10.
#
#   Da quel giorno ogni riga che sa di chi e' porta `[nome] ` **in testa al
#   corpo**, subito dopo l'area.  Un modello ancorato che non lo preveda
#   ⛔ non trova piu' NIENTE — e il guaio non e' che si ferma: e' che il
#   conto esce **zero**, cioe' un numero che ACCUSA il prodotto di non aver
#   spedito un fotogramma mentre li spediva tutti.
#   ⇒ Il gruppo qui sotto e' FACOLTATIVO apposta: cosi' il lettore funziona
#     sui registri di prima **e** su quelli di adesso.
R_SPED = re.compile(r"fotogramma (\d+) SPEDITO: (CHIAVE|delta) 0x0\d0\d, codec (\d+), "
                    r"(\d+)x(\d+), (\d+) byte di dati")
R_CICLO = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d\d\d) figlio\s+(?:\[[^\]]{1,48}\] )?ciclo: (\d+) fotogrammi "
                     r"consegnati \((\d+) chiavi\), (\d+) attese a vuoto", re.M)


def spoglia(testo, secondi):
    sped = R_SPED.findall(testo)
    chiavi = [x for x in sped if x[1] == "CHIAVE"]
    delta = [x for x in sped if x[1] == "delta"]
    byte_car = sum(int(x[5]) for x in sped)

    # ⭐ la serie al secondo, dalle righe «ciclo» del figlio (cumulative).
    #    ⭐⭐ E `attese a vuoto` e' LA COLONNA CHE SPIEGA: il figlio la chiama
    #       lui stesso «scena ferma: Mutter consegna solo quando qualcosa
    #       cambia» — cioe' dichiara nel registro perche' il ritmo cala.
    serie, prima, vuoti = [], None, 0
    for r in R_CICLO.finditer(testo):
        t = int(r.group(1)) * 3600 + int(r.group(2)) * 60 + int(r.group(3)) + int(r.group(4)) / 1000
        n, k, v = int(r.group(5)), int(r.group(6)), int(r.group(7))
        if prima is not None:
            dt = t - prima[0]
            if dt > 0.2:
                serie.append({"dt": round(dt, 2), "fot": n - prima[1],
                              "chiavi": k - prima[2], "vuote": v - prima[3]})
        prima = (t, n, k, v)
        vuoti = v

    def conta(frammento):
        return testo.count(frammento)

    d = {
        "fotogrammi_spediti": len(sped),
        "chiavi": len(chiavi),
        "delta": len(delta),
        "fotogrammi_s": round(len(sped) / secondi, 2),
        "byte_carico_video": byte_car,
        "kbit_s_carico_video": round(byte_car * 8 / secondi / 1000, 1),
        "byte_medio_fotogramma": round(byte_car / len(sped)) if sped else 0,
        # ⛔ gli ABBANDONI, §5.1 e §5.2
        "abbandoni_5_1": conta("ABBANDONATO NELLA CODA (§5.1"),
        "chiave_trattenuta_5_2": conta("§5.2 vieta di abbandonarla"),
        "chiave_non_abbandonata_a_valle": conta("§5.2 lo vieta anche a valle"),
        "fuori_elenco_5_1": conta("non entra nell'elenco e NON potra' essere abbandonato"),
        # ⛔ le RICHIESTE DI CHIAVE
        "richiedi_chiave_accolte": conta("accolta (§5.2)"),
        "richiedi_chiave_ignorate": conta("TOLLERANZA DICHIARATA"),
        "delta_buttato_perche_serve_chiave": conta("e' un delta e §5.2 vuole una CHIAVE"),
        "chiave_girata_al_palco": conta("§5.2 vuole una CHIAVE — richiesta girata al palco"),
        "intervallo_chiave_cambiato": conta("la CHIAVE si potra' richiedere ogni"),
        "attese_a_vuoto": vuoti,
        "serie_al_secondo": serie,
    }
    d["conto_finale"] = [x.strip() for x in testo.splitlines() if "conto finale" in x]
    d["righe_intervallo"] = [x.strip()[:260] for x in testo.splitlines()
                             if "la CHIAVE si potra' richiedere ogni" in x]
    return d


# ── un giro intero ─────────────────────────────────────────────────────────
def giro(nome, movimento, secondi, extra=""):
    print("\n== giro «%s» · scena %s · %d s" % (nome, movimento, secondi))
    if not palco_vivo():
        print("   --  nessun figlio vivo: apro una sessione corta per far nascere il palco")
        if not innesca():
            return {"giro": nome, "esito": "⛔ la sessione non si apre"}
    usc, guasto = (None, None)
    if movimento != "ferma":
        usc, guasto = scena_accendi(movimento)
        if guasto:
            return {"giro": nome, "esito": "⛔ " + guasto}
        print("   OK  scena «%s» sul monitor «%s»" % (movimento, usc))
    else:
        scena_spegni()
        print("   OK  nessuna scena: il desktop e' fermo")

    riga0 = righe_registro()
    fb, pb = filo()
    t0 = time.time()
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec pcm "
              "--adatta 1920x1080 %s--video-scrivi %s/b68-%s.h26x --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV,
                 extra + " " if extra else "", DENTRO_LAV, nome, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro, secondi + 300)
    durata = time.time() - t0
    fa, pa = filo()
    if movimento != "ferma":
        scena_spegni()

    testo_cli = out + err
    cli = {}
    for x in testo_cli.splitlines():
        for k, f in (("audio", "[audio] ricevuti"), ("scartati", "[audio] scartati"),
                     ("video", "[vid]  ")):
            if f in x:
                cli[k] = x.strip()

    rc, reg, _ = root("tail -n +%d %s/registro.log" % (riga0 + 1, LAV), 300)
    d = spoglia(reg, secondi)
    d.update({
        "giro": nome, "scena": movimento, "secondi_chiesti": secondi,
        "durata_giro_s": round(durata, 1), "monitor": usc,
        "cliente": cli,
        "filo_lo": {"byte": fa - fb, "pacchetti": pa - pb,
                    "mbit_s": round((fa - fb) * 8 / secondi / 1e6, 3),
                    "byte_per_pacchetto": round((fa - fb) / (pa - pb), 1) if pa > pb else None},
        "ora_macchina": time.strftime("%H:%M:%S"),
    })
    with open(os.path.join(FUORI, "reg-%s.log" % nome), "w") as f:
        f.write(reg)
    return d


def stampa(d):
    if "esito" in d:
        print("   ", d["esito"]); return
    print("   fotogrammi %d = %d CHIAVE + %d delta  ⇒ %.2f/s"
          % (d["fotogrammi_spediti"], d["chiavi"], d["delta"], d["fotogrammi_s"]))
    print("   carico video %d byte (%.1f kbit/s), medio %d byte/fotogramma"
          % (d["byte_carico_video"], d["kbit_s_carico_video"], d["byte_medio_fotogramma"]))
    print("   FILO lo: %s" % json.dumps(d["filo_lo"], ensure_ascii=False))
    print("   abbandoni §5.1 %d · chiave trattenuta §5.2 %d · fuori elenco %d"
          % (d["abbandoni_5_1"], d["chiave_trattenuta_5_2"], d["fuori_elenco_5_1"]))
    print("   RICHIEDI_CHIAVE accolte %d · ignorate %d · girate al palco %d · "
          "delta buttati per la chiave %d"
          % (d["richiedi_chiave_accolte"], d["richiedi_chiave_ignorate"],
             d["chiave_girata_al_palco"], d["delta_buttato_perche_serve_chiave"]))
    for k in ("audio", "scartati", "video"):
        if k in d["cliente"]:
            print("   CLI %s" % d["cliente"][k])
    for x in d["conto_finale"]:
        print("   SRV %s" % x[:230])
    for x in d["righe_intervallo"][:3]:
        print("   INT %s" % x)
    s = d["serie_al_secondo"]
    if s:
        print("   fotogrammi al secondo: %s" % " ".join(str(x["fot"]) for x in s))
        print("   attese a vuoto al secondo (Mutter non consegna): %s"
              % " ".join(str(x["vuote"]) for x in s))


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["giro", "tutto", "controllo", "stretto",
                                     "rimetti", "stato"])
    p.add_argument("--scena", default="ferma", choices=["ferma", "barra", "pieno"])
    p.add_argument("--secondi", type=int, default=30)
    a = p.parse_args()
    os.makedirs(FUORI, exist_ok=True)

    print("== 09-b68 · l'invariante I1 — porta %d, utente «%s», linea LARGA (nessuna strozzatura)"
          % (PORTA, UTENTE))
    fb, _ = filo(); time.sleep(3); fa, _ = filo()
    print("   ⭐ riposo di «lo» prima di misurare: %d byte in 3 s "
          "(il contatore e' pulito solo se e' ~0)" % (fa - fb))
    if a.passo == "rimetti":
        return 0 if rimetti() else 2

    if a.passo == "stato":
        print("   monitor: %s · palco vivo: %s" % (monitor(), palco_vivo()))
        print("   «%s»: %s" % (DEV, qdisc() or "(nessuna)"))
        return 0

    if a.passo == "stretto":
        # ⛔⛔ IL SECONDO CONTROLLO POSITIVO, e riguarda gli ALTRI zeri:
        #    «abbandoni §5.1 = 0» su linea larga e' una risposta solo se si sa
        #    che quel contatore SA muoversi.  Su linea larga non puo': niente
        #    e' in coda, quindi niente puo' essere abbandonato.
        # ⚠ NON e' la misura della fase — quella e' su linea larga.  Qui la
        #   linea si stringe apposta, per una volta sola, e poi si rimette.
        print("   ⛔ «%s» (ssh + la 7730 dell'utente) NON si tocca" % VIETATA)
        print("   --  «%s» prima: %s" % (DEV, qdisc() or "(nessuna)"))
        guardiano_arma(a.secondi + 400)
        try:
            ok, q = stringi(["delay", "15ms", "rate", "2mbit"])
            if not ok:
                print("   ", q); return 2
            print("    tc: %s" % " ".join(q.split("\n")[:2])[:140])
            d = giro("stretto-2mbit", "pieno", a.secondi)
            stampa(d)
        finally:
            scena_spegni()
            print("\n== ⛔ LA RETE SI RIMETTE COM'ERA")
            rimesso = rimetti()
        n = d.get("abbandoni_5_1", 0) + d.get("chiave_trattenuta_5_2", 0)
        print("\n   %s i contatori di §5.1/§5.2 %s (abbandoni %d, chiave trattenuta %d)"
              % ("OK " if n else "⛔ ", "SI MUOVONO" if n else "restano fermi",
                 d.get("abbandoni_5_1", 0), d.get("chiave_trattenuta_5_2", 0)))
        with open(os.path.join(FUORI, "b68-stretto.json"), "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        return 0 if (n and rimesso) else 2

    if a.passo == "controllo":
        # ⛔⛔ IL CONTROLLO POSITIVO, e senza di lui i numeri di sopra non
        #    valgono.  Su linea larga «abbandoni 0» e «RICHIEDI_CHIAVE 0» hanno
        #    la stessa faccia di «il banco non guarda quei contatori»
        #    (`LEZIONI.md` §1.9: vuoto e giusto si somigliano).
        # ⭐ Qui il cliente CHIEDE una chiave a meta' giro: se il contatore non
        #   si muove, e' il banco a essere cieco e i suoi zeri non dicono
        #   niente.
        # ⛔⛔ E LO STIMOLO NON E' `--chiave-dopo` DA SOLO — costa un giro
        #    saperlo: nel cliente quella riga vive DENTRO il ramo di
        #    `--puntatore-vecchia` (`01-b3-cliente.py:1463`), e senza il
        #    puntatore la RICHIEDI_CHIAVE non parte mai.  ⚠ Il primo giro di
        #    controllo ha dato «il contatore non si muove» accusando il BANCO,
        #    mentre a non essere avvenuto era lo STIMOLO — cioe' il controllo
        #    positivo aveva bisogno, lui, di essere controllato.
        #    ⇒ La tela va prima RIMPICCIOLITA (@3), o il puntatore alla tela
        #      vecchia non e' esercitabile e il cliente esce con 6.
        d = giro("controllo-chiave", "barra", 14,
                 extra="--adatta 1280x720@3 --puntatore-vecchia 0.3 --chiave-dopo 2")
        stampa(d)
        n = d.get("richiedi_chiave_accolte", 0) + d.get("richiedi_chiave_ignorate", 0)
        print("\n   %s il contatore delle RICHIEDI_CHIAVE %s (accolte %d, ignorate %d)"
              % ("OK " if n else "⛔ ", "SI MUOVE" if n else "NON si muove: il banco e' cieco",
                 d.get("richiedi_chiave_accolte", 0), d.get("richiedi_chiave_ignorate", 0)))
        with open(os.path.join(FUORI, "b68-controllo.json"), "w") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        return 0 if n else 2

    scene = [a.scena] if a.passo == "giro" else ["ferma", "barra", "pieno", "ferma"]
    esiti = []
    try:
        for i, m in enumerate(scene):
            d = giro("%s-%d" % (m, i + 1), m, a.secondi)
            stampa(d)
            esiti.append(d)
    finally:
        scena_spegni()
    with open(os.path.join(FUORI, "b68-esiti.json"), "w") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    print("\n== esiti in %s/b68-esiti.json" % FUORI)
    return 0


if __name__ == "__main__":
    sys.exit(principale())
