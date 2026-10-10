/*
 * sessione — the GNOME graphical session: REMOTIX makes it BE BORN, and makes it
 * be born WITH A MONITOR.  It does not merely find it, and it does not merely keep it alive.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY THIS FILE EXISTS IN V2, AND WHY IT IS NOT A COPY OF THE v1 ONE
 *
 * `fondamenta/remotix-c/src/sessione.c:671` is:
 *
 *     if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(larghezza, altezza, sbaglio))
 *
 * that is, the virtual monitor is written **only for KWin**.  `sessione_assicura()`
 * receives `larghezza` and `altezza` (lines 650-651) and on the GNOME branch **nobody
 * reads them**: the desktop size enters the function and is silently lost.
 * It is error form **E3** — a function does LESS than its name
 * promises: it is called «ensure» and for GNOME it does not ensure the thing without which
 * there is nothing to capture.
 *
 * ⛔ And in headless mode Mutter sets `needs_outputs = false` (`STUDI.md` §gnome §3.1):
 *    without `--virtual-monitor` the session starts **alive, complete and black**.
 *    Alive means really alive — `IsSessionRunning` answers `true`,
 *    fifty names on the bus, Nautilus and the Terminal running — and only one thing
 *    is missing, and it is missing silently.
 *
 * ⭐ It is not a fear: `[M]` 12 August 2026, the GNOME session alive on NIC-OS
 *    **for two days** was exactly that, and nobody had noticed
 *    (`fasi/rapporti/F2-1-sessione.md`, `fasi/rapporti/D4-sessione-nera.md`).
 *    A capture pointed there would have measured zero frames and sent us to
 *    look for the defect inside PipeWire.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE INVARIANT THIS FILE PAYS FOR — **I7** (`CODER.md` §2)
 *
 *     «The protection against a known defect lives in the program, not in a
 *      configuration line that can be lost.»
 *
 * Until 12 August 2026 the GNOME virtual monitor was set by
 * `fondamenta/banco/provision-server.sh`, that is a line in `/etc/systemd/user/` on a
 * rootfs that lives in RAM.  That line got lost — and the machine was black
 * for two days.  D4 put it back, ⛔ **but a line put back is still a line that
 * can be lost**: here the PROGRAM asks for the monitor, at every session
 * birth, and verifies that it was obeyed.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE TWO QUESTIONS THAT ARE NOT ONE
 *
 *     «is the session ALIVE?»   and   «does the session HAVE A MONITOR?»
 *
 * The defect stayed invisible for two days because **only one** was asked
 * — the one that answered yes.  Hence `sessione_stato()`, which has one number
 * per state, and `sessione_assicura()`, which waits for **the monitor** and not for
 * liveness.
 *
 * ---------------------------------------------------------------------------
 * ⛔ AND THE TWO DEARLY PAID RULES THAT COME FROM v1 INTACT
 *
 *   - THE ENVIRONMENT IS COMPOSED, NOT INHERITED (`CODER.md` §4.5).  Whoever starts the
 *     session hands it their whole environment, including variables that
 *     have nothing to do with it, and from there the session redistributes it to the user's
 *     systemd manager and to D-Bus activation, where it SURVIVES the
 *     compositor.  An `LC_ALL=C` arriving by mistake from an SSH shell
 *     prevented ALL applications from opening, and the symptom did not say
 *     «a variable is missing»: it said «applications do not start».
 *   - LIVENESS IS ESTABLISHED WITHOUT INTERPRETING THE ANSWER.  `sessione_viva()`
 *     only checks that the answer ARRIVES: declaring the return type of
 *     `GetCurrentState` would mean that the session's liveness depends
 *     on the exactness of that declaration, and the first draft in Rust
 *     failed that way — the session had started and REMOTIX took it for dead.
 *     ⭐ `sessione_stato()` instead READS the answer, and when it does not have the
 *        shape it can read it says «could not read» (5) and **never** «zero
 *        monitors» (1): «empty» and «forbidden» look the same, and it is
 *        error form **E8**.
 */
#ifndef REMOTIX_SESSIONE_H
#define REMOTIX_SESSIONE_H

#include <gio/gio.h>
#include <glib.h>
#include <stdbool.h>
#include <stdint.h>

/* ⭐ `REG_SESSIONE` lives in `registro.h` next to the other areas, since 12 August
 *    2026: it is the only line the assembly removed from this file, and it is the
 *    line that §6.2 of `P2-1-sessione.md` asked to move there. */

/*
 * How the session is started, and on which unit the monitor is written.
 *
 * ⛔ The command is the EASY part.  What decides whether the compositor is born with
 *    something to capture is the override of the `ExecStart` of the Shell's
 *    unit: `gnome-session` does NOT launch `gnome-shell`, it starts the Shell's
 *    user unit (`org.gnome.Shell@wayland.service` up to GNOME 49,
 *    `org.gnome.Shell@user.service` from GNOME 50), whose `ExecStart` is fixed.
 */
