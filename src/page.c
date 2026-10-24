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
#include <strings.h>
#include <zlib.h>

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
 *     there clients that never sent a byte, then clients without a whole
 *     request, then writers PAGE_EVICT_AGE_MS
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
 *       carrier /48) is one group — see `DECISIONS-11.md` §11.44.
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
/* ⭐ Holistic review, 15 Oct 2026 — the work of ONE `page_move()` call: at
 *   most this many events (a client's event or one accept each), taken round
 *   robin; the rest wait for the next pass of the main loop (`poll` is
 *   level-triggered), so QUIC, the children and PAM are never held behind a
 *   crowd of page clients. */
#define PAGE_EVENTS_PER_PASS 16
/* ⭐ Same review — accepts per second: per `rcp_key_address()` key (an IPv4
 *   address or an IPv6 /64) and per IPv6 /48, as token buckets (a burst,
 *   then a steady rate).  Over it the connection waits, parked without TLS,
 *   in a FREE slot (never evicting anybody), or is refused when there is
 *   none.  PAGE_RATE_KEYS buckets each (256: an attacker must keep more
 *   addresses than that busy to push a new address onto the shared overflow
 *   bucket); a new key takes only a FULL bucket (a full bucket is the same
 *   as no bucket), see bucket_of(). */
#define PAGE_ACCEPT_RATE 4
#define PAGE_ACCEPT_BURST 8
#define PAGE_ACCEPT_RATE_48 8
#define PAGE_ACCEPT_BURST_48 16
#define PAGE_RATE_KEYS 256
/* The kernel's queue of connections not accepted yet (independent review of
 * 16b75f33: 16 overflowed under a connect flood — the probe's SYN then
 * waited 1-2 s for its retransmit). */
#define PAGE_BACKLOG 256
/* How long a connection over the accept rate waits, parked without TLS, for
 * a token; past it, it is served «503 busy» (review of 95ed70ea: closing it
 * at accept made the page say «the server is not there», D-009). */
#define PAGE_RATE_WAIT_MS 3000u
/* A connection younger than this without a reply yet is not «silent»: a
 * browser's handshake takes one round trip (review of fc76de93: a parked
 * one used to rank above a brand-new owner during that round trip). */
#define PAGE_YOUNG_MS 1000u
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

/* F_RATE: accepted over the accept rate, parked WITHOUT TLS until a token
 * (or PAGE_RATE_WAIT_MS: then served a 503) — see `park_or_start()`. */
enum phase { F_RATE, F_HANDSHAKE, F_READ, F_WRITE, F_DONE };

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
	/* … and then `tail` (`ntail` bytes, 0 or 8: a gzip trailer composed
	 * for this response, see `banned_respond()`). */
	unsigned char tail[8];
	size_t ntail;
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
	/* The peer's handshake is complete, or the server has begun its reply
	 * (see move_client): a browser gets there in one round trip; a bare
	 * connect or a few bytes never do.  Eviction takes the silent first. */
	bool spoke;
	/* F_RATE: until when it waits for a token; `busy`: it waited in vain,
	 * every request it sends gets 503. */
	uint64_t rate_until;
	bool busy;
	/* the order of parking (FIFO), and whether the bucket that kept it
	 * waiting was the SHARED one (then the 503 does not blame the address) */
	uint64_t park_seq;
	bool busy_shared;
	/* parked: the buckets it waits on (see queue_on()) */
	struct bucket *qb, *qb48;
	/* the page_move() call that accepted it: that call's `revents` are an
	 * older owner's of the same descriptor number, never its own */
	uint64_t accepted_in;
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
	/* The not-banned page, built once for `cached_fp` (see `body`), and
	 * the same page gzip-compressed (`gz_page()`), or NULL: then every
	 * request gets the plain one.  ⚠ ONE plain and ONE compressed copy per
	 * fingerprint, replaced together.  `cached_gz_retry`: the compression
	 * failed for lack of memory, and is tried again at the next request that
	 * accepts gzip (not after a failure that would repeat: never smaller). */
	body *cached;
	body *cached_gz;
	bool cached_gz_retry;
	char cached_fp[64];
	/* ⭐ The banned page (holistic review, 15 Oct 2026: it was rebuilt WHOLE
	 *   at every banned GET, ~907 KB and 3.2 ms each).  Every marker of
	 *   `page.html` is in its first `split` bytes (~45 KB); the rest never
	 *   changes.  So a banned response is its own small prefix (the markers
	 *   replaced, gzip-compressed when asked) + `tail` or `tail_gz` (shared,
	 *   built once for the page's life) + for gzip its own 8-byte trailer. */
	bool split_done;
	size_t split;
	body *tail;
	body *tail_gz; /* raw deflate (no wrapper), with its last block */
	uLong tail_crc;
	/* The accept buckets, per key and per /48. */
	struct bucket {
		char key[64];
		uint64_t at;
		unsigned milli;
	} rate[PAGE_RATE_KEYS], rate48[PAGE_RATE_KEYS];
	/* The ONE bucket every key without a bucket of its own shares, per
	 * table (review of 95ed70ea: a newcomer used to take over the most
	 * refilled bucket with a fresh burst, so 65 rotating addresses had no
	 * rate at all). */
	struct bucket rate_over, rate48_over;
	/* parked for the rate; served 503 after waiting in vain */
	unsigned delayed_rate, busy_rate, refused_rate;
	uint64_t park_next;
	/* the buckets the last rate_take() spent a token from, and the ones it
	 * looked at */
	struct bucket *taken, *taken48, *cand, *cand48;
	/* after a failed build of `tail_gz`, not again before this time */
	uint64_t tail_gz_after;
	/* every connection ever parked for the rate, and ever refused for it
	 * (never zeroed: the fuzz harness tells a rate refusal by it) */
	unsigned long long delayed_rate_total, refused_rate_total;
	/* Round robin of `page_move()`'s event budget; the calls, counted. */
	size_t move_next;
	uint64_t move_calls;
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
	c->nhead = c->nresponse = c->oresponse = c->nrequest = c->ntail = 0;
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
static void compose_tail(client *c, const char *state, const char *kind,
                         const char *text, size_t ntext, body *shared,
                         const unsigned char *tail, size_t ntail,
                         const char *extra)
{
	char head[2048]; /* the page's security headers (PAGE_SECURITY) are ~900 bytes */
	size_t nbody = ntext + (shared ? shared->n : 0) + ntail;
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
			compose_tail(c, "500 Internal Server Error", "text/plain; charset=utf-8",
			             "response headers too long\n", 26, NULL, NULL, 0, NULL);
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
	if (ntail > sizeof c->tail)
		ntail = sizeof c->tail;
	if (ntail)
		memcpy(c->tail, tail, ntail);
	c->ntail = ntail;
	c->nresponse = c->nhead + (shared ? shared->n : 0) + ntail;
	c->oresponse = 0;
	c->phase = F_WRITE;
	c->write_start = c->last_progress = log_now_ms();
	c->acked_base = tcp_acked(c->fd, 0);
	c->delivered = 0;
}

