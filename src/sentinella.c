/*
 * sentinella.c — l'emittente che mancava a `0x04` e `0x05`.
 *
 * Il perche' di ogni scelta sta in `sentinella.h`, che si legge prima di questo
 * file.  Qui c'e' solo il come.
 */
#include "sentinella.h"

#include <gio/gio.h>
#include <string.h>
#include <unistd.h>

#include "registro.h"

#define NOME_LOGIND "org.freedesktop.login1"
#define PERCORSO_LOGIND "/org/freedesktop/login1"
#define IFACE_MANAGER "org.freedesktop.login1.Manager"
#define IFACE_SESSIONE "org.freedesktop.login1.Session"

/*
 * ⛔ 300 ms, e non i 5000 di v1.
 *
 * Questa chiamata parte dallo stesso ciclo `poll` che consegna i fotogrammi.  Su
 * una macchina sana logind risponde in meno di un millisecondo — ⚠ e se un
 * giorno non lo facesse, il ritardo lo pagherebbe l'utente in fluidita', non
 * questo modulo in correttezza.  ⇒ Si rinuncia alla risposta invece di far
 * aspettare tutti, e `sentinella_conti()` tiene il numero perche' la scelta si
 * possa RIMISURARE invece di crederla (`CODER.md` §6).
 */
#define ATTESA_MS 300

/* Oltre questa soglia la lentezza si scrive: e' il segnale che la scelta
 * «sincrona» va rifatta a processo aiutante, come PAM (`DECISIONI.md` §1.10). */
#define LENTA_MS 20

/* ⚠ `mir` c'e' perche' c'era in v1: non lo serviamo, ma una sessione Mir e'
 *   grafica lo stesso, e contarla e' piu' prudente che ignorarla. */
static const char *TIPI_GRAFICI[] = { "wayland", "x11", "mir", NULL };

struct sentinella {
	GDBusConnection *bus;
	uint64_t chiamate;
	uint64_t peggior_ms;
	/* ⛔ Una riga sola quando logind smette di rispondere, non una per giro:
	 * un ripasso ogni due secondi riempirebbe il registro di un fatto che
	 * conta una volta (`LEZIONI.md` §6.2-ter: il numero che spiega tutto si
	 * cerca, e in un registro allagato non si trova). */
	bool muto_gia_detto;
};

sentinella *sentinella_apri(void)
{
	g_autoptr(GError) sbaglio = NULL;
	GDBusConnection *bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &sbaglio);
	sentinella *s;

	if (!bus) {
		registro_dice(REG_SESSIONE,
		              "⛔ logind non raggiungibile (%s): la regola di §5.1 "
		              "— sessione locale contro remota, motivi 0x04 e 0x05 "
		              "— NON e' in vigore su questo server",
		              sbaglio ? sbaglio->message : "senza motivo");
		return NULL;
	}

	s = g_new0(sentinella, 1);
	s->bus = bus;
	registro_dice(REG_SESSIONE,
	              "guardiano delle sessioni locali pronto (bus di sistema); il "
	              "discrimine e' il SEAT, non «Remote»");
	return s;
}

void sentinella_chiudi(sentinella *s)
{
	if (!s)
		return;
	g_clear_object(&s->bus);
	g_free(s);
}

static GVariant *chiama(sentinella *s, const char *percorso,
                        const char *interfaccia, const char *metodo,
                        GVariant *argomenti, const GVariantType *tipo)
{
	return g_dbus_connection_call_sync(s->bus, NOME_LOGIND, percorso, interfaccia,
	                                   metodo, argomenti, tipo,
	                                   G_DBUS_CALL_FLAGS_NONE, ATTESA_MS, NULL,
	                                   NULL);
}

/*
 * Il tipo della sessione, se e' grafica, di classe utente, non remota e non in
 * chiusura.  NULL se non lo e' — o se e' sparita fra l'elenco e questa domanda,
 * che e' la condizione di corsa normale di logind e non un guasto.
 */
