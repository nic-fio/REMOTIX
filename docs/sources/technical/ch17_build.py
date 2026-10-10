"""Chapter 17 — Build and release. Sources: src/Makefile, src/Contenitore, src/costruisci*.sh,
src/costruzione/*, packaging/ (debian, rpm, arch, motore, archivio, rilascio.sh), installatore/costruisci.sh,
installatore/run.sh, src/opus-wasm/costruisci.sh; fasi/17-l-installatore.md §6.1-§6.4, §6.6.16, §13."""
import json
import re

from build import ROOT, arrow, box, c, code, esc, fig, flow, note, p, rif, steps, table, text, tip, tree, warn, zone

MAKEFILE = (ROOT / "src" / "Makefile").read_text()
CAT_VER = json.loads((ROOT / "installatore" / "catalogo" / "catalogo.json").read_text())["versione"]


def _make_list(nome):
    """A variable of the Makefile, continuation lines joined."""
    m = re.search(r"^" + nome + r"\s*:?=\s*((?:.*\\\n)*.*)$", MAKEFILE, re.M)
    return m.group(1).replace("\\\n", " ").split() if m else []


SORGENTI = _make_list("SORGENTI")
PROTOCOLLI = _make_list("PROTOCOLLI")
MINIMI = [x.split(":") for x in _make_list("MINIMI")]

ROADS = fig(
    zone(20, 14, 420, 132, "Every day — the developer's binary")
    + box(36, 46, 184, 46, "src/Contenitore", "Debian 13, .so in /usr/local", "dark", 12)
    + box(240, 46, 184, 46, "costruisci-in-contenitore.sh", "podman, keep-id", "blue", 11)
    + box(138, 104, 200, 34, "src/remotix + bench 04-b31", "", "green", 11.5)
    + arrow(221, 69, 238, 69) + arrow(330, 94, 270, 102)
    + zone(460, 14, 420, 132, "The installer engine")
    + box(476, 46, 184, 46, "installatore/costruisci.sh", "golang:1.25, CGO off", "blue", 11)
    + box(680, 46, 184, 46, "pacchetti-motore.sh", ".deb .rpm .pkg.tar.zst", "blue", 11)
    + box(578, 104, 200, 34, "remotix-install (static)", "", "green", 11.5)
    + arrow(661, 69, 678, 69) + arrow(568, 94, 620, 102)
    + zone(20, 160, 860, 132, "Per distribution — one container per target (src/costruzione)")
    + box(36, 192, 200, 46, "Contenitore.<target>", "+ quic-statiche.sh", "dark", 12)
    + box(256, 192, 190, 46, "costruisci-tutti.sh", "binary, ldd, versions", "blue", 11.5)
    + box(466, 192, 190, 46, "costruisci-deb.sh", "debian13, ubuntu2604", "blue", 11.5)
    + box(676, 192, 190, 46, "costruisci-rpm.sh / arch", "fedora44 … arch", "blue", 11.5)
    + arrow(237, 215, 254, 215)
    + '<path d="M136 240 V258 H771" fill="none" stroke="#0050C0" stroke-width="2.2"/>'
    + arrow(561, 258, 561, 241) + arrow(771, 258, 771, 241)
    + text(450, 278, "the same images build the packages", 10.5)
    + zone(20, 306, 860, 70, "Release")
    + box(240, 322, 200, 42, "packaging/rilascio.sh", "X.Y.Z-R", "navy", 12)
    + box(500, 322, 240, 42, "remotix-X.Y.Z-R.run + .sha256", "", "green", 11.5)
    + arrow(441, 343, 498, 343),
    900, 384, "«FIG» — The build roads: development, engine, per-distribution packages, release")

S_ROADS = p("REMOTIX is never built on the host and never with sudo: every build runs in a podman container as the "
            "user, with the source tree mounted inside. There are four roads, and they share images and scripts.",
            lead=True) + ROADS + \
    table(["Road", "Command", "Output", "Used for"], [
        ["Development", c("bash src/costruisci-in-contenitore.sh [make-target]") + " (build in the container)",
         c("src/remotix"), "every-day work; "
         "the binary is tied to the container's libraries and is never committed (" + c(".gitignore") + ")"],
        ["Per-distribution check", c("src/costruzione/costruisci-tutti.sh [target…]") + " (build all)",
         c("costruzione-uscita/<target>/") + " (build output): binary, logs, " + c("ldd") + ", versions",
         "does it compile and link cleanly on each distribution"],
        ["Packages", c("src/costruzione/costruisci-deb.sh") + ", " + c("packaging/rpm/costruisci-rpm.sh") + ", "
         + c("packaging/arch/costruisci.sh"), c(".deb") + ", " + c(".rpm") + ", " + c(".pkg.tar.zst") + " with checks",
         "the native recipes, called by the release"],
        ["Release", c("packaging/rilascio.sh X.Y.Z-R") + " (release)", c("costruzione-uscita/rilasci/remotix-X.Y.Z-R.run"),
         "the one deliverable (" + rif("The release command") + ")"],
    ], "«TAB» — How to build what") + \
    p("Why containers: on 14 Aug 2026 the C code could not be built at all — the laptop lacked ngtcp2 and nghttp3, "
      "the test machine's live root file system had no compiler, and the container there did not see the source tree. "
      "A rootless podman container on the laptop, with the tree mounted and the binary coming out on the host, "
      "solved it (the header of " + c("src/Contenitore") + ", the Containerfile). The per-target containers came with phase 17 (" + c("fasi/17-l-installatore.md") + " §6.2): the "
      "binary is not portable between distributions (OpenSSL, libei, PipeWire… differ in version and soname), so each target "
      "is compiled inside its own root.") + \
    note("everything temporary goes under " + c("costruzione-uscita/") + " (ignored by git) or "
         + c("installatore/.cache/") + ", never " + c("/tmp") + ": on the development laptop " + c("/tmp") + " is "
         "nearly full and " + c("~/.cache") + " links to it.", "Disk.")

DEP_ROWS = [
    ["ngtcp2 ≥ 1.25 + " + c("ngtcp2_crypto_ossl"), "QUIC, and the bridge to OpenSSL's native QUIC API",
     c("trasporto.c") + " (transport)" + ", " + c("tls.c"), "built from source, static (" + rif("Static ngtcp2 and nghttp3") + ")"],
    ["nghttp3 ≥ 1.18", "HTTP/3 and extended CONNECT", c("webtransport.c"), "built from source, static"],
    ["OpenSSL ≥ 3.5", "TLS 1.3 with the native QUIC API; X.509 for the two certificates", c("tls.c") + ", "
     + c("certificati.c") + " (certificates)", "distribution"],
    ["libpam", "authentication", c("autenticazione.c") + ", " + c("aiutante.c") + " (the PAM helper)", "distribution"],
    ["gio-2.0 ≥ 2.80", "the session bus: virtual monitor and Mutter's ScreenCast (named once, though two parts use it)",
     c("sessione.c") + " (session)" + ", " + c("mutter.c"), "distribution"],
    ["libpipewire-0.3 ≥ 0.3.48", "the frame stream; audio", c("cattura.c") + " (capture)" + ", " + c("suono.c") + " (sound)", "distribution"],
    ["libdrm", "only the " + c("DRM_FORMAT_MOD_*") + " headers: in CFLAGS, never in LIBS", c("cattura.c"),
     "distribution"],
    ["libva, libva-drm", "encoding on the card (since phase 18, without ffmpeg)", c("vadiretta.c") + " (direct VA-API)" + ", "
     + c("codificatore.c") + " (encoder)", "distribution"],
    ["vulkan ≥ 1.3.274", "the loader only; Vulkan Video tried before VA-API (phase 19); the SPIR-V shader is in the "
     "tree", c("vulkanvideo.c"), "distribution"],
    ["opus ≥ 1.3", "audio encoding (since phase 18)", c("audio.c"), "distribution"],
    ["libei-1.0 ≥ 1.1.0", "input injection on GNOME and KDE", c("input.c"), "distribution"],
    ["xkbcommon", "which key produces this letter in this layout", c("tastiera.c") + " (keyboard)", "distribution"],
    ["wayland-client + " + c("wayland-scanner"), "KWin and wlroots protocols, generated at every build",
     c("kwin.c") + ", " + c("wlroots.c"), "distribution"],
    ["gbm", "the GPU buffer labwc copies into (wlroots card path)", c("wlroots.c"), "distribution"],
    [c("-ldl"), "libselinux opened with " + c("dlopen") + " on Fedora and Alma", c("figlio.c") + " (the per-user child)", "libc"],
    [c("-lm"), "the test tone's " + c("sin()") + " — kept explicit, not left to glibc", c("webtransport.c"), "libc"],
]