static void compose_with(client *c, const char *state, const char *kind,
                         const char *text, size_t ntext, body *shared,
                         const char *extra)
{
	compose_tail(c, state, kind, text, ntext, shared, NULL, 0, extra);
}

static void compose(client *c, const char *state, const char *kind,
                    const char *body_text, size_t nbody, const char *extra)
{
	compose_with(c, state, kind, body_text, nbody, NULL, extra);
}

/* The page with its five markers replaced.  Returns a new body, or NULL. */
static char *build_text(const page *p, const char *src, bool banned,
                        const char *warning, const char *remain_txt)
{
	char *a, *b, *cc, *cc2, *d;

	a = replace(src, "__FINGERPRINT__", p->cert->fingerprint);
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
	return d;
}

static body *build_page(const page *p, bool banned, const char *warning,
                        const char *remain_txt)
{
	char *d = build_text(p, p->html, banned, warning, remain_txt);
	body *r;

	if (!d)
		return NULL;
	r = body_new(d, strlen(d));
	free(d);
	return r;
}

/* zlib's allocations go through this file's `malloc`/`free` (so the desk
 * test's allocation seam sees them too). */
static voidpf gz_alloc(voidpf opaque, uInt items, uInt size)
{
	(void)opaque;
	if (size && items > (size_t)-1 / size)
		return Z_NULL;
	return malloc((size_t)items * size);
}

static void gz_free(voidpf opaque, voidpf address)
{
	(void)opaque;
	free(address);
}

/* ⭐ §11.44 (the user's decision, 15 Oct 2026): `plain` gzip-compressed
 *   (RFC 1952, level 6) — ~907 KB of page become far fewer for a slow phone.
 *   ⚠ Level 6, not 9 (review of 6d8249c4): it runs on the main loop, once per
 *   fingerprint, and 9 held it ~86 ms on the real page against ~45 ms for
 *   +0.25 % of bytes.
 *   Done ONCE per fingerprint, when the shared page is built.  Returns a new
 *   body, or NULL: `*oom` says whether for lack of memory (worth retrying)
 *   or because it did not come out smaller (not worth it). */
static body *gz_page(const body *plain, bool *oom, int level)
{
	z_stream z;
	body *r;
	uLong bound;
	int rv;

	*oom = false;
	memset(&z, 0, sizeof z);
	z.zalloc = gz_alloc;
	z.zfree = gz_free;
	/* 15 + 16: a 32 KB window and the gzip wrapper (not zlib's own). */
	rv = deflateInit2(&z, level, Z_DEFLATED, 15 + 16, 8, Z_DEFAULT_STRATEGY);
	if (rv != Z_OK) {
		*oom = rv == Z_MEM_ERROR;
		return NULL;
	}
	bound = deflateBound(&z, (uLong)plain->n);
	if (plain->n > (uInt)-1 || bound > (uInt)-1) {
		deflateEnd(&z);
		return NULL;
	}
	r = malloc(sizeof *r + bound);
	if (!r) {
		*oom = true;
		deflateEnd(&z);
		return NULL;
	}
	z.next_in = (Bytef *)(uintptr_t)plain->data;
	z.avail_in = (uInt)plain->n;
	z.next_out = (Bytef *)r->data;
	z.avail_out = (uInt)bound;
	rv = deflate(&z, Z_FINISH);
	if (rv != Z_STREAM_END || z.total_out >= plain->n) {
		deflateEnd(&z);
		free(r);
		return NULL;
	}
	r->refs = 1;
	r->n = (size_t)z.total_out;
	deflateEnd(&z);
	/* ⚠ The buffer was sized for the worst case (≈ the plain page): give
	 *   the rest back.  A failed shrink keeps the big one, still valid. */
	{
		body *small = realloc(r, sizeof *r + r->n);
		if (small)
			r = small;
	}
	return r;
}

/* `n` bytes of `in` as RAW deflate (no wrapper) into a new buffer, `*nout`
 * bytes: `last` ends the stream (Z_FINISH), otherwise it ends byte-aligned
 * and open (Z_SYNC_FLUSH), so another raw deflate stream can follow it.
 * `prefix` bytes are reserved at the start (a gzip header).  NULL when out
 * of memory. */
static unsigned char *deflate_raw(const char *in, size_t n, int level, bool last,
                                  size_t prefix, size_t *nout)
{
	z_stream z;
	unsigned char *out;
	uLong bound;

	memset(&z, 0, sizeof z);
	z.zalloc = gz_alloc;
	z.zfree = gz_free;
	if (n > (uInt)-1 ||
	    deflateInit2(&z, level, Z_DEFLATED, -15, 8, Z_DEFAULT_STRATEGY) != Z_OK)
		return NULL;
	/* + 16: room for the sync flush's empty stored block */
	bound = deflateBound(&z, (uLong)n) + 16;
	out = bound <= (uInt)-1 ? malloc(prefix + bound) : NULL;
	if (!out) {
		deflateEnd(&z);
		return NULL;
	}
	z.next_in = (Bytef *)(uintptr_t)in;
	z.avail_in = (uInt)n;
	z.next_out = out + prefix;
	z.avail_out = (uInt)bound;
	if (deflate(&z, last ? Z_FINISH : Z_SYNC_FLUSH) != (last ? Z_STREAM_END : Z_OK) ||
	    z.avail_in != 0 || z.avail_out == 0) {
		deflateEnd(&z);
		free(out);
		return NULL;
	}
	*nout = prefix + (size_t)z.total_out;
	deflateEnd(&z);
	return out;
}

