/*
 * sentinel.c — the sender that `0x04` and `0x05` were missing.
 *
 * The why of every choice is in `sentinel.h`, which is read before this
 * file.  Here there is only the how.
 */
#include "sentinel.h"

#include <gio/gio.h>
#include <string.h>
#include <unistd.h>

#include "log.h"

#define LOGIND_NAME "org.freedesktop.login1"
#define LOGIND_PATH "/org/freedesktop/login1"
#define IFACE_MANAGER "org.freedesktop.login1.Manager"
#define IFACE_SESSION "org.freedesktop.login1.Session"

/*
 * ⛔ 300 ms, and not v1's 5000.
 *
 * ⭐ 15 Oct 2026: for the CHECK (`sentinel_locals()`) it is now the ceiling of
 *    a question asked WITHOUT waiting — the loop sends it and reads the answer
 *    at the next check; nothing stops while logind thinks.  For the child's
 *    two questions (`sentinel_shutdown_forbidden()`, `sentinel_without_seat()`)
 *    it is still a synchronous wait, and there it costs nobody: the child does
 *    not deliver frames while it starts.
 */
#define WAIT_MS 300

/*
 * ⭐ The question at `ATTACH` (`sentinel_local()`) is still SYNCHRONOUS —
 *    `rcp.c` wants the verdict before it answers — but with a SHORTER ceiling
 *    than the check: `[M]` §6.13, a healthy logind answers in 2.4-2.6 ms and
 *    the worst ever seen is 13.14 ms, so 100 ms only ever cuts a logind that
 *    is not well.  ⛔ And when logind has just failed to answer (here or in
 *    the check), the attach does NOT ask again for SILENT_BACKOFF_MS: it
 *    answers «no local session», which is what an unanswered question has
 *    always meant (I1).  Without this pause a slow logind would cost every
 *    attach (1+k) × the ceiling, inside the loop that delivers everyone's
 *    frames.
 */
#define ATTACH_WAIT_MS 100
#define SILENT_BACKOFF_MS 30000

/*
 * ⛔ An answer of the check is used ONCE, and only if its question is younger
 *    than this: the check asks every 2 s (`LOCAL_SWEEP_MS` in `main.c`), so a
 *    fresh answer is ~2 s old, ~4 s when it needed a second round (`GetAll`,
 *    see above `sweep_done()`).  An older one (the loop stalled, or the checks
 *    stopped because nobody was attached) is a fact about another moment, and
 *    acting on it could close a session for a local one that has already
 *    ended.  ⇒ Too old = «I don't know» = no local session (I1).
 */
#define ANSWER_MAX_AGE_MS 7000

/* Beyond this threshold the slowness is written: it is the signal that the
 * «synchronous» choice must be redone as a helper process, like PAM (`DECISIONS.md` §1.10).
 *
 * ⛔⛔ IT WAS 20 ms, AND IT WOULD NEVER HAVE SPOKEN — `[M]` 25 August 2026, §6.13: on
 *      this machine `ListSessions` costs **2.4-2.6 ms** median and the
 *      worst call seen anywhere is **13.14 ms**.  ⇒ A threshold at 20 sits
 *      ABOVE the worst measured case: it is an alarm that by construction never
 *      rings, that is form E1 («an instrument that exists and does not speak»).
 * ⭐ 10 ms is above the median by a factor of **four** — it is not noise — and
 *    below the worst measured: the first time logind really slows down, the
 *    line comes out.  ⚠ And it is not the only belt: `sentinel_counts()` brings the
 *    WORST to the log once a minute, so the number is there even
 *    when this threshold is silent. */
#define SLOW_MS 10

/* ⚠ `mir` is here because it was in v1: we do not needs it, but a Mir session is
 *   graphical all the same, and counting it is more prudent than ignoring it. */
static const char *GRAPHICAL_TYPES[] = { "wayland", "x11", "mir", NULL };

/* One local graphical session found by a check: `order` is its place in
 * `ListSessions`, because the first one in the list wins, as it always has. */
struct seen {
	unsigned order;
	char *name, *id, *kind, *seat;
};

