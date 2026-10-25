/*
 * stubs_quic.c — ngtcp2 v1.25, ngtcp2_crypto, the four OpenSSL calls of `accept_conn()` and the
 * WebTransport layer, PLAYED under the real `src/transport.c` (target `quic-conn`).
 * What is played and why, and the rules it keeps: `quic_conn.h`.
 *
 * ⭐ WHERE THE FUZZER'S BYTES GO.  A packet the harness delivers is a real UDP datagram with a
 *    real QUIC header (the dcid routes it in `read_packet()`); what follows the header is what
 *    ngtcp2 "found" after decrypting it — a little script of events, read by `read_pkt` below:
 *
 *      byte 0:  bit 7 = the packet does NOT decrypt (dropped, `read_pkt` returns 0)
 *               bit 6 = probing only (PATH_CHALLENGE/PADDING: a new path does not become current)
 *      then events, `e` = kind (low 4 bits) · p = e >> 4, each with its own argument bytes:
 *        0 END                 p = the return code (`RV[]`), and the script ends
 *        1 TX KEY              p & 1: HANDSHAKE or 1RTT → `recv_tx_key` (each level once)
 *        2 HANDSHAKE DONE      → `handshake_completed` (once, after the 1RTT key, not on the
 *                                first packet)
 *        3 STREAM DATA         a0 = stream (type a0 & 3, number a0 >> 2), a1 = length; p & 1 FIN
 *        4 STREAM CLOSE        a0 = an open stream, a1 = code; p & 1 RX code set, p & 2 TX code
 *        5 STREAM RESET        a0 = an open stream the peer sends on, a1 = code
 *        6 STOP SENDING        a0 = an open stream we send on, a1 = code
 *        7 ACKED               a0 = an open stream we send on, a1 = length
 *        8 MAX STREAMS BIDI    a0
 *        9 MAX STREAM DATA     a0 = an open stream, a1
 *       10 DATAGRAM            a0 = length, then the bytes → `recv_datagram`
 *       11 DATAGRAM FATE       a0 = id; p & 1: lost, else acknowledged
 *       12 NEW CID             p + 1 of them, up to the peer's active_connection_id_limit
 *       13 RETIRE CID          a0 = which of ours; removed later, in `handle_expiry`
 *       14 PATH RESULT         p & 1: the path being validated failed (back to the fallback);
 *                              → `path_validation` (success or failure) when a move is pending
 *       15 LOCAL / RAND        p & 1: a stream WE opened (a0); p & 2: ngtcp2 asks `rand`
 *    Stream data and datagrams only after the handshake (RFC 9001 §5.7: a server does not
 *    process 1-RTT before it): an event ngtcp2 could not produce is skipped, not invented.
 */
#include "common.h"
#include "quic_conn.h"

#include <ngtcp2/ngtcp2.h>
#include <ngtcp2/ngtcp2_crypto.h>
#include <ngtcp2/ngtcp2_crypto_ossl.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "webtransport.h"
#include "cid.h" /* the played cid.c below (`cid-firmati`) */

rxq_expectation rxq_expect;
rxq_received rxq_rx;
rxq_reg rxq_conns[RXQ_CONNS];
uint64_t rxq_last_close_code;
unsigned rxq_retries;
const char *const RXQ_STATE_NAMES[RXQ_ST_N] = {"(none)", "wait-hello", "wait-credentials",
                                               "wait-verdict", "wait-attach", "active",
                                               "finished", "detached-by-silence"};
size_t rxq_nconns;
int rxq_fail_next;
uint64_t rxq_now_ns;
void (*rxq_on_birth)(const uint8_t *token, size_t len);

/* the Retry token the last `verify_retry_token2` accepted (`rxq_on_birth`) */
static uint8_t token_seen[2048];
static size_t token_seen_len;

#define DIE(...)                                                                             \
	do {                                                                                 \
		fprintf(stderr, "⛔ quic-conn ORACLE: " __VA_ARGS__);                       \
		fprintf(stderr, "\n");                                                       \
		abort();                                                                     \
	} while (0)

/* ── the played RAND_bytes: deterministic, so that a reproducer reproduces ── */
static uint64_t rng;
void rxq_rng_seed(uint64_t seed) { rng = seed ^ 0x9e3779b97f4a7c15ull; }
bool rxq_rand(uint8_t *d, size_t n)
{
	if (rxq_fail_next == RXQ_FAIL_RAND) {
		rxq_fail_next = 0;
		return false;
	}
	for (size_t i = 0; i < n; i++) {
		uint64_t z = (rng += 0x9e3779b97f4a7c15ull);
		z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ull;
		z = (z ^ (z >> 27)) * 0x94d049bb133111ebull;
		d[i] = (uint8_t)(z ^ (z >> 31));
	}
	return true;
}

/* ── the connection ─────────────────────────────────────────────────── */
typedef struct {
	struct sockaddr_storage local, remote;
	socklen_t ll, rl;
} rxq_path;

typedef struct {
	int64_t id;
	uint64_t rx_off;
	bool fin;
} rxq_stream;

enum { ST_HANDSHAKE, ST_DONE, ST_CLOSING, ST_DRAINING };

/* ⭐ the last ngtcp2_conn_read_pkt decrypted its packet (the oracle of §5.3) */
static bool rxq_read_decrypted;

struct ngtcp2_conn {
	uint32_t magic;
	rxq_reg *reg;
	ngtcp2_callbacks cb;
	void *user_data;
	ngtcp2_transport_params params;
	int state;
	bool key_hs, key_1rtt;
	unsigned reads;
	void *tls;
	/* paths */
	rxq_path path[RXQ_PATHS];
	size_t npath;
	int cur, fallback, probe; /* index, or -1 */
	/* our CIDs: seq = index; 0 active · 1 retired, removal pending · 2 removed */
	ngtcp2_cid scid[RXQ_CIDS];
	uint8_t scid_st[RXQ_CIDS];
	uint64_t scid_retire_at[RXQ_CIDS];
	size_t nscid;
	size_t cid_limit; /* the peer's active_connection_id_limit */
	/* streams */
	rxq_stream s[RXQ_STREAMS];
	size_t ns;
	uint64_t max_streams_bidi, max_streams_uni; /* credit WE granted */
	/* timers */
	uint64_t idle_ts, loss_at;
	/* pacing, as ngtcp2 v1.25 `tx.pacing`: bytes written since the last
	 * `update_pkt_tx_time`, and the instant before which no new data goes out */
	size_t pace_bytes;
	uint64_t pace_next;
	/* the remote address the `wt` knows (the birth one, then each validated move) and the
	 * `wt_moved()` calls seen inside the current `path_validation` */
	struct sockaddr_storage told;
	socklen_t toldlen;
	int moves_seen;
	uint64_t pkt_recv; /* the packets not discarded (ngtcp2's `cstat.pkt_recv`) */
	int in_cb; /* >0 while one of transport.c's callbacks runs */
	/* ⭐ audit ngtcp2 1.25 oracles (24 Oct 2026) */
	bool dropped;          /* read_pkt returned NGTCP2_ERR_DROP_CONN: «drop silently» — NOTHING may be sent or read */
	int expiry_rv;         /* handle_expiry failed with this (0 = not failed) */
	int closes_after_exp;  /* write_connection_close calls since that failure */
	bool h3_set;           /* a played wt callback wrote an H3 code into last_error */
	uint64_t h3_code;
};
#define MAGIC 0x51c0c0a1u

rxq_reg *rxq_reg_of(const struct ngtcp2_conn *c) { return c->reg; }

/* ⭐ Every entry point TOUCHES the connection: a call on a deleted one is a heap
 *    use-after-free ASan reports, and a call from inside a callback is ours to refuse. */
static ngtcp2_conn *live(const ngtcp2_conn *c, bool outside_callbacks, const char *fn)
{
	if (c->magic != MAGIC)
		DIE("%s on something that is not a connection", fn);
	if (outside_callbacks && c->in_cb)
		DIE("%s called from inside one of the connection's own callbacks "
		    "(ngtcp2: «must not be called from inside the callback functions»)", fn);
	return (ngtcp2_conn *)c;
}

static void path_set(rxq_path *p, const ngtcp2_path *src)
{
	memset(p, 0, sizeof *p);
	if ((size_t)src->local.addrlen > sizeof p->local || (size_t)src->remote.addrlen > sizeof p->remote)
		DIE("a path with an address longer than a sockaddr_storage");
	memcpy(&p->local, src->local.addr, src->local.addrlen);
	p->ll = src->local.addrlen;
	memcpy(&p->remote, src->remote.addr, src->remote.addrlen);
	p->rl = src->remote.addrlen;
}

static bool path_eq(const rxq_path *p, const ngtcp2_path *q)
{
	return p->ll == q->local.addrlen && p->rl == q->remote.addrlen &&
	       memcmp(&p->local, q->local.addr, p->ll) == 0 &&
	       memcmp(&p->remote, q->remote.addr, p->rl) == 0;
}

/* `ngtcp2_path_copy()`: the addresses are copied INTO the storage the caller's path points
 * at (an `ngtcp2_sockaddr_union` in `ngtcp2_path_storage`) — as ngtcp2 does, so a path whose
 * pointers are not a storage is ASan's to see. */
static void path_out(const ngtcp2_conn *c, int idx, ngtcp2_path *dst, const char *who)
{
	const rxq_path *p = &c->path[idx];
	if (!dst)
		return;
	memcpy(dst->local.addr, &p->local, p->ll);
	dst->local.addrlen = p->ll;
	memcpy(dst->remote.addr, &p->remote, p->rl);
	dst->remote.addrlen = p->rl;
	dst->user_data = NULL;
	rxq_expect.valid = true;
	memcpy(&rxq_expect.to, &p->remote, p->rl);
	rxq_expect.tolen = p->rl;
	memcpy(&rxq_expect.from, &p->local, p->ll);
	rxq_expect.fromlen = p->ll;
	rxq_expect.who = who;
}

/* ⛔ THE LOCAL-END ORACLE (15 Oct 2026): the path `transport.c` hands ngtcp2 for a datagram
 *    has as local end the address THAT datagram arrived on — or ngtcp2 would answer (and
 *    validate a migration) from the wrong one of the server's addresses. */
