"""Chapter 18 — Build and release. Sources: build/build-rpm.sh, build/quic-static.sh, rpm/remotix.spec and the files of rpm/,
src/Makefile, src/opus-wasm/build.sh, src/rcp.c (BENCH_ON); the output of a build (pacchetti/<label>/: controlli.txt and the logs) was not read."""
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
    zone(20, 14, 860, 100, "Build VM «costruzione» (once)")
    + box(36, 46, 180, 50, "dnf builddep", "from rpm/remotix.spec", "dark", 12)
    + box(256, 46, 180, 50, "quic-static.sh", "ngtcp2, nghttp3: static .a", "dark", 11.5)
    + box(476, 46, 180, 50, "/usr/local/lib", "the two libraries, versions checked", "navy", 11)
    + arrow(217, 71, 254, 71) + arrow(437, 71, 474, 71)
    + zone(20, 128, 860, 100, "Package (build/build-rpm.sh, one label per package)")
    + box(36, 160, 190, 50, "copy src/ rpm/ selinux/", "tarball + spec + sources", "blue", 10.5)
    + box(246, 160, 190, 50, "rpmbuild -bb", "%build, %install", "blue", 11.5)
    + box(456, 160, 190, 50, "checks R13 and R4", "on the finished .rpm", "green", 11.5)
    + box(666, 160, 198, 50, "back to the server", "pacchetti/<label>/", "navy", 11.5)
    + arrow(227, 185, 244, 185) + arrow(437, 185, 454, 185) + arrow(647, 185, 664, 185),
    900, 244, "«FIG» — The build of the .rpm: the VM prepared once, then copy, build, check, bring back")

# ── 18.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX is never built on the machine where it is edited, and never in a container. " + c("build/build-rpm.sh") + " [label]" + " (107 lines) copies the tree to the virtual machine " + c("costruzione") + ", installs the build dependencies there, builds the static QUIC libraries once, runs " + c("rpmbuild -bb")
       + ", checks the finished package and brings the rpm and the logs back to " + sysf("/media/REMOTIX-FEDORA/pacchetti/<label>/") + " on the dev server. The machine that runs the script needs only ssh access to the dev server (its address is the variable " + c("RX_SERVER") + "): the machine that launches the build does not compile. "
       "The build machine must be on: the script does not start or stop it (" + c("server/vm-radeon.sh accendi costruzione virtuale") + ", " + rif("The VM bench") + "). It needs network access: the static libraries are cloned from GitHub and " + c("dnf") + " reads Fedora's repositories.", lead=True) + BUILD + \
    table(["Item", "Where", "Role"], [
        [c("build/build-rpm.sh"), "build/", "the driver: copy, dependencies, static libraries, rpmbuild, checks, output files. Variables " + c("RX_SERVER") + " (the ssh address of the dev server) and " + c("RX_GUEST_PORT") + " (default 2355, the build machine's ssh port on the server)"],
        [c("build/quic-static.sh"), "build/", "nghttp3 " + c("v1.18.0") + " and ngtcp2 " + c("v1.25.0") + " from source, static only, in " + c("/usr/local/lib") + " (overridable by " + c("NGHTTP3_VER") + " and " + c("NGTCP2_VER") + ")"],
        [c("rpm/remotix.spec"), "rpm/", "the recipe: BuildRequires, Requires, the build flags, the guards, what goes where, the scriptlets (" + rif("The spec file: %build, %install and the guards") + ")"],
        [sysf("rpm/*") + " (the other files)", "rpm/", "the sources the spec installs: " + c("remotix.service") + ", " + c("remotix.sysusers") + ", " + c("remotix.tmpfiles") + ", " + c("remotix.conf") + ", " + c("denied-users") + ", " + c("remotix-no-suspend.conf") + ", " + c("needrestart.conf") + ", " + c("remotix.firewalld.xml") + ", " + c("org.kde.remotix.desktop")],
        [c("selinux/"), "selinux/", "the SELinux module (" + c("remotix.te") + ", " + c("remotix.fc") + ", " + c("remotix.if") + "), compiled by the spec (" + rif("The SELinux module") + ")"],
        [c("src/Makefile"), "src/", "compiles and links the two programs (the server and " + c("remotix-local-login") + "); called by the spec"],
    ], "«TAB» — The pieces of the build") + \
    p("The build machine is a Fedora 45 virtual machine like the others of the bench (the Xfce Live image, 8 CPUs, 6 GB), so the package is built against the libraries of Fedora 45, whatever the dev server itself runs. The compiler and library versions of a build are in the " + c("rpmbuild.log") + " and " + c("controlli.txt") + " that the script brings back; "
      "they were not read for this manual, so no version is quoted here. The one version the manual does state is in the spec: OpenSSL is Fedora's own " + c("openssl-devel") + " (4.0 at the time of the work, decision D8), with no fallback to an " + c("openssl3") + " package.")

