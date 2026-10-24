/* 01-b8-logged-in-test.c — a login is «logged in» only after ADMITTED
 * (review of eab9623a).
 *
 *   gcc -std=gnu11 -Wall -Wextra -Ibenches/rcp -o /tmp/pli \
 *       benches/01-b8-logged-in-test.c benches/rcp/rcp.c && /tmp/pli
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
 *   5. ⛔ the check that says NO: a wrong password is never logged in.
 *
 * Exit status: 0 green, 1 red, 3 not all checks ran. */
#include "rcp.h"
#include <stdio.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 5

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
};

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
	else if (kind == T_REJECTED)
		o->rejected++;
}
static void o_close(void *ctx, uint8_t reason) { (void)ctx; (void)reason; }
static void o_log(void *ctx, const char *line) { (void)ctx; (void)line; }
static bool o_verify(void *ctx, const char *u, const char *p)
{
	(void)ctx;
	(void)u;
	(void)p;
	return false; /* never used: the asynchronous road below */
}
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
	memset(g, 0, sizeof *g);
	g->ctx = o;
	g->send_msg = o_send;
	g->close = o_close;
	g->record = o_log;
	g->verify = o_verify;
	g->ask_verify = o_ask;
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
