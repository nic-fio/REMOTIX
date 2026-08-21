/*
 * registro.c — vedi registro.h.
 */
#include "registro.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static bool parlantina;

void registro_parlantina(bool acceso) { parlantina = acceso; }
bool registro_parla_molto(void) { return parlantina; }

uint64_t registro_ora_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000u + (uint64_t)(ts.tv_nsec / 1000000);
}

static void riga(const char *area, const char *fmt, va_list ap)
{
	struct timespec ts;
	struct tm tm;
	char quando[32];
	/* ⛔ 4096 e' `PIPE_BUF`, il confine sotto il quale una `write` in append
	 *    non si intreccia con quelle degli altri processi. */
	char buf[4096];

	clock_gettime(CLOCK_REALTIME, &ts);
	localtime_r(&ts.tv_sec, &tm);
	strftime(quando, sizeof quando, "%H:%M:%S", &tm);

	/* ⛔⛔ UNA SOLA `write()` PER RIGA, E NON E' ELEGANZA — 21 agosto 2026.
	 *
	 *      Prima qui c'erano TRE chiamate su uno `stderr` non bufferizzato
	 *      (intestazione, corpo, a-capo), cioe' almeno tre `write()`.  ⚠ Il
	 *      padre e il figlio appendono allo STESSO file: quando le scritture
	 *      si accavallano, un corpo finisce dopo l'a-capo altrui e nasce una
	 *      riga SENZA MARCA TEMPORALE.
	 *
	 * `[M]` misurato su un registro vero di 3,0 MB (28 035 righe): **23 righe
	 *      orfane**, e fra queste **3 su 80** delle «tela CHIESTA al
	 *      produttore» — cioe' il 3,8 % di una famiglia di righe su cui un
	 *      attrezzo contava.  ⇒ Il sintomo non era «il registro e' brutto»:
	 *      era un attrezzo che moriva con `ValueError`, e per arrivarci ci e'
	 *      voluto un giro di banco.
	 *
	 * ⛔ E il difetto peggiore e' quello che NON fa morire niente: un conto
	 *    che perde il 3,8 % delle sue righe resta plausibile.  Il registro e'
	 *    lo strumento di diagnosi principale di questo progetto (`LEZIONI.md`
	 *    §2.7): se mente sotto carico, mente proprio quando serve.
	 *
	 * ⭐ `write(2)` diretta invece di `stdio`: una riga sotto `PIPE_BUF` (4096
	 *    su Linux) scritta con una sola `write` su un file aperto in append e'
	 *    atomica rispetto alle altre.  ⚠ Chi supera il buffer viene TRONCATO
	 *    con un segno, invece di uscire intrecciato: una riga tagliata si
	 *    vede, una riga intrecciata no.
	 * ⭐ E in piu' e' async-signal-safe, che `fprintf` non e'. */
	int n = snprintf(buf, sizeof buf, "%s.%03ld %-7s ", quando,
	                 ts.tv_nsec / 1000000, area);
	if (n < 0)
		return;
	if ((size_t)n > sizeof buf - 2)
		n = (int)(sizeof buf - 2);
	int m = vsnprintf(buf + n, sizeof buf - (size_t)n - 1, fmt, ap);
	if (m < 0)
		m = 0;
	if ((size_t)(n + m) > sizeof buf - 2) {
		/* ⚠ Troncata: si DICHIARA, o una riga tagliata sembra una riga corta. */
		n = (int)(sizeof buf - 4);
		buf[n++] = '.'; buf[n++] = '.'; buf[n++] = '.';
	} else {
		n += m;
	}
	buf[n++] = '\n';

	/* ⛔ Senza questa scrittura immediata il registro e' una speranza sul
	 *    momento in cui qualcuno lo vedra': `LEZIONI.md` §1.9, settima veste
	 *    — lo stdout bufferizzato su file ha gia' fatto accusare il codice
	 *    giusto.  ⭐ Con `write(2)` il problema non si pone: non c'e' buffer
	 *    da svuotare, e il `fflush` di prima non serve piu'. */
	ssize_t scritti = write(STDERR_FILENO, buf, (size_t)n);
	(void)scritti; /* ⚠ non c'e' nessun posto dove riferire che il registro
	                *    non si scrive: l'unico canale sarebbe quello rotto. */
}

void registro_dice(const char *area, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	riga(area, fmt, ap);
	va_end(ap);
}

void registro_dettaglio(const char *area, const char *fmt, ...)
{
	va_list ap;
	if (!parlantina)
		return;
	va_start(ap, fmt);
	riga(area, fmt, ap);
	va_end(ap);
}
