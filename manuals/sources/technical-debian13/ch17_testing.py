"""Chapter 17 — Testing. Sources: prove/ (all.sh, fresh.sh, matrix.sh, check-*.py, lib.py, browserlib.py, inputlib.py,
avlib.py, deskkit.py, the window scripts, package-snap.py, fanwatch.py, headless-*.sh), boxes/, server/ (vm.sh,
vm-login-test.py, prepara-server.sh); PIANO.md «Stato» sections of 17 Nov 2026; the logs of the dev server."""
from build import arrow, box, c, fig, h4, note, p, rif, sysf, table, term, text, tip, ul, warn, zone

# ── Figure: how a check sees the product ─────────────────────────────────────
RIG = fig(
    zone(20, 14, 410, 160, "Dev server (host)")
    + box(36, 46, 180, 44, "check-*.py", "one verdict line per check", "dark", 12)
    + box(236, 46, 180, 44, "lib.Rig", "compositor + browser + user", "blue", 12)
    + box(36, 112, 180, 44, "headless labwc", "software rendering", "soft", 11.5)
    + box(236, 112, 180, 44, "Chrome / Firefox", "real browser, real input", "soft", 11.5)
    + arrow(217, 68, 234, 68) + arrow(326, 92, 326, 110) + arrow(236, 134, 218, 134)
    + zone(470, 14, 410, 160, "Box (podman container, systemd, one desktop)")
    + box(486, 46, 180, 44, "remotix.service", "installed from the .deb", "navy", 12)
    + box(686, 46, 180, 44, "user session", "the real desktop", "navy", 12)
    + box(686, 112, 180, 44, "test window (GTK)", "logs every event it gets", "green", 11.5)
    + arrow(667, 68, 684, 68) + arrow(776, 92, 776, 110)
    + arrow(417, 134, 484, 80, "#475569", True)
    + text(560, 158, "page and WebTransport on 127.0.0.1", 10.5)
    + arrow(686, 134, 640, 134, "#475569", True)
    + text(600, 128, "log read", 10.5),
    900, 190, "«FIG» — What a check looks at: the browser is driven from outside, the verdict is read from inside the box")

# ── 17.1 ─────────────────────────────────────────────────────────────────────
S1 = p("The tests of REMOTIX are not unit tests of C functions: the tree has no unit-test target, and " + c("src/Makefile")
       + " builds the product only. Every check in " + c("prove/") + " installs the package in a container, drives a real "
       "browser against it the way a person would (real mouse, keyboard and touch events through the browser's debugging "
       "interface), and decides its verdict from what happened <b>inside</b> the box: a window in the user's session that "
       "writes down every event it receives, the journal, logind, the process list.", lead=True) + RIG + \
    p("Rules that hold for every check, taken from the docstrings of " + c("prove/lib.py") + " and of the check files:") + \
    ul([
        "<b>Three verdicts, one line each.</b> A check prints " + c("PASS name - evidence") + ", " + c("FAIL name - evidence")
        + " or " + c("BLOCKED name - evidence") + ", and exits 0 only if every named check is PASS. FAIL means the product did "
        "not do it (this includes: the page does not answer, a valid login is refused). BLOCKED means the tool could not look "
        "(the browser did not start, Marionette did not answer, an earlier step broke). The " + c("Results") + " class of "
        + c("prove/lib.py") + " enforces it: a broken tool step is BLOCKED, never a PASS.",
        "<b>Nothing is shared between runs.</b> Each run starts its own headless labwc in its own runtime directory (class "
        + c("Compositor") + ", started in a private user, network and mount namespace so that it takes none of the host's X "
        "display numbers), its own browser profile, and DevTools or Marionette ports picked by the operating system. That is "
        "what makes it safe to run the four desktops at the same time.",
        "<b>Every wait has a deadline.</b> " + c("guard()") + " sets a whole-run alarm; every failure of the tool is a "
        + c("ToolError") + " that says why. The compositor and the browsers are children of the check and die with it.",
        "<b>The users are the check's own.</b> Each check creates users with a prefix of its own (" + c("bc") + ", " + c("lc")
        + ", " + c("mu") + ", " + c("rs") + ", " + c("ac") + ", " + c("cb") + ", " + c("bn") + ", " + c("dk") + ", " + c("md")
        + ", plus " + c("in") + ", " + c("ph") + " and " + c("pkg") + "), and " + c("sweep()") + " at the end of " + c("all.sh")
        + " ends every session of the prefixes it knows (its pattern lists " + c("bc") + ", " + c("lc") + ", " + c("mu") + ", " + c("rs") + ", " + c("ac") + ", " + c("cb") + ", " + c("bn") + ", " + c("dk") + ", " + c("dkf") + " and " + c("md") + ": the users of " + c("check-input.py") + " and " + c("check-phone.py") + " are not in it; " + c("check-package.py") + " resets the box instead). A login with a user that may not exist is never tried, because a wrong "
        "login counts for the address ban (" + rif("Login and its defences") + ").",
        "<b>Verdicts are built on the application, not on what the browser was told.</b> A key counts as delivered only when "
        + c("window-input.py") + " inside the session logged it.",
    ]) + \
    note("The checks run on the dev server only. They need podman with root access (the boxes), the host's PipeWire-pulse "
         "for Firefox audio, two browsers, " + c("labwc") + " and PIL; " + c("server/prepara-server.sh") + " installs them "
         "after every reboot (the server's root file system is in RAM).", "Where they run.") + \
    p("Nothing in this chapter was run while writing the manual. The results quoted in "
      + rif("What was verified on 17 November 2026, and what was not") + " are the recorded logs of the dev server and the "
      "PIANO.md notes of that day.")

