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
 *   2. 32 idle connections from 8 addresses fill the table;
 *   3. a 33rd from a new address evicts the oldest idle one, and gets in;
 *   4. page_wait_ms() says the next deadline is within a second;
 *   5. page_expired(now + 10 s) closes every idle connection, and their
 *      sockets see the close;
 *   6. a real HTTPS GET / then gets the page (200, the markers replaced);
 *   7. a client that sent its request but stopped reading the response is
 *      NOT closed at 10 s, and IS closed 15 s after the last byte it
 *      acknowledged — and progress is what it acknowledged, not what the
 *      kernel's send buffer swallowed;
 *   8. the progress deadline (review of 3ed5091f): a phone that took 300 KB
 *      in 60 s (5 KB/s) is kept, one that took 100 KB (1.7 KB/s) is closed;
 *   9. 32 slow readers from 8 addresses hold every slot in F_WRITE: a new
 *      client is refused while they are young, and once they are older than
 *      5 s and slower than 32 KB/s one of them is evicted and a real GET
 *      gets the page;
 *  10. the IPv6 /48 of PAGE_PER_48 is taken only from real IPv6 peers;
 *  11. the bytes left of the eviction ranking never wrap below zero.
 *
 * Exit status: 0 green, 1 red, 3 not all checks ran. */
#define _GNU_SOURCE
#include "page.c"

#include <arpa/inet.h>
#include <openssl/evp.h>
#include <openssl/x509.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 27

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

/* Pumps until `want` clients are in F_WRITE (3 s at most); returns the last
 * one, or NULL. */
