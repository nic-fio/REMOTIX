from build import c, code, note, p, rif, sysf, table, tree, ul, warn

# ── 15.1 What the package is ─────────────────────────────────────────────
S1 = p("REMOTIX for Debian 13 is one binary package, " + c("remotix") + ", built from the " + c("debian/") + " folder "
       "(source format " + c("3.0 (native)") + ", " + c("debhelper-compat (= 13)") + ", " + c("Rules-Requires-Root: no")
       + "). It is installed with " + c("apt install ./remotix_*.deb") + "; there is no installer program. The "
       "build itself, on the build virtual machine with the static ngtcp2 and nghttp3, is in "
       + rif("Build and release") + ". The package is " + c("Architecture: any") + ": the binary is compiled for the "
       "machine, and the walls of the network side exist only for x86_64 and aarch64 (" + rif("Security model") + ").",
       lead=True) + \
    p("The package changes the machine as little as possible, and says so in the maintainer scripts. It creates one "
      "system user and a few folders, defines a firewall profile without opening it, installs two polkit rules and an "
      "AppArmor profile and one PAM line, and leaves the service disabled and stopped. The PAM line is the one change to a "
      "system file: through " + c("pam-auth-update") + " the package adds " + c("session optional pam_exec.so quiet "
      "/usr/libexec/remotix/remotix-local-login") + " to " + c("/etc/pam.d/common-session") + " (a file of "
      + c("libpam-runtime") + ", not a conffile of REMOTIX) and takes it away when the package is removed ("
      + rif("The local-login hold") + "). Two optional system-wide protections (the power "
      "keys and suspend) are shipped switched off. The sections below follow the life of the package: what it needs, "
      "what it refuses, what it installs, what it does after unpacking, what it does on removal, and what the service "
      "policy is.") + \
    note("Comments in " + c("debian/control") + ", " + c("debian/rules") + " and the maintainer scripts still speak of "
         "«the engine» and «the installer» (a program of the old multi-distribution product that no longer exists in "
         "this tree) and of " + c("phases/") + " documents. Where they say that something is done by the engine, "
         "in this package it is done by the administrator or not done. Four comments also say that the desktops survive the stop "
         "(SPECS §5.2): the one before " + c("dh_installsystemd") + " in " + c("debian/rules") + ", the one at the head of "
         + c("debian/remotix.postinst") + " (upgrade restart, “the desktops stay alive”), the one in " + c("debian/remotix.prerm")
         + " (why the sessions are closed first) and the one in " + c("debian/remotix.service") + " about " + c("KillMode")
         + ". Since 17 Nov 2026 (" + c("DECISIONS-11") + " §11.56) an orderly stop closes the desktops; those comments are "
         "product text, to be corrected at the next build. The leftovers are listed in "
         + rif("Appendix C — Known issues and open points") + ".", "Stale wording.")

