"""User Manual, chapter 2 — installing the server, and the first connection.
Sources: installer/run.sh, installer/cmd/remotix-install/main.go, installer/engine/texts.go and codes.go,
installer/ui/texts.go, installer/catalog/catalog.json (the distribution table is generated from it),
packaging/ (unit, conf, denied-users, firewall definitions, release.sh), src/certificates.c, src/page.html."""
import json

from build import ROOT, c, esc, note, p, rif, steps, table, term, tip, ul, warn

CAT = json.loads((ROOT / "installer" / "catalog" / "catalog.json").read_text())
NAMES = {"gnome": "GNOME", "kde": "KDE Plasma", "xfce": "XFCE", "lxqt": "LXQt"}
RUN = "remotix-X.Y.Z-R.run"


def distributions():
    """The platforms of the catalogue the release builds a package for (those in the matrix)."""
    rows = []
    for pl in CAT["platforms"]:
        if not pl.get("matrix"):
            continue
        desk, notes = [], []
        for d in ("gnome", "kde", "xfce", "lxqt"):
            dc = pl["desktop"].get(d) or {}
            if not dc.get("supported"):
                continue
            desk.append(NAMES[d])
            if dc.get("requires_3d"):
                notes.append(esc(dc["requires_3d"]) if isinstance(dc["requires_3d"], str)
                             else NAMES[d] + " needs a card with 3D acceleration")
            notes += [esc(x) for x in dc.get("limits", [])]
        for r in pl.get("repositories", []):
            notes.append("the " + esc(CAT["repositories"].get(r, {}).get("name", r)) + " repository must be enabled")
        der = [d["name"] for d in pl.get("derivatives", []) if d["id"] != "linuxmint"]
        if der:
            notes.append("also " + ", ".join(der) + " (compatible, not certified)")
        rows.append([esc(pl["name"]), esc(pl.get("version_label", ", ".join(pl["versions"]))), ", ".join(desk),
                     "; ".join(notes) or "—"])
    return table(["Distribution", "Version", "Desktops", "Notes"], rows,
                 "«TAB» — The seven distributions, read from the installer's catalogue (" + c(CAT["version"]) + ")")


REQ = CAT["requirements"]

S_REQ = p("REMOTIX is installed on the Linux machine whose desktop people will use. Before starting, check these "
          "points: the installer checks them too, and stops before touching anything if one is missing.", lead=True) + \
    table(["Requirement", "Details"], [
        ["A 64-bit PC", "x86_64."],
        ["One of the seven distributions", rif("The seven distributions") + "."],
        ["A desktop already installed", "GNOME " + esc(REQ["gnome_minimum"]) + ", KDE Plasma " + esc(REQ["kde_minimum"])
         + ", XFCE " + esc(REQ["xfce_minimum"]) + " or LXQt " + esc(REQ["lxqt_minimum"]) + " or newer. REMOTIX does "
         "not install a desktop."],
        ["A graphics card that encodes video", "REMOTIX encodes the picture only on the graphics card, never on the "
         "processor. Intel and AMD cards work through VA-API; AMD and NVIDIA through Vulkan Video. NVIDIA needs the "
         "proprietary driver 550 or newer with its Vulkan driver. Without such a card REMOTIX is not installed."],
        ["systemd and OpenSSL " + esc(REQ["openssl_minimum"]) + " or newer", "All seven distributions have them."],
        ["Administrator access", "The installation runs with " + c("sudo") + "."],
        ["The port", "Port 7447, TCP and UDP, free on the machine and open in its firewall (" + rif("Firewall and port")
         + ")."],
    ], "«TAB» — What the machine needs")

S_DISTROS = p("REMOTIX ships one package for each of these distributions, all inside one installation file. "
              "The installer refuses any other distribution, except the derivatives named in the table.", lead=True) + distributions() + \
    note("on AlmaLinux and RHEL 10 only GNOME and KDE Plasma are supported. KDE there runs inside REMOTIX's own "
         "copy of labwc 0.8.4, installed at " + c("/usr/lib/remotix/labwc") + " (GPL-2.0; its source is published "
         "next to each release).", "AlmaLinux and RHEL 10.") + \
    p("Out of scope: Debian 12, Ubuntu 24.04, RHEL 9 and its rebuilds, openSUSE Leap 15; Linux Mint (Mint 22 is excluded, "
      "being based on Ubuntu 24.04, and the installation file has no package for Mint 23); distributions without "
      "systemd; immutable distributions (Silverblue, Kinoite, Aeon, Kalpa, Ubuntu Core, SteamOS).")

CHECK = f"""$ sh {RUN} check
REMOTIX — machine check (read only: nothing was touched)
…
The desktops:
…
Warnings and problems:
…"""

