/*
 * rediscover.c — live REMOTIX desktops that no child holds.
 *
 * The why and the criterion are in `rediscover.h`, which is read first.  Here
 * there is only the how.
 */
#include "rediscover.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "log.h"

#define LOGIND_NAME "org.freedesktop.login1"
#define LOGIND_PATH "/org/freedesktop/login1"
#define IFACE_MANAGER "org.freedesktop.login1.Manager"
#define IFACE_SESSION "org.freedesktop.login1.Session"
/* ⚠ The same ceiling as `sentinel.c`, and for the same reason: the question
 *   leaves from the loop that delivers the frames. */
#define WAIT_MS 300
/* ⭐ 15 Oct 2026 — the ceiling of a round of the check that does NOT wait
 *    (`rediscover_search()` from the loop, every 10 s): nothing waits on it,
 *    so it can be long enough for a slow logind.  ⚠ Its `GetAll`s leave all
 *    together, and 300 ms each would cut the last ones of a long list while
 *    logind is merely busy answering the first ones.  It is judged when the
 *    context is turned (`rediscover_collect()`): a round out longer than this
 *    is cut. */
#define ASYNC_WAIT_MS 5000
/* ⛔ An answer older than this is not used: the check runs every 10 s
 *    (`FOUND_AGAIN_SWEEP_MS` in `main.c`) and a question takes two rounds
 *    (the list, then the `GetAll`s), so a fresh one is ~20 s old. */
#define ANSWER_MAX_AGE_MS 45000
/* How many logind sessions one question looks at, at most. */
#define MAX_LISTED 4096
/* How many `remotix` sessions are looked at in one go.  ⚠ Every reattach
 * leaves one more with a dead leader (`[M]` T2, §5.2 point b): 256 is ample. */
#define MAX_CANDIDATES 256

struct candidate_entry {
	uid_t uid;
	char id[32];
	char scope[128];
	char user[257];
};

/* The content of a small /proc file, terminated with '\0'.  -1 if it is missing. */
static ssize_t read_small(const char *fpath, char *buf, size_t cap)
{
	int fd = open(fpath, O_RDONLY | O_CLOEXEC);
	ssize_t n;

	if (fd < 0)
		return -1;
	n = read(fd, buf, cap - 1);
	close(fd);
	if (n < 0)
		return -1;
	buf[n] = '\0';
	return n;
}

/* The unified cgroup (line `0::`) of the process, without the `\n`.  false if it
 * cannot be read (process died meanwhile: the normal /proc race). */
static bool cgroup_di(pid_t pid, char *dove, size_t cap)
{
	char fpath[64], buf[2048];
	char *r;

	snprintf(fpath, sizeof fpath, "/proc/%ld/cgroup", (long)pid);
	if (read_small(fpath, buf, sizeof buf) < 0)
		return false;
	for (r = buf; r && *r; r = strchr(r, '\n') ? strchr(r, '\n') + 1 : NULL) {
		if (strncmp(r, "0::", 3) == 0) {
			size_t n = strcspn(r + 3, "\n");

			if (n >= cap)
				return false;
			memcpy(dove, r + 3, n);
			dove[n] = '\0';
			return true;
		}
	}
	return false;
}

static const char *last_piece(const char *cg)
{
	const char *u = strrchr(cg, '/');
	return u ? u + 1 : cg;
}

/* ⭐ ONE verdict on a session's properties for both roads (the startup one that
 *    waits, the loop's that does not): its PAM service is `remotix` and it has
 *    a scope.  Fills `e` and says true if so. */
static bool fill_candidate(struct candidate_entry *e, GVariant *r, guint32 uid,
                           const char *id, const char *name)
{
	g_autoptr(GVariant) prop = g_variant_get_child_value(r, 0);
	g_autoptr(GVariant) v_serv = g_variant_lookup_value(prop, "Service", G_VARIANT_TYPE_STRING);
	g_autoptr(GVariant) v_scope = g_variant_lookup_value(prop, "Scope", G_VARIANT_TYPE_STRING);

	if (!v_serv || !v_scope ||
	    strcmp(g_variant_get_string(v_serv, NULL), FOUND_AGAIN_PAM_SERVICE) != 0 ||
	    !g_variant_get_string(v_scope, NULL)[0])
		return false;
	e->uid = (uid_t)uid;
	snprintf(e->id, sizeof e->id, "%s", id);
	snprintf(e->scope, sizeof e->scope, "%s", g_variant_get_string(v_scope, NULL));
	snprintf(e->user, sizeof e->user, "%s", name);
	return true;
}

