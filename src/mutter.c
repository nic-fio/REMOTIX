/*
 * mutter.c — see mutter.h for the sequence and the reasons.
 */
#include "mutter.h"

#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <string.h>
#include <unistd.h>

#include "registro.h"

#define AREA "capture"

#define REMOTE_NAME "org.gnome.Mutter.RemoteDesktop"
#define REMOTE_PATH "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSION "org.gnome.Mutter.RemoteDesktop.Session"

#define SCREENCAST_NAME "org.gnome.Mutter.ScreenCast"
#define SCREENCAST_PATH "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSION "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_STREAM "org.gnome.Mutter.ScreenCast.Stream"

#define DISPLAY_NAME "org.gnome.Mutter.DisplayConfig"
#define DISPLAY_PATH "/org/gnome/Mutter/DisplayConfig"
#define IFACE_DISPLAY "org.gnome.Mutter.DisplayConfig"

/*
 * `MetaScreenCastCursorMode`: 0 hidden, 1 embedded in the image, 2 as
 * metadata.  METADATA is chosen, for two reasons:
 *
 *  - embedding it costs a whole frame for every mouse movement (in
 *    v1 it was the main reason scrolling felt like
 *    xrdp's);
 *  - ⛔ and in phase 2 the cursor in the image would be a measurable defect:
 *    the phase 4 bench looks at a frame and demands that the desktop's pointer
 *    NOT be there (`SPECIFICHE.md` §7.1).  It is not read here yet.
 */
#define CURSOR_METADATA 2u

#define WAIT_CALL_MS 15000
#define WAIT_NODE_MS 10000

#define MONITOR_MAX 16

struct MutterSession
{
	GDBusConnection *bus;
	char *check; /* path of the RemoteDesktop session    */
	char *capture;   /* path of the ScreenCast session       */
	char *stream;    /* path of the Stream                   */
	uint32_t node;
	char *mapping_id;           /* the one WE DECLARE to RecordVirtual   */
	char *published_mapping_id; /* ⛔ the one Mutter GENERATES and tells us */

	/* The input channel, opened by `ConnectToEIS` at the right point of the
	 * sequence.  -1 = not open, and whoever receives it DECLARES it. */
	int eis;

	/* ⛔ Our screen: two independent roads, and NULL if they disagree. */
	char *monitor;
	char *monitor_product;
	char *before[MONITOR_MAX]; /* the connectors that existed BEFORE RecordVirtual */
	guint monitor_before;
	guint monitor_after;
};

/* ------------------------------------------------------------------ *
 *  The bus, and why it is not GLib's shared one
 * ------------------------------------------------------------------ */

/*
 * ⛔ NEVER `g_bus_get_sync` ON THE SESSION BUS: GIO keeps
 *    `exit-on-close` on there, and at logout the dropping connection takes the PROCESS
 *    away instead of giving us an error.  A server that disappears when the user leaves
 *    the graphical session is `LEZIONI.md` §5, and the symptom — "the server dies
 *    and nobody knows who killed it" — is form E6 (the sender inferred instead
 *    of asked).
 */
static GDBusConnection *session_dbus(GError **mistake)
{
	g_autofree char *address =
	    g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, mistake);
	GDBusConnection *bus;

	if (!address)
		return NULL;
	bus = g_dbus_connection_new_for_address_sync(
	    address,
	    G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
	        G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, mistake);
	if (bus)
		g_dbus_connection_set_exit_on_close(bus, FALSE);
	return bus;
}

static GVariant *call(GDBusConnection *bus, const char *name, const char *fpath,
                        const char *interfaccia, const char *method, GVariant *call_args,
                        const GVariantType *response_type, GError **mistake)
{
	return g_dbus_connection_call_sync(bus, name, fpath, interfaccia, method, call_args,
	                                   response_type, G_DBUS_CALL_FLAGS_NONE, WAIT_CALL_MS,
	                                   NULL, mistake);
}

/* Reads a property without building a GDBusProxy: a proxy would bring along
 * a cache and a life cycle that are not needed here. */
static char *read_string_property(GDBusConnection *bus, const char *name, const char *fpath,
                               const char *interfaccia, const char *property, GError **mistake)
{
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariant) value = NULL;

	response = call(bus, name, fpath, "org.freedesktop.DBus.Properties", "Get",
	                  g_variant_new("(ss)", interfaccia, property), G_VARIANT_TYPE("(v)"),
	                  mistake);
	if (!response)
		return NULL;
	g_variant_get(response, "(v)", &value);
	if (!g_variant_is_of_type(value, G_VARIANT_TYPE_STRING))
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "%s is not a string", property);
		return NULL;
	}
	return g_variant_dup_string(value, NULL);
}

/* ------------------------------------------------------------------ *
 *  The monitors — asked of DisplayConfig, which harms nobody
 * ------------------------------------------------------------------ */

/*
 * ⛔ NOT with `org.gnome.Shell.Screenshot`.  On a session with zero monitors
 *    Mutter attempts a 0×0 texture, gnome-shell dies, and with
 *    `OnFailure=gnome-session-shutdown.target` **the whole session** goes away
 *    `[M]` 12 August 2026 — tried unintentionally.  ⇒ The check
 *    would destroy the thing it checks, and only in the faulty case.
 *
 * ⭐ `GetCurrentState` answers with the monitors one by one.  The shape is
 *    `(ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv})`: what matters here is
 *    the first element of the monitor's triple, that is `(connector, vendor,
 *    product, serial)`.
 *
 * ⛔ And a DENIED read is not "zero monitors": if the call fails
 *    -1 is returned and the caller declares it (form E8).
 */
