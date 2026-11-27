"""Chapter 17 — Testing. Sources: prove/ (all.sh, fresh.sh, matrix.sh, check-*.py, prelocal.sh, hold*.py, lib.py, browserlib.py, inputlib.py,
avlib.py, deskkit.py, the window scripts, package-snap.py, fanwatch.py, headless-*.sh, banco-vm/), server/ (vm-radeon*.sh,
prepara-server-vm.sh, live-installa.sh, VM-BANCO.md), boxes/ and server/ vm.sh, vm-login-test.py, prepara-server.sh (the older container
files, still in the tree); docs/STORIA-ubuntu-26.04.md of 19 Nov 2026; docs/REGISTRO-problemi.md (sections F, G, H); studio/giro*.md; studio/prove-1.2.0/;
the logs of the dev server (log/, albero/prove/log/)."""
from build import arrow, box, c, code, fig, h4, note, p, rif, sysf, table, term, text, tip, ul, warn, zone

# ── Figure: how a check sees the product ─────────────────────────────────────
RIG = fig(
    zone(20, 14, 410, 160, "Dev server (host)")
    + box(36, 46, 180, 44, "check-*.py", "one verdict line per check", "dark", 12)
    + box(236, 46, 180, 44, "lib.Rig", "compositor + browser + user", "blue", 12)
    + box(36, 112, 180, 44, "headless labwc", "software rendering", "soft", 11.5)
    + box(236, 112, 180, 44, "Chrome / Firefox", "real browser, real input", "soft", 11.5)
    + arrow(217, 68, 234, 68) + arrow(326, 92, 326, 110) + arrow(236, 134, 218, 134)
    + zone(470, 14, 410, 160, "Virtual machine of the bench (Ubuntu 26.04, systemd, AppArmor, one desktop)")
    + box(486, 46, 180, 44, "remotix.service", "installed from the .deb", "navy", 12)
    + box(686, 46, 180, 44, "user session", "the real desktop", "navy", 12)
    + box(686, 112, 180, 44, "test window (GTK)", "logs every event it gets", "green", 11.5)
    + arrow(667, 68, 684, 68) + arrow(776, 92, 776, 110)
    + arrow(417, 134, 484, 80, "#475569", True)
    + text(560, 158, "page and WebTransport on the machine's port", 10.5)
    + arrow(686, 134, 640, 134, "#475569", True)
    + text(600, 128, "log read", 10.5),
    900, 190, "«FIG» — What a check looks at: the browser is driven from outside, the verdict is read from inside the virtual machine")

# ── 17.1 ─────────────────────────────────────────────────────────────────────
S1 = p("The tests of REMOTIX are not unit tests of C functions: the tree has no unit-test target, and " + c("src/Makefile")
       + " builds the product only. Every check in " + c("prove/") + " works on one of the four virtual machines of the bench (" + rif("The VM bench") + ") with the package installed: it drives a real "
       "browser against it the way a person would (real mouse, keyboard and touch events through the browser's debugging "
       "interface), and decides its verdict from what happened <b>inside</b> the machine: a window in the user's session that "
       "writes down every event it receives, the journal, logind, the process list.", lead=True) + RIG + \
    p("Rules that hold for every check, taken from the docstrings of " + c("prove/lib.py") + " and of the check files:") + \
    ul([
        "<b>Three verdicts, one line each.</b> A check prints " + c("PASS name - evidence") + ", " + c("FAIL name - evidence")
        + " or " + c("BLOCKED name - evidence") + ", and exits 0 only if every named check is PASS. FAIL means the product did "
        "not do it (this includes: the page does not answer, a valid login is refused). BLOCKED means the tool could not look "
        "(the browser did not start, Marionette did not answer, an earlier step broke). The " + c("Results") + " class of "
        + c("prove/lib.py") + " enforces it: a broken tool step is BLOCKED, never a PASS. " + c("all.sh") + " adds two kinds of row that are not verdicts, "
        + c("SKIP (reason)") + " and " + c("NOTE") + " (" + rif("Running the suite") + ").",
        "<b>Nothing is shared between runs.</b> Each run starts its own headless labwc in its own runtime directory (class "
        + c("Compositor") + ", started in a private user, network and mount namespace so that it takes none of the host's X "
        "display numbers), its own browser profile, and DevTools or Marionette ports picked by the operating system. On the VM "
        "bench the Radeon is handed to one machine at a time, so the desktops are tried one after the other.",
        "<b>Every wait has a deadline.</b> " + c("guard()") + " sets a whole-run alarm; every failure of the tool is a "
        + c("ToolError") + " that says why. The compositor and the browsers are children of the check and die with it. The environment "
        "variable " + c("RX_TEMPO") + " (an integer of at least 1, anything else is refused, never read as «no deadline») multiplies every deadline: "
        "the VM bench runs with 2 (" + c("all.sh") + " sets it).",
        "<b>The users are the check's own.</b> Each check creates users with a prefix of its own (" + c("bc") + ", " + c("lc")
        + ", " + c("mu") + ", " + c("rs") + ", " + c("ac") + ", " + c("cb") + ", " + c("bn") + ", " + c("dk") + ", " + c("dkf") + ", " + c("md")
        + ", " + c("in") + ", " + c("ph") + ", " + c("pl") + ", followed by digits; " + c("check-package.py") + " uses " + c("pkg") + " and a desktop prefix), and "
        + c("sweep()") + " at the end of " + c("all.sh")
        + " ends every session of the thirteen prefixes just listed (the pattern is the same in " + c("lib.py") + " and in " + c("prove/banco-vm/fresh-vm.sh")
        + ", which also deletes the users). The checks that are not in " + c("all.sh") + " use the prefix " + c("kx") + " (" + c("check-exit.py") + ", " + c("check-kde-exit.py") + "), which the pattern does not contain: the check removes its own user. A login with a user that may not exist is never tried, because a wrong "
        "login counts for the address ban (" + rif("Login and its defences") + ").",
        "<b>Verdicts are built on the application, not on what the browser was told.</b> A key counts as delivered only when "
        + c("window-input.py") + " inside the session logged it.",
    ]) + \
    note("The checks run on the dev server only. They need QEMU with OVMF and the vfio set-up (the VM bench), "
         "the host's PipeWire-pulse for Firefox audio, two browsers, " + c("labwc") + " and PIL; " + c("server/prepara-server-vm.sh") + " installs "
         "them after every reboot (the server's root file system is in RAM; no podman and no container). There are no containers on the bench: tests and studies run on virtual machines.", "Where they run.") + \
    p("Nothing in this chapter was run while writing the manual. The results quoted in "
      + rif("What was verified on Ubuntu 26.04, and what was not") + " are the recorded logs of the dev server and the "
      "notes of " + c("docs/STORIA-ubuntu-26.04.md") + " and of the register of problems.")

# ── 17.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Everything is under " + c("prove/") + ". The Python files form three layers: libraries, checks, and test windows that "
       "run inside the virtual machine.", lead=True) + \
    table(["File", "Role"], [
        "Libraries",
        [c("lib.py"), "the common kit: " + c("Results") + " (verdict lines), " + c("Box") + " (commands in a box through "
         + c("box.sh") + "; the one of " + c("boxes/") + ", or the one of " + c("prove/banco-vm/") + " when " + c("RX_BANCO=vm") + "), " + c("Compositor") + " (headless labwc), " + c("Chrome") + " (DevTools over a hand-made "
         "WebSocket), " + c("Firefox") + " (Marionette), " + c("Rig") + " (compositor + browser + user: open the page, log "
         "in, wait for the desktop, test window, key chords), " + c("sweep()") + ", the picture judges " + c("judge_pixel()")
         + " and " + c("frac()") + ", the port table (8841 to 8844 for the VMs " + c("gnome") + ", " + c("kde") + ", " + c("xfce") + ", " + c("lxqt")
         + "; the table keeps the 8821 to 8824 of the older container boxes) and " + c("Box.apparmor()") + ", which reads the kernel journal for lines of the profile " + c("remotix_network") + " (" + c("check-apparmor.py") + ")"],
        [c("browserlib.py"), "two small browser drivers with the same face (navigate, js, screenshot, move, click, type_text, "
         "press, close), used by " + c("base-check.py") + " and " + c("avlib.py")],
        [c("inputlib.py"), "on top of " + c("lib.py") + ": real mouse buttons, wheel and keys for both browsers, the input test "
         "window and its event log, classification of a cursor image by its pixels, touch and phone emulation (used by "
         + c("check-input.py") + " and " + c("check-phone.py") + ")"],
        [c("avlib.py"), "what " + c("check-audio.py") + " and " + c("check-clipboard.py") + " share (own user, compositor, real "
         "login, key chords); it imports " + c("base-check.py") + " for its page ids and JavaScript bodies. Its private PulseAudio of the lxqt container "
         "(127.0.0.1:4713) does not exist in a VM: there " + c("ensure_pulse()") + " answers «SKIP on the VMs» and the checks use the host's PipeWire"],
        [c("deskkit.py"), "what " + c("check-desktop.py") + " and " + c("check-media.py") + " share: running commands INSIDE the "
         "user's session (the cgroup of the logind scope, the environment of the desktop panel), the file-write watcher, the "
         "counter reader. The tables " + c("PANEL") + " and " + c("LOGOUT") + " hold each desktop's panel process and its own "
         "Log Out command"],
        [c("fanwatch.py"), "a fanotify watcher: who wrote which file under a prefix (used by " + c("settings-intact") + ")"],
        [c("package-snap.py"), "runs inside a box, standard library only: a snapshot of /etc, /usr, /var/lib, /run, users, groups, "
         "units, packages, AppArmor profiles, polkit rules and the nft ruleset, and a diff that says whether a package owns "
         "what appeared (used by " + c("check-package.py") + "). It ignores " + sysf("/var/lib/snapd") + ", " + sysf("/run/snapd*") + ", " + sysf("/var/lib/cloud")
         + " and " + sysf("/run/cloud-init") + ", which Ubuntu changes by itself"],
        "Checks",
        [c("check-base.py") + ", " + c("check-lifecycle.py") + ", " + c("check-multiuser.py") + ", " + c("check-desktop.py")
         + ", " + c("check-media.py") + ", " + c("check-resilience.py") + ", " + c("check-audio.py") + ", "
         + c("check-clipboard.py") + ", " + c("check-input.py") + ", " + c("check-phone.py") + ", " + c("check-prelocal.py") + ", " + c("check-ban.py"),
         "twelve of the thirteen checks that " + c("all.sh") + " runs (next section)"],
        [c("check-apparmor.py"), "the thirteenth check of " + c("all.sh") + ": the kernel journal of the whole round holds no line of the AppArmor profile " + c("remotix_network") + " (verdict " + c("profile-coverage") + "); see the next section"],
        [c("check-exit.py") + ", " + c("check-kde-exit.py"), "the ways a remote desktop ends leave nothing behind (XFCE and LXQt; KDE). NOT part of " + c("all.sh") + "; see " + rif("The tools of the 1.2.0 work")],
        [c("check-package.py"), "the package check: install, first start, remove, purge, reinstall, the refusal of a person "
         "called remotix. NOT part of " + c("all.sh") + ": it resets the box, which a VM cannot do (" + rif("The package check") + ")"],
        [c("base-check.py"), "the earlier form of " + c("check-base.py") + " (user " + c("prova") + ", options " + c("--user")
         + " and " + c("--password") + "); still imported by " + c("avlib.py") + " and run by " + c("matrix.sh")],
        "Test windows (copied into the box and started in the user's session)",
        [c("window.py"), "a fullscreen GTK 4 window with one big text entry; one JSON line per event (ready, motion, click, "
         "text); with a colour argument the window is one colour (this is how " + c("check-multiuser.py") + " tells users apart)"],
        [c("test-window.py"), "the same idea, used by " + c("base-check.py") + " and " + c("avlib.py")],
        [c("lifecycle-window.py"), "a variant that adds the window size to every event; no caller was found in " + c("prove/")],
        [c("window-input.py"), "logs EVERY event the application receives: button presses with their repeat count, wheel, every key "
         "with its modifiers, selection, focus, size. A button <b>release</b> is not taken from the click gesture but from the raw events (a " + c("Gtk.EventControllerLegacy")
         + " in the capture phase), and carries no repeat count. The reason is GTK 4.22, the version of Ubuntu 26.04: a text entry that claims the sequence (to select by dragging) "
         "denies it to the gestures of the window around it, and the gesture then never emits «released»; GTK 4.18 did not do that (register of problems, B3-bis). Modes " + c("input") + " (fullscreen) and " + c("edge")
         + " (a 640x440 decorated window whose edges can be grabbed)"],
        [c("geom-window.py"), "geometry windows: four coloured quadrants, a 6 px frame and a cross (" + c("frame")
         + "), or a 1800x1000 cyan window with a red border (" + c("scene") + "); flat rectangles at integer pixels, so the "
         "browser's picture can be compared pixel by pixel"],
        [c("media-window.py"), "media windows: a binary-coded counter (" + c("count") + ", " + c("bursts") + "), a moving bar with "
         "a flash and a beep every second (" + c("video") + "), a sharpness pattern (" + c("pattern") + ")"],
        "Shell",
        [c("all.sh"), "every check on ONE box, in sequence, one log per check and a final table"],
        [c("fresh.sh"), "a fresh box with the package installed and the service enabled; with " + c("RX_BANCO=vm") + " it hands over to " + c("banco-vm/fresh-vm.sh")],
        [c("matrix.sh"), "every desktop on a fresh box: Chrome (new session) then Firefox (resumed); it calls " + c("fresh.sh") + " and so belongs to the container way"],
        [c("prelocal.sh"), "the real local login on gdm3, sddm and lightdm in a VM (" + rif("The tools of the 1.2.0 work") + ")"],
        [c("hold.py") + ", " + c("hold-user.py"), "helpers that log in from the browser and keep the remote session open for a number of seconds while the machine is looked at from outside (" + rif("The tools of the 1.2.0 work") + ")"],
        [c("headless-wayland.sh"), "start or stop a headless labwc (used by " + c("base-check.py") + " and " + c("avlib.py") + ")"],
        [c("headless-multi.sh"), "the same, but the pid written is labwc's own so that stop really stops it; no caller was found "
         "in " + c("prove/")],
        "The VM bench (prove/banco-vm/)",
        [c("banco-vm/box.sh"), "the same face as " + c("boxes/box.sh") + " for a virtual machine: verbs " + c("ssh") + ", " + c("rootkey") + ", " + c("install") + ", " + c("status") + ", and " + c("reset") + ", which refuses ("
         + rif("The VM bench") + ")"],
        [c("banco-vm/fresh-vm.sh"), "the «fresh box» for a VM that stays on: stops the service, removes the test users and the checks' own drop-ins, keeps the ban file under another name, "
         "installs the missing tools, starts the service again"],
        [c("banco-vm/autologin-gdm3.sh") + ", " + c("autologin-lightdm.sh") + ", " + c("autologin-sddm.sh"), "switch the automatic login of gdm3 (Ubuntu), lightdm (Xubuntu) and sddm (Kubuntu, Lubuntu) on and off in a machine, for the tests of the real local login; test-bench files, never installed by the package"],
    ], "«TAB» — The files of prove/") + \
    p("The folders " + c("shots/") + " (pictures), " + c("work/") + " and " + c("log/") + " are made by the checks and are not "
      "in git; the logs quoted in this manual are on the dev server, in " + sysf("/media/REMOTIX-UBUNTU/albero/prove/log/") + " (one folder per round, named by its tag).")

