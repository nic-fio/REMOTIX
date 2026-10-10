/*
 * tastiera.c — FROM THE LETTER TO THE HAMMER.  Link A5 of phase 4.
 *
 * ⛔ The contract is in `tastiera.h`, which belongs to the coordinator: here it is
 *    IMPLEMENTED, the seam is not changed.
 *
 * ---------------------------------------------------------------------------
 * THE PROBLEM, in one line
 *
 * On the wire letters travel as letters (`SPECIFICHE.md` §7.3,
 * `DECISIONI.md` §5-bis.6), but `libei` — the only way to inject input into a
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
 *     `xkb_keysym_to_utf32(simbolo) == carattere`, which covers both.
 *
 * ⚠ And one thing from v1 was NOT carried over, because it does not belong to this file: the
 *   count of what is pressed and the release at detach.  In V2 that lives
 *   in `input.c` (`input_rilascia_tutto()`, `input.h:98`), and keeping two copies
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
 *     `*errore`.  Whoever reads the log finds the reason, not a NULL;
 *   · ⛔ and `tastiera_disposizione()` carries inside the name the COMPILED
 *     layout gives itself — «it [Italian]», «us [English (US)]».  If one day
 *     a fallback came in from somewhere else, it would show **in the log**
 *     as «it [English (US)]», which is a line that reads by itself.
 *
 * `banchi/04-b25-tastiera.c` checks all three, and `banchi/04-b25-lancia.sh`
 * puts in front of it an implementation that falls back on purpose, to certify that the
 * bench would see it.
 */
#include "tastiera.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <xkbcommon/xkbcommon.h>
#include <xkbcommon/xkbcommon-names.h>

#include "registro.h"

/*
 * ⚠ The log area lives here and not in `registro.h`: that file is shared by
 *   ten links writing at the same moment, and a line added in
 *   there would be a guaranteed collision.  To be merged into `registro.h` when the
 *   phase closes — it is a seam, and seams are kept by the coordinator.
 */
#define REG_TASTIERA "tastiera"

/* XKB numbers keys starting from 8, evdev from 0 (`RCP.md` §7.3). */
#define EVDEV_DA_XKB(k) ((uint16_t)((k) - 8))

/* How many modifiers a layout can have.  xkbcommon allows 32. */
#define MAX_MOD 32

struct tastiera
{
	struct xkb_context *ctx;
	struct xkb_keymap *keymap;
	xkb_layout_index_t gruppo;

	/* «it [Italian]»: the requested and the compiled in the same line. */
	char nome[192];

	/*
	 * ⛔ modifier → key that lights it up, ASKED of the layout and not
	 *    written by hand.  0 = no key lights it up on its own.
	 */
	uint16_t tasto_del_mod[MAX_MOD];
	xkb_mod_index_t n_mod;

	/* The two locks, which are NEVER used to make a letter: see below. */
	xkb_mod_index_t mod_maiuscole, mod_numeri;

	/* The hijacking of xkbcommon's log, during compilation. */
	char primo_errore[256];
	int errori;

	/*
	 * ⭐⭐ WHOSE LINE IT IS — 27 August 2026, the red of C9.
	 *
	 * ⛔ This module writes `tastiera` area lines from TWO processes of different
	 *    kinds (`registro.h`), and until now treated them the same way:
	 *
	 *      · in the CHILD it is already fine: `registro_identita()` is set
	 *        at `exec` and every line of the process carries it;
	 *      · in the PARENT it is not: `tastiera_apri()` is called by `webtransport.c` to
	 *        answer "does this layout exist?" during ATTACCA, and
	 *        there a single process serves ALL sessions.
	 *
	 * `[M]` 26 August 2026, mesh C9, two tenants alive together: the lines
	 *      «modificatore N: si preferisce…» and «disposizione in vigore: …»
	 *      came out TWICE, identical word for word, ⛔ and there was no way
	 *      to tell which was whose.
	 *
	 * ⇒ The name is carried by the KEYBOARD, for the whole life of the opening: so
	 *   the lines coming out of `xkb_parla()` see it too, which has nothing else
	 *   in hand but this structure.
	 * ⚠ Empty is the truth when it is not known: `registro.c` then falls back
	 *   on the PROCESS identity, which in the child is the right one.  ⇒ The
	 *   `calloc()` leaves this field as it is, and the child's path does not
	 *   change one bit.
	 */
	char chi[REG_IDENTITA_MAX + 1];
};

