from build import arrow, box, c, code, fig, flow, h4, note, p, rif, steps, sysf, table, tip, ul, warn, zone

# ═════════════════════════════════════════════════════════════════════════
# 1. The four desktops side by side
# ═════════════════════════════════════════════════════════════════════════
S1 = p("REMOTIX serves four Wayland desktops that belong to three compositor families. Capture, input and clipboard "
       "talk to the <b>compositor</b>; birth, logout and settings talk to the <b>desktop</b>. XFCE and LXQt share "
       "labwc and therefore almost everything except the session. On KDE labwc is also present, but only as an "
       "invisible host for KWin, not as the desktop's compositor. Only Wayland sessions are served; X11 "
       "applications run through XWayland.", lead=True) + \
    table(["", "GNOME", "KDE Plasma", "XFCE", "LXQt"], [
        ["Compositor", "Mutter (inside " + c("gnome-shell") + ")", "KWin, nested in a labwc", "labwc (wlroots)",
         "labwc (wlroots)"],
        ["Recognised by", c("gnome-session") + " and " + c("gnome-shell"), c("startplasma-wayland"), c("xfce4-session"),
         c("lxqt-session")],
        ["Started by", "the machine's GNOME session (" + c("gnome-session") + "), with the Shell unit overridden by a "
         "drop-in", c("startplasma-wayland") + "; KWin's unit overridden to run " + c("remotix --kwin-nested"),
         c("labwc -m --session") + " with " + c("xfce4-session") + " as its primary client",
         c("labwc -C <ours> -S") + " with " + c("lxqt-session") + " as its primary client"],
        ["Monitor", "none of its own: the capture creates a virtual monitor with " + c("RecordVirtual"),
         "KWin's single output, nested in a labwc without a screen", "labwc's headless output, born 1280×720 and "
         "resized", "same as XFCE"],
        ["Capture", "ScreenCast on PipeWire (" + c("mutter.c") + ")", c("zkde_screencast_unstable_v1") + " on PipeWire ("
         + c("kwin.c") + ")", c("zwlr_screencopy_manager_v1") + " (" + c("wlroots.c") + ")", "same as XFCE"],
        ["Input", c("libei") + " through " + c("ConnectToEIS") + " (" + c("input.c") + ")", c("libei") + " through KWin's "
         + c("connectToEIS"), "virtual keyboard and virtual pointer (" + c("wlr_input.c") + ")", "same as XFCE"],
        ["Clipboard", "RemoteDesktop session of Mutter (" + c("clipboard.c") + ")", "wlroots data-control protocol "
         "(" + c("clipboard_kde.c") + ")", "same protocol, on labwc", "same as XFCE"],
        ["Pointer shape", "Mutter's cursor metadata (" + c("cursor.c") + ")", "KWin's cursor metadata, colour-coded "
         "theme (" + c("shape.c") + ")", "colour-coded theme, read back from the image (" + c("wlroots.c") + ")", "same as XFCE"],
        ["«Alive» means", c("DisplayConfig.GetCurrentState") + " answers", c("org.kde.KWin") + " owns its bus name",
         c("org.xfce.SessionManager") + " owns its bus name", c("org.lxqt.session") + " owns its bus name"],
        ["Log Out", c("Logout(1)") + ", then " + c("Logout(2)"), c("org.kde.Shutdown.logout") + ", then "
         + c("StopUnit") + " of " + c("graphical-session.target"), c("org.xfce.Session.Manager.Logout") + ", then SIGTERM to labwc",
         c("logout()") + " without waiting for a reply, then SIGTERM to labwc"],
    ], "«TAB» — The four desktops side by side") + \
    p("<b>Versions.</b> The facts read on the four Debian 13 test containers on 17 Nov 2026 are recorded in "
      + c("docs/PULIZIA-tranche1.md") + ": GNOME Shell 48.7, KWin 6.3.6 and labwc 0.8.3. The same file records that "
      "the user unit is " + sysf("org.gnome.Shell@wayland.service") + " as a real file, and that trixie's "
      "gnome-session offers the sessions " + c("gnome") + ", " + c("gnome-login") + " and " + c("gnome-dummy") + ". No "
      "version of XFCE or LXQt is recorded in the repository for trixie; comments in " + c("session.c") + " name "
      "components in the 4.20 series for XFCE (xfce4-session 4.20.2) and the 2.1 series for LXQt (lxqt-session 2.1.1, "
      "lxqt-panel 2.1.4, pcmanfm-qt 2.1.0), but those were read from sources or measured on other occasions and "
      "are not re-verified here. " + c("docs/DECISIONS-11.md") + " §11.8 names GNOME 46, KDE Plasma 6.1, XFCE 4.20 and "
      "LXQt 2.0 as minimums, but that ruling is about the website of the earlier multi-distribution product and takes "
      "the numbers from its installer catalogue, which this tree does not have: nothing in this code or package checks "
      "a minimum version.") + \
    p("<b>One desktop per machine.</b> REMOTIX looks for the desktop that is installed; it does not arbitrate between "
      "desktops that coexist (" + c("DECISIONS.md") + " §0.6). When two are found the choice is made and declared "
      "«ambiguous» (" + rif("How the desktop is recognised") + "). The package installs no desktop; with none of the "
      "four the server says so at startup (" + c("debian/control") + ").") + \
    p("<b>Whose settings these are</b> (" + c("DECISIONS.md") + " §8.2-bis, the rule of 13 Nov 2026). From the remote "
      "desktop the user may customise the desktop (look, themes, shortcuts, panels) and the changes stay, as they do "
      "locally. The user can never suspend, reboot, power off or lock the server. REMOTIX imposes its rules <b>only "
      "inside the remote session</b> and writes nothing permanent in the user's settings: at the monitor the user finds "
      "everything as it was. The ban on suspend, reboot and power-off is the polkit rule of the package ("
      + rif("Security model") + ", " + rif("The package") + "); what the session imposes on the desktop's own settings "
      "is a belt that hides buttons and avoids false notices. Two exceptions remain in the code and are described "
      "below: a one-time restore of values written by earlier REMOTIX versions, and on XFCE the copy and restore of a "
      "few locked keys (" + rif("What the session imposes, desktop by desktop") + ").")

# ═════════════════════════════════════════════════════════════════════════
# 2. Recognition
# ═════════════════════════════════════════════════════════════════════════
S2 = p(c("recognize_desktop()") + " in " + c("session.c") + " decides once per process, from the programs found in "
       + c("PATH") + ", and keeps the reason in words for the server's start line (" + c("session_desktop_explain()")
       + "). Parent and child both call it and must reach the same answer; they do, because both run on the same machine "
       "and read the same files.", lead=True) + \
    table(["Found", "Desktop", "Note"], [
        [c("startplasma-wayland") + " and not GNOME", "KDE", ""],
        ["both KDE and GNOME", "GNOME", "declared «ambiguous»"],
        [c("gnome-session") + " <b>and</b> " + c("gnome-shell"), "GNOME", c("gnome-session") + " alone is not GNOME: "
         "other desktops pull it in as a dependency"],
        [c("xfce4-session"), "XFCE", "together with " + c("lxqt-session") + ": XFCE, declared ambiguous. Without "
         + c("labwc") + " the start line says that the session cannot be born"],
        [c("lxqt-session"), "LXQt", "without " + c("labwc") + ", declared"],
        ["none", c("SESSION_DESKTOP_NONE"), "No session is attempted; " + c("session_spawn()") + " says why and returns"],
    ], "«TAB» — The recognition order") + \
    ul([
        "<b>Machines with two or more desktops installed.</b> The programs alone do not say which is the machine's. "
        "When more than one is present, " + c("declared_desktop()") + " reads the configuration of the machine's active "
        "display manager: lightdm's " + c("user-session") + " (directories read in lightdm's own order, then "
        + sysf("/etc/lightdm/lightdm.conf") + ") and sddm's " + c("Session") + " of the " + c("[Autologin]") + " group "
        "(" + sysf("/usr/lib/sddm/sddm.conf.d") + ", " + sysf("/etc/sddm.conf.d") + ", " + sysf("/etc/sddm.conf")
        + "). The active manager is read from " + sysf("/etc/X11/default-display-manager") + " or the target of "
        + sysf("display-manager.service") + " (" + c("active_display_manager()") + "); if it is another one, such as "
        + c("gdm3") + ", the lightdm and sddm files are leftovers and are ignored. The session name is cleaned "
        "(" + c(".desktop") + " stripped, only " + c("[A-Za-z0-9._+-]") + ") and mapped to a desktop by "
        + c("desktop_of_session_name()") + " (the words " + c("xfce") + ", " + c("lxqt") + ", " + c("plasma") + " or "
        + c("kde") + ", " + c("gnome") + "). With no usable declaration the order of the table stays. The session a "
        "single user picks at login is not read.",
        "The XFCE marker is " + c("xfce4-session") + ", not " + c("labwc") + ": labwc is the compositor shared with LXQt "
        "and remains a precondition.",
        "A machine with none of the four is declared " + c("SESSION_DESKTOP_NONE") + ": REMOTIX does not fall back to "
        "GNOME. The comment in " + c("recognize_desktop()") + " records that such a fallback once made failures blame "
        "someone else's drop-in and Mutter while the real cause was a missing desktop.",
        c("DesktopSession") + " travels as a " + c("uint32_t") + " between parent and child, so new values go at the end: "
        "GNOME 0, KDE 1, XFCE 2, none 3, LXQt 4 (" + c("session.h") + ").",
        "Capture, input, clipboard and stage rebuild ask " + c("session_on_wlroots()") + " (XFCE or LXQt), not «is it "
        "XFCE»: with five comparisons against XFCE, LXQt would have fallen silently into the GNOME/KDE branch. Every "
        "desktop branch in " + c("session.c") + " is placed in front of the GNOME code with an explicit predicate "
        "(" + c("e_kde()") + ", " + c("e_xfce()") + ", " + c("e_lxqt()") + ").",
    ])

