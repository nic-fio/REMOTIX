/*
 * page.c — see page.h.
 */
#include "page.h"

#include "rcp.h"
#include "log.h"

#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <linux/tcp.h>
#include <stddef.h>
#include <unistd.h>

#include <openssl/err.h>
#include <openssl/rand.h>

#define MAX_CLIENTS PAGE_MAX_CLIENTS
/* ⛔⭐ THE TCP LISTENER'S CLOCKS AND CAPS — 15 Oct 2026, a pre-login denial
 *     of service.  Before these lines a slot was freed ONLY by activity on its
 *     socket: 32 TCP connections that send nothing took all 32 slots for ever,
 *     and nobody could load the login page any more.  ⇒ Every client now has a
 *     birth time and two deadlines, and `page_expired()` is called by the main
 *     loop at every pass (like `transport_expired()`), activity or not.
 *
 *   · PAGE_REQUEST_MS — from accept to a WHOLE request (TLS handshake + the
 *     request headers).  A browser needs well under a second; 10 s leaves room
 *     for a phone on a bad line and for the certificate-warning case, which
 *     fails the handshake at once anyway.
 *   · While the response is written there is NO absolute deadline (review
 *     of 3ed5091f, same day): the page is ~907 KB uncompressed, and 60 s from
 *     accept cut every phone under ~125 kbit/s, every time.  The deadline
 *     follows PROGRESS instead: closed when no byte was taken for
 *     PAGE_STALL_MS (60 s: retransmission backoff, a tunnel, a handover —
 *     15 s cut phones there; a stalled writer is evictable after
 *     PAGE_EVICT_AGE_MS anyway when the table is full), or when, after PAGE_RATE_GRACE_MS, the average since the
 *     response began is below PAGE_RATE_FLOOR (2 KB/s = 16 kbit/s: the whole
 *     page within ~7.5 min).  A slow phone that keeps reading is never cut.
 *   · PAGE_PER_ADDRESS — at most this many connections at once from one
 *     address, keyed by `rcp_key_address()` (IPv4 per address, IPv6 per /64):
 *     one machine can no longer take every slot.  A page load needs one
 *     connection at a time (`Connection: close`, one GET plus `/fingerprint`);
 *     4 leaves room for a browser's speculative preconnects and a few devices
 *     behind one NAT.
 *   · PAGE_PER_48 — and at most this many from one IPv6 /48 (as transport.c):
 *     one subscriber holds a whole /48, that is 65536 /64 keys.
 *   · And when all slots are taken, one is freed to make room — by FAIR
 *     SHARE (third review, 15 Oct 2026).  A client's GROUP is its IPv6 /48
 *     for a real IPv6 peer, its address otherwise.  The victim is taken from
 *     a group holding the MOST live slots (every client counts), preferring
 *     there clients without a whole request, then writers PAGE_EVICT_AGE_MS
 *     or more into a response whatever their speed, then fresh writers; at
 *     random among equals — and when every group holds one slot, the OLDEST
 *     (refusing there would be a cheap lockout: one slot each from
 *     MAX_CLIENTS addresses).  The newcomer is REFUSED only if its own group
 *     would then hold MORE than the largest.  See `fair_victim()`.
 *     ⛔ What it replaced, measured: «the globally oldest pre-request
 *        client» let 8 addresses doing bare TCP connects evict a real browser
 *        mid-handshake after 39 connects, in 4 ms; and «writers under
 *        32 KB/s» let readers at 33 KB/s hold the table for ever.  With fair
 *        share an attacker can only push out slots of groups LARGER than his
 *        own, that is his own kind, never the lone browser.
 *     ⚠ The price: a crowd behind ONE address (a CGNAT, an office NAT, a
 *       carrier /48) is one group — see `DECISIONS.md` §11.44.
 *   · Expired and evicted clients are closed with a RESET (`SO_LINGER`
 *     {1, 0}): a gentle close would leave the kernel holding their unsent
 *     data in an orphan socket for minutes.  A response that ends normally
 *     keeps the gentle close.
 *
 * ⛔ The ban is NOT checked at accept: §4.4-bis wants the banned address to
 *    SEE the page and the sentence «attempts exhausted» — a refusal at accept
 *    would be exactly the silence it forbids. */
#define PAGE_REQUEST_MS 10000u
#define PAGE_STALL_MS 60000u
#define PAGE_RATE_GRACE_MS 20000u
#define PAGE_RATE_FLOOR 2048u /* bytes per second */
#define PAGE_PER_ADDRESS 4
#define PAGE_PER_48 8
#define PAGE_EVICT_AGE_MS 5000u
/* At most this many accepts per `accept_page()` call (refused ones included). */
#define PAGE_ACCEPTS_PER_CALL 32
/* The «GET / from …» line: at most this many per address per window; the
 * rest are counted in the summary line. */
#define PAGE_LINES_PER_ADDRESS 5
#define PAGE_LINES_WINDOW_MS 10000u
#define PAGE_LINES_KEYS 16
/* One summary line, at most every this many ms (as transport.c's pressure line). */
#define PAGE_REFUSAL_LOG_MS 10000u
#define MAX_REQUEST 8192

/* ⛔ THE TWO CROSS-ORIGIN ISOLATION HEADERS, PLUS THE THIRD THEY IMPLY.
 *
 *    `SPECS.md` §11.5 makes them a PRODUCT constraint: without them, on
 *    Firefox and Safari the page's timers fall on a 1 ms grid — against a
 *    ceiling of 50 (`STUDIES.md` §web §6.3, P6) — and shared memory does not exist.
 *
 * ⚠ And they go on EVERY response, not only on the page: this is what «changes
 *   how the server serves every resource» means in bytes. */
#define ISOLATION                                                             \
	"Cross-Origin-Opener-Policy: same-origin\r\n"                              \
	"Cross-Origin-Embedder-Policy: require-corp\r\n"                           \
	"Cross-Origin-Resource-Policy: same-origin\r\n"

