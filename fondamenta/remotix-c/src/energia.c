#include "energia.h"

#include <gio/gio.h>

#include "registro.h"
#include "sessione.h"

#define NOME "org.kde.Solid.PowerManagement"
#define PERCORSO "/org/kde/Solid/PowerManagement/PolicyAgent"
#define IFACE "org.kde.Solid.PowerManagement.PolicyAgent"

/*
 * 4 = `ChangeScreenSettings`, e implica `InterruptSession`.
 *
 * ⛔ NON E' 1.  I tipi sono una maschera di bit — `InterruptSession` vale 1,
 *    `ChangeScreenSettings` 4 — e chiedere il primo NON ferma lo schermo: e'
 *    esattamente la differenza fra questa via e quella freedesktop, che sembra
 *    la stessa e non lo e' (`kde.md` §10.2).
 */
#define TIPI_INIBITI 4

/*
 * ⛔ POWERDEVIL NON C'E' ANCORA QUANDO IL PALCO SI MONTA, e chiederglielo una
 *    volta sola significa non chiederglielo mai.
 *
 *    L'ordine di avvio di Plasma e' `plasma-kwin_wayland` → kcminit → kded6 →
 *    ksmserver → plasmashell → `plasma-core.target` → **`plasma-workspace.target`
 *    (powerdevil, kglobalaccel, …)** (`kde.md` §6.2).  Il palco si monta appena
 *    il compositore risponde, cioe' al PRIMO anello: al terzultimo mancano
 *    ancora secondi.
 *
 *    Misurato l'8 agosto 2026, alla prima prova della voce 3: «The name
 *    org.kde.Solid.PowerManagement was not provided by any .service files» —
 *    che e' l'errore di un nome NON ATTIVABILE, cioe' «non esiste ancora», non
 *    «non esistera' mai».  Si aspetta.
 *
 * ⚠ E si aspetta su un thread suo, non trattenendo il montaggio: un desktop che
 *   compare due secondi dopo perche' si stava aspettando un servizio di energia
 *   sarebbe un prezzo assurdo per una cosa che serve fra dieci minuti.
 */
#define TENTATIVI 30
#define FRA_UN_TENTATIVO_E_L_ALTRO_MS 2000

struct Energia
{
	GThread *thread;
	volatile gint fermare;

	GMutex lucchetto;
	guint gettone;
	gboolean preso;
};

static gboolean prova_a_inibire(Energia *energia)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GError) sbaglio = NULL;
	guint gettone = 0;

	if (!bus)
		return FALSE;

	risposta = g_dbus_connection_call_sync(
	    bus, NOME, PERCORSO, IFACE, "AddInhibition",
	    g_variant_new("(uss)", (guint32) TIPI_INIBITI, "REMOTIX",
	                  "una sessione remota e' in corso"),
	    G_VARIANT_TYPE("(u)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &sbaglio);
	if (!risposta)
	{
		traccia("inibizione non ancora possibile: %s", sbaglio->message);
		return FALSE;
	}

	g_variant_get(risposta, "(u)", &gettone);
	g_mutex_lock(&energia->lucchetto);
	energia->gettone = gettone;
	energia->preso = TRUE;
	g_mutex_unlock(&energia->lucchetto);
	informazione("schermo della sessione tenuto acceso (inibizione %u)", gettone);
	return TRUE;
}

static gpointer thread_energia(gpointer dati)
{
	Energia *energia = dati;

	for (int i = 0; i < TENTATIVI; i++)
	{
		if (g_atomic_int_get(&energia->fermare))
			return NULL;
		if (prova_a_inibire(energia))
			return NULL;
		g_usleep(FRA_UN_TENTATIVO_E_L_ALTRO_MS * 1000);
	}
	/*
	 * Un minuto e non e' arrivato: powerdevil su questa macchina non c'e'.  Non
	 * si fallisce niente — si dichiara, perche' il sintomo arrivera' fra dieci
	 * minuti sotto forma di schermo nero, e a quel punto nessuno lo collegherebbe
	 * a questo.
	 */
	avviso("il gestore dell'energia non ha risposto in %d secondi: lo schermo della sessione "
	       "remota si spegnera' da se' dopo dieci minuti (kde.md §10.2)",
	       TENTATIVI * FRA_UN_TENTATIVO_E_L_ALTRO_MS / 1000);
	return NULL;
}

Energia *energia_inibisci(TipoCompositore tipo)
{
	Energia *energia;

	if (tipo != COMPOSITORE_KWIN)
		return NULL;

	energia = g_new0(Energia, 1);
	g_mutex_init(&energia->lucchetto);
	energia->thread = g_thread_new("remotix-energia", thread_energia, energia);
	return energia;
}

void energia_rilascia(Energia *energia)
{
	g_autoptr(GDBusConnection) bus = NULL;
	gboolean preso;
	guint gettone = 0;

	if (!energia)
		return;

	g_atomic_int_set(&energia->fermare, 1);
	if (energia->thread)
		g_thread_join(energia->thread);

	g_mutex_lock(&energia->lucchetto);
	preso = energia->preso;
	gettone = energia->gettone;
	g_mutex_unlock(&energia->lucchetto);

	if (preso)
	{
		bus = sessione_bus(NULL);
		if (bus)
			g_dbus_connection_call(bus, NOME, PERCORSO, IFACE, "ReleaseInhibition",
			                       g_variant_new("(u)", gettone), NULL, G_DBUS_CALL_FLAGS_NONE,
			                       2000, NULL, NULL, NULL);
	}
	g_mutex_clear(&energia->lucchetto);
	g_free(energia);
}
