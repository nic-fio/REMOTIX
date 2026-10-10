/*
 * 06-b5-esiti-cattura.c — ⭐ the THREE proposals of `06-b40`, put to the test
 *                            starting from the hypothesis that they are WRONG.
 *
 *   06-b5-esiti-cattura              runs all cases
 *   06-b5-esiti-cattura <n>          runs only case n
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHERE THIS BENCH COMES FROM
 *
 * `banchi/06-b40-palco-finto.c` exercised `src/cattura.c` with a real PipeWire
 * producer and drew three proposals for the product from it, all `[R]`/`[M]` and
 * none written:
 *
 *   1. `capture_resize()` declares SUCCESS on a stream that dies, and
 *      *«`figlio.c` has no way of knowing that the renegotiation KILLED the
 *      capture: today it only finds out from the timeout of `cattura_prendi`»*;
 *   2. `measure_divergent` is **written and never read** ⇒ an accessor is needed;
 *   3. the *«granted different from requested»* branch **cannot be reached from
 *      outside** except with a race, *«and a bench cannot program a race»*.
 *
 * ⭐ The brief of this bench is the opposite of that of `06-b40`: **look for the
 *    proof that the three claims are false.**  Every case is written to
 *    DISPROVE, not to confirm — and the expected result is declared before the run.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT THIS BENCH DOES **NOT** TEST
 *
 *   · **it does not test Mutter**: the stage here is a `pw_stream` of this file, and
 *     I choose its limits.  On Mutter `[M]` (§5.0-sexies) 30 requests out of
 *     30 were granted exactly from 1x1 to 7680x4320, and `rcp_size_allowed()`
 *     cuts at 7680x4320: ⇒ the scene «the stage cannot hold the size» on the real
 *     product is `[?]`, not `[M]`.  Here what is measured is the BEHAVIOUR OF `cattura.c`
 *     when that scene happens, not how often it happens;
 *   · **it does not test the pixels**: the fake stage queues no buffer, so
 *     `capture_take()` on a HEALTHY stream answers ZERO.  ⭐ And that is exactly the
 *     positive control case 3 needs: «zero» and «fault» must remain
 *     two different answers (`CODER.md` §3.10);
 *   · **it does not test `figlio.c`**: the timings of the child's loop are quoted
 *     (`MOTION_WAIT_S 0.008`), not executed.
 */
#include "../src/cattura.h"
#include "../src/registro.h"

#include <pipewire/pipewire.h>
#include <spa/param/video/format-utils.h>
#include <spa/pod/builder.h>
#include <spa/utils/result.h>

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* ------------------------------------------------------------------ *
 *  ⛔ THE LOG IS CAPTURED — and here it is the MEASUREMENT, not a side dish.
 *
 *  `src/registro.c` writes to `stderr` and has no listening hook:
 *  ⇒ `stderr` is redirected to a temporary file and read back.  ⚠ The technique
 *  is that of `06-b40`, including the trap already paid for: **the file is not
 *  truncated, the point is marked** (an `ftruncate` does not move the write offset,
 *  and a hole of NULs is left in front, on which `strstr` stops ⇒ every `says()`
 *  would answer «no», that is green on every case that requires an absence).
 * ------------------------------------------------------------------ */
#define REG_CAP 262144
static char seen_log[REG_CAP];
static FILE *hijacked;
static bool chatter;

static void log_redirect(void)
{
	hijacked = tmpfile();
	if (!hijacked) {
		printf("  ⛔ the temporary file for the log cannot be opened\n");
		exit(2);
	}
	if (dup2(fileno(hijacked), STDERR_FILENO) < 0) {
		printf("  ⛔ stderr cannot be redirected\n");
		exit(2);
	}
	setvbuf(stderr, NULL, _IONBF, 0);
}

static off_t sign;

static void log_reset(void)
{
	fflush(stderr);
	sign = lseek(fileno(hijacked), 0, SEEK_CUR);
	if (sign < 0)
		sign = 0;
	seen_log[0] = 0;
}

static void log_reread(void)
{
	ssize_t n;
	fflush(stderr);
	n = pread(fileno(hijacked), seen_log, REG_CAP - 1, sign);
	seen_log[n > 0 ? n : 0] = 0;
	if (chatter && n > 0)
		printf("      | %s\n", seen_log);
}

static bool says(const char *piece)
{
	return strstr(seen_log, piece) != NULL;
}

/* ------------------------------------------------------------------ *
 *  ⭐ THE FAKE STAGE — a PipeWire producer, with limits I choose
 *
 *  ⚠ It is the one from `06-b40`, with **one thing more** that case 5 needs: the
 *    stage can REDO its own offer on the fly (`stage_reproposes`), which is the
 *    only way to ask «can a producer IMPOSE its size on a
 *    consumer that offers a fixed one?».
 * ------------------------------------------------------------------ */