# ── 17.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Everything is under " + c("prove/") + ". The Python files form three layers: libraries, checks, and test windows that "
       "run inside the box.", lead=True) + \
    table(["File", "Role"], [
        "Libraries",
        [c("lib.py"), "the common kit: " + c("Results") + " (verdict lines), " + c("Box") + " (commands in a box through "
         + c("boxes/box.sh") + "), " + c("Compositor") + " (headless labwc), " + c("Chrome") + " (DevTools over a hand-made "
         "WebSocket), " + c("Firefox") + " (Marionette), " + c("Rig") + " (compositor + browser + user: open the page, log "
         "in, wait for the desktop, test window, key chords), " + c("sweep()") + ", and the picture judges " + c("judge_pixel()")
         + " and " + c("frac()")],
        [c("browserlib.py"), "two small browser drivers with the same face (navigate, js, screenshot, move, click, type_text, "
         "press, close), used by " + c("base-check.py") + " and " + c("avlib.py")],
        [c("inputlib.py"), "on top of " + c("lib.py") + ": real mouse buttons, wheel and keys for both browsers, the input test "
         "window and its event log, classification of a cursor image by its pixels, touch and phone emulation (used by "
         + c("check-input.py") + " and " + c("check-phone.py") + ")"],
        [c("avlib.py"), "what " + c("check-audio.py") + " and " + c("check-clipboard.py") + " share (own user, compositor, real "
         "login, key chords); it imports " + c("base-check.py") + " for its page ids and JavaScript bodies"],
        [c("deskkit.py"), "what " + c("check-desktop.py") + " and " + c("check-media.py") + " share: running commands INSIDE the "
         "user's session (the cgroup of the logind scope, the environment of the desktop panel), the file-write watcher, the "
         "counter reader. The tables " + c("PANEL") + " and " + c("LOGOUT") + " hold each desktop's panel process and its own "
         "Log Out command"],
        [c("fanwatch.py"), "a fanotify watcher: who wrote which file under a prefix (used by " + c("settings-intact") + ")"],
        [c("package-snap.py"), "runs inside a box, standard library only: a snapshot of /etc, /usr, /var/lib, /run, users, groups, "
         "units, packages, AppArmor profiles, polkit rules and the nft ruleset, and a diff that says whether a package owns "
         "what appeared (used by " + c("check-package.py") + ")"],
        "Checks",
        [c("check-base.py") + ", " + c("check-lifecycle.py") + ", " + c("check-multiuser.py") + ", " + c("check-desktop.py")
         + ", " + c("check-media.py") + ", " + c("check-resilience.py") + ", " + c("check-audio.py") + ", "
         + c("check-clipboard.py") + ", " + c("check-input.py") + ", " + c("check-phone.py") + ", " + c("check-prelocal.py") + ", " + c("check-ban.py"),
         "the twelve checks that " + c("all.sh") + " runs (next section)"],
        [c("check-package.py"), "the package check: install, first start, remove, purge, reinstall, the refusal of a person "
         "called remotix. NOT part of " + c("all.sh") + ": it resets the box"],
        [c("base-check.py"), "the earlier form of " + c("check-base.py") + " (user " + c("prova") + ", options " + c("--user")
         + " and " + c("--password") + "); still imported by " + c("avlib.py") + " and run by " + c("matrix.sh")],
        "Test windows (copied into the box and started in the user's session)",
        [c("window.py"), "a fullscreen GTK 4 window with one big text entry; one JSON line per event (ready, motion, click, "
         "text); with a colour argument the window is one colour (this is how " + c("check-multiuser.py") + " tells users apart)"],
        [c("test-window.py"), "the same idea, used by " + c("base-check.py") + " and " + c("avlib.py")],
        [c("lifecycle-window.py"), "a variant that adds the window size to every event; no caller was found in " + c("prove/")],
        [c("window-input.py"), "logs EVERY event the application receives: buttons with their repeat count, wheel, every key "
         "with its modifiers, selection, focus, size. Modes " + c("input") + " (fullscreen) and " + c("edge")
         + " (a 640x440 decorated window whose edges can be grabbed)"],
        [c("geom-window.py"), "geometry windows: four coloured quadrants, a 6 px frame and a cross (" + c("frame")
         + "), or a 1800x1000 cyan window with a red border (" + c("scene") + "); flat rectangles at integer pixels, so the "
         "browser's picture can be compared pixel by pixel"],
        [c("media-window.py"), "media windows: a binary-coded counter (" + c("count") + ", " + c("bursts") + "), a moving bar with "
         "a flash and a beep every second (" + c("video") + "), a sharpness pattern (" + c("pattern") + ")"],
        "Shell",
        [c("all.sh"), "every check on ONE box, in sequence, one log per check and a final table"],
        [c("fresh.sh"), "a fresh box with the package installed and the service enabled"],
        [c("matrix.sh"), "every desktop on a fresh box: Chrome (new session) then Firefox (resumed)"],
        [c("headless-wayland.sh"), "start or stop a headless labwc (used by " + c("base-check.py") + " and " + c("avlib.py") + ")"],
        [c("headless-multi.sh"), "the same, but the pid written is labwc's own so that stop really stops it; no caller was found "
         "in " + c("prove/")],
    ], "«TAB» — The files of prove/") + \
    p("The folders " + c("shots/") + " (pictures), " + c("work/") + " and " + c("log/") + " are made by the checks and are not "
      "in git; the logs quoted in this manual are on the dev server, in " + sysf("/media/REMOTIX-DEBIAN/prove/log/") + ".")

