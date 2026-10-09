#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-risorse — IL CAMPIONATORE DELLE RISORSE, SUL SERVER (fase 16, §7 e §10)

    (sul server, da root)  python3 16-risorse.py --scatola kde --dir DIR [--intervallo 1]
                                                [--durata S] [--pss-ogni 5]
                                                [--segni-browser remotix-ff-,remotix-cr-]
    python3 16-risorse.py --certifica          (niente server: /proc e /sys FINTI)

Scrive DIR/risorse.jsonl, UNA riga JSON al secondo, finche' non riceve SIGTERM
(o SIGINT, o scade --durata).  La prima riga e' l'intestazione (`"tipo":
"intestazione"`: macchina, schede, scatola); le altre sono campioni.

⛔ Deve girare da ROOT (sudo): `smaps_rollup` e `fdinfo` dei processi degli
   inquilini e di root non si leggono da un altro utente.  Senza root il
   campionatore NON finge: i recinti che non puo' leggere li segnala in `avvisi`.

I TRE RECINTI (§7) — come si trovano, e perche' cosi'
----------------------------------------------------------------------------
`[M]` 25 set 2026, scatola kde con una sessione viva: i cgroup della scatola NON
coincidono coi recinti.  Il padre `remotix` sta in
  /machine.slice/libpod-<id>.scope/container/system.slice/rete11-server.service
