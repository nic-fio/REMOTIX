/*
 * certificati.c — see certificati.h.
 */
#include "certificati.h"
#include "registro.h"

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include <openssl/bio.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/pem.h>
#include <openssl/rand.h>
#include <openssl/x509v3.h>

static const char *errore_ssl(void)
{
	static char buf[256];
	unsigned long e = ERR_get_error();
	if (!e)
		return "(no error queued)";
	ERR_error_string_n(e, buf, sizeof buf);
	return buf;
}

static void percorso(char *fuori, size_t cap, const char *dir, const char *nome)
{
	snprintf(fuori, cap, "%s/%s", dir, nome);
}

static bool esiste(const char *p) { return access(p, F_OK) == 0; }

/* ------------------------------------------------------------------------ */
/* Generation.                                                               */

/* ⛔ P-256, and nothing else (§4.1): «not Ed25519 and never RSA».  P-256 is the
 *    only one that keeps the road of `serverCertificateHashes` open, and a key
 *    chosen today for convenience would close that door without anyone
 *    noticing. */
static EVP_PKEY *chiave_p256(void)
{
	EVP_PKEY *k = EVP_EC_gen("P-256");
	if (!k)
		registro_dice(REG_CERT, "⛔ EVP_EC_gen(P-256): %s", errore_ssl());
	return k;
}

/* The `subjectAltName` is chosen by FORM, not by taste: an IP address is not
 * put as DNS.  ⚠ A browser that finds a SAN that does not match shows a
 * DIFFERENT warning, and some do not even offer the click to proceed (§4.1). */
static void san_di(const char *indirizzo, char *fuori, size_t cap)
{
	struct in_addr a4;
	struct in6_addr a6;
	if (inet_pton(AF_INET, indirizzo, &a4) == 1 ||
	    inet_pton(AF_INET6, indirizzo, &a6) == 1)
		snprintf(fuori, cap, "IP:%s", indirizzo);
	else
		snprintf(fuori, cap, "DNS:%s", indirizzo);
}

static bool scrivi_pem(const char *pem, const char *key, X509 *crt, EVP_PKEY *k)
{
	FILE *f;
	int fd;

	/* ⛔ The private key is born at 0600, it does not get there with a
	 *    `chmod` afterwards: between creation and chmod there is a window in
	 *    which it is readable by anyone, and on a key that is all the time
	 *    it takes (§4.1). */
	fd = open(key, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd < 0) {
		registro_dice(REG_CERT, "⛔ cannot open %s: %s", key, strerror(errno));
		return false;
	}
	f = fdopen(fd, "w");
	if (!f) {
		close(fd);
		return false;
	}
	if (PEM_write_PrivateKey(f, k, NULL, NULL, 0, NULL, NULL) != 1) {
		registro_dice(REG_CERT, "⛔ PEM_write_PrivateKey: %s", errore_ssl());
		fclose(f);
		return false;
	}
	fclose(f);

	f = fopen(pem, "w");
	if (!f) {
		registro_dice(REG_CERT, "⛔ cannot open %s: %s", pem, strerror(errno));
		return false;
	}
	if (PEM_write_X509(f, crt) != 1) {
		registro_dice(REG_CERT, "⛔ PEM_write_X509: %s", errore_ssl());
		fclose(f);
		return false;
	}
	fclose(f);
	return true;
}

