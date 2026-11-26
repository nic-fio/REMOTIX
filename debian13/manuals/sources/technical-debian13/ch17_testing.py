"""Chapter 17 — Testing. Sources: prove/ (all.sh, fresh.sh, matrix.sh, check-*.py, prelocal.sh, hold*.py, lib.py, browserlib.py,
inputlib.py, avlib.py, deskkit.py, the window scripts, package-snap.py, fanwatch.py, headless-*.sh, banco-vm/), server/ (vm-radeon.sh,
prepara-server-vm.sh, live-installa.sh, VM-BANCO.md), boxes/ and server/vm.sh, vm-login-test.py, prepara-server.sh (the older container
files, still in the tree); PIANO.md «Stato» sections of 17 and 18 Nov and 26 Nov 2026; studio/prove-1.2.0/; the logs of the dev server."""
from build import arrow, box, c, fig, h4, note, p, rif, sysf, table, term, text, tip, ul, warn, zone

# ── Figure: how a check sees the product ─────────────────────────────────────
RIG = fig(
    zone(20, 14, 410, 160, "Dev server (host)")
    + box(36, 46, 180, 44, "check-*.py", "one verdict line per check", "dark", 12)
    + box(236, 46, 180, 44, "lib.Rig", "compositor + browser + user", "blue", 12)
    + box(36, 112, 180, 44, "headless labwc", "software rendering", "soft", 11.5)
    + box(236, 112, 180, 44, "Chrome / Firefox", "real browser, real input", "soft", 11.5)
    + arrow(217, 68, 234, 68) + arrow(326, 92, 326, 110) + arrow(236, 134, 218, 134)
    + zone(470, 14, 410, 160, "Virtual machine of the bench (Debian 13, systemd, AppArmor, one desktop)")
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
        + c("prove/lib.py") + " enforces it: a broken tool step is BLOCKED, never a PASS.",
        "<b>Nothing is shared between runs.</b> Each run starts its own headless labwc in its own runtime directory (class "
        + c("Compositor") + ", started in a private user, network and mount namespace so that it takes none of the host's X "
        "display numbers), its own browser profile, and DevTools or Marionette ports picked by the operating system. On the VM "
        "bench the Radeon is handed to one machine at a time, so the desktops are tried one after the other.",
        "<b>Every wait has a deadline.</b> " + c("guard()") + " sets a whole-run alarm; every failure of the tool is a "
        + c("ToolError") + " that says why. The compositor and the browsers are children of the check and die with it. The environment "
        "variable " + c("RX_TEMPO") + " (an integer of at least 1; anything else is refused, never read as \"no deadline\") multiplies every "
        "deadline: " + c("all.sh") + " sets it to 2 on the VM bench (" + c("lib.py") + " " + c("guard()") + ").",
        "<b>The users are the check's own.</b> Each check creates users with a prefix of its own (" + c("bc") + ", " + c("lc")
        + ", " + c("mu") + ", " + c("rs") + ", " + c("ac") + ", " + c("cb") + ", " + c("bn") + ", " + c("dk") + ", " + c("md")
        + ", " + c("in") + ", " + c("ph") + ", " + c("pl") + ", followed by digits; " + c("check-package.py") + " uses " + c("pkg") + "), and " + c("sweep()") + " at the end of " + c("all.sh")
        + " ends every session of the prefixes in its pattern (" + c("bc") + ", " + c("lc") + ", " + c("mu") + ", " + c("rs") + ", " + c("ac") + ", " + c("cb") + ", " + c("bn") + ", " + c("dk") + ", " + c("dkf") + ", " + c("md") + ", " + c("in") + ", " + c("ph") + " and " + c("pl") + "). "
        "The checks that are not in " + c("all.sh") + " use the prefix " + c("kx") + " (" + c("check-exit.py") + ", " + c("check-kde-exit.py") + "), which the pattern does not contain: the check removes its own user. A login with a user that may not exist is never tried, because a wrong "
        "login counts for the address ban (" + rif("Login and its defences") + ").",
        "<b>Verdicts are built on the application, not on what the browser was told.</b> A key counts as delivered only when "
        + c("window-input.py") + " inside the session logged it.",
    ]) + \
    note("The checks run on the dev server only. They need QEMU with OVMF and the vfio set-up (the VM bench), the host's "
         "PipeWire-pulse for Firefox audio, two browsers, " + c("labwc") + " and PIL; " + c("server/prepara-server-vm.sh") + " installs them "
         "after every reboot (the server's root file system is in RAM; its VM packages are " + c("qemu-system-x86") + ", " + c("qemu-utils") + ", "
         + c("ovmf") + ", " + c("gdisk") + ", " + c("dosfstools") + ", " + c("e2fsprogs") + ", " + c("rsync") + ", " + c("perl") + ", " + c("openssh-client") + ", "
         + c("util-linux") + " and " + c("acl") + ", and for the checks " + c("chromium") + ", " + c("firefox-esr") + ", " + c("labwc") + ", " + c("wlr-randr") + ", " + c("python3-pil") + ", " + c("libavcodec61") + " and PipeWire). "
         "There are no containers on the bench: tests and studies run on virtual machines.", "Where they run.") + \
    p("Nothing in this chapter was run while writing the manual. The results quoted in "
      + rif("What was verified, and what was not") + " are the recorded logs of the dev server and the "
      "PIANO.md notes, with their dates. The owner decides how and when a round is run.")

