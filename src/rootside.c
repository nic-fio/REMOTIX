/*
 * rootside.c — ⭐ 1.5 (DECISIONS.md §11.11, §11.50): the root side, and the
 *              network side's client of it.
 *
 * The why, the process tree and the closed list are in `rootside.h` and
 * `rootside_proto.h`.  Here are the choices that can only be seen in the code.
 *
 * ⛔ THE ROOT SIDE IS BUILT AGAINST A HIJACKED NETWORK SIDE.  Everything that
 *    arrives on the channel is the attacker's until proven otherwise: the
 *    kernel's credentials on EVERY packet, the exact length of its kind, the
 *    strings terminated inside their arrays — and any packet that fails is
 *    not «skipped»: the channel is closed, the network side killed and started
 *    again.  A name reaches PAM only inside the bounds (16 in flight, 10/s
 *    burst 20), never for uid 0, a denied or an unknown name; a child is born
 *    only with a grant PAM's «yes» minted here (single use, 30 s, bound to
 *    the user and the address of the AUTH), or — CLOSE_ORPHAN — for a desktop
 *    logind itself shows alive.  Every option of the child is the root side's.
 *
 * ⛔ SINGLE-THREADED, NO GDBus: it forks the children (`child_birth()`), and a
 *    fork of a multi-threaded process runs PAM and NSS in a copy whose locks
 *    may be held by a thread that is not there.  The signals come in through a
 *    self-pipe; the reaping is by pid, never `waitpid(-1)` (the PAM helper and
 *    `usermod` reap their own).
 */
#include "rootside.h"

#include "child.h"
#include "helper.h"
#include "log.h"
#include "render_grant.h"

#include <arpa/inet.h>
#include <errno.h>
#include <sys/stat.h>
#include <dirent.h>
#include <fcntl.h>
#include <grp.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;

/* ⚠ ONE word: the log line is «time area [who] body» and the benches read the area as the
 *   first token (11-c9: «root side» was read as «root», 16 Oct 2026). */
#define LOG_ROOT "rootside"
#define DENIED_USERS_DEFAULT "/etc/remotix/denied-users"

/* The network side's restart pause: 1 s, 2 s, 4 s … 30 s (§11.50). */
#define NET_RESTART_FIRST_MS 1000
#define NET_RESTART_CAP_MS 30000
#define NET_STABLE_MS 60000
/* SIGTERM → the network side's farewell, at most this long (§11.50). */
#define STOP_WAIT_MS 5000
/* ⛔ Review of the split, findings 2 and 10: what is asked to die is made to.
 *    The network side closed its channel ⇒ SIGTERM, SIGKILL after
 *    NET_TERM_GRACE_MS.  The network side is dead ⇒ its children have
 *    KIDS_EOF_GRACE_MS to leave on the EOF (dismantling their stage), then
 *    SIGTERM, then SIGKILL after KIDS_TERM_GRACE_MS — a hung child would
 *    otherwise refuse every new birth of its user (`own_by_uid()`).  ⚠ Only
 *    the children: the desktops are not them, and stay (§11.50). */
#define NET_TERM_GRACE_MS 3000
#define KIDS_EOF_GRACE_MS 5000
#define KIDS_TERM_GRACE_MS 3000

/* ⭐ The weak stub: until `walls.c` is linked, the network side is NOT started
 *    — no silent fallback to a network side without walls (§11.50). */
__attribute__((weak)) int walls_apply(const struct rootside_options *o, char *why,
                                      size_t why_len)
{
	(void)o;
	snprintf(why, why_len, "walls.c is not linked into this binary");
	return -1;
}
__attribute__((weak)) const char *walls_in_force(void)
{
	return "";
}

/* ======================================================================= */
/* THE PURE HALF — the validator, the bounds, the grants, the names          */

static size_t size_of_request(int kind)
{
	switch (kind) {
	case RXR_AUTH:         return sizeof(struct rxr_auth);
	case RXR_SPAWN:        return sizeof(struct rxr_spawn);
	case RXR_CLOSE_ORPHAN: return sizeof(struct rxr_close_orphan);
	case RXR_SIGNAL:       return sizeof(struct rxr_signal_msg);
	default:               return 0;
	}
}

static bool terminated(const char *s, size_t cap)
{
	return memchr(s, 0, cap) != NULL;
}

int rootside_check_packet(const struct rootside_peer *p, const void *buf,
                          size_t len, bool has_cred, pid_t cred_pid,
                          uid_t cred_uid, char *why, size_t why_len)
{
	struct rxr_head h;
	size_t want;

	if (!has_cred) {
		snprintf(why, why_len, "no kernel credentials on the packet");
		return 0;
	}
	if (cred_uid != p->remotix_uid) {
		snprintf(why, why_len, "sent by uid %ld, not remotix (%ld)", (long)cred_uid,
		         (long)p->remotix_uid);
		return 0;
	}
	if (cred_pid != p->net_pid) {
		snprintf(why, why_len, "sent by pid %ld, not the network side (%ld)",
		         (long)cred_pid, (long)p->net_pid);
		return 0;
	}
	if (len < sizeof h) {
		snprintf(why, why_len, "%zu bytes, shorter than a header", len);
		return 0;
	}
	memcpy(&h, buf, sizeof h);
	if (h.magic != RXR_MAGIC || h.version != RXR_VERSION) {
		snprintf(why, why_len, "wrong magic or version (%08x v%u)", h.magic, h.version);
		return 0;
	}
	want = size_of_request(h.kind);
	if (!want) {
		snprintf(why, why_len, "kind %u is not a request of the closed list", h.kind);
		return 0;
	}
	if (len != want) {
		snprintf(why, why_len, "kind %u of %zu bytes instead of %zu", h.kind, len, want);
		return 0;
	}
	if (h.request == 0) {
		snprintf(why, why_len, "kind %u with request number 0", h.kind);
		return 0;
	}
	if (h.kind == RXR_AUTH) {
		const struct rxr_auth *a = (const struct rxr_auth *)buf;
		if (!terminated(a->user, sizeof a->user) || !terminated(a->password, sizeof a->password)
		    || !terminated(a->rhost, sizeof a->rhost)) {
			snprintf(why, why_len, "AUTH with a string not terminated in its array");
			return 0;
		}
	} else if (h.kind == RXR_CLOSE_ORPHAN) {
		const struct rxr_close_orphan *c = (const struct rxr_close_orphan *)buf;
		if (!terminated(c->user, sizeof c->user)) {
			snprintf(why, why_len, "CLOSE_ORPHAN with a name not terminated in its array");
			return 0;
		}
	} else if (h.kind == RXR_SIGNAL) {
		const struct rxr_signal_msg *s = (const struct rxr_signal_msg *)buf;
		if (s->sig != RXR_SIG_TERM && s->sig != RXR_SIG_KILL) {
			snprintf(why, why_len, "SIGNAL %u is neither TERM nor KILL", s->sig);
			return 0;
		}
	}
	return h.kind;
}

void rootside_bounds_init(struct rootside_bounds *b, uint64_t now_ms)
{
	memset(b, 0, sizeof *b);
	b->tokens = RXR_AUTH_BURST;
	b->tokens_ms = now_ms;
	b->orphan_tokens = ROOTSIDE_ORPHAN_BURST;
	b->orphan_tokens_ms = now_ms;
	b->started_ms = now_ms;
}

bool rootside_auth_admit(struct rootside_bounds *b, uint64_t now_ms)
{
	if (now_ms > b->tokens_ms) {
		b->tokens += (double)(now_ms - b->tokens_ms) * RXR_AUTH_PER_S / 1000.0;
		if (b->tokens > RXR_AUTH_BURST)
			b->tokens = RXR_AUTH_BURST;
		b->tokens_ms = now_ms;
	}
	if (b->in_flight >= RXR_AUTH_IN_FLIGHT_MAX || b->tokens < 1.0)
		return false;
	b->tokens -= 1.0;
	b->in_flight++;
	return true;
}

bool rootside_orphan_admit(struct rootside_bounds *b, uint64_t now_ms)
{
	if (now_ms > b->orphan_tokens_ms) {
		b->orphan_tokens += (double)(now_ms - b->orphan_tokens_ms) * ROOTSIDE_ORPHAN_PER_S
		                    / 1000.0;
		if (b->orphan_tokens > ROOTSIDE_ORPHAN_BURST)
			b->orphan_tokens = ROOTSIDE_ORPHAN_BURST;
		b->orphan_tokens_ms = now_ms;
	}
	if (b->orphan_tokens < 1.0)
		return false;
	b->orphan_tokens -= 1.0;
	return true;
}

bool rootside_orphan_uid_admit(struct rootside_bounds *b, uid_t uid, uint64_t now_ms)
{
	int k = -1;

	for (int i = 0; i < ROOTSIDE_ORPHAN_UIDS; i++) {
		bool live = b->orphan_uid[i].at_ms
		            && now_ms < b->orphan_uid[i].at_ms + ROOTSIDE_ORPHAN_UID_MS;

		if (live && b->orphan_uid[i].uid == uid)
			return false;
		if (!live && k < 0)
			k = i;
	}
	/* ⛔ All the holds live: REFUSED, never one evicted (lane 1's pre-release
	 *    review, 16 Oct 2026).  Before, the OLDEST was replaced — a run of
	 *    CLOSE_ORPHANs for 32 other uids, inside the bucket, freed a user's hold
	 *    within ~16 s and gave that user a second close-only child, as the
	 *    grants' finding 4 of review 4. */
	if (k < 0)
		return false;
	b->orphan_uid[k].uid = uid;
	b->orphan_uid[k].at_ms = now_ms ? now_ms : 1;
	return true;
}

void rootside_exit_note(struct rootside_bounds *b, uid_t uid, uint64_t now_ms)
{
	int k = -1, oldest = 0;

	if (!now_ms)
		now_ms = 1;
	for (int i = 0; i < ROOTSIDE_EXIT_UIDS; i++) {
		if (b->exits[i].at_ms && b->exits[i].uid == uid) {
			b->exits[i].at_ms = now_ms;
			return;
		}
		if (!b->exits[i].at_ms) {
			if (k < 0)
				k = i;
		} else if (b->exits[i].at_ms < b->exits[oldest].at_ms || !b->exits[oldest].at_ms) {
			oldest = i;
		}
	}
	if (k < 0) {
		/* full: the OLDEST goes, and its time is kept as a floor for every uid that has no
		 * entry — a forgotten uid then waits at least as long as it really should */
		k = oldest;
		if (b->exits[k].at_ms > b->exits_forgot_ms)
			b->exits_forgot_ms = b->exits[k].at_ms;
	}
	b->exits[k].uid = uid;
	b->exits[k].at_ms = now_ms;
}

bool rootside_orphan_abandoned(const struct rootside_bounds *b, uid_t uid, uint64_t now_ms,
                               uint64_t *left_ms)
{
	uint64_t since = b->started_ms, due;

	if (left_ms)
		*left_ms = UINT64_MAX;
	if (!b->abandon_ms)
		return false;
	if (b->exits_forgot_ms > since)
		since = b->exits_forgot_ms;
	for (int i = 0; i < ROOTSIDE_EXIT_UIDS; i++)
		if (b->exits[i].at_ms && b->exits[i].uid == uid) {
			if (b->exits[i].at_ms > since)
				since = b->exits[i].at_ms;
			break;
		}
	due = since + b->abandon_ms;
	if (now_ms >= due)
		return true;
	if (left_ms)
		*left_ms = due - now_ms;
	return false;
}

void rootside_auth_done(struct rootside_bounds *b)
{
	if (b->in_flight > 0)
		b->in_flight--;
}

