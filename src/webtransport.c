/*
 * webtransport.c — vedi webtransport.h.
 *
 * ⭐ Portato da `banchi/01-b2-ngtcp2-wt-innesta.py`, che lo teneva come `git
 *    diff` sull'albero di ngtcp2.  Le decisioni e le cure che i commenti
 *    dell'innesto documentavano sono qui dentro **con la loro ragione**: sono
 *    difetti gia' pagati, e riscriverli senza la ragione significa ripagarli.
 */
#include "webtransport.h"

/* ⛔ Solo per i `FIGLI_INPUT_*`: i numeri delle azioni stanno in un posto solo
 *    (`figlio.h`), o fra due settimane saranno tre posti con tre valori. */
#include "figlio.h"

#include "aiutante.h"
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
	G_UNI_INPUT, /* ⭐ il canale di INPUT (0x01), servito dalla fase 4: i suoi
	              *    byte vanno a `rcp_ricevi_input()`.  ⛔ Sta separato da
	              *    `G_UNI_OK` apposta — dentro quel giudizio i byte si
	              *    contano nel credito e SI SCARTANO, ed e' esattamente
	              *    quel che l'input faceva fino al 14 agosto 2026. */
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
	/* ⛔⭐ FASE 3 — «MORTO» INVECE DI «TOLTO DALLA TESTA».
	 *
	 *     Fino alla fase 2 da questa coda si toglieva **solo la testa**, e
	 *     bastava: si spediva un fotogramma solo per sessione.  ⛔ Con uno
	 *     stream per fotogramma la testa non e' piu' l'unico elemento che puo'
	 *     finire — si sceglie un elemento **in mezzo** quando quelli davanti
	 *     appartengono a uno stream bloccato — e togliere dal mezzo un array
	 *     vorrebbe dire spostare tutto il resto a ogni fotogramma.
	 *
	 *     ⇒ Chi finisce si marca morto; `testa` scorre sui morti in testa. */
	bool morto;
} uscita;

/* ⛔⭐ FASE 3 — GLI STREAM BLOCCATI DI **QUESTA PASSATA**, E PERCHE' NON E' PIU'
 *     UN `bool`.
 *
 * Fino alla fase 2 qui c'era `bool coda_bloccata`: al primo
 * `NGTCP2_ERR_STREAM_DATA_BLOCKED` si fermava **tutta la coda** per la passata.
 * ⛔ Con uno stream per fotogramma quel `bool` annulla esattamente il beneficio
 *    che `RCP.md` §5.1 compra: «gli stream sono indipendenti, quindi un
 *    fotogramma in ritardo non tocca i successivi» e' vero al livello di QUIC e
 *    diventava **falso un piano sopra**, dentro casa nostra — un fotogramma
 *    lento bloccava in testa tutti quelli dopo, cioe' il blocco di testa che
 *    §5.1 esiste per togliere, rifatto a mano.
 *
 * ⇒ Si blocca **lo stream**, non la coda.  L'ordine DENTRO uno stream resta
 *   quello: si sceglie sempre il primo elemento eleggibile in ordine di
 *   inserimento, quindi il primo di uno stream non bloccato e' il suo piu'
 *   vecchio.
 *
 * ⚠ E il tetto e' dichiarato: oltre `WT_BLOCCATI_MAX` stream bloccati nella
 *   stessa passata ci si ferma come prima e **si scrive**.  Un tetto che si
 *   supera in silenzio e' un tetto che non c'e'. */
#define WT_BLOCCATI_MAX 64

/* ⛔ Quanti fotogrammi possono essere in volo insieme su una sessione.  ⚠ Il
 *    numero non e' arbitrario: `RCP.md` §2.3 dichiara normativi **16** stream
 *    unidirezionali disponibili a RCP, e uno lo prende l'input.  Oltre quel
 *    numero il credito e' finito comunque, e questa tabella non e' il tetto che
 *    morde. */
#define WT_INVOLO_MAX 32

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
	/* ⭐ L'AIUTANTE DI PAM — `DECISIONI.md` §1.10.  ⛔ Non lo possiede questo
	 *    strato: e' uno solo per tutto il server, acceso da `main.c` prima
	 *    che esista una connessione, e arriva di qui perche' il gancio
	 *    `chiedi_verifica` di RCP e' l'unico posto che lo usa.
	 * ⚠ NULL e' lecito e vuol dire «verifica sincrona»: e' il ripiego
	 *   dichiarato, ed e' il guasto che `banchi/02-pam-*` innesta. */
	aiutante *aiuto;

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
	/* ⛔ Gli stream bloccati per QUESTA passata di scrittura: ngtcp2 ha detto
	 *    STREAM_DATA_BLOCKED, e riprovare dentro la stessa passata sarebbe un
	 *    ciclo che non avanza.  ⚠ Erano un `bool` fino alla fase 2 — vedi il
	 *    riquadro di `WT_BLOCCATI_MAX`: quel `bool` rifaceva a mano il blocco
	 *    di testa che `RCP.md` §5.1 esiste per togliere. */
	int64_t bloccati[WT_BLOCCATI_MAX];
	size_t nbloccati;
	/* ⛔ Il tetto e' stato toccato e la coda si ferma davvero: si tiene per
	 *    scriverlo UNA volta invece che a ogni passata. */
	bool troppi_bloccati;

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

	/* ═══ IL VIDEO DI QUESTA SESSIONE — fase 3 ═════════════════════════ */
	/*
	 * ⛔⭐ QUI C'ERA `bool video_fatto`, ED E' IL FRENO DELLA FASE 2.
	 *
	 *     Il commento diceva: «e' un `bool` e non un contatore perche' la fase
	 *     2 consegna UN'IMMAGINE FERMA: il ciclo dei fotogrammi e' della fase
	 *     3».  ⇒ Adesso e' la fase 3, e il freno si toglie: al suo posto ci
	 *     sta lo stato del **canale**, che si accende una volta e resta acceso,
	 *     e i contatori dei fotogrammi, che crescono.
	 *
	 * ⚠ La ragione per cui il `bool` esisteva resta valida e va onorata lo
	 *   stesso: senza un fondo, `video_regola()` riscriverebbe la stessa riga
	 *   di registro a ogni battito di ogni sessione, e un registro che ripete
	 *   non si legge piu'.  ⇒ `video_detto` e' quel fondo, ed e' solo per il
	 *   registro: non ferma piu' i fotogrammi.
	 */
	/* Il canale video di questa sessione e' acceso: `SESSIONE` e' partita, il
	 * codec e' negoziato, e al figlio e' stato chiesto di catturare. */
	bool video_acceso;
	uint8_t video_codec;
	/* ⛔ «Ho gia' spiegato perche' questa sessione non ha video»: una volta
	 *    sola, e il perche' e' nella riga scritta allora. */
	bool video_detto;
	/* ⛔ L'ultima misura di fotogramma per cui si e' gia' scritto «non e' la tela
	 *    in vigore».  ⚠ E' una MISURA e non un `bool` apposta: cosi' il fondo si
	 *    riarma quando il fatto cambia, invece di tacere per sempre dopo la prima
	 *    volta — ed e' un campo suo, perche' `video_detto` racconta un altro
	 *    fatto e un flag per due fatti ne spegne uno. */
	uint32_t tela_detta_l, tela_detta_a;
	/* Quando si e' chiesta l'ultima chiave al figlio, per non chiederne una a
	 * ogni battito mentre la prima e' ancora in viaggio.  ⛔ Non e' la grazia
	 * di §5.2 (quella e' di `rcp.c` e conta dall'ultima chiave SPEDITA): e' il
	 * fondo di una richiesta ripetuta verso il palco. */
	uint64_t chiave_chiesta_ms;
	uint32_t video_diffusi, video_saltati;

	/* ⛔⭐ I FOTOGRAMMI IN VOLO — §5.1, «uno piu' recente e' gia' partito».
	 *
	 *     Un fotogramma che RCP ha gia' chiuso con FIN puo' avere ancora tutti
	 *     i suoi byte fermi in questa coda: per RCP e' partito, sul filo non
	 *     e'.  §5.1 dice che quello si PUO' azzerare — «i byte non ancora
	 *     spediti non partono affatto» — ed e' l'unica strada per cui un
	 *     abbandono si veda davvero dal lato che riceve.
	 *
	 * ⚠ Si tiene qui e non in `rcp.c` perche' e' un fatto della CODA; e le tre
	 *   conseguenze (la riga di registro, il conto, il debito della chiave)
	 *   stanno in `rcp.c`, che e' l'unico a possederle. */
	struct {
		int64_t stream;
		uint32_t numero;
		bool chiave;
		bool vivo;
		bool detto; /* la chiave che trattiene la coda si dice una volta */
	} involo[WT_INVOLO_MAX];
	size_t ninvolo;
	/* ⛔ Lo stream che `gancio_video_apri()` ha appena aperto: `rcp.c` non lo
	 *    restituisce, e dedurlo da «l'ultimo aperto sulla connessione» sarebbe
	 *    indovinare. */
	int64_t video_stream_ultimo;

	/* La lista delle sessioni vive, per la diffusione dei fotogrammi. */
	wt *viva_dopo;

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

/* ⛔ Un elemento muore qui e in nessun altro posto: e' l'unico punto in cui
 *    `byte_in_coda` cala, e due punti che lo calassero divergerebbero. */
static void coda_uccidi(wt *w, size_t i)
{
	uscita *u;
	if (i >= w->ncoda)
		return;
	u = &w->coda[i];
	if (u->morto)
		return;
	if (w->byte_in_coda >= u->dati.n)
		w->byte_in_coda -= u->dati.n;
	else
		w->byte_in_coda = 0;
	bytes_libera(&u->dati);
	u->morto = true;
	/* I morti in testa non servono a nessuno: la testa scorre. */
	while (w->testa < w->ncoda && w->coda[w->testa].morto)
		w->testa++;
	if (w->testa == w->ncoda)
		w->testa = w->ncoda = 0;
}

