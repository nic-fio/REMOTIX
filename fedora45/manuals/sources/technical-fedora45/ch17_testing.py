"""Chapter 17 — Testing. Sources: prove/ (all.sh, fresh.sh, matrix.sh, check-*.py, giro-*.sh, wall-*.sh, prelocal.sh, lib.py, browserlib.py, inputlib.py,
avlib.py, deskkit.py, the window scripts, package-snap.py, fanwatch.py, headless-*.sh, banco-vm/), server/ (vm-radeon.sh, live-installa.sh,
prepara-server.sh); docs/REGISTRO-problemi.md (F1 to F36); PIANO.md (the log of the Fedora work)."""
from build import arrow, box, c, code, fig, h4, note, p, rif, sysf, table, term, text, tip, ul, warn, zone

# ── Figure: how a check sees the product ─────────────────────────────────────
RIG = fig(
    zone(20, 14, 410, 160, "Dev server (host)")
    + box(36, 46, 180, 44, "check-*.py", "one verdict line per check", "dark", 12)
    + box(236, 46, 180, 44, "lib.Rig", "compositor + browser + user", "blue", 12)
    + box(36, 112, 180, 44, "headless labwc", "software rendering", "soft", 11.5)
    + box(236, 112, 180, 44, "Chrome / Firefox", "real browser, real input", "soft", 11.5)
    + arrow(217, 68, 234, 68) + arrow(326, 92, 326, 110) + arrow(236, 134, 218, 134)
    + zone(470, 14, 410, 160, "Virtual machine of the bench (Fedora 45, systemd, SELinux enforcing, one desktop)")
    + box(486, 46, 180, 44, "remotix.service", "installed from the .rpm", "navy", 12)
    + box(686, 46, 180, 44, "user session", "the real desktop", "navy", 12)
    + box(686, 112, 180, 44, "test window (GTK)", "logs every event it gets", "green", 11.5)
    + arrow(667, 68, 684, 68) + arrow(776, 92, 776, 110)
    + arrow(417, 134, 484, 80, "#475569", True)
    + text(560, 158, "page and WebTransport on the box's port", 10.5)
    + arrow(686, 134, 640, 134, "#475569", True)
    + text(600, 128, "log read", 10.5),
    900, 190, "«FIG» — What a check looks at: the browser is driven from outside, the verdict is read from inside the virtual machine")

# ── 17.1 ─────────────────────────────────────────────────────────────────────
S1 = p("The tests of REMOTIX are not unit tests of C functions: the tree has no unit-test target, and " + c("src/Makefile")
       + " builds the product only. Every check in " + c("prove/") + " works on one of the four virtual machines of the bench (" + rif("The VM bench") + ") with the package installed: it drives a real "
       "browser against it the way a person would (real mouse, keyboard and touch events through the browser's debugging "
       "interface), and decides its verdict from what happened <b>inside</b> the machine: a window in the user's session that "
       "writes down every event it receives, the journal, logind, the process list. SELinux is enforcing on those machines: it is the normal state, and a check that passes there passes with the package's own policy in force.", lead=True) + RIG + \
    p("Rules that hold for every check, taken from the docstrings of " + c("prove/lib.py") + " and of the check files:") + \
    ul([
        "<b>Three verdicts, one line each.</b> A check prints " + c("PASS name - evidence") + ", " + c("FAIL name - evidence")
        + " or " + c("BLOCKED name - evidence") + ", and exits 0 only if every named check is PASS. FAIL means the product did "
        "not do it (this includes: the page does not answer, a valid login is refused). BLOCKED means the tool could not look "
        "(the browser did not start, Marionette did not answer, an earlier step broke). The " + c("Results") + " class of "
        + c("prove/lib.py") + " enforces it: a broken tool step is BLOCKED, never a PASS. " + c("all.sh") + " adds two kinds of row that are not verdicts, "
        + c("SKIP (reason)") + " and " + c("NOTE") + " (" + rif("Running the suite") + ").",
        "<b>Nothing is shared between runs.</b> Each run starts its own headless labwc on the dev server, in its own runtime directory (class "
        + c("Compositor") + ", started in a private user, network and mount namespace so that it takes none of the host's X "
        "display numbers), its own browser profile, and DevTools or Marionette ports picked by the operating system. On the VM bench the Radeon allows one machine at a time.",
        "<b>Every wait has a deadline.</b> " + c("guard()") + " sets a whole-run alarm; every failure of the tool is a "
        + c("ToolError") + " that says why. The compositor and the browsers are children of the check and die with it. The environment "
        "variable " + c("RX_TEMPO") + " (an integer of at least 1, anything else is refused, never read as «no deadline») multiplies every deadline: "
        "the VM bench runs with 2.",
        "<b>The users are the check's own.</b> Each check creates users with a prefix of its own (" + c("bc") + ", " + c("lc")
        + ", " + c("mu") + ", " + c("rs") + ", " + c("ac") + ", " + c("cb") + ", " + c("bn") + ", " + c("dk") + ", " + c("dkf") + ", " + c("md")
        + ", " + c("in") + ", " + c("ph") + ", " + c("pl") + ", followed by digits), and "
        + c("sweep()") + " at the end of " + c("all.sh")
        + " ends every session of those prefixes (the pattern is in " + c("lib.py") + "). The checks born on Fedora use three more prefixes that the pattern does not contain: " + c("kx") + " (" + c("check-exit.py") + ", " + c("check-kde-exit.py") + "), " + c("kr") + " (" + c("check-kde-live.py") + ", " + c("check-kde-resize.py") + ", " + c("check-resize.py") + ") and " + c("kb") + " (" + c("check-kde-birth.py") + "), "
        "and they are not in " + c("all.sh") + ", so " + c("sweep()") + " does not see them, and those users are removed by the check itself or by hand. A login with a user that may not exist is never tried, because a wrong "
        "login counts for the address ban (" + rif("Login and its defences") + ").",
        "<b>Verdicts are built on the application, not on what the browser was told.</b> A key counts as delivered only when "
        + c("window-input.py") + " inside the session logged it.",
    ]) + \
    note("The checks run on the dev server only. They need QEMU with OVMF and the vfio set-up (the VM bench), "
         "the host's PipeWire-pulse for Firefox audio, two browsers, " + c("labwc") + " and PIL; " + c("server/prepara-server.sh") + " installs "
         "them after every reboot (the server's root file system is in RAM; its VM packages are " + c("qemu-system-x86") + ", " + c("qemu-utils") + ", "
         + c("ovmf") + ", " + c("gdisk") + ", " + c("dosfstools") + ", " + c("rsync") + ", " + c("attr") + ", " + c("btrfs-progs") + ", " + c("erofs-utils") + " and " + c("acl") + "). There are no containers on the bench: the owner's rule is that tests and studies run on virtual machines.", "Where they run.") + \
    p("Nothing in this chapter was run while writing the manual. The results quoted in "
      + rif("What was verified on Fedora 45, and what was not") + " are those written in " + c("PIANO.md") + " and in the register of problems, with their dates. The owner decides how and when the tests are run.")

