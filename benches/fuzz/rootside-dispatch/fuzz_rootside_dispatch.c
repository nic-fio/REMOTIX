/*
 * fuzz_rootside_dispatch.c — libFuzzer harness of the ROOT SIDE's channel, its whole reading
 * end (DECISIONS §11.50; the contract is src/rootside_proto.h): `chan_read()` →
 * `rootside_check_packet()` → AUTH / SPAWN / CLOSE_ORPHAN / SIGNAL, the PAM outcome
 * (`on_pam_outcome()` → VERDICT and the grant), the reaping (`reap_kids()` → CHILD_EXITED).
 *
 * ⛔ Why: after the split the attacker the root side is built against is a HIJACKED NETWORK SIDE.
 *    Everything it has is one SEQPACKET packet at a time plus the kernel's credentials.  A
 *    packet that made the root side give birth to a child for someone PAM did not admit — or
 *    signal a process it did not fork — is root handed over.
 *
 * ⭐ The seam: the REAL `src/rootside.c` is `#include`d, unmodified.  Its headers are included
 *    FIRST, then its root powers are interposed by macros, so only rootside.c's own calls see
 *    them:
 *      recvmsg / sendmsg   the channel: the harness's packet with the credentials it chose /
 *                          every answer recorded and checked
 *      kill / waitpid      fake processes: who is signalled is checked, deaths are the harness's
 *      child_birth         a fake birth: checked against the grant model, gives a pid and an fd
 *      helper_ask_bare     the PAM helper: a question recorded; the answer is an op
 *      getpwnam_r          five names (root, anna, bruno, carla; «nss» fails), denied: bruno
 *      render_grant_*      logind's «live remotix session» per uid is the harness's
 *      getrandom           a counter, so a reproducer replays
 *    No fork, no exec, no PAM.  The rest of rootside.c (rootside_main, net_start, the client)
 *    is never reached: its other calls are stubs that abort.
 *
 *   ops (op & 7), the op stream of `common.h`:
 *     0  a RAW packet: arg[0] the credentials (bit0 present · bits1-2 pid: the network side,
 *        +1, 0, 1 · bits3-4 uid: remotix, 0, remotix+1, 65534 · bit5 a descriptor attached),
 *        arg[1..] the packet, any length (up to sizeof(struct rxr_auth)+8)
 *     1  a WELL-FORMED request from the network side: arg[0] the kind (AUTH, SPAWN, CLOSE_ORPHAN,
 *        SIGNAL), arg[1] the user (% 5), arg[2] the rhost (% 3), arg[3] for SPAWN: < 0xC0 a
 *        grant from the model (arg[4] picks it), else 16 free bytes from arg[5..]; for SIGNAL
 *        < 0xC0 a serial ever born (arg[4]), else a free one; arg[5] the sig (1, 2, else as is)
 *     2  PAM answers a question in flight: arg[0] picks it, arg[1] % 4 the outcome (0 no, 1 yes,
 *        2 locked, 3 not checked)
 *     3  time passes: u16 × 16 ms
 *     4  a child dies: arg[0] picks a live one, then reap_kids()
 *     5  a new network side (if the channel was closed): a fresh channel, generation + 1
 *     6  logind: arg[0] % 5 the user, arg[1] bit0 has a live remotix session
 *     7  the next birth fails: arg[0] % 4 (none, FAILED, NAME_UNKNOWN, CLOSING)
 *   op 8+ (op & 15 ≥ 8):
 *     8  the network side dies: waitpid sees it, `reap_net()` (its children get their EOF grace)
 *     9  the next arg[0] % 4 sends fail (EAGAIN): a SPAWNED that cannot leave, CHILD_EXITED
 *        kept in the outbox
 *    10  a round of the loop's housekeeping: `outbox_flush()`, `kids_hurry()`
 *
 * ⛔ THE ORACLES (abort() → a crash with its reproducer):
 *   · a packet the contract calls malformed (wrong credentials, length, magic, version, kind,
 *     request 0, an unterminated string, a sig other than TERM/KILL, a descriptor) CLOSES the
 *     channel and SIGKILLs the network side — every time; a well-formed one keeps it open;
 *   · child_birth() for SPAWN only with a grant the root side minted on a PAM «yes», never used
 *     before, younger than RXR_GRANT_LIFE_MS, for EXACTLY its (user, rhost), and minted for the
 *     network side that sends it (the grants die with it); a close-only child at most once per
 *     user per ROOTSIDE_ORPHAN_UID_MS; for
 *     CLOSE_ORPHAN only for that packet's user, with logind showing its live remotix session;
 *     never for uid 0, a denied or an unknown name; never above the cap;
 *   · kill() only of a child the root side forked and has not reaped — for a SIGNAL, the one of
 *     that serial, born for the CURRENT network side; from `kids_hurry()`, only a child whose network side is DEAD (an older
 *     generation, or the current one after its death); at a birth, only that child (its
 *     SPAWNED could not leave) — or of the network side when it breaks the list or hangs;
 *   · a birth is `--close-only` exactly when it is a CLOSE_ORPHAN (the birth without a password);
 *   · PAM is asked only inside the bounds: ≤ RXR_AUTH_IN_FLIGHT_MAX unanswered, ≤ RXR_AUTH_BURST
 *     + RXR_AUTH_PER_S × seconds since the start; never for uid 0, denied or unknown names;
 *   · every answer the root side sends has its kind's exact size; a VERDICT YES only for a
 *     request whose PAM said yes, with a grant; VERDICT and SPAWNED/REFUSED echo a request the
 *     network side sent; SPAWNED carries one descriptor and the born child's serial;
 *     CHILD_EXITED only for a child of ours that died, once, only to the network side it was
 *     born for — sent at the reaping, or kept in the outbox and sent later, never lost while
 *     that network side lives.
 */
