/*
 * session.c — the headless GNOME session is born, and is born WITH a monitor.
 *
 * The why of every choice is in `session.h`, which is read first: here are
 * the reasons that concern the LINE, not the module.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT WAS BROUGHT OVER FROM v1, AND WHAT WAS LEFT THERE
 *
 * Brought over (`fondamenta/remotix-c/src/sessione.c`, 797 real lines):
 *   · `sess_bus()`            — our own connection, without «exit-on-close»
 *   · `compose_environment()`        — the environment from scratch, GNOME branch (408-540)
 *   · `local_utf8()`             — the local that must EXIST, not just be named
 *   · the shape of `write_dropin()` (569-623) — `user.control` folder, file,
 *     `daemon-reload`, and the rule «the drop-in BEFORE the command»
 *   · `start()` with `setsid --fork` and the session log
 *   · `exit_gnome()` with `Logout(2)` (699-711)
 *
 * Left there, because it is apparatus that does not exist in V2 or is not needed for GNOME:
 *   · the whole KWin branch: `nome_occupato()`, `esci_kde_ordinato()`,
 *     `esci_kde_a_forza()`, `SESSION_COMMAND_KDE`, `TipoCompositore` and
 *     `compositore.h` (in V2 that file does not exist, and creating it would be apparatus for
 *     a compositor this phase does not needs);
 *   · `write_cursor_theme()` + `scrivi_cursore_vuoto()` + `cartella_cursori()`
 *     — 120 lines of hand-written Xcursor format: it is the cure for KWin's double
 *     pointer, and on GNOME it **is not needed** (`STUDIES.md` §gnome §5.2: there the cursor is not
 *     inside the captured image);
 *   · `scrivi_regole_menu()` + `cartella_regole()` — KDE's KIOSK.  On GNOME
 *     the equivalent is the **dconf lockdown** (`STUDIES.md` §gnome §5.1), which is a
 *     job of its own and not of this link;
 *   · `ksmserverrc`, `XDG_MENU_PREFIX`, `XCURSOR_*`, `XDG_CONFIG_DIRS` — all
 *     Plasma levers;
 *   · the `command` parameter of `session_ensure()`: nobody ever passed it
 *     anything other than the default, and it was a lever that multiplied the
 *     scenes without anyone using it.
 *
 * ⚠ And one thing brought over from a BENCH and not from the product: waiting for `inactive`
 *   instead of «other than active» (`benches/02-session-launch.sh`,
 *   `stop_and_wait`).  v1 only waited for the process to disappear, and here
 *   more is needed because right afterwards the session is made to BE BORN AGAIN: restarting
 *   during `deactivating` is another first run.
 */
#include "session.h"

#include "shape.h"
#include "card_pick.h"
#include "render_node.h"
#include "log.h"

#include <errno.h>
#include <fcntl.h>
#include <locale.h>
#include <signal.h>
#include <pwd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
/* ⚠ `g_stat`, `g_open`, `g_close`: GLib's family, not POSIX's —
 *   it is the one `card_node()` and `my_processes()` use. */
#include <glib/gstdio.h>
/* ⭐ PHASE 17 — `gbm` for the buffer test (`card_can_draw()`): it is already
 *   in the binary for `wlroots.c` (`src/Makefile`, the `gbm` box). */
#include <gbm.h>

/* On this machine, without acceleration, the session takes about ten
 * seconds: the margin is for slower machines. */
#define WAIT_STARTUP_MS 40000
#define CHECK_INTERVAL_MS 500
#define WAIT_RESPONSE_MS 5000
/* ⚠ The bus is only asked whether a name has an owner: the bus itself answers, and
 *   if it takes more than half a second the problem is not the graphical session. */
#define WAIT_NAME_MS 500

/*
 * ⛔⭐⭐ THE POLL CEILING, and this number is the cure for the «many seconds»
 *       the user saw — the real one, after two wrong diagnoses.
 *
 * ⛔ `GetCurrentState` is not needed here for the ANSWER: it is needed to know **whether the
 *    compositor answers**.  And the comment of `session_alive()` explains why
 *    it must be a real call and not `NameHasOwner`: `org.gnome.Shell`
 *    takes the name **before** `meta_context_start()`, so the name is there
 *    when the Shell is not yet good for anything.
 *
 * ⛔⛔ BUT WITH `WAIT_RESPONSE_MS` (5 s) THAT POLL BECOMES A WAIT.  The
 *     name has an owner, the call leaves, and the Shell that is still
 *     being born does not answer: we stay there a good five seconds.  `[M]` 16
 *     August 2026, round 4 of twelve: between «THE SESSION BUS IS MINE» and
 *     the next line **seventeen seconds** pass, and in between the log does not
 *     have **a single line** — three five-second polls in a row.
 *
 * ⇒ ⚠ And in those seventeen seconds the child does not retry, does not answer the
 *   parent and does not deliver a frame.  It is **the same defect** that the
 *   box below declares cured: the cure covered the case «the name is not
 *   there», not the case «the name is there and whoever holds it does not answer yet».
 *
 * ⭐ A live compositor answers `GetCurrentState` in a millisecond.  If
 *    it does not answer within 400 ms **it is not ready**, and that is already the answer
 *    we need: back to the loop, say «ATTENDI» to the parent, and retry
 *    in 200 ms (`STAGE_BIRTH_RETRY_MS` in `child.c`).
 *
 * ⚠ And the two numbers work TOGETHER: without this ceiling the loop never comes
 *   back, and the dense retry cannot fire — `[M]` indeed it did not
 *   fire even once in twenty-two rounds.  Without the dense retry
 *   this ceiling would discover readiness up to a second later.
 */
#define WAIT_POLL_MS 400
#define WAIT_EXIT_MS 10000

/*
 * ⚠ THE GRACE — how long the MONITOR is waited for after the compositor answers.
 *
 * `[R]` The virtual monitor requested with `--virtual-monitor` is created by
 * `meta-context-main.c:592-597` when the context starts, that is **before**
 * `DisplayConfig` answers anyone: if `GetCurrentState` answers and says
 * zero monitors, the monitor will never arrive.  ⇒ This wait is prudence
 * on top of a fact that would already suffice, and it serves one thing only: that a slow
 * machine does not get a «NERA» it does not deserve.
 *
 * ⛔ And the direction in which it errs is declared: too short would say «black» to a
 *    healthy session (false red, seen at once); too long would just make us
 *    wait.  We err on the side that shows.
 */
#define GRACE_MONITOR_MS 5000

/*
 * The shape of the `GetCurrentState` answer, which is READ here.
 *
 *   (u serial,
 *    a((ssss) a(siiddada{sv}) a{sv})   monitors: (connector, vendor,
 *                                                product, serial), modes, props
 *    a(iiduba(ssss)a{sv})              logical monitors
 *    a{sv})                            properties
 *
 * and each mode is (id, width, height, refresh, preferred scale, supported
 * scales, properties), with the mode IN USE carrying `is-current`.
 *
 * ⛔ And it is NOT declared at the call: it is asked without a type and CHECKED afterwards.
 *    Declaring it would mean that, the day Mutter adds a field,
 *    the answer becomes a D-Bus error indistinguishable from «the bus does not
 *    answer» — that is a live session taken for dead, which is exactly the
 *    defect `session.h` tells about.  This way instead it is told apart: a shape I
 *    cannot read ⇒ **5, could not read**, and never «zero monitors».
 */
#define TYPE_STATE "(ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv})"

const char *session_mark(SessionState state)
{
	switch (state) {
	case SESSION_HEALTHY:
		return "HEALTHY";
	case SESSION_BLACK:
		return "BLACK: ZERO MONITORS";
	case SESSION_WRONG_SIZE:
		return "WRONG SIZE";
	case SESSION_SELF_CHOSEN:
		return "MONITOR CHOSEN BY ITSELF";
	case SESSION_DEAD:
		return "SESSION DEAD";
	case SESSION_NOT_READ:
		return "UNKNOWN READING";
	}
	return "UNKNOWN STATE";
}

/* ------------------------------------------------------------------------- */
static GMutex bus_lock;
static GDBusConnection *session_dbus;

GDBusConnection *sess_bus(GError **mistake)
{
	GDBusConnection *our = NULL;

	g_mutex_lock(&bus_lock);

	/* The user's bus dies at logout and is reborn right after, on the same
	 * socket but as a new daemon.  The old connection stays there, closed:
	 * whoever kept using it would not get a clear error, they would get
	 * silence — no session, no Mutter, black screen at the second
	 * login.  So it is thrown away and another one is opened. */
	if (session_dbus && g_dbus_connection_is_closed(session_dbus)) {
		registro_dice(LOG_SESSION, "the session bus has closed: opening another one");
		g_clear_object(&session_dbus);
	}

	if (!session_dbus) {
		g_autofree char *address =
			g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, mistake);

		/*
		 * OUR connection, not the shared one of `g_bus_get_sync`: the
		 * shared one is a single object for the whole process, which GIO keeps in
		 * cache and on which it switches «exit-on-close» on.  Opening it ourselves, the switch
		 * is born off (see the box in `session.h`).
		 */
		if (address)
			session_dbus = g_dbus_connection_new_for_address_sync(
				address,
				G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
					G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
				NULL, NULL, mistake);
		if (session_dbus)
			g_dbus_connection_set_exit_on_close(session_dbus, FALSE);
	}

	if (session_dbus)
		our = g_object_ref(session_dbus);
	g_mutex_unlock(&bus_lock);
	return our;
}

/*
 * ⛔⭐⭐ ONE DOES NOT ASK A QUESTION OF SOMEONE WHO IS NOT THERE — 16 August 2026, and this line
 *      closes the defect that made the user try five times.
 *
 * `[M]` The child, while the graphical session was BEING BORN, stayed **thirty seconds**
 * inside a synchronous call to `GetCurrentState`, and ended with
 * *«NoReply: Message recipient disconnected»*.  ⛔ In those thirty seconds it did not
 * retry, did not answer the parent and did not deliver a frame: the client
 * got tired and left.  ⇒ The symptom for the user was «the desktop does not
 * appear» or «everything broke», one time in three.
 *
 * ⚠ And shortening the wait is NOT enough: a second inside a useless call is
 *   still a second in which this process does not do its job.  ⭐ The right
 *   question is another one, and it costs nothing: **does that name have an owner?**
 *   `NameHasOwner` ALWAYS answers at once, because the bus answers and not a
 *   service that is being born.
 *
 * ⇒ If the owner is not there, the answer is «the session is not there» — which is
 *   exactly what the caller wanted to know, obtained in a millisecond
 *   instead of thirty seconds.
 */
static gboolean name_has_owner(GDBusConnection *bus, const char *name)
{
	g_autoptr(GVariant) response = NULL;
	gboolean c_e = FALSE;

	if (!bus || !name)
		return FALSE;
	response = g_dbus_connection_call_sync(
		bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
		"NameHasOwner", g_variant_new("(s)", name), G_VARIANT_TYPE("(b)"),
		G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_NAME_MS, NULL, NULL);
	if (!response)
		return FALSE;
	g_variant_get(response, "(b)", &c_e);
	return c_e;
}

/* A call to Mutter, without declaring the type of the answer. */
static GVariant *ask_mutter(GDBusConnection *bus, const char *name, const char *object,
                                 const char *interfaccia, const char *method, GError **mistake)
{
	if (!name_has_owner(bus, name)) {
		/* ⛔⭐ AND THE ERROR IS `NAME_HAS_NO_OWNER`, not just any: the
		 *     distinction between «not there» (4) and «could not look» (5) already exists
		 *     in `session_state()`, and it is recognised PRECISELY by this code.
		 *     ⚠ The first draft used `G_IO_ERROR_NOT_FOUND`, which does not match:
		 *     ⛔ and then every session came out «UNKNOWN READING», the child did not
		 *     make it be born — «states other than dead are not touched» — and
		 *     `[M]` four bench rounds out of four were red.  A right error
		 *     with the wrong name is a wrong error. */
		g_set_error(mistake, G_DBUS_ERROR, G_DBUS_ERROR_NAME_HAS_NO_OWNER,
		            "«%s» has no owner on the bus: the graphical session is not there "
		            "(or is still being born).  ⛔ One does not ASK someone who is not there: the "
		            "call would stay queued up to the ceiling, and this process "
		            "would stop answering for all that time",
		            name);
		return NULL;
	}
	/* ⛔ `WAIT_POLL_MS`, not `WAIT_RESPONSE_MS`: here we POLL, and a
	 *    poll that waits five seconds is not a poll, it is a wait
	 *    — see the box on the constant. */
	return g_dbus_connection_call_sync(bus, name, object, interfaccia, method, NULL, NULL,
	                                   G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_POLL_MS,
	                                   NULL, mistake);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐ PHASE 12 — WHICH DESKTOP.  The criterion and the why are in `session.h`.
 *
 * ⚠ The process PATH is looked at: the child has it fixed
 *   (`/usr/local/bin:/usr/bin:/bin`), so parent and child give the same
 *   answer without having to pass it along.
 */
static DesktopSession chosen_desktop;
static const char *desktop_description;

static void recognize_desktop(void)
{
	static gsize completed;

	if (g_once_init_enter(&completed)) {
		g_autofree char *gnome = g_find_program_in_path("gnome-session");
		g_autofree char *plasma = g_find_program_in_path("startplasma-wayland");
		g_autofree char *xfce = g_find_program_in_path("xfce4-session");
		g_autofree char *labwc = g_find_program_in_path(SESSION_PROCESS_XFCE);
		/* ⭐ PHASE 14 — always looked up, but it decides only AFTER XFCE: see the branch. */
		g_autofree char *lxqt = g_find_program_in_path(SESSION_MARKER_LXQT);

		if (plasma && !gnome) {
			chosen_desktop = SESSION_DESKTOP_KDE;
			desktop_description = "KDE Plasma (startplasma-wayland is there, gnome-session is "
			                   "not)";
		} else if (plasma && gnome) {
			chosen_desktop = SESSION_DESKTOP_GNOME;
			desktop_description = "GNOME — ⚠ AMBIGUOUS: this machine has both GNOME and "
			                   "KDE, and GNOME wins.  Choosing among several desktops is not available "
			                   "yet (DECISIONS.md §4.6-duodetricies, MASTERPLAN.md M5)";
		} else if (gnome) {
			chosen_desktop = SESSION_DESKTOP_GNOME;
			desktop_description = "GNOME (gnome-session is there)";
		} else if (xfce) {
			/* ⭐ PHASE 13.  The marker is `xfce4-session`, not `labwc`: see
			 *    `session.h`.  `labwc` is a PRECONDITION, and its absence
			 *    is said at once instead of letting a failed `exec` discover it. */
			chosen_desktop = SESSION_DESKTOP_XFCE;
			desktop_description =
				labwc ? "XFCE (xfce4-session is there, and labwc to run it)"
				      : "XFCE (xfce4-session is there) — ⛔ but labwc is NOT, and XFCE "
				        "on Wayland does not bring a compositor of its own: the session cannot "
				        "be born until it is installed";
			/* ⭐ PHASE 14 — XFCE and LXQt together: AMBIGUOUS, like GNOME+KDE.  XFCE
			 *    is chosen, that is what the machine did yesterday, and it is SAID:
			 *    the choice changes only the explanation, never the desktop. */
			if (lxqt)
				desktop_description =
					"XFCE — ⚠ AMBIGUOUS: this machine has both XFCE and LXQt "
					"(xfce4-session and lxqt-session), and XFCE wins.  Choosing among "
					"several desktops is not available yet (DECISIONS.md "
					"§4.6-duodetricies, MASTERPLAN.md M5)";
		} else if (lxqt) {
			/* ⭐ PHASE 14.  Same discipline as XFCE: the marker is the
			 *    SESSION, `labwc` the precondition, said at once. */
			chosen_desktop = SESSION_DESKTOP_LXQT;
			desktop_description =
				labwc ? "LXQt (lxqt-session is there, and labwc to run it)"
				      : "LXQt (lxqt-session is there) — ⛔ but labwc is NOT, and LXQt "
				        "on Wayland does not bring a compositor of its own: the session cannot "
				        "be born until it is installed";
		} else {
			/*
			 * ⛔⛔ HERE WAS THE FALLBACK TO GNOME, and it was REMOVED — phase 13,
			 *     increment 1.  The full reason is in `session.h`,
			 *     on the fourth enum value; in one line: declaring oneself GNOME
			 *     on a machine that does not have GNOME got two innocents
			 *     accused — someone else's drop-in and Mutter — while the real cause
			 *     was written only once, where nobody read it.
			 * ⚠ It is a change of behaviour, and it is intended: on a
			 *   machine without a desktop we used to try and fail badly,
			 *   now we do not try and we say why.
			 */
			chosen_desktop = SESSION_DESKTOP_NONE;
			desktop_description = "⛔ NO DESKTOP RECOGNISED — I cannot find "
			                   "gnome-session, nor startplasma-wayland, nor "
			                   "xfce4-session, nor lxqt-session: no graphical "
			                   "session can "
			                   "be born, and I am not trying any";
		}
		g_once_init_leave(&completed, 1);
	}
}

DesktopSession desktop_session(void)
{
	recognize_desktop();
	return chosen_desktop;
}

const char *session_desktop_explain(void)
{
	recognize_desktop();
	return desktop_description;
}

static gboolean e_kde(void)
{
	return desktop_session() == SESSION_DESKTOP_KDE;
}

/*
 * ⛔⛔ WHY THREE PREDICATES AND NOT A `!e_kde()` — phase 13.
 *
 * In this file not a single `!e_kde()` is written out: the
 * negation is always an `else` or a **fall-through to the end** — seven places, and they
 * read as «GNOME».  ⚠ Adding a third value to the enum turns them
 * ALL AT ONCE into «GNOME **or** XFCE», and the compiler says nothing.
 *
 * ⇒ So every place gains an `if (e_xfce())` **in front of** the GNOME
 *   block, which stays textually as before and returns with `goto`/`return`.
 *   Whoever adds the fourth desktop must go round the same way: the list of places
 *   is in `phases/13-xfce.md`, increment 1.
 */
/*
 * The render node to give wlroots — ⛔ SEARCHED FOR, not hardwired.
 *
 * ⚠ `renderD128` and `renderD129` swap between two boots (`provision.sh`
 *   §5), and on the real machine the second node is a card **excluded on purpose**.
 *   ⇒ ⭐ 1.5: NOT by name any more — see `card_pick.h` (the BIOS primary card, else the lowest PCI address).
 *   Opening is still
 *     right question, because it is exactly what wlroots will do.
 *
 * ⛔⛔ And this is not zeal: if opening fails, wlroots **says nothing**
 *     and falls back to pixman, that is to software.  The symptom for the user is «it is
 *     slow», and no line explains it — the same shape as the encoder that
 *     fell back to software, with the aggravation that there at least it declared it.
 *
 * Returns NULL if there is none: the caller says so in the log.
 */
static gboolean card_can_draw(const char *node, char **why); /* PHASE 17, below */

static char *card_node(card_pick_how *how, char **story)
{
	/* ⭐ 1.5 (27 Oct 2026, §11.37 addendum): the rule lives in `card_pick.c`, shared with `wlroots.c`: the BIOS primary
	 *   card if it can draw, else the capable card with the lowest PCI address (not the lowest NAME).  ⛔ The
	 *   administrator does not choose the card; `--render-node` stays the encoder's fallback only. */
	return card_pick("/dev/dri", "/sys/class/drm", card_can_draw, how, story);
}

/* ⭐ the same rule for `wlroots.c`'s fallback node (the compositor did not say its `main_device`) */
char *session_card_node(void)
{
	card_pick_how how;
	g_autofree char *story = NULL;

	return card_node(&how, &story);
}

/* ⭐ the log line of a chosen card: node, PCI address, driver (`render_node_describe()`) and WHY */
static void card_say(const char *who, const char *node, const char *story)
{
	char desc[160];

	render_node_describe(node, desc, sizeof desc);
	registro_dice(LOG_SESSION, "⭐ %s: the card I give the compositor is %s (%s) — %s", who, node, desc, story);
}

/*
 * ⭐ PHASE 17 — CAN THE CARD DRAW?  Opening the node is not enough.
 *
 * `[M]` 29 Sep 2026, openSUSE Leap 16 VM with `virtio_gpu` WITHOUT 3D: the node
 *   `renderD128` OPENS (so `card_node()` returns it), but labwc
 *   cannot create the output buffer on it — `gbm_bo_create failed`,
 *   `Failed to allocate buffer` — and draws nothing: black canvas.  With
 *   `WLR_RENDERER=pixman` the desktop arrives.
 *
 * ⇒ Before labwc, the SAME move labwc falls on is made: `gbm` on the node and
 *   an XRGB8888 buffer with the usages wlroots asks for when it creates without
 *   modifiers (`[R]` wlroots `render/allocator/gbm.c`, `create_buffer`:
 *   `GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING`), then with RENDERING only.
 *   ⛔ «No» is said only if BOTH fail: in doubt the card wins,
 *      because on machines with a real card nothing must change.
 * ⛔ No exception per distribution, desktop or driver: the machine is asked
 *    whether it can do the thing, and the answer is written.
 *
 * Returns TRUE if the buffer is born; otherwise FALSE, with the reason in `*why`.
 */
static gboolean card_can_draw(const char *node, char **why)
{
	static const uint32_t uses[] = { GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING,
		                        GBM_BO_USE_RENDERING };
	struct gbm_device *gbm;
	int fd, error = 0;

	fd = g_open(node, O_RDWR | O_CLOEXEC, 0);
	if (fd < 0) {
		*why = g_strdup_printf("%s does not open: %s", node, g_strerror(errno));
		return FALSE;
	}
	gbm = gbm_create_device(fd);
	if (!gbm) {
		*why = g_strdup_printf("gbm_create_device on %s fails", node);
		g_close(fd, NULL);
		return FALSE;
	}
	for (guint i = 0; i < G_N_ELEMENTS(uses); i++) {
		struct gbm_bo *bo;

		errno = 0;
		bo = gbm_bo_create(gbm, 256, 256, GBM_FORMAT_XRGB8888, uses[i]);
		if (bo) {
			gbm_bo_destroy(bo);
			gbm_device_destroy(gbm);
			g_close(fd, NULL);
			return TRUE;
		}
		error = errno;
	}
	*why = g_strdup_printf("gbm_bo_create on %s (gbm «%s») does not create the buffer: %s", node,
	                          gbm_device_get_backend_name(gbm),
	                          error ? g_strerror(error) : "no errno");
	gbm_device_destroy(gbm);
	g_close(fd, NULL);
	return FALSE;
}

static gboolean e_xfce(void)
{
	return desktop_session() == SESSION_DESKTOP_XFCE;
}

static gboolean is_nobody(void)
{
	return desktop_session() == SESSION_DESKTOP_NONE;
}

/*
 * ⭐ PHASE 14 — the fourth predicate, and the round of the «WHY THREE
 *    PREDICATES» box done again: every place that had an `if (e_xfce())` in front of the
 *    GNOME block now also has an EXPLICIT LXQt branch — merged with
 *    XFCE's where the fact belongs to labwc (family), separate where it belongs to the
 *    session.  ⛔ No place lets LXQt fall into the GNOME block.
 */
static gboolean e_lxqt(void)
{
	return desktop_session() == SESSION_DESKTOP_LXQT;
}

bool session_on_wlroots(void)
{
	return e_xfce() || e_lxqt();
}

/*
 * The short name of the desktop, for the log lines that used to name ONE.
 *
 * ⚠ `LESSONS.md` §1.9, fifth rule: *a line written when there was only one
 *   caller becomes false at the second, and no compiler says so*.  `[M]` 20
 *   Sep 2026, first XFCE test: the cursor theme — written for KWin and
 *   reused by labwc — announced «⭐ **Plasma**: theme remotix-invisibile» inside
 *   an XFCE session.  ⇒ The line is not duplicated: it is made to say the right name.
 */
static const char *desktop_name(void)
{
	switch (desktop_session()) {
	case SESSION_DESKTOP_KDE:
		return "Plasma";
	case SESSION_DESKTOP_XFCE:
		return "XFCE";
	case SESSION_DESKTOP_LXQT:
		return "LXQt";
	case SESSION_DESKTOP_NONE:
		return "no desktop";
	default:
		return "GNOME";
	}
}

/* ⭐ 1.5: the desktop's name for `child.c`'s service-card warning */
const char *session_desktop_name(void)
{
	return desktop_name();
}

/*
 * ⭐⭐ PHASE 17, D8 (`DECISIONS.md` §10.20) — WHICH GNOME SESSION: the distribution's
 *      DEFAULT one, not always `gnome`.
 *
 * On Ubuntu the GNOME seen in front of the monitor is the `ubuntu` session
 * (dock, colours, extensions: the Shell's `ubuntu` MODE); the `gnome` session
 * exists only with the `gnome-session` package from universe.  ⛔ No exceptions per
 * distribution: what the machine OFFERS is read, with one criterion only.
 *
 * ⭐ THE CRITERION (`[M]` 30 Sep 2026: Ubuntu 26.04, Debian 13, Fedora 44):
 *   1. the candidates are the sessions the display manager offers:
 *      `<system data>/wayland-sessions/<name>.desktop` whose `Exec` launches
 *      `gnome-session`; the name is that of `--session` (without it: `gnome`, the
 *      gnome-session default), and
 *      `<data>/gnome-session/sessions/<name>.session` must exist;
 *   2. if there is only one, it is that one (stock Ubuntu: `ubuntu`; stock Debian and
 *      Fedora: `gnome`);
 *   3. if there are several: the one bearing the distribution's name
 *      (`ID` of os-release — the distribution's session, like `ubuntu`);
 *      otherwise `gnome`; otherwise the first in alphabetical order — it is the
 *      upstream GDM rule (`get_fallback_session_name`), while Ubuntu
 *      patches it by hand («Prefer ubuntu session as fallback», gdm3 changelog):
 *      point 3 gives the same result without naming Ubuntu;
 *   4. no candidate ⇒ DECLARED FALLBACK to `gnome`, and it is said.
 * ⚠ The start line is the session's `Exec`, argument by argument
 *   (quoted): an `env GNOME_SHELL_SESSION_MODE=…` in front arrives as it is.
 *   `XDG_CURRENT_DESKTOP` comes from `DesktopNames` (Ubuntu: `ubuntu:GNOME`, and
 *   Ubuntu's default settings are written for `ubuntu`), as GDM does.
 */
typedef struct {
	char *name;     /* --session: `ubuntu`, `gnome` */
	char *id;       /* the .desktop file without extension: XDG_SESSION_DESKTOP */
	char *line;     /* "exec …", the start line */
	char *desktop;  /* XDG_CURRENT_DESKTOP, already with the colons */
	char *handler;  /* gnome-session-manager@<name>.service */
} GnomeSession;

/* The session name from the argv of an `Exec`, or NULL if it does not launch
 * gnome-session. */
static char *name_from_exec(char **argv)
{
	for (int i = 0; argv[i]; i++) {
		g_autofree char *base = g_path_get_basename(argv[i]);

		if (strcmp(base, "gnome-session") != 0)
			continue;
		for (int j = i + 1; argv[j]; j++) {
			if (g_str_has_prefix(argv[j], "--session="))
				return g_strdup(argv[j] + strlen("--session="));
			if (strcmp(argv[j], "--session") == 0 && argv[j + 1])
				return g_strdup(argv[j + 1]);
		}
		return g_strdup("gnome");
	}
	return NULL;
}

static gboolean c_e_il_file_session(const char *name)
{
	const char *const *data = g_get_system_data_dirs();
	g_autofree char *file = g_strconcat(name, ".session", NULL);

	for (int i = 0; data[i]; i++) {
		g_autofree char *p = g_build_filename(data[i], "gnome-session", "sessions", file, NULL);

		if (g_file_test(p, G_FILE_TEST_IS_REGULAR))
			return TRUE;
	}
	return FALSE;
}

/* A candidate from the .desktop file, or NULL if it is not one. */
static GnomeSession *has_candidate(const char *fpath, const char *id)
{
	g_autoptr(GKeyFile) kf = g_key_file_new();
	g_autofree char *exec = NULL;
	g_autofree char *prova = NULL;
	g_autofree char *found = NULL;
	g_auto(GStrv) argv = NULL;
	g_auto(GStrv) names = NULL;
	g_autoptr(GString) line = g_string_new("exec");
	GnomeSession *s;
	char *name;

	if (!g_key_file_load_from_file(kf, fpath, G_KEY_FILE_NONE, NULL) ||
	    g_key_file_get_boolean(kf, G_KEY_FILE_DESKTOP_GROUP, "Hidden", NULL) ||
	    !(exec = g_key_file_get_string(kf, G_KEY_FILE_DESKTOP_GROUP, "Exec", NULL)) ||
	    !g_shell_parse_argv(exec, NULL, &argv, NULL) || !(name = name_from_exec(argv)))
		return NULL;
	prova = g_key_file_get_string(kf, G_KEY_FILE_DESKTOP_GROUP, "TryExec", NULL);
	found = prova ? g_find_program_in_path(prova) : NULL;
	if ((prova && !found) || !c_e_il_file_session(name)) {
		g_free(name);
		return NULL;
	}
	for (int i = 0; argv[i]; i++) {
		g_autofree char *q = NULL;

		/* the field codes of .desktop entries (%U…) are not arguments */
		if (argv[i][0] == '%' && strlen(argv[i]) == 2)
			continue;
		q = g_shell_quote(argv[i]);
		g_string_append_printf(line, " %s", q);
	}
	names = g_key_file_get_string_list(kf, G_KEY_FILE_DESKTOP_GROUP, "DesktopNames", NULL,
	                                  NULL);
	s = g_new0(GnomeSession, 1);
	s->name = name;
	s->id = g_strdup(id);
	s->line = g_string_free(g_steal_pointer(&line), FALSE);
	s->desktop = names && names[0] ? g_strjoinv(":", names) : g_strdup("GNOME");
	s->handler = g_strdup_printf("gnome-session-manager@%s.service", name);
	return s;
}

static const GnomeSession *gnome_session(void)
{
	static gsize completed;
	static GnomeSession *choice;

	if (g_once_init_enter(&completed)) {
		const char *const *data = g_get_system_data_dirs();
		g_autoptr(GHashTable) seen_items = g_hash_table_new_full(g_str_hash, g_str_equal,
		                                                    g_free, NULL);
		g_autoptr(GPtrArray) all_items = g_ptr_array_new();
		g_autoptr(GString) listing = g_string_new(NULL);
		g_autofree char *os = g_get_os_info(G_OS_INFO_KEY_ID);
		const char *why = NULL;

		/* ⚠ The first data folder wins for equal file names, as
		 *   for every XDG entry. */
		for (int i = 0; data[i]; i++) {
			g_autofree char *folder = g_build_filename(data[i], "wayland-sessions", NULL);
			g_autoptr(GDir) d = g_dir_open(folder, 0, NULL);
			const char *f;

			while (d && (f = g_dir_read_name(d))) {
				g_autofree char *id = NULL;
				g_autofree char *p = NULL;
				GnomeSession *s;

				if (!g_str_has_suffix(f, ".desktop"))
					continue;
				id = g_strndup(f, strlen(f) - strlen(".desktop"));
				if (g_hash_table_contains(seen_items, id))
					continue;
				g_hash_table_add(seen_items, g_strdup(id));
				p = g_build_filename(folder, f, NULL);
				if ((s = has_candidate(p, id)))
					g_ptr_array_add(all_items, s);
			}
		}
		for (guint i = 0; i < all_items->len; i++) {
			GnomeSession *s = all_items->pdata[i];

			g_string_append_printf(listing, "%s%s (%s)", i ? ", " : "", s->id, s->name);
		}
		/* alphabetical on the file name, like GDM's list */
		for (guint i = 0; i + 1 < all_items->len; i++)
			for (guint j = i + 1; j < all_items->len; j++)
				if (strcmp(((GnomeSession *) all_items->pdata[j])->id,
				           ((GnomeSession *) all_items->pdata[i])->id) < 0) {
					gpointer t = all_items->pdata[i];

					all_items->pdata[i] = all_items->pdata[j];
					all_items->pdata[j] = t;
				}
		if (all_items->len == 1) {
			choice = all_items->pdata[0];
			why = "the only one the machine offers";
		}
		for (guint i = 0; !choice && os && i < all_items->len; i++)
			if (strcmp(((GnomeSession *) all_items->pdata[i])->name, os) == 0) {
				choice = all_items->pdata[i];
				why = "it bears the distribution's name (ID of os-release)";
			}
		for (guint i = 0; !choice && i < all_items->len; i++)
			if (strcmp(((GnomeSession *) all_items->pdata[i])->name,
			           SESSION_GNOME_FALLBACK) == 0) {
				choice = all_items->pdata[i];
				why = "it is «" SESSION_GNOME_FALLBACK "», the upstream GDM default";
			}
		if (!choice && all_items->len) {
			choice = all_items->pdata[0];
			why = "the first in alphabetical order, like upstream GDM";
		}
		if (!choice) {
			choice = g_new0(GnomeSession, 1);
			choice->name = g_strdup(SESSION_GNOME_FALLBACK);
			choice->id = g_strdup(SESSION_GNOME_FALLBACK);
			choice->line = g_strdup("exec gnome-session --session=" SESSION_GNOME_FALLBACK);
			choice->desktop = g_strdup("GNOME");
			choice->handler =
				g_strdup("gnome-session-manager@" SESSION_GNOME_FALLBACK ".service");
			registro_dice(LOG_SESSION,
			              "⚠ D8: no wayland-sessions/*.desktop session launches "
			              "gnome-session with an installed .session: DECLARED "
			              "FALLBACK to «%s»",
			              SESSION_GNOME_FALLBACK);
		} else
			registro_dice(LOG_SESSION,
			              "⭐ D8: the GNOME session is «%s» (%s.desktop): %s.  "
			              "Candidates: %s.  Line: %s · XDG_CURRENT_DESKTOP=%s",
			              choice->name, choice->id, why, listing->str, choice->line,
			              choice->desktop);
		/* ⚠ The discarded ones stay: a handful of strings, once per
		 *   process. */
		g_once_init_leave(&completed, 1);
	}
	return choice;
}

/*
 * How many processes of THIS user have this name.
 *
 * ⛔ It is needed because on XFCE the compositor is not a systemd unit: the question
 *    «has the previous session ended?» cannot be asked of systemd, and the answer
 *    systemd would give — `inactive` for a unit that does not exist — would be
 *    a **yes** (`[M]` 20 Sep 2026, inside `rete11-xfce`: code 4, «inactive»).
 *    ⇒ The guard would not fail: it would vanish.  Here a fact is looked at.
 * ⚠ `/proc` is read instead of calling `pgrep`: one tool fewer to have
 *   installed, and no command line to quote wrongly.
 */
static int my_processes(const char *name)
{
	g_autoptr(GDir) proc = g_dir_open("/proc", 0, NULL);
	const char *entry;
	uid_t my = getuid();
	int amount = 0;

	if (!proc)
		return -1;
	while ((entry = g_dir_read_name(proc))) {
		g_autofree char *comm = NULL;
		g_autofree char *fpath = NULL;
		GStatBuf st;

		if (!g_ascii_isdigit(entry[0]))
			continue;
		fpath = g_build_filename("/proc", entry, "comm", NULL);
		if (g_stat(fpath, &st) != 0 || st.st_uid != my)
			continue;
		if (!g_file_get_contents(fpath, &comm, NULL, NULL))
			continue;
		g_strstrip(comm);
		if (g_strcmp0(comm, name) == 0)
			amount++;
	}
	return amount;
}

bool session_alive(void)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GVariant) response = NULL;

	bus = sess_bus(NULL);
	if (!bus)
		return false;

	/* ⭐ On Plasma the weak question is KWin's name: it is not activatable (the
	 *    compositor takes it when it starts), and the weakness is the same one
	 *    declared in `session.h` — «alive» does not mean «ready». */
	if (e_kde())
		return name_has_owner(bus, "org.kde.KWin");

	/* ⭐ PHASE 13 — on XFCE the weak question is the session manager's name.
	 *    `[M]` 20 Sep 2026: it appears on the USER bus, because we start `labwc`
	 *    ourselves without `dbus-run-session` — that is exactly the bus that
	 *    `sess_bus()` already opens.  ⚠ And the weakness is the same declared for
	 *    the other two, with a wider margin: between the name and the USABLE
	 *    session there are up to 8 s per priority group, and they are structural
	 *    (`STARTUP_TIMEOUT_WAYLAND`, `STUDIES.md` §xfce §9.4). */
	if (e_xfce())
		return name_has_owner(bus, SESSION_BUS_XFCE);

	/* ⭐ PHASE 14 — on LXQt, the same weak question: the name of `lxqt-session`
	 *    on the user bus (labwc starts without `dbus-run-session`, as on XFCE).
	 * ⚠ And the weakness is declared upstream (`STUDIES.md` §lxqt §3.4): the name
	 *   appears in the CONSTRUCTOR, before the modules.  Real readiness would be
	 *   the signal `moduleStateChanged("lxqt-panel.desktop", true)`, but the child
	 *   has no GLib loop to listen to it.  [?] To be measured on the box:
	 *   how long passes between the name and the panel, and whether in between capture
	 *   on labwc fails and retries (as on XFCE) or does something else. */
	if (e_lxqt())
		return name_has_owner(bus, SESSION_BUS_LXQT);

	/*
	 * ⛔ IT IS NOT ENOUGH THAT THE NAME IS TAKEN, for two different reasons, both
	 *    paid for: Mutter's name is ACTIVATABLE and asking for it makes it be born;
	 *    and the Shell takes `org.gnome.Shell` **before
	 *    `meta_context_start()`** (`STUDIES.md` §gnome §3.2), so it is not an indicator
	 *    of readiness.  A real method is called and we check that the answer
	 *    ARRIVES — without interpreting it: only one thing matters here.
	 */
	response = ask_mutter(bus, "org.gnome.Mutter.DisplayConfig",
	                           "/org/gnome/Mutter/DisplayConfig",
	                           "org.gnome.Mutter.DisplayConfig", "GetCurrentState", NULL);
	return response != NULL;
}

