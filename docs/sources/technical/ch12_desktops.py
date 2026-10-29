from build import arrow, box, c, code, sysf, fig, note, p, rif, steps, table, text, ul, warn, zone


S1 = p("REMOTIX serves four Wayland desktops, which belong to three compositor families. Capture, input and "
       "clipboard talk to the <b>compositor</b>; birth, logout and settings talk to the <b>desktop</b>. XFCE "
       "and LXQt share labwc and therefore almost everything except the session. On KDE labwc is there too, "
       "but only as an invisible host for KWin, not as the desktop's compositor.", lead=True) + \
    table(["", "GNOME", "KDE Plasma", "XFCE", "LXQt"], [
        ["Compositor", "Mutter (gnome-shell)", "KWin", "labwc (wlroots)", "labwc (wlroots)"],
        ["Recognised by", c("gnome-session"), c("startplasma-wayland"), c("xfce4-session"), c("lxqt-session")],
        ["Started by", "the distribution's GNOME session, through " + c("gnome-session"),
         c("startplasma-wayland") + "; KWin through " + c("remotix --kwin-nested"), c("labwc -m --session") + " + primary client",
         c("labwc -C <ours> -S") + " + primary client"],
        ["Monitor", "none of its own; the capture creates a virtual one", "KWin's output, nested in a labwc "
         "without a screen; born at the requested size, resized at reattach", "headless output born 1280×720, "
         "resized", "same as XFCE"],
        ["Capture", "ScreenCast " + c("RecordVirtual") + " (PipeWire)", c("zkde_screencast_unstable_v1")
         + " (PipeWire)", c("zwlr_screencopy_manager_v1"), "same as XFCE"],
        ["Input", c("libei") + " via " + c("ConnectToEIS"), c("libei") + " via " + c("connectToEIS"),
         "virtual keyboard and pointer", "same as XFCE"],
        ["Clipboard", c("clipboard.c") + " (via RemoteDesktop)", c("clipboard_kde.c") + " (data-control)",
         c("clipboard_kde.c"), c("clipboard_kde.c")],
        ["Alive when", c("DisplayConfig.GetCurrentState") + " answers", c("org.kde.KWin") + " on the bus",
         c("org.xfce.SessionManager") + " on the bus", c("org.lxqt.session") + " on the bus"],
        ["Logout", c("Logout(1)") + ", then " + c("Logout(2)"), c("org.kde.Shutdown.logout") + ", then "
         + c("StopUnit"), c("Logout(false,false)") + ", then SIGTERM to labwc", c("logout()")
         + " (no reply), then SIGTERM to labwc"],
    ], "«TAB» — The four desktops side by side") + \
    p("<b>One desktop per machine</b> (" + c("DECISIONS.md") + " §0.6, 20 Sep 2026; §4.6-duodetricies): REMOTIX looks for "
      "the desktop that is installed, it does not arbitrate between desktops that coexist, and the "
      + c("--compositore") + " (compositor) option of v1 is not coming back. Machines with several desktops are out of "
      "scope; when two are found the choice is made and declared “ambiguous”. Only Wayland sessions "
      "are served; X11 applications run through XWayland.") + \
    p("The four desktops were added one per phase (12 KDE, 13 XFCE, 14 LXQt) under the user's rule "
      "“add the new desktop without breaking what already works”: every desktop branch is placed "
      "<b>in front of</b> the GNOME code, which stays textually unchanged and is skipped with a "
      + c("return") + " or " + c("goto") + ".")

S2 = p(c("recognize_desktop()") + " decides once per process, from the programs in " + c("PATH") + ", and "
       "keeps the reason in words for the server's start line (" + c("session_desktop_explain()") + ").",
       lead=True) + \
    table(["Found", "Desktop", "Note"], [
        [c("startplasma-wayland") + " and not " + c("gnome-session"), "KDE", ""],
        ["both", "GNOME", "declared ambiguous"],
        [c("gnome-session"), "GNOME", ""],
        [c("xfce4-session"), "XFCE", "with " + c("lxqt-session") + " too: XFCE, declared ambiguous; without "
         + c("labwc") + ", declared that the session cannot be born"],
        [c("lxqt-session"), "LXQt", "without " + c("labwc") + ", declared"],
        ["none", c("SESSION_DESKTOP_NONE"), "No session is attempted"],
    ], "«TAB» — The recognition order") + \
    ul([
        "The XFCE marker is " + c("xfce4-session") + ", not " + c("labwc") + ": labwc is the family's "
        "compositor, shared with LXQt, and remains a precondition.",
        "Until phase 12 a machine with neither GNOME nor KDE was declared GNOME by fallback; on an XFCE box "
        "the failure surfaced as “another drop-in wins over mine” and “Mutter does not expose "
        "RemoteDesktop”, two innocents accused (measured 20 Sep 2026). The fallback was removed: "
        + c("SESSION_DESKTOP_NONE") + " is honesty, not a desktop.",
        c("DesktopSession") + " travels as a " + c("uint32_t") + " between parent and child, so new values go "
        "at the end: GNOME 0, KDE 1, XFCE 2, none 3, LXQt 4.",
        "Capture, input, clipboard and stage rebuild ask " + c("session_on_wlroots()") + " (XFCE or LXQt), not "
        "“is it XFCE”: with five comparisons against XFCE, LXQt would have fallen silently into the "
        "GNOME/KDE branch.",
    ])

S3 = p("The environment of the session is <b>composed, not inherited</b> (" + c("compose_environment()")
       + "): whatever the starter carries ends up in the user's systemd manager and in D-Bus activation, "
       "where it outlives the compositor. A stray " + c("LC_ALL=C") + " from an SSH shell once stopped every "
       "application from opening.", lead=True) + \
    table(["Variable", "GNOME", "KDE", "XFCE", "LXQt"], [
        [c("XDG_RUNTIME_DIR") + ", " + c("DBUS_SESSION_BUS_ADDRESS") + " (the bus deduced as "
         + c("unix:path=$XDG_RUNTIME_DIR/bus") + " if absent)", "yes", "yes", "yes", "yes"],
        [c("XDG_CURRENT_DESKTOP"), c("DesktopNames") + " of the chosen session", "—", c("XFCE"),
         c("LXQt:labwc:wlroots")],
        [c("XDG_SESSION_DESKTOP") + ", " + c("XDG_SESSION_TYPE"), "session id, " + c("wayland"), "—",
         c("xfce") + ", " + c("wayland"), c("lxqt") + ", " + c("wayland")],
        [c("XDG_MENU_PREFIX"), "—", c("plasma-"), c("xfce-"), c("lxqt-")],
        [c("XDG_CONFIG_DIRS"), "—", "our " + c("xdg") + " directory first", "our labwc directory first",
         "our " + c("xdg-lxqt") + " directory, then " + c("/etc:/etc/xdg:/usr/share")],
        [c("XDG_DATA_DIRS"), "—", "—", "—", "our " + c("data-lxqt") + " (session data) directory first"],
        [c("XCURSOR_THEME") + ", " + c("XCURSOR_SIZE") + ", " + c("XCURSOR_PATH"), "—",
         c("remotix-invisible") + ", 24", c("remotix-invisible") + ", 24", c("remotix-invisible") + ", 24"],
        [c("WLR_BACKENDS") + ", " + c("WLR_LIBINPUT_NO_DEVICES"), "—", "only in KWin's labwc: "
         + c("headless") + ", 1", c("headless") + ", 1",
         c("headless") + ", 1"],
        [c("WLR_RENDER_DRM_DEVICE") + " or " + c("WLR_RENDERER"), "—", "only in KWin's labwc: same as XFCE",
         "the first openable "
         + c("renderD*") + " node, or " + c("pixman"), "same"],
        [c("LABWC_UPDATE_ACTIVATION_ENV"), "—", "only in KWin's labwc: 0", "1", "1"],
        [c("KWIN_FORCE_SW_CURSOR"), "—", "1, in KWin's environment", "—", "—"],
        ["Toolkit", "—", "—", c("GDK_BACKEND=wayland"), c("QT_QPA_PLATFORM=wayland") + ", "
         + c("QT_QPA_PLATFORMTHEME=lxqt")],
        [c("XFCE4_SESSION_COMPOSITOR"), "—", "—", c("labwc -m --session xfce4-session"), "—"],
        [c("SHELL"), "empty", "the user's login shell from passwd", "same", "same (D-022: qterminal "
         "falls back to /bin/sh without it)"],
        [c("DCONF_PROFILE"), "the session profile (D-015)", "—", "—", "—"],
        [c("LANG") + " (always a UTF-8 locale that exists), " + c("HOME") + ", " + c("USER") + ", " + c("PATH"),
         "yes", "yes", "yes", "yes"],
    ], "«TAB» — The composed environment") + \
    p("<b>The render node.</b> wlroots is given the first " + c("/dev/dri/renderD*") + " that can actually be "
      "opened (the numbers swap between boots, and on the test machine the second node is a card excluded on "
      "purpose), and REMOTIX first checks with GBM that a 256×256 " + c("XRGB8888") + " buffer can be created "
      "on it. If not, " + c("WLR_RENDERER=pixman") + " is set and declared: otherwise wlroots would fall back "
      "to software in silence, or the canvas would be black.") + \
    p("<b>Starting.</b> " + c("start()") + " runs " + c("setsid --fork sh -c") + " with the composed "
      "environment and the user's home as working directory, with the session's output appended to "
      + c("~/.local/state/remotix/session.log") + " (the session log, under " + c("$XDG_STATE_HOME")
      + "; a directory and file that must belong to the user and "
      "not be writable by others, opened with " + c("O_NOFOLLOW") + "), or to "
      + c("$XDG_RUNTIME_DIR/remotix-session.log") + " as a declared fallback. Because of "
      + c("setsid --fork") + " the session lives outside the server's unit: measured on 29 Sep 2026, stopping "
      "the unit or killing the parent or the child kills no desktop on any of the four, and a reattach finds "
      "the same compositor and windows. The child does not wait for the birth: "
      + c("session_spawn()") + " starts it only from a dead session and "
      "returns at once (at most one request a minute); the child's retry loop (1 s doubling to 30 s) finds the "
      "session on a later round. The 40 s wait " + c("WAIT_STARTUP_MS") + " belongs to the blocking "
      + c("session_ensure()") + ", which the product no longer calls. The life cycle is in "
      + rif("Startup and life cycle") + ".")

