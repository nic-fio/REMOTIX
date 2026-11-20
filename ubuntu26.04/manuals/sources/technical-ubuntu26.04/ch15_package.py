from build import c, code, h4, note, p, rif, sysf, table, tree, ul, warn

# ── 15.1 What the package is ─────────────────────────────────────────────
S1 = p("REMOTIX for Ubuntu 26.04 is one binary package, " + c("remotix") + ", built from the " + c("debian/") + " folder "
       "(source format " + c("3.0 (native)") + ", " + c("debhelper-compat (= 13)") + ", " + c("Rules-Requires-Root: no")
       + "). It is installed with " + c("apt install ./remotix_*.deb") + "; there is no installer program. The "
       "build itself, in an " + c("ubuntu:26.04") + " container with the static ngtcp2 and nghttp3 and with the sources of "
       "the package's own labwc, is in "
       + rif("Build and release") + ". The package is " + c("Architecture: any") + ": the binary is compiled for the "
       "machine, and the walls of the network side exist only for x86_64 and aarch64 (" + rif("Security model") + "). "
       "The version of the file is " + c("1.0.0-1+ubuntu26.04") + " and the changelog names the suite " + c("resolute")
       + " (" + rif("Version and release") + ").",
       lead=True) + \
    p("The package changes the machine as little as possible, and says so in the maintainer scripts. It creates one "
      "system user and a few folders, defines a firewall profile without opening it, installs two polkit rules and an "
      "AppArmor profile and one PAM line, and leaves the service disabled and stopped. The PAM line is the one change to a "
      "system file: through " + c("pam-auth-update") + " the package adds " + c("session optional pam_exec.so quiet "
      "/usr/libexec/remotix/remotix-local-login") + " to " + sysf("/etc/pam.d/common-session") + " (a file of "
      + c("libpam-runtime") + ", not a conffile of REMOTIX) and takes it away when the package is removed ("
      + rif("The local-login hold") + "). Two optional system-wide protections (the power "
      "keys and suspend) are shipped switched off. Three things are specific to this package and not to a plain "
      "server program: a second program, the guest " + c("labwc") + " that hosts KWin (" + rif("Our own labwc (KDE)")
      + "), a system dconf database that the " + c("postinst") + " compiles (" + rif("The postinst: user, folders and encoding test")
      + "), and a drop-in that tells " + c("needrestart") + " never to restart the service by itself (" + rif("Service policy: installed disabled")
      + "). The sections below follow the life of the package: what it needs, "
      "what it refuses, what it installs, what it does after unpacking, what it does on removal, and what the service "
      "policy is.") + \
    note("Comments in " + c("debian/control") + ", " + c("debian/rules") + ", the maintainer scripts and " + c("debian/remotix.service") + " still speak of "
         "«the engine» and «the installer» (a program of the old multi-distribution product that no longer exists in "
         "this tree) and of " + c("phases/") + " documents. Where they say that something is done by the engine, "
         "in this package it is done by the administrator or not done. Four comments also say that the desktops survive the stop "
         "(SPECS §5.2): the one before " + c("dh_installsystemd") + " in " + c("debian/rules") + ", the one at the head of "
         + c("debian/remotix.postinst") + " (upgrade restart, “the desktops stay alive”), the one in " + c("debian/remotix.prerm")
         + " (why the sessions are closed first) and the one in " + c("debian/remotix.service") + " about " + c("KillMode")
         + ". Since 17 Nov 2026 (" + c("DECISIONS-11") + " §11.56) an orderly stop closes the desktops; those comments are "
         "product text, to be corrected at the next build. A fifth statement of the same age is gone on this branch: the child no "
         "longer passes " + c("--session-fd") + " to keep the logind session alive (" + c("DECISIONS-11") + " §11.55, with a note of "
         "18 Nov 2026: since systemd 258 logind holds the session by a pidfd of its leader; this tree has systemd 259). The leftovers are listed in "
         + rif("Appendix C — Known issues and open points") + ".", "Stale wording.")

