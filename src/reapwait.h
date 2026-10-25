/* reapwait.h — wait for a child to exit for AT MOST a time (audit of 25 Oct 2026, part E, E-R7).
 *
 * ⛔ `children_turn_off()` in the single-process branch (no root side) did `waitpid(pid, NULL, 0)` after the SIGTERM: a child stuck in
 *    uninterruptible sleep (a GPU hang, a DRM ioctl) held the shutdown of the whole service until systemd's SIGKILL.  The branch with a root
 *    side already waits at most TURN_OFF_WAIT_MS per child; this gives the other the same shape: a bounded wait with WNOHANG, then
 *    SIGKILL, then one more bounded wait.  Header only; the caller includes <errno.h>, <signal.h>, <sys/wait.h>, <time.h>, <unistd.h>. */
#ifndef REMOTIX_REAPWAIT_H
#define REMOTIX_REAPWAIT_H

#include <errno.h>
#include <stdbool.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>

/* True when `pid` has been reaped (or is not our child any more) within `ms` milliseconds; false when it is still there. */
static inline bool reap_within(pid_t pid, unsigned ms)
{
	struct timespec nap = { 0, 5 * 1000 * 1000 };
	unsigned waited = 0;

	for (;;) {
		pid_t r = waitpid(pid, NULL, WNOHANG);

		if (r == pid || (r < 0 && errno != EINTR))
			return true; /* reaped, or ECHILD: nothing to wait for */
		if (waited >= ms)
			return false;
		nanosleep(&nap, NULL);
		waited += 5;
	}
}

/* SIGTERM already sent by the caller: wait `term_ms`, then SIGKILL and wait `kill_ms` more.  True when the child is gone. */
static inline bool reap_or_kill(pid_t pid, unsigned term_ms, unsigned kill_ms)
{
	if (reap_within(pid, term_ms))
		return true;
	kill(pid, SIGKILL);
	return reap_within(pid, kill_ms);
}

#endif
