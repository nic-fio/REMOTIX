# Phase 14 — LXQt

*Opened on **24 Sep 2026**. Closed on —*

⚠ Numbering: `PIANO.md` put LXQt in phase 13 («XFCE e LXQt») and called 14 «Il registro».
The user, opening it, called it **phase 14**: the user's name holds, and the log moves down by one.

## What it must produce

The fourth desktop: the user opens the browser and sees their **LXQt** desktop, as today GNOME, Plasma
and XFCE.

⛔ **The phase's rule, from the user, 24 Sep 2026**: *«aggiungere LXQt a REMOTIX mantenendo
intatte tutte le capacità già certificate di GNOME, KDE e XFCE»*. ⇒ **The protected baseline is
three.** We work with the gates of phase 13 (CP0 baseline · CP1 definition · CP2 observation ·
CP3 minimal change · CP4 LXQt test · real clients · full net · checkpoint), and with two new
accents: **parallel development with many agents, integration and certification in a single hand**; and every
activity ends in **PASS / FAIL / BLOCKED** (with cause, evidence, dependency, condition).

---

## ⭐ The difference that changes the shape of the phase

LXQt, like XFCE, **has no compositor of its own**: on Wayland it relies on **labwc** (wlroots).
⇒ Capture (screencopy), input (virtual-keyboard/pointer), clipboard (data-control) and output
size are **already written** for XFCE and do not look at the desktop `[R]`. What changes is the
**session**: `lxqt-session` in place of `xfce4-session`, and a different handler for bus, logout,
inactivity and settings.

`[R]` Two things phase 13 did not have:
- **in trixie no package starts LXQt on Wayland** (no `lxqt-wayland-session`, no
  `startlxqtwayland`): the startup line is written by the product, `labwc -C <cartella nostra> -S
  lxqt-session`, imitating the upstream script 0.1.1 but without its `autostart` (which turns on
  `swayidle … wlopm --off` at 5 minutes) and without its wizard;
- **the `rete11-lxqt` box did not contain the desktop**: only `labwc lxqt-session xwayland`. No
  panel, desktop, `qt6-wayland`. ⇒ Before any test, the recipe.

---

## The increments

### Increment 1 — LXQt is recognised, is born and is seen

| | |
|---|---|
| **goal** | on a machine with `lxqt-session` + `labwc` the product recognises LXQt, makes headless labwc be born with `lxqt-session`, captures, carries mouse and keyboard, knows how to close |
| **invariant** | GNOME, KDE, XFCE **identical**: the enum `SESSIONE_DESKTOP_LXQT = 4` goes at the end; every existing branch stays with the same effect |
| **modules** | `src/sessione.{c,h}` (recognition, environment, start, alive/state, logout, settings), `src/figlio.c` (5 points `== XFCE` → `sessione_su_wlroots()`); the recipe `Contenitore.lxqt`; C20's «Esci» gesture |
| **LXQt test** | C1(lxqt) green; the bare desktop photographed and passed to the judges **before** opening the `immagine` capability; the probe of the processes and of the environment |
| **client test** | real Firefox and Chrome on 8514 |
| **regressions to watch** | C1, C7 and everything certified on gnome/kde/xfce |
| **criterion** | whole net: no new red on gnome/kde/xfce, C1(lxqt) green, faults still caught |

**CP3 — the change** (`1f99d60` product; `cd7a088` `61bdc5a` `58262da` `2330e79` benches):
- `riconosci_desktop`: marker `lxqt-session`, branch after XFCE; with both, XFCE and
  «AMBIGUO» declared;
- environment: `XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots` (the upstream script's form when the
  compositor is configured), `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share`, `QT_QPA_PLATFORM=wayland`,
  `QT_QPA_PLATFORMTHEME=lxqt`, `XDG_MENU_PREFIX=lxqt-`, plus XFCE's labwc variables;