# ── 17.3 ─────────────────────────────────────────────────────────────────────
S3 = p("All checks take " + c("--box xfce|lxqt|gnome|kde") + " (ports 8811 to 8814, see " + rif("The four test boxes")
       + "). The limits are the seconds given to each " + c("run") + " call in " + c("all.sh") + "; the verdict names are the "
       + c("NAMES") + " tuples of each file.", lead=True) + \
    table(["Check (limit)", "Verdict names", "What it proves"], [
        [c("check-base.py") + ", Chrome and Firefox (480 s each)",
         c("page") + ", " + c("login") + ", " + c("desktop") + ", " + c("mouse") + ", " + c("keyboard"),
         "the page loads and shows the form; a PAM login is admitted; the decoded picture is not uniform and is still; a click "
         "and typed text reach a window inside the session"],
        [c("check-lifecycle.py") + " (1650 s)",
         c("detach-reattach") + ", " + c("kill-reattach") + ", " + c("reattach-other-size") + ", " + c("logout"),
         "clean close, 30 s, login again: \"resumed\", same window process, same text; the same after kill -9 of the browser; "
         "reattach with a smaller window adapts canvas and desktop; the desktop's own Log Out tells the client, leaves nothing "
         "of the user, and a new login gives a NEW session"],
        [c("check-multiuser.py") + " (960 s)", c("two-users") + ", " + c("three-users") + ", " + c("same-user"),
         "each user's canvas shows its own colour and not the others'; clicks and text reach only the own session; the same user "
         "logging in twice is refused with the 0x0F sentence while the first stays usable, and finds the session again when the "
         "first leaves"],
        [c("check-desktop.py") + " (2500 s)",
         c("power-entries-absent") + ", " + c("no-password-windows") + ", " + c("users-shell-and-environment") + ", "
         + c("settings-intact") + ", " + c("canvas-limits") + ", " + c("reattach-windows-inside") + ", " + c("session-cap") + ", " + c("power-implied"),
         "power actions refused by logind and polkit (15 login1 actions asked, 19 forbidden by the rule) and the box stays up; no polkit password window and no "
         "keyring prompt; the shell and environment of a local login; the user's own settings intact after use and Log Out (file "
         "writes watched with fanotify); canvases from 200x150 to 5120x2880 (multiple of 16, 320x240 to 4096x2304); a window "
         "born in a large canvas is inside after a reattach; with " + c("--session-cap 2") + " the third user is refused"],
        [c("check-media.py") + " (1600 s)",
         c("screen-updates") + ", " + c("video") + ", " + c("codec") + ", " + c("two-sessions-budget"),
         "a counter changing 8 times a second arrives complete and in order; bursts that stop show the last value within a "
         "second; at least 25 fps reach the page; flash and beep stay together (the tool's limits in the code: median 400 ms, drift "
         "150 ms); the negotiated codec, that it is hardware, and the sharpness of stripes, checker and edges; two users at "
         "60 Hz neither falls below 25 fps and the first loses at most 30%"],
        [c("check-resilience.py") + " (2700 s)",
         c("service-restart") + ", " + c("network-drop") + ", " + c("simultaneous-first-login") + ", "
         + c("login-after-other-logout") + ", " + c("clocks"),
         "after " + c("systemctl restart remotix") + " the client is told or returns to the form, the old desktop is closed "
         "with the service (no REMOTIX session of the user and no process of the old window left, the root side's journal "
         "says “the service stops clean”) and a new login is a NEW session with a working desktop; a cut of all UDP (own nft table) for longer than the "
         "silence clock; the same fresh user logging in from two browsers at the same instant, five times: exactly one is "
         "admitted; one user's Log Out does not touch another; the three clocks of SPECS §5.3 at their defaults and, through a "
         "drop-in that is always removed, at short values"],
        [c("check-audio.py") + ", Chrome and Firefox (480 s each)", c("audio-<box>-<browser>"),
         "a 440 Hz tone played in the session is heard in the browser: an AnalyserNode inserted between the page's blocks and "
         "the destination measures RMS and peak frequency, counted only while the AudioContext is running; stage A with no "
         "gesture beyond the login, stage B after a real click"],
        [c("check-clipboard.py") + " (480 s)", c("clipboard-session-to-browser") + ", " + c("clipboard-browser-to-session"),
         "a real Ctrl+C in the session window puts the text in the browser clipboard; a real Ctrl+V in the session receives text "
         "put in the browser clipboard (Chrome only: the permission API is driven by DevTools)"],
        [c("check-input.py") + ", Chrome and Firefox (1500 s each)",
         "24 common (" + c("mouse-*") + ", " + c("pointer-shape-*") + ", " + c("edge-drag") + ", " + c("kbd-*") + ", "
         + c("page-shortcuts-declared") + ", " + c("page-cad-button") + ", " + c("page-cad-chain") + "), "
         + c("page-keyboard-lock") + " (Chrome), two Firefox clipboard lines, " + c("page-ctrl-alt-end") + " last",
         "buttons, double click, wheel, drag, exact coordinates, cursor shape, edge drag, no double cursor; text, Ctrl chords, "
         "Shift+arrows, Alt+Tab, Super, function keys, key repeat, accents, AltGr characters, keys that cannot be produced, Caps "
         "Lock; the page's declared shortcuts and the Ctrl+Alt+Del button and chain"],
        [c("check-phone.py") + " (1250 s)", "19 names, " + c("login-desktop") + " to " + c("reattach-portrait"),
         "the page used as a phone, by emulation: portrait and landscape geometry, tap, drag, two- and three-finger taps, "
         "on-screen keyboard open, text, enter, delete and close, tap-and-half-drag selection, two-finger scroll, pinch zoom, "
         "rotation"],
        [c("check-prelocal.py") + " (900 s)",
         c("P1-hook-closes-desktop") + ", " + c("P2-new-desktop-after") + ", " + c("P3-hook-ignores") + ", " + c("P4-no-desktop")
         + ", " + c("P5-service-stopped") + ", " + c("P6-pam-line-order"),
         "the local-login hold (" + rif("The local-login hold") + "), with Chrome and the check's own users " + c("pl1") + " and " + c("pl2")
         + ". P1: with a remote desktop open the hook returns 0 within 15 s and afterwards nothing of the user is left (no logind "
         "session of the service, no program, no unit of the desktop in the user manager), the page was told with 0x04 and the "
         "journal has the request and the root side's answer. P2: 12 s later (births are refused for 10 s) a new remote login of "
         "the same user gets a working desktop. P3: five calls that are not a local graphical login (no seat, close_session, "
         "greeter, tty, service remotix) each return 0 in under 1 s and the desktop is still alive. P4: a user with no remote "
         "desktop: the hook returns 0 in under 2 s. P5: with the service stopped the hook returns 0 in under 2 s (the service is "
         "started again at the end). P6: " + c("/etc/pam.d/common-session") + " has the " + c("pam_exec") + " line of the hook after the "
         + c("pam_systemd") + " line"],
        [c("check-ban.py") + " (900 s, always last)",
         c("wrong-password") + ", " + c("same-answer") + ", " + c("typed-names-not-logged") + ", " + c("ban-after-limit")
         + ", " + c("ban-survives-restart") + ", " + c("unblock") + ", " + c("unblock-shipped") + ", " + c("cleanup"),
         "a wrong password is refused with one sentence and not before the 2.5 s floor (" + c("REJECT_FLOOR") + " in "
         + c("rcp.c") + "); a non-existent user gets the same sentence and time; no typed name in the log before the verdict; 5 "
         "wrong passwords ban the user and the address ban follows the code's limit (" + c("LIMIT") + " in " + c("rcp.c")
         + " is 5, 20 and 30); the ban survives a restart; the package ships no administrator unblock (by decision)"],
    ], "«TAB» — The checks run by all.sh, in the order all.sh runs them") + \
    h4("Things to know before reading a log") + \
    ul([
        c("check-ban.py") + " is the only check that types wrong passwords, and it bans the address the browser comes from on "
        "that box. To unblock it uses a drop-in with " + c("--command-socket") + " (a bench option of the binary that the packaged "
        "unit never passes; the check adds it through " + c("REMOTIX_OPTIONS") + " in " + c("/etc/remotix/remotix.conf.d/") + ") and at the end it ALWAYS unblocks, removes the drop-in, restarts the service and logs a user in normally "
        "(" + c("cleanup") + "). Run it last and alone on a box.",
        c("check-prelocal.py") + " <b>simulates</b> the local login: the boxes have no display manager, so the hook is run as root "
        "inside the box by hand, with the environment " + c("pam_exec") + " would give it (" + c("PAM_TYPE=open_session") + ", "
        + c("XDG_SEAT=seat0") + ", class " + c("user") + ", type " + c("wayland") + "), and no local session is registered in logind. It "
        "proves the hook and the root side's answer; it does not prove the interplay with the periodic sweeps, which only a real local "
        "login exercises (" + rif("Appendix C — Known issues and open points") + ").",
        c("check-phone.py") + " is an emulation, not a phone: Chrome with DevTools device emulation (412x915 CSS px, device scale 2, "
        "touch events with pointer type touch, a mobile user agent, Italian language). What it cannot prove is listed in "
        + rif("What only a real machine or a real phone can prove") + ".",
        c("check-input.py") + " states its limits in its header: DevTools and WebDriver cannot press AltGr, so the Italian AltGr "
        "characters are sent as the character itself, which exercises the page's LETTER path; the browser's pointer lock and the "
        "operating system's own cursor are in no screenshot, so the cursor is judged by the CSS rule on the canvas.",
        c("check-desktop.py") + " check " + c("session-cap") + " needs a quiet box. " + c("canvas-limits") + " judges the canvas "
        "against SPECS §6.1 (up to 4096x2304), while the page never declares more than 3840x2160 (the last rung of its size ladder, "
        + c("MEASURE_PROBES") + " in " + c("page.html") + "): the check says so in its own evidence line. The <b>declared</b> limit of "
        "the product is 3K (owner's decision, " + c("DECISIONS-11") + " §11.51, confirmed 18 Nov 2026); the sizes above are technical bounds.",
        "The check docstrings can lag behind the code: the docstring of " + c("check-ban.py") + " still describes " + c("unblock-shipped") + " as «the PACKAGE gives the administrator a way to unblock», "
        "while the code passes it when the package ships none. The code is the reference.",
    ])

