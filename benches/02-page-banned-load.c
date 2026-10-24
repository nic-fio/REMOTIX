/* 02-page-banned-load.c — what banned visitors cost the main loop
 * (holistic review, 15 Oct 2026: a banned GET rebuilt the whole ~907 KB page,
 * 3.2 ms of CPU each; 32 banned addresses × 4 froze the loop for 522 ms).
 *
 * The real `src/page.html`, the real listener (`page_open`, `page_descriptors`,
 * `poll`, `page_move`, `page_expired`, as main.c's loop), only the public API
 * of page.h — so the SAME file measures the page.c before and after.  For
 * DURATION seconds:
 *   · 128 attackers (4 processes from each of 32 BANNED addresses
 *     127.0.0.100-131), nice 19, each in a loop: connect, TLS, `GET /` (half
 *     with `Accept-Encoding: gzip`), read the whole answer, close;
 *   · one probe from 127.0.0.250 (not banned), every 300 ms: connect, TLS,
 *     `GET /fingerprint`, read it: its latency, connect to last byte;
 *   · the parent runs the loop and times every page_move() call.
 * It prints the attackers' completed GETs, the probe's latencies (median,
 * 95th, max, failures) and the loop's page_move() time (max, total), wall
 * clock and the loop thread's own CPU time (the attackers share the CPUs).
 *
 * In the build container, from src/ (after make TWIN=none):
 *   gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags gio-2.0 libpipewire-0.3 \
 *       libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon wayland-client gbm) \
 *       -o /tmp/pbl ../benches/02-page-banned-load.c $(ls *.o | grep -v '^main.o$') \
 *       -lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
 *       $(pkg-config --libs gio-2.0 libpipewire-0.3 libva libva-drm libei-1.0 \
 *       xkbcommon wayland-client gbm opus vulkan) -ldl && /tmp/pbl page.html
 *
 * A measurement, not a test: exit 0 when it ran, 3 when it could not. */
#define _GNU_SOURCE
#include "page.h"
#include "rcp.h"
#include "log.h"
#include "certificates.h"

#include <arpa/inet.h>
#include <errno.h>
#include <netinet/in.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include <openssl/evp.h>
#include <openssl/ssl.h>
#include <openssl/x509.h>

#define DURATION_MS 8000u
#define ADDRESSES 32
#define PER_ADDRESS 4
#define PROBES 70

static uint64_t now_us(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t)ts.tv_sec * 1000000u + (uint64_t)ts.tv_nsec / 1000u;
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
	    SSL_CTX_use_PrivateKey(ctx, k) != 1)
		return NULL;
	return ctx;
}

/* One GET from `src`: the bytes read, or -1. */
static long get_once(SSL_CTX *ctx, int port, const char *src, const char *req)
{
	struct sockaddr_in a = {.sin_family = AF_INET};
	int fd = socket(AF_INET, SOCK_STREAM, 0);
	long total = -1;
	SSL *s;
	char b[65536];

	struct timeval tv = {.tv_sec = 3};
	setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
	setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof tv);
	inet_pton(AF_INET, src, &a.sin_addr);
	if (bind(fd, (struct sockaddr *)&a, sizeof a) != 0) {
		close(fd);
		return -1;
	}
	inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
	a.sin_port = htons((uint16_t)port);
	if (connect(fd, (struct sockaddr *)&a, sizeof a) != 0) {
		close(fd);
		return -1;
	}
	s = SSL_new(ctx);
	SSL_set_fd(s, fd);
	if (SSL_connect(s) == 1 && SSL_write(s, req, (int)strlen(req)) > 0) {
		int r;
		total = 0;
		while ((r = SSL_read(s, b, sizeof b)) > 0)
			total += r;
		if (total == 0)
			total = -1;
	}
	SSL_free(s);
	close(fd);
	return total;
}

static uint64_t cpu_us(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
	return (uint64_t)ts.tv_sec * 1000000u + (uint64_t)ts.tv_nsec / 1000u;
}

static int cmp_u64(const void *x, const void *y)
{
	uint64_t a = *(const uint64_t *)x, b = *(const uint64_t *)y;
	return a < b ? -1 : a > b;
}

