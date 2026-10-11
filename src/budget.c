/* budget.c — ⭐⭐⭐ THE COMPOSITION BUDGET (phase 10, 25 Aug 2026).
 *
 * ⛔ The reason for every number is in `budget.h`, at the top: here there is
 *    only the mechanism.  Whoever changes a number reads that box first, or
 *    will change a calibration believing they are fixing an implementation.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "budget.h"
#include "log.h"

/* ─────────────────────────────────────────────────────────────────────────────
 * ⭐ THE DELIVERED WINDOW — eight buckets of 250 ms, that is two seconds.
 *
 * ⛔ And the buckets needs one thing only that an incremental average cannot do:
 *    **make the delivered DECAY when frames stop arriving**.  A session that
 *    stops must go down towards zero on its own, or it would stay counted at
 *    the rate it had when it was working — and then the count would say
 *    «full» on an empty machine (false NO on everyone who arrives).
 *
 * ⚠ Two seconds and not twenty: `[M]` §6.16 — when eight idle sessions wake up
 *   the **rate** collapses within the first interval of the yardstick (**less
 *   than 2 s**), while the delay rises in 8-10 s.  A longer window would see
 *   the wake-up too late; a shorter one would count the hiccup of one lost
 *   frame as a collapse.
 * ─────────────────────────────────────────────────────────────────────────── */
#define BUCKETS 8
#define BUCKET_US 250000ull
#define WINDOW_US ((uint64_t)BUCKETS * BUCKET_US)

/* ⛔⭐ HOW MANY DELAYS ARE KEPT, AND WHY THE MEDIAN AND NOT THE MAXIMUM.
 *
 *     The maximum would refuse a user for **a single hiccup** — a false NO on
 *     a datum that does not describe the state of the machine.  The median of
 *     32 samples describes *where the session sits*, and it is the same
 *     quantity that `[M]` §6.5/§6.9 measured («median delay» at every step):
 *     calibrating on one quantity and judging on another is the fastest way
 *     to have an uncalibrated yardstick.
 * ⚠ At ~40 fps, 32 samples are **0.8 s** — the same scale as the window. */
#define DELAYS 32

/* ⛔⭐ THE DELAY SAMPLES **DO NOT EXPIRE**, and it is a choice, not an
 *     oversight.
 *
 *     An **idle** session delivers `[M]` one frame every ~40 s (0.05
 *     Mpixel/s, §6.9): if its samples expired, it would be left **without a
 *     delay**, and the declared fallback (§1.33, uncomfortable direction)
 *     would count it at the worst case.  ⇒ ⛔ **Ten idle tenants would be
 *     rejected while costing nothing** — which is the twin error, and just as
 *     serious, of admitting the eighth that makes everything collapse.
 * ⭐ And in the opposite direction the choice is prudent: a **throttled**
 *    session that goes silent carries its big delay along until it delivers
 *    again.
 */

struct tenant {
	bool used;
	char user[257];
	/* the composed pixels delivered, per bucket */
	uint64_t pixel[BUCKETS];
	int bucket;              /* index of the current bucket */
	uint64_t bucket_from_us;   /* the instant the current bucket was born */
	uint64_t first_us;        /* the first frame ever seen */
	uint64_t last_us;       /* the last one, for slot reuse */
	bool never_delivered;
	uint32_t canvas_w, canvas_h;  /* the last canvas delivered */
	uint32_t delay_ms[DELAYS];
	int how_many_delays, next_delay;
};

static struct tenant *table;
static int how_many_cells;

/* ⛔ `0` = OFF, and it is the default: I6.  See `budget.h` point 5. */
static double capacity_mpixel_s;
static double reserve = BUDGET_DEFAULT_RESERVE;
static uint32_t canvas_stage_w, canvas_stage_h;

/* ------------------------------------------------------------------------- */