/* ------------------------------------------------------------------------- */
static void copy_in(char *dove, gsize how_much, const char *what)
{
	g_strlcpy(dove, what ? what : "", how_much);
}

/*
 * From the `GetCurrentState` answer to one of the six numbers.
 *
 * ⛔ And the outcomes are THREE, not two (`REVIEWER.md` §1 point 4): «one monitor»,
 *    «zero monitors» and «could not look» — and the third will never disguise
 *    itself as the second.
 */
static SessionState read_monitor(GVariant *response, uint32_t width, uint32_t height,
                                   SessionMonitor *chosen)
{
	g_autoptr(GVariant) monitor = NULL;
	g_autoptr(GVariant) property = NULL;
	g_autoptr(GVariant) layout = NULL;
	gsize amount, i;
	SessionState verdict;

	/* ⛔ The first check is on the SHAPE, and its outcome is 5. */
	if (!g_variant_is_of_type(response, G_VARIANT_TYPE(TYPE_STATE))) {
		registro_dice(LOG_SESSION,
		              "⛔ GetCurrentState answered with a shape I cannot "
		              "read («%s» instead of «%s»): it is the PARSER that is broken, not the "
		              "session — and this is not «zero monitors» (E8)",
		              g_variant_get_type_string(response), TYPE_STATE);
		return SESSION_NOT_READ;
	}

	monitor = g_variant_get_child_value(response, 1);
	property = g_variant_get_child_value(response, 3);

	/*
	 * ⭐ THE POSITIVE CHECK — «can this reader find something that is surely
	 *    there?» (`CODER.md` §3.10).  `layout-mode` is always among the properties
	 *    of `GetCurrentState`; if I do not find it, what is broken is my
	 *    reading, and then I have no right to say «zero monitors».
	 *
	 * ⚠ We check that it IS there, not what it is worth: the type of that field is
	 *   none of our business, and tying ourselves to it would repeat the error above in small.
	 */
	layout = g_variant_lookup_value(property, "layout-mode", NULL);
	if (!layout) {
		registro_dice(LOG_SESSION,
		              "⛔ the GetCurrentState answer has no «layout-mode», "
		              "which is always there: I did not read it right, and I do not say «zero monitors»");
		return SESSION_NOT_READ;
	}

	amount = g_variant_n_children(monitor);
	if (chosen) {
		memset(chosen, 0, sizeof *chosen);
		chosen->amount = (unsigned) amount;
	}

	if (amount == 0) {
		registro_dice(LOG_SESSION,
		              "⛔ ZERO MONITORS, and the session is alive: it is the «alive, "
		              "complete and BLACK» session of STUDIES.md §gnome §3.1 — there is nothing to capture");
		return SESSION_BLACK;
	}

	/*
	 * ⛔ And if there are several, ALL are NAMED.
	 *
	 * On 12 August 2026 the bench printed «2 monitors: only one had been
	 * requested» without naming them, and the name — the only thing that told them apart, given
	 * that the size was identical — was saved only by the log line.  Here the
	 * log is the only place there is: if it does not name them, nobody
	 * names them.
	 */
	verdict = (amount == 1) ? SESSION_HEALTHY : SESSION_SELF_CHOSEN;
	if (amount > 1)
		registro_dice(LOG_SESSION,
		              "⛔ %zu monitors, and ONE had been requested: I list them all, "
		              "because in size they may be identical (E2)",
		              amount);

	for (i = 0; i < amount; i++) {
		g_autoptr(GVariant) m = g_variant_get_child_value(monitor, i);
		g_autoptr(GVariant) names = g_variant_get_child_value(m, 0);
		g_autoptr(GVariant) modes = g_variant_get_child_value(m, 1);
		const char *connector = NULL, *vendor = NULL, *product = NULL, *serial_number = NULL;
		gsize how_many_modes, k;
		gboolean mode_found = FALSE;
		gint32 ml = 0, ma = 0;
		gdouble refresh = 0;

		g_variant_get(names, "(&s&s&s&s)", &connector, &vendor, &product, &serial_number);

		how_many_modes = g_variant_n_children(modes);
		for (k = 0; k < how_many_modes; k++) {
			g_autoptr(GVariant) mode = g_variant_get_child_value(modes, k);
			g_autoptr(GVariant) mprop = g_variant_get_child_value(mode, 6);
			gboolean current = FALSE;

			if (!g_variant_lookup(mprop, "is-current", "b", &current) || !current)
				continue;
			g_variant_get_child(mode, 1, "i", &ml);
			g_variant_get_child(mode, 2, "i", &ma);
			g_variant_get_child(mode, 3, "d", &refresh);
			mode_found = TRUE;
			break;
		}

		registro_dice(LOG_SESSION,
		              "monitor %zu/%zu: connector «%s» vendor «%s» product «%s» "
		              "serial «%s» mode %s%dx%d@%.3f",
		              i + 1, amount, connector, vendor, product, serial_number,
		              mode_found ? "" : "(none in use) ", ml, ma, refresh);

		if (i == 0 && chosen) {
			copy_in(chosen->connector, sizeof chosen->connector, connector);
			copy_in(chosen->vendor, sizeof chosen->vendor, vendor);
			copy_in(chosen->product, sizeof chosen->product, product);
			copy_in(chosen->serial_number, sizeof chosen->serial_number, serial_number);
			chosen->width = (uint32_t) ml;
			chosen->height = (uint32_t) ma;
			chosen->refresh = refresh;
		}

		if (verdict != SESSION_HEALTHY)
			continue;

		/*
		 * ⛔ THE NAME BEFORE THE SIZE, and the order is the lesson of 12 August:
		 *    the two virtual monitors seen together were **both
		 *    1920x1080@60**, and whoever had looked at the resolution would have
		 *    told nothing apart.
		 */
		if (g_strcmp0(product, SESSION_REQUESTED_PRODUCT) != 0) {
			registro_dice(LOG_SESSION,
			              "⛔ the monitor is called «%s» and not «%s»: it is not the one "
			              "I asked for — someone else chose it (E2)",
			              product, SESSION_REQUESTED_PRODUCT);
			verdict = SESSION_SELF_CHOSEN;
		} else if (!mode_found) {
			registro_dice(LOG_SESSION,
			              "⛔ «%s» has no mode IN USE: there is a monitor and it has "
			              "no size, so it does not have the requested size",
			              connector);
			verdict = SESSION_WRONG_SIZE;
		} else if ((uint32_t) ml != width || (uint32_t) ma != height) {
			registro_dice(LOG_SESSION,
			              "⛔ the monitor is %dx%d and I had asked for one %ux%u",
			              ml, ma, width, height);
			verdict = SESSION_WRONG_SIZE;
		}
	}

	if (verdict == SESSION_HEALTHY)
		registro_dice(LOG_SESSION, "⭐ one monitor «%s» «%s», %ux%u: there is something to capture",
		              chosen ? chosen->connector : "?", SESSION_REQUESTED_PRODUCT, width,
		              height);
	return verdict;
}

SessionState session_state(uint32_t width, uint32_t height, SessionMonitor *chosen)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GError) mistake = NULL;

	if (chosen)
		memset(chosen, 0, sizeof *chosen);

	bus = sess_bus(&mistake);
	if (!bus) {
		registro_dice(LOG_SESSION,
		              "⛔ I do not even have the session bus (%s): it is not «the session "
		              "is not there», it is «I could not look»",
		              mistake ? mistake->message : "no reason given");
		return SESSION_NOT_READ;
	}

	/*
	 * ⭐ PHASE 12 — on Plasma.  KWin with the `--virtual` backend is born with
	 *    **a single output, of the size written in the drop-in** (`STUDIES.md` §kde
	 *    §5.2; `[M]` 18 Sep 2026: `Virtual-0` 1600x900, a single `wl_output`) —
	 *    and `write_dropin()` has already re-read that line IN FORCE before the
	 *    birth.  ⇒ Name present = SANA.
	 * ⚠ And what is NOT looked at is declared: I do not re-read the output from the
	 *   compositor (it needs a Wayland client, and that arrives with capture).
	 */
	if (e_kde()) {
		if (!name_has_owner(bus, "org.kde.KWin")) {
			registro_dice(LOG_SESSION,
			              "no KWin on the bus: the Plasma session is not there");
			return SESSION_DEAD;
		}
		log_detail(LOG_SESSION,
		                   "KWin is on the bus: the Plasma session is alive, with the drop-in's "
		                   "output (verified at birth, not re-read here)");
		return SESSION_HEALTHY;
	}

	/*
	 * ⭐ PHASE 13 — on XFCE, the same discipline as KDE and one more declaration.
	 *
	 * ⛔ Here the output is NOT of the requested size, and will not be at birth:
	 *    `[M]` 20 Sep 2026 it is born `HEADLESS-1 1280x720` hardwired, and the size is
	 *    given afterwards with the protocol (`zwlr_output_manager_v1`).  ⇒ «healthy» here
	 *    means «it is there», not «of the right size», and whoever reads must know it.
	 */
	if (e_xfce()) {
		if (!name_has_owner(bus, SESSION_BUS_XFCE)) {
			registro_dice(LOG_SESSION,
			              "no " SESSION_BUS_XFCE " on the bus: the XFCE session "
			              "is not there");
			return SESSION_DEAD;
		}
		log_detail(LOG_SESSION,
		                   "the XFCE session manager is on the bus: the session is "
		                   "alive — ⚠ and its output is NOT of the requested size: on "
		                   "wlroots it is born hardwired and is resized afterwards");
		return SESSION_HEALTHY;
	}

	/* ⭐ PHASE 14 — on LXQt, XFCE's discipline word for word: same
	 *    compositor, same hardwired output; only the name on the bus changes.
	 * ⚠ «Healthy» here means «lxqt-session is there», and the name precedes the modules
	 *   (see `session_alive()`).  [?] If the box shows that capture
	 *   starts too early, the right question is `listModules()` or the panel's
	 *   signal — not a timed wait. */
	if (e_lxqt()) {
		if (!name_has_owner(bus, SESSION_BUS_LXQT)) {
			registro_dice(LOG_SESSION,
			              "no " SESSION_BUS_LXQT " on the bus: the LXQt session "
			              "is not there");
			return SESSION_DEAD;
		}
		log_detail(LOG_SESSION,
		                   "lxqt-session is on the bus: the session is alive — ⚠ and its "
		                   "output is NOT of the requested size: on wlroots it is born "
		                   "hardwired and is resized afterwards");
		return SESSION_HEALTHY;
	}

	response = ask_mutter(bus, "org.gnome.Mutter.DisplayConfig",
	                           "/org/gnome/Mutter/DisplayConfig",
	                           "org.gnome.Mutter.DisplayConfig", "GetCurrentState", &mistake);
	if (!response) {
		/*
		 * ⛔ AND HERE THE TWO CASES PART, which is the whole point.
		 *
		 *   nobody serves that name        → the session is not there  (4)
		 *   any other error                → I could not look          (5)
		 *
		 * Lumping them together would mean taking for dead a session that is there
		 * but does not answer US — a denied permission, a saturated bus — and it is
		 * error form E8 at the point where it costs most.
		 */
		if (g_error_matches(mistake, G_DBUS_ERROR, G_DBUS_ERROR_SERVICE_UNKNOWN) ||
		    g_error_matches(mistake, G_DBUS_ERROR, G_DBUS_ERROR_NAME_HAS_NO_OWNER)) {
			registro_dice(LOG_SESSION, "no compositor on the bus: the session is not there");
			return SESSION_DEAD;
		}
		registro_dice(LOG_SESSION,
		              "⛔ GetCurrentState did not answer (%s): I could not look, "
		              "and this is NOT «the session is not there»",
		              mistake ? mistake->message : "no reason given");
		return SESSION_NOT_READ;
	}

	return read_monitor(response, width, height, chosen);
}

/* ------------------------------------------------------------------------- */
/*
 * A UTF-8 local, always — and it is the trap found by the user on 7 August
 * 2026 with the sentence «the terminal does not work».
 *
 * `gnome-terminal-server` refuses to start with a non-UTF-8 local
 * («Non UTF-8 local (ANSI_X3.4-1968) is not supported!», exit 8), and the user
 * finds themselves with a desktop where programs do not open, without an error
 * anywhere.
 *
 * ⛔ AND IT IS NOT ENOUGH THAT THE NAME SAYS UTF-8: THAT LOCALE MUST EXIST.  The server
 *    carries `LANG=it_IT.UTF-8`, which by name is UTF-8; on the hardware the
 *    GENERATED locales are two — `C` and `C.utf8` — and glibc silently falls back to `C`,
 *    which is not UTF-8.  The rootfs lives in RAM, so «just generate it
 *    once» is not enough: it is checked at every start, asking the LIBRARY
 *    instead of the name.
 */
static gboolean local_exists(const char *name)
{
	locale_t prova = newlocale(LC_ALL_MASK, name, (locale_t) 0);

	if (!prova)
		return FALSE;
	freelocale(prova);
	return TRUE;
}

static const char *local_utf8(void)
{
	/* Debian generates `C.utf8`; glibc also accepts the form with the dash, but not
	 * on all versions: both are tried instead of betting. */
	static const char *FALLBACKS[] = { "C.UTF-8", "C.utf8" };
	const char *language = g_getenv("LANG");
	gsize i;

	if (language && *language) {
		g_autofree char *uppercase = g_ascii_strup(language, -1);

		if (strstr(uppercase, "UTF-8") || strstr(uppercase, "UTF8")) {
			if (local_exists(language))
				return language;
			registro_dice(LOG_SESSION,
			              "⚠ the locale «%s» is UTF-8 by name but is NOT generated on "
			              "this machine: without a fallback the session's programs "
			              "would not open",
			              language);
		} else {
			registro_dice(LOG_SESSION, "⚠ the environment's locale («%s») is not UTF-8",
			              language);
		}
	}

	for (i = 0; i < G_N_ELEMENTS(FALLBACKS); i++)
		if (local_exists(FALLBACKS[i])) {
			registro_dice(LOG_SESSION,
			              "declared fallback: the session will start with the locale «%s»",
			              FALLBACKS[i]);
			return FALLBACKS[i];
		}

	/* No UTF-8 local on the machine: it is declared, because from here on the
	 * terminal will not start and nobody else will explain it. */
	registro_dice(LOG_SESSION,
	              "⛔ no UTF-8 locale on this machine: the session's terminal "
	              "will not start (generate one with «locale-gen C.UTF-8»)");
	return "C.UTF-8";
}

/*
 * ⭐⭐ PHASE 12 — THE CURE FOR THE DOUBLE POINTER: THE KDE CURSOR BECOMES
 *      TRANSPARENT.  ⛔ Brought back from v1 (`fondamenta/remotix-c/src/sessione.c`,
 *      `write_cursor_theme` + `scrivi_cursore_vuoto`), measured on 8 August
 *      2026 (`STUDIES.md` §kde) and left out of the move to v2: `[M]` 19 Sep
 *      2026, the user's test — «the pointer's tail».
 *
 * ⛔ THE FACT: with the `--virtual` backend KWin draws the cursor INSIDE
 *    the captured image, and there is no lever to stop it.  ⇒ Whoever watches sees
 *    TWO: the browser's, immediate, and the desktop's, which arrives
 *    with the video and chases — the «tail».
 * ⭐ And the cure is not stopping it: it is enough that what it draws CANNOT BE SEEN.
 *    KWin reads `XCURSOR_THEME` **only if `XCURSOR_SIZE` is there too**
 *    (`cursor.cpp:134-145`), and we compose the session's environment.
 * ⚠ THE THEME MUST REALLY LOAD: if the theme turns out empty KWin falls back to
 *   the default one (`pointer_input.cpp:1183-1196`), that is it PUTS BACK the
 *   visible cursor.  That is why all the shapes are written, not just
 *   `left_ptr`, and no `Inherits=` in the index.
 * ⚠ And the price, as it was until 24 Sep 2026: the shape CHANGE was lost
 *   (the I-beam on text, the resize arrows) — ⭐ cured below.
 */
/*
 * ⭐⭐ PHASE 14 — AND THE THEME IS NO LONGER INVISIBLE: IT IS ENCODED (24 Sep 2026,
 *      the user's decision: the real pointer shape on all four
 *      desktops).  Each shape is still a 1x1 image, but OPAQUE and of a colour
 *      of its own: the colour comes back in the metadata and says WHICH shape the application
 *      asked for.  ⛔ The theme is written by `shape.c`, which also keeps the
 *      colour ⇒ shape dictionary: the two halves must not be able to diverge.
 * ⚠ The NAME stays `remotix-invisible`: it is the one the environment below
 *   has always declared, and changing it cures nothing.
 */
#define THEME_CURSOR SHAPE_THEME

/* Returns the folder to put in `XCURSOR_PATH`, or NULL (said in the log). */
static char *write_cursor_theme(const char *runtime)
{
	if (!shape_theme_write(runtime)) {
		registro_dice(LOG_SESSION,
		              "⚠ %s: cursor theme NOT written: the compositor will fall back "
		              "to the visible theme, and whoever watches will see TWO pointers",
		              desktop_name());
		return NULL;
	}
	registro_dice(LOG_SESSION,
	              "⭐ %s: theme «%s» encoded — the compositor's cursor is one pixel, "
	              "and its real shape is drawn by whoever watches",
	              desktop_name(), THEME_CURSOR);
	return g_build_filename(runtime, "remotix", "icons", NULL);
}

/*
 * ⭐ PHASE 12 — «LOCK» AND «SWITCH USER» REMOVED FROM THE PLASMA MENU.
 *
 * ⛔ Brought back from v1 (`fondamenta/remotix-c/src/sessione.c`,
 *    `scrivi_regole_menu`), asked for by the user on 8 August 2026 and left
 *    out of the move to v2: `[M]` 19 Sep 2026, the user's test on KDE,
 *    the two entries were there.  In a session served by REMOTIX they do not work, and
 *    that is RIGHT: locking is ours (`DECISIONS.md` §4.3, and KWin starts with
 *    `--no-lockscreen`), and switching user would need a display manager that is not
 *    here.  ⛔ But an entry that does nothing is worse than a missing one.
 *
 * The lever is KIOSK (`KAuthorized`), with the names Plasma really queries:
 *   `SessionManagement::canLock()`       → `lock_screen`
 *   `SessionManagement::canSwitchUser()` → `start_new_session`
 *   `SessionsModel::canSwitchUser()`     → `switch_user`
 * ⚠ `switch_user` and `start_new_session` are both needed (the list and the
 *   button), and `[$i]` prevents the user's `kdeglobals` from putting them back.
 * ⛔ `logout` is NOT touched: it is the only door to close the session (§4.1-ter).
 * ⭐ Under `XDG_RUNTIME_DIR` and not in `~/.config`: it applies to the session we
 *    needs, disappears with it, and touches neither the user's configuration nor
 *    whoever sits in front of the machine.
 *
 * Returns the folder to put in `XDG_CONFIG_DIRS`, or NULL (said in the log).
 */
char *session_folder_kde(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, "remotix", "xdg", NULL);
}

static char *write_kde_menu_rules(const char *runtime)
{
	g_autofree char *folder = g_build_filename(runtime, "remotix", "xdg", NULL);
	g_autofree char *fpath = g_build_filename(folder, "kdeglobals", NULL);
	g_autoptr(GError) mistake = NULL;

	if (g_mkdir_with_parents(folder, 0700) != 0 ||
	    !g_file_set_contents(fpath,
	                         "[KDE Action Restrictions][$i]\n"
	                         "action/lock_screen=false\n"
	                         "action/start_new_session=false\n"
	                         "action/switch_user=false\n",
	                         -1, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⚠ Plasma: menu rules NOT written in %s (%s): «Lock» and "
		              "«Switch User» will stay in the menu",
		              folder, mistake ? mistake->message : g_strerror(errno));
		return NULL;
	}
	registro_dice(LOG_SESSION,
	              "⭐ Plasma: menu rules in %s — no «Lock», no «Switch "
	              "User» (KIOSK); «Log Out» stays",
	              fpath);

	/*
	 * ⭐ AND IN THE SAME FOLDER, THE WINDOW BORDER — 20 Sep 2026, the
	 *    user's test: «in KDE windows cannot be
	 *    resized».  `[M]` Plasma is born with `BorderSizeAuto`, which with Breeze
	 *    means side borders of a few pixels: at the monitor they are caught because
	 *    the cursor changes shape, ⛔ in a remote session they are not — the desktop's
	 *    cursor is invisible on purpose (see above), so the border does not
	 *    announce itself and does not catch.
	 * ⚠ And it is written WITHOUT `[$i]`, unlike the menu rules: it is a
	 *   STARTING POINT, not a prohibition — the user's `kwinrc` sits higher
	 *   up and wins, that is it can be changed from System Settings and it stays.
	 */
	g_autofree char *kwinrc = g_build_filename(folder, "kwinrc", NULL);

	if (g_file_set_contents(kwinrc,
	                        "[org.kde.kdecoration2]\n"
	                        "BorderSize=Normal\n"
	                        "BorderSizeAuto=false\n",
	                        -1, NULL))
		registro_dice(LOG_SESSION,
		              "⭐ Plasma: window border «Normal» as a starting point (%s): in "
		              "a remote session the border must be CAUGHT, and Breeze's automatic one "
		              "is too thin.  ⚠ The user can change it",
		              kwinrc);
	else
		registro_dice(LOG_SESSION,
		              "⚠ Plasma: window border not written (%s): the automatic one "
		              "stays, and resizing with the mouse will be hard",
		              kwinrc);

	/*
	 * ⭐ PHASE 15, D-005 — AND THE SESSION IS BORN EMPTY.  `[M]` round 1, 15-f021 on
	 *    KDE 4 times out of 4: after «Log Out» the new login reopened the program
	 *    that had been open.  ⛔ It is not ours: it is Plasma 6.3's restore,
	 *    `plasma-fallback-session-save` on exit and
	 *    `plasma-fallback-session-restore` (autostart) on entry.
	 * `[R]` plasma-workspace 6.3.6: both read `ksmserverrc`
	 *    `[General] loginMode` — `restore.cpp:30-33` exits at once with
	 *    `emptySession`; `shutdown.cpp:87` saves only with
	 *    `restorePreviousLogout`; `ksmserver/main.cpp:187` (the X11 windows)
	 *    likewise.  ⇒ A single key stops all three roads, ⭐ and on exit nothing is
	 *    even saved: the remote session does not overwrite the one the
	 *    user saved at the monitor.
	 * ⚠ WITHOUT `[$i]`, like the border: it is the starting point.  A `loginMode` written
	 *   by the user in `~/.config/ksmserverrc` (Settings → Desktop
	 *   Session, «restore manually saved session») sits higher and wins.
	 *   `[R]` the default value is not written (KConfigSkeleton), so
	 *   whoever never touched that entry gets ours.
	 */
	g_autofree char *ksmserverrc = g_build_filename(folder, "ksmserverrc", NULL);

	if (g_file_set_contents(ksmserverrc,
	                        "[General]\n"
	                        "loginMode=emptySession\n",
	                        -1, NULL))
		registro_dice(LOG_SESSION,
		              "⭐ Plasma: the session is born EMPTY (%s, loginMode=emptySession): "
		              "after «Log Out» whoever comes back does not find the previous programs",
		              ksmserverrc);
	else
		registro_dice(LOG_SESSION,
		              "⚠ Plasma: loginMode not written (%s): Plasma will reopen the "
		              "programs of the previous session",
		              ksmserverrc);
	return g_steal_pointer(&folder);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 15, D-015 — THE SESSION'S DCONF: THE USER'S SETTINGS
 *      ARE NOT TOUCHED (the user's decision of 25 Sep 2026, on all
 *      desktops).
 *
 * ⛔ THE DEFECT: on GNOME the layout negotiated with the browser was written
 *    into `org.gnome.desktop.input-sources` of the USER's dconf
 *    (`~/.config/dconf/user`), and stayed there: whoever then logged in at the monitor
 *    found the keyboard changed.  And with it the keys of
 *    `session_settings()` (lock, idle, «Log Out», Ctrl+Alt+F*).
 *
 * ⭐ THE CURE: a session dconf PROFILE, `$XDG_RUNTIME_DIR/remotix/
 *    dconf/profile`, with on top a WRITABLE database that lives in memory:
 *
 *        service-db:shm/remotix     ← EVERY write ends up here
 *        user-db:user               ← the user's, BELOW: read only
 *        (the other lines of the system profile, if there is one)
 *
 *   `[R]` dconf 0.40 (Debian 13): with several sources **only the first is
 *   written** (`dconf-engine-profile.c`: «If the first source is a "user-db:"
 *   or "service-db:" then the resulting profile will be writable»), reading goes
 *   from top to bottom, and change signals are listened to on ALL of them
 *   (`dconf_engine_watch_fast`).  ⇒ The session sees the user's settings
 *   with ours on top; the user sees nothing.
 *   `[R]` `shm` is a `dconf-service` writer (`dconf-shm-writer.c`)
 *   that keeps the database in `$XDG_RUNTIME_DIR/dconf-service/shm/` — tmpfs,
 *   never in `~/.config`.  ⚠ The name `remotix` without dashes: it ends up in a
 *   D-Bus path (`/ca/desrt/dconf/shm/remotix`), which refuses them.
 *
 * ⭐ HOW IT REACHES GNOME: `DCONF_PROFILE` in the environment of `gnome-session`
 *    (`compose_environment()`), which EXPORTS it to the user manager
 *    (`[R]` gnome-session `gsm_util_export_user_environment`: the whole environment
 *    except four variables) — the same road by which `XDG_SESSION_TYPE`
 *    reaches the Shell unit.  ⇒ `gnome-shell` (which applies
 *    `input-sources`: `keyboard.js`, `InputSourceManager`), the `gsd-*` and every
 *    program of the session read through the profile.  In the CHILD it is
 *    set by `session_dconf_prepare()`, before any `GSettings`.
 *
 * ⛔ WHY NOT «I WRITE AND THEN PUT IT BACK AS IT WAS»: it is the fragile road.  If the
 *    child dies badly, or the machine powers off with the session open, our
 *    value stays in the user's file FOREVER, and nobody puts it back.  Here
 *    there is nothing to put back: the user's file is never written.
 *
 * ⚠ THE PRICES, declared:
 *   · whatever the USER changes from the remote desktop (the wallpaper, a
 *     shortcut) also ends up in the session database, and is lost when the
 *     session is reborn (`session_dconf_reset()`) or the machine reboots;
 *   · the MANDATORY profile (`/run/dconf/user/<uid>`) wins over
 *     `DCONF_PROFILE`: if it exists, the cure cannot hold, and it is said;
 *   · the variable stays in the user manager's environment as long as it lives
 *     (and the profile file with it: both are in `XDG_RUNTIME_DIR`).
 *     A login at the monitor that shared THAT manager would inherit it —
 *     as it already inherits the `--headless` drop-in of `write_dropin()`.
 */
#define DCONF_SESSION_SOURCE "service-db:shm/remotix"
#define DCONF_SESSION_OBJECT "/ca/desrt/dconf/shm/remotix"

static char *dconf_profile_path(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, "remotix", "dconf", "profile", NULL);
}

static gboolean dconf_in_effect;

/* The profile dconf would use WITHOUT us, in the order of
 * `dconf_engine_profile_open()`: `DCONF_PROFILE` (if it is not ours), the
 * runtime one, `user` in `/etc` and in the `XDG_DATA_DIRS`.  NULL = none, that is
 * dconf's default, «user-db:user». */
static char *dconf_base_profile(const char *our)
{
	const char *env = g_getenv("DCONF_PROFILE");
	g_autoptr(GPtrArray) candidates = g_ptr_array_new_with_free_func(g_free);
	const char *const *data = g_get_system_data_dirs();

	if (env && *env && g_strcmp0(env, our) != 0) {
		if (env[0] == '/')
			g_ptr_array_add(candidates, g_strdup(env));
		else {
			g_ptr_array_add(candidates, g_build_filename("/etc/dconf/profile", env, NULL));
			for (int i = 0; data[i]; i++)
				g_ptr_array_add(candidates,
				                g_build_filename(data[i], "dconf", "profile", env, NULL));
		}
	} else {
		g_ptr_array_add(candidates, g_build_filename(g_get_user_runtime_dir(), "dconf",
		                                            "profile", NULL));
		g_ptr_array_add(candidates, g_strdup("/etc/dconf/profile/user"));
		for (int i = 0; data[i]; i++)
			g_ptr_array_add(candidates,
			                g_build_filename(data[i], "dconf", "profile", "user", NULL));
	}
	for (guint i = 0; i < candidates->len; i++) {
		char *text = NULL;

		if (g_file_get_contents(g_ptr_array_index(candidates, i), &text, NULL, NULL))
			return text;
	}
	return NULL;
}

