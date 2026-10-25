/* test.c — runwait.h and the child of run_as_root() (audit of the session, E-R9).  Real children, real exec:
 *   1. a helper that ends at once: run_wait() returns 1 with its exit status;
 *   2. a failing helper: the status is passed through (exit 3);
 *   3. a helper that never ends (`sleep 60`): after max_ms it is KILLED and run_wait() returns 2 (reaped) well before 60 s — the old waitpid(p,..,0) waited the whole time;
 *   4. the time: the stuck helper costs max_ms plus a little, not more;
 *   5. descriptors: a fork+exec built like the child of run_as_root() (close_range(3, ~0U) before the exec, as in sessione-e) shows ONLY 0, 1, 2 (+ the one `ls` opens itself) in /proc/self/fd, while
 *      a socket the parent holds open is NOT among them; the same fork without the close_range DOES inherit it (contrast);
 *   6. source reading of src/child.c: run_as_root() uses close_range and run_wait.
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /albero && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
 *        -Isrc benches/unit/run-wait/test.c -o /tmp/test && /tmp/test'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "runwait.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

static pid_t spawn(char *const argv[], int use_close_range, int out_fd)
{
	pid_t p = fork();

	if (p == 0) {
		if (out_fd >= 0) {
			dup2(out_fd, 1);
			close(out_fd);
		}
		if (use_close_range && close_range(3, ~0U, 0) != 0)
			_exit(126);
		execv(argv[0], argv);
		_exit(127);
	}
	return p;
}

static int has(const char *file, const char *needle)
{
	FILE *f = fopen(file, "r");
	static char src[8u << 20];
	size_t n;

	if (!f) return 0;
	n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
	return strstr(src, needle) != NULL;
}

/* how many descriptors above 2, listed by a child `sh` — and is `marker` among them */
static int listed_fds(int use_close_range, int marker, int *has_marker)
{
	int pp[2], n = 0;
	char buf[4096], want[32];
	char *argv[] = { "/bin/sh", "-c", "ls /proc/$$/fd", NULL };
	ssize_t r;
	size_t len = 0;
	char *tok;

	if (pipe(pp) != 0) return -1;
	pid_t p = spawn(argv, use_close_range, pp[1]);
	close(pp[1]);
	while ((r = read(pp[0], buf + len, sizeof buf - 1 - len)) > 0)
		len += (size_t)r;
	buf[len] = 0;
	close(pp[0]);
	waitpid(p, NULL, 0);
	snprintf(want, sizeof want, "%d", marker);
	*has_marker = 0;
	for (tok = strtok(buf, "\n"); tok; tok = strtok(NULL, "\n")) {
		if (atoi(tok) > 2)
			n++;
		if (strcmp(tok, want) == 0)
			*has_marker = 1;
	}
	return n;
}

int main(void)
{
	int st = 0, r;
	uint64_t t0;

	{
		char *a[] = { "/bin/true", NULL };
		r = run_wait(spawn(a, 1, -1), 5000, &st);
		CHECK(r == 1 && WIFEXITED(st) && WEXITSTATUS(st) == 0, "1. a helper that ends: 1, status 0");
	}
	{
		char *a[] = { "/bin/sh", "-c", "exit 3", NULL };
		r = run_wait(spawn(a, 1, -1), 5000, &st);
		CHECK(r == 1 && WIFEXITED(st) && WEXITSTATUS(st) == 3, "2. exit 3 passes through");
	}
	{
		char *a[] = { "/bin/sleep", "60", NULL };
		t0 = runwait_now_ms();
		r = run_wait(spawn(a, 1, -1), 300, &st);
		CHECK(r == 2 && WIFSIGNALED(st) && WTERMSIG(st) == SIGKILL, "3. a helper that never ends is killed after max_ms and reaped");
		CHECK(runwait_now_ms() - t0 < 1500, "4. and it costs max_ms plus a little, not 60 s");
	}
	{
		int sv[2], has_m, n_with, n_without;

		socketpair(AF_UNIX, SOCK_STREAM, 0, sv);   /* no CLOEXEC, like the service sockets of the audit */
		n_with = listed_fds(1, sv[0], &has_m);
		CHECK(!has_m && n_with <= 1, "5. with close_range(3, ~0U) the helper sees only 0-2 (and the one `ls` itself opens)");
		n_without = listed_fds(0, sv[0], &has_m);
		CHECK(has_m && n_without >= 2, "5b. (contrast) without it the helper inherits the parent's socket");
	}
	CHECK(has("src/child.c", "close_range(3, ~0U, 0)") && has("src/child.c", "run_wait(p, RUN_AS_ROOT_MAX_MS, &state)") && !has("src/child.c", "if (waitpid(p, &state, 0) != p)\n		return false;\n	if (!WIFEXITED(state)"),
	      "6. child.c: run_as_root closes the descriptors and waits with a limit");
	CHECK(has("src/child.c", "if (ran == RUN_NOT_STARTED)\n		ran = run_as_root(\"/sbin/usermod\"") && has("src/child.c", "if (ran == RUN_TIMED_OUT)") && has("src/child.c", "user_in_group_now(user, primary, seen_items[placed[j]])"),
	      "7. enrolment: /sbin/usermod only if the first did not start; after a timeout the groups are read again");
	CHECK(has("src/child.c", "WEXITSTATUS(state) == 127)\n		return RUN_NOT_STARTED"), "7b. exit 127 is 'not started'");
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
