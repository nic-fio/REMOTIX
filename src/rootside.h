/*
 * rootside.h — ⭐ 1.5 (DECISIONS.md §11.11, §11.50): THE ROOT SIDE, AND THE
 *              NETWORK SIDE'S HANDLE ON IT.
 *
 * ---------------------------------------------------------------------------
 * ⛔ TWO PROCESSES, ONE BINARY, ONE CHANNEL
 *
 * systemd starts `remotix` as root, as in 1.0.  `main.c` parses its argv, binds
 * the UDP and TCP sockets of the port, and — when it runs as root — calls
 * `rootside_main()`, which never returns: that process is the ROOT SIDE (the
 * unit's main PID).  It runs the codec probe, starts the PAM helper (§1.10,
 * now its child), sweeps the render grants of a previous run, creates one
 * `SOCK_SEQPACKET` pair with `SO_PASSCRED`, and forks the NETWORK SIDE: in that
 * fork, still root, `walls_apply()` (src/walls.c) and then
 * `execve(/proc/self/exe <net_argv>)` with fd 3 = the channel, 4 = UDP, 5 = TCP.
 *
 * The network side (`main.c --network-side …`, uid `remotix`) calls
 * `rootside_attach(3)` before anything else and gets READY (the codec probe's
 * result).  From then on everything that needs root goes through the closed
 * list of `rootside_proto.h`, and NOTHING else:
 *
 *   · PAM          `helper_ask()` / `helper_move()` / `helper_expired()` keep
 *                  their shape (helper.h): in network mode they travel as
 *                  AUTH → VERDICT on this channel, and the helper itself is
 *                  the root side's child — the network side never sees it;
 *   · a child      `children_ensure_from()` keeps its shape (child.h): the
 *                  grant of the VERDICT is kept HERE, keyed by (user, rhost),
 *                  and sent as SPAWN; the child's socket end comes back by
 *                  `SCM_RIGHTS`.  A desktop found again without a login is a
 *                  CLOSE_ORPHAN (the root side checks logind by itself);
 *   · kill         SIGNAL {serial, TERM|KILL}, only to the root side's own;
 *   · reap         CHILD_EXITED {serial, wait status}: the root side reaps,
 *                  removes the render grant, then tells.
 *
 * ⛔ The root side is single-threaded and touches no GLib/GDBus: it forks
 *    children, and a fork of a multi-threaded process runs PAM and NSS in a
 *    copy whose locks may be held by a thread that is not there (inventory D,
 *    FLAG 2).  ⇒ `main.c` must call `rootside_main()` BEFORE anything that
 *    could start a GLib thread (`rediscover.c`'s `g_bus_get_sync`).
 * ---------------------------------------------------------------------------
 */
#ifndef REMOTIX_ROOTSIDE_H
#define REMOTIX_ROOTSIDE_H

#include "rediscover.h"
#include "rootside_proto.h"

#include <signal.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

/* ⭐ Review 4 B, finding 24: ONE reset of the signals for every fork of the
 *    root side's process (the network side, the PAM helper, the children, the
 *    usermod and probe forks): every disposition back to the default and
 *    nothing blocked.  This one keeps SIGPIPE IGNORED (the network side and the
 *    PAM helper: a write to a closed socket must be an EPIPE the code reads,
 *    not a death); the children and the usermod (`child.c`,
 *    `child_signals_default()`) get SIGPIPE at its default too — a child sets
 *    it ignored itself from its first instruction (`main.c`). */
static inline void rootside_fork_signals_fresh(void)
{
	sigset_t none;

	for (int s = 1; s < NSIG; s++)
		if (s != SIGKILL && s != SIGSTOP)
			signal(s, s == SIGPIPE ? SIG_IGN : SIG_DFL);
	sigemptyset(&none);
	sigprocmask(SIG_SETMASK, &none, NULL);
}

/* The descriptors the network side is born with (and nothing else above 2). */
#define ROOTSIDE_FD_CHANNEL 3
#define ROOTSIDE_FD_UDP     4
#define ROOTSIDE_FD_TCP     5

/* ⭐ What `main.c` hands the root side after parsing argv as root.  Every
 *    child option comes from HERE — the root side's own argv — never from a
 *    request of the network side (§11.50).  Pointers must stay valid for the
 *    life of the process (argv strings, statics). */
