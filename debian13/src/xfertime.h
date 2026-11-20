/* xfertime.h — an ABSOLUTE deadline for a clipboard transfer (audit of the session, S-R5 and S-R6, 25 Oct 2026).
 *
 * The clipboard code waited at most 5 s for EACH step (`poll` before every read or write) and had no limit on the sum: a program of the user's desktop that wrote one byte every
 * 4.9 s, or read one chunk every 4 s, held the clipboard thread (or the child's main loop, for the GNOME reply) for hours with 1 MB. Now one deadline per transfer,
 * XFER_TOTAL_MS from its start, and every wait is the smaller of the usual step and what is left.  Header-only, tested by benches/unit/xfer-time. */
#ifndef XFERTIME_H
#define XFERTIME_H

#include <errno.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>

#define XFER_TOTAL_MS 10000

static inline uint64_t xfer_now_ms(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000u + (uint64_t)t.tv_nsec / 1000000u;
}

static inline uint64_t xfer_deadline(void)
{
	return xfer_now_ms() + XFER_TOTAL_MS;
}

/* The wait for the next step: `step_ms` or what is left of the deadline, the smaller; 0 if the deadline has passed. */
static inline int xfer_left_ms(uint64_t deadline, int step_ms)
{
	uint64_t now = xfer_now_ms();

	if (now >= deadline)
		return 0;
	return deadline - now < (uint64_t)step_ms ? (int)(deadline - now) : step_ms;
}

/* Waits for `events` on `fd` for at most min(step_ms, left).  true = ready (or HUP/ERR: the read/write that follows says which); false = timeout or deadline. */
static inline bool xfer_wait(int fd, short events, uint64_t deadline, int step_ms)
{
	struct pollfd probe = { .fd = fd, .events = events };
	int wait = xfer_left_ms(deadline, step_ms);
	int outcome;

	if (wait <= 0)
		return false;
	do
		outcome = poll(&probe, 1, wait);
	while (outcome < 0 && errno == EINTR && (wait = xfer_left_ms(deadline, step_ms)) > 0);
	return outcome > 0;
}

#endif