# ═════════════════════════════════════════════════════════════════════════
# 3. The composed environment
# ═════════════════════════════════════════════════════════════════════════
S3 = p("The environment of the session is <b>composed, not inherited</b> (" + c("compose_environment()") + "). Whatever "
       "the starter carries ends up in the user's systemd manager and in D-Bus activation, where it outlives the "
       "compositor; a stray " + c("LC_ALL=C") + " from an SSH shell once stopped every application from opening "
       "(the comment in " + c("session.h") + "). The table is what the function writes.", lead=True) + \
    table(["Variable", "GNOME", "KDE", "XFCE", "LXQt"], [
        [c("XDG_RUNTIME_DIR") + ", " + c("DBUS_SESSION_BUS_ADDRESS") + " (the bus is deduced as "
         + c("unix:path=$XDG_RUNTIME_DIR/bus") + " if absent)", "yes", "yes", "yes", "yes"],
        [c("XDG_CURRENT_DESKTOP"), c("DesktopNames") + " of the chosen session file", "not set by REMOTIX", c("XFCE"),
         c("LXQt:labwc:wlroots")],
        [c("XDG_SESSION_DESKTOP"), "the session id (" + c("gnome") + ")", "—", "from " + c("add_session_names()") + " (fallback " + c("xfce") + ")",
         "same (fallback " + c("lxqt") + ")"],
        [c("XDG_SESSION_TYPE"), c("wayland"), "—", c("wayland"), c("wayland")],
        [c("XDG_MENU_PREFIX"), "—", c("plasma-"), c("xfce-"), c("lxqt-")],
        [c("XDG_CONFIG_DIRS"), "only if the user manager (or the child) already has one", "REMOTIX's " + c("xdg") + " folder first",
         "REMOTIX's labwc folder first", "REMOTIX's LXQt folder first, then " + c("/etc:/etc/xdg:/usr/share")],
        [c("XDG_DATA_DIRS"), "only if the user manager (or the child) already has one", "same", "same",
         "REMOTIX's session-data folder first"],
        [c("XCURSOR_THEME") + ", " + c("XCURSOR_SIZE") + ", " + c("XCURSOR_PATH"), "—", c("remotix-invisible") + ", 24",
         c("remotix-invisible") + ", 24", c("remotix-invisible") + ", 24"],
        [c("WLR_BACKENDS") + ", " + c("WLR_LIBINPUT_NO_DEVICES"), "—", "in KWin's labwc only: " + c("headless") + ", 1",
         c("headless") + ", 1", c("headless") + ", 1"],
        [c("WLR_RENDER_DRM_DEVICE") + " or " + c("WLR_RENDERER=pixman"), "—", "in KWin's labwc only", "the node chosen by "
         + c("card_pick_desktop()") + ", or pixman", "same"],
        [c("LABWC_UPDATE_ACTIVATION_ENV"), "—", "in KWin's labwc only: 0", "1", "1"],
        [c("KWIN_FORCE_SW_CURSOR"), "—", "1, in KWin's environment", "—", "—"],
        ["Toolkit", "—", "—", c("GDK_BACKEND=wayland"), c("QT_QPA_PLATFORM=wayland") + ", " + c("QT_QPA_PLATFORMTHEME=lxqt")],
        [c("XFCE4_SESSION_COMPOSITOR"), "—", "—", c("labwc -m --session xfce4-session"), "—"],
        [c("SHELL"), "empty", "the user's login shell from passwd", "same", "same (qterminal falls back to /bin/sh without it)"],
        [c("DCONF_PROFILE"), "the session profile", "—", "—", "—"],
        [c("LANG") + " (a UTF-8 locale that exists), " + c("LANGUAGE") + ", " + c("LC_*") + " (the language of the user, see below)",
         "yes", "yes", "yes", "yes"],
        [c("HOME") + ", " + c("USER") + ", " + c("PATH"), "yes", "yes", "yes",
         "yes, with REMOTIX's " + c("bin-lxqt") + " folder at the head of " + c("PATH")],
    ], "«TAB» — The composed environment") + \
    p("<b>The language.</b> A local graphical login gives the session the language the user chose in the desktop settings and "
      "otherwise the system's one; the remote session does the same (" + c("child_locale_read()") + " in " + c("child.c") + "). "
      + c("LANG") + " is the first item of " + c("Languages=") + " (or the value of the older " + c("Language=")
      + ") in " + sysf("/var/lib/AccountsService/users/<name>") + ", read by the child <b>as root before it changes identity</b>, because that "
      "folder is " + c("root:root 0700") + "; with no such choice it is the " + c("LANG") + " that " + c("pam_env") + " put in the PAM "
      "environment from " + sysf("/etc/default/locale") + " (the second " + c("pam_env") + " line of " + c("src/remotix.pam") + "). The system's "
      + c("LC_*") + " and " + c("LANGUAGE") + " come from the same PAM environment (at most " + c("CHILD_LOCALE_MAX") + " = 12 of them). "
      "Every value is checked for plain characters before it is written into an " + c("execve") + " environment, and " + c("local_utf8()")
      + " in " + c("session.c") + " still checks that the locale exists and is UTF-8, falling back to " + c("C.UTF-8")
      + " with a log line (until 1.0.1 the language was always " + c("C.UTF-8") + "). All these names are in " + c("OUR_VARIABLES")
      + " (" + rif("Ending a session and tidying up") + ").") + \
    p("<b>The language in the user manager (KDE, XFCE, LXQt).</b> On these three desktops the units of the session (KWin and its labwc, "
      "labwc, the panel) are born with the environment of the user's systemd manager, which " + c("pam_systemd") + " made with the system's "
      "language, not with the one composed for the start command. " + c("manager_set_locale()") + " (" + c("session.c") + ") therefore "
      "puts the " + c("LANG") + ", " + c("LC_*") + " and " + c("LANGUAGE") + " words of the composed environment into the manager with "
      + c("SetEnvironment") + " before the session starts; if the bus does not answer a ⚠ line says the desktop's units may get the system's. "
      "At the end of a normal session the values go back as they were (they are in " + c("OUR_VARIABLES") + ", so the snapshot of birth "
      "restores them); in the close for a local login (" + c("session_clear_out_light()") + ") they stay in the manager <b>on purpose</b>: it is the "
      "language chosen by that same user, the one the local desktop now coming in uses too, and taking it away could take it from under "
      "that desktop. They are put right at the next remote birth, or go away with the manager. GNOME needs none of this: " + c("gnome-session")
      + " exports its whole environment.") + \
    note("on <b>KDE</b> the language of the desktop follows the user's own " + sysf("~/.config/plasma-localerc") + ", as at a local login. "
         "REMOTIX hands the right language to the session (the processes of the desktop carry it), but Plasma reads that file, which it "
         "creates at its first start, and where it holds another language it wins. A user who has already used KDE in one language changes "
         "it from KDE's own Settings; REMOTIX does not write that file.", "Language on KDE.") + \
    p("<b>The PATH is the one PAM gives to a login.</b> The child opens a PAM session with the service " + c("remotix")
      + " (" + rif("How a session is born") + ") and takes the " + c("PATH") + " that " + c("pam_env") + " composed from "
      + sysf("/etc/environment") + ". If PAM gives none, or one that is not a list of absolute folders without a " + c("..")
      + " component, of plain characters and at most 400 long (" + c("child_path_ok()") + "), the fallback of " + c("become_and_exec()")
      + " in " + c("child.c") + " applies: " + c("~/.local/bin:~/bin:/usr/local/bin:/usr/bin") + " with the user's real home (not for a home "
      "that holds a colon). On LXQt REMOTIX's " + c("bin-lxqt") + " folder goes in front. " + c("src/remotix.pam") + " warns not to add "
      + c("user_readenv=1") + ": the user would then choose the session's " + c("PATH") + " from " + sysf("~/.pam_environment") + ".") + \
    p("<b>The session's own folders.</b> On a machine where a local login runs " + sysf("/etc/X11/Xsession.d/60x11-common_xdg_path")
      + ", the session's folders " + sysf("/etc/xdg/xdg-<session>") + " and " + sysf("/usr/share/<session>") + " would come "
      "in front of " + c("XDG_CONFIG_DIRS") + " and " + c("XDG_DATA_DIRS") + ". On Debian 13 that script does not exist "
      "(" + c("docs/PULIZIA-tranche1.md") + ", item 7; checked on the four containers), so " + c("local_session()")
      + " returns an empty structure and the lists carry only REMOTIX's own folders and the system's. The code still "
      "calls the same helpers (" + c("session_config_dirs()") + ", " + c("session_data_dirs()") + ") and writes one log line "
      "saying that no session folder was applied.") + \
    p("<b>The render node.</b> wlroots is given the card chosen by " + c("card_pick_desktop()") + " (" + c("src/card_pick.c")
      + "): the BIOS primary card (PCI " + c("boot_vga") + " = 1) if it is capable (it has a render node, the node opens "
      "and " + c("card_can_draw()") + " creates a buffer through GBM), otherwise the capable card with the lowest PCI "
      "address, because the node names " + c("renderD128") + " and " + c("renderD129") + " can swap between boots. If "
      "nodes open but no card can draw, " + c("WLR_RENDERER=pixman") + " is set and declared; otherwise wlroots would fall "
      "back to software in silence. GNOME chooses its own card (Mutter's Boot VGA); REMOTIX does not force it. Every "
      "choice is one log line in the " + c("session") + " area giving node, PCI address, driver and the reason (" + c("card_say()")
      + "). The encoder's fallback card is a separate matter (" + rif("Video encoding") + ").")

# ═════════════════════════════════════════════════════════════════════════
# 4. How a session is born
# ═════════════════════════════════════════════════════════════════════════
BIRTH = flow([
    ("1 Clear-out", "leftovers of the last session; snapshot of the user manager", "dark"),
    ("2 Drop-in", "GNOME Shell or KWin unit; none on labwc", "blue"),
    ("3 Guards", "manager not stopping; old session gone; stale pipewire-pulse", "navy"),
    ("4 Settings", "dconf, xfconf, kdeglobals, LXQt folders", "light"),
    ("5 start()", "setsid --fork sh -c, output to session.log", "blue"),
], "«FIG» — The steps of " + c("session_spawn()") + ", in order")

