"""Chapter 18 — Build and release. Sources: build/build-deb-vm.sh, build/build-deb.sh and build/Containerfile (the older container
way, still in the tree), build/quic-static.sh, build/labwc-ospite/, src/Makefile, debian/rules, debian/control, src/opus-wasm/build.sh,
src/rcp.c (BENCH_ON), server/vm-radeon.sh, server/VM-BANCO.md; the logs of the dev server of the 1.0.x packages
(pacchetti/<build>/: controlli.txt, lintian.txt, elenco.txt, costruzione.log, immagine.log; log/costruzione-<build>.log)."""
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
    zone(20, 14, 860, 100, "Build VM «costruzione» (Ubuntu 26.04, no container; the libraries are built once)")
    + box(36, 46, 190, 50, "apt build dependencies", "the -dev packages + tools", "dark", 11.5)
    + box(246, 46, 190, 50, "build/quic-static.sh", "ngtcp2, nghttp3: static .a", "dark", 11.5)
    + box(456, 46, 190, 50, "labwc-ospite/fetch.sh", "labwc, wlroots tarballs", "dark", 11)
    + box(666, 46, 198, 50, "/usr/local/lib", "the libraries, versions checked", "navy", 11.5)
    + arrow(227, 71, 244, 71) + arrow(437, 71, 454, 71) + arrow(647, 71, 664, 71)
    + zone(20, 128, 860, 100, "Package (build/build-deb-vm.sh, one label per package)")
    + box(36, 160, 190, 50, "copy src/ debian/ labwc-ospite/", "changelog + copyright written", "blue", 10.5)
    + box(246, 160, 190, 50, "dpkg-buildpackage", "-b -us -uc, debian/rules", "blue", 11.5)
    + box(456, 160, 190, 50, "lintian + checks", "R4 R13 R14 (R23) on the .deb", "green", 11.5)
    + box(666, 160, 198, 50, "back to the server", "pacchetti/<label>/", "navy", 11.5)
    + arrow(227, 185, 244, 185) + arrow(437, 185, 454, 185) + arrow(647, 185, 664, 185),
    900, 244, "«FIG» — The build of the .deb: the VM, then copy, build, lint and check, bring back")

