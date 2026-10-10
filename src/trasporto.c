/*
 * trasporto.c — see trasporto.h.
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

/* ⛔ 30 s, imposed by the server (`RCP.md` §2.2): «it is the silence clock:
 *    when it expires, the client is disconnected».  ⚠ It is the TRANSPORT
 *    clock — the one of `SPECIFICHE.md` §5.3 — not an application heartbeat,
 *    which §2.2 forbids.
 *
 * ⛔⛔⭐ AND IT DOES NOT GO DOWN TO 10 s — 23 Aug 2026, and the question was the
 *      user's: *«if no more packets arrive in 10 seconds the connection is
 *      dead»*.  ⇒ The rule is implemented, but NOT HERE.  Four reasons, in
 *      order of severity, and the first alone would be enough:
 *
 *      1. ⛔ THIS NUMBER IS NOT OURS: IT IS NEGOTIATED.  `max_idle_timeout` is
 *         a transport parameter and RFC 9000 §10.1 says the MINIMUM of the two
 *         announced applies `[S]`.  ⇒ Putting 10 here, the idle time goes down
 *         to 10 s FOR THE CLIENT TOO: it would be the browser dropping US
 *         after 10 s of our silence.  ⚠ And our silence exists and is measured
 *         — `[M]` 23 August, the picture frozen up to **14.26 s** under
 *         `raffica-forte`: the product would kill itself, in a case where the
 *         line may well still hold.
 *      2. ⛔ IT IS NORMATIVE: §2.2 and §5.3 say 30 s, and a decision of the
 *         user rests on that number — «whoever is silent is disconnected,
 *         whoever arrives gets in» (`DECISIONI.md` §4.4), with the declared
 *         price «from the phone you get in after thirty seconds».  At 10 s the
 *         PRODUCT would change, not a timeout.
 *      3. ⚠ IT WOULD NOT EVEN BE 10 s: ngtcp2 expires at `max(idle, 3·PTO)`
 *         `[S]`, so the written number and the one in force would diverge —
 *         form E1.
 *      4. ⚠ And the transport PINGs of §4.6 go out every 10 s
 *         (`webtransport.c`): a 10 s ceiling and the alarm that renews it
 *         would fall at the same instant, and chance would decide who wins.
 *
 * ⇒ WHERE THE USER'S 10 s GO: in `webtransport.c`, inside
 *   `linea_morta_giudica()`, where the quantity is *«how many of OUR packets
 *   went out without one coming back»* and time is only the window in which
 *   one looks.  ⭐ There it is UNILATERAL — it disconnects us, it does not
 *   teach the client to drop — ⭐ since 24 Aug 2026 it is ON by default (the
 *   user's decision; it is turned off with `--niente-linea-morta`), and it
 *   writes in the log the numbers on which it decided.
 *   ⚠ And the OTHER cause of that cure is no longer packet loss: since 23 Aug
 *     2026 it is the OUTPUT STALL — «how long since a frame went out while
 *     having some to send».  The fraction `pkt_lost/pkt_sent` was refuted by
 *     its bench (on a line that reorders it measures the reordering) and stays
 *     only as a witness in the log; the full refutation is in the box above
 *     `WT_LM_STALLO_MS` in `webtransport.c`.
 *   Case A5 of the plan (the tab in the background) stays served: the browser
 *   answers our PINGs from the network process even when the page is
 *   throttled, and `[M]` on 11 Aug 2026 eleven minutes in the background were
 *   measured with zero disconnections.
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
	/* ⛔ The datagrams that arrive and that in phase 1 are discarded: they are
	 *    COUNTED, or «the audio does not arrive» and «the audio arrives and I
	 *    throw it away» look the same (§6.3, finding B-10). */
	uint64_t datagram_visti, datagram_byte;
} connessione;