static int list_monitors(GDBusConnection *bus, char **names, char **products, guint how_many_max)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariant) monitor = NULL;
	GVariantIter iter;
	GVariant *entry;
	guint amount = 0;

	response = g_dbus_connection_call_sync(bus, DISPLAY_NAME, DISPLAY_PATH, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       WAIT_CALL_MS, NULL, &mistake);
	if (!response)
	{
		registro_dice(AREA, "⚠ DisplayConfig does not answer (%s): I do not know how many monitors "
		                    "there are, and I do not say zero",
		              mistake->message);
		return -1;
	}
	monitor = g_variant_get_child_value(response, 1);
	g_variant_iter_init(&iter, monitor);
	while ((entry = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = entry;
		g_autoptr(GVariant) key = g_variant_get_child_value(v, 0);
		const char *connector = NULL, *vendor = NULL, *product = NULL, *serial_number = NULL;

		g_variant_get(key, "(&s&s&s&s)", &connector, &vendor, &product, &serial_number);
		if (amount < how_many_max)
		{
			if (names)
				names[amount] = g_strdup(connector);
			if (products)
				products[amount] = g_strdup(product);
		}
		amount++;
	}
	return (int) amount;
}

/* ⛔⛔ THE GUARD ON THE SCALE — and it prevents the defect that is NOT seen.
 *
 * `[M]` 14 August 2026: with `org.gnome.desktop.interface scaling-factor = 2` the
 * stream's pixels stay the ones requested, but the LOGICAL monitor takes scale
 * **2.0** even when the only scale allowed for that mode is 1.0
 * (`meta-monitor.c:1988` overrides its own list).  The layout then becomes
 * `roundf(2133/2) = 1067`, and **1067x2 = 2134 != 2133**.
 *
 * ⇒ ⛔ It is the coordinate space of the INPUT: the pointer ends up elsewhere, and
 *   NO log line says so.  It is exactly the symptom the user
 *   described for two days on the Samsung DeX — "the mouse always has problems with
 *   the coordinates of the elements".
 *
 * ⚠ Here it is READ and SAID; nothing is switched off.  The caller decides
 *   what to do with it: with a fixed-size canvas the damage was theoretical, with the canvas at
 *   the client's size (`DECISIONI.md` §5.0-sexies) it is concrete.
 *
 * Returns the worst scale found, or -1 if it could not be read. */
static double logical_monitor_scale(GDBusConnection *bus)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariant) logici = NULL;
	GVariantIter iter;
	GVariant *entry;
	double worst = 1.0;
	gboolean vista = FALSE;

	response = g_dbus_connection_call_sync(bus, DISPLAY_NAME, DISPLAY_PATH, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       WAIT_CALL_MS, NULL, &mistake);
	if (!response)
		return -1.0;
	/* ⚠ Child 2 is the list of LOGICAL monitors — `(iiduba(ssss)a{sv})` — and
	 *   the scale is the third field.  Child 1, which `list_monitors` reads,
	 *   is something else: the PHYSICAL monitors, which have no scale. */
	logici = g_variant_get_child_value(response, 2);
	g_variant_iter_init(&iter, logici);
	while ((entry = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = entry;
		g_autoptr(GVariant) s = g_variant_get_child_value(v, 2);

		if (!g_variant_is_of_type(s, G_VARIANT_TYPE_DOUBLE))
			continue;
		vista = TRUE;
		if (g_variant_get_double(s) > worst)
			worst = g_variant_get_double(s);
	}
	return vista ? worst : -1.0;
}

/*
 * ⛔⭐⭐ THE SCALE OF **OUR** MONITOR, and not the worst on the machine.
 *
 * ⛔ AND THE DIFFERENCE IS THE REASON THIS FUNCTION EXISTS.  The guard
 *    of §5.0-sexies says to **fail** if the scale is not 1.0, and doing it on the
 *    "worst among all logical monitors" would switch the service off on a perfectly
 *    healthy machine: a laptop with its internal screen at 2.0 and our
 *    virtual monitor at 1.0 has no defect at all, and the worst would say 2.0.
 *    ⇒ Only the logical monitor that contains OUR connector is looked at.
 *
 * ⚠ The logical monitor is `(iiduba(ssss)a{sv})`: the scale is the third field, and the
 *   sixth is the list of physical monitors on it — of each, the
 *   first field is the connector.
 *
 * Returns -1 if it could not be read, or if our connector does not appear
 * in any logical monitor.  ⛔ "I do not know" is not "1.0".
 */