# ── 18.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX is not built on the machine where it is edited, and the 1.2.0 build uses no container. " + c("build/build-deb-vm.sh") + " [label] copies the tree to the virtual machine "
       + c("costruzione") + ", builds the package there with " + c("dpkg-buildpackage") + " (which builds the package's own labwc too), examines the finished package and brings the .deb, the source archive of "
       "the labwc and the logs back to " + sysf("/media/REMOTIX-UBUNTU/pacchetti/<label>/") + " on the dev server. The machine that runs the script needs ssh access to the dev server (its address is the variable "
       + c("RX_SERVER") + ") and a network connection: it does not compile; it fetches the two upstream tarballs of labwc and wlroots (labwc from GitHub and wlroots from gitlab.freedesktop.org, "
       "checked by hash) and makes the source archive of the labwc. It needs no git, Go, bench folder or old repository. If the build machine is off, the script turns it on (virtual only, never the Radeon) and "
       "turns it off again at the end; " + c("KEEP_VM=1") + " leaves it on (" + rif("The VM bench") + "). Inside the machine the static QUIC libraries are cloned from GitHub and apt reads the "
       "Ubuntu archives.", lead=True) + BUILD + \
    table(["Item", "Where", "Role"], [
        [c("build/build-deb-vm.sh"), "build/", "the driver: copy, dependencies, static libraries, build, lintian, checks, labwc source archive, output files. Variables " + c("RX_SERVER") + " (the ssh address of the dev server), "
         + c("RX_GUEST_PORT") + " (default 2345, the build machine's ssh port on the server), " + c("RX_VMSCRIPT") + " (the VM manager on the server) and " + c("RX_LABWC_SOURCES") + " (a folder that keeps the two tarballs between runs)"],
        [c("build/quic-static.sh"), "build/", "nghttp3 " + c("v1.18.0") + " and ngtcp2 " + c("v1.25.0") + " from source, static only, in "
         + c("/usr/local/lib") + " (overridable by " + c("NGHTTP3_VER") + " and " + c("NGTCP2_VER") + ")"],
        [c("build/labwc-ospite/"), "build/", "the recipe for the package's own labwc (" + rif("Our own labwc (KDE)") + "): " + c("README") + ", " + c("VERSIONS") + " (names, versions, sha256, URLs), " + c("fetch.sh") + " (downloads and verifies the two tarballs), "
         + c("build.sh") + " (extracts, patches, builds with meson, installs; fails if the binary links a " + c("libwlroots") + "), and the patch " + c("wlroots-0.19.2-remotix-presented-root.patch")],
        [c("src/Makefile"), "src/", "compiles and links the two programs (the server and " + c("remotix-local-login") + "); called by " + c("debian/rules")],
        [c("debian/rules"), "debian/", "the debhelper recipe: build flags, the guards, the build of the guest labwc, what goes where in the package"],
        [c("debian/control"), "debian/", "Build-Depends, Depends, Recommends, " + c("Static-Built-Using")],
        [c("build/build-deb.sh") + ", " + c("build/Containerfile"), "build/", "the older way, still in the tree: an " + c("ubuntu:26.04") + " image built with podman and a package build in it. Not the method of the 1.2.0 work (only its default version was changed, and the manuals read it); the checks of its second half are the same (" + rif("The package checks R4, R13, R14, R23 and R24") + ")"],
    ], "«TAB» — The pieces of the build") + \
    p("The virtual machine, and not the editing machine, is the point: the package is built against the libraries of Ubuntu 26.04 (measured in the buildinfo of the package of 19 Nov 2026, numbered 1.0.0: gcc 15.2.0, "
      + c("debhelper 13.31ubuntu1") + ", " + c("dpkg-dev 1.23.7ubuntu1") + ", " + c("libssl-dev 3.5.5") + ", " + c("libva-dev 2.23.0") + ", " + c("meson 1.10.1") + "). The build folders on the server are one per label, under " + sysf("/media/REMOTIX-UBUNTU/pacchetti/") + ".") + \
    note("What the package contains and how its maintainer scripts behave is in " + rif("The package") + ". This chapter is about "
         "how the bytes are made and what is checked on them.")

