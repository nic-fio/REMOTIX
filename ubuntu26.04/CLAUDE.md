# REMOTIX-DEBIAN

Remote desktop server: browser client over WebTransport/QUIC, PAM login, per-user Wayland sessions on XFCE, LXQt, GNOME, KDE.
This repo is the **Debian 13 (trixie) only** rewrite of REMOTIX; installed with `apt install ./remotix_*.deb`, no installer.
Plan and steps: `PIANO.md`. Specs: `docs/SPECS.md`, `docs/RCP.md`, `docs/DECISIONS.md`, `docs/DECISIONS-11.md`, `docs/LESSONS.md`.
## Layout
- `src/` product (C, Makefile, page.html, PAM file, polkit rules); `debian/` packaging (control, rules, maintainer scripts);
  `build/` container build (`build-deb.sh`, `Containerfile`, `quic-static.sh`); `docs/` specs and the non-Debian inventory
  (`docs/INVENTARIO-non-debian.md`: code still to remove, later and reviewed); `server/` the dev-server set-up scripts.
## Build and test
- `build/build-deb.sh` builds the .deb in a `debian:trixie` podman container; output in `$OUTPUT` (default `/media/REMOTIX-DEBIAN/pacchetti`).
- Never compile or run heavy work on the CHUWI tablet. Build and test on the server `nicfio@192.168.0.2`, work dir `/media/REMOTIX-DEBIAN`.
- The owner decides how and when tests run. Licences: only `LICENSE.md` (installed as the package's `copyright`) and `THIRD-PARTY-LICENSES` ship in the package; `licenses/` does NOT.
## Conventions
- Debian trixie only; four desktops; no distro detection or per-distro code (a future distro gets its own, separate code).
- The old repo `~/Documenti/REMOTIX` is a READ-ONLY reference: never modify, move or delete anything in it.
- Code comments in English. Reuse old code; when in doubt keep the old behaviour and note the doubt.
- The service is installed disabled and not started; the administrator enables it.
