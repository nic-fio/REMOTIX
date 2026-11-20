"""User Manual, chapter 4 — when something does not work.
Sources: src/page.html (REASON_TEXT, outcome() calls, DECLARATIONS), src/page.c (ban notice), src/rcp.c (ban
ladder: LIMIT, WINDOW_MS, LADDER_MS), src/main.c, src/log.c, src/session.c (session.log), debian/*."""
from build import c, note, p, rif, sysf, table, term, ui, ul, warn

S_SIGNIN = p("These are the sentences the page shows when you sign in or when the server refuses you. They appear in "
             "red (green only for a normal end of the session) under the form. The page never says more than it "
             "knows, and on purpose it does not say <i>why</i> a password was refused.", lead=True) + \
    table(["What the page says", "What it means", "What you do", "What the administrator does"], [
        [ui("incorrect username or password"),
         "The user name or the password is wrong, or the account is one that cannot sign in (locked, expired, "
         "excluded). The page cannot tell which, by design: a stranger must not learn whether a user name exists.",
         "Check the user name and the password (caps lock, keyboard layout). Careful: every failure counts toward "
         "a temporary ban (see below).",
         "The journal has the detail (see " + rif("Where the administrator looks") + "). Check the account with "
         + c("sudo passwd -S USER") + ", the list in " + sysf("/etc/remotix/denied-users") + " and whether a file "
         + sysf("/etc/nologin") + " exists (it stops everybody but root)."],
        [ui("too many wrong passwords from this address or network: wait (15 minutes the first time, longer if it "
            "happens again): the block ends by itself"),
         "Too many failed sign-ins came from your address or network, or for your user name from your address. "
         "You are banned for a while (see the next section). If you open the page while banned, a red notice "
         + ui("attempts exhausted") + " on the form says how many hours and minutes are left.",
         "<b>Wait.</b> Typing again does not help and does not shorten the wait. An address other than yours (for "
         "example a phone on mobile data) is not affected by your ban.",
         "<b>Nothing: there is no unblock.</b> A ban ends <i>only</i> with time. See "
         + rif("The login defences") + "."],
        [ui("this session's slot shows as taken by another client — if it was you and you just dropped, try again "
            "in a few seconds"),
         "You already have a connected session, and this is a second browser. Or it is your own session whose "
         "connection has just dropped, and the machine has not noticed yet.",
         "Close the tab of the other device, or wait. If you had just dropped, try again: it takes up to about "
         "half a minute (the second sign-in of the same user takes the place of a silent first one after about "
         "15 seconds).",
         "Nothing, normally. One person, one connected browser."],
        [ui("that user is already signed in locally"),
         "Your user has a <b>graphical session at the machine itself</b> (someone signed in at its screen). A "
         "user is either at the machine or in the browser, not both. You see this only after a <i>correct</i> "
         "password.",
         "Sign out at the machine, then sign in again here.",
         "See the sessions with " + c("loginctl list-sessions") + "; the one with a seat and a graphical type is the "
         "local one. Only a graphical session at the machine counts; a text login (ssh, console) does not."],
        [ui("the local session on that machine took precedence"),
         "You were in the browser, and the same user signed in at the machine's own screen. The local session "
         "wins: your remote desktop is closed completely, with its programs, as with Log Out. Unsaved work in it "
         "is lost.",
         "Sign in again after you have signed out at the machine.", "Nothing."],
        [ui("the server could not open your session, and it is not your mistake: try again in a moment, and if it "
            "happens again ask whoever administers the server — the precise reason is in its log"),
         "The server could not give you a desktop. This one sentence covers several different causes, on "
         "purpose: <b>the server is full</b> (the number of sessions has reached the ceiling, 10 by default), the "
         "desktop could not be created, the keyboard layout was not known, memory ran out, or the window is larger "
         "than the browser can decode.",
         "Try again in a moment. If it keeps happening, ask the administrator.",
         "Look in the journal at the time of the attempt (see " + rif("Where the administrator looks") + "). If the "
         "cause is the ceiling, count the sessions and see " + rif("Settings you can change") + "."],
        [ui("the server could not check your password just now, and it is not your mistake: try again in a moment, "
            "and if it happens again ask whoever administers the server"),
         "The machine's password checker did not answer, so your password was not judged at all.",
         "Try again; ask the administrator if it keeps happening.",
         "Look in the journal for “PAM COULD NOT JUDGE”. Check that " + sysf("/etc/pam.d/remotix") + " and "
         + sysf("/etc/remotix/denied-users") + " exist (if the second is missing nobody can sign in)."],
        [ui("this server has no capacity left for another desktop: sessions already open carry on, and a slot "
            "frees up as soon as someone leaves — try again in a moment, and if it happens again ask whoever "
            "administers the server"),
         "The machine has no capacity for one more desktop. It appears only if the administrator has set a "
         "limit based on pixels (it is <i>not</i> set by default), so you will rarely see it.",
         "Try again later.", "A limit set with the option " + c("--budget-mpixel-s") + " is in force: raise or remove "
         "it if it was not meant."],
        [ui("the server and this page have nothing in common to speak"),
         "The server and your browser have no video format in common. The usual cause: <b>the server cannot "
         "encode video</b> (no video card that encodes, or its driver is missing).",
         "Tell the administrator.",
         "Run " + c("sudo /usr/libexec/remotix/remotix --encoding-test h264") + " and look for “THIS SERVER CANNOT "
         "ENCODE VIDEO” in the journal. Install the driver (" + c("va-driver-all") + " for Intel and AMD)."],
        [ui("incompatible protocol version") + "<br>" + ui("the server and this page misunderstood each other: "
                                                           "reload the page and try again"),
         "The page in your browser and the server are not the same version, typically because the server was "
         "upgraded while the page was open.",
         "Reload the page (Ctrl+F5) and sign in again.", "Nothing."],
        [ui("the server does not answer: it is off or unreachable"),
         "The page opened but could not ask the server for its identity.",
         "Check the address and the port; try again.",
         "Is the service running (" + c("systemctl status remotix") + ")? Is TCP 7447 open in the firewall?"],
        [ui("Cannot connect: …") + "<br>" + ui("The server closed the channel without answering…") ,
         "The page could not set up the video and keys connection. The usual cause is that <b>UDP port 7447 is "
         "blocked</b> between you and the machine, while TCP, which carried the page, is open.",
         "Try another network.",
         "Open UDP 7447 as well as TCP (see " + rif("Debian 13: the firewall") + ")."],
        [ui("This browser has no WebTransport: you need Chrome/Edge, Firefox or Safari 26+."),
         "Your browser is too old, or is one that does not have the feature.",
         "Update the browser, or use Chrome, Edge or Firefox.", "Nothing."],
        [ui("Neither of the two video codecs (HEVC, H.264) reaches the pixels on this browser: the session would "
            "have no image. See the box above."),
         "Your browser cannot show video in either format REMOTIX offers.",
         "Update the browser or use another one.", "Nothing."],
    ], "«TAB» — Sentences at sign-in") + \
    note("the page may also show, in a box below the form, a short information line: for example that your "
         "browser does not decode HEVC and H.264 is used instead (the image is there; it uses more bandwidth), or "
         "that “No frame has arrived in N seconds”, with the advice to wait: after a restart the desktop can take "
         "about thirty seconds to start. These lines are for information; they are not errors.", "Information lines.")

