#include "sentinella.h"

#include <gio/gio.h>
#include <string.h>
#include <unistd.h>

#include "registro.h"

#define NOME_LOGIND "org.freedesktop.login1"
#define PERCORSO_LOGIND "/org/freedesktop/login1"
#define IFACE_MANAGER "org.freedesktop.login1.Manager"
#define IFACE_SESSIONE "org.freedesktop.login1.Session"

/* Ogni quanto si ripassa l'elenco, oltre ai segnali. */
#define RIPASSO_MS 2000
#define ATTESA_MS 5000

struct Sentinella
{
	GThread *thread;
	GMainContext *contesto;
	GMainLoop *ciclo;

	SentinellaCambio su_cambio;
	gpointer dati;

	GDBusConnection *bus;
	guint32 uid;
	char *nostra; /* la sessione dentro cui giriamo, da non contare mai */

	/* Lo stato pubblicato, letto da altri thread. */
	GMutex lucchetto;
	gboolean presente;
	char descrizione[128];
};

static const char *TIPI_GRAFICI[] = { "wayland", "x11", "mir", NULL };

static GVariant *chiama(Sentinella *s, const char *percorso, const char *interfaccia,
                        const char *metodo, GVariant *argomenti, const GVariantType *tipo)
{
	return g_dbus_connection_call_sync(s->bus, NOME_LOGIND, percorso, interfaccia, metodo,
	                                   argomenti, tipo, G_DBUS_CALL_FLAGS_NONE, ATTESA_MS, NULL,
	                                   NULL);
}

/*
 * Il tipo della sessione, se e' grafica, dell'utente, e non sta chiudendo.
 *
 * Una sessione puo' sparire fra l'elenco e queste domande: e' la condizione di
 * corsa normale di logind, non un guasto — per questo gli errori qui si
 * ingoiano invece di essere segnalati.
 */
static char *tipo_se_grafica_locale(Sentinella *s, const char *percorso)
{
	g_autoptr(GVariant) risposta =
	    chiama(s, percorso, "org.freedesktop.DBus.Properties", "GetAll",
	           g_variant_new("(s)", IFACE_SESSIONE), G_VARIANT_TYPE("(a{sv})"));
	g_autoptr(GVariant) proprieta = NULL;
	g_autoptr(GVariant) v_tipo = NULL;
	g_autoptr(GVariant) v_classe = NULL;
	g_autoptr(GVariant) v_remota = NULL;
	g_autoptr(GVariant) v_stato = NULL;
	const char *tipo;
	gboolean grafica = FALSE;

	if (!risposta)
		return NULL;
	proprieta = g_variant_get_child_value(risposta, 0);

	v_tipo = g_variant_lookup_value(proprieta, "Type", G_VARIANT_TYPE_STRING);
	v_classe = g_variant_lookup_value(proprieta, "Class", G_VARIANT_TYPE_STRING);
	v_remota = g_variant_lookup_value(proprieta, "Remote", G_VARIANT_TYPE_BOOLEAN);
	v_stato = g_variant_lookup_value(proprieta, "State", G_VARIANT_TYPE_STRING);
	if (!v_tipo || !v_classe || !v_remota)
		return NULL;

	tipo = g_variant_get_string(v_tipo, NULL);
	for (gsize i = 0; TIPI_GRAFICI[i]; i++)
		if (g_strcmp0(tipo, TIPI_GRAFICI[i]) == 0)
			grafica = TRUE;
	if (!grafica)
		return NULL;
	if (g_strcmp0(g_variant_get_string(v_classe, NULL), "user") != 0)
		return NULL;
	if (g_variant_get_boolean(v_remota))
		return NULL;
	/* `closing` e' la sessione che se ne sta andando: contarla terrebbe fuori
	 * chi si ricollega proprio mentre quella locale finisce. */
	if (v_stato && g_strcmp0(g_variant_get_string(v_stato, NULL), "closing") == 0)
		return NULL;

	return g_strdup(tipo);
}

