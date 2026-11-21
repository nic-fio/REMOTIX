"""Chapter 20 — Extending REMOTIX and porting to another distribution (Ubuntu 26.04 tree: the second port). Sources: the code of this tree
(src/session.c, src/session.h, src/kwin.c, src/main.c, src/rcp.c, src/rcp.h, src/msgrate.h, src/page.html, src/encoder.c, src/child.c, debian/*,
build/*, prove/*, server/*), docs/REGISTRO-problemi.md (every entry, "on a new distribution" line), docs/INVENTARIO-non-debian.md,
docs/PULIZIA-tranche1.md, studio/5-sistema-ubuntu.md, studio/8-pacchetto-e-prove.md."""
from build import c, h4, note, p, rif, steps, sysf, table, tip, ul, warn

# ── 20.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX 1.0.1 exists twice: for Debian 13 (trixie), in the folder " + c("debian13/") + ", and for Ubuntu 26.04 (resolute) with its four flavours "
       "(Ubuntu with GNOME, Kubuntu with KDE Plasma, Xubuntu with XFCE, Lubuntu with LXQt), in this tree. The second tree is a separate copy of the first, "
       "with its own packaging, its own build image, its own test bench and its own manual: the rule that a port is a copy and not a new <code>if</code> "
       "in the old tree has been followed once, and this chapter is written from what that port needed.", lead=True) + \
    p("Most of the code does not depend on the distribution at all: the transport, the RCP/1 protocol, capture, encoding, the budget, input, "
      "audio, clipboard, the page. Its dependencies are on the Linux kernel (DRM nodes, libei, PipeWire), on systemd and logind, on PAM and "
      "polkit, on the four desktops, and on a handful of facts about the distribution that the next section lists. The "
      "port from Debian to Ubuntu changed about fifty source files; the diff is dominated by " + c("src/session.c") + " (the desktop sessions) and by the packaging.") + \
    p("The product does not detect the distribution to choose a behaviour of its own. It does read, from the machine, what the machine offers: the session "
      "names that the display manager lists, the session that carries the distribution's name in " + sysf("/etc/os-release") + " (" + c("gnome_session()") + "), the markers "
      "of the installed desktops on the " + c("PATH") + ". That is the criterion that let the same code serve the four Ubuntu flavours (" + rif("The four desktops") + ").") + \
    warn("A decision of the first port is no longer true to the letter. The Debian tree removed the code that only another distribution needed (the Ubuntu "
         "session names, the GNOME 50 unit shape, the session-folder discovery of a local login) because it could not be reached on trixie. Ubuntu needs "
         "exactly that code, so it came back (" + rif("What the clean-up removed, kept and risked") + "). A third port must expect the same: removing code "
         "that is dead on one distribution is a loan, not a deletion.", "Removed code comes back.") + \
    note("The history of the clean-up is in two documents of " + c("docs/") + ": " + c("docs/INVENTARIO-non-debian.md") + " lists what existed only for another "
         "distribution, with a verdict per item; " + c("docs/PULIZIA-tranche1.md") + " records what tranche 1 removed on 17 Nov 2026 on the Debian tree, with "
         "the proof that each item was unreachable on trixie. Both describe the Debian tree; in this tree part of that code is live again. Line numbers in "
         "the inventory are those of the tree before tranche 1 and no longer point to the right lines.", "Where the history is.")