static double our_scale(GDBusConnection *bus, const char *connector)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariant) logici = NULL;
	GVariantIter iter;
	GVariant *entry;

	if (!bus || !connector || !connector[0])
		return -1.0;
	response = g_dbus_connection_call_sync(bus, DISPLAY_NAME, DISPLAY_PATH, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       WAIT_CALL_MS, NULL, &mistake);
	if (!response)
		return -1.0;
	logici = g_variant_get_child_value(response, 2);
	g_variant_iter_init(&iter, logici);
	while ((entry = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = entry;
		g_autoptr(GVariant) s = g_variant_get_child_value(v, 2);
		g_autoptr(GVariant) my = g_variant_get_child_value(v, 5);
		GVariantIter mi;
		GVariant *m;

		if (!g_variant_is_of_type(s, G_VARIANT_TYPE_DOUBLE))
			continue;
		g_variant_iter_init(&mi, my);
		while ((m = g_variant_iter_next_value(&mi)))
		{
			g_autoptr(GVariant) mm = m;
			const char *c = NULL, *ven = NULL, *pro = NULL, *ser = NULL;

			if (!g_variant_is_of_type(mm, G_VARIANT_TYPE("(ssss)")))
				continue;
			g_variant_get(mm, "(&s&s&s&s)", &c, &ven, &pro, &ser);
			if (c && !strcmp(c, connector))
				return g_variant_get_double(s);
		}
	}
	return -1.0;
}

static gboolean frac(char **listing, guint amount, const char *name)
{
	guint i;

	for (i = 0; i < amount; i++)
		if (listing[i] && !strcmp(listing[i], name))
			return TRUE;
	return FALSE;
}

/*
 * ⛔ OUR SCREEN IS RECOGNISED BY TWO ROADS, AND THEY MUST AGREE.
 *
 *   1. the diff of the connectors before/after `RecordVirtual`: the new one is ours;
 *   2. the PRODUCT name, which Mutter sets to "Virtual remote monitor" for the
 *      monitors of `RecordVirtual` and to "MetaVirtualMonitor" for the
 *      session's one.
 *
 * If they disagree — or if the new ones are not exactly one — NULL is left.
 * ⛔ Choosing "the first" or "the 1080p one" is form E2: on the server both
 *    monitors are 1920×1080@60 `[M]`, and under that label there are
 *    two different screens.
 */
gboolean mutter_find_monitor(MutterSession *session)
{
	char *names[MONITOR_MAX] = { NULL };
	char *products[MONITOR_MAX] = { NULL };
	guint how_many_before;
	int how_many_after = -1;
	guint i, newcomers = 0;
	int new_index = -1;

	g_return_val_if_fail(session != NULL, FALSE);
	if (session->monitor)
		return TRUE; /* already known: the bus is not asked again out of habit */
	how_many_before = session->monitor_before;

	how_many_after = list_monitors(session->bus, names, products, MONITOR_MAX);
	if (how_many_after < 0)
		return FALSE;
	session->monitor_after = (guint) how_many_after;

	/* ⛔⛔⭐ A MONITOR WAS ALREADY THERE, AND THE USER WOULD SEE ONLY THE WALLPAPER.
	 *
	 * `[M]` 20 August 2026, and it cost an hour: on the "prova" session
	 * there were TWO children of two servers of ours (ports 7700 and 7730), each with
	 * its virtual monitor — `Meta-1` 2544x926 **primary** and `Meta-0` 2532x840,
	 * ours.
	 *
	 * ⛔ And on GNOME **the bar and the dock live only on the PRIMARY monitor**: the
	 *    secondary carries the wallpaper and nothing else.  ⇒ The desktop arrived, the counters
	 *    were all green (`painted == delivered`, zero holes, zero errors) and
	 *    the user said "the shell elements are missing".  **No line in
	 *    any log told it.**
	 *
	 * ⚠ It does not FAIL, and the reason is that this is not always a defect: a
	 *   monitor that was already there can be legitimate (a session with a
	 *   real screen).  ⛔ But it is SAID, loudly, with the cure next to it — because the
	 *   symptom it produces has no other way of being diagnosed
	 *   (`CODER.md` §4.2, and `LEZIONI.md` §1.16: the instruments were all green).
	 */
	if (how_many_before > 0)
	{
		GString *listing = g_string_new(NULL);
		guint j;

		for (j = 0; j < how_many_before && j < MONITOR_MAX; j++)
			g_string_append_printf(listing, "%s%s", j ? ", " : "",
			                       session->before[j] ? session->before[j] : "?");
		registro_dice(AREA,
		              "⛔ THERE WERE ALREADY %u monitors on this session (%s) and ours is "
		              "added: on GNOME the bar and the dock live ONLY on the PRIMARY "
		              "monitor, which stays theirs ⇒ the user will see ours, that is "
		              "ONLY THE WALLPAPER, with all counters green.  ⚠ Almost always it is "
		              "ANOTHER server of ours attached to the same session: switch that one "
		              "off, or give each server its own user",
		              how_many_before, listing->str);
		g_string_free(listing, TRUE);
	}

	/* ⛔ The scale is checked HERE, once, as soon as the virtual monitor exists: it is
	 *    the first instant there is something to look at, and it is before a
	 *    single coordinate has been converted. */
	{
		double scale_factor = logical_monitor_scale(session->bus);

		if (scale_factor < 0)
			registro_dice(AREA, "⚠ the scale of the logical monitors could not be read: "
			                    "I do not say 1.0 out of habit");
		else if (scale_factor != 1.0)
			registro_dice(AREA,
			              "⛔ SCALE %.3f instead of 1.0 — the input coordinate space "
			              "does NOT match the stream's pixels, and the pointer "
			              "will go elsewhere with nothing saying so.  Cure: "
			              "`gsettings set org.gnome.desktop.interface scaling-factor 0` "
			              "(`DECISIONI.md` §5.0-sexies, guard 2)",
			              scale_factor);
	}

	for (i = 0; i < (guint) how_many_after && i < MONITOR_MAX; i++)
	{
		if (!frac(session->before, how_many_before, names[i]))
		{
			newcomers++;
			new_index = (int) i;
		}
	}

	if (newcomers != 1 || new_index < 0)
	{
		registro_dice(AREA,
		              "⚠ after mounting %u new monitors appeared instead of 1 "
		              "(%u before, %d after): I do NOT say which one is ours",
		              newcomers, how_many_before, how_many_after);
	}
	else if (!products[new_index] || !strstr(products[new_index], "remote"))
	{
		/* ⛔ The two roads disagree: stop instead of choosing the
		 *    handier one.  A wrong name here sends a full-screen window
		 *    to the other monitor, and the capture receives zero frames
		 *    without an error anywhere `[M]` 12 August 2026. */
		registro_dice(AREA,
		              "⚠ the monitor that appeared (%s) is called «%s», which is not the name Mutter "
		              "gives a RecordVirtual monitor («Virtual remote monitor»): I do not "
		              "declare it ours",
		              names[new_index], products[new_index] ? products[new_index] : "?");
	}
	else
	{
		session->monitor = g_strdup(names[new_index]);
		session->monitor_product = g_strdup(products[new_index]);
		registro_dice(AREA, "our monitor is %s («%s»), %u before and %d after",
		              session->monitor, session->monitor_product, how_many_before, how_many_after);
	}

	for (i = 0; i < MONITOR_MAX; i++)
	{
		g_free(names[i]);
		g_free(products[i]);
	}
	return session->monitor != NULL;
}

