"""Chapter 18 — Build and release. Sources: build/build-deb.sh, build/Containerfile, build/quic-static.sh, src/Makefile,
debian/rules, debian/control, src/opus-wasm/build.sh, src/rcp.c (BENCH_ON); the logs of the dev server (pacchetti/1.0.0,
pacchetti/<provisional>)."""
import re

from build import ROOT, arrow, box, c, code, fig, flow, h4, note, p, rif, sysf, table, term, text, tip, ul, warn, zone

MAKEFILE = (ROOT / "src" / "Makefile").read_text()


def _make_list(name):
    """A variable of the Makefile, continuation lines joined."""
    m = re.search(r"^" + name + r"\s*:?=\s*((?:.*\\\n)*.*)$", MAKEFILE, re.M)
    return m.group(1).replace("\\\n", " ").split() if m else []


SOURCES = _make_list("SORGENTI")
PROTOCOLS = _make_list("PROTOCOLLI")
MINIMA = [x.split(":") for x in _make_list("MINIMI")]

# ── Figure ───────────────────────────────────────────────────────────────────
BUILD = fig(
    zone(20, 14, 860, 100, "Image (podman build, needs network)")
    + box(36, 46, 240, 50, "build/Containerfile", "debian:trixie + build-deps", "dark", 12)
    + box(330, 46, 240, 50, "build/quic-static.sh", "ngtcp2, nghttp3: static .a only", "dark", 11.5)
    + box(624, 46, 240, 50, "remotix-debian-build", "localhost image", "navy", 12)
    + arrow(277, 71, 328, 71) + arrow(571, 71, 622, 71)
    + zone(20, 128, 860, 100, "Package (podman run, --userns=keep-id, copy of the tree)")
    + box(36, 160, 190, 50, "copy src/ debian/", "changelog + copyright written", "blue", 11.5)
    + box(246, 160, 190, 50, "dpkg-buildpackage", "-b -us -uc, debian/rules", "blue", 11.5)
    + box(456, 160, 190, 50, "lintian", "-I --pedantic", "blue", 12)
    + box(666, 160, 198, 50, "checks R4 R13 R14 (R23)", "on the finished .deb", "green", 11.5)
    + arrow(227, 185, 244, 185) + arrow(437, 185, 454, 185) + arrow(647, 185, 664, 185),
    900, 244, "«FIG» — The build of the .deb: image once, then copy, build, lint and check")

# ── 18.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX is never built on the host. " + c("build/build-deb.sh") + " builds a " + c("debian:trixie") + " image with podman, copies "
       "the tree into a work folder, runs " + c("dpkg-buildpackage") + " in that image and then examines the finished package. The "
       "script needs podman and network access (the image build clones ngtcp2 and nghttp3 from GitHub); it does not need git, Go, "
       "a bench folder or the old repository.", lead=True) + BUILD + \
    table(["Item", "Where", "Role"], [
        [c("build/Containerfile"), "build/", "Debian 13 image: " + c("build-essential") + ", " + c("pkg-config") + ", " + c("cmake") + ", "
         + c("ninja-build") + ", " + c("git") + ", the " + c("-dev") + " packages (OpenSSL, PAM, GLib, PipeWire, libdrm, libva, Opus, zlib, "
         "libei, xkbcommon, gbm, Wayland, Vulkan loader), then the static QUIC libraries, then in a LAST layer the packaging tools "
         "(" + c("debhelper") + ", " + c("dh-apparmor") + ", " + c("dpkg-dev") + ", " + c("fakeroot") + ", " + c("lintian") + ", "
         + c("binutils") + ") so that the layers above stay cached"],
        [c("build/quic-static.sh"), "build/", "nghttp3 " + c("v1.18.0") + " and ngtcp2 " + c("v1.25.0") + " from source, static only, in "
         + c("/usr/local/lib") + " (overridable by " + c("NGHTTP3_VER") + " and " + c("NGTCP2_VER") + ")"],
        [c("build/build-deb.sh"), "build/", "the driver: image, copy, build, lintian, checks, output files"],
        [c("src/Makefile"), "src/", "compiles and links the two programs (the server and " + c("remotix-local-login") + "); called by " + c("debian/rules")],
        [c("debian/rules"), "debian/", "the debhelper recipe: build flags, the guards, what goes where in the package"],
        [c("debian/control"), "debian/", "Build-Depends, Depends, Recommends, " + c("Static-Built-Using")],
    ], "«TAB» — The pieces of the build") + \
    note("What the package contains and how its maintainer scripts behave is in " + rif("The package") + ". This chapter is about "
         "how the bytes are made and what is checked on them.")

