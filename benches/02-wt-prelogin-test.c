/* 02-wt-prelogin-test.c — before the login a stranger can no longer fill
 * root's log from one connection, nor lend the owner's name a size it does
 * not have (holistic review of webtransport.c, 15 Oct 2026).
 *
 * In the build container, from src/ (the product's objects, then the test
 * linked against all of them except main.o and webtransport.o):
 *
 *   make TWIN=none
 *   gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags gio-2.0 \
 *       libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 \
 *       xkbcommon wayland-client gbm) -o /tmp/wpl \
 *       ../benches/02-wt-prelogin-test.c \
 *       $(ls *.o | grep -v -e '^main.o$' -e '^webtransport.o$') \
 *       -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm \
 *       $(pkg-config --libs gio-2.0 libpipewire-0.3 libva libva-drm \
 *       libei-1.0 xkbcommon wayland-client gbm opus vulkan) -ldl && /tmp/wpl
 *
 * ⚠ `webtransport.c` is INCLUDED (the seam of 02-wt-judgments-test.c); its log
 *   lines and its clock (`log_now_ms`) are interposed by macros defined after
 *   log.h, so only webtransport.c's own calls see them.  No QUIC connection:
 *   `wt_new(NULL, …)`, and the RCP sessions are real ones (rcp.o) driven here.
 *
 *   1. one connection that never logged in: of 100 RCP lines 20 are written
 *      (WT_PRELOGIN_BURST), the BAN and the failed attempt always are;
 *   2. a second connection from the same address shares that budget; another
 *      address has its own;
 *   3. once the 10 s window has passed: ONE line counts the hidden ones (81),
 *      and a later flood of 40 then a quiet window is 20 + the count + the line;
 *   4. a connection that logged in writes every line;
 *   5. a connection that never logged in: the 3rd WebTransport session and the
 *      9th request outside one close it (H3_EXCESSIVE_LOAD); a logged-in one
 *      never; a second session on a connection that has one is refused and
 *      counted (here as the 9th request: closed);
 *   6. wt_max_size_of() and wt_tenants_served() count only sessions that
 *      LOGGED IN: a stranger still waiting for PAM under the owner's name, with
 *      a bigger max_size, changes neither.
 *
 * Exit status: 0 green, 1 red, 3 not all checks ran. */
#define _GNU_SOURCE
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "log.h"

static void rxt_says_of(const char *file, int text_line, const char *area, const char *chi,
                        const char *fmt, ...);
static void rxt_detail_of(const char *file, int text_line, const char *area, const char *chi,
                          const char *fmt, ...);
static uint64_t rxt_now(void);
#define log_says_of_in rxt_says_of
#define log_detail_of_in rxt_detail_of
#define log_now_ms rxt_now
#include "webtransport.c"
#undef log_now_ms
#undef log_detail_of_in
#undef log_says_of_in

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 18

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

