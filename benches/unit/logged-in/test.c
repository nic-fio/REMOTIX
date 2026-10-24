/* test.c — a login is «logged in» only after ADMITTED
 * (review of eab9623a).
 *
 * ⛔ `wt_watch_locals()` (webtransport.c) asks logind whether a user has a LOCAL
 *    graphical session, and sends the remote one away with 0x04 if so.  The
 *    user name is set at CREDENTIALS: a login still waiting for PAM's verdict
 *    sent away there skipped the fixed second, told a guesser WITHOUT the
 *    password that the account exists and is logged in locally (§4.4), and
 *    lost its «no».  The sweep now asks only sessions `rcp_logged_in()`
 *    reports — this bench is that function's certificate:
 *
 *   1. waiting for the verdict: NOT logged in;
 *   2. a yes in hand, before the fixed second: NOT logged in;
 *   3. after ADMITTED: logged in;
 *   4. a finished session: not logged in;
 *   5. ⛔ the check that says NO: a wrong password is never logged in;
 *   6-7. (D4b of §11.50) the helper's «not checked» — `rcp_refusal_unchecked(ticket)` around the verdict — is refused as OURS,
 *        `0x0E` and never `0x07`, and not logged in;
 *   8-9. (D4b) a host WITHOUT the asynchronous hook (the helper not started) has its login refused the same way, `0x0E`:
 *        there is no synchronous PAM fallback any more.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; the real rcp.c of BOTH trees, src and the benches/rcp twin; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=2 --memory=2g -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && rc=0 &&
 *     for T in src benches/rcp; do
 *       echo "== $T" &&
 *       F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
 *          -I/albero/$T -I/albero/benches/fuzz/rcp-msg" &&
 *       clang $F -c /albero/benches/unit/logged-in/test.c -o t.o && clang $F -c /albero/$T/rcp.c -o r.o &&
 *       clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *       clang -fsanitize=address,undefined t.o r.o l.o -o test && ./test || rc=1;
 *     done; exit $rc'
 * Exit code 0 green, 1 red, 3 not all checks ran.
 */
#include "rcp.h"
#include <stdio.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 9

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
	rcp_unblock("[10.0.29.1]", T);
	rcp_unblock("[10.0.29.2]", T);

	printf("  a right password\n");
	s = open_waiting("[10.0.29.1]:1", T, &o, &g);
	require(s && !rcp_logged_in(s), "waiting for PAM's verdict: NOT logged in");
	if (s)
		rcp_verdict(s, 77, true, T + 300);
	require(s && !rcp_logged_in(s) && o.admitted == 0,
	        "a yes in hand, before the fixed second: NOT logged in (the name is only claimed)");
	rcp_time(s, T + 1001);
	require(s && o.admitted == 1 && rcp_logged_in(s), "after ADMITTED: logged in");
	rcp_dismiss(s, RCP_LOCAL_SESSION_PREVAILED, "a local session");
	require(s && !rcp_logged_in(s), "a finished session: not logged in");
	rcp_free(s);

	printf("  a check the helper could not make (D4b)\n");
	rcp_unblock("[10.0.29.3]", T);
	s = open_waiting("[10.0.29.3]:1", T, &o, &g);
	rcp_refusal_unchecked(77);
	if (s)
		rcp_verdict(s, 77, false, T + 300);
	rcp_refusal_unchecked(0);
	rcp_time(s, T + 1001);
	require(s && o.rejected == 1 && o.reason == 0x0E && !rcp_logged_in(s),
	        "a «not checked» is refused as OURS: 0x0E, not 0x07, not logged in");
	rcp_free(s);
	/* …and it was not counted: 20 more «not checked» from the same key would have banned it if they were failures */
	{
		bool banned = false;
		for (int k = 0; k < 20 && !banned; k++) {
			s = open_waiting("[10.0.29.3]:1", T + 2000 + (uint64_t)k * 2000, &o, &g);
			if (!s) {
				banned = true;
				break;
			}
			rcp_refusal_unchecked(77);
			rcp_verdict(s, 77, false, T + 2300 + (uint64_t)k * 2000);
			rcp_refusal_unchecked(0);
			rcp_time(s, T + 3001 + (uint64_t)k * 2000);
			banned = o.reason != 0x0E;
			rcp_free(s);
		}
		require(!banned, "twenty «not checked» in a row ban nobody (always 0x0E, never the ban's 0x08)");
	}

	printf("  a host without the asynchronous hook (D4b)\n");
	rcp_unblock("[10.0.29.4]", T);
	no_ask = true;
	s = open_waiting("[10.0.29.4]:1", T, &o, &g);
	no_ask = false;
	rcp_time(s, T + 1001);
	require(s && o.rejected == 1 && o.reason == 0x0E && !rcp_logged_in(s),
	        "no helper hook: refused as OURS (0x0E), no synchronous PAM");
	rcp_free(s);
	{
		bool banned = false;
		no_ask = true;
		for (int k = 0; k < 20 && !banned; k++) {
			s = open_waiting("[10.0.29.4]:1", T + 2000 + (uint64_t)k * 2000, &o, &g);
			if (!s) {
				banned = true;
				break;
			}
			rcp_time(s, T + 3001 + (uint64_t)k * 2000);
			banned = o.reason != 0x0E;
			rcp_free(s);
		}
		no_ask = false;
		require(!banned, "twenty refusals for a missing hook ban nobody (always 0x0E)");
	}

	printf("  a wrong password\n");
	s = open_waiting("[10.0.29.2]:1", T, &o, &g);
	if (s)
		rcp_verdict(s, 77, false, T + 300);
	rcp_time(s, T + 1001);
	require(s && o.rejected == 1 && !rcp_logged_in(s),
	        "⛔ the check that says NO: a wrong password is never logged in");
	rcp_free(s);

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
