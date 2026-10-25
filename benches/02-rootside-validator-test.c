/* 02-rootside-validator-test.c — the root side's own walls (DECISIONS §11.50):
 * the closed list's validator, the grants, the AUTH bounds, the names refused
 * before PAM.
 *
 * In the build container, from src/ (the product's objects, then the test
 * linked against all of them except main.o and rootside.o), as
 * 02-child-strings-test.c says:
 *
 *   make TWIN=none
 *   gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags gio-2.0 \
 *       libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 \
 *       xkbcommon wayland-client gbm) -o /tmp/rsv \
 *       ../benches/02-rootside-validator-test.c \
 *       $(ls *.o | grep -v -e '^main.o$' -e '^rootside.o$') \
 *       -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
 *       $(pkg-config --libs gio-2.0 libpipewire-0.3 libva libva-drm \
 *       libei-1.0 xkbcommon wayland-client gbm opus vulkan) -ldl && /tmp/rsv
 *
 * ⛔ A hijacked network side is the attacker the root side is built against:
 *    every packet is checked for the kernel's credentials (uid remotix, pid
 *    the network side), the exact length of its kind, a known kind, magic and
 *    version, strings terminated in their arrays; a grant is single use,
 *    30 s, and carries its own user; AUTH has 16 in flight and 10/s burst 20;
 *    uid 0, denied and unknown names never reach PAM.
 *
 * ⚠ `rootside.c` is INCLUDED (its statics too); nothing is forked, no
 *   channel is opened.
 *
 * Exit status: 0 green, 1 red, 3 not all checks ran. */
#define _GNU_SOURCE
#include <errno.h>
#include <pwd.h>
#include <string.h>

/* ⭐ The review of the split (findings 7, 8): NSS faked around the real one —
 *    an alias that resolves to another entry (sssd case-insensitive), and an
 *    ERANGE below a buffer size (an entry that does not fit). */
static int (*real_getpwnam_r)(const char *, struct passwd *, char *, size_t,
                              struct passwd **) = getpwnam_r;
static const char *alias_name, *alias_target;
static size_t erange_below;
static int fake_getpwnam_r(const char *n, struct passwd *pw, char *b, size_t c,
                           struct passwd **r)
{
	if (erange_below && c < erange_below) {
		*r = NULL;
		return ERANGE;
	}
	if (alias_name && strcmp(n, alias_name) == 0)
		n = alias_target;
	return real_getpwnam_r(n, pw, b, c, r);
}
#define getpwnam_r fake_getpwnam_r
/* ⭐ 1.6 (R8): the root side now asks `rediscover_starttime()` / `rediscover_search_files()`; the real ones (their GLib
 * half is never reached here, and is stubbed by the link) so the table can be watched by a real pidfd. */
#include "rediscover.c"
#include "rootside.c"

#include <stdio.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 83

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

static const struct rootside_peer PEER = { 977, 4242 };

static int check(const void *b, size_t n)
{
	char why[200];
	return rootside_check_packet(&PEER, b, n, true, PEER.net_pid, PEER.remotix_uid, why,
	                             sizeof why);
}

static void count_exit(void *c, uint64_t s, int st)
{
	(void)s;
	(void)st;
	(*(int *)c)++;
}

static void count_verdict(void *c, uint64_t r, int o)
{
	(void)r;
	(void)o;
	(*(int *)c)++;
}

static void auth_fill(struct rxr_auth *a)
{
	memset(a, 0, sizeof *a);
	head_fill(&a->h, RXR_AUTH, 7);
	snprintf(a->user, sizeof a->user, "anna");
	snprintf(a->password, sizeof a->password, "secret");
	snprintf(a->rhost, sizeof a->rhost, "192.0.2.1");
}

static void count_exit_gone(void *c, uid_t u, const char *n)
{
	(void)u;
	(void)n;
	(*(int *)c)++;
}

/* ── ⭐ 1.6 (R8): the desktops found again — the three events, their order, and the root side's table ─────────────────────── */

static pid_t sleeper(void)
{
	pid_t p = fork();

	if (p == 0) {
		for (;;)
			pause();
	}
	return p;
}

static void stop_sleeper(pid_t p)
{
	int st;

	kill(p, SIGKILL);
	waitpid(p, &st, 0);
}

static void desktop_of(RediscoveredDesktop *d, pid_t stage, const char *user, uid_t uid)
{
	memset(d, 0, sizeof *d);
	d->stage = stage;
	d->uid = uid;
	d->sessions = 1;
	snprintf(d->user, sizeof d->user, "%s", user);
	snprintf(d->session, sizeof d->session, "c%ld", (long)stage);
	snprintf(d->comm, sizeof d->comm, "stage-%ld", (long)stage);
	(void)rediscover_starttime("/proc", stage, &d->starttime);
}