- **our own** `rc.xml` and `autostart` in `$XDG_RUNTIME_DIR/remotix/labwc-lxqt/`;
- alive/state: the name `org.lxqt.session` on the bus; «Esci»: `logout()` without an answer, then SIGTERM
  to labwc;
- inactivity: `enableIdlenessWatcher=false` **and** `runCheckLevel=1` (below 1 the daemon sets it back to
  true), reread; no lock command (`/bin/false` would open a modal);
- the box: `lxqt-core qt6-wayland lxqt-menu-data lxqt-powermanagement nano`, `nictest`,
  `wlr-randr`; **excluded** `lxqt-branding-debian` (lxqt-leave in the panel), `qlipper` (dirties the
  clipboard), `swayidle swaylock wlopm kanshi`.

**Adversarial review** (agent sent to refute): GNOME/KDE/XFCE identical — **not refuted**.
On the LXQt branch:
- inherited from XFCE, not new: the guard and the closing force look at **every** `labwc`
  of the user, and the user bus is one per uid ⇒ the same user with a local session open
  confuses the product. `[?]` to be decided separately: it is not LXQt's;
- ⚠ **to be measured**: the name on the bus is born before the modules ⇒ an `lxqt-session` that dies
  at startup would be read as «the user has logged out» (farewell 0x10);
- minor: `g_key_file_save_to_file` replaces a symbolic link with a real file.

Binary **`404f9907`** (md5), built from the integrated tree `ae6c3ba`.

**CP4 — the LXQt test**, 24 Sep 2026, on a **fifth development box** `rete14-lxqt` (port
8524, image `lxqt:p1`, folder `/media/REMOTIX/rete14-lxqt`), decided by the user so as not to
wait for the baseline: *«parti subito con la quinta scatola. Ogni DE deve avere la sua scatola
dedicata»*. The four boxes of the net stay intact.
- `[M]` the product says «il desktop di questa macchina: LXQt (c'e' lxqt-session, e labwc per farlo
  girare)»; **C1(lxqt)×3 GREEN**, monitor `HEADLESS-1` 1920x1080;
- `[M]` the snapshot of the bare desktop: **drawn** (4181 colours), LXQt background and panel; **none** of the
  scenes' colours above 0.0 % ⇒ C2/C3/C8b cannot be fooled by the background;
- `[M]` the probe: labwc → lxqt-session → panel, desktop, powermanagement, notifications, policykit,
  runner; **Qt on wayland**, no Xwayland, no wizard nor `lxqt-leave` open, no
  swayidle/qlipper/locker; `enableIdlenessWatcher=false` and `runCheckLevel=1` **win** from the user's
  file; labwc offers layer-shell, foreign-toplevel, screencopy, virtual input, data-control;
- `[M]` **the round of all the box meshes on LXQt**, with the capabilities opened **only in the development
  copy**: passo0, C7 (+ detach), C5, C8, C9, C18, C2, C3 (+ still scene), C4, C6, C8b, C17,
  C20, C19 **all green**, and **16 grafted faults out of 16 SEEN**. C20: the gesture is the `logout()` of
  `org.lxqt.session`, «il figlio è sopravvissuto e se n'è accorto», clean re-entry.
  ⚠ A first red C19 was **class C, of my round**: it did not clear out the tenants between the meshes as
  the hook does; cleared out, C19 green and its two faults seen.

**The defect found by looking**: the panel **without icons** and without the menu button ⇒ increment 2.

### Increment 2 — the icons, and no dangerous entries

| | |
|---|---|
| **goal** | the LXQt panel has icons and menu; the menu does not offer lock, suspend, hibernate, reboot, shutdown; «Esci» stays |
| **invariant** | GNOME/KDE/XFCE identical: only `impostazioni_lxqt()` and a new layer **at the end** of the recipe |
| **cause** `[R]` | `icon_theme=breeze` in `/usr/share/lxqt/lxqt.conf`, but the theme is brought by `lxqt-system-theme` only as *Recommends*; the menu button wants `qt6-svg-plugins`. ⚠ It is the **box**: a machine with normal `apt` gets them |
| **change** | R5 `kf6-breeze-icon-theme qt6-svg-plugins` (`afc0cb0`); six `.desktop` `Hidden=true` for the user, **reread** (`a1f771e`, DECISIONI §4.7) |
| **measure** `[M]` | the snapshot shows menu, notifications, volume, «show desktop»; log «⭐ LXQt: 6/6 voci nascoste, RILETTE; resta "Esci"» |

