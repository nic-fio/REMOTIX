"""Chapter 20 — Extending REMOTIX and porting to another distribution (Fedora 45 tree: the third port). Sources: the code of this tree
(src/session.c, src/session.h, src/kwin.c, src/main.c, src/child.c, src/walls.c, src/rcp.c, src/rcp.h, src/msgrate.h, src/page.html, src/encoder.c,
src/remotix-pam-hook, rpm/*, selinux/*, build/*, prove/*, server/*), docs/REGISTRO-problemi.md (entries F1 to F36 are Fedora's), PIANO.md (decisions
D1 to D8 and the log), studio/1 to 5, docs/INVENTARIO-non-debian.md and docs/PULIZIA-tranche1.md (both describe the Debian tree)."""
from build import c, h4, note, p, rif, steps, sysf, table, tip, ul, warn

# ── 20.1 ─────────────────────────────────────────────────────────────────────
S1 = p("REMOTIX exists in three trees of the repository, one folder per distribution: " + c("debian13/") + " (Debian 13, trixie), " + c("ubuntu26.04/") + " (Ubuntu 26.04 with its four "
       "flavours) and this one, " + c("fedora45/") + " (Fedora 45), version 1.2.0. Each is a self-contained copy with its own packaging, its own build, its own test bench and its own manuals; "
       "nothing is shared between them. This tree was started on 21 November 2026 as a copy of the Ubuntu one, and " + c("CLAUDE.md") + " states the rule: Fedora 45 only, no distribution "
       "detection, the other two folders are never touched. The rule that a port is a copy and not a new <code>if</code> in an old tree has now been followed twice, and this chapter is written "
       "from what the third port needed.", lead=True) + \
    p("Most of the code does not depend on the distribution at all: the transport, the RCP/1 protocol, capture, encoding, the budget, input, "
      "audio, clipboard, the page. Its dependencies are on the Linux kernel (DRM nodes, libei, PipeWire), on systemd and logind, on PAM and "
      "polkit, on the four desktops, on the mandatory access control of the distribution, and on a handful of facts that the next section lists. Measured against the Ubuntu tree, "
      "twelve files of " + c("src/") + " differ (" + c("child.c") + ", " + c("input.c") + ", " + c("kdehost.h") + ", " + c("kwin.c") + ", " + c("kwin.h") + ", " + c("main.c") + ", " + c("Makefile") + ", "
      + c("remotix.pam") + ", " + c("remotix-remote-sessions.rules") + ", " + c("session.c") + ", " + c("transport.c") + ", " + c("walls.c") + ") and four are new (" + c("remotix-pam-hook") + " and "
      "three files of " + c("protocols/") + "); the rest of " + c("src/") + " is identical, including the whole of the protocol, the capture, the encoder and the page. The packaging, the SELinux module "
      "and the test bench are new.") + \
    p("The product does not detect the distribution to choose a behaviour of its own. It does read, from the machine, what the machine offers: the session "
      "names that the display manager lists, the session that carries the distribution's name in " + sysf("/etc/os-release") + " (" + c("gnome_session()") + "), the markers "
      "of the installed desktops on the " + c("PATH") + " (" + rif("The four desktops") + ").") + \
    warn("A decision of an earlier port is no longer true to the letter. The Debian tree removed the code that only another distribution needed because it could not be reached on trixie; "
         "the Ubuntu tree needed part of it back; the Fedora tree needs the SELinux part (" + rif("What the clean-up removed, kept and risked") + "). A port must expect the same: removing code "
         "that is dead on one distribution is a loan, not a deletion.", "Removed code comes back.") + \
    note("The history of the clean-up is in two documents of " + c("docs/") + ": " + c("docs/INVENTARIO-non-debian.md") + " lists what existed only for another "
         "distribution, with a verdict per item; " + c("docs/PULIZIA-tranche1.md") + " records what tranche 1 removed on 17 Nov 2026 on the Debian tree. Both are inherited and describe the Debian "
         "tree; part of that code is live again here. Line numbers in the inventory are those of the tree before tranche 1 and no longer point to the right lines.", "Where the history is.")

