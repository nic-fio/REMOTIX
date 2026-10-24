/*
 * log.c — see log.h.
 */
#include "log.h"

#include <errno.h>
#include <fcntl.h>
#include <linux/sockios.h>
#include <pthread.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/uio.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

static bool verbose;

/* ⭐ The journal (box in `log.h`): -1 = off.  ⚠ It is opened ONCE, at
 *    switch-on and not at the first line: `line()` runs in several threads,
 *    and two threads opening together would leave an orphan descriptor. */
static int journal_fd = -1;
static bool stderr_in_journal;

static bool stderr_is_journal(void)
{
	const char *js = getenv("JOURNAL_STREAM");
	struct stat st;
	unsigned long dev = 0, ino = 0;

	if (js && sscanf(js, "%lu:%lu", &dev, &ino) == 2 &&
	    fstat(STDERR_FILENO, &st) == 0 &&
	    (unsigned long)st.st_dev == dev && (unsigned long)st.st_ino == ino)
		return true;
	struct sockaddr_un sa;
	socklen_t sl = sizeof sa;
	memset(&sa, 0, sizeof sa);
	if (getpeername(STDERR_FILENO, (struct sockaddr *)&sa, &sl) == 0 &&
	    sa.sun_family == AF_UNIX &&
	    sl > (socklen_t)offsetof(struct sockaddr_un, sun_path) &&
	    strncmp(sa.sun_path, "/run/systemd/journal/", 21) == 0)
		return true;
	return false;
}

/* ⭐ The identity of this process — the box is in `log.h`.  ⚠ A COPY and
 *    not a pointer: whoever sets it often passes an `argv`, and a pointer to
 *    someone else's memory is a log that lies the day that memory changes. */
static char identity[LOG_IDENTITY_MAX + 1];

void log_chatter(bool is_on) { verbose = is_on; }
bool log_verbose(void) { return verbose; }

void log_identity(const char *chi)
{
	if (!chi || !*chi) {
		identity[0] = '\0';
		return;
	}
	snprintf(identity, sizeof identity, "%s", chi);
}

bool log_journal(bool is_on)
{
	if (!is_on) {
		if (journal_fd >= 0)
			close(journal_fd);
		journal_fd = -1;
		stderr_in_journal = false;
		return true;
	}
	if (journal_fd >= 0)
		return true;
	/* ⛔ NON-BLOCKING: a clogged journal must not stop the loop that serves
	 *    the screen — the line on `stderr` is there anyway.  ⚠ And CLOEXEC:
	 *    the child is born with `execve` and opens its own (`--journal`). */
	journal_fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
	stderr_in_journal = journal_fd >= 0 && stderr_is_journal();
	return journal_fd >= 0;
}

bool log_to_journal(void) { return journal_fd >= 0; }

bool log_speakable_key(unsigned c)
{
	/* `linux/input-event-codes.h`: LEFTCTRL 29, LEFTSHIFT 42, RIGHTSHIFT 54,
	 * LEFTALT 56, CAPSLOCK 58, RIGHTCTRL 97, RIGHTALT 100, LEFTMETA 125,
	 * RIGHTMETA 126.  ⚠ By hand and not with the header: the number belongs to
	 * the protocol (`RCP.md` §7.3, «evdev code»), not to the machine. */
	switch (c) {
	case 29: case 42: case 54: case 56: case 58:
	case 97: case 100: case 125: case 126:
		return true;
	default:
		return false;
	}
}

/*
 * ⭐ One line to the journal, with the native protocol — `systemd.journal-fields(7)`
 *    and systemd's «Native Journal Protocol» page.
 *
 * ⚠ The MESSAGE goes in the BINARY form (name, newline, length in 64-bit
 *   little-endian, bytes): it is the only one that holds a newline inside the
 *   value, and a body written by someone else's `%s` may have one.  The other
 *   fields are ours (constant area, identity already cleaned, `__FILE__`) and
 *   go in the simple form.
 * ⛔ `sendmsg` with the address at every line and NOT `connect` once: a
 *    connected socket stays dead forever if journald restarts, one without a
 *    connection finds the new one at the next datagram.
 */