# ── 20.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The table lists what a porter must look at, area by area, for the two distributions the tree has been ported to. The Debian column describes the "
       "folder " + c("debian13/") + " and is quoted from the Debian 13 manual; the Ubuntu column was read in the code of this tree. Names are files and "
       "functions, not line numbers.", lead=True) + \
    table(["Area", "Debian 13 (debian13/)", "Ubuntu 26.04 (this tree)", "Where"], [
        "Packaging and build",
        ["package format", ".deb through debhelper compat 13, " + c("dh-apparmor") + ", maintainer scripts calling " + c("deb-systemd-invoke") + ", "
         + c("getent") + ", " + c("systemd-sysusers") + ", " + c("systemd-tmpfiles"),
         "the same format and scripts. Added: " + c("debian/remotix.install") + " copies " + c("debian/needrestart/remotix.conf") + " to " + sysf("/etc/needrestart/conf.d")
         + " (the service is never restarted by needrestart: a restart closes every remote desktop, DECISIONS-11 §11.56); the " + c("postinst") + " compiles "
         + sysf("/etc/dconf/db/remotix") + " with " + c("dconf compile") + " and warns if the labwc of XFCE and LXQt is missing; the " + c("postrm") + " removes that database and, on purge, "
         + sysf("~/.config/dconf/remotix") + "; " + c("debian/rules") + " runs " + c("src/remotix --dconf-keyfiles") + " and builds our labwc",
         c("debian/")],
        ["dependency names", c("libpam-systemd") + ", " + c("libpam-modules") + ", " + c("passwd") + ", " + c("dbus-user-session") + ", " + c("pipewire")
         + ", " + c("wireplumber") + "; Recommends " + c("va-driver-all") + ", " + c("mesa-vulkan-drivers") + ", " + c("labwc") + ", " + c("dconf-cli")
         + ", " + c("wlr-randr") + ", " + c("xwayland") + ", " + c("fonts-dejavu-core"),
         "Depends and Recommends unchanged (the diff of " + c("debian/control") + " does not touch them). Build-Depends grow by fifteen packages for our labwc (" + c("meson") + ", "
         + c("patch") + ", " + c("hwdata") + ", " + c("wayland-protocols") + ", " + c("libinput-dev") + ", " + c("libseat-dev") + ", ...). " + c("libva-dev") + " and the Recommends are in "
         "universe; the Mesa VA driver lives in " + c("mesa-libgallium") + ", which is why the declaration stays " + c("va-driver-all") + " alone",
         c("debian/control")],
        ["build image", c("debian:trixie") + " with apt",
         c("docker.io/library/ubuntu:26.04") + " with apt (universe on). The static QUIC libraries remain: Ubuntu 26.04 carries ngtcp2 1.16 and nghttp3 1.12 (studio 8), too old for the pinned "
         "1.25.0 and 1.18.0. The image also fetches, and checks the sha256 of, the two upstream tarballs of our labwc",
         c("build/Containerfile") + ", " + c("build/quic-static.sh") + ", " + c("build/labwc-ospite/fetch.sh")],
        ["package version and archives", sysf("remotix_1.0.1-1+deb13_amd64.deb"), sysf("remotix_1.0.1-1+ubuntu26.04_amd64.deb") + " (suite " + c("resolute") + ") and the source of our labwc, "
         + sysf("remotix-<version>-labwc-source.tar.gz") + ", published with every release because labwc is GPL-2", c("build/build-deb.sh") + ", " + c("LICENSE.md")],
        ["install paths", c("/usr/libexec/remotix/remotix") + ", " + c("/usr/share/polkit-1/rules.d") + ", " + c("/etc/ufw/applications.d") + ", "
         + c("/etc/apparmor.d"), "the same, plus " + sysf("/usr/libexec/remotix/labwc") + " and " + sysf("/etc/needrestart/conf.d") + ". " + c("ufw") + " is installed but off by default on Ubuntu (" + c("ENABLED=no") + ")",
         c("debian/rules")],
        "Login and system integration",
        ["PAM service", "the file uses " + c("@include common-auth") + ", " + c("common-account") + ", " + c("common-session") + ", " + c("common-password")
         + ": a Debian modification of Linux-PAM; elsewhere the line is an illegal module type. It also lists " + c("pam_selinux") + " lines "
         "(module_unknown=ignore, harmless) and reads " + sysf("/etc/default/locale"),
         "the same file, unchanged in content (Ubuntu inherits the " + c("@include") + " syntax). Only a comment was added: the session's " + c("PATH") + " comes from "
         + c("pam_env") + " and " + sysf("/etc/environment") + " (which on Ubuntu lists " + sysf("/snap/bin") + "), so " + c("user_readenv=1") + " must NOT be added",
         c("src/remotix.pam") + ", " + c("child_path_ok()") + " in " + c("src/child.c")],
        ["PAM service lookup and messages", "the server checks " + sysf("/etc/pam.d/remotix") + ", then " + sysf("/usr/lib/pam.d/remotix") + "; some log "
         "messages still name other distributions' file names", "unchanged", c("src/main.c") + ", " + c("src/authentication.c")],
        ["who is an administrator", "polkit rules name " + c("sudo") + ", " + c("wheel") + " and " + c("admin") + "; only " + c("sudo") + " exists on trixie as shipped",
         "polkit 127 of Ubuntu names " + c("sudo") + " and " + c("admin") + " (" + sysf("49-ubuntu-admin.rules") + "), so the rule covers Ubuntu with no change; "
         + c("wheel") + " stays for other distributions",
         c("src/remotix-remote-sessions.rules") + ", " + c("src/remotix-polkit-seated")],
        ["power actions of logind", "twelve actions forbidden at first, fifteen on 17 Nov 2026",
         "nineteen: the four " + c("set-reboot-*") + " actions carry an <i>imply</i> annotation on " + c("reboot") + " and are allowed for the seated user, so polkit granted the reboot "
         "to the local user despite the explicit NO (register C6, 20 Nov 2026). The list depends on the systemd version of the distribution (" + rif("A checklist for porting to another distribution") + ")",
         c("src/remotix-no-poweroff.rules") + ", " + c("power-implied") + " in " + c("prove/check-desktop.py")],
        ["system user and directories", "sysusers and tmpfiles files; the system user " + c("remotix") + " with " + sysf("/usr/sbin/nologin"), "unchanged", c("debian/remotix.sysusers")
         + ", " + c("debian/remotix.tmpfiles")],
        ["mandatory access control", "AppArmor, profile in complain mode, never observed in a live graphical session; SELinux code was removed",
         "AppArmor in complain mode, observed in real sessions (the start-up log line was read on the live images of Ubuntu and Kubuntu and on the four virtual machines; on the Xubuntu and Lubuntu live images only the owner's report of a successful sign-in exists). Three differences from the Debian profile: the two <code>deny unix</code> lines "
         "that name their operations (the single line of Debian forbids every unix socket on the kernel of Ubuntu, 7.0, which mediates them, and a <code>deny</code> holds in complain "
         "mode too: register C4); the XKB folders of xkb-data 2.46 (" + sysf("/usr/share/xkeyboard-config-2/") + ", " + sysf("/etc/xkb/") + ", " + sysf("/etc/X11/xkb/") + "); and "
         "<code>include if exists &lt;local/remotix_network&gt;</code> for the administrator's additions. SELinux is still absent from the code",
         c("debian/remotix_network.apparmor")],
        ["firewall profile", "ufw application profile (defined, never opened)", "the same; an administrator who turns ufw on must run " + c("ufw allow REMOTIX"), c("debian/remotix.ufw")],
        ["first connection", "adds the user to the group that owns the render nodes (read from " + sysf("/dev/dri/renderD*") + "; not " + c("video") + ") with " + c("usermod") + "; for a user manager born before that, an ACL on the render nodes for the user's private group",
         "unchanged (the group " + c("render") + " is created by udev on Ubuntu)", c("src/child.c") + ", " + c("src/render_grant.c")],
        "Desktops",
        ["which desktop is installed", "markers " + c("xfce4-session") + ", " + c("lxqt-session") + ", " + c("startplasma-wayland") + ", " + c("gnome-session")
         + " found on the PATH; session names mapped to desktops by a substring match",
         "the same markers, and the names of the Ubuntu flavours in the map: " + c("desktop_of_session_name()") + " asks " + c("xubuntu") + ", " + c("lubuntu") + ", " + c("kubuntu")
         + " BEFORE " + c("ubuntu") + ", whose name they contain. A flavour outside the four (for example " + c("ubuntustudio") + ") falls in the GNOME branch by that same substring: not supported",
         c("desktop_session()") + ", " + c("desktop_of_session_name()") + " in " + c("src/session.c")],
        ["display manager readers", "the active manager from " + sysf("/etc/X11/default-display-manager") + " or the link " + sysf("/etc/systemd/system/display-manager.service")
         + "; lightdm " + c("user-session") + " and sddm " + c("[Autologin] Session") + " read from their configuration folders",
         "the same readers, and here they are used: Xubuntu sets its session in " + sysf("60-xubuntu.conf") + " (lightdm) and Kubuntu in " + sysf("20-kubuntu.conf") + " (sddm)",
         c("src/session.c")],
        ["GNOME session unit", "the user unit " + sysf("org.gnome.Shell@wayland.service") + " as a real file (GNOME 48 on trixie)",
         "GNOME 50: the template unit " + sysf("org.gnome.Shell@.service") + " with an instance (" + sysf("@ubuntu") + " or " + sysf("@user") + ") that is read from the " + c("Requires") + " of "
         + sysf("gnome-session@<session>.target") + "; the drop-ins go in the folder of the INSTANCE, never in " + sysf("org.gnome.Shell@.service.d") + " (" + c("unit_shell()") + ", " + c("SESSION_UNIT_SHELL_MODEL")
         + ", " + c("SESSION_UNIT_GRAPHICAL") + ")",
         c("src/session.c") + ", " + c("src/session.h")],
        ["compositor for XFCE and LXQt", "Debian's labwc (0.8.3 on trixie)", "Ubuntu's labwc, 0.9.3 on wlroots 0.19.2 of the system", c("debian/control") + ", " + c("src/wlroots.c")],
        ["compositor for KDE", "Debian's labwc hosts KWin so that the desktop takes the window's size at reattach; without labwc KDE starts with KWin " + c("--virtual"),
         "KWin is hosted by OUR labwc, " + sysf("/usr/libexec/remotix/labwc") + " (labwc 0.9.3 with a patched wlroots 0.19.2, linked statically; " + c("build/labwc-ospite/README") + "), "
         "because the distribution's labwc leaves KWin 6.5 and later on its first frame. The path is a build-time choice (" + c("LABWC ?=") + " in the Makefile, " + c("REMOTIX_LABWC")
         + " in " + c("kwin.c") + "); if the file is missing KDE falls back to " + c("--virtual") + ", declared in the log",
         c("build/labwc-ospite/build.sh") + ", " + c("src/kwin.c") + ", " + c("src/Makefile")],
        ["compositor component missing", "no check: the user is admitted and looks at an empty canvas",
         c("session_missing_component()") + " names " + c("labwc") + " for XFCE and LXQt; " + c("main.c") + " answers 0x0E, \"the desktop cannot start: <code>labwc</code> is not installed on this server\", before the child is born",
         c("src/session.c") + ", " + c("src/main.c")],
        ["KWin quirks", "runtime probes for KWin 6.3 (trixie) and later; no version test in the code",
         "KWin 6.6.7 (Plasma 6.6) on Ubuntu; new quirks: " + c("kwin_poke()") + " and " + c("capture_frame_lost()") + " for buffers that KWin drops, a sidecar that answers " + c("org.freedesktop.ScreenSaver") + " "
         "(" + c("SCREENSAVER_NAME") + "), and the logout rescue " + c("session_kde_logout_watch()") + " because on Plasma 6.6 the unit that the old rescue waited for never stops (register D)",
         c("src/kwin.c") + ", " + c("src/capture.c")],
        ["settings that programs read themselves", "not present: no snap programs on the test bench, and dconf 0.40",
         "GNOME rules reach the session as a system database (" + sysf("/etc/dconf/db/remotix") + ") and a runtime profile in " + sysf("$XDG_RUNTIME_DIR/dconf/profile") + ", with no " + c("DCONF_PROFILE")
         + ", because the Flutter programs of Ubuntu and the confined snaps have their own dconf reader (register C5)",
         c("src/session.c") + ", " + c("debian/remotix.postinst")],
        "Test machinery",
        ["boxes", "the images install " + c("task-<de>-desktop") + " and register " + c("gdm3") + ", " + c("sddm") + " or " + c("lightdm") + " (ports 8811 to 8814)",
         "container images " + c("rxu-<de>") + " installed with the flavours' own packages (" + c("ubuntu-desktop-minimal") + ", " + c("kubuntu-desktop") + ", " + c("xubuntu-desktop") + ", " + c("lubuntu-desktop")
         + "; ports 8821 to 8824), with the snap browsers kept out by a pin. They are still in the tree but are NOT the bench of the release",
         c("boxes/Containerfile") + ", " + c("boxes/box.sh")],
        ["release bench", "the four containers and one real virtual machine",
         "four QEMU virtual machines, installed from the desktop images, with the server's Radeon passed through (" + rif("The VM bench") + ")",
         c("server/vm-radeon.sh") + ", " + c("prove/banco-vm/box.sh")],
        ["tests", "apt for the package check; Debian's package names for the browsers on the dev server",
         c("prove/check-package.py") + " is not part of the VM bench (declared SKIP); " + c("server/prepara-server.sh") + " uses " + sysf("/media/REMOTIX-UBUNTU") + " and the container storage shared with the Debian tree",
         c("prove/all.sh") + ", " + c("server/prepara-server.sh")],
    ], "«TAB» — Where the code depends on the distribution (Debian 13 and Ubuntu 26.04)") + \
    p("The state of each item on the Debian tree (removed, left, or to be removed later) is in " + c("docs/INVENTARIO-non-debian.md") + ", section \"Status after tranche 1\".")