# ── 18.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Fedora 45's own ngtcp2 is 1.22.1, too old for the program (the comment at the head of " + c("build/quic-static.sh") + " says so), so the package builds ngtcp2 1.25.0 and nghttp3 1.18.0 from source and links them <b>statically</b>. There is no image to build: the libraries are built on the build machine once, and the script skips the step if the right versions are already in " + c("/usr/local") + " (step 3 of " + c("build-rpm.sh") + "). "
       "The version of nghttp3 that Fedora packages was not recorded.", lead=True) + \
    ul([
        "<b>The recipe</b> is the one of the Ubuntu package: " + c("quic-static.sh") + " clones the two tags from GitHub, builds with cmake and ninja, installs only the " + c(".a") + " files with the library folder fixed to " + c("lib") + " (so that " + c("LIBRARY_PATH") + " and " + c("PKG_CONFIG_PATH") + " in the spec point to " + c("/usr/local/lib") + "), builds ngtcp2 with the " + c("ngtcp2_crypto_ossl") + " bridge against the system's OpenSSL, "
        "and ends by checking that no " + c(".so") + " was installed, so that " + c("-lngtcp2") + " in the Makefile cannot pick up a dynamic library that is not there.",
        "<b>OpenSSL</b> is the system's. The Makefile keeps the minimum 3.5.0 in " + c("MINIMI") + "; the version found on the build machine was not recorded.",
        "<b>The versions are written in four places</b> and a change must touch all of them: the defaults of " + c("quic-static.sh") + ", the two " + c("test") + " lines of " + c("%build") + " in the spec, the two " + c("Provides: bundled()") + " lines of the spec, and " + c("MINIMI") + " in the Makefile (the minimum, not the pinned version).",
        "<b>The pin</b> is by tag, not by hash: the two tags of GitHub are trusted as they are. (labwc and wlroots are no longer built here, so there is nothing else to pin.)",
        "<b>Network.</b> GitHub for the clone of the two tags, Fedora's repositories for " + c("dnf") + ". If either is down, the step that needs it fails and the script says which log to read in the guest (" + c("quic.log") + ", " + c("dnf.log") + ").",
    ])

