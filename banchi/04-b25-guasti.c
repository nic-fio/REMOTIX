/*
 * 04-b25-guasti.c — THREE IMPLEMENTATIONS WRONG ON PURPOSE.
 *
 * ⛔ They exist for one reason only: to CERTIFY the bench (`CODER.md` §3.3 and
 *    §4.6).  A bench that has never seen the defect is not a test — it is a
 *    green that gives false confidence.  `04-b25-lancia.sh` compiles `04-b25-tastiera.c`
 *    against each of these and DEMANDS that it says RED.
 *
 * ⚠ None of these three is invented: they are the three ways this module
 *   really goes wrong, and each has a name in the real product.
 *
 *   FAULT=1  «sends the letter without the accent».  It does not find the accented «e'» and
 *             falls back on the «e».  ⇒ It is precisely what `RCP.md` §7.3
 *             forbids: «MUST NOT send a different character».  For the user
 *             it is the wrong letters in the password field.
 *
 *   FAULT=2  «forgets the modifiers».  It finds the right key and hands over
 *             only that: on `it` out comes «e` » instead of «e'», on `us` out comes «2»
 *             instead of «@».  It is the defect that a bench comparing the
 *             CODES would never see — the key is the right one.
 *
 *   FAULT=3  «falls back to us silently».  The requested layout does not
 *             load and `us` is loaded without saying so, still declaring the
 *             requested name.  It is the trap of `CODER.md` §4.2 in its worst
 *             form: the symptom is «it types the wrong letters» and nobody
 *             connects it to the layout.
 */
#include "../src/tastiera.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <xkbcommon/xkbcommon.h>

#ifndef FAULT
#define FAULT 1
#endif

#define XKB_A_EVDEV(k) ((uint16_t)((k) - 8))

struct keyboard
{
	struct xkb_context *ctx;
	struct xkb_keymap *km;
	char label_name[128];
};

static void quiet(struct xkb_context *c, enum xkb_log_level l, const char *f, va_list a)
{
	(void)c;
	(void)l;
	(void)f;
	(void)a;
}

static struct xkb_keymap *compile(struct xkb_context *ctx, const char *arrangement)
{
	char layout[64] = {0}, variant[64] = {0};
	const char *par = strchr(arrangement, '(');
	struct xkb_rule_names names;

	if (par)
	{
		size_t n = (size_t)(par - arrangement);
		if (n >= sizeof layout)
			return NULL;
		memcpy(layout, arrangement, n);
		snprintf(variant, sizeof variant, "%s", par + 1);
		char *ch = strchr(variant, ')');
		if (ch)
			*ch = 0;
	}
	else
		snprintf(layout, sizeof layout, "%s", arrangement);

	names.rules = "evdev";
	names.model = "pc105";
	names.layout = layout;
	names.variant = variant;
	names.options = "";
	return xkb_keymap_new_from_names(ctx, &names, XKB_KEYMAP_COMPILE_NO_FLAGS);
}

Keyboard *keyboard_open(const char *arrangement, char **failure)
{
	Keyboard *t = calloc(1, sizeof *t);
	const char *asked_size = arrangement ? arrangement : "us";

	if (failure)
		*failure = NULL;
	if (!t)
		return NULL;
	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		free(t);
		return NULL;
	}
	xkb_context_set_log_fn(t->ctx, quiet);
	t->km = compile(t->ctx, asked_size);

#if FAULT == 3
	/* ⛔ THE SILENT FALLBACK: it does not load, `us` is loaded, and nobody is told. */
	if (!t->km)
		t->km = compile(t->ctx, "us");
#endif

	if (!t->km)
	{
		if (failure)
			*failure = strdup("the layout does not compile");
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}
	snprintf(t->label_name, sizeof t->label_name, "%s", asked_size);
	return t;
}

/*
 * GUASTO=4  ⛔ «trusts the negotiated name instead of the layout the
 *           session handed over».  It is THE DEFECT FOR WHICH THE CONTRACT
 *           CHANGED on 14 Aug 2026: the keymap arrives from `libei` and is
 *           thrown away, and the one the client asked for is compiled.
 *
 *           Session `it`, client `us`, the user types `[`: this sends
 *           key 26 — right on `us` — and on the screen appears **«è»**.  The
 *           bench must catch it, or the cure is not proven.
 *
 * ⚠ For the other three faults this function is CORRECT: each must
 *   get one thing wrong only, or nobody knows what the bench has seen.
 */