#include "common.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/prctl.h>

#include "child.h"
#include "helper.h"
#include "log.h"
#include "render_grant.h"
#include "rootside.h"

static ssize_t rxr_recvmsg(int fd, struct msghdr *m, int flags);
static ssize_t rxr_sendmsg(int fd, const struct msghdr *m, int flags);
static int rxr_kill(pid_t pid, int sig);
static pid_t rxr_waitpid(pid_t pid, int *st, int opt);
static child_outcome rxr_child_birth(const struct birth_opts *b, const char *user,
                                     const char *rhost, uint64_t serial, struct child_born *out);
static bool rxr_helper_ask_bare(helper *a, const char *user, const char *password,
                                const char *rhost, uint64_t now_ms, uint64_t *ticket);
static int rxr_getpwnam_r(const char *name, struct passwd *pw, char *buf, size_t n,
                          struct passwd **res);
static int rxr_session(uid_t uid);
static void rxr_grant_remove(const char *user, uid_t uid, gid_t gid);
static ssize_t rxr_getrandom(void *buf, size_t n, unsigned flags);

#define recvmsg rxr_recvmsg
#define sendmsg rxr_sendmsg
#define kill rxr_kill
#define waitpid rxr_waitpid
#define child_birth rxr_child_birth
#define helper_ask_bare rxr_helper_ask_bare
#define getpwnam_r rxr_getpwnam_r
#define render_grant_remotix_session rxr_session
#define render_grant_remove rxr_grant_remove
#define getrandom rxr_getrandom
#include "rootside.c" /* src/rootside.c, found through -I src */
#undef recvmsg
#undef sendmsg
#undef kill
#undef waitpid
#undef child_birth
#undef helper_ask_bare
#undef getpwnam_r
#undef render_grant_remotix_session
#undef render_grant_remove
#undef getrandom

#define ORACLE(cond, ...)                                                              \
	do {                                                                           \
		if (!(cond)) {                                                         \
			fprintf(stderr, "RXFUZZ rootside-dispatch oracle: " __VA_ARGS__); \
			fprintf(stderr, "\n");                                         \
			abort();                                                       \
		}                                                                      \
	} while (0)

/* ── the rest of rootside.c and what it links: never reached ───────────── */
#define NEVER(name) \
	do { fprintf(stderr, "RXFUZZ rootside-dispatch: reached " name "\n"); abort(); } while (0)
bool child_encoding_route(const char *r) { (void)r; NEVER("child_encoding_route"); }
bool child_render_node(const char *n) { (void)n; NEVER("child_render_node"); }
bool child_video_capabilities(char *o, size_t a, char *e, size_t b)
{ (void)o; (void)a; (void)e; (void)b; NEVER("child_video_capabilities"); }
void render_grant_sweep(void) { NEVER("render_grant_sweep"); }
/* ⭐ 1.6 (R8): net_start() looks for the desktops found again and watches their stages — never reached (the harness does not
 * start a network side; it only resets a generation) */
int rediscover_search_files(RediscoveredDesktop *v, int cap, char *why, size_t n)
{ (void)v; (void)cap; (void)why; (void)n; NEVER("rediscover_search_files"); }
bool rediscover_starttime(const char *r, pid_t p, unsigned long long *o)
{ (void)r; (void)p; (void)o; NEVER("rediscover_starttime"); }
/* the journal (676af717: net_start closes and reopens it around the fd moves) — never reached
 * here either, and stubs_log.c has no journal */
bool log_to_journal(void) { NEVER("log_to_journal"); }
bool log_journal(bool on) { (void)on; NEVER("log_journal"); }
helper *helper_turn_on_root(HelperOutcome cb, void *ctx) { (void)cb; (void)ctx; NEVER("helper_turn_on_root"); }
int helper_descriptor(const helper *a) { (void)a; NEVER("helper_descriptor"); }
void helper_move(helper *a, HelperVerdict d, void *c) { (void)a; (void)d; (void)c; NEVER("helper_move"); }
void helper_expired(helper *a, uint64_t n, HelperVerdict d, void *c)
{ (void)a; (void)n; (void)d; (void)c; NEVER("helper_expired"); }
void helper_turn_off(helper *a) { (void)a; NEVER("helper_turn_off"); }

/* ── the world ──────────────────────────────────────────────────────────── */
#define NET_PID 4242
#define RX_UID 977
#define CAP 4

static const struct { const char *name; uid_t uid; } USERS[5] = {
	{ "root", 0 }, { "anna", 1001 }, { "bruno", 1002 }, { "carla", 1003 }, { "nss", 1004 },
};
static const char *RHOSTS[3] = { "192.0.2.1", "2001:db8::7", "" };
static char denied_path[64];
static bool logind_live[5];

static struct rootside_options OPTS;

/* the packet the harness puts on the channel, read once by chan_read() */
static uint8_t pkt[sizeof(struct rxr_auth) + 8];
static size_t pkt_len;
static bool pkt_pending, pkt_cred, pkt_fd;
static pid_t pkt_pid;
static uid_t pkt_uid;

/* the model */
struct mgrant { bool used; uint8_t b[RXR_GRANT_BYTES]; char user[RXR_USER_MAX];
                char rhost[RXR_RHOST_MAX]; uint64_t minted; uint32_t gen; };
#define FUZZ_ABANDON_MS 1000 /* R1: the abandonment the harness gives the root side */
static uint64_t orphan_born_ms[5]; /* the last close-only birth per user */
/* R2: the model of the root side's pause — the times of the last 5 refusals (PAM's 0 or 4) per
 * user, cleared by a yes; PAM must not be asked while all 5 are inside the 5-minute window */