/* ⭐ PHASE 17, D8 (`DECISIONI.md` §10.20): the GNOME session is NO longer always
 *    `gnome`.  It is the distribution's default one (`ubuntu` on Ubuntu), read
 *    from the sessions the display manager offers: the criterion is on
 *    `sessione_gnome()` in `sessione.c`.  `gnome` remains only as a DECLARED
 *    FALLBACK, when no offered session launches gnome-session. */
#define SESSIONE_GNOME_RIPIEGO "gnome"
/*
 * ⛔⭐ PHASE 17 — THE SHELL UNIT DOES NOT HAVE ONE NAME ONLY (`fasi/17-l-installatore.md` §5.1).
 *
 *   · up to GNOME 49 (Debian 13, Leap 16, Fedora 43): one file per mode,
 *     `org.gnome.Shell@wayland.service`;
 *   · from GNOME 50 (Fedora 44, Ubuntu 26.04, Tumbleweed, Arch): the TEMPLATE
 *     `org.gnome.Shell@.service` with `ExecStart=gnome-shell --mode=%i`, and
 *     gnome-session asks for the instance `org.gnome.Shell@user.service`
 *     (`[R]` gnome-shell `0eb754a08`; gnome-session 50.0
 *     `data/gnome.session.conf:3`).
 *   · ⛔ D8: the instance belongs TO THE SESSION, it is not fixed: `gnome` asks for `@user`,
 *     `ubuntu` asks for `@ubuntu` (`[M]` 30 Sep 2026, Ubuntu 26.04:
 *     `gnome-session@ubuntu.target.d/ubuntu.session.conf`,
 *     `Requires=org.gnome.Shell@ubuntu.service`) — and the instance is the Shell's
 *     MODE (`--mode=%i`): Ubuntu's dock and colours live there.
 *     ⇒ It is asked of the manager (`Requires` of `gnome-session@<sessione>.target`),
 *     and the drop-in keeps `--mode=%i`.
 *
 * ⇒ The choice is made from what is INSTALLED (`unita_shell()` in `sessione.c`),
 *   not from a version number.  ⛔ And the drop-in goes in the folder
 *   of the INSTANCE, never in that of the template (`org.gnome.Shell@.service.d/`):
 *   that one also applies to GDM's Shell.
 */
#define SESSIONE_UNITA_SHELL_48 "org.gnome.Shell@wayland.service"
#define SESSIONE_UNITA_SHELL_MODELLO "org.gnome.Shell@.service"
/* ⚠ The session manager unit is `gnome-session-manager@<sessione>.service`:
 *   the name is composed by `sessione_gnome()` (D8). */
/* ⛔ And the SECOND unit to wait for: when a GNOME session ends, GNOME
 * RESTARTS the session bus with this one.  A new session started while it runs
 * is born on a bus about to be replaced — and dies without writing anything
 * (`[M]` 16 August 2026: its log stays at zero bytes). */
#define SESSIONE_UNITA_DBUS "gnome-session-restart-dbus.service"

/*
 * ⭐ PHASE 12 — THE SECOND DESKTOP: PLASMA.  `fasi/12-kde.md`, increment 1.
 *
 * ✅ `DECISIONI.md` §4.6-duodetricies: **one desktop per machine**, and the
 *    server recognises it from what is installed.  ⛔ The choice among several
 *    desktops is postponed (`MASTERPLAN.md` M5).
 *
 * ⚠ The same three things as GNOME, with Plasma's names — ⛔ not an exception:
 *   the FUNCTION is the same (the session is born, is recognised, ends), what changes
 *   is **how** it is asked for.  `startplasma-wayland` does not launch KWin: it starts
 *   `plasma-kwin_wayland.service`, whose `ExecStart` is overridden with the drop-in
 *   (`STUDI.md` §kde §6.1-§6.2), exactly like the Shell unit.
 */
#define SESSIONE_COMANDO_KDE "exec startplasma-wayland"
#define SESSIONE_UNITA_KWIN "plasma-kwin_wayland.service"
#define SESSIONE_UNITA_PLASMA "plasma-workspace.target"

