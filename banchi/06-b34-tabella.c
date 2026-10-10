/*
 * 06-b34-tabella.c — ⛔ THE EXPECTED RESULT IS DECLARED FIRST, AND THE CODE COMPUTES IT.
 *
 * Sub-phase 6.2, *the keyboard that is reborn*.
 *
 * `CODER.md` §3.3 wants the expected result declared before the measurement, and §3.6
 * says how to get it at the lowest price: **isolate ONE function and call it from
 * outside**, instead of doing another bench round.
 *
 * Here `tastiera.c` — the same file that runs in the product — is asked which
 * evdev position produces each test character in each layout.
 * ⇒ The table that comes out **is the expected result** of bench `06-b34`, and it
 *   is not my opinion: it is what the product will do.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ WHY `it` → `us` IS NOT ENOUGH, AND `de` IS NEEDED TOO
 *
 * The brief said *«for example `it` → `us`, where `z`/`y` and the accented letters
 * move»*.  ⛔ **The first half is false**: `it` and `us` are **both
 * QWERTY**, and `z` is on key 44 in both.  The `z`/`y` swap belongs to
 * **`de`** (QWERTZ).  Whoever tested `it` → `us` with the `z` would measure two
 * layouts that on that character **are the same**, and a bench that does not
 * discriminate is not a bench.
 *
 * ⇒ The tests serve two different purposes, and must be kept separate:
 *
 *   `it` → `us`   discriminates on the **accented letters** and the **symbols**: `è`
 *                 exists on `it` and **does not exist at all** on `us`; the `@` is
 *                 AltGr+ò on `it` and Shift+2 on `us`.  ⚠ A character that vanishes
 *                 and one that moves: two different forms of fault;
 *
 *   `it` → `de`   discriminates on the **`z`**, and it is the NASTIER test of the
 *                 two — the only one in which the wrong character **exists**.  With
 *                 the old keymap key 44 is sent, which on `de` produces a
 *                 **`y`**: ⛔ not a missing character, **A DIFFERENT
 *                 CHARACTER**, which `RCP.md` §7.3 forbids and which nobody
 *                 would ever connect to the layout.
 *
 *   build:      cc -O2 -o 06-b34-tabella 06-b34-tabella.c ../src/tastiera.c \
 *                  ../src/registro.c $(pkg-config --cflags --libs xkbcommon glib-2.0)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../src/tastiera.h"

/* ⛔ The test characters, and next to each its reason: a test without
 *    its reason is a test the next person will remove because «it is not needed». */
static const struct
{
	unsigned cp;
	const char *utf8;
	const char *perche;
} PROVE[] = {
	{0x0061, "a", "⭐ THE CANARY: it is on key 30 in all three. If it does NOT arrive, "
	              "the test is not red: it is INVALID (the focus is not on the witness)"},
	{0x007A, "z", "⛔ the nasty test: 44 on it/us, 21 on de — with the old keymap "
	              "on de a «y» comes out, that is a DIFFERENT character"},
	{0x0079, "y", "the twin of the z"},
	{0x00E8, "e-grave", "⛔ exists on it, does NOT exist on us: here the fault is an ABSENCE"},
	{0x0040, "at-sign", "moves: AltGr+ò on it, Shift+2 on us"},
	{0x00F2, "o-grave", "like the è: only on it"},
	{0x005C, "backslash", "a symbol that moves among all three"},
	{0, NULL, NULL},
};

static const char *DISPOSIZIONI[] = {"it", "us", "de", "de(neo)", NULL};

/* ⛔⭐ AND SINCE 21 AUGUST 2026 THE PROGRAM ANSWERS A SECOND QUESTION, which
 *     is the one the A3 brief insists on:
 *
 *       «WHICH LAYOUTS DOES THIS MACHINE REALLY HAVE?»
 *
 * ⛔ The source of truth is not a hand-written list — neither mine nor the one
 *    in `rcp.c` — but the system: `xkeyboard-config` under `libxkbcommon`.  Here
 *    the question is passed to `src/tastiera.c`, which is the same file that in
 *    the product answers the `disposizione_esiste` hook (`webtransport.c:1626`).
 *    ⇒ What comes out of here **is what the product will answer**, and it is not
 *      my opinion.
 *
 *   `06-b34-tabella elenco < <list of names>`   one line per name, «SI»/«NO»
 *
 * ⚠ It serves two different purposes, and they must be kept separate:
 *    · building the expected result of case 7 (the exotic layouts);
 *    · sweeping all 99 layouts and 341 variants that
 *      `/usr/share/X11/xkb/rules/evdev.lst` declares, to find those the
 *      system HAS and that the **shape check** of `rcp.c` would throw away
 *      before even asking.  ⛔ That is the D1 form that survived the
 *      cure of 16 August: the cure took the question to XKB, but in front of the
 *      hook a second hand-written list remained — the alphabet allowed
 *      in the name.
 */