# ── 20.2 ─────────────────────────────────────────────────────────────────────
S2 = p("The table lists what a porter must look at, area by area, as it is on Fedora 45 in this tree. The last column says how the Ubuntu tree differs, where it does: that is the "
       "comparison that a fourth port starts from. Names are files and functions, not line numbers.", lead=True) + \
    table(["Area", "Fedora 45 (this tree)", "Ubuntu 26.04, for comparison", "Where"], [
        "Packaging and build",
        ["package format", "an <code>.rpm</code> from " + c("rpm/remotix.spec") + ", with the standard macros (" + c("%selinux_modules_install") + ", " + c("%systemd_post") + ", " + c("%firewalld_reload") + ") and "
         "scriptlets instead of maintainer scripts: " + c("%pre") + " (refuses a first installation without a DRM render node and an account named remotix that belongs to a person), " + c("%post") + " (loads the SELinux "
         "module, runs " + c("systemd-sysusers") + " and " + c("systemd-tmpfiles") + " by itself, compiles " + sysf("/etc/dconf/db/remotix") + ", runs " + c("restorecon") + ", applies " + c("remotix-pam-hook") + ", "
         "runs " + c("--encoding-test h264") + " at the first installation, warns if labwc is missing, reloads firewalld), " + c("%preun") + " (closes the REMOTIX sessions and the service), " + c("%postun") + " "
         "(does everything that Debian's purge does: an RPM has no purge) and triggers on the display managers. Installed with " + c("sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm") + ", removed with " + c("sudo dnf remove remotix"),
         "a <code>.deb</code> through debhelper, maintainer scripts, a " + c("pam-auth-update") + " profile", c("rpm/remotix.spec")],
        ["system user", "the macro that turns " + c("sysusers.d") + " into package provides is switched off (" + c("%global __sysusers_path ^$") + ") so that " + c("%pre") + " can see whether an account named remotix was "
         "there before the package, and " + c("%post") + " runs " + c("systemd-sysusers remotix.conf") + " itself", "sysusers and tmpfiles from the postinst", c("rpm/remotix.spec") + ", " + c("rpm/remotix.sysusers")],
        ["dependency names", "Requires " + c("pam") + ", " + c("gawk") + ", " + c("systemd-pam") + ", " + c("shadow-utils") + ", " + c("systemd") + ", " + c("dbus-broker") + ", " + c("pipewire") + ", " + c("wireplumber") + ", "
         + c("firewalld-filesystem") + "; Recommends " + c("labwc") + ", " + c("dconf") + ", " + c("wlr-randr") + ", " + c("xorg-x11-server-Xwayland") + ", " + c("dejavu-sans-fonts") + ". There is no Recommends for the video drivers: "
         "the H.264 driver of the card is a requirement of the administrator (RPM Fusion, " + c("mesa-va-drivers-freeworld") + ", decision D1). BuildRequires include " + c("openssl-devel") + ", " + c("pam-devel") + ", " + c("libselinux-devel")
         + ", " + c("glib2-devel >= 2.80") + ", " + c("pipewire-devel") + ", " + c("libdrm-devel") + ", " + c("libva-devel") + ", " + c("opus-devel") + ", " + c("libei-devel >= 1.3.901") + ", " + c("libxkbcommon-devel") + ", "
         + c("mesa-libgbm-devel") + ", " + c("wayland-devel") + ", " + c("vulkan-headers") + ", " + c("vulkan-loader-devel") + ", " + c("systemd-rpm-macros") + ", " + c("firewalld-filesystem") + ". Fedora's OpenSSL is 4.0 (decision D8); "
         "the build script has no fallback to another OpenSSL",
         c("libpam-systemd") + " and the Debian names; Recommends " + c("va-driver-all") + ", " + c("mesa-vulkan-drivers") + ", " + c("labwc") + ", " + c("dconf"), c("rpm/remotix.spec")],
        ["build", "a virtual machine (" + c("costruzione") + "), no containers: " + c("build/build-rpm.sh") + " copies the tree there, installs the build dependencies, builds the static libraries ngtcp2 1.25.0 and nghttp3 1.18.0 once with "
         + c("build/quic-static.sh") + " (declared as " + c("Provides: bundled(...)") + "), runs " + c("rpmbuild -bb") + " and checks the package (R13: the bench feature is not in the binary; R4: nothing missing in " + c("ldd") + ", no dynamic ngtcp2 or nghttp3); "
         "the spec itself checks R13 and R24 in " + c("%build") + " and passes " + c("TWIN=none") + " to " + c("make") + ". No reproducibility check (R23) and no lintian-like check are in " + c("build-rpm.sh"),
         "a container image with apt, our own labwc built into the package", c("build/build-rpm.sh") + ", " + c("build/quic-static.sh")],
        ["package name", sysf("remotix-1.2.0-1.fc45.x86_64.rpm") + "; the spec says " + c("ExclusiveArch: x86_64 aarch64") + "; no source archive of labwc (the package contains none)", sysf("remotix_1.0.1-1+ubuntu26.04_amd64.deb") + " and the source of our labwc", c("rpm/remotix.spec")],
        ["install paths", c("/usr/libexec/remotix/remotix") + ", " + c("/usr/lib/firewalld/services/remotix.xml") + ", " + c("/etc/remotix/denied-users") + ", " + c("/usr/share/remotix/belts/") + " (the two belts left off), "
         + c("/usr/share/selinux/packages/remotix.pp.bz2") + ", " + c("/etc/needrestart/conf.d/remotix.conf") + " (only meaningful if needrestart is installed, which Fedora does not do by default)", c("/etc/ufw/applications.d") + ", " + c("/etc/apparmor.d"), c("rpm/remotix.spec")],
        ["service", "installed <b>off</b> (the Fedora preset is <code>disable *</code>; the administrator runs " + c("systemctl enable --now remotix") + "); " + c("ExecStartPre=-/usr/libexec/remotix/remotix-pam-hook check") + ", "
         + c("Environment=MESA_SHADER_CACHE_DISABLE=true") + " (the codec probe of the root side opened the Mesa cache in root's home), " + c("Restart=on-failure") + ", " + c("RestartSec=2") + ", " + c("RestartPreventExitStatus=78"),
         "the same without the pam hook and the Mesa line", c("rpm/remotix.service")],
        "Login and system integration",
        ["PAM service", "Fedora's " + sysf("/etc/pam.d/sshd") + " line by line, plus the exclusion of root (" + c("pam_listfile") + " with " + c("onerr=fail") + "): " + c("auth substack password-auth") + ", " + c("include postlogin") + ", " + c("pam_sepermit") + ", "
         + c("pam_selinux close/open env_params") + ", " + c("pam_namespace") + ", and TWO " + c("pam_env") + " lines, one of them reading " + sysf("/etc/locale.conf") + ". authselect generates " + c("system-auth") + " and " + c("password-auth") + ", so "
         "whatever the administrator chose with authselect (sssd, faillock) holds for REMOTIX as for ssh",
         "the file uses " + c("@include common-auth") + " and the other common files, which Fedora does not have", c("src/remotix.pam")],
        ["the local login closes the remote desktop", "the hook line cannot go into " + c("common-session") + " (authselect would rewrite it). It goes into the PAM files of the four login screens, by " + c("remotix-pam-hook") + " "
         "(" + c("DEFAULT_DMS=\"gdm plasmalogin lightdm sddm\"") + "): for gdm, plasmalogin and lightdm a file in " + sysf("/etc/pam.d") + " that copies the vendor's file from " + sysf("/usr/lib/pam.d") + " plus a marked block; "
         "for sddm, whose files are the package's own " + c("%config") + " files, the block is added in place. The line must stand after the first " + c("pam_selinux.so close") + " session line and before " + c("pam_selinux open") + " (else before the first " + c("session") + " line), "
         "because " + c("pam_selinux open") + " sets the context of the NEXT exec and a " + c("pam_exec") + " line after it would spend that exec on our program (F6). The script runs in " + c("%post") + ", in the triggers of the four "
         "login-screen packages (" + c("gdm") + ", " + c("lightdm") + ", " + c("sddm") + ", " + c("plasma-login-manager") + "), at every start of the service and in " + c("%preun") + "; it never touches the authselect links",
         "a " + c("pam-auth-update") + " profile that puts the line in " + c("common-session"), c("src/remotix-pam-hook") + ", " + c("rpm/remotix.spec")],
        ["PATH and language of the session", "Fedora has no " + sysf("/etc/environment") + ": if PAM gives no " + c("PATH") + ", the child falls back to " + c("~/.local/bin:~/bin:/usr/local/bin:/usr/bin") + " (F34). The language is the one the user chose in the "
         "desktop (AccountsService, read before the identity changes: " + c("child_locale_read()") + ") or the system's (" + sysf("/etc/locale.conf") + "); " + c("LC_*") + " and " + c("LANGUAGE") + " of the PAM environment are passed on, validated (F34, F35)",
         "the PATH comes from " + sysf("/etc/environment") + "; the language was the fallback " + c("C.UTF-8"), c("src/child.c") + ", " + c("src/session.c")],
        ["who is an administrator", "the polkit rules name " + c("wheel") + ", " + c("sudo") + " and " + c("admin") + "; on Fedora the group is " + c("wheel") + ". The remote-sessions rule grants one action more than Ubuntu's: " + c("org.freedesktop.fwupd.refresh-remote")
         + " (F3: GNOME Software asked for it at start and the password window covered the desktop)", "the same rule without the fwupd action", c("src/remotix-remote-sessions.rules")],
        ["power actions of logind", "nineteen actions forbidden (counted in the rule file: " + c("grep -c '\"org.freedesktop.login1' src/remotix-no-poweroff.rules") + "), the four " + c("set-reboot-*") + " that imply " + c("reboot") + " included; the check "
         + c("power-implied") + " passed on XFCE with systemd 262 (F33); on the other three desktops it has not been verified. The rule must sort BEFORE " + sysf("lightdm.rules") + ", which would give the user lightdm a yes on all of login1: tried (F33)",
         "the same file", c("src/remotix-no-poweroff.rules")],
        ["mandatory access control", "<b>SELinux, enforcing</b>, with the package's own module (" + c("selinux/remotix.te") + ", " + c(".fc") + ", " + c(".if") + "): the domains " + c("remotix_t") + " (root side), " + c("remotix_net_t") + " (network side, the wall) and "
         + c("remotix_hook_t") + " (the local-login hook), and the file types " + c("remotix_exec_t") + ", " + c("remotix_dconf_db_t") + ", " + c("remotix_prelocal_t") + ". The root side writes the context of the network side into "
         + sysf("/proc/thread-self/attr/exec") + " before its " + c("execve") + " (" + c("walls.c") + "). Protection off is a note and the start goes on; loaded and refused means the network side does not start (F24). With SELinux on, any error in making the context of a "
         "login <b>refuses</b> the login (exit codes 44 to 47 of the child, " + c("child.c") + "). The Makefile links " + c("-lselinux"),
         "AppArmor, profile in complain mode", c("selinux/remotix.te") + ", " + c("src/walls.c") + ", " + c("src/child.c")],
        ["firewall", "a firewalld service <b>remotix</b> (7447 TCP and UDP), defined and never opened by the package (decision D5). The administrator opens the port: " + c("sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload") + ". The "
         "package runs " + c("%firewalld_reload") + " so that the definition is known at once. The XML must be well formed (a double hyphen in a comment made firewalld refuse it: F17)",
         "an ufw application profile, off by default", c("rpm/remotix.firewalld.xml")],
        ["video drivers", "the H.264 encoding on the card is REQUIRED; on Fedora the base repositories lack the driver, so the administrator enables RPM Fusion and installs " + c("mesa-va-drivers-freeworld") + " (NVIDIA: its own driver). The " + c("%post") + " says so if the "
         "test frame is not encoded", "the drivers come with the distribution", c("rpm/remotix.spec")],
        ["first connection", "adds the user to the group that owns the render nodes and, for a user manager born earlier, an ACL for the private group; the grant code (" + c("render_grant.c") + ") is identical to Ubuntu's. Which group owns the nodes on "
         "Fedora has not been verified here", "the group " + c("render") + " created by udev", c("src/child.c") + ", " + c("src/render_grant.c")],
        "Desktops",
        ["display managers", "gdm (GNOME), plasmalogin (KDE), lightdm (XFCE), sddm (LXQt). The readers of the active display manager in " + c("session.c") + " know lightdm, sddm and " + c("gdm3") + ": how the Fedora names " + c("gdm") + " and " + c("plasmalogin")
         + " are treated there has not been verified in detail (lightdm and sddm are the ones used for XFCE and LXQt)", "gdm3, lightdm, sddm", c("src/session.c")],
        ["which desktop is installed", "the markers on the PATH and " + c("desktop_of_session_name()") + " are the code of the Ubuntu tree; the Ubuntu flavour names stay in the map and are simply not met on Fedora. The session names of Fedora ("
         + c("gnome") + ", " + c("plasma") + ", " + c("xfce") + ", " + c("lxqt") + ") contain the keywords the function asks for; they were not checked one by one against the session files", "the flavours are asked BEFORE " + c("ubuntu"), c("src/session.c")],
        ["GNOME", "GNOME 51 (mutter 51.0, gdm 51.0 then 51.1.1 on the test machines); the session unit has the same shape as GNOME 50's (the template unit with an instance; PIANO.md), not examined further. " + c("gnome_session()") + " chooses the session that bears the "
         "distribution's name, else " + c("gnome") + ". Mutter's first absolute pointer movement arrives with one coordinate at 0, cured in " + c("input.c") + " (F34)", "GNOME 50, session " + c("ubuntu"), c("src/session.c") + ", " + c("src/input.c")],
        ["KDE", "<b>KWin 6.8 alone</b>, no labwc of ours (decision D2): the drop-in of the user unit " + sysf("plasma-kwin_wayland.service") + " replaces its " + c("ExecStart") + " with " + c("remotix --kwin-virtual W H -- <kwin_wayland_wrapper> --virtual ...") + ". The size of the output "
         "is changed through " + c("kde_output_management_v2") + " version 22 or later (" + c("kwin_output_resize()") + ", the two protocol files of " + c("src/protocols/") + "); if KWin lacks it the session is refused with a clear message (F7). KWin remembers the last "
         "mode of " + c("Virtual-0") + " in " + sysf("~/.config/kwinoutputconfig.json") + ", so the child corrects the size at birth before it mounts the stream (F8). The mark \"this KWin is REMOTIX's\" is " + c("--kwin-virtual") + " on the command line and " + c("REMOTIX_KDE_HOST=1") + " in the environment (" + c("kdehost.h") + ")",
         "KWin nested in OUR labwc (a patched build), KWin 6.6.7", c("src/kwin.c") + ", " + c("src/kdehost.h") + ", " + c("src/session.c")],
        ["XFCE and LXQt", "the labwc of Fedora (0.20.2) with " + c("wlr-randr") + " 0.5.0; the " + c("rc.xml") + " of REMOTIX needed no change (F22, F33). XFCE 4.20 draws a black background without icons (xfdesktop is not built with Wayland support: decision D7, a declared limit). LXQt 2.4 has no qlipper: "
         "the clipboard goes through the data-control protocol of labwc", "labwc 0.9.3", c("src/wlroots.c")],
        ["compositor component missing", c("session_missing_component()") + " names " + c("labwc") + " for XFCE and LXQt (unchanged), and the " + c("%post") + " warns when labwc is absent on a machine whose desktop is XFCE or LXQt", "the same, in the postinst", c("src/session.c") + ", " + c("rpm/remotix.spec")],
        ["settings that programs read themselves", "no snap and no Flutter programs on Fedora; Flatpak programs start with nothing special (PIANO.md; the owner did not try them). The dconf model is the same, but the root side compiles into " + sysf("/run/remotix/dconf-compile.tmp") + " (a type of ours) and creates in " + sysf("/etc/dconf/db")
         + " only two fixed names, with type transitions by name (F24)", "snap and Flutter programs have their own dconf reader (register C5)", c("src/session.c")],
        "Test machinery",
        ["bench", "<b>virtual machines only</b>: four Fedora 45 VMs (" + c("gnome") + ", " + c("kde") + ", " + c("xfce") + ", " + c("lxqt") + ", ssh on ports 2351 to 2354, REMOTIX on 8851 to 8854) and the build VM (ssh 2355), with the server's Radeon passed through to one of them at a time "
         "(" + rif("The VM bench") + "); no containers, by the owner's order. The server's folder is " + sysf("/media/REMOTIX-FEDORA") + ". " + c("RX_BANCO=vm") + " selects the bench", "the same four VMs, with the Ubuntu images; containers kept in the tree but not the release bench",
         c("server/vm-radeon.sh") + ", " + c("prove/banco-vm/box.sh") + ", " + c("prove/lib.py")],
        ["the local login on the bench", "lightdm and sddm get an autologin written by " + c("prove/banco-vm/autologin-lightdm.sh") + " and " + c("autologin-sddm.sh") + " (bench only), for " + c("prove/prelocal.sh"), "none", c("prove/prelocal.sh")],
        ["tests of the package", c("prove/check-package.py") + " has not been run on Fedora; the installation, the update and the removal with " + c("dnf") + " were tried by hand (F6, F19, F21, F24)", "declared SKIP on the VM bench", c("prove/all.sh")],
    ], "«TAB» — Where the code depends on the distribution (Fedora 45, with Ubuntu 26.04 for comparison)") + \
    p("The state of each item on the Debian tree (removed, left, or to be removed later) is in " + c("docs/INVENTARIO-non-debian.md") + ", section \"Status after tranche 1\".")

