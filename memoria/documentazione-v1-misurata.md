---
name: documentazione-v1-misurata
description: "~/Documenti/REMOTIX is the documentation of v1 (600 KB of measurements): read it BEFORE redoing something that worked in v1"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 779c5805-3064-4996-b3bd-0230542c5ee9
  modified: 2026-08-17T10:00:01.747Z
---

`~/Documenti/REMOTIX/` — it is **not** code, it is the **documentation of v1**, and
it carries measurements that were not redone in V2:

| file | what it contains |
|---|---|
| `REFERENCE.md` (168 KB) | the measured rules: **R25** the rhythm of the audio blocks, **R26** the real-time priority, R27 the hardware encoder, R24 the sign of the PCM |
| `SPECIFICA.md` (134 KB) | §7.5 the virtual sink created by us |
| `PIANO.md`, `LEZIONI.md` | the phases of v1 and the method |
| `protocollo-rdp.md`, `xrdp-funzionalita.md` | the dead protocol, kept for the lessons |

⛔ **R26 is the one that cost the most for not reading it**: a process with
`RLIMIT_RTPRIO` at zero cannot ask for `SCHED_FIFO`, PipeWire gets it
denied, and the symptom is **audio that crackles when the desktop is working** —
invisible to every check on the wire. It is granted in the **systemd unit**
(`LimitRTPRIO=20`, `LimitNICE=-11`), not in the code.

**Why:** on 17 Aug 2026 I chased for hours an audio defect that v1
had already measured and written down on 5 Aug. It was Nic who said *«nella prima
versione l'audio funzionava, esamina quella cartella»*.

**How to apply:** it is **point 0 of the recipe** of `LEZIONI.md` §9 — *«chi, al
mondo, fa già questa cosa?»* — in the variant that counts most: **who, in our
own house, has already solved it?** Before writing a piece that v1 had, look
here. ⚠ The code of v1 is elsewhere (`REMOTIX/fondamenta/remotix-c/src/`): this
folder is the **measurements**.

See [[misura-anche-chi-ascolta]], [[remotix-convenzioni]].