typedef struct {
	struct pw_thread_loop *cycle;
	struct pw_context *context;
	struct pw_core *core;
	struct pw_stream *flow;
	struct spa_hook hook;
	uint32_t node;
	uint32_t min_l, min_a, max_l, max_a;   /* ⛔ the limits of the fake stage */
	bool fixed;                            /* the offer is a FIXED rectangle */
	uint32_t negotiated_w, negotiated_h;
	int how_many_negotiations;
} Stage;

static void stage_parameter(void *data_v, uint32_t id, const struct spa_pod *param)
{
	Stage *p = data_v;
	struct spa_video_info_raw info;

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_video_raw_parse(param, &info) < 0)
		return;
	p->negotiated_w = info.size.width;
	p->negotiated_h = info.size.height;
	p->how_many_negotiations++;
	printf("      [stage] negotiated format: %ux%u  (negotiation no.%d)\n",
	       info.size.width, info.size.height, p->how_many_negotiations);
}

static const struct pw_stream_events stage_events = {
	PW_VERSION_STREAM_EVENTS,
	.param_changed = stage_parameter,
};

/* ⛔ The frame rate is a RANGE starting from zero, not a fixed 30/1: `cattura.c`
 *    offers `framerate` as a fixed fraction 0/1 — «the producer dictates the
 *    frame rate» — and a stage offering a fixed 30/1 would give an EMPTY
 *    intersection.  ⚠ A defect of the STAGE, already paid for by `06-b40` on 21 August 2026. */
static const struct spa_pod *stage_proposal(struct spa_pod_builder *b, Stage *p)
{
	struct spa_rectangle mis  = SPA_RECTANGLE(p->min_l, p->min_a);
	struct spa_rectangle mini = SPA_RECTANGLE(p->min_l, p->min_a);
	struct spa_rectangle maxi = SPA_RECTANGLE(p->max_l, p->max_a);
	struct spa_fraction cad   = SPA_FRACTION(0, 1);
	struct spa_fraction cmin  = SPA_FRACTION(0, 1);
	struct spa_fraction cmax  = SPA_FRACTION(120, 1);

	if (p->fixed)
		return spa_pod_builder_add_object(
		    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
		    SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
		    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
		    SPA_FORMAT_VIDEO_format, SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx),
		    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&mis),
		    SPA_FORMAT_VIDEO_framerate,
		    SPA_POD_CHOICE_RANGE_Fraction(&cad, &cmin, &cmax),
		    SPA_FORMAT_VIDEO_maxFramerate,
		    SPA_POD_CHOICE_RANGE_Fraction(&cmax, &cmin, &cmax));

	return spa_pod_builder_add_object(
	    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
	    SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
	    SPA_FORMAT_VIDEO_format, SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx),
	    SPA_FORMAT_VIDEO_size, SPA_POD_CHOICE_RANGE_Rectangle(&mis, &mini, &maxi),
	    SPA_FORMAT_VIDEO_framerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&cad, &cmin, &cmax),
	    SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&cmax, &cmin, &cmax));
}

