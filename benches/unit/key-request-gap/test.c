/*
 * test.c — REQUEST_KEY is limited to one keyframe per V_KEY_ASK_GAP_MS and a request inside the gap is NEVER LOST (review of 122dca24).
 * The first version ignored every request inside the gap; a client whose NEW gap came 60 ms after the previous request would have waited
 * for a picture that never came (the page does not ask twice for the same gap).  Now: if a keyframe is still owed the request is redundant and
 * ignored; otherwise it is DEFERRED and rcp_time() starts the keyframe when the gap ends, unless a keyframe went out in the meantime.
 *
 * The REAL rcp.c is #included (src/ or the twin, chosen by -I); a session in S_ACTIVE receives real REQUEST_KEY messages through rcp_receive()
 * and rcp_time() runs on the clock the test sets.  "A keyframe goes out" is simulated as the product does it: key_paid() and last_key_ms.
 *   1. the first request is accepted at once (a keyframe is owed);
 *   2. a request inside the gap, with no keyframe owed, is DEFERRED: nothing owed yet; one tick before the end of the gap still nothing; at the
 *      end of the gap rcp_time() makes the keyframe owed (the request was not lost);
 *   3. a request inside the gap while a keyframe is still owed is ignored and defers nothing;
 *   4. if a keyframe goes out after the request came, the deferral is dropped at the end of the gap (it was answered), and no extra keyframe is owed;
 *   5. a request every millisecond for 20 s, each keyframe going out at once: at most one keyframe per gap, i.e. no more than 20000/100 + 1;
 *   6. and no request is ever lost: after the storm stops, one more tick past the gap leaves nothing deferred.
 *
 * BUILD AND RUN (a second; from the root of the tree):
 *   for T in src benches/rcp; do F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Wno-unused-parameter -I$T -Ibenches/fuzz/rcp-msg" &&
 *      gcc $F -c benches/unit/key-request-gap/test.c -o /tmp/kr-t.o && gcc $F -c benches/fuzz/rcp-msg/stubs_log.c -o /tmp/kr-l.o &&
 *      gcc -fsanitize=address,undefined /tmp/kr-t.o /tmp/kr-l.o -o /tmp/kr-test && /tmp/kr-test $T/rcp.c || exit 1; done
 */
#include "rcp.c"

#include <stdio.h>

static int checks, bad;
#define CHECK(cond, what) do { checks++; if (!(cond)) { bad++; printf("  FAIL %s:%d  %s\n", __FILE__, __LINE__, what); } } while (0)

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
	s = rcp_open(&g, "192.0.2.7", 1000);
	s->state = S_ACTIVE;
	s->session_sent = true;
	s->never_sent_key = false;
	s->last_key_ms = 1;       /* a keyframe long ago: the grace (200 ms) has passed */
	s->last_key_number = 5;
	s->needs_key = false;
	return s;
}

static void request(rcp_session *s, uint32_t last_number, uint64_t now)
{
	uint8_t m[10] = {0x00, 0x0D, 0, 0, 0, 4};

	m[6] = (uint8_t)(last_number >> 24); m[7] = (uint8_t)(last_number >> 16); m[8] = (uint8_t)(last_number >> 8); m[9] = (uint8_t)last_number;
	s->last_life = now;
	(void)rcp_receive(s, m, sizeof m, now);
}

static void tick(rcp_session *s, uint64_t now)
{
	s->last_life = now;
	(void)rcp_time(s, now);
}

static char *slurp(const char *path)
{
	FILE *f = fopen(path, "r");
	long n;
	char *b;

	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	b = malloc((size_t)n + 1);
	if (b && fread(b, 1, (size_t)n, f) != (size_t)n) {
		free(b);
		b = NULL;
	}
	if (b)
		b[n] = 0;
	fclose(f);
	return b;
}

int main(int argc, char **argv)
{
	rcp_session *s;
	const uint64_t T0 = 100000;

	/* 1 */
	s = fresh();
	request(s, 10, T0);
	CHECK(s->needs_key, "1: the first request is accepted at once");
	rcp_free(s);

	/* 2 */
	s = fresh();
	request(s, 10, T0);
	key_paid(s); /* the keyframe went out whole */
	s->last_key_ms = T0 + 5;
	s->last_key_number = 6;
	request(s, 20, T0 + 50); /* inside the gap, nothing owed: deferred */
	CHECK(!s->needs_key && s->key_deferred, "2: inside the gap with nothing owed the request is DEFERRED, not lost");
	tick(s, T0 + 99);
	CHECK(!s->needs_key && s->key_deferred, "2: one millisecond before the end of the gap nothing is started yet");
	/* a keyframe did NOT go out in the meantime: serve it */
	s->last_key_ms = T0 + 5;
	tick(s, T0 + 100);
	CHECK(s->needs_key && !s->key_deferred, "2: at the end of the gap rcp_time() makes the keyframe owed");
	CHECK(s->key_asked_ms == T0 + 100, "2: and the gap restarts from there");
	rcp_free(s);

	/* 3 */
	s = fresh();
	request(s, 10, T0);
	request(s, 20, T0 + 30); /* a keyframe is still owed (needs_key stayed true) */
	CHECK(s->needs_key && !s->key_deferred, "3: a keyframe still owed answers the request: ignored, nothing deferred");
	rcp_free(s);

	/* 4 */
	s = fresh();
	request(s, 10, T0);
	key_paid(s);
	s->last_key_ms = T0 + 5;
	s->last_key_number = 6;
	request(s, 20, T0 + 50);
	CHECK(s->key_deferred, "4: deferred");
	key_paid(s);
	s->last_key_ms = T0 + 70; /* a keyframe went out after the request came */
	s->last_key_number = 7;
	tick(s, T0 + 100);
	CHECK(!s->key_deferred && !s->needs_key, "4: it was answered by the keyframe that went out: dropped, no extra keyframe");
	rcp_free(s);

	/* 5 and 6 */
	s = fresh();
	{
		unsigned started = 0;
		uint64_t t;

		for (t = T0; t < T0 + 20000; t++) {
			request(s, 100 + (uint32_t)(t - T0), t); /* every millisecond; last_number always newer: never a duplicate */
			tick(s, t);
			if (s->needs_key) {
				started++;
				key_paid(s); /* the keyframe goes out at once */
				s->last_key_ms = t;
				s->last_key_number = 100 + (uint32_t)(t - T0);
			}
		}
		CHECK(started <= 20000 / 100 + 1, "5: at most one keyframe per gap under a request every millisecond");
		CHECK(started >= 20000 / 100 - 5, "5: and the gap is used (about one every 100 ms)");
		tick(s, t + 100);
		CHECK(!s->key_deferred, "6: after the storm nothing is left deferred");
	}
	rcp_free(s);

	if (argc > 1) {
		char *src = slurp(argv[1]);

		CHECK(src != NULL, "source readable");
		if (src) {
			const char *g = strstr(src, "#define V_KEY_ASK_GAP_MS ");
			const char *c = strstr(src, "AT MOST ONE REQUEST_KEY PER THIS MANY ms STARTS A KEYFRAME");

			CHECK(g && atoi(g + strlen("#define V_KEY_ASK_GAP_MS ")) < 150, "the gap is under the transport's 150 ms");
			CHECK(c != NULL && g && c < g, "the comment above the gap says it STARTS a keyframe and that a request inside it is deferred, not lost");
			free(src);
		}
	}
	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
