"""User Manual, chapter 1 — what REMOTIX is and what it offers.
Sources: src/page.html (sign-in page, REASON_TEXT), SPECS.md §5.1, §11.5, §12, src/main.c and src/rcp.c
(the 30- and 60-minute clocks), installer/catalog/catalog.json, LICENSE.md."""
from build import arrow, box, c, fig, note, p, table, text, ul, warn, zone

PICTURE = fig(
    zone(20, 12, 300, 200, "Your device")
    + box(40, 50, 260, 54, "A browser tab", "Chrome, Edge or Firefox", "navy")
    + box(40, 128, 260, 54, "Nothing else to install", "no app, no plug-in", "soft")
    + zone(400, 12, 480, 200, "The Linux machine")
    + box(420, 50, 440, 54, "REMOTIX", "the service, started at boot", "blue")
    + box(420, 128, 210, 54, "Desktop of Anna", "her windows", "light")
    + box(650, 128, 210, 54, "Desktop of Bruno", "his windows", "light")
    + arrow(302, 77, 418, 77, "#0050C0", False, "port 7447, encrypted", 360, 68)
    + arrow(560, 106, 525, 126) + arrow(720, 106, 755, 126),
    900, 222, "«FIG» — REMOTIX: a page in the browser, and one desktop for each user on the Linux machine")

S_WHAT = p("<b>REMOTIX</b> shows a full Linux desktop inside a browser tab. The Linux machine runs REMOTIX; you open "
           "its address in the browser of a laptop, a phone or a tablet, sign in with your Linux user name and "
           "password, and your desktop appears, as large as the window. There is nothing to install on the device "
           "you connect from.", lead=True) + PICTURE + \
    p("What it offers:") + \
    ul([
        "<b>Your own desktop.</b> Each user gets their own desktop on the machine; several people can work on the "
        "same machine at the same time, each in their own desktop.",
        "<b>The size of your window.</b> The desktop is created as large as the browser window at the moment you "
        "sign in, up to 4096×2304. Version 1.5 is tested and declared up to 3K; version 1.0 aimed at 4K.",
        "<b>Several people at once.</b> A machine is tested with up to 8 people connected at the same time. "
        "If the machine cannot give one more desktop of that size, the sign-in is refused.",
        "<b>Keyboard, mouse and touch.</b> The page keeps no key combination for itself. A few (such as Alt+Tab "
        "or the Super key) may be taken first by your own computer or browser: the small ⌨ button at the bottom "
        "left of the page lists the ones that do not reach the remote desktop.",
        "<b>Sound.</b> What the desktop plays, you hear in the browser.",
        "<b>Copy and paste.</b> Text can be copied between your device and the remote desktop, in both directions "
        "(text only: not images or files).",
        "<b>Leave and come back.</b> Closing the tab does not close the desktop. Sign in again, from the same "
        "device or another one, and you find your windows as you left them.",
        "<b>Encrypted.</b> Everything travels encrypted, on one port (7447).",
    ])

S_DESKTOPS = p("REMOTIX works with four desktops: <b>GNOME</b>, <b>KDE Plasma</b>, <b>XFCE</b> and <b>LXQt</b>. It "
               "uses the desktop already installed on the machine: it does not install one.", lead=True) + \
    ul([
        "<b>One desktop per machine.</b> If a machine has more than one of the four installed, REMOTIX picks one — "
        "GNOME before KDE, XFCE before LXQt — and writes it in its log.",
        "<b>Wayland only.</b> The remote desktop is a Wayland session. Older programs made for X11 still run, "
        "through XWayland.",
        "<b>XFCE and LXQt</b> run on the labwc compositor, which the installation brings along as a dependency.",
        "<b>KDE Plasma</b> runs inside a small labwc that REMOTIX starts without a screen of its own; this is what "
        "lets the desktop take the size of a new window when you come back. On AlmaLinux and RHEL 10, which have no "
        "labwc package, REMOTIX brings its own (" + c("/usr/lib/remotix/labwc") + ").",
    ]) + \
    note("from version 1.5, KDE Plasma 6.5 or newer (Ubuntu 26.04, Fedora 44, AlmaLinux and RHEL 10, openSUSE "
         "Tumbleweed, Arch) works in the browser as it should: windows are redrawn, Firefox keeps drawing and the screen follows "
         "without delay. In version 1.0, on these distributions, windows could stay frozen on the first picture. Debian 13 and openSUSE Leap 16 were already fine.",
         "KDE and Firefox.") + \
    note("on KDE this costs a little at very large sizes. Measured on an Intel UHD 770: no loss at 1080p and 2K; "
         "at 3K the desktop goes from 58 to 54-55 frames per second, at 4K from 58 to 44-49.", "KDE at 3K and 4K.")

