/*
 * keyboard.c — FROM THE LETTER TO THE HAMMER.  Link A5 of phase 4.
 *
 * ⛔ The contract is in `keyboard.h`, which belongs to the coordinator: here it is
 *    IMPLEMENTED, the seam is not changed.
 *
 * ---------------------------------------------------------------------------
 * THE PROBLEM, in one line
 *
 * On the wire letters travel as letters (`SPECS.md` §7.3,
 * `DECISIONS.md` §5-bis.6), but `libei` — the only way to inject input into a
 * Wayland compositor — does not accept letters: it accepts KEY POSITIONS, and it is
 * the compositor that decides which letter it is, looking at the layout.  This file
 * makes the trip backwards.
 *
 * ---------------------------------------------------------------------------
 * ⭐ WHAT WAS REUSED FROM v1, AND WHAT WAS NOT
 *
 * `fondamenta/remotix-c/src/tastiera.c` already made this trip (372 lines, xkbcommon),
 * and its structure is the one here: the layout is scanned key by
 * key and level by level, looking for whoever produces the wanted symbol.  Three
 * things changed, and each for a reason MEASURED on 14 August 2026:
 *
 *  1. ⛔ **the modifiers are no longer guessed.**  v1 had the little rule
 *     "level 1 = Shift, level 2 = AltGr, level 3 = both"
 *     (`fondamenta/.../tastiera.c:251`).  It is true for ordinary layouts and false
 *     for the others.  ⭐ `[M]` 14 August 2026, measured on `de(neo)`:
 *
 *       U+00E4 «ä» ⇒ 46                 (no modifier)
 *       U+2192 «→» ⇒ 43 + 77
 *       U+03B1 «α» ⇒ 42 + 43 + 32
 *       U+221A «√» ⇒ 100 + 43 + 17      ⛔ TWO level modifiers
 *
 *     ⛔ Two things v1's little rule would have got wrong: on `de(neo)` the
 *        third-level key is **43** (`<BKSL>`), not the 100 v1
 *        had written at the top of the file; and the fifth level it does not name
 *        at all.  Here the answer is given by `xkb_keymap_key_get_mods_for_level()`,
 *        that is by the layout itself.
 *
 *     ⭐ And the same measurement answers the question the contract asks without
 *        saying it — **are four key positions enough?**  The worst case
 *        found uses **three** (two modifiers plus the key): `de(neo)` is
 *        the layout with the most levels the system carries, and one is left over;
 *
 *  2. ⛔ **which KEY is a modifier is not written by hand.**  v1 had
 *     `#define KEY_LEFTSHIFT 42` and `KEY_RIGHTALT 100` at the top of the file.  Here we
 *     ASK the layout: every key is pressed on an `xkb_state` and we
 *     look at which modifier lights up.  A hand-written table is a
 *     table that goes wrong silently when the layout is unusual;
 *
 *  3. ⛔ **the comparison is on the CHARACTER, not on the keysym.**  v1 translated the
 *     character into a keysym with `xkb_utf32_to_keysym()` and looked for THAT keysym.
 *     But the same character has two keysym forms — the legacy one
 *     (`XKB_KEY_eacute` = 0x00E9) and the Unicode one (0x010000E9) — and a
 *     layout may use either: looking for a single form one
 *     declares "not producible" a character that is right there.  Here we compare
 *     `xkb_keysym_to_utf32(symbol) == character`, which covers both.
 *
 * ⚠ And one thing from v1 was NOT carried over, because it does not belong to this file: the
 *   count of what is pressed and the release at detach.  In V2 that lives
 *   in `input.c` (`input_release_all()`, `input.h:98`), and keeping two copies
 *   would be the error form "two measures under the same label".
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ THE TRAP THIS FILE EXISTS NOT TO HAVE
 *
 * If the requested layout does not load and we fall back to `us` without saying so, the
 * symptom the user describes is **"it types the wrong letters"**, and nobody
 * connects it to the layout: one goes looking for the defect in the protocol, in the
 * browser, in the phone's keyboard.  `CODER.md` §4.2 — degrade, do not
 * fail, BUT THE FALLBACK IS DECLARED.  Here there is no fallback at all:
 *
 *   · `[M]` 14 August 2026 — `xkbcommon` 1.7.0 **does not fall back by itself**: asked
 *     for a layout that does not exist, `xkb_keymap_new_from_names()` returns
 *     NULL and writes `[XKB-338] Couldn't find file "symbols/..."`.  The fallback
 *     could only be put in by our code, and it is not there;
 *   · ⚠ but those lines **end up on stderr and that is all**, and the caller sees only
 *     a NULL with no reason.  ⇒ Here `xkbcommon`'s log is HIJACKED
 *     (`xkb_context_set_log_fn`) and the first error becomes the text of
 *     `*error`.  Whoever reads the log finds the reason, not a NULL;
 *   · ⛔ and `kbd_layout()` carries inside the name the COMPILED
 *     layout gives itself — «it [Italian]», «us [English (US)]».  If one day
 *     a fallback came in from somewhere else, it would show **in the log**
 *     as «it [English (US)]», which is a line that reads by itself.
 *
 * `benches/04-b25-keyboard.c` checks all three, and `benches/04-b25-launch.sh`
 * puts in front of it an implementation that falls back on purpose, to certify that the
 * bench would see it.
 */
