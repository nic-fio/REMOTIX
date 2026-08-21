/*
 * 06-b34-tabella.c — ⛔ L'ATTESO SI DICHIARA PRIMA, E LO CALCOLA IL CODICE.
 *
 * Sottofase 6.2, *la tastiera che rinasce*.
 *
 * `CODER.md` §3.3 vuole l'atteso dichiarato prima della misura, e §3.6 dice
 * come ottenerlo al prezzo piu' basso: **si isola UNA funzione e la si chiama
 * da fuori**, invece di fare un altro giro di banco.
 *
 * Qui si chiede a `tastiera.c` — lo stesso file che gira nel prodotto — quale
 * posizione evdev produce ciascun carattere di prova in ciascuna disposizione.
 * ⇒ La tabella che ne esce **e' l'atteso** del banco `06-b34`, e non e' una
 *   mia opinione: e' quel che il prodotto fara'.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ PERCHE' `it` → `us` NON BASTA, E CI VUOLE ANCHE `de`
 *
 * Il mandato diceva *«per esempio `it` → `us`, dove `z`/`y` e le accentate si
 * spostano»*.  ⛔ **La prima meta' e' falsa**: `it` e `us` sono **tutt'e due
 * QWERTY**, e `z` sta sul tasto 44 in tutte e due.  Lo scambio `z`/`y` e' di
 * **`de`** (QWERTZ).  Chi provasse `it` → `us` con la `z` misurerebbe due
 * disposizioni che su quel carattere **sono la stessa**, e un banco che non
 * distingue non e' un banco.
 *
 * ⇒ Le prove servono a due cose diverse, e vanno tenute separate:
 *
 *   `it` → `us`   distingue sulle **accentate** e sui **segni**: `è` esiste su
 *                 `it` e **non esiste affatto** su `us`; la `@` e' AltGr+ò su
 *                 `it` e Maiusc+2 su `us`.  ⚠ Un carattere che sparisce e uno
 *                 che si sposta: due forme di guasto diverse;
 *
 *   `it` → `de`   distingue sulla **`z`**, ed e' la prova PIU' CATTIVA delle
 *                 due — l'unica in cui il carattere sbagliato **esiste**.  Con
 *                 la keymap vecchia si manda il tasto 44, che su `de` fa
 *                 uscire una **`y`**: ⛔ non un carattere mancante, **UN
 *                 CARATTERE DIVERSO**, che `RCP.md` §7.3 vieta e che nessuno
 *                 collegherebbe mai alla disposizione.
 *
 *   costruire:  cc -O2 -o 06-b34-tabella 06-b34-tabella.c ../src/tastiera.c \
 *                  ../src/registro.c $(pkg-config --cflags --libs xkbcommon glib-2.0)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../src/tastiera.h"

/* ⛔ I caratteri di prova, e accanto la ragione di ciascuno: una prova senza
 *    la sua ragione e' una prova che il prossimo togliera' perche' «non serve». */
static const struct
{
	unsigned cp;
	const char *utf8;
	const char *perche;
} PROVE[] = {
	{0x0061, "a", "⭐ IL CANARINO: sta sul tasto 30 in tutte e tre. Se NON arriva, "
	              "la prova non e' rossa: e' INVALIDA (il fuoco non e' sul testimone)"},
	{0x007A, "z", "⛔ la prova cattiva: 44 su it/us, 21 su de — con la keymap vecchia "
	              "su de esce una «y», cioe' un carattere DIVERSO"},
	{0x0079, "y", "il gemello della z"},
	{0x00E8, "e-grave", "⛔ esiste su it, NON esiste su us: qui il guasto e' un'ASSENZA"},
	{0x0040, "chiocciola", "si sposta: AltGr+ò su it, Maiusc+2 su us"},
	{0x00F2, "o-grave", "come la è: solo su it"},
	{0x005C, "backslash", "un segno che si sposta fra tutte e tre"},
	{0, NULL, NULL},
};

static const char *DISPOSIZIONI[] = {"it", "us", "de", "de(neo)", NULL};

/* ⛔⭐ E DAL 21 AGOSTO 2026 IL PROGRAMMA RISPONDE A UNA SECONDA DOMANDA, che
 *     e' quella su cui il mandato di A3 insiste:
 *
 *       «QUALI DISPOSIZIONI HA DAVVERO QUESTA MACCHINA?»
 *
 * ⛔ La fonte di verita' non e' un elenco scritto a mano — ne' il mio ne' quello
 *    di `rcp.c` — ma il sistema: `xkeyboard-config` sotto `libxkbcommon`.  Qui
 *    la domanda si gira a `src/tastiera.c`, che e' lo stesso file che nel
 *    prodotto risponde al gancio `disposizione_esiste` (`webtransport.c:1626`).
 *    ⇒ Quel che esce di qui **e' quel che il prodotto rispondera'**, e non e'
 *      una mia opinione.
 *
 *   `06-b34-tabella elenco < <lista di nomi>`   una riga per nome, «SI»/«NO»
 *
 * ⚠ Serve a due cose diverse, e vanno tenute separate:
 *    · a costruire l'atteso del caso 7 (le disposizioni esotiche);
 *    · a spazzare tutte le 99 disposizioni e le 341 varianti che
 *      `/usr/share/X11/xkb/rules/evdev.lst` dichiara, per trovare quelle che il
 *      sistema HA e che il **controllo di forma** di `rcp.c` butterebbe via
 *      prima ancora di chiedere.  ⛔ Quella e' la forma D1 sopravvissuta alla
 *      cura del 16 agosto: la cura ha portato la domanda a XKB, ma davanti al
 *      gancio e' rimasto un secondo elenco scritto a mano — l'alfabeto ammesso
 *      nel nome.
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
			printf("NO  %-32s %s\n", riga, sbaglio ? sbaglio : "senza motivo");
		}
		free(sbaglio);
		fflush(stdout);
	}
	return 0;
}

/* ⛔ Le prove del CASO 7 — «una disposizione esotica produce il carattere
 *    giusto?».  ⚠ Il canarino NON e' sempre la `a`: su `gr` il tasto 30 fa una
 *    `α`, e un canarino che non esiste nella disposizione trasformerebbe ogni
 *    prova in «INVALIDA» per colpa del banco.  ⇒ Il canarino di ciascuna
 *    disposizione lo sceglie questo programma, chiedendolo alla disposizione. */
