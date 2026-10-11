/*
 * 13-w1 — the first frame pulled from wlroots, and the proof that they are the
 *          right pixels.
 *
 * ⛔ It runs INSIDE the XFCE session, as the tenant who owns it: capture has
 *    no gates on this family, but the uid does
 *    (`/run/user/<uid>` is `drwx------`).
 *
 *   13-w1 [count] [wait_s] [width height]
 *   W1_ROUTE=card 13-w1 …     ⭐ the CARD route (21 Sep 2026)
 *
 * ⭐ With `W1_ROUTE=card` the frame is taken into a DMA-BUF slab of ours
 *    (`wlroots.c`, the card section), and the time per frame is the one to set
 *    against the 8.8-14.9 ms of the memory route (`fasi/13-xfce.md`).  ⛔ The
 *    CONTENT is checked all the same, by mapping the slab: a nice time on a
 *    black frame is the defect this bench exists not to give green.
 *
 * It writes the last frame to `/tmp/13-w1.ppm` — ⚠ PPM and not PNG on
 * purpose: no library between the compositor's bytes and the file one looks
 * at. Whoever wants a PNG makes it with `ffmpeg`, outside of here, and if the
 * image were wrong they would know it was not this conversion.
 *
 * ⛔⛔ AND THE JUDGEMENT IS NOT "the program did not blow up".
 *
 *    A **black** frame and a frame that **never arrived** look the same in a
 *    count, and it is the error form this project has paid for several
 *    times. ⇒ Here the CONTENT is measured: how many bytes are not zero,
 *    and how many distinct colours there are. A real screen has many;
 *    a screen that is off has one.
 */
#include "../src/wlroots.h"

#include <glib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

/* ⚠ The two formats that wl_shm numbers 0 and 1 instead of with the fourcc. */
#define WL_SHM_ARGB8888 0
#define WL_SHM_XRGB8888 1

#define FOURCC(a, b, c, d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | ((uint32_t)(c) << 16) | \
                            ((uint32_t)(d) << 24))
#define DRM_XBGR8888 FOURCC('X', 'B', '2', '4')
#define DRM_ABGR8888 FOURCC('A', 'B', '2', '4')

static const char *format_name(uint32_t f)
{
	static char buf[8];

	if (f == WL_SHM_ARGB8888)
		return "ARGB8888";
	if (f == WL_SHM_XRGB8888)
		return "XRGB8888";
	memcpy(buf, &f, 4);
	buf[4] = 0;
	return buf;
}

/*
 * How many distinct colours, and how many bytes other than zero.
 *
 * ⛔ The colours are counted by sampling (one pixel every 37, which is prime
 *    and divides no round width): counting them all at 1080p costs more than
 *    the capture being measured, and would skew the times this bench
 *    reports.
 */
static void look_pixels(const WlrFrame *f, guint *colors, double *not_zero)
{
	GHashTable *seen_items = g_hash_table_new(g_direct_hash, g_direct_equal);
	gsize total_pixels = (gsize)f->width * f->height;
	gsize different = 0, watched = 0;

	for (gsize y = 0; y < f->height; y++) {
		const uint8_t *line = f->pixel + (gsize)y * f->stride;

		for (gsize x = 0; x < f->width; x += 37) {
			uint32_t c = ((uint32_t)line[x * 4 + 0]) | ((uint32_t)line[x * 4 + 1] << 8) |
			             ((uint32_t)line[x * 4 + 2] << 16);

			g_hash_table_add(seen_items, GUINT_TO_POINTER(c));
			if (c)
				different++;
			watched++;
		}
	}
	*colors = g_hash_table_size(seen_items);
	*not_zero = watched ? (double)different * 100.0 / watched : 0.0;
	g_hash_table_destroy(seen_items);
	(void)total_pixels;
}

