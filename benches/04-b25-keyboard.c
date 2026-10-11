/*
 * 04-b25-keyboard.c — THE KEYBOARD BENCH (phase 4, link A5).
 *
 * ⛔ Written BEFORE the code it tests, and CERTIFIED before being believed
 *    (`CODER.md` §3.3 and §3.4): `04-b25-launch.sh` also points it at
 *    FOUR implementations wrong on purpose (`04-b25-faults.c`) and
 *    DEMANDS that it says RED on each, and ON THE RIGHT TEST.  A bench that has never seen the defect is not
 *    a test.
 *
 * ---------------------------------------------------------------------------
 * ⭐ WHAT IT TESTS, and why neither QUIC nor `libei` is needed (`CODER.md` §3.6)
 *
 * The module `src/keyboard.c` answers ONE question: «to make this
 * character come out with this layout, which keys do I press?».  It is a pure
 * function: it is isolated and called from outside, on known inputs.  A round of
 * session, compositor and protocol would cost ten minutes per round and
 * would confuse «the keyboard is wrong» with «the session did not start».
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ HOW IT IS VERIFIED — FROM THE RECEIVING SIDE (`CODER.md` §3.8)
 *
 * ⚠ The temptation was to compare the codes that came out with numbers written by
 *   hand in here («the Italian accented e' is key 26 with Shift»).
 *   It would have been a bench that tests my arithmetic against itself: if
 *   I got the table wrong, both would be wrong the same way.
 *
 * ⇒ The bench SIMULATES THE COMPOSITOR.  It takes the evdev codes the module
 *   hands it, types them on an `xkb_state` state machine built on its
 *   own — the same machine that runs inside Mutter and KWin — and reads WHICH
 *   CHARACTER COMES OUT.  The yardstick is the character that appears, not the code that
 *   was sent.  It is the closest form to `I8` one can have without a
 *   screen in front.
 *
 * ⛔ AND THE SIMULATION HAS ITS POSITIVE CONTROL AND ITS NEGATIVE ONE
 *   (`CODER.md` §3.10), because otherwise «nothing came out» and «I could not
 *   look» would look the same:
 *     · positive — can the simulator see a letter that surely comes out?
 *       The «a» key is typed and an «a» must come out;
 *     · negative — can the simulator DISTINGUISH?  The key of the Italian
 *       «e'» is typed WITHOUT Shift and an «e` » must come out, i.e. a DIFFERENT
 *       character.  A simulator that said «accented e'» anyway would make
 *       even the implementation that forgets the modifiers green.
 *
 * ---------------------------------------------------------------------------
 * THE TESTS, and each is a thesis of `PLAN.md` lines 630-632 to refute
 *
 *   1. «e'» with layout `it`                 ⇒ the «e'» must COME OUT
 *   2. «e'» with layout `us`                 ⇒ ⛔ NOT producible, and ⛔ an «e» must
 *      NOT come out in its place
 *   3. «@» on `it` (wants AltGr) and on `us` (wants Shift): two different routes
 *      for the same character — and WHICH ROUTE was taken is checked
 *   4. an emoji: not producible in either — the tool can say no
 *   5. ⛔⛔ **the layout is handed over by the SESSION**, not chosen by the
 *      negotiated name: session `it` + client `us` + the `[` ⇒ «è» must not come out.
 *      It is the case for which the contract changed on 14 Aug 2026;
 *   6. ⛔ a layout that does not exist: `keyboard_open` MUST fail and
 *      say so.  If it fell back to `us` silently, the symptom for the user
 *      would be «it types the wrong letters» and nobody would connect the two
 *      things (`CODER.md` §4.2).
 *
 * ---------------------------------------------------------------------------
 * HOW TO READ THE OUTCOME
 *
 *   exit 0 = GREEN, 1 = RED, 2 = the bench itself could not measure
 *   (which is NOT green: it is «I could not look»).
 *   The lines also go to JSONL, to recheck without rerunning.
 */
#include "../src/keyboard.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <xkbcommon/xkbcommon.h>
#include <xkbcommon/xkbcommon-names.h>

/* XKB numbers keys starting from 8, evdev from 0. */
#define XKB_DA_EVDEV(e) ((xkb_keycode_t)(e) + 8)

static FILE *jsonl;
static int how_many_tests, how_many_red;

