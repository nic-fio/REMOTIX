/* test.c — the root side's PAUSE leaves as a plain refusal, not as «not checked», and is not counted (1.5, reading of rcp.c, A1).
 *
 * ⛔ The oracle: with the split on, the root side pauses a user after 5 refusals of PAM for that uid (any addresses).  Answered as «not checked» it
 *    leaves as 0x0E after ONE second, while a wrong password and a name that does not exist leave as 0x07 after 2.5 s: whoever can provoke a pause
 *    (four addresses are enough) sees that the name EXISTS (§4.4, §11.39).  The new outcome RXR_PAUSED travels to rcp.c as
 *    `rcp_refusal_paused(ticket)` around the delivery: a REFUSED/WRONG_CREDENTIALS at REJECT_FLOOR, never counted.
 *
 *   1. a wrong password: nothing before 2.5 s, then REJECTED 0x07;
 *   2. a PAUSED verdict: the SAME byte (0x07) at the SAME instant (nothing at 2499 ms, REJECTED just after 2500 ms), and not the 0x0E of «not checked»;
 *   3. the pause is counted by the rule of §11.47 B: from a key that NEVER logged in it counts as any refusal (repeated pauses ban after exactly as many tries as wrong
 *      passwords do — otherwise a name that does not exist would be banned and a paused one not: the oracle again); from a key that logged in during the last 30 days
 *      it is not counted (twenty ban nobody);
 *   4. the same on the orphan road (the client hung up);
 *   5. a «not checked» is still 0x0E at the fixed second (unchanged), so the two outcomes stay distinct for the right reasons.
 *
 * BUILD AND RUN (a few seconds; the real rcp.c of BOTH trees; run from the root of the tree):
 *   for T in src benches/rcp; do F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Wno-unused-parameter -I$T -Ibenches/fuzz/rcp-msg" && gcc $F -c benches/unit/paused-refusal/test.c -o /tmp/pr-t.o && gcc $F -c $T/rcp.c -o /tmp/pr-r.o &&
 *      gcc $F -c benches/fuzz/rcp-msg/stubs_log.c -o /tmp/pr-l.o && gcc -fsanitize=address,undefined /tmp/pr-t.o /tmp/pr-r.o /tmp/pr-l.o -o /tmp/pr-test &&
 *      /tmp/pr-test || exit 1; done
 * Exit code 0 green, 1 red, 3 not all checks ran.
 */
#include "rcp.h"
#include <stdio.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 11

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

enum { T_HELLO = 0x0001, T_HERE_I_AM = 0x0002, T_CREDENTIALS = 0x0003,
       T_ADMITTED = 0x0004, T_REJECTED = 0x0005 };

struct guest {
	int here_i_am, admitted, rejected;
	int reason; /* the byte of the last REJECTED, -1 = none */
};
static bool no_ask; /* D4b: open_waiting() leaves the asynchronous hook out */

static void o_send(void *ctx, const uint8_t *data, size_t len)
{
	struct guest *o = ctx;
	if (len < 6)
		return;
	uint16_t kind = (uint16_t)((data[0] << 8) | data[1]);
	if (kind == T_HERE_I_AM)
		o->here_i_am++;
	else if (kind == T_ADMITTED)
		o->admitted++;
	else if (kind == T_REJECTED) {
		o->rejected++;
		o->reason = len > 6 ? data[6] : -1;
	}
}
static void o_close(void *ctx, uint8_t reason) { (void)ctx; (void)reason; }
static void o_log(void *ctx, const char *line) { (void)ctx; (void)line; }
static bool o_ask(void *ctx, const char *u, const char *p, uint64_t *ticket)
{
	(void)ctx;
	(void)u;
	(void)p;
	*ticket = 77;
	return true;
}

static size_t put_str(uint8_t *b, size_t i, const char *t)
{
	size_t n = strlen(t);
	b[i++] = (uint8_t)(n >> 8);
	b[i++] = (uint8_t)(n & 0xFF);
	memcpy(b + i, t, n);
	return i + n;
}

