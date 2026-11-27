"""User Manual, chapter 1 — what REMOTIX is, what it needs, what it does not do.
Sources: src/page.html (sign-in page, REASON_TEXT), docs/SPECS.md §5, §11.4, §11.5, §12, debian/control,
debian/remotix.preinst, src/main.c (defaults), LICENSE.md; for Ubuntu 26.04 the technical manual of this tree
(chapters 12, 15, 17, 24) and docs/REGISTRO-problemi.md."""
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
        "sign in. REMOTIX is supported up to 3K; the size you really get depends on the device and the browser "
        "you connect from.",
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
         "REMOTIX is supported for up to 8 people at the same time. The program's default ceiling is 10 sessions "
         "(the administrator can change it); a machine may well serve fewer. On Ubuntu 26.04 no more than three "
         "people were tried together, and no figure for the capacity of a machine exists yet.", "How many people?")

S_REQ = p("REMOTIX works only if five conditions are met. Read them <b>before</b> you install.", lead=True) + \
    table(["", "Requirement", "Where to read more"], [
        ["1", "<b>Ubuntu 26.04 with one of the four desktops</b>: Ubuntu (GNOME), Kubuntu (KDE Plasma), Xubuntu "
              "(XFCE) or Lubuntu (LXQt), on an ordinary PC (<i>amd64</i>). REMOTIX does not install a desktop.",
         rif("The desktops")],
        ["2", "<b>A video card that encodes H.264</b>, Intel or AMD (or NVIDIA with its own driver: it worked in October 2026 with an earlier build and has not been run again with this release). REMOTIX encodes "
              "the desktop only on the video card and there is no encoding on the processor. On Ubuntu the Mesa "
              "drivers already do it: " + c("va-driver-all") + " and " + c("mesa-vulkan-drivers") + " are installed "
              "with REMOTIX as recommended packages (some of them from <i>universe</i>, which a normal Ubuntu "
              "installation has switched on), and no other repository is needed.",
         rif("Ubuntu 26.04: installing")],
        ["3", "<b>Port 7447, TCP and UDP, open between the device and the machine.</b> If the machine has a "
              "firewall (on Ubuntu, <i>ufw</i> is installed but switched off by default), the administrator opens "
              "the port; with ufw the package brings an application profile called REMOTIX, which is defined but "
              "never opened: " + c("sudo ufw allow REMOTIX") + ".",
         rif("Ubuntu 26.04: the firewall")],
        ["4", "<b>A recent browser</b>: Chrome, Edge or another Chromium browser, or Firefox on Linux.",
         rif("What you need")],
        ["5", "<b>The right date and time on the device you connect from.</b> The certificate of the video "
              "connection is short-lived, made by the machine itself, and counts as valid from one hour before it "
              "was made: a device whose clock is far wrong may fail to connect (the browser says “Opening "
              "handshake failed”; setting the right time cures it).",
         rif("When something does not work")],
    ], "«TAB» — The five requirements") + \
    p("<b>Limits that are declared, not defects.</b> These are known and were decided:") + \
    ul([
        "<b>A sign-in at the machine's own screen with the same user closes that user's remote desktop</b> "
        "with its programs: unsaved work is lost (see " + rif("Leaving and coming back") + ").",
        "<b>No power off, restart, suspend or hibernate</b> from any desktop, for any user (see "
        + rif("What REMOTIX is not") + ").",
    ])

S_NEED = p("Five things have to be in place.", lead=True) + \
    table(["What", "What it has to be"], [
        ["The machine",
         "A machine running <b>Ubuntu 26.04</b> or one of its flavours (<b>Ubuntu</b> with GNOME, <b>Kubuntu</b> with "
         "KDE Plasma, <b>Xubuntu</b> with XFCE, <b>Lubuntu</b> with LXQt), on an ordinary PC (<i>amd64</i>), on which "
         "REMOTIX is installed (see " + rif("Installing REMOTIX") + "). It must already have <b>one of the four "
         "desktops</b>; REMOTIX does not install a desktop. The remote desktop is a Wayland session; older programs "
         "made for X11 still run in it. The package is made for Ubuntu 26.04 only: other versions of Ubuntu, and "
         "Debian, are not covered by this manual. Some of the packages REMOTIX asks for are in the "
         "<i>universe</i> part of Ubuntu's archive, which a normal Ubuntu installation has switched on (see "
         + rif("Ubuntu 26.04: installing") + ")."],
        ["The video card",
         "A video card that can encode video in hardware: <b>Intel or AMD</b>, with the drivers that Ubuntu "
         "brings (Mesa, which a desktop installation already has, for VA-API and for Vulkan Video on AMD; for Intel "
         "also the package <code class=\"sys\">va-driver-all</code>). REMOTIX encodes the desktop <b>only on the "
         "video card</b>: there is no encoding on the processor. A machine with no video card at all, so that "
         "the system lists no render device, is refused when you install REMOTIX. A virtual machine that has only "
         "the emulated card is installed, but cannot encode: it needs a real card passed to it. For this release "
         "only an <b>AMD</b> card was used on Ubuntu 26.04 (a Radeon, in the test machines and on four live "
         "systems); Intel was not tried on Ubuntu 26.04."],
        ["NVIDIA cards",
         "An NVIDIA card needs NVIDIA's own (proprietary) driver. REMOTIX then uses the card through Vulkan Video. "
         "This worked on a real NVIDIA card (an RTX 4090) in October 2026, on Ubuntu 26.04 with an earlier build of "
         "REMOTIX; it has not been run again with this release."],
        ["The network",
         "Port <b>7447</b>, both <b>TCP</b> (the page) and <b>UDP</b> (the video and the keys). Both must be open "
         "between the device and the machine; if the machine has a firewall, the administrator opens them (see "
         + rif("Ubuntu 26.04: the firewall") + "). A network that blocks UDP, as some company networks do, cannot be "
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
      "one sentence when one is missing (see " + rif("When something does not work") + "). On Ubuntu 26.04 the "
      "automatic tests used Chrome and Firefox on Linux (on the four desktops in the first rounds and on GNOME in the last one); by hand, the owner of the project connected "
      "with Chrome from Linux and from Android (a phone, a tablet, Samsung DeX) and from Windows. The other rows "
      "of the table are what the design says, not something tried on Ubuntu.") + \
    note("a computer, a tablet or a phone; no app or plug-in. The device only has to decode video, which every "
         "recent browser does. If your device decodes HEVC, REMOTIX uses it; otherwise it uses H.264. Firefox on "
         "Linux uses H.264. In the automatic tests on Ubuntu the browsers on Linux used H.264. The clock of the "
         "device has to be right (see " + rif("Requirements") + ").", "What the device needs.")

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
    ])