static uint64_t refused_ms[5][3][ROOTSIDE_LOGIN_PAIR_LIMIT]; /* per (user, address of RHOSTS) */
static int refused_n[5][3];
static int rhost_index(const char *rh)
{
	for (int i = 0; i < 3; i++)
		if (strcmp(RHOSTS[i], rh ? rh : "") == 0)
			return i;
	return 2;
}
static uint64_t last_exit_ms[5];   /* R1: when the user was last left without a child (the model) */
static struct mgrant grants[1024]; /* a ring: the root side keeps 32 */
static int ngrants;
struct mq { bool open; uint64_t ticket, request; char user[RXR_USER_MAX]; char rhost[RXR_RHOST_MAX];
            int outcome; };
static struct mq qs[64];
static int nqs;
struct mkid { bool alive, dead, exited_told; pid_t pid; uint64_t serial; uid_t uid;
             uint32_t gen; uint64_t orphan_ms; };
static struct mkid kids[64];
static int nkids;
static uint64_t requests_sent[4096]; /* a ring: AUTH has 16 in flight, so 4096 back is plenty */
static int nreq;
static uint64_t next_ticket = 1;
static pid_t next_pid = 20000;
static uint64_t rand_ctr;
static int fail_next_birth;
static int asked_in_flight, asked_total;
static uint64_t t_start;
static bool killed_net;
static int signal_for_serial_pid; /* the pid the current SIGNAL may hit, -1 none */
static int dev_null = -1;
static int fail_sends;
static bool fail_epipe; /* review 2, M2: the next failures are EPIPE (a reader that shut its end) */
static bool epiped;     /* an EPIPE was returned during the current step */
static bool net_dead;
static uint32_t dead_gen; /* the newest generation whose network side died (0 none) */
static char kill_ctx;     /* 'S' a SIGNAL, 'H' kids_hurry, 'B' a birth, 0 elsewhere */
static pid_t birth_pid;   /* the child just born, during its SPAWNED */

/* the packet being handled, for the oracles in the fakes */
static const uint8_t *cur;
static size_t cur_len;

static bool req_known(uint64_t r)
{
	for (int i = 0; i < nreq && i < 4096; i++)
		if (requests_sent[i] == r)
			return true;
	return false;
}

static int user_index(const char *name)
{
	for (int i = 0; i < 5; i++)
		if (strcmp(USERS[i].name, name) == 0)
			return i;
	return -1;
}

/* ── the fakes ──────────────────────────────────────────────────────────── */
static ssize_t rxr_recvmsg(int fd, struct msghdr *m, int flags)
{
	(void)flags;
	ORACLE(fd == R.chan && fd >= 0, "recvmsg on fd %d, the channel is %d", fd, R.chan);
	if (!pkt_pending) {
		errno = EAGAIN;
		return -1;
	}
	pkt_pending = false;
	size_t cap = m->msg_iov[0].iov_len;
	size_t n = pkt_len < cap ? pkt_len : cap;
	memcpy(m->msg_iov[0].iov_base, pkt, n);
	size_t ctl = 0;
	m->msg_flags = 0;
	if (pkt_cred) {
		struct cmsghdr *c = (struct cmsghdr *)m->msg_control;
		struct ucred u = { pkt_pid, pkt_uid, 0 };
		c->cmsg_level = SOL_SOCKET;
		c->cmsg_type = SCM_CREDENTIALS;
		c->cmsg_len = CMSG_LEN(sizeof u);
		memcpy(CMSG_DATA(c), &u, sizeof u);
		ctl += CMSG_SPACE(sizeof u);
	}
	if (pkt_fd) {
		struct cmsghdr *c = (struct cmsghdr *)((char *)m->msg_control + ctl);
		int d = dup(dev_null);
		c->cmsg_level = SOL_SOCKET;
		c->cmsg_type = SCM_RIGHTS;
		c->cmsg_len = CMSG_LEN(sizeof d);
		memcpy(CMSG_DATA(c), &d, sizeof d);
		ctl += CMSG_SPACE(sizeof d);
	}
	m->msg_controllen = ctl;
	return (ssize_t)pkt_len; /* MSG_TRUNC: the true length */
}

static size_t answer_size(int kind)
{
	switch (kind) {
	case RXR_READY: return sizeof(struct rxr_ready);
	case RXR_VERDICT: return sizeof(struct rxr_verdict);
	case RXR_SPAWNED: return sizeof(struct rxr_spawned);
	case RXR_SPAWN_REFUSED: return sizeof(struct rxr_spawn_refused);
	case RXR_CHILD_EXITED: return sizeof(struct rxr_child_exited);
	default: return 0;
	}
}

