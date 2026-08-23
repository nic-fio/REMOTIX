/*
 * trasporto.c — vedi trasporto.h.
 */
#include "trasporto.h"

#include "registro.h"
#include "webtransport.h"

#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include <ngtcp2/ngtcp2.h>
#include <ngtcp2/ngtcp2_crypto.h>
#include <ngtcp2/ngtcp2_crypto_ossl.h>
#include <openssl/rand.h>

#define SCIDLEN 18
#define MAX_PACCHETTI_PER_GIRO 64

/* ⛔ 30 s, imposto dal server (`RCP.md` §2.2): «e' l'orologio del silenzio:
 *    scaduto, il client e' staccato».  ⚠ E' l'orologio del TRASPORTO — quello
 *    di `SPECIFICHE.md` §5.3 — non un battito applicativo, che §2.2 vieta.
 *
 * ⛔⛔⭐ E NON SCENDE A 10 s — 23 agosto 2026, e la domanda era dell'utente:
 *      *«se in 10 secondi non arrivano piu' pacchetti la connessione e'
 *      morta»*.  ⇒ La regola si fa, ma NON QUI.  Quattro ragioni, in ordine di
 *      gravita', e la prima da sola basterebbe:
 *
 *      1. ⛔ QUESTO NUMERO NON E' NOSTRO: E' NEGOZIATO.  `max_idle_timeout` e'
 *         un parametro di trasporto e RFC 9000 §10.1 dice che vale il MINIMO
 *         fra i due annunciati `[S]`.  ⇒ Mettendo 10 qui, il tempo di
 *         inattivita' scende a 10 s ANCHE PER IL CLIENT: sarebbe il browser a
 *         mollare NOI dopo 10 s di nostro silenzio.  ⚠ E il nostro silenzio
 *         esiste ed e' misurato — `[M]` 23 agosto, l'immagine ferma fino a
 *         **14,26 s** sotto `raffica-forte`: il prodotto si ucciderebbe da
 *         solo, in un caso in cui la linea magari regge ancora.
 *      2. ⛔ E' NORMATIVO: §2.2 e §5.3 dicono 30 s, e su quel numero poggia una
 *         decisione dell'utente — «chi tace e' staccato, chi arriva entra»
 *         (`DECISIONI.md` §4.4), col prezzo dichiarato «dal telefono si entra
 *         dopo trenta secondi».  A 10 s cambierebbe il PRODOTTO, non un tempo.
 *      3. ⚠ NON SAREBBE NEMMENO 10 s: ngtcp2 fa scadere a `max(idle, 3·PTO)`
 *         `[S]`, quindi il numero scritto e quello in vigore divergerebbero —
 *         la forma E1.
 *      4. ⚠ E i PING del trasporto di §4.6 escono ogni 10 s
 *         (`webtransport.c`): un tetto di 10 s e la sveglia che lo rinnova
 *         cadrebbero nello stesso istante, e chi vince e' il caso.
 *
 * ⇒ DOVE VANNO I 10 s DELL'UTENTE: in `webtransport.c`, dentro
 *   `linea_morta_giudica()`, dove la grandezza e' *«quanti pacchetti NOSTRI
 *   sono usciti senza che ne tornasse uno»* e il tempo e' solo la finestra in
 *   cui si guarda.  ⭐ Li' e' UNILATERALE — stacca noi, non insegna al client a
 *   mollare — sta dietro l'interruttore `--linea-morta` (I6), e scrive nel
 *   registro i numeri su cui ha deciso.
 *   ⚠ E l'ALTRA causa di quella cura non e' piu' la perdita di pacchetti: dal
 *     23 agosto 2026 e' lo STALLO DELL'USCITA — «da quanto tempo non esce un
 *     fotogramma pur avendone da mandare».  La frazione `pkt_lost/pkt_sent` e'
 *     stata refutata dal suo banco (su una linea che riordina misura il
 *     riordino) e resta solo come testimone nel registro; la refuta per intero
 *     e' nel riquadro sopra `WT_LM_STALLO_MS` in `webtransport.c`.
 *   Il caso A5 del piano (la scheda in
 *   secondo piano) resta servito: il browser risponde ai nostri PING dal
 *   processo di rete anche quando la pagina e' rallentata, e `[M]` l'11 agosto
 *   2026 sono stati misurati undici minuti in secondo piano con zero stacchi.
 */
#define IDLE_MS 30000

typedef struct connessione {
	struct connessione *prossima;
	struct trasporto *t;

	ngtcp2_conn *conn;
	ngtcp2_crypto_conn_ref ref;
	ngtcp2_ccerr ultimo_errore;
	ngtcp2_crypto_ossl_ctx *ossl;
	SSL *ssl;
	wt *w;

	ngtcp2_cid scid;
	struct sockaddr_storage remoto;
	socklen_t remotolen;
	struct sockaddr_storage locale;
	socklen_t localelen;

	char provenienza[80];
	bool morta;
	/* ⛔ I datagram che arrivano e che alla fase 1 si scartano: si CONTANO,
	 *    o «l'audio non arriva» e «l'audio arriva e lo butto» hanno la stessa
	 *    faccia (§6.3, rilievo B-10). */
	uint64_t datagram_visti, datagram_byte;
} connessione;

/* La mappa dei connection id.  ⚠ Una connessione ne ha piu' d'uno (il client
 * ne chiede fino a `active_connection_id_limit`), e ognuno deve portare alla
 * stessa connessione: e' la ragione per cui questa mappa non e' un campo della
 * connessione. */
typedef struct {
	ngtcp2_cid cid;
	connessione *c;
	bool usata;
} voce_cid;

struct trasporto {
	int fd;
	int famiglia;
	SSL_CTX *ctx;
	connessione *prime;
	size_t quante;

	voce_cid *cids;
	size_t ncids, capcids;

	uint8_t segreto[32];

	/* ⭐ L'aiutante di PAM (`DECISIONI.md` §1.10): non e' suo, glielo passa
	 *    `main.c`.  Serve solo per consegnarlo a ogni `wt` che nasce. */
	aiutante *aiuto;
};

/* ------------------------------------------------------------------------ */

static ngtcp2_tstamp adesso_ns(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (ngtcp2_tstamp)ts.tv_sec * NGTCP2_SECONDS + (ngtcp2_tstamp)ts.tv_nsec;
}

