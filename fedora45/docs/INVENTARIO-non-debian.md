# Inventory: what exists only for another distro (or to tell distros apart)

Written 17 Nov 2026 on the tree copied from the old repo. Format: `file:line — what — safe to remove now?`
(`yes` = dead on Debian 13; `needs care` = reachable on Debian or entangled, to be removed in a later reviewed step).
Line numbers are those of the tree at the moment of writing. Comments that merely mention a distro are not listed one by one.

## Already removed in this step (trivially dead on Debian)
- Not copied: `installer/`, `benches/`, `packaging/{rpm,arch,engine,labwc-ospite,archive}`, site, manuals.
- Not copied from `src/`: `Containerfile.{alma10,arch,fedora44,leap16,tumbleweed,ubuntu2404,ubuntu2604}`, `build-all.sh`,
  `build-deb.sh` (replaced by `build/build-deb.sh`), `build.sh`, `build-in-container.sh`, `provision.sh`, `restart-77/79*.sh`,
  `Containerfile` (dev image), `opus-wasm/test/`.
- Deleted after copy: `src/remotix.pam.fedora`, `.suse`, `.arch`.
- `debian/rules`: the Ubuntu-26.04-only «our labwc» block (`REMOTIX_LABWC_OSPITE`, `labwc-ospite/build.sh`, `-DREMOTIX_LABWC`
  path) removed — it evaluated to 0 on Debian; `TWIN=none` added (no `benches/rcp` any more).
- `debian/remotix.postinst`: the `remotix-install post-upgrade` call (engine is gone).

