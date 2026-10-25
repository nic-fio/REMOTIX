/* runwait.h — waiting for a helper process with a limit (audit of the session, E-R9, 25 Oct 2026).
 *
 * run_as_root() (child.c, `usermod` at the first connection of a user) did `waitpid(p, &state, 0)`: if /etc/passwd or /etc/group are locked by an administrator `usermod` waits for
 * its own timeout (tens of seconds) and the process that runs the spawn — the root side in production, the main one in the local branch — stopped serving everybody. Now: poll with
 * WNOHANG every RUNWAIT_STEP_MS up to `max_ms`, then SIGKILL and a short last wait. Header-only, tested by benches/unit/run-wait with real children. */
#ifndef RUNWAIT_H
#define RUNWAIT_H

#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <sys/wait.h>
#include <time.h>

#define RUNWAIT_STEP_MS 20
#define RUNWAIT_KILL_GRACE_MS 1000

static inline uint64_t runwait_now_ms(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000u + (uint64_t)t.tv_nsec / 1000000u;
}

static inline void runwait_nap(void)
{
	struct timespec nap = { 0, RUNWAIT_STEP_MS * 1000000L };

	nanosleep(&nap, NULL);   /* an interruption just makes the next look come earlier */
}

/* 1 = the child ended and `*state` is its status; 0 = it did not end in `max_ms`, was killed (SIGKILL) and, if it was reaped in the grace period, `*state` is set (return 2 then);
 * -1 = waitpid failed (not our child any more, ECHILD).  A killed child that cannot be reaped in RUNWAIT_KILL_GRACE_MS (uninterruptible sleep) is left: 0. */
static inline int run_wait(pid_t pid, unsigned max_ms, int *state)
{
	uint64_t end = runwait_now_ms() + max_ms;

	for (;;) {
		pid_t r = waitpid(pid, state, WNOHANG);

		if (r == pid)
			return 1;
		if (r < 0 && errno != EINTR)
			return -1;
		if (runwait_now_ms() >= end)
			break;
		runwait_nap();
	}
	kill(pid, SIGKILL);
	end = runwait_now_ms() + RUNWAIT_KILL_GRACE_MS;
	while (runwait_now_ms() < end) {
		pid_t r = waitpid(pid, state, WNOHANG);

		if (r == pid)
			return 2;
		if (r < 0 && errno != EINTR)
			return -1;
		runwait_nap();
	}
	return 0;
}

#endif
