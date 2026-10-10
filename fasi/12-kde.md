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
| **SHAPE** | the same as GNOME: TEXT ONLY (`DECISIONI.md` §5-ter.1), the same row of types, the same cap, the same memory of the last text, and if the client has nothing the session gets ITS own text back. v1's traps carried over: the echo (state criterion), the full round before reading, `POLLHUP` = ready, the minimal step towards klipper, never `x-kde-onlyReplaceEmpty` |

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


### Incremento 8 — gli appunti entrano nella rete (C17), e un difetto di tutti i desktop

| | |
|---|---|
| **OBIETTIVO** | gli appunti di KDE controllati a ogni rete, non più solo a mano (`07-b54`) |
| **LA MAGLIA** | `banchi/11-scatole/11-c17-gli-appunti-vanno-nei-due-versi.py`: tre fatti col loro nome — **A** dispositivo → sessione (`wl-paste` legge quel che il cliente ha annunciato) · **B** sessione → dispositivo (`wl-copy`, e il server lo annuncia al cliente attaccato) · **R** chi si riattacca lo riceve. Guasto innestato `--senza-copia` ⇒ tre rossi |
| **L'ARBITRO** | `wl-clipboard` vuole `zwlr_data_control_manager_v1` (o `ext_…`): KWin ce l'ha, Mutter no. ⛔ `[M]` su GNOME `wl-paste` e `wl-copy` restano appesi (uscita 124) mentre il server scrive «22 byte consegnati alla sessione» ⇒ la maglia lo chiede a `wayland-info` e, se manca, esce **3** dicendolo. Nessun cancello per desktop nel gancio |

⛔⛔ **Il difetto trovato, ed è di TUTTI i desktop** (`src/rcp.c`, copia gemella in `banchi/rcp/`):
un cliente che si riattacca a un figlio vivo fa rileggere la clipboard del desktop, ma la lettura
arriva quando la sessione RCP è ancora in `attesa-verdetto`. Il testo si teneva «per chi si
attaccherà» e **nessuno lo annunciava mai**: chi rientrava non sapeva che cosa c'era negli
appunti. ⇒ `annuncia_il_tenuto()`, chiamata appena la sessione passa ad `S_ATTIVA` (§2.5: dopo
`SESSIONE`).

| `[M]` 19 set 2026, scatola `kde` | A | B | R |
|---|---|---|---|
| ⛔ controprova: binario `c7b228c5` (senza la cura) | ⭐ | ⭐ | ⛔ «None» |
| ⭐ binario `2563cb22` (la cura) | ⭐ | ⭐ | ⭐ |
| `2563cb22`, `--senza-copia` | ⛔ | ⛔ | ⛔ — il guasto si vede |
| prova a mano, 5 giri | 5/5 | — | 5/5 |
| scatola `gnome` | esito **3**: l'arbitro non c'è su Mutter | | |

#### La rete (`[M]` 19 set 2026, 19:56→22:28, binario `2563cb22`, `--scatola "gnome kde"`, 9 116 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde** (la cura di `rcp.c` vale anche qui) · C17(gnome) **3** e 3 col guasto: l'arbitro non c'è, detto |
| ⭐ **kde** | **tutto verde**, C17 compresa · ⛔ **C17 guasto innestato «NON REGGE», classe C**: il guasto era VISTO (A, B, R rossi) ma la maglia usciva 1, e nella rete col guasto l'esito si legge al contrario (0 = visto). Corretta, e rifatta da sola: kde verde · guasto visto con esito 0 · gnome 3 e 3 |
| ⚠ e in più | la maglia aspetta che il compositore risponda (`wl_compositor`) prima di dire «l'arbitro non c'è»: un 3 su una sessione sana non deve poter capitare |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |

⚠ **Resta aperto, dichiarato**: su GNOME gli appunti non hanno ancora un arbitro nella rete. Serve
un client Wayland con `wl_data_device` e il fuoco (GTK), come diceva `07-b45`: è lavoro di GNOME,
non di questa fase.

### Incremento 9 — quel che ha trovato la prova dell'utente (19-20 set 2026)

