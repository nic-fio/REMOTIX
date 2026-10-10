/*
 * 04-b25-tastiera.c — THE KEYBOARD BENCH (phase 4, link A5).
 *
 * ⛔ Written BEFORE the code it tests, and CERTIFIED before being believed
 *    (`CODER.md` §3.3 and §3.4): `04-b25-lancia.sh` also points it at
 *    FOUR implementations wrong on purpose (`04-b25-guasti.c`) and
 *    DEMANDS that it says ROSSO on each, and ON THE RIGHT TEST.  A bench that has never seen the defect is not
 *    a test.
 *
 * ---------------------------------------------------------------------------
 * ⭐ WHAT IT TESTS, and why neither QUIC nor `libei` is needed (`CODER.md` §3.6)
 *
 * The module `src/tastiera.c` answers ONE question: «to make this
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
 * THE TESTS, and each is a thesis of `PIANO.md` lines 630-632 to refute
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
 *   6. ⛔ a layout that does not exist: `tastiera_apri` MUST fail and
 *      say so.  If it fell back to `us` silently, the symptom for the user
 *      would be «it types the wrong letters» and nobody would connect the two
 *      things (`CODER.md` §4.2).
 *
 * ---------------------------------------------------------------------------
 * HOW TO READ THE OUTCOME
 *
 *   exit 0 = VERDE, 1 = ROSSO, 2 = the bench itself could not measure
 *   (which is NOT green: it is «I could not look»).
 *   The lines also go to JSONL, to recheck without rerunning.
 */
#include "../src/tastiera.h"

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
static int quante_prove, quante_rosse;

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

static void esito(const char *prova, int verde, const char *dettaglio)
{
	quante_prove++;
	if (!verde)
		quante_rosse++;
	printf("  %s  %-46s  %s\n", verde ? "✅" : "⛔ ROSSO", prova, dettaglio);
	fprintf(jsonl, "{\"prova\":");
	jstr(prova);
	fprintf(jsonl, ",\"esito\":\"%s\",\"dettaglio\":", verde ? "verde" : "rosso");
	jstr(dettaglio);
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
	char nome[128];
} Simulatore;

static void sim_zitto(struct xkb_context *c, enum xkb_log_level l, const char *f, va_list a)
{
	(void)c;
	(void)l;
	(void)f;
	(void)a;
}

static int sim_apri(Simulatore *s, const char *disposizione)
{
	char layout[64] = {0}, variante[64] = {0};
	const char *par;
	struct xkb_rule_names nomi;

	memset(s, 0, sizeof *s);
	par = strchr(disposizione, '(');
	if (par)
	{
		size_t n = (size_t)(par - disposizione);
		if (n >= sizeof layout)
			return 0;
		memcpy(layout, disposizione, n);
		snprintf(variante, sizeof variante, "%s", par + 1);
		char *chiusa = strchr(variante, ')');
		if (chiusa)
			*chiusa = 0;
	}
	else
		snprintf(layout, sizeof layout, "%s", disposizione);

	s->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!s->ctx)
		return 0;
	xkb_context_set_log_fn(s->ctx, sim_zitto);

	nomi.rules = "evdev";
	nomi.model = "pc105";
	nomi.layout = layout;
	nomi.variant = variante;
	nomi.options = "";
	s->km = xkb_keymap_new_from_names(s->ctx, &nomi, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!s->km)
	{
		xkb_context_unref(s->ctx);
		s->ctx = NULL;
		return 0;
	}
	snprintf(s->nome, sizeof s->nome, "%s", xkb_keymap_layout_get_name(s->km, 0));
	return 1;
}

static void sim_chiudi(Simulatore *s)
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
 *   `LEZIONI.md` §4, and here seeing it costs two lines.
 */