/* ⭐ One check in flight: its question, and what has come back so far. */
struct sweep {
	sentinel *s;
	uint64_t started_ms;
	/* ⭐ What logind cost, round by round (the list, then the `GetAll`s):
	 *    from the send to the last answer of the round at the bus thread.
	 *    ⚠ Not from the first send to the last answer: between the two
	 *    rounds the question waits for US (the next turn of the context). */
	uint64_t round_cost_ms[2];
	unsigned pending;        /* questions sent and not answered yet */
	bool failed;             /* `ListSessions` did not answer */
	bool closing;            /* the sentinel is closing */
	bool cancelled;          /* … and this check was cut by it */
	GCancellable *cancel;    /* cuts the round in flight */
	uint64_t round_sent_ms;  /* when the round in flight was sent */
	char **users;            /* the names asked (a copy: theirs live in `rcp`) */
	GPtrArray *seen;         /* of `struct seen` */
};

/* One question of a check, with its D-Bus serial for the stopwatch below. */
struct ask {
	struct sweep *q;
	guint32 serial;
	uint64_t sent_ms;
	unsigned order;
	char *name, *id, *seat;
};

struct sentinel {
	GDBusConnection *bus;
	uint64_t calls;
	uint64_t worst_ms;
	/* ⛔ A single line when logind stops answering, not one per turn:
	 * a re-check every two seconds would fill the log with a fact that
	 * counts once (`LESSONS.md` §6.2-ter: the number that explains everything is
	 * searched for, and in a flooded log it is not found). */
	bool mute_already_logged;
	/* ⭐ The pause of the attach question (`SILENT_BACKOFF_MS`): when it last
	 *    asked, or when the check last found logind silent. */
	uint64_t silent_probe_ms;
	/* ⭐ The check without waiting: its own GLib context, which nobody else
	 *    runs — it is turned (never blocking) at the start of every check. */
	GMainContext *ctx;
	guint filter;
	struct sweep *inflight;  /* the question asked at the previous check */
	struct sweep *answer;    /* its answer, complete, not used yet */
};

/*
 * ⭐ THE STOPWATCH OF THE ASYNCHRONOUS QUESTIONS.
 *
 * An answer is handed to us at the NEXT check, two seconds later: timing it
 * there would write «2000 ms» for a logind that answered in 3.  ⇒ The arrival
 * is stamped in the bus thread itself, by a filter that sees every incoming
 * message, and is matched to the question by its serial
 * (`g_dbus_connection_get_last_serial()`).  `sentinel_counts()` and the
 * `SLOW_MS` line keep measuring logind, not our timetable.
 * ⚠ Static, and not in `struct sentinel`: the filter may still run once
 *   after `g_dbus_connection_remove_filter()` (GDBus documents the race), and
 *   it must never touch memory that has been freed.
 */
#define STOPWATCH_SLOTS 64
static GMutex stopwatch_lock;
static struct {
	guint32 serial;
	uint64_t arrived_ms;
} stopwatch[STOPWATCH_SLOTS];

static GDBusMessage *stopwatch_filter(GDBusConnection *c, GDBusMessage *m,
                                      gboolean incoming, gpointer data)
{
	GDBusMessageType t;
	guint32 r;

	(void)c;
	(void)data;
	if (!incoming)
		return m;
	t = g_dbus_message_get_message_type(m);
	if (t != G_DBUS_MESSAGE_TYPE_METHOD_RETURN && t != G_DBUS_MESSAGE_TYPE_ERROR)
		return m;
	r = g_dbus_message_get_reply_serial(m);
	g_mutex_lock(&stopwatch_lock);
	for (int i = 0; r && i < STOPWATCH_SLOTS; i++)
		if (stopwatch[i].serial == r && !stopwatch[i].arrived_ms)
			stopwatch[i].arrived_ms = log_now_ms();
	g_mutex_unlock(&stopwatch_lock);
	return m;
}

/* When the answer to `serial` arrived; 0 if it never did (timeout, cancel). */
static uint64_t stopwatch_take(guint32 serial)
{
	uint64_t at = 0;

	g_mutex_lock(&stopwatch_lock);
	for (int i = 0; serial && i < STOPWATCH_SLOTS; i++)
		if (stopwatch[i].serial == serial) {
			/* ⚠ Every slot with this serial: a call refused before it
			 *   was sent leaves the previous serial behind, twice. */
			if (stopwatch[i].arrived_ms > at)
				at = stopwatch[i].arrived_ms;
			stopwatch[i].serial = 0;
			stopwatch[i].arrived_ms = 0;
		}
	g_mutex_unlock(&stopwatch_lock);
	return at;
}

