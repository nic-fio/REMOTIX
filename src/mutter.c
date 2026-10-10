/*
 * mutter.c — see mutter.h for the sequence and the reasons.
 */
#include "mutter.h"

#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <string.h>
#include <unistd.h>

#include "registro.h"

#define AREA "cattura"

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"

#define NOME_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define PERCORSO_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSIONE "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_FLUSSO "org.gnome.Mutter.ScreenCast.Stream"

#define NOME_DISPLAY "org.gnome.Mutter.DisplayConfig"
#define PERCORSO_DISPLAY "/org/gnome/Mutter/DisplayConfig"
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
#define CURSORE_METADATO 2u

#define ATTESA_CHIAMATA_MS 15000
#define ATTESA_NODO_MS 10000

#define MONITOR_MAX 16

struct MutterSessione
{
	GDBusConnection *bus;
	char *controllo; /* path of the RemoteDesktop session    */
	char *cattura;   /* path of the ScreenCast session       */
	char *flusso;    /* path of the Stream                   */
	uint32_t nodo;
	char *mapping_id;           /* the one WE DECLARE to RecordVirtual   */
	char *mapping_id_pubblicato; /* ⛔ the one Mutter GENERATES and tells us */

	/* The input channel, opened by `ConnectToEIS` at the right point of the
	 * sequence.  -1 = not open, and whoever receives it DECLARES it. */
	int eis;

	/* ⛔ Our screen: two independent roads, and NULL if they disagree. */
	char *monitor;
	char *monitor_prodotto;
	char *prima[MONITOR_MAX]; /* the connectors that existed BEFORE RecordVirtual */
	guint monitor_prima;
	guint monitor_dopo;
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
static GDBusConnection *bus_di_sessione(GError **sbaglio)
{
	g_autofree char *indirizzo =
	    g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);
	GDBusConnection *bus;

	if (!indirizzo)
		return NULL;
	bus = g_dbus_connection_new_for_address_sync(
	    indirizzo,
	    G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
	        G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, sbaglio);
	if (bus)
		g_dbus_connection_set_exit_on_close(bus, FALSE);
	return bus;
}

static GVariant *chiama(GDBusConnection *bus, const char *nome, const char *percorso,
                        const char *interfaccia, const char *metodo, GVariant *argomenti,
                        const GVariantType *tipo_risposta, GError **sbaglio)
{
	return g_dbus_connection_call_sync(bus, nome, percorso, interfaccia, metodo, argomenti,
	                                   tipo_risposta, G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS,
	                                   NULL, sbaglio);
}

/* Reads a property without building a GDBusProxy: a proxy would bring along
 * a cache and a life cycle that are not needed here. */