# ── 15.2 Depends and Recommends ──────────────────────────────────────────
S2 = p("The dependencies are those that " + c("dpkg-shlibdeps") + " cannot see: it computes the libraries linked "
       "into the binary (" + c("${shlibs:Depends}") + "), and the rest is what the program uses at run time through "
       "PAM, D-Bus and commands.", lead=True) + \
    table(["Field", "Package", "Why it is there"], [
        [c("Depends"), c("libpam-systemd"), "Provides " + c("pam_systemd") + ", the module in " + c("common-session")
         + " that makes the user's logind session be born when the child calls " + c("pam_open_session()") + "."],
        [c("Depends"), c("libpam-runtime (>= 1.0.1-6)"), "Provides " + c("pam-auth-update") + ", which installs and removes the "
         "local-login line in " + sysf("/etc/pam.d/common-session") + " (" + rif("The local-login hold") + ")."],
        [c("Depends"), c("libpam-modules"), "Provides " + c("pam_listfile") + " (the denied-users line), " + c("pam_nologin")
         + ", " + c("pam_unix") + " and the other modules of the stack."],
        [c("Depends"), c("passwd"), c("usermod") + " and " + c("gpasswd") + ": the enrolment in the card's groups at a "
         "user's first connection, and its undoing at removal."],
        [c("Depends"), c("systemd"), c("loginctl") + ", " + c("systemctl") + " (including " + c("--user") + "), "
         + c("systemd-sysusers") + ", " + c("systemd-tmpfiles") + ", the unit itself."],
        [c("Depends"), c("dbus-user-session"), "The user's systemd bus, on which the child finds the compositor and "
         "the desktop's services."],
        [c("Depends"), c("pipewire") + ", " + c("wireplumber"), "The daemon: GNOME and KDE video capture and the audio "
         "of every desktop go through PipeWire. " + c("dpkg-shlibdeps") + " sees the library, not the daemon, and "
         "a minimal installation does not have it."],
        [c("Recommends"), c("va-driver-all"), "The VA-API driver of the card (Intel). Without a driver "
         "nothing is encoded, because there is no software fallback. Declared alone, without «| va-driver», because "
         "on Ubuntu 26.04 the Mesa driver lives in " + c("mesa-libgallium") + ", which provides " + c("va-driver")
         + ": with the alternative, apt would count the Recommends as satisfied and never pull the Intel driver. "
         + c("va-driver-all") + " is in " + c("universe") + " on Ubuntu (it is in " + c("main") + " on Debian)."],
        [c("Recommends"), c("mesa-vulkan-drivers"), "The Vulkan driver (RADV for AMD, the Vulkan Video road, tried before "
         "VA-API). The NVIDIA ICD comes with the proprietary driver."],
        [c("Recommends"), c("labwc") + ", " + c("wlr-randr") + ", " + c("xwayland"), "The compositor REMOTIX starts for "
         "XFCE and LXQt, with the output-size tool and Xwayland that XFCE 4.20 under labwc needs. They are installed also on a "
         "GNOME-only or KDE-only machine, because package metadata cannot say «only if XFCE is there». KDE does <b>not</b> use "
         "the distribution's " + c("labwc") + ": KWin is born nested in the package's own one (" + rif("Our own labwc (KDE)") + "). "
         + c("labwc") + " and " + c("wlr-randr") + " are in " + c("universe") + "."],
        [c("Recommends"), c("dconf-cli"), "The " + c("postinst") + " compiles the system dconf database " + sysf("/etc/dconf/db/remotix")
         + " with " + c("dconf compile") + ", and the service compiles it again at start-up if it is missing or different. Without "
         "the " + c("dconf") + " program neither the database nor the locks can be made (the session code uses the same command for its own fallback, " + c("dconf_compile_locks()") + "): no lock is in force, the session's profile has only the in-memory database on top of the user's, and "
         "what the user changes from remote is not kept at the next birth; the server says " + c("DECLARED FALLBACK, D-015: `dconf compile` is missing or failed") + " (" + rif("The postinst: user, folders and encoding test") + "). "
         "The fallback with three layers (user, compiled locks, in-memory) is the one taken when " + c("dconf") + " works but " + sysf("/etc/dconf/db/remotix") + " is missing, or when a runtime profile that is not ours is already there."],
        [c("Recommends"), c("fonts-dejavu-core"), "labwc dies without a scalable font."],
    ], "«TAB» — Dependencies of " + c("remotix") + " (" + c("debian/control") + ")") + \
    p("What apt really installed is on record for the three flavours that are not GNOME. The virtual machines of the bench "
      "(" + rif("The VM bench") + ") had the desktop installed from its ISO; installing the package with the Recommends pulled in "
      + c("labwc") + " (with " + c("libwlroots-0.19") + ", " + c("libseat1") + ", " + c("libsfdo0") + ", " + c("libliftoff0")
      + " and a few " + c("libxcb-*") + " libraries), " + c("dconf-cli") + " and " + c("wlr-randr") + ", and " + c("xwayland")
      + " (with " + c("libei1") + " and " + c("liboeffis1") + ") on Xubuntu and Lubuntu; " + c("va-driver-all") + ", "
      + c("mesa-vulkan-drivers") + " and " + c("fonts-dejavu-core") + " were not in the transaction on any of them, because the "
      "desktop already carried them (logs " + sysf("vm-radeon-installa-<name>.log") + " on the dev server, taken with the package of an earlier "
      "construction that has the same Depends and Recommends). The GNOME machine had received earlier builds of the package, so " + c("labwc")
      + " and " + c("dconf-cli") + " were already there as automatic packages: the installation of the release package on it was a " + c("--reinstall") + " and brought nothing in.") + \
    ul([
        "<b>No desktop is a dependency.</b> The package never installs a desktop by itself; with none of the four "
        "present the server says so at start-up. Nor does it recommend " + c("gnome-session") + " (the «vanilla» GNOME session of "
        + c("universe") + "; the session criterion lives in " + c("session.c") + ").",
        "<b>Whoever installs with " + c("--no-install-recommends") + " loses</b> the drivers and the compositor "
        "packages, and a desktop that needs them will not start. The server refuses the login of "
        "an XFCE or LXQt machine without " + c("labwc") + " with the code 0x0E and a line that names the package (" + rif("The startup declarations") + "); the " + c("postinst") + " also warns, but only on a machine with neither "
        + c("gnome-shell") + " nor Plasma. Xubuntu carries " + c("gnome-shell") + " even without its Recommends (" + c("studio/7-xubuntu-lubuntu.md") + "), so there the warning does not fire and the refusal of the server is the only signal. "
        + c("check-package.py") + " has an informative check, " + c("recommends") + ", that only reports which "
        "Recommends the installation pulled in (it always passes).",
        "<b>Static-Built-Using:</b> " + c("ngtcp2 (= 1.25.0)") + ", " + c("nghttp3 (= 1.18.0)") + ", " + c("labwc (= 0.9.3)") + " and "
        + c("wlroots (= 0.19.2)") + ". The build "
        "refuses (" + c("test") + " lines in " + c("debian/rules") + ") if " + c("pkg-config") + " reports another "
        "version of ngtcp2 or nghttp3, so that the field never lies; the versions of the two are also written to "
        + sysf("/usr/share/remotix/linked.json") + " for a software bill of materials. The versions of labwc and wlroots are pinned "
        "by hash in " + c("build/labwc-ospite/VERSIONS") + ", not by a test in " + c("debian/rules") + ".",
        "<b>Build-Depends</b> carry the development headers the product links (" + c("libssl-dev (>= 3.5)")
        + ", " + c("libpam0g-dev") + ", " + c("libglib2.0-dev (>= 2.80)") + ", " + c("libpipewire-0.3-dev") + ", "
        + c("libdrm-dev") + ", " + c("libva-dev") + ", " + c("libopus-dev") + ", " + c("libei-dev (>= 1.3.901)")
        + ", " + c("libxkbcommon-dev") + ", " + c("libgbm-dev") + ", " + c("libwayland-dev") + ", "
        + c("libvulkan-dev (>= 1.3.274)") + ", " + c("zlib1g-dev") + "), " + c("dh-apparmor") + ", and what the package's own labwc "
        "needs (" + c("meson") + ", " + c("patch") + ", " + c("hwdata") + ", " + c("wayland-protocols") + ", " + c("libegl-dev") + ", "
        + c("libgles-dev") + ", " + c("libinput-dev") + ", " + c("libpixman-1-dev") + ", " + c("libseat-dev") + ", " + c("libudev-dev")
        + ", " + c("libdisplay-info-dev") + ", " + c("libxml2-dev") + ", " + c("libcairo2-dev") + ", " + c("libpango1.0-dev") + ", "
        + c("libpng-dev") + "). There is no "
        "ffmpeg: encoding is on the card through libva and Vulkan Video, and audio through libopus.",
        "<b>The universe component.</b> " + c("libva-dev") + ", " + c("dh-apparmor") + ", " + c("meson") + ", " + c("libseat-dev")
        + " and, among the run-time packages, " + c("labwc") + ", " + c("wlr-randr") + " and " + c("va-driver-all")
        + " are in " + c("universe") + " on Ubuntu 26.04 (checked with " + c("apt-cache") + " in " + c("studio/8-pacchetto-e-prove.md") + "; the flavours other than GNOME are entirely in " + c("universe") + "). "
        "On a machine with " + c("main") + " only, the build image cannot be made and the Recommends do not arrive.",
    ])