/*
 * ⛔⛔ THE CHANNEL ORDER IS READ FROM THE FOURCC, AND NOT JUDGED BY EYE.
 *
 * `[M]` 21 Sep 2026, and it cost a round: the first draft always wrote
 * `B G R` (the order of XRGB8888), the image came out with **orange**
 * folders and looked right — ⛔ but labwc declares **XB24**, that is
 * `XBGR8888`, which in memory is `R G B X`. Adwaita's real folders are
 * **blue**: what looked like confirmation was the swap.
 *
 * ⇒ It is the lesson of `LEZIONI.md` §1.9 in its worst form: a check that
 *   gives a **plausible** result is not a check. Here the fact is asked of
 *   the format, which states it, instead of deduced from how it looks.
 */
static void channels(uint32_t fmt, int *ir, int *ig, int *ib)
{
	if (fmt == DRM_XBGR8888 || fmt == DRM_ABGR8888) {
		*ir = 0; *ig = 1; *ib = 2;   /* R G B X in memory */
	} else {
		*ir = 2; *ig = 1; *ib = 0;   /* B G R X — XRGB/ARGB8888 */
	}
}

static bool write_ppm(const WlrFrame *f, const char *dove)
{
	FILE *out = fopen(dove, "wb");
	int ir, ig, ib;

	channels(f->fmt, &ir, &ig, &ib);
	if (!out)
		return false;
	fprintf(out, "P6\n%u %u\n255\n", f->width, f->height);
	for (uint32_t y = 0; y < f->height; y++) {
		/* ⛔ `y_inverted`: if the compositor says the rows are to be read from
		 *    the bottom, and that is not done, the image comes out upside down —
		 *    a fault that looks like an encoder fault. */
		uint32_t real = f->y_inverted ? (f->height - 1 - y) : y;
		const uint8_t *line = f->pixel + (gsize)real * f->stride;

		for (uint32_t x = 0; x < f->width; x++) {
			fputc(line[x * 4 + ir], out);
			fputc(line[x * 4 + ig], out);
			fputc(line[x * 4 + ib], out);
		}
	}
	fclose(out);
	return true;
}

/*
 * ⭐ The card slab, lent to the CPU to look at it.  ⛔ With the DMA-BUF SYNC
 *    around it (`wlr_cpu_read`), and the mapping is taken down with
 *    `lend_end()`: frame `f` goes back to having no `pixel`.
 */
static void *lend_start(WlrFrame *f)
{
	void *m;

	if (!f->on_card)
		return NULL;
	m = mmap(NULL, f->offset + f->byte, PROT_READ, MAP_SHARED, f->fd, 0);
	if (m == MAP_FAILED)
		return NULL;
	wlr_cpu_read(f->fd, true);
	f->pixel = (const uint8_t *)m + f->offset;
	return m;
}

static void lend_end(WlrFrame *f, void *m)
{
	if (!m)
		return;
	wlr_cpu_read(f->fd, false);
	munmap(m, f->offset + f->byte);
	f->pixel = NULL;
}