static char *proprieta_stringa(GDBusConnection *bus, const char *nome, const char *percorso,
                               const char *interfaccia, const char *proprieta, GError **sbaglio)
{
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) valore = NULL;

	risposta = chiama(bus, nome, percorso, "org.freedesktop.DBus.Properties", "Get",
	                  g_variant_new("(ss)", interfaccia, proprieta), G_VARIANT_TYPE("(v)"),
	                  sbaglio);
	if (!risposta)
		return NULL;
	g_variant_get(risposta, "(v)", &valore);
	if (!g_variant_is_of_type(valore, G_VARIANT_TYPE_STRING))
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "%s is not a string", proprieta);
		return NULL;
	}
	return g_variant_dup_string(valore, NULL);
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
static int elenca_monitor(GDBusConnection *bus, char **nomi, char **prodotti, guint quanti_max)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) monitor = NULL;
	GVariantIter iter;
	GVariant *voce;
	guint quanti = 0;

	risposta = g_dbus_connection_call_sync(bus, NOME_DISPLAY, PERCORSO_DISPLAY, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       ATTESA_CHIAMATA_MS, NULL, &sbaglio);
	if (!risposta)
	{
		registro_dice(AREA, "⚠ DisplayConfig does not answer (%s): I do not know how many monitors "
		                    "there are, and I do not say zero",
		              sbaglio->message);
		return -1;
	}
	monitor = g_variant_get_child_value(risposta, 1);
	g_variant_iter_init(&iter, monitor);
	while ((voce = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = voce;
		g_autoptr(GVariant) chiave = g_variant_get_child_value(v, 0);
		const char *connettore = NULL, *venditore = NULL, *prodotto = NULL, *seriale = NULL;

		g_variant_get(chiave, "(&s&s&s&s)", &connettore, &venditore, &prodotto, &seriale);
		if (quanti < quanti_max)
		{
			if (nomi)
				nomi[quanti] = g_strdup(connettore);
			if (prodotti)
				prodotti[quanti] = g_strdup(prodotto);
		}
		quanti++;
	}
	return (int) quanti;
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
static double scala_dei_monitor_logici(GDBusConnection *bus)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) logici = NULL;
	GVariantIter iter;
	GVariant *voce;
	double peggiore = 1.0;
	gboolean vista = FALSE;

	risposta = g_dbus_connection_call_sync(bus, NOME_DISPLAY, PERCORSO_DISPLAY, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       ATTESA_CHIAMATA_MS, NULL, &sbaglio);
	if (!risposta)
		return -1.0;
	/* ⚠ Child 2 is the list of LOGICAL monitors — `(iiduba(ssss)a{sv})` — and
	 *   the scale is the third field.  Child 1, which `elenca_monitor` reads,
	 *   is something else: the PHYSICAL monitors, which have no scale. */
	logici = g_variant_get_child_value(risposta, 2);
	g_variant_iter_init(&iter, logici);
	while ((voce = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = voce;
		g_autoptr(GVariant) s = g_variant_get_child_value(v, 2);

		if (!g_variant_is_of_type(s, G_VARIANT_TYPE_DOUBLE))
			continue;
		vista = TRUE;
		if (g_variant_get_double(s) > peggiore)
			peggiore = g_variant_get_double(s);
	}
	return vista ? peggiore : -1.0;
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
static double scala_del_nostro(GDBusConnection *bus, const char *connettore)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) logici = NULL;
	GVariantIter iter;
	GVariant *voce;

	if (!bus || !connettore || !connettore[0])
		return -1.0;
	risposta = g_dbus_connection_call_sync(bus, NOME_DISPLAY, PERCORSO_DISPLAY, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       ATTESA_CHIAMATA_MS, NULL, &sbaglio);
	if (!risposta)
		return -1.0;
	logici = g_variant_get_child_value(risposta, 2);
	g_variant_iter_init(&iter, logici);
	while ((voce = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = voce;
		g_autoptr(GVariant) s = g_variant_get_child_value(v, 2);
		g_autoptr(GVariant) miei = g_variant_get_child_value(v, 5);
		GVariantIter mi;
		GVariant *m;

		if (!g_variant_is_of_type(s, G_VARIANT_TYPE_DOUBLE))
			continue;
		g_variant_iter_init(&mi, miei);
		while ((m = g_variant_iter_next_value(&mi)))
		{
			g_autoptr(GVariant) mm = m;
			const char *c = NULL, *ven = NULL, *pro = NULL, *ser = NULL;

			if (!g_variant_is_of_type(mm, G_VARIANT_TYPE("(ssss)")))
				continue;
			g_variant_get(mm, "(&s&s&s&s)", &c, &ven, &pro, &ser);
			if (c && !strcmp(c, connettore))
				return g_variant_get_double(s);
		}
	}
	return -1.0;
}