/*
 * ⭐ PHASE 13 — THE THIRD DESKTOP: XFCE.  `fasi/13-xfce.md`, increment 1.
 *
 * ⛔⛔ AND HERE THE SHAPE OF THE FIRST TWO FALLS, it does not repeat.  GNOME brings Mutter and
 *     KDE brings KWin; **XFCE does not bring a compositor**: on Wayland it leans
 *     on `labwc`, of the `wlroots` family (`STUDI.md` §xfce §1).
 *
 * ⇒ The consequences that change the code, and are not a matter of style:
 *
 *   1. ⛔ **There is no systemd user unit to override.**  On GNOME
 *      the `ExecStart` of `org.gnome.Shell@wayland.service` is rewritten, on KDE
 *      that of `plasma-kwin_wayland.service`; here the compositor is a
 *      process we start ourselves, and `scrivi_dropin()` **has no object**.
 *   2. ⛔ **The size does NOT enter the birth.**  `[M]` 20 Sep 2026, inside
 *      `rete11-xfce`: the output is born `HEADLESS-1 1280x720`, hardwired, and no
 *      protocol creates one of the wanted size.  The size is given **afterwards**,
 *      as a Wayland client (`zwlr_output_manager_v1` v4, which is there).
 *   3. ⭐ **The start line must contain `labwc` AND `--session`**, and not out of
 *      taste: `xfce4-session` reads `XFCE4_SESSION_COMPOSITOR` and, if it does not
 *      find both, at logout runs `loginctl terminate-session ''` —
 *      that is it kills **REMOTIX's logind session** (`STUDI.md` §xfce §9.2).
 *      ⇒ `--session` also does the good work: it makes `xfce4-session` labwc's primary
 *        client, so when it exits **labwc terminates on its own**.
 */
/* ⚠ The line is written ONCE and used TWICE: as a command (with `exec`) and
 *   inside `XFCE4_SESSION_COMPOSITOR` (without).  ⛔ Writing it twice would
 *   mean they could diverge, and diverging would spring the
 *   logout trap without any line saying so. */
/* ⭐ PHASE 15, D-007 — `-m` (`--merge-config`): labwc reads the `rc.xml` of
 *    ALL the XDG folders (ours, with the «bring back inside» shortcut,
 *    and the user's, which stays theirs).  Without it, labwc takes ONLY the first
 *    `rc.xml` it finds, and the user's would hide ours.  See
 *    `SESSIONE_LABWC_TASTIERA` below.  ⚠ The line always contains `labwc`
 *    and `--session`: the logout belt stays as it was. */
#define SESSIONE_TESTA_XFCE "labwc -m --session"
#define SESSIONE_PRIMARIO_XFCE "xfce4-session"
#define SESSIONE_RIGA_XFCE SESSIONE_TESTA_XFCE " " SESSIONE_PRIMARIO_XFCE
/* ⭐ 5 Oct 2026: the COMMAND is no longer a constant — the primary client is born
 *    after the client's size (`primario_misurato()` in sessione.c), as
 *    on LXQt.  ⚠ The head is the same macro: `labwc` and `--session` stay
 *    in the executed line AND in `XFCE4_SESSION_COMPOSITOR`, and the logout
 *    belt looks only at those two words (`STUDI.md` §xfce §9.2). */
/* ⛔ The compositor process, by name: on XFCE the guard against the
 *    second session cannot ask systemd — see `unita_inattiva()`. */
#define SESSIONE_PROCESSO_XFCE "labwc"
/* The session manager on the USER bus — `[M]` 20 Sep 2026: it appears there, not
 * on a private bus, because we start `labwc` ourselves without `dbus-run-session`.
 * ⚠ The name is not the interface: `org.xfce.Session.Manager` (with one more
 * dot) — `STUDI.md` §xfce §9.5. */
#define SESSIONE_BUS_XFCE "org.xfce.SessionManager"

/*
 * ⭐ PHASE 14 — THE FOURTH DESKTOP: LXQt.  Increment 1, «it is recognised, is born and
 *    is seen».  The source is `STUDI.md` §lxqt, and where the upstream source speaks
 *    it is quoted with its address.
 *
 * ⛔⛔ ON TRIXIE THE LXQt WAYLAND SESSION IS NOT PACKAGED: what is missing is the
 *     launcher (`lxqt-wayland-session`, `startlxqtwayland`), not the code
 *     (`STUDI.md` §lxqt §1).  ⇒ We make the launcher ourselves, and its shape is
 *     that of the upstream launcher contemporary with LXQt 2.1 — tag 0.1.1 —
 *     `[R]` https://raw.githubusercontent.com/lxqt/lxqt-wayland-session/0.1.1/startlxqtwayland.in
 *     (`labwc` branch):
 *
 *         exec labwc -C $XDG_CONFIG_HOME/labwc -S lxqt-session
 *
 *   with ONE intended difference: the `-C` folder is OURS (under
 *   `XDG_RUNTIME_DIR`), not the user's — the upstream script copies into it
 *   once only an `autostart` that launches `swayidle … wlopm --off` at 5
 *   minutes, and the copy is **permanent** (`STUDI.md` §lxqt §6.2).
 *   ⭐ `-C` is enough on its own: with `-C` labwc looks **only** at that folder
 *   (`[R]` labwc 0.8.3 `src/common/dir.c:151-157`).
 *
 * ⚠ The same shape as XFCE, and for the same reason: `-S` (= `--session`)
 *   makes `lxqt-session` labwc's primary client ⇒ when it exits, labwc
 *   terminates.  ✅ And XFCE's trap is not here: `lxqt-session` does not call
 *   `loginctl terminate-session` (`STUDI.md` §lxqt §3.3, `[✗]`).
 *
 * ⚠ The whole line is not a constant, unlike XFCE: the `-C` folder
 *   is under `XDG_RUNTIME_DIR` and is composed in `avvia()`.  Here are
 *   the two pieces that do not change.
 */