/* ── a real RCP session, as `rcp_start()` would hold it, driven to a state ── */
enum { T_HELLO = 0x0001, T_CREDENTIALS = 0x0003 };
static void o_send(void *ctx, const uint8_t *d, size_t n) { (void)ctx; (void)d; (void)n; }
static void o_close(void *ctx, uint8_t r) { (void)ctx; (void)r; }
static void o_log(void *ctx, const char *l) { (void)ctx; if (getenv("WPL_LOG")) fprintf(stderr, "rcp> %s\n", l); }
static bool o_verify(void *ctx, const char *u, const char *p) { (void)ctx; (void)u; (void)p; return false; }
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
	hooks_rcp.verify = o_verify;
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
	ngtcp2_ccerr e1, e2, e3, e4, e5, e6, e7;
	setvbuf(stdout, NULL, _IONBF, 0);
	memset(&e1, 0, sizeof e1);
	e2 = e3 = e4 = e5 = e6 = e7 = e1;

	printf("  1. one connection, never logged in\n");
	wt *w = wt_new(NULL, &e1, "[192.0.2.10]:4001", NULL);
	says = 0;
	for (int k = 0; k < 100; k++)
		hook_log(w, "HELLO from a stranger");
	require(says == WT_PRELOGIN_BURST, "of 100 lines, the first 20 are written");
	hook_log(w, "⛔ BANNED address [192.0.2.10] for 12 hours");
	hook_log(w, "failed attempt from [192.0.2.10]: 2 of 3");
	require(says == WT_PRELOGIN_BURST + 2, "the BAN and the failed attempt are written all the same");

	printf("  2. the budget is the address's\n");
	wt *w2 = wt_new(NULL, &e2, "[192.0.2.10]:4002", NULL);
	hook_log(w2, "HELLO from the same place");
	require(says == WT_PRELOGIN_BURST + 2, "a new connection from the same address: held back too");
	wt *w3 = wt_new(NULL, &e3, "[198.51.100.9]:4001", NULL);
	hook_log(w3, "HELLO from elsewhere");
	require(says == WT_PRELOGIN_BURST + 3, "another address: its own budget");

	printf("  3. the window passes\n");
	fake_now += WT_PRELOGIN_WINDOW_MS;
	says = 0;
	hook_log(w, "HELLO again");
	require(says == 2, "one count line, then the line");
	require(strstr(summary, "81 more lines before the login") != NULL,
	        "the count says 81 (80 of this connection + 1 of the other from the same address)");
	fake_now += WT_PRELOGIN_WINDOW_MS;
	says = 0;
	for (int k = 0; k < 40; k++)
		hook_log(w, "y");
	fake_now += WT_PRELOGIN_WINDOW_MS;
	hook_log(w, "z");
	require(strstr(last, "z") && says == WT_PRELOGIN_BURST + 2,
	        "a flood of 40 then a quiet window: 20 + the count + the line");

	printf("  4. a connection that logged in\n");
	wt *w4 = wt_new(NULL, &e4, "[192.0.2.10]:4003", NULL);
	w4->was_logged_in = true;
	says = 0;
	for (int k = 0; k < 50; k++)
		hook_log(w4, "a logged-in line");
	require(says == 50, "every line written, the address's budget does not apply");

	printf("  5. sessions and requests before the login\n");
	wt *w5 = wt_new(NULL, &e5, "[203.0.113.5]:1", NULL);
	require(!prelogin_excess(w5, true) && !prelogin_excess(w5, true),
	        "two sessions on one connection: allowed");
	require(prelogin_excess(w5, true) && e5.error_code == NGHTTP3_H3_EXCESSIVE_LOAD,
	        "the third: the connection is closed with H3_EXCESSIVE_LOAD");
	wt *w6 = wt_new(NULL, &e6, "[203.0.113.6]:1", NULL);
	bool all_ok = true;
	for (int k = 0; k < WT_PRELOGIN_REQUESTS_MAX; k++)
		all_ok &= !prelogin_excess(w6, false);
	require(all_ok && prelogin_excess(w6, false) && e6.error_code == NGHTTP3_H3_EXCESSIVE_LOAD,
	        "8 requests outside the session allowed, the 9th closes it");
	w4->sessions_opened = 50;
	require(!prelogin_excess(w4, true) && !prelogin_excess(w4, false),
	        "⛔ the check that says NO: a logged-in connection is never closed for this");
	{
		/* a second session on a connection that has one: refused, counted */
		wt *w7 = wt_new(NULL, &e7, "[203.0.113.7]:1", NULL);
		request *r = request_find(w7, 4, true);
		w7->session = 0;
		w7->stray_requests = WT_PRELOGIN_REQUESTS_MAX;
		snprintf(r->method, sizeof r->method, "CONNECT");
		snprintf(r->protocol, sizeof r->protocol, "webtransport");
		snprintf(r->uri, sizeof r->uri, "/rcp/1");
		details = 0;
		require(open_session(w7, r) == NGHTTP3_ERR_CALLBACK_FAILURE && details == 1
		        && e7.error_code == NGHTTP3_H3_EXCESSIVE_LOAD,
		        "a second session on a connection that has one: refused as chatter, and "
		        "counted (here the 9th: closed)");
		snprintf(r->uri, sizeof r->uri, "/elsewhere");
		w7->session = -1;
		details = 0;
		says = 0;
		require(open_session(w7, r) == NGHTTP3_ERR_CALLBACK_FAILURE && details == 1 && says <= 1,
		        "a refused path is a chatter line, not a normal one");
	}

	printf("  6. a claimed name lends nothing to the owner\n");
	{
		const uint64_t T = 7000000;
		wt *owner = wt_new(NULL, &e1, "[192.0.2.50]:1", NULL);
		wt *stranger = wt_new(NULL, &e2, "[192.0.2.51]:1", NULL);
		uint32_t l = 0, a = 0;
		owner->rcp = session("[192.0.2.50]:1", "anna", "1280x720", true, T);
		stranger->rcp = session("[192.0.2.51]:1", "anna", "3840x2160", false, T);
		require(owner->rcp && rcp_logged_in(owner->rcp) && stranger->rcp
		        && !rcp_logged_in(stranger->rcp) && strcmp(rcp_user(stranger->rcp), "anna") == 0,
		        "the owner logged in, the stranger waits for PAM under the same name");
		require(wt_max_size_of("anna", &l, &a) && l == 1280 && a == 720,
		        "wt_max_size_of(): the owner's 1280x720, not the stranger's 3840x2160");
		require(wt_tenants_served() == 1, "wt_tenants_served(): one tenant, not two");
		stranger->rcp = NULL;
		owner->rcp = NULL;
	}
	require(true, "the end was reached");
	(void)w2;
	(void)w3;

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