struct rootside_options {
	/* The port, bound by `main.c` as root (a port below 1024 needs no
	 * capability later).  Given to the network side as fd 4 and 5.  -1 = none
	 * (the network side then opens nothing on that protocol). */
	int udp_fd;
	int tcp_fd;
	/* The `remotix` user the network side becomes (sysusers.d).  `main.c`
	 * resolves it; the root side refuses to start if it is uid 0. */
	uid_t remotix_uid;
	gid_t remotix_gid;
	/* Children ≤ cap (`rcp_cap()` after `--session-cap`). */
	int cap;
	/* `children_turn_on()`'s birth options: the first canvas of every child,
	 * and the survey dir (`--dir-survey`, NULL or "" = none). */
	uint32_t canvas_w, canvas_h;
	const char *dir_survey;
	/* `children_phase9()`'s three. */
	bool quality_recovery;
	uint32_t bandwidth_cap_mbit;
	bool audio_silence;
	/* `--encoding-route` / `--render-node` as main.c already applied them
	 * (`child_encoding_route()`, `child_render_node()`): NULL = keep what is
	 * in force in this process.  Repeated on every child's command line. */
	const char *encoding_route;
	const char *render_node;
	/* The network side's argv for `execve(/proc/self/exe, net_argv, …)`,
	 * NULL-terminated, `net_argv[0]` included; `main.c` builds it from its own
	 * argv plus `--network-side`. */
	char *const *net_argv;
	/* NULL = "/etc/remotix/denied-users" (one name per line, `#` comments). */
	const char *denied_users_path;
	/* ⭐ For `walls_apply()` (lane 2): the only writable places of the network
	 *    side — `--network-state-dir` (default /var/lib/remotix/net) and
	 *    `--network-run-dir` (default /run/remotix/net). */
	const char *net_state_dir;
	const char *net_run_dir;
	/* ⭐ 1.5 (split audit R1): `--abandon-s` as main.c read it, in seconds.  The root side
	 * accepts CLOSE_ORPHAN for a uid only when no child of that uid has existed for this
	 * long (see `rootside_orphan_abandoned`); `0` = the abandonment clock is OFF, and then
	 * no CLOSE_ORPHAN is ever accepted (the network side does not ask either). */
	uint64_t abandon_s;
};

/* ⛔ The root side's entry: never returns while the service lives; the return
 *    value is the process's exit code (0 after a SIGTERM, 1 when it cannot
 *    start — the reason is logged). */
int rootside_main(const struct rootside_options *o);

/* ⭐ The network side's walls (lane 2, src/walls.c), applied by the root side
 *    in the fork, as root, before the `execve`.  0 = all applied; otherwise
 *    `why` says which failed and the network side is NOT started (no silent
 *    fallback, §11.50).  A weak stub in rootside.c refuses until walls.c is
 *    linked.
 * ⛔ SELinux (lane 4, module 2.0.0): the `setexeccon` for the network side
 *    belongs HERE, and is `getcon()` with ONLY the type replaced by
 *    `remotix_net_t` (the MLS range kept, e.g. `s0-s0:c0.c1023`); there is no
 *    type_transition on `remotix_exec_t`, so without it the exec stays
 *    `remotix_t`.  The root side's other execs (the PAM helper, the children)
 *    do NOT call setexeccon here: the helper stays `remotix_t`, the child gets
 *    the user's context from pam_selinux / `selinux_level_like_sshd()`.
 *    Emptying the bounding set and `PR_SET_NO_NEW_PRIVS` before the exec are
 *    allowed by the policy (setpcap, nnp_transition). */
int walls_apply(const struct rootside_options *o, char *why, size_t why_len);
/* What the last walls_apply() put in place, for one line (walls.c). */
const char *walls_in_force(void);

/* ======================================================================= */
/* THE NETWORK SIDE'S CLIENT                                                */

/* ⭐ Waits (blocking, at most `timeout_ms`) for READY on `fd` (3), checking it
 *    comes from uid 0 and the parent pid.  Fills `ready` (may be NULL).
 *    `true` = attached: from now on helper.c and child.c go through the
 *    channel. */
bool rootside_attach(int fd, int timeout_ms, struct rxr_ready *ready);
/* Whether this process is a network side attached to a root side. */
bool rootside_attached(void);
/* The channel, for the `poll`; -1 if not attached or lost. */
int rootside_descriptor(void);
/* ⛔ The root side is gone (EOF): the network side must stop (§11.50 —
 *    systemd restarts the unit; the desktops stay). */
bool rootside_lost(void);