# ── 20.3 ─────────────────────────────────────────────────────────────────────
S3 = p("The Debian tree removed, on 17 Nov 2026, the code that could not be reached on trixie (" + c("docs/PULIZIA-tranche1.md") + "). Each later port met some of those problems again: "
       "the table says, item by item, what came back in the Ubuntu and Fedora trees.", lead=True) + \
    table(["Removed on Debian", "What it did", "On the Ubuntu tree", "On the Fedora tree"], [
        ["SELinux handling in " + c("child.c") + " and " + c("walls.c"), "set the SELinux level of a login like sshd; set the exec context of the network side; the " + c("-ldl") + " link flag",
         "still absent", "<b>back</b>, and larger: " + c("selinux_exec_like_local_login()") + " and " + c("selinux_exec_checked()") + " in " + c("child.c") + " (exit codes 44 to 47), the wall of " + c("remotix_net_t") + " in " + c("walls.c") + ", " + c("-lselinux") + " in the Makefile and "
         + c("libselinux-devel") + " in the spec"],
        ["Ubuntu session names in " + c("desktop_of_session_name()"), "mapped " + c("xubuntu") + ", " + c("lubuntu") + ", " + c("kubuntu") + ", " + c("ubuntu"),
         "<b>back</b>, with the order that matters", "alive but not needed: the code is identical and the Fedora names match the other keywords"],
        ["os-release match in " + c("gnome_session()"), "chose a gnome-session whose name equals os-release ID", "<b>back</b>", "alive; on Fedora the choice falls on " + c("gnome") + " when no session bears the name of the distribution"],
        ["the GNOME 50 template branch of " + c("unit_shell()"), "handled the template unit " + sysf("org.gnome.Shell@.service"),
         "<b>back</b>, and the only branch", "the same code, with GNOME 51"],
        ["D-153 folder discovery (the session as a local login gives it)", "used Ubuntu's " + sysf("Xsession.d/60x11-common_xdg_path") + " mechanism; " + c("local_session()")
         + " then returned an empty structure", "<b>back</b>", "the same code (not examined further on Fedora)"],
        ["the EI-ping build switch, the fallback", "built without input receipts for libei older than 1.3.901", "still removed", "still removed: the minimum stays " + c("libei-1.0:1.3.901") + " in " + c("MINIMI") + " of the Makefile"],
        ["the own-labwc build switch and the " + c("LABWC=") + " knob of the Makefile", "the patched or own labwc path",
         "<b>back</b>, as a fixed build-time path for KDE", "<b>dead again</b>: " + c("REMOTIX_LABWC") + " is left in the Makefile as an orphan string and the labwc-for-KDE code of " + c("kwin.c") + ", " + c("kwin.h") + ", " + c("child.c") + " and " + c("main.c") + " cannot be reached (F7); "
         "its removal is planned for after the owner's tests (" + c("studio/5-kde-progetto.md") + ")"],
        ["the 90-default-privs branch of " + c("remotix-polkit-seated"), "openSUSE's polkit-default-privs", "still absent", "still absent"],
        ["1.0 to 1.5 upgrade machinery", c("remotix-net-move") + ", the non-split unit and tmpfiles", "still absent", "still absent"],
    ], "«TAB» — What the Debian clean-up removed and what came back on Ubuntu and Fedora") + \
    h4("What stays and why") + \
    ul([
        "The " + sysf("/usr/lib/pam.d") + " lookup of " + c("look_pam_service()") + ": " + sysf("/usr/lib/pam.d") + " is a real PAM vendor "
        "directory (on Fedora it holds the files of gdm, plasmalogin and lightdm that the hook copies), so the lookup is not dead. The text of the message itself speaks only of Fedora since 25 Nov 2026.",
        "The " + c("pam_selinux") + " lines of " + c("remotix.pam") + ": on Fedora they are functional, not a mirror (F2).",
        "The lightdm and sddm readers and " + c("declared_desktop()") + ": on Fedora, XFCE and LXQt use them.",
        "The KWin workarounds: runtime probes, not version tests.",
        c("wheel") + ", " + c("sudo") + " and " + c("admin") + " in the polkit rule: logic, kept (Fedora's group is " + c("wheel") + ").",
        "The " + c("--no-split") + " run-time option and " + c("TWIN") + " in the Makefile: the spec passes " + c("TWIN=none") + ".",
        "Several header comments that mention other distributions.",
    ]) + \
    h4("Risks recorded by tranche 1, and where they stand") + \
    ul([
        "The session-folder lookup that imitated a local login (D-153) relied on x11-common not shipping " + c("60x11-common_xdg_path") + ": the code is the one of the Ubuntu tree and was not examined on Fedora.",
        "An administrator who installs SELinux finds no SELinux handling in REMOTIX on the Debian and Ubuntu trees: <b>false on Fedora</b>, where the handling is back and SELinux is always enforcing.",
        "A build against libei older than 1.3.901 fails at " + c("make deps") + " by design.",
        "On a removal (" + c("dnf remove") + ") the " + c("%postun") + " scriptlet deletes the certificates and the ban list, the service directories, the product files in the users' homes by name, and the dconf database (an RPM has no purge, so it does what Debian's purge does); a check of where the certificates are after a removal was not run on Fedora.",
    ]) + \
    p("What tranche 2 listed as still to do (the remaining Ubuntu and Xubuntu detection in " + c("session.c") + ", the emulation of a local login's " + c("XDG_*")
      + " variables) is live code in this tree and is described in " + rif("The four desktops") + ", not left as work. Comments naming other distributions, and the other "
      "cosmetic items, are in " + rif("Appendix C — Known issues and open points") + ".")