/* The map of connection ids.  ⚠ A connection has more than one (the client
 * asks for up to `active_connection_id_limit`), and each must lead to the same
 * connection: this is the reason this map is not a field of the connection. */
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

	/* ⭐ The PAM helper (`DECISIONI.md` §1.10): it is not this module's, it is
	 *    passed in by `main.c`.  It only serves to hand it to every `wt` that
	 *    is born. */
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
	/* ⛔⭐ THE BRACKETS GO ON FOR IPv4 TOO, AND IT IS NOT AESTHETICS.
	 *
	 *     This string becomes the PROVENANCE of `rcp_apri()`, and from there
	 *     the KEY of the ban of §4.4-bis: `rcp.c` derives it by removing the
	 *     port, and `rcp_chiave_indirizzo()` — which the unblock command MUST
	 *     use — normalises everything to `[address]`.  ⚠ If `192.168.0.2:5218`
	 *     were written here, the key written in the ban file would be
	 *     `192.168.0.2` and the one looked up by the unblock `[192.168.0.2]`:
	 *     the command would answer «was not banned» to every address,
	 *     silently and forever — a command that always says the same thing has
	 *     no symptom.
	 *
	 * ⭐ It is also the form that `util::straddr()` of the ngtcp2 example uses
	 *    `[M]`, that is the one with which the phase 1 benches already wrote
	 *    ban files.
	 *
	 * ⚠ The precisions are not ornament: `NI_MAXHOST` is 1025, and without
	 *   them the compiler is right to say the text may not fit. */
	snprintf(fuori, cap, "[%.60s]:%.7s", host, serv);
}

/* ------------------------------------------------------------------------ */
/* The CID map.                                                              */

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
			registro_dice(REG_QUIC, "⛔ out of memory in the CID map");
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
/* The ngtcp2 callbacks.                                                     */

static ngtcp2_conn *dammi_conn(ngtcp2_crypto_conn_ref *ref)
{
	connessione *c = ref->user_data;
	return c->conn;
}

static void casuale(uint8_t *dest, size_t destlen, const ngtcp2_rand_ctx *ctx)
{
	(void)ctx;
	if (RAND_bytes(dest, (int)destlen) != 1) {
		registro_dice(REG_QUIC, "⛔ RAND_bytes failed");
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
	(void)sud;
	/* ⛔⛔ STREAM CREDIT IS GIVEN BACK WHEN A CLIENT STREAM CLOSES — 2 Oct
	 *      2026, and it closes the `[?]` of `initial_max_streams_uni`.
	 *
	 * `[M]` round `cure-intel-1`, bench `15-f014c`: the client's unidirectional
	 *   streams go from 2 to 74, that is EXACTLY 19, and then no more open —
	 *   Chrome writes «Failed to create send stream», on Firefox the
	 *   announcement stays hanging.  ⇒ `ngtcp2` does NOT renew the credit on
	 *   its own: the exception the box below hoped for does not apply.  For
	 *   the user: after fifteen or so copies the clipboard stops working,
	 *   which is the «not always» of their manual test.
	 * ⇒ One client stream closed, one new granted: §2.3 wants «16 available
	 *   at all times», not 16 over the whole session.  It is what the `ngtcp2`
	 *   example server does. */
	if (!ngtcp2_conn_is_local_stream(conn, stream_id)) {
		if (ngtcp2_is_bidi_stream(stream_id))
			ngtcp2_conn_extend_max_streams_bidi(conn, 1);
		else
			ngtcp2_conn_extend_max_streams_uni(conn, 1);
	}
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
	registro_dettaglio(REG_QUIC, "TLS handshake completed with %s",
	                   c->provenienza);
	return 0;
}

/* ⛔⭐ DATAGRAMS ARRIVE, AND UNTIL TONIGHT THEY VANISHED WITHOUT A LINE —
 *     finding B-10, night of 10 Aug 2026.
 *
 *     This server ANNOUNCES datagrams, and announces them twice as §2.2
 *     requires: `max_datagram_frame_size` in the transport parameters and
 *     `settings.h3_datagram = 1` in HTTP/3.  ⛔ So the browser can send some
 *     **today** — three bytes from the page are enough — and among the
 *     `ngtcp2_callbacks` `recv_datagram` WAS NOT THERE: the packet ended up in
 *     an unregistered callback and vanished, and nothing appeared in the log.
 *
 * ⛔ §6.3 says «a datagram shorter than 12 bytes, or with a `tipo` other than
 *    `0x0401`, is discarded **writing it in the log**», and §3 closes the list
 *    of the five exceptions with «and every tolerance must be written in the
 *    log: a silent tolerance is indistinguishable from a defect».  The second
 *    declared exception of §3 is «it is discarded», not «it is discarded
 *    silently», and the difference is the whole point of that section.
 *
 * ⚠ In phase 1 there is NO audio, so everything is discarded here — but the
 *   difference between «the audio does not arrive» and «the audio arrives and
 *   I throw it away» on the day audio exists can be seen only if this line
 *   exists from before.
 *
 * ⛔ And the lines are RATIONED, not one per packet: a client that sends a
 *   thousand datagrams per second would fill the log, which is another way of
 *   losing the information.  The total count is always there. */
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
		              "⚠ TOLERANCE (§3 exception 2, §6.3): datagram of %zu "
		              "bytes from %s DISCARDED — in phase 1 there is no audio and "
		              "no type of §6.3 can be served.  In all: %llu "
		              "datagrams, %llu bytes",
		              len, c->provenienza,
		              (unsigned long long)c->datagram_visti,
		              (unsigned long long)c->datagram_byte);
	return 0;
}

