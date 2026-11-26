# REMOTIX-DEBIAN

Remote desktop server: browser client over WebTransport/QUIC, PAM login, per-user Wayland sessions on XFCE, LXQt, GNOME, KDE.
Debian 13 (trixie) only, version **1.2.0** (aligned to Fedora 45 on 26 Nov 2026); installed with `apt install ./remotix_*.deb`, no installer.
Plan and steps: `PIANO.md`. Specs: `docs/SPECS.md`, `docs/RCP.md`, `docs/DECISIONS.md`, `docs/DECISIONS-11.md`, `docs/LESSONS.md`.
## Layout
- Since 20 Nov 2026 this directory is `debian13/` inside the single `main` branch of the repo (one self-contained directory per distribution: `debian13/`, `ubuntu26.04/`). Work inside it; paths below are relative to it.
- `src/` product (C, Makefile, page.html, PAM file, polkit rules); `debian/` packaging (control, rules, maintainer scripts);
  `build/` package build (`build-deb-vm.sh`, `quic-static.sh`; old podman flow: `build-deb.sh`, `Containerfile`); `docs/` specs and the non-Debian inventory
  (`docs/INVENTARIO-non-debian.md`: code still to remove, later and reviewed; `docs/REGISTRO-problemi.md`: every problem closed or postponed, read before a new distro);
  `prove/` the test tools; `server/` the dev-server set-up scripts (`prepara-server-vm.sh`, `vm-radeon.sh`).
## Build and test
- `build/build-deb-vm.sh [label]` builds the .deb on the server's `costruzione` VM (no containers; turns it on and off; lintian errors fail it); output in `/media/REMOTIX-DEBIAN/pacchetti/<label>/`. The old podman flow (`build/build-deb.sh`, `Containerfile`) is kept but no longer used.
- Tests run on the server's VMs (one per desktop, one Radeon passed through, no containers): procedure in `studio/prove-1.2.0/COME-SI-LANCIA.md`. Every Debian guest MUST have `amdgpu.runpm=0` before it gets the Radeon (without it the server froze four times, 26 Nov 2026).
- Never compile or run heavy work on the CHUWI tablet. Build and test on the server `nicfio@192.168.0.2`, work dir `/media/REMOTIX-DEBIAN`.
- The owner decides how and when tests run. Licences: only `LICENSE.md` (installed as the package's `copyright`) and `THIRD-PARTY-LICENSES` ship in the package; `licenses/` does NOT.
## Conventions
- Debian trixie only; four desktops; no distro detection or per-distro code (a future distro gets its own, separate code).
- Never modify, move or delete anything outside this directory without the owner's request; `ubuntu26.04/` and `fedora45/` are read-only references here (see the root `CLAUDE.md`).
- Code comments in English. Reuse old code; when in doubt keep the old behaviour and note the doubt.
- The service is installed disabled and not started; the administrator enables it.