# ── 15.2 Depends and Recommends ──────────────────────────────────────────
S2 = p("The dependencies are those that " + c("dpkg-shlibdeps") + " cannot see: it computes the libraries linked "
       "into the binary (" + c("${shlibs:Depends}") + "), and the rest is what the program uses at run time through "
       "PAM, D-Bus and commands.", lead=True) + \
    table(["Field", "Package", "Why it is there"], [
        [c("Depends"), c("libpam-systemd"), "Provides " + c("pam_systemd") + ", the module in " + c("common-session")
         + " that makes the user's logind session be born when the child calls " + c("pam_open_session()") + "."],
        [c("Depends"), c("libpam-runtime (>= 1.0.1-6)"), "Provides " + c("pam-auth-update") + ", which installs and removes the "
         "local-login line in " + c("/etc/pam.d/common-session") + " (" + rif("The local-login hold") + ")."],
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
        [c("Recommends"), c("va-driver-all"), "The VA-API driver of the card (Intel and Mesa); without a driver "
         "nothing is encoded, because there is no software fallback. Declared alone, without «| va-driver», because "
         "the alternative is already satisfied by Mesa's " + c("Provides") + " and apt would never pull the Intel "
         "driver."],
        [c("Recommends"), c("mesa-vulkan-drivers"), "The Vulkan driver (RADV for AMD, the Vulkan Video road). The NVIDIA "
         "ICD comes with the proprietary driver."],
        [c("Recommends"), c("labwc") + ", " + c("wlr-randr") + ", " + c("xwayland"), "The compositor REMOTIX starts for "
         "XFCE and LXQt, and for KDE (KWin is born nested in a screenless labwc). They are installed also on a "
         "GNOME-only or KDE-only machine, because package metadata cannot say «only if XFCE is there». " + c("labwc") + " is Debian's own "
         "package: REMOTIX neither contains nor builds it (nor wlroots, which it links), and uses the one of the distribution. Where it "
         "is missing on an XFCE or LXQt machine the " + c("postinst") + " says so (below) and a user who logs in is told (" + rif("Logging and diagnostics") + ")."],
        [c("Recommends"), c("dconf-cli"), "GNOME session rules are compiled with " + c("dconf compile") + "; without it "
         "GNOME goes back to a declared fallback in which the user's changes made remotely are not kept."],
        [c("Recommends"), c("fonts-dejavu-core"), "labwc dies without a scalable font."],
    ], "«TAB» — Dependencies of " + c("remotix") + " (" + c("debian/control") + ")") + \
    ul([
        "<b>No desktop is a dependency.</b> The package never installs a desktop by itself; with none of the four "
        "present the server says so at start-up. Nor does it recommend " + c("gnome-session") + ".",
        "<b>Whoever installs with " + c("--no-install-recommends") + " loses</b> the drivers and the compositor "
        "packages, and a desktop that needs them will not start. The " + c("postinst") + " only warns about the "
        "one case it can recognise, labwc missing on a machine with XFCE or LXQt and without GNOME or Plasma (below); "
        "otherwise nothing in the package verifies this after the fact; " + c("check-package.py") + " has an informative check, " + c("recommends") + ", that only reports which "
        "Recommends the installation pulled in (it always passes).",
        "<b>Static-Built-Using:</b> " + c("ngtcp2 (= 1.25.0)") + " and " + c("nghttp3 (= 1.18.0)") + ". The build "
        "refuses (" + c("test") + " lines in " + c("debian/rules") + ") if " + c("pkg-config") + " reports another "
        "version, so that the field never lies; the versions are also written to "
        + c("/usr/share/remotix/linked.json") + " for a software bill of materials.",
        "<b>Build-Depends</b> carry the development headers the product links (" + c("libssl-dev (>= 3.5)")
        + ", " + c("libpam0g-dev") + ", " + c("libglib2.0-dev (>= 2.80)") + ", " + c("libpipewire-0.3-dev") + ", "
        + c("libdrm-dev") + ", " + c("libva-dev") + ", " + c("libopus-dev") + ", " + c("libei-dev (>= 1.3.901)")
        + ", " + c("libxkbcommon-dev") + ", " + c("libgbm-dev") + ", " + c("libwayland-dev") + ", "
        + c("libvulkan-dev (>= 1.3.274)") + ", " + c("zlib1g-dev") + ") and " + c("dh-apparmor") + ". There is no "
        "ffmpeg: encoding is on the card through libva and Vulkan Video, and audio through libopus.",
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
         "The account exists and any of: uid 0 or gid 0; uid in [" + c("UID_MIN") + " from " + c("/etc/login.defs")
         + " (1000 if absent), 60000); a login shell (anything that is not empty, " + c("*/nologin") + " or "
         + c("*/false") + "); a home under " + c("/home") + ", " + c("/root") + " or " + c("/var/home") + ".",
         "The network side runs as that account, and the sysusers file only creates the user when it is missing. "
         "The message tells the administrator to rename it (" + c("usermod -l") + ") or remove it."],
    ], "«TAB» — What the " + c("preinst") + " refuses") + \
    p("Besides refusing, the " + c("preinst") + " remembers: on a first installation (" + c("$1 = install") + ", no "
      "previous version, and " + c("/usr/lib/sysusers.d/remotix.conf") + " not yet there) where an account "
      + c("remotix") + " already exists but is not a person's, it writes " + c("/var/lib/remotix/net-user-preexisting")
      + ". The " + c("postrm") + " reads that file so that a purge never deletes an account REMOTIX did not create.") + \
    p("What the " + c("preinst") + " does not check: that the card can encode. A card that exists but cannot encode "
      "H.264 is said by the " + c("postinst") + " and by the server at start-up.") + \
    p("Verification: " + c("check-package.py") + " has a " + c("preinst") + " check, which tries the refusal of a "
      "person's account only (it creates one with uid 1500 and a shell); the refusal without a card is not in it. "
      + c("PIANO.md") + " records, "
      "for 17 Nov 2026, that on a virtual machine without a video card the installation is refused cleanly, and that "
      "in containers with a card " + c("check-package.py") + " passed «8/8» on the four desktops (the file lists nine "
      "check names; the two counts were not reconciled for this manual).")

