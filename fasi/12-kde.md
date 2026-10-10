# Phase 12 — KDE

*Opened on **18 Sep 2026**. Closed on —*

## What it must produce

The second desktop: **the same thing on Plasma** (`PIANO.md` phase 12). The user opens the browser and
sees their KDE desktop, as today they see GNOME.

⛔ **The rule of the phase, the user's, 18 Sep 2026**: *«Devi sviluppare KDE senza rompere ciò
che già funziona su GNOME.»* ⇒ The phase 11 net is not the final acceptance test: it is the **guardian** of
every step. We proceed by **increments**, and every increment goes through the same gates:

| | |
|---|---|
| **CP0** | the baseline: complete net on the four boxes, the same binary everywhere |
| **CP1** | the increment is defined: goal, invariant, modules, KDE test, client test, GNOME regressions to watch, criterion |
| **CP2** | GNOME and KDE **observed** at the point of the increment, and the difference written — nothing deduced |
| **CP3** | the minimal change designed: files, why, what of GNOME stays as it is |
| **CP4** | the KDE test done for real, on the declared scene |
| **client** | Chrome and Firefox on Linux, Chrome on the Android emulator — when the increment touches the path |
| **net** | the complete net, GNOME unchanged, the injected faults still caught |
| **checkpoint** | a commit that can be resumed |

⇒ A red on GNOME is **a regression until proved otherwise**, and it is classified:
A real regression · B GNOME assumption in the common code · C bench defect · D wrong
invariant (⛔ never as a shortcut).

## The decisions produced

