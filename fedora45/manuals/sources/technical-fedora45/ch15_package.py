from build import c, code, h4, note, p, rif, sysf, table, tree, ul, warn

# ── 15.1 What the package is ─────────────────────────────────────────────
S1 = p("REMOTIX for Fedora 45 is one binary package, " + c("remotix") + ", built from the spec file " + c("rpm/remotix.spec")
       + " and the files beside it in " + c("rpm/") + ". It is installed with " + c("sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm")
       + " and removed with " + c("sudo dnf remove remotix") + "; there is no installer program. The file name is the " + c("Version")
       + " (1.2.0) and the " + c("Release") + " (" + c("1%{?dist}") + ", which is " + c("1.fc45") + " here) of the spec. The "
       "build itself, on a virtual machine, with the static ngtcp2 and nghttp3, is in " + rif("Build and release")
       + ". The package is " + c("ExclusiveArch: x86_64 aarch64") + ": the binary is compiled for the machine, and the walls of "
       "the network side exist for those two architectures (" + rif("Security model") + "); only x86_64 has been built and run "
       "on Fedora, aarch64 has not been tried. The version in the spec is the one the manuals print on their cover (" + rif("Version and release") + ").",
       lead=True) + \
    p("The package changes the machine as little as possible, and says so in its scriptlets (the RPM name for maintainer scripts: "
      + c("%pre") + ", " + c("%post") + ", " + c("%preun") + ", " + c("%postun") + " and the triggers). It creates one system user and a "
      "few folders, defines a firewalld service without opening it, installs two polkit rules, loads its own SELinux module and puts one "
      "PAM line into the stacks of the login screens, and leaves the service disabled and stopped. The PAM line is the one change to a "
      "file of another package: " + c("pam_exec.so quiet /usr/libexec/remotix/remotix-local-login") + " goes into the PAM files of "
      + c("gdm") + ", " + c("plasmalogin") + ", " + c("lightdm") + " and " + c("sddm") + ", by the script " + c("remotix-pam-hook")
      + ", and it is taken away when the package is removed (" + rif("The local-login hook on four login screens") + "). Two optional "
      "system-wide protections (the power keys and suspend) are shipped switched off. Three things are specific to this package and "
      "not to a plain server program: the SELinux module (" + rif("The SELinux module") + "), a system dconf database that the "
      + c("%post") + " compiles (" + rif("The postinst: user, folders and encoding test") + "), and a drop-in that tells "
      + c("needrestart") + " never to restart the service by itself (" + rif("Service policy: installed disabled") + "). The sections "
      "below follow the life of the package: what it needs, what it refuses, what it does after unpacking, what it installs, how "
      "SELinux, PAM and the login screens are handled, what it does on removal, and what the service policy is.") + \
    p("The package does <b>not</b> carry a compositor of its own. On Ubuntu the package builds a patched labwc for KDE; on Fedora KDE "
      "runs on KWin alone (" + rif("KDE with KWin alone") + "), and the labwc that XFCE and LXQt use is the one of Fedora's repositories.") + \
    note("Some comments in the files of the package were inherited and are no longer true. The unit " + c("rpm/remotix.service")
         + " (the comment before " + c("KillMode") + ": «the desktops … survive the stop»), the comment at the head of " + c("%post")
         + " in " + c("rpm/remotix.spec") + " («the desktops stay alive» on an upgrade) and the first line of " + c("rpm/remotix.tmpfiles")
         + " («created by postinst») still speak as before the decision of 17 Nov 2026 (" + c("DECISIONS-11") + " §11.56) that an "
         "orderly stop closes the desktops. They are comments, not behaviour: the manual follows the behaviour (" + rif("Stopping the service")
         + "). They are listed in " + rif("Appendix C — Known issues and open points") + ".", "Stale wording.")

# ── 15.2 Depends and Recommends ──────────────────────────────────────────
S2 = p("RPM finds by itself the libraries linked into the binary, so the " + c("Requires") + " lines name only what the program uses at "
       "run time through PAM, D-Bus and commands, and that rpm cannot see. The " + c("Recommends") + " are weak dependencies: "
       + c("dnf") + " installs them by default and the administrator can leave them out with " + c("--setopt=install_weak_deps=False") + ".",
       lead=True) + \
    table(["Field", "Package", "Why it is there"], [
        [c("Requires"), c("pam"), "The PAM library and the stack files that " + sysf("/etc/pam.d/remotix") + " includes (" + rif("The PAM service file on Fedora") + ")."],
        [c("Requires"), c("systemd-pam"), "Provides " + c("pam_systemd") + ", the module in " + c("password-auth")
         + " that makes the user's logind session be born when the child calls " + c("pam_open_session()") + "."],
        [c("Requires"), c("shadow-utils"), c("usermod") + " and " + c("gpasswd") + ": the enrolment in the card's groups at a user's first connection, "
         "and its undoing at removal; " + c("userdel") + " at removal. Also required by the scriptlets."],
        [c("Requires"), c("gawk"), "Used by " + c("%preun") + " to read the list of logind sessions."],
        [c("Requires"), c("systemd"), c("loginctl") + ", " + c("systemctl") + " (including " + c("--user") + "), " + c("systemd-sysusers") + ", "
         + c("systemd-tmpfiles") + ", the unit itself."],
        [c("Requires"), c("dbus-broker"), "The user's systemd bus, on which the child finds the compositor and the desktop's services "
         "(the Fedora counterpart of Ubuntu's " + c("dbus-user-session") + ")."],
        [c("Requires"), c("pipewire") + ", " + c("wireplumber"), "The daemon: GNOME and KDE video capture and the audio of every desktop go through "
         "PipeWire. rpm sees the library, not the daemon, and a minimal installation does not have it."],
        [c("Requires"), c("firewalld-filesystem"), "Owns the folder of the firewalld service definitions and the macro that reloads firewalld (" + c("%firewalld_reload") + ")."],
        [c("Requires(post/preun/postun)"), c("systemd") + " (post, preun, postun), " + c("shadow-utils") + " (preun, postun), " + c("util-linux-core") + " (postun only)", "The scriptlets run " + c("systemctl") + ", "
         + c("gpasswd") + ", " + c("userdel") + " and " + c("runuser") + " (the last, in " + c("%postun") + ", to clean the users' homes as the user)."],
        [c("Recommends"), c("labwc") + ", " + c("wlr-randr") + ", " + c("xorg-x11-server-Xwayland"), "The compositor REMOTIX starts for XFCE and LXQt, with the "
         "output-size tool and Xwayland that XFCE under labwc needs. They are installed also on a GNOME-only or KDE-only machine, because package "
         "metadata cannot say «only if XFCE is there». KDE does <b>not</b> use labwc (" + rif("KDE with KWin alone") + ")."],
        [c("Recommends"), c("dconf"), "The " + c("%post") + " compiles the system dconf database " + sysf("/etc/dconf/db/remotix")
         + " with " + c("dconf compile") + ", and the service compiles it again at start-up if it is missing or different. Without the "
         + c("dconf") + " program neither the database nor the locks can be made (the session code uses the same command for its own fallback, " + c("dconf_compile_locks()")
         + "): no lock is in force, the session's profile has only the in-memory database on top of the user's, and what the user changes from remote is "
         "not kept at the next birth; the server says " + c("DECLARED FALLBACK, D-015: `dconf compile` is missing or failed") + " (" + rif("The postinst: user, folders and encoding test") + ")."],
        [c("Recommends"), c("dejavu-sans-fonts"), "labwc dies without a scalable font."],
    ], "«TAB» — Dependencies of " + c("remotix") + " (" + c("rpm/remotix.spec") + ")") + \
    h4("The video drivers are not a dependency") + \
    p("REMOTIX encodes only on the video card, and on Fedora the H.264 driver is not in the base repositories: Fedora's Mesa is built without H.264 and "
      "HEVC. Decision D1 of the Fedora plan is that the codecs are a <b>requirement the administrator meets</b>, not a dependency of the package: "
      "enable RPM Fusion (free) and install " + c("mesa-va-drivers-freeworld") + " (NVIDIA: its proprietary driver). That is why no "
      + c("va-driver-all") + " or " + c("mesa-vulkan-drivers") + " appears in the table, and why the " + c("%post") + " tests a frame at the first installation and says so if "
      "the card does not encode (" + rif("The postinst: user, folders and encoding test") + "). The bench's virtual machines start from a snapshot "
      "that already has the RPM Fusion codecs (" + rif("The VM bench") + ").") + \
    ul([
        "<b>No desktop is a dependency.</b> The package never installs a desktop by itself; with none of the four present the server says so at "
        "start-up. The session criterion lives in " + c("session.c") + ".",
        "<b>Whoever installs with " + c("--setopt=install_weak_deps=False") + " loses</b> the compositor and the dconf program, and an XFCE or LXQt "
        "desktop will not start. The server refuses the login of an XFCE or LXQt machine without " + c("labwc") + " with the code 0x0E and a line that "
        "names the package (" + rif("The startup declarations") + "); the " + c("%post") + " also warns, but only on a machine with neither "
        + c("gnome-shell") + " nor " + c("startplasma-wayland") + ". Whether that warning fired on the Fedora virtual machines of the bench "
        "was not recorded. On Fedora the XFCE and LXQt spins do not carry " + c("gnome-shell") + ", so the warning is the normal signal there.",
        "<b>Bundled libraries.</b> " + c("Provides: bundled(ngtcp2) = 1.25.0") + " and " + c("bundled(nghttp3) = 1.18.0") + " say which libraries are linked "
        "statically into the binary; it is Fedora's way of recording what Debian calls " + c("Static-Built-Using") + ". The build "
        "refuses (" + c("test") + " lines in " + c("%build") + ") if " + c("pkg-config") + " reports another version of either, so that the declaration never lies; "
        "the versions are also written to " + sysf("/usr/share/remotix/linked.json") + " for a software bill of materials. labwc and wlroots are no longer "
        "linked statically into anything: they are Fedora's own packages.",
        "<b>BuildRequires</b> carry the development headers the product links: " + c("openssl-devel") + " (Fedora's OpenSSL, version 4.0 at the time of "
        "the work; there is no fallback to an " + c("openssl3") + " package, decision D8; the minimum 3.5.0 stays in the Makefile), " + c("pam-devel")
        + ", " + c("libselinux-devel") + " (new on Fedora), " + c("glib2-devel >= 2.80") + ", " + c("pipewire-devel") + ", " + c("libdrm-devel") + ", "
        + c("libva-devel") + ", " + c("opus-devel") + ", " + c("zlib-devel") + ", " + c("libei-devel >= 1.3.901") + ", " + c("libxkbcommon-devel") + ", "
        + c("mesa-libgbm-devel") + ", " + c("wayland-devel") + ", " + c("vulkan-headers") + ", " + c("vulkan-loader-devel") + ", the tools "
        + c("gcc") + ", " + c("make") + ", " + c("pkgconf-pkg-config") + ", " + c("bzip2") + ", " + c("systemd-rpm-macros") + ", " + c("firewalld-filesystem")
        + " and " + c("%{?selinux_requires}") + ". There is no ffmpeg: encoding is on the card through libva and Vulkan Video, and audio through libopus.",
        "<b>No " + c("universe") + " and no component to check:</b> everything the package needs, except the codecs above, is in Fedora's base repositories.",
    ]) + \
    p("What " + c("dnf") + " really pulled in on the four virtual machines of the bench was not recorded for this manual: " + c("server/live-installa.sh")
      + " installs the package and the RPM Fusion codecs, but the transaction lists were not read.")

