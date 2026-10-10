# Phase 20 — Performance, from the start

*Plan written on **5 Oct 2026**, while the NVIDIA bench was running. ⛔ **To be approved by the user before
any measure** (`fasi/19-nvidia.md` §6: *«la campagna di prestazioni si rifà da zero, una volta, a
architettura finita, con un piano approvato prima dall'utente»*). It starts **after** the NVIDIA: if the NVIDIA
finds a defect in the Vulkan route, the cure touches the Radeon too, and the measures taken before would have to be
thrown away.*

---

## 1. The question, and the two new things

The question stays that of phase 16: **how much load does REMOTIX bear while continuing to work?** The measures
of phase 16 were removed from the documents (DECISIONI §10.26: *«con questo cambio architetturale i numeri
sono completamente invalidati»*): since then REMOTIX no longer uses ffmpeg (phase 18), encodes only on the card and
on the Radeon goes through Vulkan (phase 19).

Two new things compared with phase 16:

1. **The result becomes the public table** (DECISIONI §10.30, *«la capacità si dichiara, non si
   limita»*): for every machine measured, a row **«uso ottimale fino a X utenti, degrado da Y»**. «Ottimale»
   = the last GREEN level of §5; «degrado» = the first DEGRADED.
2. **Two routes, two curves**: Intel = **VA-API**, Radeon = **Vulkan** (the user's answer, 4 Oct: *«sono due
   strade del prodotto, ognuna coi suoi numeri»*).

## 2. What is reused as it is (approved on 25 Sep, phase 16)

The method of phase 16 is taken up again **without changing it**, because it was already approved and because this way the new
numbers can be compared with the old ones where needed:

| piece | phase 16 | here |
|---|---|---|
| the setup | real browsers on the server, one `labwc` per user, input from the browser | the same (§4 of 16) |
| the four jobs | A browsing · B file manager · C terminal · D 4K video, in rotation | the same (§5 of 16) |
| the climb | steps **1 → 4 → 8 → 12 → 16**, 10 min per step, 30 min at the last, search halfway | the same (§6 of 16) |
| the check | delay, frames, stalls, video, audio, birth, short functional check, memory | the same (§7 of 16) |
| the scale | 4K → 3K → 2K → Full HD if 4K goes FAIL | the same (§8 of 16) |
| **the thresholds** | GREEN / DEGRADED / FAIL | ⛔ **the same, and they are not touched** (§9 of 16) |
| log and report | `banchi/16-stress/registro.jsonl`, generated report | the same, new campaigns `f20-*` |

## 3. The steps

0. **The server rebooted and redone clean** (Claude's answer to the user, 5 Oct: the reboot is worth it
   here, not before). Root in RAM redone with the recipe (`provisiona.sh`, key, packages, the 4 boxes),
   then we **look** that it is empty: no processes, tenants, compositors left over.
   ⭐ **7 Oct, the user's decision** (*«cerchiamo di accelerare i tempi»*): **no reboot** — we look
   that the server is empty (processes, tenants, compositors) and start as soon as the binary is decided, without
   waiting for the end of the NVIDIA rental (the declared risk: a cure born there in the last hours
   would force redoing the climbs already done).
   ⭐ **7 Oct 08:19, STARTED**: `sudo systemd-run --unit=r20-campagna … 16-campagna.sh intel-f20 amd-f20`
   (queue per card: 4K → 3K → 2K → Full HD on GNOME, KDE, XFCE, LXQt; video D = the local 4K file, 30 fps).
   Binary `e2b1afae` = commit **`716e35b`** (read from the climb: «commit del prodotto: 716e35b»), page
   `ae66b9b4`. Before: home net 732 + 733 PASS, 0 FAIL; and the A/B test of F-030 Firefox (first frame
   black) — old `5c186779` 4 out of 12, new 3 out of 12 ⇒ it does not come from the night's cures, ⏳ it stays open.
   Server looked at, empty (no tenant, no round, no browser). To stop it: `touch
   /media/REMOTIX/misure/fase16/FERMA` (between one climb and the next) or `sudo systemctl stop r20-campagna`.
   ⛔ **8 Oct 10:20 UTC, the server stuck** (rebooted by the user): Intel **finished** (16 climbs, 04:37),
   Radeon finished GNOME (4 measures) and KDE 4K; it hung in `amd-f20-3k-kde`, repetition of level 12,
   after a «dead actor» at 10:09 and level 12 FAIL (5 GREEN · 1 DEGRADED · 7 FAIL). The journal was
   in RAM ⇒ the cause is not demonstrated; the picture is that of 28 Sep (fasi/16 §17.3: RAM exhausted with 13
   sessions and 13 client browsers on the same machine). ⇒ It is a limit **of the bench** (the client browsers
   sit on the server), to be declared as such, not of the product. The interrupted climb stays in
   `amd-f20-3k-kde-interrotta`. Root redone with the recipe (packages, earlyoom, storage.conf, linger,
   `provisiona.sh` of `716e35b` + `/etc/ld.so.conf.d/remotix-prodotto.conf` → `rete11/prodotto/lib`:
   check OK; swap `/media/swapfile` 32 GB reactivated at 10:50, the reboot had removed it), and **resumed at 10:42** with the same binary: unit `r20-ripresa`
   (`misure/fase16/ripresa-8ott.sh`: Radeon KDE 3K → 2K → Full HD, then XFCE and LXQt from 4K). To stop it:
   `FERMA` as above or `sudo systemctl stop r20-ripresa`.
1. **The commit of the day**, identified, with the **short regression suite** of phase 15 on the 4 desktops
   with the two browsers. Not green ⇒ no measuring.
2. **The setup put back on its feet on today's product**: the `16-*` benches are from before phases 18 and 19
   (page with WebGL2, no ffmpeg, Vulkan route). Every meter with its own test, as back then: a
   meter that has never given red does not measure.
3. **A short trial climb** (4 users, 5 min per level) to calibrate: it does not count.
   **6 Oct, first trial** (Radeon, GNOME, 4K, binary `5c186779`, benches `d9c86d6`): two defects of the bench,
   none of the product, and both corrected in `16-salita.py`:
   - *3-min levels* = 1 of settling + 2 of short check ⇒ the memory stretch was **empty**,
     «NON MISURATO» ⇒ DEGRADED at the first step, climb stopped at 0. Now the trial lasts 4 min, and the climb
     **refuses** levels shorter than check + 2 min.
   - *second trial, 4-min levels*: the memory series has 60 points in 59 s, and `16-classifica` wants
     more than 60 s ⇒ still NON MISURATO. The trial moves to **5 min** (2 min of memory).
   - the input → frame delay at 4K on GNOME/Radeon, 1 user: **53–55 ms** (green threshold 50). It is not a
     worsening: in phase 16 it was 55–59 (`amd-4k-gnome`, `amd-b-4k-gnome`). It is the reason why the
     scale goes down; the third trial is done at 2K, where one user sits around 23 ms and the steps can climb.
   - **third trial, 2K, 5 min** (`prova-f20-prova-amd-gnome-2k`): 1, 2, 4 users **all GREEN**, the memory
     measured (remotix 95 → 96 MB, sessions 2303 → 2301 MB in 119 s). The climb goes from start to end.
   - **the other three trials at 2K** (6 Oct, 16:50–17:45), one per desktop, both routes covered:
     KDE/Intel and XFCE/Intel 1-2 GREEN, 4 DEGRADED not significant; LXQt/Radeon 1 GREEN, 2 DEGRADED
     significant then GREEN at the repetition, 4 GREEN. All the DEGRADED are an **image stall of
     1.03–1.16 s** (threshold 1 s) in a single actor: a real measure, to be looked at in the campaign, not a defect of the
     bench. ⇒ **the setup is calibrated on 4 desktops × 2 cards**; only the final binary remains.
   - *«commit del prodotto: ?»*: the climb looked for it only in `src/16-prodotto` (stuck at 26 Sep). Now it also reads
     `rete11/prodotto/VERSIONE` = `<commit> <md5 a 8>`, valid only if the md5 is the binary's.
     ⇒ **fixed step of the campaign**: with the final binary compiled, it is copied into `rete11/prodotto` and
     `VERSIONE` is written alongside.
4. **The campaigns, one configuration at a time** (performance is not measured in parallel):
   Intel = VA-API on GNOME, KDE, XFCE, LXQt; then Radeon = Vulkan, same order.
4b. ⭐ **The comparison with xrdp, on the same machine** (decided by the user on 8 Oct: *«sono curioso di vedere
   come siamo messi e soprattutto avere dei dati oggettivi di confronto»*). ⛔ Today «siamo avanti a xrdp» is
   a judgement (fasi/08 §2.5, 22 Aug, one user, by eye), not a measure, and on the web there is no load bench
   for xrdp. **A single climb**, not the matrix (~3 days, discarded for cost): **XFCE, 2K, Intel** —
   XFCE is native on X11, that is at xrdp's home, and does not penalise it; 2K is the format we declare; we there
   do **10** (`intel-f20-2k-xfce`). Same scene, same steps, same thresholds; the clients are
   **FreeRDP** (the browser does not speak RDP) ⇒ CPU, RAM, card and drops are compared one to one; delay and
   frames are read in another way and must be declared as such. Cost: ~½ day to adapt the
   bench + ~2 hours of climb. It starts **after** the campaign, with `r20-ripresa` finished. One row comes out: «a 2K su
   XFCE, stessa macchina: REMOTIX 10, xrdp N». If it is close, the user decides whether to widen.
   ⭐ **8 Oct evening, the user's choice: the complete version** (§7, ~2 days + ~3 hours of machine), not
   the reduced one (breaking point, CPU and RAM only): *«pensavo ad una suite completa anche per xrdp, avremmo un
   confronto pieno»*. ⚠ «Pieno» has a construction limit: skipped frames, holes and audio **do not exist** on the
   xrdp side (§7.3), and no extra work makes them appear. ⛔ **The user's constraint**: *«che la suite di test
   non blocchi il lavoro sul sistema di licensing»* (DECISIONI §10.30) ⇒ the **licence comes first**; the xrdp
   bench is written alongside, without taking hours from the licence, and takes the server only when the licence does not
   use it. The two things do not touch: the comparison uses the measures **already taken** of `716e35b`, so a new
   binary with the licence does not oblige redoing anything.
5. **The report** and **the public table** (§5).

**How long it lasts**, from phase 16: ~1 hour 10 per climb ⇒ ~9 hours of machine in the best case (8 climbs),
~35 if it goes down the whole scale. In blocks, at night too, and ⛔ **never while the user uses the server**.

### 3-bis. After the campaign: the two oddities (9 Oct 2026)

**1. Radeon 4K, GNOME and KDE «0 users»: it is the driver, and the cure exists.** `[M]` In the logs of `amd-f20-4k-gnome` the
Radeon uses the **Vulkan** route with **RADV 25.0.7** (Debian 13), and REMOTIX asks for `ULTRA_LOW_LATENCY`
(`src/vulkanvideo.c:629`). The project `~/Documenti/AMD` (§5-ter) measured that RADV 25.0.7 accepts it but does not
translate it to the firmware; from Mesa **25.1** it does. With one user the level was DEGRADED for the delay alone (51-56 ms,
threshold 50), everything else green: the A3 anomaly (groups of 5 frames of 31 ms).
Climbs repeated with **`mesa-vulkan-drivers 26.1.6-1~bpo13+1`** (the **official Debian 13 backport**) installed
in the box before the server (`16-salita.py --mesa-vulkan-deb`, `misure/fase16/mesa26-9ott.sh`, campaigns
`amd-m26-4k-*`, binary `716e35b` unchanged):

| Radeon GNOME 4K, 1 user | RADV 25.0.7 (`amd-f20`) | **RADV 26.1.6** (`amd-m26`) | Intel, for comparison |
|---|---|---|---|
| class | DEGRADED (twice) | **GREEN** | GREEN |
| delay p95 | 53.95 / 55.72 ms | **21.45 ms** | 35.18 ms |
| OUR p95 of the p95s | 45.0 / 46.7 ms | **12.4 ms** | 26.2 ms |

**The 4 climbs at 4K, finished on 9 Oct at 11:13** (last good level, RADV 25.0.7 → 26.1.6): GNOME **0 → 4**,
KDE 0 → 0 (old snapshot of 1.6-2.2 s with one user, cap 1 s), XFCE **2 → 0** and LXQt **3 → 0** (input lost:
2 keys out of 11 and 1 out of 13 with one user, delay good at 33 ms; confirmed by the repetition).
⇒ ⛔ **Closed here, by the user's decision (9 Oct): Mesa 26 is not in the perimeter**, it was only the verification of the cause.
The cause of A3 on GNOME is the driver, not REMOTIX. The keys lost on XFCE and LXQt appear **only** with Mesa 26, so
they too come from the driver. The product stays on Debian 13's RADV 25.0.7 and the public table reports the
`amd-f20` measures.

**2. «Buono 12, verde vero 1» (e.g. Intel XFCE Full HD): it is not a contradiction.** «Good» admits a non-significant
DEGRADED (at most one actor out of four); «true green» wants them all green. At 4, 8 and 12 users there was **a
single actor** DEGRADED, always for the **image stall** of 1.06-1.11 s (threshold 1 s). `[M]` In the case
`intel-f20-fhd-xfce/livello-04` (user 1, profile A, who types text) the **server answers every key in 23-40 ms**
(log: `input id=1524…1545` → `fotogramma SPEDITO`), no frame skipped, no input lost. `[?]` The
«still» second is born **before** the server or in the comparison between the time of the keys reconstructed by the actor
(`ore_dei_tasti`, from the return of the Marionette chain) and the time of the page's paints: **to be verified** before
calling it a defect, with the actor writing every impulse and the paint that attributes it.

⭐ **10 Oct 2026, morning — verified on the files, without touching the server** `[M]`: in `intel-f20-fhd-xfce` the stalls above
threshold are 7 (levels 4, 8, 12: user 1 profile A, users 7 and 3 profile C), all 1.05-1.13 s, all **Firefox**,
with 0 frames skipped and 0 errors. In the **same rows** of `stato.jsonl` (5 s) the **page round trip** (key →
frame, measured by the page) has its maximum at **24.7-47.5 ms**, and the terminal echo at 24-25 ms. ⇒ The screen
answered: the «still» second **does not belong to the REMOTIX server**. It sits between Marionette and Firefox: either the time of the keys reconstructed
by `ore_dei_tasti` (which assumes the chain executed without stops), or Firefox itself stalled on the loaded machine (the
actors run on the server). The 0.7-1.5 s stalls on Firefox appear **on all desktops** (from 0 to 15 per climb,
levels 1-8); Chrome, which types the keys one by one via CDP with the true time, never has them outside the video.
⇒ ⚠ **In the comparison with xrdp it weighs against REMOTIX**: xrdp's actor types with XTEST, true time, and does not have
this error. REMOTIX's «true green» cells cut **only** by a Firefox stall: Intel XFCE Full HD (1, good 12),
GNOME 3K (1, good 4), XFCE 3K (4, good 8). ⏳ Proposed cure: the key's time is written by the **page** (the
`keydown` event), not reconstructed by the actor; and the climbs already done are reclassified from the files, without redoing them.
✅ **Cured on 10 Oct 2026** (commit «🧪 fase 20 §3-bis.2», `banchi/16-stress/16-attore.py`): the probe that
the actor injects into the page (not the product: `src/pagina.html` does not change) notes in capture on `window` the time
of every `keydown`, `pointerdown` and `wheel`, in the same clock as the paints; `allinea_impulsi` puts every
impulse back at that time (Marionette or CDP estimate only if the page did not see the gesture: then it stays a real
stall). Every row of `stato.jsonl` carries `impulsi_pagina: [dalla pagina, totali]`. ⭐ The cause, seen in the tests:
a held-back chain shifts FORWARD the keys typed before the stop, beyond their echo, and the wait becomes
that of the next paint — the blinking cursor, ~1.1 s. ⏳ **Reclassification to be done with the xrdp campaign
finished**, on the server, for every climb `intel-f20-*` and `amd-f20-*`:
`cd /media/REMOTIX/src/controllo/banchi/16-stress && for s in /media/REMOTIX/misure/fase16/{intel,amd}-f20-*/; do python3 16-riclassifica.py --salita "$s"; done`
(it writes alongside `riclassificata.json` and `livello-NN/classifica-riclassificata.log`; it exits 2 if a level with no rows
touched changes class, that is if the redone judgement is not the climb's).
✅ **Done on the evening of 10 Oct on shadow copies** (the measures stay read-only): 32 climbs, all exited 0, only
the three cells foreseen above change. The result is in §8.1.

## 4. The limit of 16, declared

The product today has **16 sessions fixed in the program** (`MAX_ATTACCATE` in `src/rcp.c`, DECISIONI §1.11).
This campaign measures up to 16, like phase 16. **Beyond 16** is measured only after the work «limite deciso
all'avvio» (DECISIONI §10.30), and on a machine bigger than ours: today it cannot be done.

## 5. What comes out

- **The matrix** of phase 16: desktop × card, with last GREEN level, breaking point, step of the
  scale.
- **The public table**, one row per card (and per desktop, if they differ). ✅ It sits in the **technical
  documentation** (the sizing guide), **not on the home page** of the site (the user, 9 Oct: *«nella homepage del prodotto
  di certo le prestazioni non vengono riportate»*); the home page refers to it with a link:

  | machine | card and route | screen size | optimal up to | degraded from |
  |---|---|---|---|---|
  | i5-13500T, 31 GB | Intel UHD 770 · VA-API | 4K | … | … |
  | i5-13500T, 31 GB | AMD RX 6800 · Vulkan | 4K | … | … |

  ✅ **Filled in in §8.5** (10 Oct), with 31 GB.

  ⚠ **The RAM is 31 GB, not 64** (read with `free` on the server, 7 Oct during the campaign): the table must be
  corrected before publishing it.
  ⚠ **Intel: 256 MB of video memory in the BIOS** (noted by the user, 7 Oct). On Linux it is needed only at boot;
  afterwards, the card takes memory from the common RAM when needed (shared memory seen at 16 GB during the
  climbs). ⇒ it is not the 4K limit: there delay and frames give way (copy and compression speed), not the
  memory. To be tested separately, with the campaign finished: Intel 4K on one desktop, 256 MB against the BIOS maximum.
  ⚠ With the declaration of phase 16, which stays true: the server **also runs the N browsers**, so the
  numbers are a **lower bound**; the network is not measured.
- ⛔ The numbers are **not** written in the SPECIFICHE as promises: they stay project goals
  (DECISIONI §10.26).

## 6. Questions for the user, before starting (one at a time)

1. **The perimeter**: 4 desktops × 2 cards (~9–35 hours), or first one desktop per card (~2–9 hours) and the
   others later?
2. **The video of the D jobs**: YouTube 4K as back then, or straight away the local 4K file (it does not change underfoot, and
   makes the climbs repeatable)?
3. **The scale**: do we go down to Full HD as back then, or stop at 2K?

**The user's answers (6 Oct 2026):**
- 1 ✅ **4 desktops × 2 cards = 8 climbs: Intel and Radeon** of the home server (confirmed by the user).
- 3 ✅ **we go down to Full HD**.
- 2 ✅ **the video: the local 4K file** (a free film from the Blender Foundation, CC-BY), chosen for
  repeatability across the 8 climbs. ⚠ The network is NOT a reason: the server has a 10/2 Gb/s line (said
  by the user).

## 7. The xrdp bench: the plan

### 7.0 ⭐ 9 Oct 2026, afternoon: the user's decisions, and what is already measured

**The four decisions** (the licence is suspended, so the xrdp bench has the green light, on the server too):
1. *«i test su xrdp devono rispecchiare quelli su remotix: 4 DE, Intel e Radeon»* ⇒ **the whole matrix**:
   8 climbs, 4K → Full HD, like `intel-f20` and `amd-f20`. Point 4b of §3 (a single XFCE 2K climb) is superseded.
2. *«fai in modo che la suite lavori in modo autonomo sul server»* ⇒ the same structure as REMOTIX:
   `16-campagna.sh` → `16-coda.sh` → `16-salita.py --sistema xrdp`, in a systemd unit, with `FERMA` and resumption.
3. *«e soprattutto evita che il server si blocchi»* ⇒ §7.7.
4. *«mi aspetto che l'intera suite duri meno dei 3 giorni di remotix»* ⇒ REMOTIX's two campaigns occupied the
   machine for ~50 hours (Intel ~22, Radeon ~28). With the same protocol the duration depends on where xrdp gives way:
   estimate **1½-2½ days**. ⛔ No cap that truncates the climbs, because it would break comparability. The queue
   writes at every climb the **estimate** of the hours left, so an overrun is seen at once.

**The first piece of §7.6 is done and measured** `[M]` (9 Oct, 16:00-16:10):
- **a single recipe**, `banchi/11-scatole/Contenitore.xrdp` (`ARG DESKTOP`), built **on top of** the measures'
  image (`rete11/<desktop>:p0`); `11-accendi.sh costruisci|accendi <desktop>-xrdp`. Plus xrdp
  0.10.1-3.1+deb13u2, xorgxrdp 1:0.10.2-1 and pipewire-module-xrdp 0.2-2. To stay on X11, every desktop gets its own
  piece of Debian: GNOME `gnome-session-xsession` (Mutter 48), KDE `kwin-x11` (Plasma 6.3.6), XFCE `xfwm4` and
  `xfce4-settings`, LXQt `openbox`;
- **the 8 combinations are born up to the desktop** with `xfreerdp3 /gfx` in a 2560×1440 Xvfb on the host, and the 8 snapshots
  have been looked at. The Xorg log says `rdpPreInit: /dev/dri/renderD128` with `name [amdgpu]` on the Radeon, so
  the session draws on the right card. ⇒ Risk 3 of §7.6: **closed**;
- **the keyboard arrives** from the RDP channel (`xdotool type` in the terminal, seen in the snapshot);
- **the XDamage probe sees FreeRDP's drawings**: 63 events in 5 s while writing, 1 at rest (the clock).
  ⚠ Two conditions, discovered by getting it wrong: `d.damage_query_version()` before anything (without it, **zero** events and
  no error), and the damage must be asked on **FreeRDP's window**, not on the root (the root does not receive the
  children's drawings). ⇒ Risk 2: **closed**;
- ⛔ **port 3389 is a single one for the whole host** (`--network=host`). In the first round an xrdp box left
  on answered in place of the other three, and the snapshots looked right but were all XFCE's. ⇒ Before
  starting, the climb turns off **every** `rete11-*-xrdp` and wants 3389 free; the birth snapshot is compared
  with the expected desktop.
- on the host: `freerdp3-x11` 3.15.0+dfsg-2.1+deb13u3, `xvfb` 2:21.1.16-1.3+deb13u4, `xdotool`, `python3-xlib`
  0.33-3, `x11-apps`. ⚠ The root is in RAM: after a reboot they must be reinstalled (the climb checks it).

### 7.7 ⛔ The server must not lock up

A locked-up server means a reboot, and the reboot loses the ssh key and the provisioning: the campaign stays stopped
until the user steps in. With xrdp the risk rises, because the FreeRDP clients decode **on the host's
processor**: at 4K, 16 users mean 16 RemoteFX decodings plus 16 Xorg. ⇒ Four nets, from the outermost:
1. **the memory guard** in the climb: every 2 s it reads `MemAvailable` and `/proc/pressure/memory`. Below
   **3 GiB** free, or with `full avg10` above **20 %**, the level is closed at once as a **«host
   resources» break** (declared in the classification, not mixed with the thresholds of §9) and cleared out. ⚠ REMOTIX's
   `716e35b` did not have this guard: in the table it is declared, and we look in the campaign's `risorse.jsonl`
   of REMOTIX whether it would ever have triggered;
2. **who dies first:** the clients (Xvfb and FreeRDP) are born with `OOMScoreAdjust=+800`, so if the kernel has to
   kill something it kills a client (a red step), not `sshd` nor the queue;
3. **who never dies:** `sshd` and the queue's unit get `OOMScoreAdjust=-900` with a drop-in in `/run`
   (it disappears at reboot like everything else, and the campaign puts it back);
4. **the queue does not stop for a killed process:** `OOMPolicy=continue`, as in `16-coda.sh`.
⇒ The limit of how many clients the host bears stays that of §7.6 risk 1, and the `browser` enclosure shows it.

### 7.8 The bench is written and tested; the campaign has NOT started (9 Oct, evening)

**What there is** (commit `31d5b50` and following, in `banchi/16-stress/`):
- `16-attore-rdp.py`: the same rate and the same four jobs as `16-attore.py`. FreeRDP `/gfx` full
  screen in an Xvfb, the hands with XTEST, the snapshot from the Xvfb, the XDamage probe on FreeRDP's window
  (bursts at 5 ms). With `--controllo` it does the reduced short check of §7.3 (login, screen, keyboard), with
  one tenant per level (`c16<9NN>u99`), and if the birth fails it saves `~/.xsession-errors` and the
  Xorg log;
- `16-compositori-rdp.sh` (one Xvfb per user, with `oom_score_adj` 800);
- `--sistema xrdp` in `16-salita.py` (the box, 3389, xrdp on, xrdp's logs, the versions of the
  packages, `dpkg --verify` to prove that the configuration is the package's, the guard of §7.7,
  sshd at −900), in `16-risorse.py` (the enclosures of §7.4) and in `16-classifica.py` (the entries of §7.3; log
  `registro-xrdp.jsonl`);
- in `16-coda.sh` and `16-campagna.sh`: `REMOTIX_16_SISTEMA=xrdp` and the estimate of the hours written in `campagna.log`
  after every climb.
All the certifications pass: attore-rdp, classification 38 out of 38 (4 new for xrdp), resources 21 out of 21.

**Measured** `[M]`, XFCE 2K Intel trial (`prova-x20-xfce-2k`, steps 1, 2, 4 of 5 minutes):
- levels 1, 2 and 3: **GREEN**. Impulse → drawing delay, p95 from the watcher's side: 17-41 ms; birth
  2.6-2.7 s; video D 24.8 paints/s (0.83·f). The four snapshots of level 4 were looked at and are right:
  A browses, B Thunar, C terminal, D the film full screen;
- level 4: **FAIL, twice out of two**, and each time for the same entry, that is the short check: the fifth
  session is not born.

**⛔ The discovery: with one session watching the video, xrdp no longer lets anyone in.** `[M]` Reproduced
**without the bench**, with only `xfreerdp3` and Firefox by hand:

| sessions already open | is the 4K film running in one? | the next session | card |
|---|---|---|---|
| 6 in a row, all idle | no | all 6 are born | Intel |
| 1 | yes | it is born | Intel and Radeon |
| 4 | yes | **the 5th and the 6th die at once** | Intel and Radeon |

Each time the **new session's Xorg crashes** in xorgxrdp (`rdpCapture`, `(EE) Backtrace` in
`~/.xorgxrdp.NN.log`), `startxfce4` exits with 1, and FreeRDP receives `ERRINFO_LOGOFF_BY_USER`. It does not depend on the
tenant's name, the bench or the graphics card.
⇒ In the climb profile D enters fourth. From there on no new user is born, and **every xrdp climb would
stop at 3 users**, on all desktops and at all sizes, because of a crash and not because of resources. The campaign
(32 climbs, ~1 day) would produce mainly this number, repeated 32 times.