# ── 15.4 postinst ────────────────────────────────────────────────────────
S4 = p("The " + c("postinst") + " does, on " + c("configure") + ", in this order, and never lets a failure make apt "
       "fail (each failure is a warning on " + c("stderr") + "):", lead=True) + \
    ul([
        c("systemd-sysusers remotix.conf") + ": creates the system user " + c("remotix") + " (and its group) from "
        + c("/usr/lib/sysusers.d/remotix.conf") + ". It is run explicitly because " + c("dh_installsysusers") + " "
        "belongs to the debhelper sequence only from compat 14 (measured with debhelper 13.24.2 at compat 13: "
        "it installed nothing).",
        c("systemd-tmpfiles --create remotix.conf") + ": creates the folders and sets the modes (below).",
        "<b>The PAM line of the local-login hook.</b> If " + c("pam-auth-update") + " exists, " + c("pam-auth-update --package")
        + " reads the profile " + c("/usr/share/pam-configs/remotix") + " (" + c("Default: yes") + ", " + c("Priority: -1")
        + ", " + c("Session-Interactive-Only: yes") + ", " + c("Session-Type: Additional") + ", the single line " + c("session optional pam_exec.so quiet "
        "/usr/libexec/remotix/remotix-local-login") + ") and rewrites " + c("/etc/pam.d/common-session") + "; then the script checks that "
        + c("remotix-local-login") + " is in that file. Two cases print a warning on " + c("stderr") + " and do not stop apt: "
        "<i>remotix: ⚠ pam-auth-update not found</i>, and <i>remotix: ⚠ common-session was edited by hand</i> (the line is not in the file after "
        "the step: a local login is then not held and only the periodic check remains). A failure of " + c("pam-auth-update")
        + " itself is said too. The step runs at every " + c("configure") + ", "
        "upgrades included; whether an administrator's deselection of the profile survives an upgrade was not verified. The line is "
        "also checked at every start of the service (below). The check of the step uses a pattern that matches the line itself "
        "(" + c("session … pam_exec.so … remotix-local-login") + "), not a comment that merely names the file.",
        "<b>The encoding test, on the first configuration only</b> (the second argument of the script is empty) and "
        "only if the binary is there: " + c("MESA_SHADER_CACHE_DISABLE=true timeout 30 /usr/libexec/remotix/remotix --encoding-test h264") + " (Mesa then does not open a shader cache in " + sysf("/root/.cache") + " for a probe that runs once). Its "
        "exit status is 0 if the card encodes a test frame, 3 if no card can encode, 1 if it opens and produces "
        "nothing. Any non-zero status prints a two-line warning that REMOTIX will show no desktop until the card "
        "encodes, naming the driver to check (Intel and AMD: " + c("va-driver-all") + "; NVIDIA: its proprietary "
        "driver) and the command to repeat. It does not stop the installation: the VA driver may arrive with a "
        "Recommends configured after REMOTIX itself.",
        "<b>The compositor warning.</b> If " + c("labwc") + " is not installed, and the machine has " + c("xfce4-session") + " or "
        + c("lxqt-session") + " and has neither " + c("gnome-shell") + " nor " + c("startplasma-wayland") + " (so there is no doubt about "
        "which desktop REMOTIX would start), the step prints <i>remotix: ⚠ the package labwc is not installed (it is only a Recommends)</i> "
        "and the command " + c("sudo apt install labwc") + ". It runs at every " + c("configure") + " and never stops apt.",
        "The debhelper part (" + c("#DEBHELPER#") + "): the AppArmor lines of " + c("dh_apparmor") + " (load or reload "
        "the profile " + c("remotix_network") + ") and the systemd lines described in the service policy section. "
        "The service and the user groups are not touched.",
    ]) + \
    p("The encoding test is the product's own mode: " + c("main()") + " answers " + c("--encoding-test") + " before "
      "reading any other option. On an upgrade the test is not repeated.") + \
    p("<b>Checking and switching off the local-login line.</b> To see whether it is in force: "
      + c("grep remotix-local-login /etc/pam.d/common-session") + ". To follow what it does: " + c("journalctl -t remotix | grep 'local login'")
      + " (" + rif("Logging and diagnostics") + "). To switch it off, the standard Debian way is " + c("pam-auth-update")
      + " (untick the REMOTIX entry) or " + c("pam-auth-update --package --remove remotix") + "; <b>this was not tried</b> for this "
      "package, and the effect of switching it off is that a local login of a user who has a remote desktop is no longer held "
      "(the periodic checks of " + rif("Security model") + " remain).") + \
    warn("The " + c("postinst") + " does not enable the firewall profile, does not put the user in any group and does "
         "not enable the service. The only change it makes to a system file is the PAM line above. The comment at its head says "
         "that the groups, the firewall and the belts are set "
         "up by «the engine», which is the old installer; in this package the groups are set up by the product at "
         "each user's first connection (" + rif("Security model") + ") and the rest is the administrator's. The same comment "
         "says that on an upgrade “the desktops stay alive”, which is no longer true: the restart closes them (" + rif("Stopping the service") + ").")

