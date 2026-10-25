/* test.c — the parser of the capsules that arrive on the WebTransport CONNECT stream (webtransport.c, `capsule()`): R2 of the network
 * audit (25 Oct 2026, present since 1.0).
 *
 * THE DEFECT: every capsule moved the whole rest of the buffer down (`bytes_remove_head()` in the loop).  A capsule of type 0 and
 * length 0 is 2 bytes, so a chunk of L bytes of them cost about L²/4 bytes of `memmove` (360 KB for a 1.2 KB packet, 17 MB for an 8 KB
 * chunk), from a client that has not logged in and whose credit grows with every byte it sends (`cb_recv_data()`).
 * THE CURE: a read index, and the buffer compacted ONCE at the end of the call.
 *
 * HOW: the REAL webtransport.c is #included (never modified; its log is interposed by macros as in 02-wt-judgments-test.c and
 * wt-prelogin) and `memmove` is counted.  The OLD parser is kept below, verbatim, as `old_capsule()`, and both are fed the same bytes
 * on two zeroed sessions:
 *   1. random streams (all four varint widths, unknown types, close capsules 0x2843 with valid and invalid codes, capsules above the
 *      cap, zero-length ones) cut at random places (1 to 1500 bytes, mid-varint included): after EVERY chunk both have the same
 *      buffer, the same skip counter and the same list of close codes and log lines;
 *   2. the buffer never holds more than WT_CAPSULE_MAX + 16 bytes after a call, old and new alike (the memory did not change);
 *   3. the worst case, 2-byte capsules in chunks of 8191 bytes: the new parser moves a handful of bytes per chunk, the old one
 *      millions (printed; the check is the ratio, not a clock);
 *   4. a close capsule delivered one byte at a time closes once with its code; a capsule above the cap is skipped as it passes
 *      across chunks and the next one is read.
 *
 * BUILD AND RUN (a few seconds; the test links no other object: whatever the included file calls is generated as a stub that TRAPS if
 * reached; run from the root of the tree, in the build image of the product so the ngtcp2 and nghttp3 headers are there):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=2 --memory=2g -v "$PWD:/albero:ro" localhost/remotix-costruzione sh -c '
 *     cd /tmp && F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src $(pkg-config --cflags gio-2.0 libpipewire-0.3)" &&
 *     gcc $F -c /albero/benches/unit/capsule-parser/test.c -o t.o &&
 *     { gcc -fsanitize=address,undefined t.o -lm -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     gcc $F -c s.c -o s.o && gcc -fsanitize=address,undefined t.o s.o -lm -o test && ./test'
 * Exit code 0 green, 1 red, 3 not all checks ran.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "log.h"

static void rxt_says_of(const char *file, int text_line, const char *area, const char *chi, const char *fmt, ...);
static void rxt_detail_of(const char *file, int text_line, const char *area, const char *chi, const char *fmt, ...);
static uint64_t rxt_now(void);
static unsigned long long moved;
static void *counted_memmove(void *d, const void *s, size_t n)
{
	moved += n;
	return memmove(d, s, n);
}
#define log_says_of_in rxt_says_of
#define log_detail_of_in rxt_detail_of
#define log_now_ms rxt_now
#define memmove counted_memmove
#include "webtransport.c"
#undef memmove
#undef log_now_ms
#undef log_detail_of_in
#undef log_says_of_in

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 5

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

/* what the log hook saw, per session under test (the hook cannot tell which: the caller sets `sink`) */
struct seen {
	int lines, closes, skips;
	uint32_t codes[64];
};
static struct seen *sink;

static void rxt_says_of(const char *file, int text_line, const char *area, const char *chi, const char *fmt, ...)
{
	char line[512];
	va_list ap;
	unsigned int code;

	(void)file; (void)text_line; (void)area; (void)chi;
	va_start(ap, fmt);
	vsnprintf(line, sizeof line, fmt, ap);
	va_end(ap);
	if (!sink)
		return;
	sink->lines++;
	{
		const char *p = strstr(line, "CLOSED") ? strstr(line, "code 0x") : NULL;

		if (p && sscanf(p, "code 0x%x", &code) == 1) {
			if (sink->closes < 64)
				sink->codes[sink->closes] = code;
			sink->closes++;
		}
	}
	if (strstr(line, "SKIPPED"))
		sink->skips++;
}
static void rxt_detail_of(const char *file, int text_line, const char *area, const char *chi, const char *fmt, ...)
{
	(void)file; (void)text_line; (void)area; (void)chi; (void)fmt;
}
static uint64_t rxt_now(void) { return 5000000; }
/* prelogin_may_log() (rilettura-wt W1) is linked in by the included file and asks rcp_key_address(); this harness links no rcp.o, and no connection here is pre-login */
void rcp_key_address(const char *text, char *out, size_t cap)
{
	snprintf(out, cap, "%s", text ? text : "");
}