bool rootside_grant_mint(struct rootside_bounds *b, const char *user,
                         const char *rhost, uint64_t now_ms,
                         uint8_t out[RXR_GRANT_BYTES])
{
	int k = -1;

	for (int i = 0; i < ROOTSIDE_GRANTS_MAX; i++)
		if (!b->grants[i].used || b->grants[i].expires_ms <= now_ms) {
			k = i;
			break;
		}
	/* ⛔ all live: REFUSED, never another login's live grant overwritten
	 *    (review 4, finding 4 — before, the one closest to expiry went, and
	 *    that user's SPAWN was refused after a right password) */
	if (k < 0) {
		errno = ENOSPC;
		return false;
	}
	if (getrandom(out, RXR_GRANT_BYTES, 0) != RXR_GRANT_BYTES)
		return false;
	memset(&b->grants[k], 0, sizeof b->grants[k]);
	b->grants[k].used = true;
	memcpy(b->grants[k].bytes, out, RXR_GRANT_BYTES);
	snprintf(b->grants[k].user, sizeof b->grants[k].user, "%s", user);
	snprintf(b->grants[k].rhost, sizeof b->grants[k].rhost, "%s", rhost ? rhost : "");
	b->grants[k].expires_ms = now_ms + RXR_GRANT_LIFE_MS;
	return true;
}

bool rootside_grant_take(struct rootside_bounds *b,
                         const uint8_t bytes[RXR_GRANT_BYTES], uint64_t now_ms,
                         char user[RXR_USER_MAX], char rhost[RXR_RHOST_MAX])
{
	int hit = -1;

	for (int i = 0; i < ROOTSIDE_GRANTS_MAX; i++) {
		uint8_t diff = 0;

		if (!b->grants[i].used)
			continue;
		if (b->grants[i].expires_ms <= now_ms) {
			explicit_bzero(&b->grants[i], sizeof b->grants[i]);
			continue;
		}
		/* ⚠ Every byte compared, whatever the first says. */
		for (int j = 0; j < RXR_GRANT_BYTES; j++)
			diff |= (uint8_t)(b->grants[i].bytes[j] ^ bytes[j]);
		if (diff == 0)
			hit = i;
	}
	if (hit < 0)
		return false;
	snprintf(user, RXR_USER_MAX, "%s", b->grants[hit].user);
	snprintf(rhost, RXR_RHOST_MAX, "%s", b->grants[hit].rhost);
	/* ⛔ Single use: gone before the birth even starts. */
	explicit_bzero(&b->grants[hit], sizeof b->grants[hit]);
	return true;
}

/* 1 the name is listed · 0 it is not (or there is no file) · -1 the file
 * exists and cannot be read — and then nobody is let through (review 4 B,
 * finding 2: a deny list that could not be read let EVERY name pass, silently). */
static int listed_in(const char *path, const char *user)
{
	FILE *f = fopen(path, "re");
	char line[512];
	int hit = 0;

	if (!f)
		return errno == ENOENT ? 0 : -1;
	while (!hit && fgets(line, sizeof line, f)) {
		char *s = line, *e;

		while (*s == ' ' || *s == '\t')
			s++;
		if (*s == '#')
			continue;
		e = s + strcspn(s, " \t\r\n#");
		*e = 0;
		if (*s && strcmp(s, user) == 0)
			hit = 1;
	}
	if (!hit && ferror(f))
		hit = -1;
	fclose(f);
	return hit;
}

/* ⛔ A deny list that cannot be read FAILS CLOSED: every name is refused before
 *    PAM, with the reason.  ⚠ The line is the caller's own «refused» line, once
 *    per login asked — not a second one here. */
static int denied_check(const char *denied, const char *user, char *why, size_t why_len)
{
	int r = listed_in(denied, user);

	if (r < 0)
		snprintf(why, why_len, "the deny list %s cannot be read (%s): EVERY login is "
		         "refused until it can be", denied, strerror(errno ? errno : EIO));
	return r;
}

/* ⭐ As `child.c`'s `user_lookup()` (review of the split, finding 7): the
 *    buffer GROWS on `ERANGE` (1 → 4 → 16 → 64 KiB) — an entry that does not
 *    fit is neither «not found» nor «could not look».  ⚠ `*pw`'s strings live
 *    in this module's buffer until the next call (single-threaded). */
static int root_user_lookup(const char *name, struct passwd *pw, struct passwd **res)
{
	static char *buf;
	static size_t cap;
	int e;

	if (!buf) {
		buf = malloc(1024);
		if (!buf)
			return ENOMEM;
		cap = 1024;
	}
	for (;;) {
		char *bigger;

		*res = NULL;
		e = getpwnam_r(name, pw, buf, cap, res);
		if (e != ERANGE || cap >= 65536)
			return e;
		bigger = realloc(buf, cap * 4);
		if (!bigger)
			return e;
		buf = bigger;
		cap *= 4;
	}
}

int rootside_user_refused(const char *user, const char *denied_path, uid_t *uid,
                          char *why, size_t why_len)
{
	const char *denied = denied_path ? denied_path : DENIED_USERS_DEFAULT;
	struct passwd pw, *res = NULL;
	int e;

	if (!user || !user[0]) {
		snprintf(why, why_len, "an empty name");
		return 1;
	}
	switch (denied_check(denied, user, why, why_len)) {
	case 1:
		snprintf(why, why_len, "«%s» is in %s", user, denied);
		return 1;
	case -1:
		return 1;
	default:
		break;
	}
	e = root_user_lookup(user, &pw, &res);
	if (e != 0) {
		snprintf(why, why_len, "the name «%s» could not be looked up now (%s)", user,
		         strerror(e));
		return 2;
	}
	if (!res) {
		snprintf(why, why_len, "«%s» is not a user of this system", user);
		return 1;
	}
	if (pw.pw_uid == 0) {
		snprintf(why, why_len, "«%s» is uid 0", user);
		return 1;
	}
	/* ⛔ The name NSS gives back is checked too (review of the split,
	 *    finding 8): with sssd/LDAP case-insensitive, or an alias, «BRUNO»
	 *    resolves to «bruno» — and «bruno» is the name in the file. */
	if (strcmp(pw.pw_name, user) != 0 && denied_check(denied, pw.pw_name, why, why_len) < 0)
		return 1;
	if (strcmp(pw.pw_name, user) != 0 && listed_in(denied, pw.pw_name) == 1) {
		snprintf(why, why_len, "«%s» is «%s» for NSS, and «%s» is in %s", user,
		         pw.pw_name, pw.pw_name, denied);
		return 1;
	}
	if (uid)
		*uid = pw.pw_uid;
	why[0] = 0;
	return 0;
}

/* «» or a bare IPv4/IPv6 literal (an IPv6 zone after `%` allowed). */
static bool rhost_ok(const char *r)
{
	char v6[RXR_RHOST_MAX];
	unsigned char bin[16];
	const char *pct;

	if (!r[0])
		return true;
	if (inet_pton(AF_INET, r, bin) == 1)
		return true;
	snprintf(v6, sizeof v6, "%s", r);
	pct = strchr(v6, '%');
	if (pct) {
		for (const char *z = pct + 1; *z; z++)
			if (!((*z >= 'a' && *z <= 'z') || (*z >= 'A' && *z <= 'Z')
			      || (*z >= '0' && *z <= '9') || *z == '_' || *z == '-' || *z == '.'))
				return false;
		v6[pct - v6] = 0;
	}
	return inet_pton(AF_INET6, v6, bin) == 1;
}

/* ======================================================================= */
/* THE ROOT SIDE                                                             */

struct own_child {
	bool used;
	uint64_t serial;
	pid_t pid;
	uid_t uid;
	gid_t gid;
	bool render_grant;
	char user[64];
	uint32_t generation;  /* of the network side it was born for */
	uint64_t term_at;     /* ≠ 0: that network side is dead — SIGTERM then */
	uint64_t kill_at;     /* ≠ 0: SIGTERM sent — SIGKILL then */
};

struct pending_auth {
	bool used;
	uint64_t ticket;      /* the helper's */
	uint64_t request;     /* the network side's */
	uint32_t generation;  /* of the network side that asked */
};

static struct {
	const struct rootside_options *o;
	struct birth_opts birth;
	char my_path[512];
	int chan;
	pid_t net_pid;
	uint32_t generation;
	uint64_t net_born_ms;
	uint64_t restart_at;
	int deaths_in_row;
	helper *pam;
	struct rootside_bounds bounds;
	struct own_child *kids;
	int cap;
	uint64_t next_serial;
	struct pending_auth pending[RXR_AUTH_IN_FLIGHT_MAX * 2];
	int pipe_r, pipe_w;
	bool stopping;
	uint64_t stop_deadline;
	bool codecs_ok;
	char offered[RXR_CODEC_MAX];
	char explanation[RXR_EXPLAIN_MAX];
	uint64_t refused_logged_ms;
	uint32_t refused_hidden;
	uint64_t net_kill_at;   /* ≠ 0: SIGTERM sent on its EOF — SIGKILL then */
	uint64_t prepam_logged_ms;
	uint32_t prepam_hidden;
	struct rxr_child_exited *outbox; /* R.cap * 4 */
	int nout;
	uint64_t tables_ms;     /* the last «root side tables» line */
} R = { .chan = -1, .pipe_r = -1, .pipe_w = -1 };

static void on_signal(int s)
{
	unsigned char b = (unsigned char)s;
	int saved = errno;

	(void)!write(R.pipe_w, &b, 1);
	errno = saved;
}

static void head_fill(struct rxr_head *h, int kind, uint64_t request)
{
	h->magic = RXR_MAGIC;
	h->version = RXR_VERSION;
	h->kind = (uint16_t)kind;
	h->request = request;
}

/* ⛔ Never waits: a network side that does not read loses the packet, and
 *    the line says so — except CHILD_EXITED, kept in `R.outbox` and sent
 *    again (`outbox_flush()`). */
static void net_kill(const char *why);

static bool chan_try(const void *p, size_t len, int fd)
{
	struct msghdr m;
	struct iovec io = { (void *)p, len };
	union {
		struct cmsghdr c;
		char b[CMSG_SPACE(sizeof(int))];
	} ctl;
	ssize_t n;

	if (R.chan < 0)
		return false;
	memset(&m, 0, sizeof m);
	m.msg_iov = &io;
	m.msg_iovlen = 1;
	if (fd >= 0) {
		memset(&ctl, 0, sizeof ctl);
		m.msg_control = ctl.b;
		m.msg_controllen = sizeof ctl.b;
		struct cmsghdr *c = CMSG_FIRSTHDR(&m);
		c->cmsg_level = SOL_SOCKET;
		c->cmsg_type = SCM_RIGHTS;
		c->cmsg_len = CMSG_LEN(sizeof(int));
		memcpy(CMSG_DATA(c), &fd, sizeof fd);
	}
	n = sendmsg(R.chan, &m, MSG_NOSIGNAL | MSG_DONTWAIT);
	if (n != (ssize_t)len) {
		/* ⛔ Review 2, M2: a network side that shut its READING end
		 *    (`shutdown(SHUT_RD)`) leaves POLLOUT on for ever while every
		 *    send says EPIPE — with a CHILD_EXITED in the outbox that was a
		 *    silent 100 % CPU spin.  It will never read again: killed. */
		if (n < 0 && (errno == EPIPE || errno == ECONNRESET)) {
			int e = errno;
			net_kill("it shut the reading end of its channel (a send says EPIPE)");
			errno = e;
			return false;
		}
		if (n >= 0)
			errno = EMSGSIZE;
		return false;
	}
	return true;
}

static bool chan_send(const void *p, size_t len, int fd)
{
	static uint64_t logged_ms;
	static uint32_t hidden;
	uint64_t now;

	if (chan_try(p, len, fd))
		return true;
	if (R.chan < 0)
		return false;
	/* ⚠ One line per second at most, with the count (review 2, M2). */
	now = log_now_ms();
	hidden++;
	if (now >= logged_ms + 1000) {
		if (hidden > 1)
			registro_dice(LOG_ROOT, "⛔ a packet of kind %u to the network side did not "
			              "leave (%s) — and %u others in the last second, not written",
			              ((const struct rxr_head *)p)->kind, strerror(errno), hidden - 1);
		else
			registro_dice(LOG_ROOT, "⛔ a packet of kind %u to the network side did not "
			              "leave (%s)", ((const struct rxr_head *)p)->kind, strerror(errno));
		logged_ms = now;
		hidden = 0;
	}
	return false;
}