**The decision is the user's**, before starting:
1. **measure it like this**: it is xrdp as Debian 13 installs it, and it is a true result (to a customer with 4 colleagues,
   one of whom watches a video, xrdp refuses access). The campaign will say 3 everywhere, plus CPU, RAM and
   delay up to 3;
2. **look at the crash first** (~½ day): if it comes from glamor (xorgxrdp draws on the card) it is enough to try
   without it, but it is a change to xrdp's `xorg.conf`, that is **outside** the «configurazione del pacchetto» rule
   of §7.5, and would have to be declared;
3. **change the order of the users** only for xrdp (D enters last). ⛔ I do not advise it: the scene would no longer
   be the same, and the crash would arrive anyway at the next level.

⭐ **The user's choice (9 Oct, evening): number 1.** *«se xrdp ha dei difetti meglio: vuol dire che il nostro prodotto
e' migliore»*. ⇒ **Campaign started on 9 Oct at 17:47** (unit `r20-xrdp`, `16-campagna.sh intel-x20 amd-x20`,
`REMOTIX_16_SISTEMA=xrdp`), with the package's configuration (`dpkg --verify` clean).
⏳ **After the campaign, one hour: the crash outside the box.** xrdp installed on the host, 4 sessions with one
watching the film, then the 5th. The measures hold in any case; the check decides how the crash is told. If
it appears outside the box too, «xrdp non fa entrare il quinto» is written. If it does not appear, it is declared as a
limit of the container test and we go back to the user.
✅ **Closed from the files (§8.3)**: the crash is a `Bus error` in `rdpCapture` when the box's `/dev/shm` (64 MiB,
podman's default) is full. Outside the box `/dev/shm` is half the RAM: it is declared as a limit of the container
test, next to every xrdp capacity number.