static uint64_t now_us(bool *was_read)
{
	struct timespec t;

	if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) {
		/* ⛔ «I could not read the time» is not «it is midnight»: whoever
		 *    receives this declares it and does not judge. */
		if (was_read)
			*was_read = false;
		return 0;
	}
	if (was_read)
		*was_read = true;
	return (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
}

/* ⛔ The table is sized on the cap in force, and allocated at the first
 *    switch-on.  ⚠ If `calloc` fails, the budget **does not turn on**: a
 *    budget that cannot count must not be able to say no. */
static bool table_ready(int how_many)
{
	if (table)
		return true;
	if (how_many < 1)
		how_many = 1;
	table = (struct tenant *)calloc((size_t)how_many, sizeof *table);
	if (!table) {
		registro_dice(REG_BUDGET,
		              "⛔ there is no memory for the budget table (%d "
		              "slots): the budget stays OFF.  ⚠ It is not «it holds»: it is "
		              "«I do not count», and whoever does not count does not say no",
		              how_many);
		return false;
	}
	how_many_cells = how_many;
	return true;
}

/* ⭐ The user's slot, or the oldest one if it is not there and there is no room.
 *
 * ⛔ Oldest-first reuse looks at `last_us`, and it is needed because NOBODY
 *    tells this module that a stage has died: a tenant that vanished simply
 *    stops delivering, and its slot becomes the oldest.
 * ⚠ And it is not a disguised defect: a stale slot never enters the count,
 *   because the count is filled by the table of **live stages** and not by
 *   this one (see `budget_count_inside()`). */
static struct tenant *cell(const char *user, bool create)
{
	struct tenant *free_fn = NULL, *old = NULL;

	if (!table || !user || !user[0])
		return NULL;
	for (int i = 0; i < how_many_cells; i++) {
		struct tenant *in = &table[i];

		if (!in->used) {
			if (!free_fn)
				free_fn = in;
			continue;
		}
		if (strcmp(in->user, user) == 0)
			return in;
		if (!old || in->last_us < old->last_us)
			old = in;
	}
	if (!create)
		return NULL;
	if (!free_fn)
		free_fn = old;
	if (!free_fn)
		return NULL;
	memset(free_fn, 0, sizeof *free_fn);
	free_fn->used = true;
	free_fn->never_delivered = true;
	snprintf(free_fn->user, sizeof free_fn->user, "%s", user);
	return free_fn;
}

/* ⛔ Brings the window up to `t_now`, emptying the buckets that went out.
 *    ⚠ It is what makes the delivered of whoever stopped DECAY: without
 *      this call at verdict time too (not only at deposit), an idle session
 *      would stay counted at the rate it had. */
static void advances(struct tenant *in, uint64_t t_now)
{
	if (in->never_delivered)
		return;
	if (t_now < in->bucket_from_us)
		return;  /* ⚠ the clock is monotonic: it should not happen */
	while (t_now - in->bucket_from_us >= BUCKET_US) {
		in->bucket_from_us += BUCKET_US;
		in->bucket = (in->bucket + 1) % BUCKETS;
		in->pixel[in->bucket] = 0;
		/* ⭐ If the gap is longer than the whole window we do not loop a
		 *    thousand times: everything is zeroed and restarted from now. */
		if (t_now - in->bucket_from_us >= WINDOW_US) {
			memset(in->pixel, 0, sizeof in->pixel);
			in->bucket_from_us = t_now;
			in->bucket = 0;
			return;
		}
	}
}

/* ⭐ The delivered, in Mpixel/s.  ⛔ Returns `false` when **nothing has been
 *    measured**, and whoever receives it counts the worst case: «I have not
 *    measured» is not «zero» — a session just born has not delivered anything
 *    yet, and counting it zero is exactly the error that starves everyone. */