/* ⭐ Reads every packet waiting on the channel and dispatches it to the hooks
 *    below (and to the SPAWN waiting in `rootside_spawn()`).  Never waits.
 *    Called by `helper_move()` in network mode; whoever polls the channel
 *    calls that. */
void rootside_move(void);

/* AUTH → the VERDICT reaches `on_verdict` (helper.c).  `request` = helper.c's
 * ticket.  On YES the grant is kept here, keyed by (user, rhost).  `false` =
 * not sent. */
bool rootside_auth(uint64_t request, const char *user, const char *password,
                   const char *rhost);
typedef void (*RootsideVerdict)(void *ctx, uint64_t request, int outcome);
void rootside_hook_verdict(RootsideVerdict fn, void *ctx);

/* What `rootside_spawn()` / `rootside_close_orphan()` hand back. */
struct rootside_born {
	uint64_t serial;
	pid_t pid;
	uid_t uid;
	gid_t gid;
	int fd;                       /* the child's socket end, O_NONBLOCK, SO_PASSCRED */
	char user[RXR_USER_MAX];
};
/* ⛔ SPAWN with the grant kept for (user, rhost) — consumed, single use.
 *    Waits for SPAWNED / SPAWN_REFUSED at most `timeout_ms` (the other packets
 *    arriving meanwhile are queued for `rootside_move()`): the root side
 *    answers right after its `fork()`, as `children_ensure_from()` returned
 *    in 1.0.  0 = born; otherwise an `enum rxr_refusal` (> 0), or one of the
 *    negative codes below — distinct since review 4 B (findings 2 and 19):
 *    a request that could not be sent no longer waits the whole timeout. */
#define ROOTSIDE_NO_ANSWER (-1)  /* no SPAWNED/SPAWN_REFUSED within timeout_ms */
#define ROOTSIDE_NO_GRANT  (-2)  /* no grant kept for (user, rhost) */
#define ROOTSIDE_NOT_SENT  (-3)  /* send() of the request failed */
#define ROOTSIDE_LOST      (-4)  /* the channel is closed or broke while waiting */
int rootside_spawn(const char *user, const char *rhost, uint32_t canvas_w,
                   uint32_t canvas_h, int timeout_ms, struct rootside_born *out);
/* The same for a desktop found again (CLOSE_ORPHAN): no grant. */
/* ⭐ 1.5 (R1): after a `RXR_REF_TOO_SOON` answer, how long (ms) the root side said to wait
 * (0 = never).  Valid until the next request. */
uint64_t rootside_last_wait_ms(void);
int rootside_close_orphan(const char *user, int timeout_ms,
                          struct rootside_born *out);
/* Whether a grant is kept for (user, rhost) now. */
bool rootside_has_grant(const char *user, const char *rhost);

/* SIGNAL: `sig` is SIGTERM or SIGKILL.  No answer. */
bool rootside_signal(uint64_t serial, int sig);
typedef void (*RootsideChildExited)(void *ctx, uint64_t serial, int wait_status);
void rootside_hook_child_exited(RootsideChildExited fn, void *ctx);

/* ⭐ 1.6 (R8) — the desktops found again, asked of the ROOT side (no /proc here).  Waits (blocking, at most `timeout_ms`)
 *    for FOUND_END, putting the other packets aside as `rootside_spawn()` does, then copies what FOUND_AGAIN brought into `v`
 *    (at most `cap`, `starttime` 0) and returns how many — or -1 with `why` if the root side could not look
 *    (RXR_FOUND_UNKNOWN), did not answer in time, or the channel is lost.  The list may already have arrived: then it
 *    returns at once. */
int rootside_wait_found(RediscoveredDesktop *v, int cap, int timeout_ms, char *why, size_t why_len);
/* FOUND_GONE (after FOUND_END), from `rootside_move()`.  `uid` and `user` are the desktop's. */
typedef void (*RootsideFoundGone)(void *ctx, uid_t uid, const char *user);
void rootside_hook_found_gone(RootsideFoundGone fn, void *ctx);

/* ⚠ For `children_turn_off()` only (after the last round of the loop): pumps
 *    the channel until `done(ctx)` or `timeout_ms`. */
void rootside_pump_until(bool (*done)(void *ctx), void *ctx, int timeout_ms);

/* ======================================================================= */
/* THE ROOT SIDE'S VALIDATOR — pure, exported for the seam test             */

struct rootside_peer {
	uid_t remotix_uid;
	pid_t net_pid;
};
/* ⛔ A packet from the network side: exact length for its kind, magic,
 *    version, a known network→root kind, and the kernel's credentials (present,
 *    uid remotix, pid the network side).  Returns the kind, or 0 = malformed
 *    (and `why` says what). */
