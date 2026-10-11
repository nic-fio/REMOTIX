"""User Manual, chapter 4 — a short glossary."""
from build import dl

CHAPTER = ("Glossary", [
    ("Words used in this manual", dl([
        ("Browser", "The program you use to open web pages: Chrome, Edge, Firefox."),
        ("Certificate", "The machine's proof of identity for the encrypted connection. REMOTIX makes its own; "
         "browsers do not know it and warn once per device."),
        ("Desktop", "The screen with windows, menus and programs: GNOME, KDE Plasma, XFCE or LXQt."),
        ("Distribution", "A version of Linux: Debian, Ubuntu, Fedora, AlmaLinux, Arch, openSUSE."),
        ("Firewall", "The part of the machine that decides which connections may come in. Port 7447 must be open "
         "in it."),
        ("Graphics card", "The chip that draws the screen. REMOTIX uses it to compress the picture."),
        ("labwc", "A small Wayland compositor. XFCE and LXQt run on it; KDE Plasma runs inside it under REMOTIX."),
        ("Log", "The file or journal where a program writes what it does and why it failed."),
        ("Port", "A numbered door of the machine for network connections. REMOTIX uses 7447, TCP and UDP."),
        (".run file", "The single installation file of REMOTIX, run with " + "<code>sudo sh</code>."),
        ("Session", "Your desktop with its open programs. It stays alive when you close the tab, and ends when you "
         "log out or after an hour without input."),
        ("Wayland", "The modern way Linux desktops draw on the screen. REMOTIX desktops are Wayland sessions."),
    ], "gloss")),
])
