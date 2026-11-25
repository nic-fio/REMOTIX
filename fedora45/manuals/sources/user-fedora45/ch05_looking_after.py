"""User Manual, chapter 5 — looking after an installation (Fedora 45).
Sources: rpm/remotix.spec (%files, scriptlets, triggers), rpm/remotix.service, rpm/remotix.conf, rpm/remotix.sysusers,
rpm/remotix.tmpfiles, rpm/remotix.firewalld.xml, rpm/needrestart.conf, selinux/remotix.te and .fc,
src/main.c (options and defaults), src/child.c (group enrolment), src/render_grant.c, src/session.c,
src/remotix-*.rules, src/remotix-pam-hook, docs/SPECS.md §4.1, §5.2, §5.4, PIANO.md and docs/REGISTRO-problemi.md
(F6, F19, F20, F24, F36); the technical manual of this tree."""
from build import c, note, p, rif, sysf, table, term, tree, ui, ul, warn

S_SERVICE = p("REMOTIX is one systemd service called <b>remotix</b>. It is installed switched off and not started "
              "(see " + rif("Fedora 45: installing") + "): Fedora's own rule is that a new service starts "
              "switched off.", lead=True) + \
    term("$ sudo systemctl enable --now remotix     # start now and at every boot\n"
         "$ sudo systemctl disable --now remotix    # stop now and do not start at boot\n"
         "$ sudo systemctl restart remotix          # restart: closes the desktops (see below)\n"
         "$ systemctl status remotix                # is it running?", "The service") + \
    ul([
        "As installed it listens on all the machine's IPv4 addresses, on <b>TCP and UDP 7447</b>: the page and "
        "the sign-in over TCP, the video and the keys over UDP.",
        "It is started as root, because it has to check passwords and create the users' desktops. The part that "
        "talks to the network runs as the unprivileged user <code class=\"sys\">remotix</code>, which "
        "writes only in its own data folders (" + sysf("/var/lib/remotix/net") + " and " + sysf("/run/remotix/net")
        + ").",
        "If the service stops by itself because of a fault it is started again after two seconds. If it cannot "
        "start because of a wrong setting (status 78), it is not retried: read the journal.",
        "Stopping or restarting it closes the people's desktops: see " + rif("What a restart of the service does") + ".",
    ])

S_RESTART = p("<b>What a restart of the service does to people at work.</b> Stopping, restarting or upgrading the "
              "service <b>closes every remote desktop and its programs</b>: each is asked to end, and whatever has "
              "not ended after fifteen seconds is forced. Unsaved work is lost, so warn people first. The page "
              "tells them " + ui("the server is shutting down") + ". When the service is running again, each person "
              "signs in and gets a new desktop.", lead=True) + \
    ul([
        "If the service falls by itself (a fault) it is restarted after two seconds, and a desktop whose service "
        "fell is closed unless its user comes back within those few seconds.",
        "<b>Restarting the machine</b> ends every desktop and every program in the same way.",
        "A user who signs in at the machine's screen while their remote desktop is open waits a moment (a few "
        "seconds, at most about 25) while the remote desktop is closed; if the service is stopped there is no wait. "
        "In the tests on Fedora 45 (21 to 25 November 2026; GNOME on a virtual machine) the remote desktop was closed in about one or two "
        "seconds on GNOME, 1.7 seconds on XFCE and 0.7 seconds on LXQt. On KDE Plasma, if a program of the "
        "remote desktop does not close by itself, the wait is about five to six seconds (REMOTIX gives the KDE desktop 5 "
        "seconds, then closes it by force). These figures come from the tests, not from a promise.",
        "If the machine has <code class=\"sys\">needrestart</code> (Fedora does not install it by itself), the "
        "package tells it not to restart REMOTIX after a library update, and lists the service for a manual restart. "
        "Do it when nobody is working. This was read from the package: whether <code class=\"sys\">needrestart</code> "
        "or an automatic updater really respects it was <b>not verified</b> on Fedora.",
    ])

