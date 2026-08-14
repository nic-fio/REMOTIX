/*
 * 04-b25-guasti.c — TRE IMPLEMENTAZIONI SBAGLIATE DI PROPOSITO.
 *
 * ⛔ Esistono per una ragione sola: CERTIFICARE il banco (`CODER.md` §3.3 e
 *    §4.6).  Un banco che non ha mai visto il difetto non e' una prova — e' un
 *    verde che da' fiducia.  `04-b25-lancia.sh` compila `04-b25-tastiera.c`
 *    contro ciascuno di questi e PRETENDE che dica ROSSO.
 *
 * ⚠ Nessuna di queste tre e' inventata: sono i tre modi in cui questo modulo
 *   sbaglia davvero, e ciascuna ha un nome nel prodotto reale.
 *
 *   GUASTO=1  «manda la lettera senza accento».  Non trova la «e'» accentata e
 *             ripiega sulla «e».  ⇒ E' precisamente cio' che `RCP.md` §7.3
 *             vieta: «NON DEVE mandare un carattere diverso».  Per l'utente
 *             sono le lettere sbagliate nel campo della parola d'ordine.
 *
 *   GUASTO=2  «dimentica i modificatori».  Trova il tasto giusto e consegna
 *             solo quello: su `it` esce «e` » invece di «e'», su `us` esce «2»
 *             invece di «@».  E' il difetto che un banco che confronta i
 *             CODICI non vedrebbe mai — il tasto e' quello giusto.
 *
 *   GUASTO=3  «ripiega su us in silenzio».  La disposizione chiesta non si
 *             carica e si carica `us` senza dirlo, continuando a dichiarare il
 *             nome chiesto.  E' la trappola di `CODER.md` §4.2 nella sua forma
 *             peggiore: il sintomo e' «scrive le lettere sbagliate» e nessuno
 *             lo collega alla disposizione.
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
	/* ⛔ IL RIPIEGO SILENZIOSO: non si carica, si carica `us`, e non si dice. */
	if (!t->km)
		t->km = compila(t->ctx, "us");
#endif

	if (!t->km)
	{
		if (errore)
			*errore = strdup("la disposizione non si compila");
		xkb_context_unref(t->ctx);
		free(t);
		return NULL;
	}
	snprintf(t->nome, sizeof t->nome, "%s", chiesta);
	return t;
}

/*
 * GUASTO=4  ⛔ «si fida del nome negoziato invece che della disposizione che la
 *           sessione ha consegnato».  E' IL DIFETTO PER CUI IL CONTRATTO E'
 *           CAMBIATO il 14 agosto 2026: la keymap arriva da `libei` e viene
 *           buttata via, e si compila quella che il client ha chiesto.
 *
 *           Sessione `it`, client `us`, l'utente scrive `[`: questo manda il
 *           tasto 26 — giusto su `us` — e sullo schermo compare **«è»**.  Il
 *           banco deve accusarlo, o la cura non e' provata.
 *
 * ⚠ Per gli altri tre guasti questa funzione e' CORRETTA: ciascuno deve
 *   sbagliare una cosa sola, o non si sa che cosa il banco abbia visto.
 */
Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza, const char *negoziata,
                                  char **errore)
{
	Tastiera *t;

	if (errore)
		*errore = NULL;

#if GUASTO == 4
	/* ⛔ la keymap della sessione non si guarda nemmeno. */
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
	snprintf(t->nome, sizeof t->nome, "%s", negoziata ? negoziata : "della sessione");
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

/* Cerca un tasto che produca `carattere`; ritorna il livello in `*livello`. */
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
		/* ⛔ «meglio qualcosa che niente»: si toglie l'accento e si manda
		 *    quella.  E' la falsificazione che RCP.md §7.3 vieta. */
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
		/* La regoletta ingenua di v1: livello 1 = Maiusc, 2 = AltGr, 3 = tutt'e due. */
		if (livello == 1 || livello == 3)
			codici[q++] = 42;
		if (livello == 2 || livello == 3)
			codici[q++] = 100;
#endif
		/* ⛔ GUASTO=2: i modificatori non si mettono affatto. */
		codici[q++] = XKB_A_EVDEV(tasto);
		*n = q;
	}
	return 1;
}
