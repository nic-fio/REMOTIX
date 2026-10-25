/*
 * test.c — the budget is asked ONLY for a NEW FIT_CANVAS of the client (rcp_hooks.canvas_fits), never for the calls of `recanvas` that put a
 * session on the canvas it already had (the ATTACH, the recall of the scene) — review of 39703a57.  A budget that said no at the ATTACH leaves
 * the screen black.
 *
 * The REAL rcp.c is #included (src/ or the twin, chosen by -I); a session in S_ACTIVE with a stage canvas of 1920x1080 receives a real FIT_CANVAS
 * through rcp_receive(), and the hooks record what the host would see.
 *   1. canvas_fits says NO: the client gets CANVAS(REFUSED=2, NOT_NOW=3) with the canvas in force, and `recanvas` is NOT called;
 *   2. canvas_fits says YES: `recanvas` is called once, with the size asked, and no refusal goes out;
 *   3. the hook is not connected: `recanvas` is called (the old behaviour);
 *   4. canvas_fits is asked with the size AFTER the reductions (here: the size asked, even and in range);
 *   5. the size already in force never asks the budget (the shortcut comes first, it costs nothing);
 *   6. a refusal by the budget does not touch the request in flight (no NOT_NOW to the first, canvas_flight unchanged).
 * And by reading the source (argv[1]): rcp.c asks canvas_fits in ONE place; the two other calls of `recanvas` (ATTACH, scene recall) are not
 * preceded by it.
 *
 * BUILD AND RUN (a second; from the root of the tree):
 *   for T in src benches/rcp; do F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Wno-unused-parameter -I$T -Ibenches/fuzz/rcp-msg" &&
 *      gcc $F -c benches/unit/fit-canvas-budget/test.c -o /tmp/fc-t.o && gcc $F -c benches/fuzz/rcp-msg/stubs_log.c -o /tmp/fc-l.o &&
 *      gcc -fsanitize=address,undefined /tmp/fc-t.o /tmp/fc-l.o -o /tmp/fc-test && /tmp/fc-test $T/rcp.c || exit 1; done
 */
#include "rcp.c"

#include <stdio.h>

static int checks, bad;
#define CHECK(cond, what) do { checks++; if (!(cond)) { bad++; printf("  FAIL %s:%d  %s\n", __FILE__, __LINE__, what); } } while (0)

static int recanvas_calls, fits_calls, fits_answer;
static uint32_t recanvas_w, recanvas_h, fits_w, fits_h;
static uint8_t last_canvas[16];
static int canvas_msgs;

static bool h_recanvas(void *c, uint32_t w, uint32_t h) { (void)c; recanvas_calls++; recanvas_w = w; recanvas_h = h; return true; }
static bool h_fits(void *c, uint32_t w, uint32_t h) { (void)c; fits_calls++; fits_w = w; fits_h = h; return fits_answer; }
static void h_send(void *c, const uint8_t *d, size_t n)
{
	(void)c;
	if (n >= 6 + 10 && d[0] == 0x00 && d[1] == 0x0E) {
		canvas_msgs++;
		memcpy(last_canvas, d + 6, 10);
	}
}
static void h_close(void *c, uint8_t r) { (void)c; (void)r; }
static int canvas_lines;
static void h_record(void *c, const char *l) { (void)c; if (strncmp(l, "CANVAS", 6) == 0) canvas_lines++; }

static rcp_session *fresh(bool with_fits)
{
	rcp_hooks g;
	rcp_session *s;

	memset(&g, 0, sizeof g);
	g.send_msg = h_send;
	g.close = h_close;
	g.record = h_record;
	g.recanvas = h_recanvas;
	if (with_fits)
		g.canvas_fits = h_fits;
	s = rcp_open(&g, "192.0.2.7", 1000);
	s->state = S_ACTIVE;
	s->session_sent = true;
	s->is_attached = false;
	s->canvas_w = 1920;
	s->canvas_h = 1080;
	recanvas_calls = fits_calls = canvas_msgs = canvas_lines = 0;
	return s;
}

