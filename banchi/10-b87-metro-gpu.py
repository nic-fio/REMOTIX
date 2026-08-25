#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b87-metro-gpu — IL METRO DELL'OCCUPAZIONE DEI MOTORI DELLA GPU (Intel i915).

⭐ PERCHE' ESISTE.  Il budget della fase 10 e' un budget di **GPU**: quanti
   pixel al secondo regge la Intel UHD 730 (`/dev/dri/renderD128`, `i915`).
   ⛔ Ma prima di misurare quanto la GPU regge serve un metro che dica quanto
   la GPU **sta lavorando** — e su questa macchina `intel_gpu_top` NON c'e'.

⭐ LA STRADA SCELTA, e non chiede pacchetti nuovi: `/proc/<pid>/fdinfo/<fd>`.
   `[M]` Verificato **guardando il file** sulla macchina di prova (kernel 7.0,
   i915, i5-13500T / UHD 730), non la documentazione.  Le chiavi che quel
   kernel espone davvero, per ogni fd aperto su `/dev/dri/renderD128`:

       drm-driver:                 i915
       drm-client-id:              549
       drm-pdev:                   0000:00:02.0
       drm-total-system0:          80244 KiB      (e -shared-/-active-/-resident-/-purgeable-)
       drm-total-stolen-system0:   0              (e le stesse quattro varianti)
       drm-engine-render:          0 ns
       drm-engine-copy:            0 ns
       drm-engine-video:           1312186876 ns  ⭐ il motore di CODIFICA (VDBOX)
       drm-engine-capacity-video:  2              ⚠ i VDBOX sono DUE
       drm-engine-video-enhance:   0 ns

   Sono **nanosecondi cumulativi per cliente**: due letture a distanza nota
   danno la percentuale.  Non e' servita nessuna delle alternative:
   ⛔ `/sys/class/drm/card*/clients` su questo kernel **non esiste**
   (`ls` → «No such file or directory»), e `perf_event_open` su
   `i915/vcs0-busy/` e `debugfs` non sono stati usati.

⚠ LE DUE PERCENTUALI, e vanno tenute distinte:
   - `video_pct`     = ns/dt · 100  → **motori-equivalenti** ×100.  Con
                       `capacita_video = 2` il massimo e' **200 %**, non 100 %.
   - `video_uso_pct` = `video_pct` / capacita → **frazione della capacita'
                       video totale** della scheda, 0..100 %.
   ⛔ Chi confonde le due sbaglia il budget di un fattore due.

═══════════════════════════════════════════════════════════════════════════
⛔⛔ §CLOCK — LA COSA PIU' IMPORTANTE DI QUESTO FILE
═══════════════════════════════════════════════════════════════════════════

⛔ `drm-engine-video` conta **TEMPO OCCUPATO**, non **LAVORO FATTO**.  E il
   tempo che un fotogramma tiene il motore dipende dalla **frequenza della
   GT**, che il governatore muove col carico.  ⇒ **La stessa identica codifica
   dà percentuali diverse a frequenze diverse.**

`[M]` Misurato il 24 agosto 2026, i5-13500T / UHD 730, **una sola** codifica
   `h264_vaapi` 1080p30, **30,9 fps consegnati in tutt'e due i casi**
   (495 fotogrammi, contati dal `-progress` di ffmpeg):

       GT bloccata a  300 MHz  →  video = **26,35 %**
       GT bloccata a 1550 MHz  →  video =  **6,99 %**
       ────────────────────────────────────────────  fattore **3,8×**

⛔⛔ LA CONSEGUENZA PER IL BUDGET DELLA FASE 10: **estrapolare la capienza
   della GPU da un carico leggero è sbagliato fino a un fattore quattro**.  A
   carico leggero il governatore tiene la GT bassa, ogni fotogramma occupa più
   tempo, e l'occupazione letta è **troppo alta**.  ⇒ Il numero di pixel/s che
   la macchina regge **si misura al punto di saturazione**, non si ricava da
   una retta tirata su una sola codifica.

⭐ Per questo ogni lettura porta accanto il **contesto GT**: frequenza chiesta,
   minimo e massimo (e se sono uguali, la GT è **bloccata**), e la residenza
   in **RC6** — cioè quanto la GT è stata del tutto spenta.  `100 − RC6` è una
   **seconda misura, indipendente dai fdinfo**, e fa da tetto superiore
   all'occupazione totale della scheda.

═══════════════════════════════════════════════════════════════════════════
COME SI USA
═══════════════════════════════════════════════════════════════════════════

Da Python (e' il modo pensato per gli altri banchi della fase 10):

    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "metro", "banchi/10-b87-metro-gpu.py")
    metro = importlib.util.module_from_spec(spec); spec.loader.exec_module(metro)

    m = metro.misura(secondi=2.0)          # None se non ha potuto misurare
    if m is None:
        ...⛔ mi rifiuto di giudicare...
    else:
        m["macchina"]["video_pct"]         # tutta la macchina
        m["per_pid"][12345]["video_pct"]   # solo quel processo
        m["macchina"]["parziale"]          # ⚠ True = e' un limite INFERIORE

    a = metro.leggi_istantanea();  ...;  b = metro.leggi_istantanea()
    m = metro.confronta(a, b)              # le due letture le prendi tu

Da riga di comando:

    python3 banchi/10-b87-metro-gpu.py --una-lettura [--secondi 2]
    python3 banchi/10-b87-metro-gpu.py --per-secondi 30 [--ogni 1]
    python3 banchi/10-b87-metro-gpu.py --certifica          # ⛔ i guasti innestati
    sudo python3 banchi/10-b87-metro-gpu.py --tara          # la taratura completa
    sudo python3 banchi/10-b87-metro-gpu.py --tara-clock    # ⛔⛔ la prova §CLOCK

⛔⛔ `--tara` e `--tara-clock` METTONO CARICO SULLA GPU: prima si prende il
   lucchetto (`banchi/09-lucchetto.py`, nome `LUCCHETTO=…/.lucchetto-gpu.d`),
   o si falsa la misura di chiunque altro stia misurando (`LEZIONI.md` §1.26).

⚠ PER VEDERE TUTTA LA MACCHINA SERVE ROOT.  Da utente normale `/proc/<pid>/fd`
   degli altri utenti non si legge: `gnome-shell` della sessione grafica NON
   viene contato e il totale esce **parziale** (lo dice, non lo nasconde).

═══════════════════════════════════════════════════════════════════════════
⛔ CHE COSA QUESTO METRO **NON** SA DIRE
═══════════════════════════════════════════════════════════════════════════

0. ⛔⛔ **Non dice quanto LAVORO e' stato fatto**, ma quanto TEMPO i motori
   sono stati occupati — e quel tempo dipende dalla frequenza della GT: vedi
   il **§CLOCK** qui sopra, e' un fattore **3,8** su questa macchina.
1. ⛔ **Non dice se la GPU e' satura.**  Dice quanto tempo i motori sono stati
   occupati, non se il lavoro era in coda.  Occupazione 60 % + latenza in
   crescita e occupazione 60 % + latenza piatta hanno lo stesso numero.
