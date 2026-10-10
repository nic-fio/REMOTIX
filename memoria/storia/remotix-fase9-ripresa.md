---
name: remotix-fase9-ripresa
description: "REMOTIX phase 9 — closed on 7 Aug 2026 with zero-copy postponed: GPU acceleration is there, DMA-BUF is not, and the constraint for whoever picks it up"
metadata: 
  node_type: memory
  type: project
  originSessionId: aab51c1c-bc54-45fb-b6ac-36c9b5b96a98
  modified: 2026-08-07T09:08:14.642Z
---

**Phase 9 was closed on 7 Aug 2026**, with hardware acceleration working
(AVC420 via `h264_vaapi` on the GPU, verified on `xfreerdp3` and mstsc) and **zero-copy
capture postponed**. The account is in `PIANO.md` (phase 9 box) and in
`REFERENCE.md` R27-R30, in particular **R29 sixth point**.

**The state of the server**: `REMOTIX_DMABUF=0` is the default, written in
`provision-server.sh` with the reason why. It costs 18 ms of CPU per frame instead of 6.
The working port is **3392** (3389, 3390 and 3391 belong to the benches).

**The postponed defect**, so as not to start from scratch: the buffer that Mutter lends in
zero-copy **is not a frame, it is a *diff*** — it recycles four buffers and repaints into them
only the changed region (282 frames out of 300). Whoever takes it whole delivers
screens already past. The right correction — accumulating the regions on a persistent
surface — **is written and made things worse on mstsc**: it is behind
`REMOTIX_ACCUMULO=1`, off. The first suspect for what is missing is
`SPA_META_SyncTimeline`.

**The constraint for whoever picks it up, and it is the lesson of the day:** first the bench that makes the
defect appear **by itself**, then the correction. The two reproductions built on
7 Aug — client in the container on loopback, client on the LAN — stayed green while the
defect was alive in real use, and the correction validated there was put to the test
by the user. Without that bench, zero-copy is not done.

**Still to do**: the test on **RDM** on the in-memory path; `h264_qsv` and
`h264_nvenc` remain unmeasured.

See [[remotix-metodo-documentazione]] and [[remotix-microfono-sospeso]].