sentinel *sentinel_open(void)
{
	g_autoptr(GError) mistake = NULL;
	GDBusConnection *bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &mistake);
	sentinel *s;

	if (!bus) {
		registro_dice(LOG_SESSION,
		              "⛔ logind unreachable (%s): the rule of §5.1 "
		              "— local session against remote, reasons 0x04 and 0x05 "
		              "— is NOT in force on this server",
		              mistake ? mistake->message : "no reason given");
		return NULL;
	}

	s = g_new0(sentinel, 1);
	s->bus = bus;
	s->ctx = g_main_context_new();
	s->filter = g_dbus_connection_add_filter(bus, stopwatch_filter, NULL, NULL);
	registro_dice(LOG_SESSION,
	              "local session guardian ready (system bus); the "
	              "discriminant is the SEAT, not «Remote»");
	return s;
}

static void sweep_free(struct sweep *q)
{
	if (!q)
		return;
	g_strfreev(q->users);
	g_ptr_array_unref(q->seen);
	g_clear_object(&q->cancel);
	g_free(q);
}

static void seen_free(gpointer p)
{
	struct seen *v = p;

	g_free(v->name);
	g_free(v->id);
	g_free(v->kind);
	g_free(v->seat);
	g_free(v);
}

void sentinel_close(sentinel *s)
{
	if (!s)
		return;
	/* ⚠ A check in flight holds `s`: it is cancelled, and its callbacks are
	 *   run to the end (a cancelled call answers at once) before anything is
	 *   freed. */
	if (s->inflight) {
		s->inflight->closing = true;
		g_cancellable_cancel(s->inflight->cancel);
		while (s->inflight)
			g_main_context_iteration(s->ctx, TRUE);
	}
	sweep_free(s->answer);
	if (s->filter)
		g_dbus_connection_remove_filter(s->bus, s->filter);
	g_clear_pointer(&s->ctx, g_main_context_unref);
	g_clear_object(&s->bus);
	g_free(s);
}

static GVariant *call(sentinel *s, const char *fpath,
                        const char *interfaccia, const char *method,
                        GVariant *call_args, const GVariantType *kind,
                        int wait_ms)
{
	return g_dbus_connection_call_sync(s->bus, LOGIND_NAME, fpath, interfaccia,
	                                   method, call_args, kind,
	                                   G_DBUS_CALL_FLAGS_NONE, wait_ms, NULL,
	                                   NULL);
}

/* ⛔ logind did not answer: said ONCE, and the attach question pauses. */
static void logind_silent(sentinel *s, int wait_ms)
{
	s->silent_probe_ms = log_now_ms();
	if (s->mute_already_logged)
		return;
	/* ⛔ Carry on WITHOUT the rule instead of locking everyone out: I1.
	 * ⚠ And say it once only, not at every re-check. */
	registro_dice(LOG_SESSION,
	              "⛔ logind did not answer within %d ms: the rule "
	              "of §5.1 is not applied while it is silent (and this "
	              "line is not repeated; the question at ATTACH is asked "
	              "again at most every %d s meanwhile)",
	              wait_ms, SILENT_BACKOFF_MS / 1000);
	s->mute_already_logged = true;
}

static void logind_answers(sentinel *s)
{
	if (!s->mute_already_logged)
		return;
	registro_dice(LOG_SESSION, "logind is answering again");
	s->mute_already_logged = false;
}

/* The measured cost of one question, into the counts and, if slow, the log. */
static void count_cost(sentinel *s, uint64_t cost, size_t amount, bool waited)
{
	s->calls++;
	if (cost > s->worst_ms)
		s->worst_ms = cost;
	if (cost >= SLOW_MS)
		registro_dice(LOG_SESSION,
		              "⚠ logind took %llu ms for the list of "
		              "sessions (tenants=%zu in a single question%s): if it "
		              "repeats, this question must move to a helper "
		              "process like PAM",
		              (unsigned long long) cost, amount,
		              waited ? ", and the loop waited for it"
		                     : ", asked without stopping the loop");
}