# ── 17.2 ─────────────────────────────────────────────────────────────────────
S2 = p("Everything is under " + c("prove/") + ". The Python files form three layers: libraries, checks, and test windows that "
       "run inside the virtual machine.", lead=True) + \
    table(["File", "Role"], [
        "Libraries",
        [c("lib.py"), "the common kit: " + c("Results") + " (verdict lines), " + c("Box") + " (commands in the machine through "
         + c("box.sh") + ": with " + c("RX_BANCO=vm") + " it is " + c("prove/banco-vm/box.sh") + ", which talks to the virtual machines), "
         + c("Compositor") + " (headless labwc, on the dev server), " + c("Chrome") + " (DevTools over a hand-made "
         "WebSocket), " + c("Firefox") + " (Marionette), " + c("Rig") + " (compositor + browser + user: open the page, log "
         "in, wait for the desktop, test window, key chords), " + c("sweep()") + ", and the picture judges " + c("judge_pixel()")
         + " and " + c("frac()") + ", the port table (8861 to 8864 for the VMs " + c("gnome") + ", " + c("kde") + ", " + c("xfce") + ", " + c("lxqt")
         + "; the table keeps the 8811 to 8814 of the older container boxes) and " + c("Box.apparmor()") + ", which reads the kernel journal for lines of the "
         "profile " + c("remotix_network") + " (" + c("check-apparmor.py") + ")"],
        [c("browserlib.py"), "two small browser drivers with the same face (navigate, js, screenshot, move, click, type_text, "
         "press, close), used by " + c("base-check.py") + " and " + c("avlib.py")],
        [c("inputlib.py"), "on top of " + c("lib.py") + ": real mouse buttons, wheel and keys for both browsers, the input test "
         "window and its event log, classification of a cursor image by its pixels, touch and phone emulation (used by "
         + c("check-input.py") + " and " + c("check-phone.py") + ")"],
        [c("avlib.py"), "what " + c("check-audio.py") + " and " + c("check-clipboard.py") + " share (own user, compositor, real "
         "login, key chords); it imports " + c("base-check.py") + " for its page ids and JavaScript bodies. Its private PulseAudio of the lxqt "
         "container box (127.0.0.1:4713) does not exist in a VM: with " + c("RX_BANCO=vm") + " " + c("ensure_pulse()") + " answers \"SKIP on the VMs\" and "
         + c("check-audio.py") + " uses the host's PipeWire"],
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
         "twelve of the thirteen checks that " + c("all.sh") + " runs (next section)"],
        [c("check-apparmor.py"), "the thirteenth check of " + c("all.sh") + ": the kernel journal of the whole round holds no line of the AppArmor profile "
         + c("remotix_network") + " (verdict " + c("profile-coverage") + "); see the next section"],
        [c("check-exit.py") + ", " + c("check-kde-exit.py"), "the ways a remote desktop ends leave nothing behind (XFCE and LXQt; KDE). NOT part of " + c("all.sh")
         + "; see " + rif("The tools of the 1.2.0 work") + ""],
        [c("check-package.py"), "the package check: install, first start, remove, purge, reinstall, the refusal of a person "
         "called remotix. NOT part of " + c("all.sh") + ": it resets the box, which a VM cannot do (" + rif("The package check") + ")"],
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
        [c("all.sh"), "every check on ONE machine, in sequence, one log per check and a final table; " + c("RX_BANCO=vm") + " selects the VM bench (next sections)"],
        [c("fresh.sh"), "with " + c("RX_BANCO=vm") + " it hands over to " + c("banco-vm/fresh-vm.sh") + " (clean state inside the running VM); without it, "
         "the older container way, which needs the folder " + c("boxes/") + " (" + rif("The VM bench") + ")"],
        [c("matrix.sh"), "every desktop on a fresh box: Chrome (new session) then Firefox (resumed); it calls " + c("fresh.sh") + " and so belongs to the container way"],
        [c("prelocal.sh"), "the real local login on lightdm and sddm in a VM (" + rif("The tools of the 1.2.0 work") + ")"],
        [c("hold.py") + ", " + c("hold-user.py"), "helpers that log in from the browser and keep the remote session open for a number of seconds while the machine is looked at "
         "from outside (" + rif("The tools of the 1.2.0 work") + ")"],
        [c("headless-wayland.sh"), "start or stop a headless labwc (used by " + c("base-check.py") + " and " + c("avlib.py") + ")"],
        [c("headless-multi.sh"), "the same, but the pid written is labwc's own so that stop really stops it; no caller was found "
         "in " + c("prove/")],
        "The VM bench (prove/banco-vm/)",
        [c("banco-vm/box.sh"), "the face the checks use for a virtual machine: " + c("ssh") + " (a command AS ROOT, with the bench key), " + c("rootkey") + " (puts the key in once, through "
         + c("prova") + " and sudo), " + c("install <de> <x.deb>") + " (copies the package in and runs " + c("apt-get install -y --reinstall") + "), " + c("status") + "; "
         + c("reset") + " is not available on a VM"],
        [c("banco-vm/fresh-vm.sh"), "the \"fresh box\" for a VM that stays on: stops the service, ends and removes the test users, removes the checks' own drop-ins, "
         "renames a non-empty ban file, installs the few tools the container image had if they are missing (after a simulation: if apt would upgrade or remove "
         "anything, nothing is installed and it is a FAIL), then starts the service again. It checks the result"],
        [c("banco-vm/autologin-lightdm.sh") + ", " + c("autologin-sddm.sh"), "switch the automatic login of lightdm (XFCE) and sddm (KDE, LXQt) on and off in a machine, for the "
         "tests of the real local login; test-bench files, never installed by the package"],
    ], "«TAB» — The files of prove/") + \
    p("The folders " + c("shots/") + " (pictures), " + c("work/") + " and " + c("log/") + " are made by the checks and are not "
      "in git; the logs of a round are in " + c("log/<tag>/") + " of the folder the tree was copied to on the dev server.")