# ── 20.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The Debian tree removed, on 17 Nov 2026, the code that could not be reached on trixie (" + c("docs/PULIZIA-tranche1.md") + "). The Ubuntu port is the "
       "proof that a porter meets each of those problems again: the table says, item by item, what came back in this tree.", lead=True) + \
    table(["Removed on Debian", "What it did", "On the Ubuntu tree"], [
        ["SELinux handling in " + c("child.c") + " and " + c("walls.c"), "set the SELinux level of a login like sshd; set the exec context of the network side; the " + c("-ldl") + " link flag",
         "still absent (no SELinux handling anywhere in the code). Needed again on a distribution with SELinux enabled by default"],
        ["Ubuntu session names in " + c("desktop_of_session_name()"), "mapped " + c("xubuntu") + ", " + c("lubuntu") + ", " + c("kubuntu") + ", " + c("ubuntu"),
         "<b>back</b>, with the order that matters (the flavours before " + c("ubuntu") + ")"],
        ["os-release match in " + c("gnome_session()"), "chose a gnome-session whose name equals os-release ID", "<b>back</b>: it is how the " + c("ubuntu") + " session of GNOME is chosen"],
        ["the GNOME 50 template branch of " + c("unit_shell()"), "handled the template unit " + sysf("org.gnome.Shell@.service"),
         "<b>back</b>, and it is the only branch: the GNOME 48 unit (" + c("SESSION_UNIT_SHELL_48") + ") is gone"],
        ["D-153 folder discovery (the session as a local login gives it)", "used Ubuntu's " + sysf("Xsession.d/60x11-common_xdg_path") + " mechanism; " + c("local_session()")
         + " then returned an empty structure",
         "<b>back</b>: " + c("local_session()") + " is live again, with a field for the common folder (" + sysf("/usr/share/gnome") + " from the snippet " + sysf("profile.d/gnome-session_gnomerc.sh")
         + ", only for GNOME or an X11 login). The script exists on Ubuntu 26.04 (package x11-common)"],
        ["the EI-ping build switch, the fallback", "built without input receipts for libei older than 1.3.901", "still removed: the minimum stays " + c("libei-1.0:1.3.901") + " in " + c("MINIMI") + " of the Makefile"],
        ["the own-labwc build switch and the " + c("LABWC=") + " knob of the Makefile", "the patched or own labwc path",
         "<b>back in another form</b>: a fixed build-time path " + c("REMOTIX_LABWC") + ", not a run-time switch, for KDE only"],
        ["the 90-default-privs branch of " + c("remotix-polkit-seated"), "openSUSE's polkit-default-privs", "still absent"],
        ["1.0 to 1.5 upgrade machinery", c("remotix-net-move") + ", the non-split unit and tmpfiles", "still absent"],
    ], "«TAB» — What the Debian clean-up removed and what came back on Ubuntu") + \
    h4("What stays and why") + \
    ul([
        "The " + sysf("/usr/lib/pam.d") + " lookup and the other distributions' texts in the PAM messages: " + sysf("/usr/lib/pam.d") + " is a real PAM vendor "
        "directory, so the lookup is not provably dead. Only text.",
        "The " + c("pam_selinux") + " lines of " + c("remotix.pam") + ": the module ships with the PAM modules of both distributions and the lines mirror sshd.",
        "The lightdm and sddm readers and " + c("declared_desktop()") + ": on Ubuntu the flavours use them (Xubuntu and Kubuntu set their session there).",
        "The KWin workarounds: runtime probes, not version tests.",
        c("wheel") + " and " + c("admin") + " in the polkit rule: logic, kept (Ubuntu names " + c("admin") + ").",
        "The " + c("--no-split") + " run-time option and " + c("TWIN") + " and " + c("fingerprints") + " in the Makefile.",
        "Several header comments that mention other distributions, and the " + c("Ubuntu") + " name in the page's font stack.",
    ]) + \
    h4("Risks recorded by tranche 1, and where they stand") + \
    ul([
        "The session-folder lookup that imitated a local login (D-153) relied on x11-common not shipping " + c("60x11-common_xdg_path") + ": on Ubuntu it ships, the risk is "
        "realised and the code is back.",
        "An administrator who installs SELinux finds no SELinux handling in REMOTIX, on either tree.",
        "A build against libei older than 1.3.901 fails at " + c("make deps") + " by design.",
        "On " + c("apt remove") + " (not purge) the certificates and ban list stay in " + c("net/") + " instead of moving back to the 1.0 location; "
        "a check that looks for the 1.0 location will not find them.",
    ]) + \
    p("What tranche 2 listed as still to do (the remaining Ubuntu and Xubuntu detection in " + c("session.c") + ", the emulation of a local login's " + c("XDG_*")
      + " variables) is live code in this tree and is described in " + rif("The four desktops") + ", not left as work. Comments naming other distributions, and the other "
      "cosmetic items, are in " + rif("Appendix C — Known issues and open points") + ".")