S4 = p("The server never starts a desktop itself. The per-user child (" + rif("Startup and life cycle") + ") does, from its "
       "loop: when the state of the session is «dead» and no birth was requested in the last " + c("BIRTH_REIN_MS")
       + " (12 s), it calls " + c("session_spawn()") + ", which returns at once. The desktop shows up on the bus on a "
       "later round and the child's retry loop (" + c("STAGE_BIRTH_RETRY_MS") + " = 200 ms while the compositor is "
       "unreachable) mounts the capture then. The blocking " + c("session_ensure()") + " with its 40 s wait ("
       + c("WAIT_STARTUP_MS") + ") still exists in " + c("session.c") + " but the product no longer calls it.", lead=True) + \
    h4("The logind session") + \
    p("Before any desktop code runs, " + c("become_and_exec()") + " in " + c("child.c") + " opens a real logind session "
      "for the user with PAM: " + c("pam_start") + " with the service " + c("remotix") + ", " + c("XDG_SESSION_TYPE=wayland")
      + ", " + c("XDG_SESSION_CLASS=user"
      ) + ", no " + c("XDG_SEAT") + " (a session without a seat is headless by construction), the client's address as "
      + c("PAM_RHOST") + ", then " + c("pam_open_session") + ". The class must be " + c("user") + ": " + c("manager")
      + " is what lingering gives, and it is not enough for Mutter. " + c("pam_end()") + " is called <b>without</b> "
      + c("pam_close_session()"
      ) + ": logind keeps the session as long as the leader process lives, and the leader is the child after the "
      + c("exec") + ", so the stage outlives the client because the child outlives it. One detail was corrected on 17 Nov "
      "2026 (the comment in " + c("become_and_exec()") + "): " + c("pam_systemd") + " keeps the session alive with one "
      "descriptor, the write end of the fifo " + sysf("/run/systemd/sessions/<id>.ref") + ", opened with " + c("CLOEXEC")
      + ". The " + c("execve") + " closed it, so the session was «closing» about 0.1 s after «New session», its scope "
      "«abandoned» and nothing was ever stopped by logind at logout. The child now finds that descriptor by what it points "
      "to, clears " + c("CLOEXEC") + ", hands it to the new image with " + c("--session-fd") + ", and the new image sets "
      + c("CLOEXEC") + " again so that only the session's leader holds it. The measurement is recorded as made on the four "
      "boxes.") + \
    h4("A compositor that is not installed") + \
    p("On XFCE and LXQt the compositor is " + c("labwc") + ", a Recommends of the package, so " + c("apt install --no-install-recommends")
      + " leaves it out. " + c("session_missing_component()") + " (" + c("session.c") + ") answers it at <b>every</b> login (an administrator "
      "who installs the package while the server runs is believed at the next one): for XFCE and LXQt it looks for " + c("labwc")
      + " in the " + c("PATH") + " of the service and returns its name if it is missing; GNOME has its own compositor and KDE has the KWin "
      "fallback of " + rif("KDE Plasma: KWin nested in labwc") + ". " + c("main.c") + " asks it <b>before</b> the child is spawned, like "
      "the caps: no process and no logind session are made, the client gets " + c("0x0E") + " (" + rif("ATTACH and SESSION as implemented") + ") with the "
      "sentence «the desktop (XFCE) cannot start: `labwc` is not installed on this server», and the log names the package to install. "
      "Before this the user was admitted and looked at an empty canvas, and the cause sat in " + sysf("session.log")
      + ". " + c("session_spawn()") + " asks the same question and refuses with the same words in the tenant's slice of the log (an old "
      "child, a rebirth). The package's " + c("postinst") + " warns at installation if " + c("labwc") + " is missing "
      "(" + c("debian/remotix.postinst") + "). Declared limit (comment): the parent searches the " + c("PATH") + " of the service, the "
      "session starts with the one of the PAM login; they agree for " + c("/usr/bin") + ", where " + c("labwc") + " is packaged.") + \
    h4("The steps of " + c("session_spawn()")) + BIRTH + \
    steps([
        "<b>Clear-out and snapshot.</b> " + c("session_clear_out_handler()") + " removes what a session that ended badly left "
        "in the user manager, then " + c("session_snapshot_handler()") + " writes the previous value of each variable "
        "REMOTIX is about to set (" + c("OUR_VARIABLES") + ") into " + sysf("$XDG_RUNTIME_DIR/remotix/manager-before")
        + " (" + rif("Ending a session and tidying up") + "). " + c("dconf_profile_reinstate()") + " puts the three dconf "
        "layers back (GNOME).",
        "<b>The drop-in</b> (" + c("write_dropin()") + "): " + sysf("zz-remotix-monitor.conf") + " in "
        + sysf("$XDG_RUNTIME_DIR/systemd/user.control/<unit>.d/") + " for GNOME's Shell unit and KWin's unit; nothing for "
        "XFCE and LXQt, where the compositor is not a unit. It is always <b>re-read</b> after " + c("daemon-reload")
        + " (" + c("systemctl --user show -p ExecStart") + "): if another drop-in wins, or " + c("--virtual-monitor")
        + " is still there, the birth is refused with a ⛔ line, because the session would have a monitor of its own and the "
        "user would watch an empty screen. If the drop-in is not in force the desktop is not born.",
        "<b>Guards.</b> The user manager must not be «stopping» (" + c("systemctl --user is-system-running") + ": a "
        "session born in a dying manager dies without writing anything). The previous session must be really over "
        "(" + c("inactive_unit()") + ", below). A " + c("pipewire-pulse") + " older than the current " + c("pipewire")
        + " is a leftover and is stopped; its socket brings it back attached to the right " + c("pipewire")
        + ". The first two say no and return, and the child's retry loop tries again; the third does not stop the birth.",
        "<b>Settings</b> before the command, because " + c("gnome-session") + " starts the Shell first and a key written "
        "afterwards would hold only for the next session: " + c("session_dconf_birth()") + " on GNOME, then "
        + c("session_settings()") + " (" + rif("What the session imposes, desktop by desktop") + ").",
        "<b>" + c("start()") + "</b> composes the environment and the command, then runs " + c("setsid --fork sh -c")
        + " with the user's home as working directory. The shell line begins with " + c("exec >>log 2>&1") + ": the "
        "session's output goes to " + sysf("session.log") + " (" + rif("Where the log lines go") + "). Because of "
        + c("setsid --fork") + " the desktop lives outside the server's unit and outside the child, so neither the unit's kill nor the "
        "death of the child ends it by itself. Since 17 Nov 2026 (§11.56) the product ends it on purpose: an orderly stop of the "
        "service closes every desktop (" + rif("Stopping the service") + "), and a desktop left without a child is ended by the root side "
        "within about 10 s unless its user returns first. A reattach while the child lives finds the same compositor and windows (the "
        "claim of the comments in " + c("session.c") + " and " + c("child.c") + "; the reattach checks of " + c("prove/")
        + " exercise it, " + rif("Testing") + ").",
    ]) + \
    p("<b>The command that starts each desktop</b> (" + c("start()") + "):") + \
    table(["Desktop", "Command", "Source of the command"], [
        ["GNOME", "the " + c("Exec") + " line of the chosen " + c("wayland-sessions/*.desktop") + " file (normally "
         + c("gnome-session"), c("gnome_session()") + ": the only session that runs " + c("gnome-session") + " with an "
         "installed " + c(".session") + " file; if several, the one named " + c("gnome") + ", else the first in alphabetical "
         "order, as GDM does; if none, " + c("gnome") + " as a declared fallback"],
        ["KDE", c("exec startplasma-wayland"), c("SESSION_COMMAND_KDE")],
        ["XFCE", c("exec labwc -m --session '<primary>'"), c("SESSION_HEAD_XFCE") + "; the primary client is " + c("xfce4-session")
         + " wrapped by " + c("measured_primary()")],
        ["LXQt", c("exec labwc -C <folder> -S '<primary>'"), c("write_config_labwc_lxqt()") + " writes the folder; the primary "
         "client is " + c("lxqt-session") + " wrapped by " + c("measured_primary()")],
    ], "«TAB» — How the session is started") + \
    p("<b>The primary client and the size race.</b> labwc's headless output is born 1280×720 and the client's size arrives "
      "about 200 ms later (" + c("wlr_ask_size()") + " in " + c("wlroots.c") + "). If " + c("pcmanfm-qt") + " or the XFCE panel "
      "is born in between, its wallpaper or its position is made for the wrong size and is never redone: the comments in "
      + c("measured_primary()") + " record about one birth in 13 with a 1280×720 wallpaper on LXQt, and an XFCE panel that "
      "redrew itself at every frame on one NVIDIA test. The cure is that the primary client is an " + c("sh") + " that runs "
      + c("wlr-randr --output <first output> --custom-mode WxH") + " and then " + c("exec") + "s " + c("xfce4-session")
      + " or " + c("lxqt-session") + " (same pid, so «primary dead, labwc exits» stays true). It is a " + c(";") + ", not "
      + c("&&") + ": if " + c("wlr-randr") + " fails, the session is born anyway and the late request remains. That is why "
      + c("wlr-randr") + " is a Recommends of the package.")