int main(int argc, char **argv)
{
	int amount = argc > 1 ? atoi(argv[1]) : 10;
	double wait = argc > 2 ? atof(argv[2]) : 2.0;
	g_autoptr(GError) mistake = NULL;
	WlrStage *stage;
	WlrFrame f;
	uint32_t l = 0, a = 0;
	gint64 first_us = 0;
	int grabbed = 0, on_card = 0;
	double worst = 0, total = 0, wait_gpu = 0;
	bool card = g_strcmp0(g_getenv("W1_ROUTE"), "card") == 0;
	bool last_held = false;
	/* ⭐ The two "refute it" tests of the port onto the PENDING frame:
	 *   W1_RESUME=1  a timeout is NOT a lost frame: it is called again and
	 *                  the same one is resumed (it is the child's loop at 8 ms);
	 *   W1_KEEP=1     the previous slab is kept IN HAND while the next is
	 *                  taken, like the encoder that has not finished yet, and
	 *                  it is checked that the next is ANOTHER slab — plus a
	 *                  double return, which must stay without effect. */
	bool resume = g_strcmp0(g_getenv("W1_RESUME"), "1") == 0;
	bool keep = g_strcmp0(g_getenv("W1_KEEP"), "1") == 0;
	int resumed = 0, same_slab = 0;
	gint64 frame_start = 0;

	printf("== 13-w1 — the first frame pulled from wlroots ==\n");
	printf("   %d frames, wait %.1f s each\n\n", amount, wait);

	stage = wlr_open(&mistake);
	if (!stage) {
		printf("  ⛔ could not open the capture: %s\n", mistake->message);
		printf("\n  ⛔⛔ ROSSO\n");
		return 1;
	}
	wlr_measure(stage, &l, &a);
	printf("   output «%s», %ux%u\n", wlr_output_name(stage), l, a);
	if (card) {
		if (wlr_ask_card(stage, &mistake))
			printf("   ⭐ CARD route on\n");
		else
			printf("   ⛔ CARD route DENIED: %s — the MEMORY route is measured, "
			       "and this line says so\n",
			       mistake->message);
		g_clear_error(&mistake);
	}

	/*
	 * ⭐ THE SIZE, IF IT WAS ASKED FOR — and the judgement comes from READING IT BACK.
	 *
	 * ⛔ `DECISIONI.md` §5.0-sexies: asking for the size the output already has
	 *    answers "succeeded" without sending anything, and an old serial answers
	 *    "cancelled" without doing anything. ⇒ Here the outcome is not looked at:
	 *    the size is asked for again and compared.
	 */
	if (argc > 4) {
		uint32_t vl = (uint32_t)atoi(argv[3]), va = (uint32_t)atoi(argv[4]);
		uint32_t after_w = 0, after_h = 0;
		WlrSizeOutcome e = wlr_ask_size(stage, vl, va, 3.0, &mistake);

		wlr_measure(stage, &after_w, &after_h);
		printf("   size asked %ux%u — outcome of the REQUEST: %s\n", vl, va,
		       e == WLR_SIZE_REQUESTED       ? "accepted"
		       : e == WLR_SIZE_UNCHANGED    ? "it already was"
		       : e == WLR_SIZE_REFUSED   ? "refused"
		       : e == WLR_SIZE_CANCELLED   ? "cancelled (old serial)"
		                                     : "the compositor cannot change it");
		g_clear_error(&mistake);
		if (after_w == vl && after_h == va)
			printf("   ⭐ and the output READ BACK is %ux%u: the size really changed\n",
			       after_w, after_h);
		else
			printf("   ⛔ but the output READ BACK is %ux%u: it did NOT change\n", after_w,
			       after_h);
		l = after_w;
		a = after_h;
	}

	for (int i = 0; i < amount; i++) {
		gint64 before;
		WlrOutcome e;
		double ms;

		/* ⛔ The previous slab is RETURNED before asking for the next: it is what
		 *    the product does (`capture_stopped_free()`), and a bench that kept
		 *    them all would run out of slabs and measure its own defect. */
		WlrFrame kept = f;

		if (last_held && !keep) {
			wlr_release(stage, f.slab);
			last_held = false;
		}
		before = g_get_monotonic_time();
		if (!frame_start)
			frame_start = before;
		e = wlr_frame(stage, wait, &f, &mistake);
		/* ⚠ With resuming, the time of a frame is from the FIRST call,
		 *   not from the last: the timeouts are inside it. */
		ms = (g_get_monotonic_time() - frame_start) / 1000.0;

		/* ⚠ With a ceiling: a mute compositor must not stop the bench. */
		if (e == WLR_FRAME_EXPIRED && resume && resumed < amount * 1000) {
			resumed++;
			g_clear_error(&mistake);
			i--;
			continue;
		}
		frame_start = 0;
		if (keep && last_held) {
			/* ⛔ The slab kept must not be the one just filled: it would
			 *    mean labwc copied into it while it was "in hand".  Then it is
			 *    returned TWICE: the second does nothing. */
			if (e == WLR_FRAME_TAKEN && f.on_card && f.slab == kept.slab)
				same_slab++;
			wlr_release(stage, kept.slab);
			wlr_release(stage, kept.slab);
			last_held = false;
		}

		if (e != WLR_FRAME_TAKEN) {
			printf("  ⛔ frame %d: %s — %s\n", i + 1,
			       e == WLR_FRAME_FAILED  ? "the compositor said NO"
			       : e == WLR_FRAME_EXPIRED ? "timed out"
			                                     : "the wire dropped",
			       mistake ? mistake->message : "no reason");
			g_clear_error(&mistake);
			continue;
		}
		grabbed++;
		if (f.on_card) {
			on_card++;
			wait_gpu += f.gpu_wait_us / 1000.0;
			last_held = true;
		}
		total += ms;
		if (ms > worst)
			worst = ms;
		if (i == 0) {
			guint colors = 0;
			double not_zero = 0;

			void *m = lend_start(&f);

			first_us = g_get_monotonic_time();
			if (f.pixel)
				look_pixels(&f, &colors, &not_zero);
			lend_end(&f, m);
			printf("   first frame: %ux%u stride %u format %s%s — %s\n",
			       f.width, f.height, f.stride, format_name(f.fmt),
			       f.y_inverted ? " ⚠ Y INVERTED" : "",
			       f.on_card ? (f.explicit_wait
			                             ? "on the CARD (linear slab, fence extracted)"
			                             : "on the CARD (⚠ no fence: implicit)")
			                      : "in MEMORY");
			printf("   ⭐ the CONTENT: %u distinct colours, %.1f%% of the samples are not "
			       "black\n",
			       colors, not_zero);
			(void)first_us;
		}
	}

	if (grabbed && (!f.on_card || last_held)) {
		guint colors = 0;
		double not_zero = 0;
		void *m = lend_start(&f);

		if (f.pixel) {
			look_pixels(&f, &colors, &not_zero);
			write_ppm(&f, "/tmp/13-w1.ppm");
		}
		lend_end(&f, m);
		if (last_held) {
			wlr_release(stage, f.slab);
			last_held = false;
		}
		printf("\n   last frame: %u distinct colours, %.1f%% not black "
		       "⇒ /tmp/13-w1.ppm\n",
		       colors, not_zero);
	}

	WlrCounts c;

	wlr_counts(stage, &c);
	printf("\n   asked %" G_GUINT64_FORMAT " · taken %" G_GUINT64_FORMAT
	       " · failed %" G_GUINT64_FORMAT " · timed out %" G_GUINT64_FORMAT "\n",
	       c.requested, c.grabbed, c.failed, c.expired);
	if (grabbed)
		printf("   time per frame: %.1f ms on average, %.1f ms the worst\n",
		       total / grabbed, worst);
	/* ⛔ The route is stated NEXT TO the number: a time without its route is
	 *    a time that will lie. */
	printf("   route: %d on the CARD, %d in MEMORY", on_card, grabbed - on_card);
	if (on_card)
		printf(" — GPU wait after `ready` %.2f ms on average", wait_gpu / on_card);
	printf("\n");
	if (resume)
		printf("   resumed after a timeout: %d (the PENDING frame)\n", resumed);
	if (keep)
		printf("   slab kept in hand and filled again: %d %s\n", same_slab,
		       same_slab ? "⛔⛔ labwc wrote into a slab IN HAND" : "⭐");

	wlr_close(stage);

	if (same_slab) {
		printf("\n  ⛔⛔ ROSSO — a slab in hand was reused %d times\n", same_slab);
		return 1;
	}
	if (grabbed != amount) {
		printf("\n  ⛔⛔ ROSSO — %d frames of %d\n", grabbed, amount);
		return 1;
	}
	printf("\n  ⭐ VERDE — %d frames of %d, pulled one by one\n", grabbed, amount);
	return 0;
}
