/*
 * rootside_proto.h — ⭐ 1.5 (DECISIONS.md §11.11, §11.50): THE CLOSED LIST BETWEEN
 *                    THE NETWORK SIDE AND THE ROOT SIDE.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT CROSSES, AND NOTHING ELSE
 *
 * One `SOCK_SEQPACKET` pair, `SO_PASSCRED` on both ends, created by the root
 * side before it forks the network side (fd 3 there).  Every message is ONE
 * packet of EXACTLY the size of its kind: a packet of any other length, an
 * unknown kind, a wrong magic or version is not «skipped» — the root side logs
 * it, closes the channel, kills the network side and starts it again (§11.50:
 * a hijacked network side is the attacker the root side is built against).
 *
 * ⛔ The root side checks the kernel's `SCM_CREDENTIALS` on EVERY packet: uid =
 *    `remotix`, pid = the network side it forked.  The network side checks uid
 *    0 and pid = its parent.
 *
 * Network side → root side: AUTH, SPAWN, CLOSE_ORPHAN, SIGNAL.  Nothing else.
 * Root side → network side: READY (once, first), VERDICT, SPAWNED (+ one fd by
 * `SCM_RIGHTS`: the child's socket end, the only fd that ever crosses),
 * SPAWN_REFUSED, CHILD_EXITED.
 *
 * ⚠ The structs are sent as they are, both sides being the same binary: the
 *    sender zeroes the whole struct first (`memset`) so no padding byte carries
 *    stack (the inventory found the helper's answer leaking 7 bytes, §11.50).
 * ---------------------------------------------------------------------------
 */
#ifndef ROOTSIDE_PROTO_H
#define ROOTSIDE_PROTO_H

#include <stdint.h>

#define RXR_MAGIC   0x31525852u   /* "RXR1" little-endian */
#define RXR_VERSION 1

#define RXR_USER_MAX     257      /* as helper.c's request */
#define RXR_PASSWORD_MAX 1025
#define RXR_RHOST_MAX    64       /* a bare IP literal, or empty */
#define RXR_GRANT_BYTES  16
#define RXR_CODEC_MAX    32       /* child_video_capabilities()'s `offered` */
#define RXR_EXPLAIN_MAX  1024     /* … and its `explanation` */

/* The root side's own bounds (§11.50, «a hijacked network side is the
 * attacker it is built against»): at most 16 AUTH in flight — the PAM helper's
 * own flight table (helper.c MAX_IN_FLIGHT 16), so the root side never asks it
 * more than it can hold — and 10 per second with a burst of 20, above which an
 * AUTH is refused without asking PAM (a dictionary attack through a hijacked
 * network side costs PAM nothing).  The grant lives 30 s: a right password is
 * followed by its SPAWN within the same login, `[M]` 1–14 ms (the «SPAWNED
 * after N ms» line); 30 s is the slack for a slow PAM session stack.  `[?]`
 * the rate is a decision, not a measurement. */
#define RXR_AUTH_IN_FLIGHT_MAX 16
#define RXR_AUTH_PER_S         10
#define RXR_AUTH_BURST         20
#define RXR_GRANT_LIFE_MS      30000

enum rxr_kind {
	/* network side → root side */
	RXR_AUTH          = 1,
	RXR_SPAWN         = 2,
	RXR_CLOSE_ORPHAN  = 3,
	RXR_SIGNAL        = 4,
	/* root side → network side */
	RXR_READY         = 101,
	RXR_VERDICT       = 102,
	RXR_SPAWNED       = 103,
	RXR_SPAWN_REFUSED = 104,
	RXR_CHILD_EXITED  = 105,
};

struct rxr_head {
	uint32_t magic;       /* RXR_MAGIC */
	uint16_t version;     /* RXR_VERSION */
	uint16_t kind;        /* enum rxr_kind */
	uint64_t request;     /* chosen by the network side; echoed in the answer.
	                       * 0 in events (READY, CHILD_EXITED). */
};

/* AUTH → VERDICT.  `request` plays the role of helper.c's ticket. */
struct rxr_auth {
	struct rxr_head h;
	char user[RXR_USER_MAX];
	char password[RXR_PASSWORD_MAX];
	char rhost[RXR_RHOST_MAX];
};

