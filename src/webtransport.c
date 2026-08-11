/*
 * webtransport.c — vedi webtransport.h.
 *
 * ⭐ Portato da `banchi/01-b2-ngtcp2-wt-innesta.py`, che lo teneva come `git
 *    diff` sull'albero di ngtcp2.  Le decisioni e le cure che i commenti
 *    dell'innesto documentavano sono qui dentro **con la loro ragione**: sono
 *    difetti gia' pagati, e riscriverli senza la ragione significa ripagarli.
 */
#include "webtransport.h"

#include "rcp.h"
#include "registro.h"

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool rcp_autentica(const char *utente, const char *parola);

/* ------------------------------------------------------------------------ */
/* Le due cose che il C non porta in dote: un vettore di byte e un elenco.    */

typedef struct {
	uint8_t *d;
	size_t n, cap;
} bytes;

static bool bytes_aggiungi(bytes *b, const uint8_t *d, size_t n)
{
	if (n == 0)
		return true;
	if (b->n + n > b->cap) {
		size_t c = b->cap ? b->cap * 2 : 64;
		uint8_t *nuovo;
		while (c < b->n + n)
			c *= 2;
		nuovo = realloc(b->d, c);
		if (!nuovo)
			return false;
		b->d = nuovo;
		b->cap = c;
	}
	memcpy(b->d + b->n, d, n);
	b->n += n;
	return true;
}

static void bytes_togli_testa(bytes *b, size_t n)
{
	if (n >= b->n) {
		b->n = 0;
		return;
	}
	memmove(b->d, b->d + n, b->n - n);
	b->n -= n;
}

static void bytes_libera(bytes *b)
{
	free(b->d);
	b->d = NULL;
	b->n = b->cap = 0;
}

/* ------------------------------------------------------------------------ */

/* Come si classifica uno stream del client. */
enum genere {
	G_INCERTO, /* non si sa ancora che cosa sia: mancano i primi byte */
	G_WT,      /* e' uno stream WebTransport bidirezionale */
	G_NONWT,   /* non lo e': e' di nghttp3 */
	G_UNI_OK,  /* unidirezionale WebTransport, canale lecito ma non servito */
	G_UNI_KO,  /* unidirezionale WebTransport, violazione gia' giudicata */
};

typedef struct {
	int64_t id;
	enum genere genere;
	bytes pref;
} stream_giudizio;

typedef struct {
	int64_t id;
	bytes dati;
	size_t off;
	bool fin;
} uscita;

/* Le richieste HTTP/3: qui ne serve una sola cosa — distinguere la CONNECT
 * estesa di WebTransport da tutto il resto. */
typedef struct {
	int64_t id;
	char metodo[16];
	char protocollo[24];
	char uri[192];
	bool usato;
} richiesta;

struct wt {
	ngtcp2_conn *conn;
	ngtcp2_ccerr *ultimo_errore;
	nghttp3_conn *h3;
	char provenienza[80];

	/* lo stream di controllo di HTTP/3: serve a riconoscerlo in scrittura,
	 * che e' l'unico istante in cui si possa dire al browser che parliamo
	 * WebTransport */
	int64_t ctrl_id;
	bool impostazioni_scritte;
	bool guasto;
	uint8_t impbuf[256];
	size_t impbuf_len;
	/* ⛔ Quanti byte del SETTINGS riscritto sono GIA' USCITI, e quanti byte
	 *    di nghttp3 quel buffer sostituisce.  Servono perche' una scrittura
	 *    PARZIALE e' un esito normale di `ngtcp2_conn_writev_stream` — non
	 *    un guasto — e nell'innesto, prima della cura, uccideva la
	 *    connessione: adesso si riprende dal punto in cui si era arrivati,
	 *    come si fa da sempre per la coda d'uscita. */
	size_t impbuf_off, impbuf_orig;

	stream_giudizio *giudizi;
	size_t ngiudizi, capgiudizi;

	uscita *coda;
	size_t ncoda, capcoda, testa;
	/* ⛔ La coda nostra e' bloccata per QUESTA passata di scrittura: ngtcp2
	 *    ha detto STREAM_DATA_BLOCKED, e riprovare dentro la stessa passata
	 *    sarebbe un ciclo che non avanza. */
	bool coda_bloccata;

	int64_t sessione; /* lo stream della CONNECT estesa: E' la sessione */

	/* i byte della CONNECT che non compongono ancora una capsula intera */
	bytes capsbuf;
	/* ⛔ Quanti byte di una capsula gia' giudicata TROPPO GRANDE restano da
	 *    buttare mentre passano. */
	uint64_t capsalta;

	richiesta *richieste;
	size_t nrichieste, caprichieste;

	/* ═══ RCP sopra WebTransport ════════════════════════════════════════ */
	struct rcp_sessione *rcp;
	int64_t rcp_stream;

	/* ⛔ La chiusura della sessione ASPETTA che la coda d'uscita si sia
	 *    svuotata, e poi ancora un po': vedi `chiudi_sessione()`. */
	int chiusura;
	ngtcp2_tstamp chiusura_da;
	/* ⛔⭐ E L'ATTESA HA UN FONDO — rilievo B-3, 10 agosto 2026 notte.
	 *
	 *     «Aspetta che la coda si svuoti» e' una condizione che qualcuno deve
	 *     far avvenire.  Finche' la coda non si svuota, `wt_batti()` riazzera
	 *     `chiusura_da` a ogni battito e la capsula di §3.1 punto 3 NON PARTE
	 *     MAI: il motivo, che e' «quel che salva le diagnosi», resta dentro il
	 *     server.  ⚠ Un lavoro rimandato a una condizione che nessuno fa piu'
	 *     avvenire non e' rimandato: e' perduto.
	 *
	 * ⭐ Da qui la scadenza: passata quella, la capsula parte lo stesso e la
	 *    rinuncia si SCRIVE. */
	ngtcp2_tstamp chiusura_scadenza;

	/* ⛔⭐ §4.6 — IL TETTO DELLA SESSIONE CHE NON APRE MAI IL CANALE.
	 *
	 * ✅ `DECISIONI.md` §7.17, deciso dall'utente l'11 agosto 2026: **5 s**
	 *    dall'apertura della sessione WebTransport all'apertura del canale di
	 *    controllo, poi `TEMPO_SCADUTO`.
	 *
	 * ⛔ Perche' serviva un orologio in piu': quelli di §4.6 partono
	 *    dall'apertura del CANALE, quindi chi apriva la sessione e il canale
	 *    non lo apriva mai **non aveva addosso nessun tetto**.  `[M]` 11 agosto
	 *    2026, banco B6: la sessione senza canale e' rimasta viva 20 014 ms
	 *    senza che succedesse niente.
	 *
	 * ⚠ E il tempo d'inattivita' di QUIC non lo copriva: quello conta il
	 *   SILENZIO, e una sessione che scrive su un altro stream non e'
	 *   silenziosa — teneva il posto a tempo indeterminato.
	 *
	 * ⛔ Zero quando il canale c'e' gia' (o non c'e' ancora la sessione): un
	 *    orologio che non e' partito e uno che e' scaduto non devono avere la
	 *    stessa faccia. */
	ngtcp2_tstamp canale_entro;

	/* ⛔ Quanti byte ci sono in coda, per il tetto di `coda_metti()`. */
	size_t byte_in_coda;
	/* Quanti stream di troppo (§2.5) hanno gia' scritto: per non riempire il
	 * registro con una riga per pacchetto. */
	uint64_t scartati_stream, scartati_byte;

	/* ⭐ Il NOSTRO orologio, al posto del keep-alive dell'innesto. */
	ngtcp2_tstamp battito;
	uint64_t battito_ms;
	/* ⛔ §4.6: i PING del TRASPORTO mentre si aspettano le credenziali.  Si
	 *    tiene qui se sono accesi, per non richiamare ngtcp2 a ogni battito e
	 *    per poterlo SCRIVERE nel registro quando cambia. */
	bool tienila_viva;
};

/* ------------------------------------------------------------------------ */
/* Gli interi variabili di QUIC (RFC 9000 §16).  Servono tre volte e non ci   */
/* sono in nessuna delle due librerie: nghttp3 il suo se lo tiene per se'.    */

static size_t varint_scrivi(uint8_t *dest, uint64_t v)
{
	if (v < 64) {
		dest[0] = (uint8_t)v;
		return 1;
	}
	if (v < 16384) {
		dest[0] = (uint8_t)(0x40 | (v >> 8));
		dest[1] = (uint8_t)(v & 0xff);
		return 2;
	}
	if (v < 1073741824) {
		dest[0] = (uint8_t)(0x80 | (v >> 24));
		dest[1] = (uint8_t)((v >> 16) & 0xff);
		dest[2] = (uint8_t)((v >> 8) & 0xff);
		dest[3] = (uint8_t)(v & 0xff);
		return 4;
	}
	dest[0] = (uint8_t)(0xc0 | (v >> 56));
	for (size_t i = 1; i < 8; i++)
		dest[i] = (uint8_t)((v >> (8 * (7 - i))) & 0xff);
	return 8;
}

/* ⛔ Restituisce 0 se i byte non bastano: «non lo so ancora» e «zero» sono due
 *    cose diverse, e confonderle e' `LEZIONI.md` §1.9. */
static size_t varint_leggi(uint64_t *v, const uint8_t *src, size_t len)
{
	size_t n;
	if (len == 0)
		return 0;
	n = (size_t)1 << (src[0] >> 6);
	if (len < n)
		return 0;
	*v = src[0] & 0x3f;
	for (size_t i = 1; i < n; i++)
		*v = (*v << 8) | src[i];
	return n;
}

/* ⛔ I due numeri con cui un server dichiara WebTransport, e sono DUE perche'
 *    le bozze in circolazione sono due:
 *
 *      0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   bozza 02
 *      0xc671706a  SETTINGS_WT_MAX_SESSIONS       bozza 07 e oltre
 *
 * ⚠ E la differenza non e' accademica: `aioquic` 1.2 — il cliente di prova —
 *   implementa la 02 `[R]`, mentre i browser di oggi cercano la 07.  Un server
 *   che ne mandasse una sola funzionerebbe con meta' dei nostri strumenti e non
 *   con l'altra meta', e la meta' che funziona sarebbe quella sbagliata da cui
 *   trarre conclusioni.  Si mandano tutt'e due: un'impostazione sconosciuta si
 *   ignora. */
#define WT_ENABLE_WEBTRANSPORT 0x2b603742ULL
#define WT_MAX_SESSIONS 0xc671706aULL

/* ⛔⭐ IL TETTO DI UNA CAPSULA, E SI CONTROLLA PRIMA DI TENERE I BYTE.
 *
 * `RCP.md` §6.1: «un ricevente che alloca `lunghezza` byte e poi verifica ha
 * gia' regalato un megabyte a chiunque sappia scrivere sei byte».  ⚠ Aspettare
 * i byte invece di allocarli e' lo stesso regalo, fatto piu' lentamente.
 *
 * ⭐ Il numero e' quel che serve alla sola capsula che ci riguarda:
 * `CLOSE_WEBTRANSPORT_SESSION` porta un codice a 32 bit e una ragione che
 * WebTransport limita a 1024 byte. */
#define WT_CAPSULA_MAX (1024 + 4)

/* Quanto si aspetta, dopo che la coda si e' svuotata, prima di mandare la
 * capsula che chiude la sessione.  ⭐ Nell'innesto erano «cinque passate di
 * scrittura» col keep-alive a 100 ms, cioe' mezzo secondo: qui il tempo si
 * misura invece di contarlo, e sul filo non va niente. */
#define WT_ATTESA_CHIUSURA_NS (500ULL * NGTCP2_MILLISECONDS)

/* ⛔ §4.6, la riga che mancava: dall'apertura della sessione WebTransport
 *    all'apertura del canale di controllo, **5 s**.
 * ✅ `DECISIONI.md` §7.17, deciso dall'utente l'11 agosto 2026.
 * ⭐ Lo stesso numero del primo tetto di §4.6, e non per simmetria: aprire il
 *    canale e' il primo atto obbligatorio della sessione (§2.5), non dipende
 *    da quanto e' veloce a digitare una persona e non dipende dalla rete piu'
 *    di quanto ne dipenda il `CIAO`. */
