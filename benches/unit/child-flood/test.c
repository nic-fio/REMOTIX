/*
 * test.c — unit test of the FLOODING-CHILD defences of src/child.c (88b08213 / c41ed2c8, 15 Oct 2026):
 * the per-round budget of children_move() (ROUND_MSGS_MAX messages or ROUND_NS_MAX of time per child), the log of
 * refused messages (REFUSED_LOG_BURST per REFUSED_LOG_WINDOW_MS, the rest counted, one summary line), the streak
 * (REFUSED_STREAK_MAX refused in a row: SIGKILL and farewell) and the name checked on the RECHECK_MS timer instead
 * of per message (name_still_ours(), and since the candidate `nss-fuori` answered by the CHILD).  These are the sections 6-11 of the abandoned attempt's
 * benches/02-child-strings-test.c (sections 1-5 of that file are not in this tree).
 *
 * HOW: the REAL src/child.c is #included (never modified), like benches/unit/child-credentials/test.c; the log is
 * benches/fuzz/child-msg/stubs_log.c, but child.c's own calls to the log, recvmsg, kill, getpwnam_r and clock_gettime
 * are interposed by macros defined after the system headers.  A real SOCK_SEQPACKET pair with SO_PASSCRED: this
 * process is the "child" (the kernel stamps its pid/uid/gid), the messages go through the real children_move().
 *
 *   6. 1000 refused messages are read in rounds of at most 32, poll (level-triggered) says readable again at once
 *      while some are queued, only the first 5 lines are written, the child is not sent away;
 *   7. once the 10 s window has passed, ONE line counts the other 1095;
 *   8. an honest message afterwards still arrives (the canvas hook), and the streak starts again;
 *   9. 4000 refused, an honest one, 4000 refused: still there; 96 more, 4096 in a row: SIGKILL and farewell;
 *  10. a round is bounded in TIME as well: with a clock that runs 1 ms per look, a round reads 2 messages, not 32;
 *  11. the NAME is not looked up by the parent's loop at all: none for 40 honest messages, none from children_recheck()
 *      (which only sends the «who are you» question); the CHILD's answer (body_whoami.name_check) decides: a name that
 *      holds is left alone, a name given to another uid costs the child (SIGKILL and farewell), «gone» does NOT (the child
 *      asks NSS as an ordinary user: one line in the log, at most every NAME_GONE_LOG_MS, and the login check decides), a child
 *      not yet introduced is never judged, an answer of the old size (no name_check) is accepted; name_resolution() gives the
 *      three verdicts; a LOGIN through children_ensure_from() does one lookup and passes, or kills on another uid or a
 *      vanished name.
 *  12. (audit of the session, 25 Oct 2026) the «who are you» question that nobody answers: a child that never answers is killed 180 s after the
 *      question (not before, and not if no question was asked yet); one that answers every minute is never touched; one that does not answer but
 *      keeps sending messages is NOT killed (a line says so, the wait starts again); the wait is armed even when the question cannot go out.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=2 --memory=2g -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src -I/albero/benches/fuzz/child-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/child-flood/test.c -o t.o && clang $F -c /albero/benches/fuzz/child-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && ./test'
 * Exit code 0 = every check passed, 1 = a check failed, 3 = not all checks ran.
 */
#define _GNU_SOURCE
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "log.h"

static void rxt_log_says_in(const char *file, int text_line, const char *area,
                            const char *fmt, ...);
static ssize_t rxt_recvmsg(int fd, struct msghdr *m, int flags);
static int rxt_kill(pid_t pid, int sig);
static int rxt_getpwnam_r(const char *name, struct passwd *pw, char *buf, size_t n,
                          struct passwd **result);
