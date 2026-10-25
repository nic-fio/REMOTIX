/* RECOVERED from the 1.5-scartata tag (benches/runner/fuzz/harness/) on 24 Oct 2026 for the branch limiti-su-quic, and
 *    ADAPTED to its transport.c, which has the caps, the eviction, the 90 s age and the single-use Retry tokens (11.40) but
 *    NOT the later commits of the tag (the pre-login path-change cap, b207ad85 migration callbacks):
 *      - the eviction oracle follows pick_victim() of this branch (finished first; else the most crowded place, a PARKED
 *        connection before a fresh one, the earliest state, the oldest on a tie; the "parked" rule came back with c1624307);
 *      - the static assert on PRELOGIN_MOVES_MAX is gone; the "too many path changes" branch in stubs_quic.c is dead here;
 *      - wt_verdict() / transport_verdict() have the 4 arguments of this branch's webtransport.h / transport.h.
 *    Build and run: build.sh, run.sh in this folder (the image: ../Containerfile.fuzz). */
/*
 * fuzz_quic_conn.c — libFuzzer harness of `src/transport.c` on ESTABLISHED connections: the
 * ngtcp2 callbacks it registers (stream data, open/close/reset, STOP_SENDING, credit,
 * datagrams and their fate, CID issue/retire and the CID table, handshake completed, the
 * 1-RTT key), the per-connection timers and expiry, the §5.3 sign of life, the dead line, the
 * teardown (`reap_dead()` / `connection_free()`), the write loop (`write_connection()` /
 * `send_on()`), and `read_packet()` / `transport_read()` for a KNOWN connection — including
 * the migration of b207ad85: packets from another address, NAT rebinding, a probe.
 *
 * ⭐ `transport.c` is the REAL file, `#include`d and UNMODIFIED.  ngtcp2, ngtcp2_crypto, the
 *    four OpenSSL calls of `accept_conn()` and the WebTransport layer are PLAYED
 *    (`stubs_quic.c`, rules and oracles in `quic_conn.h`); the libc calls it makes on its
 *    socket and its clock (`recvmsg`, `sendmsg`, `getsockname`, `clock_gettime`, `RAND_bytes`)
 *    are renamed by `#define` before the `#include` — in this file only — and played here.
 *    ⇒ No handshake, no TLS: the fuzzer says what ngtcp2 found in each packet.
 * ⚠ The honest limits: what is fuzzed is `transport.c`'s use of ngtcp2 AS DOCUMENTED; a bug
 *   that needs ngtcp2 to do something the stub does not play is not found here; the real
 *   `webtransport.c` behind the callbacks is the `wt` / `wt-session` targets'; the startup
 *   (`transport_open()`, `transport_keep_secret()`) is not reached.
 *
 * Input: byte 0 = configuration (bit 0: the socket is IPv6 — remote addresses IPv6 and
 * v4-mapped; bits 1-7: the RNG seed), then an op stream (`common.h`):
 *
 *   op byte: kind = op & 0x1f · sel = op >> 5 (which connection, in order of birth)
 *    0 NEW      a client's Initial with a Retry token: a0 address, a1 dcid length (8 + a1 % 13),
 *               a2: token verdict (a2 % 3: good / stale / unreadable), bit 4 no token (→ Retry),
 *               bit 5 a token not ours, bit 6 the dcid of the previous NEW (a retransmission);
 *               bit 7 (with an op 14 before it) the dcid and token of a FLOOD birth again, the
 *               first (a1 even) or the last (a1 odd);
 *               a3 % 16: the accept step that fails (`RXQ_FAIL_*`, ≥ 8 none); a4 bit 0 hold,
 *               bits 1-2 the local address it arrives on (% 3; 2 = link-local on IPv6);
 *               the rest is what ngtcp2 finds in it (`stubs_quic.c`)
 *    1 PKT      a packet for connection `sel`: a0 address, a1 which of its CIDs (dead ones too),
 *               a2 bit 0 long header (Handshake), bit 1 hold, bits 2-3 the local address
 *               (% 3: 0 the first, 1 the other, 2 link-local on IPv6, ifindex 3);
 *               the rest is what ngtcp2 finds in it
 *    2 RAW      a0 address, the rest a datagram as it is
 *    3 TIME     u16 ms (× 256 if sel & 1); then `transport_wait_ms()` and `transport_expired()`
 *    4 WT       the played WebTransport of `sel`: a0-1 callback failure mask, a2 % 32 packets
 *               to write (a2 bit 5: in wait-verdict the refusal is OURS, made without PAM —
 *               [a2 bit 5 unused in this branch]), a3-4 their length, a5 bits: 0 wt_write fails · 1 dead line fires ·
 *               2 more to say · 3 heartbeat in a6 × 4 ms · 4 no heartbeat · 5-7 the RCP
 *               state `wt_rcp_state()` answers (`RXQ_STATE_NAMES`); a7-10 PAM ticket
 *    5 VERDICT  a0-3 ticket (sel & 1: the one `sel` waits for), a4 bit 0 admitted, bit 1 resumed
 *    6 DISMISS  a0 reason — `transport_dismiss_all()` and `transport_remain_reason()`
 *    7 WRITE    `transport_write()`
 *    8 SOCK     a0: sendmsg fails a0 & 7 times, errno (a0 >> 3) & 3: EAGAIN/EINTR/EPERM/ENOBUFS;
 *               a1 bit 0 recvmsg EINTR once, bit 1 recvmsg ENOMEM once; a2 bit 0 no PKTINFO,
 *               bit 1 getsockname fails; a3: the kernel refuses the forced source address of
 *               the next a3 & 7 sends that force one, errno EINVAL (bit 3) or EADDRNOTAVAIL
 *    9 NG       ngtcp2 of `sel`: a0 write path (current/probe/fallback), a1 write error, a2
 *               close error, a3 expiry error, a4 loss timer (ms × 4), a5 the datagram it loses,
 *               a6 bit 0 the 1452-byte MTU, a7 the send quantum (× 600 bytes, 0 = 64 KB),
 *               a8 pacing: ns of wait per byte sent
 *               a3 % 8 also the expiry error: none / NOMEM / CALLBACK_FAILURE / IDLE_CLOSE / HANDSHAKE_TIMEOUT / CRYPTO /
 *               PROTO / INTERNAL; a9 the TLS alert ngtcp2 holds (0 = none); a10 % 16 forces the return code of the NEXT
 *               decrypted read_pkt (DROP_CONN, CRYPTO, CALLBACK_FAILURE, HANDSHAKE_TIMEOUT, DRAINING, ... — 0 = the script);
 *               bit 8 of the WT op's callback mask (a0 bit 0): the failing callback first writes an H3 code in last_error.
 *               ORACLES (stubs_quic.c): nothing is read, written or expired for a connection after DROP_CONN; after a
 *               handle_expiry error exactly one CONNECTION_CLOSE (none after IDLE_CLOSE); an H3 code in last_error is
 *               the code of the CONNECTION_CLOSE that follows the failure.
 *   10 READ     `transport_read()` (delivers what was held)
 *   11 MISC     `transport_count()`, `transport_fd()`, `transport_wait_ms()`, `transport_context()`
 *   12 LIMITS   `transport_limits()` (and the handshake RATE: a4 bit 0 raises it to 1,000,000 a second everywhere, else the product's
 *               defaults of hsrate.h; every input starts at the defaults — the caps oracle below ignores the refusals
 *               for rate, told by `T->hs_refused_total`): a0 % 20 connections in all, a1 % 20 not logged in, a2 % 10
 *               of them per address, a3 % 10 per IPv6 /48 (0 = the default); every input starts
 *               at 6 / 5 / 3 / 4, so that the harness's 16 births reach every refusal and the
 *               eviction (IPv6: remotes 0-2 share a /48, 3 is v4-mapped)
 *   13 BURST    datagrams for no connection, each read alone: a0 how many (a0 + 1), a1 address,
 *               a2 ms of clock between two of them, a3 bit 0 the first RAND_bytes fails, bit 1
 *               long headers of a version not ours (1200 bytes: version negotiation) instead
 *               of short headers for an unknown dcid (Stateless Resets: the 100 per second),
 *               a4 extra length of the short ones (a4 % 64)
 *   14 FLOOD    Retry-validated Initials, each with its own token, each connection dying at once
 *               (DRAINING in its first packet) and its slot of the harness's table given back,
 *               one loop pass (wait, read, expired) each: a0-1 how many (+ 1; at most
 *               FLOOD_MAX births an input, all floods together), a2 × 10 µs of clock between two,
 *               a3 address — 4097 in < 10 s fill the ring of used tokens (TOKENS_KEPT) and push
 *               the first out early.  ⚠ This op RAISES THE HANDSHAKE RATE LIMITS (hsrate.h) to 1,000,000 a second, for the
 *               rest of the input (a LIMITS op with a4 bit 0 clear puts the defaults back): with the product's limits a
 *               single address cannot make 4097 births in 10 s, and the branch of the forgotten tokens would never be reached
 *
 * ⭐ (15 Oct 2026) after every `transport_wait_ms()` the age oracle of the wait
 *    (`wait_oracle()`); after every op the harness marks the connections transport.c counts
 *    logged in (`rxq_reg.logged_in`), which the stub's eviction / age oracle reads.
 */
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#include <ngtcp2/ngtcp2.h>
#include <ngtcp2/ngtcp2_crypto.h>
#include <ngtcp2/ngtcp2_crypto_ossl.h>
#include <openssl/rand.h>
#include <openssl/ssl.h>

#include "common.h"
#include "quic_conn.h"