#include "keyboard.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <xkbcommon/xkbcommon.h>
#include <xkbcommon/xkbcommon-names.h>

#include "log.h"

/*
 * ⚠ The log area lives here and not in `log.h`: that file is shared by
 *   ten links writing at the same moment, and a line added in
 *   there would be a guaranteed collision.  To be merged into `log.h` when the
 *   phase closes — it is a seam, and seams are kept by the coordinator.
 */
#define LOG_KEYBOARD "keyboard"

/* XKB numbers keys starting from 8, evdev from 0 (`RCP.md` §7.3). */
#define EVDEV_DA_XKB(k) ((uint16_t)((k) - 8))

/* How many modifiers a layout can have.  xkbcommon allows 32. */
#define MAX_MOD 32

struct keyboard
{
	struct xkb_context *ctx;
	struct xkb_keymap *keymap;
	xkb_layout_index_t group;

	/* «it [Italian]»: the requested and the compiled in the same line. */
	char name[192];

	/*
	 * ⛔ modifier → key that lights it up, ASKED of the layout and not
	 *    written by hand.  0 = no key lights it up on its own.
	 */
	uint16_t mod_key[MAX_MOD];
	xkb_mod_index_t n_mod;

	/* The two locks, which are NEVER used to make a letter: see below. */
	xkb_mod_index_t mod_caps, mod_num;

	/* The hijacking of xkbcommon's log, during compilation. */
	char first_error[256];
	int errors;

	/*
	 * ⭐⭐ WHOSE LINE IT IS — 27 August 2026, the red of C9.
	 *
	 * ⛔ This module writes `keyboard` area lines from TWO processes of different
	 *    kinds (`log.h`), and until now treated them the same way:
	 *
	 *      · in the CHILD it is already fine: `log_identity()` is set
	 *        at `exec` and every line of the process carries it;
	 *      · in the PARENT it is not: `keyboard_open()` is called by `webtransport.c` to
	 *        answer "does this layout exist?" during ATTACH, and
	 *        there a single process serves ALL sessions.
	 *
	 * `[M]` 26 August 2026, mesh C9, two tenants alive together: the lines
	 *      «modifier N: yes preferisce…» and «kb_layout in effect: …»
	 *      came out TWICE, identical word for word, ⛔ and there was no way
	 *      to tell which was whose.
	 *
	 * ⇒ The name is carried by the KEYBOARD, for the whole life of the opening: so
	 *   the lines coming out of `xkb_log_cb()` see it too, which has nothing else
	 *   in hand but this structure.
	 * ⚠ Empty is the truth when it is not known: `log.c` then falls back
	 *   on the PROCESS identity, which in the child is the right one.  ⇒ The
	 *   `calloc()` leaves this field as it is, and the child's path does not
	 *   change one bit.
	 */
	char chi[LOG_IDENTITY_MAX + 1];
};

/* ------------------------------------------------------------------ *
 * xkbcommon's log, hijacked
 * ------------------------------------------------------------------ */
static void xkb_log_cb(struct xkb_context *ctx, enum xkb_log_level level, const char *fmt,
                      va_list ap)
{
	Keyboard *t = xkb_context_get_user_data(ctx);
	char line[256];
	size_t n;

	if (!t)
		return;
	vsnprintf(line, sizeof line, fmt, ap);
	/* xkbcommon sends the line with a newline at the end: here it would be a nuisance. */
	n = strlen(line);
	while (n && (line[n - 1] == '\n' || line[n - 1] == '\r'))
		line[--n] = 0;

	if (level <= XKB_LOG_LEVEL_ERROR)
	{
		t->errors++;
		if (!t->first_error[0])
			snprintf(t->first_error, sizeof t->first_error, "%s", line);
		log_detail_of(LOG_KEYBOARD, t->chi, "xkbcommon: %s", line);
	}
	else
		log_detail_of(LOG_KEYBOARD, t->chi, "xkbcommon (warning): %s", line);
}

/* ------------------------------------------------------------------ *
 * The shape of the string — `RCP.md` §4.5
 *
 * ⛔ It is not pedantry, and it is the only check in this file that protects
 *    something more than a crooked letter: the string ends up inside XKB's
 *    `include` machinery, which opens files by name.  A
 *    "../../something" would arrive in there.
 *
 * ⚠ And `RCP.md` §4.5 wants the two faults DISTINCT — wrong shape is
 *   `PROTOCOL_ERROR`, a well-formed but unknown layout is
 *   `SESSION_UNSERVABLE`.  The contract of `keyboard.h` gives a single
 *   output channel (NULL + text), so the two are told apart by the PREFIX of the
 *   text: "form:" or "unknown:".  ⇒ It is one of the seams the
 *   report asks of the coordinator.
 * ------------------------------------------------------------------ */
