"""User Manual, chapter 1 — what REMOTIX is, what it needs, what it does not do (Fedora 45).
Sources: src/page.html (sign-in page, REASON_TEXT), docs/SPECS.md §5, §11.4, §11.5, §12, rpm/remotix.spec (Requires,
Recommends, %pre, %post), src/main.c (defaults), LICENSE.md, PIANO.md (decisions D1-D7); for Fedora 45 the technical
manual of this tree and docs/REGISTRO-problemi.md."""
from build import arrow, box, c, fig, note, p, rif, sysf, table, ul, warn, zone

PICTURE = fig(
    zone(20, 12, 300, 200, "Your device")
    + box(40, 50, 260, 54, "A browser tab", "Chrome, Edge or Firefox", "navy")
    + box(40, 128, 260, 54, "Nothing else to install", "no app, no plug-in", "soft")
    + zone(400, 12, 480, 200, "The Linux machine")
    + box(420, 50, 440, 54, "REMOTIX", "the service, started with the machine", "blue")
    + box(420, 128, 210, 54, "Desktop of Anna", "her windows, her programs", "light")
    + box(650, 128, 210, 54, "Desktop of Bruno", "his windows, his programs", "light")
    + arrow(302, 77, 418, 77, "#0050C0", False, "port 7447, encrypted", 360, 68)
    + arrow(560, 106, 525, 126) + arrow(720, 106, 755, 126),
    900, 222, "«FIG» — REMOTIX: a page in the browser, and one desktop for each user on the Linux machine")

S_WHAT = p("<b>REMOTIX</b> shows the desktop of a Linux machine inside a browser tab. You open the machine's address "
           "in the browser of a PC, a tablet or a phone, sign in with the Linux user name and password you already "
           "have on that machine, and your own desktop appears, with mouse, keyboard, clipboard and sound. There is "
           "nothing to install on the device you connect from.", lead=True) + PICTURE + \
    p("What you get:") + \
    ul([
        "<b>Your own desktop.</b> Every user of the machine gets a desktop of their own. Several people can work on "
        "the same machine at the same time, each in their own desktop and without seeing the others.",
        "<b>The size of your window.</b> The desktop is created as large as the browser window at the moment you "
        "sign in. The size you really get depends on the device and the browser "
        "you connect from; the program limits the desktop to 4096×2304 pixels at most.",
        "<b>Keyboard, mouse and touch.</b> On a PC, and on a tablet or phone with a mouse and keyboard (for example "
        "Samsung DeX), you work as at the machine. On a touch screen without a mouse the page switches by itself to "
        "a touch layout (see " + rif("On a phone or a tablet") + ").",
        "<b>Sound.</b> What the desktop plays, you hear in the browser.",
        "<b>Copy and paste.</b> Text can be copied between your device and the remote desktop, in both directions "
        "(text only: not images or files).",
        "<b>Leave and come back.</b> Closing the tab, a dropped line or moving to another device does not close the "
        "desktop: its programs keep running. Sign in again, from the same device or from another one, and you find "
        "your windows as you left them. It is closed, with its programs, if the service is stopped or restarted, if "
        "the machine is switched off, or if you sign in at the machine's own screen with the same user: unsaved "
        "work is then lost (see " + rif("Leaving and coming back") + ").",
        "<b>Encrypted.</b> Everything travels encrypted, on a single port, 7447.",
    ]) + \
    note("how many people one machine can serve at once depends on its video card and on how large the windows are. "
         "The program's default ceiling is 10 sessions "
         "(the administrator can change it with " + c("--session-cap") + "); a machine may well serve fewer. On Fedora 45 no more than three "
         "people were tried together (by the automatic tests, on GNOME), and no figure for the capacity of a machine "
         "exists yet.", "How many people?")