/* ------------------------------------------------------------------------ */
/* Sending.                                                                  */

static void manda(trasporto *t, const struct sockaddr *sa, socklen_t salen,
                  const uint8_t *dati, size_t len)
{
	ssize_t n;
	do {
		n = sendto(t->fd, dati, len, 0, sa, salen);
	} while (n < 0 && errno == EINTR);
	if (n < 0) {
		/* ⚠ DECLARED FALLBACK (`CODER.md` §4.2): if the socket is full the
		 *   packet is lost, and QUIC retransmits it on its own — loss is the
		 *   condition its recovery exists to handle.  ⛔ It is not silent:
		 *   the line below is what tells «the network loses» from «the
		 *   server throws away». */
		registro_dice(REG_QUIC, "packet of %zu bytes NOT sent: %s", len,
		              strerror(errno));
	}
}

/* ⛔ The callback ngtcp2 invokes for every packet, and the `user_data` it
 *    passes is the CONNECTION's — not the WebTransport layer's.
 *    ⚠ This two-line detour exists on purpose: passing `wt_scrivi` directly to
 *    ngtcp2 would compile (they are two `void *`) and would make the
 *    WebTransport layer read the fields of `connessione`.  `[M]` 10 Aug 2026:
 *    the server opened HTTP/3 and died at the first write with
 *    `ERR_CALLBACK_FAILURE`, without any of its log lines naming the cause. */
static ngtcp2_ssize scrivi_pkt(ngtcp2_conn *conn, ngtcp2_path *path,
                               ngtcp2_pkt_info *pi, uint8_t *dest, size_t destlen,
                               ngtcp2_tstamp ts, void *user_data)
{
	connessione *c = user_data;
	(void)conn;
	return wt_scrivi(c->w, path, pi, dest, destlen, ts);
}

/* Writes everything this connection has to send. */
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
		registro_dice(REG_QUIC, "⛔ write failed for %s: %s",
		              c->provenienza, ngtcp2_strerror((int)n));
		c->morta = true;
		return;
	}
	ngtcp2_conn_update_pkt_tx_time(c->conn, ts);
	if (n == 0)
		return;

	/* ⚠ No GSO: one packet per `sendto`.  It is a declared fallback — it
	 *   costs syscalls, not correctness — and phase 1 sends no video.  ⛔ It
	 *   must be redone before phase 2, where frames are one stream each and
	 *   syscalls add up. */
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
			registro_dice(REG_QUIC, "connection with %s closed (%zu left)",
			              c->provenienza, t->quante - 1);
			connessione_libera(t, c);
			t->quante--;
			continue;
		}
		p = &c->prossima;
	}
}

/* ------------------------------------------------------------------------ */

