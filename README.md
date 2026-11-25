# REMOTIX

REMOTIX is a remote desktop server for Linux. A user opens a browser, logs in with their normal system account and gets their own graphical session
(XFCE, LXQt, GNOME or KDE Plasma on Wayland). The browser talks to the server over WebTransport/QUIC; there is no client to install.

The repository has one branch (`main`) and one self-contained directory per distribution. Each directory has its own code, packaging, build,
tests, docs, manuals and licences, and builds its own package (`.deb` or `.rpm`).

| Directory | Distribution |
|---|---|
| [`debian13/`](debian13/) | Debian 13 (trixie) |
| [`ubuntu26.04/`](ubuntu26.04/) | Ubuntu 26.04 (Ubuntu, Kubuntu, Xubuntu, Lubuntu) |
| [`fedora45/`](fedora45/) | Fedora 45 (Workstation, KDE Plasma Desktop, Xfce, LXQt) |

- Manuals (technical and user): `manuals/` inside each distribution directory.
- Rebuilding the package and the test bench from this repository alone: `docs/RIPRISTINO.md` inside each distribution directory.
- Licence: `LICENSE.md` inside each distribution directory (the texts differ only in what is specific to each package, such as the paragraph about labwc, so there is no copy at the top level);
  third-party licences in `THIRD-PARTY-LICENSES`.