# ── 17.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Everything is under " + c("prove/") + ". The Python files form three layers: libraries, checks, and test windows that "
       "run inside the box.", lead=True) + \
    table(["File", "Role"], [
        "Libraries",
        [c("lib.py"), "the common kit: " + c("Results") + " (verdict lines), " + c("Box") + " (commands in a box through " + c("box.sh") + ": with " + c("RX_BANCO=vm") + " it is the one of " + c("prove/banco-vm/")
         + ", which talks to the virtual machines; the folder " + sysf("boxes/") + " of the Ubuntu tree does not exist here), " + c("Compositor") + " (headless labwc, on the dev server), " + c("Chrome") + " (DevTools over a hand-made "
         "WebSocket), " + c("Firefox") + " (Marionette), " + c("Rig") + " (compositor + browser + user: open the page, log "
         "in, wait for the desktop, test window, key chords), " + c("sweep()") + ", the picture judges " + c("judge_pixel()")
         + " and " + c("frac()") + ", and the port table: 8851 to 8854 for the four virtual machines (" + c("gnome") + ", " + c("kde") + ", " + c("xfce") + ", " + c("lxqt") + "; the table also keeps the 8821 to 8824 of the container bench that does not exist on Fedora)"],
        [c("browserlib.py"), "two small browser drivers with the same face (navigate, js, screenshot, move, click, type_text, "
         "press, close), used by " + c("base-check.py") + " and " + c("avlib.py")],
        [c("inputlib.py"), "on top of " + c("lib.py") + ": real mouse buttons, wheel and keys for both browsers, the input test "
         "window and its event log, classification of a cursor image by its pixels, touch and phone emulation (used by "
         + c("check-input.py") + " and " + c("check-phone.py") + ")"],
        [c("avlib.py"), "what " + c("check-audio.py") + " and " + c("check-clipboard.py") + " share (own user, compositor, real "
         "login, key chords); it imports " + c("base-check.py") + " for its page ids and JavaScript bodies. Its private PulseAudio of the lxqt box "
         "(127.0.0.1:4713) does not exist in a VM: there " + c("ensure_pulse()") + " answers «SKIP on the VMs» and the checks use the host's PipeWire (the dev server's)"],
        [c("deskkit.py"), "what " + c("check-desktop.py") + " and " + c("check-media.py") + " share: running commands INSIDE the "
         "user's session (the cgroup of the logind scope, the environment of the desktop panel), the file-write watcher, the "
         "counter reader. The tables " + c("PANEL") + " and " + c("LOGOUT") + " hold each desktop's panel process and its own "
         "Log Out command"],
        [c("fanwatch.py"), "a fanotify watcher: who wrote which file under a prefix (used by " + c("settings-intact") + ")"],
        [c("package-snap.py"), "runs inside a box, standard library only: a snapshot of /etc, /usr, /var/lib, /run, users, groups, "
         "units, packages, AppArmor profiles, polkit rules and the nft ruleset, and a diff that says whether a package owns "
         "what appeared (used by " + c("check-package.py") + "). <b>Inherited from Ubuntu and not adapted</b>: it still asks dpkg and AppArmor and ignores the folders of snapd and cloud-init, so it cannot be used on Fedora (" + rif("The package check") + ")"],
        "Checks",
        [c("check-base.py") + ", " + c("check-lifecycle.py") + ", " + c("check-multiuser.py") + ", " + c("check-desktop.py")
         + ", " + c("check-media.py") + ", " + c("check-resilience.py") + ", " + c("check-audio.py") + ", "
         + c("check-clipboard.py") + ", " + c("check-input.py") + ", " + c("check-phone.py") + ", " + c("check-prelocal.py") + ", " + c("check-ban.py"),
         "the twelve checks that " + c("all.sh") + " runs (next section). The checks that were born on Fedora and that " + c("all.sh") + " does not run are in " + rif("The checks born on Fedora") + "; " + c("check-desktop.py") + " differs from the Ubuntu one in three places (the LXQt panel file may be in " + sysf("/etc/xdg/lxqt/panel.conf") + ", on KDE a window that KWin made smaller passes if it stays inside the picture and is at least half of it, and the terminal of GNOME is " + c("ptyxis") + ")"],
        [c("check-package.py"), "the package check of the Ubuntu tree: apt, dpkg and AppArmor. <b>Not adapted to rpm and never run on Fedora</b> (" + rif("The package check") + "). NOT part of " + c("all.sh") + ": it resets the box"],
        [c("base-check.py"), "the earlier form of " + c("check-base.py") + " (user " + c("prova") + ", options " + c("--user")
         + " and " + c("--password") + "); still imported by " + c("avlib.py") + " and run by " + c("matrix.sh")],
        "Test windows (copied into the box and started in the user's session)",
        [c("window.py"), "a fullscreen GTK 4 window with one big text entry; one JSON line per event (ready, motion, click, "
         "text); with a colour argument the window is one colour (this is how " + c("check-multiuser.py") + " tells users apart)"],
        [c("test-window.py"), "the same idea, used by " + c("base-check.py") + " and " + c("avlib.py")],
        [c("lifecycle-window.py"), "a variant that adds the window size to every event; no caller was found in " + c("prove/")],
        [c("window-input.py"), "logs EVERY event the application receives: button presses with their repeat count, wheel, every key "
         "with its modifiers, selection, focus, size. A button <b>release</b> is not taken from the click gesture but from the raw events (a " + c("Gtk.EventControllerLegacy")
         + " in the capture phase), and carries no repeat count. The reason is a behaviour of GTK 4.22, met on Ubuntu 26.04 (the GTK version of the Fedora virtual machines was not recorded): a text entry that claims the sequence (to select by dragging) "
         "denies it to the gestures of the window around it, and the gesture then never emits «released»; GTK 4.18 did not do that (register of problems, B3-bis). Modes " + c("input") + " (fullscreen) and " + c("edge")
         + " (a 640x440 decorated window whose edges can be grabbed)"],
        [c("geom-window.py"), "geometry windows: four coloured quadrants, a 6 px frame and a cross (" + c("frame")
         + "), or a 1800x1000 cyan window with a red border (" + c("scene") + "); flat rectangles at integer pixels, so the "
         "browser's picture can be compared pixel by pixel"],
        [c("media-window.py"), "media windows: a binary-coded counter (" + c("count") + ", " + c("bursts") + "), a moving bar with "
         "a flash and a beep every second (" + c("video") + "), a sharpness pattern (" + c("pattern") + ")"],
        "Shell",
        [c("all.sh"), "every check on ONE box, in sequence, one log per check and a final table"],
        [c("fresh.sh"), "<b>Ubuntu's, not adapted</b>: its default package is the newest " + sysf("remotix_*.deb") + " under " + sysf("/media/REMOTIX-UBUNTU/pacchetti") + "; with " + c("RX_BANCO=vm") + " it hands over to " + c("banco-vm/fresh-vm.sh") + ", which is also Ubuntu's (it uses apt). Neither works on Fedora"],
        [c("matrix.sh"), "every desktop on a fresh container box: Chrome (new session) then Firefox (resumed). It calls " + c("fresh.sh") + " and so does not work on Fedora"],
        [c("headless-wayland.sh"), "start or stop a headless labwc (used by " + c("base-check.py") + " and " + c("avlib.py") + ")"],
        [c("headless-multi.sh"), "the same, but the pid written is labwc's own so that stop really stops it; no caller was found "
         "in " + c("prove/")],
        [c("giro-selinux.sh"), "the automatic checks of the SELinux step on one virtual machine: see " + rif("The checks born on Fedora")],
        "The VM bench (prove/banco-vm/)",
        [c("banco-vm/box.sh"), "the same face as the box script of the container bench, for a virtual machine: verbs " + c("ssh") + " (a command as root, with the bench key), " + c("rootkey") + " (puts the key in once), " + c("install <de> <x.rpm>") + " (copies the rpm in and runs "
         + c("rpm -U --nosignature --replacepkgs") + ", else " + c("dnf install") + " to bring the dependencies), " + c("status") + ", and " + c("reset") + ", which refuses ("
         + rif("The VM bench") + ")"],
        [c("banco-vm/autologin-lightdm.sh") + ", " + c("banco-vm/autologin-sddm.sh"), "switch the automatic login of the display manager of XFCE (lightdm) and LXQt (sddm) on and off in a virtual machine, for the tests of the real local login (" + rif("The checks born on Fedora") + ")"],
    ], "«TAB» — The files of prove/") + \
    p("The folders " + c("shots/") + " (pictures), " + c("work/") + " and " + c("log/") + " are made by the checks and are not "
      "in git; the logs quoted in this manual are kept outside the tree; the exact folder of the Fedora rounds was not recorded for this manual (" + c("prelocal.sh") + " uses " + sysf("/media/REMOTIX-FEDORA/tmp/prove-run/prove") + ").")