# ═════════════════════════════════════════════════════════════════════════
# 5. Ending a session and tidying up
# ═════════════════════════════════════════════════════════════════════════
S5 = p("A session ends in three ways: the user chooses «Log Out» in the desktop, the product asks for it, or the compositor "
       "dies. The next login is always a <b>new</b> session (" + c("SPECS.md") + " §5.2-bis): the child does not remake a "
       "desktop the user closed.", lead=True) + \
    h4("The user logs out") + \
    p("The child's loop watches the state of the session. If it was alive and becomes dead, the child records "
      + c("session_closed_by_user") + ", sends the parent " + c("MSG_SESSION_FINISHED") + " (the page receives the farewell "
      "0x10 and returns to the login form), runs " + c("session_clear_out_scope()") + ", " + c("session_dconf_neutralise()")
      + " and " + c("session_clear_out_handler_due()") + ", and then raises SIGTERM on itself (the box at " + c("§7.6")
      + " in " + c("child.c") + "). The last step is the correction of 17 Nov 2026: before it, only GNOME ended the "
      "child at logout (by an accident of GIO raising SIGTERM); on the other three the child stayed, held the logind session "
      "and the next login resumed it. Now the child dies of the signal on every desktop, its lifeline fifo closes and "
      "logind closes the session (the scope has already been emptied). A compositor that dies by itself looks the same "
      "from outside and is treated the same way.") + \
    p("<b>The farewell is said before the stage is taken down.</b> Dismantling the stage (capture, input, clipboard) waits for "
      "PipeWire, and PipeWire's real-time module can wait up to 25 s on RealtimeKit where " + c("rtkit-daemon") + " is installed but "
      "cannot start (containers, hardened machines): the page used to stay on the last image, without a word, for that long. "
      + c("session_over_early()") + " (" + c("child.c") + ") therefore sends " + c("MSG_SESSION_FINISHED") + " <b>first</b>, and the "
      "parent counts the child as «closing» from then on, so a login in the meantime gets the true " + c("0x0E") + " «still closing», "
      "never a desktop that is going away, and does not attach to it. It acts only on a <b>certain</b> death: " + c("session_life()")
      + " answers one of three, " + c("SESSION_LIFE_ALIVE") + ", " + c("SESSION_LIFE_DEAD") + " (the session bus answered and the "
      "compositor's name has no owner) or " + c("SESSION_LIFE_UNKNOWN") + " (a slow Mutter, a busy bus); only «dead» says the farewell, "
      "because the farewell cannot be taken back, and in doubt the old road holds (the remount asks again a second later). "
      "<b>KDE stays out</b>: with KWin's stage mounted, a KWin restarted by systemd leaves its name without an owner for a moment, "
      "so «no owner» is not certain there. The message is said once.") + \
    h4("The product ends it") + \
    p(c("session_terminate()") + " calls " + c("really_terminate()") + ", which asks politely, waits, and then forces. The "
      "wait is " + c("wait_until_done()") + ": up to " + c("WAIT_EXIT_MS") + " = 10 s, polling every " + c("CHECK_INTERVAL_MS")
      + " = 500 ms, until " + c("session_alive()") + " is false and " + c("inactive_unit()") + " is true. Success is "
      "followed by " + c("session_clear_out_scope()") + " and " + c("session_clear_out_handler()") + ".") + \
    table(["Desktop", "Polite request", "Force", "The fact that decides"], [
        ["GNOME", c("org.gnome.SessionManager.Logout(1)") + " (no confirmation)", c("Logout(2)") + " (forced)",
         sysf("gnome-session-manager@gnome.service") + " inactive and " + sysf("gnome-session-restart-dbus.service") + " inactive"],
        ["KDE", c("org.kde.Shutdown.logout()") + " (not " + c("LogoutPrompt") + ", which asks for a confirmation nobody gives)",
         c("StopUnit(graphical-session.target, fail)") + " (there is no " + c("Logout(2)") + " on KDE; it was " + c("plasma-workspace.target")
         + " until 1.0.1, which is not enough in time: KWin, ksmserver and plasmashell are " + c("PartOf") + " the graphical target)",
         sysf("plasma-kwin_wayland.service") + " and " + sysf("plasma-workspace.target") + " inactive"],
        ["XFCE", c("org.xfce.Session.Manager.Logout(false, false)") + "", "SIGTERM to every " + c("labwc") + " of the user (" + c("kill_xfce()") + ")",
         "no " + c("labwc") + " process of the user is left (" + c("my_processes()") + ")"],
        ["LXQt", c("org.lxqt.session.logout()") + " sent with " + c("NO_REPLY_EXPECTED") + " (it is " + c("Q_NOREPLY")
         + "; a synchronous call would report failure for a logout that worked)", "SIGTERM to labwc (same function)",
         "same as XFCE"],
    ], "«TAB» — How each desktop is asked to end") + \
    note("on XFCE the bus name is " + c("org.xfce.SessionManager") + " and the interface is " + c("org.xfce.Session.Manager")
         + " (one more dot); confusing them gives «unknown method», which looks like «the session does not answer». With "
         "force, " + c("kill_xfce()") + " sends SIGTERM, not SIGKILL, so labwc closes its clients. On XFCE and LXQt there is "
         "no unit to ask, so " + c("inactive_unit()") + " looks at processes: " + c("systemctl --user is-active") + " on a "
         "unit that does not exist answers «inactive», which would make the guard against a second session vanish "
         "silently (the comment in " + c("inactive_unit()") + ").", "XFCE names, and why XFCE and LXQt are checked by process.") + \
    p("<b>The close for a local login.</b> When a local login of the same user is held in PAM and the remote desktop must go first "
      "(" + rif("Local excludes remote and the session cap") + "), the orderly step on KDE waits " + c("KDE_PRELOCAL_ORDERLY_MS") + " = 5 s "
      "instead of 10 before the forced one. Plasma waits without limit for a program that does not close by itself (a «save changes?» "
      "dialog, a terminal running a program) and nobody is there to answer, so the ten seconds were only a delay of the local login. Every "
      "other close and every other desktop keeps " + c("WAIT_EXIT_MS") + ". The forced step is " + c("StopUnit") + " of "
      + c("graphical-session.target") + ", which takes the whole desktop down. If the parent that asked for the close is gone by then (the "
      "root side released its hold and the local desktop may be starting), the forced step is <b>not</b> taken and a line says so "
      "(" + c("force_refused()") + ").") + \
    h4("What is left in the user manager") + \
    p("What the product puts into the user's systemd manager outlives the session if the manager does (the test containers "
      "and any user with lingering enabled): the drop-ins under " + sysf("user.control") + " and the variables that "
      + c("gnome-session") + ", " + c("startplasma-wayland") + " or labwc export from the composed environment. A user "
      "who then logs in at the monitor would inherit them (on XFCE a «Log Out» that does not log out, on GNOME the in-memory "
      "dconf). The cure is two gestures:") + \
    ul([
        c("session_snapshot_handler()") + " at birth, before touching anything: the previous value of each variable in "
        + c("OUR_VARIABLES") + " (" + c("DCONF_PROFILE") + ", " + c("XDG_CONFIG_DIRS") + ", " + c("XDG_DATA_DIRS") + ", "
        + c("XCURSOR_THEME") + ", " + c("XDG_CURRENT_DESKTOP") + ", " + c("GDK_BACKEND") + ", the " + c("WLR_*")
        + " variables and the others in the list) goes into a file that exists as long as the manager does.",
        c("session_clear_out_handler()") + " when the session is over (and at the child's start and at birth, for what a "
        "crash left): REMOTIX's drop-ins are removed with " + c("daemon-reload") + ", its variables are put back as they "
        "were or removed, " + c("xfconfd") + " is restarted if it had the session's folder, and on XFCE " + c("xfce_restore_keys()")
        + " puts the user's values back. Only with the session dead: with a live session it would pull the ground from under "
        "a working desktop. Without a snapshot (a manager born before) only variables carrying REMOTIX's mark are removed, "
        "and it is said. If the session still answers when the child leaves, the child retries for at most "
        + c("CLEAR_OUT_EXIT_WAIT_MS") + " = 2 s and otherwise leaves the work to the next child, with a ⛔ line.",
        c("session_dconf_neutralise()") + " (GNOME): a belt for when that clear-out is late. When the session is over, the "
        "dconf profile file is rewritten atomically with the user's base alone, so anyone who inherited " + c("DCONF_PROFILE")
        + " reads normal settings. Never under a live desktop.",
        c("session_clear_out_scope()") + ": after the session has exited, what is left in the session's logind scope and "
        "belongs to the user (programs that detached from the session manager by D-Bus activation or a double fork) gets "
        "SIGTERM, then SIGKILL after 2 s. The comment records the case: after a XFCE logout, " + c("localsearch-3")
        + " and geoclue's agent stayed in the scope.",
    ]) + \
    h4("KDE: a Log Out that stops halfway") + \
    p("«Log Out» calls " + c("plasma-shutdown") + ", which asks ksmserver and KWin to close their windows and then asks the user manager to stop "
      + sysf("graphical-session.target") + ", which is what really stops KWin, plasmashell and the rest. If any unit has a "
      "start job queued at that moment (the comment names " + c("xdg-desktop-portal") + " in its first seconds), systemd "
      "refuses the stop («Transaction … is destructive»), plasma-shutdown ignores the refusal and exits, and the desktop "
      "stays up. " + c("session_kde_logout_watch()") + " (called at every round of the child's loop, one look per second) has two signals, "
      "and either starts the same grace. <b>First</b>: " + c("plasma-shutdown") + " owns the bus name " + c("org.kde.Shutdown") + " for its whole run "
      "and releases it when it exits (" + c("NameOwnerChanged") + ", followed on a private main context turned at each round, because a "
      "poll would miss a short run); the release alone is not a logout (the same program runs for «save session», and exits without "
      "stopping anything if the user cancels), so the watch then asks " + c("ksmserver.isShuttingDown()") + ": " + c("true") + " arms it, "
      + c("false") + " (cancelled, or not a logout) forces nothing, and a ksmserver that does not answer forces nothing either, because a "
      "logout that cannot be confirmed is not worth the user's unsaved work. <b>Second</b>, the older one: " + c("plasma-workspace.target")
      + " seen <b>active</b> in this child's life and then not active while " + c("org.kde.KWin") + " is still on the bus (on Plasma 6.6 "
      "and later plasma-shutdown never stops that target, which is why the first road exists). After a grace of "
      + c("KDE_LOGOUT_GRACE_MS") + " = 4 s, in which the normal road wins if it works, the stop of " + c("graphical-session.target")
      + " is asked again with mode " + c("fail") + " (as plasma-shutdown does), every " + c("KDE_LOGOUT_RETRY_MS") + " = 3 s, "
      + c("KDE_LOGOUT_TRIES") + " = 10 times; then in mode " + c("replace") + " (a queued start job replaces nothing of the user's work) "
      "another ten times. If even that is refused the watch returns «to be closed» and the child closes the session by the product's own "
      "road (" + c("session_terminate()") + "). One log line per attempt. Declared limits (comment): " + c("logoutAndShutdown")
      + " and " + c("logoutAndReboot") + " are not covered (they are reachable only through the menu entries, which REMOTIX removes), and "
      "a restart of KWin by its wrapper during the wait resets the request.") + \
    warn("whether a refused stop can also happen on other desktops was not investigated in the code; only KDE has this watch. "
         "The PIANO.md status of 17 Nov also lists, as an open point, that XFCE ignores a Log Out requested while the desktop "
         "is still starting: it is described there as a behaviour of the desktop itself, and the code does not retry it "
         "(" + rif("Behaviours of the four desktops worth knowing") + ").", "Scope of the KDE watch.")