S_BAN = p("REMOTIX defends the sign-in against people guessing passwords, with three counters and a ban that grows. "
          "Only <b>failed</b> sign-ins count: a wrong password, or a user name that does not exist. Protocol "
          "errors, timeouts and the refusal of a second connection do not count.", lead=True) + \
    table(["What is counted", "How many failures", "Within", "What is banned"], [
        ["A user name, from one address", "5", "5 minutes", "that user name, from that address"],
        ["One address (any user name)", "20", "5 minutes", "the address"],
        ["One IPv6 network of the /48 size", "30", "10 minutes", "the whole /48 network"],
    ], "«TAB» — The three counters") + \
    ul([
        "<b>The address</b> is the whole IPv4 address, or the /64 network for IPv6. Behind a router that gives "
        "everyone the same address (a home network, a company), people share the address counter. As installed, "
        "REMOTIX listens on IPv4 addresses only, so the IPv6 counters do not come into play.",
        "<b>The ban grows</b> each time it is earned again: <b>15 minutes</b>, then <b>1 hour</b>, then "
        "<b>12 hours</b> (the last step is the longest, however many times it repeats). The memory of earlier bans "
        "is forgotten after 24 hours without a ban.",
        "A <b>correct sign-in</b> clears only the failures of that user name from that address.",
        "The ban <b>survives a restart</b> of the service and of the machine: it is kept in a file.",
        "<b>There is no unblock for the administrator.</b> This is deliberate: no command, no file to edit, no "
        "button. A ban ends only when its time is over. The administrator can only tell the person to wait, or to "
        "use another address.",
    ]) + \
    p("While banned, the page still opens, and it says so in a red notice above the form (" + ui("attempts exhausted")
      + ") with the hours and minutes left, rounded up to the minute. The notice ends with "
      + ui("The block ends by itself when that time is up: there is no other way back in.")) 