/* ⛔ CHILD_EXITED is never lost (review of the split, finding 4): a slot the
 *    network side never sees freed stays «exiting» for ever there.  What did
 *    not leave waits here, in order, and is sent again every round (and on
 *    POLLOUT); the network side it was for dead, the list is emptied — the
 *    next one does not know those serials.  At most 4 × the children cap. */
static void outbox_flush(void)
{
	int sent = 0;

	while (sent < R.nout && chan_try(&R.outbox[sent], sizeof R.outbox[sent], -1))
		sent++;
	if (sent > 0) {
		memmove(R.outbox, R.outbox + sent, (size_t)(R.nout - sent) * sizeof R.outbox[0]);
		R.nout -= sent;
	}
}

static void send_exited(const struct rxr_child_exited *e)
{
	if (R.chan < 0)
		return;
	outbox_flush();
	if (R.nout == 0 && chan_try(e, sizeof *e, -1))
		return;
	if (R.nout >= R.cap * 4) {
		/* ⛔ Review 4, finding 5: no longer LOST — a network side that does
		 *    not read its channel for 4 × the cap of deaths is treated like
		 *    one that broke the closed list: killed and started again, and
		 *    the new one knows none of those serials (its children see EOF,
		 *    the desktops are found again).  A lost CHILD_EXITED left that
		 *    slot «exiting» there for ever. */
		registro_dice(LOG_ROOT, "⛔⛔ CHILD_EXITED for serial %llu could not leave and %d "
		              "are already waiting: the network side does not read its channel",
		              (unsigned long long)e->serial, R.nout);
		net_kill("it left 4 × the cap of CHILD_EXITED unread");
		return;
	}
	if (R.nout == 0)
		registro_dice(LOG_ROOT, "⚠ CHILD_EXITED for serial %llu did not leave now (%s): "
		              "kept, and sent again", (unsigned long long)e->serial, strerror(errno));
	R.outbox[R.nout++] = *e;
}

static void send_refused(uint64_t request, int reason)
{
	struct rxr_spawn_refused r;

	memset(&r, 0, sizeof r);
	head_fill(&r.h, RXR_SPAWN_REFUSED, request);
	r.reason = (uint8_t)reason;
	(void)chan_send(&r, sizeof r, -1);
}

static void send_verdict(uint64_t request, int outcome, const uint8_t *grant)
{
	struct rxr_verdict v;

	memset(&v, 0, sizeof v);
	head_fill(&v.h, RXR_VERDICT, request);
	v.outcome = (uint8_t)outcome;
	if (outcome == RXR_YES && grant)
		memcpy(v.grant, grant, RXR_GRANT_BYTES);
	(void)chan_send(&v, sizeof v, -1);
	explicit_bzero(&v, sizeof v);
}

/* ⛔ The network side broke the closed list: the channel closes and it dies;
 *    `reap_net()` starts it again with the pause. */
static void net_kill(const char *why)
{
	registro_dice(LOG_ROOT,
	              "⛔⛔ the network side (pid %ld) broke the closed list: %s.  The "
	              "channel is closed and the network side is KILLED; it is started "
	              "again with the pause (DECISIONS.md §11.50)",
	              (long)R.net_pid, why);
	if (R.chan >= 0) {
		close(R.chan);
		R.chan = -1;
	}
	if (R.net_pid > 0)
		kill(R.net_pid, SIGKILL);
}

static void on_pam_outcome(void *ctx, uint64_t ticket, int outcome, const char *user,
                           const char *rhost)
{
	struct pending_auth *pa = NULL;
	uint8_t grant[RXR_GRANT_BYTES];
	int out;

	(void)ctx;
	for (size_t i = 0; i < sizeof R.pending / sizeof R.pending[0]; i++)
		if (R.pending[i].used && R.pending[i].ticket == ticket)
			pa = &R.pending[i];
	if (!pa) {
		log_detail(LOG_ROOT, "PAM's answer for ticket %llu finds no pending AUTH (its "
		           "place was never given, or the network side that asked is gone): dropped",
		           (unsigned long long)ticket);
		return;
	}
	pa->used = false;
	rootside_auth_done(&R.bounds);
	if (pa->generation != R.generation || R.chan < 0)
		return; /* asked by a network side that is gone */
	/* ⭐ D3 (7645beb7): outcome 4 is the root-form EXPIRY — an attempt without a verdict is not a free one, so it
	 *    travels as a plain NO (counted by the network side); 3 stays «not checked» (cap, death, helper down). */
	out = outcome == 1 ? RXR_YES : outcome == 2 ? RXR_NO_LOCKED
	                             : (outcome == 0 || outcome == 4) ? RXR_NO : RXR_NOT_CHECKED;
	if (out == RXR_YES
	    && !rootside_grant_mint(&R.bounds, user, rhost, log_now_ms(), grant)) {
		registro_dice(LOG_ROOT, "⛔ PAM said yes to «%s» but no grant could be minted "
		              "(%s): «not checked»", user,
		              errno == ENOSPC ? "the grant table is full of live grants"
		                              : strerror(errno));
		out = RXR_NOT_CHECKED;
	}
	if (out == RXR_YES)
		registro_dice(LOG_ROOT,
		              "⭐ PAM said YES to «%s»: a grant is minted — single use, %d s, "
		              "bound to «%s» from «%s»",
		              user, RXR_GRANT_LIFE_MS / 1000, user, rhost[0] ? rhost : "?");
	send_verdict(pa->request, out, out == RXR_YES ? grant : NULL);
	explicit_bzero(grant, sizeof grant);
}

static void handle_auth(struct rxr_auth *a)
{
	char why[256];
	uint64_t ticket = 0, now = log_now_ms();
	int r = -1;
	int out = -1;

	/* ⛔ The bounds FIRST (review of the split, finding 6): the denied file,
	 *    the NSS lookup (sssd/LDAP: the network) and a log line are work the
	 *    root side does for the asker, and a flood of «root» must cost what a
	 *    flood of passwords costs — refused without looking. */
	if (!rootside_auth_admit(&R.bounds, now)) {
		/* ⚠ A flood writes one line per second, with the count. */
		R.refused_hidden++;
		if (now >= R.refused_logged_ms + 1000) {
			registro_dice(LOG_ROOT,
			              "⛔ AUTH over the root side's bounds (%d in flight max, %d/s "
			              "burst %d): %u refused without asking PAM — «not checked», "
			              "NOT counted towards the ban",
			              RXR_AUTH_IN_FLIGHT_MAX, RXR_AUTH_PER_S, RXR_AUTH_BURST,
			              R.refused_hidden);
			R.refused_logged_ms = now;
			R.refused_hidden = 0;
		}
		out = RXR_NOT_CHECKED;
	} else if ((r = rootside_user_refused(a->user, R.o->denied_users_path, NULL, why,
	                                      sizeof why)) != 0
	           || !rhost_ok(a->rhost)) {
		rootside_auth_done(&R.bounds);
		if (r == 0)
			snprintf(why, sizeof why, "«%.200s» with an address that is not an IP literal",
			         a->user);
		out = r == 1 ? RXR_NO : RXR_NOT_CHECKED;
		/* ⚠ One line per second at most, with the count (as the bounds'). */
		R.prepam_hidden++;
		if (now >= R.prepam_logged_ms + 1000) {
			if (R.prepam_hidden > 1)
				registro_dice(LOG_ROOT, "⛔ AUTH %s BEFORE PAM: %s (and %u more in the "
				              "last second, not written)", r == 1 ? "refused" : "not checked",
				              why, R.prepam_hidden - 1);
			else
				registro_dice(LOG_ROOT, "⛔ AUTH %s BEFORE PAM: %s",
				              r == 1 ? "refused" : "not checked", why);
			R.prepam_logged_ms = now;
			R.prepam_hidden = 0;
		}
	} else if (!helper_ask_bare(R.pam, a->user, a->password, a->rhost, now, &ticket)) {
		rootside_auth_done(&R.bounds);
		out = RXR_NOT_CHECKED;
	} else {
		struct pending_auth *pa = NULL;
		for (size_t i = 0; i < sizeof R.pending / sizeof R.pending[0]; i++)
			if (!R.pending[i].used) {
				pa = &R.pending[i];
				break;
			}
		if (pa) {
			pa->used = true;
			pa->ticket = ticket;
			pa->request = a->h.request;
			pa->generation = R.generation;
		} else {
			/* ⚠ Cannot happen (32 places, 16 in flight); the helper's answer
			 *   then finds nothing and is dropped.  Said (review 4 B, 11). */
			registro_dice(LOG_ROOT, "⛔ no free place for the AUTH of request %llu (all %zu "
			              "in use, which the in-flight bound should prevent): «not checked»",
			              (unsigned long long)a->h.request,
			              sizeof R.pending / sizeof R.pending[0]);
			rootside_auth_done(&R.bounds);
			out = RXR_NOT_CHECKED;
		}
	}
	explicit_bzero(a->password, sizeof a->password);
	if (out >= 0)
		send_verdict(a->h.request, out, NULL);
}

static struct own_child *own_by_uid(uid_t uid)
{
	for (int i = 0; i < R.cap; i++)
		if (R.kids[i].used && R.kids[i].uid == uid)
			return &R.kids[i];
	return NULL;
}