# ── 17.4 ─────────────────────────────────────────────────────────────────────
S4 = p("A run is one command per desktop, started on the dev server in " + c("prove/") + ". The four desktops can run at the same "
       "time: the runs share nothing (own compositor, browser profile and ports; each box has its own users and files).",
       lead=True) + \
    term("""$ cd /media/REMOTIX-DEBIAN/prove
$ /media/REMOTIX-DEBIAN/prove/all.sh xfce                   # the package already installed in the box
$ /media/REMOTIX-DEBIAN/prove/all.sh gnome --fresh /path/to/remotix_1.0.0-1+deb13_amd64.deb
$ TAG=myround /media/REMOTIX-DEBIAN/prove/all.sh kde        # logs in log/myround/ instead of log/kde-<date>-<time>/""",
         "Running all.sh") + \
    ul([
        c("--fresh <deb>") + " first runs " + c("fresh.sh") + " (reset the box, install the package, enable and start the service, "
        "check it is active); if that fails the run stops and every row is BLOCKED.",
        "The output of each check goes to " + c("log/<tag>/<check>.out") + ", ending with an " + c("exit=<n>") + " line. Each "
        "verdict line becomes one table row " + c("<check>/<name>") + "; a check that printed no verdict line is BLOCKED (\"no "
        "verdict\"), and one that hit its time limit is BLOCKED (\"no answer\").",
        "After the last check " + c("lib.sweep()") + " ends the sessions of the test users; a session left over is a BLOCKED row.",
        "The table is printed and saved as " + c("log/<tag>/summary.txt"
        ) + ". The script exits 0 only if every row is PASS (the last line is " + c("ALL PASS") + ").",
        "SIGTERM, SIGINT and SIGHUP stop the running check and mark the remaining ones BLOCKED (aborted).",
        "The limits of the " + c("run") + " calls add up to 17 860 s (about 4 h 58 min). That is a ceiling, not a measured "
        "duration: no measured duration of a whole run is recorded in the files read for this chapter.",
    ]) + \
    table(["Command", "Use"], [
        [c("prove/fresh.sh <de>"), "a fresh box with the newest " + c("remotix_*.deb") + " under "
         + sysf("/media/REMOTIX-DEBIAN/pacchetti") + ", or the file in " + c("DEB=")],
        [c("prove/matrix.sh [tag]"), "for each desktop: a fresh box, then " + c("base-check.py") + " with Chrome and with Firefox"],
        [c("python3 prove/check-package.py --box <de> --deb <file>"), "the package check (next section)"],
        [c("python3 prove/check-<name>.py --box <de>"), "one check alone; several take " + c("--only a,b") + " to run some names"],
    ], "«TAB» — Running pieces of the suite") + \
    warn(c("fresh.sh") + " calls " + c("boxes/box.sh") + " as " + sysf("$HERE/boxes/box.sh") + ", that is " + sysf("prove/boxes/box.sh")
         + ". In this repository the boxes live in the top-level " + c("boxes/") + ", and only " + c("lib.py") + " knows both "
         "places (its " + c("BOXES") + " variable). On the dev server the folder " + sysf("/media/REMOTIX-DEBIAN/prove/boxes")
         + " exists, so " + c("fresh.sh") + " works there; from a plain checkout it would not find " + c("box.sh")
         + ". The same holds for " + c("matrix.sh") + " and for " + c("all.sh --fresh") + ".", "Layout difference.")

