from build import box, c, code, sysf, fig, note, p, rif, steps, table, text, ul, warn, zone


S1 = p("REMOTIX serves four Wayland desktops, which belong to three compositor families. Capture, input and "
       "clipboard talk to the <b>compositor</b>; birth, logout and settings talk to the <b>desktop</b>. XFCE "
       "and LXQt share labwc and therefore almost everything except the session.", lead=True) + \
    table(["", "GNOME", "KDE Plasma", "XFCE", "LXQt"], [
        ["Compositor", "Mutter (gnome-shell)", "KWin", "labwc (wlroots)", "labwc (wlroots)"],
        ["Recognised by", c("gnome-session"), c("startplasma-wayland"), c("xfce4-session"), c("lxqt-session")],
        ["Started by", "the distribution's GNOME session, through " + c("gnome-session"),
         c("startplasma-wayland"), c("labwc -m --session") + " + primary client",
         c("labwc -C <ours> -S") + " + primary client"],
        ["Monitor", "none of its own; the capture creates a virtual one", c("--virtual") + " output of the "
         "requested size, fixed for the session", "headless output born 1280×720, resized", "same as XFCE"],
        ["Capture", "ScreenCast " + c("RecordVirtual") + " (PipeWire)", c("zkde_screencast_unstable_v1")
         + " (PipeWire)", c("zwlr_screencopy_manager_v1"), "same as XFCE"],
        ["Input", c("libei") + " via " + c("ConnectToEIS"), c("libei") + " via " + c("connectToEIS"),
         "virtual keyboard and pointer", "same as XFCE"],
        ["Clipboard", c("appunti.c") + " (the clipboard, via RemoteDesktop)", c("appunti_kde.c") + " (data-control)",
         c("appunti_kde.c"), c("appunti_kde.c")],
        ["Alive when", c("DisplayConfig.GetCurrentState") + " answers", c("org.kde.KWin") + " on the bus",
         c("org.xfce.SessionManager") + " on the bus", c("org.lxqt.session") + " on the bus"],
        ["Logout", c("Logout(1)") + ", then " + c("Logout(2)"), c("org.kde.Shutdown.logout") + ", then "
         + c("StopUnit"), c("Logout(false,false)") + ", then SIGTERM to labwc", c("logout()")
         + " (no reply), then SIGTERM to labwc"],
    ], "«TAB» — The four desktops side by side") + \
    p("<b>One desktop per machine</b> (" + c("DECISIONI.md") + " §0.6, 20 Sep 2026; §4.6-duodetricies): REMOTIX looks for "
      "the desktop that is installed, it does not arbitrate between desktops that coexist, and the "
      + c("--compositore") + " (compositor) option of v1 is not coming back. Machines with several desktops are out of "
      "scope; when two are found the choice is made and declared “ambiguous”. Only Wayland sessions "
      "are served; X11 applications run through XWayland.") + \
    p("The four desktops were added one per phase (12 KDE, 13 XFCE, 14 LXQt) under the user's rule "
      "“add the new desktop without breaking what already works”: every desktop branch is placed "
      "<b>in front of</b> the GNOME code, which stays textually unchanged and is skipped with a "
      + c("return") + " or " + c("goto") + ".")