S_REQ = p("On Fedora 45 REMOTIX works only if five conditions are met. The video card one (number 2) is not given by "
          "Fedora itself, so read it <b>before</b> you install.", lead=True) + \
    table(["", "Requirement", "Where to read more"], [
        ["1", "<b>Fedora 45 with one of the four desktops</b> (Workstation with GNOME, KDE Plasma, Xfce or LXQt), "
              "on an ordinary PC (x86_64). REMOTIX does not install a desktop.",
         rif("The desktops")],
        ["2", "<b>A video card that encodes H.264, with its driver from RPM Fusion.</b> REMOTIX encodes the desktop "
              "only on the video card, and Fedora's own drivers do not include H.264 and HEVC. The administrator "
              "enables RPM Fusion and installs the driver. AMD: " + c("mesa-va-drivers-freeworld") + " and " + c("mesa-vulkan-drivers-freeworld") + " (RPM Fusion free); Intel: RPM Fusion nonfree and " + c("intel-media-driver") + "; NVIDIA: its proprietary driver. There is no encoding on the processor and no way around this.",
         rif("Fedora 45: video drivers (RPM Fusion)")],
        ["3", "<b>Port 7447, TCP and UDP, opened in the firewall by the administrator.</b> The package defines the "
              "firewalld service " + c("remotix") + " but never opens it: " +
              c("sudo firewall-cmd --permanent --add-service=remotix && sudo firewall-cmd --reload") + ".",
         rif("Fedora 45: the firewall")],
        ["4", "<b>SELinux left as Fedora ships it (enforcing).</b> The package brings its own SELinux module; nothing "
              "has to be configured and nothing has to be switched off.",
         rif("Users, groups and what REMOTIX changes")],
        ["5", "<b>The right date and time on the device you connect from.</b> The certificate of the video connection "
              "is short-lived, made by the machine itself, and counts as valid from one hour before it was made: "
              "a device whose clock is far wrong may fail to connect (it was seen once, on 22 November 2026, with a "
              "notebook whose clock was wrong: the browser said “Opening handshake failed”; setting the right time "
              "cured it).",
         rif("When something does not work")],
    ], "«TAB» — The five requirements on Fedora 45") + \
    p("<b>Limits that are declared, not defects.</b> These are known and were decided, on Fedora 45:") + \
    ul([
        "<b>A sign-in at the machine's own screen with the same user closes that user's remote desktop</b> "
        "with its programs: unsaved work is lost (see " + rif("Leaving and coming back") + ").",
        "<b>No unlocked keyring.</b> A program that asks for the user's keyring (the stored passwords of the "
        "desktop) finds it locked in a remote session and asks for the password on the remote screen. At the "
        "machine itself the keyring is unlocked by the sign-in; REMOTIX does not do that for a remote one.",
        "<b>XFCE has a black background and no icons on the desktop.</b> Fedora's XFCE desktop program was built "
        "without Wayland support; the panel and the dock are there (see " + rif("The desktops") + ").",
        "<b>No power off, restart, suspend or hibernate</b> from any desktop, for any user (see "
        + rif("What REMOTIX is not") + ").",
        "<b>KDE Plasma needs KWin 6.8 or newer</b>, which Fedora 45 has; with an older KWin REMOTIX refuses to start "
        "the Plasma desktop instead of showing a wrong one.",
    ])