static size_t wrap(uint8_t *b, uint16_t kind, const uint8_t *body, size_t len)
{
	b[0] = (uint8_t)(kind >> 8);
	b[1] = (uint8_t)(kind & 0xFF);
	b[2] = (uint8_t)((len >> 24) & 0xFF);
	b[3] = (uint8_t)((len >> 16) & 0xFF);
	b[4] = (uint8_t)((len >> 8) & 0xFF);
	b[5] = (uint8_t)(len & 0xFF);
	memcpy(b + 6, body, len);
	return 6 + len;
}

/* HELLO, then CREDENTIALS on the asynchronous road (PAM asked, ticket 77) */
static rcp_session *open_waiting(const char *provenance, uint64_t now, struct guest *o,
                                 rcp_hooks *g)
{
	static const char *const ENTRIES[] = {
	    "video.codec", "hevc,av1", "video.depth", "8,10",
	    "audio.codec", "opus,pcm", "video.level", "5.1",
	    "video.max_size", "3840x2160", "clipboard.text", "yes",
	    "input.touch", "no", "client.name", "01-b8-logged-in-test", NULL};
	uint8_t body[1100], frame[1200];
	size_t i = 0;
	int how_many = 0;

	memset(o, 0, sizeof *o);
	o->reason = -1;
	memset(g, 0, sizeof *g);
	g->ctx = o;
	g->send_msg = o_send;
	g->close = o_close;
	g->record = o_log;
	g->ask_verify = no_ask ? NULL : o_ask;
	rcp_session *s = rcp_open(g, provenance, now);
	if (!s)
		return NULL;
	for (int k = 0; ENTRIES[k]; k += 2)
		how_many++;
	body[i++] = 0;
	body[i++] = 1;
	body[i++] = (uint8_t)(how_many >> 8);
	body[i++] = (uint8_t)(how_many & 0xFF);
	for (int k = 0; ENTRIES[k]; k += 2) {
		i = put_str(body, i, ENTRIES[k]);
		i = put_str(body, i, ENTRIES[k + 1]);
	}
	rcp_receive(s, frame, wrap(frame, T_HELLO, body, i), now);
	if (o->here_i_am != 1) {
		rcp_free(s);
		return NULL;
	}
	i = put_str(body, 0, "utente-di-prova");
	i = put_str(body, i, "una-password");
	rcp_receive(s, frame, wrap(frame, T_CREDENTIALS, body, i), now);
	return s;
}

