/*
 * busfilter.h — ⭐ DECISIONS.md §10.49: THE SESSION'S SYSTEM BUS, WITHOUT THE
 *               POWER BUTTONS.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS
 *
 * The director, 11 Oct 2026, on 0.19.0 on his tablet: inside a REMOTIX session
 * Power Off, Restart, Suspend (and Hibernate) must NOT appear, on all four
 * desktops; «Log Out…» stays.  And: nothing installed that the local users
 * can see (no GNOME extension), no system files (§10.36: no polkit, logind or
 * sleep files), one mechanism for all desktops.
 *
 * All four desktops decide those entries from the same place: logind's
 * `Can*` answers on the SYSTEM bus (GNOME directly and through gnome-session,
 * Plasma's libkworkspace, xfce4-session, liblxqt's `Power`).  ⇒ The session is
 * given its own way to the system bus: this filter, which forwards everything
 * untouched except logind's power operations —
 *   · `CanPowerOff`, `CanReboot`, `CanSuspend`, … answer «na» (the word logind
 *     uses for «this machine cannot»: every desktop hides the entry);
 *   · `PowerOff`, `Reboot`, `Suspend`, … (and `*WithFlags`, `ScheduleShutdown`)
 *     are refused with `AccessDenied`: `systemctl poweroff` typed in a terminal
 *     of the session fails too.
 *
 * ---------------------------------------------------------------------------
 * ⭐ HOW IT LIVES — `remotix --internal-bus-filter SOCKET -- COMMAND…`
 *
 * The session's start line (`session.c`, `start()`) goes through here.  The
 * process FORKS the filter, waits until it listens on SOCKET, and then becomes
 * COMMAND (`execvp`) with `DBUS_SYSTEM_BUS_ADDRESS=unix:path=SOCKET;<the real
 * one>`.  ⇒ The desktop keeps its pid, its name and its place as leader of the
 * stage (`rediscover.h` reads exactly that); the filter is NOT its child (a
 * double fork: no desktop meets an unknown child) and dies with it (a pidfd).
 * ⭐ The SECOND address is the real bus: if the filter is not there (dead,
 *   or the variable left behind in the user manager after a crash), a client
 *   falls back to the machine's bus instead of having none.  ⛔ That fallback is
 *   a robustness choice, not a hole to hide: the filter is NOT a security
 *   boundary — the session's user can always reach the real bus — and the
 *   power acts stay governed by logind and polkit as on any machine.
 *
 * ⚠ What the filter changes for the services behind it: they see the FILTER as
 *   the caller (pid, credentials), not the desktop's program — the filter lives
 *   in the same logind session and with the same user, so polkit and logind
 *   decide the same way (it is how `xdg-dbus-proxy` works for Flatpak).
 */
#ifndef REMOTIX_BUSFILTER_H
#define REMOTIX_BUSFILTER_H

/* The word on the command line: `remotix --internal-bus-filter SOCKET -- COMMAND…` */
#define BUSFILTER_ARG "--internal-bus-filter"

/* ⭐ The socket's name in `$XDG_RUNTIME_DIR/remotix/` */
#define BUSFILTER_SOCKET "system-bus"

/* Does not return if COMMAND starts (it becomes COMMAND); returns an exit
 * status only if COMMAND could not be executed at all. */
int busfilter_main(int argc, char **argv);

#endif
