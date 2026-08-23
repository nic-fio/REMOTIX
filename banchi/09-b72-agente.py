#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b72-agente — ⭐ IL DIRETTORE DEL GRADINO, e il contatore del filo.
Gira SULLA MACCHINA, da root.

⛔ ESISTE PER UNA RAGIONE SOLA, ED E' IL TEMPO.  Il gradino della fase 9 dura
   **3 secondi**.  Aprire e chiudere la strozzatura da `ssh` costa fra i 200 e
   i 400 ms per giro, cioe' **oltre il 10 % del gradino**, e non si sa quanto:
   il transitorio misurato sarebbe quello dell'ssh, non quello del prodotto.
   ⇒ chi cambia la disciplina e chi guarda il filo devono stare **sulla
     macchina**, con un orologio solo.

⛔ E LA DISCIPLINA E' QUELLA DI `07-b64`/`07-b65`/`09-b68`, riga per riga:
     · solo `lo`, ⛔ `enp7s0` MAI (ci passano l'ssh e la sessione dell'utente);
     · solo la porta di questo banco, per numero, in andata e in ritorno;
     · un guardiano staccato — lo arma il banco, non io — che rimette la rete
       anche se questo copione muore a meta'.

⭐ IL RITARDO NON CAMBIA MAI FRA LE FASI, cambia solo la BANDA.
   `netem delay 15ms rate X` in tutte e tre le fasi: se il gradino cambiasse
   anche l'RTT, il controllo di congestione reagirebbe a **due** cose insieme e
   il transitorio misurato non sarebbe quello della banda.  ⇒ `tc qdisc change`
   tocca il solo `rate`.

⛔ «larga» NON e' «nessuna disciplina»: e' la stessa `netem` con un tetto
   altissimo.  Togliere e rimettere la qdisc fra le fasi resetterebbe le code e
   il gradino misurerebbe anche quel salto.

Uso (da root, sulla macchina):
    python3 09-b72-agente.py --fasi larga:6,stretta:3,larga:15 \
        --rate-stretta 10mbit --uscita /media/REMOTIX/tmp/09/b72-g.jsonl
    python3 09-b72-agente.py --fasi solo:30 --senza-tc --uscita ...
"""
import argparse, json, os, subprocess, sys, time

TC = "/usr/sbin/tc"


def tc(*args):
    p = subprocess.run([TC] + list(args), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def qdisc(dev):
    return tc("qdisc", "show", "dev", dev)[1]


def filo(dev):
    """I byte sul filo si CONTANO, non si deducono — `09-b68` §1.1."""
    with open("/proc/net/dev") as f:
        for r in f:
            if r.strip().startswith(dev + ":"):
                c = r.split(":")[1].split()
                return int(c[8]), int(c[9]), int(c[0]), int(c[1])
    return None


def monta(dev, porta, ritardo, rate):
    """⛔ Se un passo fallisce si smonta tutto: una disciplina a meta' e' la
       peggiore delle uscite — strozza e nessuno sa piu' che cosa."""
    passi = [
        ("qdisc", "del", "dev", dev, "root"),
        ("qdisc", "add", "dev", dev, "root", "handle", "1:", "prio", "bands", "4"),
        ("qdisc", "add", "dev", dev, "parent", "1:4", "handle", "40:", "netem",
         "delay", ritardo, "rate", rate),
        ("filter", "add", "dev", dev, "protocol", "ip", "parent", "1:0", "prio", "1",
         "u32", "match", "ip", "protocol", "17", "0xff",
         "match", "ip", "sport", str(porta), "0xffff", "flowid", "1:4"),
        ("filter", "add", "dev", dev, "protocol", "ip", "parent", "1:0", "prio", "1",
         "u32", "match", "ip", "protocol", "17", "0xff",
         "match", "ip", "dport", str(porta), "0xffff", "flowid", "1:4"),
    ]
    for i, c in enumerate(passi):
        rc, out = tc(*c)
        if rc != 0 and i > 0:
            tc("qdisc", "del", "dev", dev, "root")
            return False, "⛔ tc ha rifiutato «%s»: %s" % (" ".join(c), out[:200])
    return True, qdisc(dev)