/* The birth for SPAWN (`rhost` the grant's) and CLOSE_ORPHAN (`rhost` NULL). */
static void birth(uint64_t request, const char *user, const char *rhost, uint32_t w,
                  uint32_t h, bool orphan)
{
	char why[256];
	uid_t uid = 0;
	struct own_child *k = NULL;
	struct birth_opts b = R.birth;
	struct child_born c;
	struct rxr_spawned s;
	child_outcome o;
	int r = rootside_user_refused(user, R.o->denied_users_path, &uid, why, sizeof why);

	if (r != 0) {
		registro_dice(LOG_ROOT, "⛔ %s refused: %s", orphan ? "CLOSE_ORPHAN" : "SPAWN", why);
		send_refused(request, r == 2 ? RXR_REF_NAME_UNKNOWN : RXR_REF_USER);
		return;
	}
	if (own_by_uid(uid)) {
		registro_dice(LOG_ROOT, "⛔ %s for «%s» refused: a child of uid %ld is still "
		              "alive here (I2)", orphan ? "CLOSE_ORPHAN" : "SPAWN", user, (long)uid);
		send_refused(request, RXR_REF_CLOSING);
		return;
	}
	if (orphan && render_grant_remotix_session(uid) != 1) {
		registro_dice(LOG_ROOT, "⛔ CLOSE_ORPHAN for «%s» refused: logind shows no live "
		              "session of uid %ld with SERVICE=remotix", user, (long)uid);
		send_refused(request, RXR_REF_NO_ORPHAN);
		return;
	}
	/* ⭐ 1.6 (split audit R1): a desktop is closed only when it has really been abandoned —
	 *    the root side's own clock (`--abandon-s`, its last child's exit or its own start),
	 *    not the network side's word: a network side taken over could otherwise close the
	 *    desktop of anyone who had merely disconnected.  BEFORE the per-uid hold, so a
	 *    refusal here takes no hold. */
	if (orphan) {
		uint64_t left;

		if (!rootside_orphan_abandoned(&R.bounds, uid, log_now_ms(), &left)) {
			if (left == UINT64_MAX)
				registro_dice(LOG_ROOT, "⛔ CLOSE_ORPHAN for «%s» refused: the abandonment "
				              "clock is off (--abandon-s 0), no desktop is closed for "
				              "abandonment", user);
			else
				registro_dice(LOG_ROOT, "⛔ CLOSE_ORPHAN for «%s» refused: uid %ld has not "
				              "been without a client for %llu s yet (%llu s to go)", user,
				              (long)uid, (unsigned long long)(R.bounds.abandon_ms / 1000),
				              (unsigned long long)((left + 999) / 1000));
			send_refused(request, RXR_REF_TOO_SOON);
			return;
		}
	}
	/* ⛔ One CLOSE_ORPHAN per uid per 30 s (review 2, M1): CLOSE_ORPHAN →
	 *    SIGNAL KILL → reaped → CLOSE_ORPHAN was a new logind session each
	 *    round, for any user with a live desktop.  ⚠ AFTER logind's check (lane
	 *    1's pre-release review): a hold is taken only for a uid that really has
	 *    a remotix session, so names without one cannot fill the table. */
	if (orphan && !rootside_orphan_uid_admit(&R.bounds, uid, log_now_ms())) {
		registro_dice(LOG_ROOT, "⛔ CLOSE_ORPHAN for «%s» refused: one was already asked "
		              "for uid %ld less than %d s ago (or every hold of the table is in use)",
		              user, (long)uid, ROOTSIDE_ORPHAN_UID_MS / 1000);
		send_refused(request, RXR_REF_RATE);
		return;
	}
	for (int i = 0; i < R.cap; i++)
		if (!R.kids[i].used) {
			k = &R.kids[i];
			break;
		}
	if (!k) {
		registro_dice(LOG_ROOT, "⛔ %s for «%s» refused: %d children already (the cap)",
		              orphan ? "CLOSE_ORPHAN" : "SPAWN", user, R.cap);
		send_refused(request, RXR_REF_FULL);
		return;
	}
	/* ⛔ The canvas is the only number of the request that reaches the child:
	 *    out of the RCP bounds (rcp.h RCP_CANVAS_MIN_W/H 320×240, MAX_W/H
	 *    4096×2304 — the numbers repeated here so this file needs no rcp.h)
	 *    ⇒ the root side's own, and SAID (review 4 B, finding 4). */
	if (w < 320 || h < 240 || w > 4096 || h > 2304) {
		registro_dice(LOG_ROOT, "⚠ %s for «%s» asks a canvas %ux%u outside 320x240..4096x2304: "
		              "the child is born at the root side's own %ux%u",
		              orphan ? "CLOSE_ORPHAN" : "SPAWN", user, w, h, R.o->canvas_w,
		              R.o->canvas_h);
		w = R.o->canvas_w;
		h = R.o->canvas_h;
	}
	b.canvas_w = w;
	b.canvas_h = h;
	/* ⛔ The birth without a password is a child that can only close the
	 *    desktop (`--close-only`, review of the split, finding 1): the root
	 *    side's choice here, never a field of the request. */
	b.close_only = orphan;
	uint64_t t0 = log_now_ms();
	o = child_birth(&b, user, rhost, R.next_serial, &c);
	/* ⭐ the network side's loop waits this long (enrolment, render grant, fork) */
	registro_dice(LOG_ROOT, "the birth for «%s» took %llu ms (%s)", user,
	              (unsigned long long)(log_now_ms() - t0),
	              o == CHILD_READY ? "born" : "refused");
	if (o != CHILD_READY) {
		send_refused(request, o == CHILD_NAME_UNKNOWN ? RXR_REF_NAME_UNKNOWN
		                      : o == CHILD_NAME_MOVED ? RXR_REF_MOVED
		                      : o == CHILD_CLOSING    ? RXR_REF_CLOSING
		                                              : RXR_REF_FAILED);
		return;
	}
	memset(k, 0, sizeof *k);
	k->used = true;
	k->serial = R.next_serial++;
	k->pid = c.pid;
	k->uid = c.uid;
	k->gid = c.gid;
	k->render_grant = c.render_grant;
	k->generation = R.generation;
	snprintf(k->user, sizeof k->user, "%s", c.user);

	memset(&s, 0, sizeof s);
	head_fill(&s.h, RXR_SPAWNED, request);
	s.serial = k->serial;
	s.pid = (int32_t)c.pid;
	s.uid = (uint32_t)c.uid;
	s.gid = (uint32_t)c.gid;
	snprintf(s.user, sizeof s.user, "%s", c.user);
	/* ⭐ review 4 B, finding 12: chan_try(), not chan_send() — ONE line for this
	 *    failure, with its consequence and its errno, not chan_send()'s generic
	 *    «did not leave» as well */
	if (R.chan < 0 || !chan_try(&s, sizeof s, c.fd)) {
		registro_dice(LOG_ROOT, "⛔ the child of «%s» is born but its socket could not "
		              "be handed over (%s): it is killed", c.user,
		              R.chan < 0 ? "no network side" : strerror(errno));
		kill(c.pid, SIGKILL);
	}
	/* ⛔ The root side keeps NO end of the child's socket: when the network
	 *    side dies, the child must see EOF (§11.50: desktops stay, children go). */
	close(c.fd);
}

static void handle_signal(const struct rxr_signal_msg *m)
{
	/* ⛔ Only a child born for THIS network side (lane 1's pre-release review):
	 *    a new network side never held the sockets of the previous one's
	 *    children — those are the root side's own business (`kids_hurry()`),
	 *    and their serials are not the new one's to name. */
	for (int i = 0; i < R.cap; i++)
		if (R.kids[i].used && R.kids[i].serial == m->serial && R.kids[i].pid > 0
		    && R.kids[i].generation == R.generation) {
			kill(R.kids[i].pid, m->sig == RXR_SIG_KILL ? SIGKILL : SIGTERM);
			return;
		}
	log_detail(LOG_ROOT, "SIGNAL for serial %llu: not a live child of this network side "
	           "(already reaped, or a previous network side's): nothing sent",
	           (unsigned long long)m->serial);
}

static void chan_read(void)
{
	for (int round = 0; round < 64 && R.chan >= 0; round++) {
		union {
			struct rxr_head h;
			struct rxr_auth a;
			struct rxr_spawn s;
			struct rxr_close_orphan c;
			struct rxr_signal_msg g;
			char raw[sizeof(struct rxr_auth) + 16];
		} pk;
		union {
			struct cmsghdr c;
			char b[CMSG_SPACE(sizeof(struct ucred)) + CMSG_SPACE(4 * sizeof(int))];
		} ctl;
		struct iovec io = { &pk, sizeof pk };
		struct msghdr m;
		struct ucred cred = { 0, (uid_t)-1, (gid_t)-1 };
		bool has_cred = false, has_fds = false;
		struct rootside_peer peer = { R.o->remotix_uid, R.net_pid };
		char why[200];
		ssize_t n;
		int kind;

		memset(&m, 0, sizeof m);
		m.msg_iov = &io;
		m.msg_iovlen = 1;
		m.msg_control = ctl.b;
		m.msg_controllen = sizeof ctl.b;
		n = recvmsg(R.chan, &m, MSG_DONTWAIT | MSG_TRUNC | MSG_CMSG_CLOEXEC);
		if (n < 0) {
			if (errno == EINTR)
				continue;
			if (errno == EAGAIN || errno == EWOULDBLOCK)
				return;
			/* ⚠ A network side that died with packets unread is an EOF,
			 *   not a broken closed list. */
			if (errno != ECONNRESET) {
				net_kill(strerror(errno));
				return;
			}
			n = 0;
		}
		if (n == 0) {
			registro_dice(LOG_ROOT, "the network side (pid %ld) closed its channel",
			              (long)R.net_pid);
			close(R.chan);
			R.chan = -1;
			if (R.net_pid > 0) {
				kill(R.net_pid, SIGTERM);
				R.net_kill_at = log_now_ms() + NET_TERM_GRACE_MS;
			}
			return;
		}
		for (struct cmsghdr *c = CMSG_FIRSTHDR(&m); c; c = CMSG_NXTHDR(&m, c)) {
			if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_CREDENTIALS
			    && c->cmsg_len == CMSG_LEN(sizeof cred)) {
				memcpy(&cred, CMSG_DATA(c), sizeof cred);
				has_cred = true;
			} else if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_RIGHTS) {
				size_t nfd = (c->cmsg_len - CMSG_LEN(0)) / sizeof(int);
				for (size_t j = 0; j < nfd; j++) {
					int fd;
					memcpy(&fd, CMSG_DATA(c) + j * sizeof(int), sizeof fd);
					close(fd);
				}
				has_fds = true;
			}
		}
		if (has_fds || (m.msg_flags & MSG_CTRUNC)) {
			explicit_bzero(&pk, sizeof pk);
			net_kill("a packet carried descriptors: none ever goes this way");
			return;
		}
		kind = rootside_check_packet(&peer, &pk, (size_t)n, has_cred, cred.pid, cred.uid,
		                             why, sizeof why);
		if (kind == 0) {
			explicit_bzero(&pk, sizeof pk);
			net_kill(why);
			return;
		}
		switch (kind) {
		case RXR_AUTH:
			handle_auth(&pk.a);
			break;
		case RXR_SPAWN: {
			char user[RXR_USER_MAX], rhost[RXR_RHOST_MAX];
			if (!rootside_grant_take(&R.bounds, pk.s.grant, log_now_ms(), user, rhost)) {
				/* ⚠ One line per second at most (review 2, M1): the
				 *   check is a memory compare, the line is the cost. */
				static uint64_t logged_ms;
				static uint32_t hidden;
				uint64_t now = log_now_ms();

				hidden++;
				if (now >= logged_ms + 1000) {
					registro_dice(LOG_ROOT, "⛔ SPAWN refused: the grant is unknown, "
					              "used or expired (%u in the last second)", hidden);
					logged_ms = now;
					hidden = 0;
				}
				send_refused(pk.h.request, RXR_REF_GRANT);
				break;
			}
			birth(pk.h.request, user, rhost, pk.s.canvas_w, pk.s.canvas_h, false);
			break;
		}
		case RXR_CLOSE_ORPHAN:
			/* ⛔ The bucket BEFORE any work (review 2, M1): the denied file,
			 *    NSS, the sessions scan and a birth are what it would cost. */
			if (!rootside_orphan_admit(&R.bounds, log_now_ms())) {
				static uint64_t logged_ms;
				static uint32_t hidden;
				uint64_t now = log_now_ms();

				hidden++;
				if (now >= logged_ms + 1000) {
					registro_dice(LOG_ROOT, "⛔ CLOSE_ORPHAN over the root side's bound "
					              "(%d/s, burst %d): refused without looking — %u in "
					              "the last second", ROOTSIDE_ORPHAN_PER_S,
					              ROOTSIDE_ORPHAN_BURST, hidden);
					logged_ms = now;
					hidden = 0;
				}
				send_refused(pk.h.request, RXR_REF_RATE);
				break;
			}
			birth(pk.h.request, pk.c.user, NULL, R.o->canvas_w, R.o->canvas_h, true);
			break;
		case RXR_SIGNAL:
			handle_signal(&pk.g);
			break;
		}
		explicit_bzero(&pk, sizeof pk);
	}
}

static const char *status_text(int st, char *d, size_t cap)
{
	if (WIFEXITED(st))
		snprintf(d, cap, "exited with %d", WEXITSTATUS(st));
	else if (WIFSIGNALED(st))
		snprintf(d, cap, "killed by signal %d", WTERMSIG(st));
	else
		snprintf(d, cap, "ended (status %d)", st);
	return d;
}

static void reap_kids(void)
{
	for (int i = 0; i < R.cap; i++) {
		struct own_child *k = &R.kids[i];
		struct rxr_child_exited e;
		char said[80];
		int st = 0;

		if (!k->used || k->pid <= 0 || waitpid(k->pid, &st, WNOHANG) != k->pid)
			continue;
		/* ⛔ The render grant first, then the event: the network side is
		 *    never asked to remove anything (§11.50). */
		if (k->render_grant)
			render_grant_remove(k->user, k->uid, k->gid);
		/* ⭐ 1.6 (R1): the moment the user was left without a client, for CLOSE_ORPHAN */
		rootside_exit_note(&R.bounds, k->uid, log_now_ms());
		registro_dice(LOG_ROOT, "the child of «%s» (pid %ld, serial %llu) is reaped by "
		              "the root side: %s", k->user, (long)k->pid,
		              (unsigned long long)k->serial, status_text(st, said, sizeof said));
		memset(&e, 0, sizeof e);
		head_fill(&e.h, RXR_CHILD_EXITED, 0);
		e.serial = k->serial;
		e.wait_status = st;
		/* ⚠ Only to the network side the child was born for: a new one
		 *   does not know that serial. */
		if (k->generation == R.generation)
			send_exited(&e);
		memset(k, 0, sizeof *k);
	}
}