# ── 15.3 preinst ─────────────────────────────────────────────────────────
S3 = p("The " + c("preinst") + " runs before the files are unpacked and has two refusals, each of which stops the "
       "installation with a message on " + c("stderr") + " and exit status 1. They replace two checks of the old "
       "installer.", lead=True) + \
    table(["Refusal", "When", "Test", "Why"], [
        ["No video card", "Only on a new installation (" + c("$1 = install") + "), never on upgrade",
         "No entry " + c("/sys/class/drm/renderD*") + " exists. That is the kernel's own list of DRM render nodes, so "
         "it does not depend on packages not yet unpacked.",
         "REMOTIX encodes only on the card; with no render node nothing can ever be shown. An installed REMOTIX is "
         "never broken by an upgrade. Requested by the owner on 17 Nov 2026."],
        ["An account named " + c("remotix") + " that belongs to a person", c("install") + " and " + c("upgrade"),
         "The account exists and any of: uid 0 or gid 0; uid in [" + c("UID_MIN") + " from " + sysf("/etc/login.defs")
         + " (1000 if absent), 60000); a login shell (anything that is not empty, " + c("*/nologin") + " or "
         + c("*/false") + "); a home under " + sysf("/home") + ", " + sysf("/root") + " or " + sysf("/var/home") + ".",
         "The network side runs as that account, and the sysusers file only creates the user when it is missing. "
         "The message tells the administrator to rename it (" + c("usermod -l") + ") or remove it."],
    ], "«TAB» — What the " + c("preinst") + " refuses") + \
    p("Besides refusing, the " + c("preinst") + " remembers: on a first installation (" + c("$1 = install") + ", no "
      "previous version, and " + sysf("/usr/lib/sysusers.d/remotix.conf") + " not yet there) where an account "
      + c("remotix") + " already exists but is not a person's, it writes " + sysf("/var/lib/remotix/net-user-preexisting")
      + ". The " + c("postrm") + " reads that file so that a purge never deletes an account REMOTIX did not create.") + \
    p("What the " + c("preinst") + " does not check: that the card can encode. A card that exists but cannot encode "
      "H.264 is said by the " + c("postinst") + " and by the server at start-up. A virtual machine that has only the emulated "
      + c("virtio-vga") + " card passes the check (the card gives a render node, " + sysf("/dev/dri/renderD128") + ") and cannot encode: the install logs of the "
      "Kubuntu, Xubuntu and Lubuntu machines, taken without the Radeon (" + c("server/vm-radeon-installa.sh") + "), show the two lines of the " + c("postinst")
      + " (<i>the video card of this machine did not encode a test frame (H.264)…</i>), and the server then says " + c("THIS SERVER CANNOT ENCODE VIDEO") + " ("
      + rif("The startup declarations") + ").") + \
    p("Verification on Ubuntu 26.04: " + c("check-package.py") + " has a " + c("preinst") + " check, which tries the refusal of a "
      "person's account only (it creates one with uid 1500 and a shell); it was not run for this manual and it is not part of the VM "
      "bench (" + rif("The package check") + "). The refusal without a card is in no check; it was not verified on Ubuntu 26.04. The "
      "installation without a card was <b>not</b> tried on this branch either: the install logs of the four VMs list a render node.")

# ── 15.4 postinst ────────────────────────────────────────────────────────
S4 = p("The " + c("postinst") + " does, on " + c("configure") + ", in this order, and never lets a failure make apt "
       "fail (each failure is a warning on " + c("stderr") + "):", lead=True) + \
    ul([
        c("systemd-sysusers remotix.conf") + ": creates the system user " + c("remotix") + " (and its group) from "
        + sysf("/usr/lib/sysusers.d/remotix.conf") + ". It is run explicitly because " + c("dh_installsysusers") + " "
        "belongs to the debhelper sequence only from compat 14 (" + c("studio/8-pacchetto-e-prove.md") + " read it in the sources of debhelper 13.31ubuntu1, the version of the build image, which has the same rule as the 13.24.2 of Debian 13; the explicit step is therefore still needed).",
        c("systemd-tmpfiles --create remotix.conf") + ": creates the folders and sets the modes (below).",
        "<b>The system dconf database.</b> If the " + c("dconf") + " command exists (package " + c("dconf-cli") + ") and the folder "
        + sysf("/usr/share/remotix/dconf/remotix.d") + " is there, it runs " + c("dconf compile") + " into a temporary file "
        + sysf("/etc/dconf/db/remotix.new.$$") + ", sets mode 0644 and renames it over " + sysf("/etc/dconf/db/remotix") + ": "
        "programs of a living session may have the old file open, so it is replaced, never rewritten in place. The keyfiles are the "
        "package's own, made at build time (" + c("debian/rules") + ", " + c("remotix --dconf-keyfiles") + ", next section); they hold the value "
        "and the lock of 24 keys of the GNOME session (the twelve " + c("VT") + " switches, Log Out kept, no user switching, no lock, "
        "no automatic suspend, the integer scale 1, and three keyboard-layout keys that are only locked). Two warnings on "
        + c("stderr") + ": <i>remotix: ⚠ dconf (package dconf-cli) not found: /etc/dconf/db/remotix not made; the GNOME remote session "
        "will use its fallback</i> and <i>remotix: ⚠ /etc/dconf/db/remotix could not be compiled…</i>. The service does the same work at "
        "every start (" + c("session_dconf_system_db_ensure()") + ", called by the root side): it compiles to a temporary file, and "
        "replaces the database only if the bytes differ or the file is missing, saying so with a line of area " + c("rootside") + " (" + rif("The startup declarations") + "). "
        "This is why a failed or skipped step here is not fatal: " + c("dconf-cli") + " is only a Recommends, and may arrive after REMOTIX.",
        "<b>The PAM line of the local-login hook.</b> If " + c("pam-auth-update") + " exists, " + c("pam-auth-update --package")
        + " reads the profile " + sysf("/usr/share/pam-configs/remotix") + " (" + c("Default: yes") + ", " + c("Priority: -1")
        + ", " + c("Session-Interactive-Only: yes") + ", " + c("Session-Type: Additional") + ", the single line " + c("session optional pam_exec.so quiet "
        "/usr/libexec/remotix/remotix-local-login") + ") and rewrites " + sysf("/etc/pam.d/common-session") + "; then the script checks that "
        + c("remotix-local-login") + " is in that file. Two cases print a warning on " + c("stderr") + " and do not stop apt: "
        "<i>remotix: ⚠ pam-auth-update not found</i>, and <i>remotix: ⚠ common-session was edited by hand</i> (the line is not in the file after "
        "the step: a local login is then not held and only the periodic check remains). A failure of " + c("pam-auth-update")
        + " itself is said too. The step runs at every " + c("configure") + ", "
        "upgrades included; whether an administrator's deselection of the profile survives an upgrade was not verified.",
        "<b>The encoding test, on the first configuration only</b> (the second argument of the script is empty) and "
        "only if the binary is there: " + c("timeout 30 /usr/libexec/remotix/remotix --encoding-test h264") + ". Its "
        "exit status is 0 if the card encodes a test frame, 3 if no card can encode, 1 if it opens and produces "
        "nothing. Any non-zero status prints a two-line warning that REMOTIX will show no desktop until the card "
        "encodes, naming the driver to check (Intel and AMD: " + c("va-driver-all") + "; NVIDIA: its proprietary "
        "driver) and the command to repeat. It does not stop the installation: the VA driver may arrive with a "
        "Recommends configured after REMOTIX itself.",
        "<b>The missing guest compositor.</b> If " + c("labwc") + " is not on the PATH, and " + c("xfce4-session") + " or "
        + c("lxqt-session") + " is, and neither " + c("gnome-shell") + " nor " + c("startplasma-wayland") + " is, the script says "
        "<i>remotix: ⚠ the package labwc is not installed (it is only a Recommends): the XFCE/LXQt desktop of this machine cannot start in REMOTIX</i> "
        "and, on a second line, <i>install it: sudo apt install labwc</i>. The test is deliberately narrow: where another desktop is "
        "present nobody can know which one REMOTIX will start, so nothing is said.",
        "The debhelper part (" + c("#DEBHELPER#") + "): the AppArmor lines of " + c("dh_apparmor") + " (load or reload "
        "the profile " + c("remotix_network") + ") and the systemd lines described in the service policy section. "
        "The service and the user groups are not touched.",
    ]) + \
    p("The encoding test is the product's own mode: " + c("main()") + " answers " + c("--encoding-test") + " before "
      "reading any other option. On an upgrade the test is not repeated.") + \
    p("<b>Checking and switching off the local-login line.</b> To see whether it is in force: "
      + c("grep remotix-local-login /etc/pam.d/common-session") + ". To follow what it does: " + c("journalctl -t remotix | grep 'local login'")
      + " (" + rif("Logging and diagnostics") + "). To switch it off, the way of Debian and Ubuntu is " + c("pam-auth-update")
      + " (untick the REMOTIX entry) or " + c("pam-auth-update --package --remove remotix") + "; <b>this was not tried</b> for this "
      "package, and the effect of switching it off is that a local login of a user who has a remote desktop is no longer held "
      "(the periodic checks of " + rif("Security model") + " remain).") + \
    warn("The " + c("postinst") + " does not enable the firewall profile, does not put the user in any group and does "
         "not enable the service. The only change it makes to a system file is the PAM line above; the dconf database is a file "
         "the package owns outside its file list, and the " + c("postrm") + " removes it. The comment at the head of the script says "
         "that the groups, the firewall and the belts are set "
         "up by «the engine», which is the old installer; in this package the groups are set up by the product at "
         "each user's first connection (" + rif("Security model") + ") and the rest is the administrator's. The same comment "
         "says that on an upgrade “the desktops stay alive”, which is no longer true: the restart closes them (" + rif("Stopping the service") + ").")