bool session_dconf_prepare(void)
{
	g_autofree char *fpath = dconf_profile_path();
	g_autofree char *folder = NULL;
	g_autofree char *mandatory = NULL;
	g_autofree char *base = NULL;
	g_autoptr(GString) profile = g_string_new(NULL);
	g_autoptr(GError) mistake = NULL;
	g_auto(GStrv) lines = NULL;
	int sources = 0;

	/* ⚠ GNOME only: the other desktops do not read their settings from
	 *   dconf, and set the layout by other roads (the session's kxkbrc
	 *   on KDE, the virtual keyboard's keymap on wlroots). */
	if (desktop_session() != SESSION_DESKTOP_GNOME)
		return false;
	if (!fpath) {
		registro_dice(LOG_SESSION,
		              "⛔ D-015: XDG_RUNTIME_DIR not set — no session dconf, "
		              "and so the negotiated layout is NOT written");
		return false;
	}
	mandatory = g_strdup_printf("/run/dconf/user/%u", (unsigned) getuid());
	if (g_file_test(mandatory, G_FILE_TEST_EXISTS)) {
		registro_dice(LOG_SESSION,
		              "⛔ D-015: there is a MANDATORY dconf profile (%s), and it wins over "
		              "DCONF_PROFILE: the session dconf cannot hold, and the "
		              "negotiated layout is NOT written",
		              mandatory);
		return false;
	}

	g_string_append(profile,
	                "# REMOTIX (D-015): the dconf of the remote session.  On top an\n"
	                "# in-memory database that takes EVERY write; below, read-only,\n"
	                "# the user's and the system databases.\n"
	                DCONF_SESSION_SOURCE "\n");
	base = dconf_base_profile(fpath);
	lines = g_strsplit(base ? base : "", "\n", -1);
	for (int i = 0; lines[i]; i++) {
		const char *r = g_strstrip(lines[i]);

		if (!*r || r[0] == '#' || g_strcmp0(r, DCONF_SESSION_SOURCE) == 0)
			continue;
		if (g_str_has_prefix(r, "user-db:") || g_str_has_prefix(r, "system-db:") ||
		    g_str_has_prefix(r, "service-db:") || g_str_has_prefix(r, "file-db:")) {
			g_string_append_printf(profile, "%s\n", r);
			sources++;
		}
	}
	if (!sources)
		g_string_append(profile, "user-db:user\n");

	folder = g_path_get_dirname(fpath);
	if (g_mkdir_with_parents(folder, 0700) != 0 ||
	    !g_file_set_contents(fpath, profile->str, -1, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⛔ D-015: the session's dconf profile cannot be written (%s): %s — "
		              "and so the negotiated layout is NOT written",
		              fpath, mistake ? mistake->message : g_strerror(errno));
		return false;
	}
	/* ⛔ Before any `GSettings` of the child: the dconf engine reads
	 *    `DCONF_PROFILE` only once, when it is born. */
	g_setenv("DCONF_PROFILE", fpath, TRUE);
	dconf_in_effect = TRUE;
	registro_dice(LOG_SESSION,
	              "⭐ D-015: SESSION dconf in %s (" DCONF_SESSION_SOURCE
	              " on top, %s below read-only): what the session writes "
	              "does NOT touch the user's settings",
	              fpath, sources ? "the system profile" : "user-db:user");
	return true;
}

bool session_dconf_of_session(void)
{
	g_autofree char *fpath = dconf_profile_path();

	return dconf_in_effect && fpath &&
	       g_strcmp0(g_getenv("DCONF_PROFILE"), fpath) == 0 &&
	       g_file_test(fpath, G_FILE_TEST_EXISTS);
}

/*
 * A direct write to a `dconf-service` writer — `object` is
 * `/ca/desrt/dconf/shm/remotix` (the session) or `/ca/desrt/dconf/Writer/user`
 * (the USER) — without going through the process's engine, which has the
 * session profile.  `value` NULL = remove (`fpath` ending with `/`: the whole
 * folder).
 * `[R]` dconf 0.40: `ca.desrt.dconf.Writer.Change` wants the bytes of an
 *    `a{smv}` (`dconf_changeset_serialise`); the writer notifies the readers
 *    (`Notify`), so the Shell and the `gsd-*` see the change at once.
 */
static gboolean dconf_change(const char *object, const char *fpath, GVariant *value,
                             GError **mistake)
{
	g_autoptr(GDBusConnection) bus = sess_bus(mistake);
	g_autoptr(GVariant) together = NULL;
	g_autoptr(GVariant) response = NULL;
	GVariantBuilder b;

	if (!bus)
		return FALSE;
	g_variant_builder_init(&b, G_VARIANT_TYPE("a{smv}"));
	g_variant_builder_add(&b, "{smv}", fpath, value);
	together = g_variant_ref_sink(g_variant_builder_end(&b));
	response = g_dbus_connection_call_sync(
		bus, "ca.desrt.dconf", object, "ca.desrt.dconf.Writer", "Change",
		g_variant_new("(@ay)",
		              g_variant_new_fixed_array(G_VARIANT_TYPE_BYTE,
		                                        g_variant_get_data(together),
		                                        g_variant_get_size(together), 1)),
		G_VARIANT_TYPE("(s)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, mistake);
	return response != NULL;
}

/*
 * ⭐ At birth the session database is EMPTIED: the new session
 *    starts from the user's current settings, plus ours — not from
 *    what the previous session (or its client) had left there.
 *    It is `dconf reset -f /` said by hand, so as not to depend on `dconf-cli`.
 */
static void session_dconf_reset(void)
{
	g_autoptr(GError) mistake = NULL;

	if (!session_dconf_of_session())
		return;
	if (dconf_change(DCONF_SESSION_OBJECT, "/", NULL, &mistake))
		registro_dice(LOG_SESSION,
		              "⭐ D-015: session dconf EMPTIED — the session is born from the "
		              "user's current settings, plus ours");
	else
		registro_dice(LOG_SESSION,
		              "⚠ D-015: the session dconf cannot be emptied (%s): the new "
		              "session inherits what the previous one had — the user stays "
		              "intact anyway",
		              mistake ? mistake->message : "no reason given");
}

/*
 * ⭐ PHASE 15, D-018 — the two folders of the LXQt SESSION, at the head of
 *    `XDG_CONFIG_DIRS` and `XDG_DATA_DIRS` (`compose_environment()`): what
 *    the session must have and which is not lock, reboot, suspend or
 *    standby lives here, and not in the user's files.  NULL without
 *    `XDG_RUNTIME_DIR`.
 */
static char *lxqt_session_config_folder(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "xdg-lxqt", NULL) : NULL;
}

static char *lxqt_session_data_folder(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "data-lxqt", NULL)
	                           : NULL;
}

/*
 * ⭐ PHASE 15, D-007 — THE labwc CONFIGURATION PIECE FOR XFCE: only the
 *    shortcut that brings windows back inside (`SESSION_LABWC_KEYBOARD`).
 *
 * ⛔ On XFCE the labwc configuration belongs to the USER (`~/.config/labwc`), and
 *    stays theirs: this file is in a folder of OURS put at the head of
 *    `XDG_CONFIG_DIRS`, and labwc starts with `-m` (`SESSION_LINE_XFCE`), which
 *    reads and MERGES the `rc.xml` of all the folders — ours first, then
 *    the user's, which win where they say the same thing (`[R]` labwc
 *    0.8.3 `src/config/rcxml.c:1898-1937`).
 * ⚠ With `<default/>`: if the user has no shortcuts of their own, their default ones
 *   stay (with ONE `<keybind>` labwc would no longer load them).
 *
 * Returns the folder to put in `XDG_CONFIG_DIRS`, or NULL (said: the
 * session is born anyway, without the cure).
 */
static char *write_config_labwc_xfce(const char *runtime)
{
	g_autofree char *folder = NULL;
	g_autofree char *below = NULL;
	g_autofree char *rc = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!runtime || !*runtime)
		return NULL;
	folder = g_build_filename(runtime, "remotix", "labwc-xfce", NULL);
	below = g_build_filename(folder, "labwc", NULL);
	rc = g_build_filename(below, "rc.xml", NULL);
	if (g_mkdir_with_parents(below, 0700) != 0 ||
	    !g_file_set_contents(rc,
	                         "<?xml version=\"1.0\"?>\n"
	                         "<!-- REMOTIX (D-007): written at every birth of the "
	                         "XFCE session, do not edit.\n"
	                         "     labwc starts with -m: this is MERGED with the user's "
	                         "rc.xml.  " SESSION_LABWC_KEY " brings "
	                         "windows back inside\n     when the remote screen "
	                         "shrinks. -->\n"
	                         "<labwc_config>\n" SESSION_LABWC_KEYBOARD
	                         "</labwc_config>\n",
	                         -1, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⛔ XFCE, D-007: the labwc configuration is NOT written in %s "
		              "(%s) — the session is born anyway, but reattaching with a "
		              "smaller window the large windows will stay partly "
		              "OUTSIDE the screen",
		              rc, mistake ? mistake->message : g_strerror(errno));
		return NULL;
	}
	registro_dice(LOG_SESSION,
	              "⭐ XFCE, D-007: «bring back inside» shortcut (%s) for labwc in %s, "
	              "merged with the user's configuration (-m)",
	              SESSION_LABWC_KEY, rc);
	return g_steal_pointer(&folder);
}

/*
 * The session environment, composed from scratch: what is not needed does not pass.
 * Ten variables, one at a time (`CODER.md` §4.5).
 */
static char **compose_environment(void)
{
	GPtrArray *environment = g_ptr_array_new_with_free_func(g_free);
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	const char *bus = g_getenv("DBUS_SESSION_BUS_ADDRESS");
	g_autofree char *bus_inferred = NULL;

	if (!runtime || !*runtime) {
		registro_dice(LOG_SESSION,
		              "⛔ XDG_RUNTIME_DIR not set: I do not know where the session lives");
		g_ptr_array_free(environment, TRUE);
		return NULL;
	}
	if (!bus || !*bus) {
		/* The session bus conventionally lives in there; deducing it is better
		 * than giving up, because an environment lacking the variable — a systemd
		 * unit, for example — is entirely normal. */
		bus_inferred = g_strdup_printf("unix:path=%s/bus", runtime);
		bus = bus_inferred;
		registro_dice(LOG_SESSION, "DBUS_SESSION_BUS_ADDRESS missing: using %s", bus);
	}

	g_ptr_array_add(environment, g_strdup_printf("XDG_RUNTIME_DIR=%s", runtime));
	g_ptr_array_add(environment, g_strdup_printf("DBUS_SESSION_BUS_ADDRESS=%s", bus));

	/*
	 * ⭐ PHASE 12 — on Plasma the middle of the environment is different, and shorter
	 *    (`STUDIES.md` §kde §6.1, v1's recipe `[M]` 7-8 August 2026):
	 *
	 *   · `XDG_MENU_PREFIX=plasma-` — ⛔ without it, `kbuildsycoca6` builds an
	 *     EMPTY index and KWin denies capture without saying why (§3.3-bis).
	 *     `startplasma` sets it on its own, but a process that rebuilds
	 *     the index before it overwrites it: it is set here, for the whole tree;
	 *   · ⛔ NO `XDG_CURRENT_DESKTOP`, `XDG_SESSION_TYPE`, `DISPLAY`,
	 *     `WAYLAND_DISPLAY`, `QT_QPA_PLATFORM`: with any of these KWin picks the
	 *     NESTED backend instead of `--virtual` (`main_wayland.cpp:452-463`),
	 *     and Plasma sets them on its own (`startplasma.cpp:353-414`);
	 *   · ⛔ no `SHELL=`: the login shell trap belongs to
	 *     `gnome-session`, and `startplasma-wayland` does not have it.
	 */
	if (e_kde()) {
		g_autofree char *rules = write_kde_menu_rules(runtime);
		g_autofree char *icons = write_cursor_theme(runtime);

		g_ptr_array_add(environment, g_strdup("XDG_MENU_PREFIX=plasma-"));
		/* ⚠ IN FRONT of `/etc/xdg`, not in its place: from there comes
		 *   `menus/plasma-applications.menu`, the file the prefix above
		 *   looks for — replacing it would switch capture off (§3.3-bis). */
		if (rules)
			g_ptr_array_add(environment,
			                g_strdup_printf("XDG_CONFIG_DIRS=%s:%s", rules,
			                                g_getenv("XDG_CONFIG_DIRS") ?: "/etc/xdg"));
		/* ⛔ THE THREE VARIABLES GO TOGETHER: `XCURSOR_THEME` alone is not enough
		 *    (KWin looks at it only with `XCURSOR_SIZE`), and `XCURSOR_PATH` is needed
		 *    because the theme lives in `XDG_RUNTIME_DIR`, which no default
		 *    search looks at — with the system folders at the end, so as not to
		 *    take the real themes away from whoever looks for them for other reasons. */
		if (icons) {
			g_ptr_array_add(environment, g_strdup("XCURSOR_THEME=" THEME_CURSOR));
			g_ptr_array_add(environment, g_strdup("XCURSOR_SIZE=24"));
			g_ptr_array_add(environment,
			                g_strdup_printf("XCURSOR_PATH=%s:%s", icons,
			                                "/usr/share/icons:/usr/local/share/icons"));
		}
		goto queue;
	}

	/*
	 * ⭐⭐ PHASE 13 — THE XFCE ENVIRONMENT, and every line has paid for its place
	 *      (`STUDIES.md` §xfce §9.3, §10.1; `[M]` tried inside `rete11-xfce` on
	 *      20 Sep 2026: whole session alive, panel and desktop included).
	 *
	 * ⭐ The «to remove» column is already free: `compose_environment()` builds
	 *   from scratch and inherits nothing except `PATH` — `DISPLAY`,
	 *   `WAYLAND_DISPLAY`, `SESSION_MANAGER` are not there by construction.  ⛔ The
	 *   danger is only what gets ADDED, and it is the GNOME block below
	 *   into which XFCE would fall without this `if`.
	 */
	/*
	 * ⭐⭐ PHASE 14 — AND THE LXQt ENVIRONMENT LIVES IN THE SAME BLOCK, because half
	 *      of the lines belong to LABWC and not to the desktop: `WLR_*`, the card,
	 *      `LABWC_UPDATE_ACTIVATION_ENV`, the cursor.  ⛔ Writing them twice
	 *      would mean they could diverge.  The DESKTOP lines live
	 *      in two separate branches, and the XFCE branch is the one from before.
	 */
	if (e_xfce() || e_lxqt()) {
		g_autofree char *icons = write_cursor_theme(runtime);

		if (e_xfce()) {
			/* ⛔ BARE and uppercase, without suffixes: labwc would put
			 *    `labwc:wlroots`, and garcon does not split on `:` — with a suffix the
			 *    `OnlyShowIn=XFCE;` entries **disappear** from the menu. */
			g_ptr_array_add(environment, g_strdup("XDG_CURRENT_DESKTOP=XFCE"));
			g_ptr_array_add(environment, g_strdup("XDG_SESSION_DESKTOP=xfce"));
			g_ptr_array_add(environment, g_strdup("XDG_SESSION_TYPE=wayland"));
			/* ⚠ Not because it is missing — garcon has a fallback — but so as not to INHERIT
			 *   a wrong one: the check in there is `prefix != NULL`. */
			g_ptr_array_add(environment, g_strdup("XDG_MENU_PREFIX=xfce-"));
			/* ⭐ PHASE 15, D-007 — the folder with the labwc shortcut, IN FRONT of
			 *    the system folders (not in their place): inside there is only
			 *    `labwc/rc.xml`, so for every other program nothing
			 *    changes. */
			{
				g_autofree char *labwc_cfg = write_config_labwc_xfce(runtime);
				const char *prima = g_getenv("XDG_CONFIG_DIRS");

				if (labwc_cfg)
					g_ptr_array_add(environment,
					                g_strdup_printf("XDG_CONFIG_DIRS=%s:%s", labwc_cfg,
					                                prima && *prima ? prima : "/etc/xdg"));
			}
		} else {
			/*
			 * ⭐ PHASE 14 — THE LXQt LINES (`STUDIES.md` §lxqt §3.2), and every value
			 *    is that of the contemporary upstream launcher, `labwc` branch:
			 *    `[R]` lxqt-wayland-session 0.1.1 `startlxqtwayland.in`.
			 *
			 * ⛔⛔ `XDG_CURRENT_DESKTOP` NOT BARE, unlike XFCE: the
			 *     panel picks the window backend **from the tokens** (`wlroots`
			 *     the strongest), and with bare `LXQt` it falls on the `dummy` backend —
			 *     empty taskbar, everything inert, a single `qWarning`.  And the modules have
			 *     `OnlyShowIn=LXQt;`: without `LXQt` the session is alive and BLACK.
			 * ⭐ `LXQt:labwc:wlroots` and not `LXQt:wlroots`: it is the form the upstream
			 *    script gives to whoever HAS configured labwc (`"LXQt:$COMPOSITOR:wlroots"`);
			 *    it uses `LXQt:wlroots` only for the first start, the one that opens the
			 *    wizard.  Both carry `LXQt` and `wlroots`; `STUDIES.md` §lxqt §3.2
			 *    chooses the first, and here it is kept.
			 * ⚠ labwc sets it only if missing (`setenv(…, 0)`, `[R]` labwc 0.8.3
			 *   `src/config/session.c:256`): ours stays. */
			g_ptr_array_add(environment, g_strdup("XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots"));
			g_ptr_array_add(environment, g_strdup("XDG_SESSION_DESKTOP=lxqt"));
			/* ⛔ Not cosmetic: the panel picks the backend from THIS, not from
			 *    `platformName()` (`STUDIES.md` §lxqt §3.2). */
			g_ptr_array_add(environment, g_strdup("XDG_SESSION_TYPE=wayland"));
			/* ⛔ No hardwired fallback in libqtxdg: without it, there is no menu. */
			g_ptr_array_add(environment, g_strdup("XDG_MENU_PREFIX=lxqt-"));
			/* ⛔ It must contain `/usr/share`: LXQt's defaults live in
			 *    `/usr/share/lxqt/<module>.conf`, and without it they vanish SILENTLY.  The
			 *    value is that of the upstream script, word for word, with
			 *    `/etc/xdg` (Debian's touch-up, `lxqt-branding-debian`) in front of
			 *    `/usr/share`.  [?] Which of the two really wins is measurement M6. */
			/* ⭐ PHASE 15, D-018 — and IN FRONT of all, the SESSION
			 *    folder (`lxqt_panel()`): what the session must have
			 *    lives there, not in the user's files.  ⚠ Only `~/.config` stays before it,
			 *    that is the user — who wins, and that is fine. */
			{
				g_autofree char *cfg = lxqt_session_config_folder();
				g_autofree char *data = lxqt_session_data_folder();
				const char *data_before = g_getenv("XDG_DATA_DIRS");

				g_ptr_array_add(environment,
				                g_strdup_printf("XDG_CONFIG_DIRS=%s%s/etc:/etc/xdg:/usr/share",
				                                cfg ? cfg : "", cfg ? ":" : ""));
				/* and the DATA: the dangerous menu entries hidden
				 * (`settings_lxqt()`), at the head of the system ones */
				if (data)
					g_ptr_array_add(environment,
					                g_strdup_printf("XDG_DATA_DIRS=%s:%s", data,
					                                data_before && *data_before
					                                        ? data_before
					                                        : "/usr/local/share:/usr/share"));
			}
			/* ⛔ BARE (`STUDIES.md` §lxqt §3.2, `LESSONS.md` §1.8): with xcb
			 *    `lxqt-session` becomes another session — a second window
			 *    manager, a modal dialog, a second commander of the
			 *    resolution.  ⚠ The upstream script does NOT set it: it is our
			 *    choice, and the price is declared — a Qt application without the
			 *    wayland plugin dies (`qFatal`) instead of falling back to Xwayland.
			 *    [?] To be looked at on the box: who dies this way (qlipper is Qt5). */
			g_ptr_array_add(environment, g_strdup("QT_QPA_PLATFORM=wayland"));
			/* LXQt's Qt theme (`lxqt-qtplugin`): the desktop's icons, style and fonts.
			 * The upstream script sets it; without it, the desktop starts with
			 * Qt's bare look. */
			g_ptr_array_add(environment, g_strdup("QT_QPA_PLATFORMTHEME=lxqt"));
		}
		/* ⛔ This family's «no screen».  With `headless` no
		 *    `wlr_session` is born and libseat is not even touched: the wall
		 *    KWin died against here does not exist. */
		g_ptr_array_add(environment, g_strdup("WLR_BACKENDS=headless"));
		g_ptr_array_add(environment, g_strdup("WLR_LIBINPUT_NO_DEVICES=1"));
		/* ⛔⛔ WITHOUT A FALLBACK: if this node does not open, wlroots falls back to
		 *     pixman — **software, silently**.  It is the same shape as the
		 *     encoder that falls back and declares it, but here nobody
		 *     declares it: the only way to notice is that the numbers collapse. */
		/* ⭐ PHASE 17 — and opening it is not enough: the card must be able to CREATE the
		 *   buffer (`card_can_draw()`).  If it cannot, labwc would draw
		 *   a black canvas ⇒ pixman is asked for by name (CODER §3.9) and it is
		 *   written: DECLARED FALLBACK, not silent.  ⚠ Without
		 *   `WLR_RENDER_DRM_DEVICE`: pixman does not draw on the card. */
		{
			card_pick_how how;
			g_autofree char *story = NULL;
			g_autofree char *node = card_node(&how, &story);

			if (!node && how == CARD_PICK_NONE_CAPABLE) {
				g_ptr_array_add(environment, g_strdup("WLR_RENDERER=pixman"));
				registro_dice(LOG_SESSION,
				              "⛔ %s: render nodes open but NO card can create the "
				              "output buffer (%s).  DECLARED FALLBACK: "
				              "WLR_RENDERER=pixman — labwc draws in MEMORY, "
				              "with the processor; without it, the canvas would be black",
				              desktop_name(), story);
			} else if (node) {
				g_ptr_array_add(environment,
				                g_strdup_printf("WLR_RENDER_DRM_DEVICE=%s", node));
				card_say(desktop_name(), node, story);
			} else {
				registro_dice(LOG_SESSION,
				              "⛔ %s: %s — I do NOT "
				              "pass WLR_RENDER_DRM_DEVICE, and wlroots will choose by itself. "
				              "⚠ If it falls back to pixman it does so SILENTLY: the numbers "
				              "will collapse and this is the only line that explains it",
				              desktop_name(), story);
			}
		}
		/* ⛔ MANDATORY: without it, on headless labwc **does not propagate**
		 *    `WAYLAND_DISPLAY` to the bus and to systemd, and does so silently ⇒ the
		 *    session's applications do not find the compositor. */
		g_ptr_array_add(environment, g_strdup("LABWC_UPDATE_ACTIVATION_ENV=1"));
		/*
		 * ⭐ PHASE 14 — the two lines below belong to XFCE and stay ONLY its own:
		 *   · bare `GDK_BACKEND` cures XFCE's screensaver on Xwayland, which
		 *     does not exist in LXQt; LXQt's upstream script does not set it, and GTK
		 *     takes wayland first by itself.  [?] To be looked at whether
		 *     a GTK application ends up on Xwayland inside LXQt;
		 *   · `XFCE4_SESSION_COMPOSITOR` is read only by `xfce4-session`: on LXQt
		 *     the `loginctl terminate-session` trap does not exist
		 *     (`STUDIES.md` §lxqt §3.3, `[✗]`).
		 */
		if (e_xfce()) {
			/* ⛔ BARE: `wayland,x11` revives the screensaver on Xwayland and
			 *    turns XSETTINGS and the grabs back on — two behaviours under a single
			 *    label, which is what makes a measurement incomparable. */
			g_ptr_array_add(environment, g_strdup("GDK_BACKEND=wayland"));
			/*
			 * ⛔⛔ THE LOGOUT BELT, and it is not a decorative variable.
			 *
			 * `xfce4-session` reads THIS, not what we really executed,
			 * and if it does not find **both** `labwc` **and** `--session` in it, at
			 * logout it runs `loginctl terminate-session ''` — that is it kills
			 * REMOTIX's logind session (`STUDIES.md` §xfce §9.2).  ⇒ We put in it
			 *   the EXACT line that is executed, removing the `exec` in front, which has nothing
			 *   to do with it here.
			 */
			g_ptr_array_add(environment,
			                g_strdup("XFCE4_SESSION_COMPOSITOR=" SESSION_LINE_XFCE));
		}
		/* The cursor: the same cure as KDE (1x1 theme with zero alpha), with one
		 * constraint fewer — `XCURSOR_SIZE` is not mandatory here.  ⛔ But the
		 * theme must BE THERE: with an empty theme wlroots falls back to a built-in,
		 * VISIBLE one, which is the opposite of what we wanted. */
		if (icons) {
			g_ptr_array_add(environment, g_strdup("XCURSOR_THEME=" THEME_CURSOR));
			g_ptr_array_add(environment, g_strdup("XCURSOR_SIZE=24"));
			g_ptr_array_add(environment,
			                g_strdup_printf("XCURSOR_PATH=%s:%s", icons,
			                                "/usr/share/icons:/usr/local/share/icons"));
		}
		goto queue;
	}

	/* The session must DECLARE itself, or GNOME applications do not
	 * recognise they are at home and stop by themselves. */
	/* ⭐ D8: from the default session (`DesktopNames` and the file name), as
	 *    GDM does — on Ubuntu `ubuntu:GNOME` and `ubuntu`: Ubuntu's default settings
	 *    are written for `ubuntu` (`[org.gnome…:ubuntu]` in the glib
	 *    overrides), and with `GNOME` the Shell would have Adwaita's colours. */
	g_ptr_array_add(environment, g_strconcat("XDG_CURRENT_DESKTOP=", gnome_session()->desktop,
	                                      NULL));
	g_ptr_array_add(environment, g_strconcat("XDG_SESSION_DESKTOP=", gnome_session()->id, NULL));
	/*
	 * ⛔ `XDG_SESSION_TYPE=wayland` IS NEEDED, and it is not a lie: the Shell's
	 *    unit carries `ConditionEnvironment=XDG_SESSION_TYPE=wayland` (checked
	 *    in the file installed on NIC-OS on 12 Aug 2026), and without it the compositor
	 *    is not started AT ALL — a maimed session, and no line saying
	 *    why.
	 */
	g_ptr_array_add(environment, g_strdup("XDG_SESSION_TYPE=wayland"));
	/*
	 * ⛔ `SHELL` EMPTY, and it is the trap of `STUDIES.md` §gnome §3.1: `gnome-session.in:3-14`
	 *    re-executes itself inside a LOGIN shell if `$SHELL` is not empty and is in
	 *    `/etc/shells` — that is it drags `~/.profile` back in, which is `CODER.md`
	 *    §4.5 lying in wait after the environment has been carefully composed.
	 *
	 * ⚠ The real check is `[ -n "$SHELL" ]`, so ABSENT and EMPTY are
	 *   both fine — and v1 left it absent, by construction, without
	 *   knowing it.  Here it is set EMPTY on purpose: absent and empty are the
	 *   same thing for `gnome-session` and **two different things for whoever measures**,
	 *   because empty shows in `/proc/<gnome-session-binary>/environ` while absent
	 *   is confused with «I did not read the environment».
	 */
	g_ptr_array_add(environment, g_strdup("SHELL="));
	/* ⭐ PHASE 15, D-015 — the session dconf: `gnome-session` exports it
	 *    to the user manager, and the Shell and the `gsd-*` inherit it (the box
	 *    above `session_dconf_prepare()`). */
	if (session_dconf_of_session()) {
		g_autofree char *profile = dconf_profile_path();

		g_ptr_array_add(environment, g_strdup_printf("DCONF_PROFILE=%s", profile));
	} else
		registro_dice(LOG_SESSION,
		              "⛔ D-015: the GNOME session is born WITHOUT the session dconf "
		              "— what the session writes will end up in the user's "
		              "settings");
	/*
	 * ⚠ And `XDG_SESSION_ID` is NOT passed, on purpose.  `STUDIES.md` §gnome §3.1 warns
	 *   that without it Mutter may latch onto the wrong logind session —
	 *   but the one we would inherit is the session of WHOEVER STARTED US (an
	 *   ssh, that is `tty`), and handing it over would send it onto the wrong
	 *   session **with our signature on it**.  ⭐ The scene measured healthy on 12
	 *   August 2026 does not carry it.  What happens when REMOTIX
	 *   runs as a system unit remains `[?]`.
	 */
queue:
	/*
	 * ⭐ D-022 (phase 16, 27-28 Sep 2026) — OUTSIDE GNOME `SHELL` is the
	 *    user's own, from their passwd line.
	 *
	 * `[M]` live XFCE session: `labwc` and `xfce4-panel` were born **without**
	 * `SHELL` (the environment here is composed from scratch), while the same user's
	 * `systemd --user` has `/bin/bash`.  xfce4-terminal, konsole and
	 * gnome-terminal read passwd and do not notice; **qterminal**
	 * (qtermwidget) reads `$SHELL`, and without it falls back to `/bin/sh` — an LXQt
	 * user opened the terminal and did not find their shell.
	 * ⛔ GNOME stays as it is: the empty `SHELL` above is the cure for the
	 *    `gnome-session` trap, which the other three do not have.
	 */
	if (e_kde() || e_xfce() || e_lxqt()) {
		const struct passwd *pw = getpwuid(getuid());

		if (pw && pw->pw_shell && *pw->pw_shell)
			g_ptr_array_add(environment, g_strdup_printf("SHELL=%s", pw->pw_shell));
		else
			registro_dice(LOG_SESSION,
			              "⚠ D-022: the user has no shell in passwd — the session "
			              "is born without `SHELL`, and qterminal will fall back to /bin/sh");
	}
	g_ptr_array_add(environment, g_strdup_printf("LANG=%s", local_utf8()));
	g_ptr_array_add(environment, g_strdup_printf("HOME=%s", g_get_home_dir()));
	g_ptr_array_add(environment, g_strdup_printf("USER=%s", g_get_user_name()));
	g_ptr_array_add(environment, g_strdup_printf("PATH=%s", g_getenv("PATH") ?: "/usr/bin:/bin"));
	g_ptr_array_add(environment, NULL);

	return (char **) g_ptr_array_free(environment, FALSE);
}

/* ------------------------------------------------------------------------- */
/*
 * A command, with its exit.
 *
 * ⛔ Two functions and not one, and the difference is `REVIEWER.md` §1 point 4: for
 *    `daemon-reload` the exit status IS the answer and is looked at; for
 *    `is-active` the exit status is 3 when the answer is «inactive», that is
 *    the normal case — looking at it there would mean calling an answer
 *    a failure.  Whoever confuses them gets a bench that stops when everything goes
 *    well, or worse one that never stops.
 */
static gboolean run(char **argv)
{
	g_autoptr(GError) mistake = NULL;
	int state = 0;

	if (!g_spawn_sync(NULL, argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, NULL, &state,
	                  &mistake) ||
	    !g_spawn_check_wait_status(state, &mistake)) {
		registro_dice(LOG_SESSION, "⛔ «%s …» did not succeed: %s", argv[0],
		              mistake ? mistake->message : "no reason given");
		return FALSE;
	}
	return TRUE;
}

/* The standard output of a command, whatever its exit status.
 * NULL only if I could not EXECUTE it — which is a different fact. */
static char *ask(char **argv)
{
	g_autoptr(GError) mistake = NULL;
	char *output = NULL;
	int state = 0;

	if (!g_spawn_sync(NULL, argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, &output, NULL, &state,
	                  &mistake)) {
		registro_dice(LOG_SESSION, "⛔ I could not execute «%s»: %s", argv[0],
		              mistake ? mistake->message : "no reason given");
		return NULL;
	}
	return output;
}

/*
 * ⭐ PHASE 17 — WHICH SHELL UNIT gnome-session starts on THIS machine
 *    (`session.h`, `SESSIONE_UNITA_SHELL_*`; `phases/17-the-installer.md` §5.1).
 *
 * The user manager is asked from which FILE it would load
 * `org.gnome.Shell@wayland.service` (`FragmentPath`):
 *   · the file `…/org.gnome.Shell@wayland.service` ⇒ GNOME ≤ 49, it is that one;
 *   · the template `…/org.gnome.Shell@.service` ⇒ GNOME 50: the session asks for
 *     ITS instance (D8: `Requires` of `gnome-session@<session>.target` —
 *     `@user` for `gnome`, `@ubuntu` for `ubuntu`), and `@wayland` is an instance
 *     that NOBODY starts.  The caller frees the string.
 *
 * ⛔⛔ It is the FALSE GREEN this function closes: on GNOME 50
 *     `systemctl --user show -p ExecStart org.gnome.Shell@wayland.service` creates
 *     the «wayland» instance from the template, applies our drop-in to it and returns
 *     our line — the check passed, and gnome-session started `@user`
 *     without `--headless`.
 *
 * ⚠ The manager and not a list of folders written here: the user unit
 *   folders are many (also from `XDG_DATA_DIRS`) and it knows them.
 * ⛔ NULL if I recognise nothing: «I don't know» does not become a bet on
 *   one of the two names, and the caller stops saying so.
 */
static char *unit_shell(void)
{
	char *argv[] = { "systemctl", "--user", "show", "-p", "FragmentPath", "--value",
		         SESSION_UNIT_SHELL_48, NULL };
	g_autofree char *fragment = ask(argv);
	g_autofree char *target = NULL;
	g_autofree char *requests = NULL;
	g_auto(GStrv) entries = NULL;
	char *ask_target[] = { "systemctl", "--user", "show", "-p", "Requires", "--value",
		                     NULL, NULL };

	if (!fragment) {
		registro_dice(LOG_SESSION, "⛔ I could not ask the user manager "
		                            "which Shell unit there is");
		return NULL;
	}
	g_strstrip(fragment);
	if (g_str_has_suffix(fragment, "/" SESSION_UNIT_SHELL_48))
		return g_strdup(SESSION_UNIT_SHELL_48);
	if (g_str_has_suffix(fragment, "/" SESSION_UNIT_SHELL_MODEL)) {
		/* ⭐ D8: the instance is asked for by the SESSION (`gnome` ⇒ `@user`, `ubuntu`
		 *    ⇒ `@ubuntu`), and it is read from its target, drop-ins included. */
		target = g_strdup_printf("gnome-session@%s.target", gnome_session()->name);
		ask_target[6] = target;
		requests = ask(ask_target);
		entries = requests ? g_strsplit_set(g_strstrip(requests), " \t\n", -1) : NULL;
		for (int i = 0; entries && entries[i]; i++)
			if (g_str_has_prefix(entries[i], "org.gnome.Shell@") &&
			    g_str_has_suffix(entries[i], ".service") &&
			    strcmp(entries[i], SESSION_UNIT_SHELL_MODEL) != 0)
				return g_strdup(entries[i]);
		registro_dice(LOG_SESSION,
		              "⛔ GNOME 50: the Shell is the template " SESSION_UNIT_SHELL_MODEL
		              ", but %s does not ask for any instance of it (Requires: «%s»): I do not know "
		              "which Shell the session will start, and I do not bet",
		              target, requests ? requests : "(no answer)");
		return NULL;
	}
	registro_dice(LOG_SESSION,
	              "⛔ I do not recognise the Shell unit: the manager loads «%s» from «%s», "
	              "and I only know " SESSION_UNIT_SHELL_48 " (GNOME ≤ 49) and the "
	              "template " SESSION_UNIT_SHELL_MODEL " (GNOME 50)",
	              SESSION_UNIT_SHELL_48, *fragment ? fragment : "(nothing)");
	return NULL;
}