2. ⛔ **Non separa codifica da decodifica**: `drm-engine-video` e' il VDBOX, e
   il VDBOX fa tutt'e due.  Su un processo che solo codifica il numero e' la
   codifica; su `gnome-shell` o un browser puo' essere altro.
3. ⛔ **Non misura la banda di memoria ne' la frequenza della GPU**: due carichi
   con la stessa occupazione possono costare energia diversa.
4. ⛔ **Non vede chi non ha un fd aperto**: lavoro sottomesso da un processo
   gia' uscito, o dal firmware, non compare.
5. ⛔ **Non e' un campionamento ad alta frequenza**: sotto ~200 ms di distanza
   fra le due letture il rumore di scansione (~10 ms su 1000 processi) pesa.
   ⇒ Il minimo consigliato e' **1 s**; sotto 0,2 s si rifiuta.
6. ⚠ **Il render della UHD 730 sotto una sessione GNOME non e' zero**: il
   totale macchina comprende il compositore, che non e' il tuo carico.  Per il
   tuo carico usa `per_pid`.
7. ⛔ **Non guarda la Radeon** (`renderD129`, `amdgpu`): e' chiusa apposta
   (`DECISIONI.md` §4.6-quinquies).  Il filtro e' sul `drm-pdev` del nodo
   scelto, non sul nome del driver.

⛔⛔ E LA REGOLA CHE VIENE PRIMA DI TUTTE: `None` NON E' ZERO.  Un permesso
   negato, un fd sparito, un processo morto fra le due letture, un contatore
   che va indietro sono tutti «non ho misurato», e questo metro torna `None`.
   Chi lo usa deve **rifiutarsi di giudicare**, non leggere 0 %.
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import time

# ───────────────────────────────────────────────────────────────────────────
# Le costanti della macchina di prova.  Nessuna e' cablata: si ricavano.
# ───────────────────────────────────────────────────────────────────────────

NODO_PREDEFINITO = "/dev/dri/renderD128"     # ⛔ la INTEGRATA, mai la discreta
DISTANZA_MINIMA = 0.2                        # s fra le due letture
MOTORI = ("render", "copy", "video", "video-enhance")

# ⭐ Il contesto che spiega la lettura: la frequenza della GT e il tempo in RC6.
#    Senza questi, una percentuale di occupazione e' ambigua (vedi il §CLOCK
#    in testa a questo file).
SYS_GT = "/sys/class/drm/card0"
SYS_GT0 = "/sys/class/drm/card0/gt/gt0"


class Guasto(Exception):
    """Innestato solo da `--certifica`.  In esercizio non si alza mai."""


# ⛔ Punto d'innesto del guasto G1: `--certifica` lo sostituisce.
_LEGGI = None


def _leggi_testo(percorso):
    """Torna il testo, oppure `None` se non si e' potuto leggere.
       ⛔ Non torna mai stringa vuota al posto di `None`."""
    try:
        if _LEGGI is not None:                # innesto di `--certifica`
            return _LEGGI(percorso)           # ⭐ dentro il try: un guasto
        with open(percorso, "rb") as f:       #    innestato si comporta come
            return f.read().decode("utf-8", "replace")   # un EACCES vero
    except Exception:
        return None


# ───────────────────────────────────────────────────────────────────────────
# Lettura
# ───────────────────────────────────────────────────────────────────────────

def pdev_del_nodo(nodo=NODO_PREDEFINITO):
    """Il `drm-pdev` (es. «0000:00:02.0») del nodo di rendering scelto.
       `None` se non si e' potuto stabilire — e allora NON si filtra a caso."""
    nome = os.path.basename(nodo)
    for base in ("/sys/class/drm/%s/device" % nome,):
        try:
            vero = os.path.realpath(base)
            pezzo = os.path.basename(vero)
            if re.fullmatch(r"[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-9]", pezzo):
                return pezzo
        except Exception:
            pass
    return None


def _avvio_di(pid):
    """Il tempo d'avvio del processo (campo 22 di /proc/pid/stat), in tick.
       ⭐ Serve a non scambiare un pid RICICLATO per lo stesso processo."""
    t = _leggi_testo("/proc/%d/stat" % pid)
    if t is None:
        return None
    try:
        # il nome del comando sta fra parentesi e puo' contenere spazi
        coda = t[t.rindex(")") + 1:].split()
        return int(coda[19])                  # campo 22 = 20° dopo la parentesi
    except Exception:
        return None


def _comm_di(pid):
    t = _leggi_testo("/proc/%d/comm" % pid)
    return t.strip() if t is not None else "?"


def _analizza_fdinfo(testo):
    """Da testo di fdinfo a dizionario di chiavi drm-*.  `None` se non e' un
       fdinfo di un cliente DRM."""
    if testo is None or "drm-driver" not in testo:
        return None
    d = {}
    for riga in testo.splitlines():
        if ":" in riga:
            k, v = riga.split(":", 1)
            d[k.strip()] = v.strip()
    return d


def _ns(d, chiave):
    """Nanosecondi da una chiave `drm-engine-*`.  `None` se manca o non e' un
       numero — ⛔ **non** 0."""
    v = d.get(chiave)
    if v is None:
        return None
    try:
        return int(v.split()[0])
    except (ValueError, IndexError):
        return None


def _kib_totali(d):
    """Somma di tutte le chiavi `drm-total-*` (KiB).  `None` se nessuna."""
    tot, viste = 0, 0
    for k, v in d.items():
        if k.startswith("drm-total-"):
            try:
                tot += int(v.split()[0]); viste += 1
            except (ValueError, IndexError):
                pass
    return tot if viste else None


def _intero(percorso):
    """Un intero da un file sysfs.  ⛔ `None` se non c'e' o non e' un numero."""
    t = _leggi_testo(percorso)
    if t is None:
        return None
    try:
        return int(t.strip())
    except ValueError:
        return None


def leggi_gt():
    """Il contesto della GT: frequenze e residenza in RC6 (cumulativa, ms).
       ⛔ Ogni voce e' `None` se non l'ha letta — mai 0."""
    return {"cur_mhz": _intero(SYS_GT + "/gt_cur_freq_mhz"),
            "act_mhz": _intero(SYS_GT + "/gt_act_freq_mhz"),
            "min_mhz": _intero(SYS_GT + "/gt_min_freq_mhz"),
            "max_mhz": _intero(SYS_GT + "/gt_max_freq_mhz"),
            "rc6_ms": _intero(SYS_GT0 + "/rc6_residency_ms")}