/* Cerca la prima sessione grafica locale del nostro utente. */
static char *cerca(Sentinella *s)
{
	g_autoptr(GVariant) risposta = chiama(s, PERCORSO_LOGIND, IFACE_MANAGER, "ListSessions", NULL,
	                                      G_VARIANT_TYPE("(a(susso))"));
	g_autoptr(GVariantIter) elenco = NULL;
	const char *id, *utente, *seat, *percorso;
	guint32 uid;

	if (!risposta)
	{
		/* Si prosegue senza la regola invece di chiudere fuori tutti. */
		avviso("elenco delle sessioni non ottenuto da logind");
		return NULL;
	}

	g_variant_get(risposta, "(a(susso))", &elenco);
	while (g_variant_iter_next(elenco, "(&su&s&s&o)", &id, &uid, &utente, &seat, &percorso))
	{
		g_autofree char *tipo = NULL;

		/* Le due condizioni che scartano quasi tutto sono gia' nell'elenco: si
		 * applicano senza aprire nulla. */
		if (uid != s->uid || !seat || !*seat)
			continue;
		if (s->nostra && g_strcmp0(id, s->nostra) == 0)
			continue;

		tipo = tipo_se_grafica_locale(s, percorso);
		if (tipo)
			return g_strdup_printf("sessione %s (%s su %s)", id, tipo, seat);
	}
	return NULL;
}

static void pubblica(Sentinella *s, char *trovata)
{
	gboolean cambiato;
	gboolean presente = trovata != NULL;

	g_mutex_lock(&s->lucchetto);
	cambiato = presente != s->presente ||
	           (presente && g_strcmp0(trovata, s->descrizione) != 0);
	if (cambiato)
	{
		s->presente = presente;
		g_strlcpy(s->descrizione, trovata ? trovata : "", sizeof s->descrizione);
	}
	g_mutex_unlock(&s->lucchetto);

	if (!cambiato)
	{
		g_free(trovata);
		return;
	}

	if (presente)
		avviso("e' comparsa una sessione grafica locale: %s", trovata);
	else
		informazione("la sessione grafica locale e' finita: si puo' entrare");

	if (s->su_cambio)
		s->su_cambio(presente, trovata, s->dati);
	g_free(trovata);
}

static gboolean ripassa(gpointer dati)
{
	Sentinella *s = dati;

	pubblica(s, cerca(s));
	return G_SOURCE_CONTINUE;
}

static void su_segnale(GDBusConnection *bus, const char *mittente, const char *percorso,
                       const char *interfaccia, const char *segnale, GVariant *parametri,
                       gpointer dati)
{
	/* Il segnale e il ripasso fanno la stessa cosa: il segnale la fa presto, il
	 * ripasso la fa comunque. */
	ripassa(dati);
}

/* L'identificatore della sessione logind dentro cui giriamo, se ce n'e' una. */
static char *sessione_nostra(Sentinella *s)
{
	g_autoptr(GVariant) risposta =
	    chiama(s, PERCORSO_LOGIND, IFACE_MANAGER, "GetSessionByPID",
	           g_variant_new("(u)", (guint32) getpid()), G_VARIANT_TYPE("(o)"));
	g_autofree char *percorso = NULL;
	g_autoptr(GVariant) proprieta = NULL;
	g_autoptr(GVariant) valore = NULL;

	if (!risposta)
		return NULL; /* avviati da un'unita' systemd: non c'e' nulla da escludere */
	g_variant_get(risposta, "(o)", &percorso);

	proprieta = chiama(s, percorso, "org.freedesktop.DBus.Properties", "Get",
	                   g_variant_new("(ss)", IFACE_SESSIONE, "Id"), G_VARIANT_TYPE("(v)"));
	if (!proprieta)
		return NULL;
	g_variant_get(proprieta, "(v)", &valore);
	return g_variant_dup_string(valore, NULL);
}

static gpointer thread_sentinella(gpointer dati)
{
	Sentinella *s = dati;

	g_main_context_push_thread_default(s->contesto);
	g_main_loop_run(s->ciclo);
	g_main_context_pop_thread_default(s->contesto);
	return NULL;
}