/* ⭐ ON by default since the migration was ported (branch migrazione-su-limiti): read_packet hands ngtcp2 the path the
 *    datagram arrived on.  Case kept in known/local-end-1.0.bin: on the code WITHOUT the migration (1.0, and
 *    limiti-su-quic) this oracle fires; build with -DQC_LOCAL_END_ORACLE=0 to switch it off. */
#ifndef QC_LOCAL_END_ORACLE
#define QC_LOCAL_END_ORACLE 1
#endif
static void local_is_received(const ngtcp2_path *path, const char *fn)
{
#if QC_LOCAL_END_ORACLE
	if (!rxq_rx.valid)
		DIE("%s with no datagram received", fn);
	if (path->local.addrlen == 0 ||
	    !rxq_same_host((const struct sockaddr *)path->local.addr, (socklen_t)path->local.addrlen,
	                   (const struct sockaddr *)&rxq_rx.local, rxq_rx.locallen))
		DIE("%s with a path whose local end is not the address the datagram arrived on", fn);
#else
	(void)path; (void)fn;
#endif
}

static int write_path(const ngtcp2_conn *c)
{
	switch (c->reg->write_path % 3) {
	case 1:
		if (c->probe >= 0)
			return c->probe;
		break;
	case 2:
		if (c->fallback >= 0)
			return c->fallback;
		break;
	}
	return c->cur;
}

/* ── connection lifecycle ────────────────────────────────────────────── */
void ngtcp2_settings_default_versioned(int v, ngtcp2_settings *s)
{
	(void)v;
	memset(s, 0, sizeof *s);
	s->initial_rtt = NGTCP2_DEFAULT_INITIAL_RTT;
	s->max_tx_udp_payload_size = 1500 - 48;
	s->handshake_timeout = UINT64_MAX;
}

void ngtcp2_transport_params_default_versioned(int v, ngtcp2_transport_params *p)
{
	(void)v;
	memset(p, 0, sizeof *p);
	p->max_udp_payload_size = 65527;
	p->ack_delay_exponent = 3;
	p->max_ack_delay = 25 * NGTCP2_MILLISECONDS;
	p->active_connection_id_limit = 2;
}

int ngtcp2_conn_server_new_versioned(ngtcp2_conn **pconn, const ngtcp2_cid *dcid,
                                     const ngtcp2_cid *scid, const ngtcp2_path *path,
                                     uint32_t version, int cbv, const ngtcp2_callbacks *cb,
                                     int sv, const ngtcp2_settings *settings, int tpv,
                                     const ngtcp2_transport_params *params,
                                     const ngtcp2_mem *mem, void *user_data)
{
	ngtcp2_conn *c;
	rxq_reg *r;
	(void)dcid; (void)version; (void)cbv; (void)sv; (void)tpv; (void)mem;
	if (rxq_fail_next == RXQ_FAIL_SERVER_NEW) {
		rxq_fail_next = 0;
		return NGTCP2_ERR_NOMEM;
	}
	if (rxq_nconns == RXQ_CONNS)
		return NGTCP2_ERR_NOMEM; /* the harness's table is full: as out of memory */
	if (!params->original_dcid_present || scid->datalen > NGTCP2_MAX_CIDLEN)
		DIE("server_new with transport parameters ngtcp2 would refuse");
	/* ⭐ `cid-firmati`: the first id of every connection is one the product made with its key */
	if (!rxq_cid_signed(scid->data, scid->datalen))
		DIE("server_new with a source id that does not verify");
	local_is_received(path, "server_new");
	c = calloc(1, sizeof *c);
	if (!c)
		return NGTCP2_ERR_NOMEM;
	c->magic = MAGIC;
	c->cb = *cb;
	c->user_data = user_data;
	c->params = *params;
	c->state = ST_HANDSHAKE;
	path_set(&c->path[0], path);
	c->npath = 1;
	c->cur = 0;
	c->fallback = c->probe = -1;
	c->scid[0] = *scid;
	c->nscid = 1;
	c->idle_ts = settings->initial_ts;
	c->loss_at = UINT64_MAX;
	c->pace_next = UINT64_MAX;
	memcpy(&c->told, &c->path[0].remote, c->path[0].rl);
	c->toldlen = c->path[0].rl;
	c->max_streams_bidi = params->initial_max_streams_bidi;
	c->max_streams_uni = params->initial_max_streams_uni;
	r = &rxq_conns[rxq_nconns++];
	r->used = r->alive = true;
	r->conn = c;
	memcpy(&r->born, &c->path[0].remote, c->path[0].rl);
	r->born_ns = settings->initial_ts;
	r->bornlen = c->path[0].rl;
	/* the routes the harness may aim at: the dcid of the client's Initial (after a Retry, the
	 * Retry's scid) and our first scid */
	r->cid[0] = params->retry_scid_present ? params->retry_scid : params->original_dcid;
	r->cid[1] = *scid;
	r->ncid = 2;
	r->wt_pkts = 1;
	r->wt_pkt_len = 1200;
	r->wt_beat_at = UINT64_MAX;
	r->quantum = 64 * 1024; /* ngtcp2: `cstat->send_quantum = 64 * 1024` at birth */
	c->reg = r;
	c->cid_limit = 2 + (rxq_nconns % 6); /* the client's limit: 2 … 7 */
	*pconn = c;
	return 0;
}

void ngtcp2_conn_del(ngtcp2_conn *c)
{
	if (!c)
		return;
	live(c, true, "ngtcp2_conn_del");
	/* ⭐ handle_expiry error ⇒ EXACTLY ONE CONNECTION_CLOSE (ngtcp2 doc: «NGTCP2_ERR_IDLE_CLOSE ... drop the
	 *    connection without calling ngtcp2_conn_write_connection_close.  If it returns any of the other negative
	 *    error codes, close the connection by sending the terminal packet produced by
	 *    ngtcp2_conn_write_connection_close»): none after IDLE_CLOSE, one after any other */
	if (c->expiry_rv == NGTCP2_ERR_IDLE_CLOSE && c->closes_after_exp != 0)
		DIE("connection #%td: %d CONNECTION_CLOSE after handle_expiry returned IDLE_CLOSE (zero expected)",
		    c->reg - rxq_conns, c->closes_after_exp);
	if (c->expiry_rv && c->expiry_rv != NGTCP2_ERR_IDLE_CLOSE && c->closes_after_exp != 1)
		DIE("connection #%td: %d CONNECTION_CLOSE after handle_expiry failed with %s (exactly one expected)",
		    c->reg - rxq_conns, c->closes_after_exp, ngtcp2_strerror(c->expiry_rv));
	c->reg->alive = false;
	c->reg->conn = NULL;
	c->magic = 0;
	free(c);
}

void ngtcp2_conn_set_tls_native_handle(ngtcp2_conn *c, void *h) { live(c, true, __func__)->tls = h; }
int ngtcp2_conn_in_closing_period2(const ngtcp2_conn *c)
{
	return live(c, false, __func__)->state == ST_CLOSING;
}
int ngtcp2_conn_in_draining_period2(const ngtcp2_conn *c)
{
	return live(c, false, __func__)->state == ST_DRAINING;
}
/* ⭐ ngtcp2 v1.25: the wait is proportional to the bytes written since the last call */
void ngtcp2_conn_update_pkt_tx_time(ngtcp2_conn *c, ngtcp2_tstamp ts)
{
	live(c, true, __func__);
	if (c->pace_bytes == 0)
		return;
	c->pace_next = ts + (uint64_t)c->pace_bytes * c->reg->pace_ns;
	c->pace_bytes = 0;
}
size_t ngtcp2_conn_get_send_quantum2(const ngtcp2_conn *c)
{
	return live(c, false, __func__)->reg->quantum;
}
size_t ngtcp2_conn_get_max_tx_udp_payload_size2(const ngtcp2_conn *c)
{
	return live(c, false, __func__)->reg->max_udp ? 1452 : 1200;
}
int ngtcp2_conn_is_local_stream2(const ngtcp2_conn *c, int64_t id)
{
	live(c, false, __func__);
	return (id & 1) == 1; /* server-initiated */
}
int ngtcp2_is_bidi_stream(int64_t id) { return (id & 2) == 0; }
void ngtcp2_conn_extend_max_streams_bidi(ngtcp2_conn *c, size_t n)
{
	live(c, false, __func__)->max_streams_bidi += n;
}
void ngtcp2_conn_extend_max_streams_uni(ngtcp2_conn *c, size_t n)
{
	live(c, false, __func__)->max_streams_uni += n;
}

/* ── callbacks: invoked only from inside an API call, never re-entered ── */
#define CALL(c, expr)                                                                        \
	({                                                                                   \
		int rv_;                                                                     \
		(c)->in_cb++;                                                                \
		rv_ = (expr);                                                                \
		(c)->in_cb--;                                                                \
		rv_;                                                                         \
	})

static rxq_stream *stream_find(ngtcp2_conn *c, int64_t id)
{
	for (size_t i = 0; i < c->ns; i++)
		if (c->s[i].id == id)
			return &c->s[i];
	return NULL;
}
static rxq_stream *stream_add(ngtcp2_conn *c, int64_t id)
{
	rxq_stream *s = stream_find(c, id);
	if (s)
		return s;
	if (c->ns == RXQ_STREAMS)
		return NULL;
	s = &c->s[c->ns++];
	memset(s, 0, sizeof *s);
	s->id = id;
	return s;
}
static void stream_del(ngtcp2_conn *c, rxq_stream *s)
{
	size_t i = (size_t)(s - c->s);
	memmove(&c->s[i], &c->s[i + 1], (c->ns - i - 1) * sizeof c->s[0]);
	c->ns--;
}
/* the peer sends on: client streams, and our bidi */
static bool peer_sends(int64_t id) { return !(id & 1) || !(id & 2); }
/* we send on: bidi, and our uni */
static bool we_send(int64_t id) { return !(id & 2) || (id & 1); }

typedef struct {
	const uint8_t *d;
	size_t n, i;
} rd;
static uint8_t u8(rd *r) { return r->i < r->n ? r->d[r->i++] : 0; }