# ── 15.3 %pre ────────────────────────────────────────────────────────────
S3 = p("The " + c("%pre") + " scriptlet (the counterpart of Debian's preinst, and the section keeps the old name for the links that point to it) runs "
       "before the files are unpacked and has two refusals, each of which stops the installation with a message on " + c("stderr")
       + " and exit status 1. In it " + c("$1") + " is 1 for a first installation and 2 for an upgrade.", lead=True) + \
    table(["Refusal", "When", "Test", "Why"], [
        ["No video card", "Only on a new installation (" + c("$1 -eq 1") + "), never on upgrade",
         "No entry " + c("/sys/class/drm/renderD*") + " exists. That is the kernel's own list of DRM render nodes, so "
         "it does not depend on packages not yet unpacked.",
         "REMOTIX encodes only on the card; with no render node nothing can ever be shown. An installed REMOTIX is "
         "never broken by an upgrade."],
        ["An account named " + c("remotix") + " that belongs to a person", c("install") + " and " + c("upgrade"),
         "The account exists and any of: uid 0 or gid 0; uid in [" + c("UID_MIN") + " from " + sysf("/etc/login.defs")
         + " (1000 if absent), 60000); a login shell (anything that is not empty, " + c("*/nologin") + " or "
         + c("*/false") + "); a home under " + sysf("/home") + ", " + sysf("/root") + " or " + sysf("/var/home") + ".",
         "The network side runs as that account, and the sysusers file only creates the user when it is missing. "
         "The message tells the administrator to rename it (" + c("usermod -l") + ") or remove it."],
    ], "«TAB» — What the " + c("%pre") + " refuses") + \
    p("Besides refusing, the " + c("%pre") + " remembers: on a first installation where an account " + c("remotix") + " already exists but is not a "
      "person's, and " + sysf("/usr/lib/sysusers.d/remotix.conf") + " is not yet there, it writes " + sysf("/var/lib/remotix/net-user-preexisting")
      + ". The " + c("%postun") + " reads that file so that a removal never deletes an account REMOTIX did not create.") + \
    p("<b>Why the spec switches off the automatic sysusers.</b> RPM 6 turns the files in " + sysf("/usr/lib/sysusers.d") + " into " + c("user()") + "/" + c("group()")
      + " provides and creates the account <i>before</i> the package's own " + c("%pre") + ". The package needs to see whether an account named "
      + c("remotix") + " was on the machine before it, so the spec sets " + c("%global __sysusers_path ^$") + " to switch the automation off and "
      "runs " + c("systemd-sysusers") + " itself in " + c("%post") + ".") + \
    p("The last line of the " + c("%pre") + " is " + c("%selinux_relabel_pre -s targeted") + ", after the refusals, so that an installation refused above leaves nothing "
      "behind in " + sysf("/var/lib/rpm-state") + ".") + \
    p("What the " + c("%pre") + " does not check: that the card can encode. A card that exists but cannot encode H.264 is said by the " + c("%post")
      + " and by the server at start-up. A virtual machine that has only the emulated " + c("virtio-vga") + " card passes the check (it gives a render node) "
      "and cannot encode; the server then says " + c("THIS SERVER CANNOT ENCODE VIDEO") + " (" + rif("The startup declarations") + ").") + \
    p("Verification on Fedora: " + c("prove/check-package.py") + " was inherited from Ubuntu and still speaks of apt and dpkg, so it was not used "
      "(" + rif("The package check") + "). The refusal of a person's account and the refusal without a card were not tried on Fedora; the installations "
      "of the bench were all on machines with a render node.")

