# Phase 16 — Stress and capacity

*⚠ Historical measures, on the machine of the time. With phase 18 (without ffmpeg) those that the change invalidated were removed — encoding without a card and colour conversion with swscale; those of encoding on the card and of the audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision.*

*Decided by the user on **25 Sep 2026**, afternoon, with phase 15 closed at zero defects. This
document fixes **before** the tests everything the campaign will do: the decisions, the setup, the
jobs, the measures, the thresholds. ⛔ The thresholds of §9 are approved before the campaign and **are not
touched afterwards**. The real tests start in a **new session**, from this document.*

---

## 1. The question

Phase 15 said: **REMOTIX works** (round 2: 329 PASS out of 329, 328 faults seen out of 328).
Phase 16 asks: **how much load does REMOTIX bear while continuing to work?**

- project limit: **16 concurrent users**, without per-user or per-session licences;
- it is not assumed that 16 hold: we look for the **last nominal level**, the levels of
  **degradation**, the possible **breaking point**;
- beyond 16 only as an **overload test**, classified separately, and never necessary;
- the result is a **property of the measured configuration** (desktop, card, commit,
  screen size, load), not a promise for every machine.

⛔ Phase 16 is **not** used to compensate for a functional defect: if a level shows a
defect that phase 15 should have seen, we go back to the suite.

## 2. The user's decisions (25 Sep 2026)

| | decision | why |
|---|---|---|
| **the client browsers run ON THE SERVER** | *«è inevitabile che la macchina di test dev'essere lo stesso server su cui gira remotix»* | the tablet is a bottleneck (graphics and Wi-Fi) and would falsify everything (`[M]` phase 15: in 4K the tablet loses frames, the server does not; the phone on 2.4 GHz lost 0.6 % of the packets) |
| ⇒ **separate accounts** | REMOTIX · sessions · browsers each measured on its own (§6) | the server does two jobs: it produces the desktops and watches them |
| ⇒ **the result is a LOWER bound** | «N utenti su questo server, **che intanto fa girare anche gli N browser**» | with separate clients the capacity would be equal or higher, never lower |
| **the session cap raised to 16** | today `--tetto-sessioni 10` (phase 10) would refuse the eleventh | it is raised for the campaign, declared in every recording, then put back; beyond 16 only in overload |
| **4K for everyone** | *«puntiamo al 4K, che è il valore a cui aspira Remotix»* | it is the specifications' size (`prove-in-4k`) |
| **the scale of sizes** | if 4K goes FAIL: **3K → 2K → Full HD** | see §8 |
| **YouTube 4K: 1 user in 4** | fixed rotation of the four profiles | see §5 |
| **two campaigns** | Intel UHD 770 integrated, then **AMD Radeon RX 6800 16 GB** | the RX 6800 must be mounted on the server; first it is tested with a single user (§11) |
| **the climb in steps: 1 → 4 → 8 → 12 → 16** (25 Sep, evening) | *«forse avevo esagerato»*: one user at a time cost 24–96 hours of machine | the breaking point is found all the same, precise to one user, with the search halfway (§6); only the user-by-user curve is lost where everything is green |
| **cap at 17 during the campaign** (25 Sep, evening) | choice 1 of two: at step 16 the short check (§7) is the 17th session, for ~70 s | the 16 users stay 16 and the load is the same as at the other steps; the 17th is only the check, declared at every level; at the end of the campaign the cap goes back to the default |
| **logging in the system journal** | `journalctl`, no systems of our own in its place | see §12 |

## 3. The preconditions — all satisfied on 25 Sep 2026

- phase 15 closed: user functions, detach/re-attach, re-entry, image, input, canvas and sizes,
  audio/video, network loss, paths, browsers (Firefox 140, Chrome 154) — **zero defects**;
- certified commit: `d121715` (tag `fase15-giro2-congelato`), binary `b1443a0b`; the new login
  page is `c5279e66` (264 PASS out of 264 in the tests that go through the form);
- ⚠ the campaign's commit will be **the one of the day** (with journald and the configurable cap
  already there): it is identified and the short regression suite is run **first** (§13).

## 4. The setup: the real path, all on the same machine

**automatic user → real browser (Firefox or Chrome) → browser API → WebTransport/HTTP3/QUIC
→ RCP → REMOTIX → real graphical session → real application**

| piece | how | why |
|---|---|---|
| **one compositor per user** | 16 `labwc` without a screen, each at 3840×2160, one per browser | `[M]` phase 15: a Chrome window covered by another stops drawing (snapshots hung for up to 17 min) — with 16 4K windows in the same compositor we would measure that |
| **the browsers** | alternating: odd users Firefox, even ones Chrome | the two engines served (`SPECIFICHE` §11.5) |
| **the users** | new tenants `c16uNN`, one per level, in the box of the desktop under test (`rete11-<desktop>`) | like the suite: born from zero, cleared out at the end |
| **the automation** | the input arrives **from the browser** (Marionette/CDP, real events), as in the suite; the applications are launched inside the session as the user | no fake client: the path is a user's |
| **the network** | local to the server (the browser connects to `192.168.0.2`) | ⚠ it does not measure the Wi-Fi: the real network is a separate matter (§15) |

**Who plays the users** (the user's proposal of 25 Sep: *«sub-agenti per simulare gli utenti che
si collegano a quel server»*, and the form chosen):

- every user is an **independent actor**: its own process, its own browser, its own compositor,
  its own clock — they start and work **in parallel and without synchrony among them**, like different
  people; no single director making them move in turn;
- the actor is a **program**, not an artificial-intelligence agent: an agent takes
  seconds to decide every gesture (the input's rate would become the model's, not a
  person's), never does the same thing twice (the climbs could not be repeated nor
  compared Intel/Radeon) and for 16 users × 3 hours would cost a great deal;
- the **realism** comes from the rate: pauses, order of actions and typing speed vary
  as in a person, drawn from a **seed** fixed per user — every climb is different inside
  and identical from one campaign to the next;