static void indirizzo_testo(const struct sockaddr *sa, socklen_t len, char *fuori,
                            size_t cap)
{
	char host[NI_MAXHOST], serv[NI_MAXSERV];
	if (getnameinfo(sa, len, host, sizeof host, serv, sizeof serv,
	                NI_NUMERICHOST | NI_NUMERICSERV) != 0) {
		snprintf(fuori, cap, "?");
		return;
	}
	/* ⛔⭐ LE QUADRE CI VANNO ANCHE PER IPv4, E NON E' ESTETICA.
	 *
	 *     Questa stringa diventa la PROVENIENZA di `rcp_apri()`, e da li' la
	 *     CHIAVE del ban di §4.4-bis: `rcp.c` la ricava togliendo la porta, e
	 *     `rcp_chiave_indirizzo()` — che il comando di sblocco DEVE usare —
	 *     normalizza tutto a `[indirizzo]`.  ⚠ Se qui si scrivesse
	 *     `192.168.0.2:5218`, la chiave scritta nel file dei ban sarebbe
	 *     `192.168.0.2` e quella cercata dallo sblocco `[192.168.0.2]`: il
	 *     comando risponderebbe «non era bannato» a ogni indirizzo, in
	 *     silenzio e per sempre — un comando che dice sempre la stessa cosa
	 *     non ha nessun sintomo.
	 *
	 * ⭐ E' anche la forma che `util::straddr()` dell'esempio di ngtcp2 usa
	 *    `[M]`, cioe' quella con cui i banchi della fase 1 hanno gia' scritto
	 *    file di ban.
	 *
	 * ⚠ Le precisioni non sono ornamento: `NI_MAXHOST` vale 1025, e senza di
	 *   esse il compilatore ha ragione a dire che il testo puo' non entrare. */
	snprintf(fuori, cap, "[%.60s]:%.7s", host, serv);
}

/* ------------------------------------------------------------------------ */
/* La mappa dei CID.                                                         */

static bool cid_uguali(const ngtcp2_cid *a, const ngtcp2_cid *b)
{
	return a->datalen == b->datalen && memcmp(a->data, b->data, a->datalen) == 0;
}

static connessione *cid_trova(trasporto *t, const uint8_t *dcid, size_t len)
{
	for (size_t i = 0; i < t->ncids; i++) {
		if (!t->cids[i].usata)
			continue;
		if (t->cids[i].cid.datalen == len &&
		    memcmp(t->cids[i].cid.data, dcid, len) == 0)
			return t->cids[i].c;
	}
	return NULL;
}

static void cid_lega(trasporto *t, const ngtcp2_cid *cid, connessione *c)
{
	for (size_t i = 0; i < t->ncids; i++)
		if (!t->cids[i].usata) {
			t->cids[i].cid = *cid;
			t->cids[i].c = c;
			t->cids[i].usata = true;
			return;
		}
	if (t->ncids == t->capcids) {
		size_t nc = t->capcids ? t->capcids * 2 : 32;
		voce_cid *n = realloc(t->cids, nc * sizeof *n);
		if (!n) {
			registro_dice(REG_QUIC, "⛔ memoria esaurita nella mappa dei CID");
			return;
		}
		t->cids = n;
		t->capcids = nc;
	}
	t->cids[t->ncids].cid = *cid;
	t->cids[t->ncids].c = c;
	t->cids[t->ncids].usata = true;
	t->ncids++;
}

static void cid_slega(trasporto *t, const ngtcp2_cid *cid)
{
	for (size_t i = 0; i < t->ncids; i++)
		if (t->cids[i].usata && cid_uguali(&t->cids[i].cid, cid))
			t->cids[i].usata = false;
}

static void cid_slega_tutti(trasporto *t, connessione *c)
{
	for (size_t i = 0; i < t->ncids; i++)
		if (t->cids[i].usata && t->cids[i].c == c)
			t->cids[i].usata = false;
}

/* ------------------------------------------------------------------------ */
/* I richiami di ngtcp2.                                                     */

static ngtcp2_conn *dammi_conn(ngtcp2_crypto_conn_ref *ref)
{
	connessione *c = ref->user_data;
	return c->conn;
}

static void casuale(uint8_t *dest, size_t destlen, const ngtcp2_rand_ctx *ctx)
{
	(void)ctx;
	if (RAND_bytes(dest, (int)destlen) != 1) {
		registro_dice(REG_QUIC, "⛔ RAND_bytes ha fallito");
		abort();
	}
}

static int cb_get_new_cid(ngtcp2_conn *conn, ngtcp2_cid *cid,
                          ngtcp2_stateless_reset_token *token, size_t cidlen,
                          void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	if (RAND_bytes(cid->data, (int)cidlen) != 1)
		return NGTCP2_ERR_CALLBACK_FAILURE;
	cid->datalen = cidlen;
	if (ngtcp2_crypto_generate_stateless_reset_token(
		    token->data, c->t->segreto, sizeof c->t->segreto, cid) != 0)
		return NGTCP2_ERR_CALLBACK_FAILURE;
	cid_lega(c->t, cid, c);
	return 0;
}

static int cb_remove_cid(ngtcp2_conn *conn, const ngtcp2_cid *cid,
                         void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	cid_slega(c->t, cid);
	return 0;
}

static int cb_recv_stream_data(ngtcp2_conn *conn, uint32_t flags,
                               int64_t stream_id, uint64_t offset,
                               const uint8_t *data, size_t datalen,
                               void *user_data, void *sud)
{
	connessione *c = user_data;
	(void)conn;
	(void)offset;
	(void)sud;
	return wt_ricevi_stream(c->w, flags, stream_id, data, datalen);
}

static int cb_acked(ngtcp2_conn *conn, int64_t stream_id, uint64_t offset,
                    uint64_t datalen, void *user_data, void *sud)
{
	connessione *c = user_data;
	(void)conn;
	(void)offset;
	(void)sud;
	return wt_ack_stream_data(c->w, stream_id, datalen);
}

static int cb_stream_close(ngtcp2_conn *conn, uint32_t flags, int64_t stream_id,
                           uint64_t rx_code, uint64_t tx_code, void *user_data,
                           void *sud)
{
	connessione *c = user_data;
	bool con_codice = (flags & NGTCP2_STREAM_CLOSE2_FLAG_RX_APP_ERROR_CODE_SET) ||
	                  (flags & NGTCP2_STREAM_CLOSE2_FLAG_TX_APP_ERROR_CODE_SET);
	uint64_t codice =
		(flags & NGTCP2_STREAM_CLOSE2_FLAG_RX_APP_ERROR_CODE_SET) ? rx_code
	                                                                  : tx_code;
	(void)conn;
	(void)sud;
	return wt_stream_chiuso(c->w, stream_id, codice, con_codice);
}

static int cb_stream_reset(ngtcp2_conn *conn, int64_t stream_id,
                           uint64_t final_size, uint64_t codice, void *user_data,
                           void *sud)
{
	connessione *c = user_data;
	(void)conn;
	(void)final_size;
	(void)codice;
	(void)sud;
	return wt_stream_reset(c->w, stream_id);
}

static int cb_stop_sending(ngtcp2_conn *conn, int64_t stream_id, uint64_t codice,
                           void *user_data, void *sud)
{
	connessione *c = user_data;
	(void)conn;
	(void)codice;
	(void)sud;
	return wt_stream_stop_sending(c->w, stream_id);
}

static int cb_extend_bidi(ngtcp2_conn *conn, uint64_t max_streams,
                          void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	return wt_estendi_max_streams_bidi(c->w, max_streams);
}

static int cb_extend_stream_data(ngtcp2_conn *conn, int64_t stream_id,
                                 uint64_t max_data, void *user_data, void *sud)
{
	connessione *c = user_data;
	(void)conn;
	(void)max_data;
	(void)sud;
	return wt_estendi_max_stream_data(c->w, stream_id);
}

static int cb_recv_tx_key(ngtcp2_conn *conn, ngtcp2_encryption_level level,
                          void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	if (level != NGTCP2_ENCRYPTION_LEVEL_1RTT)
		return 0;
	return wt_app_pronta(c->w);
}