/* ------------------------------------------------------------------ *
 * The bench's log
 * ------------------------------------------------------------------ */
static void jstr(const char *s)
{
	fputc('"', jsonl);
	for (; *s; s++)
	{
		if (*s == '"' || *s == '\\')
			fprintf(jsonl, "\\%c", *s);
		else if ((unsigned char)*s < 0x20)
			fprintf(jsonl, "\\u%04x", (unsigned char)*s);
		else
			fputc(*s, jsonl);
	}
	fputc('"', jsonl);
}

/* A Unicode character in a form readable both on screen and in JSON. */
static const char *utf8(uint32_t c, char buf[8])
{
	size_t i = 0;
	if (c < 0x80)
		buf[i++] = (char)c;
	else if (c < 0x800)
	{
		buf[i++] = (char)(0xC0 | (c >> 6));
		buf[i++] = (char)(0x80 | (c & 0x3F));
	}
	else if (c < 0x10000)
	{
		buf[i++] = (char)(0xE0 | (c >> 12));
		buf[i++] = (char)(0x80 | ((c >> 6) & 0x3F));
		buf[i++] = (char)(0x80 | (c & 0x3F));
	}
	else
	{
		buf[i++] = (char)(0xF0 | (c >> 18));
		buf[i++] = (char)(0x80 | ((c >> 12) & 0x3F));
		buf[i++] = (char)(0x80 | ((c >> 6) & 0x3F));
		buf[i++] = (char)(0x80 | (c & 0x3F));
	}
	buf[i] = 0;
	return buf;
}

static void outcome(const char *prova, int green, const char *detail)
{
	how_many_tests++;
	if (!green)
		how_many_red++;
	printf("  %s  %-46s  %s\n", green ? "✅" : "⛔ ROSSO", prova, detail);
	fprintf(jsonl, "{\"prova\":");
	jstr(prova);
	fprintf(jsonl, ",\"outcome\":\"%s\",\"detail\":", green ? "green" : "red");
	jstr(detail);
	fprintf(jsonl, "}\n");
	fflush(jsonl);
}

/* ------------------------------------------------------------------ *
 * THE COMPOSITOR SIMULATOR
 *
 * ⛔ It builds the layout BY ITSELF, from the same string of `RCP.md` §4.5,
 *    without asking anything of the module under test.  It is the independence that makes
 *    the check a check.
 * ------------------------------------------------------------------ */
typedef struct
{
	struct xkb_context *ctx;
	struct xkb_keymap *km;
	char name[128];
} Simulator;

static void sim_quiet(struct xkb_context *c, enum xkb_log_level l, const char *f, va_list a)
{
	(void)c;
	(void)l;
	(void)f;
	(void)a;
}

static int sim_open(Simulator *s, const char *kb_layout)
{
	char layout[64] = {0}, variant[64] = {0};
	const char *par;
	struct xkb_rule_names names;

	memset(s, 0, sizeof *s);
	par = strchr(kb_layout, '(');
	if (par)
	{
		size_t n = (size_t)(par - kb_layout);
		if (n >= sizeof layout)
			return 0;
		memcpy(layout, kb_layout, n);
		snprintf(variant, sizeof variant, "%s", par + 1);
		char *is_closed = strchr(variant, ')');
		if (is_closed)
			*is_closed = 0;
	}
	else
		snprintf(layout, sizeof layout, "%s", kb_layout);

	s->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!s->ctx)
		return 0;
	xkb_context_set_log_fn(s->ctx, sim_quiet);

	names.rules = "evdev";
	names.model = "pc105";
	names.layout = layout;
	names.variant = variant;
	names.options = "";
	s->km = xkb_keymap_new_from_names(s->ctx, &names, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!s->km)
	{
		xkb_context_unref(s->ctx);
		s->ctx = NULL;
		return 0;
	}
	snprintf(s->name, sizeof s->name, "%s", xkb_keymap_layout_get_name(s->km, 0));
	return 1;
}

static void sim_close(Simulator *s)
{
	if (s->km)
		xkb_keymap_unref(s->km);
	if (s->ctx)
		xkb_context_unref(s->ctx);
	memset(s, 0, sizeof *s);
}

