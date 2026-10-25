/*
 * test.c — the token bucket per client and per kind of message (src/msgrate.h), audit of 25 Oct 2026, parts P/Q.
 * After login every valid message does work in the one thread of the main loop, and most write a log line; nothing limited how
 * often a client could send them.  Now each kind has a bucket with a WIDE rate; over it the message is consumed and counted, and ONE
 * line per 10 s window says how many.
 *
 * What is checked, on the REAL header (nothing copied):
 *   1. a flood of 100000 messages in one millisecond: exactly `burst` are admitted, the rest counted;
 *   2. a steady stream at the sustained rate (one message every 1000/per_s ms) is never refused, for a minute;
 *   3. after a long silence the bucket is full again, and not more than full;
 *   4. the end of the window gives the count once, and the next window starts again; a quiet window gives no summary;
 *   5. log lines: at most MSG_LINES_PER_WINDOW per window and kind, the rest counted;
 *   6. a clock that goes back gives no free credit and does not crash; counters stop at the maximum;
 *   7. the rates are WIDE: no kind is below what a hand can do (pointer >= 1000/s, key >= 100/s, wheel >= 200/s, button >= 50/s),
 *      and every kind has a burst of at least its rate;
 *   8. a person's burst of typing, pointing and wheeling is never refused (a 1 kHz mouse, 30 keys a second held, a free wheel);
 *   9. by reading the source (argv[1] = src/rcp.c, optional): handle_input() asks msg_admit() before it reads the id; its two log
 *      lines are behind msg_line(); drain() consumes an over-rate control message without running its handler, and only in S_ACTIVE;
 *      rcp_time() flushes the windows.
 *
 * BUILD AND RUN (a second; run from the root of the tree):
 *   gcc -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Isrc benches/unit/msg-rate/test.c -o /tmp/msg-rate-test && /tmp/msg-rate-test src/rcp.c src/main.c
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "msgrate.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

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

static const char *body_of(const char *src, const char *sig, size_t *len)
{
	const char *p = strstr(src, sig);
	const char *e;

	if (!p)
		return NULL;
	e = strstr(p + 1, "\n}\n");
	*len = e ? (size_t)(e - p) : strlen(p);
	return p;
}

static int count_in(const char *p, size_t n, const char *needle)
{
	int c = 0;
	size_t k = strlen(needle);

	for (const char *q = p; q && (size_t)(q - p) + k <= n; q++)
		if (!memcmp(q, needle, k))
			c++;
	return c;
}

int main(int argc, char **argv)
{
	struct msg_gate_closed cl;

	/* 1 */
	{
		struct msg_gate g = {0};
		unsigned adm = 0;

		for (int i = 0; i < 100000; i++)
			if (msg_gate_admit(&g, 5000, 100, 200, &cl))
				adm++;
		CHECK(adm == 200, "1: a flood in one millisecond admits exactly the burst");
		CHECK(g.dropped == 100000u - 200u, "1: the rest is counted");
	}
	/* 2 */
	{
		struct msg_gate g = {0};
		unsigned refused = 0;

		for (uint64_t t = 1000; t < 61000; t += 10) /* 100 a second */
			if (!msg_gate_admit(&g, t, 100, 200, &cl))
				refused++;
		CHECK(refused == 0, "2: a steady stream at the sustained rate is never refused");
	}
	/* 3 */
	{
		struct msg_gate g = {0};
		unsigned adm = 0;

		for (int i = 0; i < 1000; i++)
			(void)msg_gate_admit(&g, 1000, 50, 100, &cl);
		for (int i = 0; i < 1000; i++)
			if (msg_gate_admit(&g, 1000 + 3600u * 1000u, 50, 100, &cl))
				adm++;
		CHECK(adm == 100, "3: after an hour of silence the bucket is full again, and not more than full");
	}
	/* 4 */
	{
		struct msg_gate g = {0};

		for (int i = 0; i < 1000; i++)
			(void)msg_gate_admit(&g, 2000, 50, 100, &cl);
		CHECK(cl.dropped == 0, "4: the first window gives no summary");
		(void)msg_gate_admit(&g, 2000 + MSG_WINDOW_MS, 50, 100, &cl);
		CHECK(cl.dropped == 900 && cl.hidden == 0, "4: the end of the window gives the count (1000 - burst 100)");
		(void)msg_gate_admit(&g, 2000 + MSG_WINDOW_MS + 1, 50, 100, &cl);
		CHECK(cl.dropped == 0 && cl.hidden == 0, "4: and only once");
		{
			struct msg_gate q = {0};

			(void)msg_gate_admit(&q, 100, 50, 100, &cl);
			(void)msg_gate_admit(&q, 100 + MSG_WINDOW_MS, 50, 100, &cl);
			CHECK(cl.dropped == 0 && cl.hidden == 0, "4: a quiet window gives no summary");
		}
		msg_gate_flush(&g, 2000 + 3 * MSG_WINDOW_MS, &cl);
		CHECK(cl.dropped == 0, "4: a flush after the summary was given has nothing more");
	}
	/* 4b: the periodic flush closes a window with no message asking */
	{
		struct msg_gate g = {0};

		for (int i = 0; i < 300; i++)
			(void)msg_gate_admit(&g, 7000, 10, 20, &cl);
		msg_gate_flush(&g, 7000 + MSG_WINDOW_MS + 5, &cl);
		CHECK(cl.dropped == 280, "4b: the periodic flush gives the summary without a new message");
	}
	/* 5 */
	{
		struct msg_gate g = {0};
		unsigned w = 0;

		for (int i = 0; i < 5000; i++)
			if (msg_gate_line(&g))
				w++;
		CHECK(w == MSG_LINES_PER_WINDOW, "5: at most MSG_LINES_PER_WINDOW lines per window");
		CHECK(g.hidden == 5000 - MSG_LINES_PER_WINDOW, "5: the rest is counted");
		(void)msg_gate_admit(&g, 50, 10, 20, &cl); /* starts the window */
		msg_gate_flush(&g, 50 + MSG_WINDOW_MS, &cl);
		w = 0;
		for (int i = 0; i < 50; i++)
			if (msg_gate_line(&g))
				w++;
		CHECK(w == MSG_LINES_PER_WINDOW, "5: the next window writes lines again");
	}
	/* 6 */
	{
		struct msg_gate g = {0};
		unsigned adm = 0;

		for (int i = 0; i < 1000; i++)
			(void)msg_gate_admit(&g, 100000, 50, 100, &cl);
		for (int i = 0; i < 1000; i++)
			if (msg_gate_admit(&g, 10, 50, 100, &cl)) /* the clock went back */
				adm++;
		CHECK(adm == 0, "6: a clock that goes back gives no free credit");
		g.dropped = ~0u - 1;
		for (int i = 0; i < 5; i++)
			(void)msg_gate_admit(&g, 10, 50, 100, &cl);
		CHECK(g.dropped == ~0u, "6: the counter stops at the maximum");
	}
	/* 7 */
	{
		unsigned p, b;

		for (int c = 0; c < MC_COUNT; c++) {
			msg_class_rate((enum msg_class)c, &p, &b);
			CHECK(p > 0 && b >= p, "7: every kind has a rate and a burst of at least one second");
		}
		msg_class_rate(MC_POINTER, &p, &b);
		CHECK(p >= 1000, "7: pointer >= 1000/s");
		msg_class_rate(MC_LETTER, &p, &b);
		CHECK(p >= 100, "7: letter >= 100/s");
		msg_class_rate(MC_KEY_POSITION, &p, &b);
		CHECK(p >= 100, "7: key position >= 100/s");
		msg_class_rate(MC_WHEEL, &p, &b);
		CHECK(p >= 200, "7: wheel >= 200/s");
		msg_class_rate(MC_BUTTON, &p, &b);
		CHECK(p >= 50, "7: button >= 50/s");
	}
	/* 7b: LAYOUT is the tightest (it replaces a keymap in the compositor), and still above what a hand does */
	{
		unsigned p, b;

		msg_class_rate(MC_LAYOUT, &p, &b);
		CHECK(p >= 2 && b >= 10, "7b: LAYOUT allows at least 2 a second and a burst of 10");
		CHECK(p <= 10, "7b: and no more than 10 a second sustained");
		msg_class_rate(MC_FIT_CANVAS, &p, &b);
		CHECK(p >= 30, "7b: FIT_CANVAS allows more than the twenty a second of a hand dragging an edge");
	}
	/* 8: a person never meets the limit */
	{
		struct msg_gate mouse = {0}, key = {0}, wheel = {0};
		unsigned p, b, refused = 0;

		for (uint64_t t = 1000; t < 121000; t++) { /* 2 minutes of a 1 kHz mouse, 30 keys a second held, a wheel at 250 Hz */
			msg_class_rate(MC_POINTER, &p, &b);
			if (!msg_gate_admit(&mouse, t, p, b, &cl))
				refused++;
			if (t % 33 == 0) {
				msg_class_rate(MC_KEY_POSITION, &p, &b);
				if (!msg_gate_admit(&key, t, p, b, &cl))
					refused++;
			}
			if (t % 4 == 0) {
				msg_class_rate(MC_WHEEL, &p, &b);
				if (!msg_gate_admit(&wheel, t, p, b, &cl))
					refused++;
			}
		}
		CHECK(refused == 0, "8: a 1 kHz mouse, 30 keys a second and a 250 Hz wheel are never refused");
	}
	/* 9: reading the source */
	if (argc > 1) {
		char *src = slurp(argv[1]);
		size_t n;
		const char *p;

		CHECK(src != NULL, "9: src/rcp.c readable");
		if (src) {
			p = body_of(src, "static bool handle_input(rcp_session *s, uint16_t kind", &n);
			CHECK(p != NULL, "9: handle_input found");
			if (p) {
				const char *adm = memmem(p, n, "msg_admit(s, input_class(kind), now)", strlen("msg_admit(s, input_class(kind), now)"));
				const char *id = memmem(p, n, "le_u32(&l)", strlen("le_u32(&l)"));

				CHECK(adm != NULL, "9: handle_input asks msg_admit() for its kind");
				CHECK(adm && id && adm < id, "9: and before it reads the id");
				CHECK(count_in(p, n, "msg_line(s, input_class(kind))") == 2, "9: both log lines are behind msg_line()");
			}
			p = body_of(src, "static bool drain(rcp_session *s, uint64_t now)", &n);
			CHECK(p != NULL, "9: drain found");
			if (p) {
				CHECK(memmem(p, n, "s->state == S_ACTIVE && !msg_admit(s, mc, now)", strlen("s->state == S_ACTIVE && !msg_admit(s, mc, now)")) != NULL,
				      "9: drain gates the control requests, only in S_ACTIVE");
				CHECK(memmem(p, n, "goto message_done", strlen("goto message_done")) != NULL, "9: an over-rate message is consumed without running its handler");
			}
			p = body_of(src, "bool rcp_time(rcp_session *s, uint64_t now)", &n);
			CHECK(p != NULL && memmem(p, n, "msg_flush_all(s, now)", strlen("msg_flush_all(s, now)")) != NULL, "9: rcp_time flushes the windows");
			p = body_of(src, "static bool drain(rcp_session *s, uint64_t now)", &n);
			if (p) {
				const char *same = memmem(p, n, "strcmp(new_one, s->layout) == 0", strlen("strcmp(new_one, s->layout) == 0"));
				const char *known = memmem(p, n, "layout_known(s, new_one)", strlen("layout_known(s, new_one)"));

				CHECK(same && known && same < known, "9: LAYOUT: the «already in force» test comes BEFORE the XKB compilation (layout_known)");
				CHECK(memmem(p, n, "strcmp(new_one, s->layout_unknown) == 0 ||", strlen("strcmp(new_one, s->layout_unknown) == 0 ||")) != NULL,
				      "9: LAYOUT: a layout already found unknown is not compiled again");
			}
			{
				const char *gp = strstr(src, "#define V_KEY_ASK_GAP_MS ");
				int gap = gp ? atoi(gp + strlen("#define V_KEY_ASK_GAP_MS ")) : -1;
				const char *kr = body_of(src, "static bool handle_key_request(rcp_session *s, reader *l, uint64_t now)", &n);

				CHECK(gap >= 50 && gap < 150, "9: REQUEST_KEY: the gap between two accepted ones is between 50 ms and the transport's 150");
				CHECK(kr != NULL, "9: handle_key_request found");
				if (kr) {
					const char *chk = memmem(kr, n, "now - s->key_asked_ms < V_KEY_ASK_GAP_MS", strlen("now - s->key_asked_ms < V_KEY_ASK_GAP_MS"));
					const char *tol = memmem(kr, n, "!s->never_sent_key && !already_seen", strlen("!s->never_sent_key && !already_seen"));
					const char *set = memmem(kr, n, "s->key_asked_ms = now;", strlen("s->key_asked_ms = now;"));
					const char *ask = memmem(kr, n, "key_needed(s,", strlen("key_needed(s,"));

					CHECK(chk && tol && chk < tol, "9: REQUEST_KEY: the gap test also covers already_seen requests (it comes first)");
					CHECK(set && ask && set < ask, "9: REQUEST_KEY: the time is taken when the request is ACCEPTED");
					CHECK(count_in(kr, n, "msg_line(s, MC_REQUEST_KEY)") == 3, "9: REQUEST_KEY: its three lines go through msg_line()");
				}
			}
			{
				const char *cc = body_of(src, "static enum msg_class control_class(uint16_t kind)", &n);
				const char *dr = body_of(src, "static bool drain(rcp_session *s, uint64_t now)", &n);
				size_t nd = n;
				const char *shortcut, *gate, *hook;

				CHECK(cc != NULL, "9: control_class found");
				CHECK(cc && !memmem(cc, 400, "T_FIT_CANVAS", strlen("T_FIT_CANVAS")),
				      "9: FIT_CANVAS is NOT dropped in silence (§7.1: one CANVAS answer for each)");
				shortcut = dr ? memmem(dr, nd, "rcp_canvas_adapted_now(s, good_w, good_h, now);", 47) : NULL;
				gate = dr ? memmem(dr, nd, "msg_admit(s, MC_FIT_CANVAS, now)", strlen("msg_admit(s, MC_FIT_CANVAS, now)")) : NULL;
				hook = dr ? memmem(dr, nd, "if (!s->g.recanvas) {", strlen("if (!s->g.recanvas) {")) : NULL;
				CHECK(gate != NULL, "9: FIT_CANVAS has its gate in its handler");
				CHECK(shortcut && gate && hook && shortcut < gate && gate < hook,
				      "9: FIT_CANVAS: after the same-size shortcut (which rebuilds nothing), before the stage hook");
				CHECK(gate && memmem(gate, 300, "NOT_NOW", strlen("NOT_NOW")) != NULL, "9: and over the rate it is ANSWERED NOT_NOW");
			}
			free(src);
		}
	}
	/* 10: the budget and a canvas that grows (src/main.c, argv[2], optional) */
	if (argc > 2) {
		char *m = slurp(argv[2]);
		size_t n;
		const char *p;

		CHECK(m != NULL, "10: src/main.c readable");
		if (m) {
			p = body_of(m, "static bool recanvas_to_child(", &n);
			CHECK(p != NULL, "10: recanvas_to_child found");
			if (p) {
				const char *fit = memmem(p, n, "recanvas_fits_budget(p, user, width, height)", strlen("recanvas_fits_budget(p, user, width, height)"));
				const char *go = memmem(p, n, "children_recanvas(", strlen("children_recanvas("));

				CHECK(fit && go && fit < go, "10: a growing canvas is judged by the budget BEFORE it leaves for the stage");
			}
			p = body_of(m, "static bool recanvas_fits_budget(", &n);
			CHECK(p != NULL, "10: recanvas_fits_budget found");
			if (p) {
				CHECK(memmem(p, n, "!budget_on()", strlen("!budget_on()")) != NULL, "10: budget OFF: it passes");
				CHECK(memmem(p, n, "<= (uint64_t)CANVAS_W * CANVAS_H", strlen("<= (uint64_t)CANVAS_W * CANVAS_H")) != NULL,
				      "10: within what the admission counted: it passes");
				CHECK(count_in(p, n, "strcmp(chi, user) != 0") + count_in(p, n, "strcmp(found_again[i].user, user) != 0") == 2,
				      "10: the user's own stage is left out of the sum");
				CHECK(memmem(p, n, "e != BUDGET_DOES_NOT_HOLD", strlen("e != BUDGET_DOES_NOT_HOLD")) != NULL,
				      "10: «I could not measure» passes, only a clear no refuses");
			}
			free(m);
		}
	}
	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