static int cb_handshake_completed(ngtcp2_conn *conn, void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	registro_dettaglio(REG_QUIC, "stretta di mano TLS completata con %s",
	                   c->provenienza);
	return 0;
}

/* ⛔⭐ I DATAGRAM ARRIVANO, E FINO A STANOTTE SPARIVANO SENZA UNA RIGA —
 *     rilievo B-10, 10 agosto 2026 notte.
 *
 *     Questo server ANNUNCIA i datagram, e li annuncia due volte come §2.2
 *     impone: `max_datagram_frame_size` nei parametri di trasporto e
 *     `settings.h3_datagram = 1` in HTTP/3.  ⛔ Quindi il browser puo'
 *     mandarne **oggi** — tre byte dalla pagina bastano — e fra i
 *     `ngtcp2_callbacks` `recv_datagram` NON C'ERA: il pacchetto finiva in un
 *     richiamo non registrato e spariva, e nel registro non compariva niente.
 *
 * ⛔ §6.3 dice «un datagram piu' corto di 12 byte, o con un `tipo` diverso da
 *    `0x0401`, si scarta **scrivendolo nel registro**», e §3 chiude l'elenco
 *    delle cinque eccezioni con «e ogni tolleranza va scritta nel registro:
 *    una tolleranza silenziosa e' indistinguibile da un difetto».  La seconda
 *    eccezione dichiarata di §3 e' «si scarta», non «si scarta in silenzio»,
 *    e la differenza e' tutto il punto di quella sezione.
 *
 * ⚠ Alla fase 1 NON c'e' audio, quindi qui si scarta tutto — ma la differenza
 *   fra «l'audio non arriva» e «l'audio arriva e lo butto» il giorno in cui
 *   l'audio ci sara' si vede solo se questa riga esiste da prima.
 *
 * ⛔ E le righe sono CONTATE, non una per pacchetto: un client che manda mille
 *   datagram al secondo riempirebbe il registro, che e' un altro modo di
 *   perdere l'informazione.  Il conto totale c'e' sempre. */
static int cb_recv_datagram(ngtcp2_conn *conn, uint32_t flags,
                            const uint8_t *dati, size_t len, void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	(void)flags;
	c->datagram_visti++;
	c->datagram_byte += len;
	if (c->datagram_visti <= 3 || (c->datagram_visti % 256) == 0)
		registro_dice(REG_QUIC,
		              "⚠ TOLLERANZA (§3 eccezione 2, §6.3): datagram di %zu "
		              "byte da %s SCARTATO — alla fase 1 non c'e' audio e "
		              "nessun tipo di §6.3 e' servibile.  In tutto: %llu "
		              "datagram, %llu byte",
		              len, c->provenienza,
		              (unsigned long long)c->datagram_visti,
		              (unsigned long long)c->datagram_byte);
	return 0;
}

/* ------------------------------------------------------------------------ */
/* La spedizione.                                                            */

static void manda(trasporto *t, const struct sockaddr *sa, socklen_t salen,
                  const uint8_t *dati, size_t len)
{
	ssize_t n;
	do {
		n = sendto(t->fd, dati, len, 0, sa, salen);
	} while (n < 0 && errno == EINTR);
	if (n < 0) {
		/* ⚠ RIPIEGO DICHIARATO (`CODER.md` §4.2): se il socket e' pieno
		 *   il pacchetto si perde, e QUIC lo ritrasmette da se' — la
		 *   perdita e' la condizione che il suo recupero esiste per
		 *   trattare.  ⛔ Non e' silenzioso: la riga qui sotto e' quel
		 *   che distingue «la rete perde» da «il server butta». */
		registro_dice(REG_QUIC, "pacchetto di %zu byte NON spedito: %s", len,
		              strerror(errno));
	}
}

/* ⛔ Il richiamo che ngtcp2 invoca per ogni pacchetto, e il `user_data` che gli
 *    passa e' quello della CONNESSIONE — non quello dello strato WebTransport.
 *    ⚠ Questo giro di due righe esiste apposta: passare `wt_scrivi` direttamente
 *    a ngtcp2 compilerebbe (sono due `void *`) e farebbe leggere allo strato
 *    WebTransport i campi di `connessione`.  `[M]` 10 agosto 2026: il server
 *    apriva HTTP/3 e moriva alla prima scrittura con `ERR_CALLBACK_FAILURE`,
 *    senza che nessuna delle sue righe di registro nominasse la causa. */
static ngtcp2_ssize scrivi_pkt(ngtcp2_conn *conn, ngtcp2_path *path,
                               ngtcp2_pkt_info *pi, uint8_t *dest, size_t destlen,
                               ngtcp2_tstamp ts, void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	return wt_scrivi(c->w, path, pi, dest, destlen, ts);
}

/* Scrive tutto quel che questa connessione ha da spedire. */
static void scrivi_connessione(connessione *c)
{
	uint8_t buf[64 * 1024];
	ngtcp2_path_storage ps;
	ngtcp2_pkt_info pi;
	size_t gso = 0;
	ngtcp2_tstamp ts = adesso_ns();
	ngtcp2_ssize n;

	if (c->morta)
		return;
	if (ngtcp2_conn_in_closing_period2(c->conn) ||
	    ngtcp2_conn_in_draining_period2(c->conn))
		return;

	ngtcp2_path_storage_zero(&ps);
	memset(&pi, 0, sizeof pi);

	n = ngtcp2_conn_write_aggregate_pkt2(c->conn, &ps.path, &pi, buf, sizeof buf,
	                                     &gso, scrivi_pkt, 0, ts);
	if (n < 0) {
		registro_dice(REG_QUIC, "⛔ scrittura fallita per %s: %s",
		              c->provenienza, ngtcp2_strerror((int)n));
		c->morta = true;
		return;
	}
	ngtcp2_conn_update_pkt_tx_time(c->conn, ts);
	if (n == 0)
		return;

	/* ⚠ Niente GSO: si spedisce un pacchetto per `sendto`.  E' un ripiego
	 *   dichiarato — costa syscall, non correttezza — e la fase 1 non manda
	 *   video.  ⛔ Va rifatto prima della fase 2, dove i fotogrammi sono uno
	 *   stream ciascuno e le syscall si contano. */
	if (gso == 0)
		gso = (size_t)n;
	{
		const uint8_t *p = buf;
		size_t resto = (size_t)n;
		while (resto > 0) {
			size_t q = resto < gso ? resto : gso;
			manda(c->t, (const struct sockaddr *)&c->remoto, c->remotolen, p,
			      q);
			p += q;
			resto -= q;
		}
	}
}

/* ------------------------------------------------------------------------ */

static void connessione_libera(trasporto *t, connessione *c)
{
	cid_slega_tutti(t, c);
	if (c->w)
		wt_libera(c->w);
	if (c->conn)
		ngtcp2_conn_del(c->conn);
	if (c->ossl)
		ngtcp2_crypto_ossl_ctx_del(c->ossl);
	if (c->ssl)
		SSL_free(c->ssl);
	free(c);
}

