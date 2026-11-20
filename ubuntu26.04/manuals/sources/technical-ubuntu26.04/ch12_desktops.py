from build import arrow, box, c, code, fig, flow, h4, note, p, rif, steps, sysf, table, tip, ul, warn, zone

# ═════════════════════════════════════════════════════════════════════════
# 1. The four desktops side by side
# ═════════════════════════════════════════════════════════════════════════
S1 = p("REMOTIX serves four Wayland desktops that belong to three compositor families; on Ubuntu 26.04 they are the four "
       "flavours Ubuntu (GNOME), Kubuntu (KDE Plasma), Xubuntu (XFCE) and Lubuntu (LXQt). Capture, input and clipboard "
       "talk to the <b>compositor</b>; birth, logout and settings talk to the <b>desktop</b>. XFCE and LXQt share "
       "labwc and therefore almost everything except the session. On KDE labwc is also present, but only as an "
       "invisible host for KWin, not as the desktop's compositor, and it is REMOTIX's own build of labwc, not the "
       "distribution's (" + rif("KDE Plasma: KWin nested in labwc") + "). Only Wayland sessions are served; X11 "
       "applications run through XWayland.", lead=True) + \
    table(["", "GNOME", "KDE Plasma", "XFCE", "LXQt"], [
        ["Compositor", "Mutter (inside " + c("gnome-shell") + ")", "KWin, nested in REMOTIX's own labwc",
         "labwc (wlroots), the distribution's", "labwc (wlroots), the distribution's"],
        ["Recognised by", c("gnome-session") + " and " + c("gnome-shell"), c("startplasma-wayland"), c("xfce4-session"),
         c("lxqt-session")],
        ["Started by", "the machine's GNOME session (" + c("gnome-session") + ", on Ubuntu the session " + c("ubuntu")
         + "), with the Shell's unit instance overridden by a drop-in", c("startplasma-wayland") + "; KWin's unit overridden to run "
         + c("remotix --kwin-nested"),
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
         + c("StopUnit") + " of " + c("plasma-workspace.target"), c("org.xfce.Session.Manager.Logout") + ", then SIGTERM to labwc",
         c("logout()") + " without waiting for a reply, then SIGTERM to labwc"],
    ], "«TAB» — The four desktops side by side") + \
    p("<b>Versions on Ubuntu 26.04.</b> The versions below are those of the Ubuntu 26.04 packages as read in the studies of "
      "this tree (" + c("studio/1-gnome50-avvio.md") + ", " + c("studio/3-sessione-ubuntu.md") + ", "
      + c("studio/4-mutter50-cattura-input.md") + ", " + c("studio/6-kubuntu-kwin-labwc.md") + ", "
      + c("studio/7-xubuntu-lubuntu.md") + ": packages opened in disposable containers) and, for dconf, on the virtual machine of "
      "the dconf measurements (" + c("docs/REGISTRO-problemi.md") + " C5). They were not read again on a running machine for "
      "this manual. GNOME: gnome-shell, mutter and gnome-session 50.1, libei 1.5.0, dconf 0.49. KDE: Plasma and KWin 6.6.7. "
      "XFCE: xfce4-session 4.20.4 and libxfce4windowing 4.20.5. LXQt: lxqt-session 2.3.0 and lxqt-panel 2.3.2. The labwc of the "
      "distribution, used by XFCE and LXQt, is 0.9.3; REMOTIX's own labwc is labwc 0.9.3 with wlroots 0.19.2 patched. systemd is "
      "259.9; the kernel of the live images on which the owner tried the release is 7.0 (REGISTRO C4). The display managers "
      "follow the flavour: GDM for Ubuntu, SDDM for Kubuntu and Lubuntu, LightDM for Xubuntu (dependencies read in studies 3, "
      "6 and 7; the login screens of Ubuntu and of Kubuntu were tried on live images, those of Xubuntu and Lubuntu were not, see "
      + rif("Local excludes remote and the session cap") + "). " + c("docs/DECISIONS-11.md") + " §11.8 names GNOME 46, KDE Plasma 6.1, "
      "XFCE 4.20 and LXQt 2.0 as minimums, taken from the catalogue of an earlier multi-distribution product that this tree does "
      "not have; all four desktops of Ubuntu 26.04 are above those numbers, and nothing in " + c("session.c") + " or in the "
      "package checks a minimum version.") + \
    p("<b>One desktop per machine.</b> REMOTIX looks for the desktop that is installed; it does not arbitrate between "
      "desktops that coexist (" + c("DECISIONS.md") + " §0.6). When two are found the choice is made and declared "
      "«ambiguous» (" + rif("How the desktop is recognised") + "). The package installs no desktop; with none of the "
      "four the server says so at startup (" + c("debian/control") + "). One case is new in this tree: XFCE or LXQt "
      "found on a machine without the package " + c("labwc") + " (a Recommends, so " + c("--no-install-recommends")
      + " leaves it out). " + c("session_missing_component()") + " says so before any child exists: the parent refuses the login "
      "after PAM's yes with " + c("0x0E") + " (" + c("delivery_verdict()") + " in " + c("main.c") + "), no process is spawned and "
      "no logind session is made (" + rif("Local excludes remote and the session cap") + "); the postinst also warns, at "
      "configuration time, on a machine that has XFCE or LXQt and neither GNOME nor Plasma.") + \
    p("<b>Whose settings these are</b> (" + c("DECISIONS.md") + " §8.2-bis, the rule of 13 Nov 2026). From the remote "
      "desktop the user may customise the desktop (look, themes, shortcuts, panels) and the changes stay, as they do "
      "locally. The user can never suspend, reboot, power off or lock the server. REMOTIX imposes its rules <b>only "
      "inside the remote session</b> and writes almost nothing in the user's settings: at the monitor the user finds "
      "everything as it was. The ban on suspend, reboot and power-off is the polkit rule of the package ("
      + rif("Security model") + ", " + rif("The package") + "); what the session imposes on the desktop's own settings "
      "is a belt that hides buttons and avoids false notices. Four exceptions remain in the code and are described "
      "below: on GNOME the small file " + sysf("~/.config/dconf/remotix") + " (the layout, three keys) and, while the session "
      "lasts, the empty file " + sysf("~/.local/share/gnome-shell/lock-warning-shown") + " (removed at the end if REMOTIX made it); "
      "on XFCE the copy and restore of a few locked keys; and a one-time restore of values written by earlier REMOTIX "
      "versions (GNOME and LXQt) (" + rif("What the session imposes, desktop by desktop") + ").")

# ═════════════════════════════════════════════════════════════════════════
# 2. Recognition
# ═════════════════════════════════════════════════════════════════════════
S2 = p(c("recognize_desktop()") + " in " + c("session.c") + " decides once per process, from the programs found in "
       + c("PATH") + ", and keeps the reason in words for the server's start line (" + c("session_desktop_explain()")
       + "). Parent and child both call it and must reach the same answer; they do, because both run on the same machine "
       "and read the same files. The parent searches the " + c("PATH") + " of the service; the child's " + c("PATH")
       + " is the one PAM composes for a login (" + rif("The composed environment") + "), so the agreement holds as long as the "
       "programs are in " + sysf("/usr/bin") + ", where Ubuntu packages them (comment of " + c("recognize_desktop()") + ").", lead=True) + \
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
        + sysf("/etc/systemd/system/display-manager.service") + " (" + c("active_display_manager()") + "); if it is another one, "
        "such as " + c("gdm3") + " (the Ubuntu flavour), the lightdm and sddm files are leftovers and are ignored. The session "
        "name is cleaned (" + c(".desktop") + " stripped, only " + c("[A-Za-z0-9._+-]") + ") and mapped to a desktop by "
        + c("desktop_of_session_name()") + ": the words " + c("xfce") + " or " + c("xubuntu") + " give XFCE, " + c("lxqt")
        + " or " + c("lubuntu") + " give LXQt, " + c("plasma") + ", " + c("kde") + " or " + c("kubuntu") + " give KDE, "
        + c("gnome") + " or " + c("ubuntu") + " give GNOME. They are asked in that order because " + c("xubuntu") + ", "
        + c("lubuntu") + " and " + c("kubuntu") + " contain «ubuntu»; the comment records the limit that " + c("ubuntu")
        + " as a substring also catches flavours outside the four supported ones (" + c("ubuntustudio") + ", "
        + c("ubuntu-budgie") + "). With no usable declaration the order of the table stays. The session a single user picks "
        "at login is not read.",
        "<b>Xubuntu has both GNOME markers.</b> With the Recommends accepted, a Xubuntu machine has " + c("gnome-shell")
        + " (50.1, pulled in by other packages even without Recommends) and " + c("gnome-session-bin") + " (which carries "
        + sysf("/usr/bin/gnome-session") + ", pulled in with the Recommends): it enters the branch of two or more desktops and is "
        "decided by lightdm's declaration " + c("user-session=xubuntu") + " (the file " + sysf("60-xubuntu.conf")
        + " of " + sysf("/usr/share/lightdm/lightdm.conf.d") + "). With " + c("--no-install-recommends") + " " + c("gnome-session")
        + " is not there and there is no ambiguity. Source: package contents simulated in a container (study 7 §3); the owner "
        "ran the release on the live Xubuntu image and reported that everything worked, without a log being read.",
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
        [c("XDG_CURRENT_DESKTOP"), c("DesktopNames") + " of the chosen session file (Ubuntu: " + c("ubuntu:GNOME") + ")",
         "not set by REMOTIX", c("XFCE"), c("LXQt:labwc:wlroots")],
        [c("XDG_SESSION_DESKTOP"), "the session file's name (" + c("ubuntu") + ")", "—",
         "as the active display manager would set it (" + c("add_session_names()") + "; fallback " + c("xfce") + ")",
         "same (fallback " + c("lxqt") + "); under sddm the " + c("DesktopNames") + " of the session file, so " + c("LXQt")
         + " for the session " + c("Lubuntu")],
        [c("DESKTOP_SESSION"), "the session name, when a local login would set it", "same", "same", "same"],
        [c("XDG_SESSION_TYPE"), c("wayland"), "—", c("wayland"), c("wayland")],
        [c("XDG_MENU_PREFIX"), "—", c("plasma-"), c("xfce-"), c("lxqt-")],
        [c("XDG_CONFIG_DIRS"), "only if the user manager (or the child) already has one, or the session has a folder",
         "REMOTIX's " + c("xdg") + " folder first", "REMOTIX's labwc folder first",
         "REMOTIX's LXQt folder first, then " + c("/etc:/etc/xdg:/usr/share")],
        [c("XDG_DATA_DIRS"), "only if the user manager (or the child) already has one, or the session has a folder (see below)",
         "same", "same", "REMOTIX's session-data folder first"],
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
        [c("SHELL"), "empty (so that " + c("gnome-session") + " does not re-run itself in a login shell)",
         "the user's login shell from passwd", "same", "same (qterminal falls back to /bin/sh without it)"],
        [c("DCONF_PROFILE"), "not set in the normal case: dconf reads " + sysf("$XDG_RUNTIME_DIR/dconf/profile") + ". Set only in the "
         "declared fallback (to the fallback's profile) and when an administrator's own variable exists (to REMOTIX's runtime file); "
         + rif("GNOME: headless Shell and session dconf"), "—", "—", "—"],
        [c("LANG") + " (a UTF-8 locale that exists), " + c("HOME") + ", " + c("USER") + ", " + c("PATH"), "yes", "yes", "yes",
         "yes, with REMOTIX's " + c("bin-lxqt") + " folder at the head of " + c("PATH")],
    ], "«TAB» — The composed environment") + \
    p("<b>The PATH is the one PAM gives to a login.</b> The child opens a PAM session with the service " + c("remotix")
      + " (" + rif("How a session is born") + ") and takes the " + c("PATH") + " that " + c("pam_env") + " composed from "
      + sysf("/etc/environment") + ": on Ubuntu that file holds " + sysf("/snap/bin") + ", the sbin folders and the games "
      "(comment of " + c("child_path_ok()") + "). The value is accepted only if it is a list of absolute folders, without a "
      + c("..") + " component, of plain characters and at most 400 long; otherwise the fixed fallback "
      + c("/usr/local/bin:/usr/bin:/bin") + " is used (" + c("become_and_exec()") + " in " + c("child.c") + "). " + c("src/remotix.pam")
      + " warns above its " + c("pam_env") + " line not to add " + c("user_readenv=1") + ": the user would then choose the "
      "session's " + c("PATH") + " from " + sysf("~/.pam_environment") + ".") + \
    p("<b>The session's own folders.</b> A local login of a session puts the session's folders in front of "
      + c("XDG_CONFIG_DIRS") + " and " + c("XDG_DATA_DIRS") + ". The system does it in one of two ways, and the rule of the code is "
      "to do what the system itself would do (comment above " + c("local_login_adds_folders()") + "): "
      + sysf("/etc/X11/Xsession.d/60x11-common_xdg_path") + ", where the login runs " + sysf("Xsession.d") + " at all (an X11 session "
      "file, or any session under lightdm), and " + sysf("/etc/profile.d/xdg_dirs_desktop_session.sh") + ", the same logic in "
      "profile form, which every login that reads " + sysf("/etc/profile") + " runs, notably " + c("gnome-session") + " itself, "
      "which on Wayland re-executes in a login shell (study 3 §2). Both exist on Ubuntu 26.04 (x11-common 1:7.7+26ubuntu1 and "
      "gnome-session-common, read from the packages). REMOTIX sets " + c("SHELL") + " empty, so nothing would run the scripts, and "
      + c("local_session()") + " does their work: it finds the session's name (GNOME: the session REMOTIX starts, " + c("ubuntu")
      + "; the other desktops: the session the display manager declares if it names the chosen desktop, else the first session file "
      "of that desktop that has a folder of its own), then " + sysf("/etc/xdg/xdg-<name>") + " and " + sysf("/usr/share/<name>")
      + " (never for " + c("gnome") + ") if they exist, and " + sysf("/usr/share/gnome") + " when the profile snippet and the folder are "
      "there and the desktop is GNOME or the session's local login is X11. REMOTIX's own folders stay in front, these come next, "
      "the system's after. On Ubuntu GNOME the session's data folder " + sysf("/usr/share/ubuntu") + " holds only entries that hide "
      "programs (such as the first-run assistant), and " + sysf("/etc/xdg/xdg-ubuntu") + " does not exist (study 3 §2.2, read from "
      "the packages). One log line (" + c("D-153") + ") states the session name, the config folder, the data folder and the common "
      "folder that were found. Declared differences from the real scripts: the config folder is added only if it exists, "
      + c("GDMSESSION") + " is not set, and " + sysf("~/.gnomerc") + " and " + sysf("~/.profile") + " are not run.") + \
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
    ("2 Drop-in", "GNOME Shell instance or KWin unit; none on labwc", "blue"),
    ("3 Guards", "manager not stopping; old session gone; stale pipewire-pulse", "navy"),
    ("4 Settings", "dconf, xfconf, kdeglobals, LXQt folders", "light"),
    ("5 start()", "setsid --fork sh -c, output to session.log", "blue"),
], "«FIG» — The steps of " + c("session_spawn()") + ", in order")