static char *tipo_se_grafica(sentinella *s, const char *percorso)
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
	bool grafica = false;

	if (!risposta)
		return NULL;
	proprieta = g_variant_get_child_value(risposta, 0);

	v_tipo = g_variant_lookup_value(proprieta, "Type", G_VARIANT_TYPE_STRING);
	v_classe = g_variant_lookup_value(proprieta, "Class", G_VARIANT_TYPE_STRING);
	v_remota = g_variant_lookup_value(proprieta, "Remote", G_VARIANT_TYPE_BOOLEAN);
	v_stato = g_variant_lookup_value(proprieta, "State", G_VARIANT_TYPE_STRING);
	if (!v_tipo || !v_classe)
		return NULL;

	tipo = g_variant_get_string(v_tipo, NULL);
	for (gsize i = 0; TIPI_GRAFICI[i]; i++)
		if (g_strcmp0(tipo, TIPI_GRAFICI[i]) == 0)
			grafica = true;
	if (!grafica)
		return NULL;
	/* `greeter`, `lock-screen` e `background` non sono l'utente al lavoro. */
	if (g_strcmp0(g_variant_get_string(v_classe, NULL), "user") != 0)
		return NULL;
	/* ⚠ La seconda cintura, e oggi non taglia niente: finche' `PAM_RHOST` non
	 *   e' impostato, le nostre sessioni risultano `Remote=no` come le locali.
	 *   ⇒ Il lavoro lo fa il SEAT, e questa riga diventera' vera dopo. */
	if (v_remota && g_variant_get_boolean(v_remota))
		return NULL;
	/* `closing` e' la sessione che se ne sta andando: contarla terrebbe fuori
	 * chi si ricollega proprio mentre quella locale finisce. */
	if (v_stato && g_strcmp0(g_variant_get_string(v_stato, NULL), "closing") == 0)
		return NULL;

	return g_strdup(tipo);
}

bool sentinella_locale(sentinella *s, const char *utente, char *descrizione,
                       size_t quanto)
{
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariantIter) elenco = NULL;
	const char *id, *nome, *seat, *percorso;
	guint32 uid;
	uint64_t inizio;
	uint64_t costo;
	bool trovata = false;

	if (descrizione && quanto)
		descrizione[0] = '\0';
	if (!s || !s->bus || !utente || !utente[0])
		return false;

	inizio = registro_ora_ms();
	risposta = chiama(s, PERCORSO_LOGIND, IFACE_MANAGER, "ListSessions", NULL,
	                  G_VARIANT_TYPE("(a(susso))"));
	if (!risposta) {
		/* ⛔ Si prosegue SENZA la regola invece di chiudere fuori tutti: I1.
		 * ⚠ E si dice una volta sola, non a ogni ripasso. */
		if (!s->muto_gia_detto) {
			registro_dice(REG_SESSIONE,
			              "⛔ logind non ha risposto entro %d ms: la regola "
			              "di §5.1 non e' applicata finche' tace (e questa "
			              "riga non si ripete)",
			              ATTESA_MS);
			s->muto_gia_detto = true;
		}
		return false;
	}
	if (s->muto_gia_detto) {
		registro_dice(REG_SESSIONE, "logind ha ripreso a rispondere");
		s->muto_gia_detto = false;
	}

	g_variant_get(risposta, "(a(susso))", &elenco);
	while (!trovata &&
	       g_variant_iter_next(elenco, "(&su&s&s&o)", &id, &uid, &nome, &seat,
	                           &percorso)) {
		g_autofree char *tipo = NULL;

		/* ⭐ Le due condizioni che scartano quasi tutto stanno GIA' nell'elenco,
		 *    e si applicano senza aprire niente: l'utente sbagliato, e — ⛔ la
		 *    riga che porta tutto il peso — **il seat vuoto**, che e' quel che
		 *    rende locale una sessione e che le nostre non hanno. */
		if (g_strcmp0(nome, utente) != 0)
			continue;
		if (!seat || !*seat)
			continue;

		tipo = tipo_se_grafica(s, percorso);
		if (!tipo)
			continue;

		trovata = true;
		if (descrizione && quanto)
			g_snprintf(descrizione, quanto, "sessione %s, %s su %s", id, tipo,
			           seat);
	}

	costo = registro_ora_ms() - inizio;
	s->chiamate++;
	if (costo > s->peggior_ms)
		s->peggior_ms = costo;
	if (costo >= LENTA_MS)
		registro_dice(REG_SESSIONE,
		              "⚠ logind ha impiegato %llu ms per l'elenco delle "
		              "sessioni: se si ripete, questa domanda va spostata su un "
		              "processo aiutante come PAM",
		              (unsigned long long) costo);

	return trovata;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ LE DUE VERIFICHE DEL FIGLIO — `DECISIONI.md` §4.3-bis e §4.7.
 *
 * ⛔ LE FA IL FIGLIO E NON IL SERVER, e non e' un dettaglio di dove sta il
 *    codice: `[M]` 15 agosto 2026, con la regola polkit in vigore, `CanPowerOff`
 *    risponde **«no» a `nicfio`** e **«yes» a root** — perche' logind guarda
 *    `CAP_SYS_BOOT` PRIMA di interrogare polkit.  ⇒ Il server, che e' root, si
 *    sentirebbe rispondere di si' sempre, e scriverebbe «verificato» avendo
 *    guardato la cosa sbagliata.  Un controllo fatto dal posto sbagliato e'
 *    peggio di un controllo che manca.
 */
