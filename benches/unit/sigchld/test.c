/*
 * test.c — the SIGCHLD gate of the main loop (src/sigchld.h): the dead are reaped when SIGCHLD says so, and at least once a second, with no
 * zombie left and no death lost.  Real processes and a real SIGCHLD handler, the same loop shape as main.c (ppoll → gate → scan).
 *
 *   1. the gate by itself (no signal): flag → one scan, then none until the safety time; the clock going backwards scans; `on` false scans always
 *   2. one child dies while the loop sleeps in ppoll: EINTR → the next pass does not sleep (pending) → reaped within a few ms, not after
 *      the ppoll's whole timeout; no zombie
 *   3. 20 children die at once (coalesced SIGCHLD): the one scan reaps all of them
 *   4. a death with the signal «lost» (the flag cleared by hand): the safety scan reaps it, at the safety time and not before
 *   5. a quiet loop (nobody dies) makes NO waitpid in 40 passes inside the safety time, and one at the safety time
 *   6. a child that dies right after the scan of a round is not lost: the flag is up for the next one
 *   7. the exec'd program starts with the default SIGCHLD (the handler does not cross execve) and with SIGCHLD NOT blocked
 *   8. by reading the sources: main.c reads the flag before it sleeps (zero wait) and installs the handler with SA_RESTART | SA_NOCLDSTOP;
 *      child.c and helper.c skip waitpid() when told (the hold flags) and default to reaping
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/sigchld/test.c -o test && ./test /albero/src'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "sigchld.h"

#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static int checks, bad;
#define CHECK(cond, ...) do { checks++; if (!(cond)) { bad++; printf("FAIL: "); printf(__VA_ARGS__); printf("\n"); } } while (0)

static struct sigchld_gate G;
static void on_chld(int s) { (void)s; sigchld_gate_flag(&G); }

static uint64_t now_ms(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000 + (uint64_t)t.tv_nsec / 1000000;
}

static void install(void)
{
	struct sigaction sa;
	memset(&sa, 0, sizeof sa);
	sa.sa_handler = on_chld;
	sigemptyset(&sa.sa_mask);
	sa.sa_flags = SA_RESTART | SA_NOCLDSTOP;
	memset(&G, 0, sizeof G);
	G.on = sigaction(SIGCHLD, &sa, NULL) == 0;
}

/* a child that exits after `ms` */
static pid_t spawn(int ms)
{
	pid_t p = fork();
	if (p == 0) {
		if (ms > 0)
			usleep((useconds_t)ms * 1000);
		_exit(7);
	}
	return p;
}

/* One pass of the loop, as main.c does it: no sleep if the flag is up; ppoll (nothing to read: a pipe that never fires); the gate; the scan.
 * `pids` are the children we track (0 = reaped).  Returns the number reaped; `*calls` counts the waitpid() calls made. */
static int pass(int waitfd, int timeout_ms, pid_t *pids, int n, int *calls, uint64_t safety_ms)
{
	struct pollfd pf = {waitfd, POLLIN, 0};
	struct timespec ts;
	int wait_ms = sigchld_gate_pending(&G) ? 0 : timeout_ms;
	int reaped = 0;
	ts.tv_sec = wait_ms / 1000;
	ts.tv_nsec = (long)(wait_ms % 1000) * 1000000L;
	if (ppoll(&pf, 1, &ts, NULL) < 0 && errno == EINTR)
		return -1;            /* main.c: `continue`, the flag is read at the top of the next pass */
	if (sigchld_gate_round(&G, now_ms(), safety_ms)) {
		for (int i = 0; i < n; i++) {
			if (pids[i] > 0) {
				int st;
				(*calls)++;
				if (waitpid(pids[i], &st, WNOHANG) == pids[i]) {
					pids[i] = 0;
					reaped++;
				}
			}
		}
	}
	return reaped;
}

static int run_until_reaped(int waitfd, pid_t *pids, int n, int limit_ms, int timeout_ms, int *calls, uint64_t safety_ms, uint64_t *took)
{
	uint64_t t0 = now_ms();
	int left = n;
	while (left > 0 && now_ms() - t0 < (uint64_t)limit_ms) {
		int r = pass(waitfd, timeout_ms, pids, n, calls, safety_ms);
		if (r > 0)
			left -= r;
	}
	*took = now_ms() - t0;
	return left;
}

static int zombies_left(void)
{
	int st;
	pid_t r = waitpid(-1, &st, WNOHANG);
	return r > 0 ? 1 : 0;      /* >0 = a child was still waiting to be reaped */
}