/* The return codes ngtcp2_conn_read_pkt documents (and the ones its `conn_recv_*` pass up). */
static const int RV[16] = {
	0, NGTCP2_ERR_DRAINING, NGTCP2_ERR_CRYPTO, NGTCP2_ERR_PROTO,
	NGTCP2_ERR_FLOW_CONTROL, NGTCP2_ERR_DROP_CONN, NGTCP2_ERR_RETRY, NGTCP2_ERR_NOMEM,
	NGTCP2_ERR_STREAM_STATE, NGTCP2_ERR_FRAME_ENCODING, NGTCP2_ERR_TRANSPORT_PARAM,
	NGTCP2_ERR_STREAM_LIMIT, NGTCP2_ERR_FINAL_SIZE, NGTCP2_ERR_AEAD_LIMIT_REACHED,
	NGTCP2_ERR_CONNECTION_ID_LIMIT, NGTCP2_ERR_INTERNAL,
};

static int issue_cid(ngtcp2_conn *c, ngtcp2_tstamp ts)
{
	size_t active = 0;
	ngtcp2_cid cid;
	ngtcp2_stateless_reset_token tok;
	int rv;
	(void)ts;
	for (size_t i = 0; i < c->nscid; i++)
		active += c->scid_st[i] == 0;
	if (active >= c->cid_limit || c->nscid == RXQ_CIDS || !c->cb.get_new_connection_id2)
		return 0;
	memset(&cid, 0, sizeof cid);
	rv = CALL(c, c->cb.get_new_connection_id2(c, &cid, &tok, c->scid[0].datalen, c->user_data));
	if (rv != 0)
		return NGTCP2_ERR_CALLBACK_FAILURE;
	if (cid.datalen != c->scid[0].datalen)
		DIE("get_new_connection_id2 gave a CID of %zu bytes, %zu asked", cid.datalen,
		    c->scid[0].datalen);
	/* ⭐ `cid-firmati`: and every NEW_CONNECTION_ID the product hands out */
	if (!rxq_cid_signed(cid.data, cid.datalen))
		DIE("get_new_connection_id2 gave a CID that does not verify");
	c->scid[c->nscid] = cid;
	c->scid_st[c->nscid] = 0;
	c->nscid++;
	if (c->reg->ncid < RXQ_CIDS)
		c->reg->cid[c->reg->ncid++] = cid;
	return 0;
}

static int run_script(ngtcp2_conn *c, rd *r, ngtcp2_tstamp ts)
{
	while (r->i < r->n) {
		uint8_t e = u8(r), k = e & 15, p = e >> 4;
		bool app = c->state == ST_DONE; /* 1-RTT is processed only after the handshake */
		int rv = 0;
		switch (k) {
		case 0: /* END */
			rv = RV[p];
			if (rv == NGTCP2_ERR_RETRY && app)
				rv = NGTCP2_ERR_PROTO; /* only the handshake retries (DROP_CONN: any state, audit 24 Oct) */
			if (rv == NGTCP2_ERR_DRAINING)
				c->state = ST_DRAINING;
			return rv;
		case 1: { /* TX KEY */
			ngtcp2_encryption_level lv = (p & 1) ? NGTCP2_ENCRYPTION_LEVEL_1RTT
			                                     : NGTCP2_ENCRYPTION_LEVEL_HANDSHAKE;
			bool *have = (p & 1) ? &c->key_1rtt : &c->key_hs;
			if (*have || !c->cb.recv_tx_key)
				break;
			*have = true;
			rv = CALL(c, c->cb.recv_tx_key(c, lv, c->user_data));
			break;
		}
		case 2: /* HANDSHAKE DONE */
			if (c->state != ST_HANDSHAKE || !c->key_1rtt || c->reads < 2)
				break;
			c->state = ST_DONE;
			if (c->cb.handshake_completed)
				rv = CALL(c, c->cb.handshake_completed(c, c->user_data));
			if (rv == 0)
				rv = issue_cid(c, ts); /* ngtcp2 fills the peer's limit from here on */
			break;
		case 3: { /* STREAM DATA */
			uint8_t a0 = u8(r), len = u8(r);
			int64_t id = (int64_t)((a0 & 3) | ((uint64_t)(a0 >> 2) << 2));
			rxq_stream *s;
			const uint8_t *data = r->d + r->i;
			size_t n = len < r->n - r->i ? len : r->n - r->i;
			uint32_t fl = (p & 1) ? NGTCP2_STREAM_DATA_FLAG_FIN : 0;
			r->i += n;
			if (!app || !peer_sends(id))
				break;
			if ((id & 1) && !stream_find(c, id))
				break; /* our bidi: only once we opened it */
			s = stream_add(c, id);
			if (!s || s->fin || (n == 0 && !fl))
				break;
			if (fl)
				s->fin = true;
			rv = CALL(c, c->cb.recv_stream_data(c, fl, id, s->rx_off, n ? data : NULL, n,
			                                    c->user_data, NULL));
			s->rx_off += n;
			break;
		}
		case 4: { /* STREAM CLOSE */
			uint8_t a0 = u8(r), code = u8(r);
			uint32_t fl = 0;
			rxq_stream *s;
			if (!app || !c->ns)
				break;
			s = &c->s[a0 % c->ns];
			if (p & 1)
				fl |= NGTCP2_STREAM_CLOSE2_FLAG_RX_APP_ERROR_CODE_SET;
			if (p & 2)
				fl |= NGTCP2_STREAM_CLOSE2_FLAG_TX_APP_ERROR_CODE_SET;
			{
				int64_t id = s->id;
				stream_del(c, s); /* ngtcp2 forgets it: closed once */
				rv = CALL(c, c->cb.stream_close2(c, fl, id, code, (uint64_t)code << 8,
				                                 c->user_data, NULL));
			}
			break;
		}
		case 5: { /* STREAM RESET */
			uint8_t a0 = u8(r), code = u8(r);
			rxq_stream *s;
			if (!app || !c->ns)
				break;
			s = &c->s[a0 % c->ns];
			if (!peer_sends(s->id) || s->fin)
				break;
			s->fin = true;
			rv = CALL(c, c->cb.stream_reset(c, s->id, s->rx_off, code, c->user_data, NULL));
			break;
		}
		case 6: { /* STOP SENDING */
			uint8_t a0 = u8(r), code = u8(r);
			rxq_stream *s;
			if (!app || !c->ns)
				break;
			s = &c->s[a0 % c->ns];
			if (!we_send(s->id))
				break;
			rv = CALL(c, c->cb.stream_stop_sending(c, s->id, code, c->user_data, NULL));
			break;
		}
		case 7: { /* ACKED */
			uint8_t a0 = u8(r), len = u8(r);
			rxq_stream *s;
			if (!app || !c->ns)
				break;
			s = &c->s[a0 % c->ns];
			if (!we_send(s->id))
				break;
			rv = CALL(c, c->cb.acked_stream_data_offset(c, s->id, 0, len, c->user_data, NULL));
			break;
		}
		case 8: { /* MAX STREAMS BIDI (the peer's credit to us) */
			uint8_t a0 = u8(r);
			if (!app || !c->cb.extend_max_remote_streams_bidi)
				break;
			rv = CALL(c, c->cb.extend_max_remote_streams_bidi(c, a0, c->user_data));
			break;
		}
		case 9: { /* MAX STREAM DATA */
			uint8_t a0 = u8(r), v = u8(r);
			rxq_stream *s;
			if (!app || !c->ns)
				break;
			s = &c->s[a0 % c->ns];
			if (!we_send(s->id))
				break;
			rv = CALL(c, c->cb.extend_max_stream_data(c, s->id, (uint64_t)v << 10, c->user_data,
			                                          NULL));
			break;
		}
		case 10: { /* DATAGRAM */
			uint8_t len = u8(r);
			size_t n = len < r->n - r->i ? len : r->n - r->i;
			const uint8_t *data = r->d + r->i;
			r->i += n;
			if (!app)
				break;
			rv = CALL(c, c->cb.recv_datagram(c, 0, data, n, c->user_data));
			break;
		}
		case 11: { /* DATAGRAM FATE */
			uint8_t id = u8(r);
			if (!app)
				break;
			if (p & 1)
				rv = CALL(c, c->cb.lost_datagram(c, id, c->user_data));
			else
				rv = CALL(c, c->cb.ack_datagram(c, id, c->user_data));
			break;
		}
		case 12: /* NEW CID */
			if (!app)
				break;
			for (int j = 0; j <= p && rv == 0; j++)
				rv = issue_cid(c, ts);
			break;
		case 13: { /* RETIRE CID: the peer retires one of ours, ngtcp2 removes it later */
			uint8_t a0 = u8(r);
			size_t i;
			if (!app || !c->nscid)
				break;
			i = a0 % c->nscid;
			if (c->scid_st[i] != 0)
				break;
			c->scid_st[i] = 1;
			c->scid_retire_at[i] = ts + 3 * 60 * NGTCP2_MILLISECONDS; /* ~3 PTO */
			rv = issue_cid(c, ts); /* and a fresh one in its place */
			break;
		}
		case 14: /* PATH RESULT */
			/* ⭐ ngtcp2 validates the path a migration moved to (the current one, with
			 *    the old one as fallback) and says how it ended */
			if (c->fallback >= 0 && c->cb.path_validation) {
				rxq_path *vp = &c->path[c->cur];
				bool failed = p & 1;
				bool news = !failed && !(vp->rl == c->toldlen &&
				                         memcmp(&vp->remote, &c->told, vp->rl) == 0);
				ngtcp2_path np = {
					.local = {(ngtcp2_sockaddr *)&vp->local, vp->ll},
					.remote = {(ngtcp2_sockaddr *)&vp->remote, vp->rl},
				};
				c->moves_seen = 0;
				if (!c->reg->logged_in)
					c->reg->path_changes++;
				rv = CALL(c, c->cb.path_validation(
					c, 0, &np, NULL,
					failed ? NGTCP2_PATH_VALIDATION_RESULT_FAILURE
					       : NGTCP2_PATH_VALIDATION_RESULT_SUCCESS,
					c->user_data));
				/* ⛔ In THIS branch `wt_moved()` / `rcp_moved()` (3ced6e1b) are NOT ported, on
				 *    purpose: WebTransport and RCP stay on the BIRTH address (the ban and the RCP
				 *    registers too).  So the `wt` must be told ZERO times, whatever the result
				 *    (a validated move, a failed one, the same address): a call would mean the
				 *    product started to follow the move without this oracle being rewritten. */
				if (rv == 0 && c->moves_seen)
					DIE("the wt was told of a move %d times (zero expected: wt_moved() is not "
					    "ported in this branch; %s)", c->moves_seen,
					    failed ? "validation FAILED" : news ? "new address" : "same address");
				if (news) {
					memcpy(&c->told, &vp->remote, vp->rl);
					c->toldlen = vp->rl;
				}
			}
			if (c->fallback >= 0 && (p & 1))
				c->cur = c->fallback; /* validation failed: back to the old path */
			c->fallback = c->probe = -1;
			break;
		case 15: { /* LOCAL STREAM / RAND */
			uint8_t a0 = u8(r);
			if ((p & 1) && app)
				stream_add(c, (int64_t)(1 | (a0 & 2) | ((uint64_t)(a0 >> 2) << 2)));
			/* ⚠ not while a RAND_bytes failure is armed: `fill_random()` aborts on it ON
			 *   PURPOSE (no randomness, no QUIC), and that is not a finding */
			if ((p & 2) && c->cb.rand && rxq_fail_next != RXQ_FAIL_RAND) {
				uint8_t buf[8];
				ngtcp2_rand_ctx rc = {0};
				c->in_cb++;
				c->cb.rand(buf, sizeof buf, &rc); /* fill_random() aborts if RAND fails:
				                                     never armed here */
				c->in_cb--;
			}
			break;
		}
		}
		if (rv != 0)
			return NGTCP2_ERR_CALLBACK_FAILURE;
	}
	return 0;
}