# ── 15.4 %post ───────────────────────────────────────────────────────────
S4 = p("The " + c("%post") + " does, in this order, and never lets a failure make " + c("dnf") + " fail (each failure is a warning on "
       + c("stderr") + "):", lead=True) + \
    ul([
        c("%selinux_modules_install -s targeted /usr/share/selinux/packages/remotix.pp.bz2") + " and " + c("%selinux_relabel_post -s targeted")
        + ": the module is loaded and the files get their types (" + rif("The SELinux module") + "). The macros never fail; so the script itself checks, "
        "if SELinux is enabled, that " + c("semodule -l") + " lists the module, and if not it says <i>the SELinux module «remotix» is NOT loaded</i> with the "
        "command to try by hand: " + c("sudo semodule -X 200 -i /usr/share/selinux/packages/remotix.pp.bz2") + ". It is a warning, never a failure.",
        c("systemd-sysusers remotix.conf") + ": creates the system user " + c("remotix") + " (and its group) from "
        + sysf("/usr/lib/sysusers.d/remotix.conf") + ". It is run explicitly because the automatic creation is switched off (previous section).",
        c("systemd-tmpfiles --create remotix.conf") + ": creates the folders and sets the modes (below).",
        "<b>The system dconf database.</b> If the " + c("dconf") + " command exists and the folder "
        + sysf("/usr/share/remotix/dconf/remotix.d") + " is there, it runs " + c("dconf compile") + " into a temporary file "
        + sysf("/etc/dconf/db/remotix.new.$$") + ", sets mode 0644 and renames it over " + sysf("/etc/dconf/db/remotix") + ": "
        "programs of a living session may have the old file open, so it is replaced, never rewritten in place. The keyfiles are the "
        "package's own, made at install time from the binary just built (" + c("%install") + ", " + c("remotix --dconf-keyfiles") + ", the section on the instruments in "
        + rif("Logging and diagnostics") + "); they hold the value and the lock of 24 keys of the GNOME session (the twelve " + c("VT") + " switches, Log Out kept, no user switching, no lock, "
        "no automatic suspend, the integer scale 1, and three keyboard-layout keys that are only locked). Two warnings on "
        + c("stderr") + ": <i>remotix: ⚠ dconf not found: /etc/dconf/db/remotix not made; the GNOME remote session "
        "will use its fallback</i> and <i>remotix: ⚠ /etc/dconf/db/remotix could not be compiled…</i>. "
        "<b>The service does the same work at every start, but not in the same way.</b> On Fedora the root side compiles into "
        + sysf("/run/remotix/dconf-compile.tmp") + " (a file of a type of the package's own) and creates in " + sysf("/etc/dconf/db")
        + " only two fixed names, " + c("remotix.new") + " and then " + c("remotix") + ", which the SELinux module lets it create by name with the type "
        + c("remotix_dconf_db_t") + " (" + c("session_dconf_system_db_ensure()") + ", register of problems F24). It replaces the database only if the bytes differ or the "
        "file is missing, saying so with a line of area " + c("rootside") + " (" + rif("The startup declarations") + "). "
        "This is why a failed or skipped step here is not fatal: " + c("dconf") + " is only a Recommends, and may arrive after REMOTIX.",
        c("restorecon -R /var/lib/remotix /run/remotix /etc/dconf/db/remotix") + ": the files the package does not ship but the service or this scriptlet makes "
        "(tmpfiles, the dconf compile) get their types from the module's file contexts. An upgrade from a package without the SELinux module finds them labelled "
        + c("var_lib_t") + ", " + c("var_run_t") + " and " + c("etc_t") + "; this line corrects it. It never fails the installation.",
        "<b>The PAM line of the local-login hook.</b> " + c("/usr/libexec/remotix/remotix-pam-hook apply") + " puts the line into the PAM stacks of the login screens "
        "that are installed (" + rif("The local-login hook on four login screens") + "). If it cannot do it completely, the scriptlet prints <i>remotix: ⚠ the hook of the local login could not be fully applied</i> "
        "and goes on. The step runs at every " + c("%post") + ", upgrades included; the service also runs it, as " + c("check") + ", before every start "
        "(" + c("ExecStartPre=-…/remotix-pam-hook check") + " in the unit). To see whether the line is in force: " + c("grep -l remotix-local-login /etc/pam.d/*") + ".",
        "<b>The encoding test, on the first installation only</b> (" + c("$1 -eq 1") + ") and only if the binary is there: "
        + c("timeout 30 /usr/libexec/remotix/remotix --encoding-test h264") + ". Its exit status is 0 if the card encodes a test frame, 3 if no card can encode, 1 "
        "if it opens and produces nothing. Any non-zero status prints a three-line warning that REMOTIX will show no desktop until the card encodes: on Fedora the H.264 "
        "driver is not in the base repositories, so enable RPM Fusion (free) and install " + c("mesa-va-drivers-freeworld") + " (NVIDIA: its proprietary driver), then repeat "
        + c("sudo /usr/libexec/remotix/remotix --encoding-test h264") + ". It does not stop the installation.",
        "<b>The missing compositor.</b> If " + c("labwc") + " is not on the PATH, and " + c("xfce4-session") + " or " + c("lxqt-session") + " is, and neither " + c("gnome-shell")
        + " nor " + c("startplasma-wayland") + " is, the script says <i>remotix: ⚠ the package labwc is not installed (it is only a weak dependency): the XFCE/LXQt desktop of this machine cannot start in REMOTIX</i> "
        "and, on a second line, <i>install it: sudo dnf install labwc</i>. The test is deliberately narrow: where another desktop is present nobody can know which one REMOTIX will start.",
        c("%firewalld_reload") + ": firewalld learns the new service definition. Without the reload the running firewalld answered <i>INVALID_SERVICE</i> to "
        + c("firewall-cmd --permanent --add-service=remotix") + " right after the installation (register F17, F20). It opens <b>nothing</b>; a reload also forgets rules that were added at run time only.",
        c("%systemd_post remotix.service") + ": the macro of Fedora's packages that applies the preset. The preset of Fedora is " + c("disable *") + ", so the service stays disabled.",
    ]) + \
    p("The encoding test is the product's own mode: " + c("main()") + " answers " + c("--encoding-test") + " before reading any other option. On an upgrade the test is not repeated.") + \
    p("<b>Switching off the local-login line.</b> There is no menu for it, as " + c("pam-auth-update") + " is on Debian and Ubuntu. The script " + c("remotix-pam-hook remove") + " takes it away "
      "from the stacks; that it is a procedure for the administrator was <b>not tried</b>, and the service puts the line back at its next start. The effect of switching it off is that a local login of "
      "a user who has a remote desktop is no longer held (the periodic checks of " + rif("Security model") + " remain). To follow what the hook does: "
      + c("journalctl -t remotix | grep 'local login'") + " (" + rif("Logging and diagnostics") + ").") + \
    warn("The " + c("%post") + " does not open the firewall, does not put the user in any group and does not enable the service. The changes it makes to files of other "
         "packages are the PAM line above; the dconf database is a file the package owns outside its file list, and the " + c("%postun") + " removes it. The groups are set up by the product "
         "at each user's first connection (" + rif("Security model") + ") and the rest is the administrator's. The comment at the head of the scriptlet says that on an upgrade "
         "“the desktops stay alive”, which is no longer true: the restart closes them (" + rif("Stopping the service") + ").")

# ── 15.5 Files ───────────────────────────────────────────────────────────
FILES = tree([
    "/usr/libexec/remotix/",
    "├── remotix  # the server, mode 0755: root side, network side, child, PAM helper (one executable)",
    "├── remotix-local-login  # the local-login hook, mode 0755, libc only: run by PAM at a local login",
    "├── remotix-polkit-seated  # shell helper of the 40- polkit rule, mode 0755",
    "└── remotix-pam-hook  # shell script that puts the hook's line into the PAM stacks of the login screens, mode 0755",
    "/usr/share/remotix/",
    "├── page.html  # the page the server sends",
    "├── remotix.conf  # defaults, read by the unit; not a config file: an upgrade rewrites it",
    "├── linked.json  # versions of the statically linked ngtcp2 and nghttp3, from pkg-config at build time",
    "├── dconf/remotix.d/  # keyfiles of the GNOME session's rules, made at install time by remotix --dconf-keyfiles",
    "│   ├── 00-remotix  # the values",
    "│   └── locks/00-remotix  # the list of locked keys",
    "└── belts/  # the two switched-off protections",
    "    ├── remotix-power-keys.conf",
    "    └── remotix-no-suspend.conf",
    "/usr/share/selinux/packages/remotix.pp.bz2  # the SELinux module, loaded by %post",
    "/usr/share/polkit-1/rules.d/",
    "├── 40-remotix-remote-sessions.rules",
    "└── 50-remotix-no-poweroff.rules",
    "/usr/share/applications/org.kde.remotix.desktop  # KWin's permission to capture the screen",
    "/usr/lib/firewalld/services/remotix.xml  # the firewalld service «remotix»: 7447/tcp and 7447/udp, defined, not opened",
    "/usr/lib/systemd/system/remotix.service",
    "/usr/lib/sysusers.d/remotix.conf  # one line: the user remotix",
    "/usr/lib/tmpfiles.d/remotix.conf  # from rpm/remotix.tmpfiles",
    "/etc/pam.d/remotix  # %config(noreplace): the PAM service",
    "/etc/remotix/denied-users  # %config(noreplace): contains root",
    "/etc/remotix/remotix.conf.d/  # empty folder for the administrator's drop-ins",
    "/etc/needrestart/conf.d/remotix.conf  # %config(noreplace): the service is never restarted by needrestart",
    "/usr/share/licenses/remotix/LICENSE.md  # %license",
    "/usr/share/doc/remotix/THIRD-PARTY-LICENSES  # %doc",
], "«TAB» — Where the package puts its files (from " + c("%install") + " and " + c("%files") + " in " + c("rpm/remotix.spec") + "; created at run time and not listed: "
   + c("/var/lib/remotix") + ", " + c("/run/remotix") + ", " + c("/etc/dconf/db/remotix") + " (the " + c("%post") + " and the service))")