/*
 * Types the sequence as `input.c` would type it: the modifiers first, the
 * key last — and reads the character the compositor would draw from it.
 * Returns 0 if nothing comes out.
 *
 * ⚠ Then it releases everything in reverse and CHECKS that the state comes back clean:
 *   a sequence that leaves a modifier down is trap 11 of
 *   `LESSONS.md` §4, and here seeing it costs two lines.
 */
static uint32_t sim_beat(Simulator *s, const uint16_t *codes, size_t n, int *dirty_state)
{
	struct xkb_state *st = xkb_state_new(s->km);
	uint32_t report;
	size_t i;

	*dirty_state = 0;
	if (!st || n == 0)
	{
		if (st)
			xkb_state_unref(st);
		return 0;
	}
	for (i = 0; i + 1 < n; i++)
		xkb_state_update_key(st, XKB_DA_EVDEV(codes[i]), XKB_KEY_DOWN);

	report = xkb_state_key_get_utf32(st, XKB_DA_EVDEV(codes[n - 1]));

	/* the real key: down and up */
	xkb_state_update_key(st, XKB_DA_EVDEV(codes[n - 1]), XKB_KEY_DOWN);
	xkb_state_update_key(st, XKB_DA_EVDEV(codes[n - 1]), XKB_KEY_UP);
	for (i = n - 1; i-- > 0;)
		xkb_state_update_key(st, XKB_DA_EVDEV(codes[i]), XKB_KEY_UP);

	if (xkb_state_serialize_mods(st, XKB_STATE_MODS_EFFECTIVE) != 0)
		*dirty_state = 1;

	xkb_state_unref(st);
	return report;
}

/* The readable name of an evdev code, for the report. */
static const char *modifier_name(uint16_t evdev)
{
	switch (evdev)
	{
		case 42: return "Shift(L)";
		case 54: return "Shift(R)";
		case 100: return "AltGr";
		case 29: return "Ctrl(L)";
		case 56: return "Alt(L)";
		case 125: return "Super";
		case 58: return "CapsLock";
		case 69: return "NumLock";
		default: return NULL;
	}
}

static void describe(char *report, size_t n, const uint16_t *codes, size_t amount)
{
	size_t i;
	int written = 0;
	report[0] = 0;
	for (i = 0; i < amount; i++)
	{
		const char *name = modifier_name(codes[i]);
		written += snprintf(report + written, (int)n - written > 0 ? n - (size_t)written : 0,
		                    "%s%u%s%s%s", i ? "+" : "", codes[i], name ? "(" : "",
		                    name ? name : "", name ? ")" : "");
		if (written < 0 || (size_t)written >= n)
			break;
	}
}

/* ------------------------------------------------------------------ *
 * ONE TEST
 * ------------------------------------------------------------------ */
typedef enum
{
	AWAITED_PRODUCIBLE,
	AWAITED_NO
} Awaited;

