/*
 * fuzz_page.c — libFuzzer harness of the HTTP listener `src/page.c` (the login page, `/fingerprint`, gzip, the slot table, the
 * accept rate, the slow-writer rules, the log lines of a request).
 *
 * ⭐ `page.c` is the REAL file, `#include`d and UNMODIFIED.  What it asks of the kernel and of OpenSSL is PLAYED here: `accept4`,
 * `getnameinfo`, `close`, `getsockopt(TCP_INFO)`, `setsockopt(SO_LINGER)`, the `SSL_*` calls and `RAND_bytes` are renamed by
 * `#define` AFTER every system header is in, in this file only; `malloc`/`calloc`/`realloc`/`free` too (zlib allocates through
 * page.c's own `gz_alloc`, so it is on the same seam).  `src/rcp.c` is linked as it is (`rcp_key_address()` makes the key of
 * every address); `rcp_banned()` is played, so that the banned path IS fuzzed (the previous fuzz never reached it).
 * ⇒ No sockets, no TLS: the fuzzer says what the peers do.  Time is `rx_now_ms` (stubs_log.c's `log_now_ms()`).
 *
 * Input: byte 0 = configuration (bit 0: the page is ~200 KB, so that the rate arithmetic of a slow writer is reached; bit 1:
 * TCP_INFO does not answer; bit 2: every connection trickles its bytes one at a time) then the ops of `common.h`
 * (`u8 op · u16 length · argument`), op % 10:
 *   0 CONNECT  a0 address (palette of 16: IPv4, several ports of one address, IPv6 in one /64, one /48, two /48s, v4-mapped, NAT64,
 *              ::1, link-local) · a1 bits 0-2 handshake (0 at once · 1 wants a write first · 2 fails · 3 a partial hello, never
 *              done · 4 the server replied, never done) · bit 3 the ClientHello is already there · bit 4 the peer half-closes
 *              after sending · a2 bytes the SSL_read_ex gives at most (0 = all) · a3 canned request: 0 none · 1 GET / · 2 GET /
 *              with Accept-Encoding: gzip · 3 GET /fingerprint · 4 gzip;q=0 · 5 two requests pipelined · 6 HEAD / · 7 POST / with a
 *              body · 8 a request line with no second space · 9 an obs-fold header · 10 a path of 3000 bytes · 11 a 70 KB header
 *              · 12 a NUL in the middle · 13 a CR/LF-forged target · 14 Accept-Encoding with an empty parameter ·
 *              the rest of the argument is appended to the bytes the peer sends
 *   1 SEND     a0 which connection (of the live ones) · a1 bit 0 the ClientHello arrives · bit 1 the peer half-closes · the rest is
 *              appended to the request
 *   2 MOVE     poll: a0 bits: 0 POLLERR added · 1 POLLHUP · 2 POLLIN on everything (spurious) · 3 report nothing honest ·
 *              4 one poll() for the descriptors of a closed-and-reused number: the honest events are reported ONCE and then
 *              page_move() is called twice with the same array (events for descriptors that may have changed owner)
 *   3 TIME     u16 ms (× 1000 if a2 bit 0) — advanced in steps of at most 1000 ms, `page_expired()` at every step, as the main loop
 *              does (`page_wait_ms()` ≤ 1000)
 *   4 ACK      a0 which connection · u32 more bytes the peer acknowledges (cumulative; 0xFFFFFFFF = everything written)
 *   5 WINDOW   a0 which connection · u32 more bytes SSL_write_ex may take (0xFFFFFFFF = unlimited), a5 the largest piece (0 = 16 KB)
 *   6 KNOB     a0 the Nth next allocation fails (0 = none) · a1 accept fails with errno (0 none · EAGAIN · EMFILE · EINTR · ECONNABORTED)
 *              · a2 TCP_INFO mode (0 answers · 1 fails · 2 too short · 3 answers but never moves) · a3 the next SSL_new fails ·
 *              a4-5 banned palette addresses (bit mask, 16 bits) · a6 RAND_bytes fails · a7 getnameinfo fails for the next accept
 *              · a8 the certificate fingerprint rotates
 *   7 PEER     a0 which connection · the peer resets (a1 bit 0: after a close) — POLLHUP/POLLERR on the next MOVE
 *   8 BURST    a0 how many (+ 1, up to 64) connections, a1 first palette address (rotates), a2 bits: 0 all from the SAME address
 *              · 1 each sends a whole ClientHello and `GET /` · 2 one byte only · 3 half-close.  A MOVE follows.
 *   9 FINISH   the peers drain: everything written acknowledged, windows opened, then MOVE (a1: MOVE count 1-4)
 * At the end of every input the harness advances the clock by 200 s in steps and requires the table to be EMPTY (every slot
 * has a deadline), then page_close() leaves nothing (LeakSanitizer).
 *
 * ORACLES.  ASan + UBSan (halt), -rss_limit_mb / -malloc_limit_mb, and ASSERTIONS (a failed one prints «INVARIANT:» and traps):
 *  H1 a response is well framed: «HTTP/1.1 NNN», headers, a blank line, `Content-Length` = the bytes that follow, NOTHING after;
 *     PAGE_SECURITY on every response (not only the html one);
 *     one response per connection (a pipelined second request never gets a second answer); the isolation headers, `Cache-Control:
 *     no-store`, `nosniff`, `Connection: close` always
 *  H2 the status is the one an INDEPENDENT reading of the request gives: 400 (no second space in the request LINE, or an obs-fold
 *     header), 431 (8191 bytes with no end of head), 503 for a connection that waited for the rate, then 200 for «/», «/index.html»
 *     and «/fingerprint» (the path cut at «?» «#» and at a NUL), 404 for the rest — the method is not looked at (HEAD gets the body
 *     too: the product, not asserted)
 *  H3 a 200 html carries PAGE_SECURITY and `Vary: Accept-Encoding`; gzip («Content-Encoding: gzip») only if the request names gzip,
 *     x-gzip or * with a q that is not zero (a LIBERAL reading: the product may refuse more, never less), and the body INFLATES
 *     (zlib checks CRC and length) to the plain page — or, if the certificate rotated meanwhile, at least inflates; a banned
 *     visitor's page says data-banned="yes", the others «no»; no marker `__X__` is left in a page
 *  H4 the table: active ⇒ fd, in a live connection; F_DONE ⇒ no fd, no SSL, no head; parked (F_RATE) ⇒ no SSL; at most 4 live per
 *     address key, at most 8 per real IPv6 /48 (not v4-mapped, NAT64 nor ::1), at most 128; `nresponse` = head + shared + tail;
 *     bodies' reference counts = the cache's + the clients' holding them; no allocation beyond 16 MiB live
 *  H5 deadlines — in BOTH directions, against a shadow of the peer's acknowledgements: after `page_expired(now)` nobody is alive
 *     past born + 10 s before the response, nor (writing) past 60 s without a new acknowledged byte, nor past write_start +
 *     max(20 s, delivered / 2 KB/s) — and nobody is closed EARLIER by it.  `page_wait_ms()` is never -1 with a client alive, never
 *     beyond the next deadline, never above 1000
 *  H6 the accept rate: connections that got TLS without having waited 3 s (the busy 503 ones excepted) per address key ≤ 8 + 4/s,
 *     per /48 ≤ 16 + 8/s; a parked connection has no SSL calls and starts TLS by its wait at the latest
 *  H7 «spoke» (the owner protection of the eviction) is true only of a connection whose handshake completed or whose server
 *     reply began; an eviction (a victim closed with SO_LINGER 0 inside a MOVE) happens only with all 128 slots taken and takes a
 *     member of the largest group, of the lowest tier among them, the oldest of them when the group is a single connection
 *  H8 the log: no event line carries a byte below 0x20 or 0x7F (no forged lines); a target is cut at 200 bytes
 *  H9 the OS calls: no SSL_accept/read/write on a freed SSL or on a parked one; SSL_read before the handshake is done; a double
 *     close; getsockopt on a closed descriptor; accept4 without SOCK_NONBLOCK
 */
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/socket.h>
#include <unistd.h>
#include <poll.h>
#include <openssl/err.h>
#include <openssl/rand.h>
#include <openssl/ssl.h>
#include <zlib.h>
#include <linux/tcp.h>

#include "page.h"
#include "rcp.h"
#include "log.h"
#include "common.h"

extern void (*rx_event_line)(const char *text); /* stubs_log.c: each EVENT line, formatted */

#define FAIL(...) do { fprintf(stderr, "INVARIANT: " __VA_ARGS__); fputc('\n', stderr); __builtin_trap(); } while (0)

