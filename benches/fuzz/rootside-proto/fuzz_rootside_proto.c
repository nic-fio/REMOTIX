/*
 * fuzz_rootside_proto.c — libFuzzer harness of the ROOT SIDE's request parser and bounds
 * (DECISIONS §11.11, §11.50; the contract is src/rootside_proto.h).
 *
 * ⛔ Why: after the split the attacker the root side is built against is a HIJACKED NETWORK SIDE —
 *    the process that parses the Internet's bytes, running as `remotix`.  Everything it can send
 *    the root side is one SEQPACKET packet plus the kernel's credentials.  This is
 *    `fuzz_helper_proto.c`'s direction REVERSED: there the untrusted party was the helper and the
 *    reader root; here the untrusted party is the asker (inventory G-tests.md §1.E, §3.3).
 *
 * ⭐ The seam is lane 1's PURE API (`rootside_check_packet`, the AUTH bounds, the grant table —
 *    src/rootside.h, «exported for the seam test»): no fork, no PAM, no socket.  Until the merge
 *    build.sh links `stub_rootside.c` (the contract alone) and says so; with src/rootside.c in the
 *    tree it links the REAL file, its other symbols stubbed to abort (as child-msg does).
 *
 *   ops (op & 7), the op stream of `common.h`:
 *     0  a RAW packet: arg[0] the credentials (bit0 present · bits1-2 pid: the network side,
 *        +1, 0, 1 · bits3-4 uid: remotix, 0, remotix+1, 65534), arg[1..] the packet, any length
 *     1  a WELL-FORMED packet with the right credentials: arg[0] the kind (the four requests, the
 *        five answers, an unknown), arg[1] one mutation (none, magic, version, length −1, +1,
 *        credentials off), arg[2..9] the request id, the rest overwrites the body (strings kept
 *        terminated)
 *     2  rootside_auth_admit()       3  rootside_auth_done()
 *     4  rootside_grant_mint(user \0 rhost from arg)
 *     5  rootside_grant_take(): arg[0] < 0xF0 picks a grant ever minted, else 16 free bytes
 *     6  time passes: u16 × 8 ms
 *
 * ⛔ THE ORACLES (abort() → a crash with its reproducer), from the contract only:
 *   · check_packet says a kind ONLY for a packet with credentials uid remotix and pid the network
 *     side, the magic, the version, a network→root kind (1-4) and EXACTLY that kind's size — an
 *     answer kind (101-105) sent as a request, an unknown kind, any other length ⇒ 0; and a 0
 *     comes with a terminated `why`;
 *   · a well-formed, unmutated request (op 1) IS accepted, as its own kind (a parser that refuses
 *     everything passes every safety oracle: this is the liveness one);
 *   · never more than RXR_AUTH_IN_FLIGHT_MAX admitted and not done; never more admitted than
 *     RXR_AUTH_BURST + RXR_AUTH_PER_S × the seconds elapsed;
 *   · a grant is taken ONLY if it was minted, never taken before, and is younger than
 *     RXR_GRANT_LIFE_MS — and it gives back the user and rhost it was minted for (bound to them).
 */
#include "common.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "rootside_api.h"

#define ORACLE(cond, ...)                                                              \
	do {                                                                           \
		if (!(cond)) {                                                         \
			fprintf(stderr, "RXFUZZ rootside oracle: " __VA_ARGS__);       \
			fprintf(stderr, "\n");                                         \
			abort();                                                       \
		}                                                                      \
	} while (0)

#define NET_PID   4242
#define RX_UID    991
#define MODEL_MAX 256

static const struct rootside_peer PEER = { .remotix_uid = RX_UID, .net_pid = NET_PID };

static size_t size_of(uint16_t kind)
{
	switch (kind) {
	case RXR_AUTH: return sizeof(struct rxr_auth);
	case RXR_SPAWN: return sizeof(struct rxr_spawn);
	case RXR_CLOSE_ORPHAN: return sizeof(struct rxr_close_orphan);
	case RXR_SIGNAL: return sizeof(struct rxr_signal_msg);
	default: return 0;
	}
}

static int expected_kind(const uint8_t *buf, size_t len, bool cred, pid_t pid, uid_t uid)
{
	struct rxr_head h;
	if (!cred || pid != NET_PID || uid != RX_UID || len < sizeof h)
		return 0;
	memcpy(&h, buf, sizeof h);
	if (h.magic != RXR_MAGIC || h.version != RXR_VERSION || !size_of(h.kind) || len != size_of(h.kind))
		return 0;
	return h.kind;
}