static gboolean fra(char **elenco, guint quanti, const char *nome)
{
	guint i;

	for (i = 0; i < quanti; i++)
		if (elenco[i] && !strcmp(elenco[i], nome))
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
gboolean mutter_monitor_cerca(MutterSessione *sessione)
{
	char *nomi[MONITOR_MAX] = { NULL };
	char *prodotti[MONITOR_MAX] = { NULL };
	guint quanti_prima;
	int quanti_dopo = -1;
	guint i, nuovi = 0;
	int indice_nuovo = -1;

	g_return_val_if_fail(sessione != NULL, FALSE);
	if (sessione->monitor)
		return TRUE; /* already known: the bus is not asked again out of habit */
	quanti_prima = sessione->monitor_prima;

	quanti_dopo = elenca_monitor(sessione->bus, nomi, prodotti, MONITOR_MAX);
	if (quanti_dopo < 0)
		return FALSE;
	sessione->monitor_dopo = (guint) quanti_dopo;

	/* ⛔⛔⭐ A MONITOR WAS ALREADY THERE, AND THE USER WOULD SEE ONLY THE WALLPAPER.
	 *
	 * `[M]` 20 August 2026, and it cost an hour: on the "prova" session
	 * there were TWO children of two servers of ours (ports 7700 and 7730), each with
	 * its virtual monitor — `Meta-1` 2544x926 **primary** and `Meta-0` 2532x840,
	 * ours.
	 *
	 * ⛔ And on GNOME **the bar and the dock live only on the PRIMARY monitor**: the
	 *    secondary carries the wallpaper and nothing else.  ⇒ The desktop arrived, the counters
	 *    were all green (`dipinti == consegnati`, zero holes, zero errors) and
	 *    the user said "the shell elements are missing".  **No line in
	 *    any log told it.**
	 *
	 * ⚠ It does not FAIL, and the reason is that this is not always a defect: a
	 *   monitor that was already there can be legitimate (a session with a
	 *   real screen).  ⛔ But it is SAID, loudly, with the cure next to it — because the
	 *   symptom it produces has no other way of being diagnosed
	 *   (`CODER.md` §4.2, and `LEZIONI.md` §1.16: the instruments were all green).
	 */
	if (quanti_prima > 0)
	{
		GString *elenco = g_string_new(NULL);
		guint j;

		for (j = 0; j < quanti_prima && j < MONITOR_MAX; j++)
			g_string_append_printf(elenco, "%s%s", j ? ", " : "",
			                       sessione->prima[j] ? sessione->prima[j] : "?");
		registro_dice(AREA,
		              "⛔ THERE WERE ALREADY %u monitors on this session (%s) and ours is "
		              "added: on GNOME the bar and the dock live ONLY on the PRIMARY "
		              "monitor, which stays theirs ⇒ the user will see ours, that is "
		              "ONLY THE WALLPAPER, with all counters green.  ⚠ Almost always it is "
		              "ANOTHER server of ours attached to the same session: switch that one "
		              "off, or give each server its own user",
		              quanti_prima, elenco->str);
		g_string_free(elenco, TRUE);
	}

	/* ⛔ The scale is checked HERE, once, as soon as the virtual monitor exists: it is
	 *    the first instant there is something to look at, and it is before a
	 *    single coordinate has been converted. */
	{
		double scala = scala_dei_monitor_logici(sessione->bus);

		if (scala < 0)
			registro_dice(AREA, "⚠ the scale of the logical monitors could not be read: "
			                    "I do not say 1.0 out of habit");
		else if (scala != 1.0)
			registro_dice(AREA,
			              "⛔ SCALE %.3f instead of 1.0 — the input coordinate space "
			              "does NOT match the stream's pixels, and the pointer "
			              "will go elsewhere with nothing saying so.  Cure: "
			              "`gsettings set org.gnome.desktop.interface scaling-factor 0` "
			              "(`DECISIONI.md` §5.0-sexies, guard 2)",
			              scala);
	}

	for (i = 0; i < (guint) quanti_dopo && i < MONITOR_MAX; i++)
	{
		if (!fra(sessione->prima, quanti_prima, nomi[i]))
		{
			nuovi++;
			indice_nuovo = (int) i;
		}
	}

	if (nuovi != 1 || indice_nuovo < 0)
	{
		registro_dice(AREA,
		              "⚠ after mounting %u new monitors appeared instead of 1 "
		              "(%u before, %d after): I do NOT say which one is ours",
		              nuovi, quanti_prima, quanti_dopo);
	}
	else if (!prodotti[indice_nuovo] || !strstr(prodotti[indice_nuovo], "remote"))
	{
		/* ⛔ The two roads disagree: stop instead of choosing the
		 *    handier one.  A wrong name here sends a full-screen window
		 *    to the other monitor, and the capture receives zero frames
		 *    without an error anywhere `[M]` 12 August 2026. */
		registro_dice(AREA,
		              "⚠ the monitor that appeared (%s) is called «%s», which is not the name Mutter "
		              "gives a RecordVirtual monitor («Virtual remote monitor»): I do not "
		              "declare it ours",
		              nomi[indice_nuovo], prodotti[indice_nuovo] ? prodotti[indice_nuovo] : "?");
	}
	else
	{
		sessione->monitor = g_strdup(nomi[indice_nuovo]);
		sessione->monitor_prodotto = g_strdup(prodotti[indice_nuovo]);
		registro_dice(AREA, "our monitor is %s («%s»), %u before and %d after",
		              sessione->monitor, sessione->monitor_prodotto, quanti_prima, quanti_dopo);
	}

	for (i = 0; i < MONITOR_MAX; i++)
	{
		g_free(nomi[i]);
		g_free(prodotti[i]);
	}
	return sessione->monitor != NULL;
}

/* ------------------------------------------------------------------ *
 *  The node announcement
 * ------------------------------------------------------------------ */

static void su_nodo_annunciato(GDBusConnection *bus, const char *mittente, const char *percorso,
                               const char *interfaccia, const char *segnale, GVariant *parametri,
                               gpointer dati)
{
	uint32_t *nodo = dati;

	if (g_variant_is_of_type(parametri, G_VARIANT_TYPE("(u)")))
		g_variant_get(parametri, "(u)", nodo);
}

static gboolean sveglia(gpointer dati)
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
static gboolean attendi_nodo(MutterSessione *sessione, GError **sbaglio)
{
	GMainContext *contesto = g_main_context_new();
	GSource *battito = NULL;
	guint sottoscrizione;
	gint64 scadenza;
	gboolean esito = FALSE;

	g_main_context_push_thread_default(contesto);

	/* The sender is left NULL on purpose: filtering on a well-known name GDBus
	 * must first resolve its owner, and between the subscription and the
	 * resolution there is a window in which the signal would be discarded.  The
	 * object path is unique to this stream, and filters enough. */
	sottoscrizione = g_dbus_connection_signal_subscribe(
	    sessione->bus, NULL, IFACE_SC_FLUSSO, "PipeWireStreamAdded", sessione->flusso, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, su_nodo_annunciato, &sessione->nodo, NULL);

	/* Only NOW is the stream started: not the capture session, which an
	 * associated capture refuses to start on its own. */
	{
		g_autoptr(GVariant) risposta = chiama(sessione->bus, NOME_SCREENCAST, sessione->flusso,
		                                      IFACE_SC_FLUSSO, "Start", NULL, NULL, sbaglio);
		if (!risposta)
			goto fine;
	}

	battito = g_timeout_source_new(50);
	g_source_set_callback(battito, sveglia, NULL, NULL);
	g_source_attach(battito, contesto);

	scadenza = g_get_monotonic_time() + (gint64) ATTESA_NODO_MS * 1000;
	while (sessione->nodo == 0 && g_get_monotonic_time() < scadenza)
		g_main_context_iteration(contesto, TRUE);

	if (sessione->nodo == 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "Mutter did not announce the PipeWire node within %d seconds",
		            ATTESA_NODO_MS / 1000);
		goto fine;
	}
	esito = TRUE;

fine:
	if (battito)
	{
		g_source_destroy(battito);
		g_source_unref(battito);
	}
	g_dbus_connection_signal_unsubscribe(sessione->bus, sottoscrizione);
	g_main_context_pop_thread_default(contesto);
	g_main_context_unref(contesto);
	return esito;
}