static uint32_t sim_batti(Simulatore *s, const uint16_t *codici, size_t n, int *stato_sporco)
{
	struct xkb_state *st = xkb_state_new(s->km);
	uint32_t fuori;
	size_t i;

	*stato_sporco = 0;
	if (!st || n == 0)
	{
		if (st)
			xkb_state_unref(st);
		return 0;
	}
	for (i = 0; i + 1 < n; i++)
		xkb_state_update_key(st, XKB_DA_EVDEV(codici[i]), XKB_KEY_DOWN);

	fuori = xkb_state_key_get_utf32(st, XKB_DA_EVDEV(codici[n - 1]));

	/* the real key: down and up */
	xkb_state_update_key(st, XKB_DA_EVDEV(codici[n - 1]), XKB_KEY_DOWN);
	xkb_state_update_key(st, XKB_DA_EVDEV(codici[n - 1]), XKB_KEY_UP);
	for (i = n - 1; i-- > 0;)
		xkb_state_update_key(st, XKB_DA_EVDEV(codici[i]), XKB_KEY_UP);

	if (xkb_state_serialize_mods(st, XKB_STATE_MODS_EFFECTIVE) != 0)
		*stato_sporco = 1;

	xkb_state_unref(st);
	return fuori;
}

/* The readable name of an evdev code, for the report. */
static const char *nome_modificatore(uint16_t evdev)
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

static void descrivi(char *fuori, size_t n, const uint16_t *codici, size_t quanti)
{
	size_t i;
	int scritti = 0;
	fuori[0] = 0;
	for (i = 0; i < quanti; i++)
	{
		const char *nome = nome_modificatore(codici[i]);
		scritti += snprintf(fuori + scritti, (int)n - scritti > 0 ? n - (size_t)scritti : 0,
		                    "%s%u%s%s%s", i ? "+" : "", codici[i], nome ? "(" : "",
		                    nome ? nome : "", nome ? ")" : "");
		if (scritti < 0 || (size_t)scritti >= n)
			break;
	}
}

/* ------------------------------------------------------------------ *
 * ONE TEST
 * ------------------------------------------------------------------ */
typedef enum
{
	ATTESO_PRODUCIBILE,
	ATTESO_NO
} Atteso;

static void prova_carattere(const char *disposizione, uint32_t carattere, Atteso atteso,
                            const char *perche)
{
	Tastiera *t = NULL;
	Simulatore sim;
	char *errore = NULL;
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t n = 0;
	int ret;
	char nome[160], dett[320], simbolo[8], uscito8[8];
	uint32_t uscito;
	int sporco = 0;

	utf8(carattere, simbolo);
	snprintf(nome, sizeof nome, "«%s» (U+%04X) on «%s» %s", simbolo, carattere, disposizione,
	         atteso == ATTESO_PRODUCIBILE ? "⇒ must come out" : "⇒ NOT producible");

	if (!sim_apri(&sim, disposizione))
	{
		esito(nome, 0, "the SIMULATOR did not compile the layout — I could not look");
		return;
	}

	t = tastiera_apri(disposizione, &errore);
	if (!t)
	{
		snprintf(dett, sizeof dett, "tastiera_apri(\"%s\") said NULL: %s", disposizione,
		         errore ? errore : "(no reason)");
		esito(nome, 0, dett);
		free(errore);
		sim_chiudi(&sim);
		return;
	}

	memset(codici, 0, sizeof codici);
	ret = tastiera_posizioni_per(t, carattere, codici, &n);

	if (ret < 0)
	{
		snprintf(dett, sizeof dett, "returned -1 (error) instead of %d",
		         atteso == ATTESO_PRODUCIBILE ? 1 : 0);
		esito(nome, 0, dett);
		goto fine;
	}

	if (atteso == ATTESO_NO)
	{
		if (ret == 0 && n == 0)
		{
			snprintf(dett, sizeof dett,
			         "said NO and sent nothing — it is the case to write in the log");
			esito(nome, 1, dett);
			goto fine;
		}
		/* ⛔ The heart of the test: what would have COME OUT if we had typed? */
		uscito = sim_batti(&sim, codici, n, &sporco);
		utf8(uscito, uscito8);
		{
			char strada[128];
			descrivi(strada, sizeof strada, codici, n);
			snprintf(dett, sizeof dett,
			         "⛔ said YES (%s) and «%s» (U+%04X) would have come out instead of «%s»: "
			         "a DIFFERENT LETTER, which RCP.md §7.3 forbids",
			         strada, uscito8, uscito, simbolo);
		}
		esito(nome, 0, dett);
		goto fine;
	}

	/* expected producible */
	if (ret == 0)
	{
		esito(nome, 0, "⛔ said «not producible» for a character that layout has");
		goto fine;
	}
	if (n == 0 || n > TASTIERA_MAX_POSIZIONI)
	{
		snprintf(dett, sizeof dett, "said YES but with n=%zu positions (the maximum is %d)", n,
		         TASTIERA_MAX_POSIZIONI);
		esito(nome, 0, dett);
		goto fine;
	}

	uscito = sim_batti(&sim, codici, n, &sporco);
	utf8(uscito, uscito8);
	{
		char strada[128];
		descrivi(strada, sizeof strada, codici, n);
		if (uscito == carattere && !sporco)
			snprintf(dett, sizeof dett, "typing %s gives «%s» — the route is %s%s", strada,
			         uscito8, n > 1 ? "with modifier" : "direct",
			         perche ? perche : "");
		else if (sporco)
			snprintf(dett, sizeof dett,
			         "⛔ «%s» comes out but the sequence %s LEAVES A MODIFIER PRESSED", uscito8,
			         strada);
		else
			snprintf(dett, sizeof dett, "⛔ typing %s gives «%s» (U+%04X), not «%s» (U+%04X)",
			         strada, uscito8, uscito, simbolo, carattere);
		esito(nome, uscito == carattere && !sporco, dett);
	}

fine:
	free(errore);
	tastiera_chiudi(t);
	sim_chiudi(&sim);
}

