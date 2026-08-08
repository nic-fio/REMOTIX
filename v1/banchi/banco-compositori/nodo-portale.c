/*
 * nodo-portale — apre una cattura via xdg-desktop-portal e stampa il nodo
 * PipeWire, poi resta vivo finche' non lo si uccide.
 *
 * Serve ai compositori wlroots (sway, labwc, wayfire), che a differenza di
 * Mutter e di KWin non hanno un'interfaccia propria per la cattura: la loro
 * strada e' `wlr-screencopy`, e chi la incarta in un nodo PipeWire e' il
 * portale (`xdg-desktop-portal-wlr`).
 *
 * ⚠ §2 di SPECIFICA.md il portale lo RIFIUTA per il prodotto, perche' chiede un
 *   permesso a video e REMOTIX e' un servizio non presidiato.  Qui non si sta
 *   costruendo il prodotto: si sta misurando un compositore, e il portale di
 *   wlroots non chiede niente se gli si dichiara l'uscita nel suo file di
 *   configurazione.  La differenza va tenuta a mente leggendo i numeri: per
 *   wlroots questa e' la strada del BANCO, non quella che REMOTIX prenderebbe.
 *
 * La sessione del portale vive quanto questo processo: chiuderlo chiude il
 * flusso.  Per questo stampa il nodo e poi dorme.
 */

#include <gio/gio.h>
#include <stdio.h>
#include <string.h>

#define PORTALE "org.freedesktop.portal.Desktop"
#define PERCORSO "/org/freedesktop/portal/desktop"
#define IFACE "org.freedesktop.portal.ScreenCast"

typedef struct
{
	GMainLoop *ciclo;
	GDBusConnection *bus;
	char *sessione;
	guint32 nodo;
	gboolean guasto;
	GVariant *risultati;
} Attesa;

static void su_risposta(GDBusConnection *bus, const char *mittente, const char *percorso,
                        const char *iface, const char *segnale, GVariant *parametri, gpointer d)
{
	Attesa *a = d;
	guint32 codice = 1;
	g_autoptr(GVariant) risultati = NULL;

	g_variant_get(parametri, "(u@a{sv})", &codice, &risultati);
	if (codice != 0)
	{
		fprintf(stderr, "il portale ha risposto %u (0 = va bene)\n", codice);
		a->guasto = TRUE;
	}
	else
	{
		if (a->risultati)
			g_variant_unref(a->risultati);
		a->risultati = g_variant_ref(risultati);
	}
	g_main_loop_quit(a->ciclo);
}

/* Ogni metodo del portale torna subito un «handle» e la risposta vera arriva
 * come segnale su quel percorso.  Ci si iscrive PRIMA di chiamare, o si
 * aspetta per sempre una risposta gia' passata — e' la stessa trappola del
 * `PipeWireStreamAdded` di Mutter (§7.3 di REFERENCE.md). */
static GVariant *chiama_e_aspetta(Attesa *a, const char *metodo, GVariant *argomenti,
                                  const char *gettone)
{
	g_autofree char *unico = NULL;
	g_autofree char *richiesta = NULL;
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	guint iscrizione;

	unico = g_strdup(g_dbus_connection_get_unique_name(a->bus) + 1);
	g_strdelimit(unico, ".", '_');
	richiesta = g_strdup_printf("/org/freedesktop/portal/desktop/request/%s/%s", unico, gettone);

	iscrizione = g_dbus_connection_signal_subscribe(a->bus, PORTALE,
	                                                "org.freedesktop.portal.Request", "Response",
	                                                richiesta, NULL, G_DBUS_SIGNAL_FLAGS_NONE,
	                                                su_risposta, a, NULL);

	risposta = g_dbus_connection_call_sync(a->bus, PORTALE, PERCORSO, IFACE, metodo, argomenti,
	                                       G_VARIANT_TYPE("(o)"), G_DBUS_CALL_FLAGS_NONE, 30000,
	                                       NULL, &sbaglio);
	if (!risposta)
	{
		fprintf(stderr, "%s rifiutata: %s\n", metodo, sbaglio->message);
		g_dbus_connection_signal_unsubscribe(a->bus, iscrizione);
		return NULL;
	}

	a->guasto = FALSE;
	g_clear_pointer(&a->risultati, g_variant_unref);
	g_main_loop_run(a->ciclo);
	g_dbus_connection_signal_unsubscribe(a->bus, iscrizione);

	if (a->guasto)
		return NULL;
	return a->risultati ? g_variant_ref(a->risultati) : NULL;
}