/* ⛔ THE HEADERS OF THE HTML PAGE ONLY — page audit, 24 Oct 2026.
 *
 *    Until now the page was served with the isolation pair and `nosniff` and nothing else: it
 *    could be framed by any site (clickjacking on a form with a password, on a page that forwards
 *    keys and the clipboard) and no policy limited what a future bug of injection could do.
 *    ⚠ They go on the HTML response and NOT on every response: `/fingerprint` is JSON.
 *
 *    Each directive is what THE PAGE REALLY USES (grep of page.html, same date) — a directive
 *    that is wrong breaks the page, so where in doubt the wider form is chosen and SAID:
 *
 *    default-src 'self'       the floor: nothing else is loaded from outside this origin.
 *    script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'
 *                             the page is ONE inline <script> (no nonce possible: the file is
 *                             static), and the Opus decoder is WebAssembly instantiated from
 *                             bytes (`opus_wasm_prepare()`): without 'wasm-unsafe-eval' the
 *                             engine refuses to compile it and the audio silently falls to
 *                             AudioDecoder.  No `eval`, no `new Function` in the page.
 *    style-src 'self' 'unsafe-inline'
 *                             one inline <style>, and `style=` / `style.cssText` in the script.
 *    img-src 'self' data: blob:
 *                             the grain and the marker are `url("data:image/svg+xml…")` in the CSS,
 *                             and the remote cursor is `cursor: url(data:image/png…)`.
 *    media-src blob:          MSE: `<video>.src = URL.createObjectURL(MediaSource)`.
 *    worker-src blob:         the video worker is `new Worker(URL.createObjectURL(Blob))`; a blob
 *                             worker inherits this policy, so the WASM line above covers it too.
 *    connect-src 'self' https:
 *                             `fetch("/fingerprint")` is same-origin, and WebTransport opens
 *                             `https://host:port/rcp/1`, which 'self' matches on the engines
 *                             that apply connect-src to WebTransport.  ⚠ NOT MEASURED on both
 *                             Chrome and Firefox, hence the `https:` next to it: the wide form
 *                             costs little (the origin that serves the page is the one that
 *                             is trusted anyway) and a narrow one that is wrong costs the whole
 *                             session.  Narrow it to 'self' once the suite has proved it.
 *    font-src 'self'          the page declares no @font-face.
 *    object-src 'none' · base-uri 'none'
 *                             no plugins, and no <base> to redirect the relative URLs.
 *    form-action 'self'       the sign-in form is handled by JS (`preventDefault`); if that ever
 *                             fails the password must not travel to another site.
 *    frame-ancestors 'none'   nobody frames this page (CSP's X-Frame-Options).
 *
 *    Referrer-Policy: no-referrer   the address of a REMOTIX box is not for third parties.
 *
 *    Permissions-Policy: the page uses the clipboard (read and write, itself only), the pointer
 *    lock, the keyboard lock and the fullscreen — those are NOT touched.  It does not use camera,
 *    microphone (no getUserMedia: the audio is only output), location, payments, USB, serial,
 *    HID, MIDI, motion sensors nor screen capture: those are turned off.  An unknown name is
 *    ignored by the engine (with a console warning), never an error. */
#define PAGE_SECURITY                                                         \
	"Content-Security-Policy: default-src 'self'; "                           \
	"script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; "                  \
	"style-src 'self' 'unsafe-inline'; "                                      \
	"img-src 'self' data: blob:; media-src blob:; worker-src blob:; "         \
	"connect-src 'self' https:; font-src 'self'; "                            \
	"object-src 'none'; base-uri 'none'; form-action 'self'; "                \
	"frame-ancestors 'none'\r\n"                                              \
	"Referrer-Policy: no-referrer\r\n"                                        \
	"Permissions-Policy: clipboard-read=(self), clipboard-write=(self), "     \
	"camera=(), microphone=(), geolocation=(), payment=(), usb=(), "          \
	"serial=(), hid=(), midi=(), accelerometer=(), gyroscope=(), "            \
	"magnetometer=(), display-capture=()\r\n"

enum phase { F_HANDSHAKE, F_READ, F_WRITE, F_DONE };

/* ⭐ A response body SHARED read-only by every client that sends it (fourth
 * review, 15 Oct 2026): before, each writing client held a private copy of
 * the ~907 KB page, and each GET made five more temporary ones — 128 slots
 * held by an attacker were ~116 MB.  Now the not-banned page is built ONCE
 * per certificate fingerprint and each client keeps its own small header, a
 * reference and an offset. */
typedef struct body {
	size_t refs;
	size_t n;
	char data[];
} body;

static body *body_new(const char *text, size_t n)
{
	body *b = malloc(sizeof *b + n);
	if (!b)
		return NULL;
	b->refs = 1;
	b->n = n;
	memcpy(b->data, text, n);
	return b;
}

static body *body_ref(body *b)
{
	if (b)
		b->refs++;
	return b;
}

static void body_unref(body *b)
{
	if (b && --b->refs == 0)
		free(b);
}

typedef struct {
	int fd;
	SSL *ssl;
	enum phase phase;
	char request[MAX_REQUEST];
	size_t nrequest;
	/* The response: `head` (this client's own: the status line and headers,
	 * and a small body) followed by `shared` (NULL, or a shared body).
	 * `nresponse` = both, `oresponse` = the offset across both. */
	char *head;
	size_t nhead;
	body *shared;
	size_t nresponse, oresponse;
	char provenance[80];
	/* `rcp_key_address(provenance)`: what PAGE_PER_ADDRESS counts. */
	char key[64];
	/* `log_now_ms()` at accept: the clock of the request deadline. */
	uint64_t born;
	/* `log_now_ms()` when the response began, and when the peer last
	 * ACKNOWLEDGED a byte of it: the clocks of the progress deadline. */
	uint64_t write_start, last_progress;
	/* Bytes of the response the PEER has acknowledged (`tcpi_bytes_acked`
	 * since the response began), sampled at every pass.  ⛔ Not
	 * `oresponse`: that counts what the KERNEL took, and its send buffer
	 * swallowed 2.6 MB on loopback from a reader that read nothing
	 * (`[M]` 15 Oct 2026) — a slow reader would look fast. */
	uint64_t acked_base, delivered;
	/* The IPv6 /48 (the first 6 bytes), when the peer is a real IPv6. */
	bool has48;
	unsigned char p48[6];
	/* ⚠ Which event OpenSSL is waiting for: without this the wrong event is
	 *   watched and the connection stays stuck until something else
	 *   expires. */
	bool wants_to_write;
} client;

struct page {
	int fd;
	SSL_CTX *ctx;
	const certificates *cert;
	char *html;
	size_t nhtml;
	client clients[MAX_CLIENTS];
	/* What was refused or closed since the last summary line. */
	unsigned refused_address, refused_48, refused_full, evicted, evicted_writing,
	         expired_request, expired_response, lines_unwritten;
	/* The per-address budget of request lines (PAGE_LINES_PER_ADDRESS). */
	struct {
		char key[64];
		uint64_t since;
		unsigned n;
	} lines[PAGE_LINES_KEYS];

	char refused_last[64];
	bool refused_ever;
	uint64_t refused_line_ms;
	/* The not-banned page, built once for `cached_fp` (see `body`). */
	body *cached;
	char cached_fp[64];
};

/* ------------------------------------------------------------------------ */

static char *read_file(const char *fpath, size_t *how_much)
{
	FILE *f = fopen(fpath, "rb");
	char *d;
	long n;
	if (!f) {
		registro_dice(LOG_PAGE, "⛔ cannot open %s: %s", fpath,
		              strerror(errno));
		return NULL;
	}
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	if (n <= 0) {
		fclose(f);
		registro_dice(LOG_PAGE, "⛔ %s is empty", fpath);
		return NULL;
	}
	d = malloc((size_t)n + 1);
	if (!d) {
		fclose(f);
		return NULL;
	}
	if (fread(d, 1, (size_t)n, f) != (size_t)n) {
		free(d);
		fclose(f);
		registro_dice(LOG_PAGE, "⛔ %s cannot be read in full", fpath);
		return NULL;
	}
	d[n] = 0;
	fclose(f);
	*how_much = (size_t)n;
	return d;
}

/* Replaces every occurrence of `sign` with `value`.  Returns a new string,
 * to be freed. */
