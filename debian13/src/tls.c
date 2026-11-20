/*
 * tls.c — see tls.h.
 */
#include "tls.h"
#include "log.h"

#include <stdbool.h>
#include <string.h>

#include <openssl/err.h>

static const char *error_ssl(void)
{
	static char buf[256];
	unsigned long e = ERR_get_error();
	if (!e)
		return "(no error queued)";
	ERR_error_string_n(e, buf, sizeof buf);
	return buf;
}

/* ⛔ The ALPN is negotiated by the browser, not by us (`RCP.md` §2.2): a page
 *    does not choose the ALPN, and the only value it sends for a WebTransport
 *    session is `h3`.  Here we choose among what it offers — and if it does
 *    not offer `h3` we refuse, instead of falling back silently (`CODER.md` §4.2). */
static int choose_alpn(SSL *ssl, const unsigned char **out, unsigned char *outlen,
                       const unsigned char *in, unsigned int inlen, void *arg)
{
	const char *wanted = (const char *)arg;
	size_t vl = strlen(wanted);
	unsigned int i = 0;

	(void)ssl;
	while (i + 1 <= inlen) {
		unsigned int l = in[i];
		if (i + 1 + l > inlen)
			break;
		if (l == vl && memcmp(in + i + 1, wanted, vl) == 0) {
			*out = in + i + 1;
			*outlen = (unsigned char)l;
			return SSL_TLSEXT_ERR_OK;
		}
		i += 1 + l;
	}
	registro_dice(REG_QUIC, "⛔ the client does not offer the ALPN «%s»: refused",
	              wanted);
	return SSL_TLSEXT_ERR_ALERT_FATAL;
}

/* ⭐ 1.5 (audit R4): the key-exchange GROUPS the server accepts.  Until now nobody set
 *   them, so OpenSSL's default list applied, and a client could offer ONLY an expensive
 *   group — ffdhe3072 costs the server about 6 ms of CPU per handshake against 1.2 ms for
 *   X25519 — and the server had to follow, on the single loop that also serves the video.
 *   Browsers send X25519MLKEM768, X25519 and P-256; P-384 is kept for the rest.  The same
 *   for the QUIC and the TCP context, because both come from `common()`.
 *
 * ⛔ `SSL_CTX_set1_groups_list()` fails AS A WHOLE when one name is unknown (checked on
 *   OpenSSL 3.5.7), and an OpenSSL older than 3.5 does not know X25519MLKEM768: then the
 *   list WITHOUT it is set and the line says so — the server does not start with the
 *   defaults, which is exactly the defect.  `ngtcp2_crypto_ossl_configure_server_session()`
 *   does not touch the groups (it imports no group or option function from OpenSSL). */
#define TLS_GROUPS         "X25519MLKEM768:X25519:P-256:P-384"
#define TLS_GROUPS_CLASSIC "X25519:P-256:P-384"

static bool set_groups(SSL_CTX *ctx, const char *wanted, const char *classic)
{
	if (SSL_CTX_set1_groups_list(ctx, wanted) == 1)
		return true;
	ERR_clear_error();
	registro_dice(REG_QUIC,
	              "this OpenSSL does not know the key-exchange groups «%s»: "
	              "using «%s» (without ML-KEM)", wanted, classic);
	if (SSL_CTX_set1_groups_list(ctx, classic) == 1)
		return true;
	registro_dice(REG_QUIC, "⛔ key-exchange groups «%s»: %s", classic, error_ssl());
	return false;
}

static SSL_CTX *common(const char *pem, const char *key)
{
	SSL_CTX *ctx = SSL_CTX_new(TLS_server_method());
	if (!ctx) {
		registro_dice(REG_QUIC, "⛔ SSL_CTX_new: %s", error_ssl());
		return NULL;
	}
	SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION);
	SSL_CTX_set_options(ctx, SSL_OP_CIPHER_SERVER_PREFERENCE |
	                           SSL_OP_NO_ANTI_REPLAY);
	SSL_CTX_set_mode(ctx, SSL_MODE_RELEASE_BUFFERS);
	if (!set_groups(ctx, TLS_GROUPS, TLS_GROUPS_CLASSIC)) {
		SSL_CTX_free(ctx);
		return NULL;
	}

	if (SSL_CTX_use_PrivateKey_file(ctx, key, SSL_FILETYPE_PEM) != 1) {
		registro_dice(REG_QUIC, "⛔ key %s: %s", key, error_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	if (SSL_CTX_use_certificate_chain_file(ctx, pem) != 1) {
		registro_dice(REG_QUIC, "⛔ certificate %s: %s", pem, error_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	if (SSL_CTX_check_private_key(ctx) != 1) {
		registro_dice(REG_QUIC, "⛔ the key does not match the certificate: %s",
		              error_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	return ctx;
}

SSL_CTX *tls_quic_context(const char *pem, const char *key)
{
	static const unsigned char sid[] = "remotix";
	SSL_CTX *ctx = common(pem, key);
	if (!ctx)
		return NULL;

	SSL_CTX_set_alpn_select_cb(ctx, choose_alpn, (void *)"h3");
	SSL_CTX_set_session_id_context(ctx, sid, sizeof sid - 1);

	/* ⛔ RCP.md §2.3: the server MUST NOT offer 0-RTT.  0-RTT data can be
	 *    REPLAYED, and the second RCP message is `CREDENTIALS`; the gain
	 *    would be one network round trip on a session that lasts hours.
	 *
	 * ⚠ And the symptom of 0-RTT left on DOES NOT EXIST (`PHASES.md` §01-filo-nudo, B2):
	 *   the session opens the same and the bytes come back the same.  The
	 *   libraries offer it by default, so leaving it as it is is not a choice:
	 *   it is an oversight that no functional bench sees.  Here it is turned
	 *   off explicitly, and the line below is the place where a reviewer
	 *   can read that it is off.
	 *
	 * ⛔ `SSL_CTX_set_max_early_data(0)` is the way to say it at CONTEXT
	 *    LEVEL, so no session can turn it on by oversight: the ngtcp2
	 *    example sets it to UINT32_MAX and then turns it on for the single
	 *    SSL. */
	SSL_CTX_set_max_early_data(ctx, 0);

	registro_dice(REG_QUIC,
	              "QUIC context ready — ALPN h3, TLS 1.3, 0-RTT OFF "
	              "(§2.3), certificate %s",
	              pem);
	return ctx;
}

SSL_CTX *tls_page_context(const char *pem, const char *key)
{
	SSL_CTX *ctx = common(pem, key);
	if (!ctx)
		return NULL;
	/* ⚠ `RCP.md` §2.4: «TCP only serves to deliver the page, and HTTP/1.1 is
	 *   enough for it».  The ALPN here is optional — a browser that does not
	 *   send it speaks HTTP/1.1 anyway — and for this reason whoever stays
	 *   silent is NOT refused: we choose only if it offered something. */
	SSL_CTX_set_alpn_select_cb(ctx, choose_alpn, (void *)"http/1.1");
	registro_dice(LOG_PAGE,
	              "TCP context ready — TLS 1.3, long-lived certificate %s", pem);
	return ctx;
}