⚠ Declared leftovers, like XFCE's «Log Out» window: the «Leave» button inside the menu is
fixed in fancymenu's code and opens `lxqt-leave`, where shutdown/reboot/suspend are **greyed out**
(polkit/logind) and «Lock screen» is **clickable but inert** (no lock command). «n/a» on the left
is the desktop switcher, which on wlroots has no engine: harmless.

**Real clients** — binary **`1a10a66e`** (tree `a1f771e`), labwc without a screen on the server:
**Firefox 140 PASS · Chrome 154 PASS** (`12-client-veri`: page, admission, first frame,
continuity 63–66 frames in 8 s, keyboard and mouse to the server, 0 JS and network errors, re-entry).
⛔ **And the snapshot of the canvas shows a defect the counters do not see**: with the browser's
canvas (1400x914) the panel goes right at the bottom, but **pcmanfm-qt's background stays at the birth
size** and the rest is black. With the Python client (1920x1080) it filled everything. Under diagnosis.

---

### Increment 3 — the background is born at the client's size

`[M]` The cause, with the Python client and without browser: **a race at birth**. labwc is born with
the output at 1280x720 and the product resizes it ~200 ms later; pcmanfm-qt starts ~160 ms after labwc.
`[R]` pcmanfm-qt 2.1.0 computes the background from `screen->size()` and recomputes it only on `resizeEvent`: if
Qt updates the screen after the window, the background stays 1280x720 forever.
**Cure** (`e4ecfbb`, LXQt branch only): labwc's primary client becomes `sh -c` that gives the output the
client's size with `wlr-randr` **before** `exec lxqt-session` (`;` and not `&&`: if it fails,
the earlier late request remains). `wlr-randr` goes from diagnostic tool to dependency of the
product on LXQt. `[M]` 1400x914: **before 1 defect out of 20, after 0 out of 20**; and 0 out of 5 at 1920x1080, 0 out of
5 at 3840x2160.

### Firefox's cure (the user's decision: «curarlo subito»)

`ec9c561`: the **width** of the requested canvas is truncated to a multiple of 16 (the height stays even),
for all browsers, without branches. `[M]` Firefox: strip of 8 and 12 px → **0**, margin of the last
icon equal to Chrome (7 px); Chrome unchanged. The price: black bands of at most 7-8 px on the sides.

### CP0 — the baseline, closed

`[M]` 24 Sep 2026, 07:36 → 12:00, binary `e681a262` (the one from before the phase), `--famiglia tutto`
on the four boxes: **a single red, `C1(lxqt)×10`**, the expected one (the old binary does not
recognise LXQt); **117 grafted faults seen out of 117**; C14 holds; C10 C12 C15 C16 «il terreno non
regge» from the server, as always. ⇒ no unexpected difference compared with the checkpoint of the night of the 24th.

### Real clients with the final binary **`c0e8f010`** and page **`d77177f1`**

`[M]` on the development box, **Firefox 140 and Chrome 154 PASS** at window 1400x914 (canvas
1392x828) **and in 4K** (canvas 3840x2014): a–g all green. Firefox's 4K snapshot: full background, 0 %
black, the last column is background (1,81,129) and not the strip.

### ✅ THE WHOLE NET ON THE FOUR BOXES — no red