/* ------------------------------------------------------------------ *
 *  The node announcement
 * ------------------------------------------------------------------ */

static void on_node_announced(GDBusConnection *bus, const char *sender, const char *fpath,
                               const char *interfaccia, const char *send_signal, GVariant *parameters,
                               gpointer data)
{
	uint32_t *node = data;

	if (g_variant_is_of_type(parameters, G_VARIANT_TYPE("(u)")))
		g_variant_get(parameters, "(u)", node);
}

static gboolean wake(gpointer data)
{
	return G_SOURCE_CONTINUE;
}

/*
 * Waits for the node announcement, and does so by listening BEFORE starting the
 * stream.
 *
 * The private context is needed because GDBus delivers signals to the thread's
 * default context AT THE TIME OF SUBSCRIPTION, and this code may
 * run on a thread that runs no GLib loop: without a context to
 * run here, the signal would arrive and never be delivered.
 */
static gboolean wait_node(MutterSession *session, GError **mistake)
{
	GMainContext *context = g_main_context_new();
	GSource *heartbeat = NULL;
	guint subscription;
	gint64 expiry;
	gboolean outcome = FALSE;

	g_main_context_push_thread_default(context);

	/* The sender is left NULL on purpose: filtering on a well-known name GDBus
	 * must first resolve its owner, and between the subscription and the
	 * resolution there is a window in which the signal would be discarded.  The
	 * object path is unique to this stream, and filters enough. */
	subscription = g_dbus_connection_signal_subscribe(
	    session->bus, NULL, IFACE_SC_STREAM, "PipeWireStreamAdded", session->stream, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, on_node_announced, &session->node, NULL);

	/* Only NOW is the stream started: not the capture session, which an
	 * associated capture refuses to start on its own. */
	{
		g_autoptr(GVariant) response = call(session->bus, SCREENCAST_NAME, session->stream,
		                                      IFACE_SC_STREAM, "Start", NULL, NULL, mistake);
		if (!response)
			goto fine;
	}

	heartbeat = g_timeout_source_new(50);
	g_source_set_callback(heartbeat, wake, NULL, NULL);
	g_source_attach(heartbeat, context);

	expiry = g_get_monotonic_time() + (gint64) WAIT_NODE_MS * 1000;
	while (session->node == 0 && g_get_monotonic_time() < expiry)
		g_main_context_iteration(context, TRUE);

	if (session->node == 0)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "Mutter did not announce the PipeWire node within %d seconds",
		            WAIT_NODE_MS / 1000);
		goto fine;
	}
	outcome = TRUE;

fine:
	if (heartbeat)
	{
		g_source_destroy(heartbeat);
		g_source_unref(heartbeat);
	}
	g_dbus_connection_signal_unsubscribe(session->bus, subscription);
	g_main_context_pop_thread_default(context);
	g_main_context_unref(context);
	return outcome;
}

/* ------------------------------------------------------------------ *
 *  The sequence
 * ------------------------------------------------------------------ */