/* ⭐ Once a minute: the expired grants are WIPED (not left for the next mint
 *    to overwrite: a grant past its 30 s is gone from memory too), and one
 *    detail line says how full every table is — what the soak bench
 *    (24-privsep-soak.sh) reads to see that nothing accumulates. */
static void tables_minute(uint64_t now)
{
	int kids = 0, grants = 0, wiped = 0, pending = 0;

	if (now < R.tables_ms + 60000)
		return;
	R.tables_ms = now;
	for (int i = 0; i < ROOTSIDE_GRANTS_MAX; i++) {
		if (!R.bounds.grants[i].used)
			continue;
		if (R.bounds.grants[i].expires_ms <= now) {
			explicit_bzero(&R.bounds.grants[i], sizeof R.bounds.grants[i]);
			wiped++;
		} else {
			grants++;
		}
	}
	for (int i = 0; i < R.cap; i++)
		kids += R.kids[i].used;
	for (size_t i = 0; i < sizeof R.pending / sizeof R.pending[0]; i++)
		pending += R.pending[i].used;
	log_detail(LOG_ROOT, "root side tables: children %d/%d, grants live %d (%d expired wiped), "
	           "AUTH in flight %d, pending %d, outbox %d, network side generation %u",
	           kids, R.cap, grants, wiped, R.bounds.in_flight, pending, R.nout, R.generation);
}

/* ⛔ What was asked to die and did not (findings 2 and 10, box at
 *    `NET_TERM_GRACE_MS`).  Called every round. */
static void kids_hurry(uint64_t now)
{
	if (R.net_pid > 0 && R.net_kill_at && now >= R.net_kill_at) {
		registro_dice(LOG_ROOT, "⛔ the network side (pid %ld) closed its channel and did "
		              "not exit within %d s of SIGTERM: SIGKILL",
		              (long)R.net_pid, NET_TERM_GRACE_MS / 1000);
		kill(R.net_pid, SIGKILL);
		R.net_kill_at = 0;
	}
	for (int i = 0; i < R.cap; i++) {
		struct own_child *k = &R.kids[i];

		if (!k->used || k->pid <= 0 || !k->term_at)
			continue;
		if (!k->kill_at && now >= k->term_at) {
			registro_dice(LOG_ROOT, "⛔ the child of «%s» (pid %ld, serial %llu) did not "
			              "leave within %d s of its network side's death: SIGTERM (the "
			              "desktop stays)", k->user, (long)k->pid,
			              (unsigned long long)k->serial, KIDS_EOF_GRACE_MS / 1000);
			kill(k->pid, SIGTERM);
			k->kill_at = now + KIDS_TERM_GRACE_MS;
		} else if (k->kill_at && now >= k->kill_at) {
			registro_dice(LOG_ROOT, "⛔ the child of «%s» (pid %ld) did not exit within %d s "
			              "of SIGTERM: SIGKILL", k->user, (long)k->pid,
			              KIDS_TERM_GRACE_MS / 1000);
			kill(k->pid, SIGKILL);
			k->kill_at = now + KIDS_TERM_GRACE_MS; /* again, until reaped */
		}
	}
}

static void net_start(uint64_t now);

static void reap_net(uint64_t now)
{
	char said[80];
	int st = 0;
	uint64_t pause = NET_RESTART_FIRST_MS;

	if (R.net_pid <= 0 || waitpid(R.net_pid, &st, WNOHANG) != R.net_pid)
		return;
	registro_dice(LOG_ROOT,
	              "%s the network side (pid %ld) is gone: %s.  Its children see EOF "
	              "and leave; the desktops stay alive (§11.50)",
	              R.stopping ? "⭐" : "⛔", (long)R.net_pid, status_text(st, said, sizeof said));
	R.net_pid = 0;
	R.net_kill_at = 0;
	if (R.chan >= 0) {
		close(R.chan);
		R.chan = -1;
	}
	/* ⛔ Its children: the EOF first, then the signals (`kids_hurry()`). */
	for (int i = 0; i < R.cap; i++)
		if (R.kids[i].used && R.kids[i].generation == R.generation && !R.kids[i].term_at)
			R.kids[i].term_at = now + KIDS_EOF_GRACE_MS;
	if (R.stopping)
		return;
	R.deaths_in_row = now - R.net_born_ms < NET_STABLE_MS ? R.deaths_in_row + 1 : 1;
	for (int i = 1; i < R.deaths_in_row && pause < NET_RESTART_CAP_MS; i++)
		pause *= 2;
	if (pause > NET_RESTART_CAP_MS)
		pause = NET_RESTART_CAP_MS;
	R.restart_at = now + pause;
	registro_dice(LOG_ROOT, "⚠ the network side will be started again in %llu ms "
	              "(death %d in a row)", (unsigned long long)pause, R.deaths_in_row);
}

/* ⭐ fd `from` onto `to`, CLOEXEC cleared; -1 ⇒ `to` closed. */
static int place(int from, int to)
{
	if (from < 0) {
		close(to);
		return 0;
	}
	return dup2(from, to) < 0 ? -1 : 0;
}

/* The whole of /proc/<pid>/cgroup (every hierarchy on a v1/hybrid system,
 * the one «0::» line on v2): two processes are in the same cgroup when the
 * files are equal.  `false` when it cannot be read. */
static bool cgroup_of(pid_t pid, char *out, size_t cap)
{
	char path[64];
	int fd;
	ssize_t n;

	snprintf(path, sizeof path, "/proc/%ld/cgroup", (long)pid);
	fd = open(path, O_RDONLY | O_CLOEXEC);
	if (fd < 0)
		return false;
	n = read(fd, out, cap - 1);
	close(fd);
	if (n <= 0 || (size_t)n >= cap - 1)
		return false;
	out[n] = 0;
	return true;
}

/* ⛔ Review 2, L1: what a dead network side forked is still uid `remotix`,
 *    and keeps fds 4/5 (the port) and the TLS key across the restart —
 *    `reap_net()` waited only for its pid.  ⇒ Before each start, every
 *    process of uid `remotix` that lives in THIS root side's own cgroup is
 *    SIGKILLed: a fork of our network side stays in our cgroup (systemd's unit,
 *    or the container's), whatever it does.
 * ⛔⛔ And ONLY those (16 Oct 2026, the coordinator's decision, option a): the
 *    first form became `remotix` and `kill(-1, SIGKILL)`ed EVERY process of that
 *    uid — in a box the rehearsal's rxp-privsep and rete11-server killed each
 *    other's network sides in a loop (privsep red on three boxes,
 *    20261016-122655).  Another REMOTIX server's network side runs as the same
 *    uid but in ANOTHER cgroup (its own unit): it is not ours, and is left
 *    alone.  Done as root, reading /proc — no fork, no `kill(-1)`.
 *  ⚠ A root side not under systemd (a bench, a container's pid 1) shares its
 *    cgroup with whatever else runs there as `remotix`: still «ours». */
static void net_leftovers_kill(void)
{
	static char own[4096];
	char other[4096];
	DIR *d;
	struct dirent *e;
	int killed = 0;

	if (!own[0] && !cgroup_of(getpid(), own, sizeof own)) {
		registro_dice(LOG_ROOT, "⚠ the root side cannot read its own cgroup: the leftovers "
		              "of a dead network side are NOT swept");
		return;
	}
	d = opendir("/proc");
	if (!d) {
		/* review 4 B, finding 14: as the cgroup failure above */
		registro_dice(LOG_ROOT, "⚠ the root side cannot read /proc (%s): the leftovers of "
		              "a dead network side are NOT swept", strerror(errno));
		return;
	}
	while ((e = readdir(d)) != NULL) {
		char path[64];
		struct stat st;
		pid_t pid;

		if (e->d_name[0] < '1' || e->d_name[0] > '9')
			continue;
		pid = (pid_t)strtol(e->d_name, NULL, 10);
		snprintf(path, sizeof path, "/proc/%ld", (long)pid);
		if (stat(path, &st) != 0 || st.st_uid != R.o->remotix_uid)
			continue;
		if (pid == R.net_pid || !cgroup_of(pid, other, sizeof other)
		    || strcmp(other, own) != 0)
			continue;
		if (kill(pid, SIGKILL) == 0)
			killed++;
	}
	closedir(d);
	if (killed)
		registro_dice(LOG_ROOT, "⛔ %d process(es) of uid %ld (remotix) were still alive in this "
		              "root side's cgroup before the network side's start — a dead network "
		              "side's leftovers: SIGKILL (other cgroups' are another server's, left "
		              "alone)", killed, (long)R.o->remotix_uid);
}

/* What the previous network side leaves behind, emptied before a new one starts
 * (the fuzz harness calls it too, as its «a new network side»). */
static void net_generation_reset(void)
{
	R.nout = 0; /* the serials of the dead one mean nothing to the new one */
	/* ⛔ And its grants (lane 1's pre-release review): they were handed to the
	 *    previous network side, in its VERDICTs — this one never saw them, and a
	 *    SPAWN with one would be a grant that left the process it was given to.
	 *    Wiped at every start, whatever road ended the previous one. */
	for (int i = 0; i < ROOTSIDE_GRANTS_MAX; i++)
		explicit_bzero(&R.bounds.grants[i], sizeof R.bounds.grants[i]);
}

/* ⛔ The network side's environment, from an ALLOW-LIST (lane 4's review, M4):
 *    the root side's whole `environ` crossed the exec before — anything the
 *    unit, a drop-in or an administrator's shell put there.  Kept: a fixed PATH,
 *    the locale (LANG, LC_*), TZ, JOURNAL_STREAM (log.c: is stderr the journal),
 *    LD_LIBRARY_PATH (the benches' own ngtcp2 builds; set by root, never by the
 *    network), REMOTIX_* (the root side's own switches, if a bench sets one) and
 *    DBUS_SYSTEM_BUS_ADDRESS (a moved system bus is followed by both sides: the
 *    rediscovery asks logind on it — lane 4's cross-review).
 *    Everything else stays behind.  Built in the fork, before the exec. */
static char **net_environment(void)
{
	static char path[] = "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin";
	static char *env[64];
	int n = 0;

	env[n++] = path;
	for (char **e = environ; e && *e && n < 63; e++) {
		const char *v = *e;

		if (strncmp(v, "LANG=", 5) == 0 || strncmp(v, "LC_", 3) == 0
		    || strncmp(v, "TZ=", 3) == 0 || strncmp(v, "JOURNAL_STREAM=", 15) == 0
		    || strncmp(v, "LD_LIBRARY_PATH=", 16) == 0 || strncmp(v, "REMOTIX_", 8) == 0
		    || strncmp(v, "DBUS_SYSTEM_BUS_ADDRESS=", 24) == 0)
			env[n++] = (char *)v;
	}
	env[n] = NULL;
	return env;
}

