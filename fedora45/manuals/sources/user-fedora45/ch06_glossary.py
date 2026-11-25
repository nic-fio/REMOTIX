"""User Manual, chapter 6 — glossary (Fedora 45)."""
from build import dl

CHAPTER = ("Glossary", [
    ("Words used in this manual", dl([
        ("Abandonment", "The 60-minute clock: after an hour without any input from the user, the desktop and its "
                        "programs are closed."),
        ("authselect", "Fedora's tool that decides which sign-in rules the machine uses. REMOTIX never changes what it "
                       "generates; the PAM service of REMOTIX only uses it."),
        ("Ban", "The temporary refusal of sign-ins from an address, or of one user name from an address, after too "
                "many wrong passwords. It lasts 15 minutes, then 1 hour, then 12 hours, and only time ends it."),
        ("Canvas", "The desktop's size in pixels, decided when you sign in from the size of your browser window."),
        ("Desktop", "GNOME, KDE Plasma, XFCE or LXQt: the windows, panels and programs you work with."),
        ("Detach", "To leave without ending: the connection goes, the desktop and its programs stay."),
        ("dnf", "Fedora's program for installing and removing packages. REMOTIX is installed with "
                "<code>sudo dnf install ./remotix-1.2.0-1.fc45.x86_64.rpm</code> and removed with "
                "<code>sudo dnf remove remotix</code>."),
        ("Encoding", "Turning the desktop picture into video. REMOTIX does it only on the video card, and on Fedora the "
                    "driver that does it for H.264 comes from RPM Fusion."),
        ("firewalld", "The firewall of Fedora. REMOTIX defines a service called <code>remotix</code> for it (port 7447, "
                      "TCP and UDP); the administrator opens it."),
        ("H.264, HEVC", "The two video formats REMOTIX can use. Your browser decodes them."),
        ("Inactivity", "The 30-minute clock: after half an hour without input, the page is disconnected and "
                       "asks for the password again; the programs stay."),
        ("Log Out", "The entry in the desktop's own menu that ends the session and closes all its programs."),
        ("PAM", "The machine's own system for checking passwords. REMOTIX uses it, through a service called "
                "<code>remotix</code>, so the password is the one you use at the machine."),
        ("Port 7447", "The one network port REMOTIX uses, over TCP for the page and over UDP for video and keys."),
        ("QUIC, WebTransport", "The way the video, the sound and the keys travel between the browser and the "
                               "machine, over UDP. Your browser must support WebTransport."),
        ("RPM, .rpm", "The kind of package file Fedora uses: <code>remotix-1.2.0-1.fc45.x86_64.rpm</code>."),
        ("RPM Fusion", "A separate repository of Fedora software, where the video drivers with H.264 and HEVC are. "
                       "REMOTIX needs them on the video card, and the administrator enables the repository."),
        ("SELinux", "The security system of Fedora, on in <i>enforcing</i> mode. REMOTIX brings a module of its own "
                    "that puts the program in three domains of its own, one of them a narrow wall round the part that "
                    "faces the network."),
        ("Session", "Your desktop on the machine, with its programs. It belongs to you, not to the browser tab."),
        ("Slot", "A user's single place among the connected ones. Taken by the first connected browser."),
        ("Touch layout", "How the page behaves when you use a finger and no mouse: trackpad-like gestures and a "
                         "keyboard button."),
        ("Wayland", "The kind of graphical session REMOTIX uses. Programs written for the older X11 still run in "
                    "it."),
        ("wheel", "The administrators' group of Fedora: its members can use <code>sudo</code>. In REMOTIX it also "
                  "decides who may control the network from a remote desktop."),
    ])),
])
