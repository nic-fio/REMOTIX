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

static const char *error_ssl(void)
{
	static char buf[256];
	unsigned long e = ERR_get_error();
	if (!e)
		return "(no error queued)";
	ERR_error_string_n(e, buf, sizeof buf);
	return buf;
}

static void fpath(char *outside, size_t cap, const char *dir, const char *label_name)
{
	snprintf(outside, cap, "%s/%s", dir, label_name);
}

static bool path_exists(const char *p) { return access(p, F_OK) == 0; }

/* ------------------------------------------------------------------------ */
/* Generation.                                                               */

/* ⛔ P-256, and nothing else (§4.1): «not Ed25519 and never RSA».  P-256 is the
 *    only one that keeps the road of `serverCertificateHashes` open, and a key
 *    chosen today for convenience would close that door without anyone
 *    noticing. */
static EVP_PKEY *key_p256(void)
{
	EVP_PKEY *k = EVP_EC_gen("P-256");
	if (!k)
		log_says(REG_CERT, "⛔ EVP_EC_gen(P-256): %s", error_ssl());
	return k;
}

/* The `subjectAltName` is chosen by FORM, not by taste: an IP address is not
 * put as DNS.  ⚠ A browser that finds a SAN that does not match shows a
 * DIFFERENT warning, and some do not even offer the click to proceed (§4.1). */
static void san_di(const char *address, char *outside, size_t cap)
{
	struct in_addr a4;
	struct in6_addr a6;
	if (inet_pton(AF_INET, address, &a4) == 1 ||
	    inet_pton(AF_INET6, address, &a6) == 1)
		snprintf(outside, cap, "IP:%s", address);
	else
		snprintf(outside, cap, "DNS:%s", address);
}

static bool write_pem(const char *pem, const char *key, X509 *crt, EVP_PKEY *k)
{
	FILE *f;
	int fd;

	/* ⛔ The private key is born at 0600, it does not get there with a
	 *    `chmod` afterwards: between creation and chmod there is a window in
	 *    which it is readable by anyone, and on a key that is all the time
	 *    it takes (§4.1). */
	fd = open(key, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd < 0) {
		log_says(REG_CERT, "⛔ cannot open %s: %s", key, strerror(errno));
		return false;
	}
	f = fdopen(fd, "w");
	if (!f) {
		close(fd);
		return false;
	}
	if (PEM_write_PrivateKey(f, k, NULL, NULL, 0, NULL, NULL) != 1) {
		log_says(REG_CERT, "⛔ PEM_write_PrivateKey: %s", error_ssl());
		fclose(f);
		return false;
	}
	fclose(f);

	f = fopen(pem, "w");
	if (!f) {
		log_says(REG_CERT, "⛔ cannot open %s: %s", pem, strerror(errno));
		return false;
	}
	if (PEM_write_X509(f, crt) != 1) {
		log_says(REG_CERT, "⛔ PEM_write_X509: %s", error_ssl());
		fclose(f);
		return false;
	}
	fclose(f);
	return true;
}

static bool generate(const char *pem, const char *key, const char *mark,
                   const char *address, int days)
{
	EVP_PKEY *k = NULL;
	X509 *crt = NULL;
	X509_NAME *label_name = NULL;
	X509_EXTENSION *ext = NULL;
	X509V3_CTX ctx;
	char san[192];
	unsigned char serial_number[16];
	BIGNUM *bn = NULL;
	bool all_ok = false;
	FILE *f;

	k = key_p256();
	if (!k)
		goto fine;

	crt = X509_new();
	if (!crt)
		goto fine;

	X509_set_version(crt, 2); /* v3 */

	/* A random serial: two certificates generated in the same second with
	 * the same serial are two certificates that a store keeps as a single
	 * one. */
	if (RAND_bytes(serial_number, sizeof serial_number) != 1)
		goto fine;
	serial_number[0] &= 0x7f;
	bn = BN_bin2bn(serial_number, sizeof serial_number, NULL);
	if (!bn || !BN_to_ASN1_INTEGER(bn, X509_get_serialNumber(crt)))
		goto fine;

	X509_gmtime_adj(X509_getm_notBefore(crt), -3600); /* one hour of margin */
	X509_gmtime_adj(X509_getm_notAfter(crt), (long)days * 86400);

	if (X509_set_pubkey(crt, k) != 1)
		goto fine;

	/* ⭐ PHASE 17 — the name is built separately and HANDED OVER, the one
	 *    inside the certificate is not modified: in OpenSSL 4.0
	 *    `X509_get_subject_name` returns `const X509_NAME *` (Ubuntu
	 *    26.10, Fedora rawhide), and writing into it no longer compiles.  This
	 *    way it works the same with 3.x (`fasi/17-l-installatore.md` §4.4). */
	label_name = X509_NAME_new();
	if (!label_name ||
	    X509_NAME_add_entry_by_txt(label_name, "CN", MBSTRING_ASC,
	                               (const unsigned char *)address, -1, -1, 0) != 1 ||
	    X509_set_subject_name(crt, label_name) != 1)
		goto fine;
	/* self-signed: issuer = subject */
	if (X509_set_issuer_name(crt, label_name) != 1)
		goto fine;

	san_di(address, san, sizeof san);
	X509V3_set_ctx_nodb(&ctx);
	X509V3_set_ctx(&ctx, crt, crt, NULL, NULL, 0);
	ext = X509V3_EXT_conf_nid(NULL, &ctx, NID_subject_alt_name, san);
	if (!ext) {
		log_says(REG_CERT, "⛔ subjectAltName «%s»: %s", san,
		              error_ssl());
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
		log_says(REG_CERT, "⛔ X509_sign: %s", error_ssl());
		goto fine;
	}

	if (!write_pem(pem, key, crt, k))
		goto fine;

	/* The marker: «we wrote this one».  See certificati.h. */
	f = fopen(mark, "w");
	if (f) {
		fprintf(f, "generated by REMOTIX\n");
		fclose(f);
	}

	log_says(REG_CERT, "generated %s — P-256, %s, %d days", pem, san,
	              days);
	all_ok = true;

fine:
	if (ext)
		X509_EXTENSION_free(ext);
	if (label_name)
		X509_NAME_free(label_name);
	if (bn)
		BN_free(bn);
	if (crt)
		X509_free(crt);
	if (k)
		EVP_PKEY_free(k);
	return all_ok;
}