# ── 17.3 ─────────────────────────────────────────────────────────────────────
S3 = p("All checks take " + c("--box xfce|lxqt|gnome|kde") + " (REMOTIX ports 8861 to 8864 on the virtual machines, see " + rif("The VM bench")
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
         + c("page-shortcuts-declared") + ", " + c("page-cad-hidden") + ", " + c("page-cad-chain") + "), "
         + c("page-keyboard-lock") + " (Chrome), two Firefox clipboard lines, " + c("page-ctrl-alt-end-passes") + " last",
         "buttons, double click, wheel, drag, exact coordinates, cursor shape, edge drag, no double cursor; text, Ctrl chords, "
         "Shift+arrows, Alt+Tab, Super, function keys, key repeat, accents, AltGr characters, keys that cannot be produced, Caps "
         "Lock; the page's declared shortcuts; outside diagnostics the page shows no Ctrl+Alt+Del or Ctrl+Alt+End button (" + c("page-cad-hidden") + "; BLOCKED if the "
         "diagnostics are on) and the diagnostic button sends the three keys (" + c("page-cad-chain") + "); a Ctrl+Alt+End typed on the keyboard reaches the "
         "desktop untouched and the session stays on (" + c("page-ctrl-alt-end-passes") + ")"],
        [c("check-phone.py") + " (1250 s)", "19 names, " + c("login-desktop") + " to " + c("reattach-portrait"),
         "the page used as a phone, by emulation: portrait and landscape geometry, tap, drag, two- and three-finger taps, "
         "on-screen keyboard open, text, enter, delete and close, tap-and-half-drag selection, two-finger scroll, pinch zoom, "
         "rotation"],
        [c("check-prelocal.py") + " (2400 s)",
         c("P1-hook-closes-desktop") + ", " + c("P2-new-desktop-after") + ", " + c("P3-hook-ignores") + ", " + c("P4-no-desktop")
         + ", " + c("P5-service-stopped") + ", " + c("P6-pam-line-order") + ", " + c("P7-busy-terminal") + ", " + c("P8-unsaved-editor"),
         "the local-login hold (" + rif("The local-login hold") + "), with Chrome and the check's own users " + c("pl1") + " and " + c("pl2")
         + ". P1: with a remote desktop open the hook returns 0 within 15 s and afterwards nothing of the user is left (no logind "
         "session of the service, no program, no unit of the desktop in the user manager), the page was told with 0x04 and the "
         "journal has the request and the root side's answer. P2: 12 s later (births are refused for 10 s) a new remote login of "
         "the same user gets a working desktop. P3: five calls that are not a local graphical login (no seat, close_session, "
         "greeter, tty, service remotix) each return 0 in under 1 s and the desktop is still alive. P4: a user with no remote "
         "desktop: the hook returns 0 in under 2 s. P5: with the service stopped the hook returns 0 in under 2 s (the service is "
         "started again at the end). P6: " + c("/etc/pam.d/common-session") + " has the " + c("pam_exec") + " line of the hook after the "
         + c("pam_systemd") + " line. <b>P7 and P8 make the forced-close road run</b>, which P1 does not (P1 closes an EMPTY desktop): the remote desktop of the user " + c("pl3")
         + " (P7) has the desktop's terminal running " + c("top") + ", the one of " + c("pl4") + " (P8) an editor holding unsaved text (KWrite on KDE, Mousepad on XFCE; on GNOME and LXQt "
         "P8 is BLOCKED, because there is no simple, reliable way to open an unsaved document without interaction). Then a REAL local login of the same "
         "user is made (the display manager's automatic login, a test-bench file, and the display manager restarted) and the check demands a local desktop "
         "(a session with the seat, the local shell, the local compositor) and NOTHING left of the remote one: no process, no desktop unit with the same invocation, no "
         + c("remotix") + " logind session, no KWin " + c("--virtual") + " (KDE), and no new core dump of the user when " + c("coredumpctl") + " is installed (" + c("fresh-vm.sh")
         + " installs " + c("systemd-coredump") + "; otherwise the evidence says it was not checked). They take about 3 minutes each and are BLOCKED, never PASS, when the program cannot be started "
         "inside the remote desktop"],
        [c("check-apparmor.py") + " (180 s, after " + c("check-ban.py") + ")",
         c("profile-coverage"),
         "the kernel journal of the whole round (from five seconds before its start, read by " + c("all.sh") + " from the machine's own clock) has no line "
         + c("apparmor=\"ALLOWED\"") + " or " + c("apparmor=\"DENIED\"") + " of the profile " + c("remotix_network") + " or a child of it. The package installs the profile in "
         "complain mode, so what the profile does not cover shows as ALLOWED (in enforce it would be DENIED); both are FAIL. If the profile is not loaded or the log cannot be read, "
         "the verdict is BLOCKED (\"AppArmor NOT checked\"), never PASS"],
        [c("check-ban.py") + " (900 s)",
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
        "that machine (on the VM bench every client reaches the VM as " + c("10.0.2.2") + ", QEMU's user network address, so that one address is tried; " + c("RX_BAN_ADDR") + " overrides it). To unblock it uses a drop-in with " + c("--command-socket") + " (a bench option of the binary that the packaged "
        "unit never passes; the check adds it through " + c("REMOTIX_OPTIONS") + " in " + c("/etc/remotix/remotix.conf.d/") + ") and at the end it ALWAYS unblocks, removes the drop-in, restarts the service and logs a user in normally "
        "(" + c("cleanup") + "). Run it alone on a machine; " + c("check-apparmor.py") + " comes after it only to read the journal.",
        c("check-prelocal.py") + " cases P1 to P6 <b>simulate</b> the local login: the hook is run as root "
        "inside the machine by hand, with the environment " + c("pam_exec") + " would give it (" + c("PAM_TYPE=open_session") + ", "
        + c("XDG_SEAT=seat0") + ", class " + c("user") + ", type " + c("wayland") + "), and no local session is registered in logind. They "
        "prove the hook and the root side's answer. P7 and P8 make a real local login through the display manager. What no check does is "
        "type the password at the real greeter: " + c("all.sh") + " lists " + c("prelocal/real-greeter") + " as a SKIP on the VMs, and the owner does it by hand on real machines (" + rif("Testing the real machine from a live USB") + "; " + rif("Appendix C — Known issues and open points") + ").",
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
S4 = p("A run is one command per desktop, started on the dev server in " + c("prove/") + ", against a virtual machine that is already on and has the "
       "package installed. The machines run one at a time with the Radeon (" + rif("The VM bench") + "); a run on a machine without it "
       "(started " + c("virtuale") + ") has no hardware encoder.", lead=True) + \
    term("""$ cd prove                                                         # on the dev server (the folder of the tree copied there)
$ RX_BANCO=vm bash all.sh xfce --fresh /path/to/remotix_1.2.0-1+deb13_amd64.deb   # clean state, package installed, then every check
$ RX_BANCO=vm bash all.sh gnome --clean                                 # clean state, keep the installed package
$ RX_BANCO=vm bash all.sh kde --only ban,audio-firefox                 # a partial round (the machine is NOT cleaned without --fresh/--clean)
$ RX_BANCO=vm python3 check-base.py --box lxqt --browser chrome     # one check alone""",
         "Running all.sh") + \
    p("With " + c("RX_BANCO=vm") + " the script first puts the bench key into the machine (" + c("box.sh rootkey") + ", a NOTE row when it had to) and tests that 300,000 random bytes sent on stdin through the root ssh arrive intact (md5); "
      "if either fails, nothing runs. " + c("--fresh <deb>") + " and " + c("--clean") + " then run " + c("fresh.sh") + ", which hands over to " + c("banco-vm/fresh-vm.sh") + ": if that fails the run stops and every row is BLOCKED.") + \
    ul([
        c("--only label,label") + " runs a subset; the labels are " + c("base-chrome") + " " + c("base-firefox") + " " + c("lifecycle") + " " + c("multiuser") + " " + c("desktop") + " " + c("media") + " "
        + c("resilience") + " " + c("audio-chrome") + " " + c("audio-firefox") + " " + c("clipboard") + " " + c("input-chrome") + " " + c("input-firefox") + " " + c("phone") + " " + c("prelocal") + " " + c("ban") + " "
        + c("apparmor") + " " + c("package") + "; an unknown label is refused with the list. " + c("package") + " is valid but runs nothing on the VMs (a SKIP row, " + rif("The package check") + ").",
        "The output of each check goes to " + c("log/<tag>/<check>.out") + ", ending with an " + c("exit=<n>") + " line. Each "
        "verdict line becomes one table row " + c("<check>/<name>") + "; a check that printed no verdict line is BLOCKED (\"no "
        "verdict\"), and one that hit its time limit is BLOCKED (\"no answer\").",
        "After the last check " + c("lib.sweep()") + " ends the sessions of the test users; a session left over is a BLOCKED row.",
        "The table is printed and saved as " + c("log/<tag>/summary.txt") + ". Besides the check rows it can hold " + c("NOTE") + " rows (the bench key was installed; the KDE Welcome Center was hidden in "
        + c("/etc/skel") + " by the bench) and " + c("SKIP (reason)") + " rows, never a PASS and never a failure: on the VMs " + c("prelocal/real-greeter") + " (the real graphical login cannot be automated), "
        + c("ban/other-addresses") + " (all clients reach the VM as one address) and " + c("package") + ". The last lines count PASS, FAIL, BLOCKED/other, SKIP and NOTE and say one of " + c("ALL PASS") + ", "
        + c("ALL PASS (n SKIP with the reason in the table, none of them a PASS)") + ", " + c("ALL PASS OF A PARTIAL RUN (only: …): not a full run") + ", " + c("NO CHECK PRODUCED A PASS: nothing proven (not ALL green)") + ", or «N line(s) not PASS».",
        "<b>Exit status.</b> 0: a full run, every line PASS. 1: anything else, including an aborted run. 2: a wrong call (usage, unknown label, a bad " + c("RX_TEMPO") + "). 3: every line PASS but the run was partial (" + c("--only") + ").",
        "SIGTERM, SIGINT and SIGHUP stop the running check and mark the remaining ones BLOCKED (aborted).",
        "The limits of the " + c("run") + " calls add up to 19,540 s (about 5 h 26 min); with " + c("RX_TEMPO=2") + " it is 39,080 s. That is a ceiling, not a measured "
        "duration: no measured duration of a whole run is recorded in the files read for this chapter.",
    ]) + \
    table(["Command", "Use"], [
        [c("prove/banco-vm/fresh-vm.sh <de>"), "a clean state inside the running machine (" + c("DEB=<file>") + " installs that package too)"],
        [c("python3 prove/check-package.py --box <de> --deb <file>"), "the package check (next section); it needs a box it can reset"],
        [c("python3 prove/check-<name>.py --box <de>"), "one check alone; several take " + c("--only a,b") + " to run some names"],
        [c("prove/prelocal.sh xfce|lxqt|kde 1|2a|2b|3"), "the real local login on the machine (" + rif("The tools of the 1.2.0 work") + ")"],
    ], "«TAB» — Running pieces of the suite") + \
    p("The desktops are tried one at a time, because the Radeon is one. The owner decides how and when a round is run; a round on a real machine, from a USB stick, is made by hand (" + rif("Testing the real machine from a live USB") + ").")

# ── 17.5 ─────────────────────────────────────────────────────────────────────
S5 = p(c("check-package.py") + " tests the .deb itself on a box that it may reset freely. It is not in " + c("all.sh") + ": it "
       "resets the box at the start (and again for the refusal check) with " + c("box.sh reset") + " and at the end leaves it fresh, with the package installed "
       "and the service enabled (" + c("fresh.sh") + "). <b>A virtual machine cannot be reset by the bench</b> (" + c("banco-vm/box.sh") + " refuses " + c("reset")
       + "; the only way back is " + c("vm-radeon.sh spegni") + " and " + c("ripristina") + ", which the owner decides), so on the VM bench the check cannot run: " + c("all.sh") + " shows a SKIP row. "
       "It was written for the older container boxes; the manual does not claim that it passes on the VMs.", lead=True) + \
    table(["Verdict name", "What it proves"], [
        [c("install"), "apt install on a fresh box: the expected files only (a snapshot diff from " + c("package-snap.py")
         + "), service installed but NOT enabled and NOT running, system user remotix with nologin shell, nothing listening on 7447; "
         "the hook " + c("remotix-local-login") + " and the profile " + c("/usr/share/pam-configs/remotix") + " are there and "
         + c("pam-auth-update") + " has put the " + c("pam_exec") + " line into " + c("/etc/pam.d/common-session")],
        [c("first-start"), "after enable --now: active, TCP and UDP listening, certificates and secrets with safe modes, no error "
         "in the journal, and the two processes as designed (root side as root; network side as remotix with an empty "
         + c("CapEff") + ", " + c("NoNewPrivs") + " and seccomp on)"],
        [c("apparmor"), "that the network side's profile is loaded and enforcing (a profile loaded in complain mode, as shipped, is a FAIL); BLOCKED if the box has no AppArmor interface. "
         "What the shipped profile does in a live session is read by " + c("check-apparmor.py") + " instead"],
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
    p("What stands in its place on the VM bench: the checks of the build (" + c("build-deb-vm.sh") + " checks the finished .deb, " + rif("The package checks R4, R13, R14, R23 and R24") + "), "
      + c("check-apparmor.py") + " at the end of every round, and the trials by hand on the machines. What the package contains and how its scripts behave is in " + rif("The package") + ".")

# ── 17.6 ─────────────────────────────────────────────────────────────────────
S6 = p("The bench of REMOTIX for Debian 13 is virtual machines: QEMU with KVM and UEFI, one per desktop, with Debian 13 really installed on a virtual disk "
       "from the system of the Debian 13.8.0 live image of that desktop, and a fifth one that only builds the package (" + rif("The build of the .deb on the build VM") + "). "
       "The server's Radeon card is handed to one machine at a time by passthrough (vfio-pci). There are no containers on this bench: tests and studies run on "
       "virtual machines only. The scripts are " + c("server/vm-radeon.sh") + " (438 lines), " + c("server/prepara-server-vm.sh") + " (94 lines) and "
       + c("prove/banco-vm/") + "; " + c("server/VM-BANCO.md") + " is the note that goes with them.", lead=True) + \
    h4("The machines") + \
    table(["Machine (check key)", "ISO (read-only)", "ssh / REMOTIX ports", "Display manager"], [
        [c("gnome"), c("debian-live-13.8.0-amd64-gnome.iso"), "2361 / 8861", c("gdm3")],
        [c("kde"), c("debian-live-13.8.0-amd64-kde.iso"), "2362 / 8862", c("sddm")],
        [c("xfce"), c("debian-live-13.8.0-amd64-xfce.iso"), "2363 / 8863", c("lightdm")],
        [c("lxqt"), c("debian-live-13.8.0-amd64-lxqt.iso"), "2364 / 8864", c("sddm")],
        [c("costruzione"), c("debian-live-13.8.0-amd64-xfce.iso"), "2365 / none", c("lightdm")],
    ], "«TAB» — The five VMs of server/vm-radeon.sh (ISO names, ports and display managers from the script)") + \
    p("The machine " + c("costruzione") + " has 8 CPUs and 6 GB of memory, never has the Radeon (the script refuses) and has no REMOTIX port forwarded. The four test machines have 4 CPUs, a 40 GB disk and "
      "5 GB of memory without the Radeon and 12 GB with it (the variable " + c("RX_VM_MEM") + " overrides both), " + c("q35") + " with UEFI (" + c("OVMF_CODE_4M.fd") + ", " + c("OVMF_VARS_4M.fd") + "), KVM, a serial console in "
      + c("serial.log") + " and user networking with the ports of the table forwarded. Each machine's disk, UEFI variables, key " + c("vmkey") + " and serial log are in its own folder under the bench folder. There are two test users (one in the group " + c("sudo") + ", one without sudo); the host name is built from the machine's name; the language is " + c("en_US.UTF-8") + " and there is no automatic login. Recorded on 25 Nov 2026: kernel " + c("6.12.118+deb13-amd64") + ", systemd 257.13, "
      + c("firmware-amd-graphics") + " 20250410-2 on all four.") + \
    p("<b>How a disk is made.</b> " + c("crea <name>") + " does not run an installer: it builds the disk from the system of the ISO's squashfs (GPT, a 512 MB EFI partition, ext4), with the kernel "
      "of Debian and never that of the server, removes the " + c("live-*") + " packages and the installer, sets the archives " + c("main non-free-firmware") + ", updates and security, runs "
      + c("apt full-upgrade") + " and adds " + c("openssh-server") + ". Inside that build the boot loader tool does not recognise the disk, so the script writes a first " + c("grub.cfg") + " by hand and, at the first boot "
      "in a VM, runs " + c("grub-install") + " and " + c("update-grub") + " (the real configuration goes only into the UEFI variables of the VM). It refuses to touch an existing disk. The server needs "
      "the packages that " + c("prepara-server-vm.sh") + " installs (" + rif("What a check is and how it decides") + ").") + \
    h4("server/vm-radeon.sh") + \
    table(["Command", "What it does"], [
        [c("crea <name>"), "makes the disk (above)"],
        [c("accendi <name>"), "binds the two PCI functions of the card (video and audio) to " + c("vfio-pci") + " and starts the VM with the Radeon as its only video card, then waits for ssh. Refuses if another VM of the bench holds the card."],
        [c("accendi <name> virtuale"), "no Radeon: a virtual video card (" + c("virtio-vga") + "), no window, same ports. Several virtual VMs may run together; the Radeon only in one."],
        [c("spegni <name>"), "turns the machine off and gives the Radeon back to the server (only if this machine held it)"],
        [c("ssh <name> [cmd]"), "ssh as a test user with the machine's key"],
        [c("stato <name>"), "running or stopped, and which VM holds the Radeon"],
        [c("prova-avvio <name> [--resta]"), "a boot check without the Radeon: prints facts, then powers off; with " + c("--resta") + " it leaves the machine on"],
        [c("schermo <name> <file.png>"), "a screen dump of a machine started with " + c("virtuale") + " (through the QEMU monitor)"],
        [c("tasti <name> <key>…") + ", " + c("scrivi <name> <text>"), "send keys or type text through QEMU's " + c("sendkey") + " (names such as " + c("ret") + ", " + c("tab") + ", " + c("ctrl-alt-f2") + "), for a machine started " + c("virtuale")],
        [c("istantanea <name> <label>"), "a qcow2 snapshot of the disk; the machine must be off"],
        [c("ripristina <name> <label>"), "restores a snapshot; the machine must be off. The current state of the disk is first saved as a snapshot named " + c("prima-<date>-<time>") + " and then discarded from the disk (it stays only in that snapshot). The UEFI variables file is not part of a snapshot"],
    ], "«TAB» — The commands of vm-radeon.sh (the Italian words are the script's own: create, switch on, switch off, state, boot check, screen, keys, type, snapshot, restore)") + \
    p("The Radeon is one, so <b>one machine at a time has it</b>. After a reboot of the server (its root file system is in RAM) " + c("prepara-server-vm.sh") + " is run first: it puts back QEMU, OVMF, the disk tools, the kernel modules "
      + c("loop") + ", " + c("squashfs") + " and " + c("vfio-pci") + ", an ACL that lets the user open " + c("/dev/kvm") + ", the browsers and tools of the checks, a sound server for Firefox (PipeWire with a null sink) and the inotify limits ("
      + c("fs.inotify.max_user_instances") + " 8192, " + c("fs.inotify.max_user_watches") + " 1048576, because several compositors and browsers of one user share them). It prints one OK or FAIL line per step and ends with " + c("ALL OK") + ".") + \
    h4("The kernel parameter that the Radeon machines need") + \
    p("Every Debian machine of the bench that receives the Radeon must carry " + c("amdgpu.runpm=0") + " in " + c("GRUB_CMDLINE_LINUX") + " (" + c("/etc/default/grub") + ", then " + c("update-grub") + "). Without it the " + c("amdgpu") + " driver "
      "inside the guest, with no monitor on the card, puts the passed-through Radeon to sleep and wakes it again over and over (" + c("amdgpu: SMU is resuming") + " in the guest's kernel log), and the dev server itself can hang. "
      "Checks: " + c("/proc/cmdline") + " contains it, " + c("/sys/module/amdgpu/parameters/runpm") + " reads 0, and the count of " + c("SMU is resuming") + " lines stays 0. It is a setting of the bench machines, not of the product.") + \
    h4("Snapshots") + \
    p("The snapshot " + c("pulito") + " is the clean install of each of the four test machines; " + c("pronta") + " is the build machine with its dependencies and the static QUIC libraries in place. The other snapshots record the stages of a round of work.") + \
    h4("The scripts around it") + \
    table(["Script", "What it does"], [
        [c("prove/banco-vm/box.sh"), "the face the checks use (" + c("ssh") + ", " + c("rootkey") + ", " + c("install") + ", " + c("status") + "; " + c("reset") + " refuses): " + c("install <de> <x.deb>") + " copies the .deb in and installs it with apt, without a " + c("REMOTIX_PORT") + " drop-in (the machine keeps 7447 inside and the host forwards 886x to it)."],
        [c("prove/banco-vm/fresh-vm.sh"), "a clean state in a running machine (" + rif("The files of prove/") + ")."],
        [c("prove/banco-vm/autologin-lightdm.sh") + ", " + c("autologin-sddm.sh"), "switch the automatic login of lightdm and sddm on and off, for the tests of the real local login."],
        [c("server/prepara-server-vm.sh"), "the server preparation above."],
        [c("server/live-installa.sh"), "286 lines. For a <b>real machine</b> started from a Debian 13 live USB stick (" + rif("Testing the real machine from a live USB") + ")."],
    ], "«TAB» — The scripts around the bench") + \
    note("The older container bench is still in the tree and is not used: " + c("boxes/") + " (" + c("box.sh") + ", " + c("common.sh") + ", " + c("set-dm.sh") + ", " + c("power.sh") + ", " + c("box-identity.sh") + ", " + c("Containerfile") + ": four systemd containers with the ports 8811 to 8814, "
         "one per desktop, with the desktop packages and a registered display manager and nothing of REMOTIX inside), " + c("server/prepara-server.sh") + " (its server preparation, with podman), "
         + c("server/vm.sh") + " (one Debian cloud-image machine on the ports 2301 and 8901) and " + c("server/vm-login-test.py") + " (logs in to that machine with the Chrome driver of " + c("prove/lib.py") + "). "
         "Without " + c("RX_BANCO=vm") + " the checks still look for " + c("boxes/box.sh") + " and the ports 8811 to 8814. The rounds of 17 and 18 November 2026 were made on those containers (" + rif("What was verified, and what was not") + "). "
         "Some comment headers in " + c("boxes/power.sh") + " and " + c("boxes/box-identity.sh") + " still describe other distributions and the old bench scripts; the code that runs is Debian-only.", "Older files.")

# ── 17.7 ─────────────────────────────────────────────────────────────────────
S7 = p("The 1.2.0 work added scripts and checks that are <b>not</b> in " + c("all.sh") + ". Each was written for one question and is run by hand or by a small script.", lead=True) + \
    table(["File", "What it does"], [
        [c("check-exit.py") + " " + c("--box xfce|lxqt"), "three cases with the user " + c("kx1") + " logged in from the browser; after each, within 45 s no process of the desktop (labwc, the session, the panel, Xwayland) and no logind session of REMOTIX may be left: " + c("loginctl terminate-session") + " on the REMOTIX session (the desktop would be an orphan, the sweep of the root side must stop it), " + c("systemctl restart remotix") + " with the desktop open, and a close of the browser followed by 20 s away (the desktop must still be alive, then a new login resumes it)"],
        [c("check-kde-exit.py"), "the same three cases on KDE (labwc, " + c("kwin_wayland") + ", " + c("plasmashell") + ", " + c("ksmserver") + ", " + c("kded6") + ", Xwayland); the state of " + sysf("plasma-kwin_wayland.service") + " is printed for information"],
        [c("prelocal.sh") + " <de> 1|2a|2b|3", "on XFCE, LXQt and KDE with the real display manager: 1, remote desktop open, local automatic login of " + c("lc1") + ", the remote closes and the local desktop stays; 2a, the same after the remote leader is killed with SIGKILL; 2b, the same after a restart of the service; 3, a local session active and a remote login of the same user refused (\"already signed in locally\"). The login is a test-bench file written by " + c("banco-vm/autologin-*.sh") + ", and the display manager is restarted"],
        [c("hold.py") + " [seconds]", "logs in from the browser (as " + c("lib.Rig") + " does) and stays logged in, writing " + c("/tmp/hold-ready") + " when the desktop has arrived. Variables " + c("RX_USER") + ", " + c("RX_PASS") + ", " + c("RX_BOX") + "; " + c("RX_KEEP=1") + " does not end the user's existing sessions first, to try a remote login while the same user has a local session"],
        [c("hold-user.py"), "like " + c("hold.py") + ", but the user is made by the script with no card groups added: the product's own enrolment at the first connection must do it. " + c("RX_NOEND=1") + " keeps the user's existing manager. With " + c("pkill -9 -u <user> -x remotix") + " and a look at the journal it is the orphan-desktop test"],
        [c("check-apparmor.py"), "also in " + c("all.sh") + " (" + rif("The checks of all.sh and what each proves") + ")"],
    ], "«TAB» — The tools of the 1.2.0 work (none of the first five is in all.sh)") + \
    p("Why " + c("check-prelocal.py") + " has P7 and P8: a check that opens an <i>empty</i> remote desktop only ever runs the orderly close, so the forced road, the one that stops a desktop with a program still open, was never asked. "
      "P7 and P8 open a desktop with a terminal running " + c("top") + " and with an editor holding unsaved text. On Debian, P7 was run on GNOME on the bench (P8 is BLOCKED there); the owner tried the local-login close with open programs (one that closes by itself, one that asks for confirmation) on the four Debian 13.8.0 live images on a real machine on 26 Nov 2026: all four passed (below).")

# ── 17.8 ─────────────────────────────────────────────────────────────────────
S7B = p("A virtual machine is not the machine: the display manager, the two video cards and the timings of a real boot are different. The owner therefore also tries the product on a <b>real machine started from a Debian 13 live USB stick</b> "
        "(13.8.0: GNOME, KDE Plasma, Xfce, LXQt), one stick per desktop. The package is put in with " + c("server/live-installa.sh") + ", run as root from the live terminal and served from another machine on the same network, "
        "and the trial is by hand: a remote desktop of the user " + c("prova") + " is opened with programs inside, then the same user logs in at the machine, and the remote desktop must close and the local one start.", lead=True) + \
    ul([
        "<b>What the script does</b> (seven numbered steps, re-runnable): initial checks (it STOPS with a clear message when the network is missing, because apt needs the Debian archive, which it checks through apt itself; it downloads with " + c("wget") + " or " + c("curl") + " and installs " + c("wget") + " if both are missing); "
        "downloads the " + c(".deb") + " and its " + c(".sha256") + " and refuses to go on if they differ; prepares apt; " + c("apt install") + " of the package with what it recommends (labwc, wlr-randr, xwayland, the video drivers); creates the two test users " + c("prova") + " and " + c("prova2") + " if they do not exist (it never touches an existing one, nor its password); "
        + c("systemctl enable --now remotix") + "; and runs " + c("remotix --encoding-test h264") + " to say whether the video card encodes. If " + c("ufw") + " is active it only warns, and says how to open the port.",
        "The name of the package is a variable at the head of the script (" + c("PACCHETTO") + "): " + c("remotix_1.2.0-1+deb13_amd64.deb") + ". If a file with an administrator's public key is also served, the script can open ssh for root with it, only to read the logs of the trial; nothing else on the system is changed.",
        "<b>What was tried</b>: the owner tried the local-login close with open programs (one that closes by itself, one that asks for confirmation) on the four Debian 13.8.0 live images on a real machine on 26 Nov 2026: all four passed.",
    ]) + \
    p("The rule that comes out of the Fedora work holds here too: on a new distribution or desktop, the trial «the local login closes the remote one» is made <b>with programs open in the remote desktop</b>, on a real machine, before publishing.")

# ── 17.8 ─────────────────────────────────────────────────────────────────────
S8 = p("Each item below is something no file in " + c("prove/") + " or " + c("server/") + " can show, with the reason.", lead=True) + \
    table(["Not proven by the tests", "Why, and what exists instead"], [
        ["AppArmor during a live session",
         "the profile " + c("remotix_network") + " ships in complain mode, and nothing in the tree switches it to enforce. " + c("check-apparmor.py") + " reads the kernel journal of every round for lines of the "
         "profile and fails on any (the box must really have AppArmor and the profile loaded, or it is BLOCKED). A round with no line is evidence for what that round started, "
         "not a proof for every program a user might start inside a desktop."],
                ["A real phone",
         "the check emulates one. The header of " + c("check-phone.py") + " lists what only a phone shows: the Android on-screen keyboard "
         "itself (opening, closing, resizing the viewport, back, autocorrection, word composition), the real size and wobble of a "
         "finger (the thresholds 180 ms, 9 px and 40 px were judged by the owner by hand), palm rejection, a real rotation sensor, "
         "Chrome for Android pointer-event differences (Samsung and DeX), decoding on a phone's hardware, a mobile network. The "
         "owner tried Samsung DeX on GNOME on 17 Nov 2026 by hand (PIANO.md)."],
        ["The first touch on GNOME",
         "on Fedora 45 (mutter 51) the first absolute pointer movement after the login was measured to reach the windows with one coordinate at 0, so that a tap made at once lands on the edge. " + c("input.c") + " sends the first movement of a device twice "
         "(its comment says the repeat is harmless on compositors that need none and must be removed when Mutter is fixed). Whether the Mutter of Debian 13 (GNOME 48) has the same defect was not measured here; "
         "before the repeat one case in thirteen of the phone check was left unexplained (PIANO.md, 17 Nov 2026), and no phone round with the repeat is recorded for this manual."],
                ["NVIDIA",
         "the code was measured on an RTX 4090 (driver 595) on Ubuntu 26.04 on 5 and 6 October 2026, with an earlier version of the code: the comments marked " + c("[M]") + " in " + c("wlroots.c") + ", " + c("child.c") + ", " + c("session.c") + ", "
         + c("capture.c") + " and " + c("vulkanvideo.c") + " record what that card does (labwc offers only 24-bit pixels, the card refuses the linear slab, Mutter on GNOME 50 agrees a format, the leftovers of the scope). "
         "Vulkan Video is a general road chosen by capability (AMD with RADV and NVIDIA's driver take it), not a road of NVIDIA. No NVIDIA run on Debian 13 is recorded; the dev server has an Intel and an AMD card, and the bench hands the Radeon to one VM."],
                ["Canvases above 3840x2160",
         "the largest canvas obtained by " + c("canvas-limits") + " is 3840x2160: the page's size ladder (" + c("MEASURE_PROBES") + " in "
         + c("page.html") + ") stops there, so the page declares no larger " + c("video.max_size") + " with any browser; SPECS "
         "§6.1 allows up to 4096x2304, which is therefore not proven in the picture (see below). The declared limit of the product is 3K."],
        ["A person typing at a real greeter",
         "P1 to P6 of " + c("check-prelocal.py") + " call the hook by hand; P7 and P8 and " + c("prelocal.sh") + " make a real local login through the display manager of the VM, but by its automatic login (a test-bench file), "
         "and " + c("all.sh") + " lists the typed login as a SKIP. The refusal of a remote login while the same user is signed in locally (RCP reason 0x05) is exercised by hand, by " + c("prelocal.sh") + " case 3. "
         "The hold was tried by the owner on the four real login screens with 1.0.x (GNOME with the journal read; KDE, XFCE and LXQt on live Debian 13 systems, as reported by the owner, journals not read), "
         "and the owner tried 1.2.0 on the four live images (" + rif("Testing the real machine from a live USB") + "). See " + rif("Appendix C — Known issues and open points") + "."],
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
S9 = p("This section reports what PIANO.md, the reports in " + c("studio/prove-1.2.0/") + " and the logs on the dev server say, with their dates. Nothing was run to write it, and the logs themselves were not read for this manual.", lead=True) + \
    h4("Version 1.2.0 on the VM bench (26 November 2026)") + \
    ul([
        "The package in trial was built on the build VM (" + rif("The build of the .deb on the build VM") + ") and installed on the four machines. PIANO.md of 26 Nov at 12:50 records the automatic rounds on GNOME, KDE, XFCE and LXQt as passed, "
        "with these items open: " + c("media/screen-updates") + " a little over its limit (1.0 to 1.5 s against 1.0 s) on GNOME, KDE and LXQt, cause not established; " + c("pkexec") + " on GNOME (" + c("users-shell-and-environment") + ", known); "
        + c("kbd-not-producible") + " with Firefox on LXQt, probably the tool.",
        "The first round on GNOME (report " + c("giro1-gnome.md") + ") counted 123 PASS lines, the known " + c("pkexec") + " failure and the same " + c("screen-updates") + " item; the removal with purge left the machine clean; the language, the " + c("PATH") + " and the register line of who closed the connection were as designed.",
        "P7 was run on GNOME on the bench (P8 is BLOCKED there); the owner tried the local-login close with open programs (one that closes by itself, one that asks for confirmation) on the four Debian 13.8.0 live images on a real machine on 26 Nov 2026: all four passed. The checks of the Ctrl+Alt+Del and Ctrl+Alt+End decisions were realigned (" + c("page-cad-hidden") + ", " + c("page-ctrl-alt-end-passes") + "), so the two lines that failed on every desktop on 17 Nov no longer exist under their old names.",
    ]) + \
    h4("The rounds of 17 and 18 November 2026 (1.0.0, on the container boxes)") + \
    p("The code under test is the tree that became version 1.0.0: PIANO.md states that the provisional version number used in its earlier notes designates the same code, tested under that "
      "number. The verdict names " + c("page-cad-button") + " and " + c("page-ctrl-alt-end") + " below are the names of that time.") + \
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
        "checks failed until the specification was aligned (the checks were then rewritten to the decision: " + c("page-cad-hidden") + " and " + c("page-ctrl-alt-end-passes") + ").",
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
    ("The VM bench", S6),
    ("The tools of the 1.2.0 work", S7),
    ("Testing the real machine from a live USB", S7B),
    ("What only a real machine or a real phone can prove", S8),
    ("What was verified, and what was not", S9),
])