*Written on the evening of **8 Oct 2026**, on the laptop, reading the bench `banchi/16-stress/`; the server was
not touched (`r20-ripresa` is running). It serves point 4b of §3. ⛔ No code before the campaign
is finished and this plan has been read.*

⚠ **The estimate of §3 point 4b was too low.** «Half a day to adapt the bench» does not hold: today's
actor talks to the **page** (Marionette/CDP, the paint probe, the diary), and for FreeRDP that
part must be redone. Honest estimate in §7.6: **~2 days of work + ~3 hours of machine**.

### 7.9 ⚠ First reading of the xrdp campaign, Intel (10 Oct 2026, morning, with the campaign in progress) `[M]`

Read from the files, without touching the server. Two things change what can be said.

1. **Most of xrdp's breaks are the check's LOGIN, not the experience of whoever works.** At 4K,
   on all four desktops, level 1 is FAIL **only** because the check session (user 99, a
   second FreeRDP connection) exits during login with `ERRINFO_LOGOFF_BY_USER`; the user working is
   **GREEN**. The same reason closes almost all levels 2 and 4 at 3K and 2K, and 7-8 in Full HD XFCE/GNOME.
   ⛔ ⇒ «A 4K xrdp non regge nemmeno una persona» **cannot be written**: one person works well, it is the
   **second one that cannot get in**. ❓ Whether it is a true limit of xrdp (a second login that fails, which for
   a customer is a true defect) or a defect of the bench (the check user, sesman, the resolution) is **to be
   reproduced by hand** with the campaign finished: one xrdp session at 4K open, then a second login.
   ✅ **Explained from the files on the evening of 10 Oct (§8.3)**: it is the box's 64 MiB `/dev/shm`, which xorgxrdp fills
   with W×H×4 bytes per session; the extra session dies with `Bus error`. It is not reproduced by hand (the user's
   decision: climbs are not redone).
   Breaks of another nature, which look real: KDE loses input (2-3 actions out of 2-3 with no effect, 2K and Full HD) and
   GNOME Full HD at 4 users (stall 6.4 s, delay p95 3.98 s).