S4 = p("GNOME is started through the distribution's own session, with a systemd drop-in that makes "
       "gnome-shell headless and without monitors: the only monitor is the virtual one that the capture "
       "creates with " + c("RecordVirtual") + ", and that is where GNOME puts its top bar and dock.",
       lead=True) + \
    steps([
        "<b>Which session</b> (D8, " + c("gnome_session()") + "): among " + c("wayland-sessions/*.desktop")
        + " entries that run " + c("gnome-session") + " with an installed " + c(".session") + " file, take the only one if "
        "there is just one, otherwise prefer the one named after the distribution (" + c("ID") + " of os-release, e.g. " + c("ubuntu") + "), then "
        + c("gnome") + ", then the first alphabetically, as GDM does; if none, " + c("gnome") + " as a declared "
        "fallback. The " + c("Exec") + " line is used as the command, " + c("DesktopNames")
        + " as " + c("XDG_CURRENT_DESKTOP") + ".",
        "<b>Which shell unit</b> (" + c("unit_shell()") + "): up to GNOME 49 " + sysf("org.gnome.Shell@wayland.service")
        + "; from GNOME 50 the template " + sysf("org.gnome.Shell@.service") + " with " + c("--mode=%i")
        + ", whose instance is the one that " + sysf("gnome-session@<session>.target") + " requires ("
        + c("@user") + " for " + c("gnome") + ", " + c("@ubuntu") + " on Ubuntu 26.04). Chosen from what is "
        "installed, not from a version number.",
        "<b>The drop-in</b> " + sysf("zz-remotix-monitor.conf") + " in "
        + c("$XDG_RUNTIME_DIR/systemd/user.control/<unit>.d/") + " replaces " + c("ExecStart") + " with "
        + c("gnome-shell --headless --no-x11") + " (plus " + c("--mode=%i") + " for the template), then "
        + c("daemon-reload") + ". No root needed, gone at reboot, and named " + c("zz-") + " so that it applies "
        "after any system drop-in. It is written in the instance directory, never the template's, which would "
        "also apply to GDM's shell.",
        "<b>The check</b>: REMOTIX re-reads the " + c("ExecStart") + " in force; if it lacks the expected "
        "arguments, or still contains " + c("--virtual-monitor") + " (an old drop-in in /etc/systemd/user), "
        "birth is refused and declared: the session would have its own monitor, the capture would add a "
        "second, and the user would watch an empty screen.",
        "<b>The previous session must be over</b>: both " + sysf("gnome-session-manager@<session>.service")
        + " and " + sysf("gnome-session-restart-dbus.service") + " inactive. A session started while GNOME "
        "restarts the session bus dies without writing anything (measured 16 Aug 2026).",
    ]) + \
    p("<b>The session dconf</b> (D-015, " + c("session_dconf_prepare()") + "). The child writes "
      + c("$XDG_RUNTIME_DIR/remotix/dconf/profile") + " (the profile) with an in-memory database " + c("service-db:shm/remotix")
      + " on top and the user's databases below, read-only, and sets " + c("DCONF_PROFILE") + " before any "
      "GSettings call; the session gets the same variable. Everything the remote session writes goes to "
      "memory and never to the user's settings, so nothing has to be restored after a crash. The database is "
      "emptied at each new birth. Prices, declared: what the user changes from the remote desktop (wallpaper, "
      "a shortcut) is lost when the session is reborn; a mandatory profile in "
      + c("/run/dconf/user/<uid>") + " wins over the variable, and then the cure cannot apply and is declared.") + \
    table(["Setting", "Value", "Written in", "Why"], [
        [c("org.gnome.mutter.wayland switch-to-session-1") + " … " + c("12"), "empty", "session dconf",
         "Headless Mutter swallows " + c("Ctrl+Alt+F1") + "…F12 for nothing"],
        [c("org.gnome.shell always-show-log-out"), "true", "session dconf", "The log-out entry is the only "
         "gesture that ends the session"],
        [c("org.gnome.desktop.lockdown disable-user-switching"), "true", "session dconf", "Only log-out stays "
         "in the menu, on every desktop"],
        [c("org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type") + ", "
         + c("…-battery-type"), c("nothing"), "user dconf", "No automatic suspend"],
        [c("org.gnome.desktop.session idle-delay"), "0", "user dconf", "No idle blanking"],
        [c("org.gnome.desktop.screensaver lock-enabled"), "false", "user dconf", "The lock is REMOTIX's, not "
         "the desktop's"],
        [c("org.gnome.desktop.input-sources"), "the negotiated layout", "session dconf (by "
         + c("input_layout()") + " in " + c("input.c") + ")",
         rif("Keyboard layout negotiation")],
    ], "«TAB» — GNOME settings, " + c("session_settings()")) + \
    p("The user decided on 25 Sep 2026 that the user's settings are not touched <b>except</b> those about "
      "lock screen, reboot, suspend and standby, which are dangerous for other users of the machine; those "
      "are written to the user's dconf writer (" + c("gnome_set_user()") + ") and then read back through "
      "the session profile, as the shell will read them. Every schema is looked up first: "
      + c("g_settings_new()") + " on a missing schema aborts the process. "
      + c("session_inhibit()") + " asks " + c("org.gnome.SessionManager.Inhibit") + " with flags "
      + c("SUSPEND | IDLE") + " (4 | 8 = 12; never " + c("LOGOUT") + "), and the cookie is never released: it lives "
      "as long as the session.")

