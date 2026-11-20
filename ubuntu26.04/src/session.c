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
/* ⭐ 19 Nov 2026: three answers instead of two.  1 = the bus ANSWERED and the name has an owner; 0 = the bus ANSWERED and
 *    nobody owns the name; -1 = I could not ask (no bus, call failed or timed out): that is NOT «nobody owns it». */
static int name_owner_three(GDBusConnection *bus, const char *name)
{
	g_autoptr(GVariant) response = NULL;
	gboolean c_e = FALSE;

	if (!bus || !name)
		return -1;
	response = g_dbus_connection_call_sync(
		bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
		"NameHasOwner", g_variant_new("(s)", name), G_VARIANT_TYPE("(b)"),
		G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_NAME_MS, NULL, NULL);
	if (!response)
		return -1;
	g_variant_get(response, "(b)", &c_e);
	return c_e ? 1 : 0;
}

static gboolean name_has_owner(GDBusConnection *bus, const char *name)
{
	return name_owner_three(bus, name) == 1;
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
 * ⭐ 1.5.2 — WHICH DESKTOP THE MACHINE DECLARES AS ITS OWN, when more than one is installed.
 *
 * ⛔ The presence of programs does not say it: on Xubuntu 26.04 (`xubuntu-desktop`) the
 *    packages `gnome-session-bin`, `gnome-shell` and `ubuntu-session` come in as dependencies of other
 *    packages (measured 14 Nov 2026), so there `ubuntu.desktop` is even offered next to
 *    `xfce-wayland.desktop`, and the old rule («gnome-session ⇒ GNOME») started GNOME on an XFCE
 *    machine.  What does say it is the configuration of the machine's DISPLAY MANAGER, written
 *    by the flavour's package: lightdm `user-session=xubuntu` (`60-xubuntu.conf`); for sddm the
 *    `Session` key of `[Autologin]` (`20-kubuntu.conf`: `plasma`) — ⚠ that is the AUTOLOGIN
 *    session, and it is used only as a HINT of what the machine is for.
 * ⚠ Read only when two or more desktops are there; with one the answer is that one, and with
 *   no declaration the documented order stays (GNOME, KDE, XFCE, LXQt: DECISIONS.md §4.6-duodetricies).
 * ⚠ Only the declarations of the machine's ACTIVE display manager count: if
 *   `/etc/X11/default-display-manager` (or, without it, the target of
 *   `/etc/systemd/system/display-manager.service`) names a manager that is neither lightdm nor sddm
 *   (gdm3…), the lightdm/sddm files are leftovers of other packages and are ignored.  When the
 *   active manager cannot be determined, the files are read as before.
 * ⛔ The session a single user picks at login (AccountsService `Session=`/`XSession=`) is NOT read:
 *   one machine, one desktop (DECISIONS.md §0.6).
 */
static gint cmp_str_ptr(gconstpointer x, gconstpointer y)
{
	return strcmp(*(char *const *) x, *(char *const *) y);
}

static void add_sorted_dir(GPtrArray *files, const char *dir)
{
	g_autoptr(GDir) d = g_dir_open(dir, 0, NULL);
	g_autoptr(GPtrArray) names = g_ptr_array_new_with_free_func(g_free);
	const char *f;

	while (d && (f = g_dir_read_name(d)))
		if (g_str_has_suffix(f, ".conf"))
			g_ptr_array_add(names, g_strdup(f));
	g_ptr_array_sort(names, (GCompareFunc) cmp_str_ptr);
	for (guint i = 0; i < names->len; i++)
		g_ptr_array_add(files, g_build_filename(dir, (char *) names->pdata[i], NULL));
}

/*
 * The last value of `key` in the configuration files, read in the order the service reads them.
 *   merge_by_name FALSE (lightdm): directory by directory, in the order of `dirs`, the files
 *     alphabetical only WITHIN each directory — lightdm does NOT merge by name across directories,
 *     so any file of a later directory (`/etc`) beats any file of an earlier one (`/usr`);
 *   merge_by_name TRUE (sddm): a name in a later folder replaces the same name earlier, then all
 *     in alphabetical order.
 * `group` NULL: the key in any group.  `last_file` is read last.
 */
static char *last_conf_value(const char *const *dirs, const char *last_file, const char *group,
                             const char *key, gboolean merge_by_name)
{
	g_autoptr(GPtrArray) files = g_ptr_array_new_with_free_func(g_free);
	char *value = NULL;

	if (merge_by_name) {
		g_autoptr(GHashTable) names = g_hash_table_new_full(g_str_hash, g_str_equal, g_free,
		                                                    g_free);
		g_autoptr(GList) keys = NULL;

		for (int i = 0; dirs[i]; i++) {
			g_autoptr(GDir) d = g_dir_open(dirs[i], 0, NULL);
			const char *f;

			while (d && (f = g_dir_read_name(d)))
				if (g_str_has_suffix(f, ".conf"))
					g_hash_table_replace(names, g_strdup(f),
					                     g_build_filename(dirs[i], f, NULL));
		}
		keys = g_list_sort(g_hash_table_get_keys(names), (GCompareFunc) strcmp);
		for (GList *l = keys; l; l = l->next)
			g_ptr_array_add(files, g_strdup(g_hash_table_lookup(names, l->data)));
	} else {
		for (int i = 0; dirs[i]; i++)
			add_sorted_dir(files, dirs[i]);
	}
	if (last_file)
		g_ptr_array_add(files, g_strdup(last_file));
	for (guint i = 0; i < files->len; i++) {
		g_autoptr(GKeyFile) kf = g_key_file_new();
		g_auto(GStrv) groups = NULL;

		if (!g_key_file_load_from_file(kf, files->pdata[i], G_KEY_FILE_NONE, NULL))
			continue;
		groups = g_key_file_get_groups(kf, NULL);
		for (int j = 0; groups[j]; j++) {
			char *v;

			if (group && strcmp(groups[j], group) != 0)
				continue;
			v = g_key_file_get_string(kf, groups[j], key, NULL);
			if (v && *g_strstrip(v)) {
				g_free(value);
				value = v;
			} else
				g_free(v);
		}
	}
	return value;
}

/* the desktop a session name (`xubuntu`, `plasma`, `ubuntu`, `lxqt`, `gnome`…) belongs to.
 * ⚠ «ubuntu» as a substring also catches `ubuntustudio`, `ubuntu-budgie`…: flavours outside the four
 * supported ones (Ubuntu, Kubuntu, Xubuntu, Lubuntu). */
static DesktopSession desktop_of_session_name(const char *name)
{
	g_autofree char *n = g_ascii_strdown(name, -1);

	/* ⚠ xubuntu, lubuntu and kubuntu contain «ubuntu»: they are asked BEFORE it */
	if (strstr(n, "xfce") || strstr(n, "xubuntu"))
		return SESSION_DESKTOP_XFCE;
	if (strstr(n, "lxqt") || strstr(n, "lubuntu"))
		return SESSION_DESKTOP_LXQT;
	if (strstr(n, "plasma") || strstr(n, "kde") || strstr(n, "kubuntu"))
		return SESSION_DESKTOP_KDE;
	if (strstr(n, "gnome") || strstr(n, "ubuntu"))
		return SESSION_DESKTOP_GNOME;
	return SESSION_DESKTOP_NONE;
}

/* The name of the machine's active display manager (`lightdm`, `sddm`, `gdm3`…), or NULL when it
 * cannot be determined. */
static char *active_display_manager(void)
{
	g_autofree char *file = NULL;
	g_autofree char *link = g_file_read_link("/etc/systemd/system/display-manager.service", NULL);

	if (g_file_get_contents("/etc/X11/default-display-manager", &file, NULL, NULL) &&
	    *g_strstrip(file))
		return g_path_get_basename(file);
	if (link) {
		char *base = g_path_get_basename(link);

		if (g_str_has_suffix(base, ".service"))
			base[strlen(base) - strlen(".service")] = '\0';
		return base;
	}
	return NULL;
}

/* A session name taken from a configuration file or from a file name: the trailing `.desktop`
 * stripped (sddm may write `Session=plasma.desktop`), and only `[A-Za-z0-9._+-]` accepted —
 * never empty, never a leading `.`, never `..` (the name ends up in a path).  NULL if refused. */
static char *clean_session_name(const char *raw)
{
	char *name;

	if (!raw)
		return NULL;
	name = g_strstrip(g_strdup(raw));
	if (g_str_has_suffix(name, ".desktop"))
		name[strlen(name) - strlen(".desktop")] = '\0';
	if (!*name || name[0] == '.' || strstr(name, "..") ||
	    strspn(name, "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._+-") !=
	            strlen(name))
		g_clear_pointer(&name, g_free);
	return name;
}

/* The sessions the machine declares (lightdm `user-session`, sddm `[Autologin] Session`), the
 * active display manager's first: `found[0]` is the strongest, `found[1]` the other; either may
 * be NULL (the strings are to be freed).  FALSE when the active manager is another one
 * (`gdm3`…: the files of the others are leftovers). */
static gboolean declared_sessions(char *found[2])
{
	/* lightdm's order: the data dirs in reverse (`/usr/share`, `/usr/local/share`), then
	 * `/etc/xdg`, then `/etc/lightdm`; then `/etc/lightdm/lightdm.conf` */
	static const char *const lightdm_dirs[] = {"/usr/share/lightdm/lightdm.conf.d",
	                                           "/usr/local/share/lightdm/lightdm.conf.d",
	                                           "/etc/xdg/lightdm/lightdm.conf.d",
	                                           "/etc/lightdm/lightdm.conf.d", NULL};
	static const char *const sddm_dirs[] = {"/usr/lib/sddm/sddm.conf.d", "/etc/sddm.conf.d", NULL};
	g_autofree char *dm = active_display_manager();
	char *lightdm, *sddm;

	found[0] = found[1] = NULL;
	if (dm && strcmp(dm, "lightdm") != 0 && strcmp(dm, "sddm") != 0)
		return FALSE;
	lightdm = last_conf_value(lightdm_dirs, "/etc/lightdm/lightdm.conf", NULL, "user-session",
	                          FALSE);
	sddm = last_conf_value(sddm_dirs, "/etc/sddm.conf", "Autologin", "Session", TRUE);
	{
		char *l = clean_session_name(lightdm), *d = clean_session_name(sddm);

		g_free(lightdm);
		g_free(sddm);
		if (dm && strcmp(dm, "sddm") == 0) {
			found[0] = d;
			found[1] = l;
		} else {
			found[0] = l;
			found[1] = d;
		}
	}
	return TRUE;
}

/* The declared session of the machine, the active display manager's first; the first that names
 * a desktop which is installed (`present[]`, indexed by DesktopSession) wins.  `*which`
 * receives the text. */
static DesktopSession declared_desktop(const gboolean *present, char **which)
{
	char *found[2];
	DesktopSession result = SESSION_DESKTOP_NONE;

	if (!declared_sessions(found))
		return SESSION_DESKTOP_NONE;
	for (int i = 0; i < 2 && result == SESSION_DESKTOP_NONE; i++) {
		DesktopSession d = found[i] ? desktop_of_session_name(found[i]) : SESSION_DESKTOP_NONE;

		if (d != SESSION_DESKTOP_NONE && present[d]) {
			*which = g_strdup(found[i]);
			result = d;
		}
	}
	g_free(found[0]);
	g_free(found[1]);
	return result;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐ PHASE 12 — WHICH DESKTOP.  The criterion and the why are in `session.h`.
 *
 * ⚠ The process PATH is looked at.  The parent searches the PATH of the service; the child
 *   (and the session) get the one of the PAM login (`child.c`): the two give the same answer
 *   as long as the programs are in `/usr/bin`, which is where the distribution puts them.
 * ⚠ 1.5.2: with two or more desktops the answer ALSO depends on world-readable
 *   configuration files (`declared_desktop()` above).  Parent and child must read the same
 *   files, and they do: both run on the same machine, the files are readable by everyone, and
 *   nobody changes them while REMOTIX runs.
 */
static DesktopSession chosen_desktop;
static const char *desktop_description;

static void recognize_desktop(void)
{
	static gsize completed;

	if (g_once_init_enter(&completed)) {
		g_autofree char *gnome_bin = g_find_program_in_path("gnome-session");
		/* ⭐ 1.5.2 — `gnome-session` ALONE is not GNOME: on Xubuntu (and on other desktops)
		 *    `gnome-session-bin` arrives as a dependency of other packages, and the Shell is
		 *    not there.  GNOME is recognised only with the Shell as well. */
		g_autofree char *gnome_shell = g_find_program_in_path("gnome-shell");
		const char *gnome = gnome_bin && gnome_shell ? gnome_bin : NULL;
		g_autofree char *plasma = g_find_program_in_path("startplasma-wayland");
		g_autofree char *xfce = g_find_program_in_path("xfce4-session");
		g_autofree char *labwc = g_find_program_in_path(SESSION_PROCESS_XFCE);
		/* ⭐ PHASE 14 — always looked up, but it decides only AFTER XFCE: see the branch. */
		g_autofree char *lxqt = g_find_program_in_path(SESSION_MARKER_LXQT);
		g_autofree char *declared_name = NULL;
		const char *declared_note = "";

		/* ⭐ 1.5.2 — two or more desktops installed: the one the machine declares as its own
		 *    wins (see `declared_desktop()`); the others are left out of the choice below. */
		if ((gnome != NULL) + (plasma != NULL) + (xfce != NULL) + (lxqt != NULL) > 1) {
			gboolean present[8] = {FALSE};
			DesktopSession decl;

			present[SESSION_DESKTOP_GNOME] = gnome != NULL;
			present[SESSION_DESKTOP_KDE] = plasma != NULL;
			present[SESSION_DESKTOP_XFCE] = xfce != NULL;
			present[SESSION_DESKTOP_LXQT] = lxqt != NULL;
			decl = declared_desktop(present, &declared_name);
			if (decl != SESSION_DESKTOP_NONE) {
				if (decl != SESSION_DESKTOP_GNOME)
					gnome = NULL;
				if (decl != SESSION_DESKTOP_KDE)
					g_clear_pointer(&plasma, g_free);
				if (decl != SESSION_DESKTOP_XFCE)
					g_clear_pointer(&xfce, g_free);
				if (decl != SESSION_DESKTOP_LXQT)
					g_clear_pointer(&lxqt, g_free);
				declared_note = declared_name;
			}
		}

		if (plasma && !gnome) {
			chosen_desktop = SESSION_DESKTOP_KDE;
			desktop_description = "KDE Plasma (startplasma-wayland is there)";
		} else if (plasma && gnome) {
			chosen_desktop = SESSION_DESKTOP_GNOME;
			desktop_description = "GNOME — ⚠ AMBIGUOUS: this machine has both GNOME and "
			                   "KDE, and GNOME wins.  Choosing among several desktops is not available "
			                   "yet (DECISIONS.md §4.6-duodetricies, MASTERPLAN.md M5)";
		} else if (gnome) {
			chosen_desktop = SESSION_DESKTOP_GNOME;
			desktop_description = "GNOME (gnome-session and gnome-shell are there)";
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
			                   "gnome-session with gnome-shell, nor startplasma-wayland, nor "
			                   "xfce4-session, nor lxqt-session: no graphical "
			                   "session can "
			                   "be born, and I am not trying any";
		}
		/* the machine declared it: it is SAID (once per process, the string stays) */
		if (*declared_note)
			desktop_description = g_strdup_printf(
				"%s — several desktops are installed here, and this one is named by the "
				"display manager configuration of this machine («%s»)",
				desktop_description, declared_note);
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
static char *card_node(card_pick_how *how, char **story)
{
	/* ⭐ 1.5 (27 Oct 2026, §11.37 addendum): the rule lives in `card_pick.c`, shared with `wlroots.c`: the BIOS primary
	 *   card if it can draw, else the capable card with the lowest PCI address (not the lowest NAME).  ⛔ The
	 *   administrator does not choose the card; `--render-node` stays the encoder's fallback only. */
	return card_pick_desktop(how, story);
}

/* ⭐ the log line of a chosen card: node, PCI address, driver (`render_node_describe()`) and WHY */
static void card_say(const char *who, const char *node, const char *story)
{
	char desc[160];

	render_node_describe(node, desc, sizeof desc);
	registro_dice(LOG_SESSION, "⭐ %s: the card I give the compositor is %s (%s) — %s", who, node, desc, story);
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

/* ⭐ 18 Nov 2026 — the program the chosen desktop NEEDS and the machine does not have, or NULL.
 *   Only `labwc` for XFCE and LXQt: it is a Recommends of the package (`--no-install-recommends`
 *   leaves it out) and these desktops bring no compositor of their own.  `wlr-randr` is not
 *   asked for (a failing one still lets the session be born: `measured_primary()`), nor is
 *   Xwayland; KDE has the KWin fallback and GNOME its own compositor.
 *   ⚠ LIMIT: the PARENT looks in the PATH of the service, the session starts with the one of
 *   the PAM login; they agree for `/usr/bin` (where `labwc` is packaged), not for a labwc
 *   installed in a folder only one of the two PATHs has.
 *   ⚠ Looked up at EVERY call, not once like `recognize_desktop()`: an administrator who
 *   installs the package while the server runs is believed at the next login. */
const char *session_missing_component(void)
{
	DesktopSession d = desktop_session();
	g_autofree char *found = NULL;

	if (d != SESSION_DESKTOP_XFCE && d != SESSION_DESKTOP_LXQT)
		return NULL;
	found = g_find_program_in_path(SESSION_PROCESS_XFCE);
	return found ? NULL : SESSION_PROCESS_XFCE;
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
		/* ⭐ D8: the one the login screen would offer first on this distribution
		 *    (Ubuntu: `ubuntu`, even when `gnome` is installed too) */
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
		/* ⭐ 1.5.2: the lines below are said only on a GNOME machine: `gnome_session()` is
		 *    also called at every birth on KDE, XFCE and LXQt, where «DECLARED FALLBACK»
		 *    would be false (nobody falls back, GNOME is not the desktop). */
		if (!choice) {
			choice = g_new0(GnomeSession, 1);
			choice->name = g_strdup(SESSION_GNOME_FALLBACK);
			choice->id = g_strdup(SESSION_GNOME_FALLBACK);
			choice->line = g_strdup("exec gnome-session --session=" SESSION_GNOME_FALLBACK);
			choice->desktop = g_strdup("GNOME");
			choice->handler =
				g_strdup("gnome-session-manager@" SESSION_GNOME_FALLBACK ".service");
			if (desktop_session() == SESSION_DESKTOP_GNOME)
				registro_dice(LOG_SESSION,
				              "⚠ D8: no wayland-sessions/*.desktop session launches "
				              "gnome-session with an installed .session: DECLARED "
				              "FALLBACK to «%s»",
				              SESSION_GNOME_FALLBACK);
		} else if (desktop_session() == SESSION_DESKTOP_GNOME)
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

/* ⭐ 19 Nov 2026: the question with THREE answers, for whoever must act on «dead» and not only on «does not answer»
 *    (`child.c`, the early farewell): ALIVE; DEAD = the bus answered and the compositor's name has no owner;
 *    UNKNOWN = I could not look (no bus, a call failed or timed out, any other error).  ⚠ Only DEAD is certain. */
SessionLife session_life(void)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GError) mistake = NULL;
	const char *name = NULL;
	int owner;

	bus = sess_bus(NULL);
	if (!bus)
		return SESSION_LIFE_UNKNOWN;

	/* ⭐ On Plasma the weak question is KWin's name: it is not activatable (the
	 *    compositor takes it when it starts), and the weakness is the same one
	 *    declared in `session.h` — «alive» does not mean «ready». */
	if (e_kde())
		name = "org.kde.KWin";

	/* ⭐ PHASE 13 — on XFCE the weak question is the session manager's name.
	 *    `[M]` 20 Sep 2026: it appears on the USER bus, because we start `labwc`
	 *    ourselves without `dbus-run-session` — that is exactly the bus that
	 *    `sess_bus()` already opens.  ⚠ And the weakness is the same declared for
	 *    the other two, with a wider margin: between the name and the USABLE
	 *    session there are up to 8 s per priority group, and they are structural
	 *    (`STARTUP_TIMEOUT_WAYLAND`, `STUDIES.md` §xfce §9.4). */
	else if (e_xfce())
		name = SESSION_BUS_XFCE;

	/* ⭐ PHASE 14 — on LXQt, the same weak question: the name of `lxqt-session`
	 *    on the user bus (labwc starts without `dbus-run-session`, as on XFCE).
	 * ⚠ And the weakness is declared upstream (`STUDIES.md` §lxqt §3.4): the name
	 *   appears in the CONSTRUCTOR, before the modules.  Real readiness would be
	 *   the signal `moduleStateChanged("lxqt-panel.desktop", true)`, but the child
	 *   has no GLib loop to listen to it.  [?] To be measured on the box:
	 *   how long passes between the name and the panel, and whether in between capture
	 *   on labwc fails and retries (as on XFCE) or does something else. */
	else if (e_lxqt())
		name = SESSION_BUS_LXQT;
	if (name) {
		owner = name_owner_three(bus, name);
		return owner > 0 ? SESSION_LIFE_ALIVE : owner == 0 ? SESSION_LIFE_DEAD : SESSION_LIFE_UNKNOWN;
	}

	/*
	 * ⛔ IT IS NOT ENOUGH THAT THE NAME IS TAKEN, for two different reasons, both
	 *    paid for: Mutter's name is ACTIVATABLE and asking for it makes it be born;
	 *    and the Shell takes `org.gnome.Shell` **before
	 *    `meta_context_start()`** (`STUDIES.md` §gnome §3.2), so it is not an indicator
	 *    of readiness.  A real method is called and we check that the answer
	 *    ARRIVES — without interpreting it: only one thing matters here.
	 */
	owner = name_owner_three(bus, "org.gnome.Mutter.DisplayConfig");
	if (owner == 0)
		return SESSION_LIFE_DEAD;
	if (owner < 0)
		return SESSION_LIFE_UNKNOWN;
	/* The name has an owner (the bus ANSWERED): the call goes straight to the owner, the same arguments `ask_mutter()` uses
	 * but WITHOUT its second question about the name — that one would turn «I could not ask» (timeout, bus gone between
	 * the two questions) into NAME_HAS_NO_OWNER.  ANY error here is UNKNOWN, never DEAD: the next look will say. */
	response = g_dbus_connection_call_sync(bus, "org.gnome.Mutter.DisplayConfig", "/org/gnome/Mutter/DisplayConfig",
	                                       "org.gnome.Mutter.DisplayConfig", "GetCurrentState", NULL, NULL,
	                                       G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_POLL_MS, NULL, &mistake);
	return response ? SESSION_LIFE_ALIVE : SESSION_LIFE_UNKNOWN;
}

bool session_alive(void)
{
	return session_life() == SESSION_LIFE_ALIVE;
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
		              "⚠ ZERO MONITORS, and the session is alive: it is the «alive, "
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
 * ⭐⭐ PHASE 15, D-015 (rewritten 13 Nov 2026) — THE SESSION'S DCONF, THREE LAYERS (since 19 Nov 2026 the fallback; see below).
 *
 * ⭐⭐ 19 Nov 2026 — WHAT FOLLOWS IS NOW THE DECLARED FALLBACK; THE MODEL IS THIS (`[M]` Ubuntu 26.04 VM with its snaps,
 *    dconf 0.49, GNOME 50, records in `log/dconf-misure/`):
 *    · Flutter programs (Firmware Updater, Security Center, App Center, the live installer) have their own dconf reader that
 *      knows only `user-db` and `system-db`: at a `file-db`/`service-db` line it drops the whole profile («Unknown DConf
 *      source»), and a confined snap cannot even open a profile under our `XDG_RUNTIME_DIR` («No DConf source to write
 *      to»).  Both were visible with the profile in `DCONF_PROFILE`.
 *    · So: the locks are a SYSTEM database `/etc/dconf/db/remotix` (the package compiles it in the postinst from keyfiles it
 *      generates at build time out of `DCONF_KEYS`: `remotix --dconf-keyfiles`), and the session profile is the file dconf
 *      reads when `DCONF_PROFILE` is NOT set, `$XDG_RUNTIME_DIR/dconf/profile`:
 *          <first line of the base profile>      (user-db:user: writable, stays)
 *          system-db:remotix                     (value + lock of the keys)
 *          user-db:remotix                       (what changes mid-session: `~/.config/dconf/remotix`, written by
 *                                                 the dconf service as `/ca/desrt/dconf/Writer/remotix`)
 *          <the other lines of the base profile>
 *      No `DCONF_PROFILE` in the session or in the user manager (a confined snap has another runtime folder, does not see
 *      the file and uses the plain `user-db:user`).  The user's file `user` is never written; the small file `remotix`
 *      is declared (emptied at every birth).
 *    · The belt and the birth work as below, on that file: at the end of the session it is REMOVED if the base is the default
 *      alone (an absent file is what a local login had before), else rewritten with the base alone; the birth puts it back.
 *    · If `/etc/dconf/db/remotix` or `dconf` is missing, or a runtime profile that is not ours is already there: the model below, said
 *      in the log.  The service also compiles the database at its start if it is missing or older than the package's keyfiles.
 *    · ⭐ N1: the runtime file is written at the BIRTH (or at the child's start only if a live desktop is found again), so a child that
 *      dies before the birth leaves nothing readable by a LOCAL login; the case of a child that dies AFTER the birth is the
 *      orphan-desktop road (the root side's light close runs the belt as the user).
 *    · ⚠ Declared, hot upgrade: a desktop born by an OLD child (model 1.0.0: shm, `DCONF_PROFILE`) keeps reading its `shm` while a NEW
 *      child for the same session would write `Writer/remotix`: the layout change would not reach that desktop.  The old model was
 *      never distributed on Ubuntu; the next birth is right.
 *    · An administrator's own `DCONF_PROFILE` stays the BASE profile; in the session the variable points to our file (else
 *      dconf would ignore it).
 *
 *
 * The user's rule: from remote the user customises the desktop and the changes STAY;
 * REMOTIX imposes its rules ONLY in the session and writes nothing permanent in the
 * user's settings.  A session dconf PROFILE, `$XDG_RUNTIME_DIR/remotix/dconf/profile`:
 *
 *     user-db:user                       ← first line of the base profile: writable, stays
 *     file-db:<runtime>/remotix/dconf/locks.db
 *                                        ← `dconf compile`: value + LOCK of our keys
 *     service-db:shm/remotix             ← in memory: the values that change mid-session
 *                                          (`input-sources`, written by `input.c`)
 *     (the other lines of the base profile)
 *
 *   `[R]` dconf 0.40: only the first source is written; a lock in a database hides
 *   the sources ABOVE it, so the keys of `DCONF_KEYS` win over the user's and cannot be
 *   written by the session.  The lock-only keys take their value from `shm` (below; in the runtime model, from `user-db:remotix`).
 *   ⚠ A `file-db` recompiled mid-session is NOT seen by programs already open: that is why
 *   what changes lives in `shm`; `locks.db` is compiled to a temporary file and RENAMED,
 *   never deleted while the session lives.
 *   ⚠ `shm` is a `dconf-service` writer (tmpfs, never `~/.config`); the name `remotix`
 *   without dashes: it ends up in a D-Bus path.
 *
 * ⭐ It reaches GNOME by `DCONF_PROFILE` in the environment of `gnome-session`
 *    (`compose_environment()`), set in the child by `session_dconf_prepare()` before any
 *    `GSettings`.  At birth: `shm` is emptied, then the real value of the user's
 *    `input-sources` (read with a `user-db:user`-only profile) is copied into it.
 *
 * ⚠ DECLARED FALLBACK: if `dconf compile` is missing or fails, the profile is the old one
 *   (`shm` on top, the user's below) and the same keys are written into `shm` — what the
 *   user changes from remote is lost at the next birth.  Nothing goes in the user's file.
 * ⭐ Once only (mark `$XDG_STATE_HOME/remotix/gnome-ripristinato`), the four keys that
 *   older REMOTIX versions wrote in the user's file are removed from it if they still
 *   hold exactly those values (`session_dconf_restore_once()`).
 * ⚠ The MANDATORY profile (`/run/dconf/user/<uid>`) wins over `DCONF_PROFILE`: then it
 *   cannot hold, and it is said.
 * ⚠ (fallback; in the runtime model there is no variable) `DCONF_PROFILE` stays in the user manager's environment while the
 *   session lives (a local login sharing that manager would inherit the locks); the clean-up removes it after «Exit»
 *   (`session_clear_out_handler()`; it also removes the one a previous version of the package left in a manager that
 *   outlives an upgrade).
 * ⭐ 14 Nov 2026, THE BELT for when that clean-up is late or never runs (`[M]` Arch: the
 *   variable stayed 126 s): when the child sees the session over, and when the child
 *   exits with the session over, the profile FILE is rewritten (atomic) with the user's base
 *   alone — no `file-db`, no `shm` (`session_dconf_neutralise()`): whoever inherited
 *   `DCONF_PROFILE` reads the normal settings.  ⛔ NEVER under a live desktop (it outlives the
 *   child and waits for the reattach): the programs born in the meantime would keep a
 *   profile without our locks.  `locks.db` is NOT deleted.  The three layers come back at the child's
 *   startup (`session_dconf_prepare()`) and at every birth (`dconf_profile_reinstate()`: the
 *   same child can give birth again after a logout, and there `g_setenv` is not allowed).
 */
#define DCONF_SESSION_SOURCE "service-db:shm/remotix"
#define DCONF_USER_OBJECT "/ca/desrt/dconf/Writer/user"

/* The keys of the session: value + lock (`text` = GVariant text), or LOCK ONLY
 * (`text` NULL: the value comes from the session's changing database — `user-db:remotix`, `shm` in the fallback).  ⚠ Grouped by `dir`: `dconf_compile_locks()`
 * writes one keyfile section per run of equal `dir`.
 * ⛔ `switch-to-session-N` (Ctrl+Alt+F1…F12): Mutter binds them NON_MASKABLE and in a
 *    headless session there is no console to switch to.  The schema is
 *    `org.gnome.mutter.wayland.keybindings` (until 13 Nov 2026 the code opened
 *    `org.gnome.mutter.wayland`, wrong: they were NEVER removed). */
struct dconf_key {
	const char *schema;
	const char *dir; /* with the first and last `/` */
	const char *key;
	const char *text;
};

#define VT_KEY(n) { "org.gnome.mutter.wayland.keybindings", \
	            "/org/gnome/mutter/wayland/keybindings/", "switch-to-session-" #n, "@as []" }
static const struct dconf_key DCONF_KEYS[] = {
	VT_KEY(1), VT_KEY(2), VT_KEY(3), VT_KEY(4), VT_KEY(5), VT_KEY(6),
	VT_KEY(7), VT_KEY(8), VT_KEY(9), VT_KEY(10), VT_KEY(11), VT_KEY(12),
	/* «Log Out…» MUST be there (§4.1-ter): the only gesture that ends the session */
	{ "org.gnome.shell", "/org/gnome/shell/", "always-show-log-out", "true" },
	/* no «Switch User», and no lock (on GNOME the desktop's lock REVOKES capture and input) */
	{ "org.gnome.desktop.lockdown", "/org/gnome/desktop/lockdown/", "disable-user-switching", "true" },
	{ "org.gnome.desktop.lockdown", "/org/gnome/desktop/lockdown/", "disable-lock-screen", "true" },
	/* no automatic suspend (§4.7: removes the «Automatic Suspend» lie) */
	{ "org.gnome.settings-daemon.plugins.power", "/org/gnome/settings-daemon/plugins/power/",
	  "sleep-inactive-ac-type", "'nothing'" },
	{ "org.gnome.settings-daemon.plugins.power", "/org/gnome/settings-daemon/plugins/power/",
	  "sleep-inactive-battery-type", "'nothing'" },
	{ "org.gnome.desktop.session", "/org/gnome/desktop/session/", "idle-delay", "uint32 0" },
	{ "org.gnome.desktop.screensaver", "/org/gnome/desktop/screensaver/", "lock-enabled", "false" },
	/* Ubuntu's own key: lock when suspending (the Shell's `lock()` would revoke capture) */
	{ "org.gnome.desktop.screensaver", "/org/gnome/desktop/screensaver/", "ubuntu-lock-on-suspend", "false" },
	/* ⭐ 19 Nov 2026 (GNOME 50, Mutter 50): the INTEGER scale of the desktop is 1 in the remote session.  The
	 *    stage refuses a scale other than 1 (guard 2 of §5.0-sexies: the input's coordinate space would not coincide
	 *    with the stream's pixels) and the user, with `scaling-factor` = 2 in their own settings, stayed in front of a
	 *    black page and could not even enter to put it back.  Value + lock here, as the keys above: the user's file is
	 *    never touched, and at a local login the user finds their 2 again. */
	{ "org.gnome.desktop.interface", "/org/gnome/desktop/interface/", "scaling-factor", "uint32 1" },
	/* the layout: lock only, the value is in the session's changing database (`user-db:remotix`; `shm` in the fallback) (`input.c`) */
	{ "org.gnome.desktop.input-sources", "/org/gnome/desktop/input-sources/", "sources", NULL },
	{ "org.gnome.desktop.input-sources", "/org/gnome/desktop/input-sources/", "current", NULL },
	{ "org.gnome.desktop.input-sources", "/org/gnome/desktop/input-sources/", "mru-sources", NULL },
};

/* Are the locks in force: `/etc/dconf/db/remotix` (runtime model) or `locks.db` compiled by us (fallback)?  FALSE = no lock at all */
static gboolean dconf_locked;

/* Runs a `dconf` command, with `DCONF_PROFILE` set to `profile` if not NULL;
 * stdout in `*out` if requested.  ⛔ Said in the log if it does not succeed. */
static gboolean dconf_spawn(char **argv, const char *profile, char **out)
{
	g_autoptr(GError) mistake = NULL;
	g_auto(GStrv) env = g_get_environ();
	int state = 0;

	if (profile)
		env = g_environ_setenv(env, "DCONF_PROFILE", profile, TRUE);
	if (!g_spawn_sync(NULL, argv, env, G_SPAWN_SEARCH_PATH | G_SPAWN_STDERR_TO_DEV_NULL, NULL,
	                  NULL, out, NULL, &state, &mistake) ||
	    !g_spawn_check_wait_status(state, &mistake)) {
		registro_dice(LOG_SESSION, "⚠ D-015: «%s %s …» did not succeed: %s", argv[0], argv[1],
		              mistake ? mistake->message : "no reason given");
		if (out)
			g_clear_pointer(out, g_free);
		return FALSE;
	}
	return TRUE;
}

/* ⭐ 19 Nov 2026 — THE ONE SOURCE of the keys: `DCONF_KEYS` is turned into the two texts of a dconf keyfile folder (the
 * values, and the list of locks), for both users — `dconf_compile_locks()` here (the declared fallback, compiled at the child's
 * start) and `session_dconf_keyfiles_write()` (the package: `remotix --dconf-keyfiles DIR` at BUILD time, compiled by the
 * postinst into `/etc/dconf/db/remotix`).  There is no second list to keep in step. */
static void dconf_keyfile_texts(GString *values, GString *locks)
{
	const char *section = NULL;

	g_string_append(values, "# REMOTIX (D-015): value + lock of the session.\n");
	for (guint i = 0; i < G_N_ELEMENTS(DCONF_KEYS); i++) {
		const struct dconf_key *k = &DCONF_KEYS[i];

		g_string_append_printf(locks, "%s%s\n", k->dir, k->key);
		if (!k->text)
			continue;
		if (g_strcmp0(section, k->dir) != 0) {
			section = k->dir;
			g_string_append_printf(values, "\n[%.*s]\n", (int) strlen(k->dir) - 2,
			                       k->dir + 1);
		}
		g_string_append_printf(values, "%s=%s\n", k->key, k->text);
	}
}

/* Writes `<keydir>/00-remotix` and `<keydir>/locks/00-remotix`; FALSE (and `*mistake`) if it cannot. */
static gboolean dconf_keyfiles_write(const char *keydir, GError **mistake)
{
	g_autofree char *lockdir = g_build_filename(keydir, "locks", NULL);
	g_autofree char *keyfile = g_build_filename(keydir, "00-remotix", NULL);
	g_autofree char *lockfile = g_build_filename(lockdir, "00-remotix", NULL);
	g_autoptr(GString) values = g_string_new(NULL);
	g_autoptr(GString) locks = g_string_new(NULL);

	dconf_keyfile_texts(values, locks);
	if (g_mkdir_with_parents(lockdir, 0755) != 0) {
		g_set_error(mistake, G_FILE_ERROR, g_file_error_from_errno(errno), "%s: %s", lockdir,
		            g_strerror(errno));
		return FALSE;
	}
	return g_file_set_contents(keyfile, values->str, -1, mistake) &&
	       g_file_set_contents(lockfile, locks->str, -1, mistake);
}

int session_dconf_keyfiles_write(const char *keydir)
{
	g_autoptr(GError) mistake = NULL;

	if (dconf_keyfiles_write(keydir, &mistake))
		return 0;
	fprintf(stderr, "remotix --dconf-keyfiles: %s\n", mistake ? mistake->message : "failed");
	return 1;
}

#define DCONF_SYSTEM_DB "/etc/dconf/db/remotix"
#define LOG_ROOT "rootside" /* the root side's log area, as in rootside.c */

/* ⭐ N5 (19 Nov 2026) — the SERVICE (root side) makes sure `/etc/dconf/db/remotix` is there and EQUAL to what the package's keyfiles
 * compile to: the postinst may have run before `dconf-cli` was configured (it is only a Recommends), or failed in an upgrade
 * and left the old database believed good.  How: compile to a temporary file at every start and replace the database only if the
 * bytes DIFFER (the compiler is deterministic) — chosen over comparing dates, which would not see an old database compiled AFTER the
 * package was built.  Same technique as the postinst (temporary file + rename, mode 0644).  Root runs `/usr/bin/dconf` by absolute
 * path (never a PATH search).  A line says what was done; if it cannot be done, the sessions run the declared fallback. */
void session_dconf_system_db_ensure(void)
{
	static const char *const KEYDIR = "/usr/share/remotix/dconf/remotix.d";
	static const char *const DCONF = "/usr/bin/dconf";
	g_autofree char *keyfile = g_build_filename(KEYDIR, "00-remotix", NULL);
	g_autofree char *lockfile = g_build_filename(KEYDIR, "locks", "00-remotix", NULL);
	g_autofree char *tmp = g_strdup_printf("%s.new.%d", DCONF_SYSTEM_DB, (int) getpid());
	g_autofree char *old = NULL;
	g_autofree char *fresh = NULL;
	gsize old_len = 0, fresh_len = 0;
	gboolean had = FALSE;
	const char *why = NULL, *failed = "";
	char *argv[] = { (char *) DCONF, "compile", tmp, (char *) KEYDIR, NULL };

	if (access(keyfile, R_OK) != 0 || access(lockfile, R_OK) != 0)
		return; /* a package without the keyfiles: nothing to compile from */
	/* the temporary files a fall left behind (only those, by name, in this folder) */
	{
		g_autoptr(GDir) d = g_dir_open("/etc/dconf/db", 0, NULL);
		const char *n;

		while (d && (n = g_dir_read_name(d))) {
			g_autofree char *leftover = NULL;

			if (!g_str_has_prefix(n, "remotix.new."))
				continue;
			leftover = g_build_filename("/etc/dconf/db", n, NULL);
			(void)unlink(leftover);
		}
	}
	had = g_file_get_contents(DCONF_SYSTEM_DB, &old, &old_len, NULL);
	if (access(DCONF, X_OK) != 0) {
		if (!had)
			registro_dice(LOG_ROOT, "⚠ D-015: %s is missing and %s (package dconf-cli) is missing: the GNOME remote sessions use "
			              "the declared fallback", DCONF_SYSTEM_DB, DCONF);
		return;
	}
	if (g_mkdir_with_parents("/etc/dconf/db", 0755) != 0) {
		failed = "cannot make /etc/dconf/db";
		goto bad;
	}
	if (!dconf_spawn(argv, NULL, NULL)) {
		failed = "`dconf compile` failed";
		goto bad;
	}
	if (!g_file_get_contents(tmp, &fresh, &fresh_len, NULL)) {
		failed = "the compiled file cannot be read";
		goto bad;
	}
	if (had && old_len == fresh_len && memcmp(old, fresh, old_len) == 0) {
		unlink(tmp); /* as it should be: nothing to say */
		return;
	}
	why = had ? "DIFFERENT from what the package's keyfiles compile to" : "missing";
	if (chmod(tmp, 0644) != 0 || rename(tmp, DCONF_SYSTEM_DB) != 0) {
		failed = g_strerror(errno);
		goto bad;
	}
	registro_dice(LOG_ROOT, "⭐ D-015: %s was %s: compiled now from %s", DCONF_SYSTEM_DB, why, KEYDIR);
	return;
bad:
	unlink(tmp);
	registro_dice(LOG_ROOT, had ? "⚠ D-015: %s may be stale and could NOT be put right (%s): the GNOME remote sessions use the "
	              "database that is there" : "⚠ D-015: %s is missing and could NOT be made (%s): the GNOME remote sessions use the "
	              "declared fallback", DCONF_SYSTEM_DB, failed);
}

/* Writes `locks.d/` (keyfile + locks) and compiles it into `<folder>/locks.db`:
 * to a temporary file, then RENAMED (never deleted: programs of a living session
 * have the old one open).  ⚠ Since 19 Nov 2026 this is the DECLARED FALLBACK (no `/etc/dconf/db/remotix`). */
static gboolean dconf_compile_locks(const char *folder)
{
	g_autofree char *keydir = g_build_filename(folder, "locks.d", NULL);
	g_autofree char *db = g_build_filename(folder, "locks.db", NULL);
	g_autofree char *tmp = g_strdup_printf("%s.new.%d", db, (int) getpid());
	g_autoptr(GError) mistake = NULL;
	char *argv[] = { "dconf", "compile", tmp, keydir, NULL };

	if (g_mkdir_with_parents(keydir, 0700) != 0 || !dconf_keyfiles_write(keydir, &mistake)) {
		registro_dice(LOG_SESSION, "⚠ D-015: locks.d not written in %s: %s", keydir,
		              mistake ? mistake->message : g_strerror(errno));
		return FALSE;
	}
	if (!dconf_spawn(argv, NULL, NULL)) {
		unlink(tmp);
		return FALSE;
	}
	if (rename(tmp, db) != 0) {
		registro_dice(LOG_SESSION, "⚠ D-015: %s not put in place: %s", db, g_strerror(errno));
		unlink(tmp);
		return FALSE;
	}
	return TRUE;
}

static char *dconf_profile_path(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, "remotix", "dconf", "profile", NULL);
}

/* ⭐ 19 Nov 2026 — the RUNTIME profile: `$XDG_RUNTIME_DIR/dconf/profile`, the file dconf reads when `DCONF_PROFILE` is not set.
 * Its first line is the mark that says it is ours (the end of the session touches no other). */
#define DCONF_RT_MARK "# REMOTIX-RUNTIME-PROFILE"
/* The head carries, when the administrator's own DCONF_PROFILE points to this file, the sign DCONF_RT_REF: the belt (stateless) then
 * REWRITES the file and never removes it (a variable pointing at a missing profile would mean no settings at all). */
#define DCONF_RT_REF "[referenced by DCONF_PROFILE: rewrite, never remove]"
static char *dconf_rt_head(gboolean full, gboolean referenced)
{
	return g_strdup_printf(DCONF_RT_MARK " (D-015, 19 Nov 2026)%s%s: %s\n", referenced ? " " : "", referenced ? DCONF_RT_REF : "",
	                       full ? "remote session — the locks are in system-db:remotix, the values that change in user-db:remotix."
	                            : "the remote session is over — the base profile alone.");
}

static char *dconf_runtime_profile_path(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, "dconf", "profile", NULL);
}

/* is `env` (a value of DCONF_PROFILE) one of OUR two files: the runtime one, or the fallback's */
static gboolean dconf_env_is_ours(const char *env)
{
	g_autofree char *old = dconf_profile_path();
	g_autofree char *rt = dconf_runtime_profile_path();

	return env && ((old && strcmp(env, old) == 0) || (rt && strcmp(env, rt) == 0));
}

static gboolean dconf_in_effect;
static gboolean dconf_runtime_mode;  /* the new model (system-db + user-db:remotix); FALSE = the declared fallback */
static gboolean dconf_admin_profile; /* the administrator's own DCONF_PROFILE was there: it stays the base, and we point it to our file */
static char *dconf_profile_file;     /* where `dconf_profile_full` lives: the runtime file, or the fallback's */
/* the texts of the profile file, as `session_dconf_prepare()` composed them */
static char *dconf_profile_full;    /* the session's: the layers */
static char *dconf_profile_neutral; /* the user's base alone (the fallback's file only: the runtime file's is computed) */

const char *session_dconf_object(void)
{
	return dconf_runtime_mode ? "/ca/desrt/dconf/Writer/remotix" : "/ca/desrt/dconf/shm/remotix";
}

/* The profile dconf would use WITHOUT us, in the order of
 * `dconf_engine_profile_open()`: `DCONF_PROFILE` (if it is not ours), the
 * runtime one, `user` in `/etc` and in the `XDG_DATA_DIRS`.  NULL = none, that is
 * dconf's default, «user-db:user». */
static char *dconf_base_profile(const char *env)
{
	g_autoptr(GPtrArray) candidates = g_ptr_array_new_with_free_func(g_free);
	const char *const *data = g_get_system_data_dirs();

	if (env && *env && !dconf_env_is_ours(env)) {
		if (env[0] == '/')
			g_ptr_array_add(candidates, g_strdup(env));
		else {
			g_ptr_array_add(candidates, g_build_filename("/etc/dconf/profile", env, NULL));
			for (int i = 0; data[i]; i++)
				g_ptr_array_add(candidates,
				                g_build_filename(data[i], "dconf", "profile", env, NULL));
		}
	} else {
		char *rt = dconf_runtime_profile_path(); /* B3: from the env, never glib's cached value (the root side's fork) */

		if (rt)
			g_ptr_array_add(candidates, rt);
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

/* The sources of the base profile `base` (the text of `dconf_base_profile()`), without our
 * own lines (the in-memory one, `system-db:remotix`, `user-db:remotix`, our `locks.db`): the first in `*first` (the writable one; «user-db:user» if there is none),
 * the others in `rest`, one per line.  Returns how many there were. */
static int dconf_base_sources(const char *base, char **first, GString *rest)
{
	g_auto(GStrv) lines = g_strsplit(base ? base : "", "\n", -1);
	int sources = 0;

	for (int i = 0; lines[i]; i++) {
		const char *r = g_strstrip(lines[i]);

		/* ⭐ 19 Nov 2026: our own lines, if the file we read is ours (the runtime file) or a fallback's */
		if (!*r || r[0] == '#' || g_strcmp0(r, DCONF_SESSION_SOURCE) == 0 ||
		    g_strcmp0(r, "system-db:remotix") == 0 || g_strcmp0(r, "user-db:remotix") == 0 ||
		    (g_str_has_prefix(r, "file-db:") && g_str_has_suffix(r, "/remotix/dconf/locks.db")))
			continue;
		if (g_str_has_prefix(r, "user-db:") || g_str_has_prefix(r, "system-db:") ||
		    g_str_has_prefix(r, "service-db:") || g_str_has_prefix(r, "file-db:")) {
			if (!*first)
				*first = g_strdup(r);
			else
				g_string_append_printf(rest, "%s\n", r);
			sources++;
		}
	}
	if (!*first)
		*first = g_strdup("user-db:user");
	return sources;
}

/* ⭐ 19 Nov 2026 — THE `lock-warning-shown` FILE: where it is, and the SIGN that we made it.
 *    The birth (`session_gnome_lock_warning()`, below) makes an empty `~/.local/share/gnome-shell/lock-warning-shown` so
 *    that the Shell does not warn «Screen Lock disabled».  A principle of the product: at the END of the session REMOTIX
 *    leaves nothing of its own in the user's home.  ⇒ The sign «we made it» lives in the session's state folder
 *    (`$XDG_RUNTIME_DIR/remotix/lock-warning-made`), like the manager's photo, and not in memory: the end of the session
 *    may be done by ANOTHER process (the child that exits, the root side's fork after a local login).  The sign holds
 *    the inode and the ctime of the file, whether the folder `gnome-shell` was made by us too, and THE PATH of that
 *    folder: the end does not recompute it (the root side's fork has no `XDG_DATA_HOME`, and a user who sets it with
 *    pam_env would be looked for in the wrong place).  The path at birth comes from `HOME`/`XDG_DATA_HOME`, not from
 *    `g_get_user_data_dir()`, which glib caches. */
static char *lock_warning_folder(void)
{
	const char *data = g_getenv("XDG_DATA_HOME");
	const char *home = g_getenv("HOME");

	if (data && data[0] == '/')
		return g_build_filename(data, "gnome-shell", NULL);
	if (!home || !*home)
		home = g_get_home_dir();
	return home && *home ? g_build_filename(home, ".local", "share", "gnome-shell", NULL) : NULL;
}

static char *lock_warning_mark_path(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "lock-warning-made", NULL) : NULL;
}

struct lock_mark {
	unsigned long long ino;
	long long ctime_s, ctime_ns;
	int made_dir;
	char *folder;
};

static bool lock_mark_read(const char *mark, struct lock_mark *m)
{
	g_autofree char *text = NULL;
	const char *f;

	memset(m, 0, sizeof *m);
	if (!mark || !g_file_get_contents(mark, &text, NULL, NULL))
		return false;
	if (sscanf(text, "ino=%llu ctime=%lld.%lld dir=%d", &m->ino, &m->ctime_s, &m->ctime_ns, &m->made_dir) != 4 || !m->ino)
		return false;
	f = strstr(text, "folder=");
	if (!f || f[7] != '/')
		return false;
	m->folder = g_strdup(f + 7);
	g_strchomp(m->folder);
	return true;
}

/* is this stat the very file we made: regular, empty, same inode, same ctime */
static bool lock_mark_matches(const struct lock_mark *m, const struct stat *st)
{
	return S_ISREG(st->st_mode) && st->st_size == 0 && (unsigned long long)st->st_ino == m->ino &&
	       (long long)st->st_ctim.tv_sec == m->ctime_s && (long long)st->st_ctim.tv_nsec == m->ctime_ns;
}

/* The end of the session: the file goes away if (and only if) WE made it, it is still that same empty regular file, and
 * no symlink is involved.  Called from `session_dconf_neutralise()`, that every road of closing already calls (normal
 * end, SIGTERM, light close, the child's exit, the root side's fork).  Idempotent; with no sign it does nothing. */
static void session_gnome_lock_warning_undo(const char *why)
{
	g_autofree char *mark = lock_warning_mark_path();
	g_autofree char *parent = NULL;
	g_autofree char *leaf = NULL;
	struct lock_mark m;
	struct stat st;
	bool gone = false;
	int dir, up;

	if (!lock_mark_read(mark, &m)) {
		if (mark && g_file_test(mark, G_FILE_TEST_EXISTS))
			g_unlink(mark); /* unreadable sign: not a license to touch anything */
		return;
	}
	dir = open(m.folder, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
	if (dir < 0) {
		registro_dice(LOG_SESSION,
		              "⚠ GNOME (%s): %s cannot be opened as a folder (%s): lock-warning-shown left alone",
		              why, m.folder, g_strerror(errno));
		g_unlink(mark);
		g_free(m.folder);
		return;
	}
	if (fstatat(dir, "lock-warning-shown", &st, AT_SYMLINK_NOFOLLOW) != 0) {
		gone = errno == ENOENT; /* the Shell with GDM deletes it itself: nothing to do, no error */
	} else if (lock_mark_matches(&m, &st)) {
		if (unlinkat(dir, "lock-warning-shown", 0) == 0) {
			gone = true;
			registro_dice(LOG_SESSION,
			              "⭐ GNOME (%s): %s/lock-warning-shown, made by REMOTIX at birth, removed: nothing of ours is left "
			              "in the user's home", why, m.folder);
		} else
			registro_dice(LOG_SESSION, "⚠ GNOME (%s): %s/lock-warning-shown NOT removed (%s)", why, m.folder,
			              g_strerror(errno));
	} else
		registro_dice(LOG_SESSION,
		              "⭐ GNOME (%s): %s/lock-warning-shown is no longer the empty file we made (changed, replaced, other "
		              "inode or not a regular file): left alone", why, m.folder);
	close(dir);
	/* the folder we made, now empty: only that one, relative to its parent (`unlinkat(AT_REMOVEDIR)` fails by itself
	 * if anything is inside, or if a symlink took its place) */
	if (m.made_dir && gone) {
		parent = g_path_get_dirname(m.folder);
		leaf = g_path_get_basename(m.folder);
		up = open(parent, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
		if (up >= 0) {
			if (unlinkat(up, leaf, AT_REMOVEDIR) == 0)
				registro_dice(LOG_SESSION,
				              "⭐ GNOME (%s): the folder %s, made by REMOTIX, was empty and is removed", why, m.folder);
			close(up);
		}
	}
	g_unlink(mark);
	g_free(m.folder);
}

#define DCONF_NEUTRAL_HEAD \
	"# REMOTIX (D-015): the remote session is over — the user's base profile alone.\n"

/*
 * ⭐ 14 Nov 2026 — THE PROFILE NEUTRALISED (the box above `DCONF_SESSION_SOURCE`).
 * The profile file becomes the user's base alone, written to a temporary file and RENAMED
 * (`g_file_set_contents`).  Only if the file is there (GNOME, a session that was prepared);
 * `locks.db` stays.  Programs already open keep the profile they read when they were born.
 */
static GHashTable *handler_environment(GDBusConnection *bus);

static void dconf_neutralise_old(const char *why)
{
	g_autofree char *fpath = dconf_profile_path();
	g_autofree char *now = NULL;
	g_autofree char *composed = NULL;
	g_autoptr(GError) mistake = NULL;
	const char *text = dconf_profile_neutral;

	if (!fpath || !g_file_get_contents(fpath, &now, NULL, NULL))
		return;
	if (!text) {
		/* a child that did not prepare the session's dconf (close-only): its
		 * `DCONF_PROFILE` is not ours, so the base is read as dconf would */
		g_autofree char *base = dconf_base_profile(g_getenv("DCONF_PROFILE"));
		g_autofree char *first = NULL;
		g_autoptr(GString) rest = g_string_new(NULL);

		dconf_base_sources(base, &first, rest);
		composed = g_strdup_printf(DCONF_NEUTRAL_HEAD "%s\n%s", first, rest->str);
		text = composed;
	}
	if (strcmp(now, text) == 0)
		return;
	if (g_file_set_contents(fpath, text, -1, &mistake))
		registro_dice(LOG_SESSION,
		              "⭐ D-015 (%s): the session's dconf profile %s is NEUTRALISED — the "
		              "user's base alone, without our locks and without the in-memory "
		              "database: whoever inherited DCONF_PROFILE reads the normal settings "
		              "(locks.db stays; the next startup or birth puts the three layers back)",
		              why, fpath);
	else
		registro_dice(LOG_SESSION,
		              "⛔ D-015 (%s): the session's dconf profile %s is NOT neutralised (%s) — "
		              "whoever inherited DCONF_PROFILE would still read our locks",
		              why, fpath, mistake->message);
}

/*
 * ⭐ 19 Nov 2026 — THE BELT, on the RUNTIME file.  Stateless (it runs also in the root side's fork and in a close-only child): the
 * file is touched ONLY if its first line is our mark; the base profile is read from it (without our lines) as `dconf_base_profile()`
 * does.  If the base is the default alone («user-db:user»), the file is REMOVED: an absent file is exactly what a local login
 * had before we came (dconf's own default), and nothing stays that could change a later LOCAL session.  Otherwise it is rewritten
 * (temporary file + rename) with the base alone, under a head that still carries the mark.  ⚠ Exception: if the head carries
 * `DCONF_RT_REF` (an administrator's DCONF_PROFILE points to this file) it is always rewritten, never removed.
 * ⛔ Never under a live desktop (the callers).
 */
static void dconf_neutralise_runtime(const char *why)
{
	g_autofree char *rt = dconf_runtime_profile_path();
	g_autofree char *now = NULL;
	g_autofree char *base = NULL;
	g_autofree char *first = NULL;
	g_autofree char *text = NULL;
	g_autofree char *head = NULL;
	g_autoptr(GString) rest = g_string_new(NULL);
	g_autoptr(GError) mistake = NULL;
	gboolean referenced;

	if (!rt || !g_file_get_contents(rt, &now, NULL, NULL) || !g_str_has_prefix(now, DCONF_RT_MARK))
		return;
	{
		g_autofree char *line1 = g_strndup(now, strcspn(now, "\n"));

		referenced = strstr(line1, DCONF_RT_REF) != NULL;
	}
	base = dconf_base_profile(g_getenv("DCONF_PROFILE"));
	dconf_base_sources(base, &first, rest);
	if (!referenced && !rest->len && strcmp(first, "user-db:user") == 0) {
		if (unlink(rt) == 0)
			registro_dice(LOG_SESSION,
			              "⭐ D-015 (%s): the runtime dconf profile %s is REMOVED — the base was the default alone, "
			              "so a program born now reads the normal settings (what a local login finds)", why, rt);
		else
			registro_dice(LOG_SESSION,
			              "⛔ D-015 (%s): the runtime dconf profile %s is NOT removed (%s) — whoever is born now "
			              "would still read our locks", why, rt, g_strerror(errno));
		return;
	}
	head = dconf_rt_head(FALSE, referenced);
	text = g_strdup_printf("%s%s\n%s", head, first, rest->str);
	if (strcmp(now, text) == 0)
		return;
	if (g_file_set_contents(rt, text, -1, &mistake))
		registro_dice(LOG_SESSION,
		              "⭐ D-015 (%s): the runtime dconf profile %s is NEUTRALISED — the base alone, without our "
		              "database and our locks (the next startup or birth puts the layers back)", why, rt);
	else
		registro_dice(LOG_SESSION,
		              "⛔ D-015 (%s): the runtime dconf profile %s is NOT neutralised (%s) — whoever is born now "
		              "would still read our locks", why, rt, mistake->message);
}

void session_dconf_neutralise(const char *why)
{
	/* ⭐ 19 Nov 2026: every road that ends a session passes here: the file we made at birth goes too (see above) */
	session_gnome_lock_warning_undo(why);
	dconf_neutralise_old(why);
	dconf_neutralise_runtime(why);
}

/* ⭐ At every BIRTH: the session's profile back in the file, if the end of the session
 *    before had neutralised it.  ⛔ No `g_setenv` here (threads alive): the environment is already as
 *    `session_dconf_prepare()` left it (19 Nov 2026: no DCONF_PROFILE at all, except the fallback and the
 *    administrator's own profile). */
static void dconf_profile_reinstate(void)
{
	const char *fpath = dconf_profile_file;
	g_autofree char *now = NULL;
	g_autofree char *folder = NULL;
	g_autoptr(GError) mistake = NULL;

	if (!dconf_in_effect || !dconf_profile_full || !fpath)
		return;
	if (g_file_get_contents(fpath, &now, NULL, NULL)) {
		if (strcmp(now, dconf_profile_full) == 0)
			return;
		/* B1: a runtime file that is not ours (put there since the child's start) is never overwritten */
		if (dconf_runtime_mode && !g_str_has_prefix(now, DCONF_RT_MARK)) {
			registro_dice(LOG_SESSION,
			              "⛔ D-015: birth — %s exists and is NOT ours (no mark): left alone, so the session is born WITHOUT "
			              "our locks and our database", fpath);
			return;
		}
	}
	folder = g_path_get_dirname(fpath);
	g_mkdir_with_parents(folder, 0700); /* the runtime file may have been removed with nothing else in its folder */
	if (g_file_set_contents(fpath, dconf_profile_full, -1, &mistake))
		registro_dice(LOG_SESSION,
		              "⭐ D-015: birth — the session's dconf profile %s is back to the "
		              "session's layers (it had been neutralised at the end of the one before)",
		              fpath);
	else
		registro_dice(LOG_SESSION,
		              "⛔ D-015: birth — the session's dconf profile %s is NOT put back (%s): "
		              "the session would be born WITHOUT our locks",
		              fpath, mistake->message);
}

bool session_dconf_prepare(void)
{
	g_autofree char *fpath = dconf_profile_path();
	g_autofree char *folder = NULL;
	g_autofree char *mandatory = NULL;
	g_autofree char *base = NULL;
	g_autoptr(GString) profile = g_string_new(NULL);
	g_autoptr(GString) rest = g_string_new(NULL);
	g_autofree char *first = NULL;
	g_autofree char *locks_db = NULL;
	g_autofree char *user_profile = NULL;
	g_autoptr(GError) mistake = NULL;
	g_autofree char *env0 = g_strdup(g_getenv("DCONF_PROFILE")); /* what we were born with, before we touch the environment */
	g_autofree char *env_base = NULL;                              /* the DCONF_PROFILE that gives the BASE profile, if any */
	SessionLife life;
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

	/* ⭐ ORDER (19 Nov 2026, review): everything up to the changes to the ENVIRONMENT (`g_setenv`/`g_unsetenv`) needs no bus; the
	 *    user's bus is opened only AFTER them (GDBus starts a worker thread, and `g_setenv` must not be done with other threads
	 *    alive).  What comes after is read-only: the thread just waits. */
	folder = g_path_get_dirname(fpath);
	if (g_mkdir_with_parents(folder, 0700) != 0) {
		registro_dice(LOG_SESSION,
		              "⛔ D-015: the session's dconf folder cannot be created (%s): %s — "
		              "and so the negotiated layout is NOT written",
		              folder, g_strerror(errno));
		return false;
	}
	/* ⭐ 19 Nov 2026: the locks are the SYSTEM database `/etc/dconf/db/remotix` (the package compiled it) and the runtime
	 *    profile is the file dconf reads without `DCONF_PROFILE`.  Without the database, or without `dconf` (the dconf engine's
	 *    own readers do not need it, but the birth reads the user's values with it), the old model: DECLARED FALLBACK. */
	{
		g_autofree char *found = g_find_program_in_path("dconf");
		g_autofree char *rt = dconf_runtime_profile_path();
		g_autofree char *rt_now = NULL;
		gboolean foreign = FALSE;

		/* B1: a runtime profile that is not ours (an administrator's, another program's) is never overwritten, nor
		 *     rewritten or removed at the end: the old model, which already takes it as the BASE profile */
		if (rt && g_file_get_contents(rt, &rt_now, NULL, NULL) && !g_str_has_prefix(rt_now, DCONF_RT_MARK))
			foreign = TRUE;
		dconf_runtime_mode = found && !foreign && access(DCONF_SYSTEM_DB, R_OK) == 0;
		if (!dconf_runtime_mode)
			registro_dice(LOG_SESSION,
			              "⚠ DECLARED FALLBACK, D-015 (19 Nov 2026): %s — the session dconf goes back to the "
			              "model of 1.0.0: three layers compiled now, `DCONF_PROFILE` in the session (Flutter and snap "
			              "programs may complain about it)",
			              !found ? "`dconf` is missing"
			              : foreign ? "the runtime dconf profile already there is not ours (no mark): left untouched, taken as the base"
			                        : DCONF_SYSTEM_DB " is missing or not readable");
		if (dconf_runtime_mode && rt) {
			g_autofree char *rtfolder = g_path_get_dirname(rt);

			if (g_mkdir_with_parents(rtfolder, 0700) != 0) {
				registro_dice(LOG_SESSION,
				              "⛔ D-015: %s cannot be created: %s — and so the negotiated layout is NOT written",
				              rtfolder, g_strerror(errno));
				return false;
			}
		}
	}
	/* an administrator's DCONF_PROFILE in OUR environment is the BASE profile and must not shadow our file */
	dconf_admin_profile = env0 && *env0 && !dconf_env_is_ours(env0);
	if (dconf_admin_profile)
		env_base = g_strdup(env0);
	/* ⛔ Before any `GSettings` of the child (the dconf engine reads the profile only once, when it is born) and BEFORE the bus:
	 *    ⭐ 19 Nov 2026: in the new model the variable is NOT set (dconf reads the runtime file) and one inherited from the
	 *    administrator is replaced by our file's path (`compose_environment()` tells the session the same).  The fallback sets
	 *    the old file's path, as 1.0.0 did. */
	if (!dconf_runtime_mode)
		g_setenv("DCONF_PROFILE", fpath, TRUE);
	else if (dconf_admin_profile) {
		g_autofree char *rt = dconf_runtime_profile_path();

		g_setenv("DCONF_PROFILE", rt, TRUE);
	} else
		g_unsetenv("DCONF_PROFILE");
	/* ── from here on: the bus (reads only) ── */
	/* ⭐ N3b: an administrator's DCONF_PROFILE may live ONLY in the user manager (`environment.d`), not in our environment: the
	 *    Shell would inherit it and ignore our file.  Looked for there too (no change to our own environment: the child's
	 *    engine, with no variable, already reads our file); a value that is ours (left by an earlier version of the package)
	 *    does not count — the clear-out removes it. */
	if (!dconf_admin_profile) {
		g_autoptr(GDBusConnection) mbus = sess_bus(NULL);
		g_autoptr(GHashTable) menv = mbus ? handler_environment(mbus) : NULL;
		const char *v = menv ? g_hash_table_lookup(menv, "DCONF_PROFILE") : NULL;

		if (v && *v && !dconf_env_is_ours(v)) {
			env_base = g_strdup(v);
			dconf_admin_profile = TRUE;
			registro_dice(LOG_SESSION, "⭐ D-015: a DCONF_PROFILE «%s» is in the user manager's environment (not ours): it is "
			              "the BASE profile, and the session is told our file instead", v);
		}
	}
	base = dconf_base_profile(env_base);
	sources = dconf_base_sources(base, &first, rest);
	/* alive / dead / UNKNOWN (never «unknown = dead»: the rule of `session_life()`) decides what is done to the runtime file */
	life = session_life();
	if (dconf_runtime_mode) {
		g_free(fpath);
		fpath = dconf_runtime_profile_path();
		dconf_locked = TRUE;
		{
			g_autofree char *head = dconf_rt_head(TRUE, dconf_admin_profile);

			g_string_append_printf(profile, "%s%s\nsystem-db:remotix\nuser-db:remotix\n%s", head, first, rest->str);
		}
	} else {
		/* a runtime file of ours left by a run that had the database must not outlive the choice made now — N6: but never
		 * under a live desktop */
		if (life == SESSION_LIFE_DEAD)
			dconf_neutralise_runtime("fallback: no system database");
		else if (life == SESSION_LIFE_UNKNOWN)
			registro_dice(LOG_SESSION, "⚠ D-015: the desktop's life is UNKNOWN (no answer yet): a runtime profile of ours, if "
			              "there is one, is left as it is (never removed under a desktop that may be alive)");
		dconf_locked = dconf_compile_locks(folder);
	}
	if (dconf_runtime_mode) {
		/* the profile text is already composed; written below */
	} else if (dconf_locked) {
		locks_db = g_build_filename(folder, "locks.db", NULL);
		g_string_append_printf(profile,
		                       "# REMOTIX (D-015): the dconf of the remote session, three layers:\n"
		                       "# the user's (writable, stays), our locks, the in-memory database.\n"
		                       "%s\nfile-db:%s\n" DCONF_SESSION_SOURCE "\n%s",
		                       first, locks_db, rest->str);
	} else {
		registro_dice(LOG_SESSION,
		              "⚠ DECLARED FALLBACK, D-015: `dconf compile` is missing or failed — "
		              "the session dconf goes back to the old model (the in-memory database "
		              "on top, the user's below): what the user changes from remote is "
		              "NOT kept (`dconf-cli` is the package that provides it)");
		g_string_append_printf(profile,
		                       "# REMOTIX (D-015): FALLBACK, in-memory database on top.\n"
		                       DCONF_SESSION_SOURCE "\n%s\n%s",
		                       first, rest->str);
	}
	/* The user's base alone: to read the user's real values (seed, restore). */
	user_profile = g_build_filename(folder, "profile-user", NULL);
	if (!g_file_set_contents(user_profile, first, -1, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⚠ D-015: %s not written (%s): the user's layout will not be copied "
		              "into the session",
		              user_profile, mistake->message);
		g_clear_error(&mistake);
	}
	/* ⭐ N1 (19 Nov 2026): the RUNTIME file is a window onto every program of the user, a LOCAL login included: it is written
	 *    now ONLY if there is a live remote desktop to serve (a child that found one again); otherwise the BIRTH writes it
	 *    (`dconf_profile_reinstate()`), so a child that dies between its start and the birth leaves nothing.  (A stale file of
	 *    ours left by an earlier fall is neutralised.)  Nothing before the birth reads it: the user's real values are read
	 *    with `profile-user`, and the first GSettings of the child is after the birth. */
	if (dconf_runtime_mode && life == SESSION_LIFE_DEAD) {
		dconf_neutralise_runtime("child startup: no live desktop");
		registro_dice(LOG_SESSION, "⭐ D-015: no live remote desktop at the child's start: the runtime profile %s is written at "
		              "the birth, not now", fpath);
	} else if (dconf_runtime_mode && life == SESSION_LIFE_UNKNOWN) {
		registro_dice(LOG_SESSION, "⚠ D-015: the desktop's life is UNKNOWN at the child's start (no answer yet): the runtime "
		              "profile %s is NOT touched — neither written nor removed; the birth writes it if it is not there", fpath);
	} else if (!g_file_set_contents(fpath, profile->str, -1, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⛔ D-015: the session's dconf profile cannot be written (%s): %s — "
		              "and so the negotiated layout is NOT written",
		              fpath, mistake->message);
		/* the environment goes back to what we were born with (the file it names is not there) */
		if (env0)
			g_setenv("DCONF_PROFILE", env0, TRUE);
		else
			g_unsetenv("DCONF_PROFILE");
		return false;
	}
	/* ⭐ 14 Nov 2026: the two texts are kept — the end of the session writes the neutral
	 *    one, the birth puts this one back (`session_dconf_neutralise()`). */
	g_free(dconf_profile_full);
	dconf_profile_full = g_strdup(profile->str);
	g_free(dconf_profile_neutral);
	dconf_profile_neutral = g_strdup_printf(DCONF_NEUTRAL_HEAD "%s\n%s", first, rest->str);
	g_free(dconf_profile_file);
	dconf_profile_file = g_strdup(fpath);
	dconf_in_effect = TRUE;
	registro_dice(LOG_SESSION,
	              "⭐ D-015: SESSION dconf in %s (%s; base profile: %s): the user's "
	              "settings stay the user's, the session's rules live in the session only",
	              fpath,
	              dconf_runtime_mode ? (dconf_admin_profile ? "RUNTIME profile (an administrator's DCONF_PROFILE points to it): system-db:remotix (locks) + user-db:remotix (values)"
	                                                         : "RUNTIME profile, no DCONF_PROFILE: system-db:remotix (locks) + user-db:remotix (values)")
	              : dconf_locked ? "FALLBACK: three layers, locks.db compiled" : "FALLBACK",
	              sources ? "the system's" : "user-db:user");
	return true;
}

bool session_dconf_of_session(void)
{
	const char *env = g_getenv("DCONF_PROFILE");

	if (!dconf_in_effect || !dconf_profile_file)
		return FALSE;
	/* the runtime model: no variable (dconf reads the runtime file) or, with an administrator's profile, our file's path.
	 * ⭐ N1: the file itself may not be there yet (it is written at the birth) — the state is the child's, not the file's */
	if (dconf_runtime_mode)
		return !env || !*env || strcmp(env, dconf_profile_file) == 0;
	return g_strcmp0(env, dconf_profile_file) == 0 && g_file_test(dconf_profile_file, G_FILE_TEST_EXISTS);
}

/*
 * A direct write to a `dconf-service` writer — `object` is
 * `/ca/desrt/dconf/Writer/remotix` (the session: user-db `remotix`, 19 Nov 2026), `/ca/desrt/dconf/shm/remotix` (the session, in the
 * declared fallback) or `/ca/desrt/dconf/Writer/user`
 * (the USER) — without going through the process's engine, which has the
 * session profile.  `value` NULL = remove (`fpath` ending with `/`: the whole
 * folder).
 * `[R]` dconf 0.40: `ca.desrt.dconf.Writer.Change` wants the bytes of an
 *    `a{smv}` (`dconf_changeset_serialise`); the writer notifies the readers
 *    (`Notify`), so the Shell and the `gsd-*` see the change at once.
 */
gboolean dconf_change(const char *object, const char *fpath, GVariant *value,
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

/* The user's REAL value of a key (a profile with only the user's database), NULL if
 * unset.  `type` is the GVariant type string. */
static GVariant *dconf_read_user(const char *path, const char *type)
{
	g_autofree char *fpath = dconf_profile_path();
	g_autofree char *folder = fpath ? g_path_get_dirname(fpath) : NULL;
	g_autofree char *uprofile = folder ? g_build_filename(folder, "profile-user", NULL) : NULL;
	g_autofree char *out = NULL;
	char *argv[] = { "dconf", "read", (char *) path, NULL };

	if (!uprofile || !g_file_test(uprofile, G_FILE_TEST_EXISTS) ||
	    !dconf_spawn(argv, uprofile, &out) || !out)
		return NULL;
	g_strstrip(out);
	if (!*out)
		return NULL;
	return g_variant_parse(G_VARIANT_TYPE(type), out, NULL, NULL, NULL);
}

/* ⭐ ONCE ONLY: the four keys that older versions wrote in the USER's file are removed from
 * it if they hold EXACTLY what REMOTIX wrote (the user's decision of 13 Nov 2026).  The mark
 * is in `$XDG_STATE_HOME/remotix/gnome-ripristinato`; without `dconf` it is not written. */
static void session_dconf_restore_once(void)
{
	static const struct { const char *path, *type, *text; } OLD[] = {
		{ "/org/gnome/settings-daemon/plugins/power/sleep-inactive-ac-type", "s", "'nothing'" },
		{ "/org/gnome/settings-daemon/plugins/power/sleep-inactive-battery-type", "s", "'nothing'" },
		{ "/org/gnome/desktop/session/idle-delay", "u", "uint32 0" },
		{ "/org/gnome/desktop/screensaver/lock-enabled", "b", "false" },
	};
	g_autofree char *folder = g_build_filename(g_get_user_state_dir(), "remotix", NULL);
	g_autofree char *mark = g_build_filename(folder, "gnome-ripristinato", NULL);
	g_autoptr(GError) mistake = NULL;
	g_autofree char *found = g_find_program_in_path("dconf");
	int removed = 0, failed = 0;

	if (g_file_test(mark, G_FILE_TEST_EXISTS))
		return;
	if (!found) {
		registro_dice(LOG_SESSION,
		              "⚠ D-015: `dconf` is missing: the old values in the user's file "
		              "are not restored (they will be at the first session with it)");
		return;
	}
	for (guint i = 0; i < G_N_ELEMENTS(OLD); i++) {
		g_autoptr(GVariant) now = dconf_read_user(OLD[i].path, OLD[i].type);
		g_autoptr(GVariant) was = g_variant_parse(G_VARIANT_TYPE(OLD[i].type), OLD[i].text,
		                                          NULL, NULL, NULL);

		if (!now || !was || !g_variant_equal(now, was))
			continue;
		g_clear_error(&mistake);
		if (dconf_change(DCONF_USER_OBJECT, OLD[i].path, NULL, &mistake)) {
			removed++;
			registro_dice(LOG_SESSION,
			              "⭐ D-015: %s was REMOTIX's old value in the user's file: "
			              "removed (the desktop's own default is back)",
			              OLD[i].path);
		} else {
			failed++;
			registro_dice(LOG_SESSION, "⚠ D-015: %s NOT removed from the user's file (%s)",
			              OLD[i].path, mistake ? mistake->message : "no reason given");
		}
	}
	if (failed)
		return; /* no mark: next birth tries again */
	g_clear_error(&mistake);
	if (g_mkdir_with_parents(folder, 0700) != 0 ||
	    !g_file_set_contents(mark, "1\n", -1, &mistake))
		registro_dice(LOG_SESSION, "⚠ D-015: mark %s not written (%s)", mark,
		              mistake ? mistake->message : g_strerror(errno));
	else
		registro_dice(LOG_SESSION,
		              "⭐ D-015: one-time restore of the user's file done (%d keys removed)",
		              removed);
}

/* ⭐ The birth of the session's dconf: the session's database (`user-db:remotix`, or `shm` in the fallback) emptied; the user's real layout copied
 * into it (locked mode) or the session's keys written into it (fallback); once, the
 * old values of the user's file restored. */
static void session_dconf_birth(void)
{
	static const struct { const char *path, *type; } SEED[] = {
		{ "/org/gnome/desktop/input-sources/sources", "a(ss)" },
		{ "/org/gnome/desktop/input-sources/current", "u" },
		{ "/org/gnome/desktop/input-sources/mru-sources", "a(ss)" },
	};
	g_autoptr(GError) mistake = NULL;

	if (!session_dconf_of_session())
		return;
	session_dconf_reset();
	session_dconf_restore_once();
	if (dconf_locked) {
		for (guint i = 0; i < G_N_ELEMENTS(SEED); i++) {
			g_autoptr(GVariant) v = dconf_read_user(SEED[i].path, SEED[i].type);

			if (!v)
				continue;
			g_clear_error(&mistake);
			if (!dconf_change(DCONF_SESSION_OBJECT, SEED[i].path, v, &mistake))
				registro_dice(LOG_SESSION,
				              "⚠ D-015: %s of the user not copied into the session (%s)",
				              SEED[i].path, mistake ? mistake->message : "no reason given");
		}
		return;
	}
	for (guint i = 0; i < G_N_ELEMENTS(DCONF_KEYS); i++) {
		const struct dconf_key *k = &DCONF_KEYS[i];
		g_autofree char *path = g_strconcat(k->dir, k->key, NULL);
		GVariant *v = k->text ? g_variant_parse(NULL, k->text, NULL, NULL, NULL) : NULL;

		if (!v)
			continue;
		g_clear_error(&mistake);
		if (!dconf_change(DCONF_SESSION_OBJECT, path, v, &mistake))
			registro_dice(LOG_SESSION, "⛔ D-015 fallback: %s NOT written in the session (%s)",
			              path, mistake ? mistake->message : "no reason given");
	}
}

/* ⭐ 18 Nov 2026 (Ubuntu 26.04, GNOME 50): the Shell warns «Screen Lock disabled — Screen Locking
 *    requires the GNOME display manager» the FIRST time a user ever has a session without GDM
 *    (`_handleLockScreenWarning()`, `js/ui/main.js`): it touches `lock-warning-shown` in its data
 *    folder and, only if it has just created the file, shows the notice.  Our session never has
 *    GDM (and never a lock screen, by design), so the notice would be a banner on the first
 *    desktop of every user for something that is not a fault.
 * ⭐ The cure is the file itself, made empty BEFORE the Shell starts: exactly what the Shell
 *    would leave behind, so it finds it and says nothing.  And only that:
 *    · an existing file (or a symlink, even a dangling one) is NEVER touched (`O_EXCL`
 *      + `O_NOFOLLOW`): it means the Shell, or the user, already did;
 *    · the LAST folder (`gnome-shell`) is opened with `O_NOFOLLOW`: a symlink in its place is not
 *      followed; the levels above it (`~/.local`, `~/.local/share`) ARE followed, we are the user in
 *      their own home;
 *    · we are the user here (the child), so the owner is right by construction.
 * ⚠ A later LOCAL login of the same user, which has GDM, makes the Shell DELETE this file
 *   (same function, «hasLockScreen» branch) and shows nothing: the file is not left behind
 *   to hide anything there.
 * ⭐ 19 Nov 2026: and it does not stay in the home at the END of the session (principle of the product, check
 *   `settings-intact`): when WE made it (`O_EXCL` succeeded) a sign goes into the session's state folder
 *   (`lock_warning_mark_path()`) and `session_gnome_lock_warning_undo()` removes the file — and the folder, if we made
 *   that too and it is empty — from every road that ends a session.  The next birth makes it again; if a session ended
 *   badly (child killed) and the sign still matches the very same file, the birth only CONFIRMS it is still ours. */
static void session_gnome_lock_warning(void)
{
	g_autofree char *folder = lock_warning_folder();
	g_autofree char *mark = lock_warning_mark_path();
	bool had_dir;
	int dir, fd;

	if (!folder)
		return;
	had_dir = g_file_test(folder, G_FILE_TEST_IS_DIR);
	if (g_mkdir_with_parents(folder, 0700) != 0) {
		registro_dice(LOG_SESSION,
		              "⚠ GNOME: %s cannot be created (%s): the «Screen Lock disabled» notice may show once",
		              folder, g_strerror(errno));
		return;
	}
	dir = open(folder, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
	if (dir < 0) {
		registro_dice(LOG_SESSION,
		              "⚠ GNOME: %s cannot be opened as a folder (%s): left alone, the «Screen Lock "
		              "disabled» notice may show once",
		              folder, g_strerror(errno));
		return;
	}
	fd = openat(dir, "lock-warning-shown", O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
	if (fd >= 0) {
		struct stat st;
		g_autofree char *run_folder = mark ? g_path_get_dirname(mark) : NULL;
		g_autofree char *text = NULL;
		bool signed_ok = false;

		/* ⭐ 19 Nov 2026: the sign that WE made it (and the folder too, and where), for the end of the session */
		if (mark && run_folder && fstat(fd, &st) == 0 && g_mkdir_with_parents(run_folder, 0700) == 0) {
			text = g_strdup_printf("ino=%llu ctime=%lld.%lld dir=%d folder=%s\n", (unsigned long long)st.st_ino,
			                       (long long)st.st_ctim.tv_sec, (long long)st.st_ctim.tv_nsec, had_dir ? 0 : 1, folder);
			signed_ok = g_file_set_contents(mark, text, -1, NULL);
		}
		close(fd);
		if (signed_ok)
			registro_dice(LOG_SESSION,
			              "⭐ GNOME: %s/lock-warning-shown made (empty): the Shell will not warn that "
			              "Screen Lock needs the display manager — this session has none by design; it goes away "
			              "at the end of the session (we made it)",
			              folder);
		else {
			if (mark)
				g_unlink(mark); /* an old sign must not vouch for this file */
			registro_dice(LOG_SESSION,
			              "⚠ GNOME: %s/lock-warning-shown made (empty) but the sign %s could NOT be written: the file "
			              "will STAY in the home at the end of the session", folder, mark ? mark : "(no runtime folder)");
		}
	} else if (errno == EEXIST) {
		/* ours still, from a session that did not end cleanly (child killed)?  The sign says; the very same file
		 * and the same folder → it stays ours (the next END removes it); anything else → not ours, the stale sign is
		 * dropped. */
		struct stat st;
		struct lock_mark m;

		if (mark && g_file_test(mark, G_FILE_TEST_EXISTS)) {
			if (!lock_mark_read(mark, &m) || g_strcmp0(m.folder, folder) != 0 ||
			    fstatat(dir, "lock-warning-shown", &st, AT_SYMLINK_NOFOLLOW) != 0 || !lock_mark_matches(&m, &st))
				g_unlink(mark);
			g_free(m.folder);
		}
	} else {
		registro_dice(LOG_SESSION,
		              "⚠ GNOME: %s/lock-warning-shown not made (%s): the notice may show once",
		              folder, g_strerror(errno));
	}
	close(dir);
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

/* the session's commands (`lxqt-leave`, `lxqt-powermanagement`, the X11 composition managers), at
 * the head of the PATH */
static char *lxqt_session_bin_folder(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "bin-lxqt", NULL)
	                           : NULL;
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
 * ⭐ 14 Nov 2026 (D-153) — THE SESSION'S OWN FOLDERS, AS A LOCAL LOGIN GIVES THEM.
 *
 * `[M]` Xubuntu 26.04: a local login runs `/etc/X11/Xsession.d/60x11-common_xdg_path` with
 * `DESKTOP_SESSION=<session>` (lightdm: `xubuntu`), which puts `/etc/xdg/xdg-<session>` in
 * front of `XDG_CONFIG_DIRS` and `/usr/share/<session>` in front of `XDG_DATA_DIRS` (not for
 * `gnome`, which `gnome-session` adds itself).  Xubuntu's own panel (whisker menu), terminal
 * and settings live in those folders: a user whose FIRST start of XFCE was the remote one got
 * XFCE's stock panel, and the first save made it theirs.
 *
 * ⭐ The same rule here, for every desktop, with NO distribution named: the session name is
 * the one the machine's login would use, and a folder is added only IF IT EXISTS.
 *   1. GNOME: the session REMOTIX starts (`gnome_session()->id`, `ubuntu`, `gnome`);
 *   2. the session the display manager declares (`declared_sessions()`: lightdm
 *      `user-session`, sddm `Session`), if it names the chosen desktop;
 *   3. otherwise the session files (`xsessions`, `wayland-sessions`) of the chosen desktop that
 *      have such a folder, the first in alphabetical order.
 * REMOTIX's own folders stay IN FRONT (they hold the remote-only rules); these come right
 * after them, before the system's.  `XDG_CURRENT_DESKTOP` is NOT taken from `DesktopNames`:
 * each desktop's value is fixed for reasons of its own (see the branches).
 */
typedef struct {
	char *name;   /* DESKTOP_SESSION, or NULL: no session known */
	char *config; /* `/etc/xdg/xdg-<name>` if it exists, or NULL */
	char *data;   /* `/usr/share/<name>` if it exists (never for `gnome`), or NULL */
	char *common; /* `/usr/share/gnome` where the profile snippet that adds it is installed, or NULL */
} LocalSession;

static gboolean session_folder_there(const char *name)
{
	g_autofree char *cfg = g_strdup_printf("/etc/xdg/xdg-%s", name);
	g_autofree char *data = g_strdup_printf("/usr/share/%s", name);

	return g_file_test(cfg, G_FILE_TEST_IS_DIR) || g_file_test(data, G_FILE_TEST_IS_DIR);
}

static gint by_name(gconstpointer a, gconstpointer b)
{
	return strcmp(*(char *const *) a, *(char *const *) b);
}

/* The session name as the login would have it: the EXACT name of the session file (`Lubuntu`,
 * not `lubuntu`: it ends up in `/etc/xdg/xdg-Lubuntu`). */
static char *local_session_name_find(DesktopSession d, const char **how)
{
	static const char *const dirs[] = {"/usr/share/xsessions", "/usr/share/wayland-sessions",
	                                   NULL};
	char *found[2];
	g_autoptr(GPtrArray) ids = g_ptr_array_new_with_free_func(g_free);
	char *result = NULL;

	if (d == SESSION_DESKTOP_GNOME) {
		*how = "the GNOME session REMOTIX starts";
		return clean_session_name(gnome_session()->id);
	}
	if (declared_sessions(found)) {
		for (int i = 0; i < 2 && !result; i++)
			if (found[i] && desktop_of_session_name(found[i]) == d)
				result = g_strdup(found[i]);
		g_free(found[0]);
		g_free(found[1]);
		if (result) {
			*how = "declared by the display manager";
			return result;
		}
	}
	for (int k = 0; dirs[k]; k++) {
		g_autoptr(GDir) dir = g_dir_open(dirs[k], 0, NULL);
		const char *f;

		while (dir && (f = g_dir_read_name(dir)))
			if (g_str_has_suffix(f, ".desktop")) {
				char *id = clean_session_name(f);

				if (id && desktop_of_session_name(id) == d && session_folder_there(id))
					g_ptr_array_add(ids, id);
				else
					g_free(id);
			}
	}
	g_ptr_array_sort(ids, by_name);
	*how = "a session file with its own folders";
	return ids->len ? g_strdup(g_ptr_array_index(ids, 0)) : NULL;
}

/* Would the local login of this session put the session's folders in front of the lists?  The
 * system does it in one of two ways, and the rule is: whatever the system itself would apply.
 *   - `Xsession.d/60x11-common_xdg_path`, where the login runs `Xsession.d` at all: an X11
 *     session file (`xsessions/<name>.desktop`, whatever the display manager), or any session
 *     under lightdm (its `session-wrapper` runs `Xsession` for Wayland sessions too).  `[M]`
 *     neither sddm's nor GDM's Wayland launcher runs it (sddm's only reads the profile, GDM's
 *     starts the session directly);
 *   - `/etc/profile.d/xdg_dirs_desktop_session.sh`, the same logic in profile form, which any
 *     login that reads `/etc/profile` runs: sddm's Wayland launcher, and `gnome-session`, which
 *     (Wayland) re-executes itself in a login shell (study 3 §2.1).  REMOTIX sets `SHELL=`
 *     empty, so nothing would run it here: we do.
 * Harmless differences from the real scripts: the config folder is added only if it exists (the
 * script adds it always); «already there» is tested per exact element (the scripts: substring);
 * the default list has no trailing `/`; `GDMSESSION` is not set.
 * ⚠ Known difference from a local login: when neither mechanism applies the name is dropped and
 * `DESKTOP_SESSION` is not set (a local Kubuntu login under sddm gives `plasma`); same as before
 * and nested KDE must not change. */
static gboolean local_login_adds_folders(const char *name)
{
	g_autofree char *x11 = g_strdup_printf("/usr/share/xsessions/%s.desktop", name);
	g_autofree char *dm = NULL;

	if (g_file_test("/etc/profile.d/xdg_dirs_desktop_session.sh", G_FILE_TEST_IS_REGULAR))
		return TRUE;
	if (!g_file_test("/etc/X11/Xsession.d/60x11-common_xdg_path", G_FILE_TEST_IS_REGULAR))
		return FALSE;
	if (g_file_test(x11, G_FILE_TEST_EXISTS))
		return TRUE;
	dm = active_display_manager();
	return dm && strcmp(dm, "lightdm") == 0;
}

static const LocalSession *local_session(void)
{
	static LocalSession s;
	static gsize done;

	if (g_once_init_enter(&done)) {
		DesktopSession d = desktop_session();
		const char *how = "";
		gboolean mechanism = FALSE;

		if (d != SESSION_DESKTOP_NONE && (s.name = local_session_name_find(d, &how))) {
			/* `profile.d/gnome-session_gnomerc.sh` (`gnome-session-common`) puts `/usr/share/gnome` in
			 * front of `XDG_DATA_DIRS`, but a Wayland login to a desktop other than GNOME leaves
			 * the script BEFORE that line (`XDG_SESSION_TYPE=wayland` and no GNOME in
			 * `XDG_CURRENT_DESKTOP`); an X11 login does not.  So: the desktop is GNOME, or the
			 * session's local login is X11 (`xsessions/<name>.desktop`).  The test is on the name
			 * found here, before the branch below may drop it.  It runs before the other snippet
			 * (alphabetical), so the session's folder ends up in front of it.  The script's other
			 * part, sourcing the user's `~/.gnomerc` (GNOME only), is NOT reproduced: not run,
			 * a decision left to the owner, like `~/.profile`. */
			{
				g_autofree char *x11 = g_strdup_printf("/usr/share/xsessions/%s.desktop", s.name);

				if ((d == SESSION_DESKTOP_GNOME || g_file_test(x11, G_FILE_TEST_EXISTS)) &&
				    g_file_test("/etc/profile.d/gnome-session_gnomerc.sh",
				                G_FILE_TEST_IS_REGULAR) &&
				    g_file_test("/usr/share/gnome", G_FILE_TEST_IS_DIR))
					s.common = g_strdup("/usr/share/gnome");
			}
			mechanism = local_login_adds_folders(s.name);
			if (mechanism) {
				g_autofree char *cfg = g_strdup_printf("/etc/xdg/xdg-%s", s.name);
				g_autofree char *data = g_strdup_printf("/usr/share/%s", s.name);

				if (g_file_test(cfg, G_FILE_TEST_IS_DIR))
					s.config = g_steal_pointer(&cfg);
				if (strcmp(s.name, "gnome") != 0 &&
				    g_file_test(data, G_FILE_TEST_IS_DIR))
					s.data = g_steal_pointer(&data);
			} else
				g_clear_pointer(&s.name, g_free);
		}
		registro_dice(LOG_SESSION,
		              "⭐ D-153: the session as a local login gives it — session «%s» (%s): "
		              "config folder %s, data folder %s, common folder %s",
		              s.name ? s.name : "(none)",
		              s.name ? how : (d != SESSION_DESKTOP_NONE && !mechanism
		                                      ? "its local login adds no session folders, "
		                                        "or no session is known"
		                                      : "no session known"),
		              s.config ? s.config : "none", s.data ? s.data : "none",
		              s.common ? s.common : "none");
		g_once_init_leave(&done, 1);
	}
	return &s;
}

/* What `XDG_SESSION_DESKTOP` is at the login screen of the active display manager: sddm gives
 * the session file's `DesktopNames` (`LXQt` for the session `Lubuntu`), every other one (lightdm,
 * gdm) the session name.  The names of the session file `name`, joined with `:`, when the active
 * manager is sddm and the file has them; NULL otherwise (to free). */
static char *login_session_desktop(const char *name)
{
	static const char *const dirs[] = {"/usr/share/xsessions", "/usr/share/wayland-sessions",
	                                   NULL};
	g_autofree char *dm = active_display_manager();

	if (!dm || strcmp(dm, "sddm") != 0)
		return NULL;
	for (int k = 0; dirs[k]; k++) {
		g_autofree char *file = g_strdup_printf("%s/%s.desktop", dirs[k], name);
		g_autoptr(GKeyFile) kf = g_key_file_new();
		g_auto(GStrv) names = NULL;

		if (g_key_file_load_from_file(kf, file, G_KEY_FILE_NONE, NULL) &&
		    (names = g_key_file_get_string_list(kf, G_KEY_FILE_DESKTOP_GROUP, "DesktopNames",
		                                       NULL, NULL)) &&
		    names[0])
			return g_strjoinv(":", names);
	}
	return NULL;
}

static GHashTable *handler_environment(GDBusConnection *bus);

/* A variable as the USER MANAGER has it (what a local login's generators and `environment.d`
 * made: snapd's and flatpak's data folders…), without the elements that are ours
 * (`/remotix/`: a leftover of an earlier birth).  NULL if the manager does not answer, or
 * has nothing. */
static GHashTable *manager_cache; /* the manager's environment, as asked once per birth */
static gboolean manager_cache_asked;
static GHashTable *dropped_said; /* the elements already reported this birth */

static void manager_cache_reset(void)
{
	g_clear_pointer(&manager_cache, g_hash_table_unref);
	g_clear_pointer(&dropped_said, g_hash_table_unref);
	manager_cache_asked = FALSE;
}

static char *manager_value(const char *name)
{
	const char *v;

	if (!manager_cache_asked) {
		g_autoptr(GDBusConnection) bus = sess_bus(NULL);

		manager_cache = bus ? handler_environment(bus) : NULL;
		manager_cache_asked = TRUE;
	}
	v = manager_cache ? g_hash_table_lookup(manager_cache, name) : NULL;
	g_auto(GStrv) parts = NULL;
	g_autoptr(GPtrArray) kept = g_ptr_array_new();

	if (!v || !*v)
		return NULL;
	parts = g_strsplit(v, ":", -1);
	for (int i = 0; parts[i]; i++) {
		const char *e = parts[i];
		gboolean safe = e[0] == '/';

		/* ⛔ the value ends up unquoted in a systemd drop-in (`Environment=`): a space would
		 *    start a second assignment, `%` is a specifier, quotes and `\` are escapes;
		 *    the manager's environment is the user's to change, so it is not trusted */
		for (const char *p = e; safe && *p; p++)
			if (g_ascii_isspace(*p) || g_ascii_iscntrl(*p) || strchr("\"'\\%", *p))
				safe = FALSE;
		if (!*e || strstr(e, "/remotix/"))
			continue;
		if (safe)
			g_ptr_array_add(kept, parts[i]);
		else if (!dropped_said)
			dropped_said = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, NULL);
		if (!safe && g_hash_table_add(dropped_said, g_strdup(e)))
			registro_dice(LOG_SESSION,
			              "⚠ D-153: «%s» of the user manager's %s dropped: not an absolute "
			              "path, or it holds a space, a quote, a backslash, a `%%` or a "
			              "control character",
			              e, name);
	}
	if (!kept->len)
		return NULL;
	g_ptr_array_add(kept, NULL);
	return g_strjoinv(":", (char **) kept->pdata);
}

/* `dir` in front of the `:`-list `current` (or of `fallback` if empty), unless it is already one
 * of its elements — the test `60x11-common_xdg_path` makes. */
static char *dir_in_front(const char *dir, const char *current, const char *fallback)
{
	const char *base = current && *current ? current : fallback;
	g_auto(GStrv) parts = g_strsplit(base, ":", -1);

	if (!dir || g_strv_contains((const char *const *) parts, dir))
		return g_strdup(base);
	return g_strdup_printf("%s:%s", dir, base);
}

/* The base of a list: the user manager's, else this process's, else NULL. */
static char *list_base(const char *name)
{
	char *v = manager_value(name);

	if (!v && g_getenv(name) && *g_getenv(name))
		v = g_strdup(g_getenv(name));
	return v;
}

/* the `XDG_CONFIG_DIRS` a local login would have: the manager's, the session's folder in front */
static char *session_config_dirs(void)
{
	g_autofree char *base = list_base("XDG_CONFIG_DIRS");

	return dir_in_front(local_session()->config, base, "/etc/xdg");
}

/* Is there anything to say about the config dirs (the manager has them, or a session folder)? */
static gboolean session_config_given(void)
{
	g_autofree char *base = list_base("XDG_CONFIG_DIRS");

	return base || local_session()->config;
}

/* the `XDG_DATA_DIRS`, same; the default is the one of the same script.  `*given` says if
 * there is anything beyond the default (the manager has it, or a session folder). */
static char *session_data_dirs(gboolean *given)
{
	g_autofree char *base = list_base("XDG_DATA_DIRS");
	g_autofree char *with_common = dir_in_front(local_session()->common, base,
	                                            "/usr/local/share:/usr/share");

	if (given)
		*given = base || local_session()->data || local_session()->common;
	return dir_in_front(local_session()->data, with_common, "/usr/local/share:/usr/share");
}

/* the system configuration folders as the session sees them (to free with g_strfreev) */
static char **session_config_dirs_strv(void)
{
	g_autofree char *list = session_config_dirs();

	return g_strsplit(list, ":", -1);
}

/* (shared by LXQt and XFCE) a system autostart entry of that file name exists in the config
 * folders the session will have (`session_config_dirs()`: the manager's and the session's own, e.g. `/etc/xdg/xdg-Lubuntu`) */
static gboolean system_autostart_exists(const char *file)
{
	g_auto(GStrv) dirs = session_config_dirs_strv();

	for (int i = 0; dirs && dirs[i]; i++) {
		g_autofree char *path = g_build_filename(dirs[i], "autostart", file, NULL);

		if (g_file_test(path, G_FILE_TEST_EXISTS))
			return TRUE;
	}
	return FALSE;
}

/* ⭐ 19 Nov 2026 — XFCE and LXQt: the programs of the SYSTEM's autostart that a remote session
 *   must not start.  `blueman-applet` (`blueman.desktop`, Xubuntu and Lubuntu): Bluetooth is a
 *   device of the machine, not of the remote user, and the applet crashes now and then (a race
 *   with `obexd`, 5 sessions in 90) and covers the screen with apport's «internal error»
 *   window.  An entry of the same file name with `Hidden=true` in the session's autostart
 *   folder, which is first in `XDG_CONFIG_DIRS`.
 * ⭐ NOT the recipe of LXQt's `LXQT_SHARED_SERVER_PROGRAMS` (a script that checks where it
 *   runs): `Hidden=true` WITHOUT a check is fine here — there is no program to replace, the
 *   folder is under `/run/user` and only the remote session reads it; in the worst case
 *   the Bluetooth icon is missing.
 * ⚠ DECLARED: the code does not remove the file at the end of the session: it goes when logind
 *   removes `/run/user/<uid>`; with another session of the same user alive (ssh, linger) it
 *   stays (harmless: no non-remote session reads that folder).
 * ⚠ [M] XFCE (`xfce4-session`, Xubuntu 26.04): a `Hidden=true` entry hides the file name
 *   whichever folder it is in, so the user's own VISIBLE `~/.config/autostart/<same name>`
 *   is not started either (a differently named user entry is).  LXQt: not measured; the
 *   user's folder comes first, so the user's own entry should win. */
static const char *const SESSION_NOT_IN_REMOTE_AUTOSTART[] = { "blueman.desktop", NULL };

/* `dir` is the `autostart` folder of the session folder that is first in `XDG_CONFIG_DIRS`
 * (XFCE: `labwc-xfce`, LXQt: `xdg-lxqt`); `desktop` is only for the log.  Returns FALSE if a
 * cover could not be written. */
static gboolean session_autostart_cover(const char *dir, const char *desktop)
{
	g_autoptr(GString) done = g_string_new(NULL);
	g_autoptr(GError) mistake = NULL;
	int covered = 0;
	gboolean ok = TRUE;

	for (int i = 0; SESSION_NOT_IN_REMOTE_AUTOSTART[i]; i++) {
		const char *file = SESSION_NOT_IN_REMOTE_AUTOSTART[i];
		g_autofree char *entry = g_build_filename(dir, file, NULL);
		g_autofree char *old = NULL;

		if (!system_autostart_exists(file)) {
			/* not (or no longer) installed: only OURS of an earlier birth goes */
			if (g_file_get_contents(entry, &old, NULL, NULL) && strstr(old, "X-REMOTIX"))
				g_unlink(entry);
			continue;
		}
		g_clear_error(&mistake);
		if (g_mkdir_with_parents(dir, 0700) == 0 &&
		    g_file_set_contents(entry,
		                        "[Desktop Entry]\nType=Application\nName=REMOTIX cover\n"
		                        "Hidden=true\n"
		                        "# X-REMOTIX: covers the system's entry of the same name\n",
		                        -1, &mistake)) {
			covered++;
			g_string_append_printf(done, "%s%s", done->len ? " " : "", file);
		} else {
			ok = FALSE;
			registro_dice(LOG_SESSION, "⛔ %s: the cover for %s is NOT in place (%s)", desktop, file,
			              mistake ? mistake->message : g_strerror(errno));
		}
	}
	if (covered && ok)
		registro_dice(LOG_SESSION,
		              "⭐ %s: %d system autostart entr%s not started in the remote session "
		              "(%s: Hidden=true in %s, first in XDG_CONFIG_DIRS) — shared server, the "
		              "machine's Bluetooth is not the remote user's; %s; "
		              "the user's files are not touched",
		              desktop, covered, covered == 1 ? "y is" : "ies are", done->str, dir,
		              strcmp(desktop, "XFCE") == 0
		                      ? "a user's own ~/.config/autostart entry of the same name "
		                        "is hidden too (measured)"
		                      : "the user's own entry of the same name wins (not measured)");
	return ok;
}

/* The session names and the data folder, for the desktops that do not compose them in their
 * own way: `DESKTOP_SESSION` (what `60x11-common_xdg_path` keys on, and what the session's
 * programs read), `XDG_SESSION_DESKTOP` (as the active display manager sets it: the session name, or sddm's `DesktopNames`;
 * `fallback` when none is known, NULL = not set here: KDE leaves it to `startplasma`) and, with `with_data`, `XDG_DATA_DIRS`
 * when the manager has one or the session has a data folder. */
static void add_session_names(GPtrArray *environment, const char *fallback, gboolean with_data)
{
	const LocalSession *s = local_session();

	if (s->name)
		g_ptr_array_add(environment, g_strdup_printf("DESKTOP_SESSION=%s", s->name));
	if (fallback) {
		g_autofree char *login = s->name ? login_session_desktop(s->name) : NULL;

		g_ptr_array_add(environment, g_strdup_printf("XDG_SESSION_DESKTOP=%s",
		                                             login ? login
		                                                   : s->name ? s->name : fallback));
	}
	if (with_data) {
		gboolean given;
		g_autofree char *dirs = session_data_dirs(&given);

		if (given)
			g_ptr_array_add(environment, g_strdup_printf("XDG_DATA_DIRS=%s", dirs));
	}
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
		if (rules) {
			g_autofree char *system_dirs = session_config_dirs();

			g_ptr_array_add(environment,
			                g_strdup_printf("XDG_CONFIG_DIRS=%s:%s", rules, system_dirs));
		}
		add_session_names(environment, NULL, TRUE);
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
			add_session_names(environment, "xfce", TRUE);
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
				g_autofree char *system_dirs = session_config_dirs();

				if (labwc_cfg) {
					g_autofree char *dir = g_build_filename(labwc_cfg, "autostart", NULL);

					session_autostart_cover(dir, "XFCE");
				}
				if (labwc_cfg || session_config_given())
					g_ptr_array_add(environment,
					                g_strdup_printf("XDG_CONFIG_DIRS=%s%s%s",
					                                labwc_cfg ? labwc_cfg : "",
					                                labwc_cfg ? ":" : "", system_dirs));
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
			add_session_names(environment, "lxqt", FALSE);
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
			 *    folder (`lxqt_session_commands()`): what the session must have
			 *    lives there, not in the user's files.  ⚠ Only `~/.config` stays before it,
			 *    that is the user — who wins, and that is fine. */
			{
				g_autofree char *cfg = lxqt_session_config_folder();
				g_autofree char *data = lxqt_session_data_folder();
				g_autofree char *data_before = session_data_dirs(NULL);

				g_ptr_array_add(environment,
				                g_strdup_printf("XDG_CONFIG_DIRS=%s%s%s%s/etc:/etc/xdg:/usr/share",
				                                cfg ? cfg : "", cfg ? ":" : "",
				                                local_session()->config
				                                        ? local_session()->config : "",
				                                local_session()->config ? ":" : ""));
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
	/* ⭐ D-153: and the rest of what a local login adds for this session (`ubuntu`: its data
	 *    folder, which hides entries such as the first-run assistant) */
	add_session_names(environment, NULL, TRUE);
	if (session_config_given()) {
		g_autofree char *dirs = session_config_dirs();

		g_ptr_array_add(environment, g_strdup_printf("XDG_CONFIG_DIRS=%s", dirs));
	}
	/*
	 * ⛔ `XDG_SESSION_TYPE=wayland` IS NEEDED, and it is not a lie: the Shell's
	 *    unit carries `AssertEnvironment=XDG_SESSION_TYPE=wayland` (GNOME 50), and without it the
	 *    job FAILS: `OnFailure=gnome-session-shutdown.target` tears the session down at once.
	 */
	g_ptr_array_add(environment, g_strdup("XDG_SESSION_TYPE=wayland"));
	/*
	 * ⛔ `SHELL` EMPTY, and it is the trap of `STUDIES.md` §gnome §3.1: gnome-session 50 (`leader-main.c`)
	 *    re-executes itself inside a LOGIN shell if `$SHELL` is not empty and is in
	 *    `/etc/shells` — that is it drags `~/.profile` back in, which is `CODER.md`
	 *    §4.5 lying in wait after the environment has been carefully composed.
	 *
	 * ⚠ The real check is `[ -n "$SHELL" ]`, so ABSENT and EMPTY are
	 *   both fine — and v1 left it absent, by construction, without
	 *   knowing it.  Here it is set EMPTY on purpose: absent and empty are the
	 *   same thing for `gnome-session` and **two different things for whoever measures**,
	 *   because empty shows in `/proc/<gnome-session-init-worker>/environ` while absent
	 *   is confused with «I did not read the environment».
	 */
	g_ptr_array_add(environment, g_strdup("SHELL="));
	/* ⭐ PHASE 15, D-015 — the session dconf.  ⚠ Since 19 Nov 2026 this holds ONLY in the fallback and with an administrator's own
	 *    DCONF_PROFILE: `gnome-session` exports the variable to the user manager, and the Shell and the `gsd-*` inherit it.  In the
	 *    runtime model there is no variable: they read `$XDG_RUNTIME_DIR/dconf/profile` (the box above `session_dconf_prepare()`). */
	if (session_dconf_of_session()) {
		/* ⭐ 19 Nov 2026: NO `DCONF_PROFILE` in the runtime model (dconf reads `$XDG_RUNTIME_DIR/dconf/profile` by itself, and
		 *    snap/Flutter programs digest it); only the fallback's, or the case of an administrator's own variable that
		 *    would shadow our file, tells the session where the profile is. */
		const char *env = dconf_runtime_mode ? (dconf_admin_profile ? dconf_profile_file : NULL) : g_getenv("DCONF_PROFILE");

		if (env && *env)
			g_ptr_array_add(environment, g_strdup_printf("DCONF_PROFILE=%s", env));
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
	{
		/* ⭐ LXQt: the session's commands in FRONT (`lxqt_session_commands()`) */
		g_autofree char *bin = e_lxqt() ? lxqt_session_bin_folder() : NULL;

		g_ptr_array_add(environment,
		                g_strdup_printf("PATH=%s%s%s", bin ? bin : "", bin ? ":" : "",
		                                g_getenv("PATH") ?: "/usr/bin:/bin"));
	}
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
		registro_dice(LOG_SESSION, "⚠ «%s …» did not succeed: %s", argv[0],
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
 *    (`session.h`, `SESSION_UNIT_SHELL_MODEL`; `phases/17-the-installer.md` §5.1).
 *
 * GNOME 50: the Shell is the template `org.gnome.Shell@.service` and the instance is asked for by
 * the SESSION (`gnome` ⇒ `@user`, `ubuntu` ⇒ `@ubuntu`): it is read from the `Requires` of
 * `gnome-session@<session>.target`, drop-ins included.  The caller frees the string.
 *
 * ⚠ The manager and not a list of folders written here: the user unit
 *   folders are many (also from `XDG_DATA_DIRS`) and it knows them.
 * ⛔ NULL if I recognise nothing: «I don't know» does not become a bet on
 *   a name, and the caller stops saying so.
 */
static char *unit_shell(void)
{
	g_autofree char *target = g_strdup_printf("gnome-session@%s.target", gnome_session()->name);
	char *argv[] = { "systemctl", "--user", "show", "-p", "Requires", "--value", target, NULL };
	g_autofree char *requests = ask(argv);
	g_auto(GStrv) entries = NULL;

	if (!requests) {
		registro_dice(LOG_SESSION, "⛔ I could not ask the user manager "
		                            "which Shell unit there is");
		return NULL;
	}
	entries = g_strsplit_set(g_strstrip(requests), " \t\n", -1);
	for (int i = 0; entries[i]; i++)
		if (g_str_has_prefix(entries[i], "org.gnome.Shell@") &&
		    g_str_has_suffix(entries[i], ".service") &&
		    strcmp(entries[i], SESSION_UNIT_SHELL_MODEL) != 0)
			return g_strdup(entries[i]);
	registro_dice(LOG_SESSION,
	              "⛔ I do not recognise the Shell unit: %s does not ask for any instance of "
	              SESSION_UNIT_SHELL_MODEL " (Requires: «%s»): I do not know which Shell the "
	              "session will start, and I do not bet",
	              target, requests);
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
	content = g_strdup_printf("[Service]\n"
	                            "ExecStart=\n"
	                            "ExecStart=%s --headless --no-x11 --mode=%%i\n",
	                            shell);
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
	 *     `/etc/systemd/user/org.gnome.Shell@<instance>.service.d/remotix-headless.conf`,
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

/* `*busy`, if not NULL, says what answered «not stopped» (unit name or description) */
static gboolean inactive_unit(const char **busy)
{
	const char *dummy;

	if (!busy)
		busy = &dummy;
	*busy = NULL;
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
	if (e_kde()) {
		if (!unit_stopped(SESSION_UNIT_KWIN)) {
			*busy = SESSION_UNIT_KWIN;
			return FALSE;
		}
		if (!unit_stopped(SESSION_UNIT_PLASMA)) {
			*busy = SESSION_UNIT_PLASMA;
			return FALSE;
		}
		return TRUE;
	}

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
			*busy = "the process " SESSION_PROCESS_XFCE;
			return FALSE;
		}
		if (amount > 0) {
			registro_dice(LOG_SESSION,
			              "%s: there are still %d " SESSION_PROCESS_XFCE
			              " of mine: the previous session has not ended",
			              desktop_name(), amount);
			*busy = "the process " SESSION_PROCESS_XFCE;
			return FALSE;
		}
		return TRUE;
	}

	/* ⭐ PHASE 17 — on GNOME 50 these units have these names
	 *    (`[V]` gnome-session 50.1: `gnome-session-manager@.service`,
	 *    `gnome-session-restart-dbus.service`).
	 * ⛔ AND A THIRD one, new in GNOME 50: `graphical-session.target`.  `gnome-session-init-worker`
	 *    (`leader-systemd.c`) ABORTS with «A graphical session is already running!» if it is still
	 *    active, and `start()` would answer TRUE all the same: a birth too close to the end of the
	 *    previous session would be a session that dies at once.  Here it means «wait» (or, for
	 *    the caller, «refuse»), cleanly.
	 * ⚠ If one day these names changed, `is-active` would answer «inactive» for a
	 *   name that does not exist, and the guard would vanish as on XFCE: to be
	 *   re-checked at every new GNOME (`phases/17-the-installer.md` §5.1). */
	if (!unit_stopped(gnome_session()->handler))
		*busy = gnome_session()->handler;
	else if (!unit_stopped(SESSION_UNIT_DBUS))
		*busy = SESSION_UNIT_DBUS;
	else if (!unit_stopped(SESSION_UNIT_GRAPHICAL))
		*busy = SESSION_UNIT_GRAPHICAL;
	return !*busy;
}

static gboolean wait_until_done(void)
{
	gint64 expiry = g_get_monotonic_time() + (gint64) WAIT_EXIT_MS * 1000;

	while (g_get_monotonic_time() < expiry) {
		g_usleep(CHECK_INTERVAL_MS * 1000);
		if (!session_alive() && inactive_unit(NULL)) {
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
 *
 * ⭐ 14 Nov 2026 — THE CLEAR-OUT IS RETRIED.  `[M]` Arch: the child saw the session over
 *   while `session_alive()` still answered yes (the desktop's name lingers on the bus a
 *   little longer than the compositor), the clear-out gave up, and nobody tried again:
 *   PATH/XDG_* (LXQt) stayed in the manager, `DCONF_PROFILE` (GNOME) for 126 s.  ⇒ At
 *   «session over» the request is REMEMBERED (`session_clear_out_handler_due()`), retried
 *   at every round of the child's loop but at most once every `CLEAR_OUT_RETRY_MS`
 *   (`session_clear_out_retry()`), and once more, for at most `CLEAR_OUT_EXIT_WAIT_MS`,
 *   when the child exits (`session_clear_out_handler_exit()`).  One log line the first
 *   time and one when it succeeds.  A birth cancels the request: that session's own end
 *   will ask again.
 */
#define CLEAR_OUT_RETRY_MS 3000
#define CLEAR_OUT_EXIT_WAIT_MS 2000
static gboolean clear_out_due;    /* asked at «session over», the session still answered */
static gint64 clear_out_due_since; /* monotonic µs */
static gint64 clear_out_last_try;
static gboolean clear_out_refused; /* the last run: the manager did not restore the variables */
static const char *const OUR_VARIABLES[] = {
	"DCONF_PROFILE", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS", "XDG_MENU_PREFIX", "DESKTOP_SESSION",
	"XCURSOR_THEME", "XCURSOR_SIZE", "XCURSOR_PATH", "XDG_CURRENT_DESKTOP",
	"XDG_SESSION_DESKTOP", "XDG_SESSION_TYPE", "SHELL", "LANG", "PATH",
	"QT_QPA_PLATFORM", "QT_QPA_PLATFORMTHEME", "GDK_BACKEND", "XFCE4_SESSION_COMPOSITOR",
	"WLR_BACKENDS", "WLR_LIBINPUT_NO_DEVICES", "WLR_RENDER_DRM_DEVICE",
	"LABWC_UPDATE_ACTIVATION_ENV", "WAYLAND_DISPLAY", "DISPLAY",
	/* ⭐ D8: it is set by a session's `Exec` (`env GNOME_SHELL_SESSION_MODE=…`),
	 *    and gnome-session exports it to the manager like its whole environment. */
	"GNOME_SHELL_SESSION_MODE",
	/* ⭐ 18 Nov 2026 (Ubuntu 26.04, GNOME 50): the four that appear in the environment of `gnome-session`
	 *    and of everything it starts, and that it then exports to the manager like the rest.  `[M]` from
	 *    `/proc/<pid>/environ` of a live session: our child has none of them, the first process that
	 *    has them is `gnome-session-init-worker` (`GNOME_DESKTOP_SESSION_ID` is also a literal of
	 *    `/usr/bin/gnome-session`).  With linger on they stayed in the manager after the Log Out.  Like
	 *    the others, they are put back as they were (or removed if they were not there): a local
	 *    login that already has them is not touched. */
	"GNOME_DESKTOP_SESSION_ID", "QT_IM_MODULE", "QT_IM_MODULES", "XMODIFIERS", NULL
};

/* { drop-in folder, name } — all of ours and only ours */
static const char *const OUR_DROPINS[][2] = {
	/* ⭐ PHASE 17: the Shell instances (`@user`, `@ubuntu`…)
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

	manager_cache_reset(); /* a birth: the next question about the manager is asked afresh */
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

static gboolean xfce_restore_keys(void);

/* ⭐ 1.5.4: set only by `session_clear_out_light()` — the session that answers is the user's LOCAL one */
static gboolean clear_out_local = FALSE;

/* FALSE = not done, the session still answers (`quiet`: without the detail line). */
static gboolean clear_out_handler_run(const char *why, gboolean quiet)
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

	clear_out_refused = FALSE;
	if (!runtime || !*runtime)
		return TRUE;
	if (session_alive() && !clear_out_local) {
		if (!quiet)
			log_detail(LOG_SESSION,
			                   "R1/R2 (%s): the session is ALIVE — I do not clear out the "
			                   "user manager under a working desktop",
			                   why);
		return FALSE;
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
	/* ⭐ D8: the Shell instances, whatever their name (`@user`,
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
	if (xfconfd && clear_out_local)
		registro_dice(LOG_SESSION,
		              "⭐ R1/R2 (%s): light mode — drop-in removed and daemon-reload done, but "
		              "NO try-restart of xfconfd: it is the one of the user's LOCAL desktop",
		              why);
	else if (xfconfd)
		run(restart);
	/* ⭐ 13 Nov 2026: with the lock gone, the user's values of the keys we had
	 *    locked go back (the copy made at birth; also the one of a session that died
	 *    badly).  No copy ⇒ nothing happens.
	 * ⛔ 1.5.4 light mode: NOT written — it would go into the xfconfd of the LOCAL desktop. */
	if (clear_out_local)
		registro_dice(LOG_SESSION,
		              "⭐ R1/R2 (%s): light mode — the XFCE keys are NOT restored (they "
		              "would be written into the local desktop's xfconfd)",
		              why);
	else
		xfce_restore_keys();

	/* 2. the variables: as they were, or only those with our mark without a snapshot */
	bus = sess_bus(NULL);
	env = bus ? handler_environment(bus) : NULL;
	/* ⛔ 1.5.4 light mode: NO photo (the manager's variables now are the LOCAL desktop's)
	 *    and only the variables whose CURRENT value carries our mark. */
	with_photo = !clear_out_local && fpath &&
	             g_key_file_load_from_file(photo, fpath, G_KEY_FILE_NONE, NULL);
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
		} else if (now && (strstr(now, "remotix") ||
		                   (strcmp(name, "DCONF_PROFILE") == 0 && dconf_env_is_ours(now)) ||
		                   (!clear_out_local && strcmp(name, "DESKTOP_SESSION") == 0))) {
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
			clear_out_refused = TRUE;
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
		              why, said->str, (xfconfd && !clear_out_local) ? " · xfconfd restarted" : "",
		              clear_out_local ? " (light mode: only variables bearing our mark)"
		              : with_photo ? "" : " (⚠ without a snapshot: removed only the variables bearing "
		                              "our mark)");
	else
		log_detail(LOG_SESSION,
		                   "R1/R2 (%s): there was nothing of ours in the user manager",
		                   why);
	return TRUE;
}

/* the remembered request is settled: said once */
static void clear_out_settled(const char *why)
{
	if (!clear_out_due)
		return;
	clear_out_due = FALSE;
	registro_dice(LOG_SESSION,
	              "⭐ R1/R2 (%s): the clear-out of the user manager that was still TO DO is "
	              "DONE, %lld ms after the session was seen over",
	              why, (long long) ((g_get_monotonic_time() - clear_out_due_since) / 1000));
}

/*
 * ⭐ 1.5.4, the LIGHT close (the user has a LOCAL session): the same clear-out as above, but
 * WITHOUT the «the session is alive» refusal — what answers is the user's local desktop, not
 * ours, and what we put in the user manager (drop-ins, variables with our mark) must go away
 * all the same.  ⛔ It touches only what is ours: no Logout, no unit stopped.  0 = done,
 * 2 = done but the manager refused something; never 1 (there is nothing to retry later).
 */
int session_clear_out_light(const char *why)
{
	int rc;

	clear_out_local = TRUE;
	if (clear_out_handler_run(why, FALSE))
		rc = clear_out_refused ? 2 : 0;
	else
		rc = 2;
	clear_out_local = FALSE;
	clear_out_due = FALSE;
	return rc;
}

void session_clear_out_handler(const char *why)
{
	if (clear_out_handler_run(why, FALSE))
		clear_out_settled(why);
}

/* ⭐ At «session over»: if the session still answers, the clear-out stays TO DO. */
int session_clear_out_handler_due(const char *why)
{
	if (clear_out_handler_run(why, FALSE)) {
		clear_out_settled(why);
		return clear_out_refused ? 2 : 0;
	}
	clear_out_last_try = g_get_monotonic_time();
	if (clear_out_due)
		return 1;
	clear_out_due = TRUE;
	clear_out_due_since = clear_out_last_try;
	registro_dice(LOG_SESSION,
	              "⚠ R1/R2 (%s): the session is over for the child but something of it still "
	              "ANSWERS — the clear-out of the user manager stays TO DO: I retry every "
	              "%d ms until it is done",
	              why, CLEAR_OUT_RETRY_MS);
	return 1;
}

/* ⭐ At every round of the child's loop: costs a comparison when nothing is due. */
void session_clear_out_retry(void)
{
	gint64 now;

	if (!clear_out_due)
		return;
	now = g_get_monotonic_time();
	if (now - clear_out_last_try < (gint64) CLEAR_OUT_RETRY_MS * 1000)
		return;
	clear_out_last_try = now;
	if (clear_out_handler_run("the session is over: retried", TRUE))
		clear_out_settled("the session is over: retried");
}

/*
 * ⭐⭐ 17 Nov 2026 — PLASMA'S LOGOUT THAT STOPS HALFWAY (KDE only; `[M]` rx-kde, lifecycle check).
 *
 * `plasma-shutdown` (what «Log Out» calls: `org.kde.Shutdown`) stops `plasma-workspace.target` and then
 * asks the user manager to stop `graphical-session.target`, which is what really stops kwin, plasmashell,
 * ksmserver and the rest (they are all `PartOf` it).  ⛔ If ANY unit has a start job queued at that
 * moment (`xdg-desktop-portal` in its first seconds, a slow or failing unit) systemd refuses the stop
 * («Transaction ... is destructive»), plasma-shutdown ignores it and exits: the desktop stays up, KWin
 * keeps its name, and the user who confirmed «Log Out» sees nothing happen.
 *
 * ⭐ THE SIGNAL: `plasma-workspace.target` seen ACTIVE in this child's life and then not active, while
 *    `org.kde.KWin` is still on the bus.  It is the most direct fact of the logout: only `plasma-shutdown`
 *    (or an administrator) stops that target; a detach, a resize, a reattach, a service restart (the child
 *    dies with it) or a crash of plasmashell alone never touch it.  ⚠ «Seen active first» keeps it silent
 *    at birth, before the target is reached.
 * ⭐⭐ 18 Nov 2026 — THE SAME SIGNAL IS NOT THERE ON PLASMA 6.6 (`[M]` rx-kde, Log Out asked in the first
 *    seconds of the desktop): `plasma-shutdown` calls `ksmserver.closeSession`, `KWin.closeWaylandWindows`,
 *    asks the stop of `graphical-session.target` (`StopUnit ... "fail"`, the answer is not looked at) and
 *    exits — and `plasma-workspace.target` is NEVER stopped by it (`startplasma` does that only after the
 *    target stop is accepted), so the signal above never fires and the logout is lost.
 * ⭐ What exists in the lost case AND in the good one: `plasma-shutdown` owns the bus name `org.kde.Shutdown`
 *    for the whole of its run and RELEASES it when it exits (`NameOwnerChanged`, subscribed on a private
 *    main context turned at each round of this watch; a poll would miss a short run).  ⛔ But the name
 *    alone is not a logout: `plasma-shutdown` is also started by `saveSession`, it holds the name for as
 *    long as an application asks «save changes?» (KWin waits, then «Cancel Logout / Log Out Anyway»), and if
 *    the user cancels it calls `resetLogout` and exits without stopping anything.  ⇒ The trigger is the
 *    RELEASE of the name and, right after, the answer of `ksmserver.isShuttingDown()`: `true` = the logout
 *    was done by plasma-shutdown and not undone (measured: `true` in the lost case, it stays so until
 *    `resetLogout`) ⇒ same grace and same retry as below; `false` = cancelled or never a logout ⇒ nothing
 *    is forced, one line.  ⚠ ksmserver not answering (seen once: `NoReply`) ⇒ CHOICE: nothing is forced,
 *    one line — a logout that cannot be confirmed is not worth the user's unsaved work.
 *    The older fact (the target seen active and then not) stays as a second road and is not asked.
 * ⚠ KNOWN LIMITS, accepted: (1) `logoutAndShutdown` / `logoutAndReboot`: in 6.6.7 `plasma-shutdown` does not exit after asking
 *    the power-off, so the name is not released and, if the stop is refused in the first seconds, that exit stays lost; it
 *    is reachable only without the menu entries (which REMOTIX removes).  (2) A restart of KWin by its wrapper during the
 *    wait resets the request (KWin leaves the bus): rare.
 * ⭐ After a grace (`KDE_LOGOUT_GRACE_MS`) in which the normal road wins when it works (KWin leaves, §7.6),
 *    the stop of `graphical-session.target` is asked again — mode `fail`, as plasma-shutdown does, so a
 *    refusal is just retried every `KDE_LOGOUT_RETRY_MS`; after `KDE_LOGOUT_TRIES` refusals the mode is
 *    `replace`, and after as many more the watch returns TRUE: the child closes the session by the product's own
 *    road (`session_terminate()`), which forces and, KWin gone, §7.6 warns the client.  One line each.
 *    The normal §7.6 road follows (KWin leaves the bus).
 * Called at every round of the child's loop; it limits its own frequency (one comparison when idle).
 */
#define KDE_LOGOUT_GRACE_MS 4000
#define KDE_LOGOUT_RETRY_MS 3000
/* `KDE_LOGOUT_TRIES` attempts in mode `fail`, then as many in mode `replace` (about a minute with the retry above);
 * if the stop is still refused the watch gives up and says «to be closed» (see the return value). */
#define KDE_LOGOUT_TRIES 10

static const char *unit_active_state(GDBusConnection *bus, const char *unit, char *out, size_t size)
{
	g_autoptr(GVariant) path = NULL, prop = NULL, inner = NULL;
	const char *object = NULL;

	g_strlcpy(out, "unknown", size);
	path = g_dbus_connection_call_sync(
		bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
		"org.freedesktop.systemd1.Manager", "GetUnit", g_variant_new("(s)", unit),
		G_VARIANT_TYPE("(o)"), G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_NAME_MS, NULL, NULL);
	if (!path)
		return out; /* not loaded = not active */
	g_variant_get(path, "(&o)", &object);
	prop = g_dbus_connection_call_sync(
		bus, "org.freedesktop.systemd1", object, "org.freedesktop.DBus.Properties", "Get",
		g_variant_new("(ss)", "org.freedesktop.systemd1.Unit", "ActiveState"), G_VARIANT_TYPE("(v)"),
		G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_NAME_MS, NULL, NULL);
	if (!prop)
		return out;
	g_variant_get(prop, "(v)", &inner);
	if (g_variant_is_of_type(inner, G_VARIANT_TYPE_STRING))
		g_strlcpy(out, g_variant_get_string(inner, NULL), size);
	return out;
}

/* `plasma-shutdown` released the name `org.kde.Shutdown`: to be asked of ksmserver at the next round */
static gboolean shutdown_released;
/* ksmserver confirmed that a logout is under way (`isShuttingDown`): the watch is armed */
static gboolean logout_asked;

static void on_shutdown_name(GDBusConnection *bus, const char *sender, const char *path,
                             const char *interface, const char *signal, GVariant *parameters,
                             gpointer data)
{
	const char *name = NULL, *before = NULL, *after = NULL;

	(void)bus; (void)sender; (void)path; (void)interface; (void)signal; (void)data;
	g_variant_get(parameters, "(&s&s&s)", &name, &before, &after);
	(void)name;
	if (*before && !*after)
		shutdown_released = TRUE;
}

/* The subscription follows the connection: a new bus (the old one closed) is subscribed again. */
static void shutdown_name_listen(GDBusConnection *bus)
{
	static GMainContext *context;
	static GDBusConnection *listening;
	static guint subscription;

	if (!context)
		context = g_main_context_new();
	if (listening != bus) {
		if (listening) {
			g_dbus_connection_signal_unsubscribe(listening, subscription);
			g_clear_object(&listening);
		}
		g_main_context_push_thread_default(context);
		subscription = g_dbus_connection_signal_subscribe(
			bus, "org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
			"/org/freedesktop/DBus", "org.kde.Shutdown", G_DBUS_SIGNAL_FLAGS_NONE,
			on_shutdown_name, NULL, NULL);
		g_main_context_pop_thread_default(context);
		listening = g_object_ref(bus);
	}
	while (g_main_context_iteration(context, FALSE))
		;
}

/* 1 = the name has an owner, 0 = it has none, -1 = the bus did not answer (NOT the same as 0) */
static int name_owner_state(GDBusConnection *bus, const char *name)
{
	g_autoptr(GVariant) response = g_dbus_connection_call_sync(
		bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
		"NameHasOwner", g_variant_new("(s)", name), G_VARIANT_TYPE("(b)"),
		G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_NAME_MS, NULL, NULL);
	gboolean has = FALSE;

	if (!response)
		return -1;
	g_variant_get(response, "(b)", &has);
	return has ? 1 : 0;
}

/* plasma-shutdown is gone: did it leave a logout under way?  Arms the watch only on a `true`. */
static void shutdown_released_judge(GDBusConnection *bus)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) answer = g_dbus_connection_call_sync(
		bus, "org.kde.ksmserver", "/KSMServer", "org.kde.KSMServerInterface", "isShuttingDown", NULL,
		G_VARIANT_TYPE("(b)"), G_DBUS_CALL_FLAGS_NO_AUTO_START, WAIT_RESPONSE_MS, NULL, &mistake);
	gboolean shutting = FALSE;

	shutdown_released = FALSE;
	if (!answer) {
		registro_dice(LOG_SESSION,
		              "⚠ Plasma: plasma-shutdown ended and ksmserver does not say whether a logout is "
		              "under way (%s) — nothing is forced",
		              mistake ? mistake->message : "no reason given");
		return;
	}
	g_variant_get(answer, "(b)", &shutting);
	if (!shutting) {
		registro_dice(LOG_SESSION,
		              "Plasma: plasma-shutdown ended and ksmserver is not shutting down (logout "
		              "cancelled, or not a logout) — nothing is forced");
		return;
	}
	logout_asked = TRUE;
}

bool session_kde_logout_watch(void)
{
	static gint64 last_look, inactive_since, last_try;
	static gboolean seen_active, finished;
	static int tries;
	g_autoptr(GDBusConnection) bus = NULL;
	char state[32];
	gint64 now = g_get_monotonic_time();

	if (finished || !e_kde() || now - last_look < 1000 * 1000)
		return FALSE;
	last_look = now;
	bus = sess_bus(NULL);
	if (!bus)
		return FALSE;
	shutdown_name_listen(bus);
	switch (name_owner_state(bus, "org.kde.KWin")) {
	case -1: /* the bus did not answer: nothing is learned, nothing is forgotten */
		return FALSE;
	case 0:
		/* the normal road (or no desktop yet): nothing to help; a new desktop starts the watch again */
		seen_active = FALSE;
		shutdown_released = FALSE;
		logout_asked = FALSE;
		inactive_since = 0;
		tries = 0;
		return FALSE;
	}
	if (shutdown_released)
		shutdown_released_judge(bus);
	unit_active_state(bus, SESSION_UNIT_PLASMA, state, sizeof state);
	if (g_strcmp0(state, "active") == 0)
		seen_active = TRUE;
	if (!logout_asked) {
		if (g_strcmp0(state, "active") == 0) {
			inactive_since = 0;
			tries = 0;
			return FALSE;
		}
		if (!seen_active || g_strcmp0(state, "activating") == 0)
			return FALSE;
	}
	if (!inactive_since) {
		inactive_since = now;
		registro_dice(LOG_SESSION,
		              "⭐ Plasma: a logout is under way and KWin is still up (%s) — %s is %s; giving it "
		              "%d s to finish by itself, then it is completed",
		              logout_asked ? "plasma-shutdown ended, ksmserver is shutting down"
		                           : "the workspace target stopped",
		              SESSION_UNIT_PLASMA, state, KDE_LOGOUT_GRACE_MS / 1000);
		return FALSE;
	}
	if (now - inactive_since < (gint64)KDE_LOGOUT_GRACE_MS * 1000 ||
	    (last_try && now - last_try < (gint64)KDE_LOGOUT_RETRY_MS * 1000))
		return FALSE;
	last_try = now;
	{
		/* ⭐ After the «fail» attempts the mode is `replace`: a queued start job (a slow unit can
		 *    hold one for 90 s) replaces nothing of the user's work, and `fail` would be refused as
		 *    long as it lasts.  `finished` only once the stop is accepted. */
		const char *mode = tries < KDE_LOGOUT_TRIES ? "fail" : "replace";
		g_autoptr(GError) mistake = NULL;
		g_autoptr(GVariant) response = g_dbus_connection_call_sync(
			bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
			"org.freedesktop.systemd1.Manager", "StopUnit",
			g_variant_new("(ss)", "graphical-session.target", mode), NULL,
			G_DBUS_CALL_FLAGS_NONE, WAIT_RESPONSE_MS, NULL, &mistake);

		tries++;
		if (response) {
			registro_dice(LOG_SESSION,
			              "⭐ Plasma logout stopped halfway: stop of graphical-session.target accepted "
			              "(attempt %d, mode %s) — the normal end follows", tries, mode);
			finished = TRUE;
		} else if (tries >= 2 * KDE_LOGOUT_TRIES) {
			registro_dice(LOG_SESSION,
			              "⛔ Plasma logout stopped halfway: stop of graphical-session.target refused "
			              "%d times (last: %s) — giving up on it: the session is to be closed by the "
			              "product's own road", tries, mistake ? mistake->message : "no reason");
			finished = TRUE;
			return TRUE;
		} else
			registro_dice(LOG_SESSION,
			              "⚠ Plasma logout stopped halfway: stop of graphical-session.target refused "
			              "(attempt %d, mode %s): %s — retrying in %d s", tries, mode,
			              mistake ? mistake->message : "no reason", KDE_LOGOUT_RETRY_MS / 1000);
	}
	return FALSE;
}

/* ⭐ When the child exits: the last moment someone can do it.  If the clear-out was still
 *    to do, it is retried for at most `CLEAR_OUT_EXIT_WAIT_MS`; otherwise it is the usual
 *    one (a session that stays alive for the reattach is NOT waited for). */
int session_clear_out_handler_exit(const char *why)
{
	gint64 expiry = g_get_monotonic_time() + (gint64) CLEAR_OUT_EXIT_WAIT_MS * 1000;

	for (;;) {
		if (clear_out_handler_run(why, clear_out_due)) {
			clear_out_settled(why);
			return clear_out_refused ? 2 : 0;
		}
		if (!clear_out_due || g_get_monotonic_time() >= expiry)
			break;
		g_usleep(200 * 1000);
	}
	if (clear_out_due)
		registro_dice(LOG_SESSION,
		              "⛔ R1/R2 (%s): the clear-out of the user manager is still TO DO and "
		              "the child is leaving (the session answered for %lld ms after it was "
		              "seen over) — the next child does it at its startup; until then a "
		              "local login of this user would inherit our variables",
		              why,
		              (long long) ((g_get_monotonic_time() - clear_out_due_since) / 1000));
	return 1;
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

/* ⭐ 1.0.0 — PRELOCAL close, parent gone: the FORCED step (SIGTERM to the compositor, StopUnit, Logout 2) is NOT taken.  When the
 *    parent that asked for the close dies, the root side's hook is released and the local desktop of the user may be starting:
 *    forcing could hit it.  Set by the child (`session_force_unless_orphaned()`), consulted before each forced step. */
static bool force_guard_on;
static pid_t force_guard_ppid;

void session_force_unless_orphaned(bool on)
{
	force_guard_on = on;
	force_guard_ppid = getppid();
}

static bool force_refused(void)
{
	if (!force_guard_on || getppid() == force_guard_ppid)
		return false;
	registro_dice(LOG_SESSION,
	              "⛔ 1.0.0: the orderly close did not complete and my parent is GONE (a local login held for this close has been "
	              "released): I do NOT force — the local desktop may be starting");
	return true;
}

static bool really_terminate(void)
{
	if (!session_alive()) {
		/* ⭐ The desktop may be gone already (it logged out by itself, or died): then the close is
		 *    DONE, not failed, and the caller must exit and clear out.  ⛔ But «the name is not
		 *    on the bus» is the WEAK question (it also answers no for a bus that did not reply, a
		 *    desktop that has not taken its name yet, or a manager that died with the compositor
		 *    alive): «gone» needs the same double proof as `wait_until_done()` — the name AND the
		 *    units/process of the desktop.  If the units or the process are still there, nothing
		 *    is claimed: the normal road below goes on (orderly exit, then the forced step). */
		if (inactive_unit(NULL)) {
			registro_dice(LOG_SESSION,
			              "there was no session to stop: no session name on the bus and no unit or "
			              "process of the desktop left — the desktop is already gone, the close is done");
			return true;
		}
		registro_dice(LOG_SESSION,
		              "⚠ the session name is not on the bus but the desktop's units or processes are "
		              "still there: not claimed as closed, closing it the normal way");
	}

	if (e_xfce()) {
		registro_dice(LOG_SESSION,
		              "asking the XFCE session to exit "
		              "(org.xfce.Session.Manager.Logout)");
		if (exit_xfce() && wait_until_done()) {
			registro_dice(LOG_SESSION, "the graphical session has exited");
			return true;
		}
		if (force_refused())
			return false;
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
		if (force_refused())
			return false;
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
		if (force_refused())
			return false;
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

	if (force_refused())
		return false;
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
 * ⭐ PHASE 15, D-015 — THE VERIFY: nothing is written here any more (the keys are in
 *    `/etc/dconf/db/remotix`, or `locks.db`/`shm` in the fallback); every key of `DCONF_KEYS` is RE-READ through
 *    the session profile — as the Shell and the `gsd-*` read it — and said whether in force.
 *    Written is not in force until it is re-read.
 */
static void session_dconf_verify(void)
{
	struct schema_open a = { NULL, NULL };
	const char *last = NULL;
	int ok = 0, bad = 0;

	if (!session_dconf_of_session()) {
		registro_dice(LOG_SESSION,
		              "⛔ D-015: the session dconf is NOT in force — none of the session keys "
		              "(Ctrl+Alt+F*, «Log Out…», «Switch User», lock, suspend, standby) "
		              "applies, and nothing is written in the user's settings");
		return;
	}
	for (guint i = 0; i < G_N_ELEMENTS(DCONF_KEYS); i++) {
		const struct dconf_key *k = &DCONF_KEYS[i];

		if (g_strcmp0(last, k->schema) != 0) {
			close_schema(&a);
			a = open_schema(k->schema);
			last = k->schema;
		}
		if (!schema_has_key(&a, k->key, k->schema))
			continue;
		if (k->text) {
			g_autoptr(GVariant) want = g_variant_parse(NULL, k->text, NULL, NULL, NULL);
			g_autoptr(GVariant) got = g_settings_get_value(a.settings, k->key);

			if (want && got && g_variant_equal(want, got))
				ok++;
			else {
				g_autofree char *read = got ? g_variant_print(got, FALSE) : NULL;

				bad++;
				registro_dice(LOG_SESSION,
				              "⛔ D-015: %s%s should be %s, the session reads %s — NOT in force",
				              k->dir, k->key, k->text, read ? read : "nothing");
			}
		}
		if (dconf_locked && g_settings_is_writable(a.settings, k->key)) {
			bad++;
			registro_dice(LOG_SESSION, "⛔ D-015: %s%s is still WRITABLE: the lock does not hold",
			              k->dir, k->key);
		}
	}
	close_schema(&a);
	registro_dice(LOG_SESSION,
	              "%s D-015: session keys re-read: %d in force, %d NOT%s",
	              bad ? "⛔" : "⭐", ok, bad,
	              dconf_locked ? " (value + lock)" : " (FALLBACK: values in the session, no lock)");
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 13 / 15 — XFCE'S LEVERS: READ, WRITE, RE-READ, SAY WHETHER IT IS IN FORCE.
 *
 * ⛔⛔ Since 13 Nov 2026 REMOTIX WRITES NOTHING PERMANENT in the user's xfconf
 *     channels while the session lives: what it imposes is LOCKED in the
 *     session folder (`xfce_session_xfconf()`, below).  What is here are the
 *     tools to READ the user's values, to keep a COPY of the few locked ones and
 *     to PUT THEM BACK at the end (`xfce_restore_keys()`).
 *
 * ⛔⛔ AND IT IS ALWAYS RE-READ: `xfconf-query` exits with **zero even when the
 *     daemon refuses** — the API is asynchronous, the local cache answers first
 *     and the old value comes back later (`STUDIES.md` §xfce §10.6).  ⇒ The writer's
 *     exit status says nothing: only re-reading tells the truth.
 */

static char **array_entries(const char *output);

/* Property `key` of `channel`, as the user's (or the effective) xfconf has it.
 * TRUE if it exists.  Scalar: `*scalar` (stripped); array: `*entries` (the
 * `+`/`-` strings, NULL-terminated).  ⚠ The exit status IS looked at here:
 * `xfconf-query` fails if the property does not exist, and that is the answer
 * «absent».  A scalar that prints nothing is a `type="empty"` left by a
 * lock (§10.6): it is NOT a value, it counts as absent. */
static gboolean xfconf_get(const char *channel, const char *key, gboolean array,
                             char **scalar, char ***entries)
{
	char *cmd[] = { "xfconf-query", "-c", (char *) channel, "-p", (char *) key, NULL };
	g_autoptr(GError) mistake = NULL;
	g_autofree char *out = NULL;
	g_autofree char *err = NULL;
	int state = 0;

	if (scalar)
		*scalar = NULL;
	if (entries)
		*entries = NULL;
	if (!g_spawn_sync(NULL, cmd, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, &out, &err, &state,
	                  &mistake) ||
	    !g_spawn_check_wait_status(state, NULL))
		return FALSE;
	if (array) {
		char **list = array_entries(out);

		if (!list || !list[0]) {
			g_strfreev(list);
			return FALSE;
		}
		if (entries)
			*entries = list;
		else
			g_strfreev(list);
		return TRUE;
	}
	if (!out)
		return FALSE;
	g_strstrip(out);
	if (!*out)
		return FALSE;
	if (scalar)
		*scalar = g_steal_pointer(&out);
	return TRUE;
}

/* A scalar written and RE-READ.  TRUE if re-reading gives exactly the written value. */
static gboolean xfconf_set(const char *channel, const char *key, const char *kind,
                             const char *value)
{
	g_autofree char *set = g_strdup_printf("--set=%s", value);
	char *write[] = { "xfconf-query", "-c", (char *) channel, "-p", (char *) key, "-n",
		           "-t", (char *) kind, set, NULL };
	g_autofree char *read = NULL;

	run(write);
	return xfconf_get(channel, key, FALSE, &read, NULL) && g_strcmp0(read, value) == 0;
}

/* An array of strings written and RE-READ.  ⚠ `--set=-lock-screen` and not
 * `-s -lock-screen`: a value starting with a dash, written separately, is read
 * as an option. */
static gboolean xfconf_set_array(const char *channel, const char *key, char **entries)
{
	g_autoptr(GPtrArray) write = g_ptr_array_new_with_free_func(g_free);
	g_auto(GStrv) reread = NULL;

	g_ptr_array_add(write, g_strdup("xfconf-query"));
	g_ptr_array_add(write, g_strdup("-c"));
	g_ptr_array_add(write, g_strdup(channel));
	g_ptr_array_add(write, g_strdup("-p"));
	g_ptr_array_add(write, g_strdup(key));
	g_ptr_array_add(write, g_strdup("-n"));
	g_ptr_array_add(write, g_strdup("-a"));
	for (int i = 0; entries[i]; i++) {
		g_ptr_array_add(write, g_strdup("--type=string"));
		g_ptr_array_add(write, g_strdup_printf("--set=%s", entries[i]));
	}
	g_ptr_array_add(write, NULL);
	run((char **) write->pdata);
	return xfconf_get(channel, key, TRUE, NULL, &reread) &&
	       g_strv_equal((const char *const *) reread, (const char *const *) entries);
}

/*
 * ⭐ 13 Nov 2026 (review) — WHAT THE SYSTEM FILES GIVE TO A KEY.
 *
 * `xfconf-query` answers with the EFFECTIVE value: the user's, or — if the user has
 * none — the one of a system channel file (`<dir>/xfce4/xfconf/xfce-perchannel-xml/`,
 * for every `<dir>` of `XDG_CONFIG_DIRS`).  `[M]` the XFCE box: `/etc/xdg` gives
 * `xfce4-session` only `FailsafeSessionName`, the failsafe sessions and an EMPTY
 * `LockCommand` (which reads as absent); other distributions ship more (a panel
 * channel, for one).  ⇒ A value that is exactly the system's is NOT a value of the
 * user's: the copy notes «absent» for it and the restore takes the key away — a
 * default of the system is never written in the user's file — and a key taken away
 * is «gone» also when what is read afterwards is the system's value.
 *
 * ⚠ Declared: the files are read HERE, along THIS process's `XDG_CONFIG_DIRS`, first
 *   folder first (the strongest for xfconfd); `xfconfd` reads them along the user
 *   manager's, which may differ.
 * ⛔ THE LIMIT, MEASURED (14 Nov 2026, openSUSE Tumbleweed, whose `/etc/xdg` gives
 *    `dpms-enabled=true`, `SaveOnExit=false` and a whole panel): `xfconfd` does NOT
 *    write in the user's file a value EQUAL to the system's — set again with
 *    `xfconf-query`, re-read right, the file still says `type="empty"`.  ⇒ For such a
 *    key the EFFECTIVE value stays identical, before and after the remote session; but
 *    an EXPLICIT line of the user's, equal to the system default, does NOT stay in the
 *    user's file: if the distribution changes that default one day, the user gets the
 *    new one.  It is a limit of `xfconfd`, not a choice: writing the line is not
 *    possible from outside.  ⇒ Such a value is noted «absent» in the copy (which is
 *    what the file will say anyway) and the restore takes the key away.
 */
struct xfce_sys_seek {
	char **want; /* the path of the key, split */
	guint n;
	guint depth;   /* <property> open */
	guint matched; /* how many of them, from the top, are the path */
	gboolean found;
	gboolean closed;
	char *kind;
	char *scalar;
	GPtrArray *entries;
};

static void xfce_sys_start(GMarkupParseContext *ctx, const char *element, const char **names,
                             const char **values, gpointer data, GError **error)
{
	struct xfce_sys_seek *s = data;
	const char *name = NULL, *type = NULL, *value = NULL;

	for (int i = 0; names[i]; i++) {
		if (strcmp(names[i], "name") == 0)
			name = values[i];
		else if (strcmp(names[i], "type") == 0)
			type = values[i];
		else if (strcmp(names[i], "value") == 0)
			value = values[i];
	}
	if (strcmp(element, "value") == 0) {
		/* an entry of the wanted array (not of an array further down) */
		if (s->found && !s->closed && s->depth == s->n && value)
			g_ptr_array_add(s->entries, g_strdup(value));
		return;
	}
	if (strcmp(element, "property") != 0)
		return;
	if (!s->found && s->depth == s->matched && s->matched < s->n && name &&
	    strcmp(name, s->want[s->matched]) == 0) {
		s->matched++;
		if (s->matched == s->n) {
			s->found = TRUE;
			s->kind = g_strdup(type ? type : "empty");
			s->scalar = g_strdup(value);
		}
	}
	s->depth++;
}

static void xfce_sys_end(GMarkupParseContext *ctx, const char *element, gpointer data,
                           GError **error)
{
	struct xfce_sys_seek *s = data;

	if (strcmp(element, "property") != 0 || !s->depth)
		return;
	s->depth--;
	if (s->found && s->depth < s->n)
		s->closed = TRUE;
	if (!s->found && s->matched > s->depth)
		s->matched = s->depth;
}

/* TRUE if a system file gives `key` a value of the asked shape (scalar, or array);
 * the value in `*scalar` / `*entries` (either may be NULL). */
static gboolean xfce_system_value(const char *channel, const char *key, gboolean array,
                                    char **scalar, char ***entries)
{
	static const GMarkupParser parser = { xfce_sys_start, xfce_sys_end, NULL, NULL, NULL };
	g_auto(GStrv) dirs = session_config_dirs_strv();
	g_autofree char *name = g_strdup_printf("%s.xml", channel);

	if (scalar)
		*scalar = NULL;
	if (entries)
		*entries = NULL;
	if (key[0] != '/')
		return FALSE;
	for (int i = 0; dirs && dirs[i]; i++) {
		g_autofree char *file = g_build_filename(dirs[i], "xfce4", "xfconf",
		                                           "xfce-perchannel-xml", name, NULL);
		g_autofree char *text = NULL;
		struct xfce_sys_seek s = { 0 };
		GMarkupParseContext *ctx;
		gboolean defined, is_array, fits;
		gsize len = 0;

		/* ⚠ never OUR session folder: what is there is the lock, not the system */
		if (strstr(dirs[i], "/remotix/xdg-xfce") ||
		    !g_file_get_contents(file, &text, &len, NULL))
			continue;
		s.want = g_strsplit(key + 1, "/", -1);
		s.n = g_strv_length(s.want);
		s.entries = g_ptr_array_new_with_free_func(g_free);
		ctx = g_markup_parse_context_new(&parser, 0, &s, NULL);
		g_markup_parse_context_parse(ctx, text, len, NULL);
		g_markup_parse_context_free(ctx);
		defined = s.found && g_strcmp0(s.kind, "empty") != 0;
		is_array = g_strcmp0(s.kind, "array") == 0;
		fits = defined && (array ? is_array && s.entries->len > 0
		                         : !is_array && s.scalar && *s.scalar);
		if (fits && array && entries) {
			g_ptr_array_add(s.entries, NULL);
			*entries = (char **) g_ptr_array_free(g_steal_pointer(&s.entries), FALSE);
		}
		if (fits && !array && scalar)
			*scalar = g_steal_pointer(&s.scalar);
		g_strfreev(s.want);
		g_free(s.kind);
		g_free(s.scalar);
		if (s.entries)
			g_ptr_array_free(s.entries, TRUE);
		/* the first folder that defines it decides: for xfconfd it is the strongest */
		if (defined)
			return fits;
	}
	return FALSE;
}

/* TRUE if the value just read is exactly the one the system files give. */
static gboolean xfce_same_as_system(const char *channel, const char *key, gboolean array,
                                      const char *scalar, char **entries)
{
	g_autofree char *sys = NULL;
	g_auto(GStrv) sys_entries = NULL;

	if (!xfce_system_value(channel, key, array, &sys, &sys_entries))
		return FALSE;
	if (array)
		return entries && g_strv_equal((const char *const *) entries,
		                               (const char *const *) sys_entries);
	return g_strcmp0(scalar, sys) == 0;
}

/* A property taken away, and RE-READ: it must be gone.
 * ⛔ 13 Nov 2026: a key that was locked is left in the user's file as
 *    `type="empty"` and `xfconf-query -r` does not see it as a property to remove:
 *    so it is first given a value (any), and THEN removed. */
static gboolean xfconf_unset(const char *channel, const char *key)
{
	char *dummy[] = { "xfconf-query", "-c", (char *) channel, "-p", (char *) key, "-n",
		           "-t", "string", "--set=x", NULL };
	char *cmd[] = { "xfconf-query", "-c", (char *) channel, "-p", (char *) key, "-r", NULL };
	g_autoptr(GError) mistake = NULL;
	g_autofree char *scalar = NULL;
	g_auto(GStrv) entries = NULL;
	int state = 0;

	/* ⚠ no `run()`: «it does not exist» is a failure of the command, and it is
	 *   the result we want. */
	g_spawn_sync(NULL, dummy, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, NULL, &state,
	             &mistake);
	g_spawn_sync(NULL, cmd, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, NULL, &state,
	             &mistake);
	/* ⚠ Gone = NO VALUE OF THE USER'S can be read.  Not «not listed»: a key that the
	 *   system files define (`LockCommand`, `FailsafeSessionName`…) stays in the listing
	 *   as an empty placeholder `type="empty"` — xfconfd dumps the system tree into the
	 *   user's file at every save, with or without locks: it is the standard, not a
	 *   leftover.  ⚠ And if the system files give it a real value, THAT is what is read
	 *   after the removal: it is «gone» all the same (`xfce_same_as_system()`). */
	if (xfconf_get(channel, key, TRUE, NULL, &entries))
		return xfce_same_as_system(channel, key, TRUE, NULL, entries);
	if (xfconf_get(channel, key, FALSE, &scalar, NULL))
		return xfce_same_as_system(channel, key, FALSE, scalar, NULL);
	return TRUE;
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
 * is no KIOSK that removes them (`STUDIES.md` §xfce §10.4): they are removed
 * by LOCKING `items` in the session (since 13 Nov 2026).
 *
 * ⛔ ONLY the named families are removed: lock, suspend
 *    (with hibernate and hybrid sleep, which are the same family), reboot
 *    and power-off.  «Log Out» (`logout`, `logout-dialog`) STAYS — §4.1-ter, it is
 *    the only door.
 * ⭐ And since 21 Sep 2026, evening, «Switch User» too (`switch-user`) — the
 *    user's decision: *«remove Switch User too to make the
 *    behaviour uniform across all DEs: the only entry that must remain is logout»*.
 *    KDE removes it since phase 12 (KIOSK), GNOME with the dconf lockdown.
 * ⚠ The plugin does NOT read `ShowSwitchUser` / `Show*` (13 Nov 2026, measured):
 *   lock-screen and switch-user disappear ONLY with `items`.
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

/* The entries as the session wants them: the ones to remove go from `+` to
 * `-`, the others stay identical and in their order.  NULL-terminated. */
static char **actions_without_power(const char *const *from)
{
	g_autoptr(GPtrArray) out = g_ptr_array_new_with_free_func(g_free);

	for (int i = 0; from[i]; i++) {
		if (to_remove(from[i]))
			g_ptr_array_add(out, g_strdup_printf("-%s", from[i] + 1));
		else
			g_ptr_array_add(out, g_strdup(from[i]));
	}
	g_ptr_array_add(out, NULL);
	return (char **) g_ptr_array_free(g_steal_pointer(&out), FALSE);
}

/* The plugin types REMOTIX puts in the panel lock file (`xfce_panel_xml()`): the only
 * ones its lock can have damaged, hence the only ones the integrity check repairs. */
#define PLUGIN_ACTIONS "actions"
#define PLUGIN_WHISKER "whiskermenu"

/* The `actions` plugins of the USER's panel channel: `/plugins/plugin-<N>`.
 * `*any_plugin` is TRUE if the channel has at least one plugin of any kind (a
 * user who never opened XFCE has none: the channel is empty until the panel is
 * born and migrates the default layout). */
static GPtrArray *panel_plugins(const char *type, gboolean *any_plugin)
{
	char *list_cmd[] = { "xfconf-query", "-c", "xfce4-panel", "-l", "-v", NULL };
	g_autofree char *listing = ask(list_cmd);
	g_auto(GStrv) lines = g_strsplit(listing ? listing : "", "\n", -1);
	GPtrArray *found = g_ptr_array_new_with_free_func(g_free);

	*any_plugin = FALSE;
	/* A line of `-l -v` is «property  value», aligned with spaces. */
	for (int i = 0; lines[i]; i++) {
		g_auto(GStrv) parts = g_strsplit_set(g_strstrip(lines[i]), " \t", 2);
		const char *nr;

		if (!parts[0] || !g_str_has_prefix(parts[0], "/plugins/plugin-"))
			continue;
		nr = parts[0] + strlen("/plugins/plugin-");
		if (!*nr || strspn(nr, "0123456789") != strlen(nr))
			continue;
		*any_plugin = TRUE;
		if (parts[1] && g_strcmp0(g_strstrip(parts[1]), type) == 0)
			g_ptr_array_add(found, g_strdup(parts[0]));
	}
	return found;
}

static GPtrArray *panel_action_plugins(gboolean *any_plugin)
{
	return panel_plugins(PLUGIN_ACTIONS, any_plugin);
}

/* The text of the STANDARD layout, `xfce4/panel/default.xml` looked up along
 * `XDG_CONFIG_DIRS` (`STUDIES.md` §xfce §9; the first file found is the one the
 * panel migrates).  NULL if there is none. */
static char *default_panel_text(void)
{
	g_auto(GStrv) dirs = session_config_dirs_strv();

	for (int i = 0; dirs && dirs[i]; i++) {
		g_autofree char *file = g_build_filename(dirs[i], "xfce4", "panel", "default.xml",
		                                           NULL);
		char *text = NULL;

		if (g_file_get_contents(file, &text, NULL, NULL))
			return text;
	}
	return NULL;
}

/* The plugins of `type` in the STANDARD layout, for the user whose panel channel is
 * still empty: `/plugins/plugin-<N>` as above. */
static GPtrArray *default_plugins(const char *type)
{
	GPtrArray *found = g_ptr_array_new_with_free_func(g_free);
	g_autofree char *wanted_value = g_strdup_printf("value=\"%s\"", type);
	g_autofree char *text = default_panel_text();

	/* every `<property …>` tag with value="actions" and name="plugin-N" */
	for (const char *p = text; p && (p = strstr(p, "<property ")); p++) {
		const char *end = strchr(p, '>');
		g_autofree char *tag = end ? g_strndup(p, end - p) : NULL;
		const char *name;

		if (!tag)
			break;
		name = strstr(tag, "name=\"plugin-");

		if (!name || !strstr(tag, wanted_value))
			continue;
		name += strlen("name=\"plugin-");
		if (strspn(name, "0123456789") > 0)
			g_ptr_array_add(found,
			                g_strdup_printf("/plugins/plugin-%.*s",
			                                (int) strspn(name, "0123456789"), name));
	}
	return found;
}

/* The type the STANDARD layout gives to `key` (`/plugins/plugin-<N>`), or NULL. */
static char *default_plugin_type(const char *key)
{
	g_autofree char *text = default_panel_text();
	g_autofree char *wanted_name = g_strdup_printf("name=\"plugin-%s\"",
	                                                 key + strlen("/plugins/plugin-"));

	for (const char *p = text; p && (p = strstr(p, "<property ")); p++) {
		const char *end = strchr(p, '>');
		g_autofree char *tag = end ? g_strndup(p, end - p) : NULL;
		const char *value;

		if (!tag)
			break;
		value = strstr(tag, "value=\"");
		if (strstr(tag, wanted_name) && value) {
			value += strlen("value=\"");
			return g_strndup(value, strcspn(value, "\""));
		}
	}
	return NULL;
}

static GPtrArray *default_action_plugins(void)
{
	return default_plugins(PLUGIN_ACTIONS);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ 13 Nov 2026 — THE COPY OF THE LOCKED KEYS, AND ITS RESTORE.
 *
 * ⛔ THE FACT (measured on the XFCE box): when a property is locked, at the
 *    first save of the channel `xfconfd` writes it in the USER's file as
 *    `type="empty"` — the user's real value is LOST.  ⇒ Before the lock, REMOTIX
 *    writes in a file of the user's own (`~/.local/state/remotix/xfce-chiavi`,
 *    0600) the value each locked key has for the user, with its type, or «absent»;
 *    at the end of the session, with the drop-in gone and `xfconfd` restarted, it
 *    puts every one back (or takes the key away, if it was absent).  Every other
 *    change of the user stays.
 *
 * ⭐ The copy is NOT deleted when restored: it is marked (`[stato] ripristinato`).
 *    A copy NOT marked is a session that died badly: whoever comes first —
 *    the clean-up of the next child, or the next birth — restores it BEFORE
 *    anything else.
 * ⭐ A PARTIAL RESTORE (review of 13 Nov 2026): a key put back LEAVES the copy at
 *    once; only the keys that did NOT go back stay in it, pending, and only those
 *    are tried again.  (Before, the whole copy stayed «not restored» and was applied
 *    again at every clean-up, over what the user had changed since at the monitor.)
 *    And a birth that finds pending keys KEEPS their originals and ADDS to the same
 *    copy the keys of that day (`xfce_copy_keep_pending()`): a new `actions` button
 *    is never locked without a copy, and an original is never read again from a
 *    channel where it is no longer there.
 * ⚠ Declared — THE PERMANENT FAILURE: a key that can NEVER be put back (a type
 *   `xfconf-query` refuses, an `xfconfd` that does not answer, a channel file that
 *   cannot be written) stays pending FOR EVER: it is tried again at every clean-up and
 *   at every birth, with a ⛔ line in the log each time, and REMOTIX never gives it
 *   up by itself.  Until the day it goes back that ONE key has, in local, the XFCE
 *   standard; and the day it does go back, the value of the copy replaces what the
 *   user may have set for it in the meantime.  The other keys are not touched.  The
 *   way out is by hand: delete its `[kN]` group from the copy.
 *
 * ⭐ WHERE THE COPY LIVES (the coordinator's decision, 13 Nov 2026):
 *    1. on DISK, `~/.local/state/remotix/xfce-chiavi`: it survives everything;
 *    2. if that cannot be written, in RAM, `$XDG_RUNTIME_DIR/remotix/xfce-chiavi`,
 *       DECLARED in the log: it lives as long as the user's runtime folder — a
 *       reboot, or the user's last logout without lingering, takes it away; a crash
 *       followed by one of those loses the user's values of the locked keys;
 *    3. if not even that: the locks are applied ALL THE SAME — the protection of the
 *       server wins over the user's comfort — with a ⛔ line that says the user's
 *       values will NOT come back, and lists them, to be put back by hand.
 *    The restore looks in both places, RAM first and disk last (the disk copy is the
 *    older and the truer one: on the same key, it has the last word).
 *
 * ⚠ Declared: if the user opens XFCE at the monitor between the crash and the
 *   restore, those few keys have the standard value of XFCE (buttons all visible).
 * ⚠ Declared: a value that is exactly the one the SYSTEM files give is noted
 *   «absent» (`xfce_same_as_system()`, above): the restore takes the key away and the
 *   system's value shows again, without a default written in the user's file.  ⛔ And
 *   so «put back» means the EFFECTIVE value: an explicit line of the user's equal to
 *   the system default is NOT in their file afterwards — `xfconfd` does not write it
 *   (measured, 14 Nov 2026: «THE LIMIT», in the box of `xfce_system_value()`).
 */
#define XFCE_COPY_NAME "xfce-chiavi"
#define XFCE_OLD_MARK_NAME "xfce-vecchi-ripristinati"

static char *xfce_state_file(const char *name)
{
	g_autofree char *folder = g_build_filename(g_get_user_state_dir(), "remotix", NULL);

	if (!is_our_dir(folder))
		return NULL;
	return g_build_filename(folder, name, NULL);
}

/* The path of the copy: on disk, or (`ram`) in the user's runtime folder.  ⚠ The
 * RAM folder is NOT created here: whoever writes there creates it. */
static char *xfce_copy_path(gboolean ram)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!ram)
		return xfce_state_file(XFCE_COPY_NAME);
	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, "remotix", XFCE_COPY_NAME, NULL);
}

/* The copy, being made: the user's value of `key`, with the type, or «absent».
 * `kind` is "bool", "uint", "string", "plugin" or "array".  ⚠ A value that is the
 * system's is «absent»: `xfconfd` itself keeps no line for it in the user's file
 * (see the box above). */
static void xfce_copy_note(GKeyFile *copy, int *count, const char *channel, const char *key,
                             const char *kind)
{
	g_autofree char *group = g_strdup_printf("k%d", (*count)++);
	g_autofree char *scalar = NULL;
	g_auto(GStrv) entries = NULL;
	gboolean array = g_strcmp0(kind, "array") == 0;
	gboolean exists = xfconf_get(channel, key, array, &scalar, &entries) &&
	                  !xfce_same_as_system(channel, key, array, scalar, entries);

	g_key_file_set_string(copy, group, "channel", channel);
	g_key_file_set_string(copy, group, "path", key);
	g_key_file_set_string(copy, group, "kind", kind);
	g_key_file_set_boolean(copy, group, "absent", !exists);
	if (exists && array)
		g_key_file_set_string_list(copy, group, "values", (const char *const *) entries,
		                           g_strv_length(entries));
	else if (exists)
		g_key_file_set_string(copy, group, "value", scalar);
}

/* The user's values held by a copy, in one line for the log («channel key = value»). */
static char *xfce_copy_said(GKeyFile *copy)
{
	g_auto(GStrv) groups = g_key_file_get_groups(copy, NULL);
	GString *said = g_string_new(NULL);

	for (int i = 0; groups[i]; i++) {
		g_autofree char *channel = g_key_file_get_string(copy, groups[i], "channel", NULL);
		g_autofree char *key = g_key_file_get_string(copy, groups[i], "path", NULL);
		g_autofree char *value = g_key_file_get_value(copy, groups[i], "value", NULL);
		g_autofree char *values = g_key_file_get_value(copy, groups[i], "values", NULL);

		if (groups[i][0] != 'k' || !channel || !key || (!value && !values))
			continue;
		g_string_append_printf(said, "%s%s %s = %s", said->len ? " · " : "", channel, key,
		                       value ? value : values);
	}
	if (!said->len)
		g_string_append(said, "none — the user had no value of their own for these keys");
	return g_string_free(said, FALSE);
}

/* A birth that finds keys still PENDING (a restore that did not put them back): their
 * originals, as the pending copies hold them, take the place of what `copy` has just
 * read for the same key — what is in the channel now is NOT the user's value — and
 * the pending keys `copy` does not have are added to it.  The keys of today that are
 * not pending stay as just read.  Disk first: on the same key it wins over RAM.
 * Returns how many pending keys were kept. */
static int xfce_copy_keep_pending(GKeyFile *copy, int *count)
{
	g_autoptr(GHashTable) taken = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, NULL);
	int kept = 0;

	for (int ram = 0; ram < 2; ram++) {
		g_autofree char *fpath = xfce_copy_path(ram);
		g_autoptr(GKeyFile) old = g_key_file_new();
		g_auto(GStrv) groups = NULL;

		if (!fpath || !g_key_file_load_from_file(old, fpath, G_KEY_FILE_NONE, NULL) ||
		    g_key_file_get_boolean(old, "stato", "ripristinato", NULL))
			continue;
		groups = g_key_file_get_groups(old, NULL);
		for (int i = 0; groups[i]; i++) {
			g_autofree char *channel = g_key_file_get_string(old, groups[i], "channel", NULL);
			g_autofree char *key = g_key_file_get_string(old, groups[i], "path", NULL);
			g_auto(GStrv) today = g_key_file_get_groups(copy, NULL);
			g_auto(GStrv) fields = NULL;
			g_autofree char *id = NULL;
			g_autofree char *target = NULL;

			if (groups[i][0] != 'k' || !channel || !key)
				continue;
			id = g_strdup_printf("%s\n%s", channel, key);
			if (g_hash_table_contains(taken, id))
				continue;
			for (int j = 0; today[j] && !target; j++) {
				g_autofree char *c = g_key_file_get_string(copy, today[j], "channel", NULL);
				g_autofree char *k = g_key_file_get_string(copy, today[j], "path", NULL);

				if (today[j][0] == 'k' && g_strcmp0(c, channel) == 0 &&
				    g_strcmp0(k, key) == 0)
					target = g_strdup(today[j]);
			}
			if (target)
				g_key_file_remove_group(copy, target, NULL);
			else
				target = g_strdup_printf("k%d", (*count)++);
			fields = g_key_file_get_keys(old, groups[i], NULL, NULL);
			for (int j = 0; fields && fields[j]; j++) {
				g_autofree char *v = g_key_file_get_value(old, groups[i], fields[j], NULL);

				if (v)
					g_key_file_set_value(copy, target, fields[j], v);
			}
			g_hash_table_add(taken, g_steal_pointer(&id));
			kept++;
		}
	}
	return kept;
}

/* The plugin type a `kind=plugin` group of a copy stands for: the user's own value, else the
 * plugin noted (whisker), else `actions` (the only other one REMOTIX locks). */
static char *xfce_copy_group_type(GKeyFile *copy, const char *group)
{
	char *type = g_key_file_get_string(copy, group, "value", NULL);

	if (!type)
		type = g_key_file_get_string(copy, group, "plugin", NULL);
	return type ? type : g_strdup(PLUGIN_ACTIONS);
}

/* Puts back the user's values from ONE copy, if it is there and not yet restored.
 * TRUE if nothing is left to restore in it. */
static gboolean xfce_restore_copy(const char *fpath)
{
	g_autoptr(GKeyFile) copy = g_key_file_new();
	g_autoptr(GPtrArray) done = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GError) mistake = NULL;
	g_auto(GStrv) groups = NULL;
	char *restart[] = { "systemctl", "--user", "try-restart", "xfconfd.service", NULL };
	int total = 0;

	if (!fpath || !g_key_file_load_from_file(copy, fpath, G_KEY_FILE_NONE, NULL) ||
	    g_key_file_get_boolean(copy, "stato", "ripristinato", NULL))
		return TRUE;
	groups = g_key_file_get_groups(copy, NULL);
	for (int i = 0; groups[i]; i++) {
		g_autofree char *channel = NULL;
		g_autofree char *key = NULL;
		g_autofree char *kind = NULL;
		gboolean absent;
		gboolean ok;

		if (groups[i][0] != 'k')
			continue;
		channel = g_key_file_get_string(copy, groups[i], "channel", NULL);
		key = g_key_file_get_string(copy, groups[i], "path", NULL);
		kind = g_key_file_get_string(copy, groups[i], "kind", NULL);
		if (!channel || !key || !kind)
			continue;
		total++;
		absent = g_key_file_get_boolean(copy, groups[i], "absent", NULL);
		if (g_strcmp0(kind, "plugin") == 0) {
			/* ⭐ The plugin's own value (`/plugins/plugin-N` = actions or whiskermenu).
			 *   The lock files no longer define it (D-X3), so the panel writes it in the
			 *   user's file; the copies made before that change may still have been
			 *   taken with the old lock, whose type the panel never wrote — and a plugin
			 *   that is not typed disappears from the user's panel in local.
			 *   ⇒ If the user had it, it goes back;
			 *   if not, and the panel has since filled the channel with its layout, it is
			 *   written as the panel would have — unless the system files already say
			 *   it (then taking the key away is enough); if the channel is still empty,
			 *   nothing. */
			gboolean any = FALSE;
			g_autoptr(GPtrArray) plugins = panel_action_plugins(&any);

			if (!absent || (any && !xfce_system_value(channel, key, FALSE, NULL, NULL))) {
				g_autofree char *type = xfce_copy_group_type(copy, groups[i]);

				ok = xfconf_set(channel, key, "string", type);
			} else {
				ok = xfconf_unset(channel, key);
			}
		} else if (absent) {
			ok = xfconf_unset(channel, key);
		} else if (g_strcmp0(kind, "array") == 0) {
			g_auto(GStrv) values = g_key_file_get_string_list(copy, groups[i], "values",
			                                                 NULL, NULL);

			ok = values && values[0] && xfconf_set_array(channel, key, values);
		} else {
			g_autofree char *value = g_key_file_get_string(copy, groups[i], "value", NULL);

			ok = value && xfconf_set(channel, key, kind, value);
		}
		if (ok)
			g_ptr_array_add(done, g_strdup(groups[i]));
		else
			registro_dice(LOG_SESSION,
			              "⛔ XFCE: %s %s NOT put back as the user had it — it stays "
			              "pending in the copy, I will try again at the next clean-up "
			              "or birth", channel, key);
	}
	/* ⚠ `xfconfd` saves the channel when it stops: without this the file would be
	 *   written a few seconds later, or never if the manager goes first. */
	if (total)
		run(restart);
	if ((int) done->len == total) {
		g_key_file_set_boolean(copy, "stato", "ripristinato", TRUE);
		if (!g_key_file_save_to_file(copy, fpath, &mistake)) {
			registro_dice(LOG_SESSION, "⛔ XFCE: the copy %s NOT marked as restored: %s",
			              fpath, mistake->message);
			return FALSE;
		}
		registro_dice(LOG_SESSION,
		              "⭐ XFCE: the user's %d locked keys put back — their EFFECTIVE values "
		              "are as they were (copy %s, marked as restored).  ⚠ A value equal "
		              "to the system default is not a line of the user's file: xfconfd "
		              "does not write it", total, fpath);
		return TRUE;
	}
	/* ⛔ PARTIAL: the keys put back leave the copy NOW — the next attempt must not
	 *    write them again over what the user will have changed in local. */
	for (guint i = 0; i < done->len; i++)
		g_key_file_remove_group(copy, g_ptr_array_index(done, i), NULL);
	if (g_key_file_save_to_file(copy, fpath, &mistake))
		registro_dice(LOG_SESSION,
		              "⛔ XFCE: %u keys out of %d put back — only the %d that did NOT go "
		              "back stay pending in the copy %s",
		              done->len, total, total - (int) done->len, fpath);
	else
		registro_dice(LOG_SESSION,
		              "⛔ XFCE: %u keys out of %d put back, and the copy %s could NOT be "
		              "rewritten (%s): it stays whole, ALL its keys will be put back again "
		              "at the next attempt",
		              done->len, total, fpath, mistake->message);
	return FALSE;
}

/* Puts back the user's values from the copies not yet restored: the one in RAM
 * first, the one on disk last (see «WHERE THE COPY LIVES»).  Only to be called
 * with NO lock in force (drop-in removed, `xfconfd` restarted).  TRUE if nothing
 * is left to restore. */
static gboolean xfce_restore_keys(void)
{
	g_autofree char *ram = xfce_copy_path(TRUE);
	g_autofree char *disk = xfce_copy_path(FALSE);
	gboolean ram_done = xfce_restore_copy(ram);
	gboolean disk_done = xfce_restore_copy(disk);

	return ram_done && disk_done;
}

/* TRUE if the `xfconfd` that runs still has OUR lock files in memory: it read them when
 * it opened the channel, and a light close removes the drop-in without restarting it.
 * ⛔ Also TRUE when it cannot be told: never write on a guess. */
static gboolean xfconfd_holds_lock(void)
{
	char *show[] = { "systemctl", "--user", "show", "-p", "MainPID", "--value",
		           "xfconfd.service", NULL };
	g_autofree char *answer = ask(show);
	int pid;
	g_autofree char *path = NULL;
	g_autofree char *environ_text = NULL;
	gsize len = 0;

	if (!answer || !*g_strstrip(answer))
		return TRUE;
	if (strcmp(answer, "0") == 0)
		return FALSE; /* not running: the next one starts with the drop-in as it is */
	pid = atoi(answer);
	if (pid <= 0)
		return TRUE;
	path = g_strdup_printf("/proc/%d/environ", pid);
	if (!g_file_get_contents(path, &environ_text, &len, NULL))
		return TRUE;
	for (const char *e = environ_text; e < environ_text + len; e += strlen(e) + 1)
		if (strstr(e, "/remotix/xdg-xfce"))
			return TRUE;
	return FALSE;
}

/* The type of `key` (`/plugins/plugin-<N>`) from a copy not yet restored, or NULL. */
static char *xfce_copy_plugin_type(const char *key)
{
	for (int ram = 0; ram < 2; ram++) {
		g_autofree char *fpath = xfce_copy_path(ram);
		g_autoptr(GKeyFile) copy = g_key_file_new();
		g_auto(GStrv) groups = NULL;

		if (!fpath || !g_key_file_load_from_file(copy, fpath, G_KEY_FILE_NONE, NULL) ||
		    g_key_file_get_boolean(copy, "stato", "ripristinato", NULL))
			continue;
		groups = g_key_file_get_groups(copy, NULL);
		for (int i = 0; groups[i]; i++) {
			g_autofree char *path = g_key_file_get_string(copy, groups[i], "path", NULL);
			g_autofree char *kind = g_key_file_get_string(copy, groups[i], "kind", NULL);

			if (g_strcmp0(path, key) == 0 && g_strcmp0(kind, "plugin") == 0)
				return xfce_copy_group_type(copy, groups[i]);
		}
	}
	return NULL;
}

/* ⭐ D-X3 — every id in a panel's `plugin-ids` must have its `/plugins/plugin-<id>`
 * type: without it the panel asks to remove the plugin and the plugin is gone.  Only what
 * OUR lock can have damaged is repaired: a missing type is written back from a pending
 * copy, else from the standard layout but ONLY if it is a type REMOTIX locks
 * (PLUGIN_ACTIONS, PLUGIN_WHISKER: the number may be another plugin by now); for any other
 * it is NOT guessed.  Never while the lock is in `xfconfd`'s memory (the value would be
 * «equal to the system's» and not written): it waits for the next birth.  Silent when all
 * is well.  One read of the channel (`-l -v`: a plugin with a type has a line, an array
 * is `[1,2,3]`). */
static void xfce_panel_integrity(void)
{
	char *list_cmd[] = { "xfconf-query", "-c", "xfce4-panel", "-l", "-v", NULL };
	g_autofree char *listing = ask(list_cmd);
	g_auto(GStrv) lines = g_strsplit(listing ? listing : "", "\n", -1);
	g_autoptr(GHashTable) typed = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, NULL);
	g_autoptr(GPtrArray) ids = g_ptr_array_new_with_free_func(g_free);
	int held = -1;

	for (int i = 0; lines[i]; i++) {
		g_auto(GStrv) parts = g_strsplit_set(g_strstrip(lines[i]), " \t", 2);
		const char *value = parts[0] && parts[1] ? g_strstrip(parts[1]) : "";

		if (!parts[0])
			continue;
		if (g_str_has_prefix(parts[0], "/plugins/plugin-") && *value)
			g_hash_table_add(typed, g_strdup(parts[0]));
		else if (g_str_has_prefix(parts[0], "/panels/panel-") &&
		         g_str_has_suffix(parts[0], "/plugin-ids") && value[0] == '[') {
			g_auto(GStrv) items = g_strsplit_set(value, "[,]", -1);

			for (int j = 0; items[j]; j++)
				if (*items[j])
					g_ptr_array_add(ids, g_strdup(items[j]));
		}
	}
	for (guint i = 0; i < ids->len; i++) {
		g_autofree char *key = g_strdup_printf("/plugins/plugin-%s",
		                                        (char *) g_ptr_array_index(ids, i));
		g_autofree char *type = NULL;

		if (strspn(key + strlen("/plugins/plugin-"), "0123456789") !=
		        strlen(key + strlen("/plugins/plugin-")) ||
		    g_hash_table_contains(typed, key))
			continue;
		if (held < 0)
			held = xfconfd_holds_lock();
		if (held) {
			registro_dice(LOG_SESSION,
			              "⚠ XFCE: %s has no type but the lock is still in xfconfd's "
			              "memory — not repaired now, at the next birth without it", key);
			continue;
		}
		type = xfce_copy_plugin_type(key);
		if (!type) {
			type = default_plugin_type(key);
			if (type && strcmp(type, PLUGIN_ACTIONS) != 0 && strcmp(type, PLUGIN_WHISKER) != 0)
				g_clear_pointer(&type, g_free);
		}
		if (!type)
			registro_dice(LOG_SESSION,
			              "⛔ XFCE: %s has no type and neither the copy nor the standard "
			              "layout (for the types we lock) knows it — NOT repaired (not "
			              "guessed)", key);
		else if (xfconf_set("xfce4-panel", key, "string", type))
			registro_dice(LOG_SESSION, "⭐ XFCE: %s had no type: put back as «%s»",
			              key, type);
		else
			registro_dice(LOG_SESSION, "⛔ XFCE: %s had no type and «%s» could NOT "
			              "be written back", key, type);
		g_hash_table_add(typed, g_strdup(key));
	}
}

/*
 * ⭐ ONCE, FOR WHOEVER USED 1.5.0 — the old values written in the user's channels.
 *
 * Until 1.5.0 REMOTIX wrote in the USER's channels `LockCommand=/bin/false`,
 * `ShowSuspend/Hibernate/HybridSleep=false`, `dpms-enabled=false`,
 * `inactivity-on-ac/battery=0` and the action button's `items` with `-`.  REMOTIX
 * does not know what was there before (user's decision, 13 Nov 2026): the first time
 * they go back to the standard of XFCE — the key is taken away if it still has OUR
 * value, the `items` go back to `+` only for the entries that are `+` in the
 * standard.  A sign in `~/.local/state/remotix/` says it was done; ⚠ and it comes
 * BEFORE the copy of the locked keys, or the copy would keep our old values.
 * ⚠ Declared: it runs ALSO for a user who never used 1.5.0 — REMOTIX cannot tell.  A
 *   `-lock-screen` (or `LockCommand=/bin/false`, `dpms-enabled=false`…) they chose on
 *   purpose goes back to the standard, ONCE: it is inside the user's decision of
 *   13 Nov 2026, and it is to be said in the release notes.
 */
struct xfce_old_key {
	const char *channel;
	const char *key;
	const char *value;
};

static const struct xfce_old_key XFCE_OLD_KEYS[] = {
	{ "xfce4-session", "/general/LockCommand", "/bin/false" },
	{ "xfce4-session", "/shutdown/ShowSuspend", "false" },
	{ "xfce4-session", "/shutdown/ShowHibernate", "false" },
	{ "xfce4-session", "/shutdown/ShowHybridSleep", "false" },
	{ "xfce4-power-manager", "/xfce4-power-manager/dpms-enabled", "false" },
	{ "xfce4-power-manager", "/xfce4-power-manager/inactivity-on-ac", "0" },
	{ "xfce4-power-manager", "/xfce4-power-manager/inactivity-on-battery", "0" },
	{ NULL, NULL, NULL },
};

static void xfce_migrate_old(void)
{
	g_autofree char *mark = xfce_state_file(XFCE_OLD_MARK_NAME);
	g_autoptr(GPtrArray) plugins = NULL;
	g_autoptr(GError) mistake = NULL;
	gboolean any = FALSE;
	int taken = 0, restored = 0;

	if (!mark || g_file_test(mark, G_FILE_TEST_EXISTS))
		return;
	for (int i = 0; XFCE_OLD_KEYS[i].key; i++) {
		g_autofree char *now = NULL;

		if (xfconf_get(XFCE_OLD_KEYS[i].channel, XFCE_OLD_KEYS[i].key, FALSE, &now, NULL) &&
		    g_strcmp0(now, XFCE_OLD_KEYS[i].value) == 0 &&
		    xfconf_unset(XFCE_OLD_KEYS[i].channel, XFCE_OLD_KEYS[i].key))
			taken++;
	}
	plugins = panel_action_plugins(&any);
	for (guint i = 0; i < plugins->len; i++) {
		g_autofree char *key = g_strdup_printf("%s/items", (char *) g_ptr_array_index(plugins, i));
		g_auto(GStrv) items = NULL;
		gboolean changed = FALSE;

		if (!xfconf_get("xfce4-panel", key, TRUE, NULL, &items))
			continue;
		for (int j = 0; items[j]; j++) {
			g_autofree char *standard = NULL;

			if (items[j][0] != '-' || !g_strv_contains(ACTIONS_TO_REMOVE, items[j] + 1))
				continue;
			standard = g_strdup_printf("+%s", items[j] + 1);
			if (g_strv_contains(DEFAULT_ACTIONS, standard)) {
				g_free(items[j]);
				items[j] = g_steal_pointer(&standard);
				changed = TRUE;
			}
		}
		if (changed && xfconf_set_array("xfce4-panel", key, items))
			restored++;
	}
	if (!g_file_set_contents(mark, "1.5.0 values put back to the XFCE standard\n", -1,
	                         &mistake))
		registro_dice(LOG_SESSION, "⛔ XFCE: the sign %s NOT written (%s): at the next birth "
		              "it will be done again", mark, mistake->message);
	registro_dice(LOG_SESSION,
	              "⭐ XFCE, ONCE: the values of the old 1.5.0 taken away from the user's "
	              "channels — %d keys, %d action buttons put back to the standard", taken,
	              restored);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ 13 Nov 2026 — THE USER'S LXQt SETTINGS STAY HIS (PIANO-13nov §3).
 *
 * REMOTIX no longer writes ANYTHING permanent into the user's LXQt files: not the
 * panel (it is the real one, with the fancymenu), not `lock_command_wayland`, not
 * `lxqt-powermanagement.conf`.  What the remote session must not do — suspend,
 * reboot, power off, lock — is imposed ONLY inside the session:
 *   · «Leave» in the fancymenu, and the menu entries, launch `lxqt-leave` by
 *     NAME, through the PATH: a folder of the session at the head of the PATH
 *     (`$XDG_RUNTIME_DIR/remotix/bin-lxqt`) holds a `lxqt-leave` that turns
 *     every request (even the dialog, even `--lockscreen`) into `--logout`;
 *   · `lxqt-powermanagement` does not run: the autostart entries launch it by NAME, and
 *     the same folder holds a `lxqt-powermanagement` that does nothing;
 *   · an X11 composition manager (`LXQT_X11_COMPOSITORS`) does not run either: Lubuntu's
 *     `picom.desktop` is a MODULE (`X-LXQt-Module=true`) with no `X-LXQt-X11-Only`, and the
 *     remote session has no X server it can compose (labwc is the compositor): `picom` dies, `lxqt-session` restarts it until the limit
 *     (`lxqtmodman.cpp`, `MAX_CRASHES_PER_APP`) and then shows «X Compositor crashed too
 *     many times».  The same folder holds a `picom` that exits 0 (a module that exits 0 is
 *     NOT restarted), and the compositor the session has — labwc — is already there;
 *   · the six «Leave» menu entries stay hidden, in the session data folder
 *     (`settings_lxqt()`), because a «Suspend» that logs out would be a lie.
 *   [M] tried on the lxqt-panel 2.1.4 box: the button and the entries go through
 *   OUR `lxqt-leave`; a user's autostart entry by name ends in OUR command too.
 *
 * ⭐ 14 Nov 2026 — THE TWO COMMANDS CHECK WHERE THEY RUN.  `[M]` Arch: once, after «Exit»,
 *   PATH/XDG_* stayed in the user manager; a LOCAL session of the same user would have
 *   inherited our folder at the head of its PATH — a «Leave» that only logs out and no
 *   power management, at the monitor.  ⇒ Each script first asks whether it runs INSIDE the
 *   remote session: its own cgroup (`/proc/self/cgroup`, logind's `session-N.scope`) and
 *   `loginctl show-session N -p Service --value` = `LXQT_PAM_SERVICE`.  In EVERY other case
 *   (no scope, loginctl missing or failing, another service) it is the real program:
 *   `exec <absolute path> "$@"`.
 *   And the session's autostart `lxqt-powermanagement.desktop` with `Hidden=true` is GONE:
 *   it travelled with `XDG_CONFIG_DIRS`, and in a local session it would have switched the
 *   power management off with no check possible.  Nothing replaces it: the system's entry
 *   is `Exec=lxqt-powermanagement`, by name (`[M]` Debian 13 and Arch), so it already ends
 *   in our command; and a session entry never wins over one of the user's.
 * ⭐ 18 Nov 2026 — ONE session autostart entry is back, for another reason: `lubuntu-update`
 *   (`LXQT_SHARED_SERVER_PROGRAMS`).  The system's entries name it by ABSOLUTE path, so the
 *   PATH cannot catch it; our entry of the same file name covers them, and it is NOT
 *   `Hidden=true`: it starts the program by NAME, i.e. our self-checking script, which in a
 *   local session `exec`s the real one.
 * ⭐ 19 Nov 2026 — and ONE MORE, with `Hidden=true` and no check: `blueman.desktop`
 *   (`SESSION_NOT_IN_REMOTE_AUTOSTART`, `session_autostart_cover()`), see there.
 * ⚠ DECLARED: a user's autostart entry with the ABSOLUTE path of the real program starts
 *   it in the remote session too (it was so with `Hidden=true` as well: the user's folder
 *   comes first).  We do not write into the user's files; the real ban on suspending lives
 *   in polkit and `sleep.conf`.  It is said in the log at birth.
 */
/* the PAM service that opens the remote session: `pam_start()` in `child.c`,
 * `SERVICE_PAM` in `authentication.c`, `FOUND_AGAIN_PAM_SERVICE` in `rediscover.h` */
#define LXQT_PAM_SERVICE "remotix"

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

/* ------------------------------------------------------------------------- */
/*
 * ⭐ THE SESSION'S COMMANDS: a folder at the head of the session's PATH.
 *
 * `lxqt-leave`: the real one is looked up in the server's PATH (which does not hold
 * our folder) and called by ABSOLUTE path, with `--logout` whatever it was
 * asked (no argument = the dialog, `--lockscreen`, `--suspend`, …).  ⛔ NEVER
 * by name: it would call itself.
 * `lxqt-powermanagement`: exits 0 and writes a line in the system log, if
 * `logger` is there.
 * The X11 composition managers (`LXQT_X11_COMPOSITORS`): same as `lxqt-powermanagement`, and
 * a line on stderr for whoever starts one by hand.
 * ⭐ 14 Nov 2026: all of them do so ONLY inside the remote session (`LXQT_SCRIPT_HEAD`); anywhere
 * else they `exec` the real program with the arguments they were given.
 * The scripts are rewritten at every birth (atomic), mode 0755, in a folder 0700 of
 * `XDG_RUNTIME_DIR`: nothing of the user's is touched.
 */
static gboolean write_session_script(const char *folder, const char *name, const char *body)
{
	g_autofree char *file = g_build_filename(folder, name, NULL);
	g_autoptr(GError) mistake = NULL;

	if (!g_file_set_contents(file, body, -1, &mistake)) {
		registro_dice(LOG_SESSION, "⛔ LXQt: %s NOT written (%s)", file, mistake->message);
		return FALSE;
	}
	if (g_chmod(file, 0755) != 0) {
		registro_dice(LOG_SESSION, "⛔ LXQt: %s: chmod failed (%s)", file,
		              g_strerror(errno));
		return FALSE;
	}
	return g_file_test(file, G_FILE_TEST_IS_EXECUTABLE);
}

/*
 * The head of the session's scripts: `%s` = what the script is for (a comment), the real program
 * (shell-quoted), the `loginctl` command (shell-quoted, with `timeout 3` in front if there
 * is one: a logind that does not answer must not hang «Leave»; a timeout = not remote = the
 * real program).  After it, the script is INSIDE the remote session.
 * ⚠ `/proc/self/cgroup` is read by `sed`, a child in the same cgroup; the scope is taken
 *   only where logind puts it, `user-UID.slice/session-N.scope`; the first line that has it
 *   (cgroup v2 has one line only).
 */
#define LXQT_SCRIPT_HEAD \
	"#!/bin/sh\n" \
	"# REMOTIX: %s\n" \
	"# ONLY inside the remote session (a logind session of the PAM service «" \
	LXQT_PAM_SERVICE "»);\n" \
	"# anywhere else this is the real program.\n" \
	"real=%s\n" \
	"n=$(sed -n '/\\/user-[0-9]*\\.slice\\/session-[^/.]*\\.scope/" \
	"{s|.*/user-[0-9]*\\.slice/session-\\([^/.]*\\)\\.scope.*|\\1|p;q;}' " \
	"/proc/self/cgroup 2>/dev/null)\n" \
	"svc=\n" \
	"[ -n \"$n\" ] && svc=$(%s show-session \"$n\" -p Service --value 2>/dev/null)\n" \
	"[ \"$svc\" = " LXQT_PAM_SERVICE " ] || exec \"$real\" \"$@\"\n"

/* the real `name`, by absolute path: never the one in our own folder */
static char *lxqt_real_program(const char *name, const char *bin)
{
	char *real = g_find_program_in_path(name);

	/* ⛔ the one in our own folder is not the real one */
	if (real && g_str_has_prefix(real, bin))
		g_clear_pointer(&real, g_free);
	return real ? real : g_build_filename("/usr/bin", name, NULL);
}

/* ⚠ DECLARED (the box above `LXQT_PAM_SERVICE`): a user's autostart entry that names the
 *   real `lxqt-powermanagement` by absolute path starts it in the remote session too.
 *   Read only: it is said, nothing is touched. */
static void lxqt_user_autostart_warn(void)
{
	g_autofree char *folder = g_build_filename(g_get_user_config_dir(), "autostart", NULL);
	g_autoptr(GDir) d = g_dir_open(folder, 0, NULL);
	const char *f;

	while (d && (f = g_dir_read_name(d))) {
		g_autofree char *file = NULL;
		g_autofree char *exec = NULL;
		g_autofree char *base = NULL;
		g_autoptr(GKeyFile) k = g_key_file_new();
		g_auto(GStrv) words = NULL;

		if (!g_str_has_suffix(f, ".desktop"))
			continue;
		file = g_build_filename(folder, f, NULL);
		if (!g_key_file_load_from_file(k, file, G_KEY_FILE_NONE, NULL) ||
		    g_key_file_get_boolean(k, "Desktop Entry", "Hidden", NULL))
			continue;
		exec = g_key_file_get_string(k, "Desktop Entry", "Exec", NULL);
		if (!exec || !g_shell_parse_argv(exec, NULL, &words, NULL) || !words[0] ||
		    !g_path_is_absolute(words[0]))
			continue;
		base = g_path_get_basename(words[0]);
		if (strcmp(base, "lxqt-powermanagement") == 0)
			registro_dice(LOG_SESSION,
			              "⚠ LXQt, DECLARED: the user's autostart %s starts %s by ABSOLUTE "
			              "path — it will run in the remote session too (we do not write "
			              "into the user's files; suspend stays forbidden by polkit and "
			              "sleep.conf)",
			              file, words[0]);
	}
}

/* ⭐ The ONE place that names programs: the X11 composition managers.  Neither the desktop's
 *   keys nor the program can tell us «this needs X»: `lxqt-session` skips only entries marked
 *   `X-LXQt-X11-Only`, and Lubuntu's picom is not marked.  A composition manager has one
 *   role, which cannot exist in the remote session (there is no X server it can compose:
 *   labwc is the compositor): a short list of that ROLE, kept here and nowhere else. */
static const char *const LXQT_X11_COMPOSITORS[] = { "picom", "compton", "xcompmgr", NULL };

/* ⭐ 18 Nov 2026 — the programs that do not belong in a SHARED server: they decide «am I
 *   already running?» by looking at the processes of ALL users, so while one user has the
 *   program alive every other user's copy exits 1, `lxqt-session` restarts it five times and
 *   shows «… crashed too many times».  Lubuntu's `lubuntu-update` does it (`ps axo comm |
 *   grep lubuntu-update`); its purpose, installing updates, also asks for a password window,
 *   which a remote session must not show.  Same recipe as the composition managers (a script
 *   of the same name in the session's PATH) PLUS the system's autostart entry that names the
 *   program by ABSOLUTE path, which the PATH cannot catch: an entry of the same file name in
 *   the session's autostart folder (first in `XDG_CONFIG_DIRS`) covers the system's. */
static const struct {
	const char *program;
	const char *autostart; /* the system's autostart file name, which ours covers */
} LXQT_SHARED_SERVER_PROGRAMS[] = {
	{ "lubuntu-update", "lubuntu-update-autostart.desktop" },
	{ NULL, NULL },
};

static void lxqt_session_commands(void)
{
	g_autofree char *bin = lxqt_session_bin_folder();
	g_autofree char *cfg = lxqt_session_config_folder();
	g_autofree char *autostart_dir = cfg ? g_build_filename(cfg, "autostart", NULL) : NULL;
	g_autofree char *startup = autostart_dir
	                                   ? g_build_filename(autostart_dir,
	                                                      "lxqt-powermanagement.desktop", NULL)
	                                   : NULL;
	g_autofree char *real = NULL;
	g_autofree char *real_power = NULL;
	g_autofree char *loginctl = g_find_program_in_path("loginctl");
	g_autofree char *leave = NULL;
	g_autofree char *power = NULL;
	g_autofree char *quoted = NULL;
	g_autofree char *quoted_power = NULL;
	g_autofree char *quoted_loginctl = NULL;
	g_autofree char *timeout = g_find_program_in_path("timeout");
	g_autoptr(GError) mistake = NULL;
	gboolean ok_leave, ok_power, ok_startup, ok_compositors = TRUE, ok_shared = TRUE;
	gboolean ok_cover;
	int compositors = 0, shared = 0;

	if (!bin || !autostart_dir) {
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: without XDG_RUNTIME_DIR there is no session folder — "
		              "«Leave» and lxqt-powermanagement stay as the desktop has them");
		return;
	}
	real = lxqt_real_program("lxqt-leave", bin);
	real_power = lxqt_real_program("lxqt-powermanagement", bin);
	quoted = g_shell_quote(real);
	quoted_power = g_shell_quote(real_power);
	/* ⚠ without `loginctl` the scripts are always the real program: said below */
	quoted_loginctl = g_shell_quote(loginctl ? loginctl : "loginctl");
	if (timeout) {
		g_autofree char *quoted_timeout = g_shell_quote(timeout);
		char *with = g_strdup_printf("%s 3 %s", quoted_timeout, quoted_loginctl);

		g_free(quoted_loginctl);
		quoted_loginctl = with;
	} else {
		registro_dice(LOG_SESSION,
		              "⚠ LXQt, DECLARED: `timeout` is not in the PATH — the session's "
		              "commands ask `loginctl` without a limit: with a logind that does "
		              "not answer, «Leave» waits for it");
	}
	leave = g_strdup_printf(LXQT_SCRIPT_HEAD
	                        "exec \"$real\" --logout\n",
	                        "in the remote session «Leave» only logs out", quoted,
	                        quoted_loginctl);
	power = g_strdup_printf(LXQT_SCRIPT_HEAD
	                        "command -v logger >/dev/null 2>&1 &&\n"
	                        "\tlogger -t remotix \"lxqt-powermanagement: not started in the "
	                        "remote session\"\n"
	                        "exit 0\n",
	                        "no power management in the remote session", quoted_power,
	                        quoted_loginctl);
	if (g_mkdir_with_parents(bin, 0700) != 0 || g_mkdir_with_parents(autostart_dir, 0700) != 0) {
		registro_dice(LOG_SESSION, "⛔ LXQt: %s cannot be created (%s)", bin,
		              g_strerror(errno));
		return;
	}
	ok_leave = write_session_script(bin, "lxqt-leave", leave);
	ok_power = write_session_script(bin, "lxqt-powermanagement", power);
	/* ⭐ 18 Nov 2026: the X11 composition managers that are installed — same recipe */
	for (int i = 0; LXQT_X11_COMPOSITORS[i]; i++) {
		g_autofree char *its = lxqt_real_program(LXQT_X11_COMPOSITORS[i], bin);
		g_autofree char *quoted_its = NULL;
		g_autofree char *shim = NULL;

		if (!g_file_test(its, G_FILE_TEST_IS_EXECUTABLE)) {
			/* not (or no longer) installed: OUR script of an earlier birth must not
			 * stay, or outside the remote session the name would be «not found» */
			g_autofree char *ours = g_build_filename(bin, LXQT_X11_COMPOSITORS[i], NULL);

			if (g_file_test(ours, G_FILE_TEST_EXISTS))
				g_unlink(ours);
			continue;
		}
		quoted_its = g_shell_quote(its);
		shim = g_strdup_printf(LXQT_SCRIPT_HEAD
		                       "command -v logger >/dev/null 2>&1 &&\n"
		                       "\tlogger -t remotix \"%s: an X11 composition manager, not "
		                       "started in the remote session (labwc composes)\"\n"
		                       "echo \"%s: not started in the remote session (REMOTIX: labwc "
		                       "is the compositor)\" >&2\n"
		                       "exit 0\n",
		                       "no X11 composition manager in the remote session", quoted_its,
		                       quoted_loginctl, LXQT_X11_COMPOSITORS[i],
		                       LXQT_X11_COMPOSITORS[i]);
		if (write_session_script(bin, LXQT_X11_COMPOSITORS[i], shim))
			compositors++;
		else
			ok_compositors = FALSE;
	}
	/* ⭐ 18 Nov 2026: the programs that count the processes of every user — same script, and
	 *   the autostart entry that covers the system's (only if the program and the system's
	 *   entry are there: otherwise nothing is written, and what an earlier birth left goes) */
	for (int i = 0; LXQT_SHARED_SERVER_PROGRAMS[i].program; i++) {
		const char *name = LXQT_SHARED_SERVER_PROGRAMS[i].program;
		g_autofree char *its = lxqt_real_program(name, bin);
		g_autofree char *ours = g_build_filename(bin, name, NULL);
		g_autofree char *entry = g_build_filename(autostart_dir,
		                                          LXQT_SHARED_SERVER_PROGRAMS[i].autostart,
		                                          NULL);
		g_autofree char *quoted_its = NULL;
		g_autofree char *shim = NULL;
		g_autofree char *text = NULL;
		g_autofree char *old_entry = NULL;
		gboolean ours_ok;

		if (!g_file_test(its, G_FILE_TEST_IS_EXECUTABLE) ||
		    !system_autostart_exists(LXQT_SHARED_SERVER_PROGRAMS[i].autostart)) {
			/* not (or no longer) installed: nothing of ours stays — and only OURS goes */
			if (g_file_test(ours, G_FILE_TEST_EXISTS))
				g_unlink(ours);
			if (g_file_get_contents(entry, &old_entry, NULL, NULL) &&
			    strstr(old_entry, "X-REMOTIX"))
				g_unlink(entry);
			continue;
		}
		quoted_its = g_shell_quote(its);
		shim = g_strdup_printf(LXQT_SCRIPT_HEAD
		                       "command -v logger >/dev/null 2>&1 &&\n"
		                       "\tlogger -t remotix \"%s: not started in the remote session "
		                       "(it counts the processes of ALL users)\"\n"
		                       "exit 0\n",
		                       "no program that counts every user's processes in the remote "
		                       "session",
		                       quoted_its, quoted_loginctl, name);
		/* by NAME, through the PATH: our script; a module that exits 0 is not restarted */
		text = g_strdup_printf("[Desktop Entry]\nType=Application\nName=%s\nExec=%s\n"
		                       "X-LXQt-Module=true\n"
		                       "# X-REMOTIX: covers the system's entry of the same name\n",
		                       name, name);
		ours_ok = write_session_script(bin, name, shim) &&
		          g_file_set_contents(entry, text, -1, &mistake);
		if (ours_ok)
			shared++;
		else {
			ok_shared = FALSE;
			registro_dice(LOG_SESSION, "⛔ LXQt: the cover for %s is NOT in place (%s)", name,
			              mistake ? mistake->message : g_strerror(errno));
		}
		g_clear_error(&mistake);
	}
	/* ⭐ 19 Nov 2026: the system's autostart entries a remote session must not start (blueman) */
	ok_cover = session_autostart_cover(autostart_dir, "LXQt");
	/* ⭐ 13 Nov 2026: the 1.5.0 leftover — `xdg-lxqt/autostart/lxqt-panel.desktop` with our
	 *   `--configfile` — would start the OLD session panel: it is overwritten with the normal
	 *   start (the system's own file, or the plain command if there is none) */
	{
		g_autofree char *old_panel = g_build_filename(autostart_dir, "lxqt-panel.desktop",
		                                              NULL);
		g_autofree char *old_text = NULL;
		g_autofree char *system_text = NULL;
		const char *normal = "[Desktop Entry]\nType=Application\nName=Panel\n"
		                     "TryExec=lxqt-panel\nExec=lxqt-panel\nOnlyShowIn=LXQt;\n"
		                     "X-LXQt-Module=true\n";

		if (g_file_get_contents(old_panel, &old_text, NULL, NULL) &&
		    strstr(old_text, "X-REMOTIX")) {
			if (g_file_get_contents("/etc/xdg/autostart/lxqt-panel.desktop", &system_text,
			                        NULL, NULL))
				normal = system_text;
			if (g_file_set_contents(old_panel, normal, -1, &mistake))
				registro_dice(LOG_SESSION,
				              "⭐ LXQt: %s was REMOTIX's 1.5.0 leftover (the panel with "
				              "--configfile): OVERWRITTEN with the normal start of the panel",
				              old_panel);
			else
				registro_dice(LOG_SESSION,
				              "⛔ LXQt: %s (1.5.0 leftover) NOT overwritten (%s): the "
				              "session would start the OLD panel",
				              old_panel, mistake->message);
			g_clear_error(&mistake);
		}
	}
	/* ⭐ 14 Nov 2026: the session's autostart with `Hidden=true` is no longer written (the
	 *    box above `LXQT_PAM_SERVICE`), and the one a previous birth left in OUR folder
	 *    is taken away — only if it is ours */
	{
		g_autofree char *old_text = NULL;

		ok_startup = TRUE;
		if (g_file_get_contents(startup, &old_text, NULL, NULL) &&
		    strstr(old_text, "X-REMOTIX")) {
			ok_startup = g_unlink(startup) == 0;
			registro_dice(LOG_SESSION,
			              ok_startup ? "⭐ LXQt: %s (our old Hidden=true autostart) REMOVED%s"
			                         : "⛔ LXQt: %s (our old Hidden=true autostart) NOT "
			                           "removed (%s): a local session that inherited "
			                           "XDG_CONFIG_DIRS would have no power management",
			              startup, ok_startup ? "" : g_strerror(errno));
		}
	}
	if (!loginctl)
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: `loginctl` is not in the PATH — the session's commands cannot "
		              "tell the remote session from a local one, and so they are ALWAYS the "
		              "real programs: «Leave» offers everything (suspend, reboot and power "
		              "off stay forbidden by polkit)");
	lxqt_user_autostart_warn();
	if (ok_leave && ok_power && ok_startup && ok_compositors && ok_shared && ok_cover)
		registro_dice(LOG_SESSION,
		              "⭐ LXQt: %s: lxqt-leave (→ %s --logout), lxqt-powermanagement "
		              "(does nothing; the real one is %s), %d X11 composition manager(s) "
		              "and %d program(s) that count every user's processes (do nothing; "
		              "their autostart entry is covered by one of the session's) "
		              "at the head of the session's PATH — "
		              "ONLY inside a logind session of the PAM service «" LXQT_PAM_SERVICE
		              "», anywhere else they are the real programs; the user's files are "
		              "not touched",
		              bin, real, real_power, compositors, shared);
	else
		registro_dice(LOG_SESSION,
		              "⛔ LXQt: session commands NOT all in place (lxqt-leave %s, "
		              "lxqt-powermanagement %s, old autostart %s, composition managers %s, "
		              "shared-server programs %s)",
		              ok_leave ? "ok" : "KO", ok_power ? "ok" : "KO",
		              ok_startup ? "removed" : "NOT removed", ok_compositors ? "ok" : "KO",
		              ok_shared ? "ok" : "KO");
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐ ONE-TIME RESTORE of what REMOTIX 1.5.0 and earlier wrote into the user's files.
 *
 * The decision of 13 Nov 2026 (PIANO-13nov §3): the user finds everything as it was.
 * Done ONCE (the mark is `~/.local/state/remotix/lxqt-restored`), BEFORE the birth,
 * and only what is surely ours:
 *   · `lock_command_wayland=true` out of `lxqt.conf` [Screensaver] and of
 *     `session.conf` — only if it is `true`: a `swaylock` is the user's;
 *   · `enableIdlenessWatcher=false` out of `lxqt-powermanagement.conf` — only if the
 *     file holds nothing but REMOTIX's keys (`__userfile__`, `enableIdlenessWatcher`,
 *     `runCheckLevel`): otherwise the user also set something there, and we cannot know
 *     whose the `false` is;
 *   · `panel.conf`: the group `fancymenu` with `type=mainmenu` goes back to `fancymenu`;
 *   · REMOTIX's old menu entries in `~/.local/share/applications` (they hid the
 *     «Leave» entries): DELETED — by the user's explicit decision of 13 Nov 2026, and only
 *     when the file holds NOTHING but REMOTIX's lines (`[Desktop Entry]`, Type, Name,
 *     Hidden, NoDisplay, X-REMOTIX, comments, blank lines).  With any other line it is left
 *     as it is and the log says so.  Every deleted file is in the log.
 *   · the old session panel's autostart (`lxqt_session_commands()`) and the old
 *     `$XDG_RUNTIME_DIR/remotix/panel-lxqt.conf`: the autostart is overwritten with the
 *     normal one; the conf is LEFT (nobody reads it any more, and it dies with the runtime).
 * A file that cannot be read is NOT rewritten (as `write_qt_key()` did).
 */
static gboolean remove_qt_key(const char *file, const char *group, const char *key,
                              const char *only_if)
{
	g_autoptr(GKeyFile) keys = g_key_file_new();
	g_autoptr(GError) mistake = NULL;
	g_autofree char *value = NULL;

	if (!g_file_test(file, G_FILE_TEST_EXISTS))
		return FALSE;
	if (!read_ini_qt(keys, file, &mistake)) {
		registro_dice(LOG_SESSION,
		              "⚠ LXQt: %s exists but I cannot read it (%s) — I do NOT rewrite it",
		              file, mistake->message);
		return FALSE;
	}
	value = g_key_file_get_value(keys, group, key, NULL);
	if (!value || (only_if && g_strcmp0(value, only_if) != 0))
		return FALSE;
	g_key_file_remove_key(keys, group, key, NULL);
	if (!g_key_file_save_to_file(keys, file, &mistake)) {
		registro_dice(LOG_SESSION, "⛔ LXQt: %s NOT rewritten (%s)", file, mistake->message);
		return FALSE;
	}
	registro_dice(LOG_SESSION, "⭐ LXQt: %s [%s] %s=%s taken out (REMOTIX's old value)",
	              file, group, key, value);
	return TRUE;
}

static gboolean only_our_keys(const char *file)
{
	static const char *const OURS[] = { "__userfile__", "enableIdlenessWatcher",
		                                 "runCheckLevel", NULL };
	g_autoptr(GKeyFile) keys = g_key_file_new();
	g_auto(GStrv) groups = NULL;

	if (!read_ini_qt(keys, file, NULL))
		return FALSE;
	groups = g_key_file_get_groups(keys, NULL);
	for (int g = 0; groups[g]; g++) {
		g_auto(GStrv) names = g_key_file_get_keys(keys, groups[g], NULL, NULL);

		if (g_strcmp0(groups[g], "General") != 0 && names && names[0])
			return FALSE;
		for (int k = 0; names && names[k]; k++)
			if (!g_strv_contains(OURS, names[k]))
				return FALSE;
	}
	return TRUE;
}

/*
 * REMOTIX's old menu entry? 0 = not ours (no X-REMOTIX, or unreadable), 1 = ours and ONLY ours:
 * every non-blank, non-comment line is `[Desktop Entry]` or Type/Name/Hidden/NoDisplay/
 * X-REMOTIX, 2 = it has X-REMOTIX but some other line too (the user's).
 */
static int old_entry_verdict(const char *file)
{
	static const char *const OURS[] = { "Type", "Name", "Hidden", "NoDisplay", "X-REMOTIX", NULL };
	g_autofree char *text = NULL;
	g_auto(GStrv) lines = NULL;
	gboolean marked = FALSE;

	if (!g_file_get_contents(file, &text, NULL, NULL))
		return 0;
	lines = g_strsplit(text, "\n", -1);
	for (int i = 0; lines[i]; i++) {
		g_autofree char *line = g_strstrip(g_strdup(lines[i]));
		g_autofree char *key = NULL;
		char *equals;

		if (!*line || *line == '#' || g_strcmp0(line, "[Desktop Entry]") == 0)
			continue;
		equals = strchr(line, '=');
		if (!equals)
			return marked || strstr(text, "X-REMOTIX") ? 2 : 0;
		key = g_strstrip(g_strndup(line, (gsize) (equals - line)));
		if (g_strcmp0(key, "X-REMOTIX") == 0)
			marked = TRUE;
		else if (!g_strv_contains(OURS, key))
			return strstr(text, "X-REMOTIX") ? 2 : 0;
	}
	return marked ? 1 : 0;
}

static void restore_user_settings_lxqt(void)
{
	g_autofree char *state = g_build_filename(g_get_user_state_dir(), "remotix", NULL);
	g_autofree char *mark = g_build_filename(state, "lxqt-restored", NULL);
	g_autofree char *folder = g_build_filename(g_get_home_dir(), ".config", "lxqt", NULL);
	g_autofree char *lxqt = g_build_filename(folder, "lxqt.conf", NULL);
	g_autofree char *session = g_build_filename(folder, "session.conf", NULL);
	g_autofree char *power = g_build_filename(folder, "lxqt-powermanagement.conf", NULL);
	g_autofree char *panel = g_build_filename(folder, "panel.conf", NULL);
	g_autofree char *applications = g_build_filename(g_get_home_dir(), ".local", "share",
	                                                 "applications", NULL);
	g_autoptr(GKeyFile) panel_keys = g_key_file_new();
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GDir) dir = NULL;
	const char *name;

	if (g_file_test(mark, G_FILE_TEST_EXISTS))
		return;

	remove_qt_key(lxqt, "Screensaver", "lock_command_wayland", "true");
	remove_qt_key(session, "General", "lock_command_wayland", "true");
	if (g_file_test(power, G_FILE_TEST_EXISTS) && only_our_keys(power))
		remove_qt_key(power, "General", "enableIdlenessWatcher", "false");

	if (g_file_test(panel, G_FILE_TEST_EXISTS) && read_ini_qt(panel_keys, panel, NULL)) {
		g_autofree char *type = g_key_file_get_value(panel_keys, "fancymenu", "type", NULL);

		if (g_strcmp0(type, "mainmenu") == 0) {
			g_key_file_set_value(panel_keys, "fancymenu", "type", "fancymenu");
			if (g_key_file_save_to_file(panel_keys, panel, &mistake))
				registro_dice(LOG_SESSION,
				              "⭐ LXQt: %s [fancymenu] type mainmenu → fancymenu "
				              "(REMOTIX's old value)",
				              panel);
			else
				registro_dice(LOG_SESSION, "⛔ LXQt: %s NOT rewritten (%s)", panel,
				              mistake->message);
		}
	}

	dir = g_dir_open(applications, 0, NULL);
	while (dir && (name = g_dir_read_name(dir))) {
		g_autofree char *entry = g_build_filename(applications, name, NULL);
		GStatBuf what = { 0 };

		if (!g_str_has_suffix(name, ".desktop") || g_lstat(entry, &what) != 0 ||
		    !S_ISREG(what.st_mode))
			continue;
		switch (old_entry_verdict(entry)) {
		case 1:
			if (g_unlink(entry) == 0)
				registro_dice(LOG_SESSION,
				              "⭐ LXQt: %s DELETED — it held only REMOTIX's lines "
				              "(Type, Name, Hidden, NoDisplay, X-REMOTIX): REMOTIX's old "
				              "entry, by the user's decision of 13 Nov 2026",
				              entry);
			else
				registro_dice(LOG_SESSION, "⛔ LXQt: %s NOT deleted (%s)", entry,
				              g_strerror(errno));
			break;
		case 2:
			registro_dice(LOG_SESSION,
			              "⚠ LXQt: %s has X-REMOTIX but ALSO lines that are not ours: "
			              "NOT deleted and not touched (it stays as it is)",
			              entry);
			break;
		default:
			break;
		}
	}

	/* the mark, even if something could not be done: it is a ONE-TIME restore */
	if (g_mkdir_with_parents(state, 0700) == 0 &&
	    g_file_set_contents(mark, "restored\n", -1, NULL))
		registro_dice(LOG_SESSION, "⭐ LXQt: one-time restore done (%s)", mark);
	else
		registro_dice(LOG_SESSION,
		              "⚠ LXQt: restore done but %s cannot be written: it will be repeated "
		              "at the next birth (harmless)",
		              mark);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ THE LXQt SETTINGS OF THE SESSION (13 Nov 2026: nothing is written into the user's
 *     files any more; the old `enableIdlenessWatcher`/`runCheckLevel`, the lock
 *     command and the session panel are gone — see `lxqt_session_commands()`).
 *
 * ⚠ `lxqt-powermanagement` is the one that watches idleness: it does not run in the
 *   session (a command that does nothing at the head of the PATH), so there is no
 *   idleness to switch off, and the user's file keeps whatever the user set.
 *
 * And the things that are NOT written, each with its reason:
 *   · `compositor=` in `session.conf` — ⛔ `[R]` the wizard for an empty `compositor`
 *     is launched by THE upstream SCRIPT (`labwc -S lxqt-config-session`),
 *     not by `lxqt-session`, which in 2.1.1 does not read that key
 *     (`lxqtmodman.cpp`).  With our launcher the key has no readers;
 *   · the lock command — the lock is not offered: `lxqt-leave` is ours;
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
	orphan_profile_pcmanfm_lxqt();
	restore_user_settings_lxqt();
	lxqt_session_commands();
	registro_dice(LOG_SESSION,
	              "LXQt: idleness and lock are not written: lxqt-powermanagement does not "
	              "run in the session, and «Leave» only logs out (PIANO-13nov §3)");

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
	 *     (`compose_environment()`): they hold for the session we need, and
	 *     the user at the monitor has their whole menu.
	 * ⚠ The price: a user file with the same id in
	 *   `~/.local/share/applications` comes FIRST and wins.  It is checked and
	 *   said (the entry stays).  One with `X-REMOTIX` is a leftover of earlier
	 *   versions: it hides all the same, and is not touched.
	 *
	 * ⭐ 13 Nov 2026 — THESE SIX ARE STILL HIDDEN, though now harmless: the entries
	 *    (and the fixed «Leave» button of the fancymenu, `[R]` lxqt-panel 2.1.4
	 *    `lxqtfancymenuwindow.cpp:165-169, 315-318`) launch `lxqt-leave` by name,
	 *    and the session's one (`lxqt_session_commands()`) turns every request into
	 *    `--logout`.  Hidden they stay because a «Suspend» or «Lock screen» that
	 *    logs the user out would be a lie, and the test of the rule (15-f031b)
	 *    asks for NO entry to suspend, reboot, power off or lock.
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
			return;
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
			/* ⚠ `NoDisplay` too: the old X-REMOTIX stub of the user, once its
			 *   `Hidden` is taken out (`restore_user_settings_lxqt()`), still hides */
			if (g_key_file_load_from_file(rereads, wins, G_KEY_FILE_NONE, NULL) &&
			    (g_key_file_get_boolean(rereads, "Desktop Entry", "Hidden", NULL) ||
			     g_key_file_get_boolean(rereads, "Desktop Entry", "NoDisplay", NULL)))
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
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ PHASE 15, D-017 — THE SESSION'S XFCONF: what REMOTIX imposes on the
 *      remote session, LOCKED, and nothing permanent in the user's channels
 *      (the user's decision of 13 Nov 2026, replacing that of 25 Sep 2026).
 *
 * ⭐ THE ROAD: xfconf has LOCKED properties.  `[R]` xfconf 4.20
 *    `xfconfd/xfconf-backend-perchannel-xml.c`:
 *    · `load_channel()` reads the system files in every folder of
 *      `XDG_CONFIG_DIRS` (from weakest to strongest), THEN the
 *      user's;
 *    · a `<property … locked="…">` in a SYSTEM file wins, and the user's
 *      with the same name is skipped; `set_property` refuses it.
 *    ⇒ A channel file in a SESSION folder, at the head of
 *      `xfconfd`'s `XDG_CONFIG_DIRS`, holds for the session.
 *
 * ⛔ `locked="*"` DOES NOT LOCK ANYTHING (measured 13 Nov 2026, xfce4-session
 *    4.20.2): the value is a USER NAME, and `locked="<user>"` works.  Before
 *    that date this comment said the contrary, and the four keys we thought
 *    locked were not.
 * ⛔ Lock on a SINGLE property, and not on the channel: the panel stays
 *    editable from the remote session.  ⚠ The price: at the first save of
 *    the channel `xfconfd` writes each locked key in the user's file as
 *    `type="empty"` and the user's value is lost ⇒ the COPY and the RESTORE
 *    (`xfce_restore_keys()`, above).
 * ⛔ `xfce4-panel`: ONLY `/plugins/plugin-N/items` of the `actions` plugin,
 *    which is the only way to take away «Lock» and «Switch User» (the plugin does
 *    not read `Show*`).  N is the user's: read from their channel BEFORE the
 *    birth; for a user without a panel channel, from the standard
 *    `default.xml`.
 *    ⚠ Declared: an `actions` button the user ADDS BY HAND while the session lives
 *      has a new N: it is NOT locked in THAT session («Lock» and «Switch User» show
 *      in it; they do nothing more than the locked `LockCommand` and polkit allow).
 *      It is locked from the next birth, which reads the N again.
 *    ⚠ Declared, an edge case: for a NEW user, while the panel migrates `default.xml`
 *      for the first time, the `items` that file may carry for the `actions` button are
 *      REFUSED by the lock; after the restore the key is absent and the plugin uses its
 *      own built-in defaults, not the distribution's.
 *
 * ⚠ `xfconfd` is NOT a child of the session: it is a user unit
 *   (`xfconfd.service`, activated by the bus), and its
 *   environment is the manager's.  ⇒ The folder is given to it by a drop-in in
 *   `user.control` (the recipe of `write_dropin()`), and if `xfconfd` is already running
 *   it is restarted: it reads the files once, when a channel is opened.
 *
 * ⭐ And instead of `rm -rf ~/.cache/sessions`: `SessionName=REMOTIX` and
 *   `SaveOnExit=false`, locked.  `[R]` xfce4-session 4.20.2
 *   `xfsm-manager.c`: the session is looked up by NAME and saved only
 *   with `SaveOnExit` (`:1278`).
 *
 * ⚠ THE PRICES, declared:
 *   · the drop-in and the folder live as long as the user manager (they are in
 *     `XDG_RUNTIME_DIR`), until the clean-up: an XFCE opened at the monitor on the
 *     SAME manager would see the same locks;
 *   · if `xfconfd` is not a systemd unit on this machine, the
 *     drop-in does not count: the re-read says so.
 *   · `session_clear_out_handler()` leaves at once if it finds
 *     `org.xfce.SessionManager` ALIVE on the same user bus: if, when the remote
 *     session ends, the same user has a LOCAL XFCE session open, the drop-in and
 *     the locks stay in force on THAT local session until a clean-up does happen
 *     (it was so before 13 Nov 2026 too — but now the locks really lock).
 */
struct key_xfconf {
	const char *channel;
	const char *group; /* the property's folder in the channel */
	const char *name;
	const char *kind;
	const char *value;
};

/* ⚠ Sorted by channel and group: the XML is written in one pass. */
static const struct key_xfconf XFCE_LOCKS[] = {
	/* the second logout belt (the first is XFCE4_SESSION_COMPOSITOR) */
	{ "xfce4-session", "general", "WaylandLogoutCommand", "string", "/bin/true" },
	/* the remote session neither finds nor saves sessions */
	{ "xfce4-session", "general", "SessionName", "string", "REMOTIX" },
	{ "xfce4-session", "general", "SaveOnExit", "bool", "false" },
	/* ⛔ THE LOCK — `STUDIES.md` §xfce §10.3.  `[R]` libxfce4ui 4.20.1,
	 *    `xfce_screensaver_lock()`: if `LockCommand` is there, it runs it and
	 *    **returns its result without trying anything else**.  `/bin/false` and
	 *    not `/bin/true` (whoever asks must be told «it is not locked»), and NOT
	 *    the empty string (it means «not set»). */
	{ "xfce4-session", "general", "LockCommand", "string", "/bin/false" },
	/* the «Log Out» dialog: Switch User, Suspend, Hibernate, Hybrid Sleep
	 * (`xfsm-logout-dialog.c:263-374`; Restart and Shut Down have no key: they
	 * stay GREY because of polkit) */
	{ "xfce4-session", "shutdown", "ShowSwitchUser", "bool", "false" },
	{ "xfce4-session", "shutdown", "ShowSuspend", "bool", "false" },
	{ "xfce4-session", "shutdown", "ShowHibernate", "bool", "false" },
	{ "xfce4-session", "shutdown", "ShowHybridSleep", "bool", "false" },
	/* ⛔⛔ THE OUTPUT IS NOT SWITCHED OFF — `STUDIES.md` §xfce §10.2: with
	 *    `dpms-enabled` false no timer is armed (`xfpm-dpms.c`); the
	 *    inactivity ones are already 0 by default, locked so as not to inherit
	 *    what the user set. */
	{ "xfce4-power-manager", "xfce4-power-manager", "dpms-enabled", "bool", "false" },
	{ "xfce4-power-manager", "xfce4-power-manager", "inactivity-on-ac", "uint", "0" },
	{ "xfce4-power-manager", "xfce4-power-manager", "inactivity-on-battery", "uint", "0" },
	{ NULL, NULL, NULL, NULL, NULL },
};

/* The XML of the locked scalar keys of one channel. */
static char *xfce_channel_xml(const char *channel, const char *user)
{
	g_autofree char *who = g_markup_escape_text(user, -1);
	GString *xml = g_string_new(NULL);
	const char *group = NULL;

	g_string_append_printf(xml, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
	                            "<!-- REMOTIX (D-017): locked for the remote session; the "
	                            "user's values are in ~/.local/state/remotix/%s -->\n"
	                            "<channel name=\"%s\" version=\"1.0\">\n",
	                       XFCE_COPY_NAME, channel);
	for (int i = 0; XFCE_LOCKS[i].name; i++) {
		if (g_strcmp0(XFCE_LOCKS[i].channel, channel) != 0)
			continue;
		if (g_strcmp0(group, XFCE_LOCKS[i].group) != 0) {
			if (group)
				g_string_append(xml, "  </property>\n");
			group = XFCE_LOCKS[i].group;
			g_string_append_printf(xml, "  <property name=\"%s\" type=\"empty\">\n", group);
		}
		g_string_append_printf(xml,
		                       "    <property name=\"%s\" type=\"%s\" value=\"%s\" "
		                       "locked=\"%s\"/>\n",
		                       XFCE_LOCKS[i].name, XFCE_LOCKS[i].kind, XFCE_LOCKS[i].value,
		                       who);
	}
	if (group)
		g_string_append(xml, "  </property>\n");
	g_string_append(xml, "</channel>\n");
	return g_string_free(xml, FALSE);
}

/*
 * ⭐ 1.5.2 — THE WHISKER MENU's OWN BUTTONS (openSUSE's default panel, and any distribution
 *    where the user added `xfce4-whiskermenu-plugin`).
 *
 * The plugin does not use the `actions` plugin nor the exit dialog: at the bottom of its
 * window it draws its own buttons, each shown or hidden by a boolean of ITS plugin in the
 * panel channel, `/plugins/plugin-<N>/show-command-<name>` (`[M]` 2.10.1 on Tumbleweed:
 * lockscreen, switchuser, suspend, hibernate, restart, shutdown, logout, logoutuser,
 * settings, menueditor, profile).  Same rule as the `actions` button: lock, Switch User,
 * suspend, hibernate, restart and shut down are locked to `false` in the session; Log Out
 * (`logout`, `logoutuser`) and the harmless ones (settings, editor, profile) are not
 * touched.  ⚠ A key that an older version does not know is simply ignored by it.  ⚠ Versions
 * before 2.4 kept these in `whiskermenu-N.rc`, not in xfconf: not covered (none of the
 * distributions we support ships them).  ⚠ The plugin ids vary, and there may be many:
 * all the `whiskermenu` plugins of the effective channel are locked, one by one; one the
 * user adds DURING the remote session is not.
 */
static const char *WHISKER_HIDE[] = { "show-command-lockscreen", "show-command-switchuser",
	                              "show-command-suspend",    "show-command-hibernate",
	                              "show-command-restart",    "show-command-shutdown", NULL };

/* The panel's XML: `items` of the `actions` plugins and the exit buttons of the
 * `whiskermenu` plugins, locked; the user's values noted in the copy.  NULL if there is
 * no plugin to lock.  `wanted` gets {key, entries} pairs for the final re-read, `flags`
 * the keys of the whisker menu (all expected `false`).
 * ⛔ RULE of the lock files: only the LEAF keys we lock are defined there; a node that
 *    is only the parent of a lock (`plugin-N`, `plugins`) is `type="empty"`, never a
 *    value the user must own.  `xfconfd` does not write in the user's file a value
 *    equal to the system's: with `plugin-N = whiskermenu` in the lock the user's file
 *    kept `type="empty"` and, once the lock was gone, the plugin had no type and was
 *    lost (D-X3). */
static char *xfce_panel_xml(const char *user, GKeyFile *copy, int *count, GPtrArray *wanted,
                              GPtrArray *flags)
{
	g_autofree char *who = g_markup_escape_text(user, -1);
	g_autoptr(GPtrArray) plugins = NULL;
	g_autoptr(GPtrArray) whiskers = NULL;
	GString *xml;
	gboolean any = FALSE;

	plugins = panel_action_plugins(&any);
	whiskers = panel_plugins(PLUGIN_WHISKER, &any);
	if (!any) {
		/* a user who never opened XFCE: the panel will migrate `default.xml` */
		g_ptr_array_extend_and_steal(plugins, default_action_plugins());
		g_ptr_array_extend_and_steal(whiskers, default_plugins(PLUGIN_WHISKER));
	}
	if (!plugins->len && !whiskers->len)
		return NULL;

	xml = g_string_new("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
	                   "<!-- REMOTIX (D-017): only the entries of the action button and the whisker menu's exit buttons, "
	                   "locked for the remote session -->\n"
	                   "<channel name=\"xfce4-panel\" version=\"1.0\">\n"
	                   "  <property name=\"plugins\" type=\"empty\">\n");
	for (guint i = 0; i < plugins->len; i++) {
		const char *base = g_ptr_array_index(plugins, i);
		g_autofree char *key = g_strdup_printf("%s/items", base);
		g_auto(GStrv) user_items = NULL;
		g_auto(GStrv) want = NULL;

		/* the user's value, BEFORE the lock (the plugin's own value too: see the restore) */
		xfce_copy_note(copy, count, "xfce4-panel", base, "plugin");
		xfce_copy_note(copy, count, "xfce4-panel", key, "array");
		xfconf_get("xfce4-panel", key, TRUE, NULL, &user_items);
		want = actions_without_power(user_items ? (const char *const *) user_items
		                                        : (const char *const *) DEFAULT_ACTIONS);
		g_string_append_printf(xml,
		                       "    <property name=\"%s\" type=\"empty\">\n"
		                       "      <property name=\"items\" type=\"array\" locked=\"%s\">\n",
		                       base + strlen("/plugins/"), who);
		for (int j = 0; want[j]; j++) {
			g_autofree char *e = g_markup_escape_text(want[j], -1);

			g_string_append_printf(xml, "        <value type=\"string\" value=\"%s\"/>\n", e);
		}
		g_string_append(xml, "      </property>\n    </property>\n");
		g_ptr_array_add(wanted, g_steal_pointer(&key));
		g_ptr_array_add(wanted, g_steal_pointer(&want));
	}
	for (guint i = 0; i < whiskers->len; i++) {
		const char *base = g_ptr_array_index(whiskers, i);
		g_autofree char *group = NULL;

		/* the plugin's own value too, as for `actions`; and WHICH plugin it is (restore) */
		xfce_copy_note(copy, count, "xfce4-panel", base, "plugin");
		group = g_strdup_printf("k%d", *count - 1);
		g_key_file_set_string(copy, group, "plugin", PLUGIN_WHISKER);
		g_string_append_printf(xml, "    <property name=\"%s\" type=\"empty\">\n",
		                       base + strlen("/plugins/"));
		for (int j = 0; WHISKER_HIDE[j]; j++) {
			char *key = g_strdup_printf("%s/%s", base, WHISKER_HIDE[j]);

			xfce_copy_note(copy, count, "xfce4-panel", key, "bool");
			g_string_append_printf(xml, "      <property name=\"%s\" type=\"bool\" "
			                            "value=\"false\" locked=\"%s\"/>\n",
			                       WHISKER_HIDE[j], who);
			g_ptr_array_add(flags, key);
		}
		g_string_append(xml, "    </property>\n");
	}
	g_string_append(xml, "  </property>\n</channel>\n");
	return g_string_free(xml, FALSE);
}

static void xfce_session_xfconf(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	const char *user = g_get_user_name();
	g_autofree char *cfg = NULL;
	g_autofree char *channels = NULL;
	g_autofree char *dropin_dir = NULL;
	g_autofree char *dropin = NULL;
	g_autofree char *line = NULL;
	g_autofree char *effect = NULL;
	g_autofree char *copy_path = NULL;
	g_autofree char *panel_xml = NULL;
	g_autoptr(GKeyFile) copy = g_key_file_new();
	g_autoptr(GPtrArray) wanted = g_ptr_array_new_with_free_func(NULL);
	g_autoptr(GPtrArray) flags = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GError) mistake = NULL;
	const char *const channel_names[] = { "xfce4-session", "xfce4-power-manager", NULL };
	char *reload[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *restart[] = { "systemctl", "--user", "try-restart", "xfconfd.service", NULL };
	char *show_cmd[] = { "systemctl", "--user", "show", "-p", "Environment", "--value",
		           "xfconfd.service", NULL };
	int in_effect = 0, how_many = 0, count = 0;
	gboolean no_pending;

	if (!runtime || !*runtime || !user) {
		registro_dice(LOG_SESSION,
		              "⛔ XFCE, D-017: without XDG_RUNTIME_DIR no session xfconf — "
		              "the session keys stay at their defaults");
		return;
	}

	/* 1. a session that died badly: its copy is put back FIRST (the clean-up of the child
	 *    should have done it; if it could not, here is the second chance), and the
	 *    old 1.5.0 values are taken away ONCE, BEFORE the new copy.  ⚠ The keys that
	 *    do not go back even now stay PENDING: step 2 keeps their originals. */
	no_pending = xfce_restore_keys();
	/* ⭐ D-X3: the repair is here, at the BIRTH of the session, not at the end of a
	 *   restore: at the birth the lock of the last session is already gone from
	 *   xfconfd (or the check says it is not and waits), and with the plugin's type no
	 *   longer in the lock files (`xfce_panel_xml()`) nothing creates the damage anew —
	 *   this only heals a user damaged before, once. */
	xfce_panel_integrity();
	xfce_migrate_old();

	/* 2. THE COPY, before any lock: the user's value of each key we lock */
	for (int i = 0; XFCE_LOCKS[i].name; i++) {
		g_autofree char *key = g_strdup_printf("/%s/%s", XFCE_LOCKS[i].group,
		                                          XFCE_LOCKS[i].name);

		xfce_copy_note(copy, &count, XFCE_LOCKS[i].channel, key, XFCE_LOCKS[i].kind);
	}
	panel_xml = xfce_panel_xml(user, copy, &count, wanted, flags);
	if (!no_pending) {
		int kept = xfce_copy_keep_pending(copy, &count);

		registro_dice(LOG_SESSION,
		              "⛔ XFCE: %d keys of a previous session are still NOT put back: "
		              "their originals stay in the copy (I do not read them again: what "
		              "the channel has now is not the user's value) and the other keys "
		              "locked by this birth are added to it",
		              kept);
	}
	/* ⛔ Disk; if not, RAM, declared; if not even that, the locks ALL THE SAME: the
	 *    protection of the server wins («WHERE THE COPY LIVES», above). */
	g_key_file_set_boolean(copy, "stato", "ripristinato", FALSE);
	copy_path = xfce_copy_path(FALSE);
	{
		g_autofree char *ram_path = xfce_copy_path(TRUE);
		g_autofree char *ram_dir = ram_path ? g_path_get_dirname(ram_path) : NULL;
		g_autoptr(GError) ram_mistake = NULL;

		if (copy_path && g_key_file_save_to_file(copy, copy_path, &mistake)) {
			g_chmod(copy_path, 0600);
			/* a RAM copy of before: what it had pending is in this one now */
			if (ram_path)
				g_unlink(ram_path);
		} else if (ram_path && is_our_dir(ram_dir) &&
		           g_key_file_save_to_file(copy, ram_path, &ram_mistake)) {
			g_chmod(ram_path, 0600);
			registro_dice(LOG_SESSION,
			              "⚠ XFCE: the copy of the user's keys NOT written on disk (%s): "
			              "DECLARED fallback to %s, in RAM — it lives only as long as the "
			              "user's runtime folder (a reboot, or the last logout without "
			              "lingering, takes it away): if the session dies badly AND that "
			              "happens before the restore, the user's values of the locked "
			              "keys are lost",
			              mistake ? mistake->message : "no safe folder", ram_path);
		} else {
			g_autofree char *said = xfce_copy_said(copy);

			registro_dice(LOG_SESSION,
			              "⛔ XFCE: the copy of the user's keys could be written NEITHER on "
			              "disk (%s) NOR in RAM (%s).  I lock ALL THE SAME — the "
			              "protection of the server wins — and at the end of this session "
			              "the user's values of the locked keys will NOT come back: in "
			              "local those keys will have the XFCE standard.  The values they "
			              "have now, to put back by hand: %s",
			              mistake ? mistake->message : "no safe folder",
			              ram_mistake ? ram_mistake->message : "no safe folder", said);
		}
	}

	/* 3. the locked files, in the session folder */
	cfg = g_build_filename(runtime, "remotix", "xdg-xfce", NULL);
	channels = g_build_filename(cfg, "xfce4", "xfconf", "xfce-perchannel-xml", NULL);
	if (g_mkdir_with_parents(channels, 0700) != 0) {
		registro_dice(LOG_SESSION, "⛔ XFCE, D-017: %s NOT created (%s)", channels,
		              g_strerror(errno));
		return;
	}
	for (int i = 0; channel_names[i]; i++) {
		g_autofree char *name = g_strdup_printf("%s.xml", channel_names[i]);
		g_autofree char *file = g_build_filename(channels, name, NULL);
		g_autofree char *xml = xfce_channel_xml(channel_names[i], user);

		g_clear_error(&mistake);
		if (!g_file_set_contents(file, xml, -1, &mistake)) {
			registro_dice(LOG_SESSION, "⛔ XFCE, D-017: %s NOT written (%s)", file,
			              mistake->message);
			return;
		}
	}
	{
		g_autofree char *file = g_build_filename(channels, "xfce4-panel.xml", NULL);

		if (panel_xml) {
			g_clear_error(&mistake);
			if (!g_file_set_contents(file, panel_xml, -1, &mistake))
				registro_dice(LOG_SESSION, "⛔ XFCE, D-017: %s NOT written (%s)", file,
				              mistake->message);
		} else {
			g_unlink(file); /* a leftover of an earlier birth */
			registro_dice(LOG_SESSION,
			              "⚠ XFCE: no `actions` nor `whiskermenu` plugin in the panel nor in default.xml — "
			              "no entry to lock");
		}
	}

	dropin_dir = g_build_filename(runtime, "systemd", "user.control", "xfconfd.service.d",
	                                   NULL);
	dropin = g_build_filename(dropin_dir, "zz-remotix-session.conf", NULL);
	{
		g_autofree char *system_dirs = session_config_dirs();

		line = g_strdup_printf("[Service]\nEnvironment=XDG_CONFIG_DIRS=%s:%s\n", cfg,
		                       system_dirs);
	}
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

	/* ⛔ AND IT IS RE-READ, as the components will read it: the EFFECTIVE value. */
	for (int i = 0; XFCE_LOCKS[i].name; i++) {
		g_autofree char *key = g_strdup_printf("/%s/%s", XFCE_LOCKS[i].group,
		                                          XFCE_LOCKS[i].name);
		g_autofree char *read = NULL;

		how_many++;
		if (xfconf_get(XFCE_LOCKS[i].channel, key, FALSE, &read, NULL) &&
		    g_strcmp0(read, XFCE_LOCKS[i].value) == 0)
			in_effect++;
		else
			registro_dice(LOG_SESSION,
			              "⛔ XFCE, D-017: %s %s is NOT in force (I re-read «%s», "
			              "wanted «%s»)",
			              XFCE_LOCKS[i].channel, key, read ? read : "nothing",
			              XFCE_LOCKS[i].value);
	}
	for (guint i = 0; i < flags->len; i++) {
		g_autofree char *read = NULL;

		how_many++;
		if (xfconf_get("xfce4-panel", g_ptr_array_index(flags, i), FALSE, &read, NULL) &&
		    g_strcmp0(read, "false") == 0)
			in_effect++;
		else
			registro_dice(LOG_SESSION,
			              "⛔ XFCE, 1.5.2: xfce4-panel %s is NOT in force (I re-read «%s»): "
			              "the whisker menu keeps that button",
			              (char *) g_ptr_array_index(flags, i), read ? read : "nothing");
	}
	for (guint i = 0; i + 1 < wanted->len; i += 2) {
		g_auto(GStrv) read = NULL;

		how_many++;
		if (xfconf_get("xfce4-panel", g_ptr_array_index(wanted, i), TRUE, NULL, &read) &&
		    g_strv_equal((const char *const *) read,
		                 (const char *const *) g_ptr_array_index(wanted, i + 1)))
			in_effect++;
		else
			registro_dice(LOG_SESSION,
			              "⛔ XFCE, D-017: xfce4-panel %s is NOT in force: the entries "
			              "stay in the action button",
			              (char *) g_ptr_array_index(wanted, i));
	}
	for (guint i = 0; i + 1 < wanted->len; i += 2) {
		g_free(g_ptr_array_index(wanted, i));
		g_strfreev(g_ptr_array_index(wanted, i + 1));
	}
	if (in_effect == how_many)
		registro_dice(LOG_SESSION,
		              "⭐ XFCE, D-017: SESSION xfconf in force (%s, %d keys "
		              "locked for «%s», RE-READ): logout belt, SessionName=REMOTIX, "
		              "SaveOnExit=false, no lock/«Switch User»/suspend in the dialog and in "
		              "the action button, DPMS and idleness off — the user's values are "
		              "in the copy and come back at the end",
		              channels, how_many, user);
	else
		registro_dice(LOG_SESSION,
		              "⛔ XFCE, D-017: session xfconf in force for %d keys out of %d.  "
		              "⚠ Some of the locks do NOT hold",
		              in_effect, how_many);
}

void session_settings(void)
{
	/* ⛔ PHASE 12 — before opening a schema: on Plasma these keys do not
	 *    exist, and nothing is set here.  ⭐ What holds on Plasma is already in
	 *    force elsewhere, and none of it writes in the user's files (D-015):
	 *    KIOSK `[$i]` in `$XDG_RUNTIME_DIR/remotix/xdg/kdeglobals`
	 *    (`write_kde_menu_rules`: lock_screen, start_new_session, switch_user);
	 *    suspend, restart and power-off are denied by the SYSTEM polkit rule
	 *    of the package (all desktops, in local too); the screen and idleness
	 *    inhibition to powerdevil is in memory (`powerdevil_guard`); the
	 *    desktop's lock is off by the start line (`--no-lockscreen`, `write_dropin`). */
	if (e_kde()) {
		registro_dice(LOG_SESSION,
		              "⭐ Plasma: nothing to set here — «Lock» and «Switch User» "
		              "are removed by KIOSK [$i] (lock_screen, start_new_session, "
		              "switch_user) in the session folder under XDG_RUNTIME_DIR; "
		              "suspend, restart and power-off are denied by the system polkit "
		              "rule; the screen inhibition to powerdevil is in memory; the "
		              "lock is off by the start line (--no-lockscreen).  The user's "
		              "files are not touched");
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
		/* ⭐ 13 Nov 2026 — everything the session imposes (power, lock, exit
		 *    dialog, action button, logout belt, saved session) is LOCKED in the
		 *    SESSION xfconf, with the copy of the user's values and their restore
		 *    at the end: nothing is written in the user's channels.  See the box above
		 *    `xfce_session_xfconf()`.  ⛔⛔ And it is RE-READ: `xfconf-query` exits with
		 *    zero even when the daemon refuses (`STUDIES.md` §xfce §10.6). */
		xfce_session_xfconf();
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
	/*
	 * ⭐⭐ PHASE 15, D-015 (13 Nov 2026) — GNOME writes NOTHING here any more: the session's
	 *     keys (Ctrl+Alt+F1…F12, «Log Out…», «Switch User», lock, suspend, standby)
	 *     are value + lock in `/etc/dconf/db/remotix` (`locks.db` in the fallback, `session_dconf_prepare()`).  Only the verify remains.
	 */
	session_dconf_verify();
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
	 * ⭐ The dangerous entries of the panel's action button are locked in the session
	 *    xfconf before the birth (`xfce_session_xfconf()`): no thread any more.
	 */
	if (e_xfce()) {
		registro_dice(LOG_SESSION,
		              "XFCE: I ask for no inhibition — xfce4-session does not "
		              "consult the inhibitor, and the output is kept on by "
		              "dpms-enabled=false (locked in the session).  The panel's entries "
		              "are locked before the birth");
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

	/* ⭐ 18 Nov 2026: and neither if the desktop's compositor is not installed — the parent
	 *    refuses before the birth (`main.c`), this is the same fact seen from here (an
	 *    old child, a rebirth), said where this tenant's slice of the log is read */
	{
		const char *missing = session_missing_component();

		if (missing) {
			registro_dice(LOG_SESSION,
			              "⛔ I am not making anything be born: %s needs `%s` and it is NOT "
			              "installed on this server — the administrator must install the "
			              "package `%s`",
			              desktop_name(), missing, missing);
			return false;
		}
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
	/* ⭐ 14 Nov 2026: a birth is under way — a clear-out still to do is no longer retried
	 *    under the session being born (its own end will ask again) */
	clear_out_due = FALSE;
	session_snapshot_handler();
	/* ⭐ 14 Nov 2026: and the dconf profile neutralised at the end of the session before
	 *    goes back to the session's layers, before `gnome-session` is started */
	dconf_profile_reinstate();

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
	{
		const char *busy_unit = NULL;

		if (!inactive_unit(&busy_unit)) {
			registro_dice(LOG_SESSION,
			              "⛔ the PREVIOUS graphical session has not ended yet "
			              "(«%s» is not inactive): I do not make a second one be born "
			              "now — it would be born inside the one that is dying.  ⭐ Retrying "
			              "shortly",
			              busy_unit);
			return false;
		}
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
	if (desktop_session() == SESSION_DESKTOP_GNOME) {
		session_dconf_birth();
		session_gnome_lock_warning();
	}
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