/* ------------------------------------------------------------------ *
 *  The sequence
 * ------------------------------------------------------------------ */

MutterSessione *mutter_apri(GError **sbaglio)
{
	MutterSessione *sessione = g_new0(MutterSessione, 1);
	g_autofree char *id_controllo = NULL;
	int quanti_prima;
	GVariantBuilder proprieta;

	/* ⛔ BEFORE any `goto guasto`: with `g_new0` it would be **0**, and
	 *    closing would close descriptor 0 — that is the standard input of whoever
	 *    hosts us.  "Not open" is written -1, not left at zero. */
	sessione->eis = -1;

	sessione->bus = bus_di_sessione(sbaglio);
	if (!sessione->bus)
		goto guasto;

	/* --- 0. the monitors BEFORE: ours will be the one that appears after - */
	quanti_prima = elenca_monitor(sessione->bus, sessione->prima, NULL, MONITOR_MAX);
	sessione->monitor_prima = quanti_prima > 0 ? (guint) quanti_prima : 0;
	if (quanti_prima == 0)
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
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_REMOTE, PERCORSO_REMOTE, IFACE_REMOTE, "CreateSession", NULL,
		           G_VARIANT_TYPE("(o)"), sbaglio);
		if (!risposta)
		{
			g_prefix_error(sbaglio,
			               "Mutter does not expose RemoteDesktop (is the graphical session started?): ");
			goto guasto;
		}
		g_variant_get(risposta, "(o)", &sessione->controllo);
	}

	id_controllo = proprieta_stringa(sessione->bus, NOME_REMOTE, sessione->controllo,
	                                 IFACE_REMOTE_SESSIONE, "SessionId", sbaglio);
	if (!id_controllo)
		goto guasto;

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
	 *    session away from someone who only wanted to see.  ⇒ It is declared, and `input_apri`
	 *    will fail with an error that says WHY.
	 */
	{
		g_autoptr(GError) sbaglio_eis = NULL;
		g_autoptr(GUnixFDList) descrittori = NULL;
		g_autoptr(GVariant) risposta = NULL;
		GVariantBuilder senza_opzioni;
		gint32 indice = -1;

		sessione->eis = -1;
		/*
		 * ⛔ No options: `device-types` absent means "turn everything on"
		 *    — keyboard | pointer | touchscreen (`meta-remote-desktop-session.c:1957-1959`
		 *    `[R]`).  ⚠ And the `MetaEis` is created ONCE ONLY per session: a
		 *    second `ConnectToEIS` would reuse the same one and **ignore** the
		 *    new options.  Asking for everything now is the only way not to
		 *    find out in phase 6.
		 */
		g_variant_builder_init(&senza_opzioni, G_VARIANT_TYPE("a{sv}"));
		risposta = g_dbus_connection_call_with_unix_fd_list_sync(
		    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "ConnectToEIS",
		    g_variant_new("(a{sv})", &senza_opzioni), G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
		    ATTESA_CHIAMATA_MS, NULL, &descrittori, NULL, &sbaglio_eis);
		if (!risposta)
		{
			registro_dice(AREA,
			              "⚠ ConnectToEIS refused (%s): the session opens all the same, but "
			              "NO input will reach the desktop",
			              sbaglio_eis->message);
		}
		else
		{
			g_variant_get(risposta, "(h)", &indice);
			sessione->eis = g_unix_fd_list_get(descrittori, indice, &sbaglio_eis);
			if (sessione->eis < 0)
				registro_dice(AREA, "⚠ ConnectToEIS answered but the descriptor cannot be read "
				                    "(%s): no input will reach the desktop",
				              sbaglio_eis->message);
			else
				registro_dice(AREA, "input channel open: EIS descriptor %d", sessione->eis);
		}
	}

	/* --- 2. the capture, which registers on the control not yet started -- */
	g_variant_builder_init(&proprieta, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&proprieta, "{sv}", "remote-desktop-session-id",
	                      g_variant_new_string(id_controllo));
	/* Taken from the reference: GNOME's animations over a remote link
	 * cost bandwidth and add nothing. */
	g_variant_builder_add(&proprieta, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) risposta = chiama(
		    sessione->bus, NOME_SCREENCAST, PERCORSO_SCREENCAST, IFACE_SCREENCAST, "CreateSession",
		    g_variant_new("(a{sv})", &proprieta), G_VARIANT_TYPE("(o)"), sbaglio);
		if (!risposta)
			goto guasto;
		g_variant_get(risposta, "(o)", &sessione->cattura);
	}

	/* --- 3. NOW the control is started ------------------------------------ */
	{
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "Start",
		           NULL, NULL, sbaglio);
		if (!risposta)
			goto guasto;
	}

	/* --- 4. the virtual monitor ------------------------------------------- */
	g_variant_builder_init(&proprieta, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&proprieta, "{sv}", "cursor-mode", g_variant_new_uint32(CURSORE_METADATO));
	/* Declares the virtual monitor a "platform" one, that is treated as
	 * a real screen from the point of view of monitor configuration: the
	 * reference does it too. */
	g_variant_builder_add(&proprieta, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	sessione->mapping_id = g_uuid_string_random();
	g_variant_builder_add(&proprieta, "{sv}", "mapping-id",
	                      g_variant_new_string(sessione->mapping_id));
	{
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_SCREENCAST, sessione->cattura, IFACE_SC_SESSIONE,
		           "RecordVirtual", g_variant_new("(a{sv})", &proprieta), G_VARIANT_TYPE("(o)"),
		           sbaglio);
		if (!risposta)
			goto guasto;
		g_variant_get(risposta, "(o)", &sessione->flusso);
	}

	/* --- 5. listening, and then starting the stream ----------------------- */
	if (!attendi_nodo(sessione, sbaglio))
		goto guasto;

	/* ⛔ AND OUR MONITOR IS NOT LOOKED FOR HERE: at this point it does not exist yet,
	 *    and that is measured — it does not appear even three seconds after `Stream.Start`.
	 *    `mutter_monitor_cerca` looks for it, called by the capturer when the stream is
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
	              "monitor has NOT appeared yet: `mutter_monitor_cerca()` looks for it when "
	              "the stream delivers (see the box above)",
	              sessione->nodo, sessione->flusso);
	return sessione;

guasto:
	mutter_chiudi(sessione);
	return NULL;
}

uint32_t mutter_nodo(const MutterSessione *sessione)
{
	return sessione ? sessione->nodo : 0;
}

const char *mutter_percorso_flusso(const MutterSessione *sessione)
{
	return sessione ? sessione->flusso : NULL;
}

const char *mutter_percorso_controllo(const MutterSessione *sessione)
{
	return sessione ? sessione->controllo : NULL;
}

GDBusConnection *mutter_bus(const MutterSessione *sessione)
{
	return sessione ? sessione->bus : NULL;
}

const char *mutter_mapping_id(const MutterSessione *sessione)
{
	return sessione ? sessione->mapping_id : NULL;
}

int mutter_eis_fd(const MutterSessione *sessione)
{
	return sessione ? sessione->eis : -1;
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
 *   exists and would ignore them (see the box inside `mutter_apri`).  Putting them
 *   here would give the impression that capabilities can be changed on the fly.
 *
 *   returns  the NEW descriptor (>= 0), already set aside in this
 *            session: whoever uses it makes a `dup` of it, as always;
 *   returns  -1 and fills `sbaglio`: ⛔ and then the EIS channel **is no longer
 *            there** — the old one was closed anyway, because it is that
 *            closing that heals the seat.  The caller must declare it.
 */