/* ------------------------------------------------------------------ *
 * xkbcommon's log, hijacked
 * ------------------------------------------------------------------ */
static void xkb_parla(struct xkb_context *ctx, enum xkb_log_level livello, const char *fmt,
                      va_list ap)
{
	Tastiera *t = xkb_context_get_user_data(ctx);
	char riga[256];
	size_t n;

	if (!t)
		return;
	vsnprintf(riga, sizeof riga, fmt, ap);
	/* xkbcommon sends the line with a newline at the end: here it would be a nuisance. */
	n = strlen(riga);
	while (n && (riga[n - 1] == '\n' || riga[n - 1] == '\r'))
		riga[--n] = 0;

	if (livello <= XKB_LOG_LEVEL_ERROR)
	{
		t->errori++;
		if (!t->primo_errore[0])
			snprintf(t->primo_errore, sizeof t->primo_errore, "%s", riga);
		registro_dettaglio_di(REG_TASTIERA, t->chi, "xkbcommon: %s", riga);
	}
	else
		registro_dettaglio_di(REG_TASTIERA, t->chi, "xkbcommon (warning): %s", riga);
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
 *   `ERRORE_PROTOCOLLO`, a well-formed but unknown layout is
 *   `SESSIONE_NON_SERVIBILE`.  The contract of `tastiera.h` gives a single
 *   output channel (NULL + text), so the two are told apart by the PREFIX of the
 *   text: "form:" or "unknown:".  ⇒ It is one of the seams the
 *   report asks of the coordinator.
 * ------------------------------------------------------------------ */
static int carattere_ammesso(char c)
{
	return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') ||
	       c == '_' || c == '-';
}

static int forma_valida(const char *s, char *layout, size_t nl, char *variante, size_t nv)
{
	const char *par = strchr(s, '(');
	size_t len_l;

	if (!*s || strlen(s) > 64)
		return 0;

	len_l = par ? (size_t)(par - s) : strlen(s);
	if (len_l == 0 || len_l >= nl)
		return 0;
	for (size_t i = 0; i < len_l; i++)
		if (!carattere_ammesso(s[i]))
			return 0;
	memcpy(layout, s, len_l);
	layout[len_l] = 0;

	variante[0] = 0;
	if (!par)
		return 1;

	{
		const char *chiusa = strchr(par + 1, ')');
		size_t len_v;

		if (!chiusa || chiusa[1] != 0)
			return 0;
		len_v = (size_t)(chiusa - par - 1);
		if (len_v == 0 || len_v >= nv)
			return 0;
		for (size_t i = 0; i < len_v; i++)
			if (!carattere_ammesso(par[1 + i]))
				return 0;
		memcpy(variante, par + 1, len_v);
		variante[len_v] = 0;
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
static const uint16_t TASTI_DI_UNA_TASTIERA_VERA[] = {
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
static int un_solo_modificatore(struct xkb_keymap *km, xkb_keycode_t k, int *quale)
{
	struct xkb_state *st = xkb_state_new(km);
	xkb_mod_mask_t attivi;

	if (!st)
		return 0;
	xkb_state_update_key(st, k, XKB_KEY_DOWN);
	attivi = xkb_state_serialize_mods(st, XKB_STATE_MODS_EFFECTIVE);
	xkb_state_unref(st);

	if (!attivi || (attivi & (attivi - 1)) != 0)
		return 0;
	*quale = __builtin_ctz(attivi);
	return 1;
}

static void impara_i_modificatori(Tastiera *t)
{
	xkb_keycode_t min = xkb_keymap_min_keycode(t->keymap);
	xkb_keycode_t max = xkb_keymap_max_keycode(t->keymap);
	uint8_t gia_preferito[MAX_MOD] = {0};
	size_t i;

	t->n_mod = xkb_keymap_num_mods(t->keymap);
	if (t->n_mod > MAX_MOD)
		t->n_mod = MAX_MOD;

	/* 1. we ask the layout, key by key. */
	for (xkb_keycode_t k = min; k <= max; k++)
	{
		int quale;
		if (k < 8 || !un_solo_modificatore(t->keymap, k, &quale))
			continue;
		if (quale < (int)t->n_mod && !t->tasto_del_mod[quale])
			t->tasto_del_mod[quale] = EVDEV_DA_XKB(k);
	}

	/*
	 * 2. and then the preference, on top of the answers already obtained.
	 *
	 * ⚠ `gia_preferito` is not a theoretical precaution: without it, the list was
	 *   walked to the end and for Shift **the right one** won (evdev 54),
	 *   because it was the last of the two to pass through here.  It worked — the bench
	 *   said green — but a log saying "right Shift" where every hand
	 *   uses the left is a line that makes whoever reads it lose half an hour.
	 *   ⇒ The FIRST of the list wins, which is the order in which one types by hand.
	 */
	for (i = 0; i < sizeof TASTI_DI_UNA_TASTIERA_VERA / sizeof *TASTI_DI_UNA_TASTIERA_VERA; i++)
	{
		uint16_t evdev = TASTI_DI_UNA_TASTIERA_VERA[i];
		xkb_keycode_t k = (xkb_keycode_t)evdev + 8;
		int quale;

		if (k < min || k > max)
			continue;
		if (!un_solo_modificatore(t->keymap, k, &quale))
			continue;
		if (quale >= (int)t->n_mod)
			continue;
		if (gia_preferito[quale] || t->tasto_del_mod[quale] == evdev)
		{
			gia_preferito[quale] = 1;
			continue;
		}
		registro_dettaglio_di(REG_TASTIERA, t->chi,
		                      "modifier %d: key %u is preferred to %u (a real "
		                      "keyboard has the first)",
		                      quale, evdev, t->tasto_del_mod[quale]);
		t->tasto_del_mod[quale] = evdev;
		gia_preferito[quale] = 1;
	}
}

/* ------------------------------------------------------------------ *
 * The opening
 * ------------------------------------------------------------------ */
Tastiera *tastiera_apri(const char *disposizione, char **errore)
{
	/* ⚠ `NULL` is the truth for whoever does not serve a single session: the lines
	 *   will come out with the PROCESS identity, if there is one (the child), and bare if
	 *   there is not.  ⛔ Whoever does not know keeps quiet (`registro.h`). */
	return tastiera_apri_per(disposizione, NULL, errore);
}

Tastiera *tastiera_apri_per(const char *disposizione, const char *chi, char **errore)
{
	Tastiera *t;
	char layout[72], variante[72];
	struct xkb_rule_names nomi;
	const char *chiesta = disposizione ? disposizione : "(the session's own)";

	if (errore)
		*errore = NULL;

	t = calloc(1, sizeof *t);
	if (!t)
		return NULL;
	t->mod_maiuscole = XKB_MOD_INVALID;
	t->mod_numeri = XKB_MOD_INVALID;
	/* ⭐ The name is set BEFORE any line: the first that can come out is
	 *   the malformed-shape one, three lines below. */
	if (chi && *chi)
		snprintf(t->chi, sizeof t->chi, "%s", chi);

	if (disposizione &&
	    !forma_valida(disposizione, layout, sizeof layout, variante, sizeof variante))
	{
		/* ⛔ `RCP.md` §4.5: this is ERRORE_PROTOCOLLO, not SESSIONE_NON_SERVIBILE. */
		registro_dice_di(REG_TASTIERA, t->chi,
		                 "malformed layout, refused without even trying: %.64s",
		                 disposizione);
		if (errore)
			*errore = strdup("form: not an XKB layout name (RCP.md §4.5)");
		free(t);
		return NULL;
	}

	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		registro_dice_di(REG_TASTIERA, t->chi, "xkbcommon context not created");
		if (errore)
			*errore = strdup("xkbcommon: context not created");
		free(t);
		return NULL;
	}
	xkb_context_set_user_data(t->ctx, t);
	xkb_context_set_log_fn(t->ctx, xkb_parla);
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
	 * ⛔ The intended exception: `disposizione == NULL` means "the one in force
	 *    in the session", and there the environment IS the answer.  Then we let
	 *    `xkbcommon` decide — and we WRITE it to the log, because it is a
	 *    case in which we do not know what we loaded until we have it
	 *    told to us.
	 */
	if (disposizione)
	{
		nomi.rules = "evdev";
		nomi.model = "pc105";
		nomi.layout = layout;
		nomi.variant = variante;
		nomi.options = "";
	}
	else
	{
		nomi.rules = NULL;
		nomi.model = NULL;
		nomi.layout = NULL;
		nomi.variant = NULL;
		nomi.options = NULL;
	}

	t->keymap = xkb_keymap_new_from_names(t->ctx, &nomi, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->keymap)
	{
		/*
		 * ⛔ HERE STOOD THE FALLBACK, AND IT IS NOT THERE.  The temptation is one line: "if
		 *    it does not compile, retry with us".  The service would go on —
		 *    `CODER.md` §4.2 asks for it — but typing the wrong letters
		 *    forever, without anyone knowing why.  ⇒ The soft degradation
		 *    of `DECISIONI.md` §5-bis.7 is something else: the session
		 *    keeps the layout it already has, and that is decided by THE CALLER,
		 *    who knows whether a session exists or not.  Here we fail and say so.
		 */
		const char *perche =
			t->primo_errore[0] ? t->primo_errore : "xkbcommon did not say why";

		registro_dice_di(REG_TASTIERA, t->chi,
		                 "layout «%s» NOT loaded, and no fallback to any other: %s",
		                 chiesta, perche);
		if (errore)
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
			         chiesta, perche);
			*errore = strdup(msg);
		}
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}

	t->gruppo = 0;
	snprintf(t->nome, sizeof t->nome, "%s [%s]", disposizione ? disposizione : "default",
	         xkb_keymap_layout_get_name(t->keymap, t->gruppo)
	             ? xkb_keymap_layout_get_name(t->keymap, t->gruppo)
	             : "unnamed");

	impara_i_modificatori(t);
	t->mod_maiuscole = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_CAPS);
	t->mod_numeri = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_NUM);

	/*
	 * ⚠ If `xkb_keymap_num_layouts()` gave more than one, the string would have
	 *   named more layouts: `RCP.md` §4.5 does not allow it, but if one
	 *   day it did (`DECISIONI.md` §5-bis.7 keeps it open) here only
	 *   the first would be used, silently.  ⇒ It is declared at once.
	 */
	if (xkb_keymap_num_layouts(t->keymap) > 1)
		registro_dice_di(REG_TASTIERA, t->chi,
		                 "layout «%s»: the session carries %u, ONLY the first is used",
		                 chiesta, xkb_keymap_num_layouts(t->keymap));

	registro_dice_di(REG_TASTIERA, t->chi, "layout in force: %s", t->nome);
	return t;
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ THE LAYOUT AS THE SESSION HANDS IT OVER
 *
 * ⭐ This function was born from a refusal of the mandate, accepted on 14 August
 *    2026.  The contract said `tastiera_apri("it")` — compile a
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
 * ⚠ And it makes false the sentence of `DECISIONI.md` §5-bis.7 — "an old
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
 * market has.  ⇒ With the total comparison, the line «RIPIEGO DICHIARATO»
 * would have come out **at every connection**, including the one where everything is fine.
 * A false alarm on this line is worth as much as a silence: whoever reads the log
 * learns to skip it, and its usefulness is over.
 *
 * ⚠ And it was not found by the bench — the bench was green, because it looked at the
 *   letter coming out and the letter came out right.  I found it **reading the
 *   log**.  ⇒ Now the bench also looks at the line (`04-b25-tastiera.c`,
 *   `prova_dichiarazione`), which is the only part of this work the user
 *   will see when something does not add up.
 *
 * ⇒ The keys that produce a character are compared.  Two layouts that
 *   differ only on the multimedia keys are the same layout **for
 *   what this file does**, and saying so would be noise.
 */
