# DECISIONS §11 — from the first 1.5 attempt (copied 21 Oct 2026 from the archive, tag `1.5-scartata` + `441d6db4`)

> Reference only: the decisions and the list of 1.5 points. The code they mention is NOT in this repository.

## 0. ⚠ READ FIRST — this file comes from the abandoned attempt (status of 25 Oct 2026)

This file was copied from the discarded first attempt (tag `1.5-scartata`) and then extended. The review of 24 Oct 2026 found
that it cites **117 commit hashes that are not in this tree** (`git cat-file -e` fails), and that many items marked ✅ / DONE
describe code that exists only in the abandoned attempt. Every such entry carried a line starting with «⚠ NOT in this
tree». Status of 25 Oct 2026, after the ports:
- **Ported and merged into `integrazione2`** (the markers of these sections now say so; the hashes they cite are still those of the
  abandoned attempt, the ports have their own): §11.4 (no more `terminate-user`; `port-sessioni`), §11.29 LXQt repair, §11.39 `0x0E`,
  §11.43 the 30-minute clock, §11.47 `refusal_uncounted` (`port-rcp`), §11.44 the page's TCP listener, §11.48 the 320×240 probe
  (`port-pagina`), §11.33 rpm `%ghost` (`port-pacchetti`), §11.32 `PACE` (OFF by default), §11.45 encoder padding, §11.33 key receipts
  (`port-varie`), §11.37 / §11.38 render nodes (`port-scheda`), the KDE «unchanged» filter, the nested `remotix-capture` name and the nested
  KWin size (`port-kde`). All of them built and unit-tested there (`verifica-rami` 28/28); the live checks are listed in CHANGES-1.5.md.
- **In the branch `finale`, not in `integrazione2`**: §11.50 the root-side split (merged from `rootside-completo`, OFF by default behind
  `REMOTIX_SPLIT_EXPERIMENTAL=1`; it still waits for the user's decision D1), `pktinfo` (replies leave from the address the client wrote to), and `rifiniture` (CSP `connect-src 'self'`; the decoder rebuilt by a keyframe after an error).
- **In neither**: §11.36 the Firefox worker (written on the branch `ff-worker`, approved on reading with the live proof still to do, merged only if the user chooses D2 = A).
What IS in the code is listed in `CHANGES-1.5.md` and in §11.6, §11.9, §11.29 (migration part), §11.40, §11.41, §11.51-§11.53.
An entry without the marker may still cite hashes of the discarded attempt; read the hash against `git log` before trusting it.

## 11. ✅ From 1.0 to 1.5: the review of two external documents — 12 Oct 2026

The user's word: *«prima del masterplan ho trovato del lavoro da fare per portare remotix dalla versione 1.0 alla
versione 1.5»*. The two documents (a security report and a 20-phase plan, written outside the project from the
public documentation only, without reading the code) were read against the code and the Technical Manual: most of
their findings restate the manual's own §14.13 (known limits) and §23.1 (open defects). Their licence constraint does
not apply (the user is the Author). What follows is what the user decided on each point, the same evening.

### 11.1 ✅ Authentication is Linux's job, and stays so

- **The ruling** (verbatim): *«eliminiamo il discorso dell'autenticazione: questo e' compito di Linux, e oggi remotix
  si limita a "consumare" il servizio (e cosi' deve rimanere)»*.
- ⇒ No MFA, no password policy, no account checks of our own, no «rate limit per identity»: PAM decides, REMOTIX
  respects the verdict. The manual's §14.13 row «Password-only authentication, no MFA — deferred» is no longer
  deferred: it is **out by principle**.
- Not touched by this: wiping the password copy with `explicit_bzero` (§11.6) and binding a reattach to the UID —
  they concern how REMOTIX handles what it receives, not who decides.

### 11.2 ✅ The address ban stays as in 1.0; unlocking goes to the MASTERPLAN

- **The ruling** (verbatim): *«anche il ban su IP lo eliminiamo. Capisco la criticita' per chi risiede dietro un NAT,
  ma la momento soluzioni che non richiedano mesi di sviluppo non ne vedo»*; then *«lo sblocco degli indirizzi
  bloccati lo mettiamo nel masterplan, ad oggi remotix non ha strumenti di gestione: una volta installato funzione
  come servizio di sistema»*.
- ⇒ The ban is not redesigned (the NAT price of §14.13 stays declared). The missing unlock socket in the packaged
  units becomes `MASTERPLAN.md` **M8**.

### 11.3 ✅ Certificates stay as they are

- **The ruling** (verbatim): *«eliminiamo questa parte dallo sviluppo e lasciamo per il momento l'attuale
  funzionamento»*.
- ⇒ No certbot guide, no reload of the page certificate without restart, no change to the first-connection
  warning. An administrator can already drop a real certificate in `/var/lib/remotix/certificates` (§1.7).

### 11.4 ✅ The first enrolment in the card groups must stop closing the user's other sessions

> ⚠ Ported (25 Oct 2026): the enrolment code of the first attempt («`loginctl terminate-user` is gone», `src/render_grant.c`) is merged into `integrazione2` from `port-sessioni` (`6349f4f2`); `child.c` no longer calls `terminate-user`. verification 28/28 on `4be3a981`, 24 Oct 2026; the live check with real browsers is still due (CHANGES-1.5.md, «Still open»).

- **The ruling** (verbatim): *«Il punto 2 mi sembra che vada contro le specifiche del progetto. Un utente puo' avere
  contemporaneamente un a sessione locale/remota testuale e un a sessione grafica remota»*; and *«e' quello su cui
  bisogna intervenire, pero' prima e' da approfondire»*.
- **Why it is a defect, not a choice**: `SPECS.md` §5.1 — text and graphical sessions coexist. The
  `loginctl terminate-user` in `enroll_in_card_groups()` (`src/child.c`) closes them.
- `[M]` **12 Oct 2026, tablet CHUWI, 1.0.0-1+deb13**: new user `usertest`, SSH from the phone with `top` running;
  first REMOTIX login (Firefox 153 ESR) at 22:04:25 got in at the first attempt, `usertest` was put in `video` and
  `render`, and the SSH session was killed. Users present at installation are not hit: the installer enrols them
  with `gpasswd` and closes nothing; the defect hits users created afterwards, and users the installer cannot see
  (network accounts).
- ⇒ To be fixed in 1.5, designed knowing that the enrolment moves to the privileged side in §11.11. To be tried
  first: a per-device permission (ACL) that takes effect without restarting the user manager; together with the
  restriction to `render` alone (§10.36).
- **13 Oct 2026, the user's direction** (verbatim): *«Cerchiamo di evitare di buttare fuori gli utenti. Se non
  dovesse esistere una soluzione decideremo che strada prendere»*; the problem was discussed with ChatGPT at the
  user's request (two rounds).
- 🔸 **The state of the study** (not yet a decision):
  · the defect needs a user manager ALREADY alive (another session, or lingering); without one, `usermod` is enough;
  · for XFCE and LXQt the compositor (labwc) is started by our child with fresh groups, not by the user manager;
  · ruled out: `terminate-user` (today), restarting only `user@UID` (the SSH shell survives, but its D-Bus, audio,
    agents and user services die), a different GNOME/KDE start path for this case only, editing the `systemd-user`
    PAM stack;
  · `[M]` Debian 13, systemd 257: `renderD*` is tagged `uaccess` like `card*` (`70-uaccess.rules`) ⇒ an ACL for the
    USER can be wiped by logind (its flush removes named-user entries);
  · the strongest candidate: an ACL for the user's PRIMARY GROUP on the card nodes, for the life of the desktop —
    the stale manager carries that gid, and logind touches only named-user entries. Its open point: proving the
    group belongs to that user alone (not a shared group of network accounts); when not provable, no grant;
  · to measure first, on the four desktops: which nodes the compositor really opens (render only, card only, both),
    with `strace` from before the unit starts.
- `[M]` **13 Oct 2026, 19:10–19:20, tablet CHUWI, REMOTIX 1.0.0-1+deb13, GNOME** — the primary-group ACL WORKS:
  · new user `usertest` (uid/gid 1001, private group), user manager started with `enable-linger` + `systemctl start
    user@1001` ⇒ pid 55055, `Groups: 1001`; then `usermod -aG video,render` ⇒ `id` shows 44 and 991, the manager
    still `Groups: 1001` (the stale manager reproduced; REMOTIX finds the groups already there and closes nothing);
  · **control**, no ACL: REMOTIX login, the desktop APPEARS (terminal opened) — gnome-shell 55481 `Groups: 1001`,
    **no `/dev/dri` fd**: Mutter draws in SOFTWARE. ⚠ Not «blind» as in phase 10 §7.4 (27 Aug 2026): today the
    stale manager costs the card, not the picture;
  · logout, `setfacl -m g:usertest:rw /dev/dri/card0 /dev/dri/renderD128`, login again: gnome-shell 56451, still
    `Groups: 1001`, **six fds on `/dev/dri/renderD128`**, none on `card0`; manager still 55055 — nothing closed.
  · ⇒ For GNOME on this machine the render node alone is enough. Still to measure: KDE, XFCE, LXQt; logind's flush
    (a local seat login/logout while the ACL is in place); the exclusivity check of the primary group.
  · `[M]` and the cleanup taught one more thing: `userdel -r usertest` left `group:1001:rw-` on both nodes (the ACL
    outlives the account, by number). The next account created would likely get gid 1001 and the grant with it ⇒
    REMOTIX must remove the grant when the desktop ends, and at start-up remove any of its grants left behind (a
    crash, a power cut). Removed by hand: `setfacl -x g:1001`.
- `[M]` **13 Oct 2026, 19:35–19:45, the four boxes on the test server** (`benches/11-boxes`, images of 11 Oct,
  product dd67792, Intel card; script and outputs in `misure/2026-10-13-gpu-enrolment-chatgpt/boxes/`). Three users
  per desktop, REMOTIX login with the automatic client: **aclc** groups before the manager is born (reference),
  **acla** stale manager without ACL (the defect), **aclb** stale manager + `setfacl -m g:<primary gid>:rw` on
  `card0` and `renderD128`:

  | desktop | aclc | acla (defect) | aclb (primary-group ACL) |
  |---|---|---|---|
  | GNOME | gnome-shell on `renderD128` | born, gnome-shell no card, MEMORY route | **gnome-shell on `renderD128`**, CARD route |
  | KDE | kwin, Xwayland, plasmashell on `renderD128` | born, no card | **all on `renderD128`** |
  | XFCE | labwc on `renderD128` | **labwc on `renderD128`** (started by our child, fresh groups) | the same |
  | LXQt | labwc on `renderD128` | **labwc on `renderD128`** | the same |

  · the user manager was never restarted (same pid before and after, 12 cases out of 12); every desktop was born;
  · ⇒ the defect costs the card only on GNOME and KDE (compositor under the user manager); on XFCE and LXQt there
    is nothing to bridge; the primary-group ACL bridges GNOME and KDE; only `renderD128` is opened, never `card0`.
- ✅ **13 Oct 2026, evening — DONE in the code** (the user: *«se funziona, questa è la prima funzione di remotix 1.5»*):
  `loginctl terminate-user` is gone from `enroll_in_card_groups()`; new `src/render_grant.c`/`.h`: at every birth of
  a GNOME or KDE desktop, if the user manager is alive (its `init.scope` in `/sys/fs/cgroup`) and its credentials in
  `/proc` lack the group of a `renderD*`, and the primary group is provably private (`/etc/group`: name = user, no
  other member; `/etc/passwd`: no other account with that gid — a network account cannot prove it and gets no grant),
  an ACL `group:<gid>:rw` goes on every `renderD*`, written directly as `system.posix_acl_access` (no `setfacl`, no
  libacl), recorded in `/var/lib/remotix/render-grants`, removed when the child is reaped, swept at start-up when no
  desktop of that user is alive. An entry the administrator had put is never claimed nor removed.
  `[M]` same evening, the four boxes (product 631a1fc1 + this change, `make BENCH=1`; outputs `grant-*.txt` in
  `misure/2026-10-13-gpu-enrolment-chatgpt/boxes/`):
  · **first connection with a stale manager** (new user, not in the groups): GNOME and KDE — enrolled, grant given,
    gnome-shell / kwin and the Plasma processes on `renderD128`, manager pid unchanged; XFCE and LXQt — enrolled, no
    grant (none needed), labwc on `renderD128`, manager unchanged;
  · **shared primary group** (`useradd -g users`): no grant, the reason in the log, the desktop born in software;
  · **the desktop ends** (GNOME): child reaped, grant and record line removed;
  · **crash** (`systemctl kill -s KILL` of the server, then the desktop ends, then the server again): GNOME and KDE —
    «left by a previous run REMOVED» at start-up;
  · ⚠ KDE after a real «Log out» (`org.kde.Shutdown.logout`) with no client attached: the child stays until the user
    comes back, and the grant with it — a behaviour of the child that was already there; declared in
    `render_grant.h` as harmless and bounded (devtmpfs, the sweep).
- `[M]` **13 Oct 2026, 20:50–20:56, tablet CHUWI (systemd 257.13), logind does not touch the grant**: test user
  `aclt`, `setfacl -m g:aclt:rw /dev/dri/renderD128`; (1) `udevadm trigger --action=change` on the node (the
  `uaccess` builtin, with flush) ⇒ `group:aclt:rw-` still there; (2) the user, at the machine, Ctrl+Alt+F3, login as
  `aclt` (logind session 10 on seat0), `exit`, the GDM greeter, back to the own session — three changes of the active
  session on seat0 ⇒ `user:nicfio:rw-` rewritten by logind, `group:aclt:rw-` still there. Cleaned up.
- ✅ **The uninstaller reads `render-grants`** (13 Oct 2026): new step `remove-render-grants`
  (`installer/engine/action_render_grants.go`), in the plan only when the record has lines, after the sessions are
  closed — every recorded gid out of every `renderD*` ACL (same on-disk format as `render_grant.c`, through
  `syscall.Getxattr`/`Setxattr`: no `setfacl`), then the record; an entry of the administrator's is left alone;
  EXACT (cancelled, entries and record come back). `go test`: uninstallation removes the grant and keeps the
  administrator's entry; killed after the step and rolled back, both come back.
- ⚠ **Declared limit**: a removal through the package manager (`dnf`, `apt`, `pacman`) WITHOUT the uninstaller leaves the ACLs on `renderD*` and the record `render-grants` until the next reboot (the ACLs are on devtmpfs); the package only removes the record files. Only the uninstaller (`remove-render-grants`) takes the ACLs back at once.
- 🔸 **Ported on 24 Oct 2026** (branch `port-sessioni`, from the abandoned attempt `158e4621`, the version BEFORE the root-side split of §11.50, which this tree does not have): `src/render_grant.c`/`.h`, the three hooks in `child.c` (sweep at start-up, grant at the birth of a GNOME/KDE desktop, removal when the child is reaped) and `terminate-user` gone from `enroll_in_card_groups()`; the `grant-*.sh/.txt` benches are in `misure/2026-10-13-gpu-enrolment-chatgpt/boxes/`. **Not built, not run** on this base: the live test on the four boxes is still due.
- **Found on the way** `[M]`: Chrome 155 on the server itself fails on `https://localhost:7447` («Opening handshake
  failed»), works on `127.0.0.1` and on `192.168.0.3`, and from Windows over the Internet. The packaged units listen
  on IPv4 only (`--address 0.0.0.0`) and Chrome tries `::1` for `localhost`. ⇒ §11.5.

### 11.5 ✅ No IPv6

- **The ruling** (verbatim): *«leviamolo. IPv6 diverra' importante fra 30 anni»*.
- ⇒ REMOTIX stays IPv4-only; not in 1.5, not in the MASTERPLAN. The `localhost` case of §11.4 is accepted.

### 11.6 🔸 The small fixes of the manual's open-defects table go in — done in package 1, under verification (24 Oct 2026)

- **The ruling** (verbatim): *«blocco 1 ok»*.
- ⇒ Retired RX codes no longer raised; BENCH_MARK out of the installed binary (`RCP.md` §7.5); journal lines no
  longer doubled; `explicit_bzero` for the password copy (R9.20); FAREWELL reason 0x10 accepted from the client; stale
  comments of §23.2; the uninstallation removes what upgrades added.
- ✅ **Done 13 Oct 2026 in the first attempt** (discarded, tag `1.5-scartata`; not committed there). Two choices made on the way: the test build is `make BENCH=1`
  (`-DREMOTIX_BENCH`; the packages build without it, and the installed binary has no `BENCH_MARK`, `bench.mark` or
  `/diary` string — checked with `strings`); `WT_FLOOR_BYTE_MS` (the transport's guess before its first measurement)
  goes from the old 20 Mbit/s floor to the decided 30 (§3.1-sexies). `explicit_bzero` also wipes the buffers freed
  after carrying the password or the clipboard, not only the password copy.
- 🔸 **In this tree (package 1, branch `pacchetto1`, 24 Oct 2026)** — the commit «Small fixes (section 11.6):
  explicit_bzero on password and clipboard, BENCH_MARK under BENCH, cancel updates in uninstall.go (+2 Go tests)»
  (`src/rcp.c` and its twin in `benches/rcp/`, `installer/engine/uninstall.go`, the packaging files, the Go tests), then
  «installer: gofmt texts.go» (formatting only). Done, `[M]`, in a copy made with `git archive`:
  · normal build and `BENCH=1`: both compile, the same two warnings as `d32ef7a1` (`vulkanvideo.c:354`, `:379`), none new;
  · `strings` on the normal binary: no `/diary`, no `bench.mark`; the only hit of `BENCH_MARK` is the symbol name
    `T_BENCH_MARK` of the type constant (the binary is not stripped; stripped: none of the three); on the `BENCH=1`
    binary: no `/diary`, `bench.mark` present;
  · Go: `go vet` and `go test ./...` of the installer pass, the two new tests (`TestUninstallUpgradeGroupOnce`,
    `TestUninstallUpgradeLogUnreadable`) among them; `gofmt -l` clean.
  **To do:** the complete functional suite and the A/B 30-perf against the 1.0 (`suite-pacchetto1.sh`,
  `ab-pacchetto1.sh`), and the reading of the packaging changes by building the packages.
- 🔸 **Added 24 Oct 2026 — the KDE clipboard and a zero in the text.** In `src/clipboard_kde.c` (commit
  «clipboard_kde: a text with a zero in the middle is not announced (as clipboard.c); last_text never states more
  than the copy») a text with a zero byte in the middle is now refused and **not announced**, as `clipboard.c` does for
  GNOME (cutting it at the zero would announce a text shorter than the announcement), and `clipboard_kde_last_text()`
  never states more bytes than the copy holds (the fallback used to read past it). Done: compiles, normal and
  `BENCH=1`, no new warning. **Not yet run:** the test `nul-kde-prova.sh --installa --contrasto` on the KDE box
  (`printf 'abc\0def' | wl-copy` in the session: «with a zero in the middle — not announced» in the log, no «the session
  copied», the child alive; then a text with accents announced as before; and on the 1.0 no «not announced»).
- 🔸 **The test for it, F-014E (24 Oct 2026, branch `f014e-int`, in `pacchetto1b`)** — `benches/15-suite/15-f014e-clipboard-with-a-zero.py`
  (commits `22ea3008`, `550b1b37`, `396f7dae`): `wl-copy` runs inside the tenant's session with `printf 'abc\0def'`; pass = the
  server log says «with a zero in the middle — not announced», there is NO announcement line «the session copied N bytes of
  text» (waiting the whole 10 s window, so a late one is seen), the tenant's child process is the same and alive, and a normal
  text with accents copied right after IS announced with its exact length. The rejections that also start with «the session
  copied …» (not text, no readable type) do not count as announcements. **KDE only**, through a new optional declaration
  `DESKTOPS = ("kde",)` in the test file, read by `15-round.py` like `FUNCTIONS`: on the other desktops the test is NOT launched,
  it is not in the exit code and its cell in the report stays «·». The other tests do not change. `15-report.py` has the
  F-014E name. Checked: `--certify` offline (15 cases), `py_compile`, `15-round.py --list` («· only kde»). **Not yet run** on the
  KDE box (`15-round.py --desktop kde --tests f014e`).
- ✅ **The order of the checks (24 Oct 2026)** — commits `322468ea` (`clipboard_kde.c`) and `d8f48441` (`clipboard.c`, GNOME).
  `g_utf8_validate_len()` **already rejects a zero**, so the `memchr` of `8031958d` placed after it was **unreachable**: the text
  was refused either way, but the log blamed «not valid UTF-8» instead of the zero. The `memchr` now runs **before** the UTF-8
  test, on both desktops; behaviour is unchanged, the log names the real cause, which is what F-014E reads, and `explicit_bzero`
  runs on both paths. **Verified: F-014E PASS 2/2 on KDE.** GNOME compiled (normal and `BENCH=1`), not run.

### 11.7 ✅ Derivative distributions: the parent picks the package, the desktop decides

- **The ruling** (verbatim): *«secondo me affidarsi solo al nome della distribuzione introduce un elemento di
  debolezza, ad esempio una distro potrebbe chiamarsi mint e avere wayland»*; then *«questa al momento mi sembra
  l'unica strada possibile»*.
- ⇒ `installer/engine/archive.go` uses the catalogue's existing `derivatives` mapping to choose the package (the
  parent named by `/etc/os-release`); whether REMOTIX installs is decided by the existing desktop checks
  (RX-MANCA-001/003), never by the name. The plan states «derivative of …, not tested directly».
- ✅ **Done 13 Oct 2026.** `installer/engine/archive.go`: `TargetIn(catalogue, machine)` — a derivative found by
  the catalogue takes its parent's folder of the `.run` (Linux Mint 23 → `ubuntu2604`); `/etc/os-release` alone
  (`Target`, the old hand-written cases) stays only for a machine the catalogue does not know. The plan declares,
  before the question, «this machine is X, a derivative of Y … not tested on it directly — whether it installs is
  decided by the desktop checks, not by the name». `go test`: twelve `os-release` cases (Mint, Manjaro, EndeavourOS,
  Rocky, RHEL and the platforms themselves); a full plan on a fake Mint 23 takes `ubuntu2604` and declares it — with
  the old code the same test fails with «no packages for linuxmint23» (RX-MANCA-004), the defect a Mint user would
  have met.

### 11.8 ✅ «Wayland only», prominent on the website

- **The ruling** (verbatim): *«sulla homepage di remotix bisognerebbe rendere molto evidente il "Wayland-only" dl
  prodotto»*; then *«il wayland-only mi sembra la strada migliore: semplice, essenziale ed efficace. Alrimenti c'e'
  sempre la manualistica»*.
- ⇒ One line near the title: **Wayland only** · GNOME 46+ · KDE Plasma 6.1+ · XFCE 4.20+ · LXQt 2.0+ (the minimums
  of `installer/catalog/catalog.json`). Nothing about local X11 sessions: the details stay in the manuals.
- ✅ **Done 13 Oct 2026** in `design/site-mockup/index.html` (not yet republished on remotix.nicfio.it).

### 11.9 🔸 Address validation (QUIC Retry) and Stateless Reset go in — under verification (24 Oct 2026)

- **The ruling** (verbatim): *«non ho capito molto, ma se mi assicuri che aiuta a prevenire glli attacchi DoS ok»*.
- ⚠ **The degree of certainty**: decided on an assurance given in the discussion, with its limit stated — it stops
  floods with forged source addresses, not attacks from real addresses nor a saturated line. The cost: one round
  trip at the opening of each connection.
- ⇒ The two declared gaps in `src/transport.c` («No address validation with Retry», «DECLARED FALLBACK» for the
  Stateless Reset) are closed. The Reset also shortens the 30 s a client waits after a server restart.
- ✅ **Done 13 Oct 2026 in the first attempt** (discarded, tag `1.5-scartata`; the same design was rebuilt on 1.5 from
  `d32ef7a1` — `src/transport.c`, `transport.h`, `main.c`): an Initial without our token gets a Retry
  (`ngtcp2_crypto_generate_retry_token2`, 10 s validity) and no connection; with it, the token is verified and
  `original_dcid`/`retry_scid` go in the transport parameters; an old token or one for another address gets
  INVALID_TOKEN, an unreadable one is ignored. A short-header packet for an unknown dcid gets a Stateless Reset (token
  from the static secret and the dcid, one byte shorter than what arrived, at most 100 per second). The static secret
  is kept in `<certificates>/quic-secret` (0600), so a reset after a restart carries the token the client already
  knows; if it cannot be read or written, the secret of the run stays and it is declared. The client's own dcid is
  now bound to its connection too, so an Initial sent again before our answer does not open a second connection.
  `[M]` same evening, GNOME box, product with this change:
  · bench client (aioquic 1.2.0): «Retry sent», «address validated with a Retry», session born; ⚠ aioquic stores the
    reset tokens but never checks an incoming reset, so it cannot judge the Reset (it waited its 30 s);
  · **Chrome** on the tablet → `https://192.168.0.2:8511`: in through the Retry; server killed (`systemctl kill -s
    KILL`) and started again: the first packet of Chrome (14 s later, at the first mouse move) got ONE reset and
    Chrome sent nothing more — the page said «the connection to the server was interrupted» at once. With the first
    version of the code (minimum length counted wrong: 41 bytes) Chrome's 39-byte packets got no answer and Chrome
    kept sending for seconds — corrected and measured again;
  · **Firefox** on the tablet: in through the Retry.
  ⚠ These `[M]` are of the discarded attempt: they are NOT a proof of the code now in the tree.
- 🔸 **Under verification (24 Oct 2026)** — the rebuilt code, on top of package 1, not yet on the main line.
  Done, `[M]`:
  · clean build, normal and `BENCH=1`: the same two warnings as `d32ef7a1` (`vulkanvideo.c:354`, `:379`), none new;
  · isolated test, private podman container on `127.0.0.1:7547` (no box, no desktop), aioquic 1.2.0 client:
    «Initial without a token: Retry sent», «address validated with a Retry», «WebTransport session ACCEPTED»;
  · `quic-secret`: 0600, 32 bytes, owner = the server's user; on restart it is read again (same sha256, same mtime),
    and its hex never appears in the log;
  · contrast, `d32ef7a1` on the same test: the session is born, no Retry, no `quic-secret`.
  To do: the Stateless Reset with real Chrome and Firefox (`reset-prova.py`: kill -9 and restart with the same
  certificates; pass = the page notices in < 5 s, against ~30 s without the Reset); the complete suite; the A/B
  against the build without the change.
- ⚠ **Limit declared and accepted by the user on 24 Oct 2026:** Retry and INVALID_TOKEN have **no cap per second**
  (only the Stateless Reset has: 100 per second). Reason: they keep **no memory** (the token is a signed
  statement, nothing is stored until the address is proved) and give **no amplification** (the answer is much
  smaller than the Initial, which is at least 1200 bytes); the only cost is the CPU of the server for each forged
  Initial. A flood of forged Initials therefore still costs CPU, as before; what Retry removes is the connection
  state it used to create.
- *Minor notes of the security review (24 Oct 2026), not fixed:*
  · in the «token not readable» branch of `read_packet` (`transport.c`) `ngtcp2_strerror(rv)` receives a code of the
    crypto part (-201/-202, not an ngtcp2 one) and prints a generic text; it only matters for the log (only with
    `--verbose`). The possible cure: write by hand «unreadable» / «internal error» according to the code;
  · **two instances on the same certificates folder** (not a supported setup) both read and write
    `quic-secret`: if it does not exist yet each makes its own and the last `rename` wins, so the other keeps a
    different secret in memory until its next restart and its Retry tokens and Stateless Reset tokens will not
    be recognised by the first.

### 11.10 🔸 `/diary` leaves the installed product — done in package 1, under verification (24 Oct 2026)

- **The ruling** (verbatim): *«non so' per quale motivo ma diary mida' l'idea di remotix che entra nel pc
  dell'utente»*; then *«via diary»*.
- **Why**: besides being unauthenticated and without a rate limit (§14.13), the page sends a measurement line every
  5 s per connected client (`src/page.html`, the `setInterval` at line 7549) — some 720 lines an hour per user,
  including whether the window has focus: telemetry the user never asked for, and on a company server a record of
  who is looking at the screen.
- ⇒ Kept only in bench/laboratory builds, like the bench messages of §11.6. *(Superseded on 22 Oct 2026 by the user's decision below: removed entirely, bench builds included.)*
- ✅ **Done 13 Oct 2026 in the first attempt** (discarded, tag `1.5-scartata`): `/diary` existed only with
  `make BENCH=1`; the page sent nothing unless the server marked it `data-diary="yes"`.
- ✅ **Decisione dell'utente del 22 ott 2026: eliminato del tutto, anche dalle build bench (nessun banco lo usa); resta
  la riga locale nel #logbook** (it is in `PIANO.md`, section of package 1). It goes further than the line above.
- 🔸 **In this tree (package 1, 24 Oct 2026)** — the commit «Remove /diary entirely (even from BENCH builds); keep the
  local line in the page #logbook» (`src/page.c`, `src/page.html`, `src/Makefile`) takes the endpoint, the 5-second
  measurement line and the `data-diary` marker out of **every** build, bench builds included; the page keeps its own
  local line in `#logbook` (nothing leaves the browser). Done, `[M]`: normal and `BENCH=1` builds compile with no new
  warning; `strings` of both binaries: no `/diary`. **To do:** the suite and the A/B.

### 11.11 ✅ The last phase of 1.5: a service user for the network side

- **The ruling** (verbatim): *«veramente in un messaggio passatio avevo lanciato l'idea di creare un utenza di
  servizio per rmotix»*; then *«si, la mettiamo come ultima fase, anzi, questa andra' divisa in sotofasi perche'
  sara' parecchio lunga tra sviluppo e test»*.
- **Why not systemd's restrictions alone**: the desktops are born inside the service and inherit every restriction
  (a read-only `/usr` for the service is a `sudo apt install` that fails in the remote desktop).
- ⇒ The part that faces the network runs as an unprivileged `remotix` user; a small root side, reachable only from
  it through a closed list of requests, does PAM (the helper of §1.10 moves under it), the birth of the desktops and
  the card-group enrolment. The desktops are born from the root side, so the network side can then be restricted
  freely. Sub-phases to be fixed when it starts (inventory of root operations; the user and its files, packaging and
  the SELinux module; the root side; the desktops' birth; dropping the powers; the full matrix and the upgrade from
  1.0).

### 11.12 ✅ The clipboard is not touched

- **The ruling** (verbatim): *«no, il copia incolla non si tocca. L'ho limitato solo al testo proprip er aumentare la
  sicurezza»*.
- ⇒ No administrator switch, no lower limit: the report's point on the clipboard is closed.

### 11.13 ✅ Fuzzing before the last phase; only the missing tests; no global pre-login limits

- **The ruling**: *«si»*, to the question: fuzzing in 1.5 before §11.11, the missing hard-case tests only, the
  global limits for those not yet logged in dropped.
- ⇒ Coverage-guided fuzzing of the RCP and HTTP parsers (a crash is a denial of service with one message; a memory
  error, before login and as root, is remote code execution — the reason to do it while the network side still has
  every power). Tests added only where the suite lacks them: the server crashing with a session open, two logins at
  the same instant, a few interruptions of the installer.

### 11.14 ✅ The manuals are rebuilt from scratch just before the release

- **The ruling** (verbatim): *«i manuali si ricostruiscono da zero subito prima del rilascio e rileggendo il
  codice»*.
- ⇒ No manual is touched during the development of 1.5; the decisions are written here, one entry each, as they are
  taken, so that the rebuilt manual can say *why* and not only *what*. As for 1.0, rereading the code to write the
  manual is also a review.

### 11.15 ✅ One test runner, divided in sections

- **The ruling** (verbatim): *«i test con un solo comando mi fa' venire alla mente una vera e propria app di
  testing»*; then *«Oppure, ancora meglio, una app divisa in "sezioni"?»* and *«si, mi sembra u idea migliore.
  Organizzazione migliore e separazione funzionale»*.
- ⇒ For 1.5: one runner over the existing benches, organised in sections that run alone or all together — Build,
  Protocol (RCP and fuzzing), Functional (F001–F026 per desktop), Stress (`benches/16-stress`), GPU (the encoders per
  card), Installer (`benches/17-distro`, the VMs) — ending in an HTML report per section, built from the
  `outcomes.jsonl` files the benches already write, with the comparison against the previous run.
- **The shape** (verbatim): *«test [sezione][patametri della sezione]»* — one command, the section, then that
  section's own parameters. 🔸 Not named `test`: that name is the shell's built-in.
- 🔸 A control panel on top of it (choose where to run, follow it live, browse the history) is not in 1.5; the
  runner must not close that road.

### 11.16 ✅ REMOTIX is exposed to the Internet

- **The ruling** (13 Oct 2026): the declared scenario is no longer «own server, own network or VPN» (`SPECS.md` §4.1)
  but a server reachable from the Internet. The user's view: fuzzing (§11.13) and address validation (§11.9)
  are the answer for 1.5.
- ⇒ `SPECS.md` §4.1 rewritten on the same day. Unchanged, and now declared for that scenario: the certificate the
  server makes itself and the click of the first connection (§11.3), the address ban (§11.2).
- **Volumetric floods (a saturated line) are out of REMOTIX's scope** (13 Oct 2026). No program on the server can stop
  traffic that fills the line before reaching it. The user's own defence, for the intended use: *«ho una difesa che i
  siti commerciali non hanno: l'IP pubblico variabile, mi basta spegnere e accendere il router»* — to be written in
  the manual with its limits (a dynamic DNS name follows the new address; the provider may give the same address
  back after a short power-off; whoever connects must learn the new address). And the boundary, verbatim: *«al
  momento remotix è relegato ad un uso personale/familiare/amatoriale. Se mai dovesse capitare il colpo di fortuna
  che un'azienda volesse acquistare il progetto allora dovrebbe pagare cloudflare per difendere il proprio servizio:
  a ciascuno il suo mestiere»*. Note for that day: the free tier of such services covers web traffic, not REMOTIX's
  UDP/WebTransport.

### 11.17 ✅ Password guessing from many addresses: Linux's own lock, `pam_faillock`

- **The question**: the ban counts per address (§1.9); three tries from each of many addresses get around it.
- **The ruling** (verbatim): *«Utilizziamo gli strumenti offerti da linux»*. Consistent with §11.1: authentication
  is Linux's job, and the global pre-login limit stays dropped (§11.13).
- ⇒ **No code change.** The `remotix` PAM file of every distribution already goes through the system's stack
  (`common-auth`, `password-auth`, `system-remote-login`), so an account lock the administrator turns on there
  holds for REMOTIX too — counted per user, whatever the address. Arch has it on by default (`system-auth`);
  Fedora/Alma: `authselect enable-feature with-faillock`; openSUSE: `pam-config --add --faillock`; Debian/Ubuntu:
  two lines in `common-auth`.
- ⚠ **Its price, to be said in the manual**: the lock is on the account, not on the attacker — whoever knows a user
  name can lock that person out (of REMOTIX and of every service using the same stack) for the lock's duration.
  It is the administrator's choice, not REMOTIX's.
- ⇒ The manual (rebuilt before the release, §11.14) gets the how-to per distribution and this price.

### 11.18 ✅ The bandwidth guess before the first measurement stays at 30 Mbit/s

- **The ruling** (verbatim): *«30 Mbit/s sono ok»* — the change made on the way in §11.6 (`WT_FLOOR_BYTE_MS` from
  20 to 30 Mbit/s, aligned with §3.1-sexies) is confirmed.

### 11.19 ✅ Housekeeping before the 1.5 work (13 Oct 2026)

- **The ruling** (verbatim): *«Questa mi sembra un opera di pulizia che si puo' fare anche adesso»*.
- ⇒ `MASTERPLAN.md`: two entries were both numbered M7 (11 Oct 2026); the later one, the «factory», is now **M9**
  (the first free number; no number reused, rule 3), and §10.46 points to it.
- ⇒ The SHA-256 of the released file is written in `README.md` too, not only in the `.sha256` beside the file on the
  site: a value from a second place is what makes the check worth something.
- ⇒ A private channel for security problems: `SECURITY.md` (shown by GitHub on the repository page), mail to
  **remotix@nicfio.it**; `README.md` and `CONTRIBUTING.md` point to it instead of sending everyone to public issues.
- ⇒ `THIRD-PARTY-LICENSES` checked against the tree: ngtcp2 1.25.0, nghttp3 1.18.0, labwc 0.8.4, 17 Go modules — it
  matches. ⚠ To redo at release time, since 1.5 may change versions.

### 11.20 ✅ The runner's sections, and fuzzing as a section of its own (14 Oct 2026)

- **The ruling** (verbatim): *«La suite per i test di sicurezza e' divisa in sezioni […] possiamo dare ad ogni agente
  il compito di costruire la sua sezione. Al termine ti occuperai di fare il "merge"»*, and the question *«Il fuzzing
  lo facciamo entrare come sezione della suite?»*.
- ✅ Fuzzing is a **section of its own** (`fuzz`), not part of `protocol` as §11.15 said — confirmed (verbatim):
  *«rendi fuzz una sezione della suite»*. The protocol checks last minutes and answer yes/no; fuzzing runs for hours on a build of its own (sanitizers)
  and finds things by chance — together they would make `protocol` slow and its outcome unpredictable.
- ⇒ Seven sections: `build`, `protocol`, `fuzz`, `functional`, `stress`, `gpu`, `installer`, plus `net` (the phase-11
  safety net). The missing tests of §11.13 go to `protocol` (server crash with a session open, two logins at the same
  instant) and to `installer` (its interruptions).
- 🔸 The command is called `rxtest` for now (`benches/runner/rxtest`; `test` is the shell's built-in): the name is
  the user's to choose. The contract of a section is `benches/runner/CONTRACT.md`.

### 11.21 ✅ The test server's integrated card is a UHD 770, not a UHD 730 (14 Oct 2026)

- **The finding**: two agents building `rxtest` (gpu, stress) read the server's card independently as PCI
  `8086:4680`, which is the **UHD Graphics 770**; the iHD driver names it «UHD 770» too, and it is the card Intel
  fits to the i5-13500T. `[M]` 14 Oct 2026: `192.168.0.2` → `i5-13500T`, `renderD128` = `0x4680`. The tablet
  (CHUWI, Intel N100) has a third one, `8086:46d1` «UHD Graphics» (Alder Lake-N).
- **The ruling** (verbatim): *«procedi alla correzione»*.
- ⇒ «UHD 730» replaced by «UHD 770» in SPECS, PHASES, DECISIONS, the phases, the benches' comments, `memoria/` and
  `design/`. The code and the manual's sources already said 770 (corrected during the English migration,
  `english-migration/residui.md`); the translation records in `english-migration/strings/` are left as they were.
  ⚠ Only the NAME was wrong: every number was measured on this server, and stays valid.

### 11.22 ✅ Where the suite runs, and the server that must not fall (14 Oct 2026)

- **The ruling** (verbatim): *«1) Il tablet non e' in grado di sostenere elevati carichi di lavoro. Quindi e' da
  valutare l'opportunita' di svolgere i test sul server - 2) I container possono cedere (e se cedono ne registriamo
  cause e misure), il server no. Questo significa che va' evitato di far collassare il server altrimenti la suite si
  interrompe»*.
- ⇒ The tablet launches and reads reports; every test runs on the server (already `CONTRACT.md` rule 6, now rule 11).
- ⇒ A container (box, VM, fuzz job) collapsing is a RESULT: it is recorded with its cause and measurements. The
  server collapsing is a FAILURE OF THE SUITE and must be prevented: heavy work runs with limits, and long loads watch
  the host. `[M]` 14 Oct 2026: the boxes run with **no memory limit** (`podman ps` shows none), and the server also
  hosts another project's service (port 8080) and tests (a Firefox from `/media/firefox-prove`).
- ✅ **The floor** (verbatim): *«con 6 gb di memoria il server dovrebbe ancora essere in grado di funzionare, ok per 4
  core»* ⇒ the suite never takes the last **6 GB** of memory nor **4 of the 20 threads**. A section whose load reaches
  the floor stops it and records where and with which numbers.
- ✅ **The light client** (verbatim): *«si, il client puo' funzionare per svolgere operazioni leggere»* ⇒ the tablet
  (or the phone) may be a real remote client — one browser session at a time, nothing else heavy — for the tests that
  only make sense from outside.
- ✅ **No `/etc/hosts` line for `NIC-OS` on the server** (15 Oct 2026, decisione dell'utente: NO). The server's own
  name is only in the router's DNS; when that DNS failed for ~1 min (09:25–09:26 UTC, a DHCP renewal) sudo warned
  «unable to resolve host NIC-OS» and kde-round's rounds refused to start. The bench copes instead: it drops
  sudo's name warnings (`b5ebfc6d`) and waits for the network before a round, a round that never started being
  said and done again (`28780933`). The server's files are not touched for it.

### 11.23 ✅ On the test server the benches user runs podman as root without a password (14 Oct 2026)

- **The need**: T10 (`benches/17-distro/17-t10.sh`) runs as the browsers user and its boxes call `sudo -n podman`
  (found by the agent building `rxtest installer`).
- **The ruling** (verbatim): *«permesso concesso»*.
- ⇒ `src/provision.sh` §4-bis adds `/usr/bin/podman` to the benches' passwordless rule. ⛔ Said plainly: this is
  root in practice (a container can mount `/`) — acceptable only on the test server, whose only user is its owner.
  It lives in the rootfs in RAM and is rewritten by `provision.sh` after every reboot.

### 11.24 ✅ How the suite runs in parallel: three levels, lanes by shared resource (14 Oct 2026)

- **The ruling** (verbatim): *«voglio ridurre allo stretto necessario le ore dedicate ai test, allo sviluppo e alle
  verifiche»*, then *«scegli tu il metodo migliore per parallelizzare i lavori»*.
- **The rule that decides**: sections run together unless they share one of these — the four rete11 boxes (one
  section per box), the one host screen of the real browsers (C21–C23 queue on its lock), a PERFORMANCE measurement
  (stress full: alone, or its numbers are false), and the floor of §11.22 (6 GB, 4 threads). The four desktops always
  run together inside a section (`[M]` C14: same outcome alone and together; net `all` 2 h 28 min instead of ~10 h).
- ⇒ **Every change** (~5–10 min), all together: `build`, `gpu`, `protocol`, `net --family works`.
- ⇒ **Before closing a phase** (~2.5–3 h), three lanes together: boxes (`net all`, then `functional`, the four desktops
  in parallel in each), installer (`installer --level short`, one bounded box at a time), CPU (`fuzz`, 4 jobs).
- ⇒ **Before a release**, at night: `stress --level full` alone; `installer --level full` two boxes at a time.
- 🔸 Two conditions before trusting it: a memory limit on the rete11 boxes too (today they have none), and one measured
  run proving `net` and `functional` together give the same outcome as alone. And the overlap between `net` and
  `functional` (C2/F-001, C4/F-007, C17/F-014, C21/F-005, C22/F-006, C23/F-008) is to be listed and pruned — the
  pruning is the user's to decide.

### 11.25 ✅ No PAM failure delay; the card drivers are the administrator's, the packages recommend none (14 Oct 2026)

Two answers of the user to the first «end of phase» lanes (`rxtest protocol`, `rxtest installer`), verbatim:
*«1) nodelay - 2) l'admin deve preparare l'ambiente»*.