static char *replace(const char *text, const char *sign, const char *value)
{
	size_t ls = strlen(sign), lv = strlen(value), cap, o = 0;
	const char *p = text;
	char *report;

	cap = strlen(text) + 1;
	for (const char *q = strstr(text, sign); q; q = strstr(q + ls, sign))
		cap += lv;
	report = malloc(cap);
	if (!report)
		return NULL;
	for (;;) {
		const char *q = strstr(p, sign);
		if (!q) {
			size_t r = strlen(p);
			memcpy(report + o, p, r + 1);
			return report;
		}
		memcpy(report + o, p, (size_t)(q - p));
		o += (size_t)(q - p);
		memcpy(report + o, value, lv);
		o += lv;
		p = q + ls;
	}
}

/* ------------------------------------------------------------------------ */

static void client_close(client *c)
{
	if (c->ssl) {
		SSL_free(c->ssl);
		c->ssl = NULL;
	}
	if (c->fd >= 0) {
		close(c->fd);
		c->fd = -1;
	}
	free(c->head);
	c->head = NULL;
	body_unref(c->shared);
	c->shared = NULL;
	c->nhead = c->nresponse = c->oresponse = c->nrequest = 0;
	c->phase = F_DONE;
}

/* ⛔ For an EXPIRED or EVICTED client only: a reset, not a FIN — the kernel
 *    drops what is still unsent instead of keeping it in an orphan socket
 *    for minutes.  A response that ended normally keeps the gentle close. */
static void client_abort(client *c)
{
	if (c->fd >= 0) {
		struct linger l = {1, 0};
		setsockopt(c->fd, SOL_SOCKET, SO_LINGER, &l, sizeof l);
	}
	client_close(c);
}

/* What the peer acknowledged on this socket, all told; `fallback` when the
 * kernel does not say (then `oresponse` stands in for it, less exact). */
static uint64_t tcp_acked(int fd, uint64_t fallback)
{
	struct tcp_info ti;
	socklen_t l = sizeof ti;
	memset(&ti, 0, sizeof ti);
	if (fd < 0 || getsockopt(fd, IPPROTO_TCP, TCP_INFO, &ti, &l) != 0 ||
	    l < offsetof(struct tcp_info, tcpi_bytes_acked) + sizeof ti.tcpi_bytes_acked)
		return fallback;
	return ti.tcpi_bytes_acked;
}

/* Brings `delivered` and `last_progress` up to date. */
static void sample(client *c, uint64_t now)
{
	uint64_t a = tcp_acked(c->fd, UINT64_MAX), v;
	if (a == UINT64_MAX)
		v = c->oresponse;
	else
		v = a > c->acked_base ? a - c->acked_base : 0;
	if (v > c->delivered) {
		c->delivered = v;
		c->last_progress = now;
	}
}

/* The response of `c`: the headers and `text` (copied: only small bodies
 * come this way), followed by `shared` when it is not NULL (referenced, not
 * copied; `Content-Length` covers both). */
static void compose_with(client *c, const char *state, const char *kind,
                         const char *text, size_t ntext, body *shared,
                         const char *extra)
{
	char head[2048]; /* the page's security headers (PAGE_SECURITY) are ~900 bytes */
	size_t nbody = ntext + (shared ? shared->n : 0);
	int n;

	n = snprintf(head, sizeof head,
	             "HTTP/1.1 %s\r\n"
	             "Content-Type: %s\r\n"
	             "Content-Length: %zu\r\n"
	             ISOLATION
	             "Cache-Control: no-store\r\n"
	             "X-Content-Type-Options: nosniff\r\n"
	             "Connection: close\r\n"
	             "%s"
	             "\r\n",
	             state, kind, nbody, extra ? extra : "");
	/* ⛔ 24 Oct 2026, review of the page headers: `snprintf` returns the length the line WOULD
	 *   have, not what fit.  With a longer `extra` the `memcpy` below read past the stack buffer
	 *   `head`.  Too long is OUR defect, never the client's: it is answered 500, with no `extra`
	 *   (so the retry cannot overflow again) and the sentence says why. */
	if (n < 0 || (size_t)n >= sizeof head) {
		if (extra) {
			compose_with(c, "500 Internal Server Error", "text/plain; charset=utf-8",
			             "response headers too long\n", 26, NULL, NULL);
		}
		return;
	}
	c->head = malloc((size_t)n + ntext);
	if (!c->head)
		return;
	memcpy(c->head, head, (size_t)n);
	memcpy(c->head + n, text, ntext);
	c->nhead = (size_t)n + ntext;
	c->shared = body_ref(shared);
	c->nresponse = c->nhead + (shared ? shared->n : 0);
	c->oresponse = 0;
	c->phase = F_WRITE;
	c->write_start = c->last_progress = log_now_ms();
	c->acked_base = tcp_acked(c->fd, 0);
	c->delivered = 0;
}

static void compose(client *c, const char *state, const char *kind,
                    const char *body_text, size_t nbody, const char *extra)
{
	compose_with(c, state, kind, body_text, nbody, NULL, extra);
}

/* The page with its five markers replaced.  Returns a new body, or NULL. */
static body *build_page(const page *p, bool banned, const char *warning,
                        const char *remain_txt)
{
	char *a, *b, *cc, *cc2, *d;
	body *r;

	a = replace(p->html, "__FINGERPRINT__", p->cert->fingerprint);
	if (!a)
		return NULL;
	b = replace(a, "__WARNING__", warning);
	free(a);
	if (!b)
		return NULL;
	cc = replace(b, "__BANNED__", banned ? "yes" : "no");
	free(b);
	if (!cc)
		return NULL;
	cc2 = replace(cc, "__REMAINING_MS__", remain_txt);
	free(cc);
	if (!cc2)
		return NULL;
	/* ⭐ §11.10: whether the page may send its diary — `yes` only in the
	 *   bench build, where `/diary` exists. */
	d = replace(cc2, "__DIARY__", DIARY_ON);
	free(cc2);
	if (!d)
		return NULL;
	r = body_new(d, strlen(d));
	free(d);
	return r;
}

/* `true` = the request line of `key` may be written now. */
static bool line_budget(page *p, const char *key, uint64_t now)
{
	size_t free_i = PAGE_LINES_KEYS;
	for (size_t i = 0; i < PAGE_LINES_KEYS; i++) {
		if (p->lines[i].key[0] && strcmp(p->lines[i].key, key) == 0) {
			if (now - p->lines[i].since >= PAGE_LINES_WINDOW_MS) {
				p->lines[i].since = now;
				p->lines[i].n = 0;
			}
			return ++p->lines[i].n <= PAGE_LINES_PER_ADDRESS;
		}
		if (!p->lines[i].key[0] || now - p->lines[i].since >= PAGE_LINES_WINDOW_MS)
			free_i = i;
	}
	/* ⛔ Table full of live windows: the line is NOT written (it is counted).
	 *    Reusing the oldest entry gave that address a fresh budget at once, so
	 *    17 addresses taking turns — 17 /64s, nothing for one IPv6 subscriber —
	 *    each wrote every line and the budget limited nothing (fuzz page,
	 *    15 Oct 2026).  Now at most PAGE_LINES_KEYS × PAGE_LINES_PER_ADDRESS
	 *    lines per window, and the 17th address is in the summary line. */
	if (free_i == PAGE_LINES_KEYS)
		return false;
	snprintf(p->lines[free_i].key, sizeof p->lines[free_i].key, "%s", key);
	p->lines[free_i].since = now;
	p->lines[free_i].n = 1;
	return true;
}