/* ------------------------------------------------------------------ *
 * THE TOOL'S CONTROLS — they are done FIRST, and if they fail the exit is 2
 * ------------------------------------------------------------------ */
static int controlli_dello_strumento(void)
{
	Simulatore sim;
	uint16_t solo_a[1] = {30};      /* KEY_A */
	uint16_t solo_ac11[1] = {26};   /* KEY_LEFTBRACE: on `it` it is the «e` » */
	uint16_t con_maiusc[2] = {42, 26};
	uint32_t c;
	int sporco;
	char b[8];
	int ok = 1;

	printf("\n  — THE TOOL'S CONTROLS (without these, «nothing came out» and «I could not\n"
	       "    look» look the same — CODER.md §3.10)\n");

	if (!sim_apri(&sim, "it"))
	{
		esito("positive control: the simulator compiles «it»", 0,
		      "no — the bench cannot measure anything");
		return 0;
	}

	c = sim_batti(&sim, solo_a, 1, &sporco);
	esito("⭐ positive: the simulator sees a letter that surely COMES OUT",
	      c == 'a' && !sporco,
	      c == 'a' ? "typed key 30 on «it», «a» came out" : "typed key 30, an «a» did NOT come out");
	ok = ok && (c == 'a');

	c = sim_batti(&sim, solo_ac11, 1, &sporco);
	utf8(c, b);
	{
		char d[128];
		snprintf(d, sizeof d, "key 26 without Shift ⇒ «%s» (U+%04X), and it is NOT the accented «e'»", b, c);
		esito("⭐ negative: the simulator DISTINGUISHES the levels", c == 0x00E8, d);
	}
	ok = ok && (c == 0x00E8);

	c = sim_batti(&sim, con_maiusc, 2, &sporco);
	utf8(c, b);
	{
		char d[160];
		snprintf(d, sizeof d, "Shift+26 ⇒ «%s» (U+%04X): the simulator APPLIES the modifiers", b, c);
		esito("⭐ the simulator applies the modifiers", c == 0x00E9 && !sporco, d);
	}
	ok = ok && (c == 0x00E9);

	sim_chiudi(&sim);
	return ok;
}

/* ------------------------------------------------------------------ *
 * ⛔ THE TRAP: the silent fallback to `us`
 * ------------------------------------------------------------------ */