int main(void)
{
	const uint64_t T = 91000000;
	struct guest o;
	rcp_hooks g;
	rcp_session *s;

	setvbuf(stdout, NULL, _IONBF, 0);
	rcp_unblock("[10.0.31.1]", T);
	rcp_unblock("[10.0.31.2]", T);
	rcp_unblock("[10.0.31.3]", T);
	rcp_unblock("[10.0.31.4]", T);

	printf("  a wrong password and a pause leave alike\n");
	s = open_waiting("[10.0.31.1]:1", T, &o, &g);
	if (s)
		rcp_verdict(s, 77, false, T + 300);
	rcp_time(s, T + 2499);
	require(s && o.rejected == 0, "a wrong password: nothing yet at 2499 ms (the floor is 2.5 s)");
	rcp_time(s, T + 2501);
	require(s && o.rejected == 1 && o.reason == 0x07, "…REJECTED 0x07 just after 2500 ms");
	rcp_free(s);

	s = open_waiting("[10.0.31.2]:1", T, &o, &g);
	rcp_refusal_paused(77);
	if (s)
		rcp_verdict(s, 77, false, T + 300);
	rcp_refusal_paused(0);
	rcp_time(s, T + 1001);
	require(s && o.rejected == 0, "a PAUSED verdict: nothing at 1 s (it is NOT the 0x0E of «not checked»)");
	rcp_time(s, T + 2499);
	require(s && o.rejected == 0, "…nor at 2499 ms");
	rcp_time(s, T + 2501);
	require(s && o.rejected == 1 && o.reason == 0x07 && !rcp_logged_in(s), "…REJECTED 0x07 just after 2500 ms: the same byte and the same instant as a wrong password");
	rcp_free(s);

	printf("  the pause is counted by the rule of §11.47 B (an unknown key: like any refusal; a key that logged in lately: not)\n");
	{
		int paused_until_ban = -1, wrong_until_ban = -1;

		for (int k = 0; k < 20 && paused_until_ban < 0; k++) {
			uint64_t t = T + 10000 + (uint64_t)k * 5000;

			s = open_waiting("[10.0.31.3]:1", t, &o, &g);
			if (!s) {
				paused_until_ban = k;
				break;
			}
			rcp_refusal_paused(77);
			rcp_verdict(s, 77, false, t + 300);
			rcp_refusal_paused(0);
			rcp_time(s, t + 2501);
			if (o.reason != 0x07)
				paused_until_ban = k;
			rcp_free(s);
		}
		for (int k = 0; k < 20 && wrong_until_ban < 0; k++) {
			uint64_t t = T + 10000 + (uint64_t)k * 5000;

			s = open_waiting("[10.0.31.4]:1", t, &o, &g);
			if (!s) {
				wrong_until_ban = k;
				break;
			}
			rcp_verdict(s, 77, false, t + 300);
			rcp_time(s, t + 2501);
			if (o.reason != 0x07)
				wrong_until_ban = k;
			rcp_free(s);
		}
		require(paused_until_ban >= 0 && paused_until_ban == wrong_until_ban,
		        "from a key that never logged in, repeated pauses BAN after exactly as many tries as wrong passwords do (no oracle: a name that does not exist and a paused one are banned alike)");
	}
	{
		bool banned = false;

		rcp_unblock("[10.0.31.7]", T);
		s = open_waiting("[10.0.31.7]:1", T, &o, &g);
		if (s)
			rcp_verdict(s, 77, true, T + 300);
		rcp_time(s, T + 1001);
		require(s && o.admitted == 1, "(setup) the key logs in once: it is a KNOWN key now");
		rcp_free(s);
		for (int k = 0; k < 20 && !banned; k++) {
			uint64_t t = T + 20000 + (uint64_t)k * 5000;

			s = open_waiting("[10.0.31.7]:1", t, &o, &g);
			if (!s) {
				banned = true;
				break;
			}
			rcp_refusal_paused(77);
			rcp_verdict(s, 77, false, t + 300);
			rcp_refusal_paused(0);
			rcp_time(s, t + 2501);
			banned = o.reason != 0x07;
			rcp_free(s);
		}
		require(!banned, "from a key that logged in lately twenty pauses ban nobody (§11.47 B: the owner does not ban himself)");
	}

	printf("  the orphan road (the client hung up)\n");
	{
		char rh[32];

		rcp_unblock("10.0.31.5", T);
		for (int k = 0; k < 20; k++) {
			rcp_refusal_paused(500 + (uint64_t)k);
			rcp_orphan_verdict("utente-di-prova", "10.0.31.5:1", false, false, 500 + (uint64_t)k, T + 100000 + (uint64_t)k * 1000, NULL, NULL);
			rcp_refusal_paused(0);
		}
		snprintf(rh, sizeof rh, "10.0.31.5");
		require(rcp_banned(rh, T + 140000, NULL), "an unknown key: twenty orphan pauses count and the key is banned, like plain orphan refusals");
		rcp_unblock("10.0.31.8", T);
		s = open_waiting("[10.0.31.8]:1", T, &o, &g);
		if (s)
			rcp_verdict(s, 77, true, T + 300);
		rcp_time(s, T + 1001);
		rcp_free(s);
		for (int k = 0; k < 20; k++) {
			rcp_refusal_paused(600 + (uint64_t)k);
			rcp_orphan_verdict("utente-di-prova", "10.0.31.8:1", false, false, 600 + (uint64_t)k, T + 100000 + (uint64_t)k * 1000, NULL, NULL);
			rcp_refusal_paused(0);
		}
		snprintf(rh, sizeof rh, "10.0.31.8");
		require(!rcp_banned(rh, T + 140000, NULL), "a key that logged in lately: orphan pauses count nothing");
	}

	printf("  «not checked» is unchanged\n");
	rcp_unblock("[10.0.31.6]", T);
	s = open_waiting("[10.0.31.6]:1", T, &o, &g);
	rcp_refusal_unchecked(77);
	if (s)
		rcp_verdict(s, 77, false, T + 300);
	rcp_refusal_unchecked(0);
	rcp_time(s, T + 1001);
	require(s && o.rejected == 1 && o.reason == 0x0E, "a «not checked» is still 0x0E at the fixed second");
	rcp_free(s);

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