/* ── the seam of the allocations, the sockets and OpenSSL: renamed ONLY inside page.c ── */
static unsigned alloc_fail_total;
static void *fz_malloc(size_t n);
static void *fz_calloc(size_t a, size_t b);
static void *fz_realloc(void *p, size_t n);
static void fz_free(void *p);
static int fz_close(int fd);
static int fz_accept4(int fd, struct sockaddr *sa, socklen_t *len, int flags);
static int fz_getnameinfo(const struct sockaddr *sa, socklen_t salen, char *host, socklen_t hostlen, char *serv,
                          socklen_t servlen, int flags);
static int fz_getsockopt(int fd, int level, int opt, void *val, socklen_t *len);
static int fz_setsockopt(int fd, int level, int opt, const void *val, socklen_t len);
static SSL *fz_SSL_new(SSL_CTX *ctx);
static void fz_SSL_free(SSL *s);
static int fz_SSL_set_fd(SSL *s, int fd);
static long fz_SSL_ctrl(SSL *s, int cmd, long larg, void *parg);
static void fz_SSL_set_accept_state(SSL *s);
static int fz_SSL_accept(SSL *s);
static int fz_SSL_get_error(const SSL *s, int rv);
static int fz_SSL_read_ex(SSL *s, void *buf, size_t num, size_t *readbytes);
static int fz_SSL_write_ex(SSL *s, const void *buf, size_t num, size_t *written);
static int fz_SSL_shutdown(SSL *s);
static int fz_SSL_get_state(const SSL *s);
static void fz_ERR_clear_error(void);
static int fz_RAND_bytes(unsigned char *buf, int num);
static bool fz_rcp_banned(const char *address, uint64_t now, uint64_t *remain);
#define malloc(n) fz_malloc(n)
#define calloc(a, b) fz_calloc(a, b)
#define realloc(p, n) fz_realloc(p, n)
#define free(p) fz_free(p)
#define close(fd) fz_close(fd)
#define accept4(fd, sa, len, fl) fz_accept4(fd, sa, len, fl)
#define getnameinfo(a, b, c, d, e, f, g) fz_getnameinfo(a, b, c, d, e, f, g)
#define getsockopt(a, b, c, d, e) fz_getsockopt(a, b, c, d, e)
#define setsockopt(a, b, c, d, e) fz_setsockopt(a, b, c, d, e)
#define SSL_new(c) fz_SSL_new(c)
#define SSL_free(s) fz_SSL_free(s)
#define SSL_set_fd(s, fd) fz_SSL_set_fd(s, fd)
#define SSL_ctrl(s, c, l, p) fz_SSL_ctrl(s, c, l, p)
#define SSL_set_accept_state(s) fz_SSL_set_accept_state(s)
#define SSL_accept(s) fz_SSL_accept(s)
#define SSL_get_error(s, rv) fz_SSL_get_error(s, rv)
#define SSL_read_ex(s, b, n, r) fz_SSL_read_ex(s, b, n, r)
#define SSL_write_ex(s, b, n, w) fz_SSL_write_ex(s, b, n, w)
#define SSL_shutdown(s) fz_SSL_shutdown(s)
#define SSL_get_state(s) fz_SSL_get_state(s)
#define ERR_clear_error() fz_ERR_clear_error()
#define RAND_bytes(b, n) fz_RAND_bytes(b, n)
#define rcp_banned(a, n, r) fz_rcp_banned(a, n, r)

#include "page.c"

#undef SSL_new
#undef SSL_free
#undef SSL_set_fd
#undef SSL_ctrl
#undef SSL_set_accept_state
#undef SSL_accept
#undef SSL_get_error
#undef SSL_read_ex
#undef SSL_write_ex
#undef SSL_shutdown
#undef SSL_get_state
#undef ERR_clear_error
#undef RAND_bytes

#undef malloc
#undef calloc
#undef realloc
#undef free
#undef close
#undef accept4
#undef getnameinfo
#undef getsockopt
#undef setsockopt
#undef rcp_banned

/* ═══════════════ the played world ═══════════════ */
#define FD0 100
#define NFD 400
#define MAXCONN 600
#define IN_MAX (80 * 1024)
#define HS_TAIL 700u
#define UNLIM UINT64_MAX
#define LIVE_BYTES_MAX (16u << 20)
#define ALLOC_MAX (4u << 20)

typedef struct fconn {
	bool used, queued, accepted, closed, peer_closed, peer_reset, hello, hs_done, hs_wrote, replied, shut, aborted;
	bool banned_at_serve, served;
	int fd, pal;
	unsigned hs_mode, state;
	struct sockaddr_storage sa;
	socklen_t salen;
	uint8_t *in;
	size_t nin, rin, rchunk;
	uint8_t *out;
	size_t nout, cap_out, piece;
	uint64_t wlimit;
	uint64_t acked, acked_base, taken, shadow_delivered, shadow_progress;
	uint64_t gen_at_serve;
	bool shadow_on, tcp_ok_at_compose;
	void *ssl;
} fconn;

typedef struct {
	uint32_t magic;
	fconn *c;
	bool fd_set, accept_state, partial, freed;
	int err;
} fz_ssl_t;
#define SSL_MAGIC 0x55aa1357u

static fconn conns[MAXCONN];
static size_t nconns;
static fconn *fd_owner[NFD];
static fconn *pending[MAXCONN];
static size_t npending;
static page *P;
static certificates CERT;
static char *HTML;
static size_t NHTML;
static bool tcp_unavailable_cfg;
static unsigned tcp_mode, accept_errno, fail_alloc_in, fail_ssl_new, fail_rand, fail_getname;
static uint16_t banned_mask;
static uint64_t gen_fp;
static size_t live_bytes;
static uint64_t t0_ms;
static bool in_expiry, in_move;
static unsigned evictions_in_move;
static int ssl_live;

#define NPAL 16
static struct sockaddr_storage PAL[NPAL];
static socklen_t PALLEN[NPAL];
static char PALKEY[NPAL][64];

static void pal_init(void)
{
	static const char *const V4[] = {"10.0.0.1", "10.0.0.1", "10.0.0.2", "192.0.2.7"};
	static const char *const V6[] = {"2001:db8:1::1", "2001:db8:1::2", "2001:db8:1:0:1::3", "2001:db8:2::1", "::ffff:10.0.0.1",
	                                 "64:ff9b::a00:1", "::1", "fe80::1", "2001:db8:1::1", "198.51.100.9", "203.0.113.5",
	                                 "10.0.0.3"};
	for (int i = 0; i < NPAL; i++) {
		memset(&PAL[i], 0, sizeof PAL[i]);
		if (i < 4) {
			struct sockaddr_in *a = (struct sockaddr_in *)&PAL[i];
			a->sin_family = AF_INET;
			a->sin_port = htons((uint16_t)(1000 + i));
			inet_pton(AF_INET, V4[i], &a->sin_addr);
			PALLEN[i] = sizeof *a;
		} else if (i == 13 || i == 14 || i == 15) {
			struct sockaddr_in *a = (struct sockaddr_in *)&PAL[i];
			a->sin_family = AF_INET;
			a->sin_port = htons((uint16_t)(2000 + i));
			inet_pton(AF_INET, V6[i - 4], &a->sin_addr);
			PALLEN[i] = sizeof *a;
		} else {
			struct sockaddr_in6 *a = (struct sockaddr_in6 *)&PAL[i];
			a->sin6_family = AF_INET6;
			a->sin6_port = htons((uint16_t)(3000 + i));
			inet_pton(AF_INET6, V6[i - 4], &a->sin6_addr);
			PALLEN[i] = sizeof *a;
		}
	}
}

/* the provenance string page.c makes from an address, and its key (the real rcp_key_address) */
static void pal_key(int i, char key[64])
{
	char host[NI_MAXHOST], serv[NI_MAXSERV], prov[80];
	fz_getnameinfo((struct sockaddr *)&PAL[i], PALLEN[i], host, sizeof host, serv, sizeof serv, NI_NUMERICHOST | NI_NUMERICSERV);
	snprintf(prov, sizeof prov, PAL[i].ss_family == AF_INET6 ? "[%s]:%s" : "%s:%s", host, serv);
	rcp_key_address(prov, key, 64);
}

