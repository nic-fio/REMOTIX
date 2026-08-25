/* 10-d1-conto.c — ⛔⭐ IL METRO SI TARA PRIMA (`LEZIONI.md` §1.33).
 *
 * ⛔ IL PROBLEMA CHE QUESTO FILE ESISTE PER CHIUDERE.  L'aritmetica del budget
 *    e' scritta **due volte**: in `banchi/10-b99-predittore.py`, che e'
 *    certificato (86 casi, 0 rossi) e da cui vengono i numeri di §6.9, e in
 *    `src/budget.c`, che e' il prodotto.  ⛔ Due copie della stessa regola in
 *    due linguaggi sono **due numeri che possono divergere**, e divergerebbero
 *    in silenzio: sul campo si vedrebbe solo «e' entrato uno di piu'» o «uno di
 *    meno», che nessuno collega a un'aritmetica.
 *
 * ⇒ Questo programmino monta `src/budget.c` COM'E' — nessuna copia, nessuna
 *   riscrittura — gli dava' in pasto scene note, e stampa una riga per scena.
 *   `banchi/10-d1-taratura.sh` fa girare le stesse scene dentro il predittore
 *   e **confronta**.  ⚠ Se le due divergono, il rosso e' qui, non sul campo.
 *
 * ⛔ E NON SOSTITUISCE LA MISURA: qui non c'e' nessuna GPU e nessun desktop.
 *    Questo dice *«il conto e' quello che credo»*; se la macchina regga davvero
 *    quel conto lo dice `10-d1-lancia.sh`, e sono due domande diverse.
 *
 * Si compila da `10-d1-taratura.sh`; a mano:
 *   cc -std=gnu11 -D_GNU_SOURCE -I src -o /tmp/conto banchi/10-d1-conto.c src/budget.c
 */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "budget.h"

/* ⚠ Lo stub del registro: qui non si prova il registro, si prova il conto.  Le
 *   righe vanno su stderr cosi' non sporcano l'uscita che il confronto legge. */
void registro_dice(const char *area, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	fprintf(stderr, "[%s] ", area);
	vfprintf(stderr, fmt, ap);
	fprintf(stderr, "\n");
	va_end(ap);
}
void registro_dettaglio(const char *area, const char *fmt, ...) { (void)area; (void)fmt; }

/* ⛔ Un fotogramma «finto» ma non falso: `budget_deposita()` e' quella vera, e
 *    l'istante lo si mette indietro di `ritardo_ms` come farebbe il figlio.
 * ⚠ Per far credere all'accumulatore che la sessione consegna a `fps`, si
 *   depositano i fotogrammi di **due secondi interi** — cioe' una finestra
 *   piena — perche' sotto la finestra il modulo risponde «non ho misurato», ed
 *   e' giusto che lo faccia. */
