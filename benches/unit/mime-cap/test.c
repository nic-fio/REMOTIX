/* test.c — mimecap.h (audit of the session, S-R10).
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /albero && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter \
 *        -Isrc benches/unit/mime-cap/test.c -o /tmp/test && /tmp/test'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "mimecap.h"
#include <stdio.h>
#include <stdlib.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

static int has(const char *file, const char *needle)
{
	FILE *f = fopen(file, "r");
	static char src[2u << 20];
	size_t n;

	if (!f) return 0;
	n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
	return strstr(src, needle) != NULL;
}

int main(void)
{
	char longname[400];
	uint64_t last = 0;

	CHECK(mime_keep(0, "text/plain") && mime_keep(63, "UTF8_STRING"), "1. normal names are kept");
	CHECK(!mime_keep(0, "") && !mime_keep(0, NULL), "2. empty / NULL refused");
	CHECK(!mime_keep(MIME_MAX_TYPES, "text/plain") && mime_keep(MIME_MAX_TYPES - 1, "text/plain"), "3. the list stops at MIME_MAX_TYPES");
	memset(longname, 'a', sizeof longname - 1); longname[sizeof longname - 1] = 0;
	CHECK(!mime_keep(0, longname), "4. a 399-byte name is refused");
	longname[MIME_MAX_LEN] = 0;
	CHECK(mime_keep(0, longname), "4b. exactly MIME_MAX_LEN bytes is kept");
	longname[MIME_MAX_LEN] = 'a'; longname[MIME_MAX_LEN + 1] = 0;
	CHECK(!mime_keep(0, longname), "4c. one byte more is refused");
	{
		size_t kept = 0;
		for (int i = 0; i < 100000; i++)
			if (mime_keep(kept, "application/x-something-else"))
				kept++;
		CHECK(kept == MIME_MAX_TYPES, "5. 100000 offered types: MIME_MAX_TYPES kept");
	}
	CHECK(mime_line_allowed(&last), "6. the first line is allowed");
	{
		int n = 0;
		for (int i = 0; i < 1000; i++)
			n += mime_line_allowed(&last);
		CHECK(n == 0, "6b. the next 1000 inside the window are not");
		last -= MIME_LINE_WINDOW_MS;
		CHECK(mime_line_allowed(&last), "6c. after the window it is allowed again");
	}
	CHECK(has("src/clipboard_kde.c", "the types we LOOK FOR are always kept"), "7a. clipboard_kde.c keeps TEXT_TYPES past the ceiling");
	CHECK(has("src/clipboard_kde.c", "mime_keep(offer->mime->len, mime)") && has("src/clipboard_kde.c", "mime_line_allowed(&last_line)"), "7. clipboard_kde.c bounds the list and the line");
	CHECK(has("src/clipboard.c", "mime_line_allowed(&last_line)") && has("src/clipboard.c", "MIME_LOG_TYPES"), "7b. clipboard.c bounds the line and the listing");
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