static bool coda_vuota(const wt *w)
{
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto)
			return false;
	return true;
}

/* ⛔ Quanti byte di QUESTO stream non sono ancora usciti.  ⚠ Zero non vuol dire
 *    «e' arrivato»: vuol dire «non e' piu' roba nostra» — l'abbiamo consegnato
 *    a ngtcp2.  La differenza si dichiara qui perche' §5.1 la usa: un
 *    fotogramma che non ha piu' byte in coda non si abbandona, perche'
 *    l'abbandono non risparmierebbe piu' niente. */
static size_t coda_byte_stream(const wt *w, int64_t id)
{
	size_t n = 0;
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto && w->coda[i].id == id)
			n += w->coda[i].dati.n - w->coda[i].off;
	return n;
}

/* ⛔ §5.1: i byte non ancora spediti **non partono affatto**.  Si chiama solo
 *    accanto a un `RESET_STREAM`: buttare i byte senza azzerare lo stream
 *    lascerebbe il client ad aspettare una fine che non arriva. */
static size_t coda_butta_stream(wt *w, int64_t id)
{
	size_t buttati = 0;
	for (size_t i = w->testa; i < w->ncoda; i++) {
		if (w->coda[i].morto || w->coda[i].id != id)
			continue;
		buttati += w->coda[i].dati.n - w->coda[i].off;
		coda_uccidi(w, i);
	}
	return buttati;
}

static bool stream_bloccato(const wt *w, int64_t id)
{
	for (size_t i = 0; i < w->nbloccati; i++)
		if (w->bloccati[i] == id)
			return true;
	return false;
}

/* ⛔ Il primo elemento eleggibile in ORDINE DI INSERIMENTO, saltando gli stream
 *    gia' bloccati in questa passata.  ⚠ Scorrere in ordine e' quel che tiene
 *    l'ordine DENTRO ogni stream: il primo elemento di uno stream non bloccato
 *    e' per costruzione il suo piu' vecchio. */
static uscita *coda_scegli(wt *w, size_t *fuori)
{
	for (size_t i = w->testa; i < w->ncoda; i++) {
		if (w->coda[i].morto)
			continue;
		if (stream_bloccato(w, w->coda[i].id))
			continue;
		if (fuori)
			*fuori = i;
		return &w->coda[i];
	}
	return NULL;
}

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
 *    prosegue in silenzio: vedi `accoda()` e il rilievo B-15.
 *
 * ⛔⭐ E IL 12 AGOSTO 2026 IL NUMERO E' CAMBIATO, con la fase 2 — da 2 MiB a
 *     17.  La ragione non e' «serviva piu' spazio»:
 *
 *     `RCP.md` §6.2 dichiara **legale** un fotogramma fino a **16 MiB**, e
 *     `rcp_video_apri()` rifiuta esattamente sopra quel numero.  ⛔ Con la coda
 *     a 2 MiB un fotogramma perfettamente legale da 3 MiB sarebbe stato
 *     rifiutato **dal nostro limitatore** invece che dal tetto del protocollo:
 *     due tetti diversi per la stessa grandezza, e quello che morde per primo
 *     non e' quello scritto nell'arbitro.
 *
 *     ⚠ E il sintomo sarebbe stato una **degradazione silenziosa** — il
 *       fotogramma non parte, il client vede un buco e chiede una chiave, la
 *       chiave e' ancora piu' grossa: la spirale di §5.2, provocata da una
 *       costante di questo file.  E' l'invariante **I1** letta da
 *       `REVIEWER.md` §3.
 *
 *     ⭐ 16 MiB (il fotogramma piu' grande che §6.2 ammette) + 1 MiB per i
 *        messaggi del canale di controllo, che stanno in qualche centinaio di
 *        byte l'uno.  ⚠ Il prezzo si dichiara: su 16 sessioni il peggio
 *        teorico e' 272 MiB, ed e' il prezzo che §6.2 ha gia' scelto — non uno
 *        nuovo. */
#define WT_CODA_MAX (17u * 1024u * 1024u)

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
	if (w->chiusura >= 0) {
		/* ⛔ E QUANTO MANCA, o la diagnosi si ferma qui — 11 agosto 2026.
		 *    «Non ancora matura» dopo 2 s, quando ne bastano 0,5, ha due
		 *    spiegazioni opposte: l'orologio non gira, oppure gira e viene
		 *    RIAZZERATO.  Il numero le separa; l'aggettivo no. */
		static char detto[220];
		ngtcp2_tstamp ora = ngtcp2_conn_get_timestamp(w->conn);
		snprintf(detto, sizeof detto,
		         "capsula di chiusura non ancora matura (coda vuota) — "
		         "chiusura=%#04x · chiusura_da=%s · mancano %lld ms · "
		         "battito fra %lld ms",
		         (unsigned)w->chiusura,
		         w->chiusura_da ? "armato" : "⛔ MAI ARMATO",
		         w->chiusura_da
		             ? (long long)(((long long)w->chiusura_da - (long long)ora)
		                           / (long long)NGTCP2_MILLISECONDS) : 0LL,
		         w->battito_ms
		             ? (long long)(((long long)w->battito - (long long)ora)
		                           / (long long)NGTCP2_MILLISECONDS) : -1LL);
		return detto;
	}
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

/* ⛔⭐ QUESTO GANCIO E' IL RIPIEGO, DAL 12 AGOSTO 2026 — `DECISIONI.md` §1.10.
 *
 *     ⚠ PAM BLOCCA, e qui bloccava il ciclo intero: la stretta di mano di un
 *       utente fermava quella di tutti gli altri e ritardava i pacchetti di
 *       chiunque fosse gia' collegato.  `[M]` B8, 11 agosto 2026: **da 1,0 a
 *       2,2 secondi**, e a metterceli era PAM (+1034 ms sui respinti contro
 *       +84 ms sugli ammessi — la firma di `pam_faildelay`).
 *
 * ⛔ Adesso la strada buona e' `gancio_chiedi`, qui sotto.  Questa resta
 *    collegata perche' `rcp.c` la usa quando l'aiutante non c'e' — e allora e'
 *    giusto che il server funzioni lo stesso, con meno (`CODER.md` §4.2).
 * ⚠ Ma il ripiego SI DICHIARA: chi lo percorre lo trova scritto nel registro
 *   da `rcp.c`, «per via SINCRONA — il filo e' rimasto fermo». */
static bool gancio_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	return rcp_autentica(utente, parola);
}

/* ⭐⭐ LA STRADA BUONA: si chiede, non si aspetta — `DECISIONI.md` §1.10.
 *
 * ⛔ Restituisce `false` quando la domanda non e' partita, e `rcp.c` lo tratta
 *    come un NO immediato: invariante I3, il fallimento e' un no e non un
 *    forse. */
static bool gancio_chiedi(void *ctx, const char *utente, const char *parola,
                          uint64_t *pratica)
{
	wt *w = (wt *)ctx;
	if (!w->aiuto)
		return false;
	return aiutante_chiedi(w->aiuto, utente, parola,
	                       ngtcp2_conn_get_timestamp(w->conn)
	                           / NGTCP2_MILLISECONDS,
	                       pratica);
}

/* ========================================================================== */
/* ⭐⭐ I QUATTRO GANCI DEL CANALE VIDEO — `RCP.md` §2.5, §5.1, §6.2.          */
/*                                                                            */
/* Innestati il 12 agosto 2026 dal montaggio della fase 2.  Le righe le aveva */
/* scritte `fasi/rapporti/P2-4-filo.md` §5, e ⛔ **non stanno in `main.c`**:   */
/* `main.c` non conosce `rcp_ganci`, la struttura la riempie `rcp_avvia()` qui */
/* dentro — la correzione al mandato che P2.4 ha messo a verbale.             */
/*                                                                            */
/* ⛔ SONO QUATTRO E NON UNO perche' §6.2 dice che **come lo stream finisce e' */
/*    parte del messaggio**: FIN ⇒ fotogramma completo, `RESET_STREAM` ⇒       */
/*    incompleto, si butta.  Un gancio solo che «manda un fotogramma» non      */
/*    saprebbe dire la differenza (forma E8, rilievo R1.7).                    */
/*                                                                            */
/* ⛔⭐ E IL PREAMBOLO DI WEBTRANSPORT NON E' UN DETTAGLIO — proposta P18.     */
/*                                                                            */
/*     Uno stream unidirezionale di WebTransport comincia con il **tipo dello  */
/*     stream** (`0x54`) seguito dal **numero della sessione**, tutt'e due     */
/*     interi variabili di QUIC (RFC 9000 §16): sul filo `0x54` sono i due     */
/*     byte `40 54`.  I 28 byte di §6.2 cominciano DOPO.                       */
/*                                                                            */
/*     ⚠ §2.5 dice «si leggono i primi due byte dello stream, che sono in ogni */
/*       caso un campo `tipo`» — e su WebTransport non e' vero.  Un lettore che */
/*       lo applicasse alla lettera ricaverebbe il canale `0x40` da OGNI       */
/*       fotogramma e chiuderebbe con `ERRORE_PROTOCOLLO`.  ⛔ Il primo giro   */
/*       dal vivo di `02-filo-cliente.py` e' finito rosso esattamente li'.     */
/*                                                                            */
/*     ⭐ Questo file lo sapeva gia' per gli stream IN ARRIVO (`smista_uni`,   */
/*        riga ~1164): qui c'e' l'altra meta', ed e' lo stesso `varint_scrivi` */
/*        — non una copia dei due byte a mano, che il giorno in cui il numero  */
/*        di sessione supera 63 diventerebbe muta e sbagliata.                 */