static int rxt_clock_gettime(clockid_t c, struct timespec *ts);
#define log_says_in rxt_log_says_in
#define recvmsg rxt_recvmsg
#define kill rxt_kill
#define getpwnam_r rxt_getpwnam_r
#define clock_gettime rxt_clock_gettime
#include "child.c"
#undef clock_gettime
#undef getpwnam_r
#undef kill
#undef recvmsg
#undef log_says_in

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 49

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

/* the last line child.c wrote, and how many */
static char last[8192];
static int lines;

static void rxt_log_says_in(const char *file, int text_line, const char *area,
                            const char *fmt, ...)
{
	va_list ap;
	(void)file;
	(void)text_line;
	(void)area;
	va_start(ap, fmt);
	vsnprintf(last, sizeof last, fmt, ap);
	va_end(ap);
	lines++;
}

/* the messages child.c read (each recvmsg that returned one) */
static int reads;

static ssize_t rxt_recvmsg(int fd, struct msghdr *m, int flags)
{
	ssize_t r = recvmsg(fd, m, flags);
	if (r > 0)
		reads++;
	return r;
}

/* the signals child.c sent: nobody receives them, they are counted */
static int kills, sigkills;
static pid_t last_kill_pid;

static int rxt_kill(pid_t pid, int sig)
{
	kills++;
	last_kill_pid = pid;
	if (sig == SIGKILL)
		sigkills++;
	return 0;
}

/* a fake passwd with one name: what it resolves to, and how many lookups */
static int lookups;
static uid_t nss_uid;
static bool nss_gone;
static struct passwd nss_pw;

static int rxt_getpwnam_r(const char *name, struct passwd *pw, char *buf, size_t n,
                          struct passwd **result)
{
	(void)buf;
	(void)n;
	lookups++;
	*result = NULL;
	if (nss_gone)
		return 0;
	memset(&nss_pw, 0, sizeof nss_pw);
	nss_pw.pw_name = (char *)name;
	nss_pw.pw_uid = nss_uid;
	nss_pw.pw_gid = getgid();
	*pw = nss_pw;
	*result = pw;
	return 0;
}

/* a clock that runs 1 ms at every look, when asked to */
static bool slow_clock;
static uint64_t slow_ns;

static int rxt_clock_gettime(clockid_t c, struct timespec *ts)
{
	if (!slow_clock)
		return clock_gettime(c, ts);
	slow_ns += 1000000;
	ts->tv_sec = (time_t)(slow_ns / 1000000000ull);
	ts->tv_nsec = (long)(slow_ns % 1000000000ull);
	return 0;
}

/* the canvas hook: an honest message reached it */
static int canvases;
static uint32_t canvas_seen_w;

static void on_canvas(void *ctx, const char *user, uid_t uid, uint32_t iw, uint32_t ih,
                      uint32_t gw, uint32_t gh)
{
	(void)ctx;
	(void)user;
	(void)uid;
	(void)ih;
	(void)gw;
	(void)gh;
	canvases++;
	canvas_seen_w = iw;
}

/* ── a live child: this process at the other end of a real SEQPACKET pair ── */
static int peer = -1;

static bool live_child(struct children *f, struct child *g)
{
	int sv[2], one = 1;

	memset(f, 0, sizeof *f);
	memset(g, 0, sizeof *g);
	if (peer >= 0)
		close(peer);
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0
	    || setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &one, sizeof one) != 0) {
		perror("socketpair/SO_PASSCRED");
		return false;
	}
	fcntl(sv[0], F_SETFL, O_NONBLOCK);
	fcntl(sv[1], F_SETFL, O_NONBLOCK);
	peer = sv[1];
	f->cap = 1;
	f->v = g;
	f->canvas = on_canvas;
	g->used = true;
	snprintf(g->user, sizeof g->user, "anna");
	g->uid = getuid();
	g->gid = getgid();
	g->pid = getpid();
	g->fd = sv[0];
	g->serial = 7;
	g->showed_up = true;
	g->born_ms = g->last_recheck_ms = 1000000;
	nss_uid = getuid();
	nss_gone = false;
	return true;
}