#define WT_TETTO_CANALE_NS (5000ULL * NGTCP2_MILLISECONDS)

/* ------------------------------------------------------------------------ */
/* Gli elenchi.                                                              */

static stream_giudizio *giudizio_trova(wt *w, int64_t id)
{
	for (size_t i = 0; i < w->ngiudizi; i++)
		if (w->giudizi[i].id == id)
			return &w->giudizi[i];
	return NULL;
}

static stream_giudizio *giudizio_crea(wt *w, int64_t id)
{
	stream_giudizio *g = giudizio_trova(w, id);
	if (g)
		return g;
	if (w->ngiudizi == w->capgiudizi) {
		size_t c = w->capgiudizi ? w->capgiudizi * 2 : 8;
		stream_giudizio *n = realloc(w->giudizi, c * sizeof *n);
		if (!n)
			return NULL;
		w->giudizi = n;
		w->capgiudizi = c;
	}
	g = &w->giudizi[w->ngiudizi++];
	memset(g, 0, sizeof *g);
	g->id = id;
	g->genere = G_INCERTO;
	return g;
}

static richiesta *richiesta_trova(wt *w, int64_t id, bool crea)
{
	for (size_t i = 0; i < w->nrichieste; i++)
		if (w->richieste[i].usato && w->richieste[i].id == id)
			return &w->richieste[i];
	if (!crea)
		return NULL;
	for (size_t i = 0; i < w->nrichieste; i++)
		if (!w->richieste[i].usato) {
			memset(&w->richieste[i], 0, sizeof w->richieste[i]);
			w->richieste[i].id = id;
			w->richieste[i].usato = true;
			return &w->richieste[i];
		}
	if (w->nrichieste == w->caprichieste) {
		size_t c = w->caprichieste ? w->caprichieste * 2 : 8;
		richiesta *n = realloc(w->richieste, c * sizeof *n);
		if (!n)
			return NULL;
		w->richieste = n;
		w->caprichieste = c;
	}
	{
		richiesta *r = &w->richieste[w->nrichieste++];
		memset(r, 0, sizeof *r);
		r->id = id;
		r->usato = true;
		return r;
	}
}

static uscita *coda_prima(wt *w)
{
	if (w->testa >= w->ncoda)
		return NULL;
	return &w->coda[w->testa];
}

static void coda_togli(wt *w)
{
	if (w->testa >= w->ncoda)
		return;
	if (w->byte_in_coda >= w->coda[w->testa].dati.n)
		w->byte_in_coda -= w->coda[w->testa].dati.n;
	else
		w->byte_in_coda = 0;
	bytes_libera(&w->coda[w->testa].dati);
	w->testa++;
	if (w->testa == w->ncoda)
		w->testa = w->ncoda = 0;
}

static bool coda_vuota(const wt *w) { return w->testa >= w->ncoda; }

/* ⛔ IL TETTO DELLA CODA D'USCITA — rilievo B-3 punto 4, 10 agosto 2026 notte.
 *
 * `coda_metti()` e `bytes_aggiungi()` raddoppiavano senza limite: la memoria
 * del processo cresceva quanto il client voleva, e cresceva **su una sessione
 * gia' dichiarata morta**.  ⚠ Un tetto che non c'e' non e' un tetto alto: e'
 * un limitatore assente, e non lo vede nessuno finche' la macchina non finisce
 * la memoria.
 *
 * ⭐ Il numero: due messaggi RCP al massimo (§6.1, 1 MiB l'uno) piu' un po' di
 *    margine.  Il canale di controllo di questa fase manda `ECCOMI`,
 *    `AMMESSO`/`RESPINTO`, `SESSIONE` e `CONGEDO`, che stanno tutti in
 *    qualche centinaio di byte: se questo tetto viene toccato, e' successo
 *    qualcosa che va guardato — e infatti si scrive.  ⛔ E chi lo tocca NON
 *    prosegue in silenzio: vedi `accoda()` e il rilievo B-15. */
#define WT_CODA_MAX (2u * 1024u * 1024u)

static bool coda_metti(wt *w, int64_t id, const uint8_t *d, size_t n, bool fin)
{
	uscita *u;
	if (w->byte_in_coda + n > WT_CODA_MAX) {
		registro_dice(REG_WT,
		              "⛔ la coda d'uscita ha toccato il tetto (%zu byte in "
		              "coda + %zu, tetto %u): non accodo",
		              w->byte_in_coda, n, WT_CODA_MAX);
		return false;
	}
	if (w->ncoda == w->capcoda) {
		if (w->testa > 0) {
			memmove(w->coda, w->coda + w->testa,
			        (w->ncoda - w->testa) * sizeof *w->coda);
			w->ncoda -= w->testa;
			w->testa = 0;
		}
		if (w->ncoda == w->capcoda) {
			size_t c = w->capcoda ? w->capcoda * 2 : 8;
			uscita *nu = realloc(w->coda, c * sizeof *nu);
			if (!nu)
				return false;
			w->coda = nu;
			w->capcoda = c;
		}
	}
	u = &w->coda[w->ncoda++];
	memset(u, 0, sizeof *u);
	u->id = id;
	u->fin = fin;
	if (!bytes_aggiungi(&u->dati, d, n)) {
		w->ncoda--;
		return false;
	}
	w->byte_in_coda += n;
	return true;
}

/* ⛔⭐ E I BYTE NON SI BUTTANO: QUESTO E' UN CANALE AFFIDABILE — rilievo B-15,
 *     10 agosto 2026 notte.
 *
 *     Questa funzione scriveva una riga nel registro e **proseguiva**.  Il
 *     chiamante — `manda_controllo()`, cioe' la strada di TUTTI i messaggi RCP
 *     — non riceveva nessun esito: RCP credeva di aver mandato `ECCOMI`,
 *     passava a `attesa-credenziali`, e il messaggio successivo si sarebbe
 *     saldato al nulla lasciato dal primo.  ⛔ Il client avrebbe letto
 *     un'inquadratura che il server non ha mai voluto scrivere: sarebbe stato
 *     il SERVER a fabbricare la violazione del client.
 *
 *     ⚠ E' la stessa lezione del riquadro di `STREAM_DATA_BLOCKED` piu' sotto,
 *       applicata all'altra delle due strade per cui i byte si possono
 *       perdere.  La cura di allora era stata messa su una sola.
 *
 * ⭐ La cura: chi non riesce ad accodare NON prosegue.  Si dichiara guasto lo
 *    strato, e `wt_scrivi()` fa morire la connessione QUIC alla prima passata.
 *    ⛔ Una connessione che muore e' inequivocabile; un messaggio saldato a
 *    meta' manda a cercare il difetto nel client.  ⚠ Il motivo di §3.1 non
 *    puo' viaggiare: se la coda non prende sei byte non prende nemmeno la
 *    capsula, e questa riga di registro e' l'unico posto in cui il fatto
 *    compare.  Si scrive perche' e' l'unico. */
static bool accoda(wt *w, int64_t id, const uint8_t *d, size_t n)
{
	if (coda_metti(w, id, d, n, false))
		return true;
	registro_dice(REG_WT,
	              "⛔⛔ %zu byte per lo stream %ld NON entrano in coda: la "
	              "sessione NON prosegue.  Un canale affidabile non butta i "
	              "byte, e mezzo messaggio sul filo sarebbe una violazione "
	              "fabbricata dal server (§6.1)",
	              n, (long)id);
	w->guasto = true;
	return false;
}

/* ------------------------------------------------------------------------ */

static void batti_fra(wt *w, uint64_t ms)
{
	w->battito_ms = ms;
	w->battito = ngtcp2_conn_get_timestamp(w->conn) + ms * NGTCP2_MILLISECONDS;
}

ngtcp2_tstamp wt_battito_ns(const wt *w)
{
	return w->battito_ms ? w->battito : UINT64_MAX;
}

const char *wt_stato_rcp(const wt *w)
{
	return w->rcp ? rcp_stato_nome(w->rcp) : "(nessuna)";
}

/* ⛔ PERCHE' ha ancora da dire — e non e' un lusso: senza questa riga
 *    «la capsula di chiusura non e' ancora matura» e «i byte non escono» hanno
 *    la stessa faccia, e chi spegne il servizio legge «1 sessioni hanno ancora
 *    byte in coda» senza sapere quale delle due sia.
 * ⚠ `[M]` 11 agosto 2026: il caso `server-in-chiusura` di B7 e' rosso proprio
 *   qui — §3.1 punto 3 assente allo spegnimento — e la diagnosi si e' fermata
 *   davanti a questa ambiguita'. */
const char *wt_perche_ha_da_dire(const wt *w)
{
	if (!w)
		return "(nessuna sessione)";
	if (w->chiusura >= 0 && !coda_vuota(w))
		return "capsula di chiusura in attesa E coda non vuota";
	if (w->chiusura >= 0)
		return "capsula di chiusura non ancora matura (coda vuota)";
	if (!coda_vuota(w))
		return "coda d'uscita non vuota";
	return "niente";
}

bool wt_ha_da_dire(const wt *w)
{
	return w->chiusura >= 0 || !coda_vuota(w);
}

/* ------------------------------------------------------------------------ */
/* 1. La riscrittura del SETTINGS.                                           */

static size_t riscrivi_impostazioni(wt *w, const nghttp3_vec *vec, size_t veccnt)
{
	uint8_t orig[512];
	size_t origlen = 0;
	uint64_t tipo_stream = 0, tipo_frame = 0, lung = 0;
	size_t n, p, o;
	uint8_t aggiunta[64], testa[16];
	size_t a = 0, t = 0;

	for (size_t i = 0; i < veccnt; i++) {
		if (origlen + vec[i].len > sizeof orig) {
			registro_dice(REG_WT,
			              "⛔ il SETTINGS di nghttp3 e' piu' lungo di "
			              "%zu byte: non lo riscrivo",
			              sizeof orig);
			return 0;
		}
		memcpy(orig + origlen, vec[i].base, vec[i].len);
		origlen += vec[i].len;
	}
	if (origlen < 3)
		return 0;

	/* ⛔ Ogni passo ha un appiglio, e se l'appiglio non c'e' NON si riscrive
	 *    alla cieca: si dice e si lascia stare.  Il server restera' senza
	 *    WebTransport, e la misura lo vedra' subito — che e' quel che
	 *    `DECISIONI.md` §6.4 chiede di riprovare a ogni aggiornamento di
	 *    nghttp3. */
	n = varint_leggi(&tipo_stream, orig, origlen);
	if (n == 0 || tipo_stream != 0x00) {
		registro_dice(REG_WT,
		              "⛔ lo stream di controllo non comincia per 0x00 (e' "
		              "%llu): non tocco niente",
		              (unsigned long long)tipo_stream);
		return 0;
	}
	p = n;

	n = varint_leggi(&tipo_frame, orig + p, origlen - p);
	if (n == 0 || tipo_frame != 0x04) {
		registro_dice(REG_WT, "⛔ il primo frame non e' SETTINGS (e' %llu)",
		              (unsigned long long)tipo_frame);
		return 0;
	}
	p += n;

	n = varint_leggi(&lung, orig + p, origlen - p);
	if (n == 0)
		return 0;
	p += n;

	if (p + lung != origlen) {
		/* C'e' altro dopo SETTINGS, oppure SETTINGS e' arrivato a pezzi. */
		registro_dice(REG_WT, "⛔ SETTINGS non e' tutto qui (%zu + %llu != %zu)",
		              p, (unsigned long long)lung, origlen);
		return 0;
	}

	a += varint_scrivi(aggiunta + a, WT_ENABLE_WEBTRANSPORT);
	a += varint_scrivi(aggiunta + a, 1);
	a += varint_scrivi(aggiunta + a, WT_MAX_SESSIONS);
	a += varint_scrivi(aggiunta + a, 1);

	t += varint_scrivi(testa + t, 0x00); /* il tipo dello stream */
	t += varint_scrivi(testa + t, 0x04); /* SETTINGS */
	t += varint_scrivi(testa + t, lung + a);

	if (t + lung + a > sizeof w->impbuf) {
		registro_dice(REG_WT, "⛔ SETTINGS troppo grande per il buffer");
		return 0;
	}

	o = 0;
	memcpy(w->impbuf + o, testa, t);
	o += t;
	memcpy(w->impbuf + o, orig + p, (size_t)lung);
	o += (size_t)lung;
	memcpy(w->impbuf + o, aggiunta, a);
	o += a;
	w->impbuf_len = o;

	registro_dice(REG_WT,
	              "⭐ SETTINGS riscritto — %zu byte di nghttp3 + %zu nostri "
	              "(ENABLE_WEBTRANSPORT e WT_MAX_SESSIONS)",
	              origlen, a);
	return origlen;
}