/* The header length of the harness's packets (RFC 9000 §17): the script follows it. */
static size_t header_len(const uint8_t *d, size_t n)
{
	size_t i;
	if (!n)
		return 0;
	if (!(d[0] & 0x80))
		return 1 + 18 <= n ? 1 + 18 : n;
	i = 5;
	if (i >= n) return n;
	i += 1 + d[i];
	if (i >= n) return n;
	i += 1 + d[i];
	if (i >= n) return n;
	if (((d[0] >> 4) & 3) == 0) { /* Initial: the token */
		size_t tl = d[i];
		i += 1 + tl;
	}
	return i < n ? i : n;
}

int ngtcp2_conn_read_pkt_versioned(ngtcp2_conn *c, const ngtcp2_path *path, int piv,
                                   const ngtcp2_pkt_info *pi, const uint8_t *pkt, size_t pktlen,
                                   ngtcp2_tstamp ts)
{
	rd r;
	int idx = -1, rv;
	(void)piv; (void)pi;
	live(c, true, __func__);
	if (c->dropped)
		DIE("read_pkt on connection #%td after it returned DROP_CONN: transport.c must drop it silently "
		    "and read nothing more for it (not even the next packets of the same round)", c->reg - rxq_conns);
	if (!path || !pktlen)
		DIE("read_pkt with no path or an empty packet");
	local_is_received(path, "read_pkt");
	if (c->state == ST_CLOSING)
		return NGTCP2_ERR_CLOSING;
	if (c->state == ST_DRAINING)
		return NGTCP2_ERR_DRAINING;
	c->reads++;
	rxq_read_decrypted = false;
	{
		volatile uint8_t x = 0; /* ngtcp2 reads all of it */
		for (size_t i = 0; i < pktlen; i++)
			x ^= pkt[i];
		(void)x;
	}
	r.d = pkt;
	r.n = pktlen;
	r.i = header_len(pkt, pktlen);
	if (r.i < r.n && (r.d[r.i] & 0x80))
		return 0; /* it does not decrypt: dropped, and 0 (`conn_recv_cpkt`) */

	for (size_t i = 0; i < c->npath; i++)
		if (path_eq(&c->path[i], path))
			idx = (int)i;
	if (idx != c->cur) {
		if (c->state == ST_HANDSHAKE)
			return 0; /* «ignore packet from unknown path during handshake» */
		if (idx < 0) {
			if (c->npath == RXQ_PATHS)
				return 0;
			path_set(&c->path[c->npath], path);
			idx = (int)c->npath++;
		}
		if (r.i < r.n && (r.d[r.i] & 0x40)) {
			c->probe = idx; /* probing only: answered there, the current one stays */
		} else {
			/* a non-probing packet: the server moves (RFC 9000 §9.3) and validates */
			if (c->fallback < 0)
				c->fallback = c->cur;
			c->cur = idx;
			c->probe = idx;
		}
	}
	if (r.i < r.n)
		r.i++;
	c->idle_ts = ts; /* decrypted: the idle timer restarts (`conn_restart_timer_on_read`) */
	rxq_read_decrypted = true;
	c->pkt_recv++;
	if (c->reg->wt_pkts < 64)
		c->reg->wt_pkts++; /* and there is an ACK to send */
	if (c->reg->read_err) { /* ⭐ the fuzzer chose the return code (NG op): DROP_CONN, CRYPTO, ... */
		rv = c->reg->read_err;
		c->reg->read_err = 0;
		if (rv == NGTCP2_ERR_RETRY && c->state == ST_DONE)
			rv = NGTCP2_ERR_PROTO; /* only the handshake retries: the rule of the script's END */
		if (rv == NGTCP2_ERR_DRAINING)
			c->state = ST_DRAINING;
	} else
		rv = run_script(c, &r, ts);
	if (rv == NGTCP2_ERR_DROP_CONN)
		c->dropped = true;
	return rv;
}

/* ── writing ─────────────────────────────────────────────────────────── */
ngtcp2_ssize ngtcp2_conn_write_aggregate_pkt2_versioned(ngtcp2_conn *c, ngtcp2_path *path, int piv,
                                                        ngtcp2_pkt_info *pi, uint8_t *buf,
                                                        size_t buflen, size_t *pgsolen,
                                                        ngtcp2_write_pkt write_pkt,
                                                        size_t num_pkts, ngtcp2_tstamp ts)
{
	/* ⭐ the loop of ngtcp2 v1.25 `ngtcp2_conn_write_aggregate_pkt2_versioned`, as it is */
	size_t max_udp = c->reg->max_udp ? 1452 : 1200, path_max = 1200;
	uint8_t *wbuf = buf;
	ngtcp2_ssize nwrite;
	ngtcp2_pkt_info pi_discard;
	ngtcp2_path_storage path_discard;
	(void)piv;
	live(c, true, __func__);
	rxq_expect.valid = false;
	if (c->dropped)
		DIE("write_aggregate_pkt2 on connection #%td after DROP_CONN: nothing may be sent to that peer",
		    c->reg - rxq_conns);
	if (c->state == ST_CLOSING || c->state == ST_DRAINING)
		return 0;
	if (buflen < path_max)
		DIE("write_aggregate_pkt2 with a buffer of %zu bytes (ngtcp2 asserts ≥ %zu)", buflen,
		    path_max);
	if (c->reg->write_err) {
		int e = c->reg->write_err;
		c->reg->write_err = 0;
		return e;
	}
	/* ⛔ THE PACING ORACLE: one burst is at most the send quantum — or one full-size
	 *    packet, the floor ngtcp2's own assert imposes */
	if (buflen > c->reg->quantum && buflen > max_udp)
		DIE("a burst of up to %zu bytes offered to write_aggregate_pkt2, beyond the send "
		    "quantum of %zu (pacing: ngtcp2 does not clamp it with num_pkts = 0)",
		    buflen, c->reg->quantum);
	/* ngtcp2 `conn_pacing_pkt_tx_allowed()`: before the tx time no new data (played: nothing) */
	if (c->pace_next != UINT64_MAX) {
		if (c->pace_next > ts)
			return 0;
		c->pace_next = UINT64_MAX;
	}
	if (num_pkts == 0)
		num_pkts = SIZE_MAX;
	for (;;) {
		size_t wbuflen = buflen >= max_udp ? max_udp : path_max;
		bool first;
		c->in_cb++;
		nwrite = write_pkt(c, path, pi, wbuf, wbuflen, ts, c->user_data);
		c->in_cb--;
		if (nwrite < 0)
			break;
		if (nwrite == 0) {
			nwrite = wbuf - buf;
			break;
		}
		if ((size_t)nwrite > wbuflen)
			DIE("write_pkt returned %zd for a buffer of %zu", nwrite, wbuflen);
		first = buf == wbuf;
		wbuf += nwrite;
		buflen -= (size_t)nwrite;
		--num_pkts;
		if (first) {
			*pgsolen = (size_t)nwrite;
			if ((size_t)nwrite != path_max || buflen < path_max || num_pkts == 0) {
				nwrite = wbuf - buf;
				break;
			}
			if (path) {
				ngtcp2_path_storage_zero(&path_discard);
				path = &path_discard.path;
			}
			if (pi)
				pi = &pi_discard;
			continue;
		}
		if (buflen < path_max || (size_t)nwrite < *pgsolen || num_pkts == 0) {
			nwrite = wbuf - buf;
			break;
		}
	}
	if (nwrite <= 0)
		rxq_expect.valid = false;
	else
		c->pace_bytes += (size_t)nwrite;
	return nwrite;
}

/* What `wt_write()` calls to put a packet together: here, stream -1 (only control frames —
 * the played `wt` has no stream data). */
ngtcp2_ssize ngtcp2_conn_writev_stream_versioned(ngtcp2_conn *c, ngtcp2_path *path, int piv,
                                                 ngtcp2_pkt_info *pi, uint8_t *dest,
                                                 size_t destlen, ngtcp2_ssize *pdatalen,
                                                 uint32_t flags, int64_t id,
                                                 const ngtcp2_vec *v, size_t vn,
                                                 ngtcp2_tstamp ts)
{
	size_t n = c->reg->wt_pkt_len;
	(void)piv; (void)flags; (void)id; (void)v; (void)vn; (void)ts;
	live(c, false, __func__);
	if (!c->in_cb)
		DIE("writev_stream outside write_pkt: wt_write() was called by someone else");
	if (pdatalen)
		*pdatalen = -1;
	if (n > destlen)
		n = destlen;
	if (n < 21)
		n = 21;
	if (n > destlen)
		return 0;
	memset(dest, 0x40, n); /* ⭐ the whole of it: a dest/destlen that lie are ASan's */
	if (pi)
		memset(pi, 0, sizeof *pi);
	/* the path this packet is for (the later packets of an aggregate get a placeholder) */
	path_out(c, write_path(c), path, "write_aggregate_pkt2");
	return (ngtcp2_ssize)n;
}