# ── 18.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Ubuntu 26.04 packages ngtcp2 1.16.0 and nghttp3 1.12.0, both in " + c("universe") + " (the report " + c("studio/8-pacchetto-e-prove.md") + ", read from " + c("apt-cache") + "; not re-measured for this manual). The comment in " + c("src/Makefile")
       + " still gives the figures of Debian (1.11 and 1.8), which is wrong for this tree and is a comment of the source, not of the manual. Either set is too old: the product needs ngtcp2 "
       "at least 1.25 with the " + c("ngtcp2_crypto_ossl") + " bridge (the " + c("NGTCP2_STREAM_CLOSE2_FLAG_*") + " flags used by "
       + c("transport.c") + ") and OpenSSL at least 3.5 for the native QUIC API (Ubuntu 26.04 has 3.5.5: " + c("make deps") + " printed " + c("openssl 3.5.5 (>= 3.5.0)") + " in the build of the package of 19 Nov 2026, numbered 1.0.0). So the build machine builds the two libraries from source, "
       "pinned at one version, and installs only the static archives.", lead=True) + \
    ul([
        "<b>Static only.</b> " + c("quic-static.sh") + " configures with " + c("-DENABLE_SHARED_LIB=OFF") + " and "
        + c("-DENABLE_STATIC_LIB=ON") + ", library directory fixed to " + c("lib") + " (not lib64 or a multiarch directory) so that "
        "the " + c("LIBRARY_PATH=/usr/local/lib") + " that the build sets works and the Makefile needs no path. At the end the script fails if "
        "any " + c("libngtcp2*.so*") + " or " + c("libnghttp3*.so*") + " exists in " + c("/usr/local/lib") + ": a shared object there "
        "would be picked up by the linker. The " + c("-dev") + " packages of Ubuntu for the two libraries are not installed on the build machine, so the static ones win; "
        "if a Build-Depends ever brought them in, the test of " + c("debian/rules") + " (below) would stop the build.",
        "<b>The result.</b> The package has no run-time dependency on ngtcp2 or nghttp3; its control file says so with "
        + c("Static-Built-Using: ngtcp2 (= 1.25.0), nghttp3 (= 1.18.0), labwc (= 0.9.3), wlroots (= 0.19.2)") + ".",
        "<b>The versions are written in four places</b> for ngtcp2 and nghttp3, and a change must touch all of them: the defaults of " + c("quic-static.sh")
        + ", the two " + c("test") + " lines of " + c("debian/rules") + " (R24, below), " + c("Static-Built-Using") + " in "
        + c("debian/control") + ", and " + c("MINIMI") + " in " + c("src/Makefile") + " (and the test of what is already installed in " + c("build-deb-vm.sh") + ", which compares the two versions with 1.25.0 and 1.18.0). Those of labwc and wlroots are in " + c("build/labwc-ospite/VERSIONS") + ", in " + c("Static-Built-Using") + " and in the name of the patch file; "
        "the build of the labwc checks the tarballs against " + c("VERSIONS") + " and the patch by its name, and " + c("debian/rules") + " has no " + c("test") + " line for them.",
        "<b>ngtcp2 and nghttp3 are not pinned by hash.</b> The script clones the two tags with " + c("git clone --depth 1 -b <tag>") + ". The tag is the pin; no "
        "commit id or archive checksum is checked, so a moved tag could in principle be fetched. <b>labwc and wlroots are pinned by hash</b>: " + c("VERSIONS") + " holds the SHA-256 of both tarballs (labwc 0.9.3 and wlroots 0.19.2), " + c("fetch.sh") + " checks them even when the files are already there, and " + c("build.sh") + " checks them again before it extracts.",
    ]) + \
    warn("The build needs network access to GitHub (the first time the libraries are built, and every time for labwc) and to gitlab.freedesktop.org (wlroots), from the machine that runs the script, and to the archives of Ubuntu (only if a build dependency is missing: the script tries "
         "the installation first and runs " + c("apt-get update") + " only if it fails). The libraries are built once: the script skips the step if " + c("pkg-config") + " already reports ngtcp2 1.25.0 and nghttp3 1.18.0 and " + c("libngtcp2_crypto_ossl.a") + " is in "
         + c("/usr/local/lib") + ". The compiling itself does not need the network (" + c("meson") + " runs with " + c("--wrap-mode=nodownload") + ", and the two labwc tarballs travel with the copy).")