/* ------------------------------------------------------------------------ */
/* RCP: i quattro ganci, che sono l'unica cosa che il protocollo sa del mondo */
/* di sotto.                                                                  */

static void manda_controllo(wt *w, const uint8_t *dati, size_t len);
static void chiudi_sessione(wt *w, uint8_t motivo);

static void gancio_manda(void *ctx, const uint8_t *dati, size_t len)
{
	manda_controllo((wt *)ctx, dati, len);
}

static void gancio_chiudi(void *ctx, uint8_t motivo)
{
	chiudi_sessione((wt *)ctx, motivo);
}

static void gancio_registra(void *ctx, const char *riga)
{
	(void)ctx;
	registro_dice(REG_RCP, "%s", riga);
}

static bool gancio_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	/* ⚠ PAM BLOCCA, e qui blocca il ciclo intero: la stretta di mano di un
	 *   utente ferma quella di tutti gli altri e ritarda i pacchetti di
	 *   chiunque sia gia' collegato.  ⛔ E' un ripiego dichiarato della fase
	 *   1 (`CODER.md` §4.2, §4.4): la verifica va su un filo a parte prima
	 *   che il server serva piu' di una persona (`SPECIFICHE.md` §5.5).
	 *   Costa meno di un secondo per tentativo, e §4.4-bis ne impone gia'
	 *   uno di ritardo fisso — ma «meno di un secondo» non e' «non blocca». */
	return rcp_autentica(utente, parola);
}

/* ⛔⭐ I PING DEL TRASPORTO MENTRE SI ASPETTANO LE CREDENZIALI — `RCP.md` §4.6,
 *     riquadro R1.8, che e' normativo e comincia con un ⛔.  Rilievo B-2, curato
 *     il 10 agosto 2026 notte.
 *
 * ⛔ IL DIFETTO, per esteso, perche' e' il documento a descriverlo parola per
 *    parola.  §4.6 da' 60 secondi fra `ECCOMI` spedito e `CREDENZIALI`
 *    ricevute — «e' il tempo in cui una persona digita la parola d'ordine».  In
 *    quei 60 secondi sul filo NON PASSA NIENTE: §2.2 vieta il battito
 *    applicativo, e prima dell'attacco non c'e' nessun altro canale attivo.  Al
 *    trentesimo secondo matura l'inattivita' di QUIC (`IDLE_MS`), la
 *    connessione muore IN SILENZIO — nessun `CONGEDO`, nessun codice, nessun
 *    motivo di §8.2 — e `TETTO_CREDENZIALI` non scade mai, perche' la sessione
 *    RCP e' gia' stata liberata trenta secondi prima.
 *
 *    ⚠ Chi ci cade: chi digita piano, cioe' chi digita su un telefono.  Difetto
 *      intermittente, il peggiore da diagnosticare — e il banco misurerebbe 30
 *      dove il documento dice 60, dando la colpa al banco.
 *
 * ⛔ E `wt_battito_ns()` NON E' LA CURA, ed e' il punto: fa scorrere l'orologio
 *    NOSTRO ogni 100 ms e per i tetti di §4.6 va benissimo, ⛔ ma non mette un
 *    byte sul filo — e l'orologio che uccide la connessione e' quello di QUIC,
 *    che guarda i byte.  Il riquadro di `webtransport.h` presentava l'assenza
 *    del keep-alive come un miglioramento sull'innesto citando §2.2: §4.6
 *    distingue esplicitamente le due cose — i PING del trasporto «non portano
 *    informazione, non hanno una risposta da interpretare, e non creano una
 *    seconda verita' sul silenzio» — e il divieto di §2.2 NON li copre.
 *
 * ⭐ 10 secondi, e non 25: il PING deve avere il tempo di essere ritrasmesso
 *    almeno una volta prima che i 30 maturino.  Un keep-alive tarato al pelo
 *    del tetto e' un keep-alive che il primo pacchetto perso rende inutile.
 *
 * ⛔ E SI SPEGNE FUORI DA QUELLA FINESTRA, che e' la meta' che nessuno scrive.
 *    Tenere viva la connessione SEMPRE cambierebbe il significato dei 30
 *    secondi di §2.2 — «l'orologio del silenzio: scaduto, il client e'
 *    staccato» — e §4.6 la cura la chiede per UN tetto solo, l'unico dei tre
 *    che sia piu' lungo dell'inattivita' (60 > 30; gli altri due sono 5 e 10).
 *
 * ⚠ E un client MORTO muore lo stesso: RFC 9000 §10.1 rimette in moto il
 *   cronometro dell'inattivita' quando si RICEVE un pacchetto, non quando lo si
 *   manda.  I nostri PING tengono viva una connessione con qualcuno che
 *   risponde, non una con nessuno. */
#define WT_TIENILA_VIVA_NS (10ULL * NGTCP2_SECONDS)

static void regola_tienila_viva(wt *w, const char *stato)
{
	/* ⚠ Il nome dello stato e' il contratto: `rcp.h` li elenca tutti e sette
	 *   per iscritto, e dice che chi li confronta deve saperlo. */
	bool serve = stato && strcmp(stato, "attesa-credenziali") == 0;

	if (serve == w->tienila_viva)
		return;
	w->tienila_viva = serve;
	ngtcp2_conn_set_keep_alive_timeout(w->conn,
	                                   serve ? WT_TIENILA_VIVA_NS : UINT64_MAX);
	registro_dice(REG_WT,
	              serve ? "⭐ PING del trasporto ACCESI ogni 10 s con %s: §4.6 "
	                      "da' 60 s per digitare la parola d'ordine e "
	                      "l'inattivita' di QUIC ne da' 30"
	                    : "PING del trasporto spenti con %s: la finestra delle "
	                      "credenziali e' chiusa, e i 30 s di §2.2 tornano a "
	                      "essere l'orologio del silenzio",
	              w->provenienza);
}

static void regola_battito(wt *w)
{
	const char *stato = w->rcp ? rcp_stato_nome(w->rcp) : NULL;

	regola_tienila_viva(w, stato);

	if (!stato) {
		/* Nessuna sessione RCP: si batte se c'e' una chiusura da far
		 * maturare — ⛔ **oppure se il tetto di §7.17 e' armato**.
		 *
		 * ⛔ E' qui che la prima stesura del tetto moriva, `[M]` 11 agosto
		 *    2026 col banco B6: `cb_end_headers` armava `canale_entro` e
		 *    chiamava `batti_fra`, e poi la prima passata di questa funzione
		 *    rimetteva `battito_ms = 0`.  Il tetto scattava solo se il client
		 *    faceva qualcos'altro che risvegliasse il battito — cioe'
		 *    **proprio nel caso che non serve**: `ciao-sessione-tardiva`
		 *    scadeva a 5,10 s, `ciao-senza-controllo` restava appeso 20 s.
		 *
		 * ⚠ E' la lezione scritta trenta righe piu' sotto, presa in flagrante
		 *   nel giro stesso in cui la si applicava: **chi mette un tetto deve
		 *   accendere anche cio' che lo fara' scadere** — e non basta
		 *   accenderlo, bisogna che nessun altro lo spenga. */
		if (w->chiusura >= 0 || w->canale_entro)
			batti_fra(w, 100);
		else
			w->battito_ms = 0;
		return;
	}
	if (strcmp(stato, "attiva") == 0) {
		/* ⭐ L'orologio del silenzio di `SPECIFICHE.md` §5.3 va valutato
		 *    MENTRE il client tace, e mentre tace nessuno percorrerebbe
		 *    il percorso di scrittura.  Un secondo di granularita' su
		 *    trenta e' abbondante. */
		batti_fra(w, 1000);
		return;
	}
	/* ⛔ `attesa-verdetto` vuole il battito perche' il ritardo fisso di
	 *    §4.4-bis dura un secondo e in quel secondo non c'e' niente da
	 *    spedire; gli altri stati della stretta di mano perche' i tre tetti
	 *    di §4.6 devono poter scadere anche se il client tace.
	 *
	 * ⛔⭐ E QUESTA E' LA LEZIONE PIU' CARA DELL'INNESTO, in due vesti:
	 *      `[M]` 10 agosto 2026, B6 e B5.  Chi mette un tetto deve accendere
	 *      anche cio' che lo fara' scadere, NELL'ISTANTE in cui il tetto
	 *      comincia — non alla prima occasione utile che capita dopo.  Un
	 *      lavoro rimandato a una condizione che nessuno fa piu' avvenire
	 *      non e' rimandato: e' perduto, e nel registro somiglia a un lavoro
	 *      non chiesto. */
	batti_fra(w, 100);
}

static void rcp_avvia(wt *w, int64_t stream_id)
{
	rcp_ganci g;

	w->rcp_stream = stream_id;

	memset(&g, 0, sizeof g);
	g.ctx = w;
	g.manda = gancio_manda;
	g.chiudi = gancio_chiudi;
	g.registra = gancio_registra;
	g.verifica = gancio_verifica;

	/* ⛔ E il tetto di §7.17 si SPEGNE qui: il canale e' stato aperto, che e'
	 *    la cosa che quell'orologio aspettava.  ⚠ Zero e non «passato»: un
	 *    orologio disarmato e uno scaduto non devono avere la stessa faccia. */
	w->canale_entro = 0;

	w->rcp = rcp_apri(&g, w->provenienza,
	                  ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);

	/* ⛔ E QUI SI ARMA L'OROLOGIO DEL PRIMO TETTO — §4.6 riga 1.  `rcp_apri`
	 *    mette lo stato a `attesa-ciao` e fa partire il cronometro: il
	 *    cronometro e l'orologio che lo fara' scadere partono dalla stessa
	 *    riga.  Nell'innesto questo mancava, e un client che apriva il canale
	 *    e poi taceva restava appeso per sempre (`[M]` B6). */
	regola_battito(w);
	registro_dice(REG_RCP, "canale di controllo = stream %ld", (long)stream_id);
}

static void rcp_passa(wt *w, const uint8_t *dati, size_t len)
{
	uint64_t ora;
	if (!w->rcp)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi(w->rcp, dati, len, ora)) {
		/* La sessione e' finita.  Il battito che fa maturare la capsula
		 * di chiusura lo ha gia' armato `chiudi_sessione()`, che e'
		 * l'unico punto attraversato da TUTTE le strade della chiusura —
		 * comprese le due che da qui non passano affatto. */
		return;
	}
	regola_battito(w);
}

/* ------------------------------------------------------------------------ */
/* La chiusura della sessione WebTransport.                                  */

