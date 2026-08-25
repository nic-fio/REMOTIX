#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b89-agente — IL CAMPIONATORE.  Gira SULLA MACCHINA DI PROVA, da root.

⛔ PERCHE' STA QUI E NON NEL BANCO.  Le quattro grandezze del costo di una
   sessione — memoria, GPU, CPU, filo — si leggono da `/proc`, e leggerle da
   fuori vorrebbe dire un `ssh` per campione: il costo dello strumento
   diventerebbe piu' grande di quel che misura.  ⇒ un solo `ssh`, un processo
   che campiona in loco, e un `jsonl` che torna indietro.

═══ ⛔ «NONE NON E' ZERO» — la regola che governa ogni lettura di questo file
   (`LEZIONI.md` §1.29 corollario 1).  Ogni lettore torna **None** quando non
   ha potuto leggere, e il conteggio dei letti/mancati viaggia accanto al
   numero.  «Il gruppo non consuma niente» e «non ho potuto guardare» non
   devono mai avere la stessa faccia.

═══ ⭐ I GRUPPI, e perche' sono cinque e non due ════════════════════════════
   · `padre`   — i processi `<albero>/src/remotix`: il server.  **Uno solo**
                 per macchina: nel conto per dieci sessioni si conta UNA volta;
   · `figlio`  — `remotix-figlio --figlio-interno`: **uno per sessione**;
   · `grafica` — tutto il resto dell'uid della sessione: `gnome-shell`,
                 PipeWire, WirePlumber, i portali, i `gsd-*`.  ⭐ E' la parte
                 grossa, quella che `DECISIONI.md` §4.6 stimava a ~1,2 GB per
                 sessione **senza averla mai misurata**;
   · `scena`   — `04-b30-scena` e il browser: ⛔ e' **il carico**, non il
                 costo del prodotto.  Contarlo dentro la sessione gonfierebbe
                 il budget di una cosa che, in una sessione vera, e' il lavoro
                 dell'utente;
   · `cliente` — `01-b3-cliente.py` dentro il contenitore: sta sulla stessa
                 macchina per comodita' del banco, e **non e' costo del
                 server**.  Si misura apposta per poterlo sottrarre.

═══ ⭐ LA MEMORIA SI LEGGE IN PSS E USS, NON SOLO IN RSS ════════════════════
   ⛔ Dieci figli condividono le stesse librerie: sommare dieci RSS conta dieci
   volte le stesse pagine.  ⇒ `smaps_rollup` da' Rss, Pss e Private_* (USS), e
   il banco moltiplica per dieci **l'USS**, non l'RSS.

═══ ⭐ LA GPU SI LEGGE IN `/proc/<pid>/fdinfo`, E SI DEDUPLICA ══════════════
   ⛔ `drm-engine-*` e' per **cliente DRM**, non per descrittore: due `fd`
   duplicati portano lo stesso `drm-client-id` e lo stesso contatore.  Sommarli
   raddoppierebbe.  ⇒ si deduplica su `(drm-pdev, drm-client-id)`.
   ⛔ E si guarda **solo** l'integrata (`DECISIONI.md` §4.6-quinquies): un
   contatore che venisse da `0000:03:00.0` sarebbe la Radeon, e va dichiarato,
   non sommato.

Uso (da root, sulla macchina):
    python3 10-b89-agente.py --uid 1100 --albero /media/REMOTIX/src/10a3-src \
        --secondi 30 --uscita /media/REMOTIX/tmp/10a3/b89-continuo.jsonl