static client *writer_wait(page *p, int want)
{
	uint64_t t0 = log_now_ms();
	while (log_now_ms() - t0 < 3000) {
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
 * or sleep without reading (the slow reader). */
static pid_t client_get(int port, const char *src, bool read_all)
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
	_exit(strncmp(b, "HTTP/1.1 200 ", 13) == 0 && strstr(b, "data-banned=\"no\"") &&
	              strstr(b, "FPTEST") && !strstr(b, "__FINGERPRINT__")
	              ? 0 : 12);
}

int main(void)
{
	char html_path[] = "/tmp/pdt-page-XXXXXX";
	int hfd = mkstemp(html_path);
	FILE *h = fdopen(hfd, "w");
	certificates cert;
	/* ~16 MB: far beyond what loopback buffers hold, so the slow reader of
	 * check 7 really stays in F_WRITE. */
	fprintf(h, "<html><body data-banned=\"__BANNED__\" data-remaining-ms=\""
	           "__REMAINING_MS__\" data-diary=\"__DIARY__\">__FINGERPRINT__ "
	           "__WARNING__<!--");
	for (int i = 0; i < 16 * 1024; i++)
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
	int fds[40], nf = 0;
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

	printf("2. 32 idle from 8 addresses fill the table\n");
	for (int a = 2; a <= 8; a++)
		for (int i = 0; i < 4; i++) {
			snprintf(src, sizeof src, "127.0.0.%d", a);
			fds[nf++] = connect_from(port, src, 0);
			pump(p, 1);
		}
	pump(p, 3);
	require(active(p) == 32, "32 clients active");

	printf("3. a 33rd from a new address evicts the oldest idle one\n");
	fds[nf++] = connect_from(port, "127.0.0.9", 0);
	pump(p, 3);
	require(active(p) == 32, "still 32 active (one out, one in)");
	require(p->evicted == 1, "one eviction counted");
	require(closed_by_server(fds[0]), "the oldest (first from 127.0.0.1) was closed");

	printf("4. the loop is woken for the deadline\n");
	{
		int w = page_wait_ms(p, log_now_ms());
		require(w >= 0 && w <= 1000, "page_wait_ms() within [0, 1000]");
	}

	printf("5. 10 s later every idle connection is closed\n");
	page_expired(p, log_now_ms() + PAGE_REQUEST_MS - 1000);
	require(active(p) == 32, "nobody closed 1 s before the deadline");
	page_expired(p, log_now_ms() + PAGE_REQUEST_MS + 1);
	require(active(p) == 0, "all 32 closed after the deadline");
	{
		int seen = 0;
		for (int i = 1; i < nf; i++)
			seen += closed_by_server(fds[i]);
		require(seen == nf - 1, "every idle socket saw the close");
	}
	for (int i = 0; i < nf; i++)
		close(fds[i]);

	printf("6. a real HTTPS GET gets the page\n");
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

	printf("7. a slow reader is held to the progress deadline, not the 10 s one\n");
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
			page_expired(p, w->last_progress + PAGE_STALL_MS - 1);
			require(active(p) == 1, "not closed 1 ms before 15 s without progress");
			page_expired(p, w->last_progress + PAGE_STALL_MS + 1);
			require(active(p) == 0, "closed 15 s after the last byte taken");
		}
		kill(c, SIGKILL);
		waitpid(c, NULL, 0);
	}

	printf("8. the progress deadline keeps a slow phone that keeps reading\n");
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
			require(active(p) == 1, "300 KB in 60 s, last byte 1 s ago: kept (the old rule cut it at 60 s)");
			w->delivered = 100000;
			page_expired(p, t);
			require(active(p) == 0, "100 KB in 60 s (under 2 KB/s): closed");
		}
		kill(c, SIGKILL);
		waitpid(c, NULL, 0);
	}

	printf("9. 32 slow readers cannot lock the page out\n");
	{
		pid_t kids[32];
		int k = 0, fd, others = 0;
		for (int a = 1; a <= 8; a++)
			for (int i = 0; i < 4; i++) {
				snprintf(src, sizeof src, "127.0.0.%d", a);
				kids[k++] = client_get(port, src, false);
				pump(p, 2);
			}
		require(writer_wait(p, 32) != NULL, "all 32 slots are slow readers in F_WRITE");
		fd = connect_from(port, "127.0.0.9", 0);
		pump(p, 3);
		require(closed_by_server(fd) && active(p) == 32,
		        "a newcomer while they are younger than 5 s is refused");
		close(fd);
		for (size_t i = 0; i < MAX_CLIENTS; i++) {
			p->clients[i].write_start -= PAGE_EVICT_AGE_MS + 1000;
			p->clients[i].born -= PAGE_EVICT_AGE_MS + 1000;
		}
		{
			pid_t c = client_get(port, "127.0.0.9", true);
			int st = -1;
			uint64_t t0 = log_now_ms();
			while (waitpid(c, &st, WNOHANG) == 0 && log_now_ms() - t0 < 20000) {
				pump(p, 1);
				page_expired(p, log_now_ms());
			}
			require(WIFEXITED(st) && WEXITSTATUS(st) == 0,
			        "once they are 6 s old and slow, a real GET gets the page");
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			others += client_active(&p->clients[i]) &&
			          strcmp(p->clients[i].key, "[127.0.0.9]") != 0;
		require(others == 31, "exactly one slow reader was evicted for it");
		for (int i = 0; i < k; i++) {
			kill(kids[i], SIGKILL);
			waitpid(kids[i], NULL, 0);
		}
		for (size_t i = 0; i < MAX_CLIENTS; i++)
			if (client_active(&p->clients[i]))
				client_close(&p->clients[i]);
	}

	printf("10. the /48 is taken only from real IPv6 peers\n");
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
	}

	printf("11. bytes left never wraps below zero\n");
	{
		client a, b;
		memset(&a, 0, sizeof a);
		memset(&b, 0, sizeof b);
		a.nresponse = 1000;
		a.delivered = 1040; /* TLS overhead acknowledged past the plaintext */
		b.nresponse = 1000;
		b.delivered = 100;
		require(bytes_left(&a) == 0 && bytes_left(&b) == 900 &&
		                bytes_left(&b) > bytes_left(&a),
		        "delivered > nresponse gives 0 left, and ranks below a client with 900 left");
	}

	page_close(p);
	unlink(html_path);
	printf("%d passed, %d failed, of %d\n", passed, failures, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
