---
name: remotix-studi-desktop-v2
description: "REMOTIX, 8 Aug 2026: XFCE and LXQt studied in depth; the four desktop studies now live in ~/Documenti/REMOTIX_V2, and the session turned into brainstorming"
metadata: 
  node_type: memory
  type: project
  originSessionId: 138511ec-a8d5-41e8-aa33-68bf30c9b950
  modified: 2026-08-08T19:43:25.521Z
---

On 8 Aug 2026, after closing KDE, **three new studies were done with ten subagents
each**: `xfce.md` (labwc/wlroots, ~10 700 lines of reports), `lxqt.md` (~6 200) and **`gnome.md`
(~7 200)** — the latter because `gnome-remote-desktop.md` studied **GNOME's RDP server, not the
desktop**. ⚠ **None of the three is measured**: they are code readings, and each one ends with its own
measurement plan.

⛔ **The GNOME study found more defects of ours than the other two together, on the desktop that
we serve in production.** The three that weigh: (1) **R29 is wrong** — Mutter's DMA-BUF **is not a
diff** (the virtual view is a persistent `CoglOffscreen` and the blit copies everything), so the
accumulation surface made things worse; the real defect is the **release** (`can_reuse_pw_buffer` gives
up without `SPA_META_SyncTimeline` and reuses the buffer while VA-API is reading). (2) **GNOME's screen lock
does not show a screen: it calls `inhibit_remote_access()` and DETACHES the RDP session from us** —
the exception is `is_headless()`, which today we have **by accident** (Mutter degrades by itself without a
seat), not because we asked for it. (3) **The machine suspends by itself at 900 s** (default
`sleep-inactive-ac-type=suspend`); cure: `SessionManager.Inhibit(…, 4|8)`. Plus: `EI_EVENT_KEYBOARD_MODIFIERS`
**does not arrive on GNOME either** (our documents said the opposite in two places), the clipboard
**does not belong to the session** but to Mutter, and the client can suspend the acks with
`queueDepth == 0xFFFFFFFF` — to be verified in our regulator.

**Where they are**: the user asked to move all the desktop documentation into
**`~/Documenti/REMOTIX_V2`** — `gnome-remote-desktop.md`, `kde.md`, `xfce.md`, `lxqt.md` and the folders
`reference-kde/`, `reference-xfce/`, `reference-lxqt/`. In `~/Documenti/REMOTIX` remain `PIANO.md`,
`SPECIFICA.md`, `REFERENCE.md`, `LEZIONI.md`, the three old studies and `strumenti/`. In REMOTIX_V2
the user put on his own `INIZIO.md`, `CODER.md`, `REVIEWER.md` (not read).

⭐ **The result that counts most of all**: the axis is **the compositor, not the desktop**. The
realistic desktop×compositor combinations on Trixie are **9**; today 2 are covered, and **after
the wlroots phase alone they become 8 out of 9** — LXQt brings four **without a line of new code**,
because it runs on the same labwc as XFCE (or on KWin, which is already done).

⛔ **And the fact that changed the LXQt phase**: on Debian Trixie **an LXQt-Wayland session does not
exist as a package** (`lxqt-wayland-session` is in forky/sid, not in Trixie) — but the Wayland code
is compiled and shipped: **only the launcher** is missing, which REMOTIX writes by itself. Hence a lesson
for the recipe: **step zero-bis, «does this desktop, on this distribution, have a Wayland
session?»** — two commands, and they must be run before studying.

**The state of the session**: the user declared that *«questa sessione si trasforma da sviluppo a
brainstorming»* and that he **intends to revolutionise the project**, saying so once the study is complete.
For this reason `PIANO.md`, `SPECIFICA.md`, `REFERENCE.md` and `LEZIONI.md` **were not updated**
with the two new studies: the update is suspended pending that decision.

See [[remotix-prossimo-kde]], [[remotix-lezioni]], [[remotix-metodo-documentazione]].