static void test_character(const char *kb_layout, uint32_t character, Awaited expected,
                            const char *why)
{
	Keyboard *t = NULL;
	Simulator sim;
	char *error = NULL;
	uint16_t codes[KEYBOARD_MAX_POSITIONS];
	size_t n = 0;
	int ret;
	char name[160], details[320], symbol[8], exited8[8];
	uint32_t has_exited;
	int dirty = 0;

	utf8(character, symbol);
	snprintf(name, sizeof name, "«%s» (U+%04X) on «%s» %s", symbol, character, kb_layout,
	         expected == AWAITED_PRODUCIBLE ? "⇒ must come out" : "⇒ NOT producible");

	if (!sim_open(&sim, kb_layout))
	{
		outcome(name, 0, "the SIMULATOR did not compile the layout — I could not look");
		return;
	}

	t = keyboard_open(kb_layout, &error);
	if (!t)
	{
		snprintf(details, sizeof details, "keyboard_open(\"%s\") said NULL: %s", kb_layout,
		         error ? error : "(no reason)");
		outcome(name, 0, details);
		free(error);
		sim_close(&sim);
		return;
	}

	memset(codes, 0, sizeof codes);
	ret = keyboard_positions_for(t, character, codes, &n);

	if (ret < 0)
	{
		snprintf(details, sizeof details, "returned -1 (error) instead of %d",
		         expected == AWAITED_PRODUCIBLE ? 1 : 0);
		outcome(name, 0, details);
		goto fine;
	}

	if (expected == AWAITED_NO)
	{
		if (ret == 0 && n == 0)
		{
			snprintf(details, sizeof details,
			         "said NO and sent nothing — it is the case to write in the log");
			outcome(name, 1, details);
			goto fine;
		}
		/* ⛔ The heart of the test: what would have COME OUT if we had typed? */
		has_exited = sim_beat(&sim, codes, n, &dirty);
		utf8(has_exited, exited8);
		{
			char route[128];
			describe(route, sizeof route, codes, n);
			snprintf(details, sizeof details,
			         "⛔ said YES (%s) and «%s» (U+%04X) would have come out instead of «%s»: "
			         "a DIFFERENT LETTER, which RCP.md §7.3 forbids",
			         route, exited8, has_exited, symbol);
		}
		outcome(name, 0, details);
		goto fine;
	}

	/* expected producible */
	if (ret == 0)
	{
		outcome(name, 0, "⛔ said «not producible» for a character that layout has");
		goto fine;
	}
	if (n == 0 || n > KEYBOARD_MAX_POSITIONS)
	{
		snprintf(details, sizeof details, "said YES but with n=%zu positions (the maximum is %d)", n,
		         KEYBOARD_MAX_POSITIONS);
		outcome(name, 0, details);
		goto fine;
	}

	has_exited = sim_beat(&sim, codes, n, &dirty);
	utf8(has_exited, exited8);
	{
		char route[128];
		describe(route, sizeof route, codes, n);
		if (has_exited == character && !dirty)
			snprintf(details, sizeof details, "typing %s gives «%s» — the route is %s%s", route,
			         exited8, n > 1 ? "with modifier" : "direct",
			         why ? why : "");
		else if (dirty)
			snprintf(details, sizeof details,
			         "⛔ «%s» comes out but the sequence %s LEAVES A MODIFIER PRESSED", exited8,
			         route);
		else
			snprintf(details, sizeof details, "⛔ typing %s gives «%s» (U+%04X), not «%s» (U+%04X)",
			         route, exited8, has_exited, symbol, character);
		outcome(name, has_exited == character && !dirty, details);
	}

fine:
	free(error);
	keyboard_close(t);
	sim_close(&sim);
}

/* ------------------------------------------------------------------ *
 * THE TOOL'S CONTROLS — they are done FIRST, and if they fail the exit is 2
 * ------------------------------------------------------------------ */
static int instrument_checks(void)
{
	Simulator sim;
	uint16_t solo_a[1] = {30};      /* KEY_A */
	uint16_t solo_ac11[1] = {26};   /* KEY_LEFTBRACE: on `it` it is the «e` » */
	uint16_t with_shift[2] = {42, 26};
	uint32_t c;
	int dirty;
	char b[8];
	int ok = 1;

	printf("\n  — THE TOOL'S CONTROLS (without these, «nothing came out» and «I could not\n"
	       "    look» look the same — CODER.md §3.10)\n");

	if (!sim_open(&sim, "it"))
	{
		outcome("positive control: the simulator compiles «it»", 0,
		      "no — the bench cannot measure anything");
		return 0;
	}

	c = sim_beat(&sim, solo_a, 1, &dirty);
	outcome("⭐ positive: the simulator sees a letter that surely COMES OUT",
	      c == 'a' && !dirty,
	      c == 'a' ? "typed key 30 on «it», «a» came out" : "typed key 30, an «a» did NOT come out");
	ok = ok && (c == 'a');

	c = sim_beat(&sim, solo_ac11, 1, &dirty);
	utf8(c, b);
	{
		char d[128];
		snprintf(d, sizeof d, "key 26 without Shift ⇒ «%s» (U+%04X), and it is NOT the accented «e'»", b, c);
		outcome("⭐ negative: the simulator DISTINGUISHES the levels", c == 0x00E8, d);
	}
	ok = ok && (c == 0x00E8);

	c = sim_beat(&sim, with_shift, 2, &dirty);
	utf8(c, b);
	{
		char d[160];
		snprintf(d, sizeof d, "Shift+26 ⇒ «%s» (U+%04X): the simulator APPLIES the modifiers", b, c);
		outcome("⭐ the simulator applies the modifiers", c == 0x00E9 && !dirty, d);
	}
	ok = ok && (c == 0x00E9);

	sim_close(&sim);
	return ok;
}

/* ------------------------------------------------------------------ *
 * ⛔ THE TRAP: the silent fallback to `us`
 * ------------------------------------------------------------------ */