ngtcp2_ssize ngtcp2_conn_write_connection_close_versioned(ngtcp2_conn *c, ngtcp2_path *path,
                                                          int piv, ngtcp2_pkt_info *pi,
                                                          uint8_t *dest, size_t destlen,
                                                          const ngtcp2_ccerr *ccerr,
                                                          ngtcp2_tstamp ts)
{
	size_t n = 48;
	(void)piv;
	live(c, true, __func__);
	rxq_expect.valid = false;
	if (c->dropped)
		DIE("write_connection_close on connection #%td after DROP_CONN: the answer to a packet ngtcp2 "
		    "judged not worth one is a reflection for whoever forges the source address", c->reg - rxq_conns);
	if (c->expiry_rv)
		c->closes_after_exp++;
	/* ⭐ an H3 code a callback wrote into last_error is never overwritten by the close that follows the
	 *    failure (the deliberate CONNECTION_REFUSED of the caps is another decision, not a failure's close) */
	if (c->h3_set && !(ccerr->type == NGTCP2_CCERR_TYPE_TRANSPORT && ccerr->error_code == NGTCP2_CONNECTION_REFUSED) &&
	    (ccerr->type != NGTCP2_CCERR_TYPE_APPLICATION || ccerr->error_code != c->h3_code))
		DIE("connection #%td: last_error held the H3 code %#llx written by a callback, the CONNECTION_CLOSE "
		    "carries type %d code %#llx", c->reg - rxq_conns, (unsigned long long)c->h3_code, (int)ccerr->type,
		    (unsigned long long)ccerr->error_code);
	if (ccerr->type == NGTCP2_CCERR_TYPE_TRANSPORT &&
	    ccerr->error_code == NGTCP2_CONNECTION_REFUSED) {
		/* the two closes of the caps, told apart by the reason transport.c writes */
		uint8_t st = c->reg->wt_state % RXQ_ST_N;
		bool after_credentials = st == RXQ_ST_ATTACH || st == RXQ_ST_ACTIVE ||
		                         st == RXQ_ST_DETACHED;
		if (ccerr->reasonlen >= 11 && memcmp(ccerr->reason, "server full", 11) == 0) {
			/* ⭐ never a logged-in or wait-verdict connection (the box on
			 *    MAX_CONNECTIONS), however the newcomers came */
			if (c->reg->logged_in || after_credentials || st == RXQ_ST_VERDICT)
				DIE("connection #%td EVICTED %s (%s)", c->reg - rxq_conns,
				    c->reg->logged_in ? "after it logged in" : "after its credentials",
				    RXQ_STATE_NAMES[st]);
			c->reg->evicted++;
		} else if (ccerr->reasonlen >= 13 && memcmp(ccerr->reason, "not logged in", 13) == 0) {
			/* ⭐ the age closes only a connection not logged in */
			if (c->reg->logged_in || after_credentials)
				DIE("connection #%td closed for its AGE %s (%s)", c->reg - rxq_conns,
				    c->reg->logged_in ? "after it logged in" : "in a logged-in state",
				    RXQ_STATE_NAMES[st]);
			c->reg->aged++;
			c->reg->aged_ns = ts;
		} else if (ccerr->reasonlen >= 21 &&
		           memcmp(ccerr->reason, "too many path changes", 21) == 0) {
			/* ⭐ the third close of transport.c (4f52eab8, PRELOGIN_MOVES_MAX in
			 *    transport_expired()): only for a connection not logged in.  Until 15 Oct
			 *    2026 this oracle did not know it and called it «a reason the caps do not
			 *    write» (fuzz lane, a harness false alarm) */
			/* ⚠ judged on the harness's own record, not on what transport.c says
			 *   (review of cda1636d): logged in or past its credentials never, and
			 *   only past RXQ_MOVES_MAX changes played before the login */
			if (c->reg->logged_in || after_credentials)
				DIE("connection #%td closed for its PATH CHANGES %s (%s)",
				    c->reg - rxq_conns,
				    c->reg->logged_in ? "after it logged in" : "in a logged-in state",
				    RXQ_STATE_NAMES[st]);
			if (c->reg->path_changes <= RXQ_MOVES_MAX)
				DIE("connection #%td closed for its PATH CHANGES after only %u (more than "
				    "%d needed)", c->reg - rxq_conns, c->reg->path_changes, RXQ_MOVES_MAX);
		} else
			DIE("a CONNECTION_REFUSED close with a reason the caps do not write");
	}
	if (c->state == ST_CLOSING || c->state == ST_DRAINING)
		return NGTCP2_ERR_INVALID_STATE;
	if (c->reg->close_err) {
		int e = c->reg->close_err;
		c->reg->close_err = 0;
		return e;
	}
	switch (ccerr->type) {
	case NGTCP2_CCERR_TYPE_TRANSPORT:
	case NGTCP2_CCERR_TYPE_APPLICATION:
		break;
	default:
		return 0; /* VERSION_NEGOTIATION, IDLE_CLOSE, DROP_CONN, RETRY: nothing to send */
	}
	if (ccerr->reasonlen && !ccerr->reason)
		DIE("a ccerr with a reason length and no reason");
	if (destlen < n)
		return NGTCP2_ERR_NOBUF;
	memset(dest, 0x41, n);
	if (pi)
		memset(pi, 0, sizeof *pi);
	path_out(c, c->cur, path, "write_connection_close");
	c->state = ST_CLOSING;
	return (ngtcp2_ssize)n;
}

/* ── timers ──────────────────────────────────────────────────────────── */
static uint64_t idle_expiry(const ngtcp2_conn *c)
{
	return c->idle_ts + c->params.max_idle_timeout;
}

/* ⭐ what transport.c reads to know a packet was DECRYPTED (§5.3, 14 Oct 2026): `pkt_recv`
 *    counts only the packets not discarded, as in ngtcp2 (`cstat.pkt_recv`) */
void ngtcp2_conn_get_conn_info2_versioned(const ngtcp2_conn *c, int v, ngtcp2_conn_info *ci)
{
	(void)v;
	live(c, false, __func__);
	memset(ci, 0, sizeof *ci);
	ci->pkt_recv = c->pkt_recv;
}

ngtcp2_tstamp ngtcp2_conn_get_expiry2(const ngtcp2_conn *c)
{
	uint64_t e;
	live(c, false, __func__);
	if (c->pace_bytes)
		DIE("the timer read with %zu bytes written and the pacing time NOT updated "
		    "(update_pkt_tx_time must follow the writes)", c->pace_bytes);
	e = idle_expiry(c);
	if (c->pace_next < e)
		e = c->pace_next;
	if (c->loss_at < e)
		e = c->loss_at;
	for (size_t i = 0; i < c->nscid; i++)
		if (c->scid_st[i] == 1 && c->scid_retire_at[i] < e)
			e = c->scid_retire_at[i];
	return e;
}

static int handle_expiry_body(ngtcp2_conn *c, ngtcp2_tstamp ts);
int ngtcp2_conn_handle_expiry(ngtcp2_conn *c, ngtcp2_tstamp ts)
{
	int rv;
	live(c, true, __func__);
	if (c->dropped)
		DIE("handle_expiry on connection #%td after DROP_CONN", c->reg - rxq_conns);
	rv = handle_expiry_body(c, ts);
	if (rv) {
		c->expiry_rv = rv;
		c->closes_after_exp = 0;
	}
	return rv;
}
static int handle_expiry_body(ngtcp2_conn *c, ngtcp2_tstamp ts)
{
	if (c->reg->loss_ms && c->loss_at == UINT64_MAX)
		c->loss_at = ts + c->reg->loss_ms * NGTCP2_MILLISECONDS;
	if (c->reg->expiry_err) {
		int e = c->reg->expiry_err;
		c->reg->expiry_err = 0;
		return e;
	}
	if (idle_expiry(c) <= ts)
		return NGTCP2_ERR_IDLE_CLOSE;
	if (c->pace_next <= ts) /* `conn_cancel_expired_pkt_tx_timer()` */
		c->pace_next = UINT64_MAX;
	for (size_t i = 0; i < c->nscid; i++)
		if (c->scid_st[i] == 1 && c->scid_retire_at[i] <= ts) {
			c->scid_st[i] = 2;
			if (c->cb.remove_connection_id &&
			    CALL(c, c->cb.remove_connection_id(c, &c->scid[i], c->user_data)) != 0)
				return NGTCP2_ERR_CALLBACK_FAILURE;
		}
	if (c->loss_at <= ts) {
		c->loss_at = UINT64_MAX;
		c->reg->loss_ms = 0;
		if (c->state == ST_DONE && c->cb.lost_datagram &&
		    CALL(c, c->cb.lost_datagram(c, c->reg->lost_dgram, c->user_data)) != 0)
			return NGTCP2_ERR_CALLBACK_FAILURE;
	}
	return 0;
}

/* ── small things ────────────────────────────────────────────────────── */
void ngtcp2_path_storage_zero(ngtcp2_path_storage *ps)
{
	ps->path.local.addr = (ngtcp2_sockaddr *)&ps->local_addrbuf;
	ps->path.local.addrlen = 0;
	ps->path.remote.addr = (ngtcp2_sockaddr *)&ps->remote_addrbuf;
	ps->path.remote.addrlen = 0;
	ps->path.user_data = NULL;
}

void ngtcp2_ccerr_default(ngtcp2_ccerr *e)
{
	memset(e, 0, sizeof *e);
	e->type = NGTCP2_CCERR_TYPE_TRANSPORT;
	e->error_code = NGTCP2_NO_ERROR;
}

void ngtcp2_ccerr_set_liberr(ngtcp2_ccerr *e, int liberr, const uint8_t *reason, size_t n)
{
	memset(e, 0, sizeof *e);
	e->reason = reason;
	e->reasonlen = n;
	switch (liberr) {
	case NGTCP2_ERR_RECV_VERSION_NEGOTIATION:
		e->type = NGTCP2_CCERR_TYPE_VERSION_NEGOTIATION;
		return;
	case NGTCP2_ERR_IDLE_CLOSE:
		e->type = NGTCP2_CCERR_TYPE_IDLE_CLOSE;
		return;
	case NGTCP2_ERR_DROP_CONN:
		e->type = NGTCP2_CCERR_TYPE_DROP_CONN;
		return;
	case NGTCP2_ERR_RETRY:
		e->type = NGTCP2_CCERR_TYPE_RETRY;
		return;
	}
	e->type = NGTCP2_CCERR_TYPE_TRANSPORT;
	e->error_code = NGTCP2_PROTOCOL_VIOLATION;
}