S5 = p("Everything is installed by the " + c("%install") + " section of the spec, and listed in " + c("%files") + ". The number of entries of the finished file "
       "(folders included) is read with " + c("rpm -qlp remotix-1.2.0-1.fc45.x86_64.rpm | wc -l") + "; it was not counted for this manual because the 1.2.0 package had not "
       "been rebuilt when the chapter was written.", lead=True) + FILES + \
    ul([
        "<b>Config files.</b> Three are marked " + c("%config(noreplace)") + ": " + sysf("/etc/remotix/denied-users") + ", " + sysf("/etc/pam.d/remotix") + " and "
        + sysf("/etc/needrestart/conf.d/remotix.conf") + ". An upgrade keeps the administrator's edits (the new text arrives as " + c(".rpmnew") + "); a removal deletes the "
        "unmodified ones, and for a modified one leaves " + c("*.rpmsave") + ", which the " + c("%postun") + " then removes by name (" + rif("Removal: prerm, postrm and purge") + "). "
        + c("remotix.conf") + " in " + sysf("/usr/share/remotix") + " is not one: choices go in " + sysf("/etc/remotix/remotix.conf.d/*.conf") + ", with the same lines, and win.",
        "<b>The page certificate is not in the package.</b> The server makes its own certificates at start-up in "
        + sysf("/var/lib/remotix/net/certificates") + " (" + c("certificates_prepare()") + "); an administrator's own, "
        "put there without the " + c(".ours") + " mark, is used instead.",
        "<b>The KDE file</b> " + c("org.kde.remotix.desktop") + " has " + c("Exec=/usr/libexec/remotix/remotix") + ", "
        + c("NoDisplay=true") + " and " + c("X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1") + ". The package "
        "ships it and the program only checks it at start-up (" + c("kwin_check_permission()") + "); it never writes it.",
        "<b>The two polkit files and the helper</b> are active as soon as they are installed; the two files under "
        + c("belts/") + " are not (" + rif("Security model") + ").",
        "<b>The unit</b> is installed by " + c("%install") + " into " + sysf("/usr/lib/systemd/system/") + ", and the spec has no line that enables it.",
        "<b>The licences.</b> " + c("LICENSE.md") + " is installed as the package's licence and " + c("THIRD-PARTY-LICENSES") + " as documentation. The "
        "licence tag of the spec is " + c("LicenseRef-REMOTIX AND MIT") + ".",
        "<b>No benchmark file and no bench option are in the package.</b> The build refuses to package if "
        + c("BENCH_ON") + " in " + c("rcp.c") + " is not 0, and its check on the finished package asserts that the binary does not carry the bench function (" + rif("Build and release")
        + "). That does not remove " + c("--command-socket") + " from the binary; see " + rif("Login and its defences") + ".",
    ]) + \
    p("<b>Folders created at run time.</b> " + c("remotix.tmpfiles") + " (installed as " + sysf("/usr/lib/tmpfiles.d/remotix.conf")
      + ") makes " + sysf("/var/lib/remotix") + " (0755, root), " + sysf("/var/lib/remotix/net") + " (0700, " + c("remotix")
      + ") and its content owned by " + c("remotix") + " at every boot, fixes the modes of the certificates folder "
      "(0700), the keys, " + c("quic-secret") + ", " + c("log-secret") + " and the ban file (0600), and makes "
      + sysf("/run/remotix") + " (0755, root) and " + sysf("/run/remotix/net") + " (0700, " + c("remotix") + "). The "
      "file is run by the " + c("%post") + " and by systemd at every boot. One more folder is not made "
      "by tmpfiles: " + sysf("/run/remotix/prelocal/") + " (root, 0700) is made by the root side when it starts, for the requests of "
      "the local-login hook (" + rif("The local-login hold") + "); it goes with " + sysf("/run/remotix") + " at removal.") + \
    p("<b>The system user.</b> " + c("remotix.sysusers") + " is the single line " + c("u remotix - \"REMOTIX network side\" / /usr/sbin/nologin")
      + ": a system user, automatic id, home " + sysf("/") + ", shell " + c("nologin") + ", no groups, because it never "
      "opens a card. The user is the one the unit's network side drops to (" + c("--network-user") + " defaults to it). The uid it gets on Fedora was not recorded.") + \
    h4("The firewalld service") + \
    p("The file " + sysf("/usr/lib/firewalld/services/remotix.xml") + " defines the firewalld service " + c("remotix") + " with the ports " + c("7447/tcp") + " (the page) and "
      + c("7447/udp") + " (QUIC). The package does not open it: defining is not opening (decision D5). The administrator opens it, in the default zone, with:") + \
    code("sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload", "bash", "Open the port") + \
    p("For another zone add " + c("--zone=NAME") + ". To close it again: " + c("sudo firewall-cmd --permanent --remove-service=remotix && sudo firewall-cmd --reload")
      + ". The port in the definition is the fixed 7447, like the variable " + c("REMOTIX_PORT") + " in " + sysf("/usr/share/remotix/remotix.conf")
      + ": changing the variable in a drop-in does not change the firewalld service. The commands were tried on the virtual machines " + c("xfce") + " and " + c("lxqt")
      + " (register F20, 22 Nov 2026): with the service added, the page answered from another machine, and the rule survived a reload when added with " + c("--permanent") + ". Fedora has no ufw.") + \
    h4("The two polkit rules") + \
    p("Both are in polkit's vendor folder, so polkit reads them in file-name order together with " + sysf("/etc/polkit-1/rules.d/") + "; an administrator "
      "writes a rule with a lower number there to decide otherwise. " + c("40-remotix-remote-sessions.rules") + " is about actions that a distribution "
      "grants without a password only to a user at a seat: refreshing the software catalogue (" + c("Flatpak.metadata-update") + ", " + c("Flatpak.appstream-update")
      + ", " + c("packagekit.system-sources-refresh") + ", and on Fedora also " + c("org.freedesktop.fwupd.refresh-remote") + ": yes for a REMOTIX user where the seated user gets yes) and, for network control "
      "and system repositories, yes for an administrator of the group " + c("wheel") + " and a silent no for anybody else. The file's own comment still says «the five actions»; "
      "it has six on Fedora: four refresh actions (fwupd added) and two of network control and repositories. A REMOTIX session is recognised by the helper " + c("remotix-polkit-seated") + ", which looks in logind's "
      "state files for a session of the user with the PAM service " + c("remotix") + ". " + c("50-remotix-no-poweroff.rules") + " returns " + c("NO")
      + " for <b>19</b> login1 actions (counted with " + c("grep -c '\"org\\.' src/remotix-no-poweroff.rules") + "): " + c("power-off") + ", " + c("reboot") + ", " + c("halt") + ", " + c("suspend") + " and " + c("hibernate")
      + ", each in the plain form, " + c("-multiple-sessions") + " and " + c("-ignore-inhibit") + " (15 actions), and the four " + c("set-reboot-parameter")
      + ", " + c("set-reboot-to-firmware-setup") + ", " + c("set-reboot-to-boot-loader-menu") + " and " + c("set-reboot-to-boot-loader-entry") + ". The last four are there because in logind's policy each of them <i>implies</i> " + c("reboot")
      + " and defaults to yes for the user at the machine, and polkit grants an implied action even when a rule says no to it. Root is not affected, because logind does not ask polkit of a caller that holds "
      + c("CAP_SYS_BOOT") + ". The checks are in " + rif("The checks of all.sh and what each proves") + " (" + c("power-entries-absent") + ", " + c("power-implied") + ", " + c("power-local-seat") + "); "
      "whether the last two pass on Fedora was not recorded.") + \
    note("The unit starts the server with " + c("--address 0.0.0.0") + ": once enabled it listens on every address, TCP "
         "for the page and UDP for QUIC. The port is the variable " + c("REMOTIX_PORT") + " (7447) in "
         + sysf("/usr/share/remotix/remotix.conf") + "; the firewalld service names 7447.", "Port and firewall.")