S_NEED = p("Five things have to be in place.", lead=True) + \
    table(["What", "What it has to be"], [
        ["The machine",
         "A machine running <b>Fedora 45</b> with one of the four desktops: <b>Fedora Workstation</b> (GNOME), "
         "<b>Fedora KDE Plasma Desktop</b>, or the <b>Xfce</b> or <b>LXQt</b> spin, on an ordinary PC (<i>x86_64</i>), on which "
         "REMOTIX is installed (see " + rif("Installing REMOTIX") + "). It must already have <b>one of the four "
         "desktops</b>; REMOTIX does not install a desktop. The remote desktop is a Wayland session; older programs "
         "made for X11 still run in it. The package is made for Fedora 45 only: other versions of Fedora, and "
         "other distributions, are not covered by this manual. SELinux has to stay in its normal "
         "<b>enforcing</b> mode: the package brings its own module for it."],
        ["The video card",
         "A video card that can encode video in hardware: <b>AMD or Intel</b>. On Fedora the drivers that do it are "
         "<b>not in the base repositories</b> (Fedora's Mesa is built without H.264 and HEVC): the administrator "
         "enables <b>RPM Fusion</b> and installs the driver (AMD: " + c("mesa-va-drivers-freeworld") + " and " + c("mesa-vulkan-drivers-freeworld") + " from RPM Fusion free; Intel: RPM Fusion nonfree and " + c("intel-media-driver") + "; see "
         + rif("Fedora 45: video drivers (RPM Fusion)") + "). The package does not bring them in by itself. "
         "REMOTIX encodes the desktop <b>only on the video card</b>: there is no encoding on the processor. A "
         "machine with no video card at all, so that the system lists no render device, is refused when you "
         "install REMOTIX. A virtual machine that has only the emulated card is installed, but cannot encode: it "
         "needs a real card passed to it. For this release the desktops were tried with an <b>AMD</b> card (a "
         "Radeon, passed to the test virtual machines, and on a real machine with an Intel and a Radeon card, "
         "started from live systems); a machine with an Intel card alone was not tried."],
        ["NVIDIA cards",
         "On Fedora an NVIDIA card needs NVIDIA's own (proprietary) driver. REMOTIX then uses the card through Vulkan Video. "
         "This worked on a real NVIDIA card in October 2026, on Ubuntu; it has not been run again on Fedora 45 with an NVIDIA card."],
        ["The network",
         "Port <b>7447</b>, both <b>TCP</b> (the page) and <b>UDP</b> (the video and the keys). Both must be open "
         "between the device and the machine; on Fedora the administrator opens them in firewalld (see "
         + rif("Fedora 45: the firewall") + "). A network that blocks UDP, as some company networks do, cannot be "
         "used."],
        ["The browser",
         "Chrome, Edge or another Chromium browser, or Firefox (the second table below)."],
    ], "«TAB» — What REMOTIX needs") + \
    table(["Browser", "Where", "Status"], [
        ["Chrome, Edge and the other Chromium browsers", "Linux, Windows", "supported"],
        ["Chrome", "Android (also with Samsung DeX)", "supported"],
        ["Firefox", "Linux", "supported"],
        ["Firefox", "Windows", "not tested yet"],
        ["Firefox", "Android", "<b>not supported</b>: it lacks a feature the page needs (WebCodecs)"],
        ["Safari", "macOS, iPhone, iPad", "not yet verified: the page says Safari 26 or newer should have what it "
                                          "needs, but it has not been tried"],
    ], "«TAB» — The browsers") + \
    p("The browser has to be recent: it needs two features, WebTransport and WebCodecs, and the page tells you in "
      "one sentence when one is missing (see " + rif("When something does not work") + "). On Fedora 45 the "
      "automatic tests used browsers on Linux; by hand, the owner of the project connected from a Linux PC, from a "
      "Windows notebook and from an Android device. The other rows of the table are what the design says, not "
      "something tried on Fedora 45.") + \
    note("a computer, a tablet or a phone; no app or plug-in. The device only has to decode video, which every "
         "recent browser does. If your device decodes HEVC, REMOTIX uses it; otherwise it uses H.264. Firefox on "
         "Linux uses H.264. The clock of the device has to be right (see " + rif("Requirements") + ").",
         "What the device needs.")

S_NOT = p("What REMOTIX deliberately does not do:", lead=True) + \
    ul([
        "<b>It does not encode video on the processor.</b> No video card able to encode, no desktop in the browser.",
        "<b>It has no sign-in of its own.</b> There are no REMOTIX accounts and no REMOTIX passwords: you sign in "
        "with the user name and password of the machine, checked by the machine's own authentication (PAM). The "
        "administrator account, <code class=\"sys\">root</code>, cannot sign in this way.",
        "<b>It does not install a desktop</b>, and does not let you choose one from the page: the machine's desktop "
        "is used (see " + rif("The desktops") + ").",
        "<b>No file transfer</b>, and no images or files in the clipboard: text only.",
        "<b>No microphone</b>: sound goes from the desktop to you, not back.",
        "<b>No power off, restart, suspend or hibernate</b> from any desktop, remote or at the machine itself, "
        "for any user: it is wanted, because other people may be working on the machine (an administrator "
        "still can, with " + c("sudo") + " in a terminal). And no screen lock inside a remote desktop.",
        "<b>No several monitors</b>, no session recording, no X11 desktop sessions (X11 programs run through "
        "XWayland), no connections from RDP, VNC or SPICE programs.",
        "<b>No unlocked keyring in a remote session.</b> REMOTIX does not add the keyring modules to the sign-in: a "
        "program that asks for the keyring finds it locked and asks for the password on the remote screen. This is "
        "declared and was decided (it is the same on the other distributions REMOTIX runs on).",
    ])