/* ⭐ the renames: they reach `transport.c` only (its headers are already in) */
#define recvmsg rxq_recvmsg
#define sendmsg rxq_sendmsg
#define getsockname rxq_getsockname
#define clock_gettime rxq_clock_gettime
#define RAND_bytes rxq_RAND_bytes
#define SSL_new rxq_SSL_new
#define SSL_free rxq_SSL_free
#define SSL_set_ex_data rxq_SSL_set_ex_data
#define SSL_set_accept_state rxq_SSL_set_accept_state
static ssize_t rxq_recvmsg(int fd, struct msghdr *m, int flags);
static ssize_t rxq_sendmsg(int fd, const struct msghdr *m, int flags);
static int rxq_getsockname(int fd, struct sockaddr *sa, socklen_t *len);
static int rxq_clock_gettime(clockid_t id, struct timespec *ts);
static int rxq_RAND_bytes(unsigned char *d, int n);
static SSL *rxq_SSL_new(SSL_CTX *ctx);
static void rxq_SSL_free(SSL *s);
static int rxq_SSL_set_ex_data(SSL *s, int idx, void *arg);
static void rxq_SSL_set_accept_state(SSL *s);

/* ⛔ the grafted copy of the fault check is the same harness on another file */
#ifdef RXQ_TRANSPORT_C
#include RXQ_TRANSPORT_C
#else
#include "transport.c"
#endif

/* (limiti-su-quic: this branch has no pre-login migration cap — PRELOGIN_MOVES_MAX is of the discarded
 *  attempt's later commits — so the static assert that tied RXQ_MOVES_MAX to it is gone.) */

#undef recvmsg
#undef sendmsg
#undef getsockname
#undef clock_gettime
#undef RAND_bytes

#define DIE(...)                                                                             \
	do {                                                                                 \
		fprintf(stderr, "⛔ quic-conn ORACLE: " __VA_ARGS__);                       \
		fprintf(stderr, "\n");                                                       \
		abort();                                                                     \
	} while (0)

/* ── the addresses ────────────────────────────────────────────────────── */
static bool v6;
static struct sockaddr_storage REMOTE[4], LOCAL[3];
static socklen_t REMOTELEN[4], LOCALLEN[3];
/* ⭐ the interface each local address is on, as the kernel's PKTINFO says it (the product keeps
 *    it for the link-local one only: `pktinfo_cmsg()`) */
static const unsigned IFINDEX[3] = {2, 2, 3};

static void addresses(void)
{
	static const char *r4[4] = {"198.51.100.7", "198.51.100.7", "203.0.113.9", "198.51.100.8"};
	/* ⭐ [2] shares the /48 of [0] and not its /64: the per-/48 cap of 15 Oct 2026 */
	static const char *r6[4] = {"2001:db8::7", "2001:db8::7", "2001:db8:0:1::9", "::ffff:198.51.100.7"};
	static const uint16_t port[4] = {40000, 40001, 5555, 40000};
	static const char *l4[3] = {"192.168.0.2", "10.0.0.2", "169.254.7.1"};
	static const char *l6[3] = {"2001:db8::1", "::ffff:192.168.0.2", "fe80::1"};
	memset(REMOTE, 0, sizeof REMOTE);
	memset(LOCAL, 0, sizeof LOCAL);
	for (int i = 0; i < 4; i++) {
		if (v6) {
			struct sockaddr_in6 *s = (struct sockaddr_in6 *)&REMOTE[i];
			s->sin6_family = AF_INET6;
			s->sin6_port = htons(port[i]);
			inet_pton(AF_INET6, r6[i], &s->sin6_addr);
			REMOTELEN[i] = sizeof *s;
		} else {
			struct sockaddr_in *s = (struct sockaddr_in *)&REMOTE[i];
			s->sin_family = AF_INET;
			s->sin_port = htons(port[i]);
			inet_pton(AF_INET, r4[i], &s->sin_addr);
			REMOTELEN[i] = sizeof *s;
		}
	}
	for (int i = 0; i < 3; i++) {
		if (v6) {
			struct sockaddr_in6 *s = (struct sockaddr_in6 *)&LOCAL[i];
			s->sin6_family = AF_INET6;
			inet_pton(AF_INET6, l6[i], &s->sin6_addr);
			if (IN6_IS_ADDR_LINKLOCAL(&s->sin6_addr))
				s->sin6_scope_id = IFINDEX[i];
			LOCALLEN[i] = sizeof *s;
		} else {
			struct sockaddr_in *s = (struct sockaddr_in *)&LOCAL[i];
			s->sin_family = AF_INET;
			inet_pton(AF_INET, l4[i], &s->sin_addr);
			LOCALLEN[i] = sizeof *s;
		}
	}
}

/* ── the socket, played ──────────────────────────────────────────────── */
#define QMAX 96
#define QBYTES 2048
static struct {
	uint8_t d[QBYTES];
	size_t n;
	int remote, local;
} q[QMAX];
static size_t qhead, qtail;
static int send_fail_left, send_errno, recv_eintr, recv_err;
static bool no_pktinfo, gsn_fail;
/* the kernel refusing the forced source (op 8 a3): how many more, with which errno */
static int src_refuse_left, src_refuse_errno;

static void enqueue(const uint8_t *d, size_t n, int remote, int local)
{
	/* ⚠ (15 Oct 2026) the slots already read are given back: without it an input could
	 *   deliver only QMAX datagrams IN ALL, and 101 resets in one second were out of reach */
	if (qtail == QMAX && qhead > 0) {
		memmove(q, q + qhead, (qtail - qhead) * sizeof q[0]);
		qtail -= qhead;
		qhead = 0;
	}
	if (qtail == QMAX)
		return;
	if (n > QBYTES)
		n = QBYTES;
	memcpy(q[qtail].d, d, n);
	q[qtail].n = n;
	q[qtail].remote = remote;
	q[qtail].local = local;
	qtail++;
}

/* The socket's own address: bound to all of them, as the product's `--address` default. */
static void wildcard(struct sockaddr_storage *ss, socklen_t *len)
{
	memset(ss, 0, sizeof *ss);
	if (v6) {
		struct sockaddr_in6 *s = (struct sockaddr_in6 *)ss;
		s->sin6_family = AF_INET6;
		s->sin6_addr = in6addr_any;
		s->sin6_port = htons(7448);
		*len = sizeof *s;
	} else {
		struct sockaddr_in *s = (struct sockaddr_in *)ss;
		s->sin_family = AF_INET;
		s->sin_addr.s_addr = htonl(INADDR_ANY);
		s->sin_port = htons(7448);
		*len = sizeof *s;
	}
}

static ssize_t rxq_recvmsg(int fd, struct msghdr *m, int flags)
{
	(void)fd; (void)flags;
	if (recv_eintr) {
		recv_eintr = 0;
		errno = EINTR;
		return -1;
	}
	if (recv_err) {
		recv_err = 0;
		errno = ENOMEM;
		return -1;
	}
	if (qhead == qtail) {
		errno = EAGAIN;
		return -1;
	}
	{
		size_t n = q[qhead].n, cap = m->msg_iov[0].iov_len;
		int r = q[qhead].remote, l = q[qhead].local;
		if (n > cap)
			n = cap;
		memcpy(m->msg_iov[0].iov_base, q[qhead].d, n);
		if (m->msg_namelen < REMOTELEN[r])
			DIE("recvmsg with a name buffer of %u bytes", (unsigned)m->msg_namelen);
		memcpy(m->msg_name, &REMOTE[r], REMOTELEN[r]);
		m->msg_namelen = REMOTELEN[r];
		m->msg_flags = 0;
		/* what `transport_read()` must make of it: the PKTINFO address, or without one the
		 * socket's (the wildcard, `rxq_getsockname()`) */
		memset(&rxq_rx, 0, sizeof rxq_rx);
		rxq_rx.valid = true;
		if (no_pktinfo) {
			wildcard(&rxq_rx.local, &rxq_rx.locallen);
		} else {
			memcpy(&rxq_rx.local, &LOCAL[l], LOCALLEN[l]);
			rxq_rx.locallen = LOCALLEN[l];
		}
		if (no_pktinfo) {
			m->msg_controllen = 0;
		} else {
			struct cmsghdr *cm;
			size_t need = v6 ? CMSG_SPACE(sizeof(struct in6_pktinfo))
			                 : CMSG_SPACE(sizeof(struct in_pktinfo));
			if (m->msg_controllen < need)
				DIE("recvmsg with a control buffer of %zu bytes", (size_t)m->msg_controllen);
			memset(m->msg_control, 0, need);
			m->msg_controllen = need;
			cm = CMSG_FIRSTHDR(m);
			if (v6) {
				struct in6_pktinfo pk;
				memset(&pk, 0, sizeof pk);
				pk.ipi6_addr = ((struct sockaddr_in6 *)&LOCAL[l])->sin6_addr;
				pk.ipi6_ifindex = IFINDEX[l];
				cm->cmsg_level = IPPROTO_IPV6;
				cm->cmsg_type = IPV6_PKTINFO;
				cm->cmsg_len = CMSG_LEN(sizeof pk);
				memcpy(CMSG_DATA(cm), &pk, sizeof pk);
			} else {
				struct in_pktinfo pk;
				memset(&pk, 0, sizeof pk);
				pk.ipi_addr = ((struct sockaddr_in *)&LOCAL[l])->sin_addr;
				pk.ipi_ifindex = (int)IFINDEX[l];
				cm->cmsg_level = IPPROTO_IP;
				cm->cmsg_type = IP_PKTINFO;
				cm->cmsg_len = CMSG_LEN(sizeof pk);
				memcpy(CMSG_DATA(cm), &pk, sizeof pk);
			}
		}
		qhead++;
		return (ssize_t)n;
	}
}

static int rxq_getsockname(int fd, struct sockaddr *sa, socklen_t *len)
{
	(void)fd;
	if (gsn_fail) {
		errno = EBADF;
		return -1;
	}
	{
		struct sockaddr_storage w;
		socklen_t wl;
		wildcard(&w, &wl);
		if (*len < wl)
			DIE("getsockname with a buffer of %u bytes", (unsigned)*len);
		memcpy(sa, &w, wl);
		*len = wl;
	}
	return 0;
}