static bool delivered(struct tenant *in, uint64_t t_now, double *mpixel_s)
{
	uint64_t total_sum = 0;
	double seconds;

	if (!in || in->never_delivered)
		return false;
	/* ⛔ Until there is a WHOLE window of history the number does not describe
	 *    a rate: it describes «how recently it was born».  ⇒ Not measured. */
	if (t_now < in->first_us + WINDOW_US)
		return false;
	advances(in, t_now);
	for (int i = 0; i < BUCKETS; i++)
		total_sum += in->pixel[i];
	/* ⚠ We divide by the time COVERED — the full buckets plus the fraction of
	 *   the current one — and not by the nominal window: the current bucket is
	 *   on average half full, and dividing it by its whole bucket would
	 *   underestimate the demand by ~6 %.  ⛔ Underestimating the demand is the
	 *   direction that starves everyone (§1.33). */
	seconds = (double)(BUCKETS - 1) * (double)BUCKET_US / 1e6;
	seconds += (double)(t_now - in->bucket_from_us) / 1e6;
	if (seconds <= 0.0)
		return false;
	*mpixel_s = (double)total_sum / 1e6 / seconds;
	return true;
}

/* ⭐ The median of the kept delays.  `false` = never delivered anything, so
 *    there is nothing to take the median of — and it is not «zero delay». */
static bool median_delay(const struct tenant *in, double *ms)
{
	uint32_t v[DELAYS];
	int n;

	if (!in || in->how_many_delays <= 0)
		return false;
	n = in->how_many_delays;
	memcpy(v, in->delay_ms, (size_t)n * sizeof v[0]);
	/* ⚠ Insertion sort on at most 32 elements, once per verdict: `qsort`
	 *   here would cost more lines than it saves. */
	for (int i = 1; i < n; i++)
		for (int j = i; j > 0 && v[j] < v[j - 1]; j--) {
			uint32_t t = v[j];
			v[j] = v[j - 1];
			v[j - 1] = t;
		}
	*ms = (double)v[n / 2];
	return true;
}

/* ⭐ The worst case of a canvas: its canvas times the maximum rate this
 *    hardware has shown it can deliver (§6.9, and see `budget.h`). */
static double worst(uint32_t l, uint32_t a)
{
	return (double)l * (double)a / 1e6 * BUDGET_MAX_FPS;
}

/* ------------------------------------------------------------------------- */

void budget_turn_on(double capabilities, double f, uint32_t canvas_w, uint32_t canvas_h)
{
	canvas_stage_w = canvas_w;
	canvas_stage_h = canvas_h;
	reserve = f;
	if (reserve < 0.0)
		reserve = 0.0;
	if (reserve > 1.0)
		reserve = 1.0;
	capacity_mpixel_s = capabilities > 0.0 ? capabilities : 0.0;
	if (capacity_mpixel_s > 0.0 && !table_ready(how_many_cells))
		capacity_mpixel_s = 0.0;
}

/* ⛔ The table is sized **before** switching on: `main.c` calls it with the
 *    cap in force, so the slots are as many as the possible stages and
 *    oldest-first reuse never bites in normal operation. */
void budget_cells(int how_many)
{
	if (!table)
		how_many_cells = how_many;
}

bool budget_on(void)
{
	return capacity_mpixel_s > 0.0 && table != NULL;
}

/* ⛔ The two counts of the noes, and they live here because this is where
 *    they are written.  ⚠ They are never reset: they are «since this server
 *    started», which is the only window a log reader can reconstruct. */
static uint64_t questions_seen, all_denied, denied_budget;