Sentinella *sentinella_avvia(SentinellaCambio su_cambio, gpointer dati)
{
	Sentinella *s = g_new0(Sentinella, 1);
	g_autoptr(GError) sbaglio = NULL;
	char *iniziale;
	GSource *tic;

	s->su_cambio = su_cambio;
	s->dati = dati;
	s->uid = (guint32) geteuid();
	g_mutex_init(&s->lucchetto);
	s->contesto = g_main_context_new();
	s->ciclo = g_main_loop_new(s->contesto, FALSE);

	g_main_context_push_thread_default(s->contesto);

	/* Il bus di SISTEMA: logind non sta su quello di sessione. */
	s->bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &sbaglio);
	if (!s->bus)
	{
		/* Non ci si nasconde dietro un `diagnostica`: significa che una delle
		 * regole di §3.4 non e' in vigore, e chi legge il registro deve poterlo
		 * sapere senza andarlo a cercare. */
		avviso("logind non raggiungibile (%s): la regola della sessione locale NON e' applicata",
		       sbaglio->message);
		g_main_context_pop_thread_default(s->contesto);
		return s;
	}

	s->nostra = sessione_nostra(s);
	diagnostica("sentinella pronta: uid %u, la nostra sessione e' «%s»", s->uid,
	            s->nostra ?: "nessuna");

	/* Il primo controllo si fa PRIMA di tornare: se la macchina ha gia' una
	 * sessione grafica locale, non deve esistere una finestra iniziale in cui
	 * si entra lo stesso. */
	iniziale = cerca(s);
	if (iniziale)
	{
		s->presente = TRUE;
		g_strlcpy(s->descrizione, iniziale, sizeof s->descrizione);
		avviso("c'e' gia' una sessione grafica locale (%s): le connessioni saranno rifiutate",
		       iniziale);
		g_free(iniziale);
	}
	else
	{
		informazione("nessuna sessione grafica locale: si puo' entrare");
	}

	g_dbus_connection_signal_subscribe(s->bus, NOME_LOGIND, IFACE_MANAGER, "SessionNew",
	                                   PERCORSO_LOGIND, NULL, G_DBUS_SIGNAL_FLAGS_NONE,
	                                   su_segnale, s, NULL);
	g_dbus_connection_signal_subscribe(s->bus, NOME_LOGIND, IFACE_MANAGER, "SessionRemoved",
	                                   PERCORSO_LOGIND, NULL, G_DBUS_SIGNAL_FLAGS_NONE,
	                                   su_segnale, s, NULL);

	tic = g_timeout_source_new(RIPASSO_MS);
	g_source_set_callback(tic, ripassa, s, NULL);
	g_source_attach(tic, s->contesto);
	g_source_unref(tic);

	g_main_context_pop_thread_default(s->contesto);

	s->thread = g_thread_new("remotix-sentinella", thread_sentinella, s);
	return s;
}

gboolean sentinella_locale_presente(Sentinella *sentinella, char *descrizione, gsize quanto)
{
	gboolean presente;

	if (!sentinella)
		return FALSE;
	g_mutex_lock(&sentinella->lucchetto);
	presente = sentinella->presente;
	if (descrizione && quanto)
		g_strlcpy(descrizione, sentinella->descrizione, quanto);
	g_mutex_unlock(&sentinella->lucchetto);
	return presente;
}

void sentinella_ferma(Sentinella *sentinella)
{
	if (!sentinella)
		return;
	if (sentinella->ciclo)
		g_main_loop_quit(sentinella->ciclo);
	if (sentinella->thread)
		g_thread_join(sentinella->thread);
	g_clear_pointer(&sentinella->ciclo, g_main_loop_unref);
	g_clear_pointer(&sentinella->contesto, g_main_context_unref);
	g_clear_object(&sentinella->bus);
	g_mutex_clear(&sentinella->lucchetto);
	g_free(sentinella->nostra);
	g_free(sentinella);
}
