"""User Manual, chapter 2 — installing REMOTIX (Ubuntu 26.04): the steps, then one section for each part.
Sources: debian/control, debian/remotix.preinst, .postinst, .prerm, .postrm, .service, .conf, .ufw, denied-users,
src/remotix.pam, src/certificates.c, src/main.c (options), docs/SPECS.md §4.1; the technical manual of this tree,
chapter 15 (the package) and 24 (what was and was not verified)."""
from build import c, note, p, rif, steps, sysf, table, term, ui, ul, warn

S_BEFORE = p("Installing REMOTIX is the installation of one package with apt. There is no installer program. These "
             "are the steps; the commands are in the sections below. REMOTIX 1.0.0 is for Ubuntu 26.04 (Ubuntu, Kubuntu, Xubuntu, Lubuntu).", lead=True) + \
    steps([
        "<b>Check the machine</b>: Ubuntu 26.04 with one of the four desktops installed, a video card that "
        "encodes (see " + rif("What you need") + "), the <i>universe</i> part of the archive switched on, and a way "
        "to reach it on the network.",
        "<b>Install the package</b> with apt, as an administrator.",
        "<b>Switch the service on.</b> The package installs the service switched off and does not start it: you "
        "decide when REMOTIX starts to listen.",
        "<b>Open the firewall</b>, if the machine's firewall is on (on Ubuntu it is installed but off): port "
        "7447, TCP and UDP. REMOTIX never changes the firewall.",
        "<b>Open the page for the first time</b> from a browser and accept the machine's certificate once on each "
        "device (see " + rif("Ubuntu 26.04: the first visit and the certificate") + ").",
    ]) + \
    p("Nothing has to be configured for the people who will connect: any user of the machine, except the ones in "
      "the list of excluded users (by default only <code class=\"sys\">root</code>), can sign in with the machine's "
      "own password. The first time a user connects, REMOTIX prepares what that user needs to use the video card "
      "(see " + rif("Users, groups and what REMOTIX changes") + ").")

S_DEB_INSTALL = p("This section is for <b>Ubuntu 26.04</b>. The package is a single file named like "
                  + c("remotix_1.0.0-1+ubuntu26.04_amd64.deb") + " (the last part is the architecture: <i>amd64</i> for "
                  "an ordinary PC). Put it on the machine and, in the folder where it is, run:", lead=True) + \
    term("$ sudo apt install ./remotix_1.0.0-1+ubuntu26.04_amd64.deb\n"
         "$ sudo systemctl enable --now remotix\n"
         "$ systemctl status remotix", "Install and start") + \
    p("The first command installs REMOTIX and what it needs. The second makes the service start with the machine "
      "and starts it now. The third shows that it is running (“active (running)”). The <b>./</b> before the file "
      "name matters: without it apt looks for a package of that name in the repositories and does not find it. "
      "Use <b>apt install</b> and not <i>dpkg -i</i>: apt reads from the package what REMOTIX needs and installs it "
      "from Ubuntu's archive, while dpkg fetches nothing and leaves the installation incomplete. If you install the "
      "same version again over itself (for example a package rebuilt with the same number), use "
      + c("sudo apt install --reinstall ./remotix_1.0.0-1+ubuntu26.04_amd64.deb") + ".") + \
    p("<b>What apt brings along.</b> Besides REMOTIX's own files, apt installs what REMOTIX needs to run and the "
      "things it recommends:") + \
    table(["Kind", "Packages", "Why"], [
        ["Needed", c("libpam-systemd") + ", " + c("libpam-runtime") + ", " + c("libpam-modules") + ", "
         + c("passwd") + ", " + c("systemd") + ", " + c("dbus-user-session"),
         "sign-in, the users' sessions, adding a user to a group at first connection, and the line REMOTIX "
         "adds to the machine's sign-in rules"],
        ["Needed", c("pipewire") + ", " + c("wireplumber"), "the audio of every desktop, and the video capture on "
                                                          "GNOME and KDE Plasma"],
        ["Recommended (installed by default)", c("va-driver-all") + ", " + c("mesa-vulkan-drivers"),
         "the video card's drivers: <b>without them nothing can be encoded</b>. On Ubuntu the AMD "
         "driver for video is part of Mesa, which the desktop already has; <code class=\"sys\">va-driver-all</code> "
         "brings the Intel one. A normal desktop installation has most of this already, so apt often installs "
         "none of it"],
        ["Recommended", c("labwc") + ", " + c("wlr-randr") + ", " + c("xwayland"), "XFCE and LXQt run on labwc "
                                                                              "(KDE Plasma uses the one inside "
                                                                              "REMOTIX); XFCE also needs XWayland; "
                                                                              "older X11 programs need XWayland"],
        ["Recommended", c("dconf-cli"), "GNOME: builds the rules of the remote session and keeps them apart "
                                        "from the user's own settings"],
        ["Recommended", c("fonts-dejavu-core"), "a font, so that the desktop's compositor can draw text"],
    ], "«TAB» — What apt installs with REMOTIX") + \
    p("Some of these (" + c("va-driver-all") + ", " + c("labwc") + ", " + c("wlr-randr") + ") are in the "
      "<i>universe</i> part of Ubuntu's archive. A normal Ubuntu installation has it on; on a machine that has only "
      "<i>main</i> they do not arrive.") + \
    warn("if you install with " + c("--no-install-recommends") + " you lose the recommended packages, among them "
         "the video card's drivers and, on XFCE and LXQt, labwc: the installation succeeds, but the desktop cannot be "
         "shown until they are installed. On Xubuntu and Lubuntu the page then says it could not open your session, "
         "and the journal names the missing package (" + c("sudo apt install labwc") + ").",
         "Do not skip the recommended packages.") + \
    p("<b>No desktop is installed by REMOTIX.</b> If the machine has none of the four, the service starts but says "
      "in its journal that it has found no desktop.") + \
    note("from the moment REMOTIX is installed, nobody can power off, restart, suspend or hibernate the machine from "
         "a desktop's menu — not even a person sitting at the machine, and not from the login screen. An "
         "administrator still can, with "
         + c("sudo systemctl poweroff") + " or " + c("sudo systemctl reboot") + " (see "
         + rif("Users, groups and what REMOTIX changes") + ").", "Power off changes for everybody.") + \
    p("<b>The video card test.</b> At the end of the first installation REMOTIX asks the video card to encode one "
      "test frame. If the card does not, apt does not fail, but prints a warning:") + \
    term("remotix: ⚠ the video card of this machine did not encode a test frame (H.264): REMOTIX will not show "
         "any desktop until it can.\n"
         "remotix:   check the card's driver (Intel/AMD: va-driver-all; NVIDIA: its proprietary driver), then: "
         "sudo /usr/libexec/remotix/remotix --encoding-test h264", "A warning at installation") + \
    p("Once the driver is in place, repeat the test yourself:") + \
    term("$ sudo /usr/libexec/remotix/remotix --encoding-test h264", "Repeat the test") + \
    p("It prints one line and ends with <b>0</b> if the card encodes, <b>3</b> if no card of the machine can encode, "
      "<b>1</b> if a card opens but produces nothing. A virtual machine that has only the emulated card gets this "
      "warning, because the card exists but cannot encode.")

