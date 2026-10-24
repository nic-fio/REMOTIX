/* 02-page-deadline-test.c — the TCP page listener cannot be locked out by
 * connections that send nothing (15 Oct 2026, pre-login denial of service:
 * 32 idle TCP connections took all 32 slots of `page.c` for ever).
 *
 * In the build container, from src/ (the product's objects, then the test
 * linked against all of them except main.o and page.o):
 *
 *   make TWIN=none
 *   gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags gio-2.0 \
 *       libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 \
 *       xkbcommon wayland-client gbm) -o /tmp/pdt \
 *       ../benches/02-page-deadline-test.c \
 *       $(ls *.o | grep -v -e '^main.o$' -e '^page.o$') \
 *       -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
 *       $(pkg-config --libs gio-2.0 libpipewire-0.3 libva libva-drm \
 *       libei-1.0 xkbcommon wayland-client gbm opus vulkan) -ldl && /tmp/pdt
 *
 * ⚠ `page.c` is INCLUDED (the seam): the test drives the listener exactly as
 *   main.c does — `page_descriptors`, `poll`, `page_move`, `page_expired` —
 *   and reads the client table directly.  The clock is moved by passing a
 *   later `now` to `page_expired()`, not by waiting.  The sources are
 *   127.0.0.1-9 (all of 127/8 is local).
 *
 *   1. four idle connections from one address are taken, the fifth is refused;
 *   2. 128 idle connections from 32 addresses fill the table;
 *   3. a newcomer from a fresh address evicts ONE idle client (fair share:
 *      from a group holding 4), and the victim sees a RESET;
 *   4. churn (third review): 200 bare connects from the crowded addresses
 *      cannot evict the lone newcomer of check 3 — they only push out each
 *      other, from the most crowded groups — while a second fresh address
 *      still gets in;
 *   5. page_wait_ms() says the next deadline is within a second;
 *   6. page_expired(now + 10 s) closes every idle connection, with a RESET;
 *  6b. every place holds ONE slot (128 addresses): a new address is still
 *      admitted, and the oldest makes room — refusing would be a cheap lockout;
 *   7. a real HTTPS GET / then gets the page (200, the markers replaced);
 *   8. a client that sent its request but stopped reading the response is
 *      NOT closed at 10 s, and IS closed 60 s after the last byte it
 *      acknowledged — progress is what it acknowledged, not what the
 *      kernel's send buffer swallowed;
 *   9. the progress deadline: a phone that took 300 KB in 60 s (5 KB/s) is
 *      kept, one that took 100 KB (1.7 KB/s) is closed;
 *  10. 128 readers from 32 addresses hold every slot in F_WRITE: a newcomer
 *      is admitted even while they are younger than 5 s (a fresh writer of a
 *      crowded address goes: the last tier); once they are 6 s in one
 *      is evicted WHATEVER its speed (they are made fast on purpose) and a
 *      real GET gets the page;
 *  11. the IPv6 /48 is taken only from real IPv6 peers, and it is the
 *      fair-share group of an IPv6 client (two /64s of one /48 are one group);
 *  12. the request-line budget: 5 per address per 10 s, the rest counted.
 *  14. (fourth review) 127 fresh writers from 32 addresses + a phone 6 s into
 *      its download + newcomers from fresh addresses: a fresh writer of a
 *      crowded address is evicted, never the phone; and all writers send ONE
 *      shared copy of the page;
 *  13. … and 17 addresses taking turns do not each get a fresh budget when the
 *      16-entry table is full: none above 5 in its window, and the 17th waits
 *      for a free entry (fuzz page, 15 Oct 2026).
 *
 *  15. a banned visitor (a real ban, loaded with rcp_ban_load()) gets the
 *      «attempts exhausted» page with its remaining time, built for its own
 *      request and freed with it; visitors from other addresses keep getting
 *      the shared page, which is not touched by the banned one;
 *  16. allocation failures injected into page.c (the malloc seam below): every
 *      failing allocation of build_page()/body_new() gives the 500 «no mem.»
 *      reply, leaks nothing and leaves the shared page whole (never a
 *      half-built or swapped one); a failing 500 head too leaves the client
 *      without a response and still leaks nothing.
 *  17. gzip (§11.44, the user's decision of 15 Oct 2026): the shared page has
 *      ONE gzip copy, built with it; `Accept-Encoding` read with its q-values
 *      (`gzip;q=0` = plain, `*`, `x-gzip`, no header = plain); a gzip request
 *      gets the shared copy with Content-Encoding, Vary and the compressed
 *      Content-Length, a real one over TLS inflates to the exact page; a banned
 *      page goes plain; every failing allocation of the copy still serves the
 *      plain page, retries at the next gzip request, and leaks nothing.
 *      After the review of 6d8249c4: an empty parameter is skipped (`gzip;q=0;, *`
 *      = plain), a parameter that does not read voids its element, a folded
 *      header line gets 400, the copy is shrunk to its bytes (a failed shrink
 *      keeps it whole).
 *
 * Exit status: 0 green, 1 red, 3 not all checks ran. */
#define _GNU_SOURCE
/* ⚠ THE MALLOC SEAM: every header page.c uses is included FIRST, so the two
 *   macros below rewrite only page.c's own calls.  Each allocation page.c
 *   makes is tracked (to see leaks), and the `fail_at`-th one from the
 *   moment it is armed returns NULL (with `fail_rest`, every one after it
 *   too). */
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
#include <zlib.h>

static void *live_allocs[4096];
static size_t nlive, page_mallocs;
static bool live_overflow;
static long fail_at; /* 0 = off */
static bool fail_rest;

static void *t_malloc(size_t n)
{
	void *r;
	page_mallocs++;
	if (fail_at > 0 && --fail_at == 0) {
		if (fail_rest)
			fail_at = 1;
		return NULL;
	}
	r = malloc(n);
	if (r) {
		if (nlive < sizeof live_allocs / sizeof live_allocs[0])
			live_allocs[nlive++] = r;
		else
			live_overflow = true;
	}
	return r;
}

static void t_free(void *q)
{
	for (size_t i = 0; q && i < nlive; i++)
		if (live_allocs[i] == q) {
			live_allocs[i] = live_allocs[--nlive];
			break;
		}
	free(q);
}

/* `realloc` (the gzip copy's shrink): tracked, NOT counted among the
 * allocations `fail_at` walks; `fail_realloc` makes it fail. */
static bool fail_realloc;

static void *t_realloc(void *q, size_t n)
{
	void *r;
	if (fail_realloc)
		return NULL;
	r = realloc(q, n);
	if (r)
		for (size_t i = 0; i < nlive; i++)
			if (live_allocs[i] == q) {
				live_allocs[i] = r;
				break;
			}
	return r;
}

#define malloc(n) t_malloc(n)
#define free(q) t_free(q)
#define realloc(q, n) t_realloc(q, n)
#include "page.c"
#undef malloc
#undef free
#undef realloc
#include <malloc.h>

#include <arpa/inet.h>
#include <openssl/evp.h>
#include <openssl/x509.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 115

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

static int port_of(page *p)
{
	struct sockaddr_in a;
	socklen_t l = sizeof a;
	getsockname(p->fd, (struct sockaddr *)&a, &l);
	return ntohs(a.sin_port);
}

static int active(page *p)
{
	int n = 0;
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		n += client_active(&p->clients[i]);
	return n;
}

/* One or more passes of the main loop, without the expiry. */
static void pump(page *p, int passes)
{
	for (int k = 0; k < passes; k++) {
		struct pollfd f[MAX_CLIENTS + 1];
		size_t n = page_descriptors(p, f, MAX_CLIENTS + 1);
		if (poll(f, n, 20) > 0)
			page_move(p, f, n);
	}
}

static int connect_from(int port, const char *src, int rcvbuf)
{
	struct sockaddr_in a = {.sin_family = AF_INET};
	int fd = socket(AF_INET, SOCK_STREAM, 0);
	if (rcvbuf)
		setsockopt(fd, SOL_SOCKET, SO_RCVBUF, &rcvbuf, sizeof rcvbuf);
	inet_pton(AF_INET, src, &a.sin_addr);
	a.sin_port = 0;
	if (bind(fd, (struct sockaddr *)&a, sizeof a) != 0) {
		perror("bind");
		exit(3);
	}
	inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
	a.sin_port = htons((uint16_t)port);
	if (connect(fd, (struct sockaddr *)&a, sizeof a) != 0) {
		perror("connect");
		exit(3);
	}
	return fd;
}

/* -1 = still open, 1 = closed by the server with a FIN, 2 = with a RESET. */
static int server_end(int fd)
{
	char b[16];
	struct pollfd f = {.fd = fd, .events = POLLIN};
	if (poll(&f, 1, 50) <= 0)
		return -1;
	ssize_t r = recv(fd, b, sizeof b, MSG_DONTWAIT);
	if (r == 0)
		return 1;
	if (r < 0 && errno == ECONNRESET)
		return 2;
	return -1;
}

/* How many active clients have this key. */
static int client_of(page *p, const char *key)
{
	int n = 0;
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		n += client_active(&p->clients[i]) && strcmp(p->clients[i].key, key) == 0;
	return n;
}

/* 1 = the server closed this socket (EOF or reset), 0 = still open. */
static int closed_by_server(int fd)
{
	char b[16];
	struct pollfd f = {.fd = fd, .events = POLLIN};
	if (poll(&f, 1, 200) <= 0)
		return 0;
	ssize_t r = recv(fd, b, sizeof b, MSG_DONTWAIT);
	return r == 0 || (r < 0 && errno == ECONNRESET);
}

static SSL_CTX *server_ctx(void)
{
	SSL_CTX *ctx = SSL_CTX_new(TLS_server_method());
	EVP_PKEY *k = EVP_EC_gen("P-256");
	X509 *x = X509_new();
	X509_set_version(x, 2);
	ASN1_INTEGER_set(X509_get_serialNumber(x), 1);
	X509_gmtime_adj(X509_getm_notBefore(x), 0);
	X509_gmtime_adj(X509_getm_notAfter(x), 3600);
	X509_set_pubkey(x, k);
	X509_NAME_add_entry_by_txt(X509_get_subject_name(x), "CN", MBSTRING_ASC,
	                           (const unsigned char *)"test", -1, -1, 0);
	X509_set_issuer_name(x, X509_get_subject_name(x));
	X509_sign(x, k, EVP_sha256());
	if (!ctx || !k || SSL_CTX_use_certificate(ctx, x) != 1 ||
	    SSL_CTX_use_PrivateKey(ctx, k) != 1) {
		fprintf(stderr, "cannot make the test certificate\n");
		exit(3);
	}
	return ctx;
}

/* Pumps until `want` clients are in F_WRITE (10 s at most); returns the last
 * one, or NULL. */
static client *writer_wait(page *p, int want)
{
	uint64_t t0 = log_now_ms();
	while (log_now_ms() - t0 < 10000) {
		client *last = NULL;
		int n = 0;
		pump(p, 1);
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]) && p->clients[i].phase == F_WRITE) {
				n++;
				last = &p->clients[i];
			}
		if (n >= want) {
			pump(p, 10);
			return last;
		}
	}
	return NULL;
}

/* In a forked child: TLS, `GET /`, then either read the whole response
 * (`read_all`) and exit 0 if it is a 200 with the page's markers replaced,
 * or sleep without reading (the slow reader).  `banned`: the page must be
 * the ban notice of section 15 (1 h 30 min left), otherwise the free one. */