/*
 * ⛔⭐ THE DROP-IN — THE LINE THAT IN v1 WAS WRITTEN ONLY FOR KWIN.
 *
 * `gnome-session` does not launch `gnome-shell`: it starts the Shell's user
 * unit (which one, `unit_shell()` says), whose `ExecStart` is fixed.  To ask for
 * the virtual monitor a drop-in is needed, and the recipe — a copy in `user.control`
 * plus `daemon-reload` — is the same v1 uses for `plasma-kwin_wayland`.
 *
 * ⛔ AND HERE IT IS ALWAYS WRITTEN, not «if the compositor is KWin».  The defect
 *    this function cures is v1's `session.c:671`, where the condition
 *    `kind == COMPOSITORE_KWIN &&` short-circuited the call away
 *    and the desktop size was silently lost.  ⚠ The day KWin
 *    returns in V2, what changes is **the unit name and the line**, not
 *    **whether** to write it: the write does not go back behind an `if` on the compositor.
 *
 * Where: `$XDG_RUNTIME_DIR/systemd/user.control/…`, for three reasons:
 *   1. root is not needed — the unit is a USER one;
 *   2. it disappears by itself on reboot, and rewriting it is this function's job
 *      at every birth: that is exactly how the protection lives in the program (I7)
 *      instead of in a file someone must remember to put back;
 *   3. ⛔ the name starts with `zz-` **on purpose**: the drop-ins of all folders
 *      are applied in FILE NAME order, and in `/etc/systemd/user` there is already
 *      one called `remotix-headless.conf`.  `zz-…` comes after, so it
 *      wins — and the win is VERIFIED, not hoped for.
 */
static gboolean write_dropin(uint32_t width, uint32_t height)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autofree char *folder = NULL;
	g_autofree char *fpath = NULL;
	g_autofree char *content = NULL;
	g_autofree char *shell = NULL;
	g_autofree char *expected = NULL;
	g_autofree char *effect = NULL;
	g_autoptr(GError) mistake = NULL;
	/* ⭐ PHASE 12: the unit and the line change, NOT whether to write it — the box above
	 *    asked for it, and the Plasma branch is below, after the folder. */
	const gboolean kde = e_kde();
	g_autofree char *unit = NULL;
	char *reload[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *show_cmd[] = { "systemctl", "--user", "show", "-p", "ExecStart", "--value", NULL, NULL };

	/*
	 * ⛔⛔ PHASE 13 — ON XFCE THIS FUNCTION HAS NO OBJECT, and it is not one branch
	 *     fewer: it is a premise that falls.
	 *
	 * This function exists because on GNOME and on KDE **the compositor is
	 * a systemd user unit** whose `ExecStart` is rewritten — and that is where
	 * the size enters the birth.  On XFCE we launch the compositor
	 * ourselves, there is no unit, and `[M]` 20 Sep 2026 the output is born anyway
	 * `1280x720` hardwired: **the size cannot enter the birth**, by
	 * any road.
	 *
	 * ⚠ And it is SAID, instead of returning `TRUE` silently: a function that
	 *   received a size and did nothing with it, without a line, is the
	 *   way two numbers get lost and nobody notices.
	 */
	/* ⭐ PHASE 14 — on LXQt the same holds, and for the same reason: the
	 *    compositor is the same labwc, launched by us. */
	if (e_xfce() || e_lxqt()) {
		registro_dice(LOG_SESSION,
		              "%s: no drop-in to write — the compositor is not "
		              "a systemd unit, I start it myself.  ⛔ And the requested canvas "
		              "(%ux%u) does NOT enter the birth: on wlroots the output is born "
		              "hardwired and is resized afterwards, with the protocol",
		              desktop_name(), width, height);
		return TRUE;
	}

	if (!runtime || !*runtime) {
		registro_dice(LOG_SESSION,
		              "⛔ XDG_RUNTIME_DIR not set: I do not know where to write the drop-in");
		return FALSE;
	}

	/* ⭐ PHASE 17: on GNOME the unit is chosen from what is installed, and
	 *    THE SAME one is re-read below (`show_cmd`) — never a fixed name on one
	 *    side and the other on the other. */
	unit = kde ? g_strdup(SESSION_UNIT_KWIN) : unit_shell();
	if (!unit)
		return FALSE;
	show_cmd[6] = unit;

	/* ⛔ `<instance>.d/`, never `org.gnome.Shell@.service.d/`: the template's
	 *    folder would also apply to GDM's Shell. */
	{
		g_autofree char *folder_name = g_strconcat(unit, ".d", NULL);

		folder = g_build_filename(runtime, "systemd", "user.control", folder_name,
		                            NULL);
	}
	fpath = g_build_filename(folder, "zz-remotix-monitor.conf", NULL);

	/*
	 * ⭐ PHASE 12 — THE PLASMA LINE, and here the size really ENTERS.
	 *
	 * ⛔ KWin on a seatless machine starts only with the `--virtual` backend
	 *    (`STUDIES.md` §kde §5.2, `[M]` M2: `--drm` exits with status 1), and with that
	 *    backend the output is decided by **the start line**, one and of the given
	 *    size: `stream_virtual_output` answers «Could not find output» to every
	 *    size.  ⇒ GNOME's «zero monitors of its own» design does not exist here —
	 *    the output is born with the session, of the size of the client that makes it
	 *    be born.  `[M]` 18 Sep 2026, rete11-kde: `Virtual-0` 1600x900, a single one.
	 *   · `--xwayland`: mandatory, ksmserver forces xcb (`STUDIES.md` §kde §6.4);
	 *   · `--no-lockscreen`: locking belongs to REMOTIX (§4.3), not to the desktop.
	 */
	if (kde) {
		g_autofree char *wrapper = g_find_program_in_path("kwin_wayland_wrapper");

		if (!wrapper) {
			wrapper = g_strdup("/usr/bin/kwin_wayland_wrapper");
			registro_dice(LOG_SESSION,
			              "⚠ «kwin_wayland_wrapper» is not in PATH: declared "
			              "fallback to %s, and if it is not there the unit will not start",
			              wrapper);
		}
		/*
		 * ⭐⭐ 11 Oct 2026 — KWin NESTED in a screenless labwc (`kwin.h`,
		 *      `DECISIONS.md` §10.40): the line no longer starts KWin, it
		 *      starts THIS binary in `--kwin-nested` mode, which starts labwc
		 *      at W×H and becomes the KWin wrapper with `--wayland-display`.
		 *      ⇒ The desktop is born at W×H as before, and at a reattach of
		 *      another size labwc's output changes and KWin follows it — the
		 *      reason `--virtual` is gone: its output cannot change size.
		 * ⚠ The card is chosen HERE, with the same two questions as XFCE's labwc
		 *   (it opens; it can create a buffer), and KWin draws on the card its
		 *   host announces (`linux-dmabuf` `main_device`).
		 */
		{
			card_pick_how how;
			g_autofree char *story = NULL;
			g_autofree char *node = card_node(&how, &story);
			g_autofree char *self_exe = realpath("/proc/self/exe", NULL);
			const char *node_arg = node ? node : "-";

			if (!node && how == CARD_PICK_NONE_CAPABLE) {
				node_arg = "pixman";
				registro_dice(LOG_SESSION,
				              "⛔ KDE: render nodes open but NO card can create a buffer "
				              "(%s). DECLARED FALLBACK: KWin's host draws in memory", story);
			} else if (!node)
				registro_dice(LOG_SESSION,
				              "⛔ KDE: %s — KWin's host will choose by itself", story);
			else
				card_say("KDE", node, story);
			if (!self_exe) {
				registro_dice(LOG_SESSION,
				              "⛔ I do not know which binary I am (%s): the nested "
				              "KWin line cannot be written", g_strerror(errno));
				return FALSE;
			}
			content = g_strdup_printf("[Service]\n"
			                            "ExecStart=\n"
			                            "ExecStart=%s --kwin-nested %u %u %s -- %s "
			                            "--xwayland --width %u --height %u "
			                            "--no-lockscreen\n",
			                            self_exe, width, height, node_arg, wrapper,
			                            width, height);
		}
		expected = g_strdup_printf("--kwin-nested %u %u", width, height);
		goto write;
	}

	/* ⚠ A fallback, and it is declared (`CODER.md` §4.2): the Shell's path is
	 *   asked of PATH, and only if it is not there do we bet on Debian's. */
	shell = g_find_program_in_path("gnome-shell");
	if (!shell) {
		shell = g_strdup("/usr/bin/gnome-shell");
		registro_dice(LOG_SESSION,
		              "⚠ «gnome-shell» is not in PATH: declared fallback to %s, and if "
		              "it is not there the unit will not start",
		              shell);
	}

	/*
	 * ⚠ `--no-x11` is there and is not removed lightly: it is the line the
	 *   machine measured healthy on 12 August 2026 really had, and changing it
	 *   together with the monitor would mean changing two things at a time.  Whoever
	 *   wants X11 applications inside the session will remove it **on its own**,
	 *   and measure that.
	 */
	/*
	 * ⛔⛔ AND `--virtual-monitor` IS NO LONGER THERE — 14 August 2026, phase 4, A1.
	 *
	 *     Until this morning this line asked for `--virtual-monitor %ux%u`, and
	 *     the session was born with **a monitor of its own**.  ⇒ Then `mutter.c:450`
	 *     captures with `RecordVirtual`, which **mounts a SECOND one**, and records
	 *     that: GNOME leaves bar, dock and windows on the first, puts only
	 *     the wallpaper on the second, and ⛔ **the user looks at an empty screen**.
	 *
	 * ⭐ MEASURED, not deduced — `[M]` 14 August 2026, bench `04-b20`:
	 *    with the previous line, the frame taken by capture is the bare
	 *    Debian wallpaper (bar edge 0.01 against threshold 4; zero text
	 *    edges), and in 40 s **no** frame reaches the client —
	 *    because on a screen where there is nothing, nothing ever changes.
	 *
	 * ⇒ ⭐ THE DESIGN IS: the session **has no monitors of its own**, and the only
	 *      monitor is the one our capture mounts.  It is what
	 *      `mutter.c:376` already declared — *«our `RecordVirtual` mounts
	 *      one of its own»* — and what this line betrayed.
	 *
	 * ⚠ THE PRICE, AND IT IS DECLARED: before the first client the session is
	 *   **black** (zero monitors).  For a **remote-only** session that is fine —
	 *   nobody looks at it — ⛔ but it is not fine for a session that must live
	 *   without anyone capturing it, and that is why `PLAN.md:399` and
	 *   `STUDIES.md` §gnome §108 («`--virtual-monitor` is not optional») must be
	 *   rewritten: see `fasi/rapporti/F4-A1-desktop-vero.md`.
	 *
	 * ⚠ `width` and `height` no longer enter this line: now the
	 *   size is decided by capture's PipeWire negotiation
	 *   (`meta-screen-cast-virtual-stream-src.c:601-606` `[R]`, which creates the
	 *   monitor with `video_format->size`).  They stay in the signature because with
	 *   them what was obtained is CHECKED — see `session_ensure`.
	 */
	/* ⭐ D8: on the GNOME 50 template the MODE is the instance (`--mode=%i` in the
	 *    default file): our line must keep it, or the `ubuntu` session
	 *    would be born with the `user` mode — without dock and without Ubuntu's colours. */
	content = g_strdup_printf("[Service]\n"
	                            "ExecStart=\n"
	                            "ExecStart=%s --headless --no-x11%s\n",
	                            shell,
	                            strcmp(unit, SESSION_UNIT_SHELL_48) != 0 ? " --mode=%i"
	                                                                        : "");
	(void) width;
	(void) height;
	expected = g_strdup_printf("--headless --no-x11");

write:
	g_mkdir_with_parents(folder, 0700);
	if (!g_file_set_contents(fpath, content, -1, &mistake)) {
		registro_dice(LOG_SESSION, "⛔ drop-in not written (%s): %s", fpath,
		              mistake->message);
		return FALSE;
	}

	if (!run(reload))
		return FALSE;

	/*
	 * ⛔ WRITTEN IS NOT IN FORCE — error form E1, «necessary mistaken for
	 *    sufficient».  It is re-read from the manager, and if another drop-in wins we
	 *    stop here instead of discovering it from the black on the user's screen.
	 */
	/*
	 * ⛔⭐ AND THE EXPECTED VALUE CHANGED WITH THE LINE — error form E1, «the check
	 *     is right, the expected value is not».  Until this morning this DEMANDED
	 *     `--virtual-monitor %ux%u`: with the flag removed, this check
	 *     would have failed the cured product.
	 *
	 * ⛔⛔ AND NOW AN ABSENCE IS ALSO LOOKED AT, which is the half that counts.
	 *
	 *     `[M]` 14 August 2026: on this machine `--virtual-monitor` was not asked
	 *     for by the product — it was asked for by
	 *     `/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf`,
	 *     that is a **system** drop-in valid for ANY user.  ⇒ That
	 *     is precisely «a configuration line that can be lost»
	 *     of invariant **I7**, and here it holds in reverse: it is not enough that
	 *     our drop-in is there, it must **win**.  If the manager still says
	 *     `--virtual-monitor`, the session would be born with the defect and we stop
	 *     here instead of discovering it from the user's empty screen.
	 */
	effect = ask(show_cmd);
	if (!effect) {
		registro_dice(LOG_SESSION,
		              "⛔ I could not re-read the ExecStart in force: written is not "
		              "in force, and without re-reading I do not know");
		return FALSE;
	}
	g_strstrip(effect);
	if (!strstr(effect, expected)) {
		registro_dice(LOG_SESSION,
		              "⛔ I wrote «%s» and the manager says something else: another "
		              "drop-in wins over mine.  ExecStart in force: %s",
		              expected, effect);
		return FALSE;
	}
	if (strstr(effect, "--virtual-monitor")) {
		registro_dice(LOG_SESSION,
		              "⛔ the ExecStart in force STILL asks for «--virtual-monitor», and it is not "
		              "me: there is a drop-in that wins over mine (usually "
		              "/etc/systemd/user/%s.d/, which applies to all users).  ⚠ This way "
		              "the session would be born with a monitor of ITS OWN, capture would mount "
		              "a second one, and the user would look at an EMPTY screen.  "
		              "ExecStart in force: %s",
		              unit, effect);
		return FALSE;
	}

	if (kde) {
		registro_dice(LOG_SESSION,
		              "⭐ the Plasma session will be born with ONE output only, %ux%u, and it is "
		              "the PROGRAM that asks for it (%s): KWin nested in a screenless labwc, "
		              "so a reattach of another size can change it.  ExecStart in force: %s",
		              width, height, fpath, effect);
		return TRUE;
	}

	registro_dice(LOG_SESSION,
	              "⭐ the session will be born WITHOUT monitors of its own, and the PROGRAM asks for it "
	              "(%s): the only monitor will be the one our capture mounts, and that is "
	              "where GNOME puts the bar and the dock.  ExecStart in force: %s",
	              fpath, effect);
	return TRUE;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 14 — THE labwc FOLDER FOR LXQt: OURS, and rewritten at every
 *      birth (I7: the protection lives in the program, not in a file that can
 *      be lost or that someone has already written badly).
 *
 * ⛔ WHY NOT `~/.config/labwc`: the upstream script COPIES into it, once
 *    only (`if [ ! -d … ]`), an `autostart` that launches
 *    `swayidle -w timeout 300 "wlopm --off *"` — the output switched off at 5 minutes,
 *    that is capture receiving `failed` (`STUDIES.md` §lxqt §6.2).  And the `rc.xml`
 *    it proposes binds `W-l` to `lxqt-leave --lockscreen` (§5): labwc would eat
 *    the key.  ⇒ A folder we do not write is a folder we do not control.
 * ⭐ With `-C` labwc looks ONLY at this folder (`[R]` labwc 0.8.3
 *    `src/common/dir.c:151-157`): what the user has in `~/.config/labwc` and
 *    in `/etc/xdg/labwc` does not get in.
 *
 * The two files, and why they are so short:
 *   · `rc.xml` — only `<decoration>server</decoration>`, which is what LXQt
 *     ships and what `STUDIES.md` §lxqt §7 says not to touch (a single bar,
 *     no flash).  ⭐ labwc's default shortcuts (`<default/>`,
 *     `[R]` `src/config/rcxml.c:1013`, `include/config/default-bindings.h`),
 *     and among them there is **no** screen lock — `W-l` stays
 *     the user's; ⭐ PHASE 15, D-007: PLUS the shortcut that brings
 *     windows back inside (`SESSION_LABWC_KEYBOARD`).  ⛔ The `<default/>` is
 *     mandatory: with ONE single `<keybind>` labwc no longer loads the
 *     default ones (`rcxml.c:1685-1687`);
 *   · `autostart` — EMPTY on purpose, with the reason written inside:
 *     `lxqt-session` starts its modules by itself from `/etc/xdg/autostart`, and
 *     what LXQt would put there (swayidle, swaybg) either switches the output off or is not
 *     needed.
 *
 * Returns the folder, or NULL (said in the log).
 */
static char *write_config_labwc_lxqt(const char *runtime)
{
	g_autofree char *folder = NULL;
	g_autofree char *rc = NULL;
	g_autofree char *autostart = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!runtime || !*runtime) {
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: XDG_RUNTIME_DIR not set — I do not know where to write "
		              "the labwc configuration");
		return NULL;
	}
	folder = g_build_filename(runtime, "remotix", "labwc-lxqt", NULL);
	rc = g_build_filename(folder, "rc.xml", NULL);
	autostart = g_build_filename(folder, "autostart", NULL);

	if (g_mkdir_with_parents(folder, 0700) != 0 ||
	    !g_file_set_contents(rc,
	                         "<?xml version=\"1.0\"?>\n"
	                         "<!-- REMOTIX: written at every birth of the "
	                         "LXQt session, do not edit.\n"
	                         "     <keyboard>: labwc's default shortcuts "
	                         "(<default/>, without screen lock) plus "
	                         SESSION_LABWC_KEY " (brings windows back inside). -->\n"
	                         "<labwc_config>\n"
	                         "  <core>\n"
	                         "    <decoration>server</decoration>\n"
	                         "  </core>\n"
	                         /* ⭐ PHASE 15, D-007: the default shortcuts
	                          *    (`<default/>`) PLUS ours — see
	                          *    `SESSION_LABWC_KEYBOARD`. */
	                         SESSION_LABWC_KEYBOARD
	                         "</labwc_config>\n",
	                         -1, &mistake) ||
	    !g_file_set_contents(autostart,
	                         "# REMOTIX: written at every birth of the LXQt session, "
	                         "do not edit.\n"
	                         "# EMPTY ON PURPOSE: no swayidle/wlopm (they would switch off "
	                         "the captured\n"
	                         "# output); the modules are started by lxqt-session from "
	                         "/etc/xdg/autostart.\n",
	                         -1, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: labwc configuration NOT written in %s (%s) — I do not "
		              "make the session be born: without OUR folder labwc "
		              "would read the user's, where LXQt's script puts "
		              "swayidle to switch the output off after 5 minutes",
		              folder, mistake ? mistake->message : g_strerror(errno));
		return NULL;
	}
	registro_dice(LOG_SESSION,
	              "⭐ LXQt: labwc configuration in %s — rc.xml without screen "
	              "lock, empty autostart (no swayidle/wlopm)",
	              folder);
	return g_steal_pointer(&folder);
}

/*
 * ⭐⭐ PHASE 14, increment 3 — THE LXQt WALLPAPER IS BORN AT THE CLIENT'S SIZE.
 *
 * `[M]` 24 Sep 2026: headless `labwc` is born with `HEADLESS-1 1280x720`, and the
 * client's size is given to it by `wlr_ask_size()` (capture.c) ~200 ms later;
 * but `pcmanfm-qt --desktop` starts ~160 ms after labwc ⇒ RACE: ~1 birth in 13
 * the wallpaper stays 1280x720 and the rest of the screen is BLACK.
 * `[R]` pcmanfm-qt 2.1.0: the desktop window is anchored to all four sides
 * (`desktopwindow.cpp:202-212`), the wallpaper is made from `screen->size()` (`:705`)
 * and is redone ONLY on `resizeEvent` (`:490`; `application.cpp:1050`) ⇒ if the
 * size arrives in the wrong gap, nobody redraws it.
 *
 * ⭐ The cure: `lxqt-session` (and so pcmanfm-qt) is born AFTER the output has
 *    the size.  labwc's primary client (`-S`) becomes an `sh` that first
 *    calls `wlr-randr --custom-mode` and then does `exec lxqt-session` — same
 *    pid, so «primary dead, labwc exits» stays true.
 * ⛔ `;` and NOT `&&`: if `wlr-randr` fails the session is born anyway, and
 *    the usual late request remains (`wlr_ask_size()`, unchanged).
 * ⭐ The output name is NOT assumed: `wlr-randr` 0.4.1 WANTS `--output`
 *    to change a mode (`[R]` wlr-randr(1): «This option must be set when
 *    making changes»), and without arguments it lists the outputs with the name as
 *    first word of the first line (`HEADLESS-1 "Headless output 1"`).  ⇒ That one is
 *    taken; if it is empty, no `wlr-randr`.
 * ⚠ Size 0 (unknown) ⇒ today's line, without `sh` in front.
 *
 * ⭐⭐ 5 October 2026 — THE SAME RACE ON XFCE, and the same cure.
 * `[M]` NVIDIA (labwc 0.9.3, xfce4-panel 4.20.7, gtk-layer-shell 0.10.0):
 * if `xfce4-panel` is born on the 1280x720 output and the size arrives later, the
 * bottom panel (centred) stays in a loop — it redraws itself at EVERY
 * frame, alternating the position for 1280 (x=487) and the one for the real
 * canvas.  With requested damage (`wlroots.c`) the compositor then answers at
 * 60/s on a still desktop: the client decodes 60 4K frames per
 * second for nothing, and on slow hardware it falls seconds behind (F-003
 * red on Firefox).  `[M]` With the panel restarted, the loop disappears and F-003
 * turns green again; resizing an ALREADY born session, the loop does not arise.
 * ⇒ It is the birth race, as for pcmanfm-qt: `xfce4-session` is born
 *   after `wlr-randr`.
 * ⚠ Two levels of quoting: our `sh -c` (the one of `start()`) and
 *   labwc's `g_shell_parse_argv()` on `-S`.  ⇒ `g_shell_quote()` twice,
 *   and no hand-written quoting.
 */
static char *measured_primary(const char *desktop, const char *primary, uint32_t width,
                               uint32_t height)
{
	g_autofree char *script = NULL;
	g_autofree char *internal = NULL;

	if (width == 0 || height == 0) {
		registro_dice(LOG_SESSION,
		              "⚠ %s: client size unknown (%ux%u) — %s is born WITHOUT the "
		              "size given first; the late request remains",
		              desktop, width, height, primary);
		return g_strdup(primary);
	}
	script = g_strdup_printf(
		"u=$(wlr-randr 2>/dev/null | sed -n '1s/ .*//p'); "
		"if [ -n \"$u\" ]; then "
		"echo \"remotix: output $u set to %ux%u BEFORE %s\"; "
		"wlr-randr --output \"$u\" --custom-mode %ux%u; "
		"else echo \"remotix: no output from wlr-randr, %s is born "
		"without the size\"; fi; "
		"exec %s",
		width, height, primary, width, height, primary, primary);
	internal = g_shell_quote(script);
	registro_dice(LOG_SESSION,
	              "⭐ %s: the client size %ux%u is given to the output BEFORE the "
	              "birth of %s (wlr-randr in labwc's primary client)",
	              desktop, width, height, primary);
	return g_strdup_printf("sh -c %s", internal);
}

/*
 * ⭐ PHASE 17 — WHERE THE SESSION LOG GOES (`phases/17-the-installer.md` §4.4).
 *
 * ⛔ It was in `/tmp/remotix-sessione-<uid>.log`: a PREDICTABLE name in a
 *    folder shared by all.  Another user could create it first — and with
 *    `fs.protected_regular` (on in Debian, Fedora, Arch) the shell's `exec >>`
 *    onto someone else's file in `/tmp` fails: the desktop did not start.  Or
 *    worse, if the file was a link, we wrote where it said.
 *
 * ⇒ `$XDG_STATE_HOME/remotix/session.log` (usually
 *   `~/.local/state/remotix/`): it belongs to the user, and like `/tmp` it survives the
 *   user manager — which is the reason why it is NOT in `XDG_RUNTIME_DIR`
 *   (box of 16 August 2026 in `start()`).
 *
 * Created safely, and it is VERIFIED instead of hoped for:
 *   · the folder 0700, and it must be a REAL folder (not a link),
 *     OURS and not writable by others;
 *   · the file opened here with `O_NOFOLLOW`, 0600, and it must be a regular file
 *     of OURS — then the shell appends to it.
 *
 * ⚠ If it cannot be done (read-only home, someone else's folder): DECLARED
 *   fallback to `XDG_RUNTIME_DIR`, which is ours but dies with the session —
 *   a log that gets lost is worth more than a desktop that does not start
 *   (`CODER.md` §4.2).  NULL only if not even that exists.
 */
static gboolean is_our_dir(const char *folder)
{
	struct stat st;

	if (g_mkdir_with_parents(folder, 0700) != 0 || lstat(folder, &st) != 0)
		return FALSE;
	return S_ISDIR(st.st_mode) && st.st_uid == getuid() && (st.st_mode & 022) == 0;
}

static gboolean our_file(const char *fpath)
{
	struct stat st;
	int fd = open(fpath, O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW | O_CLOEXEC, 0600);
	gboolean all_ok;

	if (fd < 0)
		return FALSE;
	all_ok = fstat(fd, &st) == 0 && S_ISREG(st.st_mode) && st.st_uid == getuid();
	close(fd);
	return all_ok;
}

static char *log_session_path(void)
{
	g_autofree char *folder = g_build_filename(g_get_user_state_dir(), "remotix", NULL);
	g_autofree char *fpath = g_build_filename(folder, "session.log", NULL);
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (is_our_dir(folder) && our_file(fpath))
		return g_steal_pointer(&fpath);

	if (runtime && *runtime) {
		g_autofree char *fallback = g_build_filename(runtime, "remotix-session.log", NULL);

		if (our_file(fallback)) {
			registro_dice(LOG_SESSION,
			              "⚠ I cannot write the session log in %s "
			              "(folder or file not mine, or not creatable): DECLARED fallback "
			              "to %s, which however disappears with the session",
			              fpath, fallback);
			return g_steal_pointer(&fallback);
		}
	}
	registro_dice(LOG_SESSION,
	              "⛔ no safe place for the session log (neither %s nor "
	              "XDG_RUNTIME_DIR): the session starts WITHOUT a log",
	              fpath);
	return NULL;
}

/* ⭐ `width`/`height`: the client's canvas.  ⚠ The LXQt and
 *   XFCE branches use them (`measured_primary()`): GNOME and KDE take the size from the
 *   drop-in — identical to before. */
static gboolean start(uint32_t width, uint32_t height)
{
	g_auto(GStrv) environment = NULL;
	g_autofree char *log = NULL;
	g_autofree char *line = NULL;
	g_autoptr(GError) mistake = NULL;
	/* `setsid --fork` detaches the session from our process group: if
	 * REMOTIX is restarted, the user's desktop does not notice. */
	char *argv[] = { "setsid", "--fork", "sh", "-c", NULL, NULL };
	int state = 0;
	/* ⚠ THREE-WAY, and not a nested ternary: whoever adds the fourth desktop
	 *   must see the list, not have to untangle it. */
	const char *command = gnome_session()->line; /* D8 */
	/* ⭐ PHASE 14 — the LXQt line is composed (the `-C` folder is under
	 *    `XDG_RUNTIME_DIR`): it lives here, and `command` points to it. */
	g_autofree char *lxqt_command = NULL;
	g_autofree char *xfce_command = NULL;

	if (e_kde())
		command = SESSION_COMMAND_KDE;
	else if (e_xfce()) {
		/* ⭐ 5 Oct 2026: the size BEFORE xfce4-session (`measured_primary()`) */
		g_autofree char *primary =
			measured_primary("XFCE", SESSION_PRIMARY_XFCE, width, height);
		g_autofree char *cited_primary = g_shell_quote(primary);

		xfce_command = g_strdup_printf("exec " SESSION_HEAD_XFCE " %s", cited_primary);
		command = xfce_command;
	}
	else if (e_lxqt()) {
		g_autofree char *folder = write_config_labwc_lxqt(g_getenv("XDG_RUNTIME_DIR"));

		if (!folder)
			return FALSE;
		/* ⚠ `SESSION_PROCESS_XFCE` is `labwc`: the FAMILY compositor,
		 *   the same executable — the constant's name is from phase 13. */
		g_autofree char *primary =
			measured_primary("LXQt", SESSION_PRIMARY_LXQT, width, height);
		g_autofree char *cited_primary = g_shell_quote(primary);

		lxqt_command = g_strdup_printf("exec " SESSION_PROCESS_XFCE " -C '%s' -S %s",
		                               folder, cited_primary);
		command = lxqt_command;
	}

	environment = compose_environment();
	if (!environment)
		return FALSE;

	/*
	 * ⛔⭐ THE SESSION LOG CANNOT LIVE IN `XDG_RUNTIME_DIR` — 16
	 *     August 2026, and the reason is that that folder **dies with the
	 *     session**: when the user manager shuts down, logind takes it away.
	 *
	 * ⇒ The case in which that log is needed most — *«the session started and
	 *   died at once, why?»* — is exactly the case in which it is no longer
	 *   there.  `[M]` Looking for it after a failed start one found an empty file or
	 *   no file.
	 *
	 * ⭐ PHASE 17: no longer in `/tmp` — see `log_session_path()`.
	 */
	log = log_session_path();
	if (log) {
		g_autofree char *cited = g_shell_quote(log);

		line = g_strdup_printf("exec >>%s 2>&1; %s", cited, command);
	} else {
		line = g_strdup_printf("exec >/dev/null 2>&1; %s", command);
	}
	argv[4] = line;

	registro_dice(LOG_SESSION, "starting the graphical session: %s (its log goes to %s)",
	              command, log ? log : "nowhere");
	if (!g_spawn_sync(g_get_home_dir(), argv, environment, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL,
	                  NULL, &state, &mistake) ||
	    !g_spawn_check_wait_status(state, &mistake)) {
		registro_dice(LOG_SESSION, "⛔ the session did not start: %s",
		              mistake ? mistake->message : "no reason given");
		return FALSE;
	}
	return TRUE;
}

/* `org.gnome.SessionManager.Logout`: 0 asks for confirmation, 1 does not, 2 forces. */
static gboolean exit_gnome(guint32 mode)
{
	g_autoptr(GDBusConnection) bus = sess_bus(NULL);
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!bus)
		return FALSE;
	response = g_dbus_connection_call_sync(
		bus, "org.gnome.SessionManager", "/org/gnome/SessionManager",
		"org.gnome.SessionManager", "Logout", g_variant_new("(u)", mode), NULL,
		G_DBUS_CALL_FLAGS_NONE, WAIT_RESPONSE_MS, NULL, &mistake);
	if (!response)
		registro_dice(LOG_SESSION, "⛔ Logout(%u) did not go through: %s", mode,
		              mistake ? mistake->message : "no reason given");
	return response != NULL;
}

/*
 * ⛔ «Inactive» and not «no longer active»: `is-active` goes through `deactivating`, and
 *    restarting in there is another first run (`PHASES.md` §00-ambiente,
 *    defect 4 of phase 0).  And TWO things are looked at — the unit and the process —
 *    because `Logout` may leave the manager alive.
 */
static gboolean unit_stopped(const char *unit)
{
	char *argv[] = { "systemctl", "--user", "is-active", (char *)unit, NULL };
	g_autofree char *state = ask(argv);

	if (!state)
		return FALSE;
	g_strstrip(state);
	return g_strcmp0(state, "inactive") == 0 || g_strcmp0(state, "failed") == 0 ||
	       g_strcmp0(state, "unknown") == 0;
}

static gboolean inactive_unit(void)
{
	/*
	 * ⛔⭐⭐ TWO UNITS, NOT ONE — 16 August 2026, and the second was named by the
	 *      user's journal after half a day of hypotheses:
	 *
	 *        «Started gnome-session-restart-dbus.service —
	 *         **Restart DBus after GNOME Session shutdown**»
	 *
	 * ⇒ When a GNOME session ends, GNOME **restarts the session bus**.
	 *   A new session started in that window is born on a bus that is about to
	 *   be replaced, and dies without writing a line: `[M]` its log
	 *   stayed **empty, zero bytes**, and that is why the cause
	 *   cost so much — the defect erased its own traces.
	 *
	 * ⚠ It is the same shape as `gnome_session()->handler` below — «inactive» and
	 *   not «no longer active» — applied to a second piece nobody had
	 *   looked at because nobody knew it existed.
	 */
	/* ⭐ PHASE 12 — on Plasma the two units are the compositor and the session
	 *    target.  ⛔ And it is already needed at BIRTH, not only at exit: it is the
	 *    guard against a second Plasma when KWin takes longer than the child's
	 *    leash to show up on the bus. */
	if (e_kde())
		return unit_stopped(SESSION_UNIT_KWIN) && unit_stopped(SESSION_UNIT_PLASMA);

	/*
	 * ⛔⛔ PHASE 13 — ON XFCE THIS GUARD WOULD NOT FAIL: IT WOULD VANISH.
	 *
	 * `[M]` 20 Sep 2026, inside `rete11-xfce`: `systemctl --user is-active` on
	 * a unit **that does not exist** answers **`inactive`**, code 4.  And
	 * `unit_stopped()` above accepts `inactive` ⇒ on XFCE, where there is no unit
	 * at all, the question would answer **yes always**: the protection
	 * against a second session — paid for on 16 August 2026 — would not give a
	 * red, would not give a line, it would simply no longer be there.
	 *
	 * ⇒ A FACT is looked at, and two are needed because neither is enough:
	 *   the name on the bus may already have vanished while the compositor is still
	 *   dying, and a `labwc` may exist an instant before taking the name.
	 */
	/* ⭐ PHASE 14 — on LXQt the fact is the same process, `labwc`: there is no
	 *    unit, and the `inactive` trap for a non-existent unit is identical.
	 * ⚠ Just one thing: a `labwc` of mine counts even if it belongs to another desktop —
	 *   but «one desktop per machine» (§0.6) rules that out. */
	if (e_xfce() || e_lxqt()) {
		int amount = my_processes(SESSION_PROCESS_XFCE);

		if (amount < 0) {
			/* ⛔ «I could not look» is not «it is free»: the answer is no,
			 *    and the caller retries. */
			registro_dice(LOG_SESSION,
			              "⛔ %s: I cannot read /proc, so I do not know whether "
			              "there is still a " SESSION_PROCESS_XFCE " of mine — and «I don't "
			              "know» here counts as «no»",
			              desktop_name());
			return FALSE;
		}
		if (amount > 0) {
			registro_dice(LOG_SESSION,
			              "%s: there are still %d " SESSION_PROCESS_XFCE
			              " of mine: the previous session has not ended",
			              desktop_name(), amount);
			return FALSE;
		}
		return TRUE;
	}

	/* ⭐ PHASE 17 — on GNOME 50 these two units still have these names
	 *    (`[R]` gnome-session 50.0: `data/gnome-session-manager@.service.in`,
	 *    `data/gnome-session-restart-dbus.service.in`); only the Shell's
	 *    changed name (`unit_shell()`), which is not looked at here.
	 * ⚠ If one day they changed, `is-active` would answer «inactive» for a
	 *   name that does not exist, and the guard would vanish as on XFCE: to be
	 *   re-checked at every new GNOME (`phases/17-the-installer.md` §5.1). */
	return unit_stopped(gnome_session()->handler) && unit_stopped(SESSION_UNIT_DBUS);
}