/* The logind sessions with the PAM service `remotix`.  -1 if logind does not answer. */
static int candidate(struct candidate_entry *v, int cap, char *why, size_t how_much)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GDBusConnection) bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &mistake);
	g_autoptr(GVariant) listing = NULL;
	g_autoptr(GVariantIter) it = NULL;
	const char *id, *name, *seat_id, *fpath;
	guint32 uid;
	int n = 0;

	if (!bus) {
		snprintf(why, how_much, "system bus: %s",
		         mistake ? mistake->message : "no reason given");
		return -1;
	}
	listing = g_dbus_connection_call_sync(bus, LOGIND_NAME, LOGIND_PATH, IFACE_MANAGER,
	                                     "ListSessions", NULL, G_VARIANT_TYPE("(a(susso))"),
	                                     G_DBUS_CALL_FLAGS_NONE, WAIT_MS, NULL, &mistake);
	if (!listing) {
		snprintf(why, how_much, "logind ListSessions: %s",
		         mistake ? mistake->message : "no reason given");
		return -1;
	}
	g_variant_get(listing, "(a(susso))", &it);
	while (g_variant_iter_next(it, "(&su&s&s&o)", &id, &uid, &name, &seat_id, &fpath)) {
		g_autoptr(GVariant) r = NULL;

		if (n >= cap)
			break;
		r = g_dbus_connection_call_sync(bus, LOGIND_NAME, fpath,
		                                "org.freedesktop.DBus.Properties", "GetAll",
		                                g_variant_new("(s)", IFACE_SESSION),
		                                G_VARIANT_TYPE("(a{sv})"), G_DBUS_CALL_FLAGS_NONE,
		                                WAIT_MS, NULL, NULL);
		/* ⚠ Gone between the list and the question: the normal logind race. */
		if (!r)
			continue;
		if (fill_candidate(&v[n], r, uid, id, name))
			n++;
	}
	return n;
}

/* ⭐ The heart: a single pass over /proc for all the candidates `c` (`nc` > 0).
 * `solo_uid` (if not (uid_t)-1) restricts to one user. */
static int scan(const struct candidate_entry *c, int nc, RediscoveredDesktop *v, int cap,
                uid_t solo_uid, char *why, size_t how_much)
{
	int matches = 0;
	DIR *proc;
	struct dirent *e;

	proc = opendir("/proc");
	if (!proc) {
		snprintf(why, how_much, "/proc: %s", strerror(errno));
		return -1;
	}
	while ((e = readdir(proc)) != NULL) {
		char fpath[64], stat_buf[1024], cg[1024], cg_padre[1024];
		const char *is_closed;
		long pid, ppid = 0, pgrp = 0, sid = 0;
		char state;
		struct stat st;
		int which = -1;

		if (e->d_name[0] < '1' || e->d_name[0] > '9')
			continue;
		pid = strtol(e->d_name, NULL, 10);
		snprintf(fpath, sizeof fpath, "/proc/%ld/stat", pid);
		if (read_small(fpath, stat_buf, sizeof stat_buf) < 0)
			continue;
		/* ⚠ The name is in parentheses and may contain some: start from the LAST one. */
		is_closed = strrchr(stat_buf, ')');
		if (!is_closed || sscanf(is_closed + 1, " %c %ld %ld %ld", &state, &ppid, &pgrp, &sid) != 4)
			continue;
		/* 1. leader of its own process session — the setsid signature */
		if (sid != pid || state == 'Z')
			continue;
		snprintf(fpath, sizeof fpath, "/proc/%ld", pid);
		if (stat(fpath, &st) != 0 || st.st_uid == 0)
			continue;
		if (solo_uid != (uid_t)-1 && st.st_uid != solo_uid)
			continue;
		/* 2. inside the scope of a `remotix` session of the same user */
		if (!cgroup_di((pid_t)pid, cg, sizeof cg))
			continue;
		for (int i = 0; i < nc; i++)
			if (c[i].uid == st.st_uid && strcmp(last_piece(cg), c[i].scope) == 0) {
				which = i;
				break;
			}
		if (which < 0)
			continue;
		/* 3. and the parent OUTSIDE that scope: orphan of `setsid --fork`, not the
		 *    shell of a terminal opened in the desktop */
		if (ppid > 0 && cgroup_di((pid_t)ppid, cg_padre, sizeof cg_padre) &&
		    strcmp(cg_padre, cg) == 0)
			continue;
		/* one per user: the first found; the others are only counted */
		{
			int already = -1;

			for (int k = 0; k < matches; k++)
				if (v[k].uid == st.st_uid)
					already = k;
			if (already >= 0 || matches >= cap)
				continue;
			memset(&v[matches], 0, sizeof v[matches]);
			snprintf(v[matches].user, sizeof v[matches].user, "%s", c[which].user);
			v[matches].uid = st.st_uid;
			snprintf(v[matches].session, sizeof v[matches].session, "%s", c[which].id);
			v[matches].stage = (pid_t)pid;
			{
				const char *is_open = strchr(stat_buf, '(');
				size_t n = is_open ? (size_t)(is_closed - is_open - 1) : 0;

				if (n >= sizeof v[matches].comm)
					n = sizeof v[matches].comm - 1;
				if (is_open)
					memcpy(v[matches].comm, is_open + 1, n);
				v[matches].comm[n] = '\0';
			}
			matches++;
		}
	}
	closedir(proc);
	for (int k = 0; k < matches; k++)
		for (int i = 0; i < nc; i++)
			if (c[i].uid == v[k].uid)
				v[k].sessions++;
	return matches;
}