# ── 18.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Debian 13 carries ngtcp2 1.11 and nghttp3 1.8 (the comment in " + c("src/Makefile") + "), but the product needs ngtcp2 "
       "at least 1.25 with the " + c("ngtcp2_crypto_ossl") + " bridge (the " + c("NGTCP2_STREAM_CLOSE2_FLAG_*") + " flags used by "
       + c("transport.c") + ") and OpenSSL at least 3.5 for the native QUIC API. So the image builds the two libraries from source, "
       "pinned at one version, and installs only the static archives.", lead=True) + \
    ul([
        "<b>Static only.</b> " + c("quic-static.sh") + " configures with " + c("-DENABLE_SHARED_LIB=OFF") + " and "
        + c("-DENABLE_STATIC_LIB=ON") + ", library directory fixed to " + c("lib") + " (not lib64 or a multiarch directory) so that the "
        "Containerfile's " + c("LIBRARY_PATH=/usr/local/lib") + " works and the Makefile needs no path. At the end the script fails if "
        "any " + c("libngtcp2*.so*") + " or " + c("libnghttp3*.so*") + " exists in " + c("/usr/local/lib") + ": a shared object there "
        "would be picked up by the linker.",
        "<b>The result.</b> The package has no run-time dependency on ngtcp2 or nghttp3; its control file says so with "
        + c("Static-Built-Using: ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0)") + ".",
        "<b>The versions are written in four places</b> and a change must touch all of them: the defaults of " + c("quic-static.sh")
        + ", the two " + c("test") + " lines of " + c("debian/rules") + " (R24, below), " + c("Static-Built-Using") + " in "
        + c("debian/control") + ", and " + c("MINIMI") + " in " + c("src/Makefile") + ".",
        "<b>Not pinned by hash.</b> The script clones the two tags with " + c("git clone --depth 1 -b <tag>") + ". The tag is the pin; no "
        "commit id or archive checksum is checked. The image is built once and cached, so rebuilding it later could in principle fetch a "
        "moved tag.",
    ]) + \
    warn("The image build needs network access to GitHub and to the Debian mirrors. A machine with no network cannot build the image; "
         "once the image exists, a package build does not need the network.")

# ── 18.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The script is a sequence of steps; every output goes to " + c("$OUTPUT") + " (default " + sysf("/media/REMOTIX-DEBIAN/pacchetti")
       + ", on the dev server's persistent disk).", lead=True) + \
    table(["Variable", "Default", "Meaning"], [
        [c("OUTPUT"), sysf("/media/REMOTIX-DEBIAN/pacchetti"), "where the results go"],
        [c("WORK"), c("$OUTPUT/.work"), "scratch space with the copies of the tree; " + c("TMPDIR") + " is set under it, never "
         + c("/tmp") + " (RAM-only machines)"],
        [c("RX_VERSION"), c("1.0.0~dev"), "the upstream version (see the section on versions)"],
        [c("RX_REVISION"), c("1"), "the Debian revision"],
        [c("SOURCE_DATE_EPOCH"), "newest mtime in " + c("src/") + ", " + c("debian/") + ", " + c("LICENSE.md") + " and "
         + c("THIRD-PARTY-LICENSES"), "the build date, for a reproducible package"],
        [c("TWICE"), "unset", "1: build a second time and compare the two .deb byte for byte (R23)"],
    ], "«TAB» — Environment of build-deb.sh") + \
    p("In order:") + \
    ul([
        "<b>Image.</b> " + c("podman build -t localhost/remotix-debian-build") + "; log in " + sysf("immagine.log") + ". A failure stops the script.",
        "<b>Copy.</b> " + c("prepare_copy") + " makes a clean copy of " + c("src/") + ", " + c("debian/") + " and " + c("THIRD-PARTY-LICENSES")
        + " under " + c("$WORK/a/remotix") + ". It appends " + c("LICENSE.md") + " to " + c("debian/copyright") + " as continuation lines of "
        + c("License: LicenseRef-REMOTIX") + " (an empty line becomes \" .\"), deletes leftovers of a local build "
        "(the binary, " + c("*.o") + ", the generated protocol sources) and writes " + c("debian/changelog") + " with one entry, \"Debian 13 build\", "
        "dated from " + c("SOURCE_DATE_EPOCH") + ". The working tree is never touched.",
        "<b>Build.</b> " + c("podman run --rm --userns=keep-id") + " with the copy mounted at " + c("/lavoro") + " runs "
        + c("dpkg-buildpackage -b -us -uc") + " (binary only, unsigned). Log in " + sysf("costruzione.log") + ". The .deb and the "
        + c(".buildinfo") + " are copied to " + c("$OUTPUT") + ".",
        "<b>Lintian.</b> " + c("lintian -I --pedantic --no-tag-display-limit") + " on the .deb, into " + sysf("lintian.txt")
        + ". The script prints the count of E and W lines but does NOT fail on them: its exit status depends only on the checks below.",
        "<b>Checks R13, R14, R4</b> on the finished package, one line each ending SI or NO, into " + sysf("controlli.txt")
        + ", followed by the control fields " + c("Depends") + ", " + c("Recommends") + ", " + c("Static-Built-Using") + " and the list of conffiles.",
        "<b>Second build (R23)</b> only with " + c("TWICE=1") + ".",
        "<b>Exit.</b> 0, unless some line of " + sysf("controlli.txt") + " contains \" NO\" (exit 1); also 1 if the image build or " + c("dpkg-buildpackage") + " fails or no .deb comes out; 2 if podman is missing or the output folder cannot be made.",
    ]) + \
    p("Output files in " + c("$OUTPUT") + ": the .deb, the " + c(".buildinfo") + ", " + sysf("costruzione.log") + ", " + sysf("immagine.log") + ", "
      + sysf("lintian.txt") + ", " + sysf("controlli.txt") + ", " + sysf("elenco.txt") + " (the file list of the package; from " + c("dpkg-deb -c")
      + "). The server folder holds one sub-folder per package built, for example " + sysf("pacchetti/1.0.0") + ".")