static gboolean wait_until_done(void)
{
	gint64 expiry = g_get_monotonic_time() + (gint64) WAIT_EXIT_MS * 1000;

	while (g_get_monotonic_time() < expiry) {
		g_usleep(CHECK_INTERVAL_MS * 1000);
		if (!session_alive() && inactive_unit()) {
			char *clean[] = { "systemctl", "--user", "reset-failed", NULL };

			run(clean);
			return TRUE;
		}
	}
	return FALSE;
}

/*
 * ⭐ PHASE 12 — the Plasma exit, brought over from v1 (`fondamenta/remotix-c/src/sessione.c`
 * 725-770) and measured there on 8 August 2026 (`STUDIES.md` §kde §6.5, M9).
 *
 *   orderly    `org.kde.Shutdown.logout()` — ⛔ not `LogoutPrompt`, which asks
 *              for a confirmation nobody gives in an unattended session
 *   forced     `StopUnit("plasma-workspace.target", "fail")` — ⛔ `Logout(2)`
 *              does not exist on KDE; it is what `plasma-shutdown` does at the end
 */
static gboolean exit_kde(gboolean a_force)
{
	g_autoptr(GDBusConnection) bus = sess_bus(NULL);
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!bus)
		return FALSE;
	if (a_force)
		response = g_dbus_connection_call_sync(
			bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
			"org.freedesktop.systemd1.Manager", "StopUnit",
			g_variant_new("(ss)", SESSION_UNIT_PLASMA, "fail"), NULL,
			G_DBUS_CALL_FLAGS_NONE, WAIT_RESPONSE_MS, NULL, &mistake);
	else
		response = g_dbus_connection_call_sync(
			bus, "org.kde.Shutdown", "/Shutdown", "org.kde.Shutdown", "logout", NULL,
			NULL, G_DBUS_CALL_FLAGS_NONE, WAIT_RESPONSE_MS, NULL, &mistake);
	if (!response)
		registro_dice(LOG_SESSION, "⛔ the Plasma exit (%s) did not go through: %s",
		              a_force ? "forced StopUnit" : "Shutdown.logout",
		              mistake ? mistake->message : "no reason given");
	return response != NULL;
}

/*
 * ⭐ PHASE 13 — THE XFCE EXIT.  Two moves, and the second is not `StopUnit`.
 *
 * ⛔ On GNOME and on KDE the force is systemd, which stops a unit.  Here there is
 *    no unit: the force is a signal to the compositor process.
 * ⭐ And that is enough, because the start line carries `--session`: `xfce4-session`
 *   is labwc's primary client ⇒ labwc dead, the session goes with it, and
 *   `xfce4-session` dead, labwc exits by itself.  `[M]` 20 Sep 2026, tried inside
 *   `rete11-xfce`: with `labwc` killed, nothing was left of `xfce4-session`, of the panel
 *   or of the desktop.
 * ⚠ The name on the bus is `org.xfce.SessionManager`, the interface is
 *   `org.xfce.Session.Manager` — with one more dot.  Confusing them gives
 *   «unknown method», which looks like «the session does not answer».
 */
static gboolean exit_xfce(void)
{
	g_autoptr(GDBusConnection) bus = sess_bus(NULL);
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!bus)
		return FALSE;
	/* (show_dialog, allow_save) — both false: nobody can answer a
	 * dialog inside a remote session we are closing. */
	response = g_dbus_connection_call_sync(
		bus, SESSION_BUS_XFCE, "/org/xfce/SessionManager",
		"org.xfce.Session.Manager", "Logout", g_variant_new("(bb)", FALSE, FALSE),
		NULL, G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_RESPONSE_MS, NULL, &mistake);
	if (!response) {
		registro_dice(LOG_SESSION,
		              "⚠ XFCE: Logout did not go through (%s)",
		              mistake ? mistake->message : "no reason given");
		return FALSE;
	}
	return TRUE;
}

static gboolean kill_xfce(void)
{
	g_autoptr(GDir) proc = g_dir_open("/proc", 0, NULL);
	const char *entry;
	uid_t my = getuid();
	int hit = 0;

	if (!proc)
		return FALSE;
	while ((entry = g_dir_read_name(proc))) {
		g_autofree char *comm = NULL;
		g_autofree char *fpath = NULL;
		GStatBuf st;

		if (!g_ascii_isdigit(entry[0]))
			continue;
		fpath = g_build_filename("/proc", entry, "comm", NULL);
		if (g_stat(fpath, &st) != 0 || st.st_uid != my)
			continue;
		if (!g_file_get_contents(fpath, &comm, NULL, NULL))
			continue;
		g_strstrip(comm);
		if (g_strcmp0(comm, SESSION_PROCESS_XFCE) != 0)
			continue;
		/* ⚠ SIGTERM, not SIGKILL: labwc closes its clients, and a SIGKILL
		 *   would leave behind exactly what C7 goes looking for. */
		if (kill((pid_t) g_ascii_strtoll(entry, NULL, 10), SIGTERM) == 0)
			hit++;
	}
	registro_dice(LOG_SESSION,
	              "%s: sent SIGTERM to %d " SESSION_PROCESS_XFCE " of mine", desktop_name(),
	              hit);
	return hit > 0;
}

/*
 * ⭐ PHASE 14 — THE LXQt EXIT.  The same two moves as XFCE, with another
 *    D-Bus target for the first (`STUDIES.md` §lxqt §3.4).
 *
 *   orderly    `org.lxqt.session.logout()` on `/LXQtSession` — ⛔ never
 *              `lxqt-leave --logout`, which opens a modal confirmation.
 *              ✅ LXQt's logout does not consult inhibitors, shows nothing,
 *              cannot be cancelled (`STUDIES.md` §lxqt §3.3, `[✗]`)
 *   forced     SIGTERM to labwc (`kill_xfce`): with `-S` `lxqt-session` is the
 *              primary client, and with labwc dead it goes away with it
 *
 * ⛔⛔ AND IT IS SENT WITHOUT WAITING FOR AN ANSWER, because no answer arrives:
 *     `logout()` is `Q_NOREPLY` (`[R]` lxqt-session 2.1.1
 *     `sessiondbusadaptor.h`).  A synchronous call would hang up to
 *     the ceiling and say «did not go through» to a successful logout — form E8
 *     reversed.  ⇒ A message with `NO_REPLY_EXPECTED`, and the verdict is given by
 *     `wait_until_done()`, that is a fact.
 * [?] Whether `logout()` really brings `lxqt-session` to exit (and so labwc)
 *     within the 10 s of `WAIT_EXIT_MS` is to be measured: if not we fall into
 *     the force, and the log says so.
 */
static gboolean exit_lxqt(void)
{
	g_autoptr(GDBusConnection) bus = sess_bus(NULL);
	g_autoptr(GDBusMessage) message = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!bus)
		return FALSE;
	message = g_dbus_message_new_method_call(SESSION_BUS_LXQT, "/LXQtSession",
	                                           SESSION_BUS_LXQT, "logout");
	g_dbus_message_set_flags(message, G_DBUS_MESSAGE_FLAGS_NO_REPLY_EXPECTED |
	                                            G_DBUS_MESSAGE_FLAGS_NO_AUTO_START);
	if (!g_dbus_connection_send_message(bus, message, G_DBUS_SEND_MESSAGE_FLAGS_NONE, NULL,
	                                    &mistake) ||
	    !g_dbus_connection_flush_sync(bus, NULL, &mistake)) {
		registro_dice(LOG_SESSION, "⚠ LXQt: logout() did not leave (%s)",
		              mistake ? mistake->message : "no reason given");
		return FALSE;
	}
	return TRUE;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 15, D-015/D-017 (R1, R2) — AFTER THE REMOTE SESSION, THE USER
 *      MANAGER GOES BACK TO HOW IT WAS.
 *
 * ⛔ THE HOLE, found by the clean-up review: what the product
 *    puts into systemd's USER MANAGER never went away —
 *    · the drop-ins in `$XDG_RUNTIME_DIR/systemd/user.control/` (the Shell
 *      `--headless`, KWin `--virtual`, `xfconfd` with the session's
 *      folder);
 *    · the variables that `gnome-session`/`startplasma`/labwc export into the
 *      manager from the environment we compose (`DCONF_PROFILE`,
 *      `XDG_CONFIG_DIRS`, `XCURSOR_THEME`=the invisible theme, …).
 *    And with linger on (`provision.sh`) the manager outlives the
 *    session: the user who then logs in AT THE MONITOR inherited everything — on XFCE a
 *    «Log Out» that does not log out (`WaylandLogoutCommand=/bin/true` locked), on GNOME
 *    the in-memory dconf in place of theirs.
 *
 * ⭐ THE CURE, in two gestures:
 *   · `session_snapshot_handler()`, at birth and BEFORE touching
 *     anything: the previous value of each of OUR variables
 *     (`OUR_VARIABLES`) is written in `$XDG_RUNTIME_DIR/remotix/
 *     manager-before` (it exists as long as the manager exists);
 *   · `session_clear_out_handler()`, when the remote session has ended (end
 *     seen by the child, `session_terminate`, the child's exit) and also
 *     at the child's start and at birth (for what a crash left behind):
 *     our drop-ins removed + `daemon-reload`; our variables put back as
 *     they were (or removed, if they were not there) with `UnsetAndSetEnvironment`; and
 *     `xfconfd` restarted if it had the session's folder.
 *   ⛔ ONLY with the session DEAD: with the session alive it would pull the
 *      ground out from under a working desktop.
 *   ⚠ Without the snapshot (a manager born with an earlier product) only the
 *     variables bearing our mark (`remotix` in the value) are removed:
 *     it is said, and it is the fallback.
 *
 * ⚠ What remains, declared: if the child never comes back (the machine stays
 *   without a client and the user logs in at the monitor after a crash of the child), the
 *   clear-out will be done by the next child: the server, as root, does not talk to the
 *   user manager.
 */
static const char *const OUR_VARIABLES[] = {
	"DCONF_PROFILE", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS", "XDG_MENU_PREFIX",
	"XCURSOR_THEME", "XCURSOR_SIZE", "XCURSOR_PATH", "XDG_CURRENT_DESKTOP",
	"XDG_SESSION_DESKTOP", "XDG_SESSION_TYPE", "SHELL", "LANG", "PATH",
	"QT_QPA_PLATFORM", "QT_QPA_PLATFORMTHEME", "GDK_BACKEND", "XFCE4_SESSION_COMPOSITOR",
	"WLR_BACKENDS", "WLR_LIBINPUT_NO_DEVICES", "WLR_RENDER_DRM_DEVICE",
	"LABWC_UPDATE_ACTIVATION_ENV", "WAYLAND_DISPLAY", "DISPLAY",
	/* ⭐ D8: it is set by a session's `Exec` (`env GNOME_SHELL_SESSION_MODE=…`),
	 *    and gnome-session exports it to the manager like its whole environment. */
	"GNOME_SHELL_SESSION_MODE", NULL
};

/* { drop-in folder, name } — all of ours and only ours */
static const char *const OUR_DROPINS[][2] = {
	/* ⭐ PHASE 17: the Shell instances (`@wayland`, `@user`, `@ubuntu`…)
	 *    are not here: `session_clear_out_handler()` looks for them in the folder,
	 *    because with D8 the name depends on the session (§5.1). */
	{ SESSION_UNIT_KWIN ".d", "zz-remotix-monitor.conf" },
	{ "xfconfd.service.d", "zz-remotix-session.conf" },
};

static char *manager_before_path(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "manager-before", NULL)
	                           : NULL;
}

/* The manager's environment, {name: value}, asked of it (property
 * `Environment` of `org.freedesktop.systemd1.Manager`: raw strings, without
 * the quotes of `show-environment`).  NULL if it does not answer. */
static GHashTable *handler_environment(GDBusConnection *bus)
{
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariant) inside = NULL;
	g_autofree const char **entries = NULL;
	GHashTable *env;

	response = g_dbus_connection_call_sync(
		bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
		"org.freedesktop.DBus.Properties", "Get",
		g_variant_new("(ss)", "org.freedesktop.systemd1.Manager", "Environment"),
		G_VARIANT_TYPE("(v)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, NULL);
	if (!response)
		return NULL;
	g_variant_get(response, "(v)", &inside);
	if (!g_variant_is_of_type(inside, G_VARIANT_TYPE_STRING_ARRAY))
		return NULL;
	env = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, g_free);
	entries = g_variant_get_strv(inside, NULL);
	for (int i = 0; entries[i]; i++) {
		const char *eq_sign = strchr(entries[i], '=');

		if (eq_sign)
			g_hash_table_insert(env, g_strndup(entries[i], eq_sign - entries[i]),
			                    g_strdup(eq_sign + 1));
	}
	return env;
}

void session_snapshot_handler(void)
{
	g_autoptr(GDBusConnection) bus = sess_bus(NULL);
	g_autoptr(GHashTable) env = NULL;
	g_autoptr(GKeyFile) photo = g_key_file_new();
	g_autofree char *fpath = manager_before_path();
	g_autofree char *folder = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!bus || !fpath || !(env = handler_environment(bus))) {
		registro_dice(LOG_SESSION,
		              "⚠ R1/R2: I could not snapshot the user manager's environment — "
		              "at the end of the session I will remove only the variables bearing our mark");
		return;
	}
	for (int i = 0; OUR_VARIABLES[i]; i++) {
		const char *v = g_hash_table_lookup(env, OUR_VARIABLES[i]);

		if (v)
			g_key_file_set_string(photo, "prima", OUR_VARIABLES[i], v);
		else
			g_key_file_set_boolean(photo, "assenti", OUR_VARIABLES[i], TRUE);
	}
	folder = g_path_get_dirname(fpath);
	if (g_mkdir_with_parents(folder, 0700) != 0 ||
	    !g_key_file_save_to_file(photo, fpath, &mistake))
		registro_dice(LOG_SESSION, "⚠ R1/R2: manager snapshot NOT written (%s): %s",
		              fpath, mistake ? mistake->message : g_strerror(errno));
	else
		registro_dice(LOG_SESSION,
		              "⭐ R1/R2: snapshot taken of the user manager's environment BEFORE the "
		              "session (%s): at the end I put it back as it was",
		              fpath);
}

void session_clear_out_handler(const char *why)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GHashTable) env = NULL;
	g_autoptr(GKeyFile) photo = g_key_file_new();
	g_autofree char *fpath = manager_before_path();
	g_autoptr(GPtrArray) remove = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GPtrArray) put = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GString) said = g_string_new(NULL);
	gboolean with_photo;
	int drop = 0;
	gboolean xfconfd = FALSE;
	char *reload[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *restart[] = { "systemctl", "--user", "try-restart", "xfconfd.service", NULL };

	if (!runtime || !*runtime)
		return;
	if (session_alive()) {
		log_detail(LOG_SESSION,
		                   "R1/R2 (%s): the session is ALIVE — I do not clear out the user "
		                   "manager under a working desktop",
		                   why);
		return;
	}

	/* 1. the drop-ins: all of ours and only ours */
	for (guint i = 0; i < G_N_ELEMENTS(OUR_DROPINS); i++) {
		g_autofree char *folder = g_build_filename(runtime, "systemd", "user.control",
		                                             OUR_DROPINS[i][0], NULL);
		g_autofree char *file = g_build_filename(folder, OUR_DROPINS[i][1], NULL);

		if (g_unlink(file) == 0) {
			drop++;
			xfconfd |= g_str_has_prefix(OUR_DROPINS[i][0], "xfconfd");
			g_string_append_printf(said, " %s/%s", OUR_DROPINS[i][0],
			                       OUR_DROPINS[i][1]);
			g_rmdir(folder); /* only if empty */
		}
	}
	/* ⭐ D8: the Shell instances, whatever their name (`@wayland`, `@user`,
	 *    `@ubuntu`…) — ⛔ never the template's folder, `org.gnome.Shell@.service.d`,
	 *    where we do not write and which also applies to GDM. */
	{
		g_autofree char *check = g_build_filename(runtime, "systemd", "user.control",
		                                              NULL);
		g_autoptr(GDir) d = g_dir_open(check, 0, NULL);
		const char *f;

		while (d && (f = g_dir_read_name(d))) {
			g_autofree char *folder = NULL;
			g_autofree char *file = NULL;

			if (!g_str_has_prefix(f, "org.gnome.Shell@") ||
			    !g_str_has_suffix(f, ".service.d") ||
			    strcmp(f, SESSION_UNIT_SHELL_MODEL ".d") == 0)
				continue;
			folder = g_build_filename(check, f, NULL);
			file = g_build_filename(folder, "zz-remotix-monitor.conf", NULL);
			if (g_unlink(file) == 0) {
				drop++;
				g_string_append_printf(said, " %s/zz-remotix-monitor.conf", f);
				g_rmdir(folder); /* only if empty */
			}
		}
	}
	if (drop)
		run(reload);
	if (xfconfd)
		run(restart);

	/* 2. the variables: as they were, or only those with our mark without a snapshot */
	bus = sess_bus(NULL);
	env = bus ? handler_environment(bus) : NULL;
	with_photo = fpath && g_key_file_load_from_file(photo, fpath, G_KEY_FILE_NONE, NULL);
	for (int i = 0; env && OUR_VARIABLES[i]; i++) {
		const char *name = OUR_VARIABLES[i];
		const char *now = g_hash_table_lookup(env, name);
		g_autofree char *prima = with_photo ? g_key_file_get_string(photo, "prima", name, NULL)
		                                  : NULL;
		gboolean was_absent = with_photo && g_key_file_get_boolean(photo, "assenti", name, NULL);

		if (with_photo) {
			if (prima && g_strcmp0(prima, now) != 0)
				g_ptr_array_add(put, g_strdup_printf("%s=%s", name, prima));
			else if (was_absent && now)
				g_ptr_array_add(remove, g_strdup(name));
		} else if (now && strstr(now, "remotix")) {
			g_ptr_array_add(remove, g_strdup(name));
		}
	}
	if (remove->len || put->len) {
		g_autoptr(GVariant) r = NULL;
		g_autoptr(GError) mistake = NULL;

		g_ptr_array_add(remove, NULL);
		g_ptr_array_add(put, NULL);
		r = g_dbus_connection_call_sync(
			bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
			"org.freedesktop.systemd1.Manager", "UnsetAndSetEnvironment",
			g_variant_new("(^as^as)", (char **) remove->pdata, (char **) put->pdata),
			NULL, G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &mistake);
		if (r) {
			for (guint i = 0; i + 1 < remove->len; i++)
				g_string_append_printf(said, " -%s", (char *) g_ptr_array_index(remove, i));
			for (guint i = 0; i + 1 < put->len; i++) {
				const char *m = g_ptr_array_index(put, i);

				g_string_append_printf(said, " ~%.*s", (int) (strchr(m, '=') - m), m);
			}
		} else {
			registro_dice(LOG_SESSION,
			              "⛔ R1/R2 (%s): the user manager's variables are NOT "
			              "restored (%s) — the user at the monitor would inherit ours",
			              why, mistake ? mistake->message : "no reason given");
		}
	}
	if (with_photo && env)
		g_unlink(fpath); /* consumed: the next birth makes another one */

	if (said->len)
		registro_dice(LOG_SESSION,
		              "⭐ R1/R2 (%s): the user manager goes back to how it was —%s%s%s",
		              why, said->str, xfconfd ? " · xfconfd restarted" : "",
		              with_photo ? "" : " (⚠ without a snapshot: removed only the variables bearing "
		                              "our mark)");
	else
		log_detail(LOG_SESSION,
		                   "R1/R2 (%s): there was nothing of ours in the user manager",
		                   why);
}

static bool really_terminate(void);

/*
 * The pids of the cgroup this process runs in (logind's `session-N.scope`),
 * ours included.  NULL if the cgroup cannot be read.
 */
static GArray *my_scope_pid(void)
{
	g_autofree char *my = NULL;
	g_autofree char *procs = NULL;
	g_autofree char *text = NULL;
	g_auto(GStrv) lines = NULL;
	GArray *pid;
	const char *via;

	if (!g_file_get_contents("/proc/self/cgroup", &my, NULL, NULL))
		return NULL;
	via = strstr(my, "0::");
	if (!via)
		return NULL;
	via += 3;
	procs = g_strdup_printf("/sys/fs/cgroup%.*s/cgroup.procs", (int) strcspn(via, "\n"), via);
	if (!strstr(procs, ".scope/") || !g_file_get_contents(procs, &text, NULL, NULL))
		return NULL;
	pid = g_array_new(FALSE, FALSE, sizeof(pid_t));
	lines = g_strsplit(text, "\n", -1);
	for (char **r = lines; *r; r++)
		if (**r) {
			pid_t p = (pid_t) g_ascii_strtoll(*r, NULL, 10);

			g_array_append_val(pid, p);
		}
	return pid;
}

/* A pid of the scope that can be closed: the user's, not us, not the product. */
static bool survivor(pid_t p, char *name, gsize n)
{
	g_autofree char *fpath = g_strdup_printf("/proc/%d/comm", (int) p);
	g_autofree char *comm = NULL;
	GStatBuf st;

	if (p <= 1 || p == getpid() || g_stat(fpath, &st) != 0 || st.st_uid != getuid())
		return false;
	if (!g_file_get_contents(fpath, &comm, NULL, NULL))
		return false;
	g_strstrip(comm);
	if (!g_strcmp0(comm, "remotix"))
		return false;
	g_strlcpy(name, comm, n);
	return true;
}

/*
 * ⛔ THE LEFTOVERS OF THE SCOPE — `[M]` 6 Oct 2026, NVIDIA, Ubuntu 26.04, XFCE:
 *    after «Log Out» (successful logout, labwc dead) in the `session-N.scope`
 *    `localsearch-3` and `agent` (geoclue) remained, started by the XDG
 *    autostart that machine has for the GNOME packages ⇒ F-021 red on
 *    both browsers.  The session manager closes ITS clients; whoever
 *    detached from it (D-Bus activation, double fork) stays.
 * ⇒ Once the session has exited, what is left in OUR scope and belongs
 *   to the user goes away: SIGTERM, 2 s, then SIGKILL to whoever resists.  For all
 *   desktops: the scope is the session the product opened, and a
 *   process that is in it after the end is a leftover, whoever
 *   launched it.  ⚠ The user manager (`user@.service`) is NOT the scope: the
 *   systemd --user services stay, and R1/R2 deals with those.
 */
void session_clear_out_scope(void)
{
	g_autoptr(GArray) pid = my_scope_pid();
	g_autoptr(GString) names = g_string_new(NULL);
	int hit = 0, stubborn = 0;
	char name[32];

	if (!pid) {
		log_detail(LOG_SESSION, "scope leftovers: the cgroup cannot be read, skipping");
		return;
	}
	for (guint i = 0; i < pid->len; i++) {
		pid_t p = g_array_index(pid, pid_t, i);

		if (!survivor(p, name, sizeof name) || kill(p, SIGTERM) != 0)
			continue;
		hit++;
		if (names->len < 200)
			g_string_append_printf(names, " %s", name);
	}
	if (!hit) {
		log_detail(LOG_SESSION, "scope leftovers: none");
		return;
	}
	for (int cur_round = 0; cur_round < 20; cur_round++) {
		g_autoptr(GArray) still = my_scope_pid();
		bool alive = false;

		for (guint i = 0; still && i < still->len && !alive; i++)
			alive = survivor(g_array_index(still, pid_t, i), name, sizeof name);
		if (!alive)
			break;
		g_usleep(100 * 1000);
	}
	{
		g_autoptr(GArray) still = my_scope_pid();

		for (guint i = 0; still && i < still->len; i++) {
			pid_t p = g_array_index(still, pid_t, i);

			if (survivor(p, name, sizeof name) && kill(p, SIGKILL) == 0)
				stubborn++;
		}
	}
	registro_dice(LOG_SESSION,
	              "⭐ scope leftovers after the exit: SIGTERM to %d processes (%s)%s",
	              hit, names->str + 1,
	              stubborn ? " — and SIGKILL to those that did not exit within 2 s" : "");
}

/* ⭐ R1/R2: a session closed by us leaves the user manager as it was. */
bool session_terminate(void)
{
	bool output = really_terminate();

	if (output) {
		session_clear_out_scope();
		session_clear_out_handler("session terminated by the product");
	}
	return output;
}