# ── 20.4 (new) ───────────────────────────────────────────────────────────────
S3B = p("This section is the experience of the second port, taken from the problem register (" + c("docs/REGISTRO-problemi.md") + ", the line \"on a new "
        "distribution\" of each entry) and from the code. It lists what had to change on the way from Debian 13 to Ubuntu 26.04, and what the second port found that "
        "the first had not.", lead=True) + \
    table(["Subject", "What changed in practice", "Register"], [
        ["GNOME 50 session", "the template unit with an instance, the " + c("--mode") + " option of the shell, the guard on " + c("graphical-session.target") + "; the session named " + c("ubuntu") + " is the one a user sees at the real "
         "screen, so it is the one REMOTIX starts (" + c("gnome_session()") + ")", "-"],
        ["Settings of the session", "a new dconf model: system database, runtime profile, user database " + sysf("~/.config/dconf/remotix") + ", declared fallback, and three answers (alive, dead, unknown) to the question "
         "\"is the desktop alive\"", "C5, E3"],
        ["The scale of the user", "two keys of the settings and " + c("mutter_scale_to_one()") + "; a stage refused for the scale closes the session with 0x0E", "-"],
        ["KDE", "our own labwc; KWin 6.6.7; the lost-frame watch; the logout rescue after " + c("plasma-shutdown") + " was refused by systemd", "D"],
        ["XFCE and LXQt", "the labwc of the distribution at 0.9.3; the XFCE panel integrity check; autostart entries (" + sysf("blueman") + ", " + sysf("lubuntu-update") + ") and X11 composition managers that do nothing under labwc", "E1"],
        ["Closing a session", "the child says \"the session is over\" before it dismantles its stage, only on a certain death and never on KDE; no " + c("--session-fd") + ": from systemd 258 the logind session "
         "is held by the leader's pidfd, and the leader is the child itself", "-"],
        ["AppArmor", "the kernel of Ubuntu mediates unix sockets; a <code>deny</code> without its operations forbids every socket, in complain mode too", "C4"],
        ["Polkit", "the implications of the policy files can authorise an action that the rule forbids", "C6"],
        ["Needrestart", "a drop-in so that a library update never restarts the service and closes every remote desktop", "- (" + c("debian/needrestart/remotix.conf") + ", DECISIONS-11 §11.56)"],
    ], "«TAB» — What the port to Ubuntu changed in practice") + \
    h4("What a second port found that the first did not") + \
    p("Most of these lessons were learned only because the second target had a real system around the product. None could have come from the Debian container bench; each cost a "
      "failure on a real machine or in front of the owner.") + \
    table(["Lesson", "What happened on Ubuntu", "What to do on a new distribution"], [
        ["A virtual machine, not a container, for the first sign-in",
         "On 19 Nov 2026 the first sign-in on a real Ubuntu image was refused for every user: the profile of the network side forbade every unix socket (C4). The containers had no AppArmor in force and no real login screen (B1). The bench "
         "became four virtual machines installed from the desktop images, with a real display manager, AppArmor, snap and the server's graphics card",
         "Plan a successful sign-in on a real or virtual machine with the security module in force before closing anything, and read the line \"§5.1 ... CONNECTED\" in the start-up log (register C4)"],
        ["Mandatory access control mediates more than expected",
         "A <code>deny</code> line without operations also covers <code>create</code>, which has no address; and the profile in complain mode still enforces its <code>deny</code> lines. The limit that remains: "
         "an \"autobind\" abstract socket is still allowed (" + rif("Ubuntu: what real machines showed that the boxes did not") + ")",
         "Write every <code>deny</code> with the operations it means; two stars (<code>@**</code>) where a name contains <code>/</code>; try Debian again after a kernel change. For SELinux, expect the removed code of " + c("child.c") + " and " + c("walls.c")],
        ["The polkit policy has implications",
         "The rule forbade the fifteen actions it knew by name, and a local user could still reboot: four " + c("set-reboot-*") + " actions imply " + c("reboot") + " and are open to the seated user (C6, found by the owner on his own machine on 20 Nov 2026). "
         "The round had watched only the remote session, which is not seated",
         "Read the implications of every " + c("*.policy") + " file of the machine (the check " + c("power-implied") + " does it), test from the seat of the local user too, and run it with the systemd version of the new distribution"],
        ["Programs that read the settings themselves",
         "Flutter programs (the installer of the live image, Firmware Updater, Security Center) have their own dconf reader that knows only the user and system databases and discards a profile with any other line; confined snaps have another "
         + c("XDG_RUNTIME_DIR") + " and cannot even open the path (C5). The first model, a three-layer profile in a run folder, therefore broke them",
         "Test with the real snap programs inside the remote session (no dconf exception in the log, no AppArmor DENIED); check that dconf reads a profile in the runtime folder when " + c("DCONF_PROFILE") + " is absent (dconf 0.49 does; "
         "dconf 0.40 of Debian was not measured); check that the " + c("postinst") + " built the database"],
        ["A red row that is the same everywhere is the tool first",
         "Three input rows failed identically on four machines while they were green on Debian 13: the test window, not the product, lost the mouse button release in a drag under GTK 4.22 (B3-bis). It was shown with " + c("WAYLAND_DEBUG")
         + " before the rows were archived",
         "Look at the raw events before blaming the product, and prove it before archiving"],
        ["A decision changes the tests in the same work",
         "The check of the service restart waited for the same desktop after the decision that the desktops close with the service, and the Ctrl+Alt buttons checks had lagged since August (B3)",
         "Update tests, manuals and register in the same piece of work as the decision (B5)"],
        ["Personal data in a package",
         "A personal address was found in the package and in the history of the Debian tree before publication (C3)",
         "Search the files, the history and the finished package before publishing anything"],
    ], "«TAB» — Lessons of the second port") + \
    note("The programs that read the settings themselves are a class, not a case: any program that reads dconf without the library (or from inside a confinement) bypasses what the product "
         "puts in the environment of the session. A third port to a distribution with Flatpak or snap applications should expect the same.", "A class of programs.")

