/*
 * test.c — unit test of the BODY of HERE_I_AM (RCP §6.2 / §4.3), in src/rcp.c and in its twin benches/rcp/rcp.c.
 *
 * WHY: 549a9e06 (24 Oct 2026). Since 84fdf573 `bench.mark` is written only in a BENCH build, and the product build
 * declared 5 capabilities and wrote 4: the page's DataView read past the end of the message (a regression against 1.0).
 * Nothing compared the DECLARED count with the pairs WRITTEN, in either build. This test does.
 *
 * HOW: the REAL rcp.c (src/ or the twin, chosen by -I) is #included, never modified; a session is opened with minimal
 * hooks, `send_here_i_am()` is called and the hook `send_msg` captures the whole message (the seam of
 * benches/fuzz/rcp-msg/fuzz_rcp_msg.c). The body is then parsed the way the page does it — u16 version, u16 n,
 * n pairs of (u16 length + bytes) strings — with EVERY read checked against the end:
 *   header   type 0x0002, the declared body length is what follows
 *   version  the u16 is RCP_VERSION
 *   count    n pairs are readable (no read past the end), and n == the pairs read
 *   leftover no byte is left after the n-th pair
 *   content  video.codec, video.depth, audio.codec, clipboard.text are there once each, with a value; no key twice;
 *            bench.mark is present iff the build has -DREMOTIX_BENCH (then "yes" or "no")
 * Any extra capability (PACE, later) is parsed all the same and only has to keep count == pairs, no leftover.
 *
 * Built TWICE per tree (without and with -DREMOTIX_BENCH) and for BOTH trees (src and the benches/rcp twin);
 * add -DREMOTIX_PACE (or whatever the new capability needs) to the list of variants when it exists.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=2 -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && rc=0 &&
 *     for T in src benches/rcp; do for D in "-DREMOTIX_NONE" "-DREMOTIX_BENCH"; do
 *       echo "== $T $D" &&
 *       F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE $D \
 *          -Wall -Wextra -Wno-unused-parameter -I/albero/$T -I/albero/benches/fuzz/rcp-msg" &&
 *       clang $F -c /albero/benches/unit/here-i-am/test.c -o t.o &&
 *       clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *       clang -fsanitize=address,undefined t.o l.o -o test && ./test || rc=1;
 *     done; done; exit $rc'
 * Exit code 0 = every check passed in all four builds. (-DREMOTIX_NONE is a harmless define: "no BENCH".)
 */
#include "rcp.c"

#include <stdio.h>

static int checks, bad;

