# REMOTIX 1.5 — release notes (draft, 25 Oct 2026)

> ⭐ This file describes the branch `finale` = `integrazione2` (`a4b9cb1f`) + `pktinfo` + `rootside-completo` (the split, OFF by default) + `rifiniture` (CSP and decoder correction) + `doc-chiusura`. `ff-worker` (§11.36) is NOT in it: it waits for the user's decision D2. Sections 5-7 say what is inside and what is not.
> Range of `integrazione2`: `git log 5cf8ca10..a4b9cb1f` (`finale` adds the merges of section 6: `git log a4b9cb1f..finale`) (package 1b, audit, login defences, and the ports from the abandoned
> attempt: sessions, packages, RCP, page, card, KDE, misc) over package 1 (`git log 04f6aa18..5cf8ca10`). Every line cites a commit or a
> section of `docs/1.5/DECISIONS-11.md` (written «§11.x»).
> ⚠ Status words are those of the sections: «built», «under verification», «approved, verification in progress». State of 25 Oct 2026:
> `integrazione2` builds (BENCH and product) and passes `verifica-rami` 28/28 (`4be3a981`); the functional suite on Intel gave 692 PASS
> (the 12 FAIL were the F-027 test, rewritten since: `c2766ea1`, `8a7f5247`), the A/B against 1.0 is green on fps and delay with
> two open points (see «Still open»). Fixes written after that run are on the branches listed in section 6 and are NOT in this range.

## Contents
1. What is new for the user
2. Behaviour changes (login ban, page headers, clipboard, picture, connection)
3. Defects of 1.0 fixed (security and robustness)
4. Requirements that changed
5. Still open
6. Fixes of 25 Oct 2026 merged in `finale` (not in `integrazione2`)
7. What is OFF by default
8. Upgrading from 1.0

## 1. What is new for the user
- **A flood of fake connections no longer costs the server a connection each.** The first packet of every connection must
  come back with a token (QUIC Retry), and a client that talks to a restarted server is told at once to start again
  (Stateless Reset) instead of waiting ~30 s (§11.9, under verification; `51e3634a`, `f79d1d18`). Price: one extra round trip when a
  connection opens. It stops forged source addresses, not attacks from real addresses nor a saturated line (§11.9).
- **The server cannot be filled before login.** Caps: 256 connections, 128 not yet logged in, and at most 8 not-yet-logged-in
  connections per IPv4 address or IPv6 /64, 32 per /48; when the server is full the oldest not-yet-logged-in connection is closed, never one that is
  being checked or logged in; 90 s without login closes the connection (§11.40, under verification; `ffea98a1`, `75ba1f93`).
