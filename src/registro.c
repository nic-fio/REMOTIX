/*
 * registro.c — see registro.h.
 */
#include "registro.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/uio.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

static bool parlantina;

/* ⭐ The journal (box in `registro.h`): -1 = off.  ⚠ It is opened ONCE, at
 *    switch-on and not at the first line: `riga()` runs in several threads,
 *    and two threads opening together would leave an orphan descriptor. */
static int journal_fd = -1;

/* ⭐ The identity of this process — the box is in `registro.h`.  ⚠ A COPY and
 *    not a pointer: whoever sets it often passes an `argv`, and a pointer to
 *    someone else's memory is a log that lies the day that memory changes. */
static char identita[REG_IDENTITA_MAX + 1];

void registro_parlantina(bool acceso) { parlantina = acceso; }
bool registro_parla_molto(void) { return parlantina; }

void registro_identita(const char *chi)
{
	if (!chi || !*chi) {
		identita[0] = '\0';
		return;
	}
	snprintf(identita, sizeof identita, "%s", chi);
}

bool registro_journal(bool acceso)
{
	if (!acceso) {
		if (journal_fd >= 0)
			close(journal_fd);
		journal_fd = -1;
		return true;
	}
	if (journal_fd >= 0)
		return true;
	/* ⛔ NON-BLOCKING: a clogged journal must not stop the loop that serves
	 *    the screen — the line on `stderr` is there anyway.  ⚠ And CLOEXEC:
	 *    the child is born with `execve` and opens its own (`--journal`). */
	journal_fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
	return journal_fd >= 0;
}

bool registro_nel_journal(void) { return journal_fd >= 0; }

bool registro_tasto_dicibile(unsigned c)
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
static void al_journal(const char *file, int linea, const char *area,
                       const char *chi, int priorita, const char *msg,
                       size_t msg_n)
{
	static const struct sockaddr_un dove = {
		.sun_family = AF_UNIX,
		.sun_path = "/run/systemd/journal/socket",
	};
	char campi[384];
	uint8_t lung[8];
	int n = snprintf(campi, sizeof campi,
	                 "PRIORITY=%d\nSYSLOG_IDENTIFIER=remotix\n"
	                 "REMOTIX_AREA=%s\n%s%s%sCODE_FILE=%s\nCODE_LINE=%d\n"
	                 "MESSAGE\n",
	                 priorita, area, chi ? "REMOTIX_INQUILINO=" : "",
	                 chi ? chi : "", chi ? "\n" : "", file ? file : "?", linea);
	if (n < 0 || (size_t)n >= sizeof campi)
		return;
	for (int i = 0; i < 8; i++)
		lung[i] = (uint8_t)((uint64_t)msg_n >> (8 * i));
	struct iovec iov[4] = {
		{campi, (size_t)n},
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
	(void)r; /* ⚠ silent: the channel that remains is `stderr`, and the line is there */
}

uint64_t registro_ora_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000u + (uint64_t)(ts.tv_nsec / 1000000);
}