/* ── allocation seam ── */
typedef struct { size_t n; uint64_t magic; } ahdr;
#define AMAGIC 0xA110C8EDull
static bool alloc_fails(void)
{
	if (fail_alloc_in && --fail_alloc_in == 0) {
		alloc_fail_total++;
		return true;
	}
	return false;
}
static void *fz_malloc(size_t n)
{
	ahdr *h;
	if (alloc_fails())
		return NULL;
	if (n > ALLOC_MAX)
		FAIL("one allocation of %zu bytes (page.c asked for it)", n);
	if (live_bytes + n > LIVE_BYTES_MAX)
		FAIL("%zu bytes live and %zu more asked: unbounded growth", live_bytes, n);
	h = (malloc)(sizeof *h + n);
	if (!h)
		return NULL;
	h->n = n;
	h->magic = AMAGIC;
	live_bytes += n;
	return h + 1;
}
static void *fz_calloc(size_t a, size_t b)
{
	void *p;
	if (b && a > (size_t)-1 / b)
		return NULL;
	p = fz_malloc(a * b);
	if (p)
		memset(p, 0, a * b);
	return p;
}
static void fz_free(void *p)
{
	ahdr *h;
	if (!p)
		return;
	h = (ahdr *)p - 1;
	if (h->magic != AMAGIC)
		FAIL("free() of something that is not an allocation of the seam");
	live_bytes -= h->n;
	h->magic = 0;
	(free)(h);
}
static void *fz_realloc(void *p, size_t n)
{
	void *q;
	ahdr *h;
	if (!p)
		return fz_malloc(n);
	h = (ahdr *)p - 1;
	if (h->magic != AMAGIC)
		FAIL("realloc() of something that is not an allocation of the seam");
	q = fz_malloc(n);
	if (!q)
		return NULL;
	memcpy(q, p, h->n < n ? h->n : n);
	fz_free(p);
	return q;
}

/* ── sockets ── */
static fconn *by_fd(int fd) { return (fd >= FD0 && fd < FD0 + NFD) ? fd_owner[fd - FD0] : NULL; }

static void check_response(fconn *c);
static int fz_close(int fd)
{
	fconn *c = by_fd(fd);
	if (fd == P->fd)
		FAIL("the listening descriptor was closed");
	if (!c || c->closed)
		FAIL("close(%d): a double close, or a descriptor that is not ours", fd);
	c->closed = true;
	fd_owner[fd - FD0] = NULL;
	check_response(c);
	return 0;
}
static int fz_accept4(int fd, struct sockaddr *sa, socklen_t *len, int flags)
{
	fconn *c;
	if (fd != P->fd)
		FAIL("accept4 on a descriptor that is not the listening one");
	if (!(flags & SOCK_NONBLOCK))
		FAIL("accept4 without SOCK_NONBLOCK: the listener would block the whole loop");
	if (accept_errno) {
		errno = (int)accept_errno;
		return -1;
	}
	if (!npending) {
		errno = EAGAIN;
		return -1;
	}
	c = pending[0];
	memmove(pending, pending + 1, (--npending) * sizeof pending[0]);
	for (int i = 0; i < NFD; i++)
		if (!fd_owner[i]) {
			c->fd = FD0 + i;
			fd_owner[i] = c;
			c->accepted = true;
			c->queued = false;
			if (*len < c->salen)
				FAIL("accept4: the address does not fit");
			memcpy(sa, &c->sa, c->salen);
			*len = c->salen;
			return c->fd;
		}
	errno = EMFILE;
	c->closed = true;
	return -1;
}
static int fz_getnameinfo(const struct sockaddr *sa, socklen_t salen, char *host, socklen_t hostlen, char *serv, socklen_t servlen,
                          int flags)
{
	(void)salen; (void)flags;
	if (fail_getname) {
		fail_getname = 0;
		return EAI_FAIL;
	}
	if (sa->sa_family == AF_INET) {
		const struct sockaddr_in *a = (const struct sockaddr_in *)sa;
		inet_ntop(AF_INET, &a->sin_addr, host, hostlen);
		snprintf(serv, servlen, "%u", ntohs(a->sin_port));
	} else {
		const struct sockaddr_in6 *a = (const struct sockaddr_in6 *)sa;
		inet_ntop(AF_INET6, &a->sin6_addr, host, hostlen);
		snprintf(serv, servlen, "%u", ntohs(a->sin6_port));
	}
	return 0;
}
static int fz_getsockopt(int fd, int level, int opt, void *val, socklen_t *len)
{
	fconn *c = by_fd(fd);
	struct tcp_info ti;
	if (!c || c->closed)
		FAIL("getsockopt on descriptor %d, which is not an open connection", fd);
	if (level != IPPROTO_TCP || opt != TCP_INFO) {
		errno = ENOPROTOOPT;
		return -1;
	}
	if (tcp_unavailable_cfg || tcp_mode == 1) {
		errno = ENOPROTOOPT;
		return -1;
	}
	memset(&ti, 0, sizeof ti);
	ti.tcpi_bytes_acked = tcp_mode == 3 ? 0 : c->acked;
	if (tcp_mode == 2) {
		size_t k = offsetof(struct tcp_info, tcpi_bytes_acked);
		if (*len > k)
			*len = (socklen_t)k;
		memcpy(val, &ti, *len);
		return 0;
	}
	if (*len > sizeof ti)
		*len = sizeof ti;
	memcpy(val, &ti, *len);
	return 0;
}
static void check_victim(fconn *v);
static int fz_setsockopt(int fd, int level, int opt, const void *val, socklen_t len)
{
	fconn *c = by_fd(fd);
	if (!c || c->closed)
		FAIL("setsockopt on descriptor %d, which is not an open connection", fd);
	if (level == SOL_SOCKET && opt == SO_LINGER && len >= sizeof(struct linger)) {
		const struct linger *l = val;
		if (l->l_onoff && l->l_linger == 0) {
			c->aborted = true;
			if (in_move && !in_expiry)
				check_victim(c);
		}
	}
	return 0;
}