# ── 17.3 ─────────────────────────────────────────────────────────────────────
S3 = p("All checks take " + c("--box xfce|lxqt|gnome|kde") + " (REMOTIX ports 8841 to 8844 on the virtual machines, see " + rif("The VM bench")
       + "). The limits are the seconds given to each " + c("run") + " call in " + c("all.sh") + "; the verdict names are the "
       + c("NAMES") + " tuples of each file. The list is that of the tree when this chapter was written (20 Nov 2026): "
       + c("check-desktop.py") + " was being edited at that moment, and the two last names of its tuple, " + c("power-implied") + " and " + c("power-local-seat") + ", are of 20 Nov 2026.", lead=True) + \
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
         + c("settings-intact") + ", " + c("canvas-limits") + ", " + c("reattach-windows-inside") + ", " + c("session-cap") + ", "
         + c("power-implied") + ", " + c("power-local-seat"),
         "power actions: logind answers no to every " + c("Can*") + " as the user, polkit refuses the 15 login1 actions that this check asks about, real " + c("systemctl poweroff") + " and the like are refused and the box stays up; "
         "no polkit password window and no keyring prompt; the shell and environment of a local login; the user's own settings intact after use and Log Out (file "
         "writes watched with fanotify); canvases from 200x150 to 5120x2880; a window "
         "born in a large canvas is inside after a reattach; with " + c("--session-cap 2") + " the third user is refused. The last two names are described below"],
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
         + c("page-shortcuts-declared") + ", " + c("page-cad-hidden") + ", " + c("page-cad-chain") + "), "
         + c("page-keyboard-lock") + " (Chrome), two Firefox clipboard lines, " + c("page-ctrl-alt-end-passes") + " last",
         "buttons, double click, wheel, drag, exact coordinates, cursor shape, edge drag, no double cursor; text, Ctrl chords, "
         "Shift+arrows, Alt+Tab, Super, function keys, key repeat, accents, AltGr characters, keys that cannot be produced, Caps "
         "Lock; the page's declared shortcuts. " + c("page-cad-hidden") + ": outside diagnostics the page shows no Ctrl+Alt+Del or Ctrl+Alt+End button and no control that opens one "
         "(BLOCKED if no session is on or if the diagnostics are on); " + c("page-cad-chain") + ": the button that diagnostics keep sends the three keys; "
         + c("page-ctrl-alt-end-passes") + ": Ctrl+Alt+End typed on the client keyboard reaches the desktop untouched, with no question and the session still on (PASS only if the "
         "application receives " + c("Control_L") + ", " + c("Alt_L") + ", " + c("End") + " with ctrl and alt held on End; DECISIONS-11 §11.54)"],
        [c("check-phone.py") + " (1250 s)", "19 names, " + c("login-desktop") + " to " + c("reattach-portrait"),
         "the page used as a phone, by emulation: portrait and landscape geometry, tap, drag, two- and three-finger taps, "
         "on-screen keyboard open, text, enter, delete and close, tap-and-half-drag selection, two-finger scroll, pinch zoom, "
         "rotation"],
        [c("check-prelocal.py") + " (1200 s by default, 3900 s with all nine cases)",
         c("P1-hook-closes-desktop") + ", " + c("P2-new-desktop-after") + ", " + c("P3-hook-ignores") + ", " + c("P4-no-desktop")
         + ", " + c("P5-service-stopped") + ", " + c("P6-pam-line-order"),
         "the local-login hold (" + rif("The local-login hold") + "), with Chrome and the check's own users " + c("pl1") + " and " + c("pl2")
         + ". P1: with a remote desktop open the hook returns 0 within 15 s and afterwards nothing of the user is left (no logind "
         "session of the service, no program, no unit of the desktop in the user manager), the page was told with 0x04 and the "
         "journal has the request and the root side's answer. P2: 12 s later (births are refused for 10 s) a new remote login of "
         "the same user gets a working desktop. P3: five calls that are not a local graphical login (no seat, close_session, "
         "greeter, tty, service remotix) each return 0 in under 1 s and the desktop is still alive. P4: a user with no remote "
         "desktop: the hook returns 0 in under 2 s. P5: with the service stopped the hook returns 0 in under 2 s (the service is "
         "started again at the end). P6: " + sysf("/etc/pam.d/common-session") + " has the " + c("pam_exec") + " line of the hook after the "
         + c("pam_systemd") + " line. <b>P7, P8 and P9</b> (only with " + c("RX_LOCALE_VERO=1") + "; " + rif("The tools of the 1.2.0 work") + "): a REAL local login (the display manager's automatic login, restarted in the machine) of the same user while the remote desktop holds a running terminal (P7), an editor with unsaved text (P8: Kubuntu and Xubuntu; BLOCKED on GNOME and LXQt) or the snap Firefox (P9). "
         "The local desktop must arrive and nothing of the remote one may be left (no process, no unit, no REMOTIX session, no snap scope, no new crash of the user's)"],
        [c("check-apparmor.py") + " (180 s, after ban)", c("profile-coverage"),
         "the kernel journal of the machine (and the audit log if there is one), from the start of the round, holds no line " + c("apparmor=\"DENIED\"") + " or " + c("apparmor=\"ALLOWED\"") + " of the profile " + c("remotix_network") + " or its children. "
         "The package installs the profile in complain mode, so what it does not cover shows as ALLOWED; in enforce mode it would be DENIED: both are a FAIL. Other programs' profiles (snap) are not looked at. If the log cannot be read: BLOCKED, never PASS"],
        [c("check-ban.py") + " (900 s, always last)",
         c("wrong-password") + ", " + c("same-answer") + ", " + c("typed-names-not-logged") + ", " + c("ban-after-limit")
         + ", " + c("ban-survives-restart") + ", " + c("unblock") + ", " + c("unblock-shipped") + ", " + c("cleanup"),
         "a wrong password is refused with one sentence and not before the 2.5 s floor (" + c("REJECT_FLOOR") + " in "
         + c("rcp.c") + "); a non-existent user gets the same sentence and time; no typed name in the log before the verdict; 5 "
         "wrong passwords ban the user and the address ban follows the code's limit (" + c("LIMIT") + " in " + c("rcp.c")
         + " is 5, 20 and 30); the ban survives a restart; the package ships no administrator unblock (by decision); at the end the check always unblocks and "
         "logs a user in normally (" + c("cleanup") + ", reported on its own line)"],
    ], "«TAB» — The checks run by all.sh, in the order all.sh runs them") + \
    p("In the tree the tuples give, per desktop and with the default " + c("all.sh") + " (prelocal P1 to P6), 126 verdict rows: base 5 and 5, lifecycle 4, multiuser 3, desktop 9, media 4, resilience 5, audio 1 and 1, clipboard 2, "
      "input 26 with Chrome and 27 with Firefox, phone 19, prelocal 6, ban 8 (the seven names and " + c("cleanup") + "), apparmor 1. The rounds of 1.2.0 on the four machines are in " + rif("What was verified on Ubuntu 26.04, and what was not") + ".") + \
    h4("The two checks added on 20 November 2026") + \
    p(c("power-implied") + " needs no session and no Python in the box. It reads the installed rule " + sysf("50-remotix-no-poweroff.rules") + " and <b>every</b> polkit policy file of the machine, builds the implications "
      "(the annotation " + c("org.freedesktop.policykit.imply") + ", followed along chains) and fails if an action that the rule does not forbid implies one that it forbids: polkit would then grant the forbidden action without "
      "consulting the rule. " + c("power-local-seat") + " runs from root with no REMOTIX session and asks " + c("pkcheck") + ", as the process of the greeter (the active session on seat0, that is the person at the machine), "
      "about <b>every</b> forbidden action: all must be refused. It is calibrated against " + c("login1.chvt") + ", which must be granted; with no greeter (a container) it is BLOCKED. "
      "They exist because " + c("power-entries-absent") + " looked only from the remote session, which is not at a seat, and only at the 15 actions known by name (register of problems, C6: the four " + c("set-reboot-*") + " actions imply " + c("reboot") + ").") + \
    p("Both were run on the Ubuntu GNOME virtual machine on 20 Nov 2026, first with the rule of 15 actions of the package <b>unione10</b> (run " + sysf("vm-gnome-poweroff-prima2/") + "): both FAILED, as the register describes. " + c("power-implied") + " named the four actions, "
      + c("set-reboot-parameter") + ", " + c("set-reboot-to-boot-loader-entry") + ", " + c("set-reboot-to-boot-loader-menu") + " and " + c("set-reboot-to-firmware-setup") + ", each implying " + c("login1.reboot")
      + "; " + c("power-local-seat") + " said «from the seat's active session c1 (leader 1846) polkit GRANTS: reboot». The same run had " + c("power-entries-absent") + " PASS with «polkit refuses 15/15 power actions». "
      "Then with the rule of 19 actions (package <b>unione11</b>; run " + sysf("vm-gnome-poweroff-dopo/") + "): " + c("power-implied") + " PASS («19 forbidden actions … 51 policy files read; no action left alone implies a forbidden one») and " + c("power-local-seat")
      + " PASS («from the active session of seat0 (c1, process 1846) all 19 forbidden actions are refused; calibration: chvt granted»). Limit: that run is a <b>partial</b> round of the desktop check alone (its " + c("summary.txt") + " says «PARTIAL RUN, only: desktop»: 8 PASS and 1 FAIL, the known " + c("users-shell-and-environment") + "); "
      "the complete round of 120/2/1/3 belongs to unione10 and was not repeated on unione11.") + \
    h4("Things to know before reading a log") + \
    ul([
        c("check-ban.py") + " is the only check that types wrong passwords, and it bans the address the browser comes from on "
        "that box: " + c("127.0.0.1") + " on the containers, " + c("10.0.2.2") + " on the VM bench (QEMU's user network shows every client as that address), or the value of " + c("RX_BAN_ADDR")
        + ". To unblock it uses a drop-in with " + c("--command-socket") + " (a bench option of the binary that the packaged "
        "unit never passes; the check adds it through " + c("REMOTIX_OPTIONS") + " in " + sysf("/etc/remotix/remotix.conf.d/") + ") and at the end it ALWAYS unblocks, removes the drop-in, restarts the service and logs a user in normally "
        "(" + c("cleanup") + "). If the cleanup did not run, the check prints a NOTE that says what to undo by hand (on a VM: " + c("all.sh <de> --clean") + " or " + c("banco-vm/fresh-vm.sh") + "). Run it last and alone on a box.",
        c("check-prelocal.py") + " <b>simulates</b> the local login: the boxes have no display manager running, so the hook is run as root "
        "inside the box by hand, with the environment " + c("pam_exec") + " would give it (" + c("PAM_TYPE=open_session") + ", "
        + c("XDG_SEAT=seat0") + ", class " + c("user") + ", type " + c("wayland") + "), and no local session is registered in logind. It "
        "proves the hook and the root side's answer; it does not prove the interplay with the periodic sweeps, which only a real local "
        "login exercises (" + rif("Appendix C — Known issues and open points") + "). P1 to P6 are the same on the VMs, which do have a real display manager: " + c("all.sh") + " calls the hook by hand there. The real local login is P7 to P9 (the automatic login of the display manager, restarted in the machine), which " + c("all.sh") + " runs only with " + c("RX_LOCALE_VERO=1") + " and otherwise lists as a SKIP row, "
        + c("prelocal/real-login") + ". The owner decided on 26 Nov 2026 that these cases are allowed on the Ubuntu bench with the Radeon passed through (the freezes of the server on Debian came from the old drivers of the Debian machines).",
        c("check-phone.py") + " is an emulation, not a phone: Chrome with DevTools device emulation (412x915 CSS px, device scale 2, "
        "touch events with pointer type touch, a mobile user agent, Italian language). What it cannot prove is listed in "
        + rif("What only a real machine or a real phone can prove") + ".",
        c("check-input.py") + " states its limits in its header: DevTools and WebDriver cannot press AltGr, so the Italian AltGr "
        "characters are sent as the character itself, which exercises the page's LETTER path; the browser's pointer lock and the "
        "operating system's own cursor are in no screenshot, so the cursor is judged by the CSS rule on the canvas.",
        c("check-desktop.py") + " on Ubuntu 26.04: the GNOME terminal is " + c("ptyxis") + " (not " + c("gnome-terminal") + "); " + c("sudo") + " is sudo-rs, so a refusal is recognised also by «I'm afraid I can't do that» and "
        "«interactive authentication is required»; " + c("VOLATILE") + " (the files that the desktop itself writes and that " + c("settings-intact") + " does not count) now includes " + sysf(".config/dconf/remotix") + ", "
        "the file that REMOTIX makes by design. " + c("session-cap") + " needs a quiet box.",
        c("canvas-limits") + " waits for the test window to say " + c("ready") + " (up to 150 s; up to about 78 s was measured), waits for a picture that has stopped moving (" + c("still_png()") + "), tries once more "
        "a picture that never stood still, and ignores a few stray pixels near the colour when it measures the window (the sky-blue launcher icon of KDE). The canvas it expects is the one of SPECS §6.1 "
        "(client area rounded down to 16, 320x240 to 4096x2304) <b>limited by the maximum that the page itself declares</b> (" + c("video.max_size MEASURED") + " in the page's log, read by " + c("page_max_size()")
        + "); the page declares at most 3840x2160 (the last rung of " + c("MEASURE_PROBES") + " in " + c("page.html") + "), and the evidence line says so: the server's bound of 4096x2304 cannot be exercised with this page. "
        "The <b>declared</b> limit of the product is 3K (owner's decision, " + c("DECISIONS-11") + " §11.51, confirmed 18 Nov 2026); the sizes above are technical bounds.",
        "The check docstrings can lag behind the code: the docstring of " + c("check-ban.py") + " still describes " + c("unblock-shipped") + " as «the PACKAGE gives the administrator a way to unblock», "
        "while the code passes it when the package ships none. The code is the reference.",
    ])