KDE_FIG = fig(
    zone(20, 12, 560, 240, "KWin's user unit")
    + box(40, 44, 520, 50, "Plasma and the programs", "on KWin's socket, wayland-N", "light")
    + box(40, 116, 520, 50, "KWin, nested", "one full-screen window on labwc; it draws the pointer itself", "navy")
    + box(40, 188, 520, 50, "labwc, without a screen", "headless output W×H at 240 Hz; a 1×1 ticker every 16 ms", "grey")
    + arrow(300, 94, 300, 114, "#475569") + arrow(300, 166, 300, 186, "#475569")
    + zone(600, 12, 280, 240, "REMOTIX, the user's child")
    + box(620, 116, 240, 50, "capture", "zkde_screencast on KWin's output", "blue")
    + box(620, 188, 240, 50, "reattach", "zwlr_output_manager_v1 on labwc", "blue")
    + arrow(562, 141, 618, 141, "#0050C0", label="frames", lx=590, ly=130)
    + arrow(618, 213, 562, 213, "#0050C0", True, label="new size", lx=590, ly=202),
    900, 262, "«FIG» — KWin nested in a labwc nobody sees: the capture reads KWin, the reattach resizes labwc")

S5 = p("Plasma is started with " + c("startplasma-wayland") + ", which starts KWin as the user unit "
       + sysf("plasma-kwin_wayland.service") + "; REMOTIX overrides its " + c("ExecStart") + " the same way as "
       "GNOME's shell. The line does not start KWin directly: it starts the REMOTIX binary in "
       + c("--kwin-nested") + " mode, which starts a <b>labwc without a screen</b> and then becomes KWin, "
       "running as a window inside that labwc (" + c("DECISIONS.md") + " §10.40, 11 Oct 2026). The desktop is "
       "KWin's output; KWin's output follows the size of its window; the window follows labwc's output. "
       "To change the size of the desktop at a reattach, REMOTIX changes the size of labwc's output.",
       lead=True) + \
    code("""[Service]
ExecStart=
ExecStart=/usr/libexec/remotix/remotix --kwin-nested 1920 1080 /dev/dri/renderD128 -- /usr/bin/kwin_wayland_wrapper --xwayland --width 1920 --height 1080 --no-lockscreen""",
         "text", "The KWin drop-in (zz-remotix-monitor.conf), here for a 1920×1080 canvas") + \
    KDE_FIG + \
    table(["", "Why"], [
        ["Not " + c("kwin_wayland --virtual") + ", which REMOTIX used before 1.0.0",
         "KWin up to 6.7 cannot change the size of a " + c("--virtual") + " output and cannot create a second "
         "one: the virtual backend has no " + c("createVirtualOutput()") + " (read in KWin 6.3.6; measured, every "
         "size asked was answered «Could not find output»). The desktop kept the size it was born with, and a "
         "reattach from a smaller or larger window got a rescaled picture."],
        ["Not a restart of KWin at the new size", "Measured 10 Oct 2026: Firefox and a GTK editor died at the "
         "first restart. Only Qt programs survive a compositor restart."],
        ["A nested KWin", "KWin's Wayland backend resizes its output when its window is configured to a new size "
         "(" + c("wayland_output.cpp") + ", " + c("handleConfigure") + "). labwc's output is resized with "
         + c("zwlr_output_manager_v1") + ", the protocol REMOTIX already uses on XFCE and LXQt "
         "(" + rif("Output size on labwc") + "). No program is restarted."],
        ["One path for every KWin", "Nothing in the mechanism depends on KWin's version, 6.8 included. Tried on "
         "KWin 6.3.6 (Debian 13) and 6.4.2 (openSUSE Leap 16) with the functional suite; the resize alone on "
         "KWin 6.6.4 (Alma 10, in a container). Not tried: Ubuntu 26.04 (KWin 6.6) and Plasma 6.8."],
    ], "«TAB» — Why KWin runs inside labwc") + \
    p("<b>The start line</b> (" + c("kwin_nested_alive()") + " in " + c("kwin.c") + "). "
      + c("write_dropin()") + " writes it with the path of the running binary (" + c("/proc/self/exe") + ") and "
      "the canvas size, and picks the render node with the same two questions as for XFCE's labwc: the first "
      + c("renderD*") + " that opens, and that can create a buffer. If it cannot, the node is " + c("pixman")
      + " (labwc draws in memory) and that is declared; with no node at all it is " + c("-") + " and wlroots "
      "chooses. The helper then runs as the user, inside the unit:") + \
    steps([
        "It checks the line: " + c("W H NODE -- <wrapper> …") + ", with W and H between 200 and 8192; otherwise exit 2.",
        "<b>Which labwc.</b> A build-time choice of the package, not a runtime switch: built with "
        + c("make LABWC=/usr/lib/remotix/labwc") + " (the macro " + c("REMOTIX_LABWC") + ") it runs that exact "
        "file; otherwise it runs the " + c("labwc") + " found in " + c("PATH") + ". Only the RHEL / Alma 10 "
        "package is built with it (" + rif("Where KWin's labwc comes from") + ").",
        "If there is no labwc, the session is still born: the helper runs the KWin wrapper with "
        + c("--virtual") + " added and writes " + c("⛔ labwc is not installed: KWin --virtual, and the desktop "
        "will NOT take the window's size at reattach (DECLARED FALLBACK)") + " to the unit's journal.",
        "It writes labwc's configuration, " + c("$XDG_RUNTIME_DIR/remotix-kwin-host/labwc/rc.xml")
        + " (folder 0700), rewritten at every birth.",
        "It starts labwc as " + c("labwc -C <that folder>") + " with " + c("XDG_RUNTIME_DIR")
        + " set to " + c("$XDG_RUNTIME_DIR/remotix-kwin-host") + ", " + c("WAYLAND_DISPLAY") + ", "
        + c("WAYLAND_SOCKET") + " and " + c("DISPLAY") + " removed, " + c("WLR_BACKENDS=headless") + ", "
        + c("WLR_LIBINPUT_NO_DEVICES=1") + ", " + c("WLR_RENDER_DRM_DEVICE=<node>") + " or "
        + c("WLR_RENDERER=pixman") + ", and " + c("LABWC_UPDATE_ACTIVATION_ENV=0") + ". labwc's socket is "
        "then " + c("…/remotix-kwin-host/wayland-0") + ", and KWin's " + c("wayland-N") + " stays the only "
        "socket in the user's runtime folder: whatever looks for the session's socket there (capture, input, "
        "clipboard) cannot land on the host by mistake. With activation updates said off, labwc never "
        "publishes its own display to the bus or to systemd, where the session's programs would open on a "
        "screen nobody sees.",
        "It waits for labwc's socket for at most " + c("HOST_BIRTH_MS") + " = 10 s (about 0.1 s measured; "
        "22–23 ms on Alma 10), and stops if labwc exits first.",
        "labwc's headless output is born 1280×720; the helper sets it to W×H at 240 Hz and reads the size back "
        "<b>before</b> KWin opens its window, so the desktop is born at the right size.",
        "It starts the ticker (below), sets " + c("KWIN_FORCE_SW_CURSOR=1") + " and becomes the KWin wrapper "
        "with " + c("--wayland-display <labwc's socket>") + " added to its line.",
    ]) + \
    table(["Setting in " + c("rc.xml"), "Why"], [
        [c("-C") + " on the command line", "labwc reads only this folder: a user's " + c("~/.config/labwc")
         + " (an XFCE or LXQt user has one) and " + c("/etc/xdg/labwc") + " never get in. There is no "
         + c("autostart") + " and no menu file in it."],
        [c("<windowRule title=\"*\" serverDecoration=\"no\">") + " with " + c("ToggleFullscreen"),
         "The only window is KWin's, and its size must be the output's: that is the whole mechanism. Matched on "
         "the title: on Leap 16 (labwc 0.8.1, KWin 6.4.2) a rule on " + c("identifier=\"*\"") + " never fired, "
         "KWin's window stayed floating 2×28 px smaller than the output, and the capture fell back to copying in "
         "memory (38–48 fps). One rule only: the action toggles, two would undo each other."],
        [c("<decoration>client</decoration>") + ", " + c("<gap>0</gap>"), "No title bar from the very first "
         "configure: on Leap 16 KWin's window was first configured 3822×2036 on a 3824×2064 output, and a "
         "capture mounted in that instant asked for the wrong size."],
        ["One " + c("<keybind key=\"W-Return\">") + " and one Root " + c("<mousebind>") + ", each with the "
         "single action " + c("None"), "labwc keeps <b>zero</b> bindings (" + c("DECISIONS.md") + " §10.43). A "
         + c("rc.xml") + " without bindings makes labwc load its default ones, which start programs (Super+Return "
         "a terminal, the volume keys " + c("amixer") + "); nobody presses keys on this labwc, but any program "
         "of the same user could, through the virtual-keyboard protocol on its socket. labwc decides «defaults "
         "or not» on the bindings it has read (one each: no), and only afterwards removes every binding whose "
         "action list is empty; the same order in every labwc from 0.8.0 to 0.9.8. Measured on 0.8.3, 0.8.4 and "
         "0.9.8: Super+Return and Vol+ sent through the virtual keyboard start nothing. The key must be a valid "
         "keysym: with an unknown one labwc creates no binding and the defaults come back."],
    ], "«TAB» — The labwc configuration REMOTIX writes for KWin's host") + \
    table(["Trap of KWin inside labwc (measured 11 Oct 2026)", "Cure, in " + c("kwin.c")], [
        ["KWin froze a few seconds after birth, every window at its first image. KWin draws its next frame only "
         "after labwc says the previous one was presented; labwc answers only when it repaints, and a frame "
         "without damage does not make it repaint (614 frames, 612 answered).",
         "<b>The ticker</b>: a separate process puts a 1×1 transparent surface in labwc's overlay layer and "
         "damages it every " + c("TICKER_MS") + " = 16 ms, so labwc repaints one pixel and answers. It ends with "
         "labwc or with its parent."],
        ["The pointer's shape never changed in the page, and a full-screen Firefox froze: the nested output has "
         "a cursor layer, so KWin put the cursor on labwc's screen and handed full-screen windows to labwc as "
         "they were.", c("KWIN_FORCE_SW_CURSOR=1") + ": KWin draws the pointer into the image, as it did with "
         + c("--virtual") + "."],
        ["Frames lost: labwc presents on its own 60 Hz clock and the two clocks drift (60 fps animation at "
         "3824×2064: 59 fps with " + c("--virtual") + ", 52–55 nested).", "labwc's output at 240 Hz ("
         + c("HOST_MHZ") + "): 59 fps again. KWin keeps its own 60."],
        ["A full-screen window with the pointer hidden (a video, a kiosk) froze in the picture: KWin scanned it "
         "out to labwc directly, and the stream is built from the last frame KWin composited.",
         "<b>One transparent pixel on top</b>, inside KWin, on the capture's own connection: KWin never scans "
         "out a full-screen window with any window above it, so it composites as with " + c("--virtual") + "."],
        ["At birth labwc configures KWin's window more than once, and a capture asked in between offers a size "
         "KWin's stream no longer has.", c("kwin_host_settle()") + ": before mounting the capture the child "
         "waits (at most 3 s) until KWin's output has the host's size."],
    ], "«TAB» — Five traps of KWin inside labwc, found by measuring") + \
    steps([
        "<b>At a reattach of another size</b> (" + c("child.c") + ", " + c("§7.1") + "), if KWin's output is "
        "not the canvas asked for and the host exists, the child first dismantles the capture: KWin's stream "
        "would otherwise renegotiate to a size the fixed offer refuses, and die.",
        c("kwin_host_resize()") + " asks labwc's output for the new size (read back from labwc, not believed), "
        "then reads KWin's output on a connection of its own until it has the same size, for at most 3 s: KWin "
        "follows a few milliseconds later. Measured: 18–31 ms for the whole resize.",
        "The capture is mounted again at the new canvas, and from there the road is that of every desktop "
        "(encoder, pointer, the answer to the page).",
    ]) + \
    p("A reattach at the <b>same</b> size asks for nothing: the window and the output stay as they are "
      "(measured, three reattaches in a row). A Plasma session with no host — labwc missing, or a session "
      "born with KWin " + c("--virtual") + " — keeps the size it was born with, and the child declares it: "
      + c("⚠ §7.1 KDE: this Plasma session has no host for KWin … DECLARED FALLBACK") + ". The capture "
      "takes KWin's only output, " + c("WL-0") + " when nested (" + c("Virtual-0") + " with " + c("--virtual")
      + ").") + \
    table(["Window (canvas)", "fps " + c("--virtual") + " → nested", "Server latency, ms", "KWin, % of a core",
           "labwc, % of a core"], [
        ["1080p (1872×944)", "58 → 58", "15.3–15.6 → 12.5", "4.9–5.3 → 5.9–6.4", "2.4–2.6"],
        ["2K (2512×1296)", "58 → 58", "15.5–16.4 → 13.4–13.5", "6.7–6.8 → 6.9–8.1", "2.9–3.2"],
        ["3K (2832×1488)", "58 → 54–55", "17.9–18.1 → 18.7", "5.3–5.7 → 5.5–5.6", "2.5"],
        ["4K (3824×2064)", "58 → 44–49", "25.5 → 39.4–39.9", "4.7–4.8 → 4.4–4.7", "2.5–2.6"],
        ["Still desktop", "—", "—", "0 → 0", "0.5–1.5"],
    ], "«TAB» — The cost of the nesting, measured 11 Oct 2026 on an Intel UHD 770 (i5-13500T), openSUSE Leap 16, "
       "KWin 6.4.2, labwc 0.8.1, H.264 VA-API; a 60 fps animation in a Firefox window, two runs each") + \
    p("Up to 2K the nesting costs about 3 % of one core (labwc; the ticker 0.1–0.2 %) and nothing in frames or "
      "latency. At 3K it starts to lose frames, and at 4K on this integrated card it loses 9–14 fps and adds "
      "14 ms. The likely cause, not measured, is that labwc draws KWin's whole frame once more on the same "
      "card. On an AMD RX 6800 (Debian 13, KWin 6.3.6) the same 4K animation stays at 59 → 59 fps. "
      "«Latency» is the server's stretch from the compositor's frame to the bytes on the wire (median); the "
      "browser's decoding and display are not in it. Not measured on the Intel N100.") + \
    table(["Topic", "Behaviour", "Why"], [
        ["Session configuration", c("$XDG_RUNTIME_DIR/remotix/xdg") + " first in " + c("XDG_CONFIG_DIRS")
         + " (" + c("session_folder_kde()") + ")", "Valid for the remote session only, gone with it; the "
         "user at the monitor keeps their own"],
        [c("kdeglobals"), c("[KDE Action Restrictions][$i]") + ": " + c("lock_screen") + ", "
         + c("start_new_session") + ", " + c("switch_user") + " false", "KIOSK: no Lock, no Switch User; Log "
         "Out stays"],
        [c("kwinrc"), c("BorderSize=Normal") + ", " + c("BorderSizeAuto=false"), "In a remote session the "
         "border must be grabbed; Breeze's automatic border is too thin. The user may change it"],
        [c("ksmserverrc"), c("loginMode=emptySession"), "After log-out, whoever comes back does not find the "
         "previous programs reopened"],
        [c("kxkbrc"), "the negotiated layout, keys with " + c("[$i]"), rif("Keyboard layout negotiation")],
        ["Cursor theme", c("remotix-invisible") + ", written in " + c("$XDG_RUNTIME_DIR/remotix/icons"),
         "KWin draws the pointer inside the image; the theme's one-pixel shapes are coloured codes that tell "
         "the client which shape to draw (" + rif("Screen capture per compositor") + ")"],
        ["Power", "A thread waits for " + c("org.kde.Solid.PowerManagement") + " on the bus and calls "
         + c("PolicyAgent.AddInhibition") + " with types 4, again whenever powerdevil restarts",
         "Keeps the screen on and the session not idle; powerdevil may appear late"],
        ["Screen-cast permission", sysf("/usr/share/applications/org.kde.remotix.desktop") + ", shipped by the "
         "package and only <b>verified</b> by " + c("kwin_check_permission()") + ": the "
         "file exists (else " + c("RX-KDE-001") + "), its " + c("Exec") + " resolves to the running binary (else "
         + c("RX-KDE-002") + "), " + c("X-KDE-Wayland-Interfaces") + " lists " + c("zkde_screencast_unstable_v1")
         + " (else " + c("RX-KDE-003") + ")", "KWin compares " + c("/proc/<pid>/exe") + "; without the file the "
         "global does not appear. Until phase 16 the server wrote it as root; a program rewriting a packaged "
         "file creates two truths for " + c("dpkg -V") + " and " + c("rpm -V")],
    ], "«TAB» — How Plasma is kept") + \
    p("Alive means " + c("org.kde.KWin") + " owns its name on the session bus; the previous session is over "
      "when both " + sysf("plasma-kwin_wayland.service") + " and " + sysf("plasma-workspace.target")
      + " are inactive. labwc and the ticker are processes of the KWin unit and end with it. "
      + c("session_settings()") + " writes nothing else for Plasma: the desktop lock "
      "is off from the command line (" + c("--no-lockscreen") + ").")

