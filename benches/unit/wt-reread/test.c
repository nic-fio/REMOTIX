/* test.c — second reading of src/webtransport.c (rilettura-webtransport.md, W1-W6): the connection BEFORE the login.
 *
 * ⚠ `webtransport.c` is INCLUDED (the method of benches/unit/wt-prelogin/test.c): its log lines, its clock (`log_now_ms`) and the connection's timestamp
 *   (`ngtcp2_conn_get_timestamp`, there is no QUIC connection here: `wt_new(NULL, …)`) are interposed by macros defined after the headers.  The RCP sessions are real.
 *
 *   W1  the three lines of the capsule parser (an invalid CLOSE: two lines per 7-byte capsule; a capsule beyond the cap; the CLOSE itself) go through the budget of the connection before
 *       the login — 100 capsules write at most WT_PRELOGIN_BURST lines; a logged-in connection writes them all;
 *   W2  the same for the line of every client unidirectional stream (and the "no control channel" one);
 *   W3  close_session() is idempotent: a second call re-arms nothing and writes nothing (the first reason and deadline stand);
 *   W4  network_cycle() writes nothing for a connection without a control channel (it returns before touching the QUIC connection);
 *   W5  wt_logged_in() is false again once the control channel / the session has closed (wt_stream_closed());
 *   W6  close_now() with the session stream already closed (session == -1) queues nothing.
 *
 * BUILD AND RUN (a full build of the product first, about as long as `make`: the test links every object but main.o and webtransport.o; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=2 --memory=2g -v "$PWD:/albero:ro" localhost/remotix-costruzione sh -c '
 *     mkdir /tmp/w && cp -a /albero/src /albero/benches /tmp/w/ && cd /tmp/w/src &&
 *     { make clean >/dev/null 2>&1; true; } &&
 *     { make -j2 TWIN=none >/tmp/make.log 2>&1 || { tail -40 /tmp/make.log; exit 1; }; } &&
 *     gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon wayland-client gbm) \
 *         -o /tmp/wrr ../benches/unit/wt-reread/test.c $(ls *.o | grep -v -e "^main.o$" -e "^webtransport.o$") \
 *         -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
 *         $(pkg-config --libs gio-2.0 libpipewire-0.3 libva libva-drm libei-1.0 xkbcommon wayland-client gbm opus vulkan) -ldl &&
 *     /tmp/wrr'
 * Exit code 0 green, 1 red, 3 not all checks ran.
 */
#define _GNU_SOURCE
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <ngtcp2/ngtcp2.h>
#include "log.h"

static void rxt_says_of(const char *file, int text_line, const char *area, const char *chi,
                        const char *fmt, ...);
static void rxt_detail_of(const char *file, int text_line, const char *area, const char *chi,
                          const char *fmt, ...);
static uint64_t rxt_now(void);
#define log_says_of_in rxt_says_of
#define log_detail_of_in rxt_detail_of
#define log_now_ms rxt_now
#define ngtcp2_conn_get_timestamp rxt_ts
static uint64_t rxt_ts(ngtcp2_conn *c);
#define ngtcp2_conn_extend_max_stream_offset rxt_ext_stream   /* no QUIC connection here: the credit calls are counted and dropped */
#define ngtcp2_conn_extend_max_offset rxt_ext_conn
static int rxt_ext_stream(ngtcp2_conn *c, int64_t id, uint64_t n) { (void)c; (void)id; (void)n; return 0; }
static int rxt_ext_conn(ngtcp2_conn *c, uint64_t n) { (void)c; (void)n; return 0; }
#include "webtransport.c"
#undef ngtcp2_conn_get_timestamp
#undef ngtcp2_conn_extend_max_stream_offset
#undef ngtcp2_conn_extend_max_offset
#undef log_now_ms
#undef log_detail_of_in
#undef log_says_of_in

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 11

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

static int says, details;
static char last[2048], summary[2048];
static uint64_t fake_now = 5000000;

static void rxt_says_of(const char *file, int text_line, const char *area, const char *chi,
                        const char *fmt, ...)
{
	va_list ap;
	(void)file; (void)text_line; (void)area; (void)chi;
	va_start(ap, fmt);
	vsnprintf(last, sizeof last, fmt, ap);
	va_end(ap);
	if (strstr(last, "more lines before the login"))
		snprintf(summary, sizeof summary, "%s", last);
	says++;
}
static void rxt_detail_of(const char *file, int text_line, const char *area, const char *chi,
                          const char *fmt, ...)
{
	(void)file; (void)text_line; (void)area; (void)chi; (void)fmt;
	details++;
}
static uint64_t rxt_now(void) { return fake_now; }
static uint64_t ts_ns = 1000ULL * NGTCP2_SECONDS;
static uint64_t rxt_ts(ngtcp2_conn *c) { (void)c; return ts_ns; }

