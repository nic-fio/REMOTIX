/* test.c — xfertime.h (audit of the session, S-R5 and S-R6): the deadline is ABSOLUTE.  REAL pipes, a REAL slow peer (a thread):
 *   1. xfer_left_ms(): the step when plenty is left, what is left when less, 0 when passed;
 *   2. a reader that gets one byte every 80 ms from a writer: the loop built like slurp_fd() ends at the deadline, NOT after the 20 steps it would take
 *      (the per-step wait alone would never fire);
 *   3. a writer into a pipe nobody reads (non-blocking, as the reply paths now do): gives up at the deadline, after the 64 KiB the pipe takes, and does not hang;
 *   4. a fast peer is not disturbed: 1 MB through a pipe with a reader draining it completes well before the deadline;
 *   5. the four users (clipboard.c: slurp_fd and the GNOME reply; clipboard_kde.c: ready() for read_type and the reply) are wired to xfertime.h (source reading).
 * Build: cc -std=gnu11 -fsanitize=address,undefined -fno-sanitize-recover=undefined -I src benches/unit/xfer-time/test.c -o t -lpthread && ./t   (from the root of the tree)
 * The test shortens the deadline by calling xfer_wait() with its own deadline value; XFER_TOTAL_MS itself is only checked to be set. */
#include "xfertime.h"
#include <fcntl.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

static int slow_fd;
static void *slow_writer(void *a)
{
	(void)a;
	for (int i = 0; i < 40; i++) {
		usleep(80000);
		if (write(slow_fd, "x", 1) != 1)
			break;
	}
	close(slow_fd);
	return NULL;
}

static int drain_fd;
static void *drainer(void *a)
{
	char b[65536];
	(void)a;
	while (read(drain_fd, b, sizeof b) > 0)
		;
	return NULL;
}

static int has(const char *file, const char *needle)
{
	FILE *f = fopen(file, "r");
	static char src[2u << 20];
	size_t n;

	if (!f) return 0;
	n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
	return strstr(src, needle) != NULL;
}

int main(void)
{
	uint64_t t0, d;

	signal(SIGPIPE, SIG_IGN);

	CHECK(XFER_TOTAL_MS > 0, "0. a total is set");
	d = xfer_now_ms() + 10000;
	CHECK(xfer_left_ms(d, 5000) == 5000 && xfer_left_ms(xfer_now_ms() + 100, 5000) <= 100 && xfer_left_ms(xfer_now_ms() - 1, 5000) == 0 && xfer_left_ms(0, 5000) == 0, "1. step / what is left / zero");

	{
		int p[2];
		pthread_t th;
		char c;
		int got = 0;

		if (pipe(p) != 0) return 2;
		slow_fd = p[1];
		pthread_create(&th, NULL, slow_writer, NULL);
		t0 = xfer_now_ms();
		d = t0 + 1000;
		while (xfer_wait(p[0], POLLIN, d, 5000)) {          /* the loop of slurp_fd(): the step alone (5 s) would never fire */
			if (read(p[0], &c, 1) <= 0)
				break;
			got++;
		}
		CHECK(xfer_now_ms() - t0 < 1400 && xfer_now_ms() - t0 >= 900, "2. one byte every 80 ms: the loop ends at the 1000 ms deadline");
		CHECK(got >= 5 && got <= 14, "2b. and it did read what came in the meantime");
		close(p[0]);
		pthread_join(th, NULL);
	}

	{
		int p[2];
		static char big[1 << 20];
		size_t written = 0;
		int ok = 1;

		if (pipe(p) != 0) return 2;
		fcntl(p[1], F_SETFL, fcntl(p[1], F_GETFL) | O_NONBLOCK);
		t0 = xfer_now_ms();
		d = t0 + 500;
		while (written < sizeof big) {
			ssize_t w = write(p[1], big + written, sizeof big - written);

			if (w < 0 && errno == EAGAIN) {
				if (xfer_wait(p[1], POLLOUT, d, 1000))
					continue;
				ok = 0;
				break;
			}
			if (w <= 0)
				break;
			written += (size_t)w;
		}
		CHECK(!ok && written > 0 && written < sizeof big, "3. a pipe nobody reads: gives up (after what the pipe takes)");
		CHECK(xfer_now_ms() - t0 < 900, "3b. at the deadline, not later");
		close(p[0]); close(p[1]);
	}

	{
		int p[2];
		pthread_t th;
		static char big[1 << 20];
		size_t written = 0;
		int ok = 1;

		if (pipe(p) != 0) return 2;
		drain_fd = p[0];
		pthread_create(&th, NULL, drainer, NULL);
		fcntl(p[1], F_SETFL, fcntl(p[1], F_GETFL) | O_NONBLOCK);
		t0 = xfer_now_ms();
		d = t0 + 5000;
		while (written < sizeof big) {
			ssize_t w = write(p[1], big + written, sizeof big - written);

			if (w < 0 && errno == EAGAIN) {
				if (xfer_wait(p[1], POLLOUT, d, 1000))
					continue;
				ok = 0;
				break;
			}
			if (w <= 0)
				break;
			written += (size_t)w;
		}
		CHECK(ok && written == sizeof big && xfer_now_ms() - t0 < 2000, "4. a draining reader: 1 MB goes through, well before the deadline");
		close(p[1]);
		pthread_join(th, NULL);
		close(p[0]);
	}

	CHECK(has("src/clipboard.c", "xfer_wait(fd, POLLIN, deadline, WAIT_READ_MS)") && has("src/clipboard.c", "xfer_wait(fd, POLLOUT, deadline, XFER_TOTAL_MS)") && has("src/clipboard.c", "O_NONBLOCK"), "5. clipboard.c: slurp_fd and the GNOME reply use it");
	CHECK(has("src/clipboard_kde.c", "xfer_left_ms(deadline, WAIT_TRANSFER_MS)") && has("src/clipboard_kde.c", "ready(pipe_fd[0], POLLIN, deadline)") && has("src/clipboard_kde.c", "ready(fd, POLLOUT, deadline)") && has("src/clipboard_kde.c", "O_NONBLOCK"), "5b. clipboard_kde.c: read_type and the reply use it, the fd is non-blocking");
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