S5B = p("labwc is needed on KDE only as KWin's host; it is not the desktop's compositor. Which one depends on the "
        "KWin of the distribution: from KWin 6.5 on it is <b>REMOTIX's own</b>, before that it is the distribution's.",
        lead=True) + \
    table(["Distribution", "KWin (28 Oct 2026)", "labwc for KDE", "How the package gets it"], [
        ["Debian 13", "6.3.6", "the distribution's", c("Recommends: labwc") + " (a " + c(".deb") + " cannot say "
         "«only if Plasma is there», so it is recommended to every machine)"],
        ["openSUSE Leap 16", "6.4.2", "the distribution's", c("Requires: (labwc if plasma6-workspace)")],
        ["Ubuntu 26.04", "6.6.6", "<b>REMOTIX's own</b>, " + c("/usr/lib/remotix/labwc"), "built inside the .deb (only on 26.04; "
         "older Ubuntu keeps the distribution's labwc)"],
        ["RHEL / Alma 10", "6.6.4", "<b>REMOTIX's own</b>", "built inside the .rpm"],
        ["Fedora 44", "6.7.5", "<b>REMOTIX's own</b>", "built inside the .rpm"],
        ["openSUSE Tumbleweed", "6.8.1", "<b>REMOTIX's own</b>", "built inside the .rpm"],
        ["Arch", "6.8.1", "<b>REMOTIX's own</b>", "built inside the package"],
    ], "«TAB» — Where KWin's labwc comes from") + \
    p("<b>Why REMOTIX builds its own</b> (1.5; " + c("packaging/labwc-ospite/") + "). KWin 6.5 and later paint a special "
      "black pixel as the root of their window and put the content in sub-surfaces. wlroots never reports that root as "
      "«presented», so KWin gives its clients a frame clock stuck at 0, Firefox believes its window is covered and stops "
      "painting: the windows of the remote desktop stay on their first frame. It is not a matter of the graphics card; it "
      "happens on every distribution with KWin 6.5 or later. The cure is a few lines in wlroots ("
      + "scene/surface.c of wlroots, in the " + c("frame_done") + " handler): the root surface of a shown surface counts as "
      "presented. Measured on a rented NVIDIA server on 28 Oct 2026: 3163 frames presented and 5 discarded, and the KDE suite "
      "went from 15 passed and 28 blocked to no blocked test (final package: Chrome 22 of 22, Firefox 21 of 22, the red one a "
      "limit of the test machine).") + \
    p("<b>What exactly is built.</b> One labwc <b>0.9.3</b> with one wlroots <b>0.19.2</b> plus our patch ("
      + c("wlroots-0.19.2-remotix-presented-root.patch") + "), wlroots linked <b>statically</b> into the labwc binary, installed as "
      + c("/usr/lib/remotix/labwc") + " and used <b>only</b> to host KWin (" + c("make LABWC=/usr/lib/remotix/labwc")
      + " → " + c("REMOTIX_LABWC") + " in " + c("kwin.c") + "; a build-time choice, not a switch). The same versions on the five "
      "distributions, so REMOTIX does not depend on the wlroots of each (0.18, 0.19, 0.20: different ABIs). XFCE and LXQt keep "
      "the labwc of the distribution. The sources and their sha256 are pinned in " + c("packaging/labwc-ospite/VERSIONS") + "; "
      + c("fetch.sh") + " downloads and checks them, " + c("build.sh") + " extracts, patches, builds with the minimum of options "
      "and installs. The same fix for wlroots 0.18, 0.19 and 0.20 is kept in " + c("patches-upstream/") + ", ready for the "
      "reports to the upstream projects. Licence and source: " + rif("KWin's own labwc") + ".") + \
    p("<b>What the 1.5 replaced.</b> Until the correction, RHEL / Alma 10 alone carried a labwc of its own: 0.8.4, unmodified, "
      "linked dynamically against EPEL's wlroots 0.18 (" + c("DECISIONS.md") + " §10.43, now marked as replaced). That recipe "
      "folder no longer exists; Alma now builds the same labwc as the others.") + \
    note("without labwc a Plasma session is still born, with KWin " + c("--virtual") + " and the size of its "
         "birth: a broken install (our labwc file missing) or a deb installed with "
         + c("--no-install-recommends") + ". It is declared in the unit's journal and in the child's log.",
         "Without labwc.") + \
    p("The capture side of the same KDE correction — frames with empty damage are no longer encoded — is in "
      + rif("Screen capture per compositor") + ".")