# ── 17.3 ─────────────────────────────────────────────────────────────────────
S3 = p("All checks take " + c("--box xfce|lxqt|gnome|kde") + " (REMOTIX ports 8851 to 8854 on the virtual machines, see " + rif("The VM bench") + "). The limits are the seconds given to each " + c("run") + " call in " + c("all.sh") + "; the verdict names are the "
       + c("NAMES") + " tuples of each file. The list is that of the tree of 25 Nov 2026; the names were counted from the " + c("NAMES") + " tuples. The last two names of the desktop check, " + c("power-implied") + " and " + c("power-local-seat") + ", were written for Ubuntu and are described below.", lead=True) + \
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
         "power actions: logind answers no to every " + c("Can*") + " as the user, polkit refuses the 19 login1 actions of the rule (" + c("50-remotix-no-poweroff.rules") + ") that this check asks about, real " + c("systemctl poweroff") + " and the like are refused and the box stays up; "
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
        [c("check-prelocal.py") + " (900 s)",
         c("P1-hook-closes-desktop") + ", " + c("P2-new-desktop-after") + ", " + c("P3-hook-ignores") + ", " + c("P4-no-desktop")
         + ", " + c("P5-service-stopped") + ", " + c("P6-pam-line-order") + ", " + c("P7-busy-terminal") + ", " + c("P8-unsaved-editor"),
         "the local-login hold (" + rif("The local-login hold") + "), with Chrome and the check's own users " + c("pl1") + ", " + c("pl2") + ", " + c("pl3") + " and " + c("pl4")
         + ". P1: with a remote desktop open the hook returns 0 within 15 s and afterwards nothing of the user is left (no logind "
         "session of the service, no program, no unit of the desktop in the user manager), the page was told with 0x04 and the "
         "journal has the request and the root side's answer. P2: 12 s later (births are refused for 10 s) a new remote login of "
         "the same user gets a working desktop. P3: five calls that are not a local graphical login (no seat, close_session, "
         "greeter, tty, service remotix) each return 0 in under 1 s and the desktop is still alive. P4: a user with no remote "
         "desktop: the hook returns 0 in under 2 s. P5: with the service stopped the hook returns 0 in under 2 s (the service is "
         "started again at the end). P6: the " + c("pam_exec") + " line of the hook is in the PAM files of the login screens (" + c("gdm-*") + ", " + c("plasmalogin*") + ", " + c("lightdm*") + ", " + c("sddm*") + ") and comes <b>before</b> " + c("pam_selinux open") + " in each of them (the docstring at the head of the file still says "
         + c("common-session") + ", which does not exist on Fedora). P7 and P8, added on 25 Nov 2026 after the defect of the KDE forced close (register F36): the remote desktop has the desktop's terminal running " + c("top") + " (P7), or an editor with text not saved (P8), and the real local login of the same user must still close it; "
         "a case needs the display manager of the virtual machine and takes about three minutes. " + c("--only P7,P8") + " runs some cases. " + c("all.sh") + " calls the check without " + c("--only") + ", so P7 and P8 enter the round; whether the whole check then fits in its 900 s (1800 with " + c("RX_TEMPO=2") + ") was not verified"],
        [c("check-ban.py") + " (900 s, always last)",
         c("wrong-password") + ", " + c("same-answer") + ", " + c("typed-names-not-logged") + ", " + c("ban-after-limit")
         + ", " + c("ban-survives-restart") + ", " + c("unblock") + ", " + c("unblock-shipped") + ", " + c("cleanup"),
         "a wrong password is refused with one sentence and not before the 2.5 s floor (" + c("REJECT_FLOOR") + " in "
         + c("rcp.c") + "); a non-existent user gets the same sentence and time; no typed name in the log before the verdict; 5 "
         "wrong passwords ban the user and the address ban follows the code's limit (" + c("LIMIT") + " in " + c("rcp.c")
         + " is 5, 20 and 30); the ban survives a restart; the package ships no administrator unblock (by decision); at the end the check always unblocks and "
         "logs a user in normally (" + c("cleanup") + ", reported on its own line)"],
    ], "«TAB» — The checks run by all.sh, in the order all.sh runs them") + \
    p("In the tree the tuples give, per desktop, 127 verdict rows (counted with the " + c("NAMES") + " tuples of the files): base 5 and 5, lifecycle 4, multiuser 3, desktop 9, media 4, resilience 5, audio 1 and 1, clipboard 2, "
      "input 26 with Chrome and 27 with Firefox, phone 19, prelocal 8, ban 8 (the seven names and " + c("cleanup") + ").") + \
    h4("The two checks that read the polkit policy") + \
    p(c("power-implied") + " needs no session and no Python in the box. It reads the installed rule " + sysf("50-remotix-no-poweroff.rules") + " and <b>every</b> polkit policy file of the machine, builds the implications "
      "(the annotation " + c("org.freedesktop.policykit.imply") + ", followed along chains) and fails if an action that the rule does not forbid implies one that it forbids: polkit would then grant the forbidden action without "
      "consulting the rule. " + c("power-local-seat") + " runs from root with no REMOTIX session and asks " + c("pkcheck") + ", as the process of the greeter (the active session on seat0, that is the person at the machine), "
      "about <b>every</b> forbidden action: all must be refused. It is calibrated against " + c("login1.chvt") + ", which must be granted; with no greeter it is BLOCKED. "
      "They exist because " + c("power-entries-absent") + " looks only from the remote session, which is not at a seat, and only at the actions known by name; the four " + c("set-reboot-*") + " actions imply " + c("reboot") + ", and the rule of Fedora carries 19 actions like the one of Ubuntu. "
      "Both were run on an Ubuntu virtual machine (and passed with the rule of 19 actions); <b>whether they pass on Fedora was not recorded</b>.") + \
    h4("Things to know before reading a log") + \
    ul([
        c("check-ban.py") + " is the only check that types wrong passwords, and it bans the address the browser comes from on "
        "that box: " + c("10.0.2.2") + " on the VM bench (QEMU's user network shows every client as that address), or the value of " + c("RX_BAN_ADDR")
        + ". To unblock it uses a drop-in with " + c("--command-socket") + " (a bench option of the binary that the packaged "
        "unit never passes; the check adds it through " + c("REMOTIX_OPTIONS") + " in " + sysf("/etc/remotix/remotix.conf.d/") + ") and at the end it ALWAYS unblocks, removes the drop-in, restarts the service and logs a user in normally "
        "(" + c("cleanup") + "). If the cleanup did not run, the check prints a NOTE that says what to undo by hand (on a VM, restore a snapshot, " + rif("The VM bench") + "). Run it last and alone on a box.",
        c("check-prelocal.py") + " mostly <b>simulates</b> the local login: the hook is run as root "
        "inside the box by hand, with the environment " + c("pam_exec") + " would give it (" + c("PAM_TYPE=open_session") + ", "
        + c("XDG_SEAT=seat0") + ", class " + c("user") + ", type " + c("wayland") + "), and no local session is registered in logind. It "
        "proves the hook and the root side's answer; it does not prove the interplay with the periodic sweeps, which only a real local "
        "login exercises (" + rif("Appendix C — Known issues and open points") + "). The VMs do have a real display manager, and " + c("all.sh") + " still calls the hook by hand there and adds a SKIP row, "
        + c("prelocal/real-greeter") + ", because a real graphical login at the greeter of GDM, plasmalogin, LightDM or SDDM cannot be automated; the real login is tried by hand from a USB stick (" + rif("Testing the real machine from a live USB") + "), and on XFCE and LXQt by " + c("prelocal.sh") + " (" + rif("The checks born on Fedora") + ").",
        c("check-phone.py") + " is an emulation, not a phone: Chrome with DevTools device emulation (412x915 CSS px, device scale 2, "
        "touch events with pointer type touch, a mobile user agent, Italian language). What it cannot prove is listed in "
        + rif("What only a real machine or a real phone can prove") + ".",
        c("check-input.py") + " states its limits in its header: DevTools and WebDriver cannot press AltGr, so the Italian AltGr "
        "characters are sent as the character itself, which exercises the page's LETTER path; the browser's pointer lock and the "
        "operating system's own cursor are in no screenshot, so the cursor is judged by the CSS rule on the canvas.",
        c("check-desktop.py") + " on Fedora 45: the GNOME terminal is " + c("ptyxis") + " (not " + c("gnome-terminal") + "); " + c("sudo") + " is the GNU one, whose refusal reads «a password is required» or «not in the sudoers file» (the check also knows the words of sudo-rs, which Ubuntu uses and Fedora does not); the check " + c("users-shell-and-environment")
        + " has a known FAIL on GNOME, " + c("pkexec") + " (an empty " + c("SHELL") + "), recorded in " + c("PIANO.md") + " for the Fedora rounds; " + c("VOLATILE") + " (the files that the desktop itself writes and that " + c("settings-intact") + " does not count) now includes " + sysf(".config/dconf/remotix") + ", "
        "the file that REMOTIX makes by design. " + c("session-cap") + " needs a quiet box.",
        c("canvas-limits") + " waits for the test window to say " + c("ready") + " (up to 150 s; up to about 78 s was measured), waits for a picture that has stopped moving (" + c("still_png()") + "), tries once more "
        "a picture that never stood still, and ignores a few stray pixels near the colour when it measures the window (the sky-blue launcher icon of KDE). The canvas it expects is the one of SPECS §6.1 "
        "(client area rounded down to 16, 320x240 to 4096x2304) <b>limited by the maximum that the page itself declares</b> (" + c("video.max_size MEASURED") + " in the page's log, read by " + c("page_max_size()")
        + "); the page declares at most 3840x2160 (the last rung of " + c("MEASURE_PROBES") + " in " + c("page.html") + "), and the evidence line says so: the server's bound of 4096x2304 cannot be exercised with this page. "
        "The sizes above are technical bounds, not measures of capacity.",
        "The check docstrings can lag behind the code: the docstring of " + c("check-ban.py") + " still describes " + c("unblock-shipped") + " as «the PACKAGE gives the administrator a way to unblock», "
        "while the code passes it when the package ships none. The code is the reference.",
    ])