#define CHECK(cond, ...)                                                      \
	do {                                                                  \
		checks++;                                                     \
		if (!(cond)) {                                                \
			bad++;                                                \
			printf("  FAIL %s:%d  %s  -- ", __FILE__, __LINE__, #cond); \
			printf(__VA_ARGS__);                                  \
			printf("\n");                                         \
		}                                                             \
	} while (0)

static uint8_t got[4096];
static size_t got_n;
static int sent;

static void h_send(void *c, const uint8_t *d, size_t n)
{
	(void)c;
	sent++;
	if (n <= sizeof got) {
		memcpy(got, d, n);
		got_n = n;
	}
}
static void h_close(void *c, uint8_t r) { (void)c; (void)r; }
static void h_record(void *c, const char *l) { (void)c; (void)l; }

/* A reader that, like a DataView, must not read past the end: it says so instead of returning garbage. */
typedef struct {
	const uint8_t *b;
	size_t len, i;
	int past_end;
} rd;

static unsigned rd_u16(rd *r)
{
	if (r->i + 2 > r->len) {
		r->past_end++;
		r->i = r->len;
		return 0;
	}
	unsigned v = (unsigned)(r->b[r->i] << 8) | r->b[r->i + 1];
	r->i += 2;
	return v;
}

/* A string: u16 length + bytes. Returns the length, copies up to cap-1 bytes. */
static size_t rd_str(rd *r, char *out, size_t cap)
{
	unsigned n = rd_u16(r);
	if (r->past_end)
		return 0;
	if (r->i + n > r->len) {
		r->past_end++;
		r->i = r->len;
		return 0;
	}
	size_t k = n < cap - 1 ? n : cap - 1;
	memcpy(out, r->b + r->i, k);
	out[k] = 0;
	r->i += n;
	return n;
}

int main(void)
{
	rcp_hooks g;
	rcp_session *s;
	char key[64][64], val[64][128];
	unsigned declared, pairs = 0;
	rd r;
	int seen_codec = 0, seen_depth = 0, seen_audio = 0, seen_clip = 0, seen_bench = 0, dup = 0;

	memset(&g, 0, sizeof g);
	g.send_msg = h_send;
	g.close = h_close;
	g.record = h_record;
	s = rcp_open(&g, "192.0.2.7", 1000);
	CHECK(s != NULL, "rcp_open failed");
	if (!s)
		return 1;

	send_here_i_am(s);
	CHECK(sent == 1, "HERE_I_AM sent %d times, expected once (body too big for the writer?)", sent);
	CHECK(got_n >= 6, "message of %zu bytes (< header)", got_n);
	if (sent != 1 || got_n < 6)
		return 1;

	/* header: u16 type, u32 body length */
	CHECK(got[0] == 0x00 && got[1] == 0x02, "type %02x%02x, expected 0002 (HERE_I_AM)", got[0], got[1]);
	{
		uint32_t L = ((uint32_t)got[2] << 24) | ((uint32_t)got[3] << 16) | ((uint32_t)got[4] << 8) | got[5];
		CHECK((size_t)L == got_n - 6, "header declares %u body bytes, %zu follow", L, got_n - 6);
	}

	r = (rd){got + 6, got_n - 6, 0, 0};
	CHECK(rd_u16(&r) == (unsigned)RCP_VERSION, "version is not RCP_VERSION");
	declared = rd_u16(&r);
	CHECK(r.past_end == 0, "the fixed part (version, count) is already cut");
	CHECK(declared >= 1 && declared <= 64, "declared count %u out of any sane range", declared);

	for (unsigned k = 0; k < declared && k < 64 && !r.past_end; k++) {
		rd_str(&r, key[k], sizeof key[k]);
		rd_str(&r, val[k], sizeof val[k]);
		if (!r.past_end)
			pairs++;
	}
	/* THE regression: n declared > pairs written ⇒ the page's DataView reads past the end. */
	CHECK(r.past_end == 0, "reading the %u declared pairs went PAST THE END of the message (%u read)", declared, pairs);
	CHECK(pairs == declared, "declared %u capabilities, %u pairs read", declared, pairs);
	CHECK(r.i == r.len, "%zu bytes LEFT OVER after the %u-th pair (a pair written but not counted)", r.len - r.i, pairs);

	for (unsigned k = 0; k < pairs; k++) {
		for (unsigned j = 0; j < k; j++)
			if (strcmp(key[j], key[k]) == 0)
				dup++;
		if (!strcmp(key[k], "video.codec")) seen_codec++;
		else if (!strcmp(key[k], "video.depth")) seen_depth++;
		else if (!strcmp(key[k], "audio.codec")) seen_audio++;
		else if (!strcmp(key[k], "clipboard.text")) seen_clip++;
		else if (!strcmp(key[k], "bench.mark")) {
			seen_bench++;
			CHECK(!strcmp(val[k], "yes") || !strcmp(val[k], "no"), "bench.mark = «%s»", val[k]);
		}
		CHECK(key[k][0] != 0, "pair %u has an empty name", k);
	}
	CHECK(dup == 0, "%d capability names appear twice", dup);
	CHECK(seen_codec == 1 && seen_depth == 1 && seen_audio == 1 && seen_clip == 1,
	      "the four product capabilities once each: codec %d depth %d audio %d clipboard %d",
	      seen_codec, seen_depth, seen_audio, seen_clip);
#ifdef REMOTIX_BENCH
	CHECK(seen_bench == 1, "BENCH build: bench.mark must be declared once (%d)", seen_bench);
#else
	CHECK(seen_bench == 0, "product build: bench.mark must NOT be declared (%d)", seen_bench);
#endif

	rcp_free(s);
	printf("here-i-am: %d checks, %d failed (%s build, %u capabilities declared)\n", checks, bad,
#ifdef REMOTIX_BENCH
	       "BENCH",
#else
	       "product",
#endif
	       declared);
	return bad ? 1 : 0;
}
