/*
 * stubs_log.c — the product's log (`src/log.h`), for the harnesses.
 *
 * ⚠ `src/log.c` is NOT linked: it writes every line to stderr (and the journal), and at
 *   tens of thousands of executions per second the fuzzer would measure the terminal.
 * ⛔ But every line is still FORMATTED (`vsnprintf`): see `common.h`.
 *   `RXFUZZ_LOG=1` in the environment prints them, to read what a reproducer did.
 */
#include "common.h"

#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

uint64_t rx_now_ms = 1000000;

static int verbose = -1;

/* ⭐ A harness that judges the EVENT lines (the normal log, not `log_detail`) sets this:
 *    it gets each one, formatted (quic-conn: «new connection» lines are rate-limited). */
void (*rx_event_line)(const char *text);

static void line(const char *area, const char *chi, const char *fmt, va_list ap)
{
	char buf[4096];
	vsnprintf(buf, sizeof buf, fmt, ap);
	if (verbose < 0)
		verbose = getenv("RXFUZZ_LOG") != NULL;
	if (verbose)
		fprintf(stderr, "[%s%s%s] %s\n", area ? area : "", chi ? " " : "", chi ? chi : "", buf);
}

void log_says_in(const char *file, int text_line, const char *area, const char *fmt, ...)
{
	va_list ap;
	(void)file;
	(void)text_line;
	va_start(ap, fmt);
	line(area, NULL, fmt, ap);
	va_end(ap);
	if (rx_event_line) {
		char buf[4096];
		va_start(ap, fmt);
		vsnprintf(buf, sizeof buf, fmt, ap);
		va_end(ap);
		rx_event_line(buf);
	}
}

void log_detail_in(const char *file, int text_line, const char *area, const char *fmt, ...)
{
	va_list ap;
	(void)file;
	(void)text_line;
	va_start(ap, fmt);
	line(area, NULL, fmt, ap);
	va_end(ap);
}

void log_says_of_in(const char *file, int text_line, const char *area, const char *chi,
                    const char *fmt, ...)
{
	va_list ap;
	(void)file;
	(void)text_line;
	va_start(ap, fmt);
	line(area, chi, fmt, ap);
	va_end(ap);
}

void log_detail_of_in(const char *file, int text_line, const char *area, const char *chi,
                      const char *fmt, ...)
{
	va_list ap;
	(void)file;
	(void)text_line;
	va_start(ap, fmt);
	line(area, chi, fmt, ap);
	va_end(ap);
}

uint64_t log_now_ms(void) { return rx_now_ms; }
void log_chatter(bool is_on) { (void)is_on; }
bool log_verbose(void) { return true; } /* ⭐ the detail lines are formatted too */