# ── 17.4 ─────────────────────────────────────────────────────────────────────
S4 = p("A run is one command per desktop, started on the dev server in " + c("prove/") + ", against a virtual machine that is already on and has the package installed. The machines run one at a time with the Radeon (" + rif("The VM bench") + "). "
       "The package is not put in by " + c("all.sh") + " on Fedora: " + c("all.sh --fresh") + " and " + c("--clean") + " go through " + c("fresh.sh") + " and " + c("banco-vm/fresh-vm.sh") + ", which are Ubuntu's (apt and " + c(".deb") + ") and do not work here.",
       lead=True) + \
    term("""$ cd ..                                                            # on the dev server (the folder of the tree copied there)
$ RX_BANCO=vm RX_TEMPO=2 prove/all.sh gnome                              # every check of all.sh on the machine 'gnome', package already installed
$ RX_BANCO=vm RX_TEMPO=2 prove/all.sh kde --only ban,audio-firefox       # a partial round
$ RX_BANCO=vm python3 prove/check-base.py --box xfce --browser chrome      # one check alone
$ prove/giro-selinux.sh kde --extra                                      # the round of the SELinux step on one machine (next section)""",
         "Running all.sh") + \
    p("The way to a machine ready for a run, as the bench does it:") + \
    ul([
        "Start the machine: " + c("server/vm-radeon.sh accendi <de>") + " with the Radeon, or " + c("accendi <de> virtuale") + " without it (" + rif("The VM bench") + "). The test machines start from the snapshot " + c("codec") + " (a clean install with the RPM Fusion codecs).",
        "Put the package in: " + c("prove/banco-vm/box.sh install <de> <file.rpm>") + ", then open the firewall port (the command of " + rif("Files the package installs") + ") and " + c("systemctl enable --now remotix") + ".",
        "Run the checks: " + c("all.sh <de>") + ", or a single " + c("RX_BANCO=vm python3 check-<name>.py --box <de>") + ", or the round " + c("giro-selinux.sh <de> [--extra]") + " (" + rif("The checks born on Fedora") + ").",
    ]) + \
    ul([
        c("--only label,label") + " runs a subset. The labels are " + c("base-chrome") + " " + c("base-firefox") + " " + c("lifecycle") + " " + c("multiuser") + " " + c("desktop") + " " + c("media") + " "
        + c("resilience") + " " + c("audio-chrome") + " " + c("audio-firefox") + " " + c("clipboard") + " " + c("input-chrome") + " " + c("input-firefox") + " " + c("phone") + " " + c("prelocal") + " " + c("ban") + " " + c("package")
        + "; an unknown label is refused with the list. " + c("package") + " is a valid label but runs nothing: " + c("check-package.py") + " is not part of " + c("all.sh") + " (on a VM it is a SKIP row).",
        "The output of each check goes to " + c("log/<tag>/<check>.out") + ", ending with an " + c("exit=<n>") + " line. Each "
        "verdict line becomes one table row " + c("<check>/<name>") + "; a check that printed no verdict line is BLOCKED (\"no "
        "verdict\"), and one that hit its time limit is BLOCKED (\"no answer\").",
        "After the last check " + c("lib.sweep()") + " ends the sessions of the test users; a session left over is a BLOCKED row.",
        "The table is printed and saved as " + c("log/<tag>/summary.txt") + ". Besides the check rows it can hold " + c("NOTE") + " rows (the bench key was installed in the VM) and " + c("SKIP (reason)") + " rows (never a PASS, never a failure). The last lines are " + c("lines of the checks: N PASS, N FAIL, N BLOCKED/other, N SKIP, N NOTE") + " and one of: "
        + c("ALL PASS") + ", " + c("ALL PASS (n SKIP with the reason in the table, none of them a PASS)") + ", " + c("ALL PASS OF A PARTIAL RUN (only: …): not a full run") + ", " + c("NO CHECK PRODUCED A PASS: nothing proven (not ALL green)")
        + ", or «N line(s) not PASS».",
        "<b>Exit status.</b> 0: a full run, every line PASS. 1: anything else, including an aborted run and a failed initial control. 2: a wrong call (usage, unknown label, a bad " + c("RX_TEMPO") + "). "
        "3: every line PASS but the run was partial (" + c("--only") + "): a caller that tests «= 0» cannot take it for a full green.",
        "SIGTERM, SIGINT and SIGHUP stop the running check and mark the remaining ones BLOCKED (aborted).",
        "The limits of the " + c("run") + " calls add up to 17,860 s (about 4 h 58 min). That is a ceiling, not a measured "
        "duration; with " + c("RX_TEMPO=2") + " it is 35,720 s. No duration of a whole Fedora round was recorded for this manual.",
    ]) + \
    table(["Command", "Use"], [
        [c("prove/banco-vm/box.sh install <de> <x.rpm>"), "put a package in a virtual machine (" + rif("The VM bench") + ")"],
        [c("python3 prove/check-<name>.py --box <de>"), "one check alone; several take " + c("--only a,b") + " to run some names"],
        [c("prove/giro-selinux.sh <de> [--extra]"), "the round of the SELinux step (" + rif("The checks born on Fedora") + ")"],
    ], "«TAB» — Running pieces of the suite") + \
    p("The order of the desktops is one at a time, because the Radeon is one. The owner decides how and when a round is run; a round on a real machine, from a USB stick, is made by hand (" + rif("Testing the real machine from a live USB") + ").")