#define SESSIONE_MARCATORE_LXQT "lxqt-session"
#define SESSIONE_PRIMARIO_LXQT "lxqt-session"
/* ⭐ The name on the USER bus, and also the logout object and interface:
 *    `[R]` lxqt-session 2.1.1 `sessionapplication.cpp:48-49` (service and
 *    `/LXQtSession`), `sessiondbusadaptor.h` (interface `org.lxqt.session`)
 *    — https://raw.githubusercontent.com/lxqt/lxqt-session/2.1.1/lxqt-session/src/sessiondbusadaptor.h
 * ⚠ The name appears in the CONSTRUCTOR: «the name is there» does not mean «desktop up»
 *   (`STUDI.md` §lxqt §3.4).  See `sessione_viva()`. */
#define SESSIONE_BUS_LXQT "org.lxqt.session"

/*
 * ⭐⭐ PHASE 15, D-007 — WINDOWS ARE BROUGHT BACK INSIDE WHEN THE OUTPUT
 *      SHRINKS (labwc: XFCE and LXQt).
 *
 * THE DEFECT `[M]` 25 Sep 2026: reattaching with a smaller browser window,
 * labwc's output shrinks and a large window
 * stays where it was, partly OUTSIDE the right/bottom edge.  GNOME and KWin
 * bring them back inside on their own; labwc does NOT, and by choice:
 *   `[R]` labwc 0.8.3 (the one in the boxes, and it is the same on `master` of
 *   22 Sep 2026) `src/view.c` `adjust_floating_geometry()`: on a layout
 *   change a floating window moves ONLY if its MIDPOINT
 *   leaves the screen (and then it is recentred); on the left and top it
 *   is kept inside, on the right and bottom it is not.  No option changes it.
 *
 * ⛔ The roads that do NOT exist, read in the source:
 *   · no Wayland protocol lets a client move other clients'
 *     windows (`wlr-foreign-toplevel` has maximise/minimise/close, not the
 *     position);
 *   · changing the output in two steps does not help: labwc remembers the position
 *     «from before the changes» (`last_layout_geometry`) and puts it back, so
 *     the result depends only on that and on the final output;
 *   · the only labwc action that keeps a window inside on the RIGHT and at the
 *     BOTTOM is `MoveToCursor` (`view_move_to_cursor()`: centres the window
 *     on the pointer and then clamps it inside the usable area); with the pointer
 *     placed at the CENTRE of the window (`WarpCursor to="window"`) it becomes
 *     exactly «move it as little as possible», and `FitToOutput`
 *     shrinks it ONLY if it is larger than the screen.
 *     ⚠ `[M]` 25 Sep 2026: labwc 0.8.3 writes «Action MoveToCursor is
 *     deprecated … use AutoPlace policy="cursor"» ⇒ we write
 *     `AutoPlace policy="cursor"`, which calls the SAME function
 *     (`view_place_by_policy()` → `view_move_to_cursor()`, `view.c:1080`).
 *     Below, «MoveToCursor» is the name of the function, not of the action.
 *
 * ⭐ Hence: a labwc SHORTCUT nobody uses (`SESSIONE_LABWC_TASTO`),
 *    written in the labwc configuration the product already governs, and which
 *    the product TYPES with its virtual keyboard after changing the
 *    size (`input_riporta_dentro()`).  Four `ForEach` passes, flat
 *    because labwc 0.8.3 does not nest If/ForEach (`rcxml.c` «cannot be a child
 *    action»):
 *
 *   ⛔ MAXIMISED, TILED and FULL-SCREEN windows are not touched:
 *      labwc puts them back at the new size on its own, and `MoveToCursor` would
 *      take them out of that state.  The first two are excluded with the
 *      `query`s; full screen has no `query`, and is recognised by an
 *      effect: labwc does NOT change the decoration (`view_set_ssd_mode()`) and does NOT
 *      shade (`view_set_shade()`, no `ssd`) a full-screen
 *      window.  ⇒ Change first, and move only what changed.
 *   ⛔ And the move is done with the BORDER only (`border`), never with the
 *      title bar: `MoveToCursor` centres on the window INCLUDING the borders, and with the
 *      bar on top the window would drop by half a bar at every round.
 *
 *   1. windows without server-side decoration (almost all on XFCE: GTK,
 *      Firefox) → server border, temporary;
 *   2. those NOW with the border → `FitToOutput`, pointer at the centre,
 *      `MoveToCursor`, back without decoration;
 *   3. windows with the title bar (almost all on LXQt: Qt) → shaded, as a
 *      mark;
 *   4. the shaded ones → unshaded, `FitToOutput`, border only, pointer at the
 *      centre, `MoveToCursor`, back with the title bar.
 *
 * ⚠ THE PRICES, declared (rare: they arise only from user actions inside
 *   labwc): a window the user had set to «border only» comes back without
 *   border; one they had SHADED comes back unshaded.  And the compositor's
 *   pointer stays on the last window touched: `input_riporta_dentro()`
 *   puts it back where the user had it.
 * ⚠ All the passes run in ONE shortcut, within a single labwc turn:
 *   no frame falls in between, so the temporary decoration is not
 *   seen.
 */
