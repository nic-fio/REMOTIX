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
#define EXPECTED_CHECKS 138

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
	/* ⭐ BACKPRESSURE: a channel that takes only some of the list.  The pump stops where the socket is full, resumes on the next
	 *    turn, sends every FOUND_AGAIN once and in order, FOUND_END last with the right count — and a stage that dies in the middle of
	 *    the list is taken out of the count if it was not announced yet, announced (FOUND_GONE, after FOUND_END) if it was. */
	{
		enum { BIG = 40 };
		static RediscoveredDesktop big[BIG];
		int small = 4608, got_again = 0, got_end = -1, got_gone = 0, order_ok = 1, turns, first_batch;
		bool end_seen = false, gone_before_end = false;
		char name[32];

		setsockopt(sv[0], SOL_SOCKET, SO_SNDBUF, &small, sizeof small);
		for (int i = 0; i < BIG; i++) {
			snprintf(name, sizeof name, "u%d", i);
			desktop_of(&big[i], k2, name, (uid_t)(3000 + i));
		}
		found_install(big, BIG, true, "/proc");
		found_pump();
		first_batch = 0;
		while (take(sv[1], &in, sizeof in) > 0) {
			order_ok = order_ok && in.fa.h.kind == RXR_FOUND_AGAIN && in.fa.uid == (uint32_t)(3000 + first_batch);
			first_batch++;
		}
		require(first_batch > 0 && first_batch < BIG && R.found_phase == FOUND_SENDING && order_ok,
		        "a small socket takes only part of the list (the pump stops, still SENDING, what left is in order)");
		got_again = first_batch;
		for (turns = 0; turns < 200 && !end_seen; turns++) {
			found_pump();
			while (take(sv[1], &in, sizeof in) > 0) {
				if (in.fa.h.kind == RXR_FOUND_AGAIN) {
					order_ok = order_ok && !end_seen && in.fa.uid == (uint32_t)(3000 + got_again);
					got_again++;
				} else if (in.fa.h.kind == RXR_FOUND_END) {
					end_seen = true;
					got_end = (int)in.fe.count;
				}
			}
		}
		require(got_again == BIG && order_ok && end_seen && got_end == BIG && R.found_phase == FOUND_LISTED,
		        "the pump resumes on the next turns: 40 FOUND_AGAIN once each and in order, then FOUND_END(40)");
		require(take(sv[1], &in, sizeof in) < 0, "and nothing after it");

		/* a stage that dies in the middle of the list */
		found_install(big, BIG, true, "/proc");
		found_pump();
		first_batch = 0;
		while (take(sv[1], &in, sizeof in) > 0)
			first_batch++;
		{
			pid_t k3 = k2;

			stop_sleeper(k3);
			k2 = -1;
		}
		found_check(log_now_ms());
		end_seen = false;
		got_again = first_batch;
		got_end = -1;
		for (turns = 0; turns < 200; turns++) {
			found_pump();
			while (take(sv[1], &in, sizeof in) > 0) {
				if (in.fa.h.kind == RXR_FOUND_AGAIN) {
					got_again++;
				} else if (in.fa.h.kind == RXR_FOUND_END) {
					end_seen = true;
					got_end = (int)in.fe.count;
				} else if (in.fa.h.kind == RXR_FOUND_GONE) {
					gone_before_end = gone_before_end || !end_seen;
					got_gone++;
				}
			}
			if (end_seen && R.ngone == 0)
				break;
		}
		require(first_batch > 0 && first_batch < BIG && got_again == first_batch && got_end == first_batch,
		        "the unannounced ones that died are out of the count: FOUND_END says what was sent");
		require(got_gone == first_batch && !gone_before_end,
		        "the announced ones that died get FOUND_GONE, all of them, after FOUND_END");
	}
	/* ⭐ BACKPRESSURE, one stage each (the reviewer's cases): 40 real stages, a socket that takes only part of the list.  The one
	 *    ANNOUNCED and killed gives FOUND_GONE after FOUND_END; the one NOT YET announced and killed lowers FOUND_END's count by
	 *    one and is never announced; the other 38 arrive once each, in order. */
	{
		enum { N = 40 };
		static RediscoveredDesktop dd[N];
		pid_t kk[N];
		int small = 4608, first_batch = 0, again = 0, gone = 0, end_count = -1, turns, dup = 0;
		bool order_ok = true, end_seen = false, gone_before_end = false, wrong_gone = false, seen[N] = { false };
		char name[32];

		for (int i = 0; i < N; i++) {
			snprintf(name, sizeof name, "w%d", i);
			kk[i] = sleeper();
			desktop_of(&dd[i], kk[i], name, (uid_t)(4000 + i));
		}
		setsockopt(sv[0], SOL_SOCKET, SO_SNDBUF, &small, sizeof small);
		found_install(dd, N, true, "/proc");
		found_pump();
		while (take(sv[1], &in, sizeof in) > 0) {
			order_ok = order_ok && in.fa.h.kind == RXR_FOUND_AGAIN && in.fa.uid == (uint32_t)(4000 + first_batch);
			seen[first_batch] = true;
			first_batch++;
		}
		again = first_batch;
		require(first_batch > 1 && first_batch < N - 1 && order_ok,
		        "(a) the socket takes only part of the list; what left is the beginning, in order");
		stop_sleeper(kk[0]);     /* announced */
		stop_sleeper(kk[N - 1]); /* not yet */
		found_check(log_now_ms());
		for (turns = 0; turns < 200; turns++) {
			found_pump();
			while (take(sv[1], &in, sizeof in) > 0) {
				if (in.fa.h.kind == RXR_FOUND_AGAIN) {
					int idx = (int)in.fa.uid - 4000;

					order_ok = order_ok && !end_seen && idx == again + (idx - again) && idx >= again;
					if (idx >= 0 && idx < N) {
						dup += seen[idx];
						seen[idx] = true;
					}
					again++;
				} else if (in.fa.h.kind == RXR_FOUND_END) {
					end_seen = true;
					end_count = (int)in.fe.count;
				} else if (in.fa.h.kind == RXR_FOUND_GONE) {
					gone_before_end = gone_before_end || !end_seen;
					wrong_gone = wrong_gone || in.fg.uid != 4000;
					gone++;
				}
			}
			if (end_seen && R.ngone == 0)
				break;
		}
		require(dup == 0 && order_ok && again == N - 1 && !seen[N - 1] && end_seen,
		        "(b) the rest arrive once each and in order, the killed unannounced one never");
		require(end_count == N - 1 && end_count == again, "(c) FOUND_END counts what was announced: N-1");
		require(gone == 1 && !wrong_gone && !gone_before_end,
		        "(d) the announced one that was killed gets FOUND_GONE (only it), after FOUND_END");
		for (int i = 1; i < N - 1; i++)
			stop_sleeper(kk[i]);
	}
	if (k2 > 0)
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
	static struct rootside_bounds b;
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
	require(ok_count == RXR_AUTH_BURST, "17 at once: the burst (8) admitted");
	for (int i = 0; i < ok_count; i++)
		rootside_auth_done(&b);
	ok_count = 0;
	for (int i = 0; i < 10; i++) {
		ok_count += rootside_auth_admit(&b, 1000);
		rootside_auth_done(&b);
	}
	require(ok_count == 0, "burst 8: none more in the same instant");
	ok_count = 0;
	for (int i = 0; i < 30; i++) {
		ok_count += rootside_auth_admit(&b, 2000);
		rootside_auth_done(&b);
	}
	require(ok_count == RXR_AUTH_PER_S, "one second later: 3 more (3/s)");
	rootside_bounds_init(&b, 1000);
	b.tokens = 100; /* a slow PAM, a long quiet before: the in-flight bound is its own */
	ok_count = 0;
	for (int i = 0; i < 20; i++)
		ok_count += rootside_auth_admit(&b, 1000);
	require(ok_count == RXR_AUTH_IN_FLIGHT_MAX, "20 at once with tokens to spare: 16 in flight");
	for (int i = 0; i < 16; i++)
		rootside_auth_done(&b);

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
			for (int i = 0; i < RXR_AUTH_BURST - 1; i++) {
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
			require(nos == RXR_AUTH_BURST - 1 && R.bounds.in_flight == 0,
			        "7 AUTH «root» within the burst (8): 7 NO, none left in flight");
			char d[120];
			snprintf(d, sizeof d, "… and %d «refused BEFORE PAM» line(s) written, not 7", lines);
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
		static struct rootside_bounds ob;

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
			static struct rootside_bounds hb;
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

	printf("  1.5 (split audit R1): CLOSE_ORPHAN only for a desktop abandoned for abandon_s\n");
	{
		static struct rootside_bounds ab;
		uint64_t left = 0;

		rootside_bounds_init(&ab, 5000);
		require(!rootside_orphan_abandoned(&ab, 1000, 999999999, &left) && left == UINT64_MAX,
		        "abandonment clock off (abandon_ms 0): never accepted, whatever the time");
		ab.abandon_ms = 60000;
		require(!rootside_orphan_abandoned(&ab, 1000, 64999, &left) && left == 1,
		        "no exit seen (desktop found after the root side's restart): counts from the "
		        "root side's start — 1 ms short, refused");
		require(rootside_orphan_abandoned(&ab, 1000, 65000, &left) && left == UINT64_MAX,
		        "… and accepted exactly at start + abandon_s");
		rootside_exit_note(&ab, 1000, 100000);
		require(!rootside_orphan_abandoned(&ab, 1000, 159999, &left) && left == 1
		        && rootside_orphan_abandoned(&ab, 1000, 160000, NULL),
		        "a child of uid 1000 left at 100 s: refused until 160 s, accepted from then");
		require(rootside_orphan_abandoned(&ab, 1001, 160000, NULL)
		        && rootside_orphan_abandoned(&ab, 1001, 65000, NULL),
		        "another uid is not held up by uid 1000's exit");
		rootside_exit_note(&ab, 1000, 200000);
		require(!rootside_orphan_abandoned(&ab, 1000, 250000, NULL)
		        && rootside_orphan_abandoned(&ab, 1000, 260000, NULL),
		        "a second exit of the same uid moves the clock forward (one entry, not two)");
		/* a full table drops the OLDEST and keeps its time as a floor for uids with no entry:
		 * a forgotten uid then waits at least as long as it really should */
		{
			static struct rootside_bounds fb;

			rootside_bounds_init(&fb, 5000);
			fb.abandon_ms = 60000;
			for (int i = 0; i < ROOTSIDE_EXIT_UIDS; i++)
				rootside_exit_note(&fb, (uid_t)(2000 + i), (uint64_t)(100000 + i));
			rootside_exit_note(&fb, 3000, 200000); /* evicts uid 2000 (100000) */
			require(!rootside_orphan_abandoned(&fb, 2000, 159999, NULL)
			        && rootside_orphan_abandoned(&fb, 2000, 160000, NULL),
			        "a table full: the evicted uid waits from the forgotten exit, not from the start");
			require(!rootside_orphan_abandoned(&fb, 2005, 160004, NULL)
			        && rootside_orphan_abandoned(&fb, 2005, 160005, NULL),
			        "… and a uid still in the table keeps its own time");
			require(!rootside_orphan_abandoned(&fb, 3000, 259999, NULL)
			        && rootside_orphan_abandoned(&fb, 3000, 260000, NULL),
			        "… and the newcomer has its own");
		}
	}

	printf("  1.5 (R1, review): the exit of a child whose network side died, and the overflow\n");
	{
		static struct rootside_bounds ab;
		struct own_child kid;
		pid_t netp, kidp;
		uint64_t left = 0;
		int tries;

		/* the sum with abandon_ms saturates instead of wrapping */
		rootside_bounds_init(&ab, 5000);
		ab.abandon_ms = UINT64_MAX;
		require(!rootside_orphan_abandoned(&ab, 1000, 1ull << 62, &left) && left > 0,
		        "abandon_ms at the maximum: no wrap, nothing is abandoned (it did, once, by wrapping)");
		/* network side killed, a SLOW child: the clock starts when the network side died,
		 * not when the child is finally reaped (else an honest request, made from the network
		 * side's own clock that started at its restart, would come too soon and the desktop
		 * stay open for good) */
		netp = fork();
		if (netp == 0)
			_exit(0);
		kidp = fork();
		if (kidp == 0) {
			pause();
			_exit(0);
		}
		memset(&kid, 0, sizeof kid);
		kid.used = true;
		kid.pid = kidp;
		kid.uid = 1000;
		kid.generation = 1;
		snprintf(kid.user, sizeof kid.user, "anna");
		R.cap = 1;
		R.kids = &kid;
		R.chan = -1;
		R.net_pid = netp;
		R.generation = 1;
		R.stopping = false;
		rootside_bounds_init(&R.bounds, 1000);
		R.bounds.abandon_ms = 60000;
		for (tries = 0; tries < 100 && R.net_pid > 0; tries++) {
			usleep(20000);
			reap_net(20000);
		}
		require(R.net_pid == 0 && kid.orphaned_ms == 20000,
		        "the network side's death is written on its children (orphaned_ms)");
		R.generation = 2; /* the network side was started again */
		kill(kidp, SIGKILL);
		for (tries = 0; tries < 100 && kid.used; tries++) {
			usleep(20000);
			reap_kids();
		}
		require(!kid.used, "the slow child is reaped later");
		require(!rootside_orphan_abandoned(&R.bounds, 1000, 20000 + 60000 - 1, &left) && left == 1
		        && rootside_orphan_abandoned(&R.bounds, 1000, 20000 + 60000, NULL),
		        "… and its uid counts from the network side's death (20 s), not from the reaping");
		R.kids = NULL;
		R.cap = 0;
		R.net_pid = 0;
	}

	printf("  1.5 (split audit R2): the root side's own pause for what PAM refused\n");
	{
		static struct rootside_bounds lb; /* ~400 KB: not on the stack */
		struct rootside_login_event ev;
		uint64_t left = 0;
		unsigned tk = 0, tk2 = 0;
		int n_ok = 0;
#define ADMIT(u, h, t) rootside_login_admit(&lb, (u), (h), (t), &left, &tk)
#define REFUSE(u, h, t) do { (void)ADMIT(u, h, t); rootside_login_done(&lb, (u), (h), (t), tk, RXR_LOGIN_REFUSED, &ev); } while (0)

		rootside_bounds_init(&lb, 1000);
		/* (uid, address): five refused in a row start a 15-minute pause */
		for (int i = 0; i < 5; i++) {
			require(ADMIT("1000", "192.0.2.1", 10000 + 1000 * i) == RXR_LOGIN_OK,
			        "an AUTH is asked while fewer than 5 refused");
			rootside_login_done(&lb, "1000", "192.0.2.1", 10000 + 1000 * i, tk, RXR_LOGIN_REFUSED, &ev);
			if (i < 4)
				require(!ev.pair_ban, "… and the refused one starts no pause yet");
		}
		require(ev.pair_ban && ev.pair_level == 1 && ev.pair_ms == 900000 && !ev.user_ban,
		        "the fifth refused in 5 min: pause 1 of the ladder, 15 min, for that user from that address");
		require(ADMIT("1000", "192.0.2.1", 15000) == RXR_LOGIN_PAIR_PAUSED && left == 899000,
		        "that user from that address is paused: not asked, with the time left");
		require(ADMIT("1000", "192.0.2.9", 15000) == RXR_LOGIN_OK
		        && (rootside_login_done(&lb, "1000", "192.0.2.9", 15000, tk, RXR_LOGIN_UNCHECKED, NULL), 1),
		        "the SAME user from ANOTHER address is not blocked (a stranger cannot keep anna out)");
		require(ADMIT("1001", "192.0.2.1", 15000) == RXR_LOGIN_OK
		        && (rootside_login_done(&lb, "1001", "192.0.2.1", 15000, tk, RXR_LOGIN_UNCHECKED, NULL), 1),
		        "another user from the same address is not held up either");
		require(ADMIT("1000", "192.0.2.1", 14000 + 900000 + 1) == RXR_LOGIN_OK,
		        "after 15 min the user is asked again from that address");
		rootside_login_done(&lb, "1000", "192.0.2.1", 14000 + 900000 + 1, tk, RXR_LOGIN_UNCHECKED, NULL);
		{
			uint64_t t = 14000 + 900000 + 10;

			for (int i = 0; i < 5; i++)
				REFUSE("1000", "192.0.2.1", t + i);
			require(ev.pair_ban && ev.pair_level == 2 && ev.pair_ms == 3600000, "five more: pause 2, one hour");
			for (int k = 3; k <= 4; k++) {
				t += 3600000 + 10;
				for (int i = 0; i < 5; i++)
					REFUSE("1000", "192.0.2.1", t + i);
			}
			require(ev.pair_ban && ev.pair_level == 3 && ev.pair_ms == 43200000,
			        "the third and the fourth: 12 hours, the ladder stops there");
		}
		/* in flight counts as a failure to come: a burst cannot step over the limit */
		rootside_bounds_init(&lb, 1000);
		n_ok = 0;
		for (int i = 0; i < 10; i++) {
			unsigned t_;

			n_ok += rootside_login_admit(&lb, "2000", "192.0.2.1", 5000, NULL, &t_) == RXR_LOGIN_OK;
			if (i == 0)
				tk2 = t_;
		}
		require(n_ok == ROOTSIDE_LOGIN_PAIR_LIMIT && ADMIT("2000", "192.0.2.1", 5000) == RXR_LOGIN_PAIR_BUSY,
		        "10 AUTH at once for one user from one address, none answered: 5 asked, the rest «busy»");
		for (int i = 0; i < n_ok; i++)
			rootside_login_done(&lb, "2000", "192.0.2.1", 5000, tk2, RXR_LOGIN_UNCHECKED, NULL);
		require(ADMIT("2000", "192.0.2.1", 5000) == RXR_LOGIN_OK,
		        "«not checked» answers are not failures: the places come back, nothing counted");
		rootside_login_done(&lb, "2000", "192.0.2.1", 5000, tk, RXR_LOGIN_UNCHECKED, NULL);
		/* the sliding window: failures 100 s apart never add up to five inside five minutes */
		rootside_bounds_init(&lb, 1000);
		for (int i = 0; i < 8; i++) {
			REFUSE("3000", "192.0.2.1", 1000 + (uint64_t)i * 100000);
			if (ev.pair_ban)
				break;
		}
		require(!ev.pair_ban, "failures 100 s apart: never 5 inside the window, no pause");
		/* a yes clears that user's failures (both levels), not the address's */
		rootside_bounds_init(&lb, 1000);
		for (int i = 0; i < 4; i++)
			REFUSE("4000", "198.51.100.9", 2000 + i);
		(void)ADMIT("4000", "198.51.100.9", 2010);
		rootside_login_done(&lb, "4000", "198.51.100.9", 2010, tk, RXR_LOGIN_ACCEPTED, NULL);
		REFUSE("4000", "198.51.100.9", 2020);
		require(!ev.pair_ban, "four refused, a yes, one refused: the count restarted (no pause)");
		/* the address (1.5: ROOTSIDE_LOGIN_HOST_LIMIT, 20; it was 12): that many refused in 5 min from different users pauses the address for everyone */
		rootside_bounds_init(&lb, 1000);
		for (int i = 0; i < ROOTSIDE_LOGIN_HOST_LIMIT - 1; i++) {
			char k[16];

			snprintf(k, sizeof k, "%d", 5000 + i);
			REFUSE(k, "203.0.113.7", 3000 + i);
		}
		require(!ev.host_ban && ADMIT("9999", "203.0.113.7", 3500) == RXR_LOGIN_OK,
		        "one refusal short of the limit: no pause, and a new attempt is admitted");
		rootside_login_done(&lb, "9999", "203.0.113.7", 3500, tk, RXR_LOGIN_UNCHECKED, NULL);
		/* 1.5: the ATTACHMENTS IN FLIGHT do not count at the address level: with LIMIT-1 failures, many users can be in flight at once */
		{
			unsigned tf[8];
			int ok_in_flight = 0;

			for (int i = 0; i < 8; i++) {
				char k[16];

				snprintf(k, sizeof k, "%d", 7000 + i);
				tf[i] = 0;
				if (rootside_login_admit(&lb, k, "203.0.113.7", 3600, NULL, &tf[i]) == RXR_LOGIN_OK)
					ok_in_flight++;
			}
			require(ok_in_flight == 8, "LIMIT-1 failures and eight users in flight at once from the address: all admitted (the address counts only the failures)");
			for (int i = 0; i < 8; i++) {
				char k[16];

				snprintf(k, sizeof k, "%d", 7000 + i);
				rootside_login_done(&lb, k, "203.0.113.7", 3601, tf[i], RXR_LOGIN_UNCHECKED, NULL);
			}
		}
		REFUSE("5999", "203.0.113.7", 3700);
		require(ev.host_ban && ev.host_level == 1 && !ev.pair_ban && !ev.user_ban,
		        "the LIMIT-th refusal from one address (different users): the address is paused, not the users");
		require(ADMIT("9999", "203.0.113.7", 4000) == RXR_LOGIN_HOST_PAUSED
		        && ADMIT("9999", "203.0.113.8", 4000) == RXR_LOGIN_OK,
		        "… everybody from that address waits, the others do not");
		rootside_login_done(&lb, "9999", "203.0.113.8", 4000, tk, RXR_LOGIN_UNCHECKED, NULL);
		/* the uid alone: 15 refused from 15 DIFFERENT addresses → a short, FIXED pause, never 12 h */
		rootside_bounds_init(&lb, 1000);
		for (int i = 0; i < 15; i++) {
			char h[24];

			snprintf(h, sizeof h, "192.0.2.%d", 10 + i);
			REFUSE("7000", h, 10000 + i);
		}
		require(ev.user_ban && ev.user_ms == ROOTSIDE_LOGIN_USER_PAUSE_MS && !ev.pair_ban,
		        "15 refused for one user from 15 addresses: the user is paused 15 min from anywhere");
		require(ADMIT("7000", "192.0.2.200", 20000) == RXR_LOGIN_USER_PAUSED
		        && ADMIT("7001", "192.0.2.200", 20000) == RXR_LOGIN_OK
		        && (rootside_login_done(&lb, "7001", "192.0.2.200", 20000, tk, RXR_LOGIN_UNCHECKED, NULL), 1),
		        "… and only that user");
		{
			uint64_t t = 10000 + ROOTSIDE_LOGIN_USER_PAUSE_MS + 10;
			uint64_t longest = 0;

			for (int round = 0; round < 4; round++) {
				for (int i = 0; i < 15; i++) {
					char h[24];

					snprintf(h, sizeof h, "198.18.%d.%d", round, i);
					REFUSE("7000", h, t + (uint64_t)i);
					if (ev.user_ban && ev.user_ms > longest)
						longest = ev.user_ms;
				}
				t += ROOTSIDE_LOGIN_USER_PAUSE_MS + 10;
			}
			require(longest == ROOTSIDE_LOGIN_USER_PAUSE_MS,
			        "four rounds of 15 more: the pause stays 15 min, it never grows (no 12 h from strangers)");
		}
		/* recidivism of the (uid, address) is forgotten after 24 h without a pause */
		rootside_bounds_init(&lb, 1000);
		for (int i = 0; i < 5; i++)
			REFUSE("6000", "192.0.2.1", 5000 + i);
		{
			uint64_t t = 5000 + 900000 + ROOTSIDE_LOGIN_FORGET_MS;

			for (int i = 0; i < 5; i++)
				REFUSE("6000", "192.0.2.1", t + i);
			require(ev.pair_ban && ev.pair_level == 1, "24 h after the last pause: back to the first rung");
		}
		/* the uid table is the ground floor: all its places in flight → FULL, no entry is stolen */
		rootside_bounds_init(&lb, 1000);
		n_ok = 0;
		for (int i = 0; i < ROOTSIDE_LOGIN_USERS + 5; i++) {
			char k[16];

			snprintf(k, sizeof k, "%d", 100000 + i);
			n_ok += rootside_login_admit(&lb, k, "", 6000 + (uint64_t)i, NULL, &tk2) == RXR_LOGIN_OK;
		}
		require(n_ok == ROOTSIDE_LOGIN_USERS && ADMIT("8000", "", 7000) == RXR_LOGIN_FULL,
		        "every place of the uid table in flight: a newcomer is refused (FULL)");
		for (int i = 0; i < ROOTSIDE_LOGIN_USERS; i++) {
			char k[16];

			snprintf(k, sizeof k, "%d", 100000 + i);
			rootside_login_done(&lb, k, "", 7000, RXR_LOGIN_L_USER | RXR_LOGIN_L_PAIR | RXR_LOGIN_L_HOST,
			                    RXR_LOGIN_UNCHECKED, NULL);
		}
		require(ADMIT("8000", "", 7001) == RXR_LOGIN_OK, "… and once they are idle the oldest is taken back");
		rootside_login_done(&lb, "8000", "", 7001, tk, RXR_LOGIN_UNCHECKED, NULL);
		/* the address table full: the uid level decides, no FULL (and the places are given back
		 * only where they were taken) */
		rootside_bounds_init(&lb, 1000);
		for (int i = 0; i < ROOTSIDE_LOGIN_HOSTS; i++) {
			char h[24], k[16];

			snprintf(h, sizeof h, "10.0.%d.%d", i / 200, i % 200);
			snprintf(k, sizeof k, "%d", 9200 + i);
			(void)rootside_login_admit(&lb, k, h, 6000, NULL, &tk2); /* fills the address table */
		}
		{
			unsigned t3 = 0;
			int r = rootside_login_admit(&lb, "9999", "172.16.0.1", 6001, NULL, &t3);

			require(r == RXR_LOGIN_OK && (t3 & RXR_LOGIN_L_USER) && !(t3 & RXR_LOGIN_L_HOST),
			        "the address table full: no FULL, the uid level alone decides (no place taken on the address)");
		}
		/* the (uid, address) table full: the same */
		rootside_bounds_init(&lb, 1000);
		for (int i = 0; i < ROOTSIDE_LOGIN_PAIRS; i++) {
			char h[24];

			snprintf(h, sizeof h, "10.1.%d.%d", i / 200, i % 200);
			(void)rootside_login_admit(&lb, "9300", h, 6000, NULL, &tk2); /* 512 pairs, but the uid level stops at 15 */
		}
		for (int i = 0; i < ROOTSIDE_LOGIN_PAIRS; i++) {
			char h[24], k[16];

			snprintf(h, sizeof h, "10.2.%d.%d", i / 200, i % 200);
			snprintf(k, sizeof k, "%d", 9400 + i);
			(void)rootside_login_admit(&lb, k, h, 6000, NULL, &tk2); /* 512 other pairs in flight */
		}
		{
			unsigned t3 = 0;
			int r = rootside_login_admit(&lb, "9998", "172.16.0.2", 6002, NULL, &t3);

			require(r == RXR_LOGIN_OK && (t3 & RXR_LOGIN_L_USER) && !(t3 & RXR_LOGIN_L_PAIR),
			        "the (uid, address) table full: no FULL, the uid level alone decides");
		}
#undef ADMIT
#undef REFUSE
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