# ═════════════════════════════════════════════════════════════════════════
# 6. GNOME
# ═════════════════════════════════════════════════════════════════════════
S6 = p("GNOME is started through the machine's own GNOME session, with a systemd drop-in that makes " + c("gnome-shell")
       + " headless and without monitors: the only monitor is the virtual one that the capture creates with "
       + c("RecordVirtual") + ", and that is where GNOME puts its top bar and dock.", lead=True) + \
    steps([
        "<b>Which Shell unit.</b> " + c("unit_shell()") + " asks the user manager for the " + c("FragmentPath") + " of "
        + sysf("org.gnome.Shell@wayland.service") + " and accepts it only if it ends in that name. On trixie it is a real file in "
        + sysf("/usr/lib/systemd/user") + " (" + c("docs/PULIZIA-tranche1.md") + "). The template unit of newer GNOME "
        "versions is not handled; the branch was removed as unreachable on Debian 13. A manager that loads another unit is "
        "refused with a ⛔ line.",
        "<b>The drop-in.</b> " + sysf("zz-remotix-monitor.conf") + " in the instance directory under "
        + sysf("$XDG_RUNTIME_DIR/systemd/user.control/org.gnome.Shell@wayland.service.d/") + " replaces " + c("ExecStart")
        + " with " + c("gnome-shell --headless --no-x11") + ". No root, gone at reboot, named " + c("zz-") + " so that it "
        "applies after any system drop-in. The checks of " + c("write_dropin()") + " are those of the previous section.",
        "<b>The previous session must be over</b>: " + sysf("gnome-session-manager@gnome.service") + " and "
        + sysf("gnome-session-restart-dbus.service") + " both inactive. A session started while GNOME restarts the session "
        "bus dies without writing anything (the comment in " + c("inactive_unit()") + ", measured 16 Aug 2026).",
        "<b>Capture and input</b> use Mutter's own D-Bus interfaces, not " + c("xdg-desktop-portal") + " (the portal asks "
        "permission from a user in front of the screen, which a session without a monitor cannot give). The order in "
        + c("mutter.c") + " is fixed and punished by different errors if permuted: " + c("RemoteDesktop.CreateSession")
        + ", " + c("ScreenCast.CreateSession") + " declaring " + c("remote-desktop-session-id") + ", "
        + c("RemoteDesktop.Session.Start") + ", " + c("RecordVirtual") + ", " + c("Stream.Start") + ". Keyboard and pointer "
        "go through libei (" + c("ConnectToEIS") + "); the clipboard through the same RemoteDesktop session. The size of "
        "the virtual monitor is part of the PipeWire negotiation, so a new size is a renegotiation (" + c("docs/LESSONS.md")
        + " §3 table, question 13; " + rif("Screen capture") + ").",
        "<b>The pointer.</b> Mutter delivers the cursor as metadata (" + c("cursor-mode=2") + "); " + c("cursor.c")
        + " turns it into the wire's " + c("CURSOR_SHAPE") + " and discards sizes the protocol forbids.",
        "<b>The first movement is sent twice.</b> The comment in " + c("input_pointer()") + " (" + c("input.c") + ") records that the first "
        "absolute motion after the pointer device is (re)started reaches the windows with one of the two coordinates at 0, so a click made "
        "at once (a tap from a phone) lands on the edge of the screen; the following motions, and the same position sent a second time "
        "right after the first, are exact. The first one is therefore sent twice (" + c("pointer_primed") + "); a compositor that needs no "
        "such thing ignores the repeat. The comment marks it as to be removed when Mutter is fixed.",
    ]) + \
    h4("The session dconf") + \
    p(c("session_dconf_prepare()") + " writes " + sysf("$XDG_RUNTIME_DIR/remotix/dconf/profile") + ", a profile of three "
      "layers, and sets " + c("DCONF_PROFILE") + " before any GSettings call; the session gets the same variable through the "
      "composed environment. The reason for three layers is measured: a " + c("file-db") + " recompiled during the session "
      "is not seen by programs already open (dconf 0.40, in the comment), so what changes lives in an in-memory database "
      "and the locks database is compiled to a temporary file and renamed, never deleted while the session lives.", lead=False) + \
    table(["Layer (top to bottom)", "What it holds", "Written by the session?"], [
        [c("user-db:user"), "the user's own database " + sysf("~/.config/dconf/user"), "yes, and it stays: wallpaper, theme or "
         "a shortcut changed from the remote desktop is still there next time and at the monitor"],
        [c("file-db:…/remotix/dconf/locks.db"), "the keys REMOTIX imposes, <b>value and lock</b>, compiled when the child starts (" + c("session_dconf_prepare()") + ") with "
         + c("dconf compile") + " (package " + c("dconf-cli") + ", a Recommends)", "no: a lock hides the layers above it"],
        [c("service-db:shm/remotix"), "an in-memory database (tmpfs, never " + sysf("~/.config") + "): the keyboard layout "
         "(" + c("input-sources") + ")", "yes, by " + c("input_layout()") + " in " + c("input.c")],
        ["the rest of the user's base profile", "system databases", "no"],
    ], "«TAB» — The three layers of the session profile") + \
    table(["Key (" + c("DCONF_KEYS") + " in " + c("session.c") + ")", "Value", "Why"], [
        [c("org.gnome.mutter.wayland.keybindings switch-to-session-1") + " … " + c("12"), "empty", "Headless Mutter binds "
         + c("Ctrl+Alt+F1") + "…F12 and there is no console to switch to. The schema is " + c("…wayland.keybindings")
         + "; the comment records that until 13 Nov 2026 the code opened " + c("org.gnome.mutter.wayland") + " and the "
         "keys were never removed"],
        [c("org.gnome.shell always-show-log-out"), "true", "The log-out entry is the only gesture that ends the session"],
        [c("org.gnome.desktop.lockdown disable-user-switching"), "true", "Only log-out stays in the menu"],
        [c("org.gnome.desktop.lockdown disable-lock-screen"), "true", "On GNOME the desktop's lock revokes capture and input"],
        [c("org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type") + ", " + c("…-battery-type"), c("nothing"),
         "No automatic suspend"],
        [c("org.gnome.desktop.session idle-delay"), "0", "No idle blanking"],
        [c("org.gnome.desktop.screensaver lock-enabled"), "false", "The lock is REMOTIX's, not the desktop's"],
        [c("org.gnome.desktop.input-sources") + " " + c("sources") + ", " + c("current") + ", " + c("mru-sources"),
         "the negotiated layout, from the in-memory layer", "Lock only; " + rif("Input")],
    ], "«TAB» — The GNOME keys imposed on the session") + \
    p("<b>The scale.</b> The input's coordinate space is the logical monitor's layout, and with a scale other than 1 the layout and the "
      "stream's pixels diverge: the pointer goes elsewhere without any line saying so (guard 2 of " + c("DECISIONS.md") + " §5.0-sexies, "
      "comment of " + c("mutter.h") + "). The child reads the scale of REMOTIX's own logical monitor (" + c("mutter_our_scale()") + "). If it "
      "was read and is not 1 (a scale saved from Settings → Displays in " + sysf("~/.config/monitors.xml") + ", a mandatory dconf profile "
      "of the administrator), the child makes <b>one</b> attempt, " + c("mutter_scale_to_one()") + " (" + c("mutter.c") + "), with "
      + c("ApplyMonitorsConfig") + " method 1 (temporary, never written to " + sysf("monitors.xml") + ") and only in the plain case of one "
      "logical monitor, which is ours, with one monitor; the user's own settings are untouched and at a local login they find their own "
      "scale again. If the scale re-read is exactly 1.0 the stage goes on and a line says the user's scale is ignored in the remote "
      "session. If not, the stage is refused: " + c("MSG_STAGE") + " carries " + c("fatal") + " = 1, the parent sends " + c("0x0E")
      + " to every login of that user (" + c("stage_refused_by_child()") + ", " + rif("Local excludes remote and the session cap")
      + "), and the child closes the graphical session, retrying every 10 s if that fails, instead of remounting the stage for ever in front "
      "of a black page. A scale that could not be read is not taken for 1.0: the child goes on and says so.") + \
    p("At birth the in-memory layer is emptied and the user's real " + c("input-sources") + " is copied into it; the "
      "negotiated layout replaces it later. After the birth nothing is written: " + c("session_dconf_verify()") + " "
      "<i>re-reads</i> every key through the session profile, as the Shell and the " + c("gsd-*") + " daemons do, and says "
      "whether it is in force. Every schema and key is looked up before use, because " + c("g_settings_new()") + " on a "
      "missing schema aborts the process (the comment records a child dead of SIGTRAP from a key renamed between GNOME "
      "versions).") + \
    p("<b>Declared fallbacks.</b> If " + c("dconf compile") + " is missing or fails, the profile is the old one (the "
      "in-memory layer on top, the user's databases below) and the same keys are written into the in-memory layer: nothing "
      "goes in the user's file, but what the user changes from the remote desktop is lost at the next birth. A mandatory "
      "profile in " + sysf("/run/dconf/user/<uid>") + " wins over " + c("DCONF_PROFILE") + ": the locks cannot hold, and it is "
      "declared. A one-time cleanup, marked by " + sysf("~/.local/state/remotix/gnome-ripristinato")
      + " (" + c("session_dconf_restore_once()") + "), removes from the user's dconf the four keys that older REMOTIX "
      "versions wrote, if they still hold exactly those values; the package's postrm removes the mark on purge.") + \
    p("<b>Inhibition.</b> " + c("session_inhibit()") + " calls " + c("org.gnome.SessionManager.Inhibit") + " with flags "
      + c("SUSPEND | IDLE") + " (4 | 8 = 12) and never the logout bit: with it, the user's own logout would be blocked by "
      "REMOTIX. The cookie is never released; it lives as long as the session.")

# ═════════════════════════════════════════════════════════════════════════
# 7. KDE
# ═════════════════════════════════════════════════════════════════════════
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

