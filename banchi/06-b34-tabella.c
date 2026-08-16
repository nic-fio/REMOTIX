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

int main(void)
{
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