void ngtcp2_ccerr_set_application_error(ngtcp2_ccerr *e, uint64_t code, const uint8_t *r, size_t n)
{
	memset(e, 0, sizeof *e);
	e->type = NGTCP2_CCERR_TYPE_APPLICATION;
	e->error_code = code;
	e->reason = r;
	e->reasonlen = n;
}

/* ⭐ audit ngtcp2 1.25: CRYPTO_ERROR + the TLS alert (as in ngtcp2), and the alert the connection holds
 *    (0 = none, as `ngtcp2_conn_get_tls_alert2` when nothing was set). */
void ngtcp2_ccerr_set_tls_alert(ngtcp2_ccerr *e, uint8_t alert, const uint8_t *r, size_t n)
{
	memset(e, 0, sizeof *e);
	e->type = NGTCP2_CCERR_TYPE_TRANSPORT;
	e->error_code = NGTCP2_CRYPTO_ERROR | alert;
	e->reason = r;
	e->reasonlen = n;
}

uint8_t ngtcp2_conn_get_tls_alert2(const ngtcp2_conn *c)
{
	return live(c, false, __func__)->reg->tls_alert;
}

void ngtcp2_ccerr_set_transport_error(ngtcp2_ccerr *e, uint64_t code, const uint8_t *r, size_t n)
{
	memset(e, 0, sizeof *e);
	e->type = NGTCP2_CCERR_TYPE_TRANSPORT;
	e->error_code = code;
	e->reason = r;
	e->reasonlen = n;
}

const char *ngtcp2_strerror(int e)
{
	static char buf[32];
	snprintf(buf, sizeof buf, "ngtcp2 error %d (played)", e);
	return buf;
}

/* ── packets with no connection (the `quic` target has the real ones) ─── */
int ngtcp2_pkt_decode_version_cid(ngtcp2_version_cid *dest, const uint8_t *data, size_t datalen,
                                  size_t short_dcidlen)
{
	memset(dest, 0, sizeof *dest);
	if (datalen == 0)
		return NGTCP2_ERR_INVALID_ARGUMENT;
	if (data[0] & 0x80) {
		size_t i = 5, dl, sl;
		uint32_t v;
		if (datalen < 7)
			return NGTCP2_ERR_INVALID_ARGUMENT;
		v = ((uint32_t)data[1] << 24) | ((uint32_t)data[2] << 16) | ((uint32_t)data[3] << 8) | data[4];
		dl = data[i++];
		if (i + dl + 1 > datalen)
			return NGTCP2_ERR_INVALID_ARGUMENT;
		dest->dcid = data + i;
		i += dl;
		sl = data[i++];
		if (i + sl > datalen)
			return NGTCP2_ERR_INVALID_ARGUMENT;
		dest->scid = data + i;
		dest->version = v;
		dest->dcidlen = dl;
		dest->scidlen = sl;
		if (v && v != NGTCP2_PROTO_VER_V1 && v != NGTCP2_PROTO_VER_V2) {
			if (datalen < NGTCP2_MAX_UDP_PAYLOAD_SIZE / 2) /* ngtcp2: ≥ 1200 bytes */
				return NGTCP2_ERR_INVALID_ARGUMENT;
			return NGTCP2_ERR_VERSION_NEGOTIATION;
		}
		if (dl > NGTCP2_MAX_CIDLEN || sl > NGTCP2_MAX_CIDLEN)
			return NGTCP2_ERR_INVALID_ARGUMENT;
		return 0;
	}
	if (datalen < 1 + short_dcidlen)
		return NGTCP2_ERR_INVALID_ARGUMENT;
	dest->dcid = data + 1;
	dest->dcidlen = short_dcidlen;
	return 0;
}

int ngtcp2_accept(ngtcp2_pkt_hd *hd, const uint8_t *pkt, size_t pktlen)
{
	ngtcp2_version_cid vc;
	size_t i;
	uint8_t type;
	memset(hd, 0, sizeof *hd);
	if (pktlen < 7 || !(pkt[0] & 0x80) || ngtcp2_pkt_decode_version_cid(&vc, pkt, pktlen, 0) != 0 ||
	    vc.version != NGTCP2_PROTO_VER_V1 || vc.dcidlen < 8)
		return NGTCP2_ERR_INVALID_ARGUMENT;
	type = (pkt[0] >> 4) & 3;
	if (type != 0 && type != 1)
		return NGTCP2_ERR_INVALID_ARGUMENT;
	hd->type = type == 0 ? NGTCP2_PKT_INITIAL : NGTCP2_PKT_0RTT;
	hd->version = vc.version;
	hd->dcid.datalen = vc.dcidlen;
	memcpy(hd->dcid.data, vc.dcid, vc.dcidlen);
	hd->scid.datalen = vc.scidlen;
	memcpy(hd->scid.data, vc.scid, vc.scidlen);
	i = (size_t)(vc.scid - pkt) + vc.scidlen;
	if (hd->type == NGTCP2_PKT_INITIAL) {
		if (i >= pktlen)
			return NGTCP2_ERR_INVALID_ARGUMENT;
		hd->tokenlen = pkt[i++]; /* a one-byte varint: the harness's tokens are short */
		if (hd->tokenlen > 63 || i + hd->tokenlen > pktlen)
			return NGTCP2_ERR_INVALID_ARGUMENT;
		hd->token = hd->tokenlen ? pkt + i : NULL;
	}
	return 0;
}

ngtcp2_ssize ngtcp2_pkt_write_version_negotiation(uint8_t *dest, size_t destlen,
                                                  uint8_t unused_random, const uint8_t *dcid,
                                                  size_t dcidlen, const uint8_t *scid,
                                                  size_t scidlen, const uint32_t *sv, size_t nsv)
{
	size_t n = 7 + dcidlen + scidlen + 4 * nsv;
	(void)unused_random; (void)dcid; (void)scid; (void)sv;
	rxq_expect.valid = false;
	if (destlen < n)
		return NGTCP2_ERR_NOBUF;
	memset(dest, 0x80, n);
	return (ngtcp2_ssize)n;
}

static uint64_t resets_second = UINT64_MAX;
static unsigned resets_in_second, resets_unverified_in_second;
static ngtcp2_cid last_token_cid;     /* the id of the last Stateless Reset token made: the Reset written next is for it */
static bool expect_signed_reset, signed_reset_seen;

/* ── cid.h, played ────────────────────────────────────────────────────────────────────────────────────────────────────
 * The product's cid.c (HMAC-SHA256 over OpenSSL) is not linked here: the harness plays it with a keyed mix, so that
 * the fuzzer can know what an id that verifies is.  ⚠ `rxq_cid_signed()` is the ORACLE's own reading — it reads the bytes, not
 * the product's `cidkey_ok()`; the two agree by construction of the played mix, what is checked is the product's USE of the
 * API: that it makes the ids it gives out with `cidkey_make` and spends the Reset budgets by what `cidkey_ok` says. */
struct cidkey {
	uint64_t k;
};
static uint64_t cid_key_seen;
static uint64_t cid_mix(uint64_t k, const uint8_t *nonce)
{
	uint64_t h = k ^ 0xcbf29ce484222325ull;
	for (int i = 0; i < 10; i++) {
		h ^= nonce[i];
		h *= 0x100000001b3ull;
		h ^= h >> 29;
	}
	return h;
}
cidkey *cidkey_new(const uint8_t *secret, size_t secretlen)
{
	cidkey *k = calloc(1, sizeof *k);
	if (!k || !secret || !secretlen) {
		free(k);
		return NULL;
	}
	k->k = 0x9e3779b97f4a7c15ull;
	for (size_t i = 0; i < secretlen; i++)
		k->k = (k->k ^ secret[i]) * 0x100000001b3ull;
	cid_key_seen = k->k;
	return k;
}
void cidkey_free(cidkey *k) { free(k); }
unsigned cidkey_errors(const cidkey *k) { (void)k; return 0; } /* the played MAC does not fail; the line is the unit test's (cid-firmati) */
bool cidkey_make(cidkey *k, uint8_t cid[18])
{
	uint64_t h;
	if (!k || !rxq_rand(cid, 10))
		return false;
	h = cid_mix(k->k, cid);
	memcpy(cid + 10, &h, 8);
	return true;
}
bool cidkey_ok(cidkey *k, const uint8_t *cid, size_t len)
{
	uint64_t h;
	if (!k || len != 18)
		return false;
	h = cid_mix(k->k, cid);
	return memcmp(cid + 10, &h, 8) == 0;
}
bool rxq_cid_signed(const uint8_t *cid, size_t len)
{
	uint64_t h;
	if (len != 18 || !cid_key_seen)
		return false;
	h = cid_mix(cid_key_seen, cid);
	return memcmp(cid + 10, &h, 8) == 0;
}
void rxq_cid_make(uint8_t out[18])
{
	uint64_t h;
	(void)rxq_rand(out, 10);
	h = cid_mix(cid_key_seen, out);
	memcpy(out + 10, &h, 8);
}
unsigned rxq_resets_signed_now(void)
{
	return rxq_now_ns / NGTCP2_SECONDS == resets_second ? resets_in_second : 0;
}
void rxq_expect_signed_reset(bool on)
{
	expect_signed_reset = on;
	signed_reset_seen = false;
}
bool rxq_signed_reset_seen(void) { return signed_reset_seen; }