/* one packet from the root side's end, exactly its size or -1 */
static ssize_t take(int fd, void *buf, size_t cap)
{
	return recv(fd, buf, cap, MSG_DONTWAIT);
}

static int seq(struct rootside_found_seq *q, int kind, uint32_t count, uint8_t outcome)
{
	char w[100];

	return rootside_found_step(q, kind, count, outcome, w, sizeof w);
}

static void found_tests(void)
{
	struct rootside_found_seq q;
	union {
		struct rxr_found_again fa;
		struct rxr_found_end fe;
		struct rxr_found_gone fg;
		char raw[1024];
	} in;
	int sv[2], gone_calls = 0;
	pid_t k1, k2;
	RediscoveredDesktop d[3];

	printf("\n  ⭐ 1.6 (R8): the desktops found again\n");

	/* the sizes are the wire format: a field added by accident changes them */
	require(sizeof(struct rxr_found_again) == 344 && sizeof(struct rxr_found_end) == 24 &&
	        sizeof(struct rxr_found_gone) == 280,
	        "exact sizes on the wire: FOUND_AGAIN 344, FOUND_END 24, FOUND_GONE 280");
	require(RXR_VERSION == 2 && RXR_FOUND_AGAIN == 106 && RXR_FOUND_END == 107 && RXR_FOUND_GONE == 108,
	        "version 2, kinds 106, 107, 108");
	require(size_of_event(RXR_FOUND_AGAIN) == sizeof(struct rxr_found_again) &&
	        size_of_event(RXR_FOUND_END) == sizeof(struct rxr_found_end) &&
	        size_of_event(RXR_FOUND_GONE) == sizeof(struct rxr_found_gone),
	        "the network side's client knows the exact size of each event");
	{
		bool refused = true;
		static const int kinds[3] = { RXR_FOUND_AGAIN, RXR_FOUND_END, RXR_FOUND_GONE };

		for (int i = 0; i < 3; i++) {
			memset(&in, 0, sizeof in);
			head_fill(&in.fa.h, kinds[i], 5);
			/* even with a request number, the right credentials and the event's exact size */
			refused = refused && check(&in, size_of_event(kinds[i])) == 0 && size_of_request(kinds[i]) == 0;
		}
		require(refused, "a FOUND_* sent BY the network side is not in the closed list: the root side refuses it");
	}

	/* the order, pure */
	memset(&q, 0, sizeof q);
	require(seq(&q, RXR_FOUND_AGAIN, 0, 0) == -1, "FOUND_AGAIN before READY: broken");
	memset(&q, 0, sizeof q);
	require(seq(&q, RXR_READY, 0, 0) == 0 && seq(&q, RXR_FOUND_AGAIN, 0, 0) == 0 && seq(&q, RXR_FOUND_AGAIN, 0, 0) == 0 &&
	        seq(&q, RXR_FOUND_END, 2, RXR_FOUND_OK) == 0 && seq(&q, RXR_FOUND_GONE, 0, 0) == 0 &&
	        seq(&q, RXR_FOUND_GONE, 0, 0) == 0,
	        "READY, 2 x FOUND_AGAIN, FOUND_END(2), 2 x FOUND_GONE: in order");
	require(seq(&q, RXR_FOUND_AGAIN, 0, 0) == -1 && seq(&q, RXR_FOUND_END, 2, RXR_FOUND_OK) == -1,
	        "after FOUND_END: a FOUND_AGAIN or a second FOUND_END is broken");
	memset(&q, 0, sizeof q);
	(void)seq(&q, RXR_READY, 0, 0);
	(void)seq(&q, RXR_FOUND_AGAIN, 0, 0);
	require(seq(&q, RXR_FOUND_END, 2, RXR_FOUND_OK) == -1 && seq(&q, RXR_FOUND_END, 0, RXR_FOUND_OK) == -1,
	        "a count that does not add up (too many or too few): broken");
	memset(&q, 0, sizeof q);
	(void)seq(&q, RXR_READY, 0, 0);
	require(seq(&q, RXR_FOUND_GONE, 0, 0) == -1, "FOUND_GONE before FOUND_END: broken");
	(void)seq(&q, RXR_FOUND_AGAIN, 0, 0);
	require(seq(&q, RXR_FOUND_END, 1, RXR_FOUND_UNKNOWN) == -1 && seq(&q, RXR_FOUND_END, 1, 7) == -1,
	        "UNKNOWN with desktops listed, and an outcome that does not exist: broken");
	memset(&q, 0, sizeof q);
	(void)seq(&q, RXR_READY, 0, 0);
	require(seq(&q, RXR_FOUND_END, 0, RXR_FOUND_UNKNOWN) == 0 && seq(&q, RXR_READY, 0, 0) == -1,
	        "UNKNOWN with none is fine; a second READY is broken");
	memset(&q, 0, sizeof q);
	(void)seq(&q, RXR_READY, 0, 0);
	{
		int last = 0;

		for (int i = 0; i < RXR_FOUND_MAX + 1; i++)
			last = seq(&q, RXR_FOUND_AGAIN, 0, 0);
		require(last == -1, "more than RXR_FOUND_MAX FOUND_AGAIN: broken");
	}

	/* the root side's table, on the wire */
	if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) != 0) {
		printf("    ??  no socketpair\n");
		return;
	}
	fcntl(sv[0], F_SETFL, O_NONBLOCK);
	R.chan = sv[0];
	R.found = calloc(RXR_FOUND_MAX, sizeof *R.found);
	R.gone = calloc(RXR_FOUND_MAX, sizeof *R.gone);
	found_clear();
	k1 = sleeper();
	k2 = sleeper();
	desktop_of(&d[0], k1, "anna", 1001);
	desktop_of(&d[1], k2, "bruno", 1002);
	desktop_of(&d[2], 1, "ghost", 1003);
	d[2].starttime += 5; /* the pid exists, but it is another process than the one searched */
	found_install(d, 3, true, "/proc");
	require(R.found_promised == 2, "a stage whose start time differs (a reused pid) is not watched, not announced");
	found_pump();
	{
		bool ok = take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fa && in.fa.h.kind == RXR_FOUND_AGAIN &&
		          in.fa.h.request == 0 && strcmp(in.fa.user, "anna") == 0 && in.fa.uid == 1001 && in.fa.stage == k1;
		ok = ok && take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fa && in.fa.h.kind == RXR_FOUND_AGAIN &&
		     strcmp(in.fa.user, "bruno") == 0;
		require(ok, "two FOUND_AGAIN in order, exact size, request 0, with name, uid and stage");
	}
	require(take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fe && in.fe.h.kind == RXR_FOUND_END && in.fe.count == 2 &&
	        in.fe.outcome == RXR_FOUND_OK,
	        "then FOUND_END(2, OK)");
	require(take(sv[1], &in, sizeof in) < 0, "and nothing else while all stages live");
	stop_sleeper(k1);
	found_check(log_now_ms());
	found_pump();
	require(take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fg && in.fg.h.kind == RXR_FOUND_GONE && in.fg.uid == 1001 &&
	        strcmp(in.fg.user, "anna") == 0,
	        "a stage that dies (pidfd) is announced with FOUND_GONE, after FOUND_END");
	found_check(log_now_ms());
	found_pump();
	require(take(sv[1], &in, sizeof in) < 0, "and only once");

	/* a restart: the whole current table again, in order */
	found_install(d, 2, true, "/proc"); /* k1 is dead now: its start time is gone */
	found_pump();
	require(R.found_promised == 1 && take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fa && strcmp(in.fa.user, "bruno") == 0 &&
	        take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fe && in.fe.count == 1,
	        "a new network side gets the current table again: only the live desktop, FOUND_END(1)");

	/* a stage that dies before it was announced is neither announced nor counted */
	k1 = sleeper();
	desktop_of(&d[0], k1, "carla", 1004);
	found_install(d, 1, true, "/proc");
	stop_sleeper(k1);
	found_check(log_now_ms());
	require(R.found_promised == 0 && R.ngone == 0, "a stage that dies before FOUND_AGAIN left: taken out of the count, no FOUND_GONE");
	found_pump();
	require(take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fe && in.fe.count == 0 && in.fe.outcome == RXR_FOUND_OK &&
	        take(sv[1], &in, sizeof in) < 0,
	        "FOUND_END(0, OK) alone");

	/* the root side could not look */
	found_install(NULL, 0, false, "/proc");
	found_pump();
	require(take(sv[1], &in, sizeof in) == (ssize_t)sizeof in.fe && in.fe.count == 0 && in.fe.outcome == RXR_FOUND_UNKNOWN,
	        "could not look: FOUND_END(0, UNKNOWN), and no desktop");
	stop_sleeper(k2);
	found_clear();
	free(R.found);
	free(R.gone);
	R.found = NULL;
	R.gone = NULL;
	close(sv[0]);
	close(sv[1]);
	R.chan = -1;

	/* the network side's client, fed by hand (the kernel's stamps are tested with a root side in the benches) */
	C.fd = -1;
	memset(&C.fseq, 0, sizeof C.fseq);
	C.found.n = 0;
	C.found.ended = false;
	C.lost = false;
	{
		union rpk pk;
		char w[64], why[128];
		RediscoveredDesktop got[4];
		int n;

		(void)rootside_found_step(&C.fseq, RXR_READY, 0, 0, w, sizeof w);
		rootside_hook_found_gone(count_exit_gone, &gone_calls);
		for (int i = 0; i < 2; i++) {
			memset(&pk, 0, sizeof pk);
			head_fill(&pk.fa.h, RXR_FOUND_AGAIN, 0);
			pk.fa.uid = 2000 + (uint32_t)i;
			pk.fa.stage = 50 + i;
			pk.fa.sessions = 1;
			snprintf(pk.fa.user, sizeof pk.fa.user, "u%d", i);
			snprintf(pk.fa.session, sizeof pk.fa.session, "c%d", i);
			snprintf(pk.fa.comm, sizeof pk.fa.comm, "labwc");
			dispatch(&pk, -1);
		}
		memset(&pk, 0, sizeof pk);
		head_fill(&pk.fe.h, RXR_FOUND_END, 0);
		pk.fe.count = 2;
		dispatch(&pk, -1);
		memset(got, 0, sizeof got);
		n = rootside_wait_found(got, 4, 10, why, sizeof why);
		require(n == 2 && got[1].uid == 2001 && strcmp(got[0].user, "u0") == 0 && got[1].stage == 51 &&
		        strcmp(got[1].comm, "labwc") == 0 && !rootside_lost(),
		        "the client collects the list and hands it over (2 desktops, fields kept)");
		memset(&pk, 0, sizeof pk);
		head_fill(&pk.fg.h, RXR_FOUND_GONE, 0);
		pk.fg.uid = 2001;
		snprintf(pk.fg.user, sizeof pk.fg.user, "u1");
		dispatch(&pk, -1);
		require(gone_calls == 1, "FOUND_GONE after the list reaches the hook");
		memset(&pk, 0, sizeof pk);
		head_fill(&pk.fa.h, RXR_FOUND_AGAIN, 0);
		dispatch(&pk, -1);
		require(rootside_lost(), "a FOUND_AGAIN after FOUND_END breaks the channel (the network side stops)");

		C.lost = false;
		memset(&C.fseq, 0, sizeof C.fseq);
		C.found.n = 0;
		C.found.ended = false;
		(void)rootside_found_step(&C.fseq, RXR_READY, 0, 0, w, sizeof w);
		memset(&pk, 0, sizeof pk);
		head_fill(&pk.fe.h, RXR_FOUND_END, 0);
		pk.fe.outcome = RXR_FOUND_UNKNOWN;
		dispatch(&pk, -1);
		n = rootside_wait_found(got, 4, 10, why, sizeof why);
		require(n == -1 && strstr(why, "could not look"), "FOUND_END UNKNOWN: -1 and the reason (the network side counts none)");

		C.lost = false;
		memset(&C.fseq, 0, sizeof C.fseq);
		C.found.n = 0;
		C.found.ended = false;
		(void)rootside_found_step(&C.fseq, RXR_READY, 0, 0, w, sizeof w);
		n = rootside_wait_found(got, 4, 10, why, sizeof why);
		require(n == -1 && why[0], "no answer: -1 and a reason, no hang (channel absent)");
	}
}