# ── The SELinux module ───────────────────────────────────────────────────
S5B = p("Fedora runs SELinux in enforcing mode, and the package ships its own module " + c("remotix") + " (the sources are " + c("selinux/remotix.te") + ", " + c("remotix.fc")
        + " and " + c("remotix.if") + "; the module's version is 1.1.1). It takes the place of the AppArmor profile of Debian and Ubuntu, and it does two jobs: it lets the "
        "server's root side act as a login program, so that the user's desktop is born in the user's own context, and it puts the network side in a room with no doors.",
        lead=True) + \
    table(["Domain", "What it is", "What it may do"], [
        [c("remotix_t"), "The root side of the server: PAM and the birth of the desktops.",
         "A login program, like " + c("sshd") + " or the session worker of " + c("gdm") + ": it asks PAM for the user's context, sets it for the next " + c("exec") + ", and the desktop is born as "
         "a local or an ssh login would be. It is not unconfined: every right it has is written in the " + c("remotix.te") + " with the reason (what stays wide is listed in register F27)."],
        [c("remotix_net_t"), "The network side: QUIC, WebTransport, HTTP/3.",
         "Use the three descriptors it was given; read its few files; write only " + sysf("/var/lib/remotix/net") + " and " + sysf("/run/remotix/net") + "; ask logind on the system bus; "
         "no capability, no " + c("ptrace") + ", and it cannot run any program. It cannot create an IP socket, bind a port or connect anywhere. The root side puts it there "
         "just before its " + c("execve") + " (" + c("walls.c") + ", " + c("selinux_exec_net") + "); the twin of this is the AppArmor profile of the other distributions."],
        [c("remotix_hook_t"), "The hook of the local login, " + c("remotix-local-login") + ".", "It may touch only the requests in " + sysf("/run/remotix/prelocal") + "."],
    ], "«TAB» — The three SELinux domains of REMOTIX") + \
    table(["Path", "Type"], [
        [sysf("/usr/libexec/remotix/remotix"), c("remotix_exec_t")],
        [sysf("/usr/libexec/remotix/remotix-local-login"), c("remotix_hook_exec_t")],
        [sysf("/run/remotix(/.*)?"), c("remotix_var_run_t")],
        [sysf("/run/remotix/prelocal(/.*)?"), c("remotix_prelocal_t")],
        [sysf("/run/remotix/net(/.*)?"), c("remotix_net_run_t")],
        [sysf("/var/lib/remotix(/.*)?"), c("remotix_var_lib_t")],
        [sysf("/var/lib/remotix/net(/.*)?"), c("remotix_net_state_t")],
        [sysf("/etc/dconf/db/remotix") + " and " + sysf("remotix.new"), c("remotix_dconf_db_t")],
    ], "«TAB» — The file contexts of the module (" + c("selinux/remotix.fc") + ")") + \
    ul([
        "<b>Load and removal.</b> The " + c("%post") + " loads the module with " + c("%selinux_modules_install") + " and relabels; the " + c("%postun") + " unloads it with "
        + c("%selinux_modules_uninstall") + " and, on a removal, relabels, and also runs " + c("restorecon -R /var/lib/remotix") + " if the folder is left (so that it does not keep a type that no longer exists). If the module "
        "did not get in, the " + c("%post") + " says so with the command to repeat by hand (" + c("sudo semodule -X 200 -i /usr/share/selinux/packages/remotix.pp.bz2") + "); the service then runs without its own domain.",
        "<b>No port type.</b> A module cannot carry a port definition; it would need " + c("semanage port") + " as an extra dependency, a scriptlet to run before the module is removed, and a manual command for every administrator who picks another port. "
        "The wall would gain nothing: the network side never binds, it receives the sockets already bound by the root side. The root side binds unreserved ports (and the http ones).",
        "<b>No " + c("permissive") + ", no " + c("dontaudit") + " of the package's own, no output of " + c("audit2allow") + ".</b> Every rule has the line that says what it is for.",
        "<b>The service's stop on the login screen.</b> The rule " + c("allow remotix_t xdm_unit_file_t:service { stop status };") + " lets the root side stop the user's units (its last defence when a local login on KDE has to close the "
        "remote desktop by force, " + c("systemctl --user stop plasma-kwin_wayland") + "); without it SELinux refused the stop (three denials with " + c("avc: denied { stop }") + " and " + c("tcontext=xdm_unit_file_t") + ", register F36, 25 Nov 2026). It is the thing to look for if a forced close does nothing on a machine where the module was changed.",
        "<b>Confined SELinux users.</b> For a user mapped to " + c("staff_u") + " or " + c("user_u") + " the desktop is born in " + c("staff_t") + " or " + c("user_t") + ", the context a local graphical login would give, with the session keyring in the same context "
        "(" + c("child.c") + ", register F25). If the context cannot be worked out, the login is refused, never born in the wrong domain (exit codes 44 to 47, " + rif("The startup declarations") + "). Tried on the four desktops "
        "(22 Nov 2026); on XFCE with " + c("staff_u") + " the panel does not start, which is a limit of Fedora 45 and not of REMOTIX (F30). " + c("sysadm_u") + " does not get in, as with ssh and gdm.",
        "<b>Denials that are not ours.</b> Some denials appear on a machine with confined users or other software: " + c("relabelto") + " by the user's systemd, " + c("bwrap") + " in " + c("staff_t") + ", " + c("ssh-agent")
        + " writing the session log on XFCE with a confined user, " + c("gdm-session-worker") + " toward " + c("stratisd_t") + " (F15, never seen in these runs). They are in register F28. To read the denials: " + rif("Diagnostic instruments") + ".",
        "<b>What was proved.</b> The wall was tried in enforcing mode, with no permissive and the stock " + c("dontaudit") + " rules, on the four desktops (register F24, packages of 22 Nov 2026): none of REMOTIX's own denials; and the negative test "
        + c("prove/wall-selinux.sh") + " (run as root with every capability inside the network side's domain, against targets that Unix permissions alone would allow) was repeated and passed 25 checks out of 25 on the four desktops (" + c("PIANO.md") + ", 22 Nov 2026). "
        "Installation, upgrade, removal (also with " + sysf("/var/lib/remotix") + " left over), reinstallation from nothing and a reboot of the virtual machine with the module loaded were tried (F24). One window is known: going up from a package "
        "that has no wall, with the service running, there are two denials once, between the loading of the module and the restart of the service, on " + c("session.pem") + " and " + c("session.key") + "; the service restarts clean.",
        "<b>Not tried:</b> a Fedora kernel without SELinux (the server then says <i>SELinux: …</i> as a note and goes on, like with AppArmor off), and a machine with other policy modules that change the " + c("xdm_t") + " or " + c("unconfined_t") + " rules.",
    ])

# ── The PAM service file on Fedora ───────────────────────────────────────
S5C = p("The file " + sysf("/etc/pam.d/remotix") + " (from " + c("src/remotix.pam") + ") is Fedora's " + sysf("/etc/pam.d/sshd") + ", line by line, with one extra line at the top. The file of Debian and Ubuntu includes "
        + c("common-auth") + " and its friends; those names do not exist on Fedora, where the stacks are " + c("password-auth") + " and " + c("postlogin") + ". REMOTIX is a network access, like ssh, and mirrors the authentication of the system.",
        lead=True) + \
    table(["Phase", "Lines", "Why"], [
        ["auth", c("pam_listfile.so item=user sense=deny file=/etc/remotix/denied-users onerr=fail") + " (" + c("requisite") + "), then " + c("substack password-auth") + " and " + c("include postlogin"),
         "The only difference from sshd: root is refused <i>before</i> the password is asked (in " + c("auth") + ", not in " + c("account") + ", so the answer is the same as for a wrong password). With " + c("onerr=fail") + ", a missing or badly written list refuses everybody, "
         "and PAM's log says so. Whatever the administrator chose with " + c("authselect") + " (sssd, faillock…) holds for REMOTIX as for ssh."],
        ["account", c("pam_sepermit") + ", " + c("pam_nologin") + ", " + c("include password-auth"), "Is the account usable (expired, locked…)? " + c("authentication.c") + " calls " + c("pam_acct_mgmt") + " on purpose."],
        ["session", c("pam_selinux close") + ", " + c("pam_loginuid") + ", " + c("pam_selinux open env_params") + ", " + c("pam_namespace") + ", " + c("pam_keyinit") + ", " + c("pam_motd") + ", " + c("include password-auth") + ", "
         + c("include postlogin") + ", two " + c("pam_env"), "The child calls " + c("pam_open_session") + ", and that makes the user's logind session be born, through " + c("pam_systemd") + " inside " + c("password-auth")
         + ". The first " + c("pam_env") + " reads " + sysf("/etc/environment") + " (Fedora has no such file by default, and the child then uses its own PATH); the second reads " + sysf("/etc/locale.conf") + ", where Fedora keeps the language "
         "(Debian: " + sysf("/etc/default/locale") + "). " + c("user_readenv=1") + " is deliberately absent: the user would choose the PATH of their own session."],
    ], "«TAB» — The PAM service file of Fedora") + \
    ul([
        "<b>No keyring.</b> There is no " + c("pam_gnome_keyring") + ", " + c("pam_oo7") + " or " + c("pam_kwallet") + " (decision D6, as on Debian and Ubuntu): authentication and the opening of the session are two different PAM handles in two "
        "processes, and the password is no longer there when the session opens. The desktop's keyring is therefore not unlocked in a remote session.",
        "<b>If the file is missing,</b> every right password is refused: Linux-PAM falls back to the service " + c("other") + ", which on Fedora is " + c("pam_deny") + ". The symptom is «user or password not correct» for everybody. Two protections in the "
        "program: the server looks for the file at start-up and says so (" + rif("The startup declarations") + "), and the PAM check tells <i>PAM refused</i> from <i>PAM could not judge</i> in the log (" + rif("What never enters the log") + ").",
        "<b>The two " + c("pam_selinux") + " lines work</b> because the server runs in its own domain (" + rif("The SELinux module") + "). Without the module the " + c("exec") + " of the child is refused with an AVC of type " + c("transition") + ".",
    ])