# ── 18.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The script is a sequence of steps. The label names the output folder " + sysf("/media/REMOTIX-FEDORA/pacchetti/<label>") + " (default: the date and time); it may contain only letters, digits, dot, underscore and dash, and not be " + c(".") + " or " + c("..") + ". <b>If the folder exists already, the script stops: a previous package is never overwritten.</b> There are no variables " + c("OUTPUT") + ", " + c("WORK") + ", " + c("IMAGE") + ", " + c("RX_VERSION") + ", " + c("RX_REVISION") + ", " + c("SOURCE_DATE_EPOCH") + " or " + c("TWICE") + " (they belong to the Ubuntu script).", lead=True) + \
    table(["Step", "What it does"], [
        ["1. copy", "builds a tarball of " + c("src/") + ", " + c("LICENSE.md") + ", " + c("THIRD-PARTY-LICENSES") + " and " + c("selinux/") + " in a temporary folder of the machine that runs the script, removing the leftovers of a local build (the binary, the " + c(".o") + " files and the generated protocol files); copies it with the files of " + c("rpm/") + " and " + c("quic-static.sh") + " to " + sysf("~/rpmwork/<label>") + " on the build machine. It first checks that the machine answers and that its name is " + c("rx-costruzione") + "."],
        ["2. dependencies", c("dnf -y install cmake ninja-build git gcc-c++ rpm-build selinux-policy-devel") + ", then " + c("dnf -y builddep") + " of the spec. The output goes to " + c("dnf.log") + " in the guest."],
        ["3. static libraries", c("quic-static.sh") + ", unless pkg-config already reports ngtcp2 1.25.0 and nghttp3 1.18.0 in " + c("/usr/local") + " (" + rif("The build image and the static QUIC libraries") + ")."],
        ["4. rpmbuild", "copies the tarball and the sources into " + sysf("~/rpmbuild/SOURCES") + " and the spec into " + sysf("~/rpmbuild/SPECS") + ", and runs " + c("rpmbuild -bb") + " (log " + c("rpmbuild.log") + "). The spec does the work (" + rif("The spec file: %build, %install and the guards") + ")."],
        ["5. checks", "on the finished rpm (opened with " + c("rpm2cpio") + "): <b>R13</b>, the binary does not carry the bench function (" + c("strings") + " finds no «the BENCH FUNCTION is ON»); <b>R4</b>, " + c("ldd") + " of the server finds no missing library and no dynamic ngtcp2 or nghttp3. It writes " + c("controlli.txt") + " with the two lines, the linked OpenSSL libraries, and the " + c("Requires") + ", " + c("Recommends") + ", " + c("Provides") + " and file list of the rpm. "
         "<b>If a line is missing or says NO, the package is not brought back</b> (it stays in the guest, in " + sysf("~/rpmbuild/RPMS") + ")."],
        ["6. back", "creates the output folder on the server and brings the rpm, the logs and " + c("controlli.txt") + " into it."],
    ], "«TAB» — What build-rpm.sh does, in order") + \
    p("Exit status: 0 when the package is back; 1 when a step or a check failed; 2 for a wrong call, a label that already exists, or a build machine that does not answer. There is no lint step: neither " + c("lintian") + " nor " + c("rpmlint") + " is run. A build leaves no state to clean on the machine that runs the script.") + \
    term("""$ sh build/build-rpm.sh 1.2.0-a            # the build machine already on (server/vm-radeon.sh accendi costruzione virtuale)""", "Building") + \
    p("The test packages of the Fedora work are named by a letter and a number (" + rif("What was verified on Fedora 45, and what was not") + "); the label is the folder name, and the file name of the rpm is that of the spec, " + c("remotix-1.2.0-1.fc45.x86_64.rpm") + ".")