/*
 * The type of the session, if it is graphical, of user class, not remote and not
 * closing.  NULL if it is not — or if it vanished between the list and this question
 * (`response` NULL), which is logind's normal race condition and not a fault.
 *
 * ⛔ ONE verdict for both roads (the attach that waits, the check that does
 *    not): two drafts of «what is a local session» would be two truths.
 */
static char *kind_if_graphical(GVariant *response)
{
	g_autoptr(GVariant) property = NULL;
	g_autoptr(GVariant) v_type = NULL;
	g_autoptr(GVariant) v_class = NULL;
	g_autoptr(GVariant) v_remote = NULL;
	g_autoptr(GVariant) v_state = NULL;
	const char *kind;
	bool graphical = false;

	if (!response)
		return NULL;
	property = g_variant_get_child_value(response, 0);

	v_type = g_variant_lookup_value(property, "Type", G_VARIANT_TYPE_STRING);
	v_class = g_variant_lookup_value(property, "Class", G_VARIANT_TYPE_STRING);
	v_remote = g_variant_lookup_value(property, "Remote", G_VARIANT_TYPE_BOOLEAN);
	v_state = g_variant_lookup_value(property, "State", G_VARIANT_TYPE_STRING);
	if (!v_type || !v_class)
		return NULL;

	kind = g_variant_get_string(v_type, NULL);
	for (gsize i = 0; GRAPHICAL_TYPES[i]; i++)
		if (g_strcmp0(kind, GRAPHICAL_TYPES[i]) == 0)
			graphical = true;
	if (!graphical)
		return NULL;
	/* `greeter`, `lock-screen` and `background` are not the user at work. */
	if (g_strcmp0(g_variant_get_string(v_class, NULL), "user") != 0)
		return NULL;
	/* ⚠ The second belt.  `PAM_RHOST` is set by the PAM check
	 *   (`authentication.c`) and by the child's PAM session (`child.c`), so our
	 *   sessions show `Remote=yes` and this line cuts them; the SEAT does the
	 *   rest. */
	if (v_remote && g_variant_get_boolean(v_remote))
		return NULL;
	/* `closing` is the session that is going away: counting it would lock out
	 * whoever reconnects right while the local one ends. */
	if (v_state && g_strcmp0(g_variant_get_string(v_state, NULL), "closing") == 0)
		return NULL;

	return g_strdup(kind);
}

static void clear_answers(size_t amount, bool *local, char *which_ones,
                          size_t width)
{
	/* ⛔ It is ALWAYS cleared, and first: a vector left as it was would tell the
	 *    caller the answer of the previous re-check, which is the worst lie —
	 *    indistinguishable from a fresh answer. */
	for (size_t k = 0; k < amount; k++) {
		local[k] = false;
		if (which_ones && width)
			which_ones[k * width] = '\0';
	}
}

/* ⭐ The session found goes to EVERY position asking for that name and not yet
 *    answered (the names may repeat).  Returns how many it answered. */
static size_t mark(const char *name, const char *id, const char *kind,
                   const char *seat, const char *const *users, size_t amount,
                   bool *local, char *which_ones, size_t width)
{
	size_t n = 0;

	for (size_t k = 0; k < amount; k++) {
		if (local[k] || g_strcmp0(name, users[k]) != 0)
			continue;
		local[k] = true;
		n++;
		if (which_ones && width)
			g_snprintf(which_ones + k * width, width,
			           "session %s, %s on %s", id, kind, seat);
	}
	return n;
}

/*
 * ⭐⭐⭐ THE QUESTION THAT WAITS — the attach's (`sentinel_local()`, `amount`
 *       = 1), and the shape that `[M]` §6.13 settled: ONE `ListSessions`
 *       for all the names, `N × D` that became `D`.
 */