# ── The local-login hook on four login screens ───────────────────────────
S5D = p("A local graphical login closes the user's remote desktop first (" + rif("The local-login hold") + "). The hook that asks for it is the program " + c("remotix-local-login") + ", run by PAM in the "
        + c("session") + " phase of the login screen's stack. On Debian and Ubuntu the line is put into " + c("common-session") + " by " + c("pam-auth-update") + ". On Fedora those files are generated by "
        + c("authselect") + ", a hand edit disappears at the first " + c("authselect apply-changes") + ", and a package must not replace the profile the administrator chose; so nothing generated by authselect is ever touched, and the line is put into the files of "
        "the login screens themselves by " + c("/usr/libexec/remotix/remotix-pam-hook") + " (335 lines of shell).", lead=True) + \
    table(["Login screen", "Used by", "Package", "Where its PAM files are", "What the hook does"], [
        [c("gdm"), "GNOME", c("gdm"), sysf("/usr/lib/pam.d/gdm-*") + " (vendor files)", "Makes " + sysf("/etc/pam.d/<name>") + ": a copy of the current vendor file plus our block, first line a marker that says it is ours."],
        [c("plasmalogin"), "KDE", c("plasma-login-manager"), sysf("/usr/lib/pam.d") + " (vendor files)", "As for gdm."],
        [c("lightdm"), "XFCE", c("lightdm"), sysf("/usr/lib/pam.d") + " (vendor files)", "As for gdm."],
        [c("sddm"), "LXQt", c("sddm"), sysf("/etc/pam.d/sddm") + ", " + c("sddm-autologin") + ", " + c("sddm-greeter") + ": " + c("%config(noreplace)") + " files of the sddm package", "Edits them in place: only our marked block is added or removed."],
    ], "«TAB» — The four login screens and the hook") + \
    ul([
        "<b>The line</b> is " + c("session optional pam_exec.so quiet /usr/libexec/remotix/remotix-local-login") + ", put <b>right after the first " + c("pam_selinux.so close") + " line</b>, that is before " + c("pam_selinux open")
        + ", and not after " + c("pam_systemd") + " as on Debian. Reasons, proved on gdm 51 and plasmalogin of Fedora 45: gdm's worker already puts " + c("XDG_SEAT") + ", " + c("XDG_SESSION_TYPE") + " and " + c("XDG_VTNR")
        + " in the PAM environment before the session stack runs, which is all the hook reads; " + c("pam_selinux open") + " sets the exec context of the <i>next</i> exec, and a " + c("pam_exec") + " line after it would spend that exec on the hook "
        "(AVC " + c("entrypoint") + ", the hook refused, the user's desktop born in the wrong context); and not before " + c("pam_selinux close") + " either, because the stack also runs at logout, and a hook that came first would try to run with the user's context and be refused.",
        "<b>The commands.</b> " + c("remotix-pam-hook apply [dm…]") + " makes sure the line is there (idempotent, a change is said on stderr); " + c("check") + " does the same and prints one summary line; " + c("remove") + " takes it away and leaves every file as it was; "
        + c("prepare") + " is for the triggers of sddm (below). A broken PAM file would shut everybody out, so every file is composed in a temporary file in the same folder, checked (every line has the shape of a PAM line, there is a " + c("session")
        + " line, and the file minus our block is byte for byte its source), given the owner, mode and SELinux label it must have, and only then renamed over the target. If anything looks wrong the file is not touched and the reason is said. Symbolic links (authselect's) are never touched.",
        "<b>When it runs.</b> " + c("%post") + " (" + c("apply") + "), " + c("%preun") + " (" + c("remove") + ", after the service is stopped: with the service running its " + c("ExecStartPre") + " would put the line back), the triggers below, and the unit before every start (" + c("check") + ").",
        "<b>The triggers.</b> The login screen's package may come after REMOTIX or be updated. " + c("%triggerin") + " and " + c("%triggerpostun") + " on " + c("gdm") + ", " + c("lightdm") + ", " + c("sddm") + " and " + c("plasma-login-manager") + " run " + c("apply")
        + " again (the copies in " + sysf("/etc/pam.d") + " are regenerated from the new vendor files). If our regenerated copy cannot be refreshed it is deleted, so that the vendor's new file is in force without the hook: no hook is better than a login file that is out of date.",
        "<b>Why sddm is special</b> (register F21). Its three PAM files are config files of the sddm package, which the hook modifies in place, so for rpm they are «modified by the administrator». rpm decides what to do with a config file <i>before</i> any scriptlet or trigger runs, so taking the block out in "
        + c("%triggerprein") + " alone was too late (tried: the update wrote " + c(".rpmnew") + " and kept the old text, the removal left " + c(".rpmsave") + "). What the package does: before sddm is updated or removed (" + c("%triggerprein") + "; " + c("%triggerun") + " only for a real removal, when no instance is left) "
        + c("prepare sddm") + " notes whether the file minus our block is exactly what the package shipped, using the signature in the rpm database, and takes the block out; afterwards (" + c("%triggerin") + ", " + c("%triggerpostun") + ") " + c("apply sddm") + " puts the " + c(".rpmnew") + " in force, or deletes the " + c(".rpmsave") + ", "
        "only if its signature proves it is the old vendor text, and adds the block again. A file the administrator changed gets rpm's normal outcome plus our block.",
        "<b>Known limits.</b> During an update of sddm, between " + c("%triggerprein") + " and " + c("%triggerin") + " (a few seconds), the block is not there and a local login does not close the remote desktop first; if the update fails halfway the block is missing until the next start of the service or the next trigger. Lines that the administrator writes <i>inside</i> our block "
        "(between " + c("# BEGIN remotix-pam-hook") + " and " + c("# END remotix-pam-hook") + ") are lost at the next " + c("apply") + ". " + c("rpm -V sddm") + " reports " + c("sddm") + " and " + c("sddm-autologin") + " as modified while REMOTIX is installed. A lightdm configured as an XDMCP or VNC server "
        "could give " + c("XDG_SEAT") + " to a session that is in fact remote; its XDMCP is off by default and this was not tried. These were tried on the virtual machine " + c("lxqt") + " with sddm 16, 17 and 18 (22 Nov 2026); gdm, plasmalogin and lightdm are not config files and have no such problem.",
    ])

