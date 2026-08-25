#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b94-ferro-carico — che cosa cambia SOTTO CARICO sulla Intel UHD 730.

Fase 10, agente A10 — «lo studio del ferro», domanda 4 (quella che vale più delle altre).

⛔ Non misura il soffitto (quello è di A2): misura **che cosa cambia** quando le codifiche
passano da 1 a 4 a 8 **a parità di richiesta**:

  · la **qualità** resta quella chiesta?               → i flussi restano identici byte per byte
  · il **controllo del bitrate** obbedisce ancora?     → CBR segue la richiesta, CQP la ignora
  · compare un **ripiego in software** non dichiarato? → i motori video sono davvero occupati
  · la **frequenza** tiene su un giro lungo?           → `gt_act_freq_mhz` e i motivi di freno

I metri, e come sono tarati (⛔ `LEZIONI.md` §1.33, il metro si tara PRIMA):

  1. **metro dei motori** — PMU `i915` via `perf_event_open`: `vcs0-busy`, `vcs1-busy` in ns.
     Taratura: (a) a vuoto deve leggere ≈ 0; (b) raddoppiando i fotogrammi il conteggio deve
     raddoppiare; (c) il conteggio di un motore non può superare il tempo trascorso.
  2. **metro della frequenza** — `/sys/class/drm/card0/gt_act_freq_mhz`.
     Taratura: a riposo deve stare sotto RP1, sotto carico deve salire sopra RP1.
  3. **metro del bitrate** — byte del flusso / durata. Taratura: si chiede CBR a due valori
     noti (5 e 20 Mbit/s) e il metro deve ritrovarli.

⛔ `None` non è zero: ogni metro che non ha misurato torna `None`, e il predicato si rifiuta
di giudicare invece di dire «tutto bene».

⛔⛔ Ogni giro da cui esce un numero vuole il **lucchetto della GPU** (`banchi/09-lucchetto.py`):
lo prende chi lancia, non questo file.

Modi:
    sorgente                  prepara il filmato grezzo di prova
    taratura                  tara i tre metri e basta
    confronto                 il giro vero: 1 / 4 / 8 codifiche a parità di richiesta
    lungo --minuti 10         il giro lungo, per la frequenza e il termico
    memoria                   quanto costa in RAM un contesto di codifica
    --certifica               innesta i guasti e conta sano → guasto → risanato