/* a refused message: odd ones without the signature, even ones of a type nobody knows */
/* the child's answer to the parent's question: MSG_INTRO with the result of ITS lookup of its own name */
static bool send_intro(const struct child *g, uint32_t name_check, uint32_t name_uid, size_t body_size)
{
	struct {
		struct head t;
		struct body_whoami b;
	} m;

	memset(&m, 0, sizeof m);
	magic_write(&m.t);
	m.t.kind = MSG_INTRO;
	m.t.version = CHILD_VERSION;
	m.t.serial = g->serial;
	m.t.declared_uid = (uint32_t)g->uid;
	m.t.byte = (uint32_t)body_size;
	m.b.uid = m.b.euid = m.b.suid = (uint32_t)g->uid;
	m.b.gid = m.b.egid = m.b.sgid = (uint32_t)g->gid;
	m.b.pid = (uint32_t)getpid();
	m.b.ppid = (uint32_t)getppid();
	snprintf(m.b.user, sizeof m.b.user, "%s", g->user);
	snprintf(m.b.runtime, sizeof m.b.runtime, "/run/user/%u", (unsigned)g->uid);
	m.b.name_check = name_check;
	m.b.name_uid = name_uid;
	return send(peer, &m, sizeof m.t + body_size, MSG_NOSIGNAL) == (ssize_t)(sizeof m.t + body_size);
}

static bool send_refused(const struct child *g, int k)
{
	uint8_t m[40];
	memset(m, 'x', sizeof m);
	if (k % 2 == 0) {
		struct head t;
		memset(&t, 0, sizeof t);
		magic_write(&t);
		t.kind = 0xFFFF;
		t.version = CHILD_VERSION;
		t.serial = g->serial;
		t.declared_uid = (uint32_t)g->uid;
		t.byte = sizeof m - sizeof t;
		memcpy(m, &t, sizeof t);
	}
	return send(peer, m, sizeof m, MSG_NOSIGNAL) == (ssize_t)sizeof m;
}

static bool send_canvas(const struct child *g, uint32_t w)
{
	struct {
		struct head t;
		struct body_canvas c;
	} m;
	memset(&m, 0, sizeof m);
	magic_write(&m.t);
	m.t.kind = MSG_CANVAS;
	m.t.version = CHILD_VERSION;
	m.t.serial = g->serial;
	m.t.declared_uid = (uint32_t)g->uid;
	m.t.byte = sizeof m.c;
	m.c.intended_w = m.c.got_w = w;
	m.c.intended_h = m.c.got_h = 1080;
	return send(peer, &m, sizeof m, MSG_NOSIGNAL) == (ssize_t)sizeof m;
}

/* as main.c's loop does it: poll, then children_move; returns the messages read */
static int one_round(struct children *f, uint64_t now_ms)
{
	struct pollfd p[1];
	size_t n = children_descriptors(f, p, 1);
	if (n && poll(p, n, 0) < 0)
		return -1;
	reads = 0;
	children_move(f, p, n, now_ms);
	return reads;
}

/* is the parent's end readable right now (`poll`, no wait)? */
static bool readable_now(const struct child *g)
{
	struct pollfd p = {g->fd, POLLIN, 0};
	return g->fd >= 0 && poll(&p, 1, 0) == 1 && (p.revents & POLLIN);
}

/* sends `total` refused messages, reading rounds whenever the socket is full and
 * at the end until it is empty; the largest round and the count of rounds */
struct flood {
	int max_round, rounds, sent;
	bool readable_after_capped; /* a round of 32 with messages still queued: poll said so */
	bool capped_seen;
};

