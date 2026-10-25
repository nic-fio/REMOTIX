/*
 * test.c — EIGHT USERS BEHIND ONE ADDRESS load the page together, with the REAL page.c (margins of 1.5; replaces the estimate of `otto-utenti-nat`).
 *
 * `otto-utenti-nat` models the page with pagebucket.h and the numbers of page.c.  This test drives the REAL accept path of page.c: a listening page, real
 * TCP connections from one source address (the NAT), and the real counters of the page.  No full build is needed: page.c is #included, rcp.c and the log
 * stubs are linked (rcp_key_address, rcp_banned...), and the rest is a trapping stub that must never be reached.
 *
 *   1. 8 users x 1, x 2 and x 3 connections at the same instant (8, 16, 24 connections from one address): all of them are accepted, NONE is parked, NONE is
 *      served «busy», nothing is refused (the cap per address and the accept bucket are both far from their limits);
 *   2. PAGE_PER_ADDRESS connections at once (the cap): all accepted and none parked (the burst of the accept bucket covers it); the NEXT one is closed by
 *      the server — the cap holds, and it is the declared one;
 *   3. a SECOND reload one second after the first (the first sockets closed): 24 more connections; the bucket has refilled 8 tokens, so some wait, and
 *      every one is served within PAGE_RATE_WAIT_MS — none is «busy»;
 *   4. the bucket really limits: after the burst is spent, the next connections from the address are parked (so the limit is real and this test could
 *      have failed).
 *
 * The time is the real clock (the page uses real_ms()): the test takes about ten seconds.
 *
 * BUILD AND RUN (a few seconds to build; from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter -I/albero/src -I/albero/benches/fuzz/rcp-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm -lssl -lcrypto -lz" &&
 *     clang $F -c /albero/benches/unit/page-otto-utenti/test.c -o t.o && clang $F -c /albero/src/rcp.c -o r.o && clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o r.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o r.o l.o s.o $L -o test && cd /albero && ASAN_OPTIONS=detect_leaks=0 /tmp/test'   (the SSL objects of the test certificate are not freed)
 */
#include "page.h"
#include "rcp.h"
#include "log.h"
#include <arpa/inet.h>
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
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/x509.h>
#include <zlib.h>
#include "page.c"

#include <signal.h>
#include <time.h>

extern uint64_t rx_now_ms; /* the fake clock of benches/fuzz/rcp-msg/stubs_log.c: the page reads it through real_ms() — here it follows the REAL clock */