# ── 15.5 Files ───────────────────────────────────────────────────────────
FILES = tree([
    "/usr/libexec/remotix/",
    "├── remotix  # the server, mode 0755: root side, network side, child, PAM helper (one executable)",
    "├── remotix-local-login  # the local-login hook, mode 0755, libc only: run by PAM at a local login",
    "├── remotix-pam-hook  # shell script, mode 0755: puts the hook's PAM line back at every start of the service",
    "└── remotix-polkit-seated  # shell helper of the 40- polkit rule, mode 0755",
    "/usr/share/remotix/",
    "├── page.html  # the page the server sends (lintian override: it is the program, not documentation)",
    "├── remotix.conf  # defaults, read by the unit; not a conffile: an upgrade rewrites it",
    "├── linked.json  # versions of the statically linked ngtcp2 and nghttp3, from pkg-config at build time",
    "└── belts/  # the two switched-off protections",
    "    ├── remotix-power-keys.conf",
    "    └── remotix-no-suspend.conf",
    "/usr/share/polkit-1/rules.d/",
    "├── 40-remotix-remote-sessions.rules",
    "└── 50-remotix-no-poweroff.rules",
    "/usr/share/pam-configs/remotix  # mode 0644, the pam-auth-update profile of the hook; not a conffile",
    "/usr/share/applications/org.kde.remotix.desktop  # KWin's permission to capture the screen",
    "/usr/share/doc/remotix/THIRD-PARTY-LICENSES",
    "/usr/lib/systemd/system/remotix.service  # by dh_installsystemd",
    "/usr/lib/sysusers.d/remotix.conf  # one line: the user remotix",
    "/usr/lib/tmpfiles.d/remotix.conf  # by dh_installtmpfiles from debian/remotix.tmpfiles",
    "/etc/pam.d/remotix  # conffile: the PAM service",
    "/etc/remotix/denied-users  # conffile: contains root",
    "/etc/remotix/remotix.conf.d/  # empty folder for the administrator's drop-ins",
    "/etc/ufw/applications.d/remotix  # conffile: the REMOTIX profile, defined, not opened",
    "/etc/apparmor.d/remotix_network  # conffile: the profile, complain mode",
    "/etc/needrestart/conf.d/remotix.conf  # conffile (debian/remotix.install): needrestart never restarts the service",
], "«TAB» — Where the package puts its files (from " + c("debian/rules") + "; created at run time and not listed: "
   + c("/var/lib/remotix") + ", " + c("/run/remotix") + ", and " + c("/etc/apparmor.d/local/remotix_network")
   + " made by the " + c("dh_apparmor") + " lines of the " + c("postinst") + ")")