- **nodelay.** `[M]` B8: PAM's failure delay (pam_unix / pam_faildelay, ~2 s) came on top of the fixed second of
  §4.4-bis, so a wrong password was told apart from a right one by the time alone. ⇒ `authentication.c` gives PAM
  its own `PAM_FAIL_DELAY` function, which does not sleep: the effect of `nodelay` on every module, ⭐ without
  editing the stacks REMOTIX mirrors (D3, §10.18). The only delay left is REMOTIX's fixed second, equal for yes and no.
  Brute force stays held by the ban file (§4.4-bis) and by `pam_faillock` where the administrator has it.
- **The card drivers.** `[M]` the installer lane: `Recommends: va-driver-all | va-driver` was satisfied on Ubuntu
  26.04 by Mesa and no Intel driver came; Tumbleweed boxes have recommends off; Arch brings nothing. The install
  then failed late in 7a (RX-AZIONE-003) and rolled back. ⇒ Consistent with §10.36: the .deb and the .rpm recommend
  **no** card driver (VA-API or Vulkan; Arch's `optdepends` stay, they install nothing), and `check` says when an
  Intel card has no Intel VA driver (RX-H264-002, RX-GPU-006) instead of finding out in 7a. The bench's
  administrator (`17-administrator.sh`) installs them on every family.

### 11.26 ✅ The net skips the six meshes the functional suite already covers (15 Oct 2026)

- **The ruling** (verbatim), on the overlap list of §11.24: *«si, elimina i doppioni»*.
- ⇒ `benches/11-boxes/11-hook.sh` skips C2 (F-001), C4 (F-007), C17 (F-014), C21 (F-005), C22 (F-006), C23 (F-008),
  each with the F- test that covers it as the reason (`f01b25ea`). `REMOTIX_NET_DUPLICATES=1` brings them back.

### 11.27 ✅ PipeWire on the test server, for the test browsers (15 Oct 2026)

- **The finding**: the server had no sound server, so Firefox's AudioContext had nowhere to play — it stayed
  suspended at time 0 and `resume()` never settled (F-012, F-013 sound, F-012B, P-D on Firefox: the F9 item).
- **The ruling** (verbatim): *«installa pure pipewire sul server»*.
- ⇒ `benches/11-boxes/server/server-ready.sh` installs PipeWire and **starts** the user units at every boot (`/home`
  is in RAM: enabling is not enough), plus wl-clipboard and python3-xlib that had been installed by hand
  (`e8c88dea`). `[M]` probe after: the context runs after the click (t = 1.49 s). Test server only; the product is
  not touched.

### 11.28 🔸 The first release-level night, and how its lanes ran (14–15 Oct 2026)

The «before a release» level of §11.24, release under test `remotix-1.4.99-2.run`.
- `[M]` **stress full** (run `20261015-005455`, alone): 263 pass, 28 fail; the floor of §11.22 held. Last level
  that holds at 4K: xfce 7 users, lxqt 5, gnome 1, kde 0. ⚠ gnome's break was the bench (profile B deleted outside
  its folder, fixed `631a33f1`); kde's is F-003 (photos 1.4 s old) and a lost key — open, to be rerun.
- `[M]` **installer full** as **two lanes at once**, the distributions split with `--distro` (lane 1: debian13
  ubuntu2604 linuxmint23 arch manjaro endeavouros leap16 → 111 pass, 1 fail, 14 blind, 44 skipped; lane 2: fedora44
  fedora43 alma10 rocky10 rhel10 tumbleweed → 60 pass, 20 blind, 46 skipped). For this, `full` with `--distro` now
  runs the whole matrix of those distributions instead of one machine (`4cc0503a`). The one fail and the 34 blind
  rows were the defects of §11.29 and §11.30; after the fixes the morning reruns of alma10 and leap16 pass T10 on
  the targets reached so far.
- ✅ **The stagger**: `[M]` 14 Oct 19:50 the first four browsers of a functional round, born together, took ~7 GB
  and the server went to 4949 MB, under the 6 GB floor. ⇒ `15-round.py` starts the desktops' queues 40 s apart
  (`1635895b`).