static const char *AZIONI[] = { "CanPowerOff", "CanReboot", "CanSuspend", "CanHibernate", NULL };

bool sentinella_spegnimento_vietato(sentinella *s, char *dettaglio, size_t quanto)
{
	bool tutto_no = true;

	if (dettaglio && quanto)
		dettaglio[0] = '\0';
	if (!s || !s->bus)
		return false;

	for (int i = 0; AZIONI[i]; i++) {
		g_autoptr(GVariant) risposta =
			chiama(s, PERCORSO_LOGIND, IFACE_MANAGER, AZIONI[i], NULL,
		               G_VARIANT_TYPE("(s)"));
		const char *esito = NULL;
		char pezzo[64];

		if (!risposta) {
			tutto_no = false;
			esito = "(nessuna risposta)";
		} else {
			g_variant_get(risposta, "(&s)", &esito);
			/* ⛔ «challenge» NON basta: vuol dire «si', chiedendo una
			 *    parola d'ordine», e su GNOME **mostra la voce nel menu**
			 *    invece di toglierla. */
			if (g_strcmp0(esito, "no") != 0)
				tutto_no = false;
		}
		g_snprintf(pezzo, sizeof pezzo, "%s=%s ", AZIONI[i], esito ? esito : "?");
		if (dettaglio && quanto)
			g_strlcat(dettaglio, pezzo, quanto);
	}
	return tutto_no;
}

bool sentinella_senza_seat(sentinella *s, char *quale, size_t quanto)
{
	g_autoptr(GVariant) risposta = NULL;
	g_autofree char *percorso = NULL;
	g_autoptr(GVariant) proprieta = NULL;
	g_autoptr(GVariant) valore = NULL;
	const char *seat = NULL;

	if (quale && quanto)
		quale[0] = '\0';
	if (!s || !s->bus)
		return false;

	risposta = chiama(s, PERCORSO_LOGIND, IFACE_MANAGER, "GetSessionByPID",
	                  g_variant_new("(u)", (guint32)getpid()), G_VARIANT_TYPE("(o)"));
	if (!risposta) {
		/* ⛔ NESSUNA SESSIONE e' peggio di «con un seat»: senza sessione il
		 *    compositore non parte affatto (`DECISIONI.md` §1.10-ter). */
		if (quale && quanto)
			g_strlcpy(quale, "nessuna sessione logind", quanto);
		return false;
	}
	g_variant_get(risposta, "(o)", &percorso);

	proprieta = chiama(s, percorso, "org.freedesktop.DBus.Properties", "Get",
	                   g_variant_new("(ss)", IFACE_SESSIONE, "Seat"), G_VARIANT_TYPE("(v)"));
	if (!proprieta)
		return false;
	g_variant_get(proprieta, "(v)", &valore);
	/* La proprieta' `Seat` e' una struttura `(so)`: id e percorso. */
	if (g_variant_is_of_type(valore, G_VARIANT_TYPE("(so)")))
		g_variant_get(valore, "(&so)", &seat, NULL);
	else if (g_variant_is_of_type(valore, G_VARIANT_TYPE_STRING))
		seat = g_variant_get_string(valore, NULL);

	if (quale && quanto)
		g_snprintf(quale, quanto, "sessione %s, seat «%s»", percorso,
		           seat && *seat ? seat : "(nessuno)");
	return !seat || !*seat;
}

void sentinella_conti(const sentinella *s, uint64_t *chiamate,
                      uint64_t *peggior_ms)
{
	if (chiamate)
		*chiamate = s ? s->chiamate : 0;
	if (peggior_ms)
		*peggior_ms = s ? s->peggior_ms : 0;
}