static void net_start(uint64_t now)
{
	int sv[2], one = 1;
	pid_t me = getpid(), p;
	struct rxr_ready r;
	sigset_t all, before;

	R.restart_at = 0;
	net_generation_reset();
	net_leftovers_kill();
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		registro_dice(LOG_ROOT, "⛔ no channel for the network side (socketpair: %s): "
		              "retried in %d s", strerror(errno), NET_RESTART_CAP_MS / 1000);
		R.restart_at = now + NET_RESTART_CAP_MS;
		return;
	}
	/* ⛔ review 4 B, finding 15: without SO_PASSCRED no packet carries the
	 *    kernel's stamp, every one fails the check, and the network side is
	 *    killed and restarted for ever with a line that blames it. */
	if (setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &one, sizeof one) != 0
	    || setsockopt(sv[1], SOL_SOCKET, SO_PASSCRED, &one, sizeof one) != 0) {
		registro_dice(LOG_ROOT, "⛔ SO_PASSCRED does not turn on on the network side's "
		              "channel (%s): it is not started — retried in %d s", strerror(errno),
		              NET_RESTART_CAP_MS / 1000);
		close(sv[0]);
		close(sv[1]);
		R.restart_at = now + NET_RESTART_CAP_MS;
		return;
	}
	/* ⛔ Every signal blocked across the `fork()`: the copy resets the
	 *    dispositions BEFORE it unblocks, so `on_signal()` never runs in it
	 *    (review of §11.50, finding 3). */
	sigfillset(&all);
	sigprocmask(SIG_SETMASK, &all, &before);
	p = fork();
	if (p != 0)
		sigprocmask(SIG_SETMASK, &before, NULL);
	if (p < 0) {
		registro_dice(LOG_ROOT, "⛔ fork of the network side: %s — retried in %d s",
		              strerror(errno), NET_RESTART_CAP_MS / 1000);
		close(sv[0]);
		close(sv[1]);
		R.restart_at = now + NET_RESTART_CAP_MS;
		return;
	}
	if (p == 0) {
		char why[512] = "";
		int c = fcntl(sv[1], F_DUPFD_CLOEXEC, 10);
		int u = R.o->udp_fd >= 0 ? fcntl(R.o->udp_fd, F_DUPFD_CLOEXEC, 10) : -1;
		int t = R.o->tcp_fd >= 0 ? fcntl(R.o->tcp_fd, F_DUPFD_CLOEXEC, 10) : -1;

		/* ⛔⛔ The journal's socket of the root side may BE fd 3, 4 or 5 (it is
		 *     opened first, at main.c's start): `place()` dup2s the channel
		 *     over it, and every line written in this fork after that went INTO
		 *     THE CHANNEL — `[M]` 16 Oct 2026, private box: «broke the closed
		 *     list: wrong magic or version (4f495250…)», «PRIO» of «PRIORITY=»,
		 *     the network side killed in a loop as soon as this fork wrote its
		 *     «walls in force» line.  ⇒ The journal is closed in the fork
		 *     before the fds move, and opened again on a free fd after. */
		bool journal = log_to_journal();

		if (journal)
			(void)log_journal(false);
		/* ⛔ review 4 B, finding 9: every exit of this fork says why, not only
		 *    the walls' (reap_net() prints the code alone) */
		if (c < 0 || place(c, ROOTSIDE_FD_CHANNEL) || place(u, ROOTSIDE_FD_UDP)
		    || place(t, ROOTSIDE_FD_TCP)) {
			if (journal)
				(void)log_journal(true);
			registro_dice(LOG_ROOT, "⛔⛔ the network side's fds 3/4/5 could not be put in "
			              "place (%s): it is NOT started", strerror(errno));
			_exit(125);
		}
		if (close_range(ROOTSIDE_FD_TCP + 1, ~0U, 0) != 0)
			for (int i = ROOTSIDE_FD_TCP + 1; i < 4096; i++)
				close(i);
		/* the journal again, on a free fd (CLOEXEC: gone at the execve) */
		if (journal)
			(void)log_journal(true);
		/* review 4 B, finding 24: the shared reset — SIGPIPE stays ignored */
		rootside_fork_signals_fresh();

		/* ⛔ The walls, as root, before the `exec` — any failure and the
		 *    network side does not start (§11.50). */
		if (walls_apply(R.o, why, sizeof why) != 0) {
			registro_dice(LOG_ROOT, "⛔⛔ the network side's walls did NOT go up: %s.  "
			              "It is NOT started (no network side without its walls)", why);
			_exit(126);
		}
		/* ⭐ review 4 B, finding 6: which walls, said once per birth */
		registro_dice(LOG_ROOT, "⭐ the network side's walls in force: %s", walls_in_force());
		/* ⚠ After the uid change, which clears it; and checked against a
		 *   root side that died in between. */
		prctl(PR_SET_PDEATHSIG, SIGTERM);
		if (getppid() != me) {
			registro_dice(LOG_ROOT, "⛔⛔ the root side died while its network side was "
			              "being born: it is NOT started");
			_exit(127);
		}
		execve("/proc/self/exe", R.o->net_argv, net_environment());
		registro_dice(LOG_ROOT, "⛔⛔ execve of the network side failed (%s): it is NOT "
		              "started", strerror(errno));
		_exit(127);
	}
	close(sv[1]);
	R.chan = sv[0];
	R.net_pid = p;
	if (fcntl(R.chan, F_SETFL, O_NONBLOCK) != 0) {
		/* review 4 B, finding 15: a blocking channel would stall the root side */
		registro_dice(LOG_ROOT, "⛔ the network side's channel cannot be made non-blocking "
		              "(%s)", strerror(errno));
		net_kill("its channel could not be made non-blocking");
		return;
	}
	R.net_born_ms = now;
	R.generation++;
	memset(&r, 0, sizeof r);
	head_fill(&r.h, RXR_READY, 0);
	r.remotix_uid = (uint32_t)R.o->remotix_uid;
	r.codecs_ok = R.codecs_ok ? 1 : 0;
	snprintf(r.offered, sizeof r.offered, "%s", R.offered);
	snprintf(r.explanation, sizeof r.explanation, "%s", R.explanation);
	(void)chan_send(&r, sizeof r, -1);
	registro_dice(LOG_ROOT, "⭐ network side started: pid %ld, uid %ld (remotix), fd 3 "
	              "the channel, 4 UDP, 5 TCP", (long)p, (long)R.o->remotix_uid);
}

int rootside_main(const struct rootside_options *o)
{
	struct sigaction sa;
	int pp[2];
	ssize_t n;

	if (!o || !o->net_argv || !o->net_argv[0] || o->remotix_uid == 0 || o->cap <= 0) {
		registro_dice(LOG_ROOT, "⛔ the root side does not start: %s",
		              !o || !o->net_argv || !o->net_argv[0] ? "no network side command line"
		              : o->remotix_uid == 0 ? "the network side's user is uid 0"
		                                    : "no children cap");
		return 1;
	}
	R.o = o;
	if (o->encoding_route)
		(void)child_encoding_route(o->encoding_route);
	if (o->render_node && o->render_node[0])
		(void)child_render_node(o->render_node);
	/* ⛔ The binary the children run is asked of the kernel (as
	 *    `children_turn_on()` did), never of argv. */
	n = readlink("/proc/self/exe", R.my_path, sizeof R.my_path - 1);
	if (n <= 0 || strstr((R.my_path[n] = 0, R.my_path), " (deleted)")) {
		registro_dice(LOG_ROOT, "⛔ the root side does not know which binary it runs "
		              "(«%s»): it does not start", n > 0 ? R.my_path : "?");
		return 1;
	}
	R.birth.canvas_w = o->canvas_w;
	R.birth.canvas_h = o->canvas_h;
	R.birth.dir_survey = o->dir_survey && o->dir_survey[0] ? o->dir_survey : NULL;
	R.birth.quality_rises = o->quality_recovery;
	R.birth.bandwidth_cap_mbit = o->bandwidth_cap_mbit;
	R.birth.audio_silence = o->audio_silence;
	R.birth.my_path = R.my_path;
	R.birth.parent_uid = (long)o->remotix_uid;
	R.cap = o->cap;
	R.kids = (struct own_child *)calloc((size_t)R.cap, sizeof *R.kids);
	R.outbox = (struct rxr_child_exited *)calloc((size_t)R.cap * 4, sizeof *R.outbox);
	/* review 4 B, finding 9: rootside.h promises «the reason is logged» */
	if (!R.kids || !R.outbox) {
		registro_dice(LOG_ROOT, "⛔ the root side does not start: no memory for its tables "
		              "(%d children, %d CHILD_EXITED outbox)", R.cap, R.cap * 4);
		return 1;
	}
	R.next_serial = 1;
	/* ⚠ The port stays out of every other fork (usermod, the probe): only the
	 *   network side gets it, by dup2 onto 4 and 5. */
	if (o->udp_fd >= 0)
		(void)fcntl(o->udp_fd, F_SETFD, FD_CLOEXEC);
	if (o->tcp_fd >= 0)
		(void)fcntl(o->tcp_fd, F_SETFD, FD_CLOEXEC);

	/* 1. the codec probe, as root, as 1.0 did — before any handler of ours */
	registro_dice(LOG_STARTUP,
	              "⭐ phase 18 — encoding test at startup, in a separate process: the "
	              "«opened: …» lines at 256x256 below are its own, not a session's");
	R.codecs_ok = child_video_capabilities(R.offered, sizeof R.offered, R.explanation,
	                                       sizeof R.explanation);
	/* 2. the render grants a previous run left */
	render_grant_sweep();
	/* 3. the signals, through a self-pipe */
	if (pipe2(pp, O_CLOEXEC | O_NONBLOCK) != 0) {
		registro_dice(LOG_ROOT, "⛔ the root side does not start: no self-pipe for its "
		              "signals (%s)", strerror(errno));
		return 1;
	}
	R.pipe_r = pp[0];
	R.pipe_w = pp[1];
	memset(&sa, 0, sizeof sa);
	sa.sa_handler = on_signal;
	sa.sa_flags = SA_RESTART;
	sigemptyset(&sa.sa_mask);
	sigaction(SIGTERM, &sa, NULL);
	sigaction(SIGINT, &sa, NULL);
	sigaction(SIGUSR1, &sa, NULL);
	sigaction(SIGUSR2, &sa, NULL);
	sigaction(SIGCHLD, &sa, NULL);
	signal(SIGPIPE, SIG_IGN);
	signal(SIGHUP, SIG_IGN);
	/* 4. the PAM helper, now this side's child */
	R.pam = helper_turn_on_root(on_pam_outcome, NULL);
	/* ⛔ review 4 B, finding 10: NULL is only «no memory for the helper's
	 *    table» (a helper that does not START is retried inside it, 1 s → 60 s)
	 *    — without the table every AUTH would be «not checked» with no line */
	if (!R.pam) {
		registro_dice(LOG_ROOT, "⛔ the root side does not start: no memory for the PAM "
		              "helper's table (every login would be «not checked»)");
		return 1;
	}
	rootside_bounds_init(&R.bounds, log_now_ms());
	R.bounds.abandon_ms = o->abandon_s * 1000;
	registro_dice(LOG_ROOT,
	              "⭐ ROOT SIDE on (pid %ld, DECISIONS.md §11.50): single-threaded, PAM "
	              "helper and children below it, up to %d children; the network side "
	              "runs as uid %ld",
	              (long)getpid(), R.cap, (long)o->remotix_uid);
	/* 5. the network side */
	net_start(log_now_ms());

	for (;;) {
		struct pollfd p[3];
		int np = 0, i_chan = -1, i_pam = -1;
		uint64_t now;
		unsigned char sigs[64];
		bool usr1 = false, usr2 = false;

		p[np].fd = R.pipe_r;
		p[np++].events = POLLIN;
		if (R.chan >= 0) {
			i_chan = np;
			p[np].fd = R.chan;
			p[np++].events = POLLIN | (R.nout > 0 ? POLLOUT : 0);
		}
		if (helper_descriptor(R.pam) >= 0) {
			i_pam = np;
			p[np].fd = helper_descriptor(R.pam);
			p[np++].events = POLLIN;
		}
		for (int k = 0; k < np; k++)
			p[k].revents = 0;
		(void)poll(p, (nfds_t)np, R.stopping ? 100 : 1000);
		now = log_now_ms();

		while ((n = read(R.pipe_r, sigs, sizeof sigs)) > 0)
			for (ssize_t k = 0; k < n; k++) {
				if ((sigs[k] == SIGTERM || sigs[k] == SIGINT) && !R.stopping) {
					R.stopping = true;
					R.stop_deadline = now + STOP_WAIT_MS;
					registro_dice(LOG_ROOT, "⭐ signal %d: the network side is asked "
					              "to stop (SIGTERM), %d s at most",
					              sigs[k], STOP_WAIT_MS / 1000);
					if (R.net_pid > 0)
						kill(R.net_pid, SIGTERM);
				} else if (sigs[k] == SIGUSR1) {
					usr1 = true;
				} else if (sigs[k] == SIGUSR2) {
					usr2 = true;
				}
			}
		/* ⭐ The bench's trigger reaches this process (the main PID): it is
		 *    passed on to the children here, as `children_move()` did. */
		for (int w = 0; w < 2; w++) {
			int which = w ? SIGUSR2 : SIGUSR1;
			if (!(w ? usr2 : usr1))
				continue;
			for (int i = 0; i < R.cap; i++)
				if (R.kids[i].used && R.kids[i].pid > 0) {
					kill(R.kids[i].pid, which);
					registro_dice(LOG_CHILD,
					              "⭐ trigger: %s forwarded to the child of «%s» (pid %ld)",
					              which == SIGUSR2 ? "SIGUSR2" : "SIGUSR1",
					              R.kids[i].user, (long)R.kids[i].pid);
				}
		}

		if (i_chan >= 0 && (p[i_chan].revents & (POLLIN | POLLHUP | POLLERR)))
			chan_read();
		if (R.nout > 0)
			outbox_flush();
		reap_kids();
		reap_net(now);
		kids_hurry(now);
		tables_minute(now);
		if (i_pam >= 0 && (p[i_pam].revents & (POLLIN | POLLHUP | POLLERR)))
			helper_move(R.pam, NULL, NULL);
		helper_expired(R.pam, now, NULL, NULL);

		if (R.stopping) {
			bool kids = false;
			int left = 0;
			for (int i = 0; i < R.cap; i++)
				left += R.kids[i].used;
			kids = left > 0;
			if (R.net_pid <= 0 && (!kids || now >= R.stop_deadline)) {
				/* review 4 B, finding 16: said, not left to «stopped» */
				if (kids)
					registro_dice(LOG_ROOT, "⚠ the root side stops with %d child(ren) "
					              "still alive at the deadline: systemd's KillMode=mixed "
					              "takes them", left);
				break;
			}
			if (now >= R.stop_deadline && R.net_pid > 0) {
				registro_dice(LOG_ROOT, "⛔ the network side did not stop within %d s: "
				              "SIGKILL", STOP_WAIT_MS / 1000);
				kill(R.net_pid, SIGKILL);
				R.stop_deadline = now + 1000;
			}
			continue;
		}
		if (R.net_pid <= 0 && R.restart_at && now >= R.restart_at)
			net_start(now);
	}
	helper_turn_off(R.pam);
	registro_dice(LOG_ROOT, "⭐ root side stopped");
	return 0;
}