static bool really_terminate(void)
{
	if (!session_alive()) {
		registro_dice(LOG_SESSION, "there was no session to stop");
		return false;
	}

	if (e_xfce()) {
		registro_dice(LOG_SESSION,
		              "asking the XFCE session to exit "
		              "(org.xfce.Session.Manager.Logout)");
		if (exit_xfce() && wait_until_done()) {
			registro_dice(LOG_SESSION, "the graphical session has exited");
			return true;
		}
		registro_dice(LOG_SESSION,
		              "⚠ the session does not exit: I close it by force (SIGTERM to "
		              SESSION_PROCESS_XFCE "), whatever was not saved is "
		              "lost — ⛔ and here the force is not systemd: on XFCE the "
		              "compositor is not a unit");
		if (kill_xfce() && wait_until_done()) {
			registro_dice(LOG_SESSION, "the graphical session has exited, by force");
			return true;
		}
		registro_dice(LOG_SESSION, "⛔ the graphical session did not exit even by force");
		return false;
	}

	/* ⭐ PHASE 14 — LXQt: XFCE's shape, with LXQt's target in front. */
	if (e_lxqt()) {
		registro_dice(LOG_SESSION,
		              "asking the LXQt session to exit (org.lxqt.session.logout, "
		              "without waiting for an answer: it is Q_NOREPLY)");
		if (exit_lxqt() && wait_until_done()) {
			registro_dice(LOG_SESSION, "the graphical session has exited");
			return true;
		}
		registro_dice(LOG_SESSION,
		              "⚠ the session does not exit: I close it by force (SIGTERM to "
		              SESSION_PROCESS_XFCE "), whatever was not saved is "
		              "lost — ⛔ and here the force is not systemd: on LXQt the "
		              "compositor is not a unit");
		if (kill_xfce() && wait_until_done()) {
			registro_dice(LOG_SESSION, "the graphical session has exited, by force");
			return true;
		}
		registro_dice(LOG_SESSION, "⛔ the graphical session did not exit even by force");
		return false;
	}

	if (e_kde()) {
		registro_dice(LOG_SESSION,
		              "asking the Plasma session to exit (org.kde.Shutdown.logout)");
		if (exit_kde(FALSE) && wait_until_done()) {
			registro_dice(LOG_SESSION, "the graphical session has exited");
			return true;
		}
		registro_dice(LOG_SESSION,
		              "⚠ the session does not exit: I close it by force (StopUnit %s), whatever "
		              "was not saved is lost",
		              SESSION_UNIT_PLASMA);
		if (exit_kde(TRUE) && wait_until_done()) {
			registro_dice(LOG_SESSION, "the graphical session has exited, by force");
			return true;
		}
		registro_dice(LOG_SESSION, "⛔ the graphical session did not exit even by force");
		return false;
	}

	registro_dice(LOG_SESSION, "asking the graphical session to exit (Logout 1)");
	if (exit_gnome(1) && wait_until_done()) {
		registro_dice(LOG_SESSION, "the graphical session has exited");
		return true;
	}

	registro_dice(LOG_SESSION,
	              "⚠ the session does not exit: I close it by force (Logout 2), whatever was not "
	              "saved is lost");
	if (exit_gnome(2) && wait_until_done()) {
		registro_dice(LOG_SESSION, "the graphical session has exited, by force");
		return true;
	}

	registro_dice(LOG_SESSION, "⛔ the graphical session did not exit even by force");
	return false;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ THE SETTINGS THE SESSION MUST HAVE BEFORE BEING BORN — phase 5.
 *
 * ⛔ WHY WE SET THEM, and they are not in a provisioning file: it is
 *    invariant **I7**.  A protection that lives in a configuration
 *    line someone may fail to apply is not a protection — and
 *    `[M]` on 15 August 2026 v1's provisioning, re-run after a reboot,
 *    put the WRONG state back in place and cost us an evening.
 *
 * ⛔⛔ AND `g_settings_new()` ON A SCHEMA THAT DOES NOT EXIST ABORTS THE PROCESS —
 *     it does not return NULL: it calls `g_error()`.  ⇒ Every schema is LOOKED UP first, and if
 *     it is missing a line is written and we move on.  A desktop without
 *     `org.gnome.shell` is a desktop that is not GNOME, not a fault of ours.
 */
struct setting {
	const char *schema;
	const char *key;
	const char *why;
};

/* ⛔ The twelve that Mutter SWALLOWS and that are useless in headless mode.
 *
 * `[R]` `org.gnome.mutter.wayland` binds `<Primary><Alt>F1…F12` to
 * `switch-to-session-1…12`, and `keybindings.c` registers them as
 * **`META_KEY_BINDING_NON_MASKABLE`**: no application can take them,
 * not even by asking.  ⚠ In a headless session there is NO virtual
 * console to switch to: Mutter intercepts them, tries, fails and writes a
 * warning.  ⇒ Twelve combinations taken away from the user for nothing. */
static const char *VT_SHORTCUTS[] = { "switch-to-session-1",  "switch-to-session-2",
	                                "switch-to-session-3",  "switch-to-session-4",
	                                "switch-to-session-5",  "switch-to-session-6",
	                                "switch-to-session-7",  "switch-to-session-8",
	                                "switch-to-session-9",  "switch-to-session-10",
	                                "switch-to-session-11", "switch-to-session-12",
	                                NULL };

/*
 * ⛔⛔ AND LOOKING UP THE SCHEMA IS NOT ENOUGH: THE KEY MUST BE LOOKED UP TOO.
 *
 * `[M]` 15 August 2026, and the price was a child dead of **signal 5**
 * (`SIGTRAP`) right after writing the drop-in: GLib, faced with a key
 * that does not exist in its schema, calls `g_error()` — which **aborts the
 * process**, it does not return an error.  ⇒ A key renamed upstream between two
 * GNOME versions kills the child, and the symptom the user sees is
 * «the desktop does not start», with no relation to the key.
 *
 * ⚠ The comment above this function already said so for SCHEMAS, and I
 *   wrote it myself: the lesson is that a trap known by half is a
 *   trap.  ⇒ Here both are checked, and a missing key is
 *   a log line, not a death.
 */
struct schema_open {
	GSettings *settings;
	GSettingsSchema *schema;
};

static struct schema_open open_schema(const char *name)
{
	struct schema_open a = { NULL, NULL };
	GSettingsSchemaSource *source = g_settings_schema_source_get_default();

	if (!source)
		return a;
	a.schema = g_settings_schema_source_lookup(source, name, TRUE);
	if (!a.schema) {
		registro_dice(LOG_SESSION,
		              "⚠ the schema «%s» does not exist on this machine: I do not touch it "
		              "(and this is NOT a fault: it is a different desktop)",
		              name);
		return a;
	}
	a.settings = g_settings_new_full(a.schema, NULL, NULL);
	return a;
}

static void close_schema(struct schema_open *a)
{
	g_clear_object(&a->settings);
	g_clear_pointer(&a->schema, g_settings_schema_unref);
}

/* ⛔ The guard: is the key there?  If not, say so and move on. */
static gboolean schema_has_key(const struct schema_open *a, const char *key,
                              const char *schema)
{
	if (!a->settings || !a->schema)
		return FALSE;
	if (g_settings_schema_has_key(a->schema, key))
		return TRUE;
	registro_dice(LOG_SESSION,
	              "⚠ the key «%s» does not exist in the schema «%s» of this "
	              "machine: I do not touch it.  ⛔ And it is not a slip to ignore — "
	              "without this check GLib would call `g_error()` and the "
	              "process would DIE (signal 5), with the symptom «the desktop does not "
	              "start» and no relation to the key",
	              key, schema);
	return FALSE;
}

/*
 * ⭐ PHASE 15, D-015 — ONE ALLOWED KEY, in the USER's dconf (lock,
 *    reboot, suspend, standby: the decision of 25 Sep 2026).
 *
 * ⛔ Not with `g_settings_set_*`: this process's engine has the
 *    SESSION profile, and would write into the in-memory database.  We write to the
 *    user's writer (`/ca/desrt/dconf/Writer/user`), at the path the
 *    schema declares; then it is RE-READ with GSettings — that is through the
 *    session profile, that is as the Shell and the `gsd-*` will read it:
 *    written is not in force until it is re-read.
 * ⚠ `value` may be floating: it is always taken.
 */
static gboolean gnome_set_user(const struct schema_open *a, const char *schema,
                                   const char *key, GVariant *value)
{
	g_autoptr(GVariant) v = g_variant_ref_sink(value);
	g_autoptr(GVariant) reread = NULL;
	g_autoptr(GError) mistake = NULL;
	g_autofree char *fpath = NULL;
	const char *base;

	if (!schema_has_key(a, key, schema))
		return FALSE;
	base = g_settings_schema_get_path(a->schema);
	if (!base) {
		registro_dice(LOG_SESSION, "⛔ the schema «%s» has no path: «%s» NOT written",
		              schema, key);
		return FALSE;
	}
	fpath = g_strconcat(base, key, NULL);
	if (!dconf_change("/ca/desrt/dconf/Writer/user", fpath, v, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⛔ D-015: %s NOT written in the user's dconf (%s)", fpath,
		              mistake ? mistake->message : "no reason given");
		return FALSE;
	}
	reread = g_settings_get_value(a->settings, key);
	if (!reread || !g_variant_equal(reread, v)) {
		g_autofree char *expected = g_variant_print(v, FALSE);
		g_autofree char *read = reread ? g_variant_print(reread, FALSE) : NULL;

		registro_dice(LOG_SESSION,
		              "⛔ D-015: %s written in the user's (%s) but the session re-reads %s — "
		              "NOT in force",
		              fpath, expected, read ? read : "nothing");
		return FALSE;
	}
	{
		g_autofree char *n_written = g_variant_print(v, FALSE);

		registro_dice(LOG_SESSION,
		              "⭐ D-015: %s = %s in the USER's dconf (allowed: lock, "
		              "reboot, suspend, standby), RE-READ by the session",
		              fpath, n_written);
	}
	return TRUE;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 13 — XFCE'S LEVERS: WRITE, RE-READ, SAY WHETHER IT IS IN FORCE.
 *
 * It is the logout belt's pattern (`WaylandLogoutCommand`, below in
 * `session_settings()`) made into a function, because the keys are now eight
 * and not one.
 *
 * ⛔⛔ AND IT IS ALWAYS RE-READ: `xfconf-query` exits with **zero even when the
 *     daemon refuses** — the API is asynchronous, the local cache answers first
 *     and the old value comes back later (`STUDIES.md` §xfce §10.6).  ⇒ The writer's
 *     exit status says nothing: only re-reading tells the truth.
 *
 * ⭐ AND WRITING BEFORE THE SESSION IS BORN WORKS — the question this
 *    function had to pass: `xfconfd` **has** D-Bus activation (§10.6), and
 *    `xfconf-query` talks to the user bus, which is the same as the session's
 *    (`session_alive()`: `labwc` starts without `dbus-run-session`).  ⇒ The
 *    write wakes up the daemon the session will find already alive.  `[M]` 20 Sep
 *    2026: the logout belt, written before `start()`, RE-READS correctly.
 * ⚠ And it also holds AFTERWARDS: the three components touched here (`xfce4-session`,
 *   `xfce4-power-manager`, libxfce4ui) are bound to xfconf and react to the
 *   change on the fly `[R]` (`xfpm-dpms.c` `settings_changed`,
 *   `xfce-screensaver.c:342-346`, the logout dialog reads at creation).
 *
 * Returns TRUE if re-reading gives exactly the written value.
 */
static gboolean xfconf_put(const char *channel, const char *key, const char *kind,
                             const char *value, const char *why)
{
	char *write[] = { "xfconf-query", "-c",       (char *) channel, "-p",
		           (char *) key, "-n",       "-t",            (char *) kind,
		           "-s",            (char *) value, NULL };
	char *reread_cmd[] = { "xfconf-query", "-c", (char *) channel, "-p", (char *) key, NULL };
	g_autofree char *read = NULL;

	run(write);
	read = ask(reread_cmd);
	if (read)
		g_strstrip(read);
	if (g_strcmp0(read, value) == 0) {
		registro_dice(LOG_SESSION, "⭐ XFCE: %s %s = %s, RE-READ — %s", channel, key,
		              value, why);
		return TRUE;
	}
	registro_dice(LOG_SESSION,
	              "⛔ XFCE: %s %s is NOT in force (wrote «%s», re-read «%s») — "
	              "so it does NOT hold: %s",
	              channel, key, value, read ? read : "unknown", why);
	return FALSE;
}

/*
 * ⭐ THE ENTRIES OF THE PANEL'S ACTION BUTTON — the user's decision, 21 Sep
 *   2026: *«in XFCE too the standby, lockscreen,
 *   reset and power-off entries must be disabled»*.
 *
 * `[R]` `xfce4-panel` 4.20.4, `plugins/actions/actions.c`: the plugin reads
 * `/plugins/plugin-<N>/items`, an array of strings with `+`/`-` in front; an
 * entry with `-` **is not created at all** (`:1318`, `:1518`), while one with
 * `+` that is not allowed stays **visible and grey** (`:1347`).  ⇒ In XFCE there
 * is no KIOSK that removes them (`STUDIES.md` §xfce §10.4): they are removed HERE.
 *
 * ⛔ ONLY the four named families are removed: lock, suspend
 *    (with hibernate and hybrid sleep, which are the same family), reboot
 *    and power-off.  «Log Out» (`logout`, `logout-dialog`) STAYS — §4.1-ter, it is
 *    the only door.
 * ⭐ And since 21 Sep 2026, evening, «Switch User» too (`switch-user`) — the
 *    user's decision: *«remove Switch User too to make the
 *    behaviour uniform across all DEs: the only entry that must remain is logout»*.
 *    KDE removes it since phase 12 (KIOSK), GNOME with the dconf lockdown.
 */
static const char *ACTIONS_TO_REMOVE[] = { "lock-screen", "switch-user", "suspend",
	                                    "hibernate",   "hybrid-sleep", "restart",
	                                    "shutdown",    NULL };

/* ⚠ The stock default, `actions_plugin_default_array()` (`actions.c:1437`):
 *   needed when the `items` property is not there yet — and that is the normal case
 *   for a newly born panel, because `default.xml` does not write it. */
static const char *DEFAULT_ACTIONS[] = { "+lock-screen", "+switch-user",  "+separator",
	                                 "+suspend",     "-hibernate",    "-hybrid-sleep",
	                                 "-separator",   "+shutdown",     "-restart",
	                                 "+separator",   "+logout",       NULL };

/* The entries of an array as `xfconf-query` prints them: a header line
 * (translated, so it is NOT read), an empty line, then one entry per line.  ⇒ What
 * follows the first empty line is taken.  NULL if it is not an array. */
static char **array_entries(const char *output)
{
	const char *after = output ? strstr(output, "\n\n") : NULL;
	g_autoptr(GPtrArray) entries = NULL;
	g_auto(GStrv) lines = NULL;

	if (!after)
		return NULL;
	entries = g_ptr_array_new_with_free_func(g_free);
	lines = g_strsplit(after + 2, "\n", -1);
	for (int i = 0; lines[i]; i++)
		if (lines[i][0])
			g_ptr_array_add(entries, g_strdup(lines[i]));
	g_ptr_array_add(entries, NULL);
	return (char **) g_ptr_array_free(g_steal_pointer(&entries), FALSE);
}

static gboolean to_remove(const char *entry)
{
	return entry[0] == '+' && g_strv_contains(ACTIONS_TO_REMOVE, entry + 1);
}

/* An «actions» plugin: the entries to remove go from `+` to `-`, the others
 * stay identical and in their order.  Written and RE-READ. */
/* ⭐ PHASE 15, D-017 — ALLOWED: the removed entries are lock, suspend,
 *    reboot and power-off, that is the four kinds that the user's decision
 *    of 25 Sep 2026 allows to be written in the USER's channel
 *    («dangerous for other users present on the machine»).  ⚠ It stays in the
 *    user's channel: the plugin number is theirs, and a session block
 *    for `plugin-N` cannot be written before the panel is born. */
static gboolean fix_panel_actions(const char *base)
{
	g_autofree char *key = g_strdup_printf("%s/items", base);
	char *load[] = { "xfconf-query", "-c", "xfce4-panel", "-p", key, NULL };
	g_autofree char *prima = ask(load);
	g_auto(GStrv) old_ones = array_entries(prima);
	g_autoptr(GPtrArray) write = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GPtrArray) new_ones = g_ptr_array_new_with_free_func(g_free);
	g_autofree char *reread = NULL;
	g_auto(GStrv) reread_items = NULL;
	const char *const *da = old_ones ? (const char *const *) old_ones
	                                : (const char *const *) DEFAULT_ACTIONS;
	int removed = 0;
	gboolean equal;

	for (int i = 0; da[i]; i++) {
		if (to_remove(da[i])) {
			g_ptr_array_add(new_ones, g_strdup_printf("-%s", da[i] + 1));
			removed++;
		} else {
			g_ptr_array_add(new_ones, g_strdup(da[i]));
		}
	}
	g_ptr_array_add(new_ones, NULL);
	if (removed == 0) {
		registro_dice(LOG_SESSION,
		              "⭐ XFCE: %s — no entry to remove, they were already removed",
		              key);
		return TRUE;
	}

	/* ⚠ `--set=-lock-screen` and not `-s -lock-screen`: a value starting
	 *   with a dash, written separately, is read as an option. */
	g_ptr_array_add(write, g_strdup("xfconf-query"));
	g_ptr_array_add(write, g_strdup("-c"));
	g_ptr_array_add(write, g_strdup("xfce4-panel"));
	g_ptr_array_add(write, g_strdup("-p"));
	g_ptr_array_add(write, g_strdup(key));
	g_ptr_array_add(write, g_strdup("-n"));
	g_ptr_array_add(write, g_strdup("-a"));
	for (guint i = 0; i + 1 < new_ones->len; i++) {
		g_ptr_array_add(write, g_strdup("--type=string"));
		g_ptr_array_add(write,
		                g_strdup_printf("--set=%s", (char *) g_ptr_array_index(new_ones, i)));
	}
	g_ptr_array_add(write, NULL);
	run((char **) write->pdata);

	reread = ask(load);
	reread_items = array_entries(reread);
	equal = reread_items && g_strv_equal((const char *const *) reread_items,
	                                 (const char *const *) new_ones->pdata);
	if (equal)
		registro_dice(LOG_SESSION,
		              "⭐ XFCE: %s RE-READ — %d entries removed from the action button "
		              "(lock, suspend, reboot, power-off); «Log Out» and «Switch "
		              "User» stay as they were",
		              key, removed);
	else
		registro_dice(LOG_SESSION,
		              "⛔ XFCE: %s is NOT in force (the re-read does not match): the lock, "
		              "suspend, reboot and power-off entries stay in the "
		              "action button.  ⚠ Reboot and power-off stay GREY "
		              "(polkit says no), suspend does not: sleep.conf removes it",
		              key);
	return equal;
}

/*
 * ⛔⛔ WHY A THREAD, and not a write before birth — and it is the
 *     «try to refute yourself» question that here answered YES.
 *
 * The keys of `xfce4-session` and `xfce4-power-manager` have a fixed name, and
 * are written beforehand (`xfconf_put`).  These do NOT: the plugin is called
 * `plugin-<N>`, and `N` is known only to the `xfce4-panel` channel — which for a user
 * who never opened XFCE **is empty until the panel starts** and
 * migrates the default layout into it (`migrate/main.c`).  ⇒ Written beforehand, for a
 * new user, they would have no target: not «lost», worse — **never
 * written**, and without a line saying so.
 *
 * ⇒ The channel is checked every 2 s until an `actions` plugin appears, and it is
 *   fixed.  ⭐ The panel binds `items` to xfconf (`panel_properties_bind`) and
 *   on change redoes the buttons (`actions.c:428-434`): it works on the fly.
 * ⚠ For the user who already has a panel the plugin is there at once, and the first round
 *   fixes it — usually even before the panel shows it.
 * ⚠ Declared what it does NOT cover: an `actions` plugin added by hand LATER,
 *   inside the session, keeps its default.  Reboot and power-off stay
 *   grey anyway (polkit), suspend is not there (sleep.conf), and lock
 *   does not lock (`LockCommand`).
 */
#define PANEL_XFCE_STEP_US (2 * G_USEC_PER_SEC)
#define PANEL_XFCE_PATIENCE_S 120

static gpointer xfce_panel_guard(gpointer data)
{
	const gint64 started = g_get_monotonic_time();

	(void) data;
	for (;;) {
		char *list_cmd[] = { "xfconf-query", "-c", "xfce4-panel", "-l", "-v", NULL };
		g_autofree char *listing = ask(list_cmd);
		g_auto(GStrv) lines = g_strsplit(listing ? listing : "", "\n", -1);
		int matches = 0, fixed = 0;

		/* A line of `-l -v` is «property  value», aligned with spaces. */
		for (int i = 0; lines[i]; i++) {
			g_auto(GStrv) parts = g_strsplit_set(g_strstrip(lines[i]), " \t", 2);
			const char *nr;

			if (!parts[0] || !parts[1] ||
			    !g_str_has_prefix(parts[0], "/plugins/plugin-"))
				continue;
			nr = parts[0] + strlen("/plugins/plugin-");
			if (!*nr || strspn(nr, "0123456789") != strlen(nr))
				continue;
			if (g_strcmp0(g_strstrip(parts[1]), "actions") != 0)
				continue;
			matches++;
			if (fix_panel_actions(parts[0]))
				fixed++;
		}
		if (matches) {
			registro_dice(LOG_SESSION,
			              "%s XFCE: panel action buttons: %d found, %d "
			              "fixed and re-read",
			              fixed == matches ? "⭐" : "⛔", matches, fixed);
			return NULL;
		}
		if (g_get_monotonic_time() - started > PANEL_XFCE_PATIENCE_S * G_USEC_PER_SEC) {
			registro_dice(LOG_SESSION,
			              "⚠ XFCE: in %d s no action button in the channel "
			              "xfce4-panel — I remove nothing, because there is nothing to "
			              "remove (or the panel did not start).  I stop watching",
			              PANEL_XFCE_PATIENCE_S);
			return NULL;
		}
		g_usleep(PANEL_XFCE_STEP_US);
	}
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 14, INCREMENT 4 — ON LXQt THERE IS NO «Lock screen» ANY MORE.
 *     `DECISIONS.md` §4.7: away with lock, suspend, reboot and power-off;
 *     ⛔ «Log Out» STAYS (§4.1-ter).  The user, after increment 2: «the
 *     lockscreen icon still seems active and visible».
 *
 * `[M]`/`[R]` WHERE IT WAS: in the `lxqt-leave` window, opened by the
 * FIXED «Leave» button at the bottom of the fancymenu (lxqt-panel 2.1.4
 * `plugin-fancymenu/lxqtfancymenuwindow.cpp:165-169, 315-318`) — code, not
 * a menu entry, and no key removes it.  ⛔ And clicked it was WORSE than
 * inert: `lxqt-leave` stayed hung (see the leftovers in
 * `settings_lxqt()`).
 *
 * Two cures, each with its read and its re-read:
 *   A) `lxqt_panel()` — the panel uses `mainmenu` instead of `fancymenu`:
 *      the classic menu has NO fixed buttons, and reads the same
 *      `lxqt-applications.menu`, so the six entries hidden
 *      by increment 2 stay hidden and «Leave» contains only «Logout»;
 *   B) `block_lxqt()` — the safety net: `lock_command_wayland=true`,
 *      for whoever launches `lxqt-leave` by hand (or from a shortcut).
 */

/*
 * ⚠ QSettings FILES ARE NOT ALWAYS KEY FILES: `QSettings` writes the
 *   top-level keys BEFORE any group (`[M]` Trixie's
 *   `/usr/share/lxqt/panel.conf` starts with `panels=panel1`), and
 *   GKeyFile rejects that file.  ⇒ A `[General]` is put in front, which is
 *   the name QSettings gives to that group; if the file already has a `[General]`,
 *   GKeyFile merges the two.
 */
static gboolean read_ini_qt(GKeyFile *keys, const char *file, GError **mistake)
{
	g_autofree char *inside = NULL;
	g_autofree char *with_head = NULL;

	if (!g_file_get_contents(file, &inside, NULL, mistake))
		return FALSE;
	with_head = g_strconcat("[General]\n", inside, NULL);
	return g_key_file_load_from_data(keys, with_head, -1,
	                                 G_KEY_FILE_KEEP_COMMENTS |
	                                         G_KEY_FILE_KEEP_TRANSLATIONS,
	                                 mistake);
}

/*
 * ⭐ WRITE A KEY AND RE-READ IT — the rule common to all LXQt keys:
 *   the file is read, ONLY that key is changed, the others stay; if it exists
 *   and cannot be read it is NOT rewritten.  Returns the value RE-READ from the file
 *   (NULL if it cannot be re-read), and in `*why` the reason, if it did not write.
 */
static char *write_qt_key(const char *file, const char *group, const char *key,
                              const char *value, char **why)
{
	g_autofree char *folder = g_path_get_dirname(file);
	g_autoptr(GKeyFile) keys = g_key_file_new();
	g_autoptr(GKeyFile) reread = g_key_file_new();
	g_autoptr(GError) mistake = NULL;

	if (g_file_test(file, G_FILE_TEST_EXISTS) && !read_ini_qt(keys, file, &mistake)) {
		*why = g_strdup_printf("it exists but I cannot read it (%s) — I do NOT rewrite it, "
		                          "so as not to throw away the user's keys",
		                          mistake->message);
		return NULL;
	}
	g_key_file_set_value(keys, group, key, value);
	g_clear_error(&mistake);
	if (g_mkdir_with_parents(folder, 0700) != 0 ||
	    !g_key_file_save_to_file(keys, file, &mistake)) {
		*why = g_strdup_printf("NOT written (%s)",
		                          mistake ? mistake->message : g_strerror(errno));
		return NULL;
	}
	/* ⛔ AND IT IS RE-READ: written is not in force until it is re-read. */
	if (!read_ini_qt(reread, file, NULL))
		return NULL;
	return g_key_file_get_value(reread, group, key, NULL);
}

/*
 * The SYSTEM files of an LXQt module, in the order QSettings looks for them:
 * `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share`, which we set at launch.
 */
static GPtrArray *system_files(const char *module)
{
	static const char *const DIRS[] = { "/etc", "/etc/xdg", "/usr/share", NULL };
	GPtrArray *system_wide = g_ptr_array_new_with_free_func((GDestroyNotify) g_key_file_unref);

	for (int i = 0; DIRS[i]; i++) {
		g_autofree char *name = g_strconcat(module, ".conf", NULL);
		g_autofree char *file = g_build_filename(DIRS[i], "lxqt", name, NULL);
		GKeyFile *uno = g_key_file_new();

		if (g_file_test(file, G_FILE_TEST_EXISTS) && read_ini_qt(uno, file, NULL))
			g_ptr_array_add(system_wide, uno);
		else
			g_key_file_unref(uno);
	}
	return system_wide;
}

/*
 * ⭐ THE VALUE QSettings REALLY SEES: the user's if there is one, otherwise the
 *   first of the system files, in `XDG_CONFIG_DIRS` order.  ⚠ `[R]` LXQt's
 *   user files are SPARSE: `LXQt::Settings` creates the file with only
 *   `__userfile__=true` (liblxqt 2.1.0 `lxqtsettings.cpp:53-59`), and the
 *   rest comes from the system.  ⇒ Looking at the user's file alone
 *   would say «no fancymenu» to a user who has one.
 */
static char *effective_value(GKeyFile *user, GPtrArray *system_wide, const char *group,
                              const char *key)
{
	char *value = g_key_file_get_value(user, group, key, NULL);

	for (guint i = 0; !value && i < system_wide->len; i++)
		value = g_key_file_get_value(g_ptr_array_index(system_wide, i), group, key, NULL);
	return value;
}

/*
 * The NAMES of the panel plugins that, seen as lxqt-panel sees them, are of
 * type `kind`.
 * `[R]` lxqt-panel 2.1.4: `panels` is the list of panels, `<panel>/plugins`
 * the list of the plugins' GROUP NAMES, and `<name>/type` the type
 * (`panelpluginsmodel.cpp:229`).  ⇒ The group name stays `fancymenu`:
 * only `type` counts.
 * ⚠ Empty `panels` — or `@Invalid()`, which is how QSettings writes an empty
 *   list — means `panel1` (`lxqtpanelapplication.cpp:381-383`).  ⛔ And it is the
 *   user's key that counts even when it is `@Invalid()`: QSettings
 *   finds it there and does not look at the system.
 */
static GPtrArray *plugins_of_type(GKeyFile *user, GPtrArray *system_wide, const char *kind)
{
	g_autofree char *panels = effective_value(user, system_wide, "General", "panels");
	gboolean blank = !panels || !*g_strstrip(panels) ||
	                 g_strcmp0(panels, "@Invalid()") == 0;
	g_auto(GStrv) which_ones = g_strsplit(blank ? "panel1" : panels, ",", -1);
	GPtrArray *found_names = g_ptr_array_new_with_free_func(g_free);

	for (int p = 0; which_ones[p]; p++) {
		g_autofree char *listing = effective_value(user, system_wide, g_strstrip(which_ones[p]),
		                                           "plugins");
		g_auto(GStrv) names = g_strsplit(listing ? listing : "", ",", -1);

		for (int n = 0; names[n]; n++) {
			const char *name = g_strstrip(names[n]);
			g_autofree char *e = *name ? effective_value(user, system_wide, name, "type")
			                           : NULL;

			if (g_strcmp0(e, kind) == 0)
				g_ptr_array_add(found_names, g_strdup(name));
		}
	}
	return found_names;
}

/*
 * A) THE PANEL: `fancymenu` → `mainmenu`.
 *
 * ⛔⛔ PHASE 15, D-018 — IN THE SESSION'S FILE, and the panel does not touch
 *     the user's: the user's settings are not touched
 *     (decision of 25 Sep 2026), and a menu is not lock, reboot,
 *     suspend or standby.
 *
 * ⛔ THE FIRST DRAFT WAS NOT ENOUGH — `[M]` 25 Sep 2026, 15-f031b on
 *    rete11-lxqt: a session `lxqt/panel.conf` at the head of
 *    `XDG_CONFIG_DIRS` is read, yes, but `lxqt-panel` at startup REWRITES
 *    all the configuration it sees into the USER's file
 *    (`~/.config/lxqt/panel.conf`: `type`, `alignment`, the whole `[panel1]`) —
 *    and our `type=mainmenu` ended up in there.  ⚠ The rewrite is the
 *    desktop's (`alignment`, `iconSize`… are not written by us): the trouble was
 *    only that it read it from us.
 *
 * ⭐ THE CURE: the session's panel uses a file of ITS OWN.
 *    `[R]` lxqt-panel 2.1.4 `lxqtpanelapplication.cpp`: `-c/--configfile`
 *    ⇒ `LXQt::Settings(configFile, QSettings::IniFormat)` — reads and WRITES
 *    that file, and nothing else (no system folders: the file must
 *    be COMPLETE).  And `lxqt-panel` is launched by `lxqt-session` as a module
 *    from autostart (`[R]` lxqt-session 2.1.1 `lxqtmodman.cpp`:
 *    `XdgAutoStart::desktopFileList()`, `X-LXQt-Module`, `expandExecString`),
 *    which looks by file NAME in `~/.config/autostart` and then in
 *    `XDG_CONFIG_DIRS`, and the first wins.  ⇒ Two files in the SESSION:
 *    · `$XDG_RUNTIME_DIR/remotix/panel-lxqt.conf` — the user's panel
 *      AS IT IS (the system files merged, with their sparse file on top)
 *      and `type=mainmenu` in place of the fancymenu;
 *    · `$XDG_RUNTIME_DIR/remotix/xdg-lxqt/autostart/lxqt-panel.desktop` —
 *      the same system module, with `--configfile` that file.
 *
 * ⚠ The prices: what the user changes in the panel FROM REMOTE holds for the
 *   session and is lost at the next birth (as on GNOME); and a user's
 *   `~/.config/autostart/lxqt-panel.desktop` comes before
 *   ours — it is said, and then their panel stays (with the fancymenu, and the
 *   safety net B below).
 */
static void lxqt_panel(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autofree char *file = g_build_filename(g_get_home_dir(), ".config", "lxqt", "panel.conf",
	                                         NULL);
	g_autofree char *its_startup = g_build_filename(g_get_home_dir(), ".config", "autostart",
	                                              "lxqt-panel.desktop", NULL);
	g_autofree char *cfg = lxqt_session_config_folder();
	g_autofree char *our = NULL;
	g_autofree char *startup = NULL;
	g_autofree char *autostart_dir = NULL;
	g_autofree char *old = NULL;
	g_autofree char *startup_line = NULL;
	g_autoptr(GKeyFile) user = g_key_file_new();
	g_autoptr(GKeyFile) merged = g_key_file_new();
	g_autoptr(GKeyFile) reread = g_key_file_new();
	g_autoptr(GPtrArray) system_wide = system_files("panel");
	g_autoptr(GPtrArray) ours_only = NULL;
	g_autoptr(GPtrArray) layers = g_ptr_array_new();
	g_autoptr(GPtrArray) fancy = NULL;
	g_autoptr(GPtrArray) remain = NULL;
	g_autoptr(GError) mistake = NULL;
	guint changed = 0;

	if (!runtime || !*runtime || !cfg) {
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: without XDG_RUNTIME_DIR there is no session folder — "
		              "the panel keeps the fancymenu, and its «Leave» button");
		return;
	}
	our = g_build_filename(runtime, "remotix", "panel-lxqt.conf", NULL);
	autostart_dir = g_build_filename(cfg, "autostart", NULL);
	startup = g_build_filename(autostart_dir, "lxqt-panel.desktop", NULL);
	/* ⛔ the leftover of the first draft: read by lxqt-panel, it ended up in the user's */
	old = g_build_filename(cfg, "lxqt", "panel.conf", NULL);
	g_unlink(old);

	if (g_file_test(file, G_FILE_TEST_EXISTS) && !read_ini_qt(user, file, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⚠ LXQt: %s exists but I cannot read it (%s) — the session's panel "
		              "starts from the system alone (and I do not touch the file)",
		              file, mistake->message);
		g_clear_error(&mistake);
	}

	/* the panel as it is: system from weakest to strongest, then the user */
	for (guint i = system_wide->len; i > 0; i--)
		g_ptr_array_add(layers, g_ptr_array_index(system_wide, i - 1));
	g_ptr_array_add(layers, user);
	for (guint i = 0; i < layers->len; i++) {
		GKeyFile *uno = g_ptr_array_index(layers, i);
		g_auto(GStrv) groups = g_key_file_get_groups(uno, NULL);

		for (int g = 0; groups[g]; g++) {
			g_auto(GStrv) keys = g_key_file_get_keys(uno, groups[g], NULL, NULL);

			for (int k = 0; keys && keys[k]; k++) {
				g_autofree char *v = g_key_file_get_value(uno, groups[g], keys[k], NULL);

				if (v)
					g_key_file_set_value(merged, groups[g], keys[k], v);
			}
		}
	}
	fancy = plugins_of_type(user, system_wide, "fancymenu");
	for (guint i = 0; i < fancy->len; i++)
		g_key_file_set_value(merged, g_ptr_array_index(fancy, i), "type", "mainmenu");
	if (g_mkdir_with_parents(autostart_dir, 0700) != 0 ||
	    !g_key_file_save_to_file(merged, our, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: %s NOT written (%s): the panel keeps the fancymenu, "
		              "and its «Leave» button",
		              our, mistake ? mistake->message : g_strerror(errno));
		return;
	}
	startup_line = g_strdup_printf("[Desktop Entry]\n"
	                             "Type=Application\n"
	                             "Name=Panel\n"
	                             "TryExec=lxqt-panel\n"
	                             "Exec=lxqt-panel --configfile %s\n"
	                             "OnlyShowIn=LXQt;\n"
	                             "X-LXQt-Module=true\n"
	                             "X-REMOTIX=the session's panel (D-018)\n",
	                             our);
	if (!g_file_set_contents(startup, startup_line, -1, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: %s NOT written (%s): the panel will start with the user's "
		              "file, and with the fancymenu",
		              startup, mistake->message);
		return;
	}

	/* ⛔ AND IT IS RE-READ: the session's file, alone (it is all the
	 *    panel will read), and who wins in autostart. */
	if (!read_ini_qt(reread, our, NULL)) {
		registro_dice(LOG_SESSION, "⛔ LXQt: %s written but it does NOT re-read", our);
		return;
	}
	ours_only = g_ptr_array_new();
	for (guint i = 0; i < fancy->len; i++) {
		g_autofree char *e = g_key_file_get_value(reread, g_ptr_array_index(fancy, i),
		                                          "type", NULL);

		changed += g_strcmp0(e, "mainmenu") == 0;
	}
	remain = plugins_of_type(reread, ours_only, "fancymenu");
	if (g_file_test(its_startup, G_FILE_TEST_EXISTS))
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: %s exists and belongs to the user: it comes BEFORE ours, and the "
		              "panel will start as it says (with its file, and with the fancymenu if "
		              "it has one) — I do not touch it",
		              its_startup);
	else if (remain->len == 0 && changed == fancy->len)
		registro_dice(LOG_SESSION,
		              "⭐ LXQt: the SESSION's panel is %s (%u fancymenu→mainmenu, "
		              "RE-READ), launched with --configfile from %s — the user's panel "
		              "(%s) neither reads nor writes it",
		              our, changed, startup, file);
	else
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: fancymenu→mainmenu NOT in force in the session's file "
		              "(I re-read %u mainmenu out of %u, and %u fancymenu still there)",
		              changed, fancy->len, remain->len);
}

/*
 * B) THE SAFETY NET: the lock command set to `true`.
 *
 * `[R]` liblxqt 2.1.0 `lxqtscreensaver.cpp:153-161`, on Wayland:
 *   1. the TOP-LEVEL `lock_command_wayland` in `session.conf` wins (or in the
 *      `$LXQT_SESSION_CONFIG` module: our launcher does `exec
 *      lxqt-session` without `-c`, so it is `session`);
 *   2. if it is not there, `[Screensaver] lock_command_wayland` of `lxqt.conf`,
 *      WITHOUT a default — no shipped file sets it.
 * ⛔⛔ Writing only 2 and re-reading only 2 would LIE to a user who has
 *     `lock_command_wayland=swaylock` in `session.conf`: the log would say
 *     «in force» and swaylock would hold.  ⇒ The value is computed with the same
 *     precedence as liblxqt, and if `session.conf` carries one that is not
 *     `true` — even empty, which wins anyway and leaves things hanging — it is set
 *     to `true` there too, saying what was there.
 * With `true`: the process exits with 0 ⇒ `activated` and `done` (`:196-207`) ⇒
 * `lxqt-leave` closes, and NO error window.  ⛔ Empty left it
 * hanging; `/bin/false` would open the «Screen Saver Error» modal.
 * ⚠ «Lock screen» says «done» and does not lock: it is a lie, but locking belongs to
 *   REMOTIX (§4.3), and the real cure is A, which no longer shows that button.
 * ⚠ The price, declared: these are the USER's `lxqt.conf` and (if needed) `session.conf`.
 */
static void block_lxqt(void)
{
	static const char *const CHIAVE = "lock_command_wayland";
	g_autofree char *folder = g_build_filename(g_get_home_dir(), ".config", "lxqt", NULL);
	g_autofree char *lxqt = g_build_filename(folder, "lxqt.conf", NULL);
	g_autofree char *session = g_build_filename(folder, "session.conf", NULL);
	g_autoptr(GPtrArray) system_lxqt = system_files("lxqt");
	g_autoptr(GPtrArray) system_session = system_files("session");
	g_autoptr(GKeyFile) session_user = g_key_file_new();
	g_autoptr(GKeyFile) session_reread = g_key_file_new();
	g_autoptr(GKeyFile) lxqt_user = g_key_file_new();
	g_autofree char *why = NULL;
	g_autofree char *in_lxqt = NULL;
	g_autofree char *era = NULL;
	g_autofree char *effective = NULL;

	/* number 2, always: it is the one that holds if number 1 is not there */
	in_lxqt = write_qt_key(lxqt, "Screensaver", CHIAVE, "true", &why);
	if (why)
		registro_dice(LOG_SESSION, "⛔ LXQt: %s %s", lxqt, why);
	g_clear_pointer(&why, g_free);

	/* number 1, only if it is there and is not `true` */
	if (g_file_test(session, G_FILE_TEST_EXISTS) &&
	    !read_ini_qt(session_user, session, NULL)) {
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: %s exists but I cannot read it — I do NOT rewrite it, and I do not "
		              "know which lock command holds",
		              session);
		return;
	}
	era = effective_value(session_user, system_session, "General", CHIAVE);
	if (era && g_strcmp0(era, "true") != 0) {
		g_autofree char *reread = write_qt_key(session, "General", CHIAVE, "true",
		                                            &why);

		registro_dice(LOG_SESSION,
		              "%s LXQt: %s carried %s=«%s», which WINS over lxqt.conf: %s",
		              why ? "⛔" : "⚠", session, CHIAVE, era,
		              why ? why : "set to «true» there too");
		g_clear_pointer(&why, g_free);
	}

	/* ⛔ AND THE EFFECTIVE VALUE IS RE-READ, with liblxqt's precedence. */
	if (g_file_test(session, G_FILE_TEST_EXISTS))
		read_ini_qt(session_reread, session, NULL);
	if (g_file_test(lxqt, G_FILE_TEST_EXISTS))
		read_ini_qt(lxqt_user, lxqt, NULL);
	effective = effective_value(session_reread, system_session, "General", CHIAVE);
	if (!effective)
		effective = effective_value(lxqt_user, system_lxqt, "Screensaver", CHIAVE);
	if (g_strcmp0(effective, "true") == 0)
		registro_dice(LOG_SESSION,
		              "⭐ LXQt: effective %s = true, RE-READ (session.conf, then "
		              "lxqt.conf [Screensaver]: %s) — «Lock screen» closes "
		              "lxqt-leave without locking and without error windows",
		              CHIAVE, in_lxqt ? in_lxqt : "unknown");
	else
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: effective %s is NOT true (I re-read «%s»)", CHIAVE,
		              effective ? effective : "nothing: it stays empty, and lxqt-leave "
		                                      "hangs");
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 14 — THE LXQt SETTINGS: WRITE, RE-READ, SAY WHETHER IT IS IN FORCE.
 *
 * ⛔⛔ IDLENESS, and the trap is `LESSONS.md` §1.9 in pure form: writing
 *     `enableIdlenessWatcher=false` IS NOT ENOUGH.  `[R]` lxqt-powermanagement
 *     2.1.0 `src/powermanagementd.cpp`: if `runCheckLevel` < 1 the daemon
 *     runs `performRunCheck()`, which does `setIdlenessWatcherEnabled(true)` —
 *     that is it **rewrites our key to true** at first start (and shows a
 *     «first start» notification).  ⇒ BOTH are written: `runCheckLevel=1`
 *     (= `CURRENT_RUNCHECK_LEVEL`) switches the check off, and the key stays.
 *     https://raw.githubusercontent.com/lxqt/lxqt-powermanagement/2.1.0/src/powermanagementd.cpp
 * ⚠ The keys are top-level in `LXQt::Settings("lxqt-powermanagement")`
 *   (`config/powermanagementsettings.cpp`), that is `[General]` in QSettings'
 *   INI format, in the user's file `~/.config/lxqt/lxqt-powermanagement.conf`.
 *   ⭐ `~/.config` and not `g_get_user_config_dir()`: the session environment
 *   does not carry `XDG_CONFIG_HOME`, so LXQt looks there.
 * ⚠ The price, declared as on XFCE: it is the USER's file.  If the same
 *   user opens LXQt in front of the machine, the idleness watcher
 *   stays off.  ⭐ PHASE 15, D-018 — ALLOWED (standby), like the lock
 *   command of `block_lxqt()` (lock): the decision of 25 Sep 2026.
 *   The panel and the menu entries, instead, go into the SESSION.
 * ⚠ ONLY what must be touched is touched: the file is read, two keys are changed,
 *   the others stay.  If it cannot be read (a format GKeyFile does not
 *   understand) it is NOT rewritten: it is said, and we carry on with less.
 *
 * And the three things that are NOT written:
 *   · `compositor=` in `session.conf` — ⛔ `[R]` the wizard for an empty `compositor`
 *     is launched by THE upstream SCRIPT (`labwc -S lxqt-config-session`),
 *     not by `lxqt-session`, which in 2.1.1 does not read that key
 *     (`lxqtmodman.cpp`).  With our launcher the key has no readers;
 *   · lock set to `/bin/false` — ⛔ it would open a MODAL window («Screen
 *     Saver Error»): not written.  ⚠ The lock IS written, but as `true`
 *     (increment 4, `block_lxqt()` further below): empty was NOT inert.
 *   · the D-Bus inhibition — it does not exist (`session_inhibit()`).
 */