static pid_t client_get_as(int port, const char *src, bool read_all, bool banned)
{
	pid_t pid = fork();
	if (pid != 0)
		return pid;
	int fd = connect_from(port, src, read_all ? 0 : 4096);
	SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());
	SSL *s = SSL_new(ctx);
	SSL_set_fd(s, fd);
	if (SSL_connect(s) != 1)
		_exit(10);
	const char *req = "GET / HTTP/1.1\r\nHost: test\r\n\r\n";
	if (SSL_write(s, req, (int)strlen(req)) <= 0)
		_exit(11);
	if (!read_all)
		for (;;)
			pause();
	size_t cap = 64 << 20, n = 0;
	char *b = malloc(cap + 1);
	for (;;) {
		int r = SSL_read(s, b + n, (int)(cap - n > 1 << 20 ? 1 << 20 : cap - n));
		if (r <= 0)
			break;
		n += (size_t)r;
	}
	b[n] = 0;
	bool common = strncmp(b, "HTTP/1.1 200 ", 13) == 0 && strstr(b, "FPTEST") &&
	              !strstr(b, "__FINGERPRINT__") && !strstr(b, "__WARNING__") &&
	              !strstr(b, "__BANNED__") && !strstr(b, "__REMAINING_MS__");
	if (!banned)
		_exit(common && strstr(b, "data-banned=\"no\"") &&
		      !strstr(b, "attempts exhausted") && strstr(b, "data-remaining-ms=\"0\"")
		      ? 0 : 12);
	{
		const char *r = strstr(b, "data-remaining-ms=\"");
		unsigned long long ms = r ? strtoull(r + 19, NULL, 10) : 0;
		_exit(common && strstr(b, "data-banned=\"yes\"") &&
		      strstr(b, "<b>attempts exhausted</b>") &&
		      strstr(b, "<b id=\"hours\">1</b> hours and <b id=\"minutes\">30</b> minutes") &&
		      ms > 5340000 && ms <= 5400000
		      ? 0 : 13);
	}
}

static pid_t client_get(int port, const char *src, bool read_all)
{
	return client_get_as(port, src, read_all, false);
}

/* FNV-1a of a body: «the shared page did not change» checked byte by byte. */
static uint64_t body_hash(const body *x)
{
	uint64_t h = 1469598103934665603ull;
	for (size_t i = 0; i < x->n; i++)
		h = (h ^ (unsigned char)x->data[i]) * 1099511628211ull;
	return h;
}

static bool body_has(const body *x, const char *s)
{
	return memmem(x->data, x->n, s, strlen(s)) != NULL;
}

/* `serve()` driven directly, without a socket: the request `GET /` from
 * `provenance` (fd -1, no SSL: compose only builds the response). */
static void fake_get(page *p, client *c, const char *provenance)
{
	memset(c, 0, sizeof *c);
	c->fd = -1;
	c->phase = F_READ;
	snprintf(c->provenance, sizeof c->provenance, "%s", provenance);
	c->nrequest = (size_t)snprintf(c->request, sizeof c->request,
	                               "GET / HTTP/1.1\r\nHost: t\r\n\r\n");
	serve(p, c);
}

/* `fake_get()` with an `Accept-Encoding` header (`ae`), or none (NULL). */
static void fake_get_ae(page *p, client *c, const char *provenance, const char *ae)
{
	memset(c, 0, sizeof *c);
	c->fd = -1;
	c->phase = F_READ;
	snprintf(c->provenance, sizeof c->provenance, "%s", provenance);
	c->nrequest = (size_t)snprintf(c->request, sizeof c->request,
	                               "GET / HTTP/1.1\r\nHost: t\r\n%s%s%s\r\n",
	                               ae ? "Accept-Encoding: " : "", ae ? ae : "",
	                               ae ? "\r\n" : "");
	serve(p, c);
}

/* A whole gzip member (RFC 1952) inflated: a new buffer (`*n` bytes), or NULL
 * when it is not valid gzip or has bytes after its end. */
static unsigned char *gunzip(const void *in, size_t nin, size_t *n)
{
	z_stream z;
	size_t cap = 1 << 20;
	unsigned char *out = malloc(cap);
	int rv;

	memset(&z, 0, sizeof z);
	if (!out || inflateInit2(&z, 16 + 15) != Z_OK) {
		free(out);
		return NULL;
	}
	z.next_in = (Bytef *)(uintptr_t)in;
	z.avail_in = (uInt)nin;
	do {
		if (z.total_out == cap) {
			unsigned char *b = realloc(out, cap * 2);
			if (!b)
				break;
			out = b;
			cap *= 2;
		}
		z.next_out = out + z.total_out;
		z.avail_out = (uInt)(cap - z.total_out);
		rv = inflate(&z, Z_NO_FLUSH);
	} while (rv == Z_OK);
	*n = z.total_out;
	inflateEnd(&z);
	if (rv != Z_STREAM_END || z.avail_in != 0) {
		free(out);
		return NULL;
	}
	return out;
}

/* 1 = `x` inflates to exactly the bytes of `plain`. */
static int gunzips_to(const void *x, size_t nx, const body *plain)
{
	size_t n = 0;
	unsigned char *u = gunzip(x, nx, &n);
	int ok = u && plain && n == plain->n && memcmp(u, plain->data, n) == 0;
	free(u);
	return ok;
}

/* The `Content-Length` of a composed head, or -1. */
static long long head_length(const client *c)
{
	const char *h = c->head ? memmem(c->head, c->nhead, "\r\nContent-Length: ", 18) : NULL;
	return h ? strtoll(h + 18, NULL, 10) : -1;
}

static bool head_has(const client *c, const char *s)
{
	const char *e = c->head ? memmem(c->head, c->nhead, "\r\n\r\n", 4) : NULL;
	/* up to the last header's own CRLF */
	return e && memmem(c->head, (size_t)(e - c->head) + 2, s, strlen(s)) != NULL;
}

/* In a forked child: TLS, `GET /` with `Accept-Encoding: <ae>`, the whole
 * response read; exit 0 when it is a 200 whose body is exactly
 * `Content-Length` bytes and is `want` (gzip-compressed when `gz`). */
static pid_t client_get_ae(int port, const char *src, const char *ae, bool gz,
                           const body *want)
{
	pid_t pid = fork();
	if (pid != 0)
		return pid;
	int fd = connect_from(port, src, 0);
	SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());
	SSL *s = SSL_new(ctx);
	char req[256];
	SSL_set_fd(s, fd);
	if (SSL_connect(s) != 1)
		_exit(10);
	snprintf(req, sizeof req, "GET / HTTP/1.1\r\nHost: test\r\nAccept-Encoding: %s\r\n\r\n", ae);
	if (SSL_write(s, req, (int)strlen(req)) <= 0)
		_exit(11);
	size_t cap = 16 << 20, n = 0;
	char *b = malloc(cap + 1);
	for (;;) {
		int r = SSL_read(s, b + n, (int)(cap - n > 1 << 20 ? 1 << 20 : cap - n));
		if (r <= 0)
			break;
		n += (size_t)r;
	}
	b[n] = 0;
	char *e = strstr(b, "\r\n\r\n");
	if (!e || strncmp(b, "HTTP/1.1 200 ", 13) != 0)
		_exit(12);
	e[2] = 0; /* the head, with its last header's CRLF */
	size_t hl = (size_t)(e - b) + 4;
	const char *cl = strstr(b, "\r\nContent-Length: ");
	if (!cl || strtoull(cl + 18, NULL, 10) != n - hl)
		_exit(13);
	if (!strstr(b, "\r\nVary: Accept-Encoding\r\n"))
		_exit(14);
	if (gz != (strstr(b, "\r\nContent-Encoding: gzip\r\n") != NULL))
		_exit(15);
	if (gz ? !gunzips_to(b + hl, n - hl, want)
	       : !(n - hl == want->n && memcmp(b + hl, want->data, want->n) == 0))
		_exit(16);
	_exit(0);
}

/* What the page keeps for banned visitors for its whole life (built at the
 * first one): the shared tail, and its raw-deflate copy. */
#define BANNED_LIVE(p) ((size_t)((p)->tail != NULL) + (size_t)((p)->tail_gz != NULL))

/* The client's own bytes (headers + its own prefix) contain `s`. */
static bool own_has(const client *c, const char *s)
{
	return c->head && memmem(c->head, c->nhead, s, strlen(s)) != NULL;
}

/* The accept buckets forgotten: sections 7 and 10 reuse addresses that
 * sections 1-6 drove far over PAGE_ACCEPT_RATE within the same second, and
 * they test other rules; the rate itself is section 18. */
static void rate_reset(page *p)
{
	memset(p->rate, 0, sizeof p->rate);
	memset(p->rate48, 0, sizeof p->rate48);
	memset(&p->rate_over, 0, sizeof p->rate_over);
	memset(&p->rate48_over, 0, sizeof p->rate48_over);
}

/* The fingerprint the shared page is NOT built for: setting it forces a rebuild. */
#define OTHER_FP(p) (strcmp((p)->cached_fp, "FPROT") == 0 ? "FPTEST" : "FPROT")

/* 1 = a 500 «no mem.» with no shared body. */
static int is_500(const client *c)
{
	return c->phase == F_WRITE && c->head && c->shared == NULL &&
	       strncmp(c->head, "HTTP/1.1 500 ", 13) == 0 && c->nhead >= 8 &&
	       memcmp(c->head + c->nhead - 8, "no mem.\n", 8) == 0;
}