# ── 17.5 ─────────────────────────────────────────────────────────────────────
S5 = p(c("check-package.py") + " tests the .deb itself on a box that it may reset freely. It is not in " + c("all.sh") + ": it "
       "resets the box at the start (and again for the refusal check) and at the end leaves it fresh, with the package installed "
       "and the service enabled (" + c("fresh.sh") + "), so it must not run on a box somebody else is testing.", lead=True) + \
    table(["Verdict name", "What it proves"], [
        [c("install"), "apt install on a fresh box: the expected files only (a snapshot diff from " + c("package-snap.py")
         + "), service installed but NOT enabled and NOT running, system user remotix with nologin shell, nothing listening on 7447; "
         "the hook " + c("remotix-local-login") + " and the profile " + c("/usr/share/pam-configs/remotix") + " are there and "
         + c("pam-auth-update") + " has put the " + c("pam_exec") + " line into " + c("/etc/pam.d/common-session")],
        [c("first-start"), "after enable --now: active, TCP and UDP listening, certificates and secrets with safe modes, no error "
         "in the journal, and the two processes as designed (root side as root; network side as remotix with an empty "
         + c("CapEff") + ", " + c("NoNewPrivs") + " and seccomp on)"],
        [c("apparmor"), "that the network side's profile is loaded and enforcing (a profile loaded in complain mode, as shipped, is a FAIL); BLOCKED if the box has no AppArmor interface. In "
         "the containers it is BLOCKED (securityfs is not mounted); what it can tell is that the profile text compiles with "
         + c("apparmor_parser -Q") + " and that the shipped profile has flags " + c("complain")],
        [c("remove"), "a test user logged in, then apt remove with the session alive: sessions closed, desktop processes gone, "
         "group enrolments undone, /dev/dri grants taken back, the " + c("pam_exec") + " line gone from " + c("common-session")
         + ", service stopped, binary gone, configuration and /var/lib/remotix "
         "kept, no process left, nothing else touched"],
        [c("purge"), "apt purge: everything the package or the program made is gone; the box is as before the install except for "
         "the dependencies apt pulled in"],
        [c("reinstall"), "an install after the purge, and a base login (page, login, desktop)"],
        [c("preinst"), "a PERSON account called remotix (uid at least 1000, a login shell, a home): the install is refused with "
         "the preinst message and the box stays clean"],
        [c("recommends"), "informative: what the install pulled in as Recommends and its size"],
        [c("fresh-end"), "the box is left fresh, with the package installed and the service enabled"],
    ], "«TAB» — The verdict names of check-package.py") + \
    p("What the package contains and how its scripts behave is in " + rif("The package") + ".")