2. **With a single user the delay is even, xrdp a little ahead.** Key → image delay, p95, from the watcher's
   side (REMOTIX: the page round trip, last 200 samples of the session; xrdp: XDamage, §7.3):

   | Intel, 1 user | GNOME | KDE | XFCE | LXQt |
   |---|---|---|---|---|
   | 4K | 54 / 48 | 55 / 53 | 53 / 34 | 67 / 31 |
   | 3K | 48 / 39 | 48 / 44 | 45 / 34 | 60 / 40 |
   | 2K | 43 / 37 | 43 / 41 | 40 / 32 | 40 / 41 |
   | Full HD | 39 / 35 | 39 / 39 | 37 / 33 | 36 / 44 |

   (ms, REMOTIX / xrdp). ⚠ The page round trip includes decoding and drawing in the browser, XDamage on Xvfb does not
   (§7.3): part of the gap is the yardstick. ⇒ REMOTIX's measured advantage is **holding under load**, not
   the single user's response.
3. **Video and weight: here REMOTIX is ahead, and it matches the user's impression** (10 Oct: *«remotix mi
   sembra più reattivo, più leggero. Riprodurre un video ad alta risoluzione su xrdp è un'esperienza peggiore»*).
   At 4 users, the video user (4K film at 30 fps): REMOTIX **29.9-30.0 paints/s**, 0 skipped; xrdp
   **24.7-24.9** (2K and Full HD; class GREEN for both, threshold 0.8 of f) ⇒ xrdp loses ~1 frame in 6.
   The machine's processor, level 4: REMOTIX **10.7-12.5 %**, xrdp **12.4-30.0 %** (Full HD GNOME 11 against
   30, KDE 12 against 26, XFCE 11 against 18), and REMOTIX's number includes real browsers as clients, xrdp's
   lighter FreeRDP clients: the true gap is wider. REMOTIX moves the work onto the card (at 4
   users: drawing 19-62 %, video 11-24 %).