# ── 15.5 Files ───────────────────────────────────────────────────────────
FILES = tree([
    "/usr/libexec/remotix/",
    "├── remotix  # the server, mode 0755: root side, network side, child, PAM helper (one executable)",
    "├── remotix-local-login  # the local-login hook, mode 0755, libc only: run by PAM at a local login",
    "├── remotix-polkit-seated  # shell helper of the 40- polkit rule, mode 0755",
    "└── labwc  # OUR labwc 0.9.3 with a patched wlroots 0.19.2, static, mode 0755: the host of the nested KWin",
    "/usr/share/remotix/",
    "├── page.html  # the page the server sends (lintian override: it is the program, not documentation)",
    "├── remotix.conf  # defaults, read by the unit; not a conffile: an upgrade rewrites it",
    "├── linked.json  # versions of the statically linked ngtcp2 and nghttp3, from pkg-config at build time",
    "├── dconf/remotix.d/  # keyfiles of the GNOME session's rules, made in the build by remotix --dconf-keyfiles",
    "│   ├── 00-remotix  # the values",
    "│   └── locks/00-remotix  # the list of locked keys",
    "└── belts/  # the two switched-off protections",
    "    ├── remotix-power-keys.conf",
    "    └── remotix-no-suspend.conf",
    "/usr/share/polkit-1/rules.d/",
    "├── 40-remotix-remote-sessions.rules",
    "└── 50-remotix-no-poweroff.rules",
    "/usr/share/pam-configs/remotix  # mode 0644, the pam-auth-update profile of the hook; not a conffile",
    "/usr/share/applications/org.kde.remotix.desktop  # KWin's permission to capture the screen",
    "/usr/share/doc/remotix/  # copyright (with the third-party sections), THIRD-PARTY-LICENSES.gz, changelog",
    "/usr/lib/systemd/system/remotix.service  # by dh_installsystemd",
    "/usr/lib/sysusers.d/remotix.conf  # one line: the user remotix",
    "/usr/lib/tmpfiles.d/remotix.conf  # by dh_installtmpfiles from debian/remotix.tmpfiles",
    "/etc/pam.d/remotix  # conffile: the PAM service",
    "/etc/remotix/denied-users  # conffile: contains root",
    "/etc/remotix/remotix.conf.d/  # empty folder for the administrator's drop-ins",
    "/etc/ufw/applications.d/remotix  # conffile: the REMOTIX profile, defined, not opened",
    "/etc/needrestart/conf.d/remotix.conf  # conffile: the service is never restarted by needrestart",
    "/etc/apparmor.d/remotix_network  # conffile: the profile, complain mode",
], "«TAB» — Where the package puts its files (from " + c("debian/rules") + " and " + c("debian/remotix.install") + "; created at run time and not listed: "
   + c("/var/lib/remotix") + ", " + c("/run/remotix") + ", " + c("/etc/dconf/db/remotix") + " (the " + c("postinst") + " and the service), and "
   + c("/etc/apparmor.d/local/remotix_network") + " made by the " + c("dh_apparmor") + " lines of the " + c("postinst") + ")")