S_DEPS = p("The Makefile's header lists every library with the piece of code that needs it, because “which library "
           "is this for?” is the question asked the day one is missing (" + c("LEZIONI.md") + " §2.5-bis: libraries "
           "installed by hand become invisible within a day). Since phase 18 there is no ffmpeg; since phase 19 no "
           "software encoder (OpenH264, SVT-AV1).", lead=True) + \
    table(["Library", "What for", "Code", "Where it comes from"], DEP_ROWS, "«TAB» — The declared build dependencies of "
          + c("src/Makefile")) + \
    table(["pkg-config module", "Minimum checked by " + c("make dipendenze") + " (dependencies)"],
          [[c(m), "none (presence only)" if v == "0" else esc(v)] for m, v in MINIMI],
          "«TAB» — " + c("MINIMI") + " (minimums), read from " + c("src/Makefile") + " when the manual is built") + \
    p(c("make dipendenze") + " checks each module and then compiles a one-line program per header ("
      + "the ngtcp2, OpenSSL, PAM, VA-DRM, Vulkan headers…). It has three outcomes, "
      "and says which: OK, NO (too old, with the version found), and ?? (pkg-config does not know the module — which "
      "with a prefix may only mean the " + c(".pc") + " is not on the path). The package recipes run it before "
      "compiling (" + c("override_dh_auto_configure") + ", the PKGBUILD's " + c("build()") + ").") + \
    warn("the catalogue's minimum component table says libei 1.3 and libopus 1.4; the Makefile, "
         + c("packaging/debian/control") + " and " + c("remotix.spec") + " say libei 1.1 and opus 1.3. Not settled yet "
         "which is the real floor.", "Doc vs code.")

S_MAKEFILE = p(c("src/Makefile") + " builds one program, " + c("remotix") + ", from " + str(len(SORGENTI))
               + " C files and " + str(len(PROTOCOLLI)) + " Wayland protocols. " + c("make") + " (target "
               + c("tutto") + ", “all”) runs " + c("impronte") + " (fingerprints) first, then links.", lead=True) + \
    table(["Variable / target", "What it is"], [
        [c("SORGENTI") + " (sources)", ", ".join(c(s) for s in SORGENTI)],
        [c("PROTOCOLLI") + " (protocols)", ", ".join(c(x) for x in PROTOCOLLI) + " — XML in " + c("src/protocolli/") + "; "
         + c("wayland-scanner") + " generates the client header and the private code of each at every "
         "build (only the XML is in git)"],
        [c("CFLAGS"), c("-O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter") + " by default ("
         + c("?=") + "); then " + c("override CFLAGS +=") + " adds " + c("-D_GNU_SOURCE") + " and the pkg-config flags"],
        [c("LIBS"), c("-lngtcp2_crypto_ossl") + " first, then " + c("-lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm")
         + " and the pkg-config libraries"],
        [c("PREFISSO") + " (prefix)", "where ngtcp2/nghttp3 are installed when pkg-config does not find them: the libdir is asked to "
         "pkg-config <i>inside</i> the prefix (" + c("PKG_CONFIG_LIBDIR") + ", without " + c("PKG_CONFIG_PATH")
         + "), then " + c("-L") + " and " + c("-rpath")],
        [c("GEMELLO") + " (twin)", "the twin copy to compare (" + c("../banchi/rcp") + " by default, " + c("nessuno")
         + " (none) to declare not comparing)"],
        [c("impronte"), "the twin-copy check (" + rif("The twin-copy check") + ")"],
        [c("dipendenze"), "the dependency check (" + rif("Declared build dependencies") + ")"],
        [c("banco-w1"), "the wlroots capture bench " + c("banchi/13-w1-un-fotogramma.c") + " (one frame), linked "
         "with the <i>product's</i> " + c("wlroots.o") + " and " + c("registro.o") + " (the log), not a copy"],
        [c("pulisci") + " (clean)", "removes objects, binary and generated protocol files"],
    ], "«TAB» — The Makefile, part by part") + \
    p("Each object lists the headers it includes (the “seams” between parts written in parallel): without them "
      + c("make") + " would keep an object compiled against yesterday's contract — a program that links and misbehaves "
      "(seen on 14 Aug 2026, when " + c("cattura.o") + " was not rebuilt). Every object depends on " + c("registro.h")
      + " since it became a header of macros (25 Sep 2026). " + c("main.o") + " deliberately does not depend on the "
      "capture and encoder headers: those parts run in the per-user child, never in the root parent. "
      + c("vulkanvideo.o") + " alone gets " + c("-Wno-missing-field-initializers") + " (Vulkan structures are filled by "
      "name).") + \
    table(["Rule in the Makefile", "Why"], [
        [c("override CFLAGS +=") + ", never a plain " + c("+="), "the package recipes and " + c("src/costruisci.sh")
         + " pass CFLAGS; a plain " + c("+=") + " would vanish and the error would be “No such file” on the gio header"
         + ", naming no option"],
        [c("-std=gnu11") + ", not " + c("c11"), c("accept4") + ", " + c("SOCK_NONBLOCK") + ", ancillary messages"],
        [c("ngtcp2_crypto_ossl") + " before " + c("ngtcp2"), "the linker resolves left to right"],
        ["gio-2.0 named once", "two parts need it; named twice it doubles the " + c("-l") + " flags unnoticed"],
        ["libdrm only in CFLAGS", "only macros are used; linking it would hide the day the include goes"],
    ], "«TAB» — Rules that look odd and are on purpose")