static size_t ask_now(sentinel *s, const char *const *users, size_t amount,
                      bool *local, char *which_ones, size_t width)
{
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariantIter) listing = NULL;
	const char *id, *name, *seat, *fpath;
	guint32 uid;
	uint64_t start;
	size_t found = 0;
	size_t remain = amount;

	start = log_now_ms();
	/* ⛔ logind has just been silent: no new wait for SILENT_BACKOFF_MS. */
	if (s->mute_already_logged && start - s->silent_probe_ms < SILENT_BACKOFF_MS)
		return 0;
	s->silent_probe_ms = start;

	response = call(s, LOGIND_PATH, IFACE_MANAGER, "ListSessions", NULL,
	                  G_VARIANT_TYPE("(a(susso))"), ATTACH_WAIT_MS);
	if (!response) {
		logind_silent(s, ATTACH_WAIT_MS);
		return 0;
	}
	logind_answers(s);

	g_variant_get(response, "(a(susso))", &listing);
	/* ⭐ Exit as soon as ALL have an answer (`remain == 0`), not as soon as one
	 *    has it: the question may be for N names, and stopping at the first
	 *    would leave the others with a `false` that looks like an answer. */
	while (remain &&
	       g_variant_iter_next(listing, "(&su&s&s&o)", &id, &uid, &name, &seat,
	                           &fpath)) {
		g_autofree char *kind = NULL;
		g_autoptr(GVariant) props = NULL;
		bool needs = false;

		/* ⭐ The two conditions that discard almost everything are ALREADY in the list,
		 *    and apply without opening anything: the wrong user, and — ⛔ the
		 *    line that carries all the weight — **the empty seat**, which is what
		 *    makes a session local and which ours do not have. */
		if (!seat || !*seat)
			continue;
		for (size_t k = 0; k < amount; k++)
			if (!local[k] && g_strcmp0(name, users[k]) == 0)
				needs = true;
		if (!needs)
			continue;

		/* ⚠ Only for a session that ALREADY has a seat and a name we care
		 *   about — that is for the real local session.  On a headless
		 *   machine it never happens. */
		props = call(s, fpath, "org.freedesktop.DBus.Properties", "GetAll",
		             g_variant_new("(s)", IFACE_SESSION),
		             G_VARIANT_TYPE("(a{sv})"), ATTACH_WAIT_MS);
		kind = kind_if_graphical(props);
		if (!kind)
			continue;

		{
			size_t got = mark(name, id, kind, seat, users, amount, local,
			                  which_ones, width);
			found += got;
			remain -= got;
		}
	}

	count_cost(s, log_now_ms() - start, amount, true);
	return found;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐⭐ THE CHECK THAT DOES NOT WAIT — 15 Oct 2026.
 *
 * ⛔ THE DEFECT: `wt_watch_locals()` runs every 2 s inside the loop that
 *    delivers the frames, and asked synchronously: one `ListSessions` plus one
 *    `GetAll` per seated session of a served user, up to 300 ms each.  A slow
 *    logind froze EVERY session for (1+k) × 300 ms every two seconds — the
 *    «helper process» this file promised «if it repeats».
 *
 * ⭐ THE CURE, without a thread: the question goes out with
 *    `g_dbus_connection_call()` and its answers are dispatched on a GLib
 *    context of our own, which only this file turns, and never blocking
 *    (`g_main_context_iteration(…, FALSE)`).  GDBus reads the socket in its
 *    own bus thread, which it already had.  ⇒ Every check:
 *      1. turns the context (`sentinel_collect()`): what logind answered
 *         since the previous turn is collected, and a round older than
 *         WAIT_MS is cut;
 *      2. answers the caller with the newest COMPLETE answer (younger than
 *         ANSWER_MAX_AGE_MS, used once), for the names asked now;
 *      3. sends the next question if none is in flight, and returns.
 * ⛔ WAIT_MS is still the ceiling, and it is judged on the time the answer
 *    reached the bus thread (the stopwatch above), not on when we look: a
 *    `ListSessions` that came back in 400 ms is «did not answer within
 *    300 ms», exactly as before.  GDBus's own timeout is not used — its timer
 *    would only run when the context is turned, and could fire before an
 *    answer that had arrived in time.
 *
 * ⚠ WHAT CHANGES, declared: the answer arrives ONE CHECK LATER — and TWO
 *   when a served user has a seated session, because the `GetAll` can only be
 *   sent once the list has been read.  The delay between «the user sat down
 *   at the machine» and «the remote session drops» goes from ≤ 2 s to ≤ 6 s
 *   (to ~2-4 s if `main.c` calls `sentinel_collect()` at every pass).  ⛔ WHAT DOES NOT: what is decided from the
 *   answers — the seat, the name, `kind_if_graphical()`, the first session in
 *   the list for each name, `false` for whoever logind did not answer about
 *   (I1), the once-only silent line.  A name that was not asked in the
 *   question answered (a new tenant) reads `false` until the next check.
 */
