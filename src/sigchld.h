/* sigchld.h — WHEN the main loop reaps (`waitpid(WNOHANG)`): when a child died, not at every round.
 *
 * ⛔ Why: until now every round of the main loop made N+1 `waitpid(WNOHANG)` calls (one per child in `children_move()`, one for the
 *    PAM dispatcher in `helper_expired()`), even when nobody had died: a system call per child, per round, for a thing that happens
 *    a few times an hour.  The kernel tells us when a child changes state: SIGCHLD.
 *
 * HOW (the choice and its reasons, from the commit):
 *   · a HANDLER that only sets a flag (`sigaction`, SA_RESTART | SA_NOCLDSTOP), not a `signalfd`.  A `signalfd` needs SIGCHLD BLOCKED
 *     in the whole process, and a blocked mask is INHERITED across `fork()` + `execve()`: every program we start (the per-session
 *     children, labwc, the PAM modules, whatever a PAM module runs) would have SIGCHLD blocked, and a shell script or a `wait()` in it
 *     would hang.  That would need a mask reset at every fork site (child.c ×3, helper.c, kwin.c ×2, main.c, rootside.c, GLib's own
 *     spawns): one forgotten site and the failure is silent.  A handler is reset to the default by `execve()` and leaves the mask
 *     alone.  Its price is an EINTR in the non-restartable calls (`ppoll`, `poll`) of the process: the main loop handles it (below), the
 *     other `poll` calls of the server process treat a negative result as «not ready» or retry (checked one by one), and GLib's and
 *     PipeWire's own loops retry on EINTR.
 *   · the flag is read-and-cleared ONCE PER ROUND (`sigchld_gate_round()`), BEFORE the scan: a death after the clear sets the flag
 *     again (the next round scans); a death before it is seen by the scan (the kernel marks the child a zombie before it notifies).
 *     SIGCHLD may be coalesced (several deaths, one signal): the scan visits EVERY child, so none is lost.
 *   · a SAFETY scan at least every `safety_ms` (one second in main.c) even with no flag: a signal lost for any reason (a library that
 *     replaced the handler, a child that was not ours any more) delays a reaping by a second at most, never for ever.
 *   · the loop reads the flag also BEFORE it sleeps (`sigchld_gate_pending()` → zero wait): the `ppoll` interrupted by EINTR (the
 *     branch that does `continue`) does not go back to sleep for a whole timeout with a death waiting, and a flag set between two
 *     rounds is seen at once.  The only window left is the few instructions between that read and the kernel's `ppoll` entry: a death
 *     in there waits for the next wake-up, at most the loop's own timeout (≤ 1 s) — the same bound as the safety scan.  Closing it
 *     completely needs the `ppoll` signal mask with SIGCHLD blocked in the loop, i.e. the inherited-mask problem above.
 *   · without the handler installed (`on` false: a bench or a fuzz harness that links `child.c` / `helper.c` without `main.c`), the gate
 *     says «scan» every time: the old behaviour.
 *
 * The consumers are told by a hold flag (`children_reap_hold()`, `helper_reap_hold()`), set by the loop each round to `!scan`; their
 * default (false, from `calloc`) is «reap», so nothing changes for whoever never calls the setters. */
#ifndef REMOTIX_SIGCHLD_H
#define REMOTIX_SIGCHLD_H

#include <signal.h>
#include <stdbool.h>
#include <stdint.h>

struct sigchld_gate {
	volatile sig_atomic_t flag;   /* set by the handler, cleared by sigchld_gate_round() */
	uint64_t last_ms;             /* the clock of the last scan */
	bool on;                      /* the handler is installed */
};

/* In the signal handler: async-signal-safe (one store; errno untouched). */
static inline void sigchld_gate_flag(struct sigchld_gate *g)
{
	g->flag = 1;
}

/* A death is waiting (the flag is up), without consuming it: the loop uses it to not sleep. */
static inline bool sigchld_gate_pending(const struct sigchld_gate *g)
{
	return g->flag != 0;
}

/* Once per round: true = scan every child now.  The flag is exchanged atomically (a signal between the read and the clear would be lost
 * with two plain operations). */
static inline bool sigchld_gate_round(struct sigchld_gate *g, uint64_t now_ms, uint64_t safety_ms)
{
	int f = __atomic_exchange_n(&g->flag, 0, __ATOMIC_SEQ_CST);
	if (!g->on)
		return true;
	if (f || now_ms < g->last_ms || now_ms - g->last_ms >= safety_ms) {
		g->last_ms = now_ms;
		return true;
	}
	return false;
}

#endif