S_TWINS = p(c("rcp.c") + ", " + c("rcp.h") + " and " + c("autenticazione.c") + " exist twice in the repository — in "
            + c("src/") + " and in " + c("banchi/rcp/") + " — because they are the same module mounted on two hosts: "
            "the product server and the graft into ngtcp2's example server used by the benches. Until 10 Aug 2026 they "
            "were identical by luck, not by construction.", lead=True) + \
    table(["Situation", "Outcome of " + c("make impronte")], [
        ["the copies match", "prints " + c("OK") + " with the md5 of each file, and compiles"],
        ["the copies diverge", "prints the " + c("diff") + " and refuses to compile"],
        ["the twin folder is missing", "refuses, unless the builder declares it with " + c("GEMELLO=nessuno") + " — "
         "“I did not look” must never look like “no differences”"],
    ], "«TAB» — The three outcomes of the twin-copy check (finding R12.3)") + \
    p("This is why the development container mounts the whole tree, not " + c("src/") + ", and why every package "
      "recipe copies " + c("banchi/rcp/") + " next to " + c("src/") + ". The concrete case it prevents: changing the "
      "ban duration in " + c("src/rcp.c") + " while the benches keep testing the old copy and stay green.")

S_DEVBOX = p(c("src/Contenitore") + " is the every-day build image, " + c("localhost/remotix-costruzione")
             + " (the REMOTIX build image): Debian 13 "
             "with the declared development packages, and nghttp3 1.18.0 and ngtcp2 1.25.0 built from source at fixed "
             "tags (shared libraries in " + c("/usr/local") + ", unlike the package images). Extra packages "
             "(" + c("libgbm-dev") + ", " + c("libopus-dev") + ", " + c("libvulkan-dev") + ") sit in layers of their "
             "own at the end, so the ngtcp2 layer stays cached and the image rebuilds in seconds.", lead=True) + \
    code("""podman build -t remotix-costruzione -f src/Contenitore src/   # once, about 4 minutes
bash src/costruisci-in-contenitore.sh              # builds src/remotix
bash src/costruisci-in-contenitore.sh dipendenze   # only says what is there
bash src/costruisci-in-contenitore.sh pulisci      # removes the objects""", "bash", "Every-day build") + \
    table(["Choice", "Why"], [
        [c("--userns=keep-id"), "files coming out belong to the user, not to a remapped uid that would need sudo to "
         "delete"],
        ["the whole tree mounted at " + c("/albero"), "the twin-copy check needs " + c("../banchi/rcp")],
        ["no " + c(":Z"), "it would relabel the user's source tree"],
        ["missing image ⇒ exit 3 with the command to type", "an absent image is not a failure to guess"],
        ["after a successful build, " + c("banchi/04-b31-tela.c") + " (the canvas bench) is compiled with "
         + c("src/rcp.c") + " by the host's gcc, if there is one, and run", "the strongest bench on the most delicate module stayed red for a day in August because nobody "
         "ran it; now it runs where everybody passes anyway, in two seconds, and does not stop the build"],
    ], "«TAB» — Decisions in " + c("costruisci-in-contenitore.sh")) + \
    note(c("libwayland-dev") + " (for " + c("wayland-client") + " and " + c("wayland-scanner") + ") is not named in "
         + c("src/Contenitore") + ", while every " + c("src/costruzione/Contenitore.*") + " and the Debian "
         "Build-Depends name it; the image builds today, so it arrives as a dependency of another package. Not settled "
         "yet: name it explicitly.", "Gap.") + \
    p(c("src/costruisci.sh") + " is the older road, run <i>inside</i> the test machine's container (" + c("enter.sh")
      + "): it looks for ngtcp2/nghttp3 in " + c("PREFISSO") + ", " + c("NGTCP2") + ", " + c("NGHTTP3") + " (defaults "
      "under " + c("/srv/src/b2") + "), requires OpenSSL ≥ 3.5, deletes the old binary before building (so “it exists” "
      "means “it is new”), and then greps the binary for marker strings, with a positive control that the search tool "
      "itself works. Last, if they are missing and it can write them, it installs " + c("/etc/pam.d/remotix")
      + " from " + c("src/remotix.pam") + " and " + c("/etc/remotix/utenti-negati") + " (the denied users) with "
      + c("root") + ".")

TARGETS = [
    ["debian13", c("debian:13"), "apt", "1.11 / 1.8", "also the .deb tools layer (debhelper, lintian)"],
    ["ubuntu2604", c("ubuntu:26.04"), "apt", "1.16", "also the .deb tools layer"],
    ["fedora44", c("registry.fedoraproject.org/fedora:44"), "dnf", "1.21", c("vulkan-loader-devel") + " 1.4.341 (measured 1 Oct 2026)"],
    ["alma10", c("almalinux:10"), "dnf + EPEL + CRB", "1.22 (EPEL)", "libei and pipewire devel in CRB, opus in EPEL"],
    ["arch", c("archlinux:latest"), "pacman", "1.25 with crypto_ossl", "labwc, wlr-randr, wireplumber, "
     "pipewire-pulse installed because makepkg wants runtime depends present"],
    ["tumbleweed", c("registry.opensuse.org/opensuse/tumbleweed:latest"), "zypper", "1.25 with crypto_ossl",
     "gbm asked as " + c("pkgconfig(gbm)")],
    ["leap16", c("registry.opensuse.org/opensuse/leap:16.0"), "zypper", "1.6 (unusable)",
     "gbm asked as " + c("pkgconfig(gbm)")],
    ["ubuntu2404", c("ubuntu:24.04"), "apt", "—", "only to see where it stops (OpenSSL 3.0 has no QUIC API); not "
     "released"],
]

S_TARGETS = p(c("src/costruzione/Contenitore.<target>") + " is one image per target, "
              + c("localhost/remotix-costruzione-<target>") + ", with the distribution's development packages and the "
              "same static QUIC libraries for all. The image is the build environment of that target's package.",
              lead=True) + \
    table(["Target", "Base image", "Manager", "ngtcp2 / nghttp3 the distribution has", "Notes"], TARGETS,
          "«TAB» — The per-target build images (the distribution's own versions are why ours are built)") + \
    p(c("src/costruzione/costruisci-tutti.sh [target…]") + " (all eight by default) builds the image, copies "
      + c("src/") + " and " + c("banchi/rcp/") + " into " + c("$CACHE/albero-<target>") + " (a copy of the tree) — "
      "eight targets on the same " + c("src/") + " would step on each other's objects — runs " + c("make pulisci")
      + " and " + c("make tutto") + " inside the image, and writes in "
      + c("costruzione-uscita/<target>/") + ": the binary, " + c("immagine.log") + " (image build), "
      + c("compilazione.log") + " (compilation), " + c("versioni.txt") + " (the versions of OpenSSL, opus, libva, "
      "libei, pipewire, glib, gcc, ngtcp2, nghttp3), " + c("ldd.txt") + " run inside the target, and "
      + c("esito.txt") + " (one-line outcome: compiles yes/no, ldd clean yes/no). " + c("ldd") + " is not clean if any library is "
      "“not found”, if ngtcp2/nghttp3 are dynamic, if ffmpeg (" + c("libav*") + ", " + c("libswscale") + ", "
      + c("libx264/5") + ") or a software encoder (" + c("openh264") + ", " + c("SvtAv1") + ") appears.")