S_OPTIONS = p("Settings go in " + sysf("/etc/remotix/remotix.conf.d/") + " as described in "
              + rif("Fedora 45: port, name and other settings") + ". These are the ones meant for an administrator; "
              "put them on the " + c("REMOTIX_OPTIONS") + " line (the port has its own line).", lead=True) + \
    table(["Setting", "Default", "What it does"], [
        [c("REMOTIX_PORT"), "7447", "The port for the page (TCP) and the video (UDP). Open it in the firewall (firewalld: see "
         + rif("Fedora 45: the firewall") + ")."],
        [c("--name NAME"), "the machine's host name",
         "The name or address written in the certificate: use it if people connect by IP address or by another "
         "name. It only counts when the certificate is made (see " + rif("Fedora 45: the first visit and the "
                                                                          "certificate") + ")."],
        [c("--session-cap N"), "10",
         "The most sessions served at once (the program's default is 10; how many people really work well together depends on the machine). Whoever does not fit gets the generic “could not open your session” "
         "sentence. The real limit is also decided by the machine's power: a higher number does not make a weak "
         "machine stronger."],
        [c("--inactivity-s N"), "1800 (30 minutes)",
         "Seconds without input before a connected page is disconnected. <b>0 switches it off.</b>"],
        [c("--abandon-s N"), "3600 (60 minutes)",
         "Seconds without input before a session is closed with its programs. <b>0 means no session is ever "
         "closed on its own</b>: forgotten desktops then keep using memory for ever. The highest value used is one "
         "year."],
    ], "«TAB» — Settings an administrator can change") + \
    warn("only the settings in this table are meant to be changed. The program has many more options, used by "
         "the people who develop it; leaving them alone is part of what has been tested. A wrong option can stop "
         "the service from starting (the journal says which).", "Leave the rest alone.")