static int allowed_char(char c)
{
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
	       c == '_' || c == '-';
}

static int valid_shape(const char *s, char *layout, size_t nl, char *variant, size_t nv)
{
	const char *par = strchr(s, '(');
	size_t len_l;

	if (!*s || strlen(s) > 64)
		return 0;

	len_l = par ? (size_t)(par - s) : strlen(s);
	if (len_l == 0 || len_l >= nl)
		return 0;
	for (size_t i = 0; i < len_l; i++)
		if (!allowed_char(s[i]))
			return 0;
	memcpy(layout, s, len_l);
	layout[len_l] = 0;

	variant[0] = 0;
	if (!par)
		return 1;

	{
		const char *is_closed = strchr(par + 1, ')');
		size_t len_v;

		if (!is_closed || is_closed[1] != 0)
			return 0;
		len_v = (size_t)(is_closed - par - 1);
		if (len_v == 0 || len_v >= nv)
			return 0;
		for (size_t i = 0; i < len_v; i++)
			if (!allowed_char(par[1 + i]))
				return 0;
		memcpy(variant, par + 1, len_v);
		variant[len_v] = 0;
	}
	return 1;
}

/* ------------------------------------------------------------------ *
 * ⛔ WHICH KEY LIGHTS UP WHICH MODIFIER — asked, not written by hand
 *
 * Every key of the layout is pressed on a state machine and we look at
 * which modifier lights up.  If exactly one lights up, that key
 * is the way to get it.  It is `CODER.md` §3.9 applied to a table: when
 * a component can answer, we do not guess.
 *
 * ⚠ The FIRST key that lights it up is kept, and keys are scanned in increasing
 *   order: the left comes before the right, which is everybody's habit.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ AND THEN THERE IS THE PREFERENCE, WHICH CAME FROM A MEASUREMENT — `[M]` 14 Aug 2026
 *
 * The scan above, on its own, chose evdev code **84** for the Italian
 * AltGr.  It is a LAWFUL choice — in XKB's `keycodes/evdev` file the
 * `<LVL3>` key is at code 92, that is evdev 84, and carries `ISO_Level3_Shift`
 * — and the bench declared it green, because typing it really produces «@».
 *
 * ⛔ But **evdev 84 is a hole**: in `linux/input-event-codes.h` between `KEY_KPDOT`
 *    (83) and `KEY_ZENKAKUHANKAKU` (85) THERE IS NOTHING — no keyboard in the
 *    world can emit that code.  It works because the compositor
 *    resolves it on ITS copy of the layout, and it is exactly the form of
 *    defect this project fears: it holds as long as the two sides have the same
 *    table, and the day they do not it stops **without an error**.
 *
 * ⇒ Hence the preference: among the keys that light up THE SAME modifier, we
 *   choose the one a real keyboard really has (`<RALT>` = evdev 100).
 *
 * ⚠ And note what it is NOT: it is not v1's hand-written table —
 *   "AltGr is key 100" — which goes wrong silently on unusual
 *   layouts.  It is a PREFERENCE among answers all obtained by asking the
 *   layout: if `ISO_Level3_Shift` were elsewhere, the scan would
 *   find it anyway and the preference would find nothing to prefer.
 * ------------------------------------------------------------------ */
static const uint16_t REAL_KEYBOARD_KEYS[] = {
	42,  /* KEY_LEFTSHIFT */
	54,  /* KEY_RIGHTSHIFT */
	29,  /* KEY_LEFTCTRL */
	97,  /* KEY_RIGHTCTRL */
	56,  /* KEY_LEFTALT */
	100, /* KEY_RIGHTALT — AltGr */
	125, /* KEY_LEFTMETA */
	126, /* KEY_RIGHTMETA */
};

/* Which modifier does this key light up, if it lights up exactly one? */
static int single_modifier(struct xkb_keymap *km, xkb_keycode_t k, int *which)
{
	struct xkb_state *st = xkb_state_new(km);
	xkb_mod_mask_t active;

	if (!st)
		return 0;
	xkb_state_update_key(st, k, XKB_KEY_DOWN);
	active = xkb_state_serialize_mods(st, XKB_STATE_MODS_EFFECTIVE);
	xkb_state_unref(st);

	if (!active || (active & (active - 1)) != 0)
		return 0;
	*which = __builtin_ctz(active);
	return 1;
}