/* ⭐⭐ I SEI GANCI DELL'INPUT — FASE 4, 14 agosto 2026.
 *
 * ⛔ PERCHE' SONO GANCI E NON CHIAMATE DIRETTE, e non e' stile: `rcp.c` vive in
 *    DUE cartelle che il `Makefile` (`GEMELLATI`) pretende identiche byte per
 *    byte, e la seconda copia `banchi/01-b3-rcp-innesta.py` la infila dentro
 *    `examples/` di ngtcp2, dove `input.h` **non esiste**.  Un `#include` la'
 *    dentro spegnerebbe B3, B5, B6, B8 e B11 in un colpo solo.
 *
 * ⛔ E PERCHE' PASSANO DI QUI E NON VANNO DRITTI AL PALCO: il palco e' in un
 *    ALTRO PROCESSO (`figlio.c`), che gira come l'utente ed e' l'unico ad avere
 *    la sessione grafica.  Questi sei portano il messaggio fino al ponte di
 *    `main.c`, che e' l'unico che conosce tutt'e due i lati.
 *
 * ⚠ E il valore di ritorno e' quello di `input.h`, TRE stati: 0 consegnato,
 *   -1 no, 1 «non producibile» (solo la lettera).  ⛔ Qui pero' il terzo non
 *   si puo' distinguere — l'iniezione avviene oltre il confine di processo, e
 *   la risposta non torna indietro.  ⇒ **Si risponde 0 = «consegnato al
 *   palco»**, e chi conta davvero quel che il compositore ha PRESO e' il
 *   figlio, che lo timbra sul fotogramma (§6.2).  Questa asimmetria e'
 *   dichiarata e non nascosta: e' il prezzo del confine di processo. */
static wt_input_richiesta gancio_palco_input;
static void *gancio_palco_input_ctx;

void wt_input_gancio(wt_input_richiesta f, void *ctx)
{
	gancio_palco_input = f;
	gancio_palco_input_ctx = ctx;
}

static int input_al_palco(wt *w, uint32_t id, uint8_t azione, uint16_t codice,
                          int premuto, int32_t a, int32_t b)
{
	const char *mio;
	if (!gancio_palco_input || !w->rcp)
		return -1;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return -1;
	return gancio_palco_input(gancio_palco_input_ctx, mio, id, azione, codice,
	                          premuto, a, b)
	           ? 0
	           : -1;
}

static int gancio_input_puntatore(void *ctx, uint32_t x, uint32_t y)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_PUNTATORE,
	                      0, 0, (int32_t)x, (int32_t)y);
}

static int gancio_input_pulsante(void *ctx, uint16_t codice, int premuto)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_PULSANTE,
	                      codice, premuto, 0, 0);
}

static int gancio_input_rotella(void *ctx, int32_t asse_x, int32_t asse_y)
{
	wt *w = (wt *)ctx;
	/* ⛔ Il segno NON si tocca qui, e i mezzi scatti passano interi: `RCP.md`
	 *    §7.3 mette l'inversione dentro `input_rotella()`, una volta sola.
	 *    Invertirlo anche qui lo annullerebbe. */
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_ROTELLA, 0,
	                      0, asse_x, asse_y);
}

static int gancio_input_lettera(void *ctx, uint32_t carattere)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_LETTERA, 0,
	                      0, (int32_t)carattere, 0);
}

static int gancio_input_posizione(void *ctx, uint16_t codice, int premuto)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_POSIZIONE,
	                      codice, premuto, 0, 0);
}

static int gancio_input_rilascia_tutto(void *ctx)
{
	wt *w = (wt *)ctx;
	/* ⛔⭐ «La regola col rapporto danno/costo piu' alto del documento»
	 *     (`RCP.md` §11).  ⚠ E il conto di quanti ne ha rilasciati resta al
	 *     figlio: qui non torna indietro, e si risponde 0 — che vuol dire «la
	 *     richiesta e' partita», non «non c'era niente». */
	return input_al_palco(w, 0, FIGLI_INPUT_RILASCIA_TUTTO, 0, 0, 0, 0);
}

/* ⭐⭐ IL GANCIO DELLA TELA — §7.1, e la catena intera in una riga:
 *
 *     `rcp.c` (T_ADATTA_TELA) → questo → `main.c` → `figli_ritela()` →
 *     `MSG_INPUT/RITELA` → `cattura_ridimensiona()` → `pw_stream_update_params()`
 *
 * ⛔ E la risposta NON torna da qui: torna con un fotogramma alla misura nuova,
 *    che `video_a_una()` riporta a `rcp_tela_concessa()`.  ⚠ Chi leggesse questo
 *    `true` come «la tela e' cambiata» rifarebbe l'errore che `wayvnc` fa con
 *    l'esito della richiesta (`DECISIONI.md` §5.0-sexies, «la regola di forma
 *    rubata a neatvnc»). */
static wt_ritela_richiesta gancio_palco_ritela;
static void *gancio_palco_ritela_ctx;

void wt_ritela_gancio(wt_ritela_richiesta f, void *ctx)
{
	gancio_palco_ritela = f;
	gancio_palco_ritela_ctx = ctx;
}

static bool gancio_ritela(void *ctx, uint32_t larghezza, uint32_t altezza)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_ritela || !w->rcp)
		return false;
	/* ⛔ Invariante I3: la tela si cambia al palco di CHI HA CHIESTO, e il nome
	 *    e' quello che PAM ha ammesso su questa sessione — non un parametro che
	 *    viene dal filo.  Un utente che potesse ridimensionare il monitor di un
	 *    altro sarebbe un difetto piccolo con una faccia grossa: il desktop
	 *    dell'altro che cambia misura da solo. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_ritela(gancio_palco_ritela_ctx, mio, larghezza, altezza);
}

/* ⭐⭐ §5.1 — «QUEST'UTENTE HA GIA' UNA SESSIONE GRAFICA LOCALE?»
 *
 * ⛔ Il gancio verso `sentinella.c`, e vive qui per la stessa ragione degli
 *    altri: `rcp.c` esiste in due copie e quella innestata in ngtcp2 non ha un
 *    bus di sistema.  Chi non lo collega non applica la regola, e `rcp.c` lo
 *    scrive nel registro invece di tacere. */
static wt_locale_richiesta gancio_locale;
static void *gancio_locale_ctx;

void wt_locale_gancio(wt_locale_richiesta f, void *ctx)
{
	gancio_locale = f;
	gancio_locale_ctx = ctx;
}

static bool gancio_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	(void)ctx;
	if (!gancio_locale)
		return false;
	return gancio_locale(gancio_locale_ctx, utente, quale, quanto);
}

/* ⭐⭐ §7.6 — «l'utente ha chiesto di uscire». */
static wt_termina_richiesta gancio_termina;
static void *gancio_termina_ctx;

void wt_termina_gancio(wt_termina_richiesta f, void *ctx)
{
	gancio_termina = f;
	gancio_termina_ctx = ctx;
}

static void gancio_termina_sessione(void *ctx)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_termina || !w->rcp)
		return;
	/* ⛔ Invariante I3: si termina la sessione di CHI HA CHIESTO, e il nome e'
	 *    quello che PAM ha ammesso su questa sessione — non un parametro che
	 *    viene dal filo.  Un utente che potesse chiudere la sessione di un
	 *    altro sarebbe il difetto piu' caro del documento. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return;
	gancio_termina(gancio_termina_ctx, mio);
}

static bool gancio_video_apri(void *ctx, int64_t *stream, uint64_t *restano)
{
	wt *w = (wt *)ctx;
	uint8_t pre[16];
	size_t n = 0;
	int64_t id = -1;

	if (restano)
		*restano = 0;
	if (!w->conn || w->sessione == -1 || w->guasto)
		return false;
	if (restano)
		*restano = ngtcp2_conn_get_streams_uni_left2(w->conn);

	/* ⚠ `false` qui vuol dire «non adesso», e `rcp.c` lo traduce in «non e'
	 *   partito un byte» — che e' meglio di mezzo fotogramma.  ⛔ La ragione
	 *   piu' probabile e' che il client non conceda altri stream
	 *   unidirezionali, e allora si dice quanti gliene restano invece di
	 *   scrivere «non si e' potuto». */
	if (ngtcp2_conn_open_uni_stream(w->conn, &id, NULL) != 0) {
		registro_dettaglio(REG_WT,
		              "nessuno stream unidirezionale per il fotogramma: il "
		              "client ne concede ancora %llu (§2.5 ne vuole uno PER "
		              "fotogramma).  ⚠ La riga che decide — delta si butta, "
		              "chiave si aspetta — la scrive `rcp.c` (§2.3)",
		              (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
			              w->conn));
		return false;
	}

	/* ⛔ Quanto credito ngtcp2 CREDE di avere, chiesto a lui e non dedotto
	 *    (`LEZIONI.md` §1.6).  ⚠ Serve a distinguere «il pari non ci ha dato
	 *    credito» da «ce l'ha dato e uno dei due conta male»: il 13 agosto 2026
	 *    un cliente che dichiarava `initial_max_streams_uni = 6` ha chiuso con
	 *    `STREAM_LIMIT_ERROR` dopo che avevamo aperto 11 stream, e senza questa
	 *    riga di chi fosse il conto sbagliato si poteva solo indovinare. */
	registro_dettaglio(REG_WT,
	                   "stream uni %ld aperto per un fotogramma; ngtcp2 dice che "
	                   "ne restano %llu",
	                   (long)id,
	                   (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
		                   w->conn));

	n += varint_scrivi(pre + n, 0x54);
	n += varint_scrivi(pre + n, (uint64_t)w->sessione);

	if (!coda_metti(w, id, pre, n, false)) {
		/* ⛔ Lo stream e' stato aperto e il preambolo non c'e': si AZZERA
		 *    invece di lasciarlo aperto e muto.  Uno stream unidirezionale
		 *    aperto e mai scritto tiene un posto nel conto del client e non
		 *    diventa mai un fotogramma: e' la forma «vuoto e proibito hanno la
		 *    stessa faccia», dal lato di chi aspetta. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, id, 0);
		registro_dice(REG_WT,
		              "⛔ il preambolo di WebTransport (%zu byte) non entra in "
		              "coda: stream %ld azzerato, nessun fotogramma",
		              n, (long)id);
		return false;
	}
	*stream = id;
	/* ⛔ Qui e in nessun altro posto: `rcp.c` non restituisce l'identificatore
	 *    dello stream che ha aperto, e ricavarlo da «l'ultimo aperto sulla
	 *    connessione» sarebbe indovinare.  ⭐ Senza questo, §5.1 non ha nessun
	 *    modo di dire QUALE stream azzerare quando ne parte uno piu' recente. */
	w->video_stream_ultimo = id;
	return true;
}