static void serve(page *p, client *c)
{
	/* ⛔ BOTH GROW, or nothing grows: the target is a COPY of `fpath`
	 *    taken before the cut at `?` (line below), so the real ceiling is set
	 *    by `fpath`.  ⚠ Widening `target` alone would have been a cure
	 *    that does not cure, with the air of having done it. */
	char method[16] = {0}, fpath[1024] = {0}, target[1024] = {0};
	const char *sp1, *sp2;
	char address[64];
	uint64_t remain = 0;
	bool banned;

	sp1 = memchr(c->request, ' ', c->nrequest);
	if (!sp1) {
		compose(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "request is unreadable\n", 22, NULL);
		return;
	}
	{
		size_t n = (size_t)(sp1 - c->request);
		if (n >= sizeof method)
			n = sizeof method - 1;
		memcpy(method, c->request, n);
	}
	sp2 = memchr(sp1 + 1, ' ', c->nrequest - (size_t)(sp1 + 1 - c->request));
	if (!sp2) {
		compose(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "request is unreadable\n", 22, NULL);
		return;
	}
	{
		size_t n = (size_t)(sp2 - sp1 - 1);
		if (n >= sizeof fpath)
			n = sizeof fpath - 1;
		memcpy(fpath, sp1 + 1, n);
	}

	/* ⛔⭐ THE REQUEST TARGET IS NOT THE PATH — defect B-20,
	 *     measured on 13 Aug 2026.
	 *
	 * `[M]` Before this line the comparison below was
	 * `strcmp(fpath, "/")` on the WHOLE target, query string included:
	 * `GET /` gave **200 on 166107 bytes** and `GET /?video=worker` gave
	 * **404 on 9 bytes**.  RFC 9110 §4.1 says the opposite — the query string
	 * is a component of the URI in its own right, not a piece of the path, and
	 * whoever decides what to needs looks at the path.
	 *
	 * ⛔ AND THE REAL CONSEQUENCE IS NOT THE WORKER, it is that `page.html`
	 *    has always documented TWO switches turned on from the query string —
	 *    `?canvas=desynchronized` (§6.1 of `STUDIES.md` §web) and
	 *    `?video=worker` — and **neither of them was ever reachable through
	 *    the product**: the comment pointed to a road the server closed with
	 *    a 404.  ⚠ Nobody had noticed because the benches needs the page from
	 *    a Python `http.server`, which ignores the `?` — that is, the defect
	 *    lived EXACTLY in the gap between the bench and the product.
	 *
	 * ⭐ The cure cuts, and cuts ONLY at the `?` (and the `#`, should it ever
	 *    arrive: a browser does not send the fragment, but any client can send
	 *    it, and then the path stays the path).  ⛔ The check is NOT loosened:
	 *    `/nonexistent?x=1` keeps giving 404 like `/nonexistent`, because what
	 *    changes is which string is compared, not the comparison.  ⚠ And if
	 *    the target were so long that it did not fit in `fpath`, the
	 *    truncation above takes the `?` away too: the result is a path that
	 *    matches nothing, that is 404 — the prudent outcome, not a hole.
	 *
	 * ⚠ AND THE WHOLE TARGET GOES INTO THE LOG, not the cut path: after this
	 *   cure the switches really turn on, and a log that wrote `/` for
	 *   `/?canvas=desynchronized` would make invisible precisely the only thing
	 *   this line has just made possible. */
	/* ⚠ The size is dictated by the SOURCE: this way the line holds even on
	 *   the day the two arrays were no longer the same length. */
	memcpy(target, fpath, sizeof fpath - 1);
	fpath[strcspn(fpath, "?#")] = 0;

	/* ⛔ The ban key is made by `rcp.c`, not by this file: `rcp.h` says so with
	 *    a ⛔, and the reason is that the key format is known by one module
	 *    only.  ⚠ Whoever built it on their own would look for `192.168.0.2`
	 *    where `[192.168.0.2]` is written, and the page would say «you are not
	 *    banned» to someone who is — that is, precisely to whom §4.2 wants to
	 *    see the sentence. */
	rcp_key_address(c->provenance, address, sizeof address);
	banned = rcp_banned(address, log_now_ms(), &remain);

	/* ⚠ One line per request, but at most PAGE_LINES_PER_ADDRESS per
	 *   address per PAGE_LINES_WINDOW_MS: without a budget whoever requests
	 *   the page in a loop writes the log at will.  The rest are counted in
	 *   the summary line — never dropped in silence. */
	if (line_budget(p, address, log_now_ms()))
		registro_dice(LOG_PAGE, "%s %s from %s%s", method, target,
		              c->provenance, banned ? " (address BANNED)" : "");
	else
		p->lines_unwritten++;

	/* ⛔ THE ENDPOINT FROM WHICH THE PAGE FETCHES THE UPDATED FINGERPRINT (§4.1-bis).
	 *
	 *    «A tab left open for two weeks holds the fingerprint of a
	 *    certificate that has been rotated in the meantime: on reconnection
	 *    the browser refuses, and the symptom is *it no longer connects and
	 *    does not say why*.»  Of the two cures, this is the one chosen:
	 *    reloading the page works and throws the state away.
	 *
	 * ⛔ And it does not go through RCP: the session is not open yet, so
	 *    there is no channel on which to ask.  It is fetched from the server
	 *    that served it, with an ordinary request. */
	if (strcmp(fpath, "/fingerprint") == 0) {
		char body[512];
		int n = snprintf(body, sizeof body,
		                 "{\"algorithm\":\"sha-256\",\"fingerprint\":\"%s\","
		                 "\"hex\":\"%s\",\"rotations\":%u}\n",
		                 p->cert->fingerprint, p->cert->fingerprint_hex,
		                 p->cert->rotations);
		compose(c, "200 OK", "application/json; charset=utf-8", body,
		        (size_t)n, NULL);
		return;
	}

	if (strcmp(fpath, "/") != 0 && strcmp(fpath, "/index.html") != 0) {
		compose(c, "404 Not Found", "text/plain; charset=utf-8",
		        "not here\n", 9, NULL);
		return;
	}

	/* ⛔⭐ THE BAN NOTICE — §4.4-bis, and the two findings this part paid
	 *     for on the night of 10 Aug 2026.
	 *
	 * ⛔ **B-9**: the sentence contained `l'address`, that is a
	 *    **JavaScript** escape for the apostrophe, and it was substituted in TWO
	 *    places of the page with two different syntaxes — inside a JS string
	 *    and inside a `<div>`.  In the JS string the escape became an
	 *    apostrophe; in the `<div>` it did not, because HTML does not know
	 *    `\uXXXX` escapes.  The banned owner — the one for whom §4.4-bis
	 *    wrote three normative points — read on the screen, literally,
	 *    «unblock l'address from_ server» (the Italian page of the time:
	 *    «unblock the address from the server»).
	 *    ⚠ And there was no text right for both: the cure was to separate the
	 *      two markers, not to fix the sentence.  ⛔ And there was the worse
	 *      harm: the text ended up **inside a JS string** without any
	 *      neutralisation — today it is fixed and contains no quotes, the day
	 *      a datum we do not decide ended up there that line is an injection.
	 *
	 * ⭐ The cure: the sentence lives ONLY in the HTML, and the JavaScript no
	 *    longer receives any text — it reads `data-banned` from the `<body>`.
	 *    A datum that does not enter a program cannot break it.
	 *
	 * ⛔ **R12.2**: the meter of §4.4-bis (`benches/01-b8-stopwatch.py`)
	 *    searches the document for `data-banned`, `data-remaining-ms`, the
	 *    substring «attempts esauriti» and the `id="hours"`/`id="minutes"`.  This
	 *    page had NONE of them: pointed at this server, the bench would have
	 *    given three reds **on a server that does ban**, and the red would
	 *    have landed on the wrong defendant.  ⚠ The names are not the bench's:
	 *    they are the form in which the other half of the project already
	 *    wrote the same thing, and having two would be form E2 of `REVIEWER.md`.
	 *
	 * ⚠ And the minutes are rounded UP, as in the graft: saying «0 hours
	 *   left» to someone who still has 59 minutes to wait is worse than saying
	 *   nothing. */
	{
		body *d;
		/* ⚠ 640 and not 320: the whole sentence plus the two numbers must fit
		 *   in ENTIRELY.  `[M]` night of 10 Aug 2026 — with 320 the compiler
		 *   said «directive output truncated writing 227 bytes into a
		 *   region of size between 131 and 144», and what the banned user
		 *   would have read would have ended mid-sentence.  A truncated notice
		 *   is worse than no notice: §4.4-bis wants it to be UNDERSTOOD. */
		char warning[640] = "";
		char remain_txt[32];
		unsigned long long minutes = (remain + 59999u) / 60000u;

		if (banned) {
			/* ⛔ §4.4-bis: «the page loads anyway and shows the refusal —
			 *    attempts exhausted.  Not a network error, not a silence:
			 *    whoever is banned by mistake is almost always the owner,
			 *    and must be able to understand what happened to them.» */
			snprintf(warning, sizeof warning,
			         /* ⚠ No `id` on this `<b>`: the page already has an
			          * `id="outcome"` and two elements with the same `id`
			          * would make `getElementById` take the wrong one —
			          * that is, the connection outcome would appear
			          * inside the ban notice. */
			         "<b>attempts exhausted</b>: too many failed login "
			         "attempts came from this address or network; wait a few minutes "
			         "and try again — the wait grows if it happens again "
			         "(§4.4-bis). There are still "
			         "<b id=\"hours\">%llu</b> hours and "
			         "<b id=\"minutes\">%llu</b> minutes to go. There are two "
			         "ways back in: waiting for the expiry, or with the "
			         "unblock command on the serving machine — which requires "
			         "access to that machine, and is the way for whoever "
			         "banned themselves from their own phone.",
			         minutes / 60, minutes % 60);
		}
		snprintf(remain_txt, sizeof remain_txt, "%llu",
		         (unsigned long long)remain);

		/* ⭐ Not banned: the shared page, rebuilt only when the fingerprint
		 *   changes (a rotation).  Banned: built for this request — its
		 *   remaining time is its own, and bans are rare and costly to get
		 *   (three failed logins each). */
		if (!banned) {
			if (!p->cached ||
			    strcmp(p->cached_fp, p->cert->fingerprint) != 0) {
				body *nb = build_page(p, false, warning, remain_txt);
				if (nb) {
					body_unref(p->cached);
					p->cached = nb;
					snprintf(p->cached_fp, sizeof p->cached_fp, "%s",
					         p->cert->fingerprint);
				}
			}
			d = (p->cached &&
			     strcmp(p->cached_fp, p->cert->fingerprint) == 0)
			            ? body_ref(p->cached) : NULL;
		} else {
			d = build_page(p, true, warning, remain_txt);
		}
		if (!d) {
			compose(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		compose_with(c, "200 OK", "text/html; charset=utf-8", "", 0, d, PAGE_SECURITY);
		body_unref(d);
	}
}

/* ------------------------------------------------------------------------ */

static void move_client(page *p, client *c, short events)
{
	int rv;

	(void)events;
	c->wants_to_write = false;

	if (c->phase == F_HANDSHAKE) {
		rv = SSL_accept(c->ssl);
		if (rv == 1) {
			c->phase = F_READ;
		} else {
			int e = SSL_get_error(c->ssl, rv);
			if (e == SSL_ERROR_WANT_WRITE) {
				c->wants_to_write = true;
				return;
			}
			if (e == SSL_ERROR_WANT_READ)
				return;
			/* ⚠ A failed TLS handshake is the most common thing that
			 *   happens to this listener: it is the user who has NOT yet
			 *   granted the exception on the long-lived certificate
			 *   (`RCP.md` §4.1).  It is said in a low voice, or the log
			 *   becomes unreadable at every load. */
			log_detail(LOG_PAGE,
			                   "TLS handshake failed with %s (error %d) "
			                   "— usually it is the warning about the certificate "
			                   "not yet accepted",
			                   c->provenance, e);
			ERR_clear_error();
			client_close(c);
			return;
		}
	}

	if (c->phase == F_READ) {
		for (;;) {
			size_t readings = 0;
			rv = SSL_read_ex(c->ssl, c->request + c->nrequest,
			                 sizeof c->request - c->nrequest - 1, &readings);
			if (rv != 1) {
				int e = SSL_get_error(c->ssl, rv);
				if (e == SSL_ERROR_WANT_WRITE)
					c->wants_to_write = true;
				if (e == SSL_ERROR_WANT_READ || e == SSL_ERROR_WANT_WRITE)
					return;
				client_close(c);
				return;
			}
			c->nrequest += readings;
			c->request[c->nrequest] = 0;
			if (strstr(c->request, "\r\n\r\n") ||
			    strstr(c->request, "\n\n")) {
				serve(p, c);
				break;
			}
			if (c->nrequest + 1 >= sizeof c->request) {
				/* ⛔ The length is checked before allocating, and it is
				 *    the same rule of `RCP.md` §6.1 applied to HTTP. */
				compose(c, "431 Request Header Fields Too Large",
				        "text/plain; charset=utf-8", "request headers too "
				                                     "long.\n",
				        26, NULL);
				break;
			}
		}
	}

	if (c->phase == F_WRITE) {
		while (c->oresponse < c->nresponse) {
			size_t written = 0;
			const char *from;
			size_t len;
			if (c->oresponse < c->nhead) {
				from = c->head + c->oresponse;
				len = c->nhead - c->oresponse;
			} else {
				from = c->shared->data + (c->oresponse - c->nhead);
				len = c->nresponse - c->oresponse;
			}
			rv = SSL_write_ex(c->ssl, from, len, &written);
			if (rv != 1) {
				int e = SSL_get_error(c->ssl, rv);
				if (e == SSL_ERROR_WANT_WRITE) {
					c->wants_to_write = true;
					return;
				}
				if (e == SSL_ERROR_WANT_READ)
					return;
				client_close(c);
				return;
			}
			c->oresponse += written;
		}
		SSL_shutdown(c->ssl);
		client_close(c);
	}
}

/* ------------------------------------------------------------------------ */

size_t page_descriptors(page *p, struct pollfd *dove, size_t cap)
{
	size_t n = 0;
	if (cap == 0)
		return 0;
	dove[n].fd = p->fd;
	dove[n].events = POLLIN;
	dove[n].revents = 0;
	n++;
	for (size_t i = 0; i < MAX_CLIENTS && n < cap; i++) {
		if (p->clients[i].phase == F_DONE || p->clients[i].fd < 0)
			continue;
		dove[n].fd = p->clients[i].fd;
		dove[n].events = p->clients[i].wants_to_write ? POLLOUT : POLLIN;
		dove[n].revents = 0;
		n++;
	}
	return n;
}

static bool client_active(const client *c)
{
	return c->phase != F_DONE && c->fd >= 0;
}

/* The moment the average since the response began falls under
 * PAGE_RATE_FLOOR, never before the grace: delivered / (t - write_start) <
 * floor  ⇔  t > write_start + delivered / floor. */
static uint64_t rate_deadline(const client *c)
{
	uint64_t at = c->delivered * 1000u / PAGE_RATE_FLOOR;
	return c->write_start + (at > PAGE_RATE_GRACE_MS ? at : PAGE_RATE_GRACE_MS);
}

/* The moment `c` is closed by `page_expired()`. */
static uint64_t client_deadline(const client *c)
{
	uint64_t stall, rate;
	if (c->phase != F_WRITE)
		return c->born + PAGE_REQUEST_MS;
	stall = c->last_progress + PAGE_STALL_MS;
	rate = rate_deadline(c);
	return stall < rate ? stall : rate;
}

/* The /48 of a real IPv6 peer.  ⚠ Not for the forms `rcp_key_address()` keys
 * as IPv4 or as themselves: IPv4-mapped, NAT64 (64:ff9b::/96), loopback. */
static bool key48_of(const struct sockaddr_storage *da, unsigned char p48[6])
{
	static const unsigned char nat64[12] = {0, 0x64, 0xff, 0x9b};
	const struct in6_addr *a;
	if (da->ss_family != AF_INET6)
		return false;
	a = &((const struct sockaddr_in6 *)da)->sin6_addr;
	if (IN6_IS_ADDR_V4MAPPED(a) || IN6_IS_ADDR_LOOPBACK(a) ||
	    memcmp(a->s6_addr, nat64, sizeof nat64) == 0)
		return false;
	memcpy(p48, a->s6_addr, 6);
	return true;
}

/* One line, at most every PAGE_REFUSAL_LOG_MS, with what was refused or
 * closed since the last one. */
static bool refusals_pending(const page *p)
{
	return p->refused_address || p->refused_48 || p->refused_full ||
	       p->evicted || p->evicted_writing || p->expired_request ||
	       p->expired_response || p->lines_unwritten;
}

static void refusals_report(page *p, uint64_t now)
{
	if (!refusals_pending(p))
		return;
	if (p->refused_ever && now - p->refused_line_ms < PAGE_REFUSAL_LOG_MS)
		return;
	registro_dice(LOG_PAGE,
	              "⚠ PAGE LISTENER UNDER PRESSURE%s: %u closed for not sending a "
	              "whole request within %u s; %u closed for not taking the "
	              "response (nothing for %u s, or under %u B/s after %u s); "
	              "EVICTED to make room, %d slots full, from the most crowded "
	              "address or /48: %u without a request, %u writing for %u s or "
	              "more; REFUSED: %u over %d at once from one address, %u over %d "
	              "from one IPv6 /48, %u full with no group as large as the "
	              "newcomer's would be; %u request lines not written (over %d per %u s "
	              "from one address); the last refused from %s",
	              p->refused_ever ? " in the last seconds" : "",
	              p->expired_request, PAGE_REQUEST_MS / 1000u,
	              p->expired_response, PAGE_STALL_MS / 1000u, PAGE_RATE_FLOOR,
	              PAGE_RATE_GRACE_MS / 1000u, MAX_CLIENTS, p->evicted,
	              p->evicted_writing, PAGE_EVICT_AGE_MS / 1000u,
	              p->refused_address, PAGE_PER_ADDRESS, p->refused_48,
	              PAGE_PER_48, p->refused_full, p->lines_unwritten,
	              PAGE_LINES_PER_ADDRESS, PAGE_LINES_WINDOW_MS / 1000u,
	              p->refused_last[0] ? p->refused_last : "-");
	p->refused_address = p->refused_48 = p->refused_full = 0;
	p->evicted = p->evicted_writing = p->lines_unwritten = 0;
	p->expired_request = p->expired_response = 0;
	p->refused_last[0] = 0;
	p->refused_ever = true;
	p->refused_line_ms = now;
}

/* The fair-share group: the /48 for a real IPv6 peer, the address otherwise. */
static bool same_group(const client *a, bool has48, const unsigned char *p48,
                       const char *key)
{
	if (has48 || a->has48)
		return has48 && a->has48 && memcmp(a->p48, p48, 6) == 0;
	return strcmp(a->key, key) == 0;
}

static unsigned group_size(const page *p, bool has48, const unsigned char *p48,
                           const char *key)
{
	unsigned n = 0;
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (client_active(&p->clients[i]) &&
		    same_group(&p->clients[i], has48, p48, key))
			n++;
	return n;
}

/* A number in [0, n), from RAND_bytes (fourth review: a seeded xorshift was
 * predictable).  ⚠ If RAND_bytes fails, 0 — the first candidate, which is
 * still a valid pick. */
static uint32_t random_below(uint32_t n)
{
	uint32_t r = 0;
	if (n < 2 || RAND_bytes((unsigned char *)&r, sizeof r) != 1)
		return 0;
	return r % n;
}

/* The eviction tier of a candidate: 0 = no whole request yet, 1 = writing
 * for PAGE_EVICT_AGE_MS or more, 2 = writing for less (a fresh download). */
static int tier(const client *x, uint64_t now)
{
	if (x->phase != F_WRITE)
		return 0;
	return now - x->write_start >= PAGE_EVICT_AGE_MS ? 1 : 2;
}

/* ⛔ The fair-share victim when the table is full (see the top of the file),
 *    or NULL = refuse the newcomer.  `mine` = the newcomer's group size.
 *
 *  · `best` is the size of the largest LIVE group — every client counts,
 *    fresh writers too.  ⛔ Fourth review, measured 1000/1000: computed over
 *    evictable clients only, 127 fresh writers from 32 addresses made the
 *    max a phone's group of ONE that was 5 s into its download, and every
 *    newcomer evicted the phone.
 *  · The newcomer is refused when its own group would then hold MORE than
 *    `best` (`mine + 1 > best`).
 *  · The victim comes from a group of size `best`: the lowest tier present
 *    there (no request yet, then writers ≥ 5 s, then fresh writers), at
 *    random among the equals of that tier.
 *  · ⛔ When every group holds ONE (`best` == 1), the OLDEST of the lowest
 *    tier goes instead: refusing there would be a cheap lockout — one slot
 *    per address from as many addresses as slots — and FIFO gives a real
 *    client MAX_CLIENTS - 1 arrivals of margin. */
static client *fair_victim(page *p, unsigned mine, uint64_t now)
{
	unsigned best = 0, sizes[MAX_CLIENTS];
	int low = 3;
	uint32_t ties = 0;
	client *v = NULL;

	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *x = &p->clients[i];
		sizes[i] = client_active(x) ? group_size(p, x->has48, x->p48, x->key) : 0;
		if (sizes[i] > best)
			best = sizes[i];
	}
	if (best == 0 || mine + 1 > best)
		return NULL;
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (sizes[i] == best && tier(&p->clients[i], now) < low)
			low = tier(&p->clients[i], now);
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *x = &p->clients[i];
		if (sizes[i] != best || tier(x, now) != low)
			continue;
		if (best == 1) {
			uint64_t tx = low == 0 ? x->born : x->write_start;
			uint64_t tv = !v ? UINT64_MAX : low == 0 ? v->born : v->write_start;
			if (tx < tv)
				v = x;
		} else if (random_below(++ties) == 0) {
			/* Reservoir sampling: each of the `ties` has the same chance. */
			v = x;
		}
	}
	return v;
}

