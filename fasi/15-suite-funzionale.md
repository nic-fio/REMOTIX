# Phase 15 — The functional suite

*⚠ Historical measures, on the machine of the time. With phase 18 (without ffmpeg) those that the change invalidated were removed — encoding without a card and colour conversion with swscale; those of encoding on the card and of the audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision.*

*Decided on **24 Sep 2026**, evening. To be opened in a new session.*

## Why it exists

On 24 September, at the end of phase 14, the user tested by hand and found **six defects** that the
anti-regression net had not seen (`fasi/14-lxqt.md`, «La sera del 24 settembre»): the border that cannot be
grabbed, Shift+arrow, the Firefox strip in width and in height, the LXQt lock, Chrome's click,
LXQt's «Esci» that makes the session be reborn. ⇒ The net looks at the **pieces** (the frame arrives,
the key arrives at the server); it does not look at what **the user does** (I select a text, I grab a border,
I log out). Phase 15 looks at that.

The user: *«Prima si verifica che REMOTIX faccia correttamente ciò che deve fare. Solo dopo si misura
quanto carico il sistema è in grado di sostenere.»* ⇒ Phase 15 comes **before** phase 16 (stress and
capacity) and the installation system.

## The user's decisions (24 Sep 2026, evening)

| | decision |
|---|---|
| **it replaces the whole net** | *«eviterei la rete intera… questi test la sostituiscono»*. Under the suite only a **short technical layer** remains: C7 (nothing is left), C9 (the log says whose), C14 (the boxes do not disturb each other), C18 (the card's groups), C19 (the box stays clean) |
| **real browsers** | Firefox and Chrome on the server, real windows; the Python client and the scripts **do not certify** (they can only diagnose) |
| **the matrix is born from `SPECIFICHE.md`** | and is reviewed with the user **before** writing a single new test |
| **out** the functions REMOTIX does not have | hot resolution (removed on 17 Aug 2026, `DECISIONI.md` §5.1-bis), multi-monitor, re-attach by «ID di sessione» (you get back in with user and password) |
| **in** those the document did not have | clipboard in both directions · pointer shape · keyboard layout, accents, AltGr · same user from two tabs (ghost, eviction) · the three clocks of §5.3 · wrong password and ban · Android touch |
| **the user's addition** | detach and **re-attach at a different size** |
| ⭐ **declared exception** | at re-attach at a different size, on **KDE** (KWin < 6.8, `SPECIFICHE.md` ~851) the canvas stays the old one and **the browser rescales**: on KDE it is the expected result, not a FAIL. On GNOME, XFCE, LXQt the canvas takes the new size. To be written in `DECISIONI.md` too |
| **the report serves the CLEAN-UP** | every execution recorded, every FAIL a numbered defect |
| **the cycle** | round 1 ⇒ list of defects ⇒ clean-up ⇒ **complete round 2 with outcome ZERO defects** ⇒ phase 16 |
| ⛔ **freeze** | between the end of the clean-up and round 2 neither the product nor the tests are touched; if round 2 finds a defect, it is cured and round 2 is redone **complete**, not just the red test |
| **every test has its grafted fault** | a test that has never given red is not a test (like C21-C24) |
| **duration** | every test < 10 minutes (the user: *«limitiamole ad un massimo di 10 minuti»*); the whole suite: goal < 1 hour |

## The desktops, the browsers, the combinations

- **Desktops**: GNOME (8511), KDE (8512), XFCE (8513), LXQt (8514) — the `rete11-*` boxes.
- **Browsers**: Firefox 140 and Chrome 154, **real**, on the server, in the labwc without a screen at 3840x2160
  (`XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 REMOTIX_SCHERMO_ANNIDATO=1
  REMOTIX_SUL_SERVER=1 REMOTIX_CHROME_OPZIONI=--ozone-platform=wayland MOZ_ENABLE_WAYLAND=1`).
- **Chrome Android**: the **user's** column, with the user's phone (on the emulator Chrome does not start, 19 Sep).
- ⇒ **8 suites per round** (4 desktops × 2 browsers), plus the Android column by hand.
- ⚠ The browser matrix stays **separate** from the desktop one (the user's document, §25).

## The matrix (proposal, to be reviewed with the user)

`[?]` = existing coverage to be verified; «nuova» = test to be written.

| ID | function | what is looked at (from the snapshot or from the field, not from a counter) | coverage today |
|---|---|---|---|
| F-001 | login and creation of the session | page, form, admission, desktop in view | `12-client-veri` a-b, C1 |
| F-002 | first image | desktop drawn, not degenerate, within the cap | `12-client-veri` c |
| F-003 | screen update | window opened/closed, moved, quick changes | C2, C3 (Python) ⇒ new with the browsers |
| F-004 | mouse | movement, left and right click, double click, drag, selection | `12-client-veri` e ⇒ new (effect on screen) |
| F-005 | pointer shape | arrow, I-beam on text, double arrow on the border | **C21** |
| F-006 | resizing from the border | the right border moves, the others do not | **C22** |
| F-007 | keyboard: characters and special keys | Enter, Backspace, Esc, arrows, Tab inside an application | C4 (Python) ⇒ new with the browsers |
| F-008 | modifiers and combinations | Shift+arrows, Ctrl+Shift+arrows, Ctrl+C/V in the application | **C23** (+ widen) |
| F-009 | layout, accents, AltGr | «è», «à», «@», «€» with the it layout | new |
| F-010 | desktop shortcuts | the useful ones work; the dangerous ones (lock) do not | new |
| F-011 | the canvas at attach | window size, multiple of 16, no green strip, full background | snapshot of `12-client-veri` ⇒ new |
| F-012 | audio | a real application plays, the browser receives sound not silence | C5 (Python) ⇒ new with the browsers |
| F-013 | video | a video in an application: continuous image and sound | new |
| F-014 | clipboard, browser → session | pasted in the application | C17 (Python) ⇒ new |
| F-015 | clipboard, session → browser | copied in the session, arrives at the browser | C17 (Python) ⇒ new |
| F-016 | detach | the session stays, the programs stay | C6 (Python) ⇒ new |
| F-017 | re-attach at the same size | I find the state again (window, text written) | C6 ⇒ new |
| F-018 | **re-attach at a different size** | GNOME/XFCE/LXQt: new canvas, desktop following it (background, panel); **KDE: old canvas, rescaled (exception)** | new |
| F-019 | network loss and re-entry | dead line: the wire drops, you get back in by hand, the session is there | new (⚠ how to simulate the network: to be decided) |
| F-020 | browser closed abruptly, then new connection | the session is still there, you re-attach to it | `12-client-veri` g (reload) ⇒ new |
| F-021 | «Esci» from the menu | the session ends, the programs close, the page goes back to the form, no rebirth | `12-c20-veri`, **C24** (ten times) |
| F-022 | silence clock (30 s) | mute client ⇒ detached, session alive | new, clocks shortened |
| F-023 | inactivity clock (1800 s) | ⇒ short `--inattivita-s` | new, clocks shortened |
| F-024 | abandonment clock (3600 s) | the session closes with the programs | new, clocks shortened |
| F-025 | same user from two tabs | ghost, eviction after 15 s, `GIA_ATTIVA_REMOTA` | new |
| F-026 | several users together (2-3) | independent sessions, input and image do not mix | C14 (Python) ⇒ new |
| F-027 | wrong password | clear refusal, no session | new |
| F-028 | ban | after N errors the port closes for that address; `GIA_ATTIVA_REMOTA` does not count | new |
| F-029 | dangerous entries absent | no lock, suspend, reboot, shutdown in the menu; «Esci» is there | new (snapshot of the menu) |
| F-030 | the screen does not turn off nor lock by itself | 11 minutes idle, screen on | new (⚠ exceeds 10 min: to be shortened or declared) |
| F-031 | touch (Android) | tap, tap-and-a-half to drag | **user**, by hand |

**Complete paths** (the user's document, §26): A creation→desktop→input→detach→re-attach→input ·
B creation→activity→network loss→re-entry→activity · C creation→re-attach at a different size→re-attach
back · D creation→video/audio→network loss→re-entry · E creation→browser closed→wait→new
connection · F creation→application open→detach→wait→re-attach→state. ⚠ C has changed: hot
resolution does not exist, the size change is done only by re-attaching.

**Negative tests** (§27, adapted): non-existent user · wrong password · session already closed with «Esci»
(you get back in and a NEW, clean session is born) · network not available (the page cannot be reached: what
it says) · same user already active from another device.

**Number of tests.** 30 automatic functions × 4 desktops × 2 browsers = **240 cells**; 6 paths ×
8 = **48**; ~5 negatives × 4 desktops = **20** (the negatives do not depend on the browser: a single pass) ⇒
**about 300 executions per round**, plus the Android column by hand. Not 300 sessions: a suite per desktop
and browser **makes the session be born once** and tests the functions in a row like a real user; only the
tests that close or re-attach make another one be born.

## How it is run

- **one suite per (desktop, browser)**, the **four desktops in parallel** (one box each,
  separate browsers and debug ports — `banchi-in-parallelo-isolamento`), the two browsers one after the other;
- every test: a tenant of the net (`c<n>u<n>`, seen by C19 and by the clear-out), known scene in the
  session, judgement from the **snapshot** or from the **value of the field**, **never** from a counter;
- every test has `--certifica` (pure functions) and its **grafted fault** (outcome reversed: 0 = seen);
- outcomes: **PASS**, **FAIL**, **BLOCKED** (= I could not look, *with the reason*: a BLOCKED is not
  a PASS);
- ⛔ the suite **redoes the boxes from zero**: before launching it the user is asked whether they are testing by hand
  (24 Sep: a `nictest` session of theirs closed without warning);
- the automatic tests stay **in the net**: the suite is the new net (new family in `11-gancio.sh`).

## What is recorded, and how

**1. The execution log** — `banchi/15-suite/registro.jsonl`, **additions only, never
deletions** (a repeated round stays with all its rounds: that is how a race is seen), one row per
execution:

| field | example |
|---|---|
| `giro` | `1`, `2`, or `bonifica` |
| `test` / `funzione` | `T-018-kde-firefox` / `F-018` |
| `desktop` · `browser` · `versione` | `kde` · `firefox` · `140.16.0` |
| `sistema` | `Debian 13, labwc senza schermo 3840x2160` |
| `binario` · `pagina` · `commit` | md5 `7dfd6a96` · md5 `87268f13` · `53d07b4` |
| `inizio` · `durata_s` | ISO 8601 · `41` |
| `esito` | `PASS` / `FAIL` / `BLOCKED` |
| `ragione` | one sentence: what was seen (mandatory for FAIL and BLOCKED) |
| `atteso` · `osservato` | the two sentences, as in the test case |
| `guasto_visto` | `true`/`false` for the pass with the grafted fault |
| `evidenze` | paths: snapshots before/after, product log, browser JS errors, RCP/WebTransport lines |
| `difetto` | `D-007` if the FAIL opened or touched a defect |

**2. The evidence** — on the server in `/media/REMOTIX/misure/fase15/giro<N>/<desktop>/<browser>/<test>/`
(snapshots at scale 1, the box's `registro.log` cut to the interval, browser console, the tenant's `journalctl`
when needed). Linked to the Test ID and to the commit.

**3. The list of defects** — `banchi/15-suite/difetti.jsonl` (and the report shows it):
`id` (D-001…), what is seen (with the user's words if they found it), desktop and browser where it
happens, **class** (A real regression · B a desktop's assumption in the common code · C defect of the
bench · D wrong invariant, ⛔ never as a shortcut), **state** (open · in cure · cured ·
verified), the measured cause, the commit of the cure, **the test that watches over it from that day**.

**4. The report** — it is **generated** from the log, not written by hand: the function × desktop ×
browser matrix with the last outcome and the commit on which it was measured; the list of defects with their state; for
every FAIL/BLOCKED cell the reason and the link to the evidence. It serves the **clean-up**, not the user;
it can also be published as a private page updated at every round.

## Limits to declare, and decisions still open

- `[?]` **network loss** (F-019, paths B and D): on the server there are no `tc`/`wondershaper`; with the
  browser on the server `lo` or a veth can be throttled; the real path is from the tablet (`wondershaper`,
  [[wondershaper-sul-tablet]]). **To be decided with the user.**
- **long clocks** (F-022…F-024, F-030): they are tested with the clocks shortened from the command line
  (`--inattivita-s`, abandonment) on a dedicated box; declared.
- **Android**: to the user.
- the **1 px dot** under the pointer's tip (the price of the shape on KDE and labwc): the user's
  judgement, to be recorded as an entry of the matrix (F-005).

## The order

1. the matrix above **reviewed with the user**;
2. the new tests, in parallel (one agent per group of functions), each with its fault, inside the net;
3. the log, the list of defects and the report generator;
4. **round 1** (the 8 suites) + the user's Android column ⇒ list of defects;
5. **clean-up**;
6. ⛔ freeze, **round 2**: zero defects ⇒ phase 16.

---

## How it was built

*24 September night → 25 September 2026, morning (`9264c52`, `d9743dc`).*

**Ten groups of tests**, written in parallel (one agent per group), each with its common base
imported and not copied:

| group | functions | tests | common tools |
|---|---|---|---|
| **G1** | F-001 F-002 F-003 F-011 | `15-f001` `15-f003` `15-f011` | — |
| **G1b** «il desktop si comporta da desktop remoto» | F-010 F-029 F-030 | `15-f010` `15-f029` `15-f030` | `15-g1b-comune.py` (real clicks and keys to the browser, OCR of the snapshot); `15-g1b-esplora.py` diagnosis only |
| **G2** mouse and keyboard | F-004 F-007 F-009 | `15-f004` `15-f007` `15-f009` | `15-g2-scena.py`: a known page served in the tenant's home and opened in kiosk **inside** the session |
| **G3** | F-005 F-006 F-008 | `15-f005` `15-f006` `15-f008` | `15-g3-comune.py`: C21, C22, C23 of phase 14 imported as they are |
| **G4** audio and video | F-012 F-013 | `15-f012` `15-f013` | `15-g4-comune.py`: the **ear** in the page and the eye on the video |
| **G5** clipboard | F-014 F-015 | `15-f014` | — |
| **G6** detach and re-attach | F-016 F-017 F-018 F-020, P-A P-C P-E P-F | `15-f016` `15-f018` `15-f020` | `15-g6-comune.py` (the scene and the pure judges) |
| **G7** the network dropping and the clocks | F-019 F-022 F-023 F-024, P-B P-D | `15-f019` `15-f022` | `15-g7-comune.py` + `15-g7-server.sh`: a **second server** of the product per box (ports 8611-8614, clocks shortened from the command line), and the **dead line simulated on the server with nftables** (a table of ours that drops the UDP of only the test's port) |
| **G8** the users, the password, the ban | F-025 F-026 F-027 F-028, N-1 N-3 N-4 | `15-f025` `15-f026` `15-f027` `15-n027` | `15-g8-comune.py` + `15-g8-server.sh`: second server with ports 8621-8624, ban-file, socket and log **of its own** (`banchi-in-parallelo-isolamento`) |
| **G10** «Esci» | F-021 | `15-f021` | — |

⚠ The names G1 and G5 above are reconstructed: their tests do not write the group at the head (G5 appears
only in a note of `suite.py`, the Firefox profile). The others are written by the tests themselves.

⇒ **25 tests** covering F-001…F-030, the paths A-F and the negatives N-1, N-3, N-4. Every test
declares at its head, as lines of text, what it looks at: `FUNZIONI = (…)`, and if needed
`PER_BROWSER = False` (once only, with Firefox: F-027/F-028, F-030, the negatives), `LUNGA = True`,
`SERVER = "15-g7-server.sh"`.

**The common base** — `banchi/15-suite/suite.py`. A single language for all the tests:
- command line: `--scatola` and `--browser` (only one), `--guasto` (after the healthy pass, the pass
  with the grafted fault **in the same session**, outcome reversed), `--certifica` (only the pure
  functions), `--evidenze`, `--porte-base` (the browsers' debug ports, ⛔ different for every desktop in
  parallel), 4K by default;
- output: one `SUITE {…}` line per function looked at, which the round collects; code 0 all PASS · 1
  at least one FAIL or one fault not seen · 3 at least one BLOCKED;
- the tenant is called `c15<nnn>u<n>` (C19 and the clear-out recognise it) and is **always** cleared out;
- it relies on `12-client-veri.py` (the browser drivers: Marionette for Firefox, CDP for Chrome),
  `12-c20-veri.py` (the box, the server's log, the tenants) and `11-c21-…` (full-resolution
  snapshots);
- ⭐ on the server the commands inside the boxes go with **local** `sudo podman exec`, not over ssh towards
  itself: `[M]` 24 Sep, ten agents together, sshd truncated part of them ⇒ tenants not created and
  BLOCKED that were not the product's (G7's note).

**The round** — `banchi/15-suite/15-giro.py`, on the server as `nicfio` (the real browsers live there; the
benches get there with `15-porta.sh`, a single test is launched with `15-una.sh`):
- it finds the tests `15-f*.py` and `15-n*.py` and reads their declarations;
- ⭐ **the four desktops in parallel**, one row per desktop; in the row Firefox and then Chrome; different debug
  ports per desktop;
- every test with `--guasto`, cap **10 minutes** (beyond: BLOCKED «oltre i 10 minuti», and the process is
  killed);
- ⛔ before starting it looks whether there is a person in the boxes (anyone who is not a
  `c<n>u<n>` tenant): if there is, it stops. The boxes are redone from zero with `15-rifai-scatole.sh`, only with the
  user's go-ahead (permission given on 25 Sep).

⭐ **One labwc without a screen per desktop** — `15-compositori.sh accendi|spegni|stato`, 3840x2160 each.
`[M]` groups G2 and G8, 25 Sep: with the four desktops in the **same** labwc Chrome's windows
cover each other, and **covered Chrome does not repaint**: `Page.captureScreenshot` stays hung (a snapshot
hung for 17 minutes, three runs ended at 900 s). Firefox can be photographed even when covered, Chrome cannot. ⇒ Every
desktop has its own compositor, and in each one browser at a time; the round reads the socket from
`$XDG_RUNTIME_DIR/15-compositori/<desktop>` and passes it as `WAYLAND_DISPLAY`.

**The log** — `/media/REMOTIX/misure/fase15/registro.jsonl` on the server, copied into
`banchi/15-suite/registro.jsonl`; additions only, one row per execution with the fields of the table
above (plus `passata`: `sana` or `guasto`, and `prova`). The evidence in
`/media/REMOTIX/misure/fase15/giro<N>/<desktop>/<browser>/<prova>/` (the whole output in `uscita.log`,
snapshots and console inside). The defects in `banchi/15-suite/difetti.jsonl`.

**The report** — `banchi/15-suite/15-rapporto.py`, **generated from the log, never written by hand**:
the function × desktop × browser matrix with the last outcome of the healthy pass of the chosen round and the mark
of the fault, the defects with their state, for every FAIL or BLOCKED cell the reason and the evidence; at the head
binary, page, commit and the counts. `--testo` for the terminal, `--html` for a page.

    python3 banchi/15-suite/15-rapporto.py --registro banchi/15-suite/registro.jsonl \
        --difetti banchi/15-suite/difetti.jsonl --giro 1 --testo

**The technical layer** — `15-giro.py --strato-tecnico` (or `--solo-strato-tecnico`): for every desktop, in
parallel, **C7 C9 C18 C19**, each healthy and with its fault (`--lascia-un-processo`, `--togli-nome
tutto`, `--senza-usermod`, `--lascia-un-inquilino`), launched by `11-accendi.sh`; then **C14** with the
four together. ⛔ Before every link the same **clear-out** as `11-gancio.sh` (see D-013).

**In the net** — the **`suite`** family of `banchi/11-scatole/11-gancio.sh` (`227611d`, 25 Sep 09:35):
`GIRA_SUITE` launches `15-giro.py --giro ${GIRO_SUITE:-rete} --strato-tecnico` as the browsers' user,
from the whole tree of the benches; the hook warns «⛔ ~2 ore». It is the new net, as decided on 24 Sep.

## Round 1 — 25 Sep 2026

`[M]` Binary **`7dfd6a96`**, page **`87268f13`** (those delivered by phase 14), benches
`9264c52`+changes; Debian 13, labwc without a screen 3840x2160, i5-13500T with Intel UHD 770; Firefox
140.16.0 and Chrome 154.0.8037.57, real windows. From 04:09 to 06:12 (server time 02:09-04:12
UTC): **123 minutes** for the 8 suites and the technical layer, plus C14 (786 s). The longest test: F-030,
490 s, below the 10-minute cap.

**609 executions** in the log:

| pass | PASS | FAIL | BLOCKED | total |
|---|---|---|---|---|
| **healthy** (the one that counts for the matrix) | 256 | 42 | 7 | 305 |
| **with the fault** | 299 (fault **seen**) | 0 | 5 | 304 |
| **together** | 555 | 42 | 12 | 609 |

⇒ **no grafted fault escaped**: of the 304, 299 seen and 5 BLOCKED (the same cells blocked
in the healthy pass). **C14 GREEN** (the four boxes do not disturb each other).

**The non-green cells of the healthy pass** (all the others `ok` — F-001, F-003…F-008, F-010…F-012,
F-014…F-016, F-018, F-020, F-022, F-026…F-030, the paths A-F, the negatives N-1 N-3 N-4, C7, C18, and C9 on
gnome):

| | gnome ff/ch | kde ff/ch | xfce ff/ch | lxqt ff/ch | defect |
|---|---|---|---|---|---|
| **F-002** first image | ok / ok | ok / ok | FAIL / FAIL | ok / ok | D-010 (bench) |
| **F-009** accents, AltGr | ok / ok | FAIL / FAIL | ok / ok | ok / ok | D-008 |
| **F-013** video | FAIL / ok | ok / ok | FAIL / ok | FAIL / ok | D-006, D-014 |
| **F-017** re-attach same size | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | D-001 |
| **F-019** the network drops | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | D-002 |
| **F-021** «Esci» | FAIL (fault BLOCKED) / ok | FAIL / FAIL | ok / ok | ok / ok | D-003, D-005, D-016 |
| **F-023** inactivity | FAIL / ok | FAIL / FAIL | BLOCKED / BLOCKED | FAIL / ok | D-003, D-011 |
| **F-024** abandonment | ok / ok | ok / ok | BLOCKED / BLOCKED | ok / ok | D-011 |
| **F-025** same user, two tabs | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | FAIL / FAIL | D-002 |
| **C9** the log says whose | ok | BLOCKED | BLOCKED | BLOCKED | D-012 (bench) |
| **C19** the box stays clean | FAIL | FAIL | FAIL | FAIL | D-013 (bench) |

What was seen, in the log's words:
- **F-017** (8/8): the state is found again (window in the snapshot, strip of text, token unchanged) **but**
  the page says «Ammesso, sessione nuova, … desktop sconosciuto» to a resumed session;
- **F-019** (8/8): *«il filo cade e la pagina NON lo dice: desktop congelato senza una parola (si rientra
  solo ricaricando di propria iniziativa)»*; **F-025** (8/8) falls at point 3, the same thing;
- **F-023**: *«staccato per inattività, ma la pagina non lo dice»* (the farewell is there, at 12-13 s with the cap
  of 12 s; the page stays dressed as a desktop);
- **F-021** kde: the session ends clean, but **the re-entry is not clean** (Plasma reopens the program);
- **F-009** kde: *«RIPIEGO DICHIARATO: lo schema org.gnome.desktop.input-sources non c'è»* ⇒ the session
  stays English (US);
- **F-013** Firefox: gnome audible 89 %, lxqt 75 %, holes up to 0.3-0.4 s; xfce: the page's audio context
  **never** «running», 0 % for 40 s;
- **F-002** xfce: the full-resolution snapshot judged degenerate (62-72 colours, 98 % black: the box's
  background).

⇒ 42 FAIL and 12 BLOCKED brought back to **14 defects** (D-001…D-014): 8 of the product, 3 of the bench cured
at once, 3 to investigate or decide (`774595d`). During the clean-up five more were added
(D-015…D-019). Chrome Android: the user's column, by hand.

## The defects

From `banchi/15-suite/difetti.jsonl`, with the state written in the file. Classes: **A** real regression ·
**B** a desktop's assumption in the common code · **C** defect of the bench · **?** to be established.

| id | what is seen | where | class | state | cure · test |
|---|---|---|---|---|---|
| D-001 | after login the page always says «sessione nuova» and «desktop sconosciuto», even with a resumed session | all, ff and ch | A | in cure | `9ff4c1f` · `15-f016` (F-017 8/8) |
| D-002 | the line drops (or the frozen browser wakes up): the page stays frozen with the desktop, says nothing, does not go back to the form | all, ff and ch (F-019 8/8, F-025 8/8) | A | in cure | `c7a67ea` · `15-f019` |
| D-003 | after the farewell for inactivity (and after «Esci») a frame in flight re-dresses the page as a desktop: form hidden | F-023 on 4 cells, F-021 gnome/ff | A | in cure | `c7a67ea` · `15-f022` |
| D-004 | a session opened and never touched never expires for abandonment | code (`[R]`) | A | in cure | `9ff4c1f` · `15-f024b` |
| D-005 | KDE: after «Esci» the new login is not clean, Plasma reopens the program | kde, ff and ch | B | in cure | `aa4014d` · `15-f021` |
| D-006 | Firefox with a video: short and repeated sound holes (0.1-0.4 s); Chrome not | gnome/ff 89 %, lxqt/ff 75 % | A | to be confirmed on the real device | first cure removed (`b40856d`) · `15-f013` |
| D-007 | XFCE: re-attaching smaller, a large window stays partly beyond the border | xfce | ? | to be judged (the user) | — |
| D-008 | KDE: the browser's keyboard layout is not applied («è à ò ù é ç ° §» do not come out) | kde, ff and ch | B | in cure | `aa4014d` · `15-f009` |
| D-009 | with the server off the page takes 31 s to say «Non si collega» | all, ff | A | to be decided | `e719d08` · `15-n027` |
| D-010 | F-002 on XFCE: the black desktop judged degenerate without the «dark but alive» tolerance | xfce | C | cured | `15-f001` |
| D-011 | clocks on XFCE: the bench waited 45 s for the first «non-degenerate» frame without gestures, and the shortened inactivity closed the session | xfce, ff and ch | C | cured | `e670ee3` · `15-f022` |
| D-012 | C9 BLOCKED: the log's «forma» area (`src/forma.c`, phase 14) unknown | kde, xfce, lxqt | C | cured | `11-c9` |
| D-013 | C19 FAIL: the technical layer did not clear out the tenants between one link and the next | all | C | cured | `15-giro.py` |
| D-014 | XFCE with Firefox, video: the audio context never «running», 40 s of silence | xfce/ff | ? | not reproduced | `15-f013` (watches in round 2) |
| D-015 | GNOME: the negotiated layout is written into the **user's** dconf and stays there | gnome | B | open | `ddcf28d` `85697c9` · `15-f009`, `15-f031b` |
| D-017 | XFCE: the product writes into the user's xfconf channels entries that are not lock/reboot/suspend/stand-by, and deletes `~/.cache/sessions` | xfce | B | open | `85697c9` `7543c6a` · `15-f031b` |
| D-018 | LXQt: the product writes into `~/.config/lxqt/*.conf` and puts `Hidden` entries in the user's applications | lxqt | B | open | `85697c9` `e8115e5` · `15-f031b` |
| D-016 | F-021 gnome/ff BLOCKED: the empty log slice after «Esci» read as «not read», and the fault did not re-enter a live session | gnome/ff | C | cured | `c3741d3` · `15-f021` |
| D-019 | P-B and P-D on xfce/ch: after re-entry the image looked almost still (changes 0.9-1.6 %) | xfce/ch | C | cured | `2f6c0a2` · `15-f019` |

⚠ For D-015, D-017 and D-018 the file still says «aperto», but the cures are on the `bonifica-15` branch
(section «The clean-up»). For D-009 the cure is written after the user's decision. The bench's cures
(class C) are on `fase-10-cure`.

## The user's decisions of 25 September

Morning, after round 1. Also recorded in `DECISIONI.md` §8.

| defect | decision |
|---|---|
| **D-005** | the KDE remote session starts **empty** by itself (`loginMode=emptySession` in the session's folder); but if the user in Settings chose «restore the saved session», **their choice wins** |
| ⭐ **D-015, D-017, D-018** | *«le impostazioni utente non si toccano»* — on no desktop. Specified the same morning: *«Le impostazioni dell'utente non si toccano TRANNE quelle che riguardano blocco-schermo, riavvio sistema, sospensione e stand-by: queste sono impostazioni pericolose per altri utenti presenti sulla macchina»*. ⇒ Those four families are written into the user's settings (persistent); everything else (keyboard, menu entries, shortcuts, «Esci» visible, user switching, Ctrl+Alt+F…) holds **only for the remote session**, on the four desktops |
| **D-002** | the sentence *«il collegamento con il server si è interrotto: per rientrare scrivi di nuovo la parola d'ordine»* is fine |
| **D-009** | the server being off is said **at once** (~1 s, from the refusal of `/impronta`), not after the browser's 30 s |
| ⭐ **D-006** | *«concordo sulla soluzione D [dichiararlo], ma il problema va risolto con la soluzione B [decodificatore Opus nostro in WebAssembly nella pagina, per TUTTI i browser], che è la scelta che ci consente di avere un prodotto bugs-free»* ⇒ B is done **before round 2** |

## The clean-up

On the **`bonifica-15`** branch (`git log fase-10-cure..bonifica-15 --oneline`), the product's cures; the
bench corrections born on `fase-10-cure` are brought over with the «bonifica-15: …» merges.

| commit | what it cures |
|---|---|
| `9ff4c1f` | **D-001**: `SESSIONE` says `2 = RIPRESA` when that user's graphical session already existed at PAM's verdict, and the real name of the desktop (gnome/kde/xfce/lxqt). **D-004**: the abandonment clock starts at the **birth** of the stage (the re-attach does not renew it, decision of 16 Aug) |
| `e3c8804` | new test **F-024b** (`15-f024b-sessione-mai-toccata.py`): G7 server with `--abbandono-s 60`, no gesture ⇒ the line «§5.3 — ABBANDONO» within 90 s; fault = the default clock |
| `c7a67ea` | **D-002**: the closing of the transport without CONGEDO says the sentence decided by the user and goes back to the form. **D-003**: `torna_al_modulo()` closes the screen before removing the dress, the frames in flight are thrown away |
| `aa4014d` | **D-005**: KDE is born empty (the session's `ksmserverrc loginMode=emptySession`). **D-008**: the layout reaches KWin (the session's `kxkbrc` with `[$i]` + `org.kde.keyboard reloadConfig`); the false sentence of the fallback corrected |
| `202b514` → `b40856d` | **D-006**, first cure (the stale context time on Firefox): **removed**. `[M]` with the real browsers it got worse: lxqt audible 68 % (round 1: 75 %), hole 1.2 s, gnome FAIL |
| `e719d08` | **D-009**: `/impronta` refused by the network ⇒ «il server non risponde: è spento o non raggiungibile», without opening WebTransport; a slow server has no clocks |
| `ddcf28d` | **D-015** (GNOME): the layout and the session's keys in a **session dconf** (`DCONF_PROFILE`: `service-db:shm/remotix` on top, `user-db:user` below read-only), emptied at every birth |
| `85697c9` | **D-015/D-017/D-018**, the whole rule: GNOME the permitted ones (`sleep-inactive-*`, `idle-delay`, `lock-enabled`) to the user, the others to the session; XFCE a **session** xfconf (`locked` properties in a folder at the head of xfconfd's `XDG_CONFIG_DIRS`), `SessionName=REMOTIX` + `SaveOnExit=false` instead of `rm ~/.cache/sessions`; LXQt panel.conf and `Hidden` entries in the session's folders |
| `db117f4` | new test **F-031B** (`15-f031b-impostazioni-intatte.py`, once per desktop): dconf, xfconf, lxqt, applications, kxkbrc, `~/.cache/sessions` read from disk before the login and after «Esci»; fault = simulated persistent write |
| `7543c6a` · `a0101a6` | **D-017**: Suspend, Hibernate, Hybrid sleep are suspension ⇒ permitted, back in the user's channel; in the session 4 keys remain. The fault of `13-w2` redone |
| `e8115e5` | **D-018**: `lxqt-panel` at startup rewrote the user's panel.conf ⇒ now `--configfile $XDG_RUNTIME_DIR/remotix/lxqt-pannello.conf` |
| `5792418` `7fccca7` `f99b6e7` `0efffe4` `4382bbc` `cb7b025` `f0bbf01` | the bench realigned: log, C9, technical layer (D-012, D-013), D-016, D-019, D-011, the `suite` family |

⚠ What remains before round 2: **D-006 solution B** (Opus in WebAssembly), D-007 to the user's judgement,
D-014 watched. Then ⛔ freeze and **complete round 2**.

## Lessons

Seven defects **of the bench** found by the round itself: each one a green or a red that did not belong to the
product.

- **The snapshot on a black background** (D-010, D-011). The XFCE box's background is black, and in 4K the pixel
  judge says «degenerate» at every snapshot (62-72 colours, 98 % black). The first frame had the
  «dark but alive» tolerance, the full-resolution snapshot did not. ⇒ A judge must be tested **on all
  four** backgrounds, not on the most colourful one.
- **C9 and the «forma» area** (D-012). `src/forma.c` (phase 14) writes into the log an area that C9 did not
  know ⇒ BLOCKED on kde, xfce, lxqt. The whole net had not been redone after phase 14 (decision
  of 24 Sep): the first round finds it. The BLOCKED was honest: *«un verde che le ignora sarebbe un verde
  che non le ha guardate»*.
- **C19 and the clear-out** (D-013). The links delete their tenant **before** creating it, not
  after; `11-gancio.sh` clears out between one link and the next, the round's technical layer did not ⇒ C19 saw
  C9's tenants. It is the same lesson as phase 14's red C19: whoever redoes a round outside the
  hook must redo **the clear-out too**.
- **F-021 and the empty slice** (D-016). After «Esci» the log slice can be empty: empty does not mean
  «not read». And the pass with the fault must re-enter a **live** session, otherwise its
  gesture talks to a bus that is not there.
- **The shortened clock against the slow start** (D-011). At 12 s the inactivity was shorter than
  XFCE's birth in 4K (CONGEDO 0x02 right after the first frame); at 25 s still not, because the
  real cause was the bench photographing for 45 s without gestures. ⇒ In the phases with short clocks the first
  frame is looked at with a cap **shorter than the clock**. A shortened clock also shortens
  the bench's patience.
- **The fixed pauses against the animation** (D-019). The movement judge photographed every ~0.9 s,
  that is half a turn of `weston-simple-egl`'s triangle: snapshot always at the same point, «image
  still» with a live image. ⇒ **Irregular** pauses and comparison between **all** pairs.
- **The ear, innocent but inflating** (D-006). G4's ear replaces the page's audio
  connection: the suspicion was that Firefox's holes were its own. `[M]` measured **without the ear**
  (60 s, lxqt and kde): Firefox+video 3-5 re-arms even with the video in the worker, Firefox without video 0,
  Chrome 0, Firefox+video in PCM 0, server CPU 11-14 % ⇒ the defect is **real** (Firefox's Opus
  decoder), the ear does not create it. But it **inflates** it: F-013's percentages (75-89 %) are not
  the measure of the defect. And the first cure, written on a bench that did not resemble real Firefox, got worse with the
  real browsers: removed.

---

## ⭐⭐ ROUND 2 — 25 Sep 2026: ZERO DEFECTS

`[M]` Product and tests **frozen** at commit `d121715` (tag `fase15-giro2-congelato`), binary
**`b1443a0b`**, page **`942f2873`**; boxes redone from zero; 11:25 → 13:38 (133 minutes), the four
desktops in parallel, real Firefox 140 and Chrome 154, 3840x2160, plus the technical layer and C14.

| | executions | outcome |
|---|---|---|
| healthy passes | 329 | **329 PASS** — 0 FAIL, 0 BLOCKED |
| passes with the grafted fault | 328 | **328 faults seen** — none escaped |
| technical layer (C7 C9 C18 C19 × 4, C14) | included above | all green |

Functions covered: F-001…F-030 (F-031, touch on Android, stays the user's with the phone), F-018b and
F-018c (the windows inside the screen at re-attach at a different size, born with D-007), F-024b (the
never-touched session expires), F-031B (the user's settings intact after the remote session, and the
user manager clean), the paths A-F, the negatives N-1, N-3, N-4.

⇒ **The phase-15 gate is passed**: round 1 ⇒ 21 entries (14 of the product, 7 of the bench) ⇒ clean-up
⇒ round 2 at zero. All the entries are «verificato (giro 2)»; D-014 did not repeat.

**The report**, generated from the log and never written by hand:
`banchi/15-suite/rapporto-giro2.html` (and `.txt`), `banchi/15-suite/rapporto-giro1.html` (and `.txt`); the
whole log of all the rounds — round 1, cells redone, clean-up checks, general rehearsals,
round 2 — is `banchi/15-suite/registro.jsonl` (2455 lines, additions only), the defects
`banchi/15-suite/difetti.jsonl`; the evidence on the server in `/media/REMOTIX/misure/fase15/giro2/`.

**How to redo it**: `bash banchi/15-suite/15-porta.sh`, then on the server (with the boxes redone:
`bash …/15-suite/15-rifai-scatole.sh`) `python3 …/15-suite/15-giro.py --giro <nome> --strato-tecnico`;
or `bash banchi/11-scatole/11-gancio.sh gira --famiglia suite`. The report:
`python3 banchi/15-suite/15-rapporto.py --registro banchi/15-suite/registro.jsonl --difetti
banchi/15-suite/difetti.jsonl --giro <nome> --html <file>`.

### What entered the product with the clean-up

| defect | what was seen | the cure |
|---|---|---|
| D-001 | «sessione nuova» and «desktop sconosciuto» even with a resumed session | SESSIONE says RIPRESA (2) and the real desktop |
| D-002, D-021 | line dropped or browser frozen: page mute over the still desktop | the page says so and goes back to the form, also in the window between SESSIONE and the opening of the input |
| D-003 | after the detach or «Esci» a frame in flight put the desktop back over the form | `Schermo.chiudi()` at the farewell |
| D-004 | a never-touched session never expired | the abandonment clock starts at birth |
| D-005 | KDE reopened the programs after «Esci» | Plasma session empty by itself (unless the user chooses otherwise) |
| D-006 | sound holes with Firefox and a video (Firefox's Opus decoder) | **our own Opus decoder in WebAssembly** (libopus 1.5.2), for all browsers |
| D-007 | XFCE/LXQt: at a smaller re-attach windows partly off the screen | the product makes labwc bring the windows back inside |
| D-008 | KDE: the accents did not come out | the negotiated layout reaches KWin (the session's kxkbrc) |
| D-009 | server off: 31 s before «Non si collega» | said at once |
| D-015, D-017, D-018, D-020 | REMOTIX wrote into the user's settings and left traces in the user manager | the user's settings are not touched, except lock/reboot/suspend/stand-by; everything else holds only for the remote session and is removed at the end |

⚠ **What stays the user's**: the Android column (F-031) with the user's phone, and the judgement by ear
of Firefox's audio with the video on the tablet (D-006 is green in the suite; the final judge is the user).

### The user's hand test — 25 Sep 2026, afternoon

Binary `b1443a0b`, on the four real boxes (8511-8514). **Linux** (tablet, Firefox and Chrome):
all fine. **Android** (Galaxy S23+, Chrome): on the **2.4 GHz** Wi-Fi frame losses; `[M]` from the
page's diary and from the server: 0.6 % of packets lost (63 out of 9877), 37 frames skipped out of 2199
(1.7 %, always with the decoder caught up: arrivals in groups after the retransmissions), 222 bits of audio
never arrived — against 0 packets lost by the tablet in the same hours. On the **5 GHz** Wi-Fi: smooth
(the user), `[M]` 0 packets lost and 0 skipped on gnome, xfce and lxqt; on lxqt 7 skipped out of 4067.
⇒ It is not REMOTIX and it is not the phone's power: it is the 2.4 GHz network. ⚠ How REMOTIX behaves on a
network that loses 0.6 % of the packets remains a real question: it goes into **phase 16**.
