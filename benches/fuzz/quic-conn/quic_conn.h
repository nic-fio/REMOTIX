/*
 * quic_conn.h — the played ngtcp2 of the `quic-conn` target (`stubs_quic.c`) and what the
 * harness (`fuzz_quic_conn.c`) steers in it.
 *
 * ⭐ Why a played ngtcp2 here (14 Oct 2026).  The `quic` target links the REAL ngtcp2 and
 *    reaches only `read_packet()` for a packet from an unknown address (16 % of
 *    `transport.c`): a Retry token is an AEAD under the server's secret and a handshake is
 *    TLS, so the fuzzer never gets a connection.  Everything `transport.c` does for an
 *    ESTABLISHED connection — the callbacks it registers, the CID table, the timers, the dead
 *    line, the teardown, the write loop, the migration of b207ad85 — was unfuzzed.
 *    ⇒ Here `transport.c` is the REAL file (`#include`d, unmodified) and ngtcp2 under it is
 *      played: the fuzzer decides what ngtcp2 "found" in a packet (which callbacks it invokes,
 *      with which stream ids, offsets, lengths, datagrams, CIDs) and what it returns.
 * ⛔ Only what ngtcp2 v1.25 documents or does (read in its source): a callback is invoked only
 *    from inside `read_pkt` / `write_*` / `handle_expiry`, never re-entered; a callback that
 *    fails makes the call return `NGTCP2_ERR_CALLBACK_FAILURE`; stream data only after the
 *    handshake (RFC 9001 §5.7), only on streams the peer may send on, at growing offsets, nothing
 *    after FIN; a stream is closed once; `remove_connection_id` only for a CID it issued and the
 *    peer retired, after a delay (`handle_expiry`); a packet that does not decrypt is dropped and
 *    `read_pkt` returns 0 (`conn_recv_cpkt`); a packet from a new path during the handshake is
 *    ignored (0); after it, a non-probing packet moves the current path (validation pending,
 *    the old one kept as fallback); packets are written only for paths ngtcp2 has seen, and
 *    all the packets of one `write_aggregate_pkt2` share one path; `DROP_CONN` and `RETRY`
 *    only during the handshake; `write_connection_close` writes nothing for a DROP_CONN /
 *    RETRY / IDLE_CLOSE error and refuses in the closing or draining state.
 *
 * ⭐ THE ORACLES (what ASan cannot see):
 *    · a packet `transport.c` sends must go to the address ngtcp2 wrote it for (§2.3, the fix of
 *      b207ad85) — `rxq_expect` below, checked in the harness's `sendmsg()`;
 *    · and it must leave FROM the path's local end (15 Oct 2026: IP_PKTINFO / IPV6_PKTINFO in
 *      `sendmsg`, v4-mapped on the IPv6 socket; nothing forced for the wildcard) — the local
 *      address ngtcp2 wrote it for, or, for an answer ngtcp2 did not write (Retry, reset,
 *      version negotiation), the address the datagram it answers arrived on;
 *    · the path `transport.c` gives ngtcp2 (`read_pkt`, `server_new`) has as local end the
 *      address the datagram arrived on (`rxq_rx`), not the one the connection was born on;
 *    · a callback reaches the `wt` of the SAME connection (the user_data of 10 Aug 2026);
 *    · no ngtcp2 call from inside one of its callbacks, no `ngtcp2_conn_del` / `wt_free` of a
 *      connection whose callback is running;
 *    · the `wt` is freed before its `ngtcp2_conn` (the stub `wt` touches its conn: ASan sees it);
 *    · a VALIDATED path to a new address tells the `wt` exactly once (`wt_moved()`, 15 Oct
 *      2026: the WebTransport layer's address follows the move), a failed one or one back to
 *      the same address never;
 *    · pacing (15 Oct 2026): a write offers ngtcp2 no more than the send quantum (or one
 *      full-size packet), and no timer is read while the pacing time is owed
 *      (`update_pkt_tx_time` after the writes, before `get_expiry2`);
 *    · the connection caps (15 Oct 2026, security review): after every op `how_many` is the
 *      length of the list and `unlogged` the number of connections flagged not logged in
 *      (a counter that went «negative» wraps and fails this), neither cap is exceeded while
 *      the caps were not lowered under the connections already open, and when every
 *      connection has been reaped both counters are 0;
 *    · the eviction: a connection closed with CONNECTION_REFUSED to make room is EXACTLY
 *      the one the rule names, computed apart in the harness — the oldest `finished`; else
 *      from the place (IPv4 address / IPv6 /48) with the most pending connections, the
 *      earliest state (no session, `wait-hello`, `wait-credentials`), the oldest; never
 *      `wait-verdict`, never logged in —, only when the server was full, at most one per
 *      newcomer, and only once the newcomer's connection EXISTS (an `accept_conn()` that
 *      fails closes nobody);
 *    · the age: after every op no connection is alive and not logged in `UNLOGGED_MAX_S`
 *      after its birth, and none was closed for its age before that;
 *    · a Retry token makes ONE connection: the same token again within
 *      `RETRY_TOKEN_TIMEOUT`, for no live connection, makes none and gets INVALID_TOKEN, never a
 *      second Retry;
 *    · the log: no more than 2 × BIRTH_LINES «new connection» event lines in any
 *      REFUSAL_LOG_S (the rest are counted in one line).
 *    · (15 Oct 2026, the ring of d0e56764) the harness keeps its OWN memory of the tokens that
 *      made a connection — the last 4096 births (`rxq_on_birth`), each good for 10 s — and
 *      judges by it: a token in it is refused (above); a token pushed out of it while still
 *      within its 10 s is «forgotten early», is NOT answered INVALID_TOKEN (it may make a
 *      second connection: refusing would answer every token with a Retry), and is counted:
 *      the «forgotten early» numbers of the summary lines plus the count not yet written are
 *      exactly the harness's count, and none is left unwritten once `transport_expired()`
 *      ran REFUSAL_LOG_S after the last line;
 *    · (15 Oct 2026, the source address) a link-local local end keeps its interface: the
 *      IPV6_PKTINFO a packet leaves with carries the ifindex the datagram arrived with
 *      (`rxq_same_host` compares the scope of fe80::/10); when the kernel refuses the forced
 *      source (EINVAL / EADDRNOTAVAIL), the SAME packet goes again to the same address without
 *      it, and the «kernel refused» line is written for the 1st-3rd refusal of the process and
 *      every 256th, never otherwise.
 *    · (15 Oct 2026, the gaps of the coverage run) checked AT THE CLOSE, in the stub's
 *      `write_connection_close`, whatever the op and however many NEWs share a read round:
 *      a connection closed «server full» (EVICTED) or «not logged in» (aged) was never
 *      logged in (`logged_in`, kept by the harness after every op) and is not in a state
 *      after the credentials (`wait-verdict` — eviction only —, `wait-attach`, `active`,
 *      `detached-by-silence`);
 *    · the Stateless Reset rate: never more than `RXQ_RESETS_PER_SECOND` resets written in
 *      one second of the clock (`ngtcp2_pkt_write_stateless_reset2`);
 *    · the wait: `transport_wait_ms()` never sleeps past the next age deadline of a live
 *      connection not logged in (`born_ns` + `UNLOGGED_MAX_S`, rounded up to the ms), and
 *      never answers «no timer» (-1) while there is one.
 */