static ssize_t rxr_sendmsg(int fd, const struct msghdr *m, int flags)
{
	struct rxr_head h;
	const uint8_t *b = m->msg_iov[0].iov_base;
	size_t len = m->msg_iov[0].iov_len;
	int nfd = 0, the_fd = -1;

	(void)flags;
	ORACLE(fd == R.chan, "sendmsg on fd %d, not the channel %d", fd, R.chan);
	if (fail_sends > 0) {
		fail_sends--;
		errno = fail_epipe ? EPIPE : EAGAIN;
		epiped = epiped || fail_epipe;
		return -1;
	}
	ORACLE(len >= sizeof h, "an answer of %zu bytes", len);
	memcpy(&h, b, sizeof h);
	ORACLE(h.magic == RXR_MAGIC && h.version == RXR_VERSION, "an answer without magic/version");
	ORACLE(answer_size(h.kind) == len, "answer kind %u of %zu bytes", h.kind, len);
	if (m->msg_controllen) {
		const struct cmsghdr *c = (const struct cmsghdr *)m->msg_control;
		ORACLE(c->cmsg_type == SCM_RIGHTS && c->cmsg_len == CMSG_LEN(sizeof(int)),
		       "a control message that is not one descriptor");
		memcpy(&the_fd, CMSG_DATA(c), sizeof the_fd);
		nfd = 1;
	}
	ORACLE((nfd == 1) == (h.kind == RXR_SPAWNED), "kind %u with %d descriptors", h.kind, nfd);
	switch (h.kind) {
	case RXR_VERDICT: {
		struct rxr_verdict v;
		memcpy(&v, b, sizeof v);
		ORACLE(req_known(h.request), "VERDICT for request %llu never sent",
		       (unsigned long long)h.request);
		ORACLE(v.outcome <= RXR_OUTCOME_MAX, "VERDICT outcome %u", v.outcome);
		if (v.outcome == RXR_YES) {
			struct mq *q = NULL;
			for (int i = 0; i < nqs; i++)
				if (qs[i].request == h.request && qs[i].outcome == 1)
					q = &qs[i];
			ORACLE(q, "VERDICT YES for request %llu: PAM never said yes to it",
			       (unsigned long long)h.request);
			{
				struct mgrant *g = &grants[ngrants++ % 1024];
				memset(g, 0, sizeof *g);
				memcpy(g->b, v.grant, sizeof g->b);
				snprintf(g->user, sizeof g->user, "%s", q->user);
				snprintf(g->rhost, sizeof g->rhost, "%s", q->rhost);
				g->minted = rx_now_ms;
				g->gen = R.generation;
			}
			q->outcome = -1; /* one YES per yes */
		} else {
			static const uint8_t zero[RXR_GRANT_BYTES];
			ORACLE(memcmp(v.grant, zero, sizeof zero) == 0, "a NO carrying grant bytes");
		}
		break;
	}
	case RXR_SPAWNED: {
		struct rxr_spawned s;
		bool found = false;
		memcpy(&s, b, sizeof s);
		ORACLE(req_known(h.request), "SPAWNED for request %llu never sent",
		       (unsigned long long)h.request);
		for (int i = 0; i < nkids; i++)
			if (kids[i].serial == s.serial && kids[i].pid == s.pid && kids[i].alive)
				found = true;
		ORACLE(found, "SPAWNED serial %llu pid %d: not the child just born",
		       (unsigned long long)s.serial, s.pid);
		ORACLE(the_fd >= 0, "SPAWNED without the child's socket");
		break;
	}
	case RXR_SPAWN_REFUSED:
		ORACLE(req_known(h.request), "SPAWN_REFUSED for request %llu never sent",
		       (unsigned long long)h.request);
		break;
	case RXR_CHILD_EXITED: {
		struct rxr_child_exited e;
		int k = -1;
		memcpy(&e, b, sizeof e);
		for (int i = 0; i < nkids; i++)
			if (kids[i].serial == e.serial)
				k = i;
		ORACLE(k >= 0 && kids[k].dead && !kids[k].exited_told,
		       "CHILD_EXITED for serial %llu that did not die (or told twice)",
		       (unsigned long long)e.serial);
		ORACLE(kids[k].gen == R.generation, "CHILD_EXITED of generation %u to network side %u",
		       kids[k].gen, R.generation);
		kids[k].exited_told = true;
		break;
	}
	default:
		ORACLE(0, "the dispatcher sent kind %u", h.kind);
	}
	return (ssize_t)len;
}

static int rxr_kill(pid_t pid, int sig)
{
	if (pid == NET_PID) {
		ORACLE(sig == SIGKILL || sig == SIGTERM, "signal %d to the network side", sig);
		killed_net = true;
		return 0;
	}
	int k = -1;
	for (int i = 0; i < nkids; i++)
		if (kids[i].pid == pid)
			k = i;
	ORACLE(k >= 0, "kill(%d, %d): not a child the root side forked", pid, sig);
	ORACLE(kids[k].alive && !kids[k].dead, "kill(%d, %d): a child already dead/reaped", pid, sig);
	ORACLE(signal_for_serial_pid < 0 || signal_for_serial_pid == pid,
	       "SIGNAL hit pid %d, the serial's child is %d", pid, signal_for_serial_pid);
	ORACLE(kill_ctx == 'S' || kill_ctx == 'H' || kill_ctx == 'B',
	       "kill(%d, %d) outside SIGNAL, kids_hurry and a birth", pid, sig);
	ORACLE(kill_ctx != 'H' || (dead_gen && kids[k].gen <= dead_gen),
	       "kids_hurry signalled pid %d of generation %u, whose network side lives", pid,
	       kids[k].gen);
	ORACLE(kill_ctx != 'B' || pid == birth_pid, "a birth killed pid %d, not the child just born",
	       pid);
	return 0;
}

static pid_t rxr_waitpid(pid_t pid, int *st, int opt)
{
	(void)opt;
	if (pid == NET_PID) {
		if (!net_dead)
			return 0;
		net_dead = false;
		*st = 9; /* killed by SIGKILL */
		/* R1: the root side marks the children of that network side the moment it sees it die */
		for (int i = 0; i < nkids; i++)
			if (kids[i].alive && kids[i].gen == R.generation && !kids[i].orphan_ms)
				kids[i].orphan_ms = rx_now_ms ? rx_now_ms : 1;
		return pid;
	}
	for (int i = 0; i < nkids; i++)
		if (kids[i].pid == pid && kids[i].dead && kids[i].alive) {
			kids[i].alive = false; /* reaped */
			for (int u = 0; u < 5; u++)
				if (USERS[u].uid == kids[i].uid)
					last_exit_ms[u] = kids[i].orphan_ms ? kids[i].orphan_ms
					                                    : (rx_now_ms ? rx_now_ms : 1);
			*st = 7 << 8;
			return pid;
		}
	return 0;
}