# ── 20.4 ─────────────────────────────────────────────────────────────────────
S3B = p("This section is the experience of the third port, taken from the problem register (" + c("docs/REGISTRO-problemi.md") + ", entries F1 to F36) and from the plan (" + c("PIANO.md") + "). It lists what had to change on the way from the Ubuntu tree to Fedora 45, "
        "and what the Fedora port found that the earlier ones had not. The lessons of the second port (Ubuntu) are in the register of that tree.", lead=True) + \
    table(["Subject", "What changed in practice", "Register"], [
        ["GNOME 51 and the settings", "GNOME 51 with the session unit of GNOME 50's shape; the dconf database compiled into a run folder of the product and installed by name; the first pointer movement doubled; the language and the PATH of the session", "F34, F35"],
        ["KDE", "KWin 6.8 alone on a virtual output, no labwc of ours; the size changed through the KDE output protocol; the size remembered by KWin corrected at birth; a clean refusal if the protocol is missing; a declared fallback if KWin is slow", "F7, F8, F13, F14"],
        ["SELinux instead of AppArmor", "a module of the package with three domains; the context of the user's session worked out like a local login's; the wall of the network side with a negative test; the rights of the root side narrowed and every one explained in the " + c(".te") + "; confined SELinux users", "F2, F5, F24 to F33"],
        ["the local login closes the remote desktop", "the hook put into the PAM files of the four login screens, kept right across updates (the " + c(".rpmnew") + " of sddm), and the forced close of KDE", "F6, F9, F18, F19, F21, F36"],
        ["firewalld", "a service definition that is never opened; the XML validity; the reload", "F17, F20"],
        ["the RPM package", "the scriptlets, the triggers, the sysusers handling, the removal that leaves the system clean", "F1, F21, F24"],
        ["language and PATH", "no " + sysf("/etc/environment") + ": before the cure the remote session had " + c("LANG=C.UTF-8") + " and a shorter PATH than a local login", "F4, F34, F35"],
        ["XFCE background", "xfdesktop built without Wayland: a black background and no icons, a declared limit", "F22, decision D7"],
        ["keyring", "no PAM module that opens the keyring (decision D6, as on Debian and Ubuntu: no new function, and the difference from a local login is declared in the manuals)", "decision D6"],
    ], "«TAB» — What the port to Fedora changed in practice") + \
    h4("What a third port found that the first two did not") + \
    p("Some of these lessons came only because the tests were run on a real machine at the end. Each cost a failure in front of the owner or a careful second look.") + \
    table(["Lesson", "What happened on Fedora", "What to do on a new distribution"], [
        ["Try it on a real machine, with programs open",
         "On 25 November 2026, the first test of the owner on a real machine booted from the KDE live stick failed: with Konsole and top open in the remote desktop, a local login left the remote desktop alive and the local desktop started without a compositor. The automatic check had opened an "
         "empty remote desktop, so the orderly close always worked and the forced one never ran, and the SELinux wall was never asked (F36)",
         "Try \"the local login closes the remote desktop\" ALWAYS with programs open in the remote desktop (one that closes by itself and one that asks for confirmation), on a real machine before publishing; look at which unit the compositor and the panel are tied to (" + c("systemctl --user show -p PartOf") + ") and at the SELinux label of the unit files that the root side must stop"],
        ["The line of the login screen must come first",
         "On Fedora the hook line has to stand after the first " + c("pam_selinux.so close") + " session line and before " + c("pam_selinux open") + " (else before the first " + c("session") + " line), not after " + c("pam_systemd") + ": " + c("pam_selinux open") + " sets the context of the next exec, and a " + c("pam_exec") + " line after it spends that exec on our program (F6)",
         "Try every login screen with a real password before switching it on"],
        ["Check the XML you ship",
         "firewalld refused the service file because a comment had a double hyphen; so the service did not exist and the port could not be opened (F17)", "Read every shipped XML with a parser and load it in the real daemon"],
        ["The client's clock",
         "A client whose clock was an hour behind got \"Opening handshake failed\": the session certificate has " + c("notBefore") + " = now minus 3600 s (" + c("certificates.c") + "). The cause was found only after " + c("close_why()") + " put the TLS alert into the log (F23)",
         "Say in the log who closed a connection and why, and in the manual ask for a right clock on the device"],
        ["A cure born on one distribution that is good for all",
         "The language, the PATH and the first-click cure were found on Fedora but live in code shared by every distribution. They were applied to the Fedora tree only and the others wait for a plan (" + c("PIANO-1.0.2-debian-ubuntu.md") + ")",
         "Do not apply a cure to a tree that is not the one you are working on without the owner's plan; list the difference and carry it later (the rule of uniform behaviour)"],
        ["Test a SELinux rule in enforcing",
         "The search for missing rules in permissive mode with the dontaudit rules switched off LOSES lines (sys_admin and fsetid did not appear); the rules have to be verified in enforcing, with the policy as it is (F28)",
         "Prove a rule in enforcing; use the negative test of the wall (" + c("prove/wall-selinux.sh") + ") and read the journal with " + c("journalctl -b -g avc:") + ", because " + c("ausearch") + " saw nothing on the VMs even when the journal held the lines (F24)"],
        ["A check can hide a defect",
         c("giro-selinux.sh") + " hides a dead check halfway and the failing rows of the old rounds were partly defects of the bench (a missing Chromium, a helper process of Plasma); each was classified before it was archived (F33)",
         "Classify every red row as product or bench before archiving it"],
    ], "«TAB» — Lessons of the third port") + \
    note("A class of programs that read the settings themselves (snap and Flutter programs) existed on Ubuntu and does not on Fedora; Flatpak programs start with nothing special, but the owner did not try them. A port to a distribution with those programs should test them inside the remote session.", "A class of programs.")