S5 = p("Everything is installed by " + c("override_dh_auto_install") + " and " + c("execute_after_dh_auto_install")
       + " in " + c("debian/rules") + ", plus what debhelper adds by itself and the one line of " + c("debian/remotix.install")
       + " (the needrestart drop-in). The package of the release has 59 entries in its file list, folders included.", lead=True) + FILES + \
    ul([
        "<b>Conffiles.</b> debhelper marks everything under " + sysf("/etc") + " as a conffile, so dpkg keeps the "
        "administrator's edits on upgrade and on removal, and deletes the files on purge. The release package declares five: "
        "the AppArmor profile, the needrestart drop-in, the PAM file, the denied list and the ufw profile (the list is printed by "
        + c("build-deb.sh") + " in " + sysf("controlli.txt") + "). " + c("remotix.conf") + " in " + sysf("/usr/share/remotix") + " is not one: "
        "choices go in " + sysf("/etc/remotix/remotix.conf.d/*.conf") + ", with the same lines, and win.",
        "<b>The page certificate is not in the package.</b> The server makes its own certificates at start-up in "
        + sysf("/var/lib/remotix/net/certificates") + " (" + c("certificates_prepare()") + "); an administrator's own, "
        "put there without the " + c(".ours") + " mark, is used instead.",
        "<b>The KDE file</b> " + c("org.kde.remotix.desktop") + " has " + c("Exec=/usr/libexec/remotix/remotix") + ", "
        + c("NoDisplay=true") + " and " + c("X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1") + ". The package "
        "ships it and the program only checks it at start-up (" + c("kwin_check_permission()") + "); it never writes it.",
        "<b>The two polkit files and the helper</b> are active as soon as they are installed; the two files under "
        + c("belts/") + " are not (" + rif("Security model") + ").",
        "<b>The unit comes from debhelper.</b> " + c("dh_installsystemd") + " picks " + c("debian/remotix.service") + " and "
        "installs it under " + sysf("/usr/lib/systemd/system/") + "; " + c("rules") + " has no line for it.",
        "<b>The licences.</b> " + c("debian/copyright") + " carries the licence text of REMOTIX (appended by " + c("build-deb.sh") + ") and a section for "
        + c("usr/libexec/remotix/labwc") + " («GPL-2 and Expat»: labwc is GPL-2, two of its files LGPL-2.0-or-later, wlroots is Expat). "
        + c("THIRD-PARTY-LICENSES") + " is installed (compressed) under " + sysf("/usr/share/doc/remotix/") + ".",
        "<b>No benchmark file and no bench option are in the package.</b> The build refuses to package if "
        + c("BENCH_ON") + " in " + c("rcp.c") + " is not 0, and its checks on the finished package assert that the unit "
        "passes no bench option and that no bench file is in the file list (" + rif("Build and release") + "). "
        "That does not remove " + c("--command-socket") + " from the binary; see " + rif("Login and its defences") + ".",
    ]) + \
    p("<b>Folders created at run time.</b> " + c("remotix.tmpfiles") + " (installed as " + sysf("/usr/lib/tmpfiles.d/remotix.conf")
      + ") makes " + sysf("/var/lib/remotix") + " (0755, root), " + sysf("/var/lib/remotix/net") + " (0700, " + c("remotix")
      + ") and its content owned by " + c("remotix") + " at every boot, fixes the modes of the certificates folder "
      "(0700), the keys, " + c("quic-secret") + ", " + c("log-secret") + " and the ban file (0600), and makes "
      + sysf("/run/remotix") + " (0755, root) and " + sysf("/run/remotix/net") + " (0700, " + c("remotix") + "). The "
      "file is installed and run by the " + c("postinst")
      + ", and " + c("check-package.py") + " (first-start) checks the owners and modes it produces. One more folder is not made "
      "by tmpfiles: " + sysf("/run/remotix/prelocal/") + " (root, 0700) is made by the root side when it starts, for the requests of "
      "the local-login hook (" + rif("The local-login hold") + "); it goes with " + sysf("/run/remotix") + " at a purge.") + \
    p("<b>The system user.</b> " + c("remotix.sysusers") + " is the single line " + c("u remotix - \"REMOTIX network side\" / /usr/sbin/nologin")
      + ": a system user, automatic id, home " + sysf("/") + ", shell " + c("nologin") + ", no groups, because it never "
      "opens a card. The user is the one the unit's network side drops to (" + c("--network-user") + " defaults to it). "
      "On the release run of the virtual machine it got uid 972.") + \
    p("<b>The firewall profile.</b> " + c("remotix.ufw") + " defines the application " + c("REMOTIX") + " with "
      + c("ports=7447/tcp|7447/udp") + " (TCP for the page, UDP for QUIC). The package does not run " + c("ufw allow")
      + ": defining is not opening. An administrator who uses ufw runs " + c("ufw allow REMOTIX") + ".") + \
    h4("The AppArmor profile") + \
    p("The conffile " + sysf("/etc/apparmor.d/remotix_network") + " holds the profile " + c("remotix_network") + " with the flags "
      + c("complain") + " and " + c("attach_disconnected") + ". It has no attachment path: running " + sysf("/usr/libexec/remotix/remotix")
      + " puts nothing in it, so the root side (PAM, the births of the desktops) stays unconfined. The root side writes "
      + c("exec remotix_network") + " into " + sysf("/proc/thread-self/attr/apparmor/exec") + " just before it execs the network side "
      "(" + c("apparmor_exec_net") + " in " + c("walls.c") + "), and only that process is confined. The text ends with "
      + c("include if exists <local/remotix_network>") + ", so the empty file " + sysf("/etc/apparmor.d/local/remotix_network")
      + " that " + c("dh_apparmor") + " makes is really read: the administrator's additions go there. Three rules matter on Ubuntu 26.04:") + \
    ul([
        "<b>The unix-socket denials name their operations.</b> The two lines are " + c("deny unix (bind, listen) addr=@**,") + " and "
        + c("deny unix (connect, send, receive) peer=(addr=@**),") + ". A bare " + c("deny unix addr=@*,") + " also carries " + c("create")
        + ", which has no address to compare: on the kernel of Ubuntu 26.04 (7.0, which mediates unix sockets) it forbade every unix socket, and "
        "a " + c("deny") + " holds in complain mode too. Result on the first real machine (19 Nov 2026): no D-Bus, no logind, every sign-in "
        "refused, with " + c("logind unreachable (Unable to create socket: Permission denied)") + " in the log. The register of problems has it as C4; "
        "the containers cannot show it because they run no AppArmor. Two asterisks and not one, because one stops at a " + c("/") + " and the names to close "
        "contain it (" + c("@/tmp/.X11-unix/X0") + "). Not closed: the «autobind» (a socket that lets the system give it a random abstract name).",
        "<b>The keyboard files are listed under the real folder.</b> On Ubuntu 26.04 (xkb-data 2.46) the data are in "
        + sysf("/usr/share/xkeyboard-config-2") + " and " + sysf("/usr/share/X11/xkb") + " is a symlink to it. AppArmor judges the resolved path, so both are listed, "
        "with " + sysf("/usr/share/xkeyboard-config-2.d") + ", " + sysf("/etc/xkb") + " and " + sysf("/etc/X11/xkb") + ".",
        "<b>It is still in complain mode.</b> The profile logs what it would refuse and refuses nothing except the two " + c("deny") + " lines and what "
        "the rest of the walls do. Nobody has run the whole functional suite with the profile in " + c("enforce") + ": on Ubuntu 26.04 that is "
        "<b>not verified</b>. What was seen on a real kernel: " + c("aa-status") + " lists " + c("remotix_network") + " and the line "
        + c("/usr/libexec/remotix/remotix (<pid>) remotix_network//&unconfined") + " (the root side is not in it, the network side is), and the server's own "
        "line says " + c("AppArmor: born in remotix_network") + " (" + rif("The startup declarations") + ").",
    ]) + \
    h4("The two polkit rules") + \
    p("Both are in polkit's vendor folder, so polkit reads them in file-name order together with " + sysf("/etc/polkit-1/rules.d/") + "; an administrator "
      "writes a rule with a lower number there to decide otherwise. " + c("40-remotix-remote-sessions.rules") + " is about five actions that a distribution "
      "grants without a password only to a user at a seat: refreshing the software catalogue (" + c("Flatpak.metadata-update") + ", " + c("Flatpak.appstream-update")
      + ", " + c("packagekit.system-sources-refresh") + ", yes for a REMOTIX user where the seated user gets yes) and, for network control and system repositories, "
      "yes for an administrator and a silent no for anybody else. A REMOTIX session is recognised by the helper " + c("remotix-polkit-seated") + ", which looks in logind's "
      "state files for a session of the user with the PAM service " + c("remotix") + ". " + c("50-remotix-no-poweroff.rules") + " returns " + c("NO")
      + " for <b>19</b> login1 actions: " + c("power-off") + ", " + c("reboot") + ", " + c("halt") + ", " + c("suspend") + " and " + c("hibernate")
      + ", each in the plain form, " + c("-multiple-sessions") + " and " + c("-ignore-inhibit") + " (15 actions), and the four " + c("set-reboot-parameter")
      + ", " + c("set-reboot-to-firmware-setup") + ", " + c("set-reboot-to-boot-loader-menu") + " and " + c("set-reboot-to-boot-loader-entry") + ". The last four were "
      "added on 20 Nov 2026 (register C6): in logind's policy each of them <i>implies</i> " + c("reboot") + " and defaults to yes for the user at the machine, and polkit "
      "grants an implied action even when a rule says no to it. The package " + c("unione10") + " has the rule with 15 actions; the tree and the package " + c("unione11") + " (20 Nov 2026, the one meant for the release) have 19. "
      "Root is not affected, because logind does not ask polkit of a caller that holds " + c("CAP_SYS_BOOT") + ". The checks are in " + rif("The checks of all.sh and what each proves") + " (" + c("power-entries-absent") + ", " + c("power-implied") + ", " + c("power-local-seat") + ").") + \
    note("The unit starts the server with " + c("--address 0.0.0.0") + ": once enabled it listens on every address, TCP "
         "for the page and UDP for QUIC. The port is the variable " + c("REMOTIX_PORT") + " (7447) in "
         + sysf("/usr/share/remotix/remotix.conf") + "; changing it in a drop-in does not change the ufw profile, "
         "which names 7447.", "Port and profile.")