static bool genera(const char *pem, const char *key, const char *marca,
                   const char *indirizzo, int giorni)
{
	EVP_PKEY *k = NULL;
	X509 *crt = NULL;
	X509_NAME *nome = NULL;
	X509_EXTENSION *ext = NULL;
	X509V3_CTX ctx;
	char san[192];
	unsigned char seriale[16];
	BIGNUM *bn = NULL;
	bool bene = false;
	FILE *f;

	k = chiave_p256();
	if (!k)
		goto fine;

	crt = X509_new();
	if (!crt)
		goto fine;

	X509_set_version(crt, 2); /* v3 */

	/* A random serial: two certificates generated in the same second with
	 * the same serial are two certificates that a store keeps as a single
	 * one. */
	if (RAND_bytes(seriale, sizeof seriale) != 1)
		goto fine;
	seriale[0] &= 0x7f;
	bn = BN_bin2bn(seriale, sizeof seriale, NULL);
	if (!bn || !BN_to_ASN1_INTEGER(bn, X509_get_serialNumber(crt)))
		goto fine;

	X509_gmtime_adj(X509_getm_notBefore(crt), -3600); /* one hour of margin */
	X509_gmtime_adj(X509_getm_notAfter(crt), (long)giorni * 86400);

	if (X509_set_pubkey(crt, k) != 1)
		goto fine;

	/* ⭐ PHASE 17 — the name is built separately and HANDED OVER, the one
	 *    inside the certificate is not modified: in OpenSSL 4.0
	 *    `X509_get_subject_name` returns `const X509_NAME *` (Ubuntu
	 *    26.10, Fedora rawhide), and writing into it no longer compiles.  This
	 *    way it works the same with 3.x (`fasi/17-l-installatore.md` §4.4). */
	nome = X509_NAME_new();
	if (!nome ||
	    X509_NAME_add_entry_by_txt(nome, "CN", MBSTRING_ASC,
	                               (const unsigned char *)indirizzo, -1, -1, 0) != 1 ||
	    X509_set_subject_name(crt, nome) != 1)
		goto fine;
	/* self-signed: issuer = subject */
	if (X509_set_issuer_name(crt, nome) != 1)
		goto fine;

	san_di(indirizzo, san, sizeof san);
	X509V3_set_ctx_nodb(&ctx);
	X509V3_set_ctx(&ctx, crt, crt, NULL, NULL, 0);
	ext = X509V3_EXT_conf_nid(NULL, &ctx, NID_subject_alt_name, san);
	if (!ext) {
		registro_dice(REG_CERT, "⛔ subjectAltName «%s»: %s", san,
		              errore_ssl());
		goto fine;
	}
	if (X509_add_ext(crt, ext, -1) != 1)
		goto fine;
	X509_EXTENSION_free(ext);
	ext = X509V3_EXT_conf_nid(NULL, &ctx, NID_basic_constraints, "critical,CA:FALSE");
	if (ext) {
		X509_add_ext(crt, ext, -1);
		X509_EXTENSION_free(ext);
		ext = NULL;
	}

	if (X509_sign(crt, k, EVP_sha256()) == 0) {
		registro_dice(REG_CERT, "⛔ X509_sign: %s", errore_ssl());
		goto fine;
	}

	if (!scrivi_pem(pem, key, crt, k))
		goto fine;

	/* The marker: «we wrote this one».  See certificati.h. */
	f = fopen(marca, "w");
	if (f) {
		fprintf(f, "generated by REMOTIX\n");
		fclose(f);
	}

	registro_dice(REG_CERT, "generated %s — P-256, %s, %d days", pem, san,
	              giorni);
	bene = true;

fine:
	if (ext)
		X509_EXTENSION_free(ext);
	if (nome)
		X509_NAME_free(nome);
	if (bn)
		BN_free(bn);
	if (crt)
		X509_free(crt);
	if (k)
		EVP_PKEY_free(k);
	return bene;
}

/* ------------------------------------------------------------------------ */
/* Reading what is already there.                                           */

static X509 *leggi(const char *pem)
{
	FILE *f = fopen(pem, "r");
	X509 *crt;
	if (!f)
		return NULL;
	crt = PEM_read_X509(f, NULL, NULL, NULL);
	fclose(f);
	return crt;
}

/* How many seconds are left before expiry.  Negative if already expired.
 * ⛔ And `giorni_restanti` is not «the file exists»: `LEZIONI.md` §1.9 point 8 —
 *    a file from yesterday answers «yes» to *does it exist?* exactly like one from now. */
static long secondi_alla_scadenza(X509 *crt, time_t *scade)
{
	const ASN1_TIME *fine = X509_get0_notAfter(crt);
	int giorni = 0, sec = 0;
	time_t adesso = time(NULL);

	if (!ASN1_TIME_diff(&giorni, &sec, NULL, fine))
		return -1;
	if (scade)
		*scade = adesso + (time_t)giorni * 86400 + sec;
	return (long)giorni * 86400 + sec;
}

