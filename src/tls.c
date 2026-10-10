/*
 * tls.c — see tls.h.
 */
#include "tls.h"
#include "registro.h"

#include <string.h>

#include <openssl/err.h>

static const char *errore_ssl(void)
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
static int scegli_alpn(SSL *ssl, const unsigned char **out, unsigned char *outlen,
                       const unsigned char *in, unsigned int inlen, void *arg)
{
	const char *voluto = (const char *)arg;
	size_t vl = strlen(voluto);
	unsigned int i = 0;

	(void)ssl;
	while (i + 1 <= inlen) {
		unsigned int l = in[i];
		if (i + 1 + l > inlen)
			break;
		if (l == vl && memcmp(in + i + 1, voluto, vl) == 0) {
			*out = in + i + 1;
			*outlen = (unsigned char)l;
			return SSL_TLSEXT_ERR_OK;
		}
		i += 1 + l;
	}
	registro_dice(REG_QUIC, "⛔ the client does not offer the ALPN «%s»: refused",
	              voluto);
	return SSL_TLSEXT_ERR_ALERT_FATAL;
}

static SSL_CTX *comune(const char *pem, const char *key)
{
	SSL_CTX *ctx = SSL_CTX_new(TLS_server_method());
	if (!ctx) {
		registro_dice(REG_QUIC, "⛔ SSL_CTX_new: %s", errore_ssl());
		return NULL;
	}
	SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION);
	SSL_CTX_set_options(ctx, SSL_OP_CIPHER_SERVER_PREFERENCE |
	                           SSL_OP_NO_ANTI_REPLAY);
	SSL_CTX_set_mode(ctx, SSL_MODE_RELEASE_BUFFERS);

	if (SSL_CTX_use_PrivateKey_file(ctx, key, SSL_FILETYPE_PEM) != 1) {
		registro_dice(REG_QUIC, "⛔ key %s: %s", key, errore_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	if (SSL_CTX_use_certificate_chain_file(ctx, pem) != 1) {
		registro_dice(REG_QUIC, "⛔ certificate %s: %s", pem, errore_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	if (SSL_CTX_check_private_key(ctx) != 1) {
		registro_dice(REG_QUIC, "⛔ the key does not match the certificate: %s",
		              errore_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	return ctx;
}

SSL_CTX *tls_contesto_quic(const char *pem, const char *key)
{
	static const unsigned char sid[] = "remotix";
	SSL_CTX *ctx = comune(pem, key);
	if (!ctx)
		return NULL;

	SSL_CTX_set_alpn_select_cb(ctx, scegli_alpn, (void *)"h3");
	SSL_CTX_set_session_id_context(ctx, sid, sizeof sid - 1);

	/* ⛔ RCP.md §2.3: the server MUST NOT offer 0-RTT.  0-RTT data can be
	 *    REPLAYED, and the second RCP message is `CREDENZIALI`; the gain
	 *    would be one network round trip on a session that lasts hours.
	 *
	 * ⚠ And the symptom of 0-RTT left on DOES NOT EXIST (`FASI.md` §01-filo-nudo, B2):
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

SSL_CTX *tls_contesto_pagina(const char *pem, const char *key)
{
	SSL_CTX *ctx = comune(pem, key);
	if (!ctx)
		return NULL;
	/* ⚠ `RCP.md` §2.4: «TCP only serves to deliver the page, and HTTP/1.1 is
	 *   enough for it».  The ALPN here is optional — a browser that does not
	 *   send it speaks HTTP/1.1 anyway — and for this reason whoever stays
	 *   silent is NOT refused: we choose only if it offered something. */
	SSL_CTX_set_alpn_select_cb(ctx, scegli_alpn, (void *)"http/1.1");
	registro_dice(REG_PAGINA,
	              "TCP context ready — TLS 1.3, long-lived certificate %s", pem);
	return ctx;
}