/* ── OpenSSL ── */
static fz_ssl_t *S(const SSL *s, const char *fn)
{
	fz_ssl_t *x = (fz_ssl_t *)(uintptr_t)s;
	if (!x || x->magic != SSL_MAGIC)
		FAIL("%s on an SSL that is freed or not ours", fn);
	return x;
}
static SSL *fz_SSL_new(SSL_CTX *ctx)
{
	fz_ssl_t *x;
	(void)ctx;
	if (fail_ssl_new) {
		fail_ssl_new = 0;
		return NULL;
	}
	x = (calloc)(1, sizeof *x);
	x->magic = SSL_MAGIC;
	ssl_live++;
	return (SSL *)(uintptr_t)x;
}
static void fz_SSL_free(SSL *s)
{
	fz_ssl_t *x = S(s, "SSL_free");
	if (x->c)
		x->c->ssl = NULL;
	x->magic = 0;
	ssl_live--;
	(free)(x);
}
static void rate_start(fconn *c);
static void mark_served(fconn *c);
static int fz_SSL_set_fd(SSL *s, int fd)
{
	fz_ssl_t *x = S(s, "SSL_set_fd");
	fconn *c = by_fd(fd);
	if (!c || c->closed)
		FAIL("SSL_set_fd on a descriptor that is not an open connection");
	x->c = c;
	x->fd_set = true;
	c->ssl = x;
	rate_start(c);
	return 1;
}
static long fz_SSL_ctrl(SSL *s, int cmd, long larg, void *parg)
{
	fz_ssl_t *x = S(s, "SSL_ctrl");
	(void)parg;
	if (cmd == SSL_CTRL_MODE && (larg & SSL_MODE_ENABLE_PARTIAL_WRITE))
		x->partial = true;
	return 0;
}
static void fz_SSL_set_accept_state(SSL *s) { S(s, "SSL_set_accept_state")->accept_state = true; }
static fconn *sc(fz_ssl_t *x, const char *fn)
{
	if (!x->c || !x->fd_set)
		FAIL("%s before SSL_set_fd", fn);
	if (x->c->closed)
		FAIL("%s on a connection already closed", fn);
	return x->c;
}
static int fz_SSL_accept(SSL *s)
{
	fz_ssl_t *x = S(s, "SSL_accept");
	fconn *c = sc(x, "SSL_accept");
	if (!x->accept_state)
		FAIL("SSL_accept without SSL_set_accept_state");
	if (c->hs_done)
		return 1;
	if (c->peer_reset || (c->peer_closed && !c->hello)) {
		x->err = SSL_ERROR_SYSCALL;
		return -1;
	}
	if (!c->hello) {
		c->state = TLS_ST_BEFORE;
		x->err = SSL_ERROR_WANT_READ;
		return -1;
	}
	switch (c->hs_mode) {
	case 0:
		c->hs_done = c->replied = true;
		c->state = TLS_ST_OK;
		return 1;
	case 1:
		if (!c->hs_wrote) {
			c->hs_wrote = true;
			c->state = TLS_ST_SW_SRVR_HELLO;
			c->replied = true;
			x->err = SSL_ERROR_WANT_WRITE;
			return -1;
		}
		c->hs_done = true;
		c->state = TLS_ST_OK;
		return 1;
	case 2:
		c->state = TLS_ST_SR_CLNT_HELLO;
		x->err = SSL_ERROR_SSL;
		return -1;
	case 3:
		c->state = TLS_ST_SR_CLNT_HELLO;
		x->err = SSL_ERROR_WANT_READ;
		return -1;
	default:
		c->state = TLS_ST_SW_SRVR_HELLO;
		c->replied = true;
		x->err = SSL_ERROR_WANT_READ;
		return -1;
	}
}
static int fz_SSL_get_error(const SSL *s, int rv)
{
	fz_ssl_t *x = S(s, "SSL_get_error");
	(void)rv;
	return x->err;
}
static int fz_SSL_get_state(const SSL *s)
{
	fz_ssl_t *x = S(s, "SSL_get_state");
	return x->c ? (int)x->c->state : (int)TLS_ST_BEFORE;
}
static int fz_SSL_read_ex(SSL *s, void *buf, size_t num, size_t *readbytes)
{
	fz_ssl_t *x = S(s, "SSL_read_ex");
	fconn *c = sc(x, "SSL_read_ex");
	size_t avail, n;
	if (!c->hs_done)
		FAIL("SSL_read_ex before the handshake completed (the page went to F_READ too soon)");
	if (!x->accept_state)
		FAIL("SSL_read_ex without accept state");
	if (c->served && c->shut)
		FAIL("SSL_read_ex after the response was finished");
	if (num == 0)
		FAIL("SSL_read_ex with a zero-byte buffer");
	*readbytes = 0;
	avail = c->nin - c->rin;
	if (!avail) {
		x->err = (c->peer_closed || c->peer_reset) ? (c->peer_reset ? SSL_ERROR_SYSCALL : SSL_ERROR_ZERO_RETURN)
		                                           : SSL_ERROR_WANT_READ;
		return 0;
	}
	n = avail < num ? avail : num;
	if (c->rchunk && n > c->rchunk)
		n = c->rchunk;
	memcpy(buf, c->in + c->rin, n);
	c->rin += n;
	*readbytes = n;
	return 1;
}
static int fz_SSL_write_ex(SSL *s, const void *buf, size_t num, size_t *written)
{
	fz_ssl_t *x = S(s, "SSL_write_ex");
	fconn *c = sc(x, "SSL_write_ex");
	size_t n;
	*written = 0;
	if (!c->hs_done)
		FAIL("SSL_write_ex before the handshake completed");
	if (!x->partial)
		FAIL("SSL_write_ex without SSL_MODE_ENABLE_PARTIAL_WRITE: a retry with an advanced buffer is illegal");
	if (c->shut)
		FAIL("SSL_write_ex after SSL_shutdown");
	if (num == 0)
		FAIL("SSL_write_ex of zero bytes");
	mark_served(c);
	if (c->peer_reset) {
		x->err = SSL_ERROR_SYSCALL;
		return 0;
	}
	if (c->wlimit == 0) {
		x->err = SSL_ERROR_WANT_WRITE;
		return 0;
	}
	n = num;
	if (c->piece && n > c->piece)
		n = c->piece;
	if (n > 16384)
		n = 16384;
	if (c->wlimit != UNLIM && n > c->wlimit)
		n = (size_t)c->wlimit;
	if (c->nout + n > c->cap_out) {
		size_t nc = c->cap_out ? c->cap_out * 2 : 4096;
		while (nc < c->nout + n)
			nc *= 2;
		c->out = (realloc)(c->out, nc);
		c->cap_out = nc;
	}
	memcpy(c->out + c->nout, buf, n);
	c->nout += n;
	c->taken += n;
	if (c->wlimit != UNLIM)
		c->wlimit -= n;
	*written = n;
	return 1;
}
static int fz_SSL_shutdown(SSL *s)
{
	fz_ssl_t *x = S(s, "SSL_shutdown");
	fconn *c = sc(x, "SSL_shutdown");
	c->shut = true;
	return 1;
}
static void fz_ERR_clear_error(void) {}
static uint32_t rngs = 0x2545F491u;
static int fz_RAND_bytes(unsigned char *buf, int num)
{
	if (fail_rand)
		return 0;
	for (int i = 0; i < num; i++) {
		rngs ^= rngs << 13; rngs ^= rngs >> 17; rngs ^= rngs << 5;
		buf[i] = (unsigned char)rngs;
	}
	return 1;
}
static bool fz_rcp_banned(const char *address, uint64_t now, uint64_t *remain)
{
	(void)now;
	for (int i = 0; i < NPAL; i++)
		if (((banned_mask >> i) & 1) && strcmp(PALKEY[i], address) == 0) {
			if (remain)
				*remain = 90 * 60000ull;
			return true;
		}
	if (remain)
		*remain = 0;
	return false;
}

/* ═══════════════ the oracles ═══════════════ */
static void event_line(const char *text)
{
	for (const unsigned char *q = (const unsigned char *)text; *q; q++)
		if (*q < 0x20 || *q == 0x7f)
			FAIL("H8: a log line carries the byte %#x (a forged line?): %.80s", *q, text);
	if (strlen(text) > 3000)
		FAIL("H8: a log line of %zu bytes", strlen(text));
}

/* the client of the page that owns this connection, or NULL */
static client *client_of(const fconn *c)
{
	if (c->closed || !c->accepted)
		return NULL;
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (P->clients[i].fd == c->fd && P->clients[i].phase != F_DONE)
			return &P->clients[i];
	return NULL;
}

static struct { char key[64]; unsigned n; } RT[NFD], RT48[NFD];
static unsigned *rate_cell(typeof(RT) t, const char *key)
{
	for (size_t i = 0; i < NFD; i++) {
		if (!t[i].key[0]) {
			snprintf(t[i].key, sizeof t[i].key, "%s", key);
			return &t[i].n;
		}
		if (strcmp(t[i].key, key) == 0)
			return &t[i].n;
	}
	return NULL;
}
/* H6: a connection that got TLS WITHOUT the 503 (so it spent a token): per key ≤ 8 + 4/s, per /48 ≤ 16 + 8/s */
static void rate_start(fconn *c)
{
	client *k = client_of(c);
	uint64_t ms = rx_now_ms - t0_ms;
	unsigned *cnt;
	if (!k)
		FAIL("H6: SSL_set_fd for a connection that is in no client");
	if (k->busy)
		return;
	if ((cnt = rate_cell(RT, k->key)) != NULL) {
		(*cnt)++;
		if (*cnt > 8u + (unsigned)(4u * ms / 1000u) + 1u)
			FAIL("H6: %u connections of %s got TLS in %llu ms (burst 8, 4/s)", *cnt, k->key, (unsigned long long)ms);
	}
	if (k->has48) {
		char k48[64];
		key48_text(k, k48);
		if ((cnt = rate_cell(RT48, k48)) != NULL) {
			(*cnt)++;
			if (*cnt > 16u + (unsigned)(8u * ms / 1000u) + 1u)
				FAIL("H6: %u connections of %s got TLS in %llu ms (burst 16, 8/s)", *cnt, k48, (unsigned long long)ms);
		}
	}
}

static int ref_tier(const client *x, uint64_t now)
{
	if (x->phase != F_WRITE)
		return x->spoke || x->phase == F_RATE || (now >= x->born && now - x->born < PAGE_YOUNG_MS) ? 1 : 0;
	return now - x->write_start >= PAGE_EVICT_AGE_MS ? 2 : 3;
}
static bool ref_same_group(const client *a, const client *b)
{
	if (a->has48 || b->has48)
		return a->has48 && b->has48 && memcmp(a->p48, b->p48, 6) == 0;
	return strcmp(a->key, b->key) == 0;
}
/* H7: a victim closed with SO_LINGER 0 inside a MOVE (an eviction) */
static void check_victim(fconn *vc)
{
	client *v = client_of(vc);
	unsigned best = 0, active = 0, mine = 0;
	int low = 4;
	if (!v)
		return;
	evictions_in_move++;
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *x = &P->clients[i];
		unsigned n = 0;
		if (!client_active(x))
			continue;
		active++;
		for (size_t j = 0; j < MAX_CLIENTS; j++)
			if (client_active(&P->clients[j]) && ref_same_group(x, &P->clients[j]))
				n++;
		if (n > best)
			best = n;
		if (x == v)
			mine = n;
	}
	if (active != MAX_CLIENTS)
		FAIL("H7: an eviction with %u of %d slots taken", active, MAX_CLIENTS);
	if (mine != best)
		FAIL("H7: the victim is in a group of %u, the largest has %u", mine, best);
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *x = &P->clients[i];
		unsigned n = 0;
		if (!client_active(x))
			continue;
		for (size_t j = 0; j < MAX_CLIENTS; j++)
			if (client_active(&P->clients[j]) && ref_same_group(x, &P->clients[j]))
				n++;
		if (n == best && ref_tier(x, rx_now_ms) < low)
			low = ref_tier(x, rx_now_ms);
	}
	if (ref_tier(v, rx_now_ms) != low)
		FAIL("H7: the victim is of tier %d, the lowest in the largest groups is %d", ref_tier(v, rx_now_ms), low);
	if (best == 1)
		for (size_t i = 0; i < MAX_CLIENTS; i++) {
			client *x = &P->clients[i];
			if (!client_active(x) || ref_tier(x, rx_now_ms) != low)
				continue;
			if ((low <= 1 ? x->born : x->write_start) < (low <= 1 ? v->born : v->write_start))
				FAIL("H7: the victim is not the oldest of its tier among single connections");
		}
}

