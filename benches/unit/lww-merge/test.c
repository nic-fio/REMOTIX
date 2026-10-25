/*
 * test.c — "last one wins" messages are MERGED, not dropped, when the bucket is empty (1.5, reading of rcp.c, B1).
 *
 * VIEW, LAYOUT and PACE are STATE: the last of a burst is the one that matters. The ceiling used to drop whatever was over the rate, so a burst whose last message was
 * dropped left the server on the old state (a layout never changed, a visibility lost) until the client sent another. Now the last of each kind is kept and applied
 * when the bucket has a token again (rcp_time -> lww_apply), through the same path as a message from the wire.
 *
 * The REAL rcp.c is #included (src/ or the twin, chosen by -I); the hooks record what reaches the stage.
 *   1. LAYOUT, bucket empty: "us", "it", "de" in one burst reach nothing at once; a second later exactly ONE is applied, "de", and the session's layout is "de";
 *   2. PACE, bucket empty: 15, 20, 24 frames/s: only the last (24) ever reaches the stage;
 *   3. with a full bucket every message is applied as before (nothing is kept: the merge is only for the over-rate ones);
 *   4. a kept message is forgotten when the session is no longer active (no apply after the end);
 *   5. the apply does not touch a PARTIAL message waiting in the session's buffer: half a header received, the kept LAYOUT applied, the rest arrives and the
 *      message is parsed normally;
 *   6. REQUEST_KEY is NOT merged (it is the same as one the client never sent): over the rate it is dropped and nothing is kept.
 *
 * BUILD AND RUN (a second; from the root of the tree):
 *   for T in src benches/rcp; do F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Wno-unused-parameter -I$T -Ibenches/fuzz/rcp-msg" && gcc $F -c benches/unit/lww-merge/test.c -o /tmp/lw-t.o && gcc $F -c benches/fuzz/rcp-msg/stubs_log.c -o /tmp/lw-l.o &&
 *      gcc -fsanitize=address,undefined /tmp/lw-t.o /tmp/lw-l.o -o /tmp/lw-test && /tmp/lw-test || exit 1; done
 */
#include "rcp.c"

#include <stdio.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static char layouts[16][8];
static int n_layouts;
static unsigned paces[16];
static int n_paces;

static int h_exists(void *c, const char *name) { (void)c; (void)name; return 1; }
static bool h_layout(void *c, const char *name)
{
	(void)c;
	if (n_layouts < 16)
		snprintf(layouts[n_layouts++], sizeof layouts[0], "%s", name);
	return true;
}
static bool h_pace(void *c, uint16_t v)
{
	(void)c;
	if (n_paces < 16)
		paces[n_paces++] = v;
	return true;
}
static void h_send(void *c, const uint8_t *d, size_t n) { (void)c; (void)d; (void)n; }
static void h_close(void *c, uint8_t r) { (void)c; (void)r; }
static void h_record(void *c, const char *l) { (void)c; (void)l; }

static rcp_session *fresh(void)
{
	rcp_hooks g;
	rcp_session *s;

	memset(&g, 0, sizeof g);
	g.send_msg = h_send;
	g.close = h_close;
	g.record = h_record;
	g.layout_exists = h_exists;
	g.layout = h_layout;
	g.pace = h_pace;
	s = rcp_open(&g, "192.0.2.9", 1000);
	s->state = S_ACTIVE;
	s->session_sent = true;
	s->pace_declared = true;  /* video.pace negotiated on both sides (13.2) */
	s->pace_client = true;
	n_layouts = n_paces = 0;
	return s;
}

static void empty(rcp_session *s, enum msg_class c, uint64_t now)
{
	struct msg_gate_closed cl;
	unsigned per, burst;

	msg_class_rate(c, &per, &burst);
	for (unsigned i = 0; i < burst + 10; i++)
		(void)msg_gate_admit(&s->gate[c], now, per, burst, &cl);
}

static size_t wrap(uint8_t *b, uint16_t kind, const uint8_t *body, size_t len)
{
	b[0] = (uint8_t)(kind >> 8);
	b[1] = (uint8_t)kind;
	b[2] = (uint8_t)(len >> 24);
	b[3] = (uint8_t)(len >> 16);
	b[4] = (uint8_t)(len >> 8);
	b[5] = (uint8_t)len;
	memcpy(b + 6, body, len);
	return 6 + len;
}

static void send_layout(rcp_session *s, const char *name, uint64_t now)
{
	uint8_t body[16], frame[32];
	size_t n = strlen(name);

	body[0] = (uint8_t)(n >> 8);
	body[1] = (uint8_t)n;
	memcpy(body + 2, name, n);
	s->last_life = now;
	(void)rcp_receive(s, frame, wrap(frame, T_LAYOUT, body, 2 + n), now);
}