static void riga(const char *file, int linea, bool dettaglio, const char *area,
                 const char *chi, const char *fmt, va_list ap)
{
	struct timespec ts;
	struct tm tm;
	char quando[32];
	/* ⛔ 4096 is `PIPE_BUF`, the boundary below which an append `write` does
	 *    not interleave with those of other processes. */
	char buf[4096];

	clock_gettime(CLOCK_REALTIME, &ts);
	localtime_r(&ts.tv_sec, &tm);
	strftime(quando, sizeof quando, "%H:%M:%S", &tm);

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
	 *    diagnostic tool of this project (`LEZIONI.md` §2.7): if it lies under
	 *    load, it lies precisely when it is needed.
	 *
	 * ⭐ Direct `write(2)` instead of `stdio`: a line below `PIPE_BUF` (4096
	 *    on Linux) written with a single `write` on a file opened in append is
	 *    atomic with respect to the others.  ⚠ Whatever exceeds the buffer is
	 *    TRUNCATED with a mark, instead of going out interleaved: a cut line
	 *    can be seen, an interleaved line cannot.
	 * ⭐ And on top of that it is async-signal-safe, which `fprintf` is not. */
	/* ⭐⭐ AND IN HERE IT IS SAID WHOSE LINE IT IS — 25 Aug 2026, R10-A4.
	 *
	 *     The identity of the single line beats that of the process: in the
	 *     parent a single process serves all the sessions, and the second
	 *     does not exist.
	 *     ⛔ But the bracket is composed ONLY here: the box in `registro.h`
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
	const char *id = (chi && *chi) ? chi : identita;
	char idsano[REG_IDENTITA_MAX + 1];
	int n;
	/* ⭐ For the journal: where the line without the time begins (the MESSAGE)
	 *    and where the body begins (from which the severity is read). */
	int senza_ora, corpo;
	bool con_id = false;
	if (id && *id) {
		con_id = true;
		/* ⛔ IT IS CLEANED, and it is not distrust of PAM: a `]` or a newline
		 *    inside the identifier would split the line in two, and a split
		 *    line is **plausible and false** — the defect that the cure of
		 *    21 Aug (one single `write` per line) has just finished
		 *    removing.  ⚠ Only what fits in a user name is kept. */
		size_t k = 0;
		for (const char *p = id; *p && k < REG_IDENTITA_MAX; p++, k++) {
			unsigned char c = (unsigned char)*p;
			bool buono = (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z')
			             || (c >= 'a' && c <= 'z') || c == '.' || c == '_'
			             || c == '-' || c == '@' || c == ':';
			idsano[k] = buono ? (char)c : '_';
		}
		idsano[k] = '\0';
		n = snprintf(buf, sizeof buf, "%s.%03ld %-7s [%s] ", quando,
		             ts.tv_nsec / 1000000, area, idsano);
	} else
		n = snprintf(buf, sizeof buf, "%s.%03ld %-7s ", quando,
		             ts.tv_nsec / 1000000, area);
	if (n < 0)
		return;
	if ((size_t)n > sizeof buf - 2)
		n = (int)(sizeof buf - 2);
	senza_ora = (int)strlen(quando) + 5; /* «HH:MM:SS» + «.mmm » */
	if (senza_ora > n)
		senza_ora = n;
	corpo = n;
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
	buf[n++] = '\n';

	/* ⛔ Without this immediate write the log is a hope about the moment
	 *    someone will see it: `LEZIONI.md` §1.9, seventh guise — stdout
	 *    buffered to a file has already made the right code be accused.
	 *    ⭐ With `write(2)` the problem does not arise: there is no buffer to
	 *    flush, and the earlier `fflush` is no longer needed. */
	ssize_t scritti = write(STDERR_FILENO, buf, (size_t)n);
	(void)scritti; /* ⚠ there is nowhere to report that the log cannot be
	                *    written: the only channel would be the broken one. */

	/* ⭐ And the journal, AFTER `stderr` and only if on: without `--journal`
	 *    we never get here, and the line above is all that happens.
	 * ⭐ The severity is given by the mark at the HEAD of the body, which is
	 *    the convention of the whole code: ⛔ is a fault, ⚠ a fallback or a
	 *    warning.  ⚠ At the head and not «anywhere»: many normal lines quote
	 *    a ⛔ halfway through («ban: … ⛔ …»), and they would all be errors.
	 * ⛔ The CHATTER lines do not go there (phase 16, coordinator): with 16
	 *    sessions they are tens of thousands per minute, the box's journal
	 *    would throttle them with its rate limit — losing precisely the
	 *    events — and its work would end up inside the load measurements.
	 *    The journal keeps the EVENTS (§12); the detail stays in the file. */
	if (journal_fd >= 0 && !dettaglio) {
		const char *c = buf + corpo;
		while (*c == ' ')
			c++;
		int prio = strncmp(c, "⛔", strlen("⛔")) == 0 ? 3
		         : strncmp(c, "⚠", strlen("⚠")) == 0 ? 4 : 6;
		al_journal(file, linea, area, con_id ? idsano : NULL, prio,
		           buf + senza_ora, (size_t)(n - 1 - senza_ora));
	}
}

void registro_dice_in(const char *file, int linea, const char *area,
                      const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	riga(file, linea, false, area, NULL, fmt, ap);
	va_end(ap);
}

void registro_dettaglio_in(const char *file, int linea, const char *area,
                           const char *fmt, ...)
{
	va_list ap;
	if (!parlantina)
		return;
	va_start(ap, fmt);
	riga(file, linea, true, area, NULL, fmt, ap);
	va_end(ap);
}

void registro_dice_di_in(const char *file, int linea, const char *area,
                         const char *chi, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	riga(file, linea, false, area, chi, fmt, ap);
	va_end(ap);
}

void registro_dettaglio_di_in(const char *file, int linea, const char *area,
                              const char *chi, const char *fmt, ...)
{
	va_list ap;
	if (!parlantina)
		return;
	va_start(ap, fmt);
	riga(file, linea, true, area, chi, fmt, ap);
	va_end(ap);
}