S_BROWSERS = p("The browser needs two modern features, WebTransport and WebCodecs. These are the browsers REMOTIX "
               "declares:", lead=True) + \
    table(["Browser", "Where", "Status"], [
        ["Chrome, Edge and the other Chromium browsers", "Linux, Windows", "supported"],
        ["Chrome", "Android", "supported"],
        ["Firefox", "Linux", "supported"],
        ["Firefox", "Windows", "not tested yet"],
        ["Firefox", "Android", "<b>not supported</b>: it lacks WebCodecs"],
        ["Safari", "macOS, iOS", "not tested yet"],
    ], "«TAB» — The browsers (SPECS.md §11.5)") + \
    p("On an Android phone or tablet, use Chrome. A browser that is too old lacks these features, and the page "
      "cannot show the desktop.")

S_PHONE = p("A phone or a tablet works like a computer: open the address in <b>Chrome</b>, sign in, and the "
            "desktop appears. The desktop has the shape of the phone's screen, so on a phone held upright it is tall "
            "and narrow. Turning the phone does not turn the desktop: to get the right shape again, sign in again.",
            lead=True) + \
    table(["With your fingers", "What happens"], [
        ["Drag with one finger", "Moves the pointer."],
        ["Tap with one finger", "Left click, where the pointer is."],
        ["Tap with two fingers", "Right click."],
        ["Drag with two fingers", "Scrolls."],
        ["Tap, then touch again and drag", "Drags a window or selects text."],
        ["Tap with three fingers", "Middle click."],
        ["Pinch", "Enlarges the view."],
        ["The small ⌨ button at the top right", "Opens the phone's keyboard. The keyboard never opens by itself."],
    ], "«TAB» — Touch on a phone (SPECS.md §7.2)") + \
    warn("on Android the on-screen keyboard is not right yet. After you close it with the ⌨ button it may open "
         "again by itself. The correction is planned for version 1.5.1. A physical keyboard and a mouse (for example with "
         "Samsung DeX) are not affected.", "Known limit in 1.5: the keyboard on Android.")

S_SESSION = p("Your desktop belongs to you, not to the browser tab. Closing the tab, losing the network or switching "
              "device leaves it running on the machine, with every program open.", lead=True) + \
    table(["What happens", "Result"], [
        ["You close the tab, or the network drops", "The desktop keeps running. Sign in again to find it."],
        ["You sign in from another device", "You get the same desktop. Close the tab on the first device first: "
         "while it is still connected, the second one is told “this session's slot shows as taken by another "
         "client”. If the first device simply dropped, wait a few seconds (15 to 30) and try again."],
        ["30 minutes without touching anything", "The page is disconnected; the programs stay open. Sign in again "
         "with your password."],
        ["60 minutes without touching anything", "REMOTIX closes the desktop and its programs. Unsaved work is "
         "lost."],
        ["You choose “Log Out…” in the desktop's menu", "The desktop and its programs are closed. This is the way "
         "to end a session."],
        ["You are signed in at the machine itself (in front of its screen)", "A REMOTIX session for the same user "
         "is refused; and signing in at the machine closes a REMOTIX session of that user."],
    ], "«TAB» — Leaving and coming back") + \
    warn("only your own input — keys, mouse, touch — counts as “touching”. A desktop left without any "
         "input for an hour is closed even if a video is playing in it.", "The one-hour clock.")

S_NOT = p("What REMOTIX deliberately does not do (SPECS.md §12):", lead=True) + \
    ul([
        "a Windows or macOS machine as the server: the server is Linux only;",
        "an application to install on the device you connect from;",
        "X11 desktop sessions (X11 programs run through XWayland);",
        "file transfer, or images and files in the clipboard (text only);",
        "access to the disks, printers, serial ports or smart cards of your device;",
        "several monitors;",
        "recording the session;",
        "connections from RDP, VNC or SPICE programs.",
    ])

S_LICENCE = p("REMOTIX is free for personal use and for non-profit associations, churches and religious institutes; "
              "any other use needs a written licence from the author (" + c("remotix@nicfio.it") + "). The source "
              "code can be read and checked, but it may not be modified or redistributed.", lead=True) + \
    p("The licence is in " + c("LICENSE.md") + ", included in the installation file. People who only connect "
      "with a browser need nothing from it: it concerns whoever installs and runs the server.")

CHAPTER = ("What REMOTIX is", [
    ("REMOTIX in short", S_WHAT),
    ("The desktops", S_DESKTOPS),
    ("The browsers", S_BROWSERS),
    ("On a phone or a tablet", S_PHONE),
    ("Your session waits for you", S_SESSION),
    ("What REMOTIX does not do", S_NOT),
    ("The licence", S_LICENCE),
])
