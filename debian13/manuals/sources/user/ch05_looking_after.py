"""User Manual, chapter 5 — looking after an installation.
Sources: debian/remotix.service, .conf, .tmpfiles, .sysusers, .postinst, .prerm, .postrm, debian/rules,
src/main.c (options and defaults), src/child.c (group enrolment), src/render_grant.c, src/session.c,
src/remotix-*.rules, debian/remotix_network.apparmor, docs/SPECS.md §4.1, §5.2, §5.4."""
from build import c, note, p, rif, sysf, table, term, tree, ui, ul, warn

S_SERVICE = p("REMOTIX is one systemd service called <b>remotix</b>. It is installed switched off and not started "
              "(see " + rif("Debian 13: installing") + ").", lead=True) + \
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
        "On KDE Plasma, if a program of the remote desktop does not close by itself (for example one that asks "
        "“save?”), REMOTIX gives the KDE desktop 5 seconds to close by itself and then closes it by force, so the "
        "person at the machine waits about six seconds.",
        "If the machine has <code class=\"sys\">needrestart</code> (Debian does not always have it), the "
        "package tells it never to restart REMOTIX by itself after a library update, and lists the service "
        "for a manual restart. Do it when nobody is working.",
    ])

S_OPTIONS = p("Settings go in " + sysf("/etc/remotix/remotix.conf.d/") + " as described in "
              + rif("Debian 13: port, name and other settings") + ". These are the ones meant for an administrator; "
              "put them on the " + c("REMOTIX_OPTIONS") + " line (the port has its own line).", lead=True) + \
    table(["Setting", "Default", "What it does"], [
        [c("REMOTIX_PORT"), "7447", "The port for the page (TCP) and the video (UDP). Open it in the firewall."],
        [c("--name NAME"), "the machine's host name",
         "The name or address written in the certificate: use it if people connect by IP address or by another "
         "name. It only counts when the certificate is made (see " + rif("Debian 13: the first visit and the "
                                                                          "certificate") + ")."],
        [c("--session-cap N"), "10",
         "The most sessions served at once (the program's default is 10; what is supported is 8 people at the same "
         "time). Whoever does not fit gets the generic “could not open your session” "
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
         "part of REMOTIX that faces the network runs as this user. Deleted by <i>purge</i>, unless it was there "
         "before."],
        ["A PAM service " + sysf("/etc/pam.d/remotix"),
         "The sign-in rules: the machine's own authentication, the same as for ssh, with the excluded users "
         "refused first. You may add to it as you would to any PAM file."],
        ["The list " + sysf("/etc/remotix/denied-users"), "Users who cannot sign in (see "
         + rif("Debian 13: who may connect") + ")."],
        ["<b>A user's group for the video card</b>, at the user's <b>first connection</b>",
         "A desktop on the machine needs permission to use the video card, which normally only someone sitting at "
         "the machine gets. At a user's first connection, after the password is right and before the desktop is "
         "created, REMOTIX adds the user to the group that owns the card's device files (usually "
         "<code class=\"sys\">render</code>). It writes a line in the journal, and records the change in "
         + sysf("/var/lib/remotix/group-enrollments.jsonl") + ", so that <i>remove</i> and <i>purge</i> can undo "
         "exactly what REMOTIX did and nothing else. A user who was already in the group is never recorded or "
         "touched."],
        ["<b>Permissions on the card</b> (access lists on " + sysf("/dev/dri/renderD*") + ")",
         "Given to a user while a REMOTIX desktop of theirs exists, so that the desktop can use the card at once "
         "even though the group was added a moment ago. They are recorded in " + sysf("/var/lib/remotix/render-grants")
         + ", taken back when the desktop is gone and by <i>remove</i>, and disappear at the next boot in any case."],
        ["Two polkit rules in " + sysf("/usr/share/polkit-1/rules.d/"),
         "<b>50-remotix-no-poweroff</b>: nobody can power off, restart, halt, suspend or hibernate the machine from "
         "a desktop, remote or local; root with sudo still can. <b>40-remotix-remote-sessions</b>: a few requests "
         "that desktops make on their own at sign-in, and that a remote user cannot answer, are settled instead "
         "of showing a password window: the software centre refreshing its catalogues (Flatpak, PackageKit and, "
         "where the machine's fwupd has the action, the firmware list) is allowed for every "
         "REMOTIX user; changing the network or adding a system-wide software source is allowed to administrators "
         "(members of <code class=\"sys\">sudo</code>, <code class=\"sys\">wheel</code> or "
         "<code class=\"sys\">admin</code>) and silently refused to others. Everything else still asks for a "
         "password, as with sudo."],
        ["An AppArmor profile " + sysf("/etc/apparmor.d/remotix_network"),
         "Describes what the network part may do. It is installed in <b>complain</b> mode: it logs what it would "
         "forbid and forbids nothing. Its explicit deny lines (ptrace, mount, abstract unix sockets) act only on a "
         "kernel that mediates them. An administrator can add rules in " + sysf("/etc/apparmor.d/local/remotix_network") + "."],
        ["A needrestart file " + sysf("/etc/needrestart/conf.d/remotix.conf"),
         "Keeps automatic restarts away from the service, if the machine has needrestart (it is harmless if not)."],
        ["A KDE permission " + sysf("/usr/share/applications/org.kde.remotix.desktop"),
         "Lets KWin share its screen with REMOTIX."],
        ["A ufw profile " + sysf("/etc/ufw/applications.d/remotix"), "Describes the port; it opens nothing."],
        ["A line in " + sysf("/etc/pam.d/common-session") + ", put there by <code class=\"sys\">pam-auth-update</code> "
         "from " + sysf("/usr/share/pam-configs/remotix"),
         "When somebody signs in at the machine's own screen, the login waits until that user's remote desktop is "
         "closed. The line is <i>optional</i> and ends within 25 seconds: it can never stop a login. "
         "At every start the service checks that the line is there and, if it is not (after an update, for "
         "example), puts it back with <code class=\"sys\">pam-auth-update</code> and writes one summary line in "
         "its journal (the program is " + c("remotix-pam-hook") + "). If you edited the file by hand, or switched "
         "the REMOTIX profile off in " + c("pam-auth-update") + ", the tool is not forced: the line stays out and "
         "the summary line says so. <i>remove</i> takes it out again, once the service has stopped."],
    ], "«TAB» — What REMOTIX adds to the machine") + \
    p("<b>Users' own settings.</b> While a user's remote session lasts, REMOTIX applies the session's rules to the "
      "desktop (no shut down, restart, suspend or lock buttons; “Log Out” always shown) and puts the user's values "
      "back at the end. On GNOME this needs the " + c("dconf") + " command (package " + c("dconf-cli") + "): "
      "without it GNOME still works, but what the user changes from the browser is not kept. On XFCE the values of "
      "the keys it locks are saved in " + sysf("~/.local/state/remotix/") + " and restored when the session ends, "
      "or at the next start if it ended badly. Everything else the user changes is theirs and stays.")

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
         "page (see " + rif("Debian 13: the first visit and the certificate") + ")."],
        ["Do not put it on the open Internet",
         "Keep port 7447 closed to the world: allow only your network or your VPN (see "
         + rif("Debian 13: the firewall") + "). The ban stops guessing, but a password is the only key."],
        ["The password is the machine's",
         "A user with a weak password is a weak door. REMOTIX does not add rules; use the machine's own "
         "(for example <code class=\"sys\">pam_faillock</code> in the common PAM stack: it holds for REMOTIX too)."],
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
      "the keyboard takes everybody's sessions away with one key) and forbid sleeping at all. To switch them on "
      "(effective at the next boot):") + \
    term("$ sudo install -D -m 0644 /usr/share/remotix/belts/remotix-power-keys.conf "
         "/etc/systemd/logind.conf.d/remotix-power-keys.conf\n"
         "$ sudo install -D -m 0644 /usr/share/remotix/belts/remotix-no-suspend.conf "
         "/etc/systemd/sleep.conf.d/remotix-no-suspend.conf", "Switch the optional protections on") + \
    p("They are not part of what was tested for this release; use them if the machine is a shared server that "
      "must never go to sleep.")