static void prova_ripiego_silenzioso(void)
{
	static const char *inesistenti[] = {"zz_non_esiste", "it(variante_che_non_esiste)"};
	size_t i;

	for (i = 0; i < sizeof inesistenti / sizeof *inesistenti; i++)
	{
		char *errore = NULL;
		char nome[160], dett[320];
		Tastiera *t;

		snprintf(nome, sizeof nome, "⛔ «%s» does not load ⇒ MUST fail and SAY SO", inesistenti[i]);
		t = tastiera_apri(inesistenti[i], &errore);
		if (!t)
		{
			if (errore && *errore)
			{
				snprintf(dett, sizeof dett, "NULL, with the reason: «%s»", errore);
				esito(nome, 1, dett);
			}
			else
				esito(nome, 0, "NULL but WITHOUT a reason: whoever reads the log does not know why");
			free(errore);
			continue;
		}

		/* It returned a keyboard.  Did it fall back?  Ask the `e'`. */
		{
			uint16_t codici[TASTIERA_MAX_POSIZIONI];
			size_t n = 0;
			int r = tastiera_posizioni_per(t, 'a', codici, &n);
			snprintf(dett, sizeof dett,
			         "⛔ SILENT FALLBACK: it returned a keyboard («%s») for a layout "
			         "that does not exist%s. The symptom for the user is «it types the wrong letters», and "
			         "nobody connects the two things (CODER.md §4.2)",
			         tastiera_disposizione(t) ? tastiera_disposizione(t) : "(no name)",
			         r == 1 ? " — and it even types" : "");
			esito(nome, 0, dett);
		}
		free(errore);
		tastiera_chiudi(t);
	}
}

/*
 * ⚠ And the other side: two different layouts must PRODUCE TWO DIFFERENT
 *   NAMES.  If `tastiera_disposizione()` said the same thing for `it` and
 *   for `us`, a fallback would not even show in the log.
 */
static void prova_nomi_distinti(void)
{
	Tastiera *a = tastiera_apri("it", NULL);
	Tastiera *b = tastiera_apri("us", NULL);
	char dett[320];

	if (!a || !b)
	{
		esito("the names of the two layouts are distinguishable", 0,
		      "one of the two did not open: the test could not be done");
		tastiera_chiudi(a);
		tastiera_chiudi(b);
		return;
	}
	snprintf(dett, sizeof dett, "«%s» contro «%s»",
	         tastiera_disposizione(a) ? tastiera_disposizione(a) : "(NULL)",
	         tastiera_disposizione(b) ? tastiera_disposizione(b) : "(NULL)");
	esito("⭐ the names of the two layouts are DISTINGUISHABLE",
	      tastiera_disposizione(a) && tastiera_disposizione(b) &&
	          strcmp(tastiera_disposizione(a), tastiera_disposizione(b)) != 0,
	      dett);
	tastiera_chiudi(a);
	tastiera_chiudi(b);
}

/* The inputs the protocol forbids (`RCP.md` §7.3): out of range and
 * surrogates.  They are not «not producible»: they are an error. */
static void prova_ingressi_illegali(void)
{
	Tastiera *t = tastiera_apri("it", NULL);
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t n = 1;
	char dett[160];
	int r1, r2;

	if (!t)
	{
		esito("illegal inputs are distinguished from «not producible»", 0,
		      "«it» did not open");
		return;
	}
	r1 = tastiera_posizioni_per(t, 0xD800, codici, &n);
	r2 = tastiera_posizioni_per(t, 0x110000, codici, &n);
	snprintf(dett, sizeof dett, "surrogate ⇒ %d, out of range ⇒ %d (expected -1 and -1)", r1, r2);
	esito("illegal inputs are NOT confused with «not producible»", r1 == -1 && r2 == -1,
	      dett);
	tastiera_chiudi(t);
}