static int elenco(void)
{
	char riga[256];

	while (fgets(riga, sizeof riga, stdin))
	{
		char *fine = riga + strlen(riga);
		char *sbaglio = NULL;
		Tastiera *t;

		while (fine > riga && (fine[-1] == '\n' || fine[-1] == '\r' || fine[-1] == ' '))
			*--fine = 0;
		if (!riga[0] || riga[0] == '#')
			continue;

		t = tastiera_apri(riga, &sbaglio);
		if (t)
		{
			printf("SI  %-32s %s\n", riga, tastiera_disposizione(t));
			tastiera_chiudi(t);
		}
		else
		{
			printf("NO  %-32s %s\n", riga, sbaglio ? sbaglio : "no reason given");
		}
		free(sbaglio);
		fflush(stdout);
	}
	return 0;
}

/* ⛔ The tests of CASE 7 — «does an exotic layout produce the right
 *    character?».  ⚠ The canary is NOT always the `a`: on `gr` key 30 makes an
 *    `α`, and a canary that does not exist in the layout would turn every
 *    test into «INVALID» through the bench's fault.  ⇒ The canary of each
 *    layout is chosen by this program, by asking the layout. */
static const struct
{
	const char *disp;
	unsigned cp;
	const char *nome;
	const char *perche;
} ESOTICHE[] = {
	{"hu", 0x0171, "u-double-acute (ű)", "⛔ hu: was REJECTED by the fixed list. Does not exist on it/us/de"},
	{"hu", 0x0151, "o-double-acute (ő)", "the twin of the ű"},
	{"hu", 0x007A, "z", "⛔ hu is QWERTZ like de: the z moves relative to it"},
	{"tr", 0x0131, "dotless-i (ı)", "⛔ tr: was REJECTED. The most Turkish character there is"},
	{"tr", 0x011F, "g-breve (ğ)", "the twin of the ı"},
	{"gr", 0x03B1, "alpha (α)", "⛔ gr: was REJECTED, and it is not even Latin"},
	{"ua", 0x0457, "Ukrainian yi (ї)", "⛔ ua: was REJECTED. Cyrillic, and different from Russian"},
	{"it", 0x0171, "u-double-acute (ű)", "⭐ THE NEGATIVE CONTROL: on it it must NOT exist"},
	{"it", 0x0131, "dotless-i (ı)", "⭐ the negative control of the ı"},
	{NULL, 0, NULL, NULL},
};

/* The canary candidates, in order: the first one the layout can produce. */
static const unsigned CANARINI[] = {0x0061, 0x0031, 0x0020, 0};

static int esotiche(void)
{
	printf("# 06-b34 case 7 — the expected result of the EXOTIC layouts\n");
	printf("# computed by `src/tastiera.c`, that is by the product (CODER.md §3.3 and §3.6)\n\n");
	for (int i = 0; ESOTICHE[i].disp; i++)
	{
		char *sbaglio = NULL;
		Tastiera *t = tastiera_apri(ESOTICHE[i].disp, &sbaglio);
		uint16_t codici[TASTIERA_MAX_POSIZIONI];
		size_t n = 0;
		int esito;

		if (!t)
		{
			printf("%-4s U+%04X %-20s ⛔ LAYOUT NOT OPENED: %s\n",
			       ESOTICHE[i].disp, ESOTICHE[i].cp, ESOTICHE[i].nome,
			       sbaglio ? sbaglio : "no reason given");
			free(sbaglio);
			continue;
		}
		esito = tastiera_posizioni_per(t, ESOTICHE[i].cp, codici, &n);
		printf("%-4s U+%04X %-20s ", ESOTICHE[i].disp, ESOTICHE[i].cp,
		       ESOTICHE[i].nome);
		if (esito != 1 || n == 0)
			printf("-        ");
		else
		{
			char buf[64];
			int p = 0;
			for (size_t k = 0; k < n; k++)
				p += snprintf(buf + p, sizeof buf - (size_t)p, "%s%u", k ? "+" : "",
				              (unsigned) codici[k]);
			printf("%-9s", buf);
		}
		/* ⛔ And the canary is chosen HERE, by asking: a canary that the
		 *    layout cannot produce would make every test INVALID. */
		{
			unsigned can = 0;
			for (int c = 0; CANARINI[c]; c++)
			{
				size_t m = 0;
				if (tastiera_posizioni_per(t, CANARINI[c], codici, &m) == 1 && m)
				{
					can = CANARINI[c];
					break;
				}
			}
			if (can)
				printf(" canary=U+%04X", can);
			else
				printf(" ⛔ NO CANARY");
		}
		printf("   %s\n", ESOTICHE[i].perche);
		tastiera_chiudi(t);
	}
	return 0;
}