# ── 20.5 ─────────────────────────────────────────────────────────────────────
S4 = p("The tree is not a template for a port, but the porting questions are now known from two ports. The list below is derived from the table above and "
       "from the register; it has been exercised once, for Ubuntu 26.04, and is the order in which that port met its problems.", lead=True) + \
    steps([
        "<b>Start from a copy,</b> not from a branch of an existing tree: the Ubuntu tree is a copy of the Debian one with its own " + c("debian/") + ", " + c("build/") + ", " + c("prove/") + " and " + c("manuals/") + ".",
        "<b>Check the library minimums</b> in " + c("src/Makefile") + " (" + c("MINIMI") + "): OpenSSL 3.5 or newer, GLib 2.80, libei 1.3.901, "
        "PipeWire, libva, Vulkan loader 1.3.274. The QUIC libraries are built from source in the image whatever the distribution carries (Ubuntu's are too old, too).",
        "<b>Rewrite the package</b> for the new format: dependency names, install paths, maintainer scripts. Keep the guards of " + c("debian/rules")
        + " (R13, R24) and the checks of " + c("build/build-deb.sh") + " (R4, R13, R14, R23) as requirements, however they are implemented. On Ubuntu they also cover our labwc: no libwlroots among its "
        "dependencies, and the corresponding source archive is built reproducibly.",
        "<b>Write the PAM service file</b> for that distribution's stack. Without the file, Linux-PAM falls back to the service " + c("other") + ", and what "
        + c("other") + " does depends on the distribution (on some it is a hard deny, so every right password is refused). The program checks "
        "the file at start-up (" + c("main.c") + "). Look at where the session's " + c("PATH") + " comes from.",
        "<b>Check polkit.</b> The rules directory; the groups that polkit calls administrator; whether a default privilege table overrides the rules; and the <b>implications</b> "
        "of the policy files of that systemd version (run " + c("power-implied") + "; the list of forbidden actions is 19 in this tree; the same correction was made for Debian on 20 Nov 2026 (rule with 19 actions in debian13/; the rebuilt Debian package is not yet published), and the test from the seat of the local user with the corrected Debian package was done on the owner's tablet on 20 Nov 2026: all refused, and on any new distribution it must be derived again).",
        "<b>Check the display manager and the session names</b> the desktops register, against " + c("desktop_session()") + ", " + c("gnome_session()") + " and the readers in " + c("session.c")
        + ". Check the order of the substring tests: a name that contains another (xubuntu, ubuntu) must be asked first.",
        "<b>Check mandatory access control on a real or virtual machine.</b> If SELinux is on, the removed handling of " + c("child.c") + " and " + c("walls.c") + " is needed. For AppArmor, adapt the profile, "
        "write every <code>deny</code> with its operations, and expect that the path that the profile sees is the resolved one (the XKB data are behind a symbolic link on Ubuntu). The profile is still shipped in complain mode "
        "and the enforce mode was not proven on either distribution (" + rif("What is unverified") + ").",
        "<b>Check the programs that read the settings themselves</b> (snap, Flutter, Flatpak): open them in a remote session and read the log of the session for settings errors (register C5).",
        "<b>Check the compositor</b> at the version the distribution carries, and the four desktops' versions, in particular the GNOME session unit shape (a template with instances from GNOME 50), the KWin version and "
        "whether the labwc of the distribution hosts KWin correctly: on Ubuntu it did not, and a labwc of our own is built into the package.",
        "<b>Make the bench.</b> Containers are good for speed and bad for the real login screen, the security module and the confined programs. Use virtual machines installed from the desktop images "
        "(" + rif("The VM bench") + "), keep the identity check, and run the whole of " + c("prove/all.sh") + " on each desktop; on Ubuntu the order that was followed was a full round on one desktop and a short "
        "check, then the owner's hand tests, on the others (" + rif("Testing") + ").",
        "<b>Run the package check</b> (" + c("check-package.py") + "): install, first start, remove, purge, reinstall. On Ubuntu it is not in the VM bench; it has to be run on a bench that can be reset, or by hand.",
        "<b>Write the manual from the code of the new distribution,</b> not by adapting the old one (register B5); and search for personal data in the finished package before publishing (register C3).",
    ]) + \
    warn("Do not add a branch for the new distribution to an existing tree. If code is shared, move it first; the trees must not need each other.")

