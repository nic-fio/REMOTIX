#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b9d-dove-sono-fermi — ⭐⭐ DOVE STANNO ASPETTANDO I FIGLI, in questo istante.

⛔ E' la misura che decide fra le due spiegazioni del dirupo, e le decide senza
   passare dal registro:

   · se i thread dei figli stanno dentro `sendto`/`sendmsg` ⇒ **contropressione
     del padre**: il `send()` verso il padre e' bloccante e senza scadenza
     (`figlio.c:2741`), e finche' e' li' dentro la cattura e' ferma con lui;
   · se stanno dentro `ioctl` su un nodo `/dev/dri/*` ⇒ **attesa sulla GPU**:
     e' il `vaSyncSurface` del VPP (`codificatore.c:3335`), bloccante e senza
     scadenza sul motore RENDER;
   · se stanno in `ppoll`/`futex` ⇒ stanno aspettando qualcosa che non arriva —
     tipicamente un fotogramma dal compositore.

⭐ E si guarda OGNI THREAD, non il solo processo: PipeWire ne ha di suoi, e il
   thread che aspetta non e' quello che ha il pid.

⛔ `None` non e' zero: un thread di cui non si e' letto lo stato si conta a
   parte e si dichiara.  ⚠ E la lettura di `/proc/<pid>/syscall` e' una
   fotografia: un thread che passa di li' in un microsecondo non ci sara' quasi
   mai.  ⇒ Si campiona piu' volte e si conta **in quale stato si e' trovato**,
   che e' una frequenza, non una prova.

uso (da root):  10-b9d-dove-sono-fermi.py <modello> [campioni] [pausa_s]
                modello: la parte di `comm` da cercare, es. `remotix-figlio`
"""
import json
import os
import sys
import time

MODELLO = sys.argv[1] if len(sys.argv) > 1 else "remotix"
CAMPIONI = int(sys.argv[2]) if len(sys.argv) > 2 else 12
PAUSA = float(sys.argv[3]) if len(sys.argv) > 3 else 0.4

# I numeri delle chiamate di sistema che contano, su x86-64.  ⛔ Si scrivono
# per numero E per nome: `/proc/<pid>/syscall` da' il numero, e un banco che
# stampasse «44» non direbbe niente a chi legge.
NOMI = {0: "read", 1: "write", 7: "poll", 16: "ioctl", 23: "select",
        44: "sendto", 45: "recvfrom", 46: "sendmsg", 47: "recvmsg",
        202: "futex", 232: "epoll_wait", 271: "ppoll", 281: "epoll_pwait",
        61: "wait4", 35: "nanosleep", 230: "clock_nanosleep",
        270: "pselect6", 302: "prlimit64"}


def leggi(p):
    try:
        with open(p) as f:
            return f.read()
    except Exception:
        return None


def fd_di(pid, n):
    try:
        return os.readlink("/proc/%s/fd/%s" % (pid, n))
    except Exception:
        return None


conti = {}
non_letti = 0
processi = {}

for c in range(CAMPIONI):
    for n in os.listdir("/proc"):
        if not n.isdigit():
            continue
        comm = (leggi("/proc/%s/comm" % n) or "").strip()
        if MODELLO not in comm:
            cmd = (leggi("/proc/%s/cmdline" % n) or "").replace("\x00", " ")
            if MODELLO not in cmd:
                continue
        processi.setdefault(n, comm)
        try:
            task = os.listdir("/proc/%s/task" % n)
        except Exception:
            non_letti += 1
            continue
        for t in task:
            s = leggi("/proc/%s/task/%s/syscall" % (n, t))
            tcomm = (leggi("/proc/%s/task/%s/comm" % (n, t)) or "?").strip()
            if not s:
                non_letti += 1
                continue
            p = s.split()
            if not p:
                non_letti += 1
                continue
            if p[0] == "running":
                chiave = "(in esecuzione)"
            elif p[0] == "-1":
                chiave = "(non bloccato in una chiamata)"
            else:
                try:
                    num = int(p[0])
                except ValueError:
                    non_letti += 1
                    continue
                nome = NOMI.get(num, "syscall_%d" % num)
                # ⭐ E per `ioctl` si dice SU QUALE FILE: un `ioctl` su
                #    `/dev/dri/renderD128` e un `ioctl` su un socket sono due
                #    diagnosi diverse sotto lo stesso nome.
                dove = ""
                if num in (16, 44, 45, 46, 47, 0, 1) and len(p) > 1:
                    try:
                        fd = int(p[1], 16)
                        b = fd_di(n, fd) or fd_di("%s/task/%s" % (n, t), fd)
                        if b:
                            dove = " su " + ("/dev/dri/*" if "/dev/dri/" in b
                                             else ("socket" if b.startswith("socket:")
                                                   else b[:40]))
                    except (ValueError, IndexError):
                        pass
                chiave = nome + dove
            conti.setdefault(tcomm, {})
            conti[tcomm][chiave] = conti[tcomm].get(chiave, 0) + 1
    if c < CAMPIONI - 1:
        time.sleep(PAUSA)

print(json.dumps({"modello": MODELLO, "campioni": CAMPIONI, "pausa_s": PAUSA,
                  "processi": processi, "thread_non_letti": non_letti,
                  "dove": conti}, ensure_ascii=False))