S7 = p("Plasma is started with " + c("startplasma-wayland") + ", which starts KWin as the user unit "
       + sysf("plasma-kwin_wayland.service") + ". REMOTIX overrides that unit's " + c("ExecStart") + " the same way as GNOME's "
       "shell, but the line does not start KWin directly: it starts the REMOTIX binary in " + c("--kwin-nested")
       + " mode, which starts a <b>labwc without a screen</b> and then becomes KWin, running as a window inside that labwc "
       "(" + c("DECISIONS.md") + " §10.40). The desktop is KWin's single output; KWin's output follows the size of its window; "
       "the window follows labwc's output. To change the desktop's size at a reattach, REMOTIX changes the size of labwc's "
       "output.", lead=True) + \
    code("[Service]\n"
         "ExecStart=\n"
         "ExecStart=/usr/libexec/remotix/remotix --kwin-nested 1920 1080 /dev/dri/renderD128 -- /usr/bin/kwin_wayland_wrapper --xwayland --width 1920 --height 1080 --no-lockscreen",
         "text", "The KWin drop-in written by write_dropin(), for a 1920×1080 canvas (the binary path is " + c("/proc/self/exe") + ")") + \
    KDE_FIG + \
    table(["Choice", "Why (from the comments of " + c("kwin.c") + " and " + c("docs/LESSONS.md") + ")"], [
        ["Not " + c("kwin_wayland --virtual"), "KWin 6.3.6 cannot resize a " + c("--virtual") + " output and cannot create a "
         "second one; the mode is constant and the list fixed in the constructor (" + c("docs/LESSONS.md") + " §3 table, question "
         "13). The desktop would keep its birth size and a reattach from another window size would get a rescaled picture."],
        ["Not a restart of KWin at the new size", "The comments record that Firefox and a GTK editor died at the first "
         "restart; only Qt programs survive a compositor restart."],
        ["A nested KWin", "KWin's Wayland backend resizes its output when its window is configured to a new size, and "
         "labwc's output is resized with " + c("zwlr_output_manager_v1") + ", the protocol REMOTIX already uses on XFCE and "
         "LXQt. No program is restarted."],
    ], "«TAB» — Why KWin runs inside labwc") + \
    p("<b>The start line</b> (" + c("kwin_nested_alive()") + " in " + c("kwin.c") + "). " + c("write_dropin()") + " writes it "
      "with the path of the running binary, the canvas size and a render node chosen like XFCE's labwc (" + c("pixman")
      + " if no card can draw, " + c("-") + " if no node opens, with a ⛔ line). The helper then runs as the user, inside the unit:") + \
    steps([
        "It checks the line " + c("W H NODE -- <wrapper> …") + ", W and H between 200 and 8192; otherwise exit 2.",
        "It finds " + c("labwc") + " in " + c("PATH") + " (the distribution's; there is no REMOTIX-built labwc in this tree). If "
        "there is none, the session is still born: the helper runs the KWin wrapper with " + c("--virtual") + " added and "
        "writes " + c("⛔ labwc is not installed: KWin --virtual, and the desktop will NOT take the window's size at reattach "
        "(DECLARED FALLBACK)") + " to the unit's output (the user's journal). " + c("labwc") + " is a Recommends of the package.",
        "It writes labwc's configuration " + sysf("$XDG_RUNTIME_DIR/remotix-kwin-host/labwc/rc.xml") + " (folder 0700, "
        "rewritten at every birth) and starts " + c("labwc -C <that folder>") + " with " + c("XDG_RUNTIME_DIR") + " set to "
        + sysf("$XDG_RUNTIME_DIR/remotix-kwin-host") + ", " + c("WAYLAND_DISPLAY") + ", " + c("WAYLAND_SOCKET") + " and "
        + c("DISPLAY") + " removed, " + c("WLR_BACKENDS=headless") + ", " + c("WLR_LIBINPUT_NO_DEVICES=1") + ", the node or "
        + c("WLR_RENDERER=pixman") + ", and " + c("LABWC_UPDATE_ACTIVATION_ENV=0") + ". labwc's socket is then inside that "
        "folder, and KWin's " + c("wayland-N") + " stays the only socket in the user's runtime folder, so capture, input and "
        "clipboard cannot land on the host by mistake. With activation updates off, labwc never publishes its own display to the "
        "bus or to systemd, where the session's programs would open on a screen nobody sees.",
        "It waits for labwc's socket for at most " + c("HOST_BIRTH_MS") + " = 10 s and stops if labwc exits first.",
        "labwc's headless output is born 1280×720; the helper sets it to W×H at " + c("HOST_MHZ") + " = 240 Hz and reads the size "
        "back <b>before</b> KWin opens its window, so the desktop is born at the right size.",
        "It starts the ticker and the ScreenSaver sidecar (below), both with a double fork so that neither stays a zombie of the "
        "wrapper, sets " + c("KWIN_FORCE_SW_CURSOR=1") + ", and becomes the KWin wrapper with "
        + c("--wayland-display <labwc's socket>") + " added.",
    ]) + \
    table(["Trap of KWin inside labwc (measured 11 Oct 2026, per the comments)", "Cure in " + c("kwin.c")], [
        ["KWin froze a few seconds after birth: it draws its next frame only after labwc says the previous one was "
         "presented, and labwc answers only when it repaints, which a frame without damage does not trigger.",
         "<b>The ticker</b>: a separate process puts a 1×1 transparent surface in labwc's overlay layer and damages it every "
         + c("TICKER_MS") + " = 16 ms. It ends with labwc or its parent."],
        ["The pointer's shape never changed in the page and a full-screen Firefox froze: the nested output has a cursor layer, "
         "so KWin put the cursor on labwc's screen and handed full-screen windows over as they were.",
         c("KWIN_FORCE_SW_CURSOR=1") + ": KWin draws the pointer itself."],
        ["Frames lost: labwc presents on its own 60 Hz clock and the two clocks drift.", "labwc's output at 240 Hz ("
         + c("HOST_MHZ") + "); KWin keeps its own 60."],
        ["A full-screen window with the pointer hidden froze in the picture: KWin scanned it out to labwc directly.",
         "One transparent pixel on top, inside KWin, on the capture's own connection: KWin never scans out a window with "
         "anything above it."],
        ["At birth labwc configures KWin's window more than once, and a capture asked in between offers a size KWin's "
         "stream no longer has.", c("kwin_host_settle()") + ": before mounting the capture the child waits (at most 3 s) until "
         "KWin's output has the host's size."],
    ], "«TAB» — Traps of KWin inside labwc") + \
    p("The labwc configuration is deliberately minimal. " + c("-C") + " makes labwc read only that folder, so a user's "
      + sysf("~/.config/labwc") + " never gets in. The single window rule matches on the window title with " + c("ToggleFullscreen")
      + " and no server decoration, because the window must be exactly the output's size; the comments record that on one "
      "distribution a rule on the identifier never fired. The configuration also carries one key binding and one root mouse "
      "binding, each with the single action " + c("None") + ": a configuration with no bindings makes labwc load its default "
      "ones, which start programs, and any program of the same user could press them through the virtual-keyboard protocol on "
      "its socket. The measurements behind this are in the comments of " + c("kwin.c") + " and " + c("DECISIONS.md") + " §10.43; "
      "they were made on labwc versions the comments name and are not repeated here.") + \
    steps([
        "<b>At a reattach of another size</b> (" + c("child.c") + ", §7.1), if KWin's output is not the canvas asked for and the "
        "host exists, the child first dismantles the capture: KWin's stream would otherwise renegotiate to a size the fixed offer "
        "refuses, and die.",
        c("kwin_host_resize()") + " asks labwc's output for the new size (read back, not believed), then reads KWin's output "
        "on a connection of its own until it has the same size, for at most 3 s.",
        "The capture is mounted again at the new canvas.",
    ]) + \
    p("A reattach at the <b>same</b> size asks for nothing. A Plasma session with no host (labwc missing, or born with "
      + c("--virtual") + ") keeps the size it was born with, and the child declares " + c("⚠ §7.1 KDE: this Plasma session has no "
      "host for KWin … DECLARED FALLBACK") + ". The capture takes KWin's only output (" + c("WL-0") + " when nested, "
      + c("Virtual-0") + " with " + c("--virtual") + ").") + \
    h4("Capture, input, cursor and clipboard") + \
    p("Capture uses KWin's " + c("zkde_screencast_unstable_v1") + " on a PipeWire stream, with the pointer requested as "
      "<i>metadata</i> (" + c("POINTER_METADATA") + " = 4; the choice cannot be changed on a live stream), so a pointer "
      "movement produces a buffer with no new pixels marked corrupted, which " + c("capture.c") + " discards. KWin only "
      "allows the screen-cast global to a program it recognises: " + c("kwin_check_permission()") + " verifies at startup "
      "that " + sysf("/usr/share/applications/org.kde.remotix.desktop") + " (shipped by the package, " + c("debian/org.kde.remotix.desktop")
      + ") exists (" + c("RX-KDE-001") + "), that its " + c("Exec") + " resolves to the running binary (" + c("RX-KDE-002")
      + ") and that " + c("X-KDE-Wayland-Interfaces") + " lists the interface (" + c("RX-KDE-003") + "). Input goes through "
      "libei from KWin (" + c("kwin_eis_fd()") + "), and the keyboard layout is written to a " + c("kxkbrc") + " in the "
      "session folder, which KWin is told to reload with the D-Bus signal " + c("org.kde.keyboard reloadConfig") + " ("
      + c("kwin_layout()") + "). The clipboard uses the wlroots data-control protocol (" + c("clipboard_kde.c") + ") on KWin's "
      "socket. The shape of the pointer comes from the metadata, where the session's cursor theme " + c("remotix-invisible")
      + " has one-pixel opaque images of unique colours that the dictionary " + c("shape_from_pixel()") + " maps back to a "
      "real cursor image (" + c("shape.c") + "; " + rif("Screen capture") + ").") + \
    p("<b>The ScreenSaver sidecar.</b> From Plasma 6.4 on, Ctrl+Alt+Del did nothing: the shortcut is a kded6 module that calls "
      + c("requestLogoutPrompt()") + ", which first asks " + c("org.freedesktop.ScreenSaver.GetActive") + " («never show the logout prompt on "
      "top of the lock screen»). That name belongs to KWin's lock-screen daemon, KWin starts with " + c("--no-lockscreen") + " (locking is "
      "REMOTIX's), nobody owns the name, the call fails with " + c("ServiceUnknown") + " and the failure is read as «the screen is locked» "
      "(comment in " + c("kwin.c") + ", measured on Plasma 6.6.7: with a stand-in that answered false the prompt came up in one second). The "
      "cure is " + c("screensaver_alive()") + ", a process that the start line forks beside KWin, in the unit's cgroup, that owns the name "
      "(" + c("DO_NOT_QUEUE") + ": if a real owner is there first, the sidecar ends and says so) on the two paths " + c("/ScreenSaver")
      + " and " + c("/org/freedesktop/ScreenSaver") + " and answers every method of the standard interface: «not locked» and zero times "
      "for " + c("GetActive") + " and the time queries, the harmless answer for " + c("SimulateUserActivity") + ", the standard error "
      + c("NotSupported") + " for " + c("Lock") + ", " + c("Throttle") + " and " + c("UnThrottle") + ". " + c("Inhibit") + " is <b>forwarded</b> to "
      "powerdevil's call with the same arguments and the same cookie back, and given back when the caller leaves the bus or calls "
      + c("UnInhibit") + ": measured with VLC, which asks the ScreenSaver name first and, on an error, does not go on, so a fake cookie "
      "would have left the video without a real inhibition. The sidecar dies with the unit and leaves nothing on the user's bus or in "
      "the user's files; if it cannot start, a line says Ctrl+Alt+Del will not open the logout screen.") + \
    p("<b>The lost frame.</b> KWin can leave a window on an old picture when nothing damages it: its stream is the driver of the graph, "
      "and a buffer queued before the reader ran for the previous one overwrites it, so a picture can be lost and with it its damage; if "
      "it was the last picture of an animation, nothing follows. " + c("capture_watch_sequence()") + " (" + c("capture.c") + ") counts the "
      "numbers KWin gives to its buffers, cursor-only ones included: a hole is a buffer that never arrived, and the next picture goes out "
      "«all changed». If no picture comes by itself within " + c("LOST_QUIET_MS") + " = 200 ms, " + c("capture_frame_lost()") + " tells the "
      "child, which calls " + c("kwin_poke()") + " (" + c("kwin.c") + "): the transparent pixel on top, on the capture's own connection, is "
      "attached, damaged and committed again, so KWin draws a frame. No stream restart, so no input device is recreated. At most one poke "
      "every " + c("LOST_QUIET_MS") + ", ten in a row (" + c("LOST_POKES_MAX") + ") without a picture, then it stops and says so once. A safety "
      "switch turns the count off, with a line, if more than half of " + c("SEQ_WINDOW") + " = 600 buffers in a row show a hole (a producer "
      "that does not number them one by one). It never runs on a still desktop: it takes a hole in the numbers.") + \
    note(c("kwin_check_permission()") + " ends its failure messages with «Remedy: reinstall the package from its file (sudo apt install "
         "--reinstall ./remotix_&lt;version&gt;_amd64.deb)» (" + c("RX-KDE-001") + ", " + c("RX-KDE-002") + " and " + c("RX-KDE-003") + ", "
         + c("kwin.c") + "): the remedy is the package's, since there is no installer; the same sentence is used by the other reinstall "
         "messages (" + c("main.c") + ").",
         "Remedy text.")