static child_outcome rxr_child_birth(const struct birth_opts *b, const char *user,
                                     const char *rhost, uint64_t serial, struct child_born *out)
{
	struct rxr_head h;
	int ui = user_index(user);
	int live = 0;

	memcpy(&h, cur, sizeof h);
	ORACLE(ui > 0 && USERS[ui].uid != 0, "a birth for «%s» (uid 0 or unknown)", user);
	ORACLE(strcmp(user, "bruno") != 0, "a birth for bruno, who is in denied-users");
	ORACLE(strcmp(user, "nss") != 0, "a birth for a name NSS could not resolve");
	for (int i = 0; i < nkids; i++)
		live += kids[i].alive;
	ORACLE(live < CAP, "a birth above the cap (%d alive)", live);
	ORACLE(b && b->close_only == (h.kind == RXR_CLOSE_ORPHAN),
	       "a birth for kind %u with close_only %d", h.kind, b ? (int)b->close_only : -1);
	ORACLE(b && b->canvas_w >= 320 && b->canvas_h >= 240 && b->canvas_w <= 4096
	       && b->canvas_h <= 2304, "a canvas out of bounds reached the child");
	if (h.kind == RXR_SPAWN) {
		struct rxr_spawn s;
		int g = -1;
		memcpy(&s, cur, sizeof s);
		for (int i = 0; i < ngrants && i < 1024; i++)
			if (memcmp(grants[i].b, s.grant, RXR_GRANT_BYTES) == 0)
				g = i;
		ORACLE(g >= 0, "SPAWN with a grant the root side never minted");
		ORACLE(!grants[g].used, "SPAWN with a grant already used");
		ORACLE(rx_now_ms < grants[g].minted + RXR_GRANT_LIFE_MS, "SPAWN with an expired grant");
		ORACLE(grants[g].gen == R.generation,
		       "SPAWN by network side %u with a grant minted for network side %u", R.generation,
		       grants[g].gen);
		ORACLE(rhost && strcmp(grants[g].user, user) == 0 && strcmp(grants[g].rhost, rhost) == 0,
		       "SPAWN of «%s» from «%s» with a grant of «%s» from «%s»", user,
		       rhost ? rhost : "(null)", grants[g].user, grants[g].rhost);
		grants[g].used = true;
	} else {
		struct rxr_close_orphan c;
		ORACLE(h.kind == RXR_CLOSE_ORPHAN, "a birth while handling kind %u", h.kind);
		memcpy(&c, cur, sizeof c);
		ORACLE(!rhost && strcmp(c.user, user) == 0, "CLOSE_ORPHAN of «%s» gave birth to «%s»",
		       c.user, user);
		ORACLE(logind_live[ui], "CLOSE_ORPHAN of «%s» without its live remotix session", user);
		ORACLE(rx_now_ms >= (last_exit_ms[ui] > t_start ? last_exit_ms[ui] : t_start) + FUZZ_ABANDON_MS,
		       "CLOSE_ORPHAN of «%s» accepted %llu ms after the root side started (last exit of "
		       "that uid at %llu), under the abandon clock", user,
		       (unsigned long long)(rx_now_ms - t_start), (unsigned long long)last_exit_ms[ui]);
		ORACLE(!orphan_born_ms[ui] || rx_now_ms >= orphan_born_ms[ui] + ROOTSIDE_ORPHAN_UID_MS,
		       "a second close-only child for «%s» %llu ms after the first", user,
		       (unsigned long long)(rx_now_ms - orphan_born_ms[ui]));
		orphan_born_ms[ui] = rx_now_ms ? rx_now_ms : 1;
	}
	for (int i = 0; i < nkids; i++)
		ORACLE(!(kids[i].alive && kids[i].uid == USERS[ui].uid),
		       "a second child for uid %d", (int)USERS[ui].uid);
	if (fail_next_birth) {
		int f = fail_next_birth;
		fail_next_birth = 0;
		return f == 1 ? CHILD_FAILED : f == 2 ? CHILD_NAME_UNKNOWN : CHILD_CLOSING;
	}
	ORACLE(nkids < 64 || 1, "");
	if (nkids >= 64)
		return CHILD_FAILED;
	memset(out, 0, sizeof *out);
	out->pid = next_pid++;
	out->fd = dup(dev_null);
	out->uid = USERS[ui].uid;
	out->gid = USERS[ui].uid;
	snprintf(out->user, sizeof out->user, "%s", user);
	kids[nkids].alive = true;
	kids[nkids].dead = false;
	kids[nkids].exited_told = false;
	kids[nkids].pid = out->pid;
	kids[nkids].serial = serial;
	kids[nkids].uid = USERS[ui].uid;
	kids[nkids].gen = R.generation;
	kids[nkids].orphan_ms = 0;
	birth_pid = out->pid;
	nkids++;
	return CHILD_READY;
}