static void send_pace(rcp_session *s, unsigned fps, uint64_t now)
{
	uint8_t body[2] = {(uint8_t)(fps >> 8), (uint8_t)fps}, frame[16];

	s->last_life = now;
	(void)rcp_receive(s, frame, wrap(frame, T_PACE, body, 2), now);
}

static void tick(rcp_session *s, uint64_t now)
{
	s->last_life = now;
	(void)rcp_time(s, now);
}

int main(void)
{
	rcp_session *s;
	const uint64_t t = 100000;

	/* 1 */
	s = fresh();
	empty(s, MC_LAYOUT, t);
	send_layout(s, "us", t);
	send_layout(s, "it", t);
	send_layout(s, "de", t);
	CHECK(n_layouts == 0, "1: three LAYOUT in a burst with the bucket empty reach nothing at once");
	tick(s, t + 100);
	CHECK(n_layouts == 0, "1: and none 100 ms later (the bucket gives 5 a second: no token yet)");
	tick(s, t + 1000);
	CHECK(n_layouts == 1 && strcmp(layouts[0], "de") == 0, "1: a second later exactly ONE is applied, the LAST one (de)");
	CHECK(strcmp(s->layout, "de") == 0, "1: and it is the layout of the session");
	tick(s, t + 3000);
	CHECK(n_layouts == 1, "1: it is applied once, not again");
	rcp_free(s);

	/* 2 */
	s = fresh();
	empty(s, MC_PACE, t);
	send_pace(s, 15, t);
	send_pace(s, 20, t);
	send_pace(s, 24, t);
	CHECK(n_paces == 0, "2: three PACE with the bucket empty reach nothing at once");
	tick(s, t + 1000);
	tick(s, t + 1500);
	CHECK(n_paces >= 1, "2: later a PACE reaches the stage");
	{
		int others = 0;

		for (int i = 0; i < n_paces; i++)
			others += paces[i] != 24;
		CHECK(others == 0, "2: and it is only the LAST (24): the older ones were merged away");
	}
	rcp_free(s);

	/* 3 */
	s = fresh();
	send_layout(s, "us", t);
	send_layout(s, "it", t);
	CHECK(n_layouts == 2 && strcmp(layouts[0], "us") == 0 && strcmp(layouts[1], "it") == 0, "3: with a full bucket every LAYOUT is applied as before");
	CHECK(!s->lww[1].has && !s->lww[0].has && !s->lww[2].has, "3: and nothing is kept");
	rcp_free(s);

	/* 4 */
	s = fresh();
	empty(s, MC_LAYOUT, t);
	send_layout(s, "fr", t);
	CHECK(s->lww[1].has, "4: (setup) the LAYOUT is kept");
	s->state = S_DETACHED;
	tick(s, t + 1000);
	CHECK(n_layouts == 0 && !s->lww[1].has, "4: no longer active: it is forgotten, not applied");
	rcp_free(s);

	/* 5 */
	s = fresh();
	empty(s, MC_LAYOUT, t);
	send_layout(s, "es", t);
	{
		uint8_t frame[16] = {0};
		uint8_t body[4] = {0, 0, 0, 5};
		size_t n = wrap(frame, T_REQUEST_KEY, body, 4);

		s->last_life = t;
		(void)rcp_receive(s, frame, 3, t + 10); /* half a header */
		CHECK(s->acc_len == 3, "5: (setup) half a header waits in the buffer");
		tick(s, t + 1000);
		CHECK(n_layouts == 1 && strcmp(layouts[0], "es") == 0, "5: the kept LAYOUT is applied");
		CHECK(s->acc_len == 3 && s->acc[0] == 0x00 && s->acc[1] == (uint8_t)T_REQUEST_KEY, "5: and the half header is exactly where it was");
		s->never_sent_key = true; /* the first request is accepted whatever the grace says */
		(void)rcp_receive(s, frame + 3, n - 3, t + 1100);
		CHECK(s->needs_key, "5: the rest arrives and the message is parsed normally (a keyframe is asked)");
	}
	rcp_free(s);

	/* 6 */
	s = fresh();
	empty(s, MC_REQUEST_KEY, t);
	{
		uint8_t body[4] = {0, 0, 0, 5}, frame[16];

		s->never_sent_key = true;
		s->last_life = t;
		(void)rcp_receive(s, frame, wrap(frame, T_REQUEST_KEY, body, 4), t);
	}
	CHECK(!s->needs_key && !s->lww[0].has && !s->lww[1].has && !s->lww[2].has, "6: REQUEST_KEY over the rate is dropped and nothing is kept");
	rcp_free(s);

	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