/* The question that WAITS: logind now, then /proc. */
static int search(RediscoveredDesktop *v, int cap, uid_t solo_uid, char *why, size_t how_much)
{
	struct candidate_entry *c = calloc(MAX_CANDIDATES, sizeof *c);
	int nc, n;

	if (!c) {
		snprintf(why, how_much, "out of memory");
		return -1;
	}
	nc = candidate(c, MAX_CANDIDATES, why, how_much);
	if (nc <= 0) {
		free(c);
		return nc;
	}
	n = scan(c, nc, v, cap, solo_uid, why, how_much);
	free(c);
	return n;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ THE CHECK THAT DOES NOT WAIT — 15 Oct 2026.
 *
 * ⛔ THE DEFECT: `found_again_sweep()` (`main.c`) calls `rediscover_search()`
 *    every 10 s from the loop that delivers the frames, and the logind half
 *    was synchronous: one `ListSessions` plus one `GetAll` for EVERY session
 *    of the machine, 300 ms ceiling each — a slow logind froze every
 *    session for (1+k) × 300 ms.
 *
 * ⭐ THE CURE: the FIRST search of the process (startup, before the loop:
 *    `found_again_at_startup()`) still waits, because it must know.  Every
 *    later one:
 *      1. turns this file's own GLib context, never blocking
 *         (`rediscover_collect()`): what logind answered is collected, and a
 *         round out longer than ASYNC_WAIT_MS is cut;
 *      2. uses the newest COMPLETE answer, if younger than ANSWER_MAX_AGE_MS,
 *         and walks /proc with it NOW (the /proc half is local and is still
 *         read at the moment of the call: a stage that died is seen dead at
 *         once);
 *      3. sends the next question, and returns.
 *    ⛔ No answer yet, a failed one, or one too old ⇒ -1, «I don't know»:
 *       exactly what a silent logind has always returned, and the caller
 *       keeps the desktops in the counts until it knows.
 *
 * ⚠ WHAT CHANGES, declared: the logind half is one or two checks old (≤ 20 s;
 *   less if `main.c` calls `rediscover_collect()` at every pass).  It
 *   only says which `remotix` sessions and scopes exist; a desktop whose
 *   session ended in those 10 s has no live stage in /proc either, so it is
 *   removed at once all the same.  ⛔ And a `GetAll` that does not come back
 *   within ASYNC_WAIT_MS makes the whole answer «I don't know», where the
 *   waiting road skips that session: all the `GetAll`s leave together here,
 *   and skipping one could drop a live desktop from the counts.
 */
struct question {
	GCancellable *cancel;   /* cuts the round in flight */
	uint64_t round_sent_ms; /* when the round in flight was sent */
	unsigned pending;
	bool failed;
	bool listed;
	char why[256];
	uint64_t started_ms;
	unsigned n;                      /* sessions listed */
	struct candidate_entry *listed_v; /* one per listed session, in list order */
	bool *is_candidate;
};

static struct {
	bool ever;                  /* the first (waiting) search was made */
	GMainContext *ctx;
	struct question *inflight;
	/* the newest complete answer */
	bool have;
	bool failed;
	char why[256];
	uint64_t asked_ms;
	struct candidate_entry *c;
	int nc;
} later;

struct one_session {
	struct question *q;
	unsigned i;
};

static void question_free(struct question *q)
{
	if (!q)
		return;
	free(q->listed_v);
	free(q->is_candidate);
	g_clear_object(&q->cancel);
	free(q);
}

/* ⭐ The answer is complete: it becomes the one the next search uses. */
static void question_done(struct question *q)
{
	later.inflight = NULL;
	later.have = true;
	later.asked_ms = q->started_ms;
	later.failed = q->failed;
	snprintf(later.why, sizeof later.why, "%s", q->why);
	later.nc = 0;
	if (!q->failed)
		for (unsigned i = 0; i < q->n && later.nc < MAX_CANDIDATES; i++)
			if (q->is_candidate[i])
				later.c[later.nc++] = q->listed_v[i];
	question_free(q);
}

static void on_getall(GObject *src, GAsyncResult *res, gpointer data)
{
	struct one_session *o = data;
	struct question *q = o->q;
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) r = g_dbus_connection_call_finish(G_DBUS_CONNECTION(src), res, &mistake);

	if (r) {
		struct candidate_entry *e = &q->listed_v[o->i];
		struct candidate_entry from = *e;

		q->is_candidate[o->i] = fill_candidate(e, r, from.uid, from.id, from.user);
	} else if (g_error_matches(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT) ||
	           g_error_matches(mistake, G_IO_ERROR, G_IO_ERROR_CANCELLED) ||
	           g_error_matches(mistake, G_DBUS_ERROR, G_DBUS_ERROR_NO_REPLY) ||
	           g_error_matches(mistake, G_DBUS_ERROR, G_DBUS_ERROR_TIMEOUT) ||
	           g_error_matches(mistake, G_DBUS_ERROR, G_DBUS_ERROR_TIMED_OUT)) {
		/* ⛔ Not «gone between the list and the question»: logind did not
		 *    answer, and the whole answer is «I don't know». */
		if (!q->failed)
			snprintf(q->why, sizeof q->why, "logind GetAll: %s",
			         g_error_matches(mistake, G_IO_ERROR, G_IO_ERROR_CANCELLED)
			         ? "no answer within " G_STRINGIFY(ASYNC_WAIT_MS) " ms"
			         : mistake->message);
		q->failed = true;
	}
	/* ⚠ Any other error: gone between the list and the question — the
	 *   normal logind race, skipped as on the waiting road. */
	g_free(o);
	if (--q->pending == 0)
		question_done(q);
}