static bool gancio_video_scrivi(void *ctx, int64_t stream, const uint8_t *dati,
                                size_t len)
{
	/* ⛔ `false` = «non sono entrati», e chi chiama AZZERA: `rcp.c` non chiude
	 *    mai con FIN uno stream a cui manca un pezzo, perche' FIN e'
	 *    un'affermazione (§6.2). */
	return coda_metti((wt *)ctx, stream, dati, len, false);
}

static void gancio_video_fin(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	/* ⛔ Il FIN e' un elemento della coda come gli altri, e NON si scrive
	 *    subito: deve uscire DOPO i byte che lo precedono, e la coda e' quel
	 *    che tiene l'ordine.  ⚠ Un `shutdown_stream_write` qui chiuderebbe lo
	 *    stream mentre i suoi byte sono ancora in coda — cioe' consegnerebbe
	 *    un fotogramma troncato marcato «completo». */
	if (!coda_metti(w, stream, NULL, 0, true))
		registro_dice(REG_WT,
		              "⛔ il FIN dello stream %ld non entra in coda: il "
		              "fotogramma e' uscito ma non e' dichiarato completo",
		              (long)stream);
}

static void gancio_video_azzera(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	if (!w->conn)
		return;
	/* ⛔ §5.1/§6.2: `RESET_STREAM` ⇒ il client BUTTA quel che e' arrivato e lo
	 *    tratta come un buco. */
	ngtcp2_conn_shutdown_stream_write(w->conn, 0, stream, 0);
	/* ⛔⭐ E I BYTE ANCORA IN CODA SI BUTTANO QUI, NON «alla prossima passata».
	 *
	 *     Il commento di prima diceva che li avrebbe scartati `wt_scrivi()` sul
	 *     ramo `NGTCP2_ERR_STREAM_SHUT_WR`, e con un fotogramma solo per
	 *     sessione era vero e bastava.  ⛔ A sessanta al secondo no: quei byte
	 *     restano contati in `byte_in_coda` fino alla passata dopo, cioe' il
	 *     tetto della coda morde su roba che si e' gia' deciso di non spedire —
	 *     e §5.1 dice **«i byte non ancora spediti non partono affatto»**, non
	 *     «partono dopo».  ⚠ Il conto non si sfasa: `coda_butta_stream()` passa
	 *     da `coda_uccidi()`, che e' l'unico punto in cui `byte_in_coda` cala. */
	coda_butta_stream(w, stream);
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

/* ========================================================================== */
/* ⭐⭐ IL CICLO DEI FOTOGRAMMI — FASE 3, «il desktop che si muove»            */
/*                                                                            */
/* ⛔⭐ CHE COSA C'ERA QUI PRIMA, E PERCHE' E' STATO TOLTO                     */
/*                                                                            */
/*    Fino alla fase 2 questo posto conteneva un DEPOSITO DI PROCESSO:        */
/*    `struct video_deposito video_dep[3]`, riempito una volta all'accensione */
/*    e letto da ogni sessione che arrivasse a `SESSIONE`.  Aveva tre difetti */
/*    dichiarati, e tutt'e tre sono di questa fase:                            */
/*                                                                            */
/*      1. era di PROCESSO e non di sessione — `main.c` §«il deposito e la    */
/*         fuga» lo dichiara: «la cura vera e' un deposito per sessione».  Il */
/*         ripiego era un PADRONE del deposito, e il prezzo dichiarato era    */
/*         che due utenti collegati insieme non potevano vedere tutt'e due il */
/*         proprio desktop;                                                    */
/*      2. marcava `chiave = true` **per costruzione**, e con chiave/delta    */
/*         veri quella riga diventa **una bugia sul filo** (§6.2, campo       */
/*         `tipo`);                                                            */
/*      3. serviva UN fotogramma per sessione, e il freno era `bool           */
/*         video_fatto`.                                                       */
/*                                                                            */
/* ⇒ Al suo posto c'e' una DIFFUSIONE: il figlio dell'utente cattura e        */
/*   codifica di continuo, `main.c` gira ogni fotogramma qui dentro, e questa */
/*   funzione lo consegna **alle sessioni di quell'utente e a nessun'altra**. */
/*   ⛔ Il confronto sul nome dell'utente e' l'invariante I3 sul filo, ed e'  */
/*   la stessa guardia di prima messa dove serviva: non piu' «di chi e' il    */
/*   deposito», ma «di chi e' questa sessione».  Due utenti collegati insieme */
/*   adesso vedono ciascuno il proprio.                                        */
/*                                                                            */
/* ⚠ E QUEL CHE NON SI FA, DICHIARATO: i byte NON si copiano.  Il fotogramma  */
/*   arriva da `main.c`, viene messo in coda a ciascuna sessione (che lo copia */
/*   lei, in `coda_metti`) e poi il chiamante puo' liberarlo.  Un deposito     */
/*   intermedio qui sarebbe una copia in piu' per fotogramma, cioe' fino a 60  */
/*   copie al secondo di qualche centinaio di KiB.                             */

/* ⛔ L'elenco delle sessioni vive.  Serve perche' i fotogrammi arrivano da
 *    FUORI (dal figlio, per la mano di `main.c`) e non da un evento di questa
 *    connessione: senza un elenco, chi diffonde dovrebbe tenersi lui i
 *    puntatori, e due elenchi dello stesso insieme divergono. */
static wt *vive_prima;

static wt_video_richiesta gancio_palco;
static void *gancio_palco_ctx;

void wt_video_gancio(wt_video_richiesta f, void *ctx)
{
	gancio_palco = f;
	gancio_palco_ctx = ctx;
}

/* ⛔ Ogni quanto si puo' RIchiedere una chiave al palco mentre il debito e'
 *    ancora acceso.  ⚠ Non e' la grazia di §5.2 — quella e' di `rcp.c` e conta
 *    dall'ultima chiave SPEDITA: questo e' il fondo di una richiesta che deve
 *    ancora attraversare un socket, un processo e un codificatore.  Senza,
 *    ogni battito ne manderebbe una e il figlio codificherebbe solo chiavi. */
#define WT_CHIAVE_RICHIESTA_MS 150

/* ⛔ Quanti stream uni servono al video PRIMA di dire «senza credito»: `RCP.md`
 *    §2.3 vuole che l'input ne trovi sempre uno, e il video non deve mangiarsi
 *    l'ultimo posto.  ⚠ Il numero e' il minimo che §2.3 riserva a RCP diviso a
 *    meta': si dichiara qui perche' e' una scelta nostra, non una riga
 *    dell'arbitro. */
#define WT_UNI_RISERVA 2

/* ------------------------------------------------------------------------ */
/* ⭐ §5.1 — L'ABBANDONO, ED E' QUELLO CHE SI VEDE DAL LATO CHE RICEVE.       */

static void involo_pulisci(wt *w)
{
	size_t j = 0;
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo)
			w->involo[j++] = w->involo[i];
	w->ninvolo = j;
}

/* ⛔ §5.1: «il server PUO' chiamare `RESET_STREAM` su un fotogramma che non
 *    serve piu' — perche' ne e' gia' partito uno piu' recente — e i byte non
 *    ancora spediti non partono affatto».
 *
 * ⚠ «Non ancora spediti» vuol dire «ancora nella NOSTRA coda»: quel che e' gia'
 *   passato a ngtcp2 non lo riprendiamo, e azzerare li' non risparmierebbe piu'
 *   niente.  ⇒ Un fotogramma senza byte in coda esce dall'elenco senza che si
 *   scriva niente: non e' stato abbandonato, e' stato spedito. */
static void video_sgombra(wt *w, const char *perche)
{
	if (!w->rcp || !w->conn)
		return;
	for (size_t i = 0; i < w->ninvolo; i++) {
		size_t rimasti;
		if (!w->involo[i].vivo)
			continue;
		rimasti = coda_byte_stream(w, w->involo[i].stream);
		if (rimasti == 0) {
			w->involo[i].vivo = false;
			continue;
		}
		if (w->involo[i].chiave) {
			/* ⛔ §5.2: «il server NON DEVE abbandonare un fotogramma chiave.
			 * Abbandonare la cura non e' una cura».  ⚠ E si dice UNA volta,
			 * perche' e' una cosa che dura finche' la linea non la porta via:
			 * ripeterla a ogni fotogramma renderebbe illeggibile il registro
			 * proprio quando serve. */
			if (!w->involo[i].detto) {
				w->involo[i].detto = true;
				registro_dice(REG_RCP,
				              "⚠ %s: la CHIAVE %u tiene ancora %zu byte in coda "
				              "e §5.2 vieta di abbandonarla: si ASPETTA.  ⭐ E i "
				              "delta che vengono dopo non sono bloccati da lei — "
				              "gli stream sono indipendenti (§5.1)",
				              w->provenienza, w->involo[i].numero, rimasti);
			}
			continue;
		}
		/* ⛔ La riga di registro, il conto e il debito della chiave sono di
		 * `rcp.c`: due copie dello stesso stato divergono. */
		if (!rcp_video_abbandonato_a_valle(w->rcp, w->involo[i].numero, false,
		                                   rimasti, perche))
			continue;
		/* ⛔ PRIMA si azzera lo stream, POI si buttano i byte.  Al contrario
		 * resterebbe una finestra — corta ma vera — in cui lo stream e' vivo e
		 * i suoi byte non ci sono piu': `wt_scrivi()` lo troverebbe muto invece
		 * che azzerato, e il client aspetterebbe una fine che non arriva. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, w->involo[i].stream, 0);
		coda_butta_stream(w, w->involo[i].stream);
		w->involo[i].vivo = false;
	}
	involo_pulisci(w);
}

static void involo_aggiungi(wt *w, int64_t stream, uint32_t numero, bool chiave)
{
	if (stream < 0)
		return;
	involo_pulisci(w);
	if (w->ninvolo >= WT_INVOLO_MAX) {
		/* ⚠ Si dice invece di scivolare: da qui in poi quel fotogramma non
		 *   sara' abbandonabile, e chi legge il registro deve saperlo — un
		 *   abbandono che non avviene perche' una tabella e' piena somiglia in
		 *   tutto a un abbandono che nessuno ha chiesto. */
		registro_dice(REG_WT,
		              "⚠ %s: %u fotogrammi gia' in volo: il %u non entra "
		              "nell'elenco e NON potra' essere abbandonato (§5.1)",
		              w->provenienza, WT_INVOLO_MAX, numero);
		return;
	}
	w->involo[w->ninvolo].stream = stream;
	w->involo[w->ninvolo].numero = numero;
	w->involo[w->ninvolo].chiave = chiave;
	w->involo[w->ninvolo].vivo = true;
	w->involo[w->ninvolo].detto = false;
	w->ninvolo++;
}