ngtcp2_ssize ngtcp2_pkt_write_stateless_reset2(uint8_t *dest, size_t destlen,
                                               const ngtcp2_stateless_reset_token *token,
                                               const uint8_t *rand, size_t randlen)
{
	(void)token; (void)rand;
	rxq_expect.valid = false;
	/* ⭐ THE RESET RATE: at most RXQ_RESETS_PER_SECOND in one second of the clock (each
	 *    reset written here is sent: `send_stateless_reset()` sends what it wrote) */
	if (rxq_now_ns / NGTCP2_SECONDS != resets_second) {
		resets_second = rxq_now_ns / NGTCP2_SECONDS;
		resets_in_second = 0;
		resets_unverified_in_second = 0;
	}
	/* ⭐ `cid-firmati`: the Reset written now is for the id of the token made just before it (the product makes the token,
	 *    then writes the packet); an id that verifies spends the 100, one that does not spends its own 10 */
	if (rxq_cid_signed(last_token_cid.data, last_token_cid.datalen)) {
		if (++resets_in_second > RXQ_RESETS_PER_SECOND)
			DIE("%u Stateless Resets for signed ids in the second %llu: the limit is %d", resets_in_second,
			    (unsigned long long)resets_second, RXQ_RESETS_PER_SECOND);
		signed_reset_seen = true;
	} else if (++resets_unverified_in_second > RXQ_RESETS_UNVERIFIED_PER_SECOND) {
		DIE("%u Stateless Resets for ids that do not verify in the second %llu: the limit is %d",
		    resets_unverified_in_second, (unsigned long long)resets_second, RXQ_RESETS_UNVERIFIED_PER_SECOND);
	}
	if (randlen < NGTCP2_MIN_STATELESS_RESET_RANDLEN)
		return NGTCP2_ERR_INVALID_ARGUMENT;
	if (destlen < randlen + NGTCP2_STATELESS_RESET_TOKENLEN)
		return NGTCP2_ERR_NOBUF;
	memset(dest, 0x40, randlen + NGTCP2_STATELESS_RESET_TOKENLEN);
	return (ngtcp2_ssize)(randlen + NGTCP2_STATELESS_RESET_TOKENLEN);
}

/* ── ngtcp2_crypto ───────────────────────────────────────────────────── */
int ngtcp2_crypto_generate_stateless_reset_token(uint8_t *token, const uint8_t *secret,
                                                 size_t secretlen, const ngtcp2_cid *cid)
{
	if (rxq_fail_next == RXQ_FAIL_RESET_TOKEN) {
		rxq_fail_next = 0;
		return -1;
	}
	last_token_cid = *cid;
	for (size_t i = 0; i < NGTCP2_STATELESS_RESET_TOKENLEN; i++)
		token[i] = (uint8_t)(secret[i % secretlen] ^ (i < cid->datalen ? cid->data[i] : 0));
	return 0;
}

/* The played token: magic 0xB7, then the verdict byte (`RXQ_TOKEN_*`) and the odcid. */
ngtcp2_ssize ngtcp2_crypto_generate_retry_token2(uint8_t *token, const uint8_t *secret,
                                                 size_t secretlen, uint32_t version,
                                                 const ngtcp2_sockaddr *ra, ngtcp2_socklen rl,
                                                 const ngtcp2_cid *rscid, const ngtcp2_cid *odcid,
                                                 ngtcp2_tstamp ts)
{
	(void)secret; (void)secretlen; (void)version; (void)ra; (void)rl; (void)rscid; (void)ts;
	token[0] = NGTCP2_CRYPTO_TOKEN_MAGIC_RETRY2;
	token[1] = RXQ_TOKEN_GOOD;
	token[2] = (uint8_t)odcid->datalen;
	memcpy(token + 3, odcid->data, odcid->datalen);
	return (ngtcp2_ssize)(3 + odcid->datalen);
}

int ngtcp2_crypto_verify_retry_token2(ngtcp2_cid *odcid, const uint8_t *token, size_t tokenlen,
                                      const uint8_t *secret, size_t secretlen, uint32_t version,
                                      const ngtcp2_sockaddr *ra, ngtcp2_socklen rl,
                                      const ngtcp2_cid *dcid, ngtcp2_duration timeout,
                                      ngtcp2_tstamp ts)
{
	(void)secret; (void)secretlen; (void)version; (void)dcid; (void)timeout; (void)ts;
	{
		volatile uint8_t x = 0; /* it reads the remote address it is given */
		for (ngtcp2_socklen i = 0; i < rl; i++)
			x ^= ((const uint8_t *)ra)[i];
		(void)x;
	}
	if (tokenlen < 3 || token[0] != NGTCP2_CRYPTO_TOKEN_MAGIC_RETRY2 ||
	    token[2] > NGTCP2_MAX_CIDLEN || 3u + token[2] > tokenlen ||
	    token[1] % RXQ_TOKEN_N == RXQ_TOKEN_UNREADABLE)
		return NGTCP2_CRYPTO_ERR_UNREADABLE_TOKEN;
	if (token[1] % RXQ_TOKEN_N == RXQ_TOKEN_STALE)
		return NGTCP2_CRYPTO_ERR_VERIFY_TOKEN;
	odcid->datalen = token[2];
	memcpy(odcid->data, token + 3, token[2]);
	token_seen_len = tokenlen < sizeof token_seen ? tokenlen : sizeof token_seen;
	memcpy(token_seen, token, token_seen_len);
	return 0;
}

ngtcp2_ssize ngtcp2_crypto_write_retry(uint8_t *dest, size_t destlen, uint32_t version,
                                       const ngtcp2_cid *dcid, const ngtcp2_cid *scid,
                                       const ngtcp2_cid *odcid, const uint8_t *token,
                                       size_t tokenlen)
{
	size_t n = 7 + dcid->datalen + scid->datalen + tokenlen + 16;
	(void)version; (void)odcid; (void)token;
	/* ⭐ `cid-firmati`: the id our Retry gives the client (the one it will address the next Initial to) carries its tag */
	if (!rxq_cid_signed(scid->data, scid->datalen))
		DIE("the Retry gave the client an id that does not verify");
	rxq_expect.valid = false;
	rxq_retries++;
	if (destlen < n)
		return NGTCP2_ERR_NOBUF;
	memset(dest, 0xf0, n);
	return (ngtcp2_ssize)n;
}

ngtcp2_ssize ngtcp2_crypto_write_connection_close(uint8_t *dest, size_t destlen, uint32_t version,
                                                  const ngtcp2_cid *dcid, const ngtcp2_cid *scid,
                                                  uint64_t error_code, const uint8_t *reason,
                                                  size_t reasonlen)
{
	size_t n = 7 + dcid->datalen + scid->datalen + 24 + reasonlen;
	(void)version; (void)reason;
	rxq_expect.valid = false;
	rxq_last_close_code = error_code;
	if (destlen < n)
		return NGTCP2_ERR_NOBUF;
	memset(dest, 0xc0, n);
	return (ngtcp2_ssize)n;
}

int ngtcp2_crypto_ossl_init(void) { return 0; }

struct ngtcp2_crypto_ossl_ctx {
	SSL *ssl;
};
int ngtcp2_crypto_ossl_ctx_new(ngtcp2_crypto_ossl_ctx **pctx, SSL *ssl)
{
	if (rxq_fail_next == RXQ_FAIL_OSSL_CTX) {
		rxq_fail_next = 0;
		return NGTCP2_CRYPTO_ERR_NOMEM;
	}
	*pctx = calloc(1, sizeof **pctx);
	if (!*pctx)
		return NGTCP2_CRYPTO_ERR_NOMEM;
	(*pctx)->ssl = ssl;
	return 0;
}
void ngtcp2_crypto_ossl_ctx_del(ngtcp2_crypto_ossl_ctx *ctx) { free(ctx); }
void ngtcp2_crypto_ossl_ctx_set_ssl(ngtcp2_crypto_ossl_ctx *ctx, SSL *ssl) { ctx->ssl = ssl; }
int ngtcp2_crypto_ossl_configure_server_session(SSL *ssl)
{
	(void)ssl;
	if (rxq_fail_next == RXQ_FAIL_CONFIGURE) {
		rxq_fail_next = 0;
		return -1;
	}
	return 0;
}

/* The crypto callbacks `accept_conn()` registers: the played ngtcp2 does the handshake itself
 * and never calls them. */