#define SESSIONE_LABWC_TASTO "W-C-A-S-F12"
#define SESSIONE_LABWC_ESCLUSE                                                  \
	"<query maximized=\"both\"/><query maximized=\"horizontal\"/>"         \
	"<query maximized=\"vertical\"/><query tiled=\"left\"/>"               \
	"<query tiled=\"right\"/><query tiled=\"up\"/><query tiled=\"down\"/>" \
	"<query tiled=\"center\"/><query tiled_region=\"*\"/>"
#define SESSIONE_LABWC_SPOSTA                                                  \
	"<action name=\"FitToOutput\"/>"                                         \
	"<action name=\"WarpCursor\" to=\"window\" x=\"center\" y=\"center\"/>" \
	"<action name=\"AutoPlace\" policy=\"cursor\"/>"
#define SESSIONE_LABWC_TASTIERA                                                 \
	"  <keyboard>\n"                                                        \
	"    <default/>\n"                                                      \
	"    <keybind key=\"" SESSIONE_LABWC_TASTO "\">\n"                      \
	"      <action name=\"ForEach\">" SESSIONE_LABWC_ESCLUSE                \
	"<query shaded=\"yes\"/><query decoration=\"full\"/>"                   \
	"<query decoration=\"border\"/><else>"                                  \
	"<action name=\"SetDecorations\" decorations=\"border\" forceSSD=\"yes\"/>" \
	"</else></action>\n"                                                    \
	"      <action name=\"ForEach\">" SESSIONE_LABWC_ESCLUSE                \
	"<query shaded=\"yes\"/><query decoration=\"full\"/>"                   \
	"<query decoration=\"none\"/><else>" SESSIONE_LABWC_SPOSTA              \
	"<action name=\"SetDecorations\" decorations=\"none\"/>"                \
	"</else></action>\n"                                                    \
	"      <action name=\"ForEach\">" SESSIONE_LABWC_ESCLUSE                \
	"<query shaded=\"yes\"/><query decoration=\"none\"/>"                   \
	"<query decoration=\"border\"/><else><action name=\"Shade\"/>"          \
	"</else></action>\n"                                                    \
	"      <action name=\"ForEach\">" SESSIONE_LABWC_ESCLUSE                \
	"<query shaded=\"no\"/><else><action name=\"Unshade\"/>"                \
	"<action name=\"FitToOutput\"/>"                                         \
	"<action name=\"SetDecorations\" decorations=\"border\"/>"              \
	"<action name=\"WarpCursor\" to=\"window\" x=\"center\" y=\"center\"/>" \
	"<action name=\"AutoPlace\" policy=\"cursor\"/>"                                        \
	"<action name=\"SetDecorations\" decorations=\"full\"/>"                \
	"</else></action>\n"                                                    \
	"    </keybind>\n"                                                      \
	"  </keyboard>\n"

/*
 * ⛔⛔ AND THE FOURTH VALUE IS NOT A DESKTOP: IT IS HONESTY.
 *
 * Until phase 12 a machine that had neither GNOME nor KDE was
 * declared **GNOME as a fallback**, and the product tried to start
 * `gnome-session`, which does not exist there.  `[M]` 20 Sep 2026, `rete11-xfce`: the
 * fault did not show up where one would expect — `scrivi_dropin()` re-read
 * the `ExecStart` of a non-existent unit, got nothing, and wrote
 * «**another drop-in wins over mine**»; then capture blamed «**Mutter does not
 * expose RemoteDesktop**».  ⇒ Two innocents accused, and the real cause —
 * *GNOME is not there* — written only once, at server startup, where the
 * bench does not read it.
 *
 * ⭐ With «one desktop per machine» (`DECISIONI.md` §0.6) that fallback was
 *   **the only place where the product could get the desktop wrong, and it got it wrong
 *   silently**.  ⇒ XFCE is not added to the list leaving it there: it is removed.
 *   Otherwise on LXQt's day the same thing happens again.
 *
 * ⚠ The numbers go AT THE END: `SessioneDesktop` travels as a `uint32_t` between the
 *   parent and the child, and moving 0 or 1 would break that boundary.
 */
typedef enum {
	SESSIONE_DESKTOP_GNOME = 0,
	SESSIONE_DESKTOP_KDE = 1,
	SESSIONE_DESKTOP_XFCE = 2,
	SESSIONE_DESKTOP_NESSUNO = 3,
	/* ⭐ PHASE 14 — AT THE END, per the rule above: 0..3 stay as they are. */
	SESSIONE_DESKTOP_LXQT = 4,
} SessioneDesktop;