S_DESKTOPS = p("On Fedora 45 REMOTIX works with the four desktops of Fedora: <b>GNOME</b> (Fedora Workstation), "
               "<b>KDE Plasma</b>, <b>XFCE</b> and <b>LXQt</b>. It uses the desktop already installed on "
               "the machine.", lead=True) + \
    ul([
        "<b>One desktop per machine.</b> REMOTIX is made for a machine that has <b>one</b> of the four desktops: "
        "machines with several desktops installed together are <b>not supported</b>. If it finds more than one, "
        "it still picks one (when the machine's login screen is set to a desktop, the choice of the login screen "
        "decides; otherwise GNOME, then KDE Plasma, then XFCE, then LXQt) and says so in the service's journal, on "
        "the line “the desktop of this machine”, but this is a line that tells the truth, not a feature.",
        "<b>The login screens</b> are <b>GDM</b> on GNOME, <b>plasmalogin</b> (package "
        "<code class=\"sys\">plasma-login-manager</code>) on KDE Plasma, <b>LightDM</b> on XFCE and <b>SDDM</b> on "
        "LXQt. They matter when somebody signs in at the machine itself (see " + rif("Leaving and coming back")
        + ").",
        "<b>GNOME</b> uses its own compositor (Mutter). <b>KDE Plasma</b> runs on KWin alone (version 6.8), with no "
        "second compositor under it. <b>XFCE and LXQt</b> run on a small compositor called <i>labwc</i>, the one "
        "of Fedora's repositories: it is a recommended package, so dnf installs it with REMOTIX unless weak "
        "dependencies are switched off (see " + rif("Fedora 45: installing") + ").",
        "<b>XFCE: black background, no desktop icons.</b> This is a declared limit on Fedora 45: XFCE's desktop "
        "program was built without Wayland support, so the remote XFCE desktop has a plain black background and "
        "no icons on it. The panel at the top and the dock at the bottom are there. Choosing another wallpaper "
        "does not help.",
        "<b>GNOME: the Overview.</b> The remote GNOME desktop may start in the Activities Overview, and REMOTIX "
        "does not leave it by itself: press Escape or choose a program. (This was not checked again with the "
        "GNOME of Fedora 45.)",
        "<b>No desktop at all</b> on the machine: the service says so at start-up and no desktop can be shown.",
    ]) + \
    note("REMOTIX applies a few rules to the desktop while a remote session lasts (the shut down, restart, suspend "
         "and lock buttons are not there, and “Log Out” is always shown) and takes them away again at the end. "
         "Everything else you change from the browser — look, themes, panels — stays as you set it, and you find it "
         "again at the next sign-in; on GNOME this needs the <code class=\"sys\">dconf</code> command (package "
         "<code class=\"sys\">dconf</code>, installed with REMOTIX as a recommended package). More on this in "
         + rif("Users, groups and what REMOTIX changes") + ".",
         "Your settings.")

S_LICENCE = p("REMOTIX is free for personal use and for non-profit associations, churches and religious institutes; "
              "any other use needs a written licence from the author (" + c("remotix@nicfio.it") + "). The source "
              "code may be read and checked, but not modified or redistributed.", lead=True) + \
    p("The licence concerns whoever installs and runs the server: people who only connect with a browser need "
      "nothing from it. Its full text is in " + sysf("/usr/share/licenses/remotix/LICENSE.md") + " after "
      "installation, and the licences of the third-party components are in "
      + sysf("/usr/share/doc/remotix/THIRD-PARTY-LICENSES") + ". This summary is not the licence; the text is.")

CHAPTER = ("What REMOTIX is", [
    ("REMOTIX in short", S_WHAT),
    ("Requirements", S_REQ),
    ("What you need", S_NEED),
    ("What REMOTIX is not", S_NOT),
    ("The desktops", S_DESKTOPS),
    ("The licence", S_LICENCE),
])