/* The source address a `sendmsg` forces (IP_PKTINFO / IPV6_PKTINFO), as the kernel reads it;
 * false when there is none.  Anything else in the control data is not the product's to send. */
static bool forced_source(const struct msghdr *m, struct sockaddr_storage *src, socklen_t *srclen)
{
	bool found = false;
	memset(src, 0, sizeof *src);
	*srclen = 0;
	if (m->msg_controllen == 0)
		return false;
	if (!m->msg_control)
		DIE("sendmsg with %zu bytes of control data and no buffer", (size_t)m->msg_controllen);
	for (struct cmsghdr *cm = CMSG_FIRSTHDR((struct msghdr *)m); cm;
	     cm = CMSG_NXTHDR((struct msghdr *)m, cm)) {
		if (found)
			DIE("sendmsg with more than one control message");
		found = true;
		if (v6) {
			struct in6_pktinfo pk;
			struct sockaddr_in6 *s = (struct sockaddr_in6 *)src;
			if (cm->cmsg_level != IPPROTO_IPV6 || cm->cmsg_type != IPV6_PKTINFO ||
			    cm->cmsg_len != CMSG_LEN(sizeof pk))
				DIE("sendmsg on the IPv6 socket with a control message that is not an "
				    "IPV6_PKTINFO (level %d, type %d)", cm->cmsg_level, cm->cmsg_type);
			memcpy(&pk, CMSG_DATA(cm), sizeof pk);
			s->sin6_family = AF_INET6;
			s->sin6_addr = pk.ipi6_addr;
			s->sin6_scope_id = pk.ipi6_ifindex; /* `rxq_same_host` reads it for fe80::/10 */
			*srclen = sizeof *s;
		} else {
			struct in_pktinfo pk;
			struct sockaddr_in *s = (struct sockaddr_in *)src;
			if (cm->cmsg_level != IPPROTO_IP || cm->cmsg_type != IP_PKTINFO ||
			    cm->cmsg_len != CMSG_LEN(sizeof pk))
				DIE("sendmsg on the IPv4 socket with a control message that is not an "
				    "IP_PKTINFO (level %d, type %d)", cm->cmsg_level, cm->cmsg_type);
			memcpy(&pk, CMSG_DATA(cm), sizeof pk);
			s->sin_family = AF_INET;
			s->sin_addr = pk.ipi_spec_dst; /* the kernel's source; `ipi_addr` is ignored */
			*srclen = sizeof *s;
		}
	}
	return found;
}

static bool is_wildcard(const struct sockaddr_storage *a)
{
	if (a->ss_family == AF_INET)
		return ((const struct sockaddr_in *)a)->sin_addr.s_addr == htonl(INADDR_ANY);
	if (a->ss_family == AF_INET6)
		return IN6_IS_ADDR_UNSPECIFIED(&((const struct sockaddr_in6 *)a)->sin6_addr);
	return true;
}

/* ⭐ THE MIGRATION ORACLE: a connection's packet goes where ngtcp2 wrote it for — and
 *    (15 Oct 2026) leaves FROM the local end of that path; an answer ngtcp2 did not write
 *    (Retry, reset, version negotiation) leaves from the address its datagram arrived on. */
/* ⭐ THE SOURCE-REFUSED ORACLE (15 Oct 2026): the packet the kernel refused a source for must
 *    go again — the same bytes, to the same address — without one; and the rationed line. */
static struct {
	bool valid, retried;
	struct sockaddr_storage to;
	socklen_t tolen;
	size_t len;
	uint64_t h;
} refused_pkt;
static unsigned long src_refusals; /* in the process: the product's counter is a static too */
static bool refusal_line_due, refusal_line_seen;

static uint64_t fnv(const uint8_t *d, size_t n)
{
	uint64_t h = 0xcbf29ce484222325ull;
	for (size_t i = 0; i < n; i++)
		h = (h ^ d[i]) * 0x100000001b3ull;
	return h;
}

static ssize_t rxq_sendmsg(int fd, const struct msghdr *m, int flags)
{
	const struct sockaddr *sa = m->msg_name;
	socklen_t salen = m->msg_namelen;
	struct sockaddr_storage src;
	socklen_t srclen;
	bool forced, again = false;
	size_t n = 0;
	uint64_t h;
	(void)fd; (void)flags;
	if (m->msg_iovlen != 1)
		DIE("sendmsg with %zu iovecs (one packet per sendmsg, no GSO)", (size_t)m->msg_iovlen);
	n = m->msg_iov[0].iov_len;
	h = fnv(m->msg_iov[0].iov_base, n); /* every byte is read (ASan) */
	if (!sa || salen == 0 || salen > sizeof(struct sockaddr_storage))
		DIE("sendmsg with an address of %u bytes", (unsigned)salen);
	if (refused_pkt.valid) {
		if (m->msg_controllen == 0 && n == refused_pkt.len && h == refused_pkt.h &&
		    salen == refused_pkt.tolen && memcmp(sa, &refused_pkt.to, salen) == 0) {
			/* the declared fallback: the packet again, from the address the kernel picks
			 * (and again after an EINTR) */
			if (!refused_pkt.retried && refusal_line_due != refusal_line_seen)
				DIE("the kernel's refusal no. %lu of a source address %s", src_refusals,
				    refusal_line_due ? "was not written (the 1st-3rd and every 256th are)"
				                     : "was written (only the 1st-3rd and every 256th are)");
			refused_pkt.retried = again = true;
		} else if (!refused_pkt.retried) {
			DIE("the kernel refused the source address of a packet of %zu bytes, and it was not "
			    "sent again without one (next: %zu bytes, %s control data)", refused_pkt.len, n,
			    m->msg_controllen ? "with" : "without");
		} else {
			refused_pkt.valid = false;
		}
	}
	if (rxq_expect.valid &&
	    (salen != rxq_expect.tolen || memcmp(sa, &rxq_expect.to, salen) != 0)) {
		char a[80], b[80];
		address_text(sa, salen, a, sizeof a);
		address_text((const struct sockaddr *)&rxq_expect.to, rxq_expect.tolen, b, sizeof b);
		DIE("a connection's packet sent to %s, but ngtcp2 (%s) wrote it for %s", a,
		    rxq_expect.who, b);
	}
	forced = forced_source(m, &src, &srclen);
	{
		const struct sockaddr_storage *want = NULL;
		socklen_t wantlen = 0;
		const char *whose = NULL;
		if (rxq_expect.valid) {
			want = &rxq_expect.from;
			wantlen = rxq_expect.fromlen;
			whose = rxq_expect.who;
		} else if (rxq_rx.valid) {
			want = &rxq_rx.local;
			wantlen = rxq_rx.locallen;
			whose = "the datagram it answers";
		}
		if (want) {
			char a[80], b[80];
			address_text((const struct sockaddr *)want, wantlen, b, sizeof b);
			if (again) {
				/* no source, on purpose: the address is no longer this machine's */
			} else if (is_wildcard(want)) {
				if (forced) {
					address_text((const struct sockaddr *)&src, srclen, a, sizeof a);
					DIE("a packet forced to leave from %s where the local end is the "
					    "wildcard %s (%s)", a, b, whose);
				}
			} else if (!forced) {
				DIE("a packet left without its source address: the local end is %s (%s), "
				    "the kernel would pick one of its own", b, whose);
			} else if (!rxq_same_host((const struct sockaddr *)&src, srclen,
			                          (const struct sockaddr *)want, wantlen)) {
				address_text((const struct sockaddr *)&src, srclen, a, sizeof a);
				DIE("a packet left from %s, but its local end is %s (%s)", a, b, whose);
			}
		}
	}
	if (forced && src_refuse_left > 0) {
		/* the address the client wrote to is no longer this machine's */
		src_refuse_left--;
		src_refusals++;
		refused_pkt.valid = true;
		refused_pkt.retried = false;
		memcpy(&refused_pkt.to, sa, salen);
		refused_pkt.tolen = salen;
		refused_pkt.len = n;
		refused_pkt.h = h;
		refusal_line_due = src_refusals <= 3 || src_refusals % 256 == 0;
		refusal_line_seen = false;
		errno = src_refuse_errno;
		return -1;
	}
	if (send_fail_left > 0) {
		send_fail_left--;
		errno = send_errno;
		return -1;
	}
	return (ssize_t)n;
}

static int rxq_clock_gettime(clockid_t id, struct timespec *ts)
{
	(void)id;
	ts->tv_sec = (time_t)(rxq_now_ns / 1000000000u);
	ts->tv_nsec = (long)(rxq_now_ns % 1000000000u);
	return 0;
}

static int rxq_RAND_bytes(unsigned char *d, int n) { return rxq_rand(d, (size_t)n) ? 1 : 0; }

static SSL *rxq_SSL_new(SSL_CTX *ctx)
{
	(void)ctx;
	if (rxq_fail_next == RXQ_FAIL_SSL_NEW) {
		rxq_fail_next = 0;
		return NULL;
	}
	return (SSL *)calloc(1, 64);
}
static void rxq_SSL_free(SSL *s) { free(s); }
static int rxq_SSL_set_ex_data(SSL *s, int idx, void *arg)
{
	(void)idx;
	memcpy(s, &arg, sizeof arg);
	return 1;
}
static void rxq_SSL_set_accept_state(SSL *s) { ((uint8_t *)s)[sizeof(void *)] = 1; }

/* ── building the datagrams ──────────────────────────────────────────── */
static void set_time(uint64_t ms)
{
	rx_now_ms = ms;
	rxq_now_ns = ms * 1000000u;
}