/* ------------------------------------------------------------------------ */
/* Reading what is already there.                                           */

static X509 *read_it(const char *pem)
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
static long seconds_to_expiry(X509 *crt, time_t *expires)
{
	const ASN1_TIME *fine = X509_get0_notAfter(crt);
	int days = 0, sec = 0;
	time_t clock = time(NULL);

	if (!ASN1_TIME_diff(&days, &sec, NULL, fine))
		return -1;
	if (expires)
		*expires = clock + (time_t)days * 86400 + sec;
	return (long)days * 86400 + sec;
}

/* The fingerprint: SHA-256 of the DER, in base64 and in hexadecimal. */
static bool fingerprint_of(X509 *crt, char *b64, size_t b64cap, char *hex_s,
                        size_t hexcap)
{
	unsigned char dig[EVP_MAX_MD_SIZE];
	unsigned int n = 0;
	static const char alpha_ch[] =
		"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
	size_t o = 0, i;

	if (X509_digest(crt, EVP_sha256(), dig, &n) != 1 || n != 32)
		return false;

	if (b64cap < 45)
		return false;
	for (i = 0; i + 2 < n; i += 3) {
		b64[o++] = alpha_ch[dig[i] >> 2];
		b64[o++] = alpha_ch[((dig[i] & 0x03) << 4) | (dig[i + 1] >> 4)];
		b64[o++] = alpha_ch[((dig[i + 1] & 0x0f) << 2) | (dig[i + 2] >> 6)];
		b64[o++] = alpha_ch[dig[i + 2] & 0x3f];
	}
	/* 32 bytes = 10 groups of 3 plus 2 left over */
	b64[o++] = alpha_ch[dig[i] >> 2];
	b64[o++] = alpha_ch[((dig[i] & 0x03) << 4) | (dig[i + 1] >> 4)];
	b64[o++] = alpha_ch[(dig[i + 1] & 0x0f) << 2];
	b64[o++] = '=';
	b64[o] = 0;

	if (hexcap < 2 * n + 1)
		return false;
	for (i = 0; i < n; i++)
		snprintf(hex_s + 2 * i, hexcap - 2 * i, "%02x", dig[i]);
	return true;
}

static bool update_fingerprint(certificates *c)
{
	X509 *crt = read_it(c->session_pem);
	bool all_ok;
	if (!crt) {
		log_says(REG_CERT, "⛔ cannot read %s", c->session_pem);
		return false;
	}
	all_ok = fingerprint_of(crt, c->fingerprint, sizeof c->fingerprint, c->fingerprint_hex,
	                   sizeof c->fingerprint_hex);
	seconds_to_expiry(crt, &c->session_expires);
	X509_free(crt);
	if (!all_ok) {
		log_says(REG_CERT, "⛔ fingerprint not computed");
		return false;
	}
	return true;
}

/* ------------------------------------------------------------------------ */