- **Changing network keeps the session** (e.g. Wi-Fi to mobile): the packet path follows the one the datagram came on
  and a validated move updates the connection (§11.29, RCP.md §2.3, under verification; `fa7eac00`, `f606542e`, `eb8d9db2`). Declared limit (QUIC's anti-amplification rule): until
  the new path is validated the server may send up to 3× what it received from it; the ban and the logs keep the birth
  address. Not yet measured on a real network change.
- **The last row of the picture has the right colour on Chrome** (it was tinted, e.g. green on GNOME): cure (c), the page
  trims the last row when the decoded frame has coded rows below the visible ones (§11.41, verified on gnome, xfce, kde and lxqt, Chrome and Firefox, 25 Oct 2026; `571c8145`, `9b963d77`,
  earlier steps `78b63549`, `127f69a6`). Cost: the last visible row of pixels of the picture repeats the row above it.
- **Installer and uninstaller**: the install plan states the port before «Proceed? [y/N]» (`29a4a7ce`); the uninstall removes
  what upgrades added (§11.6, under verification; `84fdf573`, `b4f0776e`). (Separately, and not a 1.5 change: the project site now offers the 1.0.0 download instead of «Coming soon», `b2f8161e`.)
- **`/diary` is gone** from the installed product and from test builds (§11.10, under verification; `8a46c9c9`, `9af7b82e`).
- **ACTIVE by default, even with the split OFF (§11.50 D3/D4b, from `rootside-completo`)**: the PAM dispatcher is **re-executed** (`/proc/self/exe --pam-helper`, a fresh memory image, `src/helper.c:170-187`)
  and **restarted by the watchdog** `helper_expired()` with a pause that doubles from 1 s to 60 s (loud after 5 deaths in a row). **The synchronous PAM fallback is gone**: with the helper down, or no helper object,
  the login is refused with `0x0E`, not counted (`src/main.c:2985`). The single-process product keeps `helper_turn_on()` and `HelperVerdict` (`src/helper.h:153-160`: `admitted` and `lost`): a PAM check that gets no answer within 8 s (the helper's own limit; the server waits at most 12 s for any verdict)
  **counts** as a failed attempt; the death of the dispatcher with the request in flight, or a limit of ours, arrives as `lost` and **does not count** towards the ban.
  The five outcomes of `HelperOutcome` (1 admitted, 0 refused, 2 refused while `pam_faillock` held the account, 3 not checked and not counted, 4 expired in 8 s and counted: `src/helper.h:183-193`) are the form used ONLY with the split on (`helper_turn_on_root()`).

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
  `unknown user [a1b2c3]`. Lines in the 1.0 format (`address expiry`) that have not expired are read and become a ban at the top step (the time left, at most 12 h); expired ones are dropped. `UNBLOCK <address>` clears every level.
- The page's ban notice and the `0x08` text follow the rule, without a number of attempts (`546fe91c`); manuals and specs updated
  (`47eba75e`, `2cc1b424`, `be61b885`, `798a00a0`). Tests: `benches/unit/login-ban` (`8db14aaa`, `a9c48435`), B8 (`f3733e77`).

### Page headers and checks (page audit)
- The HTML response carries a Content-Security-Policy, `Referrer-Policy: no-referrer` and a Permissions-Policy
  (clipboard for the page itself only) (`65e78f14`). `connect-src` is `'self'` (it was `'self' https:`); still open by choice: `unsafe-inline` (`4324ba93`).
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
- **8 users** per machine is the tested target (the highest number that still works well on the test hardware), not a rule of the server: its administrative ceiling stays at 10 sessions (`--session-cap N` changes it) and the real limit is the pixel budget, which refuses with `0x06` before the desktop is born. A ninth user is not refused by a rule of 8.
- Unchanged: REMOTIX stays IPv4-only as a goal (§11.5: «leviamolo. IPv6 diverra' importante fra 30 anni»). The code only treats an IPv6
  peer address correctly in the ban key and in the connection caps (§1.9-bis closed, §11.53, §11.40).

## 5. Still open
State of 25 Oct 2026. Queued runs are those of the evening chains (`coda-giorno3`, `coda-sera4`); none has a result yet unless said.
- **Done and measured on `integrazione2`**: build and 28 unit/bench verifications (`4be3a981`); functional suite Intel (692 PASS; the F-027
  test now follows the new login rules and is queued again on Chrome and Firefox); A/B 30-perf against 1.0 (fps and delay equal; memory
  better on Chrome; **xfce+firefox: RED in memory vs 1.0 (5 steps); analysis: a fixed box-memory offset, `srv_rss` and `ses_rss` equal to 1.0 (`/media/REMOTIX-15/tmp/rq-mem.py`); two more runs queued to confirm**);
  F-011 cure (c) on the four desktops with Chrome and Firefox; F-014E: PASS 2/2 on `pacchetto1b` (`322468ea`, now in `integrazione2`); to be re-run on the final branch; `pacing-ab` RTT at rest +5.8 % (limit 15 %).
- **Queued, not yet run**: F-027/F-028/N-1 on four desktops with Chrome and Firefox; A/B gnome+chrome (one run showed CPU +9.5 % at
  4 users and +14.8 % at 6: two more runs) and xfce+firefox (two more runs); `stream-churn` and `pam-tempi` on `finale`;
  fuzz `rcp-msg` and `child-msg` (900 s each); `verifica-rami` and B10 (caps 16/4/8) on `finale` (which holds `pktinfo`, `rootside-completo` and `rifiniture`);
  the «text» scene for 1.0 (8-user check); the 1.0 measures on the Radeon; `pacing-ab` bulk/burst/loss and the live migration, whose test
  clients were fixed on 25 Oct (the ATTACH layout, QUIC PING instead of raw bytes).
- **Not provable on the test server, due by hand or on other machines**: Stateless Reset with real Chrome and Firefox (§11.9); a real
  network change Wi-Fi → mobile (§11.29); the card changes on real AMD, Intel and two-card machines (§11.4, §11.37); the page defences with
  real browsers (§11.44). KDE with 8 users on the Radeon is **not measurable on this bench** (server RAM: ~1.1-1.2 GB per user for the
  KDE box plus ~1.5-2 GB for the test Firefox, which in use runs on the user's own device): declared, not measured.
- **Open outside this range**: Android F-031 (Chrome on the emulator: `keyboard_close` refocuses after `hide()`; the fix is in
  `PIANO.md` and on `f031-a-p1b`, to be tested on the phone) and NVIDIA (a rented server, `PIANO.md`): both excluded from this release's closing.
- **Three decisions of the user** (opinions collected from Argon, gpt-oss and Laguna in `tmp/dom5.txt`, none taken): **D1** the root-side
  split ON or OFF in 1.5 (§11.50); **D2** the Firefox worker as default (§11.36); **D3** decoder `PACE` ON by default (§11.32). Without
  a decision the release is the safe one: D1 OFF, D2 `ff-worker` not merged (it is not in `finale`), D3 OFF (section 7).
- **In `finale` (merged, to be measured)**: branch `rifiniture`: `connect-src` of the CSP narrowed to `'self'` (it was `'self' https:` in `page.c`; the WebTransport behaviour on Chrome
  and Firefox is still to be measured), and the correction of the decoder in `page.html` (`7e49f5b1`, from `b1dea604`): a keyframe rebuilds a decoder that an error closed, also at the
  same size (before, the picture stayed frozen for the rest of the session). **Not in `finale`**: branch `ff-worker` (approved on reading; the live proof is still to do), the port of §11.36 D, the worker route as default **only on desktop Firefox**, with
  automatic fallback to the main-thread route; merged only if the user chooses D2 = A.
- **Not done, optional**: the
  zero-byte test moved before the UTF-8 check also in `clipboard.c` for GNOME (behaviour correct, only the log line); a uniform delay for
  login refusals (`pam-tempi` on 1.0: a denied user answers in ~1.1 s, other refusals in ~2.0-2.2 s: a design choice, §11.53); the constant
  `RCP_SESSION_CAP` 10 in `src/rcp.h:94` is the configurable administrative ceiling (`--session-cap`); the maximum of 8 of §4 is the test target (decided 25 Oct 2026: the ceiling stays at 10).
- **Declared limits**: Retry and INVALID_TOKEN have no per-second cap (CPU only, §11.9); `handshake_timeout` stays at ngtcp2's default
  (§11.52); a live IPv6 test with a real provider is not possible on the test server (unit tests and 01-b10 in a namespace, §1.9-bis note).

## 6. Fixes of 25 Oct 2026 merged in `finale` (not in `integrazione2`)
These are approved and are **not** in the range above; `finale` has them, merged in this order: `pktinfo`, `rootside-completo`, `rifiniture`, `doc-chiusura`. Each has its queue run listed in section 5 (`coda-finale.txt` runs them on `finale`).
- **Branch `pktinfo` (head `8760f5bc`, approved; merged in `finale`; the `errno` after the fallback and `ENODEV` are corrected on it, and its fallback log line follows the `quic-conn` fuzz oracle):
  replies leave from the address the client wrote to** (`IP_PKTINFO` / `IPV6_PKTINFO`). The UDP socket is bound to the wildcard and every
  reply was a plain `sendto()`, so the kernel chose the source address; on a host with several addresses (global + ULA + temporary IPv6, or
  multi-homed IPv4) the reply may come from another address, a QUIC client does not accept it and the handshake never completes. **A defect
  of 1.0 as well** (`read_packet` used `c->local` as the path's local address, `transport.c` ~1547): found by the `quic-conn` fuzz on 24 Oct and
  seen by B10 (`c-48`: 0 of 3 rounds green on `integrazione2`, the /48 cap never reached). The stateless replies use the arrival address only while
  the datagram is handled and fall back without the source when the kernel refuses it (`5601b8e3`).
- **Branch `rootside-completo` (head `ae8cae45`; also `026f15d1` (Arch installer) and `82e87313` / `ae8cae45` (`quic-conn` fuzz harness); approved; merged in `finale`)**: besides the split (section 7, OFF by default), two corrections of today, and fixes of the `quic-conn` fuzz harness after the review.
  - The `quic-conn` fuzz harness (`1a25d20a`): an unlogged connection logged in through `transport_verdict()` before `op_wt` gave it a post-credentials
    state, a state the product cannot be in since the synchronous PAM fallback is gone (D4b); the age close then hit a «logged-in»
    connection and the oracle aborted (`verifica-rami`, replay rc=77, crash-5e4ce06f). Harness only, identical in both trees; `integrazione2`
    still logs in from `transport_expired()`, so the same input passes there.
  - Arch packaging (`d09a6738`, manual ch17 `32eb4667`): `post_remove` removed `/var/lib/remotix/net` whatever `remotix-net-move --back`
    had achieved, losing the files a half-done `--back` had refused to move. `net_back()` now writes the marker `/run/remotix/back-incomplete`
    when `--back` fails or leaves `certificates/`, `ban` or `ban.new` in `net/`; `post_remove` then keeps `net/` and says so. Test `benches/02-arch-install-back.sh`.
- **Merge order, done in `finale`**: `pktinfo` first (small; it also repairs a defect of 1.0), then `rootside-completo` (one conflict in `src/transport.c`, in
  `transport_open_fd()`: the family and `bound_any` now come from the socket's own `getsockname`, as the split needs), then `rifiniture`, then `doc-chiusura`
  (conflict in `DECISIONS-11.md`, the status paragraph: the one of `doc-chiusura` kept, then rewritten for `finale`). `verifica-rami` and the runs of section 5 are to be done on `finale`.
  `ff-worker` is **not** merged. `integrazione2` itself is not touched.
- Already in `integrazione2` since the 24 Oct run: `61ea9a6c` (the 429 for a second session counted as chatter), `879cf5fa` (a name clash of `rcp_logged_in`),
  `549a9e06` (the product build declared five capabilities in HERE_I_AM and wrote four), `0b4d3bda`/`4be3a981` (tests of the six failing units),
  `c2766ea1`/`8a7f5247` (F-027 rewritten to the new ban rules), `a4b9cb1f` (test client `--rebind` with QUIC PING).

## 7. What is OFF by default
- **Root-side / network-side split (§11.50)**: written, reviewed, packaged (service user `remotix`, installer, distro packages, SELinux, seccomp,
  `remotix-net-move --back` with its Arch marker), in `finale` (from `rootside-completo`); the server stays ONE process unless `REMOTIX_SPLIT_EXPERIMENTAL=1`,
  and `--split` without it is refused (the server logs why and exits with 78).
  **Build switches of the packages (all OFF unless asked)**: Debian: `REMOTIX_SPLIT=1` (`packaging/debian/rules:30`, passed by `src/build-targets/build-deb.sh`); Arch: `REMOTIX_SPLIT=1`
  (`packaging/arch/build.sh`); rpm: `--with split` (`%bcond_with split`, `packaging/rpm/remotix.spec:37-39`) or `RX_SPLIT=1` for `build-rpm.sh`; any other value leaves the pieces OFF.
  **Inert without the switch**: the system user `remotix` (sysusers), `remotix-net-move`, the `*.split` units and tmpfiles, the rpm SELinux domain, the Arch install script, and their guards in `postinst` / `%post` / `remotix.install`.
  **Would change today's behaviour, therefore behind the switch**: creating the user, moving `certificates/` and `ban` into `/var/lib/remotix/net`, the units' `--certificates` / `--ban-file`, `/var/lib/remotix` 0755.
  Measured on the discarded attempt (16 Oct; `benches/24-privsep-cost.sh`, run 20261016-113915); not re-measured on `rootside-completo`. Cost against 1.0 (4 interleaved rounds, one box): login to first frame −98 ms warm /
  −145 ms cold (a separate timing change), desktop birth +6 ms (noise), motion 61.5 fps both, idle CPU 0.00-0.07 %. Needs decision D1.
- **Decoder `PACE` (§11.32)**: present (`4895f2ad`, `c7bfef17`), enabled with `--decoder-pace`; the page declares `video.pace` only then. The measures
  of the first attempt favoured ON (slow decoder: 26 → 61 photos/min on Firefox 4K), but the default is a change seen by the browser. Needs decision D3.
- **Firefox worker as default (§11.36)**: written on the branch `ff-worker` (default on desktop Firefox only, fallback to the main-thread route; Chrome and Android
  unchanged), approved on reading, live proof still to do, NOT merged. It enters 1.5 only if the user chooses D2 = A.

## 8. Upgrading from 1.0
What an administrator will notice, most likely first. Everything here is in the sections above; this is the short list.
- **Login ban.** The 1.0 rule (3 failures, address out for 12 h) is gone. 5 wrong passwords of one user from one address in 5 min block that user on that address; 12 failures from one address in 5 min block the address; 30 from one IPv6 /48 in 10 min block the /48. Blocks last 15 min, then 1 h, then 12 h, and are forgotten after 24 h without a ban. Everyone behind one NAT shares an address: twelve wrong passwords from different people block them all. The page tells a blocked visitor that the attempts are used up, without a number.
- **Lifting a ban.** The packaged service does not pass `--command-socket` (the unit calls it a bench option, as in 1.0), so `UNBLOCK <address>` is not available on an installed server; a ban ends by itself.
- **Ban file and logs.** The file keeps its path and mode (0600) but the format is new (names stored as HMAC-SHA256, never in clear). Unexpired 1.0 lines are read. Going back to 1.0, the new lines are silently ignored (verified in `rcp_ban_load()` of 1.0): bans in force at that moment are lost, nothing breaks. Unknown users appear in the log as `unknown user [a1b2c3]` and the failed-attempt line has a new form: rules written for 1.0 (grep, fail2ban) must be updated.
- **Login refused with `0x0E`.** The synchronous PAM fallback is gone. If the password-checking helper is down, the login is refused with `0x0E`, and it does not count towards the ban. The helper restarts by itself (pauses of 1 s up to 60 s); if it does not, restart the service and read the log.
- **Connections.** A new connection costs one more round trip (QUIC Retry). Before login the server is capped: 256 connections, 128 not logged in, 8 per address, 32 per /48; 90 s without login close the connection. Replies leave from the address the client wrote to.
- **Page.** It is served with a Content-Security-Policy (`connect-src 'self'`), `no-referrer` and a restrictive Permissions-Policy; `/diary` is gone. Behind a reverse proxy the page and the WebTransport connection must stay on the same origin.
- **Sessions.** A first login no longer closes the user's other sessions (`9167f2f4`); the 30-minute inactivity clock counts only the five user gestures (`806ff0bf`); a user is enrolled only in the group of the render nodes (`/dev/dri/renderD*`, `8205fe12`), no longer in other card groups.
- **Limits.** 3K at most (not 4K); 8 users is the tested target, the configurable ceiling is 10.
- **Options.** New: `--max-connections`, `--max-pending`, `--max-pending-per-address`, `--max-pending-per-48`, `--render-node`, `--decoder-pace`, and the split options (`--split`, `--network-user`, `--network-run-dir`, `--network-state-dir`). None of the 1.0 options was removed.
- **Installer and packages.** The plan states the port before the question; the codes `RX-H264-003`, `RX-H264-004` and `RX-FW-004` are retired and no longer raised (`RX-H264-002` and `RX-FW-002` instead); zlib is a new dependency (the page is compressed).
- **Encoder padding.** `REMOTIX_VPP_PADDING=0` in the server's environment switches off the VPP padding strips of the encoder (`src/encoder.c:3206`; for an A/B on a box); by default they are on, and if the driver refuses them once the frame is redone without them.
- **Unchanged by default.** The root/network split, decoder `PACE` and the Firefox worker are OFF: no new system user, no moved files, no new unit. The SELinux policy of the split (`remotix.te.split`) has not been measured yet.