int mutter_eis_riattacca(MutterSessione *sessione, GError **sbaglio)
{
	g_autoptr(GUnixFDList) descrittori = NULL;
	g_autoptr(GVariant) risposta = NULL;
	GVariantBuilder senza_opzioni;
	gint32 indice = -1;

	if (!sessione || !sessione->bus || !sessione->controllo)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
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
	if (sessione->eis >= 0)
	{
		close(sessione->eis);
		registro_dice(AREA,
		              "⭐ old EIS channel closed (descriptor %d).  ⚠ It is NOT THIS that "
		              "heals the seat — `[M]` 21 Aug 2026, fault RG3: removing the "
		              "close the recovery works all the same.  The detach is sent by "
		              "`ei_disconnect()`; this line serves not to leak a descriptor at "
		              "every recovery",
		              sessione->eis);
		sessione->eis = -1;
	}

	g_variant_builder_init(&senza_opzioni, G_VARIANT_TYPE("a{sv}"));
	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "ConnectToEIS",
	    g_variant_new("(a{sv})", &senza_opzioni), G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
	    ATTESA_CHIAMATA_MS, NULL, &descrittori, NULL, sbaglio);
	if (!risposta)
	{
		registro_dice(AREA,
		              "⛔ the second ConnectToEIS was refused: from now on NO input "
		              "reaches the desktop, and the session stays alive only for watching");
		return -1;
	}
	g_variant_get(risposta, "(h)", &indice);
	sessione->eis = g_unix_fd_list_get(descrittori, indice, sbaglio);
	if (sessione->eis < 0)
	{
		registro_dice(AREA, "⛔ ConnectToEIS answered but the descriptor cannot be read: from "
		                    "now on NO input reaches the desktop");
		return -1;
	}
	registro_dice(AREA, "⭐ EIS channel REOPENED: descriptor %d.  ⚠ The session, the monitor and the "
	                    "stream were NOT touched",
	              sessione->eis);
	return sessione->eis;
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
 *   `mutter_apri` is not touched (other links work on it), and this read has
 *   no reason to be in there.
 */