static Stage *stage_open(uint32_t min_l, uint32_t min_a,
                         uint32_t max_l, uint32_t max_a)
{
	Stage *p = calloc(1, sizeof *p);
	uint8_t space[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *par[1];

	p->min_l = min_l; p->min_a = min_a;
	p->max_l = max_l; p->max_a = max_a;

	p->cycle = pw_thread_loop_new("palco-finto-b5", NULL);
	if (!p->cycle)
		goto fault;
	p->context = pw_context_new(pw_thread_loop_get_loop(p->cycle), NULL, 0);
	if (!p->context)
		goto fault;
	pw_thread_loop_lock(p->cycle);
	if (pw_thread_loop_start(p->cycle) < 0) {
		pw_thread_loop_unlock(p->cycle);
		goto fault;
	}
	p->core = pw_context_connect(p->context, NULL, 0);
	if (!p->core) {
		pw_thread_loop_unlock(p->cycle);
		goto fault;
	}
	p->flow = pw_stream_new(p->core, "palco-finto-b5",
	                          pw_properties_new(PW_KEY_MEDIA_TYPE, "Video",
	                                            PW_KEY_MEDIA_CATEGORY, "Playback",
	                                            PW_KEY_MEDIA_ROLE, "Screen",
	                                            PW_KEY_MEDIA_CLASS, "Video/Source",
	                                            PW_KEY_NODE_NAME, "remotix-palco-b5",
	                                            NULL));
	if (!p->flow) {
		pw_thread_loop_unlock(p->cycle);
		goto fault;
	}
	pw_stream_add_listener(p->flow, &p->hook, &stage_events, p);
	par[0] = stage_proposal(&b, p);
	if (pw_stream_connect(p->flow, PW_DIRECTION_OUTPUT, PW_ID_ANY,
	                      PW_STREAM_FLAG_MAP_BUFFERS, par, 1) < 0) {
		pw_thread_loop_unlock(p->cycle);
		goto fault;
	}
	pw_thread_loop_unlock(p->cycle);

	/* ⛔ The node identifier is WAITED for: before registration on the
	 *    server it is `SPA_ID_INVALID`, and attaching to it would mean attaching
	 *    to nothing — with the symptom «capture does not start» and no error. */
	for (int i = 0; i < 200; i++) {
		p->node = pw_stream_get_node_id(p->flow);
		if (p->node != SPA_ID_INVALID && p->node != 0)
			break;
		usleep(25000);
	}
	if (p->node == SPA_ID_INVALID || p->node == 0)
		goto fault;
	printf("      [stage] node %u, holds from %ux%u to %ux%u\n",
	       p->node, min_l, min_a, max_l, max_a);
	return p;

fault:
	printf("      [stage] ⛔ does not open\n");
	return NULL;
}

/* ⭐ THE STAGE REDOES ITS OFFER ON THE FLY — it is the lever of case 5.
 *
 * ⛔ If `fixed`, the stage demands EXACTLY `l x a`: it is the producer that
 *    tries to impose its own size on a consumer that offers a fixed and
 *    different one.  If not `fixed`, it is a new range. */
static int stage_reproposes(Stage *p, uint32_t min_l, uint32_t min_a,
                           uint32_t max_l, uint32_t max_a, bool fixed)
{
	uint8_t space[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *par[1];
	int outcome;

	p->min_l = min_l; p->min_a = min_a;
	p->max_l = max_l; p->max_a = max_a;
	p->fixed = fixed;

	pw_thread_loop_lock(p->cycle);
	par[0] = stage_proposal(&b, p);
	outcome = pw_stream_update_params(p->flow, par, 1);
	pw_thread_loop_unlock(p->cycle);
	printf("      [stage] re-offers %s %ux%u..%ux%u → %d\n",
	       fixed ? "FIXED" : "range", min_l, min_a, max_l, max_a, outcome);
	return outcome;
}

static void stage_close(Stage *p)
{
	if (!p)
		return;
	if (p->cycle)
		pw_thread_loop_stop(p->cycle);
	if (p->flow)
		pw_stream_destroy(p->flow);
	if (p->core)
		pw_core_disconnect(p->core);
	if (p->context)
		pw_context_destroy(p->context);
	if (p->cycle)
		pw_thread_loop_destroy(p->cycle);
	free(p);
}

/* ------------------------------------------------------------------ *
 *  The outcomes
 * ------------------------------------------------------------------ */
static int passed, failed;

static void outcome(const char *label_name, bool all_ok, const char *expected_val, const char *seen_v)
{
	if (all_ok) {
		printf("  \033[1;32mOK\033[0m  %s\n        %s\n", label_name, seen_v);
		passed++;
	} else {
		printf("  \033[1;31mNO\033[0m  %s\n        expected: %s\n        seen:     %s\n",
		       label_name, expected_val, seen_v);
		failed++;
	}
}

static void wait_for(double seconds)
{
	usleep((useconds_t)(seconds * 1000000.0));
}

static double now_ms(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1000.0 + t.tv_nsec / 1000000.0;
}

/* =====================================================================
 *  1 — ⭐ THE POSITIVE CONTROL OF THE INSTRUMENT, and it goes first.
 *
 *  ⛔ Case 3 requires `capture_take()` to answer **FAULT** on a
 *     dead stream.  A `capture_take()` that answered FAULT **always** would
 *     make it green by construction.  ⇒ Here the stream is HEALTHY and no
 *     frame arrives (the fake stage queues no buffer): the right answer
 *     is **ZERO**, not FAULT (`CODER.md` §3.10 — «a denied reading is not a
 *     reading that says zero»).
 *
 *  ⚠ And the same case certifies `says()`: the log MUST contain the line
 *    «capture started on node», which is certainly there.  If it did not find it,
 *    every other case that requires an absence would be green through a defect of the
 *    instrument.
 * ===================================================================== */
static void case1(void)
{
	Stage *p;
	Capture *c;
	GError *mistake = NULL;
	CaptureStopped fo;
	CaptureTake take;
	uint32_t nl = 0, na = 0;
	bool all_ok, instrument;
	char seen_v[600];

	log_reset();
	p = stage_open(320, 240, 4096, 4096);
	if (!p) {
		outcome("1 positive control: healthy stream ⇒ ZERO, and the instrument sees", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = capture_start(p->node, 1920, 1080, 30, CAPTURE_ROUTE_MEMORY,
	                  CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
	if (!c) {
		outcome("1 positive control: healthy stream ⇒ ZERO, and the instrument sees", false,
		      "the capture attaches to the fake stage's node",
		      mistake ? mistake->message : "⛔ capture_start said no");
		g_clear_error(&mistake);
		stage_close(p);
		return;
	}
	wait_for(1.0);
	log_reread();
	instrument = says("capture started on node");
	capture_measure_negotiated(c, &nl, &na);
	take = capture_take(c, 0.008, &fo, &mistake);
	capture_stopped_free(&fo);

	all_ok = instrument && nl == 1920 && na == 1080 && take == CAPTURE_TAKE_ZERO
	    && !says("DIVERGENT SIZE");
	snprintf(seen_v, sizeof seen_v,
	         "the instrument %s the start line; negotiated %ux%u; capture_take → "
	         "%s (%s); DIVERGENT SIZE line: %s",
	         instrument ? "SEES" : "⛔ does NOT see", nl, na,
	         take == CAPTURE_TAKE_ZERO ? "ZERO" :
	         take == CAPTURE_TAKE_DONE ? "DONE" : "⛔ FAULT",
	         mistake ? mistake->message : "no error",
	         says("DIVERGENT SIZE") ? "⛔ NAMES IT" : "absent");
	g_clear_error(&mistake);
	outcome("1 positive control: healthy stream ⇒ ZERO, and the instrument sees", all_ok,
	      "start line SEEN · negotiated 1920x1080 · capture_take = ZERO (NOT "
	      "fault) · no DIVERGENT SIZE", seen_v);
	capture_stop(c);
	stage_close(p);
}

/* =====================================================================
 *  2 — ⛔ PROPOSAL 1 PUT TO THE TEST: *«`figlio.c` has no way of knowing
 *      that the renegotiation KILLED the capture: today it only finds out from the
 *      TIMEOUT of `cattura_prendi`»*.
 *
 *  ⭐ The hypothesis to DISPROVE is that one: that the route is not there, and that when
 *     it is there it costs a timeout.  ⇒ It is timed.
 *
 *  THE SCENE: stage up to 1920x1080; 2560x1440 is requested; then
 *  `capture_take()` is called with **the same wait as the child's loop**
 *  (`MOTION_WAIT_S 0.008`, `figlio.c:3136`), in a loop, timing it.
 *
 *  EXPECTED, declared before the run — and it is the expected result of the PROPOSAL, that is
 *  the one to be disproved: `capture_take()` must either not notice, or
 *  notice by spending the whole wait (>= 8 ms per round).
 * ===================================================================== */
static void case2(void)
{
	Stage *p;
	Capture *c;
	GError *mistake = NULL;
	CaptureStopped fo;
	CaptureRecanvas r;
	double t0, t_fault = -1.0;
	int rounds = 0, zero_rounds = 0;
	char message[300] = "";
	bool names_state, all_ok;
	char seen_v[900];

	log_reset();
	p = stage_open(320, 240, 1920, 1080);
	if (!p) {
		outcome("2 the dead stream is KNOWN, and what knowing it costs", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = capture_start(p->node, 1920, 1080, 30, CAPTURE_ROUTE_MEMORY,
	                  CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
	if (!c) {
		outcome("2 the dead stream is KNOWN, and what knowing it costs", false,
		      "the capture attaches to the fake stage's node",
		      mistake ? mistake->message : "⛔ capture_start said no");
		g_clear_error(&mistake);
		stage_close(p);
		return;
	}
	wait_for(1.0);
	log_reset();

	r = capture_resize(c, 2560, 1440);
	t0 = now_ms();

	/* ⛔ The child's loop, reproduced: `capture_take(MOTION_WAIT_S)`
	 *    until it says something other than ZERO.  ⚠ The ceiling is 2 seconds:
	 *    beyond it, the proposal is right and this case is red. */
	while (now_ms() - t0 < 2000.0) {
		CaptureTake take = capture_take(c, 0.008, &fo, &mistake);
		rounds++;
		if (take == CAPTURE_TAKE_ZERO) {
			zero_rounds++;
			g_clear_error(&mistake);
			capture_stopped_free(&fo);
			continue;
		}
		if (take == CAPTURE_TAKE_FAULT) {
			t_fault = now_ms() - t0;
			snprintf(message, sizeof message, "%s",
			         mistake ? mistake->message : "no detail");
			g_clear_error(&mistake);
			capture_stopped_free(&fo);
			break;
		}
		capture_stopped_free(&fo);
		g_clear_error(&mistake);
	}
	log_reread();

	/* ⛔ «It says so» is not enough: it must ALSO say WHY.  A FAULT without the state
	 *    and without the producer's fault would leave the caller to deduce. */
	names_state = strstr(message, "error") != NULL;

	all_ok = r == CAPTURE_RECANVAS_REQUESTED && t_fault >= 0.0 && t_fault < 100.0
	    && names_state;
	snprintf(seen_v, sizeof seen_v,
	         "resize → %d (0 = «requested»); then %d rounds of 8 ms (%d ZERO) and "
	         "the FAULT arrives at %.1f ms; the message %s the state: «%s»",
	         (int)r, rounds, zero_rounds, t_fault,
	         names_state ? "NAMES" : "⛔ does NOT name", message);
	outcome("2 the dead stream is KNOWN, and what knowing it costs", all_ok,
	      "⇒ to DISPROVE proposal 1: FAULT within 100 ms (not a timeout) and "
	      "a message that names the state «error»", seen_v);
	capture_stop(c);
	stage_close(p);
}

/* =====================================================================
 *  3 — ⛔⛔ THE REAL DEFECT BEHIND PROPOSAL 1, and it is not in
 *      `cattura.c`: **the remount at the size that has just killed the stage**.
 *
 *  `figlio.c:6299` remounts with `take_stage(canvas_intended_w, canvas_intended_h, …)`
 *  — that is with **the size the client wants**, which is exactly the one that
 *  killed the stream.  And `figlio.c:6385` chooses the SHORT wait when
 *  `requested_codec && canvas_intended_w`, that is precisely when someone is watching.
 *
 *  ⇒ The question that decides whether it is a loop or a noose: **does a new
 *    `capture_start()` at the same size, on the same stage, produce a LIVE stage?**
 *
 *  ⛔⛔ AND THE QUESTION COMES IN TWO STEPS, because the first draft of this case
 *      looked only at the return value and would have been **green the wrong way round**:
 *      `[M]` `capture_start()` at 2560x1440 on a stage that reaches 1920x1080
 *      **SUCCEEDS 3 times out of 3** — a good pointer comes back.  ⇒ Looking at the
 *      return means concluding «it is not a noose» when it is: the
 *      negotiation is not yet over when the stream is already `paused`.
 *      ⇒ The stage is looked at **shortly after**, with the same `capture_take()` as the
 *      child's loop.
 *
 *  EXPECTED, declared before the run: if every remount dies at once,
 *  `figlio.c:6299` retries the same size forever and does not get out by itself.
 * ===================================================================== */
static void case3(void)
{
	Stage *p;
	Capture *c;
	GError *mistake = NULL;
	CaptureStopped fo;
	int attempts = 3, mounted = 0, living = 0;
	char first[300] = "";
	bool all_ok;
	char seen_v[800];

	log_reset();
	p = stage_open(320, 240, 1920, 1080);
	if (!p) {
		outcome("3 the remount at the size that killed the stage", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	for (int i = 0; i < attempts; i++) {
		CaptureTake take;

		c = capture_start(p->node, 2560, 1440, 30, CAPTURE_ROUTE_MEMORY,
		                  CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
		if (!c) {
			if (!first[0])
				snprintf(first, sizeof first, "capture_start: %s",
				         mistake ? mistake->message : "no detail");
			g_clear_error(&mistake);
			continue;
		}
		mounted++;
		g_clear_error(&mistake);
		/* ⛔ 300 ms: the death measured by case 2 arrives within 10 ms, and this is
		 *    thirty times that — it is not a wait tuned to the result. */
		wait_for(0.3);
		take = capture_take(c, 0.008, &fo, &mistake);
		capture_stopped_free(&fo);
		if (take != CAPTURE_TAKE_FAULT)
			living++;
		else if (!first[0])
			snprintf(first, sizeof first, "%s",
			         mistake ? mistake->message : "no detail");
		g_clear_error(&mistake);
		capture_stop(c);
	}
	log_reread();

	all_ok = living == 0;
	snprintf(seen_v, sizeof seen_v,
	         "%d `capture_start()` out of %d RETURNED a stage at 2560x1440 "
	         "(a size the stage cannot hold), but only %d were still ALIVE 300 "
	         "ms later: %s.  The refusal: «%s»",
	         mounted, attempts, living,
	         living == 0 ? "⛔ none ⇒ `figlio.c:6299` would retry the same "
	                     "size forever, with the SHORT wait of `:6385`"
	                   : "⭐ some hold ⇒ it is not a noose",
	         first);
	outcome("3 the remount at the size that killed the stage", all_ok,
	      "0 live stages out of 3 (⇒ the loop of `figlio.c:6299` does not get out by itself), "
	      "and `capture_start()` that SUCCEEDS all the same", seen_v);
	stage_close(p);
}

/* =====================================================================
 *  4 — ⭐⭐ PROPOSAL 3 PUT TO THE TEST: *«only a RACE is left, and a bench
 *      cannot program a race»*.
 *
 *  ⛔ The hypothesis to disprove.  The scene is not a laboratory race: it is
 *     **two chained `FIT_CANVAS`**, that is the user DRAGGING the edge
 *     of the window — the same scene that `DECISIONI.md` §5.0-sexies names
 *     («among which two chained `ADATTA_TELA`»).
 *
 *  THE MECHANICS, and that is why it is programmable rather than random:
 *    · `capture_resize(A)` writes `chiesta_* = A` **on the caller's
 *      thread** and then renegotiates; the answer (`on_parameters`) arrives **later**,
 *      on the PipeWire thread;
 *    · `capture_resize(B)` right after, without waiting, rewrites
 *      `chiesta_* = B`;
 *    · if the `Format` of A arrives when `chiesta_*` is already B ⇒ granted A,
 *      requested B ⇒ ⛔ **DIVERGENT SIZE**.
 *
 *  ⚠ The stage holds both sizes: there is no refusal in between, the
 *    scene is completely HEALTHY.
 *
 *  EXPECTED, declared before the run: if the line appears, proposal 3 is
 *  DISPROVED and the branch must be tested, not declared dead.  ⚠ If it does not appear, the
 *  chain is repeated several times before concluding: a race that does not fire at the
 *  first shot is not a race that does not exist.
 * ===================================================================== */
static void case4(void)
{
	Stage *p;
	Capture *c;
	GError *mistake = NULL;
	uint32_t cl = 0, ca = 0, nl = 0, na = 0;
	int chains = 160, fired = -1;
	char row[300] = "";
	bool all_ok;
	char seen_v[700];

	log_reset();
	p = stage_open(320, 240, 4096, 4096);
	if (!p) {
		outcome("4 two chained resizes ⇒ DIVERGENT SIZE?", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = capture_start(p->node, 1920, 1080, 30, CAPTURE_ROUTE_MEMORY,
	                  CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
	if (!c) {
		outcome("4 two chained resizes ⇒ DIVERGENT SIZE?", false,
		      "the capture attaches to the fake stage's node",
		      mistake ? mistake->message : "⛔ capture_start said no");
		g_clear_error(&mistake);
		stage_close(p);
		return;
	}
	wait_for(1.0);
	log_reset();

	/* ⛔⛔ THE DELAY BETWEEN THE TWO CALLS IS SWEPT, and it is not a detail:
	 *     with the two calls BACK TO BACK (delay 0) the line appears `[M]` **2
	 *     times out of 10 rounds of 40 chains** — that is, it is a real race, and a bench
	 *     that stopped there would be green or red at random.
	 *
	 * ⭐ The window has a physical width: it is the time the `Format` of A
	 *    takes to come back from the server.  If the second call arrives BEFORE
	 *    A leaves, the server answers only once (with B) and there is nothing to
	 *    diverge; if it arrives AFTER A has been delivered, `chiesta_*` was
	 *    still A and neither.  ⇒ The delay that falls in between is searched for.
	 *
	 * ⚠ And it is swept instead of guessed: a delay chosen by hand would be a
	 *   number tuned to the machine of whoever wrote it. */
	{
		static const int delays_us[] = {0, 50, 100, 200, 400, 800, 1600, 3200};
		const int how_many_r = (int)(sizeof delays_us / sizeof delays_us[0]);
		const int per_delay = chains / how_many_r;

		/* ⛔ AND IT DOES NOT STOP AT THE FIRST HIT: EVERYTHING is swept.  Stopping
		 *    would give «fired» and no profile, that is the number that is needed —
		 *    which delay makes it fire — would remain unknown. */
		for (int r = 0; r < how_many_r; r++) {
			int shots = 0;
			for (int k = 0; k < per_delay; k++) {
				int i = r * per_delay + k;
				uint32_t a_l = 1200 + (uint32_t)(i % 7) * 2u;
				uint32_t a_a =  800 + (uint32_t)(i % 5) * 2u;
				uint32_t b_l = 1600 + (uint32_t)(i % 3) * 2u;
				uint32_t b_a = 1000 + (uint32_t)(i % 11) * 2u;

				/* ⛔ The log is reset AT EVERY CHAIN, or from the first hit
				 *    on `says()` would answer «yes» forever and every later
				 *    delay would come out as a hit. */
				log_reset();
				capture_resize(c, a_l, a_a);
				if (delays_us[r])
					usleep((useconds_t)delays_us[r]);
				capture_resize(c, b_l, b_a);
				wait_for(0.03);
				log_reread();
				if (says("DIVERGENT SIZE")) {
					shots++;
					if (fired < 0) {
						const char *q = strstr(seen_log,
						                       "DIVERGENT SIZE");
						/* ⛔ Cut at the first full stop: the rest of the
						 *    line is the explanation, and here the
						 *    NUMBERS are what matters. */
						const char *fine = strstr(q, ".  ");
						fired = delays_us[r];
						snprintf(row, sizeof row, "%.*s",
						         (int)(fine ? (size_t)(fine - q)
						                    : strlen(q)), q);
						printf("      [chain] requested A=%ux%u then B=%ux%u "
						       "⇒ «%s»\n", a_l, a_a, b_l, b_a, row);
					}
				}
			}
			printf("      [chain] delay %5d us: %d hits out of %d\n",
			       delays_us[r], shots, per_delay);
		}
	}

	capture_measure_requested(c, &cl, &ca);
	capture_measure_negotiated(c, &nl, &na);

	/* ⛔ This case is GREEN when the line APPEARS: it is a bench written to
	 *    disprove, and its green is the disproof. */
	all_ok = fired >= 0;
	snprintf(seen_v, sizeof seen_v,
	         "over %d chains of two resizes (8 delays swept) the "
	         "DIVERGENT SIZE line %s%d; final requested %ux%u, negotiated %ux%u",
	         chains,
	         fired >= 0 ? "⭐ APPEARED ⇒ proposal 3 is DISPROVED, the branch "
	                         "is reachable from outside — first hit with the delay "
	                         "in us "
	                       : "⛔ does NOT appear ⇒ proposal 3 HOLDS; chains spent: ",
	         fired >= 0 ? fired : chains,
	         cl, ca, nl, na);
	outcome("4 two chained resizes ⇒ DIVERGENT SIZE?", all_ok,
	      "the line APPEARS (⇒ proposal 3 disproved)", seen_v);
	capture_stop(c);
	stage_close(p);
}

/* =====================================================================
 *  5 — ⭐ THE OTHER ROUTE TO DISPROVE PROPOSAL 3: **the producer tries to
 *      IMPOSE its size**.
 *
 *  `cattura.c:~1069` offers the size as `SPA_POD_Rectangle`, that is FIXED.
 *  The argument of proposal 3 is structural: the intersection of a fixed
 *  rectangle with anything is either that rectangle or the empty set.  ⇒ It is put
 *  to the test by asking the stage to **redo its own offer** with a
 *  DIFFERENT fixed rectangle, with the stream live.
 *
 *  EXPECTED, declared before the run: either the consumer receives a `Format` at the
 *  PRODUCER's size (⇒ divergence, proposal 3 disproved by this route),
 *  or the negotiation fails and the stream dies (⇒ the structural argument holds).
 *
 *  ⛔ MEASURED, 22 August 2026, PipeWire 1.4.2: **the stream dies**
 *     (`paused → error — no more input formats`), no new `Format`, no
 *     divergence.  ⇒ By THIS route proposal 3 holds, and the disproof is
 *     all case 4's — which goes through another door: not «the producer imposes
 *     another size», but «`chiesta_*` has already changed when the answer
 *     arrives».  ⚠ The green of this case is therefore the death of the stream: it is the
 *     control that keeps case 4 honest, because it shows that the divergence
 *     of case 4 **cannot** come from the producer.
 * ===================================================================== */
static void case5(void)
{
	Stage *p;
	Capture *c;
	GError *mistake = NULL;
	uint32_t nl = 0, na = 0, cl = 0, ca = 0;
	bool divergent, in_error, all_ok;
	char seen_v[800];

	log_reset();
	p = stage_open(320, 240, 4096, 4096);
	if (!p) {
		outcome("5 the producer tries to IMPOSE its size", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = capture_start(p->node, 1920, 1080, 30, CAPTURE_ROUTE_MEMORY,
	                  CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
	if (!c) {
		outcome("5 the producer tries to IMPOSE its size", false,
		      "the capture attaches to the fake stage's node",
		      mistake ? mistake->message : "⛔ capture_start said no");
		g_clear_error(&mistake);
		stage_close(p);
		return;
	}
	wait_for(1.0);
	log_reset();

	/* ⛔ The stage demands a FIXED 1600x900, while the consumer has 1920x1080. */
	stage_reproposes(p, 1600, 900, 1600, 900, true);
	wait_for(1.0);
	log_reread();

	capture_measure_requested(c, &cl, &ca);
	capture_measure_negotiated(c, &nl, &na);
	divergent = says("DIVERGENT SIZE");
	in_error = says("→ error");

	/* ⛔ Green = the producer did NOT manage it.  ⚠ If one day the divergence
	 *    appeared from here, this case turns red — and that is what is wanted:
	 *    it would mean that the fixed rectangle is no longer a guarantee, and that
	 *    case 4 has a second source to tell apart. */
	all_ok = !divergent && in_error && nl == 1920 && na == 1080;
	snprintf(seen_v, sizeof seen_v,
	         "the stage demanded a fixed 1600x900; requested %ux%u, negotiated %ux%u; "
	         "stream %s; DIVERGENT SIZE: %s",
	         cl, ca, nl, na, in_error ? "in ERROR" : "⛔ alive",
	         divergent ? "⛔ APPEARED ⇒ the producer IMPOSES, and case 4 has a "
	                      "second source"
	                    : "absent ⇒ the FIXED rectangle holds: either that value, or "
	                      "the empty set");
	outcome("5 the producer tries to IMPOSE its size", all_ok,
	      "still negotiated 1920x1080 · stream in error · NO divergence "
	      "(⇒ the producer cannot impose)", seen_v);
	capture_stop(c);
	stage_close(p);
}

/* =====================================================================
 *  6 — ⛔ PROPOSAL 2 PUT TO THE TEST: is an accessor for the divergence needed?
 *
 *  The argument of the proposal: `measure_divergent` is written and never read, and
 *  `cattura.h` does not expose it ⇒ no caller can know it.
 *
 *  ⭐ The hypothesis to disprove: that the caller CANNOT know it.  `cattura.h`
 *     already exposes **two** accessors — `capture_measure_requested()` and
 *     `capture_measure_negotiated()` — and the divergence is their inequality.
 *     ⇒ It is checked that the two are enough to reconstruct it, including the case in which the
 *     format is not yet known (where the third field would lie: it is `FALSE`
 *     because there is nothing to compare yet, not because everything is
 *     fine — `CODER.md` §3.10).
 * ===================================================================== */
static void case6(void)
{
	Stage *p;
	Capture *c;
	GError *mistake = NULL;
	uint32_t cl = 0, ca = 0, nl = 0, na = 0;
	gboolean known_before, known_after;
	/* ⛔ The BEFORE numbers are kept in their own variables: the first draft of
	 *    this case reprinted them as `0` written by hand in the `printf`, that is
	 *    the bench STATED a number it had not read — the author's defect,
	 *    found by rereading the output. */
	uint32_t cl0 = 0, ca0 = 0, nl0 = 0, na0 = 0;
	bool all_ok;
	char seen_v[800];

	log_reset();
	p = stage_open(320, 240, 1920, 1080);
	if (!p) {
		outcome("6 the two accessors are enough to reconstruct the divergence", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = capture_start(p->node, 1920, 1080, 30, CAPTURE_ROUTE_MEMORY,
	                  CAPTURE_COLOR_BGRX, NULL, NULL, NULL, &mistake);
	if (!c) {
		outcome("6 the two accessors are enough to reconstruct the divergence", false,
		      "the capture attaches to the fake stage's node",
		      mistake ? mistake->message : "⛔ capture_start said no");
		g_clear_error(&mistake);
		stage_close(p);
		return;
	}
	wait_for(1.0);
	capture_measure_requested(c, &cl0, &ca0);
	known_before = capture_measure_negotiated(c, &nl0, &na0);

	/* ⛔ The request the stage cannot hold: from here on «requested» and
	 *    «negotiated» diverge, and the two PUBLIC accessors say so. */
	capture_resize(c, 2560, 1440);
	wait_for(0.5);
	capture_measure_requested(c, &cl, &ca);
	known_after = capture_measure_negotiated(c, &nl, &na);

	all_ok = known_before && cl0 == 1920 && ca0 == 1080 && nl0 == 1920 && na0 == 1080
	    && known_after && cl == 2560 && ca == 1440 && nl == 1920 && na == 1080;
	snprintf(seen_v, sizeof seen_v,
	         "before: requested %ux%u, negotiated %s%ux%u.  After the request the "
	         "stage cannot hold: requested %ux%u, negotiated %s%ux%u ⇒ the divergence "
	         "%s from the two public accessors, and without the private field",
	         cl0, ca0, known_before ? "" : "⛔ UNKNOWN ", nl0, na0,
	         cl, ca, known_after ? "" : "⛔ UNKNOWN ", nl, na,
	         (cl != nl || ca != na) ? "CAN BE READ" : "⛔ cannot be read");
	outcome("6 the two accessors are enough to reconstruct the divergence", all_ok,
	      "requested 2560x1440 · negotiated 1920x1080, both readable from "
	      "`cattura.h` without a third accessor", seen_v);
	capture_stop(c);
	stage_close(p);
}

int main(int argc, char **argv)
{
	int solo = argc > 1 ? atoi(argv[1]) : 0;
	void (*cases[])(void) = {case1, case2, case3, case4, case5, case6};
	const int how_many = (int)(sizeof cases / sizeof cases[0]);

	chatter = getenv("PARLANTINA") != NULL;
	pw_init(&argc, &argv);
	/* ⛔ The LOG's verbosity is ALWAYS switched on: «stream state: paused
	 *    → error» is `log_detail()` (`cattura.c:318`) and with verbosity
	 *    off it is not written at all — the cases that REQUIRE that line
	 *    would be red for a reason unrelated to what they measure. */
	log_chatter(true);
	log_redirect();

	printf("\n== 06-b5: the three proposals of 06-b40, put to the test to DISPROVE them ==\n\n");
	for (int i = 0; i < how_many; i++) {
		if (solo && solo != i + 1)
			continue;
		cases[i]();
	}
	printf("\n  passed %d, failed %d\n\n", passed, failed);
	return failed ? 1 : 0;
}