S_CLOCKS = p("Three clocks watch a session. They are explained here because their effects are what people notice.",
             lead=True) + \
    table(["Clock", "Default", "What happens", "What the person sees"], [
        ["Silence of the connection", "30 seconds",
         "The browser is considered to have gone: the desktop stays, the place is free. A second browser of the "
         "same user can take it after about 15 seconds of silence.",
         "Nothing; another device may be refused for a few seconds after a drop."],
        ["Inactivity", "30 minutes",
         "No keys, mouse or touch for 30 minutes: the page is disconnected. The desktop is untouched.",
         ui("you went half an hour without touching anything: getting back in needs you, with your password — the "
            "programs stayed open")],
        ["Abandonment", "60 minutes",
         "No keys, mouse or touch for 60 minutes: the desktop and its programs are closed.",
         ui("the session was abandoned") + " (if you were still connected); otherwise, a new empty desktop at the "
         "next sign-in."],
    ], "«TAB» — The three clocks") + \
    p("The administrator can change the last two (see " + rif("Settings you can change") + ").")

S_FAREWELL = p("When a session ends or the connection is lost, the page returns to the sign-in form and explains.",
               lead=True) + \
    table(["What the page says", "What it means"], [
        [ui("the session has ended: the programs were closed"),
         "(Green.) You chose <b>Log Out</b> in the desktop. A normal end; everything was closed."],
        [ui("the session was closed by the user"), "The session was closed at your request."],
        [ui("you went half an hour without touching anything: getting back in needs you, with your password — the "
            "programs stayed open"),
         "The 30-minute inactivity clock. Sign in again."],
        [ui("the session was abandoned"), "The 60-minute abandonment clock: the desktop was closed."],
        [ui("the server is shutting down"),
         "The service is stopping (a restart, an upgrade) or the machine is going down. Your desktop and its "
         "programs are closed; at the next sign-in you get a new desktop."],
        [ui("timed out during the handshake"), "The connection took too long to be set up: try again."],
        [ui("the connection to the server was interrupted: to get back in, type your password again"),
         "The line dropped. The desktop is still there; sign in again. (If the service was restarted, the page "
         "says " + ui("the server is shutting down") + " instead, and the desktop is gone.)"],
        [ui("the session closed because of an error: to get back in type your password again — the precise reason "
            "is in the log"),
         "The page closed the connection because of a fault. The desktop is still there; sign in again and tell "
         "the administrator if it repeats."],
        [ui("The session closed: the server sent something that does not add up with RCP."),
         "A protocol fault. Reload the page and sign in again."],
    ], "«TAB» — How a session ends")