/* The fingerprint: SHA-256 of the DER, in base64 and in hexadecimal. */
static bool impronta_di(X509 *crt, char *b64, size_t b64cap, char *esa,
                        size_t esacap)
{
	unsigned char dig[EVP_MAX_MD_SIZE];
	unsigned int n = 0;
	static const char alfa[] =
		"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
	size_t o = 0, i;

	if (X509_digest(crt, EVP_sha256(), dig, &n) != 1 || n != 32)
		return false;

	if (b64cap < 45)
		return false;
	for (i = 0; i + 2 < n; i += 3) {
		b64[o++] = alfa[dig[i] >> 2];
		b64[o++] = alfa[((dig[i] & 0x03) << 4) | (dig[i + 1] >> 4)];
		b64[o++] = alfa[((dig[i + 1] & 0x0f) << 2) | (dig[i + 2] >> 6)];
		b64[o++] = alfa[dig[i + 2] & 0x3f];
	}
	/* 32 bytes = 10 groups of 3 plus 2 left over */
	b64[o++] = alfa[dig[i] >> 2];
	b64[o++] = alfa[((dig[i] & 0x03) << 4) | (dig[i + 1] >> 4)];
	b64[o++] = alfa[(dig[i + 1] & 0x0f) << 2];
	b64[o++] = '=';
	b64[o] = 0;

	if (esacap < 2 * n + 1)
		return false;
	for (i = 0; i < n; i++)
		snprintf(esa + 2 * i, esacap - 2 * i, "%02x", dig[i]);
	return true;
}

static bool aggiorna_impronta(certificati *c)
{
	X509 *crt = leggi(c->sessione_pem);
	bool bene;
	if (!crt) {
		registro_dice(REG_CERT, "⛔ cannot read %s", c->sessione_pem);
		return false;
	}
	bene = impronta_di(crt, c->impronta, sizeof c->impronta, c->impronta_esa,
	                   sizeof c->impronta_esa);
	secondi_alla_scadenza(crt, &c->sessione_scade);
	X509_free(crt);
	if (!bene) {
		registro_dice(REG_CERT, "⛔ fingerprint not computed");
		return false;
	}
	return true;
}

/* ------------------------------------------------------------------------ */