void budget_verdict_line(const char *user, bool admitted, uint8_t reason,
                          int session_cap, const char *why)
{
	questions_seen++;
	if (!admitted) {
		all_denied++;
		if (reason == 0x06)
			denied_budget++;
	}
	/* ⛔ ONE line per verdict, and not one per frame: we pass here at every
	 *    login, not at every pixel.  ⭐ And it is written with the budget OFF
	 *    too, because `denied 0` is the fact that proves I6 — reading it
	 *    requires someone to write it. */
	registro_dice(REG_BUDGET,
	              "verdict for «%s»: %s · denied %llu (of which budget %llu) out of "
	              "%llu requests · in force --budget-mpixel-s %.1f (%s) "
	              "--session-cap %d --reserve %.2f%s%s",
	              user ? user : "?",
	              admitted ? "⭐ ADMITTED" : "⛔ DENIED",
	              (unsigned long long)all_denied,
	              (unsigned long long)denied_budget,
	              (unsigned long long)questions_seen,
	              capacity_mpixel_s, budget_on() ? "ON" : "OFF",
	              session_cap, reserve,
	              (!admitted && why && why[0]) ? " · reason: " : "",
	              (!admitted && why && why[0]) ? why : "");
}

void budget_startup_line(int session_cap)
{
	/* ⛔⭐ THE LINE A BENCH LOOKS FOR, and it carries the THREE values with the
	 *     **option name next to the number**.  ⚠ It is written first and
	 *     always — on AND off — because it is the one whoever judges calibrates
	 *     on: an oracle calibrated on a number different from the one in force
	 *     would produce false yeses and false noes **of its own**, not of the
	 *     product. */
	registro_dice(REG_BUDGET,
	              "%s phase 10 — THE THREE VALUES IN FORCE: "
	              "budget --budget-mpixel-s %.1f (%s) · "
	              "cap --session-cap %d · "
	              "reserve --reserve %.2f",
	              budget_on() ? "⭐⭐" : "⛔",
	              capacity_mpixel_s, budget_on() ? "ON" : "OFF",
	              session_cap, reserve);
	if (budget_on())
		registro_dice(REG_BUDGET,
		              "⭐⭐ phase 10 — THE COMPOSITION BUDGET: ON at %.1f "
		              "Mpixel/s, reserve %.2f, delay threshold %.1f ms, "
		              "worst case %.2f fps (⇒ %.1f Mpixel/s for a "
		              "%ux%u), tolerance %.0f%%, %d slots.  ⛔ The quantity "
		              "is COMPOSITION, not encoding: `[M]` §6.11 the "
		              "ceiling is 0.97 Gpixel/s against 1.86 for the encoder, "
		              "and what saturates `rcs0` is the compositor.  ⛔ Whoever does not fit "
		              "receives FAREWELL 0x06 BUDGET_FULL **before** their "
		              "stage is born.  ⚠ The number does NOT self-tune (§6.9): before "
		              "the machine has given way once it is a lower "
		              "bound, not a ceiling — this was declared by whoever "
		              "typed `--budget-mpixel-s`",
		              capacity_mpixel_s, reserve, BUDGET_STRAIN_DELAY_MS,
		              (double)BUDGET_MAX_FPS,
		              worst(canvas_stage_w, canvas_stage_h), canvas_stage_w,
		              canvas_stage_h, BUDGET_TOLERANCE * 100.0, how_many_cells);
	else
		registro_dice(REG_BUDGET,
		              "⛔ phase 10 — THE COMPOSITION BUDGET: OFF "
		              "(`--budget-mpixel-s 0`, and it is the DEFAULT — "
		              "`CODER.md` I6: what changes what the user sees "
		              "is born off until they have looked at it).  ⛔⛔ With the "
		              "budget off this machine ADMITS EVERYONE: `[M]` §S.2 "
		              "on the saturated scene the eleventh gets in with `negati 0` and "
		              "the first session goes from 39.60 to 0.96 fps (−97.6 %%) "
		              "— it is the violation of I1 the budget exists to "
		              "prevent.  ⭐ It is turned on with `--budget-mpixel-s N`, where "
		              "N is the Mpixel/s of COMPOSITION this machine "
		              "holds, MEASURED at saturation (reserve in force %.2f)",
		              reserve);
}