/* ── a real RCP session, as `rcp_start()` would hold it, driven to a state ── */
enum { T_HELLO = 0x0001, T_CREDENTIALS = 0x0003 };
static void o_send(void *ctx, const uint8_t *d, size_t n) { (void)ctx; (void)d; (void)n; }
static void o_close(void *ctx, uint8_t r) { (void)ctx; (void)r; }
static void o_log(void *ctx, const char *l) { (void)ctx; if (getenv("WPL_LOG")) fprintf(stderr, "rcp> %s\n", l); }
static bool o_ask(void *ctx, const char *u, const char *p, uint64_t *t)
{
	(void)ctx; (void)u; (void)p;
	*t = 77;
	return true;
}
static size_t put_str(uint8_t *b, size_t i, const char *t)
{
	size_t n = strlen(t);
	b[i++] = (uint8_t)(n >> 8);
	b[i++] = (uint8_t)(n & 0xFF);
	memcpy(b + i, t, n);
	return i + n;
}
static size_t wrap(uint8_t *b, uint16_t kind, const uint8_t *body, size_t len)
{
	b[0] = (uint8_t)(kind >> 8);
	b[1] = (uint8_t)(kind & 0xFF);
	b[2] = (uint8_t)((len >> 24) & 0xFF);
	b[3] = (uint8_t)((len >> 16) & 0xFF);
	b[4] = (uint8_t)((len >> 8) & 0xFF);
	b[5] = (uint8_t)(len & 0xFF);
	memcpy(b + 6, body, len);
	return 6 + len;
}
static rcp_hooks hooks_rcp;
/* HELLO with `max_size`, CREDENTIALS for `user`; `login` true: PAM's yes and the fixed second */
static rcp_session *session(const char *provenance, const char *user, const char *max_size,
                            bool login, uint64_t now)
{
	const char *entries[] = {
	    "video.codec", "hevc,av1", "video.depth", "8,10", "audio.codec", "opus,pcm",
	    "video.level", "5.1", "video.max_size", max_size, "clipboard.text", "yes",
	    "input.touch", "no", "client.name", "02-wt-prelogin-test", NULL};
	uint8_t body[1100], frame[1200];
	size_t i = 0;
	int n = 0;
	memset(&hooks_rcp, 0, sizeof hooks_rcp);
	hooks_rcp.send_msg = o_send;
	hooks_rcp.close = o_close;
	hooks_rcp.record = o_log;
	hooks_rcp.ask_verify = o_ask;
	rcp_session *s = rcp_open(&hooks_rcp, provenance, now);
	if (!s)
		return NULL;
	for (int k = 0; entries[k]; k += 2)
		n++;
	body[i++] = 0;
	body[i++] = 1;
	body[i++] = (uint8_t)(n >> 8);
	body[i++] = (uint8_t)(n & 0xFF);
	for (int k = 0; entries[k]; k += 2) {
		i = put_str(body, i, entries[k]);
		i = put_str(body, i, entries[k + 1]);
	}
	rcp_receive(s, frame, wrap(frame, T_HELLO, body, i), now);
	i = put_str(body, 0, user);
	i = put_str(body, i, "a-password");
	rcp_receive(s, frame, wrap(frame, T_CREDENTIALS, body, i), now);
	if (login) {
		rcp_verdict(s, 77, true, now + 300);
		rcp_time(s, now + 1001);
	}
	return s;
}

