/*
 * test.c — unit test of the COUNTER LOGIC of the login defences (§4.4-bis, plan «Difese del login», 24 Oct 2026),
 * in src/rcp.c: login_reserve(), login_resolve(), login_release(), rcp_orphan_verdict(), rcp_banned(), rcp_unblock(),
 * save_ban()/rcp_ban_load(), rcp_key_address(), and the tags of the log (HMAC-SHA256).
 *
 * HOW: the REAL src/rcp.c is #included (never modified), like benches/fuzz/rcp-msg/fuzz_rcp_msg.c; the log is that harness's
 * stubs_log.c.  The counting code is PURE (it takes `now` as an argument and reads no clock), so the test drives it with a
 * SIMULATED clock: `at(s)` is the monotonic millisecond `s` seconds after the start.  Nothing sleeps.
 * The file test (ban file) writes in a mkdtemp() directory under /tmp, INSIDE the container.
 *
 * What it covers (each is a group of checks, named in the output):
 *   keys        IPv4 whole, IPv6 /64, ::ffff: and NAT64 -> IPv4, ::1 whole, idempotent; the /48 of a key
 *   thresholds  (key,user) 5 in 5 min · key 12 in 5 min · /48 30 in 10 min: N-1 does not ban, N does; the SLIDING window
 *               (a first failure that has left the window does not count) and the boundary of the window
 *   progression 15 min -> 1 h -> 12 h -> 12 h; forgotten after 24 h without a ban (and NOT forgotten at 23 h)
 *   reset       success resets only (key,user): not the key's count, not the /48's, not the recidivism
 *   rotation    IPv6: five addresses of one /64 are one key; another /64 is another key
 *   in flight   at most 2 per (key,user); failed + in flight at the limit refuses and is NOT a failure; release gives back
 *   orphan      a verdict whose connection is gone is counted all the same (failure, success, same key as the session's)
 *   table       full of bookings: the new entry is refused and counted; full of non-banned entries: the oldest is
 *               evicted and declared; over the ban quota (hand-made): one ban is dropped, the least valuable
 *   quota       (R1 of the audit of 25 Oct 2026 and the rule decided after the review) botnets of 300 and of 54 addresses taking
 *               turns: at most BAN_QUOTA(+a few) bans, NO ban dropped, the first ban still there after 14 minutes, the ladder
 *               climbs (level 2, 1 hour); the owner (a known key) always gets in and his own ban drops nobody; the unknown keys
 *               share a counter of 5 failures in 5 min at the quota (LV_QUOTA, nothing created or evicted, back after the window,
 *               not used below the quota); attempts and single failures from 4000 keys erase no ban; 16 bookings never LV_FULL;
 *               the attempts IN FLIGHT count in the common counter, UNBLOCK zeroes it; the known keys are written to the ban file
 *               (G2 lines, skipped by the 1.0) and read back after a restart with the quota full; the last resort is for known
 *               keys only (an unknown one gets LV_FULL); a G2 line from the future is read as recent with its date brought back to now,
 *               the newer date wins when a key is in the file twice (itself and its HMAC); the log names every ban dropped; a ban file with more bans than the quota keeps the most valuable in ANY order
 *               (ascending, descending, two shuffles) and the displaced ones keep their level
 *   unblock     removes every level of the address (user, key, /48) and the recidivism
 *   file        the old format is converted, the new one round-trips (ban, user with spaces, recidivism), -1 on a bad path
 *   log         `unknown user [hmac6]` (never the name); a real user is named; RFC 4231 vectors; the secret file is 0600
 *   secure files  the log secret and the ban file follow transport.c's secret_load(): a link at the file or at its temporary is refused
 *               and never written through, a foreign owner is refused, the 1.0's 0644 ban file is still read, the writing leaves no
 *               temporary, a world-writable directory without the sticky bit is refused
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE \
 *        -Wall -Wextra -Wno-unused-parameter -I/albero/src -I/albero/benches/fuzz/rcp-msg" &&
 *     clang $F -c /albero/benches/unit/login-ban/test.c -o t.o && clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *     clang -fsanitize=address,undefined t.o l.o -o test && ./test'
 * Exit code 0 = every check passed.
 */
/* geteuid() is interposed ONLY to let the test make a file look foreign when it runs as an ordinary user (as root it
 * chown()s the file instead): the files rcp.c trusts are those of root or of this uid. */
#include <sys/types.h>
#include <unistd.h>
static unsigned rxt_uid_shift;
static uid_t rxt_geteuid(void);
#define geteuid rxt_geteuid
#include "rcp.c"
#undef geteuid
static uid_t rxt_geteuid(void) { return geteuid() + rxt_uid_shift; }

#include <dirent.h>
#include <stdio.h>
#include <sys/stat.h>
#include "common.h"

static int checks, bad;

