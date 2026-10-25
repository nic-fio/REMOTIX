/*
 * test.c — the output queue of webtransport.c is limited in NUMBER of elements as well as in bytes (audit of 25 Oct 2026, P-R6 / Q-R5).
 * The byte cap (WT_QUEUE_MAX, 17 MiB) did not bound the bookkeeping: each element costs its own `output` and a step in every scan of
 * queue_choose(), and the cheapest element per byte is a 16-byte answer.
 *
 * Read from the source (argv[1] = src/webtransport.c; nothing is linked):
 *   1. WT_QUEUE_ITEMS_MAX exists, is at least 4096 (a stalled link filled with 4 KB audio blocks holds about 4500) and at most 65536;
 *   2. queue_put() tests it BEFORE the queue grows (before the realloc/doubling) and before anything is written in the queue;
 *   3. touching it returns false, as the byte cap does (enqueue() then makes the layer faulty: no half message goes out);
 *   4. the test counts the LIVE elements (nqueue - head), not the capacity;
 *   5. the byte cap is still there and still tested first or alongside (both limits stay).
 * And the arithmetic: the bookkeeping at the cap is below 4 MiB per session for a 150-byte element.
 *
 * BUILD AND RUN (a second; from the root of the tree):
 *   gcc -O1 -std=gnu11 -D_GNU_SOURCE -Wall -Wextra benches/unit/wt-queue-items/test.c -o /tmp/wt-queue-items-test && /tmp/wt-queue-items-test src/webtransport.c
 * Exit code 0 = every check passed, 1 = a check failed, 2 = no source given.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static char *slurp(const char *path)
{
	FILE *f = fopen(path, "r");
	long n;
	char *b;

	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	b = malloc((size_t)n + 1);
	if (b && fread(b, 1, (size_t)n, f) != (size_t)n) {
		free(b);
		b = NULL;
	}
	if (b)
		b[n] = 0;
	fclose(f);
	return b;
}

int main(int argc, char **argv)
{
	char *src;
	const char *def, *fn, *end, *items, *bytes, *grow, *ret;
	long max;

	if (argc < 2) {
		printf("usage: test src/webtransport.c\n");
		return 2;
	}
	src = slurp(argv[1]);
	CHECK(src != NULL, "the source is readable");
	if (!src)
		return 1;
	def = strstr(src, "#define WT_QUEUE_ITEMS_MAX ");
	CHECK(def != NULL, "1: WT_QUEUE_ITEMS_MAX is defined");
	max = def ? atol(def + strlen("#define WT_QUEUE_ITEMS_MAX ")) : -1;
	CHECK(max >= 4096 && max <= 65536, "1: and between 4096 and 65536");
	CHECK(max > 0 && (max * 150) < 4L * 1024 * 1024, "the bookkeeping at the cap (150 bytes each) is below 4 MiB per session");
	fn = strstr(src, "static bool queue_put(wt *w, int64_t id, const uint8_t *d, size_t n, bool fin)\n{");
	CHECK(fn != NULL, "queue_put found");
	if (fn) {
		end = strstr(fn, "\n}\n");
		items = strstr(fn, "w->nqueue - w->head >= WT_QUEUE_ITEMS_MAX");
		bytes = strstr(fn, "w->byte_in_queue + n > WT_QUEUE_MAX");
		grow = strstr(fn, "realloc(w->queue");
		ret = items ? strstr(items, "return false;") : NULL;
		CHECK(items && end && items < end, "2: queue_put tests the number of elements");
		CHECK(items && grow && items < grow, "2: and BEFORE the queue grows");
		CHECK(items && ret && grow && ret < grow, "3: touching it returns false (before any growth)");
		CHECK(items && memchr(items, '\n', 80) != NULL && strstr(fn, "w->nqueue - w->head >= WT_QUEUE_ITEMS_MAX") != NULL,
		      "4: it counts the live elements (nqueue - head)");
		CHECK(bytes && end && bytes < end, "5: the byte cap is still there");
	}
	free(src);
	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