static void set_time_ns(uint64_t ns)
{
	rx_now_ms = ns / 1000000u;
	rxq_now_ns = ns;
}

/* ⛔ The clock MOVES ON from where it is, nanoseconds included: `set_time(rx_now_ms + ms)`
 *    dropped the sub-millisecond part that op 14 (`op_flood`, steps of 10 µs) leaves, so a
 *    step of 0 ms put the clock BACK by up to 999 µs — CLOCK_MONOTONIC never does that, and
 *    the stub's oracle said «wt_sign_of_life went back in time» (fuzz 15 Oct 2026, lane 23:
 *    a harness false alarm, not transport.c). */
static void advance_ms(uint64_t ms)
{
	set_time_ns(rxq_now_ns + ms * 1000000u);
}

static uint8_t last_dcid[20];
static size_t last_dcidlen;
static unsigned births;

static transport *T;

static void deliver(bool hold)
{
	if (!hold)
		transport_read(T);
}

static size_t pad(uint8_t *b, size_t n)
{
	while (n < 24)
		b[n++] = 0; /* END, rv 0: a valid QUIC packet is ≥ 21 bytes (`transport_read()`) */
	return n;
}

/* ⭐ The caps oracle's OWN reading of a place — written apart from `address_key()` (as
 *    `rcp_key_address()` states the rule: v4-mapped and NAT64 64:ff9b::/96 are their
 *    IPv4, ::1 whole, other IPv6 by /64; the /48 only for those), so a slip there shows. */
typedef struct { uint8_t b[17]; } place;
static void own_place(const struct sockaddr_storage *ss, place *p64, place *p48)
{
	memset(p64, 0, sizeof *p64);
	if (ss->ss_family == AF_INET) {
		p64->b[0] = 4;
		memcpy(p64->b + 1, &((const struct sockaddr_in *)ss)->sin_addr, 4);
	} else {
		const uint8_t *a = ((const struct sockaddr_in6 *)ss)->sin6_addr.s6_addr;
		static const uint8_t zero[10];
		bool mapped = memcmp(a, zero, 10) == 0 && a[10] == 0xff && a[11] == 0xff;
		bool nat64 = a[0] == 0 && a[1] == 0x64 && a[2] == 0xff && a[3] == 0x9b &&
		             memcmp(a + 4, zero, 8) == 0;
		bool loop = memcmp(a, zero, 10) == 0 && !a[10] && !a[11] && !a[12] && !a[13] &&
		            !a[14] && a[15] == 1;
		if (mapped || nat64) {
			p64->b[0] = 4;
			memcpy(p64->b + 1, a + 12, 4);
		} else if (loop) {
			p64->b[0] = 1;
		} else {
			p64->b[0] = 6;
			memcpy(p64->b + 1, a, 8);
			*p48 = *p64;
			p48->b[0] = 48;
			memset(p48->b + 7, 0, 10);
			return;
		}
	}
	*p48 = *p64;
}

/* Once per process: `address_key()` and `own_place()` must make the SAME classes on
 * the addresses the fuzzed input never carries (NAT64, loopback, local-use NAT64, …). */
static void places_agree(void)
{
	static bool done;
	static const char *A[] = {"198.51.100.7", "::ffff:198.51.100.7", "64:ff9b::c633:6407",
	                          "64:ff9b::198.51.100.8", "64:ff9b:1::c633:6407", "::1", "::2",
	                          "::", "::198.51.100.7", "fe80::1", "fe80::2", "2001:db8::7",
	                          "2001:db8::8", "2001:db8:0:1::9", "2001:db8:1::9", "127.0.0.1"};
	enum { NA = sizeof A / sizeof A[0] };
	struct sockaddr_storage ss[NA];
	uint8_t k[NA][16], k48[NA][16];
	place p[NA], p48[NA];
	if (done)
		return;
	done = true;
	for (int i = 0; i < NA; i++) {
		memset(&ss[i], 0, sizeof ss[i]);
		if (strchr(A[i], ':')) {
			struct sockaddr_in6 *s6 = (struct sockaddr_in6 *)&ss[i];
			s6->sin6_family = AF_INET6;
			if (inet_pton(AF_INET6, A[i], &s6->sin6_addr) != 1)
				DIE("places_agree: %s does not parse", A[i]);
		} else {
			struct sockaddr_in *s4 = (struct sockaddr_in *)&ss[i];
			s4->sin_family = AF_INET;
			if (inet_pton(AF_INET, A[i], &s4->sin_addr) != 1)
				DIE("places_agree: %s does not parse", A[i]);
		}
		address_key((const struct sockaddr *)&ss[i], k[i], k48[i]);
		own_place(&ss[i], &p[i], &p48[i]);
	}
	for (int i = 0; i < NA; i++)
		for (int j = 0; j < NA; j++) {
			bool same = memcmp(k[i], k[j], 16) == 0, own = memcmp(&p[i], &p[j], sizeof p[i]) == 0;
			bool same48 = memcmp(k48[i], k48[j], 16) == 0,
			     own48 = memcmp(&p48[i], &p48[j], sizeof p48[i]) == 0;
			if (same != own)
				DIE("%s and %s: transport.c says %s place, the rule says %s", A[i], A[j],
				    same ? "the same" : "another", own ? "the same" : "another");
			if (same48 != own48)
				DIE("%s and %s: transport.c says %s /48, the rule says %s", A[i], A[j],
				    same48 ? "the same" : "another", own48 ? "the same" : "another");
		}
}

/* Not logged in, alive, from that place (`is48`: from that /48). */
static size_t own_from(const place *p, bool is48)
{
	size_t n = 0;
	for (connection *c = T->prime; c; c = c->upcoming) {
		place k, k48;
		if (!c->unlogged || c->dead_run)
			continue;
		own_place(&rxq_reg_of(c->conn)->born, &k, &k48);
		if (memcmp(is48 ? &k48 : &k, p, sizeof *p) == 0)
			n++;
	}
	return n;
}

/* The eviction rank as evict_rank() of this branch says it (lower goes first, -1 never): not
 * logged in, alive, and finished (0), without a session (1), wait-hello (2), wait-credentials (3);
 * NEVER wait-verdict (PAM is judging it; the rule «a wait-verdict refused by us without PAM is
 * evictable» belongs to the discarded attempt's later commits, not to this branch). */
static int own_rank(connection *c)
{
	uint8_t st = rxq_reg_of(c->conn)->wt_state % RXQ_ST_N;
	if (!c->unlogged || c->dead_run)
		return -1;
	switch (st) {
	case RXQ_ST_FINISHED: return 0;
	case RXQ_ST_VERDICT: return -1;
	case RXQ_ST_NONE: return 1;
	case RXQ_ST_HELLO: return 2;
	case RXQ_ST_CREDENTIALS: return 3;
	default: return -1;
	}
}

/* ⭐ the caps oracle: false once LIMITS lowered a cap under what was already open (the
 *    product sets its caps once, before any connection) */
static bool caps_exact;

/* ⭐ THE LOG ORACLE: «new connection» event lines are at most BIRTH_LINES per window of
 *    REFUSAL_LOG_S, so any REFUSAL_LOG_S of time holds at most 2 × BIRTH_LINES of them
 *    (it overlaps two windows at most).  The times of the last 2 × BIRTH_LINES. */
extern void (*rx_event_line)(const char *text);
static uint64_t birth_line_at[2 * BIRTH_LINES];
static size_t birth_line_next, birth_lines;

/* ⭐ the tokens «forgotten early»: what the harness's own ring counts, and what the summary
 *    lines said (`refusals_report()`) */
static unsigned long forgotten_expected, forgotten_reported;

static void on_event_line(const char *text)
{
	static const char PRESSURE[] = "⚠ SERVER UNDER PRESSURE";
	static const char REFUSED[] = "⚠ the kernel refused ";
	if (strncmp(text, REFUSED, sizeof REFUSED - 1) == 0) {
		if (!refused_pkt.valid || refused_pkt.retried)
			DIE("«%s» with no refusal of the kernel behind it", text);
		if (!refusal_line_due)
			DIE("the kernel's refusal no. %lu of a source address written (only the 1st-3rd "
			    "and every 256th are): «%s»", src_refusals, text);
		refusal_line_seen = true;
		return;
	}
	if (strncmp(text, PRESSURE, sizeof PRESSURE - 1) == 0) {
		/* «…, %u forgotten early (more than 4096 connections in 10 s)»: the numbers are the
		 * documented ones, written here apart */
		static const char TAIL[] = " forgotten early (more than 4096 connections in 10 s)";
		const char *p = strstr(text, TAIL), *q;
		if (!p || p[sizeof TAIL - 1] != 0)
			DIE("a summary line without «N forgotten early (more than 4096 connections in "
			    "10 s)» at its end: «%s»", text);
		for (q = p; q > text && q[-1] >= '0' && q[-1] <= '9'; q--)
			;
		if (q == p || q == text || q[-1] != ' ')
			DIE("a summary line with no count before «forgotten early»: «%s»", text);
		forgotten_reported += strtoul(q, NULL, 10);
		return;
	}
	if (strncmp(text, "new connection from", 19) != 0)
		return;
	if (birth_lines >= 2 * BIRTH_LINES &&
	    rxq_now_ns - birth_line_at[birth_line_next] < (uint64_t)REFUSAL_LOG_S * NGTCP2_SECONDS)
		DIE("%d «new connection» log lines within %d s: the churn floods the log",
		    2 * BIRTH_LINES + 1, REFUSAL_LOG_S);
	birth_line_at[birth_line_next] = rxq_now_ns;
	birth_line_next = (birth_line_next + 1) % (2 * BIRTH_LINES);
	birth_lines++;
}