static void raccogli_morte(trasporto *t)
{
	connessione **p = &t->prime;
	while (*p) {
		connessione *c = *p;
		if (c->morta) {
			*p = c->prossima;
			registro_dice(REG_QUIC, "connessione con %s chiusa (ne restano %zu)",
			              c->provenienza, t->quante - 1);
			connessione_libera(t, c);
			t->quante--;
			continue;
		}
		p = &c->prossima;
	}
}

/* ------------------------------------------------------------------------ */

/* ⭐⭐⭐ L'ESITO DEI DATAGRAM CHE MANDIAMO NOI — 23 agosto 2026.
 *
 *    ⛔ Fino a oggi `ngtcp2_callbacks` registrava `recv_datagram` e basta: i
 *       datagram in ARRIVO si contavano (rilievo B-10), quelli in PARTENZA —
 *       cioe' l'audio — sparivano nel filo senza lasciare traccia.  «L'audio
 *       non e' arrivato» e «e' arrivato e il cliente l'ha buttato» avevano la
 *       stessa faccia, ed e' lo stesso difetto di allora dall'altro verso.
 *
 * ⭐ E NON BASTA `lost_datagram`: `ngtcp2.h:3442` avverte che la perdita puo'
 *   essere **spuria** — dichiarata e poi riscontrata.  Registrando solo le
 *   perdite conteremmo i pacchetti FUORI SEQUENZA come persi, cioe' daremmo
 *   un numero piu' alto del vero senza dirlo.  ⇒ Si registra anche
 *   `ack_datagram`, e `webtransport.c` riconosce le perdite false: e' la
 *   MISURA DEL RIORDINO, e sul riordino ngtcp2 non da' nient'altro.
 *
 * ⚠ Non decidono niente: contano.  Il `dgram_id` e' quello che
 *   `dgram_scrivi_uno()` incrementa in `webtransport.c`.
 */
static int cb_lost_datagram(ngtcp2_conn *conn, uint64_t dgram_id,
                            void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	wt_dgram_perso(c->w, dgram_id);
	return 0;
}

static int cb_ack_datagram(ngtcp2_conn *conn, uint64_t dgram_id,
                           void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	wt_dgram_riscontrato(c->w, dgram_id);
	return 0;
}

static connessione *accetta(trasporto *t, const ngtcp2_pkt_hd *hd,
                            const struct sockaddr *locale, socklen_t localelen,
                            const struct sockaddr *remoto, socklen_t remotolen)
{
	connessione *c;
	ngtcp2_settings settings;
	ngtcp2_transport_params params;
	ngtcp2_path path;
	int rv;

	static const ngtcp2_callbacks callbacks = {
		.recv_client_initial = ngtcp2_crypto_recv_client_initial_cb,
		.recv_crypto_data = ngtcp2_crypto_recv_crypto_data_cb,
		.handshake_completed = cb_handshake_completed,
		.encrypt = ngtcp2_crypto_encrypt_cb,
		.decrypt = ngtcp2_crypto_decrypt_cb,
		.hp_mask = ngtcp2_crypto_hp_mask_cb,
		.recv_stream_data = cb_recv_stream_data,
		.acked_stream_data_offset = cb_acked,
		.rand = casuale,
		.get_new_connection_id2 = cb_get_new_cid,
		.remove_connection_id = cb_remove_cid,
		.update_key = ngtcp2_crypto_update_key_cb,
		.stream_reset = cb_stream_reset,
		.extend_max_remote_streams_bidi = cb_extend_bidi,
		.extend_max_stream_data = cb_extend_stream_data,
		.delete_crypto_aead_ctx = ngtcp2_crypto_delete_crypto_aead_ctx_cb,
		.delete_crypto_cipher_ctx = ngtcp2_crypto_delete_crypto_cipher_ctx_cb,
		.stream_stop_sending = cb_stop_sending,
		.version_negotiation = ngtcp2_crypto_version_negotiation_cb,
		.recv_tx_key = cb_recv_tx_key,
		.get_path_challenge_data2 = ngtcp2_crypto_get_path_challenge_data2_cb,
		.stream_close2 = cb_stream_close,
		/* ⛔ §6.3: i datagram si annunciano, quindi arrivano — e quel che
		 *    arriva o si serve o si scarta SCRIVENDOLO.  Rilievo B-10. */
		.recv_datagram = cb_recv_datagram,
		/* ⭐⭐ E l'esito di quelli che mandiamo NOI — in coppia, e la
		 *    ragione per cui la coppia e' obbligatoria sta sopra le due
		 *    funzioni: da sola, `lost_datagram` conterebbe il riordino
		 *    come perdita. */
		.lost_datagram = cb_lost_datagram,
		.ack_datagram = cb_ack_datagram,
	};

	c = calloc(1, sizeof *c);
	if (!c)
		return NULL;
	c->t = t;
	c->ref.get_conn = dammi_conn;
	c->ref.user_data = c;
	ngtcp2_ccerr_default(&c->ultimo_errore);

	memcpy(&c->remoto, remoto, remotolen);
	c->remotolen = remotolen;
	memcpy(&c->locale, locale, localelen);
	c->localelen = localelen;
	indirizzo_testo(remoto, remotolen, c->provenienza, sizeof c->provenienza);

	c->scid.datalen = SCIDLEN;
	if (RAND_bytes(c->scid.data, SCIDLEN) != 1)
		goto male;

	ngtcp2_settings_default(&settings);
	settings.initial_ts = adesso_ns();
	settings.log_printf = NULL;

	ngtcp2_transport_params_default(&params);
	params.initial_max_stream_data_bidi_local = 256 * 1024;
	params.initial_max_stream_data_bidi_remote = 256 * 1024;
	params.initial_max_stream_data_uni = 256 * 1024;
	params.initial_max_data = 1024 * 1024;
	params.initial_max_streams_bidi = 100;
	/* ⛔ `RCP.md` §2.3: «il server DEVE concedere credito al client per i
	 *    suoi stream unidirezionali: almeno 16 disponibili in ogni momento».
	 *    ⚠ Il client apre uno stream di input e uno per ogni trasferimento di
	 *    appunti: se il credito finisse, l'input non partirebbe affatto e il
	 *    sintomo sarebbe «il desktop non risponde», non «credito esaurito» —
	 *    cioe' una diagnosi che punta sulla fase 4 mentre il difetto e' qui.
	 *    ⭐ E i 3 dell'esempio di ngtcp2 bastano ad aprire la sessione: la
	 *       sessione si apre benissimo con 3, ed e' per questo che nessun
	 *       banco funzionale della fase 1 lo vedrebbe.
	 *
	 * ⛔⭐ E 16 NON BASTAVANO — rilievo B-12, 10 agosto 2026 notte.  §2.3 chiede
	 *     «almeno 16 **disponibili in ogni momento**», e questo numero e' un
	 *     TOTALE.  Appena HTTP/3 si apre, il browser apre TRE stream
	 *     unidirezionali suoi — il canale di controllo di HTTP/3 e i due di
	 *     QPACK — e restano aperti per tutta la connessione: al client ne
	 *     restavano **13 dal primo secondo**.  ⚠ Lo da' per scontato il nostro
	 *     stesso codice, che in `webtransport.c` controlla il credito speculare
	 *     con `< 3` prima di aprire i tre nostri.
	 *
	 *     ⭐ Da cui 19 = 16 + 3: il numero di §2.3 resta 16, e i tre di HTTP/3
	 *        si dichiarano invece di essere sottratti in silenzio.
	 *
	 * `[?]` ⚠ E RESTA UNA DOMANDA APERTA, che si chiude con una misura e non
	 *   con una riga: `ngtcp2` non alza da se' il tetto degli stream, «tranne
	 *   quando uno stream si chiude senza che `stream_open` sia stato
	 *   chiamato».  Questo codice `stream_open` non lo registra, quindi cade
	 *   probabilmente in quell'eccezione e il rinnovo e' automatico — ma
	 *   nessuna riga del prodotto lo dichiara e nessuno l'ha misurato.  Se
	 *   l'eccezione non si applicasse, il ventesimo stream unidirezionale del
	 *   client non si aprirebbe piu' e il sintomo sarebbe «il desktop non
	 *   risponde».  ⛔ Si misura alla fase 4, quando gli appunti apriranno uno
	 *   stream per trasferimento: prima di allora nessun client ne apre piu'
	 *   di quattro, e una misura senza il carico che la provoca non e' una
	 *   misura. */
	params.initial_max_streams_uni = 19;
	/* ⛔ §2.2: 30 s, imposto dal server. */
	params.max_idle_timeout = IDLE_MS * NGTCP2_MILLISECONDS;
	/* ⛔ §2.2: i datagram DEVONO essere abilitati sulla connessione HTTP/3
	 *    (e' l'audio).  ⚠ E senza QUESTO parametro di trasporto, annunciare
	 *    SETTINGS_H3_DATAGRAM=1 e' un errore di protocollo. */
	params.max_datagram_frame_size = 65536;
	params.stateless_reset_token_present = 1;
	params.active_connection_id_limit = 7;
	params.grease_quic_bit = 1;
	params.original_dcid = hd->dcid;
	params.original_dcid_present = 1;
	/* ⛔ §2.3: il server NON DEVE disabilitare la migrazione — e' la ragione
	 *    per cui QUIC e' stato scelto (`SPECIFICHE.md` §8.4): il telefono che
	 *    passa da WiFi a rete mobile.  Non si tocca
	 *    `disable_active_migration`, e questa riga esiste perche' un
	 *    revisore possa leggere che non e' una dimenticanza. */

	if (ngtcp2_crypto_generate_stateless_reset_token(
		    params.stateless_reset_token, t->segreto, sizeof t->segreto,
		    &c->scid) != 0)
		goto male;

	memset(&path, 0, sizeof path);
	path.local.addr = (ngtcp2_sockaddr *)&c->locale;
	path.local.addrlen = c->localelen;
	path.remote.addr = (ngtcp2_sockaddr *)&c->remoto;
	path.remote.addrlen = c->remotolen;

	rv = ngtcp2_conn_server_new(&c->conn, &hd->scid, &c->scid, &path,
	                            hd->version, &callbacks, &settings, &params,
	                            NULL, c);
	if (rv != 0) {
		registro_dice(REG_QUIC, "⛔ ngtcp2_conn_server_new: %s",
		              ngtcp2_strerror(rv));
		goto male;
	}

	if (ngtcp2_crypto_ossl_ctx_new(&c->ossl, NULL) != 0)
		goto male;
	c->ssl = SSL_new(t->ctx);
	if (!c->ssl)
		goto male;
	ngtcp2_crypto_ossl_ctx_set_ssl(c->ossl, c->ssl);
	if (ngtcp2_crypto_ossl_configure_server_session(c->ssl) != 0) {
		registro_dice(REG_QUIC,
		              "⛔ ngtcp2_crypto_ossl_configure_server_session");
		goto male;
	}
	SSL_set_app_data(c->ssl, &c->ref);
	SSL_set_accept_state(c->ssl);
	/* ⛔ E QUI NON SI ACCENDE 0-RTT (§2.3).  L'esempio di ngtcp2 chiama
	 *    `SSL_set_quic_tls_early_data_enabled(ssl, 1)` proprio in questo
	 *    punto: l'assenza di quella riga E' la decisione, e senza questo
	 *    commento somiglierebbe a una dimenticanza.  Lo spegnimento vero sta
	 *    in `tls.c`, a livello di contesto, dove nessuna sessione lo puo'
	 *    riaccendere per distrazione. */
	ngtcp2_conn_set_tls_native_handle(c->conn, c->ossl);

	c->w = wt_nuovo(c->conn, &c->ultimo_errore, c->provenienza, t->aiuto);
	if (!c->w)
		goto male;

	c->prossima = t->prime;
	t->prime = c;
	t->quante++;
	cid_lega(t, &c->scid, c);

	registro_dice(REG_QUIC, "connessione nuova da %s (in tutto %zu)",
	              c->provenienza, t->quante);
	return c;

male:
	connessione_libera(t, c);
	return NULL;
}