MutterSession *mutter_open(GError **mistake)
{
	MutterSession *session = g_new0(MutterSession, 1);
	g_autofree char *check_id = NULL;
	int how_many_before;
	GVariantBuilder property;

	/* ⛔ BEFORE any `goto fault`: with `g_new0` it would be **0**, and
	 *    closing would close descriptor 0 — that is the standard input of whoever
	 *    hosts us.  "Not open" is written -1, not left at zero. */
	session->eis = -1;

	session->bus = session_dbus(mistake);
	if (!session->bus)
		goto fault;

	/* --- 0. the monitors BEFORE: ours will be the one that appears after - */
	how_many_before = list_monitors(session->bus, session->before, NULL, MONITOR_MAX);
	session->monitor_before = how_many_before > 0 ? (guint) how_many_before : 0;
	if (how_many_before == 0)
	{
		/* ⛔ AND ZERO MONITORS IS THE BLACK SESSION, not a detail: `STUDI.md` §gnome
		 *    §3.1 — in headless `needs_outputs=false`, and without monitors the
		 *    session is alive, complete and black.  It does not fail (our
		 *    `RecordVirtual` mounts one of its own), but it is DECLARED: whoever reads zero
		 *    frames later must have this line in front of them. */
		registro_dice(AREA, "⚠ the graphical session has NO monitor: it is the "
		                    "\"alive, complete and black\" session of STUDI.md §gnome §3.1");
	}

	/* --- 1. the control, created and NOT started -------------------------- */
	{
		g_autoptr(GVariant) response =
		    call(session->bus, REMOTE_NAME, REMOTE_PATH, IFACE_REMOTE, "CreateSession", NULL,
		           G_VARIANT_TYPE("(o)"), mistake);
		if (!response)
		{
			g_prefix_error(mistake,
			               "Mutter does not expose RemoteDesktop (is the graphical session started?): ");
			goto fault;
		}
		g_variant_get(response, "(o)", &session->check);
	}

	check_id = read_string_property(session->bus, REMOTE_NAME, session->check,
	                                 IFACE_REMOTE_SESSION, "SessionId", mistake);
	if (!check_id)
		goto fault;

	/*
	 * ⭐ PHASE 4 HAS ARRIVED, and `ConnectToEIS` lives HERE — at the point the
	 *    phase 2 comment had marked.  *Put in on 14 August 2026.*
	 *
	 * The reference calls it right after `CreateSession` and BEFORE `Start`, and
	 * it is not a preference: the compositor faces a session not yet
	 * started, and that is where it agrees to open the channel.
	 *
	 * ⚠ And then the code was read (`reference-gnome/rapporti/06-mutter-input.md`
	 *   §1.2, `[R]`): `handle_connect_to_eis` (`meta-remote-desktop-session.c:1929`)
	 *   ⛔ **calls neither `check_permission` nor `check_can_notify`**, and
	 *   `initialize_viewports` is called by `Start` if the EIS already exists and by
	 *   `ConnectToEIS` if the session is already started: **both orders
	 *   hold**.  It stays here because it is the reference's order, not because
	 *   the other breaks.
	 *
	 * ⛔ AND IT DOES NOT FAIL IF IT DOES NOT OPEN: `CODER.md` §4.2.  Without input the
	 *    capture works all the same — the user WATCHES and does not control — and dropping
	 *    the whole opening for the input channel would take the
	 *    session away from someone who only wanted to see.  ⇒ It is declared, and `input_open`
	 *    will fail with an error that says WHY.
	 */
	{
		g_autoptr(GError) err_eis = NULL;
		g_autoptr(GUnixFDList) descriptors = NULL;
		g_autoptr(GVariant) response = NULL;
		GVariantBuilder without_options;
		gint32 idx = -1;

		session->eis = -1;
		/*
		 * ⛔ No options: `device-types` absent means "turn everything on"
		 *    — keyboard | pointer | touchscreen (`meta-remote-desktop-session.c:1957-1959`
		 *    `[R]`).  ⚠ And the `MetaEis` is created ONCE ONLY per session: a
		 *    second `ConnectToEIS` would reuse the same one and **ignore** the
		 *    new options.  Asking for everything now is the only way not to
		 *    find out in phase 6.
		 */
		g_variant_builder_init(&without_options, G_VARIANT_TYPE("a{sv}"));
		response = g_dbus_connection_call_with_unix_fd_list_sync(
		    session->bus, REMOTE_NAME, session->check, IFACE_REMOTE_SESSION, "ConnectToEIS",
		    g_variant_new("(a{sv})", &without_options), G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
		    WAIT_CALL_MS, NULL, &descriptors, NULL, &err_eis);
		if (!response)
		{
			registro_dice(AREA,
			              "⚠ ConnectToEIS refused (%s): the session opens all the same, but "
			              "NO input will reach the desktop",
			              err_eis->message);
		}
		else
		{
			g_variant_get(response, "(h)", &idx);
			session->eis = g_unix_fd_list_get(descriptors, idx, &err_eis);
			if (session->eis < 0)
				registro_dice(AREA, "⚠ ConnectToEIS answered but the descriptor cannot be read "
				                    "(%s): no input will reach the desktop",
				              err_eis->message);
			else
				registro_dice(AREA, "input channel open: EIS descriptor %d", session->eis);
		}
	}

	/* --- 2. the capture, which registers on the control not yet started -- */
	g_variant_builder_init(&property, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&property, "{sv}", "remote-desktop-session-id",
	                      g_variant_new_string(check_id));
	/* Taken from the reference: GNOME's animations over a remote link
	 * cost bandwidth and add nothing. */
	g_variant_builder_add(&property, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) response = call(
		    session->bus, SCREENCAST_NAME, SCREENCAST_PATH, IFACE_SCREENCAST, "CreateSession",
		    g_variant_new("(a{sv})", &property), G_VARIANT_TYPE("(o)"), mistake);
		if (!response)
			goto fault;
		g_variant_get(response, "(o)", &session->capture);
	}

	/* --- 3. NOW the control is started ------------------------------------ */
	{
		g_autoptr(GVariant) response =
		    call(session->bus, REMOTE_NAME, session->check, IFACE_REMOTE_SESSION, "Start",
		           NULL, NULL, mistake);
		if (!response)
			goto fault;
	}

	/* --- 4. the virtual monitor ------------------------------------------- */
	g_variant_builder_init(&property, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&property, "{sv}", "cursor-mode", g_variant_new_uint32(CURSOR_METADATA));
	/* Declares the virtual monitor a "platform" one, that is treated as
	 * a real screen from the point of view of monitor configuration: the
	 * reference does it too. */
	g_variant_builder_add(&property, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	session->mapping_id = g_uuid_string_random();
	g_variant_builder_add(&property, "{sv}", "mapping-id",
	                      g_variant_new_string(session->mapping_id));
	{
		g_autoptr(GVariant) response =
		    call(session->bus, SCREENCAST_NAME, session->capture, IFACE_SC_SESSION,
		           "RecordVirtual", g_variant_new("(a{sv})", &property), G_VARIANT_TYPE("(o)"),
		           mistake);
		if (!response)
			goto fault;
		g_variant_get(response, "(o)", &session->stream);
	}

	/* --- 5. listening, and then starting the stream ----------------------- */
	if (!wait_node(session, mistake))
		goto fault;

	/* ⛔ AND OUR MONITOR IS NOT LOOKED FOR HERE: at this point it does not exist yet,
	 *    and that is measured — it does not appear even three seconds after `Stream.Start`.
	 *    `mutter_find_monitor` looks for it, called by the capturer when the stream is
	 *    active.  Looking for it here would mean writing "no monitor
	 *    appeared" on a healthy session. */

	/* ⛔⭐ AND THE LINE SAYS WHAT IS THERE, NOT WHAT WILL BE — 27 August
	 *     2026.  Here it used to say "virtual monitor mounted", two lines below
	 *     the comment declaring that **the monitor does not exist yet**: two
	 *     opposite statements two lines apart, and the one read
	 *     in the log was the false one.  ⚠ A message that states a fact that
	 *     is not true is worse than silence: it misleads the reader, and
	 *     silence at least does not.  ⇒ Now it says the true fact — the
	 *     session is started and the stream has its node — and names what
	 *     is still missing. */
	registro_dice(AREA,
	              "capture session STARTED: PipeWire node %u, stream %s.  ⚠ The virtual "
	              "monitor has NOT appeared yet: `mutter_find_monitor()` looks for it when "
	              "the stream delivers (see the box above)",
	              session->node, session->stream);
	return session;

fault:
	mutter_close(session);
	return NULL;
}

