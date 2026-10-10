---
name: remotix-prossimo-kde
description: "REMOTIX phase 11: KDE CLOSED and documented on 8 Aug 2026. The next desktop is XFCE (wlroots family). One open defect remains in the shared path, and two decisions"
metadata:
  node_type: memory
  type: project
  originSessionId: 1aac11ab-166c-4641-9520-e34064b18f20
  modified: 2026-08-08T14:55:48.072Z
---

# Phase 11, KDE — CLOSED. The next one is XFCE

> **8 Aug 2026, user's decision**: *«nella prossima sessione occuparci del prossimo DE:
> XFCE. Però prima chiudere in modo ordinato la parte di KDE — documentazione e codice»*. Done:
> `PIANO.md` phase 11 rewritten (KDE closed, XFCE open), `kde.md` §14-bis of closure, `LEZIONI.md`
> §3 with **two corrected lines and two new questions** (13 «does a virtual screen resize?» and
> 14 «whose is the clipboard?»), the two benches that now really declare their own faults.
>
> ⭐ **For XFCE, three things that count more than everything else**: `appunti_wlr.c` **is already written** for that
> family (the protocol is wlroots'); wlroots **makes you pull** the frames instead of pushing them, and it is
> the only difference that changes the *shape* of the code; and step zero stays *«chi, al mondo, fa
> questa cosa su questo desktop?»* — for wlroots the answer is **wayvnc** and
> `xdg-desktop-portal-wlr`.

*Task set by the user on 7 Aug 2026 («prossimo DE KDE»), and the same evening: **«prima leggi la
documentazione, poi studia a fondo la codebase di KDE con 10 subagenti e produci `kde.md`»**. Done.*

## The study exists: `kde.md`, and it must be read in full

**`~/Documenti/REMOTIX/kde.md`** (1295 lines) is the project's fifth study, in the form of
`gnome-remote-desktop.md`. The eight KDE repositories are cloned at the Trixie version —
**6.3.6** — in `~/Documenti/REMOTIX/reference-kde/`, with the ten subagent reports in
`reference-kde/rapporti/` (9500 lines: the detail with `file:riga` that `kde.md` summarises).
`reference-kde/banco/` has the copies of our bench programs taken back from the server.

It is part of the documentation to read before writing ([[remotix-metodo-documentazione]]), and it is
quoted in `SPECIFICA.md`, `PIANO.md` and `REFERENCE.md`.

## The four questions have an answer — and on the evening of 7 Aug they were **measured**

| | |
|---|---|
| **Capture permission** | a `.desktop` file with `X-KDE-Wayland-Interfaces` (`NoDisplay=true` is fine): **no dialog, ever**. ✅ **measured**. ⛔ **But `XDG_MENU_PREFIX=plasma-` is also needed in the environment**, or KDE's service index is built **empty** and KWin says «Could not find the desktop file». In a Plasma session `startplasma` sets it (`startplasma.cpp:366`); in an environment built by us **it must be set by hand**. Do not run as root, `Exec=` must name the real binary |
| **Input** | **libei**: `connectToEIS` over D-Bus to KWin, **without any check**. ✅ **measured**: `(handle 0, 1)` from an SSH shell. `input.c` is reused almost entirely |
| **Session without monitor** | two mandatory variables **+ `XDG_MENU_PREFIX`**, compositor unit overridden. `--xwayland` **mandatory** (ksmserver) |
| **GPU without monitor** | ✅ **GPU, measured**: the renderer string via D-Bus names it. **R32 corrected**: our «in software» was wrong, because `kwin_wayland` is **non-dumpable** (xattr `security.capability`) and `/proc` must be read with `sudo`. ⚠ And «render node open» **does not prove the GPU**: it is open in QPainter too |

⛔ **And `--drm` is not practicable**: from a session without a seat it exits with status 1 (`Failed to activate …
session`), and not because of Unix permissions. Hence **`--virtual`**, with its price (§8.1) — and **one of the three
choices to put to the user was closed by the measurement, not by the user**. Two remain: resizing and
CapsLock/NumLock.

**Status: all 12 measurements closed between 7 and 8 Aug 2026**, plus a thirteenth found along
the way. Scripts in `reference-kde/banco/` — `permesso*-kde.sh`, `misure2..6-kde.sh`,
`plasma..plasma6-kde.sh` — also on the server.

✅ **The whole chain has been seen working**: `startplasma-wayland` → plasmashell in **1 second**
→ capture authorised by the `.desktop` alone → **PipeWire stream** → orderly logout that **does not take away
the user bus**.

## ⭐ The GPU: user's decision, and the trap attached

**«Non usare la Radeon, usa la Intel integrata»** (8 Aug 2026). The server has **Intel UHD 770
(i915) = `renderD128`** and **Radeon RX 6800 (amdgpu) = `renderD129`**; KWin `--virtual` takes **the
first that opens** (`findRenderDevice()`: no variable, `KWIN_DRM_DEVICES` only applies to `--drm`).

| How to deny the Radeon | GPU | Capture gate |
|---|---|---|
| `InaccessiblePaths=` in the unit | Intel ✅ | ⛔ **CLOSED** (0 `KWIN_UTILS` lines against 13) |
| `DeviceAllow=`/`DevicePolicy=closed` | ⛔ no effect: in a **user** unit devices are not delegated | open |
| ✅ **node permissions** (out of the `render` group) | **Intel** ✅ | ✅ **open**, stream obtained |

⛔ **Hence: never harden the compositor's unit with options that imply a mount namespace.** For
the product the GPU is excluded with a **udev rule by PCI id**
(`/dev/dri/by-path/pci-0000:03:00.0-render`), not by node number, which is not stable.

## ⭐ Zero-copy is the condition of the requirement, not an optimisation

Measured on the **Intel**, declared scene and in motion: **59 fps from 720p to 4K with zero-copy**; in
memory **43.3** at 1080p and **27.0** at 4K. The 60 at 4K the user asks for
([[remotix-requisito-prestazione]]) are obtained **only** with zero-copy: the bottleneck is
**the copy**, not the compositor nor the GPU.

And on KWin **the capture delivers whole frames**, so the defect that keeps zero-copy off
on GNOME does not come back ([[remotix-fase9-ripresa]]) — but ⚠ **synchronisation must be waited for**: the
100 % of DMA-BUF buffers arrive with drawing in progress, because KWin does `glFlush` and **not** `glFinish`
(which it does only on NVidia and llvmpipe). «It synchronises by itself» must be understood as «submits», not «waits».

## The other answers, in brief

- ⛔ **`KWIN_COMPOSE=O2` does not protect**: with the render nodes inaccessible KWin falls back to QPainter **and
  starts**. `LIBGL_ALWAYS_SOFTWARE` and Mesa's other variables **have no effect** on KWin. The only
  valid test: `gdbus … org.kde.KWin.supportInformation | grep 'renderer string'`.
- ⚠ `ksmserver` and `Xwayland` **did not start** and the session worked: the constraint
  «`--xwayland` mandatory for ksmserver» **did not show up** — but do not remove it without having
  verified the orderly logout.
- ✅ the capture is **independent of the VT**; KWin **does not crash** on absurd sizes (0×0, 99999²…); the
  wheel **is not inverted** by KWin and the two axes are treated with the same formula.
- ⚠ plasmashell, at the first OpenGL failure, writes **`SceneGraphBackend=software` persistently**
  in `kdeglobals` and restarts by itself: the modal dialog is only the second round. A
  session started without GPU **leaves a mark in the user's home**.
- ⏱ setting up a stream costs **65–67 ms**; the first Plasma session creates **23 files** in `~/.config`.

## ⭐ The reference is `KRdp`, and the first round of study had missed it

There is **a `gnome-remote-desktop` for KDE**: `plasma/krdp`, C++ on FreeRDP + kpipewire, 4 222 lines.
Its `.desktop` declares `X-KDE-Wayland-Interfaces=org_kde_kwin_fake_input,zkde_screencast_unstable_v1`
— that is, **the permission road is not a deduction of ours**. It also confirms the two codecs, the regulator
from the RTT, the exclusive region edges and TLS-with-PAM. What it does not solve: **it does not start the session**
(it lives inside Plasma) and on the direct path **it has no clipboard** (empty function).

⚠ Trixie has **krdp 6.3.5**. Reports 11-16 in `reference-kde/rapporti/` have the detail, including
**the defects corrected between 6.3.6 and the development branch**, which are defects we must not make.

**The first round of study had missed it** because it searched inside the eight repositories chosen by me:
the lesson is step **zero** added to `LEZIONI.md` §9 — *«chi, al mondo, fa questa cosa su questo
desktop?»*, and it is asked before reading.

## ✅ Resizing: solved upstream, arrives in KWin 6.8

On 6.3.6 a virtual output does not resize. But `kwin!7932` («Resizable Virtual Monitors») was
**merged on 29 Jul 2026**, milestone **6.8**, and the chosen mechanism is **PipeWire negotiation**
(`SPA_POD_CHOICE_RANGE_Rectangle`) — that is, **the code of our phase 6**. A `resize` request
in the protocol had been proposed and **rejected** precisely for that reason.

⛔ **Hence the rule for whoever writes**: resizing on KDE is written **in the form of the
negotiation**, which becomes right by itself; «close and redo the stream» is the fallback for the versions that
do not have it, not the main road.

## ✅ The three decisions, taken by the user on 8 Aug 2026

| | |
|---|---|
| **Zero-copy** | **now, inside KDE**: the capture **is born zero-copy** (with waiting on the fence), it is not written twice |
| **Resizing** | **fixed size at connection** on Trixie, but **written in the form of the PipeWire negotiation**, so on KWin 6.8 it turns on by itself |
| **CapsLock/NumLock** | **the real state is read** with `org_kde_kwin_keystate` — it costs little because on KDE the Wayland connection is already there for the capture: one more name in the `.desktop` |

## ✅ ITEM 1 IS DONE — 8 Aug 2026: the KDE desktop can be seen

**`prove/fase11.sh` passes all the checks**, in two modes (`fase11.sh` functional,
`INTEL=1 fase11.sh misura` for the rhythm), and leaves the machine clean.

| | 1920×1080 | 3840×2160 |
|---|---|---|
| **capture, real chain, Intel UHD 770** | **58.1** | **58.4** |
| the meter alone, 7-8 Aug | 59.2 | 59.0 |

That is **the bench number holds outside the bench**; the missing half frame is the conversion
on the card. ⚠ The number **at the client** is another thing (24 at 4K): the cap is `xfreerdp3`, which
decodes in software, as already in R32.

**What is new**: `src/kwin.c` (Wayland client: registry, `stream_output`, event pump that
keeps the connection alive), `src/compositore.c` (the single door: the stage no longer names Mutter),
`src/protocolli/` (the XML at **v5**), the options `--compositore` and `--installa-desktop`,
`prove/fase11.sh`.

**The four things confirmed in the field**: the permission works for us too (`.desktop` +
`XDG_MENU_PREFIX`); the fence is simply waited for (2400 buffers out of 2400 with drawing in progress, **zero
expired waits** with a 50 ms ceiling); the modifier obtained is **0x0 linear**, asking for it
first; the size is imposed by the compositor and **must be adopted in two places** — in the stage and in the graphical
canvas.

## ✅ ITEM 2 (INPUT) IS ALSO WRITTEN AND TESTED — same day

⏳ **But it is not closed**: the «done when» says *«giusti a occhio, su tre client»*, and nobody has
looked at it yet. The bench says:

```
OK  canale di input concesso da KWin (gettone 1)
OK  disposizione della sessione letta da libei: English (US)
OK  14 eventi di tastiera inoltrati al compositore
OK  regione del puntatore: 0,0 1920x1080 (mapping-id «assente»)
OK  la rotella arriva come SCATTI DISCRETI nei due versi
OK  lucchetti secondo KWin: BlocMaiusc spento, BlocNum spento
```

**The four differences, all written**: `connectToEIS` with
`g_dbus_connection_call_with_unix_fd_list_sync` (⛔ the `h` type carries an **index**, not an fd: whoever
reads the body takes a zero, which is standard input); `ei_device_scroll_discrete(±120)`;
regions by **geometry**; `org_kde_kwin_keystate` v5 with `fetchStates`.

⛔ **The confirmation that counts most is negative**: `EI_EVENT_KEYBOARD_MODIFIERS` never arrived. On
KDE the lock reconciliation written for GNOME **would not run**, and without `keystate` it would have
stayed written and dead.

## ✅ AND ITEM 3 TOO (SESSION AND MACHINE) — same day

`bash prove/fase11.sh sessione`: the machine is as after a reboot, the bench **abstains**, and the
first client that knocks finds a desktop.

```
OK  unita' del compositore sovrascritta: desktop 1280x720, senza schermo di blocco
OK  avvio la sessione grafica: exec startplasma-wayland
OK  il desktop e' venuto 1280x720: la misura la ha decisa il client che si e' collegato
OK  la sentinella dell'uscita e' passiva: sorveglia un nome, non si registra
OK  schermo della sessione tenuto acceso (inibizione 1)
OK  REMOTIX se n'e' accorto SUBITO / il logout non ha lasciato processi / e' sopravvissuto
```

⭐ **«Fixed size at connection» became LITERAL**: `--virtual` wants `--width/--height`
at startup, and it is REMOTIX that starts the session when the first client connects — so the desktop
*is* of the requested size. Scaling in the client serves only whoever arrives later with another size.

⛔ **The defect that the read code could not show**: powerdevil **is not there yet** when the
stage is set up (it starts three links after the compositor), and the error was `ServiceUnknown` — «does not exist
yet», not «never». Now `energia.c` waits on a thread of its own.

⚠ **The udev rule for the GPU is written and NOT installed**: `/media/REMOTIX/gpu-udev.sh` puts it in and
takes it out (by PCI id: the Radeon is `0000:03:00.0`, the Intel `0000:00:02.0`). Denying a node with
permissions denies it **to the user's whole session**: it is a change to the machine with a price, and
it must be put in when the user decides it.

## ⬅ WHERE TO RESUME

**From item 4: the clipboard.** `zwlr_data_control_manager_v1` v2, which on KWin **is not behind any
permission** (`kde.md` §9); watch out for the echo on `setSelection` — the server cycles over *all* the data
control devices including the originator — and for the three-condition gate of report 11. And klipper
puts back the last element when the clipboard empties.

**The plan is in `PIANO.md` phase 11**: (1) capture ✅; (2) input ✅; (3) session ✅; (5) judgment ✅.

## ✅ ITEM 4 — THE CLIPBOARD, written and green on the bench on 8 Aug 2026

`prove/fase11-appunti.sh`, **zero faults**, and the user's judgment on the three clients: *«clipboard OK
su Linux, mstsc e Android»*. Having it mattered more than usual: the clipboard has three cohabitants
(klipper, the Xwayland bank, the client) and the bench drives two of them.

⭐ **WITH THIS PHASE 11 IS CLOSED FOR KDE**: five items out of five, all with the judgment.

## ✅ The debt on GNOME is paid — and the bench found a new defect

`prove/fase11-volume.sh mutter` (8 Aug 2026, **redone from a freshly rebooted machine** at the user's
request): the slider governs **on both compositors, with the same numbers** —
25.8 / 0.40 / 0.00 on a tone of 25.9 %.

⚠ **Restoring the server has TWO unwritten steps**, discovered precisely with that reboot: the disk
`/media/REMOTIX` **does not mount by itself**, and `provision-server.sh` **does not install
`pulseaudio-utils`** (nor `wl-clipboard`/`xclip`, nor KDE) — the benches depend on them. See
[[remotix-lezioni]] §2.5-bis. The correction was in the shared
path and holds, as foreseen but now **measured**.

⛔ **STILL OPEN**: «a new audio path starts at maximum» **does not work**, neither on KWin nor on Mutter.
Whoever mutes, disconnects and reconnects finds silence again. The defect emerged only by **strengthening
the check** (before, muting happened with the client connected and the value was already back up at reading:
[[remotix-lezioni]] §1.3). What is known: `pw_node_set_param` returns an asynchronous sequence
number (accepted, not an error); sampling every half second the value **never moves**,
so it is not a race; and **`pw-cli set-param` on the same node works** — the suspect is the
**proxy**, taken from `pw_core_create_object` instead of bound from the registry. Detail in
`REFERENCE.md` §7.5.

It is in **`src/appunti_wlr.c`** — `wlr` and not `kwin` because the protocol is wlroots', so the file
already serves the compositors of XFCE and LXQt. `appunti.h` stayed a single door: `appunti.c` dispatches, the
Mutter road is in `appunti_mutter.c`. Same shape as `compositore.c`.

The two things learned writing it:

- ⛔ **the guard against the echo is about STATE, not time**: an announcement is ignored if the source is
  **still ours** and the types match. It holds because when someone else copies KWin sends
  `cancelled` *before* the announcement. The criterion «the first after ours» that `kde.md` proposed is
  a time rule, and time rules go wrong when two things happen together;
- ⛔ **`POLLHUP` counts as «ready» for reading**: whoever owns the clipboard writes and closes, and with short data
  `poll` returns with only `POLLHUP`. Looking only at `POLLIN` the code declared a 5 s timeout
  **after 3 s** — the impossible number in the log was the only clue.

## ✅ ITEM 5 IS CLOSED — 8 Aug 2026, all three clients

**xfreerdp ✅, RDM (Android) ✅, mstsc ✅** — *«mstsc OK!»*. The three-client rule is satisfied,
so items 1, 2 and 3 are closed **by the judgment** and not by the bench. The judgment, in full: **wheel ✅**, **terminal ✅**
(including privileged operations), **audio ✅ and synchronised with the video**, **1080p video «alla
massima fluidità»**, **RDM (Android): «performance eccellenti»**.

The numbers read in parallel with playback: **57.8 fps delivered**, encoding **1.7 ms** per
frame, **conversion and upload at zero** — that is, the DMA-BUF zero-copy that on Mutter had not
been obtained ([[remotix-fase9-ripresa]]). The encoder works at 10 % of the available time.

**The three defects were found by him, and they were closed the same day:**

1. **double pointer** — ⭐ the cure is **making KDE's cursor transparent**: an
   `XCURSOR_THEME` theme with a 1×1 cursor at zero alpha (KWin looks at it **only if
   `XCURSOR_SIZE` is also there**), and the pointer goes back to being the client's, as on Mutter. The first
   attempt — `SYSPTR_NULL` to the client — worked on xfreerdp but **not on RDM**, where the second
   pointer is the app's *touch pointer*, outside the protocol. ⛔ If the theme turns out empty KWin
   **falls back to the visible theme**: all the shapes are written (68), and the check that counts is
   the absence of the fallback in the journal. ⚠ The shape change is lost, as on GNOME: giving it back
   means sending the real shape on RDP's **pointer channel**, from the PipeWire metadata
2. **the volume slider governed nothing** — `monitor.channel-volumes` was missing on our
   sink, and in PipeWire the volume is applied **downstream** of the monitor tap (`kde.md` §10.5).
   ⚠ The measurement done on a sink created with `pactl` **acquitted** the code, because
   `pipewire-pulse` sets that property by itself: the lesson is in [[remotix-lezioni]] §5.
   ⭐ **User's decision**: the level is carried by the **server**, inside the samples — it is the only
   road that holds on mstsc, Linux and Android and on every desktop, and the client → server direction in RDP
   **does not exist**. Hence the sink is raised back to maximum **at every connection** (not only at
   creation: WirePlumber puts back the saved levels and wins the race). All in `REFERENCE.md` §7.5
3. **«Lock» and «Switch user» in the menu** — removed with KIOSK (`kde.md` §10.6); ⚠ they take effect
   **from the next session start**, not on a live one

⚠ **What item 1 did not do and the others need**: in the bench the Plasma session is started by the
script and the Radeon is denied by hand (`INTEL=1`, `chgrp`); `uscita.c` still looks for `gnome-session` and on
KDE will never find it (now it says so only once instead of twice a second). All this
is **item 3**.

⚠ **Three details of the reports remain to be poured in, and they are read inside the item that uses them**: the
**wall-clock window** bandwidth and the **cursor** in 171 lines (item 1), the **three-condition gate** of the
clipboard (item 4).

⛔ **And the two traps to reread before touching the compositor's systemd unit**: no
`InaccessiblePaths` (or anything else that implies a mount namespace) — it closes the capture gate; and
`KWIN_COMPOSE=O2` does not guarantee the GPU, which is verified only by asking KWin for the renderer string.

⚠ And before re-measuring: `misura-cattura.c` must be corrected in two places (`--fissa` does not negotiate with KWin;
the cursor's `SPA_CHUNK_FLAG_CORRUPTED` buffers are counted as frames).

## Two bench traps that cost half a session

1. **`/proc/<pid>` of `kwin_wayland` is denied** because the binary carries the `security.capability` xattr:
   a binary with file capabilities is **non-dumpable**, and `fd`/`maps` become root-only *even for
   whoever started it*. `ls | grep` prints nothing, the error goes to stderr, and «empty» looks like
   «zero DRM nodes». Copying the binary to lose the xattr **does not work**: the copy does not load the
   QPA plugin `wayland-org.kde.kwin.qpa` and dies with `Aborted`. It is read with `sudo`.
2. **On Mesa ≥ 25 llvmpipe lives inside `libgallium-*.so`**: looking for `llvmpipe`/`swrast_dri` among the
   loaded libraries no longer proves anything. The test that holds is **the open render node**.

And the permission diagnosis is done in three seconds with `QT_LOGGING_RULES='KWIN_UTILS.debug=true'`: the
line is in **`KWIN_UTILS`**, not `kwin_core`, and it distinguishes «Could not find the desktop file» (index)
from «Interfaces found … : ()» (empty field). These are lessons `LEZIONI.md` §1.9 and §1.10.

## The server, after the reboot of 7 Aug

Rootfs in RAM, it is put back with three commands, in this order:
`provision-server.sh` → `server.sh copia` → `tmp/banco-compositori/provision-banco.sh`.
The cadence at 60 is in `main.c`, not in an environment file — and it must not be put back by hand.

⚠ **State left on the evening of 7 Aug**: the REMOTIX service **is not installed** (`systemctl
is-active remotix` → `not-found`, `/etc/default/remotix` absent), so no 33xx port is
listening. For the KDE bench `kwin-wayland`/`kwin-common` **4:6.3.6-1**,
`pipewire 1.4.2`, `wayland-utils`, `weston` were installed, and the user is in the groups `video,render`. The machine has
**two GPUs** (`card0`/`renderD128`, `card1`/`renderD129`) and KWin takes `renderD129`.

⚠ And every SSH command opens a **new logind session** (49, 50, 51…), all **without a seat**: a
session identifier read in one command is not valid in the next.