int main(void)
{
	struct rxr_auth a;
	struct rxr_spawn s;
	struct rxr_signal_msg g;
	struct rxr_close_orphan c;
	char why[256];
	struct rootside_bounds b;
	uint8_t ga[RXR_GRANT_BYTES], gb[RXR_GRANT_BYTES];
	char user[RXR_USER_MAX], rhost[RXR_RHOST_MAX];
	int ok_count;

	setvbuf(stdout, NULL, _IONBF, 0);

	printf("  the validator\n");
	auth_fill(&a);
	require(check(&a, sizeof a) == RXR_AUTH, "a well-formed AUTH passes");
	require(check(&a, sizeof a - 1) == 0, "AUTH one byte short: malformed");
	require(check(&a, sizeof a + 0) == RXR_AUTH && check(&a, sizeof(struct rxr_head)) == 0,
	        "a bare header for AUTH: malformed");
	memset(&s, 0, sizeof s);
	head_fill(&s.h, RXR_SPAWN, 9);
	require(check(&s, sizeof s) == RXR_SPAWN, "a well-formed SPAWN passes");
	require(check(&s, sizeof a) == 0, "SPAWN with AUTH's length: malformed");
	{
		struct rxr_spawn u = s;
		u.h.kind = 99;
		require(check(&u, sizeof u) == 0, "unknown kind 99: malformed");
		u.h.kind = RXR_VERDICT;
		require(check(&u, sizeof u) == 0, "a root→network kind (VERDICT) sent to the root: malformed");
		u = s;
		u.h.magic ^= 1;
		require(check(&u, sizeof u) == 0, "wrong magic: malformed");
		u = s;
		u.h.version = RXR_VERSION + 1;
		require(check(&u, sizeof u) == 0, "wrong version: malformed");
		u = s;
		u.h.request = 0;
		require(check(&u, sizeof u) == 0, "request number 0: malformed");
	}
	require(rootside_check_packet(&PEER, &s, sizeof s, true, PEER.net_pid, 1000, why,
	                              sizeof why) == 0,
	        "sent by uid 1000, not remotix: malformed");
	require(rootside_check_packet(&PEER, &s, sizeof s, true, PEER.net_pid, 0, why, sizeof why) == 0,
	        "sent by uid 0 (not remotix): malformed");
	require(rootside_check_packet(&PEER, &s, sizeof s, true, 4243, PEER.remotix_uid, why,
	                              sizeof why) == 0,
	        "sent by another pid of uid remotix: malformed");
	require(rootside_check_packet(&PEER, &s, sizeof s, false, 0, 0, why, sizeof why) == 0,
	        "no kernel credentials: malformed");
	memset(a.user, 'x', sizeof a.user);
	require(check(&a, sizeof a) == 0, "AUTH whose user fills its array without a 0: malformed");
	memset(&g, 0, sizeof g);
	head_fill(&g.h, RXR_SIGNAL, 3);
	g.sig = RXR_SIG_KILL;
	require(check(&g, sizeof g) == RXR_SIGNAL, "SIGNAL KILL passes");
	g.sig = 9;
	require(check(&g, sizeof g) == 0, "SIGNAL 9 (neither TERM nor KILL): malformed");
	memset(&c, 0, sizeof c);
	head_fill(&c.h, RXR_CLOSE_ORPHAN, 4);
	snprintf(c.user, sizeof c.user, "anna");
	require(check(&c, sizeof c) == RXR_CLOSE_ORPHAN, "CLOSE_ORPHAN passes");

	printf("  the grants\n");
	rootside_bounds_init(&b, 1000);
	require(rootside_grant_mint(&b, "anna", "192.0.2.1", 1000, ga)
	        && rootside_grant_mint(&b, "bruno", "192.0.2.2", 1000, gb)
	        && memcmp(ga, gb, sizeof ga) != 0,
	        "two grants minted, different bytes");
	require(rootside_grant_take(&b, gb, 2000, user, rhost) && strcmp(user, "bruno") == 0
	        && strcmp(rhost, "192.0.2.2") == 0,
	        "bruno's grant gives bruno and his address — never anna");
	require(!rootside_grant_take(&b, gb, 2001, user, rhost), "the same grant again: refused (single use)");
	require(!rootside_grant_take(&b, ga, 1000 + RXR_GRANT_LIFE_MS, user, rhost),
	        "anna's grant at 30 s: refused (expired)");
	{
		uint8_t forged[RXR_GRANT_BYTES];
		rootside_bounds_init(&b, 1000);
		(void)rootside_grant_mint(&b, "anna", "", 1000, ga);
		memcpy(forged, ga, sizeof forged);
		forged[RXR_GRANT_BYTES - 1] ^= 0x01;
		require(!rootside_grant_take(&b, forged, 1001, user, rhost),
		        "a grant one bit off: refused");
		uint8_t zero[RXR_GRANT_BYTES] = { 0 };
		require(!rootside_grant_take(&b, zero, 1001, user, rhost), "the zero grant: refused");
	}

	{
		/* ⛔ review 4, finding 4: a full table refuses — it never overwrites a live grant */
		uint8_t all[ROOTSIDE_GRANTS_MAX][RXR_GRANT_BYTES], extra[RXR_GRANT_BYTES];
		char who[16];
		int minted = 0, taken = 0;
		rootside_bounds_init(&b, 1000);
		for (int i = 0; i < ROOTSIDE_GRANTS_MAX; i++) {
			snprintf(who, sizeof who, "u%d", i);
			minted += rootside_grant_mint(&b, who, "", 1000 + i, all[i]);
		}
		require(minted == ROOTSIDE_GRANTS_MAX && !rootside_grant_mint(&b, "late", "", 1100, extra),
		        "the table full of live grants: the next mint is REFUSED");
		for (int i = 0; i < ROOTSIDE_GRANTS_MAX; i++)
			taken += rootside_grant_take(&b, all[i], 1200, user, rhost);
		require(taken == ROOTSIDE_GRANTS_MAX, "… and every one of the 32 still works (none overwritten)");
		for (int i = 0; i < ROOTSIDE_GRANTS_MAX; i++)
			(void)rootside_grant_mint(&b, "x", "", 2000, all[i]);
		require(rootside_grant_mint(&b, "late", "", 2000 + RXR_GRANT_LIFE_MS, extra),
		        "once they expire, a mint fits again");
	}

	printf("  the AUTH bounds\n");
	rootside_bounds_init(&b, 1000);
	ok_count = 0;
	for (int i = 0; i < 17; i++)
		ok_count += rootside_auth_admit(&b, 1000);
	require(ok_count == RXR_AUTH_IN_FLIGHT_MAX, "17 at once: 16 admitted (in flight)");
	for (int i = 0; i < 16; i++)
		rootside_auth_done(&b);
	ok_count = 0;
	for (int i = 0; i < 10; i++) {
		ok_count += rootside_auth_admit(&b, 1000);
		rootside_auth_done(&b);
	}
	require(ok_count == RXR_AUTH_BURST - 16, "burst 20: after 16, only 4 more in the same instant");
	ok_count = 0;
	for (int i = 0; i < 30; i++) {
		ok_count += rootside_auth_admit(&b, 2000);
		rootside_auth_done(&b);
	}
	require(ok_count == RXR_AUTH_PER_S, "one second later: 10 more (10/s)");

	printf("  the names refused before PAM\n");
	require(rootside_user_refused("root", "/nonexistent", NULL, why, sizeof why) == 1
	        && strstr(why, "uid 0"),
	        "root: refused (uid 0)");
	require(rootside_user_refused("rx-no-such-user-77", "/nonexistent", NULL, why, sizeof why) == 1,
	        "an unknown name: refused");
	require(rootside_user_refused("", "/nonexistent", NULL, why, sizeof why) == 1,
	        "an empty name: refused");
	{
		char path[] = "/tmp/rx-denied-XXXXXX";
		int fd = mkstemp(path);
		struct passwd *pw;
		const char *someone = NULL;
		uid_t u = 0;

		setpwent();
		while ((pw = getpwent()) != NULL)
			if (pw->pw_uid != 0 && strlen(pw->pw_name) < 64) {
				static char name[64];
				snprintf(name, sizeof name, "%s", pw->pw_name);
				someone = name;
				break;
			}
		endpwent();
		if (fd >= 0 && someone) {
			dprintf(fd, "# a comment\n  %s  \n", someone);
			close(fd);
			require(rootside_user_refused(someone, path, NULL, why, sizeof why) == 1
			        && strstr(why, path),
			        "a name listed in denied-users (with spaces and a comment): refused");
			require(rootside_user_refused(someone, "/nonexistent", &u, why, sizeof why) == 0
			        && u != 0,
			        "the same name, not listed: allowed, with its uid");
			/* ⛔ review 4 B, finding 2: a deny list that exists and cannot be read
			 *    (here a directory: fopen works, the read fails EISDIR, as root too)
			 *    refuses EVERYONE — it used to let every name through */
			require(rootside_user_refused(someone, "/tmp", &u, why, sizeof why) == 1
			        && strstr(why, "cannot be read"),
			        "an unreadable deny list: refused, «cannot be read» (fails closed)");
			unlink(path);
		} else {
			printf("    ??  no non-root user in passwd to test denied-users with\n");
		}
	}

	printf("  the address of AUTH\n");
	require(rhost_ok("") && rhost_ok("192.0.2.1") && rhost_ok("2001:db8::1")
	        && rhost_ok("fe80::1%eth0"),
	        "empty, IPv4, IPv6 and IPv6 with zone: accepted");
	require(!rhost_ok("evil host") && !rhost_ok("1.2.3.4\n") && !rhost_ok("fe80::1%e th0"),
	        "a name with a space, a newline, a zone with a space: refused");

	printf("  the review of the split: NSS (findings 7, 8)\n");
	{
		char path[] = "/tmp/rx-denied-XXXXXX";
		int fd = mkstemp(path);
		struct passwd *pw;
		static char name[64];
		const char *someone = NULL;
		uid_t u = 0;

		setpwent();
		while ((pw = getpwent()) != NULL)
			if (pw->pw_uid != 0 && strlen(pw->pw_name) < 64) {
				snprintf(name, sizeof name, "%s", pw->pw_name);
				someone = name;
				break;
			}
		endpwent();
		if (fd >= 0 && someone) {
			dprintf(fd, "%s\n", someone);
			close(fd);
			alias_name = "RX-ALIAS-OF-SOMEONE";
			alias_target = someone;
			require(rootside_user_refused("RX-ALIAS-OF-SOMEONE", path, NULL, why, sizeof why) == 1
			        && strstr(why, "for NSS"),
			        "a typed name NSS resolves to a denied name: refused (finding 8)");
			require(rootside_user_refused("RX-ALIAS-OF-SOMEONE", "/nonexistent", &u, why,
			                              sizeof why) == 0,
			        "… the same alias, nothing denied: allowed");
			alias_name = NULL;
			unlink(path);
			erange_below = 16384;
			require(rootside_user_refused(someone, "/nonexistent", &u, why, sizeof why) == 0
			        && u != 0,
			        "an entry that needs 16 KiB: the buffer grows, allowed (finding 7)");
			erange_below = 1 << 20;
			require(rootside_user_refused(someone, "/nonexistent", &u, why, sizeof why) == 2,
			        "an entry over 64 KiB: «could not look», not «unknown»");
			erange_below = 0;
		} else {
			printf("    ??  no non-root user in passwd for the NSS checks\n");
		}
	}

	printf("  the review of the split: the bounds before the names (finding 6)\n");
	{
		static struct rootside_options opts;
		int sv[2];
		struct rxr_verdict v;
		char logpath[] = "/tmp/rx-rslog-XXXXXX";
		int lf = mkstemp(logpath), saved = dup(2);
		int nos = 0, lines = 0;
		char l[512];
		FILE *f;

		opts.denied_users_path = "/nonexistent";
		R.o = &opts;
		if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) == 0 && lf >= 0 && saved >= 0) {
			R.chan = sv[0];
			rootside_bounds_init(&R.bounds, log_now_ms());
			R.bounds.tokens = 0; /* no token, and none comes back for 100 s */
			R.bounds.tokens_ms = log_now_ms() + 100000;
			auth_fill(&a);
			snprintf(a.user, sizeof a.user, "root");
			handle_auth(&a);
			require(recv(sv[1], &v, sizeof v, MSG_DONTWAIT) == (ssize_t)sizeof v
			        && v.outcome == RXR_NOT_CHECKED,
			        "AUTH «root» with no token: not checked — the bound comes before the name");
			rootside_bounds_init(&R.bounds, log_now_ms());
			R.prepam_logged_ms = 0;
			fflush(stderr);
			dup2(lf, 2);
			for (int i = 0; i < 15; i++) {
				auth_fill(&a);
				snprintf(a.user, sizeof a.user, "root");
				handle_auth(&a);
				if (recv(sv[1], &v, sizeof v, MSG_DONTWAIT) == (ssize_t)sizeof v
				    && v.outcome == RXR_NO)
					nos++;
			}
			fflush(stderr);
			dup2(saved, 2);
			f = fopen(logpath, "r");
			while (f && fgets(l, sizeof l, f))
				lines += strstr(l, "refused BEFORE PAM") != NULL;
			if (f)
				fclose(f);
			require(nos == 15 && R.bounds.in_flight == 0,
			        "15 AUTH «root» within the burst: 15 NO, none left in flight");
			char d[120];
			snprintf(d, sizeof d, "… and %d «refused BEFORE PAM» line(s) written, not 15", lines);
			require(lines == 1, d);
			close(sv[0]);
			close(sv[1]);
			R.chan = -1;
		} else {
			printf("    ??  no socketpair or temporary file\n");
		}
		if (lf >= 0) {
			close(lf);
			unlink(logpath);
		}
	}

	printf("  the review of the split: no CHILD_EXITED or VERDICT lost (findings 4, 5)\n");
	{
		int sv[2], n_full = 0, got = 0;
		struct rxr_child_exited e, back;
		char junk[sizeof(struct rxr_ready)];

		R.cap = 4;
		R.outbox = calloc((size_t)R.cap * 4, sizeof *R.outbox);
		R.nout = 0;
		if (R.outbox && socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) == 0) {
			fcntl(sv[0], F_SETFL, O_NONBLOCK);
			R.chan = sv[0];
			memset(junk, 0, sizeof junk);
			while (send(sv[0], junk, sizeof junk, MSG_DONTWAIT) == (ssize_t)sizeof junk
			       && n_full < 100000)
				n_full++;
			memset(&e, 0, sizeof e);
			head_fill(&e.h, RXR_CHILD_EXITED, 0);
			e.serial = 77;
			send_exited(&e);
			require(R.nout == 1, "CHILD_EXITED to a full channel: kept, not lost");
			while (recv(sv[1], junk, sizeof junk, MSG_DONTWAIT) > 0)
				;
			outbox_flush();
			if (recv(sv[1], &back, sizeof back, MSG_DONTWAIT) == (ssize_t)sizeof back
			    && back.h.kind == RXR_CHILD_EXITED && back.serial == 77)
				got = 1;
			require(R.nout == 0 && got, "… and sent once the network side reads again");
			close(sv[0]);
			close(sv[1]);
			R.chan = -1;
		} else {
			printf("    ??  no socketpair\n");
		}
	}
	{
		union rpk pk;
		static int exits, verdicts;

		exits = verdicts = 0;
		C.on_exited = count_exit;
		C.exited_ctx = &exits;
		C.on_verdict = count_verdict;
		C.verdict_ctx = &verdicts;
		for (int i = 0; i < 300; i++) {
			memset(&pk, 0, sizeof pk);
			head_fill(&pk.h, RXR_CHILD_EXITED, 0);
			pk.e.serial = (uint64_t)i + 1;
			aside_or_dispatch(&pk, -1);
		}
		require(exits == 300 && C.qn == 0,
		        "300 CHILD_EXITED during a wait: all dispatched at once, none queued");
		for (int i = 0; i < 300; i++) {
			memset(&pk, 0, sizeof pk);
			head_fill(&pk.h, RXR_VERDICT, 1000 + (uint64_t)i);
			pk.v.outcome = RXR_NO;
			aside_or_dispatch(&pk, -1);
		}
		require(C.qn == 300 && verdicts == 0, "300 VERDICTs during a wait: all put aside (the old queue held 256)");
		queue_drain();
		require(verdicts == 300 && C.qn == 0, "… and all delivered at the next drain");
	}

	printf("  review 2: CLOSE_ORPHAN's own bounds (M1)\n");
	{
		struct rootside_bounds ob;

		rootside_bounds_init(&ob, 5000);
		ok_count = 0;
		for (int i = 0; i < 8; i++)
			ok_count += rootside_orphan_admit(&ob, 5000);
		require(ok_count == ROOTSIDE_ORPHAN_BURST, "8 CLOSE_ORPHAN at once: 5 looked at (burst)");
		ok_count = 0;
		for (int i = 0; i < 8; i++)
			ok_count += rootside_orphan_admit(&ob, 6000);
		require(ok_count == ROOTSIDE_ORPHAN_PER_S, "one second later: 2 more (2/s)");
		require(rootside_orphan_uid_admit(&ob, 1000, 7000)
		        && !rootside_orphan_uid_admit(&ob, 1000, 7000 + ROOTSIDE_ORPHAN_UID_MS - 1)
		        && rootside_orphan_uid_admit(&ob, 1001, 7001)
		        && rootside_orphan_uid_admit(&ob, 1000, 7000 + ROOTSIDE_ORPHAN_UID_MS),
		        "one CLOSE_ORPHAN per uid per 30 s; another uid is not held up");
		/* lane 1's pre-release review: a live hold is never evicted — a run of other uids
		 * filling the table is refused instead (before: the oldest, uid 1000's, went) */
		{
			struct rootside_bounds hb;
			int filled = 0;
			rootside_bounds_init(&hb, 10000);
			(void)rootside_orphan_uid_admit(&hb, 1000, 10000);
			for (int i = 0; i < 2 * ROOTSIDE_ORPHAN_UIDS; i++)
				filled += rootside_orphan_uid_admit(&hb, (uid_t)(2000 + i), (uint64_t)(10001 + i));
			require(filled == ROOTSIDE_ORPHAN_UIDS - 1
			        && !rootside_orphan_uid_admit(&hb, 1000, 10000 + ROOTSIDE_ORPHAN_UID_MS - 1),
			        "a table full of live holds refuses new uids and never frees uid 1000's");
		}
	}

	printf("  review 2: a network side that shut its reading end (M2)\n");
	{
		int sv[2];

		if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) == 0) {
			fcntl(sv[0], F_SETFL, O_NONBLOCK);
			R.chan = sv[0];
			R.net_pid = 0;
			shutdown(sv[1], SHUT_RD);
			send_verdict(9, RXR_NO, NULL);
			require(R.chan == -1, "a send that says EPIPE: the channel is closed (net_kill), no spin");
			close(sv[1]);
		} else {
			printf("    ??  no socketpair\n");
		}
	}
	{
		int sv[2], n_full = 0, lines = 0;
		char junk[sizeof(struct rxr_ready)], l[512];
		char logpath[] = "/tmp/rx-rslog2-XXXXXX";
		int lf = mkstemp(logpath), saved = dup(2);
		FILE *f;

		if (lf >= 0 && saved >= 0 && socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) == 0) {
			fcntl(sv[0], F_SETFL, O_NONBLOCK);
			R.chan = sv[0];
			memset(junk, 0, sizeof junk);
			while (send(sv[0], junk, sizeof junk, MSG_DONTWAIT) == (ssize_t)sizeof junk
			       && n_full < 100000)
				n_full++;
			fflush(stderr);
			dup2(lf, 2);
			for (int i = 0; i < 30; i++)
				send_verdict(10 + (uint64_t)i, RXR_NO, NULL);
			fflush(stderr);
			dup2(saved, 2);
			f = fopen(logpath, "r");
			while (f && fgets(l, sizeof l, f))
				lines += strstr(l, "did not leave") != NULL;
			if (f)
				fclose(f);
			char d[120];
			snprintf(d, sizeof d, "30 VERDICTs to a full channel: %d «did not leave» line(s), not 30",
			         lines);
			require(lines == 1 && R.chan == sv[0], d);
			close(sv[0]);
			close(sv[1]);
			R.chan = -1;
			unlink(logpath);
		} else {
			printf("    ??  no socketpair or temporary file\n");
		}
	}

	found_tests();

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