/* ⭐ THE HARNESS'S OWN MEMORY OF USED TOKENS (the rule of d0e56764, written apart from
 *    `token_keep()` / `token_used()`): the tokens of the last KEPT births, each good for
 *    TOKEN_S after its birth; a birth past KEPT pushes out the oldest, «forgotten early» if
 *    its seconds were not over.  Fed by the stub at every birth (`rxq_on_birth`), whatever op
 *    made it. */
#define KEPT 4096
#define TOKEN_NS (10ull * 1000000000u)
_Static_assert(KEPT == TOKENS_KEPT, "the ring of d0e56764 is 4096 tokens: the harness's too");
_Static_assert(TOKEN_NS == RETRY_TOKEN_TIMEOUT, "a used token is kept 10 s (d0e56764)");
typedef struct {
	uint64_t h, until;
	size_t len;
} kept_token;
static kept_token kept[KEPT], dropped[64];
static size_t kept_next, kept_n, dropped_next;

static void on_birth(const uint8_t *tok, size_t len)
{
	kept_token *k = &kept[kept_next];
	if (kept_n == KEPT && k->until > rxq_now_ns) {
		forgotten_expected++;
		dropped[dropped_next] = *k;
		dropped_next = (dropped_next + 1) % (sizeof dropped / sizeof dropped[0]);
	}
	k->h = fnv(tok, len);
	k->len = len;
	k->until = rxq_now_ns + TOKEN_NS;
	kept_next = (kept_next + 1) % KEPT;
	if (kept_n < KEPT)
		kept_n++;
}

/* 1: in the memory and within its seconds · 2: pushed out early, still within them · 0 */
static int token_state(const uint8_t *tok, size_t len)
{
	uint64_t h = fnv(tok, len);
	for (size_t k = 0; k < kept_n; k++)
		if (kept[k].len == len && kept[k].h == h && kept[k].until > rxq_now_ns)
			return 1;
	for (size_t k = 0; k < sizeof dropped / sizeof dropped[0]; k++)
		if (dropped[k].len == len && dropped[k].h == h && dropped[k].until > rxq_now_ns)
			return 2;
	return 0;
}

/* ⭐ the floods' births (op 14): each its own dcid and token, by serial */
#define FLOOD_MAX 4200
static unsigned flood_n;

static void flood_dcid(unsigned s, uint8_t *d)
{
	d[0] = 0xf0;
	d[1] = (uint8_t)(s >> 8);
	d[2] = (uint8_t)s;
	for (size_t k = 3; k < 8; k++)
		d[k] = (uint8_t)(0x3c + k);
}

static size_t flood_token(unsigned s, uint8_t *tok)
{
	tok[0] = NGTCP2_CRYPTO_TOKEN_MAGIC_RETRY2;
	tok[1] = RXQ_TOKEN_GOOD;
	tok[2] = 8;
	for (size_t k = 0; k < 8; k++)
		tok[3 + k] = (uint8_t)(0x11 * (k + 1));
	tok[11] = 0xf1;
	tok[12] = (uint8_t)(s >> 8);
	tok[13] = (uint8_t)s;
	return 14;
}

static void op_new(const uint8_t *a, size_t n)
{
	uint8_t b[QBYTES];
	size_t i = 0, dl, sl = 8, tl = 0;
	uint8_t tok[3 + 20 + 1];
	uint8_t a0 = n > 0 ? a[0] : 0, a1 = n > 1 ? a[1] : 0, a2 = n > 2 ? a[2] : 0,
	        a3 = n > 3 ? a[3] : 8, a4 = n > 4 ? a[4] : 0;
	const uint8_t *script = n > 5 ? a + 5 : NULL;
	size_t sn = n > 5 ? n - 5 : 0;

	bool replay = (a2 & 0x80) && flood_n;
	unsigned serial = replay ? ((a1 & 1) ? flood_n - 1 : 0) : 0;
	if (replay) {
		/* a FLOOD birth's Initial again, its dcid and its token (op 14) */
		dl = 8;
		flood_dcid(serial, last_dcid);
		last_dcidlen = dl;
	} else if ((a2 & 0x40) && last_dcidlen) {
		dl = last_dcidlen;
	} else {
		dl = 8 + a1 % 13;
		births++;
		for (size_t k = 0; k < dl; k++)
			last_dcid[k] = (uint8_t)(0xd0 + births + k * 7);
		last_dcidlen = dl;
	}
	b[i++] = 0xc3; /* long header, Initial */
	b[i++] = 0; b[i++] = 0; b[i++] = 0; b[i++] = 1;
	b[i++] = (uint8_t)dl;
	memcpy(b + i, last_dcid, dl);
	i += dl;
	b[i++] = (uint8_t)sl;
	for (size_t k = 0; k < sl; k++)
		b[i++] = (uint8_t)(0xa0 + births + k);
	if (replay) {
		tl = flood_token(serial, tok);
	} else if (!(a2 & 0x10)) {
		/* the token our Retry gave: magic, verdict, the odcid */
		tok[0] = (a2 & 0x20) ? 0x36 : NGTCP2_CRYPTO_TOKEN_MAGIC_RETRY2;
		tok[1] = (uint8_t)(a2 % RXQ_TOKEN_N);
		tok[2] = 8;
		for (size_t k = 0; k < 8; k++)
			tok[3 + k] = (uint8_t)(0x11 * (k + 1));
		/* ⭐ one token per Retry, as ngtcp2's are (AEAD, random nonce): a NEW that sends
		 *    the previous dcid again (a2 bit 6) sends its token again too */
		tok[11] = (uint8_t)births;
		tl = 12;
	}
	b[i++] = (uint8_t)tl;
	memcpy(b + i, tok, tl);
	i += tl;
	if (sn > sizeof b - i)
		sn = sizeof b - i;
	if (sn)
		memcpy(b + i, script, sn);
	i += sn;
	i = pad(b, i);
	rxq_fail_next = (a3 % 16) < RXQ_FAIL_N ? a3 % 16 : 0;
	{
		/* ⭐ the caps oracle, for a NEW delivered alone: a refusal only at a cap (or full
		 *    with nobody to evict), it leaves nothing behind; an eviction only when full,
		 *    exactly of the connection the rule names, and only once the newcomer exists */
		bool alone = qhead == qtail && !(a4 & 1);
		place key, key48;
		struct { rxq_reg *r; int rank; size_t crowd; unsigned evc; bool parked; } snap[RXQ_CONNS * 2];
		size_t ns = 0, before = T->how_many, births_before = rxq_nconns, from, from48,
		       live = live_count(T), pend = pending_count(T), nev = 0, evicted = 0;
		rxq_reg *want = NULL, *gone = NULL;
		bool full, newcomer = false;
		own_place(&REMOTE[a0 % 4], &key, &key48);
		from = own_from(&key, false);
		from48 = own_from(&key48, true);
		full = live >= cap_conns(T) || pend >= cap_pending(T);
		for (connection *c = T->prime; c && ns < RXQ_CONNS * 2; c = c->upcoming) {
			place k, k48;
			snap[ns].r = rxq_reg_of(c->conn);
			snap[ns].rank = own_rank(c);
			own_place(&snap[ns].r->born, &k, &k48);
			snap[ns].crowd = own_from(&k48, true);
			snap[ns].evc = snap[ns].r->evicted;
			snap[ns].parked = rxq_now_ns > snap[ns].r->born_ns &&
			                  rxq_now_ns - snap[ns].r->born_ns >= 5ull * NGTCP2_SECONDS; /* PARKED_S */
			nev += snap[ns].rank >= 0;
			ns++;
		}
		/* the victim the rule names (`pick_victim()`): the oldest finished; else the most crowded
		 * place; between equals a PARKED one (older than PARKED_S) before a fresh one; then the
		 * earliest state (lower rank), the oldest on a tie.  The
		 * snapshot is newest first, like the list: the walk is the same, with the same `<=`. */
		for (size_t k = ns; k-- > 0;)
			if (snap[k].rank == 0) {
				want = snap[k].r;
				break;
			}
		if (!want) {
			size_t bc = 0;
			int br = 0;
			bool bp = false;
			for (size_t k = 0; k < ns; k++) {
				bool better;
				if (snap[k].rank < 0)
					continue;
				if (!want || snap[k].crowd > bc)
					better = true;
				else if (snap[k].crowd < bc)
					better = false;
				else if (snap[k].parked != bp)
					better = snap[k].parked;
				else
					better = snap[k].parked || snap[k].rank <= br;
				if (better) {
					want = snap[k].r;
					bc = snap[k].crowd;
					br = snap[k].rank;
					bp = snap[k].parked;
				}
			}
		}
		/* the token: in the harness's memory of used tokens (made a connection less than
		 * 10 s ago, among the last 4096), or pushed out of it early? */
		bool token_good = tl >= 2 && tok[0] == NGTCP2_CRYPTO_TOKEN_MAGIC_RETRY2 &&
		                  tok[1] % RXQ_TOKEN_N == RXQ_TOKEN_GOOD;
		int ts = token_good ? token_state(tok, tl) : 0;
		bool reused = ts == 1, forgotten = ts == 2,
		     existing = cid_find(T, last_dcid, dl) != NULL;
		unsigned retries = rxq_retries;
		unsigned long long hs_before = T->hs_refused_total;
		rxq_last_close_code = 0;
		enqueue(b, i, a0 % 4, ((a4 >> 1) & 3) % 3);
		deliver(a4 & 1);
		/* ⚠ a recvmsg ENOMEM played by op 8 ends transport_read()'s pass BEFORE it reads the
		 *   datagram (it stays queued, read at the next wake): nothing is judged of a NEW that
		 *   was not read (fuzz 15 Oct 2026: «a Retry token used again, and no INVALID_TOKEN»
		 *   on an Initial still in the queue — a harness false alarm) */
		alone = alone && qhead == qtail;
		/* ⭐ R4: a newcomer refused for the RATE of handshakes (hsrate.h, after the token and before room_for()) is a
		 *    CONNECTION_REFUSED at any time, with free places: it is not a caps violation */
		bool rate_refused = T->hs_refused_total != hs_before;
		/* ⚠ and without PKTINFO AND without getsockname() (op 8, a2 = 3) transport_read()
		 *   has no local address to answer from: it discards the datagram, said in the log
		 *   («no local address for a packet»), and answers nothing — INVALID_TOKEN included */
		if (alone && no_pktinfo && gsn_fail) {
			/* ⭐ not «stop judging» but its own check (review of cda1636d): the
			 *    discarded datagram made NOTHING — no connection, no eviction, no
			 *    Retry, no close */
			if (rxq_nconns != births_before)
				DIE("a datagram with no local address made a connection");
			for (size_t k = 0; k < ns; k++)
				if (snap[k].r->evicted != snap[k].evc)
					DIE("a datagram with no local address EVICTED connection #%td",
					    snap[k].r - rxq_conns);
			if (rxq_retries != retries || rxq_last_close_code)
				DIE("a datagram with no local address was answered (Retry %s, close %#x)",
				    rxq_retries != retries ? "sent" : "not sent",
				    (unsigned)rxq_last_close_code);
			alone = false;
		}
		for (size_t k = births_before; k < rxq_nconns; k++)
			if (rxq_conns[k].wt_born)
				newcomer = true;
		if (alone && token_good && reused && !existing) {
			if (newcomer)
				DIE("a Retry token made a SECOND connection within %d s",
				    (int)(RETRY_TOKEN_TIMEOUT / NGTCP2_SECONDS));
			/* ⛔ INVALID_TOKEN, never a second Retry: an honest client must discard
			 *    a second Retry (RFC 9000 §17.2.5.2) and would hang to its timeout */
			if (rxq_retries != retries)
				DIE("a Retry token used again was answered with a second Retry");
			if (rxq_last_close_code != NGTCP2_INVALID_TOKEN)
				DIE("a Retry token used again, and no INVALID_TOKEN for it");
		}
		/* ⭐ a token FORGOTTEN EARLY (d0e56764: past 4096 connections in 10 s the oldest is
		 *    forgotten, counted, «refusing would answer every token with a Retry»): it is
		 *    not refused as used again — it may make a second connection */
		if (alone && forgotten && !existing && rxq_last_close_code == NGTCP2_INVALID_TOKEN)
			DIE("a Retry token forgotten early (pushed out of the %d kept) refused as used again",
			    KEPT);
		if (alone && caps_exact) {
			for (size_t k = 0; k < ns; k++)
				if (snap[k].r->evicted > snap[k].evc) {
					evicted++;
					gone = snap[k].r;
				}
			if (evicted > 1)
				DIE("%zu connections EVICTED for one newcomer", evicted);
			if (gone && !full)
				DIE("a connection EVICTED while the server was not full (%zu/%zu open, "
				    "%zu/%zu pending)", live, cap_conns(T), pend, cap_pending(T));
			if (gone && gone != want)
				DIE("EVICTED connection #%td (%s), the rule names #%td (%s)",
				    gone - rxq_conns, RXQ_STATE_NAMES[gone->wt_state % RXQ_ST_N],
				    want ? want - rxq_conns : -1,
				    want ? RXQ_STATE_NAMES[want->wt_state % RXQ_ST_N] : "none");
			if (gone && !newcomer)
				DIE("a connection EVICTED for a newcomer that does not exist (the accept "
				    "failed, or it was refused)");
			if (!gone && full && want && newcomer && from < cap_per_address(T) &&
			    from48 < cap_per_48(T))
				DIE("a newcomer accepted on a full server and nobody EVICTED for it");
		}
		if (alone && caps_exact && !rate_refused && rxq_last_close_code == NGTCP2_CONNECTION_REFUSED) {
			if (from < cap_per_address(T) && from48 < cap_per_48(T) && (!full || nev > 0))
				DIE("a connection REFUSED with %zu/%zu open, %zu/%zu pending, %zu/%zu "
				    "pending from its address, %zu/%zu from its /48, %zu evictable",
				    live, cap_conns(T), pend, cap_pending(T), from, cap_per_address(T),
				    from48, cap_per_48(T), nev);
			if (T->how_many > before)
				DIE("a refused connection was born anyway");
		}
	}
	rxq_fail_next = 0; /* a failure that was not consumed is not left armed */
}