static void accept_page(page *p)
{
	/* ⚠ At most MAX_CLIENTS accepts per call (refused ones included): a
	 *   backlog that refills as fast as it is drained would otherwise keep
	 *   the whole loop — QUIC, the children, PAM — inside this function.
	 *   What is left stays in the backlog, and the `poll` (level-triggered)
	 *   calls again at the next pass. */
	for (int round = 0; round < PAGE_ACCEPTS_PER_CALL; round++) {
		struct sockaddr_storage da;
		socklen_t dalen = sizeof da;
		int fd, same = 0, same48 = 0;
		client *c = NULL;
		uint64_t now;
		unsigned char p48[6];
		bool has48;
		char host[NI_MAXHOST], serv[NI_MAXSERV];
		char provenance[80], key[64];

		fd = accept4(p->fd, (struct sockaddr *)&da, &dalen, SOCK_NONBLOCK);
		if (fd < 0) {
			if (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)
				registro_dice(LOG_PAGE, "accept: %s", strerror(errno));
			return;
		}
		if (getnameinfo((struct sockaddr *)&da, dalen, host, sizeof host, serv,
		                sizeof serv, NI_NUMERICHOST | NI_NUMERICSERV) == 0)
			snprintf(provenance, sizeof provenance,
			         da.ss_family == AF_INET6 ? "[%s]:%s" : "%s:%s", host,
			         serv);
		else
			snprintf(provenance, sizeof provenance, "?");
		rcp_key_address(provenance, key, sizeof key);
		has48 = key48_of(&da, p48);
		now = log_now_ms();

		for (size_t i = 0; i < MAX_CLIENTS; i++) {
			client *x = &p->clients[i];
			if (!client_active(x)) {
				if (!c && x->phase == F_DONE && x->fd < 0)
					c = x;
				continue;
			}
			if (strcmp(x->key, key) == 0)
				same++;
			if (has48 && x->has48 && memcmp(x->p48, p48, 6) == 0)
				same48++;
		}
		/* ⛔ The per-address cap BEFORE the eviction: a crowded address
		 *    must not be able to push out somebody else's slot. */
		if (same >= PAGE_PER_ADDRESS) {
			p->refused_address++;
			snprintf(p->refused_last, sizeof p->refused_last, "%s", key);
			close(fd);
			refusals_report(p, now);
			continue;
		}
		if (same48 >= PAGE_PER_48) {
			char k48[64];
			p->refused_48++;
			snprintf(k48, sizeof k48, "%02x%02x:%02x%02x:%02x%02x::/48",
			         p48[0], p48[1], p48[2], p48[3], p48[4], p48[5]);
			snprintf(p->refused_last, sizeof p->refused_last, "%s", k48);
			close(fd);
			refusals_report(p, now);
			continue;
		}
		if (!c) {
			client *v = fair_victim(p, group_size(p, has48, p48, key), now);
			if (v) {
				if (v->phase == F_WRITE) {
					sample(v, now);
					log_detail(LOG_PAGE,
					           "all %d TCP slots taken: %s, from the most "
					           "crowded group, %llu of %zu bytes received in "
					           "%llu ms, is closed to make room for %s",
					           MAX_CLIENTS, v->provenance,
					           (unsigned long long)v->delivered, v->nresponse,
					           (unsigned long long)(now - v->write_start),
					           provenance);
					p->evicted_writing++;
				} else {
					log_detail(LOG_PAGE,
					           "all %d TCP slots taken: %s, from the most "
					           "crowded group, without a whole request for "
					           "%llu ms, is closed to make room for %s",
					           MAX_CLIENTS, v->provenance,
					           (unsigned long long)(now - v->born),
					           provenance);
					p->evicted++;
				}
				client_abort(v);
				c = v;
			}
		}
		if (!c) {
			/* ⛔ It is said — but in the summary line, not one line per
			 *    refusal: a silent refusal would look like a dead server
			 *    (`LESSONS.md` §1.9), and a line per refusal would let
			 *    whoever is refused write the log at will.
			 * ⚠ Reached when the newcomer's group would become larger than
			 *   any other (or all the others are writing for less than
			 *   PAGE_EVICT_AGE_MS). */
			p->refused_full++;
			snprintf(p->refused_last, sizeof p->refused_last, "%s", key);
			close(fd);
			refusals_report(p, now);
			continue;
		}
		memset(c, 0, sizeof *c);
		c->fd = fd;
		c->born = now;
		c->has48 = has48;
		memcpy(c->p48, p48, sizeof c->p48);
		memcpy(c->provenance, provenance, sizeof c->provenance);
		memcpy(c->key, key, sizeof c->key);

		c->ssl = SSL_new(p->ctx);
		if (!c->ssl) {
			close(fd);
			c->fd = -1;
			c->phase = F_DONE;
			return;
		}
		SSL_set_fd(c->ssl, fd);
		/* ⛔ PARTIAL WRITES: without this mode `SSL_write_ex()` reports
		 *    nothing until the WHOLE remaining response is out, so
		 *    `oresponse` would stay 0 for a 907 KB page — and `oresponse` is
		 *    the progress measure where `TCP_INFO` is missing.  With it,
		 *    every record taken counts. */
		SSL_set_mode(c->ssl, SSL_MODE_ENABLE_PARTIAL_WRITE);
		SSL_set_accept_state(c->ssl);
		c->phase = F_HANDSHAKE;
		move_client(p, c, 0);
	}
}