# ── 20.5 ─────────────────────────────────────────────────────────────────────
S4 = p("The tree is not a template for a port, but the porting questions are now known from three ports. The list below is derived from the table above and "
       "from the register; it has been exercised twice, for Ubuntu 26.04 and for Fedora 45, and is the order in which those ports met their problems.", lead=True) + \
    steps([
        "<b>Start from a copy,</b> not from a branch of an existing tree: each tree has its own packaging, " + c("build/") + ", " + c("prove/") + " and " + c("manuals/") + ", and the rule of the repository is one folder per distribution.",
        "<b>Check the library minimums</b> in " + c("src/Makefile") + " (" + c("MINIMI") + "): OpenSSL 3.5 or newer (Fedora carries 4.0, decision D8), GLib 2.80, libei 1.3.901, "
        "PipeWire, libva, Vulkan loader 1.3.274. The QUIC libraries are built from source whatever the distribution carries.",
        "<b>Rewrite the package</b> for the new format: dependency names, install paths, scriptlets or maintainer scripts. Keep the guards (R13: the bench feature is not in the binary; R24: the static libraries are the declared version) and the checks of the build script (R4, R13) "
        "as requirements, however they are implemented (on Fedora they are in " + c("rpm/remotix.spec") + " " + c("%build") + " and in " + c("build/build-rpm.sh") + ").",
        "<b>Write the PAM service file</b> for that distribution's stack. Without the file, Linux-PAM falls back to the service " + c("other") + ", and what "
        + c("other") + " does depends on the distribution (on Fedora it is a hard deny, so every right password is refused). The program checks "
        "the file at start-up (" + c("main.c") + "). On Fedora take sshd's file and add only what REMOTIX needs. Look at where the session's " + c("PATH") + " and language come from.",
        "<b>The hook of the local login.</b> Find out how the distribution generates its PAM files (on Fedora, authselect: never touch the links), and put the line into the files of the login screens. The line must stand after the first " + c("pam_selinux.so close") + " session line and before " + c("pam_selinux open") + " on Fedora (else before the first " + c("session") + " line) (F6). Provide for the "
        "updates of the login-screen packages (triggers) and for a file that the package declares " + c("%config") + " (F21).",
        "<b>Check polkit.</b> The rules directory; the groups that polkit calls administrator (" + c("wheel") + " on Fedora); whether a default privilege table overrides the rules; the order against the rules of the login screen (lightdm); and the <b>implications</b> "
        "of the policy files of that systemd version (run " + c("power-implied") + "; the list of forbidden actions is 19 in this tree and must be derived again on any new distribution; on Fedora the check passed on XFCE only).",
        "<b>Check the display manager and the session names</b> the desktops register, against " + c("desktop_session()") + ", " + c("gnome_session()") + " and the readers in " + c("session.c")
        + ". Check the order of the substring tests: a name that contains another must be asked first.",
        "<b>Mandatory access control.</b> If SELinux is on (Fedora): ship a module, give the root side and the network side their domains, write every right with its reason, test in enforcing (never with " + c("permissive") + " or " + c("semodule -DB") + "), run the negative test of the wall "
        "(" + c("prove/wall-selinux.sh") + ", " + c("wall-neg-domain.py") + ", " + c("wall-sesearch.sh") + ") and look for AVC lines with " + c("journalctl -b -g avc:") + ". Try the confined SELinux users too. For AppArmor, adapt the profile and write every <code>deny</code> with its operations.",
        "<b>Firewall.</b> Define the service for the distribution's firewall and do not open it; write in the manual the line that the administrator runs.",
        "<b>Check the programs that read the settings themselves</b> (snap, Flutter, Flatpak): open them in a remote session and read the log of the session for settings errors.",
        "<b>Check the compositor</b> at the version the distribution carries, and the four desktops' versions, in particular the GNOME session unit shape, the KWin version (Fedora: KWin 6.8 alone) and whether the labwc of the distribution is good for XFCE and LXQt (Fedora: 0.20.2, no change to " + c("rc.xml") + ").",
        "<b>Make the bench.</b> Use virtual machines installed from the desktop images "
        "(" + rif("The VM bench") + "), with the video card passed through, no containers; run the whole of " + c("prove/all.sh") + " and the checks specific to each desktop; and then <b>try it on a real machine</b> booted from a live image, with programs open in the remote desktop (" + rif("Testing") + ").",
        "<b>Run the package check</b> (" + c("check-package.py") + "): install, first start, remove, reinstall. On Fedora it has not been run; installation, update and removal were tried by hand with " + c("dnf") + ".",
        "<b>Write the manual from the code of the new distribution,</b> not by adapting the old one; give every closed or postponed problem an entry in the register; and search for personal data in the finished package before publishing.",
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
        "wlroots compositor, and " + c("session_on_wlroots()") + " answers \"is it the wlroots family\"; GNOME uses Mutter, and KDE uses KWin alone (" + c("--kwin-virtual") + "). A new desktop that "
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
        "<b>Packaging.</b> Recommends in " + c("rpm/remotix.spec") + " if the desktop needs a compositor package. If the compositor can be missing (a Recommends is not a Depends), make "
        + c("session_missing_component()") + " return its name: " + c("main.c") + " then answers 0x0E with the package's name before it spawns a child, and the " + c("%post") + " scriptlet warns when the "
        "desktop is installed alone. A desktop has a login screen of its own: add it to " + c("DEFAULT_DMS") + " of " + c("remotix-pam-hook") + " and to the triggers of the spec, and try \"the local login closes the remote desktop\" on it (F6). If the desktop's units must be stopped by the root side, SELinux needs a rule for them (F36: " + c("allow remotix_t xdm_unit_file_t:service { stop status }") + " in " + c("selinux/remotix.te") + ").",
        "<b>The bench.</b> Add the desktop to the dictionaries that give the bench its ports: " + c("PORTS") + " in " + c("lib.py") + " (8851 to 8854 for the VM bench chosen by " + c("RX_BANCO=vm") + "), the script " + c("prove/banco-vm/box.sh") + ", and a new virtual machine in " + c("server/vm-radeon.sh") + " (live image, ssh and REMOTIX ports, display manager).",
        "<b>Tests.</b> Add the desktop to the dictionaries of the checks: " + c("PANEL") + " and " + c("LOGOUT") + " in " + c("deskkit.py") + ", " + c("PORTS")
        + " and " + c("SHELL_UP") + " in " + c("lib.py") + ", " + c("TERMINAL") + " and " + c("FILEMGR") + " in " + c("check-desktop.py") + " (for GNOME the dictionary says " + c("ptyxis") + "; not verified on Fedora), the desktop list in "
        + c("all.sh") + " and " + c("matrix.sh") + " (" + c("fresh.sh") + " takes the desktop as its argument). Add the checks of the new desktop (for KDE: " + c("check-kde-birth.py") + ", " + c("check-kde-live.py") + ", " + c("check-kde-resize.py") + ", " + c("check-kde-exit.py") + "; for XFCE and LXQt: " + c("check-resize.py") + ", " + c("check-exit.py") + ") and the real local-login tests (" + c("prove/prelocal.sh") + ", " + c("check-prelocal.py") + "). Then run the full suite on it.",
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
    note("HEVC is offered by the server, but on Fedora only H.264 was tried. HEVC decoding in a browser was not demonstrated on Debian 13 or on Ubuntu 26.04 either (the page's probe refused every HEVC string on the test browsers). "
         "On Fedora the H.264 driver comes from RPM Fusion (decision D1), and " + c("--encoding-test h264") + " was hardware, through " + c("h264_vulkan") + " on the Radeon (F35); on the real machine of 25 November 2026 it also succeeded on the Intel card (PIANO.md).", "State of HEVC.")

# ── 20.9 ─────────────────────────────────────────────────────────────────────
S8 = p("A check is cheap to write and expensive to trust. The conventions below are what the existing checks do (nineteen " + c("check-*.py") + " files, the six of KDE, XFCE and LXQt resizing and exit among them, which " + c("all.sh") + " does not run; " + c("all.sh") + " has sixteen labels; fifteen run checks, the sixteenth (" + c("package") + ") is only a declared SKIP); a new check should do the same.", lead=True) + \
    steps([
        "<b>One file, one docstring.</b> Put the check in " + c("prove/check-<name>.py") + ". The docstring says what it proves, how to run it, the users it makes, "
        "and the verdict names. Define a " + c("NAMES") + " tuple.",
        "<b>Use the kit.</b> Build on " + c("lib.py") + ": " + c("Results") + " for verdict lines (" + c("attempt") + " turns an exception into FAIL or BLOCKED; "
        + c("sequence") + " runs the checks in order under a deadline), " + c("Rig") + " for compositor, browser, user and login, " + c("deskkit.py") + " to run things in the user's session.",
        "<b>FAIL is the product, BLOCKED is the tool.</b> Raise " + c("Fail") + " when the product did not do it; let a tool error surface as " + c("ToolError") + ". On the VM bench a check may also "
        "be reported as <b>SKIP</b> (it cannot be done there: the real login screen, other source addresses, the package check) or <b>NOTE</b>; neither is ever a PASS, and the runner's closing rule is that no check "
        "produced a pass by being left out.",
        "<b>Use a user prefix of its own</b> and add it to the pattern of " + c("lib.sweep()") + " so that sessions are ended at the end of " + c("all.sh") + " (the pattern lists the prefixes of every check; whether the checks added on Fedora are in it was not verified).",
        "<b>Judge from inside the box.</b> Log what the application received (a test window), not what the browser was told to send. If a new window is "
        "needed, add it next to " + c("window.py") + ". Where the window itself may lose events (the GTK 4.22 case of register B3-bis, found on Ubuntu), read the raw events.",
        "<b>Print evidence on the line.</b> The format is " + c("PASS|FAIL|BLOCKED <name> - evidence") + ", one line per name. A check that reads the journal must not "
        "write the string it looks for into the journal: the VM bench enters the machine as root by key and not with " + c("sudo") + ", because sudo logs each command line and the typed secret of a check.",
        "<b>Register it in all.sh</b> with a time limit: " + c("run <label> <seconds> python3 check-<name>.py --box \"$DE\"") + ". A check that changes the box in "
        "a way that other checks must not see (like " + c("check-ban.py") + " and " + c("check-package.py") + ") goes last or outside. Use " + c("all.sh --only label,label") + " to repeat a part "
        "(the run says \"PARTIAL RUN\" and exits with 3 when everything passed but not everything ran).",
        "<b>Prove that it can say red.</b> A check that cannot fail is a net with no fish. The existing checks keep a " + c("--selftest") + " for the picture judge "
        "(" + c("base-check.py") + ") and report numbers in their evidence so that a pass can be read.",
        "<b>Tools of the Fedora bench that are not checks.</b> " + c("giro-selinux.sh") + " (all the checks of one desktop on one VM, SELinux step), " + c("giro-xfce-radeon.sh") + " and " + c("giro-lxqt-radeon.sh") + ", " + c("hold.py") + " and " + c("hold-user.py") + " (log in and stay, to look from outside; without " + c("RX_KEEP=1") + " the end of " + c("hold.py") + " closes ALL the sessions of the user, the local one too: F22), and the SELinux wall tests. " + c("check-prelocal.py") + " runs P1 to P8 (P6 checks that the hook line is BEFORE " + c("pam_selinux open") + " in the files of every login screen; P7 opens a terminal with " + c("top") + ", P8 an editor with unsaved text: F36).",
        "<b>Record a limit honestly.</b> If the check is an emulation (the phone) or has a declared tool limit (AltGr), write it in the docstring.",
    ]) + \
    p("Running order and limits are in " + rif("Testing") + ".")

CHAPTER = ("Extending REMOTIX and porting to another distribution", [
    ("The one-distribution rule", S1),
    ("Where the code depends on the distribution", S2),
    ("What the clean-up removed, kept and risked", S3),
    ("Porting to Fedora: what changed in practice", S3B),
    ("A checklist for porting to another distribution", S4),
    ("Adding a message to RCP/1", S5),
    ("Adding a desktop", S6),
    ("Adding a video codec", S7),
    ("Adding a check to prove/", S8),
])
