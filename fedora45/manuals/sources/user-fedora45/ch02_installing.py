"""User Manual, chapter 2 — installing REMOTIX (Fedora 45): the steps, then one section for each part.
Sources: rpm/remotix.spec (Requires, Recommends, %pre, %post, %preun, %postun), rpm/remotix.service, rpm/remotix.conf,
rpm/remotix.firewalld.xml, rpm/denied-users, rpm/needrestart.conf, src/remotix.pam, src/certificates.c, src/main.c
(options), server/live-installa.sh (the RPM Fusion commands), docs/SPECS.md §4.1, docs/REGISTRO-problemi.md (F17, F19, F20);
the technical manual of this tree, chapter 15 (the package)."""
from build import c, note, p, rif, steps, sysf, table, term, ui, ul, warn

S_BEFORE = p("Installing REMOTIX is the installation of one package with dnf. There is no installer program. These "
             "are the steps; the commands are in the sections below. REMOTIX 1.2.0 is for Fedora 45 (Workstation with "
             "GNOME, KDE Plasma Desktop, and the Xfce and LXQt spins).", lead=True) + \
    steps([
        "<b>Check the machine</b>: Fedora 45 with one of the four desktops installed, a video card that "
        "encodes (see " + rif("What you need") + "), and a way to reach it on the network.",
        "<b>Enable RPM Fusion and install the video driver, before the package.</b> Fedora does not carry the "
        "H.264 driver of the video card and REMOTIX cannot show a desktop without it (see "
        + rif("Fedora 45: video drivers (RPM Fusion)") + ").",
        "<b>Install the package</b> with dnf, as an administrator.",
        "<b>Switch the service on.</b> The package installs the service switched off and does not start it: you "
        "decide when REMOTIX starts to listen.",
        "<b>Open the firewall</b>: port 7447, TCP and UDP, with firewalld. REMOTIX never changes the firewall (see "
        + rif("Fedora 45: the firewall") + ").",
        "<b>Open the page for the first time</b> from a browser and accept the machine's certificate once on each "
        "device (see " + rif("Fedora 45: the first visit and the certificate") + ").",
    ]) + \
    p("Nothing has to be configured for the people who will connect: any user of the machine, except the ones in "
      "the list of excluded users (by default only <code class=\"sys\">root</code>), can sign in with the machine's "
      "own password. The first time a user connects, REMOTIX prepares what that user needs to use the video card "
      "(see " + rif("Users, groups and what REMOTIX changes") + ").")

S_CODECS = p("REMOTIX encodes the desktop as H.264 video <b>on the video card</b>, and nowhere else. On Fedora the "
             "drivers that let the card do it are <b>not</b> in the base repositories: Fedora's own Mesa is built "
             "without H.264 and HEVC. They come from <b>RPM Fusion</b>, a separate repository that the administrator "
             "enables. This is a requirement of REMOTIX, like the video card itself: the package does not bring "
             "the drivers in by itself, and there is no software encoding to fall back on.", lead=True) + \
    p("The commands below are the set of drivers that the test machines had. Run them <b>before</b> installing "
      "REMOTIX, so that the test at the end of the installation passes (see "
      + rif("Fedora 45: installing") + "). All of them need an administrator.") + \
    steps([
        "<b>Enable RPM Fusion (free).</b>" + term(
            "$ sudo dnf install https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-45.noarch.rpm",
            "Enable RPM Fusion"),
        "<b>AMD cards (Radeon): install the two “freeworld” drivers.</b> Fedora's own versions are replaced by "
        "them (if they are installed, as on a desktop installation, dnf swaps them):" + term(
            "$ sudo dnf swap mesa-va-drivers mesa-va-drivers-freeworld\n"
            "$ sudo dnf swap mesa-vulkan-drivers mesa-vulkan-drivers-freeworld", "AMD drivers") +
        "If a package is not installed yet, " + c("sudo dnf install") + " with the same " + c("-freeworld") +
        " name does the work. The warning that the package prints at installation names only " +
        c("mesa-va-drivers-freeworld") + ", but the test machines had both.",
        "<b>Intel cards: enable the second RPM Fusion repository and install the Intel media driver.</b>" + term(
            "$ sudo dnf install https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-45.noarch.rpm\n"
            "$ sudo dnf install intel-media-driver", "Intel driver") +
        "If dnf says that it must replace " + c("libva-intel-media-driver") + ", add " + c("--allowerasing") +
        " to the second command. On a machine with both an Intel and an AMD card, do both steps.",
        "<b>NVIDIA cards:</b> the proprietary driver of NVIDIA. REMOTIX uses the card through Vulkan Video. It worked on a real NVIDIA card on Ubuntu, but "
        "it has not been run again on Fedora 45 (see " + rif("What you need") + ").",
        "<b>Check that the card encodes.</b> REMOTIX runs this test for you at the end of its installation and "
        "warns you if it fails; the command to repeat it by hand is in " + rif("Fedora 45: installing") + ".",
    ]) + \
    note("the encoding test succeeded on the Intel card of a real machine started from the Fedora 45 live system "
         "(25 November 2026), which also has a Radeon. A complete desktop on a machine with an Intel card alone was "
         "<b>not tried</b>.", "What was tried.")