/* ------------------------------------------------------------------ *
 * ⛔⛔ THE TEST FOR WHICH THE CONTRACT CHANGED
 *
 * `tastiera_apri()` compiles the layout FROM THE NAME the client
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
static char *testo_della_disposizione(const char *disposizione)
{
	Simulatore s;
	char *testo;

	if (!sim_apri(&s, disposizione))
		return NULL;
	testo = xkb_keymap_get_as_string(s.km, XKB_KEYMAP_FORMAT_TEXT_V1);
	sim_chiudi(&s);
	return testo;
}

static void prova_keymap_della_sessione(const char *della_sessione, const char *negoziata,
                                        uint32_t carattere, Atteso atteso)
{
	char *testo = testo_della_disposizione(della_sessione);
	Simulatore sim;
	Tastiera *t = NULL;
	char *errore = NULL;
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t n = 0;
	int ret, sporco = 0;
	char nome[256], dett[448], simbolo[8], uscito8[8], strada[128];
	uint32_t uscito;

	utf8(carattere, simbolo);
	snprintf(nome, sizeof nome, "session «%s» + negotiated «%s», «%s» (U+%04X) %s",
	         della_sessione, negoziata ? negoziata : "(none)", simbolo, carattere,
	         atteso == ATTESO_PRODUCIBILE ? "⇒ must come out" : "⇒ NOT producible");

	if (!testo || !sim_apri(&sim, della_sessione))
	{
		esito(nome, 0, "I could not build the session's layout: I DID NOT MEASURE");
		free(testo);
		return;
	}

	t = tastiera_apri_da_keymap(testo, strlen(testo), negoziata, &errore);
	if (!t)
	{
		snprintf(dett, sizeof dett, "the session's keymap did not open: %s",
		         errore ? errore : "(no reason)");
		esito(nome, 0, dett);
		goto fine;
	}

	memset(codici, 0, sizeof codici);
	ret = tastiera_posizioni_per(t, carattere, codici, &n);

	if (atteso == ATTESO_NO)
	{
		if (ret == 0 && n == 0)
			esito(nome, 1, "said NO and sent nothing");
		else
		{
			uscito = sim_batti(&sim, codici, n, &sporco);
			utf8(uscito, uscito8);
			descrivi(strada, sizeof strada, codici, n);
			snprintf(dett, sizeof dett, "⛔ said YES (%s): «%s» would appear", strada, uscito8);
			esito(nome, 0, dett);
		}
		goto fine;
	}

	if (ret != 1 || n == 0)
	{
		snprintf(dett, sizeof dett,
		         "⛔ said «not producible» (%d) for a character THE SESSION has: it "
		         "trusted the negotiated name instead of the real layout",
		         ret);
		esito(nome, 0, dett);
		goto fine;
	}

	uscito = sim_batti(&sim, codici, n, &sporco);
	utf8(uscito, uscito8);
	descrivi(strada, sizeof strada, codici, n);
	if (uscito == carattere && !sporco)
		snprintf(dett, sizeof dett, "typing %s on THE SESSION'S layout gives «%s»",
		         strada, uscito8);
	else
		snprintf(dett, sizeof dett,
		         "⛔ typing %s on THE SESSION'S layout gives «%s» (U+%04X), not «%s»: "
		         "A DIFFERENT LETTER",
		         strada, uscito8, uscito, simbolo);
	esito(nome, uscito == carattere && !sporco, dett);

fine:
	free(errore);
	tastiera_chiudi(t);
	sim_chiudi(&sim);
	free(testo);
}

/*
 * ⛔ And it can be called SEVERAL TIMES: `STUDI.md` §gnome §9 says that a keymap change
 *    destroys and recreates the keyboard device, and `input.c` reopens at every
 *    `DEVICE_ADDED`.  ⇒ Two openings alive together must neither lose nor
 *    double anything: `it` is opened, `us` is opened, and **the first one is
 *    asked again**, and it must answer as before.
 */