S_CHECK = p("REMOTIX is delivered as one file, " + c(RUN) + " (X.Y.Z is the version, R the package revision). "
            "It contains the installer and the REMOTIX packages for all seven distributions; whatever else is needed "
            "comes from the distribution's own repositories, through its package manager.", lead=True) + \
    p("Before installing you can ask the file what it thinks of the machine. This only reads, needs no "
      "administrator rights and changes nothing:") + term(CHECK, "Checking the machine") + \
    p("The report lists the four desktops (installed or not, and whether supported), then the warnings and "
      "problems, each with a code such as " + c("RX-GPU-005") + ". A section headed “MISSING — REMOTIX does not "
      "install it: providing it is up to the administrator:” lists what you must provide before installing — for "
      "example a supported desktop (" + c("RX-MANCA-001") + ") or a repository (" + c("RX-MANCA-002") + ").")

INSTALL = f"""$ sudo sh {RUN}
The plan (installation, …):
  1. …  [BEST_EFFORT]
  2. …  [EXACT]
  …
What the package manager will do (its own simulation):
  …

Port: 7447 (TCP+UDP) — use --port N to change it

Proceed? [y/N] y
…
operation …: CONFIRMED
From outside the local network: forward port 7447, TCP and UDP, on the router to this machine (REMOTIX does not do it by itself: no UPnP)."""

S_INSTALL = p("Copy the " + c(".run") + " file to the machine and run it as administrator. It works like "
              + c("apt") + ": it shows what it is going to do, asks once, and only then acts.", lead=True) + \
    steps([
        "Run " + c(f"sudo sh {RUN}") + ". Without " + c("sudo") + " it stops with “run it as administrator: sudo sh "
        "…”. The file first checks itself; if it was damaged in the download it says “the file is damaged … "
        "download it again”.",
        "The installer examines the machine (the same checks as " + c("check") + ").",
        "It prints <b>the plan</b>: the steps it will take (install the packages, add people to the graphics-card "
        "groups, start the service), each marked with how it can be undone; then, under “What the package manager "
        "will do (its own simulation):”, the exact list of packages with versions, as the package manager itself "
        "worked it out; last, the port it will use (“Port: 7447 (TCP+UDP) — use --port N to change it”, or "
        "the one given with " + c("--port N") + "). Nothing has been touched yet.",
        "If something is missing, the plan ends with the MISSING list and the line “REMOTIX is not installed: "
        "nothing was touched. Run it again when what is missing is there.”",
        "Otherwise it asks " + c("Proceed? [y/N]") + ". Only " + c("y") + " or " + c("yes") + " go ahead; anything "
        "else, or just Enter, answers no and prints “Nothing was touched.”",
        "It installs, starts the " + c("remotix.service") + " service, and checks the result: the graphics card "
        "must really encode a frame, the sign-in configuration must be complete. If a required check fails, "
        "everything it did is undone.",
        "At the end it prints the operation and its result — " + c("CONFIRMED") + ", or "
        + c("CONFIRMED_WITH_CONDITIONS") + " when something needs your attention (typically the firewall) — and "
        "reminds you about the router.",
    ]) + term(INSTALL, "An installation (shortened)") + \
    p("Options you can add after the file name:") + \
    table(["Option", "Effect"], [
        [c("--port N"), "Use port N instead of 7447 (TCP and UDP). It is written to "
         + c("/etc/remotix/remotix.conf.d/port.conf") + "."],
        [c("--users A,B"), "Give the graphics-card permissions only to these users (comma separated). Without it, "
         "every person with an account on the machine gets them."],
    ], "«TAB» — Installation options") + \
    tip(c(f"sudo sh {RUN} tui") + " runs the same installation in a text interface, with four steps (Check, Plan, "
        "Install, Ready): " + c("Enter") + " continues, " + c("d") + " shows details, " + c("y") + " / " + c("n")
        + " answer the question, " + c("Tab") + " changes the port. The last screen shows the addresses to open, "
        "the certificate fingerprint and who can sign in.", "The text interface.") + \
    note("if an installation was interrupted (power cut, closed terminal), the next run first rolls it back, so "
         "the machine is never left half installed, then starts again from the beginning.", "Interrupted.")

S_USERS = p("People sign in with <b>their Linux user name and password on that machine</b> — the same ones they "
            "would use for ssh. There is no separate list of REMOTIX users.", lead=True) + \
    ul([
        "<b>root cannot sign in.</b> The names in " + c("/etc/remotix/denied-users") + " (one per line; it contains "
        + c("root") + ") are always refused. Add other names there to keep them out.",
        "<b>Graphics-card groups.</b> To use the card, a desktop's user must be in the groups that own it (for "
        "example " + c("render") + " and " + c("video") + "). The installer adds every person on the machine (or "
        "those given with " + c("--users") + "); someone created later is added automatically the first time they "
        "connect.",
        "<b>New users</b> need nothing else: create the account as usual, and they can sign in.",
        "<b>Wrong passwords.</b> After five wrong passwords for the same user within five minutes, that user has to "
        "wait before trying again: 15 minutes the first time, then 1 hour, then 12 hours if it keeps happening "
        "(the count starts again after a day without blocks). Other users on the same network are not blocked, unless "
        "there are very many errors from that network: then the whole network waits. A correct password clears the "
        "count of that user. The blocks are kept in " + c("/var/lib/remotix/ban") + ", which "
        "REMOTIX reads only when it starts. To lift them all at once: " + c("sudo systemctl stop remotix")
        + ", delete " + c("/var/lib/remotix/ban") + ", " + c("sudo systemctl start remotix") + ". Open desktops are "
        "not closed by the restart. The administrator can also lift the block of one address at once with the "
        + c("UNBLOCK") + " command, if the server was started with its command socket.",
        "<b>One desktop per user.</b> Someone signed in at the machine itself (in front of its screen) cannot open "
        "a REMOTIX session at the same time.",
    ])