S_DEB_INSTALL = p("This section is for <b>Fedora 45</b>. The package is a single file named like "
                  + c("remotix-1.2.0-1.fc45.x86_64.rpm") + " (the last part is the architecture: <i>x86_64</i> for "
                  "an ordinary PC). Put it on the machine and, in the folder where it is, run:", lead=True) + \
    term("$ sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm\n"
         "$ sudo systemctl enable --now remotix\n"
         "$ systemctl status remotix", "Install and start") + \
    p("The first command installs REMOTIX and what it needs. The second makes the service start with the machine "
      "and starts it now. The third shows that it is running (“active (running)”). The <b>./</b> before the file "
      "name matters: without it dnf looks for a package of that name in the repositories and does not find it. "
      "Use <b>dnf install</b> and not <i>rpm -i</i>: dnf reads from the package what REMOTIX needs and installs it "
      "from Fedora's repositories, while rpm fetches nothing and refuses the installation if something is missing. "
      "If you install the same version again over itself (for example a package rebuilt with the same number), use "
      + c("sudo dnf reinstall ./remotix-1.2.0-1.fc45.x86_64.rpm") + ".") + \
    p("<b>What dnf brings along.</b> Besides REMOTIX's own files, dnf installs what REMOTIX needs to run and the "
      "things it recommends:") + \
    table(["Kind", "Packages", "Why"], [
        ["Needed", c("pam") + ", " + c("systemd-pam") + ", " + c("shadow-utils") + ", " + c("gawk") + ", "
         + c("systemd") + ", " + c("dbus-broker"),
         "sign-in, the users' sessions, adding a user to a group at first connection, the scripts of the package, "
         "and the line REMOTIX adds to the sign-in rules of the login screens"],
        ["Needed", c("pipewire") + ", " + c("wireplumber"), "the audio of every desktop, and the video capture on "
                                                          "GNOME and KDE Plasma"],
        ["Needed", c("firewalld-filesystem"), "the folder where the firewall service definition of REMOTIX is put"],
        ["Recommended (installed by default)", c("labwc") + ", " + c("wlr-randr") + ", "
         + c("xorg-x11-server-Xwayland"),
         "XFCE and LXQt run on labwc; XFCE also needs XWayland; older X11 programs need XWayland"],
        ["Recommended", c("dconf"), "GNOME: builds the rules of the remote session and keeps them apart "
                                    "from the user's own settings"],
        ["Recommended", c("dejavu-sans-fonts"), "a font, so that the desktop's compositor can draw text"],
    ], "«TAB» — What dnf installs with REMOTIX") + \
    p("<b>The video drivers are not in this table</b> on purpose: they are not a dependency of the package, they are "
      "a requirement of yours (see " + rif("Fedora 45: video drivers (RPM Fusion)") + "). A normal Fedora "
      "installation has most of the other packages already, so dnf often installs only a few of them.") + \
    warn("if you install with " + c("--setopt=install_weak_deps=False") + " you lose the recommended packages, among "
         "them, on XFCE and LXQt, labwc: the installation succeeds, but the desktop cannot be shown until it is "
         "installed. The package prints a warning when it sees this on a machine whose desktop is XFCE or LXQt, "
         "and the journal names the missing package (" + c("sudo dnf install labwc") + ").",
         "Do not skip the recommended packages.") + \
    p("<b>What else the package puts in place.</b> A <b>SELinux module</b> of its own, loaded at installation (the "
      "machine stays in enforcing mode), and the definition of a <b>firewalld service</b> called "
      + c("remotix") + ", defined and not opened (see " + rif("Fedora 45: the firewall") + "). If the module "
      "could not be loaded, the installation does not fail, but prints a warning that says so and how to load it.") + \
    p("<b>No desktop is installed by REMOTIX.</b> If the machine has none of the four, the service starts but says "
      "in its journal that it has found no desktop.") + \
    note("from the moment REMOTIX is installed, nobody can power off, restart, suspend or hibernate the machine from "
         "a desktop's menu — not even a person sitting at the machine, and not from the login screen. An "
         "administrator still can, with "
         + c("sudo systemctl poweroff") + " or " + c("sudo systemctl reboot") + " (see "
         + rif("Users, groups and what REMOTIX changes") + ").", "Power off changes for everybody.") + \
    p("<b>The video card test.</b> At the end of the first installation REMOTIX asks the video card to encode one "
      "test frame. If the card does not, dnf does not fail, but prints a warning:") + \
    term("remotix: ⚠ the video card of this machine did not encode a test frame (H.264): REMOTIX will not show "
         "any desktop until it can.\n"
         "remotix:   on Fedora the H.264 driver is not in the base repositories: enable RPM Fusion (free) and "
         "install mesa-va-drivers-freeworld\n"
         "remotix:   (NVIDIA: its proprietary driver), then: "
         "sudo /usr/libexec/remotix/remotix --encoding-test h264", "A warning at installation") + \
    p("Once the driver is in place (see " + rif("Fedora 45: video drivers (RPM Fusion)") + "), repeat the test "
      "yourself:") + \
    term("$ sudo /usr/libexec/remotix/remotix --encoding-test h264", "Repeat the test") + \
    p("It prints one line and ends with <b>0</b> if the card encodes, <b>3</b> if no card of the machine can encode, "
      "<b>1</b> if a card opens but produces nothing. A virtual machine that has only the emulated card gets this "
      "warning, because the card exists but cannot encode.")