# ── 20.6 ─────────────────────────────────────────────────────────────────────
S5 = p("RCP/1 is closed by design: a receiver that does not understand a message must close with the reason " + c("RCP_PROTOCOL_ERROR") + " (0x0B), and a "
       "capability used without having been negotiated is the same error (" + rif("The RCP/1 protocol") + "). So adding a message is a protocol change, "
       "with the page and the server changed together. The places to touch, in order:", lead=True) + \
    steps([
        "<b>Specify it first</b> in " + c("docs/RCP.md") + " (the message list of §7, the byte layout of §6, the version rules of §9) and in "
        + c("docs/SPECS.md") + " if it adds a promise. Decide whether it needs a capability in " + c("HELLO") + " and " + c("HERE_I_AM") + ".",
        "<b>The type number</b> in the right enumeration of " + c("src/rcp.c") + ": the control channel (low byte, e.g. " + c("T_TERMINATE_SESSION = 0x0011") + "), "
        "input (high byte 0x01), clipboard (0x02), video (0x03) or the audio datagram (0x0401). The same constant goes into the " + c("TYPE") + " table of "
        + c("src/page.html") + ".",
        "<b>The body length check.</b> " + c("measure_fields()") + " in " + c("rcp.c") + " reads the fields of a body before the message is acted on. A type missing "
        "from it falls into the default and the check after the switch sends the client away after the action (the comment above " + c("measure_fields()")
        + " records what that order cost with " + c("HELLO") + ", " + c("ATTACH") + " and " + c("CREDENTIALS") + "). For a fixed-size input message also update the lengths in the comment block of the input enum.",
        "<b>The handler</b> in the dispatch switch of the channel (the control handler holds " + c("case T_HELLO") + " to " + c("case T_TERMINATE_SESSION") + "). "
        "If it needs the host (the transport or a session), add a hook to the struct of function pointers in " + c("src/rcp.h") + ", with its comment, "
        "and connect it in " + c("webtransport.c") + " or " + c("main.c") + ". A function that is not a hook, like " + c("rcp_admitted_waiting()") + ", needs no wiring.",
        "<b>The rate class.</b> Messages that a client can send in a flood have a class in " + c("src/msgrate.h") + " (" + c("MC_POINTER") + " ... " + c("MC_FIT_CANVAS")
        + ", with a rate and a burst) and a mapping in " + c("control_class()") + " or " + c("lww_index()") + " in " + c("rcp.c") + ". A new message needs a "
        "decision: its own class, or one that is never dropped.",
        "<b>The page,</b> both directions: how it encodes or decodes the message, and what it does on an unexpected type. A server message the page does not know "
        "ends the session with " + c("PROTOCOL_ERROR") + ".",
        "<b>A farewell that must reach a client in every state</b> goes through " + c("wt_dismiss_user_session_over()") + " in " + c("webtransport.c") + ": it says the farewell at once to a client that is logged in, keeps it until the fixed second for a client that was already admitted, and skips a connection that "
        "is still waiting for PAM, so that a stranger trying passwords under that name learns nothing and nobody receives a false " + c("RCP_SESSION_TERMINATED") + ". It is the model of the farewells of this tree that end a session "
        "(" + c("RCP_SESSION_UNSERVABLE") + " when a stage is refused, " + c("RCP_SESSION_TERMINATED") + " at a Log Out).",
        "<b>Log lines</b> follow " + rif("Conventions") + " (the mark at the head of a body sets the journal priority).",
        "<b>A check:</b> a new name in an existing check, or a new check file (below). The test is the page driven by a real browser, so the page and the server "
        "are tested together.",
    ]) + \
    note("There is no unit-test harness for " + c("rcp.c") + " in this tree: the twin comparison and the benches that exercised the protocol alone were not carried "
         "over (" + rif("Build and release") + "). A protocol change is covered only by what the checks of " + c("prove/") + " exercise.", "No protocol-level tests.")

