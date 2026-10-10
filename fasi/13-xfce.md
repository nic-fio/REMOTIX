# Phase 13 — XFCE

*⚠ Historical measurements, on the machine of the time. With phase 18 (without ffmpeg) the ones the change invalidated were removed — encoding without a card and colour conversion with swscale; those of encoding on the card and of audio remain, because the new stream is identical (comparison of 30 Sep 2026). The user's decision.*

*Opened on **20 Sep 2026**. Closed on —*

## What it must produce

The third desktop: **the same thing on XFCE** (`PIANO.md` phase 13). The user opens the browser and sees
their XFCE desktop, as today they see GNOME and Plasma.

⛔ **The rule of the phase, the user's, 20 Sep 2026**: *«aggiungere XFCE a REMOTIX senza
perdere nessuna capacità già certificata di GNOME e KDE»*. ⇒ **From today the protected baselines are
two**: a KDE regression counts as much as a GNOME one. KDE leaves the building site and enters the
guardian.

We proceed by **increments**, and every increment goes through the same gates as phase 12:

| | |
|---|---|
| **CP0** | the baseline: complete net on the **four** boxes, the same binary everywhere |
| **CP1** | the increment is defined: goal, invariant, modules, XFCE test, client test, GNOME **and KDE** regressions to watch, criterion |
| **CP2** | GNOME, KDE and XFCE **observed** at the point of the increment, and the difference written — nothing deduced |
| **CP3** | the minimal change designed: files, why, what of GNOME and of KDE stays as it is |
| **CP4** | the XFCE test done for real, on the declared scene |
| **client** | Chrome and Firefox on Linux, Chrome on the Android emulator — when the increment touches the path |
| **net** | the complete net, GNOME **and KDE** unchanged, the injected faults still caught |
| **checkpoint** | a commit that can be resumed |

⇒ A red on GNOME or on KDE is **a regression until proved otherwise**, and it is
classified: A real regression · B assumption of one desktop in the common code · C bench defect
· D wrong invariant (⛔ never as a shortcut).

---

## ⭐ The difference that changes the shape of the phase

GNOME has Mutter, KDE has KWin. ⛔ **XFCE has no compositor of its own**: on Wayland it relies on
**labwc**, which is **wlroots** — the third and last family. ⇒ Phase 13 is not "a third branch like the
second": two pieces of the product **are not reused at all**.

| piece | GNOME and KDE, today | XFCE (wlroots) | cost |
|---|---|---|---|
| **clipboard** | `src/appunti_kde.c`, `zwlr_data_control` | ⭐ **almost free**: that file is called "kde" but **already** speaks the wlroots protocol (`src/appunti_kde.h:6-10`) | small |
| **recognition** | `riconosci_desktop()`, `src/sessione.c:275-303` | third value of the enum, at the **end** (it travels as `uint32_t` between child and parent) | small |
| **session** | two branches in `sessione.c` | ~14 points; ⛔ and `scrivi_dropin()` **has no object**: on XFCE the compositor is not a systemd unit | medium |
| **capture** | PipeWire that **pushes** the frames | ⛔ `zwlr_screencopy_manager_v1`, a **pull** model: one frame per request, no PipeWire, no D-Bus | big |
| **input** | **libei** (`ConnectToEIS`) | ⛔ libei **does not exist** on wlroots (`STUDI.md` §xfce §7, verified by absence with a positive check). `zwp_virtual_keyboard` + `zwlr_virtual_pointer`, and the **modifiers** must be written from scratch | the biggest |

⭐ **And the study is already done**: `STUDI.md`, section "XFCE, labwc e wlroots" (857 lines, §1-§15), with
the fourteen questions of `LEZIONI.md` §3 already filled in, eleven opening measurements (M1-M11) and five
choices to put before the user. ⛔ It is read **before** reopening one.

---

## The decisions produced

- **20 Sep 2026, the user's**: *«allo stato attuale remotix e' destinato a sistemi con un
  solo DE installato. I sistemi con DE multipli installato sono per il momento fuori scope»* ⇒
  `DECISIONI.md` **§0.6**, which widens §4.6-duodetricies. ⭐ Recognition stays simple: we
  look for the desktop that is there, we do not arbitrate between desktops that coexist, and ⛔ v1's
  `--compositore` option **is not put back**.
- **20 Sep 2026, the user's**: the phase is worked *«in silenzio»*, with an update
  roughly every half hour, and it is interrupted only for a checkpoint, regression, block,
  decision or milestone.
- ⇒ **The decision of 19 September falls** *«togli XFCE e LXQt»* (`fasi/12-kde.md:45-48`): the four
  boxes come back into the rounds. ⭐ Nothing needs changing in the hook to get this — the default
  is **already** `DESKTOP_NOTI="gnome kde xfce lxqt"` (`11-gancio.sh:240`) and the `pre-push` does not pass
  `--scatola`: it was enough to stop passing it by hand.
- **LXQt stays out of the building site**, and may stay red for the unimplemented capabilities. ⚠ But it is
  of the **same family** as XFCE (labwc/wlroots, `adattatore.lxqt.sh` is identical to the xfce one)
  ⇒ almost everything written here serves it too, and phase 14 will be short.

---

## The bench — what must be touched, declared before touching it

The bench is **the net of phase 11** (`banchi/11-scatole/`), pointed at the `xfce` box. The sign
that XFCE is served is the one already written: **`C1(xfce)` turns green**, and after it C2, C3, C4, C6,
C7, C8b, C9, C17 on the same box.

Readings of 20 Sep 2026, `[R]`:

1. ⛔ **The two-name gate**, `11-gancio.sh:809-813` (`le_cinque_nuove`): *«il prodotto sa
   avviare solo GNOME e KDE»*. ⚠ It skips **15 runs**, not five — C2×3, C3×4, C4×3, C6×2,
   C8b×2 **and C17×2**, because the two calls of C17 (`:863-864`) are **after** the `return`. ⇒ And
   C17 is skipped **without being named** in the log: the line is still called
   `"C2($d) C3 C4 C6 C8b"`. The comment at `:856-862` — *«Nessun cancello per desktop QUI»* — is
   false for that call site.
2. ⛔ **The misaligned twin**, `11-accendi.sh:557-560`: same whitelist, but it covers **only C8b**.
   ⇒ Two places to open; opening only one, C8b(xfce) stays mute at 3.
3. ⛔ **The `xfce` box does not contain XFCE**: `Contenitore.xfce` installs `labwc xfce4-session
   xwayland`, ⛔ but **neither `xfce4-panel` nor `xfdesktop`** — a session born in there has no
   panel nor desktop. ⇒ The box grows, as `Contenitore.kde` grew (R5).
4. ⛔ **And the adapter does not start an XFCE session**: `adattatore.xfce.sh:32-43` launches `labwc`
   **bare** — no `--session xfce4-session`, no `XFCE4_SESSION_COMPOSITOR`. ⇒ Today that bench
   measures **a compositor**, not a desktop, and in particular it cannot spring the logout
   trap (§9.2 of the study).
5. ⛔ **The clipboard tools are missing** in the xfce box (and lxqt): no `wl-clipboard`,
   no `python3-gi gir1.2-gtk-4.0` — which kde and gnome have. ⚠ And ⛔ **the bench does not say so**:
   `11-c17:150` takes `stdout` without looking at the exit code, so `wl-paste: command not
   found` becomes `""`, the guard at `:242` (which checks `None`) does not fire, and the mesh prints
   **ROSSO** instead of "I could not look". ⛔ A missing tool must give 3.
6. ~~⚠ **C1 states the wrong cause**: on xfce it outputs *«nata CIECA»* while the fact is *«mai nata,
   perché il prodotto cercava `gnome-session`»*.~~ ✅ **CLOSED by increment 1, and without touching
   the bench.** ⭐ The diagnosis was false because the product was: now the session **is really
   born** and the image is not there, so *«nata cieca»* is literally exact. ⇒ It was a product defect
   disguised as a bench defect — and the way to find it out was to cure the
   product, not to retune the mesh.
7. ⚠ **C7(xfce) today is green partly on empty**, and the bench prints it (`11-c7:1184-1204`): the
   `/dev/dri` entry is empty in all three fingerprints *«perché senza compositore nessuno apre la scheda»*.
   ⇒ The day XFCE turns on, C7 becomes **stricter** — and may turn red for real
   reasons.
8. ⚠ **C11 would not see** the addition of `wl-clipboard`/`python3-gi` to xfce alone: they are not in
   its package list. ⇒ Either they go into **all four**, or they are added to the list.
9. ⚠ **The `desktop-nuovo` family will never fire by itself** for xfce: `decidi_famiglia`
   (`11-gancio.sh:345-357`) recognises a new desktop only from a `Contenitore.*` **not present**
   in `DESKTOP_NOTI`, and xfce is already there. ⇒ It must be asked for by name.
10. ⚠ **Ten stale comments** still say *«solo gnome»* or *«il prodotto ne sa accendere UNO»*
    (`11-gancio.sh:203-205`, `:1300-1307`, `:774` · `11-accendi.sh:23-24`, `:498`, `:511`, `:522`,
    `:533` · `11-c8b:56-59` · `11-c15:114-116`). ⛔ They are the ones one reads **before** testing
    on xfce.
11. ⭐ **An XFCE fault, invented and run** (`fasi/11-…` §3.6): today it does not exist, as KDE's
    did not.

⛔ **Opening the gates softens no verdict**: it is the condition for the meshes to look at
XFCE. They are opened in the increment in which the corresponding mesh **can** turn green, not before.

---

## The increments