## Status after tranche 1 (17 Nov 2026) — details and proofs in `docs/PULIZIA-tranche1.md`
DONE: SELinux in `child.c`/`walls.c` and `-ldl`; Ubuntu names in `desktop_of_session_name()`; os-release match in `gnome_session()`;
GNOME 50 template branch (`unit_shell()`, `--mode=%i`, `SESSION_UNIT_SHELL_MODEL`); D-153 local-login folder discovery (dead because
trixie's x11-common lacks `60x11-common_xdg_path`; `local_session()` is now an empty struct with the same log line); `REMOTIX_EI_PING`
(libei minimum raised to 1.3.901); `REMOTIX_LABWC` and the `LABWC=` knob; bench/test targets of `src/Makefile`; the 90-default-privs
branch and the Alma comment in `remotix-polkit-seated`; `remotix-net-move`, `REMOTIX_SPLIT`, the non-split unit/tmpfiles and the
`.split` duplicates in `debian/`.
STAYS (with why): `/usr/lib/pam.d` lookup (real vendor dir on trixie) and the distro text in the PAM messages; `pam_selinux` lines in
`remotix.pam` (Debian ships the module, harmless); `declared_desktop()` and the lightdm/sddm readers (valid on Debian); KWin 6.5/6.6.6
workarounds (runtime probes, no version test to remove); `wheel`/`admin` in the polkit rule; `--no-split` runtime flag; `TWIN`/`fingerprints`;
`certificates.c`, `rootside.c`, `card_pick.c`, `page.html`, `kdehost.h`, `debian/control`, `.apparmor`, `.sysusers`, `quic-static.sh` comments
(comments only or shipped bytes); `main.c` SELinux wording in two log messages; `postrm` `rm` of the 1.0 paths.
The line numbers in the entries below are those of the tree BEFORE tranche 1.

## src/ — distro-specific code
- `src/session.c:381-393` — `session_desktop_of()` maps `xubuntu`/`lubuntu`/`kubuntu`/`ubuntu` session names to desktops — needs care: Debian has no such names, but the same function classifies `xfce`/`lxqt`/`plasma`/`gnome`; remove only the Ubuntu strings, with the ordering comment.
- `src/session.c:283-290, 519` — Xubuntu detection (`gnome-session` alone is not GNOME; lightdm `60-xubuntu.conf`, sddm `20-kubuntu.conf`) — needs care: the logic that decides "which desktop is installed" is shared; Xubuntu-only branches can go after a read-through.
- `src/session.c:749-775, 900-925, 2986-2987, 3227, 3990, 4122` — GNOME session choice (D8): `ubuntu` session, os-release `ID` match, `@ubuntu` Shell instance — needs care: on Debian the only session is `gnome`; rule 1 ("only one") already decides. The os-release lookup (`os`) and `@ubuntu` handling can be removed later.
- `src/session.c:2250-2259, 2333, 2803-2809` — Ubuntu/Xubuntu `XDG_*`/`DESKTOP_SESSION` emulation of a local login (`ubuntu:GNOME`, `/etc/xdg/xdg-<session>`) — needs care: the same code also emulates Debian's login for the other sessions.
- `src/clipboard_kde.c:325`, `src/kwin.c:929` — KWin 6.6.6 (Ubuntu 26.04) behaviour changes — needs care: Debian 13 has KWin 6.3; the code is a runtime probe, unverified on 6.3 only by the old tests; keep.
- `src/kwin.c:1322-1385`, `src/Makefile:127-135` — `REMOTIX_LABWC` build-time path of the patched labwc (Ubuntu 26.04/Alma) — yes for the `#ifdef REMOTIX_LABWC` branches (never defined now); the `LABWC=` Makefile knob too. Left in place for review; harmless.
- `src/child.c:1589-1640, 1793-1794` — `selinux_level_like_sshd()` (dlopen libselinux) — yes in effect (Debian has no SELinux: the function returns early) but it is called in the login path: remove in a reviewed step.
- `src/walls.c:121-249, 770-771` — `selinux_exec_net()` (network side's SELinux context) — same: no-op on Debian; needs care because it sits inside `walls_apply()` order ("2 — SELinux, while /proc can still be written").
- `src/main.c:2438, 2500` — comments/messages about SELinux denying descriptors — yes (text only), with the code above.
- `src/Makefile:196-197` — `-ldl` kept "for libselinux dlopen" — needs care: other dlopen users (Vulkan/VA) may exist; check before dropping.
- `src/input.c:689-692`, `src/Makefile:253` — `REMOTIX_EI_PING` fallback for libei < 1.3.901 (Ubuntu 24.04) — Debian 13 has libei 1.4+: the `#else` branches are dead, the `#ifdef` can become unconditional — needs care: touches the input hot path; also `Build-Depends: libei-dev (>= 1.1)` in `debian/control` could rise to 1.3.901.
- `src/Makefile:220, 228-229, 308, 515` — comments for Debian 12/Ubuntu 22.04, other distros' package names, `lib64` — yes (comments).
- `src/authentication.c:244-246`, `src/main.c:469-473` — log messages naming `/usr/lib/pam.d` (openSUSE), pam_deny on Fedora/Arch, `.fedora/.suse/.arch` files — yes (text); `main.c` also checks `/usr/lib/pam.d/remotix` as a second location — needs care (tiny).
- `src/remotix.pam` — Debian PAM (header text lists the other three variants; `pam_selinux` lines at the end) — needs care: `pam_selinux` lines are `module_unknown=ignore`, harmless on Debian; they mirror Debian's own `sshd`, keep unless the owner wants a leaner file.
- `src/remotix-polkit-seated:13,26` — "distribution's privilege table", SELinux/Alma workaround — needs care: the script is installed and run by polkit; the Alma branch can go after a read-through.
- `src/remotix-remote-sessions.rules:39-68` — openSUSE polkit-default-privs notes and `wheel` handling for root-only polkit admin — needs care: rule logic is generic (seated vs remote), comments only distro-specific.
- `src/certificates.c:151-152` — `X509_get_subject_name` const (Ubuntu 26.10/Fedora rawhide) — needs care: the code compiles on both; keep.
- `src/rootside.c:1197` — comment about `sss` in nsswitch (Ubuntu Desktop) — needs care: the code handles a lookup failure generally; keep.
- `src/card_pick.c:17` — comment on openSUSE VM `virtio_gpu` — yes (comment); the code is generic ("no exception per distribution").
- `src/page.html:488` — font stack lists `Ubuntu` — yes (cosmetic), changes nothing on Debian.
- `src/kdehost.h:262` — comment about the "distribution's own ExecStart" — yes (comment).
- `src/session.c` and `src/child.c` also carry `xwayland`, `GDK_BACKEND`, labwc workarounds that are per-desktop, not per-distro: out of scope here.

## debian/ — Debian-and-Ubuntu leftovers
- `debian/control:26, 50, 74-95` — comments about Ubuntu 26.04, openSUSE, arm64 Ubuntu, D8 `ubuntu` session — yes (comments); `va-driver-all` note valid on Debian.
- `debian/control` `Recommends: labwc, wlr-randr, xwayland` — Debian's labwc (0.8.x in trixie) is the one in use — keep.
- `debian/remotix-net-move:4, 19, 27, 71, 114, 133` — rpm `%post`, Arch hooks, "same file in packaging/{debian,rpm,arch}" — yes (comments); the script itself is the 1.0 → 1.5 move: needs care — the new product has "no update from 1.x" (PIANO): the whole script, its call in `postinst`/`prerm` and `tmpfiles` `z` lines could go after the owner confirms that no 1.x is ever upgraded.
- `debian/remotix.sysusers:5` — "the SAME line in packaging/{debian,rpm,arch}" — yes (comment).
- `debian/remotix_network.apparmor:3` — "written from packaging/rpm/selinux/remotix.te.split" — yes (comment); the profile is NOT TRIED (PIANO step 6).
- `debian/rules` `REMOTIX_SPLIT=0` single-process variant, `debian/remotix.service` (non-split), `remotix.tmpfiles` (non-split) — needs care: default is split; the `=0` build and the non-split files are not Debian-specific but are dead weight; remove after review.
- `debian/remotix.lintian-overrides`, `debian/copyright` — no change needed.
- `build/quic-static.sh` header — mentions Arch/Tumbleweed (comment) — yes.

## Not found / not applicable
- No `ID_LIKE`/`/etc/os-release` family switch outside `session.c:900-925` was found in `src/`.
- No `zypper`/`dnf`/`pacman` calls in `src/` or `debian/`.