int rootside_check_packet(const struct rootside_peer *p, const void *buf,
                          size_t len, bool has_cred, pid_t cred_pid,
                          uid_t cred_uid, char *why, size_t why_len);

/* ⭐ 1.6 (R8) — the ORDER of the root side's events about desktops found again, pure: READY, N × FOUND_AGAIN, one FOUND_END
 *    with count N, then FOUND_GONE.  The network side feeds every such packet through it; 0 = in order, -1 = the channel is
 *    broken (`why` says how).  `end_count`/`end_outcome` are read only for FOUND_END. */
enum { RXR_SEQ_BEFORE_READY = 0, RXR_SEQ_LISTING = 1, RXR_SEQ_LISTED = 2 };
struct rootside_found_seq {
	int phase;
	uint32_t seen;
};
int rootside_found_step(struct rootside_found_seq *s, int kind, uint32_t end_count, uint8_t end_outcome, char *why,
                        size_t why_len);

/* The grant table and the AUTH bounds, also pure (time is a parameter).
 * ROOTSIDE_GRANTS_MAX: a grant lives from its VERDICT to its SPAWN, about a
 * second in practice, at most RXR_GRANT_LIFE_MS; 32 is twice the AUTH that may
 * be in flight (RXR_AUTH_IN_FLIGHT_MAX), so a burst of right passwords fits.
 * `[?]` not measured at saturation; a full table REFUSES the mint (review 4,
 * finding 4), it never overwrites. */
#define ROOTSIDE_GRANTS_MAX 32
/* ROOTSIDE_ORPHAN_UIDS: the uids remembered for the per-uid CLOSE_ORPHAN hold;
 * one entry per desktop found again, and the children cap is 10 by default
 * (§11.50) — 32 leaves room for --session-cap up to it.  `[?]` */
#define ROOTSIDE_ORPHAN_UIDS 32
/* ROOTSIDE_EXIT_UIDS: the uids whose last child exit is remembered (R1); the cap of
 * children is 10 by default, so 32 holds many generations of users. */
#define ROOTSIDE_EXIT_UIDS 32
struct rootside_grant {
	bool used;
	uint8_t bytes[RXR_GRANT_BYTES];
	char user[RXR_USER_MAX];
	char rhost[RXR_RHOST_MAX];
	uint64_t expires_ms;
};
/* ⭐ 1.5 (split audit R2) — the BAN of the root side, for a network side that no longer
 * applies its own (`rcp.c`'s 5/12/30 live in the network side).  Counts only what PAM
 * answered REFUSED (outcome 0) or EXPIRED (4): never «not checked», never a yes.  Three
 * levels, the first two as rcp.c's, the third WIDER and SHORTER:
 *   · (uid, address)   5 refused in 5 min → no AUTH for that user from that address for 15 min,
 *                      then 1 h, then 12 h; forgotten after 24 h without a pause   (rcp.c LK_USER)
 *   · address         12 refused in 5 min → the same ladder, for any user          (rcp.c LK_KEY)
 *   · uid alone       15 refused in 5 min, from any addresses → no AUTH for that user for 15 min,
 *                      FIXED: it never grows and is never 12 h — a stranger who knows a name must
 *                      not be able to keep its owner out for good.  What a network side that
 *                      changes the address at every try still cannot do is pass 15 guesses.
 * The window is SLIDING.  A request in flight counts as a failure to come.  A successful login
 * clears that user's failures (both levels), not the recidivism, not the address's.  A paused
 * request gets «not checked» (the network side does not count it) and PAM is not asked.
 * ⛔ The tables never fail open: the uid table is the ground floor — when it has no place the
 * AUTH is refused (RXR_LOGIN_FULL).  When the (uid, address) or the address table has none,
 * that level is skipped and the uid level decides.
 * ⚠ These pauses live in the root side's memory: they do NOT survive its restart (rcp.c's ban
 * is written to a file).  And the global 3 AUTH/s (RXR_AUTH_PER_S) has no margin: eight users
 * logging in at once fit (burst 8), a ninth waits. */