/* ── H1-H3: the response ── */
static const uint8_t *find_mem(const uint8_t *h, size_t n, const char *needle)
{
	size_t k = strlen(needle);
	if (k > n)
		return NULL;
	for (size_t i = 0; i + k <= n; i++)
		if (memcmp(h + i, needle, k) == 0)
			return h + i;
	return NULL;
}
/* q of one element of Accept-Encoding, read LIBERALLY: «q=0», «q=0.», «q=0.000» (any case of q, blanks around) are zero, all else is not */
static bool q_is_zero(const char *el)
{
	const char *q = el;
	while ((q = strpbrk(q, "qQ")) != NULL) {
		const char *v = q + 1;
		while (*v == ' ' || *v == '\t')
			v++;
		if (*v == '=') {
			v++;
			while (*v == ' ' || *v == '\t')
				v++;
			if (*v != '0')
				return false;
			v++;
			if (*v == '.')
				v++;
			while (*v == '0')
				v++;
			return *v == 0 || *v == ' ' || *v == '\t' || *v == ';';
		}
		q++;
	}
	return false;
}
static bool liberal_gzip(const uint8_t *req, size_t n)
{
	/* any Accept-Encoding line of the head: a coding named gzip, x-gzip or * whose q is not zero.  The product may accept LESS than this. */
	size_t i = 0;
	bool first = true;
	while (i < n) {
		size_t e = i;
		while (e < n && req[e] != '\n')
			e++;
		if (!first) {
			size_t len = e - i;
			if (len && req[i + len - 1] == '\r')
				len--;
			if (len == 0)
				break;
			if (len > 16 && strncasecmp((const char *)req + i, "accept-encoding:", 16) == 0) {
				const char *s = (const char *)req + i + 16;
				size_t m = len - 16, a = 0;
				while (a <= m) {
					size_t b = a;
					char el[512];
					size_t k;
					while (b < m && s[b] != ',')
						b++;
					k = b - a < sizeof el - 1 ? b - a : sizeof el - 1;
					memcpy(el, s + a, k);
					el[k] = 0;
					if ((strcasestr(el, "gzip") || strchr(el, '*')) && !q_is_zero(el))
						return true;
					a = b + 1;
				}
			}
		}
		first = false;
		i = e + 1;
	}
	return false;
}
/* 0 = the head is not complete in these bytes (page.c waits, or 431 at 8191); 1200 = /fingerprint */
static int ref_status(const uint8_t *req, size_t n, bool busy)
{
	size_t cs = strnlen((const char *)req, n), nline = 0, sp1 = (size_t)-1, sp2 = (size_t)-1;
	char path[1024] = {0};
	bool term = false;
	for (size_t i = 0; i < cs; i++) {
		if (i + 4 <= cs && !memcmp(req + i, "\r\n\r\n", 4)) { term = true; break; }
		if (i + 2 <= cs && !memcmp(req + i, "\n\n", 2)) { term = true; break; }
	}
	if (!term)
		return n >= 8191 ? 431 : 0;
	while (nline < n && req[nline] != '\n')
		nline++;
	for (size_t i = 0; i < nline; i++)
		if (req[i] == ' ') { sp1 = i; break; }
	if (sp1 == (size_t)-1)
		return 400;
	for (size_t i = sp1 + 1; i < nline; i++)
		if (req[i] == ' ') { sp2 = i; break; }
	if (sp2 == (size_t)-1)
		return 400;
	{ /* an obs-fold: a header line after the first that starts with SP/HT, before the empty line */
		size_t nl = nline;
		for (;;) {
			size_t st = nl + 1, left = n > st ? n - st : 0;
			if (left == 0 || req[st] == '\n' || (req[st] == '\r' && left > 1 && req[st + 1] == '\n'))
				break;
			if (req[st] == ' ' || req[st] == '\t')
				return 400;
			nl = st;
			while (nl < n && req[nl] != '\n')
				nl++;
			if (nl >= n)
				break;
		}
	}
	if (busy)
		return 503;
	{
		size_t k = sp2 - sp1 - 1;
		if (k >= sizeof path)
			k = sizeof path - 1;
		memcpy(path, req + sp1 + 1, k);
		path[strcspn(path, "?#")] = 0;
	}
	if (!strcmp(path, "/fingerprint"))
		return 1200;
	if (!strcmp(path, "/") || !strcmp(path, "/index.html"))
		return 200;
	return 404;
}
static void check_response(fconn *c)
{
	const uint8_t *o = c->out;
	size_t n = c->nout;
	const uint8_t *eoh;
	int status = 0;
	long cl = -1;
	size_t hl;
	if (!c->accepted)
		return;
	if (n == 0)
		return;
	if (n < 9 || memcmp(o, "HTTP/1.1 ", 9) != 0)
		FAIL("H1: a response that does not start with «HTTP/1.1 »");
	status = atoi((const char *)o + 9);
	if (status < 200 || status > 599)
		FAIL("H1: status %d", status);
	eoh = find_mem(o, n, "\r\n\r\n");
	if (!eoh) {
		if (c->shut)
			FAIL("H1: the connection was shut down with a head that never ended");
		return; /* aborted halfway: a prefix */
	}
	hl = (size_t)(eoh - o) + 4;
#define HAS(s) (find_mem(o, hl, s) != NULL)
	/* the page's security headers (CSP, Referrer-Policy, Permissions-Policy) are on EVERY response of this page.c, errors and JSON included */
	if (!find_mem(o, hl, PAGE_SECURITY))
		FAIL("H1: a %d response without PAGE_SECURITY", status);
	if (!HAS("Cross-Origin-Opener-Policy: same-origin\r\n") || !HAS("Cross-Origin-Embedder-Policy: require-corp\r\n") ||
	    !HAS("Cross-Origin-Resource-Policy: same-origin\r\n") || !HAS("Cache-Control: no-store\r\n") ||
	    !HAS("X-Content-Type-Options: nosniff\r\n") || !HAS("Connection: close\r\n"))
		FAIL("H1: a fixed header is missing in a %d response", status);
	{
		const uint8_t *p = find_mem(o, hl, "Content-Length: ");
		if (!p)
			FAIL("H1: no Content-Length");
		cl = atol((const char *)p + 16);
	}
	if (n > hl + (size_t)cl)
		FAIL("H1: %zu bytes after the %ld announced (a second answer, or bytes past the length)", n - hl - (size_t)cl, cl);
	if (n < hl + (size_t)cl) {
		if (c->shut)
			FAIL("H1: shut down with %zu of %ld body bytes written", n - hl, cl);
		return; /* aborted halfway */
	}
	if (!c->shut)
		FAIL("H1: whole response written and the connection not shut down in order");
	if (!c->served)
		return;
	{
		int ref = ref_status(c->in, c->rin, status == 503);
		if (status == 500) {
			if (!alloc_fail_total)
				FAIL("H2: a 500 with no allocation having failed");
		} else if (ref == 0) {
			FAIL("H2: a response (%d) to a request with no end of head and %zu bytes read", status, c->rin);
		} else if (status == 503) {
			if (ref == 400 || ref == 431)
				FAIL("H2: 503 where the request was %d", ref);
		} else if (ref == 1200) {
			if (status != 200 || !HAS("Content-Type: application/json"))
				FAIL("H2: /fingerprint answered %d", status);
		} else if (ref != status) {
			FAIL("H2: the request calls for %d and the page said %d", ref, status);
		}
	}
	if (status == 200 && HAS("Content-Type: text/html")) {
		const uint8_t *b = o + hl;
		bool gz = HAS("Content-Encoding: gzip\r\n");
		if (!find_mem(o, hl, PAGE_SECURITY) || !HAS("Vary: Accept-Encoding\r\n"))
			FAIL("H3: a 200 html without PAGE_SECURITY and Vary");
		if (gz && !liberal_gzip(c->in, c->rin))
			FAIL("H3: gzip to a request that does not accept it");
		if (gz) {
			z_stream z;
			uint8_t *plain = (malloc)(IN_MAX + (1u << 22));
			int rv;
			memset(&z, 0, sizeof z);
			if (inflateInit2(&z, 15 + 16) != Z_OK)
				FAIL("H3: inflateInit2");
			z.next_in = (Bytef *)(uintptr_t)b;
			z.avail_in = (uInt)cl;
			z.next_out = plain;
			z.avail_out = IN_MAX + (1u << 22);
			rv = inflate(&z, Z_FINISH);
			if (rv != Z_STREAM_END)
				FAIL("H3: the gzip body does not inflate to its end (zlib %d)", rv);
			if (c->gen_at_serve == gen_fp && P->cached && !c->banned_at_serve &&
			    (z.total_out != P->cached->n || memcmp(plain, P->cached->data, P->cached->n) != 0))
				FAIL("H3: the gzip copy inflates to %lu bytes that are not the plain page (%zu)", z.total_out, P->cached->n);
			if (find_mem(plain, z.total_out, "__FINGERPRINT__") || find_mem(plain, z.total_out, "__BANNED__") ||
			    find_mem(plain, z.total_out, "__WARNING__") || find_mem(plain, z.total_out, "__REMAINING_MS__"))
				FAIL("H3: a marker is left in the inflated page");
			if (!find_mem(plain, z.total_out, c->banned_at_serve ? "data-banned=\"yes\"" : "data-banned=\"no\""))
				FAIL("H3: the inflated page says the wrong data-banned (banned=%d)", c->banned_at_serve);
			inflateEnd(&z);
			(free)(plain);
		} else {
			if (c->gen_at_serve == gen_fp && P->cached && !c->banned_at_serve &&
			    ((size_t)cl != P->cached->n || memcmp(b, P->cached->data, (size_t)cl) != 0))
				FAIL("H3: the plain page is not the cached one");
			if (find_mem(b, (size_t)cl, "__FINGERPRINT__") || find_mem(b, (size_t)cl, "__BANNED__") ||
			    find_mem(b, (size_t)cl, "__WARNING__") || find_mem(b, (size_t)cl, "__REMAINING_MS__"))
				FAIL("H3: a marker is left in the page");
			if (!find_mem(b, (size_t)cl, c->banned_at_serve ? "data-banned=\"yes\"" : "data-banned=\"no\""))
				FAIL("H3: the page says the wrong data-banned (banned=%d)", c->banned_at_serve);
		}
	}
#undef HAS
}