S5 = p("Everything is installed by " + c("override_dh_auto_install") + " and " + c("execute_after_dh_auto_install")
       + " in " + c("debian/rules") + ", plus what debhelper adds by itself.", lead=True) + FILES + \
    ul([
        "<b>Conffiles.</b> debhelper marks everything under " + c("/etc") + " as a conffile, so dpkg keeps the "
        "administrator's edits on upgrade and on removal, and deletes the files on purge. This holds for the PAM "
        "file, the denied list, the ufw profile and the AppArmor profile; the comment in " + c("debian/rules")
        + " says so for the first two. " + c("remotix.conf") + " in " + c("/usr/share/remotix") + " is not one: "
        "choices go in " + c("/etc/remotix/remotix.conf.d/*.conf") + ", with the same lines, and win.",
        "<b>The page certificate is not in the package.</b> The server makes its own certificates at start-up in "
        + c("/var/lib/remotix/net/certificates") + " (" + c("certificates_prepare()") + "); an administrator's own, "
        "put there without the " + c(".ours") + " mark, is used instead.",
        "<b>The needrestart file</b> (" + c("debian/needrestart/remotix.conf") + ", copied by " + c("debian/remotix.install") + ") holds the single line "
        + c("$nrconf{override_rc}{qr(^remotix\\.service$)} = 0;") + ". A restart of REMOTIX closes every remote desktop, and " + c("needrestart")
        + " (run by an automatic update, or with " + c("-r a") + ") would restart it without asking after any update of a library it uses; "
        "with the line the service is only listed under the services to restart by hand, and the administrator restarts it when no remote desktop is open "
        "(the old library stays loaded until then). It is a conffile, so an administrator's edit survives an upgrade. On a machine without "
        + c("needrestart") + " the folder " + sysf("/etc/needrestart/conf.d") + " is created by the package and the file does nothing. "
        "That the line has this effect on Debian was <b>not observed</b>.",
        "<b>The KDE file</b> " + c("org.kde.remotix.desktop") + " has " + c("Exec=/usr/libexec/remotix/remotix") + ", "
        + c("NoDisplay=true") + " and " + c("X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1") + ". The package "
        "ships it and the program only checks it at start-up (" + c("kwin_check_permission()") + "); it never writes it.",
        "<b>The two polkit files and the helper</b> are active as soon as they are installed (the 40- rule has a fourth refresh action, "
        + c("org.freedesktop.fwupd.refresh-remote") + ", which gnome-software asks at login; fwupd 2.0.20 of Debian 13 has no such action, so on Debian 13 the line has no effect yet); the two files under "
        + c("belts/") + " are not (" + rif("Security model") + ").",
        "<b>The unit comes from debhelper.</b> " + c("dh_installsystemd") + " picks " + c("debian/remotix.service") + " and "
        "installs it under " + c("/usr/lib/systemd/system/") + "; " + c("rules") + " has no line for it.",
        "<b>No benchmark file and no bench option are in the package.</b> The build refuses to package if "
        + c("BENCH_ON") + " in " + c("rcp.c") + " is not 0, and its checks on the finished package assert that the unit "
        "passes no bench option and that no bench file is in the file list (" + rif("Build and release") + "). "
        "That does not remove " + c("--command-socket") + " from the binary; see " + rif("Login and its defences") + ".",
    ]) + \
    p("<b>Folders created at run time.</b> " + c("remotix.tmpfiles") + " (installed as " + c("/usr/lib/tmpfiles.d/remotix.conf")
      + ") makes " + c("/var/lib/remotix") + " (0755, root), " + c("/var/lib/remotix/net") + " (0700, " + c("remotix")
      + ") and its content owned by " + c("remotix") + " at every boot, fixes the modes of the certificates folder "
      "(0700), the keys, " + c("quic-secret") + ", " + c("log-secret") + " and the ban file (0600), and makes "
      + c("/run/remotix") + " (0755, root) and " + c("/run/remotix/net") + " (0700, " + c("remotix") + "). The "
      "file is installed and run by the " + c("postinst")
      + ", and " + c("check-package.py") + " (first-start) checks the owners and modes it produces. One more folder is not made "
      "by tmpfiles: " + c("/run/remotix/prelocal/") + " (root, 0700) is made by the root side when it starts, for the requests of "
      "the local-login hook (" + rif("The local-login hold") + "); it goes with " + c("/run/remotix") + " at a purge.") + \
    p("<b>The system user.</b> " + c("remotix.sysusers") + " is the single line " + c("u remotix - \"REMOTIX network side\" / /usr/sbin/nologin")
      + ": a system user, automatic id, home " + c("/") + ", shell " + c("nologin") + ", no groups, because it never "
      "opens a card. The user is the one the unit's network side drops to (" + c("--network-user") + " defaults to it).") + \
    p("<b>The firewall profile.</b> " + c("remotix.ufw") + " defines the application " + c("REMOTIX") + " with "
      + c("ports=7447/tcp|7447/udp") + " (TCP for the page, UDP for QUIC). The package does not run " + c("ufw allow")
      + ": defining is not opening. An administrator who uses ufw runs " + c("ufw allow REMOTIX") + ".") + \
    note("The unit starts the server with " + c("--address 0.0.0.0") + ": once enabled it listens on every address, TCP "
         "for the page and UDP for QUIC. The port is the variable " + c("REMOTIX_PORT") + " (7447) in "
         + c("/usr/share/remotix/remotix.conf") + "; changing it in a drop-in does not change the ufw profile, "
         "which names 7447.", "Port and profile.")

