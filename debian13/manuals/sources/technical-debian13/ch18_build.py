"""Chapter 18 — Build and release. Sources: build/build-deb-vm.sh, build/build-deb.sh and build/Containerfile (the older container
way, still in the tree), build/quic-static.sh, src/Makefile, debian/rules, debian/control, debian/remotix.install,
src/opus-wasm/build.sh, src/rcp.c (BENCH_ON), server/vm-radeon.sh, server/VM-BANCO.md; the logs of the dev server (pacchetti/1.0.0,
pacchetti/<provisional>) for the 1.0.x packages."""
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
    zone(20, 14, 860, 100, "Build VM «costruzione» (prepared once: snapshot pronta)")
    + box(36, 46, 240, 50, "apt build dependencies", "the -dev packages + packaging tools", "dark", 11.5)
    + box(330, 46, 240, 50, "build/quic-static.sh", "ngtcp2, nghttp3: static .a only", "dark", 11.5)
    + box(624, 46, 240, 50, "/usr/local/lib", "the two libraries, versions checked", "navy", 11.5)
    + arrow(277, 71, 328, 71) + arrow(571, 71, 622, 71)
    + zone(20, 128, 860, 100, "Package (build/build-deb-vm.sh, one label per package)")
    + box(36, 160, 190, 50, "copy src/ debian/", "changelog + copyright written", "blue", 11.5)
    + box(246, 160, 190, 50, "dpkg-buildpackage", "-b -us -uc, debian/rules", "blue", 11.5)
    + box(456, 160, 190, 50, "lintian + checks", "R13 R14 R4 (R23) on the .deb", "green", 11.5)
    + box(666, 160, 198, 50, "back to the server", "pacchetti/<label>/", "navy", 11.5)
    + arrow(227, 185, 244, 185) + arrow(437, 185, 454, 185) + arrow(647, 185, 664, 185),
    900, 244, "«FIG» — The build of the .deb: the VM prepared once, then copy, build, lint and check, bring back")

# ── 18.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX is not built on the machine where it is edited, and the 1.2.0 build uses no container. " + c("build/build-deb-vm.sh") + " [label] (225 lines) copies the tree to the virtual machine "
       + c("costruzione") + ", builds the package there with " + c("dpkg-buildpackage") + ", examines the finished package and brings the .deb and the logs back to "
       + sysf("/media/REMOTIX-DEBIAN/pacchetti/<label>/") + " on the dev server. The machine that runs the script needs only ssh access to the dev server (its address is the variable "
       + c("RX_SERVER") + "): it does not compile, and needs no git, Go, bench folder or old repository. If the build machine is off, the script turns it on (virtual only, never the Radeon) and "
       "turns it off again at the end; " + c("KEEP_VM=1") + " leaves it on (" + rif("The VM bench") + "). The build needs network access: the static libraries are cloned from GitHub and apt reads the "
       "Debian mirrors.", lead=True) + BUILD + \
    table(["Item", "Where", "Role"], [
        [c("build/build-deb-vm.sh"), "build/", "the driver: copy, dependencies, static libraries, build, lintian, checks, output files. Variables " + c("RX_SERVER") + " (the ssh address of the dev server), "
         + c("RX_GUEST_PORT") + " (default 2365, the build machine's ssh port on the server) and " + c("RX_VMSCRIPT") + " (the VM manager on the server)"],
        [c("build/quic-static.sh"), "build/", "nghttp3 " + c("v1.18.0") + " and ngtcp2 " + c("v1.25.0") + " from source, static only, in "
         + c("/usr/local/lib") + " (overridable by " + c("NGHTTP3_VER") + " and " + c("NGTCP2_VER") + ")"],
        [c("src/Makefile"), "src/", "compiles and links the two programs (the server and " + c("remotix-local-login") + "); called by " + c("debian/rules")],
        [c("debian/rules"), "debian/", "the debhelper recipe: build flags, the guards, what goes where in the package"],
        [c("debian/control"), "debian/", "Build-Depends, Depends, Recommends, " + c("Static-Built-Using")],
        [c("build/build-deb.sh") + ", " + c("build/Containerfile"), "build/", "the older way, still in the tree: a " + c("debian:trixie") + " image built with podman and a package build in it. Not used by the 1.2.0 work; the checks of its second half are the same (" + rif("The package checks R4, R13, R14, R23 and R24") + ")"],
    ], "«TAB» — The pieces of the build") + \
    note("What the package contains and how its maintainer scripts behave is in " + rif("The package") + ". This chapter is about "
         "how the bytes are made and what is checked on them.")