# ── 18.4 ─────────────────────────────────────────────────────────────────────
S4 = p("One Makefile, no configure step. It builds " + c(str(len(SOURCES))) + " C files (the variable " + c("SORGENTI") + ") into the server "
       "binary " + c("remotix") + ", plus " + c(str(len(PROTOCOLS))) + " Wayland protocol files generated at build time. The target "
       + c("all") + " also builds a second, separate program, " + c("remotix-local-login") + ", from " + c("local_login.c")
       + " alone: libc only, the same flags, no library (the rule " + c("$(LOCAL_LOGIN)") + "). It is the PAM hook of the local-login hold ("
       + rif("The local-login hold") + ").", lead=True) + \
    table(["Topic", "What the Makefile does"], [
        ["compiler flags", c("CFLAGS ?= -O2 -g -std=gnu11 -Wall -Wextra -Wno-unused-parameter") + " as a default, then "
         + c("override CFLAGS += -D_GNU_SOURCE") + " and the " + c("pkg-config") + " flags of every library. gnu11 and not c11 because "
         + c("accept4") + ", " + c("SOCK_NONBLOCK") + " and the ancillary messages are needed. The spec passes Fedora's flags (" + c("%{optflags}") + " and " + c("%{build_ldflags}") + ") together with " + c("-std=gnu11") + ", "
         "because the default line does not apply when " + c("CFLAGS") + " is already set, and gcc 15 would default to gnu23"],
        ["libraries", c("-lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm") + " and the pkg-config libraries of GLib/GIO, "
         "PipeWire, libva and libva-drm, libei and xkbcommon, wayland-client, gbm, opus, vulkan and zlib. " + c("-lselinux") + " is new on Fedora (the SELinux context of the child, " + c("child.c") + ", and the notes of the walls, " + c("walls.c") + "); " + c("libselinux-devel") + " is in the BuildRequires of the spec, but " + c("make deps") + " does not check libselinux (it is not in " + c("MINIMI") + "), and whether the Makefile then fails with a clear message when the headers are missing was not verified. libdrm is in the compile "
         "flags only (the " + c("DRM_FORMAT_MOD_*") + " macros): nothing is linked for it"],
        ["Wayland protocols", "the XML files of " + c("src/protocols/") + " become " + c("<name>-client-protocol.h") + " and "
         + c("<name>-protocol.c") + " through " + c("wayland-scanner") + "; " + c("clean") + " removes them. Names: "
         + ", ".join(c(x) for x in PROTOCOLS) + ". Two more than on Ubuntu: " + c("kde-output-device-v2") + " and " + c("kde-output-management-v2") + ", the output configuration of KWin 6.8 that " + c("kwin_output_resize()") + " uses; their XML files are an unmodified copy from plasma-wayland-protocols, pinned by commit (" + c("src/protocols/README-kde-output.txt") + "), because Fedora's package does not carry them"],
        ["rebuild on flag change", c(".flags") + " is rewritten, only when it differs, at every run and every object depends on it: "
         "a change of flags recompiles everything"],
        ["bench build", c("BENCH ?= 0") + "; " + c("make BENCH=1") + " adds " + c("-DREMOTIX_BENCH") + ", which compiles in the bench function "
         "of RCP §7.5 (the " + c("BENCH_MARK") + " and " + c("BENCH_OUTCOME") + " messages). The package never sets it (R13)"],
        ["LABWC", c("LABWC ?= /usr/libexec/remotix/labwc") + " and " + c("override CFLAGS += -DREMOTIX_LABWC='\"$(LABWC)\"'") + " remain from the Ubuntu package, where it was the path of the package's own labwc. On Fedora the spec never sets " + c("LABWC") + ", the package has no such program, and the code that uses the path cannot be reached (" + rif("KDE with KWin alone") + "): it is a string left in the object code, not a feature"],
        ["DEPS_PREFIX", "if set, adds " + c("-I") + ", " + c("-L") + " and an " + c("-rpath") + " for a private prefix holding ngtcp2 and nghttp3; "
         "not used by the package build, where the libraries are in " + c("/usr/local") + " of the build VM"],
    ], "«TAB» — What src/Makefile does") + \
    h4("The declared minimum versions") + \
    table(["pkg-config module", "Minimum"], [[c(a), (c(b) if b != "0" else "any")] for a, b in MINIMA], "«TAB» — MINIMI in src/Makefile, checked by make deps") + \
    p(c("make deps") + " checks every module against its minimum, then tries to compile and link an empty program that includes each "
      "header the product needs (" + c("ngtcp2/ngtcp2.h") + ", " + c("ngtcp2/ngtcp2_crypto_ossl.h") + ", " + c("nghttp3/nghttp3.h") + ", OpenSSL, PAM, GIO, "
      "PipeWire, " + c("drm_fourcc.h") + ", libva, gbm, opus, vulkan, zlib). It prints OK, NO or ?? per item and exits non-zero on any "
      "failure; the " + c("%build") + " section of the spec runs it first (" + c("make -C src deps TWIN=none") + "), so a missing or old library stops the build with a line that names it.") + \
    h4("The twin comparison and TWIN=none") + \
    p(c("rcp.c") + ", " + c("rcp.h") + ", " + c("authentication.c") + " and " + c("msgrate.h") + " (variable " + c("GEMELLATI") + ") were designed to exist "
      "in two copies, the product's and a bench's, and the target " + c("fingerprints") + ", part of " + c("all") + ", compares them with "
      + c("cmp") + " before compiling. The default " + c("TWIN ?= ../benches/rcp") + " points to a folder that this repository does not "
      "have. With a missing twin folder the target stops the build (exit 2) unless the caller declares " + c("TWIN=none") + ", in which case "
      "it prints that nothing was compared. " + "The spec passes " + c("TWIN=none") + " to both " + c("make") + " calls of " + c("%build") + ", so the package build never "
      "compares anything.") + \
    warn("A plain " + c("make") + " in " + c("src/") + " fails at " + c("fingerprints") + " unless " + c("TWIN=none") + " is given. This is the "
         "result of reading the Makefile; it was not run for this manual.")