/* ⛔ `posizione <layout> <U+xxxx> …` — the plain question, to build
 *    the expected result of a new test without recompiling anything.  ⚠ It serves to
 *    CHOOSE the character that discriminates: between `de` and `de(T3)` most
 *    characters are the same, and a test on a common character
 *    would be green even with the variant thrown away. */
static int posizione(int argc, char **argv)
{
	char *sbaglio = NULL;
	Tastiera *t = tastiera_apri(argv[2], &sbaglio);

	if (!t)
	{
		printf("⛔ %s NOT OPENED: %s\n", argv[2], sbaglio ? sbaglio : "no reason given");
		free(sbaglio);
		return 1;
	}
	printf("# %s (%s)\n", argv[2], tastiera_disposizione(t));
	for (int i = 3; i < argc; i++)
	{
		uint16_t codici[TASTIERA_MAX_POSIZIONI];
		size_t n = 0;
		unsigned cp = (unsigned) strtoul(argv[i], NULL, 16);
		int esito = tastiera_posizioni_per(t, cp, codici, &n);

		printf("U+%04X  ", cp);
		if (esito != 1 || n == 0)
			printf("-\n");
		else
		{
			for (size_t k = 0; k < n; k++)
				printf("%s%u", k ? "+" : "", (unsigned) codici[k]);
			printf("\n");
		}
	}
	tastiera_chiudi(t);
	return 0;
}

int main(int argc, char **argv)
{
	if (argc > 1 && strcmp(argv[1], "elenco") == 0)
		return elenco();
	if (argc > 1 && strcmp(argv[1], "esotiche") == 0)
		return esotiche();
	if (argc > 3 && strcmp(argv[1], "posizione") == 0)
		return posizione(argc, argv);

	printf("# 06-b34 — the expected result, computed by `src/tastiera.c` (CODER.md §3.3)\n");
	printf("# position = the EVDEV codes the product would send, in order\n");
	printf("# «-» = NOT producible: RCP.md §7.3 requires sending NOTHING\n\n");

	for (int d = 0; DISPOSIZIONI[d]; d++)
	{
		char *sbaglio = NULL;
		Tastiera *t = tastiera_apri(DISPOSIZIONI[d], &sbaglio);

		if (!t)
		{
			printf("LAYOUT %-9s ⛔ NOT OPENED: %s\n", DISPOSIZIONI[d],
			       sbaglio ? sbaglio : "no reason given");
			free(sbaglio);
			continue;
		}
		printf("LAYOUT %-9s (%s)\n", DISPOSIZIONI[d], tastiera_disposizione(t));
		for (int i = 0; PROVE[i].utf8; i++)
		{
			uint16_t codici[TASTIERA_MAX_POSIZIONI];
			size_t n = 0;
			int esito = tastiera_posizioni_per(t, PROVE[i].cp, codici, &n);

			printf("    U+%04X %-12s ", PROVE[i].cp, PROVE[i].utf8);
			if (esito != 1 || n == 0)
				printf("-\n");
			else
			{
				for (size_t k = 0; k < n; k++)
					printf("%s%u", k ? "+" : "", (unsigned) codici[k]);
				printf("\n");
			}
		}
		printf("\n");
		tastiera_chiudi(t);
	}

	printf("# the reasons for the tests\n");
	for (int i = 0; PROVE[i].utf8; i++)
		printf("#   %-12s %s\n", PROVE[i].utf8, PROVE[i].perche);
	return 0;
}