# ── 18.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The script is a sequence of steps. The label names the output folder " + sysf("/media/REMOTIX-UBUNTU/pacchetti/<label>") + " (default: the date and time); it may contain only letters, digits, dot, underscore and dash, and not be "
       + c(".") + " or " + c("..") + ". <b>If the folder exists already, the script stops (exit 2): a previous package is never overwritten.</b>", lead=True) + \
    table(["Variable", "Default", "Meaning"], [
        [c("OUTPUT"), sysf("/media/REMOTIX-UBUNTU/pacchetti/<label>"), "where the results go on the dev server"],
        [c("RX_VERSION"), c("1.2.0~dev"), "the upstream version (see the section on versions)"],
        [c("RX_REVISION"), c("1"), "the revision of the package"],
        [c("SOURCE_DATE_EPOCH"), "newest mtime in " + c("src/") + ", " + c("debian/") + ", " + c("build/labwc-ospite/") + ", " + c("LICENSE.md") + " and "
         + c("THIRD-PARTY-LICENSES"), "the build date, for a reproducible package"],
        [c("TWICE"), "unset", "1: build a second time and compare the two .deb byte for byte (R23), and the source archive of labwc twice"],
        [c("KEEP_VM"), "unset", "1: do not turn the build machine off at the end"],
        [c("RX_LABWC_SOURCES"), "a temporary folder", "where the two labwc tarballs are kept between runs"],
    ], "«TAB» — Environment of build-deb-vm.sh") + \
    p("In order:") + \
    ul([
        "<b>The labwc sources.</b> " + c("labwc-ospite/fetch.sh") + " fetches the two upstream tarballs on the machine that runs the script and verifies them against " + c("VERSIONS") + "; a missing tarball or a different hash stops the script (exit 2).",
        "<b>Copy.</b> A clean copy of " + c("src/") + ", " + c("debian/") + ", " + c("build/labwc-ospite/") + " (as " + c("labwc-ospite/") + ") and " + c("THIRD-PARTY-LICENSES")
        + " is made in a temporary folder. The text of " + c("LICENSE.md") + " is appended to " + c("debian/copyright") + " as continuation lines of "
        + c("License: LicenseRef-REMOTIX") + " (an empty line becomes \" .\"), the leftovers of a local build "
        "(the binary, " + c("*.o") + ", the generated protocol sources) are deleted and " + c("debian/changelog") + " is written with one entry for the distribution " + c("resolute") + ", with the line \"Ubuntu 26.04 build\", "
        "dated from " + c("SOURCE_DATE_EPOCH") + ". The working tree is never touched.",
        "<b>The machine.</b> If it does not answer, the script starts it " + c("virtuale") + " and waits; it checks that it is the build virtual machine (host name " + sysf("rx-ub-costruzione") + ") and copies the work folder in (" + sysf("~/debwork/<label>") + " in the guest). A work folder left there by a failed run is kept for inspection and never removed: the script stops and asks for another label.",
        "<b>Dependencies.</b> In the guest, " + c("apt-get install --no-install-recommends") + " of " + c("build-essential") + ", " + c("pkg-config") + ", " + c("git") + ", " + c("cmake") + ", " + c("ninja-build") + ", the " + c("-dev") + " packages of OpenSSL, PAM, GLib, PipeWire, libdrm, libva, Opus, zlib, "
        "libei, xkbcommon, gbm, Wayland and the Vulkan loader, the build tools of labwc and wlroots (" + c("curl meson patch hwdata wayland-protocols libegl-dev libgles-dev libinput-dev libpixman-1-dev libseat-dev libudev-dev libdisplay-info-dev libxml2-dev libcairo2-dev libpango1.0-dev libpng-dev")
        + ") and the packaging tools " + c("debhelper") + ", " + c("dh-apparmor") + ", " + c("dpkg-dev") + ", " + c("fakeroot") + ", " + c("lintian") + " and " + c("binutils") + ". Log " + sysf("apt.log") + ".",
        "<b>Static libraries.</b> " + c("quic-static.sh") + ", unless the right versions are already there (" + rif("The build machine and the static QUIC libraries") + "). Log " + sysf("quic.log") + ".",
        "<b>Build.</b> " + c("dpkg-buildpackage -b -us -uc") + " (binary only, unsigned) in a copy of the tree; it builds our labwc too, from the tarballs that travelled with the copy. Log " + sysf("costruzione.log") + ". The .deb and the "
        + c(".buildinfo") + " come out, with a " + c(".sha256") + " of the .deb and the file list (" + sysf("elenco.txt") + ", from " + c("dpkg-deb -c") + ").",
        "<b>Lintian.</b> " + c("lintian -I --pedantic --no-tag-display-limit") + " on the .deb, into " + sysf("lintian.txt")
        + ". Warnings are only shown; <b>a lintian error fails the script</b> (the line " + c("lintian: E=0") + " must be in " + sysf("controlli.txt") + ").",
        "<b>Checks R13, R14, R4</b> on the finished package, one line each ending SI or NO, into " + sysf("controlli.txt")
        + ", followed by the control fields " + c("Depends") + ", " + c("Recommends") + ", " + c("Static-Built-Using") + " and the list of conffiles. R4 has two lines, one for the server and one for the guest labwc. The host script requires the lines "
        "(" + c("R13 banco-nel-binario") + ", " + c("R13 opzioni-di-banco-nell-unita") + ", " + c("R14 file-del-banco") + ", " + c("R4 ldd") + ", " + c("R4 ldd-labwc") + ", " + c("labwc-source") + ") to be there and to say SI: a line missing, or any line with NO, fails.",
        "<b>The source of the guest labwc.</b> The corresponding source of the labwc that the package carries is made on the machine that runs the script and saved as " + sysf("$OUTPUT/remotix-<version>-labwc-source.tar.gz") + " with its " + c(".sha256") + ": the two tarballs, the patch and the recipe "
        "(" + c("VERSIONS") + ", " + c("fetch.sh") + ", " + c("build.sh") + ", " + c("README") + "). The archive is made deterministic (" + c("tar --sort=name --owner=0 --group=0 --numeric-owner --mode=go-w --mtime=@SDE | gzip -n") + ") and must hold the 7 expected files. "
        "The result is the line " + c("labwc-source SI|NO") + " of " + c("controlli.txt") + "; on a failure the archive is removed. It is the file that a release has to publish: labwc is GPL-2 (" + rif("Version and release") + ").",
        "<b>Second build (R23)</b> only with " + c("TWICE=1") + ": a second clean copy is built and the two .deb are compared with " + c("cmp") + "; the source archive of labwc is also made twice and compared (" + c("R23 labwc-source-riproducibile") + ").",
        "<b>Exit.</b> 0 when everything passes. 1 if a check fails, if " + c("dpkg-buildpackage") + " fails or no .deb comes out: then no package is brought back, the logs go to " + sysf("<OUTPUT>-fallita-<time>") + " on the server and the guest's work folder stays. 2 if the label or the output folder is refused, the labwc tarballs are wrong or the machine does not answer.",
    ]) + \
    p("Output files in " + c("$OUTPUT") + ": the .deb, the " + c(".buildinfo") + ", the " + c(".sha256") + " of the .deb, " + sysf("costruzione.log") + ", " + sysf("costruzione-vm.log") + ", " + sysf("apt.log") + ", " + sysf("quic.log") + ", "
      + sysf("lintian.txt") + ", " + sysf("controlli.txt") + ", " + sysf("elenco.txt") + " (the file list of the package; from " + c("dpkg-deb -c")
      + "), and the labwc source archive with its checksum. The server folder holds one sub-folder per package built.")

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
        ["LABWC", c("LABWC ?= /usr/libexec/remotix/labwc") + " and " + c("override CFLAGS += -DREMOTIX_LABWC='\"$(LABWC)\"'") + ": the path of the guest labwc, compiled into " + c("kwin.c") + ". A build-time choice of the package (" + c("debian/rules") + " passes the same path), never an option at run time; "
         + c("make clean") + " first when it changes, because the path is in the object code (" + rif("Our own labwc (KDE)") + ")"],
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
         "the Makefile's default line would be skipped and gcc 15 (15.2.0 on the build machine, Ubuntu 26.04) would default to gnu23"],
        [c("LABWC_SOURCES"), c("?= /usr/local/src/labwc-sources") + ": where the two tarballs are (the older container image kept them there; " + c("build-deb-vm.sh") + " sets the variable to the folder that travels with the copy); no network during " + c("dpkg-buildpackage")],
        [c("LABWC_PATH"), c(":= /usr/libexec/remotix/labwc") + ": where the guest labwc goes in the package, and the path " + c("kwin.c") + " executes"],
        [c("override_dh_auto_clean"), c("make -C src clean") + " and removal of " + c("debian/labwc-build") + " and " + c("debian/labwc-root")],
        [c("override_dh_auto_configure"), c("make -C src deps TWIN=none") + ": nothing to configure, only the check of minimum versions"],
        [c("override_dh_auto_build"), "the guards, then the labwc, then the server: (R24) " + c("pkg-config --modversion") + " of ngtcp2 and nghttp3 must equal exactly 1.25.0 and 1.18.0; (R13) " + c("src/rcp.c")
         + " must contain the exact line " + c("#define BENCH_ON 0") + ", else the build stops. Then " + c("labwc-ospite/build.sh $(LABWC_SOURCES) debian/labwc-root") + " with " + c("JOBS") + " taken from " + c("DEB_BUILD_OPTIONS") + " (4 by default) and the dpkg flags in the environment: meson with "
         + c("--wrap-mode=nodownload") + ", wlroots built static and patched, " + c("-Dwerror=false") + " because the libinput of Ubuntu 26.04 gives wlroots 0.19.2 a warning (an enumeration value " + c("LIBINPUT_SWITCH_KEYPAD_SLIDE") + " not handled, seen in the build log) that its " + c("-Werror") + " would turn into a failure; the script fails if the binary links a " + c("libwlroots")
         + ". Last " + c("make -C src all TWIN=none CFLAGS=\"$(R_CFLAGS)\" LDFLAGS=\"$(LDFLAGS)\" LABWC=$(LABWC_PATH)") + ": the path of the guest labwc is compiled into the server"],
        [c("override_dh_auto_test"), "empty: the package build runs no tests (testing is in " + rif("Testing") + ")"],
        [c("override_dh_auto_install"), "installs the binary to " + c("/usr/libexec/remotix/remotix") + " and the hook " + c("remotix-local-login") + " beside it (0755), the guest labwc (0755), the page, defaults, licence file, "
         "the PAM file and denied-users (conffiles), the pam-auth-update profile " + c("debian/remotix.pam-config") + " as " + sysf("/usr/share/pam-configs/remotix") + ", the ufw profile, the KWin permission file, the polkit rules and helper, and the two "
         "switched-off \"belts\" under " + sysf("/usr/share/remotix/belts/") + "; it writes " + sysf("/usr/share/remotix/linked.json") + " with the "
         "pkg-config versions of the linked static libraries, and it runs the binary just built, <b>" + c("src/remotix --dconf-keyfiles $(B)/usr/share/remotix/dconf/remotix.d") + "</b>, which writes the keyfiles of the GNOME session's dconf rules from the one table of the program (" + c("DCONF_KEYS") + " in " + c("session.c") + "): there is no second list to keep in step. The " + c("postinst") + " compiles them (" + rif("The postinst: user, folders and encoding test") + ")"],
        [c("execute_after_dh_auto_install"), "installs the sysusers file and the AppArmor profile (a conffile in " + sysf("/etc/apparmor.d")
         + ") and runs " + c("dh_apparmor") + " so that the maintainer scripts load and reload it"],
        [c("debian/remotix.install"), "one line: " + c("debian/needrestart/remotix.conf") + " to " + sysf("/etc/needrestart/conf.d") + " (a conffile, since it is under " + sysf("/etc") + ")"],
        [c("override_dh_installsystemd"), c("--no-enable --no-start --restart-after-upgrade") + ": the package neither enables nor starts "
         "the service; on upgrade it restarts it only if it was active (the restart closes the remote desktops, see "
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
        ["R4", c("build-deb-vm.sh"), "the run-time linking is clean, for the server and for the guest labwc",
         "two lines. " + c("R4 ldd") + ": " + c("ldd") + " of the extracted server: no \"not found\", and no dynamic ngtcp2 or nghttp3; the line records the number of libraries. " + c("R4 ldd-labwc") + ": " + c("ldd") + " of " + c("usr/libexec/remotix/labwc") + ": no \"not found\" and no " + c("libwlroots")
         + " (NO if the file is not in the package); the line carries the output of " + c("labwc --version")],
        ["R23", c("build-deb-vm.sh") + " (TWICE=1)", "reproducibility",
         "a second clean copy is built the same way and the two .deb files are compared with " + c("cmp") + "; a difference is NO and the second "
         "file is kept as " + c("seconda-<name>") + ". A second line, " + c("R23 labwc-source-riproducibile") + ", compares two makings of the labwc source archive"],
        ["labwc-source", c("build-deb-vm.sh"), "the corresponding source of the guest labwc is made and complete",
         "the archive of 7 files, with the two tarballs verified against " + c("VERSIONS") + " (see the previous section); NO removes the archive"],
        ["R24", c("debian/rules"), "the linked static libraries are the declared versions",
         "the two " + c("test") + " lines compare " + c("pkg-config --modversion") + " with " + c("Static-Built-Using") + "; the versions are also "
         "written to " + c("linked.json") + " (an SBOM tool can read them). They cover ngtcp2 and nghttp3 only"],
    ], "«TAB» — The package requirements and where each is enforced") + \
    h4("What was recorded") + \
    p("The values below are those of " + sysf("controlli.txt") + " and " + sysf("lintian.txt") + " of the package of 19 Nov 2026, numbered 1.0.0 (the build called " + c("unione10") + " in the work); the build after it, " + c("unione11") + ", has the same lines and the same counts, with a different checksum (the polkit rule changed). They were read from the server for the earlier manual and were not taken again for 1.2.0: the 1.2.0 package was built on the build VM with " + c("build-deb-vm.sh") + " and lintian was clean (register G2); its " + sysf("controlli.txt") + " was not read for this manual.") + \
    ul([
        "<b>R13</b> SI: " + c("package: 0, positive control rcp.o with BENCH_ON 1: 1") + ", and no bench option in the unit. <b>R14</b> SI (none). <b>R4</b> SI: <b>33 libraries</b>, none missing; <b>R4 ldd-labwc</b> SI: no " + c("libwlroots") + ", none missing, " + c("labwc 0.9.3 (-xwayland -nls -rsvg -libsfdo)") + ".",
        "<b>The control fields</b> printed: " + c("Recommends: va-driver-all, mesa-vulkan-drivers, labwc, dconf-cli, wlr-randr, xwayland, fonts-dejavu-core") + "; " + c("Static: labwc (= 0.9.3), nghttp3 (= 1.18.0), ngtcp2 (= 1.25.0), wlroots (= 0.19.2)") + "; the five conffiles: the AppArmor profile, the needrestart drop-in, " + sysf("/etc/pam.d/remotix") + ", " + sysf("/etc/remotix/denied-users") + " and the ufw profile. "
        "The " + c("Depends") + " line has the libraries that " + c("dpkg-shlibdeps") + " found (among them " + c("libseat1") + ", " + c("libinput10 (>= 1.28.0)") + ", " + c("libxml2-16") + ", " + c("libpixman-1-0") + " and " + c("libwayland-server0"
        ) + ", which are those of the guest labwc) followed by the fixed ones of " + rif("Package metadata: Depends and Recommends") + ".",
        "<b>labwc-source</b> SI: the archive " + c("remotix-1.0.0-labwc-source.tar.gz") + ", 7 files. <b>R23</b> SI: <b>identical in two clean copies</b>, and <b>R23 labwc-source-riproducibile</b> SI. Both were made with " + c("TWICE=1") + ".",
        "<b>Lintian</b> (version of the build of 19 Nov 2026, with " + c("--pedantic") + "): 0 errors and 0 warnings; one information line, " + c("systemd-service-file-missing-documentation-key") + " for " + sysf("remotix.service") + ". The two overrides of " + c("debian/remotix.lintian-overrides") + " (the page is the program, the prerm calls " + c("systemctl") + ") still apply; "
        "that lintian of Ubuntu 26.04 reports no new tag for them is shown by this result and not by anything else.",
        "The file list has 59 entries (folders included); the guest labwc in it is 1,456,680 bytes and the server 3,707,960 bytes.",
    ]) + \
    warn("R23 compares two builds made from the same tree in the same run, with the same " + c("SOURCE_DATE_EPOCH") + ". Left to its default, "
         + c("SOURCE_DATE_EPOCH") + " is the newest modification time of files in " + c("src/") + ", " + c("debian/") + ", " + c("build/labwc-ospite/") + " and the two licence files, "
         "and a fresh checkout gives files new modification times. Two builds from two checkouts therefore differ unless the caller fixes "
         + c("SOURCE_DATE_EPOCH") + " (for example to the commit time).", "Limit of the reproducibility check.")

