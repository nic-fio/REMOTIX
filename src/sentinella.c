/*
 * sentinella.c — the sender that `0x04` and `0x05` were missing.
 *
 * The why of every choice is in `sentinella.h`, which is read before this
 * file.  Here there is only the how.
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
 * ⛔ 300 ms, and not v1's 5000.
 *
 * This call leaves from the same `poll` loop that delivers the frames.  On
 * a healthy machine logind answers in less than a millisecond — ⚠ and if one
 * day it did not, the user would pay the delay in smoothness, not
 * this module in correctness.  ⇒ The answer is given up instead of making
 * everyone wait, and `sentinella_conti()` keeps the number so that the choice can
 * be RE-MEASURED instead of believed (`CODER.md` §6).
 */
#define ATTESA_MS 300

/* Beyond this threshold the slowness is written: it is the signal that the
 * «synchronous» choice must be redone as a helper process, like PAM (`DECISIONI.md` §1.10).
 *
 * ⛔⛔ IT WAS 20 ms, AND IT WOULD NEVER HAVE SPOKEN — `[M]` 25 August 2026, §6.13: on
 *      this machine `ListSessions` costs **2.4-2.6 ms** median and the
 *      worst call seen anywhere is **13.14 ms**.  ⇒ A threshold at 20 sits
 *      ABOVE the worst measured case: it is an alarm that by construction never
 *      rings, that is form E1 («an instrument that exists and does not speak»).
 * ⭐ 10 ms is above the median by a factor of **four** — it is not noise — and
 *    below the worst measured: the first time logind really slows down, the
 *    line comes out.  ⚠ And it is not the only belt: `sentinella_conti()` brings the
 *    WORST to the log once a minute, so the number is there even
 *    when this threshold is silent. */
#define LENTA_MS 10

/* ⚠ `mir` is here because it was in v1: we do not serve it, but a Mir session is
 *   graphical all the same, and counting it is more prudent than ignoring it. */
static const char *TIPI_GRAFICI[] = { "wayland", "x11", "mir", NULL };

struct sentinella {
	GDBusConnection *bus;
	uint64_t chiamate;
	uint64_t peggior_ms;
	/* ⛔ A single line when logind stops answering, not one per turn:
	 * a re-check every two seconds would fill the log with a fact that
	 * counts once (`LEZIONI.md` §6.2-ter: the number that explains everything is
	 * searched for, and in a flooded log it is not found). */
	bool muto_gia_detto;
};

sentinella *sentinella_apri(void)
{
	g_autoptr(GError) sbaglio = NULL;
	GDBusConnection *bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &sbaglio);
	sentinella *s;

	if (!bus) {
		registro_dice(REG_SESSIONE,
		              "⛔ logind unreachable (%s): the rule of §5.1 "
		              "— local session against remote, reasons 0x04 and 0x05 "
		              "— is NOT in force on this server",
		              sbaglio ? sbaglio->message : "no reason given");
		return NULL;
	}

	s = g_new0(sentinella, 1);
	s->bus = bus;
	registro_dice(REG_SESSIONE,
	              "local session guardian ready (system bus); the "
	              "discriminant is the SEAT, not «Remote»");
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
 * The type of the session, if it is graphical, of user class, not remote and not
 * closing.  NULL if it is not — or if it vanished between the list and this question,
 * which is logind's normal race condition and not a fault.
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
	/* `greeter`, `lock-screen` and `background` are not the user at work. */
	if (g_strcmp0(g_variant_get_string(v_classe, NULL), "user") != 0)
		return NULL;
	/* ⚠ The second belt, and today it cuts nothing: until `PAM_RHOST` is
	 *   set, our sessions show `Remote=no` like the local ones.
	 *   ⇒ The SEAT does the work, and this line will become true later. */
	if (v_remota && g_variant_get_boolean(v_remota))
		return NULL;
	/* `closing` is the session that is going away: counting it would lock out
	 * whoever reconnects right while the local one ends. */
	if (v_stato && g_strcmp0(g_variant_get_string(v_stato, NULL), "closing") == 0)
		return NULL;

	return g_strdup(tipo);
}

/*
 * ⭐⭐⭐ THE HEART, AND THERE IS ONLY ONE — `sentinella.h` carries the why in
 *       full (finding P4, §6.13: `N × D` becoming `D`).
 *
 * ⛔ `sentinella_locale()` below is this same function with `quanti = 1`,
 *    and not a second draft: two drafts of the same question are two
 *    truths that the day they diverge do not give red, they give a different
 *    answer depending on who asks (`CODER.md` §2-bis, «one road only»).
 */