# ── 18.4 ─────────────────────────────────────────────────────────────────────
S4 = p("One Makefile, no configure step. It builds " + c(str(len(SOURCES))) + " C files (the variable " + c("SORGENTI") + ") into the server "
       "binary " + c("remotix") + ", plus " + c(str(len(PROTOCOLS))) + " Wayland protocol files generated at build time. The target "
       + c("all") + " also builds a second, separate program, " + c("remotix-local-login") + ", from " + c("local_login.c")
       + " alone: libc only, the same flags, no library (the rule " + c("$(LOCAL_LOGIN)") + "). It is the PAM hook of the local-login hold ("
       + rif("The local-login hold") + ").", lead=True) + \
    table(["Topic", "What the Makefile does"], [
        ["compiler flags", c("CFLAGS ?= -O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter") + " as a default, then "
         + c("override CFLAGS += -D_GNU_SOURCE") + " and the " + c("pkg-config") + " flags of every library. gnu11 and not c11 because "
         + c("accept4") + ", " + c("SOCK_NONBLOCK") + " and the ancillary messages are needed. " + c("debian/rules") + " passes its own "
         "flags because the default line does not apply when " + c("CFLAGS") + " is already set"],
        ["libraries", c("-lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm") + " and the pkg-config libraries of GLib/GIO, "
         "PipeWire, libva and libva-drm, libei and xkbcommon, wayland-client, gbm, opus, vulkan and zlib. libdrm is in the compile "
         "flags only (the " + c("DRM_FORMAT_MOD_*") + " macros): nothing is linked for it"],
        ["Wayland protocols", "the XML files of " + c("src/protocols/") + " become " + c("<name>-client-protocol.h") + " and "
         + c("<name>-protocol.c") + " through " + c("wayland-scanner") + "; " + c("clean") + " removes them. Names: "
         + ", ".join(c(x) for x in PROTOCOLS)],
        ["rebuild on flag change", c(".flags") + " is rewritten, only when it differs, at every run and every object depends on it: "
         "a change of flags recompiles everything"],
        ["bench build", c("BENCH ?= 0") + "; " + c("make BENCH=1") + " adds " + c("-DREMOTIX_BENCH") + ", which compiles in the bench function "
         "of RCP §7.5 (the " + c("BENCH_MARK") + " and " + c("BENCH_OUTCOME") + " messages). The package never sets it (R13)"],
        ["DEPS_PREFIX", "if set, adds " + c("-I") + ", " + c("-L") + " and an " + c("-rpath") + " for a private prefix holding ngtcp2 and nghttp3; "
         "not used by the package build, where the libraries are in " + c("/usr/local") + " of the image"],
    ], "«TAB» — What src/Makefile does") + \
    h4("The declared minimum versions") + \
    table(["pkg-config module", "Minimum"], [[c(a), (c(b) if b != "0" else "any")] for a, b in MINIMA], "«TAB» — MINIMI in src/Makefile, checked by make deps") + \
    p(c("make deps") + " checks every module against its minimum, then tries to compile and link an empty program that includes each "
      "header the product needs (" + c("ngtcp2/ngtcp2.h") + ", " + c("ngtcp2/ngtcp2_crypto_ossl.h") + ", " + c("nghttp3/nghttp3.h") + ", OpenSSL, PAM, GIO, "
      "PipeWire, " + c("drm_fourcc.h") + ", libva, gbm, opus, vulkan, zlib). It prints OK, NO or ?? per item and exits non-zero on any "
      "failure; " + c("debian/rules") + " runs it first, so a missing or old library stops the build with a line that names it.") + \
    h4("The twin comparison and TWIN=none") + \
    p(c("rcp.c") + ", " + c("rcp.h") + ", " + c("authentication.c") + " and " + c("msgrate.h") + " (variable " + c("GEMELLATI") + ") were designed to exist "
      "in two copies, the product's and a bench's, and the target " + c("fingerprints") + ", part of " + c("all") + ", compares them with "
      + c("cmp") + " before compiling. The default " + c("TWIN ?= ../benches/rcp") + " points to a folder that this repository does not "
      "have. With a missing twin folder the target stops the build (exit 2) unless the caller declares " + c("TWIN=none") + ", in which case "
      "it prints that nothing was compared. " + c("debian/rules") + " passes " + c("TWIN=none") + " everywhere, so the package build never "
      "compares anything.") + \
    warn("A plain " + c("make") + " in " + c("src/") + " fails at " + c("fingerprints") + " unless " + c("TWIN=none") + " is given. This is the "
         "result of reading the Makefile; it was not run for this manual.")