/* ------------------------------------------------------------------------ */
/* ⭐ LA CUCITURA FRA LA CHIAVE CHIESTA E IL CODIFICATORE — punto 4.          */

/* ⛔ `rcp_video_serve_chiave()` era LETTA e non serviva a niente:
 *    `codificatore_chiedi_chiave()` non aveva **nessun chiamante nel prodotto**.
 *    ⇒ Un `RICHIEDI_CHIAVE` del client accendeva un `bool` in `rcp.c`, il
 *    fotogramma dopo era un delta, `rcp_video_apri()` lo rifiutava con
 *    `RCP_VIDEO_SERVE_UNA_CHIAVE`, e **lo schermo restava fermo per sempre** —
 *    perche' `chiavi_ogni = 0` da' GOP infinito e dopo la prima chiave non ne
 *    arriva mai piu' una da sola.
 *
 * ⇒ Il gancio: il palco sta in un ALTRO PROCESSO (il figlio dell'utente), e
 *   questa e' la riga che attraversa il confine.  ⚠ Sta qui e non in `rcp.c`
 *   perche' `rcp.c` non conosce i figli, e non in `main.c` perche' `main.c` non
 *   conosce lo stato della sessione. */
static void video_regola(wt *w, uint64_t ora_ms)
{
	uint32_t l = 0, a = 0;
	uint8_t codec;
	const char *utente;

	if (!w->rcp || w->chiusura >= 0)
		return;

	/* ⛔ P1 / §2.5 / invariante I3 — «nessuno stream video prima di aver
	 *    SPEDITO `SESSIONE`».  `rcp_tela_in_vigore()` risponde `false` finche'
	 *    `SESSIONE` non e' partita, e non scrive niente nel registro: chiamare
	 *    `rcp_video_apri()` per saperlo riempirebbe il registro di una riga al
	 *    secondo per ogni sessione in attesa della parola d'ordine. */
	if (!rcp_tela_in_vigore(w->rcp, &l, &a))
		return;

	codec = rcp_codec_negoziato(w->rcp);
	if (codec == 0) {
		if (!w->video_detto) {
			/* ⚠ Non e' un difetto: un client della fase 1 non dichiara nessun
			 *   codec, e §4.3 gli da' ragione. */
			w->video_detto = true;
			registro_dice(REG_RCP,
			              "%s: nessun codec negoziato (§4.3) — questa sessione "
			              "non ha video, ed e' quel che la fase 1 faceva",
			              w->provenienza);
		}
		return;
	}

	utente = rcp_utente(w->rcp);
	if (!utente || !utente[0])
		return;

	if (!w->video_acceso) {
		w->video_acceso = true;
		w->video_codec = codec;
		w->chiave_chiesta_ms = ora_ms;
		registro_dice(REG_RCP,
		              "⭐ FASE 3: canale video ACCESO per «%s» da %s — codec %u, "
		              "tela %ux%u.  Chiedo al palco di catturare di continuo, e "
		              "§5.2 vuole che il PRIMO sia una CHIAVE",
		              utente, w->provenienza, codec, l, a);
		if (gancio_palco)
			gancio_palco(gancio_palco_ctx, utente, codec, true);
		return;
	}

	/* ⛔ E qui la chiave chiesta arriva davvero al codificatore. */
	if (rcp_video_serve_chiave(w->rcp)
	    && ora_ms - w->chiave_chiesta_ms >= WT_CHIAVE_RICHIESTA_MS) {
		w->chiave_chiesta_ms = ora_ms;
		if (gancio_palco)
			gancio_palco(gancio_palco_ctx, utente, codec, true);
		registro_dettaglio(REG_RCP,
		                   "%s: §5.2 vuole una CHIAVE — richiesta girata al "
		                   "palco di «%s» (codec %u)",
		                   w->provenienza, utente, codec);
	}
}

/* ------------------------------------------------------------------------ */
/* ⭐ IL FOTOGRAMMA CHE ARRIVA DAL PALCO, CONSEGNATO A UNA SESSIONE.          */

static void video_a_una(wt *w, const char *utente, uint8_t codec, bool chiave,
                        const uint8_t *dati, size_t byte, uint32_t l, uint32_t a,
                        uint64_t istante_us, uint32_t input)
{
	uint32_t tl = 0, ta = 0;
	uint64_t ora_ms;
	const char *mio;
	int e;

	if (!w->video_acceso || w->video_codec != codec)
		return;
	if (!w->rcp || !w->conn || w->chiusura >= 0)
		return;

	/* ⛔⭐ INVARIANTE I3 SUL FILO, E NON E' UNA PRUDENZA IN PIU'.
	 *
	 *     `[M]` 12 agosto 2026: con un deposito di processo, «prova» (uid 1001,
	 *     senza sessione grafica) ha ricevuto **un fotogramma conforme**, e quel
	 *     fotogramma era il desktop di «nicfio».  Non «non ricevi niente»:
	 *     **ricevi il desktop di un altro**, e nessuno dei due se ne accorge.
	 *     ⇒ Qui il confronto e' fra l'utente che ha CATTURATO e l'utente che
	 *     PAM ha ammesso su questa sessione, e sono due fatti diversi tutti e
	 *     due chiesti a chi li sa. */
	mio = rcp_utente(w->rcp);
	if (!mio || !utente || strcmp(mio, utente) != 0)
		return;

	if (!rcp_tela_in_vigore(w->rcp, &tl, &ta))
		return;

	/* ⛔⭐ E LA TELA DEV'ESSERE QUELLA, non «piu' o meno quella» — §6.2, P5.
	 *
	 *     I 28 byte portano `largh.`/`altezza` = la tela IN VIGORE, e li scrive
	 *     `rcp.c` dalla sua.  Se il fotogramma catturato ne portasse un'altra,
	 *     l'intestazione direbbe una misura e i pixel ne porterebbero un'altra:
	 *     due verita' sulla stessa cosa, e il client non avrebbe modo di
	 *     accorgersene — il decodificatore prende la misura dal flusso.
	 *     ⛔ Meglio nessun fotogramma che un fotogramma che mente. */
	if (tl != l || ta != a) {
		w->video_saltati++;
		/* ⚠ Un fondo SUO, e non piu' `video_detto`: quel campo e' il fondo del
		 *   messaggio «nessun codec negoziato», e un flag per due fatti diversi
		 *   ne spegne uno quando l'altro parla.  ⛔ E qui il fondo si RIARMA a
		 *   ogni cambio di tela, perche' il fatto e' cambiato. */
		if (w->tela_detta_l != l || w->tela_detta_a != a) {
			w->tela_detta_l = l;
			w->tela_detta_a = a;
			registro_dice(REG_RCP,
			              "⛔ %s: tela in vigore %ux%u ma il fotogramma catturato "
			              "e' %ux%u — NON lo spedisco (§6.2): l'intestazione "
			              "direbbe una misura e i pixel ne porterebbero un'altra.  "
			              "⚠ Al palco si sta richiedendo la tela in vigore",
			              w->provenienza, tl, ta, l, a);
		}
		return;
	}
	/* ⭐ Tela e fotogramma sono d'accordo: il fondo del messaggio di sopra si
	 *    disarma, cosi' il prossimo disaccordo si vedra' invece di essere
	 *    scambiato per la coda di quello di prima. */
	w->tela_detta_l = w->tela_detta_a = 0;

	ora_ms = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;

	/* ⛔ §5.1 — «ne e' gia' partito uno piu' recente»: i delta ancora fermi
	 * nella coda si azzerano PRIMA di accodare questo, o la coda crescerebbe
	 * col passato invece di portare il presente. */
	video_sgombra(w, "ne e' partito uno piu' recente (§5.1)");

	/* ⛔ §2.3 — e il credito si guarda PRIMA di chiedere lo stream, per poter
	 * distinguere «non c'era posto» da «lo stream si e' rotto».  ⚠ La riserva
	 * e' per l'input: §2.3 esiste perche' senza credito «l'input non partirebbe
	 * affatto e il sintomo sarebbe il desktop non risponde». */
	if (!chiave
	    && ngtcp2_conn_get_streams_uni_left2(w->conn) <= WT_UNI_RISERVA) {
		w->video_saltati++;
		rcp_video_niente_credito(w->rcp, false,
		                         ngtcp2_conn_get_streams_uni_left2(w->conn));
		return;
	}

	w->video_stream_ultimo = -1;
	e = rcp_video_spedisci(w->rcp, chiave, dati, byte, istante_us, input, ora_ms);
	if (e == RCP_VIDEO_SPEDITO) {
		w->video_diffusi++;
		involo_aggiungi(w, w->video_stream_ultimo,
		                rcp_video_ultimo_numero(w->rcp), chiave);
		return;
	}

	w->video_saltati++;
	/* ⛔ E il rifiuto NON e' un errore fatale: §2.3 — «il server DEVE reggere
	 * il rifiuto di aprire uno stream invece di considerarlo un errore
	 * fatale».  ⚠ Le righe le ha gia' scritte `rcp.c`, che sa quale delle sette
	 * ragioni e': qui si conta e si tace, o la stessa cosa finirebbe due volte
	 * nel registro con due parole diverse. */
}