/* ======================================================================= */
/* THE NETWORK SIDE'S CLIENT                                                 */

union rpk {
	struct rxr_head h;
	struct rxr_ready ready;
	struct rxr_verdict v;
	struct rxr_spawned s;
	struct rxr_spawn_refused r;
	struct rxr_child_exited e;
};

#define CLIENT_AUTHS 32
#define CLIENT_GRANTS 32
/* ⛔ Review 4, finding 4: an AUTH whose VERDICT never comes (lost at a full
 *    queue, a root side that dropped it) held its entry for good, and with the
 *    table full the next AUTH OVERWROTE entry 0 — someone else's pending login.
 *    Now an entry is freed by its VERDICT, by a VERDICT lost at the full queue,
 *    or by age: well past helper.c's flight expiry (8 s), when nobody waits for
 *    that answer any more.  A full table REFUSES the AUTH; nothing is
 *    overwritten (the grants likewise). */
#define CLIENT_AUTH_STALE_MS 30000
/* ⛔ Only VERDICTs are put aside (review of the split, findings 4 and 5):
 *    they need `helper_move()`'s delivery, and are delivered at its next call
 *    — `helper_expired()` makes one every loop round.  CHILD_EXITED is
 *    dispatched at once wherever it arrives (it only marks a slot), so no
 *    queue can lose it.  4096 VERDICTs: each answers an AUTH this side sent,
 *    and none is sent while a wait holds the loop. */
#define CLIENT_QUEUE 4096

static struct {
	int fd;
	bool attached, lost;
	pid_t root_pid;
	uint64_t next_request;
	RootsideVerdict on_verdict;
	void *verdict_ctx;
	RootsideChildExited on_exited;
	void *exited_ctx;
	struct {
		bool used;
		uint64_t request;
		uint64_t at_ms;   /* when the AUTH left: an entry older than CLIENT_AUTH_STALE_MS is free */
		char user[RXR_USER_MAX];
		char rhost[RXR_RHOST_MAX];
	} auths[CLIENT_AUTHS];
	struct {
		bool used;
		uint8_t grant[RXR_GRANT_BYTES];
		char user[RXR_USER_MAX];
		char rhost[RXR_RHOST_MAX];
		uint64_t expires_ms;
	} grants[CLIENT_GRANTS];
	struct rxr_verdict q[CLIENT_QUEUE];
	int qhead, qn;
} C = { .fd = -1, .next_request = 1 };

static size_t size_of_event(int kind)
{
	switch (kind) {
	case RXR_READY:         return sizeof(struct rxr_ready);
	case RXR_VERDICT:       return sizeof(struct rxr_verdict);
	case RXR_SPAWNED:       return sizeof(struct rxr_spawned);
	case RXR_SPAWN_REFUSED: return sizeof(struct rxr_spawn_refused);
	case RXR_CHILD_EXITED:  return sizeof(struct rxr_child_exited);
	default:                return 0;
	}
}

static void client_lost(const char *why)
{
	if (C.lost)
		return;
	C.lost = true;
	registro_dice(LOG_ROOT, "⛔⛔ the channel to the root side is lost: %s", why);
	if (C.fd >= 0) {
		close(C.fd);
		C.fd = -1;
	}
}

/* 1 = a packet in `pk` (`*fd` its descriptor or -1) · 0 = nothing within
 * `timeout_ms` · -1 = lost.  A packet that is not the root side's, or not of
 * the list, is dropped with its line and 0 is returned. */
static int client_recv(int timeout_ms, union rpk *pk, int *fd)
{
	union {
		struct cmsghdr c;
		char b[CMSG_SPACE(sizeof(struct ucred)) + CMSG_SPACE(4 * sizeof(int))];
	} ctl;
	struct iovec io = { pk, sizeof *pk };
	struct msghdr m;
	struct ucred cred = { 0, (uid_t)-1, (gid_t)-1 };
	bool has_cred = false;
	int nfds = 0;
	ssize_t n;

	*fd = -1;
	if (C.fd < 0)
		return -1;
	if (timeout_ms > 0) {
		struct pollfd p = { C.fd, POLLIN, 0 };
		if (poll(&p, 1, timeout_ms) <= 0)
			return 0;
	}
	memset(&m, 0, sizeof m);
	m.msg_iov = &io;
	m.msg_iovlen = 1;
	m.msg_control = ctl.b;
	m.msg_controllen = sizeof ctl.b;
	n = recvmsg(C.fd, &m, MSG_DONTWAIT | MSG_TRUNC | MSG_CMSG_CLOEXEC);
	if (n < 0) {
		if (errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK)
			return 0;
		client_lost(strerror(errno));
		return -1;
	}
	if (n == 0) {
		client_lost("the root side closed it (EOF)");
		return -1;
	}
	for (struct cmsghdr *c = CMSG_FIRSTHDR(&m); c; c = CMSG_NXTHDR(&m, c)) {
		if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_CREDENTIALS
		    && c->cmsg_len == CMSG_LEN(sizeof cred)) {
			memcpy(&cred, CMSG_DATA(c), sizeof cred);
			has_cred = true;
		} else if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_RIGHTS) {
			size_t k = (c->cmsg_len - CMSG_LEN(0)) / sizeof(int);
			for (size_t j = 0; j < k; j++) {
				int d;
				memcpy(&d, CMSG_DATA(c) + j * sizeof(int), sizeof d);
				if (*fd < 0)
					*fd = d;
				else
					close(d);
				nfds++;
			}
		}
	}
	if (!has_cred || cred.uid != 0 || cred.pid != C.root_pid || n < (ssize_t)sizeof pk->h
	    || pk->h.magic != RXR_MAGIC || pk->h.version != RXR_VERSION
	    || (size_t)n != size_of_event(pk->h.kind)
	    || (nfds > 0) != (pk->h.kind == RXR_SPAWNED) || nfds > 1) {
		registro_dice(LOG_ROOT, "⛔ a packet on the root channel that is not the root "
		              "side's or not of the list (%zd bytes, kind %u, uid %ld, pid %ld, "
		              "%d fd): DISCARDED", n, n >= (ssize_t)sizeof pk->h ? pk->h.kind : 0,
		              has_cred ? (long)cred.uid : -1L, has_cred ? (long)cred.pid : -1L,
		              nfds);
		if (*fd >= 0)
			close(*fd);
		*fd = -1;
		return 0;
	}
	return 1;
}

/* `false` when it did not leave (said here, once): the caller does not wait
 * for an answer to it (review 4 B, finding 2). */
static bool client_send(const void *p, size_t len)
{
	if (C.fd < 0)
		return false;
	if (send(C.fd, p, len, MSG_NOSIGNAL | MSG_DONTWAIT) != (ssize_t)len) {
		registro_dice(LOG_ROOT, "⛔ a packet of kind %u to the root side did not leave (%s)",
		              ((const struct rxr_head *)p)->kind, strerror(errno));
		return false;
	}
	return true;
}

static void dispatch(union rpk *pk, int fd)
{
	switch (pk->h.kind) {
	case RXR_VERDICT: {
		int k = -1;
		for (int i = 0; i < CLIENT_AUTHS; i++)
			if (C.auths[i].used && C.auths[i].request == pk->h.request)
				k = i;
		int g = -1;
		uint64_t now = log_now_ms();
		if (k >= 0 && pk->v.outcome == RXR_YES) {
			for (int i = 0; i < CLIENT_GRANTS; i++)
				if (!C.grants[i].used || C.grants[i].expires_ms <= now) {
					g = i;
					break;
				}
			/* ⛔ never another user's live grant (review 4, finding 4) */
			if (g < 0)
				registro_dice(LOG_ROOT, "⛔ the grant table is full (%d live grants): «%s»'s "
				              "grant is NOT kept — the birth will be refused and the "
				              "password asked again", CLIENT_GRANTS, C.auths[k].user);
		}
		if (g >= 0) {
			memset(&C.grants[g], 0, sizeof C.grants[g]);
			C.grants[g].used = true;
			memcpy(C.grants[g].grant, pk->v.grant, RXR_GRANT_BYTES);
			/* same-sized arrays, both terminated by `rootside_auth()` */
			memcpy(C.grants[g].user, C.auths[k].user, sizeof C.grants[g].user);
			memcpy(C.grants[g].rhost, C.auths[k].rhost, sizeof C.grants[g].rhost);
			/* ⚠ A little less than the root side's life: never sent dead. */
			C.grants[g].expires_ms = now + RXR_GRANT_LIFE_MS - 2000;
		}
		if (k >= 0)
			C.auths[k].used = false;
		explicit_bzero(pk->v.grant, sizeof pk->v.grant);
		if (C.on_verdict)
			C.on_verdict(C.verdict_ctx, pk->h.request, pk->v.outcome);
		break;
	}
	case RXR_CHILD_EXITED:
		if (C.on_exited)
			C.on_exited(C.exited_ctx, pk->e.serial, pk->e.wait_status);
		break;
	case RXR_SPAWNED:
		/* ⛔ An answer nobody waits for any more (its wait timed out): a
		 *    child nobody holds is not left alive. */
		registro_dice(LOG_ROOT, "⛔ SPAWNED for «%s» (serial %llu) arrived after its "
		              "wait: the child is killed", pk->s.user,
		              (unsigned long long)pk->s.serial);
		if (fd >= 0)
			close(fd);
		(void)rootside_signal(pk->s.serial, SIGKILL);
		return;
	default:
		log_detail(LOG_ROOT, "root channel: a packet of kind %u nobody waits for",
		           pk->h.kind);
		break;
	}
	if (fd >= 0)
		close(fd);
}

