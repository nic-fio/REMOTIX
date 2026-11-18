from build import dl

TERMS = [
    ("AppArmor", "Linux security module; the profile <code>remotix_network</code> confines the network side (complain mode)."),
    ("Ban", "Block of an address or a user after wrong passwords: 15 minutes, then 1 hour, then 12 hours."),
    ("Child", "The per-user process, running as that user, that holds the desktop stage, capture, encoder, input and audio."),
    ("Compositor", "The Wayland program that draws the desktop: labwc for XFCE and LXQt, Mutter for GNOME, KWin for KDE."),
    ("Detach, reattach", "The browser leaves and the desktop stays alive; a later login finds it again."),
    ("Found again", "A desktop with no child whose user returns within the few seconds before the root side ends it (\"no orphan desktops\"); after an orderly stop there is none. <code>rediscover.c</code>."),
    ("HTTP/3", "HTTP over QUIC; carries the page and WebTransport."),
    ("Local excludes remote", "A user with a local graphical session cannot start a remote one."),
    ("Local-login hold", "The pause of a local graphical login, made by the PAM hook <code>remotix-local-login</code>, until the user's remote desktop is closed."),
    ("Log Out", "The user's request to end the desktop session; it closes the logind session on every desktop."),
    ("Network side", "The part of the server that runs as user <code>remotix</code> with no capability and holds the sockets."),
    ("No orphan desktops", "The rule that a REMOTIX desktop with no child of ours must not stay: the root side ends it."),
    ("Opus", "Audio codec; decoded in the page by a WebAssembly build."),
    ("PAM", "Pluggable Authentication Modules; the login password is checked through the service <code>remotix</code>."),
    ("PipeWire", "Media server used to capture the screen and the sound of the session."),
    ("QUIC", "Encrypted transport over UDP (library ngtcp2, linked statically)."),
    ("RCP/1", "REMOTIX's own protocol, specified in <code>docs/RCP.md</code>."),
    ("Root side", "The part of the server that stays root: PAM, session birth, start of the network side; it answers a closed list of requests."),
    ("Sentinel", "The module (<code>sentinel.c</code>) that asks logind whether a user has a local graphical session; its answer is behind the farewells 0x04 and 0x05."),
    ("Stage", "What a desktop draws on: the compositor and its virtual monitor, with capture and input attached."),
    ("Vulkan Video", "Hardware video encoding through Vulkan; tried first, where the card's driver offers it."),
    ("VA-API", "Video Acceleration API; the way to encode on the card where Vulkan Video is missing (Intel today)."),
    ("Walls", "The ordered list of restrictions put on the network side before it starts (<code>walls.c</code>, applied as root just before the exec): identity, capabilities, mounts, seccomp, Landlock."),
    ("WebTransport", "Streams and datagrams over HTTP/3, used by the page to speak RCP/1."),
]
CHAPTER = ("Glossary", [("Terms used in this manual", dl(TERMS, "gloss"))])