static void sweep_done(struct sweep *q)
{
	sentinel *s = q->s;

	s->inflight = NULL;
	if (q->closing) {
		sweep_free(q);
		return;
	}
	if (q->failed) {
		logind_silent(s, WAIT_MS);
		sweep_free(q);
		return;
	}
	logind_answers(s);
	count_cost(s, q->round_cost_ms[0] + q->round_cost_ms[1],
	           g_strv_length(q->users), false);
	sweep_free(s->answer);
	s->answer = q;
}

/* The answer came back: what it cost (stamped in the bus thread), or the
 * ceiling if none came in time.  ⛔ True only if it came within WAIT_MS of
 * its send. */
static bool note_reply(struct sweep *q, int round, guint32 serial, uint64_t sent_ms)
{
	uint64_t at = stopwatch_take(serial);
	bool in_time = at && at >= sent_ms && at - sent_ms <= WAIT_MS;
	uint64_t cost = in_time ? at - sent_ms : WAIT_MS;

	if (cost > q->round_cost_ms[round])
		q->round_cost_ms[round] = cost;
	return in_time;
}

static guint32 send_async(sentinel *s, struct sweep *q, const char *fpath,
                          const char *iface, const char *method, GVariant *args,
                          const GVariantType *kind, GAsyncReadyCallback cb,
                          gpointer data)
{
	guint32 serial;

	/* ⚠ The lock is held across the send, so that the filter cannot stamp
	 *   the answer before its serial is in the table. */
	g_mutex_lock(&stopwatch_lock);
	g_main_context_push_thread_default(s->ctx);
	g_dbus_connection_call(s->bus, LOGIND_NAME, fpath, iface, method, args,
	                       kind, G_DBUS_CALL_FLAGS_NONE, G_MAXINT, q->cancel,
	                       cb, data);
	g_main_context_pop_thread_default(s->ctx);
	serial = g_dbus_connection_get_last_serial(s->bus);
	for (int i = 0; i < STOPWATCH_SLOTS; i++)
		if (!stopwatch[i].serial) {
			stopwatch[i].serial = serial;
			stopwatch[i].arrived_ms = 0;
			break;
		}
	g_mutex_unlock(&stopwatch_lock);
	return serial;
}

static void on_getall(GObject *src, GAsyncResult *res, gpointer data)
{
	struct ask *a = data;
	struct sweep *q = a->q;
	g_autoptr(GVariant) props =
		g_dbus_connection_call_finish(G_DBUS_CONNECTION(src), res, NULL);
	/* ⚠ Late or missing: skipped, as the waiting road skips it. */
	bool in_time = note_reply(q, 1, a->serial, a->sent_ms);
	char *kind = in_time ? kind_if_graphical(props) : NULL;

	if (kind) {
		struct seen *v = g_new0(struct seen, 1);

		v->order = a->order;
		v->name = g_steal_pointer(&a->name);
		v->id = g_steal_pointer(&a->id);
		v->seat = g_steal_pointer(&a->seat);
		v->kind = kind;
		g_ptr_array_add(q->seen, v);
	}
	g_free(a->name);
	g_free(a->id);
	g_free(a->seat);
	g_free(a);
	if (--q->pending == 0)
		sweep_done(q);
}

static void on_list(GObject *src, GAsyncResult *res, gpointer data)
{
	struct ask *a = data;
	struct sweep *q = a->q;
	sentinel *s = q->s;
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) response =
		g_dbus_connection_call_finish(G_DBUS_CONNECTION(src), res, &mistake);
	g_autoptr(GVariantIter) listing = NULL;
	const char *id, *name, *seat, *fpath;
	guint32 uid;
	unsigned order = 0;

	bool in_time = note_reply(q, 0, a->serial, a->sent_ms);

	g_free(a);
	if (q->closing) {
		q->cancelled = true;
	} else if (!response || !in_time) {
		q->failed = true;
	} else {
		g_variant_get(response, "(a(susso))", &listing);
		while (g_variant_iter_next(listing, "(&su&s&s&o)", &id, &uid, &name,
		                           &seat, &fpath)) {
			struct ask *g;

			order++;
			/* ⭐ The same two filters as the attach: a seat, and a name asked. */
			if (!seat || !*seat || !g_strv_contains((const char *const *)q->users, name))
				continue;
			g = g_new0(struct ask, 1);
			g->q = q;
			g->order = order;
			g->name = g_strdup(name);
			g->id = g_strdup(id);
			g->seat = g_strdup(seat);
			g->sent_ms = q->round_sent_ms = log_now_ms();
			q->pending++;
			g->serial = send_async(s, q, fpath, "org.freedesktop.DBus.Properties",
			                       "GetAll", g_variant_new("(s)", IFACE_SESSION),
			                       G_VARIANT_TYPE("(a{sv})"), on_getall, g);
		}
	}
	if (--q->pending == 0)
		sweep_done(q);
}

