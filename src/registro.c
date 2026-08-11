/*
 * registro.c — vedi registro.h.
 */
#include "registro.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

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

	clock_gettime(CLOCK_REALTIME, &ts);
	localtime_r(&ts.tv_sec, &tm);
	strftime(quando, sizeof quando, "%H:%M:%S", &tm);

	fprintf(stderr, "%s.%03ld %-7s ", quando, ts.tv_nsec / 1000000, area);
	vfprintf(stderr, fmt, ap);
	fputc('\n', stderr);
	/* ⛔ Senza questa riga il registro e' una speranza sul momento in cui
	 *    qualcuno lo vedra': `LEZIONI.md` §1.9, settima veste — lo stdout
	 *    bufferizzato su file ha gia' fatto accusare il codice giusto.  Qui
	 *    si scrive su stderr, che non e' bufferizzato per riga quando e'
	 *    rediretto: si forza. */
	fflush(stderr);
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
