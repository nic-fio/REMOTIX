# REMOTIX 1.5 — release notes (draft, 25 Oct 2026)

> ⭐ This file describes the branch `finale` = `integrazione2` (`a4b9cb1f`) + `pktinfo` + `rootside-completo` (the split, OFF by default) + `rifiniture` (CSP and decoder correction) + `doc-chiusura`. **`finale-ff` = this branch + `ff-worker` (§11.36): ff-worker merged (D2 = A)**; in `finale` it is not (it waits for D2). Sections 5-7 say what is inside and what is not.
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
- The attempt table is sized for 160 bans of its 256 entries (`BAN_QUOTA`), and a new ban never drops another one (a first version did: a botnet of ~54 addresses made its own bans fall after ~90 s, recidivism included). While the 160 are in force the unknown keys share a counter of 5 failures in 5 min, beyond it they are refused with `0x08`; keys that logged in in the last 30 days always get in (they are written in the ban file, as `G2 <real epoch of the login> <key or its HMAC>` lines that the 1.0 skips, so a restart does not forget them and never rejuvenates them; a line dated in the future is read as recent with its date brought back to now, and the newer date wins if a key is in the file twice), and the counter also counts the attempts in flight and is zeroed by `UNBLOCK`. A table filled with bans no longer refuses every login (audit R1; `14b12ab4`).

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
- **The RATE of new handshakes is limited** (audit R4, 25 Oct 2026, branch `handshake-ritmo`): the connection caps bound how many are open, not how fast they come, so one address could make
  hundreds of handshakes a second (0.3-1.2 ms of the single thread each). After the Retry token is verified and before `accept_conn()`, three token buckets (`src/hsrate.h`): 4 a second per address
  (IPv4 or IPv6 /64, burst 16), 16 a second per IPv6 /48 (burst 32), 200 a second for all (burst 32). Over the limit the newcomer gets the stateless `CONNECTION_REFUSED` (the address is proved by
  the token, so no amplification: the browser fails at once, and the USER has to press the button again — the page does not retry by itself) and the token is not used up; one line per 10 s counts them (`⚠ HANDSHAKE RATE`). The tables are fixed (256 + 128 entries, least recently seen evicted). Test `benches/unit/hs-rate`. The `quic-conn` fuzz harness ignores the refusals for rate in its caps oracle and RAISES the limits in op 14 (flood) and in op 12 (a4 bit 0), so the branch of the early-forgotten Retry tokens stays covered; `01-b10-flood.py` has `--flood-gap` (B10_FLOOD_GAP) because its default worker pause (0.2-0.5 s) is faster than 4 births a second per address.
- **The page's accept buckets cannot be filled from one IPv6 allocation** (audit R-5, 25 Oct 2026, branch `pagina-secchio`): the page listener's accept rate is kept per IPv4 address / IPv6 /64 and per /48 (256 buckets each);
  an attacker with rotating addresses of ONE large allocation (a /32 holds 65536 /48s) could keep all of them busy and push every new address, the legitimate visitors, onto the one shared overflow bucket, which his further
  keys drained: `503 busy` for everybody (only the login page; QUIC and the open sessions are not touched). Now at most 32 BUSY buckets of one IPv6 /32 per table (`src/pagebucket.h`, `PAGE_KEYS_PER_32`); the rest of that /32 shares the overflow bucket.
  The shared overflow bucket is also one per family (IPv4 / IPv6), so a flood of one cannot use up the overflow of the other's visitors. Declared limit: 8 different /32s still fill the table. Test `benches/unit/page-bucket`.
- **One address cannot use up the Stateless Resets** (audit R9, 25 Oct 2026, branch `reset-per-indirizzo`): the cap of 100 Stateless Resets a second was for everybody, so one address sending short packets for unknown connection ids
  took it all, and the clients that had really lost their connection (a restarted server) got no Reset and waited out their 30 s of idle time. Now one address (IPv4, or IPv6 /64) may have 5 of the 100 in a second (`src/resetcap.h`),
  and the ones it is refused do not count against the others; one line per second says so. Declared limit: about 20 addresses at 5 a second still use up the global cap. Test `benches/unit/reset-cap`.