# ── 17.4 ─────────────────────────────────────────────────────────────────────
S4 = p("A run is one command per desktop, started on the dev server in " + c("prove/") + ". On the VM bench the machines run one at a time, because the Radeon is handed to one of them. "
       "On the older container boxes the four desktops could run at the same time: the runs share nothing (own compositor, browser profile and ports; each box has its own users and files).",
       lead=True) + \
    term("""$ cd /media/REMOTIX-UBUNTU/albero/prove
$ /media/REMOTIX-UBUNTU/albero/prove/all.sh xfce                    # older container box: the package already installed in it
$ /media/REMOTIX-UBUNTU/albero/prove/all.sh gnome --fresh /path/to/remotix_1.2.0-1+ubuntu26.04_amd64.deb     # container way
$ TAG=myround /media/REMOTIX-UBUNTU/albero/prove/all.sh kde         # logs in log/myround/ instead of log/kde-<date>-<time>/
$ RX_BANCO=vm /media/REMOTIX-UBUNTU/albero/prove/all.sh gnome --fresh <deb>   # the VM bench: the machine 'ubuntu', clean state, then the package
$ RX_BANCO=vm /media/REMOTIX-UBUNTU/albero/prove/all.sh gnome --clean         # VM bench: clean state, the installed package stays
$ RX_BANCO=vm /media/REMOTIX-UBUNTU/albero/prove/all.sh gnome --only ban,audio-firefox   # a partial round
$ RX_LOCALE_VERO=1 RX_BANCO=vm /media/REMOTIX-UBUNTU/albero/prove/all.sh gnome --clean   # also P7, P8, P9 (the real local login)""",
         "Running all.sh") + \
    ul([
        c("--fresh <deb>") + " first runs " + c("fresh.sh") + " (container: reset the box, install the package, enable and start the service, "
        "check it is active; VM: the clean state of " + c("fresh-vm.sh") + ", then the package); if that fails the run stops and every row is BLOCKED. "
        + c("--clean") + " exists only with " + c("RX_BANCO=vm") + ": the same clean-up with no package. <b>Without</b> " + c("--fresh") + " or " + c("--clean") + " nothing is cleaned, on a VM as on a container.",
        c("--only label,label") + " runs a subset. The labels are " + c("base-chrome") + " " + c("base-firefox") + " " + c("lifecycle") + " " + c("multiuser") + " " + c("desktop") + " " + c("media") + " "
        + c("resilience") + " " + c("audio-chrome") + " " + c("audio-firefox") + " " + c("clipboard") + " " + c("input-chrome") + " " + c("input-firefox") + " " + c("phone") + " " + c("prelocal") + " " + c("ban") + " " + c("apparmor") + " " + c("package")
        + "; an unknown label is refused with the list. " + c("package") + " is a valid label but runs nothing: " + c("check-package.py") + " is not part of " + c("all.sh") + " (on a VM it is a SKIP row).",
        "The output of each check goes to " + c("log/<tag>/<check>.out") + ", ending with an " + c("exit=<n>") + " line. Each "
        "verdict line becomes one table row " + c("<check>/<name>") + "; a check that printed no verdict line is BLOCKED (\"no "
        "verdict\"), and one that hit its time limit is BLOCKED (\"no answer\").",
        "After the last check " + c("lib.sweep()") + " ends the sessions of the test users; a session left over is a BLOCKED row.",
        "The table is printed and saved as " + c("log/<tag>/summary.txt") + ". Besides the check rows it can hold " + c("NOTE") + " rows (the bench key was installed in the VM; the Welcome Center of KDE was hidden in "
        + sysf("/etc/skel") + " by the bench) and " + c("SKIP (reason)") + " rows (never a PASS, never a failure). The last lines are " + c("lines of the checks: N PASS, N FAIL, N BLOCKED/other, N SKIP, N NOTE") + " and one of: "
        + c("ALL PASS") + ", " + c("ALL PASS (n SKIP with the reason in the table, none of them a PASS)") + ", " + c("ALL PASS OF A PARTIAL RUN (only: …): not a full run") + ", " + c("NO CHECK PRODUCED A PASS: nothing proven (not ALL green)")
        + ", or «N line(s) not PASS».",
        "<b>Exit status.</b> 0: a full run, every line PASS. 1: anything else, including an aborted run and a failed clean-up or initial control. 2: a wrong call (usage, unknown label, a bad " + c("RX_TEMPO") + "). "
        "3: every line PASS but the run was partial (" + c("--only") + "): a caller that tests «= 0» cannot take it for a full green.",
        "SIGTERM, SIGINT and SIGHUP stop the running check and mark the remaining ones BLOCKED (aborted).",
        "The limits of the " + c("run") + " calls add up to 17,860 s (about 4 h 58 min). That is a ceiling, not a measured "
        "duration; with " + c("RX_TEMPO=2") + " it is 35,720 s. The only measured whole round on record is the one of the release package on the GNOME virtual machine: 47 min (docs/STORIA-ubuntu-26.04.md).",
    ]) + \
    table(["Command", "Use"], [
        [c("prove/fresh.sh <de>"), "a fresh box with the newest " + c("remotix_*.deb") + " under "
         + sysf("/media/REMOTIX-UBUNTU/pacchetti") + " (also under a " + c("fix*") + " sub-folder), or the file in " + c("DEB=")],
        [c("prove/matrix.sh [tag]"), "for each desktop: a fresh container box, then " + c("base-check.py") + " with Chrome and with Firefox"],
        [c("python3 prove/check-package.py --box <de> --deb <file>"), "the package check (next section)"],
        [c("python3 prove/check-<name>.py --box <de>"), "one check alone; several take " + c("--only a,b") + " to run some names"],
    ], "«TAB» — Running pieces of the suite") + \
    note(c("fresh.sh") + " looks for " + c("box.sh") + " in " + sysf("prove/boxes/") + " and, if that folder is not there, in the top-level " + c("boxes/") + ": it works from a plain checkout. "
         + c("lib.py") + " does the same with its " + c("BOXES") + " variable. The warning that the Debian manual carried about a layout difference does not apply to " + c("fresh.sh") + " in this tree; "
         + c("matrix.sh") + " has no mention of " + c("boxes") + " and calls " + c("fresh.sh") + ", so it follows.", "No layout difference.")

