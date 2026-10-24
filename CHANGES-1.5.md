# REMOTIX 1.5 — release notes (draft, 24 Oct 2026)

> Range: `git log 5cf8ca10..HEAD` on branch `integrazione` (package 1b, audit, login defences) over package 1
> (`git log 04f6aa18..5cf8ca10`). Every line cites a commit or a section of `docs/1.5/DECISIONS-11.md` (written «§11.x»).
> ⚠ Status words are those of the sections: «built», «under verification», «approved, verification in progress». Nothing here
> has been run on the full suite or the A/B yet (see «Still open»).

## Contents
1. What is new for the user
2. Behaviour changes (login ban, page headers, clipboard, picture, connection)
3. Defects of 1.0 fixed (security and robustness)
4. Requirements that changed
5. Still open

## 1. What is new for the user
- **A flood of fake connections no longer costs the server a connection each.** The first packet of every connection must
  come back with a token (QUIC Retry), and a client that talks to a restarted server is told at once to start again
  (Stateless Reset) instead of waiting ~30 s (§11.9, under verification; `51e3634a`, `f79d1d18`). Price: one extra round trip when a
  connection opens. It stops forged source addresses, not attacks from real addresses nor a saturated line (§11.9).
- **The server cannot be filled before login.** Caps: 256 connections, 128 not yet logged in, and at most 8 not-yet-logged-in
  connections per IPv4 address or IPv6 /64, 32 per /48; when the server is full the oldest not-yet-logged-in connection is closed, never one that is
  being checked or logged in; 90 s without login closes the connection (§11.40, under verification; `ffea98a1`, `75ba1f93`).
- **Changing network keeps the session** (e.g. Wi-Fi to mobile): the packet path follows the one the datagram came on
  and a validated move updates the connection (§11.29, RCP.md §2.3, under verification; `fa7eac00`, `f606542e`, `eb8d9db2`). Declared limit: until
  the new path is validated the server may send up to 3× what it received from it; the ban and the logs keep the birth
  address. Not yet measured on a real network change.
- **The last row of the picture has the right colour on Chrome** (it was tinted, e.g. green on GNOME): cure (c), the page
  trims the last row when the decoded frame has coded rows below the visible ones (§11.41, verified on gnome and xfce, kde and lxqt due; `571c8145`, `9b963d77`,
  earlier steps `78b63549`, `127f69a6`). Cost: the bottom row repeats the row above.
- **Installer and uninstaller**: the install plan states the port before «Proceed? [y/N]» (`29a4a7ce`); the uninstall removes
  what upgrades added (§11.6, under verification; `84fdf573`, `b4f0776e`). The site says «Download 1.0.0» (`b2f8161e`).
- **`/diary` is gone** from the installed product and from test builds (§11.10, under verification; `8a46c9c9`, `9af7b82e`).

## 2. Behaviour changes
### Login ban — SPEC CHANGE from 1.0 (§11.53; built on `login-difese`, not yet run on the boxes)
- 1.0 (DECISIONS §1.9): 3 failures from one address, address out for 12 h. 1.5 replaces it (`8f56da22`, `3e2d4467`, `8d397b20`).
- Three counters over a sliding window: (address, user) 5 failed in 5 min; address 12 failed in 5 min; IPv6 /48 30 failed in 10 min.
- Progressive ban per level: 15 min, then 1 h, then 12 h; forgotten after 24 h without a ban. A good login resets only the
  failures of (address, user). So 5 wrong passwords for one user block that user on that network; another network still works.
- The address key is the IPv4 address, or the IPv6 /64 (link-local with its `%zone` too); `::ffff:` and NAT64 count as the
  IPv4 inside, `::1` whole (§11.53 A; §1.9-bis, closed: `60c12018`).
- Attempts are booked when the credentials arrive (at most 2 checks at once per address and user); a verdict whose
  connection died is still counted; no verdict (PAM timeout, 12 s ceiling) counts as a failure, but a dead helper does not.
- The ban file holds an HMAC-SHA256 of the user name, never the name (0600, `fsync`ed); log lines name unknown users
  `unknown user [a1b2c3]`. Old 1.0 lines are read and become a 12 h ban. `UNBLOCK <address>` clears every level.
- The page's ban notice and the `0x08` text follow the rule, without a number of attempts (`546fe91c`); manuals and specs updated
  (`47eba75e`, `2cc1b424`, `be61b885`, `798a00a0`). Tests: `benches/unit/login-ban` (`8db14aaa`, `a9c48435`), B8 (`f3733e77`).

### Page headers and checks (page audit)
- The HTML response carries a Content-Security-Policy, `Referrer-Policy: no-referrer` and a Permissions-Policy
  (clipboard for the page itself only) (`65e78f14`). Still open by choice: `unsafe-inline` and `connect-src https:` (`4324ba93`).
- A SESSION or CANVAS granting a canvas of zero or above the maximum closes with PROTOCOL_ERROR (`d3a16466`); a response whose
  headers do not fit the buffer answers 500 instead of truncating (`bd4840db`).

### Clipboard
- A text with a zero byte in the middle is **not announced**, on KDE and GNOME (§11.6; `8031958d`, order of the checks `322468ea`,
  `d8f48441`); a type that delivers 0 bytes is skipped as an empty clipboard (`b3f8cde6`). Tests: F-014E, KDE only, PASS 2/2 on KDE on `pacchetto1b` (`22ea3008`,
  `550b1b37`, `396f7dae`), and `benches/unit/clipboard-zero` for both desktops (`c7ff0915`, `af7d8146`).
- The page logs focus, visibility, user activation and the `writeText` outcome when it writes the clipboard (diagnostics
  for F-015C, `71970919`). Passwords and clipboard copies are wiped with `explicit_bzero` after use (§11.6; `84fdf573`).