static bool rxr_helper_ask_bare(helper *a, const char *user, const char *password,
                                const char *rhost, uint64_t now_ms, uint64_t *ticket)
{
	struct rxr_head h;
	int ui = user_index(user);
	(void)a;
	(void)password;
	(void)now_ms;
	memcpy(&h, cur, sizeof h);
	ORACLE(h.kind == RXR_AUTH, "PAM asked while handling kind %u", h.kind);
	ORACLE(ui > 0 && strcmp(user, "bruno") != 0 && strcmp(user, "nss") != 0,
	       "PAM asked for «%s» (uid 0, denied, unknown or unresolvable)", user);
	asked_in_flight++;
	asked_total++;
	ORACLE(!(refused_n[ui][rhost_index(rhost)] == ROOTSIDE_LOGIN_PAIR_LIMIT
	         && rx_now_ms - refused_ms[ui][rhost_index(rhost)][0] <= ROOTSIDE_LOGIN_WINDOW_MS),
	       "PAM asked for «%s» from «%s» after %d refusals inside %d min (the root side's pause)",
	       user, rhost, ROOTSIDE_LOGIN_PAIR_LIMIT, ROOTSIDE_LOGIN_WINDOW_MS / 60000);
	ORACLE(asked_in_flight <= RXR_AUTH_IN_FLIGHT_MAX, "%d questions to PAM in flight",
	       asked_in_flight);
	ORACLE(asked_total <= RXR_AUTH_BURST + RXR_AUTH_PER_S * (int)((rx_now_ms - t_start) / 1000 + 1),
	       "%d questions to PAM in %llu ms", asked_total,
	       (unsigned long long)(rx_now_ms - t_start));
	struct mq *q = NULL;
	for (int i = 0; i < nqs && !q; i++)
		if (!qs[i].open && qs[i].outcome == -1)
			q = &qs[i]; /* an answered question's place */
	if (!q && nqs < 64)
		q = &qs[nqs++];
	ORACLE(q, "more than 64 questions open with 16 in flight");
	memset(q, 0, sizeof *q);
	q->open = true;
	q->ticket = next_ticket++;
	q->request = h.request;
	snprintf(q->user, sizeof q->user, "%s", user);
	snprintf(q->rhost, sizeof q->rhost, "%s", rhost);
	q->outcome = -1;
	*ticket = q->ticket;
	return true;
}

static int rxr_getpwnam_r(const char *name, struct passwd *pw, char *buf, size_t n,
                          struct passwd **res)
{
	int ui = user_index(name);
	(void)buf;
	(void)n;
	*res = NULL;
	if (ui == 4)
		return EIO; /* «nss»: the lookup FAILS */
	if (ui < 0)
		return 0;
	memset(pw, 0, sizeof *pw);
	pw->pw_name = (char *)USERS[ui].name;
	pw->pw_uid = USERS[ui].uid;
	pw->pw_gid = USERS[ui].uid;
	*res = pw;
	return 0;
}

static int rxr_session(uid_t uid)
{
	for (int i = 0; i < 5; i++)
		if (USERS[i].uid == uid)
			return logind_live[i] ? 1 : 0;
	return 0;
}

static void rxr_grant_remove(const char *user, uid_t uid, gid_t gid) { (void)user; (void)uid; (void)gid; }

static ssize_t rxr_getrandom(void *buf, size_t n, unsigned flags)
{
	(void)flags;
	for (size_t i = 0; i < n; i++)
		((uint8_t *)buf)[i] = (uint8_t)((++rand_ctr * 0x9E3779B97F4A7C15ull) >> 56);
	return (ssize_t)n;
}

/* ── the expected verdict of the contract on one packet ─────────────────── */
static bool contract_ok(void)
{
	struct rxr_head h;
	size_t want = 0;
	if (!pkt_cred || pkt_pid != NET_PID || pkt_uid != RX_UID || pkt_fd || pkt_len < sizeof h)
		return false;
	memcpy(&h, pkt, sizeof h);
	if (h.magic != RXR_MAGIC || h.version != RXR_VERSION || h.request == 0)
		return false;
	switch (h.kind) {
	case RXR_AUTH: want = sizeof(struct rxr_auth); break;
	case RXR_SPAWN: want = sizeof(struct rxr_spawn); break;
	case RXR_CLOSE_ORPHAN: want = sizeof(struct rxr_close_orphan); break;
	case RXR_SIGNAL: want = sizeof(struct rxr_signal_msg); break;
	default: return false;
	}
	if (pkt_len != want)
		return false;
	if (h.kind == RXR_AUTH) {
		const struct rxr_auth *a = (const void *)pkt;
		if (!memchr(a->user, 0, sizeof a->user) || !memchr(a->password, 0, sizeof a->password)
		    || !memchr(a->rhost, 0, sizeof a->rhost))
			return false;
	} else if (h.kind == RXR_CLOSE_ORPHAN) {
		const struct rxr_close_orphan *c = (const void *)pkt;
		if (!memchr(c->user, 0, sizeof c->user))
			return false;
	} else if (h.kind == RXR_SIGNAL) {
		const struct rxr_signal_msg *s = (const void *)pkt;
		if (s->sig != RXR_SIG_TERM && s->sig != RXR_SIG_KILL)
			return false;
	}
	return true;
}

static void deliver(void)
{
	bool ok = contract_ok();
	struct rxr_head h;

	if (R.chan < 0)
		return; /* no network side: nothing reads */
	memset(&h, 0, sizeof h);
	if (pkt_len >= sizeof h)
		memcpy(&h, pkt, sizeof h);
	if (h.request)
		requests_sent[nreq++ % 4096] = h.request;
	signal_for_serial_pid = -1;
	if (ok && h.kind == RXR_SIGNAL) {
		struct rxr_signal_msg s;
		memcpy(&s, pkt, sizeof s);
		signal_for_serial_pid = 0; /* no child: no kill allowed */
		for (int i = 0; i < nkids; i++)
			if (kids[i].serial == s.serial && kids[i].alive && !kids[i].dead
			    && kids[i].gen == R.generation)
				signal_for_serial_pid = kids[i].pid;
	}
	cur = pkt;
	cur_len = pkt_len;
	killed_net = false;
	epiped = false;
	pkt_pending = true;
	kill_ctx = h.kind == RXR_SIGNAL ? 'S' : h.kind == RXR_SPAWN || h.kind == RXR_CLOSE_ORPHAN ? 'B' : 0;
	birth_pid = -1;
	chan_read();
	kill_ctx = 0;
	pkt_pending = false;
	signal_for_serial_pid = -1;
	if (ok && epiped) {
		/* review 2, M2: a send that said EPIPE closes the channel and kills */
		ORACLE(R.chan < 0 && killed_net, "an EPIPE on the channel did not close it and kill "
		       "the network side");
	} else if (ok) {
		ORACLE(R.chan >= 0, "a well-formed request (kind %u, %zu bytes) closed the channel",
		       h.kind, pkt_len);
	} else {
		ORACLE(R.chan < 0 && killed_net,
		       "a malformed packet (kind %u, %zu bytes, cred %d pid %d uid %d fd %d) did not "
		       "close the channel and kill the network side",
		       h.kind, pkt_len, pkt_cred, (int)pkt_pid, (int)pkt_uid, pkt_fd);
	}
}