- **19 Sep 2026, the user's**: *Android emulator on the server*. ⚠ It changes the August rule
  "SDK and emulator stay on the tablet" (`DECISIONI.md` §5-bis.0-ter): `[M]` the tablet (7.5 GB) cannot
  handle Android 17 — free memory at 170 MB, Chrome never started. The server has KVM, 20 processors,
  22 GB free. ⇒ The SDK is in `/media/REMOTIX/android` (disk: the server's system lives in RAM).
  ⛔ Firefox for Android stays NOT supported (§7.18); the **Chrome** of the
  Android 17 image (145) is tested, and Chromium is not (no H.264).
  ⛔ **Where we got to, `[M]` 19 Sep**: SDK in `/media/REMOTIX/android`, KVM "installed and
  usable", AVD `remotix37` seen; but **Chrome 145 does not start**: the focus stays on the launcher, no
  `chrome_devtools_remote` socket, and the emulated graphics abort (`Assertion failed:
  !rcEnc->featureInfo()->hasReadColorBufferDma`) with `-gpu swiftshader_indirect`; with `-gpu guest`
  the emulator does not even reach `adb`. Same block on the tablet ⇒ it is not memory.
- **19 Sep 2026, the user's**: *«alla fine farò io stesso i test come ultima verifica e
  validazione finale»* ⇒ the Android test on the emulator **stops here** (declared, not
  hidden): Android is validated by the user with his own Chrome. If it is resumed, one starts from the line above.
- **19 Sep 2026, the user's**: *«adesso ci occupiamo di KDE, LXQt verrà dopo — togli XFCE e
  LXQt»* ⇒ while working on KDE the net runs with `--scatola "gnome kde"`: the per-desktop meshes
  only on GNOME (the guardian) and KDE (the work). ⚠ The price, declared: for that time one does not
  see whether a change touches xfce and lxqt. C11 and C14 stay on the four boxes (alignment and
  isolation). We go back to the four when the next desktop is opened.
- `DECISIONI.md` §4.6-duodetricies — **one desktop per machine**; the choice among several desktops is
  postponed (`MASTERPLAN.md` M5).

## The bench — written before developing

The bench is **the net of phase 11** (`banchi/11-scatole/`), pointed at the `kde` box. The sign
that KDE is served is the one already written: **`C1(kde)` turns green**, and after it C2, C3, C4, C6,
C7, C8b, C9 on the same box.

⚠ **Three things of the bench that the phase must touch, declared here before touching them** (readings
of 18 September, `[R]`):

1. ⛔ **Three "gnome only" gates in the launch of the meshes** — `11-gancio.sh` (`le_cinque_nuove`, and
   the fast family that does C1 only on gnome) and `11-accendi.sh` (c8b exits 3 outside gnome). The
   comment that says *«il giorno che il prodotto saprà accendere KDE non c'è niente da togliere»* is
   false. ⇒ Opening them **softens no verdict**: it is the condition for the meshes to look at
   KDE. They are opened in the increment in which the corresponding mesh can turn green, not before.
2. ⚠ **The `kde` box does not contain Plasma**: only `kwin-wayland` and `xwayland`
   (`Contenitore.kde`). The product starts a Plasma session ⇒ the box grows, declaring it.
3. ⭐ **A KDE fault, invented and run** (`fasi/11-…` §3.6): today it does not exist.

## The increments

| # | goal | mesh that tests it | status |
|---|---|---|---|
| **0** | the baseline | the whole net | ✅ **PASS** 18 Sep |
| **1** | the Plasma session **is born** for a new user | none green yet: C1(kde) stays red (capture missing) — tested with the I1 measurement below | ✅ CP1 · CP2 · CP3 · CP4 · client (Firefox, Chrome) · net — ⚠ the bench's Android open |
| **2** | Plasma's image reaches the browser | ⭐ **C1(kde)** | ✅ CP1 · CP2 · CP3 · CP4 · client · net — ⭐ **C1(kde) GREEN** |
| **3** | mouse and keyboard reach Plasma | ⭐ **C4(kde)**, and C3 · C6 on kde | ✅ CP1 · CP2 · CP4 · client · net — ⭐ **C4(kde) GREEN** |
| **4** | the bench looks at KDE like GNOME | ⭐ **C2(kde)**, **C8b(kde)** | ✅ cure · certifications · tests · net — ⭐ **KDE: all meshes** |
| **5** | the clipboard on KDE | `07-b54 --scatola rete11-kde` + counter-test | ✅ tests · net |

### Increment 1 — the Plasma session is born

| | |
|---|---|
| **GOAL** | a user who connects for the first time, on a machine that has **only** Plasma, gets from the product a Plasma session **of their own**, without a physical screen, the size of their browser window — and the product **recognises it alive**. ⛔ No capture, no input: those are the next increments |
| **INVARIANT** | on a machine with GNOME **nothing changes**: same state read, same drop-in, same command, same times. And on KDE no second session, no leftovers after closing (C7) |
| **MODULES** | `src/sessione.c` (recognise the installed desktop; give birth to Plasma; say "alive" by reading KWin) · `banchi/11-scatole/Contenitore.kde` (the box receives Plasma, declaring it) |
| **KDE TEST** | in the `kde` box, a real client (`01-b3-cliente.py`) gets in with a new user ⇒ within C1's cap (26 s): `kwin_wayland --virtual --width W --height H` **with the client's size**, `plasmashell` alive, **one** `wl_output` W×H (`wayland-info` on the user's socket), and the product's log saying the session is alive. **Negative check**: with today's binary, on the same scene, none of this |
| **CLIENT TEST** | the image on KDE is not there yet ⇒ on KDE the browser has nothing to show. ⚠ But `sessione.c` is on the path of **every** birth ⇒ Chrome and Firefox on Linux and Chrome on the emulator connect to the **GNOME** box and must see the desktop as before |
| **GNOME REGRESSIONS** | the whole net; in particular C1(gnome)×10 (birth and times), C6 (detach and reattach: the session state), C7 (closing) |
| **CRITERION** | KDE TEST green and negative check red · clients on GNOME green · whole net like the baseline, **except** what the increment changes on purpose — and C1(kde), which may change the reason for its red ("born, but without image"), not its colour |


#### CP2 — observed, not deduced (`[M]` 18 Sep 2026, inside `rete11-kde`)

| | GNOME (from the product, baseline) | KDE (v1's recipe by hand with `banchi/12-i1-osserva-plasma.sh`, then from the product) |
|---|---|---|
| who is born | `gnome-session` → `org.gnome.Shell@wayland` with the drop-in `--headless --no-x11` | `startplasma-wayland` → `plasma-kwin_wayland.service` with the drop-in `--xwayland --virtual --width W --height H --no-lockscreen` |
| monitors at birth | ⛔ **zero**: the monitor is mounted by the capture (`RecordVirtual`) | ⭐ **one**, `Virtual-0`, of the line's size — `[M]` 1600x900 requested ⇒ 1600x900, a single `wl_output` |
| how long it takes | ~1 s (C1) | KWin on the bus **0.79 s**, `plasmashell` **1.31 s** |
| the card | Intel | `OpenGL renderer string: Mesa Intel(R) UHD Graphics 770` — ⭐ GPU, not llvmpipe |
| closing | `loginctl terminate-user` cleans up | ⭐ **0 processes in 529 ms**, `/run/user` gone |

⇒ **DIFFERENCE**: on KDE the output is born with the session and the size is that of the **first** client;
it no longer changes while the session lives. ⇒ **DECISION**: the product writes the size in the drop-in
at birth (on GNOME the line does not carry it, and stays that way).

⛔ **An observational dead end, written so that it is not paid for again**: the first attempt was
installing Plasma **by hand inside the running box** (`apt-get install`). ⇒ `polkitd` was born outside
the groups recipe (`LEZIONI.md` §1.54) and died, and `loginctl` began to answer
*«Connection timed out»*: `terminate-user` no longer closed anything (20 processes alive after 55 s).
⭐ With the box **rebuilt from the recipe** (R2 in `Contenitore.kde`) the defect is not there.
⇒ It was not Plasma: it was the box made by hand.

#### CP3 — the minimal change

| file | what | GNOME |
|---|---|---|
| `src/sessione.h` | `SessioneDesktop`, `sessione_desktop()`, the three Plasma constants | nothing |
| `src/sessione.c` | `sessione_desktop()` (once per process: KDE **only** if `startplasma-wayland` is there and `gnome-session` is not); `sessione_viva`/`sessione_stato` on KWin; environment (`XDG_MENU_PREFIX=plasma-`, no GNOME variables); drop-in of KWin's unit **with the size**; command; unit to wait for; exit (`org.kde.Shutdown.logout`, then `StopUnit` by force); settings and inhibition **declared postponed** | ⭐ every GNOME branch is textually as it was: the new lines sit **before** and return, or choose a name |
| `src/main.c` | a start-up line: which desktop, and why | one more line in the log (`avvio`, not the session area ⇒ C9 does not look at it) |
| `Contenitore.kde` | `plasma-workspace plasma-desktop` (R2) | nothing |

⚠ **Postponed, and declared in the product's log**: Plasma's settings (suspend,
KIOSK menu) and the inhibition via powerdevil. The desktop lock is already off from the start-up line.

#### CP4 — the KDE test (`[M]` 18 Sep 2026, binary `6693555c`)

Test by hand with `banchi/12-i1-nasce-plasma.sh` (inside the box: a real `01-b3-cliente.py` client, new user `ki1`):

| | expected | measured |
|---|---|---|
| the user's `plasmashell` | within 26 s | ⭐ **2.59 s** from the client's start |
| KWin | `--virtual`, the client's size | ⭐ `Virtual-0` **1920x1080** = the canvas declared by the client |
| sessions born | one | ⭐ **one** (`startplasma-wayland` ×1) — the units guard holds |
| the product sees it alive | yes | ⭐ last «nessun KWin sul bus» at +0.8 s, then no more |
| closing | no leftovers | ⭐ 0 processes in 527 ms |
| ⛔ **negative check**: baseline binary `bfc5936a`, same box, same scene | nothing | ⭐ `plasmashell` **NEVER**, 0 Plasma processes |

⇒ After the birth the child tries to mount the capture and says *«Mutter non espone RemoteDesktop»*:
**expected**, it is increment 2.

#### The real clients on GNOME (`[M]` 18 Sep 2026, binary `6693555c`, `banchi/12-client-veri.py`)

New user `i1cli` in the `gnome` box (port 8511), `muovi` scene, headless, server log read with `--registro-cmd`. The bench was **certified** beforehand (`--certifica`): empty port ⇒ red on all three, wrong password ⇒ red by refusal on Firefox and Chrome, pixel judge ⇒ degenerate black and gradient not.

| browser | a · b · c · d · e · f · g | verdict |
|---|---|---|
| Firefox 140 ESR (Linux) | 0 · 0 · 0 · 0 · 0 · 0 · 0 — 7 input lines in the server log, photo = the GNOME desktop | ⭐ **PASS** |
| Chrome 153 (Linux) | 0 · 0 · 0 · 0 · 0 · 0 · 0 — 8 input lines in the server log | ⭐ **PASS** |
| Chrome 113 on the Android 14 emulator | 0 · **1** · 3 · 3 · 3 · **1** · 3 — *«Opening handshake failed»*, `net::ERR_METHOD_NOT_SUPPORTED` on `/rcp/1` | ⛔ **FAIL — class C, it was already there** |

⇒ **Android, why it is not a regression**: the server opens the WebTransport session and the
emulator's Chrome never opens the control channel (farewell `0x0d` after 5 s): the fault lies
**before** the login, where `sessione.c` does not reach. ⭐ **Check**: the baseline binary
`bfc5936a` put back in the box, same scene ⇒ **same FAIL, same lines**. Then put back
`6693555c` (md5 identical in the four boxes). ⇒ It is the Chrome 113 of the emulator's system
image, forty versions behind the desktop Chrome. ⚠ **Open**, it is a hole
in the bench and not in the product: the Android leg must be redone (the user's decision, see below).

⚠ Two bench defects, found and cured in the same test: Marionette does not have
`WebDriver:TakeElementScreenshot` (`TakeScreenshot` with `id` is used) ⇒ Firefox gave 3 on (c) and (g);
and without `--registro-cmd` Chrome gave 3 on (e). Neither one is a gifted green: they were 3.

⚠ The page writes *«desktop sconosciuto»* on GNOME too: it is fixed in `src/rcp.c` («in fase 1 non
c'è compositore»), not touched by this increment. ⇒ To be revisited when the product can say
which desktop it has started.

#### The whole net (`[M]` 18 Sep 2026, 19:53→22:06, binary `6693555c`, 7 969 s)

| | |
|---|---|
| GNOME | ⭐ **all green**, like the baseline |
| kde · xfce · lxqt | like the baseline: ⛔ only C1×10 red. ⭐ **C1(kde) changed reason, not colour**: 10 out of 10 *«la sessione è partita e nessun testimone del monitor ha parlato»* (CIECA) — it is "born, but without image", I1's criterion. C7(kde) green **with Plasma that is now really born** |
| net, on the server | C11 · C13 · C14 green (md5 identical in the four) |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |
| injected faults | ⭐ **25 out of 25 seen** (24 on the boxes, 1 on the laptop) |

⇒ **Increment 1: CRITERION met** on KDE, GNOME and the net; the bench's Android leg is
red for a reason that was already there (check done) and is declared open.

### Increment 2 — Plasma's image reaches the browser

| | |
|---|---|
| **GOAL** | in the Plasma session of increment 1 the child takes the frames from KWin and sends them to the client: the browser **sees** the KDE desktop. ⛔ No input (increment 3), no clipboard |
| **INVARIANT** | on GNOME the stage is mounted **as today**: same sequence towards Mutter, same log lines, same C1 times. The KWin/Mutter choice is made **once**, with increment 1's `sessione_desktop()` — no second way of recognising the desktop |
| **MODULES** | ⭐ new `src/kwin.c` — from v1's `fondamenta/remotix-c/src/kwin.c`: the Wayland protocol `zkde_screencast_unstable_v1` (`stream_output` on the `Virtual-0` output ⇒ PipeWire node), METADATA cursor · `src/figlio.c` (mounts/unmounts the stage: Mutter **or** KWin; afterwards, `cattura_avvia(nodo)` is the same) · `src/Makefile` (`wayland-scanner`, `wayland-client`) · the permission: a `.desktop` with `X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1`, as it was in v1 · `src/cattura.c` **only if** CP2 measures that it is needed (v1: KWin's fence, 830 buffers out of 830 not ready) |
| **KDE TEST** | ⭐ **C1(kde)×10 GREEN** — the usual mesh, no new mesh: 10 new users, session born **with a monitor** and frames within the cap. And a photo of the Plasma desktop taken from the browser |
| **CLIENT TEST** | Firefox and Chrome Linux on the **kde** box (a·b·c·d·f·g green; (e) input stays red/3, it is increment 3) and on the **gnome** box (like increment 1). Android: see the open decision |
| **GNOME REGRESSIONS** | the whole net; in particular C1, C3, C6 (the stage is remounted after the detach), C8b |
| **CRITERION** | C1(kde) green · clients on kde see Plasma · whole net as after I1 **except** C1(kde) green · GNOME unchanged · faults all caught. ⚠ The "gnome only" gates of C3/C8b are **not** opened here if they require input |

#### CP2 — observed (`[M]` 18 Sep 2026, inside `rete11-kde`, `banchi/12-i2-cancello.sh`)

| | GNOME | KDE |
|---|---|---|
| who gives the PipeWire node | Mutter, D-Bus `ScreenCast.RecordVirtual` (`mutter.c`) — a **new** monitor of the requested size | KWin 6.3.6, **Wayland** protocol `zkde_screencast_unstable_v1` **v5**, `stream_output` on the output that already exists (`Virtual-0`) |
| the gate | none | ⛔ the global **is not there** for an arbitrary client (58 others are); ⭐ it is there with a `.desktop` in `/usr/share/applications` that declares `X-KDE-Wayland-Interfaces` and has `Exec=` on the canonical executable — **even written with the session already alive** (+3 s). `XDG_MENU_PREFIX=plasma-` in KWin's environment: yes (since increment 1) |
| the size | follows the requested canvas | ⛔ **fixed**: the output is the size of the first client and KWin 6.3.6 does not resize it (v1: `kwin!7932`, expected for 6.8). `[M]` asking 1384x912 of a 1388x914 output ⇒ PipeWire `no more input formats` ⇒ stage **never again** mounted |
| the first frame | the Shell | ⭐ the **Plasma splash screen** («Plasma made by KDE», 99 % black + logo) for ~2.4 s, then the desktop. `[M]` waiting for `org.kde.plasmashell` on the bus does **not** avoid it (the name arrives earlier) ⇒ tried and **removed** |
| the rest of the route | `cattura.c` → `codificatore.c` | ⭐ **the same**: from the node onwards nothing changes. `cattura.c` already discards the `SPA_CHUNK_FLAG_CORRUPTED` buffers (KWin's cursor-only buffers, v1 §4.7) |

⚠ **Not measured and declared**: KWin's *fence* (v1: 830 buffers out of 830 arrive with drawing
in progress). The photos taken from the browser show no tearing, but a photo is not a
measurement: it stays open for when the numbers are looked at.

#### CP3 — the change

| file | what | GNOME |
|---|---|---|
| ⭐ `src/kwin.c`, `src/kwin.h` (new) | from v1's `fondamenta/remotix-c/src/kwin.c`, **only the capture**: registry, output, `stream_output` with the METADATA cursor, wait for the node (5 s), Wayland pump, closing; and `kwin_scrivi_permesso()` | not called |
| `src/protocolli/zkde-screencast-unstable-v1.xml`, `src/Makefile` | v1's XML; `wayland-scanner` generates the code at every build; `wayland-client` among the libraries | one more library in the binary (it is in all four boxes: `ldd` 0 missing) |
| `src/main.c` | at start-up, **only on KDE**: the server writes `/usr/share/applications/org.kde.remotix.desktop` with `Exec=` on its own binary (the child is an `execve` of the same) | nothing |
| `src/figlio.c` | `palco_kwin` next to `mut`: on KDE `kwin_apri()` in place of `mutter_apri()`, then `cattura_avvia(nodo)` as it was; `misura_del_palco()`: on KDE the capture asks for the output's size, and the canvas change answers with that ("the page rescales", §4.5) | ⭐ the `else` branch is the previous code, textually; `nodo_del_palco(mut)` = `mutter_nodo(mut)` |

#### CP4 — the KDE tests (`[M]` 18 Sep 2026, binary `8694ec33`)

| | measured |
|---|---|
| C1(kde)×3 (`11-accendi.sh c1 kde 3`) | ⭐ **GREEN** 3 out of 3, monitor «Virtual-0» (1 after), ~150 frames — the first time |
| Firefox Linux, new user, `kde` box | ⭐ **PASS** 7 out of 7: splash screen at 0.9 s, Plasma desktop at 3.3 s; reconnection in 0.3 s |
| Chrome Linux, same session | a·b·c·e·f·g green · ⛔ (d) 0 frames moving the mouse — ⭐ **expected**: the input reaches the server (e) but not yet KWin (increment 3), and the cursor is drawn by the page ⇒ the desktop does not change |
| ⚠ (e) on KDE | the bench proves that the input reaches **the server**, not the desktop: on KDE the child says *«il canale di input NON si apre»*. The green of (e) here does **not** mean "it can be controlled" |
| before the size cure (`b835dc63`) | ⛔ Chrome's reconnection asked for 1384x912: `no more input formats`, stage never again mounted, 0 frames in 30 s ⇒ cured with `misura_del_palco()` |

⚠ **The clients' bench has changed** (`12-client-veri.py` (c)): a single photo at +1 s judged
Plasma's splash screen; now photos are taken **up to the cap** and it is written when the
desktop arrived and how many degenerate photos preceded it. Recertified (`--certifica`: empty port,
wrong password, pixel judge — all caught). ⚠ The "degenerate up to the cap" branch has no
certification test of its own: it is declared.

#### The whole net (`[M]` 18→19 Sep 2026, 22:41→00:50, binary `8694ec33`, 7 710 s)

| | |
|---|---|
| GNOME | ⭐ all green **except C9** — ⛔ and C9 was **mine**: the only line without an owner was *««i1cli» ricontrollato…»*, that is the client test's session left alive in the box while C9 counted its two tenants (class **C**). ⭐ With the session closed, **C9(gnome) alone: outcome 0**, 631 mandatory lines out of 631 with the name |
| ⭐ **kde** | **C1(kde)×10 GREEN** — 10 out of 10 born with «Virtual-0», 155-174 frames; C5, C7, C8, C9 green, faults seen |
| xfce · lxqt | like the baseline: only C1×10 red |
| net, on the server | C11 · C13 · C14 green |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |
| injected faults | ⭐ 24 seen on the boxes + 1 on the laptop |

⇒ **Increment 2: CRITERION met.** ⚠ A lesson of method: the users of the tests by hand are
closed **before** launching the net — the net looks at the whole log, even what is not its own.

### Increment 3 — mouse and keyboard reach Plasma

| | |
|---|---|
| **GOAL** | what the user does in the browser (pointer, buttons, keys, wheel) reaches the Plasma desktop |
| **INVARIANT** | on GNOME the input channel is born and heals as today (`mutter_eis_fd`, `mutter_eis_riattacca`, the region by key, the wheel with `UNITA_PER_DELTA`) |
| **MODULES** | `src/kwin.c` (v1's `connectToEIS(7)`, the token, the healing) · `src/input.c` (three points: the descriptor, the region, the wheel) · `src/figlio.c` (which channel to open) · the bench: the "gnome only" gate of `11-gancio.sh` |
| **KDE TEST** | ⭐ **C4(kde) green** — the key gets all the way to the screen, the usual mesh — and its two faults seen |
| **CLIENT TEST** | Firefox and Chrome Linux on `kde` and on `gnome`: 7 out of 7 |
| **GNOME REGRESSIONS** | the whole net; in particular C4, C6 (the healing of the input), C8b |
| **CRITERION** | C4(kde) green · the meshes that can now be green on KDE are, and their faults are seen · GNOME unchanged |

#### CP2 — observed (`[M]` 19 Sep 2026, binary `a77366b2`, `kde` box)

| | GNOME | KDE |
|---|---|---|
| who gives the channel | Mutter, `RemoteDesktop.Session.ConnectToEIS` | ⭐ KWin, `org.kde.KWin.EIS.RemoteDesktop.connectToEIS(7)` ⇒ descriptor + token — granted at the first go, no permission to ask |
| the region | by key (`mapping-id`) | ⭐ *«regione del puntatore per geometria: 0,0 1384x912 (di 1, mapping-id «assente»)»* — the branch `input.c` already had |
| the wheel | `scroll_delta` / 12 | `scroll_discrete` in units of 120 (v1: `scroll_delta` on KWin does not make clicks) — ⚠ **not yet measured** by a mesh |

#### CP4 — the KDE tests

| | measured |
|---|---|
| Chrome and Firefox Linux on `kde` | ⭐ **PASS 7 out of 7** both; (d) moving the mouse **76** new frames in 8 s (before the input: 0) |
| ⭐ **C4(kde)** | **GREEN**: the expected area goes from the starting colour to the arrival colour at 100 %, the frame changes by 0 % |
| C4(kde) faults | `--senza-tasto` ⭐ seen · `--scena-sorda` ⭐ seen |
| ⭐ **C3(kde)** | **GREEN** (10 994 frames in 187 s, 60 pairs out of 60 different); `--fotogramma-ripetuto` ⭐ seen; `--scena-ferma` holds |
| ⚠ C3(kde) `--codificatore-fermo` | **3**, does not judge: the injection (SIGSTOP 2 s after the encoder is working) falls on Plasma's splash screen and the last frame is almost black ⇒ **skipped on KDE, declared** in the hook. C3's fault on KDE stays `--fotogramma-ripetuto` |
| ⭐ **C6(kde)** | **GREEN** (it finds itself again); `--uccidi-la-sessione` ⭐ seen (*«specie: un'altra sessione»*) |
| C2(kde) | **3**: the first 12 frames are the splash screen, and C2 takes them for its "before" ⇒ **skipped on KDE, declared**: the bench is adapted in an increment of its own |
| C8b(kde) | stopped by `11-accendi.sh` (*«il prodotto avvia solo GNOME»*) ⇒ **skipped, declared**: same increment |

⇒ **The bench**: `11-gancio.sh` `le_cinque_nuove` opens `kde` for C3, C4, C6 (with the faults that are seen) and
keeps it closed for C2, C8b and for the "encoder stopped" fault, each with its reason in the
log; xfce and lxqt stay closed.

#### The whole net (`[M]` 19 Sep 2026, 01:33→03:58, binary `a77366b2`, 8 698 s)

| | |
|---|---|
| GNOME | ⭐ **all green**, C9 included (users of the tests by hand closed beforehand) |
| ⭐ **kde** | **all green**: step 0, C1×10, C3 (+ still scene), **C4**, C5, **C6**, C7, C8, C9 — and the faults of C3, C4 (×2), C6, C5, C7, C8, C9 seen. Skipped, declared: C2, C8b, C3 "encoder stopped" |
| xfce · lxqt | like the baseline: only C1×10 red |
| net, on the server | C11 · C13 · C14 green |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |
| injected faults | ⭐ **28 seen** on the boxes (they were 24: the 4 new ones are KDE's) + 1 on the laptop |
| clients on GNOME, binary `a77366b2` | Firefox and Chrome **PASS** 7 out of 7 |

⇒ **Increment 3: CRITERION met.**

### Increment 4 — the bench looks at KDE like GNOME (C2, C8b)

⛔ **Bench only, no product**: the binary stays `a77366b2`.

| | |
|---|---|
| **GOAL** | C2 and C8b judge on KDE too |
| **THE CAUSE, `[M]`** | both took the "before" from the very first frames of the stream, and on KDE those are Plasma's splash screen (~2.4 s, 100-200 black frames). C2 looked at 12 of them, C8b at 1 ⇒ "I don't know" forever |
| **THE CURE** | the same rule in both, and it holds for every desktop: the "before" is the **first non-black frame** among the first 240. C2 already had it (`scegli_il_prima`) — only the number is raised, from 12 to 240; C8b receives it (`estrai(…, giudice)`). ⛔ If they are all black it stays "upstream" / "I don't know", as before; if the first non-black one is already the page, "already magenta" and it does not judge |
| **GNOME** | ⭐ unchanged: the first drawn is frame **1** (C2 writes it: *«fotogrammi guardati per il prima: 1»*) |
| **certifications** | `--certifica` of C2 and of C8b: exit 0 |

| `[M]` 19 Sep 2026 | outcome |
|---|---|
| C8b(kde) | ⭐ **GREEN**, 2 out of 2 see the page from the client — the "before" is frame 181 |
| C8b(kde) `--senza-cura` | ⭐ fault **seen** (1 out of 2 does not see it, and the first does) |
| C8b(gnome) | ⭐ GREEN, 2 out of 2 |
| C2(kde) | ⭐ **GREEN** — the "before" among 204 frames |
| C2(kde) `--applicazione-che-muore` · `--finestra-che-non-si-apre` | ⭐ both **seen** |
| C2(gnome) | ⭐ GREEN, "before" = frame 1 |

⇒ The gates: `11-gancio.sh` opens C2 and C8b to `kde`; `11-accendi.sh` lets C8b run on `gnome` and
`kde`. ⚠ Only C3's "encoder stopped" fault stays closed on KDE (the injection falls during the
splash screen): curing it means moving the moment of injection, and it is a step of its own.

#### The whole net (`[M]` 19 Sep 2026, 04:50→07:48, binary `a77366b2`, 10 645 s)

| | |
|---|---|
| GNOME | ⭐ **all green** (C2 and C8b with the new bench: the "before" stays frame 1) |
| ⭐ **kde** | **all green, and now all ten meshes are there**: step 0, C1×10, **C2**, C3 (+ still scene), C4, C5, C6, C7, C8, **C8b**, C9 — faults seen. Skipped, declared: only C3's "encoder stopped" fault |
| xfce · lxqt | like the baseline: only C1×10 red |
| net, on the server | C11 · C13 · C14 green |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |
| injected faults | ⭐ **31 seen** on the boxes (they were 28: the 3 new ones are C2 ×2 and C8b on KDE) + 1 on the laptop |

⇒ **Increment 4: CRITERION met.**

### Increment 5 — the clipboard on KDE

| | |
|---|---|
| **GOAL** | copy and paste of text in both directions, browser ↔ Plasma desktop, as on GNOME (the user's decision, 19 Sep) |
| **INVARIANT** | on GNOME the clipboard stays `appunti.c` as it was: the shell hands over to KDE with one line at the top of every public function, only if `kde` is there |
| **MODULES** | ⭐ `src/appunti_kde.c` and `src/appunti_kde.h` (from v1's `fondamenta/remotix-c/src/appunti_wlr.c`: `zwlr_data_control_manager_v1`, **no** permission to ask) · `src/appunti.c` and `src/appunti.h` (`appunti_apri_kde()` and the hand-overs) · `src/kwin.c` and `src/kwin.h` (`kwin_display_apri()` exported) · `src/figlio.c` (which one to open) · `src/Makefile` + `src/protocolli/wlr-data-control-unstable-v1.xml` · the bench: R3 `wl-clipboard` in the gnome and kde recipes, `07-b54-appunti-due-versi.py --scatola` |
| **SHAPE** | the same as GNOME: TEXT ONLY (`DECISIONI.md` §5-ter.1), the same row of types, the same cap, the same memory of the last text, and if the client has nothing the session gets ITS own text back. v1's traps carried over: the echo (state criterion), the full roundtrip before reading, `POLLHUP` = ready, the minimal step towards klipper, never `x-kde-onlyReplaceEmpty` |

| `[M]` 19 Sep 2026, binary `954a208c` | outcome |
|---|---|
| `07-b54 --scatola rete11-kde`, Firefox and Chrome | ⭐ **session→client ⭐ · client→session ⭐ · keyboard after the paste ⭐**, both |
| ⛔ **counter-test**: binary `a77366b2` (without the KDE clipboard), same scene | ⭐ **red in both directions** — the bench tells them apart |
| `07-b54 --scatola rete11-gnome` | Chrome ⭐⭐⭐ · Firefox: direction A ⛔ — ⚠ **it was already there**: same red with binary `a77366b2` ×2, and with Chrome **alone** on a new session. ⇒ It is "the FIRST connection on a GNOME session just born": `wl-copy`'s copy does not even reach the log (Mutter announces nothing). Hypothesis, **not proved**: `wl-copy` on Mutter has no data-control and without a focused surface it does not copy ⇒ bench. **Open**, outside KDE |
| whole net, binary `954a208c` (08:07→11:05, 10 637 s) | GNOME and KDE **all green**, xfce/lxqt like the baseline, C11 · C13 · C14 green, **31 faults seen** |

⚠ **Not yet in the net**: the clipboard has no phase 11 mesh. It is tested by `07-b54`
with the counter-test, and the day it enters the net it will be a mesh of its own.

### Increment 6 — C3's "encoder stopped" fault on KDE too

| | |
|---|---|
| **GOAL** | the last fault closed to `kde` (the user's decision, 19 Sep: «anche questo punto va fatto») |
| **THE CAUSE** | Plasma's splash screen animates for ~2.4 s: `aspetta_che_i_fotogrammi_arrivino` passed on the animation, and the SIGSTOP fell on the black |
| **THE CURE** | in the bench, not in the product: `11-c3` waits for the encoder **to stop** (`aspetta_che_il_desktop_si_fermi`) before turning on the scene, plus a 2 s breath before the injection (`--respiro-innesco`), counted in `secondi_prima`. On GNOME the desktop is already still ⇒ a single step. No question about the desktop |
| **THE GATE** | `11-gancio.sh` opens the "encoder stopped" fault to `kde` |

#### The net (`[M]` 19 Sep 2026, 13:21→15:51, binary `954a208c`, `--scatola "gnome kde"`, 9 028 s)

| | |
|---|---|
| GNOME | ⭐ **all green**, C3 "encoder stopped" included (with the new bench) |
| ⭐ **kde** | **all green, and now no fault is skipped**: step 0, C1×10, C2, C3 (+ still scene), C4, C5, C6, C7, C8, C8b, C9 — ⭐ **C3 "encoder stopped" seen** |
| net, on the server | C11 · C13 · C14 green |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen — ⚠ C16 was red because of three abbreviated paths (of the kind "kwin.c/.h") in this document: class C, written out in full |

### Suspend — it was already closed, and for all desktops

The user (19 Sep) proposes: *«perché non si fa in modo che remotix disabiliti alla radice standby,
reboot e suspend della macchina per tutti gli utenti normali, cioè tutti eccetto root?»* ⇒ ⭐ **it is
already so**, and from a decision of his: `DECISIONI.md` §4.7 (15 August), three belts put in place by
`src/provisiona.sh` — polkit (12 actions, `*-multiple-sessions` included), `AllowSuspend=no`,
logind on the keys. None of the three knows which desktop is running.

`[M]` 19 Sep 2026, on the server, as `nicfio`: `CanSuspend` · `CanReboot` · `CanPowerOff` ·
`CanHibernate` = **"no"** all four.

⚠ **The server's physical monitor** may keep going into standby (clarified with the user): the
remote sessions each have their own virtual screen.

⚠ **One piece remains, and it is a different one**: the screen **of the remote** Plasma session, which
powerdevil turns off after 10 minutes of inactivity (on GNOME the same thing is turned off by
`sessione_impostazioni()`). It is the KDE branch of `sessione_inibisci()` — increment 7.

### Increment 7 — the screen of the remote Plasma session does not turn off

| | |
|---|---|
| **GOAL** | powerdevil does not turn off the remote session's screen after 10 minutes (on GNOME `sessione_impostazioni()` already does it) |
| **MODULES** | `src/sessione.c`: `guardia_di_powerdevil()`, a thread that every 2 s looks at who owns `org.kde.Solid.PowerManagement` and asks `PolicyAgent.AddInhibition(4)` every time the owner **changes** · the bench: `banchi/12-i7-schermo.sh` · the box: R4 `powerdevil` in `Contenitore.kde`, `--cap-add=WAKE_ALARM` in `11-accendi.sh` |
| **INVARIANT** | on GNOME `sessione_inibisci()` stays as it was: the thread is born only if `e_kde()` |

⛔ **Two discoveries**, `[M]` 19 Sep 2026:
1. **in the box powerdevil did not start**: its executable carries `cap_wake_alarm=ep`, beyond the
   container's limit ⇒ 203/EXEC «Operation not permitted». Class C: `--cap-add=WAKE_ALARM`,
   which brings the box closer to the real machine.
2. **a single call arrives too early** (binary `6a41a28e`): when the stage is ready
   powerdevil is not there yet («ServiceUnknown» — it is a unit of `plasma-core.target`, it is not activated
   from the bus). And the child has no GLib loop ⇒ a watching thread, instead of `g_bus_watch_name`.

| `[M]` 19 Sep 2026, `12-i7-schermo.sh`, judge **powerdevil itself** (`HasInhibition`) | outcome |
|---|---|
| ⛔ counter-test: binary `954a208c` (without the branch) | **false** — the screen would turn off |
| binary `6a41a28e` (a single call) | **false** — «ServiceUnknown» |
| ⭐ binary `c7b228c5` (the thread) | **true** |
| ⭐ `c7b228c5`, powerdevil killed with the session alive | systemd restarts it ⇒ **true** again, the child asked the new owner for it |

#### The net (`[M]` 19 Sep 2026, 15:59→18:30, binary `c7b228c5`, `--scatola "gnome kde"`, 9 030 s)

| | |
|---|---|
| GNOME | ⭐ **all green** |
| ⭐ **kde** | **all green**, no fault skipped — and in the box's log **20** inhibitions asked of powerdevil, **0** refused, **0** "did not appear" |
| net, on the server | C13 · C14 green · ⛔ **C11 red, class C**: the new binary had been put only in gnome and kde, xfce and lxqt still had `954a208c` — the mesh did its job. `c7b228c5` put there too ⇒ C11 **green** |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |


### Increment 8 — the clipboard enters the net (C17), and a defect of all desktops

| | |
|---|---|
| **GOAL** | KDE's clipboard checked at every net, no longer only by hand (`07-b54`) |
| **THE MESH** | `banchi/11-scatole/11-c17-gli-appunti-vanno-nei-due-versi.py`: three facts with their names — **A** device → session (`wl-paste` reads what the client announced) · **B** session → device (`wl-copy`, and the server announces it to the attached client) · **R** whoever reattaches receives it. Injected fault `--senza-copia` ⇒ three reds |
| **THE REFEREE** | `wl-clipboard` wants `zwlr_data_control_manager_v1` (or `ext_…`): KWin has it, Mutter does not. ⛔ `[M]` on GNOME `wl-paste` and `wl-copy` stay hung (exit 124) while the server writes «22 byte consegnati alla sessione» ⇒ the mesh asks `wayland-info` and, if it is missing, exits **3** saying so. No per-desktop gate in the hook |

⛔⛔ **The defect found, and it belongs to ALL desktops** (`src/rcp.c`, twin copy in `banchi/rcp/`):
a client that reattaches to a live child makes the desktop's clipboard be reread, but the reading
arrives while the RCP session is still in `attesa-verdetto`. The text was kept "for whoever will
attach" and **nobody ever announced it**: whoever came back did not know what was in the
clipboard. ⇒ `annuncia_il_tenuto()`, called as soon as the session moves to `S_ATTIVA` (§2.5: after
`SESSIONE`).

| `[M]` 19 Sep 2026, `kde` box | A | B | R |
|---|---|---|---|
| ⛔ counter-test: binary `c7b228c5` (without the cure) | ⭐ | ⭐ | ⛔ «None» |
| ⭐ binary `2563cb22` (the cure) | ⭐ | ⭐ | ⭐ |
| `2563cb22`, `--senza-copia` | ⛔ | ⛔ | ⛔ — the fault is seen |
| test by hand, 5 rounds | 5/5 | — | 5/5 |
| `gnome` box | outcome **3**: the referee is not there on Mutter | | |

#### The net (`[M]` 19 Sep 2026, 19:56→22:28, binary `2563cb22`, `--scatola "gnome kde"`, 9 116 s)

| | |
|---|---|
| GNOME | ⭐ **all green** (the `rcp.c` cure holds here too) · C17(gnome) **3** and 3 with the fault: the referee is not there, stated |
| ⭐ **kde** | **all green**, C17 included · ⛔ **C17 injected fault "DOES NOT HOLD", class C**: the fault was SEEN (A, B, R red) but the mesh exited 1, and in the net with the fault the outcome is read the other way round (0 = seen). Corrected, and redone alone: kde green · fault seen with outcome 0 · gnome 3 and 3 |
| ⚠ and in addition | the mesh waits for the compositor to answer (`wl_compositor`) before saying "the referee is not there": a 3 on a healthy session must not be able to happen |
| net, on the server | C11 · C13 · C14 green |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |

⚠ **Still open, declared**: on GNOME the clipboard does not yet have a referee in the net. It needs
a Wayland client with `wl_data_device` and the focus (GTK), as `07-b45` said: it is GNOME work,
not this phase's.

### Increment 9 — what the user's test found (19-20 Sep 2026)

The user tests KDE from Chrome on his laptop, and in an hour pulls out **four things**. ⭐ Three
were decisions already taken and **lost in the passage from v1 to v2**: it is the price of the selective carry-over,
and the cure is that now each one has a bench (`banchi/12-i9-logout.sh`, `banchi/12-i10-menu-e-puntatore.sh`).

| | what the user saw | the cause | the cure |
|---|---|---|---|
| **1. one could shut down** | from Plasma's menu "Shut Down" and "Restart" | ⛔ **the box**, not the product: the three belts of §4.7 are put in place by `src/provisiona.sh` on the real machine, and in the boxes they had never been there — `CanPowerOff` said «challenge» instead of «no» | the same lines, in the same files, in the preparation of the box (`11-accendi.sh`) |
| **2. "Lock" and "Switch User"** | entries that do nothing | v1's KIOSK rules (`scrivi_regole_menu`) not carried over | `scrivi_regole_menu_kde()`: `lock_screen`, `start_new_session`, `switch_user` to `false` in `$XDG_RUNTIME_DIR/remotix/xdg/kdeglobals`, in front of `/etc/xdg`. ⛔ `logout` is not touched |
| **3. logout did not close** | after "Log Out" the page stayed on the last image | ⛔ **the product's**: on Plasma the session dies SILENTLY — KWin does not close the stream, the PipeWire node disappears and the capture goes back to "zero" forever. And `vista_viva` was a `static` turned on only by reading the state, which on KDE is never done ⇒ the child believed the session "not yet born" and made it be REBORN | `kwin.c`: the drop of the Wayland connection marks `chiuso`. `figlio.c`: if `kwin_chiuso()` the stage is unmounted, and `vista_viva` turns on with KWin's stage too ⇒ §7.6 does the rest (farewell `0x10`, the page goes back to the login form) |
| **4. the pointer's tail** | two pointers, the second chasing | ⛔ with `--virtual` KWin draws the cursor INSIDE the image (`STUDI.md` §kde, measured on 8 Aug 2026). v1's cure — a transparent cursor theme — not carried over | `scrivi_tema_cursore_kde()`: 68 1×1 shapes with zero alpha in `$XDG_RUNTIME_DIR/remotix/icons`, plus `XCURSOR_THEME`+`SIZE`+`PATH` (KWin looks at the theme **only** if `SIZE` is there too) |

| `[M]` 19-20 Sep 2026, `kde` box | old `2563cb22` | new `d7a5db20` |
|---|---|---|
| `12-i9`: the page after "Log Out" | ⛔ attached, no `0x10`, still there after 30 s | ⭐ closed after **2 s** with code `0x10`, and KWin **is not reborn** |
| `12-i10` 1. invisible cursor | ⛔ NO (XCURSOR_* 0/3, 0 shapes) | ⭐ YES (3/3, **68 shapes**, 0 fallbacks) |
| `12-i10` 2. menu without lock | ⛔ NO (0/1, rules absent) | ⭐ YES (rules 3/3) |
| `12-i10` 3. nobody shuts down | ⭐ YES (4/4 «no») — it belongs to the box, and indeed it does not change with the binary | ⭐ YES |

#### The net (`[M]` 20 Sep 2026, 02:21→04:52, binary `d7a5db20`, `--scatola "gnome kde"`, 9 119 s)

| | |
|---|---|
| GNOME | ⭐ **all green** — the three cures touch `sessione.c`, `kwin.c` and `figlio.c`, and GNOME did not notice |
| ⭐ **kde** | **all green**, C17 included: the invisible cursor does not disturb the meshes that look at the pixels, and the reduced menu disturbs nothing |
| net, on the server | C11 · C13 · C14 green |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |
| reds | **none** |

### Increment 10 — the second round of the user's test (20 Sep 2026)

The user tests again and finds **three things**, two of his and one that closes an old hole.

| what he saw | the cause | the cure |
|---|---|---|
| **no pointer** (after the invisible theme) | the invisible theme also arrives in the METADATA: the client dressed itself in an invisible shape. ⛔ Worse than two pointers | `cursore.c`: an all-transparent bitmap is "hidden" (§5.5) · and on Plasma hiding is NOT delivered (`cursore_mai_nascondere`, turned on by the child when the stage is KWin) ⇒ whoever watches keeps their own system's pointer |
| **windows cannot be resized** | Plasma is born with `BorderSizeAuto`: borders of a few pixels. At the monitor they are grabbed because the cursor changes shape, ⛔ remotely the desktop's cursor is invisible on purpose | `sessione.c`: `kwinrc` in the same folder as the rules, `BorderSize=Normal` — ⚠ **without** `[$i]`: it is a starting point, and the user can change it from System Settings |
| **on Firefox the clipboard does not go from the client to the server** | ⭐ **it is not a defect**: Firefox grants reading the clipboard **only** at the instant of `Ctrl+V` on the page. With "Paste" from the remote desktop's menu the page serves 0 bytes — `[M]` the log: «rilettura negata … servo quel che ho» | `pagina.html`: a 7 s sign on the canvas — "press Ctrl+V on this page" — when the reading is denied and there is no text to serve (decided by the user) |

⭐ **And the tools for working enter the boxes** (asked for by the user): `konsole`, `dolphin`
and `nano` on kde; `gnome-terminal`, `nautilus` and `nano` on gnome. They belong to the bench, not to the product.

#### The net (`[M]` 20 Sep 2026, 07:20→09:52, binary `836a88b6` + page `4eb65ca2`, 9 087 s)

| | |
|---|---|
| GNOME · **kde** | ⭐ **all green**, no red in any mesh |
| net, on the server and on the laptop | C10 · C11 · C12 · C13 · C14 · C15 · C16 green |

⭐ **AND THE USER'S TEST IS COMPLETE**: Chrome and Firefox on Linux, **Chrome on Android** —
audio, video and clipboard. ⚠ One round out of three of `07-b54` (Firefox on Wayland) gave red on the
**keyboard after the paste**: intermittent, to be kept an eye on.

### Increment 11 — the card's groups, put by REMOTIX (the user's decision, 20 Sep 2026)

The user's question: *«REMOTIX chiede che gli utenti appartengano ai gruppi video e render.
Normalmente le distro non ce li mettono: potrebbe essere un problema?»* ⇒ Yes, and the symptom is the
worst one: **one connects and sees nothing**, without an error. The decision and the measurement are in
`DECISIONI.md` §7.21; here the modules and the outcome remain.

| | |
|---|---|
| **at installation** | `src/provisiona.sh`: all the people of the machine (`UID_MIN..UID_MAX` read from `/etc/login.defs`, only those with a real shell) |
| **in operation** | `src/figlio.c`: `iscrivi_ai_gruppi_della_scheda()` — after PAM's yes, before the `fork`, with `usermod` and the user manager made to be reborn. ⚠ `raccogli_gruppi_scheda()` extracted: the nodes are read in **one place only** |
| ⛔ **and I7 changes** | the product now touches the groups, not only the session. The two guarantees: only after PAM, and every enrolment in the log |

| `[M]` 20 Sep 2026, `kde` box, user `senzagr` created without groups | outcome |
|---|---|
| ⛔ binary `836a88b6` (without the cure) | `id -nG` = «senzagr» · **zero frames** |
| ⭐ binary `9e3154a6` (the cure) | «PRIMA CONNESSIONE: ce lo metto io» · `id -nG` = «senzagr video render» · **105 frames delivered** |
| ⭐ on the real server, `provisiona.sh` | **3 people** enrolled · `nicfio` from «nicfio sudo» to «nicfio sudo video render» |

⭐ **And two repairs of the bench**, found by the user's `pre-push`:
1. `11-gancio.sh remoto` passed `--scatola gnome kde` **without quotes**: the remote half received
   "kde" as its own command and the round did not start;
2. ⛔ and when it failed to launch, **it had already deleted the log** of the round in progress — which
   went on writing into a nonexistent file. ⇒ Now it looks FIRST whether the unit is active, and in
   that case touches nothing and exits 3 saying so.
3. `fondamenta/strumenti/sshpw.py` forced the password (`PubkeyAuthentication=no`), written when
   a reboot had deleted the key: ⇒ it tries the key and keeps the password as a fallback.

#### The net (`[M]` 20 Sep 2026, 10:02→12:45, binary `9e3154a6`, `--scatola "gnome kde"`)

| | |
|---|---|
| GNOME · **kde** | ⭐ **all green**, no red · remote outcome **0** |
| net, on the laptop | C10 · C12 · C13 · C15 · C16 green, C10 with the fault seen |
| ⚠ the delegation | `remoto`'s waiting cap is **2 400 s** and the `tutto` family wants ~9 000: the local half declares "it did not finish within 2 400 s" while on the other side the round goes on and ends well. To be widened when needed |

### Increment 12 — the intermittent red, and the clipboard wall on GNOME

**1. The intermittent red of `07-b54` was the BENCH's** (`[M]` 20 Sep 2026: one round out of three said
"the keyboard is dead after Ctrl+V", the next two were green). ⛔ It looked at the log **only
once**, 2 s after the letter: if the line arrived a moment later, the bench measured its own
delay and called it a product fault. ⇒ Now it waits up to 8 s, and stops as soon as the line
is there. **Five rounds in a row green.** ⚠ An intermittent red gets the mesh turned off: that is why
it is not filed away.

**2. The clipboard referee for GNOME: `banchi/11-scatole/appunti-gtk.py`** — GTK (`python3-gi`),
that is `wl_data_device`, the same route as real applications, with a window presented because
on Wayland the clipboard is granted to whoever has the focus.

⛔⛔ **And the wall, measured** (`gnome` box, live session, client attached):

| who tries | outcome |
|---|---|
| `wl-copy` (without killing it: it stays alive on purpose) | ⛔ the product sees no copy |
| `wl-paste`, 20 s, even with `gnome-terminal` open | ⛔ stays hung (exit 124) |
| `appunti-gtk.py copia` | ⭐ copies **inside itself** … ⛔ and nobody else sees it |
| `appunti-gtk.py incolla` | ⛔ reads empty |
| ⭐ the PRODUCT | delivers the bytes and **closes the pipe** (verified in `appunti.c`: `close(fd)` before `SelectionWriteDone`) |

⇒ The block is **how Mutter grants the clipboard to applications in a session without a seat**:
without focus it does not grant it, and there the focus is never really there. ⚠ It is not a product defect and
not the bench's: it is the scene. ⇒ C17 on GNOME stays **outcome 3, declared**, and GNOME's clipboard
stays tested by hand (`07-b54`). It is reopened when the work on GNOME is opened.

### Increment 13 — the clipboard in the net ON GNOME TOO: the click that gives the focus

⛔ **Yesterday's wall**: on Mutter no application of the session managed to touch the
clipboard, so C17 on GNOME exited 3. ⭐ **The fourth route, pointed out by the user**: do as
a person does — **click**. And the click is sent **through the product** (`RCP.md` §7.3), as
C4 does with the key: if it did not arrive, the red would be the product's for not delivering the input.

| piece | what |
|---|---|
| `banchi/01-b3-cliente.py` | `manda_pulsante()` + `--clic X,Y`, `--clic-dopo`, `--clic-ogni`: the click that gives the FOCUS to a window of the remote desktop |
| `banchi/11-scatole/appunti-gtk.py` | the external referee: GTK (`wl_data_device`), window presented, and ⭐ **it waits for the focus** before copying or reading |
| `11-c17` | ⭐ **asks the desktop which referee it can use**: `wl-clipboard` where there is `zwlr_data_control` (KWin), GTK+click where there is not (Mutter). ⚠ The difference is the bench's; the product does the same thing on the two desktops |
| the boxes | `python3-gi` + `gir1.2-gtk-4.0` in the two recipes, and `appunti-gtk.py` copied by the `prodotto` step |

| `[M]` 20 Sep 2026 | kde | gnome |
|---|---|---|
| normal C17 | ⭐ GREEN (A · B · R) | ⭐ GREEN (A · B · R) |
| C17 `--senza-copia` | ⭐ the fault is SEEN | ⭐ the fault is SEEN |

⛔ **And an intermittent red, caught inside the net and cured**: C17(gnome) red on B and R with
a clock wait (12 s) for the copy window to take the focus. ⇒ Now the bench
**waits for the copy to have happened** (the referee declares it in its log): `[M]` happened after
**1 s**. ⚠ No product regression: the GNOME meshes were all green, and the binary is
the one already passed at 12:45.

⛔ **A cure tried and WITHDRAWN, and it must be said**: on KDE the anti-echo of `appunti_kde.c` can mistake
for an echo a real copy made by an application with our same types. I tried to read the
text and compare it — ⛔ but reading inside the callback blocks the event pump (our
source is served by the same pump) and the round got worse. ⇒ Withdrawn at once, code
back to the tested one. ⚠ `[M]` outside that scene the product **sees** GTK copies on KDE.
It stays as an open point, with the measurement.

## The measurements

| what | expected | measured | date |
|---|---|---|---|
| **CP0** — `tutto` round on the four boxes, launched **on the server** | GNOME green; on kde/xfce/lxqt only C1 red; faults all caught; a single binary | ⭐ **as expected** — see below | `[M]` 18 Sep 2026, 17:25→19:38 |

#### CP0 in detail — binary `bfc5936a2b0f` (sources `src/` of `c82c910`), 7 967 s

| | |
|---|---|
| GNOME | ⭐ **all green**: step 0, C1×10, C2, C3 (+ still scene), C4, C5, C6, C7, C8, C8b, C9 |
| kde · xfce · lxqt | step 0, C5, C7, C8, C9 green · ⛔ **C1×10 RED** on all three (the mandate) · C2 C3 C4 C6 C8b **skipped** by the "gnome only" gate (outcome 3) |
| net, on the server | C11 green (14 entries aligned, **same md5 in the four**) · C13 green · C14 green (786 s) |
| net, on the laptop | C10, C12, C15, C16 green, C10 with the fault seen — ⚠ **these four want the git repository**: launched on the server they give 2/3 "the terrain does not hold", and it is not a red. They are run **here**, in the same certification round |
| ⭐ **injected faults** | **25 out of 25 seen** (24 on the boxes, 1 on the laptop) |
| bench reds | none |

⚠ **The counts are not compared with those of 27 August**, and it must be said why they look different: the
`README.md` says *«58 verdi, 3 rossi, 49 guasti su 49»*, `fasi/11-…` §7-bis.19 says *«57 · 23 su 25
· 6 esiti 3 · 3 rossi»* — two different counts of the **same** round. ⇒ The comparison that counts is
**the shape**: the only reds are the three `C1` outside GNOME, **as it was then**. Today: 58 outcomes 0
on the boxes (34 verdicts + 24 faults seen), 3 reds, and the faults caught are 25 out of 25.

## ⛔ What did NOT work

## What remains [?]

### The screen that changes size with the session alive — the road for the future (`[R]` 19 Sep 2026)

Asked by the user: *«credo che nelle ultime versioni di KWin questo problema sia stato superato»*.
⭐ **Partly yes**: KWin **6.8** (release expected on 14 Oct 2026) makes **the capture's virtual
monitors resizable** — commit `452707eb` «screencast: Resizable Virtual Monitors» by
David Edmundson, KDE bug 512620, *fixed in 6.8.0*. The mechanism is GNOME's: the size is
**renegotiated in the PipeWire format** between whoever captures and KWin (with the twin changes in KPipeWire and KRDP).
Before, the size was fixed at 1920×1080, and renegotiating it froze the stream.

⛔ **But for us it is not enough by itself, and it must be said why** — two conditions to verify when it arrives:
1. **the backend.** The fix holds for `stream_virtual_output`, that is for a virtual monitor CREATED by the
   capture. We are on the `--virtual` backend (a machine without a seat), and there `stream_virtual_output`
   **does not exist**: `VirtualBackend` does not redefine `createVirtualOutput()` ⇒ «Could not find output»
   (`STUDI.md` §kde, the `stream_virtual_output` line, verified). 6.8 would need to add it to the
   virtual backend, or the `Virtual-0` output would need to accept a new mode (the "custom modes
   for virtual screens", Plasma 6.6, are to be read for this);
2. **the distribution.** The server has Debian Trixie's KWin, **6.3.6**: 6.8 arrives only with
   a new distribution or with backports.

⭐ **AND THE FIRST OF THE TWO CONDITIONS HAS ALREADY FALLEN** — `[R]` 20 Sep 2026, read in KWin's code
(`master`): `VirtualBackend` **declares** `createVirtualOutput(const QString &name, const QString
&description, const QSize &size, qreal scale)`, with the same signature as the base
(`OutputBackend::createVirtualOutput`, virtual with a default implementation). ⇒ The «Could not
find output» of the `--virtual` backend — which in 6.3.6 came from the base returning `nullptr` —
**is no longer there on new KWin**: even without a seat one can ask the capture for a virtual screen,
and from 6.8 that screen resizes. ⇒ Only the second condition remains: the **version**
(Trixie has 6.3.6).

⭐ **On our side the work would be small**: `misura_del_palco()` already asks KWin for the real
size and the capture already renegotiates the size on GNOME ⇒ it would be a matter of asking for the new size
instead of rescaling in the page. Sources: KDE blog «This Week in Plasma: Emoji Resizing» (1 Aug
2026), KDE bug 512620.


## The user's verdict