int main(void)
{
	char html_path[] = "/tmp/pdt-page-XXXXXX";
	int hfd = mkstemp(html_path);
	FILE *h = fdopen(hfd, "w");
	certificates cert;
	/* ~4 MB: beyond what loopback buffers hold, so a slow reader really
	 * stays in F_WRITE.  ⚠ Not 16 MB: 128 writers each hold a copy of the
	 * response, and 128 × 16 MB was killed by the 2 GB limit. */
	fprintf(h, "<html><body data-banned=\"__BANNED__\" data-remaining-ms=\""
	           "__REMAINING_MS__\">__FINGERPRINT__ "
	           "__WARNING__<!--");
	for (int i = 0; i < 4 * 1024; i++)
		fprintf(h, "%01023d\n", 0);
	fprintf(h, "--></body></html>\n");
	fclose(h);

	memset(&cert, 0, sizeof cert);
	snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPTEST");
	snprintf(cert.fingerprint_hex, sizeof cert.fingerprint_hex, "00");
	signal(SIGPIPE, SIG_IGN);

	page *p = page_open("127.0.0.1", "0", server_ctx(), html_path, &cert);
	if (!p) {
		fprintf(stderr, "page_open failed\n");
		return 3;
	}
	int port = port_of(p);
	/* ⚠ A small send buffer, inherited by every accepted socket: the kernel
	 *   then holds ~128 KB per slow reader instead of ~2.6 MB, which 128
	 *   readers would multiply. */
	{
		int sb = 65536;
		setsockopt(p->fd, SOL_SOCKET, SO_SNDBUF, &sb, sizeof sb);
	}
	static int fds[256];
	int nf = 0;
	char src[32];

	printf("1. four idle from one address are taken, the fifth is refused\n");
	for (int i = 0; i < 5; i++) {
		fds[nf++] = connect_from(port, "127.0.0.1", 0);
		pump(p, 2);
	}
	require(active(p) == 4, "4 clients active after 5 connections from 127.0.0.1");
	require(closed_by_server(fds[4]), "the 5th socket was closed by the server");
	/* ⚠ The first refusal writes the summary line at once and zeroes the
	 *   counters: «written» is what is checked. */
	require(p->refused_ever && p->refused_address == 0,
	        "the refusal was reported in the summary line");
	close(fds[4]);
	nf--;

	printf("2. 128 idle from 32 addresses fill the table\n");
	for (int a = 2; a <= 32; a++)
		for (int i = 0; i < 4; i++) {
			snprintf(src, sizeof src, "127.0.0.%d", a);
			fds[nf++] = connect_from(port, src, 0);
			pump(p, 1);
		}
	pump(p, 3);
	require(active(p) == MAX_CLIENTS, "128 clients active");

	printf("3. a newcomer from a fresh address evicts one, by fair share\n");
	{
		int lone = connect_from(port, "127.0.0.100", 0), gone = 0, reset = 0;
		pump(p, 3);
		for (int i = 0; i < nf; i++)
			switch (server_end(fds[i])) {
			case 2: reset++; /* fall through */
			case 1: gone++; break;
			}
		require(active(p) == MAX_CLIENTS && p->evicted == 1,
		        "still 128 active, one eviction counted");
		require(gone == 1 && reset == 1, "exactly one idle client closed, with a RESET");
		require(client_of(p, "[127.0.0.100]") == 1, "the newcomer got in");

		printf("4. churn cannot evict the lone client\n");
		for (int k = 0; k < 200; k++) {
			snprintf(src, sizeof src, "127.0.0.%d", 1 + k % 8);
			int f = connect_from(port, src, 0);
			pump(p, 1);
			close(f);
		}
		pump(p, 3);
		require(client_of(p, "[127.0.0.100]") == 1,
		        "after 200 connects from 8 crowded addresses the lone client is still there");
		/* ⚠ Tolerant on purpose: a churner that got in and then closed
		 *   leaves its slot free until the next accept, so the table holds
		 *   127 or 128 depending on the random victims — the lone client is
		 *   what is checked. */
		require(active(p) >= MAX_CLIENTS - 1,
		        "the table stays (almost) full: the churners pushed out each other or were refused");
		int second = connect_from(port, "127.0.0.101", 0);
		pump(p, 3);
		require(client_of(p, "[127.0.0.101]") == 1 && active(p) == MAX_CLIENTS,
		        "a second fresh address still gets in");
		fds[nf++] = lone;
		fds[nf++] = second;
	}

	printf("5. the loop is woken for the deadline\n");
	{
		int w = page_wait_ms(p, log_now_ms());
		require(w >= 0 && w <= 1000, "page_wait_ms() within [0, 1000]");
	}

	printf("6. 10 s later every idle connection is closed, with a RESET\n");
	int n6;
	{
		uint64_t first = UINT64_MAX;
		/* ⚠ Churners of section 4 parked for the accept rate (their peers
		 *   already gone) would be started by page_expired() and close on
		 *   their EOF: not what this section measures — dropped first. */
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]) && p->clients[i].phase == F_RATE)
				client_close(&p->clients[i]);
		n6 = active(p);
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]) && p->clients[i].born < first)
				first = p->clients[i].born;
		page_expired(p, first + PAGE_REQUEST_MS - 1);
	}
	require(active(p) == n6 && n6 >= MAX_CLIENTS - 8, "nobody closed 1 ms before the first deadline");
	page_expired(p, log_now_ms() + PAGE_REQUEST_MS + 1);
	require(active(p) == 0, "all closed after the deadline");
	{
		int open_before = 0, reset = 0;
		for (int i = 0; i < nf; i++) {
			int e = server_end(fds[i]);
			open_before += e != -1;
			reset += e == 2;
		}
		require(reset >= MAX_CLIENTS, "every expired socket saw a RESET");
	}
	for (int i = 0; i < nf; i++)
		close(fds[i]);

	printf("6b. every place at ONE slot: a new real client is still admitted\n");
	{
		static int one[MAX_CLIENTS];
		int n1 = 0, newc;
		unsigned full_before = p->refused_full;
		for (int i = 0; i < MAX_CLIENTS; i++) {
			snprintf(src, sizeof src, "127.0.1.%d", i + 1);
			one[n1++] = connect_from(port, src, 0);
			pump(p, 1);
		}
		pump(p, 3);
		require(active(p) == MAX_CLIENTS, "128 idle, one each from 128 addresses");
		newc = connect_from(port, "127.0.2.1", 0);
		pump(p, 3);
		require(client_of(p, "[127.0.2.1]") == 1 && p->refused_full == full_before,
		        "the newcomer is admitted, not refused");
		require(server_end(one[0]) == 2 && client_of(p, "[127.0.1.1]") == 0,
		        "the OLDEST one-slot client made room (FIFO), with a RESET");
		page_expired(p, log_now_ms() + PAGE_REQUEST_MS + 1);
		for (int i = 0; i < n1; i++)
			close(one[i]);
		close(newc);
	}

	printf("7. a real HTTPS GET gets the page\n");
	rate_reset(p);
	{
		pid_t c = client_get(port, "127.0.0.1", true);
		int st = -1;
		uint64_t t0 = log_now_ms();
		while (waitpid(c, &st, WNOHANG) == 0 && log_now_ms() - t0 < 20000) {
			pump(p, 1);
			page_expired(p, log_now_ms());
		}
		require(WIFEXITED(st) && WEXITSTATUS(st) == 0,
		        "200 with the page, markers replaced");
		pump(p, 2);
		require(active(p) == 0, "the slot is free again after the response");
	}

	printf("8. a slow reader is held to the progress deadline, not the 10 s one\n");
	{
		pid_t c = client_get(port, "127.0.0.1", false);
		client *w = writer_wait(p, 1);
		require(w && active(p) == 1, "the request was read, the response is stuck");
		if (w) {
			page_expired(p, log_now_ms());
			printf("       (%zu of %zu bytes taken by the kernel, %llu acknowledged by the "
			       "reader, before it stuck)\n",
			       w->oresponse, w->nresponse, (unsigned long long)w->delivered);
			require(w->delivered < w->oresponse / 4,
			        "progress is what the reader acknowledged, not what the kernel took");
			page_expired(p, log_now_ms() + PAGE_REQUEST_MS + 1);
			require(active(p) == 1, "not closed at 10 s while writing");
			/* ⚠ The stall alone: the average is put well over the floor,
			 *   or the 2 KB/s rule (20 s grace) would close it first. */
			w->delivered = (uint64_t)PAGE_RATE_FLOOR * 1000u;
			page_expired(p, w->last_progress + PAGE_STALL_MS - 1);
			require(active(p) == 1, "not closed 1 ms before 60 s without progress");
			page_expired(p, w->last_progress + PAGE_STALL_MS + 1);
			require(active(p) == 0, "closed 60 s after the last byte acknowledged");
		}
		kill(c, SIGKILL);
		waitpid(c, NULL, 0);
	}

	printf("9. the progress deadline keeps a slow phone that keeps reading\n");
	{
		pid_t c = client_get(port, "127.0.0.1", false);
		client *w = writer_wait(p, 1);
		require(w != NULL, "a writer to look at");
		if (w) {
			uint64_t t = log_now_ms() + 100000;
			/* ⚠ The counters are set by hand: what is checked is the
			 *   rule, not a minute of real slow reading. */
			w->write_start = t - 60000;
			w->last_progress = t - 1000;
			w->delivered = 300000;
			page_expired(p, t);
			require(active(p) == 1, "300 KB in 60 s, last byte 1 s ago: kept");
			w->delivered = 100000;
			page_expired(p, t);
			require(active(p) == 0, "100 KB in 60 s (under 2 KB/s): closed");
		}
		kill(c, SIGKILL);
		waitpid(c, NULL, 0);
	}

	printf("10. 128 readers cannot lock the page out, whatever their speed\n");
	rate_reset(p);
	{
		static pid_t kids[MAX_CLIENTS];
		int k = 0, fd, others = 0;
		for (int a = 1; a <= 32; a++)
			for (int i = 0; i < 4; i++) {
				snprintf(src, sizeof src, "127.0.0.%d", a);
				kids[k++] = client_get(port, src, false);
				pump(p, 2);
			}
		require(writer_wait(p, MAX_CLIENTS) != NULL, "all 128 slots are readers in F_WRITE");
		fd = connect_from(port, "127.0.0.100", 0);
		pump(p, 3);
		/* ⭐ Fourth review: fresh writers of the most crowded groups are the
		 *   last tier, not untouchable — or 128 fresh writers would refuse
		 *   every visitor. */
		require(!closed_by_server(fd) && client_of(p, "[127.0.0.100]") == 1 &&
		                active(p) == MAX_CLIENTS,
		        "a newcomer while they are younger than 5 s is admitted (a fresh writer goes)");
		close(fd);
		pump(p, 3);
		for (size_t i = 0; i < MAX_CLIENTS; i++) {
			client *x = &p->clients[i];
			x->write_start -= PAGE_EVICT_AGE_MS + 1000;
			x->born -= PAGE_EVICT_AGE_MS + 1000;
			/* FAST readers on purpose: 64 KB/s, over the old 32 KB/s rule. */
			x->delivered = 64u * 1024u * (PAGE_EVICT_AGE_MS + 1000) / 1000u;
			x->last_progress = log_now_ms();
		}
		{
			pid_t c = client_get(port, "127.0.0.100", true);
			int st = -1;
			uint64_t t0 = log_now_ms();
			while (waitpid(c, &st, WNOHANG) == 0 && log_now_ms() - t0 < 20000) {
				pump(p, 1);
				page_expired(p, log_now_ms());
			}
			require(WIFEXITED(st) && WEXITSTATUS(st) == 0,
			        "once they are 6 s in (and fast), a real GET gets the page");
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			others += client_active(&p->clients[i]) &&
			          strcmp(p->clients[i].key, "[127.0.0.100]") != 0;
		require(others == MAX_CLIENTS - 1, "exactly one reader was evicted for it");
		for (int i = 0; i < k; i++) {
			kill(kids[i], SIGKILL);
			waitpid(kids[i], NULL, 0);
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]))
				client_close(&p->clients[i]);
	}

	printf("11. the /48: only from real IPv6 peers, and it is the IPv6 group\n");
	{
		struct {
			const char *a;
			bool v6, want;
		} cases[] = {
			{"192.0.2.1", false, false},   {"::ffff:192.0.2.1", true, false},
			{"::1", true, false},          {"64:ff9b::192.0.2.1", true, false},
			{"2001:db8:1:2::5", true, true},
		};
		int good = 0;
		for (size_t i = 0; i < sizeof cases / sizeof cases[0]; i++) {
			struct sockaddr_storage ss;
			unsigned char k48[6] = {0};
			static const unsigned char want48[6] = {0x20, 0x01, 0x0d, 0xb8, 0, 1};
			memset(&ss, 0, sizeof ss);
			if (cases[i].v6) {
				ss.ss_family = AF_INET6;
				inet_pton(AF_INET6, cases[i].a,
				          &((struct sockaddr_in6 *)&ss)->sin6_addr);
			} else {
				ss.ss_family = AF_INET;
				inet_pton(AF_INET, cases[i].a,
				          &((struct sockaddr_in *)&ss)->sin_addr);
			}
			bool got = key48_of(&ss, k48);
			if (got == cases[i].want &&
			    (!got || memcmp(k48, want48, 6) == 0))
				good++;
			else
				printf("       wrong for %s\n", cases[i].a);
		}
		require(good == 5, "IPv4, mapped, loopback, NAT64: none; 2001:db8:1:2::5 → 2001:db8:1::/48");
		{
			client a;
			static const unsigned char same48[6] = {0x20, 0x01, 0x0d, 0xb8, 0, 1};
			static const unsigned char other48[6] = {0x20, 0x01, 0x0d, 0xb8, 0, 2};
			memset(&a, 0, sizeof a);
			a.has48 = true;
			memcpy(a.p48, same48, 6);
			snprintf(a.key, sizeof a.key, "[2001:db8:1:2::/64]");
			require(same_group(&a, true, same48, "[2001:db8:1:3::/64]") &&
			                !same_group(&a, true, other48, "[2001:db8:2:3::/64]") &&
			                !same_group(&a, false, same48, "[2001:db8:1:2::/64]"),
			        "two /64s of one /48 are one group; another /48 or an IPv4 is not");
		}
	}

	printf("12. the request-line budget\n");
	{
		uint64_t t = log_now_ms() + 1000000;
		int yes = 0;
		for (int i = 0; i < 7; i++)
			yes += line_budget(p, "[198.51.100.7]", t);
		require(yes == PAGE_LINES_PER_ADDRESS && line_budget(p, "[198.51.100.8]", t) &&
		                line_budget(p, "[198.51.100.7]", t + PAGE_LINES_WINDOW_MS),
		        "5 lines per address per 10 s; another address has its own; a new window resets");
	}

	printf("13. 17 addresses taking turns cannot reset each other's budget\n");
	{
		uint64_t t = log_now_ms() + 2000000;
		int written[17] = {0}, most = 0, total = 0;
		char key[64];
		for (int round = 0; round < 7; round++)
			for (int a = 0; a < 17; a++) {
				snprintf(key, sizeof key, "[203.0.113.%d]", a + 1);
				written[a] += line_budget(p, key, t + (uint64_t)round * 100);
			}
		for (int a = 0; a < 17; a++) {
			most = written[a] > most ? written[a] : most;
			total += written[a];
		}
		require(most <= PAGE_LINES_PER_ADDRESS &&
		                total <= PAGE_LINES_KEYS * PAGE_LINES_PER_ADDRESS,
		        "no address above 5 lines in its window, at most 16 × 5 in all");
		snprintf(key, sizeof key, "[203.0.113.%d]", 17);
		require(line_budget(p, key, t + PAGE_LINES_WINDOW_MS),
		        "after the window the waiting address gets its line");
	}

	printf("14. a phone 6 s into its download is not evicted by fresh writers' newcomers\n");
	{
		static pid_t kids[MAX_CLIENTS];
		int k = 0, writers = 0, same_body = 0, phone_ok = 1, others = 0;
		for (int i = 0; i < MAX_CLIENTS - 1; i++) {
			snprintf(src, sizeof src, "127.0.0.%d", 1 + i / 4);
			kids[k++] = client_get(port, src, false);
			pump(p, 2);
		}
		kids[k++] = client_get(port, "127.0.0.200", false);
		pump(p, 2);
		require(writer_wait(p, MAX_CLIENTS) != NULL,
		        "127 fresh writers from 32 addresses + the phone, all in F_WRITE");
		for (size_t i = 0; i < MAX_CLIENTS; i++) {
			client *x = &p->clients[i];
			if (!client_active(x) || x->phase != F_WRITE)
				continue;
			writers++;
			same_body += x->shared && x->shared == p->cached;
			/* The attackers FRESH (forking 128 clients takes longer than
			 * 5 s), the phone 6 s in. */
			if (strcmp(x->key, "[127.0.0.200]") == 0)
				x->write_start = log_now_ms() - PAGE_EVICT_AGE_MS - 1000;
			else
				x->write_start = log_now_ms();
		}
		require(writers == MAX_CLIENTS && same_body == MAX_CLIENTS &&
		                p->cached->refs == (size_t)MAX_CLIENTS + 1,
		        "all 128 writers send ONE shared copy of the page (refs 129)");
		int nc[20];
		for (int n = 0; n < 20; n++) {
			snprintf(src, sizeof src, "127.0.0.%d", 201 + n);
			nc[n] = connect_from(port, src, 0);
			pump(p, 2);
			phone_ok &= client_of(p, "[127.0.0.200]") == 1;
		}
		require(phone_ok, "20 newcomers from fresh addresses: the phone is never the victim");
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			others += client_active(&p->clients[i]) && p->clients[i].phase == F_WRITE &&
			          strcmp(p->clients[i].key, "[127.0.0.200]") != 0;
		require(others == MAX_CLIENTS - 1 - 20 && active(p) == MAX_CLIENTS,
		        "the 20 victims were fresh writers from the crowded addresses");
		for (int n = 0; n < 20; n++)
			close(nc[n]);
		for (int i = 0; i < k; i++) {
			kill(kids[i], SIGKILL);
			waitpid(kids[i], NULL, 0);
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]))
				client_close(&p->clients[i]);
		require(p->cached && p->cached->refs == 1, "the shared page is held by the listener alone again");
	}

	printf("15. a banned visitor gets its own «attempts exhausted» page, the others the shared one\n");
	char ban_path[] = "/tmp/pdt-ban-XXXXXX";
	body *shared0 = p->cached;
	uint64_t hash0 = shared0 ? body_hash(shared0) : 0;
	size_t n0 = shared0 ? shared0->n : 0, live0 = nlive;
	{
		int bfd = mkstemp(ban_path);
		FILE *bf = fdopen(bfd, "w");
		uint64_t rem = 0;
		int loaded;
		/* 90 minutes: the notice must say 1 hour and 30 minutes. */
		fprintf(bf, "[127.0.0.50] %lld\n", (long long)time(NULL) + 5400);
		fclose(bf);
		loaded = rcp_ban_load(ban_path, log_now_ms());
		require(loaded == 1 && rcp_banned("[127.0.0.50]:1", log_now_ms(), &rem) &&
		                rem > 5390000 && !rcp_banned("[127.0.0.51]:1", log_now_ms(), NULL),
		        "127.0.0.50 is banned for 90 minutes, 127.0.0.51 is not");
	}
	{
		pid_t kids[3];
		client *ban_w[2] = {NULL, NULL}, *free_w = NULL;
		int nb = 0;
		kids[0] = client_get_as(port, "127.0.0.50", false, true);
		pump(p, 2);
		kids[1] = client_get_as(port, "127.0.0.50", false, true);
		pump(p, 2);
		kids[2] = client_get_as(port, "127.0.0.51", false, false);
		pump(p, 2);
		require(writer_wait(p, 3) != NULL, "two banned slow readers and a free one in F_WRITE");
		for (size_t i = 0; i < MAX_CLIENTS; i++) {
			client *x = &p->clients[i];
			if (!client_active(x) || x->phase != F_WRITE)
				continue;
			if (strcmp(x->key, "[127.0.0.50]") == 0 && nb < 2)
				ban_w[nb++] = x;
			else if (strcmp(x->key, "[127.0.0.51]") == 0)
				free_w = x;
		}
		/* holistic review: a banned response is ITS prefix (in its head)
		 * + the page's shared tail, never a whole private page */
		require(nb == 2 && p->tail && ban_w[0]->shared == p->tail &&
		                ban_w[1]->shared == p->tail && p->tail->refs == 3 &&
		                ban_w[0]->head != ban_w[1]->head,
		        "each banned request has its own prefix and shares the page's tail (refs 3)");
		require(nb == 2 && own_has(ban_w[0], "data-banned=\"yes\"") &&
		                own_has(ban_w[0], "<b>attempts exhausted</b>") &&
		                own_has(ban_w[0], "<b id=\"minutes\">30</b>") &&
		                own_has(ban_w[0], "data-remaining-ms=\"5400000\"") &&
		                !own_has(ban_w[0], "__REMAINING_MS__") &&
		                !body_has(p->tail, "__"),
		        "the banned prefix says «attempts exhausted», 1 h 30 min, 5400000 ms (whole minutes)");
		require(free_w && free_w->shared == shared0 && p->cached == shared0 &&
		                shared0->refs == 2,
		        "the free visitor holds the SAME shared page as before (refs 2)");
		for (int i = 0; i < 3; i++) {
			kill(kids[i], SIGKILL);
			waitpid(kids[i], NULL, 0);
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]))
				client_close(&p->clients[i]);
		require(nlive == live0 + BANNED_LIVE(p) && !live_overflow && p->cached == shared0 &&
		                shared0->refs == 1 && p->tail->refs == 1,
		        "closing them frees both banned prefixes; the shared page and the tail are held by the listener alone");
	}
	{
		pid_t cb = client_get_as(port, "127.0.0.50", true, true);
		pid_t cf = client_get_as(port, "127.0.0.51", true, false);
		int sb = -1, sf = -1, db = 0, df = 0;
		uint64_t t0 = log_now_ms();
		while ((!db || !df) && log_now_ms() - t0 < 20000) {
			pump(p, 1);
			page_expired(p, log_now_ms());
			if (!db && waitpid(cb, &sb, WNOHANG) == cb)
				db = 1;
			if (!df && waitpid(cf, &sf, WNOHANG) == cf)
				df = 1;
		}
		require(db && WIFEXITED(sb) && WEXITSTATUS(sb) == 0,
		        "a real banned GET: 200, data-banned=yes, «attempts exhausted», 1 h 30 min, ms in range");
		require(df && WIFEXITED(sf) && WEXITSTATUS(sf) == 0,
		        "a real free GET at the same time: 200, data-banned=no, no notice, remaining 0");
		pump(p, 2);
		require(p->cached == shared0 && shared0->n == n0 && body_hash(shared0) == hash0 &&
		                shared0->refs == 1 && body_has(shared0, "data-banned=\"no\"") &&
		                !body_has(shared0, "attempts exhausted") &&
		                strcmp(p->cached_fp, "FPTEST") == 0 && nlive == live0 + BANNED_LIVE(p),
		        "the shared page is byte for byte the one before the banned visits; no leak");
	}

	printf("16. allocation failures: the 500 «no mem.», no leak, no half-built shared page\n");
	{
		static client fc;
		size_t n_ban, n_free, n_reb;
		int ok500 = 0, okleak = 0, okshared = 0;

		/* How many allocations one request makes, counted, so that every
		 * one of them can be made to fail (a rebuild of the shared page is
		 * build_page() + the head; a cached one is the head alone). */
		page_mallocs = 0;
		fake_get(p, &fc, "[127.0.0.50]:40000");
		n_ban = page_mallocs;
		require(fc.phase == F_WRITE && fc.shared == p->tail && p->tail->refs == 2 &&
		                own_has(&fc, "data-banned=\"yes\"") &&
		                strncmp(fc.head, "HTTP/1.1 200 ", 13) == 0 && n_ban >= 2,
		        "driven directly, a banned GET gets its own 200 prefix + the tail");
		client_close(&fc);
		page_mallocs = 0;
		fake_get(p, &fc, "[127.0.0.51]:40000");
		n_free = page_mallocs;
		require(fc.shared == shared0 && shared0->refs == 2 && n_free == 1,
		        "a free GET with the page cached allocates only its head");
		client_close(&fc);
		/* the tail and its copy stay for the page's life: from here on they are
		 * part of the baseline */
		live0 += BANNED_LIVE(p);
		require(nlive == live0, "no leak from the two direct GETs");

		/* a) banned: each allocation of build_page()/body_new() fails in turn. */
		for (size_t k = 1; k < n_ban; k++) {
			fail_at = (long)k;
			fail_rest = false;
			fake_get(p, &fc, "[127.0.0.50]:40000");
			fail_at = 0;
			ok500 += is_500(&fc);
			client_close(&fc);
			okleak += nlive == live0;
			okshared += p->cached == shared0 && shared0->refs == 1 &&
			            shared0->n == n0 && body_hash(shared0) == hash0;
		}
		printf("       (a banned GET makes %zu allocations; a free one, cached, %zu)\n",
		       n_ban, n_free);
		require(ok500 == (int)(n_ban - 1),
		        "banned: every failing allocation of build_page()/body_new() gives the 500 «no mem.»");
		require(okleak == (int)(n_ban - 1) && okshared == (int)(n_ban - 1),
		        "banned: none of them leaks, none touches the shared page");

		/* b) banned: the page is built, its 200 head fails — the page is freed. */
		fail_at = (long)n_ban;
		fail_rest = false;
		fake_get(p, &fc, "[127.0.0.50]:40000");
		fail_at = 0;
		require(fc.head == NULL && fc.shared == NULL && fc.phase != F_WRITE &&
		                nlive == live0 && p->cached == shared0 && shared0->refs == 1,
		        "banned, the 200 head fails: no response, the banned page freed, no leak");
		client_close(&fc);

		/* c) banned: the build fails AND so does the 500 head. */
		ok500 = okleak = 0;
		for (size_t k = 1; k < n_ban; k++) {
			fail_at = (long)k;
			fail_rest = true;
			fake_get(p, &fc, "[127.0.0.50]:40000");
			fail_at = 0;
			fail_rest = false;
			ok500 += fc.head == NULL && fc.shared == NULL && fc.phase != F_WRITE;
			client_close(&fc);
			okleak += nlive == live0 && p->cached == shared0 && shared0->refs == 1;
		}
		require(ok500 == (int)(n_ban - 1) && okleak == (int)(n_ban - 1),
		        "banned, the 500 head fails too: no response, no leak, shared page untouched");

		/* d) a rotation: the shared page must be rebuilt, and the rebuild fails. */
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPROT");
		page_mallocs = 0;
		fail_at = 1 << 20; /* armed but never reached: only counts */
		fake_get(p, &fc, "[127.0.0.51]:40000");
		fail_at = 0;
		n_reb = page_mallocs;
		/* ⭐ §11.44: a rebuild is build_page() (n_ban - 1 allocations, as a
		 *   banned page), THEN the gzip copy (zlib's own, through the
		 *   seam), then the head: more than a banned GET. */
		require(fc.shared && fc.shared == p->cached && fc.shared != shared0 &&
		                strcmp(p->cached_fp, "FPROT") == 0 && body_has(fc.shared, "FPROT") &&
		                p->cached_gz && n_reb > n_ban,
		        "after a rotation a free GET rebuilds the shared page and its gzip copy");
		printf("       (a rebuild makes %zu allocations, %zu of them the gzip copy)\n",
		       n_reb, n_reb - n_ban);
		/* Back to the state before the rotation, through the same road. */
		client_close(&fc);
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPTEST");
		fake_get(p, &fc, "[127.0.0.51]:40000");
		client_close(&fc);
		shared0 = p->cached;
		hash0 = body_hash(shared0);
		require(nlive == live0 && strcmp(p->cached_fp, "FPTEST") == 0 && shared0->refs == 1 &&
		                shared0->n == n0,
		        "two rebuilds: the old shared pages freed, no leak");
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPROT");
		ok500 = okleak = okshared = 0;
		/* build_page()'s allocations only: a failing gzip copy is section 17. */
		for (size_t k = 1; k < n_ban; k++) {
			fail_at = (long)k;
			fail_rest = false;
			fake_get(p, &fc, "[127.0.0.51]:40000");
			fail_at = 0;
			ok500 += is_500(&fc);
			client_close(&fc);
			okleak += nlive == live0;
			/* ⛔ Never a half-built or a stale page served as the new one:
			 *    the old one stays, whole, under its own fingerprint. */
			okshared += p->cached == shared0 && shared0->refs == 1 &&
			            body_hash(shared0) == hash0 && strcmp(p->cached_fp, "FPTEST") == 0;
		}
		require(ok500 == (int)(n_ban - 1),
		        "rotation, the rebuild fails: the 500 «no mem.», never the old page under the new fingerprint");
		require(okleak == (int)(n_ban - 1) && okshared == (int)(n_ban - 1),
		        "rotation, the rebuild fails: no leak, the old shared page whole and not replaced");
		/* e) the rebuild succeeds, the head fails: the new page is kept. */
		fail_at = (long)n_reb;
		fake_get(p, &fc, "[127.0.0.51]:40000");
		fail_at = 0;
		require(fc.head == NULL && fc.shared == NULL && p->cached != NULL &&
		                p->cached->refs == 1 && strcmp(p->cached_fp, "FPROT") == 0 &&
		                body_has(p->cached, "FPROT") && nlive == live0,
		        "rotation, the head fails after the rebuild: the new page kept (refs 1), the old freed, no leak");
		client_close(&fc);
		fake_get(p, &fc, "[127.0.0.51]:40000");
		require(fc.shared == p->cached && p->cached->refs == 2 && nlive == live0 + 1,
		        "and the next free GET is served from it");
		client_close(&fc);
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPTEST");
		require(!live_overflow, "the allocation tracker never overflowed");
	}
	printf("17. gzip (§11.44): the shared page compressed once, sent only to who accepts it\n");
	{
		static client fc, fc2;
		size_t live1, n_plain, n_gz, n_reb = 0;
		int ok = 0, okleak = 0, k_ok = 0, ntab = 0;
		struct { const char *ae; bool gz; } tab[] = {
			{"gzip", true}, {"gzip, deflate, br, zstd", true}, {"GZIP", true},
			{"x-gzip", true}, {"deflate, gzip;q=1.0", true}, {"gzip;q=0.001", true},
			{"gzip ; q=0.5", true}, {"gzip;Q=1", true}, {"gzip;level=1", true},
			{"*", true}, {"br, *;q=0.1", true}, {"*;q=0, gzip", true},
			{"gzip;q=0", false}, {"gzip;q=0.000", false}, {"gzip; q=0.", false},
			{"gzip;q=0, *", false}, {"*, gzip;q=0", false}, {"*;q=0", false},
			{"identity", false}, {"br, deflate", false}, {"", false},
			{"gzipx", false}, {"gzip;q=1.5", false}, {"gzip;q=", false},
			{"gzip;q", false}, {"gzip x", false}, {"gzip;q=0,gzip", false},
			{"gzip;q=-1", false},
			/* review of 6d8249c4: the empty parameter is skipped, not the element */
			{"gzip;q=0;, *", false}, {"gzip;;q=0, *", false}, {"gzip; ;q=0 , *", false},
			{"gzip;q=0.5;", true}, {"gzip;;", true}, {"*;q=0;, gzip;", true},
			/* … and a parameter that does not read makes the element count for nothing */
			{"gzip;=x", false}, {"gzip;a=", false}, {"gzip;a=b=c", false},
			{"gzip;a = b", false}, {"gzip;q =1", false}, {"gzip;q= 1", false},
			{"gzip;q=1;q=1", false}, {"gzip;a=\"x\"", false}, {"gzip;a=b", true},
			{"gzip;=x, *", true}, {"gzip;q=0;a=, *", true},
		};

		/* The state of section 16 put back through the road a visitor takes;
		 * a banned gzip GET first, so that the tail's gzip copy (kept for
		 * the page's life) is in the baseline. */
		fake_get(p, &fc, "[127.0.0.51]:40000");
		client_close(&fc);
		fake_get_ae(p, &fc, "[127.0.0.50]:40000", "gzip");
		client_close(&fc);
		live1 = nlive;
		require(p->cached && p->cached_gz && !p->cached_gz_retry &&
		                p->cached->refs == 1 && p->cached_gz->refs == 1 &&
		                strcmp(p->cached_fp, "FPTEST") == 0 &&
		                gunzips_to(p->cached_gz->data, p->cached_gz->n, p->cached) &&
		                p->cached_gz->n < p->cached->n / 10,
		        "one plain and one gzip copy of the shared page; the gzip copy inflates to it exactly");
		printf("       (the page: %zu bytes plain, %zu gzip)\n", p->cached->n, p->cached_gz->n);

		for (size_t i = 0; i < sizeof tab / sizeof tab[0]; i++) {
			char rq[256];
			int n = snprintf(rq, sizeof rq, "GET / HTTP/1.1\r\nHost: t\r\n"
			                 "Accept-Encoding: %s\r\n\r\n", tab[i].ae);
			bool got = accepts_gzip(rq, (size_t)n);
			ntab++;
			if (got == tab[i].gz)
				ok++;
			else
				printf("       ⛔ «Accept-Encoding: %s» → %s\n", tab[i].ae, got ? "gzip" : "plain");
		}
		{
			const char *r1 = "GET / HTTP/1.1\r\nHost: t\r\n\r\n";
			const char *r2 = "GET / HTTP/1.1\r\naccept-encoding: gzip\r\n\r\n";
			const char *r3 = "GET / HTTP/1.1\r\nAccept-Encoding: br\r\nAccept-Encoding: gzip\r\n\r\n";
			const char *r4 = "GET / HTTP/1.1\r\nX-Accept-Encoding: gzip\r\n\r\n";
			const char *r5 = "GET / HTTP/1.1\r\nHost: t\r\n\r\nAccept-Encoding: gzip\r\n";
			const char *r6 = "GET / HTTP/1.1\nAccept-Encoding:gzip\n\n";
			ok += !accepts_gzip(r1, strlen(r1)) && accepts_gzip(r2, strlen(r2)) &&
			      accepts_gzip(r3, strlen(r3)) && !accepts_gzip(r4, strlen(r4)) &&
			      !accepts_gzip(r5, strlen(r5)) && accepts_gzip(r6, strlen(r6));
			ntab++;
		}
		require(ok == ntab, "Accept-Encoding read as RFC 9110 says: q-values, gzip;q=0, *, x-gzip, no header = plain");

		/* review of 6d8249c4: a folded header line is refused with 400 */
		{
			const char *f1 = "GET / HTTP/1.1\r\nAccept-Encoding: br,\r\n gzip\r\n\r\n";
			const char *f2 = "GET / HTTP/1.1\r\nHost: t\r\n\tx\r\n\r\n";
			const char *f3 = "GET / HTTP/1.1\r\nHost: t\r\n\r\n gzip";
			const char *f4 = "GET / HTTP/1.1\nHost: t\n\n";
			memset(&fc, 0, sizeof fc);
			fc.fd = -1;
			fc.phase = F_READ;
			snprintf(fc.provenance, sizeof fc.provenance, "[127.0.0.51]:40000");
			fc.nrequest = strlen(f1);
			memcpy(fc.request, f1, fc.nrequest);
			serve(p, &fc);
			require(has_obs_fold(f1, strlen(f1)) && has_obs_fold(f2, strlen(f2)) &&
			                !has_obs_fold(f3, strlen(f3)) && !has_obs_fold(f4, strlen(f4)) &&
			                fc.head && strncmp(fc.head, "HTTP/1.1 400 ", 13) == 0 &&
			                fc.shared == NULL,
			        "a folded header line (obs-fold) gets 400, not a half-read Accept-Encoding");
			client_close(&fc);
		}

		/* review of 6d8249c4: the gzip copy keeps only its own bytes */
		{
			size_t big;
			require(malloc_usable_size(p->cached_gz) < sizeof(body) + p->cached_gz->n + 64,
			        "the gzip copy was shrunk to its bytes (not the worst-case buffer)");
			snprintf(cert.fingerprint, sizeof cert.fingerprint, "%s", OTHER_FP(p));
			fail_realloc = true;
			fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip");
			fail_realloc = false;
			big = malloc_usable_size(p->cached_gz);
			require(fc.shared == p->cached_gz && big > p->cached->n / 2 &&
			                head_length(&fc) == (long long)p->cached_gz->n &&
			                gunzips_to(p->cached_gz->data, p->cached_gz->n, p->cached),
			        "a failed shrink keeps the big buffer, served and whole");
			client_close(&fc);
			snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPTEST");
			fake_get(p, &fc, "[127.0.0.51]:40000");
			client_close(&fc);
			require(nlive == live1, "no leak around the shrink");
		}

		fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip, deflate, br");
		n_gz = fc.nresponse;
		require(fc.phase == F_WRITE && fc.shared == p->cached_gz && p->cached_gz->refs == 2 &&
		                head_has(&fc, "\r\nContent-Encoding: gzip\r\n") &&
		                head_has(&fc, "\r\nVary: Accept-Encoding\r\n") &&
		                head_length(&fc) == (long long)p->cached_gz->n &&
		                fc.nresponse == fc.nhead + p->cached_gz->n,
		        "a gzip request gets the SHARED gzip copy: Content-Encoding, Vary, Content-Length = compressed bytes");
		fake_get_ae(p, &fc2, "[127.0.0.52]:40000", "gzip");
		require(fc2.shared == p->cached_gz && p->cached_gz->refs == 3 && nlive == live1 + 2,
		        "a second gzip request shares the same copy (refs 3, only its head allocated)");
		client_close(&fc2);
		client_close(&fc);
		require(p->cached_gz->refs == 1 && nlive == live1, "closing them: refs back to 1, no leak");

		fake_get_ae(p, &fc, "[127.0.0.51]:40000", NULL);
		n_plain = fc.nresponse;
		require(fc.shared == p->cached && !head_has(&fc, "Content-Encoding") &&
		                head_has(&fc, "\r\nVary: Accept-Encoding\r\n") &&
		                head_length(&fc) == (long long)p->cached->n &&
		                fc.nresponse == fc.nhead + p->cached->n && n_gz < n_plain,
		        "no Accept-Encoding: the plain page, Content-Length = its bytes");
		client_close(&fc);
		fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip;q=0");
		require(fc.shared == p->cached && !head_has(&fc, "Content-Encoding") &&
		                head_length(&fc) == (long long)p->cached->n,
		        "«gzip;q=0»: the plain page");
		client_close(&fc);
		/* holistic review: the banned page goes gzip too — its own
		 * compressed prefix + the tail's copy + its own trailer, one gzip
		 * member that inflates to exactly the plain banned page */
		{
			static client fp;
			size_t hlg, hlp, nb_plain = 0, nb_gz = 0, nz = 0;
			char *plain = NULL, *gzb = NULL;
			unsigned char *u = NULL;
			fake_get_ae(p, &fp, "[127.0.0.50]:40000", NULL);
			fake_get_ae(p, &fc, "[127.0.0.50]:40000", "gzip");
			hlg = fc.head ? (size_t)((char *)memmem(fc.head, fc.nhead, "\r\n\r\n", 4) - fc.head) + 4 : 0;
			hlp = fp.head ? (size_t)((char *)memmem(fp.head, fp.nhead, "\r\n\r\n", 4) - fp.head) + 4 : 0;
			if (hlg && hlp) {
				nb_plain = fp.nresponse - hlp;
				nb_gz = fc.nresponse - hlg;
				plain = malloc(nb_plain);
				gzb = malloc(nb_gz);
				memcpy(plain, fp.head + hlp, fp.nhead - hlp);
				memcpy(plain + fp.nhead - hlp, fp.shared->data, fp.shared->n);
				memcpy(gzb, fc.head + hlg, fc.nhead - hlg);
				memcpy(gzb + fc.nhead - hlg, fc.shared->data, fc.shared->n);
				memcpy(gzb + fc.nhead - hlg + fc.shared->n, fc.tail, fc.ntail);
				u = gunzip(gzb, nb_gz, &nz);
			}
			require(fc.shared == p->tail_gz && fc.ntail == 8 && fp.shared == p->tail &&
			                fp.ntail == 0 && head_has(&fc, "\r\nContent-Encoding: gzip\r\n") &&
			                head_has(&fc, "\r\nVary: Accept-Encoding\r\n") &&
			                head_has(&fp, "\r\nVary: Accept-Encoding\r\n") &&
			                !head_has(&fp, "Content-Encoding") &&
			                head_length(&fc) == (long long)nb_gz &&
			                head_length(&fp) == (long long)nb_plain &&
			                nb_plain == fp.nresponse - hlp && nb_gz < nb_plain / 4,
			        "a banned visitor asking gzip gets gzip (own prefix + shared tail + 8-byte trailer); Content-Length right both ways");
			require(u && nz == nb_plain && memcmp(u, plain, nz) == 0 &&
			                memmem(plain, nb_plain, "data-banned=\"yes\"", 17) &&
			                memmem(plain, nb_plain, "<b>attempts exhausted</b>", 25) &&
			                !memmem(plain, nb_plain, "__", 2) &&
			                nb_plain > p->tail->n &&
			                memcmp(plain + nb_plain - p->tail->n, p->html + p->nhtml - p->tail->n,
			                       p->tail->n) == 0,
			        "… and it inflates to exactly the plain banned page (markers replaced, the template's tail)");
			free(u);
			free(plain);
			free(gzb);
			client_close(&fp);
			client_close(&fc);
		}
		require(nlive == live1, "no leak from the direct GETs");

		{
			bool oom = true;
			body *tiny = body_new("ab", 2);
			body *z = tiny ? gz_page(tiny, &oom, 6) : NULL;
			require(tiny && !z && !oom && nlive == live1 + 1,
			        "a body that does not come out smaller gets no gzip copy (and no retry)");
			body_unref(z);
			body_unref(tiny);
		}

		/* A real GET over TLS, both ways: Content-Length = the bytes on the wire. */
		{
			pid_t cg = client_get_ae(port, "127.0.0.61", "gzip, br", true, p->cached);
			pid_t cp = client_get_ae(port, "127.0.0.62", "br;q=1, gzip;q=0", false, p->cached);
			int sg = -1, sp = -1, dg = 0, dp = 0;
			uint64_t t0 = log_now_ms();
			while ((!dg || !dp) && log_now_ms() - t0 < 20000) {
				pump(p, 1);
				page_expired(p, log_now_ms());
				if (!dg && waitpid(cg, &sg, WNOHANG) == cg)
					dg = 1;
				if (!dp && waitpid(cp, &sp, WNOHANG) == cp)
					dp = 1;
			}
			require(dg && WIFEXITED(sg) && WEXITSTATUS(sg) == 0,
			        "a real gzip GET: 200, Content-Encoding gzip, Content-Length = bytes received, inflates to the page");
			require(dp && WIFEXITED(sp) && WEXITSTATUS(sp) == 0,
			        "a real «gzip;q=0» GET: 200, the plain page, Content-Length = bytes received");
			pump(p, 2);
			require(p->cached->refs == 1 && p->cached_gz->refs == 1 && nlive == live1,
			        "after them: both copies held by the listener alone, no leak");
		}

		/* A rotation counts the allocations of a rebuild; then each of the
		 * gzip copy's allocations fails in turn. */
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPROT");
		page_mallocs = 0;
		fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip");
		n_reb = page_mallocs;
		require(fc.shared == p->cached_gz && strcmp(p->cached_fp, "FPROT") == 0 &&
		                body_has(p->cached, "FPROT") &&
		                gunzips_to(p->cached_gz->data, p->cached_gz->n, p->cached) &&
		                nlive == live1 + 1,
		        "a rotation rebuilds BOTH copies (the new gzip inflates to the new page); the old ones freed");
		client_close(&fc);
		{
			size_t n_ban;
			page_mallocs = 0;
			fake_get(p, &fc, "[127.0.0.50]:40000");
			n_ban = page_mallocs;
			client_close(&fc);
			int ok_plain = 0, ok_retry = 0, ok_head = 0, tries = 0;
			okleak = 0;
			for (size_t k = n_ban; k < n_reb; k++) {
				tries++;
				snprintf(cert.fingerprint, sizeof cert.fingerprint, "%s", OTHER_FP(p));
				fail_at = (long)k;
				fail_rest = false;
				fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip");
				fail_at = 0;
				/* ⭐ the plain page still goes out — the gzip copy is a bonus */
				ok_plain += fc.phase == F_WRITE && fc.shared == p->cached && p->cached &&
				            !p->cached_gz && p->cached_gz_retry &&
				            strcmp(p->cached_fp, cert.fingerprint) == 0 &&
				            body_has(p->cached, cert.fingerprint) &&
				            !head_has(&fc, "Content-Encoding") &&
				            head_length(&fc) == (long long)p->cached->n;
				client_close(&fc);
				okleak += nlive == live1 - 1;
				/* the next gzip request retries, and gets it */
				fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip");
				ok_retry += fc.shared && fc.shared == p->cached_gz && !p->cached_gz_retry &&
				            head_has(&fc, "\r\nContent-Encoding: gzip\r\n") &&
				            gunzips_to(p->cached_gz->data, p->cached_gz->n, p->cached);
				client_close(&fc);
				okleak += nlive == live1;
				/* the gzip copy fails AND so does everything after it */
				snprintf(cert.fingerprint, sizeof cert.fingerprint, "%s", OTHER_FP(p));
				fail_at = (long)k;
				fail_rest = true;
				fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip");
				fail_at = 0;
				fail_rest = false;
				ok_head += fc.head == NULL && fc.shared == NULL && p->cached &&
				           !p->cached_gz && p->cached_gz_retry;
				client_close(&fc);
				okleak += nlive == live1 - 1;
			}
			printf("       (a rebuild: %zu allocations, %d of them the gzip copy's)\n", n_reb, tries);
			require(tries > 0 && ok_plain == tries,
			        "each failing allocation of the gzip copy: the plain page is served (200, no Content-Encoding)");
			require(ok_retry == tries, "… and the next gzip request builds the copy again and gets it");
			require(ok_head == tries && okleak == 3 * tries,
			        "… and with the head failing too: no response; none of them leaks");
			k_ok = 1;
		}
		/* A request that does not accept gzip never retries the copy. */
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPTEST");
		fake_get_ae(p, &fc, "[127.0.0.51]:40000", "gzip");
		client_close(&fc);
		fail_at = (long)n_reb - 1; /* the gzip copy's last allocation, the body */
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPROT");
		fake_get_ae(p, &fc, "[127.0.0.51]:40000", NULL);
		fail_at = 0;
		client_close(&fc);
		page_mallocs = 0;
		fake_get_ae(p, &fc, "[127.0.0.51]:40000", "br");
		require(k_ok && p->cached_gz_retry && !p->cached_gz && page_mallocs == 1 &&
		                fc.shared == p->cached,
		        "with the copy missing, a request without gzip allocates only its head (no retry)");
		client_close(&fc);
		snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPTEST");
		fake_get(p, &fc, "[127.0.0.51]:40000");
		client_close(&fc);
		require(nlive == live1 && p->cached_gz && !live_overflow,
		        "back to FPTEST: both copies rebuilt, no leak, the tracker never overflowed");
	}

	printf("18. holistic review: log forgery, the accept rate, the work per pass\n");
	{
		static client fc;
		char lpath[] = "/tmp/pdt-log-XXXXXX";
		int lfd = mkstemp(lpath), saved = dup(STDERR_FILENO);
		char lb[8192];
		ssize_t ln;
		int lines = 0;
		const char *forged =
			"GET /\n14:00:00.000 rcp     [owner] \xe2\xad\x90 ADMITTED from 1.2.3.4\x1b[2J HTTP/1.1\r\n"
			"Host: t\r\n\r\n";

		/* a) the request line is the first line only: a target with a raw
		 *    newline has no second space on its line → 400, and nothing of
		 *    the next line reaches the log */
		fflush(stderr);
		dup2(lfd, STDERR_FILENO);
		memset(&fc, 0, sizeof fc);
		fc.fd = -1;
		fc.phase = F_READ;
		snprintf(fc.provenance, sizeof fc.provenance, "[127.0.0.81]:40000");
		fc.nrequest = strlen(forged);
		memcpy(fc.request, forged, fc.nrequest);
		serve(p, &fc);
		require(fc.head && strncmp(fc.head, "HTTP/1.1 400 ", 13) == 0,
		        "a request line broken by a raw newline gets 400");
		client_close(&fc);

		/* b) a long target with control and escape bytes: logged cleaned
		 *    and cut, ONE line.  (The request-line budget emptied first: the
		 *    sections before filled its 16 addresses within 10 s.) */
		memset(p->lines, 0, sizeof p->lines);
		{
			char big[1200];
			int n = snprintf(big, sizeof big, "GET /?a=\x1b[31m\x7f");
			memset(big + n, 'x', 600);
			n += 600;
			n += snprintf(big + n, sizeof big - (size_t)n, " HTTP/1.1\r\nHost: t\r\n\r\n");
			memset(&fc, 0, sizeof fc);
			fc.fd = -1;
			fc.phase = F_READ;
			snprintf(fc.provenance, sizeof fc.provenance, "[127.0.0.82]:40000");
			fc.nrequest = (size_t)n;
			memcpy(fc.request, big, fc.nrequest);
			serve(p, &fc);
			client_close(&fc);
		}
		fflush(stderr);
		dup2(saved, STDERR_FILENO);
		close(saved);
		ln = pread(lfd, lb, sizeof lb - 1, 0);
		lb[ln > 0 ? ln : 0] = 0;
		for (ssize_t k = 0; k < ln; k++)
			lines += lb[k] == '\n';
		if (lines != 1 || ln >= 400)
			printf("       the log: «%s»\n", lb);
		require(ln > 0 && lines == 1 && !strstr(lb, "ADMITTED") && !strchr(lb, '\x1b') &&
		                strstr(lb, "GET /?a=?[31m?xxx") && strstr(lb, "…(610 bytes) from [127.0.0.82]") && ln < 400,
		        "the logged target: printable ASCII, each other byte `?`, cut at 200 with its length; no forged line");
		close(lfd);
		unlink(lpath);

		/* c) the accept buckets (review of 95ed70ea): a burst then the rate;
		 *    a newcomer gets a bucket of its own only if one is FULL, else
		 *    it shares ONE overflow bucket; a /48 refusal spends no /64
		 *    token, and the refusal names the bucket that refused */
		{
			static page rp;
			const char *who = NULL;
			int got = 0, later = 0, newk = 0, own = 0, n48 = 0;
			uint64_t t0 = 1000000;
			for (int i = 0; i < 20; i++)
				got += rate_take(&rp, "[10.0.0.1]", NULL, t0, &who);
			for (int i = 0; i < 20; i++)
				later += rate_take(&rp, "[10.0.0.1]", NULL, t0 + 1000, &who);
			require(got == PAGE_ACCEPT_BURST && later == PAGE_ACCEPT_RATE,
			        "a bucket: the burst (8), then 4 a second");
			memset(&rp, 0, sizeof rp);
			for (int i = 0; i < PAGE_RATE_KEYS; i++) {
				char k[32];
				snprintf(k, sizeof k, "[10.1.0.%d]", i);
				rate_take(&rp, k, NULL, t0, &who); /* each bucket one short of full */
			}
			for (int i = 0; i < 40; i++) {
				char k[32];
				snprintf(k, sizeof k, "[10.2.0.%d]", i);
				newk += rate_take(&rp, k, NULL, t0 + 100, &who);
				newk += rate_take(&rp, k, NULL, t0 + 100, &who);
			}
			printf("       (40 rotating addresses × 2 with every bucket in use: %d admitted)\n", newk);
			require(newk == PAGE_ACCEPT_BURST && strcmp(who, "(the shared overflow bucket)") == 0,
			        "rotating new addresses share ONE overflow bucket: 8 admitted, not 80 (on 95ed70ea: a fresh burst each)");
			for (int i = 0; i < 10; i++)
				own += rate_take(&rp, "[10.3.0.1]", NULL, t0 + 5000, &who);
			require(own == PAGE_ACCEPT_BURST,
			        "once a bucket is full again, a new address gets a bucket of its own");
			memset(&rp, 0, sizeof rp);
			for (int i = 0; i < 20; i++) {
				char k[32];
				snprintf(k, sizeof k, "[2001:db8:1:%x::]", i);
				n48 += rate_take(&rp, k, "2001:0db8:0001::/48", t0, &who);
			}
			{
				struct bucket *b = bucket_of(rp.rate, &rp.rate_over, "[2001:db8:1:13::]",
				                             t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
				require(n48 == PAGE_ACCEPT_BURST_48 && strcmp(who, "2001:0db8:0001::/48") == 0 &&
				                b->milli == PAGE_ACCEPT_BURST * 1000u,
				        "a /48 over its rate: refused, named as the /48, and the /64 keeps its token");
			}
		}
		/* … and over the rate a connection is PARKED (no TLS), then started
		 *   when a token comes; one that waits in vain is served 503 */
		{
			const char *who = NULL;
			client *pc = NULL;
			int f83, f84, ev0 = 0;
			uint64_t now = log_now_ms();
			while (rate_take(p, "[127.0.0.83]", NULL, now, &who))
				;
			f83 = connect_from(port, "127.0.0.83", 0);
			pump(p, 2);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]) &&
				    strcmp(p->clients[i].key, "[127.0.0.83]") == 0)
					pc = &p->clients[i];
			{
				struct pollfd f[MAX_CLIENTS + 1];
				size_t m = page_descriptors(p, f, MAX_CLIENTS + 1);
				for (size_t k = 0; k < m; k++)
					if (pc && f[k].fd == pc->fd)
						ev0 = f[k].events == 0;
			}
			require(pc && pc->phase == F_RATE && !pc->ssl && ev0 && !closed_by_server(f83),
			        "over the rate: accepted and parked — no TLS, not watched, not closed");
			usleep(400000);
			page_expired(p, log_now_ms());
			require(pc && pc->phase == F_HANDSHAKE && pc->ssl && !pc->busy,
			        "… a token later its TLS begins");
			pc = NULL;
			now = log_now_ms();
			while (rate_take(p, "[127.0.0.84]", NULL, now, &who))
				;
			f84 = connect_from(port, "127.0.0.84", 0);
			pump(p, 2);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]) &&
				    strcmp(p->clients[i].key, "[127.0.0.84]") == 0)
					pc = &p->clients[i];
			while (rate_take(p, "[127.0.0.84]", NULL, now + PAGE_RATE_WAIT_MS + 1, &who))
				;
			page_expired(p, now + PAGE_RATE_WAIT_MS + 1);
			require(pc && pc->busy && pc->phase == F_HANDSHAKE && pc->ssl,
			        "one that waited PAGE_RATE_WAIT_MS in vain gets TLS, marked busy");
			memset(&fc, 0, sizeof fc);
			fc.fd = -1;
			fc.phase = F_READ;
			fc.busy = true;
			snprintf(fc.provenance, sizeof fc.provenance, "[127.0.0.84]:40000");
			fc.nrequest = (size_t)snprintf(fc.request, sizeof fc.request,
			                               "GET /fingerprint HTTP/1.1\r\nHost: t\r\n\r\n");
			serve(p, &fc);
			require(fc.head && strncmp(fc.head, "HTTP/1.1 503 ", 13) == 0 &&
			                head_has(&fc, "\r\nRetry-After: 1\r\n"),
			        "… and its request is answered 503 with Retry-After, which the page tells apart");
			client_close(&fc);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]))
					client_close(&p->clients[i]);
			close(f83);
			close(f84);
		}

		/* d) the work per pass: at most 16 events, round robin */
		{
			struct pollfd f[40];
			size_t m0, m1, m2;
			for (int i = 0; i < 40; i++)
				f[i] = (struct pollfd){.fd = 100000 + i, .events = POLLIN, .revents = POLLIN};
			p->move_next = 0;
			page_move(p, f, 40);
			m0 = p->move_next;
			page_move(p, f, 40);
			m1 = p->move_next;
			page_move(p, f, 40);
			m2 = p->move_next;
			require(m0 == PAGE_EVENTS_PER_PASS && m1 == 2 * PAGE_EVENTS_PER_PASS &&
			                m2 == (3 * PAGE_EVENTS_PER_PASS) % 40,
			        "page_move handles at most 16 events a pass and starts where it stopped");
		}
	}

	printf("19. independent review of 16b75f33: bare connects never push out a client that spoke\n");
	rate_reset(p);
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (client_active(&p->clients[i]))
			client_close(&p->clients[i]);
	{
		static int bare[MAX_CLIENTS + 40];
		int nb = 0, owner_ok = 1, sizes_ok = 1;
		pid_t owner;
		unsigned sz[MAX_CLIENTS];
		/* the owner first — the OLDEST — a real TLS handshake, then nothing */
		owner = fork();
		if (owner == 0) {
			int fd = connect_from(port, "127.0.3.1", 0);
			SSL_CTX *cx = SSL_CTX_new(TLS_client_method());
			SSL *ss = SSL_new(cx);
			SSL_set_fd(ss, fd);
			SSL_connect(ss);
			for (;;)
				pause();
		}
		{
			uint64_t t0 = log_now_ms();
			while (log_now_ms() - t0 < 5000) {
				pump(p, 1);
				bool done = false;
				for (size_t i = 0; i < MAX_CLIENTS; i++)
					if (client_active(&p->clients[i]) &&
					    strcmp(p->clients[i].key, "[127.0.3.1]") == 0 &&
					    p->clients[i].spoke)
						done = true;
				if (done)
					break;
			}
		}
		/* review of 95ed70ea: each attacker sends ONE byte (and the start of
		 * a record): that is not a ClientHello, it is still silent */
		for (int i = 0; i < MAX_CLIENTS - 1; i++) {
			snprintf(src, sizeof src, "127.0.4.%d", i + 1);
			/* the rate out of the way: every attacker gets its TLS begun
			 * (parked ones would be silent for another reason) */
			rate_reset(p);
			bare[nb++] = connect_from(port, src, 0);
			/* 1 byte, the start of a record, or (review of 38639d7d) the
			 * 9-byte record 16 03 01 00 04 01 00 01 fc that takes OpenSSL
			 * 3.5.7 out of TLS_ST_BEFORE without being a ClientHello */
			static const char *const junk[] = {"\x16", "\x16\x03\x01\x00\x40",
			                                   "\x16\x03\x01\x00\x04\x01\x00\x01\xfc"};
			static const size_t njunk[] = {1, 5, 9};
			if (send(bare[nb - 1], junk[i % 3], njunk[i % 3], 0) < 0)
				owner_ok = 0;
			pump(p, 1);
		}
		pump(p, 3);
		{
			int nspoke = 0;
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				nspoke += client_active(&p->clients[i]) && p->clients[i].spoke;
			printf("       (%d of %d say «spoke»)\n", nspoke, active(p));
			require(owner_ok && active(p) == MAX_CLIENTS && client_of(p, "[127.0.3.1]") == 1 &&
			                nspoke == 1,
			        "the owner (a real handshake, the oldest) + 127 connects sending 1, 5 or the 9-byte record: only the owner «spoke»");
		}
		/* group sizes counted once: the same answer as one group_size() each */
		group_sizes(p, sz);
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]))
				sizes_ok &= sz[i] == group_size(p, p->clients[i].has48,
				                                p->clients[i].p48, p->clients[i].key);
		{
			uint64_t t0 = log_now_ms();
			for (int k = 0; k < 2000; k++)
				(void)fair_victim(p, 0, log_now_ms());
			printf("       (fair_victim on a full table of 128 groups: %.1f µs each)\n",
			       (log_now_ms() - t0) * 1000.0 / 2000);
		}
		/* the attackers out of their first PAGE_YOUNG_MS: silent now */
		usleep((PAGE_YOUNG_MS + 100) * 1000);
		for (int i = 0; i < 30; i++) {
			snprintf(src, sizeof src, "127.0.5.%d", i + 1);
			rate_reset(p);
			bare[nb++] = connect_from(port, src, 0);
			if (send(bare[nb - 1], "\x16\x03\x01\x00\x04\x01\x00\x01\xfc", 9, 0) < 0)
				owner_ok = 0;
			pump(p, 2);
			owner_ok &= client_of(p, "[127.0.3.1]") == 1;
		}
		require(owner_ok && active(p) == MAX_CLIENTS,
		        "30 more connects sending the 9-byte record: each evicts a SILENT one, never the owner (on 38639d7d that record counted as «spoke»)");
		require(sizes_ok, "group sizes counted once per eviction agree with one count per client");
		page_expired(p, log_now_ms() + PAGE_REQUEST_MS + 1);
		for (int i = 0; i < nb; i++)
			close(bare[i]);
		kill(owner, SIGKILL);
		waitpid(owner, NULL, 0);
		pump(p, 4);
	}

	printf("20. review of 95ed70ea: a failed build of the tail's gzip copy is not retried at every banned GET\n");
	{
		static client fc;
		size_t n_plain, n_after;
		body_unref(p->tail_gz);
		p->tail_gz = NULL;
		p->tail_gz_after = 0;
		page_mallocs = 0;
		fake_get_ae(p, &fc, "[127.0.0.50]:40000", NULL);
		n_plain = page_mallocs;
		client_close(&fc);
		/* the prefix is pre + 5 replaces (6 allocations); the 7th is zlib's
		 * first for the tail: it fails */
		fail_at = 7;
		fail_rest = false;
		fake_get_ae(p, &fc, "[127.0.0.50]:40000", "gzip");
		fail_at = 0;
		bool first = fc.head && !head_has(&fc, "Content-Encoding") && !p->tail_gz;
		client_close(&fc);
		page_mallocs = 0;
		fake_get_ae(p, &fc, "[127.0.0.50]:40000", "gzip");
		n_after = page_mallocs;
		bool second = fc.head && !head_has(&fc, "Content-Encoding") && !p->tail_gz;
		client_close(&fc);
		require(first && second && n_after == n_plain,
		        "after the failure the next banned gzip GET does not try again (plain, as many allocations as a plain one)");
		p->tail_gz_after = 0;
		fake_get_ae(p, &fc, "[127.0.0.50]:40000", "gzip");
		require(p->tail_gz && fc.shared == p->tail_gz && head_has(&fc, "\r\nContent-Encoding: gzip\r\n"),
		        "… and once the back-off has passed it is built and used");
		client_close(&fc);
	}

	printf("21. review of 38639d7d: over the rate never evicts, parked FIFO and not first to go, a parked reset is closed\n");
	rate_reset(p);
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (client_active(&p->clients[i]))
			client_close(&p->clients[i]);
	{
		static int fds21[MAX_CLIENTS + 8];
		int n21 = 0, x, nk;
		const char *who = NULL;
		client *px = NULL;
		uint64_t now = log_now_ms();

		/* a) X over its rate parks FIRST (the oldest), then 127 silent
		 *    in-rate connects fill the table */
		while (rate_take(p, "[127.0.7.1]", NULL, now, &who))
			;
		x = connect_from(port, "127.0.7.1", 0);
		pump(p, 2);
		for (int i = 0; i < MAX_CLIENTS - 1; i++) {
			snprintf(src, sizeof src, "127.0.8.%d", i + 1);
			rate_reset(p);
			/* X stays over its rate (the parked are served first now) */
			while (rate_take(p, "[127.0.7.1]", NULL, log_now_ms(), &who))
				;
			fds21[n21++] = connect_from(port, src, 0);
			pump(p, 1);
		}
		pump(p, 2);
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]) && strcmp(p->clients[i].key, "[127.0.7.1]") == 0)
				px = &p->clients[i];
		require(px && px->phase == F_RATE && active(p) == MAX_CLIENTS,
		        "a parked connection (the oldest) + 127 silent ones fill the table");
		/* b) an arrival OVER its rate with the table full: refused, nobody evicted */
		{
			uint64_t before = p->refused_rate_total;
			int y;
			now = log_now_ms();
			while (rate_take(p, "[127.0.9.1]", NULL, now, &who))
				;
			while (rate_take(p, "[127.0.7.1]", NULL, log_now_ms(), &who))
				; /* X still over its rate */
			y = connect_from(port, "127.0.9.1", 0);
			pump(p, 3);
			require(p->refused_rate_total == before + 1 && client_of(p, "[127.0.9.1]") == 0 &&
			                closed_by_server(y) && active(p) == MAX_CLIENTS &&
			                client_of(p, "[127.0.7.1]") == 1,
			        "over its rate with the table full: refused at accept, nobody evicted (on 38639d7d it evicted and parked)");
			close(y);
			/* … and refused for the SHARED bucket: every bucket in use,
			 * the overflow drained */
			now = log_now_ms();
			for (int i = 0; i < PAGE_RATE_KEYS; i++) {
				char k[32];
				snprintf(k, sizeof k, "[10.8.%d.%d]", i / 250, i % 250);
				rate_take(p, k, NULL, now, &who);
			}
			while (rate_take(p, "[127.0.9.3]", NULL, now, &who))
				;
			before = p->refused_rate_total;
			while (rate_take(p, "[127.0.7.1]", NULL, log_now_ms(), &who))
				;
			y = connect_from(port, "127.0.9.4", 0);
			pump(p, 3);
			require(p->refused_rate_total == before + 1 && closed_by_server(y) &&
			                strncmp(p->refused_last, "(the shared overflow bucket", 27) == 0 &&
			                active(p) == MAX_CLIENTS,
			        "a new address over the SHARED bucket, table full: refused, named as the shared bucket, nobody evicted");
			close(y);
			rate_reset(p);
		}
		usleep((PAGE_YOUNG_MS + 100) * 1000); /* the 127 out of their first second */
		/* c) an arrival WITHIN its rate evicts a silent one, not the parked
		 *    one although it is the oldest */
		{
			int z;
			rate_reset(p);
			while (rate_take(p, "[127.0.7.1]", NULL, log_now_ms(), &who))
				;
			z = connect_from(port, "127.0.9.2", 0);
			pump(p, 3);
			require(client_of(p, "[127.0.9.2]") == 1 && client_of(p, "[127.0.7.1]") == 1 &&
			                active(p) == MAX_CLIENTS,
			        "an arrival within its rate evicts a SILENT one, never the parked (on 38639d7d: the parked, the oldest)");
			fds21[n21++] = z;
		}
		/* d) the parked peer resets: closed at once (its descriptor would
		 *    report POLLERR/POLLHUP at every poll) */
		{
			struct linger lg = {1, 0};
			setsockopt(x, SOL_SOCKET, SO_LINGER, &lg, sizeof lg);
			close(x);
			pump(p, 3);
			require(client_of(p, "[127.0.7.1]") == 0,
			        "a parked connection whose peer resets is closed (on 38639d7d it stayed, and the loop spun)");
		}
		page_expired(p, log_now_ms() + PAGE_REQUEST_MS + 1);
		for (int i = 0; i < n21; i++)
			close(fds21[i]);
		pump(p, 4);

		/* e) FIFO: A parks before B, B in a LOWER slot, one shared token:
		 *    A goes first */
		{
			int fc_, fa, fb;
			client *ca = NULL, *cb = NULL;
			rate_reset(p);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]))
					client_close(&p->clients[i]);
			fc_ = connect_from(port, "127.0.10.1", 0); /* C: a lower slot, TLS */
			pump(p, 2);
			now = log_now_ms();
			for (int i = 0; i < PAGE_RATE_KEYS; i++) {
				char k[32];
				snprintf(k, sizeof k, "[10.9.%d.%d]", i / 250, i % 250);
				rate_take(p, k, NULL, now, &who); /* every bucket in use */
			}
			while (rate_take(p, "[127.0.10.2]", NULL, now, &who))
				; /* the shared overflow drained */
			fa = connect_from(port, "127.0.10.2", 0);
			pump(p, 2);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]) &&
				    strcmp(p->clients[i].key, "[127.0.10.1]") == 0)
					client_close(&p->clients[i]); /* C's slot, lower, freed */
			fb = connect_from(port, "127.0.10.3", 0);
			pump(p, 2);
			nk = 0;
			for (size_t i = 0; i < MAX_CLIENTS; i++) {
				client *q = &p->clients[i];
				if (!client_active(q))
					continue;
				if (strcmp(q->key, "[127.0.10.2]") == 0)
					ca = q;
				if (strcmp(q->key, "[127.0.10.3]") == 0)
					cb = q;
			}
			nk = ca && cb && ca->phase == F_RATE && cb->phase == F_RATE && cb < ca;
			p->rate_over.milli = 1000u; /* one token, shared */
			p->rate_over.at = now;
			page_expired(p, now);
			require(nk && ca->phase == F_HANDSHAKE && cb->phase == F_RATE,
			        "two parked on the shared bucket, the later in a lower slot: one token → the EARLIER goes (on 38639d7d: slot order)");
			close(fc_);
			close(fa);
			close(fb);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]))
					client_close(&p->clients[i]);
			rate_reset(p);
		}
		/* f) the 503 blames the address only when ITS bucket refused */
		{
			static client f5;
			const char *bodies[2] = {NULL, NULL};
			for (int sh = 0; sh < 2; sh++) {
				memset(&f5, 0, sizeof f5);
				f5.fd = -1;
				f5.phase = F_READ;
				f5.busy = true;
				f5.busy_shared = sh;
				snprintf(f5.provenance, sizeof f5.provenance, "[127.0.0.85]:40000");
				f5.nrequest = (size_t)snprintf(f5.request, sizeof f5.request,
				                               "GET /fingerprint HTTP/1.1\r\nHost: t\r\n\r\n");
				serve(p, &f5);
				bodies[sh] = f5.head && memmem(f5.head, f5.nhead, "from this address", 17)
				             ? "address" : f5.head && memmem(f5.head, f5.nhead, "right now", 9)
				             ? "shared" : "?";
				client_close(&f5);
			}
			require(strcmp(bodies[0], "address") == 0 && strcmp(bodies[1], "shared") == 0,
			        "the 503 says «from this address» only when that address's bucket refused");
		}
	}

	printf("22. review of fc76de93: young ranks with parked, parked before newcomers, refused-full refunds, a reused descriptor\n");
	rate_reset(p);
	for (size_t i = 0; i < MAX_CLIENTS; i++)
		if (client_active(&p->clients[i]))
			client_close(&p->clients[i]);
	{
		const char *who = NULL;
		uint64_t now = log_now_ms();

		/* a) the tiers: a connection in its first PAGE_YOUNG_MS ranks with
		 *    the parked, an older silent one below them */
		{
			static client y, o, k;
			y.phase = o.phase = F_HANDSHAKE;
			k.phase = F_RATE;
			y.born = now - 100;
			o.born = now - PAGE_YOUNG_MS - 100;
			k.born = now - 5000;
			require(tier(&y, now) == 1 && tier(&k, now) == 1 && tier(&o, now) == 0,
			        "young without a reply ranks with the parked (1), an older silent one below (0) — on fc76de93 the young owner was 0");
		}
		/* b) the parked first: A parked on the shared bucket, one token
		 *    comes, newcomer B arrives in the same pass — A gets it */
		{
			int fa, fb;
			client *ca = NULL, *cb = NULL;
			now = log_now_ms();
			for (int i = 0; i < PAGE_RATE_KEYS; i++) {
				char kk[32];
				snprintf(kk, sizeof kk, "[10.7.%d.%d]", i / 250, i % 250);
				rate_take(p, kk, NULL, now, &who);
			}
			while (rate_take(p, "[127.0.11.9]", NULL, now, &who))
				;
			fa = connect_from(port, "127.0.11.1", 0);
			pump(p, 2);
			p->rate_over.milli = 1000u;
			p->rate_over.at = log_now_ms();
			fb = connect_from(port, "127.0.11.2", 0);
			pump(p, 2);
			for (size_t i = 0; i < MAX_CLIENTS; i++) {
				client *q = &p->clients[i];
				if (!client_active(q))
					continue;
				if (strcmp(q->key, "[127.0.11.1]") == 0)
					ca = q;
				if (strcmp(q->key, "[127.0.11.2]") == 0)
					cb = q;
			}
			require(ca && cb && ca->phase == F_HANDSHAKE && cb->phase == F_RATE,
			        "a newcomer on the shared bucket waits behind the parked one (on fc76de93 it took the token first)");
			close(fa);
			close(fb);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]))
					client_close(&p->clients[i]);
			rate_reset(p);
		}
		/* c) refused because the table is full: its token given back */
		{
			static int f22[MAX_CLIENTS];
			int n22 = 0, again;
			struct bucket *b;
			for (int i = 0; i < MAX_CLIENTS; i++) {
				snprintf(src, sizeof src, "127.0.12.%d", i + 1);
				rate_reset(p);
				f22[n22++] = connect_from(port, src, 0);
				pump(p, 1);
			}
			pump(p, 2);
			rate_reset(p);
			again = connect_from(port, "127.0.12.1", 0); /* its group would hold 2 */
			pump(p, 3);
			b = &p->rate_over;
			for (int i = 0; i < PAGE_RATE_KEYS; i++)
				if (strcmp(p->rate[i].key, "[127.0.12.1]") == 0)
					b = &p->rate[i];
			require(active(p) == MAX_CLIENTS && closed_by_server(again) &&
			                b != &p->rate_over && b->milli == PAGE_ACCEPT_BURST * 1000u,
			        "refused as full after its rate check: the token is refunded (on fc76de93 it was spent)");
			close(again);
			page_expired(p, log_now_ms() + PAGE_REQUEST_MS + 1);
			for (int i = 0; i < n22; i++)
				close(f22[i]);
			pump(p, 4);
			rate_reset(p);
		}
		/* d) a descriptor closed and reused within ONE page_move() call:
		 *    the old owner's POLLHUP is not applied to the newcomer */
		{
			int fp, fn, x = -1;
			client *cp = NULL, *cn = NULL;
			struct pollfd f[2];
			fp = connect_from(port, "127.0.13.1", 0);
			pump(p, 2);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]) &&
				    strcmp(p->clients[i].key, "[127.0.13.1]") == 0)
					cp = &p->clients[i];
			if (cp)
				client_close(cp); /* its descriptor number is free again */
			now = log_now_ms();
			while (rate_take(p, "[127.0.13.2]", NULL, now, &who))
				; /* the newcomer will park: a parked one reacts to POLLHUP */
			fn = connect_from(port, "127.0.13.2", 0);
			/* the number accept4() will give the newcomer: the lowest free */
			x = dup(0);
			if (x >= 0)
				close(x);
			f[0] = (struct pollfd){.fd = p->fd, .events = POLLIN, .revents = POLLIN};
			f[1] = (struct pollfd){.fd = x, .events = 0, .revents = POLLHUP};
			p->move_next = 0;
			page_move(p, f, 2);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]) &&
				    strcmp(p->clients[i].key, "[127.0.13.2]") == 0)
					cn = &p->clients[i];
			require(x >= 0 && cn && cn->fd == x && cn->phase == F_RATE,
			        "the newcomer took the freed descriptor number and is parked, untouched by the old owner's POLLHUP (on fc76de93: closed)");
			close(fp);
			close(fn);
			for (size_t i = 0; i < MAX_CLIENTS; i++)
				if (client_active(&p->clients[i]))
					client_close(&p->clients[i]);
			rate_reset(p);
		}
	}

	rcp_unblock("127.0.0.50", log_now_ms());
	rcp_ban_load(NULL, log_now_ms());
	unlink(ban_path);

	page_close(p);
	unlink(html_path);
	printf("%d passed, %d failed, of %d\n", passed, failures, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