static void drain_rounds(struct children *f, struct child *g, uint64_t now, struct flood *r)
{
	while (g->used && !g->exiting && readable_now(g)) {
		int k = one_round(f, now);
		r->rounds++;
		if (k > r->max_round)
			r->max_round = k;
		if (k == ROUND_MSGS_MAX && !r->capped_seen) {
			struct pollfd p = {g->fd, POLLIN, 0};
			int q = 0;
			r->capped_seen = true;
			ioctl(g->fd, FIONREAD, &q);
			/* ⚠ only meaningful while something is queued */
			r->readable_after_capped = q == 0 || (poll(&p, 1, 0) == 1 && (p.revents & POLLIN));
		}
		if (k <= 0)
			break;
	}
}

static void flood(struct children *f, struct child *g, int total, int first_k, uint64_t now,
                  struct flood *r)
{
	memset(r, 0, sizeof *r);
	for (int k = 0; k < total && g->used && !g->exiting;) {
		if (send_refused(g, first_k + k)) {
			k++;
			r->sent++;
		} else
			drain_rounds(f, g, now, r);
	}
	drain_rounds(f, g, now, r);
}

int main(void)
{
	struct children f;
	struct child g;

	setvbuf(stdout, NULL, _IONBF, 0);

	/* ⚠ the rounds' instants on child.c's own clock (log_now_ms(), which also stamps a
	 *   farewell): no «3 s since the farewell» SIGKILL of its own in the middle */
	const uint64_t base = log_now_ms();

	printf("  6. a child sends 1000 refused messages\n");
	{
		struct flood r;
		uint64_t now = base;

		if (!live_child(&f, &g))
			return 1;
		/* ⚠ more than one round's worth queued before the first round */
		for (int k = 0; k < 100; k++)
			if (!send_refused(&g, k))
				break;
		{
			int k = one_round(&f, now);
			require(k == ROUND_MSGS_MAX && readable_now(&g),
			        "the first round reads 32, and poll says readable again at once");
		}
		while (readable_now(&g))
			one_round(&f, now);
		lines = 0;
		kills = sigkills = 0;
		flood(&f, &g, 1000, 100, now, &r);
		printf("       %d sent, %d rounds, the largest %d messages\n", r.sent, r.rounds,
		       r.max_round);
		require(r.sent == 1000 && r.max_round <= ROUND_MSGS_MAX && r.rounds >= 1000 / ROUND_MSGS_MAX,
		        "read in rounds of at most 32 (at least 31 rounds)");
		require(!r.capped_seen || r.readable_after_capped,
		        "after a full round with messages queued, poll is readable at once");
		require(lines == 0, "the 5 lines of this window were spent by the first 100: none more");
		require(g.refused_hidden == 1100 - REFUSED_LOG_BURST,
		        "the other 1095 are counted, not written");
		require(g.used && !g.exiting && kills == 0, "the child is not sent away for 1100");
	}

	printf("  7. the 10 s window passes\n");
	{
		lines = 0;
		one_round(&f, base + REFUSED_LOG_WINDOW_MS);
		require(lines == 1 && strstr(last, "1095 more refused messages") != NULL,
		        "ONE line counts them");
		require(g.refused_hidden == 0, "and the count starts again");
	}

	printf("  8. an honest message after the flood\n");
	{
		canvases = 0;
		require(send_canvas(&g, 1234), "sent");
		one_round(&f, base + REFUSED_LOG_WINDOW_MS);
		require(canvases == 1 && canvas_seen_w == 1234, "it arrives (the canvas hook, its numbers)");
		require(g.refused_streak == 0, "and the streak of refusals starts again");
	}

	printf("  9. refused in a row: the streak\n");
	{
		struct flood r;
		uint64_t now = base;

		if (!live_child(&f, &g))
			return 1;
		kills = sigkills = 0;
		canvases = 0;
		flood(&f, &g, 4000, 0, now, &r);
		require(send_canvas(&g, 77), "an honest one in the middle");
		while (readable_now(&g))
			one_round(&f, now);
		flood(&f, &g, 4000, 0, now, &r);
		require(canvases == 1 && g.used && !g.exiting && sigkills == 0,
		        "4000, an honest one, 4000: the child stays");
		flood(&f, &g, 200, 0, now, &r);
		require(sigkills == 1 && last_kill_pid == getpid() && g.exiting,
		        "4096 in a row: SIGKILL and farewell");
		require(g.refused_streak == REFUSED_STREAK_MAX, "at exactly the 4096th");
	}

	printf("  10. a round is bounded in time too\n");
	{
		if (!live_child(&f, &g))
			return 1;
		for (int k = 0; k < 64; k++)
			send_refused(&g, k);
		slow_clock = true;
		slow_ns = 0;
		int k = one_round(&f, base);
		slow_clock = false;
		require(k == 2, "1 ms per look, 2 ms per round: 2 messages, not 32");
		require(readable_now(&g), "the rest stays queued, and poll says so");
	}

	printf("  11. the name: never looked up by the parent's loop; the child's answer decides\n");
	{
		uint64_t now = base;
		uid_t other = 0;
		char why[256];

		if (!live_child(&f, &g))
			return 1;
		g.last_recheck_ms = now;
		lookups = 0;
		canvases = 0;
		for (int k = 0; k < 40; k++)
			send_canvas(&g, 100 + (uint32_t)k);
		while (readable_now(&g))
			one_round(&f, now);
		require(canvases == 40 && lookups == 0, "40 honest messages, 0 lookups of the name");
		kills = sigkills = 0;
		nss_uid = getuid() + 1; /* NSS has given the name to another uid: the PARENT must not notice by itself */
		children_recheck(&f, now + RECHECK_MS - 1);
		children_recheck(&f, now + RECHECK_MS);
		children_recheck(&f, now + 3 * RECHECK_MS);
		require(lookups == 0 && sigkills == 0 && g.used && !g.exiting,
		        "children_recheck() asks the child and looks nothing up: 0 lookups, nobody killed");
		nss_uid = getuid();

		require(send_intro(&g, NAME_HOLDS, 0, sizeof(struct body_whoami)), "the child answers: its name holds");
		one_round(&f, now + RECHECK_MS);
		require(sigkills == 0 && g.used && !g.exiting && lookups == 0, "a name that holds: left alone, still no lookup");

		require(send_intro(&g, NAME_NOT_ASKED, 0, WHOAMI_MIN), "an answer of the OLD size (no name_check)");
		one_round(&f, now + RECHECK_MS + 1);
		require(sigkills == 0 && g.used && !g.exiting, "is accepted as «not asked»: the child stays");

		require(send_intro(&g, NAME_OTHER_UID, (uint32_t)getuid() + 1, sizeof(struct body_whoami)),
		        "the child answers: NSS gave its name to another uid");
		one_round(&f, now + RECHECK_MS + 2);
		/* >= 1: children_move() may add its own fallback SIGKILL for a slot already dismissed (the test clock is not the real one) */
		require(sigkills >= 1 && g.exiting && lookups == 0, "SIGKILL and farewell, and the parent looked nothing up");

		if (!live_child(&f, &g))
			return 1;
		kills = sigkills = 0;
		require(send_intro(&g, NAME_GONE, 0, sizeof(struct body_whoami)), "the child answers: its name does not resolve");
		one_round(&f, now);
		require(sigkills == 0 && g.used && !g.exiting && g.name_gone_logged_ms != 0,
		        "«gone» is NOT acted on (the child asks NSS as an ordinary user): the child stays, one line is logged");
		{
			uint64_t first = g.name_gone_logged_ms;

			send_intro(&g, NAME_GONE, 0, sizeof(struct body_whoami));
			one_round(&f, now);
			require(sigkills == 0 && g.name_gone_logged_ms == first, "and a second «gone» in the window is not logged again");
		}

		if (!live_child(&f, &g))
			return 1;
		g.showed_up = false;
		kills = sigkills = 0;
		send_intro(&g, NAME_GONE, 0, sizeof(struct body_whoami));
		one_round(&f, now);
		require(sigkills == 0 && g.used && !g.exiting && g.showed_up && g.name_gone_logged_ms == 0,
		        "a child not yet introduced that says «gone» is ignored (introduced now, nothing logged)");
		g.showed_up = false;
		send_intro(&g, NAME_OTHER_UID, (uint32_t)getuid() + 1, sizeof(struct body_whoami));
		one_round(&f, now);
		require(sigkills == 0 && g.used && !g.exiting, "...and its birth message is never judged, whatever it says");

		/* a LOGIN under the name: the parent's own check, through children_ensure_from() */
		if (!live_child(&f, &g))
			return 1;
		lookups = 0;
		require(children_ensure_from(&f, "anna", "127.0.0.1") == CHILD_READY && lookups == 1 && g.used && !g.exiting,
		        "a login under a name that holds: the child is found, ONE lookup");
		nss_uid = getuid() + 1;
		kills = sigkills = 0;
		require(children_ensure_from(&f, "anna", "127.0.0.1") == CHILD_NAME_MOVED && sigkills >= 1 && g.exiting,
		        "a login under a name now given to another uid: NAME_MOVED, the child is killed");
		if (!live_child(&f, &g))
			return 1;
		nss_gone = true;
		kills = sigkills = 0;
		require(children_ensure_from(&f, "anna", "127.0.0.1") == CHILD_NAME_MOVED && sigkills >= 1 && g.exiting,
		        "a login under a name that no longer resolves: the same (the decision «gone» was left to this check)");

		/* the lookup itself, and the parent's check at a LOGIN */
		if (!live_child(&f, &g))
			return 1;
		lookups = 0;
		require(name_resolution("anna", getuid(), &other) == NAME_HOLDS && lookups == 1, "name_resolution: it holds");
		nss_uid = getuid() + 1;
		require(name_resolution("anna", getuid(), &other) == NAME_OTHER_UID && other == getuid() + 1,
		        "name_resolution: another uid, and which one");
		nss_gone = true;
		require(name_resolution("anna", getuid(), &other) == NAME_GONE, "name_resolution: gone");
		lookups = 0;
		why[0] = 0;
		require(!name_still_ours(&g, why, sizeof why) && lookups == 1 && strstr(why, "no longer resolves") != NULL,
		        "name_still_ours() (the login check): one lookup, the same words as before");
		nss_gone = false;
		nss_uid = getuid() + 1;
		why[0] = 0;
		require(!name_still_ours(&g, why, sizeof why) && strstr(why, "now uid") != NULL, "...and for another uid");
		nss_uid = getuid();
		require(name_still_ours(&g, why, sizeof why), "...and true when it holds");
	}

	printf("  12. the «who are you» question that nobody answers\n");
	{
		const uint64_t T0 = 1000000;
		struct children f;
		struct child g;

		/* 40: never answered → killed at the deadline after the question, not before; no question yet → no deadline */
		if (!live_child(&f, &g))
			return 1;
		sigkills = 0;
		children_recheck(&f, T0 + 10000);            /* before the first minute: no question, nothing armed */
		children_recheck(&f, T0 + 60000 + WHOAMI_DEADLINE_MS - 1);  /* (first question goes out here; asked_ms = this instant) */
		require(sigkills == 0 && g.used, "40a. before the first question, and at the instant it is asked: nobody is killed");
		{
			uint64_t asked = g.whoami_asked_ms;
			children_recheck(&f, asked + WHOAMI_DEADLINE_MS - 1);
			require(sigkills == 0, "40b. 1 ms before the deadline (600 s): not killed");
			children_recheck(&f, asked + WHOAMI_DEADLINE_MS);
			require(sigkills == 1 && g.exiting, "40c. the deadline after the question and not a word from the child: SIGKILL, the slot is leaving");
		}
		/* 41: it answers every minute → never touched */
		if (!live_child(&f, &g))
			return 1;
		sigkills = 0;
		for (int m = 1; m <= 12; m++) {
			children_recheck(&f, T0 + (uint64_t)m * RECHECK_MS);
			if (!send_intro(&g, NAME_HOLDS, (uint32_t)g.uid, sizeof(struct body_whoami)))
				return 1;
			one_round(&f, T0 + (uint64_t)m * RECHECK_MS + 1);
		}
		children_recheck(&f, T0 + 12 * RECHECK_MS + WHOAMI_DEADLINE_MS * 2);
		require(sigkills == 0 && g.used && !g.exiting && g.whoami_asked_ms != 0, "41. a child that answers every minute is never touched (12 minutes)");
		/* 42: it does not answer but keeps delivering → not killed, a line, the wait restarts */
		if (!live_child(&f, &g))
			return 1;
		sigkills = 0;
		children_recheck(&f, T0 + RECHECK_MS);
		{
			uint64_t asked = g.whoami_asked_ms;
			if (!send_canvas(&g, 1920))
				return 1;
			one_round(&f, asked + 100000);            /* a message arrives after the question */
			lines = 0;
			children_recheck(&f, asked + WHOAMI_DEADLINE_MS);
			require(sigkills == 0 && g.used && !g.exiting && lines >= 1 && strstr(last, "NOT killed") != NULL,
			        "42. it does not answer but sent a message after the question: NOT killed, one line says so");
			require(g.whoami_asked_ms == asked + WHOAMI_DEADLINE_MS, "42b. and the wait starts again from there");
			children_recheck(&f, asked + 2 * WHOAMI_DEADLINE_MS);
			require(sigkills == 1, "42c. if then it says nothing at all for another deadline: SIGKILL");
		}
		/* 44-45 (review of c4cf6db2): NSS is slow. The child sends its LIGHT confirmation at once (name_check NOT_ASKED), the name verdict comes
		 *       much later — the child is NOT killed in between, and the late verdict still counts */
		if (!live_child(&f, &g))
			return 1;
		sigkills = 0;
		children_recheck(&f, T0 + RECHECK_MS);
		if (!send_intro(&g, NAME_NOT_ASKED, 0, sizeof(struct body_whoami)))
			return 1;
		one_round(&f, T0 + RECHECK_MS + 100);
		children_recheck(&f, T0 + RECHECK_MS + WHOAMI_DEADLINE_MS + 5000);
		require(sigkills == 0 && g.used && !g.exiting && g.whoami_asked_ms != 0 && strstr(last, "stuck") == NULL,
		        "44. the light confirmation clears the wait: with the name check stuck in NSS for 10 minutes the child is NOT killed");
		if (!send_intro(&g, NAME_OTHER_UID, (uint32_t)g.uid + 1, sizeof(struct body_whoami)))
			return 1;
		one_round(&f, T0 + RECHECK_MS + WHOAMI_DEADLINE_MS + 6000);
		require(sigkills >= 1 && g.exiting, "45. and when NSS finally answers that the name is another uid's, that late verdict still kills it");
		/* 43: the question cannot go out (the descriptor refuses the send) → the wait is armed all the same */
		if (!live_child(&f, &g))
			return 1;
		{
			int pp[2];
			if (pipe(pp) != 0)
				return 1;
			close(g.fd);
			g.fd = pp[0];                             /* send() on a pipe: ENOTSOCK */
			sigkills = 0;
			children_recheck(&f, T0 + RECHECK_MS);
			children_recheck(&f, T0 + RECHECK_MS + WHOAMI_DEADLINE_MS);
			require(g.whoami_asked_ms == T0 + RECHECK_MS && sigkills == 1, "43. a question that cannot go out arms the wait: SIGKILL after the deadline");
			close(pp[0]);
			close(pp[1]);
			g.fd = -1;
		}
	}

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