S_DEB_REFUSALS = p("The package refuses to install, on purpose, in two cases. dnf then ends with an error (a failed "
                   "script of the package) whose lines include the messages below.", lead=True) + \
    table(["The message", "What it means", "What to do"], [
        [ui("remotix: this machine has no video card REMOTIX can use (no DRM render node: nothing named renderD* in "
            "/sys/class/drm).") + "<br>" + ui("remotix: REMOTIX encodes the desktop only on the video card (Intel, AMD or "
                                       "NVIDIA with its driver): it is not installed."),
         "The machine shows no video card that programs can use for encoding. This is checked on a "
         "<b>new</b> installation only: an upgrade of REMOTIX that is already there is never refused for this.",
         "Check that the machine has an Intel or AMD card (or NVIDIA with its own driver) and that its driver is "
         "loaded: " + c("ls /dev/dri") + " must list a file named " + c("renderD128") + " or similar. On a "
         "virtual machine the card has to be passed through to it. If the machine really has no card, REMOTIX "
         "cannot be used on it."],
        [ui("remotix: an account named «remotix» already exists and is a person's: …") + "<br>"
         + ui("remotix: the network side would run as that account. Rename it (usermod -l NEWNAME remotix) or "
              "remove it, then install again."),
         "REMOTIX uses a system user called <code class=\"sys\">remotix</code> for the part of the program that "
         "faces the network. An account with that name already exists and looks like a person's (the message "
         "says why: a root id, a user id in the range of normal users, a login shell, or a home in "
         + sysf("/home") + ", " + sysf("/root") + " or " + sysf("/var/home") + "). It will not be used for this.",
         "Rename the account, for example " + c("sudo usermod -l NEWNAME remotix") + ", after making sure that "
         "it is not in use, or remove it if it is not needed, then install again. REMOTIX will not touch an "
         "account that already exists and is a person's."],
    ], "«TAB» — The two refusals of the installation") + \
    note("both refusals are written in the package's script and were read from it; <b>not tried on Fedora "
         "45</b>: every machine on which the package was installed for this release had a render device.",
         "Not tried on Fedora.")