int main(int argc, char **argv)
{
	int quiet[2];
	pid_t p[32];
	int calls;
	uint64_t took;

	/* 1. the gate by itself */
	{
		struct sigchld_gate g;
		memset(&g, 0, sizeof g);
		g.on = true;
		CHECK(sigchld_gate_round(&g, 5000, 1000), "the first round must scan (last_ms 0)");
		CHECK(!sigchld_gate_round(&g, 5100, 1000), "no flag, 100 ms later: no scan");
		sigchld_gate_flag(&g);
		CHECK(sigchld_gate_pending(&g), "flag up: pending");
		CHECK(sigchld_gate_round(&g, 5200, 1000), "flag up: scan");
		CHECK(!sigchld_gate_pending(&g), "the flag is consumed by the round");
		CHECK(!sigchld_gate_round(&g, 5300, 1000), "after the scan, quiet again");
		CHECK(sigchld_gate_round(&g, 6200, 1000), "the safety time (1000 ms since the last scan) scans");
		CHECK(!sigchld_gate_round(&g, 6300, 1000), "and it restarts the count");
		CHECK(sigchld_gate_round(&g, 100, 1000), "the clock went backwards: scan");
		g.on = false;
		CHECK(sigchld_gate_round(&g, 100, 1000) && sigchld_gate_round(&g, 101, 1000), "handler not installed: always scan");
	}

	CHECK(pipe(quiet) == 0, "pipe");
	install();
	CHECK(G.on, "sigaction");

	/* 2. one death while the loop sleeps in ppoll */
	{
		pid_t one[1];
		sigchld_gate_round(&G, now_ms(), 5000);        /* consume the first-scan of an empty list */
		one[0] = spawn(60);
		calls = 0;
		int left = run_until_reaped(quiet[0], one, 1, 3000, 2000 /* ppoll timeout: 2 s */, &calls, 5000, &took);
		CHECK(left == 0, "the dead child was not reaped");
		CHECK(took < 400, "reaped after %llu ms: the ppoll's 2 s timeout was waited (EINTR branch lost the flag)", (unsigned long long)took);
		CHECK(zombies_left() == 0, "a zombie is left");
	}

	/* 3. twenty at once (coalesced SIGCHLD) */
	{
		for (int i = 0; i < 20; i++)
			p[i] = spawn(80);
		calls = 0;
		int left = run_until_reaped(quiet[0], p, 20, 3000, 2000, &calls, 5000, &took);
		CHECK(left == 0, "%d of 20 dead children were not reaped", left);
		CHECK(took < 500, "20 coalesced deaths took %llu ms", (unsigned long long)took);
		CHECK(zombies_left() == 0, "zombies left after 20 deaths");
	}

	/* 4. the signal «lost»: only the safety scan can see it */
	{
		pid_t one[1];
		one[0] = spawn(30);
		usleep(150000);                                 /* it is dead by now, SIGCHLD delivered: the flag is up */
		__atomic_store_n(&G.flag, 0, __ATOMIC_SEQ_CST); /* ... and we throw it away, as if it never came */
		sigchld_gate_round(&G, now_ms(), 400);          /* a scan just done (nothing tracked yet): the safety time restarts */
		calls = 0;
		int left = run_until_reaped(quiet[0], one, 1, 3000, 50, &calls, 400, &took);
		CHECK(left == 0, "the child whose signal was lost was never reaped");
		CHECK(took >= 300 && took < 900, "reaped after %llu ms: the safety scan (400 ms) must be what saw it", (unsigned long long)took);
		CHECK(zombies_left() == 0, "zombie after the safety scan");
	}

	/* 5. a quiet loop makes no waitpid inside the safety time, and one at it */
	{
		pid_t one[1];
		one[0] = spawn(2500);                           /* alive during the whole test */
		sigchld_gate_round(&G, now_ms(), 400);
		calls = 0;
		uint64_t t0 = now_ms();
		int passes = 0;
		while (now_ms() - t0 < 300) {
			pass(quiet[0], 5, one, 1, &calls, 400);
			passes++;
		}
		CHECK(passes >= 20, "only %d passes in 300 ms", passes);
		CHECK(calls == 0, "%d waitpid() calls in %d quiet passes inside the safety time (must be 0)", calls, passes);
		while (now_ms() - t0 < 520)
			pass(quiet[0], 5, one, 1, &calls, 400);
		CHECK(calls >= 1 && calls <= 3, "%d waitpid() calls around the safety time (one scan expected)", calls);
		int st;
		kill(one[0], SIGKILL);
		waitpid(one[0], &st, 0);
		sigchld_gate_round(&G, now_ms(), 400);          /* eat the flag the kill raised */
	}

	/* 6. a death right after a scan is not lost */
	{
		pid_t two[2];
		two[0] = spawn(10);
		two[1] = 0;
		usleep(100000);                                 /* the first is dead; its flag is up */
		calls = 0;
		pass(quiet[0], 0, two, 2, &calls, 5000);        /* scan: reaps it */
		CHECK(two[0] == 0, "the first death was not reaped by the scan");
		two[1] = spawn(30);                             /* dies AFTER the scan */
		int left = run_until_reaped(quiet[0], &two[1], 1, 3000, 2000, &calls, 5000, &took);
		CHECK(left == 0 && took < 400, "the death after the scan was lost or late (%llu ms)", (unsigned long long)took);
		CHECK(zombies_left() == 0, "zombie after a death right after a scan");
	}

	/* 7. what an exec'd program sees: SIGCHLD default and not blocked */
	{
		int out[2];
		CHECK(pipe(out) == 0, "pipe2");
		pid_t c = fork();
		if (c == 0) {
			dup2(out[1], 1);
			execl("/bin/sh", "sh", "-c", "grep -E '^(SigBlk|SigCgt)' /proc/self/status", (char *)NULL);
			_exit(127);
		}
		close(out[1]);
		char buf[512] = {0};
		ssize_t n = read(out[0], buf, sizeof buf - 1);
		int st;
		waitpid(c, &st, 0);
		(void)n;
		unsigned long long blk = 0, cgt = 0;
		char *l = strstr(buf, "SigBlk:");
		if (l) sscanf(l, "SigBlk: %llx", &blk);
		l = strstr(buf, "SigCgt:");
		if (l) sscanf(l, "SigCgt: %llx", &cgt);
		/* SIGCHLD is signal 17: bit 16 */
		CHECK(l != NULL, "could not read /proc/self/status of the exec'd program");
		CHECK(!(blk & (1ULL << 16)), "SIGCHLD is BLOCKED in the exec'd program (SigBlk %llx)", blk);
		CHECK(!(cgt & (1ULL << 16)), "the exec'd program inherited a SIGCHLD handler (SigCgt %llx)", cgt);
	}

	/* 8. the sources (argv[1] = the src directory) */
	if (argc > 1) {
		static char buf[8 << 20];
		char path[512];
		const char *files[] = {"main.c", "child.c", "helper.c"};
		static char txt[3][2 << 20];
		for (int k = 0; k < 3; k++) {
			snprintf(path, sizeof path, "%s/%s", argv[1], files[k]);
			FILE *f = fopen(path, "r");
			size_t got = f ? fread(txt[k], 1, sizeof txt[k] - 1, f) : 0;
			if (f) fclose(f);
			txt[k][got] = 0;
			CHECK(got > 0, "cannot read %s", path);
		}
		(void)buf;
		const char *m = txt[0], *c = txt[1], *h = txt[2];
		const char *a = strstr(m, "if (sigchld_gate_pending(&sigchld_gate))");
		const char *b = a ? strstr(a, "wait_ns = 0;") : NULL;
		const char *pp = strstr(m, "ppoll(fds, n + npage");
		CHECK(a && b && pp && a < pp && b < pp, "main.c does not read the flag before the ppoll (zero wait)");
		CHECK(strstr(m, "sc.sa_flags = SA_RESTART | SA_NOCLDSTOP;") != NULL, "main.c: the handler is not installed with SA_RESTART | SA_NOCLDSTOP");
		CHECK(strstr(m, "sigchld_gate_round(&sigchld_gate, t_now, SIGCHLD_SAFETY_MS)") != NULL, "main.c: no gate round with the safety time");
		CHECK(strstr(m, "helper_reap_hold(pam_help, !scan);") != NULL && strstr(m, "children_reap_hold(offspring, !scan);") != NULL, "main.c does not tell the consumers");
		CHECK(strstr(m, "#define SIGCHLD_SAFETY_MS 1000") != NULL, "the safety time is not one second");
		a = strstr(c, "static pid_t child_reap(");
		b = a ? strstr(a, "if (f->reap_hold)") : NULL;
		const char *w = a ? strstr(a, "return waitpid(g->pid, state, WNOHANG);") : NULL;
		CHECK(a && b && w && b < w, "child.c: child_reap() does not skip waitpid() when told");
		a = strstr(h, "static bool reap(helper *a, int *status)");
		b = a ? strstr(a, "if (a->reap_hold)") : NULL;
		w = a ? strstr(a, "waitpid(a->child, status, WNOHANG)") : NULL;
		CHECK(a && b && w && b < w, "helper.c: reap() does not skip waitpid() when told");
		CHECK(strstr(c, "bool reap_hold;") != NULL && strstr(h, "bool reap_hold;") != NULL, "the hold flags are missing in the structs");
	}

	printf("sigchld: %d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