# ── 18.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Debian 13 carries ngtcp2 1.11 and nghttp3 1.8 (the comment in " + c("src/Makefile") + "), but the product needs ngtcp2 "
       "at least 1.25 with the " + c("ngtcp2_crypto_ossl") + " bridge (the " + c("NGTCP2_STREAM_CLOSE2_FLAG_*") + " flags used by "
       + c("transport.c") + ") and OpenSSL at least 3.5 for the native QUIC API. So the build machine builds the two libraries from source, "
       "pinned at one version, and installs only the static archives.", lead=True) + \
    ul([
        "<b>Built once.</b> There is no image to build: the libraries are built on the build machine the first time, and the script skips the step if " + c("pkg-config") + " already reports ngtcp2 1.25.0 and nghttp3 1.18.0 and "
        + c("libngtcp2_crypto_ossl.a") + " is in " + c("/usr/local/lib") + ". The snapshot " + c("pronta") + " of the machine has them.",
        "<b>Static only.</b> " + c("quic-static.sh") + " configures with " + c("-DENABLE_SHARED_LIB=OFF") + " and "
        + c("-DENABLE_STATIC_LIB=ON") + ", library directory fixed to " + c("lib") + " (not lib64 or a multiarch directory) so that "
        "the " + c("LIBRARY_PATH=/usr/local/lib") + " that the build sets works and the Makefile needs no path. At the end the script fails if "
        "any " + c("libngtcp2*.so*") + " or " + c("libnghttp3*.so*") + " exists in " + c("/usr/local/lib") + ": a shared object there "
        "would be picked up by the linker.",
        "<b>The result.</b> The package has no run-time dependency on ngtcp2 or nghttp3; its control file says so with "
        + c("Static-Built-Using: ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0)") + ".",
        "<b>The versions are written in four places</b> and a change must touch all of them: the defaults of " + c("quic-static.sh")
        + ", the two " + c("test") + " lines of " + c("debian/rules") + " (R24, below), " + c("Static-Built-Using") + " in "
        + c("debian/control") + ", and " + c("MINIMI") + " in " + c("src/Makefile") + ", and the test of what is already installed in " + c("build-deb-vm.sh") + " (it compares the two versions with 1.25.0 and 1.18.0).",
        "<b>Not pinned by hash.</b> The script clones the two tags with " + c("git clone --depth 1 -b <tag>") + ". The tag is the pin; no "
        "commit id or archive checksum is checked.",
    ]) + \
    warn("The build needs network access to GitHub (the first time the libraries are built) and to the Debian mirrors (only if a build dependency is missing: the script tries "
         "the installation first and runs " + c("apt-get update") + " only if it fails). A machine with no network cannot prepare the build VM.")