/* ------------------------------------------------------------------------ */

static void nego_versione(trasporto *t, const ngtcp2_version_cid *vc,
                          const struct sockaddr *remoto, socklen_t remotolen)
{
	uint8_t buf[NGTCP2_MAX_UDP_PAYLOAD_SIZE];
	uint32_t versioni[1] = {NGTCP2_PROTO_VER_V1};
	uint8_t casuale_byte;
	ngtcp2_ssize n;

	if (RAND_bytes(&casuale_byte, 1) != 1)
		return;
	n = ngtcp2_pkt_write_version_negotiation(
		buf, sizeof buf, casuale_byte, vc->scid, vc->scidlen, vc->dcid,
		vc->dcidlen, versioni, 1);
	if (n < 0)
		return;
	registro_dice(REG_QUIC, "versione QUIC non nostra: negoziazione verso %s",
	              "il client");
	manda(t, remoto, remotolen, buf, (size_t)n);
}

static void leggi_pacchetto(trasporto *t, const struct sockaddr *locale,
                            socklen_t localelen, const struct sockaddr *remoto,
                            socklen_t remotolen, const ngtcp2_pkt_info *pi,
                            const uint8_t *dati, size_t len)
{
	ngtcp2_version_cid vc;
	connessione *c;
	ngtcp2_path path;
	int rv;

	rv = ngtcp2_pkt_decode_version_cid(&vc, dati, len, SCIDLEN);
	if (rv == NGTCP2_ERR_VERSION_NEGOTIATION) {
		nego_versione(t, &vc, remoto, remotolen);
		return;
	}
	if (rv != 0) {
		registro_dettaglio(REG_QUIC, "intestazione illeggibile: %s",
		                   ngtcp2_strerror(rv));
		return;
	}

	c = cid_trova(t, vc.dcid, vc.dcidlen);
	if (!c) {
		ngtcp2_pkt_hd hd;
		if (ngtcp2_accept(&hd, dati, len) != 0) {
			/* ⚠ Nessuna connessione e non e' un Initial.  ⛔ RIPIEGO
			 *   DICHIARATO: qui il prodotto dovrebbe mandare uno
			 *   Stateless Reset, che e' il modo di dire a un client con
			 *   uno stato vecchio «quella connessione non c'e' piu'»
			 *   invece di farlo aspettare i 30 s dell'inattivita'.
			 *   Non c'e': si ignora, e la riga qui sotto e' quel che
			 *   distingue «ignorato» da «non e' mai arrivato». */
			registro_dettaglio(REG_QUIC,
			                   "pacchetto di %zu byte per una connessione "
			                   "che non c'e': ignorato",
			                   len);
			return;
		}
		/* ⚠ Nessuna validazione dell'indirizzo con Retry: il prodotto si
		 *   usa su rete propria o VPN (`SPECIFICHE.md` §4.1).  ⛔ Va
		 *   rimessa prima di esporlo, ed e' dichiarata qui perche' non
		 *   sembri una dimenticanza. */
		c = accetta(t, &hd, locale, localelen, remoto, remotolen);
		if (!c)
			return;
	}

	if (ngtcp2_conn_in_draining_period2(c->conn))
		return;

	memset(&path, 0, sizeof path);
	path.local.addr = (ngtcp2_sockaddr *)&c->locale;
	path.local.addrlen = c->localelen;
	path.remote.addr = (ngtcp2_sockaddr *)&c->remoto;
	path.remote.addrlen = c->remotolen;

	{
		ngtcp2_tstamp ora = adesso_ns();
		rv = ngtcp2_conn_read_pkt(c->conn, &path, pi, dati, len, ora);
		/* ⛔⭐ §5.3 — E QUI, E SOLO SE `rv == 0`: il pacchetto e' stato
		 *     DECIFRATO E AUTENTICATO.  ⚠ Un datagram che arriva non basta —
		 *     chiunque ne puo' spedire uno con l'indirizzo di un altro, e
		 *     terrebbe occupato il posto di quell'altro.
		 *
		 * ⭐ E' il segno di vita che mancava: fino al 16 agosto 2026 §5.3
		 *    guardava l'ultimo byte di RCP, cioe' l'ultima volta che l'UTENTE
		 *    aveva toccato qualcosa, e trenta secondi passati a leggere una
		 *    pagina bastavano a far dichiarare sparito un client vivo.  ⛔ Il
		 *    prezzo, misurato: un secondo dispositivo entrava e prendeva il
		 *    desktop del primo. */
		if (rv == 0 && c->w)
			wt_segno_di_vita(c->w, ora);
	}
	if (rv != 0) {
		if (rv == NGTCP2_ERR_DRAINING || rv == NGTCP2_ERR_IDLE_CLOSE ||
		    rv == NGTCP2_ERR_CLOSING) {
			c->morta = true;
			return;
		}
		registro_dice(REG_QUIC, "lettura fallita da %s: %s", c->provenienza,
		              ngtcp2_strerror(rv));
		/* ⚠ RIPIEGO DICHIARATO: qui il prodotto dovrebbe entrare nel
		 *   periodo di chiusura e ritrasmettere il CONNECTION_CLOSE per
		 *   tre RTT.  Si manda una volta sola e si chiude.  ⛔ Non tocca
		 *   RCP: §3.1 chiude la SESSIONE WebTransport, non la connessione
		 *   QUIC, e quella strada e' intera. */
		{
			uint8_t buf[NGTCP2_MAX_UDP_PAYLOAD_SIZE];
			ngtcp2_pkt_info opi;
			ngtcp2_path_storage ps;
			ngtcp2_ssize n;
			ngtcp2_path_storage_zero(&ps);
			memset(&opi, 0, sizeof opi);
			if (rv != NGTCP2_ERR_CRYPTO)
				ngtcp2_ccerr_set_liberr(&c->ultimo_errore, rv, NULL, 0);
			n = ngtcp2_conn_write_connection_close(
				c->conn, &ps.path, &opi, buf, sizeof buf, &c->ultimo_errore,
				adesso_ns());
			if (n > 0)
				manda(t, (const struct sockaddr *)&c->remoto, c->remotolen,
				      buf, (size_t)n);
		}
		c->morta = true;
		return;
	}
}