static void test_silent_fallback(void)
{
	static const char *nonexistent_names[] = {"zz_non_esiste", "it(variante_che_non_esiste)"};
	size_t i;

	for (i = 0; i < sizeof nonexistent_names / sizeof *nonexistent_names; i++)
	{
		char *error = NULL;
		char name[160], details[320];
		Keyboard *t;

		snprintf(name, sizeof name, "⛔ «%s» does not load ⇒ MUST fail and SAY SO", nonexistent_names[i]);
		t = keyboard_open(nonexistent_names[i], &error);
		if (!t)
		{
			if (error && *error)
			{
				snprintf(details, sizeof details, "NULL, with the reason: «%s»", error);
				outcome(name, 1, details);
			}
			else
				outcome(name, 0, "NULL but WITHOUT a reason: whoever reads the log does not know why");
			free(error);
			continue;
		}

		/* It returned a keyboard.  Did it fall back?  Ask the `e'`. */
		{
			uint16_t codes[KEYBOARD_MAX_POSITIONS];
			size_t n = 0;
			int r = keyboard_positions_for(t, 'a', codes, &n);
			snprintf(details, sizeof details,
			         "⛔ SILENT FALLBACK: it returned a keyboard («%s») for a layout "
			         "that does not exist%s. The symptom for the user is «it types the wrong letters», and "
			         "nobody connects the two things (CODER.md §4.2)",
			         kbd_layout(t) ? kbd_layout(t) : "(no name)",
			         r == 1 ? " — and it even types" : "");
			outcome(name, 0, details);
		}
		free(error);
		keyboard_close(t);
	}
}

/*
 * ⚠ And the other side: two different layouts must PRODUCE TWO DIFFERENT
 *   NAMES.  If `kbd_layout()` said the same thing for `it` and
 *   for `us`, a fallback would not even show in the log.
 */
static void test_distinct_names(void)
{
	Keyboard *a = keyboard_open("it", NULL);
	Keyboard *b = keyboard_open("us", NULL);
	char details[320];

	if (!a || !b)
	{
		outcome("the names of the two layouts are distinguishable", 0,
		      "one of the two did not open: the test could not be done");
		keyboard_close(a);
		keyboard_close(b);
		return;
	}
	snprintf(details, sizeof details, "«%s» contro «%s»",
	         kbd_layout(a) ? kbd_layout(a) : "(NULL)",
	         kbd_layout(b) ? kbd_layout(b) : "(NULL)");
	outcome("⭐ the names of the two layouts are DISTINGUISHABLE",
	      kbd_layout(a) && kbd_layout(b) &&
	          strcmp(kbd_layout(a), kbd_layout(b)) != 0,
	      details);
	keyboard_close(a);
	keyboard_close(b);
}

/* The inputs the protocol forbids (`RCP.md` §7.3): out of range and
 * surrogates.  They are not «not producible»: they are an error. */
