/* reapwait.h — wait for a child process to be reaped, FOR A LIMITED TIME (audit of the session, 25 Oct 2026).
 *
 * ⛔ Why: `children_turn_off()` (child.c) called `waitpid(pid, NULL, 0)` for every child after the SIGTERM — without a limit.  A child stuck
 *    in a call that does not return (a compositor that does not answer, a driver in an uninterruptible state) kept the whole service from
 *    stopping, for ever: systemd's own timeout then killed everything, desktops included, instead of the server finishing its shutdown
 *    (the desktops outlive the server and are found again at the next start).  Now: SIGTERM, wait up to `ms`, then SIGKILL and a short
 *    wait; a child that is still not reaped after that is said and left (init collects it).
 *
 * Header only, no dependency on the rest of the program: benches/unit/reap-wait tests it alone with real processes. */
#ifndef REMOTIX_REAPWAIT_H
#define REMOTIX_REAPWAIT_H

#include <errno.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>

/* true = `pid` has been reaped (or is not a child of ours any more: ECHILD, someone else collected it); false = still running after `ms`. */
static inline int reap_within(pid_t pid, unsigned ms)
{
	const struct timespec step = {0, 5 * 1000 * 1000};   /* 5 ms: the shutdown is outside the poll loop, a short nap is fine */

	for (unsigned waited = 0;; waited += 5) {
		pid_t r = waitpid(pid, NULL, WNOHANG);

		if (r == pid)
			return 1;
		if (r < 0 && errno != EINTR)
			return 1;
		if (waited >= ms)
			return 0;
		nanosleep(&step, NULL);
	}
}

#endif