#define CHECK(cond, ...)                                                      \
	do {                                                                  \
		checks++;                                                     \
		if (!(cond)) {                                                \
			bad++;                                                \
			printf("  FAIL %s:%d  %s  -- ", __FILE__, __LINE__, #cond); \
			printf(__VA_ARGS__);                                  \
			printf("\n");                                         \
		}                                                             \
	} while (0)

static uint64_t at(double seconds) { return 1000000u + (uint64_t)(seconds * 1000.0); }

static void fresh(void) { rcp_reset_session_log(); ban_path[0] = 0; memset(good_keys, 0, sizeof good_keys); }

/* one complete attempt: book, then the verdict.  Returns what the booking said. */
static enum login_verdict attempt(const char *key, const char *user, bool ok, uint64_t now)
{
	struct login_info info;
	struct login_result r;
	enum login_verdict v = login_reserve(key, user, now, &info);
	if (v == LV_OK)
		login_resolve(key, user, ok, now, &r);
	return v;
}
static enum login_verdict fail(const char *key, const char *user, uint64_t now) { return attempt(key, user, false, now); }

static enum login_verdict peek(const char *key, const char *user, uint64_t now, struct login_info *info)
{
	struct login_info local;
	if (!info)
		info = &local;
	enum login_verdict v = login_reserve(key, user, now, info);
	if (v == LV_OK)
		login_release(key, user);
	return v;
}

static void key_of(const char *text, char *out) { rcp_key_address(text, out, 64); }
static int lfind_user(const char *key, const char *user) { char uk[65]; user_key(user, uk); return lfind(LK_USER, key, uk); }

/* ------------------------------------------------------------------------ */
static void test_keys(void)
{
	printf("keys\n");
	struct { const char *in, *want; } T[] = {
	    {"1.2.3.4", "[1.2.3.4]"},
	    {"[1.2.3.4]:555", "[1.2.3.4]"},
	    {"1.2.3.4:53", "[1.2.3.4]"},
	    {"2001:db8:1:2:3:4:5:6", "[2001:db8:1:2::]"},
	    {"[2001:db8:1:2:aaaa:bbbb:cccc:dddd]:443", "[2001:db8:1:2::]"},
	    {"fe80::1", "[fe80::]"},
	    {"[::ffff:1.2.3.4]:99", "[1.2.3.4]"},
	    {"::ffff:1.2.3.4", "[1.2.3.4]"},
	    {"64:ff9b::1.2.3.4", "[1.2.3.4]"},
	    {"::1", "[::1]"},
	    {"fe80::1%eth0", "[fe80::]"},
	    {"[fe80::abcd:1%enp3s0]:443", "[fe80::]"},
	    {"fe80::1%eth0%x", "[fe80::]"},
	    {"[::1]:7", "[::1]"},
	    {"   ", "[   ]"},
	    {"garbage", "[garbage]"},
	};
	for (size_t i = 0; i < sizeof T / sizeof *T; i++) {
		char k[64], k2[64];
		key_of(T[i].in, k);
		CHECK(strcmp(k, T[i].want) == 0, "«%s» -> «%s», wanted «%s»", T[i].in, k, T[i].want);
		key_of(k, k2);
		CHECK(strcmp(k, k2) == 0, "not idempotent: «%s» -> «%s» -> «%s»", T[i].in, k, k2);
	}
	char k48[64];
	CHECK(key_net48("[2001:db8:1:2::]", k48, sizeof k48) && strcmp(k48, "[2001:db8:1::]") == 0, "/48 of a /64 key: %s", k48);
	CHECK(!key_net48("[1.2.3.4]", k48, sizeof k48), "an IPv4 key has no /48");
	CHECK(!key_net48("[::1]", k48, sizeof k48), "loopback has no /48");
	CHECK(!key_net48("[garbage]", k48, sizeof k48), "a non-address has no /48");
}

/* ------------------------------------------------------------------------ */
static void test_thresholds(void)
{
	printf("thresholds\n");
	struct login_info info;
	const char *K = "[1.2.3.4]";

	/* (key,user): 4 do not ban, the 5th does; the ban is 15 minutes and is only on (key,user) */
	fresh();
	for (int i = 0; i < 4; i++)
		CHECK(fail(K, "alice", at(i)) == LV_OK, "attempt %d refused too early", i);
	CHECK(peek(K, "alice", at(5), NULL) == LV_OK, "4 failures must not ban");
	CHECK(fail(K, "alice", at(5)) == LV_OK, "the 5th is still asked to PAM");
	CHECK(peek(K, "alice", at(6), &info) == LV_BANNED && info.kind == LK_USER, "5th failure: (key,user) banned");
	CHECK(info.remain == 899000u, "remain %llu, wanted 899000 (15 min minus 1 s)", (unsigned long long)info.remain);
	CHECK(peek(K, "bob", at(6), NULL) == LV_OK, "another user on the same key is not banned (5 < 12)");
	CHECK(!rcp_banned(K, at(6), NULL), "rcp_banned (the page) does not know the user: not banned");
	CHECK(peek("[1.2.3.5]", "alice", at(6), NULL) == LV_OK, "another address is not banned");
	/* the ban ends at 15 min exactly */
	CHECK(peek(K, "alice", at(5 + 900) - 1, NULL) == LV_BANNED, "banned until the last ms");
	CHECK(peek(K, "alice", at(5 + 900), NULL) == LV_OK, "free at the 15th minute");

	/* the window is SLIDING: the failures at 0,90,180,270 and 301 -> the first has left (301 s > 300 s) */
	fresh();
	fail(K, "alice", at(0)); fail(K, "alice", at(90)); fail(K, "alice", at(180)); fail(K, "alice", at(270));
	fail(K, "alice", at(301));
	CHECK(peek(K, "alice", at(302), NULL) == LV_OK, "the failure at 0 has left the window: 4 inside, no ban");
	fail(K, "alice", at(302));
	CHECK(peek(K, "alice", at(303), NULL) == LV_BANNED, "90..302 are 5 inside 300 s: ban");
	/* the boundary is inclusive: exactly 300 s still counts as inside */
	fresh();
	fail(K, "alice", at(0)); fail(K, "alice", at(75)); fail(K, "alice", at(150)); fail(K, "alice", at(225));
	fail(K, "alice", at(300));
	CHECK(peek(K, "alice", at(301), NULL) == LV_BANNED, "0 and 300 s apart is inside the window (<=)");

	/* key: 12 failures from 12 different users in 5 minutes */
	fresh();
	char u[16];
	for (int i = 0; i < 11; i++) { snprintf(u, sizeof u, "user%d", i); fail(K, u, at(i)); }
	CHECK(peek(K, "someone", at(12), NULL) == LV_OK, "11 failures on the key: no ban");
	fail(K, "user11", at(12));
	CHECK(peek(K, "someone", at(13), &info) == LV_BANNED && info.kind == LK_KEY, "12th failure: the KEY is banned, any user");
	CHECK(rcp_banned(K, at(13), NULL), "rcp_banned says so (the page)");
	CHECK(peek("[1.2.3.9]", "someone", at(13), NULL) == LV_OK, "another IPv4 is free");
	/* 12 failures but slower than the window: 25 s apart -> the first has left when the 12th comes */
	fresh();
	for (int i = 0; i < 12; i++) { snprintf(u, sizeof u, "user%d", i); fail(K, u, at(i * 28)); }
	CHECK(!rcp_banned(K, at(12 * 28), NULL), "12 failures in 308 s: the first is out, no ban");

	/* /48: 30 failures from 30 different /64 of the same /48 (each /64 sees ONE failure), in 10 minutes */
	fresh();
	char a[64];
	for (int i = 0; i < 29; i++) {
		snprintf(a, sizeof a, "2001:db8:1:%x::5", i + 1);
		char kk[64]; key_of(a, kk);
		fail(kk, "alice", at(i * 10));
	}
	char fresh64[64]; key_of("2001:db8:1:ff::7", fresh64);
	CHECK(peek(fresh64, "alice", at(300), NULL) == LV_OK, "29 failures on the /48: no ban");
	char k30[64]; key_of("2001:db8:1:1e::5", k30);
	fail(k30, "alice", at(291));
	CHECK(peek(fresh64, "alice", at(300), &info) == LV_BANNED && info.kind == LK_NET48, "30th failure: the /48 is banned");
	CHECK(rcp_banned("2001:db8:1:abcd::1", at(300), NULL), "the page sees the /48 ban");
	char other[64]; key_of("2001:db8:2::1", other);
	CHECK(peek(other, "alice", at(300), NULL) == LV_OK, "another /48 is free");
	/* 30 failures slower than 10 minutes: 25 s apart -> the first is out when the 30th comes */
	fresh();
	for (int i = 0; i < 30; i++) {
		snprintf(a, sizeof a, "2001:db8:1:%x::5", i + 1);
		char kk[64]; key_of(a, kk);
		fail(kk, "alice", at(i * 25));
	}
	CHECK(!rcp_banned("2001:db8:1:ff::1", at(30 * 25), NULL), "30 failures in 725 s: no /48 ban");
}

/* ------------------------------------------------------------------------ */
static void ban_user(const char *key, const char *user, uint64_t t0)
{
	for (int i = 0; i < 5; i++)
		fail(key, user, t0 + (uint64_t)i * 1000u);
}

static void test_progression(void)
{
	printf("progression\n");
	const char *K = "[1.2.3.4]";
	struct login_info info;
	fresh();
	ban_user(K, "alice", at(0));                      /* ban 1: 15 min, until ~904 s */
	CHECK(peek(K, "alice", at(5), &info) == LV_BANNED && info.remain == 899000u, "ban 1 remain %llu", (unsigned long long)info.remain);
	uint64_t t = at(4 + 900 + 1);
	CHECK(peek(K, "alice", t, NULL) == LV_OK, "free after 15 min");
	ban_user(K, "alice", t);                          /* ban 2: 1 h */
	CHECK(peek(K, "alice", t + 5000, &info) == LV_BANNED && info.remain == 3600000u - 1000u, "ban 2 is 1 h: remain %llu", (unsigned long long)info.remain);
	t += 3600000u + 10000u;
	CHECK(peek(K, "alice", t, NULL) == LV_OK, "free after 1 h");
	ban_user(K, "alice", t);                          /* ban 3: 12 h */
	CHECK(peek(K, "alice", t + 5000, &info) == LV_BANNED && info.remain == 43200000u - 1000u, "ban 3 is 12 h: remain %llu", (unsigned long long)info.remain);
	CHECK(peek(K, "alice", t + 43200000u - 1u, NULL) == LV_BANNED, "banned for the whole 12 h");
	t += 43200000u + 10000u;
	CHECK(peek(K, "alice", t, NULL) == LV_OK, "free after 12 h");
	ban_user(K, "alice", t);                          /* ban 4: still 12 h, the ladder ends there */
	CHECK(peek(K, "alice", t + 5000, &info) == LV_BANNED && info.remain == 43200000u - 1000u, "ban 4 stays 12 h: remain %llu", (unsigned long long)info.remain);

	/* forgotten after 24 h WITHOUT a ban (counted from the end of the last ban) */
	fresh();
	ban_user(K, "alice", at(0));                      /* ban 1, ends at 904 s */
	t = at(904) + 1;
	ban_user(K, "alice", t);                          /* ban 2 (1 h), ends t+4000+3600000... */
	uint64_t end2 = t + 4000u + 3600000u;
	/* 23 h after the end: NOT forgotten -> the next one is the 12 h */
	uint64_t t23 = end2 + 23u * 3600000u;
	ban_user(K, "alice", t23);
	CHECK(peek(K, "alice", t23 + 5000, &info) == LV_BANNED && info.remain == 43200000u - 1000u, "23 h after: not forgotten, 12 h");
	/* now the other branch, from scratch: 25 h after the end -> forgotten, back to 15 min */
	fresh();
	ban_user(K, "alice", at(0));
	t = at(904) + 1;
	ban_user(K, "alice", t);
	end2 = t + 4000u + 3600000u;
	uint64_t t25 = end2 + 25u * 3600000u;
	ban_user(K, "alice", t25);
	CHECK(peek(K, "alice", t25 + 5000, &info) == LV_BANNED && info.remain == 900000u - 1000u, "25 h after: forgotten, 15 min again (remain %llu)", (unsigned long long)info.remain);
	/* the rungs are per level: the KEY has its own ladder */
	fresh();
	char u[16];
	for (int i = 0; i < 12; i++) { snprintf(u, sizeof u, "u%d", i); fail(K, u, at(i)); }
	CHECK(peek(K, "x", at(13), &info) == LV_BANNED && info.kind == LK_KEY && info.remain == 900000u - 2000u, "key ban 1 is 15 min");
	t = at(11) + 900000u + 1000u;
	for (int i = 0; i < 12; i++) { snprintf(u, sizeof u, "v%d", i); fail(K, u, t + (uint64_t)i * 1000u); }
	CHECK(peek(K, "x", t + 13000u, &info) == LV_BANNED && info.kind == LK_KEY && info.remain == 3600000u - 2000u, "key ban 2 is 1 h (remain %llu)", (unsigned long long)info.remain);
}

/* ------------------------------------------------------------------------ */
static void test_reset(void)
{
	printf("reset\n");
	const char *K = "[1.2.3.4]";
	struct login_info info;
	fresh();
	for (int i = 0; i < 4; i++) fail(K, "alice", at(i));
	attempt(K, "alice", true, at(5));                 /* success: the 4 go back to zero */
	for (int i = 0; i < 4; i++) fail(K, "alice", at(10 + i));
	CHECK(peek(K, "alice", at(20), NULL) == LV_OK, "success reset (key,user): 4+4 failures do not ban");
	/* ...but NOT the key's count: 8 failures of alice so far, 4 more from 4 other users make 12 */
	for (int i = 0; i < 3; i++) { char u[8]; snprintf(u, sizeof u, "o%d", i); fail(K, u, at(21 + i)); }
	CHECK(peek(K, "z", at(25), NULL) == LV_OK, "11 on the key");
	fail(K, "o3", at(26));
	CHECK(peek(K, "z", at(27), &info) == LV_BANNED && info.kind == LK_KEY, "the key counted 12 although alice succeeded in between");

	/* another user's success does not reset alice */
	fresh();
	for (int i = 0; i < 4; i++) fail(K, "alice", at(i));
	attempt(K, "bob", true, at(5));
	fail(K, "alice", at(6));
	CHECK(peek(K, "alice", at(7), NULL) == LV_BANNED, "bob's success must not reset alice");

	/* the success does not reset the recidivism: after a ban 1 the next is 1 h even with a login in between */
	fresh();
	ban_user(K, "alice", at(0));
	uint64_t t = at(4 + 901);
	attempt(K, "alice", true, t);
	ban_user(K, "alice", t + 1000u);
	CHECK(peek(K, "alice", t + 6000u, &info) == LV_BANNED && info.remain == 3600000u - 1000u, "recidivism survives the success: 1 h (remain %llu)", (unsigned long long)info.remain);

	/* and the success does not reset the /48: 29 failures on the /48, a success, one more -> banned */
	fresh();
	char a[64], kk[64];
	for (int i = 0; i < 29; i++) { snprintf(a, sizeof a, "2001:db8:1:%x::5", i + 1); key_of(a, kk); fail(kk, "alice", at(i)); }
	key_of("2001:db8:1:1::5", kk);
	attempt(kk, "alice", true, at(30));
	key_of("2001:db8:1:77::5", kk);
	fail(kk, "alice", at(31));
	CHECK(rcp_banned("2001:db8:1:1::9", at(32), NULL), "a success does not wash the /48's count");
}

/* ------------------------------------------------------------------------ */
static void test_rotation(void)
{
	printf("rotation\n");
	fresh();
	char k[64];
	/* five different addresses of the same /64, one failure each, same user */
	const char *same64[] = {"2001:db8:1:2::1", "2001:db8:1:2:aaaa::2", "2001:db8:1:2:1:2:3:4", "2001:db8:1:2:ffff:ffff:ffff:ffff",
	                        "[2001:db8:1:2:5::5]:4433"};
	for (int i = 0; i < 5; i++) { key_of(same64[i], k); fail(k, "alice", at(i)); }
	key_of("2001:db8:1:2:9::9", k);
	CHECK(peek(k, "alice", at(6), NULL) == LV_BANNED, "five addresses of ONE /64 are one key: banned at the 5th");
	key_of("2001:db8:1:3::1", k);
	CHECK(peek(k, "alice", at(6), NULL) == LV_OK, "another /64 is another key");
	/* the same rotation with 12 users: the key bans */
	fresh();
	for (int i = 0; i < 12; i++) {
		char addr[64], u[8]; snprintf(addr, sizeof addr, "2001:db8:1:2:%x::1", i + 1); snprintf(u, sizeof u, "u%d", i);
		key_of(addr, k); fail(k, u, at(i));
	}
	CHECK(rcp_banned("2001:db8:1:2:dead:beef::1", at(13), NULL), "rotation inside a /64 with 12 users: the key is banned");
	CHECK(!rcp_banned("2001:db8:1:3::1", at(13), NULL), "the neighbour /64 is not");
	/* IPv4 is NOT aggregated: neighbours are different keys */
	fresh();
	for (int i = 0; i < 5; i++) { char addr[16]; snprintf(addr, sizeof addr, "10.0.0.%d", i + 1); key_of(addr, k); fail(k, "alice", at(i)); }
	CHECK(peek("[10.0.0.9]", "alice", at(6), NULL) == LV_OK, "IPv4 is counted whole: 5 different addresses are not one");
}

/* ------------------------------------------------------------------------ */
static void test_in_flight(void)
{
	printf("in flight\n");
	const char *K = "[1.2.3.4]";
	struct login_info info;
	struct login_result r;
	fresh();
	/* a burst of ten connections sent together: only two get to PAM */
	int ok = 0;
	for (int i = 0; i < 10; i++)
		if (login_reserve(K, "alice", at(0), &info) == LV_OK)
			ok++;
	CHECK(ok == 2, "burst of 10: %d asked to PAM, wanted 2", ok);
	CHECK(login_reserve(K, "alice", at(0), &info) == LV_BUSY && info.kind == LK_USER, "the 3rd is BUSY on the user");
	CHECK(login_reserve(K, "bob", at(0), &info) == LV_OK, "another user on the same key is still allowed");
	/* the refusals counted nothing: two failures + the verdicts leave 2 failures, not 10 */
	login_resolve(K, "alice", false, at(1), &r);
	CHECK(r.inside[LK_USER] == 1, "first verdict: 1 failure");
	login_resolve(K, "alice", false, at(1), &r);
	CHECK(r.inside[LK_USER] == 2, "second verdict: 2 failures (the 8 refusals counted nothing)");
	login_resolve(K, "bob", true, at(1), &r);
	CHECK(peek(K, "alice", at(2), NULL) == LV_OK, "in flight given back: asking again is allowed");

	/* failed + in flight at the limit: 3 failed + 2 in flight = 5 -> the next is refused, and is not a failure */
	fresh();
	for (int i = 0; i < 3; i++) fail(K, "alice", at(i));
	CHECK(login_reserve(K, "alice", at(4), &info) == LV_OK, "3 failed + 1 in flight");
	CHECK(login_reserve(K, "alice", at(4), &info) == LV_OK, "3 failed + 2 in flight");
	CHECK(login_reserve(K, "alice", at(4), &info) == LV_BUSY, "3 + 2 = 5 = the limit: refused");
	login_resolve(K, "alice", false, at(5), &r);
	CHECK(r.inside[LK_USER] == 4 && !r.banned[LK_USER], "4th failure: no ban yet");
	CHECK(login_reserve(K, "alice", at(5), &info) == LV_BUSY, "4 failed + 1 in flight = 5: refused");
	login_resolve(K, "alice", false, at(6), &r);
	CHECK(r.inside[LK_USER] == 5 && r.banned[LK_USER] && r.ban_ms[LK_USER] == 900000u, "5th failure bans for 15 min");
	CHECK(peek(K, "alice", at(7), NULL) == LV_BANNED, "banned");

	/* the key level: 11 failures of 11 users + 1 in flight -> another user is refused (11 + 1 = 12) */
	fresh();
	char u[8];
	for (int i = 0; i < 11; i++) { snprintf(u, sizeof u, "u%d", i); fail(K, u, at(i)); }
	CHECK(login_reserve(K, "x", at(12), &info) == LV_OK, "11 failed + 1 in flight");
	CHECK(login_reserve(K, "y", at(12), &info) == LV_BUSY && info.kind == LK_KEY, "12 = limit of the key: refused on the KEY level");
	login_release(K, "x");
	CHECK(login_reserve(K, "y", at(12), &info) == LV_OK, "released: allowed again");

	/* the question did not leave: login_release counts nothing */
	fresh();
	login_reserve(K, "alice", at(0), &info);
	login_reserve(K, "alice", at(0), &info);
	login_release(K, "alice");
	login_release(K, "alice");
	login_release(K, "alice"); /* a release too many must not go below zero */
	int n = 0;
	for (int i = 0; i < 4; i++) if (login_reserve(K, "alice", at(1), &info) == LV_OK) n++;
	CHECK(n == 2, "release brings it back to zero (and never below): %d", n);
	for (int i = 0; i < 4; i++) { login_resolve(K, "alice", false, at(2), &r); }
	/* four verdicts on two bookings: in_flight stays at 0, failures are 4 */
	CHECK(r.inside[LK_USER] == 4, "failures %d", r.inside[LK_USER]);

	/* a ban that fires while the other booking is still in flight: the late verdict adds nothing */
	fresh();
	for (int i = 0; i < 3; i++) fail(K, "alice", at(i));
	login_reserve(K, "alice", at(3), &info);
	login_reserve(K, "alice", at(3), &info);
	login_resolve(K, "alice", false, at(4), &r);
	login_resolve(K, "alice", false, at(5), &r);
	CHECK(r.banned[LK_USER], "banned by the 2nd verdict");
	CHECK(peek(K, "alice", at(6), NULL) == LV_BANNED, "banned");
}

/* ------------------------------------------------------------------------ */
static char captured[8192];
static void capture(void *ctx, const char *line)
{
	(void)ctx;
	size_t n = strlen(captured);
	snprintf(captured + n, sizeof captured - n, "%s\n", line);
}

static void test_orphan(void)
{
	printf("orphan\n");
	const char *K = "[1.2.3.4]";
	struct login_info info;
	fresh();
	captured[0] = 0;
	/* five connections book and close: the five true verdicts arrive with no session */
	for (int i = 0; i < 5; i++) {
		CHECK(login_reserve(K, "alice", at(i), &info) == LV_OK, "booking %d", i);
		rcp_orphan_verdict("alice", "1.2.3.4", false, false, 0, at(i) + 1500u, capture, NULL);
	}
	CHECK(peek(K, "alice", at(8), NULL) == LV_BANNED, "five orphan failures ban (key,user)");
	CHECK(strstr(captured, "BANNED") != NULL, "the ban is written to the sink: %s", captured);
	CHECK(strstr(captured, "gone") != NULL, "the sink says the connection was gone");

	/* a success of a connection already gone gives the booking back and resets (key,user) */
	fresh();
	for (int i = 0; i < 4; i++) fail(K, "alice", at(i));
	login_reserve(K, "alice", at(5), &info);
	rcp_orphan_verdict("alice", "1.2.3.4", true, false, 0, at(6), capture, NULL);
	for (int i = 0; i < 4; i++) fail(K, "alice", at(10 + i));
	CHECK(peek(K, "alice", at(20), NULL) == LV_OK, "orphan success reset (key,user)");
	int n = 0;
	for (int i = 0; i < 4; i++) if (login_reserve(K, "alice", at(21), &info) == LV_OK) n++;
	CHECK(n == 1, "4 failed + 1 in flight = 5: one booking allowed, so the orphan verdict left none in flight (%d)", n);

	/* IPv6: the rhost of the flight record is the bare address; it must reach the SAME key as the session's */
	fresh();
	char k[64];
	key_of("[2001:db8:1:2:3:4:5:6]:4433", k);                   /* what the session has */
	for (int i = 0; i < 5; i++) {
		login_reserve(k, "alice", at(i), &info);
		rcp_orphan_verdict("alice", "2001:db8:1:2:9:9:9:9", false, false, 0, at(i), capture, NULL);
	}
	CHECK(peek(k, "alice", at(6), NULL) == LV_BANNED, "orphan IPv6 lands on the session's /64 key");
	/* IPv4 mapped in IPv6 (the dual-stack socket): rhost has already lost the ::ffff:, either form gives one key */
	fresh();
	key_of("[::ffff:5.6.7.8]:1", k);
	CHECK(strcmp(k, "[5.6.7.8]") == 0, "mapped: %s", k);

	/* no name or no address: nothing is counted and it is said */
	captured[0] = 0;
	rcp_orphan_verdict("", "1.2.3.4", false, false, 0, at(0), capture, NULL);
	rcp_orphan_verdict("alice", NULL, false, false, 0, at(0), capture, NULL);
	CHECK(strstr(captured, "NOT counted") != NULL, "unknown name/address is said");
}

/* ------------------------------------------------------------------------ */
static void test_table(void)
{
	printf("table\n");
	struct login_info info;
	struct login_result r;
	fresh();
	/* full of BOOKINGS: 128 keys x (user + key) = 256 entries, all in flight */
	char k[64];
	for (int i = 0; i < 128; i++) {
		snprintf(k, sizeof k, "[10.1.%d.%d]", i / 200, i % 200 + 1);
		CHECK(login_reserve(k, "u", at(0), &info) == LV_OK, "booking %d", i);
	}
	unsigned before = login_refused_full;
	CHECK(login_reserve("[9.9.9.9]", "u", at(1), &info) == LV_FULL, "129th key: table full, refused");
	CHECK(login_refused_full == before + 1, "the refusal is COUNTED (%u -> %u)", before, login_refused_full);
	CHECK(lfind(LK_KEY, "[10.1.0.1]", NULL) >= 0, "no booking was thrown away");
	/* one resolves: its two entries are now evictable */
	login_resolve("[10.1.0.1]", "u", true, at(2), &r);
	CHECK(login_reserve("[9.9.9.9]", "u", at(3), &info) == LV_OK, "room again once a booking is resolved");

	/* OVER THE QUOTA (written by hand: the ban sites keep the quota, so this is a file loaded with more, a constant lowered, a bug
	 * to come): the table repairs itself — the new key gets in and the least valuable ban (the nearest to its expiry) is dropped */
	fresh();
	for (int i = 0; i < MAX_ATTEMPTS; i++) {
		snprintf(k, sizeof k, "[10.2.%d.%d]", i / 200, i % 200 + 1);
		int s = lcreate(LK_KEY, k, NULL, at(0), NULL, NULL, 0, NULL, 0, false);
		CHECK(s == i, "slot %d", s);
		attempts[s].banned_until = at(3600 + i);
		attempts[s].level = 1;
	}
	before = login_refused_full;
	unsigned dropped0 = login_bans_dropped;
	CHECK(login_reserve("[9.9.9.9]", "u", at(1), &info) == LV_FULL, "over the quota, an UNKNOWN key finds no place: LV_FULL (the last resort is for known keys)");
	CHECK(login_refused_full == before + 1 && login_bans_dropped == dropped0 && info.dropped[0] == 0, "counted, and no ban dropped");
	good_put("[9.9.9.9]", NULL, at(0), (long long)time(NULL));
	CHECK(login_reserve("[9.9.9.9]", "u", at(1), &info) == LV_OK, "the same key once KNOWN gets in");
	CHECK(login_bans_dropped == dropped0 + 2 && strncmp(info.dropped, "BAN of", 6) == 0 &&
	      strstr(info.dropped + 6, "BAN of") != NULL,
	      "one ban dropped for each entry the key needs (user and key), BOTH named: «%s»", info.dropped);
	CHECK(lfind(LK_KEY, "[10.2.0.1]", NULL) < 0 && lfind(LK_KEY, "[10.2.0.2]", NULL) < 0, "the ones dropped are the nearest to their expiry");
	CHECK(lfind(LK_KEY, "[10.2.1.56]", NULL) >= 0 && peek("[10.2.1.56]", "u", at(2), NULL) == LV_BANNED, "and the last ban still bans");
	login_release("[9.9.9.9]", "u");
	memset(good_keys, 0, sizeof good_keys);

	/* full of FAILURES (not banned): the oldest is evicted, and it is declared */
	fresh();
	for (int i = 0; i < 128; i++) {
		snprintf(k, sizeof k, "[10.3.%d.%d]", i / 200, i % 200 + 1);
		fail(k, "u", at(i));
	}
	CHECK(login_reserve("[9.9.9.9]", "u", at(200), &info) == LV_OK, "a failed-only table makes room");
	CHECK(info.evicted[0] != 0, "and says what it threw away: «%s»", info.evicted);
	/* reclaiming entries with nothing to remember is silent: all the failures are older than 5 min */
	fresh();
	for (int i = 0; i < 128; i++) {
		snprintf(k, sizeof k, "[10.4.%d.%d]", i / 200, i % 200 + 1);
		fail(k, "u", at(0));
	}
	CHECK(login_reserve("[9.9.9.9]", "u", at(1000), &info) == LV_OK && info.evicted[0] == 0, "idle entries are reclaimed silently");
}

/* ------------------------------------------------------------------------ */
/* R1 of the audit of 25 Oct 2026: the table can never be all bans. */

static int banned_now(uint64_t now)
{
	int n = 0;
	for (int i = 0; i < MAX_ATTEMPTS; i++)
		if (attempts[i].used && is_banned(&attempts[i], now))
			n++;
	return n;
}

/* an address that fails its way to THREE banned entries (the most one address can get): user "a" 5 times, user "b" 5 times,
 * user "c" twice = 12 failures of the key.  Returns the failures spent. */
static int burn(const char *key, uint64_t t)
{
	int spent = 0;
	for (int i = 0; i < 5; i++, spent++) fail(key, "a", t + (uint64_t)i);
	for (int i = 0; i < 5; i++, spent++) fail(key, "b", t + 10u + (uint64_t)i);
	for (int i = 0; i < 2; i++, spent++) fail(key, "c", t + 20u + (uint64_t)i);
	return spent;
}

static void v4(char *out, int n) { snprintf(out, 64, "[10.%d.%d.%d]", 100 + n / 65000, (n / 250) % 250, n % 250 + 1); }

static char *slurp(const char *path);

/* a botnet of `n` addresses that burn 12 failures each, in turns, every `period` s from `from` to `to` (seconds) */
static void botnet(int n, double from, double to, double period)
{
	char k[64];
	for (double t = from; t < to; t += period)
		for (int i = 0; i < n; i++) {
			v4(k, i);
			burn(k, at(t + i * 0.01));
		}
}

struct fline { int i, level; long long exp; };
static int fline_cmp(const void *a, const void *b)   /* the most valuable first: level, then the farthest expiry */
{
	const struct fline *x = a, *y = b;
	if (x->level != y->level) return y->level - x->level;
	return x->exp < y->exp ? 1 : x->exp > y->exp ? -1 : 0;
}

static void test_quota(void)
{
	printf("quota\n");
	struct login_info info;
	char k[64];

	/* 1. a botnet of 300 addresses taking turns for 14 minutes: the quota holds, NOTHING is dropped, the first ban is still there
	 *    (the first version dropped it after ~90 s and with it the recidivism), and the server is never locked out */
	fresh();
	const char *G = "[198.51.100.9]";
	CHECK(attempt(G, "alice", true, at(0)) == LV_OK, "the owner logs in from G (a known key)");
	botnet(300, 1, 14 * 60, 10);
	int nbn = banned_now(at(14 * 60));
	CHECK(nbn >= BAN_QUOTA && nbn <= BAN_QUOTA + 4, "the bans settle at the quota (%d, quota %d)", nbn, BAN_QUOTA);
	CHECK(login_bans_dropped == 0, "NO ban was dropped by 14 minutes of botnet (%u)", login_bans_dropped);
	char A[64];
	v4(A, 0);
	CHECK(peek(A, "a", at(14 * 60), NULL) == LV_BANNED, "the very first ban is still in force after 14 minutes");
	CHECK(login_refused_quota > 0, "and the unknown keys were refused at the quota (%u)", login_refused_quota);
	CHECK(login_refused_full == 0, "never because of a full table (%u)", login_refused_full);
	/* the owner is always in, and a ban of his own is given even over the quota without dropping another */
	CHECK(peek(G, "alice", at(14 * 60), &info) == LV_OK, "the owner (known key) gets in while the botnet holds the quota");
	CHECK(peek(G, "carol", at(14 * 60), &info) == LV_OK, "also with a name the table has never seen");
	int nb0 = banned_now(at(14 * 60 + 1));
	for (int i = 0; i < 5; i++) fail(G, "alice", at(14 * 60 + 1 + i));
	CHECK(peek(G, "alice", at(14 * 60 + 10), NULL) == LV_BANNED && banned_now(at(14 * 60 + 10)) == nb0 + 1,
	      "five wrong passwords by the owner: his ban (user on this address) is given (%d -> %d)", nb0, banned_now(at(14 * 60 + 10)));
	CHECK(login_bans_dropped == 0, "...and it dropped nobody");
	/* the ladder climbs: when the bans end the botnet comes back and its entries are still there, one step up */
	botnet(300, 16 * 60, 16 * 60 + 1, 10);
	int ia = lfind(LK_KEY, A, NULL);
	CHECK(ia >= 0 && attempts[ia].level == 2, "A is at level 2 the second time (%d)", ia >= 0 ? (int)attempts[ia].level : -1);
	info.remain = 0;
	CHECK(peek(A, "a", at(16 * 60 + 5), &info) == LV_BANNED && info.remain > 50 * 60 * 1000u, "and banned for 1 hour (%llu ms)", (unsigned long long)info.remain);

	/* 2. 54 addresses (the botnet of the review): 3 bans each = 162 > the quota; the ladder reaches the 1 h step for ALL of them */
	fresh();
	botnet(54, 0, 1, 10);
	CHECK(banned_now(at(2)) >= BAN_QUOTA - 2 && banned_now(at(2)) <= BAN_QUOTA + 4, "54 addresses: bans %d", banned_now(at(2)));
	for (int t = 20; t < 15 * 60; t += 20)
		botnet(54, t, t + 1, 10);                       /* they go on every 20 s */
	CHECK(login_bans_dropped == 0, "no ban dropped in 15 minutes (it was ~90 s before)");
	botnet(54, 16 * 60, 16 * 60 + 1, 10);
	int up = 0;
	for (int i = 0; i < 54; i++) {
		v4(k, i);
		int ik = lfind(LK_KEY, k, NULL);
		if (ik >= 0 && attempts[ik].level == 2 && is_banned(&attempts[ik], at(16 * 60 + 5))) up++;
	}
	CHECK(up >= 50, "the ladder climbed to the 1-hour step for the addresses of the botnet (%d of 54)", up);

	/* 3. the unknown keys at the quota: a COMMON counter of UNKNOWN_LIMIT failures in UNKNOWN_WINDOW_MS, over it 0x08 */
	fresh();
	attempt(G, "alice", true, at(0));
	botnet(54, 1, 2, 10);                                    /* the quota is full; bans last until ~15 min */
	CHECK(banned_now(at(3)) >= BAN_QUOTA, "the quota is full (%d)", banned_now(at(3)));
	/* the botnet itself has probably used the counter: start from a quiet moment (>5 min after) */
	double t0 = 400;
	int used = 0, refused_at = -1;
	for (int i = 0; i < 20; i++) {
		snprintf(k, sizeof k, "[203.0.113.%d]", i + 1);
		enum login_verdict v = peek(k, "u", at(t0 + i), NULL);
		if (v == LV_QUOTA) { refused_at = i; break; }
		CHECK(v == LV_OK, "unknown key %d before the limit: PAM is asked (%d)", i, (int)v);
		fail(k, "u", at(t0 + i));
		used++;
	}
	CHECK(refused_at == UNKNOWN_LIMIT, "the %dth unknown key is refused after %d failures (it was %d)", UNKNOWN_LIMIT + 1, UNKNOWN_LIMIT, refused_at);
	int nuse = 0;
	for (int i = 0; i < MAX_ATTEMPTS; i++) nuse += attempts[i].used;
	unsigned rq = login_refused_quota, rf = login_refused_full;
	snprintf(k, sizeof k, "[203.0.113.99]");
	CHECK(login_reserve(k, "bob", at(t0 + 30), &info) == LV_QUOTA, "an unknown key is refused (LV_QUOTA)");
	int nuse2 = 0;
	for (int i = 0; i < MAX_ATTEMPTS; i++) nuse2 += attempts[i].used;
	CHECK(nuse2 == nuse && lfind(LK_KEY, k, NULL) < 0, "nothing was created and nothing evicted (%d entries)", nuse2);
	CHECK(login_refused_quota == rq + 1 && login_refused_full == rf, "counted as a quota refusal, not as a full table");
	CHECK(login_bans_dropped == 0 && info.dropped[0] == 0 && info.evicted[0] == 0, "no ban dropped, nothing said");
	CHECK(peek(G, "alice", at(t0 + 31), NULL) == LV_OK, "the known key is not refused");
	CHECK(peek(k, "bob", at(t0 + 298), NULL) == LV_QUOTA, "still refused inside the window");
	CHECK(peek(k, "bob", at(t0 + 305), NULL) == LV_OK, "the counter went down (5 min after the failures): asked again, though the quota is still full (%d)", banned_now(at(t0 + 305)));
	/* below the quota the counter is not used at all */
	fresh();
	for (int i = 0; i < 20; i++) {
		snprintf(k, sizeof k, "[203.0.113.%d]", i + 1);
		CHECK(attempt(k, "u", false, at(i)) == LV_OK, "below the quota every unknown key is asked (%d)", i);
	}
	CHECK(login_refused_quota == 0, "no refusal at all");

	/* 4. attempts and failures BELOW a ban erase no ban, however many keys they come from */
	fresh();
	botnet(60, 1, 2, 10);
	int before_set[MAX_ATTEMPTS], nb = 0;
	for (int i = 0; i < MAX_ATTEMPTS; i++)
		if (attempts[i].used && is_banned(&attempts[i], at(9))) before_set[nb++] = i;
	for (int i = 0; i < 4000; i++) {
		snprintf(k, sizeof k, "[172.16.%d.%d]", i / 250, i % 250 + 1);
		if (i % 2) peek(k, "x", at(10 + i * 0.001), NULL);
		else fail(k, "x", at(10 + i * 0.001));
	}
	int still = 0;
	for (int j = 0; j < nb; j++) if (is_banned(&attempts[before_set[j]], at(20))) still++;
	CHECK(still == nb, "4000 keys of attempts and single failures erased no ban (%d of %d)", still, nb);
	CHECK(login_bans_dropped == 0, "and dropped none");

	/* 5. 16 bookings + a full quota: the known key always, and no unknown key ever gets LV_FULL */
	fresh();
	attempt(G, "alice", true, at(0));
	botnet(60, 10, 11, 10);
	for (int i = 0; i < BOOKINGS_MAX; i++) {
		snprintf(k, sizeof k, "[10.200.0.%d]", i + 1);
		CHECK(login_reserve(k, "u", at(20), &info) != LV_FULL, "booking %d", i);
	}
	CHECK(login_reserve("[203.0.113.99]", "bob", at(21), &info) != LV_FULL, "16 bookings + full quota: an unknown key never gets LV_FULL");
	CHECK(login_reserve(G, "alice", at(22), &info) == LV_OK, "and the known one gets in");
	login_release(G, "alice");
	/* PATHOLOGICAL (not reachable: the helper holds 16): every non-ban entry pinned by a booking.  The known key drops the
	 * least valuable ban as a last resort and gets in; the log names it */
	fresh();
	attempt(G, "alice", true, at(0));
	botnet(60, 10, 11, 10);
	int pinned = 0;
	for (int i = 0; pinned < MAX_ATTEMPTS - BAN_QUOTA - 4; i++) {
		snprintf(k, sizeof k, "[10.201.%d.%d]", i / 250, i % 250 + 1);
		if (login_reserve(k, "u", at(30), &info) == LV_OK) pinned += 2;
		else break;
	}
	CHECK(login_reserve(G, "alice", at(32), &info) == LV_OK, "the known key is never LV_FULL");
	login_release(G, "alice");

	/* 6. the log names EVERY ban dropped in one outcome */
	fresh();
	captured[0] = 0;
	{
		struct sink sk = {NULL, capture, NULL};
		struct login_result rr;
		memset(&rr, 0, sizeof rr);
		say_append(rr.dropped, sizeof rr.dropped, "BAN of the address [1.2.3.4] (level 1, 3 s left)");
		say_append(rr.dropped, sizeof rr.dropped, "BAN of the address [5.6.7.8] (level 1, 9 s left)");
		say_append(rr.dropped, sizeof rr.dropped, "BAN of the address [9.9.9.9] (level 2, 40 s left)");
		login_report(&sk, "[1.2.3.4]", "alice", false, &rr, at(1));
	}
	CHECK(strstr(captured, "[1.2.3.4]") && strstr(captured, "[5.6.7.8]") && strstr(captured, "[9.9.9.9]"),
	      "the line names all three bans: %s", captured);

	/* 6b. the attempts IN FLIGHT count in the common counter, as LV_BUSY does */
	fresh();
	botnet(54, 1, 2, 10);
	double u0 = 400;                                        /* the botnet's own failures have left the window */
	int okb = 0;
	for (int i = 0; i < 12; i++) {
		snprintf(k, sizeof k, "[203.0.114.%d]", i + 1);
		if (login_reserve(k, "u", at(u0), &info) == LV_OK) okb++;
	}
	CHECK(okb == UNKNOWN_LIMIT, "12 unknown bookings at once: only %d pass (%d)", UNKNOWN_LIMIT, okb);
	CHECK(unknown_flights() == UNKNOWN_LIMIT, "and they are counted in flight (%d)", unknown_flights());
	snprintf(k, sizeof k, "[203.0.114.1]");
	login_release(k, "u");
	CHECK(unknown_flights() == UNKNOWN_LIMIT - 1, "a booking given back frees its place (%d)", unknown_flights());
	snprintf(k, sizeof k, "[203.0.114.2]");
	{
		struct login_result rr;
		login_resolve(k, "u", false, at(u0 + 1), &rr);
	}
	CHECK(unknown_flights() == UNKNOWN_LIMIT - 2 && unknown_inside(at(u0 + 1)) == 1, "a failure turns its place in flight into one in the window (%d, %d)",
	      unknown_flights(), unknown_inside(at(u0 + 1)));
	snprintf(k, sizeof k, "[203.0.114.77]");
	CHECK(login_reserve(k, "u", at(u0 + 2), &info) == LV_OK, "the freed place is used by another key");
	CHECK(login_reserve("[203.0.114.78]", "u", at(u0 + 2), &info) == LV_QUOTA, "and then it is full again");
	/* UNBLOCK zeroes the common counter (not the bookings) */
	fresh();
	botnet(54, 1, 2, 10);
	for (int i = 0; i < UNKNOWN_LIMIT; i++) {
		snprintf(k, sizeof k, "[203.0.115.%d]", i + 1);
		fail(k, "u", at(400 + i));
	}
	CHECK(peek("[203.0.115.99]", "u", at(410), NULL) == LV_QUOTA, "the common counter is full");
	rcp_unblock("[8.8.8.8]", at(411));
	CHECK(unknown_inside(at(411)) == 0 && peek("[203.0.115.99]", "u", at(411), NULL) == LV_OK, "UNBLOCK zeroed it");

	/* 6c. the known keys on disk: a restart with the quota full does not refuse the owner */
	{
		char d2[] = "/tmp/lg-good-XXXXXX";
		CHECK(mkdtemp(d2) != NULL, "mkdtemp");
		char p2[128];
		snprintf(p2, sizeof p2, "%s/ban", d2);
		fresh();
		memset(good_keys, 0, sizeof good_keys);
		CHECK(rcp_ban_load(p2, at(0)) == 0, "no file yet");
		struct login_result rr;
		login_reserve(G, "alice", at(1), &info);
		login_resolve(G, "alice", true, at(1), &rr);
		CHECK(rr.good_changed, "a new known key says the file must be rewritten");
		login_reserve(G, "alice", at(2), &info);
		login_resolve(G, "alice", true, at(2), &rr);
		CHECK(!rr.good_changed, "...and not again within the day");
		botnet(54, 3, 4, 10);
		save_ban(NULL, at(5));
		char *txt = slurp(p2);
		CHECK(strstr(txt, "\nG2 ") != NULL && strstr(txt, G) != NULL, "the file has a G2 line for the owner");
		/* the 1.0 loader skips it: its test is «<word> <number>» with the number in the future */
		int old_loads = 0;
		{
			char lines[32768];
			snprintf(lines, sizeof lines, "%s", txt);
			for (char *ln = strtok(lines, "\n"); ln; ln = strtok(NULL, "\n")) {
				char addr[64];
				long long ex = 0;
				if (strncmp(ln, "G2 ", 3) == 0 && sscanf(ln, "%63s %lld", addr, &ex) == 2 && ex > (long long)time(NULL))
					old_loads++;
			}
		}
		CHECK(old_loads == 0, "the 1.0 reads no G2 line as a ban (%d)", old_loads);
		struct stat sb;
		CHECK(stat(p2, &sb) == 0 && (sb.st_mode & 0777) == 0600, "file mode 0600");
		/* RESTART: nothing in memory but the file */
		fresh();
		memset(good_keys, 0, sizeof good_keys);
		CHECK(!good_recent(G, at(10)), "a restart forgets the known keys...");
		int nl = rcp_ban_load(p2, at(10));
		CHECK(nl >= BAN_QUOTA - 3 && good_recent(G, at(10)), "...and the file brings them back (%d bans loaded)", nl);
		for (int i = 0; i < UNKNOWN_LIMIT; i++) {
			snprintf(k, sizeof k, "[203.0.116.%d]", i + 1);
			fail(k, "u", at(11 + i));
		}
		CHECK(peek("[203.0.116.99]", "u", at(20), NULL) == LV_QUOTA, "after the restart the unknown keys meet the quota...");
		CHECK(peek(G, "alice", at(20), NULL) == LV_OK, "...and the owner gets in");
		/* a stale, a future and a nonsense line are not read */
		FILE *f2 = fopen(p2, "w");
		long long nowe = (long long)time(NULL);
		fprintf(f2, "G2 %lld [1.1.1.1]\nG2 %lld [2.2.2.2]\nG2 nonsense [3.3.3.3]\nG2 %lld [4.4.4.4]\n", nowe - 40 * 86400, nowe + 1000, nowe - 3600);
		fclose(f2);
		fresh();
		memset(good_keys, 0, sizeof good_keys);
		CHECK(rcp_ban_load(p2, at(0)) == 0, "G2 lines are not bans");
		CHECK(!good_recent("[1.1.1.1]", at(1)) && !good_recent("[3.3.3.3]", at(1)) &&
		      good_recent("[4.4.4.4]", at(1)), "the stale line and the nonsense are not read, the one of an hour ago is");
		/* a line from the FUTURE (the clock was wrong) is read as recent, with its date brought back to now */
		{
			int g22 = good_find("[2.2.2.2]");
			CHECK(good_recent("[2.2.2.2]", at(1)) && g22 >= 0 && good_keys[g22].epoch <= (long long)time(NULL),
			      "a login dated in the future is read as recent (epoch %lld, now %lld)", g22 >= 0 ? good_keys[g22].epoch : -1LL,
			      (long long)time(NULL));
			save_ban(NULL, at(2));
			CHECK(strstr(slurp(p2), "G2 ") != NULL && sscanf(strstr(slurp(p2), "G2 ") + 3, "%lld", &nowe) == 1 && nowe <= (long long)time(NULL) + 1,
			      "and the file does not keep the date of the future");
			f2 = fopen(p2, "w");
			fprintf(f2, "G2 %lld [5.5.5.5]\nG2 %lld [6.6.6.6]\n", (long long)time(NULL) + 40LL * 86400, (long long)time(NULL) + 400LL * 86400);
			fclose(f2);
			fresh();
			rcp_ban_load(p2, at(0));
			CHECK(good_recent("[5.5.5.5]", at(1)) && good_recent("[6.6.6.6]", at(1)), "even far ahead: recent, but only from now");
			int g6 = good_find("[6.6.6.6]");
			CHECK(g6 >= 0 && good_keys[g6].epoch <= (long long)time(NULL), "the date is brought back to now, so the trust is 30 days from this start");
			good_keys[g6].epoch -= 31 * 86400;
			CHECK(!good_recent("[6.6.6.6]", at(2)), "and it expires 30 days after");
		}
		/* the same key twice in the file, as itself and as its HMAC: the NEWER date wins, in either order */
		{
			char mk[65];
			good_mac("[8.8.4.4]", mk);
			long long tn = (long long)time(NULL), newer = tn - 3600, older = tn - 5 * 86400;
			for (int order = 0; order < 2; order++) {
				f2 = fopen(p2, "w");
				if (order == 0)
					fprintf(f2, "G2 %lld [8.8.4.4]\nG2 %lld %s\n", newer, older, mk);
				else
					fprintf(f2, "G2 %lld %s\nG2 %lld [8.8.4.4]\n", older, mk, newer);
				fclose(f2);
				fresh();
				rcp_ban_load(p2, at(0));
				int entries = 0, ge = -1;
				for (int i = 0; i < GOOD_KEYS; i++)
					if (strcmp(good_keys[i].mac, mk) == 0) { entries++; ge = i; }
				CHECK(entries == 1 && ge >= 0 && good_keys[ge].epoch == newer && good_recent("[8.8.4.4]", at(1)),
				      "order %d: one entry, with the newer date (%d entries, epoch %lld, wanted %lld)", order, entries,
				      ge >= 0 ? good_keys[ge].epoch : -1LL, newer);
			}
			/* an older login never ages a known key */
			good_put("[8.8.4.4]", NULL, at(5), older);
			int g = good_find("[8.8.4.4]");
			CHECK(g >= 0 && good_keys[g].epoch == newer, "an older login given later does not make the entry older");
			/* the system clock put right BACKWARDS: the epoch of the new login is smaller than the one kept; the epoch
			 * stays the greater, and the monotonic stamp is refreshed all the same */
			fresh();
			uint64_t w1 = at(100), w2 = at(200);
			good_put("[9.9.4.4]", NULL, w1, tn);
			bool ch = good_put("[9.9.4.4]", NULL, w2, tn - 3600);
			g = good_find("[9.9.4.4]");
			CHECK(g >= 0 && good_keys[g].epoch == tn && good_keys[g].when == w2,
			      "clock set back: the epoch stays the greater (%lld, wanted %lld) and `when` is refreshed (%llu, wanted %llu)",
			      g >= 0 ? good_keys[g].epoch : -1LL, tn, g >= 0 ? (unsigned long long)good_keys[g].when : 0ULL, (unsigned long long)w2);
			(void)ch;
			/* and an older `when` never lowers the one kept (the file loaded in the wrong order) */
			good_put("[9.9.4.4]", NULL, at(50), tn - 7200);
			CHECK(good_keys[g].epoch == tn && good_keys[g].when == w2, "an older (epoch, when) pair changes neither clock");
			CHECK(good_recent("[9.9.4.4]", at(201)), "and the key is still known");
			snprintf(ban_path, sizeof ban_path, "%s", p2);   /* fresh() cleared it: the next check writes the file */
		}
		/* a ban dropped as a last resort rewrites the file (the report) */
		captured[0] = 0;
		{
			struct sink sk = {NULL, capture, NULL};
			struct login_result r2;
			memset(&r2, 0, sizeof r2);
			say_append(r2.dropped, sizeof r2.dropped, "BAN of the address [1.2.3.4] (level 1, 3 s left)");
			login_report(&sk, "[1.2.3.4]", "alice", false, &r2, at(1));
		}
		CHECK(strstr(captured, "the ban file is up to date") != NULL, "a ban dropped rewrites the file: %s", captured);
		memset(good_keys, 0, sizeof good_keys);
		unlink(p2);
		char p3[140];
		snprintf(p3, sizeof p3, "%s.new", p2);
		unlink(p3);
		rmdir(d2);
	}

	/* 6d. the REAL epoch of the login is what the file keeps and what the 30 days are counted on: restarts do not rejuvenate it */
	{
		char d3[] = "/tmp/lg-epoch-XXXXXX";
		CHECK(mkdtemp(d3) != NULL, "mkdtemp");
		char p3[128], p3n[140];
		snprintf(p3, sizeof p3, "%s/ban", d3);
		snprintf(p3n, sizeof p3n, "%s.new", p3);
		long long nowe = (long long)time(NULL), e29 = nowe - 29 * 86400;
		FILE *f3 = fopen(p3, "w");
		fprintf(f3, "G2 %lld [7.7.7.7]\nG2 %lld [8.8.8.8]\n", e29, nowe - 31 * 86400);
		fclose(f3);
		for (int round = 0; round < 3; round++) {            /* three restarts, each with a small monotonic clock */
			fresh();
			rcp_ban_load(p3, at(0));
			CHECK(good_recent("[7.7.7.7]", at(1)), "restart %d: the key of 29 days ago is still known", round);
			CHECK(!good_recent("[8.8.8.8]", at(1)), "restart %d: the one of 31 days is not read", round);
			save_ban(NULL, at(2));
			char *tx = slurp(p3);
			long long saved = 0;
			char *g2 = strstr(tx, "G2 ");
			if (g2) sscanf(g2 + 3, "%lld", &saved);
			CHECK(saved == e29, "restart %d: the epoch written is the real one of the login (%lld, wanted %lld)", round, saved, e29);
			CHECK(strstr(tx, "[8.8.8.8]") == NULL, "restart %d: and the stale line is gone", round);
		}
		/* the real days go by: 2 more days and the key is gone, from memory and from the file */
		int g7 = good_find("[7.7.7.7]");
		CHECK(g7 >= 0, "the entry is there");
		good_keys[g7].epoch -= 2 * 86400;
		CHECK(!good_recent("[7.7.7.7]", at(3)), "31 real days after the login the key is no longer known");
		save_ban(NULL, at(4));
		CHECK(strstr(slurp(p3), "G2 ") == NULL, "and it is not written back");
		/* the HMAC form, when the secret survives a restart */
		fresh();
		log_secret_persistent = true;
		rcp_ban_load(p3, at(0));
		login_reserve(G, "alice", at(1), &info);
		struct login_result rr;
		login_resolve(G, "alice", true, at(1), &rr);
		save_ban(NULL, at(2));
		char *tx = slurp(p3);
		char *g2 = strstr(tx, "G2 ");
		CHECK(g2 != NULL && strstr(tx, G) == NULL, "persistent secret: the address of the owner is not on disk");
		char mac[80] = "";
		long long ep = 0;
		if (g2) sscanf(g2 + 3, "%lld %79s", &ep, mac);
		CHECK(strlen(mac) == 64 && strspn(mac, "0123456789abcdef") == 64, "a G2 line holds a 64-digit HMAC (%s)", mac);
		fresh();
		rcp_ban_load(p3, at(0));
		int gi = -1;
		for (int i = 0; i < GOOD_KEYS; i++) if (good_keys[i].mac[0]) gi = i;
		CHECK(gi >= 0 && good_keys[gi].key[0] == 0, "after the restart the entry knows only the HMAC");
		CHECK(good_recent(G, at(5)), "the owner is recognised by the HMAC");
		CHECK(!good_recent("[198.51.100.10]", at(5)), "another address is not");
		CHECK(gi >= 0 && strcmp(good_keys[gi].key, G) == 0, "and the entry now has its key");
		save_ban(NULL, at(6));
		CHECK(strstr(slurp(p3), mac) != NULL, "rewritten as the same HMAC, with the same epoch kept");
		log_secret_persistent = false;
		memset(good_keys, 0, sizeof good_keys);
		unlink(p3);
		unlink(p3n);
		rmdir(d3);
	}

	/* 7. a ban file with more bans than the quota keeps the most valuable, whatever the ORDER of its lines */
	char dir[] = "/tmp/lg-quota-XXXXXX";
	CHECK(mkdtemp(dir) != NULL, "mkdtemp");
	char path[128];
	snprintf(path, sizeof path, "%s/ban", dir);
	time_t t_now = time(NULL);
	struct fline L[300];
	for (int i = 0; i < 300; i++) {
		L[i].i = i;
		L[i].level = i % 5 == 0 ? 2 : 1;
		L[i].exp = (long long)t_now + 600 + i * 7;
	}
	struct fline S[300];
	memcpy(S, L, sizeof S);
	qsort(S, 300, sizeof S[0], fline_cmp);
	bool want[300] = {false};
	for (int j = 0; j < BAN_QUOTA; j++) want[S[j].i] = true;
	int order[300];
	for (int pass = 0; pass < 4; pass++) {
		for (int i = 0; i < 300; i++) order[i] = pass == 0 ? i : pass == 1 ? 299 - i : i;
		if (pass >= 2) {                                      /* two shuffles (a fixed LCG) */
			unsigned s = 12345u + (unsigned)pass;
			for (int i = 299; i > 0; i--) {
				s = s * 1103515245u + 12345u;
				int j = (int)((s >> 8) % (unsigned)(i + 1)), tmp = order[i];
				order[i] = order[j];
				order[j] = tmp;
			}
		}
		fresh();
		FILE *f = fopen(path, "w");
		for (int j = 0; j < 300; j++) {
			int i = order[j];
			fprintf(f, "B2 K %d %lld [10.9.%d.%d]\n", L[i].level, L[i].exp, i / 250, i % 250 + 1);
		}
		fclose(f);
		int loaded = rcp_ban_load(path, at(0));
		int wrong = 0;
		for (int i = 0; i < 300; i++) {
			snprintf(k, sizeof k, "[10.9.%d.%d]", i / 250, i % 250 + 1);
			int ix = lfind(LK_KEY, k, NULL);
			bool is = ix >= 0 && is_banned(&attempts[ix], at(0));
			if (is != want[i]) wrong++;
		}
		CHECK(wrong == 0 && banned_now(at(0)) == BAN_QUOTA, "order %d: exactly the %d most valuable bans are in force (wrong %d, in force %d, load said %d)",
		      pass, BAN_QUOTA, wrong, banned_now(at(0)), loaded);
		if (pass == 0) {
			int displaced = 0;
			for (int i = 0; i < 300; i++) {
				snprintf(k, sizeof k, "[10.9.%d.%d]", i / 250, i % 250 + 1);
				int ix = lfind(LK_KEY, k, NULL);
				if (!want[i] && ix >= 0 && attempts[ix].level > 0) displaced++;
			}
			CHECK(displaced > 0, "in ascending order the ones displaced keep their level (%d)", displaced);
		}
		if (pass == 1) {
			int loser = 0;
			for (int i = 0; i < 300; i++) {
				snprintf(k, sizeof k, "[10.9.%d.%d]", i / 250, i % 250 + 1);
				int ix = lfind(LK_KEY, k, NULL);
				if (!want[i] && ix >= 0 && attempts[ix].level > 0 && !is_banned(&attempts[ix], at(0))) loser++;
			}
			CHECK(loser > 0, "in descending order the lines that lose are loaded as entries that are not banned, with their level (%d)", loser);
		}
	}
	unlink(path);
	rmdir(dir);
}

/* ------------------------------------------------------------------------ */
static void test_unblock(void)
{
	printf("unblock\n");
	struct login_info info;
	const char *K = "[1.2.3.4]";
	fresh();
	ban_user(K, "alice", at(0));
	ban_user(K, "bob", at(10));
	char u[8];
	for (int i = 0; i < 12; i++) { snprintf(u, sizeof u, "x%d", i); fail(K, u, at(20 + i)); }
	CHECK(rcp_banned(K, at(40), NULL) && peek(K, "alice", at(40), NULL) == LV_BANNED, "alice and the key are banned");
	CHECK(rcp_unblock("1.2.3.4:44", at(41)), "unblock answers «was banned»");
	CHECK(!rcp_banned(K, at(41), NULL), "key free");
	CHECK(peek(K, "alice", at(41), NULL) == LV_OK && peek(K, "bob", at(41), NULL) == LV_OK, "every (key,user) free");
	CHECK(!rcp_unblock("1.2.3.4", at(42)), "second time: it was not banned");
	/* the recidivism goes too: a new ban is 15 min again */
	ban_user(K, "alice", at(50));
	CHECK(peek(K, "alice", at(56), &info) == LV_BANNED && info.remain == 900000u - 2000u, "back to 15 min: %llu", (unsigned long long)info.remain);

	/* IPv6: the /48 ban goes with an unblock of ANY address of it */
	fresh();
	char a[64], kk[64];
	for (int i = 0; i < 30; i++) { snprintf(a, sizeof a, "2001:db8:1:%x::5", i + 1); key_of(a, kk); fail(kk, "alice", at(i)); }
	CHECK(rcp_banned("2001:db8:1:99::1", at(40), NULL), "the /48 is banned");
	CHECK(rcp_unblock("2001:db8:1:5::beef", at(41)), "unblock of one address of the /48");
	CHECK(!rcp_banned("2001:db8:1:99::1", at(41), NULL), "the /48 is free");
	/* an unblock does not touch the bookings in flight */
	fresh();
	struct login_result r;
	login_reserve(K, "alice", at(0), &info);
	login_reserve(K, "alice", at(0), &info);
	rcp_unblock(K, at(1));
	CHECK(login_reserve(K, "alice", at(2), &info) == LV_BUSY, "the two bookings are still in flight after the unblock");
	login_resolve(K, "alice", true, at(3), &r);
	login_resolve(K, "alice", true, at(3), &r);
	CHECK(login_reserve(K, "alice", at(4), &info) == LV_OK, "and they give themselves back");
}

/* ------------------------------------------------------------------------ */
static char *slurp(const char *path)
{
	static char buf[32768];
	FILE *f = fopen(path, "r");
	buf[0] = 0;
	if (!f) return buf;
	size_t n = fread(buf, 1, sizeof buf - 1, f);
	buf[n] = 0;
	fclose(f);
	return buf;
}

static void test_file(void)
{
	printf("file\n");
	char dir[] = "/tmp/lg-ban-XXXXXX";
	CHECK(mkdtemp(dir) != NULL, "mkdtemp");
	char path[128];
	snprintf(path, sizeof path, "%s/ban", dir);
	const char *K = "[1.2.3.4]";
	struct login_info info;
	time_t t_now = time(NULL);

	/* the OLD format: «[address] epoch», the 12 h ban of the 1.0 */
	fresh();
	FILE *f = fopen(path, "w");
	fprintf(f, "[1.2.3.4] %lld\n[2001:db8:1:2:3:4:5:6] %lld\n[9.9.9.9] %lld\nnonsense\n[8.8.8.8] notanumber\n",
	        (long long)t_now + 7200, (long long)t_now + 7200, (long long)t_now - 10);
	fclose(f);
	int n = rcp_ban_load(path, at(0));
	CHECK(n == 2, "old format: 2 bans in force loaded (the expired and the nonsense skipped), got %d", n);
	uint64_t remain = 0;
	CHECK(rcp_banned("1.2.3.4", at(0), &remain) && remain > 7100000u && remain <= 7200000u, "IPv4 ban loaded, remain %llu", (unsigned long long)remain);
	CHECK(rcp_banned("2001:db8:1:2:ffff::1", at(0), NULL), "the old IPv6 /128 line became the /64 key");
	CHECK(!rcp_banned("9.9.9.9", at(0), NULL), "the expired line is not loaded");
	/* the converted ban sits at the top of the ladder */
	int i = lfind(LK_KEY, K, NULL);
	CHECK(i >= 0 && attempts[i].level == 2, "converted at the top of the ladder");
	/* a change rewrites the file in the NEW format */
	CHECK(rcp_unblock("9.9.9.9", at(1)) == false, "nothing to unblock there");
	CHECK(rcp_unblock("1.2.3.4", at(1)), "unblock 1.2.3.4");
	char *txt = slurp(path);
	CHECK(strstr(txt, "B2 K 2 ") != NULL && strstr(txt, "[2001:db8:1:2::]") != NULL && strstr(txt, "[1.2.3.4]") == NULL,
	      "rewritten in the new format:\n%s", txt);

	/* round trip: a (key,user) ban with a space in the name, a key ban, a /48 ban, and the recidivism of a ban that ended */
	fresh();
	snprintf(path, sizeof path, "%s/ban2", dir);
	CHECK(rcp_ban_load(path, at(0)) == 0, "no file yet: zero bans, not an error");
	ban_user(K, "john smith", at(0));                                  /* U ban 1 (15 min) */
	char u[8];
	for (int j = 0; j < 12; j++) { snprintf(u, sizeof u, "k%d", j); fail("[5.5.5.5]", u, at(1 + j)); }   /* K ban */
	char a[64], kk[64];
	for (int j = 0; j < 30; j++) { snprintf(a, sizeof a, "2001:db8:7:%x::5", j + 1); key_of(a, kk); fail(kk, "alice", at(20 + j)); }  /* N ban */
	/* a ban that has ended but is remembered: alice on 7.7.7.7 */
	ban_user("[7.7.7.7]", "ended", at(0));
	uint64_t later = at(2000);                                         /* 7.7.7.7's ban (15 min) has ended */
	save_ban(NULL, later);
	txt = slurp(path);
	CHECK(strstr(txt, "B2 U 1 ") != NULL, "bans that have ended but are not forgotten are written too:\n%s", txt);
	/* write again at a moment in which everything is in force, and read it back */
	save_ban(NULL, at(100));
	txt = slurp(path);
	{
		char uk[65], want[200];
		user_key("john smith", uk);
		snprintf(want, sizeof want, "[1.2.3.4] %s\n", uk);
		CHECK(strstr(txt, want) != NULL, "the user is written as its HMAC:\n%s", txt);
		CHECK(strstr(txt, "john") == NULL && strstr(txt, "smith") == NULL && strstr(txt, "ended") == NULL,
		      "no name in clear in the ban file:\n%s", txt);
		struct stat st;
		CHECK(stat(path, &st) == 0 && (st.st_mode & 0777) == 0600, "ban file is 0600 (mode %o)", (unsigned)(st.st_mode & 0777));
	}
	CHECK(strstr(txt, "B2 K 1 ") != NULL && strstr(txt, "[5.5.5.5]\n") != NULL, "the key ban is written");
	CHECK(strstr(txt, "B2 N 1 ") != NULL && strstr(txt, "[2001:db8:7::]\n") != NULL, "the /48 ban is written");
	fresh();
	snprintf(path, sizeof path, "%s/ban2", dir);
	n = rcp_ban_load(path, at(5000));                                  /* "now" is a restarted clock, 5000 s on the new axis */
	CHECK(n >= 0, "reload rc=%d", n);
	/* rewind the picture: the file is absolute in wall time, the loaded ones are relative to at(5000) */
	CHECK(peek(K, "john smith", at(5000), &info) == LV_BANNED && info.kind == LK_USER, "the user with a space is banned after the restart");
	CHECK(peek(K, "john", at(5000), NULL) == LV_OK, "and only that name");
	CHECK(rcp_banned("5.5.5.5", at(5000), NULL), "the key ban survived");
	CHECK(rcp_banned("2001:db8:7:1234::1", at(5000), NULL), "the /48 ban survived");
	/* the recidivism of the ended ban: 7.7.7.7 must be at level 1 again (the file was written at at(100): it was still in force) */
	int ie = lfind_user("[7.7.7.7]", "ended");
	CHECK(ie >= 0 && attempts[ie].level == 1, "the level of a ban is read back");

	/* the file written when a ban has ENDED but is not forgotten: its level comes back, the ban does not */
	fresh();
	snprintf(path, sizeof path, "%s/ban3", dir);
	rcp_ban_load(path, at(0));
	ban_user(K, "ended", at(0));
	save_ban(NULL, at(2000));                                          /* 33 min later: ended, remembered */
	txt = slurp(path);
	CHECK(strstr(txt, "B2 U 1 ") != NULL, "an ended ban with recidivism is written:\n%s", txt);
	fresh();
	snprintf(path, sizeof path, "%s/ban3", dir);
	n = rcp_ban_load(path, at(100000));
	CHECK(n == 0, "no ban in force, got %d", n);
	CHECK(peek(K, "ended", at(100000), NULL) == LV_OK, "free");
	ban_user(K, "ended", at(100000));
	CHECK(peek(K, "ended", at(100005), &info) == LV_BANNED && info.remain == 3600000u - 1000u, "the recidivism came back: the next ban is 1 h (remain %llu)", (unsigned long long)info.remain);

	/* a bad path: the file cannot be read -> -1, not zero */
	CHECK(rcp_ban_load("/etc/passwd/ban", at(0)) == -1, "unreadable path is -1");
	CHECK(rcp_ban_load("", at(0)) == 0 && rcp_ban_load(NULL, at(0)) == 0, "no path: persistence off");
	fresh();
	/* tidy the directory (files only, no rm -rf) */
	const char *names[] = {"ban", "ban.new", "ban2", "ban2.new", "ban3", "ban3.new"};
	for (size_t j = 0; j < sizeof names / sizeof *names; j++) { snprintf(path, sizeof path, "%s/%s", dir, names[j]); unlink(path); }
	rmdir(dir);
}

/* ------------------------------------------------------------------------ */
static void hex(const uint8_t *b, size_t n, char *out) { for (size_t i = 0; i < n; i++) sprintf(out + 2 * i, "%02x", b[i]); }

static void test_log(void)
{
	printf("log\n");
	uint8_t mac[32];
	char h[80];
	/* RFC 4231, test case 2 */
	hmac_sha256((const uint8_t *)"Jefe", 4, "what do ya want for nothing?", 28, mac);
	hex(mac, 32, h);
	CHECK(strcmp(h, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843") == 0, "RFC 4231 case 2: %s", h);
	/* RFC 4231, test case 6: a key longer than the block is hashed first */
	uint8_t big[131];
	memset(big, 0xaa, sizeof big);
	const char *msg = "Test Using Larger Than Block-Size Key - Hash Key First";
	hmac_sha256(big, sizeof big, msg, strlen(msg), mac);
	hex(mac, 32, h);
	CHECK(strcmp(h, "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54") == 0, "RFC 4231 case 6: %s", h);
	/* SHA-256 of "abc" and of a message that crosses the padding boundary (56 bytes) */
	struct sha256 c;
	sha256_init(&c); sha256_update(&c, "abc", 3); sha256_final(&c, mac); hex(mac, 32, h);
	CHECK(strcmp(h, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") == 0, "SHA-256 abc: %s", h);
	sha256_init(&c); sha256_update(&c, "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq", 56); sha256_final(&c, mac); hex(mac, 32, h);
	CHECK(strcmp(h, "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1") == 0, "SHA-256 56 bytes: %s", h);

	/* the secret file: made 0600, read back the same */
	char dir[] = "/tmp/lg-sec-XXXXXX";
	CHECK(mkdtemp(dir) != NULL, "mkdtemp");
	CHECK(rcp_log_secret_load(dir) == 0, "first call makes the secret");
	uint8_t first[32];
	memcpy(first, log_secret, 32);
	char path[128];
	snprintf(path, sizeof path, "%s/%s", dir, LOG_SECRET_FILE);
	struct stat st;
	CHECK(stat(path, &st) == 0 && st.st_size == 32 && (st.st_mode & 0777) == 0600, "file is 32 bytes, 0600 (mode %o)", (unsigned)(st.st_mode & 0777));
	memset(log_secret, 0, 32);
	CHECK(rcp_log_secret_load(dir) == 1 && memcmp(first, log_secret, 32) == 0, "second call reads the same secret");
	chmod(path, 0644);
	CHECK(rcp_log_secret_load(dir) == 0 && memcmp(first, log_secret, 32) != 0, "a secret readable by others is replaced");
	CHECK(rcp_log_secret_load("/etc/passwd/nope") == -1, "cannot be kept: the secret of the run only");
	unlink(path);
	snprintf(path, sizeof path, "%s/%s.new", dir, LOG_SECRET_FILE);
	unlink(path);
	rmdir(dir);

	/* the tags */
	char t1[96], t2[96], t3[96];
	CHECK(strcmp(log_user("root", t1, sizeof t1, true), "root") == 0, "a user of the machine is named");
	CHECK(strncmp(log_user("root", t1, sizeof t1, false), "user [", 6) == 0 && strstr(t1, "root") == NULL,
	      "without the lookup (refused attempts) even a real name is a tag: %s", t1);
	const char *ghost = log_user("zzqq-nosuchuser", t1, sizeof t1, true);
	CHECK(strncmp(ghost, "unknown user [", 14) == 0 && strlen(ghost) == 14 + 6 + 1 && ghost[strlen(ghost) - 1] == ']', "format: %s", ghost);
	CHECK(strstr(ghost, "zzqq") == NULL, "no character of the name in clear");
	log_user("zzqq-nosuchuser", t2, sizeof t2, true);
	CHECK(strcmp(t1, t2) == 0, "same name, same tag");
	log_user("zzqq-nosuchuser2", t3, sizeof t3, true);
	CHECK(strcmp(t1, t3) != 0, "another name, another tag");
	log_secret[0] ^= 0xff;
	log_user("zzqq-nosuchuser", t3, sizeof t3, true);
	CHECK(strcmp(t1, t3) != 0, "another secret, another tag");
	/* ...and in the lines of the limiter */
	fresh();
	captured[0] = 0;
	struct login_info info;
	login_reserve("[1.2.3.4]", "hunter2-as-user", at(0), &info);
	rcp_orphan_verdict("hunter2-as-user", "1.2.3.4", false, false, 0, at(1), capture, NULL);
	CHECK(strstr(captured, "hunter2") == NULL && strstr(captured, "unknown user [") != NULL, "the line of a failed attempt carries the tag, not the name:\n%s", captured);
	captured[0] = 0;
	login_reserve("[1.2.3.4]", "root", at(2), &info);
	rcp_orphan_verdict("root", "1.2.3.4", false, false, 0, at(3), capture, NULL);
	CHECK(strstr(captured, "as root") != NULL, "a real user is named in the line:\n%s", captured);
}

/* ------------------------------------------------------------------------ */
static void rec_line(void *ctx, const char *line) { capture(ctx, line); }

static int in_flight_of(const char *key, const char *user)
{
	int i = lfind_user(key, user);
	return i < 0 ? -1 : attempts[i].in_flight;
}
/* ⚠ counted at at(13): a failure stamped later than the instant asked (the 12 s net, tickets at at(3)) would be in the
 * future and the unsigned subtraction in failed_inside() wraps, so it would read 0 */
static int failures_of(const char *key, const char *user)
{
	int i = lfind_user(key, user);
	return i < 0 ? 0 : failed_inside(&attempts[i], at(13));
}

/* what rcp_time() puts on the wire (ported from 24f99518): the last byte of the last message, how many, the close code */
static int wire_n;
static uint8_t wire_last, wire_closed;
static void wire_reset(void) { wire_n = 0; wire_last = 0; wire_closed = 0; }
static void wire_send(void *ctx, const uint8_t *data, size_t len) { (void)ctx; wire_n++; wire_last = data[len - 1]; }
static void wire_close(void *ctx, uint8_t reason) { (void)ctx; wire_closed = reason; }

static void test_verdict_paths(void)
{
	printf("verdict paths\n");
	const char *K = "[1.2.3.4]";
	struct login_info info;
	fresh();
	/* 1. an orphan verdict WITH the rhost of the flight record gives the booking back and counts */
	login_reserve(K, "alice", at(0), &info);
	CHECK(in_flight_of(K, "alice") == 1, "booked");
	rcp_orphan_verdict("alice", "1.2.3.4", false, false, 0, at(1), rec_line, NULL);
	CHECK(in_flight_of(K, "alice") == 0 && failures_of(K, "alice") == 1, "orphan with rhost: in flight 0, failure counted (%d, %d)",
	      in_flight_of(K, "alice"), failures_of(K, "alice"));
	/* a failure stamped in the FUTURE (a clock that went back) still counts: failed_inside() asked 5 s BEFORE the stamp */
	{
		int i = lfind_user(K, "alice");
		CHECK(i >= 0 && failed_inside(&attempts[i], at(1) - 5000) == 1,
		      "a failure stamped at now+5 s counts as inside the window (no unsigned wrap)");
	}
	/* ...and WITHOUT it nothing can be resolved (this is the defect of helper.c the test of test_helper.c guards) */
	login_reserve(K, "alice", at(2), &info);
	rcp_orphan_verdict("alice", "", false, false, 0, at(3), rec_line, NULL);
	CHECK(in_flight_of(K, "alice") == 1, "an empty rhost leaves the booking up: the helper must always carry the address");

	/* 2. the helper died: orphan, lost -> booking back, NOTHING counted */
	fresh();
	login_reserve(K, "alice", at(0), &info);
	login_reserve(K, "alice", at(0), &info);
	captured[0] = 0;
	rcp_orphan_verdict("alice", "1.2.3.4", false, true, 0, at(1), rec_line, NULL);
	rcp_orphan_verdict("alice", "1.2.3.4", false, true, 0, at(1), rec_line, NULL);
	CHECK(in_flight_of(K, "alice") == 0 && failures_of(K, "alice") == 0, "orphan lost: given back, not counted (%d, %d)",
	      in_flight_of(K, "alice"), failures_of(K, "alice"));
	CHECK(failures_of(K, "") == 0 && attempts[lfind(LK_KEY, K, NULL)].amount == 0, "the key's counter is untouched either");
	CHECK(strstr(captured, "NOTHING") != NULL, "and it is said: %s", captured);
	/* a hundred dead-helper verdicts ban nobody */
	for (int i = 0; i < 100; i++) {
		login_reserve(K, "alice", at(i), &info);
		rcp_orphan_verdict("alice", "1.2.3.4", false, true, 0, at(i), rec_line, NULL);
	}
	CHECK(peek(K, "alice", at(101), NULL) == LV_OK, "100 lost verdicts: not banned");

	/* 3. with a live SESSION: the PAM timeout (rcp_verdict false) counts; the dead helper (rcp_verdict_lost) does not */
	static rcp_session s;
	memset(&s, 0, sizeof s);
	s.g.record = (void (*)(void *, const char *))rec_line;
	snprintf(s.address, sizeof s.address, "%s", K);
	snprintf(s.user, sizeof s.user, "%s", "alice");
	fresh();
	login_reserve(K, "alice", at(0), &info);
	s.state = S_WAIT_VERDICT; s.expected_verdict = true; s.ticket = 7;
	CHECK(rcp_verdict(&s, 7, false, at(1)), "session takes the timeout verdict");
	CHECK(in_flight_of(K, "alice") == 0 && failures_of(K, "alice") == 1, "timeout through a session: counted (%d, %d)",
	      in_flight_of(K, "alice"), failures_of(K, "alice"));
	login_reserve(K, "alice", at(2), &info);
	s.state = S_WAIT_VERDICT; s.expected_verdict = true; s.ticket = 8;
	CHECK(!rcp_verdict_lost(&s, 9), "a wrong ticket is not taken");
	CHECK(rcp_verdict_lost(&s, 8), "session takes the lost verdict");
	CHECK(in_flight_of(K, "alice") == 0 && failures_of(K, "alice") == 1 && s.refusal_is_ours && !s.cred_good,
	      "helper dead through a session: given back, NOT counted, refusal is ours (%d, %d)",
	      in_flight_of(K, "alice"), failures_of(K, "alice"));
	CHECK(!rcp_verdict_lost(&s, 8), "a second answer is not taken");

	/* 4. ⛔ the byte on the wire (DECISIONS.md §11.39, ported from 24f99518): a check the server could not make is
	 *    REJECTED(0x0E SESSION_UNSERVABLE), not 0x07; what PAM decided, and the attempt without a verdict, stay 0x07;
	 *    the limiter's own 0x08 is never touched.  Same fixed second in every case. */
	s.g.send_msg = wire_send;
	s.g.close = wire_close;
	/* a. the helper died (rcp_verdict_lost): ours -> 0x0E, after the fixed second only */
	fresh();
	s.state = S_WAIT_VERDICT; s.expected_verdict = false; s.refusal_is_ours = false; s.cred_good = false;
	s.cred_reason = RCP_WRONG_CREDENTIALS; s.cred_arrival = at(0);
	login_reserve(K, "alice", at(0), &info);
	s.expected_verdict = true; s.ticket = 11;
	CHECK(rcp_verdict_lost(&s, 11), "(wire) the lost verdict is taken");
	wire_reset();
	CHECK(rcp_time(&s, at(0) + FIXED_DELAY) && wire_n == 0, "(wire) nothing before the fixed second is over");
	CHECK(!rcp_time(&s, at(0) + FIXED_DELAY + 1) && wire_n == 1 && wire_last == RCP_SESSION_UNSERVABLE
	      && wire_closed == RCP_SESSION_UNSERVABLE,
	      "(wire) helper dead: REJECTED 0x0E after the fixed second alone, NOT held to the floor (got %#x, %d messages)",
	      wire_last, wire_n);
	CHECK(failures_of(K, "alice") == 0, "(wire) and nothing was counted");
	/* b. a PAM no: still 0x07 */
	fresh();
	s.state = S_WAIT_VERDICT; s.refusal_is_ours = false; s.cred_arrival = at(0);
	login_reserve(K, "alice", at(0), &info);
	s.expected_verdict = true; s.ticket = 12;
	CHECK(rcp_verdict(&s, 12, false, at(1)), "(wire) the PAM no is taken");
	wire_reset();
	CHECK(!rcp_time(&s, at(0) + REJECT_FLOOR + 1) && wire_last == RCP_WRONG_CREDENTIALS && wire_closed == RCP_WRONG_CREDENTIALS,
	      "(wire) a PAM no stays REJECTED 0x07 (got %#x)", wire_last);
	/* c. no verdict within VERDICT_CAP: counted, so 0x07 */
	fresh();
	s.state = S_WAIT_VERDICT; s.refusal_is_ours = false; s.cred_good = false; s.cred_reason = RCP_WRONG_CREDENTIALS;
	s.cred_arrival = at(0);
	login_reserve(K, "alice", at(0), &info);
	s.expected_verdict = true; s.ticket = 13;
	wire_reset();
	CHECK(!rcp_time(&s, at(0) + VERDICT_CAP + 1) && wire_last == RCP_WRONG_CREDENTIALS && failures_of(K, "alice") == 1,
	      "(wire) the 12 s net: counted as a failure and REJECTED 0x07 (got %#x, %d failures)", wire_last,
	      failures_of(K, "alice"));
	/* d. a limiter refusal that is flagged ours keeps its own reason (0x08) */
	fresh();
	s.state = S_WAIT_VERDICT; s.expected_verdict = false; s.cred_good = false; s.cred_reason = RCP_TOO_MANY_ATTEMPTS;
	s.refusal_is_ours = true; s.cred_arrival = at(0);
	wire_reset();
	CHECK(!rcp_time(&s, at(0) + FIXED_DELAY + 1) && wire_last == RCP_TOO_MANY_ATTEMPTS,
	      "(wire) a reason other than WRONG_CREDENTIALS is kept (0x08, got %#x) and goes out at the fixed second, not held to "
	      "REJECT_FLOOR (the byte already says the road; wait-verdict connections cannot be evicted)", wire_last);

	/* e. ⛔ THE UNIFORM FLOOR (25 Oct 2026, pam-tempi): a denied-list user answered by PAM in 50 ms, a wrong password
	 *    after PAM's own 2 s and a success: the refusals leave at the same instant, never before REJECT_FLOOR; the
	 *    success keeps the fixed second */
	fresh();
	s.state = S_WAIT_VERDICT; s.expected_verdict = false; s.cred_good = false; s.refusal_is_ours = false;
	s.cred_reason = RCP_WRONG_CREDENTIALS; s.cred_arrival = at(0);
	wire_reset();
	CHECK(rcp_time(&s, at(0) + 50) && rcp_time(&s, at(0) + FIXED_DELAY + 1) && rcp_time(&s, at(0) + 2200) && wire_n == 0,
	      "(floor) a refusal already decided stays unsent past the fixed second and past PAM's usual 2.2 s");
	CHECK(!rcp_time(&s, at(0) + REJECT_FLOOR + 1) && wire_last == RCP_WRONG_CREDENTIALS && wire_n == 1,
	      "(floor) and leaves after REJECT_FLOOR (got %#x, %d messages)", wire_last, wire_n);
	fresh();
	s.state = S_WAIT_VERDICT; s.expected_verdict = false; s.cred_good = true; s.refusal_is_ours = false; s.cred_arrival = at(0);
	wire_reset();
	CHECK(rcp_time(&s, at(0) + FIXED_DELAY) && wire_n == 0, "(floor) a success waits the fixed second");
	CHECK(rcp_time(&s, at(0) + FIXED_DELAY + 1) && wire_n == 1 && s.state == S_WAIT_ATTACH,
	      "(floor) and is admitted right after it, NOT held to the refusal floor (state %d, %d messages)", (int)s.state, wire_n);

	/* 5. the keys that logged in lately (ported from 4d9eb72b / 24c7b668): only an ADMITTED verdict makes a key known */
	{
		const char *G = "[7.7.7.7]", *B = "[8.8.8.8]";
		struct login_result lr;
		fresh();
		CHECK(!good_recent(G, at(0)) && !rcp_asking_for_known_key(), "(known) nobody is known at the start, and the flag is down");
		login_reserve(G, "alice", at(0), &info);
		login_resolve(G, "alice", true, at(1), &lr);
		login_reserve(B, "alice", at(0), &info);
		login_resolve(B, "alice", false, at(1), &lr);
		CHECK(good_recent(G, at(2)), "(known) a key with an admitted login is known");
		CHECK(!good_recent(B, at(2)), "(known) a key with only a failure is not");
		CHECK(good_recent(G, at(1) + GOOD_AGE), "(known) still known at exactly GOOD_AGE");
		CHECK(!good_recent(G, at(1) + GOOD_AGE + 1), "(known) not known past GOOD_AGE");
		CHECK(good_recent(G, at(0)), "(known) a login stamped after `now` (helper clock ahead) is recent, the subtraction does not wrap");

		/* 6. §11.47 B (ported from 249c534a): a PAM no given while pam_faillock had the account locked is NOT counted for
		 *    a key that logged in lately (login_release), and counts for a key that never did */
		fresh();
		good_note(G, at(0));
		snprintf(s.address, sizeof s.address, "%s", G);
		login_reserve(G, "alice", at(2), &info);
		s.state = S_WAIT_VERDICT; s.expected_verdict = true; s.ticket = 21; s.cred_arrival = at(2);
		rcp_refusal_locked(21);
		CHECK(rcp_verdict(&s, 21, false, at(3)), "(locked) the verdict is taken");
		rcp_refusal_locked(0);
		CHECK(in_flight_of(G, "alice") == 0 && failures_of(G, "alice") == 0,
		      "(locked) a locked-account no for a known key: booking given back, NOT counted (%d, %d)",
		      in_flight_of(G, "alice"), failures_of(G, "alice"));
		snprintf(s.address, sizeof s.address, "%s", B);
		login_reserve(B, "alice", at(2), &info);
		s.state = S_WAIT_VERDICT; s.expected_verdict = true; s.ticket = 22;
		rcp_refusal_locked(22);
		CHECK(rcp_verdict(&s, 22, false, at(3)), "(locked) the verdict is taken");
		rcp_refusal_locked(0);
		CHECK(failures_of(B, "alice") == 1, "(locked) the same no for a key that never logged in COUNTS (no user-name oracle): %d",
		      failures_of(B, "alice"));
		snprintf(s.address, sizeof s.address, "%s", G);
		login_reserve(G, "alice", at(2), &info);
		s.state = S_WAIT_VERDICT; s.expected_verdict = true; s.ticket = 23;
		rcp_refusal_locked(99); /* another ticket's mark */
		CHECK(rcp_verdict(&s, 23, false, at(3)), "(locked) the verdict is taken");
		rcp_refusal_locked(0);
		CHECK(failures_of(G, "alice") == 1, "(locked) a mark for ANOTHER ticket does not exempt this no: %d", failures_of(G, "alice"));
		/* the orphan road (the connection is gone), same rule */
		fresh();
		good_note(G, at(0));
		login_reserve(G, "alice", at(2), &info);
		rcp_refusal_locked(31);
		rcp_orphan_verdict("alice", "7.7.7.7", false, false, 31, at(3), rec_line, NULL);
		rcp_refusal_locked(0);
		CHECK(in_flight_of(G, "alice") == 0 && failures_of(G, "alice") == 0,
		      "(locked) orphan, known key: given back, NOT counted (%d, %d)", in_flight_of(G, "alice"), failures_of(G, "alice"));
		login_reserve(G, "alice", at(4), &info);
		rcp_orphan_verdict("alice", "7.7.7.7", false, false, 0, at(5), rec_line, NULL);
		CHECK(failures_of(G, "alice") == 1, "(locked) orphan without the mark: an ordinary no, counted (%d)", failures_of(G, "alice"));
		/* the mark belongs to ONE delivery: mark 31 and an orphan verdict of ANOTHER ticket (32) is counted */
		fresh();
		good_note(G, at(0));
		login_reserve(G, "alice", at(2), &info);
		rcp_refusal_locked(31);
		rcp_orphan_verdict("alice", "7.7.7.7", false, false, 32, at(3), rec_line, NULL);
		rcp_refusal_locked(0);
		CHECK(failures_of(G, "alice") == 1, "(locked) orphan of ANOTHER ticket than the mark: counted (%d)", failures_of(G, "alice"));
	}
}

/* ------------------------------------------------------------------------ */
static void test_extreme_expiries(void)
{
	printf("extreme expiries\n");
	char dir[] = "/tmp/lg-ext-XXXXXX";
	CHECK(mkdtemp(dir) != NULL, "mkdtemp");
	char path[128];
	snprintf(path, sizeof path, "%s/ban", dir);
	time_t t_now = time(NULL);
	fresh();
	FILE *f = fopen(path, "w");
	fprintf(f, "B2 K 1 9223372036854775807 [3.3.3.3]\n"        /* the end of time: capped at 12 h */
	           "B2 K 1 -5 [4.4.4.4]\n"                            /* negative: not a time */
	           "B2 K 1 -9223372036854775807 [4.4.4.5]\n"
	           "B2 K 1 0 [7.7.7.7]\n"                             /* 1970: forgotten */
	           "[5.5.5.5] 9223372036854775807\n"                 /* old format, same cap */
	           "[6.6.6.6] -1\n"
	           "B2 K 1 %lld [8.8.8.8]\n"                          /* a normal one */
	           "B2 K 3 %lld [9.9.9.9]\n"                          /* level out of range */
	           "B2 U 1 %lld [1.1.1.1] not-a-hash\n",              /* a name instead of a hash */
	        (long long)t_now + 600, (long long)t_now + 600, (long long)t_now + 600);
	fclose(f);
	int n = rcp_ban_load(path, at(0));
	CHECK(n == 3, "3 usable lines, got %d", n);
	uint64_t remain = 0;
	CHECK(rcp_banned("3.3.3.3", at(0), &remain) && remain == 43200000u, "the end of time is capped at 12 h: %llu", (unsigned long long)remain);
	CHECK(rcp_banned("5.5.5.5", at(0), &remain) && remain == 43200000u, "old format capped too: %llu", (unsigned long long)remain);
	CHECK(!rcp_banned("4.4.4.4", at(0), NULL) && !rcp_banned("4.4.4.5", at(0), NULL), "negative epochs are refused");
	CHECK(!rcp_banned("7.7.7.7", at(0), NULL) && !rcp_banned("6.6.6.6", at(0), NULL), "1970 and a negative old line are not bans");
	CHECK(rcp_banned("8.8.8.8", at(0), &remain) && remain > 590000u && remain <= 600000u, "a normal line: %llu", (unsigned long long)remain);
	CHECK(!rcp_banned("9.9.9.9", at(0), NULL), "level 3 is not a line");
	CHECK(lfind(LK_USER, "[1.1.1.1]", "not-a-hash") < 0, "a name in the U field is not accepted");
	/* a clock that is tiny: the end of an ended ban is clamped, no wrap-around */
	fresh();
	f = fopen(path, "w");
	fprintf(f, "B2 K 2 %lld [2.2.2.2]\n", (long long)t_now - 3600);
	fclose(f);
	n = rcp_ban_load(path, 5);
	CHECK(n == 0 && !rcp_banned("2.2.2.2", 5, NULL), "ended ban with a tiny clock: not in force");
	int i = lfind(LK_KEY, "[2.2.2.2]", NULL);
	CHECK(i >= 0 && attempts[i].banned_until == 1 && attempts[i].level == 2, "recidivism read back, end clamped to 1");
	snprintf(path, sizeof path, "%s/ban", dir);
	unlink(path);
	rmdir(dir);
	fresh();
}

/* ⭐ The secret and state files: the scheme of transport.c secret_load() (O_NOFOLLOW, owner root or us, O_EXCL temporary,
 * atomic rename).  A link is refused, a foreign owner is refused, and the writing is atomic and writes through nothing. */
static void test_secure_files(void)
{
	char sd[] = "/tmp/lg-sf-XXXXXX";
	char victim[160], lp[160], planted[200], bp[160], line[64];
	struct stat st, lst;
	const char *K = "[1.2.3.4]";
	FILE *vf;
	int n, others;
	DIR *dh;
	struct dirent *de;
	char buf[40];

	CHECK(mkdtemp(sd) != NULL, "mkdtemp");
	snprintf(victim, sizeof victim, "%s/victim", sd);
	snprintf(lp, sizeof lp, "%s/%s", sd, LOG_SECRET_FILE);
	vf = fopen(victim, "w");
	CHECK(vf != NULL, "victim file");
	for (int i = 0; i < 32; i++)
		fputc('V', vf);
	fclose(vf);
	chmod(victim, 0600);

	/* 1. a link in place of log-secret: not read (the 32 'V' are NOT the secret), not written through, replaced */
	CHECK(symlink(victim, lp) == 0, "plant a link at log-secret");
	CHECK(rcp_log_secret_load(sd) == 0, "a link in place of log-secret is refused: a new secret is made");
	CHECK(memcmp(log_secret, "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV", 32) != 0, "...it is not the victim's bytes");
	vf = fopen(victim, "r");
	n = vf ? (int)fread(buf, 1, sizeof buf, vf) : -1;
	if (vf)
		fclose(vf);
	CHECK(n == 32 && memcmp(buf, "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV", 32) == 0, "...and the victim is not written through");
	CHECK(lstat(lp, &lst) == 0 && S_ISREG(lst.st_mode) && (lst.st_mode & 0777) == 0600 && lst.st_size == 32,
	      "the link was replaced by a regular 0600 file of 32 bytes");

	/* 2. a link planted at the temporary name: O_EXCL|O_NOFOLLOW, it is removed and recreated, the victim is untouched */
	unlink(lp);
	snprintf(planted, sizeof planted, "%s/%s.tmp.%ld", sd, LOG_SECRET_FILE, (long)getpid());
	CHECK(symlink(victim, planted) == 0, "plant a link at the temporary name");
	CHECK(rcp_log_secret_load(sd) == 0, "a planted temporary does not stop the writing");
	vf = fopen(victim, "r");
	n = vf ? (int)fread(buf, 1, sizeof buf, vf) : -1;
	if (vf)
		fclose(vf);
	CHECK(n == 32 && memcmp(buf, "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV", 32) == 0, "the victim is untouched");
	CHECK(lstat(planted, &lst) != 0, "and no temporary stays");

	/* 3. a file of ANOTHER OWNER is not trusted (as root: chown'ed; as a user: this uid is made to look foreign) */
	CHECK(rcp_log_secret_load(sd) == 1, "our own good file is read");
	memcpy(line, log_secret, 32);
	bool foreign = true;
	if (geteuid() == 0)
		foreign = chown(lp, 12345, (gid_t)-1) == 0; /* a root in a user namespace may not be able to: then the check is skipped */
	else
		rxt_uid_shift = 1;
	if (foreign)
		CHECK(rcp_log_secret_load(sd) == 0 && memcmp(line, log_secret, 32) != 0, "a secret of another owner is not trusted: replaced");
	else
		CHECK(true, "(skipped: this root cannot chown to another uid)");
	rxt_uid_shift = 0;
	CHECK(stat(lp, &st) == 0 && st.st_uid == geteuid() && (st.st_mode & 0777) == 0600, "and the new file is ours, 0600");

	/* 4. the writing leaves nothing but the file itself */
	others = 0;
	dh = opendir(sd);
	while (dh && (de = readdir(dh)) != NULL)
		if (strcmp(de->d_name, ".") && strcmp(de->d_name, "..") && strcmp(de->d_name, LOG_SECRET_FILE) &&
		    strcmp(de->d_name, "victim"))
			others++;
	if (dh)
		closedir(dh);
	CHECK(others == 0, "no temporary or .new left in the directory (%d)", others);
	{
		/* a world-writable directory WITH the sticky bit (as /tmp is), made here so that nothing is left in /tmp itself */
		char td[] = "/tmp/lg-st-XXXXXX";
		char tf[200];

		CHECK(mkdtemp(td) != NULL, "mkdtemp (sticky)");
		chmod(td, 01777);
		CHECK(rcp_log_secret_load(td) == 0, "a directory with the sticky bit (as /tmp) is accepted");
		snprintf(tf, sizeof tf, "%s/%s", td, LOG_SECRET_FILE);
		unlink(tf);
		rmdir(td);
	}

	/* 5. the ban file: a link is refused (-1, not «no bans»), a foreign owner is refused, 0644 (the 1.0's) is read, and the
	 *    saving replaces a planted link without writing through it */
	snprintf(bp, sizeof bp, "%s/ban", sd);
	fresh();
	CHECK(symlink(victim, bp) == 0, "plant a link at the ban file");
	CHECK(rcp_ban_load(bp, at(0)) == -1, "a link at the ban file is a fault (-1), not zero bans");
	ban_user(K, "linkvictim", at(0));
	save_ban(NULL, at(1));
	CHECK(lstat(bp, &lst) == 0 && S_ISREG(lst.st_mode) && (lst.st_mode & 0777) == 0600,
	      "the saving replaced the link by a regular 0600 file");
	vf = fopen(victim, "r");
	n = vf ? (int)fread(buf, 1, sizeof buf, vf) : -1;
	if (vf)
		fclose(vf);
	CHECK(n == 32 && memcmp(buf, "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV", 32) == 0, "...and the victim of the link was not written");
	fresh();
	CHECK(rcp_ban_load(bp, at(0)) >= 0, "our own file is read");
	chmod(bp, 0644);
	fresh();
	CHECK(rcp_ban_load(bp, at(0)) >= 0, "a 0644 ban file (what the 1.0 wrote) is still read");
	foreign = true;
	if (geteuid() == 0)
		foreign = chown(bp, 12345, (gid_t)-1) == 0;
	else
		rxt_uid_shift = 1;
	fresh();
	if (foreign)
		CHECK(rcp_ban_load(bp, at(0)) == -1, "a ban file of another owner is a fault (-1)");
	else
		CHECK(true, "(skipped: this root cannot chown to another uid)");
	rxt_uid_shift = 0;
	fresh();
	CHECK(rcp_ban_load("/tmp/lg-sf-nonexistent-dir/ban", at(0)) == 0, "no directory, no file yet: zero bans, not an error");

	/* 6. a directory anybody can write to (no sticky bit) is refused: anybody could swap the file */
	{
		char wd[] = "/tmp/lg-sw-XXXXXX";

		CHECK(mkdtemp(wd) != NULL, "mkdtemp (world-writable)");
		chmod(wd, 0777);
		CHECK(rcp_log_secret_load(wd) == -1, "a world-writable directory: no file is made, the secret of the run only");
		char wb[200];

		snprintf(wb, sizeof wb, "%s/ban", wd);
		fresh();
		CHECK(rcp_ban_load(wb, at(0)) == -1, "...and the ban file there is a fault (-1)");
		rmdir(wd);
	}

	unlink(bp);
	unlink(lp);
	unlink(victim);
	rmdir(sd);
	fresh();
}

int main(void)
{
	test_keys();
	test_thresholds();
	test_progression();
	test_reset();
	test_rotation();
	test_in_flight();
	test_orphan();
	test_verdict_paths();
	test_extreme_expiries();
	test_table();
	test_quota();
	test_unblock();
	test_file();
	test_log();
	test_secure_files();
	printf("\n%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