# ── 18.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The script is a sequence of steps. The label names the output folder " + sysf("/media/REMOTIX-DEBIAN/pacchetti/<label>") + " (default: the date and time); it may contain only letters, digits, dot, underscore and dash, and not be "
       + c(".") + " or " + c("..") + ". <b>If the folder exists already, the script stops (exit 2): a previous package is never overwritten.</b>", lead=True) + \
    table(["Variable", "Default", "Meaning"], [
        [c("OUTPUT"), sysf("/media/REMOTIX-DEBIAN/pacchetti/<label>"), "where the results go on the dev server"],
        [c("RX_VERSION"), c("1.2.0~dev"), "the upstream version (see the section on versions)"],
        [c("RX_REVISION"), c("1"), "the Debian revision"],
        [c("SOURCE_DATE_EPOCH"), "newest mtime in " + c("src/") + ", " + c("debian/") + ", " + c("LICENSE.md") + " and "
         + c("THIRD-PARTY-LICENSES"), "the build date, for a reproducible package"],
        [c("TWICE"), "unset", "1: build a second time and compare the two .deb byte for byte (R23)"],
        [c("KEEP_VM"), "unset", "1: do not turn the build machine off at the end"],
    ], "«TAB» — Environment of build-deb-vm.sh") + \
    p("In order:") + \
    ul([
        "<b>Copy.</b> A clean copy of " + c("src/") + ", " + c("debian/") + " and " + c("THIRD-PARTY-LICENSES") + " is made in a temporary folder of the machine that runs the script. "
        "The text of " + c("LICENSE.md") + " is appended to " + c("debian/copyright") + " as continuation lines of "
        + c("License: LicenseRef-REMOTIX") + " (an empty line becomes \" .\"), the leftovers of a local build "
        "(the binary, " + c("*.o") + ", the generated protocol sources) are deleted and " + c("debian/changelog") + " is written with one entry, \"Debian 13 build\", "
        "dated from " + c("SOURCE_DATE_EPOCH") + ". The working tree is never touched.",
        "<b>The machine.</b> If it does not answer, the script starts it " + c("virtuale") + " and waits; it checks that it is the build virtual machine and copies the work folder in (" + sysf("~/debwork/<label>") + " in the guest).",
        "<b>Dependencies.</b> In the guest, " + c("apt-get install --no-install-recommends") + " of " + c("build-essential") + ", " + c("pkg-config") + ", " + c("git") + ", " + c("cmake") + ", " + c("ninja-build") + ", the " + c("-dev") + " packages of OpenSSL, PAM, GLib, PipeWire, libdrm, libva, Opus, zlib, "
        "libei, xkbcommon, gbm, Wayland and the Vulkan loader, and the packaging tools " + c("debhelper") + ", " + c("dh-apparmor") + ", " + c("dpkg-dev") + ", " + c("fakeroot") + ", " + c("lintian") + " and " + c("binutils") + ". Log " + sysf("apt.log") + ".",
        "<b>Static libraries.</b> " + c("quic-static.sh") + ", unless the right versions are already there (" + rif("The build machine and the static QUIC libraries") + "). Log " + sysf("quic.log") + ".",
        "<b>Build.</b> " + c("dpkg-buildpackage -b -us -uc") + " (binary only, unsigned) in a copy of the tree. Log " + sysf("costruzione.log") + ". The .deb and the " + c(".buildinfo") + " come out, with a " + c(".sha256") + " of the .deb and the file list (" + sysf("elenco.txt") + ", from " + c("dpkg-deb -c") + ").",
        "<b>Lintian.</b> " + c("lintian -I --pedantic --no-tag-display-limit") + " on the .deb, into " + sysf("lintian.txt")
        + ". Warnings are only shown; <b>a lintian error fails the script</b> (the line " + c("lintian: E=0") + " must be in " + sysf("controlli.txt") + ").",
        "<b>Checks R13, R14, R4</b> on the finished package, one line each ending SI or NO, into " + sysf("controlli.txt")
        + ", followed by the control fields " + c("Depends") + ", " + c("Recommends") + ", " + c("Static-Built-Using") + " and the list of conffiles. The host script requires the four lines "
        "(" + c("R13 banco-nel-binario") + ", " + c("R13 opzioni-di-banco-nell-unita") + ", " + c("R14 file-del-banco") + ", " + c("R4 ldd") + ") to be there and to say SI: a line missing, or any line with NO, fails.",
        "<b>Second build (R23)</b> only with " + c("TWICE=1") + ": a second clean copy is built and the two .deb are compared with " + c("cmp") + ".",
        "<b>Back.</b> The .deb, the " + c(".sha256") + ", the " + c(".buildinfo") + ", the logs and the " + c(".txt") + " files are brought to " + c("$OUTPUT") + " together with " + sysf("costruzione-vm.log") + " (the screen output of the build). "
        "On a failure nothing of the package is brought back: the logs go to " + sysf("<OUTPUT>-fallita-<time>/") + " on the server, and the guest's work folder stays for inspection.",
        "<b>Exit.</b> 0 when the package is back; 1 when a step or a check failed; 2 for a wrong call, a label that already exists, or a build machine that does not answer.",
    ]) + \
    p("Output files in " + c("$OUTPUT") + ": the .deb, the " + c(".buildinfo") + ", the " + c(".sha256") + ", " + sysf("costruzione.log") + ", " + sysf("apt.log") + ", " + sysf("quic.log") + ", "
      + sysf("lintian.txt") + ", " + sysf("controlli.txt") + ", " + sysf("elenco.txt") + " and " + sysf("costruzione-vm.log") + ". The server folder holds one sub-folder per package built.") + \
    h4("The older script") + \
    p(c("build/build-deb.sh") + " builds the same package in a " + c("debian:trixie") + " image with podman (variables " + c("OUTPUT") + ", " + c("WORK") + ", " + c("RX_VERSION") + ", " + c("RX_REVISION") + ", " + c("SOURCE_DATE_EPOCH") + ", " + c("TWICE") + "; default output "
      + sysf("/media/REMOTIX-DEBIAN/pacchetti") + "), runs lintian without failing on it, and applies the same four checks and R23. It is kept in the tree with " + c("build/Containerfile") + " (the image: build tools, the " + c("-dev") + " packages and the static libraries, then the packaging tools in a last layer); "
      "the 1.2.0 work does not use it. Its exit status is 0 unless a line of " + sysf("controlli.txt") + " contains \" NO\" (exit 1), 1 also if the image build or " + c("dpkg-buildpackage") + " fails, and 2 if podman is missing.")

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
         "not used by the package build, where the libraries are in " + c("/usr/local") + " of the build machine"],
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
        [c("override_dh_auto_install"), "installs the binary to " + c("/usr/libexec/remotix/remotix") + " and the hook " + c("remotix-local-login") + " beside it (0755), with " + c("remotix-pam-hook") + " (the script that the service runs before it starts to check that the PAM line of the hook is in place, "
         + rif("The local-login hold") + "), the page, defaults, licence file, "
         "the PAM file and denied-users (conffiles), the pam-auth-update profile " + c("debian/remotix.pam-config") + " as " + c("/usr/share/pam-configs/remotix") + ", the ufw profile, the KWin permission file, the polkit rules and helper, and the two "
         "switched-off \"belts\" under " + c("/usr/share/remotix/belts/") + "; it writes " + c("/usr/share/remotix/linked.json") + " with the "
         "pkg-config versions of the linked static libraries"],
        [c("execute_after_dh_auto_install"), "installs the sysusers file and the AppArmor profile (a conffile in " + c("/etc/apparmor.d")
         + ") and runs " + c("dh_apparmor") + " so that the maintainer scripts load and reload it"],
        [c("dh_install") + " (" + c("debian/remotix.install") + ")", "installs " + c("debian/needrestart/remotix.conf") + " as " + c("/etc/needrestart/conf.d/remotix.conf") + ": needrestart only lists the service for a manual restart, never restarts it by itself (the restart closes the remote desktops)"],
        [c("override_dh_installsystemd"), c("--no-enable --no-start --restart-after-upgrade") + ": the package neither enables nor starts "
         "the service; on upgrade it restarts it only if it was active or enabled (the restart closes the remote desktops, see "
         + rif("Stopping the service") + ")"],
    ], "«TAB» — The overrides of debian/rules") + \
    p("The destination paths and the role of each shipped file are described in " + rif("The package") + ".")