static uint64_t real_ms(void)
{
	struct timespec ts;

	clock_gettime(CLOCK_MONOTONIC, &ts);
	rx_now_ms = (uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u;
	return rx_now_ms;
}

static int failures, checks;
static void require(int cond, const char *desc)
{
	checks++;
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (!cond)
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

static int parked(page *p)
{
	int n = 0;

	for (size_t i = 0; i < MAX_CLIENTS; i++)
		n += client_active(&p->clients[i]) && p->clients[i].phase == F_RATE;
	return n;
}

static int busy_served(page *p)
{
	int n = 0;

	for (size_t i = 0; i < MAX_CLIENTS; i++)
		n += client_active(&p->clients[i]) && p->clients[i].busy;
	return n;
}

static void pump(page *p, int passes)
{
	for (int k = 0; k < passes; k++) {
		struct pollfd f[MAX_CLIENTS + 1];
		size_t n = page_descriptors(p, f, MAX_CLIENTS + 1);

		if (poll(f, n, 20) > 0)
			page_move(p, f, n);

	}
}

static int connect_from(int port, const char *src)
{
	struct sockaddr_in a = {.sin_family = AF_INET};
	int fd = socket(AF_INET, SOCK_STREAM, 0);

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
	static SSL_CTX *cached; /* one context for every page of the test (no leak per fresh page) */
	SSL_CTX *ctx;

	if (cached)
		return cached;
	ctx = SSL_CTX_new(TLS_server_method());
	EVP_PKEY *k = EVP_EC_gen("P-256");
	X509 *x = X509_new();

	X509_set_version(x, 2);
	ASN1_INTEGER_set(X509_get_serialNumber(x), 1);
	X509_gmtime_adj(X509_getm_notBefore(x), 0);
	X509_gmtime_adj(X509_getm_notAfter(x), 3600);
	X509_set_pubkey(x, k);
	X509_NAME_add_entry_by_txt(X509_get_subject_name(x), "CN", MBSTRING_ASC, (const unsigned char *)"test", -1, -1, 0);
	X509_set_issuer_name(x, X509_get_subject_name(x));
	X509_sign(x, k, EVP_sha256());
	if (!ctx || !k || SSL_CTX_use_certificate(ctx, x) != 1 || SSL_CTX_use_PrivateKey(ctx, k) != 1) {
		fprintf(stderr, "cannot make the test certificate\n");
		exit(3);
	}
	cached = ctx;
	return ctx;
}

/* a fresh page (a restarted server): the buckets are full */
static page *fresh_page(char *html_path, certificates *cert)
{
	page *p = page_open("127.0.0.1", "0", server_ctx(), html_path, cert);

	if (!p) {
		fprintf(stderr, "page_open failed\n");
		exit(3);
	}
	return p;
}

static void closeall(int *fds, int *n)
{
	for (int i = 0; i < *n; i++)
		close(fds[i]);
	*n = 0;
}

int main(void)
{
	char html_path[] = "/tmp/pot-page-XXXXXX";
	int hfd = mkstemp(html_path);
	FILE *h = fdopen(hfd, "w");
	certificates cert;
	static int fds[256];
	int nf = 0;

	fprintf(h, "<html><body data-banned=\"__BANNED__\" data-remaining-ms=\"__REMAINING_MS__\">__FINGERPRINT__ __WARNING__</body></html>\n");
	fclose(h);
	memset(&cert, 0, sizeof cert);
	snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPTEST");
	snprintf(cert.fingerprint_hex, sizeof cert.fingerprint_hex, "00");
	signal(SIGPIPE, SIG_IGN);
	setvbuf(stdout, NULL, _IONBF, 0);

	printf("limits of page.c: accept %d a second burst %d, wait %u ms, %d connections per address, %d slots\n", PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST,
	       PAGE_RATE_WAIT_MS, PAGE_PER_ADDRESS, MAX_CLIENTS);

	/* 1. eight users with 1, 2, 3 connections at the same instant, after a restart */
	for (int conns = 1; conns <= 3; conns++) {
		page *p = fresh_page(html_path, &cert);
		int port = port_of(p), want = 8 * conns;
		char what[160];

		for (int i = 0; i < want; i++)
			fds[nf++] = connect_from(port, "127.0.0.1");
		pump(p, 12);
		snprintf(what, sizeof what, "8 users x %d connection(s) = %d at once from one address: all %d accepted", conns, want, want);
		require(active(p) == want, what);
		require(parked(p) == 0 && p->delayed_rate_total == 0, "none is parked (the burst of the accept bucket covers them)");
		require(busy_served(p) == 0 && p->refused_rate_total == 0, "none is served «busy» and none is refused by the rate");
		require(!p->refused_ever, "nothing was refused (the cap per address is far away)");
		closeall(fds, &nf);
		pump(p, 4);
		page_close(p);
	}

	/* 2. the cap per address */
	{
		page *p = fresh_page(html_path, &cert);
		int port = port_of(p);

		for (int i = 0; i < PAGE_PER_ADDRESS + 1; i++) {
			fds[nf++] = connect_from(port, "127.0.0.1");
			if (i % 8 == 7)
				pump(p, 2);
		}
		pump(p, 12);
		require(active(p) == PAGE_PER_ADDRESS, "PAGE_PER_ADDRESS connections at once are all accepted");
		require(parked(p) == 0 && p->delayed_rate_total == 0 && busy_served(p) == 0, "…none parked, none «busy»");
		require(closed_by_server(fds[PAGE_PER_ADDRESS]), "the next one is closed by the server: the cap holds");
		closeall(fds, &nf);
		pump(p, 4);
		page_close(p);
	}

	/* 3. a second reload one second later */
	{
		page *p = fresh_page(html_path, &cert);
		int port = port_of(p);
		uint64_t t0;

		for (int i = 0; i < 24; i++)
			fds[nf++] = connect_from(port, "127.0.0.1");
		pump(p, 12);
		require(active(p) == 24 && parked(p) == 0, "first reload: 24 connections, none parked");
		closeall(fds, &nf);
		pump(p, 6);
		t0 = real_ms();
		while (real_ms() - t0 < 1000)
			pump(p, 1);
		for (int i = 0; i < 24; i++)
			fds[nf++] = connect_from(port, "127.0.0.1");
		pump(p, 12);
		require(active(p) == 24, "second reload one second later: all 24 accepted");
		/* the bucket had 32 - 24 = 8 left + about 8 refilled in 1 s = about 16: some of the 24 may wait for a token, but none past the wait */
		t0 = real_ms();
		while (real_ms() - t0 < (uint64_t)PAGE_RATE_WAIT_MS + 1000 && parked(p) > 0)
			pump(p, 1);
		require(parked(p) == 0, "…and every one that waited got its token within the wait");
		require(busy_served(p) == 0 && p->refused_rate_total == 0, "…none is served «busy»");
		closeall(fds, &nf);
		pump(p, 4);
		page_close(p);
	}

	/* 4. the bucket is real: after the whole burst is spent (and the sockets closed, so the cap is free), 16 more at once are NOT all served at once */
	{
		page *p = fresh_page(html_path, &cert);
		int port = port_of(p);

		for (int i = 0; i < PAGE_ACCEPT_BURST; i++)
			fds[nf++] = connect_from(port, "127.0.0.1");
		pump(p, 12);
		require(active(p) == PAGE_ACCEPT_BURST && parked(p) == 0, "the whole burst of the bucket is taken at once");
		closeall(fds, &nf);
		pump(p, 6);
		for (int i = 0; i < 16; i++)
			fds[nf++] = connect_from(port, "127.0.0.1");
		pump(p, 6);
		require(parked(p) > 0 && p->delayed_rate_total > 0, "with the bucket empty the next ones are PARKED: the limit is real");
		closeall(fds, &nf);
		pump(p, 4);
		page_close(p);
	}

	remove(html_path);
	printf("%d checks, %d failed\n", checks, failures);
	return failures ? 1 : 0;
}