# ── 17.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The boxes are four systemd containers, one per desktop, built from one " + c("boxes/Containerfile") + " with "
       + c("--build-arg DESKTOP=xfce|lxqt|gnome|kde") + ". There is NOTHING of REMOTIX inside the image: the package is installed "
       "later with apt, so the box is what a user's machine looks like before the install.", lead=True) + \
    table(["Box", "Container", "Image", "ssh port", "REMOTIX port (TCP + UDP)", "Desktop packages", "Display manager"], [
        ["xfce", c("rx-xfce"), c("rx/xfce:latest"), "2211", "8811", c("task-xfce-desktop"), c("lightdm")],
        ["lxqt", c("rx-lxqt"), c("rx/lxqt:latest"), "2212", "8812", c("task-lxqt-desktop"), c("sddm")],
        ["gnome", c("rx-gnome"), c("rx/gnome:latest"), "2213", "8813", c("task-gnome-desktop"), c("gdm3")],
        ["kde", c("rx-kde"), c("rx/kde:latest"), "2214", "8814", c("task-kde-desktop"), c("sddm")],
    ], "«TAB» — The four test boxes (ports from boxes/box.sh, packages from boxes/Containerfile)") + \
    p(c("boxes/box.sh") + " is the only entry point. Verbs: " + c("build") + " (image; it generates the ssh key " + c("box-key")
      + ", which is not in git), " + c("boot") + ", " + c("shutdown") + ", " + c("status") + ", " + c("ssh") + " (a command as root "
      "inside, over ssh on 127.0.0.1), " + c("install") + " (copy the .deb in, refresh the package lists as on a real machine, "
      "run " + c("apt-get install -y") + ", then write " + c("REMOTIX_PORT=<port>") + " into " + c("/etc/remotix/remotix.conf.d/10-box-port.conf")
      + " because the default 7447 would clash between boxes), and " + c("reset") + " (throw the container away and boot a "
      "fresh one from the image). The service is left as the package leaves it: disabled and not started; "
      + c("fresh.sh") + " enables it.") + \
    h4("How a box is built and started") + \
    ul([
        "<b>The desktop as a Debian user installs it.</b> The " + c("task-<de>-desktop") + " package with its Recommends, after the "
        "display manager of that desktop has been stated to debconf. " + c("boxes/set-dm.sh") + " then registers the manager as its "
        "postinst would on a real machine (a container build does not do it): " + c("/etc/X11/default-display-manager") + " and the enabled "
        "unit with its " + c("display-manager.service") + " alias. It fails if the registration is not there at the end.",
        "<b>Identity check.</b> " + c("boxes/box-identity.sh") + " is run during the image build as " + c("box-identity debian 13 <de> -")
        + ": an image that is not Debian 13 with that desktop, its display manager and its session files is not built.",
        "<b>systemd as init.</b> " + c("--systemd=always") + ", host network (so every box has its own ports), all of " + c("/dev/dri")
        + ", " + c("memlock") + " unlimited (low-memory-monitor on GNOME calls mlockall), the capabilities a real login needs "
        "(" + c("AUDIT_WRITE") + ", " + c("AUDIT_CONTROL") + ", " + c("SYS_ADMIN") + ", " + c("SYS_NICE") + ", " + c("WAKE_ALARM")
        + ") and a pids limit of 16384. " + c("boot") + " waits up to 120 s for systemd to be running and 90 s for ssh.",
        "<b>No display manager runs.</b> " + c("boxes/common.sh") + " sets the default target to " + c("multi-user.target")
        + " (the box has no monitor), configures sshd on 127.0.0.1 and on the box's port, makes the journal persistent (512 MB cap) and installs "
        + c("box-gruppi") + ", which aligns the box's " + c("video") + " and " + c("render") + " groups with the groups of the host's "
        "DRM nodes (in a box they arrive with the host's numbers).",
        "<b>Sleep questions answered as on a real machine.</b> " + c("boxes/power.sh") + " (run at every boot) mounts a tmpfs copy of "
        + c("/sys/power") + " and restarts logind: in a container " + c("/sys") + " is read-only and logind would answer \"Call failed\" "
        "before asking polkit, so the polkit rule of the package would not be what is tested. The real " + c("/sys/power") + " is not "
        "touched. It also removes " + c("/etc/systemd/sleep.conf.d/remotix-no-suspend.conf") + " if present and restarts logind each time, "
        "so it must not be run on a machine whose administrator switched that belt on.",
        "<b>Test users.</b> Two ordinary users, " + c("prova") + " and " + c("prova2") + ", with the password of the Containerfile "
        "(no sudo). The checks make their own.",
        "<b>KDE.</b> The Plasma Welcome Center is hidden for new users through " + c("/etc/skel") + " so that it does not cover a "
        "first login.",
    ]) + \
    p("The boxes share the host's kernel, network and DRM nodes, which has two known consequences. Xwayland display numbers "
      "and their abstract sockets are shared, and PIANO.md records 33 X screens in all as a limit when many containers run: this "
      "is why " + c("lib.Compositor") + " runs the test compositor in its own network and mount namespace. And inotify limits are "
      "shared by one uid, so " + c("server/prepara-server.sh") + " raises " + c("fs.inotify.max_user_instances") + " to 8192 and "
      + c("fs.inotify.max_user_watches") + " to 1048576.") + \
    note("Some comment headers in " + c("boxes/power.sh") + " and " + c("boxes/box-identity.sh") + " still describe other "
         "distributions and the old bench scripts (" + sysf("17-box.sh") + ", " + sysf("11-box-power.sh") + "); the code that runs is Debian-only. "
         "See " + rif("Where the code is Debian-specific") + " for the clean-up state.", "Stale comments.")

# ── 17.7 ─────────────────────────────────────────────────────────────────────
S7 = p("A container shares the host's kernel, has no real boot and no real device model. For what only a whole machine shows, "
       + c("server/vm.sh") + " runs a real Debian 13 under KVM.", lead=True) + \
    table(["Item", "Value (from server/vm.sh)"], [
        ["image", "Debian 13 " + c("genericcloud") + " qcow2, copied to " + c("disk.qcow2") + " and resized to 20 GB at the first start"],
        ["machine", c("qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 4096") + ", no display, serial log in " + c("serial.log")
         + ", default firmware (SeaBIOS; " + c("server/prepara-server.sh") + " installs no firmware package)"],
        ["first-boot setup", "a cloud-init seed ISO built with genisoimage: user " + c("prova") + " (password " + c("prova")
         + ", passwordless sudo), the key " + c("vmkey")],
        ["network", "QEMU user networking; host 127.0.0.1:2301 to guest 22, and TCP and UDP 127.0.0.1:8901 to guest 7447 (REMOTIX)"],
        ["files", "everything lives in the script's own folder: " + sysf("/media/REMOTIX-DEBIAN/vm")],
        ["commands", c("vm.sh start") + ", " + c("stop") + " (poweroff over ssh, then kill after 30 s), " + c("ssh [cmd]") + ", " + c("status")],
    ], "«TAB» — The virtual machine of server/vm.sh") + \
    p(c("server/vm-login-test.py") + " opens the page of the REMOTIX in the VM (127.0.0.1:8901) with the Chrome driver of "
      + c("prove/lib.py") + " (imported, not modified) and logs in as " + c("prova") + ". It touches no box: the " + c("Rig") + "'s box is "
      "replaced by a stub, because " + c("lib.Box") + " would run commands in the test containers. It prints facts and exits 0 if the "
      "login reached a session; " + c("--bad") + " uses a wrong password. Its " + c("sys.path") + " entry names " + sysf("/media/REMOTIX-DEBIAN/prove")
      + ", so it runs only on the dev server.") + \
    p("The VM has no graphics card exposed to the guest, and the package refuses a NEW installation on a machine with no DRM render "
      "node (" + rif("The package") + "). What PIANO.md records for the VM, on 17 Nov 2026: installation, AppArmor in complain and in enforce "
      "mode with 0 denials up to the connection, reboot, removal and purge without leftovers; a clean refusal where there is no "
      "video card. A graphical session could not be tried there.")