/* Where the last marker of the template ends: every byte after it is the
 * same in every page this server sends. */
static size_t page_split(page *p)
{
	static const char *const markers[] = {"__FINGERPRINT__", "__WARNING__",
	                                      "__BANNED__", "__REMAINING_MS__",
	                                      "__DIARY__"};
	size_t end = 0;

	if (p->split_done)
		return p->split;
	for (size_t i = 0; i < sizeof markers / sizeof markers[0]; i++) {
		size_t k = strlen(markers[i]);
		const char *at = p->html, *f;
		while ((f = memmem(at, p->nhtml - (size_t)(at - p->html), markers[i], k))) {
			if ((size_t)(f - p->html) + k > end)
				end = (size_t)(f - p->html) + k;
			at = f + k;
		}
	}
	p->split = end;
	p->split_done = true;
	return end;
}

/* ⭐ A banned visitor's 200 (holistic review, 15 Oct 2026): ITS prefix (the
 *   markers replaced, ~45 KB of the real page, ~0.2 ms) + the shared tail.
 *   With gzip: a gzip header + the prefix as raw deflate ending byte-aligned
 *   + `tail_gz` (raw deflate, compressed ONCE) + this response's trailer,
 *   CRC-32 of the whole (crc32_combine) and its length — one valid gzip
 *   member (RFC 1951 §3.2.4: blocks are independent of how they were made).
 *   Returns false only when the page itself could not be built (the
 *   caller's 500); a gzip that cannot be made falls back to plain. */
static bool banned_respond(page *p, client *c, bool gz, const char *warning,
                           const char *remain_txt)
{
	size_t split = page_split(p), ntext;
	char *pre, *text;

	if (!p->tail) {
		p->tail = body_new(p->html + split, p->nhtml - split);
		if (!p->tail)
			return false;
	}
	pre = malloc(split + 1);
	if (!pre)
		return false;
	memcpy(pre, p->html, split);
	pre[split] = 0;
	text = build_text(p, pre, true, warning, remain_txt);
	free(pre);
	if (!text)
		return false;
	ntext = strlen(text);
	if (gz && !p->tail_gz && log_now_ms() >= p->tail_gz_after) {
		size_t n = 0;
		/* ⚠ After a failure (no memory), not again for 10 s: retrying the
		 *   ~860 KB compression at every banned gzip GET would be the CPU
		 *   cost this design removes (review of 95ed70ea). */
		p->tail_gz_after = log_now_ms() + 10000u;
		unsigned char *raw = deflate_raw(p->tail->data, p->tail->n, 6, true, 0, &n);
		if (raw) {
			p->tail_gz = malloc(sizeof *p->tail_gz + n);
			if (p->tail_gz) {
				p->tail_gz->refs = 1;
				p->tail_gz->n = n;
				memcpy(p->tail_gz->data, raw, n);
				p->tail_crc = crc32(crc32(0L, Z_NULL, 0),
				                    (const Bytef *)p->tail->data,
				                    (uInt)p->tail->n);
			}
			free(raw);
		}
	}
	if (gz && p->tail_gz && ntext <= (uInt)-1) {
		size_t nout = 0;
		/* the gzip header (RFC 1952 §2.3): deflate, no flags, no time, Unix */
		static const unsigned char gzh[10] = {0x1f, 0x8b, 8, 0, 0, 0, 0, 0, 0, 3};
		unsigned char *out = deflate_raw(text, ntext, 1, false, sizeof gzh, &nout);
		if (out) {
			unsigned char trailer[8];
			uLong crc = crc32_combine(crc32(crc32(0L, Z_NULL, 0),
			                                (const Bytef *)text, (uInt)ntext),
			                          p->tail_crc, (z_off_t)p->tail->n);
			uint32_t isize = (uint32_t)(ntext + p->tail->n);
			memcpy(out, gzh, sizeof gzh);
			for (int i = 0; i < 4; i++) {
				trailer[i] = (unsigned char)(crc >> (8 * i));
				trailer[4 + i] = (unsigned char)(isize >> (8 * i));
			}
			compose_tail(c, "200 OK", "text/html; charset=utf-8", (const char *)out,
			             nout, p->tail_gz, trailer, sizeof trailer,
			             "Content-Encoding: gzip\r\nVary: Accept-Encoding\r\n" PAGE_SECURITY);
			free(out);
			free(text);
			return true;
		}
	}
	compose_tail(c, "200 OK", "text/html; charset=utf-8", text, ntext, p->tail,
	             NULL, 0, "Vary: Accept-Encoding\r\n" PAGE_SECURITY);
	free(text);
	return true;
}

/* The q-value of RFC 9110 §12.4.2 in thousandths («0», «0.5», «1.000»), or
 * -1 when it is not one. */
static int qvalue(const char *s, size_t n)
{
	int v = 0, digits = 0;

	if (n == 0 || (s[0] != '0' && s[0] != '1'))
		return -1;
	if (n > 1 && (s[1] != '.' || n > 5))
		return -1;
	for (size_t i = 2; i < n; i++) {
		if (s[i] < '0' || s[i] > '9')
			return -1;
		v = v * 10 + (s[i] - '0');
		digits++;
	}
	while (digits++ < 3)
		v *= 10;
	v += s[0] == '1' ? 1000 : 0;
	return v > 1000 ? -1 : v;
}