- **subagents** are used where they pay off: building the four jobs and the meters in parallel;
  and, during the campaign, one per session to **read the evidence** of a DEGRADED or FAIL level
  and look for its cause while the climb is stopped.

⛔ The Python client and the scripts that imitate a browser do **not** make load: they can only
help diagnose (§4 of the user's document).

## 5. The four jobs, and how they are distributed

The users enter **in steps** (§6); each one's job is fixed by its number and **does not
change** in any campaign:

| user | profile | what it does, in a cycle, for the whole duration |
|---|---|---|
| 1, 5, 9, 13 | **A — browsing** | a browser inside the session (the box's Firefox ESR) opens pages in turn from a fixed list (text, images, a long page that scrolls), clicks, scrolls with the wheel |
| 2, 6, 10, 14 | **B — file manager** | the desktop's file manager: opens folders, creates and deletes some in a test folder, opens and closes windows, changes view |
| 3, 7, 11, 15 | **C — terminal** | the desktop's terminal: commands with output (`ls`, `find`, `top` for a few seconds, a text file scrolling), typed from the browser's keyboard |
| 4, 8, 12, 16 | **D — YouTube 4K** | a YouTube video in 4K full screen, always the same (fixed in the execution plan), played in Firefox ESR inside the session, **for the whole climb** |

⇒ at 16 users: **4 4K videos** and 12 office jobs. ⚠ The video weighs on the same card that
encodes and draws: it is intended, it is real use. `[?]` Internet is needed from the server: `[M]` 25 Sep
reachable. If YouTube changes something underneath (ads, automatic quality), we fall back on
**a fixed local 4K video file**, declared — the choice is made in the execution plan and does not change
between campaigns.

## 6. The climb and the checks

**PREPARE → START → CLIMB TO THE STEP → 10 MINUTES → CHECK → RECORD → REPEAT**
on the steps **1 → 4 → 8 → 12 → 16** users (the user's decision, 25 Sep evening), or up to a
demonstrated real limit. The users of a step enter one after the other, each when the
previous one has its first frame (so birth under load is measured too).

1. box redone from zero, server on with the cap at 16, no other load on the server;
2. the first user and its job are started;
3. **10 minutes** of continuous work (the load is **cumulative**: whoever was there continues);
4. **check** (§7) in the last 2 minutes of the level;
5. it is recorded (§10), then we climb to the next step;
6. **at the last step (16) the level lasts 30 minutes**, not 10: it is the test of memory
   leaks at full load, which with sparse steps is no longer seen while climbing.

**The search halfway**: if a step goes FAIL (after the repetition of §14), we try halfway
between the last good step and the broken one, and narrow down until the last GREEN level is known
**precise to one user** (e.g. 8 good, 12 FAIL ⇒ 10; 10 good ⇒ 11; 10 FAIL ⇒ 9). Every level
of the search restarts from a clean box with its N users.

**Non-continuation rule**: if a check says **DEGRADED significant** or **FAIL**, we do not
climb automatically: the level is observed, documented, diagnosed, classified and
**repeated** under the same conditions (§14). The aim is not to reach 16 at any cost.

⚠ Duration: 5 steps (the last of 30 minutes) plus 0–2 search levels ≈ **1 hour 10 per climb**.
Four desktops × two cards ≈ **9 hours** of measures in the best case, ~35 with the whole scale (§8),
against the 24–96 of the one-user-at-a-time plan. They are done in blocks, at night too.

## 7. The check of every level

**The behaviour, measured in every session:**

| what | from where |
|---|---|
| the image updates | snapshot of every browser's canvas at intervals: it changes when the job changes; no long stall |
| frames painted, skipped, holes | the page's diary (`dipinti`, `video X→Y`, `salt`, `buchi`) — sent to the server every 5 s, it already exists |
| **input → frame delay** | what the product measures from its side (`SPECIFICHE` §3.2: **cap 50 ms**, target 40 ms), plus a probe from the browser of a sentinel user |
| input arrives | every job types and clicks: its effect is seen (text in the terminal, folder created) |
| the audio (D users) | the page's diary (`suonati`, `BUCHI`, `mancati`) |
| birth of a new user | time from login to the new user's first frame |
| **short functional check** | on ONE user per level, in rotation: login already done → input (F-004/F-007 reduced) → image (F-003 reduced) → clipboard (F-014) — the certified functions must stay up |
| errors | server log (RCP, WebTransport/QUIC, session), browser consoles, journal |

**The resources, per enclosure** (systemd cgroups: `remotix` · `sessioni` · `browser`):

| resource | measures |
|---|---|
| **processor** | total, per enclosure, per session; load average; processes and threads |
| **memory** | total, per enclosure, per session (PSS); growth within the level (a hint of a leak) |
| **graphics card** | engine usage (drawing, video: encoding and decoding) **per process**, from the kernel (`/proc/<pid>/fdinfo` drm-engine); frequency; temperature; throttling. Intel: `intel_gpu_top` (to be installed). AMD: amdgpu fdinfo, `radeontop` or `amdgpu_top` |
| **video memory** | RX 6800: VRAM used; Intel: shared memory |
| **network** | bytes received/sent per session (REMOTIX's QUIC log: `persi`, `spediti`, retransmissions) |
| **REMOTIX** | live sessions, refusals, encoder queues, frames dropped, «budget», birth times |

## 8. The scale of sizes

| step | screen size of every user |
|---|---|
| 4K | 3840×2160 |
| 3K | 3200×1800 |
| 2K | 2560×1440 |
| Full HD | 1920×1080 |

If a step reaches **FAIL with N users**, the next step **restarts from 1 user and
climbs back on the same steps** (§6): every size has its own complete and comparable curve. We go down until we reach 16
nominal or the scale runs out.

## 9. The thresholds — ✅ APPROVED by the user on 25 Sep 2026 (evening), now fixed

*Proposal of 25 Sep 2026. A high value of a resource **on its own is not a FAIL**: the
classification is born from behaviour, and the resources serve to explain it.*

| measure (per session, in the level's check) | **GREEN** | **DEGRADED** | **FAIL** |
|---|---|---|---|
| input → frame delay (product, p95) | ≤ 50 ms (the cap of §3.2) | 50–150 ms | > 150 ms, or input lost |
| frames skipped by the page | ≤ 2 % | 2–10 % | > 10 % |
| longest image stall with work in progress | ≤ 1 s | 1–3 s | > 3 s, or image still |
| holes in the video chain (keys requested) | 0 | ≤ 1 per minute | > 1 per minute |
| 4K video (D users): frames painted per second, **in proportion to the frequency of the chosen video** (f) | ≥ 0.8·f | 0.4·f – 0.8·f | < 0.4·f |
| audio (D users): audible sound | ≥ 99 % | 95–99 % | < 95 % |
| birth of a new user (login → first frame) | ≤ 5 s | 5–15 s | > 15 s, or refusal |
| short functional check | all PASS | — | one FAIL |
| session dropped, restart, RCP/QUIC error that detaches | none | — | any one |
| memory of the `remotix` and `sessioni` enclosures within the level, with stable work (the `browser` enclosure is **recorded** but does not classify: the cache of a browsing Firefox grows on its own) | growth ≤ 5 % | 5–15 % (it is flagged) | > 15 % and continuing (leak) |

**Which delay classifies** — `[M]` diagnosis of the evening of 25 Sep (xfce box, 1 user, terminal,
460 letters; evidence in `/media/REMOTIX/misure/fase16/diagnosi-eco/`). The page round trip
(key → frame that carries it) in 4K makes **45 / 54 ms** (p50/p95), but inside there is work that is not
ours:

| stretch (4K, p50/p95 ms) | | whose |
|---|---|---|
| the page sends the key → the terminal receives it | 4.9 / 8.7 | **ours** (limited by the child's 8 ms `poll`, `figlio.c` `MOVIMENTO_ATTESA_S`) |
| the terminal draws the echo | 10.2 / 16.6 | application |
| the compositor composes and copies it to us | 14.5 / 19.0 | compositor |
| conversion + encoding + sending → page | 14.0 / 14.9 | **ours** |
| decoding and drawing in the browser (outside the round trip) | Firefox 38, Chrome 3.4 | browser |

⇒ **Our piece** is ~19 / 24 ms, below the cap of 50. So, as §7 says («what the
product measures from its side») and the row below («product»): **the product's delay classifies**
= p95 of the per-second maxima of the child's line `TRATTO cattura → byte fuori` + 9 ms
(the constructive cap of the input stretch). ⚠ On the wlroots route that line counts the copy
twice (~4 ms more): it is on the prudent side and is not corrected during the campaign. The **page
round trip** (`giro_eco`, typing only) is **recorded** as the experience delay and does not classify.
Cure candidate for after the campaign: the parent's socket in the same `poll` as the child
(~4 ms p50, ~8 ms p95).

**The level** is GREEN if **all** sessions are GREEN; DEGRADED if at least one is DEGRADED and
none FAIL; FAIL if at least one is FAIL. **DEGRADED significant** = more than a quarter of the
sessions DEGRADED, or a single measure beyond half of the DEGRADED band.

## 10. What is recorded

Like phase 15, an **append-only log**, `banchi/16-stress/registro.jsonl`, one row per
**level** and one per **session in that level**:

`campagna` (e.g. `intel-4k-gnome`) · `livello` (1, 4, 8, 12, 16 and those of the search) · `utente` · `profilo` · `browser` and version
· `desktop` · `scheda` and driver · `misura` · `commit` · binary · page · kernel · `inizio` ·
`durata_s` · all the measures of §7 · `classe` (GREEN/DEGRADED/FAIL) · `ragione` · `evidenze`.

The **evidence** sits on the server in `/media/REMOTIX/misure/fase16/<campagna>/livello-NN/`: snapshots
of every canvas, the pages' diary, server log and journal cut to the level, the resource
series (one row per second), browser consoles. They must be enough to say **what was
happening** at the moment of degradation.

The **report** is generated from the log (like `15-rapporto.py`): the curve of every campaign, the
final matrix, the bottlenecks.

## 11. The two campaigns

| | Intel integrated | Radeon RX 6800 |
|---|---|---|
| card | Intel UHD 770 (i5-13500T) | AMD RX 6800, 16 GB |
| encoding | VA-API, iHD (`[M]` phase 11) | VA-API, radeonsi — ⚠ **never tested**: first a login with one user, to see that the AMD encoder really starts |
| order | GNOME, KDE, XFCE, LXQt | same order, same conditions |
| recorded | CPU, GPU, driver, RAM, kernel, distribution, browser, size, network, commit | same, plus VRAM |

⚠ The server has its root in RAM: mounting the card means a reboot, and the reboot loses
ssh key and packages (`riavvio-perde-la-chiave-ssh`) — the recipe is ready.

**The final matrix:**

| desktop | Intel iGPU | Radeon RX 6800 |
|---|---:|---:|
| GNOME | last GREEN level · breaking point · step | same |
| KDE | … | … |
| XFCE | … | … |
| LXQt | … | … |

Every cell refers to its climb in the log. The Intel/Radeon comparison is made **on the data**:
nominal level, degradation, CPU, RAM, GPU, VRAM, network, errors, birth and first
frame times, stability — with no conclusions beyond what the data show.

## 12. The system journal (work to do first)

Today REMOTIX writes to a file of its own (`registro.log`, from standard output). In phase 16:

- the log goes into the **journal** (`journalctl -u <unità>`), with the useful structured fields
  (area, tenant, severity level) — the file stays only if the administrator asks for it;
- events: start/stop, sessions, transport, clocks, re-entries, RCP, encoding, input, permissions,
  configuration, anomalies;
- ⛔ **never** passwords, tokens, keys, screen or input content (keystrokes
  are logged as «tasto», never as a character).

## 13. Before the campaign

0. **server rebooted** (decided by the user on 25 Sep, to start clean), `/media` intact:
   the root in RAM must be redone with steps 0, 1, 5, 6 and 7 of the recipe
   (`riavvio-perde-la-chiave-ssh`: route, key, host packages, `provisiona.sh`,
   `storage.conf` and the four boxes) — build container, libraries and images sit
   on `/media` and remain; then we **look** that the server is empty (no processes, tenants,
   compositors left over) before the first measure;
   `[M]` **done on the evening of 25 Sep**: root verified by `provisiona.sh verifica`, boxes on
   `b1443a0b`/`c5279e66`, smoke F-001/F-002 **16 PASS out of 16** (4 desktops × 2 browsers). The
   recipe was missing three pieces, now added: `labwc` and `wlr-randr` (from the apt cache),
   Chrome (`/media/REMOTIX/cache/chrome.deb`) and `~/SERVER.ssh` on the server (0600: the suite
   reads the sudo password from it — the copy is made by the user);
1. the journal (§12) and the configurable cap, with the **short regression suite** of phase 15
   (login, input, image, clipboard, «Esci», clocks — on the 4 desktops with the two browsers) on that
   commit;
2. the setup: 16 compositors, the three enclosures, the resource series, the four automatic
   jobs, the short functional check, the log and the report — every piece **with its
   own test**, as in the suite (a meter that has never given red does not measure);
3. a short **trial climb** (4 users, 3 minutes per level) to calibrate the setup, which does not
   count;
4. the thresholds of §9 **approved by the user**.

## 14. Anomalies and repetitions

1. preserve the evidence; 2. change nothing straight away; 3. analyse; 4. look for the cause;
5. **repeat under the same conditions**; 6. compare. If REMOTIX changes: new commit, short
regression suite, and **the climb concerned is redone**. A FAIL stays tied to its
configuration (desktop, card, commit, job, users, symptom) and is not generalised.

### Anomaly A1 — Firefox in 4K skips frames already with one user (25 Sep, night)

`[M]` trial climb (GNOME 4K, 1 user, Firefox client): 489 delivered, 433 painted, **11.5 %
skipped ⇒ FAIL** already at the first step; Chrome under the same conditions 3–6 %. Diagnosis (evidence in
`/media/REMOTIX/misure/fase16/diagnosi-ff-hw/`): the Firefox client decodes **already in hardware**
(VA-API, 2.3 ms of video engine per frame, like Chrome); the bottleneck is the page's drawing route:
in Firefox 140 `createImageBitmap(VideoFrame)` does a **synchronous readback from the GPU**
(~34 ms at 4K, on the main thread, Mozilla bug 1788206), the decoder queue goes above 2 and the
page skips (`saltati_coda`). With software decoding it drops to 12 %, still above 10.
⇒ It is a limit of the **product with Firefox in 4K** (the page), not of the server nor of the load: the
campaign measures it as it is, and at 4K every step with a Firefox user is affected.
Cure candidate, to be measured after the campaign: drawing with **WebGL2 `texImage2D(VideoFrame)`**
(via DMA-BUF without readback in ESR 140; estimate < 2 ms), bench ready in
`banchi/16-stress/16-banco-tela.html` (routes `bmp` and `gl`, criteria: drawing < 3 ms, skipped < 5 %, and
the snapshot of the glass with the witness to exclude the 2D's stalls).

### Anomaly A2 — on LXQt the terminal opens `dash`, not the user's shell (27 Sep)

`[M]` Profile C on LXQt did not work: qterminal opened **`/bin/sh` (dash)**, without `.bashrc`
or history. Cause (corrected on 28 Sep, `[M]` on a live XFCE session): outside GNOME sessions are born **without `SHELL`** — the environment is composed from zero and does not put it in; on GNOME it is **`SHELL=` empty** on purpose (`src/sessione.c`
~1682, `src/figlio.c` ~1159 — intended for the trap of `gnome-session`'s login shell), and
qtermwidget without `SHELL` falls back to `/bin/sh`; thunar/xfce4-terminal, konsole and gnome-terminal
read the shell from passwd and do not notice. ⇒ **It is a functional defect of the product**
(an LXQt user who opens the terminal does not find their shell), which phase 15 did not see: it is
**D-022**, to be cured AFTER the campaign (the trap is GNOME's only: outside GNOME, `SHELL` from the
passwd line) with its test in the suite. In order not to stop the campaign on a defect that does not
touch capacity, the actor opens `qterminal -e bash` — **declared**, and it is the only point where
the bench does not use the product as a person would use it.

### Anomaly A3 — Radeon, 4K: spiky delay and 3824-wide canvas without an image (27 Sep)

`[M]` `amd-4k-gnome` (binary 45d048c8, Radeon RX 6800, radeonsi 25.0.7), **1 user**:
- **delay**: OURS median **9.1–9.3 ms** but p95 of the p95s **45–50 ms** (max 60 ms), on the Intel
  at the same level it stayed green up to 3 users ⇒ DEGRADED at 1 user, twice. The normal work
  is fast; they are spikes. `[?]` Who makes them (VCN encoding, the copy from the card, the
  compositor): to be measured after the campaign, before judging the Radeon in 4K.
- **canvas 3824 × 2064**: the check with **Chrome** (window 3840×2073, canvas 3824) never
  had a frame: 99 times «il flusso MOSTRA 3840x2064 … la tela è 3824x2064» and 99 times «il
  codec 1 non ha consegnato il fotogramma dalla SCHEDA». Mutter gave a monitor 3840 wide
  instead of the 3824 requested, and the child refuses the different size. With Firefox (another width)
  the check passed. On the Intel the same Chrome was born. ⇒ **functional defect of the
  product** on the Radeon (a wide canvas not a multiple of 64 stays black): **D-023**, to be cured
  after the campaign with its test in the suite. Evidence:
  `misure/fase16/amd-4k-gnome/livello-01-ripetizione/journal-err.jsonl`.
  ⭐ **Cause and cure, 27 Sep**: it is not Mutter, it is the **driver** — `hevc_vaapi` on radeonsi declares
  in the stream the multiple of 64 without a conformance window (`ffmpeg` from the command
  line does it too: 2544 → 2560), while H.264 on the same card is right; Chrome chooses HEVC. The
  cure writes the frame into the SPS with `hevc_metadata` (§17.1). ⇒ **All the Chrome sessions
  of the Radeon campaign with the binary 45d048c8 are black because of D-023**: those steps measure the
  defect, not the capacity, and are redone with the cured binary.

### Anomaly A4 — the «lost» PageDown on KDE was the actor's (27 Sep)

`[M]` At 1 user, on all the campaigns done: **KDE 14 PageDown with no effect out of 49** (Intel and
Radeon), the other desktops **0 out of 172**; clicks, typing and wheel on KDE: 0 lost. The key
**arrives** at the server (`POSIZIONE_TASTO` pressed and released in the log). All the lost ones
come **after a wheel** (or after another lost PageDown); after a click or a navigation,
never. Cause: the actor's `aspetta()` returned at the first good row and lost the positions after it,
so after a wheel it believed the page to be halfway while it was at the bottom, and chose PageDown on a
page that could not go down. On KDE the wheel moves more (`scroll_discrete`, 144 units) and
the bottom is touched more often. ⇒ **Defect of the bench, not of the product**; cure in §17.2. It made
`amd-freq-*` FAIL and weighed on `intel-b-4k-kde` and `amd-4k-kde`. ⚠ The up/down arrows that
the user had noticed by hand remain a separate question: this bench does not test them.
`[M]` **Verification, evening of 27 Sep** (`amd-b-4k-kde`, actor cured): 10 PageDown, **0 lost**; the
1-user step now gives way only because of the delay (A3, OURS p95 ~41 ms + 9), no longer because of input.

### Anomaly A3, second half — the Radeon's delay is NOT the frequency (27 Sep)

`[M]` KDE 4K, 1 user, binary 28a947f5, two steps per condition: OURS p95 of the p95s
**39.3 / 38.6 ms** with `power_dpm_force_performance_level=auto`, **37.5 / 42.0 ms** with `high`;
median 8.8 ms in all four. ⇒ Hypothesis refuted; the card went back to `auto`. `[?]`
It remains to understand where the spikes come from (encoding has a median of the p95s of ~20 ms).

`[M]` **Where the spikes are** (server log, `amd-freq-auto/livello-01`, 3322 frames):
encoding is bimodal — median **8.7 ms**, p99 **31 ms** — and the slow ones arrive **in groups of 5
consecutive at 31 ms**, every 12–40 s, on very small deltas (300–1500 bytes); the Intel on the same
work: p99 8.7 ms, max 10.4. 11 groups out of 13 begin within 1.5 s of an action that makes
the page redraw (click, wheel, key). `[?]` **Hypothesis**, to be verified: on radeonsi the
VPP's RGB → NV12 conversion runs on the **shaders** (graphics queue), queued behind the
redraw of the session's desktop; on the Intel a dedicated block (VEBOX) does it. If so,
the cure candidate is a high priority for the VPP context, or the conversion inside the
encoder where the card allows it. The times are taken from the encoding call, which
includes the wait for the VPP.

⛔ **Hypothesis REFUTED, 29 Sep** (agent sent to refute, Mesa 25.0.7 sources and logs):
- on radeonsi the VPP **does not convert**: from the 16th frame `postproc.c` records the RGB source and
  returns (EFC), and the RGB→NV12 conversion is done by the **VCN inside the encoding** reading the
  compositor's linear buffer (conversion measured 0.03 ms, against 8.6 ms of VEBOX on the Intel);
- the groups are **always 5 frames** (64 out of 64), ~8.7 + 22 ms, **whatever the size**
  (300 B as 480 KB) and **even spread out in time** (one group on GNOME lasts 1.2 s): it counts
  frames, not time;
- **per session**: in `amd-b-4k-kde` u99 does 5×31 ms while u1, on the same card and the same
  VCN, encodes at 8.5 ms at the same instants; graphics card at 2–6 %.
  ⇒ No common queue, no priority to raise. `[?]` Candidates: the implicit wait on the buffer
  of that session's compositor, the 30 MB linear buffer in system memory (GTT), or
  the state of the VCN context. **Proposed experiments**: (1) measure first — explicit wait on the
  DMA-BUF fence (`DMA_BUF_IOCTL_EXPORT_SYNC_FILE`) outside «codifica», and encoding split
  into send/receive; (2) turn off the EFC (one extra `vaProcess` at opening: Mesa disables it
  for good) so the VCN reads an NV12 in VRAM, at the cost of ~1–2 ms of copy. To be done before
  judging the Radeon's 4K.

`[M]` **The two experiments, 29 Sep morning** (branch `a3-esperimenti`, commit `18b6437`, binaries
`3e510160` and `39e3ed86`; KDE 4K Radeon, 1 user, two steps each; evidence
`misure/fase16/a3-misura-kde`, `a3-senza-efc-kde`):
1. **the compositor's fence has NOTHING to do with it**: waited for explicitly and measured separately, it is worth
   0.37 ms on the normal frames and **0.02 ms on the slow ones**; and the extra 22 ms sit **all
   inside `avcodec_send_frame`** (receive 0.0 ms): with `async_depth=1` it is the VCN that encodes;
   still 100 and 105 slow frames per step;
2. **the EFC has NOTHING to do with it**: turned off (real conversion, 0.75 ms median), the groups of 5 × 31 ms stay
   identical — 95 and 106 slow per step, encoding p99 31.1–31.3 ms.
⇒ The delay is **inside the Radeon's VCN encoding**, one session at a time, 5 frames
every 12–40 s. What remains to be tested: the surfaces with the card's tiling (instead of linear), the
encoding in a new context; and, if neither, it is a behaviour of the driver/firmware to be
reported to Mesa with the scene reproduced. The Radeon's 4K in the summary stays with this reservation.

`[M]` **Step 1 (29 Sep 2026): Mesa 26.1.6 does not cure.** KDE box with Mesa 26.1.6 from
`trixie-backports`, same binary `4fb3287d`, KDE 4K Radeon 1 user, two steps of 6 min
(`a3-mesa26-kde`): **100 and 102** encodings > 20 ms (with 25.0.7: 100 and 105), in bursts of 5, median
31.0 ms. ⇒ The manual can NOT say «Radeon: serve Mesa ≥ X»; the next step for whoever wants to help
the driver is the minimal reproduction without REMOTIX (dossier §6.2). The box went back to Mesa 25.0.7
(rebuilt from the image).

✅ **The user's decision, 29 Sep 2026**: *«è fuori dal nostro ambito»* — A3 **is not worked around** in
REMOTIX; it is documented in minute detail so that it can be brought to the driver's developers:
**`fasi/16-a3-radeon-vcn.md`** (machine, chain, measures, hypotheses excluded, reproduction, draft of the
report for Mesa). The Radeon's 4K in the summary is limited by the driver, and this is declared.

### Note A5 — KDE Full HD on the Radeon: user 4's video stops for 1–3 s (28 Sep, night)

`[M]` `amd-b-fhd-kde`, levels 12 and 16: the only DEGRADED is user 4 (profile D, 4K video,
Chrome), «blocco più lungo dell'immagine» 1.1–2.7 s, while the frames **all arrive and are
painted** (6622 delivered = 6622 painted, 0 holes). The same user on GNOME Radeon
(0.11 s) and on KDE Intel (0.08 s) is green ⇒ **it is not the D-023 cure** (active on GNOME too). `[?]`
Hypothesis: the video player inside the KDE session stops (the image arrives but does not change). To
be looked at after the campaign, before closing KDE Full HD Radeon at 15.

⭐ **Closed, 29 Sep (agent sent to refute, the levels' logs)**: it is the **restart of the video file**.
The player runs the ~634 s file with `loop`; every stall of user 4 falls at t≈630–634 or t≈0–6 s
of the player, every ~10.5 min, and the player itself counts 60–90 frames lost at each lap. The
same happens on GNOME Radeon (2.8–4.4 s) and KDE Intel (1.5 s): KDE Radeon was DEGRADED only
because its judging windows fell on the lap. On our side, in the hole: the capture runs
(«attese a vuoto» +123/s), the frames delivered stay still (the compositor gives no damage),
no key requested, clean network; the holes at the server coincide to the millisecond with those
of the actor (2.685 against 2.68 s). ⇒ **It is not REMOTIX**, it is the bench. Cure of the bench (not done):
a file longer than the level (`ffmpeg -stream_loop`, without re-encoding), or the rows around the
lap declared and excluded. On the summary it weighs little: it touches the strict number of KDE Full HD Radeon.
⭐ **Cure of the bench done, 29 Sep**: `video/bbb_sunflower_2160p_30fps_x4.mp4`, the same file
concatenated 4 times without re-encoding (`ffmpeg -stream_loop 3 -c copy`, 2538 s = 42 min, sha256 in
`video/SHA256SUMS`), longer than any level; `16-coda.sh` uses it by default. `[M]` tested
on 29 Sep (`a5-video-lungo-kde`, KDE Full HD Radeon, 4 users, 12 min: with the old file the lap
would have fallen at 10.5 min, inside the 10–12 window): user 4 **GREEN, stall 0.08 s**, level
all GREEN (5 out of 5).

### The up/down arrows (reported by the user by hand) — study of 29 Sep

Reading of the code (agent), **no test yet**. The arrows go through `POSIZIONE_TASTO`, which
keeps a state in the page and in the server (letters do not): a state defect hits the arrows and
spares typing. Mechanisms in order: (1) in the page a lost release leaves the code in
`cl_tasti_premuti` and the next press is silently discarded (`cl_su_keyup` returns at once when
`cl_nel_modulo`); (2) on Mutter/KWin the libei keyboard paused or exchanged
(`tastiera_attiva` false) discards the press; (3) between parent and child the non-blocking socket
discards an input on `EAGAIN` when the child is late; (4) the keypad arrows with
NumLock off arrive as KP_8/KP_2; (5) keys discarded as IME composition. `[M]` in the
logs of the whole campaign: **0** inputs not sent on to the child, **1** keyboard
exchange (u2).
✅ **Closed on 29 Sep 2026, without a test**: the only report (26 Sep, 16:39) had been withdrawn by the user
one minute later (*«ignora questo messaggio, è un errore»*) and had entered the open points by
mistake; no defect observed, C23 (Shift+arrows) green. The user's words: *«ok, levale»*. If
it happens again, it is reopened with desktop and program, and the targeted test of 200 arrows is already described above.

## 15. Declared limits

- **the server also acts as the client**: the result is a lower bound (§2);
- **the network is not measured**: browser and server on the same machine. How REMOTIX bears a network
  that loses packets (`[M]` 0.6 % on the 2.4 GHz Wi-Fi, phase 15) is a separate question, to be
  added later (throttling from the tablet, `wondershaper-sul-tablet`);
- **YouTube** is an external service: if it changes, we switch to the declared local file (§5);
- the **test beyond 16** is overload, outside the certification.

## 16. Success criterion for the 16 users

For **one** configuration, the requirement is verified when: 16 real sessions are active
together · each with its own job · whoever was there continues · the check of the 16 is complete and **GREEN**
according to §9 · the evidence is collected · the result is tied to a commit · the climb is
reproducible or documented well enough to redo it.

⚠ **The times**: the server's logs, the measures' folders and the `[hh:mm:ss]` rows of the climbs
are in **UTC** (the server has no time zone set); Italian time (CEST, September) is **UTC + 2**.

## 17. The changes of phase 16 — the log for the technical manual

*The user's request, 26 Sep 2026: every change is noted here, because at the end of the work REMOTIX's
**technical manual** is written from it. One row per change: what, why, the measure, the commit, and whether
it is **installed** (in the binary or in the boxes' page) or not. The user's decisions sit in
`DECISIONI.md` §9.*

### 17.1 The product (`src/`)

| commit | what | why | measure | installed |
|---|---|---|---|---|
| `62753e7` | **log in the journal** (`--journal`): the journal's native protocol, one `sendmsg` per line, non-blocking; fields `REMOTIX_AREA`, `REMOTIX_INQUILINO`, `CODE_FILE`, `CODE_LINE`, `SYSLOG_IDENTIFIER=remotix`; severity 3/4/6 from the ⛔/⚠ mark at the head of the body; the chatter does NOT go to the journal; the child receives it from the parent (`argv[16]`) | §12, DECISIONI §9.1 | 33 lines out of 33 with the fields; stderr identical without the option | yes, from `bdde6bb1` |
| `62753e7` | **input is not written**: `rcp.c` (and the twin `banchi/rcp/rcp.c`), `tastiera.c`, `input.c` — no `U+XXXX` nor key codes, except modifiers and buttons | §12, DECISIONI §9.2 | audit of all the `registro_*` calls | yes |
| `62753e7` | `Makefile`: every object depends on `registro.h` | `registro.h` became macros (`__FILE__`/`__LINE__`) and a half build did not link | — | — |
| `ebc9dcd` | **«NOSTRO nel secondo» line** of the child: p95, maximum and median of *copy → bytes out* over only the frames of that second | the TRATTO line uses a ring of 512 frames (a spike stays inside for 8–17 s) and starts from the compositor's `pts`; §3.2 asks for **our piece** | diagnosis of the round trip in 4K: ours ~19/24 ms out of 45/54 (§9, «Quale ritardo classifica») | yes, from `4cba76f6` |
| `97e94fe` | **encoder entrypoint chosen on the capability declared** by the driver: `EncSliceLP` if present (Intel, identical), otherwise full `EncSlice` (radeonsi), declared; software only if neither is present | the Radeon has no low power ⇒ the product encoded in software | Radeon: «in HARDWARE · radeonsi · EncSlice, piena», OURS p95 17–29 ms | yes, `3fe94e8b` (binary of the Intel campaign) |
| `86598d6` | **first frame from the card judged by sampling** (64×64 grid, cap 250 ms) instead of reading the whole DMA-BUF slab | on a discrete card the slab is in VRAM: reading it from the CPU cost **63.7 s** and the session was not born | `[M]` 26 Sep, Radeon, XFCE and GNOME 4K: **5.7–6.2 ms** (before 63.7 s), `h264_vaapi` encoding in HARDWARE on radeonsi, sessions GREEN | yes, `45d048c8` |
| `ea0f82a` | **WebGL2 drawing route** in the page (`?tela=gl`): synchronous `texImage2D(VideoFrame)`, `close()` at once, full-screen quad, same counters | anomaly A1: in Firefox `createImageBitmap(VideoFrame)` reads back from the GPU (~34 ms at 4K) ⇒ 11–50 % skipped with 1 user | to be measured; then the user's look against the squares (DECISIONI §9.4) | **no** (candidate) |

| (questo commit) | **the skip rule weighted with the drawing cost**: the drawing is skipped if `coda > 2` **and** `coda × costo_disegno() > 16 ms` (cost = median of the synchronous part of the callback, + the glass on the asynchronous route); plus the counters `cq`/`cu` (queue at delivery and at exit), `dec8`, `eta`, `ric` in the diary | the «coda > 2» rule (14 Aug 2026) saved the 34 ms of 2D drawing; with WebGL (0.26 ms) it saves nothing and threw away 12 % | default Firefox: skips as before (15 = the frames at queue ≥ 3), delay unchanged (36.8 ms); Chrome and WebGL: it does not trigger; to be validated on KDE 4K with `?tela=gl` | **no** |

| (questo commit) | **WebGL2 becomes the default drawing route** for all browsers; `?tela=bmp` (or `2d`, `desincronizzata`) puts back the earlier routes for comparison; without WebGL2 the page falls back to `bitmaprenderer` and writes so | anomaly A1; DECISIONI §9.4 | the user's judgement at the screen (KDE, Firefox, 4K video and WebGL aquarium with 30 000 fish): «l'immagine è perfetta: qualità ottima, 45 fps costanti, nessuno scatto» — no 64×192 blocks | after the short suite |

| (questo commit) | **D-023, the frame the driver does not write**: if the first SPS of a context declares a size larger than the canvas by less than one block (64), `codificatore.c` passes the packets with the SPS (the keys) through `hevc_metadata`/`h264_metadata` with `crop_right`/`crop_bottom`, and declares it (line «⭐ D-023»); any other difference stays refused by `forma_va_bene()` | anomaly A3: on the Radeon (radeonsi 25.0.7) `hevc_vaapi` declares the multiple of 64 without a conformance window (from command-line `ffmpeg` too) ⇒ every HEVC session — Chrome — at a canvas not a multiple of 64 stayed **black** | `banchi/16-stress/16-d023-cornice.sh`, 4 real canvases × 2 codecs: Radeon **8 PASS** (PSNR 47 dB, the image is 1:1), without the cure **HEVC 4 FAIL out of 4**; Intel 8 PASS, the cure never triggers | **yes**, binary **`28a947f5`** (from `678a2da`), 27 Sep: short suite on the Radeon, 4 desktops × 2 browsers, **352 PASS out of 352**; in the boxes' logs the cure triggered 62 times, 0 streams refused |

| (questo commit) | **D-022, the `SHELL` outside GNOME**: `sessione.c`, at the end of the session's environment, `SHELL` from the user's passwd line for KDE, XFCE and LXQt (GNOME stays empty: `gnome-session`'s trap); without a shell in passwd it says so | anomaly A2: `[M]` in a live XFCE session `labwc` and `xfce4-panel` without `SHELL`, `systemd --user` with `/bin/bash`; qterminal fell back to `/bin/sh` | `banchi/15-suite/15-f032-la-shell-dell-utente.py` (F-032): on the 4 desktops the session's `SHELL` (empty on GNOME), and on LXQt `qterminal` launched with the panel's environment opens `bash`: **4 PASS**, fault red on the 4; with the earlier binary (28a947f5) LXQt **FAIL** («SHELL della sessione None») | **yes**, binary **`4fb3287d`**, 29 Sep (after the campaign); short suite with F-032 in parallel on the 4 desktops: 328 PASS, 4 FAIL, 36 BLOCKED — the 16 red combinations **redone one at a time: 16 out of 16 PASS**. The reds were almost all «utente o parola d'ordine non corretti» with `pam_unix: user unknown` for a tenant created 7 s earlier (`[M]` gnome 04:40:04 created, 04:40:11 unknown) and only with the round in parallel: `[?]` defect of the bench or of the environment, to be understood; on 26 Sep the same round was 352/352 |
**Binary and page of the new campaign** (from `e4e05dc`): binary **`45d048c8`**, page **`fb9a18f3`** —
extended short suite (login, input, image, clipboard, «Esci», clocks, plus canvas at attach, video,
detach and re-attach, re-attach at a different size; 4 desktops × 2 browsers): **352 PASS out of 352**, 26 Sep.

### 17.2 The test setup (benches and boxes)

| commit | what | why |
|---|---|---|
| `8e7f9ec` | `11-accendi.sh server`: `--journal` and the cap from `REMOTIX_TETTO_SESSIONI` | §12 and §2 (cap at 17) |
| `87f614e` | `11-accendi.sh accendi`: `REMOTIX_SCHEDA=intel|amd`, a single card inside the box | Radeon campaign (§11) |
| `8f7bbd8` | the card's nodes enter **with their real name too** when they are not `card0`/`renderD128` | `[M]` libdrm rebuilds the name from the node number: without that node the compositor did not announce DMA-BUF and VA-API would not open (Radeon: 205 ms → 17–29 ms) |
| various | `banchi/16-stress/`: actor, resources, classification, climb, short check, compositors, queue, report, canvas bench | the setup of §4–§10; corrected after an adversarial review (6 defects) and after the first real climbs (§14) |
| (questo commit) | job C on LXQt: `qterminal -e bash`, and the actor checks the shell under the terminal | anomaly A2 (D-022, product defect: `SHELL=` empty ⇒ dash) — declared workaround of the bench, the product's cure is after the campaign |
| (questo commit) | job B on LXQt: deletion is Shift+Del and «y» (pcmanfm-qt: the menu's Del did not trigger; «No» is the dialog's default button), snapshot on failure | `[M]` 27 Sep: «input perso: cancella» gave FAIL to LXQt already at 2 users — defect of the bench, not of the product; the LXQt 4K and 3K climbs are redone |
| `07-b46` | `REMOTIX_FF_PREFS`: extra preferences in the benches' Firefox profile | to repeat a measure with software decoding |
| (questo commit) | `16-lavori.py`, actor A: `aspetta()` reads the WHOLE group of rows of the notebook before returning, and before choosing wheel or key the actor rereads the position | anomaly A4: the «lost» PageDown on KDE was the actor's (old position, page already at the bottom). In force on the server from **13:58 UTC on 27 Sep**, that is from the second user of `amd-b-4k-gnome` onwards (user 01 of that step started at 13:55 with the earlier code) |
| (questo commit) | **the boxes' lock**: `/media/REMOTIX/rete11/.scatole.lock` (flock) taken by `15-giro.py`, `16-salita.py` and `11-gancio.sh` (not by the «carte»); whoever holds it writes so inside; the children inherit `REMOTIX_SCATOLE_TENUTE`; `sgombera_inquilini` does nothing without that variable. ⚠ Not in `/run/lock`: sticky folder + `fs.protected_regular`, root does not reopen nicfio's file | it closes the «user unknown» of 29 Sep (see D-022 in §17.1): every mesh of the hook cleared out ALL the `c<n>u<n>` tenants, and a push during a suite round deleted the tenants just born ⇒ failed logins ⇒ ban of 192.168.0.2 (12 h) | short round `16-corta-serratura-2` (4 desktops × 2 browsers, 60 min) with a «carte» push halfway: **368 PASS, 0 FAIL, 0 BLOCKED**, 0 clear-outs; «rete» hook with the lock held: **refused** (rc 1, «le tiene gia' un altro banco»); with the boxes free it starts (rc 0, no red) | copied to the server, 29 Sep |

### 17.3 The server's environment (volatile: rootfs in RAM)

To the rebuilding recipe after a reboot are added: `labwc`, `wlr-randr`, Chrome from
`/media/REMOTIX/cache/chrome.deb`, `~/SERVER.ssh` (0600) on the server, `loginctl enable-linger nicfio`
(the night queue lives without ssh sessions), and the queue's unit with `TimeoutStopSec=1200`,
`KillMode=mixed`, `OOMPolicy=continue`.

⛔ **The lock-up of 28 Sep, 08:42 (06:42 UTC)**: `amd-b-3k-xfce`, step of 16 users (17 sessions
and 17 client browsers on the same machine): the RAM ran out, the kernel's killer killed Chrome
over and over amid RCU stalls, and the system stayed **stuck** — ping yes, ssh and REMOTIX no —
until the user rebooted it. Evidence: photo of the console (the user), the climb's last line
«controllo corto: BLOCKED» at 06:41:49 UTC. ⇒ Two changes to the environment, from 28 Sep 09:05:
- **swap from 16 to 32 GB** (the user, on the disk): it does not change the measured limits, which fall where the
  RAM runs out; it lengthens the time before the killer;
- **`earlyoom`** (`/etc/default/earlyoom`: `-m 5 -s 100 -r 60`, prefers Chrome and
  Firefox processes, avoids `remotix`, `systemd`, `sshd`, `podman`, `conmon`, the compositors, `python3`): with
  available RAM below 5 % it closes a browser **before** the machine gets stuck. A
  closed browser is a FAIL of that level, as it was before; the difference is that the night goes on.
  ⚠ It goes into the recipe after every reboot (the rootfs is in RAM).