const char *mutter_mapping_id_pubblicato(MutterSessione *sessione)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) valore = NULL;
	char *letto = NULL;

	if (!sessione || !sessione->bus || !sessione->flusso)
		return NULL;
	if (sessione->mapping_id_pubblicato)
		return sessione->mapping_id_pubblicato;

	risposta = chiama(sessione->bus, NOME_SCREENCAST, sessione->flusso,
	                  "org.freedesktop.DBus.Properties", "Get",
	                  g_variant_new("(ss)", IFACE_SC_FLUSSO, "Parameters"), G_VARIANT_TYPE("(v)"),
	                  &sbaglio);
	if (!risposta)
	{
		/* ⛔ DENIED read, not "not there": whoever reads this line must be able to
		 *    tell the two cases apart (`CODER.md` §3.10). */
		registro_dice(AREA, "⚠ the stream's Parameters cannot be read (%s): Mutter's mapping-id "
		                    "stays unknown, I do NOT say it is missing",
		              sbaglio->message);
		return NULL;
	}
	g_variant_get(risposta, "(v)", &valore);
	if (!g_variant_lookup(valore, "mapping-id", "s", &letto) || !letto || !*letto)
	{
		g_free(letto);
		registro_dice(AREA, "⚠ the stream's Parameters do NOT carry a mapping-id: the pointer "
		                    "region will have to be recognised by geometry");
		return NULL;
	}

	sessione->mapping_id_pubblicato = letto;
	registro_dice(AREA, "mapping-id published by Mutter: «%s»%s", letto,
	              g_strcmp0(letto, sessione->mapping_id) == 0
	                  ? ""
	                  : "  ⛔ DIFFERENT from the one we had declared to RecordVirtual");
	return sessione->mapping_id_pubblicato;
}