# ── 17.5 ─────────────────────────────────────────────────────────────────────
S5 = p(c("prove/check-package.py") + " is the package check of the Ubuntu tree: it tests a " + c(".deb") + " on a box that it may reset freely (apt, dpkg, " + c("pam-auth-update") + ", AppArmor, purge). <b>It was not adapted to rpm and has never been run on Fedora</b>; "
       "the same is true of " + c("package-snap.py") + ", which it uses. It is not in " + c("all.sh") + ", and a virtual machine cannot be reset by the bench (" + c("banco-vm/box.sh") + " refuses " + c("reset") + "), so it could not run on the bench anyway. The manual does not claim that it passes or fails.", lead=True) + \
    p("What stands in its place on Fedora is of two kinds:") + \
    ul([
        "<b>The checks of the build.</b> " + c("build/build-rpm.sh") + " checks the finished rpm before it brings it back: R13 (the binary does not carry the bench function) and R4 (no missing library, no dynamic ngtcp2 or nghttp3), and writes " + c("controlli.txt") + " (" + rif("The package checks R4, R13, R14, R23 and R24") + ").",
        "<b>The hand trials on the virtual machines</b> (register F18, F19, F21, F24): installation, upgrade, removal, the removal of the package with the block inside the PAM files of sddm, byte for byte, the removal with the folder " + sysf("/var/lib/remotix") + " left over, reinstallation from nothing, and a reboot of the machine with the module loaded (" + rif("Removal: prerm, postrm and purge") + ").",
    ]) + \
    p("There is no purge on Fedora (" + rif("Removal: prerm, postrm and purge") + "), and the AppArmor check of the Ubuntu tree has its counterpart in the negative test of the SELinux wall, " + c("prove/wall-selinux.sh") + ", which passed 25 checks out of 25 on the four desktops (" + c("PIANO.md") + ", 22 Nov 2026; " + rif("The checks born on Fedora") + "). "
      "What the package contains and how its scriptlets behave is in " + rif("The package") + ".") + \
    note("A work item for the future: adapt " + c("check-package.py") + " and " + c("package-snap.py") + " to rpm and SELinux, or remove them from the tree. Until then the tree keeps them as inherited tools, which would fail on Fedora because they ask for programs and files that Fedora does not have.", "Inherited tools.")