S_USERS = p("REMOTIX adds very little to the machine. This is the whole list.", lead=True) + \
    table(["What", "Where it comes from and what it is for"], [
        ["A system user and group <code class=\"sys\">remotix</code>",
         "Created at installation (no login, shell " + sysf("/usr/sbin/nologin") + ", home " + sysf("/") + "). The "
         "part of REMOTIX that faces the network runs as this user. Deleted when the package is removed, unless it "
         "was there before."],
        ["A PAM service " + sysf("/etc/pam.d/remotix"),
         "The sign-in rules: the machine's own authentication, the same as for ssh (Fedora's "
         "<code class=\"sys\">password-auth</code> stack), with the excluded users refused first. It is a settings "
         "file of the package: if you change it, an upgrade keeps your version. You may add to it as you would to "
         "any PAM file."],
        ["The list " + sysf("/etc/remotix/denied-users"), "Users who cannot sign in (see "
         + rif("Fedora 45: who may connect") + ")."],
        ["<b>A user's group for the video card</b>, at the user's <b>first connection</b>",
         "A desktop on the machine needs permission to use the video card, which normally only someone sitting at "
         "the machine gets. At a user's first connection, after the password is right and before the desktop is "
         "created, REMOTIX adds the user to the group that owns the card's device files (usually "
         "<code class=\"sys\">render</code>). It writes a line in the journal, and records the change in "
         + sysf("/var/lib/remotix/group-enrollments.jsonl") + ", so that removing the package can undo "
         "exactly what REMOTIX did and nothing else. A user who was already in the group is never recorded or "
         "touched."],
        ["<b>Permissions on the card</b> (access lists on " + sysf("/dev/dri/renderD*") + ")",
         "Given to a user while a REMOTIX desktop of theirs exists, so that the desktop can use the card at once "
         "even though the group was added a moment ago. They are recorded in " + sysf("/var/lib/remotix/render-grants")
         + ", taken back when the desktop is gone and when the package is removed, and disappear at the next boot "
         "in any case."],
        ["Two polkit rules in " + sysf("/usr/share/polkit-1/rules.d/"),
         "<b>50-remotix-no-poweroff</b>: nobody can power off, restart, halt, suspend or hibernate the machine from "
         "a desktop, remote or local; root with sudo still can. <b>40-remotix-remote-sessions</b>: some requests "
         "that desktops make on their own at sign-in, and that a remote user cannot answer, are settled instead "
         "of showing a password window. Refreshing the software catalogues (Flatpak, PackageKit) and the firmware "
         "list (fwupd) is allowed for every REMOTIX user; controlling the network and adding a system-wide "
         "software source is allowed to administrators (members of <code class=\"sys\">wheel</code>, the "
         "administrators' group of Fedora) and silently refused to others. Everything else still asks for a "
         "password, as with sudo."],
        ["<b>A SELinux module</b> " + sysf("/usr/share/selinux/packages/remotix.pp.bz2"),
         "Loaded at installation and removed with the package. It puts REMOTIX in three domains of its own: "
         "<code class=\"sys\">remotix_t</code> (the part that runs as root: sign-in and the birth of the desktops), "
         "<code class=\"sys\">remotix_net_t</code> (the part that faces the network: a narrow wall, that can only "
         "use the sockets it is handed and write in its own two folders) and "
         "<code class=\"sys\">remotix_hook_t</code> (the hook of the local sign-in). It also gives their own labels "
         "to REMOTIX's files. The machine stays in <b>enforcing</b> mode; the users' desktops run in the same "
         "SELinux context as after a sign-in at the machine."],
        ["<b>A firewalld service</b> " + sysf("/usr/lib/firewalld/services/remotix.xml"),
         "Describes the port (7447, TCP and UDP); it is defined and opens nothing (see "
         + rif("Fedora 45: the firewall") + ")."],
        ["<b>A hook in the login screens</b> " + c("remotix-pam-hook") + " (" + sysf("/usr/libexec/remotix/remotix-pam-hook")
         + ")",
         "When somebody signs in at the machine's own screen, the login waits until that user's remote desktop is "
         "closed. The line that does this is added to the sign-in files of the login screens in "
         + sysf("/etc/pam.d/") + " (gdm, plasmalogin, lightdm and sddm; the files of authselect are never touched). "
         "It is put there at installation, put back by the package when the login screen's own package is installed "
         "or updated and by the service at every start, and taken out when the package is removed. The line is "
         "<i>optional</i> and ends within 25 seconds: it can never stop a login. While REMOTIX is installed, "
         + c("rpm -V sddm") + " reports its files as modified, because SDDM's sign-in files belong to the SDDM "
         "package and carry our line. It was tried at the real login screens of all four desktops (see "
         + rif("Leaving and coming back") + ")."],
        ["<b>A rules database for GNOME</b> " + sysf("/etc/dconf/db/remotix"),
         "Built by the package (it needs the " + c("dconf") + " command, package " + c("dconf") + ") and rebuilt "
         "by the service at every start if it is missing or different. It holds what REMOTIX imposes on a GNOME "
         "remote session (no lock screen, no automatic suspend, the integer scale 1, “Log Out” always shown). "
         "Removed with the package."],
        ["A needrestart file " + sysf("/etc/needrestart/conf.d/remotix.conf"),
         "Keeps automatic restarts away from the service, if the machine has needrestart (it is harmless if not)."],
        ["A KDE permission " + sysf("/usr/share/applications/org.kde.remotix.desktop"),
         "Lets KWin share its screen with REMOTIX."],
    ], "«TAB» — What REMOTIX adds to the machine") + \
    p("<b>Users' own settings.</b> While a user's remote session lasts, REMOTIX applies the session's rules to the "
      "desktop (no shut down, restart, suspend or lock buttons; “Log Out” always shown) and takes them away "
      "again at the end. Everything else the user changes — look, themes, panels, the wallpaper on GNOME — is "
      "theirs and stays, also at the machine.") + \
    p("<b>On GNOME</b> the rules are given to the session through the system database "
      + sysf("/etc/dconf/db/remotix") + " described above, so that the user's own settings file is never "
      "written by REMOTIX. The "
      "only trace in a user's home is the small file " + sysf("~/.config/dconf/remotix") + ", which holds the "
      "keyboard layout of the session and which removing the package deletes. For this to work the " + c("dconf") + " command "
      "(package " + c("dconf") + ", recommended) must be installed. <b>Without it</b> GNOME still starts, but "
      "REMOTIX cannot lock anything: the session's rules are only suggestions that the user can change, and what the "
      "user changes from the browser is not kept at the next sign-in. The journal says so with a line that starts "
      + c("DECLARED FALLBACK") + " and the installation prints a warning. To mend it, install " + c("dconf") + " and restart "
      "the service (warn the people first). This case was read from the program and <b>not tried on a machine</b>. If "
      "the administrator has set a <code class=\"sys\">DCONF_PROFILE</code> of their own, REMOTIX keeps it as the "
      "base of the session; that too is read from the program and not verified on Fedora.") + \
    p("<b>On XFCE</b> the values of the keys REMOTIX locks are saved in " + sysf("~/.local/state/remotix/")
      + " and restored when the session ends, or at the next start if it ended badly. <b>On KDE Plasma and LXQt</b> "
      "the rules live in the session's temporary folder and disappear with it. Everything else the user changes is "
      "theirs and stays.") + \
    p("<b>The keyring.</b> REMOTIX does not unlock the user's keyring when it signs a user in remotely (the modules "
      "that do it at the machine's login screen are not in REMOTIX's sign-in rules). A program that asks for the "
      "keyring finds it locked and asks for the password on the remote screen. This is declared and was decided; "
      "it is the same on the other distributions REMOTIX runs on.")