# ── 17.5 ─────────────────────────────────────────────────────────────────────
S5 = p(c("check-package.py") + " tests the .deb itself on a box that it may reset freely. It is not in " + c("all.sh") + ": it "
       "resets the box at the start (and again for the refusal check) and at the end leaves it fresh, with the package installed "
       "and the service enabled (" + c("fresh.sh") + "), so it must not run on a box somebody else is testing. A VM cannot be reset by the bench "
       "(" + c("banco-vm/box.sh") + " refuses " + c("reset") + "), so the check never runs on the VM bench.", lead=True) + \
    table(["Verdict name", "What it proves"], [
        [c("install"), "apt install on a fresh box: the expected files only (a snapshot diff from " + c("package-snap.py")
         + "), service installed but NOT enabled and NOT running, system user remotix with nologin shell, nothing listening on 7447; "
         "the hook " + c("remotix-local-login") + " and the profile " + sysf("/usr/share/pam-configs/remotix") + " are there and "
         + c("pam-auth-update") + " has put the " + c("pam_exec") + " line into " + sysf("/etc/pam.d/common-session")],
        [c("first-start"), "after enable --now: active, TCP and UDP listening, certificates and secrets with safe modes, no error "
         "in the journal, and the two processes as designed (root side as root; network side as remotix with an empty "
         + c("CapEff") + ", " + c("NoNewPrivs") + " and seccomp on)"],
        [c("apparmor"), "that the network side's profile is loaded <b>and enforcing</b>; BLOCKED if the box has no AppArmor interface. In "
         "the containers it is BLOCKED (securityfs is not mounted); what it can tell is that the profile text compiles with "
         + c("apparmor_parser -Q") + " and that the shipped profile has flags " + c("complain") + ". On a machine with AppArmor this check would FAIL as long as the profile ships in complain mode, "
         "by its own wording (" + c("profile loaded but not enforcing") + ")"],
        [c("remove"), "a test user logged in, then apt remove with the session alive: sessions closed, desktop processes gone, "
         "group enrolments undone, /dev/dri grants taken back, the " + c("pam_exec") + " line gone from " + c("common-session")
         + ", service stopped, binary gone, configuration and /var/lib/remotix "
         "kept, no process left, nothing else touched"],
        [c("purge"), "apt purge: everything the package or the program made is gone; the box is as before the install except for "
         "the dependencies apt pulled in"],
        [c("reinstall"), "an install after the purge, and a base login (page, login, desktop)"],
        [c("preinst"), "a PERSON account called remotix (uid at least 1000, a login shell, a home): the install is refused with "
         "the preinst message and the box stays clean"],
        [c("recommends"), "informative: what the install pulled in as Recommends and its size; the list it knows is " + c("labwc") + ", " + c("wlr-randr") + ", " + c("xwayland") + ", " + c("va-driver-all") + ", "
         + c("mesa-vulkan-drivers") + ", " + c("dconf-cli") + ", " + c("fonts-dejavu-core")],
        [c("fresh-end"), "the box is left fresh, with the package installed and the service enabled"],
    ], "«TAB» — The verdict names of check-package.py") + \
    warn("The check was last aligned with the file list of Debian. Its " + c("install") + " step lists as expected only " + sysf("/var/lib/remotix") + ", " + sysf("/run/remotix") + " and "
         + sysf("/etc/apparmor.d/local/remotix_network") + " among the paths that no package owns; the system dconf database " + sysf("/etc/dconf/db/remotix") + ", which the " + c("postinst") + " makes and which has " + c("remotix")
         + " in its name, is owned by no package, so by the reading of " + c("c_install()") + " the step would report it as an unexpected file wherever " + c("dconf-cli") + " is installed (it is a Recommends, so almost everywhere). "
         "This is a reading of the code: the check was <b>not run</b> on Ubuntu 26.04 and the manual does not claim it passes or fails. It is for the coordinator to decide whether to add the path to the check.",
         "Not aligned with the new postinst.") + \
    p("What the package contains and how its scripts behave is in " + rif("The package") + ".")

# ── 17.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The container boxes are four systemd containers, one per desktop, built from one " + c("boxes/Containerfile") + " with "
       + c("--build-arg DESKTOP=gnome|kde|xfce|lxqt") + ". There is NOTHING of REMOTIX inside the image: the package is installed "
       "later with apt, so the box is what a user's machine looks like before the install. <b>This is not the bench of the release</b>: it is the bench of the rounds of 18 and 19 Nov 2026 "
       "and of the first hand tests, and it is still in the tree. On the owner's order of 19 Nov 2026 the four containers and their images were deleted from the dev server, and the bench of the "
       "release is the VM bench (" + rif("The VM bench") + "); the package is no longer built in a container either (" + rif("Build and release") + "). The boxes can be rebuilt with " + c("boxes/box.sh build") + "; " + c("server/prepara-server.sh") + " prepares the server for them.", lead=True) + \
    table(["Box", "Container", "Image", "ssh port", "REMOTIX port (TCP + UDP)", "Desktop package", "Display manager"], [
        ["gnome", c("rxu-gnome"), c("rxu/gnome:latest"), "2221", "8821", c("ubuntu-desktop-minimal"), c("gdm3")],
        ["kde", c("rxu-kde"), c("rxu/kde:latest"), "2222", "8822", c("kubuntu-desktop"), c("sddm")],
        ["xfce", c("rxu-xfce"), c("rxu/xfce:latest"), "2223", "8823", c("xubuntu-desktop"), c("lightdm")],
        ["lxqt", c("rxu-lxqt"), c("rxu/lxqt:latest"), "2224", "8824", c("lubuntu-desktop"), c("sddm")],
    ], "«TAB» — The four test boxes (ports from boxes/box.sh, packages from boxes/Containerfile)") + \
    p(c("boxes/box.sh") + " is the only entry point. Verbs: " + c("build") + " (image; it generates the ssh key " + c("box-key")
      + ", which is not in git), " + c("boot") + ", " + c("shutdown") + ", " + c("status") + ", " + c("ssh") + " (a command as root "
      "inside, over ssh on 127.0.0.1), " + c("install") + " (copy the .deb in, refresh the package lists as on a real machine, "
      "run " + c("apt-get install -y --reinstall") + " so that a package of the same version replaces the files too, then write " + c("REMOTIX_PORT=<port>") + " into " + sysf("/etc/remotix/remotix.conf.d/10-box-port.conf")
      + " because the default 7447 would clash between boxes), and " + c("reset") + " (throw the container away and boot a "
      "fresh one from the image). The service is left as the package leaves it: disabled and not started; "
      + c("fresh.sh") + " enables it.") + \
    h4("How a box is built and started") + \
    ul([
        "<b>The desktop as an Ubuntu user installs it.</b> The metapackage of the flavour with its Recommends: " + c("ubuntu-desktop-minimal") + ", " + c("kubuntu-desktop") + ", " + c("xubuntu-desktop") + " or " + c("lubuntu-desktop")
        + ", after the display manager of that desktop has been stated to debconf. " + c("boxes/set-dm.sh") + " then registers the manager as its "
        "postinst would on a real machine (a container build does not do it): " + sysf("/etc/X11/default-display-manager") + " and the enabled "
        "unit with its " + c("display-manager.service") + " alias. It fails if the registration is not there at the end.",
        "<b>No snap, and a desktop that is not GNOME has no GNOME.</b> snapd does not run in a container, so an apt preference at -1 keeps out " + c("firefox") + ", " + c("thunderbird") + " and " + c("chromium-browser")
        + " (on Ubuntu they are wrappers of snaps; the browser of the tests is on the server). For Kubuntu, Xubuntu and Lubuntu a second preference keeps out " + c("gnome-shell") + ", " + c("gdm3") + " and " + c("ubuntu-session")
        + ", because the bare " + c("xubuntu-desktop") + " brings " + c("gdm3") + " as the default manager and a flavour from its ISO has no GNOME (box finding BOX-01, " + c("studio/8-pacchetto-e-prove.md") + "). "
        "The image's own user " + c("ubuntu") + " (uid 1000) is removed, so that " + c("prova") + " and " + c("prova2") + " get uid 1000 and 1001 as on a fresh install; the build fails otherwise.",
        "<b>Identity check.</b> " + c("boxes/box-identity.sh") + " is run during the image build as " + c("box-identity ubuntu 26.04 <de> -")
        + ": an image that is not Ubuntu 26.04 with that desktop, its display manager and its session files is not built.",
        "<b>systemd as init.</b> " + c("--systemd=always") + ", host network (so every box has its own ports), all of " + c("/dev/dri")
        + ", " + c("memlock") + " unlimited (low-memory-monitor on GNOME calls mlockall), the capabilities a real login needs "
        "(" + c("AUDIT_WRITE") + ", " + c("AUDIT_CONTROL") + ", " + c("SYS_ADMIN") + ", " + c("SYS_NICE") + ", " + c("WAKE_ALARM")
        + ") and a pids limit of 16384. " + c("boot") + " waits up to 120 s for systemd to be running and 90 s for ssh.",
        "<b>No display manager runs.</b> " + c("boxes/common.sh") + " sets the default target to " + c("multi-user.target")
        + " (the box has no monitor), configures sshd on 127.0.0.1 and on the box's port, makes the journal persistent (512 MB cap) and installs "
        + c("box-gruppi") + ", which aligns the box's " + c("video") + " and " + c("render") + " groups with the groups of the host's "
        "DRM nodes (in a box they arrive with the host's numbers).",
        "<b>Sleep questions answered as on a real machine.</b> " + c("boxes/power.sh") + " (run at every boot) mounts a tmpfs copy of "
        + sysf("/sys/power") + " and restarts logind: in a container " + sysf("/sys") + " is read-only and logind would answer \"Call failed\" "
        "before asking polkit, so the polkit rule of the package would not be what is tested. The real " + sysf("/sys/power") + " is not "
        "touched. It also removes " + sysf("/etc/systemd/sleep.conf.d/remotix-no-suspend.conf") + " if present and restarts logind each time, "
        "so it must not be run on a machine whose administrator switched that belt on.",
        "<b>Test users.</b> Two ordinary users, " + c("prova") + " and " + c("prova2") + ", with the password of the Containerfile "
        "(no sudo). The checks make their own.",
        "<b>KDE.</b> The Plasma Welcome Center is hidden for new users through " + sysf("/etc/skel") + " so that it does not cover a "
        "first login.",
    ]) + \
    p("The boxes share the host's kernel, network and DRM nodes, which has two known consequences. Xwayland display numbers "
      "and their abstract sockets are shared, and docs/STORIA-ubuntu-26.04.md records 33 X screens in all as a limit when many containers run: this "
      "is why " + c("lib.Compositor") + " runs the test compositor in its own network and mount namespace. And inotify limits are "
      "shared by one uid, so " + c("server/prepara-server.sh") + " raises " + c("fs.inotify.max_user_instances") + " to 8192 and "
      + c("fs.inotify.max_user_watches") + " to 1048576. The podman storage is <b>shared</b> with the Debian work: " + c("prepara-server.sh") + " keeps it under "
      + sysf("/media/REMOTIX-DEBIAN/podman") + " (the variable " + c("PODMAN_BASE") + ") and writes the configuration files only if they are absent.") + \
    note("Some comment headers in " + c("boxes/power.sh") + " and " + c("boxes/box-identity.sh") + " may still describe other "
         "distributions and the old bench scripts (" + sysf("17-box.sh") + ", " + sysf("11-box-power.sh") + "); they were not re-read for this manual, and the code that runs "
         "is the one of the two files.", "Stale comments.")