bool certificates_prepare(certificates *c, const char *dir, const char *address)
{
	X509 *crt;

	memset(c, 0, sizeof *c);
	snprintf(c->dir, sizeof c->dir, "%s", dir);
	snprintf(c->address, sizeof c->address, "%s", address);

	if (mkdir(dir, 0700) != 0 && errno != EEXIST) {
		log_says(REG_CERT, "⛔ cannot create %s: %s", dir, strerror(errno));
		return false;
	}

	fpath(c->page_pem, sizeof c->page_pem, dir, "page_v.pem");
	fpath(c->page_key, sizeof c->page_key, dir, "page_v.key");
	fpath(c->page_marker, sizeof c->page_marker, dir, "page_v.our");
	fpath(c->session_pem, sizeof c->session_pem, dir, "session_v.pem");
	fpath(c->session_key, sizeof c->session_key, dir, "session_v.key");
	fpath(c->session_mark, sizeof c->session_mark, dir, "session_v.our");

	/* ── the LONG-LIVED one ─────────────────────────────────────────── */
	if (path_exists(c->page_pem) && path_exists(c->page_key)) {
		c->page_is_ours = path_exists(c->page_marker);
		if (!c->page_is_ours) {
			/* ⛔ §4.1: it is the administrator's.  It is used and
			 *    NOT regenerated — not even if expired: regenerating
			 *    it would secretly replace their decision, and the
			 *    symptom (a warning that reappears) would never
			 *    name this line. */
			log_says(REG_CERT,
			              "⭐ the page uses a certificate that is not "
			              "ours (%s): it is used and not regenerated (§4.1)",
			              c->page_pem);
		} else {
			crt = read_it(c->page_pem);
			if (crt) {
				long s = seconds_to_expiry(crt, NULL);
				X509_free(crt);
				if (s < 0) {
					log_says(REG_CERT,
					              "the page certificate has "
					              "expired: making a new one");
					if (!generate(c->page_pem, c->page_key,
					            c->page_marker, address,
					            CERT_DAYS_PAGE))
						return false;
				}
			}
		}
	} else {
		if (!generate(c->page_pem, c->page_key, c->page_marker,
		            address, CERT_DAYS_PAGE))
			return false;
		c->page_is_ours = true;
	}

	/* ── the SHORT one ──────────────────────────────────────────────── */
	if (!path_exists(c->session_pem) || !path_exists(c->session_key)) {
		if (!generate(c->session_pem, c->session_key, c->session_mark,
		            address, CERT_DAYS_SESSION))
			return false;
		c->rotations++;
	}
	if (!update_fingerprint(c))
		return false;

	/* ⛔ And if what was there is already past the margin, rotate now —
	 *    at startup, not at the first useful occasion.  A server restarted
	 *    after three weeks would otherwise needs a page carrying the
	 *    fingerprint of a certificate the browser refuses. */
	certificates_rotate_if_needed(c);

	/* ⛔ And the two MUST be TWO.  It is the check of B13.1, and it is done at
	 *    birth instead of fourteen days later. */
	{
		X509 *p = read_it(c->page_pem), *s = read_it(c->session_pem);
		char ip[64], ipe[80], is[64], ise[80];
		bool due = false;
		if (p && s && fingerprint_of(p, ip, sizeof ip, ipe, sizeof ipe) &&
		    fingerprint_of(s, is, sizeof is, ise, sizeof ise))
			due = strcmp(ip, is) != 0;
		if (p)
			X509_free(p);
		if (s)
			X509_free(s);
		if (!due) {
			log_says(REG_CERT,
			              "⛔ the two certificates are THE SAME: it is the "
			              "defect of B13.1, the warning would reappear "
			              "every two weeks.  Not starting.");
			return false;
		}
		log_says(REG_CERT,
		              "⭐ two certificates, two fingerprints: page %.12s… "
		              "session %.12s…",
		              ip, is);
	}

	log_says(REG_CERT,
	              "session fingerprint (SHA-256 of the DER, base64): %s",
	              c->fingerprint);
	return true;
}

bool certificates_rotate_if_needed(certificates *c)
{
	X509 *crt = read_it(c->session_pem);
	long remain;

	if (!crt) {
		log_says(REG_CERT,
		              "⛔ the session certificate cannot be read: making "
		              "a new one");
		remain = -1;
	} else {
		remain = seconds_to_expiry(crt, &c->session_expires);
		X509_free(crt);
	}

	if (remain > (long)CERT_MARGIN_DAYS * 86400)
		return false;

	/* ⛔ «before it expires», not «when it has expired»: with the fingerprint
	 *    already published in an open page, an expired certificate is a
	 *    session that no longer opens and does not say why (§4.1-bis). */
	log_says(REG_CERT,
	              "⭐ rotation of the SESSION certificate: %ld "
	              "seconds were left, the margin is %d days",
	              remain, CERT_MARGIN_DAYS);
	if (!generate(c->session_pem, c->session_key, c->session_mark,
	            c->address, CERT_DAYS_SESSION)) {
		log_says(REG_CERT, "⛔ rotation FAILED: the old one stays");
		return false;
	}
	if (!update_fingerprint(c))
		return false;
	c->rotations++;
	log_says(REG_CERT,
	              "⭐ rotated (rotations since the server started: %u).  "
	              "New fingerprint: %s",
	              c->rotations, c->fingerprint);
	/* ⛔ And the page must be fetched again: whoever has a tab open holds
	 *    the old fingerprint, and the way to update it is the `/impronta`
	 *    endpoint (§4.1-bis).  Here we only say that it happened. */
	return true;
}