static void check(const uint8_t *buf, size_t len, bool cred, pid_t pid, uid_t uid, bool must_accept)
{
	char why[256];
	memset(why, 'x', sizeof why);
	int want = expected_kind(buf, len, cred, pid, uid);
	int got = rootside_check_packet(&PEER, buf, len, cred, pid, uid, why, sizeof why);
	if (got != 0)
		ORACLE(got == want, "accepted kind %d, the contract says %d (len %zu, cred %d pid %d uid %d)",
		       got, want, len, cred, (int)pid, (int)uid);
	else
		ORACLE(memchr(why, 0, sizeof why) != NULL, "a refusal without a terminated why");
	if (must_accept)
		ORACLE(got == want && want != 0, "a well-formed request of kind %d was refused: «%.*s»", want,
		       (int)sizeof why, why);
}

/* ── the model of the bounds and the grants ─────────────────────────────── */
struct mgrant {
	uint8_t bytes[RXR_GRANT_BYTES];
	char user[RXR_USER_MAX];
	char rhost[RXR_RHOST_MAX];
	uint64_t minted_ms;
	bool taken;
};
static struct rootside_bounds B;
static struct mgrant M[MODEL_MAX];
static int nm, in_flight;
static uint64_t admitted, t0;

static void op_packet_raw(const uint8_t *a, size_t n)
{
	static const pid_t pids[4] = { NET_PID, NET_PID + 1, 0, 1 };
	static const uid_t uids[4] = { RX_UID, 0, RX_UID + 1, 65534 };
	if (n == 0)
		return;
	check(a + 1, n - 1, a[0] & 1, pids[(a[0] >> 1) & 3], uids[(a[0] >> 3) & 3], false);
}

static void op_packet_good(const uint8_t *a, size_t n)
{
	static const uint16_t kinds[11] = { RXR_AUTH, RXR_SPAWN, RXR_CLOSE_ORPHAN, RXR_SIGNAL, RXR_READY,
	                                    RXR_VERDICT, RXR_SPAWNED, RXR_SPAWN_REFUSED, RXR_CHILD_EXITED,
	                                    0, 999 };
	union {
		struct rxr_head h;
		struct rxr_auth au;
		struct rxr_spawn sp;
		struct rxr_close_orphan co;
		struct rxr_signal_msg si;
		struct rxr_ready re;
		uint8_t raw[sizeof(struct rxr_ready) + sizeof(struct rxr_auth) + 8];
	} m;
	uint16_t kind = kinds[(n > 0 ? a[0] : 0) % 11];
	uint8_t mut = n > 1 ? a[1] % 6 : 0;
	size_t len = size_of(kind) ? size_of(kind) : sizeof(struct rxr_head) + 16;
	memset(&m, 0, sizeof m);
	m.h.magic = RXR_MAGIC;
	m.h.version = RXR_VERSION;
	m.h.kind = kind;
	for (size_t k = 0; k < 8 && 2 + k < n; k++)
		m.h.request = (m.h.request << 8) | a[2 + k];
	if (m.h.request == 0)
		m.h.request = 1;   /* 0 is the events' number (READY, CHILD_EXITED): a request never has it */
	if (n > 10) {
		size_t body = n - 10 < len - sizeof m.h ? n - 10 : len - sizeof m.h;
		memcpy(m.raw + sizeof m.h, a + 10, body);
	}
	if (kind == RXR_AUTH) {
		m.au.user[RXR_USER_MAX - 1] = m.au.password[RXR_PASSWORD_MAX - 1] = 0;
		m.au.rhost[RXR_RHOST_MAX - 1] = 0;
		if (!m.au.user[0])
			strcpy(m.au.user, "nic");
	} else if (kind == RXR_CLOSE_ORPHAN) {
		m.co.user[RXR_USER_MAX - 1] = 0;
		if (!m.co.user[0])
			strcpy(m.co.user, "nic");
	} else if (kind == RXR_SIGNAL) {
		m.si.sig = (m.si.sig & 1) ? RXR_SIG_KILL : RXR_SIG_TERM;
	}
	switch (mut) {
	case 1: m.h.magic ^= 1u << (n > 2 ? a[2] % 32 : 0); break;
	case 2: m.h.version++; break;
	case 3: len--; break;
	case 4: len++; break;
	}
	/* ⚠ request 0 is the events' number (rootside_proto.h: «0 in events»), and the root side
	 *   refuses it from the network side (rootside.c:128): not a well-formed REQUEST
	 *   ([M] 16 Oct 2026, campaign rehearsal: the 1-byte input 0x01 crashed this oracle). */
	check(m.raw, len, mut != 5, NET_PID, RX_UID,
	      mut == 0 && size_of(kind) != 0 && m.h.request != 0);
}