void page_expired(page *p, uint64_t now)
{
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *c = &p->clients[i];
		if (client_active(c) && c->phase == F_WRITE)
			sample(c, now);
		if (!client_active(c) || now < client_deadline(c))
			continue;
		if (c->phase == F_WRITE)
			log_detail(LOG_PAGE,
			           "%s closed: %llu of %zu bytes of the response received "
			           "in %llu ms, the last %llu ms ago",
			           c->provenance, (unsigned long long)c->delivered,
			           c->nresponse,
			           (unsigned long long)(now - c->write_start),
			           (unsigned long long)(now - c->last_progress));
		else
			log_detail(LOG_PAGE, "%s closed: no whole request within %u s",
			           c->provenance, PAGE_REQUEST_MS / 1000u);
		if (c->phase == F_WRITE)
			p->expired_response++;
		else
			p->expired_request++;
		client_abort(c);
	}
	refusals_report(p, now);
}

int page_wait_ms(const page *p, uint64_t now)
{
	uint64_t before = UINT64_MAX;

	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		const client *c = &p->clients[i];
		if (client_active(c) && client_deadline(c) < before)
			before = client_deadline(c);
	}
	if (refusals_pending(p) &&
	    p->refused_line_ms + PAGE_REFUSAL_LOG_MS < before)
		before = p->refused_line_ms + PAGE_REFUSAL_LOG_MS;
	if (before == UINT64_MAX)
		return -1;
	if (before <= now)
		return 0;
	return before - now > 1000 ? 1000 : (int)(before - now);
}