# ── 18.5 ─────────────────────────────────────────────────────────────────────
S5 = p(c("debian/rules") + " is a debhelper (compat 13) recipe with a few deliberate overrides. Each one has a reason written in the file.",
       lead=True) + \
    table(["Rule", "What it does and why"], [
        [c("DEB_BUILD_MAINT_OPTIONS = hardening=+all"), "all dpkg hardening flags; with " + c("buildflags.mk") + " the flags include "
         + c("-ffile-prefix-map") + ", which the reproducible build (R23) relies on"],
        [c("R_CFLAGS"), "dpkg's " + c("CFLAGS") + " and " + c("CPPFLAGS") + " plus " + c("-std=gnu11 -Wall -Wextra -Wno-unused-parameter") + ". Without it "
         "the Makefile's default line would be skipped and gcc 15 would default to gnu23"],
        [c("override_dh_auto_configure"), c("make -C src deps TWIN=none") + ": nothing to configure, only the check of minimum versions"],
        [c("override_dh_auto_build"), "three guards, then " + c("make -C src all TWIN=none CFLAGS=\"$(R_CFLAGS)\" LDFLAGS=\"$(LDFLAGS)\"") + ": "
         "(R24) " + c("pkg-config --modversion") + " of ngtcp2 and nghttp3 must equal exactly 1.25.0 and 1.18.0; (R13) " + c("src/rcp.c")
         + " must contain the exact line " + c("#define BENCH_ON 0") + ", else the build stops"],
        [c("override_dh_auto_test"), "empty: the package build runs no tests (testing is in " + rif("Testing") + ")"],
        [c("override_dh_auto_install"), "installs the binary to " + c("/usr/libexec/remotix/remotix") + " and the hook " + c("remotix-local-login") + " beside it (0755), the page, defaults, licence file, "
         "the PAM file and denied-users (conffiles), the pam-auth-update profile " + c("debian/remotix.pam-config") + " as " + c("/usr/share/pam-configs/remotix") + ", the ufw profile, the KWin permission file, the polkit rules and helper, and the two "
         "switched-off \"belts\" under " + c("/usr/share/remotix/belts/") + "; it writes " + c("/usr/share/remotix/linked.json") + " with the "
         "pkg-config versions of the linked static libraries"],
        [c("execute_after_dh_auto_install"), "installs the sysusers file and the AppArmor profile (a conffile in " + c("/etc/apparmor.d")
         + ") and runs " + c("dh_apparmor") + " so that the maintainer scripts load and reload it"],
        [c("override_dh_installsystemd"), c("--no-enable --no-start --restart-after-upgrade") + ": the package neither enables nor starts "
         "the service; on upgrade it restarts it only if it was active or enabled (the restart closes the remote desktops, see "
         + rif("Stopping the service") + ")"],
    ], "«TAB» — The overrides of debian/rules") + \
    p("The destination paths and the role of each shipped file are described in " + rif("The package") + ".")