def cambia(dev, ritardo, rate):
    return tc("qdisc", "change", "dev", dev, "parent", "1:4", "handle", "40:",
              "netem", "delay", ritardo, "rate", rate)


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--dev", default="lo")
    p.add_argument("--vietata", default="enp7s0")
    p.add_argument("--porta", type=int, default=7900)
    p.add_argument("--fasi", default="larga:6,stretta:3,larga:15")
    p.add_argument("--rate-larga", default="1000mbit")
    p.add_argument("--rate-stretta", default="10mbit")
    p.add_argument("--ritardo", default="15ms")
    p.add_argument("--passo", type=float, default=0.1, help="ogni quanto si guarda il filo")
    p.add_argument("--senza-tc", action="store_true")
    p.add_argument("--uscita", required=True)
    a = p.parse_args()

    if a.dev == a.vietata:
        print(json.dumps({"guasto": "⛔ «%s» non si tocca MAI" % a.vietata}))
        return 2
    fasi = []
    for x in a.fasi.split(","):
        n, s = x.split(":")
        fasi.append((n.strip(), float(s)))

    fuori = open(a.uscita, "w")
    _t = time.time()
    testa = {"che": "intestazione", "dev": a.dev, "porta": a.porta,
             "fasi": fasi, "rate_larga": a.rate_larga, "rate_stretta": a.rate_stretta,
             "ritardo": a.ritardo, "senza_tc": a.senza_tc, "passo_s": a.passo,
             "ancora_epoch": _t,
             "ancora_locale": (time.strftime("%H:%M:%S", time.localtime(_t))
                               + ".%03d" % int((_t % 1) * 1000)),
             "qdisc_prima": qdisc(a.dev),
             "vietata_prima": qdisc(a.vietata).split("\n")[0]}
    fuori.write(json.dumps(testa, ensure_ascii=False) + "\n")
    fuori.flush()

    if not a.senza_tc:
        ok, q = monta(a.dev, a.porta, a.ritardo, a.rate_larga)
        if not ok:
            fuori.write(json.dumps({"guasto": q}) + "\n")
            print(json.dumps({"guasto": q}))
            return 2
        fuori.write(json.dumps({"che": "montata", "qdisc": q}, ensure_ascii=False) + "\n")

    eventi, campioni = [], []
    try:
        t0 = time.time()
        b0 = filo(a.dev)
        prossimo = t0
        for nome, durata in fasi:
            if not a.senza_tc:
                rate = a.rate_stretta if nome == "stretta" else a.rate_larga
                ta = time.time()
                rc, out = cambia(a.dev, a.ritardo, rate)
                tb = time.time()
                eventi.append({"fase": nome, "rate": rate, "t_prima": ta, "t_dopo": tb,
                               "costo_ms": round((tb - ta) * 1000, 2),
                               "rc": rc, "detto": out[:120]})
            else:
                eventi.append({"fase": nome, "t_prima": time.time(), "t_dopo": time.time()})
            fine = time.time() + durata
            while time.time() < fine:
                prossimo += a.passo
                d = time.time()
                if prossimo > d:
                    time.sleep(prossimo - d)
                b = filo(a.dev)
                campioni.append({"t": time.time(), "fase": nome,
                                 "tx_byte": b[0] - b0[0], "tx_pac": b[1] - b0[1],
                                 "rx_byte": b[2] - b0[2], "rx_pac": b[3] - b0[3]})
    finally:
        # ⛔ SI RIMETTE, E SI VERIFICA — non si crede.
        rimessa = None
        if not a.senza_tc:
            tc("qdisc", "del", "dev", a.dev, "root")
            rimessa = qdisc(a.dev)
        coda = {"che": "coda", "eventi": eventi, "campioni": campioni,
                "t_fine": time.time(), "qdisc_dopo": rimessa,
                "vietata_dopo": qdisc(a.vietata).split("\n")[0]}
        fuori.write(json.dumps(coda, ensure_ascii=False) + "\n")
        fuori.close()
    print(json.dumps({"campioni": len(campioni), "eventi": len(eventi),
                      "qdisc_dopo": rimessa, "uscita": a.uscita}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