const char *mutter_monitor_nostro(const MutterSessione *sessione)
{
	return sessione ? sessione->monitor : NULL;
}

/* ⛔⭐⭐ GUARD 2 OF §5.0-sexies, CLOSED — and it closes a defect no
 *     log line told.
 *
 * ⚠ Until 15 August 2026 the scale was READ and SAID, and the comment above
 *   `scala_dei_monitor_logici()` declared it: *"with a fixed-size canvas the
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
double mutter_scala_nostra(const MutterSessione *sessione)
{
	if (!sessione || !sessione->bus || !sessione->monitor || !sessione->monitor[0])
		return -1.0;
	return scala_del_nostro(sessione->bus, sessione->monitor);
}

const char *mutter_monitor_prodotto(const MutterSessione *sessione)
{
	return sessione ? sessione->monitor_prodotto : NULL;
}

void mutter_monitor_conteggi(const MutterSessione *sessione, guint *prima, guint *dopo)
{
	if (prima)
		*prima = sessione ? sessione->monitor_prima : 0;
	if (dopo)
		*dopo = sessione ? sessione->monitor_dopo : 0;
}

void mutter_chiudi(MutterSessione *sessione)
{
	if (!sessione)
		return;

	/* The CONTROL is stopped, and the capture follows it: Mutter refuses to stop
	 * an associated capture directly. */
	if (sessione->bus && sessione->controllo)
	{
		g_autoptr(GError) sbaglio = NULL;
		/* SHORT wait: we almost always get here because the graphical session has
		 * already gone, and waiting fifteen seconds for an answer that cannot
		 * arrive would hold up whoever is tearing down. */
		g_autoptr(GVariant) risposta = g_dbus_connection_call_sync(
		    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL,
		    NULL, G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &sbaglio);

		if (!risposta)
			registro_dettaglio(AREA, "closing the control session: %s", sbaglio->message);
	}

	if (sessione->eis >= 0)
		close(sessione->eis);

	g_clear_object(&sessione->bus);
	g_free(sessione->controllo);
	g_free(sessione->cattura);
	g_free(sessione->flusso);
	g_free(sessione->mapping_id);
	g_free(sessione->mapping_id_pubblicato);
	g_free(sessione->monitor);
	g_free(sessione->monitor_prodotto);
	for (guint i = 0; i < MONITOR_MAX; i++)
		g_free(sessione->prima[i]);
	g_free(sessione);
}