S_FIREWALL = p("REMOTIX uses one port, <b>7447</b>, on both <b>TCP</b> (the page) and <b>UDP</b> (the desktop "
               "itself). The installer does not change the firewall: if one is on, it says so in the plan and at "
               "the end, and you open the port yourself.", lead=True) + \
    table(["Firewall", "Command"], [
        ["firewalld (Fedora, AlmaLinux, openSUSE, Arch)", c("sudo firewall-cmd --permanent --add-service=remotix")
         + " then " + c("sudo firewall-cmd --reload") + " (the " + c("remotix") + " service is defined by the "
         "package)"],
        ["ufw (Debian, Ubuntu)", c("sudo ufw allow REMOTIX") + " (the " + c("REMOTIX") + " profile is defined by "
         "the package)"],
    ], "«TAB» — Opening port 7447") + \
    p("With another port (" + c("--port N") + "), open that port, TCP and UDP, instead of the service or profile.") + \
    p("<b>From outside your home or office network</b>, the router must also forward the port, TCP and UDP, to the "
      "machine. REMOTIX does not do this itself (no UPnP).")

S_CERT = p("The connection is encrypted with a certificate. At its first start REMOTIX makes its own, valid for "
           "365 days, in " + c("/var/lib/remotix/certificates") + ". Browsers do not know it, so the first time a "
           "device connects the browser shows a warning (" + rif("The first connection") + ").", lead=True) + \
    ul([
        "<b>The name in the certificate</b> is the machine's name. If people connect with the IP address instead, "
        "write it in a file of " + c("/etc/remotix/remotix.conf.d/") + ", for example "
        + c("REMOTIX_OPTIONS=--name 192.168.1.10") + ", and restart the service with "
        + c("sudo systemctl restart remotix") + ". A name that does not match makes the browser show a different, "
        "harder warning.",
        "<b>When it expires</b>, REMOTIX makes a new one, and browsers show the warning once more.",
        "<b>A real certificate</b>: whoever has a domain name can use their own. Put the certificate (PEM, the "
        "full chain may follow it in the same file) in " + c("page.pem") + " and its private key (PEM) in "
        + c("page.key") + ", in " + c("/var/lib/remotix/certificates") + ", and delete " + c("page.ours")
        + ": that file marks a certificate REMOTIX made itself, which it replaces when it expires. Restart the "
        "service. A certificate without that mark is used as it is and never replaced, not even when it expires — "
        "renewing it is up to you. If the key does not match the certificate, the service does not start and its "
        "log says so.",
    ])

S_FIRST = p("Once the service runs, anyone with an account can connect from a browser.", lead=True) + \
    steps([
        "Open " + c("https://<machine>:7447") + " — the machine's name or address, and the port.",
        "<b>The first time on each device</b>, the browser warns that the connection is not private or the "
        "certificate is not trusted. This is expected: open the details and choose to continue to the site. The "
        "browser remembers the choice.",
        "The page “Sign in” appears. Type your <b>Username</b> and <b>Password</b> on the server and press "
        "<b>Connect</b>.",
        "Your desktop appears, as large as the window. If the window changes size later, the picture is scaled; "
        "the desktop takes the new size the next time you sign in.",
        "To finish, choose “Log Out…” in the desktop's own menu. Just closing the tab leaves the desktop running ("
        + rif("Your session waits for you") + ").",
    ]) + \
    table(["The page says", "What to do"], [
        ["incorrect username or password", "Check the user name and password on the server; mind the keyboard "
         "layout."],
        ["attempts exhausted … There are still … hours and … minutes to go", "Too many wrong passwords: wait until "
         "the time runs out, or ask the administrator to lift the block ("
         + rif("Who can sign in") + ")."],
        ["this session's slot shows as taken by another client …", "You are still connected from another device, "
         "or just dropped: close the other tab, or wait a few seconds and try again."],
        ["that user is already signed in locally", "Sign out at the machine itself first."],
        ["this server has no capacity left for another desktop …", "Too many desktops are open: try again later."],
        ["the server could not open your session, and it is not your mistake …", "Ask the administrator: the "
         "reason is in the server's log (" + rif("Where the logs are") + ")."],
    ], "«TAB» — The messages a user meets most often")

CHAPTER = ("Installing the server", [
    ("What the machine needs", S_REQ),
    ("The seven distributions", S_DISTROS),
    ("The installation file", S_CHECK),
    ("Installing", S_INSTALL),
    ("Who can sign in", S_USERS),
    ("Firewall and port", S_FIREWALL),
    ("The certificate", S_CERT),
    ("The first connection", S_FIRST),
])