# ── 15.6 prerm and postrm ────────────────────────────────────────────────
S6 = p("Removal has two scripts and two outcomes. " + c("apt remove") + " keeps the configuration and the state; "
       + c("apt purge") + " also removes what the program created by itself. A purge of an installed package runs the "
       + c("prerm") + " with the argument " + c("remove") + " first, so the closing work lives in one place.",
       lead=True) + \
    p("<b>" + c("prerm") + " (only on " + c("remove") + "; on an upgrade it closes no session itself, but the "
      "restart of the service that the " + c("postinst") + " does if it was running closes them, see the last section).</b> The order matters and each step was added "
      "deliberately (the closing of the sessions before the stop, after a measurement on 17 Nov 2026):") + \
    ul([
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
        "<b>Take the PAM line out, now that the service is down.</b> " + c("pam-auth-update --package --remove remotix") + " (if " + c("pam-auth-update")
        + " exists) removes the local-login line from " + c("/etc/pam.d/common-session") + " while the profile file is still in place. It is done only after "
        "the stop because the " + c("ExecStartPre") + " of the unit would put the line back if the service restarted in between. A failure is said "
        "(<i>remotix: ⚠ pam-auth-update --remove remotix failed: check /etc/pam.d/common-session</i>) and does not stop dpkg. A purge passes here too, "
        "because it runs the " + c("prerm") + " with " + c("remove") + " first.",
        "<b>Sweep again</b> for what the stop left in an abandoned scope, then, for each person who had a REMOTIX "
        "session and has no other graphical session (a non-REMOTIX session of type x11, wayland or mir), stop " + c("graphical-session.target") + " in "
        "that user's manager.",
        "<b>Undo the group enrolments</b> recorded in " + c("/var/lib/remotix/group-enrollments.jsonl") + " with "
        + c("gpasswd -d") + ", only if the record is a regular file, not a link, owned by root, and after checking "
        "that the names contain nothing but " + c("A-Za-z0-9._-") + ".",
        "<b>Take back the card ACLs</b> by running " + c("remotix --drop-render-grants") + ", with the service stopped and "
        "before the record and the binary go. If it fails, a warning is printed and " + c("/run/remotix/render-grants-kept")
        + " is left as a marker so the " + c("postrm") + " keeps the record.",
    ]) + \
    p("<b>" + c("postrm") + ".</b> On " + c("remove") + ", " + c("upgrade") + " and the abort cases it does nothing except "
      "the AppArmor step below. On " + c("purge") + ":") + \
    ul([
        "removes " + c("/var/lib/remotix/net") + ", " + c("/var/lib/remotix/certificates") + ", " + c("/var/lib/remotix/ban")
        + ", " + c("ban.new") + " and " + c("/run/remotix") + "; removes " + c("render-grants") + " unless the marker says "
        "the ACLs could not all be taken back (then it keeps it and says so);",
        "for each account with a folder " + c("~/.local/state/remotix") + ", removes the product's files there "
        "by name (" + c("session.log") + ", " + c("xfce-chiavi") + ", " + c("xfce-vecchi-ripristinati") + ", "
        + c("lxqt-restored") + ", " + c("gnome-ripristinato") + ") and the folder if it is left empty, <b>as that "
        "user</b> through " + c("runuser") + ", so that a link planted in a home cannot make root delete something "
        "else. Never " + c("rm -rf") + " of a folder in a home. If the product writes another file there its name "
        "must be added to the list;",
        "deletes the user " + c("remotix") + " and its group, unless " + c("net-user-preexisting") + " exists and only "
        "if its uid is between 1 and 999;",
        "removes " + c("net-user-preexisting") + " and " + c("group-enrollments.jsonl") + ", and the folder "
        + c("/var/lib/remotix") + " if it is empty.",
    ]) + \
    p("On " + c("remove") + ", " + c("purge") + " and " + c("disappear") + ", it also writes the profile name to "
      + c("/sys/kernel/security/apparmor/.remove") + " if that file is writable, so the profile leaves the kernel even "
      "if its file is already gone. The " + c("lintian") + " override in " + c("debian/remotix.lintian-overrides")
      + " explains why the " + c("prerm") + " calls " + c("systemctl") + " itself: a desktop that ignores SIGTERM is "
      "killed through its own session scope, a transient unit that " + c("deb-systemd-invoke") + " cannot address.") + \
    p("<b>Verification.</b> " + c("PIANO.md") + " records, for 17 Nov 2026, installation, restart, removal and purge on a "
      "real Debian 13 virtual machine with no residue, and " + c("check-package.py") + " «8/8» on the four desktops. "
      "Its checks are named install, first-start, apparmor, remove, purge, reinstall, preinst, recommends and "
      "fresh-end, and it compares snapshots of " + c("/etc") + ", " + c("/usr") + ", " + c("/var/lib") + " and "
      + c("/run") + ", of users, groups and unit files, before and after. The AppArmor check is BLOCKED in "
      "containers, which have no AppArmor interface.")