ma il FIGLIO per sessione (`remotix`, uid dell'inquilino) sta nella scope di
logind dell'inquilino (`…/user.slice/user-4013.slice/session-c5.scope`), insieme
alla sessione; e le applicazioni lanciate dai banchi con `podman exec … runuser`
finiscono in `…/container/init.scope`.  ⇒ il recinto si decide PROCESSO PER
PROCESSO, e il cgroup serve a dire «dentro la scatola» e a contare il totale:

  remotix   dentro la scatola, e: nel cgroup `rete11-server.service`, OPPURE il
            suo eseguibile si chiama `remotix` (i figli per sessione).
            `per_inquilino` = i figli, per inquilino; `padre` = il resto.
  sessioni  dentro la scatola, uid >= 1000 (e non 65534), e non `remotix`:
            compositore, applicazioni, pipewire, dbus… — `per_inquilino` col
            nome letto da /etc/passwd DELLA scatola.
  browser   fuori dalla scatola: ogni processo la cui riga di comando porta un
            SEGNO dei profili dei banchi (`remotix-ff-` Firefox/Marionette,
            `remotix-cr-` Chrome/CDP: `12-client-veri.py` e `07-b46`) e TUTTI i
            suoi discendenti (i processi di contenuto di Firefox non portano il
            profilo nella riga di comando: li porta il padre).  ⭐ E' il modo
            piu' affidabile senza toccare l'attore: il profilo e' fatto dal
            banco, un Firefox dell'utente non lo ha.  (Se l'attore lanciasse
            ogni browser con `systemd-run --user --scope --unit=r16-browser-NN`
            il recinto sarebbe anche un cgroup: qui basta aggiungere il segno.)
  ⭐ --sistema xrdp (fasi/20 §7.4): la scatola e' `rete11-<desktop>-xrdp`; il recinto
            `remotix` e' xrdp (eseguibili xrdp, xrdp-sesman, xrdp-sesexec, xrdp-chansrv, o
            le unita' xrdp.service / xrdp-sesman.service) — QUI si comprime RemoteFX;
            `sessioni` comprende l'Xorg di ogni inquilino (xorgxrdp, la cattura);
            `browser` sono gli xfreerdp3 (segno `remotix-rdp-`); `labwc_cliente` anche
            gli Xvfb.  `remotix_pid` e' il demone xrdp (il padre delle connessioni).
            ⛔ Le due divisioni non si confrontano recinto per recinto: il confronto si
            fa sui TOTALI della scatola.
  + a parte, e NON recinti: `altro_scatola` (i processi di root della scatola
    che non sono remotix: systemd, journald, logind…) e `labwc_cliente` (i
    compositori senza schermo dei browser, utente dei banchi, sull'ospite).

⚠ LA CPU DEI PROCESSI BREVI.  Un `ls` battuto nel terminale nasce e muore fra
  due campioni: la lettura per processo non lo vede.  ⇒ `sessioni.cpu_core` e'
  preso dal cgroup della scatola (esatto) MENO remotix e `altro_scatola`
  (processi lunghi, esatti per processo); `sessioni.cpu_non_attribuita` e' la
  parte che nessun inquilino vivo si porta (i processi morti in mezzo).  Il
  browser non ha cgroup suo: i suoi processi sono lunghi, e la perdita e' detta.

LA SCHEDA GRAFICA — dal kernel, per processo (`/proc/<pid>/fdinfo`)
----------------------------------------------------------------------------
Chiavi GENERICHE dello standard DRM (Documentation/gpu/drm-usage-stats):
  drm-engine-<motore>: <ns> ns        tempo occupato, cumulativo ⇒ Δns/Δt = uso
  drm-engine-capacity-<motore>: <n>   motori di quella classe ⇒ si divide per n
  drm-cycles-<m> / drm-total-cycles-<m>   (xe) ⇒ Δcicli/Δtotali
  drm-total-/drm-resident-<regione>, drm-memory-<regione>: <n> [KiB|MiB]
  drm-client-id, drm-pdev             un client aperto su piu' fd o ereditato
                                      da un figlio si conta UNA volta
Intel i915: render · copy · video (capacita' 2) · video-enhance, regioni
system0/stolen-system0.  AMD amdgpu: gfx · compute · enc · dec (e dma/jpeg),
regioni vram/gtt/cpu (o `drm-memory-vram` sui nuclei vecchi).  Le CATEGORIE
(`disegno`, `video`, `video_enhance`, `copia`, `calcolo`) si decidono dal nome.
⭐ `intel_gpu_top` NON serve: fdinfo da' gia' l'uso per motore e per processo, e
  la frequenza, la strozzatura e la potenza vengono da sysfs (sotto).
  ⚠ Quel che fdinfo non vede: il lavoro del nucleo senza client (scansione
  dello schermo), e l'ultimo pezzo di un client chiuso fra due campioni.
  La somma per scheda e' «somma dei client», non il contatore del hardware.

Per scheda (sysfs): i915 `gt_cur_freq_mhz`, `gt_act_freq_mhz`,
`gt/gt0/throttle_reason_*` (strozzatura: le ragioni attive); amdgpu
`gpu_busy_percent`, `mem_info_vram_used/total`, hwmon (temperature, sclk,
potenza).  Temperatura della iGPU Intel: NON esiste un sensore suo ⇒ si registra
il pacchetto della CPU (coretemp, stessa piastrina), dichiarato come tale.
Potenza: RAPL `package` e `uncore` (= la iGPU) da powercap.

LA RIGA (campione):
  {"tipo":"campione","t":<epoch>,"ora":"…","dt_s":1.0,"scatola":"kde",
   "macchina":{"cpu_core","cpu_pct","carico":[1,5,15],"processi","thread",
               "mem_totale_mb","mem_disponibile_mb","mem_usata_mb"},
   "scatola_cg":{"cpu_core","mem_mb","anon_mb","pids"},
   "recinti":{"remotix":{…,"padre":{…},"per_inquilino":{nome:{…}}},
              "sessioni":{…,"cpu_non_attribuita","per_inquilino":{nome:{…}}},
              "browser":{…,"per_browser":[{"pid","tipo","profilo",…}]},
              "altro_scatola":{…},"labwc_cliente":{…}},
     dove {…} = {"cpu_core","processi","thread","rss_mb","pss_mb",
                 "gpu":{categoria:%},"gpu_mem_mb"}
   "gpu":{"<pdev>":{"scheda","driver","motori":{nome:%},"categorie":{…},
                    "freq_mhz","freq_att_mhz","temp_c","temp_fonte","potenza_w",
                    "strozzatura":[…],"occupata_pct","vram_usata_mb"}},
   "processi_gpu":[{"pid","comm","recinto","inquilino","pdev","motori":{…}}],
   "remotix_pid":n, "avvisi":[…], "misuratore":{"cpu_core","ms"}}
  `pss_mb`: PSS da smaps_rollup, ogni processo riletto ogni --pss-ogni secondi
  a rotazione (il costo si spalma), e subito alla prima vista.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

CLK = os.sysconf("SC_CLK_TCK")
PAG_KB = os.sysconf("SC_PAGE_SIZE") // 1024
SEGNI_BROWSER = ("remotix-ff-", "remotix-cr-")
XRDP_EXE = ("xrdp", "xrdp-sesman", "xrdp-sesexec", "xrdp-chansrv")
RECINTI = ("remotix", "sessioni", "browser")
EXTRA = ("altro_scatola", "labwc_cliente")


# ─────────────────────────────── fdinfo ────────────────────────────────────
def unita(v):
    """'123 KiB' → byte.  Senza unita' sono byte (lo standard)."""
    p = v.split()
    try:
        n = float(p[0])
    except (ValueError, IndexError):
        return None
    u = p[1] if len(p) > 1 else ""
    return n * {"": 1, "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3}.get(u, 1)


def leggi_fdinfo(testo):
    """Il blocco `drm-*` di un fdinfo, in un dizionario semplice:
    {driver, pdev, client, motori{nome:ns}, capacita{nome:n}, cicli{nome:c},
     cicli_tot{nome:c}, memoria{regione:byte}}   — None se non e' DRM."""
    d = {"motori": {}, "capacita": {}, "cicli": {}, "cicli_tot": {}, "memoria": {},
         "driver": None, "pdev": None, "client": None}
    visto = False
    for riga in testo.splitlines():
        if not riga.startswith("drm-"):
            continue
        k, _, v = riga.partition(":")
        v = v.strip()
        visto = True
        if k == "drm-driver":
            d["driver"] = v
        elif k == "drm-pdev":
            d["pdev"] = v
        elif k == "drm-client-id":
            d["client"] = v
        elif k.startswith("drm-engine-capacity-"):
            try:
                d["capacita"][k[len("drm-engine-capacity-"):]] = int(v)
            except ValueError:
                pass
        elif k.startswith("drm-engine-"):
            try:
                d["motori"][k[len("drm-engine-"):]] = int(v.split()[0])
            except (ValueError, IndexError):
                pass
        elif k.startswith("drm-total-cycles-"):
            try:
                d["cicli_tot"][k[len("drm-total-cycles-"):]] = int(v.split()[0])
            except (ValueError, IndexError):
                pass
        elif k.startswith("drm-cycles-"):
            try:
                d["cicli"][k[len("drm-cycles-"):]] = int(v.split()[0])
            except (ValueError, IndexError):
                pass
        elif k.startswith("drm-resident-") or k.startswith("drm-memory-"):
            # ⚠ `resident` e non `total`: `total` conta anche quel che e' solo
            #   prenotato.  `drm-memory-*` e' la forma vecchia (amdgpu).
            reg = k.split("-", 2)[2]
            b = unita(v)
            if b is not None:
                d["memoria"][reg] = d["memoria"].get(reg, 0) + b
    return d if visto and d["driver"] else None


def categoria(motore):
    m = motore.lower()
    if "enhance" in m or m.startswith("vecs"):
        return "video_enhance"
    if m in ("render", "gfx", "rcs") or m.startswith("rcs") or m.startswith("gfx"):
        return "disegno"
    if (m.startswith("video") or m.startswith("vcs") or m in ("enc", "dec", "jpeg")
            or m.startswith("vcn") or m.startswith("uvd") or m.startswith("vce")
            or m.startswith("enc") or m.startswith("dec")):
        return "video"
    if m in ("copy", "dma", "sdma") or m.startswith("bcs") or m.startswith("sdma"):
        return "copia"
    if m.startswith("compute") or m.startswith("ccs"):
        return "calcolo"
    return m


def uso_client(prima, ora, dt_ns):
    """Uso % per motore di UN client fra due letture.  Normalizzato sulla
    capacita' (i915 video: 2 motori ⇒ 100 % = tutti e due pieni)."""
    out = {}
    if prima is None or dt_ns <= 0:
        return out
    for m, ns in ora["motori"].items():
        p = prima["motori"].get(m)
        if p is None or ns < p:            # contatore nuovo o azzerato: niente
            continue
        cap = max(1, ora["capacita"].get(m, 1))
        out[m] = 100.0 * (ns - p) / dt_ns / cap
    for m, c in ora["cicli"].items():
        p, tp, t = prima["cicli"].get(m), prima["cicli_tot"].get(m), ora["cicli_tot"].get(m)
        if None in (p, tp, t) or t <= tp or c < p:
            continue
        cap = max(1, ora["capacita"].get(m, 1))
        out[m] = 100.0 * (c - p) / (t - tp) / cap
    return out


# ─────────────────────────────── /proc ─────────────────────────────────────
def leggi(p, dflt=None):
    try:
        with open(p, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return dflt


def stat_pid(proc, pid):
    s = leggi("%s/%d/stat" % (proc, pid))
    if not s:
        return None
    i = s.rfind(")")
    comm = s[s.find("(") + 1:i]
    r = s[i + 2:].split()
    try:
        return {"comm": comm, "ppid": int(r[1]), "cpu": int(r[11]) + int(r[12]),
                "thread": int(r[17]), "avvio": int(r[19]), "rss_kb": int(r[21]) * PAG_KB}
    except (IndexError, ValueError):
        return None


def pss_kb(proc, pid):
    s = leggi("%s/%d/smaps_rollup" % (proc, pid))
    if not s:
        return None
    m = re.search(r"^Pss:\s+(\d+)\s*kB", s, re.M)
    return int(m.group(1)) if m else None


class Campionatore:
    def __init__(self, scatola, proc="/proc", sys_="/sys", contenitore=None,
                 orologio=time.monotonic, segni_browser=SEGNI_BROWSER,
                 pss_ogni=5, scopri=True, sistema="remotix"):
        self.scatola = scatola
        self.sistema = sistema
        self.proc, self.sys = proc, sys_
        self.cgroot = sys_ + "/fs/cgroup"
        self.orologio = orologio
        self.segni = tuple(s for s in segni_browser if s)
        self.pss_ogni = max(1, int(pss_ogni))
        self.cont = contenitore or (self.scopri_contenitore() if scopri else None)
        self.giro = 0
        self.t_prima = None
        self.cpu_prima = {}            # (pid, avvio) → tick
        self.cpu_mac_prima = None
        self.cg_prima = None
        self.pss = {}                  # (pid, avvio) → kB
        self.info = {}                 # (pid, avvio) → {cg, cmd, exe, uid}
        self.drm_fd = {}               # (pid, avvio) → [fd, …]
        self.drm_eta = {}              # (pid, avvio) → giro dell'ultima scansione
        self.drm_prima = {}            # chiave client → lettura
        self.rapl_prima = {}
        self.passwd = {}
        self.passwd_giro = -99
        self.ncpu = os.cpu_count() or 1
        self.io_prima = None

    # ── la scatola ──
    def scopri_contenitore(self):
        nome = "rete11-" + self.scatola
        try:
            o = subprocess.run(["podman", "inspect", nome, "--format",
                                "{{.State.Pid}} {{.State.CgroupPath}} {{.Id}}"],
                               capture_output=True, text=True, timeout=20)
            pid, cg, ident = o.stdout.split()
            return {"nome": nome, "pid": int(pid), "cgroup": cg, "id": ident[:12]}
        except (OSError, ValueError, subprocess.SubprocessError):
            return None

    def nomi_scatola(self):
        if self.giro - self.passwd_giro < 10 and self.passwd:
            return self.passwd
        self.passwd_giro = self.giro
        s = leggi("%s/%d/root/etc/passwd" % (self.proc, self.cont["pid"])) if self.cont else None
        if s:
            self.passwd = {}
            for r in s.splitlines():
                p = r.split(":")
                if len(p) > 2 and p[2].isdigit():
                    self.passwd[int(p[2])] = p[0]
        return self.passwd

    # ── identita' di un processo (letta una volta, ricontrollata ogni 10 giri) ──
    def identita(self, pid, chiave):
        i = self.info.get(chiave)
        if i and self.giro - i["giro"] < 10:
            return i
        cg = (leggi("%s/%d/cgroup" % (self.proc, pid)) or "").strip()
        cg = cg.split("::", 1)[1] if "::" in cg else cg
        if i is None:
            cmd = (leggi("%s/%d/cmdline" % (self.proc, pid)) or "").replace("\0", " ")
            try:
                exe = os.path.basename(os.readlink("%s/%d/exe" % (self.proc, pid)))
            except OSError:
                exe = None
            i = {"cmd": cmd, "exe": exe}
        # ⛔ L'uid VERO da `status`, non il padrone di /proc/<pid>: `[M]` 25 set,
        #   il figlio di remotix e' non-«dumpable» e la sua cartella in /proc
        #   risulta di ROOT — finiva nel padre invece che nell'inquilino.  E si
        #   rilegge ogni 10 giri: il figlio nasce root e poi cede i privilegi.
        m = re.search(r"^Uid:\s+(\d+)", leggi("%s/%d/status" % (self.proc, pid)) or "", re.M)
        i["uid"] = int(m.group(1)) if m else i.get("uid", -1)
        i["cg"], i["giro"] = cg, self.giro
        self.info[chiave] = i
        return i

    def fd_drm(self, pid, chiave):
        if chiave in self.drm_fd and self.giro - self.drm_eta.get(chiave, -99) < 10:
            return self.drm_fd[chiave]
        fds = []
        base = "%s/%d/fd" % (self.proc, pid)
        try:
            for e in os.scandir(base):
                try:
                    if os.readlink(e.path).startswith("/dev/dri/"):
                        fds.append(e.name)
                except OSError:
                    pass
        except OSError:
            pass
        self.drm_fd[chiave], self.drm_eta[chiave] = fds, self.giro
        return fds

    # ── /sys ──
    def cg_scatola(self):
        if not self.cont:
            return None
        b = self.cgroot + self.cont["cgroup"]
        s = leggi(b + "/cpu.stat")
        if s is None:
            return None
        u = re.search(r"usage_usec (\d+)", s)
        m = leggi(b + "/memory.current")
        ms = leggi(b + "/memory.stat") or ""
        a = re.search(r"^anon (\d+)", ms, re.M)
        pc = leggi(b + "/pids.current")
        return {"usec": int(u.group(1)) if u else None,
                "mem": int(m) if m and m.strip().isdigit() else None,
                "anon": int(a.group(1)) if a else None,
                "pids": int(pc) if pc and pc.strip().isdigit() else None}

    def schede(self, dt):
        out = {}
        base = self.sys + "/class/drm"
        try:
            nomi = sorted(n for n in os.listdir(base) if re.match(r"^card\d+$", n))
        except OSError:
            nomi = []
        for n in nomi:
            d = base + "/" + n
            try:
                pdev = os.path.basename(os.path.realpath(d + "/device"))
                drv = os.path.basename(os.path.realpath(d + "/device/driver"))
            except OSError:
                continue
            s = {"scheda": n, "driver": drv}

            def num(p, fatt=1.0):
                v = leggi(p)
                try:
                    return round(float(v.strip()) * fatt, 1)
                except (AttributeError, ValueError):
                    return None
            if drv in ("i915", "xe"):
                s["freq_mhz"] = num(d + "/gt_cur_freq_mhz")
                s["freq_att_mhz"] = num(d + "/gt_act_freq_mhz")
                if s["freq_mhz"] is None:
                    s["freq_mhz"] = num(d + "/gt/gt0/rps_cur_freq_mhz")
                    s["freq_att_mhz"] = num(d + "/gt/gt0/rps_act_freq_mhz")
                ragioni = []
                for p in sorted(_glob(d + "/gt/gt0", "throttle_reason_")):
                    r = os.path.basename(p)[len("throttle_reason_"):]
                    if r != "status" and (leggi(p) or "0").strip() not in ("0", ""):
                        ragioni.append(r)
                s["strozzatura"] = ragioni
                t, fonte = self.temp_cpu()
                s["temp_c"], s["temp_fonte"] = t, fonte
            elif drv == "amdgpu":
                s["occupata_pct"] = num(d + "/device/gpu_busy_percent")
                s["vram_usata_mb"] = num(d + "/device/mem_info_vram_used", 1 / 2 ** 20)
                s["vram_totale_mb"] = num(d + "/device/mem_info_vram_total", 1 / 2 ** 20)
                for h in _glob(d + "/device/hwmon", "hwmon"):
                    s["temp_c"] = num(h + "/temp1_input", 0.001)
                    s["temp_giunzione_c"] = num(h + "/temp2_input", 0.001)
                    s["temp_fonte"] = "amdgpu hwmon (edge/junction)"
                    s["freq_mhz"] = num(h + "/freq1_input", 1e-6)
                    p = num(h + "/power1_average", 1e-6)
                    s["potenza_w"] = p if p is not None else num(h + "/power1_input", 1e-6)
                    break
                sc = leggi(d + "/device/pp_dpm_sclk") or ""
                m = re.search(r"(\d+)Mhz \*", sc)
                if m:
                    s["freq_att_mhz"] = float(m.group(1))
            out[pdev] = s
        # la potenza RAPL (Intel): package e uncore (= la grafica integrata)
        for p in _glob(self.sys + "/class/powercap", "intel-rapl:"):
            nome = (leggi(p + "/name") or "").strip()
            e = leggi(p + "/energy_uj")
            if not e or not nome:
                continue
            e = int(e)
            pr = self.rapl_prima.get(nome)
            self.rapl_prima[nome] = e
            if pr is not None and dt > 0 and e >= pr:
                w = round((e - pr) / 1e6 / dt, 2)
                for s in out.values():
                    if s["driver"] in ("i915", "xe"):
                        if nome == "uncore":
                            s["potenza_w"] = w
                        elif nome == "package-0":
                            s["potenza_pacchetto_w"] = w
        return out

    def temp_cpu(self):
        for h in _glob(self.sys + "/class/hwmon", "hwmon"):
            if (leggi(h + "/name") or "").strip() == "coretemp":
                v = leggi(h + "/temp1_input")
                try:
                    return round(int(v) / 1000, 1), "coretemp pacchetto CPU (la iGPU non ha sensore suo)"
                except (TypeError, ValueError):
                    pass
        return None, None

    # ── un campione ──
    def campione(self):
        t0cpu = time.process_time()
        t0 = self.orologio()
        dt = (t0 - self.t_prima) if self.t_prima is not None else None
        self.giro += 1
        avvisi = []
        if self.cont is None:
            avvisi.append("⛔ scatola rete11-%s NON trovata (podman inspect): recinti remotix e "
                          "sessioni non misurabili" % self.scatola)
        pref = self.cont["cgroup"] if self.cont else None
        nomi = self.nomi_scatola() if self.cont else {}

        # 1. tutti i processi
        procs = {}
        for n in os.listdir(self.proc):
            if not n.isdigit():
                continue
            pid = int(n)
            s = stat_pid(self.proc, pid)
            if s:
                procs[pid] = s
        # 2. i browser: radici col segno e i loro discendenti
        figli = {}
        for pid, s in procs.items():
            figli.setdefault(s["ppid"], []).append(pid)
        rec = {}
        radici_browser = {}
        for pid, s in procs.items():
            ch = (pid, s["avvio"])
            i = self.identita(pid, ch)
            s["i"] = i
            s["ch"] = ch
            dentro = bool(pref) and (i["cg"] == pref or i["cg"].startswith(pref + "/"))
            s["dentro"] = dentro
            if dentro and self.sistema == "xrdp":
                if (i["exe"] in XRDP_EXE or (i["exe"] is None and s["comm"] in XRDP_EXE)
                        or "/xrdp.service" in i["cg"] or "/xrdp-sesman.service" in i["cg"]):
                    rec[pid] = "remotix"
                elif i["uid"] >= 1000 and i["uid"] != 65534:
                    rec[pid] = "sessioni"
                else:
                    rec[pid] = "altro_scatola"
            elif dentro:
                if (i["cg"].endswith("/rete11-server.service")
                        or "/rete11-server.service/" in i["cg"]
                        or i["exe"] == "remotix" or (i["exe"] is None and s["comm"] == "remotix")):
                    rec[pid] = "remotix"
                elif i["uid"] >= 1000 and i["uid"] != 65534:
                    rec[pid] = "sessioni"
                else:
                    rec[pid] = "altro_scatola"
            elif self.segni and any(g in i["cmd"] for g in self.segni):
                radici_browser[pid] = "chrome" if "remotix-cr-" in i["cmd"] else (
                    "firefox" if "remotix-ff-" in i["cmd"] else (
                        "freerdp" if "remotix-rdp-" in i["cmd"] else "browser"))
        # i discendenti (un livello alla volta: la radice vince sul figlio col segno)
        radice_di = {}
        pila = [(r, r) for r in radici_browser
                if procs[r]["ppid"] not in radici_browser and not _antenato_in(procs, r, radici_browser)]
        while pila:
            pid, r = pila.pop()
            if pid in radice_di:
                continue
            radice_di[pid] = r
            rec[pid] = "browser"
            for c in figli.get(pid, []):
                if not procs[c]["dentro"]:
                    pila.append((c, r))
        for pid, s in procs.items():
            if pid not in rec and not s["dentro"] and s["comm"] in ("labwc", "Xvfb") \
                    and s["i"]["uid"] >= 1000:
                rec[pid] = "labwc_cliente"

        # 3. CPU, memoria, fd grafici per processo
        tot = {k: _vuoto() for k in RECINTI + EXTRA}
        per_in = {"remotix": {}, "sessioni": {}}
        per_br = {}
        padre = _vuoto()
        nuovi_cpu = {}
        for pid, s in procs.items():
            ch = s["ch"]
            nuovi_cpu[ch] = s["cpu"]
            r = rec.get(pid)
            if r is None:
                continue
            d_cpu = 0.0
            if dt and ch in self.cpu_prima:
                d_cpu = max(0, s["cpu"] - self.cpu_prima[ch]) / CLK / dt
            if ch not in self.pss or (pid + self.giro) % self.pss_ogni == 0:
                v = pss_kb(self.proc, pid)
                if v is not None:
                    self.pss[ch] = v
            pss = self.pss.get(ch)
            s["d_cpu"] = d_cpu
            voce = [tot[r]]
            if r in ("remotix", "sessioni"):
                u = s["i"]["uid"]
                nome = nomi.get(u, "uid%d" % u)
                if r == "remotix" and u < 1000:
                    voce.append(padre)
                else:
                    voce.append(per_in[r].setdefault(nome, _vuoto(uid=u)))
                s["inquilino"] = nome if (u >= 1000 and u != 65534) else None
            elif r == "browser":
                rd = radice_di[pid]
                voce.append(per_br.setdefault(rd, _vuoto(pid=rd, tipo=radici_browser[rd],
                                                         profilo=_profilo(procs[rd]["i"]["cmd"]))))
            for v in voce:
                v["cpu_core"] += d_cpu
                v["processi"] += 1
                v["thread"] += s["thread"]
                v["rss_mb"] += s["rss_kb"] / 1024
                if pss is None:
                    v["pss_mancanti"] += 1
                else:
                    v["pss_mb"] += pss / 1024
        self.cpu_prima = nuovi_cpu
        vivi = set(nuovi_cpu)
        for dct in (self.pss, self.info, self.drm_fd, self.drm_eta):
            for k in [k for k in dct if k not in vivi]:
                del dct[k]

        # 4. la scheda grafica, per client (deduplicato) e per processo
        dt_ns = dt * 1e9 if dt else 0
        visti = {}
        proc_gpu = {}
        for pid in sorted(procs):
            s = procs[pid]
            if not (s["dentro"] or pid in rec):
                continue
            for fd in self.fd_drm(pid, s["ch"]):
                txt = leggi("%s/%d/fdinfo/%s" % (self.proc, pid, fd))
                d = leggi_fdinfo(txt or "")
                if not d:
                    continue
                k = (d["pdev"], d["client"]) if d["client"] else (pid, s["avvio"], fd)
                if k in visti:
                    continue                  # lo stesso client: una volta sola
                visti[k] = (pid, d)
        schede_gpu = {}
        nuovi_drm = {}
        for k, (pid, d) in visti.items():
            nuovi_drm[k] = d
            uso = uso_client(self.drm_prima.get(k), d, dt_ns)
            s = procs[pid]
            r = rec.get(pid, "altro_scatola" if s["dentro"] else None)
            sch = schede_gpu.setdefault(d["pdev"], {"motori": {}, "memoria_mb": {}, "client": 0})
            sch["client"] += 1
            for m, p in uso.items():
                sch["motori"][m] = sch["motori"].get(m, 0) + p
            for reg, b in d["memoria"].items():
                sch["memoria_mb"][reg] = sch["memoria_mb"].get(reg, 0) + b / 2 ** 20
            mem_mb = sum(d["memoria"].values()) / 2 ** 20
            if r:
                dest = [tot[r]]
                if r in ("remotix", "sessioni"):
                    u = s["i"]["uid"]
                    nome = nomi.get(u, "uid%d" % u)
                    dest.append(padre if (r == "remotix" and u < 1000)
                                else per_in[r].setdefault(nome, _vuoto(uid=u)))
                elif r == "browser":
                    dest.append(per_br[radice_di[pid]])
                for v in dest:
                    for m, p in uso.items():
                        c = categoria(m)
                        v["gpu"][c] = v["gpu"].get(c, 0) + p
                    v["gpu_mem_mb"] += mem_mb
            if any(p >= 0.05 for p in uso.values()):
                pg = proc_gpu.setdefault((pid, d["pdev"]), {
                    "pid": pid, "comm": s["comm"], "recinto": r,
                    "inquilino": s.get("inquilino"), "pdev": d["pdev"], "motori": {}})
                for m, p in uso.items():
                    pg["motori"][m] = pg["motori"].get(m, 0) + p
        proc_gpu = [dict(v, motori={m: round(p, 2) for m, p in v["motori"].items() if p >= 0.05})
                    for _, v in sorted(proc_gpu.items())]
        self.drm_prima = nuovi_drm

        # 5. macchina, scatola, schede
        st = (leggi(self.proc + "/stat") or "cpu 0 0 0 0").splitlines()[0].split()[1:]
        st = [int(x) for x in st[:8]]
        occ, tut = sum(st) - st[3] - st[4], sum(st)
        mac = {"cpu_core": None, "cpu_pct": None}
        if self.cpu_mac_prima and tut > self.cpu_mac_prima[1]:
            f = (occ - self.cpu_mac_prima[0]) / (tut - self.cpu_mac_prima[1])
            mac["cpu_pct"] = round(100 * f, 1)
            mac["cpu_core"] = round(f * self.ncpu, 2)
        self.cpu_mac_prima = (occ, tut)
        la = (leggi(self.proc + "/loadavg") or "0 0 0 0/0 0").split()
        mac["carico"] = [float(x) for x in la[:3]]
        mac["processi"] = len(procs)
        mac["thread"] = sum(s["thread"] for s in procs.values())
        mi = leggi(self.proc + "/meminfo") or ""
        mt = re.search(r"MemTotal:\s+(\d+)", mi)
        ma = re.search(r"MemAvailable:\s+(\d+)", mi)
        if mt and ma:
            mac["mem_totale_mb"] = round(int(mt.group(1)) / 1024)
            mac["mem_disponibile_mb"] = round(int(ma.group(1)) / 1024)
            mac["mem_usata_mb"] = mac["mem_totale_mb"] - mac["mem_disponibile_mb"]
        cg = self.cg_scatola()
        scat = None
        if cg:
            scat = {"mem_mb": round(cg["mem"] / 2 ** 20, 1) if cg["mem"] is not None else None,
                    "anon_mb": round(cg["anon"] / 2 ** 20, 1) if cg["anon"] is not None else None,
                    "pids": cg["pids"], "cpu_core": None}
            if dt and self.cg_prima and cg["usec"] is not None and self.cg_prima["usec"] is not None:
                scat["cpu_core"] = round(max(0, cg["usec"] - self.cg_prima["usec"]) / 1e6 / dt, 3)
        self.cg_prima = cg
        # la CPU esatta delle sessioni: il cgroup meno i processi lunghi degli altri
        if scat and scat["cpu_core"] is not None:
            ses = scat["cpu_core"] - tot["remotix"]["cpu_core"] - tot["altro_scatola"]["cpu_core"]
            attr = tot["sessioni"]["cpu_core"]
            tot["sessioni"]["cpu_core_processi"] = attr
            tot["sessioni"]["cpu_core"] = max(ses, attr)
            tot["sessioni"]["cpu_non_attribuita"] = max(0.0, ses - attr)
        g = self.schede(dt or 0)
        for pdev, sch in schede_gpu.items():
            s = g.setdefault(pdev, {"scheda": None, "driver": None})
            s["motori"] = {m: round(p, 2) for m, p in sorted(sch["motori"].items())}
            cats = {}
            for m, p in sch["motori"].items():
                c = categoria(m)
                cats[c] = cats.get(c, 0) + p
            s["categorie"] = {c: round(p, 2) for c, p in sorted(cats.items())}
            s["memoria_client_mb"] = {r: round(v, 1) for r, v in sch["memoria_mb"].items()}
            s["client"] = sch["client"]

        # 6. i recinti vuoti si DICONO (un recinto vuoto non e' un recinto sano)
        for r in RECINTI:
            if tot[r]["processi"] == 0:
                avvisi.append("⚠ recinto %s VUOTO: nessun processo trovato" % r)
        if self.sistema != "xrdp" and self.cont and tot["remotix"]["processi"] and not padre["processi"]:
            avvisi.append("⚠ remotix: nessun processo nel cgroup rete11-server.service (il padre?)")
        if self.sistema == "xrdp":
            pids_rx = sorted(p for p, r in rec.items() if r == "remotix" and procs[p]["comm"] == "xrdp"
                             and procs.get(procs[p]["ppid"], {}).get("comm") != "xrdp")
        else:
            pids_rx = sorted(p for p, r in rec.items() if r == "remotix"
                             and "rete11-server.service" in procs[p]["i"]["cg"]
                             and rec.get(procs[p]["ppid"]) != "remotix")
        if any(v["pss_mancanti"] for v in tot.values()):
            avvisi.append("⚠ PSS illeggibile per %d processi (non si e' root?)"
                          % sum(v["pss_mancanti"] for v in tot.values()))

        rec_out = {}
        for r in RECINTI + EXTRA:
            rec_out[r] = _pulisci(tot[r])
        rec_out["remotix"]["padre"] = _pulisci(padre)
        for r in ("remotix", "sessioni"):
            rec_out[r]["per_inquilino"] = {n: _pulisci(v) for n, v in sorted(per_in[r].items())}
        rec_out["browser"]["per_browser"] = [_pulisci(v) for _, v in sorted(per_br.items())]

        self.t_prima = t0
        riga = {"tipo": "campione", "t": round(time.time(), 3),
                "ora": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "dt_s": round(dt, 3) if dt else None, "scatola": self.scatola,
                "macchina": mac, "scatola_cg": scat, "recinti": rec_out, "gpu": g,
                "processi_gpu": proc_gpu, "remotix_pid": pids_rx[0] if pids_rx else None,
                "avvisi": avvisi,
                "misuratore": {"ms": round((self.orologio() - t0) * 1000, 1),
                               "cpu_s": round(time.process_time() - t0cpu, 4)}}
        return riga

    def intestazione(self):
        ci = leggi(self.proc + "/cpuinfo") or ""
        m = re.search(r"model name\s*:\s*(.+)", ci)
        return {"tipo": "intestazione", "t": round(time.time(), 3),
                "ora": time.strftime("%Y-%m-%dT%H:%M:%S"), "scatola": self.scatola,
                "contenitore": self.cont, "cpu": m.group(1).strip() if m else None,
                "ncpu": self.ncpu, "nucleo": os.uname().release,
                "schede": {p: {"scheda": s["scheda"], "driver": s["driver"]}
                           for p, s in self.schede(0).items()},
                "segni_browser": list(self.segni), "pss_ogni_s": self.pss_ogni,
                "euid": os.geteuid()}


def _antenato_in(procs, pid, insieme):
    seen = set()
    p = procs[pid]["ppid"]
    while p in procs and p not in seen and p > 1:
        if p in insieme:
            return True
        seen.add(p)
        p = procs[p]["ppid"]
    return False


def _profilo(cmd):
    m = re.search(r"(/[^ ]*remotix-(?:ff|cr)-[^ /]*)", cmd)
    return m.group(1) if m else None


def _glob(d, prefisso):
    try:
        return [d + "/" + n for n in sorted(os.listdir(d)) if n.startswith(prefisso)]
    except OSError:
        return []


def _vuoto(**extra):
    v = {"cpu_core": 0.0, "processi": 0, "thread": 0, "rss_mb": 0.0, "pss_mb": 0.0,
         "pss_mancanti": 0, "gpu": {}, "gpu_mem_mb": 0.0}
    v.update(extra)
    return v


def _pulisci(v):
    o = dict(v)
    for k in ("cpu_core", "cpu_core_processi", "cpu_non_attribuita"):
        if k in o and o[k] is not None:
            o[k] = round(o[k], 3)
    for k in ("rss_mb", "pss_mb", "gpu_mem_mb"):
        o[k] = round(o[k], 1)
    o["gpu"] = {c: round(p, 2) for c, p in sorted(o["gpu"].items())}
    if not o.get("pss_mancanti"):
        o.pop("pss_mancanti", None)
    return o


# ─────────────────────────────── giro ──────────────────────────────────────
def gira(o):
    os.makedirs(o.dir, exist_ok=True)
    c = Campionatore(o.scatola, segni_browser=o.segni_browser.split(","), pss_ogni=o.pss_ogni,
                     sistema=o.sistema)
    fermo = {"si": False}

    def ferma(*_):
        fermo["si"] = True
    signal.signal(signal.SIGTERM, ferma)
    signal.signal(signal.SIGINT, ferma)
    out = open(os.path.join(o.dir, "risorse.jsonl"), "a", encoding="utf-8")
    out.write(json.dumps(c.intestazione(), ensure_ascii=False) + "\n")
    out.flush()
    fine = time.monotonic() + o.durata if o.durata else None
    prossimo = time.monotonic()
    c.campione()                       # il primo serve solo da «prima»
    while not fermo["si"]:
        prossimo += o.intervallo
        time.sleep(max(0.0, prossimo - time.monotonic()))
        if fermo["si"]:
            break
        r = c.campione()
        out.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        out.flush()
        if fine and time.monotonic() >= fine:
            break
        if time.monotonic() - prossimo > 5 * o.intervallo:
            prossimo = time.monotonic()     # siamo rimasti indietro: non si rincorre
    out.close()
    return 0


# ─────────────────────────────── certifica ─────────────────────────────────
FDI_I915 = """pos:\t0
flags:\t02100002
drm-driver:\ti915
drm-client-id:\t{cid}
drm-pdev:\t0000:00:02.0
drm-total-system0:\t{mem} KiB
drm-resident-system0:\t{mem} KiB
drm-engine-render:\t{r} ns
drm-engine-copy:\t0 ns
drm-engine-video:\t{v} ns
drm-engine-capacity-video:\t2
drm-engine-video-enhance:\t0 ns
"""
FDI_AMD = """drm-driver:\tamdgpu
drm-client-id:\t{cid}
drm-pdev:\t0000:03:00.0
drm-memory-vram:\t{vram} KiB
drm-memory-gtt:\t0 KiB
drm-engine-gfx:\t{g} ns
drm-engine-enc:\t{e} ns
drm-engine-dec:\t0 ns
"""
FDI_XE = """drm-driver:\txe
drm-client-id:\t{cid}
drm-pdev:\t0000:00:02.0
drm-cycles-rcs:\t{c}
drm-total-cycles-rcs:\t{t}
"""


class Finto:
    """Un /proc e un /sys finti in una cartella: si scrivono i processi, si
    fanno due campioni con un orologio finto, e si guarda il numero."""

    def __init__(self):
        self.d = tempfile.mkdtemp(prefix="16-risorse-cert-")
        self.proc = self.d + "/proc"
        self.sys = self.d + "/sys"
        self.t = 1000.0
        os.makedirs(self.proc)
        os.makedirs(self.sys + "/fs/cgroup/machine.slice/libpod-x.scope")
        os.makedirs(self.sys + "/class/drm")
        self.stat_macchina(0, 0)
        with open(self.proc + "/loadavg", "w") as f:
            f.write("1.00 0.50 0.25 2/300 999\n")
        with open(self.proc + "/meminfo", "w") as f:
            f.write("MemTotal: 32000000 kB\nMemAvailable: 16000000 kB\n")
        self.cg(0)

    def cg(self, usec):
        b = self.sys + "/fs/cgroup/machine.slice/libpod-x.scope"
        with open(b + "/cpu.stat", "w") as f:
            f.write("usage_usec %d\n" % usec)
        with open(b + "/memory.current", "w") as f:
            f.write("1048576000\n")

    def stat_macchina(self, occ, idle):
        with open(self.proc + "/stat", "w") as f:
            f.write("cpu %d 0 0 %d 0 0 0 0 0 0\n" % (occ, idle))

    def processo(self, pid, comm, uid, cg, ppid=1, cpu=0, cmd="", exe=None, pss=1024,
                 fdinfo=None):
        p = "%s/%d" % (self.proc, pid)
        os.makedirs(p + "/fd", exist_ok=True)
        os.makedirs(p + "/fdinfo", exist_ok=True)
        with open(p + "/stat", "w") as f:
            f.write("%d (%s) S %d 0 0 0 0 0 0 0 0 0 %d 0 0 0 20 0 3 0 777 0 2560 0 0\n"
                    % (pid, comm, ppid, cpu))
        with open(p + "/cgroup", "w") as f:
            f.write("0::%s\n" % cg)
        with open(p + "/status", "w") as f:
            f.write("Name:\t%s\nUid:\t%d\t%d\t%d\t%d\n" % (comm, uid, uid, uid, uid))
        with open(p + "/cmdline", "w") as f:
            f.write(cmd.replace(" ", "\0"))
        with open(p + "/smaps_rollup", "w") as f:
            f.write("Rss: 9999 kB\nPss: %d kB\n" % pss)
        if exe and not os.path.lexists(p + "/exe"):
            os.symlink("/opt/remotix/" + exe, p + "/exe")
        # ⚠ il padrone della cartella resta il NOSTRO (come un processo non
        #   «dumpable», che in /proc risulta di root): l'uid si legge da status.
        for fd, txt in (fdinfo or {}).items():
            if not os.path.lexists(p + "/fd/" + fd):
                os.symlink("/dev/dri/renderD128", p + "/fd/" + fd)
            with open(p + "/fdinfo/" + fd, "w") as f:
                f.write(txt)

    def togli(self, pid):
        shutil.rmtree("%s/%d" % (self.proc, pid), ignore_errors=True)

    def orologio(self):
        return self.t


def certifica():
    esiti = []

    def guarda(nome, ok, dettaglio):
        esiti.append(ok)
        print("  %s %s — %s" % ("PASS" if ok else "FAIL", nome, dettaglio))

    CGC = "/machine.slice/libpod-x.scope"
    SRV = CGC + "/container/system.slice/rete11-server.service"
    SES = CGC + "/container/user.slice/user-4013.slice/session-c5.scope"
    OSP = "/user.slice/user-1000.slice/session-1.scope"

    def nuovo():
        return Finto()

    def campionatore(F, **kw):
        c = Campionatore("kde", proc=F.proc, sys_=F.sys, orologio=F.orologio,
                         contenitore={"nome": "rete11-kde", "pid": 1, "cgroup": CGC, "id": "x"},
                         **kw)
        c._ripristina = lambda: None
        return c

    print("16-risorse --certifica  (/proc e /sys finti, orologio finto)")
    # ── 1. i915: render 250 ms su 1 s ⇒ 25 %; video 1 s su due motori ⇒ 50 % ──
    F = nuovo()
    F.stat_macchina(0, 0)
    F.processo(10, "remotix", 0, SRV, cmd="/opt/remotix/remotix --porta 8512", exe="remotix")
    F.processo(20, "remotix", 4013, SES, ppid=10, exe="remotix",
               fdinfo={"7": FDI_I915.format(cid=5, mem=2048, r=0, v=0)})
    F.processo(21, "kwin_wayland", 4013, SES, exe="kwin_wayland",
               fdinfo={"9": FDI_I915.format(cid=6, mem=1024, r=0, v=0)})
    F.processo(30, "firefox", 1000, OSP, cmd="firefox --profile /tmp/remotix-ff-abc", exe="firefox")
    F.processo(31, "Web Content", 1000, OSP, ppid=30, cmd="firefox -contentproc 7", exe="firefox")
    F.processo(40, "firefox", 1000, OSP, cmd="firefox --profile /home/nicfio/.mozilla/x", exe="firefox")
    c = campionatore(F)
    c.campione()
    F.t += 1.0
    F.stat_macchina(1000, 1000)
    F.cg(2_000_000)
    F.processo(10, "remotix", 0, SRV, cpu=50, exe="remotix")
    F.processo(20, "remotix", 4013, SES, ppid=10, cpu=100, exe="remotix",
               fdinfo={"7": FDI_I915.format(cid=5, mem=2048, r=0, v=1_000_000_000)})
    F.processo(21, "kwin_wayland", 4013, SES, cpu=20, exe="kwin_wayland",
               fdinfo={"9": FDI_I915.format(cid=6, mem=1024, r=250_000_000, v=0)})
    r = c.campione()
    c._ripristina()
    rx, se, br = r["recinti"]["remotix"], r["recinti"]["sessioni"], r["recinti"]["browser"]
    guarda("fdinfo i915, video su 2 motori", abs(rx["gpu"].get("video", -1) - 50.0) < 0.01,
           "remotix video %s %% (atteso 50: 1 s occupato su 1 s, capacita' 2)" % rx["gpu"].get("video"))
    guarda("fdinfo i915, disegno", abs(se["gpu"].get("disegno", -1) - 25.0) < 0.01,
           "sessioni disegno %s %% (atteso 25)" % se["gpu"].get("disegno"))
    guarda("memoria grafica per client", abs(rx["gpu_mem_mb"] - 2.0) < 0.01,
           "remotix %s MB (atteso 2: 2048 KiB residenti)" % rx["gpu_mem_mb"])
    guarda("i tre recinti", (rx["processi"], se["processi"], br["processi"]) == (2, 1, 2),
           "remotix %d (padre + figlio) · sessioni %d · browser %d (il Firefox dell'utente "
           "SENZA segno resta fuori)" % (rx["processi"], se["processi"], br["processi"]))
    guarda("per inquilino", "uid4013" in rx["per_inquilino"] and "uid4013" in se["per_inquilino"],
           "figlio di remotix e sessione attribuiti all'inquilino 4013")
    guarda("CPU per processo", abs(rx["cpu_core"] - 150 / CLK) < 1e-3,
           "remotix %.3f core (attesi %.3f: 150 tick in 1 s)" % (rx["cpu_core"], 150 / CLK))
    guarda("CPU delle sessioni dal cgroup (processi brevi)",
           abs(se["cpu_core"] - (2.0 - 150 / CLK)) < 1e-3
           and abs(se["cpu_non_attribuita"] - (2.0 - 170 / CLK)) < 1e-3,
           "sessioni %.3f core = scatola 2,000 − remotix; non attribuita %.3f (quel che il "
           "cgroup ha visto e nessun processo vivo si porta: i processi brevi)"
           % (se["cpu_core"], se["cpu_non_attribuita"]))
    guarda("macchina", r["macchina"]["cpu_pct"] == 50.0, "cpu %s %% (atteso 50)" % r["macchina"]["cpu_pct"])
    guarda("PSS", abs(se["pss_mb"] - 1.0) < 0.01, "sessioni %s MB (atteso 1)" % se["pss_mb"])
    guarda("nessun avviso quando i recinti sono pieni", not r["avvisi"], str(r["avvisi"]))
    guarda("il pid del padre remotix", r["remotix_pid"] == 10, "remotix_pid %s (atteso 10)" % r["remotix_pid"])
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 2. GUASTO: lo stesso client su due fd e due processi ⇒ una volta sola ──
    F = nuovo()
    txt0 = FDI_I915.format(cid=9, mem=0, r=0, v=0)
    txt1 = FDI_I915.format(cid=9, mem=0, r=500_000_000, v=0)
    F.processo(10, "remotix", 0, SRV, exe="remotix")
    F.processo(20, "labwc", 4013, SES, fdinfo={"5": txt0, "6": txt0})
    F.processo(21, "figlio", 4013, SES, ppid=20, fdinfo={"5": txt0})
    F.processo(30, "chrome", 1000, OSP, cmd="chrome --user-data-dir=/tmp/remotix-cr-1")
    c = campionatore(F)
    c.campione()
    F.t += 1.0
    F.processo(20, "labwc", 4013, SES, fdinfo={"5": txt1, "6": txt1})
    F.processo(21, "figlio", 4013, SES, ppid=20, fdinfo={"5": txt1})
    r = c.campione()
    c._ripristina()
    v = r["recinti"]["sessioni"]["gpu"].get("disegno")
    guarda("client duplicato contato UNA volta", v is not None and abs(v - 50.0) < 0.01,
           "disegno %s %% (atteso 50; contato tre volte darebbe 150)" % v)
    guarda("browser Chrome riconosciuto dal profilo",
           r["recinti"]["browser"]["per_browser"][:1] and
           r["recinti"]["browser"]["per_browser"][0]["tipo"] == "chrome", "")
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 3. amdgpu e xe: nomi delle chiavi diversi, stesse categorie ──
    F = nuovo()
    F.processo(10, "remotix", 0, SRV, exe="remotix",
               fdinfo={"7": FDI_AMD.format(cid=1, vram=4096, g=0, e=0),
                       "8": FDI_XE.format(cid=2, c=0, t=1000)})
    F.processo(20, "kwin", 4013, SES)
    F.processo(30, "firefox", 1000, OSP, cmd="firefox --profile /tmp/remotix-ff-z")
    c = campionatore(F)
    c.campione()
    F.t += 2.0
    F.processo(10, "remotix", 0, SRV, exe="remotix",
               fdinfo={"7": FDI_AMD.format(cid=1, vram=4096, g=500_000_000, e=1_000_000_000),
                       "8": FDI_XE.format(cid=2, c=300, t=2000)})
    r = c.campione()
    c._ripristina()
    g = r["recinti"]["remotix"]["gpu"]
    guarda("amdgpu gfx/enc + xe cicli",
           abs(g.get("disegno", -1) - (25.0 + 30.0)) < 0.01 and abs(g.get("video", -1) - 50.0) < 0.01,
           "disegno %s %% (attesi 25 gfx + 30 xe rcs) · video %s %% (atteso 50 enc)"
           % (g.get("disegno"), g.get("video")))
    guarda("VRAM amdgpu (drm-memory-vram)", abs(r["recinti"]["remotix"]["gpu_mem_mb"] - 4.0) < 0.01,
           "%s MB (attesi 4)" % r["recinti"]["remotix"]["gpu_mem_mb"])
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 4. GUASTO: un contatore che non avanza ⇒ 0 %, mai l'ultimo valore ──
    F = nuovo()
    t = FDI_I915.format(cid=3, mem=0, r=7_000_000_000, v=0)
    F.processo(10, "remotix", 0, SRV, exe="remotix", fdinfo={"7": t})
    F.processo(20, "kwin", 4013, SES)
    F.processo(30, "firefox", 1000, OSP, cmd="firefox --profile /tmp/remotix-ff-z")
    c = campionatore(F)
    c.campione()
    F.t += 1.0
    r = c.campione()
    c._ripristina()
    guarda("motore fermo ⇒ 0 %", r["recinti"]["remotix"]["gpu"].get("disegno") == 0.0,
           "disegno %s %%" % r["recinti"]["remotix"]["gpu"].get("disegno"))
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 5. GUASTO: il pid riusato (stesso numero, altro avvio) non da' salti ──
    F = nuovo()
    F.processo(10, "remotix", 0, SRV, exe="remotix", cpu=100000)
    F.processo(20, "kwin", 4013, SES)
    F.processo(30, "firefox", 1000, OSP, cmd="firefox --profile /tmp/remotix-ff-z")
    c = campionatore(F)
    c.campione()
    F.t += 1.0
    F.togli(10)
    F.processo(10, "remotix", 0, SRV, exe="remotix", cpu=100500)
    with open(F.proc + "/10/stat") as f:
        s = f.read().replace(" 777 ", " 888 ")
    with open(F.proc + "/10/stat", "w") as f:
        f.write(s)
    r = c.campione()
    c._ripristina()
    guarda("pid riusato: niente CPU negativa o gigante", r["recinti"]["remotix"]["cpu_core"] == 0.0,
           "remotix %s core (il processo nuovo parte da zero; confuso col vecchio darebbe 5)" % r["recinti"]["remotix"]["cpu_core"])
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 6. GUASTO: i recinti vuoti si SEGNALANO ──
    F = nuovo()
    F.processo(20, "kwin", 4013, SES)
    c = campionatore(F)
    c.campione()
    F.t += 1.0
    r = c.campione()
    c._ripristina()
    a = " | ".join(r["avvisi"])
    guarda("recinto remotix vuoto segnalato", "recinto remotix VUOTO" in a, a)
    guarda("recinto browser vuoto segnalato", "recinto browser VUOTO" in a, "")
    guarda("recinto sessioni pieno NON segnalato", "sessioni VUOTO" not in a, "")
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 7. GUASTO: la scatola che non c'e' ──
    c = Campionatore("nessuna", proc=F.proc if os.path.isdir(F.proc) else "/proc",
                     contenitore=None, scopri=False)
    r = c.campione()
    guarda("scatola assente segnalata", any("NON trovata" in x for x in r["avvisi"]),
           r["avvisi"][0] if r["avvisi"] else "")

    n = len(esiti)
    ok = sum(esiti)
    print("CERTIFICA %s — %d su %d" % ("PASS" if ok == n else "FAIL", ok, n))
    return 0 if ok == n else 1


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=("gnome", "kde", "xfce", "lxqt", "gnome-xrdp", "kde-xrdp",
                                         "xfce-xrdp", "lxqt-xrdp"))
    a.add_argument("--sistema", choices=("remotix", "xrdp"), default="remotix",
                   help="xrdp: il recinto «remotix» e' xrdp (fasi/20 §7.4)")
    a.add_argument("--dir")
    a.add_argument("--intervallo", type=float, default=1.0)
    a.add_argument("--durata", type=float, default=0)
    a.add_argument("--pss-ogni", type=int, default=5)
    a.add_argument("--segni-browser", default=",".join(SEGNI_BROWSER))
    a.add_argument("--certifica", action="store_true")
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.scatola or not o.dir:
        a.error("servono --scatola e --dir (o --certifica)")
    if os.geteuid() != 0:
        print("⚠ 16-risorse non gira da root: PSS e fdinfo degli altri utenti saranno "
              "illeggibili (e lo dira' in `avvisi`)", file=sys.stderr)
    return gira(o)


if __name__ == "__main__":
    sys.exit(main())