S_QUIC = p(c("src/costruzione/quic-statiche.sh") + " (static QUIC) builds nghttp3 " + c("v1.18.0") + " and ngtcp2 " + c("v1.25.0")
           + " (with " + c("-DENABLE_OPENSSL=ON") + ", which produces " + c("libngtcp2_crypto_ossl") + ") from their git "
           "tags with CMake and Ninja, <b>static only</b>, PIC, libdir fixed to " + c("lib") + ", into "
           + c("/usr/local/lib") + ". It fails if any " + c(".so") + " of them is there: the linker would prefer it.",
           lead=True) + \
    table(["Choice", "Why"], [
        ["inside the binary (D2, " + c("DECISIONI.md") + " §10.6)", "ngtcp2 ≥ 1.25.0 is required by the "
         + c("NGTCP2_STREAM_CLOSE2_FLAG_*") + " flags of " + c("trasporto.c") + ", with the " + c("ngtcp2_crypto_ossl")
         + " bridge, and almost no distribution has it; security updates of these two become REMOTIX's job"],
        ["static, not a private " + c(".so"), "no library outside the system paths; the "
         + c("ld.so.conf.d") + " entry the test machines used (which put our ngtcp2 in front of the system's, also "
         "used by curl) disappears"],
        ["the same fixed version everywhere, even where Arch and Tumbleweed have 1.25", "one transport behaviour to "
         "test across families"],
        ["fixed tags, never " + c("main"), "an image rebuilt a month later must be the same image"],
    ], "«TAB» — Why ngtcp2 and nghttp3 are built this way") + \
    p("Each recipe then proves the link: " + c("debian/rules") + " and the spec refuse to build if pkg-config reports "
      "another version than the one declared (" + c("Static-Built-Using") + ", " + c("Provides: bundled(…)")
      + "), and write " + c("/usr/share/remotix/incorporate.json") + " (" + c('{"formato":"remotix-incorporate/1",…}')
      + ") with the versions actually linked — static libraries leave no version string in the binary. The Arch "
      "recipe builds the same two libraries inside " + c("build()") + " from the release tarballs, with fixed sha256.")

S_DEB = p(c("packaging/debian/") + " is copied to " + c("debian/") + " in a fresh copy of the tree by "
          + c("src/costruzione/costruisci-deb.sh") + " and built with " + c("dpkg-buildpackage -b") + " inside "
          + c("Contenitore.debian13") + " or " + c(".ubuntu2604") + " (debhelper 13, source format 3.0 native).",
          lead=True) + \
    table(["Field", "Value", "Why"], [
        ["Build-Depends", "libssl-dev (≥ 3.5), libpam0g-dev, libglib2.0-dev (≥ 2.80), libpipewire-0.3-dev, libdrm-dev, "
         "libva-dev, libopus-dev, libei-dev (≥ 1.1), libxkbcommon-dev, libgbm-dev, libwayland-dev, libvulkan-dev "
         "(≥ 1.3.274)", "ngtcp2/nghttp3 are not there: the container brings them"],
        ["Depends", c("${shlibs:Depends}") + ", libpam-systemd, libpam-modules, passwd, systemd, dbus-user-session, "
         "pipewire, wireplumber", "what the binary uses at run time and dpkg cannot see: PAM modules, the user bus, the "
         "PipeWire <i>daemon</i> (minimal installs lack it: no desktop on openSUSE GNOME without it, T10)"],
        ["Recommends", "va-driver-all | va-driver, mesa-vulkan-drivers, labwc, wlr-randr, xwayland", "the card's VA and "
         "Vulkan drivers; the XFCE/LXQt compositor pieces (a .deb cannot say “only if XFCE”)"],
        ["Static-Built-Using", c("ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0)"), "names the bundled code (SBOM, R24)"],
    ], "«TAB» — " + c("debian/control")) + \
    table(["Step of " + c("debian/rules"), "What"], [
        ["configure", c("make -C src dipendenze")],
        ["build", "pkg-config must say 1.25.0 and 1.18.0; " + c("src/rcp.c") + " must have " + c("BANCO_ACCESO 0")
         + " (the bench function switched off, R13); " + c("make tutto") + " with " + c("CFLAGS") + " = dpkg's hardening flags + " + c("-std=gnu11")
         + " + warnings"],
        ["install", "the files of " + rif("What the packages install") + ", plus " + c("incorporate.json")],
        ["systemd", c("dh_installsystemd --no-enable --no-start --restart-after-upgrade") + ": never enabled or "
         "started by the package; on upgrade restarted only if it was active or enabled"],
    ], "«TAB» — " + c("debian/rules")) + \
    p("After the build " + c("costruisci-deb.sh") + " runs lintian and checks the <i>finished</i> package, not the "
      "tree, writing one line per check in " + c("controlli.txt") + " (checks):") + \
    table(["Check", "How"], [
        ["R13 — bench function off", "the marker sentence absent from the binary extracted from the .deb <b>and</b> "
         "present in an " + c("rcp.o") + " built with " + c("BANCO_ACCESO 1") + " (the positive control: otherwise "
         "“not found” could mean “cannot search”); no bench option in the unit's ExecStart"],
        ["R14 — no bench files", "the file list against a blacklist: test files (" + c("prova") + "), provisioning, sudoers, gpu-udev, restart "
         "scripts, " + c("ld.so.conf") + ", " + c("banchi") + ", " + c("/opt/") + ", keys and certificates"],
        ["R4 — no missing libraries", c("ldd") + " of the extracted binary inside the target: nothing “not found”, no "
         "dynamic ngtcp2/nghttp3"],
        ["R23 — reproducible (" + c("DUE=1") + ")", "a second build in a second clean copy: the two .deb must be "
         "identical byte for byte"],
    ], "«TAB» — Checks on the finished .deb") + \
    p("Measured 29 Sep 2026 (commit cdefd1f): lintian 0 errors, 0 warnings; R13, R14, R4 green; R23 two identical "
      "builds on Debian 13 and Ubuntu 26.04. After " + c("apt install") + " on debian13-gnome and ubuntu2604-kde the "
      "service was disabled and inactive, nothing listened on 7447, groups were unchanged (fasi/17 §13.2).")