- ✅ **The rule**: a release build or a box image build never overlaps a lane that is starting up — `[M]` that
  overlap took the server to 3.3 GB free. Builds go before the lanes, or between them. Likewise the installer never
  runs during a functional round (the t17 boxes' ssh ports clash with the rete15 services; `17-box.sh` refuses).

### 11.29 🔸 Product defects found by the suite and fixed (14–15 Oct 2026)

- **QUIC, 14 Oct evening, from the fuzz work** (`b207ad85`, `b455f615`):
  - `webtransport.c` `wt_write()`: pointer arithmetic on NULL for a FIN-only entry (UBSan) — fixed.
  - `transport.c`, connection migration (RCP.md §2.3): the packet's real path now goes to ngtcp2 and every packet
    is sent on the path ngtcp2 wrote it for; before, a client changing network was answered on the old address
    until the silence clock. Found by reading; 🔸 not yet measured on a real network change.
  - 🔸 **State of §2.3 in branch `migrazione-su-limiti` (24 Oct 2026), under verification.** Ported: the central block
    only — the path handed to ngtcp2 is the one the datagram came on (`read_packet` / `server_new`), packets leave on
    the path ngtcp2 wrote them for (`send_on`), and `cb_path_validation` (a validated path updates `c->remote`,
    `c->local` and the provenance; a failed one leaves the traffic where it was). **NOT ported, on purpose:**
    `put_source` (the source address of the reply: `send_msg` uses `sendto` without it) and `wt_moved` / `rcp_moved`
    (`3ced6e1b`, `8758b88a` of the discarded attempt). Consequences: WebTransport and RCP stay on the **birth
    address** — the ban, `cred_address` and the RCP registers keep the address the connection was born on; after a
    move only the **registers** (the logs) show the old address, nothing is decided on a wrong one. ⚠ **Declared
    exposure:** until the new path is validated ngtcp2 may send up to **3×** what it received from that address
    (the anti-amplification limit), towards an address not yet proved.
    · Done, `[M]` (24 Oct 2026, copy made with `git archive`, low priority, no fuzz campaign): the product builds,
      normal and `BENCH=1`, with the same two warnings as before (`vulkanvideo.c:354`, `:379`); the fuzz harness
      builds; its oracles now expect **zero** `wt_moved`, and see the sends (`sendto` is routed through the
      destination checks); one more seed, a successful migration (new remote, validation OK, then a new local
      end only), passes, and so does `known/local-end-1.0.bin`; `cb_path_validation` now updates `c->local` also
      when only the local end changes (before, the «same remote» return skipped it).
    · ✅ **Corrected 24 Oct 2026:** the last seed of the migration group (a packet from a new address *during the
      handshake*) tripped the oracle «wt_sign_of_life for a packet ngtcp2 did not decrypt (§5.3)». The defect was
      in `read_packet` and already in the 1.0: the sign of life started on `rv == 0`, but ngtcp2 also returns 0 for
      a packet it discards. Now it starts only if `pkt_recv` (`ngtcp2_conn_get_conn_info`) rose. All seeds pass.
    · To do: a real network change (Wi-Fi to mobile) with Chrome and Firefox; the `quic-conn` fuzz campaign;
      the complete suite; the A/B against the build without the migration.
  - §5.3: the sign of life now needs ngtcp2's `pkt_recv` to move — an undecryptable or duplicate packet no longer
    counts (an on-path observer could keep a dead client alive and block the second device's takeover).
  - §11.9: the Retry token is handed to ngtcp2 after our Retry (no 3× limit after validation, no silent drop of a
    reordered ClientHello); a timer error other than idle closes with one CONNECTION_CLOSE (§8.1).
  - `[M]` 14 Oct, fuzz quic and quic-conn 5 min × 2 jobs clean, the grafted fault seen.
- ⚠ Ported (25 Oct 2026): the LXQt trace repair (abandoned-attempt commits `8124e05c`, `4c79c59c`) is merged into `integrazione2` from `port-rcp` (`src/session.c`). verification 28/28 on `4be3a981`, 24 Oct 2026; the live check with real browsers is still due (CHANGES-1.5.md, «Still open»).
- **LXQt black desktop after a reboot** (`8124e05c`, `src/session.c`): `[M]` T10 debian13-lxqt reboot FAIL 3/3
  with 1.0.0-1. At shutdown pcmanfm-qt dies while saving (the compositor is gone first) and leaves an empty
  `~/.config/pcmanfm-qt/lxqt/`; pcmanfm-qt 2.1.0 then skips the system profile and every later session is black.
  ⇒ Before the birth the product removes an empty folder, or gives a folder without `settings.conf` the system one;
  an existing `settings.conf` is never touched. `[M]` empty folder, folder with only recent-files, and a real
  reboot from a fresh profile: all PASS (17-t1c-look). ⚠ **Open**: the race at shutdown itself (pcmanfm-qt
  outliving the compositor) is NOT fixed; the product only cures its trace.

### 11.30 🔸 The installer's boxes: what the night found (15 Oct 2026)

- `[M]` **AlmaLinux 10's base image ships systemd-logind masked**: no PAM session, no session bus, no frame
  (t10-alma10-gnome browser FAIL). ⇒ The bench unmasks logind in every box image (`22242b33`); then alma10-gnome
  T10 passes every step. ❓ **Open, the user's**: should the installer's preflight check that logind runs? → §11.35.
- `[M]` **alma10**: the image did not build (20 blind rows): the base image's `coreutils-single` conflicts with
  `coreutils` ⇒ `--allowerasing` on the group install (`41896024`).
- `[M]` **suse**: zypper exit 107 (a post-transaction script failed, the packages are installed) was taken as a
  build failure — leap16-gnome did not build, 14 blind rows ⇒ 107 accepted (`505aafad`).
- ✅ **T10 now reboots the release under test too** (`895aafcf`, `93e5f777`): before, the only reboot ran on N (the
  previous release), so a defect fixed in N+1 — the black LXQt desktop above — could never pass, and N+1 was never
  rebooted. Now: reboot-N (documents N; a FAIL there does not stop the round), upgrade, reboot-N1, uninstall; each
  row says which release it ran on.

### 11.31 ⚠ Firefox F-013: the sound gaps are the page's main thread stalling (15 Oct 2026) — open

- `[M]` runs `20261015-051129` and `20261014-194821`, F-013 on Firefox at 4K with the video: the page's main thread
  is stalled **55–64 %** of the time, in stalls of 0.6–1.2 s about once a second (xfce too, with no audio at all);
  Chrome: no stall over 0.15 s. The audio is scheduled on that thread with a 250 ms cushion, so each longer stall
  is a gap: the 28–56 % audible is the stalls, not the ear (`03ed0e99`).
- ⇒ Diagnostic only, verdicts unchanged: the sound row reports the stalls; a red sound says whether the player
  made sound at all (`bdf91a69`); `stretches()` names the worker's route and costs with `?video=worker` (`ff0884a6`);
  `REMOTIX_15_URL_EXTRA` runs the suite with `#video=worker` (`0d30e6fa`).
- ⚠ **Open**: the diagnosis — the next run with `#video=worker` (decode and texture upload off the main thread)
  says whether the stalls are the video's drawing. No product change yet.
- `[M]` 16 Oct 2026 (B1.13, §11.36): with a slow client decoder the main-thread route stalls the main thread 44–61 %
  and fails the sound; the worker route (the default since §11.36 D) never stalls it (longest 101–112 ms) ⇒ the
  stalls are the video's work on the main thread, and the worker default is the cure already in place.
- 🔸 **In this tree (package 1, 24 Oct 2026)** — the commit «D-006: time/counts/trimmed keys and texts in
  15-d006-measure.py»: only the bench `benches/15-suite/15-d006-measure.py` (the counters' keys, `rearms`, `pulled`,
  `trimmed`, `discarded_full`, `discarded_late`, `missed`, `audible_estimate`, and its texts, in English); **no product
  change**. Done: it compiles as Python, and the names it reads (`rearms`, `pulled`, `trimmed`, `exited`,
  `discarded_full`, `discarded_late`, `missed`) are the ones `audio_counts()` of `src/page.html` writes (read in the
  code, not yet run). **To do:** one run of the bench on a Firefox box (`15-d006-measure.py`, F-013).

### 11.32 ✅ The client tells the server its decoder is behind (`PACE`) — A, measured: ON by default (15–16 Oct 2026)

> ⚠ Ported on port-varie (`4895f2ad` server, `c7bfef17` page; from `738505ff`, `d0e1fe07`) and merged into `integrazione2`; built and unit-tested there (`verifica-rami` 28/28, `4be3a981`): the `PACE` message

- `[M]` Firefox at 4K: decoder queue ≥ 5 for 80 % of the frames, decode delay median 1.35 s, while the server
  keeps sending at the full rate — nothing it can see is wrong. The page measures the queue and tells nobody.
- **The proposal** is `RCP.md` §13 (marked PROPOSED, not normative): a capability `video.pace` both sides must
  declare, and one new control message `PACE` (`0x0012`, `u16 max_fps`, 0 = no ceiling). The page sends it when
  its decoder queue stays ≥ 3 for half of the frames in a second, and lifts it step by step after 3 calm seconds.
  The server clamps (5..60), and the user's child simply encodes fewer frames — before encoding, so no frame is
  thrown away and no keyframe is owed. Only that user's session is touched; a keyframe owed is never held back.
- **Implemented, OFF by default**: the server declares `video.pace` only with `--decoder-pace` (I6). Without
  the option, nothing changes on the wire or on the screen. Server `738505ff`, page `d0e1fe07`, benches
  `583177b3`. `[M]` desk checks only: the server builds (release flags and `BENCH=1`, no new warning); fuzz
  `rcp`/`rcp-hello`/`wt`/`wt-session` run all their seeds clean, `rcp` and `wt-session` 90 s each clean; the B4
  referee gives the 7 PACE recordings the right verdict and still certifies 57/57. ⏳ **Not yet run in a
  browser or on a box.**
- ❓ **What the user decides**, three choices:
  - **A — adopt it inside RCP/1**, with one sentence added to §9: a new type is allowed only behind a
    capability both sides declare (a peer that did not declare it never sees it). Then measure Firefox 4K with
    `--decoder-pace` on/off, and if it helps, make it the default.
  - **B — keep it for RCP/2**: §12 says what is open in RCP/1 «is closed without adding message types». The
    code stays, off, and the option is removed until RCP/2.
  - **C — do not do it**: rely on the phase 9 regulator and the page's own skipping. Firefox at 4K stays
    behind.
  - Recommendation **A**: the type is invisible to any peer that did not ask for it, and the cure is the one
    the phase 9 regulator itself calls missing («carrying it as far as the child»). ⚠ Not yet measured.
- ✅ **Decided 15 Oct 2026, decisione dell'utente** — on the open decisions: *«fai quello che c'è da fare»*, i.e.
  follow the recommendation written. ⇒ **A accepted, pending the measurement**: the on/off measurement of
  Firefox 4K with `--decoder-pace` (checklist B1.14) comes first. ⛔ The default does **not** change now: the server
  declares `video.pace` only with `--decoder-pace`, as built. If the measurement shows it helps, it becomes the
  default with the §9 sentence; if not, this entry is reopened with the numbers.
- `[M]` **The measurement, B1.14** (16 Oct 2026, fixer lane): `benches/15-suite/15-f013-variants.sh`, F-013 Firefox 4K
  on the private box rxp15-xfce (:9361, never the rete11 boxes), product `main` `61488985` BENCH=1, the server with
  and without `--decoder-pace`, ≥ 3 runs each, interleaved. Medians [min–max]:

  | client browsers on | pace | runs | verdict | photos/min | longest freeze | picture age | queue ≥ 5 | NOT SENT |
  |---|---|---|---|---|---|---|---|---|
  | RX 6800 (fast) | off | 3 | 3 PASS | 60–61 | 0 s | 0 ms | 0 % | 0 |
  | RX 6800 (fast) | on | 3 | 3 PASS | 61 | 0 s | 0 ms | 0 % | 0 |
  | Intel (slow decoder downstream) | off | 3 | 3 PASS | 26 [25–27] | 0.9 [0–1.0] s | 1905 [1701–1957] ms | 65 % [61–68] | 0 |
  | Intel (slow decoder downstream) | on | 3 | 3 PASS | 61 [46–61] | 0 s | 0 [0–63] ms | 13 % [7–36] | 0 |

  The RX 6800 was 98 % busy (another agent's load) during two of the «on» runs, and nothing changed. ⇒ On a client
  that keeps up the pace never acts and costs nothing; on one that does not, it takes the backlog away (age ~1.9 s →
  ~0, photos ×2.3, no freeze) without the server dropping a frame. Evidence `/media/REMOTIX/tmp/fixer-2134b602/b113`
  (RX 6800) and `/media/REMOTIX/tmp/fixer-2134b602/b114-intel` (Intel): `runs.txt`, `table.txt`, `<v>-<rep>/v1/`.
- ✅ **Applied 16 Oct 2026 — the coordinator, under the user's rule of 15 Oct** («if the measurement shows it helps,
  it becomes the default with the §9 sentence»): the server declares `video.pace` **by default**; the switch now
  names its opposite, `--no-decoder-pace` (the old `--decoder-pace` is gone — with the default on it would mean
  nothing, the rule of the phase 9 cures in `main.c`); `RCP.md` §9 has the sentence (and §12 its exception, §13 is
  marked adopted); the benches' switch is `REMOTIX_DECODER_PACE=0` (`11-start.sh server` checks the server says
  «DECODER PACE ON» or «decoder pace OFF», `11-serves.py` reads it from the server's log). ⚠ Still in `RCP.md` §13
  and not moved into §3, §4.3, §7.1 (items 1, 2, 4 of §13.7).

### 11.33 🔸 Product changes of 15 Oct 2026 morning, not yet verified on the boxes (15 Oct 2026)

The product commits after `91b46c8c` (`git log 91b46c8c..HEAD -- src packaging installer`). Marks: `[M]`
measured, `[T]` tested by an automatic test or a desk test, ⚠ **not yet verified on the boxes** — that is every
item below unless its line says otherwise. Release notes: `docs/RELEASE-NOTES-1.5.md` (Fixes, Other improvements).
- **Connection (RCP.md §2.3, §11.9)**
  - `3ced6e1b` — after a validated migration the WebTransport and RCP layers follow the new address too
    (`wt_moved`, `rcp_moved`): one client, one address in the logs; credentials sent after a move are banned,
    counted and given to PAM as rhost under the address they came from (`cred_address` frozen at
    CREDENTIALS). `[T]` `01-b8-ban-test.c` section 6 (7 checks, 40 total); quic-conn stub oracle «exactly one
    `wt_moved` per validated move». ⚠ Not verified with a real network change.
  - `70fb2e7a` — pacing: one burst is at most ngtcp2's send quantum (before: ~54 packets whatever the rate);
    `transport_wait_ms()` rounds up, no more 100 % CPU spin on sub-millisecond gaps. `[T]` quic-conn fuzz 5 min,
    1.08 M execs, two new oracles, graft caught. ⚠ Not verified on a slow line.
  - `8758b88a` — replies leave from the local address the client wrote to (`IP_PKTINFO` / `IPV6_PKTINFO` on
    send), for connection packets and stateless answers alike; a validated migration updates `c->local`.
    `[T]` quic-conn fuzz, two new oracles, two grafts caught. ⚠ Not verified on a machine with several
    addresses.
- **Picture (KDE)**
  - ported on port-kde (`651e86ad`, `3d115f47`, `ca91b9c8`, `e951c832`, `d9fbdcb3`) and merged into `integrazione2`; built and unit-tested there (`verifica-rami` 28/28, `4be3a981`): the KDE «unchanged» filter (`1849a57d`, `ac6d5e91`, `845f4d19`, `751af3cb`, `2a02376e`)
  - `1849a57d` + `ac6d5e91` + `845f4d19` + `751af3cb` — the «unchanged» filter: a KWin frame whose damaged
    rectangles hold the same bytes as the last frame out is not encoded. Guards: area ≤ ¼ of 4K, one frame out
    every 250 ms anyway, bypass while a keyframe is due, self switch-off if a look costs > 3 ms on average
    (window mean, re-armed at a buffer renegotiation, hard off after 3). A frame the encoder dropped is not the
    reference; a held frame goes out when the scene goes still (on the card: the stream restarts, at most once
    per episode — `UcStaleGate`). `[M]` the problem: KDE/Firefox 3776×2016, ~50 buffers/s for 5 real changes,
    ~45 the same picture. `[T]` the decisions: `benches/20-unchanged-test.c` (`make -C src bench-unchanged`,
    also ASan/UBSan). ⚠ The cure is not measured: F-003 on KDE/Firefox 4K to rerun.
  - ported on port-kde (`c5f658ca`, `a19ecbd1`) and merged into `integrazione2`; built and unit-tested there (`verifica-rami` 28/28, `4be3a981`): `6da80736`, `93f9a22b`, nested KWin back to the wanted size
  - `6da80736` — KWin nested: KWin's output came up 1280×720 (labwc's own size) at the first mount; the wanted
    size is now written next to labwc's socket (`<host folder>/wanted`) and settle insists on it; `93f9a22b`:
    it is written only once labwc has taken it (birth excepted), and a KWin with no output yet is waited
    for, not nudged («KWin has announced no output after N s»). `[M]` the
    problem: run `functional/20261014-223248` (F-018b/c) and two births in the rete11-kde journal. ⚠ The cure
    is not verified.
- ported on port-kde (`ded9ca48`) and merged into `integrazione2`; built and unit-tested there (`verifica-rami` 28/28, `4be3a981`): `fa316d71`, the `remotix-capture` stream name
- **Sound** — `fa316d71`: the capture stream is named `remotix-capture` (`PW_KEY_NODE_NAME`), so
  `target.object` «remotix» names only the sink. `[M]` the problem: F-013 xfce/Firefox run `20261015-063747`,
  pw-dump shows the capture linked to itself, digital silence. ⚠ The cure is not verified.
- ⚠ Ported on port-varie (`8a2c3faa`, `6217b6dd`, `267068d4`, `cbe4534b`; from `247d4bd0`, `0153ad88`, `cbc1cb8b`, `790856bf`) and merged into `integrazione2`; built and unit-tested there (`verifica-rami` 28/28, `4be3a981`): the key receipts
- **Input (KDE lost keys)** — `247d4bd0` + `0153ad88` + `cbc1cb8b` + `790856bf`: a receipt from the compositor for every key
  (`ei_ping`; built only with libei ≥ 1.3.901), `DEVICE_PAUSED` written. Privacy (§9.2): the always-on log gets
  **one line per 10 s, only if something was slow**, with **no counts** (`790856bf`: a period starts at the
  first key, so «18 key events» after a password was its length) — slow share to 10 %, max/median to 10 ms,
  autorepeat risk yes/no, bounds to the second; exact counts, and per key only the slow ones (to the second,
  the key named only for modifiers), only under `--verbose`. `SIOCOUTQ` read
  before the key. ⚠ Not verified: no KDE run with it yet.
- **LXQt** — `4c79c59c`: the orphan pcmanfm-qt profile cure (§11.29) uses `g_lstat` and no longer follows a
  symlink out of HOME; a `settings.conf` link counts as the user's file. `[T]` `benches/21-session-orphan-test.c`
  (`ac82c60d`, `make -C src test-session`) 28/28 on the test server's build container (8124e05c's body 24/28).
- ⚠ Ported (25 Oct 2026): `quic-secret` as `%ghost` in the rpm spec (abandoned-attempt commit `ee0a692e`) is merged into `integrazione2` from `port-pacchetti` (`c89a1163`).
- **Packaging** — `ee0a692e`: `certificates/quic-secret` is `%ghost` in `remotix.spec`, so `uninstall --purge`
  on Fedora/AlmaLinux/openSUSE removes it and `/var/lib/remotix`; T10 now excuses only the engine's history.
  ⚠ Not yet seen on an rpm box.

### 11.34 ✅ The desktop ends in order at a reboot (LXQt/XFCE) — postponed until after 1.5 (15 Oct 2026)

- **The problem** (§11.29): at a reboot systemd stops the user's `session-N.scope` all at once; pcmanfm-qt
  dies while saving and leaves the empty profile folder. `8124e05c` (+ `4c79c59c`) cures the trace at the next
  birth; the race itself stays.
- **The proposal** is `phases/17-the-installer.md` §13.4 (desk study, nothing built): the child takes a logind
  **delay inhibitor** on `shutdown`; on `PrepareForShutdown(true)` it sends the orderly logout the product
  already uses for «Log Out», waits at most ~4 s, then releases the lock. Updates of the service are not
  touched. Verification: M1 by hand on one debian13-lxqt VM, then T10 `reboot-N1` with the discriminating facts
  (a)–(d) of §13.4 (blind in the boxes: `podman restart` skips logind).
- ❓ **What the user decides**, three questions:
  1. do it or not;
  2. the child only, or the child **and** the server (phase 2: covers desktops left without a child after an
     update, more code);
  3. whether to raise `InhibitDelayMaxSec` in the logind belt the engine installs (`remotix-power-keys.conf`),
     and to what (e.g. 15 s: every reboot may take up to that much longer, for every holder of a delay lock).
- ✅ **Decided 15 Oct 2026, decisione dell'utente** (*«fai quello che c'è da fare»*: the proposal's own timing,
  «after the release»). ⇒ **Postponed until after 1.5**: nothing is built for 1.5.0; the trace repair
  (`8124e05c`, `4c79c59c`) was in the abandoned attempt; it has since been ported (see the entry of the LXQt repair above, 25 Oct 2026) and is merged into `integrazione2`; the Known issue of 1.0.0-1 stays for the installations that still run it. The three questions above are asked again after the release.

### 11.35 ✅ The installer's preflight does not check that systemd-logind runs (15 Oct 2026)

- `[M]` (§11.30) AlmaLinux 10's container base image ships `systemd-logind` masked: no PAM session, no session
  bus, no picture. The bench unmasks it in every box image (`22242b33`). Never seen on an installed AlmaLinux.
- ❓ **The choices**: **A** — a new preflight check that logind is running (its exact form — refuse or warn — to be decided with it);
  **B** — leave as is, no new check. Recommendation **B**: the case was seen only in a container image.
- ✅ **Decided 15 Oct 2026, decisione dell'utente** (*«fai quello che c'è da fare»*: the recommendation). ⇒ **B**:
  no new check; the bench keeps unmasking logind in its AlmaLinux box images (`22242b33`).

### 11.36 ✅ Firefox at 4K with video: what to change (15 Oct 2026) — DECIDED D

> ⚠ NOT in this tree (25 Oct 2026): `728acd22`, the Firefox worker default, is written on the branch `ff-worker` (default on desktop Firefox only, with fallback; approved on reading, live proof still to do) but NOT merged: it waits for the user's decision D2. Chrome does not need it.

- `[M]` §11.31: the page's main thread stalls 55–64 % of the time (gaps in the sound); §11.32: the decoder queue
  ≥ 5 for 80 % of the frames, decode delay median 1.35 s, the picture 1.4 s old or more. Chrome is fine.