/* ------------------------------------------------------------------------ */

void trasporto_leggi(trasporto *t)
{
	uint8_t buf[64 * 1024];
	uint8_t ctrl[256];
	struct sockaddr_storage da;
	struct iovec iov;
	struct msghdr msg;
	ngtcp2_pkt_info pi;
	int giri = 0;

	for (; giri < MAX_PACCHETTI_PER_GIRO; giri++) {
		struct sockaddr_storage locale;
		socklen_t localelen = 0;
		ssize_t n;

		iov.iov_base = buf;
		iov.iov_len = sizeof buf;
		memset(&msg, 0, sizeof msg);
		msg.msg_name = &da;
		msg.msg_namelen = sizeof da;
		msg.msg_iov = &iov;
		msg.msg_iovlen = 1;
		msg.msg_control = ctrl;
		msg.msg_controllen = sizeof ctrl;

		n = recvmsg(t->fd, &msg, 0);
		if (n < 0) {
			if (errno == EINTR)
				continue;
			if (errno != EAGAIN && errno != EWOULDBLOCK)
				registro_dice(REG_QUIC, "recvmsg: %s", strerror(errno));
			break;
		}
		/* Un pacchetto QUIC valido non e' mai piu' corto di 21 byte. */
		if (n < 21)
			continue;

		/* L'indirizzo LOCALE si legge dal messaggio ausiliario: senza,
		 * un server legato a `0.0.0.0` darebbe a ngtcp2 un percorso con
		 * un capo sbagliato, e la validazione del percorso fallirebbe
		 * appena il client cambia rete. */
		memset(&locale, 0, sizeof locale);
		for (struct cmsghdr *cm = CMSG_FIRSTHDR(&msg); cm;
		     cm = CMSG_NXTHDR(&msg, cm)) {
			if (cm->cmsg_level == IPPROTO_IP &&
			    cm->cmsg_type == IP_PKTINFO) {
				struct in_pktinfo pk;
				struct sockaddr_in *s4 = (struct sockaddr_in *)&locale;
				memcpy(&pk, CMSG_DATA(cm), sizeof pk);
				s4->sin_family = AF_INET;
				s4->sin_addr = pk.ipi_addr;
				localelen = sizeof *s4;
			} else if (cm->cmsg_level == IPPROTO_IPV6 &&
			           cm->cmsg_type == IPV6_PKTINFO) {
				struct in6_pktinfo pk;
				struct sockaddr_in6 *s6 = (struct sockaddr_in6 *)&locale;
				memcpy(&pk, CMSG_DATA(cm), sizeof pk);
				s6->sin6_family = AF_INET6;
				s6->sin6_addr = pk.ipi6_addr;
				localelen = sizeof *s6;
			}
		}
		if (localelen == 0) {
			/* ⛔ «Vuoto» e «proibito» hanno lo stesso aspetto
			 *    (`LEZIONI.md` §1.9): se il nucleo non ha messo il
			 *    messaggio ausiliario, lo si DICE invece di far finta
			 *    che l'indirizzo locale sia zero. */
			socklen_t l = sizeof locale;
			if (getsockname(t->fd, (struct sockaddr *)&locale, &l) == 0) {
				localelen = l;
				registro_dettaglio(REG_QUIC,
				                   "niente IP_PKTINFO: uso l'indirizzo "
				                   "del socket");
			} else {
				registro_dice(REG_QUIC,
				              "⛔ nessun indirizzo locale per un "
				              "pacchetto di %zd byte: scartato",
				              n);
				continue;
			}
		}
		/* La porta non viaggia nel `pktinfo`: e' quella del socket. */
		{
			struct sockaddr_storage mia;
			socklen_t l = sizeof mia;
			if (getsockname(t->fd, (struct sockaddr *)&mia, &l) == 0) {
				if (locale.ss_family == AF_INET)
					((struct sockaddr_in *)&locale)->sin_port =
						((struct sockaddr_in *)&mia)->sin_port;
				else if (locale.ss_family == AF_INET6)
					((struct sockaddr_in6 *)&locale)->sin6_port =
						((struct sockaddr_in6 *)&mia)->sin6_port;
			}
		}

		memset(&pi, 0, sizeof pi);
		leggi_pacchetto(t, (const struct sockaddr *)&locale, localelen,
		                (const struct sockaddr *)&da, msg.msg_namelen, &pi,
		                buf, (size_t)n);
	}

	trasporto_scrivi(t);
}

