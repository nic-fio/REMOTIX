/* test.c — the stop signals of src/main.c (audit of the session, E-R8).  Real signals, a real ppoll:
 *   1. the pattern of the main loop (block the four stop signals, read the flag again, ppoll with the ORIGINAL mask, restore): a SIGTERM that is already pending when
 *      the loop gets there (the window between the flag test and the ppoll) interrupts a 5 s wait AT ONCE (the old ppoll(.., NULL) slept the whole wait);
 *   2. the same for SIGHUP and SIGQUIT, which now set the flag instead of killing the process (a process that still lives after raise() proves the handler is there);
 *   3. the mask is back to the original after the pattern: a child forked afterwards starts with the four signals OPEN (checked in a real fork);
 *   4. source reading of src/main.c: the four signals are handled, and the ppoll takes `&original` (no NULL mask left on the main ppoll).
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /albero && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
 *        -Isrc benches/unit/stop-signals/test.c -o /tmp/test && /tmp/test'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;
static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

static volatile sig_atomic_t chld_flag;   /* the sigchld_gate flag of main.c */
static void on_signal(int s) { (void)s; stop_requested = 1; }
static void on_chld(int s) { (void)s; chld_flag = 1; }

static long ms_since(const struct timespec *a)
{
	struct timespec b;
	clock_gettime(CLOCK_MONOTONIC, &b);
	return (b.tv_sec - a->tv_sec) * 1000 + (b.tv_nsec - a->tv_nsec) / 1000000;
}

/* the exact shape of the block in main.c */
static int inject;   /* a signal that "arrives" inside the window, right after the block */

static int wait_like_main(struct pollfd *fds, const struct timespec *ts)
{
	sigset_t stops, original;
	int outcome, saved;

	sigemptyset(&stops);
	sigaddset(&stops, SIGINT); sigaddset(&stops, SIGTERM); sigaddset(&stops, SIGHUP); sigaddset(&stops, SIGQUIT); sigaddset(&stops, SIGCHLD);   /* rilettura-fix B4 */
	sigprocmask(SIG_BLOCK, &stops, &original);
	if (inject) {
		raise(inject);   /* stays pending: the signals are blocked here */
		inject = 0;
	}
	if (stop_requested) {
		sigprocmask(SIG_SETMASK, &original, NULL);
		return -2;
	}
	{
		struct timespec zero = { 0, 0 };

		if (chld_flag)   /* the handler ran before the block: do not sleep (sigchld_gate_pending) */
			ts = &zero;
		outcome = ppoll(fds, 1, ts, &original);
	}
	saved = errno;
	sigprocmask(SIG_SETMASK, &original, NULL);
	errno = saved;
	return outcome;
}

static int has(const char *file, const char *needle)
{
	FILE *f = fopen(file, "r");
	static char src[4u << 20];
	size_t n;

	if (!f) return 0;
	n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
	return strstr(src, needle) != NULL;
}

int main(void)
{
	int p[2];
	struct pollfd fds[1];
	struct timespec five = { 5, 0 }, t0;
	int sigs[3] = { SIGTERM, SIGHUP, SIGQUIT };

	signal(SIGINT, on_signal); signal(SIGTERM, on_signal); signal(SIGHUP, on_signal); signal(SIGQUIT, on_signal);
	if (pipe(p) != 0) return 2;
	fds[0].fd = p[0]; fds[0].events = POLLIN;

	for (int i = 0; i < 3; i++) {
		int r;

		stop_requested = 0;
		inject = sigs[i];   /* the signal arrives AFTER the flag test of the loop and BEFORE the ppoll: the old race */
		clock_gettime(CLOCK_MONOTONIC, &t0);
		r = wait_like_main(fds, &five);
		CHECK(r < 0 && errno == EINTR && ms_since(&t0) < 500 && stop_requested, "1/2. a stop signal in the window ends the 5 s wait at once and sets the flag");
	}
	{
		/* and the OLD form, for contrast: it sleeps the whole wait */
		sigset_t one, old;
		struct timespec w = { 0, 300 * 1000000L };

		stop_requested = 0;
		sigemptyset(&one); sigaddset(&one, SIGTERM);
		sigprocmask(SIG_BLOCK, &one, &old);
		raise(SIGTERM);
		clock_gettime(CLOCK_MONOTONIC, &t0);
		(void)ppoll(fds, 1, &w, NULL);
		CHECK(ms_since(&t0) >= 280, "1b. (contrast) ppoll with a NULL mask while the signal is pending sleeps the whole wait");
		sigprocmask(SIG_SETMASK, &old, NULL);
		stop_requested = 0;
	}

	{
		sigset_t cur;
		pid_t k = fork();

		if (k == 0) {
			sigprocmask(SIG_BLOCK, NULL, &cur);
			_exit(sigismember(&cur, SIGINT) || sigismember(&cur, SIGTERM) || sigismember(&cur, SIGHUP) || sigismember(&cur, SIGQUIT) ? 1 : 0);
		}
		{
			int st = 0;
			waitpid(k, &st, 0);
			CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0, "3. after the pattern the four signals are open again (a child inherits the mask)");
		}
	}

	stop_requested = 0;
	clock_gettime(CLOCK_MONOTONIC, &t0);
	{
		struct timespec shortw = { 0, 100 * 1000000L };
		int r = wait_like_main(fds, &shortw);
		CHECK(r == 0 && ms_since(&t0) >= 90 && !stop_requested, "3b. without a signal it waits its time and returns 0");
	}

	{
		/* the SIGHUP rule of main.c, in two real children: one that inherits SIG_IGN keeps it (nohup), the other gets the handler */
		for (int ign = 0; ign < 2; ign++) {
			pid_t k = fork();

			if (k == 0) {
				struct sigaction old_hup;

				signal(SIGHUP, ign ? SIG_IGN : SIG_DFL);
				if (sigaction(SIGHUP, NULL, &old_hup) != 0 || old_hup.sa_handler != SIG_IGN)
					signal(SIGHUP, on_signal);
				raise(SIGHUP);                                  /* an ignored one leaves us alive with the flag clear */
				_exit(ign ? (stop_requested ? 1 : 0) : (stop_requested ? 0 : 1));
			}
			{
				int st = 0;
				waitpid(k, &st, 0);
				CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0, ign ? "3c. SIGHUP inherited as ignored stays ignored" : "3d. SIGHUP not ignored becomes a stop request");
			}
		}
	}

	CHECK(has("src/main.c", "old_hup.sa_handler != SIG_IGN") && has("src/main.c", "signal(SIGHUP, on_signal);") && has("src/main.c", "signal(SIGQUIT, on_signal);"), "4. main.c handles SIGHUP (unless inherited ignored) and SIGQUIT");
	CHECK(has("src/main.c", "nchildren, &wait_ts, &original)") && !has("src/main.c", "nchildren, &wait_ts, NULL)"), "4b. the main ppoll takes the original mask, not NULL");
	CHECK(has("src/main.c", "sigprocmask(SIG_BLOCK, &stops, &original);") && has("src/main.c", "sigprocmask(SIG_SETMASK, &original, NULL);"), "4c. blocked and restored around it");
	CHECK(has("src/rootside.c", "sigaction(SIGQUIT, &sa, NULL);") && has("src/rootside.c", "sigs[k] == SIGTERM || sigs[k] == SIGINT || sigs[k] == SIGQUIT"), "4e. rootside.c: SIGQUIT goes through the self-pipe and stops like SIGTERM (B1)");
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