/* ⭐⭐⭐ THE OUTCOME OF THE DATAGRAMS WE SEND — 23 Aug 2026.
 *
 *    ⛔ Until today `ngtcp2_callbacks` registered `recv_datagram` and nothing
 *       else: INCOMING datagrams were counted (finding B-10), OUTGOING ones —
 *       that is, the audio — vanished on the wire without leaving a trace.
 *       «The audio did not arrive» and «it arrived and the client threw it
 *       away» looked the same, and it is the same defect as back then in the
 *       other direction.
 *
 * ⭐ AND `lost_datagram` IS NOT ENOUGH: `ngtcp2.h:3442` warns that the loss can
 *   be **spurious** — declared and then acknowledged.  Recording only the
 *   losses we would count OUT-OF-ORDER packets as lost, that is we would give
 *   a number higher than the truth without saying so.  ⇒ `ack_datagram` is
 *   registered too, and `webtransport.c` recognises the false losses: it is
 *   the MEASURE OF REORDERING, and on reordering ngtcp2 gives nothing else.
 *
 * ⚠ They decide nothing: they count.  The `dgram_id` is the one
 *   `dgram_scrivi_uno()` increments in `webtransport.c`.
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
		/* ⛔ §6.3: datagrams are announced, so they arrive — and what arrives
		 *    is either served or discarded WRITING IT DOWN.  Finding B-10. */
		.recv_datagram = cb_recv_datagram,
		/* ⭐⭐ And the outcome of those WE send — as a pair, and the reason
		 *    the pair is mandatory is above the two functions: alone,
		 *    `lost_datagram` would count reordering as loss. */
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
	/* ⛔ `RCP.md` §2.3: «the server MUST grant the client credit for its
	 *    unidirectional streams: at least 16 available at all times».
	 *    ⚠ The client opens one input stream and one for every clipboard
	 *    transfer: if the credit ran out, input would not start at all and the
	 *    symptom would be «the desktop does not respond», not «credit
	 *    exhausted» — that is, a diagnosis pointing at phase 4 while the
	 *    defect is here.
	 *    ⭐ And the 3 of the ngtcp2 example are enough to open the session:
	 *       the session opens perfectly well with 3, and that is why no
	 *       functional bench of phase 1 would see it.
	 *
	 * ⛔⭐ AND 16 WERE NOT ENOUGH — finding B-12, night of 10 Aug 2026.  §2.3
	 *     asks for «at least 16 **available at all times**», and this number is
	 *     a TOTAL.  As soon as HTTP/3 opens, the browser opens THREE
	 *     unidirectional streams of its own — the HTTP/3 control channel and
	 *     the two of QPACK — and they stay open for the whole connection: the
	 *     client was left with **13 from the first second**.  ⚠ Our own code
	 *     takes it for granted, as in `webtransport.c` it checks the mirror
	 *     credit with `< 3` before opening our three.
	 *
	 *     ⭐ Hence 19 = 16 + 3: the number of §2.3 stays 16, and the three of
	 *        HTTP/3 are declared instead of being subtracted silently.
	 *
	 * ✅ CLOSED on 2 Oct 2026: the renewal is NOT automatic (`[M]` 19 streams
	 *    and then nothing more) — now `cb_stream_close` does it.  The text
	 *    below stays as a chronicle.
	 * `[?]` ⚠ AND AN OPEN QUESTION REMAINS, which is closed by a measurement
	 *   and not by a line: `ngtcp2` does not raise the stream ceiling on its
	 *   own, «except when a stream closes without `stream_open` having been
	 *   called».  This code does not register `stream_open`, so it probably
	 *   falls into that exception and the renewal is automatic — but no line
	 *   of the product declares it and nobody has measured it.  If the
	 *   exception did not apply, the client's twentieth unidirectional stream
	 *   would no longer open and the symptom would be «the desktop does not
	 *   respond».  ⛔ It is measured in phase 4, when the clipboard will open
	 *   one stream per transfer: before then no client opens more than four,
	 *   and a measurement without the load that provokes it is not a
	 *   measurement. */
	params.initial_max_streams_uni = 19;
	/* ⛔ §2.2: 30 s, imposed by the server. */
	params.max_idle_timeout = IDLE_MS * NGTCP2_MILLISECONDS;
	/* ⛔ §2.2: datagrams MUST be enabled on the HTTP/3 connection (they are
	 *    the audio).  ⚠ And without THIS transport parameter, announcing
	 *    SETTINGS_H3_DATAGRAM=1 is a protocol error. */
	params.max_datagram_frame_size = 65536;
	params.stateless_reset_token_present = 1;
	params.active_connection_id_limit = 7;
	params.grease_quic_bit = 1;
	params.original_dcid = hd->dcid;
	params.original_dcid_present = 1;
	/* ⛔ §2.3: the server MUST NOT disable migration — it is the reason QUIC
	 *    was chosen (`SPECIFICHE.md` §8.4): the phone that moves from WiFi to
	 *    the mobile network.  `disable_active_migration` is not touched, and
	 *    this line exists so that a reviewer can read that it is not an
	 *    oversight. */

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
	/* ⛔ AND 0-RTT IS NOT TURNED ON HERE (§2.3).  The ngtcp2 example calls
	 *    `SSL_set_quic_tls_early_data_enabled(ssl, 1)` precisely at this
	 *    point: the absence of that line IS the decision, and without this
	 *    comment it would look like an oversight.  The real switch-off is in
	 *    `tls.c`, at context level, where no session can turn it back on by
	 *    oversight. */
	ngtcp2_conn_set_tls_native_handle(c->conn, c->ossl);

	c->w = wt_nuovo(c->conn, &c->ultimo_errore, c->provenienza, t->aiuto);
	if (!c->w)
		goto male;

	c->prossima = t->prime;
	t->prime = c;
	t->quante++;
	cid_lega(t, &c->scid, c);

	registro_dice(REG_QUIC, "new connection from %s (%zu in all)",
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
	registro_dice(REG_QUIC, "QUIC version not ours: negotiation towards %s",
	              "the client");
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
		registro_dettaglio(REG_QUIC, "unreadable header: %s",
		                   ngtcp2_strerror(rv));
		return;
	}

	c = cid_trova(t, vc.dcid, vc.dcidlen);
	if (!c) {
		ngtcp2_pkt_hd hd;
		if (ngtcp2_accept(&hd, dati, len) != 0) {
			/* ⚠ No connection and it is not an Initial.  ⛔ DECLARED
			 *   FALLBACK: here the product should send a Stateless Reset,
			 *   which is the way to tell a client with old state «that
			 *   connection no longer exists» instead of making it wait the
			 *   30 s of inactivity.  It is not there: it is ignored, and the
			 *   line below is what tells «ignored» from «never arrived». */
			registro_dettaglio(REG_QUIC,
			                   "packet of %zu bytes for a connection "
			                   "that does not exist: ignored",
			                   len);
			return;
		}
		/* ⚠ No address validation with Retry: the product is used on one's
		 *   own network or VPN (`SPECIFICHE.md` §4.1).  ⛔ It must be put
		 *   back before exposing it, and it is declared here so that it does
		 *   not look like an oversight. */
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
		/* ⛔⭐ §5.3 — AND HERE, AND ONLY IF `rv == 0`: the packet has been
		 *     DECRYPTED AND AUTHENTICATED.  ⚠ A datagram arriving is not
		 *     enough — anyone can send one with someone else's address, and
		 *     would keep that someone's slot occupied.
		 *
		 * ⭐ It is the sign of life that was missing: until 16 Aug 2026 §5.3
		 *    looked at the last RCP byte, that is the last time the USER had
		 *    touched something, and thirty seconds spent reading a page were
		 *    enough to declare a live client gone.  ⛔ The price, measured: a
		 *    second device came in and took the first one's desktop. */
		if (rv == 0 && c->w)
			wt_segno_di_vita(c->w, ora);
	}
	if (rv != 0) {
		if (rv == NGTCP2_ERR_DRAINING || rv == NGTCP2_ERR_IDLE_CLOSE ||
		    rv == NGTCP2_ERR_CLOSING) {
			c->morta = true;
			return;
		}
		registro_dice(REG_QUIC, "read failed from %s: %s", c->provenienza,
		              ngtcp2_strerror(rv));
		/* ⚠ DECLARED FALLBACK: here the product should enter the closing
		 *   period and retransmit the CONNECTION_CLOSE for three RTTs.  It
		 *   is sent once only and closed.  ⛔ It does not touch RCP: §3.1
		 *   closes the WebTransport SESSION, not the QUIC connection, and
		 *   that road is intact. */
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
		/* A valid QUIC packet is never shorter than 21 bytes. */
		if (n < 21)
			continue;

		/* The LOCAL address is read from the ancillary message: without it,
		 * a server bound to `0.0.0.0` would give ngtcp2 a path with a wrong
		 * end, and path validation would fail as soon as the client changes
		 * network. */
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
			/* ⛔ «Empty» and «forbidden» look the same (`LEZIONI.md`
			 *    §1.9): if the kernel did not put the ancillary message,
			 *    it is SAID instead of pretending the local address is
			 *    zero. */
			socklen_t l = sizeof locale;
			if (getsockname(t->fd, (struct sockaddr *)&locale, &l) == 0) {
				localelen = l;
				registro_dettaglio(REG_QUIC,
				                   "no IP_PKTINFO: using the socket's "
				                   "address");
			} else {
				registro_dice(REG_QUIC,
				              "⛔ no local address for a "
				              "packet of %zd bytes: discarded",
				              n);
				continue;
			}
		}
		/* The port does not travel in the `pktinfo`: it is the socket's. */
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