# ── 15.6 Our own labwc ───────────────────────────────────────────────────
S6A = p("The package carries a second program, " + sysf("/usr/libexec/remotix/labwc") + ": labwc 0.9.3 with wlroots 0.19.2 and one patch of the "
        "project, statically linked. Its only job is to be the screenless host of the KWin of a KDE session. It is not the " + c("labwc")
        + " that XFCE and LXQt use: those take the one of the distribution, a Recommends.", lead=True) + \
    table(["Question", "Answer", "Source"], [
        ["Why the distribution's labwc is not enough",
         "KWin 6.5 and later draws a black single pixel as the root of its window and puts the content in subsurfaces. wlroots never reports that root as "
         "«presented», so KWin hands its clients a frame clock at 0, and Firefox, which then thinks its window is covered, stops painting. "
         "The fix is a few lines in wlroots (" + sysf("types/scene/surface.c") + ", " + c("frame_done") + "): the root surface of a surface shown on an output "
         "counts as presented at every output frame. The wlroots of the distribution has no such change.",
         c("build/labwc-ospite/README") + ", the patch"],
        ["What is in it",
         "labwc 0.9.3 (GitHub archive of the annotated tag) and wlroots 0.19.2 (the release tarball of gitlab.freedesktop.org), both pinned with a SHA-256 in "
         + c("VERSIONS") + "; wlroots is built into the labwc binary as a static library, with the drm and libinput backends, the gles2 renderer, the gbm allocator, "
         "no Xwayland, no SVG, no icons, no man pages, no NLS. The build fails if the binary links any " + c("libwlroots") + ". The release file is 1,456,680 bytes.",
         c("build/labwc-ospite/VERSIONS") + ", " + c("build.sh")],
        ["Who starts it",
         c("remotix --kwin-nested W H NODE -- …") + " in " + c("kwin.c") + " forks it with " + c("WLR_BACKENDS=headless") + ", its own runtime folder and "
         + c("LABWC_UPDATE_ACTIVATION_ENV=0") + ", and starts KWin inside. The path is a compile-time constant, " + c("REMOTIX_LABWC")
         + " (" + c("LABWC ?= /usr/libexec/remotix/labwc") + " in " + c("src/Makefile") + ", passed again by " + c("debian/rules") + "); it is never a switch at run time.",
         c("src/kwin.c") + ", " + c("src/Makefile")],
        ["If it is missing",
         "KWin is started with " + c("--virtual") + " and the line " + c("our labwc is not installed: KWin --virtual…") + " is written to " + c("stderr")
         + ". The desktop is born, but it does not take the size of the browser window at a reattach. The distribution's labwc is never used for KDE.",
         c("src/kwin.c")],
        ["Licence",
         "GPL-2 for labwc (two files LGPL-2.0-or-later), Expat for wlroots and for the patch. The corresponding source has to be published with every release: "
         + c("remotix-<version>-labwc-source.tar.gz") + ", made by " + c("build/build-deb.sh") + " (" + rif("What build-deb.sh does, step by step") + "): the two tarballs, the patch and the recipe, 7 files in a deterministic archive.",
         c("debian/copyright") + ", " + c("LICENSE.md")],
    ], "«TAB» — The guest labwc of the package") + \
    p("The build of it runs inside " + c("override_dh_auto_build") + " with the dpkg flags already in the environment (hardening, " + c("-ffile-prefix-map")
      + "), from the two tarballs that the build image fetched and checked. " + c("meson") + " is called with " + c("-Dwerror=false") + ": wlroots 0.19.2 is built with "
      + c("-Werror") + ", and the libinput of Ubuntu 26.04 raises a warning that it was not written for (a switch value not handled). " + c("build.sh") + " checks the sha256 again "
      "before it extracts anything. Details of the build are in " + rif("debian/rules: the overrides and the guards") + ".") + \
    warn("The path of the program is the same in the build and in " + c("kwin.c") + ": a build that changes " + c("LABWC") + " must run " + c("make clean") + " first, because the "
         "path is in the object code. That a KDE session really uses this binary was shown on the Kubuntu virtual machine and on the live Kubuntu (" + rif("What only a real machine or a real phone can prove")
         + "); the effect of removing it was not tried for this manual.", "One path, two places.")

