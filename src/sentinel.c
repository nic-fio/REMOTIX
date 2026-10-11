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
 * This call leaves from the same `poll` loop that delivers the frames.  On
 * a healthy machine logind answers in less than a millisecond — ⚠ and if one
 * day it did not, the user would pay the delay in smoothness, not
 * this module in correctness.  ⇒ The answer is given up instead of making
 * everyone wait, and `sentinel_counts()` keeps the number so that the choice can
 * be RE-MEASURED instead of believed (`CODER.md` §6).
 */
#define WAIT_MS 300

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

struct sentinel {
	GDBusConnection *bus;
	uint64_t calls;
	uint64_t worst_ms;
	/* ⛔ A single line when logind stops answering, not one per turn:
	 * a re-check every two seconds would fill the log with a fact that
	 * counts once (`LESSONS.md` §6.2-ter: the number that explains everything is
	 * searched for, and in a flooded log it is not found). */
	bool mute_already_logged;
};

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
	registro_dice(LOG_SESSION,
	              "local session guardian ready (system bus); the "
	              "discriminant is the SEAT, not «Remote»");
	return s;
}

void sentinel_close(sentinel *s)
{
	if (!s)
		return;
	g_clear_object(&s->bus);
	g_free(s);
}

static GVariant *call(sentinel *s, const char *fpath,
                        const char *interfaccia, const char *method,
                        GVariant *call_args, const GVariantType *kind)
{
	return g_dbus_connection_call_sync(s->bus, LOGIND_NAME, fpath, interfaccia,
	                                   method, call_args, kind,
	                                   G_DBUS_CALL_FLAGS_NONE, WAIT_MS, NULL,
	                                   NULL);
}

/*
 * The type of the session, if it is graphical, of user class, not remote and not
 * closing.  NULL if it is not — or if it vanished between the list and this question,
 * which is logind's normal race condition and not a fault.
 */
static char *type_if_graphical(sentinel *s, const char *fpath)
{
	g_autoptr(GVariant) response =
		call(s, fpath, "org.freedesktop.DBus.Properties", "GetAll",
	               g_variant_new("(s)", IFACE_SESSION), G_VARIANT_TYPE("(a{sv})"));
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
	/* ⚠ The second belt, and today it cuts nothing: until `PAM_RHOST` is
	 *   set, our sessions show `Remote=no` like the local ones.
	 *   ⇒ The SEAT does the work, and this line will become true later. */
	if (v_remote && g_variant_get_boolean(v_remote))
		return NULL;
	/* `closing` is the session that is going away: counting it would lock out
	 * whoever reconnects right while the local one ends. */
	if (v_state && g_strcmp0(g_variant_get_string(v_state, NULL), "closing") == 0)
		return NULL;

	return g_strdup(kind);
}

/*
 * ⭐⭐⭐ THE HEART, AND THERE IS ONLY ONE — `sentinel.h` carries the why in
 *       full (finding P4, §6.13: `N × D` becoming `D`).
 *
 * ⛔ `sentinel_local()` below is this same function with `amount = 1`,
 *    and not a second draft: two drafts of the same question are two
 *    truths that the day they diverge do not give red, they give a different
 *    answer depending on who asks (`CODER.md` §2-bis, «one road only»).
 */