bool certificati_prepara(certificati *c, const char *dir, const char *indirizzo)
{
	X509 *crt;

	memset(c, 0, sizeof *c);
	snprintf(c->dir, sizeof c->dir, "%s", dir);
	snprintf(c->indirizzo, sizeof c->indirizzo, "%s", indirizzo);

	if (mkdir(dir, 0700) != 0 && errno != EEXIST) {
		registro_dice(REG_CERT, "⛔ cannot create %s: %s", dir, strerror(errno));
		return false;
	}

	percorso(c->pagina_pem, sizeof c->pagina_pem, dir, "pagina.pem");
	percorso(c->pagina_key, sizeof c->pagina_key, dir, "pagina.key");
	percorso(c->pagina_marca, sizeof c->pagina_marca, dir, "pagina.nostro");
	percorso(c->sessione_pem, sizeof c->sessione_pem, dir, "sessione.pem");
	percorso(c->sessione_key, sizeof c->sessione_key, dir, "sessione.key");
	percorso(c->sessione_marca, sizeof c->sessione_marca, dir, "sessione.nostro");

	/* ── the LONG-LIVED one ─────────────────────────────────────────── */
	if (esiste(c->pagina_pem) && esiste(c->pagina_key)) {
		c->pagina_e_nostro = esiste(c->pagina_marca);
		if (!c->pagina_e_nostro) {
			/* ⛔ §4.1: it is the administrator's.  It is used and
			 *    NOT regenerated — not even if expired: regenerating
			 *    it would secretly replace their decision, and the
			 *    symptom (a warning that reappears) would never
			 *    name this line. */
			registro_dice(REG_CERT,
			              "⭐ the page uses a certificate that is not "
			              "ours (%s): it is used and not regenerated (§4.1)",
			              c->pagina_pem);
		} else {
			crt = leggi(c->pagina_pem);
			if (crt) {
				long s = secondi_alla_scadenza(crt, NULL);
				X509_free(crt);
				if (s < 0) {
					registro_dice(REG_CERT,
					              "the page certificate has "
					              "expired: making a new one");
					if (!genera(c->pagina_pem, c->pagina_key,
					            c->pagina_marca, indirizzo,
					            CERT_GIORNI_PAGINA))
						return false;
				}
			}
		}
	} else {
		if (!genera(c->pagina_pem, c->pagina_key, c->pagina_marca,
		            indirizzo, CERT_GIORNI_PAGINA))
			return false;
		c->pagina_e_nostro = true;
	}

	/* ── the SHORT one ──────────────────────────────────────────────── */
	if (!esiste(c->sessione_pem) || !esiste(c->sessione_key)) {
		if (!genera(c->sessione_pem, c->sessione_key, c->sessione_marca,
		            indirizzo, CERT_GIORNI_SESSIONE))
			return false;
		c->rotazioni++;
	}
	if (!aggiorna_impronta(c))
		return false;

	/* ⛔ And if what was there is already past the margin, rotate now —
	 *    at startup, not at the first useful occasion.  A server restarted
	 *    after three weeks would otherwise serve a page carrying the
	 *    fingerprint of a certificate the browser refuses. */
	certificati_ruota_se_serve(c);

	/* ⛔ And the two MUST be TWO.  It is the check of B13.1, and it is done at
	 *    birth instead of fourteen days later. */
	{
		X509 *p = leggi(c->pagina_pem), *s = leggi(c->sessione_pem);
		char ip[64], ipe[80], is[64], ise[80];
		bool due = false;
		if (p && s && impronta_di(p, ip, sizeof ip, ipe, sizeof ipe) &&
		    impronta_di(s, is, sizeof is, ise, sizeof ise))
			due = strcmp(ip, is) != 0;
		if (p)
			X509_free(p);
		if (s)
			X509_free(s);
		if (!due) {
			registro_dice(REG_CERT,
			              "⛔ the two certificates are THE SAME: it is the "
			              "defect of B13.1, the warning would reappear "
			              "every two weeks.  Not starting.");
			return false;
		}
		registro_dice(REG_CERT,
		              "⭐ two certificates, two fingerprints: page %.12s… "
		              "session %.12s…",
		              ip, is);
	}

	registro_dice(REG_CERT,
	              "session fingerprint (SHA-256 of the DER, base64): %s",
	              c->impronta);
	return true;
}

bool certificati_ruota_se_serve(certificati *c)
{
	X509 *crt = leggi(c->sessione_pem);
	long restano;

	if (!crt) {
		registro_dice(REG_CERT,
		              "⛔ the session certificate cannot be read: making "
		              "a new one");
		restano = -1;
	} else {
		restano = secondi_alla_scadenza(crt, &c->sessione_scade);
		X509_free(crt);
	}

	if (restano > (long)CERT_MARGINE_GIORNI * 86400)
		return false;

	/* ⛔ «before it expires», not «when it has expired»: with the fingerprint
	 *    already published in an open page, an expired certificate is a
	 *    session that no longer opens and does not say why (§4.1-bis). */
	registro_dice(REG_CERT,
	              "⭐ rotation of the SESSION certificate: %ld "
	              "seconds were left, the margin is %d days",
	              restano, CERT_MARGINE_GIORNI);
	if (!genera(c->sessione_pem, c->sessione_key, c->sessione_marca,
	            c->indirizzo, CERT_GIORNI_SESSIONE)) {
		registro_dice(REG_CERT, "⛔ rotation FAILED: the old one stays");
		return false;
	}
	if (!aggiorna_impronta(c))
		return false;
	c->rotazioni++;
	registro_dice(REG_CERT,
	              "⭐ rotated (rotations since the server started: %u).  "
	              "New fingerprint: %s",
	              c->rotazioni, c->impronta);
	/* ⛔ And the page must be fetched again: whoever has a tab open holds
	 *    the old fingerprint, and the way to update it is the `/impronta`
	 *    endpoint (§4.1-bis).  Here we only say that it happened. */
	return true;
}