# ── 17.8 The VM bench ────────────────────────────────────────────────────────
S7B = p("The bench of REMOTIX for Fedora is virtual machines: QEMU with KVM and UEFI, one per desktop, really installed from the Fedora Live image of that desktop, and a fifth one that only builds the rpm. The server's Radeon card is handed to one machine at a time by passthrough. "
        "There are no containers on this bench, by the owner's rule: tests and studies run on virtual machines only. The scripts are " + c("server/vm-radeon.sh") + " (496 lines), " + c("server/prepara-server.sh") + " (90 lines) and " + c("prove/banco-vm/") + ".", lead=True) + \
    h4("The machines") + \
    table(["Machine (check key)", "ISO (read-only, in /media/DOWNLOAD)", "ssh / REMOTIX ports", "Display manager"], [
        [c("gnome"), c("Fedora-Gnome-Live-45-1.4.x86_64.iso"), "2351 / 8851", c("gdm")],
        [c("kde"), c("Fedora-KDE-Desktop-Live-45-1.4.x86_64.iso"), "2352 / 8852", c("plasmalogin")],
        [c("xfce"), c("Fedora-Xfce-Live-45-1.4.x86_64.iso"), "2353 / 8853", c("lightdm")],
        [c("lxqt"), c("Fedora-LXQt-Live-45-1.4.x86_64.iso"), "2354 / 8854", c("sddm")],
        [c("costruzione"), c("Fedora-Xfce-Live-45-1.4.x86_64.iso"), "2355 / none", c("lightdm")],
    ], "«TAB» — The five VMs of server/vm-radeon.sh (ISO names, ports and display managers from the script)") + \
    p("The machine " + c("costruzione") + " is the one that builds the rpm (" + rif("The RPM build on the build VM") + "): it has 8 CPUs and 6 GB of memory, never has the Radeon and has no REMOTIX port forwarded. The four test machines have 4 CPUs, 5 GB of memory (the variable " + c("RX_VM_MEM") + " overrides it) and a 40 GB disk, "
      + c("q35") + " with UEFI (the firmware files " + c("OVMF_CODE_4M.fd") + " and " + c("OVMF_VARS_4M.fd") + "), KVM, a serial console in " + c("serial.log") + " and user networking with the ports of the table forwarded. Everything lives in " + sysf("/media/REMOTIX-FEDORA/vm-radeon/<machine>/") + ". "
      "The login of the machines is " + c("prova") + " or " + c("prova2") + " (password " + c("prova2026") + ", " + c("prova") + " is in the group " + c("wheel") + "), or the key " + c("vmkey") + ".") + \
    p("<b>How a disk is made.</b> " + c("crea <name>") + " does not run the installer: it builds the disk from the contents of the Live ISO <i>the way the live-image payload of Anaconda does</i> (the files are copied with " + c("rsync") + ", the boot loader entries and " + c("grub2-editenv") + ", " + c("kernel-install"
      ) + "), on a btrfs disk with a " + c("root") + " subvolume and a " + c("home") + " subvolume, and boots it once with a virtual video card so that the SELinux relabel (" + c("/.autorelabel") + ") and the first UEFI entry happen; it then checks the machine and powers it off. It refuses to touch an existing disk. "
      "It is not an unattended installation and does not use a squashfs of an installer. The server needs " + c("btrfs-progs") + " and " + c("erofs-utils") + " for that (the Live image's root file system is an erofs).") + \
    h4("server/vm-radeon.sh") + \
    table(["Command", "What it does"], [
        [c("crea <name>"), "makes the disk (above)"],
        [c("accendi <name>"), "binds the two functions of the Radeon (" + c("0000:03:00.0") + " and its audio function " + c("0000:03:00.1") + ") to " + c("vfio-pci") + " and starts the VM with the Radeon as its only video card, then waits for ssh. Refuses if any VM or any other qemu of the server already holds the card."],
        [c("accendi <name> virtuale"), "no Radeon: a virtual video card (" + c("virtio-vga") + "), no window, same ports. Several virtual VMs may run together; the Radeon only in one. The virtual card gives a render node but does not encode."],
        [c("spegni <name>"), "poweroff over ssh, then ACPI power-down, then a declared kill as a last resort; waits until the process is really gone; only then gives the card back (the audio function to " + c("snd_hda_intel") + ", the GPU stays without a driver, as at boot)"],
        [c("ssh <name> [cmd]"), "ssh as " + c("prova") + " with the machine's key"],
        [c("stato <name>"), "running or stopped, which VM holds the Radeon"],
        [c("prova-avvio <name> [--resta]"), "a boot check <b>without</b> the Radeon: prints facts, then powers off; with " + c("--resta") + " it leaves the machine on"],
        [c("schermo <name> <file.png>"), "a screen dump of a machine started with " + c("virtuale") + " (through the QEMU monitor)"],
        [c("tasti <name> <key>…") + ", " + c("scrivi <name> <text>"), "send keys or type text through QEMU's " + c("sendkey") + " (names such as " + c("ret") + ", " + c("tab") + ", " + c("ctrl-alt-f2") + "); these are the way to act on a greeter that has no ssh, in a machine started " + c("virtuale")],
        [c("istantanea <name> <label>"), "a qcow2 snapshot of the disk; the machine must be off"],
        [c("ripristina <name> <label>"), "restores a snapshot; the machine must be off. <b>The current state of the disk is discarded</b>: the script does not save it first (as the Ubuntu script did), and it is an explicit command only. The UEFI variables file is not part of a snapshot"],
    ], "«TAB» — The commands of vm-radeon.sh (the Italian words are the script's own: create, switch on, switch off, state, boot check, screen, keys, type, snapshot, restore)") + \
    p("The Radeon is one, so <b>one machine at a time has it</b>; the four desktops are tried one after the other. The script runs as a user that can use " + c("sudo") + ", because QEMU and vfio need root.") + \
    h4("Snapshots") + \
    p("The snapshot " + c("pulito") + " is the clean install; " + c("codec") + " is the clean install plus the RPM Fusion codecs, and it is the one the test machines start from (REMOTIX needs them, " + rif("Package metadata: Depends and Recommends") + "). The others record the stages of the work (" + c("PIANO.md") + "): " + c("consegna-<de>") + " and " + c("consegna-finale-<de>") + " (the clean machine with only the delivered package, the service on and the port open, for the owner's trials), "
      + c("dopo-prove-proprietario") + " and " + c("dopo-prove-finali") + ", " + c("finale-<de>") + ", " + c("selinux-<de>") + " and " + c("selinux2-<de>") + ", " + c("kde-i1-provato") + " and " + c("kde-i2-provato") + ". The sizes of the ISO images and the kernel version of the machines were not recorded for this manual.") + \
    h4("The scripts around it") + \
    table(["Script", "What it does"], [
        [c("prove/banco-vm/box.sh"), "the face the checks use (" + c("ssh") + ", " + c("rootkey") + ", " + c("install") + ", " + c("status") + "; " + c("reset") + " refuses): " + c("install <de> <x.rpm>") + " copies the rpm in and runs " + c("rpm -U --nosignature --replacepkgs") + ", else " + c("dnf install") + "."],
        [c("server/live-installa.sh"), "334 lines. For a <b>real machine</b> started from a Fedora Live USB stick, as root, from the live terminal: it does what the user manual asks of the administrator (the RPM Fusion codecs, " + c("dnf install") + " of the rpm, the firewalld service at run time only, " + c("systemctl enable --now remotix") + ") and makes two test users; re-runnable. The name of the rpm is a variable at its head (" + c("PACCHETTO") + "): " + c("remotix-1.2.0-1.fc45.x86_64.rpm") + "."],
        [c("server/prepara-server.sh"), "90 lines. Puts back on the server, whose root file system is in RAM and starts clean after every reboot, only what the VMs need (the packages listed in the note of " + rif("What a check is and how it decides") + ")."],
        [c("prove/banco-vm/autologin-lightdm.sh") + ", " + c("autologin-sddm.sh"), "switch the automatic login of lightdm and sddm in a machine, for the tests of the real local login."],
    ], "«TAB» — The scripts around the bench") + \
    p("What does <b>not</b> exist on Fedora, though the Ubuntu manual describes it: " + sysf("vm-radeon-installa.sh") + ", " + sysf("vm-radeon-aggiorna.sh") + ", " + sysf("vm-radeon-controllo.sh") + " and " + sysf("vm-radeon-login-test.py") + ", " + sysf("server/vm.sh") + " (the Ubuntu cloud-image machine) and " + sysf("vm-login-test.py") + ". "
      "The UEFI snapshot rule is unchanged: the " + c("OVMF_VARS.fd") + " file of a machine is not in its qcow2 snapshot.")

# ── 17.9 The checks born on Fedora ───────────────────────────────────────────
S7C = p("The Fedora work added checks and scripts that the Ubuntu tree does not have. <b>None of them is in all.sh.</b> They were written for one defect or one step each, and they are run by hand or by a round script.", lead=True) + \
    table(["File", "What it does"], [
        [c("check-exit.py"), "XFCE and LXQt: the end of a session by " + c("terminate-session") + ", by a restart of the service and by a close followed by a wait (user prefix " + c("kx") + ")"],
        [c("check-kde-exit.py"), "the same on KDE (" + c("kx") + ")"],
        [c("check-kde-birth.py"), "KWin remembers the last size of its output: the size at birth is corrected before the stream is mounted (register F8; " + c("kb") + ")"],
        [c("check-kde-live.py"), "a KDE session with a live desktop (" + c("kr") + "); a known note: «Chromium GONE» is a defect of the bench, not of the product"],
        [c("check-kde-resize.py") + ", " + c("check-resize.py"), "reattachments with different sizes, rounds of ten (" + c("kr") + "); " + c("check-resize.py") + " is the version for the other desktops (GNOME: " + c("--rounds 5") + " in " + c("giro-selinux.sh") + ")"],
        [c("giro-selinux.sh <de> [--extra]"), "the checks of the SELinux step on one virtual machine with the Radeon: for gnome and kde, base, input, lifecycle, clipboard, audio, desktop, (kde: birth, live, resize, exit; gnome: resize) and prelocal; for xfce and lxqt it calls the next two; " + c("--extra") + " adds multiuser, media, resilience, phone and ban, the rest of " + c("all.sh") + ". It prints the PASS, FAIL and BLOCKED lines only; the AVC are looked at afterwards (" + rif("Diagnostic instruments") + "). It prints only the verdict lines, so a check that dies without a verdict leaves no trace in its output: the case of " + c("check-kde-exit") + ", «service restart», which once exited without a result and passed 3 times out of 3 alone, is open (" + c("PIANO.md") + ", 23 Nov 2026)"],
        [c("giro-xfce-radeon.sh") + ", " + c("giro-lxqt-radeon.sh"), "the same round for XFCE and LXQt, with the real local-login tests on lightdm and sddm (the user " + c("lc1") + " must exist)"],
        [c("prelocal.sh"), "a real local login on lightdm and sddm (with the automatic-login scripts of the bench), as opposed to the hook called by hand of " + c("check-prelocal.py")],
        [c("wall-selinux.sh") + ", " + c("wall-neg-domain.py"), "the negative test of the SELinux wall (" + rif("Diagnostic instruments") + ")"],
        [c("wall-sesearch.sh"), "what the loaded policy says about " + c("remotix_net_t") + " (" + c("sesearch") + " on a copy of the policy; the tools are on the build machine)"],
        [c("hold.py") + ", " + c("hold-user.py"), "helpers that keep a remote session open while a test is made"],
    ], "«TAB» — The tools born on Fedora (none is in all.sh)") + \
    p("Why " + c("check-prelocal.py") + " did not see the defect of 25 Nov 2026 (register F36): until then it opened an <i>empty</i> remote desktop, so the orderly close always worked and the forced roads never ran, and the SELinux wall was never asked about them. The cases P7 and P8 (a terminal running " + c("top") + ", an editor with unsaved text) close that gap (" + rif("The checks of all.sh and what each proves") + ").")