# ── 15.6 KDE with KWin alone ─────────────────────────────────────────────
S6A = p("On Ubuntu the package carries a second program, a patched labwc that hosts the KWin of a KDE session, because the labwc of the distribution is not enough there. The package of Fedora does not: decision D2 is that KDE runs on KWin alone, and the labwc of "
        "XFCE and LXQt is Fedora's own package, a weak dependency. KDE on Fedora is KWin 6.8 (the version the output-resize protocol below needs).", lead=True) + \
    table(["Question", "Answer", "Source"], [
        ["How KDE is started",
         c("remotix --kwin-virtual W H …") + " is the program that the user's manager starts as the KWin unit. It starts a small sidecar that answers " + c("org.freedesktop.ScreenSaver") + " and then turns into the wrapper of " + c("kwin_wayland --virtual")
         + ". There is no labwc, no patch and no statically linked wlroots in the package.", c("src/main.c") + ", " + c("src/kwin.c") + " (" + c("kwin_virtual_alive()") + ")"],
        ["How the size of the desktop is changed",
         "By " + c("kwin_output_resize()") + " with the protocol " + c("kde_output_management_v2") + " (version 22 or later), with a custom mode made by " + c("add_cvt") + ": any size, odd ones too, in about 3 ms. If KWin does not offer the protocol (a KWin older than 6.8) the "
         "session is <b>refused</b> with a clear message to the service log and the user, never a silent fallback. The two protocols " + c("kde-output-device-v2") + " and " + c("kde-output-management-v2") + " are compiled from XML files fixed in " + c("src/protocols/")
         + " (an unmodified copy from plasma-wayland-protocols, because Fedora's package does not carry them; " + c("README-kde-output.txt") + " says which commit).",
         c("src/kwin.c") + ", " + c("src/protocols/")],
        ["The mark «this KWin is REMOTIX's»",
         "The option " + c("--kwin-virtual") + " on its command line and " + c("REMOTIX_KDE_HOST=1") + " in the environment of its unit (" + c("kdehost.h") + "). The sweep that stops that KWin at the end of the session recognises it by these, and by the control group and the owner of the process; "
         "the mark never chooses the user or the unit. It is not a variable read with " + c("getenv()") + ": it is read from " + sysf("/proc/<pid>/environ") + ".",
         c("src/kdehost.h")],
        ["KWin remembers the last size",
         "KWin keeps the current mode and the custom modes of the output in " + sysf("~/.config/kwinoutputconfig.json") + " (a file of KWin in the user's home); the width and height of the start line count only the first time. The program therefore checks the size at birth and corrects it "
         "<b>before</b> mounting the stream (same function as the live resize); the line " + c("KWin alone: the output «…» is WxH after N ms") + " is that check. The file is not touched; it has an entry " + c("Virtual-0") + ", harmless to the local desktop, which uses other outputs (register F8).",
         c("src/kwin.c")],
        ["How a local login ends the KDE session",
         "The user's child first asks the Plasma session to exit, on the user's own bus, with " + c("org.kde.Shutdown.logout") + " (not " + c("LogoutPrompt") + ", which asks), and waits 5 s when the close is for a local login, 10 s otherwise. If the session does not exit, the child closes it by force with " + c("StopUnit graphical-session.target")
         + ", saying that whatever was not saved is lost. The target is " + c("graphical-session.target") + " and not " + c("plasma-workspace.target") + ": the programs of the session (kwin, plasmashell and the others) are " + c("PartOf=graphical-session.target") + " and survive the stop of the workspace target. This was the defect of 25 Nov 2026 (register F36): "
         "with a program that did not close by itself the local login went on with the remote KWin alive; with the correction, on the real machine (a Konsole running " + c("top") + "), the forced close came at 10.05 s and everything was stopped 0.56 s later, before the wait was shortened to 5 s for a local login. Those figures are a measure of that machine, not a guarantee (" + rif("Lines of the stop, the orphan rule and the local-login hold") + ").",
         c("src/session.c") + ", " + c("docs/REGISTRO-problemi.md")],
        ["Dead code left in the source",
         "The old path through a patched labwc is still in the source and cannot be reached: " + c("kwin_nested_alive()") + ", the " + c("kwin_host_*") + " functions, the define " + c("REMOTIX_LABWC") + " in " + c("src/Makefile") + " that the spec never sets, and the option " + c("--kwin-nested") + ", which answers with an error. They are to be removed after "
         "the owner's tests (register F7). The manual does not describe them as a feature.",
         c("src/kwin.c") + ", " + c("src/main.c")],
    ], "«TAB» — KDE on KWin alone") + \
    warn("GNOME has the same construction for the forced close as KDE but without the last defence that KDE got on 25 Nov 2026: at the ceiling of 20 s the login goes on anyway (register F36, «Resta»). That is today's behaviour on GNOME, XFCE and LXQt.",
         "A limit of the forced close.")

# ── 15.7 Removal ─────────────────────────────────────────────────────────
S6 = p("RPM has no «purge». <b>Removal does all of it</b>: " + c("sudo dnf remove remotix") + " runs " + c("%preun") + " and " + c("%postun") + " with " + c("$1") + " equal to 0, and what Debian does in " + c("prerm") + " and in " + c("postrm purge")
       + " is done there, <b>so that the uninstallation leaves the system clean</b> (the owner's rule of 19 Nov 2026). The scriptlets also run, with " + c("$1") + " equal to 1 or more, on an upgrade, and the code below that acts only on removal is guarded by " + c("$1 -eq 0") + ".",
       lead=True) + \
    p("<b>" + c("%preun") + " (only on removal; on an upgrade it closes no session itself, but the restart of the service that " + c("%systemd_postun_with_restart") + " does if it was running closes them, see the last section).</b> The order matters and each step was added "
      "deliberately:") + \
    ul([
        "<b>Close the sessions, with the service still running.</b> " + c("remotix_close_sessions()") + " finds "
        "the logind sessions whose " + c("Service") + " is " + c("remotix") + " and which have no seat ("
        + c("remotix_sessions()") + "; a seated session is never ours whatever its service says) and runs "
        + c("loginctl terminate-session") + " on those whose scope is alive (" + c("remotix_scope_alive()") + "). "
        "Only those: never the whole user. The order is the point: if the service were stopped first, the child "
        "that leads the logind session would exit, logind would close the session and abandon its scope with the "
        "desktop inside, and " + c("terminate-session") + " would have no scope left to stop.",
        "It waits up to 15 s for the desktops to end by themselves, then sends SIGKILL to the scope of each session "
        "that did not (" + c("systemctl kill --kill-whom=all --signal=SIGKILL session-N.scope") + ", saying so on "
        + c("stderr") + "), then waits up to 5 s more. Never a process outside a REMOTIX session's scope.",
        "<b>Stop the service</b> with " + c("systemctl stop remotix.service") + ", here and not left to the macro, because the order is sessions, service, sessions again.",
        "<b>Then take the PAM line out:</b> " + c("remotix-pam-hook remove") + ". It is done only now, with the service stopped: with the service running, its " + c("ExecStartPre") + " would put the line back if the service restarted meanwhile. A failure is said "
        "(<i>remotix: ⚠ the PAM hook could not be fully removed: check /etc/pam.d/gdm-*, plasmalogin*, lightdm* and sddm*</i>) and does not stop rpm. (On Debian the line is taken out first; here it is the other way round.)",
        "<b>Sweep again</b> for what the stop left in an abandoned scope, then, for each person who had a REMOTIX "
        "session and has no other graphical session (a non-REMOTIX session of type x11, wayland or mir), stop " + c("graphical-session.target") + " in that user's manager.",
        "<b>Undo the group enrolments</b> recorded in " + sysf("/var/lib/remotix/group-enrollments.jsonl") + " with "
        + c("gpasswd -d") + ", only if the record is a regular file, not a link, owned by root, and after checking "
        "that the names contain nothing but " + c("A-Za-z0-9._-") + ".",
        "<b>Take back the card ACLs</b> by running " + c("remotix --drop-render-grants") + ", with the service stopped and "
        "before the record and the binary go. If it fails, a warning is printed and " + sysf("/run/remotix/render-grants-kept")
        + " is left as a marker so the " + c("%postun") + " keeps the record.",
        c("%systemd_preun remotix.service") + " closes the scriptlet.",
    ]) + \
    p("<b>" + c("%postun") + ".</b> On every run it reloads firewalld (the service definition is gone after a removal) and lets " + c("%systemd_postun_with_restart") + " restart the service if it was running (on an upgrade). "
      "On a removal only (" + c("$1 -eq 0") + ") it also:") + \
    ul([
        "unloads the SELinux module (" + c("%selinux_modules_uninstall") + ": the macro acts only when " + c("$1") + " is 0) and relabels (" + c("%selinux_relabel_post") + ");",
        "removes " + sysf("/var/lib/remotix/net") + ", " + sysf("/var/lib/remotix/certificates") + ", " + sysf("/var/lib/remotix/ban")
        + ", " + c("ban.new") + " and " + sysf("/run/remotix") + "; removes " + c("render-grants") + " unless the marker says "
        "the ACLs could not all be taken back (then it keeps it and says so);",
        "<b>walks every account the system lists</b> (" + c("getent passwd") + ") and, for each one that has a folder " + sysf("~/.local/state/remotix")
        + " or a file " + sysf("~/.config/dconf/remotix") + ", acts <b>as that user</b> through " + c("runuser") + ", so that a link planted in a home cannot make root delete something "
        "else. In the state folder it removes the product's files by name (" + c("session.log") + ", " + c("xfce-chiavi") + ", " + c("xfce-vecchi-ripristinati") + ", "
        + c("lxqt-restored") + ", " + c("gnome-ripristinato") + ") and the folder if it is left empty. Of the dconf folder it removes "
        "<b>only</b> the regular file " + c("remotix") + " (the small database of the three keyboard keys that change during a session), never through a link, never " + c("user")
        + ", never the folder " + c("dconf") + ". Never " + c("rm -rf") + " of a folder in a home. If the product writes another file there its name "
        "must be added to the list. Homes that are absent are skipped in silence, and the walk never makes the removal fail;",
        "deletes the user " + c("remotix") + " and its group, unless " + c("net-user-preexisting") + " exists and only "
        "if its uid is between 1 and 999;",
        "removes " + c("net-user-preexisting") + " and " + c("group-enrollments.jsonl") + ", and the folder " + sysf("/var/lib/remotix") + " if it is empty; if it is not empty, " + c("restorecon -R /var/lib/remotix") + ";",
        "removes the system dconf database " + sysf("/etc/dconf/db/remotix") + " (and " + c("remotix.new") + " and any " + c("remotix.new.*") + " left by an interrupted compile);",
        "removes by exact name the " + c("*.rpmsave") + " of the three config files and the empty folders " + sysf("/etc/remotix/remotix.conf.d") + ", " + sysf("/etc/remotix") + " (with " + c("rmdir") + ", never " + c("rm -rf") + ": the administrator's own files in the drop-in folder stay, and so does the folder that holds them), "
        "and " + sysf("/etc/needrestart/conf.d") + " and " + sysf("/etc/needrestart") + " if needrestart is not installed.",
    ]) + \
    p("On Debian " + c("apt remove") + " keeps the configuration. On Fedora " + c("dnf remove") + " deletes the config files that were not modified, and leaves " + c("*.rpmsave") + " for those that were, which the scriptlet then removes by name; the administrator's edits to the three config files are therefore not kept after a removal.") + \
    warn("The removal acts on the users that the system lists when it runs. A user that is not listed at that moment (a network directory that is down, an account in a "
         "database that is unreachable) keeps the file " + sysf("~/.config/dconf/remotix") + " and the state folder. The file is inert without REMOTIX, but the "
         "claim «the uninstallation leaves the system clean» holds for the listed users only. Declared limit, not measured on a machine with such a directory.",
         "Limit of the clean removal.") + \
    p("<b>Verification on Fedora.</b> Installation, upgrade (from the packages " + c("l6") + " and " + c("k4b") + "), removal (also with the folder " + sysf("/var/lib/remotix") + " left over: its label went back to " + c("var_lib_t") + "), reinstallation from nothing and a reboot of the virtual machine "
      "with the module loaded were tried on the bench (register F24, 22 Nov 2026), and the removal and the update of sddm with the block inside its files, byte for byte (F21). " + c("prove/check-package.py") + " was not used (it is still the Ubuntu one, " + rif("The package check")
      + "). On 25 Nov 2026 the package 1.2.0 itself was installed from nothing, upgraded from the previous build and removed on the KDE virtual machine (SELinux enforcing): after the removal nothing of REMOTIX was left, except the firewalld rule the administrator had added (the package never adds it and never removes it). It was not tried on the other three desktops nor on a real machine.")

