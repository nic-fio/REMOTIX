---
name: come-guarda-nic-lo-schermo
description: "From CHUWI/tty2 the fifth link (xrdp+RemoteFX) is NO longer there: local GNOME Wayland session, DP-2 monitor 3440x1440. The tests done before the evening of 17 Aug went through that link"
metadata:
  node_type: memory
  type: project
  originSessionId: defbf3a3-9ed8-459f-9f2a-dc508d102cbc
  modified: 2026-08-17T15:38:44.228Z
---

⭐ **17 Aug 2026, evening — Nic is PHYSICALLY in front of the machine.** `who` gives
`nicfio seat0 tty2`, `loginctl` says `Type=wayland Remote=no`, and there is no
`Xorg :10`: **native GNOME Wayland session**. The machine is a **CHUWI Hi10 X1**
(`192.168.0.3`, Intel **N100**, 4 cores, UHD Alder Lake-N) with **two outputs
on**: `DP-2` **3440×1440** (the monitor he looks at) and `DSI-1` 800×1280
(the tablet's panel, vertical).

⇒ **The chain goes back to FOUR links**: compositor (on `192.168.0.2`) → our
encoder → wire → Firefox+canvas on the CHUWI → his eyes. **What he sees
now are our pixels**, without intermediaries.

## ⛔ But the fifth link DID EXIST, and must be kept in mind to read the past

Until 17 Aug ~17:30 the CHUWI's graphical session was `Xorg :10` started by
**xrdp** (2560×1080), watched from Windows with an RDP client, and
`~/.xorgxrdp.10.log` said `got RFX capture` — **RemoteFX**, a **tile**
codec with frame acknowledgement, whose typical faults are literally the two
symptoms reported (**rectangular blocks** and **image that stops
updating**). ⚠ Put to the test (`banchi/07-b47-controllo-xrdp.html`) it had
**held**, but all the graphical tests up to that evening went through it.

⛔ **And with RDP THREE things changed together**, so a «now it doesn't show
any more» does not blame xrdp alone: (1) the RFX link disappeared; (2) Firefox no longer runs
on X11 but on **Wayland**, with a different composition path; (3) the
CPU no longer carries the RFX encoder, and on an N100 software AV1
saturated it.

**How to apply:**
- a **visual** defect reported from today on is **ours or the browser's**: there is
  nothing after our canvas any more;
- if a defect seen before the evening of the 17th **does not reproduce** now, do not
  write «it was xrdp»: write which of the three variables was isolated;
- the witness on the Linux side stays useful, but on Wayland `import -display :10`
  no longer works: use the Marionette witness
  (`banchi/07-b46-testimone-disegno.py`) that pulls down **the canvas** as PNG.

See [[testimone-sul-desktop-vero]], [[la-prova-la-fa-lutente]],
[[prestazioni-sul-ferro-modesto]].