static int fanno_la_stessa_cosa(struct xkb_keymap *a, xkb_layout_index_t ga,
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
		xkb_level_index_t quanti = na > nb ? na : nb;

		for (xkb_level_index_t l = 0; l < quanti; l++)
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

Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza, const char *negoziata,
                                  char **errore)
{
	Tastiera *t;
	const char *suo;

	if (errore)
		*errore = NULL;

	/*
	 * ⚠ `ei_keymap_get_size()` counts the final NUL, and whoever reads the descriptor
	 *   adds one of their own: the length may arrive with NULs at the end.  They
	 *   are removed here, once, instead of hoping that `xkbcommon`'s compiler
	 *   digests them — it is the only line standing between someone else's
	 *   descriptor and our compiler.
	 */
	while (lunghezza > 0 && testo && testo[lunghezza - 1] == '\0')
		lunghezza--;

	if (!testo || lunghezza == 0)
	{
		registro_dice(REG_TASTIERA,
		              "the session handed over no layout: LETTERS cannot "
		              "be typed");
		if (errore)
			*errore = strdup("session: no keymap handed over by libei");
		return NULL;
	}

	t = calloc(1, sizeof *t);
	if (!t)
		return NULL;
	t->mod_maiuscole = XKB_MOD_INVALID;
	t->mod_numeri = XKB_MOD_INVALID;

	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		registro_dice(REG_TASTIERA, "xkbcommon context not created");
		if (errore)
			*errore = strdup("xkbcommon: context not created");
		free(t);
		return NULL;
	}
	xkb_context_set_user_data(t->ctx, t);
	xkb_context_set_log_fn(t->ctx, xkb_parla);
	xkb_context_set_log_level(t->ctx, XKB_LOG_LEVEL_WARNING);

	t->keymap = xkb_keymap_new_from_buffer(t->ctx, testo, lunghezza, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                       XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->keymap)
	{
		const char *perche =
			t->primo_errore[0] ? t->primo_errore : "xkbcommon did not say why";

		registro_dice(REG_TASTIERA,
		              "the layout handed over by the session (%zu bytes) does not compile: %s",
		              lunghezza, perche);
		if (errore)
		{
			char msg[448];
			snprintf(msg, sizeof msg, "session: libei's keymap does not compile (%s)", perche);
			*errore = strdup(msg);
		}
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}

	t->gruppo = 0;
	suo = xkb_keymap_layout_get_name(t->keymap, t->gruppo);
	snprintf(t->nome, sizeof t->nome, "%s [%s]", negoziata ? negoziata : "the session's",
	         suo && *suo ? suo : "unnamed");

	impara_i_modificatori(t);
	t->mod_maiuscole = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_CAPS);
	t->mod_numeri = xkb_keymap_mod_get_index(t->keymap, XKB_MOD_NAME_NUM);

	if (xkb_keymap_num_layouts(t->keymap) > 1)
		registro_dice(REG_TASTIERA,
		              "the session carries %u layouts: ONLY the first is used (%s)",
		              xkb_keymap_num_layouts(t->keymap), suo && *suo ? suo : "unnamed");

	/*
	 * ⛔ THE COMPARISON, AND THE DECLARATION.  Nothing is changed — the session's
	 *    one ALWAYS WINS, because it is the one the compositor applies —
	 *    but if it is not the one the client asked for **it is written**, otherwise
	 *    the user will see a couple of unreachable accents without knowing
	 *    why (`CODER.md` §4.2).
	 */
	if (negoziata)
	{
		Tastiera *chiesta = tastiera_apri(negoziata, NULL);

		if (!chiesta)
			registro_dice(REG_TASTIERA,
			              "⚠ the client negotiated «%s», which this system does not know: "
			              "the session's is used (%s)",
			              negoziata, suo && *suo ? suo : "unnamed");
		else if (!fanno_la_stessa_cosa(t->keymap, t->gruppo, chiesta->keymap, chiesta->gruppo))
			registro_dice(REG_TASTIERA,
			              "⛔ FALLBACK DECLARED: the client negotiated «%s», the session has "
			              "ANOTHER layout (%s) and THAT one is used — with the other, wrong "
			              "letters would come out. Some characters will stay unreachable "
			              "(DECISIONI.md §5-bis.7)",
			              negoziata, suo && *suo ? suo : "unnamed");
		else
			registro_dettaglio(REG_TASTIERA, "the session really has «%s»: nothing to declare",
			                   negoziata);
		tastiera_chiudi(chiesta);
	}

	registro_dice(REG_TASTIERA, "layout in force (handed over by the session): %s", t->nome);
	return t;
}