# ═════════════════════════════════════════════════════════════════════════
# 8. XFCE
# ═════════════════════════════════════════════════════════════════════════
S8 = p("XFCE on Wayland has no compositor of its own: it runs on labwc. There is no unit to override, so "
       + c("write_dropin()") + " does nothing and says so, and REMOTIX starts the compositor itself with "
       + c("exec labwc -m --session '<primary>'") + ", where the primary client is " + c("xfce4-session") + " preceded by the "
       "size step (" + c("measured_primary()") + "). The picture, pointer and input paths are the wlroots ones of "
       + rif("Screen capture") + " and " + rif("Input") + ".", lead=True) + \
    table(["Topic", "Behaviour", "Why"], [
        [c("--session") + " and " + c("XFCE4_SESSION_COMPOSITOR"), "Makes " + c("xfce4-session") + " labwc's primary client: when "
         "it exits, labwc exits. Both the command line and the variable are built from the same macro " + c("SESSION_HEAD_XFCE"),
         "If " + c("xfce4-session") + " does not find " + c("labwc") + " and " + c("--session") + " in the variable, at log-out it "
         "runs " + c("loginctl terminate-session ''") + " and kills REMOTIX's logind session"],
        [c("-m") + " (merge configuration)", "labwc reads " + c("rc.xml") + " from every XDG directory: REMOTIX's own "
         "(" + sysf("$XDG_RUNTIME_DIR/remotix/labwc-xfce/labwc/rc.xml") + ", first in " + c("XDG_CONFIG_DIRS") + ") and the user's",
         "Without it the first " + c("rc.xml") + " found would hide the other. Ours carries the «bring windows back inside» "
         "shortcut " + c("W-C-A-S-F12") + " (" + c("SESSION_LABWC_KEY") + ") and the default bindings"],
        ["Session xfconf", c("$XDG_RUNTIME_DIR/remotix/xdg-xfce/…/xfce-perchannel-xml/") + ": channel files in which every key "
         "REMOTIX imposes is <b>locked</b> with " + c("locked=\"<user name>\"") + " on the single property; "
         + sysf("xfconfd.service") + " receives " + c("XDG_CONFIG_DIRS") + " through the drop-in " + sysf("zz-remotix-session.conf")
         + " and is restarted, then every value is re-read (" + c("xfce_session_xfconf()") + ")",
         "Nothing permanent in the user's channels (§8.2-bis). A lock on a whole channel would make the panel read-only; the lock "
         "is per property"],
        ["Pointer shape", "labwc has no cursor plane and screencopy has no channel for the shape: the colour-coded theme puts "
         "one opaque pixel of a unique colour under the hotspot, and " + c("wlroots.c") + " reads a 3×3 region around the pointer "
         "after every gesture (one probe in flight, a tail probe 120 ms after the last)", "The comment records the cost "
         "measured on LXQt: about 1.4 points of labwc CPU at a 60 Hz hand"],
    ], "«TAB» — How XFCE is kept") + \
    table(["Key (" + c("XFCE_LOCKS") + ")", "Value", "Why"], [
        [c("xfce4-session general WaylandLogoutCommand"), c("/bin/true"), "A log-out that does not end the logind session"],
        [c("xfce4-session general SessionName") + ", " + c("SaveOnExit"), c("REMOTIX") + ", false", "The remote session neither "
         "finds nor saves sessions"],
        [c("xfce4-session general LockCommand"), c("/bin/false"), "The lock is REMOTIX's. " + c("/bin/false") + " so that whoever "
         "asks is told «it is not locked»; not empty, which means «not set»"],
        [c("xfce4-session shutdown ShowSwitchUser") + ", " + c("ShowSuspend") + ", " + c("ShowHibernate") + ", "
         + c("ShowHybridSleep"), "false", "No such buttons in the log-out dialog. Restart and Shut Down have no key; they stay "
         "grey because of polkit"],
        [c("xfce4-power-manager dpms-enabled"), "false", "xfce4-power-manager would switch the output off after 10 minutes "
         "and on wlroots the capture then fails"],
        [c("xfce4-power-manager inactivity-on-ac") + ", " + c("inactivity-on-battery"), "0", "Locked so as not to inherit what "
         "the user set"],
    ], "«TAB» — XFCE keys imposed on the session") + \
    p("<b>The panel.</b> " + c("xfce_panel_xml()") + " locks only the " + c("items") + " array of each " + c("actions") + " plugin "
      "(" + c("lock-screen") + ", " + c("switch-user") + ", suspend, hibernate, hybrid sleep, restart and shut down are turned "
      "from " + c("+") + " to " + c("-") + "; " + c("logout") + " stays) and, for every " + c("whiskermenu") + " plugin, the six "
      "keys " + c("show-command-lockscreen") + ", " + c("…switchuser") + ", " + c("…suspend") + ", " + c("…hibernate") + ", "
      + c("…restart") + ", " + c("…shutdown") + " set to false. The plugin ids come from the user's panel channel before "
      "birth, or from the standard " + c("default.xml") + " for a user with no panel yet. Declared limit (comment): an action "
      "button the user adds by hand during the session has a new id and is not locked in that session; it is locked from the "
      "next birth. There is no inhibition on XFCE: " + c("xfce4-session") + " does not consult the inhibitor when it logs out, "
      "so one would give a false sign in the log and no protection (" + c("session_inhibit()") + ").") + \
    p("<b>Only the leaf keys are locked, and the panel is checked.</b> In the lock files the nodes that are only the parent of a lock ("
      + c("plugins") + ", " + c("plugin-N") + ") are written as " + c("type=\"empty\"") + ", never as a value the user must own (the comment above "
      + c("xfce_panel_xml()") + "). The reason was seen: with a plugin's type in the lock, " + c("xfconfd")
      + " does not write into the user's file a value equal to the system's, so the user's file kept " + c("type=\"empty\"") + " and, "
      "once the lock was gone, the plugin had no type and the panel dropped it: the «actions» button vanished at the local login. "
      + c("xfce_panel_integrity()") + " runs at every birth (in " + c("xfce_session_xfconf()") + ") and repairs the "
      + c("/plugins/plugin-<id>") + " entries of a panel's " + c("plugin-ids") + " that have no type: from a copy still pending, or from the "
      "standard layout, but <b>only</b> for the two types REMOTIX locks (" + c("PLUGIN_ACTIONS") + ", " + c("PLUGIN_WHISKER")
      + ") because the number may belong to another plugin by now, and never while " + c("xfconfd") + " still holds the lock in memory ("
      + c("xfconfd_holds_lock()") + " reads " + c("/proc/<pid>/environ") + " looking for REMOTIX's folder; if it cannot tell, it does not write). "
      "It is silent when all is well.") + \
    p("<b>Programs that a remote session does not start.</b> " + c("session_autostart_cover()") + " writes, in the " + c("autostart")
      + " folder of REMOTIX's session folder (first in " + c("XDG_CONFIG_DIRS") + "), an entry with the same file name as the system's and "
      + c("Hidden=true") + ", so XFCE does not start the program. The list is " + c("SESSION_NOT_IN_REMOTE_AUTOSTART") + ": "
      + c("blueman.desktop") + " (Bluetooth is a device of the machine, not of the remote user, and the applet crashes now and then and "
      "covers the screen with the crash reporter's window) and " + c("xiccd.desktop") + " (colour profiles: at every login it asks colord "
      "to create a device, an action polkit gives to the seated user only, and a remote session met a password window of an "
      "administrator in the middle of the desktop, holding the keyboard and the pointer). It is deliberately <b>not</b> a polkit rule: colord's "
      "devices and profiles are one set for the whole machine, and granting the action to remote sessions would let any remote user touch "
      "the seated user's screen; a remote desktop has no monitor to profile anyway. An entry is written only if the system's one exists, "
      "otherwise only one of ours (marked " + c("X-REMOTIX") + ") of an earlier birth is removed. A " + c("Hidden=true") + " entry hides the file "
      "name wherever it is, so the user's own visible " + sysf("~/.config/autostart/blueman.desktop") + " is not started either (a differently "
      "named entry is). The code does not remove the cover at the end of the session: it goes with " + sysf("/run/user/<uid>") + "; with another "
      "session of the same user alive (ssh, lingering) it stays, harmless because no non-remote session reads that folder.") + \
    p("<b>The copy and the restore.</b> A lock on a single property has a price: at the first save of the channel, " + c("xfconfd")
      + " writes each locked key into the user's file as " + c("type=\"empty\"") + " and the user's value is lost. REMOTIX "
      "therefore keeps a <b>copy</b> of the user's value of each key it locks, before locking, and puts the values back at "
      "the end of the session (" + c("xfce_restore_keys()") + "). The copy goes to the user's state folder; if that cannot be "
      "written it goes to RAM under the runtime folder (declared, with the warning that a reboot takes it); if neither works the "
      "locks are applied all the same and the line says that the user's values will not come back and lists them. Keys that "
      "cannot be put back stay pending and keep their originals in the next copy. This and the one-time restore on LXQt are "
      "the two exceptions to «nothing permanent». " + c("xfconf-query") + " exits with zero even when the daemon refused and "
      "put the previous value back, so every write is re-read.") + \
    note("the locked-key mechanism depends on " + c("locked=\"<user>\"") + ": the comment in " + c("session.c") + " records that "
         + c("locked=\"*\"") + " locks nothing (measured 13 Nov 2026 with xfce4-session 4.20.2), and that before that date the "
         "code thought four keys were locked that were not. The copy file " + sysf("~/.local/state/remotix/xfce-chiavi")
         + " is not deleted after the restore, only marked as restored (comment in " + c("session.c") + "; PIANO.md lists its "
         "removal as an open refinement); the package's postrm removes it on purge.", "Lock syntax.")

# ═════════════════════════════════════════════════════════════════════════
# 9. LXQt
# ═════════════════════════════════════════════════════════════════════════
S9 = p("According to the comment in " + c("session.h") + ", Debian trixie packages no launcher for LXQt on Wayland (not "
       "re-verified for this manual; the code does not look for one): REMOTIX starts labwc itself "
       "with " + c("labwc -C <folder> -S '<primary>'") + ", where the primary client is " + c("lxqt-session") + " preceded by "
       "the same size step as XFCE. The wallpaper is made by " + c("pcmanfm-qt") + " from the output's size, which is why the "
       "output must have its size before the session starts (" + rif("How a session is born") + ").", lead=True) + \
    table(["Topic", "Behaviour", "Why"], [
        ["labwc's folder", c("write_config_labwc_lxqt()") + " writes " + sysf("$XDG_RUNTIME_DIR/remotix/labwc-lxqt/") + " with an "
         + c("rc.xml") + " (server-side decoration, the default key bindings without a screen lock, plus the «bring windows back "
         "inside» shortcut) and an <b>empty</b> " + c("autostart"), "With " + c("-C") + " labwc reads only that folder. The "
         "empty autostart keeps " + c("swayidle") + " and " + c("wlopm") + " out: they would switch off the captured output after "
         "a few minutes. If the folder cannot be written the session is not born, because labwc would then read the user's folder"],
        ["The session's commands", c("lxqt_session_commands()") + " writes two small scripts into REMOTIX's " + c("bin-lxqt")
         + " folder, at the head of " + c("PATH") + ": " + c("lxqt-leave") + " (turned into " + c("--logout") + ") and "
         + c("lxqt-powermanagement") + " (does nothing, logs a line). Each runs the real program <b>unless</b> the calling process "
         "is inside a logind session of the PAM service " + c("remotix") + " (asked of " + c("loginctl") + ", through " + c("timeout 3")
         + " when available)", "«Leave» then only logs out, and a local login on the same machine gets the normal programs. "
         "Nothing is written in the user's LXQt files"],
        ["X11 composition managers", "The same recipe, a script of the same name that logs a line and exits 0, for " + c("picom") + ", "
         + c("compton") + " and " + c("xcompmgr") + " (" + c("LXQT_X11_COMPOSITORS") + "), <b>only if the program is installed</b> (the script of "
         "an earlier birth goes if it is not)", "Their entry is an LXQt module without " + c("X-LXQt-X11-Only") + ", so with no X server to "
         "compose it dies, " + c("lxqt-session") + " restarts it up to " + c("MAX_CRASHES_PER_APP") + " times and shows «X Compositor crashed too many "
         "times». A module that exits 0 is not restarted, and the compositor the session has, labwc, is already there"],
        ["Autostart cover", c("blueman.desktop") + " and " + c("xiccd.desktop") + " with " + c("Hidden=true") + " (" + c("session_autostart_cover()")
         + ", as on XFCE)", "Same reasons as on XFCE (" + rif("XFCE: labwc and a locked xfconf") + "). On LXQt the user's own entry of the same name should "
         "win because the user's folder comes first; this was not measured"],
        ["Menu entries", c("settings_lxqt()") + " writes six " + c("Hidden=true") + ", " + c("NoDisplay=true") + " entries "
         "(" + c("lxqt-leave") + ", " + c("lxqt-lockscreen") + ", " + c("lxqt-suspend") + ", " + c("lxqt-hibernate") + ", "
         + c("lxqt-shutdown") + ", " + c("lxqt-reboot") + ") into REMOTIX's session-data folder at the head of " + c("XDG_DATA_DIRS")
         + ", then re-reads which file wins. «Log Out» stays", "A «Suspend» or «Lock screen» that logs out would be a lie. A "
         "file of the same name in the user's " + sysf("~/.local/share/applications") + " comes first and wins; it is said and "
         "not touched"],
        ["Idleness and lock", "Not written: " + c("lxqt-powermanagement") + " does not run in the session, and «Leave» only logs out",
         "LXQt has no " + c("PowerManagement.Inhibit") + ", so " + c("session_inhibit()") + " asks for nothing"],
        ["Environment", c("QT_QPA_PLATFORM=wayland") + ", " + c("QT_QPA_PLATFORMTHEME=lxqt") + ", " + c("XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots"),
         "See " + rif("The composed environment") ],
    ], "«TAB» — How LXQt is kept") + \
    p("<b>The one-time restore.</b> " + c("restore_user_settings_lxqt()") + " runs once per user (mark "
      + sysf("~/.local/state/remotix/lxqt-restored") + ") before the birth and removes only what is surely REMOTIX's, from earlier "
      "versions that wrote into the user's files: a " + c("lock_command_wayland=true") + " line, an " + c("enableIdlenessWatcher=false")
      + " line in a file that holds nothing else of the user's, the " + c("mainmenu") + " panel type, and menu stubs marked "
      + c("X-REMOTIX") + " that hold nothing but REMOTIX's lines (deleted only in that case, with one log line per file, by the "
      "owner's decision recorded in the comment). Anything else is left and said.") + \
    p("<b>Exit.</b> " + c("exit_lxqt()") + " calls " + c("org.lxqt.session.logout()") + " without waiting, because the method is "
      + c("Q_NOREPLY") + "; the verdict comes from " + c("wait_until_done()") + ". The comment still marks as unmeasured whether "
      "the polite request alone brings " + c("lxqt-session") + " (and so labwc) to exit within the ten seconds; if not, the force "
      "runs and the log says so. Before mounting the capture on labwc the child waits for the session manager to be on the bus: the "
      "comment records that without it, on LXQt, «Log out» made the session be born again 16 times out of 20.")

