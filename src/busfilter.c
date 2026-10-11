/*
 * busfilter.c — the session's system bus, without the power buttons.
 *
 * The why is in `busfilter.h`, which is read first.  Here there is only the how.
 *
 * ⭐ THE SHAPE, the same as `xdg-dbus-proxy` (Flatpak): for every program that
 *   connects, ONE connection to the real bus, opened by the filter and not
 *   introduced (no `Hello` of ours) — the program's own `Hello` goes through, the
 *   bus gives the unique name to that connection, and from then on every message
 *   is passed as it is, serial included, file descriptors included (logind's
 *   `Inhibit` answers with one).
 * ⛔ Why not `xdg-dbus-proxy` itself (`[R]` 0.1.6 `flatpak-proxy.c:40-110,
 *    2560-2600`): its filter is a list of what is ALLOWED — every name not
 *    listed is invisible, and a name cannot be «all» (`*` is not a valid
 *    prefix) — and what it refuses is answered with an error, never with «na».
 *    Here the list is the opposite: everything passes except twenty logind
 *    methods.  And an error to `CanPowerOff` is not «no» everywhere:
 *    xfce4-session, on an error, falls back to its polkit helper.
 */
#include "busfilter.h"
#include "log.h"

#include <errno.h>
#include <gio/gio.h>
#include <glib-unix.h>
#include <glib/gstdio.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

#define SYSTEM_BUS_DEFAULT "unix:path=/run/dbus/system_bus_socket"
#define LOGIN1_PATH "/org/freedesktop/login1"
#define LOGIN1_MANAGER "org.freedesktop.login1.Manager"
/* how long the desktop waits for the filter to listen before starting without it */
#define READY_MS 5000

/* ⭐ The questions: «na», as logind says on a machine that cannot.  `[R]` systemd
 *   257 `logind-dbus.c`: they all answer `(s)`. */
static const char *const ANSWER_NA[] = {
	"CanPowerOff", "CanReboot", "CanHalt", "CanSuspend", "CanHibernate",
	"CanHybridSleep", "CanSuspendThenHibernate", "CanSleep", "CanRebootParameter",
	"CanRebootToFirmwareSetup", "CanRebootToBootLoaderMenu",
	"CanRebootToBootLoaderEntry", NULL
};

/* ⛔ The acts: refused.  ⚠ `CancelScheduledShutdown` is not here: it can only
 *   take a power-off away. */
static const char *const REFUSE[] = {
	"PowerOff", "PowerOffWithFlags", "Reboot", "RebootWithFlags", "Halt",
	"HaltWithFlags", "Suspend", "SuspendWithFlags", "Hibernate", "HibernateWithFlags",
	"HybridSleep", "HybridSleepWithFlags", "SuspendThenHibernate",
	"SuspendThenHibernateWithFlags", "Sleep", "ScheduleShutdown", "SetRebootParameter",
	"SetRebootToFirmwareSetup", "SetRebootToBootLoaderMenu",
	"SetRebootToBootLoaderEntry", NULL
};

/* One program of the session and its connection to the real bus. */
typedef struct {
	gint refs;
	GMutex lock;
	GDBusConnection *client; /* the program; NULL once closed */
	GDBusConnection *bus;    /* the real bus; NULL once closed */
	guint32 hello_serial;
	char *unique;            /* the program's name on the bus, from `Hello`'s answer */
} Pair;

static Pair *pair_ref(Pair *p)
{
	g_atomic_int_inc(&p->refs);
	return p;
}

static void pair_unref(gpointer data)
{
	Pair *p = data;

	if (!g_atomic_int_dec_and_test(&p->refs))
		return;
	g_clear_object(&p->client);
	g_clear_object(&p->bus);
	g_free(p->unique);
	g_mutex_clear(&p->lock);
	g_free(p);
}

static void pair_unref_closure(gpointer data, GClosure *closure)
{
	(void)closure;
	pair_unref(data);
}