static const struct
{
	const char *disp;
	unsigned cp;
	const char *nome;
	const char *perche;
} ESOTICHE[] = {
	{"hu", 0x0171, "u-doppioacuto (ű)", "⛔ hu: era RIFIUTATA dall'elenco fisso. Non esiste su it/us/de"},
	{"hu", 0x0151, "o-doppioacuto (ő)", "il gemello della ű"},
	{"hu", 0x007A, "z", "⛔ hu e' QWERTZ come de: la z si sposta rispetto a it"},
	{"tr", 0x0131, "i-senza-punto (ı)", "⛔ tr: era RIFIUTATA. Il carattere piu' turco che c'e'"},
	{"tr", 0x011F, "g-breve (ğ)", "il gemello della ı"},
	{"gr", 0x03B1, "alfa (α)", "⛔ gr: era RIFIUTATA, e non e' nemmeno latina"},
	{"ua", 0x0457, "ji ucraina (ї)", "⛔ ua: era RIFIUTATA. Cirillico, e diverso dal russo"},
	{"it", 0x0171, "u-doppioacuto (ű)", "⭐ IL CONTROLLO NEGATIVO: su it NON deve esistere"},
	{"it", 0x0131, "i-senza-punto (ı)", "⭐ il controllo negativo della ı"},
	{NULL, 0, NULL, NULL},
};

/* I candidati canarino, in ordine: il primo che la disposizione sa produrre. */
static const unsigned CANARINI[] = {0x0061, 0x0031, 0x0020, 0};

static int esotiche(void)
{
	printf("# 06-b34 caso 7 — l'atteso delle disposizioni ESOTICHE\n");
	printf("# calcolato da `src/tastiera.c`, cioe' dal prodotto (CODER.md §3.3 e §3.6)\n\n");
	for (int i = 0; ESOTICHE[i].disp; i++)
	{
		char *sbaglio = NULL;
		Tastiera *t = tastiera_apri(ESOTICHE[i].disp, &sbaglio);
		uint16_t codici[TASTIERA_MAX_POSIZIONI];
		size_t n = 0;
		int esito;

		if (!t)
		{
			printf("%-4s U+%04X %-20s ⛔ DISPOSIZIONE NON APERTA: %s\n",
			       ESOTICHE[i].disp, ESOTICHE[i].cp, ESOTICHE[i].nome,
			       sbaglio ? sbaglio : "senza motivo");
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
		/* ⛔ E il canarino si sceglie QUI, chiedendolo: un canarino che la
		 *    disposizione non sa produrre renderebbe ogni prova INVALIDA. */
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
				printf(" canarino=U+%04X", can);
			else
				printf(" ⛔ NESSUN CANARINO");
		}
		printf("   %s\n", ESOTICHE[i].perche);
		tastiera_chiudi(t);
	}
	return 0;
}

/* ⛔ `posizione <disposizione> <U+xxxx> …` — la domanda secca, per costruire
 *    l'atteso di una prova nuova senza ricompilare niente.  ⚠ Serve a
 *    SCEGLIERE il carattere che discrimina: fra `de` e `de(T3)` la maggior
 *    parte dei caratteri e' la stessa, e una prova su un carattere comune
 *    sarebbe verde anche con la variante buttata via. */
static int posizione(int argc, char **argv)
{
	char *sbaglio = NULL;
	Tastiera *t = tastiera_apri(argv[2], &sbaglio);

	if (!t)
	{
		printf("⛔ %s NON APERTA: %s\n", argv[2], sbaglio ? sbaglio : "senza motivo");
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

	printf("# 06-b34 — l'atteso, calcolato da `src/tastiera.c` (CODER.md §3.3)\n");
	printf("# posizione = i codici EVDEV che il prodotto manderebbe, in ordine\n");
	printf("# «-» = NON producibile: RCP.md §7.3 obbliga a non mandare NIENTE\n\n");

	for (int d = 0; DISPOSIZIONI[d]; d++)
	{
		char *sbaglio = NULL;
		Tastiera *t = tastiera_apri(DISPOSIZIONI[d], &sbaglio);

		if (!t)
		{
			printf("DISPOSIZIONE %-9s ⛔ NON APERTA: %s\n", DISPOSIZIONI[d],
			       sbaglio ? sbaglio : "senza motivo");
			free(sbaglio);
			continue;
		}
		printf("DISPOSIZIONE %-9s (%s)\n", DISPOSIZIONI[d], tastiera_disposizione(t));
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

	printf("# le ragioni delle prove\n");
	for (int i = 0; PROVE[i].utf8; i++)
		printf("#   %-12s %s\n", PROVE[i].utf8, PROVE[i].perche);
	return 0;
}