S8B = p("REMOTIX draws the desktop and encodes it on the <b>same card</b>, with no copy between cards. On a server with two or "
        "more cards (for example an Intel integrated one and a Radeon) the card is decided by the <b>BIOS</b>, not by the "
        "administrator (" + c("DECISIONS-11.md") + " §11.37, addendum of 27 Oct 2026, the user's decision). There is no option "
        "for it: to change the card, change the primary display in the BIOS.", lead=True) + \
    table(["Step", "Rule", "Why"], [
        ["1", "The <b>BIOS primary card</b> (" + c("boot_vga") + " = 1 in sysfs), if it is <b>capable</b>: it has a render node, "
         "the node opens and " + c("card_can_draw()") + " manages to create the drawing buffer", "On an ordinary machine it is the "
         "card the user already expects"],
        ["2", "Otherwise, among the capable cards, the one with the <b>lowest PCI address</b>", "The PCI address is the same "
         "after every reboot; the names " + c("renderD128") + " and " + c("renderD129") + " swap, so the old rule («the first "
         "node by name») could change card by itself"],
        ["3", "No capable card", "The declared software fallback (pixman)"],
    ], "«TAB» — How the desktop's card is chosen (" + c("card_pick()") + ", " + c("src/card_pick.c") + ")") + \
    table(["Desktop", "Who chooses the card", "Notes"], [
        ["XFCE, LXQt", "REMOTIX, with " + c("card_pick()"), "given to labwc with " + c("WLR_RENDER_DRM_DEVICE")],
        ["KDE Plasma", "REMOTIX, with " + c("card_pick()"), "the card of the labwc that hosts KWin"],
        ["GNOME", "GNOME itself (Mutter takes the BIOS primary card, Boot VGA)", "REMOTIX does not force it"],
        ["Encoder", "follows the desktop's card", c("--render-node") + " is unchanged: only the encoder's fallback, with a "
         "warning if it differs from the compositor's card"],
    ], "«TAB» — Who decides, per desktop") + \
    p("<b>A server with a service card.</b> Many servers carry a management card (ASPEED " + c("ast") + ", " + c("mgag200")
      + ", " + c("hibmc-drm") + ") that has no 3D. REMOTIX takes the capable card. GNOME may still choose the ASPEED, because it "
      "is the BIOS primary, and then it draws in software: when the compositor's card has a service driver the log carries "
      "<b>one warning per session</b> that names the desktop and says that it probably draws in software; the encoder goes to "
      "the compositor's card and, where that cannot encode, to the startup card (a copy between cards). The cure is to make the "
      "capable card the primary one in the BIOS. The behaviour does not change; the log tells.") + \
    p("<b>Where it is said.</b> One log line per session gives the node, the PCI address, the driver and why («BIOS primary card», "
      "«first capable card by PCI address; the BIOS primary … cannot draw: …», «… has no render node»), and the encoder's line "
      "(«the encoding card: node (PCI, driver) — from …») says where its choice came from. The installer lists the cards (node, "
      "PCI address, driver, BIOS primary) and says which one REMOTIX will use and why, in " + c("check") + " (" + c("desktop-card")
      + ") and in the plan — only on a machine with more than one card (" + c("installer/engine/desktop_card.go") + "). The "
      "installer cannot run " + c("card_can_draw()") + ": «capable» there means «has a render node»; the service's log has the "
      "last word. Unit test: " + c("benches/unit/card-pick") + " (fake " + c("/dev/dri") + " and sysfs: swapped names, ASPEED "
      "without node, no " + c("boot_vga") + ", primary that cannot draw, none capable, one card). Not settled yet: not yet run on a machine with two cards (§11.37); proved by the unit test only.")