#define ROOTSIDE_LOGIN_USERS 1024
#define ROOTSIDE_LOGIN_PAIRS 512
#define ROOTSIDE_LOGIN_HOSTS 128
#define ROOTSIDE_LOGIN_PAIR_LIMIT 5
#define ROOTSIDE_LOGIN_HOST_LIMIT 12
#define ROOTSIDE_LOGIN_USER_LIMIT 15
#define ROOTSIDE_LOGIN_USER_PAUSE_MS 900000u
#define ROOTSIDE_LOGIN_WINDOW_MS 300000u
#define ROOTSIDE_LOGIN_FORGET_MS 86400000u
/* the (uid, address) key is «<uid>|<rhost>»: a uid has at most 10 digits, the bar and the 0 make 12 */
#define ROOTSIDE_LOGIN_KEY_MAX (12 + RXR_RHOST_MAX)
struct rootside_fail {
	bool used;
	char key[ROOTSIDE_LOGIN_KEY_MAX];
	uint64_t times[ROOTSIDE_LOGIN_USER_LIMIT]; /* the last failures, oldest first */
	int n;
	int pending;                  /* AUTH asked to PAM, not answered */
	uint64_t until_ms;            /* paused until */
	int level;                    /* bans so far (1..3, the ladder stops at the third) */
	uint64_t last_ban_ms;
	uint64_t touched_ms;
};
struct rootside_bounds {
	struct rootside_grant grants[ROOTSIDE_GRANTS_MAX];
	int in_flight;                /* AUTH sent to PAM, not answered */
	double tokens;                /* RXR_AUTH_PER_S, burst RXR_AUTH_BURST */
	uint64_t tokens_ms;
	/* ⛔ Review 2, M1: CLOSE_ORPHAN is a birth without a password — its own
	 *    bucket (ROOTSIDE_ORPHAN_PER_S, burst ROOTSIDE_ORPHAN_BURST) BEFORE any
	 *    work, and one per uid per ROOTSIDE_ORPHAN_UID_MS. */
	double orphan_tokens;
	uint64_t orphan_tokens_ms;
	struct {
		uid_t uid;
		uint64_t at_ms;
	} orphan_uid[ROOTSIDE_ORPHAN_UIDS];
	/* ⭐ 1.5 (split audit R1): when the LAST child of a uid left, and the abandonment
	 *    the root side enforces.  See `rootside_orphan_abandoned()`. */
	uint64_t started_ms;          /* when these bounds were made: the root side's start */
	uint64_t abandon_ms;          /* 0 = clock off: CLOSE_ORPHAN is never accepted */
	uint64_t exits_forgot_ms;     /* the latest exit dropped from the table below */
	struct {
		uid_t uid;
		uint64_t at_ms;           /* 0 = free */
	} exits[ROOTSIDE_EXIT_UIDS];
	/* ⭐ 1.5 (split audit R2): the failures PAM really gave, per user and per address */
	struct rootside_fail users[ROOTSIDE_LOGIN_USERS];
	struct rootside_fail pairs[ROOTSIDE_LOGIN_PAIRS];
	struct rootside_fail hosts[ROOTSIDE_LOGIN_HOSTS];
};
/* ⛔ Review 2, M1: a CLOSE_ORPHAN is a birth without a password, so its rate is
 *    the abandonment's, not a login's — one desktop found again expires per
 *    clock round, and 2/s with a burst of 5 lets a restart with several
 *    abandoned desktops close them all in a few seconds (`[?]` not measured at
 *    more than one).  The per-uid 30 s is the close-only child's own life
 *    (CLOSE_ONLY_LIFE_MS, child.c): a second one for the same user while the
 *    first may still be closing would be a second logind session for nothing.
 *    `[M]` 16 Oct 2026, 24-privsep-orphan.sh: the hold refuses, and the
 *    network side's retry after 31 s closes the desktop. */
#define ROOTSIDE_ORPHAN_PER_S 2
#define ROOTSIDE_ORPHAN_BURST 5
#define ROOTSIDE_ORPHAN_UID_MS 30000
/* May a CLOSE_ORPHAN be looked at now?  `true` takes a token. */
bool rootside_orphan_admit(struct rootside_bounds *b, uint64_t now_ms);
/* … and one for this uid: `false` if one was born for it less than
 * ROOTSIDE_ORPHAN_UID_MS ago.  `true` records it. */