`[M]` 24 Sep 2026, 12:00 → 17:18, binary **`c0e8f010`** and page **`d77177f1`** in all four,
`rete11-lxqt` **redone** from the new recipe, `--famiglia tutto`: **«nessun rosso»**.
**34 greens on gnome, 34 on kde, 34 on xfce, 34 on lxqt** — LXQt does exactly the same meshes
as the other three; **no grafted fault escaped**; C14 (the four together) holds; C10 C12 C15
C16 «il terreno non regge» from the server, as always. ⇒ GNOME, KDE and XFCE **have lost nothing**,
neither because of LXQt nor because of Firefox's cure that touches everyone.

### ✅ The real browsers on the four official boxes

`[M]` 24 Sep 2026, evening, binary `c0e8f010`, page `d77177f1`, labwc without a screen on the server,
window 1400x914 (canvas 1392x828):

| | `12-client-veri` Firefox 140 | `12-client-veri` Chrome 154 | `12-c20-veri` Firefox | `12-c20-veri` Chrome |
|---|---|---|---|---|
| **gnome** | PASS | PASS | GREEN | GREEN |
| **kde** | PASS | PASS | GREEN | GREEN |
| **xfce** | PASS | PASS | GREEN | GREEN |
| **lxqt** | PASS | PASS | GREEN | GREEN |

⚠ On gnome the first round gave **BLOCKED** at entry *e* (input): without `--registro-cmd` the bench
looks for the input id in the frames, and Mutter with the «muovi» scene sends only 7-8 of them in 8 s ⇒ **class C**,
of the bench. Redone with `--registro-cmd`: **PASS** on both, 7-8 input lines in the log.
Android: it stays with the user, with the user's phone (the emulator does not start Chrome, 19 Sep).

### ✅ Sessions with the real browsers on LXQt (at most 10 minutes — the user, 24 Sep) and the guard

`[M]` `14-il-cliente-che-non-sta-fermo --desktop lxqt`, mouse moving in 100 % of the seconds:
**Firefox 10 min: longest stall 0 s, 0 holes · Chrome 10 min: longest stall 0 s, 0 holes.**
Heartbeat guard with the fault `--schermo-congelato` (SIGSTOP to labwc found by socket): **outcome 1,
«lo schermo si è fermato per 23,9 s mentre il mouse si muoveva» — the fault was SEEN.**

## ⭐ CHECKPOINT — 24 Sep 2026, evening

| | |
|---|---|
| **binary** | `c0e8f010` (md5), tree `a8bedb6` + benches; page `d77177f1` |
| **LXQt** | recognised, born, seen, input, clipboard, «Esci», background at the client's size, icons, dangerous entries hidden; **34/34** in the net, capabilities `immagine input appunti` opened |
| **GNOME · KDE · XFCE** | **34/34 each**, unchanged |
| **client** | Firefox 140 and Chrome 154 PASS and C20 GREEN on the four; LXQt sessions 10 min green; Android: to the user |
| **net** | «nessun rosso», no fault escaped, C14 holds; heartbeat guard sees the fault on LXQt |
| **outside LXQt, cured** | Firefox's green strip (all desktops), the user's decision |

## ⭐ THE EVENING OF 24 SEPTEMBER — the user's hand test, and the six defects the user found

The user tested by hand (tablet, Firefox and Chrome) and found what the net did not see.
All cured, measured with the real browsers, and each with a new mesh watching over it:

| # | defect `[M]` | desktop | cure | test |
|---|---|---|---|---|
| 1 | the «Lock screen» icon still active (lxqt-leave window from fancymenu's fixed button; clicked it stayed HUNG) | LXQt | panel with the classic menu (`mainmenu`), `lock_command_wayland=true` computed like liblxqt (`efb1840`, `83ea7b4`) | snapshot, measures c94u* |
| 2 | windows cannot be resized from the border: the zone is OUTSIDE the border and the double arrow did not come from REMOTIX | all | the **real pointer shape** on all four (the user's decision): coded theme + dictionary (`src/forma.c`), KDE from the metadata (`bd8a529`), labwc with the 3x3 «probe» (`95d5f54`, +1.4 % CPU to labwc) | **C21** (shape on the border), **C22** (the border is dragged) |
| 3 | Shift+arrow does not select (Shift on its own did not go out) | all | the page always resynchronises Shift and gives it back before the LETTERA (`694f77f`) | **C23** |
| 4 | with Chrome the click falls 1 px to the left on a half-pixel canvas | all | the click does not recompute the movement's point (`72d12f2`) | measure 8/8 |
| 5 | with Firefox (hardware decoding) the sensitive zone shifted «qualche mm» down | all | the **height** of the canvas too to a multiple of 16 (`fc0fbff`) | confirmed by the user |
| 6 | «Esci» makes the session be REBORN (13-16 times out of 20; 1 out of 20 with the morning's binary) | LXQt | on wlroots nothing is mounted until the session manager is on the bus (`43345ea`): **20 logouts out of 20**, XFCE 12/12, +210 ms to the first image | C20, and C24 «Esci dieci volte» (being written) |

⚠ The 1 px dot under the pointer's tip (the price of the shape on KDE and labwc) **is visible**: to be
judged by the user. ⚠ Exception declared by the user: on KDE (KWin < 6.8) at re-attach at a different
size the canvas stays the old one and the browser rescales.

**State at delivery** (24 Sep, ~23:30): binary **`7dfd6a96`** and page **`87268f13`** in the four
`rete11-*` and in 8524; the user confirmed by hand on LXQt resizing and logout, Firefox and
Chrome. ⛔ The whole net was NOT redone on this binary: by the user's decision it is replaced
by the **functional suite of phase 15**, which starts in a new session.

## ⛔ A defect found along the way, which is NOT LXQt's — Firefox and the encoder's padding

`[M]` 24 Sep 2026, from 380 canvas snapshots (`c20veri` of 23 Sep, `topo`, `veri-lxqt`): **Firefox 140
shows on the right a green strip (0,76,0) as wide as what is missing to a multiple of 16** (8 px at 1400,
4 px at 3788, 12 px at 1348), and **squashes horizontally** the image (1408 → 1400: the LXQt panel's
clock sits 6 px further left than in Chrome). In height the crop honours it. (0,76,0) is
exactly YUV (0,0,0) read as limited BT.709 ⇒ it is the encoder's padding that reaches the
screen. **Chrome 154: no strip**, on no desktop. `[R]` the server declares the crop
in the SPS (`frame_cropping_flag`); the page draws with `createImageBitmap(f)` on `bitmaprenderer`
(`pagina.html:3188`), which by specification must respect the visible rectangle: Chrome does so, Firefox
on the right does not.
- ⇒ **on GNOME, KDE, XFCE and LXQt**, every time the canvas is not a multiple of 16 wide; it was already there on
  23 September ⇒ **it is not a regression of phase 14**, and it is not cured inside phase 14 without a
  decision: the minimal cure (canvas width truncated to a multiple of 16 in `tela_da_chiedere()`)
  changes the canvas **for all** browsers, at the price of up to 15 px of border.
- ⚠ the counters of `12-client-veri` were green: it was seen only by **looking** at the snapshot.

## What remains [?]

- **Android** (Chrome on the user's phone) on LXQt and on the three with the new page: the user's.
- **the user's hand test** on `rete11-lxqt` (8514), user `nictest`/`nictest` — as for the
  other three boxes.
- `[?]` fancymenu's «Leave» button: «Lock screen» clickable and inert (declared, like XFCE's
  «Log Out» window).
- `[?]` inherited from XFCE, to be decided separately: the guard and the closing force look at every
  `labwc` of the user; the same user with a local session open confuses the product.
- `[?]` does xfdesktop have the same birth race as pcmanfm-qt? On XFCE the background in the box is
  black, so it would not be seen: not measured.
- the development box `rete14-lxqt` (8524, `/media/REMOTIX/rete14-lxqt`) stays on for the
  next tests; it does not enter the net.