# ── 17.7 ─────────────────────────────────────────────────────────────────────
S7 = p("A container shares the host's kernel, has no real boot and no real device model. For what only a whole machine shows, "
       + c("server/vm.sh") + " runs a real Ubuntu 26.04 under KVM. It is the first of the two VM scripts of the tree; the second, " + c("server/vm-radeon.sh") + ", is the bench of the release (" + rif("The VM bench") + ").", lead=True) + \
    table(["Item", "Value (from server/vm.sh)"], [
        ["image", c("ubuntu-26.04-server-cloudimg-amd64.img") + " (the Ubuntu cloud image of the server edition), copied to " + c("disk.qcow2") + " and resized to 20 GB at the first start"],
        ["machine", c("qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 4096") + ", no display, serial log in " + c("serial.log")
         + ", default firmware (SeaBIOS), and " + c("-device virtio-vga") + ": the package's " + c("preinst") + " refuses to install without a render node, and the emulated card gives one ("
         + sysf("/dev/dri/renderD128") + "); VA-API encoding does not work on it"],
        ["first-boot setup", "a cloud-init seed ISO built with genisoimage: user " + c("prova") + " (password " + c("prova")
         + ", passwordless sudo), the key " + c("vmkey")],
        ["network", "QEMU user networking; host 127.0.0.1:2301 to guest 22, and TCP and UDP 127.0.0.1:8901 to guest 7447 (REMOTIX)"],
        ["files", "everything lives in the script's own folder: " + sysf("/media/REMOTIX-UBUNTU/vm")],
        ["commands", c("vm.sh start") + ", " + c("stop") + " (poweroff over ssh, then kill after 30 s), " + c("ssh [cmd]") + ", " + c("status")],
    ], "«TAB» — The virtual machine of server/vm.sh") + \
    p(c("server/vm-login-test.py") + " opens the page of the REMOTIX in that VM (127.0.0.1:8901) with the Chrome driver of "
      + c("prove/lib.py") + " (imported, not modified) and logs in as " + c("prova") + ". It touches no box: the " + c("Rig") + "'s box is "
      "replaced by a stub, because " + c("lib.Box") + " would run commands in the test containers. It prints facts and exits 0 if the "
      "login reached a session; " + c("--bad") + " uses a wrong password. Its " + c("sys.path") + " entry names " + sysf("/media/REMOTIX-UBUNTU/prove")
      + ", whereas the corresponding script of the Radeon machines, " + c("server/vm-radeon-login-test.py") + ", names " + sysf("/media/REMOTIX-UBUNTU/albero/prove") + ": which of the two folders holds " + c("lib.py")
      + " on the server was not checked for this manual.") + \
    p("What this machine can and cannot show: it has no real card, so the server says " + c("CANNOT ENCODE VIDEO") + " and no session shows a picture; it has the real boot, the real kernel, the real AppArmor and the real "
      "package scripts. No result of a run on it is recorded in the logs read for this manual; the machine of the first round of the Debian manual (installation, AppArmor, reboot, removal and purge without leftovers) "
      "has no Ubuntu equivalent in the records.")