/*
 * Which desktop this machine has — decided ONCE per process.
 *
 * ⭐ It is a SEARCH, not an arbitration: `DECISIONI.md` §0.6 — one machine, one
 *   desktop; machines with several desktops installed are **out of scope**.
 *
 * The order, and each line has its reason:
 *
 *   1. `startplasma-wayland` **and not** `gnome-session`  → KDE
 *   2. both                                              → GNOME, and it is DECLARED
 *      ambiguous (out of scope: choose and say so, do not cure)
 *   3. `gnome-session`                                  → GNOME
 *   4. `xfce4-session`                                  → XFCE   ⭐ phase 13
 *      (and if `lxqt-session` is there too: XFCE, and it is DECLARED ambiguous — phase 14)
 *   5. `lxqt-session`                                   → LXQT   ⭐ phase 14
 *   6. none                                             → **NESSUNO**, and nothing
 *      is born — see the box on the enum
 *
 * ⚠ The order is NOT free: the first three branches stay textually those of
 *   phase 12, so **no machine served today changes behaviour**.  The
 *   XFCE branch slips in between the last known desktop and the fallback.
 * ⭐ And LXQt's AFTER XFCE, for the same reason: a machine with XFCE
 *   and LXQt together stays XFCE as it was yesterday — the only change is that now it says so.
 *
 * ⛔ And the XFCE marker is `xfce4-session`, **not `labwc`**: labwc is the
 *    FAMILY compositor, the same one LXQt uses, and recognising on it
 *    would confuse two different desktops.  `labwc` remains a **precondition**, and
 *    its absence is declared at birth instead of being discovered from a failed
 *    `exec`.  ⭐ Phase 14: for LXQt, identically, the marker is `lxqt-session`.
 */
SessioneDesktop sessione_desktop(void);

/* The choice in words, with the why — for the server's startup line. */
const char *sessione_desktop_spiega(void);

/*
 * ⭐ PHASE 14 — THE FAMILY, not the desktop: true on XFCE **and** on LXQt.
 *
 * Capture, input, clipboard and remount do not talk to the desktop: they talk to the
 * COMPOSITOR, and for both it is labwc (`STUDI.md` §lxqt §5: «full
 * reuse»).  ⛔ Until phase 13 `figlio.c` wrote it as
 * `== SESSIONE_DESKTOP_XFCE` in five places: with a fifth enum value
 * LXQt would have fallen, all at once and without a warning, into the GNOME/KDE branch.
 * ⇒ Whoever asks «wlroots?» asks this, and not a desktop.
 */
bool sessione_su_wlroots(void);

/*
 * ⛔ THE MONITOR IS CHOSEN BY NAME, AND THIS IS THE NAME.
 *
 * `[M]` 12 August 2026: on this machine **two** virtual monitors were seen
 * together, and **both 1920x1080@60**:
 *
 *     Meta-0   MetaVirtualMonitor      0x00       ← ours, --virtual-monitor
 *     Meta-1   Virtual remote monitor  0x000001   ← created by Mutter for itself
 *
 * ⭐ Exactly the same size: whoever told them apart by resolution or by index
 *    would tell nothing apart.  What tells them apart is **the product name**, which
 *    Mutter gives to the persistent monitor requested with `--virtual-monitor`
 *    (`meta-context-main.c:592-597` `[R]`) as opposed to the one it creates by itself for
 *    a virtual ScreenCast (`meta-screen-cast-virtual-stream-src.c:606-609`
 *    `[R]`).  It is `CODER.md` §3.9 to the letter: *ask for the component by name, and
 *    verify that it obeyed*.
 */
#define SESSIONE_PRODOTTO_CHIESTO "MetaVirtualMonitor"

/*
 * ⛔ THE STATE NUMBERS, AND THEY ARE THE SAME AS THE BENCH'S.
 *
 * They are, one by one, the exit codes of `banchi/02-sessione-stato.py` (0-5), and the
 * coincidence is intended: the product and the bench that judges it must say the
 * same word for the same thing, or the relation between the two numbers must be translated
 * by hand by someone, and whoever translates gets it wrong.
 *
 * ⚠ The bench has two more numbers that are not here, and the split is
 *   declared rather than suffered:
 *     6 DISAGREEMENT    command line and bus do not say the same   ← E1
 *     7 NON-EMPTY SHELL gnome-session restarted in a login shell
 *   The product prevents **6** instead of measuring it: it writes the drop-in and
 *   re-reads the `ExecStart` IN FORCE before starting (necessary), then asks the
 *   bus how many monitors there really are (sufficient).  **7** cannot
 *   happen: this file composes the environment, and sets `SHELL` empty by its own
 *   hand.  ⛔ That the product cannot produce a state does not relieve the bench
 *   of the duty to be able to see it: those two numbers remain its own.
 */
