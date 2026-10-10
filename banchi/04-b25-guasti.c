/*
 * 04-b25-guasti.c — THREE IMPLEMENTATIONS WRONG ON PURPOSE.
 *
 * ⛔ They exist for one reason only: to CERTIFY the bench (`CODER.md` §3.3 and
 *    §4.6).  A bench that has never seen the defect is not a test — it is a
 *    green that gives false confidence.  `04-b25-lancia.sh` compiles `04-b25-tastiera.c`
 *    against each of these and DEMANDS that it says ROSSO.
 *
 * ⚠ None of these three is invented: they are the three ways this module
 *   really goes wrong, and each has a name in the real product.
 *
 *   GUASTO=1  «sends the letter without the accent».  It does not find the accented «e'» and
 *             falls back on the «e».  ⇒ It is precisely what `RCP.md` §7.3
 *             forbids: «MUST NOT send a different character».  For the user
 *             it is the wrong letters in the password field.
 *
 *   GUASTO=2  «forgets the modifiers».  It finds the right key and hands over
 *             only that: on `it` out comes «e` » instead of «e'», on `us` out comes «2»
 *             instead of «@».  It is the defect that a bench comparing the
 *             CODES would never see — the key is the right one.
 *
 *   GUASTO=3  «falls back to us silently».  The requested layout does not
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

#ifndef GUASTO
#define GUASTO 1
#endif

#define XKB_A_EVDEV(k) ((uint16_t)((k) - 8))

struct tastiera
{
	struct xkb_context *ctx;
	struct xkb_keymap *km;
	char nome[128];
};

static void zitto(struct xkb_context *c, enum xkb_log_level l, const char *f, va_list a)
{
	(void)c;
	(void)l;
	(void)f;
	(void)a;
}

static struct xkb_keymap *compila(struct xkb_context *ctx, const char *disposizione)
{
	char layout[64] = {0}, variante[64] = {0};
	const char *par = strchr(disposizione, '(');
	struct xkb_rule_names nomi;

	if (par)
	{
		size_t n = (size_t)(par - disposizione);
		if (n >= sizeof layout)
			return NULL;
		memcpy(layout, disposizione, n);
		snprintf(variante, sizeof variante, "%s", par + 1);
		char *ch = strchr(variante, ')');
		if (ch)
			*ch = 0;
	}
	else
		snprintf(layout, sizeof layout, "%s", disposizione);

	nomi.rules = "evdev";
	nomi.model = "pc105";
	nomi.layout = layout;
	nomi.variant = variante;
	nomi.options = "";
	return xkb_keymap_new_from_names(ctx, &nomi, XKB_KEYMAP_COMPILE_NO_FLAGS);
}

Tastiera *tastiera_apri(const char *disposizione, char **errore)
{
	Tastiera *t = calloc(1, sizeof *t);
	const char *chiesta = disposizione ? disposizione : "us";

	if (errore)
		*errore = NULL;
	if (!t)
		return NULL;
	t->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!t->ctx)
	{
		free(t);
		return NULL;
	}
	xkb_context_set_log_fn(t->ctx, zitto);
	t->km = compila(t->ctx, chiesta);

#if GUASTO == 3
	/* ⛔ THE SILENT FALLBACK: it does not load, `us` is loaded, and nobody is told. */
	if (!t->km)
		t->km = compila(t->ctx, "us");
#endif

	if (!t->km)
	{
		if (errore)
			*errore = strdup("the layout does not compile");
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}
	snprintf(t->nome, sizeof t->nome, "%s", chiesta);
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
Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza, const char *negoziata,
                                  char **errore)
{
	Tastiera *t;

	if (errore)
		*errore = NULL;

#if GUASTO == 4
	/* ⛔ the session's keymap is not even looked at. */
	(void) testo;
	(void) lunghezza;
	return tastiera_apri(negoziata ? negoziata : "us", errore);
#else
	(void) negoziata;
	while (lunghezza > 0 && testo && testo[lunghezza - 1] == '\0')
		lunghezza--;
	if (!testo || lunghezza == 0)
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
	xkb_context_set_log_fn(t->ctx, zitto);
	t->km = xkb_keymap_new_from_buffer(t->ctx, testo, lunghezza, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                   XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!t->km)
	{
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}
	snprintf(t->nome, sizeof t->nome, "%s", negoziata ? negoziata : "the session's");
	return t;
#endif
}

const char *tastiera_disposizione(Tastiera *t) { return t ? t->nome : NULL; }

void tastiera_chiudi(Tastiera *t)
{
	if (!t)
		return;
	xkb_keymap_unref(t->km);
	xkb_context_unref(t->ctx);
	free(t);
}

/* Looks for a key that produces `carattere`; returns the level in `*livello`. */
static int cerca(struct xkb_keymap *km, uint32_t carattere, xkb_keycode_t *tasto,
                 xkb_level_index_t *livello)
{
	xkb_keycode_t min = xkb_keymap_min_keycode(km), max = xkb_keymap_max_keycode(km);

	for (xkb_keycode_t k = min; k <= max; k++)
	{
		xkb_level_index_t n = xkb_keymap_num_levels_for_key(km, k, 0);
		for (xkb_level_index_t l = 0; l < n; l++)
		{
			const xkb_keysym_t *sim = NULL;
			int quanti = xkb_keymap_key_get_syms_by_level(km, k, 0, l, &sim);
			for (int i = 0; i < quanti; i++)
				if (xkb_keysym_to_utf32(sim[i]) == carattere)
				{
					*tasto = k;
					*livello = l;
					return 1;
				}
		}
	}
	return 0;
}

int tastiera_posizioni_per(Tastiera *t, uint32_t carattere, uint16_t codici[TASTIERA_MAX_POSIZIONI],
                           size_t *n)
{
	xkb_keycode_t tasto;
	xkb_level_index_t livello;

	if (!t || !codici || !n)
		return -1;
	*n = 0;
	if (carattere > 0x10FFFF || (carattere >= 0xD800 && carattere <= 0xDFFF))
		return -1;

	if (!cerca(t->km, carattere, &tasto, &livello))
	{
#if GUASTO == 1
		/* ⛔ «better something than nothing»: the accent is dropped and that
		 *    letter is sent.  It is the falsification RCP.md §7.3 forbids. */
		static const struct
		{
			uint32_t accentata, nuda;
		} pieghe[] = {{0x00E0, 'a'}, {0x00E8, 'e'}, {0x00E9, 'e'}, {0x00EC, 'i'},
		              {0x00F2, 'o'}, {0x00F9, 'u'}, {0x00E7, 'c'}};
		for (size_t i = 0; i < sizeof pieghe / sizeof *pieghe; i++)
			if (pieghe[i].accentata == carattere &&
			    cerca(t->km, pieghe[i].nuda, &tasto, &livello))
				goto trovato;
#endif
		return 0;
	}
#if GUASTO == 1
trovato:
#endif
	{
		size_t q = 0;
#if GUASTO != 2
		/* The naive little rule of v1: level 1 = Shift, 2 = AltGr, 3 = both. */
		if (livello == 1 || livello == 3)
			codici[q++] = 42;
		if (livello == 2 || livello == 3)
			codici[q++] = 100;
#endif
		/* ⛔ GUASTO=2: the modifiers are not added at all. */
		codici[q++] = XKB_A_EVDEV(tasto);
		*n = q;
	}
	return 1;
}