- ❓ **The options** (not exclusive; none built yet except what §11.32 says):
  - **A — a backlog limit in the page**: the page does not let its own backlog grow without bound.
    ⏳ **Designed and prototyped, not decided, not run in a browser** (15 Oct 2026): local branch
    `proposal/page-backlog-limit`, commit `f5a93ec7`, reviewed since — head `02298751` (`src/page.html` only;
    not on `main`, not synced).
    - `[M]` what it answers: F-013 Firefox 153, 3776×2016 H.264 ~30 fps. Main-thread route (run
      `20261015-063747`): `decodeQueueSize` **64–78 standing**, decode→callback median 2.1 s, picture age median
      2.3 s — yet `out` ≈ `delivered` (1516/1581, 2290/2369): the decoder keeps pace, the backlog is **old and
      never drains**. Worker route (`20261015-064237`, gnome): **731 frames inside** (≈ 24 s), out 1390/2121.
    - **The rule**, checked at every delivery to the decoder, the same `Viewer` code on both routes:
      backlog = max(`decodeQueueSize`, frames handed since the last reset and not given back); wait = how long
      the oldest of them has been inside (wall clock, `t_dec`).
      **Behind** = backlog **> 10**, or backlog **≥ 3 and wait > 500 ms**; **calm** = backlog ≤ 2 and wait
      < 150 ms; in between nothing moves (hysteresis). Behind **continuously for 500 ms** and **not draining
      fast** (at the pace from the window's peak, not empty within **2 s**) ⇒ `VideoDecoder.reset()` +
      `configure()` with the same config, `REQUEST_KEY` (§5.2; `last_number` = the last frame delivered, so
      the server's 200 ms grace must accept it — it is not a duplicate), deltas **not delivered** until the
      keyframe (the last good picture stays, §5.2), asked again once per second if it does not come. If the
      frame that trips it is itself a keyframe, it goes into the emptied decoder and nothing is asked.
    - **Against reset storms**: no reset of a *cold* decoder (nothing given back since its configure) for
      10 s — the first 4K keyframe can be slow; a second reset only after the decoder gave a frame back and was
      calm, and ≥ **5 s** after the last; resets < 20 s apart double the interval up to **10 s**, and the log
      says «this decoder does not keep up with the rate: A cannot cure it, B can».
    - **Chrome**: queue ≤ 2 and stretch 8 in tens of ms ⇒ never behind. A 1–1.5 s frozen main thread hands
      a burst to a decoder ≥ 2× the rate, which drains under 2 s ⇒ no reset (node simulation); a freeze of
      ~3 s or more at 60 fps would cost one reset — the picture jumps to now instead of replaying 3 s.
    - **Measurement**: `#backlog=off` turns it off on the same page. New counts **at the end** of
      `viewer.counts`, of the diary line and of `stretches()`: `backlog_resets`, `backlog_flushed`,
      `backlog_dropped`, `backlog_key_ms` (old names untouched; `inside` still includes the flushed frames).
      Server side: one «REQUEST_KEY(last_number=…) accepted» per reset in the server log.
    - ⚠ **Risks**: (1) **keyframe cost at 4K** — `[?]` ~10× a delta (§5.2), not measured on this video;
      at most one per 5 s per page, one per 10 s on a decoder that cannot keep up. (2) **bandwidth burst** —
      the keyframe is one big frame on the wire at once; on a narrow line it queues behind itself (phase 9:
      60 KB at 3 Mbit/s = 160 ms). (3) **a visible jump** — the picture freezes ~one round trip + the keyframe
      (`backlog_key_ms`) and then jumps ~2 s ahead; the frames in between are never shown. (4) on a decoder
      slower than the rate (the worker run's 731?) A only resets the lag every 10 s — the lag still
      grows between resets: that is B's case. (5) Firefox's `reset()` + `configure()` on a hardware decoder is
      `[?]` — if it throws, a new decoder is made (the road of a decoder closed by an error).
    - **How to measure** (F-013, Firefox, default route and `#video=worker`, then the same with
      `#backlog=off`): `f013-video-route.json` `age_ms` med from ~2300 to < 300 ms, `8_decode_callback` med
      from ~2000 to tens of ms, `dec_queue` from 64 to ≤ 5, `queue_deliv[5]` no longer ~all frames,
      `queue_skipped` far lower; `backlog_resets` 1–2 per run if the decoder keeps pace (several, ~1 per 10 s,
      if not ⇒ B); the main-thread route's sound gaps — expected to move only if the backlog was their cause.
  - **B — the server slows down when the client is behind**: the server sends fewer frames while the page
    reports a backlog. Its protocol form is `PACE` (§11.32, `RCP.md` §13 PROPOSED, off behind
    `--decoder-pace`): deciding B is deciding §11.32.
  - **C — the worker route (`#video=worker`, decode and drawing off the main thread) as the default on
    Firefox**, after A — waiting for the diagnosis run of §11.31, which says whether the stalls are the
    video's drawing.
- ⚠ No recommendation yet: the `#video=worker` run of §11.31 and an on/off measurement of `--decoder-pace` come
  first.
- ✅ **Decided 15 Oct 2026, decisione dell'utente** (*«fai quello che c'è da fare»*). The entry wrote no
  recommendation among A/B/C, only the order above; that order is what is accepted: (1) the `#video=worker`
  diagnosis run (checklist B1.13) and the `PACE` on/off measurement (B1.14, = B, §11.32); (2) option A measured
  on its branch (B1.15, `proposal/page-backlog-limit` head `02298751`, worktree `scratchpad/wt-backlog`) with
  `#backlog=off` as the control; (3) the option the numbers favour is merged — ⛔ **A is NOT merged** before its
  live run; C waits for B1.13. If nothing is measured to help before the release, 1.5.0 ships Firefox at 4K with
  video as a Known issue.
- ✅ **Decisione dell'utente** (15 Oct 2026): wait for the measurements — nothing is chosen before them.
- ✅ **DECIDED D — the user, 15 Oct 2026**: on desktop Firefox the worker route (`#video=worker`) is the default, with
  automatic fall back to the main thread (`#video=main` forces the old route; Chrome, AABrowser, Firefox for Android
  unchanged); merged from `proposal/firefox-worker-default` head `728acd22`. `[M]` box test 15 Oct 17:18–17:34 UTC
  (run `20261015-171856`, gnome+xfce): F-013 video OK on firefox (default route) and chrome; F-021 OK on all 4 rows;
  the 2 blind F-021 «fault» rows on xfce are blind on chrome too (the XFCE session was not there for G2) — not the page.
- `[M]` **The measurements, 16 Oct 2026** (fixer lane, `benches/15-suite/15-f013-variants.sh`, private box rxp15-xfce,
  `main` `61488985`, ≥ 3 runs per variant; the numbers of B in §11.32):
  - **B1.13 — the route.** Clients on the RX 6800: the worker (default) and `#video=main` both PASS 3/3, 60–61
    photos/min, age 0. Clients on the Intel card (a slow decoder downstream), pace off: worker PASS 3/3 (26
    photos/min, age 1.9 s, but the page's main thread never stalled, longest 101–112 ms); `#video=main` **FAIL 3/3 on
    the sound** — the main thread stalled 44–61 % of the time (63–76 stalls over the 250 ms audio cushion, up to
    1.1 s), audible 51–79 %, picture age 2.2 s, `dec_queue` 70–75. ⇒ D stands: the worker stays the default.
  - **B1.14 — B (`PACE`)**: it helps (§11.32) ⇒ on by default since 16 Oct 2026.
  - **B1.15 — A (the backlog limit)**: measured — the limit never acted, not merged (the bullet below).
- ✅ **Decided 16 Oct 2026 — the coordinator, under the user's rule of 15 Oct** («measure, then merge what the
  numbers favour»): B is adopted (§11.32); the route stays D; A is not merged (below).
- ✅ **A NOT merged — the coordinator, 16 Oct 2026, on the user's «merge what the numbers favour»** (B1.15). `[M]`
  F-013 Firefox 4K on a private box, clients' labwc on the RX 6800, one binary (main 9316d89b BENCH=1), main's page
  vs the proposal's (scratch merge c9025c9c) on and with `#backlog=off`, 3×3 interleaved: 56–61 photos/min, freeze 0,
  picture age median 0 ms, decode callback median 4–5 ms, the queue never above 4, **0 resets**; and again with the
  client Firefox in a 1-core scope (CPUQuota 100 %): 60–61 photos/min, freeze 0, age median 0, 0 resets.  The limit
  never acted: the 15 Oct standing queue (64–78, 2.1 s) was the bench's encode-card contention (the clients' labwc on
  the boxes' Intel, fixed by 3af4966f, §11.48 B), not a slow client.  ⇒ A2 closes with D (above) + B (decoder pace
  default ON, branch `fixer12-pace-default`, smoke 8/8 run 20261016-152019).  `proposal/page-backlog-limit` stays unmerged;
  reopen only if a real client shows a standing decoder queue.

### 11.37 🔸 The encoder follows the compositor's card (15 Oct 2026) — built, not yet run on a two-card box

> 🔸 Ported on `port-scheda` and merged into `integrazione2`; built and unit-tested there (`verifica-rami` 28/28, `4be3a981`): the render node of the compositor's card (`13422add` → `27e7ea61`: `src/render_node.c/h`, `choose_render_node()`, `--render-node`), the per-card codec test (`bc3158bf` → `ef3e6ca9`) and `node_of_codec()` at the negotiated depth (`facc4daa` → `7faac773`). The `DECISIONS.md` hunk of `13422add` is not ported (the 1.0 file: this entry is its text). Built on `integrazione2` (the Makefile of the first was done by hand).
> ⚠ With `port-sessioni` (`render_grant.c`, §11.4): three adjacent-line conflicts to keep both sides (`SORGENTI` in `src/Makefile`, the `render_grant.o` / `render_node.o` rules, the two `#include`s in `src/child.c`). **No functional conflict**: `render_grant` gives the user's private group `rw` on EVERY `renderD*` (a stale GNOME/KDE manager), §11.38 enrols the group of every `renderD*`; `render_node` only chooses WHICH of those nodes the encoder opens (the compositor's `main_device`, else `--render-node`, else `renderD128`) — the chosen node is always one both mechanisms already cover. Limit: with `--render-node` naming a node the grant did not reach (hot-plugged after the grant, §11.4 «declared limits») the open fails and the encoder falls back as the entry says.

- `[R]` SPECS audit: the encoder opened `/dev/dri/renderD128` hard-wired (`RENDER_NODE`, `src/child.c`). With
  two cards (the test server: Intel UHD 770 + AMD RX 6800) that is the kernel's first card, not necessarily
  the one the compositor draws on — every frame becomes a cross-card import (fails, or slow).
- 🔸 **Now** (`src/render_node.c`, `choose_render_node()` in `src/child.c`), once per session child, before
  the first encoder opens: (1) the compositor's card — `linux-dmabuf` v4 default feedback `main_device`
  (`dev_t` → `/sys/dev/char/M:m/device/drm/renderD*`, the same as `wlroots.c`'s slabs; labwc, Mutter and
  KWin all send it), 2 s ceiling; (2) the new server option `--render-node /dev/dri/renderDN` (repeated to
  the child like `--encoding-route`); (3) `renderD128`. One log line says the node, PCI address, driver and
  vendor:device, and where the choice came from. A one-card machine gets the same node as before.