# ── 17.7B The VM bench ───────────────────────────────────────────────────────
S7B = p("The container boxes could not show what a real Ubuntu does: the profile of AppArmor is not in force in a container, no snap runs there, and a display manager does not run. "
        "The first real machine (a live Ubuntu 26.04.1, 19 Nov 2026) found two defects in an afternoon, C4 and C5, that the container rounds had not (" + rif("What was verified on Ubuntu 26.04, and what was not") + "). "
        "The bench that followed is four QEMU virtual machines, one per flavour, installed from the desktop image of the flavour and handed the server's Radeon card by passthrough, with the checks of " + c("prove/")
        + " adapted to run against them, and a fifth machine that only builds the package (" + rif("The build of the .deb on the build VM") + "). It is the bench of the release. There are no containers on it: tests and studies run on virtual machines only. The scripts are " + c("server/vm-radeon.sh") + ", " + c("server/prepara-server-vm.sh") + " and "
        + c("prove/banco-vm/") + "; " + c("server/VM-BANCO.md") + " is the note that goes with them.", lead=True) + \
    h4("The four machines") + \
    table(["Machine (check key)", "ISO", "How the disk was made", "ssh / REMOTIX ports with the Radeon", "Display manager"], [
        [c("ubuntu") + " (" + c("gnome") + ")", c("ubuntu-26.04.1-desktop-amd64.iso"), "unattended installation, " + c("autoinstall") + ", with a temporary virtual video card; the VM powers itself off at the end", "2341 / 8841", c("gdm3")],
        [c("kubuntu") + " (" + c("kde") + ")", c("kubuntu-26.04.1-desktop-amd64.iso"), "built from the squashfs of the ISO (" + c("casper/filesystem.squashfs") + ") the way Calamares does", "2342 / 8842", c("sddm")],
        [c("xubuntu") + " (" + c("xfce") + ")", c("xubuntu-26.04.1-desktop-amd64.iso"), "built from the squashfs layers " + c("casper/minimal.squashfs") + " and " + c("casper/minimal.standard.squashfs"), "2343 / 8843", c("lightdm")],
        [c("lubuntu") + " (" + c("lxqt") + ")", c("lubuntu-26.04.1-desktop-amd64.iso"), "built from the same two layers as Xubuntu", "2344 / 8844", c("sddm")],
        [c("costruzione"), c("xubuntu-26.04.1-desktop-amd64.iso"), "built like xubuntu; 8 CPUs, 6 GB, never the Radeon (the script refuses), host name " + c("rx-ub-costruzione"), "2345 / none", c("lightdm")],
    ], "«TAB» — The five VMs of server/vm-radeon.sh (ISO names and ports from the script; display managers from fresh-vm.sh)") + \
    p("Why three disks are not an " + c("autoinstall") + ": Kubuntu and Lubuntu come with Calamares, and the live kernel of Xubuntu crashed the installer (a kernel oops, recorded in docs/STORIA-ubuntu-26.04.md and in the comment of the script). "
      + c("crea") + " then builds the disk by hand: a GPT partition table with a 512 MB EFI partition and an ext4 root, the layers of the ISO unpacked one over the other with " + c("rsync") + ", then a stage run in a chroot "
      "(fstab, hostname, an empty machine-id so that a new one is made at the first boot, the users " + c("prova") + " (with sudo) and " + c("prova2") + ", the installer's own removals, the bootloader packages from the ISO pool, " + c("openssh-server")
      + ", the initramfs, " + c("grub-install --no-nvram") + " so that the server's firmware variables are never touched), and converts the raw image to qcow2. The temporary raw image is the only thing the script deletes, and only after the qcow2 exists. "
      "The four test machines have a 40 GB disk, 12 GB of memory and 8 CPUs with the Radeon (5 GB and 4 CPUs without it; " + c("RX_VM_MEM") + " overrides the memory), " + c("q35") + " with UEFI (OVMF), KVM and the host CPU, no display, a serial console in " + c("serial.log") + ", and user networking with the ports of the table forwarded (ssh, and REMOTIX over TCP and UDP). "
      "The kernel of the Ubuntu machine was 7.0.0-44-generic at the release run.") + \
    h4("server/vm-radeon.sh") + \
    table(["Command", "What it does"], [
        [c("crea <name>"), "makes the disk (above); refuses to touch an existing one"],
        [c("accendi <name>"), "binds the two functions of the Radeon (" + c("0000:03:00.0") + " and its audio function " + c("0000:03:00.1") + ") to " + c("vfio-pci") + " and starts the VM with the Radeon as its only video card, on a PCIe root port, "
         "then waits for ssh (up to 6 min). Refuses if another VM holds the card. The host is started with " + c("intel_iommu=on iommu=pt") + ", " + c("vfio-pci.ids") + " for the two functions and " + c("amdgpu") + " blacklisted (docs/STORIA-ubuntu-26.04.md)"],
        [c("spegni <name>"), "poweroff over ssh, then ACPI power-down, then a declared kill as a last resort; waits until the process is really gone; only then gives the card back (the audio function to " + c("snd_hda_intel") + ", the GPU stays without a driver, as at boot)"],
        [c("ssh <name> [cmd]"), "ssh as " + c("prova") + " with the machine's key"],
        [c("stato <name>"), "running or stopped, which VM holds the Radeon, the driver of the two functions"],
        [c("prova-avvio <name> [--resta]"), "a boot check <b>without</b> the Radeon: virtual card, 5 GB (override " + c("RX_VM_MEM") + "), 4 CPUs, ssh on the port plus 100 (2441 to 2444), no REMOTIX forward; prints the kernel, the display manager, the sessions, " + c("aa-status")
         + ", then powers off; with " + c("--resta") + " it leaves the VM running"],
        [c("schermo <name> <file.png>"), "a screen dump of a machine started with " + c("virtuale") + " (through the QEMU monitor)"],
        [c("tasti <name> <key>…") + ", " + c("scrivi <name> <text>"), "send keys or type text through QEMU's " + c("sendkey") + " (names such as " + c("ret") + ", " + c("tab") + ", " + c("ctrl-alt-f2") + "), for a machine started " + c("virtuale")],
        [c("istantanea <name> <label>"), "a qcow2 snapshot of the disk; the VM must be off; refuses an existing label"],
        [c("ripristina <name> <label>"), "restores a snapshot; the VM must be off. It first saves the <b>current</b> state as a snapshot named " + c("prima-<date>-<time>") + ", then says the current state is replaced by the chosen one (it stays only in that snapshot). "
         "The UEFI variables file is not part of a snapshot"],
    ], "«TAB» — The commands of vm-radeon.sh (the Italian words are the script's own: create, switch on, switch off, state, boot check, screen, keys, type, snapshot, restore)") + \
    p("One lock file serialises the commands: a second call while a VM is being started, stopped or built is refused with «another vm-radeon.sh holds the lock», and the scripts below retry. The Radeon is one, so <b>one VM at a time has it</b>; the four desktops are tried one after the other, "
      "and the change of machine is " + c("spegni") + " of one then " + c("accendi") + " of the other (about 5 s and 18 s, docs/STORIA-ubuntu-26.04.md). While a VM holds the card the containers cannot use it either. The script runs as a user that can use " + c("sudo") + ", because QEMU and vfio need root.") + \
    h4("The server preparation and the kernel parameter that the Radeon machines need") + \
    p("The dev server's root file system is in RAM. After every reboot " + c("prepara-server-vm.sh") + " is run first (no podman, no container): it puts back QEMU, OVMF, the disk tools, the kernel modules " + c("loop") + ", " + c("squashfs") + " and " + c("vfio-pci") + ", an ACL that lets the user open " + c("/dev/kvm") + ", the browsers and tools of the checks, "
      "a sound server for Firefox (PipeWire with a null sink) and the inotify limits, and the server side of the Radeon protection: the kernel log written to disk line by line, " + c("vfio-pci") + " with " + c("disable_idle_d3=1") + " (in " + sysf("/etc/modprobe.d/remotix-vfio.conf") + "; a loaded module with another value is reloaded when nobody uses it, otherwise the step says FAIL) and " + c("power/control=on") + " for the card and the PCI bridges above it. "
      "It prints one OK or FAIL line per step and the values it read back.") + \
    p("<b>The rule.</b> On 26 Nov 2026 the dev server froze four times because the " + c("amdgpu") + " driver in a guest put the passed-through Radeon to sleep (that was on the Debian machines, with kernel 6.12). The rule is now in the script, whoever runs it, and it is kept on the Ubuntu bench too. "
      + c("crea") + " writes " + c("amdgpu.runpm=0") + " on the guest's kernel command line (" + sysf("/etc/default/grub.d/zz-remotix-banco.cfg") + ", named to sort last so that no other " + c("99-*") + " file can undo it) and fails if the parameter is missing at the first boot. " + c("accendi") + " with the Radeon needs a marker, " + c("runpm.ok") + ", written only after the machine, started WITHOUT the Radeon, showed the parameter in " + c("/proc/cmdline") + "; "
      "the marker is good for ONE boot, so every " + c("accendi") + " with the Radeon is preceded by a fresh proof (15 to 30 s more). If the marker is missing the script makes that virtual start itself, applies the parameter if needed, reboots and checks again; with no proof it refuses and the card is not given. There is no option to skip the check. "
      "After the start with the Radeon, " + sysf("/sys/module/amdgpu/parameters/runpm") + " must read 0 and the parameter must be in " + c("/proc/cmdline") + " (read three times); otherwise the machine is switched off at once and the card given back. Only one machine of the whole server may hold the Radeon. "
      "No freeze happened in the sessions of 26 and 27 Nov 2026 (register G1).") + \
    h4("The scripts around it") + \
    table(["Script", "What it does"], [
        [c("prepara-server-vm.sh"), "the server preparation above."],
        [c("banco-vm/autologin-gdm3.sh") + ", " + c("autologin-lightdm.sh") + ", " + c("autologin-sddm.sh"), "switch the automatic login on and off in the machine of that display manager, for the real local login of " + c("prelocal.sh") + " and P7 to P9 (test-bench files, never installed by the package)."],
        [c("vm-radeon-installa.sh <name> <deb> [label]"), "installs a package in one VM <b>as the administrator would</b> (" + c("apt-get install --reinstall") + " of the file, " + c("systemctl enable --now remotix") + "), without the Radeon and without opening a session: "
         "starts the VM with " + c("prova-avvio --resta") + ", copies the .deb, reports the packages apt brought in, the relations of the package, the state of the service, the journal lines about the walls and the dconf, " + c("aa-status")
         + ", the port, " + sysf("/etc/dconf/db/remotix") + ", the version, powers off and takes a snapshot named by the file (" + c("unione<N>") + ", else " + c("installato") + "). It runs apt with " + c("NEEDRESTART_MODE=a") + ". Its output goes to " + sysf("log/vm-radeon-installa-<name>.log") + "."],
        [c("vm-radeon-aggiorna.sh <name>"), "updates a flavour VM the way a user would: " + c("apt full-upgrade") + ", " + c("snap refresh") + ", reboot, the same boot check as " + c("prova-avvio") + ", power off, snapshot " + c("aggiornato") + ". For kubuntu, xubuntu and lubuntu."],
        [c("vm-radeon-controllo.sh <name> [--ripristina <label>]"), "a short control <b>with</b> the Radeon: a timed " + c("accendi") + ", the card, the driver, the render node, the journal lines of the start, the count of " + c("CANNOT ENCODE") + " lines, the display manager and the greeter, "
         "one login as " + c("prova2") + " through " + c("vm-radeon-login-test.py") + " with the picture saved as " + sysf("log/consegna/<name>.png") + ", the sessions left after the browser is closed (the script ends them with " + c("loginctl terminate-user") + " if any remain after 15 s; the exit from the desktop is not tried by this control), the new warnings during the login, a timed " + c("spegni") + " and, with " + c("--ripristina") + ", the restore of a snapshot. The VM is switched off only with " + c("--ripristina") + "; without it the VM stays on."],
        [c("vm-radeon-login-test.py"), "the page of REMOTIX in a VM with the Chrome driver of " + c("lib.py") + ", as " + c("prova") + " or " + c("--user") + "; " + c("--bad") + " for a wrong password; " + c("--png") + " saves the settled picture of the canvas. Exit 0 if the login reached a session."],
        [c("server/live-installa.sh"), "<b>not part of the product</b> (" + rif("Testing the real machine from a live USB") + "): a test installer for a real machine started from an Ubuntu 26.04 live image. Run as root from the live terminal, it downloads the package and its sha256 from another machine on the same network (the variable <code>SORGENTE</code>), checks whether "
         + c("universe") + " is on and, if it is not, turns it on (" + c("add-apt-repository -y universe") + ", else an edit of the apt sources), runs " + c("apt-get install -y --reinstall") + " of the file, makes the users " + c("prova") + " and " + c("prova2") + ", and runs " + c("systemctl enable --now remotix") + ". Apart from turning on " + c("universe") + " when missing and making the two users, it does what the user manual asks of the administrator. Re-runnable."],
    ], "«TAB» — The scripts of the VM bench") + \
    h4("The adapted round") + \
    p("The checks of " + c("prove/") + " do not know they are on a VM except through three things. <b>" + c("RX_BANCO=vm") + "</b> makes " + c("lib.py") + " look for " + c("box.sh") + " in " + c("prove/banco-vm/") + " and use the ports 8841 to 8844. "
      "<b>" + c("RX_TEMPO") + "</b> multiplies every deadline (" + c("all.sh") + " sets it to 2 when " + c("RX_BANCO=vm") + " and nothing else is given). And the " + c("--box") + " names stay " + c("gnome") + ", " + c("kde") + ", " + c("xfce") + ", " + c("lxqt") + ": "
      + c("gnome") + " is the machine " + c("ubuntu") + ", " + c("kde") + " is " + c("kubuntu") + ", " + c("xfce") + " is " + c("xubuntu") + ", " + c("lxqt") + " is " + c("lubuntu") + ".") + \
    ul([
        "<b>" + c("banco-vm/box.sh") + "</b> has the face of " + c("boxes/box.sh") + ". " + c("ssh") + " runs the command <b>as root</b> over ssh with the bench key; it does not use " + c("sudo") + ", because sudo writes every command line, including the secrets typed by a check, into the VM's journal, and "
        + c("check-ban.py") + " then rightly found a typed name in the journal. " + c("rootkey") + " puts the public key of the machine in " + sysf("/root/.ssh/authorized_keys") + " once per VM, through " + c("prova") + " and sudo (the only use of sudo there); it is idempotent and says «bench key installed for root» "
        "when it had to write it. The key stays in the VM. " + c("install") + " copies the .deb in and runs " + c("apt-get install -y --reinstall") + "; there is no " + sysf("10-box-port.conf") + ", the VM keeps 7447 inside and the host forwards 884x. " + c("status") + " lists the four machines. " + c("reset") + " refuses.",
        "<b>" + c("banco-vm/fresh-vm.sh") + "</b> is the clean state of a VM that stays on (a VM cannot be thrown away and recreated by the bench, and " + c("ripristina") + " needs it off). It checks the identity (Ubuntu 26.04 and the display manager of that desktop), stops the service, "
        "ends the sessions of the test users and deletes them with their homes (never " + c("prova") + ", " + c("prova2") + " or any other name), removes the checks' own drop-ins, renames a non-empty ban file to " + c("ban.fresh-<time>") + " (kept, not deleted), installs with apt the tools the container image had if they are missing "
        "(after simulating: if it would upgrade or remove a package already there, nothing is installed and it is a FAIL, for the owner to decide), hides the Welcome Center in " + sysf("/etc/skel") + " on KDE, and starts the service again. It <b>checks its own work</b>: a test user, a process of theirs or the service still there is a FAIL. "
        "It is not equivalent to a container reset: the rest of the disk stays as it was (files in " + sysf("/tmp") + " and " + sysf("/var") + ", the journal, snap state, anything an earlier run left outside the list).",
        "<b>The initial control of " + c("all.sh") + " on a VM.</b> After the bench key is in place, " + c("all.sh") + " sends 300,000 random bytes through " + c("box.sh ssh <de> md5sum") + " and compares the checksum with the local one: the checks send data on stdin to commands in the VM, and it must arrive intact. "
        "If it does not, the run does not start (a line " + c("FAIL the VM of <de>: stdin through the root ssh is not intact") + ", exit 1). A first form of this control, over " + c("sudo -S") + ", stopped the first launches («stdin through sudo -S is not intact», the log " + sysf("vm-gnome-unione8b/summary.txt") + " holds only that line); "
        "it was then rewritten for root.",
        "<b>SKIP rows.</b> Three things are listed on a VM, never counted as PASS and never as a failure: " + c("prelocal/real-login") + " (P7, P8, P9, the real local login with programs open: only with " + c("RX_LOCALE_VERO=1") + "), "
        + c("ban/other-addresses") + " (every client reaches the VM as " + c("10.0.2.2") + ", so only that address is banned; the " + c("127.0.0.1") + " case of the containers does not exist) and " + c("package") + " (" + c("check-package.py") + " needs a reset a VM cannot do).",
        "<b>NOTE rows.</b> The bench key was installed for root; the Welcome Center of KDE was hidden in " + sysf("/etc/skel") + " (it stays for users made by hand too).",
    ]) + \
    h4("The round of the release package of 19 Nov 2026 on the GNOME machine") + \
    p("The round " + c("vm-gnome-unione10") + " (tag of the log folder; the package of the release at that moment, still numbered 1.0.0) ran on the " + c("ubuntu") + " machine with the Radeon, 47 min. Result: <b>120 PASS, 2 FAIL, 1 BLOCKED, 3 SKIP</b> (123 verdict rows, 0 NOTE). This complete round is of the package <b>unione10</b> (polkit rule of 15 actions); the package with the rule of 19 actions, <b>unione11</b>, has the same build checks but had no complete round, only the partial desktop round described above. "
      "The seven checks of " + c("check-desktop.py") + " that existed then were all there; " + c("power-implied") + " and " + c("power-local-seat") + " were not. The three lines that are not PASS:") + \
    ul([
        c("desktop/users-shell-and-environment") + " FAIL: <b>known and accepted</b>. The terminal of GNOME is " + c("ptyxis") + " and in it " + c("SHELL") + " is empty; " + c("pkexec") + " then says «The value for the SHELL variable was not found in the /etc/shells file» and the check, which wants " + c("pkexec")
        + " to make the agent ask for a password, fails. It was identical in the container round of 18 Nov 2026 and is listed in the register of problems (E2).",
        c("ban/typed-names-not-logged") + " FAIL: a <b>false red of the bench</b>. The evidence is the journal of the VM with " + c("sudo") + " lines written by the bench's own commands, among them the grep for the secret that the check had typed. The bench was changed to enter as root with a key (above). "
        "Re-run after the change, " + c("ban") + " gave <b>8 of 8 PASS</b> (log " + sysf("vm-gnome-rootfix/") + ", a partial round with " + c("--only ban,audio-firefox") + ": 9 PASS in all).",
        c("audio-firefox") + " BLOCKED: " + c("ToolError: no answer from Marionette in 45 s") + ". The test Firefox was mute at its first start; the tool could not look, which is BLOCKED and not FAIL. Repeated, it gave PASS, twice (" + sysf("vm-gnome-rootfix/") + " and " + sysf("vm-gnome-rootfix-af2/") + ").",
        "The 3 SKIP rows are the three above.",
    ]) + \
    p("Limits of this record. The round of 19 Nov 2026 was run once, on one machine of the four; after the change of the bench to root, the complete round was not run again, only " + c("ban") + " and " + c("audio-firefox") + " (docs/STORIA-ubuntu-26.04.md says so). The complete rounds of 1.2.0 on all four machines are the next block.") + \
    h4("The rounds of 1.2.0 (26 and 27 November 2026)") + \
    ul([
        "<b>The automatic round</b> (" + c("all.sh") + " with " + c("RX_BANCO=vm") + ", one machine at a time with the Radeon): GNOME 125 PASS and 1 known FAIL (" + c("desktop/users-shell-and-environment") + ", " + c("SHELL") + " empty with " + c("pkexec") + "); KDE, XFCE and LXQt 126 PASS (register G3). The first round of 26 Nov 2026 found three faults of the tools, all corrected in the checks and none in the product: "
        + c("check-resilience.py") + " read as its result a warning of systemd (" + sysf("unit file changed on disk") + ") on " + c("service-restart") + " (XFCE); " + c("unit_residue") + " of " + c("check-prelocal.py") + " counted " + sysf("gnome-keyring-daemon.service") + " as a leftover of the remote desktop although a local login starts it too (Xubuntu); " + c("check-desktop.py") + " read a panel file at the path of Debian (LXQt).",
        "<b>The real local login with programs open</b> (P7 and P9 on all four desktops; P8 on Kubuntu and Xubuntu, BLOCKED by construction on GNOME and LXQt): all PASS. On Kubuntu the editor (" + c("kate") + ") closed gently in 5.03 s and then by force, as designed; on Lubuntu the gentle close took about 0.6 s and the local desktop (" + c("openbox") + ") was there after 4 s. " + c("check-exit.py") + " passed its three cases on XFCE and LXQt, and " + c("check-kde-exit.py") + " on KDE, with the desktop just born included.",
        "<b>Update and removal:</b> the update from the published 1.0.1 to 1.2.0 and the removal (" + c("purge") + ") left the four machines clean.",
        "<b>The owner's hand tests on the four VMs</b> (27 Nov 2026): all OK.",
        "<b>Not explained:</b> one failure of mouse and keyboard (" + c("check-base") + ") on GNOME right after an update with a desktop open, not reproduced; the abnormal ends of " + c("wireplumber") + " on all desktops, of " + c("kwin_wayland") + " once on Kubuntu at the stop of the service and of " + c("xdg-desktop-portal-kde") + " once on Lubuntu (register H3 and H4).",
    ]) + \
    h4("Snapshots") + \
    p("The snapshots are internal qcow2 snapshots of the disk. The names that the records show: " + c("pulito") + " (clean, after the installation of the flavour), " + c("aggiornato") + " (after " + c("vm-radeon-aggiorna.sh") + "), " + c("unione6") + " and " + c("unione10") + " (the machine just after the installation of that build of the package). "
      "The control of 19 Nov 2026 took each machine back to the state «just installed with the release package» before the hand tests. A snapshot does not hold the UEFI variables. For 1.2.0 the machines were handed to the owner clean, to be opened in the browser.") + \
    h4("What was done by hand on real machines") + \
    ul([
        "<b>The four VMs, by the owner, 27 Nov 2026, with the 1.2.0 package:</b> all OK (register G3). <b>The four VMs, by the owner, 19 Nov 2026, with the package of that evening (numbered 1.0.0):</b> GNOME, KDE, XFCE and LXQt all OK, including detach and reattach from Linux and from Android (docs/STORIA-ubuntu-26.04.md). Noted and not blocking: an «internal error» notice of Ubuntu that is " + c("wireplumber") + " stopping at the end of the user's session (seen also after leaving REMOTIX; whether it depends on the VM having no audio card is not known); small stutters in the video seen by Chrome on Android (register E4). "
        "The silence from the telephone on Kubuntu was another program on the tablet that carried the telephone's audio elsewhere, not a defect.",
        "<b>The four live systems, by the owner, 19 Nov 2026:</b> Ubuntu 26.04.1 (kernel 7.0), Kubuntu 26.04.1 (7.0.0-30), Xubuntu 26.04 and Lubuntu 26.04, each started from the live image of a USB stick on the server itself, the package installed with " + c("apt install") + " and " + c("systemctl enable --now remotix")
        + " (the way " + c("live-installa.sh") + " does it). On Ubuntu: the login worked at the first attempt, the line «§5.1 … CONNECTED» was in the log, no " + c("Unknown DConf source") + " in the journal, the installer of the live started in the remote session without error. On Kubuntu: the login worked at the first attempt, the profile was loaded, " + c("labwc")
        + " and " + c("dconf-cli") + " came from apt as Recommends, and the video went through VA-API on the real card (" + c("HEVC: yes via vaapi") + "), where the VMs use the Vulkan road: both encoding roads were exercised, on different benches. On Xubuntu: «everything seems to work» (the owner's words); on Lubuntu: OK. The logs of those two live systems were not read.",
        "<b>«Local excludes remote», by hand, on the live Ubuntu and the live Kubuntu.</b> A local login at the greeter, with the remote desktop open: the login is held in PAM, the client is sent away with 0x04, the remote desktop is closed, and then the local login goes on. On GNOME the remote desktop closed in 851 ms and the runtime dconf profile was removed in the same second; "
        "after the local Log Out a new remote login worked. On KDE the desktop was closed by its own child in 10.9 s (against 0.85 s on GNOME: the closing time of KDE that the register describes in section D). It was not tried at the greeters of Xubuntu and Lubuntu.",
    ]) + \
    note("The server's cards: the live systems and the VMs use the same Radeon, so «a real card» in this chapter always means that one. The VMs encode through the Vulkan road, as the first line of the server's start says " + c("HEVC: yes via vulkan") + "; the live Kubuntu through VA-API. Intel and NVIDIA cards were not tried on Ubuntu 26.04.", "One card.")