uint32_t mutter_node(const MutterSession *session)
{
	return session ? session->node : 0;
}

const char *mutter_stream_path(const MutterSession *session)
{
	return session ? session->stream : NULL;
}

const char *mutter_control_path(const MutterSession *session)
{
	return session ? session->check : NULL;
}

GDBusConnection *mutter_bus(const MutterSession *session)
{
	return session ? session->bus : NULL;
}

const char *mutter_mapping_id(const MutterSession *session)
{
	return session ? session->mapping_id : NULL;
}

int mutter_eis_fd(const MutterSession *session)
{
	return session ? session->eis : -1;
}

/*
 * ⛔⛔⛔ CURE "C" — the EIS channel is rebuilt leaving EVERYTHING else standing.
 *       Added on 21 August 2026, and the phase document calls it "C".
 *       🔸 DERIVED: the decision is the coordinator's, not the user's.
 *
 * THE DAMAGE IT CURES, `[M]` 21 August 2026 (`banchi/06-b33-risveglio.sh`): when
 * Mutter recreates the absolute devices while a button is pressed, that
 * button stays down **in the seat** and from then on **the desktop no longer takes
 * a click** — forever, and without an error anywhere.
 *
 * ⛔ And it cannot be recovered from the client side: `handle_button`
 *    (`meta-eis-client.c:612-621`) looks at `device->button_state`, which on the
 *    NEW device is clean, and swallows the release **before** the seat
 *    sees it.  `[M]` press+release on the new one makes `count` 1→2→1 (Mutter's journal
 *    with `MUTTER_DEBUG=input`: *"Dropping repeated press … count 2"* and
 *    *"Dropping repeated release … count 1"*).
 *
 * ⭐ The ONLY code that brings the count back to zero is `drop_device()`
 *    (`meta-eis-client.c:144-168`), and its only caller is
 *    `meta_eis_client_disconnect()` (`:1075`) — that is **the EIS channel
 *    dropping**.  `[M]` In the journal the six lines *"Releasing pressed
 *    buttons while destroying virtual input device"* appear right there.
 *
 * ⛔⛔ AND WHY THIS FUNCTION LIVES IN `mutter.c` AND NOT IN `input.c` — and the
 *      reason is NOT the one I wrote the first time on 21 August.
 *
 *      I had written: *"closing libei's `dup` is not enough, because the socket
 *      still has `mutter.c`'s descriptor open"*.  ⛔ `[M]` **Refuted**
 *      by the injected fault `RG3`: removing the `close()` the recovery
 *      works all the same.  The detach is sent by `ei_disconnect()` as a
 *      protocol message (`[M]`, fault `RG4`).
 *
 *      ⭐ The true reason, which holds: **after the detach the descriptor set
 *        aside is dead**, and getting a NEW one needs a `ConnectToEIS`
 *        — that is the bus, the name and the path of the session.  `input.c` does not
 *        have them and must not have them: it knows `libei`, not D-Bus.
 *
 * ⭐ And that a second `ConnectToEIS` is legitimate is not a hope: `[R]`
 *    `meta-remote-desktop-session.c:1943-1969` — `session->eis` is **reused** if
 *    already there, and every call adds a client with its own socket.  ⇒ The
 *    `RemoteDesktop` session, the virtual monitor and the PipeWire stream **are not
 *    touched**: that is the difference between the cure and "restarting the server".
 *
 * ⚠ And the options stay absent as on the first call: the `MetaEis` already
 *   exists and would ignore them (see the box inside `mutter_open`).  Putting them
 *   here would give the impression that capabilities can be changed on the fly.
 *
 *   returns  the NEW descriptor (>= 0), already set aside in this
 *            session: whoever uses it makes a `dup` of it, as always;
 *   returns  -1 and fills `mistake`: ⛔ and then the EIS channel **is no longer
 *            there** — the old one was closed anyway, because it is that
 *            closing that heals the seat.  The caller must declare it.
 */
