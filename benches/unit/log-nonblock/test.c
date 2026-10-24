/* test.c — a log line never stops the loop (15 Oct 2026).
 *
 * Under systemd `stderr` is journald's blocking STREAM socket, and the line
 * that fell back to it (native journal send failed, or `--journal` off) went
 * out with a plain `write(2)`: a stalled journald stopped the loop that
 * delivers every session's frames.  Now `stderr` is written without waiting
 * (a socket with MSG_DONTWAIT, a pipe through a second, O_NONBLOCK open of
 * it), a line that does not fit is dropped and counted, and the count is
 * written as soon as `stderr` accepts again.
 *
 *   L1  stderr a stream socket nobody reads: 4000 lines, none waits > 10 ms;
 *   L2  … what was read back is whole lines only, and the next line comes
 *       after a notice with EXACTLY the number dropped;
 *   L3  stderr a pipe nobody reads: the same;
 *   L4  --journal with the native send failing (no journald here) and
 *       JOURNAL_STREAM naming stderr: the fallback does not wait either;
 *   L5  fd 2 redirected to a file afterwards: the lines go to the file;
 *   L6  a value with a newline, CR, tab, ESC: one line, each control byte `?`;
 *   L7  a child writing to the same stream between our lines: nothing spliced.
 *
 * ⚠ On a log.c that writes stderr with a plain write(2), L1 blocks: an
 *   alarm turns that into «BLOCKED» and exit 1.
 *
 * BUILD AND RUN (a few seconds; timing test, so no sanitizers; the real src/log.c; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=2 --memory=2g -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -std=gnu11 -D_GNU_SOURCE -O1 -Wall -Wextra -Wno-unused-parameter -I/albero/src \
 *       -o test /albero/benches/unit/log-nonblock/test.c /albero/src/log.c -lpthread && ./test'
 * Exit code 0 green, 1 red, 3 not all checks ran.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "log.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 15
#define LINES 4000

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	fflush(stdout);
	if (cond)
		passed++;
	else
		failures++;
}

static double now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

static void on_alarm(int sig)
{
	(void)sig;
	static const char m[] = "    NO  BLOCKED: a log line waited for a full stderr\n";
	ssize_t w = write(STDOUT_FILENO, m, sizeof m - 1);
	(void)w;
	_exit(1);
}

/* Everything readable on `fd` now, into `buf` (NUL-terminated). */
static size_t drain(int fd, char *buf, size_t cap)
{
	size_t n = 0;

	fcntl(fd, F_SETFL, fcntl(fd, F_GETFL) | O_NONBLOCK);
	for (;;) {
		ssize_t r = read(fd, buf + n, cap - 1 - n);

		if (r <= 0)
			break;
		n += (size_t)r;
		if (n >= cap - 1)
			break;
	}
	buf[n] = '\0';
	return n;
}

/* Whole lines only: each starts «HH:MM:SS.mmm » and ends with '\n';
 * returns how many «line N» lines there are, -1 if any line is broken. */
static int whole_lines(const char *buf, size_t n)
{
	int count = 0;
	const char *p = buf, *end = buf + n;

	while (p < end) {
		const char *nl = memchr(p, '\n', (size_t)(end - p));
		int hh, mm, ss, ms;
		char sp;

		if (!nl)
			return -1;
		if (sscanf(p, "%2d:%2d:%2d.%3d%c", &hh, &mm, &ss, &ms, &sp) != 5 || sp != ' ')
			return -1;
		/* two «test line» in one line = a cut line merged with the next */
		{
			const char *f = memmem(p, (size_t)(nl - p), "test line ", 10);
			if (f && memmem(f + 10, (size_t)(nl - f - 10), "test line ", 10))
				return -1;
		}
		if (memmem(p, (size_t)(nl - p), "test line ", 10))
			count++;
		p = nl + 1;
	}
	return count;
}

static char big[8 << 20];

/* Fills `fd 2` (whatever it is) until lines are dropped; the slowest line. */
static double flood(void)
{
	double worst = 0;
	char pad[200];

	memset(pad, 'x', sizeof pad - 1);
	pad[sizeof pad - 1] = '\0';
	alarm(20);
	for (int i = 0; i < LINES; i++) {
		double t0 = now_ms();

		registro_dice(LOG_STARTUP, "test line %d %s", i, pad);
		if (now_ms() - t0 > worst)
			worst = now_ms() - t0;
	}
	alarm(0);
	return worst;
}

