# PHASES — what was done, phase by phase

*⚠ Historical measurements, on the machine of that time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without the card and colour conversion with swscale; those of encoding on the card and of audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision. The measurements redone after the change (1 Oct 2026) are in `fasi/18-senza-ffmpeg.md` §5.*

*The documents of the **closed** phases, sewn into a single document on **16 Aug 2026** by the user's
decision. ⛔ **It is not a summary**: the text is what it was, line by line, with the headings
lowered by one level so they fit under the chapters. No measurement, no mark and no
date has been touched.*

> ## ⛔⭐ THE RULE, AND IT HAS CHANGED IN ONE PLACE ONLY
>
> **`PIANO.md` §0.1 stays intact**: *«il documento di fase si apre all'inizio e si riempie strada
> facendo. Non si scrive alla fine»*. A document written afterwards is an **account**, and in an
> account the measurements are *remembered* instead of being *recorded*.
>
> ⭐ **What changes is where that document lives while the phase is open:**
>
> | | |
> |---|---|
> | **the phase in progress** | has a file of its own, `fasi/NN-nome.md`, opened on the day the phase opens. ⭐ One always works on a small file |
> | **the closed phase** | becomes a **chapter of this file**, folded in at the closing |
>
> ⇒ The project keeps **ten documents when a phase is closed and eleven while work is going on**, and one never edits
> a fourteen-thousand-line file in the middle of a phase.
>
> ⛔ **And the rule this does NOT loosen**: the chapter is not written at the closing. At the closing
> one *moves* a document that already existed since the phase opened. If a chapter appears
> here without ever having existed as a file, the rule has been violated — and it shows, because the measurements
> would not have the time next to them.

## How to find something in here

Every chapter keeps **the numbering it had as a separate file**, and **the chapter keys are the
names the files had**: a reference that used to say §01-filo-nudo §7 now says
**`FASI.md` §01-filo-nudo §7**, and the section has the same number as before.

| chapter | the phase | closed on | lines |
|---|---|---|---|
| [**§00-ambiente**](#00-ambiente) | The environment and the benches | | 649 |
| [**§01-filo-nudo**](#01-filo-nudo) | The bare wire | 11 Aug 2026 | 2 151 |
| [**§02-primo-fotogramma**](#02-primo-fotogramma) | The first frame | 13 Aug 2026 | 594 |
| [**§03-movimento**](#03-movimento) | Movement | 14 Aug 2026 | 755 |
| [**§04-si-comanda**](#04-si-comanda) | Taking control | 14 Aug 2026 | 874 |
| [**§05-la-sessione**](#05-la-sessione) | The session | 16 Aug 2026 | 1 470 |

⚠ **And `§00-ambiente` carries an appendix at the end** that used to be §00-ambiente: the
tools that lived **only on the server**, and the logs that are measurements.

### The four rules, in brief

The model is in `PIANO.md` §0.2.

1. the **decisions** are in `DECISIONI.md`, only once: here one **refers**, one does not copy;
2. **«che cosa non ha funzionato»** is filled in even when it makes us look bad;
3. the phase closes on **a measurement judged by the user**, not on a complete document;
4. the **bench is certified** before being believed.

---

> # ⛔⛔ THE AGENTS' REPORTS ARE NO LONGER ON DISK — *16 Aug 2026*
>
> *The user's decision: «elimina i rapporti degli agenti: non dovrebbero servire più».*
>
> `fasi/rapporti/` and `web/rapporti/` — **94 files, 42 900 lines**, 63 % of everything the
> project had written — have been removed.
>
> ## ⭐ But they are NOT lost, and this is the point: how to recover one
>
> They went out with `git rm`, so the history has them in full. **The last commit in which they live is
> `0c85e5c`**, and from there any report can be pulled out without putting it back on disk:
>
> ```
> git show 0c85e5c:fasi/rapporti/F3-E-anello-rimisurato.md | less     # leggerne uno
> git show 0c85e5c --stat -- fasi/rapporti | head -100                # vedere l'elenco
> git checkout 0c85e5c -- fasi/rapporti/F4-O2-anello-input.md         # riportarne uno su disco
> ```
>
> ## ⚠ And the price, measured before removing them instead of discovered afterwards
>
> ⛔ **169 references** from the documents that remain pointed inside those reports, towards **50 different
> files**. Those references now name a file that is not on disk — ⭐ **and they remain resolvable**
> with the three lines above, because the name in the reference is still the name in the history.
>
> ⚠ **The three most cited**, because they are the ones someone will look for first:
> `web/rapporti/S-esiti-sonda.md` (18 references — ⛔ and it was not a report, it was **the measured outcomes
> of the browser probe**, with the scene next to every number), `F5-desktop-vero.md` and
> `F2-6-giudizio.md` (9 each).
>
> ⇒ ⛔ **The rule this touches is `LEZIONI.md` §9.8**, *«la fonte sta accanto alla misura»*: the
> source **is still there**, but now it is in a commit instead of a file. Whoever cites a number
> measured from here on should know it — and the right place for a number that must survive is **the
> phase chapter**, not the report that produced it.

---

## ✅ The state: `05` is closed, and `6` is not open yet — 16 Aug 2026

`§05-la-sessione` was opened on 15 Aug **with its document and before a line of code**, and
closed on the 16th **on the user's judgement** (§7 collects his words, with the date — not a verdict
written by us).

⭐ **And the test that closed it was done by the user**, with real work inside: an infinite loop
in a terminal, the browser closed, the window shrunk, the return — and the loop was still
running. ⛔ All our tests had an **empty** desktop, which as soon as it is reborn is identical to how it was:
the worst possible witness for the question «è sopravvissuta?».

⏳ **And phase 6 did not open right away**: the user first asked for a review of `PIANO.md`,
*«che ha alcuni punti secondo me fuori sequenza»*.

> ### ✅ ⭐ The review was done on 16 Aug 2026, and it changed two things
>
> | | |
> |---|---|
> | ⭐ **phase 8 is no longer «the acceleration»: it is «zero copy»** | hardware encoding had already entered the product on **13 Aug**, and 10 bits are a wall **upstream** (the capture). What remained was zero copy, and it is the whole phase |
> | ⭐⭐ **multi-tenant moves ahead of the new desktops** — *«PRIMA si chiude lo sviluppo anche con il multi-tenant, e solo dopo si pensa agli altri DE»* | **it was phase 12, it is phase 10**; KDE 10 → **11**, XFCE/LXQt 11 → **12**. 9 and 13 stay where they are (`DECISIONI.md` §4.6-sexies) |
>
> ⇒ **The order as of now**: 6 · 7 · 8 zero copy · 9 quality · **10 multi-tenant** ·
> 11 KDE · 12 XFCE and LXQt · 13 the service.
>
> ⛔ **Reading trap, and it applies to whoever searches backwards**: `STUDI.md` §kde, `STUDI.md` §gnome,
> `STUDI.md` §xfce and `STUDI.md` §lxqt say at the top *«per la fase 11»*, but that is **phase 11 of
> v1** — they are studies of 7-8 Aug 2026, written before this plan existed. Those numbers **are not
> these numbers**, and indeed they have not been touched.

> ### ⚠ ~~`05` is missing~~ — as it was written on 15 Aug, and it is kept
>
> *15 Aug 2026.* Phase 5 has not been opened yet. ⛔ And the **tail of phase 4** — the night in
> which the canvas became the browser window — sits **inside `§04-si-comanda`**, not in a
> document of its own: the phase number is given by **why** the work was done, not by the list of
> things produced. That work touches content of phase 6, and `PIANO.md` says which of its parts are
> found already done.
>
> ⚠ That tail carries its own reservation of form at the top: it was written **at the closing**, against the
> rule above. The measurements however are not remembered — they come from the server logs and from the bench
> rounds, with the time next to them. ⛔ The rule stands: **phase 5 opens with its document**.


---

<a id="00-ambiente"></a>

## Phase 0 — The environment and the benches

Opened on **9 Aug 2026** · **Closed on 9 Aug 2026**

> First phase of REMOTIX, and the only one that produces no product. The model of this document is
> in [`PIANO.md`](PIANO.md) §0.2; the decisions are in
> [`DECISIONI.md`](DECISIONI.md) and here one **refers**, one does not copy.

---

### What it must produce

The machine that compiles and tests, v1's benches put back into working order, and the Android environment that the
probe of phase 2 will require.

**What the user sees and judges**: v1's numbers **reproduced** — Mutter's capture
delivering ~37 frames per second, KWin's ~60.

⭐ **It is not a product result: it is the positive control of the whole project.** If the bench cannot
reproduce a number we know to be true, every measurement of the thirteen following phases is suspect —
and not *a little*: exactly as much as the rhythm measurements of phases 3-9
of v1 were, which were all thrown away (`LEZIONI.md` §1.1).

---

### The bench

⛔ *Written before developing, and reviewed first — `PIANO.md` §0.4, moment 1.*

#### B1. What is measured, and with what scene

| | |
|---|---|
| **the instrument** | `fondamenta/banchi/banco-compositori/misura-cattura` — PipeWire consumer that counts the frames and reports buffer type, damage, recycled buffers, whether the drawing was finished, and the distribution of intervals. It can set up Mutter's virtual screen by itself |
| **the scene** | ⛔ **declared, and moving at every redraw**: full screen, opaque, redrawing at every *frame callback* of the compositor. Not a still scene, not a motion driven by keystrokes (`LEZIONI.md` §1.1). ⚠ *Here `weston-simple-egl -f -o` was named: `[M]` **on 13 Aug 2026 it is not installed**, and from phase 3 the scene is ours — `banchi/03-scena.c`, which carries a mark and **counts its own waits***. ⛔ **And there is a third requirement, learned in phase 3**: the scene must be **on the monitor being captured** |
| **the control that says whose cap it is** | ⛔ **how much the client draws**, counted next to how much the capture delivers. Without it, a cap of the scene gets attributed to the compositor — and vice versa |
| **the duration** | ⚠ **at least 300 frames, and the first ones are discarded**: the first ten are the startup, when everything is repainted, and on them the ratio flips (`LEZIONI.md` §1.4) |

#### B2. How this bench is certified, before being believed

⛔ The question is not «does it work?», it is **«would it notice that it does not work?»**. Four tests, and
none costs more than a minute:

| # | The test | What it proves |
|---|---|---|
| **C1** | the instrument is pointed at **KWin `--virtual`**, where the expected number is 59-60 `[M]` 8 Aug | it is the positive control proper: *can the instrument find something that is certainly there?* (`LEZIONI.md` §1.9 rule 2) |
| **C2** | the **scene is switched off** and measured again | ⛔ the number **must collapse**. If it stays at ~37 with the scene still, the bench is not measuring the capture but something else, and every following phase would inherit the lie |
| **C3** | the instrument is pointed at a node **that does not exist** | ⛔ it must say **«I failed»**, not «zero frames». «Empty» and «forbidden» look the same, and it is the lesson that cost a wrong line in a reference document (`LEZIONI.md` §1.9) |
| **C4** | the bench is run **twice in a row**, without restoring the machine | one that passes only from a clean machine is not a bench, it is a demonstration (`LEZIONI.md` §2.3-ter) |

#### B3. ⛔ The three bench defects already paid for, which are checked in the code here

They are three lines, and in one afternoon of 8 Aug they produced three false reds — **none of the
three in the product** (`LEZIONI.md` §2.3-bis):

1. **`pgrep -x weston-simple-egl` never finds anything**: `comm` is truncated to **15 characters** and
   that name has **17**. `pgrep -f` is used. ⚠ The symptom is «the scene did not start» while the
   capture delivers 58 frames per second;
2. **a rejected option is not a defect of the target**: a client that prints the help page
   and exits makes the bench read «zero frames» and blame the server. Command lines are
   **copied from a bench that works**, not remembered;
3. ⛔ **never `sudo` inside a command whose stderr is redirected**: the password prompt goes
   to stderr, and the bench stays **hung forever, in silence**. It is not «remembering it»:
   it is not writing it.

#### B4. The certification of the environment, which here is worth as much as that of the bench

This phase measures a machine, not a product — so the environment **is** the unknown, and must be
ascertained with the same severity:

| | Why it is not taken for granted |
|---|---|
| ⛔ **the user is in the `render` and `video` groups** | without them, the Shell does not open `/dev/dri` and **Mutter falls back to software rendering without an error anywhere** `[M]` 6 Aug. The 37 frames measured that way would be a different number under the same label — error form **E2** |
| ⛔ **and the `systemd --user` manager has been restarted afterwards** | the supplementary groups of an already-running process **do not change**: adding the user to the group without restarting the manager leaves everything as it was, and it looks done |
| **which card the compositor draws on** | the machine has **two** GPUs (Intel `0000:00:02.0`, Radeon `0000:03:00.0`), and a buffer from the wrong card cannot be imported: the symptom is software composition **without an error** (`LEZIONI.md` §4 trap 6) |
| **the rootfs lives in RAM and is wiped at reboot** | ⚠ so «the machine is in order» is true **for this power-on**. The restoration is tested **by rebooting**, not by rereading the script (`LEZIONI.md` §2.5-bis) |

---

### What was developed

No product code: this phase puts back into working order what already exists — plus two new
things, which are bench.

| | |
|---|---|
| `fondamenta/banco/provision-server.sh` | the restoration of the machine, rerun on 9 Aug: GNOME 48.7, `vainfo`, `libei1`, and the user in the `render`/`video` groups |
| ⭐ `fondamenta/banco/provision.sh`, step **5-bis** | **the authentication test users, declared on 11 Aug 2026** — see the box below |
| `fondamenta/banchi/banco-compositori/` | brought onto the hardware in `/media/REMOTIX/tmp/`, recompiled in the `devroot` |
| ⭐ `banchi/00-sessione-gnome.sh` | **new**: starts a GNOME session without a monitor with the environment composed from scratch, and **verifies** that it is headless instead of hoping so (`DECISIONI.md` §4.3-bis) |
| ⭐ `banchi/00-c1-wlroots.sh` | **new**: the certification of `misura-wlroots`, the third bench, on sway and labwc |
| ⭐ `banchi/00-c1-kwin.sh` | **new**: the C1 certification — the same instrument on KWin, with the expected value from `STUDI.md` §kde §5.7 printed before the measurement |
| ⭐ `banchi/00-rimetti-macchina.sh` | **new**: puts the machine back on its feet starting from **before the disk**, which is the step no script contained |
| ⭐ `fondamenta/banchi/banco-compositori/misura-cattura.c` | **fixed**: now it distinguishes zero from failure |
| ⭐ `fondamenta/banchi/banco-compositori/banco.sh` | **fixed** twice: `stdbuf -oL` on the scene, and the check that the scene is alive before believing the number |
| ⭐ `fondamenta/banchi/banco-compositori/provision-banco.sh` | **fixed**: takes the credentials with `sudo -v -S -p`, like the other restoration script |

⚠ The session is started with `gnome-session --session=gnome` and the environment from `sessione.c`; the
farewell is **`Logout(2)`**, not `systemctl --user stop`.

---

### The measurements

*(Filled in along the way. The declared scene next to every number.)*

#### The state of the machine, **before** touching it

| What | Measured | Date |
|---|---|---|
| GNOME installed on the server | ⛔ **no** (`dpkg-query` → not-installed) — confirms `STUDI.md` §gnome §2 | 9 Aug |
| `vainfo` installed | ⛔ **no** | 9 Aug |
| `nicfio` in the `render`/`video` groups | ⛔ **no** (`nicfio sudo`) | 9 Aug |
| `/media` mounted, `/etc/fstab` | mounted; ⚠ **fstab empty**, as in `LEZIONI.md` §2.5-bis | 9 Aug |
| apt cache on `/media` | ✅ 1450 `.deb`, 1,1 G — the reinstallation downloads almost nothing | 9 Aug |
| visible GPUs | ✅ Intel `00:02.0` → `renderD128`, Radeon `03:00.0` → `renderD129` | 9 Aug |
| rootfs | ⚠ **32 G in RAM**, wiped at reboot | 9 Aug |

#### After the restoration (`provision-server.sh`, exit 0)

| What | Expected | Measured | Date |
|---|---|---|---|
| Mutter / gnome-shell | 48.7 (Trixie) | ✅ **48.7**, `gnome-session` 48.0 — the versions that `STUDI.md` §gnome studied | 9 Aug |
| `nicfio` in the groups | `render`, `video` | ✅ `nicfio sudo video render` | 9 Aug |
| `libei1` | present | ✅ 1.3.901 | 9 Aug |
| `weston-simple-egl` for the scene | present | ⛔ **MISSING on 13 Aug 2026** — `[M]`. It was ✅ `/usr/bin/weston-simple-egl` on 9 Aug, and it vanished: **the rootfs is in RAM** and the machine that restores itself does not restore itself *completely* (`LEZIONI.md` §2.5-bis). ⇒ The scene of phase 3 is **ours** (`banchi/03-scena.c`), and does not depend on a package | 9 Aug → **13 Aug** |

#### `vainfo` — the `[?]` of the encoder budget, closed

⛔ *Verified with the exit status, not only with the list: `USCITA=0` on both nodes. An
empty list and a driver that does not open look the same (`LEZIONI.md` §1.9).*

| | Intel UHD 730 (iHD 25.2.3) | Radeon RX 6800 (radeonsi) |
|---|---|---|
| **HEVC Main10 encoding** | ✅ `EncSliceLP` | ✅ `EncSlice` |
| HEVC **4:4:4**, 8 and 10 bit, encoding | ⭐ ✅ **yes** | ⛔ no |
| H.264 · VP9 · JPEG encoding | yes | H.264 yes |
| **AV1** | ⛔ **no profile, not even for decoding** | decoding only |

**The three consequences, all written where they belong and not only here:**

1. the 10-bit goal has its hardware path on both (`DECISIONI.md` §4.6);
2. ⭐ **4:4:4** was `[?]` with «Intel sometimes» next to it: on our hardware it is **yes**, even at 10 bit
   — it does not reopen the decision, which had been taken for the Android side, but it makes it measurable
   without buying anything (`DECISIONI.md` §2.3);
3. ⛔ `SPECIFICHE.md` §11.4 said «RDNA2 and Alder Lake only decode it»: **false for
   the Intel**, which does not touch AV1 at all. Fixed the same day.

⚠ And one line that matters for phase 8: on the Intel the only encoding entry point is **`EncSliceLP`**,
the *low power* path. It is not a fallback — it is the only one that chip exposes — but it has its own
bitrate control options, and it is the exact spot where v1 hurt itself twice.

#### ⭐ The positive control of the project — reproduced

**Declared scene**: `weston-simple-egl -f -o`, full screen, opaque, one commit for every
redraw of the compositor. 1920×1080 virtual monitor set up by the bench via `RecordVirtual`,
20 seconds of measurement, 7 discarded. GNOME 48.7 headless, DMA-BUF, BGRx, 60 declared.

> ⛔ *13 Aug 2026, and it must be read before redoing this measurement: **the scene named here is no longer
> available** (`weston-simple-egl` is not installed), and **the number this positive control
> reproduced — Mutter's ~37 — does not reproduce**. It is not a defect of the bench: at the rate it
> was asked for, Mutter delivers **31,5**, and by renegotiating the rate alone (monitor 120, brake 90)
> it delivers `[M]` **61,4**. ⚠ That the 37 was the remainder of a **truncated division** is the
> most likely explanation, and it is `[R]` — read in Mutter's code, **not measured**
> (`STUDI.md` §gnome §8.2; the «law on 13 points» that could be read here on 13 Aug **fell that same
> evening**).*
> ⇒ **The positive control of the project must be redone against the clean cells of
> `banchi/03-b14-esiti.jsonl`, not against the number**, and with the scene of phase 3 — which **counts its
> own waits** and declares whether it ran idle.

| What | Expected | Measured | Outcome | Date |
|---|---|---|---|---|
| **Mutter, moving scene** | **~37 fps** `[M]` v1 | ⭐ **36,2 on average over six rounds** — 37,82 · 37,33 · 33,66 · 36,67 · 36,39 · 35,42 | ✅ | 9 Aug |
| ⭐ **how much the CLIENT draws** | ≥ the delivered | **60,0** in every round ⇒ **the cap is the compositor's, not the scene's** | ✅ | 9 Aug |
| C2 — the same scene **still** | collapses | **0,00**, with active stream and negotiated format | ✅ | 9 Aug |
| C4 — repeated rounds without restoring anything | equal | six rounds, spread **33,7-37,8** | ✅ | 9 Aug |
| C3 — nonexistent node | «failed», not «zero» | ⛔ **gave 0,00 and exit 0** → fixed, now `GUASTO` and exit 2 | ✅ after cure | 9 Aug |
| **C1 — the same instrument on KWin** | **59,2** `[M]` `STUDI.md` §kde §5.7 | ⭐ **58,92** (1180 frames, median 17,0 ms) | ✅ | 9 Aug |
| C1-bis — KWin **in memory** | 43,3 `[M]` 8 Aug | ⚠ **49,67** — higher than expected, see below | ⚠ | 9 Aug |

⭐ **C1 is the certification that is worth more than all the others, and it was not «another number»**: it says that the
instrument can give a **different** number when the thing measured is different. Pointed at KWin it gives
58,92 with median 17,0 ms; pointed at Mutter it gives 36 with median 33,3. Had it answered ~37 on
KWin too, we would be measuring the instrument and not the compositors.

⚠ **Mutter's spread must be stated, not hidden**: six rounds between 33,7 and 37,8, with the **median
of the intervals fixed at 33,3 ms in all six**. The beat is very stable; what moves is the tail
(maximum intervals from 33,6 to 75,0 ms). So v1's «~37» is reproduced, but the honest number to
cite is **36 ± 2**, not 37,8.

⚠ **And the 49,67 in memory does not match the 43,3 of 8 Aug.** I do not explain it: I declare it. The
known differences between the two measurements are three — 20 seconds per cell instead of 10, `KWIN_COMPOSE=O2`
not set (which `LEZIONI.md` §1.11 considers **inert** anyway, measured), and the Radeon today
**present but not openable** instead of denied. `[?]` None of the three has been verified as the
cause. It does not affect the certification, which passes on the zero-copy column.

⭐ **And the distribution of intervals says more than the number alone**: `min 16,2 · mediana 33,3 ·
p95 33,5`. The frames arrive at **one or two refresh periods**, never at half — that is, two clocks
at 60 beating against each other, which is exactly the mechanism that `STUDI.md` §gnome §8.2 reads in the code
(`maxFramerate` acts as a brake on the capture **and** as the frequency of the virtual monitor). ⚠ **It is not the
proof of the cure**: it is the proof that the explanation is compatible with what is seen. The cure
remains experiment M3 of phase 3.

⚠ **Two more things read in the same round**, and they must be kept because they touch decisions already written:

| | |
|---|---|
| `disegno non finito` on **all** the counted frames | confirms question 9: with zero copy **100 %** arrives with the drawing in progress. ⚠ *Rewritten on 9 Aug after the review: this line said «944 out of 757», which is a ratio between two different populations — the 944 was over the arrived frames, not the counted ones. The conclusion holds (944 out of 944), the sentence does not. Measured again with the fixed bench: **749 out of 749**, and now the two columns share the denominator* |
| `danno: pieno 15, parziale 929` | **partial damage is the rule**, full damage the exception — as in `LEZIONI.md` §1.4 (282 out of 300) |
| `Boot VGA GPU /dev/dri/renderD128 selected as primary` | ⭐ **Mutter picks the Intel by itself**, by «Boot VGA» — unlike KWin, which takes the first one it manages to open. See `DECISIONI.md` §4.6-ter |
| `amdgpu: amdgpu_cs_ctx_create2 failed. (-13)` | the Radeon is seen but not usable (permission denied): `[?]` to be understood whether it is the udev rule or something else. **It does not hinder us**: the primary is the right one |

#### ⭐ The test that matters most: after a REAL reboot

*The machine was rebooted at **10:16 on 9 Aug 2026**, at the user's request, and
put back on its feet from scratch. `LEZIONI.md` §2.5-bis: «a restoration is tested by rebooting, not by
rereading the script».*

| What | Measured | Date |
|---|---|---|
| **manual** steps needed before the restoration existed as a file | ⛔ **one**: mounting `/media` | 9 Aug |
| restoration scripts to run | ⚠ **two**, and the first does not name the second | 9 Aug |
| defects the reboot brought to light | **four** (items 6, 7, 8 and 9 below) | 9 Aug |
| **Mutter, after the reboot and the restoration** | ⭐ **36,78 · 36,33 · 37,05** — median 33,3 ms, client at 60,0 | 9 Aug |

⭐ **The numbers before the reboot were 33,7-37,8; those after 36,3-37,1.** The machine put back
on its feet from scratch **reproduces what it reproduced before** — and it is this, not this morning's measurement,
the sentence that authorises believing the measurements of the thirteen phases that follow.

#### ⭐ The three families of compositors, all with a reproduced number

*Same scene, same machine, same afternoon — which is the only way three numbers can
be put side by side.*

| Compositor | Model | Expected | Measured | Median interval | Client |
|---|---|---|---|---|---|
| **Mutter** (GNOME) | pushes, PipeWire | ~37 `[M]` v1 | **36,3-37,1** | 33,3 ms | 60,0 |
| **KWin** (KDE), zero copy | pushes, PipeWire | 59,2 `[M]` 8 Aug | **58,92** | 17,0 ms | 60,0 |
| **sway** (wlroots), 1080p | ⭐ **makes you pull**, `wlr-screencopy` | ~61 `[M]` v1 | **61,02** | 16,4 ms | 61,2 |
| **labwc** (wlroots), 720p | makes you pull | ~61 | **61,16** | 16,4 ms | 61,2 |

⭐ **And the three benches are three different programs, now all certified**: `misura-cattura` (PipeWire),
`nodo-kwin` (KDE's protocol, used inside C1) and `misura-wlroots` (`wlr-screencopy`).
The last one had been recompiled **and never pointed at anything** — that is, not certified — until
this round.

⭐ **The sway row counts double**, because the model is the opposite: Mutter and KWin **push** the
frames, wlroots makes you **pull** them, one request per frame. That the same method gives a
consistent number on two opposite models was not a given: it is information, not a confirmation.

#### What stays out of this phase, by choice

| What | Why not here |
|---|---|
| the **tables by resolution** (720p → 4K) of Mutter and KWin | they already exist `[M]` in `STUDI.md` §kde §5.7 and in `LEZIONI.md` §3. Redoing them now would be measuring before having the question: they serve phase 8 (the acceleration) and 10 (KDE) |
| the `video` and `carico` scenes | same: they answer questions of phases 3 and 9 |
| `adb`, Desktop AVD, the real phone | the Android environment serves the **probe of phase 2**, and the user asked to leave it alone for now. ⚠ *Reread on the evening of 9 Aug: `adb` and the AVD **are no longer needed at all** (there is no Android application any more), and **the real phone serves phase 1**. See the corrected item in «Che cosa resta `[?]`»* |

---

### ⛔ What did NOT work

⭐ **Five defects in one afternoon, and none was the compositor's: four were the bench's and one
the provisioning's.** It is phase 0 doing its job — had these appeared in phase 3,
they would have looked like Mutter defects.

#### 1. ⛔ The meter did not distinguish zero from failure — and it was the instrument that certifies all the others

Pointed at a node that does not exist, `misura-cattura` answered **«frames 0 → 0,00 per second»
with exit 0**: identical to a still scene, which is a legitimate result. Two opposite things behind
the same face (`LEZIONI.md` §1.9; it is question 4 of `REVIEWER.md` §1).

**The cure**: the discriminant is whether the stream ever became **active**. Now it prints `GUASTO`,
not a `RIGA`, and exits with 2. ⭐ And the reason comes as a bonus, which PipeWire was already giving and which
we threw away: *«no target node available»*.

⚠ **The price we did not pay**: a round gone wrong — a wrong node, a permission
denied, the compositor not yet up — would have entered the table as «the compositor delivers
nothing».

#### 2. ⛔ The headless test looked for a sentence that, if everything goes well, never appears

The first draft of `00-sessione-gnome.sh` verified headless mode by searching Mutter's log
for *«No seat assigned, running headlessly»*. Then, having read the code
(`meta-backend-native.c:748-764`): that message comes out **only** on the **accidental** path —
when headless mode is inherited from the absence of a seat. Asking for it with `--headless`, as
our drop-in does, Mutter exits earlier and **says nothing**.

⛔ On a perfectly healthy session the test would have given **red forever**. It is `LEZIONI.md`
§1.11: for every indirect test one must write what the opposite case would look like, or the test does not
discriminate. Now the bench recognises **both** ways, and says which of the two it is.

#### 3. ⛔ «No line found» was a denied read

The first attempt to read what Mutter says used `journalctl --user`, which answered with
zero lines. Not because Mutter was silent: **the command had not been able to open anything** — first because of
permissions (`insufficient permissions`), then because on this machine the journal **does not exist
at all**, the rootfs living in RAM.

⭐ The cure does not require root: the Shell's unit is a **user** unit, so a drop-in in
`~/.config/systemd/user` sends its output to a file of ours.

⚠ **And the consequence goes beyond this phase**: `LEZIONI.md` §1.10 says *«accendi il registro del
componente che nega»*. On this machine that log **is not there on its own**, and every phase that wants
a component to tell it something will have to obtain the channel for it.

#### 4. ⛔ Restarting the session: `pkill` leaves the manager alive, and nobody says so

`pkill gnome-session` left `gnome-session-manager@gnome.service` **active with the
compositor dead**: the restart did nothing, and the bench waited forty seconds
without a line explaining why. It is `LEZIONI.md` §2.3-ter — on Plasma it gave «Could not start
Plasma session», here it **gives no error at all**.

⛔ **And the first cure was wrong in turn**: waiting for `is-active` to be *different from
`active`* unblocks after half a second, because it goes through **`deactivating`** — that is, one restarts
inside the teardown interval, which is the defect the guard was supposed to remove. One waits for
`inactive`. And the right farewell is **`Logout(2)`** (`STUDI.md` §gnome §3.2): `systemctl --user stop` does not
stop the manager, and `Logout(1)` would show a dialog that in an unattended session nobody
sees.

#### 5. ⚠ The provisioning did not declare a dependency of the benches

Reading the journal requires the `adm`/`systemd-journal` groups, which `provision-server.sh` does not
grant. It is the same form as `LEZIONI.md` §2.5-bis — *«i banchi dipendono da cose che il
provisioning non installa»* — and it showed up at the first real reboot. ⚠ Here it ended in a dead
end (the journal is not there anyway), but the line must be added all the same: **the dependency existed and
was not declared**.

#### 6. ⛔⛔ The real reboot: the script that puts the machine back on its feet **is on the disk that does not mount**

*Tested on 9 Aug 2026 at 10:16, really rebooting the server instead of rereading the script —
which is precisely what `LEZIONI.md` §2.5-bis prescribes. The user asked for it.*

Found right after boot, **without touching anything**:

```
/media is not a mountpoint
/etc/fstab: 1 riga, vuota
ls: cannot access '/media/REMOTIX/provision-server.sh': No such file or directory
gnome-shell: unknown ok not-installed
id -nG nicfio: nicfio sudo          ← niente render, niente video
```

⛔ **The restoration could not be run.** Not «it was incomplete»: **it did not exist as a file**, because
it lives on `/media` and `/media` does not mount by itself. The first command after every reboot is a
mount that no script contains.

⚠ **And the part that weighs more than the defect: the lesson was already written.** `LEZIONI.md` §2.5-bis has said
so since 7 Aug, in these words — *«il disco non si monta da solo — `/media` vuota,
`/etc/fstab` senza righe, e i sorgenti stanno lì. Senza quel passo il primo dei tre comandi non
esiste nemmeno come file»*. **The cure was never applied**: it remained a note in a
document. It is invariant **I7** in reverse — the protection against a known defect was not in a
configuration line that can be lost, it was in a **memory**, which is worse.

⭐ **The cure, written today**: `banchi/00-rimetti-macchina.sh`, which starts from **before** the disk —
it mounts `/media` by **UUID** (not by node name, for the same reason the GPU is chosen
by PCI id) and then calls the declared restoration. It also has a `controlla` verb, which says what
is missing without touching anything.

⚠ **And it does not solve the root, and that must be said**: this file too lives on `/media`. The root is a line
in `/etc/fstab`, which the rootfs in RAM wipes at every boot — so it must be put there by whoever builds
the rootfs image, not by us. `[?]` **It stays open**, and it is the real issue the reboot
uncovered.

#### 7. ⛔ And the benches depend on a **second** script, which the first does not name

With the machine put back on its feet with `provision-server.sh` (exit 0, over 500 packages), the measurement
gave **`fps=0.00` for three rounds in a row**. With the capture active that is a **legitimate zero**
— «the compositor has nothing to deliver» — and it was true: there was **nothing to capture**,
because the `weston` package was missing and `weston-simple-egl` did not exist at all.

⛔ `weston`, `glmark2-wayland`, `mpv` and `ffmpeg` **are not in `provision-server.sh`**: they are in
`provision-banco.sh`, a second script the first neither calls nor names. It is the exact second
half of `LEZIONI.md` §2.5-bis — *«i banchi dipendono da pacchetti che il provisioning non
installa»* — reproduced to the letter one day after being written.

#### 8. ⛔ The bench printed a measurement of a scene that had never started

It is the third face of the same defect, and the most insidious because the first two were already cured:
`misura-cattura` now distinguishes «stream never active» from «zero», but **«stream active and scene dead»**
still produced a `RIGA` with `0.00`, which in a table would look like a mute
compositor. The scene's log said *«failed to run command 'weston-simple-egl'»*, and nobody
looked at it.

**The cure**: `cella` checks that the scene is alive before believing the number, and otherwise
prints `GUASTO` with the scene's log inside.

⛔ **And the first cure was wrong**: `kill -0 $pid` **succeeds on a zombie** — a child that died
immediately stays in the process table until someone reaps it, so «the pid exists» is not
«the process is alive». The guard did not fire. One reads the **state** in `ps`, which says `Z`.

#### 9. ⚠ Two restore scripts for the same machine, two different ways of handling `sudo`

`provision-banco.sh` stopped at the first line with *«sudo: a terminal is required»*:
`provision-server.sh` takes the credentials with `sudo -v -S -p` from the first line, this one uses
bare `sudo`. Whoever brings the machine back up remotely — that is, always — finds the first one
working and the second one not.

#### 10. ⛔ `kill 0` kills its own process group — and the bench vanished without a line

In the C1 bench the cleanup wrote `kill ${PID_SCENA:-0}`. When the variable is not yet
defined — that is, if something fails **before** opening the scene — it becomes `kill 0`, which does not
mean «don't kill anything»: it means **kill my whole process group**, remote shell
included. The bench ended without printing **a single line**, and from outside it looked like
a command that does not start.

⚠ The general shape is that of §1.9 once again: the way a bench **fails** must be
designed as much as the way it succeeds.

#### 11. ⛔ Compared against the wrong column, the bench seemed to be ten frames off

The first round of C1 measured KWin **in memory** (49,67) and compared it with the **59-60** of
`STUDI.md` §kde, which is the **zero-copy** column. For a few minutes the bench seemed to be wrong;
it was answering correctly a different question. The table in `STUDI.md` §kde §5.7 has two columns, and at 1080p
it says 59,2 and 43,3.

⭐ **The cure is in the bench, not in the reader's memory**: now `00-c1-kwin.sh` takes the path
as an argument and **prints the expected value** before measuring. A bench that knows its own expected value does not
leave the comparison to whoever is watching.

#### 12-bis. ⛔ A label declaring a size the compositor had never honoured

The first round on **labwc** printed «1920×1080» on a capture made at **1280×720**: `labwc`
does not take width and height on the command line — the wlroots headless backend is born at
720p and stays there — while the bench passed the size only as a *label*.

⚠ **And the number was right**: 61,16, which at 720p is exactly the expected value. Nothing would have looked
wrong. What unmasked it was the fact that `misura-wlroots` **prints the real size next to the
number**, instead of repeating the label it had been given — that is, a tool that does not
trust its caller.

It is shape **E2** applied to the bench: two different sizes under the same label. Now with
`labwc` the label does not declare a size we did not ask for, and whoever wants 1080p on wlroots
uses `sway` — where the size is in the configuration and was honoured (**61,02 at 1920×1080**,
confirmed by the tool).

#### 12. ⚠ The check that says «whose cap it is» was mute because of a buffer

At the Mutter cell the scene log was **empty**, and it looked as if the client had not
printed anything. `stdbuf -oL` was missing: towards a file the output is block-buffered, and at
scene shutdown its frames per second stay in the buffer. ⭐ `banco-altri.sh` already had
`stdbuf` — the difference between the two files was the defect.

**With the cure** the check of `LEZIONI.md` §1.1 finally speaks: the client draws **60,0** in
every round while Mutter delivers 36. **The cap belongs to the compositor.** Without this number,
that sentence would have been a hypothesis.

#### And a measurement defect I made myself, while measuring

Twice in an hour I read `$?` **after a pipe**, where it is the status of the last command and not of
the one that mattered: once `COMPILAZIONE=0` while `gcc` did not exist at all. And once
`set -e` plus `grep -c`, which exits 1 when it finds nothing, stopped a check script
halfway making it look complete. They are the same two shapes as `LEZIONI.md` §2.3-bis, and they must be
written down because **they were not paid for by the code: they were paid for while it was being certified**.

---

### The decisions produced

| | |
|---|---|
| `DECISIONI.md` §4.6 | the Intel encoder's capabilities are `[?]` derived from the chip generation: **this is where they get confirmed**, with `vainfo` |
| `DECISIONI.md` §4.6-ter | the GPU is chosen with a udev rule, and denying the node denies it to **the user's whole session** |
| `DECISIONI.md` §5-bis.0-ter | the Android emulator is a **work bench, not a measuring instrument** |
| `DECISIONI.md` §4.3-bis | being *headless* on GNOME is a **requirement**, not luck — the check is M2, and it starts here |

---

### What remains `[?]`

| | |
|---|---|
| ✅ ~~empty `/etc/fstab`~~ → **it is not a debt: it is a user step** | *9 Aug 2026: «quando riavvio la macchina ci penso io alla cartella `/media`».* Mounting stays manual by choice, and `banchi/00-rimetti-macchina.sh` does it in one command for whoever does not remember. ⭐ **And the real risk was not forgetting the mount** — that shows immediately, because there is nothing — **but measuring on a half-restored machine**: that is now caught by the bench, which says `GUASTO` instead of printing a zero (items 1 and 8). The protection lives in the program, as **I7** requires |
| ⚠ **the two restore scripts** | `provision-server.sh` neither calls nor names `provision-banco.sh`. Today we know; in a month only whoever was there will know |
| `[?]` **KWin's 49,67 in memory** | against the 43,3 of 8 Aug. Three known differences, none verified as the cause |
| `[?]` **Mutter's tail** | the median of the intervals is stuck at 33,3 ms over six rounds, but the maximum goes from 33,6 to 75,0. Where that tail comes from has not been looked at |
| `[?]` **the denied Radeon** | `amdgpu_cs_ctx_create2 failed (-13)`: to be understood whether it is the udev rule of `DECISIONI.md` §4.6-ter. Not blocking |
| ⏳ **the Android environment** | SDK, `adb`, Desktop AVD and the real phone: not yet touched. ⛔ *It said «servono alla sonda della **fase 2**, non prima». **Corrected on the night of 9 Aug 2026**, finding **R3.14** of the phase 1 bench review: `DECISIONI.md` §1.6 removed the Android application — so **SDK, `adb` and the emulator are no longer needed for anything** — and `PIANO.md` §1.2 moved the probe to **phase 1**, «prima di tutto». **The real phone, on the other hand, is needed, and needed earlier**: it is the measuring instrument for S2, S3a and S5. The complete census of what is missing is in §01-filo-nudo, «Le dipendenze»* |
| **the pixels-per-second budget** | `vainfo` says **which** profiles, not **how many** pixels: the number of sessions is phase 10 |
| **the emulator's HEVC decoder** | it was not possible to establish that it exposes a hardware one — and it does not matter, because no number is declared there |

---

### The adversarial review of the bench

*Requested by the user on 9 Aug 2026, **after** the phase was closed, and with a narrow mandate:
not the phase — which is closed and whose measurements will be redone a hundred times — but the **four bench
files**, which are the only thing of this phase that survives the phase.*

> «La fase 0 è stata una fase in cui si sono misurate le performance. Non sono sicuro che sia
> necessaria una review avversariale.»

⭐ **The objection was half right, and must be written down.** The adversarial review was born as a
substitute for the lost referee (`PIANO.md` §0.4): it serves to notice that client and server
share the same misunderstanding. Here there is no protocol, there are no two implementations,
there is no product — that argument **does not hold**. The other one holds, the one in `REVIEWER.md` §1: *the
bench is the first suspect*, because a defect in the bench is found by nothing **and gives confidence**.

⛔ **The tally: 22 `[R]` findings, 5 `[?]`, on a bench that had just been certified with four
checks.** And the reviewer did not receive the reasoning of whoever had written it — only the code
and the rules (`PIANO.md` §0.4, practice 1).

#### The seven things fixed at once, and they are the ones that make the bench lie silently

| # | The defect | The cure |
|---|---|---|
| 1 | ⛔ **the row mixed two populations**: damage, fence, skips and buffers counted from the first instant, frames and rhythm after the discard — and `arrivati` was not printed, so it could not be seen | the counters are updated **inside** the sample, and `arrivati` is a column: the difference **is** the warm-up |
| 2 | ⛔ **death mid-measurement**: the stream *had been* active, so the guard did not fire. Killing the compositor at the twelfth second produced ~59 fps over 5 seconds under the label of a 20-second cell | the stream state is checked **at the end**, not only at the start |
| 3 | ⛔ **`--dmabuf` could deliver memory**: the type mask always also contained MemFd, and the column stated the **requested** path. At 1080p that is 59,2 versus 43,3 | requested and obtained are compared, and it fails by declaring it (`LEZIONI.md` §1.8, corollary) |
| 4 | ⛔ **a scene with the wrong name** (`tetti` instead of `tetto`) left `pid_scena` empty — the same sentinel the `fermo` scene uses on purpose — and the guard disabled itself | a fault branch that says `GUASTO` |
| 5 | ⛔ **the scene was checked only once**, one second after start | it is watched for the whole measurement |
| 6 | ⛔ **`00-c1-kwin.sh` did not check it at all**, and `misura-wlroots` **returns 0 on every path**: the two certifications could come out green on a dead compositor | the scene watched there too; and for wlroots the verdict is built by the script, ⚠ **declaring that it is a fallback** and not a cure in the source |
| 7 | ⛔ **the versioned binary was from 8 Aug**, without the cures of the 9th: whoever cloned the project would pick up defects that this document declares closed | `banco.sh` **refuses to measure** if the source is newer than the binary — I7: the protection lives in the program |

⭐ **And the seventh proved itself**: as soon as it was written, the guard blocked the first
run with *«misura-cattura è più vecchio del suo sorgente»* — that is, it caught in three
seconds the defect that had cost the reviewer a reading of `strings`.

#### A reviewer `[?]` closed in our favour

He suspected that KWin's **49,67** in memory was a 720p capture labelled 1080p —
a sharp hypothesis, because 49,6 is exactly the 720p cell of `STUDI.md` §kde §5.7. **Refuted by a datum already
recorded**: that run had printed `formato negoziato: 1920x1080`. The `[?]` on 49,67 stays
open, but with one candidate cause fewer instead of one more.

#### What the reviewer tried to break without succeeding

It is worth as much as the findings, and must be written down: the `t_inizio` guard **holds** (no input makes it
print a row without an active stream); the new-socket detection of `00-c1-wlroots.sh`
is not fooled by GNOME, by KWin or by a surviving sway; the 15-character trap
of `pgrep -x` is not paid again in any of the four files; and `sudo` with redirected stderr does not
appear anywhere.

#### ⏳ The sixteen findings not yet cured, declared instead of forgotten

None of these produces a wrong number silently — they are false reds, imprecise labels
or noise — and they are taken up when the phase that uses them touches them:

| | |
|---|---|
| `fence_non_pronta = 0` does not distinguish «all ready» from «never asked» — on the `memoria` path it is **always** 0 | phase 8 |
| the row carries the **requested** size, not the negotiated one (which is known) | phase 8 |
| `00-c1-wlroots.sh` kills a process before validating the argument's name, and the two C1 benches take arguments in **different order** | next round |
| leftover sockets on disk make a live compositor fail (false red) | next round |
| `banco.sh` synchronises the two sides with `sleep 2.5` instead of a marker (`LEZIONI.md` §2.3-quinquies) | phase 3 |
| the warm-up starts from `PAUSED`, not from when the stream is active | phase 3 |
| a failed cell disappears from the table without leaving a trace on stdout | phase 3 |
| the expected value of `00-c1-kwin.sh` is **printed and not compared**, and it is written with a comma while the measurer prints a dot | next round |
| `prepara` skips every non-empty file: a truncated scene is never redone | phase 3 |
| between one cell and the next it kills and restarts after a fixed 1,5 s, and there is no `trap` | phase 3 |
| `banco.sh` writes `scena.log` and **does not read it**: in the twenty-cell table the §1.1 check does not appear, and the file is overwritten at every cell | phase 3 |
| plus five minor findings and the `[?]` on `quanti_fd`, on the type of the last frame and on the `pkill -x` of a real session | — |

#### ⚠ And a defect I made myself while applying the cures

I uploaded the four corrected files to the hardware with `... | tail -0` so as not to print the noise of
`scp`: `tail -0` closes the pipe at once, `scp` dies of SIGPIPE, **no file was sent** — and my
`echo "caricati"` declared it done. The next round measured with the old binary and
the numbers did not add up. It is the same shape as the two I had already written up above — `$?` after a
pipe and `set -e` with `grep -c` — at the third occurrence in a day. ⛔ **The lesson is not
«remember it»: it is that the transfer must be verified from the receiving side** (`LEZIONI.md` §1.7),
which is exactly what I did right after and which found the fault in ten seconds.

---

### The user's verdict

**9 Aug 2026**, on the numbers of this phase:

> *«Non ci sono sorprese: sappiamo che tra tutti i compositor dei 4 DE Mutter è quello che performa
> peggio non riuscendo a produrre oltre i 35 fps, il che significa che GNOME non è in grado di
> garantire 4K/60 fps, ma va bene. Non sarà adatto per il gaming ma consente comunque una
> soddisfacente esperienza desktop e multimedia.»*

⭐ **What this verdict decides, written down so that it is not reopened by distraction**: the
Mutter cap is **accepted**, and the desired target of `SPECIFICHE.md` §3.1 — 4K at 60 — remains a
goal that **is not promised on GNOME**. The guaranteed minimum (`DECISIONI.md` §2.1) is very far away
and was never in question.

⚠ **Two technical clarifications the verdict does not change, but which whoever reads this in six months must have
alongside**, or they would attribute the cap to the wrong thing:

1. ⛔ **4K has nothing to do with it.** Mutter's cap is the same at every resolution — `LEZIONI.md` §3
   question 10, *«niente fino a 4K»*. The 36 frames measured today are at **1080p**: they are not lost
   going to 4K, they are simply lost. The right sentence is «GNOME delivers ~36 frames, at any
   size», not «GNOME cannot handle 4K».
2. ⏳ **And the cap is not yet `[M]` as a limit: it is `[M]` as the current state.** The intervals
   measured today — median **33,3 ms**, minimum **16,2**, never intermediate values — are the signature of two
   clocks at 60 beating against each other, that is exactly the mechanism that `STUDI.md` §gnome §8.2 reads in the
   code. The candidate cure (**M3**: negotiate high and renegotiate only the cadence) costs **zero
   lines of product** and has not been tested. It is in `PIANO.md` phase 3.
   > ⭐ ⚠ *13 Aug 2026: **M3 has been tested and the fact holds** — monitor 120, brake 90, `[M]`
   > **61,4**. ⛔ But the mechanism written here («two clocks beating») **is wrong**, and the one
   > replacing it (a **quantisation** on the ticks) is `[R]`, not `[M]`: the «law verified
   > on 13 points» written on the afternoon of 13 Aug **fell the same evening**, because the two
   > grid cells carried `scena_sul_mio_monitor: false`. ⇒ **M3 stays half done**
   > (`STUDI.md` §gnome §13).*

⚠ The difference between the two sentences is not academic: *«Mutter does not go beyond 36»* closes the question,
*«Mutter does not go beyond 36 until someone separates the two clocks»* leaves it open at zero cost. Today
the second holds.

---

### ⛔⭐ R12-A.44 — the user half of phase 1 rested on was created by nobody

*11 Aug 2026. Found while answering a user question — «devo creare un secondo utente
sul server?» — and the interesting answer was not about the second one.*

`prova` is the user with which **B5, B6, B7 and B8** authenticate, and with which the product's PAM stack
is checked (service `remotix`, `SPECIFICHE.md` §4.2). ⛔ **No file in the repository named it.**
It had been created **by hand** on 10 Aug — `/home/prova` carries that date — and it lived **inside the
container**, not on the host: `getent passwd prova` from outside exits 2, from inside gives `1001`.

⇒ Rebuilding the container, **four of the eight certified benches** would have turned red for a
reason that is not the product's. ⭐ It is the most expensive kind of false red, because it sends you looking for the
defect in the server.

#### What there is now

`provision.sh` has a step **5-bis** that creates **both** users inside the container, in a
repeatable way, and that **verifies** that PAM can accept them — because *«the user exists»* and
*«the user authenticates»* are two facts, and the second is the one the benches rest on.

| user | uid | password | why this way |
|---|---|---|---|
| `prova` | 1001 | `parola-di-prova`, **fixed** | ⚠ **declared compromise**: that string is the default in a dozen benches, and generating it today would break them all silently. Acceptable because the user lives **inside a container** that is not exposed and does not exist on anybody's machine. ⛔ The day a test user had to exist on a real machine, it must be redone |
| `prova2` | 1002 | ⭐ **generated**, written to `/media/REMOTIX/credenziali-banchi` (0600) | **outside the repository**, and it must not get in. *Decided by the user on 11 Aug 2026.* It is generated **once** and then re-read: regenerating it at every round would mean that a bench stopped halfway cannot be repeated |

#### ⭐ And the second user serves two purposes, not one

- **B10** — `SPECIFICHE.md` §5.5: the server serves several users, and one cannot take the other's
  session. With a single user that property cannot even be tested.
- **R3.26** — the PAM stack for a user who **is not the owner of the process**. ⚠ It matters more than
  it seems: on 11 Aug B8 measured that the timing medians separate because of PAM,
  and **all** those measurements are with the owner user.

⭐ **First datum, measured at once**: `prova2` with the generated password reaches **AMMESSO** and then
**SESSIONE**, *«dopo 1080 ms — il secondo fisso c'è»*; with the wrong password it gets the answer
**`RESPINTO: 0x07 = CREDENZIALI_ERRATE`**. ⇒ The second user authenticates, and the check that says
*no* works. ⚠ The timing figure for a non-owner remains to be measured properly: this is a
single sample.

#### ⚠ What is still crooked, and must be said

⛔ **The benches take the password on the command line** (`--parola …`), so it ends up in
`ps` and in every log that captures the command. For `parola-di-prova` it is the compromise mentioned above;
⛔ **for the generated password of `prova2` it is not**, and it is the same shape cured today on `sonda/`
(R12-A.34). Whoever uses `prova2` in a bench must make it take another path.


> ### ⭐ Appendix — `banchi/prodotto/`, which lived only on the server
>
> *It was §00-ambiente, 60 lines. It comes in here on 16 Aug 2026 because
> it is phase 0 bench material, and a README in a tools folder is a
> document nobody opens. ⛔ Text intact, headings lowered by two levels.*

### `banchi/prodotto/` — what lived **only on the server**

*Recovered on 11 Aug 2026, with the code frozen, before synchronising the two trees.*

⛔ **These fourteen files existed in one place only**: `/media/REMOTIX/src/` on the server
192.168.0.2, which **is not a git tree** and has no copy anywhere. They are the work of the
night of 10 Aug — the first and only power-on of the `src/` product — and no document
names them. A wrong `tar`, or a resync with `--delete`, would have deleted them without
anyone noticing.

⚠ **They are taken as they were, without touching them.** They are not benches yet: they are the throwaway tools
of whoever powered on the server that night, and the logs that came out of them. Whoever writes the product
bench (item 1 of the 11 Aug session) redoes them in the form the project demands —
declared scene, positive control, denominator — and then these get thrown away. **Until that
moment they are the only proof that that round happened.**

---

#### ⭐ The bench exists, and it is `banchi/01-p1-prodotto.sh` — 11 Aug 2026, 04:55 UTC

*Added after the first green round. ⛔ **Nothing gets thrown away yet**, and below is the row that says
exactly how much of this folder has been replaced and how much has not.*

| tool | does `01-p1-` redo it? | |
|---|---|---|
| `avvia-server.sh` · `spegni.sh` | ✅ **yes** | the power-on, the pid, the shutdown with TERM and the check that TERM was enough live in `01-p1-dentro.sh`, with **port 7448 declared** and the files in `/srv/src/tmp/p1-*` instead of scattered in `/srv/src/` |
| `fumo.sh` | ✅ **yes, and it fixes a defect** | ⛔ `fumo.sh` has **`PORTA=${2:-7447}`**: launched without arguments it powers on **the product on the graft's port**, and `bsslserver` is what 11 benches out of 14 expect there. `01-p1-` does not take the port from an argument: 7448 is written inside |
| `check-env.sh` | ✅ **yes** | what is in the container is declared by the bench, line by line, instead of just printing it |
| `b11-fumo.py` | — | it belongs to B11, not to the product |
| ⛔ `filo.sh` | ❌ **no** | it is the **RCP handshake** with the B3 test client and the B4 referee. `01-p1-` stops before the wire, and declares it: it would authenticate, and three wrong passwords put the address out for 12 hours (B0.3) |
| ⛔ `resto.sh` | ❌ **no** | certificate rotation, administrator certificate, ban + page + unban. ⚠ **And one of its legs is already dead**: line 83 calls `remotix --ban … --sblocca <ind>`, and that option **no longer exists** since finding R12.1 — `[M]` 11 Aug 2026: it prints the explanation and exits **2**, and `resto.sh` does not look at the exit status |

⛔ **So this folder is not thrown away**: `filo.sh` and `resto.sh` remain the only trace of how
the wire and the ban are tested against the **product**, and until the benches that redo them exist,
throwing them away would remove a description without replacing it.

#### The tools

| file | what it does | date |
|---|---|---|
| `avvia-server.sh` | ⭐ **how the product was powered on**: `remotix --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta 7448 --certificati /srv/src/remotix-cert --pagina …/pagina.html --ban /srv/src/remotix-ban`, inside the container, with the pid in a file. ⛔ **Port 7448**, that is not the graft's one: the two servers can be on together | 10 Aug 23:05 |
| `spegni.sh` | shuts it down from the pid file | 10 Aug 23:07 |
| `filo.sh` (57 lines) | a wire round against the product | 10 Aug 22:58 |
| `fumo.sh` (74) | the smoke test | 10 Aug 22:52 |
| `resto.sh` (95) | the rest of the round | 10 Aug 23:00 |
| `check-env.sh` (18) | what is in the container | 8 Aug 22:20 |
| `b11-fumo.py` (45) | the B11 smoke test | 10 Aug 10:25 |

#### The logs, and they are measurements

⛔ **These are not redone: they are numbers with a date.** If a future measurement contradicts them, the
difference gets explained — not overwritten.

| file | what it contains |
|---|---|
| `b8-campioni.jsonl` (15 kB) | the samples of B8's fixed second |
| `b8-fatti.jsonl` (25 kB) | the facts of the B8 round |
| `b12-esiti.jsonl` | the outcomes of B12 |
| `01-s1b-visite.jsonl` | the visits of the seven-day clock of S1b (the verdict is of 17-18 Aug) |
| `corpo.html` · `pagina-ban.html` · `pagina-dopo.html` | ⭐ **the page body as the browser saw it**, in the three states: normal, banned, after unban. It is the only proof on disk that the ban page of §4.4-bis was looked at by a real engine |


---

<a id="01-filo-nudo"></a>

## Phase 1 — The bare wire

Opened on **9 Aug 2026** · **Rewritten on the evening of 9 Aug**, after two adversarial reviews ·
⭐ **Closed on 11 Aug 2026**, on the user's verdict — the sentence, with the scene and the log, is
at the bottom of this document

> ⛔ **This document is opened before developing, and contains the benches** (`PIANO.md` §0.1). The
> measurement tables are **empty by construction**: they fill up along the way, one row at a
> time, with the date and the scene. A document written afterwards is an account, and in an account the
> measurements are *remembered* instead of being *recorded*.

> ### ⛔ The first draft was reviewed before producing a number, and it did not hold
>
> Two adversarial reviews with two different lenses — `fasi/rapporti/R3-revisione-banco-01.md` (the
> bench as an instrument, **28 findings**) and `R4-revisione-banco-01.md` (consistency with what is
> already written, **16**). **44 findings: 38 `[R]`, 6 `[?]`, no `[M]`.** Neither of the two is green.
>
> ⭐ **It is the first of the three moments of `PIANO.md` §0.4 doing its job**: the bench is the first
> suspect, and this cost a rewrite instead of three phases of poisoned measurements.
>
> **The six cures that changed the shape of the document, not the detail:**
>
> | | |
> |---|---|
> | **the order was circular** | three probe measurements required the server that the library bench has yet to choose. ⭐ **B2 now comes first**, and the probe splits into *before the wire* and *over the wire* — R3.4, R4.3 |
> | **the check that says *no* always fell off** | of the **eleven** control tests the reports prescribe for S1a, S2 and S4 only **three** had survived, and they were all of the kind that says *yes*. Two had already been rejected by `R2` with the instruction *«curare prima di scrivere una riga di banco»* — R3.1 |
> | **rigour pointed one way only** | twelve violations towards the server, **none towards the page**, while `RCP.md` §3 is written about *«un'implementazione RCP»*. ⭐ **B11** is born — R4.1 |
> | **the devices did not exist** | six measurements out of nine require hardware that no document declares. ⭐ The **dependencies** chapter is born, before the benches — R3.14 |
> | **certification covered 4 benches out of 12** | and the two uncovered ones — B3 and B7 — are the benches of v1's two most expensive defects — R3.7, R4.6 |
> | **six things produced were looked at by nobody** | among them that **the two certificates are two**, and that the password does not end up in a log. ⭐ **B13** is born — R3.24 |
>
> ⚠ **And three cures fell outside this file**, because the discord was elsewhere: `RCP.md`
> §4.1-bis and §7.3, the negative checks in the benches of `STUDI.md` §web, and the phase 0 row that sends the
> probe to phase 2. They are listed at the bottom, under «Le cure fuori da questo documento».

---

### What it must produce

The **RCP handshake over WebTransport**, from both sides: the server in C and the page served by the
server itself. No video, no audio, no input.

**What the user sees, and judges**: opens `https://192.168.0.2:7448` in the browser, types user and
password, and the page says *«ammesso, sessione nuova, tela 1920×1080, **desktop sconosciuto**»*.
Or it says **why not**, with an understandable sentence and not a number (`RCP.md` §8.2).

> ⚠ *This row said* «`…:7447` … **desktop GNOME**» *— and the user's round of 11 Aug 2026
> refuted it on both points, with the product running in front of him.* ⛔ **7447 belongs to the graft**:
> the product is on **7448**, and whoever executed this row literally was judging the bench instead
> of the product. ⛔ **And «GNOME» is a word phase 1 cannot say without inventing it**: the graphical
> session is born in phase 2, there is no compositor to ask, and `src/rcp.c` declares it in
> writing — `SESSIONE` carries `desktop=sconosciuto`. ⇒ **What changes is the expected value, not the code**:
> it had been written before the product existed. Test and scene in
> `rapporti/GIUDIZIO-11-agosto.md`.

#### ⛔ The boundary of the phase, and the four things it produces without seeming to

*Rewritten after R4.2, R4.5, R4.8 and R4.11: the first draft declared only one of them, and the other three
would have been born without a bench.*

| | |
|---|---|
| **`SESSIONE`** | `stato` is **always `NUOVA`**. The real graphical session is born in phase 2, its life and the three clocks in phase 5. ⛔ **And «always» is verified** (B13): a `RIPRESA` branch written out of caution and never tested is precisely what this box exists to prevent |
| ⛔ **the granted canvas** | is **not** «the one requested»: it is the one requested **capped at `video.misura_massima`** if the client declared it, and in any case within the limits and parity of `RCP.md` §4.5. *Correction R4.2: the previous row contradicted a MUST, and the defect would have been born invisible here to show up in phase 2 as «the browser does not open the stream» — that is, the symptom of another cause* |
| ⭐ **session occupancy** | ⛔ phase 1 produces **half of invariant I2**, and it must be said: to answer `GIA_ATTIVA_REMOTA` the server must know that a session of that user exists with a **live** client attached. What is left for phase 5 is **the three clocks** (`DECISIONI.md` §4.5), not the occupancy. *Without this row B3 tested something no phase declared it produced — R4.5* |
| ⭐ **the capabilities the server declares in `ECCOMI`** | `RCP.md` §4.3 makes them **normative**: whoever does not declare `pcm` and `8` takes its farewell with `NIENTE_IN_COMUNE`. The phase 1 server declares **`video.codec=hevc` · `video.profondita=8,10` · `audio.codec=pcm,opus` · `appunti.testo=si`** — that is, what the product will have, not what phase 1 can already do. ⚠ **It is a declaration of intent, and it is honest only if someone verifies it**: phase 2 must prove that the negotiated codec is really the one produced, or the negotiation lies from here on. *Without this row the test client would have turned red by applying §4.3 to the letter, and whoever wrote it would have thought the mistake was his — R4.8* |
| ⛔ **the served page isolated across origins** | `SPECIFICHE.md` §11.5: **it is a product constraint**, not a bench tuning — it changes how the server serves **every** resource, and deciding it later means repackaging the page. Phase 1 is the only one in which the server acquires the craft of serving it. *It was missing entirely — R4.11* |

---

## ⛔ The dependencies: what is needed, and what is not there today

*New chapter, from finding **R3.14**. The first draft wrote nine probe rows taking as
existing devices that no project document names — and §00-ambiente declares
that environment **not touched**. An undeclared dependency is a measurement that does not get done, and this
project has already paid for it twice in one day (`weston` and the `adm`/`systemd-journal` groups).*

*Censused with the user on the night of 9 Aug 2026: **the Android phone and the DeX are there, the Apple
world is not**.*

| Needed for | What | Is it there? |
|---|---|---|
| S2, S5, S3a | ⭐ **the Android phone** with Chrome | ✅ **yes** — and it needs no configuration: you open an address |
| S3a, S5 | ⭐ a **DeX** device (the lock exists only from **Android 16 QPR1**) | ✅ **yes** — ⚠ `[?]` **to be verified that it is at least Android 16 QPR1**, or S3a measures the absence of the lock and mistakes it for a loss of shortcuts |
| ⛔ **S3a on Firefox** | **Firefox ≥ 151**: `requestFullscreen({keyboardLock})` entered the standard on 8 May 2026 and Gecko shipped it **in 151** `[S]` | ⛔ **no**: the Firefox on the machine we test from is **140.0** `[M]` 9 Aug. ⭐ *Found by rule B0.6 — note the exact version — the first round it was needed: `STUDI.md` §web §2 declares it read Gecko **151-153**, and this machine is three versions behind. Whoever measured S3a here would measure **the absence of the lock**, and would mistake it for lost shortcuts* |
| S2 | a **connected PC** for `chrome://inspect` — control C, the only channel that really answers | ✅ yes |
| S7 | GNOME session and `libei` | ✅ `banchi/00-sessione-gnome.sh`, `libei1` 1.3.901 `[M]` |
| all | the `devroot`, the test machine, the package cache | ✅ phase 0 |
| B9 | `python3-aioquic` 1.2 | ⚠ `[M]` it is there, but **that it carries client-side WebTransport is not `[M]` anywhere** (R3.21) |
| B10 | a **second user** on the server, with a password, that PAM can authenticate | ⛔ **no** — and ⛔ **it goes in `provision-server.sh`, not created by hand**, or within a day it is invisible (`LEZIONI.md` §2.5-bis) |
| S2 | **five test sequences** from `hevc_vaapi` (S2 §4.1), including the grey ramp for 10 bits | ⛔ no — they depend on the encoder, which belongs to phase 2 |
| ⛔ **S1a, B2** | a **Mac** with Safari 26.4, and an **iPhone/iPad connected to the Mac** with Web Inspector — on Safari `net-export` does not exist (S1 §4.3) | ⛔ **NO, and it cannot be worked around** |
| ⏳ S3b | a **real certificate with a domain**: behind the exception the Service Worker does not install `[R]`, so **the PWA does not exist** (R3.12) | ⛔ no — *postponed* |

> ### ⭐ Safari is not measured in this phase, and it is a decision — not a shortcoming
>
> **`DECISIONI.md` §1.8**, from the user on 9 Aug 2026: *Apple is an extra, not a goal*.
> No Mac is procured, no devices are rented, no tunnel is set up. **S1a leaves
> phase 1 and stays `[?]`.**
>
> ⛔ **And it is not «Safari is not supported»**: the code is the same for all three engines, and the
> path on Safari 26.4 is the same as the other two. We do not spend to **verify it**.
>
> The three consequences, and none is cured by writing code:
>
> | | |
> |---|---|
> | **B2 loses a third of its criterion** | *«all three engines open the session»* becomes **two out of three**, and the QUIC library is chosen **knowing about Chrome and Firefox**. ⚠ It must be written next to the choice, or in six months it will look like an informed choice |
> | ⭐ **but it blocks nothing** | `serverCertificateHashes` shipped in **Safari 26.4** `[R]`: iPhone and iPad have **the same path** as the other two. S1a decided **a convenience** — whether the fingerprint can be spared there — not whether a platform can be served (`RCP.md` §4.1-bis) |
> | ⛔ **and what remains uncovered must be told to whoever installs** | until someone tests on Safari, *«works on iPhone»* is **a deduction, not a measurement**. It is shape **E5**, and the place where it must not appear is the product documentation |
>
> ⚠ **The day a Mac were available**, S1a is done in an afternoon: the three checks are already
> written up here, and the probe page is the same.

⚠ **And §00-ambiente and `PIANO.md` §1.2 did not agree** on where the probe lives: phase 0
sent it to phase 2, the plan puts it *«prima di tutto»* in phase 1. Clarified with a dated note
in the phase 0 document.

---

## The bench

⛔ **Written before developing, and reviewed before the product** — `PIANO.md` §0.4.

### ⭐ The order, and why it is that one

*Corrected by R3.4 and R4.3: the declared order was **circular**. S1a, S6 and S4 require a server
that speaks WebTransport, that is the thing B2 builds; and B2 requires knowing that Safari can
open the session, that is the question of S1a. Whoever executed the document in the written order
stopped at the first line of the first measurement.*

| When | What | Why there |
|---|---|---|
| **1** | **the five measurements independent of the wire**: S1b · S2 · S3a · S5 · S7 | they do not touch the server: they are done right away, and S1b **must be done first because it lasts seven days** |
| **2** | ⭐ **B2 — the library bench** | it produces the **fifty-line minimal server** on which everything else rests, and closes `DECISIONI.md` §6.4 |
| **3** | **the two measurements that live on top of the minimal server**: S1a · S6 | ⚠ and if the candidate then changes, **they are redone**: a positive control done on an engine different from the product's is the form **E10** |
| **4** | the wire benches: **B3-B13** | they test the product against `RCP.md`, never against itself |
| ⏳ **postponed** | **S4** → phase 3 · **S3b** → where its real certificate will arrive | S4 is not «without product»: it wants encoding, transport and decoding — ⛔ **and a protocol line, to be decided now** (see below) |

> #### ⛔ The protocol line that S4 requires, and the window that is closing
>
> S4 §5.3 declares it: the bench mark — **the 16×16 rectangle and the command that changes it, with
> the injectable delay `N` of the decisive control** — is *«a protocol extension … it must
> be written in `RCP.md` as a **bench function**, not improvised in the test code»*.
>
> ⛔ **And `RCP.md` §9 closes the window for new types «from the first byte written onwards».** If that
> message does not go in **before** the server exists, it will go in as an exception to a rule that protects
> the implementations — that is, as the first breach, made by us, of the rule we wrote
> yesterday. **Open in `RCP.md` §12, to be closed before the first byte** (R3.4).

### B0 — The rules that apply to all benches

*New section: five different findings (R3.3, R3.8, R3.16, R3.17, R3.18, R3.23) said the same
thing in five places — that the bench does not declare what state it starts from, and that what survives between
one test and the next falsifies the following test.*

| # | The rule | Where it comes from |
|---|---|---|
| **0.1** | ⛔ **every bench declares and VERIFIES its own initial state** before starting, as `00-c1-kwin.sh` verifies that KWin's socket is no longer there. A bench that does not know what state it starts from **measures the history of the machine** | R3.16 |
| **0.2** | ⛔ **and the state that survives is more than one**: the exception granted on the page certificate *(which S1a and S1b **measure**)*, the session certificate already rotated by B3, **the session created in the previous round** *(which at less than 30 s makes the first connection of the new round get `GIA_ATTIVA_REMOTA` — red on correct code)*, the `clipboard-read` permission, and ⛔ **the ban of §4.4-bis, which since 10 Aug 2026 lives in a file and so survives even a server restart** — that is, the state that survives longest of all | R3.16 |
| **0.3** | ⛔ **isolation between benches, and since 10 Aug 2026 it is the hardest constraint of the chapter**: the attempt count is **per address**, and all benches start from the same address. B7 fails one attempt, B8 fails three, **and from then on every bench on that machine is out for twelve hours** — including B10, B11 and whoever is developing. ⚠ *The old line said «the counters are per name and per address … it is cured by changing address or **declaring the wait**»: with the ban of `DECISIONI.md` §1.9 the wait is half a day, and that cure is dead.* ⛔ **The cure is the unban command** (§4.4-bis), called between one bench and the next — ⛔ **never inside B8's round**, or B8 no longer tests anything. And every bench that calls it **declares it**, or «the ban did not trigger» and «someone removed it» look the same. ⭐ **The tool is `banchi/01-b8-sblocca.py`** — it is not a piece of B8 — and it speaks a **Unix socket `0600`**: `SBLOCCA <indirizzo>` → `TOLTO` / `NON-BANNATO`, `PING` → `PONG`. ⛔ The `PING` **is the denominator of this rule**: without it, «the ban did not trigger» and «the unban never reached anyone» again look the same. ⚠ *Since the night of 10 Aug 2026 **the two servers speak the same protocol**: before, the product had an option `remotix --sblocca IND`, that is a second process that rewrote the file while the ban lives in the memory of the serving process — **it exited with 0 saying it had worked**, and at the next ban of anyone else the removed ban **came back on disk too** (finding **R12.1** of `fasi/rapporti/R12-D-cuciture.md`, and the analysis had been written out in full in `01-b3-rcp-innesta.py` for months before the defect was born). Cured in the code the same night: `src/comando.c`.* ⛔ **And the half nobody has done remains to be done**: pointing `01-b8-sblocca.py` at the product, which today has never been tested | R3.8 |
| **0.4** | ⛔ **the expected value is compared by the bench, not by the reader**: it is printed *and* compared, and the exit status is that of the **comparison**. ⚠ And watch out for the point versus the comma: `"60"` versus `"60,0"` gives red on correct code, and it is the still-open defect of `00-c1-kwin.sh` | R3.18, R3.23 |
| **0.5** | ⛔ **after every test that must drop the connection, the server must still be there**: a new connection that gets as far as `SESSIONE`. «It always drops» is also satisfied by a server **killed by the kernel** | R3.3 |
| **0.6** | ⛔ **the exact browser version is noted**, every time. *«A result without a version, six months from now, is worth nothing»* (S1 §4.5) — and this is the chapter that ages in months | R3.16 |
| **0.7** | ⛔ **the two sides synchronise with markers, not with `sleep`** — and the precedent in the house is **not** an example to copy: phase 0's `banco.sh` still has its `sleep 2.5` | R3-§4.9 |

---

### Group 1 — The five measurements independent of the wire

⛔ **All on the real device, never on a convenience browser** (`DECISIONI.md` §5-bis.0-ter).
⭐ **And every line carries the precise reference to the place where the procedure lives** — ⛔ **which for three of
them is not a report, and it must be said**: `S1a`, `S1b`, `S2`, `S3a`, `S3b` and `S4` were born in `STUDI.md` §web
§7 and **do not appear in any of the four reports**, where the tests are named in four
incompatible ways and two reports use `P1…Pn` for things of opposite nature (R3.28). ⛔ **`S5`, `S6` and
`S7` instead were not born there**: `[M]` 11 Aug 2026, `grep -cE '\bS5\b|\bS6\b|\bS7\b' web.md` →
**0**, with the positive control alongside (the other six labels appear **24** times in the same
file). They were born **in this document**, from the questions of `SPECIFICHE.md` §6.1-bis (S5),
`RCP.md` §5.3 (S6) and `RCP.md` §7.3 (S7), and refer **there** because no report exists that
contains them.

> ⚠ *This line said* «the labels `S1a…S7` **were born in `STUDI.md` §web §7**» *— and §7 of `STUDI.md` §web
> lists **six** of them, not nine. ⛔ It was the line that **establishes the convention for references**, and the two
> lines following it in this same chapter contradicted it: S5 refers to
> `SPECIFICHE.md §6.1-bis`, S7 to `RCP.md §7.3` — that is, not to a report. Corrected on 11 Aug 2026,
> finding **R12C.10**. ⭐ And it costs little and is worth it: three measurements out of five in Group 1 now have a
> provenance, that is whoever runs them knows which reading they were born from and which question they close.*

⛔ **And since the night of 10 Aug the outcomes have a single place where they live**:
`web/rapporti/S-esiti-sonda.md` — the scene, the time in UTC, the
logs, and **the recount of 11 Aug that says which numbers have a provenance on disk and
which do not**. ⚠ *Until 11 Aug that report was named by **none** of the ten documents
(finding **R12C.15**): the only place where the numbers of that night lived was not reachable
by any reading path, and the only way to know it existed was to open a folder of
reports at random.*

#### S1b — how long the exception lasts on Chrome  ·  ⏳ **STARTED on 10 Aug 2026** · `banchi/01-s1b-eccezione.sh`

> ⚠ *This line referred to* `S1 §4.2 P5`. ⛔ **P5 is not this test**: it is the test of the *secure
> context* (Service Worker, keyboard lock, clipboard, pointer lock, `isSecureContext`), and **in S1 there
> is no bench test on duration** — the seven days are **only source read** (S1
> §3.1), and the only persistence put on a bench is Safari's (S1 §4.3). ⇒ *There was no
> procedure to follow: there was one to write.* Whoever opened S1 §4.2 P5 to run S1b found
> five API calls and no procedure, and the most natural explanation is *«I must have
> misread»*. Corrected on 11 Aug 2026, finding **R12C.9** — and it is the third reference of this form
> the project pays for (R11.2, R11.18).

| | |
|---|---|
| **measured** | after how many days the warning reappears on the page |
| **expected** | **7 days** — `[S]`→`[R]` from `kCertErrorBypassExpirationInSeconds = 604800`. ⚠ **The mark promotion is declared here**: `STUDI.md` §web §8 still kept it `[?]`, and the two lines of `STUDI.md` §web contradicted each other (R4.14) |
| ⛔ **the control** | **the fingerprint of the PAGE certificate, read at the start and at the end, must be the same.** Without it, a certificate regenerated by a restart makes one write «the exception lasted four days» and the sentence that will be told to the user is born wrong (R3.15) |
| ⚠ **the calendar** | it is the only measurement that requires **seven days of real time**, and the phase does not close before. If one speeds it up by moving the machine's clock, ⭐ the control becomes *«at six days the exception is still there»* — which is a real control |
| ⏳ **day 0 taken, the clock is running** | `[M]` **2026-08-10T21:10:01Z** — **Chrome 151.0.7922.108**, persistent profile in `~/.remotix-s1b/profilo`, fake screen `Xvfb :77 1280x1024x24`, site `https://192.168.0.2:7452`, certificate **ECDSA P-256 at 3650 days** with SAN `IP Address:192.168.0.2` (⛔ **not** `localhost`, which in Chrome has a reserved lane, and ⛔ **not** in private browsing). Log `banchi/01-s1b-stato.jsonl`. **The verdict is due 17-18 Aug 2026** |
| ⛔ **and a number that does NOT hold** | Chrome recorded the expiry **2026-08-17T21:09:47.889Z** (`[M]` on the raw value `13431474587889370` µs since 1601, which is on disk; the conversion is recomputed by hand and **declared** as such). ⚠ *The report wrote «that is **exactly 604 800 s** from the grant», twice: between the two numbers it published there are **604 786,889 s**. **13,111 s** were missing, and «exactly» was false in both places — findings **A26** and **R12.6**.* ⛔ **No rounding and no re-measuring** (redoing the «start» round would reset the seven-day clock): that it is 604 800 s from the **click** has gone back to `[?]`, because **nobody recorded the instant of the click** |
| ⭐ **four controls, and the fourth was born later** | the fingerprint read **from the wire** must be that of day 0 · a **new** profile must see the warning · the site must be alive · ⭐ **the reading channel must be certified** (finding **A27**, 11 Aug): the verdict rested on `ssh` + a `grep` that, if broken, answered **NO** — and the control that says *no* read **the same channel**, so it declared itself passed on its own. The round that came out of it printed *«at N days the exception is NO longer there: this is the number of S1b»* — ⛔ **the measurement's number, in green, from a mute tool**, and on a seven-day clock someone would have noticed **a week later** |
| ⛔ **what can break the clock** | regenerating `/media/REMOTIX/s1b-certificato/s1b-pagina.pem`, deleting `~/.remotix-s1b/`, or the server's date dropping. The first two are seen by the fingerprint control; ⚠ **the third is not** |

#### S2 — HEVC Main10 in hardware, on the real phone  ·  `S2 §4.2 misure 1,2,4 · §4.4 controlli A,B,C`

| | |
|---|---|
| **measured** | throughput at saturation (4K60 Main10), **CPU canary** in a worker, **decay over ten minutes** |
| ⛔ **the expected value is NOT «`[S]` yes since Chrome 108»** | that `[S]` concerns **support in WebCodecs**, not the hardware: writing it as the expected value of a *hardware* measurement puts **E1 in the expectation box**, and indirect tests are read with indulgence when the expected value is already written. **The expected value is `[?]`** (R3.13, R4.13) |
| ⛔ **the three controls, not one** | **A**: VP9 `prefer-software` **must be declared software** · **B**: VP9 `prefer-hardware` **must be declared hardware** — *it had been dropped, and it is the one that says no* · **C**: ⭐ **`is_software_codec` read via `chrome://inspect`** |
| ⭐ **and the direct channel exists** | on Android, `media_codec_video_decoder.cc` logs `is_software_codec` with the name coming from `MediaCodec.getName()`. **The browser knows and does not answer *from JavaScript*** — but the bench is not JavaScript: the bench is whoever looks (`LEZIONI.md` §1.11 rule 2). Giving it up for three indirect tests, on the primary use, was an undeclared choice (R3.13) |
| ⛔ **the outcomes are three** | ≥ 90 fps ⇒ hardware · ≤ 30 ⇒ software · **in between: verdict suspended**. The first draft had two, where the report foresees three |
| ⚠ | on iPhone the direct channel does not exist, and there the three indirect ones remain the only way |

#### S3a — the keyboard, in the three states  ·  `S3 §4.2 (quattro controlli) · §4.3 (gruppi A-E) · §4.4`

⛔ **The question is not «does it arrive?» but «does it arrive *and only that*?»** — the states are three: *delivered* ·
**delivered *and* reserved** · *not delivered*. The second is the worst (`SPECIFICHE.md` §7.3-bis,
O8).

| | |
|---|---|
| ⛔ **the defect that inverted the measurement** | `Ctrl+W` on DeX: the page receives the `keydown` **and** the browser closes the tab. If the log lives in the page, **the closing takes the log away**: the bench writes «not delivered», that is **the opposite state** — and declares the dangerous case harmless (R3.11) |
| ⛔ **the cure, already written in the report** | S3 §4.3 orders the eleven combinations **from least risky to most risky, one at a time**, with `Ctrl+T`, `Ctrl+N` and `Ctrl+W` **last and with the log already copied off the device**. The one line that makes the measurement possible had been dropped |
| ⛔ **the four controls, before every session and on every engine** | that a **bare** keystroke arrives *(without it, every «it did not arrive» is ambiguous between «the browser kept it» and «the bench was deaf»)*; that a combination **with modifiers** arrives; that the **outgoing clipboard** works; ⛔ and that full screen was **not** entered with `F11` — because with `F11` **the lock does not exist and does not say so**, and all the tests that follow are worth nothing |
| ⚠ **and «the session»** | in phase 1 **there is no input channel**: here the receiver is **the page**. The previous wording sent whoever writes the bench looking for something that does not exist |

#### S5 — the canvas the client declares  ·  `SPECIFICHE.md §6.1-bis · DECISIONI.md §5.0-quater`

| | |
|---|---|
| **measured** | the number the page would declare in `ATTACCA`, at zoom **100 %** and **150 %**; and what `screen` answers **on DeX** |
| ⛔ **the earlier control was red on correct code** | it said *«the two numbers must differ»*. But the **correct** canvas is the screen in physical pixels, and the reasoning written here was: *«`screen.width` drops by a third, `devicePixelRatio` rises by a half, **the product stays**»*. A well-written page gave **1920 and 1920** ⇒ red, and whoever read it would have gone and broken the page until the number moved — that is, **written** the defect that `DECISIONI.md` §5.0-quater wanted to avoid (R3.10) |
| ⭐ **the correct control** | the canvas declared at 100 % and at 150 % **must be the same**, and **must match the physical resolution read outside the browser**, in the device settings. Two different tools on the same fact |
| ⛔⛔ **MEASURED, and the reasoning above is FALSE on Chrome** | `[M]` **10 Aug 2026**, log `banchi/01-s5-esiti.jsonl` (two identical rounds, 23:13 and 23:14), screen **Xvfb 1920×1080×24** with `xdpyinfo` confirming it from outside. **Chrome 151.0.7922.108** at zoom 150 %: `screen` stays **1920×1080** and `dpr` rises to 1,5 ⇒ canvas **2880×1620**, **50 % larger** than the one that exists. **Firefox 140.13.0esr** at 150 %: `screen` drops to **1280×720** ⇒ canvas **1920×1080**, invariant. ⛔ *«The product stays»* **stays on one engine out of two**, and the formula of `SPECIFICHE.md` §6.1-bis does not hold on Chrome. ⚠ Corrected on 11 Aug 2026, finding **R12C.8** — and the defect is **the product's, not the bench's** |
| ⭐ **and it is the correct control that found it** | the old control (*«the two numbers must differ»*) would have been **green on Chrome and red on Firefox**: it would have rewarded the broken engine. It is the demonstration, on a real case, that the cure of R3.10 was worth it |
| ⚠ **and half of S5 is not measured** | the **DeX** was not there. *«The laptop's Chrome does it»* says nothing about the phone's Chrome — form **E10**. The page is the same (`01-s5-pagina.html`): the day the DeX is there, one opens that address and reads the line |
| ⛔ **and the third question cannot be closed with a measurement** | *«can the rounding produce an odd number?»* — on a device one observes a number; if it is even **it does not follow that odd ones do not exist** (`LEZIONI.md` §1.3). The protection goes **in the program**, where **I7** wants it: the page rounds down to even. The measurement can only find a positive |

#### S7 — which way the wheel turns  ·  `RCP.md §7.3`

| | |
|---|---|
| **measured** | `+120` is injected with `libei` into a GNOME session (`banchi/00-sessione-gnome.sh`) and one watches which way the page goes |
| ⭐ **the control** | **`-120`** is also injected: if the page goes the same way, one is not measuring the sign. ⭐ *It is the best-written control of the first draft, and it stays* |
| ⛔ **the control that was missing** | it is redone **with `natural-scroll` in both states**: if the sign changes, the number that would end up in `RCP.md` §7.3 is **the sign of a gsetting of the test session**, and the symptom for the user is *«the wheel goes backwards»* on half of the installations. Form **E11** (R3.25) |
| ⭐⭐ **MEASURED — and the server must INVERT the vertical axis** | `[M]` **10 Aug 2026, 20:59:27→20:59:57 UTC**. `ei_device_scroll_discrete(0, **+120**)` → the `wheel` event carries **`deltaY = +114`** and the page **goes down**, that is towards the end of the document; with **−120**, `−114` and it goes up. `RCP.md` §7.3 fixes the other half — *the client sends `+120` because the user turned **up*** — so ⛔ **the two conventions are opposite and the server inverts the sign**. Injecting the value as is, the remote screen would scroll backwards for **every** user. ⇒ **`RCP.md` §7.3 is closed on 11 Aug 2026**, finding **R12C.7** |
| **the scene, in full** | test machine **192.168.0.2**; GNOME session without a monitor (`banchi/00-sessione-gnome.sh`), `gnome-shell --headless --no-x11 --virtual-monitor 1920x1080`, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**; the page in **Firefox 140.13.0esr** in `--kiosk`, `dpr` 1, document positioned 8 000 px from the edge. Log: `banchi/01-s7-esiti.jsonl`, two rounds (`7sd0u7jv`, `oq7jqrdv`) |
| ⚠ **and the controls are not all worth the same** | `[M]` **in the log**: the opposite sign, and the two tools that agree (`deltaY` and `scrollY`). ⚠ **Halfway**: `natural-scroll` in both states — the two rounds are there and give the same sign, ⛔ **but which round was which state is not in the log**, the label was only on screen. ⛔ **Not recoverable**: that `ei_device_scroll_delta` has the same direction — seen, not delivered |
| `[?]` **and the question that remains** | §7.3 binds **five** desktops and the measurement is on **Mutter**. If `libei` normalises, the number holds everywhere; if the compositor normalises, the KDE phase (the 11th) will find a different sign on KWin and will not know whether to correct the protocol or the server. ⛔ *«Not closed»* and *«not measured»* are two different states, and this is the first: the bench is **re-runnable on KWin without changing one line of the page**. ⚠ Phase 0 measured **three** families in one afternoon: here the same question has only one answer |
| ⚠ **and a number that does NOT go into the protocol** | one notch (120 units) is worth **114 pixels** on Firefox+Mutter, that is three lines. It is the conversion factor of **that pair**, not an RCP constant: it is noted and put in no formula |
| ⚠ **and the lesson cited was the wrong one** | v1's wheel bench cost **a log string searched for badly** (`LEZIONI.md` §2.3), not a table with the wrong sign. By citing the wrong lesson **one loses it at the point where it would apply** (R4.15) — the sentence is from `RCP.md` §7.3, and it is corrected there |

---

### Group 2 — B2, the library bench: which QUIC gets as far as WebTransport

⛔ **It comes before S1a and S6, and it is the thing that closes `DECISIONI.md` §6.4** — with a bench in front,
not on paper. The criterion changed on 9 Aug: it is not enough for the library to speak QUIC, it must
carry **HTTP/3 and WebTransport on the server side**, plus a **TCP** listener for the page.

**The test**: a minimal server — fifty lines, to be thrown away — that accepts a
WebTransport session on `/rcp/1`, opened by **a real browser**, with the fingerprint published in the page.

> #### ⭐ The census of the night of 9 Aug, before writing a line
>
> *Point 0 of the recipe, and it changed the question.* ⛔ **Neither of the two original candidates
> carries WebTransport on the server side**: they provide the foundations — extended CONNECT, datagram, capsule — and
> not the layer above. ⭐ **And two candidates turned up that were not on the list**, one of
> which (`lsquic`, in C) **has a WebTransport server behind a build flag**.
>
> The complete census, with the marks, is in `DECISIONI.md` §6.4 — it is not copied here.
> ⛔ **And it is all `[S]` and `[R]`: read, not measured.** It serves only to decide **for whom it is worth
> writing the fifty lines**.

| Candidate | On the hardware | What is tested |
|---|---|---|
| ⭐ **`ngtcp2` + `nghttp3`** (MIT, C) | ✅ **built from source** — `ngtcp2` 16.11.0, `nghttp3` 1.18.90, on the same BoringSSL `[M]`, **and their `bsslserver` runs** | ⭐ **passes the SNI criterion** `[M]` 10 Aug. It remains to measure how much the WebTransport layer on top weighs |
| ⭐ **`quiche`** (BSD-2, C API) | ✅ **built**, but at **0.28.0**: 0.29.3 requires `rustc` **1.88** and Trixie has **1.85** `[M]` | ⭐ **passes the SNI criterion** `[M]` 10 Aug. ⚠ It carries a **toolchain** cost, not a QUIC one — `DECISIONI.md` §6.4 |
| ⛔ **`lsquic`** (C) | ✅ compiled, **and the glue written** (333 lines) `[M]` | ⛔ **ELIMINATED**: in HTTP/3 mode it requires **SNI** to find the certificate, and whoever connects to an **IP address** does not send it. It is the product's primary case — `DECISIONI.md` §6.4 |
| ⚠ **`libwtf`** (C on MsQuic) | ⛔ nothing | *last in line*: it brings in a second QUIC stack, and has a **licence that contradicts itself** |

**The expected value, which the first draft left empty** (R3.23):

| | |
|---|---|
| **passes** | the session opens on **Chrome and Firefox**, and the page receives a byte from the server. ⛔ **There were three engines**, and Safari drops out because there is no Mac (see «The dependencies»): the library choice is made **knowing two out of three**, and this line exists so that six months from now it does not look like an informed choice |
| ⛔ **and five properties are verified here**, because they belong to the library and no other bench looks at them | **datagrams enabled** on the HTTP/3 connection (§2.2) · **no 0-RTT** (§2.3) · **migration not disabled** (§2.3) · **`max_idle_timeout` = 30 s imposed by the server** (§2.2) · **`allowPooling` set to `false`** (§4.1-bis) |
| ⛔ **and one that B3 needs** | that the bench **can change `max_idle_timeout`**: without it, B3's 30-second line cannot be told apart from the transport (R3.19). It is the kind of thing to be decided **when choosing the library**, not when writing B3 |
| **the selection criterion** | ⚠ *«the number of lines left to us»* is not an expected value: one counts the **measured glue**, candidate by candidate, and the number is written down. Without it, the choice is made by judgement |

⛔ **The symptom of 0-RTT switched on does not exist**: `CREDENZIALI` can be replayed, and no functional
bench ever sees it. QUIC libraries offer it **by default**.

---

### Group 3 — The two measurements that live on top of the minimal server

#### S1a — does the exception on Safari cover WebTransport?  ·  `S1 §4.2 P1, controlli P2-P4`

| | |
|---|---|
| **measured** | on **Safari macOS and iOS separately**: a WebTransport session behind the certificate exception alone |
| ⛔ **the three controls, not one** | **P2** the connection **with the published fingerprint must succeed** — *same browser, same page, same round* · **P3** ⛔ **with the fingerprint wrong by one byte it must FAIL** · **P4** with a **30-day** certificate it must fail **because of duration** |
| ⛔ **why P3 is the one that was missing** | without it, a page that watches **the wrong promise** — it considers the construction of the object «successful» instead of waiting for `ready` — makes **even** the test with the mangled fingerprint succeed, and the bench writes a false `[M]` *«on Safari the exception covers WebTransport»* **against two `[R]` read in the Chromium and Gecko code** (R3.1). S1 §4.4: *«only with P2 green and **P3 red** does the result of P1 mean anything»* |
| ⚠ **what it decides** | **a convenience, not a platform**: `serverCertificateHashes` has also shipped in **Safari 26.4** (`STUDI.md` §web §3.1) — *the first draft cited `RCP.md` §4.1-bis in support, and §4.1-bis said the opposite because it had not been updated. Cured (R4.4)* |

#### S6 — how much a datagram really carries  ·  `RCP.md §5.3`

| | |
|---|---|
| ⛔ **it is not a quantity of the engine** | it is decided by **the path** — the smallest MTU between the two ends minus the headers — not by the browser. The engine only decides what the API **declares**, which is the thing the line itself said not to believe: attributing it to the engine is **E2**, two different measurements under the same label (R3.22) |
| ⛔ **so the path is declared next to the number** | as phase 0 declares the scene next to every frames-per-second figure. And it is measured on the **worst path one intends to serve** — LTE, or a VPN at MTU 1400 — **not on the comfortable one** |
| **the control** | one sends a datagram of that exact size and **verifies that it arrives at the other side**, not that the API accepts it |
| ⭐ **and if the number must be a protocol cap, it is not measured at all** | one takes the **minimum guaranteed by QUIC**, which is what the **972 bytes** of PCM already do. Measuring on the LAN and raising the cap means sending audio the real user does not receive — ⛔ and PCM is **the positive control of Opus**: one would fall back on a road that does not exist |

---

### The wire benches

#### B3 — the handshake on TWO connections, and a third with the key changed

⛔ In v1 a shared certificate killed the server **at the second** connection, and a
single-connection test **stays green forever** (`LEZIONI.md` §2.1).

| | Expected |
|---|---|
| **1st connection** | complete handshake up to `SESSIONE` |
| **2nd after the first is closed** | ⛔ **identical to the first.** If the server dies, or if the second fails where the first passed, the defect is **its own** |
| **2nd while the first is alive** | `CONGEDO(GIA_ATTIVA_REMOTA = 0x0F)` towards **the one arriving**, verified **from the receiving side**, and ⛔ **one checks which of the two survives** |
| **the 2nd after the 1st goes silent** | ⛔ **35 seconds with `max_idle_timeout` raised to 120** — *not 30 seconds at the default timeout*: as it was, a server **with no notion whatsoever of a detached session** stayed green, because QUIC closed the first one by itself and the structure tied to the connection was freed. That is, the bench blessed **the violation of I4** (R3.19) |
| **3rd with the session certificate rotated by hand** | the page **fetches the current fingerprint from the server again** and succeeds (`RCP.md` §4.1-bis) |
| ⚠ **and what this does NOT prove** | the **automatic rotation** at fourteen days. Changing the key by hand proves that the page can fetch the fingerprint again; that the server regenerates **before expiry** remains without a bench, and its symptom — *«it no longer connects and does not say why»* — arrives two weeks after delivery |

#### B4 — the wire validator

A **third program** that reads a recording and says **which byte** does not conform to `RCP.md`
§6. The only mechanical arbiter we will have.

| | |
|---|---|
| **the six faulty recordings** | length inconsistent with the type (§6.1) · invalid UTF-8 (§6.0) · repeated capability name (§4.3) · high byte outside the five channels (§2.5) · message in the wrong state — `ATTACCA` before `CREDENZIALI` (§1) · ⭐ **correct body but aligned**, the padding byte that «makes the numbers add up» (§6.0) |
| ⛔ **the seventh, which was missing: a CONFORMING recording, which the validator MUST accept** | without it, «6 out of 6» is compatible with a validator that **rejects everything**: it is enough to read `lunghezza` as `u16` instead of `u32` — two characters — and from that moment the arbiter declares **every** trace non-conforming, with the diagnosis pointing at `RCP.md` §6.1 while the defect is in the tool (R3.5) |
| ⛔ **and one verifies WHICH byte, not just that it is red** | on the recording with the padding, a validator that does not know §6.0 does not see the extra byte: it reads the **next message** askew and declares **that one** non-conforming. Correct red, wrong byte — and on a real trace it sends the diagnosis to read the wrong message |

> #### ⛔ The recording format must be decided **before** writing the recorder
>
> *Finding R3.6, and the first draft saw the problem without choosing: two rules
> contradicting each other, and none saying which wins.*
>
> | What the recorder does | What happens |
> |---|---|
> | records the bytes **as they passed** | ⛔ the password in clear in a file, forbidden by `RCP.md` §4.4 *«at any level»* |
> | **replaces** the password and leaves the `lunghezza` | the body no longer has the declared length ⇒ **perpetual false red** on every trace with a successful handshake |
> | replaces **and rewrites the length** | the recording is no longer the bytes that passed: the validator validates a document the bench has rewritten — **it is no longer an arbiter** |
>
> ⭐ **The fourth road, which is chosen now**: one records **the true length** and **a fingerprint**
> of the body for the secret fields only, and the **recording format declares that that body is
> obscured**. The length adds up, the validator knows it must not look inside, the password is not there.
>
> ⛔ **And the format is a single one, written once**: two recorders — one in the C, one in the page
> — that write the same fact in two ways are exactly the silent defect against which `RCP.md`
> §0 was written.

#### B5 — the violation tests: strictness towards the server

⛔ The connection **must drop every time**, with the right reason, verified from the receiving side —
⛔ **and the server must still be there afterwards** (B0.5).

| What is sent | Expected |
|---|---|
| an unknown message type | `ERRORE_PROTOCOLLO` `0x0B` |
| a length inconsistent with the type (too long and too short) | `ERRORE_PROTOCOLLO` |
| ⛔ **an announced `lunghezza` of 4 GiB** | `ERRORE_PROTOCOLLO` **and the server alive**: §6.1 forbids allocating before checking, and a server killed by the kernel *«drops the connection» all the same* — taking with it **all the other users' sessions** (R3.3) |
| ⛔ a message that **announces more than 1 MiB** (§6.1) | `ERRORE_PROTOCOLLO` |
| `CREDENZIALI` with an **empty** user, and with an **empty** password | `ERRORE_PROTOCOLLO`, ⛔ and **neither of the two counters** of §4.4-bis moves |
| user of 257 bytes, password of 1025 | `ERRORE_PROTOCOLLO` (§4.4) |
| `CIAO(versione = 2)` on `/rcp/1` | `VERSIONE_INCOMPATIBILE` `0x0A` |
| a WebTransport session on a different path | **404** |
| a **bidirectional** stream beyond the first, from the client | `ERRORE_PROTOCOLLO` |
| `0x00` (control) on a **unidirectional** stream; `0x04` (audio) on a **stream** | `ERRORE_PROTOCOLLO` (§2.5) |
| a channel in the **wrong direction** — `0x03` from the client | `ERRORE_PROTOCOLLO` |
| a capability name with **capitals**, or of 65 bytes; an **empty value**; a value of 257 bytes | `ERRORE_PROTOCOLLO` (§4.3) |
| `video.misura_massima` declared **by the server** | `ERRORE_PROTOCOLLO` |
| `video.codec = vp9` alone | `NIENTE_IN_COMUNE` `0x09` — *it did not make a typo, it has nothing to talk about* |
| `video.codec = hevc,vp9` | ⭐ **`hevc` is read and one proceeds**, and the discard **is written in the log** |
| a `CIAO` **without `pcm`**, and one **without `8`** | `NIENTE_IN_COMUNE` (§4.3) |
| canvas `1921×1080`, `319×240`, `7682×4320` | `ERRORE_PROTOCOLLO` (§4.5) |
| ⛔ **view `300×801`, and view `1×1`** | ⛔ **MUST PASS**: §7.1 says the view does not have the canvas's constraints — *«any size from 1×1 up is legal, odd included»*. Whoever writes `ATTACCA` in C writes **one** `valida_misura()` and calls it four times: it is the natural thing to do, and it produces a server that closes the session because the user narrowed the window. On a phone with factor 2,75 the view is **odd almost always** (R4.10) |
| malformed `disposizione` / well-formed but unknown | ⛔ **two different faults**: `ERRORE_PROTOCOLLO` · `SESSIONE_NON_SERVIBILE` `0x0E` ⛔ **with the detail in the body** (§8.2) |
| ⭐ **`BANCO_MARCA` with the function off** | ⛔ **`BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — not a silence, not a close** (§7.5). ⚠ It is the **default** state of every server, so it is tested here even though the mark will be used by phase 3: a silence would leave phase 3's bench waiting forever, and the symptom would be «the bench has hung» |
| **`BANCO_MARCA` with `ritardo_ms = 20000`** | `BANCO_ESITO(RIFIUTATA, RITARDO_FUORI_LIMITI)` — ⛔ **not** `ERRORE_PROTOCOLLO`: dropping the session on the bench being calibrated is the bad idea that §7.1 avoids for out-of-range sizes |
| ⚠ **and the codec choice** | `RCP.md` §4.3 makes it **mandatory in the server log**: one verifies that it is there |

⚠ **The close is verified at the three points of §3.1** — log, `CONGEDO`, session code —
⛔ **with the second conditional**: §3.1 says *«if the control channel is still usable»*, and a
bench that requires all three always **gives red on correct code** when the violation arrives on
a unidirectional stream (R3.3).

#### B11 — ⭐ the violation tests aimed at the PAGE

*A new bench, from finding **R4.1**, and it is the biggest hole in the first draft: twelve violations
aimed at the server and **none** aimed at the client. `RCP.md` §3 is written about «an RCP implementation», and
§9 has an **explicit MUST for the client**. In a project that lost `mstsc` and writes `RCP.md`
precisely so as not to trust two programs by the same hand, **a client never put to the test is the
hole where the referee should be**.*

A **deliberately faulty** server — a few lines, to be thrown away — sends the page:

| What the faulty server sends | What the page MUST do |
|---|---|
| ⛔ `ECCOMI(versione = 2)` to a `CIAO(versione = 1)` | `CONGEDO(VERSIONE_INCOMPATIBILE)` — §9 imposes it on the **client** with a MUST, and accepting it silently is *«l'indulgenza che §3 vieta»* |
| a `SESSIONE` with an **odd** canvas, or out of bounds | refuses instead of adapting |
| a `CONGEDO` with reason **`0x00`** | `ERRORE_PROTOCOLLO`: §3.1 forbids code zero |
| a **bidirectional stream opened by the server** | `ERRORE_PROTOCOLLO` (§2.5) |
| an unknown message type on the control channel | `ERRORE_PROTOCOLLO` |
| an **unknown** capability in `ECCOMI` | ⛔ **ignore it and carry on** — it is exception 1 of §3, ⛔ **and write it in the log** |
| `video.misura_massima` in `ECCOMI` (wrong side) | `ERRORE_PROTOCOLLO` |
| a `FIN` on the control channel | ⛔ the session **is over**: the page no longer sends on any channel (§4.2) |
| `RESPINTO` **followed by** `CONGEDO` | ⛔ the second is a violation (§4.4) |
| after `RESPINTO`, the page **must not retry** on the same connection | §4.4 |
| a `SESSIONE` with `desktop = kde` while the hardware is GNOME | ⛔ the page **does not change behaviour**: §4.5 forbids it, and the field is for diagnosis |
| ⚠ **and an application heartbeat** | §2.2 **forbids** it: we check that the page does not send one, and does not wait for one |

⛔ **And the page, when it closes, closes the way §3.1 says**: log, `CONGEDO`, **and the application
error code in the closing of the WebTransport session** — which is the point that
an implementation can leave behind while staying compliant with the letter of an earlier version
of the text.

#### B6 — the handshake timings

A connection is opened and **kept silent**, for each of the three caps of `RCP.md` §4.6.

| From | To | Expected |
|---|---|---|
| ⭐ **opening of the CONTROL CHANNEL** (not «TLS finished», and not the opening of the session — see below) | `CIAO` | **5 s**, then `TEMPO_SCADUTO` `0x0D` |
| `ECCOMI` | `CREDENZIALI` | **60 s** |
| `AMMESSO` | `ATTACCA` | **10 s** |

⛔ **The check that tells the two faults apart, and it is the best-built one in the document**: if the server
does not keep the connection alive with **transport PINGs**, at the thirtieth second QUIC's idle
timeout fires. **Look at the reason**: `TEMPO_SCADUTO` at 60 s is the server doing its
job; a death at 30 s **without a reason** is the missing PING. *R3 looked for a third case that
would produce a death at 30 s with a reason and did not find one: §3.1 forbids code 0 and requires a
reason on every close.*

> #### ⭐ R3.27 is CLOSED, and B6 gave TWO answers — 10-11 Aug 2026
>
> ⚠ *This box said* «`[?]` … *Da misurare; se confermato, `RCP.md` §4.6 cambia di una
> parola»* — *and the measurement had been taken while the box stayed `[?]`. The «Measured» cell of
> B6 at the bottom of this document was empty, and the three numbers lived only in the `README.md`, which
> by convention summarises and does not decide. Closed on 11 Aug 2026, findings **R12C.11** and
> **R12-A.25**.*
>
> **The question was**: *«TLS handshake finished» is not an instant the two sides share.* In
> WebTransport the HTTP/3 connection and the **session** are two separate things, and between the two instants
> at least one network round trip passes — the browser may have established the connection long before the
> page calls the API. ⛔ And the worst case: a second session on a reused connection
> would start **with the budget already spent**.
>
> ⭐ **FIRST ANSWER — the stopwatch starts from the opening of the CONTROL CHANNEL**, and these are not two
> words for the same thing: neither the end of TLS nor the opening of the **session**. It is the instant the
> server actually observes, and it is what the code does (the RCP session is born when the channel opens,
> and the cap is counted from there). ⇒ **`RCP.md` §4.6 line 1 changed by one word**, on 11 Aug 2026.
> B6 says so with two purpose-built cases — `ciao-senza-controllo` and `ciao-sessione-tardiva` — and
> does **not** deliver it as a server red: it has its own outcome, **3**, which means *«the wire
> behaves as the code says, and the document says something else»*.
>
> ⛔ **SECOND ANSWER — and curing the word is NOT ENOUGH.** If the stopwatch starts from the opening of the
> channel, whoever opens the WebTransport **session** and **never opens the channel** has **no
> cap** on them at all: it stays there, alive and with no deadline. It is exactly the connection that *«tiene un posto e non
> lo dichiara a nessuno»*, that is the first line of §4.6 — **which survived the cure**. §4.6 has no
> line for that state: the table starts at *«`CIAO` received»*, and before the `CIAO` there is a state
> in which the server counts nothing.
> ⚠ Only QUIC's idle timeout covers it — **30 seconds of silence** — and whoever keeps the
> session open by writing on another stream is not silent, so it **never** expires.
> ⛔ **What cap to give it, and from which instant, is an open question and not an oversight**: `DECISIONI.md`
> §7.17, ❓, with the two readings and the concrete case. A bench that had printed **a single line**
> for the two answers would have delivered the easy half.
>
> ⚠ **And B6's three numbers — 5,0 · 60,1 · 10,0 s — have no log.** They run, and the output goes to the
> screen: no `.jsonl` of B6 exists, so the scene of that round cannot be reconstructed and the
> numbers cannot be re-verified. They sit at the bottom of this document with what is known about them
> **and with what is not known**.

#### B7 — the farewell, verified from the receiving side

⛔ **Never from the log of the sender**: in v1, for **three phases**, the server wrote «congedo il
client» while the client wrote «errore di rete» (`LEZIONI.md` §1.7).

⛔ **The denominator is fifteen, and the ones that can be provoked in this phase are SEVEN** — `CHIUSO_DALL_UTENTE`,
`VERSIONE_INCOMPATIBILE`, `NIENTE_IN_COMUNE`, `ERRORE_PROTOCOLLO`, `TEMPO_SCADUTO`,
`SESSIONE_NON_SERVIBILE`, `GIA_ATTIVA_REMOTA`. For each one we verify the `CONGEDO` **and** the code
in the close.

> ⚠ *This line said* «Per ciascuno degli **otto** motivi che questa fase sa produrre … `SERVER_IN_CHIUSURA`»
> *and further down «le **otto** frasi devono essere distinte». ⛔ It was false in both senses, and the
> bench had **measured and written it** — `banchi/01-b7-congedo.py`, table `ESCLUSI`, entry `0x0C`:*
> «il server della fase 1 non ha un percorso di spegnimento: `RCP_SERVER_IN_CHIUSURA` è dichiarato in
> `rcp.h` e non compare in nessuna riga di `rcp.c`. ⚠ MISURATO col grep, non supposto — **e
> contraddice §01-filo-nudo B7**». *Corrected on 11 Aug 2026, finding **R12C.6**.*
>
> ⛔ **And the true denominator is FIFTEEN, not eight**: §8.2 has fifteen reasons. Writing «8 out of 8»
> by choosing the eight you know how to provoke is true **by construction**, and it is the emptiest
> form of green there is. The **eight excluded** sit in `ESCLUSI` with the reason for each, and
> `certifica_denominatore()` checks that 7 + 8 = 15 instead of trusting it: `0x02` and `0x03` are session
> clocks (phase 5) · `0x04` and `0x05` need a local graphical session (phase 2) · `0x06`
> needs the encoding capability (phase 3) · `0x07` and `0x08` **do not travel in a `CONGEDO`** but in
> `RESPINTO` (§4.4), and provoking `0x08` would ban the bench's address (B0.3) · `0x0C` for the
> missing shutdown path.
>
> ⭐ **And `0x0C` changed subject on the night of 10 Aug, and it is the first place where the two
> servers diverge visibly**: **the product** now has a shutdown path —
> `src/main.c` bids everyone farewell with `SERVER_IN_CHIUSURA` before exiting — while **the graft**, which is
> what B7 switches on, does not (`grep`: zero occurrences in `01-b3-rcp-innesta.py`). ⛔ So the
> provocable ones stay **seven against the target B7 measures**, and become **eight the day
> B7 is pointed at the product**. The number to write next to an outcome is that of the target
> that was switched on.

| | |
|---|---|
| ⛔ **«tante su tante» is not enough, and the first draft stopped there** | a `switch` with the default branch — `mostra("Errore " + codice)` — gives a non-empty string for **every** reason, and so the count always adds up. The user reads *«Errore 14»* for `SESSIONE_NON_SERVIBILE`, which §8.2 forbids with a ⛔ and an almost identical example (R3.20) |
| ⭐ **the two criteria that make the line measurable** | the sentences must be **distinct from each other** — ⛔ **all fifteen**, not only the seven provocable ones: the client builds the sentence from the code, so it can be read without provoking the reason — and ⛔ **none must contain the reason's number** nor «errore» followed by a digit. A two-line `grep` |
| ⚠ **and «the bench looks at the screen» is not executable** | either the DOM is read — the only thing an automated test can do — **or it is the user** (I8), and then the line goes into **judgement**, not into a table with a «tante su tante». Declared, so that nobody reads it as already covered |
| ⚠ **the two reasons that do NOT travel in a `CONGEDO`** | `CREDENZIALI_ERRATE` and `TROPPI_TENTATIVI` sit in `RESPINTO` (§4.4, finding R1.18): a bench looking for them in a `CONGEDO` **would fail by construction** |
| ⛔ **the `dettaglio` is not shown** | it is for the log (§8.2) |

#### B8 — the fixed second, and the address ban

> ⛔ **Rewritten on 10 Aug 2026, after the user replaced the form of the rate limiting**
> (`DECISIONI.md` §1.9): three failed authentications from the same address ⛔ **within a window
> of 5 minutes**, and that address is out for **12 hours**. Gone with the old rule are the doubling of the window, the
> expiry after 30 minutes of quiet and **the per-username counter**; ⭐ **and gone is the check that
> held this bench in place** — *«four failed · one successful · four more»* is no longer
> executable, because after the third failure no fifth attempt exists.
>
> ⚠ *And the red of 10 Aug must be reread under the new rule before investigating it: the fifth attempt
> — the one with the good credentials — had received `CREDENZIALI_ERRATE` `0x07` and **not**
> `TROPPI_TENTATIVI` `0x08`. §4.4-bis refuses **without querying PAM**, so it has no way of saying
> «wrong»: the reason on the wire accuses **the bench's leg**, not the limiter. The check is
> rewritten from scratch anyway, and the half hour is spent on the new one.*

⭐ **It is a bench that sees two properties nobody else sees**, and a regression that removed them would
make nothing fail.

**The fixed second** — unchanged, the rule did not touch it:

| | |
|---|---|
| ⛔ **the criterion is NOT «≥ 1 s», and it is this bench's most important cure** | `pam_authenticate(); sleep(1); rispondi();` gives **1,001 · 1,050 · 1,300 s** in the three cases: **three green lines**, and the distinction §4.4 forbids writing in the reason can be read with the stopwatch **exactly as before**. The bench that declares itself *«the only one that sees this property»* did not see it (R3.2) |
| ⭐ **the right criterion has a different form, not a different threshold** | ⛔ **the medians of the three cases differ by less than the measurement noise** — many samples per case, not one. With one sample the fifty milliseconds separating «non-existent user» from «wrong password» are not even visible. **Expected: ≥ 1 s in every sample, and the three medians indistinguishable** |
| ⛔ **and samples now cost something** | three per address, then the ban. The medians need **many** samples per case, so the bench must **vary the source address** or unban between one block and the next — ⛔ **and declare which of the two it does**, because they change what the measurement is measuring |
| ⚠ **and the `[?]` this bench has already found** | `[M]` 10 Aug: median **2636 ms** on the refused ones, where §4.4-bis wants ~1000. ⛔ **PAM governs the timings, not us**, and until that delay is constant the fixed second does not hide what it claims to hide. The ban does **not** close this `[?]` |

**The ban** — new, and it replaces all the limiter lines:

> ⛔ **THE FIVE-MINUTE WINDOW, which this section did not name.**
>
> ⚠ *The box above and the table that follows said* «tre autenticazioni fallite
> **consecutive** dallo stesso indirizzo», *with no window — and «consecutive» was the user's **first**
> wording, tightened the same day by a **third** sentence:* «i 3 tentativi falliti
> devono avvenire **entro i 5 minuti** per far scattare il ban» *(`DECISIONI.md` §1.9). The window
> was in `DECISIONI.md`, in `RCP.md` §4.4-bis, in `SPECIFICHE.md` §4.2 and in the code
> (`#define FINESTRA 300000u`) — and it was missing in the **two** documents from which the bench is written.
> Corrected on 11 Aug 2026, finding **R12C.5**.*
>
> ⛔ **Why it bites on the bench and not on paper**: the two rules give **opposite outcomes on the same
> input**. Three failures at 0:00, 4:00 and 8:00 are *consecutive* ⇒ banned according to the old
> line, and **outside the window** ⇒ not banned according to the code. A bench written from here that spaced
> the three attempts would give **red on the correct code**, which is the form of `LEZIONI.md` §2.3.
> ⚠ And the reason it happened is the one the `README.md` forbids: the decision was **copied** into
> four documents instead of referenced, and the four copies were not equal.
>
> ⚠ **The window slides**: one looks at the time of the **last three** failures, one does not restart from the
> first. Anchoring it to the first, three failures at 0:00 · 4:59 · 5:01 would restart the count from
> one, and whoever tries at a pace just slower than the window would **never** be stopped.
> ⇒ **The decision lives in `DECISIONI.md` §1.9 and is not copied here**: this is its consequence on the
> bench.

| | Expected |
|---|---|
| ⛔ three failed authentications from the same address, **within 5 minutes** | the first three answer `RESPINTO(CREDENZIALI_ERRATE)`, each **not before one second** |
| ⭐ **the fourth check that says *no*, and it is new: OUTSIDE the window the ban does NOT fire** | three failures spaced more than 5 minutes apart ⇒ **no ban**, and the fourth attempt with the right password **gets in**. ⛔ Without it, «the ban fires at the fourth» is compatible with a server that does not look at the clock, and the line of `DECISIONI.md` §1.9 that protects *«chi sbaglia a digitare ogni tanto»* is proven by nobody |
| ⛔ **the fourth attempt, with the RIGHT password** | ⛔ **refused all the same**, and the page **says so**: `TROPPI_TENTATIVI`. ⭐ *It is the line that tells a ban from a counter, and it is also the symptom the user will see — «l'ho scritta giusta e non mi fa entrare» — so it is intended and must be tested, not avoided* |
| ⛔ **and the three usernames MUST be different** | ⚠ With the same name three times, a server that still had the old form's **per-name** counter would give green: the bench would test the wrong rule. It is the same form with which **B5** found the counter keyed on the port |
| ⭐ **the check that says *no*, first**: **another** address | gets in **immediately**, with the good credentials. Without it, «the fourth is refused» is compatible with a server that has stopped working |
| ⭐ **the check that says *no*, second**: the reset | **two** failed · **one successful** · **two** failed ⇒ the third failure does **not** ban. If success did not reset, the second block would already have fired. ⚠ *It is the check of R3.9 in the form the new rule makes executable: before, it needed a fifth attempt that no longer exists* |
| ⭐ **the check that says *no*, third**: persistence | ban, **restart the server**, and the address **is still banned**. ⛔ Without it, the ban lives in memory and a package update hands three attempts to anyone — it is invariant **I7** |
| **what the user sees** | ⛔ the **page loads** and says the attempts are exhausted (§4.4-bis). The DOM is read, as for B7's eight sentences: a bench does not look at a screen |
| **and the tab already open** | the WebTransport session is refused with `TROPPI_TENTATIVI` in the close code, verified **from the receiving side** |
| **the unban** | the command removes the ban, **writes it in the log**, and the address is let back in. ⛔ **This line is tested at the end**, not at the beginning: an unban called within the round makes everything else pass by construction (B0.3) |

⛔ **And `TROPPI_TENTATIVI` does not travel in a `CONGEDO`, it travels in `RESPINTO`** (§4.4, finding R1.18):
a bench looking for it in a farewell would fail by construction, and whoever writes it would think
they had got it wrong themselves.

#### B9 — the test client: the second reader

⭐ A few hundred lines, **in a language different from the server and the page**, written
by reading `RCP.md`.

| | |
|---|---|
| ⛔ **the separation must be a MECHANISM, not a rule** | the first draft wrote *«whoever writes it does not look at the C nor at the page»*, that is it entrusted **the only external referee left** to a memory. It is **I7 in reverse**, and it is the form this project paid for three days ago: *«la lezione era già scritta, la cura è rimasta una nota in un documento»* (R3.21) |
| ⭐ **the mechanism, and it costs little** | whoever writes the test client **receives `RCP.md` and its references, and not the tree of the server and the page**. And this is **declared here**, so that the day the test client agrees with the server we know whether that agreement is worth anything |
| ⛔ **a dependency to verify first**, and it is B2's criterion not reapplied | that **`python3-aioquic` 1.2 brings client-side WebTransport is not `[M]` anywhere**. If it does not, the test client does not exist — that is, the referee falls — and we would notice after writing the server |
| ⚠ **the most valuable outcome is not «passes»** | it is **every point where whoever writes it had to choose** because `RCP.md` allowed two readings. Those points go into «what did NOT work», and they are defects **of the document** |

#### B10 — the second user: the defect inherited from `autenticazione.c`

⛔ The bench authenticates a user **different** from the one that owns the server process.
`autenticazione_utente_atteso()` refuses anyone who is not the owner of the process: it was right
in v1, **it contradicts the multi-tenancy** of `SPECIFICHE.md` §5.5.

| | |
|---|---|
| ⛔ **«does not get in» has four causes, and the bench named one** | *(1)* the guard is still there — **the defect**; *(2)* the per-address counter is in its window (B0.3); *(3)* the PAM stack does not allow the process to verify the password of **another** user; *(4)* the second user does not exist or has no password. Whoever reads that red believing the old line goes looking in the wrong place — `LEZIONI.md` §1.6 (R3.26) |
| ⛔ **who owns the process must be declared** | the bench defined itself as *«a user different from the one that owns the process»* **without saying who that is**, while `SPECIFICHE.md` §5.5 wants it to be **a system user** |
| ⭐ **the check that costs ten seconds** | before believing the red, verify that the same password **works outside the server**: `pamtester` on the same PAM service. If it fails there too, **you are not measuring the server** |
| **expected** | the user `prova` — created by provisioning, not by hand — completes the handshake up to `SESSIONE` |

> #### ⭐⭐ THE BENCH HAS EXISTED SINCE 11 AUG 2026, EVENING — and it certified itself in the same round
>
> *It was the only one of the twelve **never tested**, and the reason was that it did not exist: `banchi/01-b10-secondo-utente.py`
> and `banchi/01-b10-lancia.sh`. ⭐ The bench **imports** `01-b3-cliente.py` as a module instead of
> copying it: it measures RCP with the second reader, and the password does not pass through any `argv`.*
>
> | | |
> |---|---|
> | ⭐ **the expected is measured** | **`prova2`** — from provisioning, not by hand — reaches `SESSIONE` on the **PRODUCT**: `AMMESSO` at **1001-1059 ms** (the fixed second of §4.4-bis), whole handshake **1213-1261 ms**. `[M]` **11 Aug 2026, 13:08 UTC**, NIC-OS, port **7491**, binary md5 `9dcb9657…`. Log `banchi/b10-esiti-prodotto.jsonl` |
> | ⛔ **who owns the process is DECLARED** | **`root`, effective uid 0** — read from `/proc/<pid>/status`, not assumed — that is **a system user**, as §5.5 wants. ⭐ And the bench checks that it is **not vacuous**: if the server ran as the test user it exits **2**, *«I could not measure»*, instead of printing a green that means nothing |
> | ⛔ **the four causes are told apart, and with three observations** | *(1)* **the guard** — the server refuses **and its log has no line from `autenticazione.c`**: PAM was not even queried; *(2)* **the per-address counter** — the reason on the wire is `TROPPI_TENTATIVI` `0x08`, and then the bench **unbans, declaring it, and retries**, or (2) would cover (1); *(3)* **the PAM stack** — `pamtester` fails with the same password; *(4)* **the user** — `getent passwd` and `getent shadow` |
> | ⭐ **the check that costs ten seconds, and its negative** | `pamtester remotix prova2 authenticate` **succeeds** — ⛔ on the **`remotix`** service, not `login` — and with the wrong password it **fails**: without the second, the first would be worth nothing |
> | ⭐⭐ **and the `[?]` R3.26 is MEASURED** | from an **unprivileged** user, verifying the password of **another** user **fails**; from **root it succeeds**. ⇒ **the PAM stack judges another user only if the process is privileged**. The server today runs as root and succeeds; ⛔ a system service that **dropped privileges** would see cause (3), and the symptom would again be *«wrong credentials»* — it is the question phase 2 carries with it |
> | ⭐ **two users, not one** | after the refusal, **`prova`** reaches `SESSIONE`: it is at once **B0.5** (the server is still there) and §5.5 (two different users, **neither of them** owner of the process) |
> | ⛔ **the generated password does not pass through any command line** | the compromise the `README.md` declared **not accepted** is closed: the password is read from `credenziali-banchi`, written with a **builtin** into a `0600` file, arrives as `--parola-file`, and a `trap` deletes it. ⚠ A copy remains on disk for the duration of the round, and it is declared |
>
> ⭐ **CERTIFIED — `0 → 1 → 0`** `[M]` 11 Aug, **15:09 UTC**. The fault **puts back v1's
> guard** — `getpwuid(geteuid())` and the comparison with the name, **before** `pam_start` — on a **whole
> copy** of the product tree, ⛔ **never on `src/remotix`**: the other benches were measuring it
> in those same minutes, and for a quarter of an hour they would have had a lying server
> under their feet. Mark **`CAUSA-1-GUARDIA-PRE-PAM`: 2 in the faulty round, 0 in the two healthy rounds**.
>
> ⛔ **And the fault in the catalogue broke nothing.** The hook `autenticazione_utente_atteso` was
> pointed at a file where it appears **only inside a comment**: the substitute stuck the
> mark next to it and the compiled code stayed **identical byte for byte**. ⚠ **It is the third time in one day**
> that a comment hook makes one believe something has been broken — after B5 and B3 — and it is the form that
> costs the most, because the round *looks* like a successful certification.
>
> ⚠ **B10 does not go through `01-b12-lancia.sh`**: its fault is rebuilt with
> `GEMELLO=nessuno <copia>/costruisci.sh`, while `attrezzi-misura-marca.sh` can only do
> `ninja … bsslserver`, that is **the graft**. Until `gira()` learns to build the **product**,
> certification is done from the bench's launcher — and it is the same gap as point 4 of the list.
>
> ⛔ **And what B10 does NOT test**: the case of the user who **owns** the process. `root` has no
> known password in the container, so *«with the guard put back only root gets in»* is
> **deduced, not measured**. ⚠ And B10 is tested only against the **product**, never against the graft.

#### B12 — certification: how these benches earn belief

⛔ `PIANO.md` §0.3 rule 4. *The first draft built **four** faults for **twelve** benches, and
the two uncovered were the benches of v1's two costliest defects (R3.7, R4.6).*

| # | The test | What it proves |
|---|---|---|
| **C1** | ⛔ **a hand-built fault FOR EACH BENCH**, and there are twelve | the bench **must turn red**. Among the new ones: **B3** — the per-connection structure is not freed (v1's defect); **B7** — ⛔ **the sending of the `CONGEDO` is removed and the code in the close is kept**: if B7 stays green it is doing a `\|\|` where a `&&` is needed, and **the bench was born not to notice**; **B4** — the validator that reads `lunghezza` as `u16`; **B9** — the test client that has read the C |
| **C2** | ⛔ **the connection is broken in THREE ways and THREE different diagnoses are demanded**: nobody listening · **UDP 7447 filtered with TCP answering** · fingerprint not current. *The first draft tested only the first — and the second is the concrete case with which `R2` showed that the project's first positive check was blind* (R3.17) | a bench that confuses them will say «the server does not answer» the day the certificate has expired |
| **C3** | everything is run **twice in a row**, without resetting anything | ⚠ and what survives is **five things, not one**: see B0.2 |
| **C4** | the two sides synchronise with **markers** | `LEZIONI.md` §2.3-quinquies |
| **C5** | ⛔ **each bench compares its own expected**, and the exit status is that of the comparison | ⚠ *The first draft cited `00-c1-kwin.sh` as the model: that file **prints and does not compare**, and it is a defect declared open in phase 0. Cited now as **the defect not to repeat*** (R3.18) |

> #### ⭐ THE ROUND OF 11 AUG, AFTERNOON — and the first thing to say is that this morning's count had already expired
>
> ⛔ **None of the three certificates was valid any more.** The log carries, next to each certification,
> the fingerprint of the `rcp.c` it was made with: **`d839839f…`**. Today `rcp.c` is **`cb7af778…`** —
> the cures of 10-11 Aug changed it. ⇒ *«3 out of 12»* was **3 out of 12 on code that no longer
> exists**, and that is exactly what the log says when you read it instead of reading its total.
>
> ⚠ ⛔ **And the proof above is written in two alphabets, that is it cannot be redone** — found on the evening of 11
> Aug. `d839839f…` is a **truncated sha256** (the log writes it in full); `cb7af778…` is an
> **md5**. The `sha256` of `rcp.c` today is **`84411b9c…`**. ⇒ The **conclusion holds** — the code
> really changed, `d839839f…` → `84411b9c…` — but **the printed comparison sets two different
> functions side by side**, and whoever redid it tomorrow would find two numbers that have nothing to do with each other and would not
> know whether they had got it wrong. ⭐ *A fingerprint without the name of the function is the same thing as a
> number without a unit of measurement.*
>
> | Bench | Today | How |
> |---|---|---|
> | **B4** | ⭐ **certified** | `0 → 1 → 0`, mark «⛔ atteso il byte» |
> | **C2** | ⭐ **certified** | `0 → 1 → 0`, mark «IRRAGGIUNGIBILE» |
> | **B9** | ⭐ **certified** | `0 → 3 → 0`, mark «il testo è cambiato sotto il banco». ⭐ **But first it found a real defect, and ours**: the healthy round exited **3**, because entry **L6** cited the old line 1 of `RCP.md` §4.6 — the one that started from the end of TLS — and **we corrected it ourselves** on 11 Aug on B6's measurement. ⛔ No other bench would have noticed: the others would have become **greener**, not less. The `[?]` R3.27 is now logged as **DECIDED**, which is not «vanished» |
> | **B7** | ⭐ **certified** | `0 → 1 → 0`, mark «il motivo nel `CONGEDO` sul canale: assente» — ⛔ and the reservation of 10 Aug (*«non-discriminating mark, 37 occurrences»*) **is closed**: today's mark does not appear in the healthy round |
> | **B6** | ⭐ **certified — and it had never been tested** | `0 → 1 → 0`, mark «⭐ nessuna caduta», that is the line that only a **fallen** `-presto` case can produce. The fault takes `TETTO_CIAO` from 5000 to 500 ms: ⭐ *the half of the requirement nobody writes is «not before»* |
> | ⭐ **B5** | ⭐ **certified — and it had never been tested** | `0 → 1 → 0`, mark «§3.1 punto 3 su «capacita-ripetuta»». ⛔ The fault in the catalogue **broke nothing**: the hook was a *comment* string and the substitute stuck the mark next to it — the compiled code stayed identical byte for byte. Redone on the **branch**: `if (ripetuto)` switched off, `congeda()` never called |
> | ⛔ **B8** | ⛔ **tested and NOT certified**, and the reason has changed — *then **certified on the evening of the same day**, see the end of the section* | see the box below |
> | ⭐ **B3** | ⭐ **certified — and it had never been tested** | `0 → 2 → 0`, mark «`CONGEDO invece di SESSIONE: motivo 0x0f = GIA_ATTIVA_REMOTA`». ⛔ The hook in the catalogue had **two** spaces of indentation where the file has **four**: it appeared **zero** times, and the fault would not have been grafted. ⭐ The symptom with the fault is v1's to the letter: the first connection goes through, the second is refused because the first's slot was not freed |
> | ⭐ **B2** | ⭐ **certified — and it found a real defect before letting itself be certified** | `0 → 1 → 0`, mark «`- credito uni DISPONIBILE a RCP all'apertura`». See the box |
> | ⭐ **B11** | ⭐ **certified by its OWN round** | **CONFORME, 0 points** against the faulty server; **NON-CONFORME, 9 points** against the healthy one — the check that says *no*. ⚠ Written reservation: **one engine only**. See the box |
> | **B13** | ⛔ **not certifiable, and the reason has a name** | see the box below |
>
> ⇒ ⭐ **9 certified out of 12 on today's code**, against **3 out of 12 on code that no longer exists**.
> ⚠ There remain **two tested and not certified** — **B8** and **B13**, both on gaps with a name,
> not on whims of the tool — and **one never tested**, **B10**. ⛔ None of the three is «clean».
>
> ⛔ **And this line carried «5» for half a day while the log said 8** — R12-A.49.
> Two updates of this file had come to nothing **silently**, because a text substitution
> does not complain when it does not find its target, and the script said «done» all the same. ⭐ It is the form «nobody
> looks at the denominator», applied to a document instead of a bench: now every
> substitution is verified, and whoever does not find the anchor **stops**.
>
> ⚠ **And the number depends on where you ask for it — R12-A.36.** The log lived in **two copies**,
> one per machine, and neither knew about the other: the server gave «B9 NOT certified»
> while on the laptop B9 had been certified for an hour. ⭐ Merged (the file is the versioned one,
> `banchi/01-b12-registro.jsonl`, and the server's copy is now a reflection of it). ⛔ But even merged, the
> server says **4 out of 12** and the laptop **5 out of 12**, and ⭐ **both are right**: on the server
> `RCP.md` is not there, so B9's certification cannot be *re-verified* there — and the tool
> writes *«it cannot be said whether it holds today»* instead of rounding it to «certified». ⇒ The number is
> **5**, and one must say **where** it is read.
> ⚠ And the two that remain testable right away are **B5** and **B8**, both stuck on the **missing
> mark**; **B2** costs a whole rebuild; **B3** and **B11** do not have the mark;
> **B10** does not even have the bench.
>
> ##### ⭐⭐ `01-b0-terreno.sh` — the check that looks UNDER the benches
>
> *Born on 11 Aug 2026, finding **R12-A.46**. It does not move the count by one point, and it protects all of them.*
>
> ⛔ **Twice on the same day a bench was green on ground that was not what we
> believed**, and in both cases the bench had no reason to notice: the RCP graft
> vanished from `examples/` (**R12-A.45**) and the user `prova` that nobody created
> (**R12-A.44**). ⚠ In the first case **B2's certification passed all the same** — its probe
> reads the QUIC parameters and knows nothing of RCP. ⭐ **I caught it by chance**, while testing something
> else: without that coincidence it would sit in the log, dated, and wrong in a way nobody
> would find again.
>
> ⇒ It runs **before** every certification round and looks at **14 things**: the two grafts in their place
> in both files that contend for them · the three files B3 copies into `examples/` · that
> `examples/rcp.c` is **identical** to `rcp/rcp.c` · that no B12 or B11 fault has been left
> on · ⭐ and that **the binary is newer than all the sources it declares**. If it does not hold, B12
> **does not certify and does not write in the log**.
>
> ⭐ **And it had itself told *no* three times before being believed**: with a B12 fault left
> on → red; with a piece of the graft removed → red; and ⭐ **the third I had not prepared** —
> my own test round had left `rcp.c` newer than the binary, that is *healthy source and
> old binary*, trap **R12-A.6** in person. The check found it on its own.
>
> ⚠ **What it does not prove**: that the server is *correct*. It proves that it is **the declared one** —
> that is, that the benches look in the right place. A server can pass all 14 and be full of
> defects: those are the benches' job.
>
> ⛔ And the first draft got it wrong **in the same form cured that morning on S1b** (A31): `grep
> -c` exits **1** when it finds nothing — which is the answer «zero», not an error — and the `|| printf
> '?'` stuck a `?` after the zero already printed. **Five false reds in one go, inside the
> file that exists to prevent them.**

> ##### ⛔⭐ Three false reds, all produced by B12 itself — and they are the part that counts
>
> **R12-A.31 — B12 was certifying where it could not.** The launcher warned *«B9 and B4 are certified
> where their files are»* and then launched them anyway. `[M]`: on the server **`RCP.md` does not exist** —
> benches arrive there, not documents — B9 exited **4** and the log wrote **«B9 NOT
> certified»**. ⛔ It is **the opposite form of the false green**, and it costs the same: a healthy bench branded
> red sends people looking for a defect that does not exist, and the log carries it along with a date.
> ⭐ Cure: `--provabile` checks whether the files the certification rests on are there, and the launcher
> **refuses** instead of measuring. *«I cannot test it here»* and *«I tested it and it does not pass»* are two
> facts.
>
> **R12-A.32 — B6 was certifiable, and the objection in the catalogue did not hold.** It said the fault
> cannot be grafted because *«`01-b6-lancia.sh` re-copies the source at every round»*. ⭐ Both
> halves of the objection talk about the **launcher**, and **B12 does not use it**: it calls the bench's
> program. Added the command line, with the caps **read** from the compiled source instead of written by
> hand. ⚠ And it must be said what this certification does **not** cover: it certifies `01-b6-tetti.py`, not the
> source/binary comparison that sits in the launcher.
>
> **R12-A.33 — `--bersaglio` became mandatory and the callers were left behind. Three times
> in two days.** On 10 Aug on `01-b6-lancia.sh` and `01-b3-quarto-giro.sh`; today on
> `01-b12-lancia.sh`, which called B7 **without `--bersaglio`** and with a `--sorgente` that no longer
> exists: the round wrote **«B7 NOT certified»** on a healthy bench.
>
> ⭐ **Hence a new bench: `banchi/01-b0-chiamate.py`** — *does whoever calls a bench pass it what
> the bench demands?* It reads the `add_argument` calls with the AST, resolves the shell variables defined in the
> file, and distinguishes **three** outcomes: approved · broken · **UNKNOWN** (a variable that could
> hide the name of an option). It immediately found **R12-A.33-bis**: `01-b8-lancia.sh` called
> the stopwatch without `--bersaglio` or `--porta`, so the step *«what I expect, before
> measuring»* had for days been printing **an argparse usage message** — and made nothing fail.
>
> ⛔ **And writing it taught four things, all measured, all on the same theme:**
> · it accused **21** *example* lines inside the explanations. ⭐ A check that shouts on the false is not
>   ignored less than one that keeps quiet: it is ignored **together with its true ones**;
> · a filter too narrow made the `python3 -u` calls vanish **silently** — the ones seen
>   went from **83 to 22** and the count just looked cleaner. ⛔ Coverage that drops
>   without saying so is a bench that stops looking, and it shows **only from the denominator**;
> · *«there is a `$` ⇒ unknown»* made **26 lines out of 34** unknown, ⛔ including the one that had just
>   broken B7. The right question is not «is there a variable», it is **«can that variable hide the
>   name of an option?»**;
> · ⭐⭐ and the most instructive: merging the options of the shared module I had taken the **allowed** ones and
>   not the **demanded** ones. Result: the line for B6 I had just written — **without
>   `--bersaglio`** — the check declared **approved**, and the certification round
>   wrote «B6 NOT certified» on a mistake of mine that the tool born to find it had looked at and
>   promoted. ⛔ **Widening the mesh to silence the false ones takes away the true ones in the same
>   move**, and it does not show, because the count of reds goes down — which is precisely what
>   progress looks like.
>
> ⚠ And the three surviving accusations **I actually launched** instead of deducing them: two were false (B7 has
> an `--elenco` shortcut before `parse_args`) and one true. Curing all three would have broken two
> working calls to silence my own tool.
>
> ##### ⭐⭐ B11: certified — and the defect was a RACE, not a divergence
>
> ⚠ It was not «never tested»: it was **never launched**. And it must be launched **from the machine of whoever is watching**, not
> from the server — `01-b11-lancia.sh` looks for `fondamenta/strumenti/sshpw.py`, which is not on the server. Launched from
> there it dies before applying any fault (verified: zero marks in the sources and in the binary,
> port 7447 free).
>
> ⛔ **At the first round a single point did not pass**: against the faulty server, `respinto-non-riprovare`
> returned **`canale-rotto`** where the expected says **`muta`**. ⭐ **And the page was right**:
> telling a `FIN` from a `RESET_STREAM` is the cure of finding R6.12, and the server in that case
> **sends no `FIN`** — it closes the *session* with `CLOSE_WEBTRANSPORT_SESSION`.
>
> ⭐⭐ **But the real cause was another, and by widening the expected I would never have found it.** The page
> did not even reach the `RESPINTO` branch: the server sends `RESPINTO` and **closes right
> behind it**, and the close **races** against the page's reader. ⇒ The verdict depended on who
> won the race.
>
> ⛔ **And the cure was already written in the file, for the twin case.** `respinto-poi-congedo` carries
> this comment: *«La chiusura di §3.1 partirebbe subito dietro al messaggio, e correrebbe contro
> la risposta della pagina… un banco che cambia verdetto fra due giri identici non misura la pagina:
> misura il carico della macchina»*. ⇒ Same cure, same place: after `RESPINTO` the faulty server
> **stays silent**, and the one who closes will be the page.
>
> ⚠ **And it is not widening the expected**: the expected stays `muta`, and the case can still say no — if the
> page retried, the extra bytes would be seen by the **server log**, which is the witness that
> case has always declared (§8.1).
>
> ⭐ **Outcome**: **CONFORME, 0 points** against the faulty server; **NON-CONFORME, 9 points** against
> the healthy one, in 35 seconds. ⚠ Reservation written in the log: **one engine only** — Chrome has not
> looked at it, and with one engine only the second path of §3.1 cannot be seen.
>
> ⭐ **And B12 learned to judge it — R12-A.48.** The healthy/faulty/re-healthy model does not
> apply to it: its «healthy» round **must be red**, because it is the check that says *no*. `giudica()`
> now has a **`proprio-giro`** step that demands **both halves, explicit** — ⛔ a round that
> carried only *«the fault is green»* certifies nothing, because it would be compatible with a
> page that declares anything conformant.

> ##### ⛔⭐ B13: the password in an address — and the bench had been right since yesterday
>
> B13 is not certified because **its subject really is broken**, and that is the right rule: it is left
> NOT CERTIFIED instead of widening the expected result until it fits. Today the defect has a name — **finding
> R12-A.34**.
>
> `B13.2` — *«la parola d'ordine compare in 1 registri su 1288»* — pointed at
> `sonda/racc.log`. ⛔ It was not a stale log to delete: **`sonda/lancia.sh` passed the
> credentials in the query of the address** (`&utente=prova&parola=…`), and the query is part of the
> **HTTP request line**, which every server logs as a matter of course.
>
> ⚠ And the same page, twenty lines further down, printed *«CREDENZIALI mandate (la parola non compare
> in nessun registro)»*: a sentence that contradicted itself in the file next door.
>
> ⛔ **And the defect was wider than the log**: the password was also in the saved session of
> **two Firefox profiles** (`prof-ammesso`, `prof-respinto`), because the address went through the
> history.
>
> ⭐ **Cure**: the credentials travel in the **fragment** (`#`), which the browser **does not send to the
> server** — so it enters no HTTP log, neither ours nor that of a proxy in between. ⛔ And the
> second half, without which the cure would have been a fiction: `lancia.sh` **printed the address**
> on the terminal, and the terminal of a round ends up in a file like everything else — now it prints it
> masked.
>
> ⚠ **What the cure does not close, said here and not elsewhere**: the fragment stays in the browser's **history**.
> For a bench with a test password that is fine; ⛔ **a product page must not
> take the password from any part of the address**.
>
> ⛔ **And the dirty logs were NOT deleted**: doing it before verifying the cure
> would mean turning B13 green **by throwing away the evidence**. They are thrown away the day a new round of the
> probe produces clean ones. ⚠ `B13.4` also remains open (*«qualcuno ascolta in TCP ma la pagina
> non si carica»*): B13 is not certified until both pass.
>
> ##### ⭐⭐ THE EVENING OF 11 AUGUST: the cure holds, the logs are thrown away, and **B13 is certified**
>
> ⭐ **The new round of the probe verified it** `[M]` **11 Aug 2026, 12:54:33Z-12:54:53Z**, on
> **NIC-OS**, against the **PRODUCT** on `192.168.0.2:7481` (collector on `127.0.0.1:7482`,
> **Firefox 140.13.0esr**): `AMMESSO` and `RIFIUTATO`, **8 files produced**, ⛔ **zero logs with the
> password inside**. Only the two **sources** still contain it — and that is what `B13.2` declares it does
> not call red.
>
> ⛔ **And the new round found that the cure was written and not done.** `sonda-rcp.html` promised
> *«il profilo lo si butta a fine giro (`lancia.sh`)»*, and `lancia.sh` threw it away at the **start**:
> the one from the last round stayed on disk. ⚠ **And the first two cures did not hold, and it is
> measured**: profile deleted at **12:49:54**, `recovery.jsonlz4` reappeared at **12:50:10**
> (2223 bytes, the password inside) — Firefox was still alive; then, with `setsid` + `kill -- -$p`,
> reappeared at **12:51:31**, because *«il gruppo è morto»* answered **at once**: ⛔ **the check
> was mute, and a mute check has the same face as a check that passes**. ⭐ Now we look
> in `/proc` for **whoever still has that profile among its arguments** — never `pkill -f` — and the
> deletion **is re-verified five seconds later**.
>
> ⭐ **Then the dirty logs were thrown away, and not before**: `sonda/racc.log` and the **two whole Firefox
> profiles**, **33 files**, of which **5** contained the password. ⛔ The trace — name, bytes,
> `sha256`, date, and **whether** they contained it but not **which one** — is in `banchi/01-b13-buttati.jsonl`:
> throwing away evidence without leaving its account is the second half of the same defect.
> ⇒ ⭐ **`B13.2` is green**: *«la parola non compare in nessuno dei **1368** registri»*, denominator
> **22 461 files**, **zero unreadable**, with the positive control next to it.
>
> ⭐⭐ **`B13.4` closes, because against the product it finally has a suspect**: the page loads
> (**200, 31 083 bytes**), carries the **current fingerprint**, and **`/impronta` answers**. **4 out of 4**.
> ⚠ Against the **graft** it will stay `[?]` forever: there nobody listens on TCP.
>
> ⭐⭐ **And B13 is certified** `[M]` **11 Aug 2026, 15:19**, NIC-OS: **healthy 3 → fault 1 → healed
> 3**, with B12's fault (`pagina.pem` replaced by `sessione.pem`) and the mark *«LE IMPRONTE
> COMBACIANO»* **in its place** — plus the **14 hand-built faults** of `--certifica`: **14 out of
> 14** ⚠ **as a normal user**, and **13 out of 14 as root**, because `0000` permissions do not stop root and
> ⛔ **a skipped fault is not a passed fault**. ⚠ **Three deviations from B12, written inside the log
> line**: port **7481** instead of 7447 · target the **product** and not the graft · the
> cycle driven by its own script, because `01-b12-lancia.sh` **writes `PORTA=7447` in plain text** and cannot
> be pointed elsewhere.
>
> ⛔ **What remains open, and there are two**: **`B13.3`** — there is a suspect (`src/certificati.c`, **45
> lines**) and this bench **does not question it**: it needs a bench that *installs* an authority
> certificate and looks at what the server presents on the wire afterwards · **`B13.5`** — **not measured**: the
> credit read from the peer is **19** (§2.3 wants at least 16), but `aioquic` grants **all** 23
> streams requested, so the tool cannot say *no* and its *yes* is worthless. ⚠ It is a defect of the
> **bench**, not of the server.
>
> ⛔⭐ **And B13's first log line did not count, and it took two readings to notice.**
> The bench was certified and the report said so; ⚠ but `01-b12-guasti.py --registro` classified
> B13 among the **NOT RE-VERIFIABLE** certifications, that is, **it did not count it**. ⛔ And the reason was not
> *«mancano le impronte»*: the fingerprints were there, **under names the catalogue does not know**
> (`01-b13-sera-certifica.sh`, `src/rcp.c`, `src/pagina.c`). `FILE_CHE_CONTANO["B13"]` names
> **two** of them — `01-b13-proprieta.py` and `rcp/rcp.c` — and `confronta_impronte()` walks the old keys
> with a `get`: ⛔ **a single key outside the catalogue sends the whole line to *«non si sa»***.
> ⭐ **The tool was right, and for the right reason**: *«non so se valga oggi»* is not
> rounded to *«certificato»* (`LEZIONI.md` §1.9).
> ⭐ **And the correction is a NEW line, not a rewritten line**: the 15:07 one stays where it is, and
> the 15:19 one says why it exists. ⚠ *And it became clear why the other half of the
> cure was needed too: between one `--put` of the whole log and the next, the server had gained **a line
> from another agent** — which a `--put` would have deleted silently.*
>
> ⚠ **And the line carries written inside it a reservation that would otherwise not be seen**:
> `FILE_CHE_CONTANO["B13"]` names `rcp/rcp.c`, the **benches'** copy, while the cycle measured
> the **product**. Today the two copies are identical byte for byte (`84411b9c…`) — ⛔ **by
> coincidence, not by construction**: the day they diverge, that line will re-verify the wrong
> file and go on saying yes.
>
> ⭐ **And the `sonda/` folder was not in the repository**: like the fourteen files of 10 August, it lived
> only on the server. Now it is in `banchi/sonda/`.
>
> ---
>
> #### ⛔ What B12 REALLY certified: **3 out of 12** — as of 11 Aug 2026, *morning*
>
> ⚠ *The box below is this morning's state, and it is kept because it explains where we started from.
> Today's count is in the box above.*
>
> *Written here because it is the question that counts double, and the answer was in no document: the
> `README.md` said «sei verdi» at the same moment B12's log certified two.
> ⛔ **«Verde» and «certificato» are two different things** — green means the bench ran and
> found nothing; certified means someone **broke the code underneath it** and the bench
> turned red, and on the right mark. It is the second that says whether the first is worth anything. Finding
> **R12C.16**, and the count comes from `banchi/01-b12-registro.jsonl` read line by line on 11 August.*
>
> ⛔ **And the words are four, not two**, because there are four states:
>
> | Bench | State | When, and on what |
> |---|---|---|
> | **B4** | ⭐ **certified** | 11 Aug 00:27, machine `CHUWI`, with the fingerprints of the **three files that take part** (`01-b4-lancia.py`, `01-b4-validatore.py`, `01-b4-registrazioni.py`) |
> | **B9** | ⭐ **certified**, ⚠ **with a written reservation** | 11 Aug 00:27, `CHUWI`, fingerprints of `01-b9-letture.py`, `01-b3-cliente.py` and of `RCP.md`. ⚠ The fault built for it **deletes a quotation** from the document: what it proves is that B9 can see **a changed text**, which is the thing B9 openly declares it can do — **not** that it can see the second reader aligning with the first (finding **A8**) |
> | **C2** | ⭐ **certified** | 10 Aug 22:32, machine `NIC-OS`, with a **discriminating** mark — that is, one that **does not appear** in the healthy round |
> | **B13** | ⛔ **tested and NOT certified** | 10 Aug 22:24 and 22:25, twice. ⛔ And the reason belongs to the **fault, not the bench**: it is of the «command line» type and the orchestrator does not know how to graft it; and even grafting it by hand it would build a defect that **B13.1 does not look at** (findings **A1**, **A2**) |
> | **B7** | ⚠ **certified and NOT re-verifiable** | 10 Aug 21:19. ⛔ The required mark was the word `CONGEDO`, which `01-b7-congedo.py` prints **37 times** and in the **healthy** round too: *«una marca che compare in tutt'e due i giri non è una marca, è un modo di certificare senza guardare»* (finding **A3**). And that round did not leave per-bench fingerprints |
> | **B2 · B3 · B5 · B6 · B8 · B10 · B11** | ⛔ **never tested** — seven | no B12 round touched them |
>
> ⛔ **The honest count: 3 certified out of 12**, one tested and failed, one not re-verifiable,
> seven never tested. ⚠ **It is not rounded to «quattro»** (the number the log declared at
> 21:19) **nor to «sei»** (the README's greens): *«provato e non riuscito»* and *«mai provato»* have two
> different cures, and a log that merges them always merges them **into the more innocent one**.
>
> ⚠ **And the denominator must be declared, or it is a count without a denominator**: the twelve of this
> table are **B12's catalogue**, which includes **B10** — which has no script of its own — and
> excludes **B12**, which does not certify itself. ⛔ **They are not the same twelve** as the written benches
> (the prefixes in `banchi/`, which include B12 and not B10): two sets of twelve that look alike
> and do not coincide, and that is precisely how a count stops being a measurement.
>
> ⭐ **And two defects of the log itself were cured on the night of the 10th, and they must be stated because they
> explain why yesterday's count did not add up**:
> · the field was called **`mai_provati`** and meant *«mai provati **in questo giro**»*: B7 and C2,
>   certified at 21:19, appeared at 23:01 as **never tested**, and B13 went from *«provato e
>   non riuscito»* to *«mai provato»* — with the **same** code fingerprint (finding **A4**). Now
>   the field is called `non_provati_in_questo_giro`;
> · the recorded fingerprint was that of `banchi/rcp/rcp.c` **even for the benches `rcp.c` does not
>   enter at all** (B4, B9, C2): a denominator that promises one thing and measures another, that is
>   **worse than no fingerprint**, because it gives the line the look of having already been checked
>   (finding **A5**). Now every line carries the fingerprints **of the files that really take part**.

> #### ⭐ P1 and P5 enter the catalogue, and the denominator changes — the evening of 11 Aug 2026
>
> The `README.md` said it with a number: *«P1 e P5 non sono nel catalogo di B12: i banchi sono 14,
> le voci 12»*. ⛔ And those two were not «clean»: they were **two benches that had never turned red**, that is the
> definition of NOT CERTIFIED — ⛔ **and they are the two that look at the PRODUCT**, the only thing in
> this phase a user would see.
>
> ⛔ **The true denominator, counted and not remembered** (`ls banchi/`): **22** `01-` prefixes, which are not
> 22 benches — **14 benches** (B2 B3 B4 B5 B6 B7 B8 B9 B11 **B12** B13 C2 **P1 P5**), **1
> toolkit** (`01-b0-*`) and **7 Group 1 probes** (S1b S2 S3a S5 S6 S7 S-telefono), which are
> measurements and not benches that get certified. The catalogue entries go from **12 to 14**.
> ⚠ ⭐ **And they are not the same fourteen**: the catalogue includes **B10** and excludes **B12**, which
> does not certify itself. ⇒ The benches the catalogue can certify are **13**, and the entries that
> have a bench behind them are **13**: two sets that now **coincide**, whereas before tonight
> they were twelve and twelve **different** ones — that is, the count added up and counted things that were not the same.
>
> | | |
> |---|---|
> | ⭐⭐ **P1 is CERTIFIED** | `[M]` NIC-OS, port **7501**, three rounds at **12:56:20 · 12:56:56 · 12:57:24 UTC**: **0 → 1 → 0**, GREEN 34/34 → RED 33/34 → GREEN 34/34. Fault: `Cross-Origin-Opener-Policy` from `same-origin` to **`unsafe-none`**. Mark `MANCA: Cross-Origin-Opener-Policy: same-origin`, measured **0 · 2 · 0** |
> | ⭐ **and the red is from ONE check only** | `costruzione.esito` stays **0** and `binario.marche` stays **8/8**: the fault did **not** go through a failed build, which would turn any bench red and would certify **zero** |
> | ⛔ **and the first draft of the fault would have been exactly that** | it removed **the header**. ⚠ But `src/costruisci.sh` **looks for `Cross-Origin-Opener-Policy` inside the binary and stops if it does not find it**, and P1 looks for it too among its eight marks. ⭐ Caught **by reading `costruisci.sh` before grafting**, and the cure is in the shape of the fault: **change the value, leave the name** |
> | ⛔ **P5 is TESTED and NOT CERTIFIED** | and not *«non provabile»*, which is the other thing. ⭐ But its count changed twice in an hour, and the second time for the better |
> | ⛔⛔ **WARNING: the two rows below were REFUTED the same evening** | ⭐ The bench really had a defect — `ctrl+w` on the wrong display, and that is true — ⛔ **but the acquittal that followed was false**: the arbitration counted a closure **without looking at its reason**. The product defect **is there, on both engines**. Read these rows **to the bottom of the box**, where the measurement corrects them |
> | ⭐⭐ **and the accusation against the PRODUCT belonged to the BENCH** *(row refuted — see below)* | ⛔ P5 wrote *«nessun congedo, per nessuna delle due strade di §3.1»* — that is, it accused the page of violating §8.1 **for a gesture never made**: `01-p5-lancia.sh` typed `xdotool key ctrl+w` **without the `X` function**, on a `DISPLAY` that is not the fake screen. The key did not arrive, `pagehide` did not fire. ⭐ **The arbitration is `banchi/01-p5-congedo.sh`** `[M]` **13:26 UTC**: one leaves in **two ways** — navigating away, where `pagehide` fires for sure, and with `ctrl+w`, where it fires only if the key arrives — and ⭐ **from both the farewell GOES OUT** (way 2 of §3.1, slot `LASCIATO`, **zero** `STACCATO per silenzio`, and the gesture verified by the windows **1 → 0**). ⇒ **The page does what §8.1 requires of it.** ⚠ It is `LEZIONI.md` §1.9 again, and **the second time in this phase after B3**: the red pointed at the wrong suspect |
> | ⭐ **and the witness was well chosen** | the **server's** log, read at **+8 s** — before the 30-second cap can free the slot: without that window, *«si è congedato»* and *«staccato per silenzio»* arrive with the same face. ⚠ *And the first round of the arbitration got it wrong itself: the segment closed on the end marker, while `pagehide` fires **while that request is in flight**, and the farewell line fell outside. A zero from a wrong segment has the same face as a true zero — the **second** round is the one that counts* |
> | ⭐ **pilot cured, the numbers move** | `X` in front of `ctrl+w`, and `fuoco` moved **out of the N2 branch** — with the unban not answering, that branch was skipped, and the `P` leg was reached **without ever having given focus to any window**. `[M]` healthy round **13:29:41 UTC**: ⭐ **Chrome becomes CONFORMING**, and ⭐ **Firefox now MEASURES** — it reaches `SESSIONE`, **14 out of 15**, fixed second **1069 ms** — where before it had no denominator |
> | ⛔ **and ONE point remains, which this time does NOT belong to the bench** | on **Firefox** the farewell does not go out all the same: from the server's log the client closes with a **bare `FIN` on the control channel**, the slot is `LASCIATO` **in an orderly way** and `STACCATO per silenzio` is **0**. ⇒ **The gesture arrived, the session closed properly, and the client did not say why** — where §8.1 requires it unconditionally. ⚠ **The two remaining suspects cannot be told apart from this side**: *«la pagina non spedisce»* and *«Firefox butta via quel che la pagina spedisce dentro `pagehide`»* arrive identical at the server, and separating them needs the **browser's** log. ⭐ And note that the page anticipates the **opposite** case — *«Chrome butta un messaggio spedito subito prima di chiudere, quindi la strada che regge è il codice di chiusura»* — while on Firefox **neither** of the two holds: it is the difference between engines P5 exists for, ⛔ **and it appeared only AFTER curing the pilot**, which is the proof that the two columns are needed |
> | ⭐ **and P5's fault is measured all the same** | the mark `sono due impronte diverse per lo stesso certificato di sessione` appears **1** time in the red round and **0** in the healthy one: the bench **sees** its own fault. ⇒ P5 is not certified because **its healthy round is not green** — the same shape as B8 — **not** because it is blind |
>
> ##### ⛔⛔ AND THEN THE MEASUREMENT REFUTED THE ACQUITTAL: **the farewell does not go out, and it belongs to the PAGE**
>
> *`[M]` 11 Aug 2026, evening, `banchi/01-p5-ff-*`. ⛔ Two identical rounds per engine, on an **instrumented
> copy** of `src/pagina.html` served by a separate server — the product was not touched.
> The tracer is `navigator.sendBeacon`, that is **a carrier that does not go through WebTransport**: if it
> went that way it would share the fate of the thing being measured.*
>
> ⛔ **The suspect is the page, and Gecko is cleared by measurement.** Closing the tab with `ctrl+w`
> **with the browser alive**, on Firefox 140.13.0esr `pagehide` **fires** — and the page's trace says
> `congeda_corrente NULLA`. ⇒ The handler in `src/pagina.html` is **dead code**: the `finally`
> of the `submit` handler (line **620**) zeroes `congeda_corrente` **one millisecond after
> `SESSIONE`**, because `collega()` returns there. The slot goes away after `STACCATO per silenzio:
> 30060 ms`.
>
> | variant, same engine and same scene | `pagehide` | `congeda()` called | what reaches the SERVER |
> |---|---|---|---|
> | **faithful** — the product as it is | ⭐ **1** | **0** | ⛔ **nothing** |
> | **tenacious** — the *same* `congeda()`, reference not zeroed | 1 | 1 | ⭐ **`CONGEDO` on the channel + code `0x01`** |
> | **code** — only `wt.close(0x01)` | 1 | — | ⭐ code `0x01` |
> | **alive** — the same `congeda()`, tab **alive** | — | 1 | ⭐ `CONGEDO` + code `0x01` |
>
> ⇒ ⭐ **Firefox throws nothing away**: inside `pagehide` **both** ways of
> §3.1 work. **All that is missing is someone to take them.**
>
> ⛔⛔ **And Chrome's ⭐ was a FALSE GREEN — it is the most valuable finding.** In the same scene,
> on Chrome, the page sends nothing and what reaches the server is **Chrome's teardown**:
>
> ```
> ⛔ VIOLAZIONE §3.1 — la pagina ha chiuso la sessione col codice 0x0 … A verbale va ERRORE_PROTOCOLLO
> la pagina ha chiuso la sessione, motivo 0x0b
> ```
>
> ⛔ `01-p5-congedo.sh` counts the line *«la pagina ha chiuso la sessione, motivo»* **without
> looking at the reason**: it counted **a violation of §3.1 as a farewell**, and printed
> *«⭐⭐ LA PAGINA FA QUEL CHE §8.1 LE IMPONE»*. ⇒ ⭐⭐ **The two engines were not opposite: they showed
> the SAME page defect through two different teardowns**, and on one of the two the bench
> tripped over its own counter. ⚠ *And the server said so*: it writes the violation line itself,
> and it was in the log.
>
> ⭐ **The cure is three lines, and it is DESCRIBED AND NOT APPLIED** — the phase had been closed for an hour, and a
> product cure slipped in after the closure is not a cure, it is an undeclared change.
> The anchor of `congeda_corrente` is wrong: it is not *«il tentativo è finito»*, it is ⭐ ***«la sessione è
> finita»***. ⇒ remove the zeroing from the `finally` (line 620) · zero it inside
> `wt.closed.then(…)` of `collega()`, the only point that knows when the session is gone · leave
> the one at the start of the handler (line 606), because a new attempt must throw away the old reference.
>
> ##### ⭐⭐ AND THEN THE CURE WAS APPLIED AND RE-MEASURED — **two rounds per engine, and the defect is gone**
>
> *`[M]` 11 Aug 2026, late evening, `banchi/01-p5-ff-*` on **7511**, log in
> `banchi/01-p5-ff-registro-cura.log`. ⛔ **The expected result is written in
> `banchi/01-p5-ff-strumenta.py` BEFORE measuring**, and that is the document that gives the verdict:
> «`fedele` deve comportarsi come `tenace`; `eco` deve dire `congeda_corrente PRESENTE`; gli altri
> tre invariati».*
>
> | the same scene, `ctrl+w` on two tabs | BEFORE the cure | AFTER, two rounds per engine |
> |---|---|---|
> | **Firefox** — `pagehide` | fires, guard **NULLA** | fires, guard ⭐ **PRESENTE** |
> | **Firefox** — `congeda()` | **0** | ⭐ **1** |
> | **Firefox** — at the server | ⛔ **nothing**, bare `FIN` and `STACCATO per silenzio` | ⭐ `CONGEDO` on the channel **+** code **`0x01`** |
> | **Chrome** — at the server | ⛔ closure with code **`0x0`**, which §3.1 **forbids** and which the server puts on record | ⭐ `CONGEDO` on the channel **+** code **`0x01`**, and **zero** violations |
> | **`fedele` versus `tenace`** | two different columns: the defect was **there** | ⭐ **they can no longer be told apart** — and that is the definition of the cure, since `tenace` was the variant that bypassed it |
>
> ⭐ **And the lowest trace says the same thing from below**: `finally-congeda_corrente-PRESENTE-cura-in-vigore`
> arrived in **10 variants out of 10** (five per engine), and `fine-sessione-lascio-il-mio-riferimento`
> where the session really closes ⇒ the reference is let go **only once, at the end
> of the session**, which is exactly the new anchor. On Firefox also by the **synchronous** route
> (`eco-congeda_corrente`: **NULLA → PRESENTE**, in both rounds).
>
> ⛔ **Three things the measurement added that were not in the expected result**, and they are written down:
>
> | | |
> |---|---|
> | ⛔ **the bench's tracer is BLIND on Chrome inside `pagehide`** | **neither** `sendBeacon` **nor the synchronous XHR** of `eco` gets out: six rounds, zero traces. ⇒ On Chrome the attribution rests **only** on the server's log — which however is clear-cut, because between before and after **the violation line** changes. ⚠ And it explains in hindsight all the zero columns of the Chrome rounds: they were not a silence of the product, they were a silence of the **carrier** |
> | ⚠ **a race seen only once in six rounds** | in the 18:54 `vivo` on Firefox the `CONGEDO` **on the channel** did not arrive, although the page had seen *«la write si è risolta»* and *«il FIN del canale è passato»*. It is the same race that **B11 measured on Chrome** (defect 2). ⛔ **It does not touch §8.1**: the reason `0x01` arrived all the same, through the **closure code** — that is, through the way `DECISIONI.md` §7.14 chose **precisely for this**. ⚠ One observation is not a measurement: it is written down and not concluded |
> | ⭐ **and `eco` on Chrome is the negative control nobody had asked for** | there the closure with code **`0x0`** is **still** present, with the violation on record — and that is right: `eco` leaves `pagehide` **without sending anything**, that is it is the product **from before**. ⇒ The `0x0` has not disappeared from the engine: it disappears **when someone says farewell** |
>
> ⛔ **And what this measurement does NOT say.** It runs on an **instrumented copy** of `src/pagina.html`
> served by a separate server: the home product was not switched on, and the usual line holds —
> *«nessun banco ha mai acceso `src/`»*.
>
> ##### ⛔⭐ AND THE CURE UNCOVERED ANOTHER ONE BENEATH: **the slot that is freed silently**
>
> *Found while curing P5's scene, `[M]` the late evening of 11 Aug 2026 — and not by looking for it.*
>
> ⛔ **The defect.** `src/rcp.c` frees the slot in **four** places, and **three** write it to the
> log. The fourth — `CONGEDO` received from the client — does not. ⇒ On the way that **§8.1 requires**, that is
> the one the healthy product always takes, the log carries **no** `posto LASCIATO`.
>
> ⚠ **And the slot really was freed**: `[M]` twelve sessions in a row in the evening's logs, and
> **every** subsequent `posto PRESO` says `occupati adesso: 1`. It was not a leak — it was that
> **the §8.2 `0x0F` invariant could no longer be observed**. ⛔ And the consequence is concrete: P5
> **judges the final number** of `occupati adesso`, did not find it, and would have written *«IL POSTO NON
> SI È LIBERATO»* on a server that had done its job — a red at the wrong suspect, the
> seventh guise of `LEZIONI.md` §1.9 for the **third** time in this phase.
>
> ⭐ **And it was invisible until tonight**: before the farewell cure the client **never** said farewell,
> so that branch was never taken and the slot always went away through the inactivity
> cap — which does write its line. ⇒ **The cure uncovered the defect that the cure itself
> made reachable.**
>
> | P5's judge on the same kind of segment | faults |
> |---|---|
> | before the farewell cure (Chrome) | ⛔ **2** — *«nessun congedo per nessuna delle due strade»* **+** *«violazione-31 trovate=1 atteso=0»* |
> | farewell cured, slot not yet | ⛔ **1** — *«IL POSTO NON SI È LIBERATO»*, **and it was false** |
> | slot cured too | ⭐ **0**, way *«congedo del client (posto LASCIATO)»* — `[M]` **two rounds per engine**, four out of four |
>
> ⛔ **And «zero faults» does not mean «P5 is certified».** What is green is **P5's judge on
> a real segment** produced by the cured product; the **P5 round** — with its grafted fault, the
> two columns and all the scaffolding — **has not been done**. They are two different words, and this phase
> has already confused them once.
>
> ##### ⭐⭐ AND SO P5 WAS RELAUNCHED — the leg that counted is **GREEN on both engines**
>
> *`[M]` the night between 11 and 12 Aug 2026, against a **copy of the cured product** on
> **7501** (`banchi/01-p5-accendi.sh`, written tonight: the recipe was in prose inside the
> fault catalogue, and a recipe in prose gets copied by hand by whoever uses it).*
>
> | | |
> |---|---|
> | ⭐⭐ **`p-sessione`: CONFORMING, Chrome AND Firefox** | 15 checks, **0 faults**: farewell by **both** ways with reason `0x01`, `violazione-31` at **zero**, slot **taken and released**. ⇒ The point that kept P5 out of the green **is gone** |
> | ⭐ **and the N2 leg runs, for the first time since it has existed** | it only needed to be able to go through `sudo`: `SSH_ROOT` chooses the carrier of the privileged commands (`fondamenta/strumenti/sshpw.py` types the password on a pty), and the §4.4-bis unban answers `PONG`. ⛔ And the two carriers stay **two**: `sshpw.py` leaves two preamble lines in its own stdout, and using it also to **download** the log would soil the evidence with the tool that collects it |
>
> ⛔ **And two defects of the PILOT came out one after the other, both found by a
> PHOTOGRAPH** — that is, by the thing this bench takes saying *«materiale per chi legge, NON un
> verdetto»*:
>
> | | found by | and the cure |
> |---|---|---|
> | ⛔ **N1's browser survives, and the next leg attaches to it** | `firefox-n2-parola-sbagliata-1-pagina.png`: Firefox with **three tabs** — two from N1's probe — stuck on the start marker, after two `ctrl+l`+address+`Invio` gone into the void | `kill` kills the process but **the window stays**, and the next leg reuses **the same profile**: the new browser is not born, it attaches to the old one as an extra tab. ⭐ Cure **already at home**: it is the one `01-p5-ff-lancia.sh` had measured the same day |
> | ⛔ **the data bar shifts the page by ~23 px** | `firefox-0-avviso-non-superato.png`: the certificate warning **not passed**, with the bar *«Firefox automatically sends some data…»* at the top | the two clicks of `supera_avviso` are at **measured** coordinates, and with the bar they land **above** the buttons. ⭐ The cure is not moving the coordinates — it is **removing the bar**, so the measurement those numbers come from is valid again |
>
> ⛔⭐ **And the first was hiding the second**: as long as the product leg reused N1's browser,
> the bar had already been eaten by the previous session. ⇒ *One defect cured, the second
> appeared* — and it is the same shape as the mute `posto` above, twice in the same night.
>
> ⚠ **And the bench did the right thing the first time it happened**: the N2 leg on Firefox did not
> give a red, it said **SENZA-DENOMINATORE**. It is the check added while curing the scene, and it
> worked at the first real case.
>
> ⭐⭐⭐ **AND THE CERTIFICATION IS DONE: `0 → 1 → 0`** — `[M]` the night between 11 and 12 Aug 2026,
> the three rounds `sano → guasto → sano` in full against the copy on **7501**, with the browsers on
> CHUWI and the product on NIC-OS. `01-b12-registro.jsonl`, the 21:02 line on CHUWI, with the fingerprint
> of the three files it rests on.
>
> | | |
> |---|---|
> | ⭐ **healthy: GREEN on two engines** | n1 right/mangled `ok`, N2 **11 checks 0 faults**, `p-sessione` **15 checks 0 faults**, Chrome **and** Firefox |
> | ⭐ **fault: RED, and it names the right thing** | *«la pagina pubblica «AAAA…=» e l'endpoint dice «PJ03…=»: sono due impronte diverse per lo stesso certificato di sessione»* — defect **R1.14** |
> | ⭐ **and the mark is a mark** | `[M]` **0** times in the healthy round, **1** in the fault, **0** in the healed one — counted on that night's three rounds, not on a measurement from yesterday |
> | ⭐ **healed: GREEN, and the binary returns identical** | `d69df441…` → `117911ca…` → `d69df441…`: that the fault went in and then out is told by **the binary's fingerprint**, not by the colour of the verdict |
>
> ⛔ **And the fault proves LESS than its title says.** With the false fingerprint in the page
> the `p-sessione` legs stay **CONFORMING**: the session **opens all the same**. ⭐ The reason belongs to the
> product and is §4.1-bis applied — `pagina.html` **fetches `/impronta` again before every attempt** and
> uses that, keeping the served fingerprint only as a fallback, and **says so** when the two diverge.
> ⇒ The fault proves that **P5 sees the divergence**, which is what P5 exists for; it does **not** prove that the
> divergence kills the session, because on this product it does not kill it. ⚠ The symptom described in
> R1.14 remains that of a product that does **not** fetch the fingerprint again.
>
> ⛔⭐ **And the first attempt at a healthy round came out RED with all four legs CONFORMING** — the
> contradiction between the table and the final line was the symptom. The suspect was named by a line
> that `grep` prints by itself: `binary file matches`. The server's log had a **hole of 37.120
> NUL bytes** (`svuota-registro` called with the server alive), `grep` became blind **with exit
> status 0**, and the bench sent the §4.4-bis unban **to the server instead of to us**. Three cures,
> all re-measured; the lesson is `LEZIONI.md` §1.9 point 9.
>
> ✅ **And the cure is a product change after the phase closed, so it was
> DECLARED**: `DECISIONI.md` §1.12, by the user the same night. ⛔ **Phase 1 is not reopened** and
> the certification stays **12 out of 14** as it was delivered — this section is a **dated
> appendix**, and it does not change a number in the document. ⭐ **And the cure is not rolled back**, because it is measured
> with the same rigour as the phase. ⇒ What passes to phase 2 is the **re-certification of P5**, which did not pass
> precisely because of this defect — ⚠ and it first needs the cure of its scene, which still closes `ctrl+w`
> on the **only** tab.
> ⭐ *Update from the same night: the scene is cured, and **P5's re-certification no longer passes
> to phase 2 — it is done**, above. ⛔ What passes to phase 2 instead is the **re-run of
> seven expired certifications**: the §1.12 cure touched `rcp.c` and `RCP.md`, and `--registro` counts them
> as not certified — B3, B5, B6, B7, B8, B13 and B9. The count is in `README.md`.*
>
> ⚠ *One round was **cancelled**, and it is written in `01-p5-ff-esiti.jsonl`: the **browsers' PC
> reset with the round open** at 18:40. The last trace at the server is `ffm-183953-29125-fedele-avvio`,
> no outcome was written and the «after» unban never started. ⛔ It counts neither for nor
> against, and the pair of agreeing rounds was redone from scratch.*
>
> ⚠ **And two findings for the benches, which are valid beyond this case**: *(a)* one counts **`motivo 0x01`**,
> not *«una chiusura qualunque»* — a counter that does not read the reason turns a violation into
> a green; *(b)* ⛔ **`ctrl+w` on the only tab makes Firefox QUIT**, and in that scene nothing goes out
> by **any** way, not even for the variants that bypass the defect: **the scene must be done
> with two tabs**, or one measures the program quitting instead of a tab closing. *It was
> P5's scene.*
>
> ⛔ **And both faults are grafted onto a WHOLE COPY of the product**, never onto
> `/media/REMOTIX/src/remotix/`. ⚠ The reason is **not** that of the Python faults of the other
> benches: it is that **P1 rebuilds the binary as the first step of its own round**, and faulting the
> home product would leave, for the minutes of the middle step, **a lying binary under the feet
> of anyone else who switched it on again**. *On the evening of 11 August on the test machine there was a
> live `remotix` on 7448 and five agents working together.*
>
> ⭐ **And `01-p1-prodotto.sh` and `01-p1-dentro.sh` accept from tonight `PORTA`, `PORTA_MORTA`, `SORG`
> and `PREFISSO_TMP`**, with the previous defaults: whoever launches by hand measures what they measured before.
>
> #### ⭐⭐ B8 CERTIFIED — and the cure was not completing the copy, it was REMOVING the copy
>
> | | |
> |---|---|
> | ⭐ **B8** | **certified, and it never had been**: `[M]` 11 Aug 2026, **13:46 UTC**, NIC-OS, graft, port **7471** — **`5 → 1 → 5`**, mark *«N risposte sotto il secondo»*, seen **only** in the red |
> | ⛔ **and the healthy expected value is 5, not 0** | ⭐ **written in the catalogue before the round, not widened afterwards**: it is B8's fifth outcome — *«il ban passa per intero, ma le mediane si separano»* — and it is granted **only** because the suspect is **measured** and is **PAM**. ⭐ The day that `[?]` closes, the healthy value will become **0** and **that catalogue line will turn red by itself**: it is the right way to notice |
> | ⭐ **the fault gives a full red** | `RITARDO_FISSO` from 1000 to **0**: `[M]` **17 answers under the second**, the fastest **49,7 ms**, and the median of the «right password» case from **1085,9** to **56,3 ms** |
> | ⭐ **and the round finally covers the whole sequence** | **two lives of the server** — the second start declares *«ban caricati: 1»*, that is the ban comes back **from disk** and not from memory (**I7**) · **the page** (HTTP **200**, `bannato=True`, *«tentativi esauriti»*, **12h 0m**, with the check that says no at 594 bytes) · **the unban on a real ban** (`TOLTO` → then `NON-BANNATO` → and the address **gets back in**) |
> | ⭐ **the secret does NOT leak** | medians `[M]`: **nonexistent 2123,2 · wrong 2198,1 · right 1085,9 ms**; the pair §4.4 protects — *«inesistente − sbagliata»* — is **−74,8 ms**, interval **[−509,3; +255,7]** ⇒ ⛔ **it does not separate**. And the suspect for the rest is measured: the server waited **+1034 ms** beyond the fixed second on the rejected and **+84 ms** on the admitted — the signature of `pam_faildelay` |
> | ⚠ **and the two denominators beside it** | the certification **off the wire** 33 out of 33, and B8's **judge** 15 out of 15 hand-made faults, in all three steps |
>
> ⭐⭐ **And the structural cure is point 4 of the list, done where it bit.** `01-b12-lancia.sh`
> **rewrote by hand** B8's sequence, and the copy was incomplete in three places: the healthy round
> came out red on **eight** points that spoke **of the orchestrator, not of the bench**. ⇒ Now
> `gira()` **calls `01-b8-lancia.sh`** — as it had always done with C2, so it is a precedent at
> home and not an invented exception — and reads the mark from the file B8's verdict writes by itself.
> ⚠ **And it stopped there on purpose**: extending this to the other benches tonight would have changed the
> way of launching benches **certified today**, that is invalidated nine certifications to redo them in a
> time that was not there.
>
> ⛔ **What this certification does NOT cover**, and it must be said: B8 is certified **against the graft**.
> On the **product** the three hooks of the ban page exist, ⚠ but the round was not done there; and
> **the page is read by a socket, not a browser**, while this section asks for its DOM *«come per
> le otto frasi di B7»*.
>
> ⚠ **And P1's certification cannot be re-verified from CHUWI**: its line lists `remotix/pagina.c`,
> which from `banchi/` exists **only on the server** — here the product is in `../src/`. ⛔ So
> `--registro` classifies it *«non si può dire se valga oggi»*, and it is **B9's scene in reverse**
> (there `RCP.md` was missing on the server). ⭐ *«Non riverificabile da questa macchina»* is not
> *«non certificato»*, and the tool does well not to merge them — but the count **still depends on where
> one asks for it**, and it is the same `[?]` as the afternoon, not cured.

#### B13 — ⭐ Sei cose che la fase produce e che nessun banco guardava

*Rilievo **R3.24**. Tre hanno un ⛔ scritto in `RCP.md`.*

| # | Che cosa si verifica | Quando morderebbe |
|---|---|---|
| **1** | ⛔ **che i due certificati siano DUE** (§4.1-bis): impronte diverse, scadenze diverse | un server che ne genera uno solo a scadenza breve **passa tutti i banchi** — e l'avviso ricompare **quattordici giorni dopo**, quando *«nessuno collegherebbe le due cose»* |
| **2** | ⛔ **che la parola d'ordine non sia in nessun registro**: un `grep` della parola di prova su **tutti** i file prodotti dal giro — registro del server, registro della pagina, registrazione del validatore | la fase riusa `registro.c`, che in v1 è *«un registratore di battitura»*, e aggiunge un registratore di byte decifrati |
| **3** | **la chiave privata a `0600`**, il `subjectAltName` che combacia, e ⛔ **che un certificato d'autorità installato venga usato senza rigenerare il proprio** (§4.1) | nessuna fase lo dichiarava |
| **4** | **la pagina servita in TCP**: che si carichi, che pubblichi l'impronta **corrente**, e che **l'endpoint da cui si ritira l'impronta aggiornata esista** (§4.1-bis) | è il secondo mestiere che il server acquista qui, e B3 lo presupponeva in una riga |
| **5** | **il credito di almeno 16 stream unidirezionali** concessi al client (§2.3) | se finisse, *«l'input non partirebbe affatto»* e il sintomo sarebbe «il desktop non risponde» — alla fase 4, lontano da qui |
| **6** | ⛔ **che `stato` valga SEMPRE `NUOVA`**, cioè che nessuno abbia scritto per prudenza un ramo `RIPRESA` che nessuno proverà fino alla fase 5 | un `[?]` implementato a metà e non provato è quel che il confine dichiara di voler evitare |

#### B14 — che cosa di `RCP.md` §11 questa fase NON prende, e dove va

| Banco di §11 | Dove |
|---|---|
| ⛔ **il rilascio dei tasti al distacco** | **fase 5**, non fase 4 — *corretto da R4.7*: §11 ne scrive la procedura come *«si stacca una connessione con un tasto premuto **e si riattacca**»*, e alla fase 4 non esiste una sessione a cui riattaccarsi. Alla fase 4 la sessione **muore con la connessione**, quindi il banco o non si scrive o **si scrive verde per costruzione** |
| l'audio ascoltato, il formato del PCM | **fase 7** — ⚠ ma **S6** è qui, perché decide i 5 ms |
| gli appunti, i tre messaggi, i due trasferimenti insieme | **fase 7** |
| l'anello del ritardo | **fase 3**, ⛔ **e S4 con lui** (vedi «L'ordine») |
| il fotogramma abbandonato e la chiave che segue | **fase 3** |
| il credito degli stream oltre i 256 fotogrammi | **fase 3** — ⚠ il **credito concesso al client** invece è qui (B13.5): sono due versi diversi dello stesso obbligo |
| ⏳ **`GIA_ATTIVA_LOCALE` `0x05`** | ⛔ **non era di nessuna fase** *(R4.16)*: nasce all'attacco, cioè nel messaggio che questa fase scrive, e la riga di `SPECIFICHE.md` §5.1 che lo impone è la stessa che genera `GIA_ATTIVA_REMOTA`. ⚠ **Va alla fase 5**, con i tre orologi e la sessione locale — ma **dichiarato qui**, o cadeva fra le fasi |

---

## Che cosa è stato sviluppato

> ⚠ **Questo capitolo si apriva con** *«Nessuna riga di **prodotto** scritta. Quel che c'è è
> banco.»* — ⛔ **ed era falso dalla notte del 10 agosto 2026**, quando `src/` è nato: venti file,
> poi ventidue. Nessuno dei dieci documenti del progetto nominava quella cartella, e `PIANO.md` §0.2
> assegna proprio a questo capitolo il compito di dire che cosa la fase ha prodotto. ⛔ **Il costo
> era concreto**: chi riprendeva la fase leggeva *«nessuna riga di prodotto»* e **riscriveva da zero
> un server che esiste** — oppure lo trovava per caso con un `ls` e non sapeva se fosse prodotto,
> scarto o l'esperimento di qualcuno. Riscritto l'11 agosto 2026, rilievo **R12C.1**.
>
> ⛔ **E c'è una seconda cosa che quella riga faceva, meno visibile**: da quando `src/` esiste, ogni
> frase che dice *«il server»* ha **due soggetti** — il prodotto e l'innesto di
> `banchi/01-b3-rcp-innesta.py` dentro `bsslserver`. In questo documento, da qui in poi, *«il
> prodotto»* è `src/` e *«l'innesto»* è l'altro, **e i banchi misurano l'innesto**.

### ⭐⭐ Il prodotto — `src/`, il server della fase 1 in C

`[M]` **11 agosto 2026** (`wc -l` e `grep -cvE` su questo albero, codice fermo alle 00:36):
**22 file**, **9.647 righe**, di cui **5.248 di codice** nei `.c`/`.h`.

⭐ **Che cosa fa, in una riga**: un browser vero apre `https://192.168.0.2:7447`, l'utente digita
nome e parola d'ordine, e **la stretta di mano di RCP/1 arriva fino a `SESSIONE`** — con i due
certificati, la pagina servita dal server stesso, e il ban di `RCP.md` §4.4-bis. ⛔ **Niente video,
niente audio, niente input**: quelle sono le fasi da 2 in poi.

| | |
|---|---|
| `src/main.c` | ⛔ **i due ascoltatori sulla stessa porta 7447** (`RCP.md` §2.4): UDP per HTTP/3 e WebTransport, TCP per il primo caricamento della pagina — e sono **indipendenti**, WebTransport non passa da `Alt-Svc`. Un ciclo `poll` solo. ⭐ All'avvio **guarda che `/etc/pam.d/remotix` ci sia** e lo scrive: senza, Linux-PAM ripiega su `other` (che su Debian è `pam_deny`) e **ogni parola giusta viene rifiutata**, con una diagnosi che punta sulla parola d'ordine mentre il difetto è un file mancante. ⭐ E alla chiusura **congeda tutti** con `SERVER_IN_CHIUSURA` (§8.2 `0x0C`) invece di sparire |
| `src/trasporto.c` | QUIC su **ngtcp2**: `max_idle_timeout` 30 s imposto dal server, datagram annunciati, **19** stream unidirezionali concessi (§2.3 ne vuole 16 *disponibili* e HTTP/3 se ne prende 3 — il numero si dichiara invece di essere sottratto in silenzio), migrazione non disabilitata. ⭐ I datagram che arrivano si **contano e si scartano scrivendolo nel registro** (§6.3), invece di sparire in un callback che non c'è |
| `src/webtransport.c` | HTTP/3 e WebTransport: la `CONNECT` estesa **solo** su `/rcp/1` (404 altrove, §2.2), le capsule, la chiusura col codice del motivo. ⭐ E i **PING del trasporto** mentre il server aspetta le credenziali — senza, al trentesimo secondo la connessione muore in silenzio e i 60 s di §4.6 non scadono mai (§4.6, rilievo R1.8) |
| ⭐⭐ `src/rcp.c` + `rcp.h` | **RCP/1**, la stretta di mano e il ban. ⛔ **Identici byte per byte a `banchi/rcp/`** — `[M]` 11 agosto 2026, `md5sum`: `cb7af778…` (`rcp.c`), `0458f154…` (`rcp.h`). ⚠ **Identici per fortuna, non per costruzione**: nessuno script confronta le due copie a ogni giro, e da stanotte hanno **due storie diverse** (una in git, una no). `src/costruisci.sh` accetta `GEMELLO=` per dichiarare il confronto |
| `src/autenticazione.c` + `remotix.pam` | PAM, ⭐ **servizio `remotix`** come vuole `SPECIFICHE.md` §4.2 — con il file del servizio nella cartella, non in una nota d'installazione. ⚠ *Il 10 agosto notte diceva `pam_start("login")`, cioè la pila della **console locale** con `pam_securetty`, `pam_lastlog`, `pam_limits`: rilievo **B-11** di `fasi/rapporti/R12-B-prodotto.md`, curato nel codice la stessa notte* |
| `src/certificati.c` | i **due** certificati di §4.1-bis, con il rifiuto di partire se le due impronte coincidono, il breve a 13 giorni che ruota quando ne restano due, e `/impronta` servito con `no-store` |
| `src/tls.c` | TLS per l'ascoltatore TCP. ⭐ **0-RTT spento a livello di contesto**, dove nessuna sessione lo può riaccendere (§2.3) |
| `src/pagina.c` + `pagina.html` | la pagina servita dal server: l'impronta corrente, la stretta di mano dal lato del browser, e l'avviso di chi è bannato con **le ore che mancano** (§4.4-bis). ⭐ Il server **si rifiuta di partire** se la pagina non contiene i segni da sostituire, o se ne contiene due — una sostituzione che «riesce senza fare niente» servirebbe per sempre una pagina senza impronta |
| ⭐ `src/comando.c` + `comando.h` | **il comando di sblocco di §4.4-bis**, su un **socket Unix `0600`**: `SBLOCCA <indirizzo>` → `TOLTO` / `NON-BANNATO`, `PING` → `PONG`. ⛔ È lo stesso protocollo, byte per byte, che parla `banchi/01-b8-sblocca.py`, cioè lo strumento della regola **B0.3** |
| `src/registro.c` | riusato da v1, con l'obbligo di **B13.2**: la parola d'ordine non compare in nessun registro |
| `src/Makefile` + `costruisci.sh` | ⭐ **butta il binario prima di ricostruire** (così *«c'è»* vuol dire *«è di adesso»*) e **controlla cinque marche dentro il binario prodotto**, con il controllo positivo dello strumento. È la ottava veste di `LEZIONI.md` §1.9 curata prima di pagarla |

#### ⛔ Che cosa di `src/` NON è provato

*Elencato riga per riga, perché è la metà che non si vede. Le prime due voci vengono da
`fasi/rapporti/R12-B-prodotto.md` §0; le altre le ho misurate io l'11 agosto 2026, e dove ho
misurato lo dico.*

| | |
|---|---|
| ⛔ **il server intero non è mai stato eseguito da un revisore** | sulla macchina del revisore mancano `ngtcp2`, `nghttp3`, `libssl-dev` e `libpam0g-dev` (`make dipendenze` dà **cinque NO**). ⇒ tutto quel che riguarda `trasporto.c`, `webtransport.c`, `pagina.c`, `certificati.c` è **letto, non misurato**. ⭐ L'unica esecuzione è `src/rcp.c` **compilato isolato** con `-Wall -Wextra` — **zero avvisi** — contro un driver del revisore, sei ingressi byte per byte |
| ⛔ **UN SOLO MOTORE** | l'unica traccia di un giro con un **browser vero** contro questo server è un commento dentro `src/pagina.html`: `[M]` 10 agosto notte, **Firefox** — e quel giro ha trovato un difetto vero (la pagina mandava `disposizione = en`, che **non è** un nome XKB, e il server congedava con `SESSIONE_NON_SERVIBILE` facendo esattamente il suo mestiere). ⛔ **Di Chrome contro questo server non c'è nessuna traccia**, e il criterio di B2 vuole **due motori su due** |
| ⛔ **e quel giro non è riverificabile da questa parte** | `[M]` 11 agosto 2026, **mattina**: in `src/` non c'è né il binario `remotix` né un `.o`; nessun `.jsonl`; `git status` dà `src/` **untracked**, mai committata. E **nessuno dei 14 script `01-*-lancia.sh` accende il prodotto**: `bsslserver` compare in **11** di loro, il binario `remotix` in **zero** (l'unica occorrenza della parola è `remotix.prova`, un nome SNI in `01-b2-lancia-sni.sh`). ⚠ ⛔ **E questa riga è SCADUTA la sera dello stesso giorno, e va letta con la data addosso**: `[M]` 11 agosto **sera** — `git ls-files src/` dà **22 file** (commit `ffeb341`), gli script di lancio sono **16** e **11 di loro sanno puntare al `BERSAGLIO=prodotto`**, tre accendono il binario per nome. ⭐ *Una riga che dichiara un'assenza invecchia nel verso peggiore: resta vera nell'aspetto e falsa nei fatti, e chi la legge non ha nessun motivo di sospettarla* |
| ⛔ **le proprietà di trasporto non sono state rimisurate contro questo server** | le sei di B2 — tetto 30 s · datagram · credito uni · migrazione · niente 0-RTT · `allowPooling` — sono `[M]` **sull'innesto**, letto dal pari. `src/trasporto.c` oggi dichiara **19** stream uni dove la misura di B2 ne leggeva 16: è un numero diverso, ed è **la sonda `01-b2-sonda-trasporto.py` puntata al prodotto** che lo direbbe |
| `[?]` **il rinnovo del credito degli stream** | il prodotto lo dichiara **di suo** (`src/trasporto.c`): ngtcp2 non alza il tetto da sé *«tranne quando uno stream si chiude senza che `stream_open` sia stato chiamato»*, e questo codice cade **probabilmente** in quell'eccezione. Nessuno l'ha misurato. ⛔ Si misura alla **fase 4**, quando gli appunti apriranno uno stream per trasferimento: prima di allora nessun client ne apre più di quattro, e una misura senza il carico che la provoca non è una misura |
| ⚠ **la pagina del prodotto e quella dell'innesto sono due documenti diversi** | e **B8 misura i marcatori che solo l'innesto produceva**. Curato nel prodotto la notte del 10 (`data-bannato` e `data-restano-ms` ci sono, in una sola occorrenza ciascuno, e il server rifiuta di partire se ce ne fossero due) — ⛔ **ma nessuno ha puntato B8 al prodotto per verificarlo**: finché non lo si fa, «curato» è letto e non misurato |

#### ⛔ I ripieghi di fase — due che pesano e uno minore, dichiarati qui e non solo in un commento

> ### ⭐ E i due che pesano hanno una SCADENZA, decisa dall'utente alla chiusura della fase
>
> *11 agosto 2026, sera. ⛔ Le decisioni stanno in `DECISIONI.md` e qui si rimanda: sotto c'è la
> conseguenza sulla fase, non la decisione.*
>
> | | |
> |---|---|
> | **il filo** | **`DECISIONI.md` §1.10** — ⛔ **si cura PRIMA della fase 2**, e con un **processo aiutante** (PAM non è affidabilmente rientrante). ⭐ A spostare la scadenza dalla fase 5 alla 2 è stato **un numero di B8**: il blocco è di **1,0-2,2 s** a tentativo, ⛔ **e a metterlo è PAM**. Fino alla fase 1 il sintomo è *«l'ultimo dei dieci aspetta»*; **dalla fase 2 in poi è lo schermo di chi sta già lavorando che si pianta quando entra qualcun altro**, e chi lo vede lo attribuisce al video. ⛔ **E la proprietà da provare non è «PAM funziona ancora»**: è *«mentre uno si autentica, gli altri non se ne accorgono»* — e **quel banco oggi non esiste** |
> | **il tetto** | **`DECISIONI.md` §1.11** — ⛔ **resta 16 fisso fino alla fase 3**, di proposito: `SPECIFICHE.md` §5.5 dice di sé che *«il limite vero non è un conteggio, è un budget di pixel al secondo»*, quindi qualunque numero di oggi è un segnaposto. ⚠ **Il prezzo dichiarato**: per due fasi il codice dice **16** e la specifica dice **dieci**. ⛔ E vale per qualunque numero: **nessun banco ha mai visto quel tetto mordere** — riempirlo vuole dieci utenti **diversi** (I2), e il motivo del rifiuto è di fase 3 |

*Rilievo **R12C.17**: stavano scritti in `src/main.c` e `src/rcp.c`, cioè dove non li legge nessuno
che non stia leggendo quel file — mentre `SPECIFICHE.md` §5.5 e `DECISIONI.md` §4.6 promettono dieci
sessioni insieme senza una riga che dica il contrario. ⚠ Un ripiego di fase dichiarato nel codice non
è una promessa rotta: è una promessa **non ancora dovuta**. Ma il posto in cui si scrive è dove la
fase dichiara i propri confini.*

| | |
|---|---|
| ⛔ **un solo filo, e la verifica PAM lo BLOCCA** | tutto gira in un ciclo `poll` solo, e `pam_authenticate` è sincrona: la stretta di mano di un utente **ritarda i pacchetti di chiunque altro**. ⛔ E il secondo fisso di §4.4-bis lo rende misurabile: con dieci utenti che entrano insieme, l'ultimo aspetta **dieci secondi** — e il sintomo, *«il server è lento quando c'è gente»*, non nomina né PAM né il filo. **Prima della fase 5 la verifica va su un filo a parte** |
| ⚠ **sedici sessioni attaccate, in compilazione** | `src/rcp.c`: `#define MAX_ATTACCATE 16`, col commento *«un server vero lo sostituirà con la sua tabella delle sessioni»*. `SPECIFICHE.md` §5.5 dice **dieci, configurabile**: qui è sedici e fisso |
| ⚠ **e un terzo, minore, che vale la pena di nominare adesso** | l'interruttore della funzione di banco di `RCP.md` §7.5 è `#define BANCO_ACCESO 0`. L'invariante **I6** è rispettata — è spenta di suo — ⛔ ma §7.5 la vuole accendibile **nella configurazione del server**, e oggi accenderla richiede di **ricompilare**. Il giorno in cui la configurazione ci sarà, questa è la riga da cambiare |

### I banchi

| | |
|---|---|
| ⭐ `banchi/01-b2-costruisci.sh` | **nuovo**: costruisce BoringSSL e `lsquic` con `-DLSQUIC_WEBTRANSPORT=ON`, e ⛔ **verifica che il flag abbia prodotto i simboli** — non che compili |
| ⭐ `banchi/01-b2-certificati.sh` | **nuovo**: i **due** certificati di `RCP.md` §4.1-bis con quattro controlli — curva, `subjectAltName`, durata sotto i 14 giorni, e ⛔ **che i due siano davvero due** (il difetto di B13.1, colto alla nascita invece che due settimane dopo) |
| ⭐ `banchi/01-b2-controllo-aioquic.py` | **nuovo**: ⛔ **il controllo positivo di B2** — una sessione WebTransport che *deve* riuscire. Senza, «la candidata non apre la sessione» e «il banco non sa aprirne nessuna» hanno lo stesso aspetto (R3.17) |
| ⭐ `banchi/01-b2-cliente-aioquic.py` | **nuovo**: il germe del **cliente di prova** (B9), e il controllo d'ambiente che separa «il server non regge» da «il browser non accetta» |
| ⭐ `banchi/01-b2-sonda.html` | **nuovo**: la pagina, ⛔ **servita da `localhost`** — contesto sicuro senza avvisi, così quel che si misura è **la sessione** e non il clic dell'utente |
| ⭐ `banchi/01-b2-sni-ngtcp2.sh` | **nuovo, 10 agosto**: costruisce `bsslserver`, il server d'esempio di `ngtcp2`, che è il bersaglio della prova SNI. ⛔ **Non guarda l'uscita di `ninja`: guarda se il binario c'è** — `examples/CMakeLists.txt` costruisce quel blocco solo `if(LIBEV_FOUND AND HAVE_BORINGSSL AND LIBNGHTTP3_FOUND)`, e se una manca cmake **salta in silenzio** |
| ⭐ `banchi/01-b2-sonda-sni.py` | **nuovo, 10 agosto**: la sonda del criterio nuovo di `DECISIONI.md` §6.4. Due gambe (senza SNI · con SNI), e ⛔ **due gradini per gamba**: la stretta di mano riesce **e** l'impronta del certificato ricevuto combacia con quella del file |
| ⭐ `banchi/01-b2-sni-quiche.sh` | **nuovo, 10 agosto**: la terza candidata. ⛔ **Due azioni separate — `leggi` e `costruisci`** — perché se leggere e misurare stanno nello stesso comando la previsione la si scrive **dopo** aver visto il risultato, cioè non la si scrive. ⭐ E **sceglie la versione**: confronta il `rust-version` di ogni etichetta col compilatore presente, e dice quale e perché |
| ⭐⭐ `banchi/rcp/rcp.c` + `rcp.h` | **nuovo, 10 agosto**: ⭐ **la stretta di mano di RCP/1 E IL BAN DELL'INDIRIZZO, in C** — `[M]` **11 agosto 2026** (`wc -l` su questo albero, codice fermo alle 00:36): `rcp.c` **2.566 righe / 1.418 di codice**, `rcp.h` **197 / 54**. ⚠ *Diceva «**1292 righe / 875 di codice**, `rcp.h` **131 / 49**», `[M]` delle **ore 16:30 del 10 agosto**, e alle 23:48 il file ne misurava già 2.339: lo scarto era dell'**81 %** — rilievo **R12C.12**. E prima ancora diceva «807 righe, 662 di codice», il conto della mattina. ⛔ **La cura era già in questa tabella, tre righe più giù**, applicata a un numero della stessa natura (la riga del collante di B2, che porta «alle 08:00 la stessa misura dava 456/329»): una cura applicata in un posto solo, dentro la stessa tabella.* ⛔ **E la riga non nominava il ban**, che è il lavoro della notte del 10 — `FINESTRA` di 5 minuti, `BAN_DURATA` di 12 ore, `salva_ban`, `rcp_ban_carica`, `rcp_sblocca`, `rcp_bannato`, la tabella da 256 posti con lo sfratto che non butta mai una voce bannata — cioè la decisione dell'utente del giorno (`DECISIONI.md` §1.9). ⛔ **E questo numero non c'entra con quello dello strato WebTransport**: il protocollo **non dipende da ngtcp2** — riceve byte, restituisce byte, e non entra in nessuna delle misure di collante di B2. ⛔ **Non sa che sotto c'è QUIC**: riceve byte, restituisce byte, e il tempo glielo passa chi lo ospita. È la ragione per cui potrà passare al server vero senza riscritture, e per cui §6.4 — se si riaprisse — non porterebbe via il protocollo |
| ⭐ `banchi/rcp/autenticazione.c` | **nuovo, 10 agosto**: `[M]` **99 righe / 52 di codice** (ore 16:30) — PAM, derivato da `fondamenta/remotix-c/src/autenticazione.c` con ⛔ **la cura di B10** — è caduto il confronto con l'utente del processo, che contraddiceva il multi-tenant di `SPECIFICHE.md` §5.5 |
| ⭐ `banchi/01-b3-rcp-innesta.py` | **nuovo, 10 agosto**: ⛔ **un innesto SEPARATO da quello di B2**, perché quel numero misura WebTransport e farlo crescere con RCP dentro renderebbe due misure diverse sotto la stessa etichetta (E2) |
| ⭐ `banchi/01-b3-cliente.py` | **nuovo, 10 agosto**: **il cliente di prova** — la stretta di mano scritta una seconda volta, in un linguaggio diverso, e **registra** nel formato di §11.1 con la parola d'ordine oscurata |
| ⭐ `banchi/01-b3-lancia.sh` + `01-b3-terzo-giro.sh` | **nuovi, 10 agosto**: le tre connessioni di B3, e ⛔ **ogni traccia passa dal validatore di B4** — non si collauda il server contro il client |
| ⭐⭐ `banchi/01-b3-quarto-giro.sh` | **nuovo, 10 agosto**: l'**orologio del silenzio** — 35 s a `max_idle_timeout` 120, con il controllo a +6 s che dice **no**. ⛔ Senza quel primo tempo, «dopo 35 s la seconda entra» è compatibile con «la seconda entra sempre» |
| ⭐⭐ `banchi/01-b3-quinto-giro.sh` | **nuovo, 10 agosto**: ⚠ **gira da questa parte del filo** — ruota il certificato, riavvia, e prova che la pagina ritira l'**impronta corrente**. ⛔ E che con la **vecchia** non si apre: senza quel controllo, «funziona con la nuova» è compatibile con un browser che l'impronta non la guarda |
| ⭐⭐ `banchi/01-b4-validatore.py` | **nuovo, 10 agosto**: ⭐ **il validatore del filo** — un terzo programma che legge una registrazione e dice **quale byte** non è conforme a `RCP.md`. ⛔ Scritto leggendo **solo la specifica**, prima che esistesse un byte di server. Ha **tre** esiti, non due: conforme · non conforme · ⚠ *registrazione malformata*, perché «il file è rotto» e «il filo non era conforme» sono due fatti con due cure |
| ⭐ `banchi/01-b4-registrazioni.py` + `01-b4-lancia.py` | **nuovi, 10 agosto**: le **sette** registrazioni, ciascuna col **byte offensivo dichiarato in anticipo** in un manifesto — e il confronto lo fa il banco, non chi guarda |
| ⭐ `banchi/01-b2-sonda-trasporto.py` + `01-b2-lancia-trasporto.sh` | **nuovi, 10 agosto**: le sei proprietà, lette **dal pari** con una spia dichiarata su `pull_quic_transport_parameters` di `aioquic`. ⛔ Hanno trovato due difetti che nessun banco funzionale vedeva, e il secondo giro (`--timeout=10s`) misura la proprietà che serve a **B3** |
| ⭐ `banchi/01-b2-sonda-impostazioni.py` | **nuovo, 10 agosto**: legge **sul filo** quali impostazioni un server HTTP/3 dichiara (`received_settings` di `aioquic`), e dice se c'è WebTransport. ⛔ È la prova che ha chiuso §6.4, e stampa **tutte** le impostazioni: un elenco vuoto e uno senza le due che interessano sono due fatti diversi |
| `banchi/01-b2-quiche-wt-innesta.py` + `01-b2-lancia-impostazioni.sh` | **nuovi, 10 agosto**: accendono su `quiche` tutto quel che la sua API C permette (3 righe di codice), e conducono il confronto con `ngtcp2` come **controllo positivo** |
| ⭐⭐ `banchi/01-b2-ngtcp2-wt-innesta.py` | **nuovo, 10 agosto**: ⭐ **il server minimo** — innesta lo strato WebTransport nel server d'esempio di `ngtcp2`. ⛔ Ogni innesto ha un **appiglio che deve comparire una volta sola**: zero o due, e lo script si ferma dicendo quante ne ha trovate. E **conta le righe nostre** da `git diff`, che è il dato di §6.4 |
| ⭐ `banchi/01-b2-lancia-wt.sh` | **nuovo, 10 agosto**: misura il server minimo col cliente di prova, ⛔ **e col controllo che dice no** — `/rcp/9` deve essere rifiutato (`RCP.md` §2.2). `accendi`/`spegni` servono alla misura col browser |
| ⭐ `banchi/01-b2-lancia-sonda.sh` | **nuovo, 10 agosto**: ⚠ **gira sulla macchina di chi guarda, non sul server** — i browser stanno lì. Accende il server dall'altra parte, serve la pagina da `127.0.0.1`, lancia i due motori sotto `xvfb` e aspetta che il **registro cresca**, non un tempo fisso |
| `banchi/01-b2-sonda.html` | **corretto**: `?avvia=1` fa partire la prova da sé. ⛔ Un banco che ha bisogno di una mano **non si può rifare uguale**, e rifarlo uguale è l'unico modo di sapere se una misura è cambiata perché è cambiato il server |
| `banchi/01-b2-raccogli.py` | **corretto**: registra **ogni richiesta**. Prima taceva, «il rumore non serve» — ed è quel silenzio che ha reso indistinguibili «il browser non ha caricato la pagina» e «l'ha caricata e la prova è fallita» |
| ⭐ `banchi/01-b2-lancia-sni.sh` | **nuovo, 10 agosto**: conduce la prova sui **tre** bersagli — `ngtcp2`, `quiche`, e `lsquic` come **controllo negativo** in coda, che a ogni esecuzione ridimostra che la sonda sa vedere un rifiuto. ⛔ Verifica che le porte siano libere **prima**, che i server ascoltino davvero (`ss`, non solo «il processo è vivo»), e li ferma **per PID** |
| `fondamenta/banco/provision.sh` | **corretto**: `libev-dev` fra i pacchetti — è quel che serve agli esempi di `ngtcp2`, ed è **un'altra libreria** da `libevent-dev` che c'era già. ⚠ Senza, cmake mette `LIBEV_LIBRARY-NOTFOUND` e **salta gli esempi senza dire niente** |
| `fondamenta/banco/provision.sh` | **corretto**: `golang-go` fra i pacchetti del contenitore. Serve a compilare BoringSSL, che è la sola pila TLS con cui `lsquic` e `quiche` parlano QUIC. ⛔ Nel provisioning, non a mano (`LEZIONI.md` §2.5-bis) |

> #### ⛔ E i banchi che questa tabella non nominava — undici, contati
>
> *Rilievo **R12C.13**. Questa tabella si fermava a B5 e agli innesti di B2, mentre il README
> dichiarava chiusi B6, B7, B8 e B11 e la notte del 10 ne ha fatti nascere altri quattro. ⛔ La
> regola con cui **R11.21** era stato chiuso sta nel `README.md` e vale identica qui: «un banco che
> non è nominato dove si dice come rimettere in piedi i banchi **non si può rifare uguale**», e
> rifarlo uguale è l'unico modo di sapere se una misura è cambiata perché è cambiato il server.
> Aggiunti l'11 agosto 2026.*
>
> | | |
> |---|---|
> | `banchi/01-b6-lancia.sh` + `01-b6-tetti.py` | **B6**, i tre tetti di §4.6. ⭐ Legge i `#define TETTO_*` **da tutt'e due** le copie del sorgente — quella dei banchi e quella compilata — e pretende che combacino, «perché una copia stantia darebbe un numero che nel binario non c'è». ⭐ E ha **tre esiti separati**: il server sbaglia · il **documento** sbaglia · non ho saputo classificare |
> | `banchi/01-b7-lancia.sh` + `01-b7-congedo.py` | **B7**, il congedo dal lato che riceve. ⛔ Dichiara il **denominatore vero**: §8.2 ha **quindici** motivi, i provocabili in questa fase sono **sette**, e gli altri otto stanno in una tabella `ESCLUSI` con la ragione di ciascuno |
> | `banchi/01-b8-lancia.sh` + `01-b8-cronometro.py` + `01-b8-prova-ban.c` + ⭐ `01-b8-sblocca.py` | **B8**, il secondo fisso e il ban. ⭐ `01-b8-sblocca.py` **non è un pezzo di B8**: è lo strumento della regola **B0.3**, e parla il socket di comando di §4.4-bis con tre esiti distinti (`TOLTO` · `NON-BANNATO` · «non ho parlato con nessuno», che esce **3**) |
> | ⭐ `banchi/01-b9-letture.py` | **B9**, il secondo lettore messo a confronto con l'arbitro: **dodici** punti in cui `RCP.md` ammette due letture, ciascuno con **i byte che cambiano sul filo**. L'elenco sta in «Che cosa NON ha funzionato» |
> | `banchi/01-b11-lancia.sh` + `01-b11-pagina.html` + `01-b11-guasto.sh` + `01-b11-guasto-innesta.py` | **B11**, le violazioni verso la **pagina**, col server guasto di proposito e `ricostruisci()` che rimette quello sano nei due `--togli` nell'ordine |
> | `banchi/01-b12-guasti.py` + `01-b12-lancia.sh` + `01-b12-copie/` + `01-b12-registro.jsonl` | **B12**, il banco che certifica gli altri: un guasto costruito a mano per ogni banco, e il registro delle certificazioni con la data e le impronte. ⛔ Quel che ha certificato davvero sta più sotto, ed è **3 su 12** |
> | `banchi/01-b13-lancia.sh` + `01-b13-proprieta.py` | **B13**, le sei cose che nessun altro banco guardava |
> | `banchi/01-c2-lancia.sh` + `01-c2-diagnosi.py` | **C2**, le tre diagnosi del collegamento guasto — nessuno in ascolto · UDP filtrato col TCP che risponde · impronta non corrente |
> | ⭐ **le sette pagine della sonda** | `01-s1b-eccezione.sh` + `01-s1b-pagina.html` + `01-s1b-sito.sh` + `01-s1b-servi.py` (**S1b**, l'orologio dei sette giorni) · `01-s2-pagina.html` (**S2**) · `01-s3a-pagina.html` (**S3a**) · `01-s5-tela.sh` + `01-s5-pagina.html` + `01-s5-raccogli.py` (**S5**) · `01-s6-pagina.html` (**S6**) · `01-s7-rotella.sh` + `01-s7-rotella.c` + `01-s7-pagina.html` + `01-s7-raccogli.py` (**S7**) · `01-s-telefono.sh` (le procedure che aspettano un dispositivo) |
>
> ⚠ **E i registri che quei banchi lasciano**, perché un banco senza il suo registro non è
> riverificabile: `banchi/01-s7-esiti.jsonl` · `01-s5-esiti.jsonl` · `01-s1b-stato.jsonl` ·
> `01-b12-registro.jsonl` · `b2-esiti.jsonl`. ⛔ **B6, B7, B8, B11, B13 e C2 non ne hanno nessuno**:
> i loro numeri vivono nell'uscita a schermo del giro, e quando la scena è smontata non ci si torna.

**Si riusa** (`PIANO.md` fase 1): `autenticazione.c` di v1 (144 righe) — ⛔ **con la cura di B10**,
e quel che ne è uscito misura **99 righe / 52 di codice** `[M]` — e `registro.c` (140) — ⚠ **con
l'obbligo di B13.2**.

---

## Le misure

*⛔ Con la scena, il dispositivo e la **versione** dichiarati accanto a ogni numero (B0.6).*

#### La sonda

⛔ **Gli esiti per esteso, con i registri e la ricontata dei numeri, stanno in
`web/rapporti/S-esiti-sonda.md`** — qui c'è il numero con la
data, come vuole B0.6. ⚠ *Fino all'11 agosto 2026 queste sei celle erano **vuote** mentre tre delle
misure erano state prese la notte del 10: chi leggeva questo documento credeva che la misura non ci
fosse (rilievi **R12.7** e **R12C.7**, e la sonda lo aveva scritto di suo — voce S.6 del suo §9).*

| # | Che cosa | Dispositivo · versione | Atteso | Misurato | Data |
|---|---|---|---|---|---|
| S1b | durata dell'eccezione su Chrome | **Chrome 151.0.7922.108**, profilo persistente, `Xvfb :77 1280x1024x24` | **7 giorni** `[R]` | ⏳ **AVVIATA — giorno 0 preso.** Chrome si è segnato la scadenza **2026-08-17T21:09:47.889Z** `[M]` (grezzo su disco, conversione dichiarata). ⚠ `[?]` **che siano 604 800 s esatti dal clic**: l'istante del clic non l'ha registrato nessuno. Il numero sul campo si legge **il 17-18 agosto** | **10 ago**, 21:10:01Z |
| S2 | HEVC Main10 **in hardware** | ✅ telefono + PC per `chrome://inspect` | `[?]` — ⛔ *non «sì da Chrome 108»* | ⛔ **non eseguita**: manca il telefono, manca il PC per il controllo C, e le cinque sequenze dipendono dal codificatore della **fase 2**. ⭐ Banco pronto: `01-s2-pagina.html`, e finché A e B non passano **non pubblica verdetti** | |
| S3a | tastiera, nei tre stati di O8 | ✅ DeX — ⚠ `[?]` **verificare che sia ≥ Android 16 QPR1** | `[?]` | ⛔ **non eseguita**: manca il DeX. ⚠ E una riga di S3 §4.4 non è eseguibile **nemmeno col DeX**: `requestFullscreen({keyboardLock})` vuole **Firefox ≥ 151** e questa macchina ha la **140.13.0esr** — chi provasse qui misurerebbe l'assenza della lock e la scambierebbe per scorciatoie perdute | |
| S5 | tela dichiarata, zoom 100 %/150 % | **Chrome 151.0.7922.108** e **Firefox 140.13.0esr** su `Xvfb 1920×1080×24` (⛔ il **DeX** manca) | **uguale nei due**, e = risoluzione fisica | ⛔ **I DUE MOTORI NON CONCORDANO.** Firefox: `screen` 1280×720 a 150 % ⇒ tela **1920×1080**, invariante ✅. Chrome: `screen` resta 1920×1080 ⇒ tela **2880×1620**, del **50 % più grande** ⛔. `[M]`, due giri identici, `01-s5-esiti.jsonl`. ⇒ la formula di `SPECIFICHE.md` §6.1-bis **non regge su Chrome** | **10 ago**, 23:13-23:14 |
| S7 | segno della rotella, `natural-scroll` nei due stati | **server 192.168.0.2**, GNOME headless, **libmutter 48.7-0+deb13u1**, **libei 1.3.901**, **Firefox 140.13.0esr** in `--kiosk` | `[?]`, e **non deve cambiare** con la gsetting | ⭐ **`+120` → `deltaY +114`, la pagina SCENDE** ⇒ ⛔ **il server inverte l'asse verticale**. `[M]`, due giri, `01-s7-esiti.jsonl`. Il segno **non cambia** fra i due giri ⚠ (`[?]` che fossero i due stati di `natural-scroll`: l'etichetta non è nel registro). ⛔ Misurata **su Mutter**: per gli altri quattro desktop resta `[?]` | **10 ago**, 20:59 UTC |
| S6 | carico utile di un datagram, **sul percorso peggiore** | ✅ telefono su LTE | ≥ **972 byte** | ⛔ **non eseguita**: manca una LTE vera e manca la metà di server che faccia l'**eco** dei datagram. ⭐ Banco pronto: `01-s6-pagina.html`, che **si rifiuta di misurare senza `?percorso=`** | |
| ⛔ S1a | eccezione ⇒ WebTransport su Safari | ⛔ **niente Mac** | *fuori dalla fase, resta `[?]`* | | |
| ⏳ S3b | PWA su Chrome per Android | ⛔ + certificato vero | *rimandata* | | |
| ⏳ S4 | anello del ritardo del disegno | | *→ fase 3* | | |

#### Il filo

⚠ *Tre `[M]` di **B3** — la 2ª mentre la 1ª è viva, l'orologio del silenzio, la 3ª col certificato
ruotato — stavano in questa tabella **senza la cella della data**, in un capitolo che apre
imponendola: rilievo **R11.17**. La data c'è dal 10 agosto 2026, e la cella mancante non era
formalismo — `[M]` è definito come «misurato da noi, sul ferro, **con la data**» (`README.md`), e
la riga della 3ª è quella che dichiara un esito su **due browser**, cioè quella che B0.6 nomina per
prima.*
⚠ *E la stessa cura è dovuta tornare l'11 agosto 2026, tre righe sotto quel riquadro: la riga di
**B8** portava il suo `[M]` nella colonna dell'**atteso**, con «Misurato» e «Data» vuote e il «10
ago» dentro il testo invece che nella cella — rilievo **R12C.14**. ⛔ Il controllo meccanico che
aveva trovato R11.17 (contare le `|`) qui **non vede niente**: le celle sono cinque su tutte le
righe, e il difetto è nel loro **ordine**. Cioè la cura era stata applicata alla forma che il rilievo
descriveva e non alla proprietà che il rilievo proteggeva — che è, di nuovo, «una cura applicata in
un posto solo».*

⛔ **E la scena, che B0.6 pretende accanto a ogni numero**: i giri **1-4** di B3 li fa il cliente
`banchi/01-b3-cliente.py` contro il server minimo su `ngtcp2`, sulla macchina di prova — **nessun
browser**, quindi nessuna versione di browser da annotare; il **quinto** (certificato ruotato) è
l'unico coi browser veri, e le loro versioni sono dentro la riga.

| Che cosa | Atteso | Misurato | Data |
|---|---|---|---|
| **B2** — BoringSSL compila nel `devroot` | sì | ✅ **sì** — ramo predefinito, `libssl.a` e `libcrypto.a` | 9 ago |
| **B2** — `lsquic` compila con `-DLSQUIC_WEBTRANSPORT=ON` | sì | ✅ **sì**, v4.9.3, e la define è nei `FLAGS` di `build.ninja` | 9 ago |
| ⛔ **B2** — **il flag ha prodotto i simboli?** | **4 su 4** | ⭐ **4 su 4** `[M]` — dopo aver curato il banco, vedi sotto | 9 ago |
| **B9** — `aioquic` porta WebTransport? | `[?]` | ⭐ **sì** `[M]` 1.2.0: 29 occorrenze nel modulo h3, l'evento e `create_webtransport_stream`. *Era la `[?]` di R3.21: se fosse stata «no», cadeva l'arbitro* | 9 ago |
| **B2** — i due certificati, quattro controlli | 4 su 4 | ✅ **4 su 4** — e i due sono davvero due | 9 ago |
| ⭐ **B2** — **il controllo positivo d'ambiente** (senza browser) | sessione accettata **e** byte che tornano | ⭐ **`:status = 200`, `b'ciao'` torna identico** `[M]` | 9 ago |
| ⭐ **B2** — **la sessione si apre da un BROWSER VERO** | si apre, e i byte tornano | ⭐ **APERTA in 30,2 ms** su **Chrome 151.0.0.0** (X11, Linux), `"ciao"` torna identico `[M]` | 9 ago |
| ⭐ **B2** — lo stesso su **Firefox** | si apre | ⭐ **APERTA in 52,0 ms** su **Firefox 140.0**, `"ciao"` torna identico `[M]` | 9 ago |
| ⭐ **B2** — ⛔ **`ngtcp2` serve il certificato SENZA SNI?** | **sì** (previsione scritta prima: zero ricerche per nome in 109+18 file) | ⭐ **sì** `[M]` — sessione stabilita, e **l'impronta del certificato ricevuto combacia** con quella del file | 10 ago |
| **B2** — lo stesso con SNI, il controllo | sì | ✅ **sì** — `remotix.prova` | 10 ago |
| ⭐ **B2** — ⛔ **`quiche` serve il certificato SENZA SNI?** | **sì** (previsione scritta prima: l'unico punto che nomina l'SNI è un **lettore**, `tls/mod.rs:510`) | ⭐ **sì** `[M]` su **`quiche` 0.28.0** — sessione stabilita, **impronta combaciante** | 10 ago |
| **B2** — lo stesso con SNI, il controllo | sì | ✅ **sì** | 10 ago |
| ⛔ **B2** — quale `quiche` si costruisce con `rustc` di Trixie? | *non era una domanda* | ⛔ **la 0.28.0**: la **0.29.3 pretende rustc 1.88**, Trixie ha **1.85** `[M]` | 10 ago |
| ⭐ **B2** — il **controllo negativo**: `lsquic` senza SNI | **fallisce** | ⭐ **fallisce** `[M]`, e il suo registro dice **perché**: `SNI is not set … fail certificate lookup` | 10 ago |
| ⭐ **B2** — `lsquic` **con** SNI: trova il certificato? | sì — *la metà che mancava alla diagnosi del 9* | ⭐ **sì** `[M]`: `looked up cert for remotix.prova`. ⚠ poi cade su ALPN (avviso 120), **causa non indagata** | 10 ago |
| ⭐⭐ **B2** — **la sessione si apre da un BROWSER VERO, su `ngtcp2`** | 2 motori su 2 | ⭐ **2 su 2** `[M]`: **Chrome 151.0.0.0** (118,6 ms) e **Firefox 140.0** (140,0 ms), impronta pubblicata, nessun avviso, `"ciao"` torna identico | 10 ago |
| ⛔ **B2** — e il percorso **sbagliato** si rifiuta? | non 200 | ⭐ **404** su `/rcp/9` `[M]`, come impone §2.2 (R1.24) | 10 ago |
| ⭐ **B2** — le sei proprietà della libreria | 6 su 6 | ⭐ **6 su 6** `[M]`, e **lette dal pari, non dal registro del server**: `max_idle_timeout` 30 000 ms · datagram 65 536 · credito uni **16** · migrazione **non** disabilitata · **niente 0-RTT** · `allowPooling: false` | 10 ago |
| ⛔ **B2** — e il tetto d'inattività si può **cambiare**? (serve a B3) | il pari vede il valore nuovo | ⭐ **sì** `[M]`: con `--timeout=10s` il pari legge **10 000 ms**. B3 potrà distinguere il tetto del protocollo da quello del trasporto | 10 ago |
| ⛔ **B2** — ⭐ **due difetti trovati proprio da queste misure** | *nessuno era atteso* | ⛔ il server offriva **0-RTT** (2 biglietti, `max_early_data_size` 0xffffffff) e concedeva **3** stream unidirezionali invece di 16. **Nessuno dei due ha un sintomo funzionale**: la sessione si apriva uguale | 10 ago |
| ⛔⭐ **B2** — **`quiche` riesce a dichiarare WebTransport dal C?** | **no** (previsione scritta prima: `set_additional_settings` esiste in Rust, **non nell'FFI**) | ⛔ **no** `[M]`: 4 impostazioni sul filo, **nessuna** delle due di WebTransport. Il controllo positivo (`ngtcp2`) ne dichiara 7 | 10 ago |
| **B2** — la sessione si apre, **per candidata** | 2 motori su 2, **e le sei proprietà** | ⭐ **fatto su `ngtcp2`**; su `quiche` **non si arriva a provarlo**: cade al cancello prima | 10 ago |
| ⭐ **B2** — righe di collante **per lo strato WebTransport** | *si conta, non si stima* | ⭐ **`ngtcp2`, lo strato di B2 da solo: 553 righe aggiunte — 373 di CODICE, 134 di commento, 46 vuote** `[M]` **ore 16:30**, su albero pulito dopo i due `--togli` e riapplicando il solo innesto di B2. ⚠ *Alle 08:00 la stessa misura dava **456 / 329**: la lettura della capsula di chiusura è cresciuta lì dentro. La successione sta in `DECISIONI.md` §6.4, non qui.* ⛔ **I 972 / 618 dei due innesti insieme non vanno in questa riga.** ⚠ Su `quiche` il numero **non esiste e non esisterà**: la candidata cade prima, ed è il lavoro che non abbiamo speso | 10 ago |
| **B2** — quanto pesa il loro esempio (il punto di partenza) | *si conta* | `ngtcp2` **7.041 righe** (HTTP/3 completo, C++, 13 file) · `quiche` **614** (esempio minimo, C, 1 file) `[M]`. ⛔ Due etichette diverse: non si sottraggono | 10 ago |
| ⭐ **B3** — la **1ª** connessione, fino a `SESSIONE` | passa | ⭐ **passa** `[M]` 10 ago: `CIAO`→`ECCOMI`→`CREDENZIALI`(PAM)→`AMMESSO`→`ATTACCA`→`SESSIONE`, e ⛔ **la traccia è dichiarata CONFORME dal validatore di B4** | 10 ago |
| ⭐ **B3** — la **2ª dopo la chiusura della 1ª** | **identica alla prima** | ⭐ **passa** `[M]`, e anche la sua traccia è conforme. ⛔ **Non lo era al primo giro**: vedi il difetto qui sotto | 10 ago |
| ⭐ **B3** — la **2ª mentre la 1ª è viva** | `CONGEDO(0x0F)` a chi arriva, e la 1ª sopravvive | ⭐ **passa** `[M]`: la seconda riceve `GIA_ATTIVA_REMOTA` **per tutt'e due le strade di §3.1** — `CONGEDO` sul controllo *e* codice `0x0f` nella chiusura della sessione — e la prima sopravvive. ⚠ *Era rossa al primo giro, e il difetto era del banco* | 10 ago |
| ⭐⭐ **B3** — la 2ª **dopo il silenzio** della 1ª, 35 s a `max_idle_timeout` **120** | **entra** | ⭐ **entra** `[M]`, e ⛔ **con il controllo che dice no**: a **+6 s** la seconda è **rifiutata** con `0x0F`, a **+35 s** la terza **entra**. Il registro: `STACCATO per silenzio: 30072 ms`. ⭐ E la connessione della prima è **ancora viva**: a liberare il posto è stato **il server**, non QUIC | 10 ago |
| ⭐ **B3** — la 3ª con il certificato **ruotato a mano** | passa | ⭐ **PASSA, pieno** `[M]` **2026-08-10 sera**: rotazione (impronta nuova ≠ vecchia, quattro controlli sui certificati su quattro), la pagina ritira la nuova e apre su Chrome 151 e Firefox 140, **e il server risponde `ECCOMI` al `CIAO` della sonda** — la seconda metà del criterio di B2 è soddisfatta —, e con la vecchia **tutt'e due rifiutano**. ⛔ Il rosso del mattino era della SONDA, non del certificato: mandava `ciao` e aspettava l'eco di B2, che con RCP innestato non esiste più. ⚠ Resta `[?]` che a rifiutare sia il confronto dell'impronta e non una delle altre due cause con lo stesso aspetto.<br><br>*Quel che diceva prima* `[M]` **2026-08-10 09:36**, Chrome **151.0.0.0** e Firefox **140.0**: con l'impronta corrente (`5o99/7rSTJER…`) la **sessione si apre** su tutt'e due — 149,0 ms Firefox, 180,0 ms Chrome — ⛔ **ma lo stream non ha funzionato in nessuno dei due** (`remote WebTransport close` · `The session is closed.`), e il criterio di B2 vuole *«la sessione si apre su Chrome e Firefox, **e la pagina riceve un byte dal server**»*. ⚠ Con l'impronta vecchia (`35wqjGTOmKSj…`) **tutt'e due rifiutano** — Firefox `WebTransport connection rejected`, ⚠ Chrome `Opening handshake failed.`, *due frasi diverse* — ma `[?]` **che a rifiutare sia il confronto dell'impronta non è dimostrato**: l'esito registrato dichiara di suo **tre cause con lo stesso aspetto** (UDP filtrato · impronta non del certificato servito · certificato oltre i 14 giorni), e nessuno le ha distinte. È la forma **E1**, e il banco l'aveva già dichiarata | 10 ago |
| ⭐ **B3** — il **secondo fisso** di §4.4-bis, cronometrato | ≥ 1000 ms **anche su `AMMESSO`** | ⭐ **1074–1085 ms** `[M]` su tre connessioni. È una proprietà che nessun altro banco vede | 10 ago |
| ⭐ **B10** — PAM, con `pamtester` come controllo | entra | ⭐ **entra** `[M]`: `pamtester login prova authenticate` riesce, e il server ammette lo stesso utente | 10 ago |
| ⭐ **B4** — sette guaste, quattro rotte, una conforme, una senza niente da giudicare | i **quattro esiti** coperti, byte esatto | ⭐ **13 su 13** `[M]` 10 ago sera: ciascuna guasta accusata sul **byte dichiarato in anticipo**, e i quattro codici d'uscita del validatore tutti esercitati (0 conforme · 1 non conforme · 2 registrazione rotta · 3 niente da giudicare). Il validatore è **certificato** | 10 ago |
| ⭐⭐ **B4** — e ha trovato una contraddizione in `RCP.md` | *non era un atteso* | ⛔ §4.3 vietava il trattino basso nei nomi di capacità **e ne definisce uno che ce l'ha** (`video.misura_massima`). Curato in `RCP.md` §4.3 | 10 ago |
| ⭐⭐ **B5** — le violazioni, e il server vivo dopo ciascuna | motivo giusto sempre, **server vivo sempre** | ⭐ **36 violazioni su 36 + 8 verdi attesi su 8** `[M]` 10 ago sera, e per **tutt'e due le strade di §3.1** ogni volta — ⛔ **36 su 36 anche sul punto 3**, che nessuno aveva mai contato: `CONGEDO` sul controllo *e* il codice del motivo nella chiusura della sessione. ⛔ E dopo **ciascuna** una connessione nuova arriva a `ECCOMI`: il server è sempre lì | 10 ago |
| ⭐ **B5** — i cinque casi che **devono passare** | *nessuna caduta* | ⭐ **5 su 5** `[M]`: `hevc,vp9` sceglie `hevc` e scrive lo scarto · **vista 300×801** e **1×1** passano (§7.1, R4.10) · `BANCO_MARCA` a funzione spenta risponde `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` e **la sessione regge** · `ritardo_ms = 20000` → `RITARDO_FUORI_LIMITI`, **non** `ERRORE_PROTOCOLLO`. ⛔ Senza di loro «il server chiude su tutto» darebbe 44 verdi su 44 | 10 ago |
| ⭐⭐ **B5** — e ha trovato **un difetto che nessun altro banco vedeva** | *non era un atteso* | ⛔ il contatore **per indirizzo** di §4.4-bis era chiavato sulla `provenienza`, che contiene **la porta**: con un solo tentativo per connessione (§4.4) la porta cambia ogni volta, e quel contatore **valeva sempre 1**. Codice presente, che sembrava giusto, e che non faceva niente. Curato, e ora al **sesto** tentativo scatta `TROPPI_TENTATIVI` — anche per la parola d'ordine **giusta**. ⚠ *Il **sesto** è della regola di quel giorno; dal 10 agosto sera la regola è il **ban al quarto** (`DECISIONI.md` §1.9), e questa riga resta com'è perché una misura porta la data della regola che misurava* | 10 ago |
| ⭐ **B5** — e una **seconda contraddizione in `RCP.md`** | *non era un atteso* | ⛔ §2.2 dice che un `CIAO(2)` su `/rcp/1` è `VERSIONE_INCOMPATIBILE`; §9 dice che il server sceglie *«la più alta che non superi quella del `CIAO`»*, cioè `ECCOMI(1)`. **Byte diversi sul filo per lo stesso ingresso**, e nessuna delle due cita l'altra. Vince §2.2 (la più specifica); `RCP.md` §9 curata. ⚠ *La cura citava **§2.4**, che è «La porta»: numero corretto lo stesso giorno, rilievo **R11.2*** | 10 ago |
| ⭐⭐ **B11** — le violazioni verso la pagina | 13 su 13 | ⭐ **13 su 13 su TUTT'E DUE i motori** `[M]` 10 ago sera — Firefox **140.0** e Chrome **151.0.0.0**, `CONFORME` con **0 guasti** — **più le due proprietà negative** (`desktop` non cambia i byte usciti · nessun battito applicativo). ⭐ **E ripetuto**: due giri completi conformi, `15:51:54`+`15:52:28` e `15:54:51`+`15:55:24`. ⚠ *Alle 11 questa riga diceva «12 su 12 su Firefox, 9 su 12 su Chrome»: i tre rossi di Chrome sono stati chiusi la sera stessa, e questo documento era rimasto indietro fino al rilievo **R11.4** del 10 agosto* | 10 ago |
| ⛔ **B11** — e il controllo che dice **no** | la pagina contro un server **SANO** deve dire NON-CONFORME | ⭐ **NON-CONFORME** `[M]`, **9 casi su 13** falliti. Senza, «tredici verdi» sarebbe compatibile con una pagina che approva qualunque cosa. ⚠ `[?]` **gira su un motore solo** (Firefox), e il banco lo dichiara di suo — **rilievo R11.24**. ⭐ *Dalla notte del 10 agosto 2026 lo dichiara anche il `README.md`, che prima lo elencava dentro «su tutt'e due i motori»: resta da **eseguirlo anche su Chrome**, e la differenza morde proprio qui, perché i tre casi rossi di stasera vivevano **nella differenza fra i due motori*** | 10 ago |
| **B6** — i tre tetti | 5 s · 60 s · 10 s, **col motivo giusto** | ⚠ **5,0 · 60,1 · 10,0 s**, e ⭐ **il cronometro parte dall'apertura del CANALE DI CONTROLLO** — R3.27 chiusa, `RCP.md` §4.6 riga 1 cambiata di una parola. ⛔ **E una seconda risposta**: la sessione che il canale non lo apre mai **non ha addosso nessun tetto** (`DECISIONI.md` §7.17). ⛔ **Questi tre numeri non hanno un registro**: non esiste nessun `.jsonl` di B6, la scena di quel giro non è dichiarata da nessuna parte e **non sono riverificabili** — si rifanno col registro, o restano tre numeri di cui si sa solo l'ordine di grandezza | **10 ago**, ora non registrata |
| **B7** — i motivi dal lato che riceve, frasi distinte, nessun numero | ⛔ **7 provocabili su 15 dichiarati** + **15 frasi distinte** | ⭐ **7 su 7 + 15 su 15**, con gli **otto esclusi** e la ragione di ciascuno. ⚠ *L'atteso di questa riga diceva «**8 su 8** + 8 frasi distinte», e l'ottavo — `SERVER_IN_CHIUSURA` — è quello che il banco **misura** di non poter produrre sull'innesto* | **10 ago** |
| **B8** — ≥ 1 s per campione, **e le tre mediane indistinguibili** | ≥ 1 s in **ogni** campione, e le tre mediane **indistinguibili** fra loro | ⚠ **parziale**: **2636 ms** di mediana sui **42** tentativi respinti, dove §4.4-bis vuole ~1000 ⇒ ⛔ **a governare i tempi è PAM, non il nostro ritardo fisso**. Le tre mediane **restano da confrontare**. ⚠ E il numero è la mediana **del servizio `login`**: il prodotto usa `remotix`, quindi con lui **la misura va rifatta** | **10 ago** |
| ⛔ **B8** — il ban: tre falliti con **tre nomi diversi**, poi il quarto con la parola **giusta** | il quarto **rifiutato** con `TROPPI_TENTATIVI`, e la pagina lo dice | | |
| ⭐ **B8** — i tre controlli che dicono *no* | un **altro** indirizzo entra · **2 falliti · 1 riuscito · 2 falliti** non banna · il ban **sopravvive al riavvio** | | |
| **B8** — lo sblocco, in fondo al giro | l'indirizzo rientra, e lo sblocco è **nel registro** | | |
| **B9** — `aioquic` porta WebTransport; la stretta di mano completa | sì; e **l'elenco delle ambiguità trovate** | ⭐ **12 punti su 12**, ciascuno con le due letture, la lettura che il secondo lettore ha scelto, **i byte che cambiano sul filo** e il caso concreto in cui la differenza morde. L'elenco sta in «Che cosa NON ha funzionato» — ⛔ **sono difetti del documento, non del banco** | **10 ago** |
| **B10** — l'utente `prova` entra, con `pamtester` come controllo | entra | ⭐ **entra** — vedi la riga di B10 qui sopra | **10 ago** |
| **B13** — le sei cose | 6 su 6 | ⛔ **non certificato**: il guasto costruito per lui **non è quello giusto** (accende il server con l'altro certificato, che B13.1 non guarda perché legge le impronte dei **file su disco**), e l'orchestratore non lo sa nemmeno innestare. `[M]` B12, 10 ago 22:24 e 22:25 | **10 ago** |
| **C1** — dodici guasti costruiti a mano | **12 rossi su 12** | ⛔ **3 su 12**, e le parole giuste per gli altri: vedi il riquadro «Che cosa B12 ha certificato davvero» | **10-11 ago** |
| **C2** — tre modi di fallire | **tre diagnosi diverse** | ⭐ **certificato** `[M]` 10 ago 22:32 (macchina `NIC-OS`), con una marca **discriminante**. ⚠ Un giro precedente (22:28) lo dava **non certificato**: fra i due è cambiato il file, non il verdetto — l'impronta di `01-c2-diagnosi.py` è diversa nelle due righe | **10 ago** |

---

## ⛔ Che cosa NON ha funzionato

*Si riempie anche quando fa una brutta figura* (`PIANO.md` §0.3 regola 2). ⭐ **E qui va ogni punto
in cui `RCP.md` ha ammesso due letture**: sono difetti del documento, e questa è la fase in cui
costano meno.

### ⭐⭐ I dodici punti in cui `RCP.md` ammette due letture — B9, 10 agosto 2026

*È **l'esito più prezioso di B9**, e questa sezione lo dichiarava in anticipo: «l'esito più prezioso
non è "passa": è ogni punto in cui chi lo scrive ha dovuto scegliere perché `RCP.md` ammetteva due
letture». `banchi/01-b9-letture.py` li ha trovati e li tiene con **gli appigli citati alla lettera**
— una citazione che non si trova più è una voce che parla di un altro documento — e con **i byte che
cambiano sul filo** fra l'una e l'altra. ⛔ Portati qui l'11 agosto 2026: finché stavano solo nel
banco, erano dodici difetti del documento che il documento non sapeva di avere.*

⛔ **Perché la colonna dei byte è quella che conta**: due letture che producono gli stessi byte sono
una questione di gusto. Queste **producono byte diversi per lo stesso ingresso**, cioè due
implementazioni conformi a `RCP.md` divergono senza che nessuna delle due abbia torto — che è
esattamente ciò che §0 esiste per impedire.

| # | Dove | La domanda | Che cosa ha scelto il secondo lettore | ⛔ Il byte che cambia |
|---|---|---|---|---|
| **L1** | §4.3 | `ECCOMI` porta **l'elenco** dei codec del server o **la scelta**? | ⚠ nessuna delle due: legge i due byte della versione e **butta il resto** — la lettura A **per omissione**, cioè la scelta fatta senza accorgersi di sceglierla | il valore di `video.codec`: `0008 «hevc,av1»` contro `0004 «hevc»`, e con lui la `lunghezza` u32 |
| **L2** | §3.1 punto 3 | il codice d'errore della chiusura: il motivo **nudo** nei 32 bit, o **mappato** come vuole HTTP/3? | A — e ⛔ **in più tronca**: legge l'**ultimo dei quattro byte**, quindi un codice sopra 255 gli arriverebbe come **un altro motivo**, senza una riga che lo dica | `00 00 00 0D` contro otto byte di un valore mappato — e la capsula cambia lunghezza. ⚠ `RCP.md` **non dichiara la larghezza del campo in nessun punto** |
| **L3** | §3.1 p. 2 contro §4.2 | dopo il `CONGEDO`, il canale si chiude **con un FIN** o si chiude solo la sessione? | B — non manda mai il FIN; e dal lato che riceve chiama il FIN *«il canale si è chiuso»*, che è un esito **diverso** da «sessione chiusa dal server» | il **bit FIN** del frame STREAM che porta il `CONGEDO`: gli stessi byte di carico, un bit di trasporto in più |
| **L4** | §6.1 | byte in più in coda al corpo, con la `lunghezza` che li conta: **violazione** o **riserva** per il futuro? | ⛔ **i nostri due lettori hanno scelto DIVERSAMENTE**: il cliente di prova legge `lunghezza` byte e passa il corpo così com'è (B, tollerante); il **validatore di B4** ha una registrazione apposta per bocciarlo (A) | quattro byte in coda e la `lunghezza`: `0000002A` contro `0000002E`. ⛔ È il difetto che B9 esiste per trovare: **l'arbitro e il secondo lettore non leggono la stessa specifica** |
| **L5** | §4.3 | una capacità **assente** è un elenco **vuoto** (⇒ `NIENTE_IN_COMUNE`) o una cosa **non negoziata**? | ⚠ **la domanda l'ha evitata**: dichiara sempre tutte e otto le capacità, quindi nessuna sua esecuzione la farà mai emergere | il campo `quante`: `0003` contro `0002`, e ventidue byte in meno |
| **L6** | §4.6 riga 1 | da quale istante parte il primo tetto? | ⛔ **ha scelto B6**, che lo fa partire dall'apertura del canale — ed è una scelta **del banco**, non del documento | ⛔ **nessuno, e va detto invece di inventarne uno**: le due letture mandano lo stesso `CIAO`. Cambia **quando** arriva il `CONGEDO(TEMPO_SCADUTO)` — e nel caso della sessione senza canale, **se** arriva. ⇒ `DECISIONI.md` §7.17 |
| **L7** | §2.2 | la `CONNECT` estesa deve portare un `origin`? | A — **lo manda**, copiando il browser. ⚠ È prudente e ha un prezzo: mandandolo, **non può più scoprire** se il server lo pretenda — l'arbitro si è adattato all'imputato | il campo `origin` nell'intestazione della `CONNECT`: una riga in più, compressa da QPACK |
| **L8** | §4.5 | un `desktop` fuori dai sei nomi: **campo fuori intervallo** (§3) o **stringa di diagnosi** da non guardare? | B — lo stampa e non lo controlla | la stringa in fondo a `SESSIONE`: `0005 «gnome»` contro `0007 «plasma6»` — e la connessione che sopravvive o cade. ⚠ **Le due letture stanno in sei righe, una sotto l'altra, e sono opposte** |
| **L9** | §11.1 contro §6.0 | nella registrazione, che cosa si scrive in `stream` quando l'identificatore non si conosce? | ⛔ **sempre zero** — ma §6.0 vieta i valori sentinella impliciti, e **zero è un identificatore di stream legale** (è quello della `CONNECT`) | gli otto byte di `stream`: `…04` contro `…00`. ⚠ E il validatore **non se ne può accorgere**: un campo sempre zero e un campo assente hanno lo stesso aspetto — forma **E8** |
| **L10** | §8.1 contro §4.4 | il client, dopo un `RESPINTO`, deve mandare `CONGEDO`? | ⚠ **una terza cosa**: non manda mai un `CONGEDO`, in nessun caso — cioè **non esercita mai** l'obbligo che §8.1 mette su chi chiude | un'inquadratura di **undici byte** contro **il silenzio**. ⛔ Il caso è già costato un rosso: il server contava come «byte dopo la fine» anche il congedo **conforme** della pagina |
| **L11** | §9 contro §2.2 | che versione mette nel `CIAO` un client che ne sa parlare **due**, su `/rcp/1`? | ⚠ scrive `1` a mano perché ne sa parlare una sola: **la domanda non gli si è posta**, e non se la porrà finché RCP/2 non esisterà | i due byte di `versione`: `0002` contro `0001` — e una connessione che vive o muore |
| **L12** | §4.5 contro §7.1 | i limiti 320×240-7680×4320 e la parità valgono anche per `vista_*` dentro `ATTACCA`? | ⚠ manda **vista = tela**: ancora una volta la domanda evitata, non risposta | `vista_larghezza`/`vista_altezza`: `00000780 00000438` contro `0000012C 00000321` (sotto il minimo e dispari). ⭐ **La risposta esiste ed è B**, ma sta in **§7.1** — chi implementa `ATTACCA` leggendo §4.5 non ha nessun motivo di andarci |

⛔ **Che cosa se ne fa**, e non è «si sistemano tutte adesso»: **tre** di queste dodici sono già
domande aperte dove le decisioni stanno — L3 in `DECISIONI.md` §7.14, L10 in §7.15, L6 in §7.17. Le
altre nove sono **difetti di scrittura di `RCP.md`**, e il posto in cui si curano è `RCP.md`, una
riga per volta, ⛔ **senza aggiungere tipi di messaggio**: la clausola di §9 è consumata dal 10
agosto.

⚠ **E una cosa che B9 dice di sé, e va letta**: `01-b9-letture.py` verifica che le due letture di
ogni voce producano **byte diversi**, e una voce «UGUALI» è **un rosso di B9**. Cioè l'elenco non
può crescere di voci inventate per far tornare la colonna — e L6, che byte non ne cambia, lo
**dichiara** invece di fabbricarne uno.

### ⛔ Tre trappole in un giro solo, e la terza non era nei banchi — 11 agosto 2026, sera

*Dal giro che ha certificato **B8**. ⭐ Le prime due sono difetti che il progetto aveva già scritto,
e la terza spiega perché le prime due erano rimaste invisibili.*

- ⛔ **La pagina del ban era illeggibile sull'innesto, e nessuno lo sapeva.** `leggi_pagina()`
  incartava **sempre** in TLS — `[M]` `SSLError: WRONG_VERSION_NUMBER` da tutt'e due gli indirizzi —
  perché l'innesto la serve **in chiaro**. ⇒ Il banco scriveva *«la pagina non si è caricata»*, cioè
  **il silenzio che §4.4-bis vieta al ban**, su un server che la pagina la serve. ⚠ **Ed era la cura
  del giorno prima ad averlo spostato**: era stata scritta per il **prodotto**, che vuole HTTPS. Due
  rossi opposti a un giorno di distanza, e in tutt'e due i casi **il server faceva la cosa giusta**.
  ⭐ Ora il dialetto lo **dichiara il bersaglio**, e se quello dichiarato tace si prova l'altro:
  *«il dialetto è l'altro»* è un fatto, *«non ho parlato con nessuno»* è un altro fatto.
- ⛔ **Due redirezioni ATTORNO a `enter.sh` — dentro i due file che quella trappola la descrivono in
  testa.** La richiesta di `sudo` esce su **stderr**: buttandola via, **nessuno può rispondere**.
  `[M]` `ps` sul server: `sudo -v -S -p Password` fermo, ⛔ **col guasto ancora addosso al codice**,
  che è il peggior punto in cui fermarsi. ⚠ Da un terminale interattivo è **invisibile** finché il
  credito di `sudo` regge: morde solo sui giri lunghi, cioè quelli che costano di più da rifare.
  ⇒ È la **quinta veste** della regola pagata il 10 agosto, e stavolta dentro i suoi stessi guardiani.
- ⛔⭐ **E la causa vera stava nello strumento, non nei banchi**: `fondamenta/strumenti/sshpw.py` rispondeva
  ad al massimo **64** richieste di parola d'ordine, e un giro di certificazione di B8 — **tre**
  esecuzioni del banco, una sessantina di ingressi nel contenitore ciascuna — ne chiede **oltre
  200**. Il giro si fermava a metà del passo «guasto», ⚠ **e il sintomo era di nuovo quello che
  inganna: non un errore, una prova «lenta»**. Chi guardava il registro vedeva l'ultimo blocco
  stampato e credeva che stesse ancora misurando. ⚠ Il tetto era **già stato alzato una volta**, da 8
  a 64, per la stessa ragione: **è la terza**. ⭐ Il numero giusto non è *«quante ne servono oggi»*:
  a proteggere non è il tetto, è **l'ancora** che spedisce la parola d'ordine solo a chi la sta
  chiedendo **in quell'istante**.

### I difetti pagati, uno per uno

| | |
|---|---|
| ⛔ **la prima stesura del banco, 9 agosto** | 44 rilievi su due revisioni. La forma che si ripete: **cadeva sempre il controllo che dice *no***, e in tre casi era già stato scritto da chi ci era passato prima. ⚠ *Due delle tre amputazioni erano state bocciate da `R2` poche ore prima, con l'istruzione «curare prima di scrivere una riga di banco»: il documento che le doveva ereditare curate le ha ereditate intatte* |

#### ⛔ Tre difetti di banco pagati in un'ora, sul primo banco eseguito — 9 agosto 2026

*E il terzo è il più istruttivo del progetto finora, perché **stava per cancellare la candidata
migliore** con un `[M]` falso contro un `[R]`.*

| # | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | `git clone -b master` di BoringSSL: *«Remote branch master not found»*. Google l'ha rinominato | ⚠ **un ramo scritto a mano è una dipendenza dal nome di qualcun altro**. Tolto: si prende il predefinito |
| **2** | ⛔ il fallimento è arrivato **con «uscita 0»** a chi guardava, perché avevo messo `\| tail` in coda al comando remoto: lo stato d'uscita era quello di `tail` | `LEZIONI.md` §1.9 — *zero e fallimento con la stessa faccia* — **presa nell'invocazione invece che nello script**. Il banco era innocente; chi lo lanciava no |
| **3** | ⛔⭐ il banco ha dichiarato **«0 simboli su 4»** stampando **i quattro simboli tre righe sopra** | vedi il riquadro |

> ##### ⛔ Il terzo: `set -o pipefail` più `grep -q`, cioè un falso rosso garantito
>
> Il controllo era `nm -g --defined-only "$LIB" \| grep -q " $s$"`. **`grep -q` esce al primo
> riscontro** e chiude il tubo; `nm` sta ancora scrivendo, prende `SIGPIPE`, muore con **141**; e
> `set -o pipefail`, in cima allo script, fa valere **quel 141** come esito della pipeline.
>
> ⛔ **Il riscontro riuscito veniva letto come fallimento** — e la perversione è che *più il simbolo
> era facile da trovare, prima `grep` usciva, più sicuro era il falso rosso.*
>
> ⚠ **Che cosa avrebbe prodotto se nessuno avesse guardato**: la riga *«il flag di `lsquic` non
> produce niente»* in `DECISIONI.md` §6.4 — cioè **la candidata con più WebTransport dentro,
> cancellata da un difetto del banco**, con un `[M]` falso che avrebbe battuto un `[R]` letto nel
> codice. È `LEZIONI.md` §2.3 (*una prova che boccia il codice giusto costa quanto una che promuove
> quello sbagliato*) e `CODER.md` §3.11 (*quando codice letto e misura si contraddicono, il sospetto
> va prima sulla misura*) nello stesso difetto.
>
> ⭐ **Che cosa l'ha fatto emergere**: non l'intuito — **tre righe di strumentazione nel banco**, che
> dichiarano su quale archivio si sta guardando e quanti simboli si vedono *prima* di dire quali
> mancano. Ora sono permanenti: erano la differenza fra «chi dei due mente» e mezza giornata di
> supposizioni.
>
> ⚠ **E una quarta, che non è un difetto ma un'abitudine da prendere**: la diagnosi a mano era
> passata attraverso **tre shell annidate** (locale → ssh → `enter.sh` → chroot) e si è rotta sulle
> virgolette, restituendo `grep: ...: No such file or directory`. La regola della fase 0 vale qui:
> **le righe di comando si mettono in un file, non si ricordano**.

#### ⛔ E il terzo difetto della stessa famiglia, che ha stampato un VERDE

*9 agosto, banco di `ngtcp2`.* Il controllo diceva **«nessuna traccia di `SETTINGS_WT_MAX_SESSIONS`:
la previsione regge»** — ⛔ **da una ricerca mai eseguita**. I due alberi erano passati a `grep` come
**una stringa sola**, quindi cercava in un percorso con uno spazio dentro che non esiste; e
`2>/dev/null` nascondeva il «No such file or directory» che l'avrebbe detto subito.

⛔ **È il peggiore dei tre, perché gli altri due davano rosso e questo ha dato verde** — e un verde
non lo si va a verificare. A insospettirmi non è stato il banco: è stato **un numero impossibile**
nella riga accanto — «extended CONNECT in 0 file» su una libreria che implementa RFC 9220.

⭐ **La cura è diventata una regola generale**, ed è entrata in `LEZIONI.md` §1.9 come **quarta
regola**: *una misura deve dichiarare su che cosa ha guardato — il denominatore, non solo il
risultato*. Adesso il banco stampa «dentro 447 file di 2 alberi» e **cerca una cosa che deve
esserci** (`nghttp3`, trovata in 110 file) prima di credere a uno zero.

#### ⚠ `aioquic` sa creare uno stream WebTransport e non sa riconoscerlo quando risponde

*Trovato costruendo il controllo positivo, 9 agosto 2026, ed è del **cliente di prova** — quindi
tornerà a mordere a ogni fase in cui quello cresce.*

Il primo giro andava in **timeout aspettando il ritorno**, mentre il server dichiarava di averlo
spedito. `[R]` `H3Connection.create_webtransport_stream` di aioquic 1.2 scrive l'intestazione dello
stream e **non registra lo stream in ricezione**: i byte tornano — si vedono a livello QUIC — e il
livello H3 non emette nessun `WebTransportStreamDataReceived`.

⛔ **Che cosa l'ha distinto**: due righe che stampano gli eventi **a tutt'e due i livelli**. Senza,
*«i byte non arrivano»* e *«i byte arrivano e nessuno li riconosce»* sono lo stesso rosso — e sono
due difetti in due posti diversi. È la seconda volta in un'ora che la strumentazione batte
l'intuito.

⚠ **La cura è dichiarata, non nascosta**: il ritorno si legge a livello QUIC, **scrivendo perché**.
Fingere che l'abbia riconosciuto il livello H3 sarebbe stato comodo e falso.

#### ⛔ Sei difetti di banco per una prova che dura due secondi — 10 agosto 2026

*La prova SNI di B2 è **una connessione**. Ci sono volute **sei esecuzioni** per arrivarci, e
nessuno dei sei difetti era della libreria che si stava misurando.*

| # | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | ⛔ **Due server della sessione del 9 agosto erano ancora vivi**, otto ore dopo, e tenevano le porte 7447 e 7448. `bsslserver` ha scritto *«Could not bind»* ed è morto | ⚠ Il rootfs del server è in RAM e **non si riavvia mai**: *«l'avevo fermato»* non è un'informazione. ⛔ E il rosso non sarebbe stato «il banco non parte», sarebbe stato **«`ngtcp2` rifiuta»** — un rosso attribuito alla libreria. Ora la porta si controlla **prima** |
| **2** | La sessione remota è rimasta **appesa senza stampare nulla** | `>/dev/null 2>&1` su una chiamata a `enter.sh`: era la prima della sessione, `sudo` chiedeva la parola d'ordine, e **la domanda finiva nel nulla**. ⛔ È il `2>/dev/null` del 9 agosto in una veste peggiore: un errore nascosto fa sbagliare diagnosi, **una domanda nascosta ferma la macchina** |
| **3** | ⛔ E non si vedeva **dove** si fermasse, perché avevo messo `\| tail` in coda al comando remoto | ⚠ **Identico al difetto n. 2 del 9 agosto**, commesso di nuovo dalla stessa mano il giorno dopo: `tail` non stampa niente finché il flusso non finisce. La cura non è ricordarsene — è **scrivere su un file e leggerlo** |
| **4** | Il banco ha dichiarato **MORTI due server che stavano ascoltando** | `setsid` **forca**: `$!` era il PID di `setsid`, che esce subito, non quello del server. ⭐ E `lsquic` lo smentiva **tre righe sotto**, con un *«in ascolto»* stampato nel suo stesso registro |
| **5** | E l'ha rifatto dopo la cura | `kill -0` da utente normale su un processo di **root** risponde *«operazione non permessa»* — cioè **un errore**, non *«non esiste»*. ⛔ **Vuoto e proibito con la stessa faccia**, `LEZIONI.md` §1.9 regola 1, su un controllo di sanità. Cura: `[ -d /proc/<pid> ]` |
| **6** | Il collegamento è caduto su `cannot find -lngtcp2`, e ⛔ **il banco ha dato la diagnosi opposta** — *«cmake ha saltato gli esempi in silenzio»* | Cmake li aveva configurati benissimo: mancava la libreria **condivisa** (`ENABLE_SHARED_LIB=OFF`), che è il bersaglio che gli esempi chiedono. ⚠ Un messaggio d'errore che indovina la causa **manda a cercare nel posto sbagliato**: ora il banco distingue «ninja è fallito» da «ninja è riuscito e il file non c'è» |

> ##### ⛔⭐ E il settimo, che è il più grave del progetto finora: **la sonda dichiarava un denominatore falso**
>
> La quarta regola di `LEZIONI.md` §1.9 era **applicata**: la sonda stampava, a ogni gamba, che cosa
> avesse messo nel campo `server_name`. Diceva `'192.168.0.2'` — **e sul filo non andava niente.**
>
> Due righe di `aioquic`, in due file diversi: `asyncio/client.py:66` riempie il campo con l'ospite
> **anche se è un indirizzo IP**; `tls.py:1551` poi, scrivendo il ClientHello, **butta gli indirizzi
> IP**. La sonda leggeva la prima e credeva di descrivere la seconda.
>
> ⛔ **Conseguenza: la gamba «con SNI» mandava esattamente quel che mandava la gamba «senza SNI».**
> Le due gambe misuravano **la stessa cosa** mentre la sonda dichiarava che erano opposte — cioè il
> controllo che doveva distinguere «la libreria pretende l'SNI» da «il banco è rotto» **non
> distingueva niente**.
>
> ⚠ **E il verde di `ngtcp2` era già stampato quando me ne sono accorto.** Era vero — la misura
> rifatta lo conferma — ma era vero **per caso**: nessuna delle due gambe stava provando quel che
> diceva di provare.
>
> ⭐ **Che cosa l'ha fatto emergere**: non un sospetto, la riga stessa. `server_name spedito:
> '192.168.0.2'` in **tutt'e due** le gambe è un'impossibilità visibile — e l'ha resa visibile
> proprio la regola che stava sbagliando. Un denominatore falso si scopre solo se lo si stampa.
>
> ⛔ **La cura, in tre pezzi**: la sonda stampa il valore configurato **e** quel che finisce sul
> filo, con la riga di codice che li separa; la gamba di controllo usa un **nome** (`remotix.prova`)
> invece dell'indirizzo, perché è l'unico modo di far comparire l'estensione davvero; e ⭐ **il
> testimone finale non è nostro** — il registro di `lsquic`, che scrive *«SNI is not set»* guardando
> lo stesso filo dall'altro capo. È entrata in `LEZIONI.md` §1.9 come **corollario della quarta
> regola**: *un denominatore si legge dove la cosa succede*.

#### ⚠ E su `quiche`, quattro intoppi e **una trappola vera** — 10 agosto 2026

*I primi tre sono cronaca di costruzione, e stanno qui perché costano tempo a chi li rifà. Il
quarto è un fatto per `DECISIONI.md` §6.4. **La trappola è il quinto**, e sarebbe stata il terzo
falso rosso attribuito a una libreria in due giorni.*

| | Che cosa è successo | |
|---|---|---|
| **1** | `cargo`/`rustc` **non erano nel contenitore** | ⚠ Il `[M]` del 9 agosto diceva che *Trixie li offre* (1.85.0) — ed era vero. **«Disponibile come pacchetto» e «installato» sono due cose diverse**, e la seconda ora sta in `provision.sh` |
| **2** | Gli esempi in C stanno in `quiche/examples`, non in `examples` | Il deposito ha una cassetta per ogni pezzo e una si chiama come il deposito. ⭐ **Il banco l'ha detto** invece di contare zero: era la quarta regola che funzionava |
| **3** | Il loro esempio non compilava: manca `uthash.h` | Nel `provision.sh`, come le altre. È una dipendenza del **banco** di `quiche`, non del prodotto |
| **4** | ⛔ `cargo` si è fermato: **`quiche` 0.29.3 pretende `rustc` 1.88**, Trixie ne ha **1.85** | ⭐ **Non è un intoppo, è un dato della decisione.** Il banco adesso sceglie da sé la versione più recente che il compilatore presente sa costruire — la **0.28.0** — e stampa quale e perché. ⚠ E nemmeno quella basta da sola: il loro `workspace` tira dentro `tonic`, `icu`, `image`; si costruisce `-p quiche`, il solo pacchetto che useremmo |

> ##### ⛔ La trappola: il loro esempio **non controlla** di aver caricato il certificato
>
> `[R]` `quiche/examples/http3-server.c:564-565`: legge `./cert.crt` e `./cert.key` **dalla
> cartella corrente**, e ⛔ **ignora l'esito** di `quiche_config_load_cert_chain_from_pem_file`.
>
> ⚠ Con i due file assenti **il server parte lo stesso**, ascolta, e ogni stretta di mano
> fallisce — che alla sonda ha esattamente l'aspetto di *«`quiche` pretende l'SNI»*. Sarebbe stato
> il **terzo falso rosso attribuito a una libreria in due giorni**, dopo il `0 su 4` di `lsquic` e i
> due server dichiarati morti.
>
> ⭐ **La cura sta nel conduttore, non nella speranza**: mette i due file con i nomi che l'esempio
> pretende e **controlla che ci siano** prima di avviare. ⚠ E il controllo usa `case`, non
> `grep -q` in un tubo: con `pipefail`, `grep -q` esce al primo riscontro e il **riscontro riuscito**
> diventa un errore — il difetto del 9 agosto, che qui non si è ripetuto perché era scritto.

#### ⛔ E la misura col browser: **quattro silenzi**, e un verde su zero misure

*Il server minimo ha funzionato al primo colpo col cliente di prova. La misura col **browser** — che
è il criterio vero di B2 — ha richiesto cinque giri, e nessuno dei difetti era del server.*

| | Che cosa è successo | Che cosa insegna |
|---|---|---|
| **1** | ⛔ **L'impronta del certificato arrivava tagliata della prima cifra** | Il banco la estraeva con `[A-Za-z0-9+/]{42}=`, e un SHA-256 in base64 è **43** cifre più il riempimento. ⚠ Il sintomo sarebbe stato *«i browser non aprono la sessione con `ngtcp2`»* — cioè **una candidata bocciata per una lettera**. Ora il banco **conta i caratteri** invece di fidarsi dell'espressione |
| **2** | Firefox non chiedeva nemmeno la pagina, e **non lo diceva** | La cartella del profilo non esisteva: con `--profile` su una cartella assente, Firefox si ferma sul suo gestore dei profili. ⛔ **Silenzio su tutt'e due i lati** — zero richieste al raccoglitore, registro del browser vuoto — per una cartella mancante |
| **3** | ⛔ E non c'era modo di saperlo, perché il raccoglitore **taceva le richieste** | `log_message` era `pass`, con scritto accanto *«il rumore delle richieste non serve: serve l'esito»*. È falso: la richiesta **è il denominatore dell'esito**. Senza, *«il browser non è partito»* e *«è partito e la prova è fallita»* sono lo stesso silenzio |
| **4** | E il primo tentativo di denominatore **contava sé stesso** | Cercavo `01-b2-sonda.html` nel registro del raccoglitore, e quel nome compare anche nel suo **banner d'avvio**: ha stampato *«richieste: 1»* quando erano **zero**. ⚠ Terzo falso denominatore in due giorni, e stavolta l'ho scritto io mentre curavo il secondo |

> ##### ⛔ E il peggiore, che non è un difetto di diagnosi ma di giudizio: **OK su zero motori**
>
> Un giro ha stampato `OK — i motori provati hanno registrato il loro esito`, e i motori provati
> erano **zero**: il controllo di presenza guardava `xvfb-run -a`, cioè verificava che esistesse un
> programma chiamato `-a`, e saltava tutt'e due i browser dicendolo in una riga di avviso che
> l'esito finale contraddiceva.
>
> ⛔ *«Tutti quelli provati sono andati bene»* **è vero anche quando i provati sono zero**, ed è la
> forma di verde più vuota che ci sia — perché non ha nemmeno bisogno che qualcosa vada storto.
> ⭐ Ora il banco conta i motori provati, li stampa, e **si rifiuta di dare un esito se sono zero**.
>
> ⚠ *E vale la pena dire come si è visto: non da un sospetto, ma perché il numero dei motori è stato
> messo accanto al verdetto. È la quarta regola di `LEZIONI.md` §1.9 applicata al **verdetto**
> invece che alla misura — il denominatore di un'approvazione è quante cose ha approvato.*

#### ⭐⛔ Le sei proprietà: due difetti veri, e nessuno dei due aveva un sintomo

*E il difetto peggiore era in una misura **nostra**, dichiarata verde poche ore prima.*

> ##### ⛔ La misura che non misurava: il server che si dà ragione da solo
>
> Il 10 agosto il server minimo stampava all'avvio
> `REMOTIX B2: max_idle_timeout=30000ms max_datagram_frame_size=65536`, e quella riga è finita nei
> documenti come una misura di `RCP.md` §2.2. ⛔ **Ma è la sua configurazione, non il filo**: dice
> che cosa il server ha *chiesto* a ngtcp2, non che cosa è *arrivato* al pari.
>
> ⚠ È **esattamente** il corollario di `LEZIONI.md` §1.9 nato quella stessa mattina — *un
> denominatore si legge dove la cosa succede* — e l'ho violato io, quel pomeriggio, su una misura
> mia. La regola scritta contro `aioquic` non mi ha protetto dal commetterla contro me stesso.
>
> ⭐ La cura è `01-b2-sonda-trasporto.py`, che legge i parametri **dal pari**. E leggendoli da lì ha
> trovato subito due cose che nessuno aveva chiesto:

| | Che cosa si è visto | Perché nessun banco lo vedeva |
|---|---|---|
| ⛔ **il server offriva 0-RTT** | due biglietti di sessione con `max_early_data_size` = `0xffffffff`. `RCP.md` §2.3 lo **vieta**: i dati 0-RTT si possono ripetere, e il secondo messaggio di RCP è `CREDENZIALI` | ⭐ **Il documento l'aveva previsto**: *«il sintomo di 0-RTT acceso non esiste… le librerie QUIC lo offrono per impostazione predefinita»*. La sessione si apre uguale, i byte tornano uguali |
| ⛔ **concedeva 3 stream unidirezionali su 16** | `initial_max_streams_uni = 3` — quanti ne vuole HTTP/3 per il controllo e QPACK. §2.3 ne impone **almeno 16** «in ogni momento» | Il client di prova non ne apre nessuno. Il sintomo sarebbe comparso **nella fase 3**, come *«il desktop non risponde»* — e nessuno l'avrebbe collegato al credito |
| ⚠ **e la pagina non passava `allowPooling: false`** | §4.1-bis lo mette fra i vincoli, accanto al certificato di 14 giorni e alla chiave P-256 | Mettendolo a `true` la sessione si aprirebbe **uguale**: è un vincolo senza sintomo, e i due browser avevano già dato verde senza di lui |

⭐ **E il 0-RTT ha avuto il suo controllo positivo per caso, dal bersaglio stesso**: la sonda ha
*visto* un 0-RTT acceso prima di vederne uno spento. Il verde che è seguito è un verde dopo una
cura, non un verde da uno strumento cieco — che è la differenza fra i due che conta.

⚠ **E un colpo a vuoto, mio, che vale come regola**: curando la pagina ho sostituito una riga con
`str.replace` in Python su un appiglio con l'indentazione sbagliata. ⛔ **Python non protesta**:
restituisce la stringa intatta. La proprietà era nel codice ma non nell'esito registrato — cioè
affermata dal sorgente e non vista da nessuno. `01-b2-ngtcp2-wt-innesta.py` questo controllo ce
l'ha (l'appiglio dev'essere **uno**); le modifiche fatte a mano no, finché non l'ho aggiunto.

#### ⭐⛔ B3: due difetti veri, e il primo è **esattamente** quello che B3 esiste per trovare

> ##### ⛔ La stretta di mano funzionava **una volta sola**
>
> Al primo giro di B3 la **prima** connessione veniva rifiutata con
> `GIA_ATTIVA_REMOTA` — cioè il server diceva *«c'è già qualcuno»* a un client che era solo.
>
> La causa: `rcp_libera()`, che libera il posto nel registro delle sessioni, **non la chiamava
> nessuno**. Ogni connessione occupava un posto per sempre; dopo la prima riuscita, il server
> rispondeva `0x0F` a chiunque, per sempre.
>
> ⭐ **È la forma di `LEZIONI.md` §2.1 alla lettera**: *in v1 un certificato condiviso uccideva il
> server alla seconda connessione, e una prova a collegamento singolo resta verde per sempre*. Il
> banco che B3 impone — **due, mai una** — l'ha preso al primo giro. Una prova a connessione
> singola sarebbe stata verde e sarebbe rimasta verde fino alla fase 5.
>
> ⚠ E si noti dove **non** si sarebbe visto: la traccia della prima connessione è *conforme* a
> `RCP.md`. Il validatore non poteva dire niente — il difetto non è nei byte, è nello stato del
> server fra una connessione e l'altra.

> ##### ⭐⛔ Il secondo: il banco accusava il server, e il colpevole era il buffer di Python
>
> Il terzo giro dava **rosso sul server**: la seconda connessione, che arriva mentre la prima è
> attaccata, veniva **accettata** invece che rifiutata con `0x0F`. Sembrava una violazione
> dell'invariante **I2** — *«la seconda connessione è rifiutata con messaggio esplicito»*.
>
> ⛔ **Non lo era. Il server aveva ragione dal primo istante.**
>
> La diagnosi, e sono state due righe di strumentazione — *chi prende il posto, chi lo lascia, e
> quanti ne restano occupati*:
>
> ```
> posto PRESO da prova via [..]:39390 (occupati adesso: 1)
> sessione aperta utente=prova via=[..]:39390
> posto LASCIATO da prova via [..]:39390 (occupati adesso: 0)   ← prima che la 2ª arrivi
> ```
>
> E i **timestamp** di ngtcp2 hanno chiuso il caso: la prima connessione si chiude a **t≈13,1 s**
> con `CONNECTION_CLOSE 0x0` — cioè ha retto i suoi dodici secondi — e la seconda arriva **dopo**.
> Le due non erano mai state contemporanee.
>
> ⭐ **La causa**: il banco aspettava la parola `SESSIONE` nel registro della prima connessione, e
> **Python bufferizza lo stdout quando è rediretto su un file**. Quella riga compariva solo
> all'uscita del processo — cioè **nell'istante esatto in cui il client si staccava**. Il controllo
> stampava `OK la prima è attaccata` leggendo una verità appena scaduta, e la seconda trovava
> sempre il posto libero.
>
> ⛔ **È la forma peggiore di difetto di banco**: non un rosso su un verde, ma **un rosso puntato
> sull'imputato sbagliato**. Il server rispettava §3.1 alla lettera — manda `CONGEDO(0x0F)` sul
> canale di controllo *e* chiude la sessione col codice `0x0f` — e il banco lo dichiarava in
> violazione di un'invariante.
>
> ⭐ **La cura, e la regola che ne esce**: il client scrive un **file** quando la sessione è aperta,
> e il banco aspetta quel file. *Un file scritto e chiuso è un fatto; una riga stampata è una
> speranza sul momento in cui qualcuno la vedrà.* (E `python3 -u`, che toglie l'altra metà della
> causa.)
>
> ⚠ E vale la pena dire **come non si è visto prima**: il controllo «la prima è attaccata» c'era, ed
> era proprio quello che doveva impedire questo errore. Era scritto giusto e misurava l'istante
> sbagliato.

#### ⛔ E due difetti di banco degli ultimi due giri, uno dei quali ha dato un VERDE

| | Che cosa è successo | |
|---|---|---|
| **1** | ⛔ Il validatore ha dichiarato **«conforme»** una registrazione mentre il cliente di *quel* giro non si era nemmeno collegato | Stava giudicando il **file rimasto dal giro precedente**. ⚠ Un verde da un file stantio: la registrazione ora si **butta prima**, e se manca il banco dice *«non ho niente da giudicare»* — che non è «conforme» |
| **2** | Il cliente «non si collegava», e il colpevole ero io | `shift 3` con **meno di tre argomenti non sposta niente e non fallisce**: `$*` restava `accendi`, il server riceveva il nome dell'azione come opzione e moriva con *«port: invalid port number»*. ⛔ **Di nuovo il rosso sull'imputato sbagliato**, e stavolta a una manciata d'ore dalla lezione che l'aveva appena nominato |

> ⚠ **E una scelta di documento, dichiarata invece che nascosta**: `SPECIFICHE.md` §5.3 dice che un
> client silenzioso da trenta secondi «si considera staccato», e **non dice che cosa succede alla
> sua connessione**. Qui si è scelto di **lasciarla aperta** e liberare solo il posto: chiuderla
> sarebbe un congedo, e §8.2 non ha un motivo che voglia dire *«taci da un po'»*. È uno dei punti
> in cui `RCP.md` ammette due letture, ed è quel che questa sezione esiste per raccogliere.
>
> ⚠ **E un filo dell'ospite, non del protocollo**: per valutare l'orologio mentre il client tace, il
> server accende il **keep-alive di QUIC a 5 s** — è un battito del *trasporto*, che §2.2 non
> vieta, ma un server vero armerà un proprio timer e non metterà niente sul filo.

#### ⛔ E tre trappole di shell in una sera, tutte la stessa

Il terzo giro di B3 si è impiccato **tre volte**, e ogni volta per lo stesso motivo in una veste
diversa: una **sottoshell in secondo piano**, una **sostituzione di comando**, e un
**`nohup ... &` con le virgolette annidate** — tutt'e tre attorno a `enter.sh`, e tutt'e tre si
portano via la richiesta di password di `sudo`. Lo script resta ad aspettare una domanda che
nessuno vede.

⭐ **La cura è la regola che il progetto aveva già**: le righe di comando si mettono in un file. Il
terzo giro adesso è `01-b3-terzo-giro.sh`, e gira **dentro** il contenitore, dove non c'è nessun
`sudo` e nessuna shell annidata.

⚠ **E un'ultima, a mio carico**: fermando i banchi ho scritto `pkill -f "01-b2-raccogli.py"`, e il
comando **ha ucciso la shell che lo eseguiva** — il modello compariva nella sua stessa riga di
comando. È la trappola del 9 agosto, scritta nel README di questo progetto, ripetuta il giorno dopo
da chi l'aveva appena documentata. Si ferma **per PID**.

⛔ **E la quarta veste, la sera dopo, su `01-b5-lancia.sh`**: `bash enter.sh --root "ninja …" > log
2>&1`. Nessuna sottoshell, nessun `&`, nessuna virgoletta annidata — **solo una redirezione**, e
`sudo` si è fermato lo stesso. Sei minuti a guardare un processo senza figli e un registro vuoto.
⭐ **La regola è più larga di come era stata scritta**: *non è `>/dev/null`, è **qualunque
redirezione attorno a `enter.sh`***. Dentro le virgolette invece è del comando remoto, e la
richiesta resta sul filo dove qualcuno la vede.

#### ⭐⛔ B5: quarantaquattro violazioni, e **un difetto che nessun altro banco poteva vedere**

*Il banco è passato al primo giro su tutte le violazioni. Il rosso è arrivato da un **controllo**,
ed era stato **previsto per iscritto dentro il banco prima di misurare**.*

⛔ **Il contatore per indirizzo di §4.4-bis non ha mai bloccato nessuno.** La chiave era
`s->provenienza`, cioè `192.168.0.2:44661` — **con la porta**. E §4.4 ammette **un solo tentativo
per connessione**: la porta cambia ogni volta, quindi quel contatore valeva **sempre 1**.

⚠ **È la forma peggiore**: il codice c'era, si leggeva bene, sembrava giusto, e **non faceva
niente**. Nessun registro lo nominava; il sintomo — *«si può provare una parola d'ordine
all'infinito»* — non arriva mai da solo.

⭐ **E il controllo che l'ha trovato è preciso**: sette tentativi falliti con **sette nomi diversi**
dallo stesso indirizzo. Con lo stesso nome, il contatore **per nome** copriva il buco e il banco
sarebbe stato verde. Curato; ora al **sesto** tentativo scatta `TROPPI_TENTATIVI` — ⛔ **anche per
la parola d'ordine giusta**, che è il secondo controllo, quello che distingue un contatore da un
blocco.

⚠ **E un ordine che è una misura**: il giro completo buono si esegue **prima** del limitatore. Dopo,
l'indirizzo è bloccato per trenta secondi, e un banco che mettesse la stretta di mano in coda
leggerebbe quel rifiuto come *«il server è rotto»* — cioè darebbe rosso **proprio quando la regola
funziona**.

#### ⭐⛔ B11: il difetto che serviva **un browser vero** per esistere

*E che B3 non poteva vedere, per cinque giri, con nessun cliente di prova.*

⛔ **Il posto nel registro delle sessioni si liberava solo alla morte della CONNESSIONE.**
`rcp_libera()` stava in `~ProtoCodec`. Con `aioquic` i due istanti coincidono — il cliente di prova
chiude tutto — e B3 è rimasto verde. ⭐ **Un browser no**: chiude la *sessione* e **tiene viva la
connessione**, e da quel momento il posto resta occupato da una sessione che non esiste più.
Con Chrome: **sette `posto NEGATO` su nove tentativi**, e alla pagina arrivava solo silenzio.

⚠ È **la stessa forma** del difetto che B3 aveva trovato il giorno prima — il posto che non si
libera — in un altro punto. ⛔ *Il difetto viveva nella differenza fra i due client, quindi nessuna
prova con un client solo poteva trovarlo.* È `LEZIONI.md` §2.1, la regola dei tre client, applicata
a una cosa che sembrava già provata.

⛔ **E il secondo, che riguarda §3.1 alla lettera.** `respingi()` manda `RESPINTO` sul canale di
controllo e chiude la sessione **nella riga dopo**: i due finivano nello stesso volo di pacchetti, e
il browser processa la capsula `CLOSE_WEBTRANSPORT_SESSION` **prima** dei byte dello stream, che a
quel punto butta. ⛔ **La pagina non ha mai visto `RESPINTO`: ha visto silenzio.**

⭐ **Ed è la dimostrazione che il punto 3 di §3.1 non è ridondanza**: il motivo è arrivato comunque,
dentro il codice d'errore della chiusura. *«Se il congedo non arriva — perché lo stream era rotto,
perché il messaggio era illeggibile — il motivo viaggia comunque»* è vero alla lettera, e questo è
il caso che lo prova. ⚠ Curato lo stesso da tutt'e due i lati: il server **rimanda** la capsula
finché la coda d'uscita non è vuota, e la pagina **legge `wt.closed`**.

⛔ **E il terzo, che è della PAGINA e lo ha reso visibile la differenza fra due motori.** La pagina
**chiudeva senza congedarsi**: chiamava `close()` e basta. Ma §8.1 dice che chi chiude *DEVE*
mandare `CONGEDO` con un motivo **prima** di chiudere — e vale anche per una chiusura volontaria
(`CHIUSO_DALL_UTENTE`). ⚠ Con Firefox non si vedeva: il trasporto chiudeva gli stream in tempo e il
posto si liberava lo stesso. ⛔ Con **Chrome** no, e otto casi su dodici ricevevano
`GIA_ATTIVA_REMOTA`. ⭐ *Non è una cura per Chrome: è §8.1 applicata, e la pagina non se ne era
accorta perché nessuno gliel'aveva chiesto.* Aggiunta: i falliti su Chrome sono passati **da 8 a 4**.

⛔ **E il quarto, che è stato l'ultimo a cadere.** Su Chrome, dopo il caso in cui è il **server** a
chiudere il canale di controllo con un `FIN`, il posto restava occupato: da lì in poi non arrivava
più un byte che potesse liberarlo, e la pagina non poteva rimediare. ⭐ **Il difetto viveva nella
differenza fra i due motori** — su Firefox il trasporto chiudeva lo stream in tempo e il posto se ne
andava lo stesso, quindi con un motore solo non esisteva. ⭐ **Curato la sera del 10 agosto: il
server libera il posto anche quando a chiudere è lui**, ed è quello che ha chiuso i tre casi rossi
di Chrome. Da lì Firefox 140 e Chrome 151 fanno **13 su 13** tutt'e due, `CONFORME` con zero
guasti, e il giro è stato **ripetuto**.

⚠ *Fino al rilievo **R11.4** del 10 agosto questo paragrafo diceva «quella riga non c'è ancora», e
la tabella delle misure «12 su 12 su Firefox, 9 su 12 su Chrome»: il commit che ha chiuso B11 ha
toccato `README.md`, `RCP.md`, cinque file di banco e `b2-esiti.jsonl`, e **non questo documento** —
che è quello che `PIANO.md` §0.1 fa leggere per primo alla ripresa. Chi riprendeva domani
riscopriva come aperto un difetto curato, e cercava una riga che c'è.*

⚠ **E la giustificazione che si dava a quel rosso è a sua volta `[?]`**: si diceva che la pagina non
poteva mandare il congedo perché *«§4.2 le vieta di spedire ancora»*. §4.2 vieta di continuare a
spedire **sugli altri canali**, e su uno stream bidirezionale il `FIN` del server non chiude il
verso della pagina — che quindi **potrebbe** mandare il `CONGEDO` che §8.1 le impone. Le due letture
danno byte diversi, il banco ha scelto il silenzio, e `RCP.md` **non dice quale sia giusta**:
rilievo aperto **R11.22**. ⛔ **La domanda sta in `DECISIONI.md` §7.14** — le due letture, i nove
byte di `CONGEDO` contro il silenzio, e il prezzo di ciascuna — e ci è arrivata la notte del 10
agosto 2026: era nominata qui, nel `README.md` e nel rapporto, e **in nessun posto dove si
decide**. ⚠ *E `RCP.md` §4.2 adesso lo dice di suo, invece di lasciar credere a chi implementa che
stia obbedendo mentre sta scegliendo.*

⛔ **E un difetto di banco che avrebbe accusato la pagina**: il confronto *«`desktop` non cambia
niente»* metteva a paragone **tutti** i byte usciti nei due giri — compreso il `CIAO`, che porta
`banco.guasto=…kde` contro `…gnome`, due stringhe di lunghezza diversa. Il denominatore conteneva
**il byte che il banco stesso aveva cambiato**, e avrebbe detto «DIVERSI» anche su una pagina
perfetta.

---

## Le decisioni prodotte

*Rimandi, non copie (`PIANO.md` §0.3 regola 1). ⚠ La prima stesura copiava tre passaggi da `RCP.md`
§4.1-bis e da `PIANO.md`, e uno aveva perso il rimando dell'originale (R4.12).*

| | |
|---|---|
| ⭐ `DECISIONI.md` §6.4 | 🔸 **CHIUSA il 10 agosto 2026, con un banco**: **`ngtcp2`+`nghttp3`**. `lsquic` fuori sull'SNI, `quiche` fuori perché **dal C non riesce a dichiarare WebTransport**, `ngtcp2` dentro perché **due browser veri aprono la sessione**. ⚠ Il prezzo — **373 righe di codice** `[M]` ore 16:30, di cui la riscrittura del SETTINGS di nghttp3 — è scritto accanto alla scelta |
| ✅ `DECISIONI.md` §1.8 | ⭐ **Apple è un di più, non un obiettivo** — 9 agosto 2026, dall'utente: S1a esce dalla fase, e la libreria si sceglie su due motori su tre |
| ⭐ ✅ `DECISIONI.md` §1.9 | **Il ban dell'indirizzo** — 10 agosto 2026, dall'utente: **tre autenticazioni fallite, dodici ore**, con un contatore solo e senza quello per nome utente. Riscrive `RCP.md` §4.4-bis — che da 🔸 diventa ✅ — `SPECIFICHE.md` §4.2, la regola **B0.3** e il banco **B8** per intero. ⛔ Nessun tipo nuovo sul filo: `TROPPI_TENTATIVI` c'era già |
| ⏳ `DECISIONI.md` §1.7 | resta aperta solo la comodità su Safari, e nessuno la misurerà per ora |
| ✅ `DECISIONI.md` §7.14 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: dopo un `FIN` sul canale di controllo **chi lo riceve tace** — cioè la lettura che **B11** aveva scelto da sé. ⚠ *Questa riga l'ha data **aperta** per mezza giornata dopo che era stata decisa (commit `ea35b5a`), e il documento di chiusura della fase **sottostimava quel che la fase aveva prodotto**: quattro decisioni contate come domande* |
| ✅ `DECISIONI.md` §7.15 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: il congedo di §8.1 vale **se il canale è ancora utilizzabile** — vince la condizione di §3.1 punto 2, e **B5 e B11 applicavano già quella** |
| ✅ `DECISIONI.md` §7.16 | ⭐ **CHIUSA dall'utente l'11 agosto 2026**: la funzione di banco resta 🔸 — ⭐ **e fuori dal prodotto consegnato** |
| ⛔ `DECISIONI.md` §5.0-quater | **S5 ha risposto, e la risposta smentisce la ragione scritta accanto alla decisione**: la tela resta lo schermo in pixel fisici, ⛔ **ma la formula con cui il client lo legge non regge su Chrome** — `screen.width × devicePixelRatio` dà `risoluzione × zoom`. `[M]` 10 agosto 2026. ⚠ La decisione **resta 🔸** e non è ripensata: cade la formula, non l'oggetto. La cura è di `SPECIFICHE.md` §6.1-bis e **non c'è ancora** |
| ⭐ `RCP.md` §7.3 | ⭐ **CHIUSA su Mutter l'11 agosto 2026**: S7 ha misurato il segno, e il server **inverte l'asse verticale**. ⛔ Resta `[?]` per gli altri quattro desktop, e *«non chiusa»* e *«non misurata»* sono due stati diversi |
| ✅ `DECISIONI.md` §7.17 | ⭐ **CHIUSA dall'utente l'11 agosto 2026: cinque secondi.** L'ha **prodotta una misura** — B6, chiudendo R3.27, ha trovato che una sessione che **non apre mai il canale di controllo** non aveva addosso nessun tetto — e l'ha chiusa l'utente dandogliene uno. ⭐ È il giro intero: una misura apre una domanda, la domanda va dove si decide, e la decisione torna nel protocollo |
| ⏳ `RCP.md` §5.3 | S6 dice se i 5 ms del PCM reggono |
| 🔸 `RCP.md` §7.5 | ⭐ **chiusa la notte del 9 agosto**: la funzione di banco — `BANCO_MARCA` e `BANCO_ESITO` — è entrata **prima del primo byte**, sotto la clausola di §9. ⚠ La usa la fase 3; qui se ne prova solo il **rifiuto a funzione spenta** (B5). ⚠ *Era marcata ✅, cioè «deciso dall'utente» (`README.md`), e non risulta presa dall'utente: §7.5 dichiara di venire dal **rilievo R3.4** e la motivazione da `web/rapporti/S4-ritardo-disegno.md` §5.3 — non c'è né frase né voce, come invece l'hanno §1.6 e §1.8. Corretta il 10 agosto 2026, rilievo **R11.15**, e **registrata dove le decisioni stanno**: `DECISIONI.md` §1.5 riga 26.* ⛔ **E la domanda «era sua?» è aperta, e sta in `DECISIONI.md` §7.16**: si chiude con una parola, e conta perché quei due tipi hanno consumato la clausola di §9 che `RCP.md` §12 dichiara essere stata *«l'ultima occasione»* |
| ⭐ `RCP.md` §4.6 | ⭐ **CHIUSA l'11 agosto 2026**: il cronometro parte dall'**apertura del canale di controllo**, e la riga 1 è cambiata di una parola (B6, R3.27). ⛔ Con la seconda risposta che apre `DECISIONI.md` §7.17 |
| ⭐ `SPECIFICHE.md` §11.5 | ⭐ **MISURATA l'11 agosto 2026, sera**, e da fuori: `curl -skI https://192.168.0.2:7448/` sul **prodotto** risponde **200, 31 840 byte**, con `Cross-Origin-Opener-Policy: same-origin` · `Cross-Origin-Embedder-Policy: require-corp` · `Cross-Origin-Resource-Policy: same-origin` · `Cache-Control: no-store`. ⇒ l'isolamento fra origini **c'è sulla pagina che il prodotto serve**, e non è più *«un vincolo da rispettare»* letto in un documento. ⚠ È `[M]` sulle **intestazioni**, non sul comportamento del browser sotto attacco |

---

## Che cosa resta `[?]`

| | |
|---|---|
| quanti **stream al secondo** regga ciascun browser | `RCP.md` §2.3 — banco della **fase 3** |
| **Safari su HTTP/2 e TCP** | l'unico motore che ci ripiega, e il nostro server non lo parla: ⏳ **va deciso** se implementarlo o dichiarare Safari fuori dal ripiego (`STUDI.md` §web §3.2, O5) |
| ⭐ **S1a — l'eccezione su Safari e su iOS** | ✅ **resta `[?]` per decisione**, non per dimenticanza (`DECISIONI.md` §1.8). ⛔ E finché è `[?]`, *«funziona su iPhone»* **non si scrive nella documentazione del prodotto** |
| i **10 bit** fino allo schermo | tre indizi contrari, nessuno è una misura (`STUDI.md` §web §1.2 A). Verifica alla **fase 2**, e la prova finale è **guardare una sfumatura** |
| il **pezzo cieco** di S4 | 16-40 ms fra il disegno e il pixel acceso, e nessuna API JavaScript lo vede: la stima **si dichiara accanto a ogni numero** |
| ⚠ **che a rifiutare l'impronta vecchia sia il CONFRONTO dell'impronta** | il terzo giro di B3 lo dava per dimostrato, e non lo è: l'esito registrato dichiara **tre cause con lo stesso aspetto** — UDP filtrato, impronta non del certificato servito, certificato oltre i 14 giorni — e nessuno le ha distinte. ⛔ Si chiude con un controllo che le separi, non con la frase *«il browser confronta davvero»* (R11.3) |
| ⭐ **~~e la seconda metà del criterio di B2 sul terzo giro~~ — CHIUSA** | il giro è stato **rifatto la sera del 10 agosto**, su decisione dell'utente, e adesso passa pieno: la sonda manda un `CIAO` conforme e accetta `ECCOMI`, invece dell'eco di B2 che il server non fa più. ⭐ E registra **sempre** un esito, anche quando il server tace: prima restava appesa, e «il browser non è partito», «la sessione non si è aperta» e «il server non ha risposto» avevano lo stesso aspetto (R11.3) |
| ⚠ **il segno della rotella su più di un compositore** | R3.25 — ⭐ **misurato su Mutter** il 10 agosto 2026 (`+120` ⇒ il server inverte), ⛔ **e §7.3 vincola cinque desktop**: se a normalizzare è `libei` il numero vale ovunque, se normalizza il compositore KWin darà un segno diverso. Il banco è rieseguibile su KWin senza cambiare una riga |
| ~~**l'istante da cui parte il primo tetto**~~ — **CHIUSA** | R3.27, chiusa da **B6** l'11 agosto 2026: si parte dall'apertura del **canale di controllo**. ⛔ E la seconda risposta di B6 ha aperto `DECISIONI.md` §7.17 — **la sessione senza canale non ha nessun tetto** |
| ⭐ ~~**la pila PAM per un utente diverso dal proprietario del processo**~~ — **CHIUSA** | R3.26, chiusa da **B10** l'11 agosto 2026 **con una misura**, sul servizio **`remotix`**: la pila PAM verifica la parola di un utente **diverso dal proprietario del processo** ⛔ **solo se il processo è privilegiato** — da `root` riesce, da un utente normale no. Il server oggi è di root. ⚠ **Resta la domanda della fase 2**: un servizio di sistema che **lascia i privilegi** vedrebbe quella causa, e il sintomo sarebbe *«credenziali errate»* |
| ⛔ **il secondo fisso di §4.4-bis, e l'imputato adesso ha un nome** | ⭐ **Rimisurato la sera dell'11 agosto 2026** dal giro di certificazione di B8: mediane **2123,2 · 2198,1 · 1085,9 ms** — ⛔ *e quindi i «1984 ms» del `README` e i «2636 ms» qui sotto sono **due fotografie di giri diversi**, non un numero corretto due volte*. ⭐ **Quel che è cambiato non è il numero, è che l'imputato è misurato**: il server attende **+1034 ms** oltre il secondo fisso sui respinti e **+84 ms** sugli ammessi — la firma di `pam_faildelay`, cioè **PAM e non il nostro codice**. ⚠ E la `[?]` resta aperta lo stesso, perché finché quel ritardo non è costante il secondo fisso **non nasconde quel che dichiara di nascondere** |
| ⛔ **il secondo fisso di §4.4-bis contro il servizio `remotix`** | i **2636 ms** di B8 sono la mediana **di `login`**. Il prodotto ha il suo servizio PAM, quindi *«a governare i tempi è PAM»* va rimisurato prima di credergli, e il `[?]` sul secondo fisso **non lo chiude quella misura** |
| ⛔ **la formula della tela, dopo S5** | `screen.width × devicePixelRatio` non è invariante allo zoom su Chrome 151, e lo zoom di pagina **non è leggibile da JavaScript in modo portabile**. Non è una `[?]` da misurare: è una **cura da trovare**, in `SPECIFICHE.md` §6.1-bis |
| ⛔ **S5 su DeX, e S2, S3a, S6** | quattro misure che aspettano un **dispositivo**, non un'idea: il telefono Android, il DeX, una rete LTE vera. ⭐ I banchi sono pronti e girano il giorno che il ferro c'è (`web/rapporti/S-esiti-sonda.md` §4-§6) |
| ⏳ **il numero di S1b** | l'orologio è in moto dal 10 agosto 21:10 UTC: il verdetto è il **17-18 agosto 2026**. Fino ad allora S1b dice *«a N giorni l'eccezione c'è ancora»*, e il `[R]` dei sette giorni **non è confermato dal comportamento** — solo dalla contabilità di Chrome |
| ⛔⛔ ~~**il congedo di §8.1 su FIREFOX**~~ — **NON È PIÙ UNA `[?]`: È UN DIFETTO DI PRODOTTO, CON UN NOME** | ⭐ **Attribuito la sera stessa** (`banchi/01-p5-ff-*`, due giri per motore): **è della PAGINA**, e su **tutt'e due i motori**. `src/pagina.html` · `registro_visibile()` azzera `congeda_corrente` un millisecondo dopo `SESSIONE`, e il gestore di `pagehide` (riga 331) è **codice morto**. ⇒ Chiudendo la scheda, il client **non manda nessun congedo** dove §8.1 lo impone senza condizioni, e il posto se ne va per il tetto dei 30 s. ⛔ **Gecko è scagionato per misura**: la stessa `congeda()` chiamata da dentro `pagehide` consegna **tutt'e due** le strade di §3.1. ⛔ E su Chrome quel che sembrava un congedo era **lo smontaggio col codice `0x0`, che §3.1 vieta** — il banco lo contava senza leggere il motivo. ⭐⭐ **E la cura è APPLICATA E RIMISURATA la tarda serata dell'11**, `[M]` **due giri per motore**: `pagehide` scatta con la guardia **PRESENTE**, `congeda()` viene chiamata, e al server arrivano **tutt'e due** le strade di §3.1 col motivo `0x01` — su Firefox **e** su Chrome, dove la chiusura col codice `0x0` **non compare più**. Il riquadro di P5 porta i numeri. ✅ **E la dichiarazione c'è**: `DECISIONI.md` §1.12 — la cura è **fuori fase**, la fase 1 **non si riapre** e resta a **12 su 14**; alla fase 2 passa la ricertificazione di P5 |
| ⛔ **il prodotto contro i banchi** | nessun banco ha mai acceso `src/`. Finché non lo fa, *«il server fa X»* è vero **dell'innesto**, e di `src/` è **letto** |
| `[?]` **il rinnovo del credito degli stream unidirezionali** | dichiarato dal prodotto stesso; si misura alla **fase 4**, col carico che lo provoca |
| ⚠ **perché `lsquic` con l'SNI cada su ALPN** | `[M]` 10 agosto: avviso TLS **120**, `no suitable application protocol`, **dopo** che il certificato è stato trovato. ⛔ **Non indagato di proposito**: `lsquic` è fuori per un motivo che non dipende da questo, e la riga esiste perché nessuno lo riscopra credendolo nuovo |
| ⚠ **la previsione sulla bozza 02 di `lsquic`** | ⛔ **ancora aperta dopo due misure**: nemmeno con l'SNI si arriva alle impostazioni HTTP/3. Non è stata né confermata né smentita |

---

## Le cure fuori da questo documento

*Tre stonature che le revisioni hanno trovato guardando questo banco, e che stavano altrove. ⛔
Curate lo stesso giorno, o sarebbero rimaste note in un documento.*

| | |
|---|---|
| `RCP.md` §4.1-bis | diceva ancora *«`[S]` WebKit non lo implementa»*, mentre `STUDI.md` §web §3.1 e `DECISIONI.md` §1.7 erano stati corretti il 9 agosto. ⛔ **È l'arbitro**: chi lo leggeva alla lettera scriveva il ramo sbagliato **restando conforme** (R4.4) |
| `RCP.md` §7.3 | attribuiva al banco della rotella di v1 una tabella di conversione: `LEZIONI.md` §2.3 dice che è costato **una stringa di registro cercata male** (R4.15) |
| `STUDI.md` §web §3.3, §4.3, §6.3 | i **controlli negativi** che i rapporti prescrivono e che la sintesi aveva perso — è la cura che `R2` aveva ordinato *«prima di scrivere una riga di banco»* (R3.1) |
| `STUDI.md` §web §8 | la durata dell'eccezione su Chrome era `[?]` in §8 e `[R]` in §3.2, **nello stesso documento** (R4.14) |
| §00-ambiente | dichiara che l'ambiente della sonda serve *«alla fase 2, non prima»*, mentre `PIANO.md` §1.2 la mette prima di tutto nella fase 1 (R3.14) |
| `PIANO.md` §1.2 | la sonda era di quattro misure e **S4 non è eseguibile in questa fase** |

**E quelle dell'11 agosto 2026**, uscite dalla revisione avversariale della notte
(`fasi/rapporti/R12-A/B/C/D`) e dalle misure della sonda. ⛔ *Ogni riga dice **dove** la cura è
andata: quando si cura una riga si cercano tutti gli altri posti che dicevano la stessa cosa, ed è
la forma di difetto che questo progetto paga più spesso.*

| | |
|---|---|
| `RCP.md` §0-bis · §9 · §7.5 · §8.2 · `DECISIONI.md` §1.5 | ⛔ **cinque punti dicevano «oggi non esiste nessuna implementazione»**, al presente, mentre ne esistono tre: la finestra di §9 era dichiarata **aperta** dall'arbitro. Chiusa in tutti e cinque, con la data del primo byte (R12C.2) — ⭐ **e §9 adesso conta QUATTRO tipi entrati sotto la clausola, non due** (R12C.3) |
| `RCP.md` §7.3 | il segno della rotella: da `[?]` a **misurato**, con la scena, la data, i quattro controlli e quel che di ciascuno è nel registro (R12C.7) |
| `RCP.md` §4.6 | la riga 1 cambia di una parola, ⛔ **e la tabella guadagna la riga dello stato che non aveva** (R12C.11) |
| `RCP.md` §4.4-bis | il comando di sblocco **non è di RCP e non sta sul filo**: dichiarato, con la forma che non funziona e perché (R12C.4, R12.1) |
| `SPECIFICHE.md` §6.1-bis | *«va misurato quanto e su quali motori»* → **è misurato**, e la formula non regge su Chrome (R12C.8) |
| `SPECIFICHE.md` §5.5 | ⛔ prometteva dieci sessioni insieme mentre la fase 1 gira su **un filo solo con PAM sincrona**: il ripiego era dichiarato **solo in un commento di `src/main.c`** (R12C.17) |
| `DECISIONI.md` §5.0-quater | la `[?]` su cui poggiava è misurata, e va **nell'altro verso** — `LEZIONI.md` §2.3-quater preso in flagrante (R12C.8) |
| `DECISIONI.md` §7.17 | ❓ **nuova**, aperta da una misura di B6 e non da una lettura |
| `STUDI.md` §web §7 · §8 | le etichette della sonda, e S1b che non è più *«da avviare»* |

---

## ⛔ Un verdetto che la regola dell'utente ha cambiato: **R9.10**

*Scritto qui la notte del 10 agosto 2026, e non nel rapporto: ⛔ **`fasi/rapporti/R9-prodotto-rcp.md`
porta la sua data e non si riscrive**. Chi lo legge domani deve poter sapere, da qualche parte, che
una sua metà è decaduta e l'altra è peggiorata — e da quando.*

Il rilievo diceva due cose sul limitatore di `banchi/rcp/rcp.c` (*«il blocco per indirizzo non
scade mai, e raddoppia fra prove separate da settimane»*).

| | |
|---|---|
| ⭐ **la prima metà è DECADUTA** | il blocco che raddoppiava — 30 s, poi 60, poi 120, fino a 15 minuti, e `blocco_corrente` che nessuna strada riportava a zero — **descriveva la forma 🔸 che non esiste più**. `DECISIONI.md` §1.9, la sera dello stesso giorno, l'ha sostituita per intero: niente finestra che raddoppia, niente contatore per nome utente, **un ban di dodici ore con una scadenza scritta su file**. ⛔ La cura non è più *«far scadere il contatore»*, è che il ban abbia **una scadenza e un comando di sblocco** (`RCP.md` §4.4-bis) |
| ⛔ **la seconda metà è PEGGIORATA** | *«due giri identici, due verdetti diversi, e la causa non è nel banco»*: l'indirizzo del banco resta bloccato dal giro prima, e nel secondo ogni caso che passa da `fino_ad_ammesso()` riceve `TROPPI_TENTATIVI` invece di `AMMESSO`. ⛔ **Adesso quel blocco dura 12 ore invece di 15 minuti, e sta su file**: sopravvive anche al riavvio del server, quindi «si aspetta» e «si riavvia» non sono più cure. E non tocca solo B5: **B7 fallisce un tentativo, B8 ne fallisce tre**, e da lì in poi B10, B11 e chi sta sviluppando sono fuori da quella macchina per mezza giornata |

⛔ **La cura è la regola B0.3 di questo documento**, e va letta prima di lanciare qualunque banco: il
**comando di sblocco** fra un banco e l'altro — ⛔ **mai dentro il giro di B8**, o B8 non prova più
niente — e **ogni banco che lo chiama lo dichiara**, o *«il ban non è scattato»* e *«qualcuno l'ha
tolto»* hanno lo stesso aspetto.

⚠ E la parte del rilievo che **non** cambia: era, ed è, il **difetto noto n. 6** del mandato del 10
agosto — *«B11 ha dato verdetti diversi fra giri identici»* — con l'imputato fuori dal banco.

---

## Il giudizio dell'utente

*La frase vera, con la data. La fase si chiude qui, non quando questo documento è pieno.*

> ### ✅ **«Va bene, la stretta di mano funziona: fase 1 approvata.»**
>
> — l'utente, **11 agosto 2026**, dopo aver aperto `https://192.168.0.2:7448` **dal portatile**, in
> **Chrome**, digitato `prova` e la parola d'ordine, e aver letto sulla pagina *«Ammesso, sessione
> nuova, tela 1920×1080, desktop sconosciuto»*.

⭐ **La misura che chiude la fase ha una provenienza su disco**, e non è un ricordo:
`rapporti/GIUDIZIO-11-agosto.md` — la scena, le impronte, il
registro del server verbatim (`GET /` alle **12:45:44 UTC**, la stretta di mano alle
**12:48:55-12:48:56 UTC**) e quel che la pagina ha mostrato.

⛔ **E quel giro ha chiuso da solo le due cose che il `README.md` di quella mattina dichiarava non
misurate**: che **la pagina l'abbia servita il prodotto** (`GET /` era a **zero**) e che un giro
**abbia attraversato la rete** (le 19 connessioni del 10 agosto venivano **dal server stesso**). Su
**Chrome**, di cui contro questo server non c'era nessuna traccia.

⚠ **Che cosa il giudizio NON è**: un banco. Non ha un atteso confrontato da una macchina (**B0.4**),
non ha un controllo che dica *no*, non è rieseguibile senza una persona, e ⛔ **la versione esatta di
Chrome non è annotata** (regola **B0.6** mancata). È **I8**, e vale per quello che è — che è
esattamente ciò che `PIANO.md` §0.2 regola 3 chiede per chiudere una fase: *una misura giudicata
dall'utente, non un documento completo*.

⛔ **E la fase si chiude con del lavoro dichiarato aperto**, che è la forma onesta: le certificazioni
mancanti e i `[?]` qui sopra non si cancellano perché il giudizio è arrivato — si portano in fase 2
scritti, o la prossima fase comincia credendo a misure che nessuno ha fatto certificare.


---

<a id="02-primo-fotogramma"></a>

## Fase 2 — Il primo fotogramma

Aperta il **12 agosto 2026** · ⭐⭐⭐ **CHIUSA il 13 agosto 2026, sul giudizio dell'utente** — la
catena consegna, e l'utente ha guardato il proprio desktop dentro una scheda del browser.
⭐ La provenienza sta in `rapporti/GIUDIZIO-13-agosto.md`: la scena,
il registro del server verbatim, le impronte, e ⭐ **la misura fatta sui pixel dello scatto**.

> ⚠ *Questa riga diceva «il banco esiste, il prodotto no», e con lei altri tre punti del documento
> (§«Come è stata divisa», §«Che cosa è stato sviluppato», §«Il giudizio dell'utente»). Erano vere
> del **giro del 12 agosto mattina** e sono rimaste addosso al documento mentre il prodotto nasceva
> la sera stessa. ⛔ **È la causa di processo di R12-C alla terza occorrenza**: il documento è stato
> chiuso alle **08:36** del 13 agosto e il codice è arrivato fino alle **09:55** — quattro commit
> più tardi. Corretto il 13 agosto 2026 a codice fermo, revisione **R13**, rilievi 1 e 2.*

> Il modello di questo documento sta in [`PIANO.md`](PIANO.md) §0.2; le decisioni stanno in
> [`DECISIONI.md`](DECISIONI.md) e qui si **rimanda**, non si copia. ⛔ E si rimanda anche ai
> **sei rapporti di sotto-fase e ai sette del prodotto**: quel che sta lì non si ricopia qui, o le
> due copie divergono — è la lezione del 10 agosto, quando i `.md` erano stati chiusi due ore prima
> del codice.

---

### Che cosa deve produrre

Cattura da una sessione GNOME vera → codifica → filo → `VideoDecoder` → tela della pagina.
**Un'immagine ferma.**

**Che cosa vede e giudica l'utente**: il proprio desktop, dentro una scheda del browser. Fermo, ma
suo — e da qualunque dispositivo.

**Il banco**: il fotogramma decodificato confrontato con quello catturato. Non «il programma non è
crollato»: **i pixel**.

---

### Come è stata divisa, e perché

⭐ **Su richiesta dell'utente, il 12 agosto 2026**: la fase è stata tagliata in **sei sotto-fasi** e
ciascuna affidata a un agente, che ha lavorato in parallelo agli altri. Il taglio segue **gli anelli
della catena**, non delle fette arbitrarie: ogni sotto-fase possiede file suoi, una porta sua, e
consegna alle altre attraverso una sezione dichiarata — **le cuciture**.

Il mandato comune sta in `rapporti/MANDATO-12-agosto-fase2.md`.

| # | Sotto-fase | Rapporto | Banco | Porta |
|---|---|---|---|---|
| **F2.1** | La sessione GNOME headless | `rapporti/F2-1-sessione.md` | `banchi/02-sessione-*` | 7511 |
| **F2.2** | La cattura | `rapporti/F2-2-cattura.md` | `banchi/02-cattura-*` | 7512 |
| **F2.3** | La codifica HEVC in software | `rapporti/F2-3-codifica.md` | `banchi/02-codifica-*` | 7513 |
| **F2.4** | Il filo | `rapporti/F2-4-filo.md` | `banchi/02-filo-*` | 7514 |
| **F2.5** | La pagina | `rapporti/F2-5-pagina.md` | `banchi/02-pagina-*` | 7515 |
| **F2.6** | Il giudizio | `rapporti/F2-6-giudizio.md` | `banchi/02-giudizio-*` | 7516 |

⛔ **E il giro del 12 agosto MATTINA non ha scritto una riga di prodotto**, per la regola di
`PIANO.md` §0.4: il revisore interviene **appena il banco esiste**, prima che il prodotto esista,
perché *«un difetto nel prodotto lo trova un banco buono; un difetto nel banco non lo trova niente,
e avvelena ogni misura successiva perché dà fiducia»*. In quel momento `src/` era **intatto**.

⭐ **Il prodotto è arrivato la sera dello stesso giorno**, con lo stesso taglio ad anelli e un
rapporto per ciascuno — ⛔ e questa tavola non li nominava, così che chi riprendeva leggendo questo
documento **non sapeva che esistessero** (revisione **R13**, rilievo 1; è il danno di R12C.1, dove
*«chi riprendeva il lavoro leggeva quella riga e riscriveva da zero un server che esiste»*):

| # | Il prodotto dell'anello | Rapporto |
|---|---|---|
| **P2.1** | la sessione GNOME | `rapporti/P2-1-sessione.md` |
| **P2.2** | la cattura | `rapporti/P2-2-cattura.md` |
| **P2.3** | la codifica, HEVC **e** AV1 in software | `rapporti/P2-3-codifica.md` |
| **P2.4** | il canale video, dentro `rcp.c` | `rapporti/P2-4-filo.md` |
| **P2.5** | la pagina che dipinge il fotogramma | `rapporti/P2-5-pagina.md` |
| **P2.6** | il montaggio: i cinque anelli messi insieme | `rapporti/P2-6-montaggio.md` |
| **P2.7** | il figlio per utente (`DECISIONI.md` §1.10-bis) | `rapporti/P2-7-figlio.md` |

---

### Il banco

⭐ **Sei banchi, e tutti e sei certificati nello stesso giro in cui sono nati** — la regola scritta
l'11 agosto 2026 (*chi scrive un banco lo certifica nello stesso giro, o il conto non cala mai*)
è stata rispettata sei volte su sei.

| | La certificazione, `[M]` 12 agosto 2026 |
|---|---|
| **F2.1** | sul ferro `sano 0 → guasto 1 (zero monitor) → risanato 0`, girato **due volte**, sessione fermata e riavviata sei volte · sulle scene registrate **9 su 9**, otto guasti ciascuno nel suo punto |
| **F2.2** | `sano 0 → quattro guasti 1 → risanato 0`, con la marca **pretesa** *e* quella **vietata**: il grigio deve dare *«scena non riconosciuta»* e ⛔ **mai** *«fotogramma nero»*, o il giudice sbaglia la diagnosi peggiore proprio dove serve |
| **F2.3** | **30 su 30** verde su CHUWI **e** dentro il contenitore di NIC-OS · sano → guasto → risanato su **due** organi, cinque esecuzioni, marca verificata **assente** nel giro sano |
| **F2.4** | **6 pezzi su 6** · il giudice **27 su 27** come previsto · `sano 0 → guasto 4/1/2/3 → risanato 0`, marca vista nel guasto e mai nel sano |
| **F2.5** | sano → **cinque** guasti → risanato, uscita 0. ⚠ Due dei cinque sono **nati certificando**: erano stati innestati e non facevano virare niente |
| **F2.6** | `sano 0 → dodici guasti su dodici con la marca giusta → risanato 0` |

#### ⭐⭐ E la cosa che dice se il giro è valso la pena: **nove difetti trovati dentro i banchi, prima che il prodotto esista**

⛔ Non nel prodotto — **nei banchi appena scritti**, e tutti trovati *girando*, non rileggendo:

- **F2.2** — ⛔ **il suo banco è uscito VERDE col difetto vivo**, al primo giro: zero fotogrammi di
  regime, riga gialla, verdetto verde. La forma **E8**. Causa: la sessione aveva già `Meta-0`, il
  banco montava `Meta-1`, e la scena finiva sul primo. ⭐ Curato in tre punti, e **le due righe
  sbagliate restano nel registro** con accanto la nota che dice perché non valgono.
- **F2.6** — quattro: un controllo che correlava i canali su tutta l'immagine (R, G, B sono correlati
  a 0,978 ⇒ **rosso su catena sana**); uno che sottraeva 8 bit da 16 (−3,18 dB su catena perfetta);
  uno che innestava il guasto sull'imputato e **ri-scambiando i piani li rimetteva a posto**; e uno
  che aggregava `None` con `is not False` e **promuoveva** un giro senza riferimento.
- **F2.4** — due: il confronto della regola citata dava **rosso su quattro giudizi esatti**, e le
  marche di due guasti erano nomi che compaiono **anche nel giro sano**.
- **F2.5** — due, quelli «nati certificando».

⇒ Ciascuno di questi, se il prodotto fosse stato scritto prima, sarebbe diventato **un'accusa al
prodotto**. La fase 1 ne ha pagati tre di quel tipo.

---

### Che cosa è stato sviluppato

**Il 12 agosto mattina, niente prodotto** — e non era un ritardo, era l'ordine (`PIANO.md` §0.4).
Quel che esisteva era il banco, e con esso la **forma** che il prodotto avrebbe dovuto avere: le
decisioni qui sotto erano vincoli per chi avrebbe scritto il codice.

⭐ **Il prodotto è stato scritto la sera del 12 e la mattina del 13**, e sta in `src/` — la sessione,
la cattura, le due codifiche, il canale video dentro `rcp.c`, la pagina che dipinge, il montaggio e
il figlio per utente. I sette rapporti sono nella tavola `P2.1` … `P2.7` qui sopra, e **quel che sta
lì non si ricopia qui**.

---

### Le misure

#### ⛔ 1. Il terreno era rotto da due giorni, e nessuno lo sapeva

`[M]` 12 agosto: la sessione GNOME viva su NIC-OS **dal 10 agosto** girava `--headless --no-x11`
**senza** `--virtual-monitor`. `GetCurrentState` → **zero monitor**, con `IsSessionRunning` true,
cinquanta nomi sul bus, Nautilus e Terminale accesi.

⇒ **Il guasto M9 di `STUDI.md` §gnome §13 non è stato innestato: era già addosso alla macchina.** Una
cattura puntata lì avrebbe misurato **zero fotogrammi** cercandoli dentro PipeWire, e l'imputato
sarebbe stata la cattura.

- ⚠ **La sessione nera non è solo nera: è fragile.** `Shell.Screenshot` su zero monitor fa tentare a
  Mutter una texture 0×0; con `OnFailure=gnome-session-shutdown.target` **cade tutta la sessione**.
  `[M]`, provato involontariamente e dichiarato.
- ⛔ **La cura di oggi non sopravvive a un riavvio**: il drop-in vive in `$XDG_RUNTIME_DIR`. Si
  rimette con `bash banchi/02-sessione-lancia.sh sano`.
- ⛔ **E la cura vera è di prodotto**: `fondamenta/remotix-c/src/sessione.c:671` è
  `if (tipo == COMPOSITORE_KWIN && …)` — sul ramo GNOME `larghezza` e `altezza` **entrano nella
  funzione e si perdono**. Che il monitor virtuale stia in `provision-server.sh` invece che nel
  programma è l'invariante **I7** violato.

#### ⛔ 2. La sorgente dà OTTO bit — il desiderato dei 10 bit non passa di qui

`[M]` 12 agosto: **Mutter consegna solo BGRx/BGRA**, cioè 8 bit per canale. 1920×1080, stride 7680
**letto dal manifesto** e non calcolato, 8 294 400 byte, range non dichiarato da Mutter ma **misurato
0-255**, e **nessuna matrice** — i pixel sono RGB.

Il conto che lo dimostra, fatto **sulla sfumatura** della scena (⚠ sulle barre piatte i livelli sono
una ventina per costruzione, e direbbe «8 bit» su qualunque cosa): **255/256/255 livelli distinti,
multipli di 4 a 0,259/0,259/0,249**.

⇒ ⛔ **Main10 da questa strada significa otto bit promossi a dieci**, e l'etichetta continuerebbe a
dire *«10 bit»* per tutta la catena. Il desiderato di `SPECIFICHE.md` §3.1 **non è raggiungibile in
fase 2 per via MemFd**, e la `[?]` viva si sposta su **DMA-BUF**, che F2.2 dichiara **non provata**.

⭐ E la previsione era stata scritta prima: F2.3 aveva messo a verbale *«se la cattura dà 8 bit, tutta
la catena resta verde e l'etichetta dice Main10 lo stesso»* come rischio da misurare. F2.2 ha
risposto: **è una certezza, e l'imputato sono io.**

#### ⛔⛔ 3. HEVC non arriva al pixel su Firefox, e su Chrome esiste solo con la GPU

`[M]` 12 agosto, F2.5 — **e la scena decide una delle due risposte**:

| | schermo vero `:10` (GPU) | Xvfb (senza GPU) |
|---|---|---|
| **Chrome 151** | ⭐ **HEVC arriva al pixel**, 8 celle su 8, Main **e** Main10, Annex-B **e** hvcC | ⛔ **zero**: ogni stringa HEVC rifiutata |
| **Firefox 140 ESR** | ⛔ **zero**, `NotSupportedError` | ⛔ **zero**, identico |

⭐ **VP9 dipinge 8 su 8 in tutti e quattro i casi**: il «no» è **di HEVC**, non del banco — il
controllo positivo c'era.

**La causa è misurata, non dedotta**: con `prefer-software` Chrome dice `Unsupported`, con
`prefer-hardware` dipinge ⇒ `[M]` **Chrome su Linux non ha un decodificatore HEVC software**. HEVC
esiste **solo via VA-API**, e senza GPU sparisce.

> ⭐ **Verificato una seconda volta, su un secondo strumento e sul browser vero dell'utente** — `[M]`
> 12 agosto, ricognizione fatta guidando il Chrome di CHUWI da fuori, con i due controlli:
>
> ```
> hev1.1.6.L93.B0 (Main)     no-preference SI · prefer-hardware SI · prefer-software  no
> hvc1.1.6.L93.B0 (Main)     no-preference SI · prefer-hardware SI · prefer-software  no
> hev1.2.4.L93.B0 (Main10)   no-preference SI · prefer-hardware SI · prefer-software  no
> vp09.00.10.08  (positivo)  SI · SI · SI
> avc1.42E01E    (positivo)  SI · SI · SI
> pippo.00.00    (negativo)  no · no · no
> ```
>
> ⇒ La firma è **esattamente** quella descritta da F2.5: HEVC cade **solo** su `prefer-software`,
> mentre VP9 e H.264 reggono tutte e tre le strade e il codec inventato è rifiutato da tutte e tre.
> ⚠ **E questa non è un banco**: è una ricognizione a mano, non lascia traccia su disco e non si
> rifà domani. Vale come **secondo testimone** della causa, non come misura della fase — e
> `isConfigSupported` resta la forma **E1** (*necessario scambiato per sufficiente*): dice che la
> configurazione è accettata, **non** che il pixel arriva. Quello lo dice il banco di F2.5.

#### ⭐⭐ 4. E su Firefox tre testimoni concordi dicono il falso

`[M]`: `mediaCapabilities` risponde `supported / smooth / powerEfficient: true` e `canPlayType`
risponde *«probably»* per **tutte e sette** le stringhe HEVC — mentre `isConfigSupported` dice
**false** e il pixel **non arriva**.

⇒ ⛔ **Una pagina che scegliesse il codec da lì non dipingerebbe niente**, e nessuno dei tre testimoni
l'avrebbe avvertita. È una trappola di prodotto, non di banco.

#### 5. Le altre misure, in breve

| | |
|---|---|
| ⭐ **il prefisso non conta** | `hev1.` **e** `hvc1.` vanno tutti e due in Annex-B puro `[M]`: Chromium decide dalla presenza della `description`, non dal prefisso. ⇒ la `[?]` che F2.3 aveva lasciato aperta **è chiusa** |
| ⛔ **il livello non lo controlla il browser** | Chrome accetta `L30` su un flusso di livello 3.0 e **dipinge 8 su 8** `[M]`. L'atteso del banco è stato **smentito**, col guasto verificato in vigore ⇒ **il controllo del livello deve stare dal lato server** |
| ⛔ **`ffmpeg` non rifiuta un flusso corrotto: lo conceala** | due storpiature su tre escono con stato **0** `[M]` ⇒ un giudizio sulla decodifica **non si prende mai dallo stato d'uscita**: si prende sui pixel |
| ⛔ **il codec non è un rivelatore di corruzione** | un byte girato nell'intestazione di uno slice ha lasciato il fotogramma **identico bit per bit** `[M]` — numero da avere in mano se qualcuno propone scorciatoie attorno alle garanzie di QUIC |
| ⚠ **x265 sceglie da sé** | `bframes=4` e `open-gop` di default, che nessuno ha chiesto: costano **un fotogramma di ritardo** contro un tetto di 50 ms. v1 li vietava a mano ⇒ si decide, non si eredita |
| ⭐ **`cattura.h` e `STUDI.md` §gnome §8.1 si contraddicevano** | sul buffer riciclato. Misurato: danno **parziale** e le sette bande **intere** ⇒ ha ragione `STUDI.md` §gnome, il commento nel codice è vecchio. ⛔ Se avesse avuto ragione `cattura.h`, la fase 2 avrebbe consegnato **mezzo desktop senza un errore** |
| ⛔ **la `[?]` del piano sull'ordine di `libei` è contraddetta** | `[M]`, riprodotta due volte: un client Wayland tenuto vivo *attraverso* la nascita del puntatore **riceve** `capabilities(0)` → `capabilities(1)`. La spiegazione *«non si iscrive mai»* **non regge**, e la caccia si sposta dal compositore al client. ⭐ E la regola vera è più stretta del piano: `ensure_virtual_device()` sta nei gestori di `NotifyPointerMotion*`, **non** in `Start()` — il puntatore nasce al **primo movimento iniettato**, la tastiera al **primo tasto** `[R]` |
| ⛔ **E2 preso sul campo** | sul server ci sono **due** monitor virtuali, `Meta-0`/`MetaVirtualMonitor` e `Meta-1`/`Virtual remote monitor`, **entrambi 1920×1080@60**: li distingue **il nome del prodotto**, non la misura. Sceglierne uno «per misura» o «per indice» è la forma E2 |

---

### Le decisioni prodotte

| | La decisione | Perché |
|---|---|---|
| ⭐ **D1 — Annex-B puro, e NESSUNA `description`** | il flusso sul filo è `[00 00 00 01] VPS · SPS · PPS · SEI · IDR` | quattro ragioni **lette**: è quel che `libavcodec` già produce (l'hvcC lo fa il muxer MP4, e sarebbe codice nostro da mantenere — `CODER.md` §4.1); in Chromium l'hvcC costa **un'allocazione e una copia per fotogramma** perché converte comunque ad Annex-B `[R]`; l'hvcC ha una trappola documentata sul profile-tier-level che fa **rifiutare** `isConfigSupported()`; tre progetti su tre fanno così. ⚠ **Il prezzo dichiarato**: WebKit fa la conversione inversa ⇒ si paga su Safari |
| ⭐ **D2 — il primo fotogramma è sempre chiave, coi parameter set dentro** | e ogni chiave si decodifica da sola | oggi `RCP.md` lascia **conforme** un delta in apertura, e il client **non ha modo di accorgersene**: nessun buco, nessun errore dal decodificatore ⇒ la fase 2 mostrerebbe spazzatura **senza che nessuno abbia torto** |
| ⭐ **D3 — il metro della fase è a due piani** | *piano 1*: `pagina ⟷ riferimento ffmpeg`, perdita ammessa **zero**, soglia **PSNR-Y ≥ 45 dB** — perché la decodifica HEVC è **normativa** · *piano 2*: `Δ = PSNR(pagina, cattura) − PSNR(riferimento, cattura) ≥ −0,5 dB` | il piano 2 è una **differenza**: il QP scelto da F2.3 si cancella, e **la soglia non invecchia** quando la codifica cambia. ⭐ E il riferimento `ffmpeg` è **il secondo lettore** che `PIANO.md` §0.4 dichiara mancante |
| ⛔ **D4 — il controllo del livello sta dal lato server** | non dal lato pagina | misurato: Chrome accetta un livello sbagliato e dipinge lo stesso |
| ⛔ **D5 — `codificatore.c` si riscrive, non si «riporta»** | ne sopravvive **la forma**, non le righe | 889 righe (la cifra del piano è giusta), ma **77 nominano H.264/AVC**, **47 nominano RDP/FreeRDP**, e *HEVC*, *265*, *10 bit* compaiono **zero volte**: è un codificatore H.264 AVC420 per RDP, quattro candidati tutti `h264_*`, tutti **NV12 a 8 bit**. Sopravvivono il giro dei tentativi, il divieto di ripiego silenzioso, il conto dei tempi, il divieto di `GLOBAL_HEADER` |

#### ⚠ E una correzione a una misura della fase 1

⛔ **La prova dei 10 bit «contando le bande»** — sonda **S2**, `web/` §3.7 punto 2 — **non
sopravvive alla codifica con perdita**: `[M]` rapporto **4,13** prima, **1,31** dopo QP 20.
⭐ Sostituita dai **due bit bassi del piano Y sulle zone sfumate**, che convergono con la misura
indipendente di F2.3 (**0,25** su catena sana contro **1,000** su un flusso troncato a 8 bit).
⚠ E la firma dei «multipli di 4» **non sopravvive alla conversione RGB→YUV**: i bit veri si misurano
**alla sorgente**, o non si misurano.

---

### ⛔ Che cosa NON ha funzionato

- ⛔ **La sessione del server è caduta**, chiamando `Shell.Screenshot` su zero monitor. Rimessa in
  due minuti; **7448 e 7501 verificate intatte** prima e dopo (girano nel contenitore). ⭐ Da lì è
  uscita la scoperta che la sessione nera è **fragile**, che vale più del disturbo.
- ⛔ **Un banco verde col difetto vivo** (F2.2, sopra). La forma E8, dentro un banco appena scritto.
- ⛔ **Nove difetti di banco** trovati girando (elenco sopra).
- ⚠ **In Chrome headless `VideoEncoder.flush()` non ritorna.** Aggirato con una finestra vera,
  ⛔ **non capito**: resta `[?]`, e chi lo riusa altrove deve saperlo.
- ⛔⛔ **E un difetto del COORDINAMENTO, che è mio.** La regola *«ogni agente possiede file suoi, e
  non tocca quelli degli altri»* — scritta per impedire che sei agenti si sovrascrivessero — ha
  prodotto questo: l'agente degli arbitri ha **fatto e riferito cinque ricertificazioni**, e
  **nessuna ha scritto una riga nel registro**, perché il registro apparteneva a un altro agente.
  ⇒ Per ore il conto ha detto *«B9 scaduta»* mentre B9 era stato rigirato **quattro volte**.
  ⚠ È la stessa forma che questa giornata ha inseguito tutto il tempo — ***«fatto» e «scritto dove
  qualcuno lo legge» sono due cose diverse*** — applicata al registro invece che al filo.
  ⭐ **La regola che ne esce**: *chi è autorizzato a certificare deve essere autorizzato a scrivere
  la riga della certificazione*. Un permesso a metà produce lavoro che non esiste per nessuno.
- ⚠ **`misura-cattura.c` stampa nella riga di esito la misura CHIESTA, non quella negoziata** — la
  voce 12-bis fu curata in `misura-wlroots` e **non lì**. Rilievo `[R]` **lasciato aperto e non
  toccato**: non è di questa fase, ed è lo strumento che certifica gli altri banchi.

---

### Che cosa resta `[?]`

| | |
|---|---|
| ⛔ **i 10 bit veri** | ⇒ **`DECISIONI.md` §2.3-ter, e non è più una `[?]`**: non escono da Mutter per **nessuna** strada — né MemFd né DMA-BUF, e i formati a 10 bit chiesti **per nome** danno `no more input formats` su tutt'e due, col controllo positivo accanto. ⚠ *Questa riga diceva «restano possibili solo per via DMA-BUF, non provata»: era una **copia invecchiata di una decisione**, cioè proprio quel che il riquadro in testa promette di non fare, e teneva aperta una speranza che una misura aveva chiuso (R13.5b)* |
| ⚠ **il telefono, e la `[?]` adesso è più stretta** | `[M]` **13 agosto 2026**, telefono vero — **SM-S916B**, Chrome 151.0.7922.108, Adreno 740: **4 sequenze su 4 dipinte**, HEVC Main10 **e** AV1 10 bit. ⛔ **Ma `copyTo` dà `format` `RGBA` e 4 byte per pixel**: al capo del dispositivo i dieci bit sono **otto promossi**, come alla sorgente. ⛔ **E resta aperto l'hardware**: senza cavo dati non si legge `Created MediaCodec <nome>`, quindi *«lo decodifica il silicio o la CPU?»* non ha risposta — e il criterio A/B esce `valido: false`, perché misura **spesa fissa**. ⚠ *Questa riga diceva «nessun numero prodotto, e nessuno dedotto», e i numeri stanno in `banchi/02-giudizio-sonda.jsonl` dalle 07:53 del 13 (R13.5a)* |
| ⛔ **il buffer della scheda sbagliata** | il banco della cattura **non lo vedrebbe**, e il suo verde **non lo assolve**. La macchina ha due GPU |
| ✅ **che un fotogramma arrivi davvero sul filo** | ⭐ **chiusa il 13 agosto**: l'utente l'ha guardato, e il registro del server lo scrive — `fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 2, 1920x1080, 9746 byte, FIN` |
| ⛔ **M5 — lo scarto di crominanza fra due decodificatori** | 0,9791 contro un limite di 0,98: è **l'unico rosso rimasto su catena sana** — M0 e M1 erano rossi ai giri delle 09:19-09:20, prima della cura del riscalamento. ⛔ **Non si riproduce sulla mira**, e **la soglia non è stata allargata**: il rosso non è stato curato, **è sparito quando è cambiata la scena** |
| ⛔ **P15** | `RCP.md` §7.1, il secondo di grazia sulle coordinate: **l'ultimo posto della fase dove un orologio decide**. Sta per esteso in `rapporti/F2-4-filo.md` |
| ⛔⛔ **«due utenti con due sessioni vere, ciascuno vede LA PROPRIA»** | ⛔ **non lo copre nessun banco**, ed è il buco più grande della fase. `[M]` 13 agosto: il caso `senza-palco` di `02-figlio-prova.py` prova **la metà negativa** — `prova` (uid 1001, tutti e quattro i campi chiesti al nucleo) **non** vede il desktop di `nicfio`, e il cliente RCP indipendente conta **zero** fotogrammi dove il 12 agosto ne contava uno conforme. ⛔ **Ma la metà positiva no**: su quella macchina `prova` non ha mai fatto login — niente `/run/user/1001`, niente bus, niente palco — quindi **un prodotto che non consegnasse niente a nessuno passerebbe allo stesso modo**. La metà positiva regge oggi **solo per uid 1000**. ⚠ Guardati e scartati: `01-b10-secondo-utente.py`, `attrezzi-prova2.sh`, `02-pam-i3.py --caso secondo` si fermano tutti **all'autenticazione**, non al vedere |
| ⚠ **`02-figlio-accendi.sh` conta i figli di tutti** | `pgrep -f -- "--figlio-interno" \| wc -l` non guarda **di chi** sono: allo spegnimento ha accusato due orfani che erano figli vivi di padri vivi (la 7693 di un altro banco e ⛔ **la 7561 dell'utente**). È la stessa forma che il file **vieta trenta righe più su** per l'azione `stato`. ⚠ Non cura, non ferma nessuno (`spegni` esce 0 lo stesso) — si accende solo quando due banchi girano in parallelo, e il 12 agosto infatti taceva. ⇒ ✅ **Curato in fase 3** (13 agosto 2026) — ⛔ **`[R]`, non eseguito**: la cura è letta nel codice e **non è stata girata**, quindi non porta la marca `[M]` |
| ⛔ **la risoluzione del desktop, `1920×1080`** | ⛔ **ereditata dalla scena di un banco, senza decisione né misura** — `grep 1920 DECISIONI.md` non trova nessuna decisione che la fissi, e in v1 era **2560×1080**. ⚠ È la tela che l'utente vedrà: `LEZIONI.md` §2.3-quater la vuole scritta come **provvisoria**, ed è quel che questa riga fa. ⇒ ✅ **CHIUSA il 13 agosto 2026, e decisa dall'utente**: **1920×1080 resta**, con il prezzo misurato accanto (tela dipinta all'**86 %**, **912 px di nero**) e la ragione di metodo scritta — `DECISIONI.md` §5.0-quinquies. ⛔ E le bande nere **non sono la risoluzione**: sono la forma della finestra |
| ⚠ **`VideoEncoder.flush()` in headless** | aggirato, non capito |
| ⚠ **le soglie M1b e M3 del metro** | **calcolate**, non tarate sul campo |
| ⚠ **Safari, e Chrome per Android/DeX** | manca il dispositivo |
| ⚠ **Firefox con `media.hevc.enabled`** | **non provato di proposito**: si misura il browser che l'utente ha, non quello che potrebbe configurare |

---

### Che cosa aspetta l'utente

#### ✅ 1. ~~Una decisione: HEVC esclude Firefox~~ — **decisa e chiusa il 12 agosto**

Il progetto promette *«nessun client da installare — basta un browser moderno»*, e con HEVC quella
frase valeva per **Chrome con una GPU che porta VA-API**: Firefox non dipinge, e Chrome senza GPU
nemmeno. ⛔ La difesa dei tre motori indipendenti — quella che `DECISIONI.md` §1.6 comprava al posto
dell'arbitro perduto — **su HEVC non c'era**.

✅ **L'utente ha deciso: `DECISIONI.md` §1.13** — HEVC **con un ripiego negoziato**, non un requisito
dichiarato, perché `CODER.md` §4.2 impone che ogni dipendenza mancante abbia un ripiego e che il
ripiego **si dichiari**.

🔸 **E il secondo codec è AV1**, chiuso lo stesso giorno **su una misura** e non su una preferenza:
`[M]` **quattro caselle su quattro** — i due motori, con GPU e senza — a **8 e a 10 bit**, e ⛔ **con
`prefer-software`**, cioè senza dipendere dalla GPU. ⭐ AV1 riempie **esattamente** le tre caselle che
HEVC lascia vuote, e ⭐⭐ i 10 bit su Chrome diventano per la prima volta **osservabili**
(`VideoFrame.format` = `I420P10`, massimo del luma **870** — impossibile a 8 bit).

⭐ **E non costa una riga di protocollo**: `av1` era già fra i valori ammessi di `RCP.md` §4.3 e aveva
già `codec = 2` in §6.2 ⇒ **§9 non viene sfiorata**. ⛔ *VP9, che pure era misurato funzionare,
sarebbe costato **RCP/2**: in §4.3 compare come l'esempio di valore che RCP/1 deve **ignorare**.*

⛔ **L'ordine di preferenza non si rovescia**: resta `hevc,av1`. HEVC è ancora il primo, perché è
quello che il telefono decodifica in hardware — ed è la domanda **S2**, ancora aperta.

#### ⚖️ 2. La sonda del telefono, che non si fa da soli

*Un telefono **Android** con **Chrome ≥ 108** — non il portatile — sulla stessa WiFi, con un cavo
USB e il debug acceso per `chrome://inspect`. Si apre l'indirizzo stampato da
`bash banchi/02-giudizio-telefono.sh serve`, si accetta l'avviso del certificato **una volta**, si
premono i bottoni 1 e 2 tenendo schermo acceso e scheda in primo piano: **~10 minuti**, più 10 di
fila per il decadimento quando le sequenze di F2.3 ci sono.*

⛔ **Non gli si chiede se «si vede bene»: la sonda produce numeri.**

#### ⛔ 3. E un debito della fase 1 che questa fase NON può scavalcare

⚠ *Il `README.md` elenca fra «quel che aspetta l'utente» i due ripieghi — il filo unico e il tetto
delle sessioni. **Quella riga è scaduta**: tutt'e due sono state decise dall'utente la sera dell'11
agosto, e stanno in `DECISIONI.md` §1.10 e §1.11. Corretto il 12 agosto 2026.*

⛔ **E `DECISIONI.md` §1.10 impone una cosa a questa fase**: la verifica PAM esce dal filo unico
**prima che la fase 2 si apra**, con un **processo aiutante** e non con un filo — perché PAM non è
affidabilmente rientrante.

La ragione è scritta lì, ed è del video: *«finché non c'è video il sintomo è «l'ultimo dei dieci
aspetta dieci secondi», sgradevole e circoscritto; dalla fase 2 in poi lo schermo di **tutti** quelli
collegati si pianta per uno o due secondi ogni volta che **qualcun altro** entra — e chi lo vedrà lo
attribuirà al **video**»*. `[M]` da B8: **da 1,0 a 2,2 secondi** per tentativo, e il ritardo lo mette
`pam_faildelay`, non il nostro codice.

⇒ ⭐ **Il banco di questa fase poteva nascere prima della cura — il prodotto no.** Questo giro ha
scritto solo banchi, quindi il debito non è stato violato; ⛔ **ma la prima riga di prodotto della
fase 2 viene dopo quella cura**, o si misura il video con dentro un difetto che si attribuirà al
video.

#### ⏳ 4. Il tetto delle sessioni resta 16, e il prezzo è dichiarato

`DECISIONI.md` §1.11: non si cambia fino alla fase 3, perché *«il limite vero non è un conteggio: è
un budget di pixel al secondo, e lo pone il codificatore»*. ⚠ Per due fasi **il codice dice 16 e la
specifica dice 10**.

---

---

### ⭐ LA SERA DEL 12 AGOSTO — il cancello si apre, e l'arbitro si corregge sei volte

*Su richiesta dell'utente — «fai una lista dei bug, assegna un agente a ciascuno, e arriva al
completamento della fase 2» — sono stati aperti **dodici difetti** (`rapporti/DIFETTI-12-agosto.md`)
e affidati a un agente ciascuno, in ondate che non si pestassero i piedi.*

#### ⭐⭐ Il cancello della fase 2 è aperto: `DECISIONI.md` §1.10 è applicata e misurata

La verifica PAM esce dal filo unico, **con un processo aiutante** — tre piani: il server scrive su un
`socketpair` SEQPACKET e torna al `poll`; uno **smistatore** che non chiama mai PAM legge e forca; un
**nipote** fa **una sola** transazione PAM e muore. ⇒ La rientranza di PAM non è *«gestita»*: **non è
in gioco**.

| | `[M]` 12 agosto 2026, cinque giri per lato |
|---|---|
| ⭐⭐ **chi NON si autentica** | picco **2259 → 3 ms** |
| ⭐ **la stretta di mano di chi arriva in quel momento** | **2262 → 10 ms** |
| ⚠ **chi si autentica** | 2260 → 1844 ms, cioè **invariato** — e deve restarlo: quel tempo lo mette PAM |

⛔ **E il fallimento è un no, non un forse** (I3): il `true` nasce in **un punto solo del programma**,
e sette strade portano a un no. Provato ammazzando l'aiutante con `SIGKILL` e presentando la parola
**giusta** → `RESPINTO` in 1001 ms, col controllo positivo accanto.

⭐ **E il filo NON è cambiato**: B3 `0→2→0` e B5 `0→1→0` danno gli **stessi identici numeri** di
prima della cura. L'ipotesi di chi l'ha scritta è diventata una misura.

#### ⛔ Il prodotto sul server non era il prodotto che avevamo scritto

`[M]`: **10 file su 24 diversi**, e i due che mancavano **del tutto** erano i due nuovi
(`aiutante.c`, `aiutante.h`); il binario girava dall'11 agosto con `exe` marcato `(deleted)`.

⭐ **E la cura non è la copia: è l'attrezzo che mancava** — `banchi/attrezzi-allinea-prodotto.sh`,
che **enumera l'albero intero** invece di un elenco scritto a mano. È esattamente la lezione del
difetto: *i due file che mancavano sono quelli che un elenco a mano non avrebbe mai avuto*. E non si
ferma ai sorgenti: ⛔ **sorgenti allineati e binario nuovo non bastano finché il processo vivo è
l'altro**.

#### ⛔⛔ E l'arbitro si è corretto sei volte in una sera

Le sette righe di F2.4 sono entrate in `RCP.md`; ⛔ **due erano sbagliate**, e le due cure che le
sistemavano ne hanno generate altre quattro. La successione **P8 → P11 → P13 → P14** e la lezione che
ne esce stanno in **`LEZIONI.md` §1.13**, ed è la cosa più riusabile prodotta oggi:

> ⭐ *Una tolleranza si scrive sulla **grandezza vera del fenomeno**, o si sposta di un passo a ogni
> rilettura.* La risposta esatta stava dentro i 28 byte dell'intestazione da tre giorni — il campo
> `numero` — e le prime tre stesure hanno usato una **grandezza sostitutiva**: una misura, un tempo,
> un evento.

⚠ **E chi le ha trovate, tutte e quattro: non chi rileggeva il documento, ma chi doveva far
rispettare la regola** scrivendo l'arbitro che la giudica.

#### Il conto dei banchi, la sera del 12 agosto

```
banchi nel catalogo: 15   (P5R e' entrato: il guasto che toglie il RITIRO, non il valore)
13  certificati e valgono oggi
 0  non riverificabili        ⭐ la riga di P5R adesso porta le impronte
```

⚠ **E il numero è sceso e risalito sei volte in una sera**, sempre per la stessa ragione dichiarata:
curare il prodotto o l'arbitro **fa scadere le certificazioni che li guardavano**. ⛔ *«Scaduta» non
è «fallita»*, e non è nemmeno «pulita».

#### ⭐ Gli attrezzi nuovi, e servono al prossimo giro

- **`attrezzi-allinea-prodotto.sh`** — quel che il `README` dichiarava mancante da ieri.
- **`02-sessione-guardia.sh`** — si mette **davanti** a una misura e fa le **due domande separate**:
  *«è viva?»* e *«ha un monitor?»*. Con tre bande d'uscita, così un **rifiuto** non si confonde con
  un fallimento del comando.
- ⭐⭐ **il controllo positivo dell'àncora** (in `01-b8-cronometro.py`, riusato in
  `01-b10-secondo-utente.py`) — allunga la riga di registro nei modi già successi e pretende che
  l'esito **non cambi**. ⛔ Nato perché **un'àncora fragile passa tutti i guasti**: rompersi *fa*
  diventare rossi, quindi nessuno dei quindici guasti la smascherava.
- **`01-b12-lancia.sh`** prende `B12_BERSAGLIO=innesto|prodotto`, e ⛔ **la scena finisce in ogni
  riga del registro**: chi non la dichiara ottiene *«non dichiarata»*, mai «innesto».

---

### ⭐⭐⭐ L'UTENTE HA VISTO IL PROPRIO DESKTOP — 13 agosto 2026, mattina

*Non è il giudizio di fase: è il fatto che la catena consegna. Si scrive qui perché è la prima volta
che un essere umano guarda l'uscita di questo prodotto, e perché fin qui tutto quel che ne sapevamo
erano decibel.*

> **«È lo sfondo GNOME, è OK.»** — l'utente, davanti a `https://192.168.0.2:7561/`, entrato come sé
> stesso.

⭐ Cattura → codifica → filo → `VideoDecoder` → pixel sullo schermo di una persona, con in mezzo un
protocollo scritto da zero. Il registro del server, dalla stessa sessione:

```
il client dichiara video.misura_massima=3840x2160   ← MISURATA decodificando, non dedotta dallo schermo
sessione aperta utente=nicfio  tela=1920x1080  vista=2559x922
fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 2, 1920x1080, 9746 byte, FIN — spediti 1, abbandonati 0
```

⚠ **E si scrive che cosa questo NON è**: non è il giudizio della fase, e la fase resta aperta.

⚠ *Questo riquadro, chiuso alle **08:36**, proseguiva così: «L'immagine è **piccola** — la pagina non
riscala alla vista, che §6.1 le impone — e il metro a pixel sulla catena vera non è stato girato».
⛔ **Tutt'e due le metà sono morte nell'ora e venti che è seguita**, e il documento è rimasto indietro
di quattro commit (R13.2):*

- ⭐ *il riscalamento è **in servizio** dalle **08:56** (`dc2f6a9`): due grandezze si chiamavano
  tutt'e due «larghezza della tela». E il rimando era **rotto** — `RCP.md` §6.1 è «Sui canali
  affidabili» e non nomina né vista né riscalamento; la sezione giusta è **`SPECIFICHE.md` §6.1**,
  ed è la terza volta in due fasi che un `§x.y` manda altrove (R13.8);*
- ⭐ *il metro a pixel **ha girato sulla catena vera** alle **09:50** — e quel che dice, per intero e
  senza arrotondarlo, sta nella sezione qui sotto.*

#### ⛔ E i tre difetti che l'utente ha trovato in una mattina, che 518 file di banco non avevano preso

| | Che cosa ha visto | Perché il banco non lo vedeva |
|---|---|---|
| **1** | ⛔ entrando come `prova` vedeva il desktop di **`nicfio`** | il deposito dei fotogrammi era **di processo**, non di sessione — e nessun banco entrava con **due** utenti diversi sullo stesso server |
| **2** | ⛔ **pagina vuota**, nessuna spiegazione | la pagina dichiarava `video.misura_massima` dalla **misura dello schermo** invece che da quel che sa decodificare ⇒ tela concessa più piccola della cattura, e il prodotto **si rifiutava di spedire**. ⚠ Le pagine di prova dichiaravano un tetto comodo: **solo la pagina del prodotto, su uno schermo vero, sbagliava** |
| **3** | ⚠ l'immagine è **piccola** | i banchi guardano **se** i pixel arrivano, non **quanto grandi** sono dipinti |

⇒ ⭐ **È l'invariante I8 in azione** — *il metro è quel che l'utente vede, non il numero che esce dal
banco*. Quella notte i banchi dicevano **48,27 dB**; l'utente ha detto *«non vedo nessun desktop»*, e
aveva ragione lui.

---

---

### ⭐ Il metro ha girato sulla catena vera — e che cosa dice, per intero

`[M]` **13 agosto 2026**. I quattro ingressi messi insieme per la prima volta: la **cattura** (il
buffer BGRx che il prodotto ha scritto con `--rilievo`), il **flusso** che il prodotto ha spedito, il
**riferimento** (lo stesso flusso decodificato da `ffmpeg` — ⭐ il *secondo lettore* che `PIANO.md`
§0.4 dichiarava mancante) e la **pagina** (`getImageData` dalla tela, in un browser vero collegato al
server vero).

| la scena | l'esito | PSNR-Y | strumenti vivi |
|---|---|---|---|
| ⭐ **la mira di F2.6 a sfondo del desktop** | **PROMOSSO** | **62,09 dB** (soglia 45) | **12 su 12**, zero ciechi |
| ⛔ **il desktop naturale dell'utente** | **BOCCIATO su M5** | 58,62 dB | 8 su 12 — ciechi *precedente · otto-bit · piani · ribaltato* |

⛔ **E le due righe non si scelgono: si leggono insieme.** Il verde è del metro **con la mira**; sul
desktop nudo il metro vede meno — senza i marcatori, M4, M7 e M-V si spengono per costruzione — e
trova un rosso. ⚠ Il rosso di M5 **non è stato curato: è sparito quando è cambiata la scena**, e
resta `[?]`.

#### ⛔ E uno dei dodici era verde per costruzione

Trovato da una **revisione avversariale** il 13 agosto, mandata a *refutare* la frase invece che a
confermarla. M8 leggeva un contatore `reset` che la pagina del prodotto chiama **`azzerati`**: valeva
sempre zero, e con lui due costanti scritte a mano. ⇒ **erano 11 vivi più un verde vuoto.**

⭐ Curato, **e la cura di una parola era sbagliata**: `azzerati > 0` è *il prodotto che si comporta
bene*, quindi leggerlo lì avrebbe prodotto un **falso rosso**. La grandezza vera è l'invariante
**`consegnati > completi`**. La storia intera, col controllo del falso rosso e con quel che la
certificazione **non** dice, sta in `rapporti/F2-6-giudizio.md` — qui non
si ricopia.

#### ⛔ Il punto cieco che non è del metro: **a monte della cattura**

Il fondo di verità del metro è **il buffer che il prodotto stesso ha catturato**. ⇒ Quale monitor,
quale sessione, **quale utente** sono fuori dalla sua portata: se il prodotto catturasse il desktop
di un altro utente, cattura, flusso, riferimento e pagina sarebbero **tutti d'accordo**, e il metro
direbbe **62 dB e promosso**.

⛔ **Ed è il difetto numero 1 che l'utente ha trovato in una mattina.** Lo copre un altro banco,
`02-figlio-prova.py` — rigirato il 13 agosto sul prodotto di oggi, **9 misure, 9 uscite 0, nessuna
uscita 2** — ⛔ ma solo per **metà**: vedi la tavola «Che cosa resta `[?]`».

---

### ⛔ Che cosa va detto insieme al verde, o il giudizio è preso su metà quadro

*Scritta il 13 agosto 2026, revisione **R13** rilievo 9. ⛔ Queste tre cose vivevano solo in un
riquadro del `README`, e chi leggeva **questo** documento — che il `README` gli dice di leggere per
primo — ne trovava una e mezza, e sbagliata.*

#### 1. Il **piano 2** del metro non è applicabile: la catena intera non è stata giudicata

Il metro ha due piani (`banchi/02-giudizio-metro.py:46,56`): **piano 1** confronta *pagina ⟷
riferimento* — il browser contro `ffmpeg` **sullo stesso flusso**, cioè due decodificatori
indipendenti; **piano 2** confronta *pagina ⟷ cattura*, che è la catena intera.

⛔ **Il numero che il verde porta è del piano 1.** Il piano 2 il metro lo dichiara **non
applicabile**, e la ragione è aritmetica: perché la sottrazione misuri il client e non la tela, la
perdita del codificatore deve stare **10 dB sotto** il rumore della tela a 8 bit, e qui ne sta
**7,01** (55,08 contro 62,09). Il numero grezzo esiste — **54,11 dB** — ma non è un giudizio.

> ⚠ **E si dichiara un difetto dello strumento**: il messaggio che finisce nel file di esiti dice
> *«non è almeno **6 dB** sotto la prima»* mentre il codice usa **10** (`02-giudizio-metro.py` · `m2_catena_intera()`).
> La soglia vera è quella del codice; il messaggio è rimasto alla prima stesura.

#### 2. I dieci bit sono **otto promossi**, e lo sono **a tutt'e due i capi**

- **alla sorgente**: ⇒ `DECISIONI.md` §2.3-ter — non escono da Mutter per **nessuna** strada, né
  MemFd né DMA-BUF, e i formati a 10 bit chiesti per nome danno `no more input formats`;
- **al dispositivo**: `[M]` 13 agosto sul telefono vero — `VideoFrame.format` è **`RGBA`** e `copyTo`
  dà **4 byte per pixel**, su una sequenza dichiarata `hev1.2.4.L90.90`, profondità 10.

⇒ ⛔ **L'etichetta `Main10` continuerebbe a dirlo per tutta la catena senza che nessuno se ne
accorga**: l'immagine viene bene lo stesso. Non è un ripiego nostro, ed è per questo che si scrive.

#### 3. Il telefono **è stato misurato**, ma non sull'hardware

`[M]` 13 agosto, **SM-S916B**, Chrome 151.0.7922.108, Adreno 740: **4 sequenze su 4 dipinte** — HEVC
Main10 **e** AV1 10 bit, `tela_rileggibile: true`.

⛔ **Quel che non ha risposta è «lo decodifica il silicio o la CPU?»**: nel browser il nome del
decodificatore non c'è, senza cavo dati non si legge `Created MediaCodec <nome>` da
`chrome://media-internals`, e il criterio A/B esce **`valido: false`** perché misura *spesa fissa*.
⇒ `[?]` dichiarata — ed è la misura **S2** che `PIANO.md` §1.2 mette in questa fase.

---

### ⭐⭐⭐ Il giudizio dell'utente — **dato il 13 agosto 2026, e la fase è chiusa**

L'utente ha riaperto `https://192.168.0.2:7561/` **come sé stesso** dopo la cura del riscalamento, ha
consegnato lo scatto come risultato, e — messe davanti le **sette cose dichiarate aperte** — ha deciso
di **chiudere la fase adesso**, con quelle scritte come aperte.

⭐ **E questa volta il giudizio non è solo una frase**: lo scatto è stato letto **pixel per pixel**, e
il numero si confronta con quel che il server dichiara.

| dal registro del server, `08:45:44 UTC` | dai pixel dello scatto, otto secondi dopo |
|---|---|
| `vista=2545x927` | la zona dipinta è alta **927 px** ⭐ **identico** |
| `tela=1920x1080` | larga **1648 px**, rapporto **1,7778** contro un 16:9 di **1,7778** |

⇒ ⭐⭐ **La pagina riscala alla vista rispettando la proporzione, e non di un pixel storta** — è
`SPECIFICHE.md` §6.1 misurata **sul vetro**, non dichiarata. Le bande nere (448 a sinistra, 464 a
destra) sono la conseguenza aritmetica di una finestra 2,74 che ospita una tela 16:9: l'alternativa
sarebbe **stirare**, che §6.1 vieta.

⛔ **E lo scatto ha sollevato una cosa che nessun banco aveva visto**: la tela viene dipinta all'**86%**
su un monitor largo **2560**. Non è un difetto del riscalamento — è la `[?]` sulla risoluzione, e
**912 px di nero** sono il suo prezzo, misurato.

⚠ *Si scrive quel che è successo e non una frase che non è stata detta: il verdetto dell'11 agosto
era una **citazione**, questo è una **decisione presa davanti a un elenco**. Le due cose hanno lo
stesso valore e non la stessa forma.* ⇒
`rapporti/GIUDIZIO-13-agosto.md`.


---

<a id="03-movimento"></a>

## Fase 3 — Il movimento

Aperta il **13 agosto 2026**, subito dopo la chiusura della fase 2.
⏳ **In corso.** Questo documento è aperto **all'apertura della fase**, non alla chiusura: è la
regola di [`README.md`](README.md) di questa cartella, e la ragione è che in un documento scritto
dopo le misure si *ricordano* invece di essere *registrate*.

> ⛔ **Stato al 13 agosto 2026, sera**: le **misure sono finite**, i **documenti sono allineati**,
> e restano due cose prima del giudizio — **rigirare le certificazioni** (curare il prodotto le ha
> fatte scadere, ed era previsto) e **il giudizio dell'utente**. ⚠ La fase **non si chiude su un
> documento completo**: si chiude su una misura che l'utente guarda.

> Il modello sta in [`PIANO.md`](PIANO.md) §0.2; le decisioni stanno in
> [`DECISIONI.md`](DECISIONI.md) e qui si **rimanda**, non si copia.

---

### Che cosa deve produrre

Uno **stream per fotogramma**, l'abbandono con `RESET_STREAM`, la **cadenza**.

**Che cosa vede e giudica l'utente**: il desktop **che si muove**, e dice se è fluido.

**I numeri da raggiungere**: ritardo **≤ 50 ms**, traguardo **40** (`SPECIFICHE.md` §3.2).

---

### ⛔ Le tre cose decise PRIMA di scrivere, e da chi

*Il punto di ripresa del 13 agosto ne elencava tre, e imponeva di scioglierle prima di qualunque
riga. Sciolte tutte e tre la mattina del 13 agosto, a codice ancora fermo.*

| # | La cosa | Decisa da | Che cosa è stato deciso |
|---|---|---|---|
| **1** | ⛔⛔ **la risoluzione della tela** | ⭐ **l'utente**, 13 agosto 2026 | **1920×1080 resta**. Era ereditata dalla scena di un banco e mai decisa; adesso è **decisa** |
| **2** | ⛔ **la scena** | il progetto, su `LEZIONI.md` §1.1 | un client **a schermo intero, opaco, che ridisegna a ogni *frame callback*** del compositore, che **conta da sé quanto disegna**, e che porta una **marca leggibile a macchina** |
| **3** | ⚠ **l'attesa dichiarata in anticipo** | il progetto, su `SPECIFICHE.md` §3.2 | il numero da battere è **≤ 50 ms**; il traguardo dei **40** è dichiarato **a rischio** sul muro dei 37 fotogrammi di Mutter — ⛔ **e l'attesa è stata sbagliata due volte**, vedi §3 |

#### 1. ⭐ La tela: **1920×1080**, e adesso è una decisione

La domanda era posta con il suo prezzo misurato accanto: sullo schermo dell'utente la tela viene
dipinta all'**86 %**, cioè **912 px di nero**. Le alternative messe davanti erano tre — tenerla,
portarla a 2560×1440 (lo schermo dell'utente), o accendere subito `SPECIFICHE.md` §6.1 (*la tela
nasce dallo schermo del client*, che il prodotto oggi **non** fa: `src/main.c` · `TELA_L` ha `TELA_L 1920`
scritto a mano).

⭐ **Scelta la prima**, e la ragione è di metodo: la fase 3 misura il **tempo**, non la geometria.
Con la tela ferma, un ritardo che sfora i 50 ms accusa l'architettura; con la tela cambiata sotto,
non si saprebbe se accusa l'architettura o il conto dei pixel.

⛔ **E le bande nere non sono la risoluzione**: 2545×927 di finestra fanno un rapporto **2,74**
contro un 16:9 di **1,7778**. Quelle bande sono la **forma della finestra**, e sparirebbero solo a
schermo pieno — cambiare la tela non le tocca. Va detto perché la `[?]` non venga riaperta
credendo di curarle.

⏳ **Resta aperta** — e va nominata alla fase in cui si accende — l'attuazione di `SPECIFICHE.md`
§6.1: *la tela nasce dallo schermo del client*. Oggi è una specifica scritta e non attuata.

#### 2. ⛔ La scena, e perché non è negoziabile

`LEZIONI.md` §1.1 la prescrive, e il prezzo di averla sbagliata è già stato pagato: **tutte le
misure di ritmo delle fasi 3-9 di v1 sono state buttate**. Un compositore Wayland consegna un
fotogramma **solo quando qualcosa cambia** ⇒ una misura di fotogrammi senza la scena dichiarata
**non è una misura**.

Le due parti, e la seconda è quella che si dimentica:

1. la scena **si muove a ogni ridisegno** — non a raffiche, come farebbe una scena mossa battendo
   tasti;
2. ⛔ **si conta quanto disegna il client**, che è il controllo che dice se il tetto è **del
   compositore** o **della scena**. Senza, il 7 agosto si sarebbe attribuito a Mutter un tetto che
   era della scena — e viceversa.

⭐ **E la fase 3 ne chiede una terza, che §1.1 non chiede**: la scena porta una **marca** — un
contatore che cresce a ogni disegno, e l'istante — rileggibile **dai pixel del fotogramma
decodificato**, e ⛔ **rileggibile dopo la codifica con perdita**, il che va **provato** e non
supposto. Serve a chiudere **M6** e a riaprire il `giro` di **M8** (qui sotto).

#### 3. ⚠ L'attesa, dichiarata prima della misura

Su GNOME il traguardo dei **40 ms** probabilmente **non si raggiunge**, per il muro dei 37
fotogrammi di Mutter. ⛔ Se la misura lo confermasse **non è un difetto nostro** — ed è una ragione
in più per la fase di KDE. Il numero da battere resta **≤ 50 ms**.

⭐ **Ma prima di dichiararlo si prova la cadenza disaccoppiata**, ed è lo **step 1** proprio perché
costa **tre celle e zero righe di prodotto**.

> #### ⛔⛔ L'attesa era sbagliata, e **la parte che ha sbagliato è quella che dava la colpa a un altro**
>
> *Scritto alla chiusura, e questa è la ragione per cui l'attesa si dichiara **prima**: perché poi
> si possa scrivere di quanto si era sbagliato, e in che direzione.*
>
> | quel che l'attesa diceva | quel che la misura dice |
> |---|---|
> | il traguardo dei **40** è a rischio | ⛔ **peggio**: si sfora anche il **tetto dei 50** — ⛔ *il numero, misurato con la codifica senza scheda, è tolto con la fase 18* |
> | ⛔ per il **muro dei 37 fotogrammi di Mutter** | ⛔⛔ **falso in tutt'e due i pezzi**: il 37 **non si riproduce**, e Mutter pesa **la parte minore** del ritardo. **Il grosso è nostro**, quasi tutto nel codificatore in software *(le percentuali, calcolate su un totale della codifica senza scheda, sono tolte con la fase 18)* |
> | ⛔ *«non è un difetto nostro»* | ⛔ **è un difetto nostro.** Ed è la riga che questa fase ha smentito nel modo più utile |
>
> ⚠ **E la cura dello step 1 riesce, ma non salva il numero**: monitor 120 + freno 90 danno `[M]`
> **61,4** fotogrammi al secondo — e il ritardo **non si muove**, perché il collo è altrove. La
> cadenza non è il ritardo (`LEZIONI.md` §6.2).
>
> ⭐ **Che cosa ha funzionato del metodo**: dichiarare l'attesa prima ha reso **visibile** lo
> scarto. Un'attesa non scritta si sarebbe riadattata al risultato, e nessuno avrebbe notato che la
> fase è entrata credendo di misurare la colpa di Mutter ed è uscita con la propria.

---

### Come è divisa: cinque step

⭐ **Su richiesta dell'utente, il 13 agosto 2026**: la fase è tagliata in **cinque step**, e a
ciascuno sono assegnati **uno o due agenti**, che si occupano di **sviluppo, prova e correzione**.
Il taglio segue le dipendenze, non delle fette arbitrarie.

| # | Step | Che cosa produce | Dipende da | Porta |
|---|---|---|---|---|
| **1** | ⭐ **La cadenza disaccoppiata** | la misura **M3** di `STUDI.md` §gnome §13: `maxFramerate` rinegoziato **da solo**, a monitor fermo | — | 7601 |
| **2** | ⛔ **La scena che si dichiara** | la scena, il conto dei suoi disegni, la marca e il suo lettore | — | 7602 |
| **3** | **Il prodotto: uno stream per fotogramma** | cattura continua · chiave/delta · l'intestazione da 28 byte · `RESET_STREAM` · il credito di stream | 1, 2 | 7603 |
| **4** | **La pagina: i fotogrammi consegnati** | molti stream in parallelo · FIN contro RESET · l'ordine · il buco → `RICHIEDI_CHIAVE` · ⭐ **il conto dei fotogrammi DIPINTI** | 3 | 7604 |
| **5** | ⭐ **L'anello del ritardo (S4)** | il numero, i sette controlli di `STUDI.md` §web §6.3, e il pezzo cieco dichiarato | 4 | 7605 |

⛔ **Ogni step ha porta, file di ban e socket propri**: in fase 3 i banchi girano in parallelo per
davvero, e due banchi che condividono un ban-file si fermano a vicenda.
⚠ **Le tre porte che non si toccano**: **7448** (prodotto di casa), **7501** (bersaglio di P5) e
soprattutto **7561**, che è **quella che l'utente apre** ed è anche il bersaglio del metro — si
legge, non si tocca.

⭐⭐ **E il mandato degli agenti è di REFUTARE, non di verificare.** È la lezione che il 13 agosto
ha prodotto il risultato migliore della giornata: la riga su cui si stava per chiedere il giudizio
è stata smentita da chi era mandato a smentirla, e uno mandato a *verificare* l'avrebbe confermata.
⭐ **E il mandato ammette il rifiuto**: una cura passata dall'alto può essere sbagliata, e chi cura
deve poterla rifiutare con un caso.

---

### ⭐ Che cosa la fase 3 eredita, con due occasioni dentro

| | |
|---|---|
| ⭐ **M6 si può chiudere** | «il fotogramma è del giro prima» è l'unico controllo che vede quel guasto, e **non è mai stato misurato sulla catena vera** perché mancava la cattura del giro precedente. In fase 3 i giri precedenti **ci sono** |
| ⭐ **il `giro` di M8 si può riaprire** | oggi è dichiarato **NON APPLICABILE** perché il prodotto non conosce il nome del giro del banco. Con un `numero` che cresce a ogni fotogramma la domanda torna ponibile ⇒ `rapporti/F2-6-giudizio.md` |
| ⛔ **P15** | `RCP.md` §7.1, il secondo di grazia sulle coordinate: **l'ultimo posto dove un orologio decide**. La fase 3 è tutta tempo — è qui che si scopre se regge |
| ⛔ **il punto cieco a monte della cattura** | il metro non guarda prima della cattura, e con molti fotogrammi il punto cieco **si allarga** |
| ⛔ **«due utenti, ciascuno vede la propria sessione»** | non lo copre nessun banco (metà positiva scoperta). Col movimento diventa **più caro** sbagliarlo, non meno |
| ⚠ **`02-figlio-accendi.sh`** | conta i figli **di tutti** invece dei propri: si accende solo quando due banchi girano in parallelo, **e in fase 3 girano** |

#### Gli esiti delle sei eredità, alla chiusura

| | esito |
|---|---|
| ⭐ **M6** | ✅ **chiusa**: da `[?]` a `[M]`, ⛔ **col limite della catena scritto accanto** — mancano la cattura PipeWire e la tela del browser riletta, quindi non è la catena intera |
| ⭐ **il `giro` di M8** | ✅ **riaperto**: la dichiarazione *«NON APPLICABILE per costruzione»* **cade**, con il `numero` che cresce a ogni fotogramma il controllo è **eseguibile** |
| ⛔ **P15**, il secondo di grazia | ⏳ non è quel che ha morso. L'orologio che ha fatto danni in questa fase è stato un altro: quello **del banco**, non del protocollo (§P1 a blocchi, `LEZIONI.md` §1.13) |
| ⛔ **il punto cieco a monte della cattura** | ⛔ **si è allargato come previsto, e adesso ha un numero**: 16-40 ms non compresi nel totale misurato. ⚠ E **su Xvfb non esiste**: la stima vale per l'utente, non per il banco |
| ⛔ **«due utenti, ciascuno vede la propria sessione»** | ⭐ **il prezzo è stato pagato, non rinviato**: il deposito del video è sparito **del tutto** — non «uno per sessione», **nessuno**. ⏳ Il banco che copre la metà positiva **resta da scrivere** |
| ⚠ **`02-figlio-accendi.sh`** | ✅ **curato** `[R]` — ⛔ **e non eseguito**: la cura è letta nel codice, non girata. Non porta la marca `[M]` |

---

### Lo stato della macchina all'apertura

⛔ *Verificato il 13 agosto 2026, non ricordato.*

| | |
|---|---|
| **albero** | pulito, `f2f21c2` |
| ⭐ **il catalogo dei banchi** | **15 su 15 certificati oggi**, zero scadute, zero non riverificabili — `python3 banchi/01-b12-guasti.py --registro`, rieseguito **all'apertura della fase 3** |
| ⏳ **la scadenza del giorno** | `01-s1b-eccezione.sh oggi` — **4 controlli su 4**, a **2,50 giorni su 7**; la scadenza che Chrome si è segnato è il **2026-08-17T21:09:47Z** |
| ⚠ **le porte in ascolto** | 7448, 7501, 7561 — le sole `:7xxx` |

⛔ **E va detto in anticipo**: la fase 3 tocca `rcp.c` e la pagina, e **curare il prodotto fa
scadere le certificazioni che lo guardavano**. Il catalogo va ricontato alla chiusura, non
all'apertura soltanto.

> ⭐ **È successo esattamente così, ed era previsto dal documento** — quindi non è una riga da
> correggere, è **la riga da rieseguire**. Alla sera del 13 agosto il catalogo dava **5 su 15**, con
> **10 scadute**, e ⛔ **nove banchi nuovi non erano ancora a catalogo** con le loro impronte:
> **sei numerati** — `03-b14` · `03-b15` · `03-b16` · `03-b17` · `03-b18` · `03-b19` — **più tre
> senza numero**: `03-scena`, `03-marca`, `03-deposita`.
> ⚠ **I tre senza numero sono quelli che si dimenticano**, ed è la ragione per cui il conto si fa
> con `ls banchi/03-*` e non a memoria: un catalogo contato sui nomi che uno ricorda è un catalogo
> che dichiara un denominatore falso (`LEZIONI.md` §1.9, regola 5).
> ⚠ **La ricontata si fa a codice fermo e a documenti scritti**, non prima: è la stessa ragione per
> cui questo documento si aggiorna tutto insieme alla chiusura.

---

### Che cosa è stato sviluppato

⛔ *Scritto alla chiusura, **a codice fermo**, dai numeri dei sei gruppi di lavoro — non a memoria.*

#### ⭐ Il numero della fase, che è quel che la fase esisteva per produrre

**Ritardo cattura → vetro**: ⛔⛔ **SFORA il tetto dei 50 e il traguardo dei 40**, con **6 giri** da ~800
campioni ciascuno e il **pezzo cieco di 16-40 ms NON compreso**. ⛔ *Il totale e i suoi percentili erano
misurati con la codifica **senza scheda** (libsvtav1 / libx265): tolti con la fase 18, non valgono più.* *→ rifatta coi browser veri in 4K e OpenH264: `fasi/18-senza-ffmpeg.md` §5.4.*
⚠ **Non è input → vetro**: il canale di input nasce alla fase 4 (`input` = 0 in **953 su 953**), e
al suo posto sta il controllo **P1**.

| dove se ne va | mediana | di chi è |
|---|---|---|
| disegno → cattura (il `pts` di Mutter) | 16,66 ms | Mutter |
| ⛔ **cattura → primo byte in pagina** | ⛔ *tolta con la fase 18 (codifica senza scheda)* | ⛔ **nostro** — codificatore in software |
| il filo | 0,32 ms | — |
| stream completo → `decode()` · decodifica · disegno | ⛔ *tolti con la fase 18 (misurati sulla catena con la codifica senza scheda)* | nostro |

⛔⛔ **Il muro non è di Mutter, e le tre prove sono queste**: la scena disegna **59,98/s con 0
attese**; il figlio del prodotto consegna **con ZERO attese a vuoto** — *non aspetta mai
Mutter*; il codificatore è **in software** e lo dichiara il prodotto stesso (libsvtav1 / libx265).
⇒ **Il grosso del ritardo è nostro**, soprattutto nel tratto cattura→filo. **La cura è la fase 8.**
⛔ *Il ritmo consegnato e la parte nostra del ritardo erano numeri della codifica senza scheda: tolti con la fase 18.*

#### La tavola dei cinque step, con gli esiti

| # | Step | Che cosa ha prodotto | Esito |
|---|---|---|---|
| **1** | ⭐ **La cadenza disaccoppiata** (M3) | `[M]` monitor **120** + freno **90** ⇒ **61,4** consegnati (60,04), mediana **16,66 ms** — cella **D**, pulita. ⚠ E la spiegazione, che è `[R]`: `min_interval_us = 10⁶/maxFramerate` **troncato a intero** contro un tick da 16666,67 µs — una **quantizzazione**, non un battimento, **letta nel codice di Mutter** | ⭐ **il fatto riesce** — ⛔ **ma M3 è MEZZA, non chiusa**: la causa non è misurata, il prodotto non sa chiedere quella cadenza, e la causa scritta in tre documenti era sbagliata |
| **2** | ⛔ **La scena che si dichiara** | `banchi/03-scena.c` — `wl_shm` + `xdg-shell`, marca a **144 bit**, quattro conti fra cui le **attese**, verifica `wl_surface.enter` — e il suo lettore | ✅ **34 verdi / 0 rossi**. M6 chiusa `[M]`, il `giro` di M8 riaperto |
| **3** | **Il prodotto: uno stream per fotogramma** | **135 fotogrammi**, `numero` 1→135 · **132 delta e 3 chiavi** · il primo dopo `SESSIONE` è una **chiave con FIN** · `RICHIEDI_CHIAVE` → chiave *(il tempo, della codifica senza scheda, è tolto con la fase 18)* · **10 stream azzerati contro 18 con FIN**, nessuna chiave abbandonata, **E8 provata sul filo** · ⭐ nei 28 byte il **`pts` di Mutter** (scarto dal nostro `CLOCK_MONOTONIC`: **11 347 µs**) · ⭐ **il deposito del video sparito del tutto** | ✅ **6 punti su 7 chiusi** · 13 controlli di certificazione, **13 verdi** · giro dal vivo **8 verdi, 1 rosso** |
| **4** | **La pagina: i fotogrammi consegnati** | i fotogrammi dipinti e il tetto a saturazione *(numeri presi con la codifica senza scheda: tolti con la fase 18)* | ✅ **19 casi verdi**, **8 guasti innestati su 8 accusati** |
| **5** | ⭐ **L'anello del ritardo (S4)** | il numero qui sopra. **P1** verde (N=25 → **+25,08**; N=60 → **+58,58**), con l'iniezione **fuori dal prodotto** e l'ancora d'orologio che **non ci passa**. **P3** verde **sui pixel veri**: 234 fotogrammi in movimento, **0 falsi positivi** | ✅ **banco 31 su 31, ponte 11 su 11** — ⛔ **ma P5 NON ESEGUITO, e adesso lo dice** |

> ⛔⛔ ⚠ **La riga dello step 1 diceva un'altra cosa, e va detto che cosa diceva.** *Fino alla sera
> del 13 agosto 2026 portava: «13 punti, 8 confermano, 0 smentiscono» e l'esito «⭐ **M3 chiusa, e
> riesce**». ⛔ **Falso tutt'e due.** Il file degli esiti della griglia,
> `banchi/03-b14-esiti-griglia.jsonl`, porta **tre righe**: il terreno e **due celle**
> (`griglia-apertura-120` e `griglia-freno-90`), e **tutt'e due portano `scena_sul_mio_monitor:
> false`** ⇒ sono rifiutate dal banco stesso, che sul verdetto stampa «⛔ la legge NON regge su **0
> punti su 0**». **Corretta il 13 agosto 2026**, rilievo del coordinatore della fase 3, verificato
> sui due file di esiti.*
>
> | | |
> |---|---|
> | ✅ **che cosa sopravvive** | tutto quel che sta in `banchi/03-b14-esiti.jsonl`: sette celle, **tutte** con `scena_sul_mio_monitor: true` — A (60/60 → 31,5), B (120/120 → 82,9), C (120/60 → 46,13), ⭐ **D (120/90 → 61,4, mediana 16,66, p99 20,43)** e i tre controlli. E con loro il **«sei decimi non si riproducono»** (la A dà 0,50 pulito) e il **«37 non si riproduce»** |
> | ⛔ **che cosa cade** | la **legge della griglia verificata**. La quantizzazione torna `[R]`: resta la spiegazione migliore che abbiamo, coerente con la cella D, **ma è letta nel codice di Mutter, non misurata** |
> | ⛔ **e cade anche** | il **riscontro incrociato**: in `banchi/03-b14-esiti-scena2.jsonl` la cella D porta `scena_sul_mio_monitor: false` e **1 fotogramma in 25 s**, e il controllo di ritorno di quella scena non torna. ⇒ **il 61,4 ha una scena sola** |
> | ⚠ **e M3** | **non è chiusa: è mezza** — il fatto è `[M]`, la causa `[R]`, il riscontro non c'è (`STUDI.md` §gnome §13) |
>
> ⭐⭐ **E la cosa che vale più della correzione**: la ragione del rifiuto è **la trappola numero uno
> della giornata** — *la scena deve stare sul monitor che si sta catturando* — che stamattina era
> già costata **quattro giri** ad altri due gruppi ed era già stata scritta in `LEZIONI.md` §1.1.
> ⛔ Il banco **lo aveva scritto nel proprio file**, campo `scena_sul_mio_monitor: false`, e nessuno
> l'ha guardato: si è letto il numero e non la riga accanto. ⇒ *Un banco che dichiara la propria
> invalidità non serve a niente se chi legge guarda solo il risultato* — `LEZIONI.md` §1.1-bis.

#### ⭐ E tre cose che il prodotto sa fare adesso e non sapeva stamattina

1. ⭐ **il deposito del video non esiste più.** Il prezzo dichiarato il 12 agosto — *«due utenti
   insieme non possono vedere tutt'e due il proprio»* — **è pagato**, e la cura non è «un deposito
   per sessione»: è **nessun deposito**. `wt_video_deposita` non esiste;
2. ⛔ **la cura B-18**, che è la più cara di tutte a non averla: uno dei tre percorsi di abbandono di
   un delta **non accendeva** la richiesta di chiave ⇒ **un solo delta saltato per mancanza di posto
   sfasciava l'immagine per sempre e in silenzio** — il `numero` non veniva consumato, quindi nessun
   buco, quindi il client non poteva chiedere la chiave, e con un GOP infinito non ne arrivava più
   una da sola;
3. ⛔ **la pagina nel worker**, scritta per intero, **misurata e tenuta spenta** — vedi qui sotto.
   ⭐ È uno sviluppo finito nella colonna delle cose che non hanno funzionato, **e ha prodotto lo
   stesso una riga utilizzabile**: la **decodifica** fuori dal thread principale guadagna; è la
   **tela** che affonda il conto *(i numeri, della codifica senza scheda, sono tolti con la fase 18)*.

---

### ⛔ Che cosa non ha funzionato

⭐ *Si riempie anche quando fa una brutta figura — è la regola 2 del modello. E questa fase ne ha
prodotta abbastanza da riempirla: ci vanno i **giri buttati**, le **cure rifiutate**, e i **banchi
che hanno accusato il prodotto a torto**.*

#### ⛔⛔⛔ 0. LA PEGGIORE, e non è stata trovata da un banco: è stata trovata **rileggendo un piano**

*13 agosto 2026, sera, a codice fermo, sulla richiesta dell'utente di **controllare che il piano
della sessione nuova non avesse problemi**.*

Il piano della sessione seguente si apriva con una corsia dichiarata *«quella da cui comincia la
sessione»*: **dare al banco un palco con una GPU vera**. Nasceva da una conclusione scritta la notte
prima, e scritta con la fermezza di una misura ripetuta — *«`[M]` 5 giri validi su 5:
`isConfigSupported` è `false` per tutte le stringhe HEVC. E la causa vera: su **Xvfb non c'è GPU
affatto** ⇒ non è un problema di codec, è un problema di PALCO»*.

⛔⛔ **Era la bandiera `--disable-gpu` del banco stesso** (`03-b17-ritardo.py` · `leggi_celle()`). La sonda
chiedeva a un browser **accecato da lei** se vedesse.

| Chrome, stesso Xvfb, stesso script, **una sola variabile** | webgl | HEVC |
|---|---|---|
| **senza** `--disable-gpu` | `ANGLE (Intel, Mesa Intel(R) Graphics (ADL-N))` | ⭐ **true** |
| **con** `--disable-gpu` | `niente webgl` | no |

⭐⭐ **E non è rimasta una dichiarazione**: il flusso uscito da `hevc_vaapi` è stato fatto
**dipingere** allo stesso Chrome — `[M]` **5 giri su 5**, 1920×1080, **119 fotogrammi su 120**,
`powerEfficient: true`.

⚠ **Il segnale c'era, ed era stato archiviato**: il piano stesso annotava *«un giro della sonda ha
detto HEVC = true con GPU, e non si è più riprodotto (0 su 5 successivi)»*, catalogandolo come
**anomalia da inseguire**. ⇒ Era **l'unico giro giusto**. *Un esito che non si riproduce una volta
su sei non è rumore: è una **variabile non dichiarata**.*

⭐ **Quel che NON è successo, e va detto perché era il rischio grosso**: `03-b17-ritardo.py` · `leggi_celle()` ha
**`gpu=True` di default** — `--senza-gpu` è opt-in ⇒ ⛔ **il numero della fase NON era
misurato al buio.** Era **la sonda dei codec** a esserlo, non la misura.

⇒ **Costo**: una corsia intera di un piano, e la sessione seguente sarebbe cominciata da lì.
⇒ **Riga nuova per `LEZIONI.md`, ed è la §2.0**: *un banco che risponde «no» deve scrivere **con che
palco** ha risposto* — «non c'è» e «non ho potuto guardare» hanno lo stesso aspetto, e il secondo è
più frequente del primo.

#### ⛔ 1. I giri buttati, e sono tutti dello stesso errore

⛔ **La scena stava sul monitor sbagliato**, e i monitor virtuali erano **quattro**. Una scena
aperta su quello che non si stava catturando produce un banco che **gira, non fallisce, e misura il
palco di qualcun altro**. *Costo: **quattro giri** — due allo step 3 e due allo step 1.*
⚠ E la stessa forma è arrivata come **cura passata dall'alto**: *«accendi su `Meta-3`»* — il monitor
giusto era `Meta-2`, e seguirla avrebbe fatto misurare il palco di un altro gruppo.
⇒ **Riga nuova per `LEZIONI.md` §1.1**: *la scena deve stare sul monitor che si sta catturando*, che
su un palco con monitor virtuali **non è quello dell'utente**.

#### ⛔⛔ 2. Le cure passate dal coordinatore e RIFIUTATE — cinque, e avevano ragione tutte e cinque

*È il risultato di metodo della giornata, e va scritto qui perché l'imputato è chi coordinava.*

| la cura passata | perché è stata rifiutata |
|---|---|
| la `ResizeObserver` | ⛔ **la premessa era falsa** |
| la seconda cura della vista | ⛔ **caduta alla misura**: `overflow-y: scroll` tiene `clientWidth` **fermo** |
| il **seqlock in contesa** | ⛔ **200 letture su 200 riuscite** con la scena a 1034 disegni/s. La causa era un **relitto a `seq` dispari**, non la contesa |
| *«quel che manca ai 60 è di Mutter»* | ⛔ **zero attese a vuoto** |
| *«accendi su `Meta-3`»* | ⛔ i monitor sono **quattro**, il suo era `Meta-2` |

⭐ **E il mandato ammetteva il rifiuto**, che è la ragione per cui i cinque si sono visti. Una cura
passata dall'alto può essere sbagliata, e chi cura deve poterla rifiutare **con un caso**.

#### ⛔⛔ 3. I banchi che hanno accusato il prodotto a torto

1. ⛔⛔ **lo `STREAM_LIMIT_ERROR`, ed è la specie peggiore: il banco aveva creato lui la condizione,
   e illegalmente.** Doveva provare che il prodotto regge un credito basso, e annunciava
   `initial_max_streams_uni = 6` **dopo** la stretta di mano — cosa che **RFC 9000 §4.6 vieta** ⇒
   ⛔ **il `6` non è mai passato sul filo.** `[M]` il server aveva **128 posti concessi** e ne ha
   aperti **14**. ⇒ **`ngtcp2` non ha violato niente, e lì il prodotto non ha un difetto.** ⚠ Il
   prodotto reagiva **correttamente** a una condizione impossibile, e la reazione corretta è stata
   letta come il guasto. ⭐ Ma cercandolo è uscito **B-18**, che era vero e peggiore;
2. ⛔ **«nessuna delle tre porte protette è in ascolto»**: misura presa dalla **macchina sbagliata**
   — il controllo girava su CHUWI, e 7448/7501/7561 ascoltano su **NIC-OS**. Verificato: `ss -ltn`
   su `192.168.0.2` le dà tutt'e tre vive, più la **7603** dello step 3;
3. ⛔ **la mia diagnosi del seqlock in contesa era sbagliata**, ed è la stessa specie: accusava il
   lettore mentre il difetto stava nella scena.

#### ⛔⛔ 4. Un verde in catalogo lo produceva lo STRUMENTO — ed era peggio di un falso verde

**Non era falso nel merito: non era mai stato provato capace di arrossire.** Su Xvfb i quadri non
girano, e in Blink l'evento `resize` si consegna **dentro** il giro di rendering ⇒ senza quadri non
arriva mai. A svegliare la conduttura era `Page.captureScreenshot`, chiamata solo `if args.copia`:
⛔ **un'opzione di comodo di stampa**, con un effetto collaterale non dichiarato.

| il banco ORIGINALE, sul prodotto SANO | esito |
|---|---|
| **senza** `--copia` | ⛔ **ROSSO, 5 pretese cadute** — fra cui «la tela è stata RICOMPOSTA (1 → 1)» |
| con `--copia` | verde (1 → 3) |

⛔ **E il buco strutturale**: le **quattro** pretese di quel blocco **non erano mai state innestate
con nessun guasto**. Verdi da sempre, senza che nessuno sapesse se sapessero fare altro.
⭐ **Curato**: il quadro si batte apposta (5 battiti fissi, non «finché diventa verde»); una spia del
palco conta quadri ed eventi; ⭐ **si giudica prima il palco** — se il `resize` non è arrivato il
banco dice *«IL PALCO, NON IL PRODOTTO»* e si ferma; due guasti nuovi accusano 5 e 4 pretese.
Tre giri: **9 giri, 5 scene sane verdi, 4 pagine guaste rosse**.
⚠ **Stessa trappola armata altrove e oggi non vulnerabile**: un secondo banco regge solo perché
nessuna sua pretesa passa da un quadro. Chi ve ne aggiunga una ci cade, **in verde**.

#### ⛔⛔ 5. La scena che correva a vuoto, e i suoi due sintomi erano lo stesso difetto

**Causa unica**: `buffer_libero()` chiamava `wl_display_dispatch()` **da dentro un gestore di
eventi** ⇒ `disegna()` annidata ⇒ da un `wl_surface.frame` in volo se ne fanno due, e si moltiplica.
⚠ Si accende **solo fuori da casa sua**: serve che i tre buffer siano occupati insieme, cioè un
compositore più carico — **quel che succede quando accanto gira una cattura**.

| | sano | guasto innestato | risanato |
|---|---|---|---|
| `fidato` | true | **false** | true |
| `frame` in volo, max | **1** | **18** (fino a 26) | 1 |
| disegni/s a 60 Hz | 60 | **461,7** (fino a 1034) | 60 |

⭐ **E i due sintomi erano lo stesso difetto**: una scena in corsa a vuoto non torna al ciclo
principale ⇒ ignora `--secondi` (**6 chiesti, 146 vissuti**) ⇒ il banco la **uccide** ⇒ la morte cade
a metà scrittura ⇒ `seq` del seqlock resta **dispari per sempre**. Il lettore vecchio falliva **3 su
3**, non «ogni tanto».
⭐ **Il rilevatore misura la CAUSA, non il ritmo**: *«i `wl_surface.frame` in volo non possono mai
essere più di 1»* — un invariante di protocollo, che non ha bisogno di sapere a che frequenza va il
monitor. E lo **stato d'uscita porta il verdetto** (2 = letto ma NON fidato), così `set -e` ferma chi
legge i disegni senza guardare `fidato`. **Chiusa: 43 righe verdi, 0 rosse.**

⛔⛔ **RIGA CHE VALE PER TUTTO IL PROGETTO**: *ogni cella di ritmo misurata con `03-scena` **prima**
del 13 agosto va rifatta o marcata `[?]`* — la scena poteva correre a vuoto senza dirlo.
⭐ **Le celle che contano dello step 1 reggono**: `banchi/03-b14-esiti.jsonl` usa `03-b14-scena`
(EGL, sua), e la matrice dei tetti rifatta con la cura è **invariata** (60,0-60,2 disegni/s,
0 attese).

> ⛔ ⚠ *Questa riga diceva: «**Il riscontro incrociato dello step 1 regge** […] ⇒ l'accordo **entro
> il 4 %** fra due scene indipendenti tiene». **Non regge.** La seconda scena del riscontro è
> proprio `03-scena`, cioè quella che questa stessa riga dichiara da rifare — e in
> `banchi/03-b14-esiti-scena2.jsonl` la sua **cella D** porta `scena_sul_mio_monitor: false`,
> `palco_stabile: false` e **1 fotogramma in 25 s**, mentre il suo controllo di **ritorno** dà 52,84
> contro gli 80,28 della sua cella B: **non torna**. Il 4 % vale su A (0,7 %), B (3,2 %) e il
> controllo positivo; C sta al **5,4 %** e il negativo al **7 %**. ⇒ ⛔ **La cella D — il 61,4 — ha
> UNA scena sola.** Corretta il 13 agosto 2026, rilievo del coordinatore della fase 3.*

#### ⛔ 6. Il metro si stava regalando 11 ms, e P5 si dichiarava verde senza esserlo

1. ⛔ **la prima stesura del metro chiudeva al richiamo del decodificatore**, regalandosi **~11 ms**
   nostri e misurabili su un tetto di 50. ⭐ **Il confine è stato spostato nella direzione scomoda**:
   il numero è salito di **~11 ms** e lo si è lasciato salire *(i due totali, della codifica senza scheda, sono tolti con la fase 18)*;
2. ⛔ **P5 si dichiarava verde**, e dopo tre iniettori `scavalcati = 0` non è *«l'anello regge»*: è
   *«il fenomeno non si è presentato»*. Adesso è dichiarato **NON ESEGUITO**. ⚠ E la causa vera del
   fuori ordine è la **dimensione** del fotogramma, non la rete: l'evento scatta al completamento
   dello stream, quindi l'ordine d'arrivo è quello delle dimensioni — e **una chiave grossa viene
   scavalcata dai delta**.

#### ⛔ 7. La pagina nel worker: scritta, misurata, e **sbagliata a metà**

`STUDI.md` §web §6.1 la prescriveva. Attuata, ha alzato il ritardo e abbassato di molto il tetto a saturazione. ⛔ **Ma il totale nasconde
la cosa che serve**, e la scomposizione la mostrava: la consegna al worker e il disegno salivano, la
decodifica scendeva. *(I numeri, della catena con la codifica senza scheda, sono tolti con la fase 18.)*

⭐⭐ **⇒ §6.1 non è sbagliata per intero: vale la DECODIFICA, non la TELA.** Il decodificatore
consegna prima quando non contende; è la tela che affonda il conto. ⇒ La riga utilizzabile non è
*«il worker è sbagliato»* — quella sarebbe solo una porta chiusa — ma *«la decodifica sì, la tela
no»*, che dice dove mettere il confine.

⭐ **E il meccanismo è la scoperta che cambia una regola**: `transferControlToOffscreen` **impegna la
tela al ritmo del quadro** — un `requestAnimationFrame` implicito che nessuno ha scritto. ⛔⛔ **La
prescrizione conteneva la propria smentita**: §6.1 prescriveva il worker e vietava il salto di
quadro, che il worker reintroduce in silenzio. Nessuna rilettura del documento poteva accorgersene
senza misurarla.

⚠ **E le due grandezze dicono cose opposte**: sulla catena vera il worker dipinge **di più**, a
saturazione crolla (`LEZIONI.md` §6.2).

⏳ ⛔ **`[?]` E questo va letto accanto ai numeri, non in fondo**: tutto è su **Xvfb, in software,
senza GPU**, e la penale è in gran parte sincronizzazione al quadro. ⇒ **Su hardware vero il conto
va rifatto prima di seppellire §6.1.** Il codice resta dietro `#video=worker`, **spento**, proprio
perché quel giorno il numero si rifà senza riscrivere niente (`DECISIONI.md` §2.8).

#### ⚠ 8. E le cose che non hanno funzionato senza essere colpa di nessuno

- ⛔ **`src/pagina.c` · `servi()`**: `strcmp(percorso, "/")` ⇒ `/?qualunque-cosa` prende **404** (`[M]`: `/`
  → 200 / 166107 byte, `/?video=worker` → 404 / 9). ⇒ **`?tela=desincronizzata` non è MAI stato
  raggiungibile**, e il commento della pagina indica da sempre una strada che non esiste. Non visto
  da nessuno perché i banchi servono la pagina da un `http.server` di Python, che il `?` lo ignora;
- ⛔ **i due gemelli `rcp.c` divergevano**, e **il prodotto non compilava per nessuno**. Riallineati
  la sera del 13;
- ⚠ **`weston-simple-egl` non è installato** sulla macchina di prova (rootfs in RAM), mentre due
  documenti lo davano presente e uno lo prescriveva come scena. Ha smesso di essere un riferimento:
  la scena della fase 3 è la nostra;
- ⚠⚠ **`/tmp` è una tmpfs da 3,8 G al 94 %**, 246 M liberi: ha già fatto fallire un giro di
  `03-b16` (Chrome non parte). ⛔ **Non è stata svuotata di proposito** — dentro ci sono le prove
  dei giri di oggi, e buttarle toglierebbe la **provenienza** dei numeri di questa fase.

---

### Il giudizio dell'utente — ⭐ DATO il 14 agosto 2026, mattina

> #### ⭐ **«Mi sembra abbastanza fluido, non il massimo ma pur sempre fluido.»**
> — l'utente, davanti a `https://192.168.0.2:7571/`, entrato come sé stesso

⇒ ⭐ **La fase 3 si chiude qui**, ed è la regola: *una fase si chiude su una misura giudicata
dall'utente, non su un documento completo* (`PIANO.md` §0.3).

#### ⭐⭐ E il giudizio è stato MISURATO — dalla registrazione fatta dall'utente

*L'utente ha registrato il proprio schermo mentre guardava (`Screencast From 2026-08-14 07-47-30.webm`).
⇒ **La sua impressione si può contare invece di crederla**: si segue il baricentro della barra bianca
fotogramma per fotogramma.*

⛔ *I numeri — fotogrammi rimasti uguali, ritmo del contenuto, pause, e il ritmo concorde del banco
dell'anello e del registro del prodotto — erano della catena con **AV1 in software**: tolti con la
fase 18. Restano il metodo e la conclusione sul ritmo.*

⛔ **E la causa del «non il massimo» è stata cercata, non supposta.** L'ipotesi naturale era
*l'irregolarità* — che la barra avanzasse a scatti. **Falsa**: la distribuzione dei passi è
**bimodale sui due valori attesi** (~7-8 colonne = un fotogramma di attesa, ~14-15 = due), e **solo
una piccola parte dei passi** sta fuori da quei due gruppi.

> ⇒ ⭐ **Il «non il massimo» non è instabilità: è il RITMO.** Con meno fotogrammi al secondo di
> quanti lo schermo ne mostri, **l'occhio vede spesso lo stesso fotogramma due volte** — e
> quello si sente, anche quando non c'è nessuno scatto.
> ⛔ **Quindi la strada per «il massimo» non è togliere jitter: è alzare il ritmo** — e il ritmo lo
> tiene giù un tratto che allora chiamavamo «il disegno».
> ⚠ ⛔ **E quel nome era falso, corretto il 14 agosto 2026** (deciso dall'utente): il disegno costa
> poco, e il tratto era **l'attesa del fotogramma dalla GPU** più il disegno. I numeri sono tolti con
> la fase 18 (catena che passava dalla memoria e da `sws_scale`). `fasi/rapporti/F4-A2-pagina-dipinge.md` e `F4-A10-anello-input.md`.

⚠ **I limiti di questa misura, dichiarati**: la registrazione stessa gira a 30,3/s, quindi **non può
vedere niente di più veloce**; e un fotogramma perso dal registratore si conterebbe come una pausa
del prodotto. ⇒ Il ritmo contato così è un **limite inferiore**.

#### ⛔ E i tre limiti del giudizio, scritti PRIMA che lo desse e non dopo

| | |
|---|---|
| **1** | vale per la catena con **AV1 in software** — ⭐ ed è **esattamente** la configurazione su cui è stato misurato il numero *(tolto con la fase 18: codifica senza scheda)* |
| **2** | ⛔ **non** vale per la codifica in hardware: **il browser dell'utente non dipinge HEVC** (§0-ter) |
| **3** | ⛔ **non ha visto un desktop**: ha visto **un monitor aggiunto** con dentro la scena dei banchi (§0-quater) |

#### ⭐⭐ E il giudizio ha prodotto DUE difetti che nessun banco aveva trovato

*È il valore che il piano attribuiva al giudizio — «l'utente guarda **il suo** desktop, un'altra
scena da quella misurata» — e si è realizzato in trenta secondi, due volte.*

> #### ⛔⛔ §0-ter — Il browser dell'utente NON dipinge HEVC, e chiede chiavi a vuoto
>
> `[M]` dal registro del prodotto, sessione vera del 14 agosto:
> ```
> 1748 fotogrammi consegnati (118 chiavi) … 0 guasti — codec 1
> [192.168.0.3]: §5.2 vuole una CHIAVE — richiesta girata al palco   ← 1 659 volte
> ```
> **Il server manda, il client rifiuta e richiede una chiave, per sempre.** Schermo nero.
> ⛔ **E i banchi dicevano il contrario** — 1 047 fotogrammi dipinti, 30 fps esatti, `consegnati ==
> dipinti`. La differenza: quel giro aveva **una scena sintetica e un Chrome lanciato dal banco**;
> questo ha **il browser dell'utente e il suo desktop**.
> ⇒ ⭐ *Un banco che dice sì e un utente che vede nero: il banco stava misurando un'altra cosa.*

> #### ⛔⛔ §0-quater — Il prodotto non mostra il desktop: ne AGGIUNGE uno vuoto
>
> `[M]` dal registro: `il nostro monitor e' **Meta-2**, **2 prima e 3 dopo**` — il prodotto trova la
> sessione grafica dell'utente e **le attacca un monitor nuovo**, poi registra quello. GNOME ci
> disegna **lo sfondo** (va su tutti i monitor) ma **barra, dock e finestre restano sul primario**,
> che nessuno guarda.
> ⇒ ⛔ **L'utente non vede il suo desktop: vede un secondo schermo vuoto.** E senza input (fase 4)
> lì non ci finirà mai niente da solo — quindi *«l'utente vede il desktop che si muove»* **non era
> realizzabile per costruzione**.
> ⛔⛔ **E la riga che ha nascosto tutto questo per due fasi** è il giudizio della fase 2 —
> *«è lo sfondo GNOME, è OK»*: **uno sfondo vuoto preso per un successo**. ⇒ `SPECIFICHE.md` §5.1
> vuole che la sessione remota **sia** la sessione grafica dell'utente. Non lo è ancora, ed è
> **lavoro della fase 5**.

---

### ⏳ Il punto lasciato APERTO dall'utente — il debito di chiave strozzato

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**a freddo non si può prendere una decisione:
l'esperienza potrebbe essere migliore di quello che si teme. Lasciamo il punto aperto**».*

⛔ **E la decisione è metodologicamente giusta, non una rinuncia**: è `LEZIONI.md` §2.6 — *l'utente
non è il banco*. Curare sulla base di un sintomo **temuto** invece che **osservato** è scrivere una
tolleranza su una grandezza che nessuno ha misurato (`LEZIONI.md` §1.13).

#### Che cos'è

`rcp_video_serve_chiave()` **non ha nessun chiamante in `src/`**: il debito di chiave arriva al
codificatore solo per una strada laterale (`webtransport.c`), **strozzata a una richiesta al
secondo**. Il prodotto è **conforme** a `RCP.md` §5.2 — la chiave arriva — ma paga il ritardo.

⛔ **E il numero non è quel che sembra: `[M]` 343 delta buttati in un giro solo NON sono 343
intoppi. Sono UNO, moltiplicato.** La catena:

1. si butta **un** fotogramma (legittimo, §5.1 — «si butta il passato quando è passato»);
2. scatta il debito di chiave (§5.2);
3. il server **rifiuta tutti i delta** finché la chiave non è pronta;
4. ⛔ ma la richiesta passa da una strada che ne lascia passare **una al secondo**;
5. ⇒ per quel secondo, **tutto quel che il prodotto produce viene buttato**.

⇒ A 60 fotogrammi al secondo, **un abbandono legittimo ne genera fino a sessanta illegittimi**, e
il sintomo — l'immagine che resta rotta **per un secondo intero** dopo un singolo intoppo — è
precisamente quel che un utente chiama *«va a scatti»* senza saper dire perché.

#### ⭐⭐⭐ CHIUSO IL 14 AGOSTO 2026 — e la risposta è **peggiore della domanda**

*Letto dal registro della sessione in cui l'utente ha dato il giudizio, come previsto: **costo
zero**, nessun banco nuovo.*

⛔ **La strozzatura a «una richiesta al secondo» NON tiene** — e non tiene **esattamente nel caso
per cui esiste**. `[M]`, due sessioni vere dello stesso prodotto, stesso giorno:

| sessione | intervalli fra due richieste di chiave | ritmo |
|---|---|---|
| **AV1** — il client dipinge | `33.558 · 34.585 · 35.586 · 36.586` | ⭐ **1 al secondo**: la strozzatura tiene |
| ⛔ **HEVC** — il client NON dipinge | `40.160 · 40.360 · 40.560 · 40.760` | ⛔ **5 al secondo**, esatte |

⇒ ⛔⛔ **Quando il client decodifica, la strozzatura funziona; quando NON decodifica — cioè quando
ogni chiave è sprecata — si apre a cinque volte tanto.** `[M]` **1 659 richieste** in una sessione,
ciascuna girata al palco, e **la chiave è il fotogramma più caro che esista**.

⭐ **E i tre numeri che il punto aperto chiedeva, con la risposta accanto:**

| | domanda | risposta misurata |
|---|---|---|
| **1** | quante volte scatta | **1 659** nella sessione del giudizio |
| **2** | quanti delta per volta | ⚠ **nessuno**: `abbandonati 0` in tutta la sessione AV1 ⇒ **lo scenario temuto — «un abbandono legittimo ne genera fino a sessanta illegittimi» — NON si è presentato** |
| **3** | quanto passa fino alla chiave | più nel caso sano che in quello rotto *(i tempi, della sessione con la codifica senza scheda, sono tolti con la fase 18)* |

⇒ ⭐ **Il timore era mal posto e il difetto è un altro**: non è l'abbandono a generare richieste, è
**il client che non decodifica**. E il freno che doveva contenerlo **si stacca proprio lì**.
⚠ *Il punto era stato lasciato aperto per non decidere su un sintomo temuto invece che osservato
(`LEZIONI.md` §2.6). Osservato, il sintomo era un altro.* ⛔ **Non si cura qui**: si cura dove nasce,
cioè in fase 5 insieme al difetto di HEVC.

#### ⭐ Come si chiudeva, e costava ZERO lavoro in più

Il prodotto **scrive già ogni abbandono nel registro**: `RCP.md` §5.1 lo impone — *«un fotogramma
perso in silenzio e uno abbandonato di proposito hanno lo stesso aspetto dal lato che riceve»*.

⇒ ⭐ **Basta leggere il registro DOPO la sessione in cui l'utente dà il giudizio.** Tre numeri, e
decidono da soli:

| che cosa si legge | che cosa dice |
|---|---|
| quante volte il debito di chiave è scattato | se sulla rete vera l'evento **capita** o no |
| quanti delta sono stati buttati per ciascuno | se il moltiplicatore è **60** o **2** |
| quanto è passato fra l'abbandono e la chiave | se il secondo di strozzatura si paga davvero |

⛔ **Se il debito non scatta mai sulla LAN dell'utente, il punto si chiude come `[?]` che non morde
qui** — e va nominato alla fase in cui la rete è cattiva per davvero. **Se scatta, il numero dice di
quanto**, e la cura si giustifica su un fatto invece che su un timore.

⚠ **Quel che NON va fatto**: chiudere questo punto perché il desktop *sembrava* fluido. La sessione
del giudizio si guarda **e si legge**, ed è la stessa disciplina con cui la fase 2 è stata chiusa —
davanti a un elenco, non a un'impressione.

---

### ⏳ Il secondo punto lasciato APERTO dall'utente — dove finisce di contare il tetto

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**alla tua domanda si può rispondere solo dopo
aver misurato i risultati con l'accelerazione HW**».*

#### La domanda che oggi nessun documento risponde

`SPECIFICHE.md` §3.2 chiede **≤ 50 ms**. ⛔ **Ma non dice fino a dove si conta**, e la fase 3 ha
scoperto che la differenza non è accademica:

| dove si smette di contare | con la codifica di **oggi** (software) | con un codificatore **gratis** `[R]` |
|---|---|---|
| al **disegno finito** | fuori | ⭐ **dentro il tetto, vicino al traguardo** |
| al **pixel acceso** (col pezzo cieco) | fuori | ⛔ **fuori anche a fase 8 fatta** |

*⛔ I numeri della tabella — le misure con la codifica in software e le somme dei tratti presi sulla
stessa catena — sono tolti con la fase 18. Restano gli esiti di allora.* *→ rifatta: `fasi/18-senza-ffmpeg.md` §5.4.*

⇒ **La stessa architettura è promossa o bocciata a seconda di dove si mette il traguardo.**

⚠ *E il confine della **misura** è stato spostato oggi, nella direzione scomoda: la prima stesura
dell'anello chiudeva al richiamo del decodificatore, regalandosi ~11 ms nostri e misurabili. Il
numero è salito di ~11 ms ed è stato lasciato salire. `CODER.md` §1-bis dichiara adesso dove
finisce la **misura** — non fino a dove vale il **tetto**, che è questa domanda.*

#### ⛔ Perché NON si decide adesso, e sono due ragioni indipendenti

1. **il pavimento con l'accelerazione vera non è misurato**, e non lo sarà finché la fase 8 non
   esiste;
2. ⛔ **il pezzo cieco è a sua volta una `[?]`**: **16-40 ms** è una forbice larga **due volte e
   mezzo**, e nessuna API JavaScript la espone (`STUDI.md` §web §6.2). Decidere dove finisce di contare un
   tetto di **50** appoggiandosi a un numero che oscilla di **24** è decidere su niente — ed è la
   grandezza sostitutiva che `LEZIONI.md` §1.13 vieta.

⇒ È la stessa disciplina del primo punto aperto: **non si cura, e non si decide, su un sintomo
temuto invece che osservato** (`LEZIONI.md` §2.6).

#### ⛔ E una cosa che va detta perché non venga letta male

**Il «codificatore finto» misurato in fase 3 NON è un codificatore hardware.** Risponde a
*«la catena regge quando la codifica costa poco?»*, che è una domanda utile e **diversa**. Un
codificatore vero in hardware ha un profilo di ritardo suo — la consegna alla GPU, l'attesa della
fine, il ritorno dei byte — che un finto **non modella affatto**.
⇒ ⛔ **Quel numero dice se l'architettura ha margine, NON quanto varrà la fase 8.** Le due cose non
si sommano, e chi le sommasse otterrebbe una previsione che nessuno ha misurato.

#### ⭐ Come si chiude

Alla **fase 8**, e nell'ordine:

1. si misura l'anello **con la codifica in hardware**, con lo stesso banco (`03-b17-ritardo.py`) e
   la stessa scena, così i due numeri si sottraggono davvero;
2. si guarda **dove cade il totale al disegno finito**, e **quanto vale davvero** il tratto della
   codifica quando è la GPU a farla;
3. ⛔ **solo allora** la domanda «fino al disegno o fino al vetro» ha davanti due numeri veri invece
   di una forbice, e l'utente decide **sapendo che cosa costa ciascuna delle due letture**.

⚠ **Quel che NON va fatto**: scrivere in `SPECIFICHE.md` una risposta oggi. Una soglia decisa per
prudenza, e poi trovata comoda, è una soglia che si sposta di un passo a ogni rilettura — è la
famiglia **P8 → P11 → P13 → P14**, che questo progetto ha già percorso quattro volte.

---

### ⭐⭐⭐ LA FASE NON SI CHIUDE QUI — la codifica in hardware è anticipata dentro la fase 3

*Deciso dall'utente la sera del 13 agosto 2026: ⭐ «**si anticipa la codifica HW alla fase 3. Per
questo però dopo servirà una nuova sessione**».*

⛔ **Quindi tutto quel che sta scritto sopra è vero e NON è finale.** Il documento resta com'è —
non si riscrive una misura perché è arrivata una decisione — e questa sezione dice **che cosa manca
ancora prima del giudizio**.

#### Perché, in un numero

⛔ **Più della metà del ritardo misurato era la codifica in software** *(i numeri, della codifica senza
scheda, sono tolti con la fase 18)*. Gli altri tratti, sommati, davano il **pavimento della catena a
codificatore gratis** *(la somma, presa sulla stessa catena, è tolta anch'essa)*: `[R]` **dentro il tetto dei 50, e vicino al traguardo dei 40**.

⇒ L'obiezione dell'utente, che è quella giusta: *«senza accelerazione hw stiamo ragionando e
sviluppando su numeri non molto affidabili»*. Un totale dominato da un pezzo che sta per essere
sostituito **non è un numero su cui prendere decisioni** — e le fasi 4-7 ne produrrebbero altri
uguali, da rifare dopo.

⚠ **Ma il danno era stretto, e va detto perché non si legga la giornata come persa**: dei risultati
della fase 3, **solo il verdetto sul ritardo** dipendeva dal codificatore. La cella **D** (61,4 a
monitor 120 e freno 90), il verde prodotto dallo strumento, **B-18**, **B-20**, il worker respinto,
la scena che correva a vuoto e i tre falsi rossi **non ci si appoggiano affatto**.

> ⛔ ⚠ *Questa riga cominciava l'elenco con «**La legge della griglia**». **Va tolta di lì**: la
> legge della griglia non è mai stata misurata — le due celle della griglia sono rifiutate dal banco
> stesso (riquadro nella tavola dei cinque step). Al suo posto sta la **cella D**, che è pulita e
> regge. **Corretta il 13 agosto 2026**, rilievo del coordinatore della fase 3.*

#### ⭐⭐ E si può fare — `[M]` verificato il 13 agosto sul server

```
Intel iHD driver 25.2.3   ·   /dev/dri/renderD128 e renderD129
VAProfileHEVCMain10     : VAEntrypointEncSliceLP    ← 10 bit, IN HARDWARE
VAProfileHEVCMain444_10 : VAEntrypointEncSliceLP    ← e perfino 4:4:4 a 10 bit
```

⛔ **E questa riga corregge un errore di oggi**: un agente aveva riferito *«su questo server non c'è
un codificatore hardware per nessuno dei due codec»*, e **nessuno l'aveva verificata**. È vera per
**AV1** — e stava già nei documenti — ed è **falsa per HEVC**. ⚠ È la stessa forma dei «37
fotogrammi di Mutter»: una riga **ripetuta** invece che **misurata**, che poi decide un piano.

#### Che cosa manca, e in che ordine

| | |
|---|---|
| 1 | ⛔ **il primo scoglio, e va affrontato per primo**: il codec negoziato nelle misure di oggi è **AV1**, perché la sonda HEVC di Chrome **fallisce su Xvfb** (`EncodingError`). Senza un client che accetti HEVC, l'anello intero non si misura — al massimo si misura il lato server, e sarebbe **mezzo anello** |
| 2 | la codifica HEVC in hardware nel prodotto, **su una copia** finché non è misurata |
| 3 | ⭐ **l'anello rimisurato con lo STESSO banco e la STESSA scena** — o i due numeri non si sottraggono |
| 4 | ⛔ **i CINQUE tratti affiancati**, non il totale: *tolta la codifica in software, gli altri quattro restano dove sono?* Se restano, l'architettura è **assolta**; se si muovono, c'è una contesa che nessuno ha visto |
| 5 | ⚠ **i fotogrammi consegnati accanto ai millisecondi** (`LEZIONI.md` §6.2): in v1 il costo per fotogramma scese da 41 a 6 **mentre i consegnati calavano da 29 a 22,7** |
| 6 | e **solo allora** il giudizio dell'utente, su un numero che non ha il freno a mano tirato |

⚠ **`EncSliceLP` è la codifica «a bassa potenza»**: veloce, ma con limiti suoi di qualità e di
funzioni. **Non è equivalente** alla codifica piena, e va dichiarato accanto al numero.
⭐ **E porta un'occasione**: `EncSliceLP` è l'entrypoint che `STUDI.md` §web nomina come *«da verificare»*
per i **sotto-livelli temporali** — cioè la strada per abbandonare un fotogramma **senza rompere
quelli dopo**, che oggi costa una chiave ogni volta.

⛔ **Che cosa NON si anticipa**: la **copia zero** resta alla fase 8. È lavoro suo, e non tocca
questo numero.


---

<a id="04-si-comanda"></a>

## Fase 4 — Si comanda

*Aperta il 14 agosto 2026, mattina. ⛔ Questo documento è aperto **all'apertura della fase**, non
alla chiusura: le misure qui si **registrano** strada facendo, non si ricordano dopo
(questo documento).*

---

### Che cosa deve produrre

`PIANO.md` §«Fase 4 — Si comanda», e in testa la priorità decisa dall'utente:

| | | |
|---|---|---|
| ⭐ **1** | **IL DESKTOP VERO** — deciso dall'utente il 14 agosto 2026, ed è **dentro la fase, in testa** | finché il desktop non si vede, **non c'è niente da comandare** |
| **2** | il **canale di input**: puntatore assoluto, pulsanti, rotella, lettere, posizioni | `RCP.md` §7.3 |
| **3** | il **puntatore disegnato dalla pagina**, e il cursore che non entra mai nell'immagine | `SPECIFICHE.md` §7.1 |
| **4** | le **due disposizioni della pagina** — classica con `Pointer Lock`, tocco coi sette gesti, **passaggio automatico sul contesto** | `DECISIONI.md` §5-bis.0-bis |
| **5** | le **scorciatoie che il browser si tiene**, **dichiarate** e non falsificate | `SPECIFICHE.md` §7.3-bis |

**E i due lavori ereditati dalla fase 3**, che senza di loro l'utente non ha niente da giudicare:

| | | dove |
|---|---|---|
| ⛔ | **HEVC non dipinge nel browser dell'utente** — 1 748 consegnati, **0 dipinti** | §03-movimento §0-ter |
| ⛔ | **il disegno**, il collo di bottiglia nuovo *(i numeri, con la scheda dalla memoria, sono tolti con la fase 18)* | `fasi/rapporti/F3-E-anello-rimisurato.md` |

**L'utente vede**: ⭐ **usa il desktop**. È il momento in cui REMOTIX smette di essere una
dimostrazione.

---

### Il banco *(scritto PRIMA di sviluppare)*

⛔ **Ogni sottofase scrive il proprio banco prima del proprio codice, e lo certifica prima di
crederlo** (`CODER.md` §3.3). L'elenco vive qui e si riempie strada facendo.

**Le dieci sottofasi, un agente ciascuna** *(lanciate il 14 agosto 2026, in parallelo)*:

| | sottofase | il banco | che cosa accusa | porte | esito |
|---|---|---|---|---|---|
| **A1** | ⭐ il desktop vero | `04-b20-desktop-vero` | la shell è **sul monitor che si cattura** — non uno schermo in più, vuoto | 7601-05 | ✅ **205 contro 0** |
| **A2** | la pagina che dipinge | `04-b21-dipinge` · `04-b22-disegno` | fotogrammi **dipinti**, non «consegnati» · il tratto del disegno scomposto | 7611-15 | ⭐ **le due accuse CADONO** |
| **A3** | il filo dell'input | `04-b23-filo-input` | le violazioni di `RCP.md` §7.3, ciascuna col motivo giusto | 7621-25 | ✅ **64 su 64** |
| **A4** | l'iniezione (libei/EIS) | `04-b24-iniezione` | l'input arriva **al desktop**, e il segno della rotella è quello giusto | 7631-35 | ✅ **27 OK, 0 NO** |
| **A5** | la tastiera | `04-b25-tastiera` | la lettera accentata con la disposizione giusta **e** con quella sbagliata | 7641-45 | ✅ **26 su 26** |
| **A6** | il cursore | `04-b26-cursore` | il cursore **non** è nell'immagine, e la forma arriva in banda laterale | 7651-55 | ✅ **0 contro 762** |
| **A7** | la pagina, modo classico | `04-b27-classico` | `Pointer Lock`, il puntatore disegnato, il rilascio alla perdita del fuoco | 7661-65 | ✅ **19 su 19**, due giri |
| **A8** | la pagina, modo tocco | `04-b28-gesti` | i sette gesti, e il passaggio automatico sul contesto | 7671-75 | ⭐ **24 su 25**, tre giri |
| **A9** | le scorciatoie (sonda S3) | `04-b29-scorciatoie` | «arriva **e basta**?» — i tre stati, su due motori | 7681-85 | ⭐ **594 misure**, 74 buttate |
| **A10** | i banchi di fase | `04-b30-anello-input` | ⭐ l'anello **input → vetro**, che alla fase 3 non era misurabile | 7691-95 | ⭐ **16 su 16**, e ⏳ `n=0` |
| ⭐ **O2** | **il numero dell'anello** | `04-b30-*` (esteso) · `04-b32-terreno` · `04-b32-coda` · `04-b32-ritmo` | ⭐ **il ritardo input → vetro, con `n` e la scomposizione**, e la coda che cresce | **7721-25** | ⭐⭐ **~140 ms, n = 326 e 322**, 10 controlli su 11 |

⭐ **E le cuciture le tiene il coordinatore, non gli anelli** — `src/input.h`, `src/tastiera.h`,
`src/cursore.h`, più `figlio.c`, `main.c` e il `Makefile`. ⛔ È la lezione di
`fasi/rapporti/F5-desktop-vero.md`: *il difetto della fase 3 non era **dentro** un pezzo, era **fra**
due pezzi ciascuno corretto per conto suo — e le cuciture, non avendo un proprietario, non le
guardava nessun banco.* Qui il proprietario ce l'hanno.

---

### Che cosa è stato sviluppato

#### ⭐ A5 — la tastiera *(chiusa il 14 agosto 2026)*

`src/tastiera.c` su `xkbcommon` 1.7.0: dato un carattere Unicode e la disposizione, quali codici
**evdev** premere e in che ordine. Rapporto in
`rapporti/F4-A5-tastiera.md`.

---

### Le misure *(si riempie strada facendo)*

#### ⭐ Il costruttore, prima di ogni misura — `[M]` 14 agosto 2026

L'albero della fase 4 **costruisce**: `make` esce 0 nel contenitore della macchina di prova, con
`-lei -lxkbcommon` collegate davvero e `input.o · tastiera.o · cursore.o` dentro il binario.
⛔ È il controllo che vale **prima** di tutti gli altri: dieci anelli interrotti a metà da un guasto
del server potevano lasciare l'albero rotto, e non l'hanno fatto. ⭐ E i **gemelli sono pari**
(`src/rcp.c` ≡ `banchi/rcp/rcp.c`).

#### ⭐⭐ LA CATENA DELL'INPUT È CUCITA DA UN CAPO ALL'ALTRO — `[M]` 14 agosto 2026

*E la cucitura è del coordinatore, per la ragione scritta in testa a questo documento.*

⛔ **Il fatto che nessun anello aveva in mano, e che cambia la forma del lavoro: il palco vive in un
ALTRO PROCESSO.** `libei` parla con la sessione grafica dell'utente, e quella ce l'ha il **figlio**;
QUIC, RCP e i byte del client stanno nel **padre**. ⇒ Fra il tasto premuto nel browser e il tasto
premuto sul desktop c'è **un confine di processo**, e nessuno dei due lati poteva attraversarlo da
solo.

| il tubo | il verso | dove |
|---|---|---|
| ⭐ **l'input** | padre → figlio | `MSG_INPUT` + `figli_input()` · i **sei ganci** in `rcp_avvia()` · il ponte `input_al_figlio()` in `main.c` |
| ⭐ **la forma del cursore** | figlio → padre | `MSG_CURSORE` a pezzi (un 256×256 in BGRA fa 262 144 byte, otto volte `PEZZO_MAX`) · `wt_cursore_diffondi()` · `rcp_cursore_forma()` |
| ⭐ **il campo `input` dei fotogrammi** | figlio → padre, **dentro il fotogramma** | ⛔ e questa è la scelta che lo rende **vero** invece di plausibile |

> ##### ⛔⭐ Perché il campo `input` lo timbra il FIGLIO e non il padre
>
> §6.2 promette che «l'effetto di quell'input è già nella scena». Il padre sa che cosa ha
> **mandato** al palco; solo il figlio sa che cosa il compositore ha **preso**, e in che istante ha
> catturato. ⇒ Riempirlo nel padre direbbe *«l'ultimo input spedito prima della spedizione»*: un
> numero più alto, e l'anello del ritardo misurerebbe un ritardo **più corto del vero — in nostro
> favore**, che è la direzione in cui nessuno sbaglia per caso.
> ⭐ Da cui due conseguenze scritte nel codice: il contatore avanza **solo se l'iniezione è
> riuscita**, e il fotogramma *tenuto* porta il **suo** `input`, non quello di adesso.
> `CODER.md` §1-bis: *il confine si sposta nella direzione scomoda*.

⭐ **E l'albero costruisce con tutti e tre i tubi collegati**: `make` esce 0, `-lei -lxkbcommon`
dentro, gemelli pari, e la marca nel binario verificata.

---

#### ⭐⭐ A1 — il desktop vero, e **la persistenza** `[M]` 14 agosto 2026

**L'A/B, stessa scena in movimento, stesso quarto d'ora:**

| | monitor | fotogrammi al client in 40 s | verdetto sui pixel |
|---|---|---|---|
| **con** `--virtual-monitor` | 1 → 2 | ⛔ **0** (`0 guasti`: uno zero vero) | ⛔ **VUOTO** |
| **senza** (curato) | 0 → 1 | ⭐ **205 conformi** | ⭐ **SHELL** (salto di luminanza 51,3 · fronti del testo 548) |

⭐ **E il banco non si fida di «c'è lo sfondo»** — è l'errore che ha nascosto il difetto per due fasi.
Distingue con **due indicatori di natura diversa**, calibrati su immagini vere *prima* di fissare le
soglie: il **salto di luminanza** al bordo basso della barra (11,8 shell / 0,07 sfondo) e i **fronti**
del testo dell'orologio (565 / 0). ⛔ Il terzo indicatore (la dock) **non distingueva, e sta scritto
che è stato scartato**.

##### ⛔ Tre cose che hanno smentito il mandato che avevo scritto

| | |
|---|---|
| ⛔ **`sessione.c` · `esegui()` non lo esegue nessuno** | `sessione_assicura()` **non è chiamata dal prodotto**. Su questa macchina `--virtual-monitor` lo impone un drop-in scritto a mano ⇒ **I7 violato**, e il desktop di `prova` si vedeva grazie a un file di configurazione, non al prodotto |
| ⛔ **la cura è in QUATTRO posti, non due** | coi due soli, `sessione_assicura()` avrebbe **ucciso la sessione giusta a ogni chiamata** (0 monitor = `SESSIONE_NERA` = «fai rinascere»). La macchina a stati è stata rovesciata, e dichiarato |
| ⛔ **la tela concessa è una promessa che nessuno mantiene** | client a 1280×720: il server la concede, il palco cattura a 1920×1080 (costante di compilazione), `rcp` rifiuta ogni fotogramma — `[M]` **145 prodotti, 0 spediti, client nero senza errori**. ⚠ E la misura la decide il **nostro** formato PipeWire `[R]`, non `RecordVirtual`: la `[?]` n. 1 di questo documento è **risolta, e la risposta era un'altra** |

##### ⭐⭐ E la persistenza REGGE — la tesi del difetto è **falsa**

*Nata da un'obiezione dell'utente, il 14 agosto: «deve lavorare anche quando nessuno guarda lo
schermo — altrimenti che senso ha la persistenza della sessione?».*

⛔ **La tesi da refutare era**: *«un client che si stacca porta via l'unico monitor: la sessione resta
senza dove disegnare, e le applicazioni se ne accorgono»* — cioè il difetto che in v1 mandava
`libmutter` in asserzione fallita. `[M]` otto letture in 11 minuti, sessione fatta nascere dal
prodotto curato, scena dichiarata (una finestra che scrive l'ora 5 volte al secondo, **sullo schermo
e su un file**):

| | |
|---|---|
| ⭐ il monitor | **mai sparito**: sempre **1**, `Virtual remote monitor`, anche nei quattro minuti senza nessuno. Mai `0` |
| ⭐ l'applicazione | **1 160 righe fra 07:37:36 e 07:41:36** — i 240 s a 4,8/s **senza un buco**, mentre non guardava nessuno |
| ⭐ `libmutter` | **nessuna asserzione nuova**: le 2 asserzioni e 7 critiche sono **costanti** dalla prima all'ultima lettura, e portano il pid di un `gnome-shell` che il prodotto stava **congedando** |
| ⭐ al riattacco | `riattacco-1` **120 fotogrammi conformi → SHELL**; `riattacco-2` → **SHELL**. ⭐ Ed è **la stessa finestra**: **pid invariato** (465823 all'inizio e alla fine, da 154 a 3 497 righe) — una finestra nuova avrebbe un pid nuovo |

⇒ ⭐ **L'esito è «il monitor c'è e nessuno lo cattura», che non è un difetto: è l'invariante I4
mantenuta.** E il merito è del **figlio**, che sopravvive al distacco per costruzione.
⚠ **Ma resta una cosa per la fase 5, e non era attesa**: **il palco muore col FIGLIO, non con la
sessione** ⇒ chi congederà un figlio che gira a vuoto **toglierebbe il monitor a una sessione viva**
— il difetto di v1 preso dall'altro capo.

⛔ **E tre numeri del banco mentivano**, trovati da chi li aveva scritti: il conteggio dei monitor era
**il doppio** (`GetCurrentState` elenca ogni schermo due volte) e sbagliava **nella direzione che
rassicura**; il contatore dei client **non esisteva** (QUIC vive su un solo socket non connesso, e
dava zero in tutt'e due i modi di guardare); e il file di esiti non era JSON valido. ⭐ **Nessuno dei
tre entrava nel verdetto — e proprio per questo nessuno li avrebbe controllati.**

---

#### ⭐⭐ A2 — le due accuse ereditate dalla fase 3 sono CADUTE

| | |
|---|---|
| ⛔ «HEVC non dipinge» | **falso**: `[M]` **8 caselle su 8** dipingono (profilo della stringa × profondità del flusso, HEVC e AV1, 64×48 **e** 1920×1080), compresa la combinazione esatta del prodotto — flusso Main10 letto con la stringa Main8. Palco = il **desktop vero**, GPU vera, dichiarato e verificato dall'altro capo. E in continuo: **60 su 60**, sei giri |
| ⛔ i «1 748 consegnati, 0 dipinti» | ⛔ **il conto era letto male**: nella finestra della sessione nera il contatore **entra a 1748 ed esce a 1748** per 2 min 38 s — il 1748 è **il residuo della sera prima** (`ciclo_fotogrammi` è statico di file). E il «1 659» era un `grep -c` su tutto il file da 6,7 MB: nella finestra vera sono **653** |
| ⇒ la causa vera | **il monitor aggiunto e vuoto**: nulla si muove, Mutter non consegna. **Lavoro di A1, non del codec** |
| ⛔ «il disegno costa quel tratto» | **falso**: il disegno vero costa poco, stesso confine della fase 3, e il controllo positivo su AV1 torna coi valori della fase 3 ⇒ **il cronometro era tarato**. *(I numeri, presi sulla catena con la codifica senza scheda o dalla memoria, sono tolti con la fase 18.)* |

⭐ **E la prima ipotesi dell'anello — profondità 8 negoziata contro flusso a 10 — è stata scritta
prima di misurare e smentita alla prima casella.** *Scritta prima, quindi smentibile: è il verso
giusto.*

---

#### ⭐⭐ A3 — il filo dell'input: **64 casi su 64**, e **16 guasti** certificati

29 violazioni + 25 verdi attesi + **10 su §7.2** (il cursore). 64/64 con una connessione nuova che
arriva a `ECCOMI` dopo ciascuna, e gli stessi numeri su due macchine.

⭐ **E la certificazione ha trovato DUE difetti del prodotto che nessun giro verde avrebbe visto:**

| | |
|---|---|
| ⛔ `6u + lung` a 32 bit | con `lung = 0xFFFFFFFF` vale **5**: un annuncio da 4 GiB passava il controllo di lunghezza |
| ⛔⭐ il `CURSORE_FORMA` da otto byte | spediva `w.len` invece di `n` ⇒ dichiarava `16×16` con **otto byte di corpo**, e **la pagina avrebbe chiuso a ogni cambio di forma**. ⭐ E la riga più preziosa: **il registro del server scriveva il vero e il filo un'altra cosa** — un banco che avesse guardato il valore di ritorno sarebbe stato **verde** |

⭐ **E la coppia dei limiti è provata nei DUE versi**, che è la cosa che un caso solo non dimostra:
`0×5` e `5×0` devono essere **rifiutati** *e* `0×0` (il nascosto) deve **passare**. Due guasti
opposti: togliendo il controllo parte il messaggio vietato; rendendolo troppo severo **sparisce per
sempre il cursore nascosto**. ⛔ Nessuno dei tre casi, da solo, distingue le due implementazioni.

⚠ **E la divisione dei compiti che ne è uscita**, che vale oltre il cursore: `cursore.c` decide **che
cos'è** quel cursore; `rcp.c` non deve **emettere** ciò che la specifica vieta. *Sono due obblighi a
due strati, e confonderli fa perdere quello che protegge l'utente.*

---

#### ⭐⭐ A4 — l'iniezione: l'input arriva DAVVERO al desktop `[M]` 14 agosto 2026

*Macchina di prova, utente `prova`, `libmutter` 48.7 · `libei` 1.3.901 · `wl_seat` v8.*

⛔ **Come si è misurato, ed è la metà che conta**: il testimone è **una finestra Wayland vera**
(`banchi/04-b24-testimone.c`) a schermo intero **sul monitor che abbiamo montato noi**, che stampa
una riga per ogni evento che il **compositore le consegna**. ⚠ Il registro dell'iniettore *non è* la
misura: dice che abbiamo chiamato una funzione.
⭐ **E il monitor non si spera, si sceglie per misura**: la sessione aveva già un `Meta-0` di un
altro client; il nostro `RecordVirtual` monta `Meta-1`, e il testimone si mette **su quello**. Senza,
ogni iniezione sarebbe finita sullo schermo sbagliato — la stessa forma d'errore che alla fase 2
teneva verde un banco mentre la cattura riceveva zero fotogrammi.

**Il giro sano: 27 righe `OK`, 0 `NO`, 0 `??`.** E il banco è **certificato con due guasti innestati
su una COPIA di `input.c`** — ⛔ e se la copia risulta identica all'originale **il banco si rifiuta di
girare**, perché un guasto che non cambia niente certifica il nulla:

| guasto | il banco ha detto |
|---|---|
| **`segno`** — si toglie l'inversione | ⛔ **ROSSO**: *«lo schermo remoto scorre AL CONTRARIO»* — ⭐ e la riga del mezzo scatto è rimasta **verde**: ha accusato **il segno**, non «qualcosa» |
| **`conto`** — il rilascio non rilascia | ⛔ **ROSSO** su tre righe, e una è **dal lato che riceve**: *«la finestra NON ha visto il rilascio del tasto»* |

##### ⭐ I quattro `[R]` portati a `[M]`

| | |
|---|---|
| ⭐⭐ **il `mapping-id` era INVERTITO in v1** | quello che dichiariamo (`277896a5…`) **non è** quello che la regione porta (`d72788c1…`): lo genera **Mutter** e ce lo pubblica, e `handle_record_virtual` **ignora in silenzio** la nostra proprietà. ⇒ Riusare v1 alla lettera dava **un puntatore che finiva sull'altro monitor** |
| **il segno della rotella, nei DUE versi** | `+120` (utente in su) → `axis_value120 = −120`; `−120` → `+120`. ⭐ Segni **opposti**: si misura il segno, non «che qualcosa si muove». E l'orizzontale passa com'è, misurato anche lui nei due versi |
| **i mezzi scatti** | `60` → `−60`. ⛔ Con `scroll_discrete` sarebbe stato `60/120 = 0`: la strada è `scroll_delta` |
| ⭐⭐ **i due ricambi silenziosi, riprodotti a dispositivo IN USO** | keymap `us`→`de` (68 402 → 70 138 byte, `ricambi_tastiera 0→1`) e geometria 1600×900 → 1280×720 (`ricambi_puntatore 0→2`). ⭐ **E il codice li regge**: rilegge keymap e regioni a ogni `DEVICE_ADDED` |

⭐ **E due fatti che nessun documento portava**: **la regione non è all'origine** (`1920,0`) — senza
sommarla il puntatore va sull'altro schermo **senza errore** — e **senza un consumatore PipeWire il
dispositivo assoluto non nasce affatto**.

⭐ **Il rilascio al distacco** (`RCP.md` §11): conto tenuto, `input_rilascia_tutto()` ritorna **2**, e
⭐ **la finestra vede i due rilasci**. ⏳ La metà «e si riattacca a verificare» è della fase 5, ed è
dichiarata.

⛔ **Che cosa NON ha funzionato**: **Firefox non chiede mai la pagina** in questa sessione (5 giri,
149 s, **zero richieste HTTP**, causa non trovata) ⇒ lo strumento è stato sostituito con il testimone
Wayland nativo — ⭐ più vicino alla verità, ⛔ **ma il ponte con `deltaY` scende da `[M]` a `[S]`**.
E **tre difetti erano del banco**: il contatore dei ricambi cieco (accusava «non riprodotto» su un
difetto avvenuto), la prova del rilascio che girava dopo i ricambi e **accusava la cosa sbagliata**,
e — dopo la cura — il banco che **leggeva il `PRONTA` di ieri** e stampava un `NO` falso contro il
prodotto.

---

#### ⭐⭐ A7 — la pagina, modo classico: **19 casi su 19**, due giri di fila

`[M]` 14 agosto 2026, Chrome 151, GNOME Wayland, pagina **isolata fra origini**. ⭐ **Il verdetto si
costruisce sui BYTE**, decodificati fuori dal browser da un lettore scritto leggendo `RCP.md` §7.3 —
**mai dal registro della pagina**. E il giudice è **certificato prima di ogni misura** (sano → otto
guasti → risanato).

| | |
|---|---|
| ⭐ **il caso del bordo** | spinto oltre con `Pointer Lock` esce **1919, 1079 e mai 1920**. ⚠ E l'attesa è **ricalcolata in Python** a cinque fattori di scala: a `1279×719` il valore vero è **1918,5**, dove `round`/`ceil` direbbero 1919 — cioè il banco sa distinguere l'arrotondamento giusto da quello che chiude la sessione |
| ⭐ **`Ctrl+C` copia** | `29↓ 46↓ 46↑ 29↑`, **zero `LETTERA`**; e `Maiusc+a` → **una** `LETTERA` U+0041 e **zero** posizioni |
| ⭐ **il rilascio alla perdita del fuoco** | fuoco tolto con una **scheda vera**: i due rilasci escono. A fuoco tenuto: **nessuno** |
| **la rotella** | +120 su, −120 giù, **+60 mezzo scatto**, e il segno invertito **una volta sola** (dal server) |

⛔⭐ **E la tesi 5 è metà refutata, con una misura**: l'`id` è confermato, ⛔ ma **la premessa
dell'`istante` in `RCP.md` §7.3 era FALSA** — `performance.now()` ha grana **5 µs**, non 1 ms:
**duecento volte** più fine. ⇒ La riga è stata corretta in `RCP.md` il 14 agosto: la regola
sopravvive alla premessa, ma un client che moltiplicasse i millisecondi per mille butterebbe via
**199 parti su 200** di una misura che ha già.

⛔ **Che cosa NON ha funzionato**: `unadjustedMovement` **rifiutato** da Chrome su Wayland (ripiego
dichiarato) · la lock è **negata senza fuoco** · ⚠ **tre rossi su tre erano del BANCO**, non del
prodotto (l'attesa sul bordo, `wheelDelta` che gonfia il mezzo scatto a uno intero `[M]`, e le fasi
marcate a tempo invece che a quiete) · **«e poi che cosa fa il desktop» non è misurato** · e **solo
Chrome**.

---

#### ⭐⭐ A6 — il cursore: il canale aveva un capo e nessuna sorgente

| | |
|---|---|
| ⛔ **il `[R]` portato a `[M]`** | con la negoziazione di ieri: **62 buffer, 0 `SPA_META_Cursor`, 0 `CURSORE_FORMA`**. Lo stesso strumento con una riga in più: ⭐ **49 su 49**. ⇒ *Lo zero era uno zero, non una cecità* |
| ⭐ **il cursore NON è nell'immagine** | riquadro 96×96 sul puntatore fermo su tinta nota: **0 pixel** fuori tinta con `cursor-mode=2`, ⛔ **762** con `cursor-mode=1` — il controllo positivo sui pixel veri |
| ⭐ **la forma arriva, riletta dai byte** | 48×48 (attivo 6,2) · `0×0` nascosto · 48×48 al ritorno · 32×32 (3,1). **Zero violazioni** di §7.2/§5.5 |
| ⭐ **e non si rimanda mille volte** | 52 metadati ⇒ **4** forme (7,7 %); **40 movimenti ⇒ 0 forme nuove** |

⛔ **E una cosa che va dichiarata invece di inventata**: su un flusso appena aperto la forma **può non
arrivare mai** — `cursor_bitmap_invalid` nasce falso e si accende **solo** su `cursor-changed`
(43 metadati su 43 con la sola posizione). `cursore.c` lo **dichiara**, e non inventa una freccia.

---

#### ⭐⭐ A8 — la pagina, modo tocco: **24 verdi su 25**, tre giri

`[M]` 14 agosto 2026, Chrome 151. Giudice certificato **verde → rosso → verde su 5 guasti**, uno per
**famiglia di confusione**; 78 messaggi §7.3 con `id` 1→78 crescenti.

⛔⭐ **E le tre confusioni che ha trovato, `DECISIONI.md` §5-bis.3 non ne nomina NESSUNA** — cioè la
tabella dei sette gesti descrive che cosa fare, non che cosa *si confonde con che cosa*:

| | |
|---|---|
| ⛔ **tap-e-mezzo e doppio clic sono lo stesso gesto** | ⭐ e la cura **non è una soglia**: *si preme al contatto e si rilascia al distacco*, e le due strade divergono da sole **senza ritardo**. ⚠ La stesura «prudente» — aspettare per decidere — **rompe il doppio clic**. Provato coi casi gemelli |
| ⛔ **«2 dita tap» contro «1 dito tap ripetuto»** | un **clic destro che esce come doppio clic sinistro**. ⛔ Nessuna soglia in ms li separa, e separarli costerebbe **300 ms su ogni clic** — vietati da `CODER.md` §1-bis. ⇒ La soglia è **una sovrapposizione: ≥ 1 campione**, e sotto quella il difetto è **DICHIARATO**, non nascosto |
| ⛔ **rotella contro pizzico** | che la tabella non nomina affatto: si confronta Δdistanza contro Δcentro, e si decide **una volta sola** |

**Le soglie, in ms e px CSS**: `T_TAP` **180 ms per CONTATTO** · `D_TAP` 9 px · `T_SEQUENZA` 300 ms ·
⭐ `D_STESSO_DITO` **40 px ≈ 10 mm** — e viene da `SPECIFICHE.md` §7.1: **lo stesso millimetraggio che
motiva il puntatore disegnato** separa il tap-e-mezzo dal tap a due dita · `D_PIZZICO` 24 px `[?]` ·
`PX_PER_SCATTO` 40 px `[?]`.

⭐ **Due difetti trovati dal banco e non dalla lettura**: la durata va misurata **per contatto** (o il
tap a tre dita **non esce mai**), e **un dito che si stacca sposta il centro di 40 px senza che
nessuno si muova** — veniva letto come rotella.

---

#### ⭐⭐ A9 — le scorciatoie: **594 misure, 520 credibili, 74 buttate e CONTATE**

`[M]` 14 agosto 2026, Chrome 151 e Firefox 140 ESR.

> ##### ⛔⛔ Lo stato di mezzo esiste, è misurato, **ed è LARGO**
> `[M]` **18 combinazioni su 42** su Chrome in finestra arrivano alla sessione remota **e** fanno
> agire anche il browser. ⇒ ⭐ *Una prova che avesse guardato solo il lato della sessione le avrebbe
> dichiarate **tutte verdi**.* È la ragione per cui §7.3-bis dice che la misura non è «arriva?» ma
> «arriva **e basta**?», e adesso quella riga ha un numero sotto.

**La ricetta, ogni gradino col suo numero:**

| gradino | Chrome 151 | Firefox 140 ESR |
|---|---|---|
| `preventDefault()` nella pagina | caso peggiore **18 → 0** | **15 → 0** |
| schermo intero **+ Keyboard Lock** | riservate dal browser **8 → 0** | ⛔ **impossibile**: non ha nessuna delle due forme, e a schermo intero **PEGGIORA** (5 → 7) |
| i bottoni a schermo | restano **5** | idem |

⛔ **E quel che resta perso non è del browser**: `Super`, `Super+D`, `Alt+Tab`, `Alt+F2`, `Alt+F4`,
`Ctrl+Alt+Canc` — sono del **compositore del client**, e **nessuna API le riprenderà mai**.

⭐⭐ **E il giro salvato dalla regola di credibilità vale quanto la misura**: un giro di Firefox usciva
*«Firefox si tiene tutto, `Ctrl+C` compreso»* — **verosimile e interamente falso**, perché
`document.hasFocus()` ⛔ **mente su Firefox/Wayland**. ⇒ Da lì il cancello vero: **non si chiede alla
pagina se CREDE di avere il fuoco — le si chiede di DIMOSTRARE che riceve i tasti.** 74 righe su 594
buttate da quella regola, e **contate**.

⛔ **Non provati, e non dedotti** (ciascuno col suo strumento scritto nel rapporto): Safari/WebKit,
iPhone, **DeX**, **PWA su Chrome per Android**, Firefox ≥ 151, Edge. ⭐ La PWA è `[M]` **solo sul
desktop** (`--app`: **0 riservate già in finestra**); la metà Android resta `[?]`.

---

#### ⛔⭐ E la quinta cucitura rotta della fase, trovata dall'anello che la subiva

`REMOTIX_PUNTATORE.muovi()` non accendeva `cl_noto` ⇒ su una pagina che nasce in **disposizione a
tocco** e non entra mai nel modo classico, il dito muoveva **un puntatore che non compariva mai** —
⛔ e senza nessun errore, da nessuna parte. Cura di **una riga**, chiusa dal coordinatore.
⭐ **E l'anello del tocco nel frattempo aveva fatto la cosa giusta**: ha verificato la cucitura, ha
**dichiarato il ripiego nel registro** e ha disegnato un puntatore suo — invece di tacere o di
rompersi. Il ripiego sparisce da sé adesso che la riga c'è.

⚠ ⭐ **Cinque cuciture rotte su cinque erano FRA due pezzi, e nessuna dentro uno.** È la lezione di
`fasi/rapporti/F5-desktop-vero.md` verificata cinque volte in una fase sola.

---

#### ⭐⭐ A10 — il metro dell'anello **input → vetro**

| | |
|---|---|
| ⭐ **la certificazione** | **16 guasti innestati accusati su 16** · **53 controlli su 53** (uscita 0) · di cui il ponte **19 su 19** |
| ⭐ **tre guasti NUOVI**, che alla fase 3 non erano nemmeno esprimibili | e il più importante è *«la mediana sale di N ma **nel tratto sbagliato**»*: ⛔ **un metro così non diventa mai rosso — dice bugie sulla diagnosi**, che è esattamente quel che è successo all'etichetta del disegno |
| ⭐ **la catena in UNDICI tratti** (quattro nuovi) | provata sul finto che li somma al totale con scarto **0,00 ms** |
| ⛔ **e il numero NON c'è: `n = 0`, uscita 3** | *«non ho niente da giudicare»* — ⭐ **e dirlo è la cosa giusta**: il client non manda ancora §7.3. È il difetto che il validatore della fase 1 aveva (conforme e «niente da giudicare» con lo stesso codice d'uscita), qui evitato per costruzione |
| ⭐ **i pezzi ciechi sono DUE, non uno** | quello in uscita (16-40 ms, noto) e ⭐ **quello in INGRESSO** — `[?]` **4-12 ms** fra la mano e `event.timeStamp` — **che nessuno aveva mai nominato** |

⛔ **E il suo controllo di precondizione ha dato un FALSO VERDE**: cercava `0x0101` in `pagina.html`,
ne trovava cinque, ed erano **tutti commenti**. ⚠ *Pagata dentro il banco che esiste per non pagarla.*

---

#### ⭐⭐⭐ O2 — IL NUMERO C'È: **~140 ms fra la mano e il pixel**, e sono **due giri che concordano**

*14 agosto 2026, pomeriggio. Rapporto in `rapporti/F4-O2-anello-input.md`.*

`[M]` **139,40 ms** (n = **326 su 326**) e **141,60 ms** (n = **322 su 322**), due giri indipendenti
che concordano entro **2,2 ms** · p95 **190-195** · p99 **200-232**. ⛔ **Il tetto è 50 ms: si sfora
di quasi tre volte.** Coi due pezzi ciechi dichiarati: **160-193 ms sullo schermo di un utente, più
la rete.** ⚠ E sul prodotto di un'ora prima — senza la cura di O1 in `src/figlio.c` — erano
**151,17 ms** (n = 573).

⭐ **E la scomposizione dice che NESSUN TRATTO DOMINA** — la tesi 1 del mandato è **refutata**:

| tratto | ms | | tratto | ms |
|---|---|---|---|---|
| **5** cattura → primo byte *(codifica compresa)* | **30,4** | | **4** la scena disegna → cattura | **16,2** |
| **3** la scena riceve → disegna | **26,6** | | **1a** evento → il prodotto lo vede | **13,1** |
| **2** byte usciti → la scena riceve | **26,0** | | **8** la decodifica **vera** | **0,75** |
| **9** richiamo → 1° `drawImage` *(l'ATTESA)* | **25,6** | | **10** 1° → 2° `drawImage` *(il disegno VERO)* | **0,08** |

⇒ I **sei** tratti maggiori valgono fra **13,1 e 30,4 ms** e fanno il **99 %**: curarne uno solo
toglie al massimo il **22 %** del ritardo, e il tetto resterebbe sforato di due volte e mezzo.
⚠ La codifica sta **dentro** il tratto 5 e vale **5,3 su 30,4**; la **decodifica** vale **0,75 ms**:
«il collo di bottiglia è la codifica» resta falsa, e adesso con un numero sotto.
⭐ **E la scomposizione è ripetibile quanto il totale**: nessun tratto si sposta di più di **1,6 ms**
fra i due giri.

⭐⭐ **E i tratti che il metro della fase 3 NON attraversava** (1a + 1b + 2 + 3) valgono **65,8 ms**,
cioè **il 47 %**: ⛔ *il numero della fase 3 non vedeva quasi metà del ritardo che l'utente sente.*

> ##### ⛔⛔ E IL DIFETTO PIÙ GRAVE NON È UN TRATTO: È UNA CODA CHE CRESCE
> `[M]` il server consegna **39,6** fotogrammi/s, la pagina ne dipinge **34,7**, e ⛔ **nessuno
> butta l'avanzo** (`scartati_ordine` 0 · `trattenuti` 0 · `corti` 0). ⇒ Il ritardo cresce di
> **+108 ms al secondo**: 31,6 ms dopo 1 s → **4 650 ms dopo 43 s**. **Dopo un minuto l'utente
> comanda un desktop che ha visto sei secondi fa, e tutti i contatori sono verdi.**
> ⭐ **Curato** in `src/pagina.html` (ancora `F4-CODA-DEL-DECODIFICATORE`): si salta **il disegno**,
> non la decodifica — nessun buco, nessuna chiave. `[M]` dopo: pendenza **−2 ms/s**, ritardo **1,3
> ms** dopo 41 s.

> ##### ⛔ E LA TESI 2 — *«il ritmo è quanto ci consegna Mutter»* — **REFUTATA in questo regime**
> `[M]` quattro conti nella stessa finestra di 30 s: la scena disegna **59,99/s**, Mutter ce ne
> consegna **30,84** (il 51 %), il server ne spedisce **30,54**, la pagina ne dipinge **30,6** —
> ⭐ e le **attese a vuoto sono 0,00/s**: ogni volta che abbiamo chiesto un fotogramma ce n'era già
> uno pronto. ⇒ **Non stiamo aspettando Mutter: il limite è nel nostro ciclo.**
> ⚠ `[?]` I 10,8/s che l'utente ha misurato dal suo video sono su un desktop **vero**, cioè in
> regime di scarsità: le due misure rispondono a due domande diverse.

> ##### ⛔⛔ E LA TESI 3 (tastiera contro mouse) NON È CHIUSA — ⭐ e a dirlo è **la scomposizione**
> `[M]` ultimo giro: **35 sonde chiuse su 296**, mediana **151,7 ms** contro i **141,6** del mouse
> nello stesso giro. ⚠ Verosimile: *«la tastiera è 10 ms più lenta»*. ⛔ **È falso**, e la prova è
> che la sua scomposizione **non è fisica**: `2 byte usciti → la scena riceve` = **−562,8 ms**,
> negativo. ⇒ L'accoppiamento prende il fotogramma sbagliato, e **il totale da solo non lo direbbe
> mai**: è il **guasto n. 12 della certificazione di A10** visto dal vivo.
> ⇒ ⛔ **Il numero non è stato pubblicato.** Serve un eco della tastiera che non si sovrascriva
> (lavoro mio su `04-b30-scena.c`).

⭐ **Quel che invece è `[M]` e regge: il cammino della tastiera arriva al compositore** — `Escape`
mandato dal canale del prodotto **chiude la Panoramica di GNOME**, quattro volte su quattro,
verificato nei pixel; e la scena riceve **744** eventi di tastiera in un giro.

⭐⭐ **E Q6 — il controllo del ramo d'ANDATA, che alla fase 3 non poteva esistere — PASSA sul ferro**:
iniettando 30 ms il totale sale di **30,84** e il surplus compare **tutto nel tratto 2** (+33,49) e
**in nessun altro**. ⇒ Metà dell'anello che non aveva nessuna taratura adesso ce l'ha.
⛔ Q5 (ramo di ritorno) resta rosso **per 0,2 ms**: il surplus sta nel tratto giusto (+24,70 contro
N = 25) ma il totale sale di 20,78. ⚠ **La tolleranza non è stata allargata.**

**⛔ E i tre difetti che tenevano `n = 0` erano tutti del banco o del contorno, nessuno del canale:**

| | |
|---|---|
| ⛔⛔ **la Panoramica di GNOME** | una sessione headless appena nata si apre in Panoramica: la scena «a schermo intero» era **una miniatura a 0,79** e la Panoramica teneva il fuoco. ⇒ `eventi_puntatore = 0` (diagnosi suggerita: «`libei` non consegna») **e** 0 marche lette su 966 (diagnosi suggerita: «l'eco non si legge»). ⭐ **A trovarlo è stato guardare l'immagine**, non leggere un numero |
| ⛔ **`04-b30-scena.c`: `oy` sommato due volte** | le celle della **seconda** marca finivano fuori dalla loro zona di quiete, sullo sfondo del desktop. Sulla marca 1 (`oy = 0`) non si vedeva. ⭐ E la certificazione era verde 53 su 53: **i sedici guasti si innestano nel verbale, e nessuno dipinge un pixel** |
| ⛔ **il controllo di precondizione di A10, falso ROSSO** | cercava i ganci in `figlio.c`; stanno in `webtransport.c` (il canale è del **padre**). ⚠ Stamattina lo stesso controllo aveva dato un falso **verde**: adesso guarda tutt'e due i lati del confine |

---

#### ⭐ A5 — la tastiera: **26 prove, 0 rosse** `[M]` 14 agosto 2026

Identiche in locale e nel contenitore (`xkbcommon` 1.7.0 su tutt'e due). Si ricontrolla con
`bash banchi/04-b25-lancia.sh` — ⭐ **senza sessione, senza `libei` e senza nessuna porta**.

| | |
|---|---|
| ⭐ **il metro è la lettera che ESCE** | non il codice che parte: il banco simula il compositore su una `xkb_state` costruita da sé e **legge il carattere** |
| ⭐ **e ha un controllo negativo** | tasto 26 **senza** Maiusc ⇒ `è`, non `é`. Senza di lui, un simulatore compiacente avrebbe dato verde anche a chi dimentica i modificatori |
| **le tre prove che `PIANO.md` nomina** | `é` su `it` ⇒ `42+26`, esce `é` · `é` su `us` ⇒ ⛔ **niente**, e la riga nel registro · `@` per due strade: `100(AltGr)+16` su `it`, `42(Maiusc)+3` su `us` · emoji e `中` non producibili ovunque |
| ⭐ **il banco è CERTIFICATO** | tre implementazioni sbagliate apposta, e il lanciatore pretende **ROSSO sulla prova giusta**: quella che manda `e` al posto di `é` è rossa |
| **il ripiego non è silenzioso** | `[M]` `xkbcommon` 1.7.0 **non ripiega da sé** (ritorna NULL), e `tastiera_disposizione()` dice `it [Italian]` ⇒ un ripiego entrato da altrove si leggerebbe nel registro come `it [English (US)]` |

⛔ **E tre misure hanno cambiato il codice** — cioè il banco ha lavorato:

| | |
|---|---|
| ⛔ **evdev 84 non esiste** | la prima stesura sceglieva per l'AltGr italiano un codice che **non è in `linux/input-event-codes.h`** (c'è un buco fra 83 e 85). ⚠ **Il banco era VERDE**: dal lato che riceve quel codice funziona. Trovato **guardando il numero**, non dal banco. Ora esce `100` |
| **`de(neo)`** | `√` vuole `100+43+17`, e il terzo livello lì è il tasto **43**, non il `100` che v1 aveva scritto a mano. ⭐ E la stessa misura risponde alla domanda implicita del contratto: **quattro posizioni bastano**, il caso peggiore ne usa tre |
| il Maiusc | usciva **destro**; ora sinistro |

#### ⛔⛔ E il contratto della tastiera era SBAGLIATO — il rifiuto è stato accolto

*`src/tastiera.h` diceva: «la disposizione è la stringa negoziata all'attacco». L'anello l'ha
attuata, ha visto che funzionava, **e l'ha rifiutata lo stesso** — con la ragione giusta.*

⛔ **Non scegliamo noi la disposizione della sessione: la sceglie GNOME, e `libei` ce la CONSEGNA**
col dispositivo tastiera. Il danno, in concreto — sessione `it`, client che ha negoziato `us`,
l'utente scrive `[`:

| | |
|---|---|
| su `us` | `[` sta sul tasto **26**, da solo |
| su `it` | sul tasto **26** c'è la **`è`**, e `[` vuole l'AltGr |

⇒ Mandiamo `26` e sullo schermo compare **`è`**: ⛔ non un carattere *mancante* — **un carattere
DIVERSO**, che `RCP.md` §7.3 vieta. E nessuno collegherebbe il sintomo alla disposizione.
⚠ **E rende falsa una riga che credevamo vera**: `DECISIONI.md` §5-bis.7 dice che la degradazione è
morbida — *«mai caratteri sbagliati, al massimo un paio di accenti irraggiungibili»*. È vero **solo**
usando la keymap della sessione.
⭐ **E v1 lo faceva già così** (`fondamenta/remotix-c/src/tastiera.c:69`): è l'unico pezzo di v1 che il primo
contratto di V2 non aveva ripreso.

⇒ ✅ **Accolto il 14 agosto 2026**: `tastiera_apri_da_keymap()` è in `src/tastiera.h`, e
`input_apri()` **non** prende la disposizione — la keymap arriva da `libei` dentro `input.c`, a ogni
`DEVICE_ADDED`.

---

### ⛔ Che cosa NON ha funzionato

⏳ *si riempie anche quando fa una brutta figura.*

---

### Le decisioni prodotte

⏳ *le decisioni stanno in `DECISIONI.md` una sola volta: qui si **rimanda**.*

---

### Che cosa resta [?]

Aperte all'apertura della fase, e vanno **misurate prima di essere credute**:

1. ~~chi decide la misura del monitor ora che non la dà più la sessione~~ ⇒ ✅ **CHIUSA il
   14 agosto 2026, e la risposta era un'altra da quella che la domanda supponeva**: ⛔ **non la
   decide `RecordVirtual` — la decide il NOSTRO formato PipeWire** `[R]`. E la promessa della tela
   concessa **oggi nessuno la mantiene**: `[M]` client a 1280×720 ⇒ il server la concede, il palco
   cattura a 1920×1080 (costante di compilazione), `rcp` rifiuta ogni fotogramma — **145 prodotti,
   0 spediti, client nero senza errori**. ⏳ La cura è lavoro della fase 6 (`RCP.md` §4.5);
2. ⚠ `PIANO.md` **399, 402-404, 591-593** e `STUDI.md` §gnome **108-109, 111-112, 551** dicono che
   `--virtual-monitor` **non è opzionale**: ⛔ sono vere solo per una sessione che deve vivere
   **senza nessuno che la catturi**, e vanno riscritte. *(Righe individuate da A1, non toccate da
   lui: si riscrivono a codice fermo.)*
3. `[?]` la Keyboard Lock su **DeX**, e la PWA su **Chrome per Android** (`SPECIFICHE.md` §7.3-bis);
4. `[?]` il segno della rotella sugli **altri quattro** compositori (`RCP.md` §7.3);
5. ⭐ **CHIUSA il 14 agosto 2026 — la persistenza al distacco REGGE**, e la tesi del difetto è
   **falsa**: il monitor non sparisce (sempre 1, anche senza nessuno), l'applicazione lavora
   (1 160 righe in 240 s senza un buco), `libmutter` non scrive asserzioni nuove, e al riattacco
   si ritrova **la stessa finestra** (pid invariato), due volte di fila. ⚠ **Ma il palco muore col
   FIGLIO, non con la sessione**: chi congederà un figlio che gira a vuoto toglierebbe il monitor a
   una sessione viva — ⏳ **fase 5**;
6. ⛔ **aperta il 14 agosto, e nessuno l'aveva posta**: se la sessione ha `us` e il client ha
   negoziato `it`, **chi cambia la disposizione della sessione?** `DECISIONI.md` §5-bis.7 dice che
   si rinegozia all'attacco — ⚠ ma un client `libei` **non può imporre una keymap all'EIS: la
   riceve**. ⇒ O la si cambia dalla sessione (`org.gnome.desktop.input-sources`, prima di
   attaccare), oppure §5-bis.7 va riscritta come *«il client **dichiara**, il server **si adegua a
   quel che trova**, e lo dice»*. `[?]` — nessuno l'ha misurato.

---

### Il giudizio dell'utente — ⭐ DATO il 14 agosto 2026

> ### *«Mi sembra ok.»*
> — l'utente, 14 agosto 2026, dopo aver usato il desktop di `prova` dentro una scheda di Chrome
>
> e, poco prima, sulle due cose che aveva chiesto di ottimizzare:
> > *«La situazione mi sembra migliorata. La comparsa del desktop è più immediata.»*

⭐⭐ **E la fase si chiude qui**, come `PIANO.md` §0.2 impone: *«su una misura giudicata dall'utente,
non su un documento completo»*.

#### ⭐ Che cosa il giudizio ha confermato, e con quale numero accanto

| la sua frase | il numero che le corrisponde |
|---|---|
| *«la comparsa del desktop è più immediata»* | `[M]` **5,11 s → 1,04-1,13 s** (7 giri) — e di quel secondo, **1,00 s è il secondo fisso di §4.4-bis**: ⭐ quel che è nostro sono **34-124 ms** |
| *«mi sembra ok»* (dopo qualche minuto d'uso) | `[M]` il ritardo **non cresce più**: pendenza da **+108 ms/s a −2 ms/s**, e **1,3 ms** dopo 41 s |

#### ⛔ E i limiti del giudizio, scritti PRIMA che lo desse e non dopo

*Gli sono stati messi davanti in tavola prima della prova — «un giudizio dato senza sapere che cosa
manca è un'approvazione al buio», la stessa regola con cui ha chiuso la fase 2.*

| | |
|---|---|
| ⛔ **il ritardo SFORA** | `[M]` **139,40 ms** (n=326) contro un tetto di **50**. ⚠ Ha giudicato **con gli occhi**, non su quel numero — e i due non si sostituiscono |
| ⛔ **nessun tratto domina** | sei tratti da ~25 ms: **nessuna cura singola** porta 140 a 50. È lavoro della **fase 8**, e va detto perché il giudizio non venga letto come «il ritardo è a posto» |
| ⛔ **la tela non è la sua** | il suo schermo è **21:9**, il desktop remoto **16:9** ⇒ `[M]` dal suo video, **il 36 % dei pixel è banda nera**. Ha giudicato una finestra, non uno schermo pieno |
| ⚠ **un browser solo** | **Chrome 151**. Safari, iPhone e DeX restano `[?]` **dichiarate, non dedotte** |
| ⚠ **qualche minuto, non qualche ora** | i tre orologi della sessione sono della **fase 5**: l'abbandono lungo non è stato giudicato |

#### ⭐⭐ E il giudizio dell'utente ha trovato SETTE difetti che nessuno dei dieci banchi vedeva

*Non è un aneddoto: è il conto della giornata, ed è la ragione per cui il piano fa chiudere le fasi
così.*

| che cosa ha detto | che cosa c'era sotto |
|---|---|
| *«se il server non mostra il desktop, a che serve REMOTIX?»* | il monitor aggiunto e vuoto — **due fasi** l'avevano preso per uno sfondo |
| *«non si vede nessun desktop»* | **due server nostri** che montavano un monitor a testa sulla stessa sessione |
| *«lo schermo appare strano»* | la dichiarazione delle scorciatoie che copriva il **38 %** della finestra |
| *«non vedo il drawer di gnome»* | la barra piazzata **esattamente dove GNOME tiene il dock** |
| *«il puntatore sembra catturato… studia XPRA»* | ⭐ `SPECIFICHE.md` §7.1 che contraddiceva §7.5: la cattura **non comprava niente** |
| *«niente desktop»*, due volte | il figlio che tiene per sempre **un palco fallito** |
| *«il tempo fra login e desktop è troppo lungo»* | ⛔ **una riga del coordinatore**: `poll()` su due descrittori e `pf.revents` mai guardato |

⛔ **Sette su sette stavano FRA i pezzi, nessuno dentro uno** — ed è la lezione di
`fasi/rapporti/F5-desktop-vero.md` verificata sette volte in una giornata sola.

---

### ⭐⭐ Il numero della fase — `[M]` 14 agosto 2026

*L'anello **input → vetro**, che alla fase 3 non era misurabile: il campo `input` valeva 0 in 953
fotogrammi su 953, perché il canale non esisteva.*

| | |
|---|---|
| ⭐ **il numero** | **139,40 ms** (n = 326 su 326) e **141,60 ms** (n = 322 su 322), ⭐ **due giri indipendenti che concordano entro 2,2 ms** |
| ⚠ **coi pezzi ciechi** | **160-193 ms** sullo schermo dell'utente, **più la rete** |
| ⛔ **contro il tetto** | **50 ms**. Si sfora di quasi **tre volte**, e si scrive com'è |

#### ⭐ La scomposizione, e la risposta a «che cosa ottimizzo?»

| tratto | mediana |
|---|---|
| cattura → primo byte | **30,4 ms** |
| la scena riceve → disegna *(è il desktop remoto, non noi)* | 26,6 |
| byte → scena | 26,0 |
| richiamo → primo `drawImage` | 25,6 |
| disegno → cattura | 16,2 |
| decodifica | 0,75 |
| ⭐ **il `drawImage` vero** | **0,08** |

⇒ ⛔ **Nessun tratto domina**: sono sei tratti da ~25 ms. **Nessuna cura singola porta 140 a 50.**
⭐ La somma dei tratti fa **139,08** contro un totale di **139,40** — scarto **0,32 ms**: la
scomposizione è completa, non ha buchi.
⭐⭐ **E i tratti che il metro della fase 3 NON attraversava valgono 65,8 ms, il 47 %**: metà del
ritardo vero stava fuori dal vecchio metro.

> #### ⭐⭐ E la prova sul ferro che l'etichetta corretta stamattina era giusta
> Il **primo** `drawImage` costa **25,6-27,1 ms**, il **secondo 0,080** ⇒ **320-339 volte**.
> ⛔ *Il disegno non è mai stato caro: era l'attesa del fotogramma dalla GPU.*

---

### ⭐⭐ Le due ottimizzazioni chieste dall'utente — e tutt'e due erano NOSTRE

#### 1. Il login → desktop: **5,11 s → 1,04-1,13 s**

⛔⛔ **E la causa era una riga del coordinatore, scritta la mattina stessa.** Per far arrivare
l'input più in fretta era stato messo il descrittore di `libei` nello stesso `poll()` del figlio —
⛔ ma il codice dopo **non guardava `pf.revents`**: svegliandosi per `libei`, il figlio andava lo
stesso a leggere il socket del padre, **bloccante**.
⇒ *Una modifica fatta per risparmiare millisecondi sull'input costava **quattro secondi** al login.*
⭐ **La cura è una riga**: `if (!pf.revents) break;`

⚠ **E il registro lo diceva già**: *«0 fotogrammi consegnati, **0 attese a vuoto**»* — zero attese a
vuoto vuol dire che il ciclo **non aveva nemmeno provato** a catturare. ⛔ Era scritto, ed è stato
letto due volte come «la scena è ferma». *Il difetto ha resistito a due sonde leggere che davano
risposte opposte: l'ha chiuso solo un debugger attaccato al processo.*

#### 2. ⭐⭐ E il ritardo CRESCEVA senza limite, con tutti i contatori verdi

`[M]` il server consegnava **39,6 fotogrammi/s**, la pagina ne dipingeva **34,7**, e **nessuno
buttava l'avanzo**: `scartati_ordine 0 · trattenuti 0 · corti 0`.

| | |
|---|---|
| la crescita | ⛔ **+108 ms al secondo** |
| dopo 43 s | ⛔ **4 650 ms** — si comandava un desktop visto **sei secondi prima** |
| ⭐ curato | pendenza **−2 ms/s**, ritardo **1,3 ms** dopo 41 s |

⇒ ⛔ **È il difetto che l'utente sentiva e che nessun contatore contava**: tutti verdi, e la coda del
decodificatore che si allungava e basta.

#### ⭐ E i due difetti che potevano rovinare una macchina vera

| | prima | dopo |
|---|---|---|
| il registro a raffica | **151,9 MB/s** (⛔ `[M]` **30,8 GB** scritti in una mattina) | **284 B/s** |
| un nucleo bruciato a vuoto | **1,00** | **0,00** |
| il desktop dopo che la sessione grafica torna | ⛔ **non tornava mai** | ⭐ **1,11 s, stesso figlio** |

⚠ ⭐ **E il ciclo a vuoto ha DUE facce, e una è MUTA**: per questo il banco misura il registro **e**
la CPU. E con un client muto **un difetto ne nasconde un altro** — serve un client che *chieda le
chiavi*, come fa un client vero che non vede niente.


---
---

## ⭐⭐ LA CODA DELLA FASE 4 — 15 agosto 2026, la notte in cui la tela è diventata la finestra

*Questa fase è stata giudicata «mi sembra ok» il 14 agosto sera, ⛔ ma il suo mandato
(`fasi/rapporti/F4-IN-12-mandato-prossima-sessione.md`) diceva **«a lavoro riuscito ma non
finito»**: mancava un pezzo solo, `figli_ritela()` → `cattura_ridimensiona()`, e da lì dipendevano
quattro sintomi che l'utente vedeva sull'input e sul video.*

⛔ **E questa coda NON è la fase 6**, anche se ne tocca il contenuto: il numero della fase lo dà il
**perché si è fatto il lavoro**, non l'elenco delle cose prodotte. Qui si è fatto per **curare il
mouse e il ritardo dei clic**, cioè per finire la fase 4 — e infatti tutti i rapporti della notte si
chiamano `F4-IN-*`. ⚠ La fase 6 resta **aperta**: `PIANO.md` dice quali sue parti si trovano già
fatte e quali no.

⚠ **E vale la riserva di forma di questo documento**: queste righe sono scritte **alla chiusura**.
⭐ Le misure però non sono ricordate: ognuna viene da un registro del server o da un giro di banco,
con l'ora accanto.

### Che cosa doveva produrre questa coda

Il mandato di `F4-IN-12` §1, in una riga: **scrivere la catena `figli_ritela()` →
`cattura_ridimensiona()`**, quella che porta la misura chiesta dal client dal filo fino al
compositore.

⭐ **E vale più di quanto sembri perché chiude QUATTRO sintomi, non uno** — tutti e quattro nascono
dalla stessa cosa, *la misura della tela non la chiede nessuno*:

| sintomo | perché sparisce |
|---|---|
| le bande nere laterali | le due tele combaciano ⇒ niente da impaginare |
| il testo interpolato | scala **1** ⇒ nessuno ricampiona l'immagine |
| il ri-attacco a misura diversa | la tela si cambia a caldo |
| ⭐⭐ i 4 secondi fra login e desktop | riavviare il flusso **consegna un buffer** |

**Che cosa l'utente vede e giudica**: il desktop remoto riempie la finestra del browser, **senza
bande nere e senza testo sfocato**, ritrova la sua misura quando si riattacca, e **risponde al
clic** invece di farsi aspettare.

---

### Il banco

⛔ **Scritto DOPO la prima stesura del codice, non prima** — e va detto: la regola di §0.2 vuole il
banco per primo. Quel che ha retto al posto suo è stato il mandato **avversariale** a quattro agenti
(§«che cosa non ha funzionato»), che ha trovato dieci difetti prima che il banco esistesse.

| | |
|---|---|
| `banchi/04-b31-tela.c` | monta `rcp.c` **nudo**, con un palco finto che si può far rispondere in ritardo, concedere un'altra misura, o non rispondere affatto. **19 casi**, ciascuno con l'atteso dichiarato prima (⭐ il 19° aggiunto il 16 agosto 2026, vedi §05-la-sessione §6-ter) |
| `banchi/04-b31-certifica.sh` | ⭐ **il controllo positivo**: innesta **12 guasti** in una copia di `rcp.c` e pretende che diventino rossi **i casi attesi** — non «che diventi rosso qualcosa» |

⛔ **E il banco è stato corretto due volte dalla misura, non il contrario**: l'atteso di G1 diceva
dieci casi e ne ha accesi sei; G9 restava verde perché un **secondo** controllo mascherava il guasto
innestato nel primo. Tutt'e due scritti accanto al guasto, con la ragione.

⚠ **Quel che questo banco NON prova, dichiarato**: non prova che il compositore ridimensioni
(quello è `[M]` di `banchi/04-in8-misura.c`), non prova che i pixel siano giusti (qui non c'è un
pixel), non prova la pagina. Prova la sola cosa che sta in mezzo, e che nessun banco guardava: **che
a ogni `ADATTA_TELA` risponda esattamente un `TELA`, e che la tela in vigore non prenda mai un
valore che nessuno ha concesso.**

---

### Che cosa è stato sviluppato

| file | che cosa |
|---|---|
| `src/cattura.c` · `.h` | `cattura_ridimensiona()` (l'esito è la RICHIESTA, non il cambio), `cattura_risveglia()`, `cattura_misura_negoziata()`, i quattro parametri di consumo in un posto solo, la guardia sulla geometria incoerente |
| `src/figlio.c` · `.h` | `figli_ritela()`, il ramo `RITELA`, **la riconciliazione sul fotogramma** (codificatore riaperto, puntatore rimappato, chiavi tenute buttate), `MSG_TELA` — la risposta al padre —, la tela *voluta* per il rimontaggio, l'attesa che cresce sul codificatore |
| `src/rcp.c` · `.h` | i ganci `ritela` e `tela_del_palco`, `rcp_tela_dal_palco()` (tre casi), `tela_richiama_il_palco()`, il fondo di §7.1, i limiti di §4.5 per lato, il tetto `video.misura_massima` anche su `ADATTA_TELA` |
| `src/webtransport.c` · `.h` | il ponte dei due ganci, la tabella delle tele dei palchi per utente |
| `src/main.c` | le due cuciture, e `wt_palco_dimentica()` alla morte del figlio |
| `src/mutter.c` · `.h` | `mutter_scala_nostra()` — la scala del **nostro** monitor logico |
| `src/pagina.html` | `chiedi_tela()`, `tela_da_chiedere()`, l'interruttore `?adatta=`, il bersaglio, i limiti per lato, e tre correzioni al lettore dei fotogrammi |
| ⭐ `src/Contenitore` · `src/costruisci-in-contenitore.sh` | **come si costruisce**, che era il blocco dichiarato di `F4-IN-12` §3 |

---

### Le misure

Tutte sulla macchina di prova (`192.168.0.2`, NIC-OS, GNOME headless), utente `prova`, client
Chrome. ⚠ L'orologio di quella macchina è **indietro di due ore** rispetto a quello del portatile:
le ore qui sono le sue.

| che cosa | scena | atteso | misurato | data |
|---|---|---|---|---|
| tela concordata all'attacco | finestra 1265×800 | la misura della finestra | **1264×800** (pari, troncata in giù) | 15 ago |
| ⭐ dal canale video al primo fotogramma | login, desktop fermo | «meno dei 4,4 s del 14 ago» | **311 ms** | 15 ago |
| scala di disegno del client | idem | 1,000 | **1,000**, `imageRendering: pixelated` | 15 ago |
| ridimensionamento a caldo | 1264×800 → 1000×640 | ~41 ms (`[M]` F4-IN-8) | **6 ms** dalla risposta del palco alla chiave spedita | 15 ago |
| ri-attacco a misura diversa | palco a 1264×800, pagina che chiede 1920×1080 | i pixel arrivano subito | `SESSIONE` concede **1264×800** (§4.5), **0 fotogrammi scartati** | 15 ago |
| fotogrammi scartati per misura · trattenuti · errori | sessione intera | 0 · 0 · 0 | **0 · 0 · 0** | 15 ago |
| guardia 2 (la scala del monitor) | montaggio del palco | 1,000 | **1,000** su «Meta-0», e la riga si scrive **anche quando è buona** | 15 ago |
| ⭐⭐ clic → primo fotogramma spedito | 25 clic veri dell'utente, desktop fermo | ≤ 50 ms (`CODER.md` §1-bis) | ⛔ **136 ms** (peggiore 502) → dopo la cura **41 ms** (peggiore 47) | 15 ago |
| il giro completo, misurato dalla pagina (`GIRO`) | 10 clic, portatile su rete locale | — | **55 ms**, peggiore 71 (era 135 dal DeX il 14 ago) | 15 ago |
| il banco | `04-b31` | 18 verdi | **18 verdi**, e **11 guasti su 11** visti | 15 ago |
| ⛔ **e il 16 agosto era 11/18** | `04-b31` | — | l'atteso di sette casi non contava la richiesta della nascita di `477d708`. ✅ **19/19 e 12 guasti su 12**, col caso 19 a guardia della cura | 16 ago |

⭐ **E la misura che non viene da noi**: GNOME *Impostazioni → Displays*, **dentro** la sessione
remota, dichiara **«Resolution 1264 × 800 (3:2)»** e **«Scale 100%»**. È il compositore che dice la
misura che gli abbiamo chiesto.

---

### ⛔ Che cosa NON ha funzionato

#### I dieci difetti trovati refutando la cura appena scritta

Quattro agenti, mandato **avversariale** («parti dall'ipotesi che sia falsa»). ⭐ Tre affermazioni su
quattro sono state smentite, e **otto dei dieci difetti erano nati quella notte insieme alla cura**.
L'elenco per intero è in `fasi/rapporti/F4-IN-13-la-tela-che-cambia.md` §3. I quattro che avrebbero
fatto danno:

1. una **lettura oltre la memoria copiata** quando la tela si allarga (la guardia copriva un verso
   solo dei due);
2. il **`TELA` non richiesto**, che per §6.2 fa **chiudere una sessione sana**;
3. **due `ADATTA_TELA` incatenate**: il fotogramma della prima preso per la risposta della seconda,
   e il desktop assestato sulla misura sbagliata **con i conti dei messaggi in ordine**;
4. il ritorno a una misura **già stata in vigore**, che chiudeva la sessione di chi trascina un
   bordo e lo rimette dov'era.

#### ⛔⛔ E il difetto che ha trovato l'UTENTE, non il banco

*15 agosto, mattina, con queste parole: «su Android il mouse dà problemi: non prende più i click».*

Erano **due sue sessioni che si contendevano il palco**: il portatile staccato per silenzio aveva
perso il posto **ma continuava a pretendere la sua misura**, il telefono pretendeva la propria, e il
palco rimbalzava fra 2544×926 e 2560×926 **diciassette volte al secondo**. Ogni giro riavviava il
flusso, e Mutter ricreava i dispositivi di `libei`: `[M]` **640 «ricambi»** del puntatore, e la
regione dell'input mai d'accordo con la tela. ⇒ I clic partivano, arrivavano, venivano iniettati — e
finivano altrove.

⭐ La cura è l'invariante che c'era già: **I2 — chi non ha il posto guarda, non comanda**. Una riga.
⛔ E la mia difesa dell'attesa che cresce **non bastava**, per una ragione che vale più della cura:
si azzerava ogni volta che il palco arrivava dove *quella* sessione lo voleva, cioè a ogni giro del
ping-pong. **Un fondo temporale cura un padrone insistente, non due padroni.**

#### ⛔ Il quarto di secondo su ogni clic, e il numero che stava nel registro da un giorno

Il ciclo del figlio aspettava un fotogramma fino a **250 ms**, e in quell'attesa non leggeva il
socket del padre. `[M]` 136 ms di mediana sui clic veri. ⭐ E la causa era stampata **una volta al
secondo** in una riga scritta per un'altra domanda: *«3 attese a vuoto»* = quattro giri al secondo =
250 ms per giro. È la seconda volta in due giorni che il registro aveva già il fatto
(`LEZIONI.md` §6.2-ter).

#### Le tre cose che ho sbagliato di metodo, e che il banco ha corretto

- l'**atteso di G1** dichiarava dieci casi rossi e ne ha accesi sei;
- **G9 restava verde** perché un secondo controllo mascherava il guasto innestato nel primo;
- il **caso 18** non riproduceva la scena vera finché non ha avuto **due** sessioni: con una sola, il
  posto se lo riprendeva da sé e il difetto non compariva.

---

### Le decisioni prodotte

- `DECISIONI.md` **§5.0-sexies** — attuata per intero, con le misure della notte, le tre guardie
  chiuse e i quattro tempi (`RCP_TELA_ATTESA_MS`, `RCP_TELA_RICHIAMO_MS`, `TELA_FONDO_MS`,
  `RISVEGLIO_MS`);
- `DECISIONI.md` **§5.1** — vale **durante** la sessione, non all'attacco: l'inseguimento della
  finestra sta dietro `?adatta=segui`, spento di suo (I6). ⛔ **E il 17 agosto 2026 è uscito del
  tutto** — `DECISIONI.md` **§5.1-bis**, decisione dell'utente: *«non voglio mettere delle
  eccezioni nel progetto»*. Durante la sessione la tela non si tocca, e non c'è più interruttore;
- `SPECIFICHE.md` **§6.4** e `RCP.md` **§7.1** — corrette: *«mai come automatismo»* non è più vero
  all'attacco, e il perché è scritto con la data;
- `LEZIONI.md` **§7.5** (una deduzione al posto di un messaggio), **§6.2-bis** (un'attesa che
  protegge un anello è un ritardo per gli altri), **§6.2-ter** (il numero è già nel registro).

---

### Che cosa resta `[?]`

| | |
|---|---|
| ⏳ **la riga che manca a `RCP.md` §7.1** | che cosa fa il server quando il palco cambia misura **da sé**. Oggi lo richiama e non manda nessun `TELA` — funziona, ma è una regola del prodotto che l'arbitro non nomina |
| ⛔ **il banco del riattacco che BATTE UN TASTO dopo** | `PIANO.md` lo chiede per questa fase. `[M]` si è visto nel registro che `libei` ricrea i dispositivi al cambio di geometria e che `input.c` li riaggancia, ⛔ **e l'utente ha scritto in un terminale dopo un riattacco** — ma un banco che lo provi non c'è |
| ⛔ **il ripiego su KWin dichiarato nel registro** | `PIANO.md` lo chiede per questa fase e **non è verificabile**: KDE è la fase 11, e su questa macchina non c'è. Il percorso di codice esiste (`COMPOSITORE_INCAPACE`) ed è provato dal caso 11 del banco, **su un ospite finto** |
| `[?]` **il mezzo pixel del `margin: 0 auto`** | quando `clientWidth × devicePixelRatio` è dispari. ⭐ Giudizio dell'utente sul DeX: *«tutto perfetto»* ⇒ **non si presenta**, ma nessuno l'ha misurato |
| ⚠ **i 4 ms di ritardo medio aggiunto** | l'attesa di 8 ms è un **ripiego dichiarato**: la cura vera è un descrittore che la cattura scrive quando il fotogramma è pronto, nello stesso `poll()` del padre e di `libei` |
| ⚠ **il multi-monitor** | `SPECIFICHE.md` §6.5, fuori scopo come funzione |
| ⚠ **i banchi RCP/1 non esercitano la strada nuova** | `01-b3-cliente.py` e `01-b4-validatore.py` restano verdi perché il filo non è cambiato, ⛔ ma nessuno dei due manda un `ADATTA_TELA` |

---

### Il giudizio dell'utente

> **«Funziona. Niente barre nere, il desktop riempie perfettamente la finestra del browser e mouse e
> tastiera funzionano.»** — 15 agosto 2026, dal portatile Linux
>
> **«Sia su Linux sia su Android (DeX) è tutto perfetto. Ci sono i presupposti per chiudere la
> fase.»** — 15 agosto 2026, dopo la cura del ritardo

⭐ E prima, con l'immagine del desktop remoto a schermo intero: **«Questo è linux!»**


---

<a id="05-la-sessione"></a>

## Fase 5 — La sessione

⭐ **Aperta il 15 agosto 2026**, col suo documento e prima di una riga di codice (questo documento).
Il mandato di partenza è `rapporti/F5-IN-0-mandato.md`; il piano è
`PIANO.md` §«Fase 5 — La sessione».

> **La scena che l'utente giudicherà**: *«chiude il client, va a pranzo, riapre — e ritrova tutto
> com'era»*.

⛔ **E il 15 agosto l'utente ha aggiunto quattro punti** che il piano non conteneva, o conteneva
sparsi. Sono il §1 di questo documento, prima del resto, perché due di essi **cambiano l'ordine del
lavoro**: il primo tocca la configurazione del desktop, il secondo apre una decisione di protocollo.

---

### 1 · ⭐ I QUATTRO PUNTI AGGIUNTI DALL'UTENTE

#### 1.1 ⛔ Togliere «Spegni, Riavvia, Sospendi, Iberna» dal menu di sistema del desktop

*Motivo dichiarato dall'utente: un utente collegato da remoto non deve poter «sfilare da sotto il
naso» la macchina agli altri, in remoto o in locale.*

`SPECIFICHE.md` §11.3 lo prometteva già in una riga — *«spegnimento, riavvio, sospensione: **tolti**
alla sessione remota»* — e **nessuna riga di codice la mantiene**.

⭐ **La leva ovvia è quella sbagliata, ed è misurabile nelle fonti che abbiamo in casa:**

| strada | che cosa fa davvero |
|---|---|
| ❌ `org.gnome.desktop.lockdown disable-log-out` | fa sparire Spegni **e** Riavvia — ⛔ **ma fa sparire anche «Esci…»**, e fa rifiutare `org.gnome.SessionManager.Logout` con `GSM_MANAGER_ERROR_LOCKED_DOWN`. Cioè ci porta via **il punto 1.2 dell'utente** *e* il congedo che `sessione.c` · `scrivi_dropin()` usa oggi per fermare la sessione |
| ✅ **regola polkit `no`** su `org.freedesktop.login1.power-off`, `reboot`, `suspend`, `hibernate` (e le varianti `*-multiple-sessions`, `*-ignore-inhibit`) | `[R]` `gsm-manager.c`: `CanShutdown = !lockdown && (can_stop ‖ can_restart ‖ can_suspend ‖ can_hibernate)`, e ciascuno dei quattro è vero solo se logind risponde `yes` o `challenge` (`gsm-systemd.c:698-803`). Con tutt'e quattro a `no` ⇒ `CanShutdown` falso ⇒ gnome-shell nasconde **Spegni** e **Riavvia** (`systemActions.js:340-359`), e **Sospendi** cade per conto suo (`loginManager` `CanSuspend`). ⭐ **«Esci…» resta**, perché dipende solo da `disable-log-out` |

⛔ **`no`, mai `auth_admin`**: `"challenge"` **mostra** la voce — vale su GNOME e su KDE
(`STUDI.md` §gnome §5.1, `STUDI.md` §kde §1579). ⚠ E la voce **sparisce**, non si ingrigisce: `system.js:218-226`
lega `can-*` a `visible`.

> #### ✅ E LA PORTATA È DECISA — dall'utente, il 15 agosto 2026
>
> > *«No, nessuno può spegnere, riavviare, mettere in standby o sospensione il server, altrimenti si
> > rischia di "buttare fuori" anche altri eventuali utenti collegati alla macchina.»*
> > *«L'utente collegato a REMOTIX può solo fare espressamente il logout o, ovviamente, operare sul
> > PC che sta utilizzando.»*
>
> ⇒ `DECISIONI.md` §4.7, e `SPECIFICHE.md` §11.3 è stata allargata: **non «alla sessione remota»,
> a tutti**. ⛔ La regola polkit si scrive **piatta**, senza `subject.local`: la discriminante che
> avevo proposto non serve più, e con lei sparisce la misura che sarebbe costata.
>
> ⭐ **Il metro del banco, ed è più forte di «le voci sono sparite»:** *nel menu di sistema del
> desktop remoto resta «Esci…» **e nient'altro** di quella famiglia.*

**Il lavoro, allora — tre cinture, perché le strade sono tre** (`DECISIONI.md` §4.7):

1. **la regola polkit**, piatta, sulle quattro azioni e le loro varianti `*-multiple-sessions` /
   `*-ignore-inhibit`. ⭐ Copre **due strade con una riga sola**, perché guarda l'azione e non
   l'interfaccia: il menu **e** `systemctl poweroff` da un terminale dentro la sessione;
2. **`logind.conf`**: `HandlePowerKey`, `HandleSuspendKey`, `HandleHibernateKey`, `HandleLidSwitch`
   = `ignore` — ⛔ il tasto fisico **non passa da polkit**, e la prima cintura non lo vede;
3. **la sospensione automatica**, che è §2.2 di questo documento: l'`Inhibit` **e**
   `sleep-inactive-ac-type=nothing`. ⚠ Due cinture per **due sintomi**: polkit impedisce il fatto,
   dconf toglie dallo schermo la notifica *«Automatic Suspend»* che l'utente vedrebbe lo stesso.

**E quel che resta da fare bene:**

- ⚠ **sono tutte righe di configurazione, cioè quel che I7 vieta**: vanno **installate da noi** e
  **verificate dopo l'avvio**, come l'headless di `DECISIONI.md` §4.3-bis. ⭐ Qui la verifica non ha
  incognite: si chiede a logind `CanPowerOff` / `CanReboot` / `CanSuspend` / `CanHibernate`
  **dalla sessione dell'utente** e si pretende **`no`**; se risponde `yes` o `challenge`, si dichiara
  il fallimento;
- ⚠ **root resta, e deve restare**: `systemctl --force poweroff` parla con PID 1 e salta logind.
  ⭐ È la strada dell'amministratore, e i client attaccati lo vengono a sapere con
  `SERVER_IN_CHIUSURA 0x0C` — ⭐ già emesso da `main.c` · `main()`, cura del rilievo B-7. ⇒ **questo
  percorso va provato in questa fase**: adesso è l'unico spegnimento legittimo che esista;
- gli altri desktop arrivano con le loro fasi (KDE è la 10): la regola polkit è **la stessa per
  tutti e quattro** — `STUDI.md` §xfce §618 dice che su XFCE non esiste nessuna chiave e restano solo
  polkit e logind — ⛔ ma **si verifica desktop per desktop**, quando la fase arriva.

#### 1.2 ⛔⛔ Chiusura della scheda **contro** «Esci» dal menu: due esiti, e oggi uno solo esiste

> ### ⭐⭐ LA DISTINZIONE, DETTATA DALL'UTENTE IL 15 AGOSTO 2026
>
> > *«Distinguiamo il comportamento del PC usato dall'utente rispetto a quello che fa REMOTIX. Se
> > l'utente chiude, spegne o riavvia il **proprio** PC, questo lo trattiamo come browser chiuso /
> > connessione caduta. Se invece sceglie la voce «Esci/logout», allora significa che l'utente vuole
> > **terminare la sessione**, il che comporta la chiusura di tutti i programmi che aveva in
> > esecuzione.»*
>
> ⭐ **Il PC dell'utente non è mai un caso speciale**, e questo toglie lavoro invece di aggiungerne:
> scheda chiusa, browser chiuso, PC spento, PC riavviato, campo perso in galleria — **un caso solo**,
> quello già misurato. Non c'è niente da rilevare dal lato client e niente da distinguere sul filo.
>
> ⭐ **«Esci/logout» è l'unico gesto che significa «ho finito»**, e la sua conseguenza è dichiarata:
> **i programmi dell'utente si chiudono**. Non è un distacco più forte: è l'altro verso.
>
> ⛔ **E tre cose smettono di essere domande:**
>
> 1. ⛔ **`disable-log-out` è VIETATA.** Toglieva la voce «Esci…» e faceva rifiutare
>    `SessionManager.Logout`: adesso che il logout è una funzione **promessa**, quella chiave
>    toglierebbe la funzione. ⇒ per §1.1 resta **solo** la regola polkit — la strada si è chiusa da
>    sé, senza doverla scegliere. *(Era la domanda 2 di §4, e decade.)*
> 2. **`org.gnome.shell always-show-log-out` va acceso.** `[R]` Senza, su una macchina con un utente
>    e una sessione sola gnome-shell **non mostra** la voce. ⚠ E rovescia
>    `reference-gnome/rapporti/02-shell-blocco-voci.md:214` — *«va lasciata `false`»* — che era
>    scritto quando l'obiettivo era togliere voci, non darne una. *(Era la domanda 3 di §4, e
>    decade.)*
> 3. **Fra il clic e la fine non tocchiamo niente**: se un programma ha lavoro non salvato, GNOME
>    mostra il **suo** dialogo dentro il desktop remoto, come se l'utente fosse al monitor. È I8, e
>    vale anche qui.

| caso | oggi | che cosa manca |
|---|---|---|
| **1 · il filo cade** — scheda chiusa, browser chiuso, ⭐ **il PC dell'utente spento o riavviato** | ⭐ **vivo e misurato**: `pagina.html` · `MP4_DURATA_MAX()` aggancia `pagehide` (⛔ non `beforeunload`) e spedisce `CONGEDO 0x01` prima di morire — `[M]` il server l'ha visto arrivare. Il posto si libera, **la sessione sopravvive** (I4, `SPECIFICHE.md` §5.2). ⚠ E quando il PC muore di colpo il `CONGEDO` non parte affatto: allora è l'orologio del **silenzio** a liberare il posto, 30 s (§5.3) — ⭐ **stesso esito, altra strada** | il **banco** che lo provi, e lo provi **due volte di fila** (`LEZIONI.md` §2.3-ter) |
| **2 · l'utente sceglie «Esci…» nel menu del desktop** | ⛔ **non è definito da nessuna parte e non è gestito**: `gnome-session` esce, Mutter muore, il palco cade — e sul filo **non parte nessun motivo**. Il client vede una connessione che si spegne, cioè esattamente la forma di guasto del rilievo **B-7** | tutto quel che segue |

**Quel che il caso 2 richiede, in ordine:**

- **chi se ne accorge**: il figlio sorveglia già l'unità `gnome-session-manager@gnome.service`
  (`sessione.c`, `unita_inattiva()`); qui serve accorgersene **mentre accade**, non chiederlo;
- ⛔ **il motivo deve partire PRIMA che il filo muoia**, ed è la parte che oggi non esiste: quando
  Mutter cade, il palco cade con lui e il canale non serve più a niente. ⚠ È l'ordine, non il
  contenuto, a essere il difetto — la stessa forma del rilievo **B-7**;
- ✅ **il motivo sul filo è `0x10 SESSIONE_TERMINATA`**, aggiunto a `RCP.md` §8.2 il 15 agosto: non
  il riuso di `0x01`, che porta la promessa opposta *«riattacca e ritrovi tutto»*. ⇒ da definire in
  `rcp.h`, da **emettere** in `rcp.c`, e da leggere in `pagina.html` — ⛔ e i tre pezzi vanno insieme,
  o è il rilievo B-7 daccapo;
- ✅ **che cosa legge l'utente**: *«la sessione è terminata»* sopra il **modulo di accesso**
  (deciso dall'utente il 15 agosto, `DECISIONI.md` §4.1-quater). ⛔ Non una schermata di chiusura;
- **la pulizia**: posto liberato, palco smontato, e il prossimo attacco è una **sessione nuova** —
  non un riattacco a un palco morto;
- ⭐ **la seconda strada per lo stesso logout** (`DECISIONI.md` §4.1-quinquies, 15 agosto): la
  scorciatoia **`Ctrl+Alt+Fine`** gestita **dalla pagina** — con `preventDefault()`, la conferma
  *«terminare la sessione?»*, e ⛔ da **aggiungere alla sonda S3** (`banchi/04-b29-scorciatoie.py`,
  42 combinazioni: questa non c'è) e misurare su due motori prima di prometterla. ⛔ **Nessun
  bottone a schermo**: la voce del menu si raggiunge col dito e basta a sé stessa. ⚠ E le due strade
  finiscono **nella stessa** `sessione_termina()`: un solo percorso di uscita, o due che divergono;
- ⚠ **e la nostra `sessione_termina()` resta valida**: chiude con `SessionManager.Logout`, che
  `disable-log-out` avrebbe ucciso (`STUDI.md` §gnome §5.1). ⭐ Vietando quella chiave, il congedo del
  server e il logout dell'utente **passano dalla stessa porta**, e la porta resta aperta.

#### 1.3 Il riattacco da uno schermo di misura diversa — e i compositori

⭐ **Tre quarti sono già fatti e misurati**, ma nella **coda della fase 4** (§04-si-comanda,
`rapporti/F4-IN-13-la-tela-che-cambia.md`): la tela è la finestra, `SESSIONE` concede la tela che il
palco ha già con **zero fotogrammi scartati** `[M]`, e il ridimensionamento a caldo costa **6 ms**.

> #### ✅ ⭐⭐ E IL RIATTACCO A MISURA DIVERSA È STATO MISURATO — 16 agosto 2026, **e l'ha fatto l'utente**
>
> *`banchi/05-b4` dichiara per iscritto di non poterlo provare: «`01-b3-cliente.py` non conosce
> `ADATTA_TELA` (zero occorrenze; la pagina ne ha 45) ⇒ si misura col browser».*
>
> `[M]` Sessione aperta col browser **massimizzato** (`2544x926`), scheda chiusa, riattacco con la
> finestra **ridotta**. La catena intera in **61 millisecondi**:
>
> ```
> 17:11:00.875  ⚠ RIPIEGO DICHIARATO (§4.5): chiesta 1240x622, il palco ha 2544x926
>                 → CONCESSA quella del palco, così i fotogrammi arrivano da subito
> 17:11:00.887  ⭐ ADATTA_TELA 1240x622 GIRATA al palco            (+12 ms)
> 17:11:00.935  ⭐ tela IN VIGORE cambiata da 2544x926 a 1240x622  (+60 ms)
> ```
>
> | | |
> |---|---|
> | fotogrammi dopo il cambio | **62**, tutti a `1240x622` — **zero** alla misura vecchia |
> | CHIAVE alla misura nuova (§5.2) | ✅ `fotogramma 2` |
> | `NON lo spedisco` (il congelamento) · «il palco non è alla tela» (il *ballo*) | **0** e **0** |
> | ⭐ **e quel che ha visto l'utente** | *«il desktop copre per intero lo schermo (che adesso è di dimensioni ridotte)»* · *«funziona»* |
>
> ⚠ **E una trappola del registro, pagata sul posto**: il primo conteggio diceva «1 fotogramma alla
> misura vecchia dopo il cambio». ⛔ Era falso: una riga del registro aveva **perso il timestamp** —
> due processi che scrivono sullo stesso file si erano accavallati — e senza data `$1 >= "17:11:00.935"`
> la prendeva per buona, perché una parola ordina dopo una cifra. ⇒ *Un confronto su un campo che può
> mancare non è un filtro, è una scommessa.*

**Quel che resta a questa fase:**

- ✅ **il tasto e il puntatore DOPO il riattacco a misura diversa** — ⭐ **chiuso il 16 agosto 2026, e
  l'ha chiuso l'utente senza saperlo.** Il timore era misurato: al cambio di geometria **`libei`
  distrugge e ricrea i dispositivi assoluti** (`[M]` 15 ago, *«il puntatore è stato TOLTO dal
  compositore, ricambio n. 640»*), e il puntatore al dispositivo vecchio smette di funzionare **senza
  errore** (`STUDI.md` §gnome §9) ⇒ la prova sarebbe stata **verde per costruzione**.

  `[M]` **E il ricambio è avvenuto davvero**, al ridimensionamento verso `1240x622`:

  ```
  17:11:00.918  il puntatore e' stato TOLTO dal compositore (ricambio n. 1)
  17:11:00.918  il puntatore e' stato TOLTO dal compositore (ricambio n. 2)
  ```

  ⭐ **Un minuto dopo, alla misura nuova, l'utente ha aperto il menu di sistema col mouse e premuto
  «Log Out»** (`17:12:05.742 §7.6: prova ha chiesto di USCIRE`, e la sua schermata mostra il menu
  aperto): un bersaglio piccolo, nell'angolo. ⇒ **I clic finiscono dove punta, dopo il ricambio dei
  dispositivi.** E lo stesso nell'altro verso, verso `2544x926`: `[M]` alle `17:13:09` trenta
  `PUNTATORE` con coordinate fino a `2509`, coerenti con la tela nuova.

  ⚠ **Quel che questa prova NON è**: un banco. È una misura su gesti veri, e vale per Mutter su
  questa macchina. ⇒ Il banco resta desiderabile, ma non è più l'unica cosa che sta fra noi e il
  sapere;
- ✅ **che fine fanno le finestre aperte** quando la tela rimpicciolisce — ⭐ **chiuso dall'utente il
  16 agosto 2026**, e con l'argomento giusto: *«il punto 1 si è chiuso nel momento in cui ho
  riattaccato la sessione con il browser a finestra: se fosse accaduto qualcosa il terminale lasciato
  aperto si sarebbe chiuso»*.

  ⇒ `[M]` La tela è passata da `2544x926` a `1240x622` con un terminale aperto e un `cat /dev/urandom`
  dentro: **la finestra è sopravvissuta, il processo pure** (PID 523560, 2 min 31 s), e il desktop è
  rimasto usabile alla misura nuova — l'utente ci ha aperto il menu di sistema col mouse.

  ⚠ **Quel che resta NON osservato**, e si scrive per non spacciarlo per provato: se una finestra
  **più grande dello schermo nuovo** venga riportata dentro da Mutter o resti tagliata. ⛔ Il
  terminale della prova era piccolo, quindi il caso non si è presentato. È cosmetica, è di GNOME, e
  non blocca niente;
- **la tabella dei compositori**, che è la parte «studia bene i compositori» del punto:

| | ridimensiona a caldo? |
|---|---|
| **Mutter** (GNOME) | ✅ `[M]` — è la strada su cui la coda della fase 4 è stata misurata |
| ⛔ **KWin** | **no fino a `v6.7.4` compreso** — `[R]` verificato su invent.kde.org il 14 ago: il ridimensionamento c'è **solo su `master`**, `Plasma/6.8` **non esiste** e non ha data. Riavviare KWin ucciderebbe la sessione, cioè proprio il distacco che il modello offre ⇒ **ripiego dichiarato** (`DECISIONI.md` §5.0-bis): si tiene la tela vecchia e riscala il client. ⛔ La riga nel registro (`COMPOSITORE_INCAPACE`) esiste nel codice ed è provata **su un ospite finto** — verificabile davvero solo alla **fase 11** (KDE) |
| **labwc** (XFCE, LXQt) | ⚠ e il rischio non è la misura: su **XFCE** `xfsettingsd` è il primo client della sessione e **spegne ogni output nuovo** (`enabled = FALSE`); su **LXQt** non c'è niente di simile (`SPECIFICHE.md` §11.2) |
| **muffin** (Cinnamon) | la riga peggiore, e prima del ridimensionamento mancano `RecordVirtual`, libei e gli appunti |

⭐ **La memoria dell'utente era giusta**: KWin è il caso problematico, e la sua degradazione è
**l'unico punto del modello che non può essere servito**.

#### 1.4 L'utente che ha **già** una sessione grafica attiva

`SPECIFICHE.md` §5.1 li elenca tutti e quattro. Lo stato, oggi:

| situazione | motivo | stato |
|---|---|---|
| remota viva + un **secondo dispositivo** | `0x0F GIA_ATTIVA_REMOTA` | ⭐ **vivo e provato** `[M]`: il registro dei posti in `rcp.c`, e il caso 18 del banco `04-b31` |
| remota **muta da 30 s** + un altro dispositivo | *(entra)* | vivo: `torna_a_parlare()` |
| ⛔ **locale già attiva**, arriva la remota | `0x05 GIA_ATTIVA_LOCALE` | **definito in `rcp.h` · `rcp_tetto_imposta()` e MAI EMESSO da nessun `.c`** |
| ⛔ remota viva, **si apre la locale** | `0x04 SESSIONE_LOCALE_PREVALSA` | **definito in `rcp.h` · `rcp_tetto_imposta()` e MAI EMESSO** |

⛔ È la stessa forma di guasto di `RCP_SERVER_IN_CHIUSURA` (rilievo **B-7**): un motivo che esiste
nell'intestazione e che nessuno spedisce. ⭐ E la pagina **è già pronta a leggerli**
(`pagina.html:440-441`): manca solo chi li manda.

**Quel che serve:**

- **chi guarda le sessioni locali — logind.** Oggi l'unico file che lo nomina è `sessione.c`, di
  sfuggita. Il pezzo da riportare è `fondamenta/remotix-c/src/sentinella.c` (307 righe): `ListSessions` +
  i segnali `SessionNew` / `SessionRemoved`, e le proprietà `Type`, `Remote`, `Active`;
- ⛔⛔ **la definizione di «sessione grafica locale», scritta prima del codice — e la prima stesura
  ovvia è SBAGLIATA.** Il criterio che viene in mente è `Type ∈ {wayland, x11}` **e**
  `Remote = false`; ⛔ ma `[R]` **noi non chiamiamo `pam_set_item(PAM_RHOST, …)` da nessuna parte**
  — `autenticazione.c` · `rcp_autentica()` fa `pam_start` e basta — quindi `pam_systemd` crea le **nostre** sessioni
  senza host remoto e logind le segna con ogni probabilità `Remote=no`. ⇒ ⭐ **con quel criterio la
  nostra sessione remota conterebbe come locale, e ci rifiuteremmo da soli con `0x05`.**

  **Due cure, e conviene farle tutt'e due:**
  1. **il discrimine è il SEAT, non `Remote`**: locale = **ha un seat** (`seat0`); la nostra
     headless non ne ha (è la stessa proprietà su cui Mutter decide `is_headless()`, §2.3);
  2. ⭐ **e `PAM_RHOST` va impostato lo stesso**, con l'indirizzo del client: costa una riga e
     ripaga due volte — logind segna la sessione `Remote=yes`, **e** l'accesso finisce nei registri
     di sistema (`last`, audit) con la provenienza, che oggi non c'è.

  ⏳ `[?]` **Da misurare sulla macchina**, e non è dedotto: `loginctl show-session` sulla sessione
  di `prova` e su quella locale di `nicfio`, guardando `Type`, `Class`, `Remote`, `Seat`, `Active`.
  ⚠ Tentato il 15 agosto sera: la macchina non rispondeva a ssh;
- le sessioni **testuali** (ssh, tty) devono continuare a convivere: sono innumerevoli, §5.1;
- ⚠ il caso `0x04` è l'unico in cui **il server butta fuori un client sano**: `DECISIONI.md` §4.1-bis
  lo ammette solo con un motivo dicibile, ed è per questo che il motivo esiste. Il banco lo verifica
  **dal lato che lo riceve**.

#### 1.5 ⭐ Il multi-tenant: la domanda dell'utente, e la riga dove passa il confine

*Chiesto dall'utente il 15 agosto: «poiché qui trattiamo le sessioni, mi chiedo se il multi-tenant
non ricada in questa fase».*

✅ **Deciso dall'utente lo stesso giorno: «potremmo anche lasciare in questa fase 1 solo utente, e
nella fase 12 il multi-tenant».** ⇒ `DECISIONI.md` §4.6-quater, dove il confine vive per intero.
⚠ La domanda era buona perché i documenti dicevano cose diverse: `SPECIFICHE.md` §5.5 dice *«il
multi-tenant è delle fasi da 5 in poi»*, `PIANO.md` intitolava la fase 12 «Multi-tenant e il budget».

> ⚠ **E quella fase adesso è la 10, non la 12** — spostata dall'utente il **16 agosto 2026**
> (`DECISIONI.md` §4.6-sexies): *«PRIMA si chiude lo sviluppo anche con il multi-tenant, e solo
> dopo si pensa agli altri DE»*. ⭐ **Il confine deciso qui non è cambiato**, è cambiato il posto in
> fila. ⛔ E la frase virgolettata qui sopra **resta com'era detta**: era il numero di quel giorno.

| | dove | in breve |
|---|---|---|
| **un utente remoto per volta** | ⭐ **questa fase** | nessuna prova di due sessioni remote insieme, nessun budget, nessun conteggio |
| **più sessioni insieme, il budget, `BUDGET_PIENO`, `MAX_ATTACCATE` configurabile** | **fase 10** | hanno bisogno di un numero vero, e lo dà il codificatore hardware della **fase 8** |
| ⛔ **il codice chiavato sull'utente**, e il guardiano di logind che **discrimina per utente** | ⭐ **questa fase, e non è rinviabile** | ⛔ non perché sia importante: perché **non si può scrivere «per un utente solo»** |

⛔ **E la ragione per cui l'ultima riga non si rinvia è che la macchina la smaschera da sola.** Il
guardiano di §1.4 risponde a una domanda che suona in due modi diversissimi — *«c'è una sessione
grafica locale?»* contro *«c'è una sessione grafica locale **di questo utente**?»* — che sono una
riga di differenza e due prodotti diversi. ⭐ E la macchina di prova è **già** nella configurazione
che smaschera l'errore: `nicfio` ha la sua sessione grafica **locale**, `prova` si collega da
**remoto**. Scritto male, `prova` viene rifiutato con `0x05` **il primo giorno**.

⇒ ⭐ **Il banco di `0x04`/`0x05` si scrive su quella coppia** — locale `nicfio` e remota `prova`, che
**devono convivere senza toccarsi** — e costa quanto costerebbe comunque.

⚠ ~~**E il ripiego resta dichiarato**: `MAX_ATTACCATE` è un `#define` a **16** dove §5.5 promette
**dieci configurabile**. Oggi non morde, e la sua scadenza è la fase 10.~~ ✅ **PAGATO il 25 agosto
2026** (fase 10): `RCP_TETTO_SESSIONI` in `src/rcp.h`, e **`--tetto-sessioni N`** lo cambia.

---

### 2 · Quel che il piano chiedeva già, e resta

*Dal mandato §3 e §4 — nessuno di questi ha un banco, ed è esattamente il lavoro della fase.*

1. ✅ **Il rilascio dei tasti al distacco, CON UN TASTO PREMUTO DAVVERO** — `[M]` **16 agosto,
   provato col browser su due delle quattro strade, e il testimone è il desktop vero.**
   `RCP.md` §11 la chiama *«la regola col rapporto danno/costo più alto del documento»*.
   ⇒ **Regge**, e i tempi sono quelli di §6-bis qui sotto. ⛔ Ma la prova ha trovato **due difetti**,
   uno chiuso e uno aperto: la riga che diceva sempre `0` (chiusa) e **l'orologio del silenzio**
   (punto 4, e adesso ha una misura).
2. ✅ **L'inibizione della sospensione** — `[M]` 16 agosto, **20 giri su 20**: *«sospensione e
   inattività INIBITE al gestore di sessione (flag 12 = SUSPEND\|IDLE — mai LOGOUT)»*. ~~Quel che
   segue resta come cronaca di com'era:~~ `[M]` 15 agosto: la notifica **«Automatic Suspend —
   Suspending soon because of inactivity»** compare in due schermate del desktop remoto.
   `sleep-inactive-ac-type` vale `suspend` a **900 s**. La cura è una chiamata:
   `SessionManager.Inhibit(…, 12)` = `SUSPEND|IDLE` **insieme**, ⛔ **mai** il bit `LOGOUT`.
   ⚠ `energia.c` **non esiste in `src/`**: va portato da `fondamenta/remotix-c/src/energia.c`.
   ⚠ E senza questa, il banco delle **sei ore** non misura niente.
3. ✅ **L'headless si dichiara e si verifica dopo l'avvio** — `[M]` 16 agosto, **20 giri su 20**: il
   figlio scrive *«VERIFICATO: la mia sessione non ha seat ⇒ Mutter è headless»*. ⛔ Non è più «per
   accidente»: è un fatto letto dal nucleo a ogni sessione.
4. **I tre orologi**: ✅ **30 s di silenzio** — era **rotto**, trovato il 16 agosto col browser
   mentre si provava il punto 1 (contava i secondi in cui *l'utente non tocca niente* invece di
   quelli in cui *il client tace*: un secondo dispositivo entrava e si prendeva il desktop di chi
   stava guardando). **Riparato e provato in tre punti**, §6-bis. ✅ **30 min di inattività**: fatto il 16 agosto,
   motivo `0x02` di §8.2 che era dichiarato e mai spedito — §6-quinquies. ✅ **il terzo**: niente 6 ore — **60 minuti
   senza input e la sessione si chiude** (`DECISIONI.md` §4.8), provato a 20 s in §6-septies.
5. ✅ **Distacco e riaggancio due volte di fila** — *«un banco che passa solo da macchina pulita non è
   un banco, è una dimostrazione»*. ⇒ `[M]` 16 agosto: **cinque giri**, tre col distacco pulito e
   **due col filo tagliato**. Indistinguibili fra loro, e ⭐ **niente si accumula** — §6-sexies.
6. ✅ **La sessione senza nessuno che guarda** — `[M]` 16 agosto, col browser. In v1 il monitor
   virtuale spariva al distacco e `libmutter` andava in asserzione fallita: ⭐ **qui non succede**, e
   il costo di un desktop che nessuno guarda è **praticamente zero**. Misure in §6-quater.
7. ✅ **PAM per intero**: asincrono (`aiutante.c`) **e** la sessione PAM aperta dal figlio (passo
   2-bis). `[M]` provato venti volte col browser: *«PAM ha risposto: ammesso — e il filo non si è mai
   fermato»*.

⇒ ⭐ **I sette punti di §2 sono chiusi.**

---

### 3 · Quel che la coda della fase 4 lascia aperto e che passa di qui

| | |
|---|---|
| ⏳ la riga che manca a `RCP.md` §7.1 | che cosa fa il server quando il palco cambia misura **da sé** |
| ⚠ i 4 ms di ritardo medio aggiunto | `MOVIMENTO_ATTESA_S` a 8 ms è un ripiego dichiarato |
| ⚠ i banchi RCP/1 non esercitano `ADATTA_TELA` | `01-b3` e `01-b4` restano verdi perché il filo non è cambiato |

---

### 4 · ⛔ LE DECISIONI CHE ASPETTANO L'UTENTE

*⭐ Le domande si affrontano **una alla volta**, per volontà dell'utente.*

**Chiuse:**

| | |
|---|---|
| ✅ **le due uscite** — il filo che cade contro il logout | `DECISIONI.md` §4.1-ter, 15 agosto |
| ✅ **dopo il logout la pagina torna al modulo di accesso**, e il motivo è `0x10` | `DECISIONI.md` §4.1-quater, `RCP.md` §8.2, 15 agosto |
| ✅ ~~`disable-log-out`?~~ **vietata** · ✅ ~~`always-show-log-out`?~~ **acceso** | cadute per conseguenza, non per scelta |
| ✅ **nessuno spegne il server**, chi è davanti alla macchina compreso — e l'utente remoto ha **il solo logout** | `DECISIONI.md` §4.7, `SPECIFICHE.md` §11.3, 15 agosto |
| ✅ **il logout si raggiunge in due modi**: la voce del menu e `Ctrl+Alt+Fine` — ❌ `Ctrl+Alt+F12` e ❌ `Win+F12` scartate **con una misura ciascuna**, ❌ **nessun bottone a schermo** | `DECISIONI.md` §4.1-quinquies, `SPECIFICHE.md` §5.2-bis, 15 agosto |
| ✅ **il multi-tenant è della fase 10** — qui **un utente remoto per volta**, ⛔ ma il guardiano di logind discrimina **per utente** | `DECISIONI.md` §4.6-quater, 15 agosto |

| ✅ **due secondi all'accesso vanno bene; diciotto no** — 16 agosto. ⇒ Il guadagno da 2,1 s a ~1,2 s (dichiarare la misura della finestra nel saluto invece che dopo l'ammissione) **non si fa adesso**: costa mezza giornata **nella stretta di mano**, che è l'unico pezzo dove uno sbaglio è un buco e non un difetto estetico. ⭐ Si riprende quando il protocollo si aprirà comunque — la fase 12 tocca quella zona | qui sotto, e la misura è già fatta |

**Aperte:** ⭐ nessuna. ⚠ Il 16 agosto ne è passata una che **non era una decisione**: l'orologio del
silenzio contava i secondi sbagliati (§6-bis). `SPECIFICHE.md` §5.3 e `RCP.md` §8.2 avevano già
deciso, e il prodotto non li rispettava — ⇒ **riparato senza chiedere**, perché non c'era niente da
scegliere.

#### ⏳ Il secondo che si potrebbe recuperare, con la misura già fatta

`[M]` L'accesso costa **2087 ms** di mediana, e **968** sono il figlio che aspetta: il browser
dichiara la misura della sua finestra **solo dopo essere stato ammesso**, e prima di allora la
sessione non può nascere perché non si sa a che misura.

⇒ Se la misura arrivasse **col saluto** — come già fa il tetto del decodificatore — la sessione
nascerebbe **durante** il secondo fisso invece che dopo: accesso a **~1,2 s**. ⛔ E il secondo fisso
resterebbe intatto: cambia *quando si dichiara la misura*, non *quando si risponde*, quindi il
canale del cronometro resta chiuso.

⚠ **Il costo**: `RCP.md`, `pagina.html`, `rcp.c` **e il suo gemello identico byte per byte** in
`banchi/rcp/`, `figlio.c`, il client di banco, più una prova per il caso «client vecchio che non lo
manda». **Mezza giornata**, e nel pezzo più delicato del programma.

---

### 5 · Che cosa non ha funzionato

#### 15 agosto 2026, sera — quattro cose, e tre le ha trovate il banco

1. ⛔⛔ **La pila PAM del prodotto non chiamava `pam_systemd`.** `src/remotix.pam` chiudeva con
   `common-session-noninteractive`, che su Debian **non** contiene `pam_systemd` — quindi nessuna
   sessione logind, quindi niente `is_headless()` e niente soggetto per §5.1. ⭐ **E funzionava
   lo stesso, per un accidente rovesciato**: il file non era installato, PAM ripiegava su `other`,
   e `other` include `common-session`, che `pam_systemd` ce l'ha. ⇒ Installare il nostro file
   «come si deve» avrebbe **rotto** quel che l'assenza del file faceva funzionare.
   *(`DECISIONI.md` §1.10-ter.)*
2. ⛔ **La regola polkit di v1 copriva 3 azioni su 12**, e la mancante era
   `power-off-multiple-sessions` — cioè **il caso multi-utente**, l'unico per cui la regola era
   stata scritta. Con un utente solo funzionava.
3. ⛔ **Il mio ragionamento su root era sbagliato**, e me l'ha detto la misura: avevo scritto in
   `DECISIONI.md` che serviva un'eccezione per root, altrimenti `sudo systemctl poweroff` sarebbe
   fallito. `[M]` Non serve: logind guarda `CAP_SYS_BOOT` **prima** di polkit. ⇒ La voce è stata
   corretta, e con lei la conseguenza vera — **la verifica non si può fare dal server, che è root**.
4. ⛔⛔ **Il banco è stato verde due volte per il motivo sbagliato**, ed è la forma che questo
   progetto paga più spesso:
   - la prima perché **gli utenti di prova non esistevano** (il rootfs vive in RAM e il riavvio li
     aveva cancellati come la chiave ssh): PAM apriva sessioni per un conto inesistente, e i casi
     «falso» erano falsi perché **non c'era niente**;
   - la seconda perché **logind rifiutava in silenzio** la seconda sessione sulla stessa console
     virtuale: `pam_systemd` è `optional`, PAM tornava `SUCCESS`, e il caso 6 era verde **perché
     vuoto**.
   ⇒ In tutt'e due i casi a smascherarlo è stato **il dump di `loginctl` dentro il banco**: un banco
   che dice solo il colore fa ricominciare la caccia da capo.

#### 15 agosto 2026, 19:02 UTC — lo schermo nero, e la domanda dell'utente

**Il sintomo**: l'utente si collega, entra, e **non vede il desktop**. La domanda che ha fatto —
*«sicuri che non hai introdotto regressioni?»* — era quella giusta da fare.

**Non era una regressione**, e il registro lo diceva per intero: l'attacco è passato (nessun `0x05`,
nessun rifiuto), e il figlio ha scritto tre volte

> ⛔ *runtime «/run/user/1001» NON c'è, socket del bus non c'è — senza bus non c'è niente da catturare*

⇒ Il riavvio aveva cancellato l'utente `prova` insieme alla chiave ssh (rootfs in RAM); ricreandolo
**non avevo acceso il linger**, e `/run/user/<uid>` lo crea quello. Curato con
`loginctl enable-linger prova prova2`, e scritto come **requisito** in `DECISIONI.md` §1.10-ter.

> #### ⭐⭐ E l'utente ha visto sotto il sintomo un tema — 15 agosto 2026
>
> > *«Bisogna fare attenzione al corretto setting delle variabili d'ambiente (XDG…). Dovrebbe essere
> > compito del session manager, ma per qualche motivo in REMOTIX sembra che non vengano
> > impostate.»*
>
> ⭐ **Ha ragione, e la ragione è strutturale**: quelle variabili le imposta `pam_systemd` al login,
> e ⛔ **noi il login non lo facciamo** — `figlio.c` · `scatto_chiudi()` dichiara fuori mandato far nascere la
> sessione. ⇒ Nessuno le imposta, e noi le **componiamo a mano**.
>
> **Quel che c'è oggi**, letto nel codice:
>
> | dove | che cosa compone |
> |---|---|
> | `figlio.c:723-737` | `HOME`, `USER`, `LOGNAME`, `PATH`, `SHELL=` (vuota), `XDG_RUNTIME_DIR`, `DBUS_SESSION_BUS_ADDRESS` — **sette, e nient'altro esiste dall'altra parte** (`execve`) |
> | `sessione.c:492-511` | le due di sopra più `XDG_CURRENT_DESKTOP`, `XDG_SESSION_DESKTOP`, `XDG_SESSION_TYPE`, `LANG` |
>
> ⛔ **E `XDG_RUNTIME_DIR` è ASSERITA, non ottenuta**: si scrive `/run/user/<uid>` per convenzione.
> La convenzione è giusta su systemd — ⚠ ma è esattamente la forma del guasto di stasera: un valore
> **dichiarato** al posto di un valore **avuto**.
>
> ⚠ **Quel che nessuno imposta, e che ricade sui predefiniti in silenzio**: `XDG_DATA_DIRS`,
> `XDG_CONFIG_DIRS`, `XDG_DATA_HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`,
> `XDG_SESSION_CLASS`. ⛔ E `XDG_SESSION_ID` **di proposito** (`sessione.c` · `locale_utf8()`).
>
> ⇒ **Il lavoro che ne nasce, per questa fase:**
> 1. un posto solo che compone l'ambiente **e lo verifica**, scrivendo per ogni variabile **da dove
>    viene** — asserita, ereditata, dedotta. Oggi `sessione.c` già lo fa per il bus (*«assente: uso
>    …»*), ed è la forma da estendere;
> 2. ⛔ `XDG_RUNTIME_DIR` si **verifica prima di `execve`**: esiste, ed è di quell'uid. Se non c'è, il
>    messaggio deve **nominare la causa probabile** — *«quell'utente ha il linger acceso?»* — invece
>    del solo sintomo, che stasera è costato un giro;
> 3. decidere se le sei `XDG_*_DIRS`/`_HOME` vadano dichiarate invece di lasciate al predefinito.

#### 15 agosto 2026, 20:00 UTC — ⛔⛔ il lag, e il prezzo nascosto dell'headless

**Il sintomo**, riferito dall'utente: *«qualche piccolo lag in generale»*, e poi il numero che conta —
*«impartisco un comando nel terminale e risponde con 1-2 secondi di ritardo»*.

**Le due cose escluse per prime, con una misura ciascuna** — ⛔ e la prima è quella che avevo
aggiunto io, quindi andava esclusa per prima:

| sospetto | misura |
|---|---|
| il **ripasso di logind** ogni 2 s, sincrono nel ciclo dei fotogrammi | ⭐ `[M]` 200 chiamate: **mediana 0,125 ms**, p95 0,226, **max 0,351 ms**. ⇒ Non è quello, e il ripiego «sincrono» di `sentinella.c` regge |
| il **danno degenerato** — `libmutter-WARNING: Not enough buffers (4) to accommodate damaged regions (6)` | `[M]` 18 avvisi in tutto, non continui. ⚠ E la lettura del sorgente di Mutter (`meta-screen-cast-stream-src.c:891`) dice che **non** sono i buffer PipeWire: sono i **posti-regione** nel metadato `VideoDamage`, che chiediamo `×4` con tetto `×16` (`cattura.c` · `parametri_di_consumo()`). Quando le regioni sono di più, Mutter dichiara **tutto il fotogramma danneggiato**. ⏳ Difetto vero, piccolo, da curare — ma non è questo il lag |

⛔ **La causa era il compositore che disegnava IN SOFTWARE**, e l'ho introdotta io: `[M]`
`gnome-shell` non aveva **nessun** nodo `/dev/dri/*` aperto. Ricreando l'utente `prova` dopo il
riavvio l'ho fatto con `useradd` nudo — `groups=prova` e basta — mentre `nicfio` è in **`video`
(44)** e **`render` (991)**, e i nodi sono `root:render` in modo `0660`. Senza accesso alla GPU,
Mesa ripiega su llvmpipe e il compositore compone **a mano** un desktop di 2544×926.

**La cura, in due passi e il secondo non è ovvio**: `usermod -aG video,render prova` — ⛔ **e far
rinascere `user@1001.service`**, perché il compositore lo avvia il **gestore d'utente**, che le
credenziali le fissa alla propria partenza: `[M]` dopo il solo `usermod` il processo aveva ancora
`Groups: 1001`. Dopo il riavvio del gestore: `Groups: 44 991 1001` e **10 descrittori** su
`/dev/dri/renderD129`.

> #### ⭐⭐ E LA DOMANDA DELL'UTENTE HA SCOPERTO UN PREZZO CHE NON ERA SCRITTO DA NESSUNA PARTE
>
> > *«Nei DE normali l'utente NON appartiene ai gruppi `video` e `render`, eppure usano
> > l'accelerazione hardware. Come mai?»*
>
> ⭐ **Perché su un desktop normale non servono i gruppi: serve il SEAT.** `[M]` verificato sulla
> macchina: `/dev/dri/renderD129` porta i tag udev **`uaccess`** e **`seat`**, e logind concede
> l'accesso con un'**ACL per utente** — è il `+` nei permessi — all'utente della sessione **attiva
> su quel seat**. Nessun gruppo, nessuna configurazione: la dà il fatto di essere seduti lì.
>
> ⛔ **E noi quel seat non ce l'abbiamo, di proposito**: è la condizione di `is_headless()`
> (`DECISIONI.md` §4.3-bis), cioè quel che ci salva dalla revoca del blocca-schermo di GNOME.
> `[M]` `getfacl` sul nodo, adesso: **nessuna voce per utente** — perché nessuna sessione sta su un
> seat.
>
> ⇒ ⛔⛔ **Il prezzo dell'headless è la perdita delle ACL di `uaccess`**, e nessun documento lo
> diceva. Per una sessione REMOTIX i gruppi `video` e `render` **non sono una comodità
> dell'ambiente di prova: sono un requisito del prodotto**, esattamente come il linger — e come
> quello vanno dichiarati e verificati, o si ripaga una serata.
>
> ⚠ **E c'è una coda da non perdere**: senza la regola udev di `DECISIONI.md` §4.6-ter — `[M]` non
> installata: `/etc/udev/rules.d` è vuota — i gruppi danno accesso a **tutt'e due** le schede, e
> `[M]` il compositore ha scelto **`renderD129`, l'AMD**. Che sia quella giusta è una decisione
> della fase 8, non un caso da lasciare all'ordine di enumerazione.

#### 15 Aug 2026, 22:09 — ⭐⭐ the cross-check, and the user brings it

*Screen recording of the client, 17,3 s at 2560×1080, delivered by the user.*

**The scene**: the WebGL **«Aquarium»** benchmark from `webglsamples.org` — 100 fish, canvas 1024×1024 —
run **inside** the remote desktop in Firefox, and watched through REMOTIX.

| what | measurement |
|---|---|
| the Aquarium's counter, **read at full resolution over 16 consecutive seconds** | ⭐ **58 · 59 · 60 · 61** — nailed at sixty, never a dip |
| **distinct** frames that reached the client's screen (`mpdecimate`) | ⭐ **453 over 17,26 s = 26,2 per second** ⚠ and the cap is the recorder's, which samples at 30: «26 delivered» cannot be told from «more than 26, sampled at 30» |

⭐ **It is the cross-check of tonight's §5 cure**: llvmpipe does not do 60 fps on a WebGL with 100
fish, not even by mistake. ⇒ The GPU is there, and the missing-groups defect really was the whole lag.

⚠ **And what this measurement does NOT say, declared**: it is not a **latency** measurement — it says the
stream is smooth, not how much time passes between the key and the pixel. That remains `[M]` 41 ms from the tail
of phase 4, and must be redone on this configuration.

> #### ⛔⛔ AND THIS MEASUREMENT WAS TAKEN ON THE WRONG CARD — constraint set by the user, 15 Aug
>
> > *«I test vanno fatti sulla GPU integrata, altrimenti "trucchiamo" il gioco. La solidità del
> > sistema la si vede su GPU poco potenti, non mostri come la RX 6800.»*
>
> `[M]` The Aquarium's 60 fps were taken on the **Radeon RX 6800**, because without the udev
> rule of `DECISIONI.md` §4.6-ter — not installed — **the compositor chose the card**, and
> it had taken the discrete one. ⇒ ⛔ **The number is not valid as a measurement of the product**: it says how fast
> that hardware is.
>
> ⭐ **Cured the same evening** (`DECISIONI.md` §4.6-quinquies): `gpu-udev.sh 0000:03:00.0` excludes the
> Radeon, and `[M]` after restarting the manager and the session `gnome-shell` opens **6 descriptors on
> `renderD128`** — the **Intel UHD 730**, and only that.
>
> ⇒ **The Aquarium measurement must be redone on the integrated one**, and that is the one that counts.
>
> #### ⭐⭐⭐ AND REDONE ON THE INTEGRATED ONE IT HOLDS — reported by the user, 15 Aug 2026, 20:15
>
> > *«Su Android ho 60 fps fissi con il test Aquarium.»*
>
> `[M]` **Verified that the scene was the right one before believing it**: `gnome-shell` pid 22462 —
> the one born **after** the udev rule — has 6 descriptors on **`renderD128`**, the Intel UHD 730; and the
> log says that at `20:15:12` **`192.168.0.24`** connected, a device different from the
> laptop (`.3`), with canvas 2544×926 and view 2560×926: the **DeX**.
>
> ⇒ ⭐ **WebGL Aquarium, 100 fish, steady 60 fps — on the integrated GPU, watched from Android.** ⚠ And
> it counts double because DeX is the **primary** use (`DECISIONI.md` §5-bis.0), i.e. the case where the wire
> is longest and the device weakest. ⛔ What this measurement is not remains: **it is not latency**.

#### 15 Aug 2026, 20:27 UTC — ⭐⭐⭐ THE PRODUCT GIVES BIRTH TO THE SESSION, and the chain closes

*Order of work **changed at the user's indication**: «il discorso `Ctrl+Alt+Fine` introduce
poi anche il discorso della persistenza della sessione, del detach e re-attach». ⛔ They were right, and
the consequence was tighter than that: **implementing logout before the product owns the
birth of the session would have been harmful** — `Ctrl+Alt+Fine` would have closed the session and
nobody would have made another. A function that takes the user to a black screen.*

**What was written:**

| | |
|---|---|
| `figlio.c`, `diventa_ed_esegui()` **step 2-bis** | opens the **PAM session** after closing the descriptors and before dropping to the uid: `XDG_SESSION_TYPE=wayland`, `XDG_SESSION_CLASS=user`, `PAM_RHOST`, ⛔ **no `XDG_SEAT`** — headless by construction. `pam_end` **without** `pam_close_session`: the session belongs to the leader process, and it is I4 seen from the system |
| `figlio.c`, `prendi_il_palco()` | the line *«guardo e non tocco»* became **«LA FACCIO NASCERE io»**, with a one-minute bridle |
| `sessione.c/h`, `sessione_fai_nascere()` | gives birth **without waiting**: `sessione_assicura()` waits up to 40 s, and the caller is the only process that in those 40 s must answer the parent (`LEZIONI.md` §6.2-bis). ⭐ The wait already exists and it is the retry loop |
| `/media/REMOTIX/tmp/riavvia-7700-unita.sh` | ⛔ **the server outside any user session** — see below |

⛔⛔ **And the deployment constraint that follows from it, measured**: `pam_systemd`, when the caller is
already in a session, **does not create a second one and does not say so**. `[M]` With the old
`riavvia-7700.sh` — which uses `setsid`, which detaches the terminal but **does not change the cgroup** — the
server was in `session-127.scope` (`nicfio`'s ssh), and the children stayed without a session: **the
same black screen, from a new cause**. With `systemd-run` it is in `system.slice`.

**The test, from a clean slate** — no `prova` session, no `/run/user/1001`, ⛔ **linger
off**, no scaffolding:

| time | the log |
|---|---|
| 20:27:15 | `⭐ IL BUS DI SESSIONE È MIO: collegato come uid 1001` |
| 20:27:15 | `⭐ nessuna sessione grafica per «prova»: LA FACCIO NASCERE io (tela 1920x1080) e torno subito` |
| 20:27:15 | `sessione avvio la sessione grafica: exec gnome-session --session=gnome` |
| 20:27:47 | `cattura il nostro monitor è Meta-0 («Virtual remote monitor»), 0 prima e 1 dopo` |
| 20:27:47 | ⭐ `fotogramma catturato COME «prova»: 1920x1080 … BGRx a 8 bit, **non nero**` |

`[M]` **And the session born from the product is the right one**: `loginctl` gives it as `c52`, **`Class=user`**,
`RemoteHost=remotix`, **`Seat=` empty**; and the compositor opens **`renderD128`**, the integrated one — the
udev rule holds even on a session that is born by itself.

⚠ **The price, declared**: from the first attach to the first frame **~32 seconds** pass, and it is
the cold start of `gnome-session`. It happens once per session, ⛔ but in those 32 s the client is
attached and sees nothing — and today we do not tell it why.

> ⭐ **And this number is OLD: on 16 Aug the cold start measures `[M]` 2353 ms**, not 32 s (see
> §«venti giri dal browser»). ⇒ The underlying defect remains — *while you wait we do not tell you why* —
> but the wait went from half a minute to two and a half seconds, and the urgency with it. ⏳ To be covered,
> not rushed.

#### 15 Aug 2026, 20:50 UTC — ⛔⛔ «il terminale è congelato finché non muovo il mouse»

**The symptom, and the user isolated it** after I had chased the bandwidth for half an hour:

> *«Dal terminale do il comando `exit` e il terminale sembra come congelato: non appena muovo il
> mouse allora si chiude correttamente.»*

⭐ **That sentence is the diagnosis**: if the screen catches up as soon as *any frame* arrives,
then the right frame **had been produced and was not delivered**.

**What I had excluded before, with measurements** — and they are needed, because they say where it is NOT:

| | |
|---|---|
| from the stage to the wire | `[M]` **0 ms** median and p95, **1 ms** maximum over 200 frames |
| the encoder | `hevc_vaapi` **in hardware** on `renderD128` *(the key's time, with the card from memory, is removed with phase 18)* |
| the logind recheck | `[M]` 0,125 ms median |
| the bandwidth | ⚠ there were drops at 45 Mbit/s **with the Aquarium running** — ⛔ but the user said *«niente Aquarium»*, and the lead fell |

⛔⛔ **THE CAUSE, and it was written in a comment in our code**: `cattura.c` delivered the
frame **only if someone was waiting for it at that instant** —
`if (qualcuno_aspetta && !posto_pieno)` — with this justification: *«copiare 8 MB per nessuno
sarebbe lavoro dentro la richiamata di tempo reale, fatto per niente»*.

⭐ **The reasoning is right for the steady state and wrong for the case the user sees.** The window
that closes produces a **burst**: we take the first frame and spend time converting it
and compressing it; ⛔ all those arriving in that time find `qualcuno_aspetta == FALSE` and
**are thrown away — including the last one**, the one with the window already gone. Then the scene is still and
Mutter sends nothing more (cadence `0/1`: *«un fotogramma quando cambia qualcosa»*). ⇒ The user
is left looking at the **first** frame of the burst, until a movement produces another one.

⛔ **And the second half of the same defect was on the consumer's side**: `cattura_prendi()`
on entry did `posto_pieno = FALSE`, i.e. **threw away the frame it found already ready**
and started waiting for a new one that, with a still scene, would never arrive.

**The cure**: **the latest one is always kept** — a single slot, the most recent wins, which is also the
right policy for a remote desktop (nobody has any use for an old frame). ⭐ And the
cost the old comment feared **is paid less than before**: the buffer is **reused**
(`posto_capienza`), so the real-time callback does one `memcpy` and no longer a
`g_free`+`g_malloc` of 8 MB.

⚠ **With a new counter in the summary line** — *«sostituiti nel posto N (prima del 15 ago
erano PERSI)»* — because the number that counts is not that the cure is there: it is **how many times it is needed**.

> #### ⭐⭐⭐ CONFIRMED BY THE USER — 15 Aug 2026, and the judgement goes beyond the defect
>
> > *«Ora il terminale si chiude subito, problema risolto **sia su Linux sia su Android**. Inoltre
> > adesso il sistema mi sembra **tremendamente responsivo**, i tempi di risposta sono istantanei
> > anche su Android, e considerando che sia su una Intel integrata direi risultato eccellente.»*
>
> ⭐ **And the gain is bigger than the cure, for a reason worth understanding**: it was not only
> the last frame being lost — **all those of every burst** were lost, i.e. those that
> arrived while we were compressing the previous one. ⇒ Every window that opens, every scroll, every
> terminal line was choppier than necessary, **and nobody had ever noticed** because the
> defect showed only in the tail.
>
> ⇒ ⚠ *A defect that shows up in an edge case can cost in all the others, silently.*
> The full lesson is in `LEZIONI.md` §6.5.
>
> ⏳ **And now the latency measurement must be redone**: the `[M]` 41 ms of the tail of phase 4 are from before
> this cure, and on a different configuration. We do not know the real number yet.

*⚠ The test machine's clock is **UTC**, i.e. two hours behind ours: the times
below are its own.*

#### 15 Aug 2026, 18:20-18:35 UTC — the machine, after the reboot

*The machine had frozen; the user rebooted it, and the rootfs lives in RAM ⇒ ssh key
reinstalled and `provision-server.sh` run again.*

| | outcome |
|---|---|
| **`provision-server.sh`** | passed, ⛔ **except §4** (*«daemon-reload d'utente fallito»*, the user bus was not there). ⭐ **And it is not a problem**: that section writes `--virtual-monitor` in `/etc/systemd/user/`, i.e. exactly what v2 **no longer wants** since 14 Aug — `sessione.c` writes its own `zz-` drop-in precisely to win over that one. ⇒ **v1 provisioning left behind**, to be redone for v2 |
| ⭐ **`loginctl` — the discriminant** | `[M]` the **ssh** session shows `Remote=yes`, `RemoteHost=192.168.0.3`, `Type=tty`, **`Seat=` empty**. The seat exists (`seat0`) but ⛔ **no local graphical session is alive**: to test `0x05` a real login at the console will be needed |
| ⛔⛔ **v1's polkit rule covered 3 actions out of 12** | `[M]` `org.freedesktop.login1.policy` also has `*-multiple-sessions` and `*-ignore-inhibit`. ⇒ With **several users** logind asks for `power-off-multiple-sessions`, which v1 did not name: **it failed exactly in the case it was written for**. ⚠ And `…login1.halt` **does not exist**: dead line |
| ⭐ **root needs no exceptions** | `[M]` with the rule in force: from `nicfio` `CanPowerOff="no"`, **from root `"yes"`** — logind looks at `CAP_SYS_BOOT` **before** polkit. ⇒ ⛔ **the check must be done from the CHILD, not from the server**, which is root and would always be told yes |
| ⭐ **the physical button was live** | `[M]` all the `Handle*` lines of `logind.conf` were **commented out** ⇒ `HandlePowerKey=poweroff`. The button powered off the server with anyone connected to it |
| ✅ **the two belts installed and reread** | `[M]` from `nicfio`: `CanPowerOff` `CanReboot` `CanSuspend` `CanHibernate` = **all `"no"`**; `systemd-analyze cat-config` says `HandlePowerKey=ignore`, `HandleSuspendKey=ignore`, `HandleLidSwitch=ignore`. ⇒ `src/remotix-niente-spegnimento.rules` and `src/remotix-tasti.conf`, **in the repository** (I7) |
| ⭐ **suspend has a stronger belt** | `[M]` `sleep.conf.d AllowSuspend=no` makes `CanSuspend="no"` **even for root**: it is systemd refusing, not polkit |

#### 15 Aug 2026, 18:31-18:45 UTC — the logind guard, built and certified

| | |
|---|---|
| **the code** | `src/sentinella.c` + `.h` (new), the `sessione_locale` hook in `rcp.h`/`rcp.c`, `wt_locale_gancio` and `wt_sorveglia_locali()` in `webtransport.c`, the seam in `main.c` with a recheck every **2 s** |
| ⭐ **it is live on the server** | `[M]` in the log: *«guardiano delle sessioni locali pronto (bus di sistema); il discrimine è il SEAT, non «Remote»»* |
| ⭐⭐ **the measurement that justifies the discriminant** | `[M]` a session made **like ours** — `pam_open_session` without `XDG_SEAT` — shows to logind: `Seat=` **empty**, `Remote=no`, `Type=wayland`. ⛔ That is, **indistinguishable from a local one** if the criterion were `Remote`: the first connected user would have been rejected with `0x05` by their own session |
| ✅ **the bench** | `banchi/05-b1-sentinella.c`, **6 cases, 0 red**: no session · one like ours · a local one (`seat0`, wayland) · the local one closed · the local one **belongs to another user** · the user is at the console **in a text session** |
| ⭐⭐ **certified** | `banchi/05-b1-certifica.sh`, **3 injected faults, all three fall where they must**: seat removed → red 2 4 5 6; user removed → 5 6; graphical type removed → 6 |
| ⛔ **and the certification wrote the bench, not just checked it** | the fault «the graphical type is no longer looked at» made **nothing** fall ⇒ no case exercised that check. ⭐ From there **case 6** was born — the user at the console in a text session, which `SPECIFICHE.md` §5.1 explicitly admits («testuali e grafiche convivono») and which nobody had tested |
| ⏳ **what the bench does NOT test**, declared | it does not test the wire (`0x05` has never gone out on a real connection), it does not test `0x04` end-to-end, and ⛔ **it does not test the scene with a REAL local session**: there is nobody at the machine's console, and the bench's sessions are created by PAM |

### 6 · ⭐⭐ 16 AUG 2026 — THE RELEASE ON DETACH, TESTED WITH THE REAL DESKTOP

*«Da adesso i test si fanno sul browser e non più su banchi ipotetici. Così misuriamo quello che
succede davvero, non quello che simuliamo»* — the user, 16 Aug.

#### 6.1 The witness: a file that grows by thirty lines a second

⛔ The problem of this test was not pressing the key: it was **seeing the damage**. «A Ctrl left
down» cannot be read in a screenshot.

⭐ **The cure**: inside `prova`'s graphical session a terminal runs

```sh
while IFS= read -r _; do date +%s%N >> /tmp/testimone.txt; done
```

⇒ Every `Invio` keystroke that reaches the desktop writes **a line with the instant in nanoseconds**.
A key left down repeats by itself — it is the remote desktop doing it, not the page (`pagina.html`
says so: *«la ripetizione automatica la fa il DESKTOP remoto, che il tasto ce l'ha giù»*) — and the
file grows. A released key stops the file **instantly**.

| | |
|---|---|
| `[M]` **the repetition exists, and it is measured** | 1016 lines in ~30 s ⇒ **~33 keystrokes per second** on the real desktop |
| `[M]` **the release stops it sharply** | between the last keystroke and the log line declaring the release: **1 ms · 15 ms · 28 ms** in the three tests |

⚠ **What is fake in this test, declared**: the *keydown* is born from `dispatchEvent` inside the
page, because the browser driver cannot **hold down** a key (it always sends down-and-up
together). ⭐ Everything else is real: same page handler, same message on the wire, same
server, same `libei`, same desktop. And for the **closing of the tab** the page's
safety net (`cl_rilascia_tutto` on `blur`/`pagehide`) was removed, which is the equivalent of a browser
that dies: without removing it, **it is the page that releases and the server never has anything to do** — and that is
the reason why the morning's twenty rounds always read zero.

#### 6.2 The two paths tested, and both hold

| path | how it was provoked | `[M]` outcome |
|---|---|---|
| ⭐ **the silence of §5.3** — «the phone dead in a tunnel» | `Invio` held down, then the wire cut with `nft` on port 7700 in both directions | `13:33:07.251 STACCATO per silenzio: 30949 ms` → `13:33:07.257 rilascio al distacco: **1**`. Last keystroke of the witness: `13:33:07.229` — **28 ms before** |
| ⭐ **the client's farewell** — the tab that closes | `Invio` **and** left button held down, the page's net removed, tab closed | `13:42:55.042 congedo del client` → `13:42:55.052 rilascio al distacco: **2**`. Last keystroke: `13:42:55.037` — **15 ms before** |

⏳ **The other two paths of §7.3 were not tested** and this is declared instead of letting it be
believed: the **protocol error** (`viola_input()`) and the **freeing of the session**
(`rcp_libera()`). ⚠ The second is the safety net of all the others, and goes through the same
`rilascia_al_distacco()` with the same `inp_rilasciato` guard.

#### 6.3 ⛔⛔ AND THE SHOWCASE LINE ALWAYS SAID ZERO

`[M]` In all four detaches, one millisecond apart, the log said **two different things
about the same fact**:

```
13:42:55.042 rcp     ⭐ §7.3 — RILASCIO AL DISTACCO (congedo del client): 0 fra tasti e pulsanti
                        erano premuti e sono stati rilasciati
13:42:55.052 input   rilascio al distacco: 2 fra tasti e pulsanti (restano segnati 0 e 0)
```

⛔ **The zero was structural, not chance.** Whoever holds the map of pressed keys is the **child**, another
process; `webtransport.c` sent the request and answered `0` meaning *«it has gone out»*, and
`rcp.c` wrote it as *«zero were pressed»*. The comment in the code even said so — two
functions away from the one that printed.

> ⚠ **It is `LEZIONI.md` §1.9 in the worst place it could have.** The rule with the highest damage/cost
> ratio in the document had a single witness, and that witness **always** said «nothing was
> down» — i.e. **the face of green on a release that never happened**. A real defect in
> `input_rilascia_tutto()` would have been invisible to anyone reading that line.

✅ **Closed**: the hook has three answers instead of a number — the real count, `SENZA_CONTO`
(«asked, and the child knows the number: look for it there»), `IMPOSSIBILE` («⛔ it could not be asked: if
something was pressed, it stays pressed»). `[M]` Remeasured after the cure:

```
13:54:24.166 rcp     ⭐ §7.3 — RILASCIO AL DISTACCO (congedo del client): richiesta MANDATA al
                        palco.  ⚠ Questa riga NON porta il numero, perche' chi lo sa e' il figlio…
13:54:24.172 input   rilascio al distacco: 2 fra tasti e pulsanti
```

### 6-bis · ⛔⛔⛔ THE SILENCE CLOCK COUNTS THE WRONG THING

*Found by chance on 16 Aug, while testing §7.3: **twice in a row the key released
by itself before I cut the wire**, and the reason was not §7.3.*

`SPECIFICHE.md` §5.3 keeps **three separate clocks, each with its own meaning**:

| clock | how long | what it measures |
|---|---|---|
| **client silence** | 30 s | *«un client che tace è un client che si è staccato»* — ⭐ and the paragraph says **why**: *«i 30 secondi coprono solo le interruzioni vere»* |
| **user inactivity** | 30 **minutes** without input | *«chi resta mezz'ora a guardare un video senza toccare nulla viene staccato»* |

⛔ **Today the product has confused them**: `rcp.c` measures `ultimo_byte`, i.e. the last **RCP** byte
arrived from the client — and a client that watches and does not touch **sends nothing**. ⇒ Thirty seconds
without touching the keyboard count as «the client has disappeared».

`[M]` **The measurement, with the browser, and the expectation declared beforehand:**

| | |
|---|---|
| `13:46:27.968` | `sessione aperta utente=prova via=[192.168.0.3]:53805` |
| ⛔ `13:46:57.980` | `STACCATO per silenzio: 30013 ms senza un byte` — **seats occupied now: 0** |
| ⭐ **and the connection was alive** | for **111 seconds** QUIC said nothing: no `trenta secondi di silenzio (§2.2)`, no closure |
| ⭐ `13:48:19.750` | a single key: `posto RIPRESO … dopo il silenzio`, **same connection `:53805`**, no new `sessione aperta` |

⇒ ⭐⭐ **The two clocks measured the same thing and gave opposite answers.** In the real cut
of the wire, QUIC declared the silence at `13:33:43` — **exactly 30 s after the cut at
`13:33:13`**, i.e. right. RCP had declared it at `13:33:07`, **36 seconds earlier and for no reason**.

#### ⛔ And the price gets paid, measured

`[M]` First tab in and still (no input); after 30 s the seat shows as free. **Second
tab, same user:**

```
13:49:57.274 rcp  posto PRESO da prova via [192.168.0.3]:54839 (occupati adesso: 1)
13:49:57.332 rcp  ⛔ [192.168.0.3]:53805: tela in vigore 2544x926 ma il fotogramma catturato e'
                     1552x568 — NON lo spedisco (§6.2)
```

⇒ **The second device got in and took the desktop of the first, which was alive and connected.**
And the first tab **froze**, because the newcomer resized the stage.

⛔ It is invariant **I2** broken **in the case that `RCP.md` §8.2 names in writing**:

> *«Chi viene rifiutato è chi arriva, non chi c'era. Nessun client attaccato e vivo viene mai
> spodestato da un altro.»* · *«Un client silenzioso da 30 secondi non è più attaccato, quindi non
> occupa niente e il nuovo entra. Un client **vivo** occupa, e il nuovo è rifiutato. ⛔ Il discrimine
> è l'orologio del silenzio»*

⚠ The discriminant is there, and it is the right one. ⛔ **It is the clock that is calibrated on the wrong thing.**

#### ⭐ The cure, and it does not touch the protocol

The right sign of life **already exists and works**: it is the QUIC packet. `trasporto.c` has its own
clock (`NGTCP2_ERR_IDLE_CLOSE`, the 30 s of §2.2) and in the cut test it answered **to the
second**. ⇒ It is enough for §5.3 to look at **the last packet arrived from that peer** instead of the last
RCP byte.

| | |
|---|---|
| **what is touched** | `s->ultima_vita` in `rcp.c` next to `ultimo_byte` (**two fields, two clocks**) · `rcp_segno_di_vita()` · the bridge `wt_segno_di_vita()` · the call in `trasporto.c` after `ngtcp2_conn_read_pkt()` |
| ⭐ **what is NOT touched** | **the protocol**: no new message, no heartbeat to add to the page, `RCP.md` unchanged. ⚠ And `rcp.c` has a twin identical byte for byte in `banchi/rcp/` |
| ⛔ **and ONLY if `rv == 0`** | the packet must be **decrypted and authenticated**: any UDP datagram is not enough, or anyone could keep someone else's seat occupied by sending packets with their address |
| ⚠ **the case not to break** | the tab **frozen** by the browser after ~5 minutes in the background (§5.3 names it): a frozen tab also stops answering QUIC ⇒ the two clocks stay in agreement, the seat is freed all the same |

#### ✅ DONE, and the cross-check has three points — 16 Aug 2026

⛔ **Two out of three were not enough**: had I tested only that the seat is not lost, I could have
**switched off** the clock instead of repairing it. The third point is the positive control.

| | the expectation, declared beforehand | `[M]` |
|---|---|---|
| 1 | I log in and **touch nothing for 90 s** ⇒ no detach | ✅ `occupati: 1` at +15/30/45/60/75/90 s, zero detaches (before, it detached at 30 s) |
| 2 | **second tab** while the first is alive and still ⇒ **rejected** | ✅ `posto NEGATO a prova … lo occupa un altro client di questo stesso utente` · `congedo motivo=0x0f` |
| 3 | ⛔ **I cut the wire** ⇒ the seat is **really** freed, and at a clean 30 s | ✅ `STACCATO per silenzio: 30015 ms senza un PACCHETTO … e l'ultimo byte di RCP è di 66695 ms fa` |

⭐ **The new line carries both numbers**, and it is the difference in a single line: 30 s without
packets *versus* 66 s without the user touching anything. Before, it would have been the second number
throwing the user out.

#### ⚠ And what the cure rests on, written instead of hoped

⛔ **The repair has an assumption**: that less than 30 s pass between one packet and the next. Nobody
guarantees it — the transport's PINGs are on **only** in the credentials window, and for a
written reason (`webtransport.c`, `regola_tienila_viva()`: keeping them always on would change the
meaning of the 30 s of §2.2). During the session packets arrive because **something moves**
— frames, cursor, acknowledgements — and on a still scene it is not certain that things move often enough.

⇒ ⭐ **So the assumption watches itself**: `rcp_segno_di_vita()` writes in the log when
the gap between two packets exceeds **half** the cap.

> ⛔ **And it is the morning's lesson applied to its own cure**: a protection that rests on
> something nobody can look at is the protection found broken by a user thrown out
> while reading.

#### ⛔⭐ AND THE SURVEILLANCE SPOKE ON THE FIRST RUN

`[M]` Session still for **260 seconds**, nobody touching anything. ✅ The seat held for all
260. ⛔ **But the margin line appeared 8 times**, and the number is striking for how
regular it is:

```
15:31:00.007  ⚠ §5.3: fra due pacchetti sono passati 15004 ms, e il tetto è 30000
15:31:30.016  ⚠ §5.3: fra due pacchetti sono passati 15005 ms, e il tetto è 30000
15:32:00.019  ⚠ §5.3: fra due pacchetti sono passati 15002 ms, e il tetto è 30000
```

⇒ **Exactly fifteen seconds.** A number that precise is not traffic: it is **a keep-alive**, and ⛔ **it is not
ours** — our PINGs in that window are off. It is the browser.

⚠ **So the margin is 2×, and it depends on Chrome's courtesy.** A different browser, or Chrome
changing that number, and the seats start dropping again under the nose of whoever is reading.

> #### ⛔ THE DECISION THAT COMES OUT OF IT, and I do not take it alone
>
> **The real cure**: turn on the transport's PINGs **also with the session active**, so the sign of
> life is produced by the server on a clock of its own instead of hoping in the browser's. ⭐ It costs one
> line in `regola_tienila_viva()`.
>
> ⚠ **But the reason they are off today is written**, and must be looked at closely:
>
> | the objection written in `webtransport.c` | does it hold? |
> |---|---|
> | *«Tenere viva la connessione SEMPRE cambierebbe il significato dei 30 secondi di §2.2»* | ⭐ **No, for the DEAD client**: RFC 9000 §10.1 restarts the timer when one **receives**, not when one sends. A dead client does not answer our PINGs and dies all the same — and the comment itself says so, two lines further down |
> | ⛔ **but it holds for the FROZEN tab** | `SPECIFICHE.md` §5.3 promises that a tab put in the background and frozen by the browser after ~5 minutes **goes silent, so it detaches**. If the browser's network service keeps answering our PINGs while the page is frozen, that promise falls: the seat would stay occupied by a zombie |
>
> ⇒ ⏳ **And the question can be measured instead of argued**: *does a background tab, frozen,
> still answer QUIC?* Six minutes of testing with the browser. ⛔ If it answers, then the promise of
> §5.3 about the frozen tab **is already false today** — because those 15 seconds arrive all the same — and the
> decision changes shape.

#### ⛔ The measurement was made, and the answer is «I DON'T KNOW» — and the counter says so

`[M]` 16 Aug, tab in the background for **8 minutes and 30 seconds**, never touched.

| | |
|---|---|
| ✅ detaches for silence | **zero**, the seat held for all 8 minutes |
| ✅ the packets | punctual: `15003 · 15018 · 15006 · 15001 · 15002 ms` to the last |
| ⛔ **was the tab frozen?** | **NO** |

⭐ **And the answer to this last row is worth more than the first two**, because without it I would have come out with a
false conclusion. In the page a counter was armed that beats once a second:

```
battiti: 542   ·   attesi se MAI congelata: 544   ·   JS fermo da: 0 s
```

⇒ ⛔ **542 out of 544**: the tab's JavaScript ran at full speed the whole time — **it was not
frozen, and not even slowed down** (a normal background tab gets its timers
throttled to one a minute: there would have been ~9, not 542).

⚠ **The reason is the tool**: Chrome **does not freeze a tab under automation** — the debugger
attaches and detaches at every command, and this exempts it. ⇒ The test measured *a hidden tab*,
not *a frozen tab*, and **they are two different things**.

> ⭐ **It is `LEZIONI.md` §1.9 rule 2 that pays for the ticket**: the positive control — *«questo
> strumento sa distinguere il caso che mi interessa?»* — cost three lines of JavaScript and
> prevented writing «the frozen tab answers QUIC» from a test in which **no tab ever
> froze**.

⏳ **So the question stays open, and automation cannot close it**: a human being is needed who
opens the page in a normal browser, switches to another tab and leaves it there **ten minutes**. The
server log says all the rest by itself — if `STACCATO per silenzio` appears, the promise of
§5.3 holds and always-on PINGs would break it; if it does not appear, the promise **is already false today**.

#### ✅ THE USER CLOSED IT, and the promise of §5.3 does not come true

`[M]` 16 Aug 2026, the user's browser, **with no automation attached** — i.e. in the condition in
which Chrome really freezes. Tab in the background for **eleven minutes**:

```
15:54:38  posto PRESO da prova
   …      nessuno stacco, nessun congedo, nessun silenzio di QUIC
16:04:30  ⚠ fra due pacchetti sono passati 15002 ms
16:05:30  ⚠ … 15002 ms
16:06:00  ⚠ … 15002 ms
16:07:25  posto LASCIATO   (l'utente chiude la scheda: congedo pulito)
16:07:55  quic: trenta secondi di silenzio, staccato (§2.2)
```

⇒ ⛔ **The background tab does not stop answering**, and the 15 seconds arrive punctually well
beyond the five minutes of freezing. The line of `SPECIFICHE.md` §5.3 — *«una scheda congelata
tace, quindi si stacca»* — is `[S]`, a **prediction** about the behaviour of browsers, and the measurement
refutes it.

⚠ **What this measurement does NOT prove**, declared: it does not prove that the tab *was* frozen — inside
the user's browser one cannot look. ⭐ But for the decision nothing changes: **frozen or
not, it answers**.

#### ✅ DONE: the PINGs stay on for the whole session

`regola_tienila_viva()` turned the PINGs on only in the credentials window. Now it keeps them
on until the session is `finita`.

| the objection that kept them off | why it fell |
|---|---|
| *«cambierebbe il significato dei 30 secondi di §2.2»* | ⛔ **it had already changed, and not because of these PINGs**: since §6-bis the clock counts **packets**. «The client is there» already means «it answers on the wire» — the PINGs do not add that semantics, they make it **reliable** |
| *«la scheda congelata deve staccarsi»* | ⛔ measured: **it does not detach**, eleven minutes |
| ⚠ **the price, declared** | a client with the **page** dead and the **network** alive keeps the seat. ⭐ But it kept it already, and whoever comes back to that tab finds their session again (I4). What stays uncovered is only the client that stops answering **on the wire too** — and that one detaches at thirty seconds as always |

⭐ **And the acceptance yardstick is the margin line**: with PINGs at 10 s the gap between two packets
cannot exceed 15, so *«il margine si sta assottigliando»* **must never appear**.

`[M]` **Measured, and the positive control is the second row:**

| | expected | seen |
|---|---|---|
| three minutes still | zero margin lines, seat held | ✅ **0 margin lines** (before: one every 30 s), zero detaches |
| ⛔ **wire cut** | the seat is freed all the same: PINGs do not keep a dead one alive | ✅ cut `16:13:26`, detached `16:13:50` |

⭐ **And the detach line carries the whole repair in one sentence:**

```
16:13:50  STACCATO per silenzio: 30701 ms senza un PACCHETTO — e l'ultimo byte
          di RCP e' di 238832 ms fa
```

⇒ **Thirty seconds** without packets versus **four minutes** without the user touching anything.
This morning it would have been the second number throwing them out.

⭐⭐ And the two clocks now **agree**: `rcp` at `16:13:50`, `quic` at `16:14:00` — ten
seconds apart. ⛔ This morning they diverged by **36 seconds, and in the wrong direction**.

### 6-ter · ⛔⛔ AND THE CANVAS BENCH HAS BEEN RED SINCE YESTERDAY, and nobody had noticed

*Found on 16 Aug while checking that the clock repair had not broken the in-process
benches. ⭐ Nothing had broken it — it was already broken.*

`banchi/04-b31-tela.c` mounts **bare** `rcp.c` with a fake stage: **18 cases, each with the expectation
declared beforehand**. §04-si-comanda calls it the canvas bench, and
`fasi/rapporti/F5-IN-0-mandato.md` cites it among those to keep green.

`[M]` Rebuilt by hand on seven versions of `rcp.c`, one per commit:

| commit | outcome | |
|---|---|---|
| `c7c57e5` | 17 / 0 | *«La tela del server prende la misura del client»* |
| `2e061f6` · `a4c26fa` · `bbc93a2` | ⭐ **18 / 0** | |
| ⛔ `477d708` | **11 / 7** | *«La tela era sbagliata dal primo istante»* — **the cure of the tail of the times, yesterday** |
| `26d463c` · `d32cda6` | 11 / 7 | today, identical ⇒ **it is not from today** |

⇒ ⛔ **Seven cases out of eighteen have been red since yesterday**, and the bench was not rerun after the cure.
⚠ The fallen cases are 6, 9, 10, 17 and three others: all around the **granted size** — which is
exactly what `477d708` changed, introducing the declared fallback of §4.5 *«concessa la
tela del palco»*.

#### ⭐ The diagnosis, done: **a single cause**, and the product is right

`[M]` All seven reds have **the very same gap**: `richieste al palco` is **exactly
one more** than expected.

| case | expected | seen |
|---|---|---|
| 1 · 6 · 9 · 10 | requests to the stage **1** | **2** |
| 2 · 5 · 17 | requests to the stage **0** | **1** |

⇒ ⭐ **It is the BIRTH request**, the one `477d708` added on purpose and that the log
declares at every session: *«§4.5: dico al palco che la tela di questa sessione è NxM — così nasce
già così invece di nascere a una misura sua e doverla cambiare (e il cambio è una gara)»*.

⚠ And the «TELA usciti 0» of cases 1, 6, 9, 10 **is not a second defect**: those cases are written
`bene = …; if (bene) { palco_consegna(…); … }`, so once the first condition falls the second half
**is never executed**. A single defect, seven faces.

⇒ ⛔ **The expectation is old, the product is right** — the **fifth** time in two days that a bench
measures itself.

#### ✅ Repaired — and **not** by adding one

⛔ Adding one would have been the wrong move: the bench would have gone back to green and **blind exactly
to the thing that had made it red**. The day the birth request disappeared — that is, the
seventeen seconds of tail came back — the sums would add up all the same. ⇒ Two moves instead of one:

1. the seven cases count **from after the birth** (`dopo_la_nascita()`), which tells the reader that the
   birth exists and is a different thing. And the outcome line names it: *«richieste al palco 2 (di cui 1
   alla nascita, §4.5)»*;
2. ⭐ **case 19 tests the birth on its own**: *«UNA richiesta al palco già con l'`ATTACCA`, a
   1600x900»*.

⭐ **And the repaired bench was certified before trusting it** (`CODER.md` §3.3). `[M]` With the fault
injected — the birth request removed from the product:

| | |
|---|---|
| the **18 old cases** | ⛔ **all eighteen GREEN** — the blindness was real, not hypothetical |
| **case 19** | ✅ **red, and only it** |

⇒ ✅ **19 out of 19**, and the fault went into `04-b31-certifica.sh` as **G12**, which demands red
on exactly case 19.

⭐ **And the process lesson is independent of the outcome**: the strongest bench we have on `rcp.c`
stayed red for a whole day because **nobody runs it**. It costs two seconds:

```sh
gcc -O1 -std=gnu11 -w -D_GNU_SOURCE -o /tmp/b31 banchi/04-b31-tela.c src/rcp.c && /tmp/b31
```

### 6-quater · ✅ THE SESSION WITH NOBODY WATCHING — 16 Aug 2026

*In v1 this was the case that broke: the virtual monitor disappeared on detach and `libmutter` hit a
failed assertion. It is point 6 of §2.*

**The expectation, declared beforehand**: (1) the graphical session stays alive and keeps its PID; (2) ⛔ zero
assertions in `mutter.log`; (3) with nobody watching, zero frames and CPU close to zero — ⚠ *if
the child kept capturing for nothing it would be a waste nobody would see*; (4) on
reattach everything is found again.

#### `[M]` Two minutes with nobody attached

| | |
|---|---|
| **child** | **2 ticks in 120 s** ⇒ ~0,017 % of one core |
| **gnome-shell** | 33 ticks ⇒ 0,27 % |
| **frames sent** | **0** |
| **new lines in `mutter.log`** | **0** — ⭐ the v1 defect is not there |
| child · gnome-shell · terminal | all three **alive** |

⭐ **The comparison that gives the number its meaning**: with a client attached and the scene still, the child
uses **0,63 ticks per second**; with nobody, **0,017**. ⇒ **37 times less**: the capture loop
really stops when nobody is watching, it does not spin idle.

⭐ And the child is not silent: every 60 seconds it writes *«"prova" ricontrollato: uid 1001, pid 476758, padre
476313, 40 descrittori — il legame regge»*. A session that nobody watches **says it is alive**.

#### `[M]` The reattach

| | |
|---|---|
| `gnome-shell` | **390241** — the same across a server restart, a detach from a cut wire, the two minutes of nobody and **three** reattaches |
| graphical session starts | **0** ⇒ it is a reattach, not a new login: the user lost nothing |
| first frame | **KEY `0x0301`**, as §5.2 demands |
| the canvas, looked at in the pixels | **1113 distinct colours**, mean brightness 102 ⇒ not black, not flat |
| the input | ✅ an `Invio` held 200 ms ⇒ **18 keystrokes** reached the terminal, and `cl_tasti_premuti` empty afterwards |

⏳ **What this test does NOT cover, declared**: the window is **two minutes**, not hours.
⇒ The clock of the **6 hours of abandonment** remains to be tested, and it is the last of the three of §5.3.

⚠ And `mutter.log` contains **7 `CRITICAL` lines** that are not ours: they are all at 13:18 and 13:19, from
two `gnome-shell` **that were shutting down** (*«has been already disposed»*), i.e. GNOME
teardown noise at logout. None from the live session.

### 6-quinquies · ✅ THE 30-MINUTE INACTIVITY — and how to test a long cap without waiting for it

> *«30 minuti di inattività va bene testare, ma le 6 ore proprio no, significa tenere il PC occupato
> 6 ore»* — the user, 16 Aug 2026.

⭐ **And the constraint improved the work**, because the answer was already written in `SPECIFICHE.md`
§5.3: *«il secondo e il terzo sono **configurabili**, con quei valori come predefiniti»*. ⇒ Two
checks instead of one, and neither keeps a machine busy:

| what | how it is tested |
|---|---|
| **the mechanism** | at short values: `riavvia-7700.sh --inattivita-s 10` |
| **the number in force** | ⭐ it is **read**, because the server writes it at startup |

```
⭐ §5.3, i tre orologi in vigore: silenzio del client 30 s (fisso) ·
   inattivita' dell'utente 1800 s · abbandono della sessione:
   ⛔ NON ANCORA IN VIGORE, nessun codice lo conta
```

⛔ **Without that line nobody would ever verify the default value**, and it is form E1
(«scritto non è in vigore») — the same one that cost dearly twice this morning.

#### ⛔ And `RCP_INATTIVITA = 0x02` was exactly that: declared and never used

`rcp.h` had the reason of §8.2, `RCP.md` §8.2 documented it — and **there was not one line of code that
sent it**. A farewell reason that another implementation would have had to handle for nothing.

#### `[M]` The two tests, with the expectation declared beforehand

| | expected | seen |
|---|---|---|
| I log in and **touch nothing** | farewell `0x02` at ~10 s, and the page goes back to the form | ✅ `16:31:13 INATTIVITA': 10048 ms (tetto 10000)` · `congedo motivo=0x02` · the page went back to the login form |
| ⛔ **positive control**: one key every 4 s for 32 s | **zero** triggers while working | ✅ input at `16:34:23 · 27 · 31 · 36`, zero triggers; then `16:34:46.979`, **10051 ms after the last one** |
| the graphical session | stays (I4) | ✅ `gnome-shell` 390241, terminal open, **0** starts |

⚠ **And the first draft of the positive control measured itself** — the sixth time in two days.
The stimulus was a synthetic `mousemove`, and **nothing reached** the server: the session dropped
for inactivity and it looked like a product defect. ⭐ The log refuted it before I wrote
the conclusion: `input id=` **zero**. ⇒ Redone with a key — a stimulus already tested end-to-end
today — it passed.

#### ⛔ The page said the wrong thing for `0x02`

The text was *«silenzio troppo lungo: la sessione è scaduta»*, i.e. **the other clock**: the silence
lasts thirty *seconds* and sends no farewell. ✅ Now it says *«sei stato mezz'ora senza toccare
niente: per rientrare servi tu, con la tua parola d'ordine — i programmi sono rimasti aperti»*, and
⭐ **goes back to the login form** as §5.3 demands (*«per rientrare servono utente e password»*):
before, only `0x10` did that, and the inactive user was left in front of a frozen desktop.

#### ⏳ The third clock, and why the 30-minute run is not done

⛔ **The 6-hour abandonment does not exist yet**, and the server **declares** it instead of keeping quiet.
⚠ When it is done, on expiry it **closes the session**: the open programs go away. §5.3 says so,
but it is the consequence to keep in front of one's eyes.

⭐ **And not even the real 30-minute run is done**, with the reason written down: the mechanism is tested, and
the only thing a half-hour run would add is that `1800000 ms` are thirty minutes — which is
arithmetic, not a measurement. ⇒ *A cap is tested on the mechanism and read on the number.*

### 6-sexies · ✅ DETACH AND REATTACH TWICE IN A ROW — 16 Aug 2026

> *«Un banco che passa solo da macchina pulita non è un banco, è una dimostrazione»* — the mandate,
> point 5 of §2.

⇒ So **five rounds, of two kinds**: three with a **clean** detach (the tab closes, farewell
`0x10`) and two with a **dirty** detach (the wire cut, detach for silence of §5.3).

**The expectation, declared beforehand**: the rounds must be **indistinguishable from each other**, and ⛔ *nothing must
accumulate* — that is the way this stuff breaks the second time.

#### `[M]` The three clean rounds

| | round 1 | round 2 | round 3 |
|---|---|---|---|
| ms to the desktop | 1430 | 1318 | **1164** |
| first frame | KEY | KEY | KEY |
| **child's descriptors** | **41** | **41** | **41** |
| `gnome-shell` | 390241 | 390241 | 390241 |
| keystrokes reaching the witness | +18 | +18 | +18 |
| keys left down | 0 | 0 | 0 |

⭐ And the times **go down** instead of up: 1430 → 1318 → 1164 ms.

#### `[M]` The two dirty rounds — the wire cut

| | cut A | cut B |
|---|---|---|
| detach | `30492 ms senza un PACCHETTO` | `30939 ms` |
| descriptors, before and after | 41 → 41 | 41 → 41 |
| following reattach | ✅ 1245 ms, 894 colours | ✅ 2007 ms, 894 colours |

#### ⭐ The balance, over all six attaches

| | |
|---|---|
| first frames, and how many were **KEY** (§5.2) | **6 out of 6** |
| graphical session starts | **0** — no round is a new login |
| stage teardowns | **0** — the stage survives all the detaches |
| child's descriptors | **41**, always |
| `gnome-shell` | **390241**, always |

#### ⛔ And the defect that turned up was MINE, the seventh time in two days

Cut B, the first time, **did not detach**: the seat stayed occupied and it looked like a big
defect — *«il server non fa scattare i suoi orologi quando l'uscita è bloccata»*.

⭐ **Arithmetic refuted it, before I wrote the conclusion.** Around cut A I had put
a safety guard, `(sleep 100; nft delete table) &`. Cut A at `16:42:53`; +100 s =
**`16:44:33`** — the exact instant at which the `NON spedito` lines stop in the log. ⇒ The
guard of cut A **put the wire back nine seconds into cut B**: B lasted 9 seconds,
not 40, i.e. under the cap.

⚠ **And the second draft killed itself**: `pkill -f "sleep 100"` killed the script that
contained it, because that text was in its own command line. ⇒ No guards in
the background: **`trap ... EXIT INT TERM`**, which removes the cut whatever happens.

> ⭐ Redone clean, cut B detached at `30939 ms`. **No product defect** — and the
> rule remains the one of `SPECIFICHE.md` §5.9: *when a bench is red, the first thing to suspect is
> the expectation* (or the tool).

### 6-septies · ✅ THE THIRD CLOCK — 60 minutes without input, tested at 20 seconds

*Decided by the user on 16 Aug 2026 (`DECISIONI.md` §4.8), and tested right away: «procedi con il tetto
dei 20 secondi».* ⭐ It is exactly the way to test a long cap without keeping a
machine busy — the mechanism at short values, the number read in the startup line.

```
17:22:53.004  ⭐ §5.3 — ABBANDONO: «prova» non tocca niente da 20065 ms (tetto 20000)
17:22:53.004  congedo motivo=0x03
17:22:53.011  rilascio al distacco: 0 fra tasti e pulsanti
17:22:53.011  ⭐ §5.3: la sessione e' ABBANDONATA — chiudo la sessione grafica
```

| | |
|---|---|
| the trigger | **20065 ms** on a cap of 20000 |
| `gnome-shell` | **shut down** |
| the page | back to the login form with *«la sessione è stata abbandonata»* |
| ⭐ the farewell `0x03` | sent **before** closing, as the normative order of §7.6 requires |

#### ⛔ And on the first round the log told TWO lies — the same illness as the whole day

| the line | why it was false |
|---|---|
| *«guardavano senza toccare niente **da un'ora**»* | the cap is **configurable**, and in that round it was **20 seconds**. «Un'ora» is true only with the default ⇒ a line asserting a number it does not know |
| *«⭐ §7.6: **l'utente ha chiesto** di USCIRE»* | ⛔ **nobody had asked for anything**: what closed it was a clock. The child wrote that sentence for *every* closure, because until this morning the only one asking it was §7.6 |

⭐ **Both cured**, and the second without adding a message to the internal protocol: the field
`a` of the envelope was free, and now it carries the **why** (`FIGLI_USCITA_UTENTE` /
`FIGLI_USCITA_ABBANDONO`). Remeasured, the lines say `20065 ms (tetto 20000)` and *«⚠ Non l'ha
chiesto nessuno: è scaduto il tetto»*.

> ⚠ **It is the third time in one day** that a log line asserts a cause or a number it does not
> possess — after `RILASCIO AL DISTACCO: 0` and the page's `0x02` text. ⇒ It is not bad luck: it is that
> **a line written when only one caller existed becomes false at the second one**, and no
> compiler says so.

### 6-octies · ⭐⭐ THE TEST THAT COUNTS, AND THE USER DID IT — with real work inside

*All the tests of this day had an **empty** desktop. ⛔ And an empty desktop is the worst possible
witness for the question «did the session survive?»: freshly reborn it is identical to how it was.*

The user, on 16 Aug 2026, in their own words:

> *«Mi sono loggato con la finestra del browser massimizzata e ho lanciato un task nel terminale (un
> ciclo infinito), poi ho chiuso il browser. Ho ridimensionato a finestra il browser, mi sono
> ricollegato e il task nel terminale era ancora in esecuzione.»*

`[M]` The log, line by line:

```
17:30:13.541  posto LASCIATO da prova            ← chiude il browser: e' un DISTACCO
                                                   ⛔ nessun «USCIRE», nessun «avvio la sessione»
17:30:36.535  posto PRESO da prova
17:30:36.535  ⚠ RIPIEGO §4.5: chiesta 1240x622, il palco ha 2544x926 — e SOPRAVVIVE al client (I4)
17:30:36.635  ⭐ tela IN VIGORE cambiata a 1240x622        (+100 ms)
```

`[M]` And the real witness, which none of my tests had:

```
PID 523560   ELAPSED 02:31   %CPU 20.8   cat /dev/urandom
```

⇒ **The user's work had been running for two and a half minutes, across a detach of twenty-three seconds and
a size change.** Had the session died, it would have died with it.

⭐ **In a single test it closes three**: invariant **I4**, the **reattach at a different size**, and — the
only one that really counts — **the scene on which this phase is judged**: *«chiude il client, va a pranzo,
riapre, e ritrova tutto com'era»*.

#### ⚠ And the distinction that had made the user suspicious, because it will fool the next one too

The user had written: *«guarda che la sessione non è stata distrutta»*. ⭐ **They had seen a true
thing** — but there are **two** different things both called «session»:

| | what it is | fate |
|---|---|---|
| **the user manager** — `user@1001.service`, logind `8799`, `Class=manager` | the *linger*: the bus, `/run/user/1001`, the user services | ⭐ **never dies**. `[M]` active since 13:13, hours before. **It is deliberate**: it is the cure that brought the session bus from **2,6 s to 18 ms** |
| **the graphical session** — `gnome-session`, `gnome-shell`, logind `Class=user` `remotix` | the desktop, and the programs inside | ⛔ **this one** dies: at logout, and when the abandonment expires |

⇒ Whoever looks at `loginctl` or `/run/user/1001` after a closure **sees something alive and concludes that
nothing happened**. ⛔ The only witness that does not deceive is the **process number** of
`gnome-shell`, or a user program that was there before.

### 6-novies · ✅⭐ THE SECOND DEVICE IS REJECTED — tested from Android, 16 Aug 2026

*§05-la-sessione §1.4 declared that this path was tested **only on a fake guest**:
«non prova il filo». ⇒ Tested by the user with a **real phone**, another network, another engine.*

`[M]` Session active on the PC (`192.168.0.3`), attempt from Android (`192.168.0.24`):

```
17:50:00.664  ammesso utente=prova da=[192.168.0.24]      ← la parola d'ordine era GIUSTA
17:50:00.742  posto NEGATO a prova: lo occupa un altro client di questo stesso utente
17:50:00.742  congedo motivo=0x0f — «c'e' gia' un client attaccato», stato=attesa-attacca
```

| the expectation of `RCP.md` §8.2 | `[M]` |
|---|---|
| **first admitted, then denied** — or the phone would be told a lie about the password | ✅ `ammesso` and then `posto NEGATO` |
| reason **`0x0F`**, not a generic error | ✅ and `stato=attesa-attacca`: stopped **before** touching the desktop |
| *«chi viene rifiutato è chi arriva, non chi c'era»* | ✅ the PC's frames kept going out (`1571`, `1572`…) during the rejection; `occupati adesso: 1`, no `posto LASCIATO` |
| ⭐ **`0x0F` does not count as a failed attempt** (§4.4-bis: *«chi prova a riattaccarsi tre volte dal telefono si bannerebbe da sé»*) | ✅ **zero** attempts counted, no ban |
| and the sentence the user reads | ✅ *«quell'utente e' gia' collegato da un altro dispositivo»*, on the clean form |

⭐ **And the page goes back to the form**: it is the fix made ten minutes earlier (§6-decies). Without it,
`0x0f` would have produced the broken screen — i.e. a defect in place of a correct rejection.

### 6-decies · ⛔⛔ THE LOGIN FORM UNDER THE DESKTOP — three reports for one cause

*The user, three times, increasingly annoyed: «ho notato solo una sezione della finestra» · «devi
togliermi quella barra perché mi blocca tutto» · «ancora quella cazzo di barra del login? LEVALA!»*

⛔ **And the first two times I removed the wrong thing**, looking at the screen instead of the style
sheet: first the `⌨` shortcuts bar, then the diagnostics strip. ⚠ Both had to
go — the little `⌨` button sits 4 px from the bottom-left corner, i.e. where one goes looking for the
things of the **desktop**, and gets pressed while aiming at something else — **but they were not the cause**.

#### The cause

The «desktop dress» (`body[data-schermo="acceso"]`) did **four** things: no margin, the
canvas first (`order: -1`), black background, flexible column. ⛔ **And it hid nothing.**

⇒ Title, notice, **login form**, outcome and declarations stayed in the column **under the
canvas**. The white and black bands of the user's screenshot **were the form's fields** on a black
background, with the «Collegati» button below. The page became taller than the window: scroll
bar, half the desktop out of view, and the clicks of the bottom strip eaten.

⭐ **The rule was already written**, in the comment of `torna_al_modulo()`: *«chi accende uno stato è lo
stesso che deve saperlo spegnere; un ritorno che ripristina metà delle cose è peggio di un ritorno
che non c'è, perché sembra riuscito»*. ⛔ Nobody had read it **the other way round**: *whoever turns on the
desktop dress must hide what the desktop replaces.*

#### And a second defect found along the way, from the same symptom

```js
if (mot === 0x10 || mot === 0x02) torna_al_modulo();
```

⛔ The page went back to the form for **two reasons out of fifteen**. For `0x0c` (the server is shutting down), `0x03`
(abandoned), **`0x0f` (already connected elsewhere)**, `0x07`, and network errors, the page stayed
in the desktop dress with the form underneath. ⇒ Now **every** `CONGEDO` goes back to the form: the discriminant is not
the reason, it is the fact — *a finished session is re-entered from the form*.

> ⚠ **And the cost of my method, declared**: I restarted the server **twice while the user
> was testing**, throwing them out halfway (`congedo motivo=0x0c`), after saying I would
> ask. ⛔ A fix delivered on top of someone who is measuring is not a delivery: it is another
> variable in their measurement.

### 6-undecies · ⭐ THE MEASUREMENTS THAT WERE IN `SESSIONE.md`

> ⚠ *`SESSIONE.md` was dissolved on 16 Aug 2026: the outline went into `SPECIFICHE.md`
> §5.9, and **eleven** of its fourteen measurement sections were already here, item by item
> (§6…§6-decies) — 237 lines, thrown away because duplicated. ⛔ **These three were not**: they carry numbers that
> could not be found anywhere else, and I checked it number by number rather than by
> eye on the titles. They come in here because they are measurements of phase 5.*

### ⏱ The times, measured (16 Aug 2026, 20 rounds, integrated GPU)

| phase | median | p90 | max |
|---|---|---|---|
| login → session request | 244 ms | 300 ms | 301 ms |
| ⛔ request → stage mounted | **2907 ms** | 16969 ms | 17885 ms |
| stage → first frame | 84 ms | 89 ms | 91 ms |
| ⭐ **TOTAL login → desktop** | **3211 ms** | 17255 ms | 18158 ms |

⭐ **The typical round is 3,2 s**, and of these ~2,9 are `gnome-session` getting up: what we do
takes ~330 ms. ⛔ **The tail does not**: about one round in seven costs 13-18 seconds, and underneath is the
**open point** below.

### ⭐⭐⭐ TWENTY ROUNDS FROM THE REAL BROWSER — the measurement the user had asked for

*«Fai il login/logout almeno venti volte e misura esattamente i tempi» · «per i test usa il browser,
non il banco: è l'unico modo di misurare effettivamente quello che accade».*

`[M]` 16 Aug 2026, Chrome on this laptop → the server, twenty cycles **login → desktop →
`Ctrl+Alt+Fine` → confirm → login form**, without ever touching the bench.

| phase | median |
|---|---|
| birth of the child → canvas declared by the browser | 968 ms |
| canvas → start of `gnome-session` | 214 ms |
| start → stage mounted | 850 ms |
| stage → **first frame sent** | 45 ms |
| ⭐ **TOTAL, «Collegati» → desktop** | **2087 ms** |

⭐ **p90 2142 ms · minimum 1968 · maximum 2155.** ⇒ **187 ms of spread over twenty rounds**: no
spike, no slow round.

⭐ And the three things that were frightening are at zero:

| what | how many times |
|---|---|
| frames at a size different from the one requested | **0** (all 263 at `1552x532`) |
| «il palco non è alla tela in vigore» (the *dance*) | **0** |
| child stopped waiting without trying | **0** |
| clean `0x10` farewells | **21 out of 21** |

⚠ And the **fixed second** of admission is almost half the total (968 ms out of 2087): it is the defence against
brute force — without it, one would read **with a stopwatch** the difference between «l'utente non esiste» and «la
parola è sbagliata», which §4.4 forbids saying in words.

#### ⭐ And the worst case: the first login of the day

`[M]` Same test with the browser, but with **the graphical session never started** — no desktop in
memory, everything cold:

| | |
|---|---|
| birth of the child → canvas from the browser | 1074 ms |
| canvas → start of `gnome-session` | 229 ms |
| start → stage | 952 ms |
| stage → first frame | 98 ms |
| ⭐ **TOTAL cold** | **2353 ms** |

⇒ ⭐ **The worst reproducible case is 2,4 seconds**, not eighteen. ⚠ And the criterion is the user's:
*«se il tempo medio fra la parola d'ordine e la comparsa del desktop è circa 2 secondi va bene. Ma
non va bene se i secondi diventano 18»*.

### ⚠ What is still NOT in order, declared

- ✅ ~~The «Power Off» item stays in the menu~~ — **closed by the user on 16 Aug 2026**: *«il menù di
  sistema è corretto. L'utente non può spegnere, riavviare o mandare in standby la macchina»*.
  ⭐ **Three items out of four are gone** (Restart, Suspend, Hibernate) `[M]`, and the four actions are
  denied to whoever counts — asked **by the child, which is the real user**: `CanPowerOff = CanReboot =
  CanSuspend = CanHibernate = no`. ⇒ §4.7 asked that **nobody can power off**, and nobody can.
  ⚠ The item on screen remains, and whoever presses it gets refused by logind.
  ⛔ **And the cause this document attributed to it is REFUTED by a measurement**: it said «una cache di
  gnome-shell letta all'avvio». `[M]` The session of 17:13:07 on 16 Aug was born **long after**
  the polkit rules were in force, and the item is there all the same. ⇒ The real cause **is not established**,
  and it is not chased: the defect is cosmetic and the user judged it acceptable.
> ### ⭐⭐⭐ THE TAIL: FOUND, and it is the resize against a still scene
>
> `[M]` 16 Aug 2026, clean log and child finally **talkative** (see below). In a
> slow round:
>
> - frames sent: **only one, and at `1920x1080`** — i.e. at the **fallback** canvas, not the one
>   requested by the client (`2544x926`);
> - «TELA NUOVA DAL PALCO» lines: **zero** — the resize **never happened**;
> - and the loop said so: *«1 fotogrammi consegnati, **3538 attese a vuoto** (scena ferma: Mutter
>   consegna solo quando qualcosa cambia)»*.
>
> ⇒ ⛔ **The stage is born at the wrong canvas.** The child is spawned with `1920x1080` (the value
> of the children table) **before** the client declares its window, mounts the stage at that
> size, and sends a wrong key. Then `2544x926` arrives and a resize is needed —
> ⛔ **but on Wayland the resize completes only when the compositor delivers a
> new frame, and on a freshly born desktop nothing changes.** ⇒ One waits for something to move
> by itself.
>
> ⭐ **And this is the common cause of all the symptoms the user listed on 16 Aug**: black
> bands (frame at the wrong size), «desktop rotto», «nessun input» (the pointer region
> follows the canvas), «ci mette molti secondi». ⚠ B5 and B6 of this table already said it in words; the
> written cure (`rcp.c` §4.5, telling the stage the canvas) **arrives too late**, because the child has
> already mounted.
>
> ⇒ ⭐ **The cure**: the child does not give birth to the session nor mount the stage **until it knows the
> client's canvas**. ⚠ With a cap (`TELA_ATTESA_MS`), because I1 forbids standing still out of caution: if the
> client does not declare it, it starts with the fallback and **declares** it.
>
> ### ⭐⭐⭐ And the measurement, 20 rounds, before and after
>
> | phase | ⛔ before | ⭐ after |
> |---|---|---|
> | login → request | 244 ms | 1192 ms |
> | **request → stage** | 2907 ms · p90 **16969** | **900 ms** · p90 950 |
> | stage → 1st frame | 84 ms | 85 ms |
> | ⭐ **TOTAL to the desktop** | 3211 ms · p90 **17255** · max **18158** | **2164 ms** · p90 **2242** · max **2294** |
> | frames at the wrong size | 1 out of 1 at `1920x1080` | ⭐ **none**: all at `2544x926` |
>
> ⇒ ⭐ **Median −33%, p90 −87%, maximum −87%.** And the twenty rounds lie between **2067 and 2294 ms**: the
> total spread is **227 ms**, i.e. the time to the desktop is now a *number*, not a range.
>
> ⚠ `login → request` grows from 244 ms to 1192 because now the **fixed second** of admission
> is on the critical path: the session cannot be born before the client is admitted and has
> declared the window. ⭐ And it is paid back with interest by the next piece.

- ⛔⛔ **THE TAIL: one round in seven costs 13-18 seconds** — ⭐ **cause found**, see the box
  above. What remains here is the diary of how we got there, which is worth more than the cause. `[M]`
  What was EXCLUDED by measurement, and each was a diagnosis that looked right:

  | hypothesis | how it was excluded |
  |---|---|
  | the wait that doubles (1→2→4→…→30 s) | ⭐ it was **true** and cured (see below), but the tail remains |
  | the user manager being reborn | cured with **linger**: bus 2,6 s → **18 ms** `[M]`, tail unchanged |
  | the 5 s poll to Mutter | cap lowered to 400 ms, tail unchanged; and `[M]` that cap never triggers |
  | a slow step inside `prendi_il_palco` | ⏱ the three stopwatches **are silent**: no step above 250 ms |
  | the child waiting instead of trying | ⏳ **no line**: it is not waiting |

  ⇒ ⚠ In the 17 seconds the child **writes nothing, does not wait and has no slow steps**: the three things
  together do not add up, so a piece of instrumentation is still missing. ⭐ **The suspect that
  remains**, and it is the only region not yet timed: the **mounting of the capture after
  `mutter_apri`** — `ATTESA_AVVIO_S 10` in `cattura.c` and `ATTESA_NODO_MS 10000` in `mutter.c`.
  Ten seconds plus the compositor's startup make exactly the seventeen.

  ⛔⛔ **AND THE REASON IT TOOK SIX DIAGNOSES IS ONE ONLY, and it is the worst possible:
  the child did not have verbosity.**

  `[M]` The child **is not a `fork`**: it is an `execve` of `remotix-figlio`. ⇒ It did not inherit the
  `--parlantina` flag, and **every `registro_dettaglio()` of `figlio.c` ended in nothing, silently,
  without an error.** ⚠ Half the instrumentation of that file never reached the log.

  ⭐ And it lied in the worst direction: hunting the tail, I concluded for hours that certain branches
  «never triggered» *because their line did not appear* — while they triggered all right. ⇒ It is form
  **E8** (`LEZIONI.md` §1.9) inside the very tool meant to unmask it: «non l'ha fatto» and «non
  me l'ha detto» with the same face.

  ⇒ *A diagnostic that is silent is not neutral: **it lies**.* And the first thing to verify on a
  tool is not that it tells the truth, it is that it **tells**.

- ⭐ **Cured**: the wait between one attempt and the next doubled up to 30 s **even while a
  client was looking at a still screen**. `[M]` The log: *«attesa in corso 30000 ms,
  nascita chiesta 0 ms fa»* — and the two numbers together say everything: it doubled, and the guard could not
  trigger because it arms only when the session turns out **dead**, while the slow rounds are
  precisely those in which the previous one **is still closing** (`State=closing`). ⇒ Now: if
  someone is watching, it retries every **200 ms**. p90 from 21,2 s to 17,3 s, and the 30 s spikes gone.

### 7 · The user's judgement

*(the phase closes here, not on a complete document)*

### ✅ CLOSED ON 16 AUG 2026 — authorised by the user

⛔ **One does not write a verdict the user has not given.** Below are their words, with the
date, and nothing else.

| when | what they said | about what |
|---|---|---|
| 16 Aug | *«Se il tempo medio tra l'inserimento della password e la comparsa del desktop è circa 2 secondi va bene. Ma non va bene se i secondi diventano 18»* | the timing criterion — `[M]` median **2087 ms**, worst cold case **2353 ms** |
| 16 Aug | *«Mi ritengo più che soddisfatto così»* | the times, after the measurement |
| 16 Aug | *«Il menù di sistema è corretto. L'utente non può spegnere, riavviare o mandare in standby la macchina»* | §1.1 and `DECISIONI.md` §4.7 |
| 16 Aug | *«Niente timeout delle 6 ore: se dopo 60 minuti non c'è traccia di input la sessione viene killata»* | the third clock — `DECISIONI.md` §4.8 |
| 16 Aug | *«Funziona»* · *«Il desktop copre per intero lo schermo»* | the reattach at a different size (§1.3) |
| 16 Aug | *«Il task nel terminale era ancora in esecuzione»* | ⭐ the scene on which the phase is judged (§6-octies) |
| 16 Aug | *«Possiamo considerare chiusa la fase 5?»* → **«procedi»** | the closure |

#### ⏳ What remains — cleaned up with the user's criterion

> ⛔ *«Se i punti non toccano il prodotto è solo rumore burocratico»* — the user, 16 Aug 2026.

⭐ **And they are right**, and this list was **cut** rather than defended. What was written here
and changed nothing was removed, not moved:

| removed | why it was not a debt |
|---|---|
| ~~«due strade di §7.3 su quattro»~~ | they all go through the **same funnel** (`rilascia_al_distacco` + `inp_rilasciato`), and the funnel is exercised twice. Covered by **construction**, not to be tested |
| ~~the three tails of phase 4~~ | we had been **moving them house for two phases**. If nobody does them they are not a list: they are a way of not deciding. ⇒ They stay where they were born, in §04-si-comanda |
| ~~«la latenza va rimisurata»~~ | it is not an open point: it is **a number we do not have**. It gets taken when a number is needed |

**This remains, and it is only two things:**

1. ⭐ **`0x05` — the user already has a LOCAL graphical session.** It is the only piece of product of the phase
   never brought out on a real scene: the bench tests it with fake sessions created by PAM, because nobody ever sat
   at the console of that machine. ⇒ It closes as `0x0F` closed:
   **with a person**, who logs into the local desktop and then tries remotely;
2. ⏳ **A bench for the pointer after the devices are replaced.** ⚠ It is not paperwork: on a
   geometry change `libei` destroys and recreates the absolute devices and **the old pointer stops
   working without an error** (`STUDI.md` §gnome §9). Today it was tested with the user's hands and passes.

#### ⭐ And the cure for the «bench nobody runs», which is the same objection

`[M]` `04-b31-tela.c` — 19 cases on the most delicate module — stayed **red for a whole day**
because nobody ran it. ⛔ A bench nobody runs **is** bureaucratic noise.

⚠ And the cure **is not a launcher**: of benches that judge themselves and run without a machine there
is **one**, and a script to launch one is the same bureaucracy under another name.

⇒ **It runs by itself, where one passes anyway**: `src/costruisci-in-contenitore.sh` compiles and runs it at
every build, in two seconds.

```
⭐ costruito: …/src/remotix
⭐ 04-b31 (la tela,  passati 19, falliti 0):
```

⛔ And it **does not stop the build**: the binary is there and may be useful. But the red shows — and that was the only
thing needed.

#### ⭐ The lesson of the day, in one line

> **A log line written when only one caller existed becomes false at the second one, and no
> compiler says so.**

`[M]` Three times in one day, on the most important protections we have: `RILASCIO AL DISTACCO: 0`
that could not say anything else; the page's `0x02` text that named the wrong clock;
*«l'utente ha chiesto di USCIRE»* said by a clock. ⇒ And it is the same form as `LEZIONI.md` §1.9,
which now has its **fifth rule**.

⚠ **And the corollary, paid seven times today**: when a test is red, the first thing to suspect
is **the tool** — the old expectation of the canvas bench, the `sleep 100` guard that put the
wire back inside the next cut, the synthetic `mousemove` that did not arrive, the filter on the timestamp
of a line that had no timestamp, the counter that revealed that Chrome does not freeze a
tab under automation.