# ── 17.7C The tools of the 1.2.0 work ────────────────────────────────────────
S7C = p("The 1.2.0 work added scripts and checks that are <b>not</b> all in " + c("all.sh") + ". Each was written for one question and is run by hand or by a small script.", lead=True) + \
    table(["File", "What it does"], [
        [c("check-exit.py") + " " + c("--box xfce|lxqt"), "three cases with the user " + c("kx1") + " logged in from the browser; after each, within 45 s no process of the desktop (labwc, the session, the panel, Xwayland) and no logind session of REMOTIX may be left: " + c("loginctl terminate-session") + " on the REMOTIX session (the desktop would be an orphan, the sweep of the root side must stop it), " + c("systemctl restart remotix") + " with the desktop open, and a close of the browser followed by 20 s away (the desktop must still be alive, then a new login resumes it)"],
        [c("check-kde-exit.py"), "the same three cases on KDE (labwc, " + c("kwin_wayland") + ", " + c("plasmashell") + ", " + c("ksmserver") + ", " + c("kded6") + ", Xwayland); the state of " + sysf("plasma-kwin_wayland.service") + " is printed for information"],
        [c("prelocal.sh") + " <de> 1|2a|2b|3", "with the real display manager of the machine (gdm3, sddm, lightdm): 1, remote desktop open, local automatic login of " + c("lc1") + ", the remote closes and the local desktop stays; 2a, the same after the remote leader is killed with SIGKILL; 2b, the same after a restart of the service; 3, a local session active and a remote login of the same user refused (\"already signed in locally\"). The login is a test-bench file written by " + c("banco-vm/autologin-*.sh") + ", and the display manager is restarted"],
        [c("hold.py") + " [seconds]", "logs in from the browser (as " + c("lib.Rig") + " does) and stays logged in, writing " + c("/tmp/hold-ready") + " when the desktop has arrived. Variables " + c("RX_USER") + ", " + c("RX_PASS") + ", " + c("RX_BOX") + "; " + c("RX_KEEP=1") + " does not end the user's existing sessions first, to try a remote login while the same user has a local session"],
        [c("hold-user.py"), "like " + c("hold.py") + ", but the user is made by the script with no card groups added: the product's own enrolment at the first connection must do it. " + c("RX_NOEND=1") + " keeps the user's existing manager. With " + c("pkill -9 -u <user> -x remotix") + " and a look at the journal it is the orphan-desktop test"],
        [c("check-apparmor.py"), "also in " + c("all.sh") + " (" + rif("The checks of all.sh and what each proves") + ")"],
    ], "«TAB» — The tools of the 1.2.0 work (the first five are not in all.sh, except P1 to P9 of check-prelocal.py)") + \
    p("Why " + c("check-prelocal.py") + " has P7, P8 and P9: a check that opens an <i>empty</i> remote desktop only ever runs the orderly close, so the forced road, the one that stops a desktop with a program still open, was never asked. "
      "P7, P8 and P9 open a desktop with a terminal running " + c("top") + ", with an editor holding unsaved text and with the snap Firefox, and then make a real local login. Ubuntu has what the other distributions do not: the snap program runs in its own transient scope, so P9 also asks that no " + sysf("snap.firefox.firefox-<uuid>.scope") + " and no " + c("firefox") + " process are left. "
      "The case looks for new crashes of the user with " + c("coredumpctl") + " where " + c("systemd-coredump") + " is installed (Kubuntu) and in " + sysf("/var/crash") + " where apport is (the other three); apport records not every crash, so that line is a hint and not a proof of «none», and the result line says which of the two was looked at.") + \
    note("The cases that restart the display manager inside a machine with the Radeon passed through are forbidden on the Debian bench (the server froze). On the Ubuntu bench the owner allowed them on 26 Nov 2026, with the protection of " + rif("The VM bench") + " in force (" + c("studio/prove-1.2.0/COME-SI-LANCIA.md") + ").", "Allowed on Ubuntu.")

# ── 17.7D Live USB ───────────────────────────────────────────────────────────
S7D = p("A virtual machine is not the machine: the display manager, the video card and the timings of a real boot are different. The owner therefore also tries the product on a <b>real machine started from a live image of Ubuntu 26.04.1</b> "
        "(Ubuntu, Kubuntu, Xubuntu, Lubuntu), one image per flavour. The package is put in with " + c("server/live-installa.sh") + ", run as root from the live terminal and served from another machine on the same network, "
        "and the trial is by hand: a remote desktop of the user " + c("prova") + " is opened, then the same user logs in at the machine, and the remote desktop must close and the local one start.", lead=True) + \
    ul([
        "<b>What the script does</b> (numbered steps, re-runnable): initial checks (it stops with a clear message when the network is missing; it warns if the system is not Ubuntu 26.04); "
        "downloads the " + c(".deb") + " and its " + c(".sha256") + " and refuses to go on if they differ; turns " + c("universe") + " on if it is off; " + c("apt-get install -y --reinstall") + " of the package with what it recommends; creates the two test users " + c("prova") + " and " + c("prova2") + " if they do not exist (it never touches an existing one, nor its password); "
        + c("systemctl enable --now remotix") + ". Apart from " + c("universe") + " and the two users it does what the user manual asks of the administrator.",
        "The name of the package is a variable at the head of the script (" + c("PACCHETTO") + "): " + c("remotix_1.2.0-1+ubuntu26.04_amd64.deb") + ".",
        "<b>What was tried</b> (the owner, 27 Nov 2026, four live images 26.04.1 on a real machine): Ubuntu, Kubuntu and Xubuntu OK; Lubuntu OK after the point of register H7 was understood. On all four the local login closes the remote desktop of the same user; the local desktop starts a few seconds later, the time to close the remote one in order (seen by the owner and accepted). "
        "<b>On the Lubuntu live image</b> the remote desktop takes the settings folder of the installer's session (" + sysf("/etc/xdg/xdg-lubuntu-live-environment") + ", the «Try or install» screen) and not the one of the normal session: icons missing and the panel complete only after about a minute (" + c("local_session_name_find()") + " in " + c("src/session.c") + "). It does not happen on the installed system, "
        "where the installer declares the normal session (a Lubuntu virtual machine had icons and panel in order); the owner decided to leave it as it is. From then on the trials on a real machine are made with a distribution installed on a USB stick, not on a live image.",
    ]) + \
    p("The rule that comes out of the Fedora work holds here too: on a new distribution or desktop, the trial «the local login closes the remote one» is made <b>with programs open in the remote desktop</b>, on a real machine, before publishing.")