#define NEVER(name, ret, ...)                                                                \
	ret name(__VA_ARGS__)                                                                \
	{                                                                                    \
		DIE(#name " called: the played ngtcp2 has no TLS");                          \
	}
NEVER(ngtcp2_crypto_recv_client_initial_cb, int, ngtcp2_conn *c, const ngtcp2_cid *d, void *u)
NEVER(ngtcp2_crypto_recv_crypto_data_cb, int, ngtcp2_conn *c, ngtcp2_encryption_level l,
      uint64_t o, const uint8_t *d, size_t n, void *u)
NEVER(ngtcp2_crypto_encrypt_cb, int, uint8_t *dest, const ngtcp2_crypto_aead *a,
      const ngtcp2_crypto_aead_ctx *ac, const uint8_t *p, size_t pl, const uint8_t *nc, size_t nl,
      const uint8_t *ad, size_t al)
NEVER(ngtcp2_crypto_decrypt_cb, int, uint8_t *dest, const ngtcp2_crypto_aead *a,
      const ngtcp2_crypto_aead_ctx *ac, const uint8_t *p, size_t pl, const uint8_t *nc, size_t nl,
      const uint8_t *ad, size_t al)
NEVER(ngtcp2_crypto_hp_mask_cb, int, uint8_t *dest, const ngtcp2_crypto_cipher *hp,
      const ngtcp2_crypto_cipher_ctx *hc, const uint8_t *s)
NEVER(ngtcp2_crypto_update_key_cb, int, ngtcp2_conn *c, uint8_t *rs, uint8_t *ts,
      ngtcp2_crypto_aead_ctx *ra, uint8_t *ri, ngtcp2_crypto_aead_ctx *ta, uint8_t *ti,
      const uint8_t *crs, const uint8_t *cts, size_t sl, void *u)
NEVER(ngtcp2_crypto_version_negotiation_cb, int, ngtcp2_conn *c, uint32_t v,
      const ngtcp2_cid *cid, void *u)
NEVER(ngtcp2_crypto_get_path_challenge_data2_cb, int, ngtcp2_conn *c,
      ngtcp2_path_challenge_data *d, void *u)
void ngtcp2_crypto_delete_crypto_aead_ctx_cb(ngtcp2_conn *c, ngtcp2_crypto_aead_ctx *a, void *u)
{
	DIE("delete_crypto_aead_ctx_cb called: the played ngtcp2 has no TLS");
}
void ngtcp2_crypto_delete_crypto_cipher_ctx_cb(ngtcp2_conn *c, ngtcp2_crypto_cipher_ctx *a, void *u)
{
	DIE("delete_crypto_cipher_ctx_cb called: the played ngtcp2 has no TLS");
}

/* ── the WebTransport layer, played ────────────────────────────────────
 * ⚠ `webtransport.c` is the `wt` / `wt-session` targets' (the real one, with nghttp3): here it
 *   is a stand-in whose answers the fuzzer chooses — 0 or `NGTCP2_ERR_CALLBACK_FAILURE`, as
 *   `webtransport.h` documents («0 or an ngtcp2 error (negative) to propagate»).
 * ⭐ It is heap memory and it touches its connection on every call: a `wt` used after
 *   `wt_free()`, or one whose `ngtcp2_conn` was deleted first, is ASan's to see. */
struct wt {
	uint32_t magic;
	ngtcp2_conn *conn;
	ngtcp2_ccerr *last_error;
	char *provenance;
	rxq_reg *reg;
	uint64_t last_life;
};
#define WT_MAGIC 0x77744c49u

static wt *W(wt *w, const char *fn, bool from_callback)
{
	if (!w || w->magic != WT_MAGIC)
		DIE("%s on something that is not a wt", fn);
	live(w->conn, false, fn); /* its connection must still exist */
	if (from_callback && !w->conn->in_cb)
		DIE("%s called outside the callbacks of its own connection", fn);
	return w;
}
static int answer(wt *w, int bit)
{
	if (!((w->reg->wt_fail >> bit) & 1))
		return 0;
	/* ⭐ as webtransport.c does before a CALLBACK_FAILURE: an H3 code into last_error (if none yet),
	 *    when bit 8 of the mask asks for it; the oracle in write_connection_close keeps it honest */
	if ((w->reg->wt_fail >> 8) & 1 && w->last_error->error_code == 0) {
		ngtcp2_ccerr_set_application_error(w->last_error, 0x0100u + 0x10u + (unsigned)bit,
		                                   (const uint8_t *)"cb", 2);
		w->conn->h3_set = true;
		w->conn->h3_code = w->last_error->error_code;
	}
	return NGTCP2_ERR_CALLBACK_FAILURE;
}

wt *wt_new(ngtcp2_conn *conn, ngtcp2_ccerr *last_error, const char *provenance, helper *help)
{
	wt *w;
	(void)help;
	if (rxq_fail_next == RXQ_FAIL_WT_NEW) {
		rxq_fail_next = 0;
		return NULL;
	}
	live(conn, true, __func__);
	w = calloc(1, sizeof *w);
	if (!w)
		return NULL;
	w->magic = WT_MAGIC;
	w->conn = conn;
	w->last_error = last_error;
	w->provenance = strdup(provenance); /* ⭐ it must be a terminated string */
	w->reg = conn->reg;
	w->reg->wt_born = true;
	if (rxq_on_birth)
		rxq_on_birth(token_seen, token_seen_len);
	return w;
}
/* ⭐ the oracle of 15 Oct 2026 counts these (see PATH RESULT in `run_script()`) */
void wt_moved(wt *w, const char *provenance)
{
	W(w, __func__, true);
	if (!provenance || !provenance[0])
		DIE("wt_moved with no address");
	free(w->provenance);
	w->provenance = strdup(provenance);
	w->conn->moves_seen++;
}
void wt_free(wt *w)
{
	W(w, __func__, false);
	if (w->conn->in_cb)
		DIE("wt_free from inside a callback of its connection");
	w->magic = 0;
	free(w->provenance);
	free(w);
}
int wt_app_ready(wt *w) { return answer(W(w, __func__, true), 7); }
int wt_receive_stream(wt *w, uint32_t flags, int64_t id, const uint8_t *data, size_t len)
{
	volatile uint8_t x = 0;
	(void)flags; (void)id;
	W(w, __func__, true);
	for (size_t i = 0; i < len; i++)
		x ^= data[i];
	(void)x;
	return answer(w, 0);
}
int wt_ack_stream_data(wt *w, int64_t id, uint64_t len) { (void)id; (void)len; return answer(W(w, __func__, true), 1); }
int wt_stream_closed(wt *w, int64_t id, uint64_t code, bool with_code)
{
	(void)id; (void)code; (void)with_code;
	return answer(W(w, __func__, true), 2);
}
int wt_stream_reset(wt *w, int64_t id) { (void)id; return answer(W(w, __func__, true), 3); }
int wt_stream_stop_sending(wt *w, int64_t id) { (void)id; return answer(W(w, __func__, true), 4); }
int wt_extend_max_streams_bidi(wt *w, uint64_t n) { (void)n; return answer(W(w, __func__, true), 5); }
int wt_extend_max_stream_data(wt *w, int64_t id) { (void)id; return answer(W(w, __func__, true), 6); }
void wt_dgram_lost(wt *w, uint64_t id) { (void)id; W(w, __func__, true); }
void wt_dgram_acked(wt *w, uint64_t id) { (void)id; W(w, __func__, true); }

ngtcp2_ssize wt_write(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi, uint8_t *dest, size_t destlen,
                      ngtcp2_tstamp ts)
{
	ngtcp2_ssize pdl;
	W(w, __func__, true);
	if (w->reg->wt_write_fail)
		return NGTCP2_ERR_CALLBACK_FAILURE;
	if (w->reg->wt_pkts == 0)
		return 0;
	w->reg->wt_pkts--;
	return ngtcp2_conn_writev_stream_versioned(w->conn, path, NGTCP2_PKT_INFO_VERSION, pi, dest,
	                                           destlen, &pdl, 0, -1, NULL, 0, ts);
}

ngtcp2_tstamp wt_heartbeat_ns(const wt *w)
{
	W((wt *)w, __func__, false);
	return w->reg->wt_beat_at;
}
void wt_beat(wt *w, ngtcp2_tstamp ts)
{
	W(w, __func__, false);
	w->reg->wt_beat_at = ts + 100 * NGTCP2_MILLISECONDS;
	if (w->reg->wt_pkts < 64)
		w->reg->wt_pkts++; /* a beat usually has something to say */
}
void wt_sign_of_life(wt *w, ngtcp2_tstamp ts)
{
	W(w, __func__, false);
	/* ⛔ §5.3: a sign of life only for a packet ngtcp2 DECRYPTED — `[R]` 14 Oct 2026, read_pkt
	 *    returns 0 also for the undecryptable, the duplicate, the unknown path in the handshake */
	if (!rxq_read_decrypted)
		DIE("wt_sign_of_life for a packet ngtcp2 did not decrypt (§5.3)");
	if (ts < w->last_life)
		DIE("wt_sign_of_life went back in time");
	w->last_life = ts;
}
bool wt_dead_line_fired(const wt *w)
{
	W((wt *)w, __func__, false);
	if (w->reg->wt_dead_line)
		/* webtransport.c writes H3_NO_ERROR with the reason into last_error */
		ngtcp2_ccerr_set_application_error(w->last_error, 0x100, (const uint8_t *)"dead line", 9);
	return w->reg->wt_dead_line;
}
bool wt_verdict(wt *w, uint64_t ticket, bool admitted, bool resumed)
{
	(void)resumed;
	W(w, __func__, false);
	if (w->reg->wt_ticket && w->reg->wt_ticket == ticket) {
		w->reg->wt_ticket = 0;
		if (admitted)
			w->reg->wt_state = RXQ_ST_ATTACH;
		w->reg->wt_pkts += 1;
		return true;
	}
	return false;
}
bool wt_verdict_as(wt *w, uint64_t ticket, bool admitted, bool resumed, const char *canonical) { (void)canonical; return wt_verdict(w, ticket, admitted, resumed); }
bool wt_verdict_lost(wt *w, uint64_t ticket) { return wt_verdict(w, ticket, false, false); }
/* transport.c counts a verdict whose connection is gone through rcp.c, which this harness does not link */
void rcp_orphan_verdict(const char *user, const char *rhost, bool admitted, bool lost, uint64_t ticket, uint64_t now_ms,
                        void (*fn)(void *, const char *), void *ctx)
{
	(void)user; (void)rhost; (void)admitted; (void)lost; (void)now_ms; (void)fn; (void)ctx;
}
void wt_dismiss(wt *w, uint8_t reason, const char *detail)
{
	(void)reason;
	W(w, __func__, false);
	(void)strlen(detail);
	w->reg->wt_pkts += 1;
	w->reg->wt_more_to_say = true;
}
bool wt_ha_da_dire(const wt *w) { return W((wt *)w, __func__, false)->reg->wt_more_to_say; }
/* the names `rcp_state_name()` gives (rcp.c's STATE_NAMES) */
/* `rcp_awaits_verdict()` played on the same ticket wt_verdict() takes */
bool wt_awaits_verdict(const wt *w, uint64_t ticket)
{
	W((wt *)w, __func__, false);
	return w->reg->wt_ticket && w->reg->wt_ticket == ticket;
}
/* `rcp_credentials_wait_from()`: the instant op_wt chose, in wait-credentials only */
uint64_t wt_credentials_wait_from(const wt *w)
{
	W((wt *)w, __func__, false);
	return w->reg->wt_state % RXQ_ST_N == RXQ_ST_CREDENTIALS ? w->reg->wt_cred_from_ms : 0;
}
const char *wt_rcp_state(const wt *w)
{
	return RXQ_STATE_NAMES[W((wt *)w, __func__, false)->reg->wt_state % RXQ_ST_N];
}
/* the pre-login log budget (webtransport.c): played as «always room» — transport.c
 * only asks it whether to write its «connection … closed» line */
bool wt_prelogin_may_log(wt *w, const char *provenance)
{
	(void)provenance;
	if (w)
		W(w, __func__, false);
	return true;
}
/* the pre-login lines counted for ALL addresses (webtransport.c, log-tetti R8): played as "nothing counted";
 * transport.c only asks when to wake up for their line, and flushes them */
uint64_t wt_prelogin_expiry_ms(void)
{
	return UINT64_MAX;
}
void wt_prelogin_flush(uint64_t now_ms)
{
	(void)now_ms;
}
const char *wt_pending_reason(const wt *w)
{
	W((wt *)w, __func__, false);
	return "queue not empty (played)";
}

void rxq_reset(void)
{
	memset(rxq_conns, 0, sizeof rxq_conns);
	rxq_nconns = 0;
	rxq_fail_next = 0;
	rxq_last_close_code = 0;
	rxq_retries = 0;
	token_seen_len = 0;
	resets_second = UINT64_MAX;
	resets_in_second = resets_unverified_in_second = 0;
	expect_signed_reset = signed_reset_seen = false;
	memset(&last_token_cid, 0, sizeof last_token_cid);
	memset(&rxq_expect, 0, sizeof rxq_expect);
	memset(&rxq_rx, 0, sizeof rxq_rx);
}