/* ⭐ THE PAM VERDICT COMING BACK — `DECISIONI.md` §1.10.
 *
 * ⛔ It is passed to all live connections and ONE only takes it: the request
 *    number is a number of the process, and whoever knows whom it belongs to
 *    is `rcp.c`.  ⚠ A loop over at most sixteen connections costs less than a
 *    table to keep aligned — and a table of pointers to connections that can
 *    die while PAM answers is precisely the place where a dangling pointer is
 *    born.
 *
 * ⭐ And if nobody takes it, it is WRITTEN: «the connection died while PAM was
 *    answering» and «the verdict ended up nowhere because of a defect of ours»
 *    look the same, and without this line they would be indistinguishable. */
void trasporto_verdetto(trasporto *t, uint64_t pratica, bool ammesso,
                        bool ripresa)
{
	for (connessione *c = t->prime; c; c = c->prossima) {
		if (c->morta || !c->w)
			continue;
		if (wt_verdetto(c->w, pratica, ammesso, ripresa)) {
			/* ⛔ And it is written again AT ONCE: the verdict may have made
			 *    the `AMMESSO`/`RESPINTO` ripe, and waiting for the next beat
			 *    would add up to 100 ms for whoever authenticates — that is,
			 *    it would worsen the number this cure must not touch. */
			if (wt_battito_ns(c->w) != UINT64_MAX)
				wt_batti(c->w, adesso_ns());
			trasporto_scrivi(t);
			return;
		}
	}
	registro_dice(REG_RCP,
	              "⚠ the verdict of request %llu (%s) was taken by "
	              "nobody: the connection waiting for it is gone",
	              (unsigned long long)pratica, ammesso ? "admitted" : "rejected");
}