static void check_after(int rd, const char *what)
{
	size_t n = drain(rd, big, sizeof big);
	int got = whole_lines(big, n);
	char desc[200];
	const char *notice;
	unsigned long long d = 0;

	snprintf(desc, sizeof desc, "%s: what was read back is whole lines only (%d of %d)",
	         what, got, LINES);
	require(got > 0 && got < LINES, desc);
	registro_dice(LOG_STARTUP, "after the flood");
	n = drain(rd, big, sizeof big);
	notice = strstr(big, "log     ⚠ ");
	if (notice && sscanf(notice + strlen("log     ⚠ "), "%llu", &d) != 1)
		notice = NULL;
	if (notice && !strstr(notice, "DROPPED"))
		notice = NULL;
	snprintf(desc, sizeof desc,
	         "%s: then a notice «%llu log lines DROPPED» (= %d), then the next line",
	         what, d, LINES - got);
	require(notice && got >= 0 && d == (unsigned long long)(LINES - got) &&
	        strstr(big, "after the flood") > notice, desc);
}

int main(void)
{
	int sv[2], pp[2];
	int sndbuf = 4096;
	double worst;

	signal(SIGALRM, on_alarm);
	signal(SIGPIPE, SIG_IGN);

	printf("L1-L2 stderr is a stream socket nobody reads\n");
	if (socketpair(AF_UNIX, SOCK_STREAM, 0, sv) != 0)
		return 2;
	setsockopt(sv[0], SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof sndbuf);
	dup2(sv[0], STDERR_FILENO);
	worst = flood();
	printf("        (slowest line: %.3f ms)\n", worst);
	require(worst < 10, "L1 4000 lines into a full socket: none waits > 10 ms");
	check_after(sv[1], "L2 socket");

	printf("L3 stderr is a pipe nobody reads\n");
	if (pipe(pp) != 0)
		return 2;
	dup2(pp[1], STDERR_FILENO);
	close(pp[1]);
	worst = flood();
	printf("        (slowest line: %.3f ms)\n", worst);
	require(worst < 10, "L3 4000 lines into a full pipe: none waits > 10 ms");
	check_after(pp[0], "L3 pipe");
	{
		int fl = fcntl(STDERR_FILENO, F_GETFL);
		require(!(fl & O_NONBLOCK), "L3 fd 2 itself is left blocking (the shared open file is untouched)");
	}

	printf("L4 --journal, native send failing, stderr is «the journal stream»\n");
	{
		struct stat st;
		char js[64];

		dup2(sv[0], STDERR_FILENO);
		drain(sv[1], big, sizeof big);
		fstat(STDERR_FILENO, &st);
		snprintf(js, sizeof js, "%llu:%llu", (unsigned long long)st.st_dev,
		         (unsigned long long)st.st_ino);
		setenv("JOURNAL_STREAM", js, 1);
		require(log_journal(true), "L4 journal on (stderr is declared as its stream by JOURNAL_STREAM)");
		worst = flood();
		printf("        (slowest line: %.3f ms)\n", worst);
		require(worst < 10, "L4 the fallback to a full stderr: none waits > 10 ms");
		check_after(sv[1], "L4 fallback");
		log_journal(false);
	}

	printf("L5 fd 2 redirected to a file afterwards\n");
	{
		char path[] = "/tmp/lnb-XXXXXX";
		int fd = mkstemp(path);
		char buf[4096];
		ssize_t n;

		dup2(fd, STDERR_FILENO);
		registro_dice(LOG_STARTUP, "into the file");
		n = pread(fd, buf, sizeof buf - 1, 0);
		buf[n > 0 ? n : 0] = '\0';
		require(n > 0 && strstr(buf, "into the file"), "L5 the line went to the new fd 2");

		/* L6 (holistic review, 15 Oct 2026): a value carrying a newline
		 * cannot forge a second line; control bytes become `?`, UTF-8 stays. */
		{
			off_t at = lseek(fd, 0, SEEK_END);
			int lines = 0;
			registro_dice(LOG_PAGE, "GET %s from x ⭐",
			              "/\n14:00:00.000 rcp     [owner] ⭐ ADMITTED\r\t\x1b[2J");
			n = pread(fd, buf, sizeof buf - 1, at);
			buf[n > 0 ? n : 0] = '\0';
			for (ssize_t k = 0; k < n; k++)
				lines += buf[k] == '\n';
			require(n > 0 && lines == 1 && buf[n - 1] == '\n' &&
			                strstr(buf, "GET /?14:00:00.000 rcp     [owner] ⭐ ADMITTED???[2J from x ⭐\n"),
			        "L6 a newline, CR, tab and ESC in a value: ONE line, each byte a `?`, UTF-8 kept");
			/* reviews of 95ed70ea, 38639d7d, fc76de93: DEL, C1 controls as
			 * UTF-8 (U+0085, U+009B) and as lone raw bytes (0x85), the bidi
			 * controls and marks (U+202E, U+2066, U+200E, U+200F, U+061C),
			 * U+2028/9, U+2060–U+2064 and U+FEFF are `?`; other UTF-8
			 * (U+00A0, U+200D, é) and a lone non-C1 byte (0xA0) stay */
			at = lseek(fd, 0, SEEK_END);
			registro_dice(LOG_PAGE, "X%sY", "a\x7f" "b\xc2\x85" "c\xc2\x9b" "d\xe2\x80\xae"
			              "e\xe2\x81\xa6" "f\xe2\x80\xa9" "g\xc2\xa0" "h\xe2\x80\xa8"
			              "i\xe2\x80\x8e" "j\xe2\x80\x8f" "k\xd8\x9c" "l\xe2\x80\x8d" "m"
			              "\xef\xbb\xbf" "n\xe2\x81\xa0" "o\xe2\x81\xa4" "p\x85" "q\xa0" "r\xc3\xa9");
			n = pread(fd, buf, sizeof buf - 1, at);
			buf[n > 0 ? n : 0] = '\0';
			require(n > 0 && strstr(buf, "Xa?b?c?d?e?f?g\xc2\xa0h?i?j?k?l\xe2\x80\x8dm?n?o?p?q\xa0r\xc3\xa9Y\n"),
			        "L6 DEL, C1 (UTF-8 and lone bytes), bidi controls and marks, U+2028/9, U+2060–4, U+FEFF become `?`; other UTF-8 stays");
		}
		unlink(path);
	}

	/* L7 (independent review of 16b75f33): a line the stream socket takes
	 * only in part must not have its rest spliced in after ANOTHER writer's
	 * line (a child writing to the same journald stream). */
	printf("L7 a child writes to the same stream between our lines\n");
	{
		int sp[2], bad = 0, nlines = 0, sb = 1;
		static char got[1 << 22];
		size_t ng = 0;
		/* longer than half the smallest send buffer: the kernel splits it
		 * in two pieces, and the second may not fit */
		char fill[3000];

		memset(fill, 'f', sizeof fill - 1);
		fill[sizeof fill - 1] = 0;
		socketpair(AF_UNIX, SOCK_STREAM, 0, sp);
		setsockopt(sp[0], SOL_SOCKET, SO_SNDBUF, &sb, sizeof sb);
		dup2(sp[0], STDERR_FILENO);
		for (int i = 0; i < 2000; i++) {
			registro_dice(LOG_STARTUP, "L7 %d %s", i, fill);
			/* the reader catches up now and then — and the child writes
			 * right after it, before our next line */
			if (i % 7 == 6)
				ng += drain(sp[1], got + ng, sizeof got - ng - 1);
			if (send(sp[0], "CHILD\n", 6, MSG_DONTWAIT | MSG_NOSIGNAL) < 0)
				(void)0;
		}
		registro_dice(LOG_STARTUP, "L7 the last");
		ng += drain(sp[1], got + ng, sizeof got - ng - 1);
		got[ng] = 0;
		for (char *l = got, *e; *l; l = e + 1) {
			e = strchr(l, '\n');
			if (!e)
				break;
			nlines++;
			bool stamp = e - l > 13 && l[2] == ':' && l[5] == ':' && l[8] == '.';
			bool child = e - l == 5 && strncmp(l, "CHILD", 5) == 0;
			if (!stamp && !child)
				bad++;
			else if (stamp && memmem(l, (size_t)(e - l), "CHILD", 5))
				bad++;
		}
		printf("        (%d lines read, %d spliced)\n", nlines, bad);
		require(nlines > 100 && bad == 0,
		        "L7 every line is ours, whole, or the child's — nothing spliced across them");
		close(sp[0]);
		close(sp[1]);
	}

	printf("%d/%d passed, %d failed\n", passed, EXPECTED_CHECKS, failures);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