/* the response of a connection has begun (compose() ran): what was true then, for H2/H3 and for the shadow of H5 */
static void mark_served(fconn *f)
{
	client *c = client_of(f);
	if (f->served || !c || c->phase != F_WRITE)
		return;
	f->served = true;
	f->banned_at_serve = false;
	for (int k = 0; k < NPAL; k++)
		if (((banned_mask >> k) & 1) && strcmp(PALKEY[k], c->key) == 0)
			f->banned_at_serve = true;
	f->gen_at_serve = gen_fp;
	f->tcp_ok_at_compose = !(tcp_unavailable_cfg || tcp_mode == 1 || tcp_mode == 2);
	f->acked_base = f->tcp_ok_at_compose ? (tcp_mode == 3 ? 0 : f->acked) : 0;
	f->shadow_on = true;
	f->shadow_delivered = 0;
	f->shadow_progress = rx_now_ms;
	if (c->write_start != rx_now_ms)
		FAIL("H5: write_start %llu but the clock is %llu", (unsigned long long)c->write_start, (unsigned long long)rx_now_ms);
	if (c->acked_base != f->acked_base)
		FAIL("H5: the page took acked_base %llu, the peer had acknowledged %llu", (unsigned long long)c->acked_base,
		     (unsigned long long)f->acked_base);
}
static uint64_t truth_v(const fconn *f)
{
	if (tcp_unavailable_cfg || tcp_mode == 1 || tcp_mode == 2)
		return f->taken;
	return tcp_mode == 3 ? 0 : (f->acked > f->acked_base ? f->acked - f->acked_base : 0);
}
/* what the page's sample() sees, as the shadow: called at the end of every op and before every page_expired() */
static void shadow_sample(void)
{
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *c = &P->clients[i];
		fconn *f;
		if (!client_active(c) || c->phase != F_WRITE || !(f = by_fd(c->fd)) || !f->shadow_on)
			continue;
		{
			uint64_t v = truth_v(f);
			if (v > f->shadow_delivered) {
				f->shadow_delivered = v;
				f->shadow_progress = rx_now_ms;
			}
		}
	}
}

/* ── H4: the table ── */
static void check_state(const char *where)
{
	unsigned active = 0;
	body *bodies[4] = {P->cached, P->cached_gz, P->tail, P->tail_gz};
	size_t refs[4] = {1, 1, 1, 1};
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *c = &P->clients[i];
		fconn *f;
		if (c->phase == F_DONE) {
			if (c->fd >= 0 || c->ssl || c->head || c->shared)
				FAIL("H4 %s: slot %zu is F_DONE with fd %d ssl %p head %p shared %p", where, i, c->fd, (void *)c->ssl,
				     (void *)c->head, (void *)c->shared);
			continue;
		}
		if (c->fd < 0)
			FAIL("H4 %s: slot %zu active (phase %d) with no descriptor", where, i, c->phase);
		f = by_fd(c->fd);
		if (!f || f->closed)
			FAIL("H4 %s: slot %zu holds descriptor %d that is not an open connection", where, i, c->fd);
		active++;
		if (c->phase == F_RATE && c->ssl)
			FAIL("H4 %s: a parked connection owns an SSL", where);
		if (c->phase != F_RATE && !c->ssl)
			FAIL("H4 %s: slot %zu in phase %d has no SSL", where, i, c->phase);
		if (c->nrequest >= sizeof c->request)
			FAIL("H4 %s: nrequest %zu", where, c->nrequest);
		if (c->ntail > sizeof c->tail)
			FAIL("H4 %s: ntail %zu", where, c->ntail);
		if (c->spoke && !f->replied && !f->hs_done)
			FAIL("H7 %s: «spoke» of a connection whose handshake never began its reply", where);
		if (c->phase == F_WRITE) {
			size_t ns = c->shared ? c->shared->n : 0;
			if (c->nresponse != c->nhead + ns + c->ntail)
				FAIL("H4 %s: nresponse %zu != head %zu + shared %zu + tail %zu", where, c->nresponse, c->nhead, ns, c->ntail);
			if (c->oresponse > c->nresponse)
				FAIL("H4 %s: oresponse %zu > nresponse %zu", where, c->oresponse, c->nresponse);
			if (c->shared)
				for (int k = 0; k < 4; k++)
					if (c->shared == bodies[k])
						refs[k]++;
			mark_served(f);
		}
	}
	for (int k = 0; k < 4; k++)
		if (bodies[k] && bodies[k]->refs != refs[k])
			FAIL("H4 %s: body %d has %zu references, the cache and the clients hold %zu", where, k, bodies[k]->refs, refs[k]);
	/* caps per key and per real /48 */
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		unsigned same = 0, same48 = 0;
		client *a = &P->clients[i];
		if (!client_active(a))
			continue;
		for (size_t j = 0; j < MAX_CLIENTS; j++) {
			client *b = &P->clients[j];
			if (!client_active(b))
				continue;
			if (strcmp(a->key, b->key) == 0)
				same++;
			if (a->has48 && b->has48 && memcmp(a->p48, b->p48, 6) == 0)
				same48++;
		}
		if (same > PAGE_PER_ADDRESS)
			FAIL("H4 %s: %u live connections of %s (cap %d)", where, same, a->key, PAGE_PER_ADDRESS);
		if (same48 > PAGE_PER_48)
			FAIL("H4 %s: %u live connections in one /48 (cap %d)", where, same48, PAGE_PER_48);
	}
	if (active > MAX_CLIENTS)
		FAIL("H4 %s: %u active", where, active);
	if (live_bytes > LIVE_BYTES_MAX)
		FAIL("H4 %s: %zu bytes live", where, live_bytes);
}