S6 = p("XFCE on Wayland has no compositor of its own: it runs on labwc. There is no systemd unit to "
       "override, so " + c("write_dropin()") + " has nothing to do and REMOTIX starts the compositor itself.",
       lead=True) + \
    code("""exec labwc -m --session "sh -c 'u=$(wlr-randr | sed -n 1s/ .*//p);
    wlr-randr --output $u --custom-mode 1920x1080; exec xfce4-session'\"""",
         "bash", "The XFCE command line for a 1920×1080 canvas, simplified (the inner script is built by measured_primary())") + \
    table(["Topic", "Behaviour", "Why"], [
        [c("--session") + " (also in " + c("XFCE4_SESSION_COMPOSITOR") + ")", "Makes " + c("xfce4-session")
         + " labwc's primary client: when it exits, labwc exits. Both lines start from the "
         "same macro, " + c("SESSION_HEAD_XFCE") + " (" + c("labwc -m --session") + "), from which "
         + c("SESSION_LINE_XFCE") + " is built for the variable", "If " + c("xfce4-session") + " does not find both "
         + c("labwc") + " and " + c("--session") + " in that variable, at log-out it runs "
         + c("loginctl terminate-session ''") + " and kills REMOTIX's logind session"],
        [c("-m") + " (merge config)", "labwc reads " + c("rc.xml") + " from every XDG directory: ours (in "
         + c("$XDG_RUNTIME_DIR/remotix/labwc-xfce") + ", first in " + c("XDG_CONFIG_DIRS") + ") and the "
         "user's", "Without it the first " + c("rc.xml") + " found would hide the other; ours carries the "
         "bring-back-inside shortcut"],
        ["Session channel of xfconf", c("$XDG_RUNTIME_DIR/remotix/xdg-xfce/…/xfce4-session.xml") + " with "
         + c("WaylandLogoutCommand=/bin/true") + ", " + c("SessionName=REMOTIX") + ", "
         + c("SaveOnExit=false") + ", " + c("ShowSwitchUser=false") + "; " + sysf("xfconfd.service")
         + " gets " + c("XDG_CONFIG_DIRS") + " through the drop-in " + sysf("zz-remotix-session.conf")
         + " and is restarted, then the value in force is re-read", "D-017: what is not lock, reboot, suspend or "
         "standby stays in the session, not in the user's settings"],
        ["Power manager", c("dpms-enabled=false") + ", " + c("inactivity-on-ac=0") + ", "
         + c("inactivity-on-battery=0"), c("xfce4-power-manager") + " switches the output off after 10 minutes, "
         "and on wlroots that makes the capture fail"],
        ["Session", c("LockCommand=/bin/false") + ", " + c("ShowSuspend") + ", " + c("ShowHibernate") + ", "
         + c("ShowHybridSleep") + " false", "No lock (it is REMOTIX's), no suspend in the log-out dialog"],
        ["Panel action button", "A thread (" + c("xfce_panel_guard()") + ", started by "
         + c("session_inhibit()") + "; every 2 s for up to "
         "120 s) finds every " + c("actions") + " plugin and turns " + c("lock-screen") + ", "
         + c("switch-user") + ", " + c("suspend") + ", " + c("hibernate") + ", " + c("hybrid-sleep") + ", "
         + c("restart") + ", " + c("shutdown") + " from " + c("+") + " to " + c("-") + "; " + c("logout")
         + " stays", "XFCE has no KIOSK; a " + c("+") + " entry that is not permitted stays visible and grey, a "
         + c("-") + " entry is not created. The plugin has no number until the panel exists"],
        ["Inhibition", "None", c("xfce4-session") + " does not consult the inhibitor when it logs out: an "
         "inhibition would give a false sign in the log and no protection"],
    ], "«TAB» — How XFCE is kept") + \
    warn(c("xfconf-query") + " exits with 0 even when the daemon refused and restored the old value: the API "
         "is asynchronous and the local cache answers first. Every key REMOTIX writes ("
         + c("xfconf_put()") + ") is therefore read back, and only a read-back value counts as applied.",
         "A successful write is not an applied setting.") + \
    p("Alive means " + c("org.xfce.SessionManager") + " owns its name on the <b>user</b> bus (labwc is "
      "started without " + c("dbus-run-session") + "). The previous session is over when no " + c("labwc")
      + " process of the user is left, read from " + c("/proc") + " (" + c("my_processes()") + "): asked "
      "about a unit that does not exist, systemd would answer " + c("inactive") + ", and the guard would vanish "
      "instead of failing.")