/* ⭐⭐ §7.2 — la forma del cursore a tutte le sessioni di quell'utente.
 *
 * ⛔ E il confronto del nome NON e' una formalita': il deposito e' di processo e
 *    le sessioni sono di utenti diversi.  Mandare la forma del cursore di un
 *    altro non e' un difetto grafico — e' l'immagine di quel che sta facendo
 *    un'altra persona che finisce sullo schermo sbagliato. */
void wt_cursore_diffondi(const char *utente, uint16_t larghezza,
                         uint16_t altezza, int16_t attivo_x, int16_t attivo_y,
                         const uint8_t *immagine, size_t byte)
{
	if (!utente || !utente[0])
		return;
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || strcmp(mio, utente) != 0)
			continue;
		/* ⚠ Il ritorno non si guarda qui: `rcp.c` ha gia' scritto nel registro
		 *   quale delle sue ragioni e' — e guardarlo anche noi metterebbe la
		 *   stessa cosa due volte con due parole diverse. */
		rcp_cursore_forma(w->rcp, larghezza, altezza, attivo_x, attivo_y,
		                  immagine, byte);
	}
}

/* ⛔⭐⭐ LA MISURA CHE IL PALCO HA ADESSO, per utente — e sopravvive alla
 *     connessione, come il palco (invariante I4).
 *
 * ⛔ SERVE AL RI-ATTACCO, ed e' l'unico posto del padre in cui quel numero
 *    esiste: `rcp.c` conosce la tela CONCESSA, il figlio conosce quella VERA, e
 *    fra i due passano solo fotogrammi.  ⇒ Si legge dal fotogramma — che e'
 *    anche l'unica fonte che non mente (`DECISIONI.md` §5.0-sexies).
 *
 * ⚠ Non e' una cache da tenere fresca: e' un FATTO datato all'ultimo fotogramma
 *   consegnato.  Se il palco muore e rinasce a un'altra misura, la prima riga di
 *   `rcp_tela_concessa()` se ne accorge e chiede al palco di venire dov'e' la
 *   tela in vigore.
 *
 * ⚠ Otto voci: `MAX_ATTACCATE` in `rcp.c` e' dello stesso ordine, e un utente
 *   in piu' che non trova posto perde solo questa comodita' — riparte come
 *   prima del 15 agosto 2026, cioe' concedendo quel che il client chiede. */
#define WT_PALCHI 8
static struct {
	/* ⛔ 257 e non 64: e' la misura del campo `utente` di `rcp.c`.  ⚠ Con un
	 *    campo piu' corto `snprintf` troncava in scrittura e `strcmp` confrontava
	 *    il nome INTERO con quello troncato: la voce non si ritrovava mai, se ne
	 *    prendeva una nuova a ogni fotogramma, e in otto giri la tabella era piena
	 *    dello stesso nome — spenta **per tutti gli utenti della macchina**.
	 *    Difetto trovato refutando, 15 agosto 2026. */
	char utente[257];
	uint32_t l, a;
} palchi[WT_PALCHI];
static bool palchi_pieni_detto;

static void palco_misura_segna(const char *utente, uint32_t l, uint32_t a)
{
	int libero = -1;

	if (!utente || !utente[0] || !l || !a)
		return;
	for (int i = 0; i < WT_PALCHI; i++) {
		if (palchi[i].utente[0] == '\0') {
			if (libero < 0)
				libero = i;
			continue;
		}
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		palchi[i].l = l;
		palchi[i].a = a;
		return;
	}
	if (libero < 0) {
		/* ⛔ Il ripiego si DICHIARA (`CODER.md` §4.2), e una volta sola: senza
		 *    questa riga il nono utente perdeva la cura del ri-attacco in
		 *    silenzio, e il sintomo sarebbe stato «a me il desktop al riattacco
		 *    non torna» per quel solo utente. */
		if (!palchi_pieni_detto) {
			palchi_pieni_detto = true;
			registro_dice(REG_RCP,
			              "⚠ RIPIEGO DICHIARATO: la tabella delle tele dei palchi "
			              "e' piena (%d): «%s» non ci sta, e al suo ri-attacco la "
			              "tela verra' concessa come la chiede il client invece "
			              "che come il palco ce l'ha",
			              WT_PALCHI, utente);
		}
		return;
	}
	snprintf(palchi[libero].utente, sizeof palchi[libero].utente, "%s", utente);
	palchi[libero].l = l;
	palchi[libero].a = a;
}

/* ⛔⭐ IL PALCO E' MORTO: la sua misura non e' piu' un fatto, e' un ricordo.
 *
 * ⚠ Difetto trovato refutando: senza questa riga la voce restava, e al
 *   ri-attacco `SESSIONE` concedeva **la misura di ieri** — quella di un palco
 *   che non esiste piu'.  Il palco nuovo ne consegna un'altra, la sessione nasce
 *   in disaccordo, e la cura del ri-attacco si ritorceva contro se stessa.
 * ⛔ «Non lo so» e «era 1920x1080» sono due fatti diversi, e il secondo, quando
 *    e' falso, e' peggio del primo. */
void wt_palco_dimentica(const char *utente)
{
	if (!utente || !utente[0])
		return;
	for (int i = 0; i < WT_PALCHI; i++) {
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		registro_dice(REG_RCP,
		              "la tela del palco di «%s» (%ux%u) si dimentica: quel palco "
		              "non c'e' piu', e un numero vecchio spacciato per fatto e' "
		              "peggio di nessun numero",
		              utente, palchi[i].l, palchi[i].a);
		memset(&palchi[i], 0, sizeof palchi[i]);
		palchi_pieni_detto = false;
		return;
	}
}

/* ⭐⭐ LA RISPOSTA DEL PALCO SULLA TELA — §7.1, e arriva dal FIGLIO.
 *
 * ⛔ Va a TUTTE le sessioni di quell'utente, e non solo a chi ha chiesto: la
 *    tela del palco e' una sola, e una sessione che non lo sapesse continuerebbe
 *    a scartare ogni fotogramma per misura sbagliata.  ⚠ `rcp.c` decide da se'
 *    se quel messaggio risponde a una SUA richiesta — qui non si sceglie. */
void wt_tela_dal_palco(const char *utente, uint32_t voluta_l, uint32_t voluta_a,
                       uint32_t avuta_l, uint32_t avuta_a)
{
	/* ⛔ E la tabella si aggiorna QUI e non solo dai fotogrammi: questa e' la
	 *    notizia piu' fresca che il padre abbia sulla misura del palco, e arriva
	 *    anche quando nessun fotogramma parte. */
	palco_misura_segna(utente, avuta_l, avuta_a);
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		rcp_tela_dal_palco(w->rcp, voluta_l, voluta_a, avuta_l, avuta_a,
		                   w->conn ? ngtcp2_conn_get_timestamp(w->conn)
		                                 / NGTCP2_MILLISECONDS
		                           : 0);
	}
}

static bool wt_palco_misura(const char *utente, uint32_t *l, uint32_t *a)
{
	if (!utente || !utente[0])
		return false;
	for (int i = 0; i < WT_PALCHI; i++) {
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		if (!palchi[i].l || !palchi[i].a)
			return false;
		if (l)
			*l = palchi[i].l;
		if (a)
			*a = palchi[i].a;
		return true;
	}
	return false;
}

/* ⛔ Il gancio che `rcp.c` chiama in `ATTACCA`.  ⚠ L'utente e' quello che PAM ha
 *    ammesso su QUESTA sessione: chiedere il palco di un altro sarebbe dire a
 *    questo client la misura del desktop di qualcun altro. */
static bool gancio_tela_del_palco(void *ctx, uint32_t *l, uint32_t *a)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!w->rcp)
		return false;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return wt_palco_misura(mio, l, a);
}

size_t wt_sorveglia_locali(void)
{
	size_t congedate = 0;

	if (!gancio_locale)
		return 0;

	/* ⛔ Si guarda la lista a ogni giro invece di tenere un elenco di utenti:
	 *    una sessione puo' nascere e morire fra due ripassi, e un elenco che si
	 *    aggiorna da solo e' un secondo stato da tenere d'accordo col primo —
	 *    cioe' il modo in cui due verita' entrano in un programma. */
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		char quale[160];
		const char *mio;

		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !mio[0])
			continue;

		quale[0] = '\0';
		if (!gancio_locale(gancio_locale_ctx, mio, quale, sizeof quale))
			continue;

		/* ⛔⭐ §5.1: «ha una sessione grafica REMOTA attiva e ne apre una
		 *     LOCALE ⇒ **la locale vince**: la remota viene chiusa».
		 *
		 * ⭐ Ed e' l'unico punto del prodotto in cui il server porta via una
		 *    sessione SANA — `DECISIONI.md` §4.1-bis lo ammette **solo** con un
		 *    motivo dicibile, ed e' per questo che `0x04` esiste. */
		registro_dice(REG_WT,
		              "⛔ «%s» ha aperto una sessione grafica LOCALE (%s): la "
		              "sessione remota viene chiusa — §5.1, motivo 0x04",
		              mio, quale[0] ? quale : "senza dettaglio");
		wt_congeda(w, RCP_SESSIONE_LOCALE_PREVALSA,
		           "e' stata aperta una sessione grafica locale su questa "
		           "macchina");
		congedate++;
	}
	return congedate;
}

void wt_tela_rimanda(const char *utente, uint32_t voluta_l, uint32_t voluta_a)
{
	uint64_t ora = registro_ora_ms();

	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		rcp_tela_rimanda(w->rcp, voluta_l, voluta_a, ora);
	}
}

