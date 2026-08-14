/*
 * 04-b20-nasci.c — il programma minimo di A1: chiama UNA funzione del prodotto
 * e restituisce il suo numero.  `CODER.md` §3.6 alla lettera.
 *
 * ⛔ NON misura e NON giudica.  Serve a una cosa sola: far scrivere il drop-in
 *    e far nascere la sessione **al PRODOTTO**, e non a una riga di bash.
 *    Senza questo, la differenza fra il giro rosso e il giro verde sarebbe una
 *    riga di configurazione del banco — cioe' il banco giudicherebbe se stesso.
 *
 * ⭐ Lo stato d'uscita E' `SessioneStato`: 0 SANA · 1 NERA · 2 MISURA ALTRA ·
 *    3 SCELTO DA SE · 4 MORTA · 5 NON LETTA.  Nessuno deve tradurre.
 *    ⚠ 6 e' «non so che verbo mi hai detto», e non e' una misura.
 *
 * ⛔ E DOPO LA CURA IL NUMERO ATTESO CAMBIA, ed e' tutto il punto del rapporto:
 *    prima della cura la sessione remota sana e' **0 SANA** (un monitor suo);
 *    dopo la cura e' **1 NERA** — zero monitor propri, perche' l'unico monitor
 *    lo deve montare `RecordVirtual` quando arriva il client.  Chi legge questo
 *    numero senza aver letto `fasi/rapporti/F4-A1-desktop-vero.md` lo prendera'
 *    per un guasto: per questo la riga qui sotto lo scrive a parole.
 */
#include "sessione.h"

#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
	const char *verbo = argc > 1 ? argv[1] : "stato";
	unsigned larghezza = 1920, altezza = 1080;
	SessioneMonitor monitor;
	SessioneStato stato;
	bool nata = false;

	if (argc > 2 && sscanf(argv[2], "%ux%u", &larghezza, &altezza) != 2) {
		fprintf(stderr, "⛔ «%s» non e' una misura LxA\n", argv[2]);
		return 6;
	}

	if (strcmp(verbo, "assicura") == 0) {
		stato = sessione_assicura(larghezza, altezza, &nata);
		printf("assicura: %d %s (l'ho fatta nascere io: %s)\n", stato,
		       sessione_marca(stato), nata ? "si" : "no");
		return (int) stato;
	}
	if (strcmp(verbo, "stato") == 0) {
		stato = sessione_stato(larghezza, altezza, &monitor);
		printf("stato: %d %s\n", stato, sessione_marca(stato));
		if (monitor.quanti)
			printf("monitor: «%s» «%s» %ux%u@%.3f (in tutto %u)\n",
			       monitor.connettore, monitor.prodotto, monitor.larghezza,
			       monitor.altezza, monitor.refresh, monitor.quanti);
		return (int) stato;
	}
	fprintf(stderr, "uso: %s <assicura|stato> [LxA]\n", argv[0]);
	return 6;
}