# ── 15.7 Service policy ──────────────────────────────────────────────────
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
    p("<b>Two lines of the unit.</b> " + c("ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check") + ": at every start the script looks for the "
      "hook's line in " + c("/etc/pam.d/common-session") + " and, if it is missing (an update, a hand edit), puts it back with " + c("pam-auth-update --package")
      + " and writes one line in the service's log saying what it found; the " + c("-") + " means a failure never prevents the start, and the script never uses "
      + c("--force") + " or " + c("--enable") + ", so a file edited by hand or a profile switched off in " + c("pam-auth-update") + " stay as they are (the line then "
      "says the hook is not in place). And " + c("Environment=MESA_SHADER_CACHE_DISABLE=true") + ": the codec probe of the root side would otherwise make Mesa "
      "open a shader cache in " + sysf("/root/.cache") + "; the users' desktops get their environment from PAM and keep their cache.") + \
    p("<b>Reinstalling.</b> The messages that tell the administrator to reinstall (the KDE permission file, a missing PAM file) give the command for a " + c(".deb") + ": "
      + c("sudo apt install --reinstall ./remotix_<version>_amd64.deb") + ". A reinstall runs the scripts as an upgrade does: the service is restarted if it was running, "
      "and the encoding test of the " + c("postinst") + " is not repeated.") + \
    p("The rule comes from point 1 of decision §10.12 of " + c("DECISIONS.md") + " (the package switches nothing on; "
      "the rest of that decision is about the old installer) and is stated in the repository's " + c("CLAUDE.md")
      + ": the service is installed disabled and not started, and the administrator enables it. The unit uses the "
      "machine's name (" + c("%H") + ") for the certificate; an administrator who connects by IP address puts "
      + c("REMOTIX_OPTIONS=--name 192.0.2.10") + " in a drop-in under " + c("/etc/remotix/remotix.conf.d/")
      + " (the last " + c("--name") + " wins). The runtime life cycle of the service is in "
      + rif("Startup and life cycle") + ".")

CHAPTER = ("The package", [
    ("What the package is and how it is built", S1),
    ("Package metadata: Depends and Recommends", S2),
    ("The preinst refusals", S3),
    ("The postinst: user, folders and encoding test", S4),
    ("Files the package installs", S5),
    ("Removal: prerm, postrm and purge", S6),
    ("Service policy: installed disabled", S7),
])