size_t wt_congeda_utente(const char *utente, uint8_t motivo, const char *dettaglio,
                         const wt *tranne)
{
	size_t quante = 0;

	if (!utente || !utente[0])
		return 0;
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;

		if (w == tranne || !w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || strcmp(mio, utente) != 0)
			continue;
		wt_congeda(w, motivo, dettaglio);
		quante++;
	}
	return quante;
}

void wt_video_diffondi(const char *utente, uint8_t codec, bool chiave,
                       const uint8_t *dati, size_t byte, uint32_t larghezza,
                       uint32_t altezza, uint64_t istante_us, uint32_t input)
{
	if (codec != 1 && codec != 2)
		return;
	/* ⛔ Si segna PRIMA di consegnare, e vale anche se non c'e' nessuna sessione
	 *    a cui consegnare: e' un fatto del palco, non della connessione — ed e'
	 *    esattamente il caso del ri-attacco, dove la sessione che vedra' quel
	 *    numero **non esiste ancora**. */
	palco_misura_segna(utente, larghezza, altezza);
	for (wt *w = vive_prima; w; w = w->viva_dopo)
		video_a_una(w, utente, codec, chiave, dati, byte, larghezza, altezza,
		            istante_us, input);
}

bool wt_video_qualcuno_guarda(const char *utente, uint8_t *codec)
{
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->video_acceso || !w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		if (codec)
			*codec = w->video_codec;
		return true;
	}
	return false;
}

void wt_video_conti(const wt *w, uint32_t *diffusi, uint32_t *saltati,
                    uint32_t *spediti, uint32_t *abbandonati)
{
	if (diffusi)
		*diffusi = w ? w->video_diffusi : 0;
	if (saltati)
		*saltati = w ? w->video_saltati : 0;
	rcp_video_conti(w ? w->rcp : NULL, spediti, abbandonati);
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
	/* ⛔ E si collega SOLO se l'aiutante c'e': `rcp.c` guarda questo puntatore
	 *    per decidere quale delle due strade percorrere, e collegarlo a vuoto
	 *    vorrebbe dire dirgli «chiedi a nessuno». */
	if (w->aiuto)
		g.chiedi_verifica = gancio_chiedi;

	/* ⛔ §2.5: il canale video vive su stream unidirezionali del server.
	 *
	 * ⚠ E si collegano TUTTI E QUATTRO: `rcp.c` rifiuta di aprire se ne manca
	 *   uno, perche' un ospite che sapesse aprire e non azzerare non potrebbe
	 *   onorare §5.1 — e se ne accorgerebbe a meta' di un fotogramma.
	 * ⭐ La compatibilita' con l'innesto di `banchi/rcp/` e' gratis: li' il
	 *   `memset` di sopra li lascia a NULL, e `rcp_video_apri()` restituisce
	 *   `RCP_VIDEO_NIENTE_CANALE` invece di tacere. */
	g.video_apri = gancio_video_apri;
	g.video_scrivi = gancio_video_scrivi;
	g.video_fin = gancio_video_fin;
	g.video_azzera = gancio_video_azzera;

	/* ⭐⭐ §7.3 — IL CANALE DI INPUT.  ⛔ E si collegano TUTTI E SEI o nessuno:
	 *     `rcp.c` guarda il primo e se c'e' pretende gli altri, perche' un
	 *     canale che sapesse muovere il puntatore e non sapesse rilasciare un
	 *     pulsante lascerebbe il desktop **peggio di come l'ha trovato**.
	 * ⚠ E si collegano solo se il ponte verso il palco c'e': senza,
	 *   `rcp.c` convalida lo stesso il messaggio (quello e' protocollo) e
	 *   scrive che non l'ha iniettato.  «Non ho un canale di input» e «il
	 *   client ha sbagliato» sono due fatti diversi. */
	if (gancio_palco_input) {
		g.input_puntatore = gancio_input_puntatore;
		g.input_pulsante = gancio_input_pulsante;
		g.input_rotella = gancio_input_rotella;
		g.input_lettera = gancio_input_lettera;
		g.input_posizione = gancio_input_posizione;
		g.input_rilascia_tutto = gancio_input_rilascia_tutto;
	}

	/* ⭐⭐ §7.1 — IL GANCIO DELLA TELA, e si collega DA SOLO: non appartiene ai
	 *     sei dell'input, e la ragione e' che senza di lui `rcp.c` ha una
	 *     risposta giusta da dare — `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` —
	 *     mentre senza i sei dell'input non ce l'ha.
	 * ⚠ E come quelli, si collega solo se il ponte verso il palco c'e': un
	 *   gancio collegato a vuoto direbbe a `rcp.c` «so ridimensionare» e poi
	 *   lascerebbe il client ad aspettare un fotogramma che nessuno ha chiesto a
	 *   nessuno. */
	if (gancio_palco_ritela)
		g.ritela = gancio_ritela;

	/* ⛔⭐ E QUESTO SI COLLEGA SEMPRE, anche senza il ponte verso il palco: non
	 *     chiede niente a nessuno — legge un numero che questo modulo ha gia',
	 *     l'ultima misura consegnata dal palco di quell'utente.  ⚠ Se non c'e'
	 *     ancora (primo attacco, nessun fotogramma) risponde `false`, e `rcp.c`
	 *     concede quel che il client chiede: il comportamento di prima. */
	g.tela_del_palco = gancio_tela_del_palco;

	/* ⛔⭐ §5.1 — e si collega SOLO se il guardiano c'e', come tutti gli altri:
	 *     un gancio collegato a vuoto direbbe a `rcp.c` «ho guardato, non c'e'
	 *     nessuna sessione locale», che e' la bugia peggiore delle due — perche'
	 *     e' indistinguibile dalla verita'. */
	if (gancio_locale)
		g.sessione_locale = gancio_sessione_locale;

	/* ⭐ §7.6 — e si collega solo se c'e' chi puo' davvero terminare la
	 *    sessione: senza, `rcp.c` congeda con `0x10` e scrive che il desktop
	 *    non e' stato toccato, invece di far credere che sia finito. */
	if (gancio_termina)
		g.termina_sessione = gancio_termina_sessione;

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
	/* ⭐ E QUI, non un giro dopo: `rcp_ricevi()` e' la riga che puo' aver
	 *    appena spedito `SESSIONE`, e aspettare il battito costerebbe fino a un
	 *    secondo intero prima che il desktop compaia — cioe' il numero che
	 *    l'utente guarda. */
	video_regola(w, ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);
	regola_battito(w);
}

/* ⭐⭐ IL CANALE DI INPUT — la cucitura della fase 4, 14 agosto 2026.
 *
 * ⛔ Prima di oggi i byte dell'input arrivavano davvero e finivano in
 *    `conta_credito()` **e basta**: il canale era lecito, la riga di registro
 *    lo dichiarava («questa fase non lo serve»), e il client poteva muovere il
 *    mouse per un'ora senza che al desktop arrivasse niente.  ⇒ Qui quella
 *    tolleranza dichiarata si CHIUDE.
 *
 * ⚠ `stream` viaggia con i byte e non e' un di piu': `RCP.md` §2.5 ammette
 *   **un solo** stream di input, e senza l'identificatore `rcp.c` non puo'
 *   distinguere il secondo stream dalla continuazione del primo.  ⛔ E chi
 *   ospita non lo puo' giudicare al posto suo: vede gli stream, ma non sa che
 *   cosa sia «di input» finche' non ha letto i primi due byte del carico.
 *
 * ⚠ E il ritorno `false` si tratta come in `rcp_passa()`: la sessione e'
 *   finita, e la capsula di chiusura l'ha gia' armata `chiudi_sessione()`. */