static void chiudi_adesso(wt *w, uint8_t motivo)
{
	uint8_t b[16];
	size_t n = 0;

	/* ⛔⭐ LA CAPSULA VA DENTRO UN FRAME `DATA`, E NELL'INNESTO USCIVA NUDA.
	 *
	 *    Il corpo di una CONNECT estesa e' un flusso di capsule (RFC 9297),
	 *    ma in HTTP/3 il corpo di un messaggio viaggia dentro frame `DATA`:
	 *    la capsula NON sta nuda sullo stream.  ⭐ E che il client le
	 *    incapsuli lo dimostra il nostro stesso lato di LETTURA: la capsula
	 *    ci arriva da `recv_data`, che nghttp3 invoca soltanto sul carico
	 *    utile di un `DATA`.
	 *
	 * ⛔ Scritti nudi, i sette byte `68 43 04 00 00 00 mm` il browser li
	 *    legge col proprio strato HTTP/3: `0x68` ha i due bit alti a `01`,
	 *    quindi e' un intero variabile di due byte, e il tipo di frame
	 *    diventa `0x2843` — che non e' un tipo di frame HTTP/3 noto, e RFC
	 *    9114 §9 impone di IGNORARLO.  La pagina non vedeva nessuna capsula:
	 *    vedeva solo il FIN che arriva subito dietro, e un FIN sullo stream
	 *    della CONNECT senza `CLOSE_WEBTRANSPORT_SESSION` chiude la sessione
	 *    con codice 0 — cioe' il solo valore che `RCP.md` §3.1 vieta. */
	b[n++] = 0x00; /* frame DATA */
	b[n++] = 7;    /* 2 byte di tipo + 1 di lunghezza + 4 di codice */
	b[n++] = 0x68; /* 0x2843, primo byte dell'intero variabile */
	b[n++] = 0x43;
	b[n++] = 4; /* la lunghezza della capsula: solo il codice */
	b[n++] = 0;
	b[n++] = 0;
	b[n++] = 0;
	b[n++] = motivo;

	if (!coda_metti(w, w->sessione, b, n, true)) {
		registro_dice(REG_WT, "⛔ la capsula di chiusura non entra in coda");
		return;
	}
	registro_dice(REG_WT,
	              "chiusa la sessione WebTransport, codice 0x%02x (%zu byte: "
	              "2 di frame DATA + 7 di capsula)",
	              motivo, n);
}

static void chiudi_sessione(wt *w, uint8_t motivo)
{
	/* ⛔ `RCP.md` §3.1 punto 3: si chiude la SESSIONE WebTransport con il
	 *    codice d'errore applicativo pari al codice del motivo — non la
	 *    connessione QUIC, che puo' reggere altro. */
	if (w->sessione == -1)
		return;

	/* ⛔⭐ E LA CAPSULA SI RIMANDA, invece di accodarla adesso — trovato da
	 *     B11 il 10 agosto 2026, con browser veri.
	 *
	 *     `respingi()` manda `RESPINTO` sul canale di controllo e chiude la
	 *     sessione nella riga dopo.  I due finivano nella stessa passata di
	 *     scrittura, cioe' spesso nello stesso volo di pacchetti — e il
	 *     browser processa la capsula `CLOSE_WEBTRANSPORT_SESSION` PRIMA dei
	 *     byte dello stream, che a quel punto butta.  ⛔ La pagina non ha
	 *     mai visto `RESPINTO`: ha visto silenzio.
	 *
	 * ⛔ E ACCODARE LA CAPSULA DIETRO AL `CONGEDO`, NELLA STESSA CODA, NON E'
	 *    LA CURA: l'ordine sul filo ci sarebbe, ⚠ ma l'ordine sul filo non e'
	 *    quel che manca.  Quel che serve e' TEMPO fra i due. */
	w->chiusura = motivo;
	w->chiusura_da = 0;
	/* ⛔ E L'ATTESA HA UN FONDO — rilievo B-3.  «Quando la coda si sara'
	 *    svuotata» e' una condizione che qualcun altro deve far avvenire; se
	 *    non avviene, il punto 3 di §3.1 non si esegue mai e il motivo resta
	 *    dentro il server.  Tre secondi sono sei volte l'attesa normale. */
	w->chiusura_scadenza =
	    ngtcp2_conn_get_timestamp(w->conn) + 3ULL * NGTCP2_SECONDS;
	/* ⛔ E chi rimanda un lavoro deve accendere anche cio' che lo fara'
	 *    maturare: senza questo battito, su una violazione trovata al primo
	 *    messaggio il client tace, nessuno ripassa di qui e la capsula non
	 *    parte mai.  ⚠ E' il difetto misurato da B5 — 22 su 36. */
	batti_fra(w, 100);
	registro_dice(REG_WT,
	              "chiusura della sessione RIMANDATA, codice 0x%02x (in coda: "
	              "%zu elementi)",
	              motivo, w->ncoda - w->testa);
}

static void manda_controllo(wt *w, const uint8_t *dati, size_t len)
{
	if (w->rcp_stream == -1)
		return;
	(void)accoda(w, w->rcp_stream, dati, len);
}

/* ⛔⭐ I BYTE DI UNO STREAM DI TROPPO SI BUTTANO, E NON SI RIMANDANO INDIETRO
 *     — rilievo B-3, 10 agosto 2026 notte.
 *
 *     Qui c'era `accoda(w, stream_id, dati, len)`, cioe' il server rispediva
 *     al client i suoi stessi byte su uno stream che due righe piu' su aveva
 *     appena giudicato una **violazione di §2.5**.  ⛔ Un'eco che nessuna riga
 *     di `RCP.md` prevede, e tre conseguenze una peggiore dell'altra:
 *
 *       1. `coda_vuota()` non tornava mai vera, quindi la capsula di chiusura
 *          di §3.1 punto 3 non partiva mai (vedi `chiusura_scadenza`);
 *       2. `conta_credito()` riapriva la finestra a ogni giro, quindi il
 *          client poteva scrivere senza fine — e l'inattivita' di 30 s non
 *          scattava, perche' stava scrivendo;
 *       3. la coda cresceva quanto il client voleva, su una sessione gia'
 *          dichiarata morta (vedi `WT_CODA_MAX`).
 *
 * ⭐ Quel che si fa invece: si butta, NON si riapre il credito, e §3 lo impone
 *    — «e ogni tolleranza va scritta nel registro».  ⚠ Le righe sono contate e
 *    non una per pacchetto: un client che scrive senza fine riempirebbe il
 *    registro, che e' un altro modo di perdere l'informazione. */
static void scarta_stream_di_troppo(wt *w, int64_t stream_id, size_t len)
{
	w->scartati_stream++;
	w->scartati_byte += len;
	if (w->scartati_stream <= 3 || (w->scartati_stream % 256) == 0)
		registro_dice(REG_WT,
		              "⛔ %zu byte BUTTATI dallo stream %ld: non e' il canale "
		              "di controllo (§2.5, la violazione e' gia' a verbale) — "
		              "%llu blocchi, %llu byte in tutto, e il credito NON si "
		              "riapre",
		              len, (long)stream_id,
		              (unsigned long long)w->scartati_stream,
		              (unsigned long long)w->scartati_byte);
}

/* ------------------------------------------------------------------------ */
/* Le capsule che arrivano dal client.                                       */

static void chiusa_dal_client(wt *w, uint32_t codice)
{
	bool valido;
	uint8_t motivo;

	/* ⛔⭐ E PRIMA DI TUTTO SI GUARDA SE QUEL CODICE ESISTE.
	 *
	 *    `RCP.md` §3.1: il codice 0 significa «chiusura senza motivo» e NON
	 *    DEVE essere usato — ogni chiusura ha un motivo di §8.2.  E §3 — la
	 *    regola di rigore — chiede di scrivere NEL REGISTRO che cosa non si
	 *    e' capito, non di supplire in silenzio.
	 *
	 * ⛔ E IL CODICE ARRIVA SU 32 BIT, NON SU 8: troncarlo al byte basso
	 *    faceva entrare a verbale `0x0100` come `0x00`, cioe' come il solo
	 *    valore che §3.1 vieta, e i due registri della STESSA chiusura si
	 *    contraddicevano a due righe di distanza. */
	valido = codice >= (uint32_t)RCP_CHIUSO_DALL_UTENTE &&
	         codice <= (uint32_t)RCP_GIA_ATTIVA_REMOTA;
	if (!valido)
		registro_dice(REG_RCP,
		              "⛔ VIOLAZIONE §3.1 — la pagina ha chiuso la sessione "
		              "col codice 0x%x, che non e' un motivo di §8.2 "
		              "(0 = «senza motivo», ed e' vietato).  A verbale va "
		              "ERRORE_PROTOCOLLO",
		              codice);
	motivo = (uint8_t)(valido ? codice : (uint32_t)RCP_ERRORE_PROTOCOLLO);

	if (w->rcp && rcp_e_finita(w->rcp))
		registro_dice(REG_RCP,
		              "⭐ il motivo e' arrivato per la seconda strada di "
		              "§3.1 (il codice di chiusura): 0x%02x — i byte sul "
		              "canale non erano piu' spedibili",
		              motivo);
	/* ⛔ E il POSTO si lascia adesso: §4.2, la sessione e' finita perche' lo
	 *    dice il client.  Aspettare lo smontaggio del trasporto vuol dire
	 *    tenerlo occupato addosso a chi si ricollega subito. */
	if (w->rcp)
		rcp_chiusa_dal_client(w->rcp, motivo);
}

/* ⛔⭐ Il corpo di una CONNECT estesa e' un flusso di capsule (RFC 9297):
 * varint tipo, varint lunghezza, corpo.  Di tutte, qui se ne guarda UNA:
 * `CLOSE_WEBTRANSPORT_SESSION` (0x2843).  ⚠ Si accumula, perche' una capsula
 * puo' arrivare a pezzi; e si scarta il resto senza rumore, perche' un flusso
 * di capsule sconosciute non e' un errore (RFC 9297 §3.2). */
static void capsula(wt *w, int64_t stream_id, const uint8_t *dati, size_t len)
{
	if (stream_id != w->sessione || len == 0)
		return;

	/* ⛔ I byte di una capsula gia' giudicata troppo grande si buttano
	 *    MENTRE PASSANO, senza tenerli: e' l'unico modo di non farsi
	 *    riempire la memoria da chi sa scrivere due interi variabili. */
	if (w->capsalta > 0) {
		uint64_t n = w->capsalta < len ? w->capsalta : (uint64_t)len;
		w->capsalta -= n;
		dati += n;
		len -= (size_t)n;
		if (len == 0)
			return;
	}
	if (!bytes_aggiungi(&w->capsbuf, dati, len))
		return;

	for (;;) {
		uint64_t tipo = 0, lung = 0;
		size_t a, b;
		const uint8_t *corpo;

		/* ⚠ Qui il buffer non puo' crescere senza fine: un intero
		 *   variabile e' al massimo 8 byte, quindi con 16 byte tipo e
		 *   lunghezza si leggono sempre. */
		a = varint_leggi(&tipo, w->capsbuf.d, w->capsbuf.n);
		if (a == 0)
			return;
		b = varint_leggi(&lung, w->capsbuf.d + a, w->capsbuf.n - a);
		if (b == 0)
			return;

		/* ⛔⭐ E LA LUNGHEZZA SI CONTROLLA QUI, PRIMA DI ASPETTARE I BYTE.
		 *
		 *    L'ingresso che questo chiude: la pagina manda, sullo stream
		 *    della CONNECT, un tipo di capsula sconosciuto e una
		 *    lunghezza di 2^62-1, poi manda dati all'infinito.  Nessuna
		 *    capsula si completava mai, il buffer cresceva di ogni byte
		 *    che arrivava — e il credito continuava ad allargarsi, quindi
		 *    il client poteva spedire senza fine.  ⛔ Su una connessione
		 *    che non ha ancora superato la stretta di mano di RCP. */
		if (lung > WT_CAPSULA_MAX) {
			uint64_t qui = w->capsbuf.n - a - b;
			uint64_t presi = qui < lung ? qui : lung;
			registro_dice(REG_WT,
			              "capsula 0x%llx lunga %llu byte, oltre il "
			              "tetto di %d: si SALTA senza tenerla (RFC "
			              "9297 §3.2; RCP.md §6.1)",
			              (unsigned long long)tipo,
			              (unsigned long long)lung, WT_CAPSULA_MAX);
			w->capsalta = lung - presi;
			bytes_togli_testa(&w->capsbuf, a + b + (size_t)presi);
			if (w->capsalta > 0)
				return;
			continue;
		}
		if (w->capsbuf.n < a + b + lung)
			return; /* sta sotto il tetto: si puo' aspettare */

		corpo = w->capsbuf.d + a + b;
		if (tipo == 0x2843 && lung >= 4) {
			uint32_t codice = ((uint32_t)corpo[0] << 24) |
			                  ((uint32_t)corpo[1] << 16) |
			                  ((uint32_t)corpo[2] << 8) |
			                  (uint32_t)corpo[3];
			registro_dice(REG_WT,
			              "la pagina ha CHIUSO la sessione "
			              "WebTransport: codice 0x%x",
			              codice);
			chiusa_dal_client(w, codice);
		}
		bytes_togli_testa(&w->capsbuf, a + b + (size_t)lung);
	}
}