int main(int argc, char **argv)
{
	Attesa a = { 0 };
	g_autoptr(GError) sbaglio = NULL;
	GVariantBuilder opzioni;
	g_autoptr(GVariant) esito = NULL;

	a.ciclo = g_main_loop_new(NULL, FALSE);
	a.bus = g_bus_get_sync(G_BUS_TYPE_SESSION, NULL, &sbaglio);
	if (!a.bus)
	{
		fprintf(stderr, "niente bus di sessione: %s\n", sbaglio->message);
		return 1;
	}

	/* --- 1. la sessione ------------------------------------------------ */
	g_variant_builder_init(&opzioni, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&opzioni, "{sv}", "handle_token", g_variant_new_string("misura1"));
	g_variant_builder_add(&opzioni, "{sv}", "session_handle_token",
	                      g_variant_new_string("misuras"));
	esito = chiama_e_aspetta(&a, "CreateSession", g_variant_new("(a{sv})", &opzioni), "misura1");
	if (!esito || !g_variant_lookup(esito, "session_handle", "s", &a.sessione))
	{
		fprintf(stderr, "il portale non ha creato la sessione\n");
		return 1;
	}
	g_clear_pointer(&esito, g_variant_unref);

	/* --- 2. che cosa si cattura: un monitor, cursore come metadato ----- */
	g_variant_builder_init(&opzioni, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&opzioni, "{sv}", "handle_token", g_variant_new_string("misura2"));
	g_variant_builder_add(&opzioni, "{sv}", "types", g_variant_new_uint32(1));
	g_variant_builder_add(&opzioni, "{sv}", "multiple", g_variant_new_boolean(FALSE));
	g_variant_builder_add(&opzioni, "{sv}", "cursor_mode", g_variant_new_uint32(2));
	esito = chiama_e_aspetta(&a, "SelectSources",
	                         g_variant_new("(oa{sv})", a.sessione, &opzioni), "misura2");
	if (!esito)
	{
		fprintf(stderr, "il portale non ha accettato la sorgente\n");
		return 1;
	}
	g_clear_pointer(&esito, g_variant_unref);

	/* --- 3. via, e il nodo arriva nei risultati ------------------------ */
	g_variant_builder_init(&opzioni, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&opzioni, "{sv}", "handle_token", g_variant_new_string("misura3"));
	esito = chiama_e_aspetta(&a, "Start", g_variant_new("(osa{sv})", a.sessione, "", &opzioni),
	                         "misura3");
	if (!esito)
	{
		fprintf(stderr, "il portale non ha avviato la cattura\n");
		return 1;
	}
	{
		g_autoptr(GVariant) flussi = g_variant_lookup_value(esito, "streams", NULL);
		GVariantIter iter;
		guint32 nodo = 0;
		g_autoptr(GVariant) proprieta = NULL;

		if (!flussi)
		{
			fprintf(stderr, "nessun flusso nella risposta\n");
			return 1;
		}
		g_variant_iter_init(&iter, flussi);
		if (!g_variant_iter_next(&iter, "(u@a{sv})", &nodo, &proprieta))
		{
			fprintf(stderr, "elenco dei flussi vuoto\n");
			return 1;
		}
		printf("%u\n", nodo);
		fflush(stdout);
		fprintf(stderr, "  portale: nodo PipeWire %u\n", nodo);
	}

	/* La sessione del portale muore con questo processo. */
	g_main_loop_run(a.ciclo);
	return 0;
}