S_DEB_FIREWALL = p("REMOTIX never changes the firewall: the package only <i>describes</i> what has to be opened. On "
                   "Fedora 45 the firewall is <b>firewalld</b>, and what has to be open is the port "
                   "<b>7447</b>, both <b>TCP</b> and <b>UDP</b>. With only TCP open the page loads and the desktop "
                   "never arrives.", lead=True) + \
    p("<b>Is it already open?</b> It depends on the edition. On the test machines (a fresh installation, 21-22 "
      "November 2026) the default zone of <b>Fedora Workstation</b> (GNOME) and of the <b>KDE Plasma</b> edition "
      "leaves the ports from 1025 upward open for everybody, so 7447 was reachable without doing anything; on the "
      "<b>Xfce</b> and <b>LXQt</b> spins the zone was <i>public</i> and the port was closed. Do not rely on "
      "either: look at your own machine with " + c("sudo firewall-cmd --get-active-zones") + " and "
      + c("sudo firewall-cmd --list-all") + ", and open the port as shown below if you want it open on purpose "
      "(for example if you later narrow the zone).") + \
    p("<b>With firewalld</b>, the package adds a service called <b>remotix</b> that stands for exactly those two "
      "ports. It is defined but not opened. To open it, for good, in the default zone:") + \
    term("$ sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload",
         "Open the port with firewalld") + \
    ul([
        "For another zone, add " + c("--zone=NAME") + " to the first command.",
        "To close it again: " + c("sudo firewall-cmd --permanent --remove-service=remotix && sudo firewall-cmd "
                                  "--reload") + ".",
        "The package makes the running firewall know the new service when it is installed, so the first command "
        "works right after the installation. Without " + c("--permanent") + " the rule lasts only until the "
        "next reload or restart of the firewall.",
    ]) + \
    p("<b>With another firewall</b>, or a firewall outside the machine (a provider's, a router's), open 7447 for TCP "
      "and for UDP by hand.") + \
    p("Letting only your own network in, instead of everybody, is done with a more specific rule or zone of "
      "firewalld; the command above does not do it, and no such rule was tried for this manual.") + \
    note("if you change the port (see " + rif("Fedora 45: port, name and other settings") + "), the firewalld service "
         "still says 7447. Open the new port instead, for TCP and for UDP.", "A different port.")