/*
 * ⭐⭐ 15 Oct 2026 — THE ORPHAN pcmanfm-qt PROFILE: after a reboot, the LXQt
 *     desktop came back BLACK (no wallpaper, the icons and the panel there).
 *
 * `[M]` T10 on debian13-lxqt (box, 3 runs out of 3): the first session shows
 * the Debian wallpaper; the reboot ends the session with everything at once
 * (labwc and its clients are stopped together), `pcmanfm-qt --desktop` starts
 * saving its settings, the compositor is already gone («The Wayland connection
 * broke»), and it dies after creating `~/.config/pcmanfm-qt/lxqt/` but BEFORE
 * writing `settings.conf` in it.  At the next session that EMPTY folder is the
 * whole fault:
 * `[R]` pcmanfm-qt 2.1.0 `settings.cpp:165-187` (`Settings::profileDir`): the
 * system profiles (`/etc/xdg/pcmanfm-qt/lxqt/settings.conf`, where Debian puts
 * `Wallpaper=` and `WallpaperMode=zoom`) are read ONLY IF THE USER'S FOLDER
 * DOES NOT EXIST.  If it exists, `settings.conf` is read from it, and a missing
 * file means the built-in defaults: `WallpaperMode=none`, `BgColor=#000000`.
 * ⇒ black, for every session after, until someone opens the desktop settings.
 * `[M]` In the black session: copying the system `settings.conf` into the empty
 * folder and restarting pcmanfm-qt brings the wallpaper back (T1C PASS).
 *
 * ⭐ The cure, BEFORE the birth, and only in the broken state (folder there,
 *    `settings.conf` not there):
 *   · the folder is EMPTY ⇒ it is removed (`g_rmdir`, only if empty): pcmanfm-qt
 *     goes back to the system profile by itself, and no user file is written;
 *   · it holds something else (e.g. `recent-files.conf`) ⇒ the system
 *     `settings.conf` that pcmanfm-qt itself would have read is copied there,
 *     looked for in the session's `XDG_CONFIG_DIRS` order (`/etc`, `/etc/xdg`,
 *     `/usr/share`, as `system_files()`).  It is what pcmanfm-qt writes on its
 *     first clean exit: no choice of the user is changed, there was none.
 * ⛔ A `settings.conf` that exists is NEVER touched: it is the user's.
 * ⛔ A SYMLINK in place of the folder (or of `settings.conf`) is left alone: it
 *    is a choice of the user, and following it would write OUT of the home
 *    (`[M]` 15 Oct 2026, `benches/21-session-orphan-test.c`: before this guard a
 *    link to a foreign folder got the system `settings.conf` written into it).
 *
 * ⚠ `ORPHAN_PROFILE_SYSTEM_DIRS` exists only so that the test can point the
 *   system folders at a temporary one (`make test-session`); the product is
 *   built without it and keeps the three folders below.
 */
#ifndef ORPHAN_PROFILE_SYSTEM_DIRS
#define ORPHAN_PROFILE_SYSTEM_DIRS "/etc", "/etc/xdg", "/usr/share"
#endif
static void orphan_profile_pcmanfm_lxqt(void)
{
	static const char *const DIRS[] = { ORPHAN_PROFILE_SYSTEM_DIRS, NULL };
	g_autofree char *folder = g_build_filename(g_get_home_dir(), ".config", "pcmanfm-qt",
	                                           "lxqt", NULL);
	g_autofree char *file = g_build_filename(folder, "settings.conf", NULL);
	g_autoptr(GError) mistake = NULL;
	g_autofree char *content = NULL;
	gsize size = 0;
	GStatBuf what = { 0 };

	/* `g_lstat`, not `g_file_test(IS_DIR)`: the latter follows a symlink. */
	if (g_lstat(folder, &what) != 0 || !S_ISDIR(what.st_mode))
		return; /* no folder (pcmanfm-qt's fallback), or not a real folder */
	if (g_file_test(file, G_FILE_TEST_EXISTS | G_FILE_TEST_IS_SYMLINK))
		return; /* the user's file — a dangling link too is the user's */

	if (g_rmdir(folder) == 0) {
		registro_dice(LOG_SESSION,
		              "⭐ LXQt: %s was there EMPTY (a pcmanfm-qt that died before saving, "
		              "e.g. at a reboot) — removed: with it pcmanfm-qt ignores the system "
		              "profile and the desktop is BLACK, without it the wallpaper comes back",
		              folder);
		return;
	}
	for (int i = 0; DIRS[i]; i++) {
		g_autofree char *system = g_build_filename(DIRS[i], "pcmanfm-qt", "lxqt",
		                                           "settings.conf", NULL);

		if (!g_file_get_contents(system, &content, &size, NULL))
			continue;
		if (!g_file_set_contents(file, content, (gssize) size, &mistake)) {
			registro_dice(LOG_SESSION,
			              "⛔ LXQt: %s has no settings.conf and I cannot copy %s there (%s): "
			              "pcmanfm-qt will start WITHOUT wallpaper (black desktop)",
			              folder, system, mistake->message);
			return;
		}
		registro_dice(LOG_SESSION,
		              "⭐ LXQt: %s had no settings.conf (a pcmanfm-qt that died before "
		              "saving) — copied %s there, the profile pcmanfm-qt would have "
		              "read: without it the desktop is BLACK",
		              folder, system);
		return;
	}
	registro_dice(LOG_SESSION,
	              "⚠ LXQt: %s has no settings.conf and no system profile was found "
	              "(/etc, /etc/xdg, /usr/share): pcmanfm-qt starts with its own "
	              "defaults (no wallpaper)",
	              folder);
}

static void settings_lxqt(void)
{
	g_autofree char *file = g_build_filename(g_get_home_dir(), ".config", "lxqt",
	                                         "lxqt-powermanagement.conf", NULL);
	g_autofree char *why = NULL;
	g_autofree char *active = NULL;
	g_autofree char *level = NULL;

	orphan_profile_pcmanfm_lxqt();
	/* ⚠ If the file cannot be read, `write_qt_key()` does NOT rewrite it, and the
	 *   dangerous menu entries below are hidden all the same. */
	active = write_qt_key(file, "General", "enableIdlenessWatcher", "false", &why);
	if (!why)
		level = write_qt_key(file, "General", "runCheckLevel", "1", &why);
	if (why)
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: %s %s.  ⚠ The idleness watcher stays as it is",
		              file, why);
	else if (g_strcmp0(active, "false") == 0 && g_strcmp0(level, "1") == 0)
		registro_dice(LOG_SESSION,
		              "⭐ LXQt: %s [General] enableIdlenessWatcher=false and "
		              "runCheckLevel=1, RE-READ — the idleness watcher is "
		              "off, and the daemon does not turn it back on at first start",
		              file);
	else
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: %s is NOT in force (I re-read enableIdlenessWatcher=«%s», "
		              "runCheckLevel=«%s»)",
		              file, active ? active : "unknown", level ? level : "unknown");
	registro_dice(LOG_SESSION,
	              "LXQt: I do not write «compositor=» (with our launcher it has no "
	              "readers); the lock command I write further below as «true», "
	              "because /bin/false would open a modal window");

	/*
	 * ⭐⭐ PHASE 14, increment 2 — THE DANGEROUS MENU ENTRIES ARE HIDDEN.
	 *     `DECISIONS.md` §4.7 (commit af9a19e): away with suspend, lock,
	 *     reboot, power-off.  ⛔ «Log Out» STAYS (§4.1-ter): `lxqt-logout`
	 *     is NOT in the list, on purpose.
	 *
	 * ⭐ HOW: a `.desktop` with the SAME NAME, with `Hidden=true` and
	 *   `NoDisplay=true`, in a folder that comes BEFORE the system ones.
	 *   `[R]` libqtxdg 4.1.0:
	 *   · `xdgmenureader.cpp:320-325` — the `AppDir`s are the user's folder
	 *     and then `XDG_DATA_DIRS` in order;
	 *   · `xdgmenuapplinkprocessor.cpp:156-167` — for each id the first
	 *     found wins, and discarded entries do not enter the menu;
	 *   · `xdgdesktopfile.cpp:1346-1373` — `NoDisplay` and `Hidden` true ⇒ the
	 *     entry is discarded.
	 *   `[R]` lxqt-menu-data 2.1.0 `lxqt-applications.menu:206-223`: it is the
	 *   menu's «Leave» folder, where these six live.
	 * ⛔⛔ PHASE 15, D-018 — NO LONGER in `~/.local/share/applications`: the
	 *     user's settings are not touched (decision of 25 Sep 2026),
	 *     and a menu is not lock, reboot, suspend or standby.  ⇒ The entries
	 *     live in the SESSION DATA folder
	 *     (`$XDG_RUNTIME_DIR/remotix/data-lxqt`), at the head of `XDG_DATA_DIRS`
	 *     (`compose_environment()`): they hold for the session we needs, and
	 *     the user at the monitor has their whole menu.
	 * ⚠ The price: a user file with the same id in
	 *   `~/.local/share/applications` comes FIRST and wins.  It is checked and
	 *   said (the entry stays).  One with `X-REMOTIX` is a leftover of earlier
	 *   versions: it hides all the same, and is not touched.
	 *
	 * ⛔ THE TWO LEFTOVERS THESE SIX DO NOT CURE — cured by increment 4,
	 *    `lxqt_panel()` and `block_lxqt()` at the end of this function:
	 *   1. the «Leave» button inside the fancymenu is FIXED CODE, not a
	 *      menu entry (`[R]` lxqt-panel 2.1.4 `lxqtfancymenuwindow.cpp:
	 *      165-169, 315-318`, and no key removes it): it opens `lxqt-leave`,
	 *      where Shut Down/Reboot/Suspend/Hibernate are GREY because polkit/logind
	 *      say no (belt 1 of §4.7, as on XFCE);
	 *   2. ⛔⛔ in there «Lock screen» is ALWAYS active (`[R]` lxqt-session
	 *      2.1.1 `lxqt-leave/leavedialog.cpp:76-78`), and it was NOT «inert» as
	 *      this comment said: with an empty `lock_command_wayland`
	 *      `lockScreen()` exits WITHOUT emitting `done` (`[R]` liblxqt 2.1.0
	 *      `lxqtscreensaver.cpp:281-292`), and `lxqt-leave` stays HUNG in its
	 *      `loop.exec()` (`leavedialog.cpp:113-118`) — `[M]` still alive 34 s
	 *      after the click.
	 */
	{
		static const char *const DANGEROUS[] = {
			"lxqt-leave", "lxqt-lockscreen", "lxqt-suspend",
			"lxqt-hibernate", "lxqt-shutdown", "lxqt-reboot", NULL
		};
		const int how_many = G_N_ELEMENTS(DANGEROUS) - 1;
		g_autofree char *data = lxqt_session_data_folder();
		g_autofree char *applications = data ? g_build_filename(data, "applications", NULL)
		                                     : NULL;
		g_autofree char *user_share = g_build_filename(g_get_home_dir(), ".local", "share",
		                                                "applications", NULL);
		int hidden = 0;

		if (!applications || g_mkdir_with_parents(applications, 0700) != 0) {
			registro_dice(LOG_SESSION,
			              "⛔ LXQt: the session data folder (%s) cannot be created "
			              "(%s): 0/%d entries hidden — suspend, lock, reboot and "
			              "power-off stay in the menu (grey because of polkit, but visible)",
			              applications ? applications : "without XDG_RUNTIME_DIR",
			              g_strerror(errno), how_many);
			/* ⚠ `goto` and not `return`: the panel and the lock are cured
			 *   even if the entries could not be hidden. */
			goto panel;
		}
		for (int i = 0; DANGEROUS[i]; i++) {
			g_autofree char *name = g_strconcat(DANGEROUS[i], ".desktop", NULL);
			g_autofree char *entry = g_build_filename(applications, name, NULL);
			g_autofree char *its = g_build_filename(user_share, name, NULL);
			g_autofree char *content = NULL;
			g_autoptr(GKeyFile) rereads = g_key_file_new();
			g_autoptr(GError) fault = NULL;
			const char *wins = entry;

			content = g_strdup_printf("[Desktop Entry]\n"
			                            "Type=Application\n"
			                            "Name=%s\n"
			                            "Hidden=true\n"
			                            "NoDisplay=true\n"
			                            "X-REMOTIX=hidden by REMOTIX in the session "
			                            "(DECISIONS.md §4.7, D-018)\n",
			                            DANGEROUS[i]);
			if (!g_file_set_contents(entry, content, -1, &fault))
				registro_dice(LOG_SESSION, "⛔ LXQt: %s NOT written (%s)", entry,
				              fault->message);

			/* ⛔ AND WHAT WINS IS RE-READ: the user's file, if there is one,
			 *    comes before ours. */
			if (g_file_test(its, G_FILE_TEST_EXISTS)) {
				wins = its;
				registro_dice(LOG_SESSION,
				              "⚠ LXQt: %s exists in the user's folder and wins over "
				              "ours: its Hidden counts (I do not touch it)",
				              its);
			}
			if (g_key_file_load_from_file(rereads, wins, G_KEY_FILE_NONE, NULL) &&
			    g_key_file_get_boolean(rereads, "Desktop Entry", "Hidden", NULL))
				hidden++;
		}
		if (hidden == how_many)
			registro_dice(LOG_SESSION,
			              "⭐ LXQt: %d/%d entries hidden IN THE SESSION (%s), RE-READ; "
			              "\"Log Out\" stays",
			              hidden, how_many, applications);
		else
			registro_dice(LOG_SESSION,
			              "⛔ LXQt: %d/%d entries hidden, RE-READ — %d are missing, "
			              "and stay in the menu (grey because of polkit, but visible); "
			              "\"Log Out\" stays",
			              hidden, how_many, how_many - hidden);
	}