def leggi_istantanea(nodo=NODO_PREDEFINITO, solo_pid=None, pdev=None):
    """Una fotografia dei contatori di TUTTI i clienti DRM della scheda scelta.

    Torna un dizionario, oppure ⛔ `None` se non ha potuto leggere:
      - `/proc` non elencabile, oppure
      - ha trovato fd DRM ma **nessuno** leggibile (permesso negato ovunque).

    ⚠ Non torna `None` quando i clienti sono legittimamente zero: quello e' un
      fatto misurato, e si distingue guardando `pid_non_letti`.
    """
    if pdev is None:
        pdev = pdev_del_nodo(nodo)
    try:
        cartelle = glob.glob("/proc/[0-9]*")
    except Exception:
        return None
    if not cartelle:
        return None

    clienti = {}
    pid_visti = 0
    pid_non_letti = 0
    fd_trovati = 0
    fd_non_letti = 0
    gt = leggi_gt()
    t0 = time.monotonic()

    for cart in cartelle:
        try:
            pid = int(os.path.basename(cart))
        except ValueError:
            continue
        if solo_pid is not None and pid not in solo_pid:
            continue
        pid_visti += 1
        try:
            fd = os.listdir(cart + "/fd")
        except Exception:
            pid_non_letti += 1               # ⛔ non e' «questo pid non usa la GPU»
            continue
        for n in fd:
            try:
                dove = os.readlink("%s/fd/%s" % (cart, n))
            except Exception:
                continue
            if not dove.startswith("/dev/dri/"):
                continue
            fd_trovati += 1
            d = _analizza_fdinfo(_leggi_testo("%s/fdinfo/%s" % (cart, n)))
            if d is None:
                fd_non_letti += 1
                continue
            if pdev is not None and d.get("drm-pdev") not in (None, pdev):
                continue                     # ⛔ un'altra scheda (la Radeon): fuori
            cid = d.get("drm-client-id")
            if cid is None:
                fd_non_letti += 1
                continue
            avvio = _avvio_di(pid)
            chiave = (pid, avvio, cid)       # ⭐ pid+avvio+cliente: niente scambi
            if chiave in clienti:
                continue                     # stesso cliente su piu' fd: uno solo
            voce = {"pid": pid, "cid": cid, "avvio": avvio,
                    "comm": _comm_di(pid), "driver": d.get("drm-driver"),
                    "pdev": d.get("drm-pdev"), "mem_kib": _kib_totali(d),
                    "capacita": {}}
            for mot in MOTORI:
                voce[mot] = _ns(d, "drm-engine-" + mot)
                cap = d.get("drm-engine-capacity-" + mot)
                if cap is not None:
                    try:
                        voce["capacita"][mot] = int(cap)
                    except ValueError:
                        pass
            clienti[chiave] = voce

    if fd_trovati and not clienti and fd_non_letti == fd_trovati:
        return None                          # ⛔ trovati, ma nessuno leggibile

    return {"t": (t0 + time.monotonic()) / 2.0,   # ⭐ il centro della scansione
            "durata_scansione": time.monotonic() - t0, "gt": gt,
            "clienti": clienti, "pdev": pdev, "nodo": nodo,
            "pid_visti": pid_visti, "pid_non_letti": pid_non_letti,
            "fd_trovati": fd_trovati, "fd_non_letti": fd_non_letti,
            "radice": (os.geteuid() == 0)}


# ───────────────────────────────────────────────────────────────────────────
# Confronto — ⭐ funzione PURA: nessuna lettura, quindi si puo' guastare a mano
# ───────────────────────────────────────────────────────────────────────────

