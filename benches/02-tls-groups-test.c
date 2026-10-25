/*
 * 02-tls-groups-test.c — ⭐ 1.5 (audit R4): the TLS contexts accept only the key-exchange
 *                        groups of `TLS_GROUPS`; `src/tls.c` INCLUDED (its statics reachable).
 *
 * A server SSL made from `tls_page_context()` / `tls_quic_context()` shakes hands IN MEMORY
 * (two BIOs, no network) with a client that offers ONE group: X25519, P-256, P-384 and
 * X25519MLKEM768 must pass; ffdhe2048, ffdhe3072, X448, P-521 must fail.  And `set_groups()`
 * with an unknown name falls back to the list without ML-KEM instead of failing or leaving
 * the OpenSSL defaults.
 *
 *   cd src && make test-tls-groups        (needs `openssl` on the PATH, to make a P-256 certificate)
 *
 * Exit 0 all passed · 1 a check failed · 3 could not look.  Last line: «N passed, M failed».
 */
#include "tls.c"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

#include <openssl/bio.h>

void log_says_in(const char *file, int text_line, const char *area, const char *fmt, ...)
{
	va_list ap;
	(void)file; (void)text_line;
	printf("       [log %s] ", area);
	va_start(ap, fmt);
	vprintf(fmt, ap);
	va_end(ap);
	printf("\n");
}

static int passed, failed;

#define CHECK(cond, ...)                                                   \
	do {                                                               \
		if (cond) {                                                \
			passed++;                                          \
			printf("  ok   ");                                 \
		} else {                                                   \
			failed++;                                          \
			printf("  FAIL ");                                 \
		}                                                          \
		printf(__VA_ARGS__);                                       \
		printf("\n");                                              \
	} while (0)

/* true = the handshake completed on both sides */
static bool shake(SSL_CTX *server_ctx, const char *client_group, const unsigned char *alpn,
                  unsigned int alpnlen)
{
	SSL_CTX *cc = SSL_CTX_new(TLS_client_method());
	SSL *c, *s;
	BIO *cb, *sb;
	bool done = false;
	int i;

	if (!cc)
		return false;
	SSL_CTX_set_min_proto_version(cc, TLS1_3_VERSION);
	if (SSL_CTX_set1_groups_list(cc, client_group) != 1) {
		ERR_clear_error();
		SSL_CTX_free(cc);
		return false;	/* the client itself does not know the group */
	}
	c = SSL_new(cc);
	SSL_set_alpn_protos(c, alpn, alpnlen);
	s = SSL_new(server_ctx);
	/* a BIO pair: what the client writes the server reads, and the other way round */
	if (BIO_new_bio_pair(&cb, 0, &sb, 0) != 1)
		return false;
	SSL_set_bio(c, cb, cb);
	SSL_set_bio(s, sb, sb);
	SSL_set_connect_state(c);
	SSL_set_accept_state(s);
	for (i = 0; i < 20 && !done; i++) {
		int rc = SSL_do_handshake(c);
		int rs = SSL_do_handshake(s);
		int ec = rc == 1 ? 0 : SSL_get_error(c, rc);
		int es = rs == 1 ? 0 : SSL_get_error(s, rs);
		if (rc == 1 && rs == 1)
			done = true;
		else if ((rc != 1 && ec != SSL_ERROR_WANT_READ && ec != SSL_ERROR_WANT_WRITE) ||
		         (rs != 1 && es != SSL_ERROR_WANT_READ && es != SSL_ERROR_WANT_WRITE))
			break;
	}
	ERR_clear_error();
	SSL_free(c);
	SSL_free(s);
	SSL_CTX_free(cc);
	return done;
}

int main(void)
{
	static const char *ok[] = { "X25519", "P-256", "P-384", "X25519MLKEM768" };
	static const char *no[] = { "ffdhe2048", "ffdhe3072", "X448", "P-521" };
	char dir[] = "/tmp/remotix-test-tls.XXXXXX", cmd[1024], pem[256], key[256];
	SSL_CTX *ctxs[2], *x;
	const char *names[2] = { "page", "quic" };
	static const unsigned char alpn[2][10] = { "\x08http/1.1", "\x02h3" };
	static const unsigned int alpnlen[2] = { 9, 3 };
	size_t i, k;

	if (!mkdtemp(dir)) {
		perror("mkdtemp");
		return 3;
	}
	snprintf(pem, sizeof pem, "%s/c.pem", dir);
	snprintf(key, sizeof key, "%s/k.pem", dir);
	snprintf(cmd, sizeof cmd,
	         "openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes "
	         "-keyout %s -out %s -days 2 -subj /CN=t >/dev/null 2>&1", key, pem);
	if (system(cmd) != 0) {
		printf("cannot make a certificate\n");
		return 3;
	}
	ctxs[0] = tls_page_context(pem, key);
	ctxs[1] = tls_quic_context(pem, key);
	CHECK(ctxs[0] && ctxs[1], "both contexts are made");
	for (k = 0; k < 2 && ctxs[0] && ctxs[1]; k++) {
		for (i = 0; i < sizeof ok / sizeof *ok; i++)
			CHECK(shake(ctxs[k], ok[i], alpn[k], alpnlen[k]), "%s context: a client offering only %s is served",
			      names[k], ok[i]);
		for (i = 0; i < sizeof no / sizeof *no; i++)
			CHECK(!shake(ctxs[k], no[i], alpn[k], alpnlen[k]), "%s context: a client offering only %s is REFUSED",
			      names[k], no[i]);
	}
	/* the fallback: an unknown name in the wanted list */
	x = SSL_CTX_new(TLS_server_method());
	CHECK(set_groups(x, "NOSUCHKEM:X25519", "X25519:P-256"),
	      "set_groups: an unknown name falls back to the list without ML-KEM");
	CHECK(!set_groups(x, "NOSUCHKEM", "NOSUCHKEM2"),
	      "set_groups: when the fallback is unknown too it says no");
	SSL_CTX_free(x);

	snprintf(cmd, sizeof cmd, "rm -f %s %s && rmdir %s", pem, key, dir);
	if (system(cmd) != 0)
		printf("  (could not remove %s)\n", dir);
	printf("%d passed, %d failed, of %d\n", passed, failed, passed + failed);
	return failed ? 1 : 0;
}