static bool al_journal(const char *file, int text_line, const char *area,
                       const char *chi, int priority, const char *msg,
                       size_t msg_n)
{
	static const struct sockaddr_un dove = {
		.sun_family = AF_UNIX,
		.sun_path = "/run/systemd/journal/socket",
	};
	char fields[384];
	uint8_t lung[8];
	int n = snprintf(fields, sizeof fields,
	                 "PRIORITY=%d\nSYSLOG_IDENTIFIER=remotix\n"
	                 "REMOTIX_AREA=%s\n%s%s%sCODE_FILE=%s\nCODE_LINE=%d\n"
	                 "MESSAGE\n",
	                 priority, area, chi ? "REMOTIX_TENANT=" : "",
	                 chi ? chi : "", chi ? "\n" : "", file ? file : "?", text_line);
	if (n < 0 || (size_t)n >= sizeof fields)
		return false;
	for (int i = 0; i < 8; i++)
		lung[i] = (uint8_t)((uint64_t)msg_n >> (8 * i));
	struct iovec iov[4] = {
		{fields, (size_t)n},
		{lung, sizeof lung},
		{(void *)msg, msg_n},
		{(void *)"\n", 1},
	};
	struct msghdr mh = {
		.msg_name = (void *)&dove,
		.msg_namelen = sizeof dove,
		.msg_iov = iov,
		.msg_iovlen = 4,
	};
	ssize_t r = sendmsg(journal_fd, &mh, MSG_NOSIGNAL | MSG_DONTWAIT);
	return r >= 0; /* ⚠ silent: the channel that remains is `stderr`, and the line is there */
}

/*
 * ⛔⭐ STDERR MUST NEVER STOP THE LOOP — 15 Oct 2026.
 *
 * Under systemd `stderr` is journald's STREAM socket, and it is BLOCKING: the
 * native send above does not wait (`MSG_DONTWAIT`), but the line that falls
 * back to `stderr` — and every line when `--journal` is off — went out with a
 * plain `write(2)`.  A journald that stalls fills the socket, and the
 * `write` stops the single loop that delivers every session's frames, for as
 * long as journald likes.
 *
 * ⭐ The cure: `stderr` is written WITHOUT waiting when it can block —
 *   · a socket: `send(MSG_DONTWAIT)`;
 *   · a pipe: a SECOND open of the same pipe (`/proc/self/fd/2`) with
 *     `O_NONBLOCK` — ⚠ not `fcntl` on fd 2 or on a `dup`, which share the
 *     open file with the parent's shell and would change it for others too.
 *     A line is < `PIPE_BUF`, so it goes in whole or not at all;
 *   · a file or a terminal: as before.
 * ⛔ A line that does not fit is DROPPED and COUNTED, and the count is written
 *    as soon as `stderr` accepts again — a hole in the log that is declared,
 *    instead of a loop that stops.  ⚠ A stream socket may take a line in
 *    part: the rest is kept and goes out first, so that the next line does not
 *    begin in the middle of this one.
 * ⚠ fd 2 is looked at again (`fstat`) at every line: whoever redirects it
 *   later must not be written through a descriptor of the old one.
 */
enum { ERR_PLAIN, ERR_SOCKET, ERR_PIPE };
static pthread_mutex_t err_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_once_t err_once = PTHREAD_ONCE_INIT;
static bool err_known;
static dev_t err_dev;
static ino_t err_ino;
static int err_kind = ERR_PLAIN;
static int err_nb = -1;
static char err_tail[4096];
static size_t err_tail_n;
static unsigned long long err_dropped;

/* ⚠ A child forked while another thread writes must not inherit the lock taken. */
static void err_prepare(void) { pthread_mutex_lock(&err_lock); }
static void err_release(void) { pthread_mutex_unlock(&err_lock); }
static void err_init(void) { pthread_atfork(err_prepare, err_release, err_release); }

/* With `err_lock` held: what fd 2 is now. */
static void err_look(void)
{
	struct stat st;

	if (fstat(STDERR_FILENO, &st) != 0) {
		err_known = false;
		err_kind = ERR_PLAIN;
		return;
	}
	if (err_known && st.st_dev == err_dev && st.st_ino == err_ino)
		return;
	if (err_nb >= 0)
		close(err_nb);
	err_nb = -1;
	err_tail_n = 0;
	err_known = true;
	err_dev = st.st_dev;
	err_ino = st.st_ino;
	err_kind = ERR_PLAIN;
	if (S_ISSOCK(st.st_mode)) {
		err_kind = ERR_SOCKET;
	} else if (S_ISFIFO(st.st_mode)) {
		err_nb = open("/proc/self/fd/2", O_WRONLY | O_NONBLOCK | O_CLOEXEC);
		if (err_nb >= 0)
			err_kind = ERR_PIPE;
	}
}