L'utente prova KDE da Chrome sul suo portatile, e in un'ora tira fuori **quattro cose**. ⭐ Tre
erano decisioni già prese e **perdute nel passaggio da v1 a v2**: è il prezzo del riporto selettivo,
e la cura è che adesso ciascuna ha un banco (`banchi/12-i9-logout.sh`, `banchi/12-i10-menu-e-puntatore.sh`).

| | che cosa vedeva l'utente | la causa | la cura |
|---|---|---|---|
| **1. si poteva spegnere** | dal menu di Plasma «Spegni» e «Riavvia» | ⛔ **la scatola**, non il prodotto: le tre cinture di §4.7 le mette `src/provisiona.sh` sulla macchina vera, e nelle scatole non c'erano mai state — `CanPowerOff` diceva «challenge» invece di «no» | le stesse righe, negli stessi file, nella preparazione della scatola (`11-accendi.sh`) |
| **2. «Blocca» e «Cambia utente»** | voci che non fanno niente | le regole KIOSK di v1 (`scrivi_regole_menu`) non riportate | `scrivi_regole_menu_kde()`: `lock_screen`, `start_new_session`, `switch_user` a `false` in `$XDG_RUNTIME_DIR/remotix/xdg/kdeglobals`, davanti a `/etc/xdg`. ⛔ `logout` non si tocca |
| **3. il logout non chiudeva** | dopo «Esci» la pagina restava sull'ultima immagine | ⛔ **del prodotto**: su Plasma la sessione muore in SILENZIO — KWin non chiude il flusso, il nodo PipeWire sparisce e la presa torna «zero» per sempre. E `vista_viva` era una `static` accesa solo dalla lettura dello stato, che su KDE non si fa mai ⇒ il figlio credeva la sessione «non ancora nata» e la faceva RINASCERE | `kwin.c`: la caduta della connessione Wayland segna `chiuso`. `figlio.c`: se `kwin_chiuso()` si smonta il palco, e `vista_viva` si accende anche col palco di KWin ⇒ §7.6 fa il resto (congedo `0x10`, la pagina torna al modulo d'accesso) |
| **4. la coda del puntatore** | due puntatori, il secondo che insegue | ⛔ con `--virtual` KWin disegna il cursore DENTRO l'immagine (`STUDI.md` §kde, misurato l'8 ago 2026). La cura di v1 — tema del cursore trasparente — non riportata | `scrivi_tema_cursore_kde()`: 68 forme 1×1 ad alfa zero in `$XDG_RUNTIME_DIR/remotix/icons`, più `XCURSOR_THEME`+`SIZE`+`PATH` (KWin guarda il tema **solo** se c'è anche `SIZE`) |

| `[M]` 19-20 set 2026, scatola `kde` | vecchio `2563cb22` | nuovo `d7a5db20` |
|---|---|---|
| `12-i9`: la pagina dopo «Esci» | ⛔ attaccata, nessun `0x10`, dopo 30 s ancora lì | ⭐ chiusa dopo **2 s** col codice `0x10`, e KWin **non rinasce** |
| `12-i10` 1. cursore invisibile | ⛔ NO (XCURSOR_* 0/3, 0 forme) | ⭐ SI (3/3, **68 forme**, 0 ripieghi) |
| `12-i10` 2. menu senza blocco | ⛔ NO (0/1, regole assenti) | ⭐ SI (regole 3/3) |
| `12-i10` 3. nessuno spegne | ⭐ SI (4/4 «no») — è della scatola, e infatti non cambia col binario | ⭐ SI |

#### La rete (`[M]` 20 set 2026, 02:21→04:52, binario `d7a5db20`, `--scatola "gnome kde"`, 9 119 s)

| | |
|---|---|
| GNOME | ⭐ **tutto verde** — le tre cure toccano `sessione.c`, `kwin.c` e `figlio.c`, e GNOME non se n'è accorto |
| ⭐ **kde** | **tutto verde**, C17 compresa: il cursore invisibile non disturba le maglie che guardano i pixel, e il menu ridotto non disturba niente |
| rete, sul server | C11 · C13 · C14 verdi |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| rossi | **nessuno** |

### Incremento 10 — la seconda tornata della prova dell'utente (20 set 2026)

L'utente riprova e trova **tre cose**, due sue e una che chiude un buco vecchio.

| che cosa vedeva | la causa | la cura |
|---|---|---|
| **nessun puntatore** (dopo il tema invisibile) | il tema invisibile arriva anche nel METADATO: il client si vestiva di una forma invisibile. ⛔ Peggio di due puntatori | `cursore.c`: una bitmap tutta trasparente è «nascosto» (§5.5) · e su Plasma il nascondimento NON si consegna (`cursore_mai_nascondere`, acceso dal figlio quando il palco è KWin) ⇒ chi guarda tiene il puntatore del suo sistema |
| **le finestre non si ridimensionano** | Plasma nasce con `BorderSizeAuto`: bordi di pochi pixel. Al monitor si prendono perché il cursore cambia forma, ⛔ in remoto il cursore del desktop è invisibile apposta | `sessione.c`: `kwinrc` nella stessa cartella delle regole, `BorderSize=Normal` — ⚠ **senza** `[$i]`: è un punto di partenza, e da Impostazioni di sistema l'utente lo cambia |
| **su Firefox la clipboard non va dal client al server** | ⭐ **non è un difetto**: Firefox concede la lettura degli appunti **solo** nell'istante del `Ctrl+V` sulla pagina. Con «Incolla» dal menu del desktop remoto la pagina serve 0 byte — `[M]` il registro: «rilettura negata … servo quel che ho» | `pagina.html`: un cartello di 7 s sulla tela — «premi Ctrl+V su questa pagina» — quando la lettura è negata e non c'è testo da servire (deciso dall'utente) |

⭐ **E nelle scatole entrano gli strumenti per lavorare** (chiesti dall'utente): `konsole`, `dolphin`
e `nano` su kde; `gnome-terminal`, `nautilus` e `nano` su gnome. Sono del banco, non del prodotto.

#### La rete (`[M]` 20 set 2026, 07:20→09:52, binario `836a88b6` + pagina `4eb65ca2`, 9 087 s)

| | |
|---|---|
| GNOME · **kde** | ⭐ **tutto verde**, nessun rosso in nessuna maglia |
| rete, sul server e sul portatile | C10 · C11 · C12 · C13 · C14 · C15 · C16 verdi |

⭐ **E LA PROVA DELL'UTENTE È COMPLETA**: Chrome e Firefox su Linux, **Chrome su Android** —
audio, video e appunti. ⚠ Un giro su tre di `07-b54` (Firefox su Wayland) ha dato rosso sulla
**tastiera dopo l'incolla**: intermittente, da tenere d'occhio.

### Incremento 11 — i gruppi della scheda, messi da REMOTIX (decisione dell'utente, 20 set 2026)

Domanda dell'utente: *«REMOTIX chiede che gli utenti appartengano ai gruppi video e render.
Normalmente le distro non ce li mettono: potrebbe essere un problema?»* ⇒ Sì, e il sintomo è il
peggiore: **si collega e non vede niente**, senza un errore. La decisione e la misura stanno in
`DECISIONI.md` §7.21; qui restano i moduli e l'esito.

| | |
|---|---|
| **all'installazione** | `src/provisiona.sh`: tutte le persone della macchina (`UID_MIN..UID_MAX` letti da `/etc/login.defs`, solo chi ha una shell vera) |
| **in esercizio** | `src/figlio.c`: `iscrivi_ai_gruppi_della_scheda()` — dopo il sì di PAM, prima del `fork`, con `usermod` e il gestore d'utente fatto rinascere. ⚠ `raccogli_gruppi_scheda()` estratta: i nodi si leggono in **un posto solo** |
| ⛔ **e cambia I7** | il prodotto adesso tocca i gruppi, non solo la sessione. Le due garanzie: solo dopo PAM, e ogni iscrizione nel registro |

| `[M]` 20 set 2026, scatola `kde`, utente `senzagr` creato senza gruppi | esito |
|---|---|
| ⛔ binario `836a88b6` (senza la cura) | `id -nG` = «senzagr» · **zero fotogrammi** |
| ⭐ binario `9e3154a6` (la cura) | «PRIMA CONNESSIONE: ce lo metto io» · `id -nG` = «senzagr video render» · **105 fotogrammi consegnati** |
| ⭐ sul server vero, `provisiona.sh` | **3 persone** iscritte · `nicfio` da «nicfio sudo» a «nicfio sudo video render» |

⭐ **E due riparazioni del banco**, trovate dal `pre-push` dell'utente:
1. `11-gancio.sh remoto` passava `--scatola gnome kde` **senza apici**: la metà remota riceveva
   «kde» come comando suo e il giro non partiva;
2. ⛔ e quando non riusciva a lanciare, **aveva già cancellato il log** del giro in corso — che ha
   continuato a scrivere in un file inesistente. ⇒ Adesso guarda PRIMA se l'unità è attiva, e in
   quel caso non tocca niente ed esce 3 dicendolo.
3. `fondamenta/strumenti/sshpw.py` imponeva la password (`PubkeyAuthentication=no`), scritta quando
   un riavvio aveva cancellato la chiave: ⇒ prova la chiave e tiene la password come ripiego.

#### La rete (`[M]` 20 set 2026, 10:02→12:45, binario `9e3154a6`, `--scatola "gnome kde"`)

| | |
|---|---|
| GNOME · **kde** | ⭐ **tutto verde**, nessun rosso · esito remoto **0** |
| rete, sul portatile | C10 · C12 · C13 · C15 · C16 verdi, C10 col guasto visto |
| ⚠ la delega | il tetto d'attesa di `remoto` è **2 400 s** e la famiglia `tutto` ne vuole ~9 000: la metà locale dichiara «non ha finito entro 2 400 s» mentre di là il giro prosegue e finisce bene. Da allargare quando servirà |

### Incremento 12 — il rosso intermittente, e il muro degli appunti su GNOME

**1. Il rosso intermittente di `07-b54` era del BANCO** (`[M]` 20 set 2026: un giro su tre diceva
«la tastiera è morta dopo il Ctrl+V», i due dopo erano verdi). ⛔ Guardava il registro **una volta
sola**, 2 s dopo la lettera: se la riga arrivava un attimo più tardi, il banco misurava il proprio
ritardo e lo chiamava guasto del prodotto. ⇒ Adesso aspetta fino a 8 s, e si ferma appena la riga
c'è. **Cinque giri di fila verdi.** ⚠ Un rosso intermittente fa spegnere la maglia: è il motivo per
cui non si archivia.

**2. L'arbitro degli appunti per GNOME: `banchi/11-scatole/appunti-gtk.py`** — GTK (`python3-gi`),
cioè `wl_data_device`, la stessa strada delle applicazioni vere, con una finestra presentata perché
su Wayland la clipboard si concede a chi ha il fuoco.

⛔⛔ **E il muro, misurato** (scatola `gnome`, sessione viva, client attaccato):

| chi prova | esito |
|---|---|
| `wl-copy` (senza ucciderlo: resta vivo apposta) | ⛔ il prodotto non vede nessuna copia |
| `wl-paste`, 20 s, anche con `gnome-terminal` aperto | ⛔ resta appeso (uscita 124) |
| `appunti-gtk.py copia` | ⭐ copia **dentro di sé** … ⛔ e nessun altro la vede |
| `appunti-gtk.py incolla` | ⛔ legge vuoto |
| ⭐ il PRODOTTO | consegna i byte e **chiude il tubo** (verificato in `appunti.c`: `close(fd)` prima di `SelectionWriteDone`) |

⇒ Il blocco è **come Mutter concede gli appunti alle applicazioni in una sessione senza seat**:
senza fuoco non li concede, e lì il fuoco non c'è mai davvero. ⚠ Non è un difetto del prodotto e
non è del banco: è la scena. ⇒ C17 su GNOME resta **esito 3, dichiarato**, e gli appunti di GNOME
restano provati a mano (`07-b54`). Si riapre quando si aprirà il lavoro su GNOME.

### Incremento 13 — gli appunti nella rete ANCHE su GNOME: il clic che dà il fuoco

⛔ **Il muro di ieri**: su Mutter nessuna applicazione della sessione riusciva a toccare gli
appunti, quindi C17 su GNOME usciva 3. ⭐ **La quarta strada, indicata dall'utente**: si fa come
fa una persona — **si clicca**. E il clic si manda **attraverso il prodotto** (`RCP.md` §7.3), come
fa C4 col tasto: se non arrivasse, il rosso sarebbe del prodotto che non consegna l'input.

| pezzo | che cosa |
|---|---|
| `banchi/01-b3-cliente.py` | `manda_pulsante()` + `--clic X,Y`, `--clic-dopo`, `--clic-ogni`: il clic che dà il FUOCO a una finestra del desktop remoto |
| `banchi/11-scatole/appunti-gtk.py` | l'arbitro esterno: GTK (`wl_data_device`), finestra presentata, e ⭐ **aspetta il fuoco** prima di copiare o leggere |
| `11-c17` | ⭐ **chiede al desktop quale arbitro può usare**: `wl-clipboard` dove c'è `zwlr_data_control` (KWin), GTK+clic dove non c'è (Mutter). ⚠ La differenza è del banco; il prodotto fa la stessa cosa sui due desktop |
| le scatole | `python3-gi` + `gir1.2-gtk-4.0` nelle due ricette, e `appunti-gtk.py` copiato dal passo `prodotto` |

| `[M]` 20 set 2026 | kde | gnome |
|---|---|---|
| C17 normale | ⭐ VERDE (A · B · R) | ⭐ VERDE (A · B · R) |
| C17 `--senza-copia` | ⭐ il guasto è VISTO | ⭐ il guasto è VISTO |

⛔ **E un rosso intermittente, preso dentro la rete e curato**: C17(gnome) rossa su B e R con
un'attesa a orologio (12 s) perché la finestra della copia prendesse il fuoco. ⇒ Adesso il banco
**aspetta che la copia sia avvenuta** (l'arbitro lo dichiara nel suo registro): `[M]` avvenuta dopo
**1 s**. ⚠ Nessuna regressione del prodotto: le maglie di GNOME erano tutte verdi, e il binario è
quello già passato alle 12:45.

⛔ **Una cura provata e RITIRATA, e va detta**: su KDE l'anti-eco di `appunti_kde.c` può scambiare
per eco una copia vera fatta da un'applicazione con i nostri stessi tipi. Ho provato a leggere il
testo e confrontarlo — ⛔ ma leggere dentro la richiamata blocca la pompa degli eventi (la nostra
sorgente viene servita dalla stessa pompa) e il giro è peggiorato. ⇒ Ritirata subito, codice
tornato a quello provato. ⚠ `[M]` fuori da quella scena il prodotto **vede** le copie GTK su KDE.
Resta come punto aperto, con la misura.

## Le misure

| che cosa | atteso | misurato | data |
|---|---|---|---|
| **CP0** — giro `tutto` sulle quattro scatole, lanciato **sul server** | GNOME verde; su kde/xfce/lxqt solo C1 rosso; guasti tutti presi; un binario solo | ⭐ **come atteso** — vedi sotto | `[M]` 18 set 2026, 17:25→19:38 |

#### CP0 in dettaglio — binario `bfc5936a2b0f` (sorgenti `src/` di `c82c910`), 7 967 s

| | |
|---|---|
| GNOME | ⭐ **tutto verde**: passo 0, C1×10, C2, C3 (+ scena ferma), C4, C5, C6, C7, C8, C8b, C9 |
| kde · xfce · lxqt | passo 0, C5, C7, C8, C9 verdi · ⛔ **C1×10 ROSSO** su tutte e tre (il mandato) · C2 C3 C4 C6 C8b **saltate** dal cancello «solo gnome» (esito 3) |
| rete, sul server | C11 verde (14 voci allineate, **stesso md5 nelle quattro**) · C13 verde · C14 verde (786 s) |
| rete, sul portatile | C10, C12, C15, C16 verdi, C10 col guasto visto — ⚠ **queste quattro vogliono il deposito git**: lanciate sul server danno 2/3 «il terreno non regge», e non è un rosso. Si fanno girare **qui**, nello stesso giro di certificazione |
| ⭐ **guasti innestati** | **25 su 25 visti** (24 sulle scatole, 1 sul portatile) |
| rossi del banco | nessuno |

⚠ **I conti non si confrontano con quelli del 27 agosto**, e va detto perché sembrano diversi: il
`README.md` dice *«58 verdi, 3 rossi, 49 guasti su 49»*, `fasi/11-…` §7-bis.19 dice *«57 · 23 su 25
· 6 esiti 3 · 3 rossi»* — due conteggi diversi dello **stesso** giro. ⇒ Il confronto che vale è
**la forma**: gli unici rossi sono i tre `C1` fuori da GNOME, **com'era allora**. Oggi: 58 esiti 0
sulle scatole (34 verdetti + 24 guasti visti), 3 rossi, e i guasti presi sono 25 su 25.

## ⛔ Che cosa NON ha funzionato

## Che cosa resta [?]

### Lo schermo che cambia misura a sessione viva — la strada per il futuro (`[R]` 19 set 2026)

Chiesto dall'utente: *«credo che nelle ultime versioni di KWin questo problema sia stato superato»*.
⭐ **In parte sì**: KWin **6.8** (uscita prevista il 14 ottobre 2026) rende **ridimensionabili i
monitor virtuali della cattura** — commit `452707eb` «screencast: Resizable Virtual Monitors» di
David Edmundson, bug KDE 512620, *fixed in 6.8.0*. Il meccanismo è quello di GNOME: la misura si
**rinegozia nel formato PipeWire** fra chi cattura e KWin (con i cambi gemelli in KPipeWire e KRDP).
Prima la misura era fissa a 1920×1080, e rinegoziarla congelava il flusso.

⛔ **Ma per noi non basta da solo, e va detto perché** — due condizioni da verificare quando arriva:
1. **il backend.** Il fix vale per `stream_virtual_output`, cioè per un monitor virtuale CREATO dalla
   cattura. Noi siamo sul backend `--virtual` (una macchina senza seat), e lì `stream_virtual_output`
   **non esiste**: `VirtualBackend` non ridefinisce `createVirtualOutput()` ⇒ «Could not find output»
   (`STUDI.md` §kde, riga di `stream_virtual_output`, verificato). Serve che 6.8 lo aggiunga al
   backend virtuale, oppure che l'uscita `Virtual-0` accetti un modo nuovo (i «modi personalizzati
   per gli schermi virtuali», Plasma 6.6, sono da leggere per questo);
2. **la distribuzione.** Il server ha la KWin di Debian Trixie, **6.3.6**: 6.8 arriva solo con
   una distribuzione nuova o con i backport.

⭐ **E LA PRIMA DELLE DUE CONDIZIONI E' GIA' CADUTA** — `[R]` 20 set 2026, letto nel codice di KWin
(`master`): `VirtualBackend` **dichiara** `createVirtualOutput(const QString &name, const QString
&description, const QSize &size, qreal scale)`, con la stessa firma della base
(`OutputBackend::createVirtualOutput`, virtuale con implementazione predefinita). ⇒ Il «Could not
find output» del backend `--virtual` — che nella 6.3.6 veniva dalla base che tornava `nullptr` —
**su KWin nuovo non c'è più**: anche senza seat si può chiedere uno schermo virtuale alla cattura,
e dalla 6.8 quello schermo si ridimensiona. ⇒ Resta solo la seconda condizione: la **versione**
(Trixie ha la 6.3.6).

⭐ **Dalla nostra parte il lavoro sarebbe piccolo**: `misura_del_palco()` chiede già a KWin la misura
vera e la cattura rinegozia già la misura su GNOME ⇒ si tratterebbe di chiedere la misura nuova
invece di riscalare nella pagina. Fonti: blog KDE «This Week in Plasma: Emoji Resizing» (1 ago
2026), bug KDE 512620.


## Il giudizio dell'utente