- **The Stateless Resets cannot be used up by forged ids** (audit R9, 25 Oct 2026, branch `cid-firmati`, on top of the per-address cap above): the Connection IDs the server issues (the first one, the Retry's, every NEW_CONNECTION_ID)
  are now 10 random bytes + 8 of HMAC-SHA256 under a key derived from the static `quic-secret` (`src/cid.c`). A short packet whose destination id carries a valid tag gets its Reset from the 100 a second; one that does not, from 10
  a second of its own, so a flood of random ids (from any number of forged addresses, which the per-address cap does not see) cannot take the Resets away from the ids this server issued. Not dropped: a client of the 1.0 holds
  unsigned ids whose Reset token is still valid, and it gets it, at most 10 a second, while the server is upgraded. The tag and the Reset token come from the same secret: an id issued before a restart still verifies after it.
  The search of the id map is skipped for an id that does not verify. Cost: one HMAC (~170 ns) per received packet. Test `benches/unit/cid-firmati`; the fuzz `quic-conn` has the new oracles (and its harness now sets `bound_any`).
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
- **WebTransport capsule parser quadratic, before any login** (R2 of the network audit; `43fdc3f1`): every capsule on the CONNECT stream moved the whole rest of the buffer down, so a client without credentials sending 2-byte capsules cost the server about L²/4 bytes of `memmove` per chunk of L bytes (360 KB for a 1.2 KB packet, 16.8 MB for an 8 KB one) with its credit widened by every byte it sent — a way to stall the single-threaded server. Now one read index and one compaction per call: linear. Test `benches/unit/capsule-parser`.
- **Child messages**: the fixed char arrays of MSG_INTRO and MSG_STAGE read from the child socket had no final zero (`d80a4244`),
  found by the `child-msg` fuzz (`7ea65b2d`, with `benches/unit/child-credentials`, `8d2a4f5e`).
- **Clipboard on KDE**: a zero byte cut the text and the fallback read past the copy (§11.6; `8031958d`).
- **Small fixes of the manual's table** (§11.6): retired RX codes no longer raised, BENCH_MARK out of the installed binary,
  journal lines no longer doubled, FAREWELL reason 0x10 accepted (`84fdf573`).
- **The user name in the PAM refusal lines** (audit R3, 25 Oct 2026, branch `log-nome`): `why_no()` wrote the raw name the client typed on stderr, so a password typed in the user
  field stayed in clear in the journal and control characters went through without `log.c`'s cleaning. Now a user of the machine is named (control bytes → `?`, 64 bytes at most) and
  anything else is `unknown user [a1b2c3]`, the same HMAC tag as the other login lines (the server computes it and hands it to the PAM helper in the request; no tag → `??????`).
  Test `benches/unit/auth-log`.
- **The card grant could call a group private without having seen all of it** (audit R-4, 25 Oct 2026, branch `gruppo-privato`): `group_is_private()` read `/etc/group` and
  `/etc/passwd` with a 4096-byte `fgets`, so the members of a long group line after the first 4095 bytes (and a later account with the same gid behind a long line) were never seen.
  Lines are now read whole with `getline()` (up to 1 MiB). NOT private: a line that is too long, with a zero byte inside, with too few fields, any `+` line (NIS compat: other accounts with the gid
  cannot be excluded), or a read error; skipped: blank lines, `#` lines and `-name` lines. NSS (`getgrgid_r`, `getpwent`) was weighed and not added:
  the code runs in the parent as root and must not block on sssd/LDAP, and enumeration is off by default so it would prove nothing; a gid absent from `/etc/group` stays refused.
  Test `benches/unit/render-grant`, checks 41-57 (35-40 are the package removal).
- **A stranger could fill the journal before any login** (audit R8 and R12, 25 Oct 2026, branch `log-tetti`): the line `packet … NOT sent` of `send_from()` had no limit (one source flooding Initials against a full
  socket buffer wrote one line per failed reply, at the packet rate), and the pre-login budgets of `webtransport.c` are per address (20 lines every 10 s for each of 128 addresses): whoever has many addresses, or
  rotates an IPv6 /48, gets a fresh budget for each. Both now also go through a GLOBAL budget per 10 s window (`src/linebudget.h`, the idea of `BIRTH_LINES`): 5 `NOT sent` lines and 100 pre-login lines for the whole
  server, the rest counted in one line at the end of the window (with the last error for the first). The «BANNED» and «failed attempt» lines are exempt as before. Tests `benches/unit/line-budget` and `wt-prelogin` (7).
- **The service can always stop** (audit of the session, 25 Oct 2026, branch `chiusure-figli`): `children_turn_off()` waited for every child with `waitpid(pid, NULL, 0)`, without a limit, after the SIGTERM; one child stuck in a call
  that does not return kept the whole service from stopping until systemd's own timeout killed everything. Now SIGTERM, 1.5 s, SIGKILL, 1 s more (`src/reapwait.h`); a child still not reaped is said in the log and left to init.
  Test `benches/unit/reap-wait`.
- **A child that no longer answers is found** (audit of the session, 25 Oct 2026, branch `chiusure-figli`): a child that had introduced itself had no deadline at all (invariant I4: the stage outlives the detach, and an idle child is doing its job), so one
  stuck in a call that does not return stayed for ever, with its slot and its session. The parent already asks every child «who are you» once a minute; if that question stays unanswered for 600 s and the child has sent
  NOTHING else since, it is killed (SIGKILL; the desktop survives and is found again). A child that does not answer but still delivers messages is not killed: one line says so and the wait starts again. Test `benches/unit/child-flood` (12).
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
  a decision the release is the safe one: D1 OFF, D2 `ff-worker` merged only in `finale-ff` (D2 = A; it is not in `finale`), D3 OFF (section 7).
- **In `finale` (merged, to be measured)**: branch `rifiniture`: `connect-src` of the CSP narrowed to `'self'` (it was `'self' https:` in `page.c`; the WebTransport behaviour on Chrome
  and Firefox is still to be measured), and the correction of the decoder in `page.html` (`7e49f5b1`, from `b1dea604`): a keyframe rebuilds a decoder that an error closed, also at the
  same size (before, the picture stayed frozen for the rest of the session). **`ff-worker` merged (D2 = A) in `finale-ff` only**: the port of §11.36 D, the worker route as default **only on desktop Firefox**, with
  automatic fallback to the main-thread route (its `4c9c78ee` is the same decoder fix as `7e49f5b1`: one copy in `page.html`); approved on reading, the live proof in a browser is still to do.
- **Not done, optional**: the
  zero-byte test moved before the UTF-8 check also in `clipboard.c` for GNOME (behaviour correct, only the log line); a uniform delay for
  login refusals (`pam-tempi` on 1.0: a denied user answers in ~1.1 s, other refusals in ~2.0-2.2 s: a design choice, §11.53); the constant
  `RCP_SESSION_CAP` 10 in `src/rcp.h:94` is the configurable administrative ceiling (`--session-cap`); the maximum of 8 of §4 is the test target (decided 25 Oct 2026: the ceiling stays at 10).
- **Declared limits**: with about 50 addresses at 4 handshakes a second each, an attacker uses up the global bucket (200 a second) and the NEW logins are refused for as long as it lasts (in IPv6 about 13 /48s are enough: 13 × 16 a second);  the sessions already open are not touched. Retry and INVALID_TOKEN have no per-second cap (CPU only, §11.9); `handshake_timeout` stays at ngtcp2's default
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
  `ff-worker` is merged in `finale-ff` (D2 = A) and **not** in `finale`. `integrazione2` itself is not touched.
- Already in `integrazione2` since the 24 Oct run: `61ea9a6c` (the 429 for a second session counted as chatter), `879cf5fa` (a name clash of `rcp_logged_in`),
  `549a9e06` (the product build declared five capabilities in HERE_I_AM and wrote four), `0b4d3bda`/`4be3a981` (tests of the six failing units),
  `c2766ea1`/`8a7f5247` (F-027 rewritten to the new ban rules), `a4b9cb1f` (test client `--rebind` with QUIC PING).
- TLS key-exchange groups restricted to X25519MLKEM768, X25519, P-256, P-384 (`src/tls.c`, both the QUIC and the TCP context; audit R4). Present since 1.0: no group was set, so a client could offer only `ffdhe3072` and make each handshake cost about 6 ms of CPU instead of 1.2. Needs a try with Chrome, Firefox and Android before it is merged.

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
- **Firefox worker as default (§11.36)**: **ff-worker merged (D2 = A)** in the branch `finale-ff` (default on desktop Firefox only, fallback to the main-thread route; Chrome and Android
  unchanged); approved on reading, live proof still to do. In `finale` it is NOT merged: it enters 1.5 only with D2 = A, i.e. with `finale-ff`.

## 8. Upgrading from 1.0
What an administrator will notice, most likely first. Everything here is in the sections above; this is the short list.
- **Login ban.** The 1.0 rule (3 failures, address out for 12 h) is gone. 5 wrong passwords of one user from one address in 5 min block that user on that address; 12 failures from one address in 5 min block the address; 30 from one IPv6 /48 in 10 min block the /48. Blocks last 15 min, then 1 h, then 12 h, and are forgotten after 24 h without a ban. Everyone behind one NAT shares an address: twelve wrong passwords from different people block them all. The page tells a blocked visitor that the attempts are used up, without a number.
- **Lifting a ban.** The packaged service does not pass `--command-socket` (the unit calls it a bench option, as in 1.0), so `UNBLOCK <address>` is not available on an installed server; a ban ends by itself.
- **Ban file that is a link or belongs to a stranger.** `rcp_ban_load()` opens the file without following links and only if it is a regular file of root or of the uid the server runs as, in a directory not writable by everybody: a symbolic link, a foreign owner or such a directory now stops the start, like an unreadable file (the log gives the owner and mode); the `0644` file the 1.0 wrote is still read.
- **Ban file and logs.** The file keeps its path and mode (0600) but the format is new (names stored as HMAC-SHA256, never in clear). Unexpired 1.0 lines are read. Going back to 1.0, the new lines are silently ignored (verified in `rcp_ban_load()` of 1.0): bans in force at that moment are lost, nothing breaks. Unknown users appear in the log as `unknown user [a1b2c3]` and the failed-attempt line has a new form: rules written for 1.0 (grep, fail2ban) must be updated.
- **Login refused with `0x0E`.** The synchronous PAM fallback is gone. If the password-checking helper is down, the login is refused with `0x0E`, and it does not count towards the ban. The helper restarts by itself (pauses of 1 s up to 60 s); if it does not, restart the service and read the log.
- **Connections.** A new connection costs one more round trip (QUIC Retry). Before login the server is capped: 256 connections, 128 not logged in, 8 per address, 32 per /48; 90 s without login close the connection. Replies leave from the address the client wrote to.
- **Page.** It is served with a Content-Security-Policy (`connect-src 'self'`), `no-referrer` and a restrictive Permissions-Policy; `/diary` is gone. Behind a reverse proxy the page and the WebTransport connection must stay on the same origin.
- **Sessions.** A first login no longer closes the user's other sessions (`9167f2f4`); the 30-minute inactivity clock counts only the five user gestures (`806ff0bf`); a user is enrolled only in the group of the render nodes (`/dev/dri/renderD*`, `8205fe12`), no longer in other card groups.
- **Limits.** 3K at most (not 4K); 8 users is the tested target, the configurable ceiling is 10.
- **Options.** New: `--max-connections`, `--max-pending`, `--max-pending-per-address`, `--max-pending-per-48`, `--render-node`, `--decoder-pace`, and the split options (`--split`, `--network-user`, `--network-run-dir`, `--network-state-dir`). None of the 1.0 options was removed.
- **Installer and packages.** The plan states the port before the question; the codes `RX-H264-003`, `RX-H264-004` and `RX-FW-004` are retired and no longer raised (`RX-H264-002` and `RX-FW-002` instead); zlib is a new dependency (the page is compressed).
- **Encoder padding.** `REMOTIX_VPP_PADDING=0` in the server's environment switches off the VPP padding strips of the encoder (`src/encoder.c:3206`; for an A/B on a box); by default they are on, and if the driver refuses them once the frame is redone without them.
- **Unchanged by default.** The root/network split and decoder `PACE` are OFF (the Firefox worker is the default on desktop Firefox in this branch, `finale-ff`: D2 = A): no new system user, no moved files, no new unit. The SELinux policy of the split (`remotix.te.split`) has not been measured yet.