void budget_deposit(const char *user, uint32_t width, uint32_t height,
                     uint64_t instant_us)
{
	struct tenant *in;
	bool was_read = false;
	uint64_t t_now;

	if (!budget_on() || !user || !user[0] || !width || !height)
		return;
	t_now = now_us(&was_read);
	if (!was_read)
		return;
	in = cell(user, true);
	if (!in)
		return;
	if (in->never_delivered) {
		in->never_delivered = false;
		in->first_us = t_now;
		in->bucket_from_us = t_now;
		in->bucket = 0;
	}
	advances(in, t_now);
	in->pixel[in->bucket] += (uint64_t)width * (uint64_t)height;
	in->last_us = t_now;
	in->canvas_w = width;
	in->canvas_h = height;
	/* ⛔ The delay is *capture → parent*, and the instant is stamped by the
	 *    CHILD: it is the uncomfortable direction (an upper bound), which is
	 *    the right one.
	 * ⚠ An instant ahead of our time would mean two different clocks: zero is
	 *   counted instead of subtracting backwards, and no negative number is
	 *   invented. */
	{
		uint64_t d = t_now > instant_us ? t_now - instant_us : 0;
		uint32_t ms = (uint32_t)(d / 1000ull);

		in->delay_ms[in->next_delay] = ms;
		in->next_delay = (in->next_delay + 1) % DELAYS;
		if (in->how_many_delays < DELAYS)
			in->how_many_delays++;
	}
}

void budget_count_open(struct budget_count *c)
{
	memset(c, 0, sizeof *c);
	c->now_us = now_us(&c->clock);
}

void budget_count_inside(struct budget_count *c, const char *user)
{
	struct tenant *in;
	double delivery = 0.0, delay = 0.0, pg, d;
	bool got_delivery, got_delay;
	uint32_t l, a;

	if (!c || !c->clock || !budget_on() || !user || !user[0])
		return;
	c->amount++;
	in = cell(user, false);

	/* ⚠ The canvas: that of the last frame delivered; if it has never
	 *   delivered, that of the STAGE — which is the upper bound of what it can
	 *   obtain.  ⛔ Uncomfortable direction. */
	l = (in && in->canvas_w) ? in->canvas_w : canvas_stage_w;
	a = (in && in->canvas_h) ? in->canvas_h : canvas_stage_h;
	pg = worst(l, a);

	got_delivery = delivered(in, c->now_us, &delivery);
	got_delay = median_delay(in, &delay);

	/* ── ⛔⛔ THE DELAY GATE — and it stands BEFORE the sum ────────────────
	 *
	 * `[M]` §6.9: at eight sessions the total delivered is 26.6 Mpixel/s against
	 * 480, that is the count on pixels would say *«there is room for five more»*
	 * while everyone sits at 1.5 fps.  ⇒ Whoever delivers little **with a delay
	 * above the threshold** is throttled, not idle, and admitting now violates
	 * I1 on whoever is already working. */
	if (got_delay && delay > BUDGET_STRAIN_DELAY_MS &&
	    (!c->throttled[0] || delay > c->throttled_ms)) {
		snprintf(c->throttled, sizeof c->throttled, "%s", user);
		c->throttled_ms = delay;
	}

	/* ── THE DEMAND OF THIS TENANT ────────────────────────────────────── */
	if (!got_delivery || !got_delay) {
		/* ⛔ DECLARED fallback, and in the uncomfortable direction: without
		 *    the delivered — or without the delay, which is what tells «idle»
		 *    from «throttled» — the worst case is counted. */
		d = pg;
		c->at_worst++;
	} else {
		/* ⭐⭐ THE RESERVE: the larger of what it delivers and the fraction
		 *     `F` of its worst case.  It is the defence against the WAKE-UP —
		 *     `[M]` §6.16: eight idle ones at 0.01 % each wake up in 19 ms and
		 *     ask for 130 % of an engine that has 100, and ⛔ the rate
		 *     regulator of phase 9 cannot remedy it (it holds back frames
		 *     already composed and already encoded).  At F = 0.5 the
		 *     overshoot goes from 1 640× to 2×. */
		d = pg * reserve;
		if (delivery > d)
			d = delivery;
	}
	c->question += d;
}