size_t sentinella_locali(sentinella *s, const char *const *utenti, size_t quanti,
                         bool *locale, char *quali, size_t larghezza)
{
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariantIter) elenco = NULL;
	const char *id, *nome, *seat, *percorso;
	guint32 uid;
	uint64_t inizio;
	uint64_t costo;
	size_t trovate = 0;
	size_t restano;

	/* ⛔ It is ALWAYS cleared, and first: a vector left as it was would tell the
	 *    caller the answer of the previous re-check, which is the worst lie —
	 *    indistinguishable from a fresh answer. */
	for (size_t k = 0; k < quanti; k++) {
		locale[k] = false;
		if (quali && larghezza)
			quali[k * larghezza] = '\0';
	}
	if (!s || !s->bus || !utenti || !quanti)
		return 0;
	restano = quanti;

	inizio = registro_ora_ms();
	risposta = chiama(s, PERCORSO_LOGIND, IFACE_MANAGER, "ListSessions", NULL,
	                  G_VARIANT_TYPE("(a(susso))"));
	if (!risposta) {
		/* ⛔ Carry on WITHOUT the rule instead of locking everyone out: I1.
		 * ⚠ And say it once only, not at every re-check. */
		if (!s->muto_gia_detto) {
			registro_dice(REG_SESSIONE,
			              "⛔ logind did not answer within %d ms: the rule "
			              "of §5.1 is not applied while it is silent (and this "
			              "line is not repeated)",
			              ATTESA_MS);
			s->muto_gia_detto = true;
		}
		return 0;
	}
	if (s->muto_gia_detto) {
		registro_dice(REG_SESSIONE, "logind is answering again");
		s->muto_gia_detto = false;
	}

	g_variant_get(risposta, "(a(susso))", &elenco);
	/* ⭐ Exit as soon as ALL have an answer (`restano == 0`), not as soon as one
	 *    has it: the question is now for N tenants, and stopping at the first
	 *    would leave the others with a `false` that looks like an answer. */
	while (restano &&
	       g_variant_iter_next(elenco, "(&su&s&s&o)", &id, &uid, &nome, &seat,
	                           &percorso)) {
		g_autofree char *tipo = NULL;
		bool serve = false;

		/* ⭐ The two conditions that discard almost everything are ALREADY in the list,
		 *    and apply without opening anything: the wrong user, and — ⛔ the
		 *    line that carries all the weight — **the empty seat**, which is what
		 *    makes a session local and which ours do not have.
		 * ⛔ And the comparison is against ALL the names asked, in memory: it is the
		 *    loop that replaced the N calls to logind. */
		if (!seat || !*seat)
			continue;
		for (size_t k = 0; k < quanti; k++)
			if (!locale[k] && g_strcmp0(nome, utenti[k]) == 0)
				serve = true;
		if (!serve)
			continue;

		/* ⚠ It is the only call left inside the loop, and it does not grow with the
		 *   tenants: it is made only for a session that ALREADY has a seat and a name
		 *   we care about — that is for the real local session, which is what
		 *   we are looking for.  On a headless machine it never happens. */
		tipo = tipo_se_grafica(s, percorso);
		if (!tipo)
			continue;

		for (size_t k = 0; k < quanti; k++) {
			if (locale[k] || g_strcmp0(nome, utenti[k]) != 0)
				continue;
			locale[k] = true;
			trovate++;
			restano--;
			if (quali && larghezza)
				g_snprintf(quali + k * larghezza, larghezza,
				           "session %s, %s on %s", id, tipo, seat);
		}
	}

	costo = registro_ora_ms() - inizio;
	s->chiamate++;
	if (costo > s->peggior_ms)
		s->peggior_ms = costo;
	if (costo >= LENTA_MS)
		registro_dice(REG_SESSIONE,
		              "⚠ logind took %llu ms for the list of "
		              "sessions (%zu tenants in a single question): if it "
		              "repeats, this question must move to a helper "
		              "process like PAM",
		              (unsigned long long) costo, quanti);

	return trovate;
}

bool sentinella_locale(sentinella *s, const char *utente, char *descrizione,
                       size_t quanto)
{
	bool locale = false;
	const char *uno = utente;

	if (descrizione && quanto)
		descrizione[0] = '\0';
	if (!utente || !utente[0])
		return false;
	/* ⛔ One road only: the question for one is the question for all with N = 1.
	 *    ⚠ `quali` may be NULL, and then `larghezza` is not looked at. */
	sentinella_locali(s, &uno, 1, &locale, descrizione, descrizione ? quanto : 0);
	return locale;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ THE CHILD'S TWO CHECKS — `DECISIONI.md` §4.3-bis and §4.7.
 *
 * ⛔ THE CHILD DOES THEM AND NOT THE SERVER, and it is not a detail of where the
 *    code sits: `[M]` 15 August 2026, with the polkit rule in force, `CanPowerOff`
 *    answers **«no» to `nicfio`** and **«yes» to root** — because logind looks at
 *    `CAP_SYS_BOOT` BEFORE asking polkit.  ⇒ The server, which is root, would
 *    always be answered yes, and would write «verified» having
 *    looked at the wrong thing.  A check made from the wrong place is
 *    worse than a missing check.
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
			esito = "(no answer)";
		} else {
			g_variant_get(risposta, "(&s)", &esito);
			/* ⛔ «challenge» is NOT enough: it means «yes, asking for a
			 *    password», and on GNOME it **shows the menu entry**
			 *    instead of removing it. */
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
		/* ⛔ NO SESSION is worse than «with a seat»: without a session the
		 *    compositor does not start at all (`DECISIONI.md` §1.10-ter). */
		if (quale && quanto)
			g_strlcpy(quale, "no logind session", quanto);
		return false;
	}
	g_variant_get(risposta, "(o)", &percorso);

	proprieta = chiama(s, percorso, "org.freedesktop.DBus.Properties", "Get",
	                   g_variant_new("(ss)", IFACE_SESSIONE, "Seat"), G_VARIANT_TYPE("(v)"));
	if (!proprieta)
		return false;
	g_variant_get(proprieta, "(v)", &valore);
	/* The `Seat` property is a `(so)` structure: id and path. */
	if (g_variant_is_of_type(valore, G_VARIANT_TYPE("(so)")))
		g_variant_get(valore, "(&so)", &seat, NULL);
	else if (g_variant_is_of_type(valore, G_VARIANT_TYPE_STRING))
		seat = g_variant_get_string(valore, NULL);

	if (quale && quanto)
		g_snprintf(quale, quanto, "session %s, seat «%s»", percorso,
		           seat && *seat ? seat : "(none)");
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