static void fit(rcp_session *s, uint32_t w, uint32_t h, uint64_t now)
{
	uint8_t m[14] = {0x00, 0x0B, 0, 0, 0, 8};

	m[6] = (uint8_t)(w >> 24); m[7] = (uint8_t)(w >> 16); m[8] = (uint8_t)(w >> 8); m[9] = (uint8_t)w;
	m[10] = (uint8_t)(h >> 24); m[11] = (uint8_t)(h >> 16); m[12] = (uint8_t)(h >> 8); m[13] = (uint8_t)h;
	(void)rcp_receive(s, m, sizeof m, now);
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

	/* 1 */
	s = fresh(true);
	fits_answer = 0;
	fit(s, 3840, 2160, 50000);
	CHECK(fits_calls == 1, "1: the budget is asked for a NEW, larger request");
	CHECK(recanvas_calls == 0, "1: and when it says no `recanvas` is NOT called");
	CHECK(canvas_msgs == 1 && last_canvas[0] == 2 && last_canvas[1] == 3, "1: the client gets CANVAS(REFUSED, NOT_NOW)");
	CHECK(((last_canvas[2] << 24) | (last_canvas[3] << 16) | (last_canvas[4] << 8) | last_canvas[5]) == 1920u, "1: with the canvas in force (1920 wide)");
	CHECK(!s->canvas_flight, "6: nothing is in flight after a refusal by the budget");
	rcp_free(s);

	/* 2 */
	s = fresh(true);
	fits_answer = 1;
	fit(s, 3840, 2160, 50000);
	CHECK(fits_calls == 1 && recanvas_calls == 1, "2: when it says yes, `recanvas` is called once");
	CHECK(recanvas_w == 3840 && recanvas_h == 2160, "2: with the size asked");
	CHECK(canvas_msgs == 0, "2: and no CANVAS goes out yet (the answer is the first frame at the new size)");
	CHECK(s->canvas_flight, "2: the request is in flight");
	/* 6: a second, refused request does not disturb the one in flight */
	fits_answer = 0;
	recanvas_calls = 0;
	fit(s, 4096, 2304, 50010);
	CHECK(canvas_msgs == 1 && last_canvas[0] == 2 && last_canvas[1] == 3, "6: the refused second request is answered NOT_NOW");
	CHECK(s->canvas_flight && s->canvas_flight_w == 3840 && s->canvas_flight_h == 2160, "6: and the first one is still in flight, unchanged");
	CHECK(recanvas_calls == 0, "6: nothing more reached the stage");
	rcp_free(s);

	/* 3 */
	s = fresh(false);
	fit(s, 2560, 1440, 50000);
	CHECK(recanvas_calls == 1 && fits_calls == 0, "3: without the hook `recanvas` is called (the old behaviour)");
	rcp_free(s);

	/* 4 */
	s = fresh(true);
	fits_answer = 1;
	fit(s, 2560, 1441, 50000); /* odd height: reduced to even by rcp_size_allowed */
	CHECK(fits_calls == 1 && fits_w == 2560 && (fits_h % 2) == 0 && fits_h <= 1441, "4: the budget sees the size AFTER the rule of range and parity");
	rcp_free(s);

	/* 5 */
	s = fresh(true);
	fits_answer = 0;
	fit(s, 1920, 1080, 50000); /* the size already in force */
	CHECK(fits_calls == 0, "5: the size already in force never asks the budget");
	CHECK(canvas_msgs == 1 && last_canvas[0] == 1, "5: it is answered CANVAS(FITTED)");
	rcp_free(s);

	/* 7 (reading of rcp.c, M1): the size already in force passes through the bucket and writes no line per message */
	s = fresh(true);
	fits_answer = 1;
	{
		int fitted = 0, not_now = 0;

		for (int i = 0; i < 1000; i++) {
			int before = canvas_msgs;

			fit(s, 1920, 1080, 50000); /* the size in force, 1000 times in the same millisecond */
			if (canvas_msgs == before + 1) {
				if (last_canvas[0] == 1)
					fitted++;
				else if (last_canvas[0] == 2 && last_canvas[1] == 3)
					not_now++;
			}
		}
		CHECK(fitted + not_now == 1000, "7: every one of the 1000 identical requests gets ITS CANVAS (§7.1: one for each)");
		CHECK(fitted <= 180 && fitted >= 170, "7: only the burst of the bucket (180) is answered FITTED");
		CHECK(not_now == 1000 - fitted, "7: the rest is answered NOT_NOW, with the canvas in force");
		CHECK(canvas_lines <= 2 * MSG_LINES_PER_WINDOW, "7: and the log gets at most a few lines, not one per message");
		CHECK(recanvas_calls == 0 && fits_calls == 0, "7: nothing reached the stage or the budget");
	}
	rcp_free(s);

	if (argc > 1) {
		char *src = slurp(argv[1]);

		CHECK(src != NULL, "source readable");
		if (src) {
			int ask = 0;
			const char *p = src;
			const char *attach, *recall;

			while ((p = strstr(p, "s->g.canvas_fits(")) != NULL) {
				ask++;
				p++;
			}
			CHECK(ask == 1, "rcp.c asks canvas_fits in ONE place");
			attach = strstr(src, "s->g.recanvas(s->g.ctx, tl, ta);");
			recall = strstr(src, "s->g.recanvas(s->g.ctx, target_w, target_h);");
			CHECK(attach != NULL && recall != NULL, "the ATTACH and the scene recall call `recanvas` as before");
			CHECK(attach && !memmem(attach - 400, 400, "canvas_fits", strlen("canvas_fits")), "and the ATTACH is not preceded by the budget");
			CHECK(recall && !memmem(recall - 400, 400, "canvas_fits", strlen("canvas_fits")), "and neither is the recall of the scene");
			free(src);
		}
	}
	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