void trasporto_scrivi(trasporto *t)
{
	for (connessione *c = t->prime; c; c = c->prossima)
		scrivi_connessione(c);
	raccogli_morte(t);
}

int trasporto_attesa_ms(const trasporto *t)
{
	ngtcp2_tstamp prima = UINT64_MAX;
	ngtcp2_tstamp ora = adesso_ns();

	for (connessione *c = t->prime; c; c = c->prossima) {
		ngtcp2_tstamp e;
		if (c->morta)
			return 0;
		e = ngtcp2_conn_get_expiry2(c->conn);
		if (e < prima)
			prima = e;
		e = wt_battito_ns(c->w);
		if (e < prima)
			prima = e;
	}
	if (prima == UINT64_MAX)
		return -1;
	if (prima <= ora)
		return 0;
	{
		uint64_t d = (prima - ora) / NGTCP2_MILLISECONDS;
		if (d > 1000)
			d = 1000;
		return (int)d;
	}
}

/* ⭐ IL VERDETTO DI PAM CHE RIENTRA — `DECISIONI.md` §1.10.
 *
 * ⛔ Si passa a tutte le connessioni vive e UNA sola lo prende: la pratica e'
 *    un numero del processo, e chi sa a chi appartiene e' `rcp.c`.  ⚠ Un giro
 *    su al massimo sedici connessioni costa meno di una tabella da tenere
 *    allineata — e una tabella di puntatori a connessioni che possono morire
 *    mentre PAM risponde e' precisamente il posto in cui nasce un puntatore
 *    penzolante.
 *
 * ⭐ E se non lo prende nessuno si SCRIVE: «la connessione e' morta mentre PAM
 *    rispondeva» e «il verdetto e' andato a finire da nessuna parte per un
 *    difetto nostro» hanno lo stesso aspetto, e senza questa riga sarebbero
 *    indistinguibili. */
void trasporto_verdetto(trasporto *t, uint64_t pratica, bool ammesso)
{
	for (connessione *c = t->prime; c; c = c->prossima) {
		if (c->morta || !c->w)
			continue;
		if (wt_verdetto(c->w, pratica, ammesso)) {
			/* ⛔ E si riscrive SUBITO: il verdetto puo' aver reso maturo
			 *    l'`AMMESSO`/`RESPINTO`, e aspettare il prossimo battito
			 *    aggiungerebbe fino a 100 ms a chi si autentica — cioe'
			 *    peggiorerebbe il numero che questa cura non deve toccare. */
			if (wt_battito_ns(c->w) != UINT64_MAX)
				wt_batti(c->w, adesso_ns());
			trasporto_scrivi(t);
			return;
		}
	}
	registro_dice(REG_RCP,
	              "⚠ il verdetto della pratica %llu (%s) non l'ha preso "
	              "nessuno: la connessione che l'aspettava non c'e' piu'",
	              (unsigned long long)pratica, ammesso ? "ammesso" : "respinto");
}

void trasporto_scaduti(trasporto *t)
{
	ngtcp2_tstamp ora = adesso_ns();

	for (connessione *c = t->prime; c; c = c->prossima) {
		if (c->morta)
			continue;
		/* ⭐ Il NOSTRO orologio, prima di quello di QUIC: e' quello che fa
		 *    scadere i tetti di `RCP.md` §4.6 e maturare la capsula di
		 *    chiusura.  Nell'innesto lo faceva il keep-alive, cioe' byte
		 *    sul filo; qui non esce niente. */
		if (wt_battito_ns(c->w) <= ora)
			wt_batti(c->w, ora);

		/* ⛔⭐⭐ FASE 9 — LA LINEA MORTA, e la fa cadere QUI perche' la
		 *      connessione QUIC e' di questo file: `webtransport.c` ha i
		 *      contatori e prende la decisione (con la sua riga di registro),
		 *      questo pezzo la esegue.
		 *
		 * ⛔ Si manda UN `CONNECTION_CLOSE` e si chiude — lo stesso ripiego
		 *    dichiarato della lettura fallita, cento righe piu' su: il prodotto
		 *    dovrebbe entrare nel periodo di chiusura e ritrasmetterlo per tre
		 *    RTT.  ⚠ Qui costa meno che altrove: per ipotesi la linea non
		 *    porta, e quel pacchetto e' un tentativo, non una promessa.  Se non
		 *    arriva, il client se ne accorge col SUO tempo di inattivita'.
		 *
		 * ⚠ E il motivo NON e' un codice RCP: `webtransport.c` ha gia' scritto
		 *   `H3_NO_ERROR` con la ragione in chiaro dentro `c->ultimo_errore`,
		 *   e §9 vieta di inventare un motivo nuovo di §8.2 dentro RCP/1. */
		if (c->w && wt_linea_morta_scattata(c->w)) {
			uint8_t buf[NGTCP2_MAX_UDP_PAYLOAD_SIZE];
			ngtcp2_pkt_info opi;
			ngtcp2_path_storage ps;
			ngtcp2_ssize n;
			ngtcp2_path_storage_zero(&ps);
			memset(&opi, 0, sizeof opi);
			n = ngtcp2_conn_write_connection_close(
				c->conn, &ps.path, &opi, buf, sizeof buf, &c->ultimo_errore,
				ora);
			if (n > 0)
				manda(t, (const struct sockaddr *)&c->remoto, c->remotolen, buf,
				      (size_t)n);
			registro_dice(REG_QUIC,
			              "⛔ %s: LINEA MORTA — la connessione QUIC si chiude "
			              "(un solo CONNECTION_CLOSE, %s).  Il perche', coi "
			              "numeri, e' nella riga `linea-morta` qui sopra",
			              c->provenienza,
			              n > 0 ? "spedito" : "⚠ nemmeno spedito");
			c->morta = true;
			continue;
		}

		if (ngtcp2_conn_get_expiry2(c->conn) <= ora) {
			int rv = ngtcp2_conn_handle_expiry(c->conn, ora);
			if (rv != 0) {
				if (rv == NGTCP2_ERR_IDLE_CLOSE)
					registro_dice(REG_QUIC,
					              "%s: trenta secondi di silenzio, "
					              "staccato (§2.2)",
					              c->provenienza);
				else
					registro_dice(REG_QUIC, "%s: timer scaduto: %s",
					              c->provenienza, ngtcp2_strerror(rv));
				c->morta = true;
			}
		}
	}
	trasporto_scrivi(t);
}