static void learn_modifiers(Keyboard *t)
{
	xkb_keycode_t min = xkb_keymap_min_keycode(t->keymap);
	xkb_keycode_t max = xkb_keymap_max_keycode(t->keymap);
	uint8_t already_preferred[MAX_MOD] = {0};
	size_t i;

	t->n_mod = xkb_keymap_num_mods(t->keymap);
	if (t->n_mod > MAX_MOD)
		t->n_mod = MAX_MOD;

	/* 1. we ask the layout, key by key. */
	for (xkb_keycode_t k = min; k <= max; k++)
	{
		int which;
		if (k < 8 || !single_modifier(t->keymap, k, &which))
			continue;
		if (which < (int)t->n_mod && !t->mod_key[which])
			t->mod_key[which] = EVDEV_DA_XKB(k);
	}

	/*
	 * 2. and then the preference, on top of the answers already obtained.
	 *
	 * ⚠ `already_preferred` is not a theoretical precaution: without it, the list was
	 *   walked to the end and for Shift **the right one** won (evdev 54),
	 *   because it was the last of the two to pass through here.  It worked — the bench
	 *   said green — but a log saying "right Shift" where every hand
	 *   uses the left is a line that makes whoever reads it lose half an hour.
	 *   ⇒ The FIRST of the list wins, which is the order in which one types by hand.
	 */
	for (i = 0; i < sizeof REAL_KEYBOARD_KEYS / sizeof *REAL_KEYBOARD_KEYS; i++)
	{
		uint16_t evdev = REAL_KEYBOARD_KEYS[i];
		xkb_keycode_t k = (xkb_keycode_t)evdev + 8;
		int which;

		if (k < min || k > max)
			continue;
		if (!single_modifier(t->keymap, k, &which))
			continue;
		if (which >= (int)t->n_mod)
			continue;
		if (already_preferred[which] || t->mod_key[which] == evdev)
		{
			already_preferred[which] = 1;
			continue;
		}
		log_detail_of(LOG_KEYBOARD, t->chi,
		                      "modifier %d: key %u is preferred to %u (a real "
		                      "keyboard has the first)",
		                      which, evdev, t->mod_key[which]);
		t->mod_key[which] = evdev;
		already_preferred[which] = 1;
	}
}

/* ------------------------------------------------------------------ *
 * The opening
 * ------------------------------------------------------------------ */
Keyboard *keyboard_open(const char *kb_layout, char **error)
{
	/* ⚠ `NULL` is the truth for whoever does not needs a single session: the lines
	 *   will come out with the PROCESS identity, if there is one (the child), and bare if
	 *   there is not.  ⛔ Whoever does not know keeps quiet (`log.h`). */
	return keyboard_open_for(kb_layout, NULL, error);
}