void trasporto_scaduti(trasporto *t)
{
	ngtcp2_tstamp ora = adesso_ns();

	for (connessione *c = t->prime; c; c = c->prossima) {
		if (c->morta)
			continue;
		/* ⭐ OUR clock, before QUIC's: it is the one that makes the ceilings
		 *    of `RCP.md` §4.6 expire and the closing capsule ripen.  In the
		 *    graft the keep-alive did it, that is bytes on the wire; here
		 *    nothing goes out. */
		if (wt_battito_ns(c->w) <= ora)
			wt_batti(c->w, ora);

		/* ⛔⭐⭐ PHASE 9 — THE DEAD LINE, and it is dropped HERE because the
		 *      QUIC connection belongs to this file: `webtransport.c` has the
		 *      counters and takes the decision (with its log line), this piece
		 *      carries it out.
		 *
		 * ⛔ ONE `CONNECTION_CLOSE` is sent and the connection closed — the
		 *    same declared fallback as the failed read, a hundred lines
		 *    above: the product should enter the closing period and
		 *    retransmit it for three RTTs.  ⚠ Here it costs less than
		 *    elsewhere: by hypothesis the line does not carry, and that packet
		 *    is an attempt, not a promise.  If it does not arrive, the client
		 *    notices with ITS OWN idle timeout.
		 *
		 * ⚠ And the reason is NOT an RCP code: `webtransport.c` has already
		 *   written `H3_NO_ERROR` with the reason in clear inside
		 *   `c->ultimo_errore`, and §9 forbids inventing a new reason of §8.2
		 *   inside RCP/1. */
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
			              "⛔ %s: DEAD LINE — the QUIC connection is closing "
			              "(one single CONNECTION_CLOSE, %s).  The why, with the "
			              "numbers, is in the `linea-morta` line above",
			              c->provenienza,
			              n > 0 ? "sent" : "⚠ not even sent");
			c->morta = true;
			continue;
		}

		if (ngtcp2_conn_get_expiry2(c->conn) <= ora) {
			int rv = ngtcp2_conn_handle_expiry(c->conn, ora);
			if (rv != 0) {
				if (rv == NGTCP2_ERR_IDLE_CLOSE)
					registro_dice(REG_QUIC,
					              "%s: thirty seconds of silence, "
					              "disconnected (§2.2)",
					              c->provenienza);
				else
					registro_dice(REG_QUIC, "%s: timer expired: %s",
					              c->provenienza, ngtcp2_strerror(rv));
				c->morta = true;
			}
		}
	}
	trasporto_scrivi(t);
}