static void prova_riaperture(void)
{
	char *ti = testo_della_disposizione("it");
	char *tu = testo_della_disposizione("us");
	Tastiera *a = NULL, *b = NULL;
	uint16_t ca[TASTIERA_MAX_POSIZIONI], cb[TASTIERA_MAX_POSIZIONI];
	size_t na = 0, nb = 0, na2 = 0;
	uint16_t ca2[TASTIERA_MAX_POSIZIONI];
	char dett[320];
	int r1, r2, r3;

	if (!ti || !tu)
	{
		esito("⭐ it can be reopened several times without losing anything", 0, "I DID NOT MEASURE");
		goto fine;
	}
	a = tastiera_apri_da_keymap(ti, strlen(ti), NULL, NULL);
	r1 = a ? tastiera_posizioni_per(a, 0x00E9, ca, &na) : -1; /* é on it */

	b = tastiera_apri_da_keymap(tu, strlen(tu), NULL, NULL);
	r2 = b ? tastiera_posizioni_per(b, 0x00E9, cb, &nb) : -1; /* é on us */

	/* ⛔ and now the FIRST one again, which is still alive */
	r3 = a ? tastiera_posizioni_per(a, 0x00E9, ca2, &na2) : -1;

	snprintf(dett, sizeof dett,
	         "it⇒%d (%zu pos.), then us⇒%d (%zu pos.), then AGAIN it⇒%d (%zu pos.)", r1, na, r2, nb,
	         r3, na2);
	esito("⭐ two layouts alive together do not get mixed up",
	      r1 == 1 && r2 == 0 && r3 == 1 && na == na2 && na > 0 &&
	          memcmp(ca, ca2, na * sizeof *ca) == 0,
	      dett);

fine:
	tastiera_chiudi(a);
	tastiera_chiudi(b);
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
static void prova_dichiarazione(const char *della_sessione, const char *negoziata,
                                int deve_dichiarare)
{
	char *testo = testo_della_disposizione(della_sessione);
	char nome[256], dett[384], riga[4096];
	int salvato = -1, tmp = -1;
	FILE *f = NULL;
	Tastiera *t = NULL;
	long letti = 0;
	int dichiarato = 0;
	char modello[] = "/tmp/04-b25-reg-XXXXXX";

	snprintf(nome, sizeof nome, "the log: session «%s» + negotiated «%s» ⇒ %s",
	         della_sessione, negoziata ? negoziata : "(none)",
	         deve_dichiarare ? "MUST declare the fallback" : "must NOT cry fallback");

	if (!testo)
	{
		esito(nome, 0, "I did not build the layout: I DID NOT MEASURE");
		return;
	}

	tmp = mkstemp(modello);
	if (tmp < 0)
	{
		esito(nome, 0, "I could not redirect the log: I DID NOT MEASURE");
		free(testo);
		return;
	}
	fflush(stderr);
	salvato = dup(STDERR_FILENO);
	dup2(tmp, STDERR_FILENO);

	t = tastiera_apri_da_keymap(testo, strlen(testo), negoziata, NULL);

	fflush(stderr);
	dup2(salvato, STDERR_FILENO);
	close(salvato);

	f = fdopen(tmp, "r");
	if (f)
	{
		rewind(f);
		while (fgets(riga, sizeof riga, f))
		{
			letti++;
			if (strstr(riga, "DECLARED FALLBACK"))
				dichiarato = 1;
		}
		fclose(f);
	}
	unlink(modello);

	/*
	 * ⛔ The TOOL's positive control: if I had read no line
	 *    at all, «it did not declare» and «I could not read the log»
	 *    would look the same (`CODER.md` §3.10).
	 */
	if (letti == 0)
	{
		esito(nome, 0, "⛔ I read NO log line at all: I cannot tell "
		               "silence from not having looked");
		goto fine;
	}

	snprintf(dett, sizeof dett, "%ld log lines, «DECLARED FALLBACK» %s", letti,
	         dichiarato ? "present" : "absent");
	esito(nome, dichiarato == deve_dichiarare, dett);

fine:
	tastiera_chiudi(t);
	free(testo);
}

/* ------------------------------------------------------------------ *
 * main
 * ------------------------------------------------------------------ */
int main(int argc, char **argv)
{
	const char *dove = argc > 1 ? argv[1] : "banchi/04-b25-esiti.jsonl";

	jsonl = fopen(dove, "w");
	if (!jsonl)
	{
		fprintf(stderr, "⛔ I cannot write %s\n", dove);
		return 2;
	}

	printf("\n== BENCH 04-b25 — THE KEYBOARD: from the letter to the hammer\n");
	printf("   the yardstick is THE CHARACTER THAT COMES OUT of an independent `xkb_state`,\n"
	       "   not the code the module says it chose.\n");

	if (!controlli_dello_strumento())
	{
		printf("\n⛔ THE TOOL IS NOT CERTIFIED: I measure nothing.\n");
		fclose(jsonl);
		return 2;
	}

	printf("\n  — THE LETTERS (PIANO.md lines 630-632)\n");
	prova_carattere("it", 0x00E9, ATTESO_PRODUCIBILE, "");  /* é */
	prova_carattere("us", 0x00E9, ATTESO_NO, "");           /* ⛔ the test that weighs the most */
	prova_carattere("it", 0x00E8, ATTESO_PRODUCIBILE, "");  /* è, without modifier */
	prova_carattere("it", 'a', ATTESO_PRODUCIBILE, "");     /* positive control on the module */
	prova_carattere("us", 'A', ATTESO_PRODUCIBILE, "");     /* Shift MAKES the letter */

	printf("\n  — THE SAME CHARACTER, TWO ROUTES (SPECIFICHE.md §7.3: Shift and AltGr\n"
	       "    are not commands, they serve to MAKE the letter)\n");
	prova_carattere("it", '@', ATTESO_PRODUCIBILE, "");     /* AltGr */
	prova_carattere("us", '@', ATTESO_PRODUCIBILE, "");     /* Shift */

	printf("\n  — WHAT CANNOT BE TYPED IS DECLARED, NOT FALSIFIED\n");
	prova_carattere("it", 0x1F600, ATTESO_NO, "");          /* 😀 */
	prova_carattere("us", 0x1F600, ATTESO_NO, "");
	prova_carattere("it", 0x4E2D, ATTESO_NO, "");           /* 中 */

	printf("\n  — ⛔ THE TRAP: THE SILENT FALLBACK\n");
	prova_ripiego_silenzioso();
	prova_nomi_distinti();

	printf("\n  — THE INPUTS THE PROTOCOL FORBIDS\n");
	prova_ingressi_illegali();

	printf("\n  — ⛔⛔ THE LAYOUT IS HANDED OVER BY THE SESSION, NOT CHOSEN BY THE NAME\n"
	       "    (the case for which the contract changed: session «it», client «us»)\n");
	/* ⛔ THE CASE: the `[` — on `us` it is bare key 26, on `it` that key holds the «è». */
	prova_keymap_della_sessione("it", "us", '[', ATTESO_PRODUCIBILE);
	/* and the twin: a character the session does NOT have, however much the client asks for it */
	prova_keymap_della_sessione("us", "it", 0x00E9, ATTESO_NO);
	/* the positive controls: when they match, everything as before */
	prova_keymap_della_sessione("it", "it", 0x00E9, ATTESO_PRODUCIBILE);
	prova_keymap_della_sessione("it", NULL, '[', ATTESO_PRODUCIBILE);
	prova_riaperture();

	printf("\n  — ⛔ AND THE LOG LINE, IN BOTH DIRECTIONS\n");
	prova_dichiarazione("it", "us", 1);  /* they do not match ⇒ it is declared */
	prova_dichiarazione("it", "it", 0);  /* ⛔ they match ⇒ NO crying out */
	prova_dichiarazione("us", "us", 0);
	prova_dichiarazione("it", NULL, 0);  /* none negotiated: nothing to compare */

	printf("\n== %d tests, %d RED  ⇒  %s\n\n", quante_prove, quante_rosse,
	       quante_rosse ? "⛔ ROSSO" : "✅ VERDE");
	fprintf(jsonl, "{\"totale\":%d,\"rosse\":%d,\"esito\":\"%s\"}\n", quante_prove, quante_rosse,
	        quante_rosse ? "rosso" : "verde");
	fclose(jsonl);
	return quante_rosse ? 1 : 0;
}