/* The other end, with a reference, or NULL if the pair is closing. */
static GDBusConnection *other_end(Pair *p, gboolean toward_bus)
{
	GDBusConnection *c;

	g_mutex_lock(&p->lock);
	c = toward_bus ? p->bus : p->client;
	if (c)
		g_object_ref(c);
	g_mutex_unlock(&p->lock);
	return c;
}

static gboolean in_list(const char *const *list, const char *member)
{
	for (int i = 0; list[i]; i++)
		if (strcmp(list[i], member) == 0)
			return TRUE;
	return FALSE;
}

/*
 * 1 = a question to answer «na», 2 = an act to refuse, 0 = let it pass.
 * ⚠ The interface may be absent in a call (the D-Bus specification allows it):
 *   then the path and the name decide.  ⚠ The destination is not looked at — a
 *   program may address logind by its unique name; no one else on the system bus
 *   implements `org.freedesktop.login1.Manager` at that path.
 */
static int power_call(GDBusMessage *m)
{
	const char *path = g_dbus_message_get_path(m);
	const char *iface = g_dbus_message_get_interface(m);
	const char *member = g_dbus_message_get_member(m);

	if (!path || !member || strcmp(path, LOGIN1_PATH) != 0)
		return 0;
	if (iface && strcmp(iface, LOGIN1_MANAGER) != 0)
		return 0;
	if (in_list(ANSWER_NA, member))
		return 1;
	if (in_list(REFUSE, member))
		return 2;
	return 0;
}

/* The answer given in logind's place, sent to the program. */
static void answer_in_place(Pair *p, GDBusConnection *client, GDBusMessage *call, int kind)
{
	g_autoptr(GDBusMessage) reply = NULL;
	g_autoptr(GError) mistake = NULL;
	const char *member = g_dbus_message_get_member(call);

	if (kind == 1) {
		reply = g_dbus_message_new_method_reply(call);
		g_dbus_message_set_body(reply, g_variant_new("(s)", "na"));
		log_detail(LOG_SESSION, "§10.49: login1.%s → «na» (asked by %s)", member,
		           p->unique ? p->unique : "?");
	} else {
		reply = g_dbus_message_new_method_error(
			call, "org.freedesktop.DBus.Error.AccessDenied",
			"%s is not available inside a remote session (REMOTIX DECISIONS 10.49)",
			member);
		registro_dice(LOG_SESSION,
		              "⭐ §10.49: login1.%s REFUSED to %s — power off, restart and suspend "
		              "are not done from inside a remote session",
		              member, p->unique ? p->unique : "?");
	}
	if (g_dbus_message_get_flags(call) & G_DBUS_MESSAGE_FLAGS_NO_REPLY_EXPECTED)
		return;
	/* ⛔ The destination is the program's unique name: sd-bus (systemctl,
	 *    busctl) DROPS a reply addressed to anyone else. */
	g_mutex_lock(&p->lock);
	if (p->unique)
		g_dbus_message_set_destination(reply, p->unique);
	g_mutex_unlock(&p->lock);
	if (g_dbus_message_get_destination(call))
		g_dbus_message_set_sender(reply, g_dbus_message_get_destination(call));
	if (!g_dbus_connection_send_message(client, reply, G_DBUS_SEND_MESSAGE_FLAGS_NONE, NULL,
	                                    &mistake))
		log_detail(LOG_SESSION, "§10.49: the answer to login1.%s did not leave: %s", member,
		           mistake->message);
}