static void rcp_passa_input(wt *w, int64_t stream, const uint8_t *dati,
                            size_t len)
{
	uint64_t ora;
	if (!w->rcp || len == 0)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi_input(w->rcp, stream, dati, len, ora))
		return;
	/* ⛔ E il battito si rimette in riga anche di qui: un input puo' aver
	 *    fatto scattare un congedo (una violazione di §7.3), e aspettare il
	 *    giro dopo lascerebbe il motivo fermo in coda. */
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
	/* ⛔⭐ L'ATTESA PARTE ADESSO, non «quando un battito vedra' la coda vuota»
	 *     — misurato dal banco B7 l'11 agosto 2026, caso `server-in-chiusura`.
	 *
	 *     Qui c'era `w->chiusura_da = 0`, cioe' «non armato»: ad armarlo era
	 *     il ramo di `wt_batti` che trova la coda gia' vuota.  ⛔ Allo
	 *     spegnimento quel ramo non veniva percorso mai — il registro del
	 *     server lo ha detto con queste parole: «capsula di chiusura non
	 *     ancora matura (coda vuota) — chiusura_da = MAI ARMATO» dopo 200
	 *     giri, quando ne bastavano cinquanta.
	 *
	 * ⛔ Che cosa vedeva il client: il `CONGEDO 0x0c` arrivava, e la sessione
	 *    si chiudeva SENZA codice — QUIC terminato con `codice 0, nessun
	 *    motivo`.  Cioe' mancava la SECONDA strada di §3.1 punto 3, che le
	 *    decisioni dell'11 agosto (§7.14, §7.15) rendono l'unica che arrivi
	 *    sempre — su Firefox, che azzera il canale, era l'UNICA.
	 *
	 * ⚠ E il senso non cambia: se la coda NON e' vuota, il ramo `!coda_vuota`
	 *   di `wt_batti` riazzera questo campo e l'attesa riparte da capo, come
	 *   prima.  Quel che cambia e' che adesso l'attesa esiste anche quando
	 *   nessuno ripassa a dire «la coda e' vuota». */
	w->chiusura_da = ngtcp2_conn_get_timestamp(w->conn)
	                 + WT_ATTESA_CHIUSURA_NS;
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
	const uint8_t *carico = NULL;
	size_t carico_n = 0;
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
		case G_UNI_INPUT:
			/* ⭐ Il canale di input, gia' riconosciuto: i byte si
			 *    contano nel credito **e si consegnano**.  ⛔ Il
			 *    credito prima della consegna: se la consegna facesse
			 *    cadere la sessione, quei byte sono comunque arrivati
			 *    e il conto di §2.3 non deve restare indietro. */
			conta_credito(w, stream_id, len);
			rcp_passa_input(w, stream_id, dati, len);
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
	/* ⛔ IL CARICO RCP COMINCIA QUI, e comincia **col `tipo`**: i due byte che
	 *    abbiamo appena sbirciato per sapere di che canale si tratta sono del
	 *    messaggio, non del preambolo.  ⚠ Sbirciarli e poi non consegnarli
	 *    darebbe a `rcp.c` un messaggio senza intestazione — e il sintomo
	 *    sarebbe «il primo input di ogni sessione e' malformato».
	 * ⚠ E `bytes_libera()` e' stato spostato in fondo apposta: fino a quel
	 *   momento `carico` punta dentro `g->pref`. */
	carico = g->pref.d + 2 + n;
	carico_n = g->pref.n - (2 + n);
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
	g->genere = guasto      ? G_UNI_KO
	            : canale == 0x01 ? G_UNI_INPUT
	                             : G_UNI_OK;
	registro_dice(REG_WT,
	              "stream unidirezionale %ld del client, sessione %llu, tipo "
	              "0x%04x, canale 0x%02x — %s",
	              (long)stream_id, (unsigned long long)sessione, tipo, canale,
	              guasto ? "VIOLAZIONE"
	              : canale == 0x01
	                     ? "⭐ INPUT, e da oggi si SERVE: i byte vanno a "
	                       "rcp_ricevi_input() (§7.3)"
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
	} else if (canale == 0x01) {
		/* ⭐ Il primo pezzo del canale di input arriva insieme al
		 *    preambolo che l'ha fatto riconoscere: si consegna SUBITO.
		 *    ⛔ Aspettare il pacchetto dopo perderebbe il primo
		 *    messaggio di ogni sessione — e il primo messaggio e'
		 *    proprio quello che l'utente sente come «il primo clic non
		 *    ha fatto niente». */
		rcp_passa_input(w, stream_id, carico, carico_n);
	}
	bytes_libera(&g->pref);
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
             const char *provenienza, aiutante *aiuto)
{
	wt *w = calloc(1, sizeof *w);
	if (!w)
		return NULL;
	w->conn = conn;
	w->ultimo_errore = ultimo_errore;
	w->aiuto = aiuto;
	w->ctrl_id = -1;
	w->sessione = -1;
	w->rcp_stream = -1;
	w->chiusura = -1;
	w->video_stream_ultimo = -1;
	snprintf(w->provenienza, sizeof w->provenienza, "%s",
	         provenienza ? provenienza : "");
	/* ⛔ Nell'elenco delle vive PRIMA di restituire: un fotogramma puo'
	 *    arrivare dal palco fra due giri di `poll`, e una sessione che non e'
	 *    nell'elenco non lo riceve — senza che nessuno se ne accorga. */
	w->viva_dopo = vive_prima;
	vive_prima = w;
	return w;
}

void wt_libera(wt *w)
{
	if (!w)
		return;
	/* ⛔ Fuori dall'elenco delle vive PRIMA di liberare qualunque cosa: da qui
	 *    in poi `wt_video_diffondi()` non deve piu' trovarla. */
	if (vive_prima == w) {
		vive_prima = w->viva_dopo;
	} else {
		for (wt *p = vive_prima; p; p = p->viva_dopo)
			if (p->viva_dopo == w) {
				p->viva_dopo = w->viva_dopo;
				break;
			}
	}
	/* ⛔⭐ E SI SPEGNE IL PALCO SE NESSUNO GUARDA PIU'.
	 *
	 *     Il figlio cattura e codifica solo perche' qualcuno guarda: un palco
	 *     lasciato acceso su una sessione chiusa spenderebbe una GPU e una CPU
	 *     per nessuno, per sempre.  ⚠ E non e' l'invariante I1 al contrario —
	 *     I1 vieta di calare il ritmo **per prudenza mentre qualcuno guarda**;
	 *     qui non guarda piu' nessuno, e il palco (I4) resta in piedi: si ferma
	 *     solo il ciclo dei fotogrammi. */
	if (w->video_acceso && w->rcp && gancio_palco) {
		const char *mio = rcp_utente(w->rcp);
		if (mio && mio[0] && !wt_video_qualcuno_guarda(mio, NULL)) {
			registro_dice(REG_RCP,
			              "l'ultima sessione di «%s» se ne va: il palco smette "
			              "di catturare (il figlio resta, e' l'invariante I4)",
			              mio);
			gancio_palco(gancio_palco_ctx, mio, 0, false);
		}
	}
	if (w->rcp)
		rcp_libera(w->rcp);
	if (w->h3)
		nghttp3_conn_del(w->h3);
	for (size_t i = 0; i < w->ngiudizi; i++)
		bytes_libera(&w->giudizi[i].pref);
	free(w->giudizi);
	for (size_t i = 0; i < w->ncoda; i++)
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

/* ⭐ IL VERDETTO DI PAM CHE RIENTRA — `DECISIONI.md` §1.10.
 *
 * ⛔ Il trasporto lo passa a tutte le connessioni vive e una sola lo prende:
 *    la pratica e' un numero del PROCESSO, e chi la riconosce e' `rcp.c`.  ⚠ E
 *    se non la prende nessuno va bene cosi' — vuol dire che la connessione e'
 *    morta mentre PAM rispondeva, e non c'e' piu' nessuno da ammettere. */
bool wt_verdetto(wt *w, uint64_t pratica, bool ammesso)
{
	if (!w || !w->rcp)
		return false;
	return rcp_verdetto(w->rcp, pratica, ammesso,
	                    ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);
}

void wt_batti(wt *w, ngtcp2_tstamp ts)
{
	if (w->rcp)
		rcp_tempo(w->rcp, ts / NGTCP2_MILLISECONDS);

	/* ⭐ La seconda delle due strade: `SESSIONE` puo' partire anche da
	 *    `rcp_tempo()` — il ritardo fisso di §4.4-bis la fa maturare qui, non
	 *    all'arrivo delle credenziali.  ⛔ Con la sola chiamata in `rcp_passa`
	 *    il fotogramma sarebbe partito solo per le sessioni che dicono ancora
	 *    qualcosa dopo, e su un client che tace dopo le credenziali non sarebbe
	 *    partito mai. */
	video_regola(w, ts / NGTCP2_MILLISECONDS);

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

	/* ⭐ Una passata di scrittura comincia qui, e gli stream ripartono tutti
	 *    SBLOCCATI: l'elenco vale per una passata sola.  ⚠ Sta fuori dal ciclo
	 *    apposta — azzerarlo dentro rimetterebbe in gioco lo stesso elemento a
	 *    ogni giro, che e' precisamente il ciclo che non avanza. */
	w->nbloccati = 0;
	w->troppi_bloccati = false;

	for (;;) {
		int64_t stream_id = -1;
		int fin = 0;
		nghttp3_ssize sveccnt = 0;
		nghttp3_vec wtvec[1];
		size_t wt_orig = 0;
		bool wt_mio = false;
		size_t mio_i = 0;
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
		/* ⛔ `coda_scegli()` e non «la testa»: la testa puo' appartenere a uno
		 *    stream bloccato, e fermarsi li' rifarebbe il blocco di testa che
		 *    §5.1 esiste per togliere. */
		if (sveccnt <= 0 && !w->troppi_bloccati) {
			uscita *u = coda_scegli(w, &mio_i);
			if (u) {
				stream_id = u->id;
				fin = u->fin ? 1 : 0;
				wtvec[0].base = u->dati.d + u->off;
				wtvec[0].len = u->dati.n - u->off;
				wt_mio = true;
			}
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
					uscita *u = &w->coda[mio_i];
					registro_dettaglio(
						REG_WT,
						"stream %ld bloccato: %zu byte RESTANO in "
						"coda (%zu gia' usciti) — ⭐ gli ALTRI stream "
						"continuano (§5.1)",
						(long)stream_id, u->dati.n - u->off, u->off);
					/* ⛔⭐ SI BLOCCA LO STREAM, NON LA CODA — ed e' la
					 *     cura del punto 5 della fase 3.  Fino alla fase 2
					 *     qui si alzava `coda_bloccata`, che fermava
					 *     TUTTA la coda per la passata: un fotogramma
					 *     lento bloccava in testa i successivi **a
					 *     livello applicativo**, annullando esattamente il
					 *     beneficio che §5.1 compra al livello di QUIC. */
					if (w->nbloccati < WT_BLOCCATI_MAX) {
						w->bloccati[w->nbloccati++] = stream_id;
					} else {
						/* ⚠ Il tetto si dichiara invece di scivolare:
						 *   da qui in poi la passata si ferma davvero, e
						 *   chi legge sa che non e' §5.1 a non
						 *   funzionare, e' questa tabella a essere
						 *   piena. */
						w->troppi_bloccati = true;
						registro_dice(REG_WT,
						              "⚠ %u stream bloccati nella stessa "
						              "passata: la coda si ferma qui.  Non "
						              "e' §5.1 che non vale, e' il tetto "
						              "di WT_BLOCCATI_MAX",
						              WT_BLOCCATI_MAX);
					}
					continue;
				}
				nghttp3_conn_block_stream(w->h3, stream_id);
				continue;
			case NGTCP2_ERR_STREAM_SHUT_WR:
				if (wt_mio) {
					/* Lo stream e' gia' chiuso in scrittura — di norma
					 * perche' lo abbiamo AZZERATO noi (§5.1): i byte che
					 * restavano non partono, che e' quel che si voleva. */
					coda_uccidi(w, mio_i);
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
				uscita *u = &w->coda[mio_i];
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
					coda_uccidi(w, mio_i);
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