### 7.1 How a session is born today, and what changes

| today (REMOTIX) | xrdp | who does it |
|---|---|---|
| box `rete11-xfce` redone from zero (`11-accendi.sh`), inside `rete11-server` | **the same box** with in addition `xrdp` and `xorgxrdp` (derived image `rete11-xfce-xrdp`, built **once**), `rete11-server` **stopped**; `xrdp` and `xrdp-sesman` on with Debian's files **as they are** | `16-salita.py --sistema xrdp` |
| tenant `c16NNNuN` created by the actor (`suite.Sessione`), the box's PAM | **the same**: sesman goes through PAM (`/etc/pam.d/xrdp-sesman` → `common-auth`), the tenant is the same | reuse |
| one **labwc without a screen** per user (`16-compositori.sh`), with a browser inside | one **Xvfb** per user (`:2NN`, 2560×1440) with **`xfreerdp3`** inside, full screen: `/v:127.0.0.1 /u:… /p:… /cert:ignore /gfx /f /sound:sys:fake /wm-class:remotix-rdp-NN` | `16-compositori-rdp.sh` (new) |
| the input: Marionette/CDP on the page's canvas | **`xdotool`** on the Xvfb's display (mouse, keys, wheel): the input goes **through the RDP channel**, like the user's | new `Mani` |
| the snapshot: the page's canvas | the snapshot of the Xvfb (`xwd -root` → PIL), **1:1 with the desktop** (no snapshot → desktop conversion) | new `foto_pil` |
| the paints: the probe in the page (every 10 ms the time of every change) | **XDamage on the Xvfb** (`python3-xlib`): every time FreeRDP draws, the time. ⭐ It is the **same measure from the watcher's side** | new probe |

⭐ **Why xfreerdp in Xvfb and not sdl-freerdp in labwc.** With Xvfb the input is injected with `xdotool`,
which is proven; in labwc `wtype` and a virtual pointer would be needed, never tested in the bench. ⚠ **The
price, to be declared:** FreeRDP decodes RemoteFX **on the processor** and does not use the Intel card. Today the
browsers sit on the Intel together with the server; with xrdp they do not. On the card xrdp is **advantaged**, on the
processor **disadvantaged**.

**The new actor** is `16-attore-rdp.py`, not a change to `16-attore.py`. It reuses `Ritmo` (same seeds,
same choices in the same order) and **all four jobs of `16-lavori.py`**: they use only `dorme`,
`verifica`, `impulso`, `mani.*`, `foto_pil`, `s.nella_sessione`, `sc.dentro`, `chi`, `desktop`. Of these
three things change:
- `nella_sessione`: `DISPLAY=:N` of the tenant's Xorg (read from `ps -u <inquilino>`), `XAUTHORITY`,
  the session bus from `/proc/<xfce4-session>/environ`, without `MOZ_ENABLE_WAYLAND`;
- `Mani`: xdotool with the same pauses and the same typing as the `Ritmo`;
- the snapshot: from the Xvfb.

The state row is written **in the same schema** (`stato.jsonl`, `nascita.json`), so the classification reads it.

### 7.2 The work scene: the same

The four profiles A/B/C/D run **inside the XFCE session** as today. The files are prepared the same way
(`prepara`), the applications are the same (`firefox-esr --kiosk`, `thunar`, `xfce4-terminal`) and
the video is the same local 4K file (`/rete11/.c16-video/`). The checks look at **the disk** (the notebook,
the folder created, the bash history) and **do not know** whether REMOTIX or xrdp is in front.
⚠ The only difference is that XFCE runs **on X11**, because xrdp does not know Wayland. It is xrdp's natural environment
(§3 point 4b), and the session is chosen by a `~/.xsession` with `startxfce4` written by `prepara`.

### 7.3 The measures, one by one