S_SECURITY = p("<b>REMOTIX is made for your own server, on your own network or behind a VPN.</b> That is its stated "
               "assumption, and the notes below follow from it.", lead=True) + \
    table(["", "What to know"], [
        ["Two layers",
         "<b>The transport</b> is always encrypted with TLS, with a certificate the machine makes itself (or yours). "
         "<b>The access</b> is address, port, user and password, and nothing else: there is no second factor. "
         "Real extra hardening, such as two-factor sign-in, has been postponed until the project is complete."],
        ["The first click",
         "With the machine's own certificate, the first visit from each device depends on you clicking through a "
         "warning. Someone who could interpose on that very first visit could answer instead of the machine. The "
         "risk is accepted for an own server on an own network. A real certificate removes the problem for the "
         "page (see " + rif("Fedora 45: the first visit and the certificate") + ")."],
        ["Do not put it on the open Internet",
         "Keep port 7447 closed to the world: allow only your network or your VPN (see "
         + rif("Fedora 45: the firewall") + "). The package opens nothing, but on some editions of Fedora the "
         "firewall's default zone already leaves the ports above 1024 open (on the test machines: Workstation and "
         "KDE Plasma), so the port may be reachable before you do anything: look at your zone, and narrow it if the "
         "machine is not on a trusted network. The ban stops guessing, but a password is the only key."],
        ["The password is the machine's",
         "A user with a weak password is a weak door. REMOTIX does not add rules; use the machine's own "
         "(for example <code class=\"sys\">pam_faillock</code>, which Fedora offers as a feature of its sign-in "
         "profile: it is not switched on in a fresh Workstation installation, it would hold for REMOTIX too, and "
         "its use together with REMOTIX's own ban was not tried)."],
        ["root is excluded", "The administrator account cannot sign in through REMOTIX. Do not remove it from "
                              + sysf("/etc/remotix/denied-users") + "."],
        ["A shared server",
         "Each person has their own desktop, but all share the machine: CPU, memory, disk, and the video card. "
         "Ordinary users cannot power it off, and administrative actions in a desktop ask for a password. The "
         "screen lock of a remote desktop is off, because the sign-in page is the lock."],
        ["A ban ends only with time", "The administrator has no way to lift it: see " + rif("The login defences") + "."],
    ], "«TAB» — Security notes for a shared server") + \
    p("<b>Optional protections you can switch on.</b> Two more protections ship <i>switched off</i> in "
      + sysf("/usr/share/remotix/belts/") + ", because they change settings of the machine that are yours to "
      "decide. They stop the <i>physical</i> power, restart, suspend and lid keys of the machine (so that nobody at "
      "the keyboard takes everybody's sessions away with one key) and forbid sleeping at all. As installed, the "
      "machine's <i>physical</i> power button therefore still works (the polkit rule that stops the desktops' menus "
      "is the only protection in force). To switch them on (effective at the next boot):") + \
    term("$ sudo install -D -m 0644 /usr/share/remotix/belts/remotix-power-keys.conf "
         "/etc/systemd/logind.conf.d/remotix-power-keys.conf\n"
         "$ sudo install -D -m 0644 /usr/share/remotix/belts/remotix-no-suspend.conf "
         "/etc/systemd/sleep.conf.d/remotix-no-suspend.conf", "Switch the optional protections on") + \
    p("They are not part of what was tested for this release; use them if the machine is a shared server that "
      "must never go to sleep.")