/* Passed on as it is, serial included. */
static void forward(GDBusConnection *to, GDBusMessage *m, GDBusConnection *back)
{
	g_autoptr(GError) mistake = NULL;

	if (g_dbus_connection_send_message(to, m, G_DBUS_SEND_MESSAGE_FLAGS_PRESERVE_SERIAL, NULL,
	                                   &mistake))
		return;
	log_detail(LOG_SESSION, "system bus filter: a message did not pass (%s)", mistake->message);
	/* ⚠ A call that cannot pass is answered, or the program waits for its timeout */
	if (back && g_dbus_message_get_message_type(m) == G_DBUS_MESSAGE_TYPE_METHOD_CALL &&
	    !(g_dbus_message_get_flags(m) & G_DBUS_MESSAGE_FLAGS_NO_REPLY_EXPECTED)) {
		g_autoptr(GDBusMessage) e = g_dbus_message_new_method_error(
			m, "org.freedesktop.DBus.Error.Failed", "REMOTIX system bus filter: %s",
			mistake->message);

		g_dbus_connection_send_message(back, e, G_DBUS_SEND_MESSAGE_FLAGS_NONE, NULL, NULL);
	}
}

/* ⚠ The filters run in GDBus's worker thread, in order: they only look and send. */
static GDBusMessage *from_program(GDBusConnection *c, GDBusMessage *m, gboolean incoming,
                                  gpointer data)
{
	Pair *p = data;
	g_autoptr(GDBusConnection) bus = NULL;
	int kind = 0;

	if (!incoming)
		return m;
	if (g_dbus_message_get_message_type(m) == G_DBUS_MESSAGE_TYPE_METHOD_CALL) {
		if (g_strcmp0(g_dbus_message_get_destination(m), "org.freedesktop.DBus") == 0 &&
		    g_strcmp0(g_dbus_message_get_member(m), "Hello") == 0) {
			g_mutex_lock(&p->lock);
			p->hello_serial = g_dbus_message_get_serial(m);
			g_mutex_unlock(&p->lock);
		}
		kind = power_call(m);
	}
	if (kind)
		answer_in_place(p, c, m, kind);
	else if ((bus = other_end(p, TRUE)))
		forward(bus, m, c);
	g_object_unref(m);
	return NULL;
}

static GDBusMessage *from_bus(GDBusConnection *c, GDBusMessage *m, gboolean incoming,
                              gpointer data)
{
	Pair *p = data;
	g_autoptr(GDBusConnection) client = NULL;

	(void)c;
	if (!incoming)
		return m;
	if (g_dbus_message_get_message_type(m) == G_DBUS_MESSAGE_TYPE_METHOD_RETURN) {
		GVariant *body = g_dbus_message_get_body(m);

		g_mutex_lock(&p->lock);
		if (!p->unique && p->hello_serial &&
		    g_dbus_message_get_reply_serial(m) == p->hello_serial && body &&
		    g_variant_is_of_type(body, G_VARIANT_TYPE("(s)")))
			g_variant_get(body, "(s)", &p->unique);
		g_mutex_unlock(&p->lock);
	}
	if ((client = other_end(p, FALSE)))
		forward(client, m, NULL);
	g_object_unref(m);
	return NULL;
}

/* One end closed: the other is closed too, and the pair lets go of both. */
static void on_closed(GDBusConnection *c, gboolean remote, GError *why, gpointer data)
{
	Pair *p = data;
	GDBusConnection *client, *bus;

	(void)c;
	(void)remote;
	(void)why;
	g_mutex_lock(&p->lock);
	client = g_steal_pointer(&p->client);
	bus = g_steal_pointer(&p->bus);
	g_mutex_unlock(&p->lock);
	if (client) {
		g_dbus_connection_close(client, NULL, NULL, NULL);
		g_object_unref(client);
	}
	if (bus) {
		g_dbus_connection_close(bus, NULL, NULL, NULL);
		g_object_unref(bus);
	}
}