static rxq_reg *pick(uint8_t sel)
{
	if (!rxq_nconns)
		return NULL;
	return &rxq_conns[sel % rxq_nconns];
}

static void op_pkt(uint8_t sel, const uint8_t *a, size_t n)
{
	uint8_t b[QBYTES];
	size_t i = 0;
	rxq_reg *r = pick(sel);
	const ngtcp2_cid *cid;
	uint8_t a0 = n > 0 ? a[0] : 0, a1 = n > 1 ? a[1] : 0, a2 = n > 2 ? a[2] : 0;
	size_t sn = n > 3 ? n - 3 : 0;
	if (!r || !r->ncid)
		return;
	cid = &r->cid[a1 % r->ncid];
	if (a2 & 1) {
		b[i++] = 0xe3; /* long header, Handshake */
		b[i++] = 0; b[i++] = 0; b[i++] = 0; b[i++] = 1;
		b[i++] = (uint8_t)cid->datalen;
		memcpy(b + i, cid->data, cid->datalen);
		i += cid->datalen;
		b[i++] = 8;
		memset(b + i, 0xa5, 8);
		i += 8;
	} else {
		/* short header: the dcid is SCIDLEN = 18 bytes, whatever the CID's length */
		uint8_t d[18] = {0};
		memcpy(d, cid->data, cid->datalen < 18 ? cid->datalen : 18);
		b[i++] = 0x41;
		memcpy(b + i, d, 18);
		i += 18;
	}
	if (sn > sizeof b - i)
		sn = sizeof b - i;
	if (sn)
		memcpy(b + i, a + 3, sn);
	i += sn;
	i = pad(b, i);
	enqueue(b, i, a0 % 4, ((a2 >> 2) & 3) % 3);
	deliver(a2 & 2);
}

static void op_wt(uint8_t sel, const uint8_t *a, size_t n)
{
	rxq_reg *r = pick(sel);
	uint8_t z[11] = {0};
	if (!r)
		return;
	memcpy(z, a, n < sizeof z ? n : sizeof z);
	r->wt_fail = (uint16_t)((z[0] << 8) | z[1]);
	r->wt_pkts = z[2] % 32;
	r->wt_pkt_len = (uint16_t)((z[3] << 8) | z[4]);
	r->wt_write_fail = z[5] & 1;
	r->wt_dead_line = (z[5] >> 1) & 1;
	r->wt_more_to_say = (z[5] >> 2) & 1;
	r->wt_state = (uint8_t)(((z[5] >> 5) & 7) % RXQ_ST_N);
	/* a2 bit 5: unused in this branch (it was «wait-verdict refused without PAM»); kept so the corpus format does not change */
	if (z[5] & 8)
		r->wt_beat_at = rxq_now_ns + (uint64_t)z[6] * 4 * NGTCP2_MILLISECONDS;
	else if (z[5] & 16)
		r->wt_beat_at = UINT64_MAX;
	r->wt_ticket = rx_u32(z + 7, 4);
	/* entered wait-credentials z[6] × 64 ms ago (0 … 16.3 s): both sides of PARKED_CRED_S */
	r->wt_cred_from_ms = 0;
	if (r->wt_state == RXQ_ST_CREDENTIALS) {
		uint64_t back = (uint64_t)z[6] * 64;
		r->wt_cred_from_ms = rx_now_ms > back ? rx_now_ms - back : 1;
	}
	/* ⛔ A state past the credentials is reached in the product ONLY through an admitted verdict
	 *    (transport_verdict_from() -> note_login()): since 8d5629f3 transport_expired() no longer
	 *    sees the login from the RCP state, as the synchronous PAM fallback it served is dead
	 *    (D4b).  Decreeing ATTACH/ACTIVE/DETACHED on a connection still `unlogged` played a state
	 *    the product cannot be in, and the age close of "not logged in in time" then hit a "logged
	 *    in" connection (rootside-completo d283a02b, crash-5e4ce06f).  So such a connection logs in
	 *    first, by the real road, and only then gets the state the input chose. */
	if (r->wt_state == RXQ_ST_ATTACH || r->wt_state == RXQ_ST_ACTIVE || r->wt_state == RXQ_ST_DETACHED) {
		for (connection *c = T->prime; c; c = c->upcoming) {
			if (rxq_reg_of(c->conn) != r || c->dead_run || !c->unlogged)
				continue;
			uint8_t want = r->wt_state;
			r->wt_state = RXQ_ST_VERDICT;
			/* ⛔ transport_verdict() hands the verdict to the FIRST connection that has the ticket,
			 *    and the stub compares only the number (it comes from the input): the ticket must be
			 *    UNIQUE among all the connections, or another one logs in in place of `c`. */
			uint64_t tk = r->wt_ticket ? r->wt_ticket : 1;
			for (size_t k = 0; k < rxq_nconns;) {
				if (&rxq_conns[k] != r && rxq_conns[k].wt_ticket == tk) {
					tk++;
					k = 0;
				} else {
					k++;
				}
			}
			r->wt_ticket = tk;
			(void)transport_verdict(T, tk, true, false);
			/* ⛔ `c` may be GONE here: transport_write() inside the verdict reaps a connection whose
			 *    write failed (wt_write_fail).  Look it up again by its registry entry: still there
			 *    and still unlogged is the incoherence; gone means it logged in and was closed. */
			for (connection *x = T->prime; x; x = x->upcoming)
				if (rxq_reg_of(x->conn) == r && !x->dead_run && x->unlogged)
					DIE("connection #%td: an admitted verdict (ticket %llu) left it unlogged: the harness "
					    "or transport_verdict() lost the login", r - rxq_conns, (unsigned long long)tk);
			r->wt_state = want;
			break;
		}
	}
}