/* the deadline of a client by the documented rule, from the shadow: `hard` = lawful to close, `soft` = must be closed by now
 * (a second of slack on the stall: page_expired() samples at its own steps) */
static bool due_at(const client *c, const fconn *f, uint64_t now, bool soft)
{
	if (c->phase != F_WRITE)
		return now >= c->born + PAGE_REQUEST_MS;
	{
		uint64_t at = f->shadow_delivered * 1000u / PAGE_RATE_FLOOR;
		return now >= f->shadow_progress + PAGE_STALL_MS + (soft ? 1000u : 0u) ||
		       now >= c->write_start + (at > PAGE_RATE_GRACE_MS ? at : PAGE_RATE_GRACE_MS);
	}
}
static void do_expired(void)
{
	bool hard[MAX_CLIENTS] = {false}, soft[MAX_CLIENTS] = {false}, alive[MAX_CLIENTS] = {false};
	int phase0[MAX_CLIENTS] = {0};
	shadow_sample();
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *c = &P->clients[i];
		fconn *f;
		if (!client_active(c))
			continue;
		f = by_fd(c->fd);
		hard[i] = f && due_at(c, f, rx_now_ms, false);
		soft[i] = f && due_at(c, f, rx_now_ms, true);
		alive[i] = true;
		phase0[i] = c->phase;
	}
	in_expiry = true;
	page_expired(P, rx_now_ms);
	in_expiry = false;
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *c = &P->clients[i];
		bool still = client_active(c);
		if (!alive[i])
			continue;
		if (soft[i] && still)
			FAIL("H5: a client (phase %d, born %llu, write_start %llu, now %llu) alive past its deadline", c->phase,
			     (unsigned long long)c->born, (unsigned long long)c->write_start, (unsigned long long)rx_now_ms);
		/* (a parked connection started by page_expired may end for its own reasons: handshake failure, a whole response) */
		if (!hard[i] && !still && phase0[i] != F_RATE && phase0[i] != F_HANDSHAKE)
			FAIL("H5: a client in phase %d closed by page_expired before its deadline (now %llu)", phase0[i],
			     (unsigned long long)rx_now_ms);
	}
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		client *c = &P->clients[i];
		if (client_active(c) && c->phase == F_RATE && rx_now_ms >= c->rate_until)
			FAIL("H6: a parked connection past its wait (%llu >= %llu) after page_expired", (unsigned long long)rx_now_ms,
			     (unsigned long long)c->rate_until);
	}
	check_state("expired");
	{
		int w = page_wait_ms(P, rx_now_ms);
		bool any = false;
		uint64_t first = UINT64_MAX;
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&P->clients[i])) {
				uint64_t d = client_deadline(&P->clients[i]);
				any = true;
				if (d < first)
					first = d;
			}
		if (w < -1 || w > 1000)
			FAIL("H5: page_wait_ms() = %d", w);
		if (any && w < 0)
			FAIL("H5: page_wait_ms() = -1 with a client alive");
		if (any && w > 0 && first > rx_now_ms && (uint64_t)w > first - rx_now_ms)
			FAIL("H5: page_wait_ms() = %d but the next deadline is in %llu ms", w, (unsigned long long)(first - rx_now_ms));
		if (any && first <= rx_now_ms && w != 0)
			FAIL("H5: a deadline is due and page_wait_ms() = %d", w);
	}
}

/* ═══════════════ the ops ═══════════════ */
static fconn *nth_live(uint8_t k)
{
	fconn *l[MAXCONN];
	size_t n = 0;
	for (size_t i = 0; i < nconns; i++)
		if (conns[i].used && !conns[i].closed)
			l[n++] = &conns[i];
	return n ? l[k % n] : NULL;
}
static void add_in(fconn *c, const void *d, size_t n)
{
	if (c->nin + n > IN_MAX)
		n = IN_MAX - c->nin;
	if (n)
		memcpy(c->in + c->nin, d, n);
	c->nin += n;
}
static const char *CANNED(unsigned k)
{
	switch (k) {
	case 1: return "GET / HTTP/1.1\r\nHost: x\r\n\r\n";
	case 2: return "GET / HTTP/1.1\r\nHost: x\r\nAccept-Encoding: gzip, deflate, br\r\n\r\n";
	case 3: return "GET /fingerprint HTTP/1.1\r\nHost: x\r\n\r\n";
	case 4: return "GET / HTTP/1.1\r\nAccept-Encoding: gzip;q=0, *;q=0\r\n\r\n";
	case 5: return "GET / HTTP/1.1\r\nHost: x\r\n\r\nGET /fingerprint HTTP/1.1\r\nHost: x\r\n\r\n";
	case 6: return "HEAD / HTTP/1.1\r\nHost: x\r\nAccept-Encoding: gzip\r\n\r\n";
	case 7: return "POST / HTTP/1.1\r\nContent-Length: 5\r\n\r\nhello";
	case 8: return "GET /\r\nHost: x\r\n\r\n";
	case 9: return "GET / HTTP/1.1\r\nHost: x\r\n folded: y\r\n\r\n";
	case 12: return "GET /\0 HTTP/1.1\r\nHost: x\r\n\r\n";
	case 13: return "GET /\n14:00:00.000 rcp [owner] ADMITTED\r\nx HTTP/1.1\r\n\r\n";
	case 14: return "GET / HTTP/1.1\r\nAccept-Encoding: gzip;;q=0, *;q=1\r\n\r\n";
	default: return "";
	}
}
static void op_connect_conn(unsigned pal, unsigned hsmode, bool hello, bool halfclose, size_t rchunk, unsigned canned,
                            const uint8_t *extra, size_t nextra)
{
	fconn *c;
	if (nconns >= MAXCONN || npending >= MAXCONN - 1)
		return;
	c = &conns[nconns++];
	memset(c, 0, sizeof *c);
	c->used = c->queued = true;
	c->pal = (int)(pal % NPAL);
	c->sa = PAL[c->pal];
	c->salen = PALLEN[c->pal];
	c->hs_mode = hsmode;
	c->hello = hello;
	c->rchunk = rchunk;
	c->wlimit = 0;
	c->in = (calloc)(1, IN_MAX + 1);
	if (canned == 10) {
		static char longpath[3100];
		memset(longpath, 'a', sizeof longpath - 1);
		longpath[0] = '/';
		add_in(c, "GET ", 4);
		add_in(c, longpath, 3000);
		add_in(c, " HTTP/1.1\r\n\r\n", 13);
	} else if (canned == 11) {
		add_in(c, "GET / HTTP/1.1\r\nX: ", 19);
		for (int i = 0; i < 70 * 1024 / 8; i++)
			add_in(c, "aaaaaaaa", 8);
	} else if (canned == 12) {
		add_in(c, "GET /", 5);
		add_in(c, "\0", 1);
		add_in(c, " HTTP/1.1\r\nHost: x\r\n\r\n", 22);
	} else {
		const char *r = CANNED(canned);
		add_in(c, r, strlen(r));
	}
	if (nextra)
		add_in(c, extra, nextra);
	c->peer_closed = halfclose;
	pending[npending++] = c;
}
static void op_move(unsigned flags)
{
	struct pollfd fds[PAGE_MAX_DESCRIPTORS + 8];
	size_t n = page_descriptors(P, fds, PAGE_MAX_DESCRIPTORS + 8);
	if (n > PAGE_MAX_DESCRIPTORS)
		FAIL("H4: page_descriptors() returned %zu (> PAGE_MAX_DESCRIPTORS)", n);
	for (size_t i = 0; i < n; i++) {
		fds[i].revents = 0;
		if (flags & 8)
			continue;
		if (fds[i].fd == P->fd) {
			if (npending || accept_errno)
				fds[i].revents = POLLIN;
		} else {
			fconn *c = by_fd(fds[i].fd);
			if (!c)
				FAIL("H4: page_descriptors() lists descriptor %d, which is not open", fds[i].fd);
			if ((fds[i].events & POLLIN) && (c->nin > c->rin || c->peer_closed || c->peer_reset || !c->hs_done || c->hello))
				fds[i].revents |= POLLIN;
			if ((fds[i].events & POLLOUT) && (c->wlimit != 0 || c->peer_reset))
				fds[i].revents |= POLLOUT;
			if (c->peer_reset)
				fds[i].revents |= POLLHUP | POLLERR;
			if (flags & 4)
				fds[i].revents |= POLLIN;
			if (flags & 1)
				fds[i].revents |= POLLERR;
			if (flags & 2)
				fds[i].revents |= POLLHUP;
		}
	}
	in_move = true;
	evictions_in_move = 0;
	page_move(P, fds, n);
	if (flags & 16)
		page_move(P, fds, n); /* the same events again: descriptors may have changed owner */
	in_move = false;
	check_state("move");
}
static void op_time(uint32_t ms)
{
	uint64_t end;
	unsigned steps = 0;
	if (ms > 400000u)
		ms = 400000u; /* (at most 400 steps of ≤ 1 s: the main loop wakes at least every second, and H5 relies on it) */
	end = rx_now_ms + ms;
	while (rx_now_ms < end && steps++ < 1100) {
		uint64_t step = end - rx_now_ms;
		int w = page_wait_ms(P, rx_now_ms);
		if (step > 1000)
			step = 1000;
		if (w >= 0 && (uint64_t)w < step && w > 0)
			step = (uint64_t)w;
		rx_now_ms += step;
		do_expired();
	}
	if (rx_now_ms < end)
		rx_now_ms = end, do_expired();
}
static void fp_set(void)
{
	snprintf(CERT.fingerprint, sizeof CERT.fingerprint, "FINGERPRINTBASE64====%llu", (unsigned long long)gen_fp);
	snprintf(CERT.fingerprint_hex, sizeof CERT.fingerprint_hex, "ab%llu", (unsigned long long)gen_fp);
}
static void fp_rotate(void)
{
	gen_fp++;
	fp_set();
	CERT.rotations++;
}