# ── 18.5 ─────────────────────────────────────────────────────────────────────
S5 = p("The recipe of the package is " + c("rpm/remotix.spec") + " (502 lines). Its " + c("%build") + " and " + c("%install") + " sections are what " + sysf("debian/rules") + " is for Debian; the scriptlets are in " + rif("The package") + ". Each override has a reason written in the file.", lead=True) + \
    table(["Piece", "What it does", "Why"], [
        [c("%global debug_package %{nil}"), "no debuginfo package", "the package is one binary with its libraries linked statically"],
        [c("%global rxlibexec %{_libexecdir}/remotix"), "the folder of the programs, " + c("/usr/libexec/remotix"), "one name for the many install lines"],
        [c("%build") + ": " + c("make -C src deps TWIN=none"), "the check of the minimum versions and headers (" + rif("src/Makefile: sources, libraries, minimum versions") + "), with " + c("LIBRARY_PATH=/usr/local/lib") + " and " + c("PKG_CONFIG_PATH=/usr/local/lib/pkgconfig") + " exported", "a missing or old library stops the build with a line that names it; the static libraries are in " + c("/usr/local") + ", outside the BuildRequires"],
        ["R24: two " + c("test") + " lines", c("pkg-config --modversion libngtcp2") + " must be 1.25.0 and " + c("libnghttp3") + " 1.18.0", "so that the " + c("Provides: bundled()") + " lines never lie"],
        ["R13: " + c("grep -qx '#define BENCH_ON 0' src/rcp.c"), "the build stops if " + c("rcp.c") + " has the bench function switched on", "the package must not carry it"],
        [c("make -C src all TWIN=none CFLAGS=\"%{optflags} -std=gnu11 -Wall -Wextra -Wno-unused-parameter\" LDFLAGS=\"%{build_ldflags}\""), "builds the two programs with Fedora's flags", "the hardening flags of the distribution come with " + c("%{optflags}") + " and " + c("%{build_ldflags}") + "; " + c("-std=gnu11") + " is added because gcc 15 defaults to gnu23, which the code is not written for"],
        ["the SELinux module", c("make -C selinux -f /usr/share/selinux/devel/Makefile remotix.pp") + " and " + c("bzip2 -9 -f selinux/remotix.pp"), "the module is compiled in the build and installed as " + c("remotix.pp.bz2") + " (" + rif("The SELinux module") + ")"],
        [c("%install"), "puts every file in its place (" + rif("Files the package installs") + "); runs " + c("remotix --dconf-keyfiles") + " to make the dconf keyfiles from the binary just built; writes " + sysf("linked.json") + " from pkg-config; installs the needrestart drop-in with " + c("install -D … %{SOURCE7}"), "the keyfiles come from the same table the program uses, so there is no second list to keep in step"],
    ], "«TAB» — The build and install sections of the spec") + \
    p("What does not exist on Fedora: the guest labwc and its meson build, the wrap-mode and the hardening of debhelper (" + c("hardening=+all") + "), the units installed by debhelper, and the " + c(".install") + " file of the needrestart drop-in. The system is simpler because the package ships one program, not two.")