static gint seen_by_order(gconstpointer a, gconstpointer b)
{
	const struct seen *x = *(const struct seen *const *)a;
	const struct seen *y = *(const struct seen *const *)b;

	return x->order < y->order ? -1 : x->order > y->order;
}

/* ⭐ What logind has answered so far is collected — never waiting — and a
 *    round that has been out longer than WAIT_MS is cut (a cut call answers
 *    at once, with «cancelled», and counts as no answer). */
void sentinel_collect(sentinel *s)
{
	if (!s || !s->ctx)
		return;
	while (g_main_context_iteration(s->ctx, FALSE))
		;
	if (s->inflight && log_now_ms() - s->inflight->round_sent_ms > WAIT_MS) {
		g_cancellable_cancel(s->inflight->cancel);
		while (g_main_context_iteration(s->ctx, FALSE))
			;
	}
}

static void ask_later(sentinel *s, const char *const *users, size_t amount)
{
	struct sweep *q = g_new0(struct sweep, 1);
	struct ask *a = g_new0(struct ask, 1);

	q->s = s;
	q->started_ms = log_now_ms();
	q->users = g_new0(char *, amount + 1);
	for (size_t k = 0; k < amount; k++)
		q->users[k] = g_strdup(users[k] ? users[k] : "");
	q->seen = g_ptr_array_new_with_free_func(seen_free);
	q->cancel = g_cancellable_new();
	q->pending = 1;
	a->q = q;
	a->sent_ms = q->round_sent_ms = q->started_ms;
	s->inflight = q;
	a->serial = send_async(s, q, LOGIND_PATH, IFACE_MANAGER, "ListSessions", NULL,
	                       G_VARIANT_TYPE("(a(susso))"), on_list, a);
}

/*
 * ⭐⭐⭐ THE CHECK — `sentinel.h` carries the why in full (finding P4, §6.13:
 *       `N × D` becoming `D`), and the box above `sweep_done()` the why of
 *       not waiting (15 Oct 2026).
 */
size_t sentinel_locals(sentinel *s, const char *const *users, size_t amount,
                         bool *local, char *which_ones, size_t width)
{
	struct sweep *q;
	size_t found = 0;

	clear_answers(amount, local, which_ones, width);
	if (!s || !s->bus || !users || !amount)
		return 0;

	sentinel_collect(s);
	q = g_steal_pointer(&s->answer);
	if (q && log_now_ms() - q->started_ms <= ANSWER_MAX_AGE_MS) {
		/* ⭐ The first session in the list wins, as when it was read in
		 *    order: the answers may come back in any order. */
		g_ptr_array_sort(q->seen, seen_by_order);
		for (guint i = 0; i < q->seen->len; i++) {
			struct seen *v = g_ptr_array_index(q->seen, i);

			/* ⚠ Only for the names THIS question asked: a name that was not
			 *   asked has no answer, and «no answer» is `false` (I1). */
			if (!g_strv_contains((const char *const *)q->users, v->name))
				continue;
			found += mark(v->name, v->id, v->kind, v->seat, users, amount,
			              local, which_ones, width);
		}
	}
	sweep_free(q);
	/* ⚠ One question in flight at a time: with a 300 ms ceiling and a check
	 *   every 2 s the previous one has always come back — this is only the
	 *   belt for a loop that calls twice in a row. */
	if (!s->inflight)
		ask_later(s, users, amount);
	return found;
}