enum budget_outcome budget_count_verdict(struct budget_count *c,
                                        const char *fresh, uint32_t canvas_w,
                                        uint32_t canvas_h, char *why,
                                        size_t why_cap)
{
	double d_new, cap, question;

	if (why && why_cap)
		why[0] = '\0';
	if (!budget_on())
		return BUDGET_HOLDS;
	if (!c || !c->clock) {
		if (why && why_cap)
			snprintf(why, why_cap,
			         "the monotonic clock could not be read: the budget "
			         "HAS NOT MEASURED, and does not judge");
		return BUDGET_UNKNOWN;
	}
	if (c->throttled[0]) {
		if (why && why_cap)
			snprintf(why, why_cap,
			         "this machine is already struggling: the session of «%s» "
			         "delivers with %.0f ms of delay (measured threshold %.1f "
			         "ms), and letting someone in now would take frame rate away "
			         "from whoever is working.  ⭐ Try again shortly",
			         c->throttled, c->throttled_ms, BUDGET_STRAIN_DELAY_MS);
		return BUDGET_DOES_NOT_HOLD;
	}

	if (!canvas_w || !canvas_h) {
		canvas_w = canvas_stage_w;
		canvas_h = canvas_stage_h;
	}
	d_new = worst(canvas_w, canvas_h);
	question = c->question + d_new;
	cap = capacity_mpixel_s * (1.0 + BUDGET_TOLERANCE);

	if (question <= cap) {
		if (why && why_cap)
			snprintf(why, why_cap,
			         "demand %.1f ≤ %.1f Mpixel/s (%d inside%s, the newcomer "
			         "asks for %.1f at worst with %ux%u)",
			         question, cap, c->amount,
			         c->at_worst ? ", some of them counted at the worst "
			                          "case" : "",
			         d_new, canvas_w, canvas_h);
		return BUDGET_HOLDS;
	}
	/* ⛔⭐ THE BODY CARRIES THE FIGURES, and it is not decoration: **demand**
	 *     and **capacity** are the two numbers on which the no was decided, and
	 *     without them tomorrow's line cannot be reread — «the server is full»
	 *     says neither how much, nor of what.
	 *
	 * ⛔⛔ AND THE GESTURE PROMISED IS ONLY THE ONE THAT IS TRUE HERE.
	 *
	 *      At this point the session's canvas **is not decided yet** (it is
	 *      decided at `SESSION`), and the only canvas number at hand is
	 *      `video.max_size` — which is the **DECODER**'s ceiling, not the
	 *      size of the window: `src/page.html` spells it out, *«it does not
	 *      change the canvas: it is a ceiling … because a phone's decoder has
	 *      limits its screen does not declare»*, and the page measures it with
	 *      a ladder of `VideoDecoder.isConfigSupported`.
	 *      ⇒ ⛔ **Shrinking the window does NOT lower the cost counted here**:
	 *        whoever did so and tried again would receive the very same no,
	 *        and a sentence promising it would be **false**.
	 *      ⭐ What is true instead: capacity comes back as soon as someone
	 *        leaves, and a device that declares a smaller ceiling really costs
	 *        less.  ⚠ That is what is promised, and only that. */
	if (why && why_cap)
		snprintf(why, why_cap,
		         "this machine has no composition capacity left: the %d "
		         "sessions already open ask for %.0f of the %.0f Mpixel/s "
		         "declared, and yours would ask for %.0f more (%ux%u at %.1f "
		         "fps).  ⭐ Try again shortly: capacity comes back as soon as "
		         "someone leaves",
		         c->amount, c->question, capacity_mpixel_s, d_new, canvas_w,
		         canvas_h, (double)BUDGET_MAX_FPS);
	return BUDGET_DOES_NOT_HOLD;
}