S_DEB_CERT = p("REMOTIX is reached with an address like <code class=\"sys\">https://machine-name:7447</code> (or the "
               "machine's IP address instead of its name; see below). Everything is encrypted, but the certificate "
               "that proves the machine's identity is <b>made by the machine itself</b> the first time the service "
               "starts: no certificate authority has signed it, and the machine has no way of getting one without a "
               "domain name.", lead=True) + \
    p("So, <b>the first time you open the page on each device</b>, the browser warns you. This is expected:") + \
    steps([
        "Open the address in the browser.",
        "The browser shows a warning page (Chrome and Edge: “Your connection is not private”; Firefox: “Warning: "
        "Potential Security Risk Ahead”; the words vary with the browser and its language).",
        "Choose <b>Advanced</b>, then the link that continues to the site (Chrome and Edge: “Proceed to … "
        "(unsafe)”; Firefox: “Accept the Risk and Continue”).",
        "The REMOTIX sign-in page opens. The browser remembers your choice for this device.",
    ]) + \
    warn("that first click is a real trust decision: it is safe only if you are really talking to your machine. "
         "Do it from a network you trust (your own network or a VPN). Someone who sits between you and the machine "
         "could in principle answer instead of it the very first time; after that, the browser would notice a "
         "different certificate. See " + rif("Security on a shared server") + ".", "Do it once, on your own network.") + \
    p("<b>The name in the certificate.</b> The certificate carries the machine's host name (what the command "
      + c("hostname") + " prints), and the browser expects to be reached with that name. If people connect with the IP "
      "address or with another name, the browser shows a <i>different</i> warning, and some browsers do not offer a "
      "way to continue. To make a certificate for another name or address, write it in the settings "
      "(" + c("--name") + ", see " + rif("Fedora 45: port, name and other settings") + ") <b>before the service is "
      "started for the first time</b>. The certificate is made once and then kept; to replace it later with a new "
      "self-made one, do this:") + \
    term("$ sudo systemctl stop remotix\n"
         "$ sudo mkdir -p /root/remotix-old-certificate\n"
         "$ sudo sh -c 'mv /var/lib/remotix/net/certificates/page.* /root/remotix-old-certificate/'\n"
         "$ sudo systemctl start remotix", "Make the machine's certificate again") + \
    p("The third command is written with " + c("sh -c") + " and quotes on purpose: the folder can be read only by "
      "root and by REMOTIX, so the <code class=\"sys\">page.*</code> has to be worked out by root. "
      "After this every browser asks once more. Stopping the service closes the desktops of the people who are "
      "working: warn them first.") + \
    p("<b>Your own certificate.</b> If you have a domain name and a real certificate (from Let's Encrypt or from "
      "your organisation), REMOTIX will use it for the page, and the browser's warning disappears. Put the "
      "certificate (with its chain) and its key in the folder where REMOTIX keeps its own, under the names "
      "<code class=\"sys\">page.pem</code> and <code class=\"sys\">page.key</code>, owned by the user "
      "<code class=\"sys\">remotix</code>. Start from the commands above (stop the service, move the old "
      "<code class=\"sys\">page.*</code> files out of the way), then:") + \
    term("$ sudo cp fullchain.pem /var/lib/remotix/net/certificates/page.pem\n"
         "$ sudo cp privkey.pem /var/lib/remotix/net/certificates/page.key\n"
         "$ sudo chown remotix:remotix /var/lib/remotix/net/certificates/page.pem "
         "/var/lib/remotix/net/certificates/page.key\n"
         "$ sudo chmod 600 /var/lib/remotix/net/certificates/page.key\n"
         "$ sudo systemctl start remotix", "Use a real certificate") + \
    p("The journal then says “the page uses a certificate that is not ours”. A certificate that REMOTIX did not "
      "make is used as it is and <b>never regenerated, not even when it expires</b>: renewing it is your job (copy "
      "the new files in the same way and restart the service). The address people type must be one of the names in "
      "the certificate. This was written from what the program does; it has <b>not yet been tried</b> in this "
      "release with a certificate from a real authority, nor with SELinux's labels of the copied files looked at "
      "(a file made by " + c("cp") + " in that folder takes the folder's label, which is the right one).") + \
    note("the video and the keys travel over a second connection (QUIC, UDP port 7447) that uses a short-lived "
         "certificate REMOTIX makes and renews by itself; the page hands its fingerprint to the browser. You never "
         "see it and never have to touch it, even when you use your own certificate for the page.",
         "A second certificate.")

S_DEB_SETTINGS = p("The settings are a few lines in a small file. REMOTIX's defaults live in "
                   + sysf("/usr/share/remotix/remotix.conf") + ": <b>do not edit that file</b>, an upgrade rewrites "
                   "it. Your choices go in a file of your own ending in <code class=\"sys\">.conf</code> in "
                   + sysf("/etc/remotix/remotix.conf.d/") + ", with the same kind of lines; they win over the "
                   "defaults. If several files set the same line, the last one in alphabetical order wins.",
                   lead=True) + \
    term("$ sudo nano /etc/remotix/remotix.conf.d/local.conf", "Create the file") + \
    p("A file that changes the port, names the machine by its IP address and lowers the ceiling to six sessions "
      "looks like this:") + \
    term("REMOTIX_PORT=7500\n"
         "REMOTIX_OPTIONS=--name 192.168.1.10 --session-cap 6", "/etc/remotix/remotix.conf.d/local.conf") + \
    p("Then restart the service for the change to take effect:") + \
    term("$ sudo systemctl restart remotix", "Apply") + \
    p("The two lines are " + c("REMOTIX_PORT") + " (the port, for TCP and UDP; default 7447) and "
      + c("REMOTIX_OPTIONS") + " (extra options, separated by spaces). Which options are safe to use, and what "
      "they do, is in " + rif("Settings you can change") + ". Restarting the service closes the people's desktops "
      "and the programs in them (see " + rif("What a restart of the service does") + "): warn them first.") + \
    note("the page and the video use the same port number. If you change it, open the new port in the firewall for "
         "TCP and UDP (the firewalld service " + c("remotix") + " says 7447 whatever you choose, so use "
         + c("sudo firewall-cmd --permanent --add-port=7500/tcp --add-port=7500/udp") + " and then "
         + c("sudo firewall-cmd --reload") + "), and tell people to type it after the name: "
         "<code class=\"sys\">https://machine-name:7500</code>. SELinux's module of REMOTIX lets the service use any "
         "port from 1024 upward that has no label of its own, and the web ports (80, 443, 8080 and the like); a port that Fedora "
         "already labels for another service would need an extra SELinux command, as for any server. A different "
         "port was <b>not tried</b> with SELinux enforcing.",
         "Changing the port.")