bool sentinel_local(sentinel *s, const char *user, char *description,
                       size_t how_much)
{
	bool local = false;
	const char *uno = user;

	if (description && how_much)
		description[0] = '\0';
	if (!user || !user[0] || !s || !s->bus)
		return false;
	/* ⛔ The ATTACH waits for its answer (`rcp.c` needs the verdict now),
	 *    with ATTACH_WAIT_MS and the pause after a silence.
	 *    ⚠ `which_ones` may be NULL, and then `width` is not looked at. */
	ask_now(s, &uno, 1, &local, description, description ? how_much : 0);
	return local;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ THE CHILD'S TWO CHECKS — `DECISIONS.md` §4.3-bis and §4.7.
 *
 * ⛔ THE CHILD DOES THEM AND NOT THE SERVER, and it is not a detail of where the
 *    code sits: `[M]` 15 August 2026, with the polkit rule in force, `CanPowerOff`
 *    answers **«no» to `nicfio`** and **«yes» to root** — because logind looks at
 *    `CAP_SYS_BOOT` BEFORE asking polkit.  ⇒ The server, which is root, would
 *    always be answered yes, and would write «verified» having
 *    looked at the wrong thing.  A check made from the wrong place is
 *    worse than a missing check.
 */
static const char *ACTIONS[] = { "CanPowerOff", "CanReboot", "CanSuspend", "CanHibernate", NULL };

bool sentinel_shutdown_forbidden(sentinel *s, char *detail, size_t how_much)
{
	bool all_no = true;

	if (detail && how_much)
		detail[0] = '\0';
	if (!s || !s->bus)
		return false;

	for (int i = 0; ACTIONS[i]; i++) {
		g_autoptr(GVariant) response =
			call(s, LOGIND_PATH, IFACE_MANAGER, ACTIONS[i], NULL,
		               G_VARIANT_TYPE("(s)"), WAIT_MS);
		const char *outcome = NULL;
		char piece[64];

		if (!response) {
			all_no = false;
			outcome = "(no answer)";
		} else {
			g_variant_get(response, "(&s)", &outcome);
			/* ⛔ «challenge» is NOT enough: it means «yes, asking for a
			 *    password», and on GNOME it **shows the menu entry**
			 *    instead of removing it. */
			if (g_strcmp0(outcome, "no") != 0)
				all_no = false;
		}
		g_snprintf(piece, sizeof piece, "%s=%s ", ACTIONS[i], outcome ? outcome : "?");
		if (detail && how_much)
			g_strlcat(detail, piece, how_much);
	}
	return all_no;
}

bool sentinel_without_seat(sentinel *s, char *which, size_t how_much)
{
	g_autoptr(GVariant) response = NULL;
	g_autofree char *fpath = NULL;
	g_autoptr(GVariant) property = NULL;
	g_autoptr(GVariant) value = NULL;
	const char *seat = NULL;

	if (which && how_much)
		which[0] = '\0';
	if (!s || !s->bus)
		return false;

	response = call(s, LOGIND_PATH, IFACE_MANAGER, "GetSessionByPID",
	                  g_variant_new("(u)", (guint32)getpid()), G_VARIANT_TYPE("(o)"),
	                  WAIT_MS);
	if (!response) {
		/* ⛔ NO SESSION is worse than «with a seat»: without a session the
		 *    compositor does not start at all (`DECISIONS.md` §1.10-ter). */
		if (which && how_much)
			g_strlcpy(which, "no logind session", how_much);
		return false;
	}
	g_variant_get(response, "(o)", &fpath);

	property = call(s, fpath, "org.freedesktop.DBus.Properties", "Get",
	                   g_variant_new("(ss)", IFACE_SESSION, "Seat"), G_VARIANT_TYPE("(v)"),
	                   WAIT_MS);
	if (!property)
		return false;
	g_variant_get(property, "(v)", &value);
	/* The `Seat` property is a `(so)` structure: id and path. */
	if (g_variant_is_of_type(value, G_VARIANT_TYPE("(so)")))
		g_variant_get(value, "(&so)", &seat, NULL);
	else if (g_variant_is_of_type(value, G_VARIANT_TYPE_STRING))
		seat = g_variant_get_string(value, NULL);

	if (which && how_much)
		g_snprintf(which, how_much, "session %s, seat «%s»", fpath,
		           seat && *seat ? seat : "(none)");
	return !seat || !*seat;
}

void sentinel_counts(const sentinel *s, uint64_t *calls,
                      uint64_t *worst_ms)
{
	if (calls)
		*calls = s ? s->calls : 0;
	if (worst_ms)
		*worst_ms = s ? s->worst_ms : 0;
}
