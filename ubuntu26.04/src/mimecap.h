/* mimecap.h — limits on the list of MIME types a desktop program offers (audit of the session, S-R10, 25 Oct 2026).
 *
 * A program of the user's own desktop can offer thousands of long type names and copy several times a second: the child's memory grew (KDE/wlroots keeps every name) and
 * every copy wrote a line with all of them.  (Log injection was checked and excluded: log.c replaces every control byte.)  Now: at most MIME_MAX_TYPES names per offer,
 * each at most MIME_MAX_LEN bytes (the rest are not kept: the ones we look for, TEXT_TYPES, are short and found among the first); in the log at most MIME_LOG_TYPES
 * names, then «and N more»; and the «not text» line itself at most once per MIME_LINE_WINDOW_MS.  Header-only, tested by benches/unit/mime-cap. */
#ifndef MIMECAP_H
#define MIMECAP_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#define MIME_MAX_TYPES 64
#define MIME_MAX_LEN 127
#define MIME_LOG_TYPES 8
#define MIME_LINE_WINDOW_MS 1000

/* May this name be kept, having `have` already? (empty, too long, or the list full: no) */
static inline bool mime_keep(size_t have, const char *mime)
{
	return mime && *mime && have < MIME_MAX_TYPES && strnlen(mime, MIME_MAX_LEN + 1) <= MIME_MAX_LEN;
}

/* true at most once per MIME_LINE_WINDOW_MS for the same `*last` (monotonic ms; 0 = never yet) */
static inline bool mime_line_allowed(uint64_t *last)
{
	struct timespec t;
	uint64_t now;

	clock_gettime(CLOCK_MONOTONIC, &t);
	now = (uint64_t)t.tv_sec * 1000u + (uint64_t)t.tv_nsec / 1000000u + 1u;
	if (*last && now - *last < MIME_LINE_WINDOW_MS)
		return false;
	*last = now;
	return true;
}

#endif