# ── 17.10 Live USB ────────────────────────────────────────────────────────────
S7D = p("A virtual machine is not the machine: the display manager, the two video cards and the timings of a real boot are different. The owner therefore also tries the product on a <b>real machine started from a Fedora 45 Live USB stick</b>, one stick per desktop, with an Intel and a Radeon card. "
        "The package is put in with " + c("server/live-installa.sh") + " (served from another machine on the same network), SELinux stays enforcing, and the trial is by hand: a remote desktop of the user " + c("prova") + " is opened with programs inside, then the same user logs in at the machine, and the remote desktop must close and the local one start.", lead=True) + \
    table(["Desktop", "Date and package", "Result (from PIANO.md)"], [
        ["GNOME (gdm)", "25 Nov 2026, " + c("h1"), "OK: the local session disconnected the remote session. 0 denials after the installation; the encoding succeeded on the Intel card."],
        ["KDE (plasmalogin)", "25 Nov 2026, " + c("h1"), "<b>Not passed</b>, a defect of the product (register F36): the orderly close did not end in 10 s, the forced close was refused by the SELinux wall, and the local login went on with the remote KWin alive. Corrected."],
        ["XFCE (lightdm)", "25 Nov 2026, " + c("h1"), "OK: the remote desktop closed in 1.7 s, the local session opened at the first try, nothing of the remote was left, no new denial, no core dump."],
        ["LXQt (sddm)", "25 Nov 2026, " + c("h1"), "OK: closed in 0.7 s, the same outcome."],
        ["KDE (plasmalogin)", "25 Nov 2026, " + c("i1"), "OK, with Konsole running " + c("top") + ": the forced close at 10.05 s, everything stopped 0.56 s later, the hook released at 10.9 s, 0 denials, 0 core dumps."],
        ["KDE (plasmalogin)", "25 Nov 2026, " + c("i2"), "OK with the wait of 5 s: forced at 5.04 s, hook released at 5.9 s, 0 denials, 0 core dumps."],
    ], "«TAB» — The trials from a USB stick of 25 Nov 2026 (the logs of KDE, XFCE and LXQt are kept outside the tree and were not read for this manual; the GNOME logs were not saved)") + \
    p("The lesson, written in the register (F36): on a new distribution or desktop, the trial «the local login closes the remote one» must be made <b>always with programs open in the remote desktop</b> (one that closes by itself and one that asks for confirmation), on a real machine, before publishing; look at which unit the compositor and the panel are bound to (" + c("systemctl --user show -p PartOf") + ") and at the SELinux label of the unit files that the root side must stop. "
      "The trial with the programs that are slow to close, and the one where the user abandons the login, were not made.")

# ── 17.11 ────────────────────────────────────────────────────────────────────
S8 = p("Each item below is something no file in " + c("prove/") + " or " + c("server/") + " can show, with the reason.", lead=True) + \
    table(["Not proven by the tests", "Why, and what exists instead"], [
        ["SELinux on a real local login at the greeter",
         "the wall is in enforcing mode and was proved on the four virtual machines: none of REMOTIX's own denials, the negative test 25 out of 25 (register F24, " + c("PIANO.md") + " of 22 and 23 Nov 2026), and a reboot of the machine with the module loaded. A real graphical login at the machine, with the wall in force, was tried by hand from a USB stick on 25 Nov 2026 on the four desktops (" + rif("Testing the real machine from a live USB") + "); it is not automatable (" + c("all.sh") + " says SKIP)."],
        ["A real phone",
         "the check emulates one. The header of " + c("check-phone.py") + " lists what only a phone shows: the Android on-screen keyboard "
         "itself (opening, closing, resizing the viewport, back, autocorrection, word composition), the real size and wobble of a "
         "finger (the thresholds 180 ms, 9 px and 40 px were judged by the owner by hand), palm rejection, a real rotation sensor, "
         "Chrome for Android pointer-event differences, decoding on a phone's hardware, a mobile network. No phone trial is recorded for Fedora."],
        ["The first touch on GNOME",
         "on Fedora the cause is known and cured: GNOME 51's Mutter gave the first absolute pointer movement after the login with one coordinate at 0 (register F34, 23 Nov 2026), and " + c("input.c") + " sends the first movement twice. After the cure " + c("two-users") + ", " + c("three-users") + " and the phone checks passed (" + c("PIANO.md") + "). "
         "The register says the same defect is almost surely the «first touch» that the Ubuntu tree lists as intermittent."],
        ["NVIDIA and Intel",
         "the first version targets Intel and AMD, Vulkan Video is a general road chosen by capability (the Radeon of the bench takes it), and the dev server has one Radeon that is handed to the VMs. On Fedora, the encoding succeeded on the Intel card of the real machine started from the USB stick (" + c("PIANO.md") + ", 25 Nov 2026). NVIDIA was measured on an RTX 4090 on Ubuntu 26.04 (5–6 Oct 2026) with an earlier version of the code; no NVIDIA run on Fedora 45 is recorded."],
        ["Canvases above 3840x2160",
         "the page's size ladder (" + c("MEASURE_PROBES") + " in " + c("page.html") + ") stops at 3840x2160, so the page declares no larger " + c("video.max_size") + " with any browser; SPECS "
         "§6.1 allows up to 4096x2304, which is therefore not proven in the picture. " + c("canvas-limits") + " limits what it expects by the declared maximum (" + rif("The checks of all.sh and what each proves") + ")."],
        ["The language of the session",
         "the session takes the language the user chose (AccountsService) or the system's (" + c("child.c") + ", register F34 and F35); it was tried on GNOME with a desktop really in Italian (" + c("PIANO.md") + ", 23 Nov 2026). A language without an encoding in AccountsService (" + c("it_IT") + " alone) is <b>to be tried</b> (open in " + c("PIANO.md") + ")."],
        ["Confined SELinux users",
         "tried on the four desktops with " + c("staff_u") + " and " + c("user_u") + " (register F25); on XFCE with " + c("staff_u") + " the panel does not start, a limit of Fedora 45 that is not REMOTIX's (F30). No automated check makes such a user."],
        ["Flatpak programs",
         "they start without anything special, according to the studies (" + c("PIANO.md") + "); no check opens one. Not verified by a run."],
        ["Real networks",
         "the tests run on QEMU's user network. The only fault injected is the nft cut of UDP in " + c("network-drop") + "; loss, jitter, NAT "
         "and mobile links are not exercised by this suite. A client device with a wrong clock cannot connect and the browser says only «Opening handshake failed»; the server's log now says why (" + rif("The startup declarations") + ")."],
        ["Real keyboards",
         "AltGr is not producible through DevTools or WebDriver; physical layouts other than the emulated Italian one are not "
         "tried."],
        ["Several users on real load",
         "the most users attached together in any check is three (" + c("three-users") + "). The capacity figures are in "
         + rif("Performance and capacity") + "."],
        ["The removal of the package 1.2.0 outside the KDE virtual machine",
         "the removal, upgrade and reinstallation were tried on the virtual machines with earlier packages of the same code (register F24); the package 1.2.0 itself was installed, upgraded and removed by hand on the KDE virtual machine only (25 Nov 2026), not by a check of the suite, not on the other desktops and not on a real machine (" + rif("The package check") + ")."],
    ], "«TAB» — What the test suite cannot prove") + \
    tip("A statement in this manual that depends on one of the rows above is marked as not verified where it appears.") + \
    h4("The lesson of the missing protection") + \
    p("A bench that does not run a protection cannot show that the protection is wrong, and it shows green. On Ubuntu, two defects (every sign-in refused by a rule of AppArmor, and the settings of snap programs) were invisible on the container bench for that reason. On Fedora the same lesson came back in another form: the bench did not see the defect of the KDE local login (register F36) because " + c("check-prelocal.py") + " opened an empty remote desktop, so the forced road, and with it the SELinux wall, was never exercised. "
      "The rule that follows, written in the register: before publishing for a new distribution or desktop, a login must succeed on a real or virtual machine with SELinux in force, the local login must be tried with programs open, and the log must be read, not only the verdict. "
      "The second lesson (B3-bis): when the <i>same</i> line is red on all four desktops while it was green on the earlier distribution, suspect the tool and look at the raw events first.")