S_DEB_REFUSALS = p("The package refuses to install, on purpose, in two cases. apt then ends with an error whose "
                   "last lines are the messages below.", lead=True) + \
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
    note("both refusals are written in the package's script and were read from it; <b>not tried on Ubuntu "
         "26.04</b>: every machine on which the package was installed for this release had a render device.", "Not tried on Ubuntu.")

S_DEB_FIREWALL = p("REMOTIX never changes the firewall: the package only <i>describes</i> what has to be opened. If the "
                   "machine's firewall is off, there is nothing to do: on Ubuntu 26.04 <b>ufw</b> is installed but "
                   "<b>switched off</b> by default, so on a normal installation the port is reachable "
                   "anyway. If you (or your provider) switch a firewall on, what has to be open is the port "
                   "<b>7447</b>, both <b>TCP</b> and <b>UDP</b>. With only TCP open the page loads and the desktop "
                   "never arrives.", lead=True) + \
    p("<b>With ufw</b> (see whether it is on with " + c("sudo ufw status") + "), the package adds an application "
      "profile called <b>REMOTIX</b> that stands for exactly those two ports. It is defined but not opened. To look "
      "at it and open it:") + \
    term("$ sudo ufw app info REMOTIX\n"
         "$ sudo ufw allow REMOTIX", "Open the port with ufw") + \
    p("To let only your own network in, give the port with an address instead of the profile (adapt the address):") + \
    term("$ sudo ufw allow from 192.168.1.0/24 to any port 7447", "Only the local network") + \
    p("<b>With another firewall</b>, or a firewall outside the machine (a provider's, a router's), open 7447 for TCP "
      "and for UDP by hand.") + \
    note("if you change the port (see " + rif("Ubuntu 26.04: port, name and other settings") + "), the ufw profile "
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
      "(" + c("--name") + ", see " + rif("Ubuntu 26.04: port, name and other settings") + ") <b>before the service is "
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
      "release with a certificate from a real authority.") + \
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
         "TCP and UDP, and tell people to type it after the name: <code class=\"sys\">https://machine-name:7500</code>.",
         "Changing the port.")