int main(int argc, char **argv)
{
	certificates cert;
	char ban_path[] = "/tmp/pbl-ban-XXXXXX";
	FILE *bf;
	int port, bfd;
	/* the attackers' counts, in shared memory: read after they are killed */
	long *counts = mmap(NULL, 2 * sizeof(long) * ADDRESSES * PER_ADDRESS,
	                    PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
	pid_t kids[ADDRESSES * PER_ADDRESS + 1];
	int nk = 0;
	page *p;
	SSL_CTX *sctx;

	if (argc < 2) {
		fprintf(stderr, "usage: %s page.html\n", argv[0]);
		return 3;
	}
	signal(SIGPIPE, SIG_IGN);
	memset(&cert, 0, sizeof cert);
	snprintf(cert.fingerprint, sizeof cert.fingerprint, "FPLOAD");
	snprintf(cert.fingerprint_hex, sizeof cert.fingerprint_hex, "00");
	sctx = server_ctx();
	p = sctx ? page_open("127.0.0.1", "0", sctx, argv[1], &cert) : NULL;
	if (!p) {
		fprintf(stderr, "page_open failed\n");
		return 3;
	}
	{
		struct pollfd f[1];
		struct sockaddr_in a;
		socklen_t l = sizeof a;
		page_descriptors(p, f, 1);
		getsockname(f[0].fd, (struct sockaddr *)&a, &l);
		port = ntohs(a.sin_port);
	}
	bfd = mkstemp(ban_path);
	bf = fdopen(bfd, "w");
	for (int i = 0; i < ADDRESSES; i++)
		fprintf(bf, "[127.0.0.%d] %lld\n", 100 + i, (long long)time(NULL) + 5400);
	fclose(bf);
	if (rcp_ban_load(ban_path, log_now_ms()) != ADDRESSES) {
		fprintf(stderr, "the bans did not load\n");
		return 3;
	}
	if (counts == MAP_FAILED)
		return 3;

	uint64_t t_end = now_us() + DURATION_MS * 1000u;
	for (int i = 0; i < ADDRESSES * PER_ADDRESS; i++) {
		pid_t k = fork();
		if (k == 0) {
			char src[32];
			SSL_CTX *c = SSL_CTX_new(TLS_client_method());
			const char *req = i % 2 ? "GET / HTTP/1.1\r\nHost: t\r\nAccept-Encoding: gzip\r\n\r\n"
			                        : "GET / HTTP/1.1\r\nHost: t\r\n\r\n";
			if (nice(19) < 0)
				(void)0;
			snprintf(src, sizeof src, "127.0.0.%d", 100 + i / PER_ADDRESS);
			while (now_us() < t_end) {
				if (get_once(c, port, src, req) > 0)
					counts[2 * i]++;
				else
					counts[2 * i + 1]++;
			}
			_exit(0);
		}
		kids[nk++] = k;
	}
	{
		pid_t k = fork();
		if (k == 0) {
			uint64_t lat[PROBES];
			int n = 0, failed = 0;
			SSL_CTX *c = SSL_CTX_new(TLS_client_method());
			usleep(500000); /* the attack running */
			while (n + failed < PROBES && now_us() < t_end) {
				uint64_t t0 = now_us();
				long r = get_once(c, port, "127.0.0.250",
				                  "GET /fingerprint HTTP/1.1\r\nHost: t\r\n\r\n");
				if (r > 0)
					lat[n++] = now_us() - t0;
				else
					failed++;
				usleep(300000); /* under PAGE_ACCEPT_RATE: a visitor, not a flood */
			}
			qsort(lat, (size_t)n, sizeof lat[0], cmp_u64);
			printf("probe: %d answered, %d failed; latency median %.1f ms, 95th %.1f ms, max %.1f ms\n",
			       n, failed, n ? lat[n / 2] / 1000.0 : -1.0,
			       n ? lat[(n * 95) / 100 < n ? (n * 95) / 100 : n - 1] / 1000.0 : -1.0,
			       n ? lat[n - 1] / 1000.0 : -1.0);
			fflush(stdout);
			_exit(0);
		}
		kids[nk++] = k;
	}

	uint64_t move_max = 0, move_total = 0, passes = 0, t_start = now_us();
	uint64_t cpu_max = 0, cpu_total = 0, over20 = 0;
	static uint64_t cpu_each[1 << 20];
	while (now_us() < t_end + 2000000u) {
		struct pollfd f[PAGE_MAX_DESCRIPTORS];
		size_t n = page_descriptors(p, f, PAGE_MAX_DESCRIPTORS);
		if (poll(f, n, 20) > 0) {
			uint64_t t0 = now_us(), c0 = cpu_us(), d, dc;
			page_move(p, f, n);
			d = now_us() - t0;
			dc = cpu_us() - c0;
			cpu_total += dc;
			if (passes < sizeof cpu_each / sizeof cpu_each[0])
				cpu_each[passes] = dc;
			over20 += dc > 20000;
			if (dc > cpu_max)
				cpu_max = dc;
			move_total += d;
			if (d > move_max)
				move_max = d;
			passes++;
		}
		page_expired(p, log_now_ms());
		int st;
		pid_t w;
		while ((w = waitpid(-1, &st, WNOHANG)) > 0)
			nk--;
		if (nk == 0)
			break;
	}
	for (int i = 0; i < ADDRESSES * PER_ADDRESS + 1; i++)
		kill(kids[i], SIGKILL);
	while (waitpid(-1, NULL, 0) > 0)
		;
	{
		long done = 0, failed = 0;
		for (int i = 0; i < ADDRESSES * PER_ADDRESS; i++) {
			done += counts[2 * i];
			failed += counts[2 * i + 1];
		}
		printf("attackers: %d processes from %d banned addresses, %ld GETs answered, %ld refused or failed, in %u s\n",
		       ADDRESSES * PER_ADDRESS, ADDRESSES, done, failed, DURATION_MS / 1000u);
	}
	{
		size_t np = passes < sizeof cpu_each / sizeof cpu_each[0] ? passes
		                                                         : sizeof cpu_each / sizeof cpu_each[0];
		qsort(cpu_each, np, sizeof cpu_each[0], cmp_u64);
		printf("loop: %llu page_move() passes; wall: the longest %.1f ms, %.0f ms in all; "
		       "CPU: the longest %.1f ms, 99th %.1f ms, %llu over 20 ms, %.0f ms in all; over %.1f s\n",
		       (unsigned long long)passes, move_max / 1000.0, move_total / 1000.0,
		       cpu_max / 1000.0, np ? cpu_each[(np * 99) / 100] / 1000.0 : 0.0,
		       (unsigned long long)over20, cpu_total / 1000.0, (now_us() - t_start) / 1e6);
	}
	page_close(p);
	unlink(ban_path);
	return 0;
}
