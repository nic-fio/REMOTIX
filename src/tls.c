/*
 * tls.c — vedi tls.h.
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
		return "(nessun errore in coda)";
	ERR_error_string_n(e, buf, sizeof buf);
	return buf;
}

/* ⛔ L'ALPN lo negozia il browser, non noi (`RCP.md` §2.2): una pagina non
 *    sceglie l'ALPN, e l'unico valore che manda per una sessione WebTransport
 *    e' `h3`.  Qui si sceglie fra quel che offre — e se non offre `h3` si
 *    rifiuta, invece di ripiegare in silenzio (`CODER.md` §4.2). */
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
	registro_dice(REG_QUIC, "⛔ il client non offre l'ALPN «%s»: rifiutato",
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
		registro_dice(REG_QUIC, "⛔ chiave %s: %s", key, errore_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	if (SSL_CTX_use_certificate_chain_file(ctx, pem) != 1) {
		registro_dice(REG_QUIC, "⛔ certificato %s: %s", pem, errore_ssl());
		SSL_CTX_free(ctx);
		return NULL;
	}
	if (SSL_CTX_check_private_key(ctx) != 1) {
		registro_dice(REG_QUIC, "⛔ la chiave non combacia col certificato: %s",
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

	/* ⛔ RCP.md §2.3: il server NON DEVE offrire 0-RTT.  I dati 0-RTT si
	 *    possono RIPETERE, e il secondo messaggio di RCP e' `CREDENZIALI`;
	 *    il guadagno sarebbe un giro di rete su una sessione che dura ore.
	 *
	 * ⚠ E il sintomo di 0-RTT acceso NON ESISTE (`FASI.md` §01-filo-nudo, B2):
	 *   la sessione si apre uguale e i byte tornano uguali.  Le librerie lo
	 *   offrono di serie, quindi lasciarlo com'e' non e' una scelta: e' una
	 *   distrazione che nessun banco funzionale vede.  Qui si spegne
	 *   esplicitamente, e la riga qui sotto e' il posto in cui un revisore
	 *   puo' leggere che e' spento.
	 *
	 * ⛔ `SSL_CTX_set_max_early_data(0)` e' il modo di dirlo a LIVELLO DI
	 *    CONTESTO, cosi' nessuna sessione puo' accenderlo per distrazione:
	 *    l'esempio di ngtcp2 lo mette a UINT32_MAX e poi lo accende sulla
	 *    singola SSL. */
	SSL_CTX_set_max_early_data(ctx, 0);

	registro_dice(REG_QUIC,
	              "contesto QUIC pronto — ALPN h3, TLS 1.3, 0-RTT SPENTO "
	              "(§2.3), certificato %s",
	              pem);
	return ctx;
}

SSL_CTX *tls_contesto_pagina(const char *pem, const char *key)
{
	SSL_CTX *ctx = comune(pem, key);
	if (!ctx)
		return NULL;
	/* ⚠ `RCP.md` §2.4: «il TCP serve solo a consegnare la pagina, e le basta
	 *   HTTP/1.1».  L'ALPN qui e' facoltativo — un browser che non lo manda
	 *   parla HTTP/1.1 lo stesso — e per questo NON si rifiuta chi tace: si
	 *   sceglie solo se ha offerto qualcosa. */
	SSL_CTX_set_alpn_select_cb(ctx, scegli_alpn, (void *)"http/1.1");
	registro_dice(REG_PAGINA,
	              "contesto TCP pronto — TLS 1.3, certificato longevo %s", pem);
	return ctx;
}