# ── 17.12 ────────────────────────────────────────────────────────────────────
S9 = p("This section reports what the records say: " + c("PIANO.md") + " (the log of the Fedora work), the register of problems " + c("docs/REGISTRO-problemi.md") + " (F1 to F36), and the studies in " + c("studio/") + ". Nothing was run to write it, and the figures are those written there, with their date; the logs themselves, kept outside the tree, were not read for this manual. "
       "The test packages of the Fedora work are letters and numbers, in sequence: " + c("p4f") + " (GNOME), " + c("k4b") + " (KDE), " + c("l6") + " (XFCE and LXQt), " + c("s8") + ", " + c("s13") + " and " + c("s15") + " (the SELinux wall), " + c("f1") + ", " + c("g6") + ", " + c("h1") + " (the final package of the four desktops, 23 Nov 2026) and " + c("i1") + " and " + c("i2") + " (KDE, 25 Nov 2026). "
       "The package " + c("1.2.0") + " has the same code as " + c("i2") + " with another version number; that it has been rebuilt and tried again was not verified when this chapter was written.", lead=True) + \
    table(["Round", "Where and with what", "Result (from PIANO.md and the register)"], [
        ["The wall, " + c("s13") + ", 22 Nov 2026", "the four VMs, enforcing, Radeon", "gnome 51 PASS (FAIL: " + c("pkexec") + ", known); kde 64 PASS with 4 FAIL that were the same without the wall; xfce 60/0; lxqt 60/0; the negative test of the wall 25/25; reboot of the machine with the module loaded."],
        ["Final round, " + c("f1") + ", 23 Nov 2026", "the four VMs, enforcing", "gnome 52 PASS (FAIL: " + c("pkexec") + ") and the rest of " + c("all.sh") + " 36 PASS (FAIL: " + c("two-users") + ", " + c("three-users") + ", " + c("tap-click-portrait") + ", later cured by " + c("g6") + "); kde 78/0; xfce 60/0; lxqt 60/0; none of REMOTIX's own AVC."],
        ["Final round, " + c("h1") + ", 23 Nov 2026", "the four VMs, enforcing, no permissive, stock " + c("dontaudit") + ", Radeon", "gnome 52 PASS (FAIL: " + c("pkexec") + ") and " + c("all.sh") + " 39 PASS; kde 76; xfce 60; lxqt 60; the negative test 0 FAIL; none of REMOTIX's own AVC."],
        ["KDE, " + c("i2") + ", 25 Nov 2026", "the VM " + c("kde") + ", " + c("check-prelocal.py") + " cases P1 to P8", "all PASS (with the new cases P7 and P8); ten healthy programs close by themselves in 1.1 s; programs that are slow to close were not tried."],
    ], "«TAB» — The rounds, with their dates (figures not recounted)") + \
    p("<b>By hand, by the owner.</b> With " + c("h1") + " and the wall, on the four desktops, on the machines prepared for him (23 Nov 2026): GNOME, KDE, XFCE and LXQt OK. From a USB stick on a real machine, 25 Nov 2026: GNOME, XFCE and LXQt OK, KDE not passed and then OK with " + c("i1") + " and " + c("i2") + " (" + rif("Testing the real machine from a live USB") + ").") + \
    h4("Open points") + \
    ul([
        "<b>The round script hides a dead check.</b> " + c("prove/giro-selinux.sh") + " shows only verdict lines; " + c("check-kde-exit") + ", case «service restart», once exited without a result and passed 3 out of 3 alone: intermittent, the cause to be found when the round keeps the output (23 Nov 2026).",
        "<b>The language without an encoding</b> in AccountsService (" + c("it_IT") + ") is to be tried.",
        "<b>GNOME has no last defence</b> for the forced close, as KDE got on 25 Nov 2026 (register F36), and the code of the forced close is the same on Debian and Ubuntu.",
        c("catatonit") + " (a helper of podman started by Konsole) stays in the user's manager after the local login; a harmless denial, " + c("search") + " on " + sysf("/proc/sys/dev") + ", appears in the journal.",
        c("force_guard_on") + " stays on after a failed local login (" + c("session.c") + "; the line number written in " + c("PIANO.md") + " was not re-checked).",
        "A comment in " + c("child.c") + " (near line 1636) is to be aligned; the code of the old labwc road for KDE is to be removed after the owner's tests (register F7).",
        "<b>Not run, or not adapted:</b> " + c("check-package.py") + " and " + c("package-snap.py") + "; whether " + c("power-implied") + " and " + c("power-local-seat") + " pass on Fedora.",
    ]) + \
    p("The checks of the build system (R13, R4, R24) are described in " + rif("The package checks R4, R13, R14, R23 and R24") + ".")

CHAPTER = ("Testing", [
    ("What a check is and how it decides", S1),
    ("The files of prove/", S2),
    ("The checks of all.sh and what each proves", S3),
    ("Running the suite", S4),
    ("The package check", S5),
    ("The VM bench", S7B),
    ("The checks born on Fedora", S7C),
    ("Testing the real machine from a live USB", S7D),
    ("What only a real machine or a real phone can prove", S8),
    ("What was verified on Fedora 45, and what was not", S9),
])