S_RPM = p(c("packaging/rpm/remotix.spec") + " is one spec with " + c("%if 0%{?fedora}") + ", " + c("0%{?rhel}")
          + " and " + c("0%{?suse_version}") + " branches, as Cockpit does, built by "
          + c("packaging/rpm/costruisci-rpm.sh") + " in the target's image (fedora44, alma10, tumbleweed, leap16) with "
          + c("rpmbuild -ba") + " and rpmlint.", lead=True) + \
    table(["Topic", "What the spec does"], [
        ["Requires", "automatic by soname (libva, libopus, libssl with " + c("OPENSSL_3.5.0") + ", libpam, …); by hand "
         "only what rpm cannot see: " + c("pipewire") + ", " + c("wireplumber") + ", and on Fedora and Alma "
         + c("firewalld-filesystem")],
        ["Desktop-bound requires", "<b>conditional</b>, never pulling a desktop: " + c("(labwc if xfce4-session)") + ", "
         + c("(wlr-randr if lxqt-session)") + ", " + c("(xorg-x11-server-Xwayland if labwc)") + " / "
         + c("(xwayland if labwc)") + ", a scalable font " + c("if labwc") + ", " + c("(breeze6-wallpapers if plasma6-workspace)")
         + " on openSUSE"],
        ["Recommends", "on Fedora " + c("mesa-dri-drivers") + ", the Intel VA driver and " + c("mesa-vulkan-drivers")
         + "; on openSUSE " + c("Mesa-libva") + " and " + c("intel-media-driver") + "; on Alma nothing (RHEL 10's Mesa "
         "has no VA-API and EPEL has no Intel driver). The distribution's drivers do not encode H.264 for some cards, "
         "and the package does not add RPM Fusion or Packman"],
        ["Bundled", c("Provides: bundled(ngtcp2) = 1.25.0") + ", " + c("bundled(nghttp3) = 1.18.0") + "; "
         + c("%build") + " fails if pkg-config reports other versions"],
        ["Flags", c("%{optflags} -std=gnu11") + " in the environment; on openSUSE also " + c("-fPIE -pie")],
        ["PAM", c("remotix.pam.fedora") + " in " + c("/etc/pam.d") + " (" + c("%config(noreplace)") + "); "
         + c("remotix.pam.suse") + " in " + c("/usr/lib/pam.d") + " on openSUSE"],
        [c("remotix-selinux"), "noarch subpackage: the policy module (" + c("remotix_t") + ", "
         + c("remotix_exec_t") + ", " + c("remotix_port_t") + ", " + c("remotix_var_lib_t") + ", " + c("remotix_var_run_t") + ") built against "
         "<i>that</i> distribution's policy, and " + c("remotix_porta.cil") + " (the port) for port 7447 TCP and UDP; required "
         "only " + c("if selinux-policy-targeted") + "; " + c("rx_selinux_permissivo") + " (permissive) builds a permissive domain "
         "for measuring, never for release"],
        [c("%ghost"), "the certificates, the " + c(".nostro") + " (“ours”) markers and the ban files the service creates, so a remove "
         "cleans them (measured on Tumbleweed in T3: without them " + c("/var/lib/remotix") + " stayed)"],
        ["Scriptlets", c("%post") + " only " + c("%tmpfiles_create") + " (no " + c("%systemd_post") + ": a machine "
         "preset “enable *” would enable the service); " + c("%preun") + " stops and disables; " + c("%postun")
         + " restarts on upgrade only if running; " + c("%posttrans") + " calls " + c("post-upgrade")],
    ], "«TAB» — The RPM recipe") + \
    p("The rpm unit starts the binary directly, without " + c("/bin/sh -c") + ": under SELinux systemd moves to "
      + c("remotix_t") + " only when it executes " + c("remotix_exec_t") + " itself (T6). The Debian unit keeps "
      + c("sh -c 'exec …'") + " to expand " + c("REMOTIX_PORTA") + " and " + c("REMOTIX_OPZIONI") + ". "
      + c("costruisci-rpm.sh") + " validates " + c("remotix-firewalld.xml") + " as XML first: firewalld silently drops "
      "a malformed service (a " + c("--") + " inside a comment, measured on Fedora 44, 29 Sep 2026).")

S_ARCH = p(c("packaging/arch/PKGBUILD") + " is built by " + c("packaging/arch/costruisci.sh [commit]") + ": "
           + c("git archive") + " of " + c("src/") + ", " + c("banchi/rcp/") + " and " + c("packaging/arch/")
           + " at that commit, then " + c("makepkg") + " as the user in " + c("localhost/remotix-costruzione-arch")
           + ", namcap in a throw-away container, and the R14 blacklist. Unlike .deb and .rpm, uncommitted changes "
           "never enter an Arch package.", lead=True) + \
    table(["Topic", "What the PKGBUILD does"], [
        ["Paths", "the binary in " + c("/usr/lib/remotix/remotix") + " (Arch has no libexec: namcap “ELF file outside "
         "of a valid path”); the KWin " + c(".desktop") + " and the unit follow"],
        ["depends by soname", c("libopus.so") + ", " + c("libssl.so") + ", " + c("libva.so") + "… become the exact "
         "sonames the binary uses: a library update with the same soname goes through, a new soname makes "
         + c("pacman -Syu") + " refuse until we rebuild — “better a refused update than one that breaks silently” "
         "(fasi/17 §6.2); an exact version would block every security update"],
        ["Unconditional runtime depends", c("labwc") + ", " + c("wlr-randr") + " (pacman has no conditional depends; "
         "as optdepends they would never be installed), " + c("pipewire") + ", " + c("wireplumber") + ", "
         + c("pipewire-pulse") + " (the xfce4 group has no audio: measured 29 Sep on arch-xfce)"],
        ["optdepends", c("vulkan-radeon") + ", " + c("nvidia-utils")],
        ["Build", "static nghttp3/ngtcp2 in " + c("$srcdir/quic") + " first on " + c("CPATH") + "/" + c("LIBRARY_PATH")
         + " (Arch's own " + c("libngtcp2") + " may be present, pulled by curl); " + c("-ffile-prefix-map")
         + " so ngtcp2's asserts do not carry " + c("$srcdir") + "; " + c("!lto !debug")],
        [c("check()"), c("BANCO_ACCESO 0") + "; " + c("ldd") + " shows no ngtcp2/nghttp3 and nothing missing"],
        [c("remotix.install"), "post_install prints a notice only; post_upgrade " + c("systemctl try-restart")
         + " then " + c("post-upgrade") + "; pre_remove " + c("disable --now") + "; post_remove removes certificates "
         "and ban"],
        ["Reproducible", c("SOURCE_DATE_EPOCH") + " = commit time (without it, same binary but different packages "
         "for " + c("builddate") + " and mtree dates, measured 29 Sep)"],
    ], "«TAB» — The Arch recipe") + \
    warn("the Arch unit has no " + c("EnvironmentFile") + " for " + c("/etc/remotix/remotix.conf.d/*.conf") + " (it sets "
         + c("REMOTIX_PORTA=7447") + " and " + c("REMOTIX_NOME=%H") + " with " + c("Environment=") + ") and no "
         + c("--journal") + ", and the package ships neither " + c("/usr/share/remotix/remotix.conf") + " nor the "
         + c("remotix.conf.d") + " folder. The installer's port step writes " + c("/etc/remotix/remotix.conf.d/porta.conf") + ": on Arch a "
         "non-default port is not applied, " + c("start-service") + " waits for a port nobody opens, and the "
         "installation rolls back.", "Code finding.")

INSTALLED = [
    ["the server", c("/usr/libexec/remotix/remotix"), c("/usr/libexec/remotix/remotix"), c("/usr/lib/remotix/remotix")],
    ["the page", c("/usr/share/remotix/pagina.html"), "same", "same"],
    ["defaults", c("/usr/share/remotix/remotix.conf") + " (" + c("REMOTIX_PORTA") + ", " + c("REMOTIX_OPZIONI") + ")",
     "same", "— (in the unit)"],
    ["administrator's choices", c("/etc/remotix/remotix.conf.d/") + " (empty)", "same", "—"],
    ["linked versions", c("/usr/share/remotix/incorporate.json"), "same", "same"],
    ["unit", c("remotix.service") + " (via " + c("sh -c") + ")", c("remotix.service") + " (direct exec)",
     c("remotix.service") + " (direct, no " + c("--journal") + ")"],
    ["tmpfiles", c("/var/lib/remotix") + " 0700, " + c("/run/remotix") + " 0700", "same", c("/var/lib/remotix")
     + " only"],
    ["PAM", c("/etc/pam.d/remotix") + " (" + c("src/remotix.pam") + ", conffile)", c("/etc/pam.d/remotix")
     + " or " + c("/usr/lib/pam.d/remotix") + " (openSUSE)", c("/etc/pam.d/remotix") + " (" + c("remotix.pam.arch")
     + ", backup)"],
    ["who cannot log in", c("/etc/remotix/utenti-negati") + " = " + c("root"), "same", "same"],
    ["KWin capture permission", c("/usr/share/applications/org.kde.remotix.desktop"), "same", "same (" + c("Exec=")
     + " the Arch path)"],
    ["guards, switched off", c("/usr/share/remotix/cinture/") + " (the guards): no power-off rule, no-suspend, keys", "same", "same"],
    ["firewall definition", c("/etc/ufw/applications.d/remotix") + " (profile REMOTIX)", c("/usr/lib/firewalld/services/remotix.xml"),
     c("/usr/lib/firewalld/services/remotix.xml")],
    ["SELinux", "—", c("remotix-selinux") + " subpackage", "—"],
]

