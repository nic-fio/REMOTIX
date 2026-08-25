#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b9d-chi-tiene-la-gpu — l'occupazione della GPU **PER PROGRAMMA**.

⛔ PERCHE' NON BASTAVA QUEL CHE C'ERA.  `10-b92-sonda.py` somma i motori per
   MACCHINA e per UID, e `10-b87-metro-gpu.py` sa fare il per-pid ma va chiamato
   a parte (due letture sue, in due istanti suoi).  ⭐ La domanda del dirupo non
   e' *«quanto e' occupato il motore render»* — quello e' gia' misurato, 99,5 % —
   ma **CHI lo tiene**: il compositore di ciascun utente, la scena del banco, o
   il figlio che converte i colori e codifica.  Tre risposte diverse, tre
   meccanismi diversi, e la colonna `GPU video` che crolla dice che il terzo non
   sta lavorando.

⛔⛔ E IL DELTA SI FA PER CONTESTO, non per programma: `drm-engine-*` sono
    cumulativi **per contesto DRM**, e il contesto muore col processo.  Sommare
    due totali presi su due platee diverse non da' il lavoro fatto (`10-b92`,
    riquadro di `fra()`: al gradino 1 diede **−76 %**).  ⇒ Qui si tiene il
    cumulativo per contesto, si dice a quale programma appartiene, e il
    raggruppamento per programma si fa DOPO la sottrazione, sui contesti
    presenti in tutt'e due le fotografie.

⛔ Deduplicazione per `(pdev, drm-client-id)`: lo stesso contesto compare su piu'
   descrittori (`[M]` `gnome-shell` con quattro fd sullo stesso client-id).

⛔ Va eseguito DA ROOT: gli `fdinfo` altrui non si leggono da utente, e una
   lettura NEGATA non e' una lettura che dice zero.  Il conto di quel che non si
   e' letto esce nel risultato.

uso:  10-b9d-chi-tiene-la-gpu.py <pdev> [uid1,uid2,...]
"""
import json
import os
import sys
import time

PDEV = sys.argv[1] if len(sys.argv) > 1 else "0000:00:02.0"
UID_MIEI = set(int(x) for x in (sys.argv[2].split(",")
                                if len(sys.argv) > 2 and sys.argv[2] else []))


def leggi(p):
    try:
        with open(p) as f:
            return f.read()
    except Exception:
        return None


def uid_di(pid):
    t = leggi("/proc/%d/status" % pid)
    if not t:
        return None
    for r in t.splitlines():
        if r.startswith("Uid:"):
            return int(r.split()[1])
    return None


t0 = time.clock_gettime(time.CLOCK_MONOTONIC)
per_contesto = {}      # cid → {"chi": comm, "pid": .., "uid": .., motore: ns}
capacita = {}
visti = set()
altri_pdev = {}
fd_trovati = fd_non_letti = pid_non_letti = 0

for n in os.listdir("/proc"):
    if not n.isdigit():
        continue
    pid = int(n)
    try:
        fds = os.listdir("/proc/%d/fd" % pid)
    except Exception:
        pid_non_letti += 1
        continue
    for fd in fds:
        try:
            b = os.readlink("/proc/%d/fd/%s" % (pid, fd))
        except Exception:
            continue
        if "/dev/dri/" not in b:
            continue
        fd_trovati += 1
        t = leggi("/proc/%d/fdinfo/%s" % (pid, fd))
        if not t:
            fd_non_letti += 1
            continue
        campi = {}
        for r in t.splitlines():
            k, _, v = r.partition(":")
            campi[k.strip()] = v.strip()
        pdev, cid = campi.get("drm-pdev"), campi.get("drm-client-id")
        if not pdev or not cid:
            fd_non_letti += 1
            continue
        if pdev != PDEV:
            # ⛔ La discreta e' chiusa da udev (`DECISIONI.md` §4.6-quinquies):
            #    si DICHIARA e non si somma.
            altri_pdev[pdev] = altri_pdev.get(pdev, 0) + 1
            continue
        if (pdev, cid) in visti:
            continue
        visti.add((pdev, cid))
        comm = (leggi("/proc/%d/comm" % pid) or "?").strip()
        u = uid_di(pid)
        voce = {"chi": comm, "pid": pid, "uid": u, "mio": u in UID_MIEI}
        for k, v in campi.items():
            if k.startswith("drm-engine-capacity-"):
                m = k[len("drm-engine-capacity-"):]
                try:
                    capacita[m] = max(capacita.get(m, 1), int(v.split()[0]))
                except (ValueError, IndexError):
                    pass
                continue
            if k.startswith("drm-engine-"):
                m = k[len("drm-engine-"):]
                p = v.split()
                voce[m] = int(p[0]) if p and p[0].isdigit() else 0
        per_contesto[cid] = voce

print(json.dumps({
    "t_ms": ((t0 + time.clock_gettime(time.CLOCK_MONOTONIC)) / 2.0) * 1000.0,
    "pdev": PDEV, "radice": os.geteuid() == 0,
    "per_contesto": per_contesto, "capacita": capacita,
    "contesti": len(per_contesto), "altri_pdev": altri_pdev,
    "fd_trovati": fd_trovati, "fd_non_letti": fd_non_letti,
    "pid_non_letti": pid_non_letti,
    "costo_ms": round((time.clock_gettime(time.CLOCK_MONOTONIC) - t0) * 1000, 1),
}))