# ── 18.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The labels R4, R13, R14, R23 and R24 are requirement names carried over from the project's earlier packaging work. In this "
       "repository they are defined only by the two scripts that implement them, " + c("build/build-deb.sh") + " and " + c("debian/rules")
       + ". (R followed by a number is also used for unrelated audit findings elsewhere, for example in the comments of "
       + c("hsrate.h") + " and " + c("tls.c") + ".)", lead=True) + \
    table(["Label", "Where", "What it checks", "How"], [
        ["R13", c("debian/rules") + ", " + c("build-deb.sh"), "the installed binary has no bench function, and the unit starts none",
         "<b>At build:</b> " + c("src/rcp.c") + " must hold the line " + c("#define BENCH_ON 0") + ". <b>On the .deb:</b> the binary extracted "
         "from the package must NOT contain the string \"the BENCH FUNCTION is ON\"; an " + c("rcp.o") + " built from a copy of the tree with "
         + c("BENCH_ON") + " set to 1 and " + c("make BENCH=1") + " MUST contain it (the positive control, so that \"not found\" cannot mean "
         "\"cannot search\"). <b>Unit:</b> the " + c("ExecStart") + " of " + c("remotix.service") + " passes none of " + c("--survey") + ", "
         + c("--command-socket") + ", " + c("--audio-test") + ", " + c("--verbose")],
        ["R14", c("build-deb.sh"), "no bench or test file in the package",
         "the file list of the .deb is matched against " + c("/test") + ", " + c("sudoers") + ", " + c("gpu-udev") + ", " + c("restart-") + ", "
         + c("ld.so.conf") + ", " + c("provision") + ", " + c("benches") + ", " + c("/opt/") + ", " + c(".pem") + " and " + c(".key")
         + "; any match is NO"],
        ["R4", c("build-deb.sh"), "the binary's run-time linking is clean",
         c("ldd") + " of the extracted binary: no \"not found\", and no dynamic ngtcp2 or nghttp3. The line records the number of libraries (32 in "
         "the recorded runs)"],
        ["R23", c("build-deb.sh") + " (TWICE=1)", "reproducibility",
         "a second clean copy is built the same way and the two .deb files are compared with " + c("cmp") + "; a difference is NO and the second "
         "file is kept as " + c("seconda-<name>")],
        ["R24", c("debian/rules"), "the linked static libraries are the declared versions",
         "the two " + c("test") + " lines compare " + c("pkg-config --modversion") + " with " + c("Static-Built-Using") + "; the versions are also "
         "written to " + c("linked.json") + " (an SBOM tool can read them)"],
    ], "«TAB» — The package requirements and where each is enforced") + \
    h4("What was recorded") + \
    ul([
        "For the packages with the provisional number and with 1.0.0 the recorded " + sysf("controlli.txt") + " has R13 (package: 0 occurrences, positive control: 1), R14 and R4 "
        "(32 libraries, none missing) all SI, and the two options-in-unit line SI. Lintian shows 0 E and 0 W for both; the 1.0.0 file adds one "
        "information line (" + c("systemd-service-file-missing-documentation-key") + ").",
        "<b>R23 has no recorded run.</b> None of the " + sysf("controlli.txt") + " files found on the dev server contains an R23 line, so no run with "
        + c("TWICE=1") + " is on record. The statement \"the package is reproducible\" is therefore not made by this manual.",
    ]) + \
    warn("R23 compares two builds made from the same tree in the same run, with the same " + c("SOURCE_DATE_EPOCH") + ". Left to its default, "
         + c("SOURCE_DATE_EPOCH") + " is the newest modification time of files in " + c("src/") + ", " + c("debian/") + " and the two licence files, "
         "and a fresh checkout gives files new modification times. Two builds from two checkouts therefore differ unless the caller fixes "
         + c("SOURCE_DATE_EPOCH") + " (for example to the commit time).", "Limit of the reproducibility check.")