# ── 18.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The labels R4, R13, R14, R23 and R24 are requirement names carried over from the project's earlier packaging work. On Fedora <b>three are active</b>: R4, R13 and R24; R14 and R23 do not exist here. The title of this section keeps the five names because other chapters refer to it.", lead=True) + \
    table(["Label", "Where it is checked", "What it asserts", "State on Fedora"], [
        ["R4", c("build/build-rpm.sh") + ", step 5", c("ldd") + " of the installed server: nothing is missing, and neither ngtcp2 nor nghttp3 is linked dynamically", "active; there is no check of a labwc (the package has none)"],
        ["R13", c("%build") + " in the spec, and " + c("build-rpm.sh") + ", step 5", "the source has " + c("#define BENCH_ON 0") + ", and the binary of the finished package carries no «the BENCH FUNCTION is ON» string", "active at both levels. The Ubuntu package also had a positive check (the bench build does carry the string) and a check that the unit passes no bench option; whether an equivalent exists on Fedora was not verified"],
        ["R14", "—", "no benchmark or test file in the package", "not active: the file list of the spec is explicit and has none, but no script checks it"],
        ["R23", "—", "a reproducible build (two builds, same bytes)", "not active: there is no " + c("TWICE") + " and no " + c("SOURCE_DATE_EPOCH") + " in the script"],
        ["R24", c("%build") + " in the spec", "the linked static libraries are the declared versions", "active (the two " + c("test") + " lines)"],
    ], "«TAB» — The checks of the package build and their state") + \
    p("There is no " + c("lintian") + " and no " + c("rpmlint") + ", and no source archive of a guest labwc (the package has none). The numbers that the Ubuntu manual records for its package (the number of linked libraries, the number of entries, the size of the labwc and of the server) are not repeated: the figures of a Fedora build are in the " + c("controlli.txt") + " that " + c("build-rpm.sh") + " writes for each package, "
      "in " + sysf("/media/REMOTIX-FEDORA/pacchetti/<label>/controlli.txt") + ", and none was read for this manual. A reader who needs them takes them from there for the package he has in his hands.")

# ── 18.7 ─────────────────────────────────────────────────────────────────────
S7 = p("The version of the product exists only as package metadata. There is no version constant in " + c("src/") + ": the manuals read it from the spec at every generation, so the cover and the file names never drift from it. It is in " + c("rpm/remotix.spec") + ": " + c("Version: 1.2.0") + " and " + c("Release: 1%{?dist}") + ", which gives the file "
       + c("remotix-1.2.0-1.fc45.x86_64.rpm") + ". The history is the " + c("%changelog") + " of the spec; the last entry (25 Nov 2026, 1.2.0-1) says «First release for Fedora 45 (GNOME, KDE Plasma, XFCE, LXQt), with its own SELinux module» and «KDE: a local login closes the remote desktop also when a program does not close by itself». "
       "There are no variables " + c("RX_VERSION") + " or " + c("RX_REVISION") + ", no " + c("~dev") + " suffix and no " + sysf("debian/changelog") + ".", lead=True) + \
    p("<b>The number.</b> 1.2.0 is the way the owner wrote «1.2» (25 Nov 2026), because the changes born on Fedora, KDE above all, are substantial and are to be carried to the Debian 13 and Ubuntu 26.04 packages as well. The package 1.2.0 has the same code as the test package " + c("i2") + ", and it was not yet rebuilt when this manual was written; the way to build it is " + c("build/build-rpm.sh <label>") + " (" + rif("What build-rpm.sh does, step by step") + ").") + \
    h4("What release means") + \
    p("There is no release script, no signature and no repository of REMOTIX for Fedora: the rpm is <b>not signed</b>, which is why the bench installs it with " + c("rpm -U --nosignature") + ", and an administrator who has the file installs it with " + c("sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm") + " (dnf accepts a local file; whether it asks about the signature of an unsigned local file on a given machine was not recorded). "
      "Publishing the package, the site or a repository is done only by the owner's order (" + c("PIANO.md") + "). Debian 13 and Ubuntu 26.04 have their own manuals and their own package names (the suffix " + c("+deb13") + " and " + c("+ubuntu26.04") + ").") + \
    h4("Licences") + \
    p("The package carries " + c("LICENSE.md") + " (as the licence file) and " + c("THIRD-PARTY-LICENSES") + " (as documentation). The licence tag of the spec is " + c("LicenseRef-REMOTIX AND MIT") + ". labwc is not REMOTIX's any more: on Fedora it is a package of the distribution, which the product starts for XFCE and LXQt and does not carry, so a release has <b>no source archive of labwc to publish</b>, which the Ubuntu package had to. "
      "Note for the reader of the sources: " + c("LICENSE.md") + " was corrected on 25 Nov 2026 to drop the paragraph on the labwc of the Ubuntu package.")

