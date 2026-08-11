/*
 * certificati.c — vedi certificati.h.
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
		return "(nessun errore in coda)";
	ERR_error_string_n(e, buf, sizeof buf);
	return buf;
}

static void percorso(char *fuori, size_t cap, const char *dir, const char *nome)
{
	snprintf(fuori, cap, "%s/%s", dir, nome);
}

static bool esiste(const char *p) { return access(p, F_OK) == 0; }

/* ------------------------------------------------------------------------ */
/* La generazione.                                                           */

/* ⛔ P-256, e nient'altro (§4.1): «non Ed25519 e mai RSA».  P-256 e' l'unica
 *    che tiene aperta la strada di `serverCertificateHashes`, e una chiave
 *    scelta oggi per comodita' chiuderebbe quella porta senza che nessuno se ne
 *    accorga. */
static EVP_PKEY *chiave_p256(void)
{
	EVP_PKEY *k = EVP_EC_gen("P-256");
	if (!k)
		registro_dice(REG_CERT, "⛔ EVP_EC_gen(P-256): %s", errore_ssl());
	return k;
}

/* Il `subjectAltName` si sceglie per FORMA, non per gusto: un indirizzo IP non
 * si mette come DNS.  ⚠ Un browser che trova un SAN che non combacia mostra un
 * avviso DIVERSO, e alcuni non offrono nemmeno il clic per proseguire (§4.1). */
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

	/* ⛔ La chiave privata nasce a 0600, non ci arriva con una `chmod`
	 *    dopo: fra la creazione e la chmod c'e' una finestra in cui e'
	 *    leggibile da chiunque, e su una chiave e' tutto il tempo che
	 *    serve (§4.1). */
	fd = open(key, O_WRONLY | O_CREAT | O_TRUNC, 0600);
	if (fd < 0) {
		registro_dice(REG_CERT, "⛔ non apro %s: %s", key, strerror(errno));
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
		registro_dice(REG_CERT, "⛔ non apro %s: %s", pem, strerror(errno));
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
	X509_NAME *nome;
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

	/* Un seriale casuale: due certificati generati nello stesso secondo con
	 * lo stesso seriale sono due certificati che un magazzino tiene per uno
	 * solo. */
	if (RAND_bytes(seriale, sizeof seriale) != 1)
		goto fine;
	seriale[0] &= 0x7f;
	bn = BN_bin2bn(seriale, sizeof seriale, NULL);
	if (!bn || !BN_to_ASN1_INTEGER(bn, X509_get_serialNumber(crt)))
		goto fine;

	X509_gmtime_adj(X509_getm_notBefore(crt), -3600); /* un'ora di margine */
	X509_gmtime_adj(X509_getm_notAfter(crt), (long)giorni * 86400);

	if (X509_set_pubkey(crt, k) != 1)
		goto fine;

	nome = X509_get_subject_name(crt);
	X509_NAME_add_entry_by_txt(nome, "CN", MBSTRING_ASC,
	                           (const unsigned char *)indirizzo, -1, -1, 0);
	/* autofirmato: emittente = soggetto */
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

	/* La marca: «questo l'abbiamo scritto noi».  Vedi certificati.h. */
	f = fopen(marca, "w");
	if (f) {
		fprintf(f, "generato da REMOTIX_V2\n");
		fclose(f);
	}

	registro_dice(REG_CERT, "generato %s — P-256, %s, %d giorni", pem, san,
	              giorni);
	bene = true;

fine:
	if (ext)
		X509_EXTENSION_free(ext);
	if (bn)
		BN_free(bn);
	if (crt)
		X509_free(crt);
	if (k)
		EVP_PKEY_free(k);
	return bene;
}

/* ------------------------------------------------------------------------ */
/* La lettura di quel che c'e' gia'.                                         */

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

/* Quanti secondi mancano alla scadenza.  Negativo se e' gia' scaduto.
 * ⛔ E `giorni_restanti` non e' «esiste il file»: `LEZIONI.md` §1.9 punto 8 —
 *    un file di ieri risponde «si'» a *esiste?* esattamente come uno di adesso. */
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

