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
 *       -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm \
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

#define malloc(n) t_malloc(n)
#define free(q) t_free(q)
#include "page.c"
#undef malloc
#undef free

#include <arpa/inet.h>
#include <openssl/evp.h>
#include <openssl/x509.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 64

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
	              !strstr(b, "__BANNED__") && !strstr(b, "__REMAINING_MS__") &&
	              !strstr(b, "__DIARY__");
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
	           "__REMAINING_MS__\" data-diary=\"__DIARY__\">__FINGERPRINT__ "
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
	{
		uint64_t first = UINT64_MAX;
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]) && p->clients[i].born < first)
				first = p->clients[i].born;
		page_expired(p, first + PAGE_REQUEST_MS - 1);
	}
	require(active(p) == MAX_CLIENTS, "nobody closed 1 ms before the first deadline");
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
		require(nb == 2 && ban_w[0]->shared && ban_w[1]->shared &&
		                ban_w[0]->shared != p->cached && ban_w[1]->shared != p->cached &&
		                ban_w[0]->shared != ban_w[1]->shared &&
		                ban_w[0]->shared->refs == 1 && ban_w[1]->shared->refs == 1,
		        "each banned request has its own body (refs 1), never the shared page");
		require(nb == 2 && body_has(ban_w[0]->shared, "data-banned=\"yes\"") &&
		                body_has(ban_w[0]->shared, "<b>attempts exhausted</b>") &&
		                body_has(ban_w[0]->shared, "<b id=\"minutes\">30</b>") &&
		                !body_has(ban_w[0]->shared, "data-remaining-ms=\"0\"") &&
		                !body_has(ban_w[0]->shared, "__REMAINING_MS__"),
		        "the banned body says «attempts exhausted», 1 h 30 min, its remaining ms");
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
		require(nlive == live0 && !live_overflow && p->cached == shared0 && shared0->refs == 1,
		        "closing them frees both banned bodies; the shared page is held by the listener alone");
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
		                strcmp(p->cached_fp, "FPTEST") == 0 && nlive == live0,
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
		require(fc.phase == F_WRITE && fc.shared && fc.shared != p->cached &&
		                fc.shared->refs == 1 && body_has(fc.shared, "data-banned=\"yes\"") &&
		                strncmp(fc.head, "HTTP/1.1 200 ", 13) == 0 && n_ban >= 2,
		        "driven directly, a banned GET gets its own 200 page");
		client_close(&fc);
		page_mallocs = 0;
		fake_get(p, &fc, "[127.0.0.51]:40000");
		n_free = page_mallocs;
		require(fc.shared == shared0 && shared0->refs == 2 && n_free == 1,
		        "a free GET with the page cached allocates only its head");
		client_close(&fc);
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
		require(fc.shared && fc.shared == p->cached && fc.shared != shared0 &&
		                strcmp(p->cached_fp, "FPROT") == 0 && body_has(fc.shared, "FPROT") &&
		                n_reb == n_ban,
		        "after a rotation a free GET rebuilds the shared page (as many allocations as a banned one)");
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
		for (size_t k = 1; k < n_reb; k++) {
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
		require(ok500 == (int)(n_reb - 1),
		        "rotation, the rebuild fails: the 500 «no mem.», never the old page under the new fingerprint");
		require(okleak == (int)(n_reb - 1) && okshared == (int)(n_reb - 1),
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