# ── 20.7 ─────────────────────────────────────────────────────────────────────
S6 = p("The product knows four desktops, by the enumeration " + c("DesktopSession") + " in " + c("src/session.h") + ". A fifth is a larger change than it looks, "
       "because the desktop appears in places beyond " + c("session.c") + ". The order that the code and its comments suggest:", lead=True) + \
    steps([
        "<b>Classify the family.</b> Capture, input, clipboard and remount talk to the compositor, not the desktop. XFCE and LXQt share labwc, a "
        "wlroots compositor, and " + c("session_on_wlroots()") + " answers \"is it the wlroots family\"; GNOME uses Mutter, and KDE uses KWin nested in our own labwc. A new desktop that "
        "runs on labwc reuses the whole wlroots path.",
        "<b>The enumeration.</b> Add the value to " + c("DesktopSession") + " at the END: the value travels as a " + c("uint32_t") + " between the parent and the "
        "child, and renumbering the existing ones would break that boundary.",
        "<b>Detection.</b> " + c("desktop_session()") + " in " + c("session.c") + " chooses by markers on the PATH, in a stated order (the comment lists the branches "
        "and why the order is not free), and " + c("desktop_of_session_name()") + " maps session names, including those of the Ubuntu flavours, where the order of the tests matters "
        "(a name that contains another is asked first). Add the marker and the name, and decide what happens "
        "when two desktops are installed (the code picks one and says so in the log).",
        "<b>The names of the desktop's session</b> as macros in " + c("session.h") + " (for XFCE, " + c("SESSION_PRIMARY_XFCE") + " and " + c("SESSION_BUS_XFCE")
        + "), and its Log Out command.",
        "<b>The places that branch on the desktop.</b> In " + c("child.c") + ", the birth of the session and the stage (the XFCE and LXQt wording and the KDE "
        "branch), and the close; in " + c("main.c") + ", the switch that names the desktop in the log; in " + c("session.c") + ", the branches that are specific to one desktop "
        "(for example the GNOME-only ones). Search for " + c("SESSION_DESKTOP_") + " to find all of them.",
        "<b>Packaging.</b> Recommends in " + c("debian/control") + " if the desktop needs a compositor package. If the compositor can be missing (a Recommends is not a Depends), make "
        + c("session_missing_component()") + " return its name: " + c("main.c") + " then answers 0x0E with the package's name before it spawns a child, and the " + c("postinst") + " warns when the "
        "desktop is installed alone.",
        "<b>The bench.</b> Add the desktop to the dictionaries that give the bench its ports: " + c("PORTS") + " in " + c("lib.py") + " (8821 to 8824 for the containers, 8841 to 8844 for the virtual machines "
        "chosen by " + c("RX_BANCO=vm") + "), " + c("box.sh") + " of the container bench and the one of " + c("prove/banco-vm/box.sh") + ", the " + c("boxes/Containerfile") + " and the identity check of the containers, or a new virtual machine in "
        + c("server/vm-radeon.sh") + ".",
        "<b>Tests.</b> Add the desktop to the dictionaries of the checks: " + c("PANEL") + " and " + c("LOGOUT") + " in " + c("deskkit.py") + ", " + c("PORTS")
        + " and " + c("SHELL_UP") + " in " + c("lib.py") + ", " + c("TERMINAL") + " and " + c("FILEMGR") + " in " + c("check-desktop.py") + " (on Ubuntu GNOME the terminal is " + c("ptyxis") + "), the desktop list in "
        + c("all.sh") + " and " + c("matrix.sh") + " (" + c("fresh.sh") + " takes the desktop as its argument). Then run the full suite on it.",
    ]) + \
    p("The four existing desktops are described in " + rif("The four desktops") + ". The comments in " + c("session.h") + " record what each addition cost: for "
      "example that, before LXQt, five places wrote the XFCE test directly, so the fifth value would have fallen into the GNOME and KDE branch silently.")