/* ── the OLD parser, verbatim from b0aabae3 (webtransport.c, `capsule()`): bytes_remove_head() at every capsule ── */
static void old_capsule(wt *w, int64_t stream_id, const uint8_t *data, size_t len)
{
	if (stream_id != w->session || len == 0)
		return;
	if (w->capsule_skip > 0) {
		uint64_t n = w->capsule_skip < len ? w->capsule_skip : (uint64_t)len;
		w->capsule_skip -= n;
		data += n;
		len -= (size_t)n;
		if (len == 0)
			return;
	}
	if (!bytes_add(&w->capsbuf, data, len))
		return;
	for (;;) {
		uint64_t kind = 0, lung = 0;
		size_t a, b;
		const uint8_t *body;

		a = varint_read(&kind, w->capsbuf.d, w->capsbuf.n);
		if (a == 0)
			return;
		b = varint_read(&lung, w->capsbuf.d + a, w->capsbuf.n - a);
		if (b == 0)
			return;
		if (lung > WT_CAPSULE_MAX) {
			uint64_t here = w->capsbuf.n - a - b;
			uint64_t grabbed = here < lung ? here : lung;
			rxt_says_of(__FILE__, __LINE__, REG_WT, NULL, "capsule 0x%llx %llu bytes long, beyond the cap of %d: SKIPPED without keeping it",
			               (unsigned long long)kind, (unsigned long long)lung, WT_CAPSULE_MAX);
			w->capsule_skip = lung - grabbed;
			bytes_remove_head(&w->capsbuf, a + b + (size_t)grabbed);
			if (w->capsule_skip > 0)
				return;
			continue;
		}
		if (w->capsbuf.n < a + b + lung)
			return;
		body = w->capsbuf.d + a + b;
		if (kind == 0x2843 && lung >= 4) {
			uint32_t code = ((uint32_t)body[0] << 24) | ((uint32_t)body[1] << 16) | ((uint32_t)body[2] << 8) | (uint32_t)body[3];
			rxt_says_of(__FILE__, __LINE__, REG_WT, NULL, "the page CLOSED the WebTransport session: code 0x%x", code);
			closed_by_client(w, code);
		}
		bytes_remove_head(&w->capsbuf, a + b + (size_t)lung);
	}
}

/* ── building streams ── */
static uint64_t rng_state = 88172645463325252ull;
static uint32_t rnd(void)
{
	rng_state ^= rng_state << 13;
	rng_state ^= rng_state >> 7;
	rng_state ^= rng_state << 17;
	return (uint32_t)(rng_state >> 11);
}
static size_t put_varint(uint8_t *b, uint64_t v, int width)
{   /* width 1, 2, 4 or 8 bytes (the minimum that fits is not required: a client may use a longer form) */
	int n = width;

	if (v >= (1ull << (n == 1 ? 6 : n == 2 ? 14 : n == 4 ? 30 : 62)))
		n = v < (1ull << 6) ? 1 : v < (1ull << 14) ? 2 : v < (1ull << 30) ? 4 : 8;
	for (int i = n - 1; i >= 0; i--)
		b[n - 1 - i] = (uint8_t)(v >> (8 * i));
	b[0] |= (uint8_t)((n == 1 ? 0 : n == 2 ? 1 : n == 4 ? 2 : 3) << 6);
	return (size_t)n;
}
static size_t one_capsule(uint8_t *out, size_t cap)
{
	static const int widths[] = {1, 2, 4, 8};
	size_t n = 0;
	uint64_t kind, lung;
	uint32_t pick = rnd() % 10;

	if (pick == 0) {                          /* a close capsule, valid or invalid code */
		kind = 0x2843;
		lung = rnd() % 12;                  /* 0..11: also the ones shorter than the 4 bytes of a code (no close, just consumed) */
	} else if (pick == 1) {                   /* above the cap */
		kind = rnd() % 3000;
		lung = WT_CAPSULE_MAX + 1 + rnd() % 3000;
	} else if (pick == 2) {                   /* zero-length */
		kind = rnd() % 70;
		lung = 0;
	} else {
		kind = rnd() % 500;
		lung = rnd() % 200;
	}
	n += put_varint(out + n, kind, widths[rnd() % 4]);
	n += put_varint(out + n, lung, widths[rnd() % 4]);
	if (n + lung > cap)
		lung = cap > n ? cap - n : 0;
	if (kind == 0x2843 && lung >= 4) {
		uint32_t code = rnd() % 4 == 0 ? rnd() % 300 : (uint32_t)(1 + rnd() % 12);
		out[n] = (uint8_t)(code >> 24); out[n + 1] = (uint8_t)(code >> 16); out[n + 2] = (uint8_t)(code >> 8); out[n + 3] = (uint8_t)code;
		memset(out + n + 4, 0xAB, lung - 4);
	} else {
		for (uint64_t i = 0; i < lung; i++)
			out[n + i] = (uint8_t)rnd();
	}
	return n + (size_t)lung;
}