# ── 18.7 ─────────────────────────────────────────────────────────────────────
S7 = p("The version of the product exists only as package metadata. I found no version constant in " + c("src/") + " (no source file or "
       "header carries the number), and the page and the protocol have their own versions that are not the package's.", lead=True) + \
    table(["Where", "What"], [
        [c("RX_VERSION") + " in " + c("build/build-deb.sh"), "the upstream version; the default is " + c("1.0.0~dev") + ". The tilde makes a development build sort "
         "BEFORE 1.0.0 in dpkg's ordering"],
        [c("RX_REVISION"), "the Debian revision, default 1"],
        ["the full version", c("<RX_VERSION>-<RX_REVISION>+deb13") + ", for example " + c("1.0.0-1+deb13") + "; the file is "
         + c("remotix_1.0.0-1+deb13_amd64.deb")],
        [c("debian/changelog"), "not in git: written by " + c("prepare_copy") + " with that version, the distribution " + c("trixie") + ", urgency medium, "
         "one line \"Debian 13 build\" and a maintainer line written in the script (the same name and address as in " + c("debian/control") + ")"],
        ["the manual's cover", c("manuals/sources/build.py") + " reads the default of " + c("RX_VERSION") + " and drops " + c("~dev") + ": the manual says 1.0.0"],
    ], "«TAB» — Where the version lives") + \
    term("""$ RX_VERSION=1.0.0 RX_REVISION=1 OUTPUT=/media/REMOTIX-DEBIAN/pacchetti/1.0.0 build/build-deb.sh
$ TWICE=1 RX_VERSION=1.0.0 build/build-deb.sh          # also R23""", "Building the release package") + \
    p("Without " + c("RX_VERSION") + " a build is a development build, " + c("remotix_1.0.0~dev-1+deb13_amd64.deb") + ".") + \
    h4("What \"release\" means in this tree") + \
    p("The tree has no release script, no signing step, no repository and no publication tool: the old packaging and site folders were "
      "not carried over (" + c("docs/INVENTARIO-non-debian.md") + "). A release is the output of " + c("build-deb.sh") + " with " + c("RX_VERSION=1.0.0")
      + ": the .deb, the " + c(".buildinfo") + " and the check files. The package is built unsigned (" + c("-us -uc") + "). PIANO.md leaves "
      "publication, the site and public repositories to the owner's decision, so none of them is described as existing.")

# ── 18.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Three files in the product are generated by tools that are not part of the package build. Their results are committed.",
       lead=True) + \
    table(["File", "Made by", "State"], [
        [c("src/opus-wasm/opus.wasm") + ", embedded as base64 in " + c("src/page.html") + " between the two " + c("OPUS_WASM") + " markers",
         c("src/opus-wasm/build.sh"), "libopus 1.5.2 (source URL and SHA-256 pinned) compiled with emscripten 4.0.15 from an image pinned by digest, in "
         "podman with " + c("--network=none") + " for the compile; embeds into the page. " + c("sh src/opus-wasm/build.sh --verify") + " checks that the "
         "page carries exactly " + c("opus.wasm") + " and that the module exports every " + c("rx_*") + " function the page calls. The SHA-256 of "
         "the committed module is in " + c("opus.wasm.sha256") + ". The verification was not run for this manual"],
        [c("src/vulkanvideo_rgb_nv12_spv.h"), "a script named in its first line, " + sysf("benches/19-vulkan/19-shader.sh"), "the SPIR-V of "
         + c("vulkanvideo_rgb_nv12.comp") + " as a C array. The script is not in this repository, so the shader cannot be rebuilt from the tree as "
         "it stands"],
        [c("src/protocols/*.xml"), "copied from their upstreams", "turned into C by " + c("wayland-scanner") + " at every build"],
    ], "«TAB» — Generated or vendored inputs") + \
    tip("A change to " + c("vulkanvideo_rgb_nv12.comp") + " needs a tool chain (glslang or similar) that no script in the tree provides. "
        "See " + rif("Extending REMOTIX and porting to another distribution") + " for how to add a codec.")

CHAPTER = ("Build and release", [
    ("The build of the .deb in one container", S1),
    ("The build image and the static QUIC libraries", S2),
    ("What build-deb.sh does, step by step", S3),
    ("src/Makefile: sources, libraries, minimum versions", S4),
    ("debian/rules: the overrides and the guards", S5),
    ("The package checks R4, R13, R14, R23 and R24", S6),
    ("Version and release", S7),
    ("Generated and vendored inputs", S8),
])