# ── 15.7 prerm and postrm ────────────────────────────────────────────────
S6 = p("Removal has two scripts and two outcomes. " + c("apt remove") + " keeps the configuration and the state; "
       + c("apt purge") + " also removes what the program created by itself, <b>so that the uninstallation leaves the system clean</b> "
       "(the owner's rule of 19 Nov 2026). A purge of an installed package runs the "
       + c("prerm") + " with the argument " + c("remove") + " first, so the closing work lives in one place.",
       lead=True) + \
    p("<b>" + c("prerm") + " (only on " + c("remove") + "; on an upgrade it closes no session itself, but the "
      "restart of the service that the " + c("postinst") + " does if it was running closes them, see the last section).</b> The order matters and each step was added "
      "deliberately (the closing of the sessions before the stop, after a measurement on 17 Nov 2026):") + \
    ul([
        "<b>Take the PAM line out first.</b> " + c("pam-auth-update --package --remove remotix") + " (if " + c("pam-auth-update")
        + " exists) removes the local-login line from " + sysf("/etc/pam.d/common-session") + ", before anything else and while the "
        "profile file is still in place; a failure is said (<i>remotix: ⚠ pam-auth-update --remove remotix failed: check "
        "/etc/pam.d/common-session</i>) and does not stop dpkg. A purge passes here too, because it runs the " + c("prerm") + " with "
        + c("remove") + " first.",
        "<b>Close the sessions, with the service still running.</b> " + c("remotix_close_sessions()") + " finds "
        "the logind sessions whose " + c("Service") + " is " + c("remotix") + " and which have no seat ("
        + c("remotix_sessions()") + "; a seated session is never ours whatever its service says) and runs "
        + c("loginctl terminate-session") + " on those whose scope is alive (" + c("remotix_scope_alive()") + "). "
        "Only those: never the whole user. The order is the point: if the service were stopped first, the child "
        "that leads the logind session would exit, logind would close the session and abandon its scope with the "
        "desktop inside, and " + c("terminate-session") + " would have "
        "no scope left to stop (that is the historical reason for the order: it was written when the desktops outlived the "
        "service by design, before the decision of 17 Nov 2026 that a stop closes them, and it was kept); with the user's manager lingering the desktop then stayed up for minutes after "
        + c("apt remove") + ".",
        "It waits up to 15 s for the desktops to end by themselves, then sends SIGKILL to the scope of each session "
        "that did not (" + c("systemctl kill --kill-whom=all --signal=SIGKILL session-N.scope") + ", saying so on "
        + c("stderr") + "), then waits up to 5 s more. Never a process outside a REMOTIX session's scope.",
        "<b>Stop the service</b> with " + c("deb-systemd-invoke stop") + ", because " + c("--no-start") + " makes "
        "debhelper not do it on removal and a started service would otherwise stay alive on a deleted binary.",
        "<b>Sweep again</b> for what the stop left in an abandoned scope, then, for each person who had a REMOTIX "
        "session and has no other graphical session (a non-REMOTIX session of type x11, wayland or mir), stop " + c("graphical-session.target") + " in "
        "that user's manager.",
        "<b>Undo the group enrolments</b> recorded in " + sysf("/var/lib/remotix/group-enrollments.jsonl") + " with "
        + c("gpasswd -d") + ", only if the record is a regular file, not a link, owned by root, and after checking "
        "that the names contain nothing but " + c("A-Za-z0-9._-") + ".",
        "<b>Take back the card ACLs</b> by running " + c("remotix --drop-render-grants") + ", with the service stopped and "
        "before the record and the binary go. If it fails, a warning is printed and " + sysf("/run/remotix/render-grants-kept")
        + " is left as a marker so the " + c("postrm") + " keeps the record.",
    ]) + \
    p("<b>" + c("postrm") + ".</b> On " + c("upgrade") + " and the abort cases it does nothing. On " + c("remove") + ", " + c("purge") + " and " + c("disappear")
      + " it does two things: it deletes " + sysf("/etc/dconf/db/remotix") + " and any " + sysf("/etc/dconf/db/remotix.new.*") + " left by an interrupted compile, "
      "and it writes the profile name to " + sysf("/sys/kernel/security/apparmor/.remove") + " if that file is writable, so the profile leaves the kernel even "
      "if its file is already gone. On " + c("purge") + " it also:") + \
    ul([
        "removes " + sysf("/var/lib/remotix/net") + ", " + sysf("/var/lib/remotix/certificates") + ", " + sysf("/var/lib/remotix/ban")
        + ", " + c("ban.new") + " and " + sysf("/run/remotix") + "; removes " + c("render-grants") + " unless the marker says "
        "the ACLs could not all be taken back (then it keeps it and says so);",
        "<b>walks every account the system lists</b> (" + c("getent passwd") + ") and, for each one that has a folder " + sysf("~/.local/state/remotix")
        + " or a file " + sysf("~/.config/dconf/remotix") + ", acts <b>as that user</b> through " + c("runuser") + ", so that a link planted in a home cannot make root delete something "
        "else. In the state folder it removes the product's files by name (" + c("session.log") + ", " + c("xfce-chiavi") + ", " + c("xfce-vecchi-ripristinati") + ", "
        + c("lxqt-restored") + ", " + c("gnome-ripristinato") + ") and the folder if it is left empty. Of the dconf folder it removes "
        "<b>only</b> the regular file " + c("remotix") + " (the small database of the three keyboard keys that change during a session), never through a link, never " + c("user")
        + ", never the folder " + c("dconf") + ". Never " + c("rm -rf") + " of a folder in a home. If the product writes another file there its name "
        "must be added to the list. Homes that are absent are skipped in silence, and the walk never makes the purge fail;",
        "deletes the user " + c("remotix") + " and its group, unless " + c("net-user-preexisting") + " exists and only "
        "if its uid is between 1 and 999;",
        "removes " + c("net-user-preexisting") + " and " + c("group-enrollments.jsonl") + ", and the folder "
        + sysf("/var/lib/remotix") + " if it is empty.",
    ]) + \
    warn("The purge acts on the users that the system lists when it runs. A user that is not listed at that moment (a network directory that is down, an account in a "
         "database that is unreachable) keeps the file " + sysf("~/.config/dconf/remotix") + " and the state folder. The file is inert without REMOTIX, but the "
         "claim «the uninstallation leaves the system clean» holds for the listed users only. Declared limit, not measured on a machine with such a directory.",
         "Limit of the clean purge.") + \
    p("The " + c("lintian") + " override in " + c("debian/remotix.lintian-overrides")
      + " explains why the " + c("prerm") + " calls " + c("systemctl") + " itself: a desktop that ignores SIGTERM is "
      "killed through its own session scope, a transient unit that " + c("deb-systemd-invoke") + " cannot address. The other override is about "
      + c("page.html") + ", which is the program and not documentation.") + \
    p("<b>Verification on Ubuntu 26.04.</b> The four VMs and the live systems ran installation, restart and (for the three flavours installed from a clean state) the "
      "first start of the package, and the service came up active and enabled with " + c("remotix_network") + " loaded; the removal and the purge were <b>not</b> run by a check on this "
      "branch. " + c("check-package.py") + " names its checks install, first-start, apparmor, remove, purge, reinstall, preinst, recommends and fresh-end, "
      "and compares snapshots of " + sysf("/etc") + ", " + sysf("/usr") + ", " + sysf("/var/lib") + " and " + sysf("/run") + ", of users, groups and unit files, before and after; "
      "it needs a box that can be reset, which a VM cannot (" + rif("The package check") + "), and no run of it on Ubuntu 26.04 is on record. The clean purge, with the two "
      "new removals of 19 Nov 2026, is therefore a reading of the script, not a measurement. The AppArmor check is BLOCKED in containers, which have no AppArmor interface.")