S_DEB_WHO = p("Anyone who has a user account on the machine, with a password, can sign in with that name and "
              "password. The password is checked by the machine's own authentication (the same stack that "
              "<code class=\"sys\">ssh</code> uses, defined in " + sysf("/etc/pam.d/remotix") + "), so whatever the "
              "machine already enforces — a locked or expired account, a nologin file, a failure counter if you have "
              "set up one — holds for REMOTIX too. (A fresh Fedora Workstation has no failure counter such as "
              "<code class=\"sys\">pam_faillock</code> switched on, for ssh as for REMOTIX: see "
              + rif("Security on a shared server") + ".)", lead=True) + \
    p("<b>Who is excluded.</b> The file " + sysf("/etc/remotix/denied-users") + " lists, one per line, the user names "
      "that can <b>never</b> sign in through REMOTIX, whatever their password. It comes with one line, "
      "<code class=\"sys\">root</code>. To exclude someone else:") + \
    term("$ echo anna | sudo tee -a /etc/remotix/denied-users\n"
         "$ cat /etc/remotix/denied-users", "Exclude a user") + \
    ul([
        "The change holds from the next sign-in; it does not disconnect someone who is already working.",
        "Keep <code class=\"sys\">root</code> in the file. The file must stay owned by root and not writable by others, "
        "and must exist: if it is missing or damaged, <b>nobody</b> can sign in.",
        "To close an account to REMOTIX <i>and</i> everything else, lock the account in the usual way for the machine "
        "(for example " + c("sudo passwd -l anna") + ").",
    ]) + \
    p("<b>Two more things stop a sign-in</b>, and they are not settings: a user who is <b>already signed in at the "
      "machine itself</b>, in front of its screen, is refused remotely; and a user who is already connected from "
      "another browser is refused a second connection (see " + rif("When something does not work") + "). And the "
      "other way round: if a user signs in at the machine's own screen while their remote desktop is open, that "
      "remote desktop is closed with its programs.")