Keyboard *keyboard_open_from_keymap(const char *body_text, size_t length, const char *negotiated,
                                  char **failure)
{
	Keyboard *t;

	if (failure)
		*failure = NULL;

#if FAULT == 4
	/* ⛔ the session's keymap is not even looked at. */
	(void) body_text;
	(void) length;
	return keyboard_open(negotiated ? negotiated : "us", failure);
#else
	(void) negotiated;
	while (length > 0 && body_text && body_text[length - 1] == '\0')
		length--;
	if (!body_text || length == 0)
		return NULL;
	t = calloc(1, sizeof *t);
	if (!t)
		return NULL;
	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		free(t);
		return NULL;
	}
	xkb_context_set_log_fn(t->ctx, quiet);
	t->km = xkb_keymap_new_from_buffer(t->ctx, body_text, length, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                   XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->km)
	{
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}
	snprintf(t->label_name, sizeof t->label_name, "%s", negotiated ? negotiated : "the session's");
	return t;
#endif
}

const char *keyboard_layout(Keyboard *t) { return t ? t->label_name : NULL; }

void keyboard_close(Keyboard *t)
{
	if (!t)
		return;
	xkb_keymap_unref(t->km);
	xkb_context_unref(t->ctx);
	free(t);
}

/* Looks for a key that produces `character`; returns the level in `*level`. */
static int search(struct xkb_keymap *km, uint32_t character, xkb_keycode_t *key,
                 xkb_level_index_t *level)
{
	xkb_keycode_t min = xkb_keymap_min_keycode(km), max = xkb_keymap_max_keycode(km);

	for (xkb_keycode_t k = min; k <= max; k++)
	{
		xkb_level_index_t n = xkb_keymap_num_levels_for_key(km, k, 0);
		for (xkb_level_index_t l = 0; l < n; l++)
		{
			const xkb_keysym_t *sim = NULL;
			int how_many = xkb_keymap_key_get_syms_by_level(km, k, 0, l, &sim);
			for (int i = 0; i < how_many; i++)
				if (xkb_keysym_to_utf32(sim[i]) == character)
				{
					*key = k;
					*level = l;
					return 1;
				}
		}
	}
	return 0;
}

int keyboard_positions_for(Keyboard *t, uint32_t character, uint16_t codes[KEYBOARD_MAX_POSITIONS],
                           size_t *n)
{
	xkb_keycode_t key;
	xkb_level_index_t level;

	if (!t || !codes || !n)
		return -1;
	*n = 0;
	if (character > 0x10FFFF || (character >= 0xD800 && character <= 0xDFFF))
		return -1;

	if (!search(t->km, character, &key, &level))
	{
#if FAULT == 1
		/* ⛔ «better something than nothing»: the accent is dropped and that
		 *    letter is sent.  It is the falsification RCP.md §7.3 forbids. */
		static const struct
		{
			uint32_t accented, bare;
		} folds[] = {{0x00E0, 'a'}, {0x00E8, 'e'}, {0x00E9, 'e'}, {0x00EC, 'i'},
		              {0x00F2, 'o'}, {0x00F9, 'u'}, {0x00E7, 'c'}};
		for (size_t i = 0; i < sizeof folds / sizeof *folds; i++)
			if (folds[i].accented == character &&
			    search(t->km, folds[i].bare, &key, &level))
				goto located;
#endif
		return 0;
	}
#if FAULT == 1
located:
#endif
	{
		size_t q = 0;
#if FAULT != 2
		/* The naive little rule of v1: level 1 = Shift, 2 = AltGr, 3 = both. */
		if (level == 1 || level == 3)
			codes[q++] = 42;
		if (level == 2 || level == 3)
			codes[q++] = 100;
#endif
		/* ⛔ FAULT=2: the modifiers are not added at all. */
		codes[q++] = XKB_A_EVDEV(key);
		*n = q;
	}
	return 1;
}
