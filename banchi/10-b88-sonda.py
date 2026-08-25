#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-b88-sonda — IL MECCANISMO ACCANTO AL SINTOMO, campionato mentre il carico gira.

⭐ PERCHE' ESISTE (`LEZIONI.md` §1.31).  «I fotogrammi sono calati» e' un
   sintomo: non dice se ha ceduto la GPU, la CPU o la memoria.  Questa sonda gira
   **sulla macchina di prova, insieme al carico**, e campiona ogni secondo le
   quattro cose che rispondono a quella domanda.

═══════════════════════════════════════════════════════════════════════════
⛔⛔ IL METRO DELLA GPU NON E' MIO: E' QUELLO DI A1, `10-b87-metro-gpu.py`
═══════════════════════════════════════════════════════════════════════════

Questa sonda **non legge da se'** `/proc/<pid>/fdinfo`: importa il metro
dell'agente A1 e gli chiede `leggi_istantanea()` / `confronta()`.  ⛔ La ragione
e' la regola 6 del preambolo — *un metro non tarato produce numeri, non misure* —
e quel metro e' tarato (`--certifica` 43/43, `--tara`, `--tara-clock`), mentre
uno scritto qui non lo sarebbe.  ⚠ E porta tre cose che una lettura ingenua
sbaglia:

  1. ⛔ **filtra sul `drm-pdev` del nodo** ⇒ la Radeon `renderD129`, chiusa
     apposta (`DECISIONI.md` §4.6-quinquies), resta fuori dal conto;
  2. ⛔ **i VDBOX sono DUE** (`drm-engine-capacity-video: 2`): il massimo e'
     **200 %** in motori-equivalenti, cioe' **100 %** di capacita'.  Confondere
     i due numeri sbaglia il budget di un fattore due, e per questo la sonda
     scrive tutt'e due con nomi diversi (`video_pct`, `video_uso_pct`);
  3. ⛔⛔ **`drm-engine-video` conta TEMPO OCCUPATO, non LAVORO FATTO**, e il
     tempo dipende dalla frequenza della GT: `[M]` A1, stessa identica codifica
     1080p30, **26,41 %** a 300 MHz contro **7,01 %** a 1550 MHz — un fattore
     **3,77** a lavoro uguale.  ⇒ Accanto a ogni lettura va il **contesto GT**
     (frequenza chiesta/atto/min/max, «bloccata» se min = max) e la **residenza
     RC6**, che e' una seconda misura indipendente dai fdinfo.

⇒ ⛔ **Da cui la regola che vincola il saturatore**: la capienza della GPU **si
  misura a saturazione**, non si estrapola con una retta tirata su un carico
  leggero.

═══════════════════════════════════════════════════════════════════════════
⛔ LE ALTRE TRE COSE CHE SI CAMPIONANO

  la CPU        `/proc/stat`, DIVISA fra utente e sistema: `sws_scale` sta
                nell'utente, le ioctl del driver nel sistema.
  la MEMORIA    `/proc/meminfo` — `MemAvailable`, `MemFree`, `Dirty`.
  ⛔ GLI ESTRANEI  quanto del motore video se lo prende **chi non e' il mio
                carico**.  La GPU e' una (`LEZIONI.md` §1.26): se mentre saturo
                c'e' un'altra sessione viva sulla scheda, il mio numero e' piu'
                basso del vero **e non lo grida nessuno**.

⛔ `None` NON E' ZERO.  Ogni voce che non si e' potuta leggere esce `null`, e
   chi legge si rifiuta di giudicarla.  ⚠ Per vedere TUTTA la macchina serve
   `root`: senza, il metro marca la lettura `parziale` e quel marchio arriva
   fino al verdetto.

Uso (sulla macchina di prova, da root):
    python3 10-b88-sonda.py --uscita S.jsonl --secondi 90 [--passo-ms 1000]
                            [--processo 10-b88-flusso] [--nodo /dev/dri/renderD128]
                            [--metro PERCORSO]