# ── 17.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Each item below is something no file in " + c("prove/") + " or " + c("server/") + " can show, with the reason.", lead=True) + \
    table(["Not proven by the tests", "Why, and what exists instead"], [
        ["AppArmor during a live session",
         "the profile " + c("remotix_network") + " ships in complain mode. In the containers the kernel interface is not mounted "
         "(" + c("check-package.py") + " says BLOCKED); in the VM there is no video card, so no session can be opened. The VM showed "
         "0 denials up to the connection only. PIANO.md: the profile must be observed in a session on a machine with a video card "
         "before it is switched to enforce."],
        ["A real phone",
         "the check emulates one. The header of " + c("check-phone.py") + " lists what only a phone shows: the Android on-screen keyboard "
         "itself (opening, closing, resizing the viewport, back, autocorrection, word composition), the real size and wobble of a "
         "finger (the thresholds 180 ms, 9 px and 40 px were judged by the owner by hand), palm rejection, a real rotation sensor, "
         "Chrome for Android pointer-event differences (Samsung and DeX), decoding on a phone's hardware, a mobile network. The "
         "owner tried Samsung DeX on GNOME on 17 Nov 2026 by hand (PIANO.md)."],
        ["The first touch on GNOME",
         "PIANO.md: GNOME starts in the Overview, which holds touches (a real user sees it too), and one case in thirteen remains "
         "unexplained: the first tap may land at the initial point if the pointer position reaches the page before Mutter is ready. "
         "Not demonstrated; low priority."],
        ["NVIDIA",
         "the first version targets Intel and AMD (PIANO.md); the dev server has an Intel and an AMD card, and the code has a "
         "Vulkan Video route, but no NVIDIA run is recorded."],
        ["Canvases above 3840x2160",
         "the largest canvas obtained by " + c("canvas-limits") + " is 3840x2160: the page's size ladder (" + c("MEASURE_PROBES") + " in "
         + c("page.html") + ") stops there, so the page declares no larger " + c("video.max_size") + " with any browser; SPECS "
         "§6.1 allows up to 4096x2304, which is therefore not proven in the picture (see below). The declared limit of the product is 3K."],
        ["A machine with a real local graphical session",
         "the boxes boot to " + c("multi-user.target") + " with no display manager running. The only automated check of this rule is "
         + c("check-prelocal.py") + ", which covers the 0x04 on the hook's road and simulates the login by calling the hook by hand. "
         "The RCP reason 0x05 (a local session is already active) and the sweeps of the network side and of the root side against a "
         "real local session are not covered by an automated check. The hold was tried by the owner on the four real login screens: GNOME "
         "on the tablet with the journal read; KDE, XFCE and LXQt on live Debian 13 systems, as reported by the owner (journals not read). See " + rif("Appendix C — Known issues and open points") + "."],
        ["Real networks",
         "the tests run on 127.0.0.1. The only fault injected is the nft cut of UDP in " + c("network-drop") + "; loss, jitter, NAT "
         "and mobile links are not exercised by this suite."],
        ["Real keyboards",
         "AltGr is not producible through DevTools or WebDriver; physical layouts other than the emulated Italian one are not "
         "tried."],
        ["Several users on real load",
         "the most users attached together in any check is three (" + c("three-users") + "). The capacity figures are in "
         + rif("Performance and capacity") + "."],
    ], "«TAB» — What the test suite cannot prove") + \
    tip("A statement in this manual that depends on one of the rows above is marked as not verified where it appears.")