| # | goal | mesh that tests it | status |
|---|---|---|---|
| **0** | the baseline on the **four** boxes | the whole net | ✅ **PASS** 20 Sep — 32 faults out of 32 |
| **1** | the XFCE session **is born** for a new user | none green yet: C1(xfce) stays red (capture missing) — tested with the I1 measurement | ✅ **PASS** — CP1 · CP2 · CP3 · CP4 · whole net |
| **2** | XFCE's image reaches the browser (`zwlr_screencopy`) | ⭐ **C1(xfce)** | ✅ C1(xfce) GREEN, 530 frames · ⛔ **swapped colours** found by the reviewer and cured · ⏳ colour test (C2) and net |
| **3** | mouse and keyboard reach XFCE (`virtual-keyboard`, `virtual-pointer`) | ⭐ **C4(xfce)**, and C3 · C6 on xfce | 🔧 written (agent, 21 Sep), `[M]` **tested on the laptop** against labwc 0.8.3 — ⏳ on the machine |
| **4** | the bench looks at XFCE like GNOME | ⭐ **C2(xfce)**, **C8b(xfce)** | 🔧 gates opened per capability (`11-capacita-del-prodotto.sh`), C17 gives 3 and not red — ⏳ on the machine |
| **5** | the clipboard on XFCE | ⭐ **C17(xfce)** | 🔧 written and built, **not tested** (21 Sep) |
| **6** | ⭐ the screen changes size with the session alive (`set_custom_mode`) — ⛔ **it can be done**, here: it is the fallback KDE had forced on us | to be defined | 🔧 `zwlr_output_manager` v4 written inside increment 2 — ⏳ on the machine |
| — | power, lock, dangerous entries (the user's decision of 21 Sep) | the 11-minute test | 🔧 written (agent) — ⏳ on the machine |
| — | the CARD route for capture (zero-copy, `gbm`) | stroke and CPU of labwc | 🔧 written (agent), `[M]` on the laptop: labwc's CPU **halved** — ⚠ **to be carried over by hand** on top of the rewritten `wlroots.c` |

⚠ **The order 2-3 may be reversed**, and the reason must be written the day it is decided: on KDE
capture came before input because it was the smallest; here they are **both big**, and
capture is the one that turns a mesh green.

### Increment 1 — the XFCE session is born *(CP1 sketched on 20 Sep; CP2 not yet done)*

| | |
|---|---|
| **GOAL** | a user who connects for the first time, on a machine that has **only** XFCE, gets from the product an XFCE session **of their own**, without a physical screen, and the product **recognises it alive**. ⛔ No capture, no input, no clipboard. ⛔⛔ And **no size**: on wlroots the output is not born at the requested size — resizing is increment 6, and this is written in the goal instead of being discovered |
| **INVARIANT** | on GNOME and on KDE **nothing changes**: same desktop recognised, same drop-in, same command, same times. On XFCE no second session, no leftovers after closing (C7). ⚠ Machines with several desktops are out of scope (`DECISIONI.md` §0.6) and stay as today |
| **MODULES** | `src/sessione.c` + `src/sessione.h` · `banchi/11-scatole/Contenitore.xfce` · `banchi/11-scatole/adattatore.xfce.sh` |

#### ⭐⭐ The cure is not "add XFCE to the list": it is **remove the fallback**

⛔ Today `riconosci_desktop()` has a fourth case (`src/sessione.c:295-299`): no known
desktop ⇒ **GNOME as a fallback, silently**. That is where an XFCE-only machine falls.

⚠ And the fault **does not show up where one thinks**: `scrivi_dropin()` (`src/sessione.c:1175-1189`) rereads
the `ExecStart` of `org.gnome.Shell@wayland.service`, a unit that does not exist, gets an empty
answer and writes *«un altro drop-in vince sul mio»*. ⛔ **The symptom blames someone else's drop-in; the
cause is that GNOME is not there.** `[?]` to be confirmed in CP2.

⇒ With "one desktop per machine" (§0.6) that branch is **the only place where the product can
get the desktop wrong, and it gets it wrong silently**. If increment 1 added XFCE leaving it there, the
day of LXQt would repeat identically. ⇒ After the cure the fourth case says **"I recognise no
desktop"** and starts nothing. ⚠ It is a change of behaviour on a machine without a
desktop, and it is declared.

#### ⛔ The three dangers the survey found, which are not branches to add

1. ⛔⛔ **A guard that evaporates, without a log line.** `unita_inattiva()`
   (in `src/sessione.c`) protects from the second session by asking systemd whether the compositor's
   unit is stopped; `unita_ferma()` (`:1290-1300`) accepts `unknown` ⇒ **it answers true for
   a unit that does not exist**. On XFCE, where there is no unit, the protection paid for on 16 Aug 2026
   **would not fail: it would vanish**. A real fact is needed (name absent from the bus **and** no `labwc`
   of the user).
2. ⛔ **`scrivi_dropin()` has no object on XFCE**: it exists because the compositor is a systemd user
   unit — true for GNOME and KDE, **false here**. It is not a branch to add: it is a function that
   on this desktop has nothing to talk about, and the branch must **declare it in the log**, not pretend
   to have written.
3. ⛔ **Thirteen implicit negations.** There is no literal `!e_kde()` in `src/`: the
   negation is always an `else` or a fall-through at the end — `:345`, `:550`, `:908`, `:1084`, `:1406`,
   `:1537`, `:1751`. ⚠ Adding a third value to the enum turns them **all together** from
   "GNOME" into "GNOME **or** XFCE", ⛔ **without a compiler warning**. Forgetting a single one does not
   give an error: it gives an XFCE session that is born with GNOME's environment.

⚠ And a fourth, not cured here but declared: `sessione_assicura()` (`:1891-2086`) is **dead
code** (no caller), ⛔ but its `case SESSIONE_SANA` (`:1902-1931`) would bring down a
healthy XFCE session. It is not touched, it is written down.

#### CP2 — observed, not deduced (`[M]` 20 Sep 2026, inside `rete11-xfce`)

**(1) What the product does today on an XFCE-only machine.** ⭐ The start-up line **tells the truth**:

> `il desktop di questa macchina: GNOME per ripiego — ⛔ non trovo NE' gnome-session NE'
> startplasma-wayland: nessuna sessione grafica potra' nascere`

⛔ **But then the fault blames two innocents**, and the survey's hypothesis is confirmed to the letter:

| `[M]` the line | what it makes one believe |
|---|---|
| `⚠ «gnome-shell» non e' nel PATH: ripiego dichiarato su /usr/bin/gnome-shell` | honest |
| ⛔ `ho scritto «--headless --no-x11» e il gestore dice un'altra cosa: un altro drop-in vince sul mio. ExecStart in vigore:` *(empty)* | ⛔ **blames someone else's drop-in**; the cause is that GNOME is not there |
| ⛔ `senza il drop-in in vigore non la faccio nascere` | consequence of the previous one |
| ⛔ `nessun monitor virtuale da catturare: ScreenCast: Mutter non espone RemoteDesktop (la sessione grafica e' avviata?)` | ⛔ **blames Mutter**, which does not exist on that machine |

⇒ And C1 reads **only the tenant's slice**, where the true line is not: that is why it says *«nata
CIECA»* instead of *«il prodotto cercava gnome-session»*. Two diagnoses, one face.

**(2) ⛔ The danger of the evaporating guard is CONFIRMED.** `[M]` Inside the box, for a unit
that **does not exist**: `systemctl --user is-active org.gnome.Shell@wayland.service` → **`inactive`**,
code 4. ⇒ `unita_ferma()` (`src/sessione.c:1290-1300`) accepts `inactive` and answers **true**: on
XFCE the guard against the second session would not fail, **it would vanish**.

**(3) ⭐⭐ The headless XFCE session is born, and it is born whole.** `[M]` Recipe by hand inside the box
— `labwc --session xfce4-session` with the environment of `STUDI.md` §xfce §9.3 — alive together:
`labwc` · `xfce4-session` · `xfce4-panel` · `xfdesktop` · `xfsettingsd` · `xfconfd` · `Thunar`.
⭐ And `org.xfce.SessionManager` appears on the **USER bus**, not on a private one: ⇒ running
`labwc` directly (without going through `startxfce4 --wayland`, which brings `dbus-run-session`)
**decision 4 resolves itself** — the product sees the session's liveness with the code it already
has.

**(4) ⛔ The output is born 1280×720, and the client does not decide it.** `[M]` `HEADLESS-1, 1280×720,
refresh 0.000 Hz`. ⇒ On wlroots the size **does not enter the birth**: it is given afterwards, with the protocol.
⚠ And this weighs on the order of the increments — an image delivered at 1280×720 while the client
asks for 1920×1080 is not useful, so increment 6 may have to move up next to 2.

**(5) ⭐⭐ The protocols are ALL there — 47 globals announced, and these are the ones that count:**

| serves | protocol | `[M]` |
|---|---|---|
| **capture** | `zwlr_screencopy_manager_v1` | **v3** |
| capture, the other route | `zwlr_export_dmabuf_manager_v1` | v1 — ⭐ direct DMA-BUF export, which `STUDI.md` had not weighed |
| **keyboard** | `zwp_virtual_keyboard_manager_v1` | v1 |
| **mouse** | `zwlr_virtual_pointer_manager_v1` | v2 |
| **clipboard** | `zwlr_data_control_manager_v1` | **v2** — ⭐ it is exactly the one `src/appunti_kde.c` already speaks |
| **output size** | `zwlr_output_manager_v1` | **v4** — ⇒ hot resizing **can be done** |
| power (who turns the output off) | `zwlr_output_power_manager_v1` | v1 |
| the panel and the desktop | `zwlr_layer_shell_v1` | v4 |
| buffers | `zwp_linux_dmabuf_v1` v4 · `wp_presentation` v1 | |

⛔ **Absent, and it must be known before writing**: `ext_image_copy_capture_manager_v1` (screencopy's
successor: ⇒ we write against `zwlr_screencopy`, not against it) and
`wp_linux_drm_syncobj_manager_v1` (explicit fences: ⇒ synchronisation must be solved
differently). ⚠ And `ext_data_control_manager_v1` is not there — as on KWin, and as `STUDI.md` predicted:
the route stays `zwlr_data_control`.

**(6) The box has grown**, and the recipe declares it (R6): `xfce4-panel`, `xfdesktop4`,
`xfce4-terminal`, `thunar`, `nano`. ⛔ It is not cosmetic: without `xfdesktop` and `xfce4-panel` two of the ways
in which the birth fails — `exit(1)` without layer-shell, and the silent exit with `n_monitors == 0` —
**cannot even be seen**.

#### ⭐ The test, and the negative check that is worth more than the test

- **negative check of the fallback**: same box, **today's binary** ⇒ the start-up line says
  *«GNOME per ripiego»* and the session is not born; **cured binary** ⇒ it says *«XFCE»* and it is born. It is the
  proof that the cure hit the right branch and not another.
- ⭐ **the test of the logout trap** (no analogue on KDE): if the compositor's line does not
  contain **both** `labwc` **and** `--session`, at logout `xfce4-session` runs `loginctl
  terminate-session ''` — that is, it **kills REMOTIX's logind session**, not only the desktop.
  ⛔ `STUDI.md` §xfce §9.2 says to test it **on the bench and never on the user**.
- ⚠ **the waiting cap must be justified**, not copied from KDE: on Wayland no XFCE client
  registers and every priority group unblocks at timeout — `STARTUP_TIMEOUT_WAYLAND` = **8 s
  per group**, structural and not shortenable.
- ⚠ **the xfconf belts are reread**: `xfconf-query` exits with zero even when the daemon has
  refused and restored the value. A successful write is not an applied configuration.

#### CP3 — the minimal change (`src/sessione.c`, `src/sessione.h`)

⭐ **Two files, and no GNOME or KDE branch touched**: every new block sits **before** GNOME's
and returns with `goto la_coda` or `return`, so the old branches stay textually the same.

| # | where | what |
|---|---|---|
| 1 | `sessione.h` | `SESSIONE_RIGA_XFCE` / `SESSIONE_COMANDO_XFCE` — ⭐ **the line is written once and used twice** (command, and `XFCE4_SESSION_COMPOSITOR`): writing it twice would mean they could diverge, and diverging would spring the logout trap without a line saying so |
| 2 | `sessione.h` | enum: `SESSIONE_DESKTOP_XFCE = 2`, `SESSIONE_DESKTOP_NESSUNO = 3` — ⚠ **at the end**, because the number travels as `uint32_t` between parent and child |
| 3 | `riconosci_desktop()` | the `xfce4-session` branch, **after** GNOME and KDE; ⛔ and the fallback **removed**: whoever recognises nothing now says so |
| 4 | `e_xfce()` · `e_nessuno()` | ⛔ and never a `!e_kde()`: the thirteen implicit negations are the danger, and the way not to fall into it is written above the two functions |
| 5 | `nodo_della_scheda()` | the node is **opened**, not hard-wired: `renderD128` and `renderD129` swap between two boots, and if the opening fails wlroots falls back to pixman **silently** |
| 6 | `sessione_viva()` · `sessione_stato()` | the name `org.xfce.SessionManager` on the user bus, with it declared that "alive" does **not** mean "of the right size" |
| 7 | `componi_ambiente()` | ten variables, each with its reason — ⭐ and the "to remove" column was already free: the function builds from scratch |
| 8 | `scrivi_dropin()` | ⛔ on XFCE it **has no object**, and it says so instead of returning `TRUE` silently |
| 9 | `avvia()` | the three-way command, not a nested ternary |
| 10 | `unita_inattiva()` | ⛔ the guard that would have **vanished**: two facts are looked at (`/proc` and the name on the bus) instead of asking systemd about a unit that is not there |
| 11 | `sessione_termina()` | `Logout`, then **SIGTERM to labwc** — here the force is not systemd. ⚠ `SIGTERM` and not `SIGKILL`: labwc closes its clients, and a `SIGKILL` would leave behind precisely what C7 looks for |
| 12 | `sessione_impostazioni()` | the belt `WaylandLogoutCommand=/bin/true`, ⭐ **reread**; the cache of saved sessions deleted; the rest declared postponed |
| 13 | `sessione_inibisci()` | ⛔ **declared no-op**: `xfce4-session` does not consult the inhibitor, so asking would give a ⛔ false one and zero protection |
| 14 | `sessione_fai_nascere()` | the honest refusal when there is no desktop — ⭐ **in the tenant's slice**, where the bench reads it |
| 15 | `nome_desktop()` | ⚠ `LEZIONI.md` §1.9: the cursor theme, written for KWin and reused by labwc, announced "⭐ **Plasma**" inside an XFCE session. The line is not duplicated: it is made to say the right name |

#### CP4 — the test (`[M]` 20 Sep 2026, binary `48c87296`)

| what | expected | measured |
|---|---|---|
| the desktop recognised, in the four boxes | four different and right answers | ⭐ gnome → *GNOME* · kde → *KDE Plasma* · xfce → ⭐ *XFCE (c'è xfce4-session, e labwc per farlo girare)* · lxqt → ⛔ *NESSUN DESKTOP RICONOSCIUTO* |
| **the XFCE session is born** for a new tenant | labwc + xfce4-session alive | ⭐ **and it is born whole**: `labwc` · `xfce4-session` · `xfce4-panel` · `xfdesktop` · `xfsettingsd` · `xfconfd` · `Thunar` · `wrapper-2.0` |
| the product **recognises it alive** | the name on the user bus | ⭐ *«il gestore di sessione XFCE c'è sul bus: la sessione è viva»* |
| how long it takes | ≥ 8 s (priority groups) | `[M]` **17.0 s** from «la faccio nascere» to the name on the bus (clean round at 21:40). ⚠ A second round gave 0.4 s and **I do not count it**: the log had not been truncated again, and two measurements that cannot be separated are not averaged — `[?]` to be redone clean before tuning the bench's cap |
| the logout belt | written **and reread** | ⭐ *«WaylandLogoutCommand = /bin/true, RILETTA»* |
| the card given to wlroots | opened, not deduced | ⭐ *«la scheda che do a wlroots è /dev/dri/renderD128 (aperta, non dedotta)»* |
| the drop-in | declared absent, not faked | ⭐ *«nessun drop-in da scrivere … E la tela chiesta (1920x1080) NON entra nella nascita»* |
| **C7(xfce)** — it closes and nothing remains | green | ⭐ **GREEN**, 1.15 s. ⚠ And the bench declares by itself that one entry (`/dev/dri`) still passes **on empty**: the session does not open the card until there is capture |
| **C1(xfce)** | ⛔ **red, and for a NEW reason** | ⛔ red: *«nate CIECHE»*. ⭐ And now it is literally true — the session is there, the image is not: that is increment 2 |
| **C1(gnome)** · **C1(kde)** | green, unchanged | ⭐ **both green**, 2 sessions out of 2 each |

⚠ **What remains crooked and is declared**, because the next increment cures it: on XFCE capture
still falls into Mutter's branch and writes *«Mutter non espone RemoteDesktop»* — ⛔ a line that blames
an innocent. It is the same point where KDE's increment 1 stopped, and it is the first thing that
increment 2 removes.

#### The whole net (`[M]` 20→21 Sep 2026, 23:48→03:00, binary `48c87296`, 11 460 s)

| | |
|---|---|
| **GNOME** | ⭐ **all green**, C17 included — identical to CP0 |
| **KDE** | ⭐ **all green**, and ⭐⭐ **C2(kde) is judging again**: 0 · 0 · 0 where at CP0 it gave 3 · 3 · 3. The cure of the "before" (240→900) holds, and its **two injected faults are seen** |
| **xfce** | passo0, C5, C7, C8, C9 green with the faults · ⛔ **C1 red** — and that is increment 2, declared |
| **lxqt** | the same as xfce — ⚠ and its red C1 now has a **new and right** cause: the product tells it to its face that it **recognises no desktop** |
| the net | C11 green (same binary in the four) · C13 green · C14 green, 786 s |
| ⭐ **injected faults** | **34 out of 34 seen** — two more than CP0, and they are precisely the two of C2(kde) that CP0 had not been able to certify |
| reds | **2**, and they are the two declared |

⇒ ⭐ **Increment 1 passes the gate**: XFCE gained the birth of the session, GNOME and KDE
lost nothing, and the net can still give red.

---

### Increment 2 — XFCE's image reaches the browser *(CP1, 21 Sep 2026 — not yet started)*

| | |
|---|---|
| **GOAL** | a client attached to the XFCE session **sees the desktop**: real frames, that change. The mesh that tests it is **C1(xfce)**, the same that tested it for Plasma |
| **INVARIANT** | on GNOME and on KDE **nothing changes**: same route (PipeWire), same numbers, same damage book. ⛔ And the DMA-BUF consumer of phases 8-9 **is reused, not rewritten** |
| **THE DECISION THAT GOVERNS IT** | ✅ **direct** capture (`zwlr_screencopy_manager_v1` v3), the user's, 20 Sep 2026 |

#### ⛔ The difference that does the work, and it is not the protocol: it is the direction

On GNOME and on KDE the compositor **pushes**: it mounts a PipeWire stream and the frames arrive by
themselves. All of `src/cattura.c` (2 348 lines) is built on that direction, and `figlio.c` uses it at **35
points** through ten functions (`cattura_avvia` ×7, `cattura_prendi` ×5, `cattura_fermo_libera`
×7, `cattura_ridimensiona` ×3, `cattura_risveglia` ×3, …).

⛔ On wlroots one **pulls**: `capture_output → frame → copy → ready`, **one request per
frame**, and no PipeWire node anywhere. ⇒ The rate is not a property of the
compositor: **it is our loop** — which is precisely what the user's decision
bought.

⚠ **And the design question to be resolved in CP3** is only one, and it must be posed well: does the second source
go **next to** `Cattura` (a source that is chosen, and the thirty-five points of `figlio.c`
stay where they are) or **under** it? ⛔ The answer is not chosen by taste: it is chosen by
measuring how many of the ten functions make sense in the pull direction. `cattura_ridimensiona`, for
example, on wlroots **is not the same thing**: there the size is changed on the output, not on the stream.

#### What has already been measured, and must not be measured again

| | `[M]` 20 Sep 2026, inside `rete11-xfce` |
|---|---|
| the protocol | `zwlr_screencopy_manager_v1` **v3** — and there is also `zwlr_export_dmabuf_manager_v1` v1, a second route that `STUDI.md` had not weighed |
| the permission | ✅ **does not exist**: no `.desktop`, no portal, no dialog |
| the card's buffer | `zwp_linux_dmabuf_v1` **v4** |
| ⛔ explicit fences | **absent** (`wp_linux_drm_syncobj_manager_v1` is not there) ⇒ synchronisation must be solved another way, and measured |
| ⛔ the successor | `ext_image_copy_capture_manager_v1` **absent** on Trixie ⇒ we write against screencopy, knowing it |
| ⛔ the output size | it is born **1280×720** hard-wired, and the client asks for 1920×1080 |

#### CP2/CP4 of the first step — `[M]` 21 Sep 2026: **the pixels arrive**

⭐⭐ The module `src/wlroots.c` + `src/wlroots.h` exists, and the bench
`banchi/13-w1-un-fotogramma.c` tests it inside a live XFCE session.

| what | measured |
|---|---|
| frames pulled | ⭐ **10 out of 10**, then 3 out of 3 — none failed, none timed out |
| the output | `HEADLESS-1`, **1280×720**, stride 5120 |
| the format | **XB24** (`XBGR8888`) — ⚠ **not** the one that would have been taken for granted |
| the content | **199-201 distinct colours**, 6.1 % of the samples non-black ⇒ it is a real desktop, not a switched-off screen |
| the time per frame | `[M]` **8.8-14.9 ms** on average, 16.5 ms the worst — ⚠ and it is the WHOLE round with the copy to memory, on Intel UHD 730 |
| the pointer | **inside the image** (`overlay_cursor = 1`), as expected: on this family there is no channel for its shape |

#### ⛔⛔ And a trap paid for at once, which is worth more than the frame

`[M]` The first draft of the bench wrote the channels in the order of `XRGB8888`.
The image came out **with orange folders** — and it looked right: an Xfce
desktop with pumpkin-coloured icons is perfectly plausible. ⛔ But labwc declares
**XBGR8888**, which in memory is `R G B X`: **R and B were swapped**, and the real
Adwaita folders are **blue**.

⇒ ⭐ It is `LEZIONI.md` §1.9 in its worst form: **a check that gives a
plausible result is not a check**. The fact is asked of the format — which
says it — instead of being deduced from how it looks. ⚠ And had it reached the
encoder, the user would have seen a blue desktop without a line
explaining it.

#### CP3/CP4 — `[M]` 21 Sep 2026: **C1(xfce) is GREEN**

⭐⭐ **The second source goes UNDER the capture's door, not next to it.** Like the clipboard, which
already has two constructors behind a single door at home. ⇒ `figlio.c` uses that interface at **35
points and changes none of them**: GNOME and KDE stay textually as they were.

| file | what |
|---|---|
| `src/wlroots.c` · `.h` | the Wayland client: `zwlr_screencopy` v3 (the frames) and `zwlr_output_manager` v4 (the size) |
| `src/cattura.h` | `cattura_avvia_wlr()`: the constructor of the other direction |
| `src/cattura.c` | the `wlr` field at the top of `struct Cattura`, and a guard at the top of every public function |
| `src/figlio.c` | the third branch of the stage: on XFCE **there is nothing to open**, the source is the capture |
| `banchi/13-w1-un-fotogramma.c` | the bench, which links **the same objects as the product** (R12.3) |

| the test | measured |
|---|---|
| **C1(xfce)** | ⭐⭐ **GREEN**, 3 sessions out of 3 |
| C1(gnome) · C1(kde) | ⭐ green, 3 out of 3 each |
| the **real** frames | ⭐ **530 delivered, 19 keyframes, 0 faults** |

⛔ **And that last row is the one that counts**: C1 reads a log line, and a line can be
written. Frames cannot. ⇒ They are counted on purpose, because the green of a mesh that looks at the
log is not worth anything until the traffic has been seen to pass.

#### ⛔⛔ Three defects found by TESTING, and two by REREADING

By testing:
1. `mutter_monitor_cerca(NULL)` — a failed assertion in the log. Noise that looks like a
   fault: on wlroots the monitor is the compositor's output, and there is no Mutter session.
2. The witness *«formato negoziato: LxA»* was written by PipeWire's callback, which does not
   exist here. ⇒ Without it, the mesh would have said *«nata cieca»* of a session that is perfectly visible.
3. The divergence between the **requested** canvas (1920×1080) and the **real** output (1280×720): now it is declared
   on the first line.

⭐ By rereading one's own code, **before they were seen**:

4. **The buffer reused after an abandoned copy.** Once a frame is dropped after sending `copy`,
   the compositor may write into it **later**: reusing it gives an old frame among the
   new ones — ⛔ not an error, a **flicker**. It is `LEZIONI.md` §8 (it was not *acquire*, it was
   *release*). ⇒ Whoever abandons after `copy` marks the buffer.
5. ⛔⛔ **The swapped channel, all the way to the encoder.** `figlio.c` declares
   `CODIFICATORE_PIXEL_BGRX` — `B G R x` in memory, fixed since phase 2 — and labwc offers
   **XBGR8888** first, which is `R G B x`. ⇒ **The user would have seen the desktop with red and blue
   swapped**, without a line explaining it.
   ⭐ And the cure is not teaching a new format to the encoder, which GNOME and KDE use: it is
   **asking for the one we already know how to read**. On screencopy v3 the compositor offers more than one
   on purpose, and `buffer_done` exists for this. ⚠ And the offered list ends up in the log, because the
   day the channels come out crooked the first question is *«che cosa offriva il compositore?»*.

⭐ **The same trap, twice in one day, and the second did not reach the user.** The first
had been paid for by the bench (**orange** folders that looked right, and were blue instead). ⇒ It is
`LEZIONI.md` §1.9 in the worst form: **a plausible result is not a confirmation**.

#### ⚠ And the order with increment 6 must be decided here, not at once

An image delivered at **1280×720** while the client asked for one at **1920×1080** is not
"the image that arrives": it is a wrong image. ⇒ Either increment 2 also takes
`zwlr_output_manager_v1` (which is there, v4), or C1(xfce) will stay red for a reason that is not the
capture. **It is decided with the first frame in hand**, not before.

---

### Increment 5 — the clipboard on XFCE *(written and built on 21 Sep 2026; C17(xfce) not yet run)*

⭐ **The module was already there**: `src/appunti_kde.c` speaks `zwlr_data_control_manager_v1`, which is
wlroots'. The change is five files and does not touch the protocol:

- `appunti_kde.c`: the opening becomes `apri_su(compositore)`, with two doors —
  `appunti_kde_apri()` («KWin») and `appunti_kde_apri_wlroots()` («labwc»). The name serves **only** the
  three log lines; on KDE they come out identical letter for letter;
- `src/appunti.c` and `src/appunti.h`: `appunti_apri_wlroots()`, the same wrapper as `appunti_apri_kde()`;
- `figlio.c`: if `sessione_desktop() == SESSIONE_DESKTOP_XFCE` that one is opened, **first**; the
  KWin/Mutter branch below is the one from before.

⚠ **`kwin_display_apri()` stays**, declared: it takes `WAYLAND_DISPLAY` or the first `wayland-0..9` that
answers, without looking at who is behind it `[R]` (`kwin.c`). Moving it into a neutral file would mean
touching `kwin.c`, which carries KDE's video, to gain only a name. ⇒ Reservation 1 of
`STUDI.md` §xfce §8 is **closed**.

**The other reservations, reread on the wlroots 0.18.2 source** (`sources.debian.org`, 21 Sep 2026):

| reservation | outcome |
|---|---|
| the echo | ⭐ **certain, and the guard holds** `[R]`: every device is subscribed to `set_selection` without a filter (`wlr_data_control_v1.c:459-468`); `wlr_seat_set_selection` destroys the old source (⇒ `cancelled`, `:145`) **before** emitting the signal, and the two notices travel on the same connection |
| duplicate MIME ⇒ loop | ⭐ **cannot fire** `[R]`: wlroots discards only `strcmp`-equal duplicates (`:38-45`), and we always offer only the three types of `TIPI_TESTO`, all different. It was a risk of v1, which passed on the client's list. ⚠ And if the guard broke there would still be no loop: reading our own source from the pump that serves it times out in 5 s without delivering anything |
| `onlyReplaceEmpty` | ⭐ **no harm** `[R]`: we never offer it and never read it |
| the selection that dies with whoever copied | ⚠ **true, and not ours**: in XFCE on Wayland there is no manager. `selection(NULL)` arrives ⇒ nothing is sent to the client, and the client keeps the last text. **Our** source (the client's text) lives as long as the child |

⛔ **To test it** (C17 on xfce) the box must have the clipboard tools — see point 5
of the bench above: without `wl-clipboard` the mesh reads `""` and does not say so.

## 🔸 The choices waiting for the user

The five of `STUDI.md` §xfce §13, plus the three that came out of the survey of 20 September. ⛔ They are put
**when the measurement that concerns them has been done**, not before.

| # | the choice | when it is put |
|---|---|---|
| ~~**1**~~ | ✅ **DECIDED on 20 Sep 2026, by the user: DIRECT capture.** *«Li chiediamo noi»* — rate, cursor and size stay ours, and the DMA-BUF consumer of phases 8-9 is reused whole. ⛔ The PipeWire bridge is excluded: four processes inside a 16.6 ms budget, and none of the three things above | ⭐ done |
| **2** | is hot resizing turned on at once or later? | increment 6 |
| **3** | the cursor inside the image or on the pointer channel? | increment 3 |
| **4** | the session bus: `dbus-run-session` (private) or user bus? ⛔ With the private one the session's liveness is **blind** for the product as it is written today | increment 1, after CP2 |
| ~~**5**~~ | ✅ **DECIDED on 21 Sep 2026, by the user**: *«anche in XFCE vanno disabilitate le voci di standby, lockscreen, reset e spegnimento»* — the same as GNOME and KDE (`DECISIONI.md` §4.7). ⛔ **"Log Out" stays** (§4.1-ter): it is the only gesture that ends the session. ⚠ "Switch User" was not named: it stays open | in progress |
| **6** | "alive" = the name on the bus, or `StateChanged(0→1)`? The first is a two-line branch; the second is a **signal watcher**, which does not exist in `sessione.c` | increment 1, after CP2 |
| **7** | how much does `Contenitore.xfce` grow: panel and desktop already in increment 1? | increment 1 |

⚠ **And one thing decision 1 carries along, known from the first day.** The XML of
`wlr-screencopy-unstable-v1` — put in the repository in `src/protocolli/` on 20 Sep 2026, and verified
by regenerating the code on it: the tables come out **identical** to those v1 had generated — carries
at the top a new line compared to then:

> *«This protocol is deprecated and not intended for production use. The ext-image-copy-capture-v1
> protocol should be used instead.»*

⛔ But `[M]` 20 Sep 2026 labwc on Trixie **does not expose** `ext_image_copy_capture_manager_v1`: there is
nothing to use in its place. ⇒ We write against screencopy **knowing it**, and `STUDI.md` §xfce §4.6
already says how: the code is written so that the second actuator can come in next to the first, not
in its place.

---

## The measurements

| what | expected | measured | date |
|---|---|---|---|
| **CP0** — `tutto` round on the **four** boxes, launched on the server | GNOME green; KDE green for all of the certificate; on xfce/lxqt only C1 red; faults all caught; a single binary | ⚠ **as expected except one cell**, explained and cured — see below | `[M]` 20 Sep 2026, 16:19→19:31 |

### CP0 in detail — binary `9e3154a6`, 11 521 s, 86 meshes

| | |
|---|---|
| **GNOME** | ⭐ **all green**: passo0, C1×10, C2 (+2 faults), C3 (+still scene +2 faults), C4 (+2), C5, C6, C7, C8, C8b, C9, **C17 (+fault)** |
| **KDE** | green everywhere **except C2 ×3, exit 3** — ⚠ the only unexpected difference of the round, classified **C (bench defect)**: see below |
| **xfce · lxqt** | passo0, C5, C7, C8, C9 green with their faults · ⛔ **C1×10 RED** on both (the phase's mandate) · C2 C3 C4 C6 C8b **and C17** skipped by the "only GNOME and KDE" gate |
| **the net** | C11 green (same binary in the four) · C13 green · **C14 green, 786 s, four boxes** · C10 C12 C15 C16 at 2/3 because the git repository is not on the server — declared, it is not a red |
| ⭐ **injected faults** | **32 out of 32 seen** |
| reds | **2**, and they are the two declared: `C1(xfce)` and `C1(lxqt)` |

⇒ ⭐ **C17 on GNOME is green inside a complete round**: increment 13 of phase 12 closes here, and
that cell stops being "tested by hand".

#### ⛔ The only unexpected difference — C2(kde), and it was not the product

`[M]` In the round, C2(kde) came out **3** all three times (healthy + two faults): *«i primi 240
fotogrammi sono tutti neri o quasi: il desktop non aveva niente da mostrare PRIMA
dell'applicazione»*. ⛔ But **the window had opened**: the round's "after" image is the declared
colour covering the screen. ⇒ The bench did not have the **term of comparison**, and abstained —
which is its duty, not a defect of judgement.

`[M]` Measured again at once, on the same box, **three times**: **186** · **186** (box rebuilt from
scratch) · **189** (⭐ and with the host's cache emptied, to get the cold disk out of the way).
⇒ The real number is **~187 and stable**: the margin on 240 was **54 frames, 29 %**.

`[?]` Why more are needed inside the complete round (379 frames in all against 249) is not
measured. The suspicion is written: between two benches on the same seat **the previous seat stays
attached for about twenty seconds**, and C2(kde) in the round comes right after C9(kde), which made
two sessions.

⭐ **The cure is a cap that does not bite**, not a cap retuned to the hair: `--fotogrammi-prima` from 240 to
**900**, that is more than the stream has ever had. ⛔ And **the verdict does not change one
iota** — the yardstick stays the colour that grows by 20 points and covers 25 %: only how
long the bench looks for its own term of comparison changes, and the search **stops at the first frame
drawn**, so raising the cap costs nothing when the desktop paints early.

#### ⚠ And two misalignments closed in the same round

1. **Images behind the recipes**: `Contenitore.gnome` and `Contenitore.kde` had been
   touched by increment 13 (`nano`, `python3-gi`, `gir1.2-gtk-4.0`) but the images had not. ⚠ No
   mesh depended on it (`[M]` gnome had `gi` as a dependency; on kde C17 uses `wl-clipboard`), but
   at the next test by hand `nano` would not have been there. ⇒ **Rebuilt**, and the four boxes
   carry the same binary `9e3154a6`.
2. **The waiting cap of the remote delegation** was 2 400 s against rounds of 11 521: the waiting half
   gave up after 40 minutes saying "I could not look" **while on the other side it was still
   measuring**. ⇒ `ATTESA_REMOTA` to 14 400, and written that the real protection is not the cap but the
   question about the remote unit.

### ⭐ The certification — binary of `4cd86a0`, 21 Sep 2026, 14 697 s

`tutto` round on the four boxes **rebuilt from scratch**, trigger `fase13-danno-scheda`, launched on the
server at 13:26 UTC and closed at 17:31 UTC.

| | |
|---|---|
| ⭐ **XFCE** | **27 meshes out of 27 green**: passo0, C1×10, C2 (+2 faults), C3 (+still scene +2 faults, **including "encoder stopped"**), C4 (+2), C5, C6, C7, C8, C8b, C9, **C17 (+fault)** |
| **GNOME · KDE** | no regression: green as at CP0 |
| **lxqt** | as at CP0: the product does not recognise it, and the product's meshes skip saying so |
| **the net** | C11 C13 C14 green on the server · ⭐ **C10 C12 C15 C16 run on the laptop, where the repository is: all green** |
| ⭐ **injected faults** | **43 out of 43 seen** |

⇒ **XFCE is in the protected perimeter**, next to GNOME and KDE.

#### The two cures the net asked for before giving green

1. ⛔ **C3(xfce) did not see the "encoder stopped" fault** (net of 10:27): labwc delivered
   **60 identical frames per second** on a still desktop, and a stream that does not change cannot
   tell a stopped encoder from a healthy one. ⇒ **`copy_with_damage`** (screencopy v2+): the
   compositor answers only when the screen changes. ⚠ Which broke C4(xfce) at once: a pending
   "with damage" copy blocked the forced full frame ⇒ if the stage must give a full
   frame and there is a damage copy pending, **it is abandoned**. `[M]` Then: 62 fps on the
   card route, C3 and C4 green with their faults.
2. ⛔ **C17 red on all three desktops** — classified **C (bench defect)**: the referee's
   file in `/tmp` had a fixed name, belonged to another user, and my tests by hand
   had dirtied it. Proved by bisection (yesterday's binary was red too in the dirty
   box; the new one green in a clean box). ⇒ Name per user, removed at the end.

### ⭐ The real clients — 21 Sep 2026, evening, port 8513

`banchi/12-client-veri.py`, **certified first** (empty port and wrong password seen on both
browsers):

| browser | verdict | what |
|---|---|---|
| **Firefox 140** Linux | ⭐ **PASS** | form · admitted · first frame in 1.0 s · 84 frames in 8 s · key and mouse in the server log · 0 errors · reconnection |
| **Chrome 153** Linux | ⭐ **PASS** | same: 85 frames in 8 s, first frame at once, reconnection |
| **Chrome Android** | ⏳ **to the user** | the emulator has not launched it since phase 12: the validation stays his, as for KDE |

`[M]` The photo of the desktop: panel at the top, Home and File System icons, the dock at the bottom, the
folders **blue** (the channels are right). ⚠ The wallpaper is **black**: the box lacks the
wallpapers package — it is the box, not the product.
⚠ The page says "unknown desktop" on XFCE — ⛔ **and it says it on GNOME and KDE too**: the server
sends the fixed string of phase 1 (`src/rcp.c`, message `SESSIONE`). It does not belong to this phase, and
touching it would touch GNOME and KDE: it stays as it is.

### ⭐ The entries that switch off — decision 5

`[M]` In the box, with the session on:

| | |
|---|---|
| the panel's user menu | `-lock-screen`, `-suspend`, `-hibernate`, `-hybrid-sleep`, `-shutdown`, `-restart` · ⭐ **`+logout` is there** · `+switch-user` is there |
| xfce4-session | `LockCommand=/bin/false` · `ShowSuspend/Hibernate/HybridSleep=false` · `WaylandLogoutCommand=/bin/true` |
| xfce4-power-manager | `dpms-enabled=false` · inactivity 0 |
| the "Log Out" window of the Applications menu | restart and shut down **greyed out**: the polkit rule `50-remotix-niente-spegnimento.rules` is there, logind denies `CanPowerOff`/`CanReboot` and says `CanSuspend=no` (`sleep.conf`) — belt 1 of `DECISIONI.md` §4.7, the same for all desktops |
| ⭐ **11 minutes of still session** | the screen is **still the desktop**: no lock, no black, no screensaver around |

### ⭐ The logout trap — `banchi/13-w2`

| mode | outcome |
|---|---|
| `--certifica` (the dry judge) | ⭐ 0 |
| healthy | ⭐ **GREEN**: the desktop disappears in 0.3 s, the logind session stays alive for all 20 s |
| `--senza-xfconf` | ⭐ fault **seen** |
| `--senza-variabile` | ⭐ fault **seen** |
| `--senza-cinture` | ⚠ **3**, declared: the session does not fall |

⭐⭐ **Why the trap does not bite** `[M]`: in Trixie's `xfce4-session` 4.20.2 binary the command
is written **`loginctl terminanate-session`** — an upstream typo. The command fails, and
the session saves itself. ⇒ **Today the trap sleeps**; the two belts stay, for the day
upstream corrects the word. ⛔ And the 3 of `--senza-cinture` stays a 3: the bench cannot
prove a defence against a blow that is not struck.

⚠ **And a correction to the bench, measured before making it.** The first draft required the
product's session to be `active` before the logout, and used `State=closing` as "fallen". `[M]`
But **on GNOME (baseline) and on XFCE** the product's session is `Service=remotix State=closing` **from
the first instant**, with the child alive: it is the state it always has, not a signal. ⇒ "Alive" now means
logind describes it **and** its Leader (the child) is alive; "fallen" means logind has
forgotten it **or** the child is dead. The dry judge stays certified.

## ⛔ What did NOT work

## What remains [?]

### ⭐ The state on 23 Sep 2026, evening — the four points before LXQt

The user, 23 Sep: *«prima si chiudono i punti aperti»*. How they were at 19 h and how they are now:

| # | point | status |
|---|---|---|
| 1 | **C20 does not look** ("I could not look" after "Log Out") | ✅ **CLOSED** — it was the 999 ms **fixed second**; cured, and in the final net C20 is green and sees the fault on all three |
| 2 | **long sessions** with real browsers only on kde/Firefox | ✅ **GREEN**: gnome and xfce, Firefox and Chrome, 20 min in 4K with the mouse moving, longest freeze **0 s** in all four |
| 3 | **the heartbeat guard** is not permanent | ✅ **DONE AND TESTED ON THE HARDWARE**: mouse in all the scenarios, 10 s threshold tuned, injected fault SEEN on gnome, kde and xfce |
| 4 | Chrome Android on XFCE | ⏳ the user's |

- ✅ **THE NET OF 23 SEP EVENING — no red** — binary `3fa352a2`, `--famiglia tutto`, gnome + kde +
  xfce, **14 571 s** (4 h 03). Every box **18 out of 18** in the basic checks, all injected faults
  SEEN, C14 (the three boxes alone and together) holds, "no red, neither here nor there".
  ⚠ The only gap: **C20 "I could not look" on all three**, in both rounds. It is the item below.

- ✅ **THE FIXED SECOND WAS 999 MS** — found and cured on 23 Sep 2026, evening (`612b0ed`), binary
  **`e681a262`**. `ora - cred_arrivo < RITARDO_FISSO` compared **truncated** milliseconds: a
  difference of 1000 can be 999.x real ms, and `AMMESSO` left **before** the second.
  `[M]` From the boxes' logs: **gnome 15 admitted out of 50 at 999 ms, kde 16 out of 50**.
  ⇒ The test client, which checks §4.4-bis, left saying "less than a second", and C20 at the
  second login was left without a client: on gnome the mesh, giving up, did `terminate-user` —
  **the signal 15 that in the journal looked like logind** —, on kde and xfce nobody reattached and the
  product, rightly, did not remake the desktop. ⭐ The cure is `<=`: one pays at most 1 ms.
  ⚠ **For the real user the effect was nil**: browsers do not make that check. It was the net that could
  not look — that is, a blind guard on one of the defects the user had found by hand.

- ✅ **C20 WITH THE REAL BROWSERS, IN 4K: GREEN EVERYWHERE** — 23 Sep 2026, evening (`b3b8f5b`), binary
  `e681a262`. New bench `banchi/12-c20-veri.py`: login, "Log Out" from the menu, **new login from the
  same page**, C20's scene, and the canvas photographed and judged with C20's judge. Real windows
  inside a **nested headless labwc at 3840x2160** (the specifications are 4K — the user, 23 Sep).

  | | Firefox 140 | Chrome 154 |
  |---|---|---|
  | **gnome** | ⭐ GREEN, 0 skips | ⭐ GREEN, 0 skips |
  | **kde** | ⭐ GREEN, 0 skips | ⭐ GREEN, 0 skips |
  | **xfce** | ⭐ GREEN ×3, 0 skips | ⭐ GREEN, 0 skips |

  In all of them: after "Log Out" the page goes back to the form with *«la sessione e' terminata: i programmi sono
  stati chiusi»*, and the new login has the image in 0.3–1.6 s. ⚠ Three defects **of the bench**, found
  by running it, are in the message of `b3b8f5b` (Chrome inside labwc wants "maximised"; xfce
  in 4K has a black wallpaper and the judge of `12-client-veri` called it degenerate; xfce's "Log Out" gesture
  launched without collecting stderr).
  ✅ And the net's C20 **mesh**, with the fixed second cured, **looks again**: final net of
  24 Sep night, **C20 GREEN on gnome, kde and xfce, and the injected fault SEEN on all three**.

- ✅ **THE FINAL NET OF 24 SEP NIGHT — no red** — binary `e681a262`, `--famiglia tutto`,
  gnome + kde + xfce, **14 498 s**. Every box **18 out of 18**, C20 green and fault seen everywhere,
  "no red, neither here nor there". C10 C12 C15 C16 "cannot look" from the server, as expected
  (they run on the laptop).
  ⭐ **THE FOUR POINTS BEFORE LXQt ARE CLOSED** except Chrome Android on XFCE, which is the user's.

- 🔸 **THE HEARTBEAT GUARD IS WRITTEN** — 23 Sep 2026 (`32511f9`). The moving mouse entered
  **all** the scenarios of `banchi/14-stress` that look at the screen, as normal client
  behaviour (`scenari/_comune.py`, the `Topo`; `REMOTIX_TOPO=no` turns it off for the counter-test). The judge
  `giudica_il_blocco`: threshold **`[?]` 10 s** on the longest freeze without new frames, with at least 30 s
  watched and the mouse moving in half of the seconds. The injected fault **without recompiling**:
  `--schermo-congelato` stops the tenant's compositor (SIGSTOP, found through its Wayland socket,
  not by name) for ~25 s and always releases it. Pure certifications: bench 14 **53 tests 0 troubles**,
  scenarios **45 OK**, core 91, eye 37.
  ✅ **AND ON THE HARDWARE IT HOLDS** — 23 Sep 2026, night, binary `e681a262`:

  | | healthy round (longest freeze) | with the compositor frozen 25 s |
  |---|---|---|
  | **gnome** | Firefox 20 min **0 s** · Chrome 20 min **0 s** | ⭐ RED, 24.4 s — fault SEEN |
  | **kde** | *(on the 23rd afternoon, cured: 0 s out of 340)* | ⭐ RED, 24.6 s — and in the `pesante` scenario 25.5 s |
  | **xfce** | Firefox 20 min **0 s** · Chrome 20 min **0 s** | ⭐ RED, 24.8 s — fault SEEN |

  ⇒ The **10 s** threshold becomes `[M]`: the healthy ones are at 0, the faults at 24-25, the real defect at 46-370.
  ⚠ Four defects **of the bench** found by running it, all cured: (1) gnome-shell and kwin
  have a file capability ⇒ their folder in `/proc` belongs to root, and even root **inside the
  box** cannot read their `fd` ⇒ the compositor was never found: now the user is read from
  `status`, and if the socket cannot be read it falls back **by name** to the three compositors the
  product knows, declaring it; (2) a round with the fault requested and **not** injected exited **0**
  from `_lancia.py`: now it is 3; (3) visible Firefox refused to start when another user is in the
  foreground, even inside the nested compositor: `REMOTIX_SCHERMO_ANNIDATO=1` declares it;
  (4) ⛔ **two benches launched together on the same tenant `c43u1`** stole the session from each other
  and gave two "freezes" of 51 and 58 s that **did not belong to the product** — redone alone: 0 s.
  It is the usual lesson about benches in parallel.

- ✅ **THE FRAMES LOST IN 4K WERE THE TABLET'S, NOT REMOTIX'S** — 24 Sep 2026, morning.
  On the tablet, night of the 23rd: Chrome **34 gaps** in 20 min on gnome and **88** on xfce; Firefox received
  everything but painted **93 %** of it. ⭐ From the server's logs: Chrome's gaps were made by the
  **rate regulator** (3 597 frames dropped out of ~26 000 because two were already waiting), with the
  witness scene at **~190 Mbit/s**, the network delay from **2 to 76-95 ms** (queue: saturated line) and
  the tablet on **5 GHz Wi-Fi with a -74 dBm signal** (540 Mbit/s nominal).
  ⭐⭐ THE CONTROL TEST `[M]`: same sessions, 4K, mouse moving, **browser on the server**
  (`REMOTIX_SUL_SERVER=1`, headless labwc at 3840x2160 — ⚠ and on the **same Intel that encodes**,
  the Radeon excluded on purpose: the test is stricter than the real case), 3 min per round:

  | | on the tablet | on the server |
  |---|---|---|
  | gnome · Chrome | 21 fr/s, 34 gaps in 20 min | **40 fr/s, 0 gaps** |
  | xfce · Chrome | 88 gaps in 20 min | **35 fr/s, 0 gaps** |
  | gnome · Firefox | painted 93 % | **painted 100 %** (3 981 out of 3 982) |

  ⇒ **The limit is the tablet** (weak Wi-Fi and 4K decoding), not the product. ⚠ One thing of the
  product remains to be kept for the stress test: on a line narrower than the stream the server
  **drops and then sends a whole keyframe**, which weighs more — it is today's choice (quality ramp-up
  and bandwidth cap off, I6), and a real user on a weak Wi-Fi would see it.

- ✅ **KDE RESTARTS AFTER A SERVER RESTART EVEN IF THE WINDOW HAS CHANGED SIZE** — 22 Sep 2026,
  binary `1c592928`. Found by the user: the Plasma session survives the server (I4), ⛔ but the table
  of the stages' canvases lives in the PROCESS and is reset by the restart ⇒ the fallback of §4.5 ("one grants what
  the stage **has**") had nothing to grant and passed on the client's size; KWin `--virtual`
  does not resize, §6.2 forbids sending a frame of a different size, and the screen stayed **black
  forever** while the log repeated "I ask it again" with a doubling wait.
  ⭐ Cure in `src/rcp.c` (`rcp_tela_dal_palco()`, branch 4): as long as **no frame has gone out** the
  server **adopts** the stage's size and announces it with a `TELA(ADATTATA)`; after the first frame
  it stays forbidden. `RCP.md` §7.1 thus closes the `⏳` of 15 August ("what does the server do when the stage
  changes size without any `ADATTA_TELA` having asked it").
  `[M]` REAL browsers on 8512, session born at 1548x862 and return from a window of another size:

  | browser | before (`f1807378`) | after (`1c592928`) |
  |---|---|---|
  | **Firefox 140** | ⛔ screen never lit, **0** frames in 60 s | ⭐ lit in **2.0 s**, **+3324** frames, 0 gaps |
  | **Chrome 153** | ⛔ screen never lit, **0** frames in 40 s | ⭐ lit, **+2273** frames, 0 gaps |

  ⚠ In all four rounds the adopted canvas is the stage's (1548x862), not the one requested by the
  window (1228x722 · 1240x692): it is the `TELA` that says so, and the frames start from there.
- ✅ **THE HEAVY VIDEO: CURED IN TWO BLOWS** — 22 Sep 2026, binary `f1807378` + page `e2b8c43`.
  (1) `a50b389` the **keyframe spiral** (RCP.md §5.2): the page no longer freezes — before, it stopped
  at 41 delivered out of 8810 streams. (2) `e2b8c43` **the delivery order**: the streams are read chained,
  in the order in which the server opens them. It was not Firefox: 173 gaps out of 173 were frames that arrived after
  their successor, with 0 abandons on the server side.
  `[M]` KDE, scene ~236 Mbit/s, 190 s, real and visible browsers: Firefox gaps **173 → 3**, out of order
  207 → 3, delivered/s 37.9 → 48.1, canvas **clean** (dispersion of the 8×8 blocks over the noise 37.8 → 23.3,
  Chrome 16.7); Chrome gaps 14 → 2. No dead line. The chain costs no delay: stroke
  capture→byte out 16.4–16.9 ms, as before.
  ⏳ **Open, and neither of the two is from today**: (a) Firefox receives 48/s and paints 37/s — 1858 frames
  vanish inside its decoder, without errors and without **anybody counting them** (a counter is needed,
  `decode()` against frames coming out) → ⭐ **(a) was reread on 23 Sep, and it is not what it
  seemed: see the item below**; (b) 3 gaps remain in 190 s: the chain respects the order in which
  the browser presents the streams, not the `numero` — they would close only with a reordering and a brief wait.
  ⚠ In KDE the tenants left by the net were removed by hand (`nictest` and `provanic` remain): C7 does not
  remove them, and in GNOME and XFCE they are still there.

- ✅ **FIREFOX'S FRAMES: CLOSED, AND FIREFOX IS CLEARED** — measured on 23 Sep 2026,
  afternoon, with a **real and visible** Firefox 140 on `rete11-kde`, 20 minutes, new counters read
  every second: `consegnati 25 880 = fuori 25 880 + dentro 1`. ⇒ Firefox's decoder does **not**
  swallow anything silently (`dentro` at most **5**, median 0), and it is not us holding them back
  (`bmp` at most **1**: `createImageBitmap` always resolves). ⛔ **The two predictions written
  beforehand were both refuted**; the third route holds, the one marked `⚠`: the residue of the 22nd
  was an artefact of that day's binaries, cured by `a50b389`/`e2b8c43`.
  ⭐ And over 110 intervals of 5 s, **zero** intervals that lose ≥16 %: the bursts are no longer there.
  ⇒ The count closes with no unknowns: 25 880 − 24 998 = 882 = `saltati_coda` + `tardive` + 1 in flight.

- ⏳ **The frames that "vanish" in Firefox are NOT queued: they are thrown away, and in BURSTS** —
  23 Sep 2026, the diaries of the 22nd reread (no new measurement: only arithmetic on logs already in hand),
  page `src/pagina.html`.

  ⛔ **The old subtraction was ambiguous, and had to be undone first of all.** Between `consegnati` ("I
  gave it to `decode()`") and `dipinti` ("it is on the glass") there are **four** passages and **one**
  was counted (`saltati_coda`). ⇒ `consegnati − dipinti` was not "lost by the decoder": it was a number without
  an owner. `[M]` The **majority** of cases already explain themselves today: of 477 diary lines with
  `consegnati − dipinti − salt − tard` between 0 and 2, the rest is only the frame **in flight** at the moment
  of reading (the two counters are read at different moments — the question was right). And the episode
  `dipinti 1097 video 3882→1097 salt 2785` closes **exactly**: 3882 − 1097 = 2785 = `salt`, zero
  unknowns. ⇒ The real gap is only what remains **after** removing `salt` and `tard`: I call it **residue**.

  ⭐⭐ **AND THE RESIDUE IS NOT A DELAY — the proof is `voff`, which was already on the same line.**
  `voff` = (client time at the glass) − (the server's `istante` of that frame): if the residue were
  a queue, `voff` should grow **with it**, by `residuo / ritmo`.

  | `[M]` 22 Sep, 190-200 s per round | final residue | growth of `voff` expected **if it were a queue** | growth of `voff` **measured** |
  |---|---|---|---|
  | Firefox 140, KDE (`n-ff-kde`) | **2007** | **+45 600 ms** | **+47 ms** |
  | Firefox 140, KDE (`h-ff-kde-base`) | **1757** | **+39 900 ms** | **+3 ms** |
  | Firefox 140, XFCE (`v-fi-xfce`) | **937** (flat for 60 s) | **+21 300 ms** | **+155 ms** |
  | Firefox 140, GNOME (`v-fi-gnome`) | **1** | +23 ms | +32 ms |
  | Chrome 153, KDE (`n-cr-kde`) | **0** out of 10 066 | 0 | +106 ms |

  ⇒ **A thousand frames of residue and zero milliseconds of delay.** The page always paints
  the **current** image: those frames are not waiting anywhere, **they no longer exist**.

  ⭐ **And the shape is a burst, not a rate.** `[M]` Of 39 intervals of 5 s of `n-ff-kde`, **17 lose
  exactly 0** and another 6 lose 1-2 frames (in flight); the **16** that remain lose from 16 %
  to **88 %**: `t18` = 261 in, **31 painted**. ⇒ The average
  "receives 48 / paints 37" **hides the defect instead of stating it**: what the user sees is not a lower
  rate, it is **freezes of 1-4 seconds** several times a minute, with the desktop then restarting
  from the right image. ⚠ It is the same defect that phase 9 called `F4-CODA-DEL-DECODIFICATORE`, and
  **the guard is blind**: `saltati_coda` fires on `dec.decodeQueueSize > 2`, and Firefox kept
  `decodeQueueSize` **below 3 with 1800 frames missing from the roll call**. A switch that never
  turns on is worse than one that is not there.

  ⭐ **THE COUNTER, written today** (`src/pagina.html`, `conti.usciti` + `conti.in_bmp`), on the diary
  line next to the others: `video C→D **fuori U dentro N coda_dec Q bmp B** salt … tard … err …`.
  `fuori` is recorded in the **first line of `dipingi()`**, which is the decoder's callback; `dentro` =
  `C − U`; `coda_dec` is what **it** declares; `bmp` are the `createImageBitmap` in flight. Cost: **three
  integer sums per frame**, no allocation, no clock. The count now **closes**:
  `consegnati = fuori + dentro` and `fuori = salt + dipinti + tard + bmp + bmp_falliti`. The same names
  come out of `REMOTIX.tratti()`. ⚠ Cured at the same point a line that **falsified stroke 8**:
  `t_dec` was emptied **entirely** beyond 240 entries — that is, precisely when the decoder does not deliver —
  and now it drops only the oldest.

  ⭐⭐ **THE PREDICTION, written BEFORE the measurement on the hardware** (integrated Intel UHD 730, not a powerful
  card), and with it declared what would refute me. The two hypotheses are separable because the counter
  separates them:
  - **I predict `dentro` ≈ residue and `bmp` ≈ 0-2**, with `coda_dec` ≤ 3 throughout the round. It would mean that
    Firefox's decoder **takes `decode()` and produces nothing**, silently: the defect is its own,
    our chain is clean, and the cure is to give up those frames **knowing it** (that is: `dentro`
    growing becomes a red verdict, not a silence).
  - ⛔ **WHAT REFUTES ME: `bmp` climbing to hundreds and staying up.** It would mean the opposite — that the
    decoder delivers and it is **we** who do not finish drawing, with the `createImageBitmap` that never
    resolve and hold the `VideoFrame`. In that case the defect is **ours**, it lies in
    `mostra()`, and it is the same family as "the leak that no log names".
  - ⚠ I am also refuted by `dentro ≈ 0` with `fuori ≈ dipinti` and the residue gone: it would mean that the
    residue of the 22nd was an artefact of that day's binaries, cured by `a50b389`/`e2b8c43`.

  ⇒ **The real measurement is done by the user when the net frees the field**: Firefox visible on KDE, ~190 s of
  moving scene, and `dentro` and `bmp` are read on the diary line. Until then this point
  stays ⏳.
- ✅ **Three "dead lines" in 13 minutes on KDE: THE ONE THAT WENT SILENT IS THE BROWSER, and it had already been CLOSED** —
  23 Sep 2026, from the logs of the 22nd (`registri-22set/kde-1045.log`, which goes from 10:27 to 10:45 **UTC** =
  12:27-12:45 local) put next to the **tablet's journal** (`journalctl`, local time). ⭐ The proof
  that closes the point is **systemd's scopes**: the browser process dies BEFORE the silence,
  not after.

  | | the client's last word (log, UTC) | the browser process exits (tablet's journal, local) | dead line |
  |---|---|---|---|
  | **12:30** Chrome 153 | 10:30:11.698 «il client si congeda, motivo=0x01 **la scheda è stata chiusa**» | `app-…Chrome-4339.scope` **12:30:11** (1.8 G peak) | 10:30:22.330 |
  | **12:41** Firefox 140 | 10:41:26.73 last packet · 10:41:27.834 last diary | `app-…firefox-esr-5792.scope` **12:41:28** (7min 9s CPU, 1.7 G) | 10:41:36.874 |
  | **12:42** Firefox 140 | 10:42:33.47 last packet | `app-…firefox-esr-6666.scope` **12:42:33** (830 M) | 10:42:44.297 |

  ⇒ In all three the client was talking up to **the instant the process exited**: no
  10 s freeze of the browser, no OOM, no kernel message, no WiFi event in the
  window. The three lines `causa=silenzio` all carry `offerti=0 usciti_byte=0 coda_video=0
  persi=0`: we were waiting for nothing of ours, **there was no longer anybody on the other side**. ⇒ (a) network,
  (c) tablet and (d) server are **excluded by measurement**; the continuous ping was not needed.

  ⭐ **And the real defect lay BEFORE, and it is the one the user then cured the same afternoon.**
  The page's diary (every 5 s, always punctual to the millisecond ⇒ the page's main thread
  was NOT blocked) holds the counters **still**, while the server keeps sending ~58 frames/s
  and 1.5 MB/s:
  - Firefox session of 12:39-12:41: `dipinti 1097 video 3882→1097 salt 2785` **identical for 50 s**
    (10:40:37.788 → 10:41:27.834). It stops exactly on the **heavy video**: frame 3882 is
    the last counted, and right after come 3886 of **131 238 bytes** and the KEYFRAME 3888 of **152 074
    bytes**, requested by the page at 10:40:34.583 (§5.2) because the `buchi` had just gone from 1 to 3.
  - Firefox session of 12:41-12:42: `dipinti 146 video 190→146` **still for 40 s**, and
    frame 190 weighs **144 305 bytes**, 193 is the KEYFRAME of **152 901 bytes** requested at 10:41:49.283.
  ⇒ It is **the keyframe spiral**, word for word as `a50b389` tells it («la pagina restava
  ferma sull'ultima immagine buona, con Firefox e con Chrome, **finché la linea moriva**»): cured on
  22 Sep at **17:08** (`a50b389`) and at **18:55** (`e2b8c43`), that is **4 and a half hours after** these
  three episodes. The "what remains" line had fallen behind. The post-cure `[M]` (190 s, real
  browsers, ~236 Mbit/s, "no dead line") is already above.
  ⛔ **Two corrections to the old line**: the 1097 out of 3882 were **Firefox 140**'s, not Chrome's —
  Chrome, in the same half hour, painted `817 video 817→817 salt 0 buchi 0`; and the dead line is not
  a symptom of the freeze, it is the **tail** of the browser the user was closing because the screen was still.

- ✅ **A ⛔ dead line is no longer written on a client that has just said goodbye to us** — 23 Sep 2026,
  binary `5f0be589`, and it was our last residue of the three episodes.
  Episode of 12:30: 10:30:11.698 the page takes its leave (`motivo=0x01`, tab closed) → 10:30:11.798
  **we ourselves** write «PING del trasporto spenti: la sessione è finita, **non c'è più niente da
  tenere vivo**» → 10:30:12.199 we send the closing capsule → and then we keep the QUIC
  connection open, sending 2 packets every second or two to a browser that is no longer there, until at 10:30:22.330
  a ⛔ **LINEA MORTA** comes out that reads like a product fault.
  ⚠ When instead it is the client that sends the `CONNECTION_CLOSE` the connection goes away in **9 ms**
  (10:39:11.675 farewell → 10:39:11.684 «connessione chiusa»): the behaviour depends on the client, and
  Chrome exiting does not say goodbye at the QUIC level.
  ⇒ The guardian is `linea_morta_giudica()` (`src/webtransport.c`): it stopped on `!w->rcp ||
  w->chiusura >= 0`, **but did not look at the `"finita"` state** — the same state on which
  `regola_tienila_viva()` (`src/webtransport.c`) turns off the PINGs. ⛔ `w->rcp` is not reset at
  farewell: only `wt_stream_chiuso()` resets it, that is the CLIENT closing the stream — and a browser
  that exits never closes it. ⇒ **Cure: one line, `if (rcp_e_finita(w->rcp)) return;`**.

  ⭐ **Of the two possible routes the first was chosen, and the second was refused with the
  reasons in the clear.** Closing the QUIC connection when the last session goes away would have seemed
  more honest, but "session finished, connection still alive" is a state **foreseen twice in
  this same file**, and both times the choice was to free the SEAT and leave the transport
  standing: `fin_dal_client()` («la pagina che chiude la parte scrivente del canale e tiene viva la
  connessione») and `chiusa_dal_client()` («il posto si lascia adesso … aspettare lo smontaggio del
  trasporto vuol dire tenerlo occupato addosso a chi si ricollega subito»). And `wt_stream_chiuso()`
  puts `w->sessione` back to `-1` on purpose so that a new session can open on top of it. ⇒ The
  second route would undo a decision taken twice; the first is not a sticking plaster, it is **the
  comment that was already there coming true**. And there is no waste: the PINGs are already off, and the
  transport goes away by itself with the `max_idle_timeout` of 30 s (`src/trasporto.c`).

  `[M]` **23 Sep 2026, `gnome` box (8511), binary `5f0be589`, REAL headless Chrome 153** — two
  identical rounds with **a single difference**: whether the client says goodbye before disappearing.
  ⭐ `5f0be589` is the binary running at this moment on **all three** boxes (`md5sum
  /proc/<pid>/exe` on gnome, kde and xfce), and it contains **all three** of this morning's cures: `7e0c0e2`
  (the frame already encoded pays for the keyframe), `f5527c2` (the keyframe is requested when the
  debt is born) and this one. The gnome box's server was born at 05:06:34 UTC, that is **before** the two
  rounds below, and in its whole log there is **exactly one** `linea-morta` line: the one of
  round B.

  | round | what the client does | dead line | how the connection ends |
  |---|---|---|---|
  | **A** | `about:blank` (⇒ farewell `0x01` «la scheda è stata chiusa») and **300 ms later `SIGKILL`** — no `CONNECTION_CLOSE`, like Chrome on 22 Sep | ⭐ **NONE**, in 30 s of silence | 05:08:12.276 «**trenta secondi di silenzio, staccato (§2.2)**» — a REAL reason in place of a false alarm |
  | **B** | **`SIGKILL` and nothing else**, with the session ACTIVE | ⛔ **FIRES**, `causa=silenzio silenzio_ms=10017 prove=13` | 05:08:42.064, the connection closes as it should |

  ⇒ The cure removes **only** the false positive: whoever dies does not say goodbye, and the guardian still catches it.
  In A the log goes through the whole sequence of 22 September — farewell 05:07:41.775, PINGs off
  05:07:41.875, capsule 05:07:42.276, `ricevuti` stuck at 40 for 30 s — and **writes no ⛔**.
  ⚠⚠ **AND THE PRICE OF THE CURE, DECLARED instead of discovered later.** The dead line, while wrong,
  also did something useful: by closing the connection at +10 s it stopped **the stage**. The log
  says so in both cases — 22 Sep, farewell 10:30:11.698 → «il palco smette di catturare»
  10:30:22.330 (**+10.6 s**); 23 Sep with the cured binary, farewell 05:07:41.775 → «il palco smette di
  catturare» 05:08:12.276 (**+30.5 s**, that is at the `max_idle_timeout`). ⇒ The window in which **one
  captures and encodes for nobody** goes from ~10 s to ~30 s.
  ⭐ On the still desktop of the test it costs nothing (11 frames in all), but on a live scene at 58
  frames/s it is **twenty more seconds of encoding for every client that leaves**, on a
  machine that has other tenants. The measurement under load is in the long session.

- ✅ **THE STAGE STOPS CAPTURING AT FAREWELL — CURED AND MEASURED** — 23 Sep 2026, `103280f`,
  binary `cd8a3aec`. The cure hooks onto the session's **state** (`"finita"`), not onto the three
  doors through which one gets there — the routes are **seven** and three alone left four uncovered.
  ⛔ And it also cured a worse case found while writing: the client that closed the CONNECT stream
  **properly** never stopped the stage, **ever**, not even at the death of the connection.
  `[M]` All five predictions written beforehand hold: **zero** `⛔ NIENTE VIDEO` lines, the
  stage stops **+100 ms** after the farewell (before: +30 s), children 2→2→2 and RSS still (I4 holds),
  on return `canale video ACCESO` and 404 frames right after, zero on/off pairs.
  ⚠ P5 (the audio) holds by half: the switch-off is exact, but in that session nothing was
  playing, so "audio muted on return" was neither confirmed nor refuted.

- ⏳ **The stage stops capturing when the TRANSPORT dies, not when the client TAKES ITS LEAVE** —
  23 Sep 2026, found while curing the dead line. At farewell we free the seat (`posto LASCIATO …
  occupati adesso: 0`) but we do **not** turn off the capture: it stops only when the QUIC
  connection goes away. In between every frame is captured, encoded, offered, **refused** by
  `rcp_video_apri()` (`src/rcp.c`, `RCP_VIDEO_PRIMA_DI_SESSIONE`) and put on record as
  `⛔ NIENTE VIDEO: «SESSIONE» non è stata spedita (stato finita)`.
  ⇒ It is work done for nobody **and** a ⛔ line that looks like a fault. 🔸 The sensible cure is
  to turn off the frame loop on the same event that frees the seat — ⚠ but it must be checked against
  I4 ("the stage stays standing"), which is another thing: stopping the *capture* is not dismantling the stage.

- ✅ **THE NET AFTER THE CURE OF THE GHOSTS HAS RUN** — 22 Sep 2026, `--famiglia tutto --scatola "gnome kde
  xfce"`, binary `defc5ad5`: **no red**, 13 506 s, C14 included (alone and together, same fingerprint).
  ⚠ The net uses the Python client, not a browser: it does NOT see the video freeze in **Firefox**
  below. ✅ And `13-w4` **has become a fixed mesh of the net** — 23 Sep 2026, see `C20` below.
- ✅ **THE NET DIRTIES THE BOXES: now it is a VERDICT** — closed on 23 Sep 2026. The clear-out was
  already done (22 Sep, `08172a6`, `d0406fd`): the **hook** clears out after every mesh, on the net's
  namespace (users, homes, failed `user@` units, orphans in `/tmp`); the scene is launched with
  `setsid`; C3 stops only the product's process and no longer the browser.
  ⭐ The verdict was missing, and it is **C19** (`banchi/11-scatole/11-c19-la-scatola-resta-pulita.py`,
  `la_scatola_resta_pulita` in the hook, **last mesh of every box** in `tutto` and in
  `desktop-nuovo`): *«a fine giro non sopravvive nessun inquilino della rete»*. Before, the dirt was
  an `inf` line noted `riuscita=true`, that is ⛔ the net could leave twenty tenants inside a
  box and call itself green all the same.
  ⭐⭐ **The `nictest` pitfall is solved by counting by NAME, not by uid.** `bilancio` counts
  `uid>=1000` excluding only `provanic` ⇒ for it `nictest` is a tenant; C19 counts on the **net's
  namespace** (`^c[0-9]+b?u[0-9]+$`, the same as `sgombera_inquilini`) ⇒ `nictest`,
  `provanic` and the system users do not fall into it **by shape**, not by a list of
  exceptions. The two stay different on purpose: `bilancio` is a measurement for whoever diagnoses, C19 is the
  verdict.
  ⚠ It judges **U** (users), **C** (homes left, that is `userdel` without `-r`) and **P** (processes);
  failed orphan `user@` units and orphans in `/tmp` stay a **finding**, not a verdict — they are the
  tenants' rubbish, not the tenants, and a perpetual red for a file in `/tmp` would be a
  switch that somebody turns off (§1.49). Whoever wants to measure them asks for it: `--anche-lo-sporco`.
  `[M]` 23 Sep 2026, binary `9b5df38b`, boxes **kde** and **xfce**: healthy round **GREEN** on both
  (0 tenants, 0 homes, 0 processes; finding kde 8 failed units · 0 orphans, xfce 10 · 49), and the **two**
  injected faults **SEEN** on both — `--lascia-un-inquilino` (U·C·P red) and
  `--lascia-una-casa` (only C red: ⭐ the residue that no `pgrep` and no `getent` would see).
  ⚠ And a finding the mesh prints and nobody looked at: in kde there was `occhio2`, in xfce `corrx1` and
  `corrx2` — tenants of other benches **outside** the namespace, hence neither cleared out by the hook
  nor counted by C19. 🔸 New benches should give their tenants a `c<n>u<n>` name, as C20 does.
- ✅ **`13-w4` HAS BECOME C20, A FIXED MESH OF THE NET** — 23 Sep 2026.
  `banchi/11-scatole/11-c20-la-rinascita-non-porta-fantasmi.py`, inside `le_cinque_nuove` (that is in
  `tutto` and in `desktop-nuovo`), with the capability gate: it wants the **image**.
  It watches the defect the user found on 22 Sep on KDE with Chrome — after "Log Out" and a new
  login the screen alternated desktop, logout screen and black — and that `src/codificatore.c`
  describes as *«un'immagine VECCHIA, senza nessun errore»*: ⛔ precisely because there is no error, only
  whoever **looks** notices it.
  ⭐ On entering the net it took three things that as a one-evening bench it did not have:
  (1) **the injected fault** `--scena-che-lampeggia` (without it, the day the judge stopped
  looking it would say green forever); (2) **it no longer knows what Plasma is** — birth and end of the
  session it reads from the product's log (`formato negoziato`, `la sessione grafica … E' FINITA`)
  and the "Log Out" gesture it looks for with the same question as `src/sessione.c` (`org.kde.Shutdown` ·
  `org.gnome.SessionManager` · `xfce4-session-logout`); (3) the tenant is called **`c20u<n>`**,
  inside the net's namespace, so the hook clears it out and C19 sees it.
  ⛔⛔ **And it had to put a scene there itself, like C3** — it is the measurement that rewrote the mesh. With the
  desktop still, at the second login: **kde 1 800 frames in 45 s** (KWin always delivers),
  **xfce 7 in 60 s** (labwc, like every wlroots, delivers only on damage) ⇒ on xfce and lxqt the mesh
  would have been **3 forever**. The cure is `banchi/11-scatole/11-c20-scena.html`: a dark band that
  scrolls on a light background, **two** bands 100 points apart so that in view there is always
  exactly 20 % dark ⇒ ⭐ every frame is different (there is damage, hence delivery) **and the
  mean luminance does not move**. `[M]` measured: **156**, and a **single distinct value** over 2 166
  frames.
  `[M]` 23 Sep 2026, binary `9b5df38b`, with the declared scene:

  | | healthy round | injected fault (`--scena-che-lampeggia`) |
  |---|---|---|
  | **kde** | ⭐ GREEN (outcome 0) — 4 332 frames, tail 2 166, **0 skips**, luminance **156**, 1 distinct value; cache: 4 surfaces thrown away | ⭐ SEEN (outcome 0) — **762 skips** over a tail of 2 167, 26 distinct values (14…234) |
  | **xfce** | ⭐ GREEN (outcome 0) — 4 454 frames, tail 2 227, **0 skips**, luminance **156**, 1 distinct value; cache: 5 surfaces | ⭐ SEEN (outcome 0) — **766 skips** over a tail of 2 229, 25 distinct values |

  ⚠ Two pitfalls found while certifying, and both were the BENCH's:
  (a) the browser did not paint because `/tmp/mozilla` belonged to another tenant — it is the cure of the
  provisioning that C3 has paid for since 27 August, and now C20 calls it (⛔ no copy is made of it);
  (b) the "the screen is black" check was **before** the one on flashing ⇒ C3's scene, which
  is dark (median 17), made it output **3** instead of red. ⭐ A screen that alternates is never
  ambiguous, however dark: it is the **still** black that cannot be told from a frozen image.
- 🔸 **The net does not look at real browsers under load — HALF CLOSED** — 23 Sep 2026. ⭐ Now
  the tool is there: `banchi/14-stress/stress_occhio.py`, the judge that **looks at the image** instead
  of counting frames, hooked to four scenarios (`ac59daf`, `99a4a74`). `[M]` With the injected fault
  the counters are PERFECT (320 delivered, 320 painted, 0 gaps) and the eye gives **RED**
  on all four, where with the eye off they gave **GREEN** — that is what the suite saw on the
  night between the 22nd and the 23rd while the user was looking at a mosaic.
  ⏳ Still open: the suite has never run in full (the user's decision on 23 Sep: the stress
  test is designed by him, after LXQt), and the **net** keeps using the Python client.
  ⛔⛔ And on 23 Sep it was discovered how much it matters: the most serious defect of the day (58 % of the screen
  still) was invisible because **no bench moved the mouse**. See the heartbeat item.
- ⏳ **The net does not look at real browsers under load** — 22 Sep 2026, and that is why the keyframe
  spiral got through: the net uses the Python client, and `12-client-veri.py` tests real Firefox and Chrome
  for **8 s with the desktop still**. 🔸 A round with a full-screen video for minutes is needed, with the page's
  counters (`video consegnati→dipinti`, `buchi`) as the verdict.
- ⏳ **Chrome Android** on XFCE: the validation is the user's.
- ✅ **The `video`/`render` groups on ALL desktops** — closed on 22 Sep 2026, and the cure was not needed:
  the code that enrols (`src/figlio.c`, `iscrivi_ai_gruppi_della_scheda`) is in the **parent**, runs as
  root after PAM and **before the `fork`** ⇒ it does not even know which compositor will be born, and holds on every
  desktop. It was **measured** only on kde, not done only for kde.
  `[M]` 22 Sep 2026, tenants created WITHOUT groups, **real** browsers and a real window: gnome Firefox 140
  **PASS** · Chrome 153 **PASS**; xfce Firefox **PASS** · Chrome **PASS**. In all four the
  log says «PRIMA CONNESSIONE … ce lo METTO io» and then «è nei gruppi della scheda … può vedere in
  hardware», `id -nG` goes from "only itself" to "video render", and the first frame arrives in
  0.6–1.6 s. (kde was already `[M]` on 20 Sep, `DECISIONI.md` §7.21.)
  ⭐ **And now the net looks at it**: mesh **C18** "the card's groups are put by the product",
  the only one that does NOT call `garantisci_i_gruppi` — all the others put them in by themselves and thus
  **hid** that piece of the product. Injected fault `--senza-usermod` (`usermod` is hidden
  for the duration of the round, and always put back): `[M]` GREEN and fault SEEN on gnome and xfce.
- ⏳ ⛔ **BEFORE LXQt, the user's tests by hand** — asked on 21 Sep 2026: in the three boxes
  gnome, kde and xfce there are Firefox, a terminal and a file manager (already in the layers), and
  the tenant **`nictest`** (password `nictest`, in the `sudo` group), a new last layer of the three
  recipes. ⭐ `[M]` 21 Sep 2026, evening: images rebuilt, `nictest` in `sudo video render` in the three
  boxes, `sudo` answers, and Firefox gets in as `nictest` on **8511 · 8512 · 8513**: PASS on all
  three. ⏳ The user's tests remain.
- ✅ **"Switch User"** — ⭐ DECIDED by the user on 21 Sep 2026, evening: it goes **on all desktops**,
  only "Log Out" stays. `[M]` binary `eb327ffd`: XFCE `-switch-user` in the panel and
  `ShowSwitchUser=false`; GNOME `disable-user-switching=true` with `always-show-log-out=true`; KDE
  already since phase 12. ⭐ `[M]` net **gnome+xfce** (reduced by the user's decision: KDE does not go through the touched code), trigger `fase13-cambia-utente`, 9 275 s: **GNOME 27/27 · XFCE 27/27 · faults 26/26 seen**, C10 C12 C15 C16 green on the laptop.
- `[?]` **The product's session is `closing` from birth**, on every desktop («logged out.
  Waiting for processes to exit» in the journal right after «New session»). It does not belong to this phase nor
  is it a regression (GNOME is the same), but with `KillUserProcesses=yes` logind could treat it as a
  finished session. ⇒ To be looked at in a phase of its own.
- `[?]` Choices 2, 3, 4, 6, 7 of the table above were **dealt with in the code** by the
  increments (resizing on, user bus, liveness from the facts of `/proc` and of the bus) and
  must be reread with the user, not taken as decided.

## The user's verdict

- ⛔⛔ **THE HEARTBEAT COULD BE POSTPONED FOREVER — the most serious defect of the project, and it had been there
  forever** — found and cured on 23 Sep 2026 (`2be9527`, `2737d56`), binary `3fa352a2`.
  `batti_fra()` moved the heartbeat's deadline **forward** at every call, and `regola_battito()`
  runs at the end of `rcp_passa_input()`, that is **at every input message from the client**. A real browser
  following the mouse sends ~40 per second ⇒ the heartbeat **never matured**. And with the heartbeat stopped
  `video_regola()` does not run, the only place from which the KEYFRAME is asked of the stage — nor `rcp_tempo()`,
  that is the silence clock (§5.3) and the caps of §4.6: ⛔ **for six minutes no protection
  could fire**.
  `[M]` Real and visible Firefox, `rete11-kde`, 20 minutes, moving scene: **698 s out of 1199 (58 %)**
  without a single new frame, seven freezes (74 · 56 · 62 · 25 · **370** · 53 · 56 s), 45 278
  frames encoded and thrown away (~13 GB for nobody on a UHD 730). ⭐ And **the image never
  breaks** (1146 photos, 0 broken cells): it was not corruption, it was a **freeze**. The freeze ended
  when one stopped moving the mouse for a second — it is in the log.
  ⭐ A two-belt cure: `batti_fra()` sets a **cap** and not an appointment (a nearer deadline
  stays where it is); and if the debt of §5.2 has been on for over 1000 ms the keyframe is requested again from the
  refusal of the frame, by a route that does not go through the heartbeat.
  `[M]` After: **0 seconds still out of 340**, longest freeze **0 s**, heartbeats from 22 in 3 min to 508 in
  8 min, longest `da_ms` from **46 192 ms** to **1 102 ms**, keyframe requests 0.76/s (not 6-7/s:
  that would be the spiral of `07-b65`).
  ⛔⛔ **WHY IT WAS INVISIBLE, and it is the lesson worth more than the cure**: the net uses the Python
  client, which sends no input, and the benches with real browsers opened the page and **watched**. All
  our clients were *polite*. ⇒ The whole net had passed **green** on that same binary
  a few hours earlier. The bench that found it does one thing only: it moves the mouse
  (`banchi/14-stress/14-il-cliente-che-non-sta-fermo.py`).
  ⚠ And a defect that needs **two** conditions together (dense input **and** debt on) cannot be
  ruled out by any green: the control round on the broken binary, without the second one, froze
  nothing.
  🔸 Still to do: bring the mouse movement **into the scenarios that already exist**, tune the
  threshold on the longest freeze (between 46 s with the defect and 1.1 s cured there is a factor of forty, so it
  is not delicate), and only at the end the injected fault. ⛔ As long as the first two are missing, putting it in the net
  would mean adding a guard that cannot turn red.
