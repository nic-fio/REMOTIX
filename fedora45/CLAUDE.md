# REMOTIX — Fedora 45

Remote desktop server: browser client over WebTransport/QUIC, PAM login, per-user Wayland sessions on GNOME, KDE, XFCE, LXQt.
This directory is the **Fedora 45 only** code (started 21 Nov 2026 as a copy of `ubuntu26.04/` at version 1.0.1; released as 1.2.0). Plan: `PIANO.md`.
Studies of the four desktops on Fedora 45: `studio/` (read the one for your desktop first). Problem register: `docs/REGISTRO-problemi.md`.
## Layout
- `src/` product (C, Makefile, page.html, PAM file, polkit rules); `prove/` test tools; `docs/` specs and register (inherited from Ubuntu);
  `server/` test-bench scripts (`vm-radeon.sh`, `prepara-server.sh`); `studio/` studies; `rpm/` RPM packaging (spec, unit, firewalld service);
  `selinux/` the package's policy module; `build/build-rpm.sh` builds on the build VM; `manuals/` the two manuals (`sources/build.py`).
## Build and test
- NO containers, no podman (owner's order): build and test only on the VMs of `server/vm-radeon.sh`
  (server `nicfio@192.168.0.2`, `/media/REMOTIX-FEDORA/vm-radeon/`; four desktops + one build VM; one Radeon: one VM at a time has it).
- Never compile or run heavy work on the tablet. The owner decides how and when tests run.
- Test VMs start from snapshot `codec` (clean install + RPM Fusion codecs, required by REMOTIX on Fedora).
## Conventions
- Fedora 45 only; no distro detection; never touch `../debian13/` or `../ubuntu26.04/`. Change only what Fedora requires.
- Development goes ONE desktop at a time: GNOME, then KDE (KWin 6.8 alone, no patched labwc), XFCE, LXQt.
- SELinux stays enforcing; the package ships its own policy module. Service installed disabled.
- Code comments in English. Every closed or postponed problem gets a register entry.