S7 = p("Debian Trixie packages no launcher for LXQt on Wayland (no " + c("lxqt-wayland-session") + ", no "
       + c("startlxqtwayland") + "). REMOTIX writes the line itself, modelled on the upstream launcher 0.1.1 "
       "(labwc branch), with one deliberate difference: the labwc configuration directory is ours.", lead=True) + \
    code("""exec labwc -C "$XDG_RUNTIME_DIR/remotix/labwc-lxqt" -S "sh -c '...wlr-randr as for XFCE...; exec lxqt-session'\"""",
         "bash", "The LXQt command line, simplified") + \
    table(["Topic", "Behaviour", "Why"], [
        [c("-C <ours>"), c("rc.xml") + " with " + c("<decoration>server</decoration>") + ", labwc's default "
         "keybindings and the bring-back-inside shortcut; " + c("autostart") + " empty on purpose", "The "
         "upstream script copies once and for ever an " + c("autostart") + " that runs " + c("swayidle")
         + " and " + c("wlopm --off") + " after 5 minutes, switching off the captured output. With " + c("-C")
         + " labwc reads only that directory. If it cannot be written, the session is not started"],
        [c("-S") + " (" + c("--session") + ")", c("lxqt-session") + " is the primary client: labwc exits with it",
         "The logout trap of XFCE does not exist here: " + c("lxqt-session") + " never calls " + c("loginctl")],
        ["Idleness", c("enableIdlenessWatcher=false") + " and " + c("runCheckLevel=1") + " in the user's "
         "power configuration, read back", "Below level 1 the daemon turns the watcher back on"],
        ["Dangerous entries", c("lxqt-leave") + ", " + c("lxqt-lockscreen") + ", " + c("lxqt-suspend") + ", "
         + c("lxqt-hibernate") + ", " + c("lxqt-shutdown") + ", " + c("lxqt-reboot") + " hidden with "
         + c("Hidden=true") + " entries in the session's " + c("data-lxqt/applications") + " (first in "
         + c("XDG_DATA_DIRS") + "), read back; a user's own entry of the same name wins and is declared",
         "No lock, suspend, reboot or shutdown in the menu; log-out stays"],
        ["Panel menu", "The panel is started from " + c("$XDG_RUNTIME_DIR/remotix/xdg-lxqt/autostart/lxqt-panel.desktop")
         + " with " + c("--configfile") + " pointing to " + sysf("$XDG_RUNTIME_DIR/remotix/panel-lxqt.conf")
         + ": the user's panel configuration merged with the system files, with " + c("fancymenu")
         + " turned into " + c("mainmenu"), "D-018: fancymenu has a fixed Leave button; the panel rewrites the "
         "file it reads, so it must read a file of the session, not the user's (measured 25 Sep 2026)"],
        ["Lock command", c("lock_command_wayland=true") + " in the user's " + sysf("lxqt.conf")
         + " (and in " + sysf("session.conf") + " if a different value wins there), computed with liblxqt's "
         "precedence", "A safety net: an empty command leaves " + c("lxqt-leave") + " hanging, "
         + c("/bin/false") + " opens an error dialog. “Lock screen” then says done and locks nothing. "
         "The price, declared: two user files are written"],
        ["Inhibition", "None", "Idleness is switched off at its source"],
    ], "«TAB» — How LXQt is kept") + \
    p("Alive means " + c("org.lxqt.session") + " owns its name on the user bus; the name appears in the "
      "constructor, before the modules, so a " + c("lxqt-session") + " dying at start would be read as a user "
      "log-out (not measured). Log-out is " + c("org.lxqt.session.logout") + " on " + c("/LXQtSession") + ", sent "
      "without waiting for a reply (it is declared no-reply), then SIGTERM to labwc if the session is still "
      "there.") + \
    note("the test box for LXQt installs " + c("lxqt-core qt6-wayland lxqt-menu-data lxqt-powermanagement")
         + " plus " + c("kf6-breeze-icon-theme qt6-svg-plugins") + " (without them the panel has no icons and "
         "no menu button) and " + c("wlr-randr") + ", and excludes " + c("lxqt-branding-debian") + ", "
         + c("qlipper") + ", " + c("swayidle") + ", " + c("swaylock") + ", " + c("wlopm") + " and "
         + c("kanshi") + ". On a normal machine " + c("apt") + " pulls the recommended icon packages.",
         "The LXQt package set.")

LABWC_FIG = fig(
    zone(20, 12, 860, 150, "After every change of the output size, inside one keybinding of labwc")
    + box(36, 48, 196, 56, "1. no decoration", "give a temporary border", "blue")
    + box(248, 48, 196, 56, "2. bordered", "fit, centre pointer, place", "blue")
    + box(460, 48, 196, 56, "3. with title bar", "shade, as a mark", "light")
    + box(672, 48, 196, 56, "4. shaded", "unshade, fit, place, restore", "light")
    + text(450, 136, "maximised, tiled and full-screen windows are excluded: labwc resizes them itself", 11.5),
    900, 168, "«FIG» — The four passes of the bring-back-inside shortcut (SESSION_LABWC_KEYBOARD)")

S8 = p("On labwc the output size is not part of the birth: the headless output is born 1280×720, hard-wired "
       "(measured 20 Sep 2026), and no protocol creates one of a chosen size. REMOTIX resizes it as a "
       "Wayland client, twice.", lead=True) + \
    table(["When", "How", "Why"], [
        ["Before the desktop starts", "The primary client is " + c("sh -c") + " running " + c("wlr-randr --output <first> --custom-mode WxH")
         + " and then " + c("exec") + " of the session manager (" + c("measured_primary()") + "); joined with "
         + c(";") + " so that a failure still starts the desktop", "A race at birth: pcmanfm-qt computed the "
         "wallpaper from the old size and kept it. Measured 24 Sep 2026 at 1400×914: 1 bad wallpaper in 20 "
         "before, 0 in 20 after; 0 in 5 at 1920×1080 and at 3840×2160. " + c("wlr-randr") + " is therefore a "
         "dependency of the product on XFCE and LXQt"],
        ["When the capture starts on an output of another size, and at every " + c("capture_resize()"),
         c("wlr_ask_size()") + " with " + c("zwlr_output_manager_v1")
         + " (bound at version 4 at most) and a custom mode", "The canvas follows the browser window at attach and on "
         + c("FIT_CANVAS")],
    ], "«TAB» — Sizing the labwc output") + \
    p("<b>Bringing windows back inside</b> (D-007, measured 25 Sep 2026). When the output shrinks, labwc "
      "moves a floating window only if its centre leaves the screen; on the right and bottom edges large "
      "windows stay partly outside. No Wayland protocol lets a client move other clients' windows, and "
      "resizing in two steps does not help because labwc restores the pre-change position. The only labwc "
      "action that keeps a window inside on the right and bottom is the move-to-cursor placement; with the "
      "pointer warped to the window centre it means “move it as little as possible”. REMOTIX "
      "therefore writes into labwc's configuration a keybinding nobody uses, " + c("W-C-A-S-F12") + ", whose "
      "actions do it in four flat passes (labwc 0.8.3 does not nest " + c("ForEach") + "), and the child "
      "types it after each resize (" + rif("Virtual keyboard and pointer on labwc") + ").") + LABWC_FIG + \
    ul([
        "Full-screen windows have no query of their own: labwc does not change the decoration of a full-screen "
        "window and does not shade it, so only windows that did change are moved.",
        "Moves use the border only, never the title bar, or the window would drop by half a bar at every pass.",
        "All passes run inside one labwc action, so no frame shows the temporary border.",
        "Prices, declared and rare: a window the user had set to border-only comes back without border; a shaded "
        "one comes back unshaded. The pointer is put back where the user had it.",
        "labwc 0.8.3 marks " + c("MoveToCursor") + " deprecated; the configuration uses "
        + c("AutoPlace policy=\"cursor\"") + ", which calls the same function.",
    ])

S9 = p("Nobody may shut down, reboot, suspend or hibernate the server, the person sitting in front of it "
       "included (" + c("DECISIONS.md") + " §4.7, user decision of 15 Aug 2026): shutting down is the one gesture that takes "
       "away every session at once, and whoever does it from a desktop menu cannot see who is connected. "
       "Inside the remote desktop the user has a single gesture that ends something: log-out.", lead=True) + \
    table(["Entry", "GNOME", "KDE", "XFCE", "LXQt"], [
        ["Shut down, reboot", "hidden (polkit rule)", "hidden (polkit rule)", c("-shutdown") + ", "
         + c("-restart") + " in the panel; grey in the log-out dialog (rule)", "entries hidden; grey in "
         + c("lxqt-leave") + " (rule)"],
        ["Suspend, hibernate", "hidden (rule); no automatic suspend", "hidden (rule); powerdevil inhibited",
         "removed from panel and log-out dialog; inactivity 0", "entries hidden; idleness watcher off"],
        ["Lock screen", c("lock-enabled=false"), "KIOSK " + c("lock_screen") + ", " + c("--no-lockscreen"),
         c("LockCommand=/bin/false") + ", removed from panel", "entry hidden, command " + c("true")],
        ["Switch user", c("disable-user-switching"), "KIOSK " + c("switch_user") + ", " + c("start_new_session"),
         c("ShowSwitchUser=false") + ", removed from panel", "—"],
        ["Virtual consoles", c("Ctrl+Alt+F1") + "…F12 emptied", "—", "—", "—"],
        ["Log out", "always shown", "stays", "stays", "stays"],
    ], "«TAB» — What is removed from the session menus") + \
    p("<b>The polkit rule</b> (" + c("DECISIONS.md") + " §10.50, an exception to §10.36) is what removes power "
      "off, restart, suspend and hibernate on all four desktops with one mechanism: every desktop decides those "
      "entries from logind's " + c("Can*") + " answers, and the packages install "
      + c("/usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules") + " <b>active</b>, so for every user but "
      "root logind answers " + c("no") + " and the desktops hide the entries by themselves; "
      + c("systemctl poweroff") + " typed in a session terminal is refused too. It holds for local users as well: "
      "the machine is shared, and a REMOTIX session counts as active, so without the rule any connected user could "
      "power it off without a password. The rule returns " + c("polkit.Result.NO") + " for the twelve login1 "
      "actions, the " + c("*-multiple-sessions") + " and " + c("*-ignore-inhibit") + " variants included, which v1 "
      "had missed. Root keeps " + c("CAP_SYS_BOOT") + " and can still run " + c("sudo systemctl poweroff")
      + " (measured 15 Aug 2026: " + c("CanPowerOff") + " is " + c("no") + " for a user and " + c("yes")
      + " for root); attached clients are told with the farewell reason " + c("SERVER_CLOSING") + ". Removing the "
      "package removes the rule. The other two belts, the logind keys of " + sysf("remotix-power-keys.conf")
      + " (a physical key does not go through polkit) and the " + c("[Sleep]") + " section of "
      + sysf("remotix-no-suspend.conf") + ", stay inert in " + c("/usr/share/remotix/belts/") + ": the "
      "administrator's choice. Checked by " + c("benches/11-boxes/11-c25-no-power-entries.sh") + ". Details in "
      + rif("The power belts") + ".") + \
    note("XFCE's “Log Out” window always draws Restart and Shut Down (xfce4-session 4.20.2 "
         + "xfsm-logout-dialog.c:263-288, no key removes them): with the rule they are grey and "
         "refused, not gone. In " + c("lxqt-leave") + ", reached only by hand or from fancymenu's fixed Leave "
         "button when the user's own panel configuration wins, shut down, reboot and suspend are grey and "
         "“Lock screen” is clickable but inert. Both are declared residues.", "What is left visible.")