static bool is_tchar(unsigned char ch)
{
	return (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') ||
	       (ch >= '0' && ch <= '9') || (ch && strchr("!#$%&'*+-.^_`|~", ch));
}

static bool is_ows(char ch)
{
	return ch == ' ' || ch == '\t';
}

/* One element of `Accept-Encoding` (no comma inside), RFC 9110 §12.5.3:
 *   coding *( OWS ";" OWS [ name "=" value ] )
 * — an EMPTY parameter (`gzip;q=0;`, `gzip;;q=0`) is allowed and skipped
 * (review of 6d8249c4: it used to throw the whole element away, so
 * `gzip;q=0;, *` got gzip).  Only `q` matters.  ⛔ An element that does not
 * read — a coding or a name that is not a token, a parameter without a name
 * or without a value, a value that is not a token (`a=b=c`, a quoted string),
 * whitespace around `=`, `q` twice, a `q` that is no qvalue — COUNTS FOR
 * NOTHING: as if it were not there. */
static void accept_encoding_element(const char *s, size_t n, int *q_gzip, int *q_any)
{
	size_t i = 0, c0, c1;
	int q = 1000;
	bool have_q = false;

	while (i < n && is_ows(s[i]))
		i++;
	while (n > i && is_ows(s[n - 1]))
		n--;
	c0 = i;
	while (i < n && is_tchar((unsigned char)s[i]))
		i++;
	c1 = i;
	if (c1 == c0)
		return; /* empty, or no coding */
	for (;;) {
		size_t p0, p1, v0, v1;

		while (i < n && is_ows(s[i]))
			i++;
		if (i == n)
			break;
		if (s[i] != ';')
			return;
		i++;
		while (i < n && is_ows(s[i]))
			i++;
		if (i == n || s[i] == ';')
			continue; /* the empty parameter */
		p0 = i;
		while (i < n && is_tchar((unsigned char)s[i]))
			i++;
		p1 = i;
		if (p1 == p0 || i == n || s[i] != '=')
			return;
		i++;
		v0 = i;
		while (i < n && is_tchar((unsigned char)s[i]))
			i++;
		v1 = i;
		if (v1 == v0 || (i < n && !is_ows(s[i]) && s[i] != ';'))
			return;
		if (p1 - p0 == 1 && (s[p0] == 'q' || s[p0] == 'Q')) {
			if (have_q)
				return;
			have_q = true;
			q = qvalue(s + v0, v1 - v0);
			if (q < 0)
				return;
		}
	}
	if ((c1 - c0 == 4 && strncasecmp(s + c0, "gzip", 4) == 0) ||
	    (c1 - c0 == 6 && strncasecmp(s + c0, "x-gzip", 6) == 0))
		*q_gzip = *q_gzip < 0 ? q : (q < *q_gzip ? q : *q_gzip);
	else if (c1 - c0 == 1 && s[c0] == '*')
		*q_any = *q_any < 0 ? q : (q < *q_any ? q : *q_any);
}

/* One `Accept-Encoding` value: its elements, split on `,`. */
static void accept_encoding_value(const char *s, size_t n, int *q_gzip, int *q_any)
{
	size_t i = 0;

	while (i <= n) {
		const char *comma = memchr(s + i, ',', n - i);
		size_t e = comma ? (size_t)(comma - s) : n;
		accept_encoding_element(s + i, e - i, q_gzip, q_any);
		i = e + 1;
	}
}

/* `true` = a header line begins with whitespace: an obs-fold (RFC 9112
 * §5.2), refused with 400 as the RFC allows — never half-read. */
static bool has_obs_fold(const char *req, size_t n)
{
	const char *line = memchr(req, '\n', n);

	while (line) {
		const char *start = line + 1;
		size_t left = n - (size_t)(start - req);
		if (left == 0 || *start == '\n' || (*start == '\r' && left > 1 && start[1] == '\n'))
			return false; /* the empty line: the end of the headers */
		if (is_ows(*start))
			return true;
		line = memchr(start, '\n', left);
	}
	return false;
}

/* ⭐ `true` = the request's `Accept-Encoding` allows gzip (RFC 9110
 *   §12.5.3): `gzip` (or `x-gzip`) with q > 0, or, when it is not named, `*`
 *   with q > 0.  `gzip;q=0` refuses it even if `*` allows everything; no
 *   header at all, or a header that names neither, gets the plain page —
 *   the prudent reading.  Named twice, the lower q wins. */
static bool accepts_gzip(const char *req, size_t n)
{
	int q_gzip = -1, q_any = -1;
	const char *line = memchr(req, '\n', n);

	while (line) {
		const char *start = line + 1, *end, *colon;
		size_t left = n - (size_t)(start - req), len;

		end = memchr(start, '\n', left);
		len = end ? (size_t)(end - start) : left;
		if (len && start[len - 1] == '\r')
			len--;
		if (len == 0)
			break; /* the empty line: the end of the headers */
		colon = memchr(start, ':', len);
		if (colon && colon - start == 15 &&
		    strncasecmp(start, "accept-encoding", 15) == 0)
			accept_encoding_value(colon + 1, len - (size_t)(colon + 1 - start),
			                      &q_gzip, &q_any);
		line = end;
	}
	if (q_gzip >= 0)
		return q_gzip > 0;
	return q_any > 0;
}

/* How much of a request target the «GET … from» line quotes. */
#define PAGE_LOG_TARGET 200

/* `src` (a C string) for the log: printable ASCII kept, any other byte a
 * `?`, at most `limit` bytes, then «…(N bytes)» when it was longer. */
static void log_clean(char *dst, size_t cap, const char *src, size_t limit)
{
	size_t len = strlen(src), j = 0;

	for (size_t i = 0; i < len && i < limit && j + 1 < cap; i++) {
		unsigned char x = (unsigned char)src[i];
		dst[j++] = (x >= 0x20 && x < 0x7F) ? (char)x : '?';
	}
	dst[j] = '\0';
	if (len > limit)
		snprintf(dst + j, cap - j, "…(%zu bytes)", len);
}

/* `true` = the request line of `key` may be written now.
 * ⚠ The price, stated (independent review of 16b75f33): when 16 other
 *   addresses hold every entry inside their window, the owner's own «GET /
 *   from» line is not written either — it is COUNTED in the summary line
 *   («request lines not written»), never lost in silence. */
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
	size_t nline;
	char address[64];
	uint64_t remain = 0;
	bool banned;

	/* ⛔ The method and the target are looked for in the REQUEST LINE only
	 *    (holistic review, 15 Oct 2026): searched across the whole request,
	 *    a line without its second space took the next header lines into the
	 *    target — newlines included, and into the log. */
	{
		const char *eol = memchr(c->request, '\n', c->nrequest);
		nline = eol ? (size_t)(eol - c->request) : c->nrequest;
	}
	sp1 = memchr(c->request, ' ', nline);
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
	sp2 = memchr(sp1 + 1, ' ', nline - (size_t)(sp1 + 1 - c->request));
	if (!sp2) {
		compose(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "request is unreadable\n", 22, NULL);
		return;
	}
	/* ⚠ A folded header line (obs-fold) is refused, not half-read: an
	 *   `Accept-Encoding` continued on the next line would otherwise be
	 *   read without its continuation (review of 6d8249c4). */
	if (has_obs_fold(c->request, c->nrequest)) {
		compose(c, "400 Bad Request", "text/plain; charset=utf-8",
		        "request is unreadable\n", 22, NULL);
		return;
	}
	/* ⭐ It waited PAGE_RATE_WAIT_MS for the accept rate in vain: «busy»,
	 *   which the page tells apart from «not there» (D-009) and retries. */
	if (c->busy) {
		const char *t = c->busy_shared ? "busy: too many connections right now, retry\n"
		                               : "busy: too many connections from this address, retry\n";
		compose(c, "503 Service Unavailable", "text/plain; charset=utf-8", t,
		        strlen(t), "Retry-After: 1\r\n");
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
	{
		/* ⛔ What the peer sent is logged CLEANED and SHORT: printable
		 *    ASCII only (any other byte a `?`), the target cut at
		 *    PAGE_LOG_TARGET bytes with its length said.  A target like
		 *    `/\n14:00:00.000 rcp [owner] ⭐ ADMITTED …` wrote a forged
		 *    line in server.log without any password (holistic review,
		 *    15 Oct 2026); `log.c` now also turns control bytes into `?`
		 *    for every caller, and this keeps the escape codes and the
		 *    3 KB out too. */
		char lm[sizeof method + 32], lt[PAGE_LOG_TARGET + 32];
		log_clean(lm, sizeof lm, method, sizeof method - 1);
		log_clean(lt, sizeof lt, target, PAGE_LOG_TARGET);
		registro_dice(LOG_PAGE, "%s %s from %s%s", lm, lt,
		              c->provenance, banned ? " (address BANNED)" : "");
	}
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
		/* ⚠ The remaining time in whole minutes, rounded up as the
		 *   sentence says it (holistic review, 15 Oct 2026): the page's
		 *   countdown may end up to a minute late, never early. */
		snprintf(remain_txt, sizeof remain_txt, "%llu", minutes * 60000ull);

		/* ⭐ Not banned: the shared page, rebuilt only when the fingerprint
		 *   changes (a rotation), with its gzip copy (§11.44).  Banned: its
		 *   own prefix + the shared tail, gzip too (`banned_respond()`). */
		const char *extra = PAGE_SECURITY; /* + the gzip headers below */
		bool gz = accepts_gzip(c->request, c->nrequest);
		if (banned) {
			if (!banned_respond(p, c, gz, warning, remain_txt))
				compose(c, "500 Internal Server Error",
				        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		{
			bool oom;
			if (!p->cached ||
			    strcmp(p->cached_fp, p->cert->fingerprint) != 0) {
				body *nb = build_page(p, false, warning, remain_txt);
				if (nb) {
					body_unref(p->cached);
					body_unref(p->cached_gz);
					p->cached = nb;
					p->cached_gz = gz_page(nb, &oom, 6);
					p->cached_gz_retry = !p->cached_gz && oom;
					snprintf(p->cached_fp, sizeof p->cached_fp, "%s",
					         p->cert->fingerprint);
				}
			} else if (gz && p->cached_gz_retry) {
				p->cached_gz = gz_page(p->cached, &oom, 6);
				p->cached_gz_retry = !p->cached_gz && oom;
			}
			if (p->cached &&
			    strcmp(p->cached_fp, p->cert->fingerprint) == 0) {
				/* ⚠ `Vary` on BOTH: which copy goes out depends on
				 *   `Accept-Encoding`, gzip or not. */
				if (gz && p->cached_gz) {
					d = body_ref(p->cached_gz);
					extra = "Content-Encoding: gzip\r\n"
					        "Vary: Accept-Encoding\r\n" PAGE_SECURITY;
				} else {
					d = body_ref(p->cached);
					extra = "Vary: Accept-Encoding\r\n" PAGE_SECURITY;
				}
			} else {
				d = NULL;
			}
		}
		if (!d) {
			compose(c, "500 Internal Server Error",
			        "text/plain; charset=utf-8", "no mem.\n", 8, NULL);
			return;
		}
		/* ⚠ `Content-Length` is `d->n`: the COMPRESSED length when `d` is
		 *   the gzip copy — and so are `nresponse` and the progress and
		 *   eviction arithmetic built on it. */
		compose_with(c, "200 OK", "text/html; charset=utf-8", "", 0, d, extra);
		body_unref(d);
	}
}

/* ------------------------------------------------------------------------ */

/* The server has begun its handshake reply: the state is one OpenSSL
 * reaches only after a whole, valid ClientHello. */
static bool server_replied(SSL *ssl)
{
	switch (SSL_get_state(ssl)) {
	case TLS_ST_BEFORE:
	case TLS_ST_SR_CLNT_HELLO:
	case TLS_ST_OK:
		return false;
	default:
		return true;
	}
}

static void move_client(page *p, client *c, short events)
{
	int rv;

	if (c->phase == F_RATE) {
		/* no TLS yet: parked_move() decides — except that a peer that
		 * reset or hung up is closed NOW: its descriptor would report
		 * POLLERR/POLLHUP at every `poll`, events 0 or not, and the loop
		 * would spin (review of 38639d7d) */
		if (events & (POLLERR | POLLHUP | POLLNVAL))
			client_close(c);
		return;
	}
	c->wants_to_write = false;

	if (c->phase == F_HANDSHAKE) {
		rv = SSL_accept(c->ssl);
		/* ⛔ «Spoke» = the handshake is COMPLETE, or the server has begun
		 *    its reply (a server-write state: OpenSSL parsed a whole, valid
		 *    ClientHello and answered it).  Not «left TLS_ST_BEFORE»: `[M]`
		 *    OpenSSL 3.5.7 leaves it after the 9-byte record 16 03 01 00 04
		 *    01 00 01 fc (review of 38639d7d), nor «a byte arrived» (review
		 *    of 95ed70ea).  Asked after every SSL_accept, the one at accept
		 *    included. */
		if (!c->spoke && (rv == 1 || server_replied(c->ssl)))
			c->spoke = true;
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
			size_t nshared = c->shared ? c->shared->n : 0;
			if (c->oresponse < c->nhead) {
				from = c->head + c->oresponse;
				len = c->nhead - c->oresponse;
			} else if (c->oresponse < c->nhead + nshared) {
				from = c->shared->data + (c->oresponse - c->nhead);
				len = c->nhead + nshared - c->oresponse;
			} else {
				from = (const char *)c->tail + (c->oresponse - c->nhead - nshared);
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
		/* ⚠ a parked one is watched for nothing (its ClientHello would
		 *   wake the loop at every pass): parked_move() starts it */
		dove[n].events = p->clients[i].phase == F_RATE ? 0
		               : p->clients[i].wants_to_write ? POLLOUT : POLLIN;
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
	       p->delayed_rate || p->busy_rate || p->refused_rate ||
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
	              "newcomer's would be, %u over the accept rate with no free slot; "
	              "DELAYED: %u over %d accepts a second from one "
	              "address or /64 (%d per /48), %u of them then answered 503 busy after "
	              "%u s; %u request lines not written (over %d per %u s "
	              "from one address); the last refused from %s",
	              p->refused_ever ? " in the last seconds" : "",
	              p->expired_request, PAGE_REQUEST_MS / 1000u,
	              p->expired_response, PAGE_STALL_MS / 1000u, PAGE_RATE_FLOOR,
	              PAGE_RATE_GRACE_MS / 1000u, MAX_CLIENTS, p->evicted,
	              p->evicted_writing, PAGE_EVICT_AGE_MS / 1000u,
	              p->refused_address, PAGE_PER_ADDRESS, p->refused_48,
	              PAGE_PER_48, p->refused_full, p->refused_rate, p->delayed_rate, PAGE_ACCEPT_RATE,
	              PAGE_ACCEPT_RATE_48, p->busy_rate, PAGE_RATE_WAIT_MS / 1000u,
	              p->lines_unwritten,
	              PAGE_LINES_PER_ADDRESS, PAGE_LINES_WINDOW_MS / 1000u,
	              p->refused_last[0] ? p->refused_last : "-");
	p->refused_address = p->refused_48 = p->refused_full = 0;
	p->delayed_rate = p->busy_rate = p->refused_rate = 0;
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

/* The size of every live client's group, counted ONCE per eviction
 * (independent review of 16b75f33: group_size() for each of 128 clients was
 * 128 × 128 comparisons per eviction).  A hash of the group's identity (the
 * /48, or the key) into 2 × MAX_CLIENTS buckets, linear probing: each client
 * is placed once, then its group's count read back. */
static void group_sizes(const page *p, unsigned sizes[MAX_CLIENTS])
{
	enum { NB = 2 * MAX_CLIENTS };
	int rep[NB];
	unsigned count[NB] = {0};
	int slot_of[MAX_CLIENTS];

	for (size_t b = 0; b < NB; b++)
		rep[b] = -1;
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		const client *x = &p->clients[i];
		uint32_t h = 2166136261u;
		const unsigned char *id;
		size_t n;

		slot_of[i] = -1;
		if (!client_active(x))
			continue;
		if (x->has48) {
			id = x->p48;
			n = 6;
			h ^= 0x48;
		} else {
			id = (const unsigned char *)x->key;
			n = strlen(x->key);
		}
		for (size_t k = 0; k < n; k++)
			h = (h ^ id[k]) * 16777619u;
		for (size_t b = h % NB;; b = (b + 1) % NB) {
			if (rep[b] < 0) {
				rep[b] = (int)i;
				slot_of[i] = (int)b;
				count[b] = 1;
				break;
			}
			const client *r = &p->clients[rep[b]];
			if (same_group(r, x->has48, x->p48, x->key)) {
				slot_of[i] = (int)b;
				count[b]++;
				break;
			}
		}
	}
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		sizes[i] = slot_of[i] >= 0 ? count[slot_of[i]] : 0;
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

/* The eviction tier of a candidate: 0 = SILENT (no complete handshake nor
 * server reply, PAGE_YOUNG_MS after accept: a bare TCP connect, a few
 * bytes), 1 = no whole request yet (or parked for the rate, or young), 2 = writing for
 * PAGE_EVICT_AGE_MS or more, 3 = writing for less (a fresh download).
 * ⛔ Tier 0 is the independent review of 16b75f33: with every group at one
 *    slot the OLDEST without a request went, and ~127 addresses doing bare
 *    connects (each evicted one reconnecting, so always younger) made the
 *    owner's handshake the oldest — evicted at every try. */
static int tier(const client *x, uint64_t now)
{
	if (x->phase != F_WRITE)
		/* parked for the rate: waiting through no act of its own, it goes
		 * after the silent ones (review of 38639d7d) — and so does a
		 * connection still in its first PAGE_YOUNG_MS, the owner's
		 * handshake included (review of fc76de93); among them, the
		 * oldest first */
		return x->spoke || x->phase == F_RATE ||
		       (now >= x->born && now - x->born < PAGE_YOUNG_MS) ? 1 : 0;
	return now - x->write_start >= PAGE_EVICT_AGE_MS ? 2 : 3;
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
 *    there (silent — not one byte —, then no request yet, then writers
 *    ≥ 5 s, then fresh writers), at random among the equals of that tier.
 *  · ⛔ When every group holds ONE (`best` == 1), the OLDEST of the lowest
 *    tier goes instead: refusing there would be a cheap lockout — one slot
 *    per address from as many addresses as slots — and FIFO gives a real
 *    client MAX_CLIENTS - 1 arrivals of margin. */
static client *fair_victim(page *p, unsigned mine, uint64_t now)
{
	unsigned best = 0, sizes[MAX_CLIENTS];
	int low = 4;
	uint32_t ties = 0;
	client *v = NULL;

	group_sizes(p, sizes);
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (sizes[i] > best)
			best = sizes[i];
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
			uint64_t tx = low <= 1 ? x->born : x->write_start;
			uint64_t tv = !v ? UINT64_MAX : low <= 1 ? v->born : v->write_start;
			if (tx < tv)
				v = x;
		} else if (random_below(++ties) == 0) {
			/* Reservoir sampling: each of the `ties` has the same chance. */
			v = x;
		}
	}
	return v;
}

/* The bucket of `key` in `t`, refilled to `now` (`rate` per second up to a
 * burst of `burst`).  A key without one gets a bucket only if some bucket is
 * FULL (refilled to the burst: forgetting it forgets nothing) or empty;
 * otherwise it is charged to `over`, ONE bucket shared by every such key —
 * so rotating more addresses than buckets buys no fresh bursts. */
static struct bucket *bucket_of(struct bucket *t, struct bucket *over,
                                const char *key, uint64_t now, unsigned rate,
                                unsigned burst)
{
	struct bucket *b = NULL, *free_one = NULL;
	unsigned cap = burst * 1000u;

	for (size_t i = 0; i < PAGE_RATE_KEYS; i++) {
		struct bucket *x = &t[i];
		if (x->key[0] && strcmp(x->key, key) == 0) {
			b = x;
			break;
		}
		if (!free_one && (!x->key[0] || (now >= x->at &&
		                  (now - x->at >= (uint64_t)cap / rate ||
		                   x->milli + (now - x->at) * rate >= cap))))
			free_one = x;
	}
	if (!b && free_one) {
		b = free_one;
		snprintf(b->key, sizeof b->key, "%s", key);
		b->milli = cap;
		b->at = now;
	}
	if (!b) {
		b = over;
		if (!b->key[0]) {
			snprintf(b->key, sizeof b->key, "*");
			b->milli = cap;
			b->at = now;
		}
	}
	if (now > b->at) {
		/* ⚠ only forward: a clock that went back refills nothing */
		uint64_t d = now - b->at;
		uint64_t m = d >= (uint64_t)cap / rate ? cap : (uint64_t)b->milli + d * rate;
		b->milli = m > cap ? cap : (unsigned)m;
		b->at = now;
	}
	return b;
}

/* One token from `key`'s bucket — and from the /48's, when `k48` is not
 * NULL — or none: ⚠ when either refuses, NEITHER is spent (review of
 * 95ed70ea: a /48 refusal used to cost the /64 a token).  `*who` = the
 * bucket that refused. */
static void key48_text(const client *c, char k48[64])
{
	snprintf(k48, 64, "%02x%02x:%02x%02x:%02x%02x::/48", c->p48[0], c->p48[1],
	         c->p48[2], c->p48[3], c->p48[4], c->p48[5]);
}

/* `true` = a connection is parked waiting on bucket `b` (or `b48`): a
 * newcomer on the same bucket queues behind it (review of fc76de93).  Each
 * parked one remembers the buckets it last waited on (`qb`, `qb48`, set
 * whenever its rate_take() refuses): a pointer comparison per parked one. */
static bool queue_on(page *p, const struct bucket *b, const struct bucket *b48)
{
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		const client *c = &p->clients[i];
		if (!client_active(c) || c->phase != F_RATE)
			continue;
		if (c->qb == b || (b48 && c->qb48 == b48))
			return true;
	}
	return false;
}

/* One token from `key`'s bucket — and from the /48's, when `k48` is not
 * NULL — or none: ⚠ when either refuses, NEITHER is spent (review of
 * 95ed70ea: a /48 refusal used to cost the /64 a token).  `*who` = the
 * bucket that refused.  `queue`: a newcomer, which waits behind the
 * connections already parked on its bucket.  The buckets taken are kept
 * for rate_refund(). */
static bool rate_take_q(page *p, const char *key, const char *k48, uint64_t now,
                        const char **who, bool queue)
{
	struct bucket *b = bucket_of(p->rate, &p->rate_over, key, now,
	                             PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	struct bucket *b48 = k48 ? bucket_of(p->rate48, &p->rate48_over, k48, now,
	                                     PAGE_ACCEPT_RATE_48, PAGE_ACCEPT_BURST_48)
	                         : NULL;

	p->taken = p->taken48 = NULL;
	p->cand = b;
	p->cand48 = b48;
	if (b->milli < 1000u) {
		*who = b == &p->rate_over ? "(the shared overflow bucket)" : key;
		return false;
	}
	if (b48 && b48->milli < 1000u) {
		*who = b48 == &p->rate48_over ? "(the shared /48 overflow bucket)" : k48;
		return false;
	}
	if (queue && queue_on(p, b, b48)) {
		*who = b == &p->rate_over ? "(the shared overflow bucket, queued)" : key;
		return false;
	}
	b->milli -= 1000u;
	if (b48)
		b48->milli -= 1000u;
	p->taken = b;
	p->taken48 = b48;
	return true;
}

static bool rate_take(page *p, const char *key, const char *k48, uint64_t now,
                      const char **who)
{
	return rate_take_q(p, key, k48, now, who, false);
}

/* The token(s) of the last rate_take() given back: the arrival was then
 * refused anyway (review of fc76de93). */
static void rate_refund(page *p)
{
	if (p->taken && p->taken->milli + 1000u <= PAGE_ACCEPT_BURST * 1000u)
		p->taken->milli += 1000u;
	if (p->taken48 && p->taken48->milli + 1000u <= PAGE_ACCEPT_BURST_48 * 1000u)
		p->taken48->milli += 1000u;
	p->taken = p->taken48 = NULL;
}

/* TLS for `c` (its descriptor accepted): an SSL object, the handshake begun.
 * False if there is no SSL object (then `c` is closed). */
static bool client_start_tls(page *p, client *c)
{
	c->ssl = SSL_new(p->ctx);
	if (!c->ssl) {
		close(c->fd);
		c->fd = -1;
		c->phase = F_DONE;
		return false;
	}
	SSL_set_fd(c->ssl, c->fd);
	/* ⛔ PARTIAL WRITES: without this mode `SSL_write_ex()` reports
	 *    nothing until the WHOLE remaining response is out, so
	 *    `oresponse` would stay 0 for a 907 KB page — and `oresponse` is
	 *    the progress measure where `TCP_INFO` is missing.  With it,
	 *    every record taken counts. */
	SSL_set_mode(c->ssl, SSL_MODE_ENABLE_PARTIAL_WRITE);
	SSL_set_accept_state(c->ssl);
	c->phase = F_HANDSHAKE;
	move_client(p, c, 0);
	return true;
}

/* The parked clients: a token → TLS; waited PAGE_RATE_WAIT_MS in vain →
 * TLS all the same, but `busy` (its request gets 503, which the page tells
 * apart from «not there»).  Called by page_expired() at every pass. */
static void parked_move(page *p, uint64_t now)
{
	/* ⭐ In ARRIVAL order (review of 38639d7d: slot order let a later
	 *   arrival in a lower slot take the shared bucket's token first). */
	client *order[MAX_CLIENTS];
	size_t n = 0;

	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *c = &p->clients[i];
		if (client_active(c) && c->phase == F_RATE) {
			size_t k = n++;
			while (k > 0 && order[k - 1]->park_seq > c->park_seq) {
				order[k] = order[k - 1];
				k--;
			}
			order[k] = c;
		}
	}
	for (size_t i = 0; i < n; i++) {
		client *c = order[i];
		char k48[64];
		const char *who = NULL;
		if (c->has48)
			key48_text(c, k48);
		if (!rate_take(p, c->key, c->has48 ? k48 : NULL, now, &who)) {
			c->qb = p->cand;
			c->qb48 = p->cand48;
			if (now < c->rate_until)
				continue;
			c->busy = true;
			c->busy_shared = who && who[0] == '(';
			p->busy_rate++;
			snprintf(p->refused_last, sizeof p->refused_last, "%s", who);
		}
		client_start_tls(p, c);
	}
}

static int accept_page(page *p, int budget)
{
	/* ⚠ At most PAGE_ACCEPTS_PER_CALL (32) accepts per call, and no more
	 *   than `page_move()`'s budget left (refused ones included): a
	 *   backlog that refills as fast as it is drained would otherwise keep
	 *   the whole loop — QUIC, the children, PAM — inside this function.
	 *   What is left stays in the backlog, and the `poll` (level-triggered)
	 *   calls again at the next pass. */
	int round;

	/* ⭐ The parked FIRST (review of fc76de93): a newcomer must not take
	 *   the token they have been waiting for. */
	parked_move(p, log_now_ms());
	for (round = 0; round < PAGE_ACCEPTS_PER_CALL && round < budget; round++) {
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
			return round;
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
		/* ⛔ The accept rate BEFORE any eviction (review of 38639d7d): an
		 *    arrival over its rate never evicts anybody — it waits, parked,
		 *    in a slot that is FREE, or it is refused.  Checked after the
		 *    per-address caps, which cost nothing. */
		bool over_rate;
		const char *rate_who = NULL;
		/* ⚠ Here, not in a block: `rate_who` may point into it (the fuzzer,
		 *   ASan stack-use-after-scope). */
		char rate_k48[64];
		if (has48)
			snprintf(rate_k48, sizeof rate_k48, "%02x%02x:%02x%02x:%02x%02x::/48",
			         p48[0], p48[1], p48[2], p48[3], p48[4], p48[5]);
		over_rate = !rate_take_q(p, key, has48 ? rate_k48 : NULL, now, &rate_who, true);
		if (over_rate && !c) {
			p->refused_rate++;
			p->refused_rate_total++;
			snprintf(p->refused_last, sizeof p->refused_last, "%s", rate_who);
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
			 * ⚠ Reached only when the newcomer's group would become larger
			 *   than the largest live group: within that group any client
			 *   can be evicted, fresh writers too (the last tier). */
			p->refused_full++;
			rate_refund(p);
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
		c->accepted_in = p->move_calls;

		/* ⛔ The accept rate (holistic review, 15 Oct 2026; reviews of
		 *    95ed70ea and 38639d7d): every connection costs a TLS handshake
		 *    and maybe a page.  Over PAGE_ACCEPT_RATE a second per key (and
		 *    PAGE_ACCEPT_RATE_48 per /48) it is PARKED in this FREE slot,
		 *    without TLS, served in arrival order (`park_seq`) — not closed:
		 *    a closed one made the page say «the server is not there». */
		if (over_rate) {
			c->qb = p->cand;
			c->qb48 = p->cand48;
			c->phase = F_RATE;
			c->rate_until = now + PAGE_RATE_WAIT_MS;
			c->park_seq = ++p->park_next;
			p->delayed_rate++;
			p->delayed_rate_total++;
			snprintf(p->refused_last, sizeof p->refused_last, "%s", rate_who);
			continue;
		}
		if (!client_start_tls(p, c))
			return round + 1;
	}
	return round;
}

void page_expired(page *p, uint64_t now)
{
	parked_move(p, now);
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
		/* a parked one: a token comes every 1000 / PAGE_ACCEPT_RATE ms */
		if (client_active(c) && c->phase == F_RATE && now + 50 < before)
			before = now + 50;
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
	/* ⭐ At most PAGE_EVENTS_PER_PASS events, starting where the last call
	 *   stopped (round robin): the descriptors not reached keep their
	 *   `revents` for the next `poll`, level-triggered. */
	int budget = PAGE_EVENTS_PER_PASS;
	size_t start = amount ? p->move_next % amount : 0;

	p->move_calls++;

	for (size_t j = 0; j < amount && budget > 0; j++) {
		size_t k = (start + j) % amount;
		if (dove[k].revents == 0)
			continue;
		p->move_next = k + 1;
		if (dove[k].fd == p->fd) {
			/* each accept is an event (refused ones too); the last
			 * attempt that found the backlog empty is one as well */
			int used = accept_page(p, budget);
			budget -= used > 0 ? used : 1;
			continue;
		}
		budget--;
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (p->clients[i].fd == dove[k].fd &&
			    p->clients[i].phase != F_DONE) {
				/* ⚠ accepted in THIS call: the descriptor number was
				 *   another client's when `poll` filled `revents` */
				if (p->clients[i].accepted_in != p->move_calls)
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
		if (bind(fd, r->ai_addr, r->ai_addrlen) == 0 && listen(fd, PAGE_BACKLOG) == 0)
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
	body_unref(p->cached_gz);
	body_unref(p->tail);
	body_unref(p->tail_gz);
	free(p->html);
	if (p->fd >= 0)
		close(p->fd);
	free(p);
}