/* L'impronta: SHA-256 del DER, in base64 e in esadecimale. */
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
	/* 32 byte = 10 gruppi da 3 piu' 2 che avanzano */
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
		registro_dice(REG_CERT, "⛔ non leggo %s", c->sessione_pem);
		return false;
	}
	bene = impronta_di(crt, c->impronta, sizeof c->impronta, c->impronta_esa,
	                   sizeof c->impronta_esa);
	secondi_alla_scadenza(crt, &c->sessione_scade);
	X509_free(crt);
	if (!bene) {
		registro_dice(REG_CERT, "⛔ impronta non calcolata");
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
		registro_dice(REG_CERT, "⛔ non creo %s: %s", dir, strerror(errno));
		return false;
	}

	percorso(c->pagina_pem, sizeof c->pagina_pem, dir, "pagina.pem");
	percorso(c->pagina_key, sizeof c->pagina_key, dir, "pagina.key");
	percorso(c->pagina_marca, sizeof c->pagina_marca, dir, "pagina.nostro");
	percorso(c->sessione_pem, sizeof c->sessione_pem, dir, "sessione.pem");
	percorso(c->sessione_key, sizeof c->sessione_key, dir, "sessione.key");
	percorso(c->sessione_marca, sizeof c->sessione_marca, dir, "sessione.nostro");

	/* ── il LONGEVO ─────────────────────────────────────────────────── */
	if (esiste(c->pagina_pem) && esiste(c->pagina_key)) {
		c->pagina_e_nostro = esiste(c->pagina_marca);
		if (!c->pagina_e_nostro) {
			/* ⛔ §4.1: e' dell'amministratore.  Si usa e NON si
			 *    rigenera — nemmeno se e' scaduto: rigenerarlo
			 *    sarebbe sostituire di nascosto la sua decisione,
			 *    e il sintomo (un avviso che ricompare) non
			 *    nominerebbe mai questa riga. */
			registro_dice(REG_CERT,
			              "⭐ la pagina usa un certificato che non e' "
			              "nostro (%s): si usa e non si rigenera (§4.1)",
			              c->pagina_pem);
		} else {
			crt = leggi(c->pagina_pem);
			if (crt) {
				long s = secondi_alla_scadenza(crt, NULL);
				X509_free(crt);
				if (s < 0) {
					registro_dice(REG_CERT,
					              "il certificato della pagina e' "
					              "scaduto: se ne fa uno nuovo");
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

	/* ── il BREVE ───────────────────────────────────────────────────── */
	if (!esiste(c->sessione_pem) || !esiste(c->sessione_key)) {
		if (!genera(c->sessione_pem, c->sessione_key, c->sessione_marca,
		            indirizzo, CERT_GIORNI_SESSIONE))
			return false;
		c->rotazioni++;
	}
	if (!aggiorna_impronta(c))
		return false;

	/* ⛔ E se quel che c'era e' gia' oltre il margine, si ruota adesso —
	 *    all'avvio, non alla prima occasione utile.  Un server riacceso dopo
	 *    tre settimane servirebbe altrimenti una pagina con dentro
	 *    l'impronta di un certificato che il browser rifiuta. */
	certificati_ruota_se_serve(c);

	/* ⛔ E i due DEVONO essere DUE.  E' il controllo di B13.1, e si fa alla
	 *    nascita invece che quattordici giorni dopo. */
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
			              "⛔ i due certificati sono LO STESSO: e' il "
			              "difetto di B13.1, l'avviso ricomparirebbe "
			              "ogni due settimane.  Non si parte.");
			return false;
		}
		registro_dice(REG_CERT,
		              "⭐ due certificati, due impronte: pagina %.12s… "
		              "sessione %.12s…",
		              ip, is);
	}

	registro_dice(REG_CERT,
	              "impronta della sessione (SHA-256 del DER, base64): %s",
	              c->impronta);
	return true;
}

bool certificati_ruota_se_serve(certificati *c)
{
	X509 *crt = leggi(c->sessione_pem);
	long restano;

	if (!crt) {
		registro_dice(REG_CERT,
		              "⛔ il certificato di sessione non si legge: se ne "
		              "fa uno nuovo");
		restano = -1;
	} else {
		restano = secondi_alla_scadenza(crt, &c->sessione_scade);
		X509_free(crt);
	}

	if (restano > (long)CERT_MARGINE_GIORNI * 86400)
		return false;

	/* ⛔ «prima che scada», non «quando e' scaduto»: con l'impronta gia'
	 *    pubblicata in una pagina aperta, un certificato scaduto e' una
	 *    sessione che non si apre piu' e non dice perche' (§4.1-bis). */
	registro_dice(REG_CERT,
	              "⭐ rotazione del certificato di SESSIONE: ne restavano %ld "
	              "secondi, il margine e' %d giorni",
	              restano, CERT_MARGINE_GIORNI);
	if (!genera(c->sessione_pem, c->sessione_key, c->sessione_marca,
	            c->indirizzo, CERT_GIORNI_SESSIONE)) {
		registro_dice(REG_CERT, "⛔ rotazione FALLITA: resta il vecchio");
		return false;
	}
	if (!aggiorna_impronta(c))
		return false;
	c->rotazioni++;
	registro_dice(REG_CERT,
	              "⭐ ruotato (rotazioni da quando il server e' acceso: %u).  "
	              "Nuova impronta: %s",
	              c->rotazioni, c->impronta);
	/* ⛔ E la pagina va ritirata di nuovo: chi ha una scheda aperta ha in
	 *    mano l'impronta vecchia, e la strada per aggiornarla e' l'endpoint
	 *    `/impronta` (§4.1-bis).  Qui si dice soltanto che e' successo. */
	return true;
}