static gboolean on_new_program(GDBusServer *server, GDBusConnection *client, gpointer data)
{
	const char *upstream = data;
	g_autoptr(GError) mistake = NULL;
	GDBusConnection *bus;
	Pair *p;

	(void)server;
	bus = g_dbus_connection_new_for_address_sync(
		upstream,
		G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
			G_DBUS_CONNECTION_FLAGS_DELAY_MESSAGE_PROCESSING,
		NULL, NULL, &mistake);
	if (!bus) {
		registro_dice(LOG_SESSION,
		              "⛔ system bus filter: the real bus (%s) does not answer (%s) — "
		              "the program is turned away",
		              upstream, mistake->message);
		g_dbus_connection_close(client, NULL, NULL, NULL);
		return TRUE;
	}
	p = g_new0(Pair, 1);
	p->refs = 1;
	g_mutex_init(&p->lock);
	p->client = g_object_ref(client);
	p->bus = bus;
	g_dbus_connection_add_filter(client, from_program, pair_ref(p), pair_unref);
	g_dbus_connection_add_filter(bus, from_bus, pair_ref(p), pair_unref);
	g_signal_connect_data(client, "closed", G_CALLBACK(on_closed), pair_ref(p),
	                      pair_unref_closure, 0);
	g_signal_connect_data(bus, "closed", G_CALLBACK(on_closed), pair_ref(p),
	                      pair_unref_closure, 0);
	g_dbus_connection_start_message_processing(bus);
	pair_unref(p);
	return TRUE; /* the client's processing starts when this returns (GDBusServer) */
}

static gboolean on_end(gpointer loop)
{
	g_main_loop_quit(loop);
	return G_SOURCE_REMOVE;
}

static gboolean on_desktop_gone(gint fd, GIOCondition c, gpointer loop)
{
	(void)fd;
	(void)c;
	g_main_loop_quit(loop);
	return G_SOURCE_REMOVE;
}

/* ⚠ Without a pidfd (a kernel older than 5.3): asked every two seconds */
static pid_t watched_desktop;

static gboolean desktop_poll(gpointer loop)
{
	if (kill(watched_desktop, 0) == 0 || errno == EPERM)
		return G_SOURCE_CONTINUE;
	g_main_loop_quit(loop);
	return G_SOURCE_REMOVE;
}

/*
 * ⭐ The filter's life, in a grandchild (double fork): it is NOT the desktop's
 * child, so no desktop ever meets an unknown child among its own — `[M]` 11 Oct
 * 2026: with a plain fork, a desktop that waits for ALL its children (`script`)
 * waited for the filter, and the filter for it.  It dies with the desktop
 * through a pidfd.  Writes one byte on `ready` when it listens.  Never returns.
 */
static void filter_lives(const char *socket_path, const char *upstream, int ready,
                         pid_t desktop)
{
	g_autofree char *escaped = g_dbus_address_escape_value(socket_path);
	g_autofree char *address = g_strdup_printf("unix:path=%s", escaped);
	g_autofree char *guid = g_dbus_generate_guid();
	g_autoptr(GError) mistake = NULL;
	GDBusServer *server;
	GMainLoop *loop;
	struct stat st;
	int pidfd;

	signal(SIGPIPE, SIG_IGN);
	/* ⛔ It dies with the desktop: no filter left behind.  The pidfd is opened
	 *    while the desktop waits for `ready`, so it is that process and no other. */
	pidfd = (int)syscall(SYS_pidfd_open, desktop, 0);
	if (pidfd < 0 && kill(desktop, 0) != 0)
		_exit(0);
	if (lstat(socket_path, &st) == 0 && S_ISSOCK(st.st_mode))
		g_unlink(socket_path); /* a previous session's, ours: the folder is the user's */
	server = g_dbus_server_new_sync(address,
	                                G_DBUS_SERVER_FLAGS_AUTHENTICATION_REQUIRE_SAME_USER,
	                                guid, NULL, NULL, &mistake);
	if (!server) {
		registro_dice(LOG_SESSION,
		              "⛔ §10.49: the system bus filter does NOT start (%s) — the session "
		              "goes on with the real bus, and Power Off, Restart, Suspend WILL "
		              "appear in its menu",
		              mistake->message);
		_exit(1);
	}
	loop = g_main_loop_new(NULL, FALSE);
	g_signal_connect(server, "new-connection", G_CALLBACK(on_new_program),
	                 (gpointer)upstream);
	g_dbus_server_start(server);
	g_unix_signal_add(SIGTERM, on_end, loop);
	g_unix_signal_add(SIGINT, on_end, loop);
	if (pidfd >= 0) {
		g_unix_fd_add(pidfd, G_IO_IN, on_desktop_gone, loop);
	} else {
		watched_desktop = desktop;
		g_timeout_add_seconds(2, desktop_poll, loop);
	}
	registro_dice(LOG_SESSION,
	              "⭐ §10.49: the session's system bus goes through the filter (%s → %s): "
	              "logind's Can* answer «na», PowerOff/Reboot/Suspend/Hibernate… are "
	              "refused, everything else passes",
	              socket_path, upstream);
	if (write(ready, "1", 1) != 1)
		_exit(1);
	close(ready);
	g_main_loop_run(loop);
	g_dbus_server_stop(server);
	g_unlink(socket_path);
	_exit(0);
}