S4 = p("The server never starts a desktop itself. The per-user child (" + rif("Startup and life cycle") + ") does, from its "
       "loop: when the state of the session is «dead» and no birth was requested in the last " + c("BIRTH_REIN_MS")
       + " (12 s), it calls " + c("session_spawn()") + ", which returns at once. The desktop shows up on the bus on a "
       "later round and the child's retry loop (" + c("STAGE_BIRTH_RETRY_MS") + " = 200 ms while the compositor is "
       "unreachable) mounts the capture then. The blocking " + c("session_ensure()") + " with its 40 s wait ("
       + c("WAIT_STARTUP_MS") + ") still exists in " + c("session.c") + " but the product no longer calls it. Before any step, "
       + c("session_spawn()") + " returns without doing anything, and says why in the " + c("session") + " area, if no desktop was "
       "recognised or if " + c("session_missing_component()") + " names a missing compositor (" + c("labwc") + " for XFCE and LXQt): "
       "«I am not making anything be born».", lead=True) + \
    h4("The logind session") + \
    p("Before any desktop code runs, " + c("become_and_exec()") + " in " + c("child.c") + " opens a real logind session "
      "for the user with PAM: " + c("pam_start") + " with the service " + c("remotix") + ", " + c("XDG_SESSION_TYPE=wayland")
      + ", " + c("XDG_SESSION_CLASS=user"
      ) + ", no " + c("XDG_SEAT") + " (a session without a seat is headless by construction), the client's address as "
      + c("PAM_RHOST") + ", then " + c("pam_open_session") + ". The class must be " + c("user") + ": " + c("manager")
      + " is what lingering gives, and it is not enough for Mutter. " + c("pam_end()") + " is called <b>without</b> "
      + c("pam_close_session()"
      ) + ": logind keeps the session as long as the leader process lives, and the leader is the child after the "
      + c("exec") + ", so the stage outlives the client because the child outlives it.") + \
    p("On Ubuntu 26.04 nothing has to be carried across the " + c("execve") + ". The comment in " + c("become_and_exec()")
      + " records that since systemd 258 logind tracks a session by the pidfd of its leader, not by a fifo: " + c("pam_systemd")
      + " opens the pidfd of the calling process and returns a dummy descriptor, and the exit of the leader stops the session at "
      "once; the child keeps its pid across the " + c("execve") + ", so the session lasts as long as " + c("remotix-child")
      + " does. This tree is born with systemd 259.9 and no longer looks for the descriptor or passes " + c("--session-fd")
      + ". The comment states the limit: a logind older than 258 still in memory during an upgrade would hand " + c("pam_systemd")
      + " a fifo and the session would close at the " + c("execve") + "; the case is excluded on a freshly installed Ubuntu 26.04. "
      "Source: the code comment and study 5 §7.1 (systemd sources); the behaviour was not observed with an old logind.") + \
    h4("The steps of " + c("session_spawn()")) + BIRTH + \
    steps([
        "<b>Clear-out and snapshot.</b> " + c("session_clear_out_handler()") + " removes what a session that ended badly left "
        "in the user manager, then " + c("session_snapshot_handler()") + " writes the previous value of each variable "
        "REMOTIX is about to set (" + c("OUR_VARIABLES") + ") into " + sysf("$XDG_RUNTIME_DIR/remotix/manager-before")
        + " (" + rif("Ending a session and tidying up") + "). " + c("dconf_profile_reinstate()") + " then writes the session's "
        "dconf profile (or puts it back, if the end of the session before had neutralised it); in the new model this is where the runtime file is written for the first time, when the child's start found no live desktop (GNOME, "
        + rif("GNOME: headless Shell and session dconf") + "). The snapshot can be old after a close made from the root side: "
        "the root side's close does not delete it, so the next clean-up may take it for valid (" + c("docs/REGISTRO-problemi.md")
        + " E3, a known and non-blocking limit).",
        "<b>The drop-in</b> (" + c("write_dropin()") + "): " + sysf("zz-remotix-monitor.conf") + " in "
        + sysf("$XDG_RUNTIME_DIR/systemd/user.control/<unit>.d/") + " for GNOME's Shell unit and KWin's unit; nothing for "
        "XFCE and LXQt, where the compositor is not a unit. On GNOME the folder is the one of the <b>instance</b> "
        "(" + sysf("org.gnome.Shell@ubuntu.service.d") + ", or " + sysf("org.gnome.Shell@user.service.d") + "), never the template's, "
        "which would also apply to the Shell of the login screen. It is always <b>re-read</b> after " + c("daemon-reload")
        + " (" + c("systemctl --user show -p ExecStart") + "): if another drop-in wins, or " + c("--virtual-monitor")
        + " is still there, the birth is refused with a ⛔ line, because the session would have a monitor of its own and the "
        "user would watch an empty screen. If the drop-in is not in force the desktop is not born.",
        "<b>Guards.</b> The user manager must not be «stopping» (" + c("systemctl --user is-system-running") + ": a "
        "session born in a dying manager dies without writing anything). The previous session must be really over "
        "(" + c("inactive_unit()") + ", which on GNOME looks at three units, see " + rif("GNOME: headless Shell and session dconf")
        + "; the refusal line now names the unit that is still busy). A " + c("pipewire-pulse") + " older than the current "
        + c("pipewire") + " is a leftover and is stopped; its socket brings it back attached to the right " + c("pipewire")
        + ". The first two say no and return, and the child's retry loop tries again; the third does not stop the birth.",
        "<b>Settings</b> before the command, because " + c("gnome-session") + " starts the Shell first and a key written "
        "afterwards would hold only for the next session: " + c("session_dconf_birth()") + " and "
        + c("session_gnome_lock_warning()") + " on GNOME, then "
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
        ["GNOME", "the " + c("Exec") + " line of the chosen " + c("wayland-sessions/*.desktop") + " file (on Ubuntu "
         + c("/usr/bin/gnome-session --session=ubuntu") + ")", c("gnome_session()") + ": the candidates are the sessions whose "
         + c("Exec") + " launches " + c("gnome-session") + " and whose " + c(".session") + " file is installed. If there is only one, "
         "that one (stock Ubuntu: " + c("ubuntu") + "). If several, the one that bears the distribution's name (the " + c("ID")
         + " of os-release: " + c("ubuntu") + ", even when the universe package " + c("gnome-session") + " adds " + c("gnome")
         + "; the log says «it bears the distribution's name»), else " + c("gnome") + ", else the first in alphabetical order, as GDM "
         "does. If none, " + c("gnome") + " as a declared fallback"],
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
      "and the next login resumed it. Now the child dies of the signal on every desktop, the pidfd of the session's leader fires "
      "and logind closes the session (the scope has already been emptied). A compositor that dies by itself looks the same "
      "from outside and is treated the same way.") + \
    h4("The farewell is said before the stage is dismantled") + \
    p(c("session_over_early()") + " in " + c("child.c") + " (19 Nov 2026) sends " + c("MSG_SESSION_FINISHED") + " <b>before</b> the "
      "capture, input and clipboard are taken down, not after. The comment records the measurement that made it necessary (Ubuntu "
      "26.04 box, 18 Nov 2026): taking the stage down waits for PipeWire, whose " + c("module-rt") + " can be held for up to 25 s "
      "by a D-Bus call to RealtimeKit wherever " + c("rtkit-daemon") + " is installed but cannot start (containers, hardened "
      "machines), and the page stayed on the last image for 17 s without a word. It is said only on a <b>certain</b> death: "
      + c("session_life()") + " has three answers, " + c("SESSION_LIFE_ALIVE") + " (0), " + c("SESSION_LIFE_DEAD") + " (1: the bus "
      "answered and the compositor's name has no owner) and " + c("SESSION_LIFE_UNKNOWN") + " (2: no bus, a call failed or timed "
      "out), and only DEAD sends the farewell, because the farewell cannot be taken back. KDE is left out (" + c("stage_kwin")
      + "): a KWin restarted by systemd leaves its name without an owner for a moment, so «no owner» is not certain there. The "
      "parent also counts the child as «closing» from that message on, so a login in the meantime gets the true " + c("0x0E")
      + " «still closing» and never a desktop that is going away. " + c("session_alive()") + " is now " + c("session_life()")
      + " equal to ALIVE. When the input channel has closed and the answer is UNKNOWN, the child asks again, at most once a second, "
      "up to " + c("EIS_UNKNOWN_ROUNDS") + " = 3 rounds; if it stays UNKNOWN the old road holds (the stage is dismantled, with no "
      "early farewell). The reason, from the comment: at a logout the user's session bus itself goes away for a moment (" + sysf("dbus.service")
      + " is stopped by " + sysf("gnome-session-restart-dbus.service") + "), so UNKNOWN can come exactly when the session has just "
      "ended. " + rif("Ending a graphical session") + " has the life-cycle side.") + \
    h4("The product ends it") + \
    p(c("session_terminate()") + " calls " + c("really_terminate()") + ", which asks politely, waits, and then forces. The "
      "wait is " + c("wait_until_done()") + ": up to " + c("WAIT_EXIT_MS") + " = 10 s, polling every " + c("CHECK_INTERVAL_MS")
      + " = 500 ms, until " + c("session_alive()") + " is false and " + c("inactive_unit()") + " is true. Success is "
      "followed by " + c("session_clear_out_scope()") + " and " + c("session_clear_out_handler()") + ". If the desktop is "
      "already gone when " + c("really_terminate()") + " starts, the close counts as done only if " + c("inactive_unit()")
      + " agrees; if the session name is off the bus but units or processes of the desktop are still there, the log says so "
      "(«not claimed as closed») and the normal road goes on.") + \
    table(["Desktop", "Polite request", "Force", "The fact that decides"], [
        ["GNOME", c("org.gnome.SessionManager.Logout(1)") + " (no confirmation)", c("Logout(2)") + " (forced)",
         sysf("gnome-session-manager@<session>.service") + " (on Ubuntu " + sysf("@ubuntu") + "), " + sysf("gnome-session-restart-dbus.service")
         + " and " + sysf("graphical-session.target") + " all inactive"],
        ["KDE", c("org.kde.Shutdown.logout()") + " (not " + c("LogoutPrompt") + ", which asks for a confirmation nobody gives)",
         c("StopUnit(plasma-workspace.target, fail)") + " (there is no " + c("Logout(2)") + " on KDE)",
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
    h4("What is left in the user manager") + \
    p("What the product puts into the user's systemd manager outlives the session if the manager does (the test containers "
      "and any user with lingering enabled): the drop-ins under " + sysf("user.control") + " and the variables that "
      + c("gnome-session") + ", " + c("startplasma-wayland") + " or labwc export from the composed environment. A user "
      "who then logs in at the monitor would inherit them (on XFCE a «Log Out» that does not log out). The cure is "
      "four gestures:") + \
    ul([
        c("session_snapshot_handler()") + " at birth, before touching anything: the previous value of each variable in "
        + c("OUR_VARIABLES") + " (" + c("DCONF_PROFILE") + ", " + c("XDG_CONFIG_DIRS") + ", " + c("XDG_DATA_DIRS") + ", "
        + c("XCURSOR_THEME") + ", " + c("XDG_CURRENT_DESKTOP") + ", " + c("GDK_BACKEND") + ", the " + c("WLR_*")
        + " variables and the others in the list) goes into a file that exists as long as the manager does. The list has four "
        "entries that only appear with GNOME 50 (" + c("GNOME_DESKTOP_SESSION_ID") + ", " + c("QT_IM_MODULE") + ", "
        + c("QT_IM_MODULES") + ", " + c("XMODIFIERS") + "): the first process that has them is " + c("gnome-session-init-worker")
        + " (comment, read from " + c("/proc/<pid>/environ") + " of a live session on 18 Nov 2026), and with lingering they stayed "
        "in the manager after the Log Out.",
        c("session_clear_out_handler()") + " when the session is over (and at the child's start and at birth, for what a "
        "crash left): REMOTIX's drop-ins are removed with " + c("daemon-reload") + ", its variables are put back as they "
        "were or removed, " + c("xfconfd") + " is restarted if it had the session's folder, and on XFCE " + c("xfce_restore_keys()")
        + " puts the user's values back. A " + c("DCONF_PROFILE") + " that is REMOTIX's own, left in a manager that outlived an "
        "upgrade, is removed too (" + c("dconf_env_is_ours()") + "). Only with the session dead: with a live session it would "
        "pull the ground from under a working desktop. Without a snapshot (a manager born before) only variables carrying "
        "REMOTIX's mark are removed, and it is said. If the session still answers when the child leaves, the child retries for at most "
        + c("CLEAR_OUT_EXIT_WAIT_MS") + " = 2 s and otherwise leaves the work to the next child, with a ⛔ line.",
        c("session_dconf_neutralise()") + " (GNOME): a belt for when that clear-out is late. It is called by every road that ends "
        "a session (the user's logout, SIGTERM, the light close, the child's exit, and the root side's fork after a local login), "
        "and does three things: it removes the file " + sysf("lock-warning-shown") + " if REMOTIX made it, it neutralises the "
        "fallback's profile file, and it deals with the runtime profile as described in " + rif("GNOME: headless Shell and session dconf")
        + ". Never under a live desktop.",
        c("session_clear_out_scope()") + ": after the session has exited, what is left in the session's logind scope and "
        "belongs to the user (programs that detached from the session manager by D-Bus activation or a double fork) gets "
        "SIGTERM, then SIGKILL after 2 s. The comment records the case: after a XFCE logout, " + c("localsearch-3")
        + " and geoclue's agent stayed in the scope.",
    ]) + \
    warn("two places treat «I could not ask the desktop whether it is alive» as «it is closed»: the clean-up of the user manager "
         "(near " + c("session_alive()") + " in " + c("session.c") + ") and the child's exit (" + c("child.c") + "). The preparation "
         "of the session's dconf was corrected on 19 Nov 2026 to use the three answers; these two were not. It was not corrected "
         "because the cases are forced (an old snapshot, lingering and a failed birth together; a live desktop that does not answer "
         "at that very moment) and cannot be provoked on the bench (" + c("docs/REGISTRO-problemi.md") + " E3).",
         "Known limit.") + \
    h4("KDE: a Log Out that stops halfway") + \
    p("«Log Out» calls " + c("plasma-shutdown") + ", which stops " + sysf("plasma-workspace.target") + " and then asks the user "
      "manager to stop " + sysf("graphical-session.target") + ", which is what really stops KWin, plasmashell and the rest. If any "
      "unit has a start job queued at that moment (the comment names " + c("xdg-desktop-portal") + " in its first seconds), systemd "
      "refuses the stop («Transaction … is destructive»), plasma-shutdown ignores the refusal and exits, and the desktop stays up "
      "(" + c("docs/REGISTRO-problemi.md") + " D, Kubuntu 26.04, Plasma 6.6, 18 Nov 2026). The first remedy of 17 Nov watched "
      + c("plasma-workspace.target") + " seen <b>active</b> in this child's life and then not active while " + c("org.kde.KWin")
      + " is still on the bus. On Plasma 6.6 that signal never fires: " + c("plasma-shutdown") + " never stops the workspace target, "
      "so the logout was lost. It stays in the code as a second road.") + \
    p("The first road is now the name " + c("org.kde.Shutdown") + ". " + c("plasma-shutdown") + " owns it for the whole of its run and "
      "releases it when it exits. " + c("shutdown_name_listen()") + " subscribes to " + c("NameOwnerChanged") + " on a private GLib "
      "context that the watch turns at each round (a poll would miss a short run). A release alone is not a logout: "
      + c("plasma-shutdown") + " is also started to save the session and holds the name while an application asks «save changes?», "
      "and if the user cancels it exits without stopping anything. So after the release " + c("shutdown_released_judge()")
      + " asks " + c("ksmserver") + " (" + c("isShuttingDown") + "): <b>true</b> arms the watch; <b>false</b> (cancelled, or not a "
      "logout) or no answer forces nothing and writes one line, a choice recorded in the comment so as not to lose a user's unsaved "
      "work. After a grace of " + c("KDE_LOGOUT_GRACE_MS") + " = 4 s, in which the normal road wins if it works, the stop of "
      + sysf("graphical-session.target") + " is asked again every " + c("KDE_LOGOUT_RETRY_MS") + " = 3 s: " + c("KDE_LOGOUT_TRIES")
      + " = 10 attempts with mode " + c("fail") + " (as plasma-shutdown does), then up to 10 more with mode " + c("replace")
      + ", which passes even with a start job queued; one log line per attempt. After 20 refusals (about a minute) "
      + c("session_kde_logout_watch()") + " returns true (it returns a boolean for this purpose) and the child closes the session by the "
      "product's own road (" + c("terminate_and_clear()") + "), with the line «giving up on it». The function runs at every round of "
      "the child's loop and limits itself to one look per second.") + \
    p("Limits declared in the comment: " + c("logoutAndShutdown") + " and " + c("logoutAndReboot") + " of Plasma 6.6.7 do not "
      "release the name, so a power-off or reboot requested in the first seconds and refused would stay lost (reachable only "
      "without the menu entries, which REMOTIX removes); and a restart of KWin by its wrapper during the wait resets the request "
      "(rare). A lesson recorded in REGISTRO D: a first remedy, stopped in review and never "
      "released, closed the session as soon as plasma-shutdown started, so also with an unsaved document or after «Cancel». "
      "What the comment records as measured about ksmserver's answer: " + c("true") + " in the lost case, where it stays true until "
      + c("resetLogout") + "; one " + c("NoReply") + " was seen once, and that case forces nothing.") + \
    warn("whether a refused stop can also happen on other desktops was not investigated in the code; only KDE has this watch. "
         "On XFCE the register records the opposite case: XFCE refuses a Log Out requested while the session is still starting "
         "(«must be at rest»), seen on 17 and 18 Nov; the cure is the force after the ten seconds (" + c("kill_xfce()") + "), and "
         "the same behaviour was confirmed in the sources of xfce4-session 4.20.4 (study 7 §14). The code does not retry the "
         "polite request (" + rif("Behaviours of the four desktops worth knowing") + ").", "Scope of the KDE watch.")

# ═════════════════════════════════════════════════════════════════════════
# 6. GNOME
# ═════════════════════════════════════════════════════════════════════════
DCONF_FIG = flow([
    ("User's database", "user-db:user: writable, stays the user's", "light"),
    ("System database", "system-db:remotix: value and lock of 21 keys", "navy"),
    ("Session database", "user-db:remotix: the layout, written during the session", "blue"),
    ("The rest of the base", "other lines of the base profile, if any", "grey"),
], "«FIG» — The runtime profile of a GNOME remote session, top to bottom; the file starts with a line that marks it as REMOTIX's")

S6 = p("GNOME is started through the machine's own GNOME session (on Ubuntu 26.04 the session " + c("ubuntu") + "), with a systemd "
       "drop-in that makes " + c("gnome-shell") + " headless and without monitors: the only monitor is the virtual one that the "
       "capture creates with " + c("RecordVirtual") + ", and that is where GNOME puts its top bar and dock.", lead=True) + \
    h4("The session on Ubuntu 26.04") + \
    steps([
        "<b>Which session.</b> " + c("gnome_session()") + " chooses it as described in " + rif("How a session is born") + ": on stock "
        "Ubuntu the only candidate is " + c("ubuntu") + " (" + sysf("/usr/share/wayland-sessions/ubuntu.desktop") + ": " + c("Exec=/usr/bin/gnome-session --session=ubuntu")
        + ", " + c("DesktopNames=ubuntu;GNOME") + "), so " + c("XDG_CURRENT_DESKTOP") + " is " + c("ubuntu:GNOME") + ". The value matters: "
        "Ubuntu's defaults are gschema overrides keyed to " + c("ubuntu") + " in " + c("XDG_CURRENT_DESKTOP") + ", and with plain "
        + c("GNOME") + " the Shell would have Adwaita's look (comment in " + c("compose_environment()") + ", study 3 §4.1). The session file is "
        "read from the package and is not under REMOTIX's control.",
        "<b>Which Shell unit.</b> On GNOME 50 the Shell is a template, " + sysf("org.gnome.Shell@.service") + " (" + c("SESSION_UNIT_SHELL_MODEL")
        + "), whose instance is the mode: " + sysf("gnome-session@ubuntu.target") + " requires " + sysf("org.gnome.Shell@ubuntu.service")
        + ", " + sysf("gnome-session@gnome.target") + " requires " + sysf("org.gnome.Shell@user.service") + " (study 1 §3.3, read from the "
        "packages). " + c("unit_shell()") + " therefore asks the user manager for the " + c("Requires") + " of "
        + sysf("gnome-session@<session>.target") + " (" + c("systemctl --user show -p Requires --value") + ") and takes the instance "
        "that is not the template; if there is none it refuses, with a ⛔ line («I do not recognise the Shell unit»), and does not "
        "guess a name. The old name " + sysf("org.gnome.Shell@wayland.service") + " does not exist on Ubuntu 26.04.",
        "<b>The drop-in.</b> " + sysf("zz-remotix-monitor.conf") + " in the instance directory under "
        + sysf("$XDG_RUNTIME_DIR/systemd/user.control/org.gnome.Shell@ubuntu.service.d/") + " replaces " + c("ExecStart")
        + " with " + c("gnome-shell --headless --no-x11 --mode=%i") + ". The " + c("--mode=%i") + " is essential: the instance name "
        "is how the Shell learns its mode (the " + c("GNOME_SHELL_SESSION_MODE") + " variable is overridden by the option), and the mode "
        + c("ubuntu") + " is where the dock, the colours and the extensions live (the next paragraph). No root, gone at reboot, "
        "named " + c("zz-") + " so that it applies after any system drop-in. The checks of " + c("write_dropin()") + " are those of "
        "the previous section.",
        "<b>The previous session must be over</b>: " + c("inactive_unit()") + " asks three units of the user manager, "
        + sysf("gnome-session-manager@<session>.service") + ", " + sysf("gnome-session-restart-dbus.service") + " and, new with GNOME 50, "
        + sysf("graphical-session.target") + ", and says which one is busy. A session started while GNOME restarts the session "
        "bus dies without writing anything (the comment, measured 16 Aug 2026); with " + sysf("graphical-session.target")
        + " still active " + c("gnome-session-init-worker") + " aborts with «A graphical session is already running!» (comment, read in "
        "gnome-session's sources) while " + c("start()") + " would answer true all the same.",
        "<b>Capture and input</b> use Mutter's own D-Bus interfaces, not " + c("xdg-desktop-portal") + " (the portal asks "
        "permission from a user in front of the screen, which a session without a monitor cannot give). The order in "
        + c("mutter.c") + " is fixed and punished by different errors if permuted: " + c("RemoteDesktop.CreateSession")
        + ", " + c("ScreenCast.CreateSession") + " declaring " + c("remote-desktop-session-id") + ", "
        + c("RemoteDesktop.Session.Start") + ", " + c("RecordVirtual") + ", " + c("Stream.Start") + ". Keyboard and pointer "
        "go through libei (" + c("ConnectToEIS") + "); the clipboard through the same RemoteDesktop session. The size of "
        "the virtual monitor is part of the PipeWire negotiation, so a new size is a renegotiation (" + c("docs/LESSONS.md")
        + " §3 table, question 13; " + rif("Screen capture") + "). Study 4 reads in Mutter 50's sources that each monitor change "
        "republishes the stream's parameters (one more renegotiation after every resize) and that with libeis 1.5.0 the answer to a client's "
        + c("ping") + " leaves only when Mutter releases the event; this is not verified in the code of this manual.",
        "<b>The pointer.</b> Mutter delivers the cursor as metadata (" + c("cursor-mode=2") + "); " + c("cursor.c")
        + " turns it into the wire's " + c("CURSOR_SHAPE") + " and discards sizes the protocol forbids.",
    ]) + \
    p("<b>The Ubuntu mode and its extensions.</b> The mode " + c("ubuntu") + " is the file " + sysf("/usr/share/gnome-shell/modes/ubuntu.json")
      + " of the package " + c("gnome-shell-common") + ": " + c("parentMode") + " " + c("user") + ", the Yaru style sheet and the "
      "enabled extensions " + c("ubuntu-dock@ubuntu.com") + ", " + c("ubuntu-appindicators@ubuntu.com") + ", " + c("ding@rastersoft.com")
      + " (the icons of the desktop), " + c("tiling-assistant@ubuntu.com") + ", " + c("snapd-prompting@canonical.com") + ", "
      + c("snapd-search-provider@canonical.com") + " and " + c("web-search-provider@ubuntu.com") + " (study 3 §1.3, from the package; the "
      "extensions come from " + c("gnome-shell-ubuntu-extensions") + "). REMOTIX loads none of them and writes nothing about them: "
      "they arrive with the mode. The earlier tree recorded, on 30 Sep 2026, a remote Ubuntu 26.04 session with the dock on the "
      "left, the 26.04 wallpaper and the orange Home folder of the icons extension (study 3 §3.1); that was not repeated for this "
      "manual.") + \
    p("<b>Leaving and coming back.</b> The way out is " + c("Logout(1)") + " then " + c("Logout(2)") + " and the deciding fact is the "
      "three units above (" + rif("Ending a session and tidying up") + "). On the Ubuntu 26.04 container box " + c("rxu-gnome")
      + " (18 Nov 2026, study 12 §A) the Log Out asked 1, 2, 4 and 8 s after the desktop was ready ended with no session, no process "
      "and no runtime folder left in 48 attempts out of 48, from the page and from the desktop. The rejoin right after a Log Out "
      "was either admitted with a working desktop 1.5 to 2.9 s later or refused with the generic «could not open your session» text "
      "(" + c("0x0E") + ": the child is still closing); no blank screen was seen, and the guard of the three units never fired in the "
      "roughly 100 tests of that study, because the parent's rule on a closing child stops the rejoin first. Those runs predate "
      "the early farewell of 19 Nov 2026 (" + rif("Ending a session and tidying up") + ").") + \
    p("<b>The session is born in the Overview, and without the lock notice.</b> The first thing a person sees and the first tap go to "
      "the Activities Overview (" + rif("Behaviours of the four desktops worth knowing") + "). On the first desktop of any user, "
      "GNOME 50's Shell would also show «Screen Lock disabled», because a session without GDM has no screen lock: the Shell "
      "touches " + sysf("lock-warning-shown") + " in its data folder and, only if it has just created it, shows the notice. "
      + c("session_gnome_lock_warning()") + " makes that empty file first, at birth, before the Shell starts. This is one of the four "
      "writes in the user's home (" + rif("The four desktops side by side") + ") and the product's rule is that the session leaves nothing "
      "of its own there: a sign in " + sysf("$XDG_RUNTIME_DIR/remotix/lock-warning-made") + " records the inode and ctime of the file, "
      "whether REMOTIX also made the folder, and the folder's path, because the end of the session may be done by another process "
      "(the child that exits, the root side's fork). " + c("session_dconf_neutralise()") + " removes the file only if it is still "
      "that same empty regular file, without following links, and removes the folder only if REMOTIX made it and it is empty; "
      "otherwise it says that the file was left alone.") + \
    h4("The session's dconf (D-015)") + \
    p("What the session imposes on GNOME is a table of keys, " + c("DCONF_KEYS") + " in " + c("session.c") + ": 24 keys, 21 with a "
      "value and a lock and three with the lock only (the keyboard layout, whose value changes during the session). The Shell and "
      "the " + c("gsd-*") + " daemons read them through dconf; the user's own file " + sysf("~/.config/dconf/user") + " must never "
      "be written. Since 19 Nov 2026 the rules reach the session in the following way, which is <b>different from the model of "
      "the Debian 1.0.0 release</b>; that model survives, as a declared fallback, further down.") + \
    p("<b>Why the model changed.</b> " + c("docs/REGISTRO-problemi.md") + " C5: on the first real Ubuntu 26.04.1 live image (19 Nov "
      "2026) the live installer showed «Something went wrong» (" + c("Unknown DConf source") + ") and the Firmware Updater and the "
      "Security Center said " + c("No DConf source to write to") + "; the desktop opened all the same. The 1.0.0 model put a profile "
      "of three layers (" + c("file-db") + " and " + c("service-db") + " lines) under " + sysf("$XDG_RUNTIME_DIR/remotix/dconf/")
      + " and pointed " + c("DCONF_PROFILE") + " at it. The Flutter programs of Ubuntu have a dconf reader of their own that knows "
      "only " + c("user-db") + " and " + c("system-db") + " and, at any other line, drops the whole profile (the measurement lists the "
      "strings of the program's " + c("libapp.so") + ", among them «Unknown DConf source» and «No DConf source to write to»: "
      + c("/media/REMOTIX-UBUNTU/log/dconf-misure/q2-strings.txt") + " on the dev server), and a confined snap has another "
      + c("XDG_RUNTIME_DIR") + " and cannot even open a profile under REMOTIX's folder. The containers had no snaps and AppArmor "
      "did not act in them, and Debian does not have those programs, which is why it had not been seen before. After the change the "
      "journal of the same live had zero such errors and the installer started in the remote session without an error (state "
      "«WAITING»; " + c("docs/STORIA-ubuntu-26.04.md") + ", 19 Nov 2026).") + \
    table(["Piece", "What it is", "Who makes it, and when"], [
        ["Keyfiles", sysf("/usr/share/remotix/dconf/remotix.d/00-remotix") + " (values) and " + sysf("locks/00-remotix")
         + " (the list of locks)", "Generated <b>at build time</b> by " + c("remotix --dconf-keyfiles DIR") + " (" + c("session_dconf_keyfiles_write()")
         + ", called from " + c("main()") + "; " + c("debian/rules") + "), from the same table " + c("DCONF_KEYS")
         + " the program uses: there is no second list to keep in step (" + c("dconf_keyfile_texts()") + ")."],
        ["System database", sysf("/etc/dconf/db/remotix") + " (mode 0644)", "Compiled by the <b>postinst</b> with " + c("dconf compile")
         + " to a temporary file and renamed (programs of a live session may have the old one open). The <b>service</b> checks it at "
         "every start: " + c("session_dconf_system_db_ensure()") + ", called at the start of " + c("rootside_main()") + ", compiles "
         "to a temporary file and replaces the database only if the bytes differ (the compiler is deterministic; dates would not "
         "see an old database compiled after the package was built). Root runs " + c("/usr/bin/dconf") + " by absolute path, never a " + c("PATH") + " search. Before compiling it removes the "
         + c("remotix.new.*") + " files a failure left in " + sysf("/etc/dconf/db") + "; it does nothing if the package's keyfiles are missing; if "
         + c("/usr/bin/dconf") + " is missing and the database exists it stays silent, and if it is missing too it warns and the sessions use the "
         "fallback; if the compilation fails with the database present it warns and the sessions use the database that is there. Said in the log "
         "with ⭐ or ⚠. Removed by the postrm at remove, purge and disappear."],
        ["Runtime profile", sysf("$XDG_RUNTIME_DIR/dconf/profile"), "The file dconf reads when " + c("DCONF_PROFILE") + " is not set. "
         "Written at <b>birth</b> (" + c("dconf_profile_reinstate()") + ") and, in one case, at the child's start (below). First "
         "line: the mark " + c("# REMOTIX-RUNTIME-PROFILE (D-015, 19 Nov 2026)") + " followed by a descriptive text, and by the sign "
         + c("[referenced by DCONF_PROFILE: rewrite, never remove]") + " when an administrator's variable points to the file; then the first source of the user's base profile "
         "(normally " + c("user-db:user") + "), " + c("system-db:remotix") + ", " + c("user-db:remotix") + ", then the other lines of the base."],
        ["Session database", sysf("~/.config/dconf/remotix") + " = " + c("user-db:remotix"), "Written by the dconf service as the writer "
         + sysf("/ca/desrt/dconf/Writer/remotix") + " (" + c("session_dconf_object()") + ", " + c("dconf_change()") + "): the layout, "
         "keys " + c("sources") + ", " + c("current") + ", " + c("mru-sources") + " of " + c("org.gnome.desktop.input-sources") + " (" + rif("Input")
         + "). Emptied at every birth (" + c("session_dconf_reset()") + "), then the user's real values are copied into it."],
    ], "«TAB» — The pieces of the session's dconf") + DCONF_FIG + \
    p("A lock in a database hides the layers above it and cannot be written by the session. The top layer " + c("user-db:user")
      + " stays the writable one, so a wallpaper, a theme or a shortcut changed from the remote desktop stays and is there at "
      "the monitor (comment of the code). REGISTRO C5 records the " + c("user") + " file as identical after the test sessions, and the "
      "sha256 of " + c("~/.config/dconf/user") + " read after the logout was the same in five test cycles on the measurement machine "
      "(" + c("ciclo5.out") + " to " + c("ciclo7.out") + ", " + c("ripiego.out") + " and " + c("t2.out") + " in " + c("/media/REMOTIX-UBUNTU/log/dconf-correzione/")
      + " on the dev server). The "
      "twenty-one keys with a value get it from " + c("system-db:remotix") + "; the three lock-only keys of the layout take their value "
      "from " + c("user-db:remotix") + ", below the lock. On the stock Ubuntu there is no " + sysf("/etc/dconf/profile/user") + ": the base "
      "profile is the default alone, and the log says «base profile: user-db:user» (study 3 §4.1; the measurement logs).") + \
    p("<b>No " + c("DCONF_PROFILE") + ".</b> In the normal case the variable is not set in the child's environment (" + c("session_dconf_prepare()")
      + " removes it), not in the environment composed for the session and not in the user manager. The reason, from the comment: "
      "a confined snap has another runtime folder, does not see the file and uses the plain " + c("user-db:user") + ". Exceptions: <b>an administrator's own " + c("DCONF_PROFILE")
      + "</b>, if it is in the child's environment or only in the user manager's (for example " + sysf("environment.d") + "), stays the "
      "<b>base</b> profile (" + c("dconf_base_profile()") + " reads it as dconf would: an absolute path, or a name looked for in " + sysf("/etc/dconf/profile") + " and in "
      + sysf("<XDG_DATA_DIRS>/dconf/profile/<name>") + "), and in the session the variable is set to REMOTIX's runtime file, otherwise dconf would ignore it. The first line of the "
      "runtime file then also carries " + c("[referenced by DCONF_PROFILE: rewrite, never remove]") + ": a variable that points at a "
      "missing profile would mean no settings at all, so the end of the session rewrites the file and never removes it. The case "
      "of a variable only in the user manager was seen once, in a test on the Ubuntu virtual machine (" + c("docs/REGISTRO-problemi.md")
      + " E3); the case of a variable in the child's own environment is <b>verified by reading the code only</b>.") + \
    p("<b>What the child does at its start.</b> The runtime file is a window onto every program of the user, a local login included, "
      "so a child that dies between its start and the birth must not leave it. " + c("session_dconf_prepare()") + " therefore asks "
      + c("session_life()") + " and acts on the three answers (REGISTRO C5, «life of the desktop at the child's start»):") + \
    table(["session_life()", "What happens to the runtime file", "Log"], [
        [c("ALIVE"), "A live remote desktop is there for this child to serve (a child that finds one again): the file is written at once.", "No line of its own: the line «SESSION dconf in …» is written in all three cases (after the DEAD line in " + c("t2.out") + ")"],
        [c("DEAD"), "A runtime file of ours left behind by an earlier run is neutralised (removed, or the base alone); the birth writes the file.",
         "«no live remote desktop at the child's start … written at the birth, not now»"],
        [c("UNKNOWN"), "Nothing is touched: not written, not removed. The birth writes it if it is not there.",
         "«the desktop's life is UNKNOWN at the child's start»"],
    ], "«TAB» — The three outcomes of the question about the desktop's life") + \
    p("The DEAD branch was seen in the tests (a service restart with a live desktop: the file was removed when the child exited and "
      "written again at the next birth, " + c("t2.out") + " of the same folder). The ALIVE branch is the case of a child that finds a live desktop "
      "again (the comment's words); it was not provoked as such in the tests that were read. The UNKNOWN branch is <b>verified by reading the code only</b>: it was not provoked on the bench "
      "(REGISTRO C5).") + \
    p("<b>The end of the session.</b> " + c("session_dconf_neutralise()") + " works on the runtime file with no memory of the child: it "
      "touches the file <b>only</b> if its first line is the mark, so it can run in the root side's fork and in a close-only child. It "
      "reads the base profile from the file itself, without REMOTIX's lines. If the base is the default alone (and the file is not "
      "marked as referenced) the file is <b>removed</b>: an absent file is exactly what a local login had before REMOTIX came, and "
      "nothing stays that could change a later local session. Otherwise it is rewritten, through a temporary file and a rename, "
      "with the base alone under a head that still carries the mark. The log says «REMOVED» or «NEUTRALISED», and ⛔ if it could "
      "not. It is never done under a live desktop. On the measurement machine the file was gone after the logout and in the same "
      "second as the close for a local login on the live Ubuntu image (" + c("docs/STORIA-ubuntu-26.04.md") + "). The runtime file is "
      "written at birth and not earlier, so a child that dies before the birth leaves nothing; a child that dies <b>after</b> the "
      "birth leaves the file until the root side closes the orphan desktop, by the road of the light close, which runs the belt "
      "as the user.") + \
    p("<b>A foreign file between the child's start and the birth.</b> If a runtime profile that is not REMOTIX's (no mark) appears after the "
      "child has started and before the birth, " + c("dconf_profile_reinstate()") + " does not touch it: the session is born <b>without</b> "
      "REMOTIX's locks and without its database, and the log says «exists and is NOT ours (no mark): left alone, so the session is born "
      "WITHOUT our locks and our database» with ⛔.") + \
    h4("The declared fallback") + \
    p("The model of the Debian 1.0.0 release is kept for the cases in which the new one cannot hold, and every use of it is said in the "
      "log as «DECLARED FALLBACK, D-015 (19 Nov 2026)». It has two levels. <b>First level</b>, when "
      + sysf("/etc/dconf/db/remotix") + " is missing or not readable, or when a runtime profile that is not REMOTIX's (no mark on its first "
      "line) is already there (that file is never overwritten, removed or rewritten, and it is taken as the base): the child writes "
      + sysf("$XDG_RUNTIME_DIR/remotix/dconf/profile") + ", a profile of three layers, compiles the locks at its start with " + c("dconf compile")
      + " and sets " + c("DCONF_PROFILE") + " to the profile in the child and in the session:") + \
    table(["Layer (top to bottom)", "What it holds", "Written by the session?"], [
        [c("user-db:user"), "the user's own database " + sysf("~/.config/dconf/user"), "yes, and it stays"],
        [c("file-db:…/remotix/dconf/locks.db"), "the keys REMOTIX imposes, value and lock, compiled when the child starts with "
         + c("dconf compile") + " (" + c("dconf_compile_locks()") + "), to a temporary file and renamed, never deleted while the session lives",
         "no: a lock hides the layers above it"],
        [c("service-db:shm/remotix"), "an in-memory database (tmpfs, never " + sysf("~/.config") + "): the keyboard layout",
         "yes, by " + c("input_layout()") + " in " + c("input.c")],
        ["the rest of the user's base profile", "system databases", "no"],
    ], "«TAB» — The three layers of the fallback profile") + \
    p("<b>Second level</b>, when the " + c("dconf") + " program is missing from " + c("PATH") + " (" + c("dconf-cli") + " is a Recommends), or "
      "when " + c("dconf compile") + " fails: without the program " + c("dconf_compile_locks()") + " cannot run, " + c("dconf_locked")
      + " stays false and the session takes the last branch of " + c("session_dconf_prepare()") + ": the profile is the in-memory layer on top and the "
      "user's databases below, with <b>no lock at all</b>. The keys that have a value are written into the in-memory layer at the birth, but "
      "nothing prevents the user from changing them (for example " + c("scaling-factor") + " is not locked), nothing goes in the user's file, "
      "and what the user changes from the remote desktop is lost at the next birth. In this level the user's keyboard layout is not copied "
      "into the session (that branch of " + c("session_dconf_birth()") + " does not do it) and it does not need to be: without locks the "
      "user's values are read from the layer below, and the negotiated layout is written into the in-memory layer. Without the "
      "program the one-time cleanup warns and waits. (Read in the code; "
      "not provoked on a machine.) A mandatory profile in " + sysf("/run/dconf/user/<uid>") + " wins over any profile and over "
      + c("DCONF_PROFILE") + ": the locks cannot hold, and it is declared; the session is then born without them and the layout is not "
      "written. The fallback profile is neutralised at the end like the runtime one (only the file, " + c("locks.db") + " stays). On the "
      "measurement machine the fallback was provoked by taking the database away: the same twenty-one keys were in force and the profile "
      "was neutralised after the logout (" + c("ripiego.out") + " in the same folder). The comments of the code that describe dconf's behaviour "
      "(only the first source is written, a lock hides the sources above it, a recompiled " + c("file-db") + " is not seen by programs already "
      "open) carry the mark of dconf 0.40, the version of Debian 13, and were not re-measured on 0.49; Ubuntu 26.04 has 0.49, and the model "
      "above was measured on it.") + \
    p("<b>One-time cleanup.</b> " + c("session_dconf_restore_once()") + " (called by " + c("session_dconf_birth()") + ", in the new model and in the "
      "fallback) removes from the user's own dconf, once, the four keys that older REMOTIX versions wrote there (the two power-sleep "
      "types, " + c("idle-delay") + " and " + c("lock-enabled") + "), if they still hold exactly those values. The mark is "
      + sysf("~/.local/state/remotix/gnome-ripristinato") + "; without the " + c("dconf") + " program nothing is done and no mark is written. "
      "No earlier REMOTIX was distributed on Ubuntu, so in this tree it matters only for a machine where an older build was tried. The "
      "postrm removes the mark at purge.") + \
    p("<b>Verification.</b> After the birth nothing is written: " + c("session_dconf_verify()") + " <i>re-reads</i> every key through the "
      "session profile, as the Shell and the " + c("gsd-*") + " daemons do, and says whether it is in force («session keys re-read: 21 in "
      "force, 0 NOT» on the measurement machine, in the new model and in the fallback). Every schema and key is looked up before use, "
      "because " + c("g_settings_new()") + " on a missing schema aborts the process (the comment records a child dead of SIGTRAP from a "
      "key renamed between GNOME versions).") + \
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
        [c("org.gnome.desktop.screensaver ubuntu-lock-on-suspend"), "false", "Ubuntu's own key: lock when suspending; the Shell's "
         + c("lock()") + " would revoke capture"],
        [c("org.gnome.desktop.interface scaling-factor"), c("uint32 1"), "The integer scale is 1 in the remote session (next paragraph)"],
        [c("org.gnome.desktop.input-sources") + " " + c("sources") + ", " + c("current") + ", " + c("mru-sources"),
         "the negotiated layout, from " + c("user-db:remotix") + " (" + c("shm") + " in the fallback)", "Lock only; " + rif("Input")],
    ], "«TAB» — The GNOME keys imposed on the session") + \
    p("<b>The scale.</b> The input's coordinate space is the logical monitor's layout, and with a scale other than 1 the layout and the "
      "stream's pixels diverge: with " + c("scaling-factor") + " 2 the layout of a 2133-pixel canvas becomes 1067 × 2 = 2134 and the pointer goes "
      "elsewhere without any line saying so (measured 14 Aug 2026, comment of " + c("mutter.h") + "). The first cure is the key above, "
      "locked to 1: the user's file is not touched and at a local login they find their own value again. The safety net is in the "
      "child (guard 2 of " + c("DECISIONS.md") + " §5.0-sexies): if the scale read from Mutter for REMOTIX's monitor is not 1, the child makes "
      "<b>one</b> attempt, " + c("mutter_scale_to_one()") + ", with " + c("ApplyMonitorsConfig") + " method 1 (temporary, never "
      + sysf("monitors.xml") + ") and only in the plain case of one logical monitor, which is ours, with one monitor; three synchronous "
      "D-Bus calls of up to " + c("WAIT_CALL_MS") + " = 15 s each, so about 45 s at worst, only in a broken Mutter. If the scale re-read is "
      "not exactly 1.0 the stage is refused: " + c("MSG_STAGE") + " carries " + c("fatal") + " = 1, the parent sends " + c("0x0E")
      + " to every login of that user (" + c("stage_refused_by_child()") + " and " + c("wt_dismiss_user_session_over()") + ", "
      + rif("Local excludes remote and the session cap") + "), and the child closes the graphical session, retrying every 10 s if "
      "that fails, instead of remounting the stage for ever in front of a black page. The likely causes the log names when the "
      "net is needed are a scale saved in " + sysf("~/.config/monitors.xml") + ", a mandatory dconf profile of the administrator, or the "
      "fallback without " + c("dconf compile") + ". A scale that could not be read is not taken for 1.0: the child goes on and says "
      "so.") + \
    h4("Known limits of the session's dconf") + \
    ul([
        "<b>A child that dies after the birth</b> leaves the runtime file until the root side closes the orphan desktop (the light "
        "close runs the belt as the user). A local login of a user with no known REMOTIX session does not run the belt, because that would "
        "need a new fork as that user; the probability is low, since the file now exists only after a birth (REGISTRO C5, limit 1).",
        "<b>A hot upgrade</b> with a desktop born by the old model: its programs go on reading the in-memory layer while a new child writes "
        "the database " + c("remotix") + ", so a keyboard layout change does not reach that desktop until the next birth. The old model was "
        "never distributed on Ubuntu (limit 2). The clean-up of the user manager also removes a " + c("DCONF_PROFILE") + " that an earlier "
        "version of the package left in a manager that outlived the upgrade.",
        "<b>The purge</b> removes " + sysf("~/.config/dconf/remotix") + " as the user, only that regular file (a link is not followed, "
        + c("user") + " and the folder are never touched); a user the system does not list at that moment, for example a network home that is "
        "down, keeps it, and it is inert without REMOTIX (limit 3; " + rif("Removal: prerm, postrm and purge") + ").",
        "<b>The profile is in the runtime folder,</b> so any program born in the meantime with that folder reads it, not only those that "
        "inherited a variable as before; the mandatory profile still wins and is declared.",
        "<b>A foreign runtime profile</b> that appears between the child's start and the birth leaves the session without the locks "
        "and the database (above).",
        "<b>Not proven in the field:</b> the UNKNOWN branch at the child's start (in the new model and in the fallback), the branch of "
        "the database that is different or older at the service's start (only «missing» was tried), the case with no " + c("dconf")
        + " program at all, and an administrator's variable in the child's own environment. They are <b>verified by reading the code "
        "only</b> (REGISTRO C5).",
        "<b>The manager's snapshot</b> can be old after a close made from the root side, and the question «is the desktop alive» treats an "
        "unanswered question as «closed» in two places (REGISTRO E3, " + rif("Ending a session and tidying up") + ").",
    ]) + \
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
    + box(40, 188, 520, 50, "REMOTIX's labwc, without a screen", "headless output W×H at 240 Hz; a 1×1 ticker every 16 ms", "grey")
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
       + " mode, which starts <b>REMOTIX's own labwc without a screen</b> and then becomes KWin, running as a window inside that labwc "
       "(" + c("DECISIONS.md") + " §10.40). The desktop is KWin's single output; KWin's output follows the size of its window; "
       "the window follows labwc's output. To change the desktop's size at a reattach, REMOTIX changes the size of labwc's "
       "output. On Ubuntu 26.04 this is Kubuntu: Plasma and KWin 6.6.7 (" + rif("The four desktops side by side") + ").", lead=True) + \
    code("[Service]\n"
         "ExecStart=\n"
         "ExecStart=/usr/libexec/remotix/remotix --kwin-nested 1920 1080 /dev/dri/renderD128 -- /usr/bin/kwin_wayland_wrapper --xwayland --width 1920 --height 1080 --no-lockscreen",
         "text", "The KWin drop-in written by write_dropin(), for a 1920×1080 canvas (the binary path is " + c("/proc/self/exe") + ")") + \
    KDE_FIG + \
    h4("Our own labwc (KDE)") + \
    p("The labwc that hosts KWin is <b>not</b> the distribution's. " + c("build/labwc-ospite/README") + " gives the reason: KWin 6.5 and later "
      "draws a single black pixel as the root of its window and puts the content in subsurfaces; wlroots never reports that root as "
      "«presented», KWin gives its clients a frame clock stuck at 0, and Firefox takes its window for covered and stops painting. The "
      "fix is a few lines in wlroots (" + sysf("types/scene/surface.c") + ", the " + c("frame_done") + " handler: the root of a surface shown on an output "
      "counts as presented at every output frame; " + c("wlroots-0.19.2-remotix-presented-root.patch") + "). Study 6 checked that the wlroots "
      "source of Ubuntu 26.04 is byte for byte the upstream 0.19.2 file, that upstream's master and 0.20.0 do not have the fix, and "
      "that the earlier tree had seen the symptom with the distribution's labwc on this very release: the windows of a KDE session "
      "stayed on their first frame and the picture came one to three seconds late. So the package carries labwc 0.9.3 "
      "with wlroots 0.19.2 patched, <b>linked statically</b>, as " + sysf("/usr/libexec/remotix/labwc") + ": the sources are pinned with "
      "their sha256 in " + c("build/labwc-ospite/VERSIONS") + ", " + c("build/labwc-ospite/build.sh") + " fails if the binary links any "
      + c("libwlroots") + ", and the build packages are in " + c("debian/control") + " (" + rif("Our own labwc (KDE)") + " has the build and "
      "licence side). The path is fixed at build time: " + c("LABWC") + " in " + c("src/Makefile") + " becomes " + c("-DREMOTIX_LABWC")
      + ", and " + c("debian/rules") + " passes " + c("LABWC_PATH") + ". XFCE and LXQt use the distribution's labwc, and the " + c("labwc")
      + " Recommends of the package serves only them.") + \
    table(["Choice", "Why (from the comments of " + c("kwin.c") + " and " + c("docs/LESSONS.md") + ")"], [
        ["Not " + c("kwin_wayland --virtual"), "The comments record, measured on Debian with KWin 6.3.6, that KWin cannot resize a " + c("--virtual")
         + " output and cannot create a second one; the mode is constant and the list fixed in the constructor (" + c("docs/LESSONS.md")
         + " §3 table, question 13). The desktop would keep its birth size and a reattach from another window size would get a rescaled "
         "picture. This was not measured again with KWin 6.6.7 on Ubuntu 26.04 (not verified there); the nested design is unchanged."],
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
        "It checks that " + c("REMOTIX_LABWC") + " (the path fixed at build time) is executable, and starts that labwc, never the "
        "distribution's. If it is not there, the session is still born: the helper runs the KWin wrapper with " + c("--virtual")
        + " added and writes " + c("⛔ our labwc is not installed: KWin --virtual, and the desktop will NOT take the window's size at reattach "
        "(DECLARED FALLBACK)") + " to the unit's output (the user's journal). The desktop then keeps the size it was born with.",
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
        "It starts the ticker and the ScreenSaver sidecar (below), sets " + c("KWIN_FORCE_SW_CURSOR=1") + ", and becomes the KWin wrapper with "
        + c("--wayland-display <labwc's socket>") + " added.",
    ]) + \
    table(["Trap of KWin inside labwc (measured, per the comments)", "Cure in " + c("kwin.c") + " and in the package"], [
        ["KWin ≥ 6.5 draws a black pixel as the root of its window and its content in subsurfaces; the stock wlroots never reports the root "
         "as presented, KWin's clients get a stopped clock and Firefox stops painting (windows stayed on their first frame).",
         "<b>REMOTIX's own labwc</b>, with wlroots patched and linked statically (above)."],
        ["KWin froze a few seconds after birth (measured 11 Oct 2026): it draws its next frame only after labwc says the previous one was "
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
    p("<b>The ScreenSaver sidecar.</b> From Plasma 6.4 on, Ctrl+Alt+Del did nothing: the shortcut calls " + c("requestLogoutPrompt()")
      + ", which first asks " + c("org.freedesktop.ScreenSaver.GetActive") + " («never show the logout prompt on top of the lock screen»). That name "
      "belongs to KWin's lock-screen daemon, KWin starts with " + c("--no-lockscreen") + " (locking is REMOTIX's), nobody owns the name, the "
      "call fails with " + c("ServiceUnknown") + " and the failure is read as «the screen is locked» (comment in " + c("kwin.c") + ", measured "
      "18 Nov 2026 on Plasma 6.6.7: with a stand-in that answered false the prompt came up in one second). The cure is " + c("screensaver_alive()")
      + ", a second process beside the ticker, in the unit's cgroup, that owns the name (" + c("DO_NOT_QUEUE") + ": if a real owner is there "
      "first, the sidecar ends and says so) on the two paths " + c("/ScreenSaver") + " and " + c("/org/freedesktop/ScreenSaver") + " and answers "
      "every method of the standard interface: «not locked» and zero times for " + c("GetActive") + ", " + c("SetActive") + ", "
      + c("GetActiveTime") + ", " + c("GetSessionIdleTime") + " and " + c("SimulateUserActivity") + "; the standard error " + c("NotSupported")
      + " for " + c("Lock") + ", " + c("Throttle") + " and " + c("UnThrottle") + ". " + c("Inhibit") + " is <b>forwarded</b> to powerdevil's "
      + c("org.freedesktop.PowerManagement.Inhibit") + " with the same arguments and the same cookie back, and given back when the caller "
      "leaves the bus or calls " + c("UnInhibit") + ": measured with VLC, which asks the ScreenSaver name first and, on an error, does not go "
      "on, so a fake cookie would have left the video without a real inhibition. The sidecar dies with the unit and leaves nothing on the "
      "user's bus or in the user's files.") + \
    p("<b>The lost frame.</b> KWin can leave a window on an old picture when nothing damages it. " + c("kwin_poke()") + " (" + c("kwin.h")
      + ", 19 Nov 2026) re-commits the transparent pixel with damage, on the capture's own connection, to make KWin draw a frame, and "
      + c("capture_watch_sequence()") + " and " + c("capture_frame_lost()") + " count the holes in KWin's buffer numbers; the behaviour, "
      "its constants and its limits are in " + rif("The lost frame (KWin)") + ".") + \
    steps([
        "<b>At a reattach of another size</b> (" + c("child.c") + ", §7.1), if KWin's output is not the canvas asked for and the "
        "host exists, the child first dismantles the capture: KWin's stream would otherwise renegotiate to a size the fixed offer "
        "refuses, and die.",
        c("kwin_host_resize()") + " asks labwc's output for the new size (read back, not believed), then reads KWin's output "
        "on a connection of its own until it has the same size, for at most 3 s.",
        "The capture is mounted again at the new canvas.",
    ]) + \
    p("A reattach at the <b>same</b> size asks for nothing. A Plasma session with no host (our labwc missing, or born with "
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
    note(c("kwin_check_permission()") + " ends its failure messages with «Remedy: reinstall the package (apt install --reinstall remotix)» "
         "(" + c("RX-KDE-001") + ", " + c("RX-KDE-002") + " and " + c("RX-KDE-003") + ", " + c("kwin.c") + "): the remedy is the package's, since there is no installer.",
         "Remedy text.")

# ═════════════════════════════════════════════════════════════════════════
# 8. XFCE
# ═════════════════════════════════════════════════════════════════════════
S8 = p("XFCE on Wayland has no compositor of its own: it runs on labwc, the distribution's (labwc 0.9.3 on Ubuntu 26.04). There is no "
       "unit to override, so " + c("write_dropin()") + " does nothing and says so, and REMOTIX starts the compositor itself with "
       + c("exec labwc -m --session '<primary>'") + ", where the primary client is " + c("xfce4-session") + " preceded by the "
       "size step (" + c("measured_primary()") + "). The picture, pointer and input paths are the wlroots ones of "
       + rif("Screen capture") + " and " + rif("Input") + ". The Xubuntu panel has the whisker menu and no " + c("actions")
       + " button (study 7), so on Xubuntu the lock on the whisker menu is the only protection of the shutdown entries.", lead=True) + \
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
        ["Autostart cover", c("session_autostart_cover()") + " writes " + c("blueman.desktop") + " with " + c("Hidden=true")
         + " in the " + c("autostart") + " folder of the session's labwc folder (first in " + c("XDG_CONFIG_DIRS") + ")",
         "The Bluetooth applet crashed now and then (a race with " + c("obexd") + ", 5 sessions in 90, comment of 19 Nov 2026) "
         "and covered the screen with apport's «internal error» window; Bluetooth is a device of the machine, not of the remote "
         "user. See the next paragraph"],
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
    p("<b>Only the leaf keys are locked (D-X3).</b> In the lock files the nodes that are only the parent of a lock (" + c("plugins")
      + ", " + c("plugin-N") + ") are written as " + c("type=\"empty\"") + ", never as a value the user must own (the comment above "
      + c("xfce_panel_xml()") + "). The reason was seen: with " + c("plugin-N") + " = " + c("whiskermenu") + " in the lock, " + c("xfconfd")
      + " does not write into the user's file a value equal to the system's, so the user's file kept " + c("type=\"empty\"") + " and, "
      "once the lock was gone, the plugin had no type and the panel dropped it. " + c("xfce_panel_integrity()") + " runs at every "
      "birth (in " + c("xfce_session_xfconf()") + ") and repairs once the " + c("/plugins/plugin-<id>") + " entries of a panel's "
      + c("plugin-ids") + " that have no type: from a copy still pending, or from the standard layout, but <b>only</b> for the "
      "two types REMOTIX locks (" + c("PLUGIN_ACTIONS") + ", " + c("PLUGIN_WHISKER") + ") because the number may belong to another plugin "
      "by now, and never while " + c("xfconfd") + " still holds the lock in memory (" + c("xfconfd_holds_lock()") + " reads "
      + c("/proc/<pid>/environ") + " looking for " + c("/remotix/xdg-xfce") + "; if it cannot tell, it does not write).") + \
    p("<b>The autostart cover.</b> The entry in the session's " + c("autostart") + " folder has the same file name as the system's and "
      + c("Hidden=true") + ", so XFCE does not start it. The list is " + c("SESSION_NOT_IN_REMOTE_AUTOSTART") + " (today only " + c("blueman.desktop") + "); "
      "an entry is written only if the system's one exists, otherwise only an entry of ours (marked " + c("X-REMOTIX") + ") of an earlier "
      "birth is removed. It was measured on Xubuntu 26.04 that a " + c("Hidden=true") + " entry hides the file name wherever it is, so the user's own "
      "visible " + sysf("~/.config/autostart/blueman.desktop") + " is not started either (a differently named entry is). The code does not "
      "remove the cover at the end of the session: it disappears with " + sysf("/run/user/<uid>") + "; with another session of the same user alive "
      "(ssh, lingering) it stays, harmless because no non-remote session reads that folder.") + \
    p("<b>The copy and the restore.</b> A lock on a single property has a price: at the first save of the channel, " + c("xfconfd")
      + " writes each locked key into the user's file as " + c("type=\"empty\"") + " and the user's value is lost. REMOTIX "
      "therefore keeps a <b>copy</b> of the user's value of each key it locks, before locking, and puts the values back at "
      "the end of the session (" + c("xfce_restore_keys()") + "). The copy goes to the user's state folder; if that cannot be "
      "written it goes to RAM under the runtime folder (declared, with the warning that a reboot takes it); if neither works the "
      "locks are applied all the same and the line says that the user's values will not come back and lists them. Keys that "
      "cannot be put back stay pending and keep their originals in the next copy. This and the one-time restores of earlier versions' "
      "values are the exceptions to «nothing permanent» (" + rif("The four desktops side by side") + "). " + c("xfconf-query")
      + " exits with zero even when the daemon refused and put the previous value back, so every write is re-read.") + \
    note("the locked-key mechanism depends on " + c("locked=\"<user>\"") + ": the comment in " + c("session.c") + " records that "
         + c("locked=\"*\"") + " locks nothing (measured 13 Nov 2026 with xfce4-session 4.20.2, in the earlier tree), and that before that date the "
         "code thought four keys were locked that were not. Ubuntu 26.04 has xfce4-session 4.20.4 and the measurement was not repeated "
         "(not verified there). The copy file " + sysf("~/.local/state/remotix/xfce-chiavi")
         + " is not deleted after the restore, only marked as restored (comment in " + c("session.c") + "); the package's postrm removes it on purge.",
         "Lock syntax.") + \
    note("on Xubuntu the session has a black wallpaper (" + c("docs/REGISTRO-problemi.md") + " E1, seen by the owner on the live image on "
         "18 Nov 2026). The cause found is " + c("libxfce4windowing") + " 4.20.2, which loses the compositor's message that names the "
         "monitor of the workspace if it arrives before the monitor is known, so " + c("xfdesktop") + " paints black; the authors "
         "fixed it from 4.20.4. Ubuntu 26.04 has 4.20.5, so the wallpaper should appear, but that was not checked with a picture "
         "of a session on Ubuntu 26.04 (not verified).", "Black wallpaper.")

# ═════════════════════════════════════════════════════════════════════════
# 9. LXQt
# ═════════════════════════════════════════════════════════════════════════
S9 = p("Ubuntu 26.04 has a launcher for LXQt on Wayland, " + c("lxqt-wayland-session") + " 0.3.1, but Lubuntu does not install it (study 7 "
       "§3.1, from the package dependencies), and the code does not look for one: REMOTIX starts labwc itself "
       "with " + c("labwc -C <folder> -S '<primary>'") + ", where the primary client is " + c("lxqt-session") + " (2.3.0 on Ubuntu) preceded by "
       "the same size step as XFCE. The wallpaper is made by " + c("pcmanfm-qt") + " from the output's size, which is why the "
       "output must have its size before the session starts (" + rif("How a session is born") + ").", lead=True) + \
    table(["Topic", "Behaviour", "Why"], [
        ["labwc's folder", c("write_config_labwc_lxqt()") + " writes " + sysf("$XDG_RUNTIME_DIR/remotix/labwc-lxqt/") + " with an "
         + c("rc.xml") + " (server-side decoration, the default key bindings without a screen lock, plus the «bring windows back "
         "inside» shortcut) and an <b>empty</b> " + c("autostart"), "With " + c("-C") + " labwc reads only that folder. The "
         "empty autostart keeps " + c("swayidle") + " and " + c("wlopm") + " out: they would switch off the captured output after "
         "a few minutes. If the folder cannot be written the session is not born, because labwc would then read the user's folder"],
        ["The session's commands", c("lxqt_session_commands()") + " writes small scripts into REMOTIX's " + c("bin-lxqt")
         + " folder, at the head of " + c("PATH") + ": " + c("lxqt-leave") + " (turned into " + c("--logout") + ") and "
         + c("lxqt-powermanagement") + " (does nothing, logs a line). Each runs the real program <b>unless</b> the calling process "
         "is inside a logind session of the PAM service " + c("remotix") + " (asked of " + c("loginctl") + ", through " + c("timeout 3")
         + " when available)", "«Leave» then only logs out, and a local login on the same machine gets the normal programs. "
         "Nothing is written in the user's LXQt files"],
        ["X11 composition managers", "The same recipe, a script of the same name that logs a line and exits 0, for " + c("picom") + ", "
         + c("compton") + " and " + c("xcompmgr") + " (" + c("LXQT_X11_COMPOSITORS") + "), only if the program is installed",
         "Lubuntu's " + c("picom") + " is a module without " + c("X-LXQt-X11-Only") + ": there is no X server to compose in the remote session, "
         "it dies, " + c("lxqt-session") + " restarts it up to " + c("MAX_CRASHES_PER_APP") + " times and shows «X Compositor crashed too many "
         "times». A module that exits 0 is not restarted"],
        ["Programs that count every user's processes", c("lubuntu-update") + " (" + c("LXQT_SHARED_SERVER_PROGRAMS") + "): a script of the same name "
         "that exits 0, plus an autostart entry " + c("lubuntu-update-autostart.desktop") + " in the session folder that names the program <b>by name</b>",
         "It decides «am I already running?» by looking at the processes of all users, so the copy of a second user exits 1 and the same "
         "message appears. The system's entry names it by absolute path, which the " + c("PATH") + " cannot catch, so the entry of the same file "
         "name covers it; it is <b>not</b> " + c("Hidden=true") + ", otherwise the script would not start by name. Its purpose, installing "
         "updates, also asks for a password window, which a remote session must not show"],
        ["Autostart cover", c("blueman.desktop") + " with " + c("Hidden=true") + " (" + c("session_autostart_cover()") + ", as on XFCE)",
         "Same reason as on XFCE. On LXQt the user's own entry of the same name should win because the user's folder comes first; "
         "this was not measured"],
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
    p("The pieces are written only if the program and the system's entry exist; otherwise only what is REMOTIX's (marked " + c("X-REMOTIX")
      + ") is removed. The log line of " + c("lxqt_session_commands()") + " counts the X11 composition managers and the programs that count "
      "every user's processes that it covered. The crash windows that these pieces cover were seen in the Ubuntu 26.04 test rounds (a «Lubuntu Update crashed too many times» window "
      "on one user was not reproduced); the comments of the code date the cures to 18 and 19 Nov 2026.") + \
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
      "comment records, from a measurement of the earlier tree, that without it, on LXQt, «Log out» made the session be born again "
      "16 times out of 20; that was not repeated on Lubuntu.")

# ═════════════════════════════════════════════════════════════════════════
# 10. What the session imposes
# ═════════════════════════════════════════════════════════════════════════
S10 = p("One table to answer «where does REMOTIX write, for this desktop?». " + c("session_settings()") + " dispatches to "
        "the per-desktop code; the common rule is that everything lives under " + c("$XDG_RUNTIME_DIR") + " (gone with the user's "
        "runtime folder) and the user's own files are not touched, with the exceptions in " + rif("The four desktops side by side")
        + ": on GNOME " + sysf("~/.config/dconf/remotix") + " and, during the session, " + sysf("lock-warning-shown") + "; on XFCE the copy of the "
        "locked keys; and the one-time restores.", lead=True) + \
    table(["Desktop", "What is imposed", "Where it lives", "How it is verified"], [
        ["GNOME", "the 24 keys of " + c("DCONF_KEYS") + " (21 with value and lock, 3 lock only: the keyboard layout), including " + c("scaling-factor")
         + " = 1 and " + c("ubuntu-lock-on-suspend") + " = false; " + c("--headless --no-x11 --mode=%i") + "; the empty " + sysf("lock-warning-shown"),
         sysf("/etc/dconf/db/remotix") + " (system database), " + sysf("$XDG_RUNTIME_DIR/dconf/profile") + " (runtime profile), "
         + sysf("~/.config/dconf/remotix") + " (the layout), the drop-in in " + sysf("user.control") + "; in the fallback "
         + sysf("$XDG_RUNTIME_DIR/remotix/dconf/") + " and the in-memory layer",
         c("session_dconf_verify()") + " re-reads every key; the drop-in's " + c("ExecStart") + " is re-read"],
        ["KDE", "KIOSK " + c("[KDE Action Restrictions][$i]") + ": " + c("action/lock_screen") + ", " + c("action/start_new_session")
         + ", " + c("action/switch_user") + " false in " + c("kdeglobals") + "; " + c("BorderSize=Normal") + ", "
         + c("BorderSizeAuto=false") + " in " + c("kwinrc") + " (a starting point, written without " + c("[$i]") + ", so the user's "
         "own value wins); " + c("loginMode=emptySession") + " in " + c("ksmserverrc") + " (also a starting point); the screen "
         "inhibition to powerdevil; the start line's " + c("--no-lockscreen") + "; the ScreenSaver sidecar (not a setting: it only answers "
         "«not locked»)",
         sysf("$XDG_RUNTIME_DIR/remotix/xdg/") + " (first in " + c("XDG_CONFIG_DIRS") + "), the drop-in, memory",
         c("write_kde_menu_rules()") + " logs each file; the drop-in is re-read"],
        ["XFCE", "the locked keys of " + c("XFCE_LOCKS") + ", the panel's action and whisker entries (leaf keys only), labwc's " + c("rc.xml")
         + ", the autostart cover of " + c("blueman.desktop"),
         sysf("$XDG_RUNTIME_DIR/remotix/xdg-xfce/") + " and " + sysf("labwc-xfce/") + ", the " + sysf("xfconfd.service") + " drop-in; "
         "a copy of the user's values in the state folder",
         "every key re-read through " + c("xfconf-query") + "; the manager's environment for " + sysf("xfconfd.service") + " re-read"],
        ["LXQt", "the labwc folder, the session's command scripts (" + c("lxqt-leave") + ", " + c("lxqt-powermanagement") + ", the X11 composition "
         "managers, " + c("lubuntu-update") + "), the autostart covers (" + c("lubuntu-update") + ", " + c("blueman.desktop") + "), six hidden menu entries",
         sysf("$XDG_RUNTIME_DIR/remotix/labwc-lxqt/") + ", " + sysf("bin-lxqt/") + ", " + sysf("data-lxqt/"),
         "the six entries are re-read (" + c("n/6 entries hidden, RE-READ") + ")"],
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
S11 = p("What follows is what the maintainer will meet on the four desktops. The sources are " + c("docs/REGISTRO-problemi.md")
        + " (sections D and E), the studies of the tree, the code and its comments; what was not seen on Ubuntu 26.04 is said.",
        lead=True) + \
    table(["Desktop", "Behaviour", "Source and status"], [
        ["GNOME", "<b>The session is born in the Activities Overview</b>, which covers the desktop and holds the input, so the "
         "first thing a person sees and the first click go to the Overview. The check scripts ask the Shell (" + c("OverviewActive")
         + ") and press Escape before they test anything (" + c("prove/base-check.py") + " " + c("leave_overview()") + "). REMOTIX "
         "does not leave the Overview by itself.", "REGISTRO D: a real user sees it too. The touch-mode failures on GNOME were "
         "of the check, not of the product; a residual case where the first tap can land on the initial point if the pointer "
         "position arrives before Mutter is ready is intermittent and listed in REGISTRO E2 (first tap from a phone on GNOME)."],
        ["GNOME", "A new user's first desktop does not show «Screen Lock disabled» because REMOTIX makes " + sysf("lock-warning-shown")
         + " first, and removes it at the end if it made it.", "Code and comments (" + c("session_gnome_lock_warning()") + "); the notice itself was seen "
         "on the Ubuntu 26.04 box (study 12 §D)."],
        ["GNOME", "The check that runs " + c("pkexec") + " gets an empty " + c("SHELL") + ", by design (the composed environment sets it "
         "empty): " + c("pkexec") + " then refuses with «The value for the SHELL variable was not found in the /etc/shells file» and "
         "the row " + c("users-shell-and-environment") + " of " + c("prove/check-desktop.py") + " is red.", "REGISTRO E2; the only red "
         "row of the GNOME round of 18 Nov (123 of 124, " + c("studio/giro2-gnome.md") + ")."],
        ["KDE", "<b>A Log Out asked in the first seconds of the desktop was lost</b> on Plasma 6.6: " + c("plasma-shutdown")
         + " asks systemd to stop the session target, systemd refuses while a unit (usually the portal) is still starting, and "
         "plasma-shutdown does not repeat the request (" + rif("Ending a session and tidying up") + ").", "REGISTRO D (Kubuntu 26.04, 18 Nov 2026), "
         "fixed in " + c("session_kde_logout_watch()") + ". Lesson recorded there: an exit must also be tried with unsaved work (save, "
         "discard, cancel) and with the «Log Out» window cancelled; tests on an empty desktop are not enough."],
        ["KDE", "An exit asked by the desktop in the first seconds is forced after ten seconds when it does not complete, so the time the "
         "close is allowed to take is longer than ten seconds.", "REGISTRO D."],
        ["XFCE", "<b>A Log Out requested while the desktop is still starting is refused by XFCE</b> («must be at rest»): REMOTIX "
         "closes the desktop by force after the ten seconds (" + c("kill_xfce()") + ").", "REGISTRO D, seen 17 and 18 Nov; the same code in "
         "xfce4-session 4.20.4 (study 7 §14, from the sources)."],
        ["XFCE", "A window corner covered by the panel cannot be dragged.", "REGISTRO E2 (the panel sits over the corner)."],
        ["XFCE", "The wallpaper of the remote session can be black.", "REGISTRO E1, see " + rif("XFCE: labwc and a locked xfconf") + "."],
        ["LXQt", "Lubuntu's compositing manager and update checker would crash or fail in a shared session; they are covered by "
         "scripts and an autostart entry.", "Code (" + c("lxqt_session_commands()") + "), study 7; the Lubuntu live image worked in the owner's test, "
         "without a log being read."],
        ["All", "The Bluetooth applet's crash window is hidden by an autostart cover on XFCE and LXQt.", "Code, 19 Nov 2026."],
        ["All", "The snapshot of the user manager's variables can be old after a close made by the root side, and an unanswered "
         "question about the desktop counts as «closed» in two places.", "REGISTRO E3, not corrected on purpose (forced cases)."],
        ["All", "Small stutters in a video seen from Chrome on an Android phone, not from Chrome on Linux: not told apart between the "
         "phone, the video player in the virtual machine, the frame cadence in a virtual machine and the encoding route on the Radeon.",
         "REGISTRO E4, not blocking, no change made."],
    ], "«TAB» — Behaviours of the four desktops") + \
    p("The AppArmor profile and what was observed on a real Ubuntu 26.04 are in " + rif("The AppArmor profile and its mode")
      + ". The canvas limits that the product guarantees (3K, eight users) are in " + rif("Security model") + " and "
      + rif("Performance and capacity") + "; the maximum canvas that the decoder of the test browser reached on Debian is not a result "
      "of this tree and is not repeated.") + \
    p("<b>Places that differ per desktop</b> (the list to walk when a fifth is added): " + c("recognize_desktop()") + ", "
      + c("desktop_name()") + ", " + c("compose_environment()") + ", " + c("write_dropin()") + ", " + c("start()") + ", "
      + c("inactive_unit()") + ", " + c("really_terminate()") + ", " + c("session_settings()") + ", " + c("session_inhibit()")
      + ", " + c("session_alive()") + ", " + c("session_life()") + ", " + c("session_missing_component()") + ", " + c("local_session()")
      + ", " + c("unit_shell()") + " in " + c("session.c") + "; " + c("session_over_early()") + " in " + c("child.c") + "; the capture, input and "
      "clipboard branches in " + c("child.c")
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