"""
import argparse, importlib.util, json, os, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))


def carica_metro(percorso):
    """⛔ Il metro di A1.  Se non c'e', la sonda NON si inventa un ripiego: le
       voci della GPU escono `null` e lo dice."""
    if not os.path.exists(percorso):
        return None
    spec = importlib.util.spec_from_file_location("metro", percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cpu_totale():
    with open("/proc/stat") as f:
        p = f.readline().split()
    v = [int(x) for x in p[1:]]
    return {"utente": v[0] + v[1], "sistema": v[2], "inattiva": v[3] + v[4],
            "altro": sum(v[5:8]) if len(v) >= 8 else 0, "tutti": sum(v)}


def memoria():
    fuori = {}
    with open("/proc/meminfo") as f:
        for riga in f:
            c = riga.split(":")
            if c[0] in ("MemAvailable", "Dirty", "MemFree"):
                fuori[c[0]] = int(c[1].strip().split()[0])
    return fuori


def spezza(m, nome):
    """Dal confronto del metro alle due meta' che servono: il MIO carico e gli
       ESTRANEI.  ⛔ Se anche un solo pezzo manca, la meta' corrispondente esce
       `None`: sommare quel che si e' letto e chiamarlo totale e' la forma E8."""
    miei, altri, miei_null, altri_null = 0.0, 0.0, False, False
    chi_estraneo = {}
    for pid, d in (m.get("per_pid") or {}).items():
        v = d.get("video_pct")
        if d.get("comm") == nome:
            if v is None:
                miei_null = True
            else:
                miei += v
        else:
            if v is None:
                altri_null = True
            else:
                altri += v
                if v > 0.5:
                    chi_estraneo["%s/%s" % (pid, d.get("comm"))] = round(v, 2)
    return {"miei_video_pct": None if miei_null else miei,
            "estranei_video_pct": None if altri_null else altri,
            "chi_estraneo": chi_estraneo or None}


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--uscita", required=True)
    a.add_argument("--secondi", type=float, default=90.0)
    a.add_argument("--passo-ms", type=int, default=1000)
    a.add_argument("--processo", default="10-b88-flusso")
    a.add_argument("--nodo", default="/dev/dri/renderD128")
    a.add_argument("--metro", default=os.path.join(QUI, "10-b87-metro-gpu.py"))
    # ⛔ Il guasto innestabile: si punta il metro su un file che non c'e' ⇒ le
    #    voci della GPU escono `null`.  Serve a far vedere che il banco SI
    #    RIFIUTA di giudicare invece di stampare «0 %».
    a.add_argument("--metro-cieco", action="store_true")
    o = a.parse_args()

    metro = None if o.metro_cieco else carica_metro(o.metro)
    pdev = metro.pdev_del_nodo(o.nodo) if metro else None
    prima = metro.leggi_istantanea(o.nodo, None, pdev) if metro else None

    fine = time.time() + o.secondi
    with open(o.uscita, "w") as u:
        while time.time() < fine:
            time.sleep(o.passo_ms / 1000.0)
            voce = {"t": time.time(), "cpu": cpu_totale(), "memoria": memoria(),
                    "metro": bool(metro)}
            if metro:
                dopo = metro.leggi_istantanea(o.nodo, None, pdev)
                m = metro.confronta(prima, dopo)
                prima = dopo if dopo is not None else prima
                if m is None:
                    # ⛔ `None`, non zero: «non ho misurato» ≠ «non e' successo
                    #    niente».
                    voce["gpu"] = None
                else:
                    voce["gpu"] = {
                        "dt": m["dt"],
                        "capacita_video": m["capacita_video"],
                        "video_pct": m["macchina"]["video_pct"],
                        "video_uso_pct": m["macchina"]["video_uso_pct"],
                        "render_pct": m["macchina"]["render_pct"],
                        "video_enhance_pct": m["macchina"]["video-enhance_pct"],
                        "copy_pct": m["macchina"]["copy_pct"],
                        "parziale": m["macchina"]["parziale"],
                        "perche": m["macchina"]["perche"],
                        "radice": m["radice"],
                        "gt": m["gt"],
                    }
                    voce["gpu"].update(spezza(m, o.processo))
            else:
                voce["gpu"] = None
            u.write(json.dumps(voce) + "\n")
            u.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