# ── 15.8 Service policy ──────────────────────────────────────────────────
S7 = p("The package installs the service disabled and does not start it. The administrator enables it with "
       + c("systemctl enable --now remotix") + ", as the package description says. This is decided in "
       + c("debian/rules") + ":", lead=True) + \
    code("override_dh_installsystemd:\n\tdh_installsystemd --no-enable --no-start --restart-after-upgrade", "bash",
         "debian/rules") + \
    table(["Event", "What happens to the service"], [
        ["First installation", "Nothing is enabled or started. The files, the user and the folders are there."],
        ["Upgrade", "If the service was running, debhelper's restart lines restart it (" + c("try-restart") + ", as the "
         + c("postinst") + " comment says; a stopped service stays stopped) after the new files are in place (" + c("--restart-after-upgrade")
         + "). The restart is a stop followed by a start, so it <b>closes every remote desktop</b> (" + rif("Stopping the service")
         + "): the stop takes up to the bounds given there (the network side and the children have 25 s). Warn the users of a "
         "busy server before upgrading; they log in again and get a new session."],
        ["Removal", "The " + c("prerm") + " closes the REMOTIX sessions and stops the service (see the previous section)."],
        ["Purge", "As removal, then the state is deleted."],
    ], "«TAB» — The package and the service") + \
    h4("Installing as the administrator does") + \
    p("The administrator's way is two commands, and it is the one the bench follows (" + c("server/vm-radeon-installa.sh") + "):") + \
    code("sudo apt install ./remotix_1.0.0-1+ubuntu26.04_amd64.deb\nsudo systemctl enable --now remotix", "bash", "Install and start") + \
    p("The same version installed over an earlier build of itself is not a change for apt, which then does nothing; " + c("apt install --reinstall ./remotix_*.deb")
      + " replaces the files (it is what " + c("prove/banco-vm/box.sh install") + ", " + c("server/live-installa.sh") + " and " + c("server/vm-radeon-installa.sh")
      + " run, so that a package rebuilt with the same version number is really installed). A reinstall runs the maintainer scripts as an upgrade would: "
      "the service is restarted if it was running, and the encoding test of the " + c("postinst") + " is not repeated. On the release run the line of apt was "
      + c("Unpacking remotix (1.0.0-1+ubuntu26.04) over (1.0.0-1+ubuntu26.04)…") + " followed by " + c("Setting up remotix (1.0.0-1+ubuntu26.04)…") + ".") + \
    h4("needrestart") + \
    p("On Ubuntu, " + c("needrestart") + " (run by apt after an upgrade, by " + c("unattended-upgrades") + " or by hand) restarts a service that uses a library that has just "
      "been upgraded (" + c("libc6") + ", " + c("libssl3") + ", " + c("libpam") + "…) without asking, and a restart of REMOTIX closes every remote desktop. The package therefore installs "
      + sysf("/etc/needrestart/conf.d/remotix.conf") + " with the single line " + c("$nrconf{override_rc}{qr(^remotix\\.service$)} = 0;") + ": the service is then listed under "
      "«Services to be restarted manually» and left running, with the old library loaded, until the administrator restarts it when no remote desktop is open. The display managers "
      "and xrdp are exempted in the same way by the distribution's own file. That the line has this effect on a machine that gets an upgrade of a library <b>was not observed</b> "
      "(study 11, item P9, is marked postponed); the bench runs apt with " + c("NEEDRESTART_MODE=a") + " on purpose, so it does not show it either. The file is a conffile, so an administrator's edit survives.") + \
    p("The rule of the installed-disabled service comes from point 1 of decision §10.12 of " + c("DECISIONS.md") + " (the package switches nothing on; "
      "the rest of that decision is about the old installer) and is stated in the repository's " + c("CLAUDE.md")
      + ": the service is installed disabled and not started, and the administrator enables it. The unit uses the "
      "machine's name (" + c("%H") + ") for the certificate; an administrator who connects by IP address puts "
      + c("REMOTIX_OPTIONS=--name 192.168.1.10") + " in a drop-in under " + sysf("/etc/remotix/remotix.conf.d/")
      + " (the last " + c("--name") + " wins). The runtime life cycle of the service is in "
      + rif("Startup and life cycle") + ".")

CHAPTER = ("The package", [
    ("What the package is and how it is built", S1),
    ("Package metadata: Depends and Recommends", S2),
    ("The preinst refusals", S3),
    ("The postinst: user, folders and encoding test", S4),
    ("Files the package installs", S5),
    ("Our own labwc (KDE)", S6A),
    ("Removal: prerm, postrm and purge", S6),
    ("Service policy: installed disabled", S7),
])