S_DESKTOPS = p("On Ubuntu 26.04 REMOTIX works with the four official flavours: <b>Ubuntu</b> (GNOME), <b>Kubuntu</b> "
               "(KDE Plasma), <b>Xubuntu</b> (XFCE) and <b>Lubuntu</b> (LXQt). It uses the desktop already installed on "
               "the machine.", lead=True) + \
    ul([
        "<b>One desktop per machine.</b> REMOTIX is made for a machine that has <b>one</b> of the four desktops: "
        "machines with several desktops installed together are <b>not supported</b>. If it finds more than one, "
        "it still picks one (when the machine's login screen is set to a desktop, LightDM's or SDDM's choice "
        "decides; otherwise GNOME, then KDE Plasma, then XFCE, then LXQt) and says so in the service's journal, on "
        "the line “the desktop of this machine”, but this is a line that tells the truth, not a feature. Xubuntu "
        "is a special case without being a problem: it carries a few GNOME programs too, and REMOTIX knows it is "
        "Xubuntu from the choice of its login screen (LightDM).",
        "<b>The login screens</b> of the flavours are Ubuntu: GDM; Kubuntu and Lubuntu: SDDM; Xubuntu: LightDM. "
        "They matter when somebody signs in at the machine itself (see " + rif("Leaving and coming back") + ").",
        "<b>GNOME</b> uses its own compositor (Mutter). <b>XFCE and LXQt</b> run on a small compositor called "
        "<i>labwc</i>, the one of Ubuntu, which apt installs with REMOTIX if it is not there (it is a recommended "
        "package, in <i>universe</i>). <b>KDE Plasma</b> does <i>not</i> use that one: it runs on its own "
        "compositor, KWin, placed inside a second labwc that comes <i>inside</i> the REMOTIX package "
        "(" + c("/usr/libexec/remotix/labwc") + "), because with the labwc of Ubuntu programs such as Firefox think "
        "their window is hidden and stop drawing.",
        "<b>XFCE: the wallpaper.</b> XFCE keeps one wallpaper for each screen: the one you chose at the machine "
        "does not pass to the remote screen by itself.",
        "<b>GNOME: the Overview.</b> The remote GNOME desktop starts in the Activities Overview, and REMOTIX does "
        "not leave it by itself: press Escape or choose a program.",
        "<b>If labwc is missing</b> on a machine whose desktop is XFCE or LXQt, nobody can be shown a desktop: "
        "the package says so when it is installed, the journal names the package, and a user who signs in gets "
        "the sentence “could not open your session” instead of a black screen (see "
        + rif("When something does not work") + ").",
        "<b>No desktop at all</b> on the machine: the service says so at start-up and no desktop can be shown.",
    ]) + \
    note("REMOTIX applies a few rules to the desktop while a remote session lasts (the shut down, restart, suspend "
         "and lock buttons are not there, and “Log Out” is always shown) and takes them away again at the end. "
         "Everything else you change from the browser — look, themes, panels — stays as you set it, and you find it "
         "again at the next sign-in; on GNOME this needs the <code class=\"sys\">dconf</code> command (package "
         "<code class=\"sys\">dconf-cli</code>, installed with REMOTIX). More on this in "
         + rif("Users, groups and what REMOTIX changes") + ".",
         "Your settings.")

S_LICENCE = p("REMOTIX is free for personal use and for non-profit associations, churches and religious institutes; "
              "any other use needs a written licence from the author (" + c("remotix@nicfio.it") + "). The source "
              "code may be read and checked, but not modified or redistributed.", lead=True) + \
    p("The licence concerns whoever installs and runs the server: people who only connect with a browser need "
      "nothing from it. Its full text is in " + sysf("/usr/share/doc/remotix/copyright") + " after installation, "
      "and the licences of the third-party components are in " + sysf("/usr/share/doc/remotix/THIRD-PARTY-LICENSES.gz")
      + ". They include the copy of labwc (with wlroots) that comes inside the package: it keeps its own licence (labwc: GNU GPL version 2 only, two of its files LGPL version 2 or later; wlroots: MIT), "
        "which applies to it and not to REMOTIX. This summary is not the licence; the text is.")

CHAPTER = ("What REMOTIX is", [
    ("REMOTIX in short", S_WHAT),
    ("Requirements", S_REQ),
    ("What you need", S_NEED),
    ("What REMOTIX is not", S_NOT),
    ("The desktops", S_DESKTOPS),
    ("The licence", S_LICENCE),
])
