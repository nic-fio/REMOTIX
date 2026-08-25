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

/* ⭐ L'identita' di questo processo — il riquadro sta in `registro.h`.  ⚠ Una
 *    COPIA e non un puntatore: chi la posa passa spesso un `argv`, e un
 *    puntatore a memoria altrui e' un registro che mente il giorno in cui
 *    quella memoria cambia. */
static char identita[REG_IDENTITA_MAX + 1];

void registro_parlantina(bool acceso) { parlantina = acceso; }
bool registro_parla_molto(void) { return parlantina; }

void registro_identita(const char *chi)
{
	if (!chi || !*chi) {
		identita[0] = '\0';
		return;
	}
	snprintf(identita, sizeof identita, "%s", chi);
}

uint64_t registro_ora_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000u + (uint64_t)(ts.tv_nsec / 1000000);
}

static void riga(const char *area, const char *chi, const char *fmt, va_list ap)
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
	/* ⭐⭐ E QUI DENTRO SI DICE DI CHI E' LA RIGA — 25 agosto 2026, R10-A4.
	 *
	 *     L'identita' della singola riga batte quella del processo: nel padre
	 *     un processo solo serve tutte le sessioni, e la seconda non c'e'.
	 *     ⛔ Ma la parentesi si compone SOLO qui: il riquadro di `registro.h`
	 *        dice perche', ed e' la ragione per cui i chiamanti passano il nome
	 *        nudo invece della stringa gia' fatta.
	 *
	 * ⛔ In TESTA AL CORPO, non fra l'ora e l'area, e non e' estetica: chi
	 *    legge il registro lo spezza in «ora · area · corpo» e un campo nuovo
	 *    in mezzo gli sposta l'area sotto gli occhi.  In testa al corpo, un
	 *    lettore vecchio continua a leggere, e uno nuovo la stacca.
	 * ⚠ E i byte in piu' li pagano SOLO le righe che hanno qualcosa da dire:
	 *   chi non sa tace, e non paga. */
	const char *id = (chi && *chi) ? chi : identita;
	char idsano[REG_IDENTITA_MAX + 1];
	int n;
	if (id && *id) {
		/* ⛔ SI RIPULISCE, e non e' diffidenza verso PAM: un `]` o un a-capo
		 *    dentro l'identificatore spezzerebbe la riga in due, e una riga
		 *    spezzata e' **plausibile e falsa** — il difetto che la cura del
		 *    21 agosto (una sola `write` per riga) ha appena finito di
		 *    togliere.  ⚠ Si tiene solo quel che sta in un nome utente. */
		size_t k = 0;
		for (const char *p = id; *p && k < REG_IDENTITA_MAX; p++, k++) {
			unsigned char c = (unsigned char)*p;
			bool buono = (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z')
			             || (c >= 'a' && c <= 'z') || c == '.' || c == '_'
			             || c == '-' || c == '@' || c == ':';
			idsano[k] = buono ? (char)c : '_';
		}
		idsano[k] = '\0';
		n = snprintf(buf, sizeof buf, "%s.%03ld %-7s [%s] ", quando,
		             ts.tv_nsec / 1000000, area, idsano);
	} else
		n = snprintf(buf, sizeof buf, "%s.%03ld %-7s ", quando,
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
	riga(area, NULL, fmt, ap);
	va_end(ap);
}

void registro_dettaglio(const char *area, const char *fmt, ...)
{
	va_list ap;
	if (!parlantina)
		return;
	va_start(ap, fmt);
	riga(area, NULL, fmt, ap);
	va_end(ap);
}

void registro_dice_di(const char *area, const char *chi, const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	riga(area, chi, fmt, ap);
	va_end(ap);
}

void registro_dettaglio_di(const char *area, const char *chi, const char *fmt,
                           ...)
{
	va_list ap;
	if (!parlantina)
		return;
	va_start(ap, fmt);
	riga(area, chi, fmt, ap);
	va_end(ap);
}