static void on_list(GObject *src, GAsyncResult *res, gpointer data)
{
	struct question *q = data;
	GDBusConnection *bus = G_DBUS_CONNECTION(src);
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) listing = g_dbus_connection_call_finish(bus, res, &mistake);
	g_autoptr(GVariantIter) it = NULL;
	const char *id, *name, *seat_id, *fpath;
	guint32 uid;
	gsize total;

	if (!listing) {
		snprintf(q->why, sizeof q->why, "logind ListSessions: %s",
		         g_error_matches(mistake, G_IO_ERROR, G_IO_ERROR_CANCELLED)
		         ? "no answer within " G_STRINGIFY(ASYNC_WAIT_MS) " ms"
		         : mistake ? mistake->message : "no reason given");
		q->failed = true;
	} else {
		g_variant_get(listing, "(a(susso))", &it);
		total = g_variant_iter_n_children(it);
		if (total > MAX_LISTED)
			total = MAX_LISTED;
		q->listed_v = calloc(total ? total : 1, sizeof *q->listed_v);
		q->is_candidate = calloc(total ? total : 1, sizeof *q->is_candidate);
		if (!q->listed_v || !q->is_candidate) {
			snprintf(q->why, sizeof q->why, "out of memory");
			q->failed = true;
		} else {
			q->round_sent_ms = log_now_ms();
			g_main_context_push_thread_default(later.ctx);
			while (q->n < total &&
			       g_variant_iter_next(it, "(&su&s&s&o)", &id, &uid, &name, &seat_id, &fpath)) {
				struct one_session *o = g_new0(struct one_session, 1);
				struct candidate_entry *e = &q->listed_v[q->n];

				e->uid = (uid_t)uid;
				snprintf(e->id, sizeof e->id, "%s", id);
				snprintf(e->user, sizeof e->user, "%s", name);
				o->q = q;
				o->i = q->n++;
				q->pending++;
				g_dbus_connection_call(bus, LOGIND_NAME, fpath,
				                       "org.freedesktop.DBus.Properties", "GetAll",
				                       g_variant_new("(s)", IFACE_SESSION),
				                       G_VARIANT_TYPE("(a{sv})"), G_DBUS_CALL_FLAGS_NONE,
				                       G_MAXINT, q->cancel, on_getall, o);
			}
			g_main_context_pop_thread_default(later.ctx);
		}
	}
	if (--q->pending == 0)
		question_done(q);
}