static void op_ng(uint8_t sel, const uint8_t *a, size_t n)
{
	static const int WERR[4] = {0, NGTCP2_ERR_NOMEM, NGTCP2_ERR_CALLBACK_FAILURE,
	                            NGTCP2_ERR_PKT_NUM_EXHAUSTED};
	static const int CERR[4] = {0, NGTCP2_ERR_NOMEM, NGTCP2_ERR_NOBUF, NGTCP2_ERR_PKT_NUM_EXHAUSTED};
	static const int EERR[8] = {0, NGTCP2_ERR_NOMEM, NGTCP2_ERR_CALLBACK_FAILURE, NGTCP2_ERR_IDLE_CLOSE,
	                            NGTCP2_ERR_HANDSHAKE_TIMEOUT, NGTCP2_ERR_CRYPTO, NGTCP2_ERR_PROTO,
	                            NGTCP2_ERR_INTERNAL};
	/* the next read_pkt's return code (a10 % 16; 0 = what the packet's script says) */
	static const int RERR[16] = {0, NGTCP2_ERR_DROP_CONN, NGTCP2_ERR_CRYPTO, NGTCP2_ERR_CRYPTO,
	                             NGTCP2_ERR_CALLBACK_FAILURE, NGTCP2_ERR_HANDSHAKE_TIMEOUT, NGTCP2_ERR_PROTO,
	                             NGTCP2_ERR_NOMEM, NGTCP2_ERR_DRAINING, NGTCP2_ERR_DROP_CONN,
	                             NGTCP2_ERR_TRANSPORT_PARAM, NGTCP2_ERR_INTERNAL, NGTCP2_ERR_IDLE_CLOSE,
	                             NGTCP2_ERR_CLOSING, NGTCP2_ERR_RETRY, NGTCP2_ERR_FLOW_CONTROL};
	rxq_reg *r = pick(sel);
	uint8_t z[11] = {0};
	if (!r)
		return;
	memcpy(z, a, n < sizeof z ? n : sizeof z);
	r->write_path = z[0] % 3;
	r->write_err = WERR[z[1] & 3];
	r->close_err = CERR[z[2] & 3];
	r->expiry_err = EERR[z[3] & 7];
	r->tls_alert = z[9];                       /* a9: the TLS alert ngtcp2 holds (0 = none) */
	r->read_err = RERR[z[10] & 15];            /* a10: force the next read_pkt's return code */
	r->loss_ms = (uint64_t)z[4] * 4;
	r->lost_dgram = z[5];
	r->max_udp = z[6] & 1;
	r->quantum = z[7] ? (size_t)z[7] * 600 : 64 * 1024;
	r->pace_ns = z[8];
}

/* ⭐ THE WAIT ORACLE (15 Oct 2026): `transport_wait_ms()` never sleeps past the next age
 *    deadline — `born_ns` (ngtcp2's `initial_ts`, not transport.c's own `born`) plus
 *    UNLOGGED_MAX_S — of a live connection not logged in; the product rounds UP to the ms. */
static int wait_oracle(int ms)
{
	uint64_t deadline = UINT64_MAX;
	for (connection *c = T->prime; c; c = c->upcoming) {
		uint64_t d;
		if (!c->unlogged || c->dead_run)
			continue;
		d = rxq_reg_of(c->conn)->born_ns + (uint64_t)UNLOGGED_MAX_S * NGTCP2_SECONDS;
		if (d < deadline)
			deadline = d;
	}
	/* ⭐ and the summary lines (15 Oct 2026): counts waiting for their line wake the loop —
	 *    on an idle server nothing else would */
	if ((T->refused_full || T->refused_address || T->refused_48 || T->evicted || T->aged ||
	     T->token_replayed || T->token_forgotten) &&
	    T->refused_line_ns + (uint64_t)REFUSAL_LOG_S * NGTCP2_SECONDS < deadline)
		deadline = T->refused_line_ns + (uint64_t)REFUSAL_LOG_S * NGTCP2_SECONDS;
	if (T->births_quiet &&
	    T->birth_window_ns + (uint64_t)REFUSAL_LOG_S * NGTCP2_SECONDS < deadline)
		deadline = T->birth_window_ns + (uint64_t)REFUSAL_LOG_S * NGTCP2_SECONDS;
	if (deadline == UINT64_MAX)
		return ms;
	if (ms < 0)
		DIE("transport_wait_ms() says «no timer» with an age or summary deadline %llu ms away",
		    (unsigned long long)((deadline - rxq_now_ns) / 1000000u));
	{
		uint64_t gap = deadline > rxq_now_ns ? deadline - rxq_now_ns : 0;
		uint64_t most = gap / NGTCP2_MILLISECONDS + (gap % NGTCP2_MILLISECONDS != 0);
		if ((uint64_t)ms > most)
			DIE("transport_wait_ms() sleeps %d ms, the next age or summary deadline is %llu ms "
			    "away", ms,
			    (unsigned long long)most);
	}
	return ms;
}

/* ⭐ THE SUMMARY ORACLE (15 Oct 2026), right after a `transport_expired()`: the tokens
 *    forgotten early are counted exactly — the summary lines' numbers plus the count not yet
 *    written are the harness's own — and none waits for its line once REFUSAL_LOG_S (10 s)
 *    passed since the last one. */
static void summary_oracle(bool expired)
{
	if (forgotten_reported + T->token_forgotten != forgotten_expected)
		DIE("%lu Retry tokens forgotten early in the summary lines and %u counted, the "
		    "harness's ring pushed out %lu within their 10 s", forgotten_reported,
		    T->token_forgotten, forgotten_expected);
	if (expired && T->token_forgotten && !T->refused_ever)
		DIE("%u Retry tokens forgotten early, counted and not written: no summary line yet",
		    T->token_forgotten);
	if (expired && T->token_forgotten && rxq_now_ns - T->refused_line_ns >= 10ull * 1000000000u)
		DIE("%u Retry tokens forgotten early, counted and not written: the last summary line "
		    "was %llu ms ago", T->token_forgotten,
		    (unsigned long long)((rxq_now_ns - T->refused_line_ns) / 1000000u));
}

/* Retry-validated Initials, each born and dead at once (op 14): the ring of used tokens filled
 * at the rate the fuzzer picks. */
static void op_flood(const uint8_t *a, size_t n)
{
	/* the product's rate limits (hsrate.h) would stop a single address after 16 births: the flood raises them (see the header comment of op 14) */
	T->hs_lim = (struct hs_limits){ 1000000u, 1000000u, 1000000u, 1000000u, 1000000u, 1000000u };
	unsigned count = (n > 1 ? ((unsigned)a[0] << 8 | a[1]) : n ? a[0] : 0) + 1u;
	uint64_t step = (uint64_t)(n > 2 ? a[2] : 0) * 10000u;
	int addr = n > 3 ? a[3] % 4 : 0;
	if (count > FLOOD_MAX - flood_n)
		count = FLOOD_MAX - flood_n;
	for (unsigned k = 0; k < count; k++) {
		uint8_t b[64], tok[16];
		size_t i = 0, tl, before = rxq_nconns;
		unsigned s = flood_n++;
		if (k > 0 && step)
			set_time_ns(rxq_now_ns + step);
		(void)wait_oracle(transport_wait_ms(T));
		b[i++] = 0xc3; /* long header, Initial */
		b[i++] = 0; b[i++] = 0; b[i++] = 0; b[i++] = 1;
		b[i++] = 8;
		flood_dcid(s, b + i);
		i += 8;
		b[i++] = 8;
		for (size_t j = 0; j < 8; j++)
			b[i++] = (uint8_t)(0xa0 + j);
		tl = flood_token(s, tok);
		b[i++] = (uint8_t)tl;
		memcpy(b + i, tok, tl);
		i += tl;
		b[i++] = 0x00; /* what ngtcp2 finds: it decrypts … */
		b[i++] = 0x10; /* … and the peer closed: DRAINING, the connection dies at once */
		i = pad(b, i);
		enqueue(b, i, addr, 0);
		transport_read(T);
		/* ⭐ the table's slots of the connections born here and already dead are given back:
		 *    4097 births through a table of RXQ_CONNS */
		while (rxq_nconns > before && !rxq_conns[rxq_nconns - 1].alive)
			memset(&rxq_conns[--rxq_nconns], 0, sizeof rxq_conns[0]);
		transport_expired(T);
		summary_oracle(true);
	}
}

/* Datagrams for no connection, one read each (op 13). */
static void op_burst(const uint8_t *a, size_t n)
{
	uint8_t b[1300];
	unsigned count = (n > 0 ? a[0] : 0) + 1u;
	uint8_t a1 = n > 1 ? a[1] : 0, a2 = n > 2 ? a[2] : 0, a3 = n > 3 ? a[3] : 0,
	        a4 = n > 4 ? a[4] : 0;
	for (unsigned k = 0; k < count; k++) {
		size_t len;
		if (a3 & 2) {
			/* a long header of a version not ours, ≥ 1200 bytes (RFC 9000 §6) */
			memset(b, 0, sizeof b);
			b[0] = 0xc3;
			b[1] = 0x1a; b[2] = 0x2a; b[3] = 0x3a; b[4] = (uint8_t)(0x4a + k);
			b[5] = 8;
			memset(b + 6, 0xe0 + (k & 15), 8);
			b[14] = 8;
			memset(b + 15, 0xb0, 8);
			len = 1200;
		} else {
			/* a short header for a dcid nobody has (ours are minted by the RNG) */
			b[0] = 0x41;
			memset(b + 1, 0xee, 18);
			b[1] = (uint8_t)k;
			b[2] = (uint8_t)(k >> 8);
			len = 24 + a4 % 64;
			memset(b + 19, 0x5c, len - 19);
		}
		/* the clock moves BEFORE the pass, never after the last one: a clock moved with no
		 * `transport_expired()` behind it is not the loop's either (15 Oct 2026, the
		 * age oracle: a connection 90.1 s old «alive» after the burst's last step) */
		if (k > 0 && a2)
			advance_ms(a2);
		if (k == 0 && (a3 & 1))
			rxq_fail_next = RXQ_FAIL_RAND;
		/* ⛔ the loop's pass, as `main.c` runs it (wait, read, expired): a burst that moved
		 *    the clock through reads alone would age connections the product never leaves
		 *    unexpired (the first 5-minute run, 15 Oct 2026: a harness artifact) */
		(void)wait_oracle(transport_wait_ms(T));
		enqueue(b, len, a1 % 4, 0);
		transport_read(T);
		rxq_fail_next = 0;
		transport_expired(T);
		summary_oracle(true);
	}
}