static void test_illegal_inputs(void)
{
	Keyboard *t = keyboard_open("it", NULL);
	uint16_t codes[KEYBOARD_MAX_POSITIONS];
	size_t n = 1;
	char details[160];
	int r1, r2;

	if (!t)
	{
		outcome("illegal inputs are distinguished from «not producible»", 0,
		      "«it» did not open");
		return;
	}
	r1 = keyboard_positions_for(t, 0xD800, codes, &n);
	r2 = keyboard_positions_for(t, 0x110000, codes, &n);
	snprintf(details, sizeof details, "surrogate ⇒ %d, out of range ⇒ %d (expected -1 and -1)", r1, r2);
	outcome("illegal inputs are NOT confused with «not producible»", r1 == -1 && r2 == -1,
	      details);
	keyboard_close(t);
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ THE TEST FOR WHICH THE CONTRACT CHANGED
 *
 * `keyboard_open()` compiles the layout FROM THE NAME the client
 * negotiated.  But the one with which the compositor will interpret our codes is
 * ITS OWN, the one `libei` hands over with the device.
 *
 * ⇒ Here they are set to quarrel on purpose: **the session has `it`, the client
 *   negotiated `us`, and the user types `[`.**
 *
 *     · on `us` the `[` sits on key 26, alone;
 *     · on `it` key 26 holds the «e` », and the `[` wants AltGr.
 *
 *   A module that trusts the negotiated name sends «26», and on the user's
 *   screen appears **«è»**.  ⛔ Not a missing character: A DIFFERENT
 *   CHARACTER — what `RCP.md` §7.3 forbids, and what nobody would ever connect
 *   to the layout.
 *
 * ⚠ The simulator, here, is built on THE SESSION'S layout: it is
 *   the only one that counts, because it is the only one the compositor applies.
 * ------------------------------------------------------------------ */
static char *layout_text(const char *kb_layout)
{
	Simulator s;
	char *text;

	if (!sim_open(&s, kb_layout))
		return NULL;
	text = xkb_keymap_get_as_string(s.km, XKB_KEYMAP_FORMAT_TEXT_V1);
	sim_close(&s);
	return text;
}

static void test_session_keymap(const char *session_layout, const char *negotiated,
                                        uint32_t character, Awaited expected)
{
	char *text = layout_text(session_layout);
	Simulator sim;
	Keyboard *t = NULL;
	char *error = NULL;
	uint16_t codes[KEYBOARD_MAX_POSITIONS];
	size_t n = 0;
	int ret, dirty = 0;
	char name[256], details[448], symbol[8], exited8[8], route[128];
	uint32_t has_exited;

	utf8(character, symbol);
	snprintf(name, sizeof name, "session «%s» + negotiated «%s», «%s» (U+%04X) %s",
	         session_layout, negotiated ? negotiated : "(none)", symbol, character,
	         expected == AWAITED_PRODUCIBLE ? "⇒ must come out" : "⇒ NOT producible");

	if (!text || !sim_open(&sim, session_layout))
	{
		outcome(name, 0, "I could not build the session's layout: I DID NOT MEASURE");
		free(text);
		return;
	}

	t = keyboard_open_from_keymap(text, strlen(text), negotiated, &error);
	if (!t)
	{
		snprintf(details, sizeof details, "the session's keymap did not open: %s",
		         error ? error : "(no reason)");
		outcome(name, 0, details);
		goto fine;
	}

	memset(codes, 0, sizeof codes);
	ret = keyboard_positions_for(t, character, codes, &n);

	if (expected == AWAITED_NO)
	{
		if (ret == 0 && n == 0)
			outcome(name, 1, "said NO and sent nothing");
		else
		{
			has_exited = sim_beat(&sim, codes, n, &dirty);
			utf8(has_exited, exited8);
			describe(route, sizeof route, codes, n);
			snprintf(details, sizeof details, "⛔ said YES (%s): «%s» would appear", route, exited8);
			outcome(name, 0, details);
		}
		goto fine;
	}

	if (ret != 1 || n == 0)
	{
		snprintf(details, sizeof details,
		         "⛔ said «not producible» (%d) for a character THE SESSION has: it "
		         "trusted the negotiated name instead of the real layout",
		         ret);
		outcome(name, 0, details);
		goto fine;
	}

	has_exited = sim_beat(&sim, codes, n, &dirty);
	utf8(has_exited, exited8);
	describe(route, sizeof route, codes, n);
	if (has_exited == character && !dirty)
		snprintf(details, sizeof details, "typing %s on THE SESSION'S layout gives «%s»",
		         route, exited8);
	else
		snprintf(details, sizeof details,
		         "⛔ typing %s on THE SESSION'S layout gives «%s» (U+%04X), not «%s»: "
		         "A DIFFERENT LETTER",
		         route, exited8, has_exited, symbol);
	outcome(name, has_exited == character && !dirty, details);

fine:
	free(error);
	keyboard_close(t);
	sim_close(&sim);
	free(text);
}

/*
 * ⛔ And it can be called SEVERAL TIMES: `STUDIES.md` §gnome §9 says that a keymap change
 *    destroys and recreates the keyboard device, and `input.c` reopens at every
 *    `DEVICE_ADDED`.  ⇒ Two openings alive together must neither lose nor
 *    double anything: `it` is opened, `us` is opened, and **the first one is
 *    asked again**, and it must answer as before.
 */
static void test_reopenings(void)
{
	char *ti = layout_text("it");
	char *tu = layout_text("us");
	Keyboard *a = NULL, *b = NULL;
	uint16_t ca[KEYBOARD_MAX_POSITIONS], cb[KEYBOARD_MAX_POSITIONS];
	size_t na = 0, nb = 0, na2 = 0;
	uint16_t ca2[KEYBOARD_MAX_POSITIONS];
	char details[320];
	int r1, r2, r3;

	if (!ti || !tu)
	{
		outcome("⭐ it can be reopened several times without losing anything", 0, "I DID NOT MEASURE");
		goto fine;
	}
	a = keyboard_open_from_keymap(ti, strlen(ti), NULL, NULL);
	r1 = a ? keyboard_positions_for(a, 0x00E9, ca, &na) : -1; /* é on it */

	b = keyboard_open_from_keymap(tu, strlen(tu), NULL, NULL);
	r2 = b ? keyboard_positions_for(b, 0x00E9, cb, &nb) : -1; /* é on us */

	/* ⛔ and now the FIRST one again, which is still alive */
	r3 = a ? keyboard_positions_for(a, 0x00E9, ca2, &na2) : -1;

	snprintf(details, sizeof details,
	         "it⇒%d (%zu pos.), then us⇒%d (%zu pos.), then AGAIN it⇒%d (%zu pos.)", r1, na, r2, nb,
	         r3, na2);
	outcome("⭐ two layouts alive together do not get mixed up",
	      r1 == 1 && r2 == 0 && r3 == 1 && na == na2 && na > 0 &&
	          memcmp(ca, ca2, na * sizeof *ca) == 0,
	      details);

fine:
	keyboard_close(a);
	keyboard_close(b);
	free(ti);
	free(tu);
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ AND THE LOG LINE IS CHECKED, NOT ONLY THE LETTER
 *
 * ⚠ This test was born from a defect the bench had NOT seen.  The
 *   comparison between the session's layout and the negotiated one, in its
 *   first draft, declared a fallback **even when the two were the
 *   same** — and the bench stayed green, because it looked at the letter that
 *   came out and the letter came out right.  The defect was entirely in the log
 *   line, which is the only part of this work someone will read on the
 *   day the letters do not add up.
 *
 * ⛔ A «DECLARED FALLBACK» that comes out at every connection is worse than useless:
 *    whoever reads the log learns to skip it.  ⇒ It is checked in BOTH directions —
 *    that it comes out when it must, and that it does **not** come out when it must not.
 *
 * The log goes to stderr: it is redirected to a file for the duration of the
 * call, and then read.  It is `CODER.md` §3.8 — verify from the receiving
 * side, and whoever receives this line is a log file.
 * ------------------------------------------------------------------ */
static void test_declaration(const char *session_layout, const char *negotiated,
                                int must_declare)
{
	char *text = layout_text(session_layout);
	char name[256], details[384], line[4096];
	int saved = -1, tmp = -1;
	FILE *f = NULL;
	Keyboard *t = NULL;
	long readings = 0;
	int claimed = 0;
	char model[] = "/tmp/04-b25-reg-XXXXXX";

	snprintf(name, sizeof name, "the log: session «%s» + negotiated «%s» ⇒ %s",
	         session_layout, negotiated ? negotiated : "(none)",
	         must_declare ? "MUST declare the fallback" : "must NOT cry fallback");

	if (!text)
	{
		outcome(name, 0, "I did not build the layout: I DID NOT MEASURE");
		return;
	}

	tmp = mkstemp(model);
	if (tmp < 0)
	{
		outcome(name, 0, "I could not redirect the log: I DID NOT MEASURE");
		free(text);
		return;
	}
	fflush(stderr);
	saved = dup(STDERR_FILENO);
	dup2(tmp, STDERR_FILENO);

	t = keyboard_open_from_keymap(text, strlen(text), negotiated, NULL);

	fflush(stderr);
	dup2(saved, STDERR_FILENO);
	close(saved);

	f = fdopen(tmp, "r");
	if (f)
	{
		rewind(f);
		while (fgets(line, sizeof line, f))
		{
			readings++;
			if (strstr(line, "DECLARED FALLBACK"))
				claimed = 1;
		}
		fclose(f);
	}
	unlink(model);

	/*
	 * ⛔ The TOOL's positive control: if I had read no line
	 *    at all, «it did not declare» and «I could not read the log»
	 *    would look the same (`CODER.md` §3.10).
	 */
	if (readings == 0)
	{
		outcome(name, 0, "⛔ I read NO log line at all: I cannot tell "
		               "silence from not having looked");
		goto fine;
	}

	snprintf(details, sizeof details, "%ld log lines, «DECLARED FALLBACK» %s", readings,
	         claimed ? "present" : "absent");
	outcome(name, claimed == must_declare, details);

fine:
	keyboard_close(t);
	free(text);
}

/* ------------------------------------------------------------------ *
 * main
 * ------------------------------------------------------------------ */
int main(int argc, char **argv)
{
	const char *dove = argc > 1 ? argv[1] : "benches/04-b25-outcomes.jsonl";

	jsonl = fopen(dove, "w");
	if (!jsonl)
	{
		fprintf(stderr, "⛔ I cannot write %s\n", dove);
		return 2;
	}

	printf("\n== BENCH 04-b25 — THE KEYBOARD: from the letter to the hammer\n");
	printf("   the yardstick is THE CHARACTER THAT COMES OUT of an independent `xkb_state`,\n"
	       "   not the code the module says it chose.\n");

	if (!instrument_checks())
	{
		printf("\n⛔ THE TOOL IS NOT CERTIFIED: I measure nothing.\n");
		fclose(jsonl);
		return 2;
	}

	printf("\n  — THE LETTERS (PLAN.md lines 630-632)\n");
	test_character("it", 0x00E9, AWAITED_PRODUCIBLE, "");  /* é */
	test_character("us", 0x00E9, AWAITED_NO, "");           /* ⛔ the test that weighs the most */
	test_character("it", 0x00E8, AWAITED_PRODUCIBLE, "");  /* è, without modifier */
	test_character("it", 'a', AWAITED_PRODUCIBLE, "");     /* positive control on the module */
	test_character("us", 'A', AWAITED_PRODUCIBLE, "");     /* Shift MAKES the letter */

	printf("\n  — THE SAME CHARACTER, TWO ROUTES (SPECS.md §7.3: Shift and AltGr\n"
	       "    are not commands, they serve to MAKE the letter)\n");
	test_character("it", '@', AWAITED_PRODUCIBLE, "");     /* AltGr */
	test_character("us", '@', AWAITED_PRODUCIBLE, "");     /* Shift */

	printf("\n  — WHAT CANNOT BE TYPED IS DECLARED, NOT FALSIFIED\n");
	test_character("it", 0x1F600, AWAITED_NO, "");          /* 😀 */
	test_character("us", 0x1F600, AWAITED_NO, "");
	test_character("it", 0x4E2D, AWAITED_NO, "");           /* 中 */

	printf("\n  — ⛔ THE TRAP: THE SILENT FALLBACK\n");
	test_silent_fallback();
	test_distinct_names();

	printf("\n  — THE INPUTS THE PROTOCOL FORBIDS\n");
	test_illegal_inputs();

	printf("\n  — ⛔⛔ THE LAYOUT IS HANDED OVER BY THE SESSION, NOT CHOSEN BY THE NAME\n"
	       "    (the case for which the contract changed: session «it», client «us»)\n");
	/* ⛔ THE CASE: the `[` — on `us` it is bare key 26, on `it` that key holds the «è». */
	test_session_keymap("it", "us", '[', AWAITED_PRODUCIBLE);
	/* and the twin: a character the session does NOT have, however much the client asks for it */
	test_session_keymap("us", "it", 0x00E9, AWAITED_NO);
	/* the positive controls: when they match, everything as before */
	test_session_keymap("it", "it", 0x00E9, AWAITED_PRODUCIBLE);
	test_session_keymap("it", NULL, '[', AWAITED_PRODUCIBLE);
	test_reopenings();

	printf("\n  — ⛔ AND THE LOG LINE, IN BOTH DIRECTIONS\n");
	test_declaration("it", "us", 1);  /* they do not match ⇒ it is declared */
	test_declaration("it", "it", 0);  /* ⛔ they match ⇒ NO crying out */
	test_declaration("us", "us", 0);
	test_declaration("it", NULL, 0);  /* none negotiated: nothing to compare */

	printf("\n== %d tests, %d RED  ⇒  %s\n\n", how_many_tests, how_many_red,
	       how_many_red ? "⛔ ROSSO" : "✅ VERDE");
	fprintf(jsonl, "{\"total\":%d,\"red_count\":%d,\"outcome\":\"%s\"}\n", how_many_tests, how_many_red,
	        how_many_red ? "red" : "green");
	fclose(jsonl);
	return how_many_red ? 1 : 0;
}