S2 = p(c("riconosci_desktop()") + " (recognise the desktop) decides once per process, from the programs in " + c("PATH") + ", and "
       "keeps the reason in words for the server's start line (" + c("sessione_desktop_spiega()") + ", “explain”).",
       lead=True) + \
    table(["Found", "Desktop", "Note"], [
        [c("startplasma-wayland") + " and not " + c("gnome-session"), "KDE", ""],
        ["both", "GNOME", "declared ambiguous"],
        [c("gnome-session"), "GNOME", ""],
        [c("xfce4-session"), "XFCE", "with " + c("lxqt-session") + " too: XFCE, declared ambiguous; without "
         + c("labwc") + ", declared that the session cannot be born"],
        [c("lxqt-session"), "LXQt", "without " + c("labwc") + ", declared"],
        ["none", c("SESSIONE_DESKTOP_NESSUNO") + " (none)", "No session is attempted"],
    ], "«TAB» — The recognition order") + \
    ul([
        "The XFCE marker is " + c("xfce4-session") + ", not " + c("labwc") + ": labwc is the family's "
        "compositor, shared with LXQt, and remains a precondition.",
        "Until phase 12 a machine with neither GNOME nor KDE was declared GNOME by fallback; on an XFCE box "
        "the failure surfaced as “another drop-in wins over mine” and “Mutter does not expose "
        "RemoteDesktop”, two innocents accused (measured 20 Sep 2026). The fallback was removed: "
        + c("NESSUNO") + " is honesty, not a desktop.",
        c("SessioneDesktop") + " travels as a " + c("uint32_t") + " between parent and child, so new values go "
        "at the end: GNOME 0, KDE 1, XFCE 2, none 3, LXQt 4.",
        "Capture, input, clipboard and stage rebuild ask " + c("sessione_su_wlroots()") + " (XFCE or LXQt), not "
        "“is it XFCE”: with five comparisons against XFCE, LXQt would have fallen silently into the "
        "GNOME/KDE branch.",
    ])