/* ⭐ THE CAPS ORACLE (15 Oct 2026): the two counters are the list's, and the caps hold. */

static void caps_oracle(const char *when)
{
	size_t n = 0, u = 0;
	for (connection *c = T->prime; c; c = c->upcoming) {
		n++;
		if (c->unlogged)
			u++;
		if (caps_exact && c->unlogged && !c->dead_run) {
			place k, k48;
			own_place(&rxq_reg_of(c->conn)->born, &k, &k48);
			if (own_from(&k, false) > cap_per_address(T))
				DIE("%s: %zu connections not logged in from one address, the cap is %zu",
				    when, own_from(&k, false), cap_per_address(T));
			if (own_from(&k48, true) > cap_per_48(T))
				DIE("%s: %zu connections not logged in from one /48, the cap is %zu",
				    when, own_from(&k48, true), cap_per_48(T));
		}
	}
	if (n != T->how_many)
		DIE("%s: how_many %zu, the list holds %zu", when, T->how_many, n);
	/* ⭐ the age: none alive and not logged in past UNLOGGED_MAX_S, none closed before */
	for (connection *c = T->prime; c; c = c->upcoming) {
		rxq_reg *r = rxq_reg_of(c->conn);
		if (c->unlogged && !c->dead_run &&
		    rxq_now_ns - r->born_ns >= (uint64_t)UNLOGGED_MAX_S * NGTCP2_SECONDS)
			DIE("%s: a connection not logged in %llu ms after its birth is still alive",
			    when, (unsigned long long)((rxq_now_ns - r->born_ns) / 1000000u));
	}
	for (size_t k = 0; k < rxq_nconns; k++)
		if (rxq_conns[k].aged &&
		    rxq_conns[k].aged_ns - rxq_conns[k].born_ns < (uint64_t)UNLOGGED_MAX_S * NGTCP2_SECONDS)
			DIE("%s: a connection closed for its age %llu ms after its birth", when,
			    (unsigned long long)((rxq_conns[k].aged_ns - rxq_conns[k].born_ns) / 1000000u));
	if (u != T->unlogged)
		DIE("%s: unlogged %zu, the list holds %zu not logged in", when, T->unlogged, u);
	if (caps_exact && live_count(T) > cap_conns(T))
		DIE("%s: %zu connections, the cap is %zu", when, live_count(T), cap_conns(T));
	if (caps_exact && pending_count(T) > cap_pending(T))
		DIE("%s: %zu pending, the cap is %zu", when, pending_count(T), cap_pending(T));
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	rx_ops o;
	uint8_t op;
	const uint8_t *a;
	size_t n;

	if (size < 1)
		return 0;
	v6 = data[0] & 1;
	addresses();
	rxq_reset();
	rxq_rng_seed(data[0] >> 1);
	set_time(1000000);
	qhead = qtail = 0;
	send_fail_left = recv_eintr = recv_err = 0;
	no_pktinfo = gsn_fail = false;
	last_dcidlen = 0;
	births = 0;
	kept_next = kept_n = dropped_next = 0;
	memset(dropped, 0, sizeof dropped);
	forgotten_expected = forgotten_reported = 0;
	flood_n = 0;
	rxq_on_birth = on_birth;
	src_refuse_left = 0;
	memset(&refused_pkt, 0, sizeof refused_pkt);
	rx_event_line = on_event_line;
	birth_line_next = birth_lines = 0;

	T = calloc(1, sizeof *T);
	T->fd = -1;
	T->family = v6 ? AF_INET6 : AF_INET;
	for (size_t i = 0; i < sizeof T->secret; i++)
		T->secret[i] = (uint8_t)(0x5a ^ i);
	places_agree();
	T->max_conns = 6;
	T->max_pending = 5;
	T->per_address = 3;
	T->per_48 = 4;
	caps_exact = true;

	o.d = data + 1;
	o.n = size - 1;
	o.i = 0;
	while (rx_next(&o, &op, &a, &n)) {
		uint8_t sel = op >> 5;
		switch (op & 0x1f) {
		case 0:
			op_new(a, n);
			break;
		case 1:
			op_pkt(sel, a, n);
			break;
		case 2:
			if (n > 1) {
				enqueue(a + 1, n - 1, a[0] % 4, 0);
				transport_read(T);
			}
			break;
		case 3: {
			uint64_t ms = n >= 2 ? ((uint64_t)a[0] << 8 | a[1]) : n ? a[0] : 1;
			if (sel & 1)
				ms *= 256;
			advance_ms(ms);
			(void)wait_oracle(transport_wait_ms(T));
			transport_expired(T);
			summary_oracle(true);
			break;
		}
		case 4:
			op_wt(sel, a, n);
			break;
		case 5: {
			uint64_t ticket = rx_u32(a, n);
			rxq_reg *r = pick(sel);
			if ((sel & 1) && r)
				ticket = r->wt_ticket;
			(void)transport_verdict(T, ticket, n > 4 && (a[4] & 1), n > 4 && (a[4] & 2));
			break;
		}
		case 6:
			(void)transport_dismiss_all(T, n ? a[0] : 0x0C, "server shutting down (fuzz)");
			(void)transport_remain_reason(T);
			break;
		case 7:
			transport_write(T);
			break;
		case 8: {
			static const int E[4] = {EAGAIN, EINTR, EPERM, ENOBUFS};
			uint8_t a0 = n > 0 ? a[0] : 0, a1 = n > 1 ? a[1] : 0, a2 = n > 2 ? a[2] : 0,
			        a3 = n > 3 ? a[3] : 0;
			src_refuse_left = a3 & 7;
			src_refuse_errno = (a3 & 8) ? EINVAL : EADDRNOTAVAIL;
			send_fail_left = a0 & 7;
			send_errno = E[(a0 >> 3) & 3];
			if (send_errno == EINTR && send_fail_left > 1)
				send_fail_left = 1;
			recv_eintr = a1 & 1;
			recv_err = (a1 >> 1) & 1;
			no_pktinfo = a2 & 1;
			gsn_fail = (a2 >> 1) & 1;
			break;
		}
		case 9:
			op_ng(sel, a, n);
			break;
		case 10:
			transport_read(T);
			break;
		case 11:
			(void)transport_count(T);
			(void)transport_fd(T);
			(void)wait_oracle(transport_wait_ms(T));
			transport_context(T, T->ctx);
			break;
		case 12: {
			size_t mc = n > 0 ? a[0] % 20 : 0, mp = n > 1 ? a[1] % 20 : 0,
			       pa = n > 2 ? a[2] % 10 : 0, p48 = n > 3 ? a[3] % 10 : 0;
			transport_limits(T, mc, mp, pa, p48);
			{
				unsigned big = (n > 4 && (a[4] & 1)) ? 1000000u : 0;
				struct hs_limits def = HS_LIMITS_DEFAULT, up = { 1000000u, 1000000u, 1000000u, 1000000u, 1000000u, 1000000u };

				T->hs_lim = big ? up : def;
			}
			for (connection *c = T->prime; c; c = c->upcoming) {
				place k, k48;
				if (!c->unlogged || c->dead_run)
					continue;
				own_place(&rxq_reg_of(c->conn)->born, &k, &k48);
				if (own_from(&k, false) > cap_per_address(T) ||
				    own_from(&k48, true) > cap_per_48(T))
					caps_exact = false;
			}
			if (live_count(T) > cap_conns(T) || pending_count(T) > cap_pending(T))
				caps_exact = false;
			break;
		}
		case 13:
			op_burst(a, n);
			break;
		case 14:
			op_flood(a, n);
			break;
		}
		caps_oracle("after an op");
		summary_oracle(false);
		if (refused_pkt.valid && !refused_pkt.retried)
			DIE("the kernel refused the source address of a packet of %zu bytes, and it was "
			    "never sent again without one", refused_pkt.len);
		/* the logged-in mark the stub's eviction / age oracle reads: sticky (a login is
		 * never undone; `reap_dead()` clears `unlogged` of a DEAD one only) */
		for (connection *c = T->prime; c; c = c->upcoming)
			if (!c->unlogged && !c->dead_run)
				rxq_reg_of(c->conn)->logged_in = true;
	}
	/* ⭐ every connection closes: both counters must come back to 0 through the real
	 *    release path (`reap_dead()`), not through `transport_close()` */
	for (connection *c = T->prime; c; c = c->upcoming)
		c->dead_run = true;
	reap_dead(T);
	caps_oracle("all closed");
	if (T->how_many != 0 || T->unlogged != 0)
		DIE("all closed, and how_many is %zu, unlogged %zu", T->how_many, T->unlogged);
	/* ⭐ the end of the process: everything is freed (a `wt` or a connection that leaks is
	 *    LeakSanitizer's) */
	transport_close(T);
	T = NULL;
	return 0;
}