int mutter_eis_reattach(MutterSession *session, GError **mistake)
{
	g_autoptr(GUnixFDList) descriptors = NULL;
	g_autoptr(GVariant) response = NULL;
	GVariantBuilder without_options;
	gint32 idx = -1;

	if (!session || !session->bus || !session->check)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "no RemoteDesktap session open: there is no EIS channel to rebuild");
		return -1;
	}

	/*
	 * ⛔⛔ AND HERE THERE WAS A WRONG EXPLANATION, REFUTED BY MEASUREMENT — 21
	 *      August 2026, injected fault `RG3` of
	 *      `banchi/06-b33-risveglio-guasti.py`.
	 *
	 * It said: *"close first and ask after, and the order IS the cure: as long as
	 * this descriptor is open the socket stays connected and Mutter sees
	 * no detach"*.  ⛔ `[M]` **False**: with this `close()` removed, the
	 * recovery works **exactly as before** and no case of the bench
	 * changes colour.
	 *
	 * ⭐ The detach is sent by `ei_disconnect()` (in `input.c`) as a **protocol
	 *   message**: Mutter runs `meta_eis_client_disconnect()` — and therefore
	 *   `drop_device()` — without waiting for the socket's EOF.  `[M]` Fault
	 *   `RG4` proves it, removing exactly that line and breaking the recovery.
	 *
	 * ⚠ And the `close()` stays, for a more modest and true reason: **without it, one
	 *   descriptor is leaked at every recovery**.  ⛔ A defect that makes no
	 *   noise for hours and then exhausts the descriptor table.
	 *
	 * ⚠ This function is still necessary, and that has not changed: after the
	 *   detach the descriptor set aside is dead, and a NEW one can only be
	 *   asked for by whoever has the bus and the session path — that is, here.
	 */
	if (session->eis >= 0)
	{
		close(session->eis);
		registro_dice(AREA,
		              "⭐ old EIS channel closed (descriptor %d).  ⚠ It is NOT THIS that "
		              "heals the seat — `[M]` 21 Aug 2026, fault RG3: removing the "
		              "close the recovery works all the same.  The detach is sent by "
		              "`ei_disconnect()`; this line serves not to leak a descriptor at "
		              "every recovery",
		              session->eis);
		session->eis = -1;
	}

	g_variant_builder_init(&without_options, G_VARIANT_TYPE("a{sv}"));
	response = g_dbus_connection_call_with_unix_fd_list_sync(
	    session->bus, REMOTE_NAME, session->check, IFACE_REMOTE_SESSION, "ConnectToEIS",
	    g_variant_new("(a{sv})", &without_options), G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
	    WAIT_CALL_MS, NULL, &descriptors, NULL, mistake);
	if (!response)
	{
		registro_dice(AREA,
		              "⛔ the second ConnectToEIS was refused: from now on NO input "
		              "reaches the desktop, and the session stays alive only for watching");
		return -1;
	}
	g_variant_get(response, "(h)", &idx);
	session->eis = g_unix_fd_list_get(descriptors, idx, mistake);
	if (session->eis < 0)
	{
		registro_dice(AREA, "⛔ ConnectToEIS answered but the descriptor cannot be read: from "
		                    "now on NO input reaches the desktop");
		return -1;
	}
	registro_dice(AREA, "⭐ EIS channel REOPENED: descriptor %d.  ⚠ The session, the monitor and the "
	                    "stream were NOT touched",
	              session->eis);
	return session->eis;
}