# ═════════════════════════════════════════════════════════════════════════
# 10. What the session imposes
# ═════════════════════════════════════════════════════════════════════════
S10 = p("One table to answer «where does REMOTIX write, for this desktop?». " + c("session_settings()") + " dispatches to "
        "the per-desktop code; the common rule is that everything lives under " + c("$XDG_RUNTIME_DIR") + " (gone with the user's "
        "runtime folder) and the user's own files are not touched, with the two exceptions in " + rif("The four desktops side by side")
        + ".", lead=True) + \
    table(["Desktop", "What is imposed", "Where it lives", "How it is verified"], [
        ["GNOME", "the keys of " + c("DCONF_KEYS") + " (value and lock), the keyboard layout, " + c("--headless --no-x11"),
         sysf("$XDG_RUNTIME_DIR/remotix/dconf/") + ", the drop-in in " + sysf("user.control") + ", the in-memory dconf layer",
         c("session_dconf_verify()") + " re-reads every key; the drop-in's " + c("ExecStart") + " is re-read"],
        ["KDE", "KIOSK " + c("[KDE Action Restrictions][$i]") + ": " + c("action/lock_screen") + ", " + c("action/start_new_session")
         + ", " + c("action/switch_user") + " false in " + c("kdeglobals") + "; " + c("BorderSize=Normal") + ", "
         + c("BorderSizeAuto=false") + " in " + c("kwinrc") + " (a starting point, written without " + c("[$i]") + ", so the user's "
         "own value wins); " + c("loginMode=emptySession") + " in " + c("ksmserverrc") + " (also a starting point); the screen "
         "inhibition to powerdevil; the start line's " + c("--no-lockscreen") + "; the ScreenSaver sidecar (not a setting: it only answers "
         "a question on the bus)",
         sysf("$XDG_RUNTIME_DIR/remotix/xdg/") + " (first in " + c("XDG_CONFIG_DIRS") + "), the drop-in, memory",
         c("write_kde_menu_rules()") + " logs each file; the drop-in is re-read"],
        ["XFCE", "the locked keys of " + c("XFCE_LOCKS") + ", the panel's action and whisker entries, labwc's " + c("rc.xml"),
         sysf("$XDG_RUNTIME_DIR/remotix/xdg-xfce/") + " and " + sysf("labwc-xfce/") + ", the " + sysf("xfconfd.service") + " drop-in; "
         "a copy of the user's values in the state folder",
         "every key re-read through " + c("xfconf-query") + "; the manager's environment for " + sysf("xfconfd.service") + " re-read; the panel's "
         "plugin types checked (" + c("xfce_panel_integrity()") + "); the autostart covers (" + c("blueman.desktop") + ", " + c("xiccd.desktop") + ")"],
        ["LXQt", "the labwc folder, the two command scripts, the scripts for the X11 composition managers that are installed, the autostart covers, six hidden menu entries",
         sysf("$XDG_RUNTIME_DIR/remotix/labwc-lxqt/")
         + ", " + sysf("bin-lxqt/") + ", " + sysf("data-lxqt/"), "the six entries are re-read (" + c("n/6 entries hidden, RE-READ") + ")"],
    ], "«TAB» — What the session imposes, per desktop") + \
    p("<b>KDE's powerdevil inhibition.</b> " + c("powerdevil_guard()") + " runs as a thread in the child: powerdevil's default "
      "is to switch the screen off after 10 minutes, which in a remote session means the desktop goes black. The thread waits for "
      + c("org.kde.Solid.PowerManagement") + " on the bus (it is not bus-activated and may appear late; the child has no GLib "
      "loop, so ownership is polled every " + c("POWERDEVIL_STEP_US") + " = 2 s for as long as the child lives; after "
      + c("POWERDEVIL_PATIENCE_S") + " = 120 s without powerdevil one warning line is written and the watch goes on) and calls " + c("PolicyAgent.AddInhibition") + " with type 4 each time the owner changes, so that "
      "a powerdevil restart is covered. The machine's own suspend is not handled here: it is refused by the package's polkit "
      "rule for all desktops. The comment also names the " + c("AllowSuspend=no") + " drop-in, but the package ships that one "
      "switched off in " + sysf("/usr/share/remotix/belts/") + " (" + c("debian/rules") + "); it holds only if the administrator "
      "puts it in force (" + rif("Security model") + ").") + \
    p("<b>The checks are the log.</b> For every desktop the lines of the " + c("session") + " area name each file written and "
      "each value re-read, with ⛔ when something is not in force (" + rif("Logging and diagnostics") + "). A desktop whose "
      "protection did not apply still starts, and says so: the rule in the comments is that a missing belt is declared, not "
      "silent.")

# ═════════════════════════════════════════════════════════════════════════
# 11. Behaviours worth knowing
# ═════════════════════════════════════════════════════════════════════════
S11 = p("What follows is what the maintainer will meet on the four desktops. Items marked «PIANO.md» come from the status of "
        "17 Nov 2026 in " + c("PIANO.md") + "; the others come from the code and its comments.", lead=True) + \
    table(["Desktop", "Behaviour", "Source and status"], [
        ["GNOME", "<b>The session is born in the Activities Overview</b>, which covers the desktop and holds the input, so the "
         "first thing a person sees and the first click go to the Overview. The check scripts ask the Shell (" + c("OverviewActive")
         + ") and press Escape before they test anything (" + c("prove/base-check.py") + " " + c("leave_overview()") + "). REMOTIX "
         "does not leave the Overview by itself.", "PIANO.md; the scripts in " + c("prove/") + ". The touch-mode failures on GNOME "
         "were of the check, not of the product; a residual case (1 in 13) where the first tap can land on the initial point if "
         "the pointer position arrives before Mutter is ready is unproven and rated low priority."],
        ["KDE", "<b>A Log Out can stop halfway</b> when systemd refuses to stop " + sysf("graphical-session.target") + ": REMOTIX "
         "finishes the stop itself (" + rif("Ending a session and tidying up") + ").", "Fixed on 17 Nov 2026 in "
         + c("session_kde_logout_watch()") + "; checked by the lifecycle script on the four containers."],
        ["KDE", "The Delete key held down is kept by the desktop (visible only in diagnostics).", "PIANO.md, one of the "
         "non-green results of the final run, listed there as explained (the desktop keeps the key); not investigated here."],
        ["XFCE", "<b>A Log Out requested while the desktop is still starting is ignored by XFCE</b>: nothing closes.",
         "PIANO.md, open point, described as the desktop's own behaviour. The code has no retry for it."],
        ["XFCE", "A window corner covered by the panel cannot be dragged.", "PIANO.md, final run (the panel sits over the corner)."],
        ["All", "The maximum canvas the container check reached was 3840×2160, the limit of the test browser's decoder.",
         "PIANO.md; see " + rif("Performance and capacity") + "."],
        ["GNOME", "The check that runs " + c("pkexec") + " gets an empty " + c("SHELL") + ", by design (the composed environment "
         "sets it empty).", "PIANO.md, final run."],
        ["GNOME, XFCE, LXQt, KDE", "The AppArmor profile of the network side is checked on every desktop by " + c("prove/check-apparmor.py")
         + ", which looks in the kernel journal for denials (and, in complain mode, for «allowed» lines of the profile) since the start of "
         "the round.", "The package installs the profile in complain mode; " + rif("Security model") + "; " + rif("Testing") + "."],
    ], "«TAB» — Behaviours of the four desktops") + \
    p("<b>Places that differ per desktop</b> (the list to walk when a fifth is added): " + c("recognize_desktop()") + ", "
      + c("desktop_name()") + ", " + c("compose_environment()") + ", " + c("write_dropin()") + ", " + c("start()") + ", "
      + c("inactive_unit()") + ", " + c("really_terminate()") + ", " + c("session_settings()") + ", " + c("session_inhibit()")
      + ", " + c("session_alive()") + " in " + c("session.c") + "; the capture, input and clipboard branches in " + c("child.c")
      + " (" + c("session_on_wlroots()") + " first, then KDE, then the Mutter default); and the cursor shape road. "
      + rif("Extending REMOTIX and porting to another distribution") + " has the general procedure.")

CHAPTER = ("The four desktops", [
    ("The four desktops side by side", S1),
    ("How the desktop is recognised", S2),
    ("The composed environment", S3),
    ("How a session is born", S4),
    ("Ending a session and tidying up", S5),
    ("GNOME: headless Shell and session dconf", S6),
    ("KDE Plasma: KWin nested in labwc", S7),
    ("XFCE: labwc and a locked xfconf", S8),
    ("LXQt: labwc folder and session commands", S9),
    ("What the session imposes, desktop by desktop", S10),
    ("Behaviours of the four desktops worth knowing", S11),
])