# ── 17.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Each item below is something no file in " + c("prove/") + " or " + c("server/") + " can show, with the reason.", lead=True) + \
    table(["Not proven by the tests", "Why, and what exists instead"], [
        ["AppArmor in enforce mode",
         "the profile " + c("remotix_network") + " ships in complain mode. In the containers the kernel interface is not mounted "
         "(" + c("check-package.py") + " says BLOCKED). On the real kernel (live Ubuntu 26.04.1, kernel 7.0, 19 Nov 2026) the profile found defect C4, every sign-in refused by a " + c("deny") + " line that holds even in complain mode, "
         "and the correction was measured there: the system bus and the journal reachable, the abstract sockets still refused, the check of local sessions «CONNECTED». A session works with the profile loaded and in complain mode on the four VMs and the live systems, and since 1.2.0 " + c("check-apparmor.py") + " reads the kernel journal of every round and fails on any line of the profile (the profile also reads " + sysf("/usr/share/applications/org.kde.remotix.desktop") + "). "
         "<b>Not verified:</b> a whole round with the profile in " + c("enforce") + "; docs/STORIA-ubuntu-26.04.md and the register ask for it before the switch."],
        ["A real phone",
         "the check emulates one. The header of " + c("check-phone.py") + " lists what only a phone shows: the Android on-screen keyboard "
         "itself (opening, closing, resizing the viewport, back, autocorrection, word composition), the real size and wobble of a "
         "finger (the thresholds 180 ms, 9 px and 40 px were judged by the owner by hand), palm rejection, a real rotation sensor, "
         "Chrome for Android pointer-event differences, decoding on a phone's hardware, a mobile network. On Ubuntu the owner tried by hand GNOME from Windows, Linux and Android (tablet, Samsung DeX, notebook) on the container box, "
         "and detach and reattach from Linux and from Android on the four VMs (docs/STORIA-ubuntu-26.04.md, 19 Nov 2026). The small video stutters seen from Chrome on Android (register E4) were measured on the server "
         "(no lost packet, 60 frames per second in 35 s of 39, about one frame in twenty a few milliseconds late) and the cause was not isolated between the telephone, the player in the VM, the cadence in a VM and the encoding road on the Radeon; the owner suspects the telephone. "
         "Not closed: the same video from the tablet with the same measure, and on a real machine."],
        ["The first touch on GNOME",
         "GNOME starts in the Overview, which holds touches (a real user sees it too), and one case in thirteen on the Debian bench remained "
         "unexplained: the first tap may land at the initial point if the pointer position reaches the page before Mutter is ready. "
         "Not demonstrated; low priority. On Ubuntu 26.04 (GNOME 50) the check " + c("phone/tap-click-portrait") + " passed in the round of the release (register E2 lists the first touch among the lines that are not always green)."],
        ["NVIDIA and Intel",
         "the code has a Vulkan Video road, chosen by capability, and the dev server has one Radeon that is handed to the VMs and an Intel integrated graphics that stays with the server. NVIDIA was measured on an RTX 4090 on Ubuntu 26.04 on 5 and 6 October 2026, with an earlier version of the code (the comments marked " + c("[M]") + " in the sources); no run of the current build on NVIDIA is recorded, and no Intel encoding run on Ubuntu 26.04 either."],
        ["Canvases above 3840x2160",
         "the page's size ladder (" + c("MEASURE_PROBES") + " in " + c("page.html") + ") stops at 3840x2160, so the page declares no larger " + c("video.max_size") + " with any browser; SPECS "
         "§6.1 allows up to 4096x2304, which is therefore not proven in the picture. " + c("canvas-limits") + " limits what it expects by the declared maximum (" + rif("The checks of all.sh and what each proves") + "). The declared limit of the product is 3K."],
        ["A real graphical login at the machine",
         "the container boxes boot to " + c("multi-user.target") + " with no display manager running; on the VMs P7 to P9 of " + c("check-prelocal.py") + " make a real local login by the automatic login of the display manager, and " + c("prelocal.sh") + " the cases 1 to 3, but nobody types a password at a greeter. "
         "On the four live images on a real machine the owner tried the local login with the remote desktop open (27 Nov 2026, " + rif("Testing the real machine from a live USB") + "); the Lubuntu live image behaves differently from the installed system (register H7), and a Lubuntu installed on a real machine, with the Calamares of the image, was not tried. See " + rif("Appendix C — Known issues and open points") + "."],
        ["The programs of snap and Flutter in the remote session",
         "defect C5 (the settings file of the remote session that snap and Flutter programs could not read) appeared only on the real systems, because the containers have no snap. The correction (the system dconf database) was verified by hand: the installer of the live, Firmware Updater, Security Center and App Center opened without the error "
         "(docs/STORIA-ubuntu-26.04.md and register C5). No automated check opens such a program; " + c("package-snap.py") + " and " + c("check-desktop.py") + " do not know of them."],
        ["Real networks",
         "the tests run on 127.0.0.1 (or on QEMU's user network). The only fault injected is the nft cut of UDP in " + c("network-drop") + "; loss, jitter, NAT "
         "and mobile links are not exercised by this suite."],
        ["Real keyboards",
         "AltGr is not producible through DevTools or WebDriver; physical layouts other than the emulated Italian one are not "
         "tried."],
        ["Several users on real load",
         "the most users attached together in any check is three (" + c("three-users") + "). The capacity figures are in "
         + rif("Performance and capacity") + "."],
        ["The removal and the purge of the package on Ubuntu 26.04",
         "" + c("check-package.py") + " needs a box that can be reset; no run of it on Ubuntu 26.04 is on record (" + rif("The package check") + "). The update from 1.0.1 to 1.2.0 and the removal with " + c("purge") + " were tried by script on the four VMs in the 1.2.0 round and left them clean (register G3)."],
    ], "«TAB» — What the test suite cannot prove") + \
    tip("A statement in this manual that depends on one of the rows above is marked as not verified where it appears.") + \
    h4("The lesson of the containers") + \
    p("Two defects of the Ubuntu work, C4 (every sign-in refused) and C5 (snap and Flutter programs), were invisible on the container bench for reasons that are written in the tree: <b>a container does not exercise AppArmor and has no snap</b>. "
      "A bench that does not run a protection cannot show that the protection is wrong, and it shows green. The rule that came out of it (register C4): before closing a port to a new distribution, a login must succeed on a real machine, or a virtual one, with AppArmor (or SELinux) in force, and the log line «§5.1 … CONNECTED» must be read. "
      "The second lesson (B3-bis): when the <i>same</i> line is red on all four desktops while it was green on the earlier distribution, suspect the tool and look at the raw events first. Three lines (" + c("mouse-drag") + " in two browsers and " + c("tap-and-half-drag-select") + ") failed identically everywhere, and the cause was the test window, not the product (GTK 4.22, above).")

# ── 17.9 ─────────────────────────────────────────────────────────────────────
S9 = p("This section reports what the records say: the reports in " + c("studio/") + ", " + c("docs/STORIA-ubuntu-26.04.md") + ", the register of problems and the logs on the dev server. Nothing was run to write it. The package of the container and first VM rounds is " + c("remotix_1.0.0-1+ubuntu26.04_amd64.deb") + " in successive builds (the work called them " + c("unione1") + " to " + c("unione10") + ", and then " + c("unione11") + "); the one of the 1.2.0 rounds is " + c("remotix_1.2.0-1+ubuntu26.04_amd64.deb") + ". The name of a build does not matter here, the checks quoted are named with the build that ran them.", lead=True) + \
    h4("Container rounds, 18 November 2026") + \
    p("Full rounds of " + c("all.sh") + " on the four container boxes, with the first build that had all four desktops (" + c("unione1") + ") and with the build after the first corrections (" + c("unione2") + ") (reports " + c("studio/giro1-<desktop>.md") + " and " + c("giro2-<desktop>.md") + "; the counts are theirs, not re-measured):") + \
    table(["Desktop", "unione1", "unione2", "Lines that explain the difference or stay red"], [
        ["GNOME", "116 PASS of 124", "123 of 124", c("desktop/users-shell-and-environment") + " (" + c("pkexec") + ", SHELL empty: known and accepted, E2). Closed: " + c("mouse-drag") + " in both browsers and " + c("tap-and-half-drag-select") + " (the test window did not log the release, B3-bis), and the two renamed Ctrl+Alt lines"],
        ["KDE", "111 of 124", "121 of 124", "unione1 had " + c("lifecycle/logout") + " and " + c("desktop/settings-intact") + " red (KDE leaving in the first seconds, closed by a correction), " + c("reattach-windows-inside") + " (the panel's pixels in the measure) and one " + c("media/codec") + " line that did not repeat. The three red lines of unione2 are not detailed in the report read for this manual"],
        ["XFCE", "117 of 124", "126 of 128", "128 rows because of the renamed and added lines; why 128 and not 124 is not stated in the report read. Two lines were not PASS in unione2"],
        ["LXQt", "117 of 124", "124 of 124 (ALL PASS)", "seven FAIL to PASS, no regression"],
    ], "«TAB» — The container rounds of 18 Nov 2026 (from studio/giro1-* and giro2-*)") + \
    p("Later container rounds (for example those of the builds " + c("unione4") + " and " + c("unione5") + ") and the hand tests on the containers (19 Nov 2026: all four desktops OK from Windows, Linux and Android) are recorded only as lines of " + c("docs/STORIA-ubuntu-26.04.md") + ". One recorded finding: the red " + c("canvas-limits")
      + " line of XFCE in the " + c("unione4") + " round was a crash dialog of " + c("blueman") + " that covered the screen (" + c("studio/14-canvas-xfce.md") + "), not a defect of REMOTIX.") + \
    h4("The first real machine, and what it found") + \
    p("19 Nov 2026, afternoon: the live Ubuntu 26.04.1 on the server's own hardware, package of the build then current. Every sign-in was refused (C4: the " + c("deny unix") + " line of the profile); once corrected, the GNOME desktop opened, and the programs of snap made with Flutter failed on the settings file of the remote session (C5). "
      "Neither was visible on the containers. The corrections are described in " + rif("Files the package installs") + " and in " + rif("The startup declarations") + ".") + \
    h4("The 1.2.0 rounds") + \
    p("On 26 and 27 Nov 2026 the four machines of the bench had a complete automatic round with the 1.2.0 package (GNOME 125 PASS and 1 known FAIL, the others 126 PASS), the real local login with programs open, the update from 1.0.1 and the removal; the owner then tried the four VMs and the four live images by hand, all OK. The details are in " + rif("The VM bench") + " and " + rif("Testing the real machine from a live USB") + "; open points: registers H1 to H7.") + \
    h4("The VM bench") + \
    p("The round of the release package of 19 Nov 2026 on the GNOME machine, 120 PASS, 2 FAIL, 1 BLOCKED and 3 SKIP, with the explanation of each line, is in " + rif("The VM bench") + ". Everything else that the bench produced is the installation logs of the four machines and the short controls with the Radeon "
      "(log folder " + sysf("log/consegna/") + "): each machine started, the card arrived two seconds after the start of the service (" + rif("The startup declarations") + "), a login as " + c("prova2") + " reached a session with a picture, and the browser was then closed: the session of " + c("prova2") + " stayed (detached, as designed) and the bench ended it with " + c("loginctl terminate-user") + ". The exit from the desktop was not tried by that control.") + \
    h4("Package checks of the build system") + \
    p("The checks that " + c("build/build-deb.sh") + " and now " + c("build/build-deb-vm.sh") + " make on the finished file, with " + c("TWICE=1") + ", are in " + rif("The package checks R4, R13, R14, R23 and R24") + ": all SI for the package of 19 Nov 2026, lintian with 0 errors and 0 warnings. "
      "The final 1.2.0 package (build finale1, 27 Nov 2026, sha256 78ebec78f49709928bc42d1afce9a37dd7f9e552f2ba4a20c37eeb2e9f51fe8f) was built on the build VM, twice with an identical result; its check files were read: every line YES, lintian E=0 W=0, 35 files.") + \
    h4("Open items that touch the tests") + \
    ul([
        "The three checks that the register lists as not always green: " + c("desktop/users-shell-and-environment") + " on GNOME (wanted so), the pointer at the corner covered by the panel on XFCE, and the first touch of the phone check on GNOME (register E2).",
        "The two checks of 20 Nov 2026, " + c("power-implied") + " and " + c("power-local-seat") + ", failed on the Ubuntu VM with the rule of 15 actions (unione10) and passed with the rule of 19 (unione11) in a partial round of the desktop check only (log " + sysf("vm-gnome-poweroff-dopo/") + "); no complete round exists for unione11 (" + rif("The checks of all.sh and what each proves") + ").",
        c("check-package.py") + " not run on Ubuntu 26.04, and probably not aligned with the dconf database made by the postinst (" + rif("The package check") + ").",
        "AppArmor in enforce mode not tried; the autobind of unix sockets is not closed by the profile (register C4).",
        "The register's E3 (the snapshot of the user manager's environment can be old, and «could not look» counts as «closed») and E4 (video stutters from Chrome on Android) are open and not blocking.",
        "From the 1.2.0 round: one failure of mouse and keyboard on GNOME not explained and not reproduced, and the abnormal ends of some programs after the end of the session (registers H3 and H4); the Lubuntu live image (H7).",
    ])

CHAPTER = ("Testing", [
    ("What a check is and how it decides", S1),
    ("The files of prove/", S2),
    ("The checks of all.sh and what each proves", S3),
    ("Running the suite", S4),
    ("The package check", S5),
    ("The four test boxes", S6),
    ("The real-system virtual machine", S7),
    ("The VM bench", S7B),
    ("The tools of the 1.2.0 work", S7C),
    ("Testing the real machine from a live USB", S7D),
    ("What only a real machine or a real phone can prove", S8),
    ("What was verified on Ubuntu 26.04, and what was not", S9),
])