S10 = p(c("session_terminate()") + " ends the graphical session when the product must (for instance when the "
        "same user logs in locally, invariant I2: the local session wins, and two graphical sessions on one "
        + c("XDG_RUNTIME_DIR") + " would make the local one fail). It asks first and insists afterwards.",
        lead=True) + \
    table(["Desktop", "Ask", "Insist", "Over when"], [
        ["GNOME", c("org.gnome.SessionManager.Logout(1)") + " (no questions)", c("Logout(2)") + " (force), "
         "logged as a possible loss of unsaved work", "session manager unit and " + sysf("gnome-session-restart-dbus.service")
         + " inactive"],
        ["KDE", c("org.kde.Shutdown.logout"), c("StopUnit plasma-workspace.target fail"), "KWin unit and "
         "workspace target inactive"],
        ["XFCE", c("org.xfce.Session.Manager.Logout(false, false)"), "SIGTERM to every " + c("labwc") + " of "
         "the user", "no " + c("labwc") + " of the user left"],
        ["LXQt", c("org.lxqt.session.logout") + ", no reply expected", "SIGTERM to every " + c("labwc") + " of "
         "the user", "no " + c("labwc") + " of the user left"],
    ], "«TAB» — Ending a session") + \
    p("After each step REMOTIX waits up to " + c("WAIT_EXIT_MS") + " = 10 s, checking every 500 ms that the "
      "session is not alive <b>and</b> its units are " + c("inactive") + " (not merely “not active”: "
      + c("deactivating") + " is a trap), then runs " + c("systemctl --user reset-failed") + ". An application "
      "with unsaved changes may inhibit a polite log-out and show a dialog that nobody in an unattended session "
      "will close; that is why the second step exists.") + \
    p("<b>Tidying up after a session.</b> Once the session is dead, never while it lives:") + \
    ul([
        c("session_clear_out_scope()") + " closes what is left of the user's processes in "
        "REMOTIX's own " + c("session-N.scope") + " — SIGTERM, then SIGKILL to whatever is still there after 2 s — "
        "declared in the log.",
        c("session_clear_out_handler()") + " gives the user's systemd manager back as it "
        "was — after a session ends, and also at the next birth for what a crash left: it removes our "
        "drop-ins (the KWin and " + sysf("xfconfd.service") + " ones, and the shell instance ones found in the "
        "directory), reloads, restores with " + c("UnsetAndSetEnvironment") + " the values that "
        + c("session_snapshot_handler()") + " recorded at birth for the variables "
        "REMOTIX sets (" + c("OUR_VARIABLES") + "), and restarts " + sysf("xfconfd.service") + " if it had our directory. "
        "Without a photograph only values carrying the " + c("remotix") + " mark are removed, declared. If the "
        "child never comes back, the next child does it: the root server does not talk to a user manager.",
        "Everything else REMOTIX wrote for the session lives under " + c("$XDG_RUNTIME_DIR/remotix") + " (and, on "
        "KDE, KWin's labwc configuration and socket under " + c("$XDG_RUNTIME_DIR/remotix-kwin-host") + ") and is "
        "rewritten at every birth; the exceptions in the user's home are the GNOME and XFCE power and lock "
        "keys and LXQt's power and lock files, all of them in the categories the user allowed on 25 Sep 2026.",
    ])

S11 = p("Every place where the four desktops differ, in one table: the list to walk when a fifth desktop "
        "is added (the procedure is in " + rif("Extending REMOTIX") + ").", lead=True) + \
    table(["Concern", "Function", "File"], [
        ["Recognition", c("recognize_desktop()") + ", " + c("session_on_wlroots()"), c("session.c")],
        ["Environment", c("compose_environment()"), c("session.c")],
        ["Command line", c("start()") + ", " + c("measured_primary()"), c("session.c")],
        ["Unit override", c("write_dropin()") + ", " + c("unit_shell()"), c("session.c")],
        ["Alive, state", c("session_alive()") + ", " + c("session_state()"), c("session.c")],
        ["Previous session over", c("inactive_unit()"), c("session.c")],
        ["Settings and menus", c("session_settings()") + ", " + c("settings_lxqt()") + ", "
         + c("xfce_session_xfconf()"), c("session.c")],
        ["Inhibition and guards", c("session_inhibit()"), c("session.c")],
        ["Log-out", c("really_terminate()"), c("session.c")],
        ["KWin's host (KDE only)", c("kwin_nested_alive()") + ", " + c("kwin_host_resize()") + ", "
         + c("kwin_host_settle()") + "; the reattach branch in " + c("child.c"), c("kwin.c") + ", " + c("child.c")],
        ["Capture (the “open” functions)", c("mutter_open()") + ", " + c("kwin_open()") + ", " + c("wlr_open()"), c("mutter.c")
         + ", " + c("kwin.c") + ", " + c("wlroots.c")],
        ["Input", c("input_open()") + ", " + c("input_open_kwin()") + ", " + c("input_open_wlr()"), c("input.c")],
        ["Clipboard", c("clipboard_open()") + ", " + c("clipboard_open_kde()") + ", " + c("clipboard_open_wlroots()"),
         c("clipboard.c") + ", " + c("clipboard_kde.c")],
        ["Layout", c("input_layout()") + ", " + c("kwin_layout()") + ", "
         + c("wlr_input_keymap_from_name()"), c("input.c") + ", " + c("kwin.c") + ", " + c("wlr_input.c")],
    ], "«TAB» — Where the desktops branch") + \
    note(c("SPECS.md") + " §11.2 still lists XFCE and LXQt as “studied, not yet served”; the code serves "
         "both since phases 13 and 14 (September 2026). Cinnamon was studied on 9 Aug 2026 and is not served: "
         "upstream it has neither " + c("RecordVirtual") + ", nor libei, nor a clipboard path.",
         "Status of the desktops.")

CHAPTER = ("The four desktops", [
    ("Desktops at a glance", S1),
    ("Recognising the desktop", S2),
    ("The environment of a session", S3),
    ("GNOME sessions", S4),
    ("KDE Plasma sessions", S5),
    ("Where KWin's labwc comes from", S5B),
    ("XFCE sessions on labwc", S6),
    ("LXQt sessions on labwc", S7),
    ("Output size on labwc", S8),
    ("Servers with more than one graphics card", S8B),
    ("What is removed from the session menus", S9),
    ("Ending a session and tidying up", S10),
    ("Where the desktops branch", S11),
])