static bool same_state(const wt *a, const wt *b)
{
	return a->capsbuf.n == b->capsbuf.n && a->capsule_skip == b->capsule_skip &&
	       (a->capsbuf.n == 0 || memcmp(a->capsbuf.d, b->capsbuf.d, a->capsbuf.n) == 0);
}
static bool same_seen(const struct seen *a, const struct seen *b)
{
	return a->lines == b->lines && a->closes == b->closes && a->skips == b->skips &&
	       memcmp(a->codes, b->codes, sizeof(uint32_t) * (size_t)(a->closes < 64 ? a->closes : 64)) == 0;
}
static double now_s(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

static wt Wo, Wn;

int main(void)
{
	struct seen so, sn;

	setvbuf(stdout, NULL, _IONBF, 0);

	/* 1 + 2: random streams, random cuts, compared after every chunk */
	{
		static uint8_t stream[8192];
		bool equal = true;
		size_t maxbuf_n = 0, maxbuf_o = 0, chunks = 0;
		int streams = 0;

		for (int s = 0; s < 400 && equal; s++) {
			size_t used = 0, at = 0;

			memset(&Wo, 0, sizeof Wo);
			Wo.was_logged_in = true;   /* (both parsers call the same closed_by_client(), now behind prelogin_may_log()) */
			memset(&Wn, 0, sizeof Wn);
			Wn.was_logged_in = true;   /* rilettura-wt W1: capsule()'s lines pass prelogin_may_log(); a logged-in connection writes every line, as the old parser did */
			memset(&so, 0, sizeof so);
			memset(&sn, 0, sizeof sn);
			while (used + 64 < sizeof stream && rnd() % 40 != 0)
				used += one_capsule(stream + used, sizeof stream - used);
			while (at < used) {
				size_t c = 1 + rnd() % (rnd() % 8 == 0 ? 1500 : 60);

				if (c > used - at)
					c = used - at;
				sink = &so;
				old_capsule(&Wo, 0, stream + at, c);
				sink = &sn;
				capsule(&Wn, 0, stream + at, c);
				sink = NULL;
				at += c;
				chunks++;
				if (Wo.capsbuf.n > maxbuf_o)
					maxbuf_o = Wo.capsbuf.n;
				if (Wn.capsbuf.n > maxbuf_n)
					maxbuf_n = Wn.capsbuf.n;
				if (!same_state(&Wo, &Wn) || !same_seen(&so, &sn)) {
					printf("       differs in stream %d after %zu of %zu bytes\n", s, at, used);
					equal = false;
					break;
				}
			}
			streams++;
			bytes_free(&Wo.capsbuf);
			bytes_free(&Wn.capsbuf);
		}
		printf("       %d streams, %zu chunks compared; largest buffer after a call: old %zu, new %zu\n", streams, chunks, maxbuf_o, maxbuf_n);
		require(equal && streams == 400, "1. 400 random streams cut at random places: after every chunk old and new have the same buffer, skip counter, close codes and log lines");
		require(maxbuf_n <= (size_t)WT_CAPSULE_MAX + 16 && maxbuf_o <= (size_t)WT_CAPSULE_MAX + 16,
		        "2. the buffer holds at most one incomplete capsule after a call (WT_CAPSULE_MAX + 16): the memory did not change");
	}

	/* 3: the worst case, 2-byte capsules (type 0, length 0) in chunks of 8191 bytes */
	{
		static uint8_t chunk[8191];
		unsigned long long mo, mn;
		double t0, to, tn;
		const int N = 50;

		memset(chunk, 0, sizeof chunk);                      /* 0x00 0x00 pairs: 4095 capsules and one stray byte */
		memset(&Wo, 0, sizeof Wo);
			Wo.was_logged_in = true;   /* (both parsers call the same closed_by_client(), now behind prelogin_may_log()) */
		memset(&Wn, 0, sizeof Wn);
			Wn.was_logged_in = true;   /* rilettura-wt W1: capsule()'s lines pass prelogin_may_log(); a logged-in connection writes every line, as the old parser did */
		moved = 0; t0 = now_s();
		for (int i = 0; i < N; i++)
			old_capsule(&Wo, 0, chunk, sizeof chunk);
		mo = moved; to = now_s() - t0;
		moved = 0; t0 = now_s();
		for (int i = 0; i < N; i++)
			capsule(&Wn, 0, chunk, sizeof chunk);
		mn = moved; tn = now_s() - t0;
		printf("       %d chunks of 8191 bytes of 2-byte capsules: old moves %llu bytes (%.1f MB per chunk, %.3f s), new moves %llu bytes (%.3f s)\n",
		       N, mo, (double)mo / N / 1e6, to, mn, tn);
		require(mn <= (unsigned long long)N * 2 && mo >= (unsigned long long)N * 8000000ull,
		        "3. 2-byte capsules in 8191-byte chunks: the new parser moves at most 2 bytes a chunk, the old one 8 MB or more");
		bytes_free(&Wo.capsbuf);
		bytes_free(&Wn.capsbuf);
	}

	/* 4: byte by byte, and a capsule above the cap across chunks */
	{
		uint8_t close_cap[16] = {0}, big[1100 + 40], after[8];
		size_t n = 0, nb = 0;

		memset(&Wn, 0, sizeof Wn);
			Wn.was_logged_in = true;   /* rilettura-wt W1: capsule()'s lines pass prelogin_may_log(); a logged-in connection writes every line, as the old parser did */
		memset(&sn, 0, sizeof sn);
		n += put_varint(close_cap + n, 0x2843, 2);
		n += put_varint(close_cap + n, 4, 1);
		close_cap[n++] = 0; close_cap[n++] = 0; close_cap[n++] = 0; close_cap[n++] = 3;
		sink = &sn;
		for (size_t i = 0; i < n; i++)
			capsule(&Wn, 0, close_cap + i, 1);
		sink = NULL;
		require(sn.closes == 1 && sn.codes[0] == 3 && Wn.capsbuf.n == 0, "4. a close capsule delivered one byte at a time: closes once, code 0x3, buffer empty");
		bytes_free(&Wn.capsbuf);

		memset(&Wn, 0, sizeof Wn);
			Wn.was_logged_in = true;   /* rilettura-wt W1: capsule()'s lines pass prelogin_may_log(); a logged-in connection writes every line, as the old parser did */
		memset(&sn, 0, sizeof sn);
		nb += put_varint(big + nb, 0x77, 1);
		nb += put_varint(big + nb, 5000, 2);                  /* above the cap of 1028 */
		sink = &sn;
		capsule(&Wn, 0, big, nb);                             /* the header alone: nothing kept, 5000 to skip */
		for (int i = 0; i < 4; i++)
			capsule(&Wn, 0, (const uint8_t *)memset(big, 0x55, 1100), 1100);   /* 4400 skipped */
		capsule(&Wn, 0, big, 600);                            /* 600 more: the last 600 of the 5000 end here */
		n = 0;
		n += put_varint(after + n, 0x2843, 2);
		n += put_varint(after + n, 4, 1);
		after[n++] = 0; after[n++] = 0; after[n++] = 0; after[n++] = 9;
		capsule(&Wn, 0, after, n);
		sink = NULL;
		require(sn.skips == 1 && sn.closes == 1 && sn.codes[0] == 9 && Wn.capsule_skip == 0 && Wn.capsbuf.n == 0,
		        "5. a 5000-byte capsule above the cap is skipped as it passes (nothing kept) and the next capsule is read");
		bytes_free(&Wn.capsbuf);
	}

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