static void setup(void)
{
	memset(&R, 0, sizeof R);
	R.chan = R.pipe_r = R.pipe_w = -1;
	if (dev_null < 0)
		dev_null = open("/dev/null", O_RDWR | O_CLOEXEC);
	if (!denied_path[0]) {
		snprintf(denied_path, sizeof denied_path, "/tmp/rxfuzz-denied-%d", (int)getpid());
		FILE *f = fopen(denied_path, "w");
		if (f) {
			fprintf(f, "# denied\nbruno\n");
			fclose(f);
		}
	}
	memset(&OPTS, 0, sizeof OPTS);
	OPTS.remotix_uid = RX_UID;
	OPTS.cap = CAP;
	OPTS.canvas_w = 1920;
	OPTS.canvas_h = 1080;
	OPTS.denied_users_path = denied_path;
	R.o = &OPTS;
	R.cap = CAP;
	R.kids = calloc(CAP, sizeof *R.kids);
	R.outbox = calloc(CAP * 4, sizeof *R.outbox);
	R.nout = 0;
	fail_sends = 0;
	fail_epipe = false;
	net_dead = false;
	dead_gen = 0;
	kill_ctx = 0;
	R.next_serial = 1;
	R.pam = (helper *)&OPTS; /* never dereferenced: helper_ask_bare is the harness's */
	R.chan = dup(dev_null);
	R.net_pid = NET_PID;
	R.generation = 1;
	rootside_bounds_init(&R.bounds, rx_now_ms);
	R.bounds.abandon_ms = FUZZ_ABANDON_MS; /* R1: CLOSE_ORPHAN needs this much quiet */
	t_start = rx_now_ms;
	ngrants = nqs = nkids = nreq = 0;
	memset(orphan_born_ms, 0, sizeof orphan_born_ms);
	memset(last_exit_ms, 0, sizeof last_exit_ms);
	memset(refused_n, 0, sizeof refused_n);
	asked_in_flight = asked_total = 0;
	fail_next_birth = 0;
	memset(logind_live, 0, sizeof logind_live);
}

static void teardown(void)
{
	if (R.chan >= 0)
		close(R.chan);
	free(R.kids);
	R.kids = NULL;
	free(R.outbox);
	R.outbox = NULL;
}