size_t sentinel_locals(sentinel *s, const char *const *users, size_t amount,
                         bool *local, char *which_ones, size_t width)
{
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariantIter) listing = NULL;
	const char *id, *name, *seat, *fpath;
	guint32 uid;
	uint64_t start;
	uint64_t cost;
	size_t found = 0;
	size_t remain;

	/* ⛔ It is ALWAYS cleared, and first: a vector left as it was would tell the
	 *    caller the answer of the previous re-check, which is the worst lie —
	 *    indistinguishable from a fresh answer. */
	for (size_t k = 0; k < amount; k++) {
		local[k] = false;
		if (which_ones && width)
			which_ones[k * width] = '\0';
	}
	if (!s || !s->bus || !users || !amount)
		return 0;
	remain = amount;

	start = log_now_ms();
	response = call(s, LOGIND_PATH, IFACE_MANAGER, "ListSessions", NULL,
	                  G_VARIANT_TYPE("(a(susso))"));
	if (!response) {
		/* ⛔ Carry on WITHOUT the rule instead of locking everyone out: I1.
		 * ⚠ And say it once only, not at every re-check. */
		if (!s->mute_already_logged) {
			registro_dice(LOG_SESSION,
			              "⛔ logind did not answer within %d ms: the rule "
			              "of §5.1 is not applied while it is silent (and this "
			              "line is not repeated)",
			              WAIT_MS);
			s->mute_already_logged = true;
		}
		return 0;
	}
	if (s->mute_already_logged) {
		registro_dice(LOG_SESSION, "logind is answering again");
		s->mute_already_logged = false;
	}

	g_variant_get(response, "(a(susso))", &listing);
	/* ⭐ Exit as soon as ALL have an answer (`remain == 0`), not as soon as one
	 *    has it: the question is now for N tenants, and stopping at the first
	 *    would leave the others with a `false` that looks like an answer. */
	while (remain &&
	       g_variant_iter_next(listing, "(&su&s&s&o)", &id, &uid, &name, &seat,
	                           &fpath)) {
		g_autofree char *kind = NULL;
		bool needs = false;

		/* ⭐ The two conditions that discard almost everything are ALREADY in the list,
		 *    and apply without opening anything: the wrong user, and — ⛔ the
		 *    line that carries all the weight — **the empty seat**, which is what
		 *    makes a session local and which ours do not have.
		 * ⛔ And the comparison is against ALL the names asked, in memory: it is the
		 *    loop that replaced the N calls to logind. */
		if (!seat || !*seat)
			continue;
		for (size_t k = 0; k < amount; k++)
			if (!local[k] && g_strcmp0(name, users[k]) == 0)
				needs = true;
		if (!needs)
			continue;

		/* ⚠ It is the only call left inside the loop, and it does not grow with the
		 *   tenants: it is made only for a session that ALREADY has a seat and a name
		 *   we care about — that is for the real local session, which is what
		 *   we are looking for.  On a headless machine it never happens. */
		kind = type_if_graphical(s, fpath);
		if (!kind)
			continue;

		for (size_t k = 0; k < amount; k++) {
			if (local[k] || g_strcmp0(name, users[k]) != 0)
				continue;
			local[k] = true;
			found++;
			remain--;
			if (which_ones && width)
				g_snprintf(which_ones + k * width, width,
				           "session %s, %s on %s", id, kind, seat);
		}
	}

	cost = log_now_ms() - start;
	s->calls++;
	if (cost > s->worst_ms)
		s->worst_ms = cost;
	if (cost >= SLOW_MS)
		registro_dice(LOG_SESSION,
		              "⚠ logind took %llu ms for the list of "
		              "sessions (%zu tenants in a single question): if it "
		              "repeats, this question must move to a helper "
		              "process like PAM",
		              (unsigned long long) cost, amount);

	return found;
}

bool sentinel_local(sentinel *s, const char *user, char *description,
                       size_t how_much)
{
	bool local = false;
	const char *uno = user;

	if (description && how_much)
		description[0] = '\0';
	if (!user || !user[0])
		return false;
	/* ⛔ One road only: the question for one is the question for all with N = 1.
	 *    ⚠ `which_ones` may be NULL, and then `width` is not looked at. */
	sentinel_locals(s, &uno, 1, &local, description, description ? how_much : 0);
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
		               G_VARIANT_TYPE("(s)"));
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
	                  g_variant_new("(u)", (guint32)getpid()), G_VARIANT_TYPE("(o)"));
	if (!response) {
		/* ⛔ NO SESSION is worse than «with a seat»: without a session the
		 *    compositor does not start at all (`DECISIONS.md` §1.10-ter). */
		if (which && how_much)
			g_strlcpy(which, "no logind session", how_much);
		return false;
	}
	g_variant_get(response, "(o)", &fpath);

	property = call(s, fpath, "org.freedesktop.DBus.Properties", "Get",
	                   g_variant_new("(ss)", IFACE_SESSION, "Seat"), G_VARIANT_TYPE("(v)"));
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