enum rxr_outcome {
	RXR_NO          = 0,  /* any refusal (as helper.c's 0) */
	RXR_YES         = 1,  /* the only yes; `grant` is filled */
	RXR_NO_LOCKED   = 2,  /* refused while pam_faillock held the account (§11.47) */
	RXR_NOT_CHECKED = 3,  /* the root side did not ask PAM: over its bounds, helper
	                       * down, timeout — «could not check», never counted
	                       * towards the ban (§11.39: 0x0E on the page) */
};

struct rxr_verdict {
	struct rxr_head h;
	uint8_t outcome;                  /* enum rxr_outcome */
	uint8_t grant[RXR_GRANT_BYTES];   /* single use, RXR_GRANT_LIFE_MS, bound to
	                                   * (user, rhost) of the AUTH; zero unless YES */
};

/* SPAWN → SPAWNED + fd | SPAWN_REFUSED.  The user and rhost are the grant's:
 * the network side cannot name anyone else. */
struct rxr_spawn {
	struct rxr_head h;
	uint8_t grant[RXR_GRANT_BYTES];
	uint32_t canvas_w, canvas_h;      /* bounded by the root side as main.c does */
};

/* CLOSE_ORPHAN → SPAWNED + fd | SPAWN_REFUSED.  Allowed only if the root side
 * itself finds in /run/systemd/sessions/ a live session of that user's uid
 * with SERVICE=remotix and no child of its own for it. */
struct rxr_close_orphan {
	struct rxr_head h;
	char user[RXR_USER_MAX];
};

enum rxr_signal { RXR_SIG_TERM = 1, RXR_SIG_KILL = 2 };

/* SIGNAL: no answer.  Only to a serial the root side forked and not yet reaped. */
struct rxr_signal_msg {
	struct rxr_head h;
	uint64_t serial;
	uint8_t sig;                      /* enum rxr_signal */
};

/* READY: the first packet, once, before the network side opens anything. */
struct rxr_ready {
	struct rxr_head h;
	uint32_t remotix_uid;             /* what the network side runs as, for its log */
	uint8_t codecs_ok;                /* child_video_capabilities()'s return */
	char offered[RXR_CODEC_MAX];
	char explanation[RXR_EXPLAIN_MAX];
};

struct rxr_spawned {
	struct rxr_head h;
	uint64_t serial;
	int32_t pid;
	uint32_t uid, gid;
	char user[RXR_USER_MAX];          /* the grant's user, for the network side's table */
};

enum rxr_refusal {
	RXR_REF_GRANT     = 1,  /* unknown, used, expired grant */
	RXR_REF_FULL      = 2,  /* the cap of the root side's argv */
	RXR_REF_USER      = 3,  /* uid 0, denied-users, name no longer resolves */
	RXR_REF_NO_ORPHAN = 4,  /* CLOSE_ORPHAN: no live remotix session of that uid */
	RXR_REF_FAILED    = 5,  /* socketpair/fork/PAM session/exec failed: see the root side's log */
	RXR_REF_CLOSING   = 6,  /* a child of that user is still being closed (child_outcome CHILD_CLOSING) */
	RXR_REF_MOVED     = 7,  /* the name now points to another uid (CHILD_NAME_MOVED) */
	RXR_REF_NAME_UNKNOWN = 8, /* ⭐ lane 1, 16 Oct 2026: the name could not be looked
	                           * up NOW (NSS failed) — CHILD_NAME_UNKNOWN, «retry» */
	RXR_REF_RATE      = 9,  /* ⭐ review 4 B, finding 22: over a rate bound (the CLOSE_ORPHAN
	                         * bucket, one per uid per 30 s) — it used to travel as FULL or
	                         * CLOSING, and the network side wrote the wrong reason */
};

struct rxr_spawn_refused {
	struct rxr_head h;
	uint8_t reason;                   /* enum rxr_refusal */
};

struct rxr_child_exited {
	struct rxr_head h;
	uint64_t serial;
	int32_t wait_status;              /* as waitpid(); the render grant is already removed */
};

#endif