S_FILES = p("Where REMOTIX keeps things on a Fedora 45 machine (the paths are those of the package's file list):",
            lead=True) + \
    tree([
        "/usr/libexec/remotix/",
        "├── remotix  # the program",
        "├── remotix-local-login  # the hook that closes a remote desktop when its user signs in at the machine",
        "├── remotix-pam-hook  # puts that hook's line into the login screens' PAM files",
        "└── remotix-polkit-seated  # a helper of the polkit rule",
        "/usr/share/remotix/",
        "├── page.html  # the page served to browsers",
        "├── remotix.conf  # the defaults: do not edit",
        "├── linked.json  # the versions of the libraries built into the program",
        "├── dconf/  # the rules of the GNOME session, before they are compiled",
        "└── belts/  # the optional protections, switched off",
        "/etc/remotix/",
        "├── denied-users  # users who cannot sign in",
        "└── remotix.conf.d/  # your settings",
        "/etc/pam.d/remotix  # the sign-in rules",
        "/etc/pam.d/  # also the sign-in files of the login screens (gdm-*, plasmalogin*, lightdm*, sddm*) that carry REMOTIX's line",
        "/etc/needrestart/conf.d/remotix.conf  # keeps automatic restarts away from the service",
        "/etc/dconf/db/remotix  # GNOME: the rules database (made by the package and the service)",
        "/usr/lib/firewalld/services/remotix.xml  # the firewalld service (defined, not opened)",
        "/usr/share/selinux/packages/remotix.pp.bz2  # the SELinux module (loaded at installation)",
        "/usr/share/polkit-1/rules.d/  # the two polkit rules (40 and 50)",
        "/usr/share/applications/org.kde.remotix.desktop  # the KDE permission",
        "/usr/lib/systemd/system/remotix.service  # the service",
        "/usr/lib/sysusers.d/remotix.conf  # the system user",
        "/usr/lib/tmpfiles.d/remotix.conf  # the data folders",
        "/usr/share/licenses/remotix/LICENSE.md  # the licence",
        "/usr/share/doc/remotix/THIRD-PARTY-LICENSES  # the licences of the third-party components",
        "/var/lib/remotix/",
        "├── net/  # what the network part writes (owner: remotix)",
        "│   ├── certificates/  # page.pem, page.key, and the short-lived certificate",
        "│   └── ban  # the ban list: do not edit",
        "├── group-enrollments.jsonl  # who REMOTIX added to a group",
        "└── render-grants  # permissions given on the card",
        "~/.local/state/remotix/  # in each user's home: the session log and a few records",
        "~/.config/dconf/remotix  # in each user's home, GNOME only: the session's keyboard layout",
        "~/.config/kwinoutputconfig.json  # in each user's home, KDE Plasma only: KWin's own file (not REMOTIX's), the last size of the remote screen",
    ], "«FIG» — Folders and files") + \
    p("<b>Certificates.</b> They live in " + sysf("/var/lib/remotix/net/certificates/") + " (see "
      + rif("Fedora 45: the first visit and the certificate") + "). The page's certificate lasts a year and is made "
      "again when it expires; the short-lived one used by the video connection is renewed by the service well "
      "before it runs out. <b>The ban list</b> is " + sysf("/var/lib/remotix/net/ban") + ". It does not hold any user "
      "name (they are stored in a scrambled form), is rewritten by REMOTIX, and survives restarts; do not edit it.")

CHAPTER = ("Looking after an installation", [
    ("The service", S_SERVICE),
    ("What a restart of the service does", S_RESTART),
    ("Settings you can change", S_OPTIONS),
    ("Users, groups and what REMOTIX changes", S_USERS),
    ("Security on a shared server", S_SECURITY),
    ("Where things are", S_FILES),
])
