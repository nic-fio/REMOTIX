# Clean-up, tranche 1: what was removed because it is dead on Debian 13 (trixie)

17 Nov 2026. Rule: only what cannot be reached on trixie as shipped; when in doubt the code stays (see «Left in place»).
Baseline for the line counts: the tree before this step (copy of the old repo, no git history yet). Facts below were read
on the four trixie boxes (xfce, lxqt, gnome, kde), read-only: libselinux1 3.8.1 present but `/sys/fs/selinux` absent;
libei1 1.3.901; kwin-wayland 6.3.6; gnome-shell 48.7; labwc 0.8.3; `/usr/share/gnome-session/sessions` = gnome, gnome-login,
gnome-dummy; user unit `org.gnome.Shell@wayland.service` is a real file (no `@.service` template); polkit admin rule =
`unix-group:sudo`, groups `wheel`/`admin` do not exist, no `90-default-privs.rules`; x11-common 7.7+24+deb13u1 has no
`Xsession.d/60x11-common_xdg_path`; no os-release/session named `debian` among the gnome-session sessions.

## Removed

| # | Item | Files (what) | Lines removed | Proof it is unreachable on trixie |
|---|------|--------------|---------------|-----------------------------------|
| 1 | `selinux_level_like_sshd()` + its call + `dlfcn.h` | `src/child.c` | 91 | On trixie `libselinux.so.1` opens, but `is_selinux_enabled()` is 0 (no `/sys/fs/selinux`, no policy: checked on 4 boxes), so the function returned at `enabled() != 1`. Debian does not enable SELinux by default. |
| 2 | `selinux_exec_net()`, `context_with_type()`, `WALLS_SELINUX_TYPE`, the call in `walls_apply()`, `dlfcn.h` | `src/walls.c` (+ 2 comment lines in `walls.h`, `rootside.h` block on `setexeccon`) | 86 (+13 comment) | Same: it ended with `note("SELinux: off (is_selinux_enabled)")` and rc 0. Only visible effect: that text is gone from the one-line «walls in force» note in the journal. |
| 3 | `-ldl` (`DL_LIBS`), no `dlopen` left | `src/Makefile` | 6 | After 1+2 no `dlopen`/`dlsym` in `src/` (grep). glibc 2.41 (trixie) has no separate libdl; `ldd` list of the binary identical before/after (32 libs). |
| 4 | Ubuntu names in `desktop_of_session_name()` (`xubuntu`, `lubuntu`, `kubuntu`, `ubuntu`) | `src/session.c` | 6 (4 replaced) | Names come from lightdm `user-session` / sddm `Session`; on Debian they are `xfce`, `lxqt`, `plasma`, `gnome`. No Debian package ships a session called `*ubuntu*`. |
| 5 | os-release `ID` match in `gnome_session()` (point 3 of the D8 criterion) | `src/session.c` | 8 | It matched a gnome-session whose `--session` name equals os-release `ID` (`debian`). trixie GNOME offers only `gnome`/`gnome-wayland.desktop`, both name `gnome` (checked); no `debian.session` exists. The result (alphabetical first, `gnome`) is unchanged. |
| 6 | GNOME 50 template branch of `unit_shell()` (`org.gnome.Shell@.service`, `@user`/`@ubuntu`, the `Requires` query), `SESSION_UNIT_SHELL_MODEL`, the `--mode=%i` suffix in the drop-in, the template-folder guard in the clear-out | `src/session.c`, `src/session.h` | 52 + 22 | `FragmentPath` of `org.gnome.Shell@wayland.service` on GNOME 48 ends in that very name (real file in `/usr/lib/systemd/user`, checked), so the first `return` is always taken; `unit != SHELL_48` is therefore never true; `org.gnome.Shell@.service.d` is never written by us. |
| 7 | D-153 discovery of «the session as a local login gives it»: `session_folder_there()`, `by_name()`, `local_session_name_find()`, `xsession_d_applies()`, body of `local_session()` | `src/session.c` | 77 (+20 new for the small replacement) | `xsession_d_applies()` returned FALSE unless `/etc/X11/Xsession.d/60x11-common_xdg_path` exists. It is Ubuntu's patch to x11-common: absent on all four boxes. So `s.name/config/data` were always NULL. `local_session()` now returns that empty struct and writes the SAME log line as before (byte-identical text). The callers (`add_session_names`, `session_config_dirs`, …) are untouched. |
| 8 | `REMOTIX_EI_PING`: `#ifdef` made unconditional, `#else` stubs deleted; Makefile `-DREMOTIX_EI_PING` probe | `src/input.c`, `src/Makefile` | 18 + 4 | The probe was `pkg-config --atleast-version=1.3.901 libei-1.0`; the build container has 1.3.901, so the flag was always defined in the package. `Build-Depends` / `make deps` minimum raised from libei 1.1 to 1.3.901 (`debian/control`, `MINIMI`), so a build without it now stops instead of building a binary without receipts. |
| 9 | `REMOTIX_LABWC` (patched/own labwc path): both `#ifdef`s in `kwin.c`, the `LABWC=` knob in the Makefile | `src/kwin.c`, `src/Makefile` | 13 + 8 | `debian/rules` stopped passing it (block already gone in the previous step); never defined in a build of this tree, so the `#else` branches were the only ones compiled. |
| 10 | Bench/test targets of `src/Makefile` pointing to `../benches` (`bench-w1`, `test-damage`, `bench-unchanged`, `test-session`, `test-colors709`, `test-rootside`, `test-walls`, `test-tls-groups`, `test-rediscover`, `test-all`) and their variables | `src/Makefile` | 121 | `benches/` is not in this tree (all those paths are missing); `debian/rules` calls only `deps` and `all`. The `TWIN`/`fingerprints` comparison stays: it is part of `all` (see below). |
| 11 | 90-default-privs branch of the polkit helper + Alma/SELinux comment | `src/remotix-polkit-seated` | 25 | `/etc/polkit-1/rules.d/90-default-privs.rules` is openSUSE's polkit-default-privs; absent on trixie (checked), so `v` was always empty and the `.policy` lookup (kept, now unconditional) always ran. |
| 12 | 1.0 → 1.5 upgrade machinery: `debian/remotix-net-move` (184), its call in `postinst`, the `--back` block in `prerm`, `REMOTIX_SPLIT` and the `ifeq` blocks in `debian/rules`, the non-split `remotix.service` / `remotix.tmpfiles`; the `.split` files renamed over them; `REMOTIX_SPLIT` in `build/build-deb.sh` | `debian/rules`, `debian/remotix.postinst`, `debian/remotix.prerm`, `debian/remotix.service(.split)`, `debian/remotix.tmpfiles(.split)`, `build/build-deb.sh` | ~230 | «No upgrade from 1.x» is decided. The default build was already `REMOTIX_SPLIT=1`, so the package that comes out is the same except for the files listed under «Package differences». |