"""
import argparse, json, os, sys, time

HZ = os.sysconf("SC_CLK_TCK")
PAGINA = os.sysconf("SC_PAGE_SIZE")
PDEV_INTEGRATA = "0000:00:02.0"          # Intel UHD 730 — l'unica su cui si misura
GRUPPI = ("padre", "figlio", "grafica", "scena", "cliente", "agente", "taratura")


# ── chi e' chi ─────────────────────────────────────────────────────────────
def leggi(percorso):
    """⛔ Torna None se non ha potuto leggere.  Mai "" e mai 0."""
    try:
        with open(percorso, "rb") as f:
            return f.read().decode("utf-8", "replace")
    except (OSError, IOError):
        return None


def uid_di(pid):
    t = leggi("/proc/%d/status" % pid)
    if t is None:
        return None
    for r in t.splitlines():
        if r.startswith("Uid:"):
            return int(r.split()[1])
    return None


def censimento(uid_sessione, albero, mio_pid):
    """Torna {pid: gruppo}.  ⛔ Rifatto a ogni campione: i processi di una
       sessione nascono e muoiono, e una lista presa una volta sola
       misurerebbe la sessione di dieci secondi fa."""
    fuori = {}
    for nome in os.listdir("/proc"):
        if not nome.isdigit():
            continue
        pid = int(nome)
        cmd = leggi("/proc/%d/cmdline" % pid)
        if cmd is None:
            continue                       # e' morto mentre lo guardavo
        cmd = cmd.replace("\0", " ").strip()
        if pid == mio_pid:
            fuori[pid] = "agente"
            continue
        u = uid_di(pid)
        if u == uid_sessione:
            if "remotix-figlio" in cmd:
                fuori[pid] = "figlio"
            elif "04-b30-scena" in cmd or "firefox" in cmd:
                fuori[pid] = "scena"
            else:
                fuori[pid] = "grafica"
        elif albero + "/src/remotix" in cmd:
            fuori[pid] = "padre"
        elif "01-b3-cliente.py" in cmd:
            fuori[pid] = "cliente"
        elif "ffmpeg" in cmd:
            # ⭐ Il carico NOTO della taratura del metro di GPU (`LEZIONI.md`
            #    §1.33): non e' ne' prodotto ne' sessione, e sta in un gruppo
            #    suo perche' il banco possa leggerlo senza confonderlo.
            fuori[pid] = "taratura"
    return fuori


# ── CPU: utime + stime, in tacche ─────────────────────────────────────────
def tacche(pid):
    t = leggi("/proc/%d/stat" % pid)
    if t is None:
        return None
    # ⛔ Il nome del comando sta fra parentesi e puo' contenere spazi: si
    #    taglia dopo l'ULTIMA ')', o `nautilus (deleted)` sposta tutti i campi.
    try:
        resto = t[t.rindex(")") + 2:].split()
        return int(resto[11]) + int(resto[12])          # utime, stime
    except (ValueError, IndexError):
        return None


# ── memoria: RSS, PSS, USS ────────────────────────────────────────────────
def memoria_pid(pid, rotto=False):
    """⛔ `smaps_rollup` o niente: `statm` non sa dire PSS, e senza PSS dieci
       sessioni si contano dieci volte le stesse librerie."""
    percorso = "/proc/%d/smaps_rollup" % pid if not rotto \
        else "/proc/%d/smaps_rollup_INESISTENTE" % pid
    t = leggi(percorso)
    if t is None:
        return None
    d = {}
    for r in t.splitlines():
        p = r.split()
        if len(p) >= 2 and p[0].endswith(":"):
            try:
                d[p[0][:-1]] = int(p[1])
            except ValueError:
                pass
    if "Pss" not in d or "Rss" not in d:
        return None
    return {"rss_kb": d["Rss"], "pss_kb": d["Pss"],
            "uss_kb": d.get("Private_Clean", 0) + d.get("Private_Dirty", 0),
            "swap_kb": d.get("Swap", 0)}


def memoria_gruppi(censo, rotto=False):
    fuori = {g: {"rss_kb": 0, "pss_kb": 0, "uss_kb": 0, "swap_kb": 0,
                 "letti": 0, "mancati": 0, "pidi": []} for g in GRUPPI}
    for pid, g in censo.items():
        m = memoria_pid(pid, rotto)
        if m is None:
            fuori[g]["mancati"] += 1
            continue
        for k in ("rss_kb", "pss_kb", "uss_kb", "swap_kb"):
            fuori[g][k] += m[k]
        fuori[g]["letti"] += 1
        fuori[g]["pidi"].append(pid)
    # ⛔ Zero letture = None, non zero byte.
    for g in GRUPPI:
        if fuori[g]["letti"] == 0:
            fuori[g] = {"misurato": None, "mancati": fuori[g]["mancati"]}
    return fuori


# ── GPU: `drm-engine-*` dedotto per CLIENTE, non per descrittore ──────────
def clienti_drm(pid, rotto=False):
    """Torna {(pdev, client_id): {motore: ns}} oppure None se non ho letto."""
    if rotto:
        return None
    try:
        fdi = os.listdir("/proc/%d/fd" % pid)
    except (OSError, IOError):
        return None
    fuori, visto_qualcosa = {}, False
    for fd in fdi:
        try:
            b = os.readlink("/proc/%d/fd/%s" % (pid, fd))
        except (OSError, IOError):
            continue
        if not b.startswith("/dev/dri/"):
            continue
        t = leggi("/proc/%d/fdinfo/%s" % (pid, fd))
        if t is None:
            continue
        visto_qualcosa = True
        pdev, cid, motori = None, None, {}
        for r in t.splitlines():
            if r.startswith("drm-pdev:"):
                pdev = r.split(":", 1)[1].strip()
            elif r.startswith("drm-client-id:"):
                cid = r.split(":", 1)[1].strip()
            elif r.startswith("drm-engine-") and r.rstrip().endswith("ns"):
                nome = r.split(":", 1)[0][len("drm-engine-"):]
                try:
                    motori[nome] = int(r.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
        if pdev is None or cid is None:
            continue
        fuori[(pdev, cid)] = motori
    # ⛔ Un dizionario VUOTO e' una risposta («questo processo non tocca la
    #    GPU»); `None` e' l'assenza di risposta («non ho potuto guardare»), e
    #    l'ha gia' tornato il `return` sopra.  Le due cose non si mescolano.
    _ = visto_qualcosa
    return fuori


# ── ⛔⛔ IL CONTESTO DELLA GT — senza, l'occupazione e' un numero senza unita'
#
# `banchi/10-b87-metro-gpu.py` §CLOCK (agente A1, 24 agosto 2026) misura che la
# **stessa identica codifica** da' `[M]` **26,35 %** con la GT bloccata a 300 MHz
# e **6,99 %** a 1550 MHz: un fattore **3,8**.  `drm-engine-*` conta TEMPO
# OCCUPATO, non lavoro fatto, e il governatore muove la frequenza col carico.
# ⇒ ogni occupazione che esce da qui porta accanto la frequenza a cui e' stata
#   letta, e chi la moltiplica per dieci deve saperlo.
GT = "/sys/class/drm/card0"


def gt_stato():
    d = {}
    for chiave, file_ in (("cur_mhz", "gt_cur_freq_mhz"), ("act_mhz", "gt_act_freq_mhz"),
                          ("min_mhz", "gt_min_freq_mhz"), ("max_mhz", "gt_max_freq_mhz"),
                          ("rc6_ms", "power/rc6_residency_ms")):
        t = leggi(GT + "/" + file_)
        try:
            d[chiave] = int(t.strip()) if t is not None else None
        except ValueError:
            d[chiave] = None
    return d


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--uid", type=int, required=True)
    p.add_argument("--albero", required=True)
    p.add_argument("--secondi", type=float, default=30.0)
    p.add_argument("--intervallo", type=float, default=1.0)
    p.add_argument("--uscita", required=True)
    # ⛔ I due guasti innestabili, che servono a `--certifica` del banco:
    #    il lettore della memoria e quello della GPU senza permessi.
    p.add_argument("--memoria-rotta", action="store_true")
    p.add_argument("--gpu-rotta", action="store_true")
    a = p.parse_args()

    mio = os.getpid()
    censo = censimento(a.uid, a.albero, mio)
    t0 = time.time()
    fuori = open(a.uscita, "w")

    def riga(d):
        fuori.write(json.dumps(d, ensure_ascii=False) + "\n")
        fuori.flush()

    def filo_lo():
        t = leggi("/proc/net/dev")
        if t is None:
            return None
        for r in t.splitlines():
            if r.strip().startswith("lo:"):
                c = r.split(":", 1)[1].split()
                return {"rx_byte": int(c[0]), "rx_pac": int(c[1]),
                        "tx_byte": int(c[8]), "tx_pac": int(c[9])}
        return None

    riga({"che": "intestazione", "ancora_epoch": t0,
          "ancora_locale": time.strftime("%H:%M:%S", time.localtime(t0))
                           + ".%03d" % int((t0 % 1) * 1000),
          "uid": a.uid, "albero": a.albero, "hz": HZ,
          "cpu_filati": os.cpu_count(), "pdev_integrata": PDEV_INTEGRATA,
          "memoria_rotta": a.memoria_rotta, "gpu_rotta": a.gpu_rotta,
          "memoria_inizio": memoria_gruppi(censo, a.memoria_rotta),
          "filo_inizio": filo_lo(), "gt_inizio": gt_stato(),
          "censo_inizio": {g: sum(1 for x in censo.values() if x == g) for g in GRUPPI}})

    # gli accumulatori: si sommano i DELTA per processo, cosi' un processo che
    # nasce o muore a meta' giro non fa un salto nel conto del gruppo.
    gt_serie = []
    cpu_tot = {g: 0 for g in GRUPPI}
    cpu_letti = {g: 0 for g in GRUPPI}
    cpu_mancati = {g: 0 for g in GRUPPI}
    gpu_tot = {g: {} for g in GRUPPI}
    gpu_letture_ok = 0
    gpu_altre_schede = {}
    prec_cpu, prec_gpu = {}, {}
    n_campioni = 0

    fine = t0 + a.secondi
    while time.time() < fine:
        censo = censimento(a.uid, a.albero, mio)
        ora = time.time()
        for pid, g in censo.items():
            t = tacche(pid)
            if t is None:
                cpu_mancati[g] += 1
            else:
                if pid in prec_cpu and t >= prec_cpu[pid]:
                    cpu_tot[g] += t - prec_cpu[pid]
                prec_cpu[pid] = t
                cpu_letti[g] += 1
            cl = clienti_drm(pid, a.gpu_rotta)
            if cl is None:
                continue
            gpu_letture_ok += 1
            for (pdev, cid), motori in cl.items():
                if pdev != PDEV_INTEGRATA:
                    gpu_altre_schede[pdev] = gpu_altre_schede.get(pdev, 0) + 1
                    continue
                for nome, ns in motori.items():
                    chiave = (cid, nome)
                    if chiave in prec_gpu and ns >= prec_gpu[chiave]:
                        gpu_tot[g][nome] = gpu_tot[g].get(nome, 0) + ns - prec_gpu[chiave]
                    else:
                        gpu_tot[g].setdefault(nome, 0)
                    prec_gpu[chiave] = ns
        n_campioni += 1
        gt = gt_stato()
        if gt.get("act_mhz") is not None:
            gt_serie.append(gt["act_mhz"])
        riga({"che": "campione", "t": ora, "n": n_campioni, "gt": gt,
              "cpu_tacche": dict(cpu_tot), "gpu_ns": {g: dict(v) for g, v in gpu_tot.items()},
              "filo": filo_lo(),
              "censo": {g: sum(1 for x in censo.values() if x == g) for g in GRUPPI}})
        d = a.intervallo - (time.time() - ora)
        if d > 0:
            time.sleep(d)

    t1 = time.time()
    censo = censimento(a.uid, a.albero, mio)
    riga({"che": "coda", "t": t1, "durata_s": t1 - t0, "campioni": n_campioni,
          "memoria_fine": memoria_gruppi(censo, a.memoria_rotta),
          "filo_fine": filo_lo(), "gt_fine": gt_stato(),
          "gt_act_mhz": {"n": len(gt_serie),
                         "media": round(sum(gt_serie) / len(gt_serie)) if gt_serie else None,
                         "min": min(gt_serie) if gt_serie else None,
                         "max": max(gt_serie) if gt_serie else None},
          "cpu_tacche": dict(cpu_tot), "cpu_letti": dict(cpu_letti),
          "cpu_mancati": dict(cpu_mancati),
          "gpu_ns": {g: dict(v) for g, v in gpu_tot.items()},
          "gpu_letture_ok": gpu_letture_ok,
          "gpu_altre_schede": gpu_altre_schede,
          "censo_fine": {g: sum(1 for x in censo.values() if x == g) for g in GRUPPI}})
    fuori.close()
    print("AGENTE FINITO: %d campioni in %.1f s" % (n_campioni, t1 - t0))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