S3 = p("The environment of the session is <b>composed, not inherited</b> (" + c("componi_ambiente()")
       + ", “compose the environment”): whatever the starter carries ends up in the user's systemd manager and in D-Bus activation, "
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
        [c("XDG_DATA_DIRS"), "—", "—", "—", "our " + c("dati-lxqt") + " (session data) directory first"],
        [c("XCURSOR_THEME") + ", " + c("XCURSOR_SIZE") + ", " + c("XCURSOR_PATH"), "—",
         c("remotix-invisibile") + " (“invisible”), 24", c("remotix-invisibile") + ", 24", c("remotix-invisibile") + ", 24"],
        [c("WLR_BACKENDS") + ", " + c("WLR_LIBINPUT_NO_DEVICES"), "—", "—", c("headless") + ", 1",
         c("headless") + ", 1"],
        [c("WLR_RENDER_DRM_DEVICE") + " or " + c("WLR_RENDERER"), "—", "—", "the first openable "
         + c("renderD*") + " node, or " + c("pixman"), "same"],
        [c("LABWC_UPDATE_ACTIVATION_ENV"), "—", "—", "1", "1"],
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
    p("<b>Starting.</b> " + c("avvia()") + " (start) runs " + c("setsid --fork sh -c") + " with the composed "
      "environment and the user's home as working directory, with the session's output appended to "
      + c("~/.local/state/remotix/sessione.log") + " (the session log, under " + c("$XDG_STATE_HOME")
      + "; a directory and file that must belong to the user and "
      "not be writable by others, opened with " + c("O_NOFOLLOW") + "), or to "
      + c("$XDG_RUNTIME_DIR/remotix-sessione.log") + " as a declared fallback. Because of "
      + c("setsid --fork") + " the session lives outside the server's unit: measured on 29 Sep 2026, stopping "
      "the unit or killing the parent or the child kills no desktop on any of the four, and a reattach finds "
      "the same compositor and windows. The child does not wait for the birth: "
      + c("sessione_fai_nascere()") + " (bring the session to life) starts it only from a dead session and "
      "returns at once (at most one request a minute); the child's retry loop (1 s doubling to 30 s) finds the "
      "session on a later round. The 40 s wait " + c("ATTESA_AVVIO_MS") + " belongs to the blocking "
      + c("sessione_assicura()") + ", which the product no longer calls. The life cycle is in "
      + rif("Startup and life cycle") + ".")

S4 = p("GNOME is started through the distribution's own session, with a systemd drop-in that makes "
       "gnome-shell headless and without monitors: the only monitor is the virtual one that the capture "
       "creates with " + c("RecordVirtual") + ", and that is where GNOME puts its top bar and dock.",
       lead=True) + \
    steps([
        "<b>Which session</b> (D8, " + c("sessione_gnome()") + "): among " + c("wayland-sessions/*.desktop")
        + " entries that run " + c("gnome-session") + " with an installed " + c(".session") + " file, take the only one if "
        "there is just one, otherwise prefer the one named after the distribution (" + c("ID") + " of os-release, e.g. " + c("ubuntu") + "), then "
        + c("gnome") + ", then the first alphabetically, as GDM does; if none, " + c("gnome") + " as a declared "
        "fallback. The " + c("Exec") + " line is used as the command, " + c("DesktopNames")
        + " as " + c("XDG_CURRENT_DESKTOP") + ".",
        "<b>Which shell unit</b> (" + c("unita_shell()") + ", “shell unit”): up to GNOME 49 " + sysf("org.gnome.Shell@wayland.service")
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
    p("<b>The session dconf</b> (D-015, " + c("sessione_dconf_prepara()") + ", “prepare”). The child writes "
      + c("$XDG_RUNTIME_DIR/remotix/dconf/profilo") + " (the profile) with an in-memory database " + c("service-db:shm/remotix")
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
         + c("input_disposizione()") + ", “layout”, in " + c("input.c") + ")",
         rif("Keyboard layout negotiation")],
    ], "«TAB» — GNOME settings, " + c("sessione_impostazioni()") + " (session settings)") + \
    p("The user decided on 25 Sep 2026 that the user's settings are not touched <b>except</b> those about "
      "lock screen, reboot, suspend and standby, which are dangerous for other users of the machine; those "
      "are written to the user's dconf writer (" + c("gnome_metti_utente()") + ", “put in the user”) and then read back through "
      "the session profile, as the shell will read them. Every schema is looked up first: "
      + c("g_settings_new()") + " on a missing schema aborts the process. "
      + c("sessione_inibisci()") + " (inhibit) asks " + c("org.gnome.SessionManager.Inhibit") + " with flags "
      + c("SUSPEND | IDLE") + " (4 | 8 = 12; never " + c("LOGOUT") + "), and the cookie is never released: it lives "
      "as long as the session.")

S5 = p("Plasma is started with " + c("startplasma-wayland") + ", which starts KWin as the user unit "
       + sysf("plasma-kwin_wayland.service") + "; REMOTIX overrides its " + c("ExecStart") + " the same way as "
       "GNOME's shell.", lead=True) + \
    code("""[Service]
ExecStart=
ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual --width 1920 --height 1080 --no-lockscreen""",
         "text", "The KWin drop-in (zz-remotix-monitor.conf), here for a 1920×1080 canvas") + \
    table(["Topic", "Behaviour", "Why"], [
        ["Output size", "Given at birth with " + c("--virtual") + "; it does not change while the session "
         "lives. At a reattach of a different size the canvas keeps the old size and the browser rescales "
         "(" + c("DECISIONI.md") + " §8.6)", "KWin 6.3.6 of Debian stable, and no released branch up to 6.7.4, resizes a "
         "virtual output live; restarting KWin would destroy the session"],
        ["Session configuration", c("$XDG_RUNTIME_DIR/remotix/xdg") + " first in " + c("XDG_CONFIG_DIRS")
         + " (" + c("sessione_cartella_kde()") + ", “KDE folder”)", "Valid for the remote session only, gone with it; the "
         "user at the monitor keeps their own"],
        [c("kdeglobals"), c("[KDE Action Restrictions][$i]") + ": " + c("lock_screen") + ", "
         + c("start_new_session") + ", " + c("switch_user") + " false", "KIOSK: no Lock, no Switch User; Log "
         "Out stays"],
        [c("kwinrc"), c("BorderSize=Normal") + ", " + c("BorderSizeAuto=false"), "In a remote session the "
         "border must be grabbed; Breeze's automatic border is too thin. The user may change it"],
        [c("ksmserverrc"), c("loginMode=emptySession"), "After log-out, whoever comes back does not find the "
         "previous programs reopened"],
        [c("kxkbrc"), "the negotiated layout, keys with " + c("[$i]"), rif("Keyboard layout negotiation")],
        ["Cursor theme", c("remotix-invisibile") + ", written in " + c("$XDG_RUNTIME_DIR/remotix/icons"),
         "KWin draws the pointer inside the image; the theme's one-pixel shapes are coloured codes that tell "
         "the client which shape to draw (" + rif("Screen capture per compositor") + ")"],
        ["Power", "A thread waits for " + c("org.kde.Solid.PowerManagement") + " on the bus and calls "
         + c("PolicyAgent.AddInhibition") + " with types 4, again whenever powerdevil restarts",
         "Keeps the screen on and the session not idle; powerdevil may appear late"],
        ["Screen-cast permission", sysf("/usr/share/applications/org.kde.remotix.desktop") + ", shipped by the "
         "package and only <b>verified</b> by " + c("kwin_verifica_permesso()") + " (verify the permission): the "
         "file exists (else " + c("RX-KDE-001") + "), its " + c("Exec") + " resolves to the running binary (else "
         + c("RX-KDE-002") + "), " + c("X-KDE-Wayland-Interfaces") + " lists " + c("zkde_screencast_unstable_v1")
         + " (else " + c("RX-KDE-003") + ")", "KWin compares " + c("/proc/<pid>/exe") + "; without the file the "
         "global does not appear. Until phase 16 the server wrote it as root; a program rewriting a packaged "
         "file creates two truths for " + c("dpkg -V") + " and " + c("rpm -V")],
    ], "«TAB» — How Plasma is kept") + \
    p("Alive means " + c("org.kde.KWin") + " owns its name on the session bus; the previous session is over "
      "when both " + sysf("plasma-kwin_wayland.service") + " and " + sysf("plasma-workspace.target")
      + " are inactive. " + c("sessione_impostazioni()") + " writes nothing else for Plasma: the desktop lock "
      "is off from the command line (" + c("--no-lockscreen") + ").")

S6 = p("XFCE on Wayland has no compositor of its own: it runs on labwc. There is no systemd unit to "
       "override, so " + c("scrivi_dropin()") + " (write the drop-in) has nothing to do and REMOTIX starts the compositor itself.",
       lead=True) + \
    code("""exec labwc -m --session "sh -c 'u=$(wlr-randr | sed -n 1s/ .*//p);
    wlr-randr --output $u --custom-mode 1920x1080; exec xfce4-session'\"""",
         "bash", "The XFCE command line for a 1920×1080 canvas, simplified (the inner script is built by primario_misurato(), “sized primary client”)") + \
    table(["Topic", "Behaviour", "Why"], [
        [c("--session") + " (also in " + c("XFCE4_SESSION_COMPOSITOR") + ")", "Makes " + c("xfce4-session")
         + " labwc's primary client: when it exits, labwc exits. Both lines start from the "
         "same macro, " + c("SESSIONE_TESTA_XFCE") + " (the head, " + c("labwc -m --session") + "), from which "
         + c("SESSIONE_RIGA_XFCE") + " (the line) is built for the variable", "If " + c("xfce4-session") + " does not find both "
         + c("labwc") + " and " + c("--session") + " in that variable, at log-out it runs "
         + c("loginctl terminate-session ''") + " and kills REMOTIX's logind session"],
        [c("-m") + " (merge config)", "labwc reads " + c("rc.xml") + " from every XDG directory: ours (in "
         + c("$XDG_RUNTIME_DIR/remotix/labwc-xfce") + ", first in " + c("XDG_CONFIG_DIRS") + ") and the "
         "user's", "Without it the first " + c("rc.xml") + " found would hide the other; ours carries the "
         "bring-back-inside shortcut"],
        ["Session channel of xfconf", c("$XDG_RUNTIME_DIR/remotix/xdg-xfce/…/xfce4-session.xml") + " with "
         + c("WaylandLogoutCommand=/bin/true") + ", " + c("SessionName=REMOTIX") + ", "
         + c("SaveOnExit=false") + ", " + c("ShowSwitchUser=false") + "; " + sysf("xfconfd.service")
         + " gets " + c("XDG_CONFIG_DIRS") + " through the drop-in " + sysf("zz-remotix-sessione.conf")
         + " and is restarted, then the value in force is re-read", "D-017: what is not lock, reboot, suspend or "
         "standby stays in the session, not in the user's settings"],
        ["Power manager", c("dpms-enabled=false") + ", " + c("inactivity-on-ac=0") + ", "
         + c("inactivity-on-battery=0"), c("xfce4-power-manager") + " switches the output off after 10 minutes, "
         "and on wlroots that makes the capture fail"],
        ["Session", c("LockCommand=/bin/false") + ", " + c("ShowSuspend") + ", " + c("ShowHibernate") + ", "
         + c("ShowHybridSleep") + " false", "No lock (it is REMOTIX's), no suspend in the log-out dialog"],
        ["Panel action button", "A thread (" + c("guardia_del_pannello_xfce()") + ", the panel guard, started by "
         + c("sessione_inibisci()") + "; every 2 s for up to "
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
         + c("xfconf_metti()") + ", “set in xfconf”) is therefore read back, and only a read-back value counts as applied.",
         "A successful write is not an applied setting.") + \
    p("Alive means " + c("org.xfce.SessionManager") + " owns its name on the <b>user</b> bus (labwc is "
      "started without " + c("dbus-run-session") + "). The previous session is over when no " + c("labwc")
      + " process of the user is left, read from " + c("/proc") + " (" + c("processi_miei()") + ", “my processes”): asked "
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
         + c("Hidden=true") + " entries in the session's " + c("dati-lxqt/applications") + " (first in "
         + c("XDG_DATA_DIRS") + "), read back; a user's own entry of the same name wins and is declared",
         "No lock, suspend, reboot or shutdown in the menu; log-out stays"],
        ["Panel menu", "The panel is started from " + c("$XDG_RUNTIME_DIR/remotix/xdg-lxqt/autostart/lxqt-panel.desktop")
         + " with " + c("--configfile") + " pointing to " + sysf("$XDG_RUNTIME_DIR/remotix/lxqt-pannello.conf")
         + " (panel): the user's panel configuration merged with the system files, with " + c("fancymenu")
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
    900, 168, "«FIG» — The four passes of the bring-back-inside shortcut (SESSIONE_LABWC_TASTIERA, the keyboard section)")

S8 = p("On labwc the output size is not part of the birth: the headless output is born 1280×720, hard-wired "
       "(measured 20 Sep 2026), and no protocol creates one of a chosen size. REMOTIX resizes it as a "
       "Wayland client, twice.", lead=True) + \
    table(["When", "How", "Why"], [
        ["Before the desktop starts", "The primary client is " + c("sh -c") + " running " + c("wlr-randr --output <first> --custom-mode WxH")
         + " and then " + c("exec") + " of the session manager (" + c("primario_misurato()") + "); joined with "
         + c(";") + " so that a failure still starts the desktop", "A race at birth: pcmanfm-qt computed the "
         "wallpaper from the old size and kept it. Measured 24 Sep 2026 at 1400×914: 1 bad wallpaper in 20 "
         "before, 0 in 20 after; 0 in 5 at 1920×1080 and at 3840×2160. " + c("wlr-randr") + " is therefore a "
         "dependency of the product on XFCE and LXQt"],
        ["When the capture starts on an output of another size, and at every " + c("cattura_ridimensiona()")
         + " (resize the capture)", c("wlr_misura_chiedi()") + " (ask for a size) with " + c("zwlr_output_manager_v1")
         + " (bound at version 4 at most) and a custom mode", "The canvas follows the browser window at attach and on "
         + c("ADATTA_TELA")],
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
       "included (" + c("DECISIONI.md") + " §4.7, user decision of 15 Aug 2026): shutting down is the one gesture that takes "
       "away every session at once, and whoever does it from a desktop menu cannot see who is connected. "
       "Inside the remote desktop the user has a single gesture that ends something: log-out.", lead=True) + \
    table(["Entry", "GNOME", "KDE", "XFCE", "LXQt"], [
        ["Shut down, reboot", "refused by polkit", "refused by polkit", c("-shutdown") + ", " + c("-restart")
         + " in the panel; grey in dialogs (polkit)", "entries hidden; grey in " + c("lxqt-leave") + " (polkit)"],
        ["Suspend, hibernate", "no automatic suspend; refused by polkit and " + sysf("sleep.conf"),
         "powerdevil inhibited; refused", "removed from panel and log-out dialog; inactivity 0",
         "entries hidden; idleness watcher off"],
        ["Lock screen", c("lock-enabled=false"), "KIOSK " + c("lock_screen") + ", " + c("--no-lockscreen"),
         c("LockCommand=/bin/false") + ", removed from panel", "entry hidden, command " + c("true")],
        ["Switch user", c("disable-user-switching"), "KIOSK " + c("switch_user") + ", " + c("start_new_session"),
         c("ShowSwitchUser=false") + ", removed from panel", "—"],
        ["Virtual consoles", c("Ctrl+Alt+F1") + "…F12 emptied", "—", "—", "—"],
        ["Log out", "always shown", "stays", "stays", "stays"],
    ], "«TAB» — What is removed from the session menus") + \
    p("The menu work is cosmetic on top of three system-wide belts, which the package ships <b>inert</b> under "
      + c("/usr/share/remotix/cinture/") + " (the belts), where nothing reads them; since " + c("DECISIONI.md")
      + " §10.36 the installer no longer puts them in force, so the “refused by polkit” entries above hold only "
      "where the administrator has installed them. They are: a polkit rule (" + c("remotix-niente-spegnimento.rules")
      + ", “no power-off”, shipped as " + c("50-remotix-niente-spegnimento.rules") + ") that says "
      "no to every power action of logind, including the " + c("*-multiple-sessions") + " and "
      + c("*-ignore-inhibit") + " variants that v1 had missed; the logind keys of " + c("remotix-tasti.conf")
      + " (“keys”: " + c("HandlePowerKey") + ", suspend, hibernate, reboot and lid switch, with their long-press "
      "variants, all " + c("ignore") + "), because a physical key does not go through polkit; and the "
      + c("[Sleep]") + " section of " + c("remotix-niente-sospensione.conf") + " (“no suspend”). Root keeps "
      + c("CAP_SYS_BOOT") + " and can still run " + c("systemctl poweroff") + " (measured 15 Aug 2026: "
      + c("CanPowerOff") + " is " + c("no") + " for a user and " + c("yes") + " for root); attached clients are "
      "told with the farewell reason " + c("SERVER_IN_CHIUSURA") + " (server closing). Details in "
      + rif("The power belts, shipped inert") + ".") + \
    note("in " + c("lxqt-leave") + ", reached from fancymenu's fixed Leave button when the user's own panel "
         "configuration wins, shut down, reboot and suspend are grey and “Lock screen” is clickable "
         "but inert. On XFCE the separate “Log Out” window keeps grey entries. Both are declared "
         "residues.", "What is left visible.")

S10 = p(c("sessione_termina()") + " (end the session) ends the graphical session when the product must (for instance when the "
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
    p("After each step REMOTIX waits up to " + c("ATTESA_USCITA_MS") + " (exit wait) = 10 s, checking every 500 ms that the "
      "session is not alive <b>and</b> its units are " + c("inactive") + " (not merely “not active”: "
      + c("deactivating") + " is a trap), then runs " + c("systemctl --user reset-failed") + ". An application "
      "with unsaved changes may inhibit a polite log-out and show a dialog that nobody in an unattended session "
      "will close; that is why the second step exists.") + \
    p("<b>Tidying up after a session.</b> Once the session is dead, never while it lives:") + \
    ul([
        c("sessione_sgombera_scope()") + " (clear the scope) closes what is left of the user's processes in "
        "REMOTIX's own " + c("session-N.scope") + " — SIGTERM, then SIGKILL to whatever is still there after 2 s — "
        "declared in the log.",
        c("sessione_sgombera_gestore()") + " (clear the manager) gives the user's systemd manager back as it "
        "was — after a session ends, and also at the next birth for what a crash left: it removes our "
        "drop-ins (the KWin and " + sysf("xfconfd.service") + " ones, and the shell instance ones found in the "
        "directory), reloads, restores with " + c("UnsetAndSetEnvironment") + " the values that "
        + c("sessione_fotografa_gestore()") + " (photograph the manager) recorded at birth for the variables "
        "REMOTIX sets (" + c("VARIABILI_NOSTRE") + ", “our variables”), and restarts " + sysf("xfconfd.service") + " if it had our directory. "
        "Without a photograph only values carrying the " + c("remotix") + " mark are removed, declared. If the "
        "child never comes back, the next child does it: the root server does not talk to a user manager.",
        "Everything else REMOTIX wrote for the session lives under " + c("$XDG_RUNTIME_DIR/remotix") + " and is "
        "rewritten at every birth; the exceptions in the user's home are the GNOME and XFCE power and lock "
        "keys and LXQt's power and lock files, all of them in the categories the user allowed on 25 Sep 2026.",
    ])

S11 = p("Every place where the four desktops differ, in one table: the list to walk when a fifth desktop "
        "is added (the procedure is in " + rif("Extending REMOTIX") + ").", lead=True) + \
    table(["Concern", "Function", "File"], [
        ["Recognition", c("riconosci_desktop()") + ", " + c("sessione_su_wlroots()"), c("sessione.c")],
        ["Environment", c("componi_ambiente()"), c("sessione.c")],
        ["Command line", c("avvia()") + ", " + c("primario_misurato()"), c("sessione.c")],
        ["Unit override", c("scrivi_dropin()") + ", " + c("unita_shell()"), c("sessione.c")],
        ["Alive, state", c("sessione_viva()") + " (alive), " + c("sessione_stato()") + " (state)", c("sessione.c")],
        ["Previous session over", c("unita_inattiva()") + " (units inactive)", c("sessione.c")],
        ["Settings and menus", c("sessione_impostazioni()") + ", " + c("impostazioni_lxqt()") + ", "
         + c("xfce_xfconf_di_sessione()") + " (the session's xfconf)", c("sessione.c")],
        ["Inhibition and guards", c("sessione_inibisci()"), c("sessione.c")],
        ["Log-out", c("termina_davvero()") + " (really end)", c("sessione.c")],
        ["Capture (the “open” functions)", c("mutter_apri()") + ", " + c("kwin_apri()") + ", " + c("wlr_apri()"), c("mutter.c")
         + ", " + c("kwin.c") + ", " + c("wlroots.c")],
        ["Input", c("input_apri()") + ", " + c("input_apri_kwin()") + ", " + c("input_apri_wlr()"), c("input.c")],
        ["Clipboard", c("appunti_apri()") + ", " + c("appunti_apri_kde()") + ", " + c("appunti_apri_wlroots()"),
         c("appunti.c") + ", " + c("appunti_kde.c")],
        ["Layout", c("input_disposizione()") + ", " + c("kwin_disposizione()") + ", "
         + c("wlr_input_keymap_da_nome()") + " (keymap from a name)", c("input.c") + ", " + c("kwin.c") + ", " + c("wlr_input.c")],
    ], "«TAB» — Where the desktops branch") + \
    note(c("SPECIFICHE.md") + " §11.2 still lists XFCE and LXQt as “studied, not yet served”; the code serves "
         "both since phases 13 and 14 (September 2026). Cinnamon was studied on 9 Aug 2026 and is not served: "
         "upstream it has neither " + c("RecordVirtual") + ", nor libei, nor a clipboard path.",
         "Status of the desktops.")

CHAPTER = ("The four desktops", [
    ("Desktops at a glance", S1),
    ("Recognising the desktop", S2),
    ("The environment of a session", S3),
    ("GNOME sessions", S4),
    ("KDE Plasma sessions", S5),
    ("XFCE sessions on labwc", S6),
    ("LXQt sessions on labwc", S7),
    ("Output size on labwc", S8),
    ("What is removed from the session menus", S9),
    ("Ending a session and tidying up", S10),
    ("Where the desktops branch", S11),
])