S_FILES = p("Where REMOTIX keeps things on a Debian 13 machine:", lead=True) + \
    tree([
        "/usr/libexec/remotix/",
        "├── remotix  # the program",
        "├── remotix-local-login  # the hook that closes a remote desktop when its user signs in at the machine",
        "└── remotix-pam-hook  # checks that the hook's line is in the PAM file, at every start",
        "/usr/share/remotix/",
        "├── page.html  # the page served to browsers",
        "├── remotix.conf  # the defaults: do not edit",
        "└── belts/  # the optional protections, switched off",
        "/etc/remotix/",
        "├── denied-users  # users who cannot sign in",
        "└── remotix.conf.d/  # your settings",
        "/etc/pam.d/remotix  # the sign-in rules",
        "/usr/share/pam-configs/remotix  # the line pam-auth-update adds to /etc/pam.d/common-session",
        "/etc/ufw/applications.d/remotix  # the ufw profile",
        "/etc/apparmor.d/remotix_network  # the AppArmor profile (complain mode)",
        "/etc/needrestart/conf.d/remotix.conf  # keeps automatic restarts away from the service",
        "/usr/share/applications/org.kde.remotix.desktop  # the KDE permission",
        "/usr/share/polkit-1/rules.d/  # the two polkit rules (40 and 50)",
        "/var/lib/remotix/",
        "├── net/  # what the network part writes (owner: remotix)",
        "│   ├── certificates/  # page.pem, page.key, and the short-lived certificate",
        "│   └── ban  # the ban list: do not edit",
        "├── group-enrollments.jsonl  # who REMOTIX added to a group",
        "└── render-grants  # permissions given on the card",
        "~/.local/state/remotix/  # in each user's home: the session log and a few records",
    ], "«FIG» — Folders and files") + \
    p("<b>Certificates.</b> They live in " + sysf("/var/lib/remotix/net/certificates/") + " (see "
      + rif("Debian 13: the first visit and the certificate") + "). The page's certificate lasts a year and is made "
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