#ifndef RXFUZZ_QUIC_CONN_H
#define RXFUZZ_QUIC_CONN_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>

#include <ngtcp2/ngtcp2.h>

#define RXQ_CONNS 16   /* connections remembered by the harness (alive or not) */
#define RXQ_CIDS 24    /* CIDs remembered per connection (issued, retired, removed) */
#define RXQ_PATHS 8    /* paths ngtcp2 has seen, per connection */
#define RXQ_STREAMS 64 /* streams open per connection */

/* ── the address the next packet must go to (the migration oracle) ── */
typedef struct {
	bool valid;
	struct sockaddr_storage to, from; /* from: the path's local end */
	socklen_t tolen, fromlen;
	const char *who; /* which ngtcp2 call wrote it */
} rxq_expectation;
extern rxq_expectation rxq_expect;

/* ── the local address the last datagram arrived on, as `transport_read()` must have read it
 *    (the PKTINFO address, or the socket's wildcard when there was none) ── */
typedef struct {
	bool valid;
	struct sockaddr_storage local;
	socklen_t locallen;
} rxq_received;
extern rxq_received rxq_rx;

/* The same HOST (family and address; the port does not travel in a PKTINFO). */
static inline bool rxq_same_host(const struct sockaddr *a, socklen_t al, const struct sockaddr *b,
                                 socklen_t bl)
{
	if (a->sa_family != b->sa_family)
		return false;
	if (a->sa_family == AF_INET && al >= (socklen_t)sizeof(struct sockaddr_in) &&
	    bl >= (socklen_t)sizeof(struct sockaddr_in))
		return ((const struct sockaddr_in *)a)->sin_addr.s_addr ==
		       ((const struct sockaddr_in *)b)->sin_addr.s_addr;
	if (a->sa_family == AF_INET6 && al >= (socklen_t)sizeof(struct sockaddr_in6) &&
	    bl >= (socklen_t)sizeof(struct sockaddr_in6)) {
		const struct sockaddr_in6 *x = (const struct sockaddr_in6 *)a,
		                          *y = (const struct sockaddr_in6 *)b;
		if (memcmp(&x->sin6_addr, &y->sin6_addr, 16) != 0)
			return false;
		/* ⭐ a link-local address is only that address ON its interface */
		return !IN6_IS_ADDR_LINKLOCAL(&x->sin6_addr) || x->sin6_scope_id == y->sin6_scope_id;
	}
	return false;
}

