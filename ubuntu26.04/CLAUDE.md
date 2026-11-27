# REMOTIX-UBUNTU

Remote desktop server: browser client over WebTransport/QUIC, PAM login, per-user Wayland sessions on Ubuntu (GNOME), Kubuntu (KDE), Xubuntu (XFCE), Lubuntu (LXQt).
Ubuntu 26.04 only, version **1.2.0** (aligned to Fedora 45, 26-27 Nov 2026); installed with `apt install ./remotix_*.deb`, no installer.
Plan and steps: `PIANO.md`. Specs: `docs/SPECS.md`, `docs/RCP.md`, `docs/DECISIONS.md`, `docs/DECISIONS-11.md`, `docs/LESSONS.md`.
## Layout
- This directory is `ubuntu26.04/` inside the single `main` branch of the repo (one self-contained directory per distribution: `debian13/`, `ubuntu26.04/`, `fedora45/`). Work inside it; paths below are relative to it.
- `src/` product (C, Makefile, page.html, PAM file, polkit rules); `debian/` packaging (control, rules, maintainer scripts);
  `build/` package build (`build-deb-vm.sh`, `quic-static.sh`; old podman flow: `build-deb.sh`, `Containerfile`); `docs/` specs and
  `docs/REGISTRO-problemi.md` (every problem closed or postponed, read before a new distro); `prove/` the test tools;
  `server/` the dev-server bench (`vm-radeon.sh`, `prepara-server-vm.sh`; see `server/VM-BANCO.md`); `studio/` analyses and `studio/prove-1.2.0/COME-SI-LANCIA.md`.
## Build and test
- `build/build-deb-vm.sh [label]` builds the .deb in the server's `costruzione` VM (no containers); output in `/media/REMOTIX-UBUNTU/pacchetti/<label>/`.
- Tests run on the server's VMs (one per desktop, one Radeon passed through, no containers): procedure in `studio/prove-1.2.0/COME-SI-LANCIA.md`. `vm-radeon.sh accendi` checks `amdgpu.runpm=0` in the guest before giving it the Radeon: never bypass it (server freezes).
- Never compile or run heavy work on the CHUWI tablet. Build and test on the server `nicfio@192.168.0.2`, work dir `/media/REMOTIX-UBUNTU`.
- The owner decides how and when hands-on tests run. Licences: only `LICENSE.md` (installed as the package's `copyright`) and `THIRD-PARTY-LICENSES` ship in the package; `licenses/` does NOT.
## Conventions
- Ubuntu 26.04 only; four desktops; no distro detection or per-distro code.
- Never modify, move or delete anything outside this directory without the owner's request; `debian13/` and `fedora45/` are read-only references here.
- Code comments in English. Reuse old code; when in doubt keep the old behaviour and note the doubt.
- The service is installed disabled and not started (`dh_installsystemd --no-enable --no-start`); the administrator enables it.