const char *tastiera_disposizione(Tastiera *t)
{
	return t ? t->nome : NULL;
}

/*
 * ⛔⭐ The question that avoids asking twice for the same layout — and
 *     that, above all, avoids NOT asking for it when needed.
 *
 * ⚠ The contract in `tastiera.h` tells the defect that gave birth to it:
 *   a memory of "what I asked for" instead of "what there is".  Here the
 *   answer comes from the REAL keymap, the one `libei` handed over, and it is
 *   compared with what the named layout WOULD DO — not with its name.
 *
 * ⛔ And `fanno_la_stessa_cosa()` is reused, which is already the only place where
 *    this comparison is written: two comparisons in two places become two
 *    different rules the day one changes (form E2).
 */
int tastiera_e_questa(Tastiera *t, const char *nome)
{
	Tastiera *altra;
	int uguali;

	if (!t || !t->keymap || !nome || !*nome)
		return -1;

	/* ⚠ `NULL` as error channel: here it does not matter WHY it does not compile —
	 *   if it does not compile, the question has no answer, and -1 says so. */
	altra = tastiera_apri(nome, NULL);
	if (!altra)
		return -1;

	uguali = fanno_la_stessa_cosa(t->keymap, t->gruppo, altra->keymap, altra->gruppo);
	tastiera_chiudi(altra);
	return uguali ? 1 : 0;
}