# ── 18.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The labels R4, R13, R14, R23 and R24 are requirement names carried over from the project's earlier packaging work. In this "
       "repository they are defined only by the scripts that implement them, " + c("build/build-deb-vm.sh") + " (and the older " + c("build/build-deb.sh") + ") and " + c("debian/rules")
       + ". (R followed by a number is also used for unrelated audit findings elsewhere, for example in the comments of "
       + c("hsrate.h") + " and " + c("tls.c") + ".)", lead=True) + \
    table(["Label", "Where", "What it checks", "How"], [
        ["R13", c("debian/rules") + ", " + c("build-deb-vm.sh"), "the installed binary has no bench function, and the unit starts none",
         "<b>At build:</b> " + c("src/rcp.c") + " must hold the line " + c("#define BENCH_ON 0") + ". <b>On the .deb:</b> the binary extracted "
         "from the package must NOT contain the string \"the BENCH FUNCTION is ON\"; an " + c("rcp.o") + " built from a copy of the tree with "
         + c("BENCH_ON") + " set to 1 and " + c("make BENCH=1") + " MUST contain it (the positive control, so that \"not found\" cannot mean "
         "\"cannot search\"). <b>Unit:</b> the " + c("ExecStart") + " of " + c("remotix.service") + " passes none of " + c("--survey") + ", "
         + c("--command-socket") + ", " + c("--audio-test") + ", " + c("--verbose")],
        ["R14", c("build-deb-vm.sh"), "no bench or test file in the package",
         "the file list of the .deb is matched against " + c("/test") + ", " + c("sudoers") + ", " + c("gpu-udev") + ", " + c("restart-") + ", "
         + c("ld.so.conf") + ", " + c("provision") + ", " + c("benches") + ", " + c("/opt/") + ", " + c(".pem") + " and " + c(".key")
         + "; any match is NO"],
        ["R4", c("build-deb-vm.sh"), "the binary's run-time linking is clean",
         c("ldd") + " of the extracted binary: no \"not found\", and no dynamic ngtcp2 or nghttp3. The line records the number of libraries (32 in "
         "the recorded runs)"],
        ["R23", c("build-deb-vm.sh") + " (TWICE=1)", "reproducibility",
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
        "The 1.2.0 package was built on the build VM and lintian showed no error and no warning (PIANO.md, 26 Nov 2026); the checks of the later builds were not read for this manual.",
        "<b>R23 has no recorded run.</b> None of the " + sysf("controlli.txt") + " files read for this manual (those of the 1.0.x packages) contains an R23 line, so no run with "
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
        [c("RX_VERSION") + " in " + c("build/build-deb-vm.sh") + " and " + c("build/build-deb.sh"), "the upstream version; the default is " + c("1.2.0~dev") + ". The tilde makes a development build sort "
         "BEFORE 1.2.0 in dpkg's ordering"],
        [c("RX_REVISION"), "the Debian revision, default 1"],
        ["the full version", c("<RX_VERSION>-<RX_REVISION>+deb13") + ", for example " + c("1.2.0-1+deb13") + "; the file is "
         + c("remotix_1.2.0-1+deb13_amd64.deb")],
        [c("debian/changelog"), "not in git: written by the build script (the copy step) with that version, the distribution " + c("trixie") + ", urgency medium, "
         "one line \"Debian 13 build\" and a maintainer line written in the script (the same name and address as in " + c("debian/control") + ")"],
        ["the manual's cover", c("manuals/sources/build.py") + " reads the default of " + c("RX_VERSION") + " and drops " + c("~dev") + ": the manual says 1.2.0"],
    ], "«TAB» — Where the version lives") + \
    term("""$ RX_VERSION=1.2.0 RX_REVISION=1 build/build-deb-vm.sh 1.2.0
$ TWICE=1 RX_VERSION=1.2.0 build/build-deb-vm.sh 1.2.0-twice     # also R23""", "Building the release package") + \
    p("Without " + c("RX_VERSION") + " a build is a development build, " + c("remotix_1.2.0~dev-1+deb13_amd64.deb") + ".") + \
    h4("What \"release\" means in this tree") + \
    p("The tree has no release script, no signing step, no repository and no publication tool: the old packaging and site folders were "
      "not carried over (" + c("docs/INVENTARIO-non-debian.md") + "). A release is the output of " + c("build-deb-vm.sh") + " with " + c("RX_VERSION=1.2.0")
      + ": the .deb, the " + c(".buildinfo") + " and the check files. The package is built unsigned (" + c("-us -uc") + "). PIANO.md leaves "
      "publication, the site and public repositories to the owner's decision, so none of them is described as existing.")

# ── 18.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Three files in the product are generated by tools that are not part of the package build. Their results are committed.",
       lead=True) + \
    table(["File", "Made by", "State"], [
        [c("src/opus-wasm/opus.wasm") + ", embedded as base64 in " + c("src/page.html") + " between the two " + c("OPUS_WASM") + " markers",
         c("src/opus-wasm/build.sh"), "libopus 1.5.2 (source URL and SHA-256 pinned) compiled with emscripten 4.0.15 from an image pinned by digest, in "
         "podman with " + c("--network=none") + " for the compile (the only tool of the tree that still uses a container; it is run to regenerate the file, never by the package build or the bench); embeds into the page. " + c("sh src/opus-wasm/build.sh --verify") + " checks that the "
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
    ("The build of the .deb on the build VM", S1),
    ("The build machine and the static QUIC libraries", S2),
    ("What build-deb-vm.sh does, step by step", S3),
    ("src/Makefile: sources, libraries, minimum versions", S4),
    ("debian/rules: the overrides and the guards", S5),
    ("The package checks R4, R13, R14, R23 and R24", S6),
    ("Version and release", S7),
    ("Generated and vendored inputs", S8),
])