Keyboard *keyboard_open_for(const char *kb_layout, const char *chi, char **error)
{
	Keyboard *t;
	char layout[72], variant[72];
	struct xkb_rule_names names;
	const char *asked_size = kb_layout ? kb_layout : "(the session's own)";

	if (error)
		*error = NULL;

	t = calloc(1, sizeof *t);
	if (!t)
		return NULL;
	t->mod_caps = XKB_MOD_INVALID;
	t->mod_num = XKB_MOD_INVALID;
	/* ⭐ The name is set BEFORE any line: the first that can come out is
	 *   the malformed-shape one, three lines below. */
	if (chi && *chi)
		snprintf(t->chi, sizeof t->chi, "%s", chi);

	if (kb_layout &&
	    !valid_shape(kb_layout, layout, sizeof layout, variant, sizeof variant))
	{
		/* ⛔ `RCP.md` §4.5: this is PROTOCOL_ERROR, not SESSION_UNSERVABLE. */
		log_says_of(LOG_KEYBOARD, t->chi,
		                 "malformed layout, refused without even trying: %.64s",
		                 kb_layout);
		if (error)
			*error = strdup("form: not an XKB layout name (RCP.md §4.5)");
		free(t);
		return NULL;
	}

	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		log_says_of(LOG_KEYBOARD, t->chi, "xkbcommon context not created");
		if (error)
			*error = strdup("xkbcommon: context not created");
		free(t);
		return NULL;
	}
	xkb_context_set_user_data(t->ctx, t);
	xkb_context_set_log_fn(t->ctx, xkb_log_cb);
	xkb_context_set_log_level(t->ctx, XKB_LOG_LEVEL_WARNING);

	/*
	 * ⚠ All five fields are declared, and NULL will not do: for every
	 *   NULL field `xkbcommon` substitutes the environment variable
	 *   `XKB_DEFAULT_*` and then a build-time value.  An
	 *   `XKB_DEFAULT_VARIANT` inherited from the environment of whoever started the
	 *   service would change the session's layout without anyone
	 *   having asked — and it is `CODER.md` §4.5, the environment is composed and
	 *   not inherited.
	 *
	 * ⛔ The intended exception: `kb_layout == NULL` means "the one in force
	 *    in the session", and there the environment IS the answer.  Then we let
	 *    `xkbcommon` decide — and we WRITE it to the log, because it is a
	 *    case in which we do not know what we loaded until we have it
	 *    told to us.
	 */
	if (kb_layout)
	{
		names.rules = "evdev";
		names.model = "pc105";
		names.layout = layout;
		names.variant = variant;
		names.options = "";
	}
	else
	{
		names.rules = NULL;
		names.model = NULL;
		names.layout = NULL;
		names.variant = NULL;
		names.options = NULL;
	}

	t->keymap = xkb_keymap_new_from_names(t->ctx, &names, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->keymap)
	{
		/*
		 * ⛔ HERE STOOD THE FALLBACK, AND IT IS NOT THERE.  The temptation is one line: "if
		 *    it does not compile, retry with us".  The service would go on —
		 *    `CODER.md` §4.2 asks for it — but typing the wrong letters
		 *    forever, without anyone knowing why.  ⇒ The soft degradation
		 *    of `DECISIONS.md` §5-bis.7 is something else: the session
		 *    keeps the layout it already has, and that is decided by THE CALLER,
		 *    who knows whether a session exists or not.  Here we fail and say so.
		 */
		const char *why =
			t->first_error[0] ? t->first_error : "xkbcommon did not say why";

		log_says_of(LOG_KEYBOARD, t->chi,
		                 "layout «%s» NOT loaded, and no fallback to any other: %s",
		                 asked_size, why);
		if (error)
		{
			/*
			 * ⛔ The size is WIDE ON PURPOSE.  This text IS the way the
			 *    fallback is declared, and a truncated message is a fallback
			 *    half declared: the layout name (up to 64 bytes,
			 *    `RCP.md` §4.5) plus `xkbcommon`'s line (up to 255) do not
			 *    fit in 320.  ⚠ Finding of the coordinator's builder, 14
			 *    August 2026: gcc said so, and said it well.
			 */
			char msg[448];
			snprintf(msg, sizeof msg, "unknown: layout «%s» does not compile (%s)",
			         asked_size, why);
			*error = strdup(msg);
		}
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}

	t->group = 0;
	snprintf(t->name, sizeof t->name, "%s [%s]", kb_layout ? kb_layout : "default",
	         xkb_keymap_layout_get_name(t->keymap, t->group)
	             ? xkb_keymap_layout_get_name(t->keymap, t->group)
	             : "unnamed");

	learn_modifiers(t);
	t->mod_caps = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_CAPS);
	t->mod_num = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_NUM);

	/*
	 * ⚠ If `xkb_keymap_num_layouts()` gave more than one, the string would have
	 *   named more layouts: `RCP.md` §4.5 does not allow it, but if one
	 *   day it did (`DECISIONS.md` §5-bis.7 keeps it open) here only
	 *   the first would be used, silently.  ⇒ It is declared at once.
	 */
	if (xkb_keymap_num_layouts(t->keymap) > 1)
		log_says_of(LOG_KEYBOARD, t->chi,
		                 "layout «%s»: the session carries %u, ONLY the first is used",
		                 asked_size, xkb_keymap_num_layouts(t->keymap));

	log_says_of(LOG_KEYBOARD, t->chi, "layout in force: %s", t->name);
	return t;
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ THE LAYOUT AS THE SESSION HANDS IT OVER
 *
 * ⭐ This function was born from a refusal of the mandate, accepted on 14 August
 *    2026.  The contract said `keyboard_open("it")` — compile a
 *    layout from the name the client negotiated — and rested on an
 *    assumption nobody had measured: **that the layout we
 *    compile is the same with which the compositor will interpret the codes
 *    we send it.**
 *
 * ⛔ It is not, and we do not decide it: the session's layout is
 *    chosen by GNOME, and `libei` HANDS it to us with the keyboard device.  The
 *    damage, concretely — `it` session, client that negotiated `us`, the user
 *    types `[`:
 *
 *      · on `us` the `[` is on key 26, alone;
 *      · on `it` key 26 holds «e` », and `[` wants AltGr.
 *
 *    ⇒ We send «26» and **«è»** appears on screen.  Not a missing
 *      character: A DIFFERENT CHARACTER, which `RCP.md` §7.3 forbids.
 *
 * ⚠ And it makes false the sentence of `DECISIONS.md` §5-bis.7 — "an old
 *   layout never produces wrong characters, at most it makes a couple of
 *   accents unreachable".  That sentence is true **only** if one
 *   uses the session's keymap.  With ours, wrong characters come out.
 * ------------------------------------------------------------------ */

/*
 * ⛔ THE COMPARISON IS ON WHAT THE TWO LAYOUTS **DO**, NOT ON WHAT THEY ARE
 *    CALLED — and it is a choice, not a detail.
 *
 * The short way was to compare the group names: «Italian» against «English
 * (US)».  ⭐ `[M]` 14 August 2026 the name **survives** serialisation and
 * the way back (`it` → serialised → recompiled → still «Italian»), so it
 * would have worked.  ⚠ But A4 measured that the keymap Mutter hands over
 * carries `xkb_symbols "(unnamed)"`: the SECTION name is not there.  The
 * GROUP name is another thing and it is there — but they are two different fields in a file we do not
 * write, and hanging on a label the line that declares the fallback
 * means that the day the label is missing **the fallback is cried at every
 * connection**.  A false alarm on this line is worth as much as a silence.
 *
 * ⇒ Two layouts are the same if **they produce the same characters on the
 *   same keys**.  It is independent of names, and measures the thing that matters.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ AND ONLY THE KEYS THAT MAKE A CHARACTER ARE COMPARED — measured, not chosen
 *
 * The first draft compared **everything**, and ⛔ **cried fallback even when
 * the two layouts were the same**.  `[M]` 14 August 2026: an `it` keymap
 * serialised and recompiled — that is the exact trip ours makes, from Mutter
 * to us — comes back with **two keysyms fewer**, on two keys only:
 *
 *     evdev key 610  XF86KbdInputAssistPrevgroup  ⇒ gone
 *     evdev key 611  XF86KbdInputAssistNextgroup  ⇒ gone
 *
 * They are two keys that **make no character** and that no keyboard on the
 * market has.  ⇒ With the total comparison, the line «FALLBACK DICHIARATO»
 * would have come out **at every connection**, including the one where everything is fine.
 * A false alarm on this line is worth as much as a silence: whoever reads the log
 * learns to skip it, and its usefulness is over.
 *
 * ⚠ And it was not found by the bench — the bench was green, because it looked at the
 *   letter coming out and the letter came out right.  I found it **reading the
 *   log**.  ⇒ Now the bench also looks at the line (`04-b25-keyboard.c`,
 *   `test_declaration`), which is the only part of this work the user
 *   will see when something does not add up.
 *
 * ⇒ The keys that produce a character are compared.  Two layouts that
 *   differ only on the multimedia keys are the same layout **for
 *   what this file does**, and saying so would be noise.
 */
static int do_the_same(struct xkb_keymap *a, xkb_layout_index_t ga,
                                struct xkb_keymap *b, xkb_layout_index_t gb)
{
	xkb_keycode_t min = xkb_keymap_min_keycode(a);
	xkb_keycode_t max = xkb_keymap_max_keycode(a);

	if (xkb_keymap_min_keycode(b) > min)
		min = xkb_keymap_min_keycode(b);
	if (xkb_keymap_max_keycode(b) < max)
		max = xkb_keymap_max_keycode(b);

	for (xkb_keycode_t k = min; k <= max; k++)
	{
		xkb_level_index_t na = xkb_keymap_num_levels_for_key(a, k, ga);
		xkb_level_index_t nb = xkb_keymap_num_levels_for_key(b, k, gb);
		xkb_level_index_t amount = na > nb ? na : nb;

		for (xkb_level_index_t l = 0; l < amount; l++)
		{
			const xkb_keysym_t *sa = NULL, *sb = NULL;
			int qa = l < na ? xkb_keymap_key_get_syms_by_level(a, k, ga, l, &sa) : 0;
			int qb = l < nb ? xkb_keymap_key_get_syms_by_level(b, k, gb, l, &sb) : 0;
			/* the character that key, at that level, produces — 0 = none */
			uint32_t ca = qa > 0 ? xkb_keysym_to_utf32(sa[0]) : 0;
			uint32_t cb = qb > 0 ? xkb_keysym_to_utf32(sb[0]) : 0;

			if (ca != cb)
				return 0;
		}
	}
	return 1;
}

Keyboard *keyboard_open_from_keymap(const char *text, size_t length, const char *negotiated,
                                  char **error)
{
	Keyboard *t;
	const char *its;

	if (error)
		*error = NULL;

	/*
	 * ⚠ `ei_keymap_get_size()` counts the final NUL, and whoever reads the descriptor
	 *   adds one of their own: the length may arrive with NULs at the end.  They
	 *   are removed here, once, instead of hoping that `xkbcommon`'s compiler
	 *   digests them — it is the only line standing between someone else's
	 *   descriptor and our compiler.
	 */
	while (length > 0 && text && text[length - 1] == '\0')
		length--;

	if (!text || length == 0)
	{
		registro_dice(LOG_KEYBOARD,
		              "the session handed over no layout: LETTERS cannot "
		              "be typed");
		if (error)
			*error = strdup("session: no keymap handed over by libei");
		return NULL;
	}

	t = calloc(1, sizeof *t);
	if (!t)
		return NULL;
	t->mod_caps = XKB_MOD_INVALID;
	t->mod_num = XKB_MOD_INVALID;

	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		registro_dice(LOG_KEYBOARD, "xkbcommon context not created");
		if (error)
			*error = strdup("xkbcommon: context not created");
		free(t);
		return NULL;
	}
	xkb_context_set_user_data(t->ctx, t);
	xkb_context_set_log_fn(t->ctx, xkb_log_cb);
	xkb_context_set_log_level(t->ctx, XKB_LOG_LEVEL_WARNING);

	t->keymap = xkb_keymap_new_from_buffer(t->ctx, text, length, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                       XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->keymap)
	{
		const char *why =
			t->first_error[0] ? t->first_error : "xkbcommon did not say why";

		registro_dice(LOG_KEYBOARD,
		              "the layout handed over by the session (%zu bytes) does not compile: %s",
		              length, why);
		if (error)
		{
			char msg[448];
			snprintf(msg, sizeof msg, "session: libei's keymap does not compile (%s)", why);
			*error = strdup(msg);
		}
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}

	t->group = 0;
	its = xkb_keymap_layout_get_name(t->keymap, t->group);
	snprintf(t->name, sizeof t->name, "%s [%s]", negotiated ? negotiated : "the session's",
	         its && *its ? its : "unnamed");

	learn_modifiers(t);
	t->mod_caps = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_CAPS);
	t->mod_num = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_NUM);

	if (xkb_keymap_num_layouts(t->keymap) > 1)
		registro_dice(LOG_KEYBOARD,
		              "the session carries %u layouts: ONLY the first is used (%s)",
		              xkb_keymap_num_layouts(t->keymap), its && *its ? its : "unnamed");

	/*
	 * ⛔ THE COMPARISON, AND THE DECLARATION.  Nothing is changed — the session's
	 *    one ALWAYS WINS, because it is the one the compositor applies —
	 *    but if it is not the one the client asked for **it is written**, otherwise
	 *    the user will see a couple of unreachable accents without knowing
	 *    why (`CODER.md` §4.2).
	 */
	if (negotiated)
	{
		Keyboard *asked_size = keyboard_open(negotiated, NULL);

		if (!asked_size)
			registro_dice(LOG_KEYBOARD,
			              "⚠ the client negotiated «%s», which this system does not know: "
			              "the session's is used (%s)",
			              negotiated, its && *its ? its : "unnamed");
		else if (!do_the_same(t->keymap, t->group, asked_size->keymap, asked_size->group))
			registro_dice(LOG_KEYBOARD,
			              "⛔ DECLARED FALLBACK: the client negotiated «%s», the session has "
			              "ANOTHER layout (%s) and THAT one is used — with the other, wrong "
			              "letters would come out. Some characters will stay unreachable "
			              "(DECISIONS.md §5-bis.7)",
			              negotiated, its && *its ? its : "unnamed");
		else
			log_detail(LOG_KEYBOARD, "the session really has «%s»: nothing to declare",
			                   negotiated);
		keyboard_close(asked_size);
	}

	registro_dice(LOG_KEYBOARD, "layout in force (handed over by the session): %s", t->name);
	return t;
}

const char *kbd_layout(Keyboard *t)
{
	return t ? t->name : NULL;
}

/*
 * ⛔⭐ The question that avoids asking twice for the same layout — and
 *     that, above all, avoids NOT asking for it when needed.
 *
 * ⚠ The contract in `keyboard.h` tells the defect that gave birth to it:
 *   a memory of "what I asked for" instead of "what there is".  Here the
 *   answer comes from the REAL keymap, the one `libei` handed over, and it is
 *   compared with what the named layout WOULD DO — not with its name.
 *
 * ⛔ And `do_the_same()` is reused, which is already the only place where
 *    this comparison is written: two comparisons in two places become two
 *    different rules the day one changes (form E2).
 */
int keyboard_is_this(Keyboard *t, const char *name)
{
	Keyboard *another;
	int equal;

	if (!t || !t->keymap || !name || !*name)
		return -1;

	/* ⚠ `NULL` as error channel: here it does not matter WHY it does not compile —
	 *   if it does not compile, the question has no answer, and -1 says so. */
	another = keyboard_open(name, NULL);
	if (!another)
		return -1;

	equal = do_the_same(t->keymap, t->group, another->keymap, another->group);
	keyboard_close(another);
	return equal ? 1 : 0;
}

void keyboard_close(Keyboard *t)
{
	if (!t)
		return;
	if (t->keymap)
		xkb_keymap_unref(t->keymap);
	if (t->ctx)
		xkb_context_unref(t->ctx);
	free(t);
}

/* ------------------------------------------------------------------ *
 * The choice of the path
 * ------------------------------------------------------------------ */

/*
 * From a modifier mask to the keys to press.  Returns 0 if this
 * mask is NOT walkable, and there are two cases:
 *
 *  1. ⛔ **it asks for a lock**.  `xkb_keymap_key_get_mods_for_level()` for a
 *     letter answers "Shift, OR CapsLock": both are ways of
 *     reaching the capital.  But pressing CapsLock CHANGES THE SESSION —
 *     it stays on afterwards, and the next letter comes out capital on its own.  A
 *     modifier is held down and released; a lock is not.  ⇒ The
 *     masks that name CapsLock or NumLock are discarded: there is always
 *     the other way;
 *  2. it asks for a modifier that no key lights up in this layout.
 */
static int mask_keys(Keyboard *t, xkb_mod_mask_t mask,
                                uint16_t report[KEYBOARD_MAX_POSITIONS], size_t *amount)
{
	*amount = 0;
	for (xkb_mod_index_t i = 0; i < t->n_mod; i++)
	{
		if (!(mask & (1u << i)))
			continue;
		if (i == t->mod_caps || i == t->mod_num)
			return 0;
		if (!t->mod_key[i])
			return 0;
		if (*amount + 1 >= KEYBOARD_MAX_POSITIONS) /* +1: the real key */
			return 0;
		report[(*amount)++] = t->mod_key[i];
	}
	return 1;
}

int keyboard_positions_for(Keyboard *t, uint32_t character,
                           uint16_t codes[KEYBOARD_MAX_POSITIONS], size_t *n)
{
	xkb_keycode_t min, max;
	uint16_t best[KEYBOARD_MAX_POSITIONS];
	size_t best_n = 0;
	int found = 0;

	if (!t || !t->keymap || !codes || !n)
		return -1;
	*n = 0;

	/*
	 * ⛔ Out of range and surrogates are NOT "not producible": they are a
	 *    protocol error (`RCP.md` §7.3), and must be told apart — if they returned
	 *    0 the caller would write to the log "the user asked for a
	 *    character the layout does not have", which is false.
	 */
	if (character > 0x10FFFF || (character >= 0xD800 && character <= 0xDFFF))
	{
		/* ⛔ Phase 16 §12: not even here the value — it is what was typed. */
		registro_dice(LOG_KEYBOARD, "character outside the Unicode scalar values: refused");
		return -1;
	}

	min = xkb_keymap_min_keycode(t->keymap);
	max = xkb_keymap_max_keycode(t->keymap);

	for (xkb_keycode_t k = min; k <= max && !(found && best_n == 1); k++)
	{
		xkb_level_index_t levels = xkb_keymap_num_levels_for_key(t->keymap, k, t->group);

		if (k < 8)
			continue; /* it would have no evdev code */

		for (xkb_level_index_t l = 0; l < levels; l++)
		{
			const xkb_keysym_t *symbols = NULL;
			int how_many_symbols;
			int is_match = 0;
			xkb_mod_mask_t masks[8];
			size_t how_many_masks;

			how_many_symbols = xkb_keymap_key_get_syms_by_level(t->keymap, k, t->group, l,
			                                                  &symbols);
			for (int i = 0; i < how_many_symbols; i++)
			{
				/*
				 * ⛔ The comparison is on the CHARACTER, not on the keysym: the same
				 *    character has the legacy form and the Unicode one, and a
				 *    layout may carry either.
				 */
				uint32_t product = xkb_keysym_to_utf32(symbols[i]);
				if (product && product == character)
				{
					is_match = 1;
					break;
				}
			}
			if (!is_match)
				continue;

			how_many_masks = xkb_keymap_key_get_mods_for_level(t->keymap, k, t->group, l,
			                                                    masks,
			                                                    sizeof masks / sizeof *masks);
			if (how_many_masks == 0 && l == 0)
			{
				masks[0] = 0;
				how_many_masks = 1;
			}

			for (size_t m = 0; m < how_many_masks; m++)
			{
				uint16_t via[KEYBOARD_MAX_POSITIONS];
				size_t how_many_mod = 0;

				if (!mask_keys(t, masks[m], via, &how_many_mod))
					continue;

				/*
				 * The shortest path is kept: the fewer modifiers are pressed,
				 * the fewer things can go wrong, and it is also what a hand
				 * would do.  On a tie, the lowest key wins — which is the
				 * criterion that keeps the numeric keypad out of the digits.
				 */
				if (found && how_many_mod + 1 >= best_n)
					continue;

				memcpy(best, via, how_many_mod * sizeof *via);
				best[how_many_mod] = EVDEV_DA_XKB(k);
				best_n = how_many_mod + 1;
				found = 1;
			}
		}
	}

	if (!found)
	{
		/*
		 * ⛔⛔ THE CASE `RCP.md` §7.3 REQUIRES TO BE DECLARED: "if a LETTER
		 *     is not producible in the session's layout, the server
		 *     MUST write it to the log and MUST NOT send a different character
		 *     nor keep quiet".  The line is here and not in the caller because
		 *     here we know WHICH layout it is — which is the only thing that
		 *     whoever reads the log six hours later needs.
		 */
		registro_dice(LOG_KEYBOARD,
		              "a character is not producible with layout %s: NOTHING "
		              "sent (RCP.md §7.3; which one, is not written — phase 16 §12)",
		              t->name);
		return 0;
	}

	memcpy(codes, best, best_n * sizeof *best);
	*n = best_n;
	/* ⛔ Phase 16 §12: neither the character nor the key that makes it — the two together
	 *    are the keystroke, one line per letter. */
	log_detail(LOG_KEYBOARD, "a character ⇒ %zu key positions", best_n);
	return 1;
}