void tastiera_chiudi(Tastiera *t)
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
static int tasti_della_maschera(Tastiera *t, xkb_mod_mask_t maschera,
                                uint16_t fuori[TASTIERA_MAX_POSIZIONI], size_t *quanti)
{
	*quanti = 0;
	for (xkb_mod_index_t i = 0; i < t->n_mod; i++)
	{
		if (!(maschera & (1u << i)))
			continue;
		if (i == t->mod_maiuscole || i == t->mod_numeri)
			return 0;
		if (!t->tasto_del_mod[i])
			return 0;
		if (*quanti + 1 >= TASTIERA_MAX_POSIZIONI) /* +1: the real key */
			return 0;
		fuori[(*quanti)++] = t->tasto_del_mod[i];
	}
	return 1;
}

int tastiera_posizioni_per(Tastiera *t, uint32_t carattere,
                           uint16_t codici[TASTIERA_MAX_POSIZIONI], size_t *n)
{
	xkb_keycode_t min, max;
	uint16_t migliori[TASTIERA_MAX_POSIZIONI];
	size_t migliori_n = 0;
	int trovato = 0;

	if (!t || !t->keymap || !codici || !n)
		return -1;
	*n = 0;

	/*
	 * ⛔ Out of range and surrogates are NOT "not producible": they are a
	 *    protocol error (`RCP.md` §7.3), and must be told apart — if they returned
	 *    0 the caller would write to the log "the user asked for a
	 *    character the layout does not have", which is false.
	 */
	if (carattere > 0x10FFFF || (carattere >= 0xD800 && carattere <= 0xDFFF))
	{
		/* ⛔ Phase 16 §12: not even here the value — it is what was typed. */
		registro_dice(REG_TASTIERA, "character outside the Unicode scalar values: refused");
		return -1;
	}

	min = xkb_keymap_min_keycode(t->keymap);
	max = xkb_keymap_max_keycode(t->keymap);

	for (xkb_keycode_t k = min; k <= max && !(trovato && migliori_n == 1); k++)
	{
		xkb_level_index_t livelli = xkb_keymap_num_levels_for_key(t->keymap, k, t->gruppo);

		if (k < 8)
			continue; /* it would have no evdev code */

		for (xkb_level_index_t l = 0; l < livelli; l++)
		{
			const xkb_keysym_t *simboli = NULL;
			int quanti_simboli;
			int e_lui = 0;
			xkb_mod_mask_t maschere[8];
			size_t quante_maschere;

			quanti_simboli = xkb_keymap_key_get_syms_by_level(t->keymap, k, t->gruppo, l,
			                                                  &simboli);
			for (int i = 0; i < quanti_simboli; i++)
			{
				/*
				 * ⛔ The comparison is on the CHARACTER, not on the keysym: the same
				 *    character has the legacy form and the Unicode one, and a
				 *    layout may carry either.
				 */
				uint32_t prodotto = xkb_keysym_to_utf32(simboli[i]);
				if (prodotto && prodotto == carattere)
				{
					e_lui = 1;
					break;
				}
			}
			if (!e_lui)
				continue;

			quante_maschere = xkb_keymap_key_get_mods_for_level(t->keymap, k, t->gruppo, l,
			                                                    maschere,
			                                                    sizeof maschere / sizeof *maschere);
			if (quante_maschere == 0 && l == 0)
			{
				maschere[0] = 0;
				quante_maschere = 1;
			}

			for (size_t m = 0; m < quante_maschere; m++)
			{
				uint16_t via[TASTIERA_MAX_POSIZIONI];
				size_t quanti_mod = 0;

				if (!tasti_della_maschera(t, maschere[m], via, &quanti_mod))
					continue;

				/*
				 * The shortest path is kept: the fewer modifiers are pressed,
				 * the fewer things can go wrong, and it is also what a hand
				 * would do.  On a tie, the lowest key wins — which is the
				 * criterion that keeps the numeric keypad out of the digits.
				 */
				if (trovato && quanti_mod + 1 >= migliori_n)
					continue;

				memcpy(migliori, via, quanti_mod * sizeof *via);
				migliori[quanti_mod] = EVDEV_DA_XKB(k);
				migliori_n = quanti_mod + 1;
				trovato = 1;
			}
		}
	}

	if (!trovato)
	{
		/*
		 * ⛔⛔ THE CASE `RCP.md` §7.3 REQUIRES TO BE DECLARED: "if a LETTER
		 *     is not producible in the session's layout, the server
		 *     MUST write it to the log and MUST NOT send a different character
		 *     nor keep quiet".  The line is here and not in the caller because
		 *     here we know WHICH layout it is — which is the only thing that
		 *     whoever reads the log six hours later needs.
		 */
		registro_dice(REG_TASTIERA,
		              "a character is not producible with layout %s: NOTHING "
		              "sent (RCP.md §7.3; which one, is not written — phase 16 §12)",
		              t->nome);
		return 0;
	}

	memcpy(codici, migliori, migliori_n * sizeof *migliori);
	*n = migliori_n;
	/* ⛔ Phase 16 §12: neither the character nor the key that makes it — the two together
	 *    are the keystroke, one line per letter. */
	registro_dettaglio(REG_TASTIERA, "a character ⇒ %zu key positions", migliori_n);
	return 1;
}