static void build_request(const uint8_t *a, size_t n)
{
	uint8_t kind = n ? a[0] % 4 : 0;
	const char *user = USERS[(n > 1 ? a[1] : 1) % 5].name;
	const char *rhost = RHOSTS[(n > 2 ? a[2] : 0) % 3];
	static uint64_t req = 1000;

	memset(pkt, 0, sizeof pkt);
	pkt_cred = true;
	pkt_pid = NET_PID;
	pkt_uid = RX_UID;
	pkt_fd = false;
	switch (kind) {
	case 0: {
		struct rxr_auth x;
		memset(&x, 0, sizeof x);
		head_fill(&x.h, RXR_AUTH, ++req);
		snprintf(x.user, sizeof x.user, "%s", user);
		snprintf(x.password, sizeof x.password, "pw");
		snprintf(x.rhost, sizeof x.rhost, "%s", rhost);
		memcpy(pkt, &x, sizeof x);
		pkt_len = sizeof x;
		break;
	}
	case 1: {
		struct rxr_spawn x;
		memset(&x, 0, sizeof x);
		head_fill(&x.h, RXR_SPAWN, ++req);
		if (n > 3 && a[3] < 0xC0 && ngrants) {
			memcpy(x.grant, grants[(n > 4 ? a[4] : 0) % (ngrants < 1024 ? ngrants : 1024)].b,
			       RXR_GRANT_BYTES);
		} else {
			for (size_t k = 0; k < RXR_GRANT_BYTES && 5 + k < n; k++)
				x.grant[k] = a[5 + k];
		}
		x.canvas_w = n > 21 ? rx_u32(a + 21, n - 21) : 1280;
		x.canvas_h = n > 25 ? rx_u32(a + 25, n - 25) : 720;
		memcpy(pkt, &x, sizeof x);
		pkt_len = sizeof x;
		break;
	}
	case 2: {
		struct rxr_close_orphan x;
		memset(&x, 0, sizeof x);
		head_fill(&x.h, RXR_CLOSE_ORPHAN, ++req);
		snprintf(x.user, sizeof x.user, "%s", user);
		memcpy(pkt, &x, sizeof x);
		pkt_len = sizeof x;
		break;
	}
	default: {
		struct rxr_signal_msg x;
		memset(&x, 0, sizeof x);
		head_fill(&x.h, RXR_SIGNAL, ++req);
		if (n > 3 && a[3] < 0xC0 && nkids)
			x.serial = kids[(n > 4 ? a[4] : 0) % nkids].serial;
		else
			x.serial = n > 4 ? a[4] : 99;
		uint8_t sg = n > 5 ? a[5] : 1;
		x.sig = sg % 4 == 1 ? RXR_SIG_TERM : sg % 4 == 2 ? RXR_SIG_KILL : sg;
		memcpy(pkt, &x, sizeof x);
		pkt_len = sizeof x;
		break;
	}
	}
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	rx_ops o = { data, size, 0 };
	uint8_t op;
	const uint8_t *a;
	size_t n;
	static const pid_t PIDS[4] = { NET_PID, NET_PID + 1, 0, 1 };
	static const uid_t UIDS[4] = { RX_UID, 0, RX_UID + 1, 65534 };

	setup();
	while (rx_next(&o, &op, &a, &n)) {
		switch (op & 15) {
		case 0: {
			uint8_t c = n ? a[0] : 1;
			pkt_cred = c & 1;
			pkt_pid = PIDS[(c >> 1) & 3];
			pkt_uid = UIDS[(c >> 3) & 3];
			pkt_fd = (c >> 5) & 1;
			pkt_len = n > 1 ? n - 1 : 0;
			if (pkt_len > sizeof pkt)
				pkt_len = sizeof pkt;
			memset(pkt, 0, sizeof pkt);
			if (pkt_len)
				memcpy(pkt, a + 1, pkt_len);
			deliver();
			break;
		}
		case 1:
			build_request(a, n);
			deliver();
			break;
		case 2: {
			int open_n = 0, pick, k = -1;
			for (int i = 0; i < nqs; i++)
				open_n += qs[i].open;
			if (!open_n)
				break;
			pick = (n ? a[0] : 0) % open_n;
			for (int i = 0; i < nqs && k < 0; i++)
				if (qs[i].open && pick-- == 0)
					k = i;
			int outc = (n > 1 ? a[1] : 1) % 4;
			qs[k].open = false;
			qs[k].outcome = outc;
			asked_in_flight--;
			cur = NULL;
			{
				int ui_ = user_index(qs[k].user), ri_ = rhost_index(qs[k].rhost);

				if (ui_ >= 0) {
					if (outc == 1) {
						refused_n[ui_][ri_] = 0;
					} else if (outc == 0 || outc == 4) {
						if (refused_n[ui_][ri_] == ROOTSIDE_LOGIN_PAIR_LIMIT) {
							memmove(refused_ms[ui_][ri_], refused_ms[ui_][ri_] + 1,
							        (ROOTSIDE_LOGIN_PAIR_LIMIT - 1) * sizeof refused_ms[0][0][0]);
							refused_n[ui_][ri_]--;
						}
						refused_ms[ui_][ri_][refused_n[ui_][ri_]++] = rx_now_ms;
					}
				}
			}
			on_pam_outcome(NULL, qs[k].ticket, outc, qs[k].user, qs[k].rhost);
			qs[k].outcome = -1; /* answered: a later VERDICT YES for it is no longer PAM's */
			break;
		}
		case 3:
			rx_now_ms += 16u * (n >= 2 ? ((uint32_t)a[0] << 8 | a[1]) : n ? a[0] : 100);
			break;
		case 4: {
			int alive_n = 0, pick, k = -1;
			for (int i = 0; i < nkids; i++)
				alive_n += kids[i].alive && !kids[i].dead;
			if (alive_n) {
				pick = (n ? a[0] : 0) % alive_n;
				for (int i = 0; i < nkids && k < 0; i++)
					if (kids[i].alive && !kids[i].dead && pick-- == 0)
						k = i;
				kids[k].dead = true;
			}
			bool due[64] = { false };
			bool open_chan = R.chan >= 0;
			epiped = false;
			for (int i = 0; i < nkids; i++)
				due[i] = kids[i].dead && kids[i].alive;
			reap_kids();
			for (int i = 0; i < nkids; i++) {
				if (!due[i])
					continue;
				ORACLE(!kids[i].alive, "child %d died and was not reaped", kids[i].pid);
				/* told (or kept to be told) when its own network side is there; never
				 * otherwise */
				bool kept = false;
				for (int q = 0; q < R.nout; q++)
					kept = kept || R.outbox[q].serial == kids[i].serial;
				/* (an EPIPE while telling closes the channel: then nobody is told) */
				bool mine = open_chan && !epiped && kids[i].gen == R.generation;
				ORACLE(epiped || (mine ? (kids[i].exited_told || kept || R.nout >= CAP * 4)
				                       : (!kids[i].exited_told && !kept)),
				       "child %d reaped: CHILD_EXITED %s%s, its network side %s", kids[i].pid,
				       kids[i].exited_told ? "sent" : "not sent", kept ? " (kept)" : "",
				       mine ? "is there" : "is gone");
				kids[i].pid = -kids[i].pid; /* gone for good */
			}
			break;
		}
		case 5:
			if (R.chan < 0) {
				/* as net_start(): a fresh channel, a new generation, the outbox emptied */
				net_generation_reset(); /* net_start()'s own, before its fork */
				R.chan = dup(dev_null);
				R.generation++;
			}
			break;
		case 6:
			logind_live[(n ? a[0] : 1) % 5] = n > 1 ? (a[1] & 1) : 1;
			break;
		case 7:
			fail_next_birth = (n ? a[0] : 1) % 4;
			break;
		case 8:
			if (R.net_pid > 0) {
				net_dead = true;
				reap_net(rx_now_ms);
				if (R.net_pid == 0)
					dead_gen = R.generation;
				R.net_pid = NET_PID; /* the next network side has the same pid here */
				R.restart_at = 0;
			}
			break;
		case 9:
			fail_sends = (n ? a[0] : 1) % 4;
			fail_epipe = n && (a[0] & 4);
			break;
		default:
			if (R.chan >= 0) {
				int before = R.nout;
				outbox_flush();
				ORACLE(R.nout <= before, "the outbox grew while flushing");
			}
			kill_ctx = 'H';
			kids_hurry(rx_now_ms);
			kill_ctx = 0;
			break;
		}
	}
	teardown();
	return 0;
}