S_DEB_WHO = p("Anyone who has a user account on the machine, with a password, can sign in with that name and "
              "password. The password is checked by the machine's own authentication (the same stack that "
              "<code class=\"sys\">ssh</code> uses, defined in " + sysf("/etc/pam.d/remotix") + "), so whatever the "
              "machine already enforces — a locked or expired account, a nologin file, a failure counter if you have "
              "set up one — holds for REMOTIX too.", lead=True) + \
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
    term("$ sudo apt install ./remotix_NEW-VERSION_amd64.deb", "Upgrade") + \
    ul([
        "The restart closes every remote desktop with its programs: unsaved work is lost. At the next sign-in "
        "people get a new desktop.",
        "If you changed a file that the package also ships (for example " + sysf("/etc/pam.d/remotix")
        + "), apt asks which version to keep.",
        "An upgrade is never refused because of the video card.",
        "Ubuntu's own updates of a library (for example the system's security libraries) do <b>not</b> restart "
        "REMOTIX by themselves: the package tells <code class=\"sys\">needrestart</code> never to do it, because a "
        "restart closes every desktop. The service is then listed as one to restart by hand: do it when nobody is "
        "working. This was written from the package; it was <b>not seen at work</b> on an Ubuntu machine.",
    ]) + \
    p("<b>Removing.</b> There are two ways, and the difference is what stays behind. <b>Warn the people connected "
      "first</b>: both close the remote desktops and everything running in them, and unsaved work is lost.") + \
    term("$ sudo apt remove remotix", "Remove, keeping the settings") + \
    ul([
        "The service is stopped and the remote desktops are closed (each is asked to end, and any that has not ended "
        "after fifteen seconds is killed).",
        "The users that REMOTIX had added to a group for the video card are taken out of it again, and the "
        "permissions it gave on the card are taken back.",
        "The line REMOTIX had added to " + sysf("/etc/pam.d/common-session") + " (see "
        + rif("Users, groups and what REMOTIX changes") + ") is taken out again.",
        "The rules database for GNOME sessions, " + sysf("/etc/dconf/db/remotix") + ", that the package made is deleted, "
        "and the AppArmor profile is unloaded from the kernel (its file stays).",
        "The two polkit rules, including the one that forbids power off, go away with the package: the desktops' "
        "power entries are the machine's own again.",
        "Your settings stay: " + sysf("/etc/remotix/") + ", " + sysf("/etc/pam.d/remotix") + ", the AppArmor "
        "profile file, the ufw profile, the needrestart file, and the data folder " + sysf("/var/lib/remotix/")
        + " (certificates, ban list).",
        "<b>What you did yourself stays too</b>: a firewall rule you added (for example " + c("ufw allow REMOTIX")
        + ") is not removed by REMOTIX; take it out yourself if you do not want it.",
    ]) + \
    term("$ sudo apt purge remotix", "Remove and delete everything REMOTIX keeps") + \
    ul([
        "Everything above, and in addition: the package's own settings files (a file you added yourself in "
        + sysf("/etc/remotix/remotix.conf.d/") + " is not touched), the certificates and the ban list "
        "(" + sysf("/var/lib/remotix/net") + "), the record of group changes, and the files REMOTIX keeps in each "
        "user's own folder: in " + sysf("~/.local/state/remotix/") + " (the session log and a few small records; "
        "the folder too if nothing else is in it) and, on GNOME, the small file " + sysf("~/.config/dconf/remotix")
        + " (three keyboard values). Only these files are removed, and as that user: the rest of the user's "
        "folders is never touched.",
        "The system user <code class=\"sys\">remotix</code> is deleted too, unless it was already on the machine "
        "before REMOTIX.",
        "Your own documents and the users' desktop settings are never touched.",
    ]) + \
    p("<b>What the purge does not reach.</b> It acts on the users the system lists at that moment. A user who is "
      "not listed then (a network home folder that is down, an account in a directory that cannot be reached) keeps "
      "those files: they do nothing without REMOTIX, and you can delete them by hand. "
      "A file of your own that you put in " + sysf("~/.local/state/remotix/") + " stays, and so does the folder "
      "that holds it. The folder " + sysf("~/.config/dconf/") + " itself stays. REMOTIX's own labwc and the rest of "
      "its files leave with the package. <b>Not tried on Ubuntu:</b> no complete removal or purge of the package "
      "was run on an Ubuntu 26.04 machine for this release. The steps above are read from the package's scripts, "
      "and only the part that deletes the user's small file was tried, once, on a virtual machine.") + \
    p("The packages that apt installed together with REMOTIX (drivers, labwc, PipeWire…) are not removed. "
      "If you want them gone, " + c("sudo apt autoremove") + " lists them first: read the list before you agree.")

CHAPTER = ("Installing REMOTIX", [
    ("The steps", S_BEFORE),
    ("Ubuntu 26.04: installing", S_DEB_INSTALL),
    ("Ubuntu 26.04: the two refusals", S_DEB_REFUSALS),
    ("Ubuntu 26.04: the firewall", S_DEB_FIREWALL),
    ("Ubuntu 26.04: the first visit and the certificate", S_DEB_CERT),
    ("Ubuntu 26.04: port, name and other settings", S_DEB_SETTINGS),
    ("Ubuntu 26.04: who may connect", S_DEB_WHO),
    ("Ubuntu 26.04: upgrading and removing", S_DEB_UPGRADE),
])