typedef enum {
	SESSIONE_SANA = 0,          /* one monitor only, of the requested name and size */
	SESSIONE_NERA = 1,          /* alive, and ZERO monitors — fault M9 of STUDI.md §gnome §13 */
	SESSIONE_MISURA_ALTRA = 2,  /* one monitor, but not of the requested size */
	SESSIONE_SCELTO_DA_SE = 3,  /* product other than the requested one, or more than one ← E2 */
	SESSIONE_MORTA = 4,         /* no compositor: the bus does not answer */
	SESSIONE_NON_LETTA = 5,     /* I COULD not read: denied or unreadable ← E8 */
} SessioneStato;

/* The mark in words, with the same words as the bench. */
const char *sessione_marca(SessioneStato stato);

/* The monitor as Mutter declares it, for whoever must capture it by NAME. */
typedef struct {
	char connettore[64]; /* «Meta-0» */
	char fornitore[64];  /* «MetaVendor» */
	char prodotto[64];   /* «MetaVirtualMonitor» — this is what is looked at */
	char seriale[64];    /* «0x00» */
	uint32_t larghezza;
	uint32_t altezza;
	double refresh;
	unsigned quanti; /* how many monitors there were in all: 2 is already a defect */
} SessioneMonitor;

/*
 * The ONLY lawful way to get the session bus.
 *
 * ⛔ `g_bus_get_sync(G_BUS_TYPE_SESSION, ...)` is never called directly.
 *
 * GIO, on the SESSION bus connection, keeps «exit-on-close» on: if
 * the bus closes, the library calls `raise(SIGTERM)` on our behalf.  At
 * logout the user's `dbus.service` stops — and it has a culprit with a name and a
 * line, `gnome-session-ctl.c:130-133` does `StopUnit("dbus.service")`
 * (`STUDI.md` §gnome §3.3) — and REMOTIX died there: not killed by systemd nor by
 * anyone else, but by itself.  The stack that proves it is from 4 August 2026.
 * For the SYSTEM bus the defect does not exist: that one stays.
 *
 * Returns a new reference, or NULL with `sbaglio` written.
 */
GDBusConnection *sessione_bus(GError **sbaglio);

/*
 * The configuration folder of the Plasma session we serve:
 * `$XDG_RUNTIME_DIR/remotix/xdg`, put IN FRONT in `XDG_CONFIG_DIRS` when the
 * session is born (the menu rules, the border, `loginMode`).  ⭐ `kwin_disposizione()`
 * writes there too (`kxkbrc`).  NULL without `XDG_RUNTIME_DIR`;
 * to be freed with `g_free`.
 */
char *sessione_cartella_kde(void);

/*
 * ⭐ PHASE 15, D-015 — the SESSION's dconf (GNOME only): writes the profile
 * `$XDG_RUNTIME_DIR/remotix/dconf/profilo` (an in-memory database on top,
 * the user's below, read-only) and sets `DCONF_PROFILE` in the
 * process.  ⛔ It must be called BEFORE any `GSettings`: the dconf engine
 * reads the variable only once.  False on another desktop, or if the cure
 * cannot hold (said in the log).
 */
bool sessione_dconf_prepara(void);

/*
 * Is the session's dconf in force in THIS process?  ⛔ If not, whoever
 * writes GNOME settings would write them into the user's.
 */
bool sessione_dconf_di_sessione(void);

/*
 * ⭐ PHASE 15 (R1/R2) — systemd's USER MANAGER goes back to how it was after the
 * remote session: `sessione_fotografa_gestore()` at birth saves the
 * value our variables had before; `sessione_sgombera_gestore()` —
 * with the session DEAD, otherwise it does nothing — removes our drop-ins and
 * restores the variables.  The box is in `sessione.c`.
 */
void sessione_fotografa_gestore(void);
/* Once the session has exited, closes what is left of the user in THEIR session-N.scope
 * (said in the log).  The why is above the definition, in sessione.c. */
void sessione_sgombera_scope(void);
void sessione_sgombera_gestore(const char *perche);

/*
 * Is there a compositor that answers?
 *
 * ⚠ It is the WEAK question, and it is here on purpose so that its weakness shows: a
 *   black session answers «yes».  Whoever needs to know whether there is something to
 *   capture calls `sessione_stato()`.
 */
bool sessione_viva(void);

/*
 * What state the session is in, with the REQUESTED size next to it.
 *
 * `scelto` (optional) receives the monitor found — or the first of many,
 * when there are many — so that whoever captures can name it instead of deducing it.
 *
 * ⛔ It touches nothing: it can be called at any moment, and harms
 *    nobody.  ⚠ In particular `org.gnome.Shell.Screenshot` is NOT asked, which
 *    on a zero-monitor session makes Mutter attempt a 0x0 texture
 *    (`cogl_texture_2d_new_with_size: assertion 'width >= 1' failed`), kills
 *    `gnome-shell` and, with `OnFailure=gnome-session-shutdown.target` and
 *    `Restart=no`, **takes the whole session away** `[M]` 12 Aug 2026.  ⇒ That
 *    check **destroys the thing it is checking**, and does so **only in the
 *    faulty case**: green when it is healthy, rubble when it is black.
 */