/* A packet that arrived while a wait held the loop: a VERDICT is put aside
 * for `rootside_move()`; anything else is dispatched now. */
static void aside_or_dispatch(union rpk *pk, int fd)
{
	if (pk->h.kind != RXR_VERDICT) {
		dispatch(pk, fd);
		return;
	}
	if (C.qn >= CLIENT_QUEUE) {
		/* ⚠ Not silent for the login: helper.c's flight expires it «not
		 *   checked», never counted towards the ban. */
		registro_dice(LOG_ROOT, "⛔⛔ the root channel's queue is full: the VERDICT for "
		              "request %llu is LOST (it expires «not checked»)",
		              (unsigned long long)pk->h.request);
		explicit_bzero(pk->v.grant, sizeof pk->v.grant);
		/* ⛔ … and its AUTH entry goes with it (review 4, finding 4) */
		for (int i = 0; i < CLIENT_AUTHS; i++)
			if (C.auths[i].used && C.auths[i].request == pk->h.request)
				C.auths[i].used = false;
		return;
	}
	C.q[(C.qhead + C.qn) % CLIENT_QUEUE] = pk->v;
	C.qn++;
	explicit_bzero(pk->v.grant, sizeof pk->v.grant);
}

static void queue_drain(void)
{
	while (C.qn > 0) {
		union rpk pk;

		memset(&pk, 0, sizeof pk);
		pk.v = C.q[C.qhead];
		explicit_bzero(&C.q[C.qhead], sizeof C.q[C.qhead]);
		C.qhead = (C.qhead + 1) % CLIENT_QUEUE;
		C.qn--;
		dispatch(&pk, -1);
	}
}

bool rootside_attach(int fd, int timeout_ms, struct rxr_ready *ready)
{
	union rpk pk;
	int one = 1, got;
	uint64_t until = log_now_ms() + (uint64_t)(timeout_ms > 0 ? timeout_ms : 0);

	C.fd = fd;
	C.root_pid = getppid();
	/* ⛔ review 4 B, finding 15: each one checked — without SO_PASSCRED no
	 *    packet from the root side would carry its stamp, and the line would
	 *    have been a misleading «no READY» */
	if (fcntl(fd, F_SETFD, FD_CLOEXEC) != 0
	    || setsockopt(fd, SOL_SOCKET, SO_PASSCRED, &one, sizeof one) != 0
	    || fcntl(fd, F_SETFL, O_NONBLOCK) != 0) {
		registro_dice(LOG_ROOT, "⛔ the root channel (fd %d) cannot be set up "
		              "(CLOEXEC, SO_PASSCRED, O_NONBLOCK: %s)", fd, strerror(errno));
		return false;
	}
	for (;;) {
		uint64_t now = log_now_ms();
		int d;

		if (now >= until)
			break;
		got = client_recv((int)(until - now), &pk, &d);
		if (got < 0)
			return false;
		if (got == 1 && pk.h.kind == RXR_READY) {
			pk.ready.offered[sizeof pk.ready.offered - 1] = 0;
			pk.ready.explanation[sizeof pk.ready.explanation - 1] = 0;
			if (ready)
				*ready = pk.ready;
			C.attached = true;
			registro_dice(LOG_ROOT, "⭐ attached to the root side (pid %ld): this is the "
			              "NETWORK SIDE, uid %ld", (long)C.root_pid, (long)getuid());
			return true;
		}
		if (got == 1) {
			registro_dice(LOG_ROOT, "⛔ the root side's first packet is kind %u, not READY",
			              pk.h.kind);
			if (d >= 0)
				close(d);
		}
	}
	registro_dice(LOG_ROOT, "⛔ no READY from the root side within %d ms", timeout_ms);
	return false;
}

bool rootside_attached(void) { return C.attached; }
int rootside_descriptor(void) { return C.attached ? C.fd : -1; }
bool rootside_lost(void) { return C.lost; }

void rootside_hook_verdict(RootsideVerdict fn, void *ctx)
{
	C.on_verdict = fn;
	C.verdict_ctx = ctx;
}

void rootside_hook_child_exited(RootsideChildExited fn, void *ctx)
{
	C.on_exited = fn;
	C.exited_ctx = ctx;
}

void rootside_move(void)
{
	union rpk pk;
	int d;

	queue_drain();
	for (int round = 0; round < 256 && C.fd >= 0; round++) {
		int got = client_recv(0, &pk, &d);
		if (got <= 0)
			break;
		dispatch(&pk, d);
		queue_drain(); /* what a dispatch's SPAWN wait put aside */
	}
}

bool rootside_auth(uint64_t request, const char *user, const char *password,
                   const char *rhost)
{
	struct rxr_auth a;
	int k = -1;
	uint64_t now = log_now_ms();

	if (C.fd < 0 || !user || !password)
		return false;
	/* ⛔ a free entry BEFORE sending, or the AUTH is refused (review 4,
	 *    finding 4): a stale one (older than CLIENT_AUTH_STALE_MS) counts as free */
	for (int i = 0; i < CLIENT_AUTHS; i++)
		if (!C.auths[i].used || now >= C.auths[i].at_ms + CLIENT_AUTH_STALE_MS) {
			k = i;
			break;
		}
	if (k < 0) {
		registro_dice(LOG_ROOT, "⛔ %d AUTH already waiting for their VERDICT: the login of "
		              "«%s» is NOT asked (refused, never overwriting another)", CLIENT_AUTHS, user);
		return false;
	}
	memset(&a, 0, sizeof a);
	head_fill(&a.h, RXR_AUTH, request);
	snprintf(a.user, sizeof a.user, "%s", user);
	snprintf(a.password, sizeof a.password, "%s", password);
	snprintf(a.rhost, sizeof a.rhost, "%s", rhost ? rhost : "");
	if (send(C.fd, &a, sizeof a, MSG_NOSIGNAL | MSG_DONTWAIT) != (ssize_t)sizeof a) {
		/* ⭐ review 4 B, finding 12: said HERE, with the real errno — helper.c
		 *    writes no second line for a refused rootside_auth() */
		registro_dice(LOG_ROOT, "⛔ the AUTH of «%s» did not leave towards the root side "
		              "(%s): it is answered NO, not asked", user, strerror(errno));
		explicit_bzero(&a, sizeof a);
		return false;
	}
	explicit_bzero(&a, sizeof a);
	C.auths[k].used = true;
	C.auths[k].request = request;
	C.auths[k].at_ms = now;
	snprintf(C.auths[k].user, sizeof C.auths[k].user, "%s", user);
	snprintf(C.auths[k].rhost, sizeof C.auths[k].rhost, "%s", rhost ? rhost : "");
	return true;
}

bool rootside_has_grant(const char *user, const char *rhost)
{
	uint64_t now = log_now_ms();

	for (int i = 0; i < CLIENT_GRANTS; i++)
		if (C.grants[i].used && C.grants[i].expires_ms > now
		    && strcmp(C.grants[i].user, user) == 0
		    && strcmp(C.grants[i].rhost, rhost ? rhost : "") == 0)
			return true;
	return false;
}

/* SPAWNED / SPAWN_REFUSED for `request`; the rest is put aside. */
static int wait_birth(uint64_t request, int timeout_ms, struct rootside_born *out)
{
	uint64_t until = log_now_ms() + (uint64_t)timeout_ms;

	for (;;) {
		uint64_t now = log_now_ms();
		union rpk pk;
		int d, got;

		if (now >= until)
			return ROOTSIDE_NO_ANSWER;
		got = client_recv((int)(until - now), &pk, &d);
		if (got < 0)
			return ROOTSIDE_LOST;
		if (got == 0)
			continue;
		if ((pk.h.kind == RXR_SPAWNED || pk.h.kind == RXR_SPAWN_REFUSED)
		    && pk.h.request == request) {
			if (pk.h.kind == RXR_SPAWN_REFUSED)
				return pk.r.reason ? pk.r.reason : RXR_REF_FAILED;
			memset(out, 0, sizeof *out);
			out->serial = pk.s.serial;
			out->pid = (pid_t)pk.s.pid;
			out->uid = (uid_t)pk.s.uid;
			out->gid = (gid_t)pk.s.gid;
			out->fd = d;
			pk.s.user[sizeof pk.s.user - 1] = 0;
			snprintf(out->user, sizeof out->user, "%s", pk.s.user);
			return 0;
		}
		/* an old SPAWNED: killed, never queued with its fd */
		aside_or_dispatch(&pk, d);
	}
}

int rootside_spawn(const char *user, const char *rhost, uint32_t canvas_w,
                   uint32_t canvas_h, int timeout_ms, struct rootside_born *out)
{
	struct rxr_spawn s;
	uint64_t now = log_now_ms();
	int k = -1;

	if (C.fd < 0 || !user)
		return ROOTSIDE_LOST;
	for (int i = 0; i < CLIENT_GRANTS; i++)
		if (C.grants[i].used && C.grants[i].expires_ms > now
		    && strcmp(C.grants[i].user, user) == 0
		    && strcmp(C.grants[i].rhost, rhost ? rhost : "") == 0)
			k = i;
	if (k < 0)
		return ROOTSIDE_NO_GRANT;
	memset(&s, 0, sizeof s);
	head_fill(&s.h, RXR_SPAWN, C.next_request++);
	memcpy(s.grant, C.grants[k].grant, RXR_GRANT_BYTES);
	explicit_bzero(&C.grants[k], sizeof C.grants[k]); /* single use, here too */
	s.canvas_w = canvas_w;
	s.canvas_h = canvas_h;
	if (!client_send(&s, sizeof s)) {
		explicit_bzero(s.grant, sizeof s.grant);
		return ROOTSIDE_NOT_SENT;
	}
	explicit_bzero(s.grant, sizeof s.grant);
	return wait_birth(s.h.request, timeout_ms, out);
}

int rootside_close_orphan(const char *user, int timeout_ms, struct rootside_born *out)
{
	struct rxr_close_orphan c;

	if (C.fd < 0 || !user)
		return ROOTSIDE_LOST;
	memset(&c, 0, sizeof c);
	head_fill(&c.h, RXR_CLOSE_ORPHAN, C.next_request++);
	snprintf(c.user, sizeof c.user, "%s", user);
	if (!client_send(&c, sizeof c))
		return ROOTSIDE_NOT_SENT;
	return wait_birth(c.h.request, timeout_ms, out);
}

bool rootside_signal(uint64_t serial, int sig)
{
	struct rxr_signal_msg m;

	if (C.fd < 0)
		return false;
	memset(&m, 0, sizeof m);
	head_fill(&m.h, RXR_SIGNAL, C.next_request++);
	m.serial = serial;
	m.sig = sig == SIGKILL ? RXR_SIG_KILL : RXR_SIG_TERM;
	if (send(C.fd, &m, sizeof m, MSG_NOSIGNAL | MSG_DONTWAIT) != (ssize_t)sizeof m) {
		/* ⭐ review 4 B, finding 13: a SIGNAL that does not leave leaves that
		 *    child alive (a late SPAWNED's, a refused one's) — said, once,
		 *    here, for every caller */
		registro_dice(LOG_ROOT, "⛔ SIGNAL %s for serial %llu did not leave towards the root "
		              "side (%s): that child is NOT signalled",
		              sig == SIGKILL ? "KILL" : "TERM", (unsigned long long)serial,
		              strerror(errno));
		return false;
	}
	return true;
}

void rootside_pump_until(bool (*done)(void *ctx), void *ctx, int timeout_ms)
{
	uint64_t until = log_now_ms() + (uint64_t)timeout_ms;

	for (;;) {
		uint64_t now = log_now_ms();
		union rpk pk;
		int d, got;

		/* ⛔ No VERDICT is delivered here: this is not `helper_move()`,
		 *    and a verdict without its delivery is a login lost
		 *    (finding 5).  They wait for the next round's. */
		if (done(ctx) || now >= until || C.fd < 0)
			return;
		got = client_recv((int)(until - now), &pk, &d);
		if (got == 1)
			aside_or_dispatch(&pk, d);
		else if (got < 0)
			return;
	}
}