/* ── what the harness steers, per connection (kept in the registry, so it survives
 *    the connection: the harness may aim a packet at a dead one's CID) ── */
typedef struct {
	bool used, alive;
	struct ngtcp2_conn *conn; /* NULL once deleted */
	ngtcp2_cid cid[RXQ_CIDS]; /* [0] the client's dcid, then ours as ngtcp2 issued them */
	size_t ncid;
	/* the ngtcp2 knobs */
	uint8_t write_path;   /* 0 current · 1 the path being probed · 2 the fallback */
	int write_err;        /* write_aggregate_pkt2 fails with this (0 = no) */
	int close_err;        /* write_connection_close fails with this (0 = no) */
	int expiry_err;       /* handle_expiry fails with this (0 = no) */
	uint64_t loss_ms;     /* a loss-detection timer in this many ms (0 = none) */
	uint64_t lost_dgram;  /* the datagram declared lost when that timer fires */
	uint8_t max_udp;      /* 0: path MTU 1200 · 1: 1452 */
	size_t quantum;       /* `get_send_quantum2()` (ngtcp2 starts at 64 KB) */
	uint8_t pace_ns;      /* pacing: ns of wait per byte sent (0 = the tx time is «now») */
	/* the `wt` knobs (the WebTransport layer is played too: see `stubs_quic.c`) */
	uint16_t wt_fail;     /* bit per forwarded callback: answer CALLBACK_FAILURE */
	uint8_t wt_pkts;      /* packets `wt_write()` produces per write round */
	uint16_t wt_pkt_len;  /* their length (≤ destlen) */
	bool wt_write_fail;   /* `wt_write()` answers CALLBACK_FAILURE */
	uint64_t wt_beat_at;  /* `wt_heartbeat_ns()`, in ns (UINT64_MAX = never); a beat re-arms
	                         it 100 ms later */
	bool wt_dead_line, wt_more_to_say;
	uint64_t wt_ticket;   /* the PAM request this `wt` waits for (0 = none) */
	uint8_t wt_state;     /* what `wt_rcp_state()` answers: `RXQ_STATE_NAMES[wt_state]`
	                         (an admitted verdict makes it «wait-attach», as `rcp.c`
	                         would after its second) */
	bool logged_in;       /* transport.c counted it logged in (`!unlogged`) at the end of an
	                         op: sticky, the harness sets it (the eviction / age oracle) */
	struct sockaddr_storage born; /* the remote address it was born on (the caps' place) */
	socklen_t bornlen;
	unsigned evicted;     /* CONNECTION_CLOSEs with CONNECTION_REFUSED «server full…»: the
	                         caps' eviction */
	unsigned aged;        /* … with CONNECTION_REFUSED «not logged in…»: the age limit */
	uint64_t born_ns, aged_ns; /* `settings.initial_ts` at birth; the time of that close */
	unsigned path_changes; /* `path_validation` callbacks played while not logged in
	                          (`reg->logged_in` false): the move cap's oracle */
	uint64_t wt_cred_from_ms; /* what `wt_credentials_wait_from()` answers in
	                             wait-credentials (ms; 0 = none): op_wt sets it up to ~16 s
	                             back, so «parked after 10 s there» is reached */
	bool wt_born;         /* `wt_new()` succeeded: the last step of `accept_conn()` that
	                         can fail */
	/* counters, for the record (RXFUZZ_LOG) */
	uint64_t sign_of_life_after_discard;
} rxq_reg;