# ── 18.7 ─────────────────────────────────────────────────────────────────────
S7 = p("The version of the product exists only as package metadata. I found no version constant in " + c("src/") + " (no source file or "
       "header carries the number), and the page and the protocol have their own versions that are not the package's.", lead=True) + \
    table(["Where", "What"], [
        [c("RX_VERSION") + " in " + c("build/build-deb-vm.sh") + " and " + c("build/build-deb.sh"), "the upstream version; the default is " + c("1.2.0~dev") + ". The tilde makes a development build sort "
         "BEFORE 1.2.0 in dpkg's ordering"],
        [c("RX_REVISION"), "the revision of the package, default 1"],
        ["the full version", c("<RX_VERSION>-<RX_REVISION>+ubuntu26.04") + ", for example " + c("1.2.0-1+ubuntu26.04") + "; the file is "
         + c("remotix_1.2.0-1+ubuntu26.04_amd64.deb")],
        [c("debian/changelog"), "not in git: written by the build script (the copy step) with that version, the distribution " + c("resolute") + ", urgency medium, "
         "one line \"Ubuntu 26.04 build\" and a maintainer line written in the script (the same name and address as in " + c("debian/control") + ")"],
        ["the manual's cover", c("manuals/sources/build.py") + " reads the default of " + c("RX_VERSION") + " and drops " + c("~dev") + ": the manual says 1.2.0"],
    ], "«TAB» — Where the version lives") + \
    term("""$ RX_VERSION=1.2.0 RX_REVISION=1 build/build-deb-vm.sh 1.2.0
$ TWICE=1 RX_VERSION=1.2.0 build/build-deb-vm.sh 1.2.0-twice     # also R23""", "Building the release package") + \
    p("Without " + c("RX_VERSION") + " a build is a development build, " + c("remotix_1.2.0~dev-1+ubuntu26.04_amd64.deb") + ". The Debian 13 product has its own manual and its own file name, with a " + c("+deb13") + " suffix; the two packages are not interchangeable.") + \
    h4("What \"release\" means in this tree") + \
    p("The tree has no release script, no signing step, no repository and no publication tool: the old packaging and site folders were "
      "not carried over (" + c("docs/INVENTARIO-non-debian.md") + " lists what was left behind). A release is the output of " + c("build-deb-vm.sh") + " with " + c("RX_VERSION=1.2.0")
      + ": the .deb, the " + c(".buildinfo") + ", the check files, and <b>the source archive of the guest labwc</b> with its checksum. The package is built unsigned (" + c("-us -uc") + "). docs/STORIA-ubuntu-26.04.md leaves "
      "publication, the site and public repositories to the owner's decision, so none of them is described as existing.") + \
    note("The guest labwc is GPL-2 software that the package ships in binary form. A release must therefore publish " + c("remotix-<version>-labwc-source.tar.gz") + " (and its " + c(".sha256") + ") next to the .deb: this is stated in " + c("debian/copyright") + " and in section 8 of " + c("LICENSE.md") + ", and it is why the build makes the archive and checks that it holds the two tarballs, the patch and the recipe. "
         "Whether the publication has been made is outside this tree and is not claimed here.", "A release has two files to publish.")

# ── 18.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Four kinds of file in the product come from outside the package build. Their results are committed, except the tarballs of labwc and wlroots, which are fetched by the build script and checked by hash.",
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
        [c("labwc-0.9.3.tar.gz") + ", " + c("wlroots-0.19.2.tar.gz") + " and " + c("build/labwc-ospite/wlroots-0.19.2-remotix-presented-root.patch"), c("build/labwc-ospite/fetch.sh") + " (the tarballs, fetched at every build); the patch is committed",
         "the two upstream sources pinned in " + c("VERSIONS") + " with SHA-256; the tarballs are not in git, they travel with the copy to the build machine and are in the labwc source archive of each release. The patch is ours (Expat, like wlroots): in " + sysf("types/scene/surface.c") + ", " + c("frame_done") + ", it counts the root of a surface shown on an output as presented at every frame, "
         "for KWin 6.5 and later nested in the guest labwc (" + rif("Our own labwc (KDE)") + ")"],
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