# ── 20.8 ─────────────────────────────────────────────────────────────────────
S7 = p("The chain is: card capability, encoder route, codec number in RCP, the offer in " + c("HERE_I_AM") + ", the page's decoder. Video encoding is described "
       "in " + rif("Video encoding") + "; for an addition:", lead=True) + \
    steps([
        "<b>Encoder.</b> Routes are chosen by capability when each encoder opens (" + c("h264_card") + " and " + c("hevc_card") + " in " + c("src/encoder.c") + ": "
        "Vulkan first, VA-API where Vulkan is not there). A codec needs an implementation on each route that can carry it (" + c("vadirect.c") + " for VA-API, "
        + c("vulkanvideo.c") + " for Vulkan) and an entry in the capability probe.",
        "<b>The measurement at start-up.</b> " + c("child_video_capabilities()") + " measures what the card encodes and the result becomes the offer: "
        + c("rcp_video_codec_set()") + ". With an empty list every " + c("HELLO") + " ends in " + c("RCP_NOTHING_IN_COMMON") + ".",
        "<b>The number in RCP.</b> Codec numbers are never reused: 1 is HEVC, 2 stays AV1 even though AV1 left the product, 3 is H.264 (the comment in "
        + c("page.html") + " gives the reason: an old client hearing a reused number would paint garbage without an error). " + c("RCP_CODEC_VIDEO_MAX")
        + " in " + c("rcp.h") + " bounds the list.",
        "<b>The page.</b> The tables " + c("CODEC_RCP") + " and " + c("CODEC_NAME") + ", the preference list " + c("PREFERENCE") + ", and the capability "
        "probe (the page asks the browser whether it can decode the codec string) in " + c("src/page.html") + ". The server decides in the end; the page's "
        "list is a preference.",
        "<b>The keyframe rules</b> of RCP §5.2 apply to every codec: the first frame after " + c("SESSION") + ", after a canvas change, and on request.",
        "<b>Tests.</b> The " + c("codec") + " check of " + c("check-media.py") + " reports the negotiated codec per browser and that it is hardware; a new codec "
        "needs its own expectation there and in the sharpness judge.",
    ]) + \
    note("HEVC is offered by the server but did not reach the pixel on the test browsers in the round of 19 Nov 2026 on Ubuntu (the page's probe refused every HEVC string, on "
         "Chrome and on Firefox: log " + c("media.out") + " of " + c("vm-gnome-unione10") + ", check " + c("codec") + "), as it did not on Debian 13 on 17 Nov 2026. Every recorded run negotiated H.264. HEVC decoding "
         "in a browser is therefore not demonstrated by the logs of either distribution. On a real machine of the owner the server logged \"HEVC: yes via vaapi\" (" + c("docs/STORIA-ubuntu-26.04.md") + "), which is the "
         "server's side only.", "State of HEVC.")

# ── 20.9 ─────────────────────────────────────────────────────────────────────
S8 = p("A check is cheap to write and expensive to trust. The conventions below are what the existing checks do (thirteen " + c("check-*.py") + " files; " + c("all.sh") + " runs fifteen steps of "
       "them, " + c("check-package.py") + " is run apart); a new check should do the same.", lead=True) + \
    steps([
        "<b>One file, one docstring.</b> Put the check in " + c("prove/check-<name>.py") + ". The docstring says what it proves, how to run it, the users it makes, "
        "and the verdict names. Define a " + c("NAMES") + " tuple.",
        "<b>Use the kit.</b> Build on " + c("lib.py") + ": " + c("Results") + " for verdict lines (" + c("attempt") + " turns an exception into FAIL or BLOCKED; "
        + c("sequence") + " runs the checks in order under a deadline), " + c("Rig") + " for compositor, browser, user and login, " + c("deskkit.py") + " to run things in the user's session.",
        "<b>FAIL is the product, BLOCKED is the tool.</b> Raise " + c("Fail") + " when the product did not do it; let a tool error surface as " + c("ToolError") + ". On the VM bench a check may also "
        "be reported as <b>SKIP</b> (it cannot be done there: the real login screen, other source addresses, the package check) or <b>NOTE</b>; neither is ever a PASS, and the runner's closing rule is that no check "
        "produced a pass by being left out.",
        "<b>Use a user prefix of its own</b> and add it to the pattern of " + c("lib.sweep()") + " so that sessions are ended at the end of " + c("all.sh") + " (the pattern lists the prefixes of every check).",
        "<b>Judge from inside the box.</b> Log what the application received (a test window), not what the browser was told to send. If a new window is "
        "needed, add it next to " + c("window.py") + ". Where the window itself may lose events (the GTK 4.22 case of register B3-bis), read the raw events.",
        "<b>Print evidence on the line.</b> The format is " + c("PASS|FAIL|BLOCKED <name> - evidence") + ", one line per name. A check that reads the journal must not "
        "write the string it looks for into the journal: the VM bench enters the machine as root by key and not with " + c("sudo") + ", because sudo logs each command line and the typed secret of a check "
        "(the false red of " + c("typed-names-not-logged") + " in the first full round on Ubuntu).",
        "<b>Register it in all.sh</b> with a time limit: " + c("run <label> <seconds> python3 check-<name>.py --box \"$DE\"") + ". A check that changes the box in "
        "a way that other checks must not see (like " + c("check-ban.py") + " and " + c("check-package.py") + ") goes last or outside. Use " + c("all.sh --only label,label") + " to repeat a part "
        "(the run says \"PARTIAL RUN\" and exits with 3 when everything passed but not everything ran).",
        "<b>Prove that it can say red.</b> A check that cannot fail is a net with no fish. The existing checks keep a " + c("--selftest") + " for the picture judge "
        "(" + c("base-check.py") + ") and report numbers in their evidence so that a pass can be read.",
        "<b>Record a limit honestly.</b> If the check is an emulation (the phone) or has a declared tool limit (AltGr), write it in the docstring.",
    ]) + \
    p("Running order and limits are in " + rif("Testing") + ".")

CHAPTER = ("Extending REMOTIX and porting to another distribution", [
    ("The one-distribution rule", S1),
    ("Where the code depends on the distribution", S2),
    ("What the clean-up removed, kept and risked", S3),
    ("Porting from Debian to Ubuntu: what changed in practice", S3B),
    ("A checklist for porting to another distribution", S4),
    ("Adding a message to RCP/1", S5),
    ("Adding a desktop", S6),
    ("Adding a video codec", S7),
    ("Adding a check to prove/", S8),
])