static ssize_t err_out(const char *b, size_t n)
{
	ssize_t r;

	switch (err_kind) {
	case ERR_SOCKET:
		/* ⛔ All or nothing (independent review of 16b75f33): a line the
		 *    stream socket would take only in part is NOT started — its
		 *    rest, sent later, could land after a CHILD's line written to
		 *    the same journald stream in between (21 Aug's «line without a
		 *    timestamp»).  The room is the send buffer minus what is queued
		 *    (both in the kernel's own accounting), with a margin for it. */
		{
			int queued = 0, cap = 0;
			socklen_t cl = sizeof cap;
			if (ioctl(STDERR_FILENO, SIOCOUTQ, &queued) == 0 &&
			    getsockopt(STDERR_FILENO, SOL_SOCKET, SO_SNDBUF, &cap, &cl) == 0 &&
			    (long)cap - queued < (long)n + 2048) {
				errno = EAGAIN;
				return -1;
			}
		}
		r = send(STDERR_FILENO, b, n, MSG_DONTWAIT | MSG_NOSIGNAL);
		if (r < 0 && errno == ENOTSOCK)
			r = write(STDERR_FILENO, b, n);
		return r;
	case ERR_PIPE:
		return write(err_nb, b, n);
	default:
		return write(STDERR_FILENO, b, n);
	}
}

/* With `err_lock` held: one whole piece out, or kept (the rest of a stream
 * line), or nothing.  True if it all went. */
static bool err_piece(const char *b, size_t n)
{
	ssize_t r = err_out(b, n);

	if (r < 0)
		/* ⚠ EAGAIN: full.  Any other error: nowhere to report it (the
		 *   only channel would be the broken one), as before. */
		return !(errno == EAGAIN || errno == EWOULDBLOCK);
	if ((size_t)r < n && err_kind == ERR_SOCKET) {
		/* ⚠ Taken in part all the same (the margin was not enough): the
		 *   REST is not spliced into the stream later; the cut line is
		 *   only closed, with a mark, at the first chance. */
		static const char cut[] = " …[line cut: stderr full]\n";
		err_tail_n = sizeof cut - 1;
		memcpy(err_tail, cut, err_tail_n);
		err_dropped++;
	} else if ((size_t)r < n && err_kind == ERR_PLAIN) {
		/* a short write to a file or a terminal: the rest, now (a file
		 * does not make us wait) — not silently lost */
		size_t done = (size_t)r;
		while (done < n) {
			ssize_t k = write(STDERR_FILENO, b + done, n - done);
			if (k <= 0) {
				err_dropped++;
				break;
			}
			done += (size_t)k;
		}
	}
	return true;
}

/* How many lines were dropped and not told yet — taken (zeroed). */
static unsigned long long err_take_dropped(void)
{
	unsigned long long d;

	pthread_once(&err_once, err_init);
	pthread_mutex_lock(&err_lock);
	d = err_dropped;
	err_dropped = 0;
	pthread_mutex_unlock(&err_lock);
	return d;
}

static void err_give_back(unsigned long long d)
{
	pthread_mutex_lock(&err_lock);
	err_dropped += d;
	pthread_mutex_unlock(&err_lock);
}

static int dropped_notice(char *b, size_t cap, unsigned long long d, bool with_time)
{
	struct timespec ts;
	struct tm tm;
	char when[32];

	if (!with_time)
		return snprintf(b, cap,
		                "log     ⚠ %llu log line%s DROPPED: stderr was not "
		                "accepting (journald stalled?) and the loop does not "
		                "wait for it",
		                d, d == 1 ? "" : "s");
	clock_gettime(CLOCK_REALTIME, &ts);
	localtime_r(&ts.tv_sec, &tm);
	strftime(when, sizeof when, "%H:%M:%S", &tm);
	return snprintf(b, cap,
	                "%s.%03ld log     ⚠ %llu log line%s DROPPED: stderr was not "
	                "accepting (journald stalled?) and the loop does not wait "
	                "for it\n",
	                when, ts.tv_nsec / 1000000, d, d == 1 ? "" : "s");
}