/*
 * ⛔⛔ THE `mapping-id` COMES FROM MUTTER, NOT FROM US — and the direction matters.
 *
 * `reference-gnome/rapporti/06-mutter-input.md` §7.2 `[≠]`, reread in the code
 * on 14 August 2026:
 *
 *   - `handle_record_virtual` (`meta-screen-cast-session.c:747-765`) reads
 *     **`cursor-mode` and `is-platform` and nothing else**: our
 *     `mapping-id` property is **silently ignored**, without an error;
 *   - `meta_screen_cast_stream_initable_init` (`meta-screen-cast-stream.c:445-458`)
 *     calls `meta_remote_desktop_session_acquire_mapping_id`, which generates a
 *     **random UUID** (`:558-575`), and publishes it in the stream's
 *     `Parameters` property.
 *
 * ⇒ Looking for the `libei` region with the UUID WE declared means
 *   never finding it, and falling back on "take the first" — which with
 *   a single screen works, and stops working exactly the day
 *   there are two screens.  It is the defect `input.c` must not have.
 *
 * ⚠ It is read LAZILY, the first time it is needed: the sequence of
 *   `mutter_open` is not touched (other links work on it), and this read has
 *   no reason to be in there.
 */
const char *mutter_published_mapping_id(MutterSession *session)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GVariant) response = NULL;
	g_autoptr(GVariant) value = NULL;
	char *read = NULL;

	if (!session || !session->bus || !session->stream)
		return NULL;
	if (session->published_mapping_id)
		return session->published_mapping_id;

	response = call(session->bus, SCREENCAST_NAME, session->stream,
	                  "org.freedesktop.DBus.Properties", "Get",
	                  g_variant_new("(ss)", IFACE_SC_STREAM, "Parameters"), G_VARIANT_TYPE("(v)"),
	                  &mistake);
	if (!response)
	{
		/* ⛔ DENIED read, not "not there": whoever reads this line must be able to
		 *    tell the two cases apart (`CODER.md` §3.10). */
		registro_dice(AREA, "⚠ the stream's Parameters cannot be read (%s): Mutter's mapping-id "
		                    "stays unknown, I do NOT say it is missing",
		              mistake->message);
		return NULL;
	}
	g_variant_get(response, "(v)", &value);
	if (!g_variant_lookup(value, "mapping-id", "s", &read) || !read || !*read)
	{
		g_free(read);
		registro_dice(AREA, "⚠ the stream's Parameters do NOT carry a mapping-id: the pointer "
		                    "region will have to be recognised by geometry");
		return NULL;
	}

	session->published_mapping_id = read;
	registro_dice(AREA, "mapping-id published by Mutter: «%s»%s", read,
	              g_strcmp0(read, session->mapping_id) == 0
	                  ? ""
	                  : "  ⛔ DIFFERENT from the one we had declared to RecordVirtual");
	return session->published_mapping_id;
}

const char *mutter_our_monitor(const MutterSession *session)
{
	return session ? session->monitor : NULL;
}

/* ⛔⭐⭐ GUARD 2 OF §5.0-sexies, CLOSED — and it closes a defect no
 *     log line told.
 *
 * ⚠ Until 15 August 2026 the scale was READ and SAID, and the comment above
 *   `logical_monitor_scale()` declared it: *"with a fixed-size canvas the
 *   damage was theoretical, with the canvas at the client's size it is concrete"*.  ⛔ Since
 *   tonight the canvas IS at the client's size, so the damage is concrete: the
 *   layout of the logical monitor and the stream's pixels no longer match, **and the
 *   input coordinate space is the layout** ⇒ the pointer goes elsewhere.
 *
 * ⛔ Mutter is asked, and asked ABOUT OUR monitor: the worst scale of the
 *    machine would say 2.0 on a laptop with a hi-dpi internal screen, and
 *    would switch off a session that has no defect at all.
 *
 * Returns -1 if it could not be read: ⛔ and the caller must NOT treat it
 * as 1.0 — "I do not know" and "it is fine" are two different facts. */
double mutter_our_scale(const MutterSession *session)
{
	if (!session || !session->bus || !session->monitor || !session->monitor[0])
		return -1.0;
	return our_scale(session->bus, session->monitor);
}

const char *mutter_monitor_product(const MutterSession *session)
{
	return session ? session->monitor_product : NULL;
}

void mutter_monitor_counts(const MutterSession *session, guint *before, guint *after)
{
	if (before)
		*before = session ? session->monitor_before : 0;
	if (after)
		*after = session ? session->monitor_after : 0;
}

void mutter_close(MutterSession *session)
{
	if (!session)
		return;

	/* The CONTROL is stopped, and the capture follows it: Mutter refuses to stop
	 * an associated capture directly. */
	if (session->bus && session->check)
	{
		g_autoptr(GError) mistake = NULL;
		/* SHORT wait: we almost always get here because the graphical session has
		 * already gone, and waiting fifteen seconds for an answer that cannot
		 * arrive would hold up whoever is tearing down. */
		g_autoptr(GVariant) response = g_dbus_connection_call_sync(
		    session->bus, REMOTE_NAME, session->check, IFACE_REMOTE_SESSION, "Stop", NULL,
		    NULL, G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &mistake);

		if (!response)
			log_detail(AREA, "closing the control session: %s", mistake->message);
	}

	if (session->eis >= 0)
		close(session->eis);

	g_clear_object(&session->bus);
	g_free(session->check);
	g_free(session->capture);
	g_free(session->stream);
	g_free(session->mapping_id);
	g_free(session->published_mapping_id);
	g_free(session->monitor);
	g_free(session->monitor_product);
	for (guint i = 0; i < MONITOR_MAX; i++)
		g_free(session->before[i]);
	g_free(session);
}