static void op_admit(void)
{
	bool ok = rootside_auth_admit(&B, rx_now_ms);
	if (!ok)
		return;
	ORACLE(in_flight < RXR_AUTH_IN_FLIGHT_MAX, "an AUTH admitted with %d already in flight", in_flight);
	in_flight++;
	admitted++;
	ORACLE((double)admitted <= RXR_AUTH_BURST + RXR_AUTH_PER_S * (double)(rx_now_ms - t0) / 1000.0 + 1e-6,
	       "%llu AUTH admitted in %llu ms: over the burst %d + %d/s", (unsigned long long)admitted,
	       (unsigned long long)(rx_now_ms - t0), RXR_AUTH_BURST, RXR_AUTH_PER_S);
}

static void op_done(void)
{
	if (in_flight == 0)
		return;
	rootside_auth_done(&B);
	in_flight--;
}

static void op_mint(const uint8_t *a, size_t n)
{
	char user[RXR_USER_MAX] = "", rhost[RXR_RHOST_MAX] = "";
	size_t k = 0, u = 0, r = 0;
	for (; k < n && a[k] && u < sizeof user - 1; k++)
		user[u++] = (char)a[k];
	for (; k < n && a[k]; k++)
		;
	for (k++; k < n && a[k] && r < sizeof rhost - 1; k++)
		rhost[r++] = (char)a[k];
	uint8_t out[RXR_GRANT_BYTES];
	if (!rootside_grant_mint(&B, user, rhost, rx_now_ms, out) || nm >= MODEL_MAX)
		return;
	memcpy(M[nm].bytes, out, sizeof out);
	memcpy(M[nm].user, user, sizeof user);
	memcpy(M[nm].rhost, rhost, sizeof rhost);
	M[nm].minted_ms = rx_now_ms;
	M[nm].taken = false;
	nm++;
}

static void op_take(const uint8_t *a, size_t n)
{
	uint8_t bytes[RXR_GRANT_BYTES] = { 0 };
	char user[RXR_USER_MAX], rhost[RXR_RHOST_MAX];
	if (n > 0 && a[0] < 0xF0 && nm > 0)
		memcpy(bytes, M[a[0] % nm].bytes, sizeof bytes);
	else if (n > 1)
		memcpy(bytes, a + 1, n - 1 < sizeof bytes ? n - 1 : sizeof bytes);
	memset(user, 0x55, sizeof user);
	memset(rhost, 0x55, sizeof rhost);
	if (!rootside_grant_take(&B, bytes, rx_now_ms, user, rhost))
		return;
	int k;
	for (k = 0; k < nm; k++)
		if (memcmp(M[k].bytes, bytes, sizeof bytes) == 0)
			break;
	ORACLE(k < nm, "a grant never minted was taken");
	ORACLE(!M[k].taken, "a grant was taken TWICE (single use)");
	ORACLE(rx_now_ms - M[k].minted_ms <= RXR_GRANT_LIFE_MS, "a grant taken %llu ms after its minting",
	       (unsigned long long)(rx_now_ms - M[k].minted_ms));
	ORACLE(memchr(user, 0, sizeof user) && strcmp(user, M[k].user) == 0, "the grant gave back another user");
	ORACLE(memchr(rhost, 0, sizeof rhost) && strcmp(rhost, M[k].rhost) == 0, "the grant gave back another rhost");
	M[k].taken = true;
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	rx_ops o = { data, size, 0 };
	uint8_t op;
	const uint8_t *arg;
	size_t argn;
	rx_now_ms = 1000000;
	t0 = rx_now_ms;
	rootside_bounds_init(&B, rx_now_ms);
	nm = in_flight = 0;
	admitted = 0;
	while (rx_next(&o, &op, &arg, &argn)) {
		switch (op & 7) {
		case 0: op_packet_raw(arg, argn); break;
		case 1: op_packet_good(arg, argn); break;
		case 2: op_admit(); break;
		case 3: op_done(); break;
		case 4: op_mint(arg, argn); break;
		case 5: op_take(arg, argn); break;
		case 6: rx_now_ms += (uint64_t)((argn > 1 ? (arg[0] << 8) | arg[1] : argn ? arg[0] : 1)) * 8; break;
		default: op_take(arg, argn); break;
		}
	}
	return 0;
}