int main(void)
{
	setvbuf(stdout, NULL, _IONBF, 0);

	printf("  W1. the capsule parser's lines before the login\n");
	{
		ngtcp2_ccerr e;
		uint8_t close_bad[7] = { 0x68, 0x43, 0x04, 0, 0, 0, 0 };                 /* CLOSE_WEBTRANSPORT_SESSION, code 0: invalid -> two lines */
		static uint8_t big[4 + 5000] = { 0x52, 0x34, 0x53, 0x88 };                 /* type 0x1234, length 5000: beyond the cap -> "SKIPPED" */
		wt *a, *b;

		memset(&e, 0, sizeof e);
		a = wt_new(NULL, &e, "[192.0.2.31]:4001", NULL);
		a->session = 0;
		says = 0;
		for (int k = 0; k < 100; k++)
			capsule(a, 0, close_bad, sizeof close_bad);
		require(says > 0 && says <= WT_PRELOGIN_BURST, "100 invalid CLOSE capsules before the login: at most WT_PRELOGIN_BURST lines (before: 200)");
		says = 0;
		for (int k = 0; k < 100; k++)
			capsule(a, 0, big, sizeof big);
		require(says <= 2, "100 capsules beyond the cap: the budget is spent, nothing (or the summary) more");
		b = wt_new(NULL, &e, "[198.51.100.31]:4001", NULL);
		b->session = 0;
		b->rcp = session("[198.51.100.31]:4001", "anna", "1920x1080", true, fake_now);
		require(b->rcp && wt_logged_in(b), "a connection that logged in");
		says = 0;
		for (int k = 0; k < 10; k++)
			capsule(b, 0, big, sizeof big);
		require(says == 10, "and it writes every one of its 10 \"SKIPPED\" lines");
	}

	printf("  W2. one line per unidirectional stream of the client\n");
	{
		ngtcp2_ccerr e;
		wt *a, *b;
		bytes held;
		uint8_t pre[5] = { 0x40, 0x54, 0x00, 0x01, 0x00 };                        /* WebTransport stream (0x54), session 0, kind 0x0100: channel 0x01 (input) */

		memset(&e, 0, sizeof e);
		a = wt_new(NULL, &e, "[192.0.2.32]:4001", NULL);
		says = 0;
		for (int k = 0; k < 100; k++) {
			memset(&held, 0, sizeof held);
			(void)dispatch_uni(a, 2 + 4 * k, pre, sizeof pre, true, &held);
		}
		require(says > 0 && says <= WT_PRELOGIN_BURST + 1, "100 unidirectional streams before the login: at most WT_PRELOGIN_BURST lines (before: 100)");
		b = wt_new(NULL, &e, "[198.51.100.32]:4001", NULL);
		b->rcp = session("[198.51.100.32]:4001", "anna", "1920x1080", true, fake_now);
		says = 0;
		for (int k = 0; k < 30; k++) {
			memset(&held, 0, sizeof held);
			(void)dispatch_uni(b, 2 + 4 * k, pre, sizeof pre, true, &held);
		}
		require(says >= 30, "a logged-in connection writes its line for every stream (30)");
	}

	printf("  W3. close_session() is idempotent\n");
	{
		ngtcp2_ccerr e;
		wt *a;
		uint64_t first_deadline, first_since;
		int first_reason;

		memset(&e, 0, sizeof e);
		a = wt_new(NULL, &e, "[192.0.2.33]:4001", NULL);
		a->session = 0;
		close_session(a, 5);
		first_reason = a->closing;
		first_deadline = a->closing_deadline;
		first_since = a->closing_since;
		require(first_reason == 5 && first_deadline > ts_ns, "the first call arms the reason and the 3 s deadline");
		says = 0;
		ts_ns += 400ULL * NGTCP2_MILLISECONDS;
		close_session(a, 7);
		require(a->closing == first_reason && a->closing_deadline == first_deadline && a->closing_since == first_since,
		        "400 ms later a second call keeps the FIRST reason and re-arms neither the wait nor the deadline");
		require(says == 0, "and writes no line");
		for (int k = 0; k < 50; k++) {
			ts_ns += 400ULL * NGTCP2_MILLISECONDS;
			close_session(a, 9);
		}
		require(a->closing_deadline == first_deadline && says == 0, "20 s of offending streams every 400 ms: the deadline is still the first one (the closure can mature)");
	}

	printf("  W4. network_cycle() without a control channel\n");
	{
		ngtcp2_ccerr e;
		wt *a;

		memset(&e, 0, sizeof e);
		a = wt_new(NULL, &e, "[192.0.2.34]:4001", NULL);
		a->conn = (ngtcp2_conn *)(uintptr_t)0x10;   /* never dereferenced: network_cycle() must leave before it asks ngtcp2 anything */
		says = 0;
		network_cycle(a, 5000);
		network_cycle(a, 7000);
		require(says == 0 && a->network_logged_ms == 0, "no control channel: no quic-net line and nothing armed");
		a->conn = NULL;
	}

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	return failures ? 1 : (passed == EXPECTED_CHECKS ? 0 : 3);
}
