/*
 * test.c — the bounded wait for a child (src/reapwait.h, used by children_turn_off() in src/child.c), audit of the session, 25 Oct 2026.
 * children_turn_off() sent SIGTERM and then called waitpid(pid, NULL, 0) for every child, WITHOUT a limit: one child stuck in a call that does not
 * return kept the whole service from stopping for ever (then systemd's timeout killed everything).  Now: SIGTERM, wait TURN_OFF_WAIT_MS, SIGKILL, wait a
 * little, and say it if the child is still there.
 *
 * What is checked, with REAL processes:
 *   1. a child that exits at once is reaped quickly (reap_within returns 1);
 *   2. a child that ignores SIGTERM is still there after the limit (returns 0, after about the limit, not before, not much after), and once SIGKILLed it is
 *      reaped (returns 1) — the sequence children_turn_off() runs;
 *   3. a pid that is not our child (already reaped: ECHILD) is «reaped» at once: the shutdown does not wait for a ghost;
 *   4. the whole shutdown of 3 stuck children is bounded (each ~limit, then the kill): under 1.5 s with a 100 ms limit — with waitpid(pid, NULL, 0) it
 *      would never end;
 *   5. by reading src/child.c (argv[1], optional): children_turn_off() no longer contains `waitpid(g->pid, NULL, 0)`, and has reap_within(), a SIGKILL and
 *      the line that says a child is left to init.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/reap-wait/test.c -o test && ./test /albero/src/child.c'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "reapwait.h"

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static double now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

static pid_t stuck_child(void)
{
	pid_t p = fork();
	if (p == 0) {
		signal(SIGTERM, SIG_IGN);
		for (;;)
			pause();
	}
	return p;
}

int main(int argc, char **argv)
{
	pid_t p;
	double t0;

	/* 1 */
	p = fork();
	if (p == 0)
		_exit(0);
	t0 = now_ms();
	CHECK(reap_within(p, 500) == 1 && now_ms() - t0 < 200, "1. a child that exits at once is reaped quickly");

	/* 2 */
	p = stuck_child();
	usleep(50000);
	kill(p, SIGTERM);
	t0 = now_ms();
	CHECK(reap_within(p, 100) == 0, "2. a child that ignores SIGTERM is still there after the limit");
	{
		double d = now_ms() - t0;
		CHECK(d >= 95 && d < 400, "2b. and the wait took about the limit, not less, not much more");
	}
	kill(p, SIGKILL);
	CHECK(reap_within(p, 1000) == 1, "2c. SIGKILLed, it is reaped");

	/* 3 */
	p = fork();
	if (p == 0)
		_exit(0);
	waitpid(p, NULL, 0);
	t0 = now_ms();
	CHECK(reap_within(p, 500) == 1 && now_ms() - t0 < 100, "3. a pid that is no longer our child (ECHILD) counts as reaped, at once");

	/* 4 */
	{
		pid_t k[3];
		for (int i = 0; i < 3; i++)
			k[i] = stuck_child();
		usleep(50000);
		t0 = now_ms();
		for (int i = 0; i < 3; i++) {
			kill(k[i], SIGTERM);
			if (!reap_within(k[i], 100)) {
				kill(k[i], SIGKILL);
				reap_within(k[i], 1000);
			}
		}
		CHECK(now_ms() - t0 < 1500, "4. the shutdown of 3 stuck children ends in well under 1.5 s (SIGTERM, 100 ms, SIGKILL)");
	}

	/* 5 */
	if (argc > 1) {
		FILE *f = fopen(argv[1], "r");
		char *b = NULL, *fn;
		long n;

		if (f) {
			fseek(f, 0, SEEK_END);
			n = ftell(f);
			rewind(f);
			b = calloc(1, (size_t)n + 1);
			if (b && fread(b, 1, (size_t)n, f) != (size_t)n)
				b[0] = 0;
			fclose(f);
		}
		fn = b ? strstr(b, "void children_turn_off(children *f)") : NULL;
		if (fn) {
			char *end = strstr(fn, "\n\tfree(f->v);");
			if (!end)
				end = fn + 3500;
			char save = *end;
			*end = 0;
			CHECK(strstr(fn, "waitpid(g->pid, NULL, 0)") == NULL, "5. children_turn_off() has no unlimited waitpid left");
			CHECK(strstr(fn, "reap_within(g->pid, TURN_OFF_WAIT_MS)") && strstr(fn, "child_signal(f, g, SIGKILL)") &&
			      strstr(fn, "left to init"), "5b. it waits a limited time, then SIGKILL, and says a child is left to init");
			*end = save;
		} else {
			CHECK(0, "5. children_turn_off() found in child.c");
		}
		free(b);
	}

	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