S_ADMIN = p("The administrator has three places to look, and three quick checks.", lead=True) + \
    p("<b>1. The journal.</b> REMOTIX writes to the systemd journal. Everything REMOTIX says, including the "
      "processes it starts for each user's desktop, carries the identifier <code class=\"sys\">remotix</code>:") + \
    term("$ sudo journalctl -u remotix                     # the service, from its start\n"
         "$ sudo journalctl -t remotix                     # every REMOTIX line, users' sessions included\n"
         "$ sudo journalctl -t remotix -p warning -b       # only warnings and errors since the boot\n"
         "$ sudo journalctl -t remotix -f                  # follow it live", "The journal") + \
    table(["Priority", "Mark in the line", "What it means"], [
        ["error (3)", "starts with ⛔", "something is wrong that needs attention: for example a new ban, "
                                      "a missing component, a failure to start."],
        ["warning (4)", "starts with ⚠", "something went wrong but REMOTIX carried on: for example a connection "
                                       "dropped, a session not ready yet, the audio of a session lost."],
        ["info (6)", "no mark", "normal events: a desktop born, a client leaving, the start-up report."],
    ], "«TAB» — The priorities of the journal") + \
    p("Lines about one user's session also carry the field " + c("REMOTIX_TENANT") + " (the user name), and every "
      "line carries " + c("REMOTIX_AREA") + ", the part of the program that wrote it. For example "
      + c("sudo journalctl -t remotix REMOTIX_TENANT=anna") + ".") + \
    p("At every start the service writes a report. Useful lines: “the desktop of this machine: …” (which desktop it "
      "found), “video.codec offered …” (the video card encodes) or “THIS SERVER CANNOT ENCODE VIDEO” (it does not), "
      "and the PAM service line (the sign-in file is there).") + \
    p("<b>2. The user's own session log.</b> Each desktop writes its own output to "
      + sysf("~/.local/state/remotix/session.log") + " in the user's home (if that folder cannot be used, to "
      + sysf("remotix-session.log") + " in the user's runtime folder, which disappears with the session). Useful "
      "when the desktop is born but something in it does not start.") + \
    p("<b>3. Three quick checks:</b>") + \
    term("$ systemctl status remotix                      # running?\n"
         "$ sudo ss -ltnup | grep 7447                    # listening on TCP and UDP?\n"
         "$ sudo /usr/libexec/remotix/remotix --encoding-test h264   # does the card encode? (exit 0 = yes)",
         "Quick checks")

S_DESIGN = p("Some things REMOTIX does not offer, deliberately. They are not defects.", lead=True) + \
    ul([
        "<b>No power off, restart, suspend or hibernate</b> from a remote desktop. The entries are not in the "
        "menus, and the machine refuses the request from any user, at the machine or remote. "
        + c("sudo systemctl poweroff") + " as the administrator still works.",
        "<b>No unblocking of a ban by the administrator.</b> A ban ends with time (see " + rif("The login defences")
        + ").",
        "<b>No screen lock</b> inside the remote desktop; the sign-in page is the only door.",
        "<b>No remote sign-in for root</b>, and none for a user at the machine's own screen.",
        "<b>One session per user, one connected browser at a time.</b>",
        "<b>The page cannot send</b> the key combinations that the browser keeps (see " + rif("The keyboard") + ").",
    ])

CHAPTER = ("When something does not work", [
    ("What the page says when you sign in", S_SIGNIN),
    ("The login defences", S_BAN),
    ("The three clocks", S_CLOCKS),
    ("How a session ends", S_FAREWELL),
    ("Where the administrator looks", S_ADMIN),
    ("What cannot be done, by design", S_DESIGN),
])