static page *make_page(bool big)
{
	page *p = fz_calloc(1, sizeof *p);
	size_t off = 0;
	static const char HEAD[] =
	    "<!doctype html><html><head><title>t</title></head><body data-fp=\"__FINGERPRINT__\">"
	    "<div id=\"s\" data-banned=\"__BANNED__\" data-remaining-ms=\"__REMAINING_MS__\">__WARNING__</div>";
	size_t filler = big ? 200 * 1024 : 2000;
	HTML = (malloc)(sizeof HEAD + filler + 64);
	memcpy(HTML, HEAD, sizeof HEAD - 1);
	off = sizeof HEAD - 1;
	for (size_t i = 0; i < filler; i++)
		HTML[off++] = (char)('a' + (i * 7 + i / 13) % 26 + ((i % 61) == 0 ? -32 : 0));
	memcpy(HTML + off, "</body></html>", 14);
	off += 14;
	HTML[off] = 0;
	NHTML = off;
	p->fd = 99;
	p->ctx = NULL;
	p->cert = &CERT;
	{
		char *h = fz_malloc(NHTML + 1);
		memcpy(h, HTML, NHTML + 1);
		p->html = h;
	}
	p->nhtml = NHTML;
	for (size_t i = 0; i < MAX_CLIENTS; i++) {
		p->clients[i].fd = -1;
		p->clients[i].phase = F_DONE;
	}
	return p;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	rx_ops o;
	uint8_t op;
	const uint8_t *a;
	size_t n;
	if (size < 1)
		return 0;
	memset(conns, 0, sizeof conns);
	nconns = npending = 0;
	memset(fd_owner, 0, sizeof fd_owner);
	tcp_mode = accept_errno = fail_alloc_in = fail_ssl_new = fail_rand = fail_getname = 0;
	tcp_unavailable_cfg = (data[0] & 2) != 0;
	banned_mask = 0;
	gen_fp = 0;
	live_bytes = 0;
	in_expiry = in_move = false;
	ssl_live = 0;
	rx_now_ms = 1000000;
	t0_ms = rx_now_ms;
	rx_event_line = event_line;
	memset(&CERT, 0, sizeof CERT);
	gen_fp = 0;
	fp_set();
	pal_init();
	for (int i = 0; i < NPAL; i++)
		pal_key(i, PALKEY[i]);
	alloc_fail_total = 0;
	memset(RT, 0, sizeof RT);
	memset(RT48, 0, sizeof RT48);
	P = make_page((data[0] & 1) != 0);

	o.d = data + 1;
	o.n = size - 1;
	o.i = 0;
	while (rx_next(&o, &op, &a, &n)) {
		uint8_t z[16] = {0};
		memcpy(z, a, n < sizeof z ? n : sizeof z);
		switch (op % 10) {
		case 0:
			op_connect_conn(z[0], z[1] & 7, (z[1] >> 3) & 1, (z[1] >> 4) & 1, (data[0] & 4) ? 1 : z[2], z[3] % 15,
			                n > 4 ? a + 4 : NULL, n > 4 ? n - 4 : 0);
			break;
		case 1: {
			fconn *c = nth_live(z[0]);
			if (!c)
				break;
			if (z[1] & 1)
				c->hello = true;
			if (z[1] & 2)
				c->peer_closed = true;
			if (n > 2)
				add_in(c, a + 2, n - 2);
			break;
		}
		case 2:
			op_move(z[0]);
			break;
		case 3:
			op_time((uint32_t)((z[0] << 8) | z[1]) * ((z[2] & 1) ? 1000u : 1u));
			break;
		case 4: {
			fconn *c = nth_live(z[0]);
			uint32_t k = ((uint32_t)z[1] << 24) | ((uint32_t)z[2] << 16) | ((uint32_t)z[3] << 8) | z[4];
			if (!c)
				break;
			{
				uint64_t total = HS_TAIL + c->nout;
				c->acked = k == 0xFFFFFFFFu ? total : (c->acked + k > total ? total : c->acked + k);
			}
			break;
		}
		case 5: {
			fconn *c = nth_live(z[0]);
			uint32_t k = ((uint32_t)z[1] << 24) | ((uint32_t)z[2] << 16) | ((uint32_t)z[3] << 8) | z[4];
			if (!c)
				break;
			c->piece = z[5] ? (size_t)z[5] * 64 : 0;
			if (k == 0xFFFFFFFFu)
				c->wlimit = UNLIM;
			else if (c->wlimit != UNLIM)
				c->wlimit += k;
			break;
		}
		case 6:
			fail_alloc_in = z[0];
			accept_errno = z[1] == 0 ? 0 : z[1] == 1 ? EAGAIN : z[1] == 2 ? EMFILE : z[1] == 3 ? EINTR : ECONNABORTED;
			tcp_mode = z[2] & 3;
			fail_ssl_new = z[3] & 1;
			banned_mask = (uint16_t)((z[4] << 8) | z[5]);
			fail_rand = z[6] & 1;
			fail_getname = z[7] & 1;
			if (z[8] & 1)
				fp_rotate();
			break;
		case 7: {
			fconn *c = nth_live(z[0]);
			if (c)
				c->peer_reset = true;
			break;
		}
		case 8: {
			unsigned cnt = z[0] % 64 + 1;
			for (unsigned i = 0; i < cnt; i++) {
				unsigned pal = (z[2] & 1) ? z[1] : z[1] + i;
				uint8_t one = 'x';
				op_connect_conn(pal, 0, (z[2] >> 1) & 1, (z[2] >> 3) & 1, 0, (z[2] & 2) ? 1 : 0, (z[2] & 4) ? &one : NULL,
				                (z[2] & 4) ? 1 : 0);
			}
			op_move(0);
			break;
		}
		case 9: {
			unsigned moves = z[1] % 4 + 1;
			for (size_t i = 0; i < nconns; i++)
				if (conns[i].used && !conns[i].closed) {
					conns[i].wlimit = UNLIM;
					conns[i].acked = HS_TAIL + conns[i].nout;
				}
			for (unsigned i = 0; i < moves; i++)
				op_move(0);
			break;
		}
		}
		for (size_t i = 0; i < nconns; i++)
			if (conns[i].used && !conns[i].closed)
				mark_served(&conns[i]);
		shadow_sample();
		check_state("op");
	}
	/* the end: every slot has a deadline.  Open the windows, let time run in steps, require an EMPTY table. */
	{
		for (size_t i = 0; i < nconns; i++)
			if (conns[i].used && !conns[i].closed) {
				conns[i].wlimit = 0;
			}
		op_time(200000);
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&P->clients[i]))
				FAIL("H5: a client (phase %d) is still alive 200 s after the last event: no deadline closed it",
				     P->clients[i].phase);
	}
	for (size_t i = 0; i < nconns; i++)
		if (conns[i].used) {
			(free)(conns[i].in);
			(free)(conns[i].out);
		}
	(free)(HTML);
	HTML = NULL;
	P->fd = -1;
	page_close(P);
	P = NULL;
	if (live_bytes)
		FAIL("%zu bytes still allocated after page_close()", live_bytes);
	if (ssl_live)
		FAIL("%d SSL objects leaked", ssl_live);
	return 0;
}
