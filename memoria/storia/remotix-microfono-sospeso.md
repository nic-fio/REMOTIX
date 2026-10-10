---
name: remotix-microfono-sospeso
description: "REMOTIX — the microphone (phase 8, item 4, MS-RDPEAI) is suspended by the user's decision since 6 Aug 2026"
metadata: 
  node_type: memory
  type: project
  originSessionId: aab51c1c-bc54-45fb-b6ac-36c9b5b96a98
  modified: 2026-08-06T04:53:09.136Z
---

In the REMOTIX project item 4 of phase 8 — **microphone, MS-RDPEAI** — is **suspended
by explicit decision of the user (6 Aug 2026)**: it is not written until he
says so. Items 0, 1 and 2 (virtual sink, PCM audio output, clipboard) are closed
and measured; phase 8 does not stay open because of this.

**Why:** the user decides the features and their order; the suspension is a choice
of priority, not a technical block.

**How to apply:** do not propose or start the `AUDIO_INPUT` channel; if a piece of work
touches it, stop and ask. Also noted in `PIANO.md`, phase 8. See
[[remotix-metodo-documentazione]].