/* ⛔⭐ §8.1 — «MAI CON UN SILENZIO»: IL SERVER CHE SI SPEGNE LO DICE.
 *     Rilievo B-7, 10 agosto 2026 notte.
 *
 *     Prima di stanotte `systemctl stop` (o Ctrl-C) con una sessione attiva
 *     faceva questo: il ciclo usciva, si scriveva «chiusura richiesta: 1
 *     connessioni QUIC vive», e `trasporto_chiudi()` liberava tutto.  ⛔ Nessun
 *     `CONGEDO(0x0C)`, nessuna capsula di chiusura con `0x0C`, e nemmeno un
 *     `CONNECTION_CLOSE` di QUIC: il client restava ad aspettare i 30 secondi
 *     dell'inattivita' e mostrava «errore di rete».
 *
 *     ⚠ Il motivo `0x0C SERVER_IN_CHIUSURA` esiste in §8.2 apposta, ed era
 *       definito in `rcp.h` senza che nessuna riga del prodotto lo emettesse.
 *
 * ⭐ Restituisce quante connessioni hanno ancora qualcosa da far uscire: chi
 *    spegne fa girare il ciclo finche' non e' zero, invece di contare i giri —
 *    «consegnato a ngtcp2» non e' «uscito sul filo». */
size_t trasporto_congeda_tutte(trasporto *t, uint8_t motivo, const char *perche)
{
	size_t restano = 0;
	for (connessione *c = t->prime; c; c = c->prossima) {
		if (c->morta || !c->w)
			continue;
		wt_congeda(c->w, motivo, perche);
	}
	trasporto_scrivi(t);
	for (connessione *c = t->prime; c; c = c->prossima)
		if (!c->morta && c->w && wt_ha_da_dire(c->w))
			restano++;
	return restano;
}

/* ⛔ Che cosa trattiene chi non ha ancora finito — per il registro dello
 *    spegnimento.  Torna la prima ragione trovata, che basta a mandare la
 *    diagnosi dalla parte giusta. */
const char *trasporto_perche_restano(const trasporto *t)
{
	for (connessione *c = t->prime; c; c = c->prossima)
		if (!c->morta && c->w && wt_ha_da_dire(c->w))
			return wt_perche_ha_da_dire(c->w);
	return "niente";
}

size_t trasporto_quante(const trasporto *t) { return t->quante; }
int trasporto_fd(const trasporto *t) { return t->fd; }
void trasporto_contesto(trasporto *t, SSL_CTX *ctx) { t->ctx = ctx; }

/* ------------------------------------------------------------------------ */

trasporto *trasporto_apri(const char *indirizzo, const char *porta, SSL_CTX *ctx,
                          aiutante *aiuto)
{
	struct addrinfo suggerimenti, *ris = NULL, *r;
	trasporto *t;
	int fd = -1, uno = 1;

	memset(&suggerimenti, 0, sizeof suggerimenti);
	suggerimenti.ai_family = AF_UNSPEC;
	suggerimenti.ai_socktype = SOCK_DGRAM;
	suggerimenti.ai_flags = AI_PASSIVE;

	if (getaddrinfo(indirizzo, porta, &suggerimenti, &ris) != 0) {
		registro_dice(REG_QUIC, "⛔ %s:%s non si risolve", indirizzo, porta);
		return NULL;
	}
	for (r = ris; r; r = r->ai_next) {
		fd = socket(r->ai_family, r->ai_socktype | SOCK_NONBLOCK, r->ai_protocol);
		if (fd < 0)
			continue;
		/* ⛔⭐ QUI NON SI METTE `SO_REUSEADDR`, E NON E' UNA DIMENTICANZA.
		 *
		 *     `[M]` 10 agosto 2026, prima accensione: con `SO_REUSEADDR`
		 *     il socket UDP si e' legato alla 7447 **mentre un altro
		 *     server la teneva gia'** — su Linux due socket UDP unicast
		 *     con quell'opzione condividono la porta, e i pacchetti li
		 *     prende uno solo dei due.  ⛔ Il sintomo sarebbe «il server
		 *     e' acceso e la pagina non si collega», con due processi
		 *     entrambi convinti di ascoltare: nessuno dei due errori che
		 *     ne uscirebbero nominerebbe la porta.
		 *
		 * ⚠ Sul TCP invece resta, e li' serve davvero: senza, un riavvio
		 *   trova la porta occupata dal socket in TIME_WAIT.  ⭐ E la
		 *   differenza fra i due casi e' che sul TCP il nucleo RIFIUTA
		 *   comunque un secondo ascoltatore, mentre sull'UDP lo accetta —
		 *   cioe' e' l'unico dei due in cui l'opzione compra un guasto
		 *   silenzioso invece di una comodita'. */
		if (r->ai_family == AF_INET6) {
			setsockopt(fd, IPPROTO_IPV6, IPV6_RECVPKTINFO, &uno, sizeof uno);
		} else {
			setsockopt(fd, IPPROTO_IP, IP_PKTINFO, &uno, sizeof uno);
		}
		if (bind(fd, r->ai_addr, r->ai_addrlen) == 0)
			break;
		close(fd);
		fd = -1;
	}
	if (fd < 0) {
		registro_dice(REG_QUIC, "⛔ non mi lego a %s:%s in UDP: %s", indirizzo,
		              porta, strerror(errno));
		freeaddrinfo(ris);
		return NULL;
	}

	t = calloc(1, sizeof *t);
	if (!t) {
		close(fd);
		freeaddrinfo(ris);
		return NULL;
	}
	t->fd = fd;
	t->famiglia = r->ai_family;
	t->ctx = ctx;
	t->aiuto = aiuto;
	freeaddrinfo(ris);

	if (RAND_bytes(t->segreto, sizeof t->segreto) != 1) {
		registro_dice(REG_QUIC, "⛔ non genero il segreto statico");
		trasporto_chiudi(t);
		return NULL;
	}

	if (ngtcp2_crypto_ossl_init() != 0) {
		registro_dice(REG_QUIC, "⛔ ngtcp2_crypto_ossl_init");
		trasporto_chiudi(t);
		return NULL;
	}

	registro_dice(REG_QUIC,
	              "ascolto UDP su %s:%s — max_idle_timeout=%d ms, datagram "
	              "abilitati e scartati con una riga (§6.3), %d stream "
	              "unidirezionali concessi = 16 di §2.3 + i 3 di HTTP/3",
	              indirizzo, porta, IDLE_MS, 19);
	return t;
}

void trasporto_chiudi(trasporto *t)
{
	connessione *c;
	if (!t)
		return;
	c = t->prime;
	while (c) {
		connessione *p = c->prossima;
		connessione_libera(t, c);
		c = p;
	}
	free(t->cids);
	if (t->fd >= 0)
		close(t->fd);
	free(t);
}