S_INSTALLED = p("The three families install the same pieces in the same places, except where the distribution's "
                "conventions differ. The package carries <b>inert pieces</b> only: it never enables or starts the "
                "service, never touches groups, firewall or system configuration (" + c("DECISIONI.md") + " §10.12, kept by §10.36).", lead=True) + \
    table(["Piece", ".deb", ".rpm", "Arch"], INSTALLED, "«TAB» — What the REMOTIX package installs, per family") + \
    p("The KWin permission file is byte-for-byte what the product would check (" + c("kwin_verifica_permesso()")
      + "), so the product finds it right and never writes to " + c("/usr") + ". Never in any package (fasi/17 §6.4, R14): test "
      "users, bench sudoers, " + c("gpu-udev.sh") + ", " + c("riavvia-*.sh") + ", " + c("provisiona.sh") + ", "
      + c("ld.so.conf.d") + " entries.") + \
    table(["Removed by the package scripts", ".deb (" + c("postrm purge") + ")", ".rpm (on erase)", "Arch (" + c("post_remove") + ", every removal)"], [
        ["certificates and ban", "yes", "yes (" + c("%ghost") + ")", "yes"],
        [c("/run/remotix"), "yes", "ghost", "—"],
        [c("/var/lib/remotix"), "only if empty: the engine's history is not the package's", "rpm removes the empty dirs",
         "only if empty"],
    ], "«TAB» — What the package scripts clean") + \
    warn("the package comments (and the Debian " + c("remotix.ufw") + " comment) still say the guards, the ufw profile "
         "and the firewalld service are “mounted by the engine with consent”. Since §10.36 the engine does none of this: "
         "the guards ship switched off and nothing switches them on; the firewall definitions are only names an "
         "administrator may use. Not settled yet: whether the guard files stay in the packages.", "Doc vs code.")

S_ENGINE = p(c("installatore/costruisci.sh") + " (the installer's build script) builds "
             + c("installatore/uscita/remotix-install") + " (" + c("uscita") + ": output) in "
             + c("docker.io/library/golang:1.25") + ": " + c("CGO_ENABLED=0") + ", " + c("GOFLAGS=-mod=vendor") + ", "
             + c("GOPROXY=off") + ", " + c("GOTOOLCHAIN=local") + ", " + c("-trimpath -ldflags '-s -w'") + ", Go caches "
             "in " + c("installatore/.cache/") + ". Go is not installed on the laptop and does not need to be.",
             lead=True) + \
    code("""installatore/costruisci.sh            # builds uscita/remotix-install
installatore/costruisci.sh prove      # gofmt -l, go vet ./..., go test -count=1 ./...
installatore/costruisci.sh go ...     # any go command in the same container
RX_VERSIONE=1.0.0 installatore/costruisci.sh   # -X remotix/installatore/motore.VersioneMotore=1.0.0""",
         "bash", "Building the engine") + \
    p("Static and without cgo, the engine runs on every distribution before any package is there — Debian's glibc or "
      "Alma's. Until 10 Oct 2026 there was a second, cgo build for the Gio GUI on Debian 12's glibc; with the GUI gone "
      "(§10.31) " + c("vendor/") + " went from 37 to 14 MB and there is one build.") + \
    p(c("packaging/motore/pacchetti-motore.sh") + " (engine packages; called by the release) packages that one binary three times, "
      "refusing if the binary's " + c("version") + " is not the release's:") + \
    table(["Package", "Built with", "Contents and scripts"], [
        [c("remotix-install_V-R_amd64.deb"), c("dpkg-deb --root-owner-group -Zxz") + ", " + c("SOURCE_DATE_EPOCH"),
         c("/usr/bin/remotix-install") + ", " + c("/usr/share/remotix-install/README") + "; Depends systemd; postinst "
         "on upgrade: " + c("post-upgrade")],
        [c("remotix-install-V-R.x86_64.rpm"), c("rpmbuild") + " in " + c("registry.fedoraproject.org/fedora:44") + " with "
         + c("remotix-install.spec"), "the same files; " + c("%posttrans") + " " + c("post-upgrade") + "; no "
         "brp-strip (" + c("__os_install_post") + " nil): measured 30 Sep, rpm's strip changed the binary, and the "
         "package must hold byte for byte the engine that installed it"],
        [c("remotix-install-V-R-x86_64.pkg.tar.zst"), c("makepkg --nodeps") + " in the Arch image", "the same files; " + c("!strip") + "; " + c("post_upgrade") + " " + c("post-upgrade")],
    ], "«TAB» — The engine packages (" + c("packaging/motore/") + ")") + \
    note("the engine's Arch package is built in " + c("localhost/remotix-costruzione-arch") + " even when " + c("BERSAGLI")
         + " (the targets) excludes Arch: the image must exist for any release.", "Release prerequisite.")

REL_FLOW = flow([
    ("1. Tree", "a commit, nothing dirty", "dark"),
    ("2. Engine", "tests, static build", "blue"),
    ("3. Product", ".deb · .rpm · Arch", "blue"),
    ("4. Engine pkgs", "three families", "blue"),
    ("5. .run", "payload, header, sha256", "navy"),
    ("6. Summary", "RELEASES.txt, message", "green"),
], "«FIG» — The steps of " + c("packaging/rilascio.sh") + "; it stops at the first error", width=900)