- ⚠ **Not covered**: the parent's startup measure (which codecs to offer) has no compositor yet — it runs on
  `--render-node` or `renderD128`; if the compositor's card differs, the session's «encoder OPENED» line is
  the truth. No PipeWire-side device lookup (the DMA-BUF's exporter in `/proc/self/fdinfo`): the compositor's
  answer covers the three desktop families.
- 🔸 **Per-card codec test** (`node_of_codec()`, bc3158bf/facc4daa): when the session's card differs from
  the startup card, each codec is tested there once per depth before the first encoder; «no» ⇒ the
  startup card (cross-card import). A card that is FULL (`TOO_MANY_OBJECTS`) decides nothing and the test
  is not repeated for 10 s (`ENC_RETRY_MAX_MS`), so a full card costs one probe per 10 s, not one per retry.
- ⚠ **Known limits** (review of bc3158bf/facc4daa, 15 Oct 2026):
  - a «no» from the per-card test that is NOT «full» (a transient driver error included) sends that codec
    and depth to the startup card for the rest of the session child's life — it is not retried;
  - a hot-unplug of the session card is not re-checked: the choice is made once per session child;
  - the modifier list (`modifiers_per_route()`, NVIDIA without linear) is asked of the compositor's card
    only, even when a codec has fallen back to the startup card;
  - inside a box, a `--render-node` path that does not exist in the child falls back to `renderD128`,
    which may be a card the startup measure never measured;
  - a PROVISIONAL slab/modifier decision (taken before the compositor answered) is redone only at the
    next mount: if no remount follows, it sticks;
  - slab memory: on two cards the slabs are full size (3 × 4096×2304×4 = 113 MB) if EITHER card encodes
    in Vulkan, and this is not revisited once `node_of_codec()` has decided — a later client at another
    codec/depth may still fall back to the Vulkan card, and shrinking the slabs under it is the Radeon
    GPU hang case. The memory is wasted when the session ends up on VA-API only;
  - the per-card test delays the first image by one encoder open + at most 8 small (256×256) frames, per
    codec and depth — only on two-card machines whose session and startup cards differ.

### 11.38 🔸 First-login enrolment: only the render nodes' group (15 Oct 2026) — built, not yet run on the boxes

> 🔸 Ported on `port-scheda` and merged into `integrazione2`; built and unit-tested there (`verifica-rami` 28/28, `4be3a981`): the product (`76b602b1` → `8205fe12`: `collect_card_groups()` scans `renderD*` only; the box bench `11-c18`), the installer (`add575c6` → `e2620c0d`: `CardGroups()` and its Go test) and the benches (`002f4d14` → `e5d8f11f`: tenants, `tools-card-groups.sh`, `provision.sh`). Not ported on purpose: the `DECISIONS.md` and `docs/` hunks of `76b602b1` (the manuals are rebuilt before the release, §11.14). Expected overlap with `port-sessioni` in `src/child.c`: none at the text level (`git merge-tree` is clean); rechecked when built: no text-level conflict in `integrazione2`.

- **The evidence** (closes §10.36's «only `render`, once tested on the four desktops»): §11.4, `[M]` 13 Oct 2026 —
  the four boxes (Intel card), GNOME, KDE, XFCE, LXQt, users enrolled before the manager is born: gnome-shell, kwin,
  Xwayland, plasmashell and labwc all on `renderD128`, **never `card0`**; and the tablet (GNOME, primary-group ACL on
  both nodes): six fds on `renderD128`, none on `card0`. The encoder of the child opens render nodes only.
- **The change** (`src/child.c`, `collect_card_groups()`): `/dev/dri` is scanned for `renderD*` only; the group is
  still the node's real `st_gid` (a distribution that does not call it `render` works the same). Both callers follow:
  `card_groups()` (the «can see / IS NOT IN THE CARD'S GROUP» line) and `enroll_in_card_groups()` (`usermod -aG`, one
  `group-enrollments.jsonl` line per group, same `remotix-enrollments/1` format). The uninstaller reads the record
  per (user, group) and removes only what is recorded, so it needs no change. A user already in `video` from 1.0 is
  left there (PREEXISTING to this run; it was recorded then and is removed at uninstallation).
- **Not covered by the measurement** `[?]`: AMD/NVIDIA cards (the boxes are Intel), and a Vulkan encoder that might
  want the primary node; if a desktop is born in software on such a machine, `video` comes back with that
  measurement.
- ⚠ **Known limit, not measured — NVIDIA's proprietary driver.** With that driver the card is not opened through
  `/dev/dri` but through `/dev/nvidiactl`, `/dev/nvidia0`, `/dev/nvidia-modeset`, `/dev/nvidia-uvm` (the encoder's
  Vulkan Video route, `installer/engine/encoding_routes.go`; the installer advertises it, `installer/ui/texts.go`
  `t.scheda.nvidia`). Their group and mode come from the module's `NVreg_DeviceFileGID`/`NVreg_DeviceFileMode`:
  the usual default is root, 0666 (anyone opens them, no group needed), but a distribution that sets
  `NVreg_DeviceFileGID=<video's gid>` with mode 0660 (Gentoo's default) lets only `video` members in — and from
  §11.38 nobody is put in `video`. Expected symptom: the compositor and the encoder cannot open the card; the
  desktop draws in software, or the encoder has no route. Neither `card_groups()` nor `CardGroups()` looks at
  `/dev/nvidia*`, so the log's «can see» line would say OK. Said in `docs/RELEASE-NOTES-1.5.md` (Known issues:
  add the users to `video` by hand). Built (15 Oct 2026), the warning only: when `gpu.nvidia_proprietary` is yes the
  installer's check reads `/proc/driver/nvidia/params` (else the group and mode of `/dev/nvidiactl`,
  `/dev/nvidia[0-9]*`) into `gpu.nvidia_group` and raises the WARNING `RX-GPU-007` naming the group when it is not
  root, not the render group, and the mode does not give everyone read and write; `CardGroups()` is NOT widened
  (enrolling in that group as well stays the user's decision). Not measured on a real NVIDIA machine.
  ❓ **Still open** (15 Oct 2026): the user has not decided whether `CardGroups()` widens to the NVIDIA group; the
  «fai quello che c'è da fare» of that day did not cover it, because no recommendation was written for it.
  ✅ **Decisione dell'utente** (15 Oct 2026): wait for the measurements on a real NVIDIA machine; `CardGroups()`
  stays as it is until then.
- **Installer aligned** (15 Oct 2026, `add575c6`): `CardGroups()` (`installer/engine/install_plan.go`) scans
  `/dev/dri/renderD*` only, the group read from each node; the users present at installation get the render group,
  not `video`. Record format and uninstallation unchanged; unit tests in `installer/engine/card_groups_test.go`
  (render only, another group name, no `renderD*` ⇒ «nobody to add»).
- Bench: `benches/11-boxes/11-c18-the-product-sets-the-groups.py` asks only the `renderD*` groups (certification
  green); `17-t10.sh` compares the groups before installation and after uninstallation, unchanged.

### 11.39 ✅ When the server could not check the password, the page no longer says «wrong password»: `0x0E` (15 Oct 2026)

> ⚠ Ported (25 Oct 2026): the `0x0E SESSION_UNSERVABLE` refusal (abandoned-attempt commit `24f99518`) is merged into `integrazione2` from `port-rcp`. verification 28/28 on `4be3a981`, 24 Oct 2026; the live check with real browsers is still due (CHANGES-1.5.md, «Still open»).

- **The problem, in plain words.** Sometimes the server cannot check a password at all: the helper process that
  asks PAM has died or is restarting (`c7e86ead`), PAM hangs and the 12 s net gives up (`VERDICT_CAP`,
  `963afb42`), or the helper already has its 16 checks in flight (`MAX_IN_FLIGHT`, `helper.c`). These refusals are
  «ours» (`refusal_is_ours` in `src/rcp.c`): the server never counts them toward the ban, and its log says
  «this REJECTED is OURS, not PAM's». ⛔ But on the wire they leave as `REJECTED(0x07 WRONG_CREDENTIALS)`, and
  the page shows *«incorrect username or password»* — the owner retypes a password that was right, doubts the
  keyboard layout, and the User Manual (ch02 «TAB») tells them to check the password. The real cause is only in
  the server's log.
- **Why it was done that way.** `src/rcp.c` (the comment before `reject()` in `rcp_time()`) reads `RCP.md` §4.4
  as «§4.4 forbids distinguishing them». The reviews note that §4.4 forbids one thing only: telling «no such
  user» from «wrong password». A sentence like «the server could not check your credentials, try again» says
  nothing about the user or the password — the check never happened — and the 12 s wait already shows that
  something is wrong on the server side.
- **What is NOT in question.** Refusals decided by PAM stay `0x07` in every option, and only `0x07` is counted
  (§4.4-bis). The two refusals that already say `0x08` without PAM (the table full of bans; too many checks in
  flight from one address) keep `0x08`. ⛔ «PAM could not judge» (`authentication.c` `why_no()`: a missing
  `/etc/pam.d/remotix`, `PAM_SYSTEM_ERR`, `PAM_AUTHINFO_UNAVAIL`…) stays `0x07` **and counted** — it comes
  through a PAM answer, and some of those codes depend on the user name (a directory user against a local one),
  so a different reason there **would** be an oracle. If that case is to change, it is a decision of its own.
- ❓ **The options:**
  - **A — keep `0x07` for everything.** Nothing changes. Security: nothing to analyse — it is today's wire.
    Price: the owner's wrong diagnosis above; and benches that require `0x07` to mean «PAM said no»
    (`02-pam-standstill.py` sample C) cannot tell a sample PAM never saw.
  - **B — a new reason, e.g. `0x11 CHECK_NOT_MADE`**, sent only when `refusal_is_ours` is true *and* the count
    was not touched; same fixed-second floor (≥ 1000 ms, `FIXED_DELAY`), so the stopwatch is unchanged.
    Price: ⛔ `RCP.md` §9 says the window for new reasons **closed on 10 Aug 2026** (`0x10` came in on 15 Aug
    anyway, §4.1-quater, by the user's decision — a precedent, not a rule). Every RCP reader must learn it or it
    says «unknown reason»: `benches/01-b4-validator.py` (`REASONS`, raises `NotCompliant`), `01-b3-client.py`,
    `01-b11-page.html`, `02-pam-standstill.py`; a tab opened before the update shows *«refused, reason 0x11»*.
  - **C — reuse `0x0E SESSION_UNSERVABLE`** in `REJECTED` for the same refusals, same timing. RCP has no
    «server busy» code: `0x06 BUDGET_FULL` is desktop capacity, `0x0C SERVER_CLOSING` and `0x0D TIMED_OUT`
    (handshake ceilings of §4.6) would be false. `0x0E` already means «the server could not serve this, it is
    not your mistake, try again, the reason is in the log», and every reader already knows it — no byte is
    added, §9 is not touched. The page knows a `REJECTED` answers `CREDENTIALS`, so it can show a login sentence
    of its own, e.g. *«the server could not check your password just now, and it is not your mistake: try again
    in a moment, and if it happens again ask whoever administers the server»*. Price: §8.2 widens `0x0E` to a
    sixth road, and its «MUST carry the detail in the body» cannot hold for `REJECTED` (its body is the reason
    byte only) — one line must say so.
- **Security, B and C alike** (the same refusals, only the byte changes):
  - *no password oracle*: these refusals are decided before PAM answers — or without asking it — so the
    password was never judged; the byte carries nothing about it;
  - *no user-existence oracle*: helper down and 16 slots full are decided before PAM sees the name. A PAM hang
    *can* depend on the name (a directory lookup), but it already shows as a 12 s answer instead of ~1 s; the
    new byte adds nothing the stopwatch does not already say. ⛔ The rule to write: **the reason may not say
    more than the timing already says**;
  - *timing*: unchanged — the fixed second stays a floor for every refusal (`rcp_time()`);
  - *ban counting*: unchanged — these are already not counted. ⭐ Gain: on the wire **«counted» becomes
    exactly «`0x07`»** (or `0x08`), so a bench can check the count from the reason;
  - *the 16-slot DoS*: whoever floods the server from many addresses can fill the 16 slots and keep the owner
    out (each address can hold ≤ 3 checks, §4.4-bis hardening). Neither option makes this easier or harder.
    Today the owner sees «wrong password» and is not banned; with B/C they see «try again», which is true. ⚠
    The attacker also learns that the flood works (with `nodelay`, §11.25, the stopwatch barely tells it today)
    — a small gain for them, against a true sentence for the owner;
  - ⛔ the page must **not** retry by itself on this reason: retries are by hand, as today.
- **What would change** (B or C): `src/rcp.c` — `reject(s, s->refusal_is_ours ? <code> : s->cred_reason)` in
  `rcp_time()` only where the reason is still `0x07` (the `0x08` roads unchanged), with its comment and log line
  rewritten, and the copy `benches/rcp/rcp.c` kept identical (the `Makefile` compares them); `RCP.md` §4.4 (one
  line: «a check the server could not perform is refused with `<code>`, after the fixed second, and is not
  counted») and §8.2 (the row; for C the sixth road of `0x0E` and the body exception; for B also §9 and the
  §0-bis count); `src/page.html` `REASON_TEXT` (B: a new entry; C: a login sentence chosen when the code arrives
  in `REJECTED`); benches — `01-b8-ban-test.c` section 7a (`VERDICT_CAP` now expects the new code; a «no»
  delivered by PAM still `0x07`), `02-pam-i3.py` cases `dead` and `dead-in-flight` (require the new code, and
  `0x07` still for the PAM refusals), `02-pam-standstill.py` (sample C: the new code is a thrown-away sample,
  like `0x08`), and for B the readers listed above; User Manual ch02 «TAB» (a row), Technical Manual
  (ch05 RCP, ch14 security) regenerated.
- **Recommendation: C (`0x0E`).** It fixes the owner's wrong diagnosis with no new byte on the wire, so §9
  stays closed and no reader breaks; the security analysis is the same as B's. B is the cleaner name, and is
  the choice if the user prefers a dedicated code over widening `0x0E`. A is defensible only if the extra signal
  to a flooding attacker is judged worse than misleading the owner — it is not, in my reading.
- ✅ **Decided 15 Oct 2026, decisione dell'utente** (*«fai quello che c'è da fare»*: the recommendation). ⇒ **C**:
  `REJECTED(0x0E SESSION_UNSERVABLE)`. Built in `24f99518`: `src/rcp.c` (+ the bench copy) sends `0x0E` where the
  refusal is ours and the reason was still `0x07`; `RCP.md` §4.4 (the rule, «the reason may not say more than the
  timing already says», no automatic retry) and §8.2 (`0x0E` in `REJECTED`, detail in the log only); `src/page.html`
  a login sentence of its own, not overwritten by the close code; `01-b8-ban-test.c` 7a + section 22 (155 checks),
  `02-pam-i3.py` `dead`/`dead-in-flight` require `0x0E`; manuals' rows. `[M]` 192.168.0.2 build container:
  `01-b8` 155/155, helper-orphan 12/12, and `01-b8` against the old `rcp.c` RED on 7a and 22a. ⏳ Not yet:
  `02-pam-i3.py` against a running server, the page in a browser. `02-pam-standstill.py` needs nothing (it already
  throws away every sample that is not `0x07`).
- ⭐ **Addendum, 15 Oct 2026 — two of the 16 places are kept for a key that logged in lately** (adversarial review
  of main, MEDIUM). The «16-slot DoS» above, made concrete: about six fresh addresses × 3 checks each keep the 16
  places of `MAX_IN_FLIGHT` full, and the owner reads `0x0E` for as long as the flood lasts. ⇒ `src/helper.c`
  `RESERVED_FOR_KNOWN 2`: `helper_ask()` gives an unknown key 14 places and a key that logged in within
  `GOOD_AGE` (30 days, the same `good_keys` the ban's eviction already uses) all 16. `rcp.c` says which through
  `rcp_asking_for_known_key()`, true only while it is inside `ask_verify` for such a key (the §4.4-bis key: IPv4
  address or IPv6 /64); the twins `benches/rcp/rcp.c|h` are kept identical. Nothing else changes: the refusal is
  the same `0x0E` after the fixed second, not counted; the per-key limit of 3 checks in flight still holds for a
  known key. ⚠ What it does NOT do: someone behind the owner's own address (the same NAT, the same /64) shares the
  reserve; a flood that also holds the last 2 (it would need a key that logged in) still locks out; the owner on a
  new network is unknown until a first login there. `[M]` 192.168.0.2 build container, uid 1000: `01-b8` section 25
  (5 checks, 177/25 green), helper-orphan section 9 (6 checks, 28/28; on the old `helper.c` 25/28, RED on the
  reserve), `helper-proto` fuzz 90 s with the oracle made key-aware, no finding.

### 11.40 🔸 QUIC connection caps, and who is closed when the server is full (15 Oct 2026) — approved 24 Oct 2026, ported on §11.9, under verification

- 🔸 **State on 24 Oct 2026.** *Approved by the user on 24 Oct 2026* (after §11.9, on which it depends: the caps count
  connections whose address the Retry has proved). The code of the first attempt (discarded; the tag `1.5-scartata` is in
  the archive repository `REMOTIX-V15-archivio` on the laptop, **not in this repository**) was **ported by hand on top of
  `quic-su-p1`** (branch `limiti-su-quic`, the porting commit), not applied as a patch: it does not apply cleanly (the file
  differs by ~1000 lines). Taken from the tag (its commits, which do not change): `2f671726`, `a723eb6b`, `f4201ee6`, `d0e56764`,
  and from `0e0f6c32` the answer `INVALID_TOKEN` for a token used twice (the design below; `d0e56764` still sent a
  second Retry). **Left out** on purpose: the later commits of the tag (`91f6edb7`, `eab9623a`, `3d661878`, `8faaa131`,
  `24c7b668`, `4f52eab8`, `5843b5b6`, `cda1636d`, `2cb0be61`): the rule «wait-verdict is never evicted» stays.
  *Adaptations:* `send_msg()` here has no local-address arguments and there is no `send_on()` (the close goes to
  `c->remote`, as the dead-line close does); `<arpa/inet.h>` added; the split-binary helpers of the bench launcher
  (`01-net-split.sh`) are gone (plain `/flood` state dirs); the «new connection» line says «address validated with a
  Retry» always (here every connection has passed the Retry).
  Done, `[M]`: clean build, normal and `BENCH=1`, in a copy made with `git archive`: the same two warnings as
  `quic-su-p1` (`vulkanvideo.c:354`, `:379`), none new.
  **To do:** `benches/01-b10-flood.py` + `01-b10-launch.sh` (the 01-b10 bench, recovered from the tag) with small caps
  16/4/8, 3 runs of 9 checks; the default caps (128/8/32) live; the complete suite, Chrome and Firefox; the A/B at
  sample against the build without the change; **running the `quic-conn` fuzz (`benches/fuzz/quic-conn/run.sh`)**.
  The `quic-conn` fuzz harness (the fuzz harness commit on this branch) is **now here**: `benches/fuzz/quic-conn/`,
  recovered from the tag (`benches/runner/fuzz/`, which this tree does not have) and adapted — a wait-verdict is never
  evicted, as `evict_rank()` of this branch; the later rules of the tag (the «parked» connection, the pre-login
  path-change cap) are not in it. It builds (`build.sh`, 80 seeds) but has **not been run yet**: the oracles below were
  never run on this code.
- ⚠ Everything below this note (the design, the `[M]` and `[?]` runs, the churn analysis) describes the **first
  attempt**: the numbers were measured on its code, not on the code now in the tree.

- **The problem, in plain words** (security review of the 1.0 code): `accept_conn()` in `src/transport.c` never
  looked at how many connections were open. Each connection that has not signed in yet can hold about 1 MiB for
  about 65 s (and keep PAM slots busy), so a flood of connections could fill the memory. The first cure
  (`2f671726`) added caps; its own review (finding 3, HIGH) showed the 256 places could then be held by
  connections that never sign in (32 IPv4 addresses × 8, or one IPv6 /56), 65 s at a time, locking everybody
  out. `a723eb6b` closed that.
- **The design** (`2f671726`, `a723eb6b`):
  - four caps, all server options: `--max-connections` (default **256**, all connections), `--max-pending`
    (default **128**, of those not yet signed in), `--max-pending-per-address` (default **8** not signed in per
    IPv4 address or IPv6 /64), `--max-pending-per-48` (default **32** not signed in per IPv6 /48);
  - the address is keyed by the same rule as the ban (`address_key()` follows `rcp_key_address()`, §1.9-bis):
    v4-mapped and NAT64 `64:ff9b::/96` count as their IPv4, `::1` whole, other IPv6 by /64;
  - beyond a cap the newcomer gets a stateless `CONNECTION_CLOSE(CONNECTION_REFUSED)`, only after the Retry
    token has proved its address; nothing is kept. One log line at most every 10 s, with the counts;
  - **when all connections or all pending places are taken**, the server makes room by closing the **oldest**
    connection that has not signed in **and has not yet sent its credentials** (no WebTransport session yet,
    or waiting for HELLO or for CREDENTIALS). ⛔ A connection in **wait-verdict** (its password is being
    checked) is **never** evicted, nor one already signed in. A newcomer whose own address or /48 is full is
    refused, not given room. Evictions are counted in the 10 s summary line;
  - a connection stops counting as «pending» at sign-in (admitted verdict, in `transport_verdict_from()`) or when reaped. ⭐ It is charged to its **birth
    address** and keeps it after a migration (§2.3), so moving cannot free a place on the old address.
- ⚠ **The price, accepted knowingly:** everybody behind one shared IPv4 address (an office behind one NAT
  router) gets **8 sign-ins in progress at once**; the ninth is refused and must retry (the administrator can raise
  `--max-pending-per-address`). Behind one IPv6 /48, 32. And under a flood, an honest connection that is slow to
  send its password can be the one evicted — it reconnects; one already typing into wait-verdict is safe.
- **How sure** `[?]`: the `quic-conn` fuzz harness (op 12 LIMITS, `wt_rcp_state()` played, birth address per
  connection) with its oracles — caps hold by the harness's own reading of the rule, an eviction only when full,
  only of a connection before its credentials, the oldest first, at most two per newcomer — run **locally only,
  with ASan**; 8 deliberate mutations of the new code, all 8 caught. ⛔ **Not yet run on the test server** (`rxtest
  fuzz --target quic-conn`) **nor against a running server** (RELEASE-CHECKLIST B1.10).
- *Where:* `src/transport.c` (`accept_conn()`, `address_key()`), `src/main.c` (the options),
  `benches/runner/fuzz/harness/` (`quic-conn`). Said in `docs/RELEASE-NOTES-1.5.md` («Limits on connections»,
  upgrade note 7).
- **Addendum (15 Oct 2026, `f4201ee6`) — the review of `a723eb6b`, three fixes:**
  - *HIGH*: a client that opens the session and never sends HELLO ends «finished» (timed out, no ban), but its
    PINGs keep the QUIC connection alive — 16 addresses × 8 could hold all 128 pending places. Now a «finished»
    connection is the first to be evicted, and **any connection still not signed in 90 s after its birth is
    closed** (`UNLOGGED_MAX_S`: 5 s for HELLO + 60 s for the credentials + 12 s verdict + margin). These closes
    are counted in the 10 s summary line;
  - *MEDIUM*: the connection evicted now comes from the **most crowded place** (the IPv4 address or IPv6 /48
    with the most pending connections), then the earliest state, then the oldest — so a flood evicts itself,
    not real users signing in from elsewhere;
  - *LOW*: the victim is closed only **after** the newcomer has really been accepted, and at most one per
    newcomer.
  - How sure `[?]`: `quic-conn` fuzz with new oracles (the evicted one is exactly the one the rule names, no
    unsigned connection alive past 90 s, none closed for age before) — **local ASan only**, 7 mutations all
    caught. ⛔ Still not run on the test server nor against a running server.
- **Live run (15 Oct 2026, HEAD `496b6dbd`, bench `benches/01-b10-flood.py` + `01-b10-launch.sh`, `rxtest protocol
  --only b10`)** `[M]`: the built product in a private podman container on the test server (no box, no desktop, one
  private network namespace, caps 16 pending / 4 per address / 8 per /48), 9 checks of 9 pass, 3 runs out of 3:
  the 5th pending from one address and the 9th from one IPv6 /48 are refused with `CONNECTION_REFUSED` before the
  handshake ends, and the server never logs them as born; a connection with no session and one that never says
  HELLO, both kept alive by client PINGs, are closed at 90.1 s; a never-HELLO flood (40 workers, 10 addresses)
  fills the 16 places and is evicted ~200 times in ~20 s, every eviction from a flood address, while 5 logins out of
  5 from another address are admitted by PAM. ⚠ Without a desktop the login ends at PAM's yes (FAREWELL 0x10, the
  stage dies at once), not at `ADMITTED`; and the default caps (128/8/32) were not run live.
- **Addendum (15 Oct 2026) — churn: what the eviction rule costs an attacker, and two holes closed.**
  - *What it takes to push a real user out* (churn analysis): the victim comes from the most crowded place, so a
    flood from a few places evicts only itself — against 8 addresses QUIC holds. To reach a real user's
    connection an attacker needs about **`--max-pending` − 1 distinct places at one connection each** (≈ 127
    IPv4 addresses or IPv6 /48s with the defaults), **and** to renew them faster than an honest client finishes
    its handshake and sends its credentials (its window is a few round trips, not the 90 s age limit).
  - ⭐ **FIFO among equals is chosen on purpose**: when every place holds one pending connection, the oldest
    goes. It gives an honest arrival `--max-pending` − 1 arrivals of margin, and costs the attacker a steady churn
    from ~127 places instead of a burst.
  - ⛔ **`page.c`'s refuse rule must NOT be copied here** (`fair_victim()`: refuse the newcomer when its own
    place would hold more than the victim's). On QUIC it would make a **cheap lockout**: with the places full at
    count 1, every newcomer — the owner too — would be refused while the attacker only keeps his connections
    alive. Here a full server always evicts, and only a full ADDRESS or /48 is refused.
  - *Retry tokens are single-use* (`transport.c`, `TOKENS_KEPT`): until today a token stayed good for its 10 s,
    so an evicted connection's Initial, sent again, was a new connection with no new Retry — **one datagram per
    eviction**. Now the tokens that made a connection are remembered until they expire (a keyed 64-bit hash in a
    ring of 4096 = 64 KB, bounded), and one seen again is answered `INVALID_TOKEN` — not a second Retry, because
    an honest client can get there too (its half-open connection evicted and the close lost, or reaped after
    «read failed») and must discard a second Retry (RFC 9000 §17.2.5.2), so it would wait its whole handshake
    timeout; with `INVALID_TOKEN` it fails at once and reconnects. Each new connection costs the attacker a fresh
    Initial, a Retry and a round trip at a real address. ⚠ Past 4096 connections in 10 s (≈ 400 a second) the oldest
    remembered token is forgotten early and counted in the summary line; refusing instead would answer every
    token with a Retry and nobody could connect.
  - *The log*: «new connection from …» was one normal line per accepted connection, so a churn flooded the log.
    Now the first 5 in a 10 s window are written, and the rest counted in one line at the end of the window
    (they stay in the `--verbose` detail).
  - How sure `[?]`: `quic-conn` fuzz oracles — the same token within 10 s for no live connection makes no
    connection and gets `INVALID_TOKEN`, not a Retry; never more than 2 × 5 «new connection» lines in any 10 s — with seeds
    (a dead or evicted connection's Initial again at 0, 5 and 11 s; a 12-connection churn); local ASan clean,
    5 mutations of the new code all caught; on the test server, 3 minutes each: `quic` 8.1 M runs clean,
    `quic-conn` 260 k runs clean (after a harness fix: the BURST op moved the clock after its last pass), the
    `quic-conn-graft` fault check found.

### 11.41 🔸 The last row of the picture is tinted in the browser — A, the page clamp (15 Oct 2026) — in package 1, live check due

- **The problem, in plain words.** On Chrome the bottom row of pixels of the remote screen has the wrong colour
  (e.g. green on GNOME): the brightness is right, the colour is pulled about ¼ toward zero (`66c70ba9`). ⭐ The
  stream is clean: `4b194bbc` proves it — two picture rows share one colour sample, the row above is right, so no
  stream could carry that picture. The browser, when it converts the decoded frame to RGB
  (`texImage2D(VideoFrame)`), mixes in a row of zeros **below** the picture. The numbers match that model to the
  unit on three desktops, within 3 on KDE.
- **Where it shows.** Chrome on all four desktops (GNOME, KDE, XFCE, LXQt). Firefox probably too, since the
  photo fix `3d1d234c` stopped cutting the row away — not yet checked.
- ⚠ **What it does to the tests:** the new bench check `chroma_bleed()` (`66c70ba9`) will now make **F-011 FAIL
  on Chrome**, until one of the options below is chosen.
- ❓ **The options:**
  - **A — fix it in the page** (branch `proposal/last-row-page`, head `64fe796a`): on the WebGL route the canvas's
    last row is drawn from the row above it, so the browser's zero row is never read. Price: the last row of the
    screen is a **copy of the row above** (one pixel row; a one-pixel line at the very bottom would not show).
    ⚠ The shader has **not** been through a real GLSL compiler and has **not** been run live.
  - **B — fix it in the encoder**: encode a few extra rows below the picture and tell the decoder to crop them
    (the SPS crop). Price: a bigger change in the server, a little more to encode, and ⚠ it helps **only if** the
    browser reads the decoder's extra rows rather than its own zeros — not known; the experiment could come out
    empty.
  - **C — call it a known browser fault**: F-011 reports it as a known issue, not a failure. Price: nothing to
    build, but the users keep seeing a wrong-coloured bottom row, and a real bottom-row fault of ours would be
    hidden by the same exception.
  - **Recommendation: A, after a live check** — compile the shader in a real browser, watch F-011 go green on
    the four Chrome desktops and on Firefox, then merge. The price (one row repeated) is invisible in practice;
    B is a gamble on browser internals; C leaves the fault on screen.
- ✅ **Decided 15 Oct 2026, decisione dell'utente**: **A**, the page clamp. In the first attempt (discarded, tag
  `1.5-scartata`) it was `main` as `6fa5fd60`, cherry-picked from `proposal/last-row-page` (`64fe796a`). ⏳ The live
  check is still due: `verify-round.sh` step 10 (F-011 on Chrome and Firefox, the four desktops) — `chroma_bleed` must go
  green; a red there reopens this entry.
- 🔸 **In this tree (package 1, 24 Oct 2026)** — the commit «F-011: page.html shader samples with textureSize,
  half-texel clamp, highp» (`src/page.html`, +15 −2). It is the page clamp of A **written again, and not the same
  code** as `proposal/last-row-page`: the shader reads the real size of the texture with `textureSize()`, scales the
  coordinate by visible/real size and keeps it half a texel **inside** the visible rectangle (the last row is not copied
  from the row above; sampling just never reaches the padding), and uses `highp` (`mediump` is too coarse for
  coordinates past 1024). Why it differs: Chrome 156 imports the frame with the CODED height (2082) above the visible one
  (2064) and the linear filter mixes the padding in at the edge. Done: it compiles with the page (normal and `BENCH=1`,
  no new warning). ⚠ **Not yet done:** the shader has not been through a real GLSL compiler nor run in a browser from this
  tree — F-011 on Chrome and Firefox, four desktops, is the test, and it is still due.
- 🔸 **Cure (b), 24 Oct 2026 — branch `f011-riga`, in `pacchetto1b`** (commit `127f69a6`, `src/page.html`, +10 −2).
  **Cause:** cure (a) was not enough, F-011 stayed red on Chrome. The texture is already RGB when the shader sees it:
  Chrome converts the VideoFrame to RGB **before** the shader, and builds the last visible row from 3/4 of chroma row 1031
  plus 1/4 of the padding chroma row 1032, which is zero ⇒ **R −57, G +24, B −68 on every desktop**. (The test passes on
  xfce only because of its threshold.) **Fix:** the bottom clamp moves one row higher **only when** `textureSize().y` is
  greater than the visible height `vis.y` (the browser uploaded padding rows): the last visible row then repeats the row
  above. Columns and the Firefox path (texture = visible) are untouched. **Cost:** one row of detail lost at the bottom
  edge on Chrome. ⛔ **Insufficient on its own** (24 Oct 2026): the test of cure (b) showed that Chrome uploads a texture of
  exactly the **visible** size with the last row **already tinted**, so `textureSize().y > vis.y` is never true there and the
  clamp never moves.
- ✅ **Cure (c), 24 Oct 2026 — branch `f011-riga`** (commits `571c8145` and `9b963d77`, `src/page.html`; merged into
  `pacchetto1b` as `3a4d447d`). The signal that does not lie is the **VideoFrame**: when `codedHeight` is greater than the
  visible rectangle (`visibleRect.y + height`) there are coded rows below the visible ones, and the page passes the shader a
  new uniform `trim = 1.0`; the shader then moves the bottom clamp one row up, as in (b), whatever `textureSize()` says. The
  Firefox path (no coded rows below) keeps `trim = 0.0`. The shader comment mentions (c). **Verified 8/8 PASS on 24 Oct 2026**
  with `f011-riga-prova` (F-011 / `chroma_bleed`) — gnome and xfce, Chrome and Firefox, 2 rounds each; kde and lxqt still due.
  The last row = the one above (on Chrome 2063 = 2062, on Firefox 2015 = 2014). Cure (b) stays in the code, as the second guard.

### 11.42 ✅ The test server's Intel card for the stress bench: `nicfio` in the card groups (15 Oct 2026)

- **The problem, in plain words.** The stress bench runs a client Chrome and a small desktop (labwc) on the test
  server, and they should use the **Intel** card. But the benches user `nicfio` **cannot open** the Intel card's
  render node (`renderD128` is `root:render 0660`, `nicfio` is not in `render`, no ACL), while the AMD node
  (`renderD129`) has an ACL `user:nicfio:rw`. ⚠ Both ACLs changed at **05:17 UTC on 15 Oct** — cause unknown.
- **What it did:** the client Chrome and labwc fell back to the **AMD card or to software** (`fd8ada94`). So
  **last night's client numbers in the stress are not clean** and must be measured again.
- **What is built:** `fd8ada94` makes each climb start run `setfacl -m u:nicfio:rw` on the Intel node (through
  the climb's sudo), read it back and write it in the log. Not yet run (the sudo was refused when tested).
- ❓ **The options** (it touches a **shared** server, so it is the user's choice):
  - **A — the ACL at each climb start** (as built). Price: only `nicfio`, only that node; but it is redone each
    time and lost at reboot or whenever something resets the ACLs again (as happened at 05:17); it needs the
    climb's sudo to allow `setfacl`.
  - **B — add `nicfio` to the `render` group** (once, `usermod -aG render nicfio`). Price: permanent and
    survives reboots and ACL resets; `nicfio` can then use **every** render node of the server, not only the
    Intel one; it takes effect at its next login.
  - **C — both**: the group as the base, the ACL as a safety net that also writes in the log what it found.
  - **Recommendation: B** (or C if the user wants the log line too): it is the normal Linux way and does not
    depend on something resetting ACLs. ⚠ Whatever the choice, find out what changed the ACLs at 05:17.
- ✅ **Decided 15 Oct 2026, decisione dell'utente**: B, done by the user — `nicfio` was added to the groups
  **`video` and `render`** on the server (effective from its next login). `fd8ada94`'s ACL at each climb start stays
  as a harmless fallback: with the group its log line will say «already openable». ⚠ **Still unknown**: what
  changed both render nodes' ACLs at 05:17 UTC on 15 Oct. ⏳ Last night's client numbers in the stress are still to
  be measured again (checklist B1.12).

### 11.43 ✅ Someone who only watches is detached after 30 minutes — keep it, or give the page a «still here» (15 Oct 2026) — DECIDED A

> ⚠ Ported (25 Oct 2026): the 30-minute watcher clock (abandoned-attempt commit `496b6dbd`) is merged into `integrazione2` from `port-rcp`. verification 28/28 on `4be3a981`, 24 Oct 2026; the live check with real browsers is still due (CHANGES-1.5.md, «Still open»).

> **Decision (user, 15 Oct 2026): A, keep it as specified.** «la password serve sempre, più che altro una sessione rimasta aperta consuma risorse»: asking for the password again is expected, and the point of the clocks is to free the resources of a session nobody uses. No «still here» signal, no grace after a reconnection (a reconnection past 30 minutes simply asks for the password). The 30- and 60-minute clocks stay as in 496b6dbd/24f99518.

- **The problem, in plain words.** Since `496b6dbd` (bench twin and test) and `24f99518` (the same `rcp.c` blob in
  `src/`), the 30-minute clock of `SPECS.md` §5.3 is reset **only** by the five user gestures of `RCP.md` §7.3
  (`POINTER`, `BUTTON`, `WHEEL`, `LETTER`, `KEY_POSITION`), in `handle_input()`. Before, any RCP byte reset it, and
  the page sends some **on its own** (`REQUEST_KEY` after a hole, `PACE`, the opening `CLIPBOARD_ANNOUNCE`, canvas
  and layout updates): a tab left open on an abandoned desk held its session, and its slot, forever. ⇒ Now **whoever
  only watches** for 30 minutes gets `FAREWELL 0x02` and the sign-in form. Examples: REMOTIX in AABrowser on Android
  Auto while driving (the user's own use, 14 Oct 2026), a dashboard on a wall screen, a long
  video. ⚠ A **local** pinch-zoom on the phone sends nothing to the server, so it does not count either.
- **Why §5.3 exists — it is a security clock, not a resource clock.** §4.3: the desktops' own screen lockers are
  **off** on purpose (they break capture and input on GNOME and KDE), and «the lock is REMOTIX's»: 30 minutes
  without input ⇒ the client is detached and **getting back in needs user and password**. It is the only thing that
  puts the password back in front of a remote desktop left open in a browser tab — the unattended office PC, the
  phone forgotten on a table with the tab open. §5.3 already says the price in writing: *«whoever spends half an
  hour watching a video without touching anything is detached. The cost is small — reattaching is quick.»*
  `496b6dbd` did not change the rule; it made the code do what the rule said.
- ⛔ **And the 60-minute clock is the bigger surprise** (§5.3 third row, §4.8, `main.c` `abandon_round()`): it has
  **always** counted only the five gestures (`input_to_child()` → `presence_mark()`). ⇒ Someone watching for **60
  minutes** without touching has the **whole desktop closed** (`0x03`, open programs lost) — before `496b6dbd` too.
  Any «still here» below must feed **both** clocks, or it only moves the problem from 30 to 60 minutes.
- **The reconnection case (`speak_again()`, `src/rcp.c:8516`).** During a detach for silence (30 s without packets:
  a tunnel, a dead WiFi) the inactivity clock is not checked — it looks only at attached sessions. When the client
  comes back, `speak_again()` takes the slot back and sets the session active again; if the last gesture is
  **more than 30 minutes old**, the very next `rcp_time()` round sends `FAREWELL 0x02`. ⚠ It is saved only if the
  first thing that arrives is a gesture (`handle_input()` resets the clock before `rcp_time()` runs); after a drop
  the page's first bytes are usually a `REQUEST_KEY`, so in practice the watcher back from the tunnel gets the
  sign-in form at once.
  - **Simplest fix:** in `speak_again()` (which then takes `now`), when the slot is taken back and the clock is
    already past the ceiling, move `last_input` to `now − ceiling + GRACE` (GRACE ≈ 2 minutes): the user has two
    minutes to make a first gesture, and that gesture counts as usual. ⛔ **Bounded to a SHORT silence** (the
    detach lasted ≤ GRACE, from a new `detached_at` field): a tab frozen in the background (the browser freezes it
    after ~5 minutes, §5.3) on an abandoned desk must **not** get the grace — otherwise whoever sits at that desk an
    hour later clicks the tab, gets two minutes, moves the mouse and has the desktop **without the password**.
    Files: `src/rcp.c` and its twin `benches/rcp/rcp.c`, a section in `benches/01-b8-ban-test.c`. Effort: small
    (half a day with the test). Independent of the choice below; with B or D it is still needed for the first
    seconds after a drop.
- ❓ **The options:**
  - **A — keep it as specified.** Price: security unchanged (the best of the four); UX: the watcher signs in again
    every 30 minutes and loses the desktop at 60 — on Android Auto, while driving, that is a sign-in form on the
    car screen. Effort: none. Files: none (the release notes will say it when the documentation is written, at the end of the project).
  - **B — the page sends a «still watching» signal by itself**, only while the tab is **visible** (Page
    Visibility API) **and** the user has made a real gesture in the last N hours; the server counts it as a gesture
    for both clocks. Price: security — for N hours an unattended PC with the tab in front keeps the desktop open
    without a password, which is exactly the case §4.3 and §5.3 close; a phone is better off (its screen turns off,
    the tab goes hidden, the signal stops) but a car screen or a wall screen never hides. UX: invisible, the best.
    Effort: medium (~1 day + tests). Files: `RCP.md` (a new control message, e.g. `STILL_HERE`), `SPECS.md` §5.3,
    `src/page.html` (timer + visibility), `src/rcp.c`/`rcp.h` + twins (count it), `src/main.c` (a hook to
    `presence_mark()` for the 60-minute clock), `benches/01-b8-ban-test.c`, the page tests.
  - **C — an option to raise or switch off the limit.** ⭐ **Server-wide it already exists**: `--inactivity-s`
    (`0` = off) and `--abandon-s` (`0` = off), written in the log at start-up. A **per-user** setting does not
    exist. Price: security — whatever the administrator chooses, for **everyone** on that server (server-wide),
    or for the named users (per-user); UX: perfect for a kiosk or a dashboard machine, no help to a normal user on
    a normal server. Effort: server-wide **none** (only document it in the User/Technical Manual); per-user medium
    (a config file read at sign-in, the value carried into the session). Files (per-user): `src/main.c`,
    `src/rcp.c`/`rcp.h` + twins, the installer's config, `SPECS.md` §5.3, the manuals.
  - **D — the page warns at 28 minutes, with an «I am still here» button**, and the tap counts as a gesture for
    both clocks (the same new control message as B, sent only on a tap). Price: security — nearly unchanged: a
    **person** must be there and tap; an abandoned desk still locks at 30. UX: one tap every half hour; on Android
    Auto that is a dialog on the car screen while driving (one tap, but still a tap). Effort: medium (~1 day +
    tests); the page must know the server's ceiling, so the server announces it (e.g. a `SESSION` entry), or a
    changed `--inactivity-s` would make the warning come at the wrong time. Files: `RCP.md` (the message and the
    ceiling), `SPECS.md` §5.3, `src/page.html` (the warning, its countdown, the button), `src/rcp.c`/`rcp.h` +
    twins, `src/main.c` (the 60-minute hook), `benches/01-b8-ban-test.c`, the page tests, the User Manual.
  - **Recommendation: D, plus the bounded reconnection grace, plus C server-wide documented as it is.** D keeps
    the reason §5.3 exists (only a present person keeps the desktop) and turns «signed out without warning» into
    «one tap»; the grace removes the sign-in form after a short drop; and for a real wall dashboard the administrator
    already has `--inactivity-s 0 --abandon-s 0` on a server dedicated to it. B is the nicest to use but reopens
    the abandoned-desk hole for N hours; per-user C is work for a case the server-wide option already covers.
  - ⚠ And §4.3 has an expiry condition that applies here: the day REMOTIX gets a stronger sign-in (MFA, §1.7) the
    trade-offs change — a sign-in every 30 minutes would cost more, and a desktop lock would protect more.

### 11.44 🔸 The page's TCP listener: deadlines and a per-address cap (15 Oct 2026) — built, not yet on the boxes

> ⚠ Ported (25 Oct 2026): the page's TCP listener, deadlines and per-address cap (abandoned-attempt commit `3ed5091f`) are merged into `integrazione2` from `port-pagina` (`69843995`, with the child-flood test `f4837c27`). verification 28/28 on `4be3a981`, 24 Oct 2026; the live check with real browsers is still due (CHANGES-1.5.md, «Still open»).

- **The defect** (pre-login denial of service): `src/page.c` has 32 client slots and freed one only on activity
  of its socket — no deadline, no idle timeout, no keepalive, no per-address limit. 32 TCP connections that send
  nothing took every slot for ever, and nobody could load the login page. `[M]` 192.168.0.2, private server in a
  `--network none` container, HEAD da690451: with 32 idle connections a real `GET /` gets EOF, and still EOF 12 s
  later; the server says «already 32 TCP connections» and nothing else.
- **The cure**: each client has a birth time; **10 s** to finish TLS and send a whole request, **60 s** from
  accept to the last byte of the response (sized on `page.html`, ~907 KB: ≥ ~15 KB/s; 30 s would cut a
  ~200 kbit/s phone mid-page). `page_expired()` runs at every pass of the main loop, `page_wait_ms()` feeds the
  `poll` wait. At most **4** at once per `rcp_key_address()` key (IPv4 address / IPv6 /64), checked before
  anything else; when all 32 are taken the **oldest client without a whole request** is closed to make room
  (as `transport.c` evicts a login not yet begun). One summary line at most every 10 s.
- ⛔ **Not done**: refusing banned addresses at accept — §4.4-bis wants the banned owner to SEE the page and
  «attempts exhausted»; a refusal at accept is the silence it forbids.
- ⚠ What it does NOT stop: many addresses opening connections faster than the eviction turns them over make the
  page slower, not unreachable; 32 slow readers that each took a request hold their slots up to 60 s.
- `[M]` `benches/02-page-deadline-test.c` (includes `page.c`) 17/17; live on the new binary: GET while 32 idle are
  held → 200 (eviction), the 32 closed by the server at 10 s, GET after → 200, the 5th connection from one
  address closed at once.
- **And the `poll` array** (same day): `main.c`'s loop had a fixed 64 slots; the page alone can take 33, so with a
  raised `--session-cap` the children after the 28th were left out of the `poll` (frozen, in silence) by whoever
  held 32 page connections. The array is now allocated at start-up as 1 + `PAGE_MAX_DESCRIPTORS` (33) + 1 + 1 +
  `rcp_cap()`; `accept_page()` accepts at most 32 per call. `[M]` live with `--session-cap 40`: starts, same
  results; ⚠ a session count above 28 was not run.
- **After the review of 3ed5091f** (same day), two changes:
  1. *Slow readers could still lock it out*: eviction skipped clients writing a response, so 8 keys × 4
     connections that send `GET /` and then read almost nothing held all 32 slots. Now: at most **8** at once from
     one IPv6 /48 (as `transport.c`); and when the table is full, a writing client **≥ 5 s** into its response
     and **under 32 KB/s** can be evicted, the one with the most bytes left first.
  2. *60 s from accept cut slow phones* (under ~125 kbit/s, every time). Now no absolute limit while writing:
     closed after **15 s with no byte received**, or below **2 KB/s** on average after **20 s**.
  ⛔ Progress is what the peer ACKNOWLEDGED (`TCP_INFO` `tcpi_bytes_acked`), not what `SSL_write` handed to the
  kernel: `[M]` on loopback the kernel took 2.6 MB from a reader that had acknowledged 4 KB. Partial TLS writes
  are switched on so the fallback (`oresponse`, where `TCP_INFO` is missing) moves too. The «full» refusal now goes
  into the summary line instead of one log line each.
  ❓ **Not done, open**: serving `page.html` gzip-compressed (~907 KB → far less). The page is substituted per
  request (fingerprint, ban notice), so it would mean compressing per request or caching the not-banned page per
  fingerprint, and linking zlib directly: a new build and package dependency on 7 distros (`-lz`, `zlib.h` in the
  build images, the Debian/RPM/Arch dependency lists). Every browser REMOTIX supports sends
  `Accept-Encoding: gzip` over HTTPS; the plain page would stay as the fallback.
  ✅ **Decided — decisione dell'utente** (15 Oct 2026): YES, «inseriamo la libreria come dipendenza di remotix».
  zlib becomes a build and package dependency of REMOTIX; the shared not-banned page is compressed once per
  fingerprint and sent gzip when the request's `Accept-Encoding` allows it, the plain page otherwise.
  `[M]` `02-page-deadline-test` 26/26 (a slow reader held to the 15 s stall; 300 KB in 60 s kept, 100 KB closed;
  32 slow readers: a newcomer refused while they are young, a real GET served once they are 6 s old, exactly one
  evicted; the /48 key). Live, private server: 9th connection from 9 /64s of one /48 refused; with a 17 MB page
  (so slow readers really hold their slots) 32 slow readers → GET refused at 1 s, 200 at 6.5 s, the other 31
  closed at 15 s; a phone reading at 12 KB/s gets the whole 907 KB page in 74 s. ⚠ On loopback the kernel takes the
  whole 907 KB page at once, so the 12 KB/s phone would also have passed under 3ed5091f's 60 s rule: the 60 s
  regression is shown by the desk test, not by the live one.
- **Third review** (same day): the eviction is now by **fair share**, and the table has **128** slots.
  - *Measured hole*: «evict the globally oldest client without a request» let 8 IPv4 addresses doing bare TCP
    connects push out a real browser mid-handshake after 39 connects, in 4 ms; and «writers under 32 KB/s» let
    readers at 33 KB/s hold the table for ever.
  - *The rule*: a client's group is its IPv6 /48 (a real IPv6 peer) or its address. When full, the victim comes
    from the group holding the most slots, at random among its clients without a whole request or ≥ 5 s into a
    response at **any** speed; when every group holds ONE, the **oldest** goes (refusing there would be a cheap
    lockout: one slot each from 128 addresses, renewed every 10 s); the newcomer is refused only when its group
    would then hold MORE than the victim's. A stalled writer now has **60 s** (not 15) before it is closed:
    retransmission backoff, tunnels and handovers; when the table is full it is evictable at 5 s anyway.
  - Expired and evicted clients are closed with a reset (`SO_LINGER` {1, 0}), so the kernel does not keep their
    unsent data in an orphan socket; a response that ends normally keeps the gentle close. The «GET / from …» line
    is limited to 5 per address per 10 s, the rest counted in the summary line.
  - ⚠ **The price of the per-address caps — shared addresses.** Everyone behind ONE IPv4 address (a home or office
    NAT, a mobile carrier's CGNAT, a hotel or campus Wi-Fi) is ONE key: at most 4 page connections at once among
    them, and under attack their group is the first to lose slots. Everyone in one IPv6 /48 (a carrier that gives
    each customer a /64 from a shared /48) is ONE group of at most 8. A page load needs one connection at a time,
    so a few people behind one address still load it; a crowd behind one CGNAT address loading the page in the
    same second may see some loads refused and need a reload. The QUIC side has the same keys (§11.40).
  - `[M]` `02-page-deadline-test` 34/34 and the live re-check, in the commit message.
- **Fourth review** (same day): ⛔ the largest group was computed over EVICTABLE clients only, so 127 fresh
  writers from 32 addresses (GET, then read nothing) made a phone 5 s into its download the only candidate, and
  every newcomer evicted it — measured 1000/1000. Now the largest group counts every live client; the victim comes
  from a group of that size, preferring clients without a request, then writers ≥ 5 s in, then fresh writers;
  oldest-first only when every group holds one. The not-banned page is built once per fingerprint and shared
  read-only (it was ~907 KB per writing client plus five temporary copies per GET: ~116 MB for 128 slots); a
  banned visitor's page is still built per request (its remaining time is its own). The request-line budget
  refuses a 17th address instead of reusing an entry (from the page fuzzing), and the random pick uses
  `RAND_bytes`.

### 11.45 ✅ The encoder's padding on AMD: edge copies, or the encoder's own colour conversion (15 Oct 2026) — decided: A

> ⚠ Ported on port-varie (`19749144`, from `ceaf026f`; the bench case 5 of `benches/23-colors709-edge-test.c` is not ported, that file is not in this tree) and merged into `integrazione2` (`3614a853`), built and unit-tested there (25 Oct 2026): the encoder padding (edge copies past the canvas)

- **What padding is, in plain words.** The card encodes a picture a little bigger than the screen: the width and
  height are rounded up (H.264: to 16; HEVC on AMD: to 64 wide and 16 high). A 1080-row screen is encoded with
  1088 rows; the decoder is told to hide the extra 8. Those hidden rows still take part in the compression, so
  what is in them can leak into the last row or column you **do** see, on some decoders.
- **What we do since `ceaf026f`** (zero copy, `convert_on_gpu()` in `src/encoder.c`): in the same GPU step that
  turns the screen's RGB into the encoder's YUV, up to three more «layers» copy the last row, the last column
  and the corner pixel into the hidden strip. `REMOTIX_VPP_PADDING=1` is the default; `=0` turns them off.
- `[M]` **What `cd4260ff` measured on the real cards** (`benches/19-vulkan/19-padding.sh` and
  `19-padding-judge.py`, Intel iHD 25.2.3 and AMD radeonsi 25.0.7 on the RX 6800, H.264 and HEVC, 1920x1080 and
  3788x2022, 40 frames, the server loaded, ±5 %):
  - **=1**: the hidden strip is the edge, within 0–0.9 levels. **=0**: black (Intel HEVC) or garbage, 114–207
    levels away from the edge (both cards).
  - ⚠ With more than one layer **both drivers switch to another conversion engine**, so the visible picture
    changes too. On AMD with one layer the encoder converts the colours itself; with the layers the GPU's 3D
    engine does it with a shader. Against the CPU's reference (`colors709`): **brightness (luma) gets much
    closer**, 42–47 dB → 55–60 dB, on both cards; **colour (chroma)** is unchanged on Intel and **1–5 dB further
    on AMD**.
  - **Time per frame**: Intel the same. AMD **+1.5–3 %** at 3788x2022 (e.g. 12.1 → 12.5 ms) and **+6–12 %** at
    1080p (3.8 → 4.3 ms with H.264, 3.6 → 3.9 ms with HEVC) — well inside a 60 fps frame (16.7 ms).
- **What C would cost — read in the code.** C is **already what the code does, on every card**: `convert_on_gpu()`
  adds a layer only if the input pool (`pool_width`/`pool_height`, `vadirect.c`) is bigger than the canvas; when
  the canvas is already aligned there are zero layers, one picture, and on AMD the encoder's own conversion. So
  C costs nothing to build, and also changes nothing. And it rarely applies: 1920x1080 is never aligned (1080 is
  not a multiple of 16), nor is a browser-window size like 3788x2022; 3840x2160, 2560x1440 and 1280x720 are
  aligned in both codecs and already take the one-layer route today. (B, for comparison: a few lines in
  `open_vpp()` — set `vpp_padding_off` when the VA vendor string, `c->device.vendor`, names radeonsi and the
  variable is not set — plus `REMOTIX_VPP_PADDING=1` to force it back.)
- ❓ **The options:**
  - **A — keep `=1` on every driver** (what is built). Price: on AMD +1.5–3 % per frame at 4K and +6–12 % at
    1080p, and colour 1–5 dB further from the reference (brightness 10+ dB closer). Nothing to build.
    Verify: `19-padding.sh` rows `*-card-p1` on D128 and D129 — the judge must show the padding within ~1 level
    of the edge, the «⭐ VPP: the padding …» line in every log, never «refused»; then, live, F-011 /
    `chroma_bleed` green on Chrome and Firefox (`verify-round.sh` step 10, as §11.41 already asks).
  - **B — default `=0` on radeonsi only**, keeping the encoder's own conversion. Price: the hidden strip on AMD
    goes back to garbage (114–207 levels off), which some decoders smear into the last visible row/column — the
    very fault `ceaf026f` was written to remove; brightness back to 42–47 dB. Gains the 1.5–12 % back. A few
    lines to build, and one more rule that differs per vendor.
    Verify: a new `19-padding.sh` row with `REMOTIX_VPP_PADDING` **unset** (the script always sets it today):
    on D129 it must log the padding as off and match `*-card-p0`; on D128 it must match `*-card-p1`. Then live
    F-011 on an AMD box with Chrome and Firefox, to see whether the garbage actually shows.
  - **C — `=1` on radeonsi only when the canvas is not aligned.** Price: none — it is A as built (see above);
    choosing C means choosing A. Verify: add an aligned size to `19-padding.sh` (2560x1440 or 3840x2160): on
    both cards the log must have **no** «⭐ VPP: the padding» line and `*-card-p1` must be bit-identical to
    `*-card-p0` (judge PSNR p1/p0 = inf); the two unaligned sizes stay as in A.
  - **Recommendation: A.** The price is a fraction of a millisecond per frame on AMD, far inside the frame time,
    and buys a picture whose edge is clean on any decoder; B saves that fraction by bringing back a fault we can
    see in the numbers. The colour being 1–5 dB further is the one real cost: ⚠ not yet looked at by eye — if
    the live check on an AMD box shows a visible colour shift against the Intel box, this entry is reopened
    with B. ⏳ Not run on the boxes, not in a browser.
- ✅ **Decided — decisione dell'utente** (15 Oct 2026): **A**, keep `REMOTIX_VPP_PADDING=1` on every driver.

### 11.46 ✅ A right password on a full server: the page says «full», and so tells a guesser the password was right (15 Oct 2026) — decided: A

- **The situation, in plain words.** Someone types a user name and password. PAM says the password is **right**,
  but the server cannot give that login a desktop: all the desktops this server may hold are in use (the stage
  cap), the machine has no capacity left (budget, `0x06`), that user's previous desktop is still closing, the
  user directory did not answer, or the desktop could not be started. Since `91f6edb7` the page gets, at the
  fixed second, `FAREWELL` with `0x0E` (or `0x06`) **and a text** — «all the stages of this server are in use»,
  «retry in a few seconds» — and never `ADMITTED`.
- **The price.** A wrong password gets `REJECTED 0x07`; a right one on a full server gets `0x0E`/`0x06`. So
  whoever is guessing passwords learns **«this one was right»** while the server is full, without getting in.
  It is less than before `91f6edb7` — then the page could even see `ADMITTED` first and the farewell after — and
  it is the price `main.c` already declared in its box «AND THE FAREWELL GOES OUT HERE, AFTER THE VERDICT»
  («the declared price of not leaving them in front of a black page»), the same that a full session table
  (`slot_take()`, `0x0E`) pays. The ban of §4.4-bis still counts every wrong guess (three in five minutes, twelve
  hours), and a right password resets it as any login does.
- ❓ **The options:**
  - **A — keep it** (what is built). The owner reads why they cannot get in and that retrying helps; a guesser on
    a full server learns that a password is right (they still have to wait for a free desktop to use it, and the
    ban limits how many they can try). Nothing to build.
  - **B — answer `REJECTED 0x07` («wrong password»)** whenever PAM said yes but there is no desktop. Hides the
    fact completely, but **lies to the owner**: told the password is wrong, they retype a right one, may get
    banned for twelve hours by their own retries, or change a password that was fine. It is the confusion
    §11.39 removed for «the check was not made».
  - **C — send `0x0E` with no text.** The guesser still learns «not 0x07, so right» — the byte alone tells it —
    and the owner loses the «retry in a few seconds» / «all desktops in use» explanation. Saves nothing real.
  - **Recommendation: A.** B trades a real harm to the owner for hiding a fact that is only useful to a guesser
    while the server happens to be full; C hides nothing. ⏳ Waiting for the user's choice; `RCP.md` will be
    updated with the answer, at the end.
- ✅ **Decided — decisione dell'utente** (15 Oct 2026): **A**, keep it as it is (`FAREWELL` `0x0E`/`0x06` with
  its text).

### 11.47 ✅ A stranger locks the account with `pam_faillock`, and then the owner bans themselves (15 Oct 2026) — DECIDED B

> ⚠ Ported (25 Oct 2026): `rcp.c` `refusal_uncounted()` is merged into `integrazione2` from `port-rcp` (`a560aabf`, with `rcp_orphan_verdict`); the ban counters it feeds are those of §11.53 (`login-difese`). verification 28/28 on `4be3a981`, 24 Oct 2026; the live check with real browsers is still due (CHANGES-1.5.md, «Still open»).

*15 Oct 2026, from the holistic security review. Established by reading the code and `pam_faillock`'s documented
behaviour (`pam_faillock(8)`, `faillock.conf(5)`); ⚠ **not run live** — `[?]` until a bench measures it.*

- **The situation, in plain words.** On **Arch and Manjaro** the `remotix` PAM file (`src/remotix.pam.arch`) includes
  `system-remote-login`, and through it `pambase`'s `system-auth`, which has `pam_faillock` **on by default**: three
  wrong passwords within 15 minutes lock the **account** for 10 minutes (`deny=3`, `fail_interval=900`,
  `unlock_time=600`). This is the lock §11.17 relies on against guessing from many addresses. While the account is
  locked, `pam_faillock`'s `preauth` step refuses **even the right password**, and it refuses it with an ordinary
  `PAM_AUTH_ERR` (not `PAM_MAXTRIES`). `authentication.c` `why_no()` logs it as «PAM REFUSED», `rcp.c`
  `mark_failed()` counts it, and the page gets `REJECTED 0x07` — «incorrect username or password».
- **How it is abused.** §1.9-bis already says that REMOTIX's sliding window lets one address make **two tries every
  five minutes for ever** without being banned. That is more than enough to keep `pam_faillock` locked: three
  failures in 15 minutes lock it, and each failure recorded during the lock moves the unlock time forward. So a
  stranger who only knows (or guesses) the **user name** — no password needed, one address, no rotation — keeps the
  account locked as long as they like.
- **What the owner then lives.**
  1. They type the **right** password and read «incorrect username or password». They retype it twice more.
  2. Three PAM refusals from their address in five minutes: REMOTIX **bans their own address** (their whole /64 on
     IPv6) for **12 hours** (§1.9). From then on even after the lock ends they cannot connect from there.
  3. The lock is on the **account**, not on REMOTIX: for the lock's duration they are also refused at the
     **console** (if `login`/the display manager use `system-auth`/`system-local-login`, as on Arch), by **ssh** and by
     **sudo**. §11.17 wrote this price; what it did not write is that REMOTIX's own ban adds 12 hours on top, and
     that the owner is told their password is wrong.
- **Which distributions are concerned** (the four PAM files, `src/remotix.pam*`, and `packaging/`):

  | distribution | `remotix` file includes | faillock / tally2 by default |
  |---|---|---|
  | **Arch, Manjaro** | `system-remote-login` → `system-auth` | ⛔ **yes**, `pam_faillock` (`deny=3`, 15 min, 10 min) — `packaging/arch/PKGBUILD` notes it |
  | Fedora, RHEL, Rocky, Alma | `password-auth` (sshd's file, line by line) | no — only if the administrator runs `authselect enable-feature with-faillock` |
  | openSUSE Leap, Tumbleweed | `common-auth` (sshd's file) | no — only with `pam-config --add --faillock` |
  | Debian, Ubuntu, Mint | `@include common-auth` (sshd's file) | no — only if the administrator adds the lines |

  None of the files names `pam_faillock` or `pam_tally2` directly; `pam_tally2` was removed from Linux-PAM in 1.5.0
  (2020) and no supported distribution ships it. ⇒ Out of the box, **only Arch/Manjaro** has the problem; on the
  others it appears the day the administrator follows the manual's §11.17 how-to — so the same manual must say it.
- **What is NOT in question.** The «mirror the system's authentication» rule (§10.18, D3), the ban rule (§1.9,
  §1.9-bis) and «`0x07` only for PAM's no» (§11.39) stay as they are in A and B.
- ❓ **The options:**
  - **A — document only.** The manual says: on Arch the account locks after three wrong passwords; if REMOTIX says
    «incorrect password» and you are sure it is right, **stop after the first retry**, wait 10 minutes or run
    `faillock --user <name> --reset` as root, and use the unblock command (§1.9) if already banned; and that a
    stranger can keep the account locked (§11.17). Price: the owner reads «wrong password» for a right one — the
    wrong diagnosis §11.39 removed for another case — and, under attack, still bans themselves for 12 hours. Nothing
    to build.
  - **B — the helper recognises «refused while `pam_faillock` had the account locked» and REMOTIX does not count
    it**; the wire is unchanged (`REJECTED 0x07`, same fixed second), so a guesser learns nothing new. How: after a
    PAM refusal the helper (root, §11.11) reads the user's tally file (`/run/faillock/<user>`, the `dir` of
    `faillock.conf`) and applies `deny`, `fail_interval`, `unlock_time` from `faillock.conf` — the same judgement
    `pam_faillock preauth` makes — or runs `faillock --user <name>`; if the account was locked **before** this
    attempt, the verdict to `rcp.c` is «refused, locked» and `refusal_is_ours`-like code does not call
    `mark_failed()`. ⚠ `PAM_MAXTRIES` cannot be used: `pam_faillock` does not return it. ⚠ Reading the
    conversation's «The account is locked…» message is not enough either: it is translated, and absent with the
    `silent` option. Price: some code in the helper (a tally-file reader, or a call to `faillock`, plus
    `faillock.conf` parsing, ~100–150 lines) and a bench on an Arch box; it reads a file format that is
    `pam_faillock`'s, not a public API (stable since 2010, but ours to follow); module options written **on the
    `pam_faillock.so` line** instead of in `faillock.conf` would be missed (Arch and authselect use
    `faillock.conf`). While the lock lasts, the stranger's tries are not counted either — they could never succeed
    (the right password is refused too), and §1.9-bis already lets them keep the lock without a ban, so nothing is
    lost. What B does **not** fix: the account stays locked and the owner still reads «incorrect password»; it
    removes the 12-hour ban on top.
  - **C — ship REMOTIX's PAM files without faillock**, leaving the choice to the administrator. On Arch it means
    **not** including `system-remote-login`/`system-auth` for `auth`, and rewriting the stack by hand
    (`pam_unix`, `pam_systemd_home`, `pam_env`…). Price: ⛔ it breaks §10.18 (D3, «REMOTIX must mirror PAM»,
    the user's own words); it drops the only defence §11.17 chose against guessing from many addresses; an
    administrator who **turned faillock on** elsewhere would see it not apply to REMOTIX — and REMOTIX would become
    the one open door for a many-address guesser while ssh is locked. On the other three families it changes
    nothing by default (faillock is already off there).
  - **D — detect the lock (as in B) and answer `0x0E` with a text «account temporarily locked, retry later»**, not
    counted. The owner learns the real cause at once. Price: ⛔ it **reveals that the user name exists** —
    `pam_faillock` ignores unknown users, so only a real account can ever be «locked» — and §4.4 forbids exactly
    that oracle (§11.39: «no such user» must look like «wrong password»); it also tells a stranger their lock is
    working. Needs `RCP.md` and the page's text, and every RCP reader to accept `0x0E` in `REJECTED` for this case.
  - **Recommendation: B, with A's paragraph in the manual.** B removes the part REMOTIX adds — the owner banning
    their own address for 12 hours with the right password — without changing the wire, without telling a guesser
    anything, and without leaving D3; the remaining harm (the account locked for a while) is `pam_faillock`'s own,
    already the administrator's choice in §11.17, and the manual says how to undo it. C costs a ruling the user
    gave in so many words; D costs the user-name oracle.
- ✅ **Decided — decisione dell'utente** (15 Oct 2026): **B**. Built the same day:
  - **How the lock is told apart** — not the tally file, not `faillock.conf`: `pam_faillock preauth` itself says
    «The account is locked due to N failed logins.» (`PAM_TEXT_INFO`) **before** the password is asked, and only
    when the account is locked. `authentication.c` (`rcp_authenticate_judged()`) answers «refused, locked» only for
    that line before the prompt **and** `PAM_AUTH_ERR`; the helper's outcome byte carries it as `2`
    (`1` alone is still «yes»). English is safe: the program never calls `setlocale()`. Absent line (translation,
    `silent`, Fedora's authselect) ⇒ an ordinary no, counted as before — the failure is the old behaviour.
    `[M]` 15 Oct 2026, `t17/arch-xfce` (pam 1.7.3, pambase 20260616), our `remotix.pam.arch`, the real
    `authentication.c` linked to Arch's libpam: right password and wrong one while locked ⇒ `2`; not locked,
    unknown user, `root` (denied-users), `silent` in `faillock.conf` ⇒ `0`; after `faillock --reset` ⇒ `1`.
    ⚠ Measured too: on pam 1.7.3 a wrong password **during** the lock adds no tally record (the lock is not
    pushed forward); the stranger renews it with failures after it ends.
  - ⛔ **Not counted only for a key that logged in during the last 30 days** (`good_recent()`, as the reserved
    PAM places) — `rcp.c` `refusal_uncounted()`, for live sessions and orphans. Reason, found while building it:
    only a real account can be locked, so «not counted» for anyone would be a **user-name oracle** (lock it
    with 2 + 1 tries over five minutes, §1.9-bis, then see that further tries stop banning). A stranger's key
    counts exactly as before; the owner from home or office no longer bans themselves. ⚠ The owner from a NEW
    address while locked still is counted (the 30-day table is in memory, 64 keys).
  - ⭐ The mark of the lock belongs to ONE delivery: `rcp_orphan_verdict()` now receives the ticket (from `transport_verdict_from()`) and
    `refusal_uncounted()` compares it on both roads, with no «ticket 0 matches any mark» exception.
  - Unchanged: the wire (`REJECTED 0x07`, the fixed second), the ban check before PAM, the 3 checks in flight
    per address. Desk test `benches/01-b8-faillock-test.c` (row «rcp faillock (C)»), 18/18; on 5843b5b6
    1, 7, 9, 10, 15, 18 red. The manual paragraph (option A's text) is written at the end.

### 11.48 ✅ The stress bench's client browsers do not share the boxes' card (16 Oct 2026) — DECIDED B

> ⚠ Ported (25 Oct 2026): the page probe that retries at 320×240 (abandoned-attempt commit `4cfdd4a8`) is merged into `integrazione2` from `port-pagina` (`ba4c6204`). verification 28/28 on `4be3a981`, 24 Oct 2026; the live check with real browsers is still due (CHANGES-1.5.md, «Still open»).

- **The problem, in plain words.** The stress bench runs the fake users' browsers (Firefox, Chrome) and their small
  desktop (labwc) on the test server itself. Since `fd8ada94` (15 Oct) they were pinned to the **Intel** card — the
  same card the boxes use to draw their desktops and for REMOTIX's capture and encoding. `[M]` Night run
  `20261015-180010`: gnome broke at 2 users with the clients' GPU work sitting on the boxes' Intel (and the night
  before, `20261015-005455`, Chrome had landed on the RX 6800 by accident). The bench was measuring the clients'
  load together with the product's.
- ✅ **Decided 16 Oct 2026, decisione dell'utente: B** — the client browsers and their labwc go on **another card**
  of the server, never on the boxes' one. This overrides checklist B1.12's «clients on the Intel».
- **What is built** (`16-climb.py`): `--client-card auto` (default) = the card the box does **not** use (box on the
  Intel ⇒ clients on the RX 6800 `0000:03:00.0`; box on the RX 6800 ⇒ clients on the Intel); the box's own card
  is refused (BLOCKED, code 3), and so is a server with no second card. The node goes to Chrome
  (`--render-node-override`, `DRI_PRIME`, `MESA_VK_DEVICE_SELECT`) and to `16-compositors.sh`
  (`REMOTIX_16_RENDER`). level.json `browser_cards` now says `client_card`, `client_pci`, `box_pci`,
  `off_client_card` and `on_box_card`; ⛔ any client process seen on the box's card (16-resources
  `gpu_processes`) makes the level **«?»** («CLIENT ON THE BOX'S CARD»), which stops the climb like an unreadable
  class. A GPU-busy check in `host_quiet` was **not** added: the client-on-the-box's-card check covers the case seen;
  foreign GPU users are not attributed by the meter today.
- ⚠ Price: the clients now draw on the RX 6800 (radeonsi) instead of the Intel, so client-side numbers are not
  comparable one-to-one with the runs before 16 Oct.
- ⛔ **Found on the first run** (`[M]` 16 Oct 2026, `misure/runner/stress79/20261016-052246`, gnome level-01):
  Firefox 153 ESR on the RX 6800 picks **VA-API** for WebCodecs H.264 and the page's 64×48 codec probe fails there
  (FFmpeg «avcodec_send_packet error: Invalid data found», `EncodingError`); HEVC `isConfigSupported` is false ⇒ the
  page sends no codec, the server ends with `NOTHING_IN_COMMON`, every Firefox user is refused. On the Intel the
  same Firefox decodes H.264 in **software** and passes. ⇒ The bench gives the clients' Firefox on the RX 6800
  `media.hardware-video-decoding.enabled = false` (`REMOTIX_FF_PREFS`), i.e. the same software decoding as before.
  ✅ **Product question, closed (16 Oct 2026):** a real user with Firefox on an AMD card would hit the same refusal.
  `[M]` Cause: the RX 6800's VA-API decoder takes no H.264 picture **below 64 rows** (64×48 and 128×48 fail;
  64×64, 64×96, 320×240 … 1920×1080 paint; prefer-software paints all; HEVC refused at every size, as on the
  Intel). Fix `4cfdd4a8`: when the 64×48 probe does not paint, the page probes again at 320×240 (§4.5 minimum
  canvas), same pixel test; bench 22 J1–J5. `[M]` gnome box, Firefox on the RX 6800 in hardware decode: main's
  page refused, the fix F-013 PASS (3445 VA-API frames); F-013 Firefox+Chrome pass 4. ⇒ the bench's
  software-decode override is removed.
- ✅ **Extended to the functional suite** (coordinator, 16 Oct 2026, `3af4966f`): the suite's client browsers render
  on the card that does not encode, like the stress bench (`86f99e72`) — `15-compositors.sh` puts its labwc on the
  server's other card (`REMOTIX_15_RENDER` chooses it; it had renderD128, the Intel, by hand), `15-round.py` pins
  Chrome there. Why: F-013 Firefox «STILL IMAGE» on all four desktops, split and pre-split alike. `[M]` 16 Oct 2026,
  private boxes (`15-suite/15-private-one.sh`), Firefox's WebCodecs H.264 in **software** on both cards («Using
  preferred software codec h264», so hardware vs software decoding is not the variable):

  | where the clients' labwc draws | load | decode → callback median | picture age | photos in 60 s |
  |---|---|---|---|---|
  | Intel (the boxes' card), 1 box | 8 | 189 ms | 652 ms | 28 |
  | RX 6800, 1 box | 19 | 4 ms | 0 | 61 |
  | Intel, 2 boxes at once | ~5 | 47 / 297 ms | 234 / 830 ms | 33 / 26 |
  | RX 6800, 2 boxes at once | ~5 | 5 / 4 ms | 0 | 61 / 57 |
  | Intel, the failing 4-desktop rounds | 15–25 | 1152 ms | 2.3 s | 18 in 49 s |

  The decoded frame reaches the glass through the client compositor's GPU, which on the Intel queues behind the
  boxes' 4K encoding and desktops. Chrome on the RX 6800 with the pins: F-013 PASS (61 photos).

### 11.49 ✅ The stress bench's memory rule on KDE: the «unchanged» filter's capped reference is accepted (16 Oct 2026) — DECIDED A

- **The problem, in plain words.** On KDE the product keeps one reference picture per session for the
  «unchanged» filter (`src/unchanged.h`, `2a02376e`): it grows with the largest damaged area seen and is **capped**
  at a quarter of 4K × 4 bytes = **7.9 MB per session** (`UC_MAX_PIXELS`). `[M]` Night run `20261015-180010`, kde
  level-01 and its repeat: `remotix` PSS 56 → 62 MB and 53 → 60 MB (+12 %), in steps in the first half, then flat
  (second half +0–3 %/hour). The §9 memory row (> 5 % flagged, > 10 % significant ⇒ the climb stops) stopped KDE at
  1 user on a cost that is bounded by construction.
- ✅ **Decided 16 Oct 2026, decisione dell'utente: A** — accept the capped cost and correct the bench rule for
  this case. §9 is frozen: the thresholds (5 / 15 %, half band 10 %) do **not** change; what changes is what is
  counted as growth, recorded as **memory rule v2** (`16-classify.py` `MEMORY_RULE_VERSION = 2`, field
  `rule_version` in each memory entry, a pointer under the §9 table of `phases/16-stress-and-capacity.md`).
- **The rule v2.** Only for the `remotix` enclosure, only on kde (`UC_DESKTOPS`), not for xrdp, and **only if the
  growth has stopped** (the existing «keeps going» test on the second half is false): growth judged =
  (growth − 7.9 MB × the sessions of the stretch, never below 0) / start. Whatever exceeds the cap counts in full.
  A growth that keeps going is judged whole, with the note «allowance NOT applied» — a real leak is still caught.
  The raw growth, the sessions and the allowance are recorded (`raw_growth_pct`, `uc_sessions`,
  `uc_allowance_mb`). Self-test (`--certify`, 49/49): kde step then flat ⇒ GREEN; the same on GNOME ⇒ significant
  DEGRADED; kde steady rise ⇒ FAIL; kde stopped step beyond the cap ⇒ DEGRADED. Re-judged with v2, last night's
  kde level-01 is GREEN on memory (its repeat stays FAIL for the lost key, the known KWin defect).

### 11.50 ✅ §11.11: the shape of the split, the closed list, and the user's choices (16 Oct 2026)

> ⚠ In the branch `finale`, NOT in `integrazione2` (25 Oct 2026): the whole section is merged from `rootside-completo` (`ae8cae45`; D1-D7 plus installer and packages), OFF by default (the server stays one process unless `REMOTIX_SPLIT_EXPERIMENTAL=1`). Whether it is ON or OFF in 1.5 waits for the user's decision D1; see CHANGES-1.5.md.
>
> ⭐ **D3 / D4b, from `port-rootside-D3`; approved on `rootside-completo` and merged in `finale` (`verifica-rami` on `finale` is queued). Active even with the split OFF:**
> - The PAM dispatcher is **re-executed** (`/proc/self/exe --pam-helper`, fresh memory image, descriptors above 3 closed) and
>   **restarted with a doubling pause** (1 s … 60 s; loud after 5 deaths in a row) by `helper_expired()`, the watchdog.
>   While it is down the logins are refused as ours.
> - **Root form** (`helper_turn_on_root`, `helper_ask_bare`, `HelperOutcome`): every request ends in ONE callback: 1 admitted, 0
>   refused, 2 refused while `pam_faillock` held the account, **3 not checked** (the dispatcher's cap of 2×16, a failed `fork`
>   there, the dispatcher dead or down — our defect, never counted), **4 expired** (no answer in 8 s: it COUNTS as a failed
>   attempt, the 24 Oct 2026 decision).
> - **The synchronous PAM fallback is GONE** (a deliberate change): with no helper, or its hook missing, the login is refused
>   `0x0E`, not counted, booking released (`login_release`); `hook_verify`/`rcp_hooks.verify` removed, and `rcp_refusal_unchecked(ticket)`
>   brackets the delivery of «not checked» so `rcp.c` turns it into `refusal_is_ours` (same road as `rcp_verdict_lost`).
>   In the single-process product «not checked» also travels as `lost=true`.
> 🔸 Phase F (packaging) from `port-rootside-pacch`; approved on `rootside-completo`, merged in `finale` (queued for `verifica-rami`), **OFF by default behind one switch** (debian: `REMOTIX_SPLIT=1`, passed through by `build-deb.sh`; rpm: `--with split`, `build-rpm.sh` with `RX_SPLIT=1`; Arch: `REMOTIX_SPLIT=1`, passed by `packaging/arch/build.sh`; any other value, or none, leaves the pieces OFF): the system user `remotix` (`sysusers`), `remotix-net-move` (the 1.0 → 1.5 move of `certificates/` and `ban` into `/var/lib/remotix/net`), the split units and tmpfiles (`*.split`), the rpm SELinux domain (`remotix.{te,fc}.split`), the Arch install script. **Inert today** (no build installs them without the switch; the install scripts' blocks run only if `remotix-net-move` is in the package): the new files, the guards in `postinst` / `%post` / `remotix.install`, the extra `rm`/`rmdir` of `net/` at purge. **Would change today's behaviour, therefore behind the switch**: creating the user, moving the certificates and the ban file (today's 1.5 server reads the old paths and would regenerate its certificate and `quic-secret`), the units' `--certificates` / `--ban-file` on `net/`, `/var/lib/remotix` 0755 (0700 today), the SELinux domain `remotix_net_t`, `daemon-reload` and `tmpfiles --create` in the scripts. No hardening in the units by design (the desktops inherit what the unit restricts): the network side hardens itself with `walls.c` (phase C, `walls.c`, in this tree). `remotix-net-move --back` (the reverse, for a downgrade or removal) leaves the service STOPPED after a downgrade: the marker `/run/remotix/was-running` (written if the unit was active or activating) says whether it was running, so whoever does the downgrade (or the installer engine, later) can start it again; Arch calls it only from `pre_remove`, on a downgrade the administrator runs it by hand.

- **The user's rulings** (16 Oct 2026, to the questions put after the inventory of the root operations — seven
  reports, one per area: network side, PAM, desktop birth, the per-session child, cards and input, packaging,
  benches): *«Restano vivi»* — when the network side dies or restarts, the open desktops stay alive and their owners
  get back in, as after a restart today; *«Tolto con --purge»* — `uninstall --purge` removes the `remotix` user,
  a plain uninstall keeps it (the distributions' rule for system users). The deadline: everything closed by Sunday
  18 Oct 2026 evening, the server working without pause and five lanes in parallel.
- **The process tree.** systemd starts `remotix` as today (same unit, same `ExecStart`, no new unit to enable,
  §10.12 stays true): that process is the **root side** and the unit's main PID. Before anything else it binds the
  UDP and TCP sockets of the port (so a port below 1024 needs no capability later), runs the codec probe (as today,
  `child_video_capabilities()`, so a card only root can open behaves as in 1.0), starts the PAM helper (§1.10,
  unchanged code, now its child), creates one `SOCK_SEQPACKET` pair with `SO_PASSCRED`, and forks the **network
  side**. In that fork, still root, it applies the network side's walls and then `execve(/proc/self/exe
  --network-side …)`: fd 3 = the root channel, fd 4 = UDP, fd 5 = TCP. The desktops' children are forked by the
  root side, never by the network side, so no wall of the network side reaches a desktop (the reason of §11.11:
  `sudo apt install` in the remote desktop keeps working). Rejected: a second systemd unit for the network side —
  the walls would be declarative, but the port, the ordering, the upgrade and four packagings would all change for
  the same result.
- **The network side's walls** (all applied by the root side in the fork, before `execve`; any failure ⇒ the
  network side is not started and the reason is logged, never a silent fallback): a new mount namespace where the
  whole tree is read-only (`mount_setattr(AT_RECURSIVE, MOUNT_ATTR_RDONLY)`) except `/var/lib/remotix/net` and
  `/run/remotix/net`, a private `/tmp`; `setgroups(0, NULL)`, `setgid`/`setuid(remotix)`, checked with
  `getresuid`/`getresgid` and an empty capability set; `PR_SET_NO_NEW_PRIVS`; on SELinux, `setexeccon` to
  `remotix_net_t`. No supplementary group: the network side never opens a card (the probe stays on the root side).
  `/proc` is not hidden (the rediscovery of §T7 reads it). The TLS key, certificates, ban table and QUIC secret live
  only in the network side.
- **Files.** `/var/lib/remotix` stays root 0755 (render grants, group enrolments, engine state). New
  `/var/lib/remotix/net` `remotix:remotix` 0700 with `certificates/` (and its `quic-secret`) and `ban`; the units
  pass `--certificates /var/lib/remotix/net/certificates --ban-file /var/lib/remotix/net/ban`. `/run/remotix/net`
  `remotix` 0700 (tmpfiles) for the bench's command socket. The user: `sysusers.d` `u remotix - "REMOTIX network
  side" / /usr/sbin/nologin`, no groups. The upgrade from 1.0 moves `certificates/` and `ban` into `net/` and
  gives them to `remotix` **before** the restart (a ban file it cannot read stops the server, a root-owned
  `quic-secret` is silently replaced by a per-run secret — both found by the inventory).
- **The closed list** (`src/rootside_proto.h`): fixed-size messages, header `{magic "RXR1", version 1, kind,
  request id}`, exact length checked; the root side checks on every message the kernel's `SCM_CREDENTIALS` (uid =
  `remotix`, pid = the network side it forked). Network side → root side, and nothing else:
  1. `AUTH {user, password, rhost}` → `VERDICT {outcome, grant}` — the root side asks its PAM helper; on a yes it
     mints a **grant**: 16 random bytes, single use, 30 s, bound to (user, rhost).
  2. `SPAWN {grant, canvas w×h}` → `SPAWNED {serial, pid, uid, gid}` + the child's socket end (`SCM_RIGHTS`, the
     only fd that ever crosses), or `SPAWN_REFUSED {reason}`. Enrolment in the card group, the render grant,
     `pam_open_session`, the SELinux level, the uid drop and the `execve` happen inside it, as today in
     `children_ensure_from()`. Every option of the child (`--journal`, the encoding route, the render node, the
     phase-9 flags, the survey dir) comes from the root side's own argv, never from the request.
  3. `CLOSE_ORPHAN {user}` → as `SPAWN`: the one birth without a password, for a desktop found again (main.c's
     abandonment clock); allowed only when the root side itself finds in `/run/systemd/sessions/` a live session
     of that uid with `SERVICE=remotix` and no child of its own for it.
  4. `SIGNAL {serial, TERM|KILL}` — only to children the root side forked.
  Root side → network side, events: `READY {codec probe result}` (first message), `CHILD_EXITED {serial, wait
  status}` (the root side reaps, then removes the render grant itself — it never waits to be told). The bench's
  SIGUSR1/SIGUSR2 to the main PID are forwarded to the children by the root side itself.
- **The root side's own bounds** (a hijacked network side is the attacker it is built against): at most 16 `AUTH`
  in flight and 10 per second (burst 20), above that refused without asking PAM; uid 0, names in
  `/etc/remotix/denied-users` and unknown names refused before PAM; children ≤ the cap of its own argv; any
  malformed or unknown message ⇒ logged, the channel closed, the network side killed and started again. The root
  side is single-threaded and links no GLib/GDBus in the code that forks (the inventory found GDBus's worker thread
  alive at today's fork, `rediscover.c`, against `child.c`'s comment).
- **Deaths.** The network side dies ⇒ the root side logs it, the children see EOF on their socket and exit, the
  desktops stay alive (the user's ruling), the root side starts the network side again (1 s, 2 s, 4 s … 30 s) and
  the new one finds the desktops again (T7). The root side dies ⇒ the network side sees EOF and exits, systemd
  restarts the unit, desktops alive. Stop/restart: SIGTERM reaches the root side (main PID, `KillMode=mixed`), which
  passes it to the network side, waits for its farewell (0x0c) up to 5 s, then exits.
- **Removed**: the synchronous PAM fallback in the network process (`webtransport.c` `hook_verify` →
  `authentication.c`): as `remotix` it would refuse every right password and count it towards the ban.
  ⭐ *Done in step D4b on `port-rootside-D3`, in the single-process product too (not only in the network side): with no helper
  the login is `0x0E`, not counted.*
- **Kept byte-identical** (benches read them): the log lines «PAM helper started: pid N», «child spawned for…»,
  «I AM MAKING IT BE BORN», «is in the card's groups», «FOUND AGAIN», «graphical session is over», under the same
  `-t remotix`.
- **The lanes** (16 Oct 2026, five agents at once, merged on `main` one at a time): (1) root side and children's
  birth (`rootside.c`, the root half of `child.c`, `render_grant.c`, helper under it); (2) network side (`main.c`,
  `transport.c`, `page.c`, `certificates.c`, `rcp.c`/`webtransport.c`, the network half of `child.c` through the
  `rootside.h` client calls); (3) packaging and installer (sysusers, tmpfiles, units' args, upgrade, purge, Go
  engine and its tests); (4) SELinux (`remotix_net_t`, the root side's new needs, the four rpm distributions);
  (5) benches (boxes started like the package, the ~30 benches that assume one root process, `rxtest privsep`, a
  fuzz harness for the root side's parser).
- **Choices taken while building it** (16 Oct 2026; «coord.» = the coordinator, «agent» = the lane or fixer
  that built it and wrote the evidence; the user's rulings are above). The source the rebuilt manual cites.
  - **One unit**, the root side its main PID (coord., the plan): no second unit for the network side — port,
    ordering, upgrade and four packagings would all change for the same walls (`dd2c1129`).
  - **SPAWN is a synchronous wait** of the network side's loop, ≤ `SPAWN_WAIT_MS` 15 s (agent, review 2 L4,
    `44f0316e`; first 5 s). Measured: 0–3 ms in a container with a real `usermod` enrolment (`e15c0893`), 1–14 ms
    on the boxes (coord.); both sides log it («SPAWNED after N ms», «the birth for «u» took N ms»).
  - **«Not checked» is delivered at once** as `0x0E` at the fixed second, never counted towards the ban (coord.,
    reversing lane 1's wait for the 12 s VERDICT_CAP; `5a1d8852`, seam `01-b8-unchecked-test.c`).
  - **CLOSE_ORPHAN births a close-only child** (agent, review 1 finding 1, `13c316cb`): `--close-only` written
    by the root side, never by the request; no stage, no frame, no input or clipboard, only «end the session»
    (and SHUT_DOWN, «who are you»), exit after the attempt or after 30 s; no card-group enrolment and no render
    grant for it (review 2 L2, `44f0316e`); for a login it is «closing», never «already served» (L3). Rejected:
    the root side closing the desktop itself — outside the user's bus it could only kill. A `closing` logind
    session with a process left in its scope counts as live (lane 4, `8c0a3aa8`, alma10 enforcing).
  - **CLOSE_ORPHAN's own bounds** (agent, review 2 M1, `fd3f9900`): 2/s burst 5 before any work, one per uid per
    30 s; the AUTH bounds come before the denied file and NSS too (review 1 finding 6, `9b7d8271`); refusal lines
    at most one a second with the count.
  - **A dead network side's children are killed** (agent, review 1 findings 2 and 10, `2134b602`): 5 s to leave on
    the EOF, then SIGTERM, then SIGKILL every 3 s until reaped — only that generation's; the desktops survive. A
    network side that closed its channel gets SIGKILL 3 s after SIGTERM; a send that says EPIPE/ECONNRESET kills
    it (review 2 M2, `fd3f9900`).
  - **Signals reset in every fork** of the root side's code (agent, finding 3, `7701f16d`): all blocked across
    `fork()`, the copy back to the defaults, SIGPIPE ignored as 1.0 passed it on.
  - **CHILD_EXITED is never lost** (agent, finding 4, `a7a01d02`): an outbox of 4 × the cap, sent again every round
    and on POLLOUT; the network side dispatches it at once and queues only VERDICTs (4096).
  - **RLIMIT_NPROC 128** for the network user (agent, review 2 L1, `5fab2954`: 64; raised to 128 on 16 Oct 2026
    by the coordinator after lane 1's review, `ef67682b` — every network side of the uid counts, `[M]` 4 threads each on the
    boxes, GLib's pool up to ~14 more, and a failed thread creation aborts: a restart loop), and **before each network-side
    start a copy as `remotix` does `kill(-1, SIGKILL)`** (`0eec7950`) — ⛔ nothing else may ever run as `remotix`.
    🔸 Known (review 4 B, finding 7, 16 Oct 2026, the coordinator): RLIMIT_NPROC counts per REAL uid, so two
    REMOTIX servers whose network sides share one uid share the 128 — ONE REMOTIX per network uid; a bench that
    runs a second server and needs the headroom passes its own `--network-user`. Not measured with two.
  - **The walls, beyond the first list** (agent, review 3, `7095d83f`; `2b43e8f0`; `65d915c6`): mounts SLAVES of
    the host's (an unmount reaches in, nothing is pinned; a later host mount arrives without RDONLY — the choice of
    systemd's ProtectSystem=); the tree also nosuid and nodev; `/dev` a read-only tmpfs with null, zero, full,
    random, urandom only; a raw-BPF seccomp filter — `unshare`/`clone` with CLONE_NEWUSER EPERM, `clone3` ENOSYS,
    x32 or a foreign arch EPERM (x86_64 and aarch64 only; another architecture does not start the network side);
    the root side's folder kept as cwd (a relative `--page` resolves as in 1.0); a state or run dir under `/tmp`
    refused by name (lane 2).
  - **`--certificates`/`--ban-file` outside `--network-state-dir` refuse the start** (agent, review 3 F6,
    `c05eddca`), with the fix in the line; the engine flags a REMOTIX_OPTIONS drop-in that does it (RX-NETUSER-003).
  - **`remotix-net-move` sets no owner and no mode** (agent, review 3 F1, `02d731c5`): a root `find|chown/chmod`
    over a remotix-owned tree races a live old network side; tmpfiles' `Z` and new `z` lines do it, every family
    calling `systemd-tmpfiles --create` after the move and before the restart. A `page.pem`/`page.key` kept as a
    link (letsencrypt) is said by the move, the engine (RX-NETUSER-003) and the network side, with the fix
    (`791eb648`).
  - **`--bench-assume-codec`** exists only under `make BENCH=1` (coord., lane 4's need; `6fe84ea1`): the VMs have no
    encoding card, and without it no login reached PAM in the enforcing check; absent from the package binary.
  - **SELinux** `remotix_net_t` for the network side, `remotix_t` stays the root side (lane 4, `5198dd67`), with
    `process2 { nnp_transition nosuid_transition }` — without `nosuid_transition` the exec of the network side
    fails EPERM (the walls' mount counts as nosuid) — and the rules measured enforcing on fedora44, alma10,
    tumbleweed, leap16 (`60555cb5`).
  - **B7 adapted, the product's log budget kept** (coord., 16 Oct): the pre-login lines are a stranger's to
    trigger and the budget (`16b75f33`) exists for them; B7 waits for the budget's summary and reruns the case in
    a fresh window (`ef1ca4c8`).
  - **What the split costs, against 1.0** (agent, `[M]` 16 Oct 2026, `benches/24-privsep-cost.sh` run
    `20261016-113915`: one private xfce box, the two versions interleaved 4 rounds, load 13–23; paired 1.5 − 1.0):
    warm login to the first frame −98 ms, cold −145 ms (the fixed-second tick of `757bf688`, not the split); the
    birth (PAM asked → child spawned) +6 ms, within noise; SESSION → first frame 0; motion 61.5 fps both; idle
    CPU 0.00–0.07 % both; idle server memory +10 MB (root side 9.0 + network side 16.2 MB against 15.2) and the
    PAM helper +5.5 MB (a fresh image, not a fork). The user's two numbers (SPECS §3.1) are not worse.
  - **The walls, after lane 4's network-side review** (coord., 16 Oct 2026, `l4-net-review`): the seccomp filter
    also refuses io_uring (ENOSYS), userfaultfd, perf_event_open, bpf, keyctl/add_key/request_key, ptrace and
    ioctl TIOCSTI/TIOCLINUX (EPERM) — none used by the network side, all stepping stones of a local kernel exploit
    whatever the distribution's sysctls; the two writable directories are noexec (`make test-walls` as root
    24/24). 🔸 **Known limit, 1.6 candidate**: abstract unix sockets (X11's `@/tmp/.X11-unix/X0`, other
    services') and world-accessible path sockets stay reachable from the network side — neither the mount
    namespace nor the read-only tree isolates them. On SELinux `remotix_net_t` may connect only to itself; on
    Debian, Ubuntu and Arch only the peer services' own checks (SO_PEERCRED, cookies) stand. The cure, Landlock's
    `LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET` (+ `SIGNAL`, kernel ≥ 6.12), is a new isolation layer: **not in 1.5**
    (too late before the release), 1.6. The network side's environment reduced to a minimal list is for 1.5,
    handed to lane 1 (`rootside.c`'s `execve`).
  - **The root side after lane 1's pre-release review** (agent, 16 Oct 2026; tested by two `rootside-dispatch`
    seeds red before and green after, and by the fuzz below):
    - **Grants belong to one network side** (`aea36497`, `153a3c20`): wiped when it is reaped and again at every
      network side's start (`net_generation_reset()`, called by `net_start`) — a SPAWN by the next side with the
      previous side's grant is refused.
    - **SIGNAL only to the current generation's children** (`aea36497`): a new network side cannot signal, by
      serial, the children born for the previous one.
    - **The per-uid CLOSE_ORPHAN hold** (`aea36497`): taken only after logind's check, and a live hold is never
      evicted — a full table refuses; before, 32 CLOSE_ORPHANs for other uids freed a user's hold in ~16 s.
    - **The network side's environment is an allow-list** (lane 4's review M4, `46bdc995`; `24331520`): a fixed
      `PATH`, `LANG` and `LC_*`, `TZ`, `JOURNAL_STREAM`, `LD_LIBRARY_PATH`, `REMOTIX_*` and
      `DBUS_SYSTEM_BUS_ADDRESS` (a moved system bus is followed by both sides); nothing else crosses the `execve`.
    - **`--render-node` is not checked in the network side** (`47bab921`): behind the walls its `/dev` has no
      `/dev/dri`, the check exited 2 and the side was restarted for ever; the root side checks it and passes it to
      the children (`benches/24-privsep-render-node.sh`, the smoke's part «rendernode»).
    - **A `--page` the network side cannot read refuses the start** (`014543d0`): under `/tmp` (the walls' private
      tmpfs) or not openable by the network user (a forked copy as that uid tries); before, `page_open_fd()` failed
      in the network side, a restart loop. The engine flags such a drop-in (RX-NETUSER-003, «net.pagina»).
    - **The fuzz** (B1.20, `[M]` 16 Oct 2026, on `76af115b`): `rootside-proto` on the REAL `src/rootside.c`
      56 M runs and `rootside-dispatch` 16.5 M runs, 10 min × 2 jobs each, 0 crashes.

### 11.51 ✅ 1.5 lowers two requirements of 1.0: 3K and 8 users (recorded 21 Oct 2026)

- **Maximum resolution 3K** instead of 4K (user's words: *«la 1.0 prevedeva il 4K, ma ho abbassato i
  requisiti»*). It replaces, for 1.5 only, the 4096-px canvas of 1.0 and the «⛔ 3K as the maximum was proposed and
  discarded» written for 1.0.
- **At most 8 users** per machine, or the highest number that still works well.
- ⚠ Recorded after 1.5 was declared a failure (`FAILURE.md`).


### 11.52 🔸 The fuzz and the ngtcp2 / nghttp3 audit of 24 Oct 2026: 13 fixes (A 1 + B 6 + C 6), all «present since 1.0» — approved by the user on 24 Oct 2026; verification in progress

- **Status of the whole section: approved by the user on 24 Oct 2026** («Sì, i bug della 1.0 si correggono»); verification in progress. Nothing below is on the main line yet (the fixes are gathered on the integration branch). The fixes live on
  separate branches, stacked: `pacing-su-migrazione` (A), `audit-ngtcp2` (B), `audit-nghttp3` (C), and gathered on the
  integration branch `audit-tutto` (merges of B and C; tip `3c0fa624` when this was written). None of these defects is a
  regression of 1.5: all are in 1.0. What has been done so far: the product builds (`make -j2 BENCH=1`, no new
  warning), the `quic-conn` fuzz harness builds, `page.html` passes the JS check. **Not yet done:** the 30-minute fuzz
  on `audit-tutto`, the stream-churn bench, the functional A/B, the `pacing-ab` micro-bench. A fix whose test is not
  green stays out and is reported.
- **How the defects were found.** The `quic-conn` fuzz harness (§11.13, `benches/fuzz/quic-conn`, the real
  `src/transport.c` over a played ngtcp2) got a *pacing oracle*; it reported the first defect (A). Then the ngtcp2 1.25
  and nghttp3 1.18 headers were read call by call against `transport.c` and `webtransport.c` («the documentation says X,
  we do Y»): B and C.

#### A. Pacing bypassed (`643e9a40`, `3a6d128c`)
- **Cause:** `write_connection` passed a 64 KB buffer to `ngtcp2_conn_write_aggregate_pkt2` with `num_pkts = 0`. The doc:
  *«It also does not clamp |buflen|, and does not call `ngtcp2_conn_update_pkt_tx_time`»* (the non-`2` variant clamps to
  the send quantum). One call could put ~45 full packets on the wire at once, past ngtcp2's pacing.
- **Fix:** `buflen` = the send quantum, never less than one full packet (`get_max_tx_udp_payload_size2`, the floor the
  doc of `write_aggregate_pkt` asks for); and the loop timeout is rounded UP, so the loop no longer spins on `poll(0)`
  before a pacing deadline.
- **Verified by:** the fuzz pacing oracle (red before, green after). **To do:** `limiti-prove/pacing-ab.sh` (before/after:
  throughput, latency of small messages, packets per burst, losses at a `tbf` bottleneck; on loopback the burst phase
  will probably be «in the noise», the loss phase is the one that counts) and the A/B on smoothness. This is the fix
  with the most risk of performance effects: it goes in last.
- **`pacing-ab` done 24 Oct 2026:** the round-up of `3a6d128c` cost **+1 ms of RTT at rest** (every timer-driven send waited up to 1 ms
  more; rounded down it spun instead). Cured by waiting on the exact nanosecond deadline with `ppoll` (`1b447d3c`, `de5ebdfa`).
  **To do:** measure again with `pacing-ab --dopo integrazione`.

#### B. ngtcp2 audit (`audit-ngtcp2`, 6 fixes in 7 commits: B1 has two)
- **B1 `d624d875`+`0cc6df15`:** `NGTCP2_ERR_DROP_CONN` from `read_pkt` — doc: *«Server application must drop the
  connection silently (without sending any CONNECTION_CLOSE frame)»*. We answered with one (a reflection towards a
  forged source). Now dropped silently, and a connection already marked dead is no longer read (a second packet of the
  same burst would have reached `read_pkt`). Risk: medium.
- **B2 `5cb76986`:** `NGTCP2_ERR_CRYPTO` — a failed handshake was closed with NO_ERROR; now CRYPTO_ERROR + the TLS alert
  (`ngtcp2_conn_get_tls_alert2`). Low.
- **B3 `94c1f5ac`:** `handle_expiry` errors other than `IDLE_CLOSE` — doc: *«close the connection by sending the terminal
  packet produced by `ngtcp2_conn_write_connection_close`»*; we only marked it dead and the client waited for its own idle
  timeout. Low/medium.
- **B4 `cbe7d0cd`:** `SSL_set_app_data(ssl, NULL)` before `ngtcp2_conn_del` — doc of
  `ngtcp2_crypto_ossl_configure_server_session`. The ssl's app data kept a `get_conn` returning a freed conn. Low/medium.
- **B5 `d935abcf`:** the calls deprecated in 1.23.0 → their «2» versions (`is_local_stream`, `get_conn_info`,
  `get_pto`, `get_cwnd_left`, `get_send_quantum`, `get_remote_transport_params`; `transport.c` and `webtransport.c`).
  Same behaviour; maintenance. Only `settings.log_printf = NULL` (a deprecated field) is left, harmless.
- **B6 `8171e6c1`:** a code already written in `last_error` (the H3 code `webtransport.c` sets before a
  `CALLBACK_FAILURE`) is no longer overwritten when closing after a failed read or an expired timer.
- **Not done, on purpose:** (a) the `stream_open` / stream-credit question of `cb_stream_close` (needs a measurement:
  the doc says ngtcp2 extends by itself in one case, the 2 Oct 2026 measurement says it does not); (b) `handshake_timeout`
  stays at ngtcp2's default (no limit) — needs a decision; the 90 s limit of §11.40 covers the never-logged-in.
- **Verified by:** builds; fuzz stubs updated (`is_local_stream2`, `get_conn_info2`, `tls_alert2`, `ccerr_set_tls_alert`).

#### C. nghttp3 audit (`audit-nghttp3`, 6 fixes: C1, C2, C4-C7; C3 was NOT a defect; C7 has two commits)
- **C1 `672c9d42`:** `nghttp3_conn_close_stream` is called for every closed stream (H3_NO_ERROR when ngtcp2 gives no
  code); before, a stream closed without a code was never released: memory grew with every stream. Medium.
- **C2 `e7c469f1`:** the results of `nghttp3_conn_shutdown_stream_read` and `nghttp3_conn_unblock_stream` were ignored;
  now an application error + callback failure. Low.
- **C3 (no fix; `513b3b21`, then `fb0c6cd6`):** not a defect. `wt_stream_stop_sending` is ngtcp2's `stream_stop_sending`
  (we stop reading), NOT the client's STOP_SENDING, which comes back as STREAM_SHUT_WR from `writev_stream` and is already
  handled. `513b3b21` mistook it for the client's and moved it to the write side; `fb0c6cd6` restored the read side.
  `fb0c6cd6` still leaves one small real change: the return value is handled, through `h3_shutdown_read`; it belongs to
  C2. Recorded so nobody re-opens it.
- **C4 `86af9276`:** `NGTCP2_ERR_STREAM_NOT_FOUND` from `writev_stream` is handled like `STREAM_SHUT_WR`, not as a
  connection error. Low.
- **C5 `b6e3c5c1`:** `cb_rand` uses `getrandom()`, not `rand()`. Low.
- **C6 `f395aff5`:** a second CONNECT+webtransport while a session exists is refused with 429; before it renewed the 5 s
  `channel_deadline` of the first, and it also overwrote `w->session`, so the capsules of the first session were no
  longer recognised. Low.
- **C7 `515c2e7a`, `4923f68d` (new):** every closed stream left ~40 bytes in a list never emptied, and `judgment_find`
  scanned it at every packet — the cost grew with the streams opened in the connection's life (a slowdown, not only
  memory). The judgment of a closed stream is now released; `dispatch` / `dispatch_uni` take the prefix bytes out of the
  judgment BEFORE the rcp calls, so closing the stream inside them cannot free what is read next. Medium.
- **To do:** a stream-churn bench (open/close repeatedly: 1.0 vs before vs after), the WebTransport functional suite.

#### D. The fuzz harnesses
- **`quic-conn`** (on `audit-tutto`; `benches/fuzz/quic-conn`): besides the pacing oracle of A, the commits `6afde242` and
  `66d96d37` exercise the error paths of `transport.c` with forced `read_pkt` / `handle_expiry` errors, the TLS alert and
  the H3 code, with oracles: no read or write after DROP_CONN, one CONNECTION_CLOSE after an expiry error, the H3 code in
  `last_error` kept; a forced RETRY after the handshake becomes PROTO, as in the script.
- **`rcp-msg`** (branch `fuzz-rcp`, commits `a63cd356`, `fd02e3a4`, `c1b453b3`; NOT in `audit-tutto`): libFuzzer +
  ASan/UBSan on the messages the server receives from the browser (`src/rcp.c`: control, input, clipboard), with hooks
  that fail on purpose (`ask_verify`, `video_write`, `input`, `recanvas`, `layout`, `clipboard_write/offer`). Runs: to do.


### 11.53 🔸 The defences of the login: three levels of counters, a progressive ban, a /64 key — **SPEC CHANGE from 1.0** (24 Oct 2026) — built on `login-difese`, not yet run on the boxes

- ⛔ **SPEC CHANGE.** `DECISIONS.md` §1.9 (10 Aug 2026, decided by the user) says: *three consecutive failed
  authentications from the same address, and that address is out for 12 hours*, with a single counter on the address and
  the user name not counting. This section **replaces** that rule for 1.5. The decision was delegated by the user to the
  project leader on 24 Oct 2026, 13:40, after the opinions of Gemini Argon, ChatGPT, gpt-oss-20b and Laguna (LFM gave
  none). **Approved by the user on 24 Oct 2026**, who delegated it to the project leader («applica la migliore combinazione possibile… sei tu il capo-progetto»): this rule replaces §1.9 for 1.5; verification on the boxes in progress.
- **What changes (A-D of `PIANO.md`):**
  - **A. The key.** IPv4: the whole address. IPv6: the **/64** (a subscriber has a /64 at least and rotates inside it for
    free; counting the single address was a limiter that is not there). Plus an aggregate on the IPv6 **/48**.
    `::ffff:a.b.c.d` and NAT64 are the IPv4 inside, `::1` stays whole — the same rule as `address_key()` in
    `transport.c` (§1.9-bis). It lives in `rcp_key_address()` only (idempotent).
  - **B. Attempts in flight.** The attempt is **booked at `CREDENTIALS`**: counters are *failed + in flight*, and the check
    and the booking are one step (`login_reserve()`) before PAM is called. At most **2** verifications at once for the same
    (key, user). The verdict is booked by the **name and address of the request** (`struct flight` keeps both), so a
    verdict whose connection died is counted all the same (`rcp_orphan_verdict()`, from `transport_verdict()`).
    An attempt **without a verdict** (PAM timeout of the helper, the 12 s ceiling in `rcp_time()`, helper dead) **counts as
    failed**; a refusal that is our defect does **not** count — the booking is given back (`login_release`): the question
    never left (helper off, socket full, 16 already in flight) and, decided by the project lead on 24 Oct 2026, **the PAM
    helper dying** with requests in flight (`lost`, with a live session or with the connection gone). The helper's own
    8 s timeout and the 12 s ceiling still count as failures. This reverses the earlier rule that a timeout never counts.
    The 12 s double case (the ceiling in `rcp_time()` and the late verdict) also applies to the **release of a lost verdict**: it can
    release another booking of the same pair (key, user). Harmless: at most one extra attempt.
    The name and address of the request in flight travel with EVERY delivery of `helper.c` (answered, expired, dead
    helper): without the address a verdict whose connection is gone cannot be resolved and the booking would stay in
    flight for ever.
  - **C. Three levels, sliding window** (the time of the last N failures is kept, as in 1.0):

    | level | limit | window | ban of |
    |---|---|---|---|
    | (key, user) | 5 failed | 5 min | that user on that key |
    | key | 12 failed (any user) | 5 min | the key |
    | IPv6 /48 | 30 failed | 10 min | the /48 |

    Duration **progressive per level: 15 min, then 1 h, then 12 h** (the 1.0 duration is now the top of the ladder);
    the memory of the previous bans is forgotten after **24 h without a ban**. A **successful login resets only the
    failures of (key, user)** — not the recidivism, not the key's and /48's counters (an attacker with one valid account
    must not be able to wash the count). **The table never evicts a banned entry** nor one with an attempt in flight: if
    nothing else can go, the new entry is refused (`TOO_MANY_ATTEMPTS`), and the refusal is counted and logged. Before
    that, entries with nothing to remember are taken back, then the oldest without recidivism (declared in the log).
    `UNBLOCK <address>` removes **every level** that concerns the address (its (key, user) pairs, the key, the /48) and the
    recidivism. The ban file has a new format (`B2 <U|K|N> <level> <epoch> <key>[ <user>]`); the old lines
    (`[address] epoch`, the 12 h ban of 1.0) are read and converted at the top of the ladder, and the file is rewritten in
    the new format at the next change. ⛔ **The ban file never holds a name**: the (key, user) line carries the full
    HMAC-SHA256 of the name (64 hex digits, same secret as the log tags), the file is created 0600 and `fsync`ed before the
    rename; the secret is therefore loaded before `rcp_ban_load()`, and a replaced secret makes the old (key, user) lines
    match nobody (key and /48 lines are not affected). Values read from the file are bounded: no negative epoch, a ban
    never longer than 12 h.
  - **D. The log.** A name that is not a user of the machine is written `unknown user [a1b2c3]`: HMAC-SHA256 of the
    name cut to 6 hex digits, under a secret in `<certificates dir>/log-secret` (0600, next to `quic-secret`). Nothing
    of the name in clear (control characters were already refused). SHA-256/HMAC are written out in `rcp.c` so the module
    stays free of OpenSSL in the benches (checked against RFC 4231).
- **Link-local addresses (`fe80::x%eth0`) go to the /64 too** (project lead's decision, 24 Oct 2026): the zone id is
  cut before parsing, so the key is `[fe80::]`. The price is accepted: LAN users share one counter (five wrong
  passwords from one LAN machine ban that user on all of them for 15 min), because an attacker on the LAN must not be
  able to rotate addresses to escape the counters. `UNBLOCK` clears it.
- **What is NOT in this round:** the uniform delay (first measure with `pam-tempi`), and the points already covered by
  `PENDING_PER_ADDRESS`. The manual and `RCP.md` §4.4-bis still describe the 1.0 rule: to update when the user confirms.
- **Doubts left open:** (1) the page's `rcp_banned()` sees only the key and /48 levels, not (key, user) — it does not
  know the user; (2) `getpwnam_r` for the «unknown user» tag may ask NSS in the single-threaded loop: it is made only
  for attempts the limiter let through (the refused ones are logged as `user [hmac6]`, no lookup); (3) ⚠ **theoretical
  double counting after the 12 s cap**: if `rcp_time()` hits the 12 s ceiling it counts the failure and resolves the
  booking; a verdict of the helper arriving later for the same request would be counted a second time as an orphan. It
  is not reachable while the helper's own 8 s expiry is lower than the 12 s ceiling (the helper removes the request and
  delivers first); it would be if one of the two numbers changed.
- **Verification:** `benches/unit/login-ban/test.c` (counter logic, simulated clock: thresholds, window, progression and
  forgetting, reset, /64 rotation, /48, in flight, orphan verdict, full table, unblock, ban file, log tags). To do on the
  boxes: harness `rcp-msg` with new oracles, the functional suite (F-027 password and ban), `pam-tempi`.

**§1.9-bis closed (24 Oct 2026).** The rule «IPv4 whole, v4-mapped and NAT64 = the IPv4 inside, ::1 whole, any other IPv6 = its /64» is now applied in both places that need it: the login ban (`rcp_key_address()`, §11.53) and the connection caps before login (`address_key()`, §11.40, 8 per address or /64 and 32 per /48). Both give the same key: `benches/unit/address-key/test.c` runs the two real functions on the same 35 strings (IPv4, `::ffff:`, NAT64, `::1`, global /64, link-local with `%zone`, with port, with brackets, malformed) and compares the keys (150 checks). ⚠ A live test with a real IPv6 provider is **not possible here** (the server has only `::1` and `fe80::`): the coverage is the unit tests (`address-key`, `login-ban`) plus `01-b10-flood.py` in a private namespace with IPv6 addresses on `lo`.

### 11.55 🔸 The codec probe: a hardware decoder that refuses 64x48 gets a second probe at 320x240 (16 Oct 2026, ported 24 Oct 2026) — not yet built or run in the new tree

- **The defect**: `[M]` 16 Oct 2026, Firefox 153.5 ESR on an RX 6800 (radeonsi, Mesa 25.0.7, VA-API): H.264 at 64x48 and
  128x48 -> `EncodingError` (FFmpeg «Invalid data found»); 64x64, 64x96, 128x96 ... 1920x1080 paint; HEVC is refused by
  `isConfigSupported` at every size. The page declared no codec and the server refused with NOTHING_IN_COMMON, on a
  card that decodes the real session.
- **The cure**: the retry runs only when the 64x48 probe fails, with the first rung of the size ladder (320x240 = the
  minimum canvas of §4.5), with the same pixel test («only what paints is declared» does not move). A browser that
  paints 64x48 pays nothing more. The log line says when only the second probe painted.
- **Ported** from `4cfdd4a8` (abandoned first attempt; the §11.48 cited in the original code is this entry). Its bench
  `benches/22-page-decoder-sim.js` (cases J1-J5) does not exist in the new tree and was NOT ported.