/* ⭐ One line to `stderr`, never waiting. */
static void err_write(const char *buf, size_t n)
{
	char notice[256];

	pthread_once(&err_once, err_init);
	pthread_mutex_lock(&err_lock);
	err_look();
	if (err_tail_n) {
		ssize_t r = err_out(err_tail, err_tail_n);

		if (r > 0) {
			memmove(err_tail, err_tail + r, err_tail_n - (size_t)r);
			err_tail_n -= (size_t)r;
		} else if (r < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
			err_tail_n = 0;
		}
		if (err_tail_n) {
			err_dropped++;
			goto out;
		}
	}
	if (err_dropped) {
		int k = dropped_notice(notice, sizeof notice, err_dropped, true);

		if (k <= 0 || (size_t)k >= sizeof notice)
			k = 0;
		if (k && !err_piece(notice, (size_t)k)) {
			err_dropped++;
			goto out;
		}
		err_dropped = 0;
		if (err_tail_n) {
			err_dropped++;
			goto out;
		}
	}
	if (!err_piece(buf, n))
		err_dropped++;
out:
	pthread_mutex_unlock(&err_lock);
}

uint64_t log_now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000u + (uint64_t)(ts.tv_nsec / 1000000);
}

static void line(const char *file, int text_line, bool detail, const char *area,
                 const char *chi, const char *fmt, va_list ap)
{
	struct timespec ts;
	struct tm tm;
	char when[32];
	/* ⛔ 4096 is `PIPE_BUF`, the boundary below which an append `write` does
	 *    not interleave with those of other processes. */
	char buf[4096];

	clock_gettime(CLOCK_REALTIME, &ts);
	localtime_r(&ts.tv_sec, &tm);
	strftime(when, sizeof when, "%H:%M:%S", &tm);

	/* ⛔⛔ ONE SINGLE `write()` PER LINE, AND IT IS NOT ELEGANCE — 21 Aug 2026.
	 *
	 *      Before, there were THREE calls here on an unbuffered `stderr`
	 *      (header, body, newline), that is at least three `write()`.  ⚠ The
	 *      parent and the child append to the SAME file: when the writes
	 *      overlap, a body ends up after someone else's newline and a line
	 *      WITHOUT A TIMESTAMP is born.
	 *
	 * `[M]` measured on a real log of 3.0 MB (28 035 lines): **23 orphan
	 *      lines**, and among them **3 out of 80** of the «canvas REQUESTED from
	 *      the producer» — that is 3.8 % of a family of lines a tool counted on.
	 *      ⇒ The symptom was not «the log is ugly»: it was a tool dying with
	 *      `ValueError`, and getting there took one bench round.
	 *
	 * ⛔ And the worst defect is the one that makes NOTHING die: a count that
	 *    loses 3.8 % of its lines stays plausible.  The log is the main
	 *    diagnostic tool of this project (`LESSONS.md` §2.7): if it lies under
	 *    load, it lies precisely when it is needed.
	 *
	 * ⭐ Direct `write(2)` instead of `stdio`: a line below `PIPE_BUF` (4096
	 *    on Linux) written with a single `write` on a file opened in append is
	 *    atomic with respect to the others.  ⚠ Whatever exceeds the buffer is
	 *    TRUNCATED with a mark, instead of going out interleaved: a cut line
	 *    can be seen, an interleaved line cannot.
	 * ⚠ It WAS async-signal-safe; since 15 Oct 2026 `err_write()` takes a
	 *   lock (no signal handler of the product logs: they set a flag). */
	/* ⭐⭐ AND IN HERE IT IS SAID WHOSE LINE IT IS — 25 Aug 2026, R10-A4.
	 *
	 *     The identity of the single line beats that of the process: in the
	 *     parent a single process serves all the sessions, and the second
	 *     does not exist.
	 *     ⛔ But the bracket is composed ONLY here: the box in `log.h`
	 *        says why, and it is the reason the callers pass the bare name
	 *        instead of the ready-made string.
	 *
	 * ⛔ At the HEAD OF THE BODY, not between the time and the area, and it is
	 *    not aesthetics: whoever reads the log splits it into «time · area ·
	 *    body» and a new field in the middle moves the area under their eyes.
	 *    At the head of the body, an old reader keeps reading, and a new one
	 *    detaches it.
	 * ⚠ And the extra bytes are paid ONLY by the lines that have something to
	 *   say: whoever does not know stays silent, and does not pay. */
	const char *id = (chi && *chi) ? chi : identity;
	char safe_id[LOG_IDENTITY_MAX + 1];
	int n;
	/* ⭐ For the journal: where the line without the time begins (the MESSAGE)
	 *    and where the body begins (from which the severity is read). */
	int without_time, body;
	bool con_id = false;
	if (id && *id) {
		con_id = true;
		/* ⛔ IT IS CLEANED, and it is not distrust of PAM: a `]` or a newline
		 *    inside the identifier would split the line in two, and a split
		 *    line is **plausible and false** — the defect that the cure of
		 *    21 Aug (one single `write` per line) has just finished
		 *    removing.  ⚠ Only what fits in a user name is kept. */
		size_t k = 0;
		for (const char *p = id; *p && k < LOG_IDENTITY_MAX; p++, k++) {
			unsigned char c = (unsigned char)*p;
			bool good = (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z')
			             || (c >= 'a' && c <= 'z') || c == '.' || c == '_'
			             || c == '-' || c == '@' || c == ':';
			safe_id[k] = good ? (char)c : '_';
		}
		safe_id[k] = '\0';
		n = snprintf(buf, sizeof buf, "%s.%03ld %-7s [%s] ", when,
		             ts.tv_nsec / 1000000, area, safe_id);
	} else
		n = snprintf(buf, sizeof buf, "%s.%03ld %-7s ", when,
		             ts.tv_nsec / 1000000, area);
	if (n < 0)
		return;
	if ((size_t)n > sizeof buf - 2)
		n = (int)(sizeof buf - 2);
	without_time = (int)strlen(when) + 5; /* «HH:MM:SS» + «.mmm » */
	if (without_time > n)
		without_time = n;
	body = n;
	int m = vsnprintf(buf + n, sizeof buf - (size_t)n - 1, fmt, ap);
	if (m < 0)
		m = 0;
	if ((size_t)(n + m) > sizeof buf - 2) {
		/* ⚠ Truncated: it is DECLARED, or a cut line looks like a short line. */
		n = (int)(sizeof buf - 4);
		buf[n++] = '.'; buf[n++] = '.'; buf[n++] = '.';
	} else {
		n += m;
	}
	/* ⛔ NO CONTROL BYTE IN THE BODY — 15 Oct 2026, holistic review.  A
	 *    newline inside a value (a request target, a user name, a peer's
	 *    text) would write a SECOND line that looks like ours: whoever sends
	 *    `/\n14:00:00.000 rcp [owner] ⭐ ADMITTED …` forges server.log without
	 *    a password.  Every byte below 0x20 of the body becomes `?`, for
	 *    every caller; UTF-8 (≥ 0x80) is untouched.  The one newline is the
	 *    one below. */
	/* ⛔ … and DEL, the C1 controls (U+0080–U+009F, written as UTF-8 or as
	 *    lone raw bytes 0x80–0x9F: some terminals obey them), the bidi
	 *    controls (U+202A–U+202E, U+2066–U+2069, and the marks U+200E,
	 *    U+200F, U+061C: they reorder what a reader sees), the Unicode line
	 *    and paragraph separators (U+2028, U+2029: some viewers break the
	 *    line there) and the invisible ones (U+2060–U+2064, U+FEFF) — each
	 *    one `?` (reviews of 95ed70ea, 38639d7d and fc76de93).  Valid UTF-8
	 *    otherwise passes untouched; the line can only get shorter. */
	{
		int w = body;
		for (int k = body; k < n;) {
			unsigned char b0 = (unsigned char)buf[k];
			int len = b0 < 0x80 ? 1 : b0 >= 0xC2 && b0 <= 0xDF ? 2
			        : b0 >= 0xE0 && b0 <= 0xEF ? 3 : b0 >= 0xF0 && b0 <= 0xF4 ? 4 : 0;
			uint32_t cp = len == 1 ? b0 : len == 2 ? b0 & 0x1Fu : len == 3 ? b0 & 0x0Fu
			            : b0 & 0x07u;
			bool valid = len > 0 && k + len <= n;
			for (int j = 1; valid && j < len; j++) {
				unsigned char bj = (unsigned char)buf[k + j];
				if ((bj & 0xC0) != 0x80)
					valid = false;
				else
					cp = (cp << 6) | (bj & 0x3Fu);
			}
			if (!valid) {
				/* a byte outside a valid sequence: a lone C1 is `?`, any
				 * other is copied as it came (as before) */
				buf[w++] = b0 >= 0x80 && b0 <= 0x9F ? '?' : (char)b0;
				k++;
				continue;
			}
			if (cp < 0x20 || cp == 0x7F || (cp >= 0x80 && cp <= 0x9F) || cp == 0x061C ||
			    cp == 0x200E || cp == 0x200F || (cp >= 0x2028 && cp <= 0x202E) ||
			    (cp >= 0x2060 && cp <= 0x2064) || (cp >= 0x2066 && cp <= 0x2069) ||
			    cp == 0xFEFF) {
				buf[w++] = '?';
			} else {
				memmove(buf + w, buf + k, (size_t)len);
				w += len;
			}
			k += len;
		}
		n = w;
	}
	buf[n++] = '\n';

	/* ⭐ With `--journal` the EVENTS (§12) go to the native journal socket
	 *    with their fields (`REMOTIX_AREA`, `REMOTIX_TENANT`, `PRIORITY`).
	 *    If `stderr` is itself connected to systemd's journal stream
	 *    (`remotix.service`), a line already delivered to the socket is NOT
	 *    written to `stderr` a second time; if `stderr` is a file or terminal
	 *    (or if `sendmsg` failed, or the line is chatter), `write(2)` runs.
	 * ⭐ The severity is given by the mark at the HEAD of the body, which is
	 *    the convention of the whole code: ⛔ is a fault, ⚠ a fallback or a
	 *    warning.  ⚠ At the head and not «anywhere»: many normal lines quote
	 *    a ⛔ halfway through («ban: … ⛔ …»), and they would all be errors.
	 * ⛔ The CHATTER lines do not go there (phase 16, coordinator): with 16
	 *    sessions they are tens of thousands per minute, the box's journal
	 *    would throttle them with its rate limit — losing precisely the
	 *    events — and its work would end up inside the load measurements.
	 *    The journal keeps the EVENTS (§12); the detail stays in the file. */
	bool sent = false;
	if (journal_fd >= 0 && !detail) {
		const char *c = buf + body;
		while (*c == ' ')
			c++;
		int prio = strncmp(c, "⛔", strlen("⛔")) == 0 ? 3
		         : strncmp(c, "⚠", strlen("⚠")) == 0 ? 4 : 6;
		sent = al_journal(file, text_line, area, con_id ? safe_id : NULL, prio,
		                  buf + without_time, (size_t)(n - 1 - without_time));
	}

	/* ⛔ Without this immediate write the log is a hope about the moment
	 *    someone will see it: `LESSONS.md` §1.9, seventh guise — stdout
	 *    buffered to a file has already made the right code be accused.
	 *    ⭐ With `write(2)` the problem does not arise: there is no buffer to
	 *    flush, and the earlier `fflush` is no longer needed. */
	if (sent && stderr_in_journal) {
		/* ⭐ Lines `stderr` dropped earlier are told here, natively, when
		 *    `stderr` is not going to be written. */
		unsigned long long d = err_take_dropped();

		if (d) {
			char notice[256];
			int k = dropped_notice(notice, sizeof notice, d, false);

			if (k <= 0 || (size_t)k >= sizeof notice ||
			    !al_journal(__FILE__, __LINE__, "log", NULL, 4, notice, (size_t)k))
				err_give_back(d);
		}
		return; /* already in the journal, with its fields: once is enough */
	}

	/* ⛔ Never waiting — the box is above `err_write()`. */
	err_write(buf, (size_t)n);
}

void log_says_in(const char *file, int text_line, const char *area,
                      const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	line(file, text_line, false, area, NULL, fmt, ap);
	va_end(ap);
}

void log_detail_in(const char *file, int text_line, const char *area,
                           const char *fmt, ...)
{
	va_list ap;
	if (!verbose)
		return;
	va_start(ap, fmt);
	line(file, text_line, true, area, NULL, fmt, ap);
	va_end(ap);
}

void log_says_of_in(const char *file, int text_line, const char *area,
                         const char *chi, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	line(file, text_line, false, area, chi, fmt, ap);
	va_end(ap);
}

void log_detail_of_in(const char *file, int text_line, const char *area,
                              const char *chi, const char *fmt, ...)
{
	va_list ap;
	if (!verbose)
		return;
	va_start(ap, fmt);
	line(file, text_line, true, area, chi, fmt, ap);
	va_end(ap);
}