### Connection and timing
- One write burst is at most the send quantum, and the loop timeout is rounded up (§11.52 A; `643e9a40`, `3a6d128c`). `pacing-ab`
  then measured +1 ms of RTT at rest from that round-up (24 Oct), so the main loop now waits on the exact deadline with `ppoll`
  (`1b447d3c`, `de5ebdfa`); to be measured again (see Still open).
- «Connection closed» log lines of connections that never logged in are limited per window, the rest in a summary (`6368c6a8`).

## 3. Defects of 1.0 fixed (all «present since 1.0»)
Found on 24 Oct 2026 by the fuzz harnesses and by reading the ngtcp2 1.25 / nghttp3 1.18 headers call by call (§11.52,
**approved by the user on 24 Oct 2026, verification in progress**; 13 fixes: A 1 + B 6 + C 6).
- **Pacing bypassed** (found by the `quic-conn` fuzz pacing oracle): one call could put ~45 packets on the wire at once (A).
- **ngtcp2 (B)**: a connection to be dropped silently was answered with a CONNECTION_CLOSE (a reflection toward a forged address)
  (`d624d875`, `0cc6df15`); a failed handshake closed with NO_ERROR instead of the TLS alert (`5cb76986`); timer errors never sent the
  close (`94c1f5ac`); freed connection reachable through the SSL app data (`cbe7d0cd`); deprecated calls renamed (`d935abcf`); an
  H3 error code overwritten on close (`8171e6c1`).
- **nghttp3 (C)**: closed streams never released, memory and a list scan growing with every stream (`672c9d42`, `515c2e7a`, `4923f68d`);
  ignored results (`e7c469f1`); `NGTCP2_ERR_STREAM_NOT_FOUND` treated as a connection error (`86af9276`); `rand()` in the random
  callback (`b6e3c5c1`); a second WebTransport CONNECT renewed the first session's deadline and overwrote its state (`f395aff5`).
- **Sign of life** counted a packet ngtcp2 had discarded, letting an observer keep a dead client alive (found by the `quic-conn`
  fuzz, §11.29; `9f7e2419`). **NULL pointer arithmetic** in `wt_write()` for a FIN-only entry (found by UBSan, §11.29; `721dfd64`).
- **Child messages**: the fixed char arrays of MSG_INTRO and MSG_STAGE read from the child socket had no final zero (`d80a4244`),
  found by the `child-msg` fuzz (`7ea65b2d`, with `benches/unit/child-credentials`, `8d2a4f5e`).
- **Clipboard on KDE**: a zero byte cut the text and the fallback read past the copy (§11.6; `8031958d`).
- **Small fixes of the manual's table** (§11.6): retired RX codes no longer raised, BENCH_MARK out of the installed binary,
  journal lines no longer doubled, FAREWELL reason 0x10 accepted (`84fdf573`).
- **Fuzz harnesses now in the repository**: `quic-conn`, `rcp-msg` (`a63cd356`, `fd02e3a4`), `child-msg`; the rcp-msg runs are still to do (§11.52 D).

## 4. Requirements that changed (§11.51, recorded 21 Oct 2026)
- Maximum resolution **3K** instead of the 4K that 1.0 aimed at (the user: «la 1.0 prevedeva il 4K, ma ho abbassato i requisiti»).
- **At most 8 users** per machine, or the highest number that still works well.
- Unchanged: REMOTIX stays IPv4-only as a goal (§11.5: «leviamolo. IPv6 diverra' importante fra 30 anni»). The code only treats an IPv6
  peer address correctly in the ban key and in the connection caps (§1.9-bis closed, §11.53, §11.40).

## 5. Still open
- **A/B 30-perf against 1.0** and the complete functional suite on the integrated branch: running now, no result yet (§11.6, §11.9, §11.40).
- **Android F-031** (Chrome on the emulator: `keyboard_close` refocuses after `hide()`): to be tested on the phone (the emulator could not confirm it); the proposed fix
  is in `PIANO.md`, not in this range.
- **F-011 cure (c)**: verified 8/8 on gnome and xfce, Chrome and Firefox; **kde and lxqt still due** (§11.41, `9c770c61`).
- **Live checks due**: Stateless Reset with real Chrome and Firefox (§11.9); caps 16/4/8 with 01-b10, 3 runs of 9 (§11.40); migration on a
  real network change (§11.29); F-014E on the integrated branch (KDE box); `pacing-ab --dopo integrazione` (the +1 ms RTT cured by `ppoll`); the login ban on the boxes (§11.53); the 30-minute fuzz on the integrated branch
  and the stream-churn bench (§11.52).
- **Not in this tree (abandoned attempt; see «READ FIRST» at the top of `docs/1.5/DECISIONS-11.md`)** — being ported on `port-pagina` /
  `port-rcp`: §11.4 (the 1.0 `terminate-user` is still there), §11.29 LXQt repair, §11.39 `0x0E`, §11.43 30-minute clock,
  §11.44 page TCP listener, §11.48 320×240 probe, rpm `%ghost` of `quic-secret`. **Still to port**: §11.32 `PACE`, §11.36 Firefox
  worker, §11.37 and §11.38 render nodes, §11.45 encoder padding, §11.47 `refusal_uncounted`, §11.50 root-side split, and from
  §11.33 the KDE «unchanged» filter, nested KWin size, `remotix-capture` name, key receipts.
- **Declared limits**: Retry and INVALID_TOKEN have no per-second cap (CPU only, §11.9); `handshake_timeout` stays at ngtcp2's default
  (§11.52); a live IPv6 test with a real provider is not possible on the test server (unit tests and 01-b10 in a namespace, §1.9-bis note).