/* ------------------------------------------------------------------------ */
/* Lo smistamento: che cosa e' WebTransport e che cosa e' di nghttp3.        */

/* ⛔ `RCP.md` §4.2: «un FIN su quello stream, da una qualunque delle due parti,
 *    chiude la sessione.  Chi lo riceve DEVE considerarla finita».  ⚠ Era
 *    l'unica delle due direzioni che nessuno aveva percorso: la pagina che
 *    chiude la parte scrivente del canale e tiene viva la connessione lasciava
 *    il posto del registro occupato finche' non moriva la connessione — e una
 *    connessione un browser la tiene viva. */
static void fin_dal_client(wt *w, int64_t stream_id)
{
	if (!w->rcp || stream_id != w->rcp_stream)
		return;
	registro_dice(REG_RCP,
	              "⛔ FIN del CLIENT sul canale di controllo (stream %ld): "
	              "§4.2, la sessione e' finita",
	              (long)stream_id);
	rcp_canale_chiuso(w->rcp);
}

static void conta_credito(wt *w, int64_t stream_id, size_t n)
{
	if (n == 0)
		return;
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, n);
	ngtcp2_conn_extend_max_offset(w->conn, n);
}

enum esito { E_MIO, E_ATTENDI, E_HTTP3 };

/* ⛔ `RCP.md` §2.5 — gli stream unidirezionali aperti dal CLIENT.
 *
 * ⭐ Come si riconosce il canale: «si leggono i primi due byte dello stream,
 *    che sono in ogni caso un campo `tipo`».  Il byte alto dice il canale, e di
 *    cinque valori leciti TRE sono violazioni quando arrivano di qui:
 *
 *    0x00  controllo  ⛔ il controllo vive solo sul primo bidirezionale
 *    0x01  input      ✓  legale: e' l'unico unidirezionale che il client apre
 *    0x02  appunti    ✓  legale, uno per trasferimento
 *    0x03  video      ⛔ verso sbagliato: il video va dal server al client
 *    0x04  audio      ⛔ «solo su datagram.  Su uno stream e' ERRORE_PROTOCOLLO»
 *
 * ⚠ E prima ancora bisogna sapere se lo stream e' NOSTRO: fra gli
 *   unidirezionali del client ci sono il canale di controllo di HTTP/3 e i due
 *   di QPACK, che sono di nghttp3.  Uno stream WebTransport si riconosce dal
 *   suo tipo, 0x54 — che come 0x41 non sta in un byte: sul filo sono 0x40 0x54. */
static enum esito smista_uni(wt *w, int64_t stream_id, const uint8_t *dati,
                             size_t len, bytes *riunito)
{
	stream_giudizio *g = giudizio_trova(w, stream_id);
	uint64_t sessione = 0;
	size_t n, consumati;
	uint16_t tipo;
	uint8_t canale;
	const char *guasto = NULL;

	if (g) {
		switch (g->genere) {
		case G_NONWT:
			return E_HTTP3;
		case G_UNI_OK:
		case G_UNI_KO:
			/* ⚠ I due giudizi NON sono la stessa cosa:
			 *   G_UNI_KO  violazione, la sessione e' gia' caduta;
			 *   G_UNI_OK  canale LECITO di §2.5 che questa fase non
			 *             serve ancora (l'input arriva alla fase 4,
			 *             gli appunti alla 7).
			 *   ⛔ Nell'innesto entrambi erano segnati «violazione»,
			 *      e un client conforme che apriva il canale di input
			 *      si vedeva scartare OGNI byte per sempre, senza una
			 *      riga di registro.
			 *   In tutt'e due i casi i byte si contano nel credito:
			 *   non contarli lascerebbe il client senza credito su
			 *   una connessione viva (§2.3). */
			conta_credito(w, stream_id, len);
			return E_MIO;
		default:
			break;
		}
	} else {
		g = giudizio_crea(w, stream_id);
		if (!g)
			return E_HTTP3;
	}

	if (!bytes_aggiungi(&g->pref, dati, len))
		return E_HTTP3;
	if (g->pref.n < 2)
		return E_ATTENDI;

	if (!(g->pref.d[0] == 0x40 && g->pref.d[1] == 0x54)) {
		/* Non e' WebTransport: e' di nghttp3, e i byte vanno consegnati
		 * interi — compresi quelli che abbiamo trattenuto. */
		bytes_aggiungi(riunito, g->pref.d, g->pref.n);
		bytes_libera(&g->pref);
		g->genere = G_NONWT;
		return E_HTTP3;
	}
	n = varint_leggi(&sessione, g->pref.d + 2, g->pref.n - 2);
	if (n == 0 || g->pref.n < 2 + n + 2)
		return E_ATTENDI; /* il campo `tipo` non e' ancora tutto arrivato */

	consumati = g->pref.n;
	tipo = (uint16_t)((g->pref.d[2 + n] << 8) | g->pref.d[2 + n + 1]);
	canale = (uint8_t)(tipo >> 8);
	bytes_libera(&g->pref);
	conta_credito(w, stream_id, consumati);

	switch (canale) {
	case 0x00:
		guasto = "il canale di CONTROLLO su uno stream unidirezionale: il "
		         "controllo vive solo sul primo stream bidirezionale (§2.5)";
		break;
	case 0x03:
		guasto = "il canale VIDEO dal client: e' del server, verso sbagliato "
		         "(§2.5)";
		break;
	case 0x04:
		guasto = "il canale AUDIO su uno stream: l'audio vive solo sui "
		         "datagram (§2.5, §6.3)";
		break;
	case 0x01:
	case 0x02:
		break;
	default:
		guasto = "byte alto del tipo sconosciuto su uno stream "
		         "unidirezionale (§2.5)";
		break;
	}
	g->genere = guasto ? G_UNI_KO : G_UNI_OK;
	registro_dice(REG_WT,
	              "stream unidirezionale %ld del client, sessione %llu, tipo "
	              "0x%04x, canale 0x%02x — %s",
	              (long)stream_id, (unsigned long long)sessione, tipo, canale,
	              guasto ? "VIOLAZIONE"
	                     : "lecito (§2.5).  ⚠ Ma questa fase non lo serve: i "
	                       "byte si contano nel credito e si scartano, e "
	                       "questa riga e' la tolleranza dichiarata (§3)");
	if (guasto) {
		if (w->rcp) {
			rcp_violazione(w->rcp, guasto);
		} else {
			/* ⚠ Nessun canale di controllo ancora aperto: il `CONGEDO`
			 *   non ha una strada, e resta il punto 3 di §3.1 — il
			 *   motivo dentro la chiusura della sessione.  ⭐ E' il
			 *   secondo condizionale di §3.1 all'opera: pretendere
			 *   tutt'e tre i punti sempre darebbe rosso sul codice
			 *   giusto. */
			registro_dice(REG_WT,
			              "⚠ nessun canale di controllo: il motivo "
			              "viaggia solo nella chiusura della sessione");
			chiudi_sessione(w, RCP_ERRORE_PROTOCOLLO);
		}
	}
	return E_MIO;
}

static enum esito smista(wt *w, int64_t stream_id, const uint8_t *dati,
                         size_t len, bool fin, bytes *riunito)
{
	stream_giudizio *g;
	uint64_t sessione = 0;
	size_t n, consumati;

	/* ⛔ Gli unidirezionali APERTI DAL CLIENT (§2.5) passano di qui prima di
	 *    tutto: fra loro c'e' il canale di controllo di HTTP/3 e i due di
	 *    QPACK, che sono di nghttp3 e non nostri. */
	if ((stream_id & 0x03) == 0x02)
		return smista_uni(w, stream_id, dati, len, riunito);

	/* Solo gli stream bidirezionali aperti dal client: la CONNECT estesa e
	 * gli stream WebTransport arrivano tutti di li'. */
	if ((stream_id & 0x03) != 0x00)
		return E_HTTP3;

	g = giudizio_trova(w, stream_id);
	if (g && g->genere == G_NONWT)
		return E_HTTP3;

	if (g && g->genere == G_WT) {
		/* ⭐ Uno stream WebTransport gia' riconosciuto. */
		if (len > 0) {
			if (stream_id == w->rcp_stream) {
				rcp_passa(w, dati, len);
				conta_credito(w, stream_id, len);
			} else {
				/* ⛔ NON si rimandano indietro e NON si riapre il
				 *    credito: vedi `scarta_stream_di_troppo()`. */
				scarta_stream_di_troppo(w, stream_id, len);
			}
		}
		/* ⛔ E IL FIN SI GUARDA DOPO I BYTE, non prima: gli ultimi byte
		 *    sono arrivati INSIEME a lui e vanno consegnati mentre la
		 *    sessione e' ancora viva, o chi li riceve li leggerebbe come
		 *    byte spediti dopo la fine — cioe' come una violazione del
		 *    client che non c'e' stata. */
		if (fin)
			fin_dal_client(w, stream_id);
		return E_MIO;
	}

	if (!g) {
		g = giudizio_crea(w, stream_id);
		if (!g)
			return E_HTTP3;
	}
	if (!bytes_aggiungi(&g->pref, dati, len))
		return E_HTTP3;
	if (g->pref.n < 2) {
		/* ⚠ E NON si allarga la finestra: quei byte non li ha ancora
		 *   presi nessuno, e contarli adesso e poi di nuovo falserebbe il
		 *   credito. */
		return E_ATTENDI;
	}

	/* ⛔ Il tipo di frame WEBTRANSPORT_STREAM e' 0x41 — ma un intero
	 *    variabile non lo scrive in un byte: 0x41 vale 65, e in un byte ce
	 *    ne stanno 63.  Sul filo sono DUE byte, 0x40 0x41, ed e' per questo
	 *    che due bastano a decidere.  Un frame HEADERS comincia per 0x01,
	 *    uno DATA per 0x00. */
	if (!(g->pref.d[0] == 0x40 && g->pref.d[1] == 0x41)) {
		bytes_aggiungi(riunito, g->pref.d, g->pref.n);
		bytes_libera(&g->pref);
		g->genere = G_NONWT;
		return E_HTTP3;
	}

	n = varint_leggi(&sessione, g->pref.d + 2, g->pref.n - 2);
	if (n == 0)
		return E_ATTENDI;

	consumati = g->pref.n;
	g->genere = G_WT;

	/* ⭐ `RCP.md` §4.2: il PRIMO stream bidirezionale che il client apre
	 *    nella sessione e' il canale di controllo.
	 *
	 * ⚠ E «il primo» QUI e' il primo RICONOSCIUTO, non il primo APERTO: i
	 *   due stream viaggiano in pacchetti diversi, e fra stream diversi la
	 *   rete non promette nessun ordine. */
	if (w->rcp_stream == -1) {
		rcp_avvia(w, stream_id);
	} else {
		/* ⛔ `RCP.md` §2.5: «il client NON DEVE aprire stream
		 *    bidirezionali oltre lo 0».  Un secondo bidirezionale non e'
		 *    un canale nuovo: e' una violazione.
		 *
		 * ⛔ E LA DIAGNOSI NON DEVE INCOLPARE L'ORDINE D'ARRIVO.  Se
		 *    questo stream ha un numero PIU' BASSO di quello eletto, il
		 *    primo aperto era lui, e a scambiarli e' stata la rete: gli
		 *    stream restano due — e due e' la violazione, comunque siano
		 *    arrivati — ma «un secondo stream» detto del numero piu'
		 *    basso manda a cercare il difetto nel client, che li' non ha
		 *    sbagliato niente. */
		if (stream_id < w->rcp_stream)
			registro_dice(REG_WT,
			              "⛔ due stream bidirezionali dal client dentro "
			              "la sessione: %ld e %ld — e il PRIMO APERTO "
			              "era il %ld, arrivato per secondo: il canale "
			              "di controllo e' stato eletto per ordine "
			              "d'arrivo, non per numero",
			              (long)w->rcp_stream, (long)stream_id,
			              (long)stream_id);
		else
			registro_dice(REG_WT,
			              "⛔ due stream bidirezionali dal client dentro "
			              "la sessione: il controllo e' il %ld, e il %ld "
			              "e' di troppo",
			              (long)w->rcp_stream, (long)stream_id);
		if (w->rcp)
			rcp_violazione(w->rcp,
			               "due stream bidirezionali dal client dentro "
			               "la sessione (§2.5)");
	}
	registro_dice(REG_WT, "stream %ld e' WebTransport, sessione %llu",
	              (long)stream_id, (unsigned long long)sessione);

	if (consumati > 2 + n) {
		const uint8_t *resto = g->pref.d + 2 + n;
		size_t rn = consumati - 2 - n;
		if (stream_id == w->rcp_stream)
			rcp_passa(w, resto, rn);
		else
			scarta_stream_di_troppo(w, stream_id, rn);
	}
	bytes_libera(&g->pref);
	/* ⚠ Il credito dei byte del PREFISSO si riapre comunque: quei byte li
	 *   abbiamo consumati noi per giudicare lo stream, e non contarli
	 *   bloccherebbe anche il canale di controllo legittimo.  ⛔ Quel che NON
	 *   si riapre e' il credito dei byte di un canale di troppo — vedi il
	 *   ramo qui sopra e `scarta_stream_di_troppo()`. */
	conta_credito(w, stream_id, consumati);

	/* ⛔ Anche qui: lo stream puo' essere riconosciuto e finito nello stesso
	 *    pacchetto (§4.2, il FIN da una qualunque delle due parti). */
	if (fin)
		fin_dal_client(w, stream_id);
	return E_MIO;
}