S_RELEASE = p(c("packaging/rilascio.sh X.Y.Z-R") + " is the one command of a release (for example " + c("0.17.0-7")
              + ": X.Y.Z is REMOTIX's version, R the package revision of a rebuild). The same version goes to everything: "
              "the product packages, the engine and its packages.", lead=True) + REL_FLOW + \
    table(["Step", "What it does", "Stops if"], [
        ["1. the tree", "records " + c("git rev-parse HEAD") + " in the log", "uncommitted changes in " + c("src")
         + ", " + c("packaging") + ", " + c("installatore") + ", " + c("banchi/rcp") + " (unless " + c("RX_SPORCO=1")
         + ", for tests only); the " + c(".run") + " of that version already exists — a new content needs a new revision"],
        ["2. the engine", c("costruisci.sh prove") + ", then the static build with " + c("RX_VERSIONE=X.Y.Z") + "; "
         "prints the catalogue line", "any " + c("FAIL") + " or " + c("gofmt:") + " line; the binary does not say X.Y.Z"],
        ["3. the product", c("costruisci-deb.sh") + " (debian13, ubuntu2604), " + c("costruisci-rpm.sh") + " (fedora44, "
         "alma10, tumbleweed, leap16), " + c("packaging/arch/costruisci.sh") + ", with " + c("RX_VERSIONE")
         + "/" + c("RX_REVISIONE"), "a recipe fails; an rpm target without " + c("pacchetto=si") + " (package = yes) in its "
         + c("esito.txt")],
        ["4. the engine packages", c("pacchetti-motore.sh"), "a package fails"],
        ["5. the .run", "the payload: " + c("packages/<target>/") + " = product packages + the engine package of that "
         "family, the static engine at the root, " + c("tar --sort=name --owner=0 --group=0 --numeric-owner "
         "--mtime=@<commit time>") + " | " + c("gzip -n -9") + "; then " + c("run.sh") + " with " + c("VERSIONE")
         + " (version) and " + c("PAYLOAD_SHA256") + " filled in by " + c("sed") + " (checked with grep), the payload "
         "appended, " + c("<run>.sha256") + " written, " + c("sh <run> version") + " run",
         "the header did not take the sha256"],
        ["6. the summary", "a line appended to " + c("RELEASES.txt") + " (version, time, commit, targets, sha256) and "
         "the final message", "—"],
    ], "«TAB» — " + c("rilascio.sh") + " step by step") + \
    table(["Variable", "Default", "Meaning"], [
        [c("BERSAGLI"), c("debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch"), "targets in the " + c(".run")],
        [c("USCITA") + " (output)", c("costruzione-uscita/rilasci"), "where the " + c(".run") + " goes"],
        [c("RX_SPORCO=1") + " (dirty)", "unset", "accept a dirty tree (the packages say so); never for a published release"],
    ], "«TAB» — The release's environment") + \
    p("Work files stay in " + c("costruzione-uscita/rilascio-X.Y.Z-R/") + ": " + c("rilascio.log") + " (the journal of "
      "the release), " + c("prove-motore.log") + " (the engine tests), the product packages, the engine packages, the payload. The rpm "
      "containers leave files owned by another sub-uid, so the folder is removed with " + c("podman unshare rm -rf")
      + ". The final message gives the sha256 to publish next to the file, over HTTPS, and the install command "
      + c("sudo sh remotix-X.Y.Z-R.run") + ".")

RUN_LAYOUT = fig(
    box(150, 20, 600, 56, "Header: installatore/run.sh", "POSIX sh · VERSIONE='X.Y.Z-R' · PAYLOAD_SHA256='…'", "navy")
    + box(150, 84, 600, 26, "__PAYLOAD__", "", "amber", 12)
    + zone(150, 120, 600, 214, "tar.gz payload (reproducible: sorted, owner 0, commit mtime, gzip -n)")
    + box(170, 150, 560, 36, "remotix-install", "the static engine (catalogue inside)", "blue", 12)
    + box(170, 196, 270, 54, "packages/debian13/", "remotix_*.deb, remotix-install_*.deb", "dark", 11.5)
    + box(460, 196, 270, 54, "packages/ubuntu2604/", "same", "dark", 11.5)
    + box(170, 260, 270, 54, "packages/fedora44 · alma10 /", "remotix, remotix-selinux, -install .rpm", "dark", 11)
    + box(460, 260, 270, 54, "packages/tumbleweed · leap16 · arch/", ".rpm / .pkg.tar.zst", "dark", 11),
    900, 344, "«FIG» — The .run file: a shell header, a marker line, then the payload")

S_RUN = p("The " + c(".run") + " is the single installation file of §10.36: a POSIX shell header followed by a "
          "tar.gz. It needs only " + c("tar") + ", " + c("gzip") + ", " + c("sha256sum") + ", " + c("awk") + " and "
          + c("mktemp") + " on the target.", lead=True) + RUN_LAYOUT + \
    table(["Invocation", "What the header does"], [
        [c("sudo sh remotix-X.Y.Z-R.run") + " (= " + c("install") + ")", "root required; extract; run "
         + c("remotix-install install --bundle <dir>/packages") + " with the other arguments"],
        [c("sudo sh … tui"), "the same with " + c("tui")],
        [c("sh … check"), "no root needed; " + c("remotix-install check") + " (without " + c("--bundle") + ")"],
        [c("sh … version"), "prints " + c("REMOTIX X.Y.Z-R") + " without extracting"],
        ["anything else", "usage, exit 1"],
    ], "«TAB» — The commands of the .run") + \
    steps([
        "Find the first line after " + c("__PAYLOAD__") + " with " + c("awk") + "; none ⇒ “the file is damaged (no "
        "payload): download it again”.",
        "Create " + c("/var/tmp/remotix-run.XXXXXX") + " and a trap that removes it on exit, interrupt or termination.",
        "Copy the payload out with " + c("tail -n +N") + " and check its sha256 against " + c("PAYLOAD_SHA256")
        + "; a mismatch ⇒ “the file is damaged (sha256 does not match)”. (An empty value — a header not filled by the "
        "release — skips the check.)",
        "Extract, delete the archive, run the engine, exit with the engine's code.",
    ]) + \
    p("Two sha256 protect the file: the one of the whole " + c(".run") + ", published on the site for the "
      "administrator, and the one of the payload, inside the header, checked every time. The rpm files inside are not "
      "signed: " + c("dnf") + " installs them with " + c("localpkg_gpgcheck=0") + " and " + c("zypper") + " with "
      + c("--allow-unsigned-rpm") + " (measured 30 Sep on tumbleweed-kde: “Signature verification failed [6-File is "
      "unsigned]” otherwise) — only for these files; repository packages stay verified. The runtime side is in the "
      "installer chapter (" + rif("An installation from the .run file") + ").") + \
    note("tested so far only on the laptop and only in its header: extraction, sha256, refusal of a damaged file, "
         + c("check") + " (fasi/17 §6.6.16). A full " + c("install") + " from a released " + c(".run") + " on the "
         "distributions is still to be run.", "Status.")

S_REPRO = p("The goal (R23) is four levels of reproducibility: binary, package, package metadata, and what is "
            "published. What the recipes do for it:", lead=True) + \
    table(["Recipe", "Source of time", "Other measures", "Measured"], [
        [".deb", c("debian/changelog") + " written with the commit date ⇒ " + c("SOURCE_DATE_EPOCH"),
         c("-ffile-prefix-map") + " from dpkg's flags; " + c("DUE=1") + " builds twice", "identical .deb on Debian 13 "
         "and Ubuntu 26.04, 29 Sep 2026"],
        ["Arch", c("SOURCE_DATE_EPOCH") + " = commit time", c("-ffile-prefix-map=$srcdir=/usr/src/remotix"),
         "same binary sha256 in two builds, 29 Sep"],
        [".rpm", "rpm's defaults", "—", "Not settled yet: R23 for .rpm is still to do (fasi/17 T3)"],
        ["engine", "—", c("-trimpath") + ", vendored modules, local toolchain", "—"],
        [".run payload", "the commit time as mtime", "sorted names, owner 0, " + c("gzip -n"), "—"],
    ], "«TAB» — Reproducibility, recipe by recipe") + \
    p("SBOM and third-party licences (R24): every product package carries " + c("incorporate.json")
      + " with the linked ngtcp2/nghttp3 versions, and declares them (" + c("Static-Built-Using") + ", "
      + c("Provides: bundled(…)") + "). " + c("packaging/archivio/sbom.py") + " (SPDX per package, red if declared and linked "
      "differ) and " + c("packaging/archivio/licenze.py") + " (THIRD-PARTY-LICENSES with the text of every licence, "
      "including the Go modules of " + c("vendor/") + ") were written for the signed archive's publishing step, which "
      "no longer exists: nothing calls them. Not settled yet: putting the licences back into the " + c(".run")
      + " (an open point of §10.36).") + \
    warn("the package metadata still say the licence is proprietary (" + c("debian/copyright") + ": "
         "“License: proprietary”, with a note that the distribution licence is not decided yet; "
         + c("License: LicenseRef-Proprietary") + " in both specs; " + c("LicenseRef-REMOTIX")
         + " in both PKGBUILDs), while " + c("DECISIONI.md") + " §10.33 makes REMOTIX free of charge with a draft "
         "licence awaiting the user's approval. The package descriptions and summaries are still in Italian, against "
         "§10.32 (everything the administrator reads is English).", "Doc vs code.")