Per-item counts are approximate (comments adjusted around the code); the exact per-file totals are the diff: `session.c` -144/+20, `child.c` -89, `walls.c` -86/+5, `input.c` -18, `kwin.c` -13/+1, `Makefile` -141/+6.
Total: 551 lines removed / 42 added in `src/`, ~300 / 35 in `debian/` (net-move 184 of them), 2 / 1 in `build/`.

## Fresh install: why behaviour is identical (item 12)
`remotix-net-move` (forward) on a fresh install: checks that the user exists (sysusers had just created it), makes
`/var/lib/remotix` 0755 root and `net/` 0700 remotix, and moves nothing (no 1.0 files). `remotix.tmpfiles` (`d` lines) does the
same at the very next step of the postinst (`systemd-tmpfiles --create remotix.conf`, kept). The postinst now runs
sysusers then tmpfiles; the move step in between is gone. Compared the two `.deb` (fix2 `-3` vs pulizia1 `-4`): every file is
byte-identical (unit, tmpfiles, sysusers, AppArmor profile, polkit rules apart from the helper, conffiles, page, conf,
`postrm`, `preinst`) except: `remotix` binary (expected), `remotix-polkit-seated` (item 11), `postinst` and `prerm`
(net-move blocks), `md5sums`/`control` (version, Installed-Size), changelog, and the deleted `/usr/libexec/remotix/remotix-net-move`.
Depends, Recommends, Static-Built-Using, Conffiles: identical.
One observable difference, on `apt remove` (not purge): the old prerm ran `remotix-net-move --back`, which moved
`net/certificates` and `net/ban` back to `/var/lib/remotix/` (1.0 layout) and made `/var/lib/remotix` 0700. Now they stay in `net/`.
Purge deletes both locations in `postrm` (unchanged) and a reinstall finds them where it expects them. Say so to the owner:
if a «remove then check» test looks for files in the 1.0 places it will now not find them.

## Left in place (and why)
- `/usr/lib/pam.d/remotix` as second location in `main.c` `look_pam_service()` and the openSUSE/Fedora/Arch text in the PAM
  messages (`main.c`, `authentication.c`): on trixie `/usr/lib/pam.d` is a real PAM vendor directory (it holds `polkit-1`,
  `systemd-user`), so it is not provably dead; the code only writes a log line. Text-only change, left.
- `pam_selinux.so` lines in `src/remotix.pam`: the module ships in Debian's libpam-modules and the lines mirror Debian's sshd; harmless.
- `declared_desktop()` / `declared_sessions()` / `active_display_manager()` / `last_conf_value()`: read lightdm and sddm files, valid
  on Debian when several desktops are installed (lightdm `user-session` is a Debian setting too). Only the Ubuntu names were removed.
- KWin 6.5 / 6.6.6 workarounds (`clipboard_kde.c` ext-data-control, `kwin.c` `org.kde.kconfig.notify`): there is NO version test in
  the code, they are runtime probes (bind whichever global the compositor offers; both signals are sent). Nothing is provably
  unreachable by a constant, so nothing removed.
- `wheel`/`admin` in `remotix-remote-sessions.rules`: groups do not exist on trixie as shipped, but an administrator can create
  them; rule logic, kept. Same file's openSUSE comments: comments only, not rewritten.
- `--no-split` runtime option and `main.c` single-process code path: a run-time flag, not the build switch; kept.
- `TWIN` / `fingerprints` in the Makefile: part of `all`, prints that nothing was compared (`TWIN=none`); not a bench target.
- `postrm` `rm -rf` of the 1.0 paths `/var/lib/remotix/{certificates,ban,ban.new}`: one line, harmless, left.
- `main.c` log text about SELinux denying descriptors: the descriptor check is generic; only the message names SELinux.
- All comments that merely name a distribution, `page.html` font stack (changes the shipped page), `debian/control` comments.
- `debian/remotix.tmpfiles` still carries its «NOT ACTIVE YET» header comment and `remotix.service` the `--split` comments:
  editing them would change the `.deb` bytes; to be done in a later step on purpose.

## Risks
- Item 7 relies on x11-common not shipping `60x11-common_xdg_path`. If a future Debian adds it, the folder mechanism (not tested
  on Debian ever) would be needed again: restore from the old repo.
- Items 1-2 assume SELinux is not enabled; an administrator who installs `selinux-basics` on Debian would find no SELinux handling.
- Item 8: a build against libei < 1.3.901 now fails at `make deps` by design.
