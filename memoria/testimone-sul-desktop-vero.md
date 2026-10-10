---
name: testimone-sul-desktop-vero
description: "How to measure with the browser what actually reaches the remote desktop — the witness file, and the two nets to remove from the page"
metadata: 
  node_type: memory
  type: project
  originSessionId: 6c6f9648-d9f9-4e2a-9127-2557b8767681
  modified: 2026-08-16T13:59:02.925Z
---

⭐ **The meter of the browser tests** (16 Aug 2026, phase 5). Inside the
graphical session of `prova` a terminal is launched from ssh with:

```sh
while IFS= read -r _; do date +%s%N >> /tmp/testimone.txt; done
```

⇒ Every `Invio` (Enter) that **reaches the desktop** writes a line with the instant in
nanoseconds. A key left down repeats by itself — `[M]` **~33 strokes per
second**, it is the remote desktop that does it — and the last stroke is compared with
the time of the line in the log. Precision obtained: **milliseconds**.

**Two traps, both paid for:**

1. ⛔ **The browser driver cannot HOLD DOWN** a key: `computer` always sends
   down-and-up. Use `javascript_tool` with
   `window.dispatchEvent(new KeyboardEvent("keydown", {code:"Enter"}))` — the
   page's functions are true globals, reachable by name.
   ⚠ Only **non-letter** keys can be held down: a letter goes out as
   `LETTERA`, which is press-and-release.
2. ⛔⛔ **The page releases by itself** on `blur`, `visibilitychange` and
   `pagehide` (`cl_rilascia_tutto`). ⇒ From the browser the server almost never has
   anything to release, and **you certify the page believing you are certifying the
   server**. To test the server, replace `window.cl_rilascia_tutto`
   with a stub.

⚠ **And the silence clock steals thirty seconds from the tests**: if between
preparing and provoking 30 s go by, `§5.3` has already released everything and the
measurement is of something else. It happened twice.

The wire cut is done from the server with an `nft` table of its own
(`nft delete table inet provataglio` to remove it), never with `iptables` — on the
test machine it is not there.

See [[costruire-serve-il-contenitore]] and [[utente-prova-si-conserva]].