/* ⛔⭐ §8.1 — «NEVER WITH A SILENCE»: THE SERVER THAT SHUTS DOWN SAYS SO.
 *     Finding B-7, night of 10 Aug 2026.
 *
 *     Before tonight `systemctl stop` (or Ctrl-C) with an active session did
 *     this: the loop exited, «chiusura richiesta: 1 connessioni QUIC vive» was
 *     written, and `trasporto_chiudi()` freed everything.  ⛔ No
 *     `CONGEDO(0x0C)`, no closing capsule with `0x0C`, and not even a QUIC
 *     `CONNECTION_CLOSE`: the client was left waiting the 30 seconds of
 *     inactivity and showed «network error».
 *
 *     ⚠ The reason `0x0C SERVER_IN_CHIUSURA` exists in §8.2 on purpose, and it
 *       was defined in `rcp.h` without any line of the product emitting it.
 *
 * ⭐ Returns how many connections still have something to get out: whoever
 *    shuts down runs the loop until it is zero, instead of counting rounds —
 *    «handed to ngtcp2» is not «out on the wire». */
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

/* ⛔ What holds back whoever has not finished yet — for the shutdown log.
 *    Returns the first reason found, which is enough to send the diagnosis
 *    the right way. */
const char *trasporto_perche_restano(const trasporto *t)
{
	for (connessione *c = t->prime; c; c = c->prossima)
		if (!c->morta && c->w && wt_ha_da_dire(c->w))
			return wt_perche_ha_da_dire(c->w);
	return "nothing";
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
		registro_dice(REG_QUIC, "⛔ %s:%s does not resolve", indirizzo, porta);
		return NULL;
	}
	for (r = ris; r; r = r->ai_next) {
		fd = socket(r->ai_family, r->ai_socktype | SOCK_NONBLOCK, r->ai_protocol);
		if (fd < 0)
			continue;
		/* ⛔⭐ `SO_REUSEADDR` IS NOT SET HERE, AND IT IS NOT AN OVERSIGHT.
		 *
		 *     `[M]` 10 Aug 2026, first switch-on: with `SO_REUSEADDR` the UDP
		 *     socket bound to 7447 **while another server already held it**
		 *     — on Linux two unicast UDP sockets with that option share the
		 *     port, and the packets are taken by only one of the two.  ⛔ The
		 *     symptom would be «the server is on and the page does not
		 *     connect», with two processes both convinced they are listening:
		 *     none of the errors that would come out would name the port.
		 *
		 * ⚠ On TCP instead it stays, and there it is really needed: without
		 *   it, a restart finds the port held by the socket in TIME_WAIT.
		 *   ⭐ And the difference between the two cases is that on TCP the
		 *   kernel REFUSES a second listener anyway, while on UDP it accepts
		 *   it — that is, it is the only one of the two where the option buys
		 *   a silent fault instead of a convenience. */
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
		registro_dice(REG_QUIC, "⛔ cannot bind to %s:%s over UDP: %s", indirizzo,
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
		registro_dice(REG_QUIC, "⛔ cannot generate the static secret");
		trasporto_chiudi(t);
		return NULL;
	}

	if (ngtcp2_crypto_ossl_init() != 0) {
		registro_dice(REG_QUIC, "⛔ ngtcp2_crypto_ossl_init");
		trasporto_chiudi(t);
		return NULL;
	}

	registro_dice(REG_QUIC,
	              "listening over UDP on %s:%s — max_idle_timeout=%d ms, datagrams "
	              "enabled and discarded with a line (§6.3), %d unidirectional "
	              "streams granted = 16 of §2.3 + the 3 of HTTP/3",
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