S_VERSIONS = p("One version per release, written in several dialects.", lead=True) + \
    table(["Artifact", "Release " + c("X.Y.Z-R"), "Without a release (development)"], [
        ["REMOTIX .deb", c("X.Y.Z-R+deb13") + ", " + c("X.Y.Z-R+ubuntu26.04"), c("0.17.0~gitYYYYMMDD.<hash>-1+deb13")
         + " (" + c(".modificato") + ", “modified”, added for a dirty tree)"],
        ["REMOTIX .rpm", "Version X.Y.Z, Release R%{?dist} (the macros " + c("rx_versione") + " and " + c("rx_rilascio")
         + ", version and release)", "0.17.0-1 (the spec's defaults; without " + c("RX_VERSIONE") + ", "
         + c("costruisci-rpm.sh") + " reads the version from there)"],
        ["REMOTIX Arch", c("pkgver=X.Y.Z") + ", " + c("pkgrel=R"), "the PKGBUILD's " + c("pkgver") + "/" + c("pkgrel")],
        ["engine", c("VersioneMotore") + " (engine version) = X.Y.Z via " + c("-ldflags -X"), c("0.1.0") + " ("
         + c("installatore/motore/formato.go") + ")"],
        ["engine packages", "X.Y.Z-R", "—"],
        ["the .run", c("remotix-X.Y.Z-R.run") + ", " + c("version") + " prints " + c("REMOTIX X.Y.Z-R"), "—"],
        ["object format", c("remotix-install/3") + " (independent of the release)", ""],
    ], "«TAB» — Version numbers") + \
    p("The catalogue has its own version and sequence (" + c(CAT_VER) + ") and the minimum engine that understands it; "
      "a new catalogue ships only with a new release.")

S_OPUS = p("The browser decodes Opus with a small WebAssembly module, embedded as base64 in " + c("src/pagina.html")
           + " between the " + c("OPUS_WASM_INIZIO") + " / " + c("OPUS_WASM_FINE") + " (start / end) markers. "
           + c("src/opus-wasm/costruisci.sh") + " (build) rebuilds it reproducibly.", lead=True) + \
    table(["Pinned input", "Value"], [
        ["libopus", "1.5.2, tarball checked against a fixed sha256"],
        ["toolchain", "the official emscripten image (4.0.15) pinned <b>by digest</b>, run with " + c("--network=none")],
        ["build", "decode only: no programs, tests, hardening, intrinsics, DRED or OSCE; " + c("-O3") + " without SIMD "
         "(old phone browsers); standalone wasm, no imports, 1 MiB memory, no growth"],
        ["output", c("src/opus-wasm/opus.wasm") + " and its " + c(".sha256") + ", then embedded into the page"],
    ], "«TAB» — The Opus decoder build") + \
    p(c("sh src/opus-wasm/costruisci.sh --verifica") + " (verify) checks that the page carries exactly " + c("opus.wasm")
      + ". The decoder's role in the page is described in " + rif("Audio and clipboard") + ".")

S_PITFALLS = p("Problems already met while building, and the cure now in the scripts — so nobody meets them twice.",
               lead=True) + \
    table(["Symptom", "Cause", "Cure (where)"], [
        ["the build loses " + c("-std=gnu11") + " and gcc 15 compiles as gnu23", "dpkg's CFLAGS in the environment "
         "replace the Makefile's " + c("CFLAGS ?=") + " line", "the recipes pass flags + " + c("-std=gnu11")
         + " + warnings (" + c("debian/rules") + ", spec, PKGBUILD)"],
        ["“No such file” on the gio header", c("make CFLAGS=…") + " on the command line cancels plain " + c("+=")
         + " lines", c("override CFLAGS +=") + " (Makefile); recipes export CFLAGS instead"],
        ["the wrong ngtcp2 is used", c("PKG_CONFIG_PATH") + " is searched before the prefix; " + c("/usr/local")
         + " answered", c("PKG_CONFIG_LIBDIR") + " inside " + c("PREFISSO") + " (Makefile)"],
        ["the binary uses a shared ngtcp2", "a " + c(".so") + " next to the " + c(".a"), c("quic-statiche.sh")
         + " fails if one is there; " + c("ldd") + " checks in every recipe"],
        ["rpmlint: position-independent-executable-suggested", "openSUSE's " + c("%{optflags}") + " lack PIE",
         c("-fPIE -pie") + " on openSUSE (spec)"],
        ["firewalld ignores REMOTIX's service", "a " + c("--") + " inside an XML comment", "XML validated before "
         "building (" + c("costruisci-rpm.sh") + ")"],
        ["the engine package differs from the engine in the .run", "rpm's brp-strip", c("__os_install_post") + " nil; "
         + c("!strip") + " on Arch"],
        ["makepkg “reference to $srcdir”", "ngtcp2/nghttp3 asserts carry " + c("__FILE__"), c("-ffile-prefix-map")],
        ["two Arch builds, two packages", c("builddate") + " and mtree dates", c("SOURCE_DATE_EPOCH")],
        [c("/var/lib/remotix") + " left after " + c("zypper remove"), "files created by the service unknown to rpm",
         c("%ghost") + " entries (spec)"],
        ["release 0.18.1-1 stopped on " + c("libyuv-dev"), "a dependency left in the recipes after phase 18",
         "removed from the three recipes (T10)"],
        ["“No space left” on the laptop", c("/tmp") + " nearly full, " + c("~/.cache") + " links there", "TMPDIR and "
         "caches under " + c("costruzione-uscita/") + " or " + c("installatore/.cache/")],
        ["files nobody can delete after a build", "container root mapped to an unknown uid", c("--userns=keep-id")
         + "; " + c("podman unshare rm -rf") + " for rpm work folders"],
    ], "«TAB» — Build pitfalls already met")

CHAPTER = ("Build and release", [
    ("The build roads", S_ROADS),
    ("Declared build dependencies", S_DEPS),
    ("The product Makefile", S_MAKEFILE),
    ("The twin-copy check", S_TWINS),
    ("The development container", S_DEVBOX),
    ("Per-distribution build images", S_TARGETS),
    ("Static ngtcp2 and nghttp3", S_QUIC),
    ("The Debian package", S_DEB),
    ("The RPM package", S_RPM),
    ("The Arch package", S_ARCH),
    ("What the packages install", S_INSTALLED),
    ("Building the installer engine", S_ENGINE),
    ("The release command", S_RELEASE),
    ("The .run file format", S_RUN),
    ("Reproducible builds, SBOM and licences", S_REPRO),
    ("Version numbers", S_VERSIONS),
    ("The Opus decoder build", S_OPUS),
    ("Build pitfalls already met", S_PITFALLS),
])
