/*
 * test.c — the bounded wait for a child (src/reapwait.h), audit of 25 Oct 2026, part E, E-R7.
 * What is checked, on the REAL header (nothing copied), with real processes:
 *   1. a child that exits at once is reaped within the wait;
 *   2. a child that ignores SIGTERM and sleeps is NOT reaped in a short wait (reap_within says false in about the time asked, not forever);
 *   3. reap_or_kill: that same child is killed after the first wait and reaped (true), in about term_ms, not seconds later;
 *   4. a pid that is not our child (already reaped) counts as gone;
 *   5. by reading src/child.c (argv[1], optional): children_turn_off() no longer calls waitpid(g->pid, NULL, 0) and uses reap_or_kill().
 *
 * BUILD AND RUN (a few seconds; run from the root of the tree):
 *   gcc -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Isrc benches/unit/reap-wait/test.c -o /tmp/reap-wait && /tmp/reap-wait src/child.c
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "reapwait.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures, passed;

static void check(int cond, const char *what)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", what);
	if (cond)
		passed++;
	else
		failures++;
}

static double now_s(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec + t.tv_nsec / 1e9;
}

static pid_t stubborn(void)
{
	pid_t p = fork();

	if (p == 0) {
		signal(SIGTERM, SIG_IGN);
		for (;;)
			sleep(1);
	}
	return p;
}

int main(int argc, char **argv)
{
	pid_t p;
	double t0;

	p = fork();
	if (p == 0)
		_exit(0);
	check(reap_within(p, 2000), "a child that exits at once is reaped");

	p = stubborn();
	usleep(50 * 1000);
	kill(p, SIGTERM);
	t0 = now_s();
	check(!reap_within(p, 200), "a child that ignores SIGTERM is not reaped within 200 ms");
	check(now_s() - t0 < 1.0, "…and the wait lasted about 200 ms, not forever");

	t0 = now_s();
	check(reap_or_kill(p, 100, 2000), "reap_or_kill: the same child is killed and reaped");
	check(now_s() - t0 < 1.5, "…in about the first wait, not seconds later");

	check(reap_within(p, 100), "a pid already reaped (ECHILD) counts as gone");

	if (argc > 1) {
		FILE *f = fopen(argv[1], "rb");
		long n;
		char *b, *a;

		if (!f) {
			printf("    --  (cannot read %s: source check skipped)\n", argv[1]);
		} else {
			fseek(f, 0, SEEK_END);
			n = ftell(f);
			fseek(f, 0, SEEK_SET);
			b = calloc(1, (size_t)n + 1);
			if (b && fread(b, 1, (size_t)n, f) == (size_t)n) {
				a = strstr(b, "void children_turn_off(children *f)");
				check(a != NULL, "child.c has children_turn_off()");
				if (a) {
					char *end = strstr(a, "free(f->v);");
					char *w;
					int blocking = 0;

					for (w = a; end && (w = strstr(w, "waitpid(g->pid, NULL, 0)")) != NULL && w < end; w++)
						blocking++;
					check(blocking == 0, "children_turn_off() has no blocking waitpid(g->pid, NULL, 0)");
					check(end && memmem(a, (size_t)(end - a), "reap_or_kill(g->pid", 19) != NULL,
					      "children_turn_off() waits with reap_or_kill()");
				}
			}
			free(b);
			fclose(f);
		}
	}
	printf("\n  %d passed, %d failed\n", passed, failures);
	return failures ? 1 : 0;
}