/* ------------------------------------------------------------------------ */
/* I richiami di nghttp3.                                                    */

static int cb_acked(nghttp3_conn *conn, int64_t stream_id, uint64_t datalen,
                    void *cud, void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)datalen;
	(void)cud;
	(void)sud;
	return 0;
}

static int cb_recv_data(nghttp3_conn *conn, int64_t stream_id,
                        const uint8_t *data, size_t datalen, void *cud,
                        void *sud)
{
	wt *w = cud;
	(void)sud;
	(void)conn;
	/* ⭐ Il corpo della CONNECT e' un flusso di capsule. */
	capsula(w, stream_id, data, datalen);
	/* I byte del corpo si contano nel credito: senza, il client resta senza
	 * finestra su una connessione viva (§2.3). */
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, datalen);
	ngtcp2_conn_extend_max_offset(w->conn, datalen);
	return 0;
}

static int cb_deferred_consume(nghttp3_conn *conn, int64_t stream_id,
                               size_t consumed, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, consumed);
	ngtcp2_conn_extend_max_offset(w->conn, consumed);
	return 0;
}

static int cb_begin_headers(nghttp3_conn *conn, int64_t stream_id, void *cud,
                            void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	if (!richiesta_trova(w, stream_id, true))
		return NGHTTP3_ERR_CALLBACK_FAILURE;
	return 0;
}

static void copia(char *fuori, size_t cap, nghttp3_rcbuf *v)
{
	nghttp3_vec b = nghttp3_rcbuf_get_buf(v);
	size_t n = b.len < cap - 1 ? b.len : cap - 1;
	memcpy(fuori, b.base, n);
	fuori[n] = 0;
}

static int cb_recv_header(nghttp3_conn *conn, int64_t stream_id, int32_t token,
                          nghttp3_rcbuf *name, nghttp3_rcbuf *value,
                          uint8_t flags, void *cud, void *sud)
{
	wt *w = cud;
	richiesta *r = richiesta_trova(w, stream_id, true);
	(void)conn;
	(void)name;
	(void)flags;
	(void)sud;
	if (!r)
		return 0;
	switch (token) {
	case NGHTTP3_QPACK_TOKEN__PATH:
		copia(r->uri, sizeof r->uri, value);
		break;
	case NGHTTP3_QPACK_TOKEN__METHOD:
		copia(r->metodo, sizeof r->metodo, value);
		break;
	/* ⭐ L'intestazione che distingue una CONNECT estesa da una CONNECT
	 *    normale (RFC 9220). */
	case NGHTTP3_QPACK_TOKEN__PROTOCOL:
		copia(r->protocollo, sizeof r->protocollo, value);
		break;
	default:
		break;
	}
	return 0;
}

/* Lo stream della CONNECT estesa NON si chiude: E' la sessione.  Un lettore che
 * dicesse «ho finito» ci metterebbe sopra il FIN, e la sessione morirebbe
 * nell'istante in cui si apre. */
static nghttp3_ssize cb_niente_dati(nghttp3_conn *conn, int64_t stream_id,
                                    nghttp3_vec *vec, size_t veccnt,
                                    uint32_t *pflags, void *cud, void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)vec;
	(void)veccnt;
	(void)pflags;
	(void)cud;
	(void)sud;
	return NGHTTP3_ERR_WOULDBLOCK;
}

static int risposta_secca(wt *w, int64_t stream_id, const char *stato)
{
	nghttp3_nv nv[2];
	int rv;

	nv[0].name = (uint8_t *)":status";
	nv[0].namelen = 7;
	nv[0].value = (uint8_t *)stato;
	nv[0].valuelen = strlen(stato);
	nv[0].flags = NGHTTP3_NV_FLAG_NONE;
	nv[1].name = (uint8_t *)"server";
	nv[1].namelen = 6;
	nv[1].value = (uint8_t *)"remotix";
	nv[1].valuelen = 7;
	nv[1].flags = NGHTTP3_NV_FLAG_NONE;

	rv = nghttp3_conn_submit_response(w->h3, stream_id, nv, 2, NULL);
	if (rv != 0)
		registro_dice(REG_WT, "⛔ nghttp3_conn_submit_response: %s",
		              nghttp3_strerror(rv));
	return rv;
}

static int apri_sessione(wt *w, richiesta *r)
{
	nghttp3_nv nv[2];
	nghttp3_data_reader dr;
	int rv;

	/* ⛔ `RCP.md` §2.2: il server NON DEVE accettare una sessione
	 *    WebTransport su un percorso diverso, e il rifiuto e' 404 (rilievo
	 *    R1.24, che ha scelto uno dei tre stati che erano tutti leciti).  E
	 *    si scrive nel registro: e' §3 applicata al primo byte, prima ancora
	 *    che RCP cominci. */
	if (strcmp(r->uri, "/rcp/1") != 0) {
		registro_dice(REG_WT,
		              "⛔ sessione WebTransport RIFIUTATA, percorso «%s» "
		              "(atteso /rcp/1 — §2.2): 404",
		              r->uri);
		return risposta_secca(w, r->id, "404");
	}

	nv[0].name = (uint8_t *)":status";
	nv[0].namelen = 7;
	nv[0].value = (uint8_t *)"200";
	nv[0].valuelen = 3;
	nv[0].flags = NGHTTP3_NV_FLAG_NONE;
	nv[1].name = (uint8_t *)"server";
	nv[1].namelen = 6;
	nv[1].value = (uint8_t *)"remotix";
	nv[1].valuelen = 7;
	nv[1].flags = NGHTTP3_NV_FLAG_NONE;

	memset(&dr, 0, sizeof dr);
	dr.read_data = cb_niente_dati;

	rv = nghttp3_conn_submit_response(w->h3, r->id, nv, 2, &dr);
	if (rv != 0) {
		registro_dice(REG_WT, "⛔ nghttp3_conn_submit_response: %s",
		              nghttp3_strerror(rv));
		return rv;
	}

	w->sessione = r->id;

	/* ⛔⭐ E QUI PARTE IL TETTO DI §4.6 PER L'APERTURA DEL CANALE — 5 s.
	 *
	 * ✅ `DECISIONI.md` §7.17, dall'utente l'11 agosto 2026.  Chi apre la
	 *    sessione e non apre mai il canale di controllo non aveva addosso
	 *    NESSUN tetto: `[M]` B6, 20 014 ms senza che succedesse niente.
	 *
	 * ⛔ E si arma anche cio' che lo fara' scadere, nello stesso istante — e'
	 *    la lezione piu' cara dell'innesto, scritta trenta righe piu' sotto in
	 *    `rcp_avvia`: un tetto senza battito e' un tetto che non scade. */
	w->canale_entro = ngtcp2_conn_get_timestamp(w->conn)
	                  + WT_TETTO_CANALE_NS;
	batti_fra(w, 100);

	registro_dice(REG_WT, "⭐ sessione WebTransport APERTA su %s (stream %ld) — "
	              "il canale di controllo va aperto entro %llu ms (§4.6, "
	              "DECISIONI.md §7.17)",
	              r->uri, (long)r->id,
	              (unsigned long long)(WT_TETTO_CANALE_NS / NGTCP2_MILLISECONDS));
	return 0;
}

static int cb_end_headers(nghttp3_conn *conn, int64_t stream_id, int fin,
                          void *cud, void *sud)
{
	wt *w = cud;
	richiesta *r = richiesta_trova(w, stream_id, false);
	(void)conn;
	(void)fin;
	(void)sud;
	if (!r)
		return 0;
	/* ⭐ E' qui che nasce la sessione WebTransport. */
	if (strcmp(r->metodo, "CONNECT") == 0 &&
	    strcmp(r->protocollo, "webtransport") == 0)
		return apri_sessione(w, r) == 0 ? 0 : NGHTTP3_ERR_CALLBACK_FAILURE;

	/* ⚠ Tutto il resto NON e' servito da questo ascoltatore: la pagina la
	 *   serve il TCP (`RCP.md` §2.4).  Un 404 e' la risposta esatta, e si
	 *   dichiara invece di lasciare la richiesta appesa. */
	registro_dice(REG_WT,
	              "richiesta HTTP/3 %s %s sullo stream %ld: 404 (su UDP si "
	              "serve solo la sessione WebTransport)",
	              r->metodo, r->uri, (long)stream_id);
	return risposta_secca(w, stream_id, "404") == 0
	         ? 0
	         : NGHTTP3_ERR_CALLBACK_FAILURE;
}

static int cb_stop_sending(nghttp3_conn *conn, int64_t stream_id,
                           uint64_t app_error_code, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_shutdown_stream_read(w->conn, 0, stream_id, app_error_code);
	return 0;
}

static int cb_reset_stream(nghttp3_conn *conn, int64_t stream_id,
                           uint64_t app_error_code, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_shutdown_stream_write(w->conn, 0, stream_id, app_error_code);
	return 0;
}

static int cb_end_stream(nghttp3_conn *conn, int64_t stream_id, void *cud,
                         void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)cud;
	(void)sud;
	return 0;
}

static void cb_rand(uint8_t *dest, size_t destlen)
{
	for (size_t i = 0; i < destlen; i++)
		dest[i] = (uint8_t)(rand() & 0xff);
}

/* ------------------------------------------------------------------------ */