"""

import argparse
import ctypes
import ctypes.util
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time

NODO = "/dev/dri/renderD128"
CARD = "/sys/class/drm/card0"
LAVORO = "/media/REMOTIX/tmp/10a10"


# ═════════════════════════════════════════════════════════════════════════════
# METRO 1 · i motori video, dalla PMU di i915
# ═════════════════════════════════════════════════════════════════════════════

PERF_EVENT_OPEN = 298  # x86_64


def leggi_intero(percorso):
    """Legge un intero da un file di /sys. ⛔ Torna None se non ha potuto leggere:
    «negato» e «zero» non devono avere lo stesso aspetto (`LEZIONI.md` §1.9)."""
    try:
        return int(open(percorso).read().strip())
    except Exception:
        return None


class AttrPerf(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("config", ctypes.c_uint64),
        ("sample_period", ctypes.c_uint64),
        ("sample_type", ctypes.c_uint64),
        ("read_format", ctypes.c_uint64),
        ("flags", ctypes.c_uint64),
        ("wakeup_events", ctypes.c_uint32),
        ("bp_type", ctypes.c_uint32),
        ("config1", ctypes.c_uint64),
        ("config2", ctypes.c_uint64),
        ("branch_sample_type", ctypes.c_uint64),
        ("sample_regs_user", ctypes.c_uint64),
        ("sample_stack_user", ctypes.c_uint32),
        ("clockid", ctypes.c_int32),
        ("sample_regs_intr", ctypes.c_uint64),
        ("aux_watermark", ctypes.c_uint32),
        ("sample_max_stack", ctypes.c_uint16),
        ("riservato2", ctypes.c_uint16),
        ("aux_sample_size", ctypes.c_uint32),
        ("riservato3", ctypes.c_uint32),
        ("sig_data", ctypes.c_uint64),
    ]


class MetroMotori:
    """Legge i contatori di occupazione dei motori della GPU. ⛔ Vuole i privilegi di root
    (`/proc/sys/kernel/perf_event_paranoid` vale 2 su questa macchina)."""

    def __init__(self, eventi=None):
        self.base = "/sys/bus/event_source/devices/i915"
        self.eventi = eventi or ["vcs0-busy", "vcs1-busy", "rcs0-busy", "vecs0-busy",
                                 "rc6-residency"]
        self.fd = {}
        self.errore = None
        self.libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

    def apri(self):
        try:
            tipo = int(open(f"{self.base}/type").read().strip())
            cpu = int(open(f"{self.base}/cpumask").read().strip().split(",")[0].split("-")[0])
        except Exception as ex:
            self.errore = f"PMU i915 non leggibile: {ex}"
            return False
        for nome in self.eventi:
            try:
                testo = open(f"{self.base}/events/{nome}").read().strip()
            except Exception as ex:
                self.errore = f"evento {nome} assente: {ex}"
                return False
            cfg = int(re.search(r"config=(0x[0-9a-fA-F]+|\d+)", testo).group(1), 0)
            a = AttrPerf()
            ctypes.memset(ctypes.byref(a), 0, ctypes.sizeof(a))
            a.type = tipo
            a.size = 128
            a.config = cfg
            fd = self.libc.syscall(PERF_EVENT_OPEN, ctypes.byref(a),
                                   ctypes.c_int(-1), ctypes.c_int(cpu),
                                   ctypes.c_int(-1), ctypes.c_ulong(0))
            if fd < 0:
                e = ctypes.get_errno()
                self.errore = (f"perf_event_open({nome}) → errno {e} "
                               f"({os.strerror(e)}); serve root o perf_event_paranoid ≤ 0")
                self.chiudi()
                return False
            self.fd[nome] = fd
        return True

    def leggi(self):
        """Torna {evento: nanosecondi cumulativi} oppure ⛔ None se non ha potuto leggere."""
        if not self.fd:
            return None
        fuori = {}
        for nome, fd in self.fd.items():
            try:
                # ⚠ i descrittori di perf non sono posizionabili: si legge con read(), non pread()
                dati = os.read(fd, 8)
            except Exception as ex:
                self.errore = f"lettura {nome}: {ex}"
                return None
            if len(dati) != 8:
                self.errore = f"lettura {nome}: {len(dati)} byte invece di 8"
                return None
            fuori[nome] = int.from_bytes(dati, "little")
        return fuori

    def chiudi(self):
        for fd in self.fd.values():
            try:
                os.close(fd)
            except OSError:
                pass
        self.fd = {}


# ⚠ Energia e temperatura del pacchetto: leggibili SOLO da root, quindi stanno qui
#   dentro la sonda invece che nel campionatore in filo.
ENERGIA = "/sys/class/powercap/intel-rapl:0/energy_uj"
TEMPERATURA = "/sys/class/hwmon/hwmon2/temp1_input"   # «Package id 0»


def sonda_motori(secondi, uscita):
    """Sottoprogramma da lanciare con i privilegi di root: campiona e scrive JSONL.

    Oltre ai motori legge **l'energia del pacchetto** e la **temperatura**: su un
    35 W (dichiarato) la domanda «il soffitto misurato a freddo è quello di una
    sessione che dura ore?» non si risponde senza queste due colonne.
    """
    m = MetroMotori()
    if not m.apri():
        with open(uscita, "w") as f:
            f.write(json.dumps({"errore": m.errore}) + "\n")
        return 1
    t0 = time.monotonic()
    with open(uscita, "w") as f:
        f.write(json.dumps({"errore": None, "avvio": True}) + "\n")
        f.flush()
        while time.monotonic() - t0 < secondi:
            v = m.leggi()
            riga = {"t": round(time.monotonic() - t0, 3), "v": v,
                    "energia_uj": leggi_intero(ENERGIA),
                    "temp_mc": leggi_intero(TEMPERATURA)}
            if v is None:
                riga["errore"] = m.errore  # ⛔ un buco dichiarato, non uno zero
            f.write(json.dumps(riga) + "\n")
            f.flush()
            time.sleep(0.2)
    m.chiudi()
    return 0


class SondaEsterna:
    """Lancia la sonda dei motori come processo root e ne raccoglie il primo/ultimo campione."""

    def __init__(self, uscita, secondi, parola="nicfio"):
        self.uscita = uscita
        self.secondi = secondi
        self.parola = parola
        self.proc = None

    def avvia(self):
        if os.path.exists(self.uscita):
            os.unlink(self.uscita)
        cmd = ["sudo", "-S", "-p", "", sys.executable, os.path.abspath(__file__),
               "sonda", "--secondi", str(self.secondi), "--uscita", self.uscita]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.PIPE, text=True)
        self.proc.stdin.write(self.parola + "\n")
        self.proc.stdin.flush()
        # si aspetta che la sonda sia davvero in piedi, o si dichiara il buco
        for _ in range(100):
            if os.path.exists(self.uscita) and os.path.getsize(self.uscita) > 0:
                prima = json.loads(open(self.uscita).readline())
                if prima.get("errore"):
                    return prima["errore"]
                return None
            time.sleep(0.1)
        return "la sonda dei motori non è partita entro 10 s"

    def ferma(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def campioni(self):
        """Torna la lista dei campioni, oppure ⛔ None se il file non dice niente."""
        if not os.path.exists(self.uscita):
            return None
        righe = []
        for r in open(self.uscita):
            r = r.strip()
            if not r:
                continue
            d = json.loads(r)
            if "v" in d and d["v"] is not None:
                righe.append(d)
        return righe or None


def occupazione(campioni, da=None, a=None):
    """Da due campioni ricava i nanosecondi occupati per motore, e il tempo trascorso.

    ⛔ Torna None se non ci sono almeno due campioni: «non ho misurato» ≠ «zero».
    """
    if da is None or a is None:
        if not campioni or len(campioni) < 2:
            return None
        p = campioni[0] if da is None else da
        u = campioni[-1] if a is None else a
    else:
        p, u = da, a
    dt = u["t"] - p["t"]
    if dt <= 0:
        return None
    fuori = {"secondi": round(dt, 3)}
    for k in p["v"]:
        fuori[k] = u["v"][k] - p["v"][k]
    # ⚠ l'energia del pacchetto è un contatore che gira: si scarta il giro invece di
    #   inventarsi un numero negativo.
    e0, e1 = p.get("energia_uj"), u.get("energia_uj")
    fuori["watt_pacchetto"] = (round((e1 - e0) / 1e6 / dt, 1)
                               if (e0 is not None and e1 is not None and e1 >= e0) else None)
    fuori["temp_C_inizio"] = None if p.get("temp_mc") is None else p["temp_mc"] / 1000
    fuori["temp_C_fine"] = None if u.get("temp_mc") is None else u["temp_mc"] / 1000
    return fuori


# ═════════════════════════════════════════════════════════════════════════════
# METRO 2 · la frequenza della GPU e i motivi di freno
# ═════════════════════════════════════════════════════════════════════════════

MOTIVI_FRENO = ["pl1", "pl2", "pl4", "prochot", "ratl", "thermal", "vr_tdc", "vr_thermalert"]


def stato_gpu():
    s = {
        "act_mhz": leggi_intero(f"{CARD}/gt_act_freq_mhz"),
        "cur_mhz": leggi_intero(f"{CARD}/gt_cur_freq_mhz"),
        "RP0": leggi_intero(f"{CARD}/gt_RP0_freq_mhz"),
        "RP1": leggi_intero(f"{CARD}/gt_RP1_freq_mhz"),
        "RPn": leggi_intero(f"{CARD}/gt_RPn_freq_mhz"),
        "freni": {},
    }
    for m in MOTIVI_FRENO:
        v = open(f"{CARD}/gt/gt0/throttle_reason_{m}").read().strip() \
            if os.path.exists(f"{CARD}/gt/gt0/throttle_reason_{m}") else None
        s["freni"][m] = v
    return s


class Campionatore(threading.Thread):
    """Campiona frequenza e freni ogni `passo` secondi, in un filo a parte."""

    def __init__(self, passo=1.0):
        super().__init__(daemon=True)
        self.passo = passo
        self.campioni = []
        self.vivo = True

    def run(self):
        t0 = time.monotonic()
        while self.vivo:
            s = stato_gpu()
            s["t"] = round(time.monotonic() - t0, 2)
            self.campioni.append(s)
            time.sleep(self.passo)

    def ferma(self):
        self.vivo = False
        self.join(timeout=3)
        return self.campioni or None  # ⛔ None se non ha campionato


def riassunto_frequenza(campioni, finestra=30):
    """Media della frequenza attiva nei primi e negli ultimi `finestra` secondi, e i freni visti."""
    if not campioni or len(campioni) < 4:
        return None
    val = [(c["t"], c["act_mhz"]) for c in campioni if c["act_mhz"] is not None]
    if len(val) < 4:
        return None
    tmax = val[-1][0]
    primi = [v for t, v in val if t <= min(finestra, tmax / 3)]
    ultimi = [v for t, v in val if t >= tmax - min(finestra, tmax / 3)]
    if not primi or not ultimi:
        return None
    freni = set()
    for c in campioni:
        for m, v in c["freni"].items():
            if v == "1":
                freni.add(m)
    return {
        "primi_mhz": round(sum(primi) / len(primi), 1),
        "ultimi_mhz": round(sum(ultimi) / len(ultimi), 1),
        "minimo_mhz": min(v for _, v in val),
        "massimo_mhz": max(v for _, v in val),
        "durata_s": round(tmax, 1),
        "freni_visti": sorted(freni),
    }


# ═════════════════════════════════════════════════════════════════════════════
# La sorgente: un filmato grezzo, riletto dalla cache, che non costa GPU
# ═════════════════════════════════════════════════════════════════════════════

def prepara_sorgente(cartella, larghezza=1920, altezza=1080, fotogrammi=60):
    percorso = os.path.join(cartella, f"sorgente-{larghezza}x{altezza}-{fotogrammi}.nv12")
    atteso = larghezza * altezza * 3 // 2 * fotogrammi
    if os.path.exists(percorso) and os.path.getsize(percorso) == atteso:
        return percorso
    os.makedirs(cartella, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
           "-f", "lavfi", "-i",
           f"testsrc2=size={larghezza}x{altezza}:rate=30:duration={fotogrammi/30}",
           "-pix_fmt", "nv12", "-f", "rawvideo", percorso]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or os.path.getsize(percorso) != atteso:
        raise RuntimeError(f"sorgente non preparata: {r.stderr[:400]}")
    return percorso


# ═════════════════════════════════════════════════════════════════════════════
# Un giro: N codifiche insieme, a parità di richiesta
# ═════════════════════════════════════════════════════════════════════════════

RE_FPS = re.compile(r"frame=\s*(\d+).*?fps=\s*([\d.]+)", re.S)


# ⭐⭐ QVBR — E I TRE NUMERI NON SI SCRIVONO A MANO: SI DERIVANO DAL PAVIMENTO
#
# ⛔ Sono gli stessi conti di `src/codificatore.c` (`TETTO_QUOTA_FILO 80`,
#    `TETTO_QUOTA_PUNTO 75`, `TETTO_VBV_MS 40`), ripetuti qui perché questo banco
#    parla a `ffmpeg` e non al prodotto. ⚠ E il fatto che siano ripetuti è un
#    posto dove divergere: chi cambia i numeri là dentro deve cambiarli qui, e la
#    prova che non siano divergiti la dà `10-b88-saturatore.py bitrate`, che
#    quei tre numeri li **rilegge dal contesto** del prodotto invece di dedurli.
#
# ⛔ E `punto < filo` NON è una raffinatezza: con `rc_max_rate == bit_rate` il
#    driver Intel **deduce CBR** — nessun errore, nessun avviso, nessuna riga di
#    registro, e c'era una bolletta. È R31, la lezione più cara del progetto.
def numeri_del_tetto(pavimento_mbit):
    filo = int(pavimento_mbit * 1e6 * 80 / 100)
    punto = int(filo * 75 / 100)
    serbatoio = int(filo * 40 / 1000)   # 40 ms di VBV, in bit
    return {"rc": "QVBR", "b": f"{punto}", "maxrate": f"{filo}",
            "bufsize": f"{serbatoio}", "qp": 26, "pavimento_mbit": pavimento_mbit}


def comando_ffmpeg(sorgente, uscita, larghezza, altezza, fotogrammi, richiesta,
                   codec="h264_vaapi", registro=None):
    """`richiesta` è un dizionario:
       {'rc': 'CQP', 'qp': 26} · {'rc': 'CBR', 'b': '10M'} ·
       {'rc': 'QVBR', 'b': …, 'maxrate': …, 'bufsize': …, 'qp': 26}."""
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y",
           "-loglevel", "info", "-stats", "-stats_period", "5",
           "-vaapi_device", NODO,
           "-f", "rawvideo", "-pix_fmt", "nv12",
           "-s", f"{larghezza}x{altezza}", "-r", "30",
           "-stream_loop", "-1", "-i", sorgente,
           "-vf", "format=nv12,hwupload",
           "-c:v", codec, "-g", "60", "-low_power", "1",
           # ⛔ Il modo si chiede PER NOME, mai `auto`: `auto` sceglie in base
           #    alle altre opzioni, ed è esattamente il gesto di R31.
           "-rc_mode", richiesta["rc"]]
    if richiesta["rc"] == "CQP":
        cmd += ["-qp", str(richiesta["qp"])]
    elif richiesta["rc"] == "QVBR":
        # ⚠ Sotto QVBR il `qp` NON è il quantizzatore: è il FATTORE DI QUALITÀ, e
        #   conta. Sotto VBR sarebbe ignorato — `[M]` byte per byte identico con
        #   e senza — ed è la ragione per cui il prodotto usa QVBR e non VBR.
        cmd += ["-b:v", richiesta["b"], "-maxrate", richiesta["maxrate"],
                "-bufsize", richiesta["bufsize"], "-qp", str(richiesta["qp"])]
    else:
        cmd += ["-b:v", richiesta["b"], "-maxrate", richiesta["b"],
                "-bufsize", richiesta["b"]]
    if "qualita" in richiesta:
        cmd += ["-quality", str(richiesta["qualita"])]
    cmd += ["-frames:v", str(fotogrammi), "-f", codec.split("_")[0], uscita]
    return cmd


def un_giro(n, sorgente, cartella, larghezza, altezza, fotogrammi, richiesta,
            etichetta, sonda=None, passo_freq=0.25):
    """Lancia `n` codifiche insieme e riferisce. Torna un dizionario con i numeri, e
    ⛔ `None` nei campi che non è riuscito a misurare."""
    os.makedirs(cartella, exist_ok=True)
    processi = []
    uscite = []
    camp = Campionatore(passo=passo_freq)
    if sonda:
        prima = sonda.campioni()
        segna_prima = prima[-1] if prima else None
    else:
        segna_prima = None
    camp.start()
    t0 = time.monotonic()
    for k in range(n):
        u = os.path.join(cartella, f"{etichetta}-{n}x-{k}.bin")
        uscite.append(u)
        cmd = comando_ffmpeg(sorgente, u, larghezza, altezza, fotogrammi, richiesta)
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                             text=True)
        processi.append(p)
    # ⛔⛔ I registri si svuotano IN PARALLELO, uno per filo.
    #    Leggerli in fila bloccherebbe i processi 1..n-1 sul tubo pieno (64 KB) mentre
    #    si aspetta il processo 0: la misura misurerebbe il banco, non la GPU. È la
    #    forma di `LEZIONI.md` §1.26 dentro un solo banco.
    registri = [None] * len(processi)
    finiti = [None] * len(processi)

    def svuota(k, p):
        registri[k] = p.stderr.read()
        p.wait()
        finiti[k] = time.monotonic() - t0

    fili = [threading.Thread(target=svuota, args=(k, p), daemon=True)
            for k, p in enumerate(processi)]
    for f in fili:
        f.start()
    for f in fili:
        f.join()
    esiti = []
    for k, p in enumerate(processi):
        esiti.append({"indice": k, "uscita": p.returncode,
                      "registro": (registri[k] or "")[-3000:],
                      "secondi_processo": round(finiti[k] or 0.0, 3)})
    dt = time.monotonic() - t0
    campioni_freq = camp.ferma()
    if sonda:
        dopo = sonda.campioni()
        segna_dopo = dopo[-1] if dopo else None
    else:
        segna_dopo = None

    for k, e in enumerate(esiti):
        u = uscite[k]
        if e["uscita"] == 0 and os.path.exists(u):
            b = open(u, "rb").read()
            e["byte"] = len(b)
            e["md5"] = hashlib.md5(b).hexdigest()
            e["bitrate_mbit"] = round(len(b) * 8 / (fotogrammi / 30) / 1e6, 3)
        else:
            e["byte"] = None      # ⛔ None non è zero
            e["md5"] = None
            e["bitrate_mbit"] = None
        m = RE_FPS.findall(e["registro"])
        e["fotogrammi_visti"] = int(m[-1][0]) if m else None
        # ⚠ `fps=` di ffmpeg vale 0.0 sui giri corti: il ritmo si calcola qui, sul tempo
        #    di parete del processo, e i fotogrammi si contano da quel che è ARRIVATO (§1.30).
        e["fps"] = (round(e["fotogrammi_visti"] / e["secondi_processo"], 1)
                    if e["fotogrammi_visti"] and e["secondi_processo"] > 0 else None)
        e["fps_dichiarato_da_ffmpeg"] = float(m[-1][1]) if m else None
        e["ripiego_in_software"] = ("Using VAAPI/EncSlice " in e["registro"]
                                    or "libx264" in e["registro"])
        # ⛔⛔ LA FRASE CON CUI LIBAVCODEC DEDUCE AL POSTO DEL DRIVER, e si estrae
        #    QUI perché qui il registro è INTERO: `confronto()` lo tronca agli
        #    ultimi 600 byte per non gonfiare il JSON, e questa riga compare
        #    all'APERTURA — un predicato che la cercasse dopo non la troverebbe
        #    mai e darebbe verde per sempre.  ⚠ È la forma E9 di `REVIEWER.md`:
        #    il testimone si raccoglie dove esiste, non dove fa comodo leggerlo.
        e["libavcodec_ha_dedotto"] = "assuming CQP only" in (e["registro"] or "")
        e["file"] = u

    occ = None
    if segna_prima and segna_dopo:
        occ = occupazione(None, da=segna_prima, a=segna_dopo)

    return {
        "etichetta": etichetta,
        "codifiche": n,
        "richiesta": richiesta,
        "risoluzione": f"{larghezza}x{altezza}",
        "fotogrammi_per_codifica": fotogrammi,
        "secondi": round(dt, 2),
        "fps_totale": (round(sum(e["fps"] for e in esiti) , 1)
                       if all(e["fps"] is not None for e in esiti) else None),
        "fps_per_flusso": [e["fps"] for e in esiti],
        "esiti": esiti,
        "motori": occ,
        "frequenza": riassunto_frequenza(campioni_freq, finestra=max(5, dt / 3)),
        "campioni_freq": campioni_freq,
    }


# ═════════════════════════════════════════════════════════════════════════════
# I PREDICATI — ⛔ ognuno può dire None, e allora non si giudica
# ═════════════════════════════════════════════════════════════════════════════

def p_non_e_software(giro, soglia_frazione=0.10):
    """I motori video devono risultare occupati. Se la PMU non ha misurato → None."""
    occ = giro.get("motori")
    if occ is None:
        return None, "i motori non sono stati misurati"
    busy = occ.get("vcs0-busy", 0) + occ.get("vcs1-busy", 0)
    tot = occ["secondi"] * 1e9
    frazione = busy / tot if tot else None
    if frazione is None:
        return None, "tempo trascorso nullo"
    ok = frazione >= soglia_frazione
    return ok, f"motori video occupati al {frazione*100:.1f}% di un motore-tempo"


def p_bitrate_obbedisce(giro, tolleranza=0.25):
    """Con CBR il bitrate misurato deve stare attorno a quello chiesto."""
    r = giro["richiesta"]
    if r["rc"] != "CBR":
        return None, "predicato applicabile solo a CBR"
    chiesto = float(r["b"].rstrip("M"))
    misure = [e["bitrate_mbit"] for e in giro["esiti"]]
    if any(m is None for m in misure):
        return None, "un flusso non ha prodotto byte: non si giudica"
    peggio = max(abs(m - chiesto) / chiesto for m in misure)
    return peggio <= tolleranza, (
        f"chiesti {chiesto} Mbit/s, misurati {min(misure)}–{max(misure)}; "
        f"scarto peggiore {peggio*100:.1f}%")


def p_qvbr_obbedisce(giro, tolleranza=0.15):
    """⭐⭐ QVBR — ED È IL MODO CHE IL PRODOTTO USA QUANDO IL TETTO È ACCESO.

    ⛔ Il predicato NON è quello del CBR, e confonderli sarebbe misurare due
       grandezze sotto la stessa etichetta: il CBR ha un bitrate da RITROVARE, il
       QVBR ha un **tetto da non superare** e un punto di lavoro che è un
       obiettivo, non una promessa. ⇒ Qui si giudica una cosa sola, quella
       verificabile senza ambiguità: **il flusso sta sotto il filo?**

    ⛔ E il rosso porta il NUMERO, non arrotondato: «ha sforato» non dice se è un
       margine o un ordine di grandezza.

    ⚠ Quel che questo predicato NON sa dire, e va letto insieme a lui: a scena
      FACILE stare sotto il filo è gratis, e un CBR travestito lo passerebbe.
      La domanda *«spende quando non serve?»* si fa a scena facile e la fa
      `10-b88-saturatore.py bitrate` (P3), non questo.
    """
    r = giro["richiesta"]
    if r["rc"] != "QVBR":
        return None, "predicato applicabile solo a QVBR"
    filo = float(r["maxrate"]) / 1e6
    misure = [e["bitrate_mbit"] for e in giro["esiti"]]
    if any(m is None for m in misure):
        return None, "un flusso non ha prodotto byte: non si giudica"
    ammesso = filo * (1 + tolleranza)
    peggio = max(misure)
    if peggio <= ammesso:
        return True, (f"filo {filo:.3f} Mbit/s, i flussi fanno "
                      f"{min(misure):.3f}–{peggio:.3f} (ammesso {ammesso:.3f}): "
                      f"il tetto tiene")
    return False, (f"⛔ BERSAGLIO MANCATO: filo {filo:.3f} Mbit/s, il peggiore fa "
                   f"**{peggio:.3f}** — sforo di {peggio - filo:.3f} Mbit/s, cioè "
                   f"il {(peggio / filo - 1) * 100:.1f}% in più "
                   f"(tolleranza {tolleranza * 100:.0f}% ⇒ {ammesso:.3f})")


def p_modo_ottenuto(giro):
    """⛔⛔ IL MODO CHIESTO È QUELLO OTTENUTO? — e si guarda il FLUSSO, non la
    rilettura.

    `fasi/10-…md` §6.6: su questo driver `vaQueryConfigAttributes` sulla config
    creata rende **la maschera delle capacità**, identica qualunque cosa si sia
    chiesta ⇒ *quale* modo sia in vigore **non si legge**. ⇒ Quel che resta è:
      (a) `ffmpeg` deve aver aperto senza ripiegare — se il modo non c'è,
          `avcodec_open2` fallisce e il processo esce diverso da zero;
      (b) il flusso deve esistere e portare byte.
    ⛔ E se il registro contiene la frase con cui libavcodec DEDUCE al posto del
       driver (*«assuming CQP only»*), il giro non si conta: quell'assunzione è
       di ffmpeg, non del driver, ed è R31 in una veste nuova."""
    esiti = giro["esiti"]
    if any(e["uscita"] is None for e in esiti):
        return None, "un processo non ha riferito il proprio esito"
    falliti = [e["indice"] for e in esiti if e["uscita"] != 0]
    if falliti:
        return False, (f"⛔ il modo «{giro['richiesta']['rc']}» è stato CHIESTO e "
                       f"i flussi {falliti} non si sono aperti: il driver non ce "
                       f"l'ha, e NON si ripiega su un altro modo (sarebbe R31 "
                       f"dall'altro capo)")
    if any(e.get("libavcodec_ha_dedotto") is None for e in esiti):
        return None, ("il testimone «libavcodec ha dedotto» non è stato raccolto: "
                      "non si conclude che non abbia dedotto")
    dedotti = [e["indice"] for e in esiti if e["libavcodec_ha_dedotto"]]
    if dedotti:
        return False, (f"⛔⛔ libavcodec ha DEDOTTO il modo al posto del driver "
                       f"(«assuming CQP only») sui flussi {dedotti}: quell'assunzione "
                       f"è SUA, non del driver — è R31 in una veste nuova")
    senza = [e["indice"] for e in esiti if not e["byte"]]
    if senza:
        return None, f"i flussi {senza} non hanno prodotto byte: non si giudica"
    return True, (f"modo «{giro['richiesta']['rc']}» chiesto per nome, "
                  f"{len(esiti)}/{len(esiti)} flussi aperti e con byte, nessuna "
                  f"deduzione di libavcodec nel registro")


def p_qualita_invariata(solo, sotto_carico):
    """A parità di richiesta, il flusso prodotto sotto carico deve essere IDENTICO
    a quello prodotto da solo. Se cambia, qualcosa ha deciso al posto nostro."""
    rif = solo["esiti"][0]["md5"]
    if rif is None:
        return None, "il giro di riferimento non ha prodotto byte"
    md5 = [e["md5"] for e in sotto_carico["esiti"]]
    if any(m is None for m in md5):
        return None, "un flusso sotto carico non ha prodotto byte"
    uguali = sum(1 for m in md5 if m == rif)
    return uguali == len(md5), (
        f"{uguali}/{len(md5)} flussi identici byte per byte al giro da solo")


def p_frequenza_tiene(giro, calo_ammesso=0.10):
    """⚠ Il CALO e i FRENI sono due grandezze diverse e vanno tenute separate.

    Il giudizio è sul **calo**: è quello che si sente. I motivi di freno si
    riferiscono accanto, perché un motivo acceso a **qualunque** carico — anche a
    un flusso solo — non è il freno del carico, è come sta la macchina.
    """
    f = giro.get("frequenza")
    if f is None:
        return None, "la frequenza non è stata campionata"
    if f["primi_mhz"] <= 0:
        return None, "frequenza iniziale nulla: metro non attendibile"
    calo = (f["primi_mhz"] - f["ultimi_mhz"]) / f["primi_mhz"]
    return calo <= calo_ammesso, (
        f"{f['primi_mhz']} → {f['ultimi_mhz']} MHz in {f['durata_s']} s "
        f"(calo {calo*100:.1f}%); freni accesi: {f['freni_visti'] or 'nessuno'}")


# ═════════════════════════════════════════════════════════════════════════════
# LA TARATURA — ⛔ prima dei numeri (§1.33)
# ═════════════════════════════════════════════════════════════════════════════

def taratura(cartella, sonda, larghezza=1920, altezza=1080):
    """Inietta valori NOTI e verifica che i metri li ritrovino."""
    esito = {"metri": {}}
    sorg = prepara_sorgente(cartella, larghezza, altezza)

    # ── metro dei motori: (a) a vuoto ≈ 0 ────────────────────────────────────
    a = sonda.campioni()
    time.sleep(4)
    b = sonda.campioni()
    if not a or not b:
        esito["metri"]["motori_a_vuoto"] = {"valore": None,
                                            "nota": "la sonda non ha campionato"}
    else:
        occ = occupazione(None, da=a[-1], a=b[-1])
        fraz = ((occ["vcs0-busy"] + occ["vcs1-busy"]) / (occ["secondi"] * 1e9)
                if occ else None)
        esito["metri"]["motori_a_vuoto"] = {
            "valore": None if fraz is None else round(fraz, 5),
            "atteso": "< 0.02", "ok": None if fraz is None else fraz < 0.02}

    # ── metro dei motori: (b) raddoppiando i fotogrammi deve raddoppiare ─────
    g1 = un_giro(1, sorg, cartella, larghezza, altezza, 1200,
                 {"rc": "CQP", "qp": 26}, "tara-1200", sonda=sonda)
    g2 = un_giro(1, sorg, cartella, larghezza, altezza, 2400,
                 {"rc": "CQP", "qp": 26}, "tara-2400", sonda=sonda)
    b1 = (g1["motori"] or {}).get("vcs0-busy", None)
    b1b = (g1["motori"] or {}).get("vcs1-busy", None)
    b2 = (g2["motori"] or {}).get("vcs0-busy", None)
    b2b = (g2["motori"] or {}).get("vcs1-busy", None)
    if None in (b1, b1b, b2, b2b) or (b1 + b1b) == 0:
        rapporto = None
    else:
        rapporto = (b2 + b2b) / (b1 + b1b)
    esito["metri"]["motori_raddoppio"] = {
        "ns_1200": None if b1 is None else b1 + b1b,
        "ns_2400": None if b2 is None else b2 + b2b,
        "rapporto": None if rapporto is None else round(rapporto, 3),
        "atteso": "1.8 – 2.2",
        "ok": None if rapporto is None else 1.8 <= rapporto <= 2.2,
    }

    # ── metro dei motori: (c) non può superare il tempo trascorso ────────────
    occ = g2["motori"]
    if occ is None:
        esito["metri"]["motori_limite"] = {"ok": None, "nota": "non misurato"}
    else:
        tetto = occ["secondi"] * 1e9
        esito["metri"]["motori_limite"] = {
            "vcs0_su_tempo": round(occ["vcs0-busy"] / tetto, 3),
            "vcs1_su_tempo": round(occ["vcs1-busy"] / tetto, 3),
            "ok": occ["vcs0-busy"] <= tetto * 1.02 and occ["vcs1-busy"] <= tetto * 1.02,
        }

    # ── metro della frequenza: a riposo sotto RP1, sotto carico sopra RP1 ────
    s = stato_gpu()
    time.sleep(3)
    riposo = stato_gpu()["act_mhz"]
    f = g2.get("frequenza")
    esito["metri"]["frequenza"] = {
        "RP1": s["RP1"], "RPn": s["RPn"], "RP0": s["RP0"],
        "a_riposo_mhz": riposo,
        "sotto_carico_mhz": None if f is None else f["massimo_mhz"],
        "ok": None if (riposo is None or f is None) else
              (riposo < s["RP1"] and f["massimo_mhz"] > s["RP1"]),
    }

    # ── metro del bitrate: si chiedono 5 e 20 Mbit/s e li si deve ritrovare ──
    letture = {}
    for chiesto in ("5M", "20M"):
        g = un_giro(1, sorg, cartella, larghezza, altezza, 1200,
                    {"rc": "CBR", "b": chiesto}, f"tara-cbr-{chiesto}", sonda=sonda)
        letture[chiesto] = g["esiti"][0]["bitrate_mbit"]
    ok = None
    if None not in letture.values():
        ok = (abs(letture["5M"] - 5) / 5 < 0.25 and abs(letture["20M"] - 20) / 20 < 0.25)
    esito["metri"]["bitrate"] = {"chiesti": [5, 20], "letti": letture,
                                 "atteso": "±25%", "ok": ok}

    esito["ritmo_da_solo"] = {
        "fps_1200": g1["esiti"][0]["fps"],
        "fps_2400": g2["esiti"][0]["fps"],
        "motori_1200": g1["motori"],
        "motori_2400": g2["motori"],
    }
    esito["tarato"] = all(v.get("ok") is True for v in esito["metri"].values())
    return esito


# ═════════════════════════════════════════════════════════════════════════════
# IL CONFRONTO — 1 / 4 / 8 codifiche a parità di richiesta
# ═════════════════════════════════════════════════════════════════════════════

def confronto(cartella, sonda, gradini=(1, 4, 8), fotogrammi=600,
              larghezza=1920, altezza=1080):
    sorg = prepara_sorgente(cartella, larghezza, altezza)
    esito = {"gradini": gradini, "risoluzione": f"{larghezza}x{altezza}",
             "fotogrammi": fotogrammi, "giri": {}, "predicati": []}
    # ⛔ TRE MODI E NON DUE, e il terzo è quello che al primo giro mancava.
    #    CQP e CBR sono i due ESTREMI, quelli in cui il predicato del bitrate è
    #    verificabile senza ambiguità. ⭐ QVBR è **il modo che il prodotto usa
    #    quando il tetto è acceso**, ed è quello con una discrezionalità in più:
    #    è lì che la risposta a «sotto carico decide qualcuno al posto nostro?»
    #    può cambiare. ⚠ Le tre colonne non si mediano fra loro.
    richieste = {
        "CQP26": {"rc": "CQP", "qp": 26},
        "CBR10": {"rc": "CBR", "b": "10M"},
        "QVBR20": numeri_del_tetto(20),   # il pavimento del prodotto: filo 16, punto 12
    }
    for nome, r in richieste.items():
        esito["giri"][nome] = {}
        for n in gradini:
            g = un_giro(n, sorg, cartella, larghezza, altezza, fotogrammi, r,
                        f"conf-{nome}", sonda=sonda)
            # i campioni di frequenza sono voluminosi: si tiene il riassunto
            g.pop("campioni_freq", None)
            for e in g["esiti"]:
                e["registro"] = e["registro"][-600:]
            esito["giri"][nome][n] = g
            time.sleep(2)

    # ── i predicati ─────────────────────────────────────────────────────────
    def agg(nome, coppia):
        esito["predicati"].append({"nome": nome, "esito": coppia[0], "motivo": coppia[1]})

    for nome in richieste:
        for n in gradini:
            g = esito["giri"][nome][n]
            agg(f"P1 non è software · {nome} × {n}", p_non_e_software(g))
            agg(f"P0 il modo chiesto è quello ottenuto · {nome} × {n}",
                p_modo_ottenuto(g))
            if nome.startswith("CBR"):
                agg(f"P2 CBR obbedisce · {nome} × {n}", p_bitrate_obbedisce(g))
            if nome.startswith("QVBR"):
                agg(f"P2-bis QVBR sta sotto il filo · {nome} × {n}",
                    p_qvbr_obbedisce(g))
        solo = esito["giri"][nome][gradini[0]]
        for n in gradini[1:]:
            agg(f"P3 qualità invariata · {nome} 1 → {n}",
                p_qualita_invariata(solo, esito["giri"][nome][n]))
    return esito


def giro_lungo(cartella, sonda, minuti=10, n=8, larghezza=1920, altezza=1080):
    """⚠ `LEZIONI.md` §1.32: i giri corti sottostimano. Qui si sta sul carico a lungo."""
    sorg = prepara_sorgente(cartella, larghezza, altezza)
    # ⛔ Il numero di fotogrammi NON si indovina: il ritmo di questo ferro non è 30 fps.
    #    Si fa un assaggio corto allo stesso carico e si dimensiona su quello, se no
    #    «dieci minuti» diventano tre e §1.32 resta non provata.
    assaggio = un_giro(n, sorg, cartella, larghezza, altezza, 400,
                       {"rc": "CQP", "qp": 26}, "assaggio", sonda=sonda)
    ritmo = (assaggio["fps_totale"] or 0) / n
    if ritmo <= 0:
        return {"errore": "⛔ l'assaggio non ha dato un ritmo: non misuro il giro lungo",
                "minuti_chiesti": minuti, "codifiche": n}
    fotogrammi = int(minuti * 60 * ritmo)
    esito = {"minuti_chiesti": minuti, "codifiche": n,
             "assaggio_fps_per_flusso": round(ritmo, 1),
             "fotogrammi_per_flusso": fotogrammi}
    g = un_giro(n, sorg, cartella, larghezza, altezza, fotogrammi,
                {"rc": "CQP", "qp": 26}, "lungo", sonda=sonda, passo_freq=1.0)
    esito["frequenza"] = g["frequenza"]
    esito["motori"] = g["motori"]
    esito["secondi"] = g["secondi"]
    esito["fps_per_flusso"] = g["fps_per_flusso"]
    esito["fps_totale"] = g["fps_totale"]
    # ⭐ il meccanismo accanto al sintomo (§1.31): l'andamento, non solo i due estremi
    camp = g.get("campioni_freq") or []
    esito["andamento_mhz"] = [
        {"t": c["t"], "mhz": c["act_mhz"]} for c in camp[:: max(1, len(camp) // 60)]
    ]
    esito["predicati"] = [
        {"nome": f"P1 non è software · lungo × {n}", **dict(zip(
            ("esito", "motivo"), p_non_e_software(g)))},
        {"nome": f"P4 la frequenza tiene · lungo × {n}", **dict(zip(
            ("esito", "motivo"), p_frequenza_tiene(g)))},
    ]
    return esito


def memoria(cartella, quanti=(1, 8, 64, 256), larghezza=1920, altezza=1080):
    """Quanto costa in RAM di sistema un contesto di codifica. ⚠ Su un'integrata non
    c'è VRAM: i buffer stanno nella stessa memoria del sistema."""
    import importlib.util
    qui = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "vaapi", os.path.join(qui, "10-b94-ferro-vaapi.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    def libera_kb():
        for r in open("/proc/meminfo"):
            if r.startswith("MemAvailable:"):
                return int(r.split()[1])
        return None

    fuori = {"risoluzione": f"{larghezza}x{altezza}", "gradini": []}
    p = m.PROFILI["VAProfileH264High"]
    i = m.INGRESSI["VAEntrypointEncSliceLP"]
    for n in quanti:
        prima = libera_kb()
        va = m.Va(NODO).apri()
        risorse = []
        errore = None
        for _ in range(n):
            cfg, e = va.crea_config(p, i, [(m.ATTRIBUTI["VAConfigAttribRTFormat"], 1)])
            if cfg is None:
                errore = e
                break
            sup, e = va.crea_superfici(larghezza, altezza, 4)
            if sup is None:
                errore = e
                break
            ctx, e = va.crea_contesto(cfg, larghezza, altezza, sup, 4)
            if ctx is None:
                errore = e
                break
            risorse.append((cfg, sup, ctx))
        dopo = libera_kb()
        for cfg, sup, ctx in risorse:
            va.distruggi_contesto(ctx)
            va.distruggi_superfici(sup, 4)
            va.distruggi_config(cfg)
        va.chiudi()
        fuori["gradini"].append({
            "contesti": len(risorse),
            "errore": errore,
            "mb_consumati": None if (prima is None or dopo is None)
                            else round((prima - dopo) / 1024, 1),
            "mb_per_contesto": None if (prima is None or dopo is None or not risorse)
                               else round((prima - dopo) / 1024 / len(risorse), 2),
        })
    fuori["memlock_kb"] = None
    try:
        import resource
        fuori["memlock_kb"] = resource.getrlimit(resource.RLIMIT_MEMLOCK)[0] // 1024
        fuori["nofile"] = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    except Exception:
        pass
    return fuori


# ═════════════════════════════════════════════════════════════════════════════
# ⛔ --certifica · sano → guasto → risanato
# ═════════════════════════════════════════════════════════════════════════════

def certifica(cartella, sonda):
    righe, esiti = [], []

    def registra(nome, sano, guasto, risanato, atteso_guasto=False):
        ok = (sano is True) and (guasto is atteso_guasto) and (risanato is True)
        esiti.append(ok)
        righe.append(f"  {'✅' if ok else '⛔'} {nome}: "
                     f"sano={sano} → guasto={guasto} → risanato={risanato}")

    # ⚠ 3000 fotogrammi e non 300: con 300 il giro dura mezzo secondo e il
    #   campionatore della frequenza non fa in tempo a prendere quattro campioni —
    #   il guasto G5 non si potrebbe innestare, e un guasto non innestato vale zero.
    sorg = prepara_sorgente(cartella, 1280, 720)
    base = un_giro(1, sorg, cartella, 1280, 720, 3000, {"rc": "CQP", "qp": 26},
                   "cert", sonda=sonda)
    cbr = un_giro(1, sorg, cartella, 1280, 720, 3000, {"rc": "CBR", "b": "10M"},
                  "cert-cbr", sonda=sonda)

    import copy

    # ── G1 · il metro dei motori è congelato: il ripiego in software non si vede più ──
    s1 = p_non_e_software(base)[0]
    g = copy.deepcopy(base)
    g["motori"] = {"secondi": g["motori"]["secondi"], "vcs0-busy": 0, "vcs1-busy": 0,
                   "rcs0-busy": 0, "vecs0-busy": 0, "rc6-residency": 0}
    g1 = p_non_e_software(g)[0]
    r1 = p_non_e_software(base)[0]
    registra("G1 motori a zero (ripiego in software simulato)", s1, g1, r1,
             atteso_guasto=False)

    # ── G2 · «None non è zero»: la PMU non ha misurato → il predicato NON giudica ──
    g = copy.deepcopy(base)
    g["motori"] = None
    g2 = p_non_e_software(g)[0]
    esiti.append(g2 is None)
    righe.append(f"  {'✅' if g2 is None else '⛔'} G2 motori non misurati: "
                 f"giudizio={g2!r} — atteso None, non False e non True")

    # ── G3 · un flusso alterato: la qualità invariata deve andare in rosso ──
    doppio = un_giro(2, sorg, cartella, 1280, 720, 3000, {"rc": "CQP", "qp": 26},
                     "cert2", sonda=sonda)
    s3 = p_qualita_invariata(base, doppio)[0]
    g = copy.deepcopy(doppio)
    g["esiti"][0]["md5"] = "0" * 32
    g3 = p_qualita_invariata(base, g)[0]
    r3 = p_qualita_invariata(base, doppio)[0]
    registra("G3 flusso alterato sotto carico", s3, g3, r3, atteso_guasto=False)

    # ── G4 · il bitrate non obbedisce: metà di quel che si è chiesto ──
    s4 = p_bitrate_obbedisce(cbr)[0]
    g = copy.deepcopy(cbr)
    for e in g["esiti"]:
        e["bitrate_mbit"] = e["bitrate_mbit"] / 2
    g4 = p_bitrate_obbedisce(g)[0]
    r4 = p_bitrate_obbedisce(cbr)[0]
    registra("G4 bitrate a metà della richiesta", s4, g4, r4, atteso_guasto=False)

    # ── G5 · la frequenza crolla e i freni si accendono ──
    s5 = p_frequenza_tiene(base)[0]
    g = copy.deepcopy(base)
    g["frequenza"] = dict(g["frequenza"] or {})
    if not g["frequenza"]:
        g5 = None
    else:
        g["frequenza"]["ultimi_mhz"] = g["frequenza"]["primi_mhz"] * 0.5
        g["frequenza"]["freni_visti"] = ["thermal"]
        g5 = p_frequenza_tiene(g)[0]
    r5 = p_frequenza_tiene(base)[0]
    registra("G5 frequenza dimezzata + freno termico", s5, g5, r5, atteso_guasto=False)

    # ── G6 · taratura del metro: un raddoppio NOTO dev'essere visto come raddoppio ──
    #   (controllo positivo sullo strumento, §1.9 regola 2)
    trecento = base["motori"]
    seicento = un_giro(1, sorg, cartella, 1280, 720, 6000, {"rc": "CQP", "qp": 26},
                       "cert6000", sonda=sonda)["motori"]
    if trecento and seicento:
        r = ((seicento["vcs0-busy"] + seicento["vcs1-busy"]) /
             max(1, trecento["vcs0-busy"] + trecento["vcs1-busy"]))
        ok6 = 1.7 <= r <= 2.3
        righe.append(f"  {'✅' if ok6 else '⛔'} G6 taratura del metro dei motori: "
                     f"6000/3000 fotogrammi → rapporto {r:.2f} (atteso 1.7–2.3)")
    else:
        ok6 = False
        righe.append("  ⛔ G6 taratura del metro dei motori: non misurata")
    esiti.append(ok6)

    # ── G8 · QVBR: il tetto chiesto e NON rispettato ──
    #    ⛔ Il predicato è quello VERO (`p_qvbr_obbedisce`), non una copia: un
    #       guasto innestato su una copia certifica la copia.
    qvbr = un_giro(1, sorg, cartella, 1280, 720, 3000, numeri_del_tetto(20),
                   "cert-qvbr", sonda=sonda)
    s8, riga_s8 = p_qvbr_obbedisce(qvbr)
    g = copy.deepcopy(qvbr)
    for e in g["esiti"]:
        # il flusso spende il doppio del filo: il tetto NON ha morso
        e["bitrate_mbit"] = (e["bitrate_mbit"] or 0) + 32.0
    g8, riga_g8 = p_qvbr_obbedisce(g)
    c = copy.deepcopy(qvbr)
    for e in c["esiti"]:
        e["bitrate_mbit"] = None        # ⛔ «non ho misurato» ≠ «zero»
    c8, riga_c8 = p_qvbr_obbedisce(c)
    r8, _ = p_qvbr_obbedisce(qvbr)
    registra("G8 QVBR: il filo di 16 Mbit/s sforato", s8, g8, r8,
             atteso_guasto=False)
    righe.append(f"     sano:   {riga_s8}")
    righe.append(f"     guasto: {riga_g8}")
    esiti.append(c8 is None)
    righe.append(f"  {'✅' if c8 is None else '⛔'} G8-bis QVBR senza byte: "
                 f"giudizio={c8!r} — atteso None, non False e non True "
                 f"({riga_c8})")

    # ── G9 · il modo CHIESTO e non ottenuto ──
    #    ⚠ Il guasto si innesta sul TESTIMONE, non sui numeri: la frase con cui
    #      libavcodec deduce al posto del driver sul ferro vero non la si può far
    #      comparire senza rompere il driver.  ⛔ Si dichiara per quel che è: quel
    #      che si certifica è che il predicato la VEDA, non che il driver taccia.
    s9, _ = p_modo_ottenuto(qvbr)
    g = copy.deepcopy(qvbr)
    g["esiti"][0]["libavcodec_ha_dedotto"] = True
    g9, riga_g9 = p_modo_ottenuto(g)
    g = copy.deepcopy(qvbr)
    g["esiti"][0]["uscita"] = 1
    g9b, riga_g9b = p_modo_ottenuto(g)
    r9, _ = p_modo_ottenuto(qvbr)
    registra("G9 libavcodec deduce il modo («assuming CQP only»)", s9, g9, r9,
             atteso_guasto=False)
    righe.append(f"     {riga_g9}")
    registra("G9-bis il modo chiesto non si apre (avcodec_open2 fallisce)",
             s9, g9b, r9, atteso_guasto=False)
    righe.append(f"     {riga_g9b}")

    # ── G7 · quanta sollecitazione è ARRIVATA (§1.30) ──
    arrivati = [e["fotogrammi_visti"] for e in doppio["esiti"]]
    ok7 = all(a is not None and a >= 3000 for a in arrivati)
    esiti.append(ok7)
    righe.append(f"  {'✅' if ok7 else '⛔'} G7 sollecitazione arrivata: "
                 f"fotogrammi codificati per flusso = {arrivati} (chiesti 3000)")

    print("⛔ CERTIFICAZIONE — sano → guasto → risanato")
    print("\n".join(righe))
    tutti = all(esiti)
    print(f"\n{'✅ CERTIFICATO' if tutti else '⛔ NON CERTIFICATO'}: "
          f"{sum(esiti)}/{len(esiti)} guasti visti e risanati")
    return 0 if tutti else 1


# ═════════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", nargs="?", default="confronto",
                    choices=["sorgente", "taratura", "confronto", "lungo", "memoria",
                             "sonda"])
    ap.add_argument("--cartella", default=LAVORO)
    ap.add_argument("--gradini", default="1,4,8")
    ap.add_argument("--fotogrammi", type=int, default=600)
    ap.add_argument("--larghezza", type=int, default=1920)
    ap.add_argument("--altezza", type=int, default=1080)
    ap.add_argument("--minuti", type=float, default=10)
    ap.add_argument("--codifiche", type=int, default=8)
    ap.add_argument("--secondi", type=float, default=60)
    ap.add_argument("--uscita", default=None)
    ap.add_argument("--senza-sonda", action="store_true",
                    help="⚠ senza il metro dei motori: i predicati P1 diranno None")
    ap.add_argument("--certifica", action="store_true")
    a = ap.parse_args()

    if a.modo == "sonda":
        return sonda_motori(a.secondi, a.uscita)

    os.makedirs(a.cartella, exist_ok=True)
    if a.modo == "sorgente":
        print(prepara_sorgente(a.cartella, a.larghezza, a.altezza))
        return 0
    if a.modo == "memoria":
        print(json.dumps(memoria(a.cartella), indent=2, ensure_ascii=False))
        return 0

    sonda = None
    nota_sonda = None
    if not a.senza_sonda:
        durata = max(300, a.minuti * 60 * 2 + 300)
        sonda = SondaEsterna(os.path.join(a.cartella, "pmu.jsonl"), durata)
        nota_sonda = sonda.avvia()
        if nota_sonda:
            print(f"⚠ metro dei motori non disponibile: {nota_sonda}", file=sys.stderr)
            sonda.ferma()
            sonda = None
    try:
        if a.certifica:
            return certifica(a.cartella, sonda)
        if a.modo == "taratura":
            e = taratura(a.cartella, sonda, a.larghezza, a.altezza)
        elif a.modo == "lungo":
            e = giro_lungo(a.cartella, sonda, a.minuti, a.codifiche,
                           a.larghezza, a.altezza)
        else:
            gr = tuple(int(x) for x in a.gradini.split(","))
            e = confronto(a.cartella, sonda, gr, a.fotogrammi, a.larghezza, a.altezza)
        e["metro_motori"] = nota_sonda or "attivo"
        print(json.dumps(e, indent=2, ensure_ascii=False))
    finally:
        if sonda:
            sonda.ferma()
    return 0


if __name__ == "__main__":
    sys.exit(main())