bool rootside_orphan_uid_admit(struct rootside_bounds *b, uid_t uid, uint64_t now_ms);
/* ⭐ 1.5 (split audit R1): a child of `uid` has just left (reaped by the root side). */
void rootside_exit_note(struct rootside_bounds *b, uid_t uid, uint64_t now_ms);
/* ⭐ 1.5 (split audit R1): may a CLOSE_ORPHAN for `uid` be accepted now?  Only if the uid
 * has had no child for at least `b->abandon_ms`, counted from its last exit, or — for a
 * desktop found again after the root side's own restart, whose exit nobody saw — from
 * the root side's start (or from the latest exit forgotten when the table was full: the
 * strictest of the two, never a shorter wait than the real one).  `*left_ms` (may be
 * NULL) = how much longer to wait; UINT64_MAX when the clock is off.  The network
 * side's own clock starts no earlier than this one, so an honest request is not refused
 * on a normal day. */
bool rootside_orphan_abandoned(const struct rootside_bounds *b, uid_t uid, uint64_t now_ms,
                               uint64_t *left_ms);
/* The largest `--abandon-s` the root side takes (one year): above it the sum with a time
 * would overflow, and a longer abandonment is the same as «never» for any real service. */
#define ROOTSIDE_ABANDON_S_MAX 31536000ull

enum rootside_login_result {
	RXR_LOGIN_OK = 0,
	RXR_LOGIN_PAIR_PAUSED,  /* this user from this address is in a pause */
	RXR_LOGIN_USER_PAUSED,  /* the user, from anywhere, is in the short pause */
	RXR_LOGIN_HOST_PAUSED,  /* the address is in a pause */
	RXR_LOGIN_PAIR_BUSY,    /* failures + AUTH in flight reach the limit: not yet a pause */
	RXR_LOGIN_USER_BUSY,
	RXR_LOGIN_HOST_BUSY,
	RXR_LOGIN_FULL,         /* the uid table has no place */
};
/* the levels an admitted attempt took a place in (the bits of `*taken`) */
#define RXR_LOGIN_L_USER 1u
#define RXR_LOGIN_L_PAIR 2u
#define RXR_LOGIN_L_HOST 4u
/* verdicts for `rootside_login_done()` */
enum { RXR_LOGIN_REFUSED = 0, RXR_LOGIN_ACCEPTED = 1, RXR_LOGIN_UNCHECKED = 2 };
struct rootside_login_event {
	bool user_ban, pair_ban, host_ban;       /* this failure started a pause */
	int pair_level, host_level;              /* the n-th pause of the ladder */
	uint64_t user_ms, pair_ms, host_ms;      /* … lasting this long */
};
/* May PAM be asked for this user (key: the uid in decimal) from this address?  `rhost` may
 * be empty.  `OK` takes a place in flight on the levels of `*taken` (never NULL): every OK is
 * followed by exactly one `rootside_login_done()` with the same `taken`.  `*left_ms` (may be
 * NULL): how long the pause still lasts, for the *_PAUSED answers. */
int rootside_login_admit(struct rootside_bounds *b, const char *ukey, const char *rhost,
                         uint64_t now_ms, uint64_t *left_ms, unsigned *taken);
/* The end of an attempt admitted above. `ev` (may be NULL) says whether it started a pause. */
void rootside_login_done(struct rootside_bounds *b, const char *ukey, const char *rhost,
                         uint64_t now_ms, unsigned taken, int verdict,
                         struct rootside_login_event *ev);
void rootside_bounds_init(struct rootside_bounds *b, uint64_t now_ms);
/* May this AUTH go to PAM now?  `false` = over the in-flight or rate bound
 * (VERDICT NOT_CHECKED).  `true` takes a token and a place in flight. */
bool rootside_auth_admit(struct rootside_bounds *b, uint64_t now_ms);
void rootside_auth_done(struct rootside_bounds *b);
/* Mints a grant (getrandom) for (user, rhost); `false` = no randomness. */
bool rootside_grant_mint(struct rootside_bounds *b, const char *user,
                         const char *rhost, uint64_t now_ms,
                         uint8_t out[RXR_GRANT_BYTES]);
/* ⛔ Consumes a grant: single use, unexpired.  Fills user/rhost.  `false` =
 *    unknown, used or expired. */
bool rootside_grant_take(struct rootside_bounds *b,
                         const uint8_t bytes[RXR_GRANT_BYTES], uint64_t now_ms,
                         char user[RXR_USER_MAX], char rhost[RXR_RHOST_MAX]);
/* ⛔ Names refused before PAM: uid 0, listed in `denied_path` (NULL = the
 *    default), or unknown.  0 = allowed (`*uid` filled, may be NULL) ·
 *    1 = refused · 2 = the lookup FAILED now (NSS down: «not checked»).
 *    `why` says which. */
int rootside_user_refused(const char *user, const char *denied_path, uid_t *uid,
                          char *why, size_t why_len);

#endif