S_DEB_UPGRADE = p("<b>Upgrading.</b> Install the newer file in the same way. If the service is running, it is "
                  "restarted by the package; if it is switched off, it stays off. <b>Warn the people connected "
                  "first</b>, as for a removal.", lead=True) + \
    term("$ sudo dnf install ./remotix-NEW-VERSION.x86_64.rpm", "Upgrade") + \
    ul([
        "The restart closes every remote desktop with its programs: unsaved work is lost. At the next sign-in "
        "people get a new desktop.",
        "If you changed a file that the package also ships (for example " + sysf("/etc/pam.d/remotix")
        + "), rpm keeps your file and, if the package's own version of it changed, puts the new one beside it with the ending "
        "<code class=\"sys\">.rpmnew</code>; compare the two when you have time. The files concerned are "
        + sysf("/etc/pam.d/remotix") + ", " + sysf("/etc/remotix/denied-users") + " and the needrestart file.",
        "An upgrade is never refused because of the video card.",
        "If the machine has <code class=\"sys\">needrestart</code> (Fedora does not install it by itself), the "
        "package tells it never to restart REMOTIX by itself, because a restart closes every desktop: the service is "
        "then listed as one to restart by hand, which you do when nobody is working. This was written from the "
        "package; it was <b>not seen at work</b>.",
    ]) + \
    p("<b>Removing.</b> There is one command. An RPM package has no separate “purge”: removing REMOTIX also deletes what "
      "it keeps, so that the machine is left clean. <b>Warn the people connected first</b>: it closes the remote "
      "desktops and everything running in them, and unsaved work is lost.") + \
    term("$ sudo dnf remove remotix", "Remove, and delete everything REMOTIX keeps") + \
    ul([
        "The service is stopped and the remote desktops are closed (each is asked to end, and any that has not ended "
        "after fifteen seconds is killed: only the programs of that desktop, nothing else).",
        "The users that REMOTIX had added to a group for the video card are taken out of it again, and the "
        "permissions it gave on the card are taken back.",
        "The lines REMOTIX had added to the sign-in files of the login screens (in " + sysf("/etc/pam.d/")
        + ": gdm, plasmalogin, lightdm and sddm) are taken out again, and the files "
        "of the login screen are as they were before (see "
        + rif("Users, groups and what REMOTIX changes") + ").",
        "The rules database for GNOME sessions, " + sysf("/etc/dconf/db/remotix") + ", that the package made is deleted, "
        "and the SELinux module of REMOTIX is unloaded.",
        "The two polkit rules, including the one that forbids power off, go away with the package: the desktops' "
        "power entries are the machine's own again.",
        "The package's own data go: the certificates and the ban list (" + sysf("/var/lib/remotix/net")
        + "), the record of group changes, the files REMOTIX keeps in each user's own folder — in "
        + sysf("~/.local/state/remotix/") + " (the session log and a few small records; the folder too if nothing "
        "else is in it) and, on GNOME, the small file " + sysf("~/.config/dconf/remotix") + " (three keyboard "
        "values) — and the system user <code class=\"sys\">remotix</code>, unless it was already on the machine "
        "before REMOTIX. Only these files are removed, and as that user: the rest of the user's folders is never "
        "touched.",
        "<b>What stays:</b> your own files in " + sysf("/etc/remotix/remotix.conf.d/") + " (and the folder that "
        "holds them), and <b>what you did yourself</b>: a firewall rule you added (for example "
        + c("firewall-cmd --add-service=remotix") + ") is not removed by REMOTIX; take it out yourself if you do not "
        "want it. A settings file of the package that you had modified (for example "
        + sysf("/etc/remotix/denied-users") + ") is renamed by rpm with the ending <code class=\"sys\">.rpmsave</code> "
        "and then deleted too: keep a copy of it if you want it.",
        "Your own documents and the users' desktop settings are never touched.",
    ]) + \
    p("<b>What the removal does not reach.</b> It acts on the users the system lists at that moment. A user who is "
      "not listed then (a network home folder that is down, an account in a directory that cannot be reached) keeps "
      "those files: they do nothing without REMOTIX, and you can delete them by hand. "
      "A file of your own that you put in " + sysf("~/.local/state/remotix/") + " stays, and so does the folder "
      "that holds it. The folder " + sysf("~/.config/dconf/") + " itself stays.") + \
    p("<b>The packages that dnf installed together with REMOTIX</b> (labwc, wlr-randr and the like, which came as "
      "recommended packages) are removed by dnf together with REMOTIX if nothing else needs them: they are not "
      "files of REMOTIX, it is dnf that cleans up, and installing REMOTIX again brings them back. Read the list dnf "
      "shows before you agree. " + c("sudo dnf autoremove") + " also lists, before doing anything, whatever else "
      "is no longer needed.") + \
    note("the removal and the reinstallation were tried on the Fedora test machines (virtual machines): "
         "the removal leaves the login screens' files as they were byte for byte, also when "
         "<code class=\"sys\">/var/lib/remotix</code> was left over, and installing from scratch again works. The "
         "package 1.2.0 itself was installed from nothing, updated from the previous build and removed on the KDE "
         "test machine (25 November 2026): nothing of REMOTIX was left, except the firewall rule added by hand. They "
         "were <b>not tried</b> on a real machine other than those.", "What was tried.")

CHAPTER = ("Installing REMOTIX", [
    ("The steps", S_BEFORE),
    ("Fedora 45: video drivers (RPM Fusion)", S_CODECS),
    ("Fedora 45: installing", S_DEB_INSTALL),
    ("Fedora 45: the two refusals", S_DEB_REFUSALS),
    ("Fedora 45: the firewall", S_DEB_FIREWALL),
    ("Fedora 45: the first visit and the certificate", S_DEB_CERT),
    ("Fedora 45: port, name and other settings", S_DEB_SETTINGS),
    ("Fedora 45: who may connect", S_DEB_WHO),
    ("Fedora 45: upgrading and removing", S_DEB_UPGRADE),
])