def confronta(a, b):
    """Da due istantanee alla misura.  ⛔ `None` se non e' misurabile:
       una delle due manca, il tempo fra le due e' <= 0 o troppo corto."""
    if a is None or b is None:
        return None
    try:
        dt = float(b["t"]) - float(a["t"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (dt > 0.0):                        # ⛔ zero, negativo, NaN
        return None
    if dt < DISTANZA_MINIMA:
        return None                           # ⛔ troppo corto per valere

    per_cliente, per_pid = {}, {}
    spariti = nuovi = anomali = 0
    somma = {mot: 0.0 for mot in MOTORI}
    mancanti = {mot: 0 for mot in MOTORI}     # ⛔ clienti che NON ho misurato
    capacita = {}
    pezzi = {}                                # pid → motore → [valori o None]

    for chiave, vb in b["clienti"].items():
        for mot, c in vb["capacita"].items():
            capacita.setdefault(mot, c)
        va = a["clienti"].get(chiave)
        if va is None:
            nuovi += 1                        # ⭐ cliente ricreato / appena nato
            continue
        voce = {"pid": vb["pid"], "comm": vb["comm"], "cid": vb["cid"],
                "mem_kib": vb.get("mem_kib")}
        for mot in MOTORI:
            na, nb = va.get(mot), vb.get(mot)
            pct = None
            if na is None or nb is None:
                pass                          # ⛔ non misurato, non zero
            elif nb - na < 0:                 # ⛔ contatore all'indietro
                anomali += 1
            elif (nb - na) / (dt * 1e7) > 150.0 * max(1, vb["capacita"].get(mot, 1)):
                anomali += 1                  # ⛔ piu' del possibile: un salto
            else:
                pct = (nb - na) / (dt * 1e7)
            voce[mot + "_pct"] = pct
            if pct is None:
                mancanti[mot] += 1
            else:
                somma[mot] += pct
        per_cliente[chiave] = voce

        p = vb["pid"]
        d_pid = per_pid.setdefault(p, {"comm": vb["comm"], "clienti": 0,
                                       "mem_kib": 0})
        d_pid["clienti"] += 1
        if vb.get("mem_kib"):
            d_pid["mem_kib"] += vb["mem_kib"]
        for mot in MOTORI:
            pezzi.setdefault(p, {}).setdefault(mot, []).append(voce[mot + "_pct"])

    # ⛔ un pid con anche UN SOLO cliente non misurato non ha un totale: None
    for p, d_pid in per_pid.items():
        for mot in MOTORI:
            v = pezzi[p][mot]
            d_pid[mot + "_pct"] = None if any(x is None for x in v) else sum(v)

    for chiave in a["clienti"]:
        if chiave not in b["clienti"]:
            spariti += 1                      # ⛔ morto fra le due letture

    cap_video = capacita.get("video", 1) or 1
    perche = []
    if not b.get("radice", False):
        perche.append("non sono root: i processi di altri utenti non li vedo")
    if a["pid_non_letti"] or b["pid_non_letti"]:
        perche.append("%d processi non ispezionabili"
                      % max(a["pid_non_letti"], b["pid_non_letti"]))
    if a["fd_non_letti"] or b["fd_non_letti"]:
        perche.append("%d fd DRM non letti"
                      % max(a["fd_non_letti"], b["fd_non_letti"]))
    if spariti:
        perche.append("%d clienti spariti fra le due letture" % spariti)
    if nuovi:
        perche.append("%d clienti nuovi fra le due letture" % nuovi)
    if anomali:
        perche.append("%d contatori anomali (all'indietro o impossibili)" % anomali)
    if any(mancanti.values()):
        perche.append("%d clienti non misurati su qualche motore"
                      % max(mancanti.values()))

    macchina = {"parziale": bool(perche), "perche": perche,
                "clienti": len(per_cliente), "mancanti": mancanti}
    for mot in MOTORI:
        # ⛔ Un totale si dichiara SOLO se ogni cliente vivo e' stato misurato.
        #    Niente clienti misurati + qualcosa che non torna ⇒ None, non 0.
        if mancanti[mot] or (not per_cliente and perche):
            macchina[mot + "_pct"] = None
        else:
            macchina[mot + "_pct"] = somma[mot]
    macchina["video_uso_pct"] = (None if macchina["video_pct"] is None
                                 else macchina["video_pct"] / cap_video)

    # ⭐ Il CONTESTO, senza il quale la percentuale e' ambigua (vedi §CLOCK).
    #    `rc6_pct` e' una seconda misura INDIPENDENTE dalla somma dei fdinfo:
    #    quanto la GT e' stata del tutto spenta.  100 − rc6 e' un tetto
    #    superiore all'occupazione totale della scheda.
    ga = a.get("gt") or {}
    gb = b.get("gt") or {}
    rc6 = None
    if ga.get("rc6_ms") is not None and gb.get("rc6_ms") is not None:
        d = gb["rc6_ms"] - ga["rc6_ms"]
        if 0 <= d <= dt * 1000.0 * 1.05:      # ⛔ all'indietro o impossibile ⇒ None
            rc6 = d / (dt * 1000.0) * 100.0
    gt = {"rc6_pct": rc6,
          "sveglia_pct": None if rc6 is None else 100.0 - rc6,
          "cur_mhz": gb.get("cur_mhz"), "act_mhz": gb.get("act_mhz"),
          "min_mhz": gb.get("min_mhz"), "max_mhz": gb.get("max_mhz"),
          "bloccata": (gb.get("min_mhz") is not None
                       and gb.get("min_mhz") == gb.get("max_mhz"))}

    return {"dt": dt, "capacita_video": cap_video, "radice": b.get("radice"),
            "macchina": macchina, "per_pid": per_pid, "per_cliente": per_cliente,
            "spariti": spariti, "nuovi": nuovi, "anomali": anomali, "gt": gt,
            "pdev": b.get("pdev"), "nodo": b.get("nodo")}


def misura(secondi=1.0, nodo=NODO_PREDEFINITO, solo_pid=None):
    """Due letture a distanza `secondi`.  ⛔ `None` se non ha misurato."""
    if not (secondi >= DISTANZA_MINIMA):
        return None
    pdev = pdev_del_nodo(nodo)
    a = leggi_istantanea(nodo, solo_pid, pdev)
    if a is None:
        return None
    time.sleep(secondi)
    b = leggi_istantanea(nodo, solo_pid, pdev)
    return confronta(a, b)


# ───────────────────────────────────────────────────────────────────────────
# Stampa
# ───────────────────────────────────────────────────────────────────────────

def _n(v, largo=6):
    return ("%*.2f" % (largo, v)) if v is not None else ("%*s" % (largo, "None"))


def stampa(m, minimo=0.05):
    if m is None:
        print("   ⛔ ROSSO — non ho misurato (None).  Non giudico.")
        return
    mac = m["macchina"]
    marca = "[M]" if not mac["parziale"] else "[?]"
    print("   %s dt=%.3f s · capacita video=%d motori · %s (%s)"
          % (marca, m["dt"], m["capacita_video"], m["nodo"], m["pdev"]))
    print("       MACCHINA  video=%s%%  (= %s%% della capacita video)  "
          "render=%s%%  copy=%s%%  clienti=%d"
          % (_n(mac["video_pct"]), _n(mac["video_uso_pct"]),
             _n(mac["render_pct"]), _n(mac["copy_pct"]), mac["clienti"]))
    g = m.get("gt") or {}
    print("       GT        %s MHz chiesti · %s MHz min · %s MHz max%s · "
          "RC6 %s%% (sveglia %s%%)"
          % (g.get("cur_mhz"), g.get("min_mhz"), g.get("max_mhz"),
             "  ⚠ BLOCCATA" if g.get("bloccata") else "",
             _n(g.get("rc6_pct")), _n(g.get("sveglia_pct"))))
    if mac["parziale"]:
        for p in mac["perche"]:
            print("       ⚠  parziale: %s" % p)
        print("       ⚠  ⇒ il totale e' un LIMITE INFERIORE, non una misura")
    righe = sorted(m["per_pid"].items(),
                   key=lambda kv: -(kv[1].get("video_pct") or 0))
    for pid, v in righe:
        if (v.get("video_pct") or 0) < minimo and (v.get("render_pct") or 0) < minimo:
            continue
        print("       pid=%-7d %-18s video=%s%%  render=%s%%  mem=%d MiB"
              % (pid, v["comm"], _n(v.get("video_pct")),
                 _n(v.get("render_pct")), (v.get("mem_kib") or 0) // 1024))


# ───────────────────────────────────────────────────────────────────────────
# ⛔⛔ `--certifica` — i guasti innestati, e FATTI GIRARE
# ───────────────────────────────────────────────────────────────────────────

def _finta(t=0.0, cid="1", pid=999, avvio=7, video=0, render=0, radice=True,
           non_letti=0, fd_non_letti=0, cap=2, rc6=0, gt=True):
    """Un'istantanea sintetica: serve a guastare senza toccare la macchina."""
    return {"t": t, "durata_scansione": 0.001, "pdev": "0000:00:02.0",
            "nodo": NODO_PREDEFINITO, "radice": radice,
            "gt": ({"cur_mhz": 300, "act_mhz": 0, "min_mhz": 300,
                    "max_mhz": 1550, "rc6_ms": rc6} if gt else
                   {"cur_mhz": None, "act_mhz": None, "min_mhz": None,
                    "max_mhz": None, "rc6_ms": None}),
            "pid_visti": 100, "pid_non_letti": non_letti,
            "fd_trovati": 1, "fd_non_letti": fd_non_letti,
            "clienti": {(pid, avvio, cid): {
                "pid": pid, "cid": cid, "avvio": avvio, "comm": "ffmpeg",
                "driver": "i915", "pdev": "0000:00:02.0", "mem_kib": 1024,
                "capacita": {"video": cap},
                "render": render, "copy": 0, "video": video,
                "video-enhance": 0}}}


def certifica():
    print("═" * 74)
    print("⛔ CERTIFICAZIONE del metro — sano → guasto → risanato")
    print("═" * 74)
    esiti = []

    def prova(nome, atteso, fatto):
        ok = (atteso == fatto)
        esiti.append((nome, ok, atteso, fatto))
        print("   %s %-52s atteso=%-14s letto=%s"
              % ("OK " if ok else "⛔ROSSO", nome, atteso, fatto))
        return ok

    # ── SANO 0: la lettura vera sulla macchina ───────────────────────────
    print("\n── SANO — la lettura vera ─────────────────────────────────────")
    ist = leggi_istantanea()
    prova("S0 leggi_istantanea() non torna None",
          True, ist is not None)
    m = misura(secondi=1.0)
    prova("S1 misura(1 s) non torna None", True, m is not None)
    if m is not None:
        prova("S2 la percentuale video e' un numero >= 0",
              True, m["macchina"]["video_pct"] is not None
              and m["macchina"]["video_pct"] >= 0.0)
        prova("S3 la capacita video e' stata letta dal kernel",
              True, m["capacita_video"] >= 1)
    if ist is not None:
        print("       (clienti DRM visti: %d · pid non ispezionabili: %d · "
              "root: %s)" % (len(ist["clienti"]), ist["pid_non_letti"],
                             ist["radice"]))

    # ── SANO di riferimento sul sintetico ────────────────────────────────
    a = _finta(t=0.0, video=0)
    b = _finta(t=2.0, video=int(0.25 * 2.0 * 1e9))     # 25 % su 2 s
    r = confronta(a, b)
    prova("S4 sintetico: 25 % di un motore letto come 25,00 %",
          "25.00", None if r is None else "%.2f" % r["macchina"]["video_pct"])
    prova("S5 sintetico: con capacita 2 l'uso e' 12,50 % del totale",
          "12.50", None if r is None else "%.2f" % r["macchina"]["video_uso_pct"])
    prova("S6 sintetico: attribuito al pid giusto",
          "25.00", None if r is None else "%.2f" % r["per_pid"][999]["video_pct"])

    # ── G1 il file fdinfo non e' leggibile ───────────────────────────────
    print("\n── G1 · fdinfo NON leggibile (permesso negato ovunque) ────────")
    # ⛔ Il guasto si puo' innestare solo se c'e' almeno un fd DRM da negare.
    prova("G1 precondizione: sulla macchina ci sono fd DRM da negare",
          True, ist is not None and ist["fd_trovati"] > 0)
    global _LEGGI

    def _nega(p):
        if "/fdinfo/" in p:
            raise Guasto("permesso negato (innestato)")
        return None
    _LEGGI = _nega
    try:
        ist_g = leggi_istantanea()
        sfuggita = None
    except Exception as e:                    # ⛔ non deve sfuggire nulla
        ist_g, sfuggita = "eccezione", repr(e)
    _LEGGI = None
    prova("G1 istantanea con ogni fdinfo negato ⇒ None (⛔ non 0)",
          True, ist_g is None)
    prova("G1 ⇒ e nessuna eccezione e' sfuggita", None, sfuggita)
    _LEGGI = _nega
    m_g = misura(secondi=0.3)
    _LEGGI = None
    prova("G1 ⇒ misura() a valle torna None, non 0 %", None, m_g)
    ist_r = leggi_istantanea()
    prova("G1 risanato ⇒ torna a leggere", True, ist_r is not None)

    # ── G1-bis: UN SOLO cliente illeggibile ⇒ percentuale None, non 0 ────
    a = _finta(t=0.0, video=0)
    b = _finta(t=2.0, video=int(0.25 * 2.0 * 1e9))
    b["clienti"][(999, 7, "1")]["video"] = None        # chiave assente nel file
    r = confronta(a, b)
    prova("G1b un cliente senza la chiave video ⇒ pct None (⛔ non 0)",
          None, None if r is None else r["per_cliente"][(999, 7, "1")]["video_pct"])
    prova("G1b ⇒ il totale macchina e' None e si dichiara parziale",
          "None|True", None if r is None else "%s|%s"
          % (r["macchina"]["video_pct"], r["macchina"]["parziale"]))
    a = _finta(t=0.0, video=0)
    b = _finta(t=2.0, video=int(0.25 * 2.0 * 1e9))
    r = confronta(a, b)
    prova("G1b risanato ⇒ pct di nuovo 25,00", "25.00",
          None if r is None else "%.2f" % r["per_cliente"][(999, 7, "1")]["video_pct"])

    # ── G2 il pid muore fra le due letture ───────────────────────────────
    print("\n── G2 · il processo muore fra la prima e la seconda lettura ───")
    a = _finta(t=0.0, video=0)
    b = _finta(t=2.0, video=0)
    b["clienti"] = {}                                   # sparito
    r = confronta(a, b)
    prova("G2 cliente sparito ⇒ contato come sparito", 1,
          None if r is None else r["spariti"])
    prova("G2 ⇒ il totale NON dice 0 %, dice None", None,
          None if r is None else r["macchina"]["video_pct"])
    prova("G2 ⇒ e il totale e' marcato parziale", True,
          None if r is None else r["macchina"]["parziale"])
    b = _finta(t=2.0, video=int(0.25 * 2.0 * 1e9))
    r = confronta(a, b)
    prova("G2 risanato ⇒ 25,00 % e nessuno sparito", "25.00|0",
          None if r is None else "%.2f|%d" % (r["macchina"]["video_pct"],
                                              r["spariti"]))

    # ── G3 contatore all'indietro ────────────────────────────────────────
    print("\n── G3 · il contatore VA INDIETRO (cliente ricreato) ───────────")
    a = _finta(t=0.0, video=int(5.0 * 1e9))
    b = _finta(t=2.0, video=int(1.0 * 1e9))             # meno di prima
    r = confronta(a, b)
    prova("G3 delta negativo ⇒ pct None (⛔ mai negativa)", None,
          None if r is None else r["per_cliente"][(999, 7, "1")]["video_pct"])
    prova("G3 ⇒ contato fra gli anomali", 1, None if r is None else r["anomali"])
    prova("G3 ⇒ il totale non inventa un numero", None,
          None if r is None else r["macchina"]["video_pct"])

    # ── G3-bis drm-client-id cambiato ────────────────────────────────────
    a = _finta(t=0.0, cid="10", video=int(5.0 * 1e9))
    b = _finta(t=2.0, cid="11", video=int(1.0 * 1e9))   # cliente RICREATO
    r = confronta(a, b)
    prova("G3b client-id cambiato ⇒ 1 sparito + 1 nuovo, nessuna pct inventata",
          "1|1|None", None if r is None else "%d|%d|%s"
          % (r["spariti"], r["nuovi"], r["macchina"]["video_pct"]))

    # ── G3-ter salto impossibile (piu' del 100 % × capacita) ─────────────
    a = _finta(t=0.0, video=0)
    b = _finta(t=2.0, video=int(60.0 * 1e9))            # 30 motori su 2
    r = confronta(a, b)
    prova("G3t salto impossibile (3000 %) ⇒ None, non un numero enorme", None,
          None if r is None else r["per_cliente"][(999, 7, "1")]["video_pct"])

    # ── G3-quater: pid RICICLATO (stesso pid, avvio diverso) ─────────────
    a = _finta(t=0.0, pid=999, avvio=7, video=int(5.0 * 1e9))
    b = _finta(t=2.0, pid=999, avvio=99, video=int(1.0 * 1e9))
    r = confronta(a, b)
    prova("G3q pid riciclato (avvio diverso) ⇒ non confuso col precedente",
          "1|1", None if r is None else "%d|%d" % (r["spariti"], r["nuovi"]))

    # ── G4 il tempo fra le due letture e' zero ───────────────────────────
    print("\n── G4 · dt = 0, dt < 0, dt troppo corto ───────────────────────")
    a = _finta(t=5.0, video=0)
    b = _finta(t=5.0, video=int(1.0 * 1e9))
    try:
        r = confronta(a, b)
        scoppiato = False
    except ZeroDivisionError:
        r, scoppiato = "ZeroDivisionError", True
    prova("G4 dt = 0 ⇒ None (⛔ nessuna divisione per zero)", None, r)
    prova("G4 ⇒ e non e' scoppiato", False, scoppiato)
    b = _finta(t=4.0, video=int(1.0 * 1e9))
    prova("G4 dt < 0 (letture invertite) ⇒ None", None, confronta(a, b))
    b = _finta(t=5.05, video=int(1.0 * 1e9))
    prova("G4 dt = 50 ms (sotto il minimo di %.1f s) ⇒ None" % DISTANZA_MINIMA,
          None, confronta(a, b))
    b = _finta(t=7.0, video=int(0.5 * 1e9))
    prova("G4 risanato (dt = 2 s) ⇒ 25,00 %", "25.00",
          "%.2f" % confronta(a, b)["macchina"]["video_pct"])

    # ── G5 valore non numerico nel file ──────────────────────────────────
    print("\n── G5 · il kernel scrive qualcosa che non e' un numero ────────")
    prova("G5 «abc ns» ⇒ None (⛔ non 0)", None,
          _ns({"drm-engine-video": "abc ns"}, "drm-engine-video"))
    prova("G5 chiave assente ⇒ None (⛔ non 0)", None,
          _ns({}, "drm-engine-video"))
    prova("G5 risanato: «123 ns» ⇒ 123", 123,
          _ns({"drm-engine-video": "123 ns"}, "drm-engine-video"))

    # ── G7 il contesto GT: RC6 e frequenza ───────────────────────────────
    print("\n── G7 · il contesto GT (RC6, frequenza) ───────────────────────")
    a = _finta(t=0.0, rc6=1000)
    b = _finta(t=2.0, rc6=1000 + 1500)                  # 1,5 s spenta su 2 s
    r = confronta(a, b)
    prova("G7 sano: RC6 1,5 s su 2 s ⇒ 75,00 % spenta, 25,00 % sveglia",
          "75.00|25.00", None if r is None else "%.2f|%.2f"
          % (r["gt"]["rc6_pct"], r["gt"]["sveglia_pct"]))
    b = _finta(t=2.0, rc6=100)                          # ⛔ contatore indietro
    r = confronta(a, b)
    prova("G7 RC6 all'indietro ⇒ None (⛔ mai negativa)", None,
          None if r is None else r["gt"]["rc6_pct"])
    b = _finta(t=2.0, rc6=1000 + 9000)                  # ⛔ 9 s spenta in 2 s
    r = confronta(a, b)
    prova("G7 RC6 impossibile (450 %) ⇒ None, non un numero enorme", None,
          None if r is None else r["gt"]["rc6_pct"])
    a = _finta(t=0.0, gt=False); b = _finta(t=2.0, gt=False)
    r = confronta(a, b)
    prova("G7 sysfs della GT assente ⇒ tutto None (⛔ non 0 MHz, non 0 %)",
          "None|None|None", None if r is None else "%s|%s|%s"
          % (r["gt"]["rc6_pct"], r["gt"]["cur_mhz"], r["gt"]["max_mhz"]))
    a = _finta(t=0.0, rc6=1000); b = _finta(t=2.0, rc6=1000 + 1500)
    r = confronta(a, b)
    prova("G7 risanato ⇒ di nuovo 75,00 %", "75.00",
          None if r is None else "%.2f" % r["gt"]["rc6_pct"])
    gv = leggi_gt()
    prova("G7 lettura vera: la GT espone la frequenza massima", True,
          gv["max_mhz"] is not None and gv["max_mhz"] > 0)
    prova("G7 lettura vera: la GT espone la residenza RC6", True,
          gv["rc6_ms"] is not None)

    # ── G6 una delle due istantanee e' None ──────────────────────────────
    print("\n── G6 · una delle due letture non c'e' ────────────────────────")
    prova("G6 confronta(None, b) ⇒ None", None, confronta(None, _finta(t=2.0)))
    prova("G6 confronta(a, None) ⇒ None", None, confronta(_finta(), None))
    prova("G6 misura(secondi=0) ⇒ None (troppo corto)", None, misura(secondi=0.0))

    # ── il verdetto ──────────────────────────────────────────────────────
    buoni = sum(1 for _, ok, _, _ in esiti if ok)
    print("\n" + "═" * 74)
    print("   %d/%d predicati.  %s" % (buoni, len(esiti),
          "✅ il metro da' rosso dove deve" if buoni == len(esiti)
          else "⛔ IL METRO NON E' BUONO"))
    print("═" * 74)
    return 0 if buoni == len(esiti) else 1


# ───────────────────────────────────────────────────────────────────────────
# ⛔⛔ `--tara` — la taratura: carichi NOTI, e il metro deve ritrovarli
# ───────────────────────────────────────────────────────────────────────────

LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/10a1")


def _sorgenti(lav):
    """Genera i file grezzi nv12 (una volta sola).  ⭐ Sorgente sintetica
       `testsrc2`, 1 s in circolo: cosi' il costo di CPU e' solo la lettura."""
    fatti = {}
    for nome, larg, alt in (("1080", 1920, 1080), ("720", 1280, 720)):
        f = "%s/src-%s.nv12" % (lav, nome)
        if not os.path.exists(f):
            subprocess.run(
                ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i",
                 "testsrc2=size=%dx%d:rate=30" % (larg, alt),
                 "-t", "1", "-pix_fmt", "nv12", "-f", "rawvideo", f],
                check=True)
        fatti[nome] = (f, larg, alt)
    return fatti


def _accendi(lav, quanti, ritmo, sorg, larg, alt, durata):
    figli = []
    for i in range(quanti):
        prog = "%s/prog-%d.txt" % (lav, i)
        if os.path.exists(prog):
            os.unlink(prog)
        p = subprocess.Popen(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-re",
             "-stream_loop", "-1", "-f", "rawvideo", "-pix_fmt", "nv12",
             "-s", "%dx%d" % (larg, alt), "-r", str(ritmo), "-i", sorg,
             "-init_hw_device", "vaapi=va:" + NODO_PREDEFINITO,
             "-filter_hw_device", "va", "-vf", "hwupload",
             "-c:v", "h264_vaapi", "-b:v", "8M", "-t", str(durata),
             "-progress", prog, "-f", "null", "-"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True)
        figli.append(p)
    return figli


def _spegni(figli):
    for p in figli:
        try:
            p.terminate()
        except Exception:
            pass
    for p in figli:
        try:
            p.wait(timeout=10)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


def _arrivata(lav, quanti, larg, alt):
    """⛔ `LEZIONI.md` §1.30 — quanta sollecitazione e' ARRIVATA davvero.
       Legge i file `-progress`: fotogrammi codificati e tempo di uscita.
       Torna (Mpixel/s, fotogrammi/s totali) oppure `None`."""
    tot_frame, tot_s = 0, 0.0
    for i in range(quanti):
        t = _leggi_testo("%s/prog-%d.txt" % (lav, i))
        if t is None:
            return None
        fr = re.findall(r"^frame=(\d+)", t, re.M)
        us = re.findall(r"^out_time_us=(-?\d+)", t, re.M)
        if not fr or not us:
            return None
        tot_frame += int(fr[-1])
        tot_s += int(us[-1]) / 1e6
    if tot_s <= 0:
        return None
    fps = tot_frame / (tot_s / quanti)
    return (fps * larg * alt / 1e6, fps)


def tara(durata_misura=12.0, riscaldo=4.0):
    print("═" * 78)
    print("⛔⛔ TARATURA del metro — i carichi sono NOTI, il metro deve ritrovarli")
    print("═" * 78)
    if os.geteuid() != 0:
        print("   ⚠  NON sono root: il totale macchina sara' parziale "
              "(gnome-shell escluso).")
    os.makedirs(LAV, exist_ok=True)
    print("   preparo le sorgenti grezze nv12 (testsrc2, 1 s in circolo)...")
    src = _sorgenti(LAV)

    scene = [
        ("zero — macchina ferma",            0, 30, "1080"),
        ("1 × 1080p30",                      1, 30, "1080"),
        ("1 × 1080p15  (meta' ritmo)",       1, 15, "1080"),
        ("2 × 1080p30",                      2, 30, "1080"),
        ("4 × 1080p30",                      4, 30, "1080"),
        ("1 × 720p30   (altra risoluzione)", 1, 30, "720"),
        ("zero — di nuovo (controllo)",      0, 30, "1080"),
    ]

    righe = []
    for nome, quanti, ritmo, ris in scene:
        sorg, larg, alt = src[ris]
        figli = _accendi(LAV, quanti, ritmo, sorg, larg, alt,
                         durata_misura + riscaldo + 4) if quanti else []
        try:
            if quanti:
                time.sleep(riscaldo)          # ⚠ §1.4: l'avvio non e' il regime
            m = misura(secondi=durata_misura)
        finally:
            _spegni(figli)
        arr = _arrivata(LAV, quanti, larg, alt) if quanti else (0.0, 0.0)
        mpx = None if arr is None else arr[0]
        fps = None if arr is None else arr[1]
        mpx_atteso = quanti * ritmo * larg * alt / 1e6
        v = None if m is None else m["macchina"]["video_pct"]
        # ⭐ il carico MIO, separato dal resto della macchina
        mio = None
        if m is not None:
            mio = sum(x.get("video_pct") or 0.0
                      for x in m["per_pid"].values() if x["comm"] == "ffmpeg")
        righe.append({"nome": nome, "quanti": quanti, "mpx_atteso": mpx_atteso,
                      "mpx": mpx, "fps": fps, "video": v, "mio": mio,
                      "render": None if m is None else m["macchina"]["render_pct"],
                      "cap": None if m is None else m["capacita_video"],
                      "m": m})
        print("\n── %s ──" % nome)
        if m is None:
            print("   ⛔ ROSSO — non ho misurato")
            continue
        print("   sollecitazione ATTESA  %7.1f Mpx/s   ARRIVATA %s Mpx/s (%s fps tot)"
              % (mpx_atteso, _n(mpx, 7), _n(fps, 6)))
        if mpx is not None and mpx_atteso > 0:
            print("   ⇒ e' arrivato il %.1f %% di quel che ho chiesto"
                  % (100.0 * mpx / mpx_atteso))
        stampa(m)

    # ── la tavola ────────────────────────────────────────────────────────
    print("\n" + "═" * 78)
    print("LA TAVOLA DELLA TARATURA  (video_pct = motori-equivalenti ×100, "
          "capacita = %s)" % (righe[1]["cap"] if len(righe) > 1 else "?"))
    print("═" * 78)
    base = None
    for r in righe:
        if r["quanti"] == 1 and abs(r["mpx_atteso"] - 62.2) < 2 and r["mio"]:
            base = r["mio"] / r["mpx"]        # % per Mpx/s, dal carico singolo
    print("%-34s %10s %10s %9s %9s %8s" %
          ("scena", "Mpx/s arr", "video %", "mio %", "atteso %", "scarto"))
    for r in righe:
        att = None if base is None or r["mpx"] is None else base * r["mpx"]
        sc = ("%+.1f %%" % (100.0 * (r["mio"] - att) / att)
              if att not in (None, 0) and r["mio"] is not None else "—")
        print("%-34s %10s %10s %9s %9s %8s" %
              (r["nome"], _n(r["mpx"], 10), _n(r["video"], 10),
               _n(r["mio"], 9), _n(att, 9), sc))
    if base is not None:
        print("\n⭐ k = %.5f %% di un motore VDBOX per Mpixel/s  "
              "(= %.5f %% della capacita video, che e' di %d motori)"
              % (base, base / (righe[1]["cap"] or 1), righe[1]["cap"] or 1))
        print("   ⚠⚠ e questo `k` vale SOLO alla frequenza che il governatore "
              "teneva qui.")
        print("      Estrapolando: un motore saturo a %.0f Mpx/s, la capacita "
              "video a %.0f Mpx/s" % (100.0 / base,
                                      100.0 * (righe[1]["cap"] or 1) / base))
        print("      ⛔ MA E' UN LIMITE INFERIORE, e sbagliato fino a un "
              "fattore ~4: vedi §CLOCK.")
        print("      A carico leggero la GT sta bassa e ogni fotogramma occupa "
              "PIU' tempo.  ⇒ il numero")
        print("      vero della fase 10 si misura A SATURAZIONE "
              "(`--tara-clock` mostra perche').")
    # ⭐ la retta, coi minimi quadrati su tutte le scene con carico
    punti = [(r["mpx"], r["mio"]) for r in righe
             if r["quanti"] and r["mpx"] and r["mio"] is not None]
    if len(punti) >= 3:
        n = len(punti)
        sx = sum(p[0] for p in punti); sy = sum(p[1] for p in punti)
        sxx = sum(p[0] * p[0] for p in punti); sxy = sum(p[0] * p[1] for p in punti)
        den = n * sxx - sx * sx
        if den:
            a1 = (n * sxy - sx * sy) / den
            a0 = (sy - a1 * sx) / n
            res = [y - (a0 + a1 * x) for x, y in punti]
            err = (sum(e * e for e in res) / n) ** 0.5
            print("\n⭐ retta ai minimi quadrati su %d punti:  "
                  "video_pct = %.5f · Mpx/s %+.3f" % (n, a1, a0))
            print("   errore quadratico medio %.3f punti percentuali "
                  "(scarto massimo %.3f)" % (err, max(abs(e) for e in res)))
    return 0


def _scrivi_sysfs(percorso, valore):
    try:
        with open(percorso, "w") as f:
            f.write("%d\n" % valore)
        return True
    except Exception:
        return False


def tara_clock(durata_misura=12.0, riscaldo=4.0):
    """⛔⛔ La prova del §CLOCK: **lo stesso identico carico** a due frequenze
       bloccate.  Se il numero cambia, il metro misura TEMPO, non LAVORO."""
    print("═" * 78)
    print("⛔⛔ TARATURA §CLOCK — stesso carico, due frequenze di GT bloccate")
    print("═" * 78)
    if os.geteuid() != 0:
        print("   ⛔ serve root per bloccare la frequenza della GT.  Mi fermo.")
        return 1
    g0 = leggi_gt()
    if g0["min_mhz"] is None or g0["max_mhz"] is None:
        print("   ⛔ non leggo le frequenze della GT.  Mi fermo.")
        return 1
    rpn = _intero(SYS_GT + "/gt_RPn_freq_mhz") or g0["min_mhz"]
    rp0 = _intero(SYS_GT + "/gt_RP0_freq_mhz") or g0["max_mhz"]
    print("   la GT va da %d a %d MHz; la rimetto a %d..%d quando ho finito"
          % (rpn, rp0, g0["min_mhz"], g0["max_mhz"]))
    os.makedirs(LAV, exist_ok=True)
    src = _sorgenti(LAV)
    sorg, larg, alt = src["1080"]
    righe = []
    try:
        for f_mhz in (rpn, rp0):
            _scrivi_sysfs(SYS_GT + "/gt_min_freq_mhz", rpn)
            _scrivi_sysfs(SYS_GT + "/gt_max_freq_mhz", f_mhz)
            _scrivi_sysfs(SYS_GT + "/gt_min_freq_mhz", f_mhz)
            _scrivi_sysfs(SYS_GT + "/gt_boost_freq_mhz", f_mhz)
            figli = _accendi(LAV, 1, 30, sorg, larg, alt,
                             durata_misura + riscaldo + 4)
            try:
                time.sleep(riscaldo)
                m = misura(secondi=durata_misura)
            finally:
                _spegni(figli)
            arr = _arrivata(LAV, 1, larg, alt)
            print("\n── GT bloccata a %d MHz ──" % f_mhz)
            if arr:
                print("   ARRIVATI %.2f Mpx/s (%.2f fps)" % arr)
            stampa(m)
            mio = None if m is None else sum(
                x.get("video_pct") or 0.0 for x in m["per_pid"].values()
                if x["comm"] == "ffmpeg")
            righe.append((f_mhz, mio, arr))
    finally:
        # ⛔ Si rimette com'era, sempre — anche se qualcosa e' andato storto.
        _scrivi_sysfs(SYS_GT + "/gt_min_freq_mhz", rpn)
        _scrivi_sysfs(SYS_GT + "/gt_max_freq_mhz", g0["max_mhz"])
        _scrivi_sysfs(SYS_GT + "/gt_min_freq_mhz", g0["min_mhz"])
        _scrivi_sysfs(SYS_GT + "/gt_boost_freq_mhz", g0["max_mhz"])
        g1 = leggi_gt()
        print("\n   rimessa: min=%s max=%s (era min=%s max=%s) %s"
              % (g1["min_mhz"], g1["max_mhz"], g0["min_mhz"], g0["max_mhz"],
                 "OK" if (g1["min_mhz"], g1["max_mhz"])
                 == (g0["min_mhz"], g0["max_mhz"]) else "⛔ NON RIMESSA"))
    print("\n" + "═" * 78)
    if len(righe) == 2 and all(r[1] for r in righe) and all(r[2] for r in righe):
        (fa, va, aa), (fb, vb, ab) = righe
        print("   %4d MHz → video %5.2f %%   (%.2f fps consegnati)"
              % (fa, va, aa[1]))
        print("   %4d MHz → video %5.2f %%   (%.2f fps consegnati)"
              % (fb, vb, ab[1]))
        d_fps = abs(aa[1] - ab[1]) / max(aa[1], 1e-9) * 100.0
        print("   ⇒ lavoro consegnato uguale entro il %.1f %%, "
              "occupazione diversa di un fattore %.2f" % (d_fps, va / vb))
        print("   ⛔ ⇒ `drm-engine-video` misura TEMPO, non LAVORO: il budget "
              "si misura a saturazione, non si estrapola.")
    else:
        print("   ⛔ ROSSO — non ho misurato tutt'e due le frequenze")
    print("═" * 78)
    return 0


# ───────────────────────────────────────────────────────────────────────────
# Riga di comando
# ───────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Metro dell'occupazione dei motori della GPU i915 "
                    "(fdinfo).  ⛔ None non e' zero.")
    ap.add_argument("--una-lettura", action="store_true",
                    help="una misura sola e poi esci")
    ap.add_argument("--per-secondi", type=float, metavar="N",
                    help="misura in continuo per N secondi")
    ap.add_argument("--ogni", type=float, default=1.0, metavar="S",
                    help="distanza fra le due letture di ogni misura (default 1 s)")
    ap.add_argument("--secondi", type=float, default=1.0, metavar="S",
                    help="distanza fra le due letture (--una-lettura)")
    ap.add_argument("--pid", type=int, action="append",
                    help="restringi a questi pid (ripetibile)")
    ap.add_argument("--nodo", default=NODO_PREDEFINITO,
                    help="nodo di rendering (default %s)" % NODO_PREDEFINITO)
    ap.add_argument("--certifica", action="store_true",
                    help="⛔ innesta i guasti e conta sano→guasto→risanato")
    ap.add_argument("--tara", action="store_true",
                    help="⛔ la taratura coi carichi noti (serve ffmpeg)")
    ap.add_argument("--tara-clock", action="store_true",
                    help="⛔⛔ stesso carico a due frequenze di GT bloccate "
                         "(serve root; rimette la GT com'era)")
    a = ap.parse_args()

    if a.certifica:
        return certifica()
    if a.tara:
        return tara()
    if a.tara_clock:
        return tara_clock()

    solo = set(a.pid) if a.pid else None
    if a.per_secondi:
        fine = time.monotonic() + a.per_secondi
        picchi, buone, cieche = [], 0, 0
        while time.monotonic() < fine:
            m = misura(secondi=max(a.ogni, DISTANZA_MINIMA), nodo=a.nodo,
                       solo_pid=solo)
            print("[%7.1f s]" % (a.per_secondi - (fine - time.monotonic())))
            stampa(m)
            if m is None or m["macchina"]["video_pct"] is None:
                cieche += 1
            else:
                buone += 1
                picchi.append(m["macchina"]["video_pct"])
        print("\n── riassunto ──")
        if buone:
            print("   %d misure buone · video medio %.2f %% · massimo %.2f %%"
                  % (buone, sum(picchi) / len(picchi), max(picchi)))
        if cieche:
            print("   ⛔ %d misure CIECHE (None): non entrano in nessuna media"
                  % cieche)
        return 0 if buone else 1

    # predefinito: --una-lettura
    m = misura(secondi=max(a.secondi, DISTANZA_MINIMA), nodo=a.nodo, solo_pid=solo)
    stampa(m)
    return 0 if m is not None else 1


if __name__ == "__main__":
    sys.exit(main())