panel:
	lxqt_panel();
	block_lxqt();
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 15, D-017 — THE SESSION'S XFCONF: the user's settings
 *      are not touched, except lock, reboot, suspend and standby
 *      (the user's decision of 25 Sep 2026).
 *
 * ⛔ Until now `xfconf-query` wrote into the USER's channels even what
 *    is not of those four kinds — the logout belt, «Switch
 *    User» in the exit dialog — and deleted `~/.cache/sessions`.
 *
 * ⭐ THE ROAD: xfconf has LOCKED properties.  `[R]` xfconf 4.20
 *    `xfconfd/xfconf-backend-perchannel-xml.c`:
 *    · `load_channel()` reads the system files in every folder of
 *      `XDG_CONFIG_DIRS` (from weakest to strongest), THEN the
 *      user's;
 *    · a `<property … locked="*">` in a SYSTEM file wins, and the user's
 *      with the same name is skipped («not system file, prop
 *      already locked, pass on this one»); `set_property` refuses it.
 *    ⇒ A channel file in a SESSION folder, at the head of
 *      `xfconfd`'s `XDG_CONFIG_DIRS`, holds for the session and writes
 *      nothing into the user's.
 *
 * ⚠ `xfconfd` is NOT a child of the session: it is a user unit
 *   (`xfconfd.service`, activated by the bus — `[R]` xfconf since 2015,
 *   `org.xfce.Xfconf.service`: `SystemdService=xfconfd.service`), and its
 *   environment is the manager's.  ⇒ The folder is given to it by a drop-in in
 *   `user.control` (the recipe of `write_dropin()`), and if `xfconfd` is already running
 *   it is restarted: it reads the files once, when a channel is opened.
 *
 * ⭐ And instead of `rm -rf ~/.cache/sessions` (which also took away the
 *   sessions saved BY THE USER at the monitor): `SessionName=REMOTIX` and
 *   `SaveOnExit=false`, locked.  `[R]` xfce4-session 4.20.2
 *   `xfsm-manager.c`: the session is looked up by NAME (`/general/SessionName`,
 *   by default «Default») and, if it is not there, the default one is born; it is saved only
 *   with `SaveOnExit` (`:1278`).  ⇒ The remote session never finds anything
 *   saved, and never saves anything.
 *
 * ⚠ THE PRICES, declared:
 *   · the drop-in and the folder live as long as the user manager (they are in
 *     `XDG_RUNTIME_DIR`): an XFCE opened at the monitor on the SAME manager
 *     would see the same locks, as long as the manager lives;
 *   · if `xfconfd` is not a systemd unit on this machine, the
 *     drop-in does not count: the re-read says so, and the session keys
 *     stay at their defaults (the logout belt stays `XFCE4_SESSION_COMPOSITOR`).
 */
struct key_xfconf {
	const char *group; /* the property's folder in the channel */
	const char *name;
	const char *kind;
	const char *value;
};

static const struct key_xfconf XFCE_SESSION[] = {
	/* the second logout belt (the first is XFCE4_SESSION_COMPOSITOR) */
	{ "general", "WaylandLogoutCommand", "string", "/bin/true" },
	/* the remote session neither finds nor saves sessions */
	{ "general", "SessionName", "string", "REMOTIX" },
	{ "general", "SaveOnExit", "bool", "false" },
	/* the «Log Out» dialog (decision of 21 Sep 2026): «Switch User».
	 * ⚠ Suspend, Hibernate and Hybrid Sleep NOT: they are suspend, that is
	 *   ALLOWED, and they live in the user's channel (`session_settings()`). */
	{ "shutdown", "ShowSwitchUser", "bool", "false" },
	{ NULL, NULL, NULL, NULL },
};

static void xfce_session_xfconf(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autofree char *cfg = NULL;
	g_autofree char *channels = NULL;
	g_autofree char *file = NULL;
	g_autofree char *dropin_dir = NULL;
	g_autofree char *dropin = NULL;
	g_autofree char *line = NULL;
	g_autofree char *effect = NULL;
	g_autoptr(GString) xml = g_string_new(NULL);
	g_autoptr(GError) mistake = NULL;
	const char *group = NULL;
	char *reload[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *restart[] = { "systemctl", "--user", "try-restart", "xfconfd.service", NULL };
	char *show_cmd[] = { "systemctl", "--user", "show", "-p", "Environment", "--value",
		           "xfconfd.service", NULL };
	int in_effect = 0, how_many = 0;

	if (!runtime || !*runtime) {
		registro_dice(LOG_SESSION,
		              "⛔ XFCE, D-017: without XDG_RUNTIME_DIR no session xfconf — "
		              "the session keys stay at their defaults");
		return;
	}
	cfg = g_build_filename(runtime, "remotix", "xdg-xfce", NULL);
	channels = g_build_filename(cfg, "xfce4", "xfconf", "xfce-perchannel-xml", NULL);
	file = g_build_filename(channels, "xfce4-session.xml", NULL);

	g_string_append(xml, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
	                     "<!-- REMOTIX (D-017): they hold for the remote session, locked; "
	                     "the user's channel is not touched -->\n"
	                     "<channel name=\"xfce4-session\" version=\"1.0\">\n");
	for (int i = 0; XFCE_SESSION[i].name; i++) {
		if (g_strcmp0(group, XFCE_SESSION[i].group) != 0) {
			if (group)
				g_string_append(xml, "  </property>\n");
			group = XFCE_SESSION[i].group;
			g_string_append_printf(xml, "  <property name=\"%s\" type=\"empty\">\n", group);
		}
		g_string_append_printf(xml,
		                       "    <property name=\"%s\" type=\"%s\" value=\"%s\" "
		                       "locked=\"*\"/>\n",
		                       XFCE_SESSION[i].name, XFCE_SESSION[i].kind,
		                       XFCE_SESSION[i].value);
	}
	g_string_append(xml, "  </property>\n</channel>\n");
	if (g_mkdir_with_parents(channels, 0700) != 0 ||
	    !g_file_set_contents(file, xml->str, -1, &mistake)) {
		registro_dice(LOG_SESSION, "⛔ XFCE, D-017: %s NOT written (%s)", file,
		              mistake ? mistake->message : g_strerror(errno));
		return;
	}

	dropin_dir = g_build_filename(runtime, "systemd", "user.control", "xfconfd.service.d",
	                                   NULL);
	dropin = g_build_filename(dropin_dir, "zz-remotix-session.conf", NULL);
	line = g_strdup_printf("[Service]\nEnvironment=XDG_CONFIG_DIRS=%s:%s\n", cfg,
	                       g_getenv("XDG_CONFIG_DIRS") && *g_getenv("XDG_CONFIG_DIRS")
	                               ? g_getenv("XDG_CONFIG_DIRS")
	                               : "/etc/xdg");
	g_clear_error(&mistake);
	if (g_mkdir_with_parents(dropin_dir, 0700) != 0 ||
	    !g_file_set_contents(dropin, line, -1, &mistake)) {
		registro_dice(LOG_SESSION, "⛔ XFCE, D-017: xfconfd drop-in NOT written (%s): %s",
		              dropin, mistake ? mistake->message : g_strerror(errno));
		return;
	}
	run(reload);
	effect = ask(show_cmd);
	if (!effect || !strstr(effect, cfg))
		registro_dice(LOG_SESSION,
		              "⚠ XFCE, D-017: the manager does not show the session folder "
		              "in the environment of xfconfd.service («%s») — the re-read will say whether it holds",
		              effect ? g_strstrip(effect) : "unknown");
	/* ⛔ xfconfd reads the files when a channel is opened: if it is running, it restarts. */
	run(restart);

	/* ⛔ AND IT IS RE-READ, as xfce4-session will read it: the EFFECTIVE value. */
	for (int i = 0; XFCE_SESSION[i].name; i++) {
		g_autofree char *key = g_strdup_printf("/%s/%s", XFCE_SESSION[i].group,
		                                          XFCE_SESSION[i].name);
		char *reread_cmd[] = { "xfconf-query", "-c", "xfce4-session", "-p", key, NULL };
		g_autofree char *read = ask(reread_cmd);

		how_many++;
		if (read && g_strcmp0(g_strstrip(read), XFCE_SESSION[i].value) == 0)
			in_effect++;
		else
			registro_dice(LOG_SESSION,
			              "⛔ XFCE, D-017: xfce4-session %s is NOT in force (I re-read «%s», "
			              "wanted «%s»)",
			              key, read ? read : "nothing", XFCE_SESSION[i].value);
	}
	if (in_effect == how_many)
		registro_dice(LOG_SESSION,
		              "⭐ XFCE, D-017: SESSION xfconf in force (%s, %d keys "
		              "locked, RE-READ): logout belt, SessionName=REMOTIX, "
		              "SaveOnExit=false, no «Switch User» — the user's channel "
		              "is not touched",
		              file, how_many);
	else
		registro_dice(LOG_SESSION,
		              "⛔ XFCE, D-017: session xfconf in force for %d keys out of %d.  "
		              "⚠ The logout belt stays XFCE4_SESSION_COMPOSITOR; «Switch "
		              "User» stays in the dialog",
		              in_effect, how_many);
}

void session_settings(void)
{
	/* ⛔ PHASE 12 — before opening a schema: on Plasma these keys do not
	 *    exist, and Plasma's levers (lock, suspend, menu) are work for
	 *    the later increments.  ⚠ The desktop's lock is already switched off by the
	 *    start line (`--no-lockscreen`, `write_dropin`). */
	if (e_kde()) {
		registro_dice(LOG_SESSION,
		              "⚠ Plasma: the session settings (suspend, menu) "
		              "I do not set yet — phase 12, increments after the first.  The "
		              "desktop's lock is switched off by the start line");
		return;
	}
	/*
	 * ⭐ PHASE 13 — on XFCE: the logout belt, power, lock and the
	 *    exit dialog; the panel entries are removed by `session_inhibit()`.
	 *
	 * ⛔ THE LOGOUT BELT, which is the only one that cannot wait: if
	 *    `xfce4-session` decides the compositor is not good, at logout it runs
	 *    `loginctl terminate-session ''` and **kills REMOTIX's logind
	 *    session**.  The environment already carries `XFCE4_SESSION_COMPOSITOR` written
	 *    correctly; this is the second belt, and it takes precedence over the first.
	 *
	 * ⛔⛔ AND IT IS RE-READ.  `xfconf-query` exits with **zero even when the daemon
	 *     refused** and put the previous value back: the API is asynchronous and the
	 *     local cache answers first.  ⇒ A successful write is not an applied
	 *     configuration (`STUDIES.md` §xfce §10.6), and it is
	 *     `LESSONS.md` §1.9 moved from measurement to configuration.
	 */
	if (e_xfce()) {
		/* ⭐ PHASE 15, D-017 — what the session must have and which is NOT
		 *    lock, reboot, suspend or standby: in the SESSION xfconf
		 *    (the logout belt, «Switch User» in the exit dialog, and the saved
		 *    session in place of the old `rm -rf ~/.cache/sessions`).  The
		 *    box is above `xfce_session_xfconf()`. */
		xfce_session_xfconf();

		/*
		 * ⛔⛔ THE OUTPUT IS NOT SWITCHED OFF — `STUDIES.md` §xfce §10.2.
		 *
		 * `[R]` `xfce4-power-manager` 4.20.0 is born with `dpms-enabled` TRUE and
		 * `dpms-on-ac-sleep` = **10 minutes** (`common/xfpm-config.h`), and on
		 * Wayland it translates them into `zwlr_output_power_v1(OFF)`: labwc switches off
		 * the output, and capture receives `failed`.  ⇒ With `dpms-enabled` false
		 * `refresh()` (`xfpm-dpms.c`) arms NO timer, and the change also holds
		 * on the fly (`settings_changed`).
		 * ⭐ WHY xfconf and not `org.freedesktop.PowerManagement.Inhibit`:
		 *    xfce4-power-manager **has no D-Bus activation** — an inhibition
		 *    asked for before it starts would fail (it is powerdevil's `ServiceUnknown`
		 *    on KDE) and would live as long as our connection.  The
		 *    key is there before the daemon is born, and it reads it when born.
		 * ⚠ The price, declared: it is written in the USER's channel.  If the
		 *   same user opens XFCE in front of the machine, their screen no longer
		 *   switches off by itself.
		 * ⭐ PHASE 15, D-017 — ALLOWED, and they stay in the user's: DPMS and
		 *    idleness (standby, suspend) and, below, `LockCommand`
		 *    (lock) — the user's decision of 25 Sep 2026.
		 */
		xfconf_put("xfce4-power-manager", "/xfce4-power-manager/dpms-enabled", "bool",
		             "false",
		             "the session's screen does not switch off after 10 minutes (DPMS "
		             "of xfce4-power-manager, which on wlroots SWITCHES OFF the output and makes "
		             "capture fail)");
		/* ⚠ They are already 0 («never») by default: they are written so as not to inherit what
		 *   the user set themselves.  Suspend is stopped by sleep.conf anyway
		 *   (§4.7) — this removes the LIE, that is the attempt that fails. */
		xfconf_put("xfce4-power-manager", "/xfce4-power-manager/inactivity-on-ac", "uint",
		             "0", "no suspend on idleness, on mains power");
		xfconf_put("xfce4-power-manager", "/xfce4-power-manager/inactivity-on-battery",
		             "uint", "0", "no suspend on idleness, on battery");

		/*
		 * ⛔ THE LOCK — `STUDIES.md` §xfce §10.3, and the user's decision of 21
		 *    Sep 2026.  `[R]` libxfce4ui 4.20.1, `xfce_screensaver_lock()`
		 *    (`xfce-screensaver.c:564-596`): if `LockCommand` is there, it runs it and
		 *    **returns its result without trying anything else**.  ⇒ With
		 *    `/bin/false` `xflock4` does not lock (it calls xfce4-session's `Lock`
		 *    and looks at the answer), the D-Bus method does not lock,
		 *    the panel button does not lock, and nothing locks before a
		 *    suspend (`lock-screen-suspend-hibernate`).
		 * ⚠ `/bin/false` and not `/bin/true`: whoever asks for a lock must be
		 *   told «it is not locked», not «done».  And NOT the empty string: it means
		 *   «not set», and the D-Bus chain resumes (`:299-305`).
		 * ✅ The other two lockers do not start here: `xfce4-screensaver` is pure X11
		 *    and exits if GDK is not X11, and `GDK_BACKEND=wayland` is bare;
		 *    `light-locker` wants LightDM and X11.
		 */
		xfconf_put("xfce4-session", "/general/LockCommand", "string", "/bin/false",
		             "the screen lock is off: locking belongs to REMOTIX (§4.3)");

		/*
		 * ⛔ THE «LOG OUT» DIALOG — the user's decision of 21 Sep 2026.
		 *
		 * `[R]` xfce4-session 4.20.2, `xfsm-logout-dialog.c:263-374`: Suspend,
		 * Hibernate and Hybrid Sleep have a key that REMOVES them; ⛔ Restart and
		 * Shut Down do not — they stay GREY because of polkit (belt 1 of §4.7).
		 * ⭐ PHASE 15, D-017 — these three are SUSPEND, that is ALLOWED
		 *    (decision of 25 Sep 2026): they stay in the user's channel.
		 *    «Switch User» (`ShowSwitchUser`) instead is SESSION, in
		 *    `xfce_session_xfconf()`.
		 */
		xfconf_put("xfce4-session", "/shutdown/ShowSuspend", "bool", "false",
		             "no «Suspend» in the exit dialog");
		xfconf_put("xfce4-session", "/shutdown/ShowHibernate", "bool", "false",
		             "no «Hibernate» in the exit dialog");
		xfconf_put("xfce4-session", "/shutdown/ShowHybridSleep", "bool", "false",
		             "no «Hybrid Sleep» in the exit dialog");

		registro_dice(LOG_SESSION,
		              "XFCE: the entries of the panel's action button I remove "
		              "when the panel exists (session_inhibit): before that, for a "
		              "new user, its plugin does not have a number yet");
		return;
	}
	/*
	 * ⭐ PHASE 14 — on LXQt: idleness, the menu entries, the panel
	 *    (fancymenu→mainmenu) and the lock command set to `true`.  And the things that
	 *    are NOT written, each with its reason.
	 */
	if (e_lxqt()) {
		settings_lxqt();
		return;
	}
	struct schema_open wayland = open_schema("org.gnome.mutter.wayland");
	struct schema_open shell = open_schema("org.gnome.shell");
	struct schema_open energy = open_schema("org.gnome.settings-daemon.plugins.power");
	struct schema_open session = open_schema("org.gnome.desktop.session");
	struct schema_open screensaver = open_schema("org.gnome.desktop.screensaver");
	struct schema_open blocks = open_schema("org.gnome.desktop.lockdown");
	const char *empty[] = { NULL };
	int removed = 0;
	/*
	 * ⛔⛔ PHASE 15, D-015 — THE TWO KINDS OF KEYS (the user's decision of
	 *     25 Sep 2026: «The user's settings are not touched EXCEPT
	 *     those concerning screen lock, system reboot, suspend and
	 *     standby: these are settings dangerous for other users
	 *     present on the machine»).
	 *
	 *   · ALLOWED, written in the USER's dconf and persistent
	 *     (`gnome_set_user()`): `sleep-inactive-ac-type`,
	 *     `sleep-inactive-battery-type` (suspend), `idle-delay`
	 *     (standby), `lock-enabled` (lock);
	 *   · SESSION, written ONLY in the session dconf (GSettings of the
	 *     child, which has the profile of `session_dconf_prepare()`): the
	 *     Ctrl+Alt+F1…F12, `always-show-log-out`, `disable-user-switching` (and
	 *     the layout, in `input.c`).  ⛔ Without the session dconf
	 *     they are NOT written: they would end up in the user's.
	 */
	const gboolean per_session = session_dconf_of_session();

	if (!per_session)
		registro_dice(LOG_SESSION,
		              "⛔ D-015: the session dconf is NOT in force — the "
		              "SESSION keys (Ctrl+Alt+F*, «Log Out…» always, «Switch User») I do NOT "
		              "write: they would end up in the user's settings.  The allowed ones "
		              "(lock, suspend, standby) are written anyway");

	for (int i = 0; per_session && VT_SHORTCUTS[i]; i++)
		if (schema_has_key(&wayland, VT_SHORTCUTS[i], "org.gnome.mutter.wayland") &&
		    g_settings_set_strv(wayland.settings, VT_SHORTCUTS[i], empty))
			removed++;
	if (removed)
		registro_dice(LOG_SESSION,
		              "⭐ removed %d Ctrl+Alt+F1…F12 shortcuts out of 12, in the SESSION: in "
		              "headless mode there is no virtual console to switch to, and Mutter "
		              "swallowed them without being able to honour them (they are NON_MASKABLE: not even the "
		              "page could take them back)",
		              removed);

	/*
	 * ⭐ «Log Out…» MUST BE THERE — `DECISIONS.md` §4.1-ter, decided by the user on 15
	 *    August 2026: it is the only gesture that ends the session.
	 *
	 * `[R]` `systemActions.js:394-410`: the entry appears only if
	 * `always-show-log-out` **or** there are several users **or** more than one
	 * session in `/usr/share/…-sessions`.  ⇒ On a machine with one user and one
	 * session only it DOES NOT APPEAR, and without it logout does not exist.
	 * ⭐ D-015: SESSION.
	 */
	if (per_session && schema_has_key(&shell, "always-show-log-out", "org.gnome.shell") &&
	    g_settings_set_boolean(shell.settings, "always-show-log-out", TRUE))
		registro_dice(LOG_SESSION,
		              "⭐ «Log Out…» on (always-show-log-out, in the SESSION): without it, on "
		              "a machine with a single user the entry does NOT appear, and the logout "
		              "of §4.1-ter would not exist");

	/*
	 * ⛔ AUTOMATIC SUSPEND — `DECISIONS.md` §4.7, third belt, and it is the
	 *    half that removes the LIE from the screen: polkit and `sleep.conf`
	 *    prevent the fact, this line prevents the «Automatic
	 *    Suspend» notification followed by a silent failure.
	 * ⭐ D-015: ALLOWED — in the user's, persistent.
	 */
	if (gnome_set_user(&energy, "org.gnome.settings-daemon.plugins.power",
	                       "sleep-inactive-ac-type", g_variant_new_string("nothing")) &&
	    gnome_set_user(&energy, "org.gnome.settings-daemon.plugins.power",
	                       "sleep-inactive-battery-type", g_variant_new_string("nothing")))
		registro_dice(LOG_SESSION,
		              "⭐ automatic suspend off (it was «suspend» at 900 s, "
		              "upstream and on Debian): the machine belongs to several people, and whoever "
		              "suspends it takes it away from everyone");

	/* ⛔ And the screen locker stays OFF — §4.3: on GNOME the desktop's one does not
	 *    show a lock, it REVOKES our capture and input.  ⭐ D-015: ALLOWED. */
	if (gnome_set_user(&session, "org.gnome.desktop.session", "idle-delay",
	                       g_variant_new_uint32(0)))
		registro_dice(LOG_SESSION, "⭐ desktop idleness off (idle-delay 0)");
	if (gnome_set_user(&screensaver, "org.gnome.desktop.screensaver", "lock-enabled",
	                       g_variant_new_boolean(FALSE)))
		registro_dice(LOG_SESSION,
		              "⭐ desktop screen locker off (§4.3: locking belongs to "
		              "REMOTIX, and on GNOME the desktop's one REVOKES our capture and "
		              "input instead of showing a lock)");

	/*
	 * ⛔ «SWITCH USER» GOES — the user's decision of 21 Sep 2026, evening:
	 *    *«the only entry that must remain is logout»*, the same on all desktops
	 *    (KDE removes it with KIOSK since phase 12, XFCE from the panel and the
	 *    dialog).  On GNOME the entry appears when the machine has several users
	 *    and GDM, that is exactly on the shared machine.
	 * ⚠ Only `disable-user-switching`: `disable-log-out` stays as it is.
	 * ⭐ D-015: SESSION.
	 */
	if (per_session &&
	    schema_has_key(&blocks, "disable-user-switching", "org.gnome.desktop.lockdown") &&
	    g_settings_set_boolean(blocks.settings, "disable-user-switching", TRUE))
		registro_dice(LOG_SESSION,
		              "⭐ «Switch User» removed (disable-user-switching, in the SESSION): "
		              "the only entry left is «Log Out…»");

	g_settings_sync();
	close_schema(&wayland);
	close_schema(&shell);
	close_schema(&energy);
	close_schema(&session);
	close_schema(&screensaver);
	close_schema(&blocks);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐ PHASE 12 — THE SCREEN OF THE REMOTE PLASMA SESSION DOES NOT SWITCH OFF.
 *
 * On Plasma the commander of idleness is powerdevil, and `[R]` (`STUDIES.md`
 * §kde §10.2) it has **«switch the screen off after 10 minutes» on by default**: in
 * a remote session it means the desktop going black for whoever watches.
 * ⇒ `PolicyAgent.AddInhibition(types=4)`: 4 = `ChangeScreenSettings`, which
 * IMPLIES `InterruptSession` (`powerdevilpolicyagent.cpp:737-745`); no
 * permission check, and it releases itself when our name drops.
 * ⚠ NOT `org.freedesktop.PowerManagement.Inhibit`: it maps only
 *   `InterruptSession`, and the screen would switch off anyway.
 * ⚠ The MACHINE's suspend is not here: it is stopped by the system belts
 *   of `DECISIONS.md` §4.7 (polkit and `AllowSuspend=no`), for all desktops.
 *
 * ⛔⛔ WHY A THREAD, and not a single call — `[M]` 19 Sep 2026, box
 *     `kde`, binary `6a41a28e`: called when the stage is ready, powerdevil
 *     **is not there yet** («ServiceUnknown»: it is a unit of `plasma-core.target`,
 *     it is not activated by the bus).  And the child has no GLib loop, so no
 *     `g_bus_watch_name`: who owns the name is checked every 2 s, and the
 *     inhibition is asked for every time the owner CHANGES — at the first appearance
 *     and if powerdevil restarts (the old inhibition died with it).
 *     The thread lives as long as the child, that is as long as the session.
 */
#define POWERDEVIL "org.kde.Solid.PowerManagement"
#define POWERDEVIL_STEP_US (2 * G_USEC_PER_SEC)
#define POWERDEVIL_PATIENCE_S 120

static char *owner_of(GDBusConnection *bus, const char *name)
{
	g_autoptr(GVariant) response = g_dbus_connection_call_sync(
		bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
		"GetNameOwner", g_variant_new("(s)", name), G_VARIANT_TYPE("(s)"),
		G_DBUS_CALL_FLAGS_NONE, WAIT_RESPONSE_MS, NULL, NULL);
	char *chi = NULL;

	if (response)
		g_variant_get(response, "(s)", &chi);
	return chi;
}

static gpointer powerdevil_guard(gpointer data)
{
	g_autofree char *last = NULL;
	const gint64 started = g_get_monotonic_time();
	gboolean logged_absent = FALSE;

	(void) data;
	for (;;) {
		g_autoptr(GDBusConnection) bus = sess_bus(NULL);
		g_autofree char *chi = bus ? owner_of(bus, POWERDEVIL) : NULL;

		if (!chi && !last && !logged_absent &&
		    g_get_monotonic_time() - started > POWERDEVIL_PATIENCE_S * G_USEC_PER_SEC) {
			logged_absent = TRUE;
			registro_dice(LOG_SESSION,
			              "⚠ Plasma: powerdevil did not appear within %d s: nobody "
			              "switches the screen off, and I keep watching",
			              POWERDEVIL_PATIENCE_S);
		}
		if (chi && g_strcmp0(chi, last) != 0) {
			g_autoptr(GVariant) response = NULL;
			g_autoptr(GError) mistake = NULL;
			guint32 token = 0;

			response = g_dbus_connection_call_sync(
				bus, POWERDEVIL, "/org/kde/Solid/PowerManagement/PolicyAgent",
				"org.kde.Solid.PowerManagement.PolicyAgent", "AddInhibition",
				g_variant_new("(uss)", 4u, "REMOTIX",
			                      "a remote session is alive: the screen does not "
			                      "turn off and the session is not idle"),
				G_VARIANT_TYPE("(u)"), G_DBUS_CALL_FLAGS_NONE, WAIT_RESPONSE_MS,
				NULL, &mistake);
			if (response) {
				g_variant_get(response, "(u)", &token);
				registro_dice(LOG_SESSION,
				              "⭐ Plasma: screen and idleness INHIBITED to powerdevil "
				              "%s (cookie %u, types 4 = ChangeScreenSettings ⊃ "
				              "InterruptSession)%s",
				              chi, token, last ? " — powerdevil had restarted" : "");
				g_free(last);
				last = g_steal_pointer(&chi);
			} else {
				registro_dice(LOG_SESSION,
				              "⛔ Plasma: the inhibition to powerdevil %s did NOT go through "
				              "(%s): retrying in 2 s",
				              chi, mistake ? mistake->message : "no reason given");
			}
		}
		g_usleep(POWERDEVIL_STEP_US);
	}
	return NULL;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ THE SUSPEND INHIBITION — `DECISIONS.md` §4.7, third belt.
 *
 * ⛔ THE FACT THAT MAKES IT NECESSARY, measured: `[M]` 15 August 2026, in the
 *    remote desktop the notification **«Automatic Suspend — Suspending soon
 *    because of inactivity»** appeared.  `sleep-inactive-ac-type` is `suspend` at 900 s,
 *    upstream **and** on Debian.
 *
 * ⭐ It is the THIRD belt and not a duplicate of the other two, because it acts at a
 *    different level: polkit and `sleep.conf` prevent anyone from suspending
 *    the machine; `session_settings()` takes away `gsd-power`'s wish to;
 *    this one tells the session manager **«someone is working»**, which is
 *    the only one of the three that speaks the desktop's language.
 *
 * ⛔⛔ THE FLAGS ARE 12 — `SUSPEND` (4) | `IDLE` (8) — AND NEVER THE `LOGOUT` BIT (1).
 *     With `LOGOUT` inhibited, the user's logout would be **blocked by us**:
 *     `DECISIONS.md` §4.1-ter says that «Log Out» is the only gesture that ends the
 *     session, and preventing it would take away their only door.
 *
 * Returns the cookie (0 if it failed).  ⚠ It is never released: it lasts
 * as long as the session, and dies with it.
 */
guint32 session_inhibit(void)
{
	g_autoptr(GDBusConnection) bus = sess_bus(NULL);
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GError) mistake = NULL;
	guint32 token = 0;

	if (!bus)
		return 0;

	/* ⭐ PHASE 12 — on Plasma the session manager is not this one: the screen
	 *    is kept on by a thread that waits for powerdevil
	 *    (`powerdevil_guard`, above). */
	if (e_kde()) {
		g_thread_unref(g_thread_new("powerdevil", powerdevil_guard, NULL));
		registro_dice(LOG_SESSION,
		              "Plasma: I ask powerdevil for the screen inhibition "
		              "as soon as it appears on the bus");
		return 0;
	}
	/*
	 * ⭐ PHASE 13 — on XFCE there is NO inhibition, and it is a choice with a measurement
	 *    behind it, not an oversight: `xfce4-session` **does not consult
	 *    the inhibitor** when it runs `Logout` (`STUDIES.md` §xfce §9.5), so
	 *    asking for an inhibition here would give a false ⛔ in the log and
	 *    zero protection.
	 * ⚠ What really switches the output off on this desktop is `xfce4-power-manager`,
	 *   after 10 minutes: it is stopped by `dpms-enabled=false`, written and re-read in
	 *   `session_settings()` before the birth.
	 * ⭐ And here, where the stage exists, starts the thread that removes the dangerous entries
	 *    from the panel's action button (`xfce_panel_guard`): its
	 *    target exists only after the panel is born.
	 */
	if (e_xfce()) {
		g_thread_unref(g_thread_new("pannello-xfce", xfce_panel_guard, NULL));
		registro_dice(LOG_SESSION,
		              "XFCE: I ask for no inhibition — xfce4-session does not "
		              "consult the inhibitor, and the output is kept on by "
		              "dpms-enabled=false.  I watch the panel to remove from it "
		              "lock, suspend, reboot and power-off");
		return 0;
	}
	/*
	 * ⭐ PHASE 14 — on LXQt there is NO inhibition, and here there is not even anyone to
	 *    ask: `PowerManagement.Inhibit` in LXQt **does not exist** — neither
	 *    exposed nor consumed (`STUDIES.md` §lxqt §6.2, `[✗]`, zero occurrences).
	 * ⚠ Idleness is switched off by `settings_lxqt()` before the birth; and
	 *   `lxqt-powermanagement` cannot switch the output off on Wayland (DPMS only
	 *   on xcb).  Whoever would switch it off is `swayidle` from labwc's autostart, which
	 *   our `-C` folder does not have.
	 * [?] The strongest lever, labwc's `zwp_idle_inhibit_manager_v1`, is not part of
	 *     this increment: it is measurement M5.
	 * ⚠ The dangerous panel entries (`fancymenu`, `lxqt-leave` in Debian's
	 *   quicklaunch) are NOT touched here: later increments.
	 */
	if (e_lxqt()) {
		registro_dice(LOG_SESSION,
		              "LXQt: I ask for no inhibition — LXQt has no "
		              "PowerManagement.Inhibit; idleness is switched off by the "
		              "configuration, and swayidle does not start (our autostart, empty)");
		return 0;
	}

	response = g_dbus_connection_call_sync(
		bus, "org.gnome.SessionManager", "/org/gnome/SessionManager",
		"org.gnome.SessionManager", "Inhibit",
		g_variant_new("(susu)", "REMOTIX", 0u,
	                      "a remote session is alive: the machine must "
	                      "not suspend nor consider itself idle",
	                      (guint32)(4u | 8u)),
		G_VARIANT_TYPE("(u)"), G_DBUS_CALL_FLAGS_NONE, WAIT_RESPONSE_MS, NULL,
		&mistake);

	if (!response) {
		registro_dice(LOG_SESSION,
		              "⛔ the suspend inhibition did NOT go through (%s): the "
		              "machine may fall asleep under a live session.  ⚠ The "
		              "other two belts (polkit and sleep.conf) hold anyway, but "
		              "this is the one that speaks to the desktop",
		              mistake ? mistake->message : "no reason given");
		return 0;
	}
	g_variant_get(response, "(u)", &token);
	registro_dice(LOG_SESSION,
	              "⭐ suspend and idleness INHIBITED to the session manager "
	              "(cookie %u, flags 12 = SUSPEND|IDLE — ⛔ never LOGOUT, or we would take away "
	              "the user's only door to leave)",
	              token);
	return token;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ MAKE IT BE BORN AND RETURN AT ONCE — 15 August 2026, phase 5.
 *
 * ⛔ WHY `session_ensure()` WAS NOT ENOUGH, though it does the same thing:
 *    it **waits** up to `WAIT_STARTUP_MS` (40 s), and its caller is the
 *    child, that is the only process that during those 40 s must keep
 *    answering the parent.  ⚠ `LESSONS.md` §6.2-bis: a wait that protects one
 *    link is a delay for all the others.
 *
 * ⭐ And the wait is not needed, because it already exists: the child retries the stage with
 *    a doubling wait (1 s → 30 s).  ⇒ Here the birth is ASKED for and we
 *    return; finding out that the session is there is the next round's job.
 *
 * ⚠ It starts ONLY from `SESSION_DEAD`.  The other states are governed by
 *   `session_ensure()`, and redoing them here would mean two rules on the same
 *   fact — that is two different rules the day one of them changes.
 */
bool session_spawn(uint32_t width, uint32_t height)
{
	SessionState state;

	/*
	 * ⛔⛔ FIRST OF ALL: IF THERE IS NO DESKTOP, WE DO NOT TRY — phase 13.
	 *
	 * Until yesterday we got here anyway, because a machine without a desktop
	 * declared itself **GNOME as a fallback**; then it failed three times blaming
	 * someone else (`[M]` 20 Sep 2026: «another drop-in wins over mine»,
	 * «Mutter does not expose RemoteDesktop»).  ⇒ Now it is said here, where whoever
	 * looks at THIS tenant's slice of the log finds it — and not just once
	 * at server startup, where no bench reads it.
	 */
	if (is_nobody()) {
		registro_dice(LOG_SESSION,
		              "⛔ I am not making anything be born: %s.  ⚠ It is not «the session was "
		              "born blind», it is «there is no desktop to switch on»: they are "
		              "two different faults and this is the second",
		              session_desktop_explain());
		return false;
	}

	state = session_state(width, height, NULL);

	if (state != SESSION_DEAD) {
		registro_dice(LOG_SESSION,
		              "I am not making it be born: the state is «%s», not «dead» — and "
		              "the other cases are governed by session_ensure()",
		              session_mark(state));
		return false;
	}

	/* ⭐ R1/R2 — before putting anything into the user manager: away with the
	 *    leftovers of a session that ended badly, and the snapshot of how it is now
	 *    (the box above `session_clear_out_handler()`). */
	session_clear_out_handler("birth: leftovers from before");
	session_snapshot_handler();

	/* ⛔ The drop-in BEFORE the command: the desktop size is inside it, and
	 *    `gnome-session` starts the Shell unit as the first thing.
	 *    Writing it afterwards would mean writing it for the NEXT session. */
	if (!write_dropin(width, height)) {
		registro_dice(LOG_SESSION,
		              "⛔ without the drop-in in force I do not make it be born: "
		              "it would be born with one monitor too many, and the user would again look at "
		              "an empty screen");
		return false;
	}

	/*
	 * ⛔⛔⛔ AND FIRST OF ALL: IS THE USER MANAGER DYING? — 16 August 2026,
	 *      and it is the cause that made the user try five times.
	 *
	 * `[M]` After a logout, `user@<uid>.service` **shuts down**: in the journal one
	 * reads *«Finished systemd-exit.service — Exit the Session»*, and with it
	 * `dbus.socket`, `pipewire.socket`, `session.slice` go away.  ⛔ If at that
	 * moment we launch `gnome-session`, it starts **inside a session
	 * that is dying** and dies with it — without an error saying so.
	 *
	 * ⇒ The symptom was this, and it looked like four different defects: the desktop
	 *   that does not appear, that appears after thirty seconds, that appears «broken», and
	 *   the input that does not arrive.  `[M]` The session was started two or three times
	 *   in a row (06:28:33, :46, :59) and only the last one took hold.
	 *
	 * ⭐ The cure is not waiting on a timer: it is ASKING.  The manager can say of itself
	 *    «stopping», and as long as it says so nothing is made to be born — we go
	 *    back, and the retry loop tries again shortly.  ⚠ It is the same
	 *    shape as the «ATTENDI» of §7.1: **one does not ask someone who is not there, and one is not
	 *    born where things are dying**.
	 */
	{
		char *argv[] = { "systemctl", "--user", "is-system-running", NULL };
		g_autofree char *state = ask(argv);

		if (state) {
			g_strstrip(state);
			if (g_strcmp0(state, "stopping") == 0) {
				registro_dice(LOG_SESSION,
				              "⛔ the user manager is SHUTTING DOWN "
				              "(«stopping»): I do NOT make the session be born "
				              "now — it would be born inside a session that "
				              "is dying, and would die with it without saying why.  "
				              "⭐ Retrying shortly");
				return false;
			}
		}
	}

	/*
	 * ⛔⭐ AND THE OLD ONE MUST HAVE REALLY ENDED, not «almost».
	 *
	 * `inactive_unit()` has existed since August and already carries the right lesson in its
	 * comment: *«inactive» and not «no longer active»: `is-active` goes through
	 * `deactivating`, and restarting in there is another first run*.
	 * ⇒ It is exactly our case, seen from another door: `[M]` 16 August,
	 * the first start after a logout failed because the previous session's
	 * manager was still closing.
	 *
	 * ⚠ We do not wait in here: we say no and return: our caller has a
	 *   retry loop made on purpose, and a wait inside this
	 *   function would be a child that stops answering (`LESSONS.md`
	 *   §6.2-bis).
	 */
	if (!inactive_unit()) {
		registro_dice(LOG_SESSION,
		              "⛔ the PREVIOUS graphical session has not ended yet "
		              "(«%s» is not inactive): I do not make a second one be born "
		              "now — it would be born inside the one that is dying.  ⭐ Retrying "
		              "shortly",
		              e_kde()                   ? SESSION_UNIT_KWIN
		              : (e_xfce() || e_lxqt()) ? "the process " SESSION_PROCESS_XFCE
		                                        : gnome_session()->handler);
		return false;
	}

	/*
	 * ⛔⛔ THE `pipewire-pulse` LEFT OVER FROM THE PREVIOUS SESSION — 2 October 2026,
	 *      the user's manual test on the Radeon: «in GNOME audio does not work».
	 *
	 * `[M]` After «Log Out», with the user manager still alive, the ending
	 * session stops `pipewire`, `wireplumber` and `filter-chain` but NOT
	 * `pipewire-pulse` (14:13:18).  At the new session `pipewire` restarts
	 * (14:13:29) and `pipewire-pulse` stays the one from 14:04, attached to a
	 * `pipewire` that is no longer there: whoever plays with PulseAudio (Firefox) talks
	 * to nothing, and our sink captures only silence.  The audio tests
	 * did not see it because they always open a new session.
	 *
	 * ⇒ If `pipewire` is NOT active and `pipewire-pulse` is, the latter is a
	 *   leftover: it is stopped.  Its socket stays, and the first program that
	 *   wants to play turns it back on attached to the right `pipewire`.  ⭐ No
	 *   per-desktop branch: it is the user manager, the same for all.
	 */
	{
		/* ⛔ AND «pipewire off» IS NOT ENOUGH: `[M]` 3 Oct 2026, round
		 *    `19-chiusura-intel`, F-012B on GNOME — at «Log Out» `wireplumber` and
		 *    `pipewire` stop (13:34:33) but not `pipewire-pulse`; at the
		 *    new login `pipewire` RESTARTS (13:34:38) and when we look it is
		 *    already active ⇒ the check did not fire and the old pulse stayed.
		 * ⇒ The start INSTANTS are compared: a `pipewire-pulse` started
		 *   before the `pipewire` in force is the leftover, whatever the order. */
		char *pw[] = { "systemctl", "--user", "show", "-p", "ActiveState",
		               "-p", "ActiveEnterTimestampMonotonic", "pipewire.service", NULL };
		char *pp[] = { "systemctl", "--user", "show", "-p", "ActiveState",
		               "-p", "ActiveEnterTimestampMonotonic", "pipewire-pulse.service", NULL };
		g_autofree char *s_pw = ask(pw);
		g_autofree char *s_pp = ask(pp);
		bool pw_active = s_pw && strstr(s_pw, "ActiveState=active\n");
		bool pp_active = s_pp && strstr(s_pp, "ActiveState=active\n");
		const char *t;
		unsigned long long da_pw = 0, da_pp = 0;

		if (s_pw && (t = strstr(s_pw, "ActiveEnterTimestampMonotonic=")))
			da_pw = g_ascii_strtoull(t + 30, NULL, 10);
		if (s_pp && (t = strstr(s_pp, "ActiveEnterTimestampMonotonic=")))
			da_pp = g_ascii_strtoull(t + 30, NULL, 10);
		if (pp_active && (!pw_active || da_pp < da_pw)) {
			char *halt[] = { "systemctl", "--user", "stop", "pipewire-pulse.service", NULL };

			registro_dice(LOG_SESSION,
			              "⚠ `pipewire-pulse` (since %llu) is older than `pipewire` "
			              "(%s, since %llu): it is the leftover of the previous session, and "
			              "programs playing through PulseAudio would stay mute.  I "
			              "stop it: the socket turns it back on attached to the new `pipewire` — %s",
			              da_pp, pw_active ? "active" : "off", da_pw,
			              run(halt) ? "stopped" : "⛔ NOT stopped");
		} else {
			registro_dice(LOG_SESSION,
			              "`pipewire-pulse` %s (since %llu), `pipewire` %s (since %llu): no "
			              "leftovers of the previous session",
			              pp_active ? "active" : "off", da_pp,
			              pw_active ? "active" : "off", da_pw);
		}
	}

	/* ⛔ THE SETTINGS BEFORE THE COMMAND, for the same reason as the drop-in:
	 *    `gnome-session` starts the Shell as the first thing, and a key
	 *    written afterwards holds for the NEXT session — that is it is right tomorrow. */
	/* ⭐ D-015: first the session dconf is emptied, then it is written to. */
	if (desktop_session() == SESSION_DESKTOP_GNOME)
		session_dconf_reset();
	session_settings();

	return start(width, height) ? true : false;
}

SessionState session_ensure(uint32_t width, uint32_t height, bool *was_started)
{
	SessionMonitor chosen;
	SessionState state;
	gint64 expiry, viva_da = 0;

	if (was_started)
		*was_started = false;

	state = session_state(width, height, &chosen);
	switch (state) {
	case SESSION_HEALTHY:
		/*
		 * ⛔⛔ AND THIS IS NO LONGER THE GOOD CASE — 14 August 2026, phase 4, A1.
		 *
		 *     `SESSION_HEALTHY` means «one monitor only, «MetaVirtualMonitor»,
		 *     of the requested size»: that is a session that took **a
		 *     monitor of its own**.  Then capture mounts a second one and records
		 *     that ⇒ ⛔ the user looks at an empty screen.  `[M]` measured
		 *     by bench `04-b20` on 14 August 2026.
		 *
		 * ⇒ ⭐ Now the good case is `SESSION_BLACK` — zero monitors of its own —
		 *      and this is the DEFECT.  ⛔ I make it be born again, and the reason is
		 *      the same, reversed, that `session.h` gives for the black one: a
		 *      «MetaVirtualMonitor» monitor exists **only** if someone
		 *      passed `--virtual-monitor`, that is only in a headless session
		 *      — that is ours.  Nothing is taken away from anyone.
		 *
		 * ⚠ And it is reborn ONLY here, where the monitors are **one**: if there were two
		 *   there would be a live capture (`SESSION_SELF_CHOSEN`), and knocking down
		 *   the session would take the desktop away from an attached client.
		 */
		registro_dice(LOG_SESSION,
		              "⛔ THE SESSION HAS A MONITOR OF ITS OWN («%s» «%s» %ux%u): it is the "
		              "invisible desktop defect — capture will mount a SECOND one and "
		              "the user will look at that one, empty.  I make it BE BORN AGAIN without "
		              "monitors of its own, and I write it here because a session that disappears "
		              "without a line is worse than the defect",
		              chosen.connector, chosen.product, chosen.width,
		              chosen.height);
		break;
	case SESSION_NOT_READ:
		registro_dice(LOG_SESSION,
		              "⛔ I could not read the session state: I touch "
		              "NOTHING.  «I could not look» is not «it is not there» (E8), and a "
		              "session knocked down because of a failed read is damage done "
		              "on a hypothesis");
		return SESSION_NOT_READ;
	case SESSION_WRONG_SIZE:
		/* ⛔ It is the same defect as above with another size: a
		 *    «MetaVirtualMonitor» monitor the session was not supposed to have. */
		registro_dice(LOG_SESSION,
		              "⛔ the session has a monitor of ITS OWN, %ux%u instead of the requested %ux%u: "
		              "it is the invisible desktop defect with another size.  I "
		              "make it BE BORN AGAIN without monitors of its own",
		              chosen.width, chosen.height, width, height);
		break;
	case SESSION_SELF_CHOSEN:
		/*
		 * ⭐ AND THIS, AFTER THE CURE, IS OFTEN THE HEALTHY CASE: «Virtual remote
		 *    monitor» is the name Mutter gives to the monitor of a `RecordVirtual`
		 *    (`meta-screen-cast-virtual-stream-src.c:606-609` `[R]`), that is to the
		 *    monitor OUR capture mounts when a client is attached.
		 * ⛔ It is not touched in any case: making it be born again would take the
		 *    desktop away from whoever is watching it (I4).
		 */
		registro_dice(LOG_SESSION,
		              "the session is there with %u monitors, the first is «%s»: I do NOT touch it.  "
		              "⭐ After the cure of 14 August 2026 this is often the healthy case — "
		              "«Virtual remote monitor» is the monitor capture mounts when "
		              "a client is attached, and knocking it down would take it away (I4)",
		              chosen.amount, chosen.product);
		return SESSION_SELF_CHOSEN;
	case SESSION_BLACK:
		/*
		 * ⛔⛔ AND THIS IS NO LONGER A FAULT — 14 August 2026, phase 4, A1.
		 *
		 *     Until this morning the session was made to BE BORN AGAIN here.  ⇒ After the
		 *     cure that line **would destroy the right session at every
		 *     call**, and make another identical one, forever.
		 *
		 * ⭐ Zero monitors of its own IS the goal: the only monitor is mounted by our
		 *    capture, and GNOME puts the bar and the dock on it.
		 * ⚠ The price is declared: before the first client the session is really
		 *    BLACK — it has nothing to show, and must not show it to
		 *    anyone.  For a **remote-only** session that is correct.
		 */
		registro_dice(LOG_SESSION,
		              "⭐ the session is there and has no monitors of its own: it is exactly what "
		              "is needed, and I do NOT touch it.  The only monitor will be mounted by "
		              "capture when the first client arrives, and that is where GNOME puts "
		              "the bar and the dock.  ⚠ Until then the session is black, and that is "
		              "fine: it is a REMOTE-ONLY session");
		return SESSION_BLACK;
	case SESSION_DEAD:
		registro_dice(LOG_SESSION, "no graphical session: I am starting it");
		break;
	}

	/*
	 * ⛔ THE DROP-IN BEFORE THE COMMAND, and it is not just any order: the desktop
	 *    size is inside it, and `gnome-session` starts the Shell's unit
	 *    as the first thing.  Writing it afterwards would mean writing it for the
	 *    NEXT session — that is being right tomorrow.
	 *
	 * ⛔ AND BEFORE KNOCKING DOWN THE ONE WITH THE EXTRA MONITOR: if the drop-in
	 *    cannot be put in force, making it be born again would give another session
	 *    with the same defect, and on top of that we would have taken away from the user the one
	 *    that was there.
	 */
	if (!write_dropin(width, height)) {
		registro_dice(LOG_SESSION,
		              "⛔ without the drop-in in force the session would be reborn with the "
		              "same extra monitor, and the user would again look at an empty "
		              "screen: I do not make it be born at all, and the state stays «%s»",
		              session_mark(state));
		return state;
	}

	/* ⛔ Only the one with ITS OWN monitor (just one, and ours) is knocked down: never the
	 *    black one — which is now the right one — and never the one with two monitors, which
	 *    has a live capture on it. */
	if ((state == SESSION_HEALTHY || state == SESSION_WRONG_SIZE) &&
	    !session_terminate()) {
		registro_dice(LOG_SESSION,
		              "⛔ the session with the extra monitor did not go away: I do not "
		              "start a second one (one graphical session per user, I2)");
		return session_state(width, height, NULL);
	}

	if (!start(width, height))
		return session_state(width, height, NULL);

	/*
	 * ⛔⭐ AND HERE WE WAIT FOR THE SESSION **WITHOUT MONITORS OF ITS OWN**, not for a monitor.
	 *
	 * ⚠ Until 14 August 2026 this wait ended on `SESSION_HEALTHY` — «there is
	 *   a monitor». It was the right question for the previous design, where the
	 *   session had to bring a monitor of its own; ⛔ after the cure it is the
	 *   REVERSED question, and waiting for `SANA` would mean waiting for the defect.
	 *
	 * ⭐ v1's lesson remains, though, and we do not go back to `session_alive()`: we
	 *   still look at **how many monitors there are**, because it is the only way to
	 *   notice that someone else's drop-in won over ours.  The
	 *   question is the same, it is the expected value that has been reversed.
	 *
	 * ⚠ The grace is still needed, and for the opposite reason: `--virtual-monitor`
	 *   would create the monitor BEFORE `DisplayConfig` answers, so if after
	 *   the grace the monitors are still zero, zero they will stay.
	 */
	expiry = g_get_monotonic_time() + (gint64) WAIT_STARTUP_MS * 1000;
	while (g_get_monotonic_time() < expiry) {
		g_usleep(CHECK_INTERVAL_MS * 1000);
		if (!session_alive())
			continue;
		if (viva_da == 0) {
			viva_da = g_get_monotonic_time();
			registro_dice(LOG_SESSION,
			              "the compositor answers; I check that it has NOT taken a "
			              "monitor of its own (grace %d ms)",
			              GRACE_MONITOR_MS);
			continue;
		}
		if (g_get_monotonic_time() - viva_da < (gint64) GRACE_MONITOR_MS * 1000)
			continue;

		state = session_state(width, height, &chosen);
		if (state == SESSION_BLACK) {
			if (was_started)
				*was_started = true;
			registro_dice(LOG_SESSION,
			              "⭐ graphical session ready and WITHOUT monitors of its own: it is "
			              "what is needed.  The monitor will be mounted by capture at the "
			              "first client, and the bar and the dock will go on it");
			return SESSION_BLACK;
		}
		if (state != SESSION_DEAD && state != SESSION_NOT_READ) {
			/* It is born, and it took a monitor: waiting longer would
			 * change nothing, and this is the number to give. */
			if (was_started)
				*was_started = true;
			registro_dice(LOG_SESSION,
			              "⛔ the session was born AND TOOK A MONITOR («%s»): "
			              "«%s».  My drop-in did not win, and the user "
			              "will look at an empty screen",
			              chosen.product, session_mark(state));
			return state;
		}
	}

	state = session_state(width, height, NULL);
	registro_dice(LOG_SESSION,
	              "⛔ the graphical session did not answer within %d seconds: it stays «%s»",
	              WAIT_STARTUP_MS / 1000, session_mark(state));
	return state;
}