static void ask_later(void)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GDBusConnection) bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &mistake);
	struct question *q = calloc(1, sizeof *q);

	if (!q)
		return;
	q->started_ms = log_now_ms();
	if (!bus) {
		snprintf(q->why, sizeof q->why, "system bus: %s",
		         mistake ? mistake->message : "no reason given");
		q->failed = true;
		later.inflight = q;
		question_done(q);
		return;
	}
	q->pending = 1;
	q->cancel = g_cancellable_new();
	q->round_sent_ms = q->started_ms;
	later.inflight = q;
	g_main_context_push_thread_default(later.ctx);
	g_dbus_connection_call(bus, LOGIND_NAME, LOGIND_PATH, IFACE_MANAGER, "ListSessions",
	                       NULL, G_VARIANT_TYPE("(a(susso))"), G_DBUS_CALL_FLAGS_NONE,
	                       G_MAXINT, q->cancel, on_list, q);
	g_main_context_pop_thread_default(later.ctx);
}

void rediscover_collect(void)
{
	if (!later.ctx)
		return;
	while (g_main_context_iteration(later.ctx, FALSE))
		;
	if (later.inflight && log_now_ms() - later.inflight->round_sent_ms > ASYNC_WAIT_MS) {
		g_cancellable_cancel(later.inflight->cancel);
		while (g_main_context_iteration(later.ctx, FALSE))
			;
	}
}

int rediscover_search(RediscoveredDesktop *v, int cap, char *why, size_t how_much)
{
	uint64_t now;
	int n;

	if (why && how_much)
		why[0] = '\0';
	if (!v || cap <= 0)
		return 0;
	if (!later.ctx) {
		later.ctx = g_main_context_new();
		later.c = calloc(MAX_CANDIDATES, sizeof *later.c);
		if (!later.c) {
			snprintf(why, how_much, "out of memory");
			return -1;
		}
	}
	/* ⭐ The first search of the process waits: it is the startup's, before
	 *    the loop, and it must know.  Its answer is also the first one the
	 *    loop's check uses. */
	if (!later.ever) {
		later.ever = true;
		later.asked_ms = log_now_ms();
		later.nc = candidate(later.c, MAX_CANDIDATES, later.why, sizeof later.why);
		later.have = true;
		later.failed = later.nc < 0;
		if (later.failed) {
			later.nc = 0;
			snprintf(why, how_much, "%s", later.why);
			return -1;
		}
		return later.nc ? scan(later.c, later.nc, v, cap, (uid_t)-1, why, how_much) : 0;
	}

	rediscover_collect();
	now = log_now_ms();
	if (!later.have) {
		snprintf(why, how_much, "logind has not answered yet");
		n = -1;
	} else if (later.failed) {
		snprintf(why, how_much, "%s", later.why);
		n = -1;
	} else if (now - later.asked_ms > ANSWER_MAX_AGE_MS) {
		snprintf(why, how_much, "the newest answer of logind is %llu s old",
		         (unsigned long long)((now - later.asked_ms) / 1000));
		n = -1;
	} else {
		n = later.nc ? scan(later.c, later.nc, v, cap, (uid_t)-1, why, how_much) : 0;
	}
	/* ⭐ And the next question leaves AFTER this answer is used. */
	if (!later.inflight)
		ask_later();
	return n;
}

int rediscover_alive(uid_t uid, RediscoveredDesktop *d)
{
	RediscoveredDesktop uno;
	char why[256] = "";
	int n = search(&uno, 1, uid, why, sizeof why);

	if (n < 0)
		return -1;
	if (n > 0 && d)
		*d = uno;
	return n > 0 ? 1 : 0;
}