# ── 17.9 ─────────────────────────────────────────────────────────────────────
S9 = p("This section reports what PIANO.md and the logs on the dev server say. The code under test is the tree that became "
       "version 1.0.0: PIANO.md states that the provisional version number used in its earlier notes designates the same code, tested under that "
       "number.", lead=True) + \
    h4("The final round of 17 November, 19:40") + \
    p("The round ran " + c("all.sh") + " on the four desktops at the same time with the package " + c("remotix_<provisional>-1+deb13_amd64.deb")
      + " (logs in " + sysf("log/v160-<de>/summary.txt") + " on the server). Each desktop has 118 table rows: 117 verdict lines and the row of the fresh box.") + \
    table(["Desktop", "PASS", "Not PASS", "The lines that are not PASS"], [
        ["XFCE", "111", "7", c("canvas-limits") + "; " + c("page-cad-button") + " and " + c("page-ctrl-alt-end") + " in both browsers; "
         + c("mouse-coordinates") + " in both browsers (the top-right corner is covered by the panel)"],
        ["LXQt", "112", "6", c("canvas-limits") + "; " + c("page-cad-button") + " and " + c("page-ctrl-alt-end") + " in both browsers; "
         + c("audio-lxqt-firefox") + " BLOCKED (Marionette gave no answer in 45 s); a re-run recorded as PASS"],
        ["KDE Plasma", "111", "7", c("canvas-limits") + "; " + c("page-cad-button") + ", " + c("page-cad-chain") + " and "
         + c("page-ctrl-alt-end") + " in both browsers"],
        ["GNOME", "104", "14", c("canvas-limits") + "; " + c("users-shell-and-environment") + " (pkexec; the SHELL variable is empty, "
         "which PIANO.md calls intended); " + c("page-cad-button") + " and " + c("page-ctrl-alt-end") + " in both browsers; the phone "
         "check 7 FAIL and 1 BLOCKED, 18 of 19 PASS when run alone"],
    ], "«TAB» — The round of 17 Nov 2026, 19:40, package with the provisional version number") + \
    p("The explanations that PIANO.md gives for the lines that are not green:") + \
    ul([
        "<b>Ctrl+Alt+Del and Ctrl+Alt+End.</b> The page hides the Ctrl+Alt+Del button unless diagnostics are on (changed on 16 Aug "
        "2026) and no longer keeps Ctrl+Alt+End (removed on 17 Aug). SPECS §7.3-bis and §5.2-bis still promise them, so the "
        "checks fail until the specification is aligned. PIANO.md lists the alignment as pending.",
        "<b>canvas-limits.</b> PIANO.md calls the maximum size 3840x2160 the ceiling of the decoder of the test browser. The evidence line of "
        "the check corrects it: the ceiling is the last rung of the page's own size ladder (" + c("MEASURE_PROBES") + " in " + c("page.html")
        + "), so no client obtains 4096x2304. The larger canvases "
        "(4096x2304, 5120x2880 and wide ones) arrive as 3840x2160 or 3840x1440 and the check judges them as a failure.",
        "<b>XFCE corner.</b> The pointer at the top-right corner falls on the panel, not on the application window.",
        "<b>KDE.</b> The Delete key held down is kept by the desktop (visible in the diagnostic chain check only).",
        "<b>GNOME pkexec.</b> The test user has an empty SHELL variable in that case; PIANO.md calls it intended.",
        "<b>GNOME phone.</b> The failures were of the test: GNOME is born in the Overview, which holds touches. Alone: 18 of 19.",
    ]) + \
    h4("Other results recorded") + \
    ul([
        c("check-package.py") + ": 8 of the 8 checks that can run PASS on the four desktops; " + c("apparmor") + " is BLOCKED in the "
        "containers, so the script itself exits 1 (the log of the XFCE run, " + sysf("v160-pkg-xfce.out") + ", ends with " + c("exit=1")
        + ").",
        "The package check of the new rule \"no installation without a video card\": VM without a card gives a clean refusal; a container "
        "with a card gives 8 of 8.",
        "The earlier round " + c("pulizia1b") + " (after clean-up tranche 1, see " + c("docs/PULIZIA-tranche1.md") + "): 34 PASS lines per "
        "desktop; the summaries on the server hold two more rows that are not PASS on every desktop, " + c("ban/unblock-shipped") + " FAIL (the "
        "check then expected an unblock command; since the decision of 17 Nov its absence is the PASS) and the final sweep BLOCKED. The package of that round carried the provisional label " + c("2.0.0~dev-4") + ". " + c("docs/PULIZIA-tranche1.md") + " also compares the contents of that package and of the one before it, "
        "file by file.",
        "Owner's hand test with Samsung DeX on GNOME (17 Nov): clipboard, audio and video, and window resize all regular.",
        "The package labelled 1.0.0 was built by " + c("build/build-deb.sh") + " (checks R4, R13, R14 SI) and installed in the four boxes; "
        "the logs " + sysf("v100-<de>.out") + " contain only a service-active answer, and the logs " + sysf("v100c-<de>.out") + " record "
        + c("check-base.py") + " and " + c("check-ban.py") + " on a fresh box with that file: 13 PASS lines on each of the four desktops. "
        "No full " + c("all.sh") + " round on the file named 1.0.0 is recorded in the logs read for this chapter.",
    ]) + \
    h4("18 November 2026: the local-login hold and the restart check") + \
    ul([
        c("check-prelocal.py") + " (new): 6 of 6 PASS on the four desktops; the remote desktop was closed by its own child in 0.6 to "
        "1.3 s, the page was told with 0x04, a new desktop could be opened afterwards, calls that are not a local login had no effect, "
        "nothing was slowed with the service stopped, and the PAM line came after " + c("pam_systemd") + ".",
        "A full round after it: 117 PASS lines on GNOME, KDE and XFCE and 119 on LXQt. The lines that were not green were those of "
        "the day before (Ctrl+Alt+Del, Ctrl+Alt+End, the XFCE coordinates, the GNOME " + c("pkexec") + ") and two more: "
        + c("resilience/service-restart") + " on the four desktops, because that check still expected to find the same desktop after "
        "the restart of the service, while since the night of 17 Nov (§11.56) the desktops are closed at the restart; and "
        + c("phone/tap-click-portrait") + " on GNOME (the first tap, a known unstable case, low priority).",
        c("service-restart") + " was then re-aligned (it expects the desktop closed with the service and a NEW session at re-entry) and "
        + c("check-resilience.py") + " was run again on the four desktops: all PASS.",
    ]) + \
    h4("Open items of PIANO.md that touch the tests") + \
    ul([
        "Without a video card the error repeats every 2 seconds in the log; " + c("xfce-chiavi") + " is not removed after the restore.",
        "The AppArmor profile must be observed in a session on a machine with a video card (see above).",
        "XFCE ignores a Log Out requested while it is still starting (desktop behaviour).",
        "The first status of the evening lists Firefox clipboard as open; in the final round the two " + c("clipboard-firefox-*")
        + " lines of " + c("check-input.py") + " are not among the non-PASS lines of any desktop.",
        "Commit, manuals, site and the alignment of the specification text wait for the owner's decision.",
    ])

CHAPTER = ("Testing", [
    ("What a check is and how it decides", S1),
    ("The files of prove/", S2),
    ("The checks of all.sh and what each proves", S3),
    ("Running the suite", S4),
    ("The package check", S5),
    ("The four test boxes", S6),
    ("The real-system virtual machine", S7),
    ("What only a real machine or a real phone can prove", S8),
    ("What was verified on 17 November 2026, and what was not", S9),
])