SessioneStato sessione_stato(uint32_t larghezza, uint32_t altezza, SessioneMonitor *scelto);

/*
 * Makes sure there is a graphical session WITH A MONITOR of the requested
 * size, making it be born if it is missing or black.
 *
 * Returns **the state of the world when it has finished**, not a yes/no: 0 is
 * success, and every other number says in what way it is not.  ⛔ The why is
 * in the log, area «sessione»: there is no `GError` to propagate because there
 * is nobody to propagate it to — the caller can only declare it and carry on
 * with less (`CODER.md` §4.2), and that is what it must do.
 *
 * `avviata` (optional) says whether it had to make it be born.
 *
 * ⛔ WHAT IT DOES, CASE BY CASE — written here so that it is not discovered from the code:
 *
 *   SANA            touches nothing.  The stage belongs to the session (I4)
 *   MORTA           writes the drop-in, starts, and WAITS FOR THE MONITOR
 *   NERA            ⛔ writes the drop-in and makes it BE BORN AGAIN, declaring it loudly.
 *                   Why it is lawful: a local session would have
 *                   a real monitor, and a session with ZERO monitors can only be a
 *                   headless one — that is, ours.  Nothing is taken away from anyone
 *   MISURA_ALTRA    ⚠ DECLARES and carries on: there is something to capture, and the
 *                   size of an already live session is not changed on the fly
 *                   (`STUDI.md` §gnome §8.2: `ensure_virtual_monitor` returns early if the
 *                   size does not change — and whether it survives a hot change is `[?]`)
 *   SCELTO_DA_SE    ⚠ DECLARES, lists ALL monitors by name, and carries on.
 *                   Making it be born again would cure nothing: whoever creates the extra
 *                   monitor is someone else's ScreenCast
 *   NON_LETTA       ⛔ TOUCHES NOTHING.  «I could not read» is not «there
 *                   is none» (E8), and a session knocked down because of a failed
 *                   read is damage done on a hypothesis
 */
/* ⭐ Asks for the birth of the graphical session and RETURNS AT ONCE — phase 5.
 * It starts only from `SESSIONE_MORTA`; whoever retries takes care of finding out that it is there.
 * ⛔ The CHILD uses it, which during a 40 s wait would stop answering the
 *    parent.  The full why is above the function in `sessione.c`. */
bool sessione_fai_nascere(uint32_t larghezza, uint32_t altezza);

/* ⭐ The settings the session must have BEFORE being born: the twelve
 * virtual console shortcuts (which headless Mutter swallows for
 * nothing), the «Log Out…» entry on, automatic suspend off, the
 * desktop's screen locker off.  ⛔ The PRODUCT sets them and not a
 * provisioning file: invariant I7.  ⚠ Each schema is looked up first — `g_settings_new`
 * on a missing schema ABORTS the process. */
void sessione_impostazioni(void);

/* ⭐ Tells the session manager that someone is working: `SUSPEND|IDLE`,
 * ⛔ never `LOGOUT`.  Returns the cookie, 0 if it failed.  ⚠ It is not
 * released: it lasts as long as the session.  (`DECISIONI.md` §4.7, third belt.) */
guint32 sessione_inibisci(void);

SessioneStato sessione_assicura(uint32_t larghezza, uint32_t altezza, bool *avviata);

/*
 * Terminates the graphical session.  True if it was there and now it is gone.
 *
 * # Why it exists
 *
 * Because «the local session wins» (I2) does not only mean detaching the
 * client: if the remote compositor stayed up, the user who sits down
 * in front of the machine would have **two graphical sessions in their name** on the
 * same `$XDG_RUNTIME_DIR`, and the second would find `org.gnome.Shell` already
 * taken.  The defect would show where nobody looks for it: on the
 * LOCAL session that does not start.
 *
 * # First ask, then insist
 *
 * `Logout(1)` is the orderly exit without questions.  But it may also happen that
 * nothing happens — a program with unsaved changes has the right to INHIBIT
 * the exit, and `Logout(1)` in that case shows the dialog, which in an
 * unattended session nobody closes (`STUDI.md` §gnome §3.2).  After ten seconds it
 * insists with `Logout(2)`, **declaring it in the log**: it is a possible
 * loss of unsaved work, and whoever reads must be able to reconstruct it.
 *
 * ⛔ And it waits for `inactive`, NOT «other than active»: `is-active` goes through
 *    `deactivating`, and restarting a session in there is another first
 *    run (`FASI.md` §00-ambiente, defect 4 of phase 0).
 */
bool sessione_termina(void);

#endif