| entry (§9, fixed thresholds) | xrdp | how |
|---|---|---|
| **input → frame delay** | ⚠ **in another way** | from the watcher's side: p95 per second between the **impulse** (key, click, notch) and the **first** XDamage **paint** after it. ⛔ The campaign's REMOTIX is judged from the **server side** («NOSTRO» + 9 ms). ⇒ In the comparison REMOTIX's **round trip** is put alongside (`stato.jsonl` → `giro`, the page's command → frame delay, **already recorded** in `intel-f20-2k-xfce`): client side against client side. ⚠ The page round trip includes decoding and drawing, XDamage on Xvfb does not: a slight advantage to xrdp, declared |
| **skipped frames** | ⛔ **not measured** | FreeRDP acknowledges every frame (FRAME_ACKNOWLEDGE): xrdp **does not send** those it cannot, it does not skip them. There is no «delivered against painted» to count |
| **longest image stall** | ✅ **the same** | same function (`attese_impulsi`, `pausa_piu_lunga`), but with the XDamage paints |
| **holes in the video chain** | ⛔ **not measured** | it is a counter of our page, it has no equivalent |
| **video: paints per second** | ⚠ **in another way** | the XDamage bursts per second in the video window (bursts separated by more than 5 ms). ⚠ xrdp has `rfx_frame_interval=32 ms` by default (≈31 per s): with the film at 30 fps **it does not penalise it** |
| **audible audio** | ⛔ **not measured** (but **on**) | `pipewire-module-xrdp` in the session and `/sound:sys:fake` in the client: the audio **travels**, so the load is even, but nobody plays it and so it is not counted |
| **birth** | ⚠ **in another way** | from the start of xfreerdp (with user and password: no login screen) to the **first paint with the XFCE panel**, that is a non-degenerate snapshot; same thresholds |
| **drop, restart, error** | ✅ **equivalent** | xfreerdp exits or writes `ERRCONNECT_*`; in `/var/log/xrdp.log` and `xrdp-sesman.log` «connection problem» or «session … terminated» appear |
| **short functional check** | ⚠ **reduced** | `16-controllo-corto.py` tests the page's F-0xx functions and here it does not apply. ⇒ A 17th FreeRDP session gets in, types a command, finds it in the history and exits: **login, keyboard, screen**, nothing else |
| **memory growth** | ✅ **the same** | from `risorse.jsonl` |
| **input arrives** (the jobs' checks) | ✅ **the same** | gesture → effect on the disk; ⭐ it is **the most comparable number** between the two |

### 7.4 Resources: the enclosures of `16-risorse.py`

| enclosure | REMOTIX | xrdp |
|---|---|---|
| `remotix` (the server) | `rete11-server` + the `remotix` children | `xrdp`, `xrdp-sesman`, `xrdp-sesexec`, `xrdp-chansrv`, by executable name, inside the box. ⭐ **Here** the RemoteFX compression is done, on the processor |
| `sessioni` | compositor and applications of the tenants | **the same**, and inside there is also the tenant's **`Xorg` + xorgxrdp**, which does the **capture** (`rdpCapture`, with glamor on the Intel) |
| `browser` (the watcher) | Firefox/Chrome with the mark `remotix-ff-`/`remotix-cr-` | `xfreerdp3` with the mark `remotix-rdp-` (already foreseen: `--segni-browser`) |
| `labwc_cliente` | the labwc without a screen | the clients' **Xvfb** (one more line in the recognition) |

⛔ The split between «server» and «sessions» is not the same in the two systems: with us the
`remotix` child copies, in xrdp `Xorg` copies. ⇒ The comparison is made on the **box totals** (CPU, RAM, card),
which the sampler already measures from the cgroup. The enclosures explain the totals, but they are not put side by
side.

### 7.5 The packages (Debian 13) and the configuration

| where | package | version | note |
|---|---|---|---|
| box | `xrdp` | 0.10.1-3.1+deb13u2 | ⭐ **compiled WITHOUT H.264**: no link to x264/OpenH264, no `gfx.toml` (read on the laptop, same Debian 13 version). It compresses with **RemoteFX** on the processor, and that is how it is measured: it is **xrdp as Debian 13 installs it** |
| box | `xorgxrdp` | 1:0.10.2-1 | with **glamor** and `DRMDevice /dev/dri/renderD128` by default ⇒ the session draws on the Intel, like ours |
| box | `pipewire-module-xrdp` | 0.2-2 | the session's audio |
| host | `freerdp3-x11` | 3.15.0+dfsg-2.1+deb13u3 | the client |
| host | `xvfb` · `xdotool` · `python3-xlib` · `x11-apps` | 2:21.1.16 · 1:3.20160805 · 0.33-3 · 7.7 | fake screen, input, XDamage (⚠ `Xlib.ext.damage` to be verified), `xwd` |

**Configuration:** Debian's **as it is**. The exceptions are three, all needed to make the test start and not to make it faster:
`startwm.sh` → `startxfce4` (through `~/.xsession`), port 3389 free on the host (⚠ **to be looked at** first, with
`--network=host`), and `rete11-server` stopped. ⛔ No retouching of `xrdp.ini` (frame intervals,
`max_bpp`): if we touch them, the comparison is not valid. An xrdp recompiled with x264 would be **another**
test, to be proposed to the user only if the result asks for it.

**`16-salita.py --sistema xrdp`**: the check of the empty server is the same, plus port 3389. The box
is redone from zero with the `-xrdp` image, without `prodotto` and without cap. In place of commit and binary,
`livello.json` gets the versions of the packages. `server.log` becomes the extract of `xrdp.log` and
`xrdp-sesman.log`, and the classification runs with `--sistema xrdp`. **Everything else does not change**: steps 1,4,8,12,16,
10 minutes (30 the last), repetition, search halfway, clean box between repetitions.

### 7.6 What it costs, and the risks

| piece | hours |
|---|---|
| image `rete11-xfce-xrdp`, xrdp on in the box, **one session by hand** up to the desktop | 2 |
| `16-attore-rdp.py` (Xvfb, xdotool, XDamage, snapshot, state schema) + certify without server | 6 |
| `16-compositori-rdp.sh`, `16-risorse.py` (mark and Xvfb), `16-classifica.py --sistema xrdp` | 3 |
| `16-salita.py --sistema xrdp` | 2 |
| tests on the server: 1, 2, 4 users of 5 minutes (as §3 point 3) | 3 |
| **work** | **~16 hours ≈ 2 days** |
| **the climb** (XFCE 2K Intel, up to ~11-12 users with the search halfway) | **~2½-3 hours of machine** |

**The risks:**
1. ⚠ **The clients might give way before the server.** 11-12 FreeRDP decoding RemoteFX at 2K, with the
   video, **on the processor of the same machine**. If it happens, the measure becomes a limit **of the bench**.
   The `browser` enclosure shows it, and it must be declared as it is, without passing it off as an xrdp number.
2. ✅ **The XDamage probe: tested on the evening of 8 Oct** on the laptop, in a Debian 13 container (`python3-xlib`
   0.33, Xvfb, `xclock -update 1`): the extension is there, the events arrive, **~1 burst per second** like
   the clock. ⚠ The call is `finestra.damage_create(livello)`, not `display.damage_create`. ⇒ The risk
   goes down; it remains to see it with FreeRDP really drawing. The earlier text, for the record: The fallback is FreeRDP's logs
   (`WLOG_LEVEL=DEBUG` on the rdpgfx channel), but it is likely that in Debian's build the frame
   messages are off. Without paints neither the delay nor the stall can be measured ⇒ it must be tested **first**.
3. ⚠ **xrdp inside the podman box** (systemd, PAM, `pam_systemd`, Xorg as a user, glamor on the
   Intel, Firefox with VA-API on X11) has never been tested. The session done by hand in the
   first piece decides it; if it does not hold we go back to the user **before** writing the rest.

⚠ **What the comparison will NOT say:** skipped frames, holes and audio. It will tell the delay **from the watcher's side for
both**, not with the REMOTIX table's number. ⭐ **What it will say well:** where each one breaks
(same thresholds for the measured entries), how much CPU, RAM and card each user costs, and whether the input arrives.

## 8. ⭐ The result: REMOTIX and xrdp compared (10 Oct 2026, campaigns closed) `[M]`

*Written on the evening of **10 Oct 2026**, from the files, without touching the server: the queues `coda-intel-f20.log`,
`coda-amd-f20.log` (REMOTIX, 7-9 Oct) and `coda-intel-x20.log`, `coda-amd-x20.log` (xrdp, 9 Oct 17:47 → 10 Oct
16:09 UTC), the logs `registro.jsonl` and `registro-xrdp.jsonl`, `16-rapporto.py --testo` on the four campaigns.
⛔ The user's decisions already taken, not put back into question: **climbs are not redone**; the verdict on video and
processor is solid; for xrdp's capacity the note of the «wall» of §8.3 is written alongside.*

**The iron, always:** a single machine, i5-13500T (14 cores, 20 threads), **31 GB**, Debian 13, kernel 7.0.
- **Intel UHD 770 integrated** (the processor's card, not a dedicated card) · REMOTIX with **VA-API**;
- **AMD Radeon RX 6800** · REMOTIX with **Vulkan**, Debian 13's RADV **25.0.7** (not Mesa 26: §3-bis.1).

**The two products:** REMOTIX commit **`716e35b`** (binary `e2b1afae`, page `ae66b9b4`), budget **off**
(`--budget-mpixel-s 0`) and cap at 17 to let the check of the 16th step in; clients Firefox 153.4 ESR and
Chrome 154. xrdp **0.10.1-3.1+deb13u2** with xorgxrdp 1:0.10.2-1, the package's configuration (`dpkg --verify`
clean, §7.5); FreeRDP 3.15.0 clients in one Xvfb each. Same scene (A/B/C/D, the 4K film at 30 fps), same
steps, same thresholds (§9 of 16), same box per desktop.

### 8.1 Capacity: how many sessions they bear

Two numbers per cell. **True green** = the last level with **all** sessions GREEN (the queue's «ultimo GREEN
vero» row). **Good** = the last level the climb passed, admitting a non-significant
DEGRADED (at most one actor out of four, within half of the band). «—» = not even one user.

⭐ **REMOTIX reclassified (§3-bis.2), done on the evening of 10 Oct.** `16-riclassifica.py` run on the 32 climbs
`*-f20-*` on **shadow copies** (links to the real files in `/tmp/prestazioni-ombra` on the server: the measures are
read-only), with `--fps-video 30`. All exited **0**: no level without rows touched changed class,
so the redone judgement is the climb's. **Exactly the three cells** foreseen in §3-bis change:
Intel GNOME 3K **1 → 4**, Intel XFCE 3K **4 → 8**, Intel XFCE Full HD **1 → 12**. All the other 29 stay
the same. To make it permanent next to the data the command of §3-bis.2 is enough (it writes only new files).

**Intel UHD 770 integrated** — REMOTIX (VA-API) / xrdp, true green · good:

| desktop | 4K | 3K (3200×1800) | 2K | Full HD |
|---|---|---|---|---|
| GNOME | **1 · 1** / — · — | **4 · 4** / 1 · 1 | **4 · 8** / 1 · 1 | **11 · 11** / 5 · 5 |
| KDE | **3 · 3** / — · — | **1 · 5** / 1 · 1 | **4 · 8** / 1 · 1 | **10 · 10** / 1 · 1 |
| XFCE | **4 · 8** / — · — | **8 · 8** / 1 · 1 | **10 · 10** / 3 · 3 | **12 · 12** / 6 · 6 |
| LXQt | **7 · 7** / — · — | **8 · 8** / 1 · 1 | **10 · 10** / 3 · 3 | **11 · 11** / 6 · 6 |

**AMD Radeon RX 6800** — REMOTIX (Vulkan) / xrdp, true green · good:

| desktop | 4K | 3K | 2K | Full HD |
|---|---|---|---|---|
| GNOME | **— · —** / — · — | **4 · 10** / 1 · 1 | **11 · 11** / 1 · 1 | **11 · 11** / 4 · 6 |
| KDE | **— · —** / — · — | **4 · 9** / 1 · 1 | **15 · 15** / 1 · 1 | **15 · 15** / 1 · 1 |
| XFCE | **2 · 2** / — · — | **12 · 13** / 1 · 1 | **15 · 15** / 3 · 3 | **15 · 15** / 6 · 6 |
| LXQt | **3 · 3** / — · — | **15 · 15** / 1 · 1 | **15 · 15** / 3 · 3 | **15 · 15** / 6 · 6 |

How to read them:
- **REMOTIX bears from 1.8 to 15 times xrdp's users** («good») in every cell where xrdp bears at least one
  (the minimum: Radeon GNOME Full HD, 11 against 6; the maximum: Radeon KDE 2K and Full HD, 15 against 1); at 4K xrdp
  bears none, REMOTIX from 1 to 8 on the Intel and 2-3 on the Radeon (XFCE, LXQt). In «true green» there are
  **three even cells**: Intel KDE 3K (1 and 1) and Radeon 4K GNOME and KDE (neither of the two); in the other 29 REMOTIX is
  ahead.
- **15 is the bench's ceiling, not the Radeon's**: in the 7 cells at 15, level 16 falls **only** because the
  17th session, the short check's, does not paint within 90 s (e.g. `amd-f20-fhd-xfce/livello-16-ripetizione`:
  16 GREEN, 1 FAIL = the check). The 16 users working are all green.