void page_move(page *p, struct pollfd *dove, size_t amount)
{
	for (size_t k = 0; k < amount; k++) {
		if (dove[k].revents == 0)
			continue;
		if (dove[k].fd == p->fd) {
			accept_page(p);
			continue;
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (p->clients[i].fd == dove[k].fd &&
			    p->clients[i].phase != F_DONE) {
				move_client(p, &p->clients[i], dove[k].revents);
				break;
			}
	}
}

void page_context(page *p, SSL_CTX *ctx) { p->ctx = ctx; }

/* ------------------------------------------------------------------------ */

page *page_open(const char *address, const char *port, SSL_CTX *ctx,
                    const char *file_html, const certificates *cert)
{
	struct addrinfo hints, *result = NULL, *r;
	page *p;
	int fd = -1, uno = 1;

	memset(&hints, 0, sizeof hints);
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_flags = AI_PASSIVE;

	if (getaddrinfo(address, port, &hints, &result) != 0) {
		registro_dice(LOG_PAGE, "⛔ %s:%s does not resolve", address, port);
		return NULL;
	}
	for (r = result; r; r = r->ai_next) {
		fd = socket(r->ai_family, r->ai_socktype | SOCK_NONBLOCK, r->ai_protocol);
		if (fd < 0)
			continue;
		setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &uno, sizeof uno);
		if (bind(fd, r->ai_addr, r->ai_addrlen) == 0 && listen(fd, 16) == 0)
			break;
		close(fd);
		fd = -1;
	}
	freeaddrinfo(result);
	if (fd < 0) {
		registro_dice(LOG_PAGE, "⛔ cannot bind to %s:%s over TCP: %s", address,
		              port, strerror(errno));
		return NULL;
	}

	p = calloc(1, sizeof *p);
	if (!p) {
		close(fd);
		return NULL;
	}
	p->fd = fd;
	p->ctx = ctx;
	p->cert = cert;

	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		p->clients[i].fd = -1;
		p->clients[i].phase = F_DONE;
	}

	p->html = read_file(file_html, &p->nhtml);
	if (!p->html) {
		page_close(p);
		return NULL;
	}
	/* ⛔ The positive check of the marker: if the page does NOT contain
	 *    `__FINGERPRINT__`, the substitution would succeed «doing nothing» and
	 *    the server would needs forever a page without a fingerprint — with
	 *    the symptom «WebTransport does not connect» and no error naming the
	 *    fingerprint (`LESSONS.md` §1.9: a tool that finds nothing is not
	 *    clean, it is uncertified). */
	/* ⛔ AND THE MARKERS ARE FOUR, not one — night of 10 Aug 2026, finding
	 *    R12.2.  `__BANNED__` and `__REMAINING_MS__` are what the meter of
	 *    §4.4-bis reads to say whether the ban is there and for how long: a
	 *    page without those markers would be served perfectly well, and the
	 *    bench would say «the ban did not trigger» on a server that does ban.
	 *    ⚠ A substitution that «succeeds doing nothing» is the seventh guise
	 *    of `LESSONS.md` §1.9, and it holds for all four. */
	{
		static const char *const PLACEHOLDERS[] = {"__FINGERPRINT__", "__WARNING__",
		                                    "__BANNED__", "__REMAINING_MS__",
		                                    NULL};
		for (int i = 0; PLACEHOLDERS[i]; i++)
			if (!strstr(p->html, PLACEHOLDERS[i])) {
				registro_dice(LOG_PAGE,
				              "⛔ %s does not contain the marker %s: the page "
				              "would serve an answer that is not there — and a "
				              "substitution that succeeds doing nothing would "
				              "not tell anyone.  Not starting.",
				              file_html, PLACEHOLDERS[i]);
				page_close(p);
				return NULL;
			}
	}

	/* ⛔⭐ AND EACH OF THE TWO ATTRIBUTES MUST APPEAR ONLY ONCE.
	 *
	 *     `[M]` night of 10 Aug 2026, and I did it myself while curing R12.2:
	 *     the style sheet said `#warning { display:none }` under an attribute
	 *     selector on `data-banned`, and that selector puts the string
	 *     `data-banned=«yes»` INSIDE the `<style>`, that is BEFORE the `<body>`.
	 *     ⛔ Whoever reads the document with a search — and that is what the
	 *     meter of §4.4-bis does — takes the FIRST occurrence: it read
	 *     «banned» on a free address.  ⚠ The page was right, the measurement
	 *     was not, and the red would have landed on the wrong defendant.
	 *
	 * ⭐ The cure lives in the PROGRAM and not in a comment (invariant I7): the
	 *    second occurrence cannot be introduced without the server refusing to
	 *    start — not even inside a comment, which is bytes served to the
	 *    browser as much as the rest. */
	{
		static const char *const UNIQUE[] = {"data-banned=\"",
		                                    "data-remaining-ms=\"", NULL};
		for (int i = 0; UNIQUE[i]; i++) {
			int how_many = 0;
			for (const char *q = strstr(p->html, UNIQUE[i]); q;
			     q = strstr(q + strlen(UNIQUE[i]), UNIQUE[i]))
				how_many++;
			if (how_many != 1) {
				registro_dice(LOG_PAGE,
				              "⛔ %s contains «%s» %d times instead of only "
				              "once: whoever reads the document searching for that "
				              "string would take the wrong occurrence and "
				              "would measure nobody's ban (§4.4-bis).  "
				              "Not starting.",
				              file_html, UNIQUE[i], how_many);
				page_close(p);
				return NULL;
			}
		}
	}

	registro_dice(LOG_PAGE,
	              "listening over TCP on %s:%s — page %s (%zu bytes), cross-origin "
	              "isolated (COOP+COEP+CORP, SPECS.md §11.5)",
	              address, port, file_html, p->nhtml);
	return p;
}

void page_close(page *p)
{
	if (!p)
		return;
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (p->clients[i].fd >= 0)
			client_close(&p->clients[i]);
	body_unref(p->cached);
	free(p->html);
	if (p->fd >= 0)
		close(p->fd);
	free(p);
}
