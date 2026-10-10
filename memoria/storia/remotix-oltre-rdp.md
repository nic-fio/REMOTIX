---
name: remotix-oltre-rdp
description: "REMOTIX — discussion OPEN and parked on 7 Aug 2026: leaving RDP. The user's criterion, the three roads, the question that closes one for free, and the correction on the 18 fps"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2a0517e7-89e9-4d34-9714-c2d00ae6c5ce
  modified: 2026-08-07T16:11:19.601Z
---

On **7 Aug 2026, in the evening**, the user opened a chat — declared as such, without
work — about **developing a protocol of our own with client and server**, and **parked it
to pick it up later**. His position, which is the thing not to lose:

> *«Sono stufo di andare incontro a problemi per colpa di protocolli che non si capisce bene
> come funzionano. Io ho le mie esigenze: se qualcosa le soddisfa bene, altrimenti il software
> ce lo scriviamo.»*

And before, on the blank sheet: *«comincio ad avere il prurito»*. It is the same reversal as
[[remotix-requisito-prestazione]] one level up — **the needs come before the
protocol**, not the other way round.

## The three roads on the table

| | Cost | Does it move the two numbers? |
|---|---|---|
| **Staying on RDP** | zero | the minimum yes (it is upstream of the wire), the desired no: EGFX is capped at H.264, and the reference Android client does not decode it |
| **Our own protocol + three clients** | **3-4 times everything built so far**, plus maintenance forever, and it changes §1 of the specification (REMOTIX is no longer a «standard RDP client») | yes, but only after having solved the capture anyway |
| **Sunshine/Moonlight protocol on our host** ⭐ | a «new phase 2», big | **the shortest road to 60 fps at 4K**: hardware decoding on Android is their normal road |

## The third, as it would stand up

**The client is not forked.** Their protocol is implemented on **our** host and the
official clients taken from the store, vanilla, connect to it; clipboard and live resizing do not exist
in version one. The fork is decided after having used it. This way half of the licence
question (GPL) also falls: implementing a protocol is not bringing a host's code into the house.

The piece that **would stay ours and is not thrown away** is almost all of REMOTIX: GNOME session without
monitor, `RecordVirtual`, libei, logind, PAM, the invented audio sink, the clipboard via Mutter. It is
the part that Sunshine on GNOME **lacks**.

And as a dowry: on the other side of the wire there would be an **open and recompilable** client, that is the
best bench the project has ever had — with mstsc a black screen is a riddle,
there it is a `printf`.

## ⛔ The question that closes the third road FOR FREE, and it must be asked first

**Does Sunshine capture a GNOME session without monitor WITHOUT asking for an on-screen permission?** Its
road on Wayland historically goes through the **portal**, which §2 of the specification rejects for an
unattended service. If there is no direct way to the compositor, what we would have to write
is again everything, and the question is closed without spending anything. An afternoon of bench,
[[remotix-prove-sul-banco-non-sull-utente]].

## ⛔ Correction: the 18 fps do NOT measure the compositor

Said badly by me in this conversation, and the user was right to doubt it
(*«i compositor moderni su MESA non hanno prestazioni così scarse»*). Verified on 7 Aug:

- **the groups trap is closed**: the user's systemd manager has `44 (video)` and
  `991 (render)`, so the Shell opens `/dev/dri` and GNOME **composites on the GPU**, not in software
  (§8.6-ter of `REFERENCE.md`);
- **18 is not a ceiling of ours**: to PipeWire we declare **30** (`main.c:136`, `--fotogrammi`);
- **the scene of the measurement is not declared**, and Mutter sends a frame only when something
  changes: a scene moved by keystrokes does not measure a throughput. **All** the frame
  measurements on the real desktop have this flaw.

What the 18 proves is **only** that the bottleneck is neither the protocol nor the
encoder.

> ✅ **MEASURED on the evening of 7 Aug 2026, and the answer is a third one: neither of the two candidates.**
> The 18 are **the cadence we declare ourselves**: we ask PipeWire for 30 and Mutter gives 18;
> asking for 60 it gives 37. The ceiling that remains at 37 is Mutter's — the client draws 60 on a screen
> at 60 Hz — and **KWin (60) and wlroots (61) do not have it**. `REFERENCE.md` **R32**.
>
> **Fallout on this discussion**: the third road (Sunshine/Moonlight) stays the shortest to 60
> fps at 4K *on the wire*, but it would not solve by itself the capture ceiling, which is upstream of the
> protocol. The shortest road to 60 measured so far is **changing compositor**, not protocol.

**Counter-proof that RDP's age is not the cap**: `gnome-remote-desktop` aims at 60
(`TARGET_SURFACE_REFRESH_RATE`) and xrdp declares `h264_frame_interval=16` ms, that is still 60 —
on the same Wayland/Mesa stack.

See [[remotix-metodo-documentazione]] and [[remotix-fase9-ripresa]].