static void alimenta(const char *chi, uint32_t l, uint32_t a, double fps,
                     double ritardo_ms, double secondi)
{
	struct timespec t0, t;
	uint64_t adesso;
	int quanti = (int)(fps * secondi);

	clock_gettime(CLOCK_MONOTONIC, &t0);
	(void)t0;
	for (int i = 0; i < quanti; i++) {
		clock_gettime(CLOCK_MONOTONIC, &t);
		adesso = (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
		budget_deposita(chi, l, a, adesso - (uint64_t)(ritardo_ms * 1000.0));
	}
}

int main(int argc, char **argv)
{
	double capacita = 480.0, riserva = 0.5;
	int quanti_dentro = 0;
	uint32_t tela_l = 1920, tela_a = 1080;
	double consegna_fps = 0.0, ritardo_ms = 10.0;
	int mai_consegnato = 0;
	char perche[320];
	struct budget_conto conto;
	enum budget_esito e;

	for (int i = 1; i < argc; i++) {
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (!strcmp(argv[i], "--capacita") && v) capacita = atof(argv[++i]);
		else if (!strcmp(argv[i], "--riserva") && v) riserva = atof(argv[++i]);
		else if (!strcmp(argv[i], "--dentro") && v) quanti_dentro = atoi(argv[++i]);
		else if (!strcmp(argv[i], "--tela") && v) {
			sscanf(argv[++i], "%ux%u", &tela_l, &tela_a);
		}
		else if (!strcmp(argv[i], "--fps") && v) consegna_fps = atof(argv[++i]);
		else if (!strcmp(argv[i], "--ritardo-ms") && v) ritardo_ms = atof(argv[++i]);
		else if (!strcmp(argv[i], "--mai-consegnato")) mai_consegnato = 1;
		else { fprintf(stderr, "opzione ignota: %s\n", argv[i]); return 2; }
	}

	budget_caselle(quanti_dentro + 2);
	budget_accendi(capacita, riserva, 1920, 1080);
	if (!budget_acceso() && capacita > 0.0) {
		printf("ESITO NON-ACCESO\n");
		return 2;
	}

	/* ⚠ La finestra dell'accumulatore e' di due secondi: se si vuole che il
	 *   conto guardi il CONSEGNATO e non il ripiego, bisogna dargliene due. */
	if (!mai_consegnato && consegna_fps > 0.0) {
		struct timespec t;
		uint64_t t0, adesso;
		clock_gettime(CLOCK_MONOTONIC, &t);
		t0 = (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
		/* Si depositano i fotogrammi di 2,2 s di storia, spalmati all'indietro
		 * non si puo': l'accumulatore usa l'ora vera.  ⇒ si aspetta davvero. */
		for (;;) {
			clock_gettime(CLOCK_MONOTONIC, &t);
			adesso = (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
			if (adesso - t0 > 2400000ull)
				break;
			for (int k = 0; k < quanti_dentro; k++) {
				char chi[64];
				snprintf(chi, sizeof chi, "dentro%d", k);
				budget_deposita(chi, tela_l, tela_a,
				                adesso - (uint64_t)(ritardo_ms * 1000.0));
			}
			/* ⚠ Il passo e' il periodo del ritmo che si vuole imitare. */
			struct timespec pausa = {0, (long)(1e9 / (consegna_fps > 0 ? consegna_fps : 1))};
			nanosleep(&pausa, NULL);
		}
	} else if (!mai_consegnato) {
		/* ⭐ La sessione FERMA: consegna il suo scoppio iniziale e poi tace.
		 *    ⛔ E' il caso che vale doppio — dieci ferme devono ENTRARE. */
		alimenta("x", tela_l, tela_a, 0, 0, 0);
		for (int k = 0; k < quanti_dentro; k++) {
			char chi[64];
			struct timespec t;
			uint64_t adesso;
			snprintf(chi, sizeof chi, "dentro%d", k);
			clock_gettime(CLOCK_MONOTONIC, &t);
			adesso = (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
			for (int j = 0; j < 3; j++)
				budget_deposita(chi, tela_l, tela_a,
				                adesso - (uint64_t)(ritardo_ms * 1000.0));
		}
		struct timespec pausa = {2, 500000000L};
		nanosleep(&pausa, NULL);
	}

	budget_conto_apri(&conto);
	for (int k = 0; k < quanti_dentro; k++) {
		char chi[64];
		snprintf(chi, sizeof chi, "dentro%d", k);
		budget_conto_dentro(&conto, chi);
	}
	e = budget_conto_verdetto(&conto, "nuovo", tela_l, tela_a, perche,
	                          sizeof perche);
	printf("ESITO %s DOMANDA %.1f DENTRO %d AL-PEGGIORE %d PERCHE %s\n",
	       e == BUDGET_REGGE ? "REGGE"
	                         : (e == BUDGET_NON_REGGE ? "NON-REGGE" : "NON-SO"),
	       conto.domanda, conto.quanti, conto.al_peggiore, perche);
	return 0;
}