int busfilter_main(int argc, char **argv)
{
	const char *socket_path;
	const char *inherited = g_getenv("DBUS_SYSTEM_BUS_ADDRESS");
	g_autofree char *upstream = NULL;
	g_autofree char *escaped = NULL;
	char **command;
	int pipe_fd[2];
	pid_t desktop = getpid();
	pid_t filter;
	char byte = 0;

	if (argc < 5 || strcmp(argv[1], BUSFILTER_ARG) != 0 || strcmp(argv[3], "--") != 0) {
		fprintf(stderr, "use: %s " BUSFILTER_ARG " SOCKET -- COMMAND…\n", argv[0]);
		return 2;
	}
	socket_path = argv[2];
	command = argv + 4;
	/* ⚠ The real bus is the one inherited, if any (a bench's private bus), or the
	 *   machine's — and never our own socket (a filter inside a filter). */
	escaped = g_dbus_address_escape_value(socket_path);
	if (inherited && *inherited && !strstr(inherited, escaped))
		upstream = g_strdup(inherited);
	else
		upstream = g_strdup(SYSTEM_BUS_DEFAULT);

	/* ⛔ The fork comes BEFORE any GDBus object: a fork after GLib's threads
	 *    is a child with half a library. */
	if (pipe(pipe_fd) != 0) {
		registro_dice(LOG_SESSION, "⛔ §10.49: no pipe for the filter (%s) — the session "
		                           "starts with the real system bus",
		              g_strerror(errno));
	} else if ((filter = fork()) == 0) {
		close(pipe_fd[0]);
		if (fork() == 0)
			filter_lives(socket_path, upstream, pipe_fd[1], desktop);
		_exit(0); /* the middle one: the filter is adopted, not the desktop's */
	} else if (filter < 0) {
		registro_dice(LOG_SESSION, "⛔ §10.49: no fork for the filter (%s) — the session "
		                           "starts with the real system bus",
		              g_strerror(errno));
		close(pipe_fd[0]);
		close(pipe_fd[1]);
	} else {
		struct pollfd w = { .fd = pipe_fd[0], .events = POLLIN };

		close(pipe_fd[1]);
		waitpid(filter, NULL, 0);
		/* ⭐ The desktop starts only when the filter listens: before, its first
		 *    programs would take the fallback address, that is the real bus. */
		if (poll(&w, 1, READY_MS) == 1 && read(pipe_fd[0], &byte, 1) == 1) {
			g_autofree char *value = g_strdup_printf("unix:path=%s;%s", escaped, upstream);

			g_setenv("DBUS_SYSTEM_BUS_ADDRESS", value, TRUE);
		} else {
			registro_dice(LOG_SESSION,
			              "⛔ §10.49: the system bus filter did not get ready in %d ms — "
			              "the session starts with the real bus, and Power Off, Restart, "
			              "Suspend WILL appear in its menu",
			              READY_MS);
		}
		close(pipe_fd[0]);
	}
	execvp(command[0], command);
	registro_dice(LOG_SESSION, "⛔ the session's command «%s» cannot be executed: %s",
	              command[0], g_strerror(errno));
	return 127;
}