extern rxq_reg rxq_conns[RXQ_CONNS];
extern size_t rxq_nconns;

/* The harness's clock in ns (the product's `now_ns()` and ngtcp2's `ts` both read it). */
extern uint64_t rxq_now_ns;

/* Knobs of the accept path: the call that fails next (0 = none). */
enum {
	RXQ_FAIL_NONE,
	RXQ_FAIL_SERVER_NEW,
	RXQ_FAIL_OSSL_CTX,
	RXQ_FAIL_SSL_NEW,
	RXQ_FAIL_CONFIGURE,
	RXQ_FAIL_WT_NEW,
	RXQ_FAIL_RESET_TOKEN,
	RXQ_FAIL_RAND,
	RXQ_FAIL_N
};
extern int rxq_fail_next;

/* The error code of the last stateless `ngtcp2_crypto_write_connection_close()` (the
 * connection caps of 15 Oct 2026 answer CONNECTION_REFUSED with it). */
extern uint64_t rxq_last_close_code;
/* Retry packets written (`ngtcp2_crypto_write_retry()`), all along. */
extern unsigned rxq_retries;
/* ⭐ A connection is born (`wt_new()` succeeded: the last step of `accept_conn()` that can
 *    fail, after which `transport.c` keeps its token): the harness's hook gets the Retry token
 *    the played `verify_retry_token2` last accepted — the one of that Initial. */
extern void (*rxq_on_birth)(const uint8_t *token, size_t len);

/* The RCP states the played `wt_rcp_state()` answers (0 = no WebTransport session yet). */
/* The pre-login path-change cap of the discarded attempt's later commits (PRELOGIN_MOVES_MAX).  This branch's
 * transport.c has no such cap: nothing asserts it any more and the «too many path changes» branch of
 * stubs_quic.c is dead here. */
#define RXQ_MOVES_MAX 16

enum { RXQ_ST_NONE, RXQ_ST_HELLO, RXQ_ST_CREDENTIALS, RXQ_ST_VERDICT, RXQ_ST_ATTACH,
       RXQ_ST_ACTIVE, RXQ_ST_FINISHED, RXQ_ST_DETACHED, RXQ_ST_N };

/* The Stateless Reset rate the product promises (§11.9: 100 per second), written apart. */
#define RXQ_RESETS_PER_SECOND 100
extern const char *const RXQ_STATE_NAMES[RXQ_ST_N];

/* The Retry token the next Initial carries, as the played `verify_retry_token2` judges it. */
enum { RXQ_TOKEN_GOOD, RXQ_TOKEN_STALE, RXQ_TOKEN_UNREADABLE, RXQ_TOKEN_N };

void rxq_reset(void);              /* before every input */
void rxq_rng_seed(uint64_t seed);  /* the played RAND_bytes */
bool rxq_rand(uint8_t *d, size_t n);
rxq_reg *rxq_reg_of(const struct ngtcp2_conn *c);

#endif
