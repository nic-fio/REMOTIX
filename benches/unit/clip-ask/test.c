/*
 * test.c — a CLIPBOARD_ASK is never lost to the rate of the clipboard (1.5, reading of rcp.c, B2).
 *
 * The page asks AT ONCE for every announcement of the server (once), and RCP.md 7.4 has no refusal an ASK can be answered with: an empty TEXT does not match
 * the announced length and the page closes the session, and silence leaves that transfer's text unfetched. The bucket of the clipboard (ANNOUNCE and ASK together,
 * 10 a second, burst 20) used to discard an ASK in silence when ANNOUNCEs had spent the tokens. Now the first CLIPBOARD_ASK_FREE (2) requests for the same transfer
 * are served whatever the bucket says; only the repeats past them are subject to it, and what it refuses is written in the log.
 *
 * The REAL rcp.c is #included (src/ or the twin, chosen by -I), a session has an announced text and the clipboard hooks count what is written on the stream.
 *   1. with the bucket EMPTY, the first ASK for a transfer is served (a TEXT leaves) and so is the second;
 *   2. the third (past CLIPBOARD_ASK_FREE) is ignored, and the line says so — the client's session is kept;
 *   3. another transfer, with the bucket still empty, is served again (the count is per transfer);
 *   4. with the bucket FULL the third is served too (the cap is for floods, not for a repeat);
 *   5. an ASK for an identifier that was never announced is still a violation (the session ends) even with the bucket empty — the cheap check comes first;
 *   6. a flood of 1000 ASK for ONE transfer with the bucket empty serves 2 and ignores the rest (the amplification is bounded), and logs a few lines, not 1000.
 *
 * BUILD AND RUN (a second; from the root of the tree):
 *   for T in src benches/rcp; do F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Wno-unused-parameter -I$T -Ibenches/fuzz/rcp-msg" && gcc $F -c benches/unit/clip-ask/test.c -o /tmp/ca-t.o && gcc $F -c benches/fuzz/rcp-msg/stubs_log.c -o /tmp/ca-l.o &&
 *      gcc -fsanitize=address,undefined /tmp/ca-t.o /tmp/ca-l.o -o /tmp/ca-test && /tmp/ca-test || exit 1; done
 */
#include "rcp.c"

#include <stdio.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static int texts;       /* TEXT messages written on a clipboard stream */
static int ignored_lines, closes;

static bool h_open(void *c, int64_t *stream, uint64_t *remain) { (void)c; *stream = 3; *remain = 100; return true; }
static bool h_write(void *c, int64_t stream, const uint8_t *d, size_t n)
{
	(void)c;
	(void)stream;
	if (n == 6 && d[0] == 0x02 && d[1] == 0x03)
		texts++;
	return true;
}
static void h_fin(void *c, int64_t stream) { (void)c; (void)stream; }
static bool h_offer(void *c) { (void)c; return true; }
static bool h_response(void *c, uint32_t serial, const char *t, size_t n) { (void)c; (void)serial; (void)t; (void)n; return true; }
static void h_send(void *c, const uint8_t *d, size_t n) { (void)c; (void)d; (void)n; }
static void h_close(void *c, uint8_t r) { (void)c; (void)r; closes++; }
static void h_record(void *c, const char *l) { (void)c; if (strstr(l, "IGNORED") && strstr(l, "transfer")) ignored_lines++; }

static rcp_session *fresh(void)
{
	rcp_hooks g;
	rcp_session *s;

	memset(&g, 0, sizeof g);
	g.send_msg = h_send;
	g.close = h_close;
	g.record = h_record;
	g.clipboard_open = h_open;
	g.clipboard_write = h_write;
	g.clipboard_fin = h_fin;
	g.clipboard_offer = h_offer;
	g.clipboard_response = h_response;
	s = rcp_open(&g, "192.0.2.9", 1000);
	s->state = S_ACTIVE;
	s->session_sent = true;
	s->negotiate_clipboard = true;
	s->app_my_id = 3;
	s->app_text = strdup("hello");
	s->app_text_n = 5;
	texts = ignored_lines = closes = 0;
	return s;
}

static bool ask(rcp_session *s, uint32_t id, uint64_t now)
{
	uint8_t b[4] = {(uint8_t)(id >> 24), (uint8_t)(id >> 16), (uint8_t)(id >> 8), (uint8_t)id};

	return handle_clipboard(s, T_CLIPBOARD_ASK, b, 4, now);
}

static void empty_the_bucket(rcp_session *s, uint64_t now)
{
	for (int i = 0; i < 100; i++)
		(void)clipboard_over_rate(s, now);
}

int main(void)
{
	rcp_session *s;
	const uint64_t t = 50000;

	/* 1, 2, 3 */
	s = fresh();
	empty_the_bucket(s, t);
	CHECK(ask(s, 3, t) && texts == 1, "1: with the bucket EMPTY the first ASK for transfer 3 is served");
	CHECK(ask(s, 3, t) && texts == 2, "1: and the second");
	CHECK(ask(s, 3, t) && texts == 2 && ignored_lines == 1, "2: the third is ignored, and the log says so");
	CHECK(closes == 0 && s->state == S_ACTIVE, "2: the session is kept");
	CHECK(ask(s, 2, t) && texts == 3, "3: another transfer with the bucket still empty is served (the count is per transfer)");
	rcp_free(s);

	/* 4 */
	s = fresh();
	CHECK(ask(s, 3, t) && ask(s, 3, t) && ask(s, 3, t) && texts == 3, "4: with the bucket full the third is served too (the cap is for floods)");
	rcp_free(s);

	/* 5 */
	s = fresh();
	empty_the_bucket(s, t);
	CHECK(!ask(s, 9, t) && s->state == S_FINISHED, "5: an ASK for an identifier never announced ends the session, bucket empty or not");
	CHECK(texts == 0, "5: and nothing was sent");
	rcp_free(s);

	/* 6 */
	s = fresh();
	empty_the_bucket(s, t);
	for (int i = 0; i < 1000; i++)
		(void)ask(s, 3, t);
	CHECK(texts == 2, "6: a flood of 1000 ASK for one transfer, bucket empty: 2 texts, not 1000 (the amplification is bounded)");
	CHECK(ignored_lines <= (int)MSG_LINES_PER_WINDOW, "6: and a few log lines, not one per message");
	rcp_free(s);

	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