# ── 18.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Three kinds of file in the product come from outside the package build. Their results are committed. (The tarballs of labwc and wlroots of the Ubuntu package are gone: Fedora's package does not build them.)",
       lead=True) + \
    table(["File", "Made by", "State"], [
        [c("src/opus-wasm/opus.wasm") + ", embedded as base64 in " + c("src/page.html") + " between the two " + c("OPUS_WASM") + " markers",
         c("src/opus-wasm/build.sh"), "libopus 1.5.2 (source URL and SHA-256 pinned) compiled with emscripten 4.0.15 from an image pinned by digest, in "
         "podman with " + c("--network=none") + " for the compile; embeds into the page. " + c("sh src/opus-wasm/build.sh --verify") + " checks that the "
         "page carries exactly " + c("opus.wasm") + " and that the module exports every " + c("rx_*") + " function the page calls. The SHA-256 of "
         "the committed module is in " + c("opus.wasm.sha256") + ". The verification was not run for this manual; inherited, and not run in the Fedora work (no containers on this bench)"],
        [c("src/vulkanvideo_rgb_nv12_spv.h"), "a script named in its first line, " + sysf("benches/19-vulkan/19-shader.sh"), "the SPIR-V of "
         + c("vulkanvideo_rgb_nv12.comp") + " as a C array. The script is not in this repository, so the shader cannot be rebuilt from the tree as "
         "it stands"],
        [c("src/protocols/*.xml") + " (the other ten)", "copied from their upstreams", "turned into C by " + c("wayland-scanner") + " at every build"],
        [sysf("src/protocols/kde-output-*.xml"), "copied unmodified from plasma-wayland-protocols (commit " + c("cd65734…") + " of 19 Nov 2026; the file " + c("README-kde-output.txt") + " names the commit, the files' last changes and the interface versions)", "Fedora's package of those protocols (1.23.0) does not carry them. Licence MIT-CMU, with its text in " + c("THIRD-PARTY-LICENSES") + ". Used by " + c("kwin_output_resize()") + " (" + rif("KDE with KWin alone") + ")"],
    ], "«TAB» — Generated or vendored inputs") + \
    tip("A change to " + c("vulkanvideo_rgb_nv12.comp") + " needs a tool chain (glslang or similar) that no script in the tree provides. "
        "See " + rif("Extending REMOTIX and porting to another distribution") + " for how to add a codec.")


CHAPTER = ("Build and release", [
    ("The RPM build on the build VM", S1),
    ("The build image and the static QUIC libraries", S2),
    ("What build-rpm.sh does, step by step", S3),
    ("src/Makefile: sources, libraries, minimum versions", S4),
    ("The spec file: %build, %install and the guards", S5),
    ("The package checks R4, R13, R14, R23 and R24", S6),
    ("Version and release", S7),
    ("Generated and vendored inputs", S8),
])