- **Radeon 4K GNOME and KDE «—»**: it is the RADV 25.0.7 driver (§3-bis.1, delay 51-56 ms with one user, threshold 50).
  With Mesa 26 GNOME reaches 4; the product stays on Debian 13's driver.
- **Where REMOTIX gives way on the Intel** (`16-rapporto.py`, «bottleneck» at the first non-green level): either the card's
  **drawing** engine at 98-99 %, occupied for 58-69 % by the sessions' **compositors** and for 25-31 %
  by the bench's browsers (KDE 4K and 2K, XFCE 4K); or the machine's **RAM** at 98-99 % (GNOME, XFCE and LXQt at 2K and
  Full HD), of which ~5 GB are the client browsers the bench runs on the same server. **On the Radeon** the
  **video** engine gives way (the encoding, ~100 %) or, on GNOME, the RAM. ⇒ It is the physics of DECISIONI §4.6-nonies: the bottleneck
  is upstream of us (composition) or in the bench's memory, not in the processor.

### 8.2 Video, processor, memory, delay

**The video** (user D with the 4K film at 30 fps, paints per second from the watcher's side), Intel and Radeon:
- REMOTIX **29.0-30.3** paints/s on all 106 GREEN levels (KDE excluded), **0 frames skipped**; it drops
  (20-29) only at the breaking levels. On KDE the page's counter rises to 53-58: it counts the compositor's
  redraws, not the film's frames `[?]`;
- xrdp **23.1-24.9** paints/s at **every** level, from 1 user up and with any load: **it loses ~1 frame
  in 5-6**, always. GREEN threshold 0.8·f = 24: xrdp is right at the edge, and on GNOME 2K at 4 users it falls below (23.1-23.7,
  DEGRADED). It is RemoteFX's ceiling on the processor (`rfx_frame_interval` and the compression), not the load.

**The processor and the memory**, level **4 users** (the last one xrdp lives through at least in Full HD; at 2K xrdp's level
4 is FAIL because of the wall of §8.3 but the four work and are measured). Processor **of the machine** (20 threads),
then the cores of the server side (enclosures `remotix` + `sessioni`, that is server, compositors and applications) and the
PSS memory of the same side:

| 4 users | REMOTIX Intel | REMOTIX Radeon | xrdp Intel | xrdp Radeon |
|---|---|---|---|---|
| machine, Full HD | 10.9-12.5 % | 10.4-12.5 % | 18.1-31.8 % | 18.2-31.0 % |
| machine, 2K | 11.2-13.3 % | 10.7-13.0 % | 23.0-38.6 % | 23.0-40.3 % |
| server-side cores, Full HD (GNOME · KDE · XFCE · LXQt) | 0.93 · 1.11 · 1.08 · 1.05 | 0.95 · 1.10 · 1.10 · 1.07 | 4.31 · 3.22 · 1.61 · 1.53 | 4.16 · 3.18 · 1.63 · 1.54 |
| server-side memory, Full HD (GNOME · KDE · XFCE · LXQt) | 2.4 · 3.1 · 1.8 · 1.9 GB | 2.7 · 3.5 · 2.0 · 2.0 GB | 4.1 · 4.8 · 2.9 · 2.8 GB | 4.1 · 4.8 · 2.9 · 2.8 GB |

⇒ For the same work, **xrdp consumes from ~1.5 to ~4.6 times REMOTIX's cores on the server side** (the maximum on
GNOME: Mutter on X11 plus xorgxrdp's capture and RemoteFX on the processor) and **~1.3-1.7 times the memory**.
REMOTIX moves the work onto the card (hardware encoding). With **a single user** instead xrdp on XFCE and LXQt
uses **less** of the machine's processor (1.9-2.6 % against 4.3-4.9 %): the FreeRDP client weighs less than a browser.
The gap opens with load, and that is what counts.

**The delay with one user** (key → image, p95, from the watcher's side, in the classification window;
REMOTIX: the page round trip; xrdp: XDamage) — ms, REMOTIX / xrdp:

| | GNOME | KDE | XFCE | LXQt |
|---|---|---|---|---|
| Intel 4K | 54 / 45 | 58 / 55 | 53 / 33 | 67 / 36 |
| Intel 2K | 43 / 37 | 43 / 41 | 40 / 32 | 41 / 41 |
| Intel Full HD | 38 / 35 | 39 / 39 | 37 / 33 | 36 / 44 |
| Radeon 2K | 42 / 39 | 45 / 40 | 36 / 38 | 35 / 34 |
| Radeon Full HD | 41 / 38 | 37 / 45 | 33 / 32 | 33 / 34 |

(The numbers of §7.9 differ by a few ms: there the last 200 samples of the session, here the classification
window.) ⇒ **Even**, xrdp a little ahead on the Intel at high resolution; and the yardstick favours xrdp (the page
round trip includes decoding and drawing in the browser, XDamage on Xvfb does not, §7.3). REMOTIX's advantage is
**holding under load**, not the single user's response.

### 8.3 ⚠ xrdp's capacity and the «wall» of 64 MB

`[M]` **Most of xrdp's breaks are not the working user's: it is the session that cannot manage to be
born**, and the cause is in the files. xorgxrdp asks, for **every** session, a shared memory area as large
as the screen, **W×H×4 bytes** (lines `rdpClientConAllocateSharedMemory … bytes N` in `journal-scatola.log`),
and when there is no more room the new session's Xorg dies with **`Caught signal 7 (Bus error)`** in
`rdpCapture` (`controllo-corto/diagnosi-sessione.txt`: it is the «crash» of §7.8). The boxes are born with podman's
default `/dev/shm`, **64 MiB** (`shm_size = "65536k"`, no `--shm-size` in `11-accendi.sh`).
The count matches step by step:

| size | bytes per session (read) | how many fit in 64 MiB | users + check | xrdp measured (XFCE, LXQt) |
|---|---|---|---|---|
| 4K | 33 423 360 | 1 (the 2nd just fits and gives way) | 0 + 1 | — |
| 3K | 23 756 800 | 2 | 1 + 1 | 1 |
| 2K | 15 073 280 | 4 | 3 + 1 | 3 |
| Full HD | 8 355 840 | 7 (the 8th just fits and gives way) | 6 + 1 | 6 |

⇒ On XFCE and LXQt **the wall is xrdp's limit, step by step**; on GNOME and KDE xrdp gives way **earlier** for
reasons of its own (GNOME: delay p95 67 ms with 2 users at 2K, ~51 ms and machine processor at 40-42 % with 6 in
Full HD; KDE: **input lost**, 3 actions out of 3 with no effect with 2 users, at 3K, 2K and Full HD, on both cards).

**How to read it, and how the user read it.** It is an **architectural difference**: xorgxrdp captures in shared
memory, W×H×4 bytes per session; REMOTIX does not — the frames go through DMA-BUF from the card to the encoder,
and the few memory buffers it uses (the fallback path of `src/wlroots.c`, the keymap) are born with
`memfd_create`, which does not live in `/dev/shm` — and indeed in the **same box, with the same limit**, REMOTIX let
16 in. The user (10 Oct): *«il 4K è un limite per tutti … i numeri parlano chiaro: remotix è più
efficiente e performante di xrdp grazie alla sua architettura più nuova»*.
⚠ **To be declared next to every xrdp capacity number:** on a normal installation `/dev/shm` is half
of the RAM (16 GB on this machine) and that wall is not there; xrdp's cells on XFCE and LXQt are therefore a
**lower bound** due to the box. The verdict on video, processor and memory (§8.2) does not depend on the wall:
it is measured with the users that were inside.

### 8.4 The limits of the measures

- **A single machine**, and a modest one: the Intel card is the **integrated** UHD 770. The Radeon RX 6800 is a
  high-end gaming card from 2020. The numbers do not carry over to other iron (DECISIONI §10.26: they stay goals,
  not promises in the SPECIFICHE).
- **The clients run on the server**: for REMOTIX up to 16 real browsers (~5 GB of RAM at 11-12 users: it is the RAM that
  runs out on the Intel at 2K and Full HD), for xrdp the FreeRDPs (1.8-2.4 cores at 4 users, the RemoteFX decoding).
  ⇒ REMOTIX's numbers are a **lower bound**; the network is not measured (everything goes through `lo`).
- **The bench's cap**: 16 users + 1 check. Seven Radeon cells sit at 15 because of the 17th session.
- **The memory guard** of §7.7 (below 3 GiB free the level is closed) existed only for xrdp, which never
  reached it (memory used ≤ 40 %); REMOTIX on the Intel would have triggered it at the breaking levels
  (RAM at 98 %), that is at the same points where the level is already FAIL.
- **Skipped frames, holes, audio** do not exist on the xrdp side (§7.3); the delay is compared only from the watcher's side.
  The card is not measured for xrdp (the engine readings are empty).
- **The 64 MB wall** (§8.3) cuts xrdp's cells on XFCE and LXQt.
- **Firefox and Marionette**: the false «stall» of §3-bis.2 is cured and the climbs already done are reclassified
  (§8.1); with Chrome it was not there.

### 8.5 The public table (§5)

It goes into the technical documentation, chapter «Performance and capacity» of the manual
(`docs/sources/technical/ch18_performance.py`), not on the site's home page. «Optimal up to» = true green;
«holds up to» = good. One row per card and size; the range goes from the worst desktop to the best (the detail
per desktop is in §8.1):

| machine | card and route | size | optimal up to | holds up to |
|---|---|---|---|---|
| i5-13500T, 31 GB | Intel UHD 770 (integrated) · VA-API | 4K | 1-7 | 1-8 |
| | | 3K | 1-8 | 4-8 |
| | | 2K | 4-10 | 8-10 |
| | | Full HD | 10-12 | 10-12 |
| i5-13500T, 31 GB | AMD RX 6800 · Vulkan | 4K | 0-3 | 0-3 |
| | | 3K | 4-15 | 9-15 |
| | | 2K | 11-15 | 11-15 |
| | | Full HD | 11-15 | 11-15 |