static int apri_http3(wt *w)
{
	static const nghttp3_callbacks callbacks = {
		.acked_stream_data = cb_acked,
		.recv_data = cb_recv_data,
		.deferred_consume = cb_deferred_consume,
		.begin_headers = cb_begin_headers,
		.recv_header = cb_recv_header,
		.end_headers = cb_end_headers,
		.stop_sending = cb_stop_sending,
		.end_stream = cb_end_stream,
		.reset_stream = cb_reset_stream,
		.rand = cb_rand,
	};
	nghttp3_settings settings;
	const ngtcp2_transport_params *params;
	int64_t ctrl, enc, dec;
	int rv;

	if (w->h3)
		return 0;
	if (ngtcp2_conn_get_streams_uni_left2(w->conn) < 3) {
		registro_dice(REG_WT,
		              "⛔ il client non concede nemmeno 3 stream "
		              "unidirezionali: HTTP/3 non si apre");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	nghttp3_settings_default(&settings);
	settings.qpack_max_dtable_capacity = 4096;
	settings.qpack_blocked_streams = 100;
	/* ⭐ Le due che nghttp3 sa fare da se', e sono negli RFC. */
	settings.enable_connect_protocol = 1; /* RFC 9220, l'extended CONNECT */
	settings.h3_datagram = 1;             /* RFC 9297 (RCP.md §2.2) */

	rv = nghttp3_conn_server_new(&w->h3, &callbacks, &settings,
	                             nghttp3_mem_default(), w);
	if (rv != 0) {
		registro_dice(REG_WT, "⛔ nghttp3_conn_server_new: %s",
		              nghttp3_strerror(rv));
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	params = ngtcp2_conn_get_local_transport_params2(w->conn);
	nghttp3_conn_set_max_client_streams_bidi(w->h3,
	                                         params->initial_max_streams_bidi);

	if (ngtcp2_conn_open_uni_stream(w->conn, &ctrl, NULL) != 0 ||
	    ngtcp2_conn_open_uni_stream(w->conn, &enc, NULL) != 0 ||
	    ngtcp2_conn_open_uni_stream(w->conn, &dec, NULL) != 0) {
		registro_dice(REG_WT, "⛔ non apro i tre stream di servizio di HTTP/3");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	/* ⭐ Si tiene il numero: quando nghttp3 scrivera' il suo SETTINGS su
	 *    questo stream sara' l'unica occasione di aggiungerci le due
	 *    dichiarazioni di WebTransport. */
	w->ctrl_id = ctrl;

	if (nghttp3_conn_bind_control_stream(w->h3, ctrl) != 0 ||
	    nghttp3_conn_bind_qpack_streams(w->h3, enc, dec) != 0) {
		registro_dice(REG_WT, "⛔ non lego gli stream di servizio a nghttp3");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}
	registro_dettaglio(REG_WT, "HTTP/3 aperto: controllo=%ld qpack=%ld/%ld",
	                   (long)ctrl, (long)enc, (long)dec);
	return 0;
}

/* ------------------------------------------------------------------------ */

wt *wt_nuovo(ngtcp2_conn *conn, ngtcp2_ccerr *ultimo_errore,
             const char *provenienza)
{
	wt *w = calloc(1, sizeof *w);
	if (!w)
		return NULL;
	w->conn = conn;
	w->ultimo_errore = ultimo_errore;
	w->ctrl_id = -1;
	w->sessione = -1;
	w->rcp_stream = -1;
	w->chiusura = -1;
	snprintf(w->provenienza, sizeof w->provenienza, "%s",
	         provenienza ? provenienza : "");
	return w;
}

void wt_libera(wt *w)
{
	if (!w)
		return;
	/* ⭐ Il posto nel registro delle sessioni si libera qui, se non l'ha gia'
	 *    fatto la chiusura dello stream. */
	if (w->rcp)
		rcp_libera(w->rcp);
	if (w->h3)
		nghttp3_conn_del(w->h3);
	for (size_t i = 0; i < w->ngiudizi; i++)
		bytes_libera(&w->giudizi[i].pref);
	free(w->giudizi);
	for (size_t i = w->testa; i < w->ncoda; i++)
		bytes_libera(&w->coda[i].dati);
	free(w->coda);
	bytes_libera(&w->capsbuf);
	free(w->richieste);
	free(w);
}

int wt_app_pronta(wt *w) { return apri_http3(w); }

int wt_ricevi_stream(wt *w, uint32_t flags, int64_t stream_id,
                     const uint8_t *dati, size_t len)
{
	bytes riunito = {0};
	nghttp3_ssize nconsumed;
	bool fin = (flags & NGTCP2_STREAM_DATA_FLAG_FIN) != 0;
	int esito = 0;

	if (!w->h3)
		return 0;

	/* ⛔ Gli stream WebTransport non sono affari di nghttp3: leggerebbe 0x41
	 *    come un tipo di frame sconosciuto e poi il numero della sessione
	 *    come una LUNGHEZZA, sballando tutto il resto.
	 *    ⛔ E il FIN viaggia con loro: §4.2 lo rende la fine della sessione,
	 *       e per uno stream che gestiamo noi qui e' l'ULTIMO posto in cui si
	 *       puo' vedere — sotto si torna prima di `nghttp3_conn_read_stream2`,
	 *       quindi nemmeno nghttp3 lo incontra. */
	switch (smista(w, stream_id, dati, len, fin, &riunito)) {
	case E_MIO:
	case E_ATTENDI:
		bytes_libera(&riunito);
		return 0;
	case E_HTTP3:
		break;
	}

	if (riunito.n > 0) {
		dati = riunito.d;
		len = riunito.n;
	}

	nconsumed = nghttp3_conn_read_stream2(w->h3, stream_id, dati, len, fin,
	                                      ngtcp2_conn_get_timestamp(w->conn));
	if (nconsumed < 0) {
		registro_dice(REG_WT, "⛔ nghttp3_conn_read_stream2: %s",
		              nghttp3_strerror((int)nconsumed));
		ngtcp2_ccerr_set_application_error(
			w->ultimo_errore,
			nghttp3_err_infer_quic_app_error_code((int)nconsumed), NULL, 0);
		esito = NGTCP2_ERR_CALLBACK_FAILURE;
	} else {
		conta_credito(w, stream_id, (size_t)nconsumed);
	}
	bytes_libera(&riunito);
	return esito;
}

int wt_stream_chiuso(wt *w, int64_t stream_id, uint64_t codice, bool con_codice)
{
	richiesta *r;

	/* ⛔⭐ `RCP.md` §4.2: il canale di controllo si chiude, e IL SUO
	 *     CHIUDERSI E' LA FINE DELLA SESSIONE.  Il posto nel registro (§8.2
	 *     motivo 0x0F) va liberato QUI — e anche quando a chiudersi e' lo
	 *     stream della CONNECT estesa, che PORTA la sessione WebTransport.
	 *
	 * ⚠ Nell'innesto il posto si liberava solo alla morte della CONNESSIONE.
	 *   Con un cliente di prova i due istanti coincidono, e B3 e' rimasto
	 *   verde per cinque giri.  ⛔ Un BROWSER no: chiude la sessione e tiene
	 *   viva la connessione, e da quel momento il posto resta occupato da una
	 *   sessione che non esiste piu' — SETTE `posto NEGATO` su nove
	 *   tentativi, `[M]` B11 con Chrome. */
	if (w->rcp && (stream_id == w->rcp_stream || stream_id == w->sessione)) {
		registro_dice(REG_RCP,
		              "chiuso lo stream %ld: la sessione e' finita, il posto "
		              "si libera",
		              (long)stream_id);
		rcp_libera(w->rcp);
		w->rcp = NULL;
		w->rcp_stream = -1;
		regola_battito(w);
	}
	if (stream_id == w->sessione)
		w->sessione = -1;

	r = richiesta_trova(w, stream_id, false);
	if (r)
		r->usato = false;

	if (!w->h3)
		return 0;
	if (con_codice) {
		int rv = nghttp3_conn_close_stream(w->h3, stream_id, codice);
		if (rv != 0 && rv != NGHTTP3_ERR_STREAM_NOT_FOUND) {
			registro_dice(REG_WT, "⛔ nghttp3_conn_close_stream: %s",
			              nghttp3_strerror(rv));
			ngtcp2_ccerr_set_application_error(
				w->ultimo_errore,
				nghttp3_err_infer_quic_app_error_code(rv), NULL, 0);
			return NGTCP2_ERR_CALLBACK_FAILURE;
		}
	}
	return 0;
}

int wt_stream_reset(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_shutdown_stream_read(w->h3, stream_id);
	return 0;
}

int wt_stream_stop_sending(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_shutdown_stream_read(w->h3, stream_id);
	return 0;
}

int wt_ack_stream_data(wt *w, int64_t stream_id, uint64_t len)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_add_ack_offset(w->h3, stream_id, len);
	return 0;
}

int wt_estendi_max_stream_data(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_unblock_stream(w->h3, stream_id);
	return 0;
}

int wt_estendi_max_streams_bidi(wt *w, uint64_t max_streams)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_set_max_client_streams_bidi(w->h3, max_streams);
	return 0;
}

/* ------------------------------------------------------------------------ */

/* ⛔⭐ §8.1 — «MAI CON UN SILENZIO».  Rilievo B-7, 10 agosto 2026 notte.
 *
 *     La chiama `trasporto_congeda_tutte()` quando il server si spegne.  Le due
 *     strade di §3.1 le percorre `rcp_congeda()`: `CONGEDO(0x0C)` sul canale di
 *     controllo, e lo stesso `0x0C` nel codice della chiusura della sessione.
 *
 * ⚠ E se la sessione RCP non c'e' ancora — una connessione QUIC aperta ma senza
 *   canale di controllo — resta la seconda strada, che e' proprio il caso per
 *   cui §3.1 ne ha volute due. */
void wt_congeda(wt *w, uint8_t motivo, const char *dettaglio)
{
	if (!w)
		return;
	if (w->rcp && !rcp_e_finita(w->rcp)) {
		rcp_congeda(w->rcp, motivo, dettaglio);
		return;
	}
	if (w->sessione != -1 && w->chiusura < 0) {
		registro_dice(REG_RCP,
		              "⚠ %s: nessuna sessione RCP viva, il motivo %#04x "
		              "viaggia solo nel codice di chiusura della sessione "
		              "(§3.1, seconda strada)",
		              w->provenienza, motivo);
		chiudi_sessione(w, motivo);
	}
}

void wt_batti(wt *w, ngtcp2_tstamp ts)
{
	if (w->rcp)
		rcp_tempo(w->rcp, ts / NGTCP2_MILLISECONDS);

	/* ⛔⭐ §4.6 — LA SESSIONE CHE NON APRE MAI IL CANALE DI CONTROLLO.
	 *
	 * ✅ `DECISIONI.md` §7.17, 11 agosto 2026: 5 s, poi `TEMPO_SCADUTO`.
	 *
	 * ⚠ E il `CONGEDO` NON si manda: il canale di controllo non e' mai nato,
	 *   quindi non c'e' dove spedirlo.  E' la condizione decisa lo stesso
	 *   giorno in §7.15 — «se il canale e' ancora utilizzabile» — e qui non lo
	 *   e'.  Il motivo viaggia SOLO nel codice di chiusura della sessione, che
	 *   e' la seconda strada di §3.1 punto 3.
	 *
	 * ⭐ Le due decisioni si incastrano proprio qui, ed e' il primo posto in
	 *    cui succede: senza §7.15 questa riga dovrebbe spedire un byte su un
	 *    canale mai nato. */
	if (w->canale_entro && ts >= w->canale_entro && w->chiusura < 0) {
		registro_dice(REG_RCP,
		              "⛔ %s: sessione WebTransport aperta e canale di "
		              "controllo MAI aperto entro %llu ms — congedo "
		              "%#04x TEMPO_SCADUTO (§4.6, DECISIONI.md §7.17).  "
		              "⚠ nessun CONGEDO sul canale: il canale non esiste, "
		              "il motivo viaggia nel codice di chiusura (§3.1 punto "
		              "3, e §7.15 lo consente)",
		              w->provenienza,
		              (unsigned long long)(WT_TETTO_CANALE_NS
		                                   / NGTCP2_MILLISECONDS),
		              RCP_TEMPO_SCADUTO);
		w->canale_entro = 0;
		chiudi_sessione(w, RCP_TEMPO_SCADUTO);
	}

	/* ⛔ La capsula di chiusura parte SOLO quando la coda d'uscita e' vuota:
	 *    il `CONGEDO` deve essere gia' partito, o il browser lo butta insieme
	 *    alla sessione.  ⚠ E non basta che sia vuota: «consegnato a ngtcp2»
	 *    non e' «uscito sul filo», quindi si aspetta ancora mezzo secondo. */
	if (w->chiusura >= 0) {
		/* ⛔ La scadenza si guarda PRIMA della coda — rilievo B-3.  Se si
		 *    guardasse dopo, il ramo «coda non vuota» riazzererebbe
		 *    `chiusura_da` per sempre e non si arriverebbe mai qui: e'
		 *    esattamente il difetto che questa riga toglie. */
		if (w->chiusura_scadenza && ts >= w->chiusura_scadenza) {
			uint8_t m = (uint8_t)w->chiusura;
			registro_dice(REG_WT,
			              "⛔ la coda d'uscita non si e' svuotata in 3 s "
			              "(%zu elementi, %zu byte): la capsula di chiusura "
			              "parte LO STESSO col codice 0x%02x — §3.1 punto 3 "
			              "e' il motivo che salva le diagnosi, e aspettare "
			              "per sempre vuol dire non eseguirlo mai",
			              w->ncoda - w->testa, w->byte_in_coda, m);
			w->chiusura = -1;
			w->chiusura_da = 0;
			w->chiusura_scadenza = 0;
			chiudi_adesso(w, m);
		} else if (!coda_vuota(w)) {
			w->chiusura_da = 0;
		} else if (w->chiusura_da == 0) {
			w->chiusura_da = ts + WT_ATTESA_CHIUSURA_NS;
		} else if (ts >= w->chiusura_da) {
			uint8_t m = (uint8_t)w->chiusura;
			w->chiusura = -1;
			w->chiusura_da = 0;
			w->chiusura_scadenza = 0;
			chiudi_adesso(w, m);
		}
	}

	regola_battito(w);
	if (w->battito_ms && w->battito <= ts) {
		/* Il tempo non e' avanzato quanto serve: si rimanda comunque in
		 * avanti, o il ciclo girerebbe a vuoto. */
		w->battito = ts + w->battito_ms * NGTCP2_MILLISECONDS;
	}
}

/* ------------------------------------------------------------------------ */
/* ⭐ La scrittura: e' qui che le due cose che nghttp3 non sa fare si fanno.   */

ngtcp2_ssize wt_scrivi(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi,
                       uint8_t *dest, size_t destlen, ngtcp2_tstamp ts)
{
	nghttp3_vec vec[16];

	/* ⭐ Una passata di scrittura comincia qui, e la coda nostra riparte
	 *    SBLOCCATA: `coda_bloccata` vale per una passata sola.  ⚠ Sta fuori
	 *    dal ciclo apposta — azzerarlo dentro rimetterebbe in gioco lo stesso
	 *    elemento a ogni giro, che e' precisamente il ciclo che non avanza. */
	w->coda_bloccata = false;

	for (;;) {
		int64_t stream_id = -1;
		int fin = 0;
		nghttp3_ssize sveccnt = 0;
		nghttp3_vec wtvec[1];
		size_t wt_orig = 0;
		bool wt_mio = false;
		ngtcp2_ssize ndatalen = -1, nwrite;
		const nghttp3_vec *v;
		size_t vcnt;
		uint32_t flags;

		/* ⭐ Se la riscrittura delle impostazioni ha perso il conto, ci si
		 *    ferma: uno stream di controllo sfasato e' peggio di una
		 *    connessione chiusa.  ⚠ NON e' il caso della scrittura
		 *    PARZIALE, che e' un esito normale e si riprende dopo. */
		if (w->guasto)
			return NGTCP2_ERR_CALLBACK_FAILURE;

		if (w->h3 && ngtcp2_conn_get_max_data_left2(w->conn)) {
			sveccnt = nghttp3_conn_writev_stream(w->h3, &stream_id, &fin,
			                                     vec, 16);
			if (sveccnt < 0) {
				registro_dice(REG_WT, "⛔ nghttp3_conn_writev_stream: %s",
				              nghttp3_strerror((int)sveccnt));
				ngtcp2_ccerr_set_application_error(
					w->ultimo_errore,
					nghttp3_err_infer_quic_app_error_code((int)sveccnt),
					NULL, 0);
				return NGTCP2_ERR_CALLBACK_FAILURE;
			}
		}

		/* ── 1. le impostazioni ─────────────────────────────────────── */
		if (sveccnt > 0 && stream_id == w->ctrl_id && !w->impostazioni_scritte) {
			/* ⛔ La riscrittura si fa UNA VOLTA SOLA.  Se la passata di
			 *    prima ne ha spedito solo un pezzo, nghttp3 ci rioffre
			 *    gli stessi byte — non gli abbiamo ancora detto di
			 *    averli consumati — e ricomporre il buffer da capo
			 *    rispedirebbe il pezzo gia' uscito. */
			if (w->impbuf_off == 0)
				w->impbuf_orig =
					riscrivi_impostazioni(w, vec, (size_t)sveccnt);
			wt_orig = w->impbuf_orig;
		}

		/* ── 2. la coda nostra ──────────────────────────────────────── */
		if (sveccnt <= 0 && !w->coda_bloccata && !coda_vuota(w)) {
			uscita *u = coda_prima(w);
			stream_id = u->id;
			fin = u->fin ? 1 : 0;
			wtvec[0].base = u->dati.d + u->off;
			wtvec[0].len = u->dati.n - u->off;
			wt_mio = true;
		}

		v = vec;
		vcnt = (size_t)(sveccnt > 0 ? sveccnt : 0);

		if (wt_orig) {
			wtvec[0].base = w->impbuf + w->impbuf_off;
			wtvec[0].len = w->impbuf_len - w->impbuf_off;
			v = wtvec;
			vcnt = 1;
		} else if (wt_mio) {
			v = wtvec;
			vcnt = 1;
		}

		flags = NGTCP2_WRITE_STREAM_FLAG_MORE |
		        NGTCP2_WRITE_STREAM_FLAG_PADDING;
		if (fin)
			flags |= NGTCP2_WRITE_STREAM_FLAG_FIN;

		nwrite = ngtcp2_conn_writev_stream(w->conn, path, pi, dest, destlen,
		                                   &ndatalen, flags, stream_id,
		                                   (const ngtcp2_vec *)v, vcnt, ts);
		if (nwrite < 0) {
			switch (nwrite) {
			case NGTCP2_ERR_STREAM_DATA_BLOCKED:
				/* ⛔⭐ E I BYTE NON SI BUTTANO: QUESTO E' UN CANALE
				 *     AFFIDABILE.  Nell'innesto qui si scartava
				 *     l'elemento INTERO — compreso il caso in cui una
				 *     parte era gia' uscita sul filo: il messaggio dopo
				 *     si saldava a quei byte monchi e il client leggeva
				 *     un `tipo`/`lunghezza` inventato.  ⛔ Era il
				 *     SERVER a fabbricare la violazione del client.
				 *
				 * ⚠ E STREAM_DATA_BLOCKED non e' un guasto: e' la
				 *   condizione normale e transitoria che si scioglie col
				 *   primo MAX_STREAM_DATA. */
				if (wt_mio) {
					uscita *u = coda_prima(w);
					registro_dettaglio(
						REG_WT,
						"stream %ld bloccato: %zu byte RESTANO in "
						"coda (%zu gia' usciti), si riprova alla "
						"passata dopo",
						(long)stream_id, u->dati.n - u->off, u->off);
					w->coda_bloccata = true;
					continue;
				}
				nghttp3_conn_block_stream(w->h3, stream_id);
				continue;
			case NGTCP2_ERR_STREAM_SHUT_WR:
				if (wt_mio) {
					coda_togli(w);
					continue;
				}
				nghttp3_conn_shutdown_stream_write(w->h3, stream_id);
				continue;
			case NGTCP2_ERR_WRITE_MORE:
				break;
			default:
				registro_dice(REG_WT, "⛔ ngtcp2_conn_writev_stream: %s",
				              ngtcp2_strerror((int)nwrite));
				ngtcp2_ccerr_set_liberr(w->ultimo_errore, (int)nwrite,
				                        NULL, 0);
				return NGTCP2_ERR_CALLBACK_FAILURE;
			}
		}

		if (nwrite == NGTCP2_ERR_WRITE_MORE || ndatalen >= 0) {
			/* Quanti byte DI NGHTTP3 sono stati consumati.  Se il suo
			 * buffer e' stato sostituito, il numero che ngtcp2
			 * restituisce e' il NOSTRO, e dirglielo sfaserebbe i suoi
			 * conti. */
			if (wt_mio) {
				uscita *u = coda_prima(w);
				u->off += (size_t)ndatalen;
				if (u->off >= u->dati.n) {
					/* ⛔⭐ `RCP.md` §4.2: il canale di controllo
					 *     che si chiude e' la fine della sessione,
					 *     ANCHE dal lato nostro.  Il posto va
					 *     lasciato QUI, perche' da adesso in poi non
					 *     arrivera' piu' un byte che lo liberi. */
					if (u->fin && w->rcp &&
					    (u->id == w->rcp_stream || u->id == w->sessione))
						rcp_canale_chiuso(w->rcp);
					coda_togli(w);
				}
			} else if (wt_orig) {
				uint64_t c = (uint64_t)ndatalen;
				/* ⛔⭐ E UNA SCRITTURA PARZIALE NON E' UN GUASTO.
				 *
				 *    `ndatalen` minore della lunghezza offerta e' un
				 *    esito NORMALE: nello stream frame ci va quel che
				 *    avanza nel pacchetto.  I ~24 byte del SETTINGS
				 *    riscritto viaggiano nel primo volo dopo la
				 *    stretta di mano, quello che porta anche
				 *    HANDSHAKE_DONE e i NEW_CONNECTION_ID: li' dentro
				 *    24 byte possono non starci.
				 *
				 * ⛔ Nell'innesto qui MORIVA LA CONNESSIONE, mentre
				 *    dieci righe piu' sopra la coda nostra la stessa
				 *    scrittura parziale la gestiva con `off`.  Due
				 *    politiche opposte per lo stesso esito, nello
				 *    stesso modulo. */
				if (c > w->impbuf_len - w->impbuf_off) {
					registro_dice(REG_WT,
					              "⛔ impostazioni, conto impossibile "
					              "(%llu presi su %zu offerti)",
					              (unsigned long long)c,
					              w->impbuf_len - w->impbuf_off);
					w->guasto = true;
					return NGTCP2_ERR_CALLBACK_FAILURE;
				}
				w->impbuf_off += (size_t)c;
				if (w->impbuf_off < w->impbuf_len) {
					registro_dettaglio(
						REG_WT,
						"impostazioni, %zu byte su %zu — il resto "
						"alla passata dopo",
						w->impbuf_off, w->impbuf_len);
				} else {
					w->impostazioni_scritte = true;
					if (nghttp3_conn_add_write_offset(
						    w->h3, stream_id, w->impbuf_orig) != 0) {
						w->guasto = true;
						return NGTCP2_ERR_CALLBACK_FAILURE;
					}
				}
			} else if (stream_id >= 0) {
				int rv = nghttp3_conn_add_write_offset(w->h3, stream_id,
				                                       (uint64_t)ndatalen);
				if (rv != 0) {
					registro_dice(REG_WT,
					              "⛔ nghttp3_conn_add_write_offset: %s",
					              nghttp3_strerror(rv));
					ngtcp2_ccerr_set_application_error(
						w->ultimo_errore,
						nghttp3_err_infer_quic_app_error_code(rv), NULL,
						0);
					return NGTCP2_ERR_CALLBACK_FAILURE;
				}
			}
		}

		if (nwrite == NGTCP2_ERR_WRITE_MORE)
			continue;

		return nwrite;
	}
}