# ── 15.8 Service policy ──────────────────────────────────────────────────
S7 = p("The package installs the service disabled and does not start it. The administrator enables it with "
       + c("systemctl enable --now remotix") + ", as the package description says. The preset of Fedora is " + c("disable *") + ", and the macros of the spec follow it:", lead=True) + \
    code("%systemd_post remotix.service           # in %post\n%systemd_preun remotix.service            # at the end of %preun\n%systemd_postun_with_restart remotix.service   # in %postun", "bash",
         "rpm/remotix.spec") + \
    table(["Event", "What happens to the service"], [
        ["First installation", "Nothing is enabled or started. The files, the user and the folders are there."],
        ["Upgrade", "If the service was running, " + c("%systemd_postun_with_restart") + " restarts it after the new files are in place; a stopped service stays stopped. The restart is a stop followed by a start, so it <b>closes every remote desktop</b> (" + rif("Stopping the service")
         + "): the stop takes up to the bounds given there (the network side and the children have 25 s). Warn the users of a busy server before upgrading; they log in again and get a new session."],
        ["Removal", "The " + c("%preun") + " closes the REMOTIX sessions and stops the service (see the previous section)."],
    ], "«TAB» — The package and the service") + \
    h4("Installing as the administrator does") + \
    code("sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm\nsudo systemctl enable --now remotix\nsudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload", "bash", "Install, start and open the port") + \
    p("The package is not signed. The bench installs it with " + c("rpm -U --nosignature --replacepkgs") + " (" + c("prove/banco-vm/box.sh install") + "), so that a package rebuilt with the same version number is really installed; for the administrator, " + c("sudo dnf reinstall ./remotix-1.2.0-1.fc45.x86_64.rpm")
      + " does the same. A reinstall runs the scriptlets as an upgrade would: the service is restarted if it was running, and the encoding test of the " + c("%post") + " is not repeated. The machine must also have the codecs of " + rif("Package metadata: Depends and Recommends") + ".") + \
    h4("needrestart") + \
    p("A tool that restarts the services that use a library that has just been upgraded (" + c("needrestart") + ", on machines that have it, for example run by an automatic update) would restart REMOTIX and close every remote desktop. The package therefore installs "
      + sysf("/etc/needrestart/conf.d/remotix.conf") + " with the single line " + c("$nrconf{override_rc}{qr(^remotix\\.service$)} = 0;") + ": the service is then listed under "
      "«Services to be restarted manually» and left running, with the old library loaded, until the administrator restarts it when no remote desktop is open. "
      "<b>needrestart is not installed on Fedora by default</b> (its counterpart is " + c("dnf needs-restarting") + "), and that the line has this effect on Fedora was <b>not observed</b>. The file is a config file, so an administrator's edit survives an upgrade.") + \
    p("The rule of the installed-disabled service comes from point 1 of decision §10.12 of " + c("DECISIONS.md") + " (the package switches nothing on) and is stated in the " + c("CLAUDE.md") + " of the Fedora tree: the service is installed disabled and not started, and the administrator enables it. The unit uses the "
      "machine's name (" + c("%H") + ") for the certificate; an administrator who connects by IP address puts "
      + c("REMOTIX_OPTIONS=--name 192.168.1.10") + " in a drop-in under " + sysf("/etc/remotix/remotix.conf.d/")
      + " (the last " + c("--name") + " wins). Two lines of the unit are new on Fedora: " + c("ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check") + " (the hook's line is checked at every start, and a failure never prevents the start) and "
      + c("Environment=MESA_SHADER_CACHE_DISABLE=true") + " (the codec probe of the root side would otherwise make Mesa open its shader cache in " + sysf("/root/.cache") + ", which the SELinux module does not allow; the users' desktops get their own environment from PAM and keep the cache). "
      "The runtime life cycle of the service is in " + rif("Startup and life cycle") + ".")

# ── What the administrator provides ──────────────────────────────────────
S8 = p("A few things are not in the package and are the administrator's. They are the conditions under which the package, once installed, shows a desktop.", lead=True) + \
    table(["Requirement", "What to do", "If it is missing"], [
        ["A video card that encodes H.264", "Enable RPM Fusion (free) and install " + c("mesa-va-drivers-freeworld") + "; NVIDIA, its proprietary driver. Check with " + c("sudo /usr/libexec/remotix/remotix --encoding-test h264") + " (decision D1).",
         "The " + c("%post") + " warns once; the server says " + c("THIS SERVER CANNOT ENCODE VIDEO") + " and every connection ends in «nothing in common»."],
        ["The port in the firewall", "The two commands of " + rif("Files the package installs") + " (decision D5).", "The page does not answer from another machine."],
        ["SELinux enforcing", "Nothing to do: it is the normal state, and the package brings its module. Do not switch it off to «make it work».", "The server says that the module is not loaded and runs without the wall; see " + rif("The SELinux module") + "."],
        ["The right time on the client device", "A device whose clock is wrong makes the TLS handshake fail with <i>certificate unknown</i>, and the browser says «Opening handshake failed». The server's log now says why (" + c("connection with … closed — the PEER closed it: transport error … TLS alert 46 certificate_unknown") + ", register F23, area "
         + c("quic") + ").", "The client cannot connect, with no other sign on the page."],
        ["A desktop and its login screen", "GNOME (" + c("gdm") + "), KDE Plasma (" + c("plasmalogin") + "), XFCE (" + c("lightdm") + "), LXQt (" + c("sddm") + "); and " + c("labwc") + " for XFCE and LXQt.", "No desktop: the server says so at start-up (" + rif("The startup declarations") + ")."],
    ], "«TAB» — What the administrator provides")

CHAPTER = ("The package", [
    ("What the package is and how it is built", S1),
    ("Package metadata: Depends and Recommends", S2),
    ("The preinst refusals", S3),
    ("The postinst: user, folders and encoding test", S4),
    ("Files the package installs", S5),
    ("The SELinux module", S5B),
    ("The PAM service file on Fedora", S5C),
    ("The local-login hook on four login screens", S5D),
    ("KDE with KWin alone", S6A),
    ("Removal: prerm, postrm and purge", S6),
    ("Service policy: installed disabled", S7),
    ("What the administrator provides", S8),
])
