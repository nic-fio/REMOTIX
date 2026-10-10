/*
 * appunti.c — the SESSION's clipboard, that is Mutter's.
 *
 * ⛔ The four traps, the thread contract and the reason for "text only"
 *    are in `appunti.h`, and are not repeated here: this file IMPLEMENTS them, and
 *    every point where one of them bites is marked on the spot.
 *
 * ⭐ Descends from `fondamenta/remotix-c/src/appunti_mutter.c` (450 lines, measured on 5
 *    August 2026 against GNOME 48.7).  ⛔ The differences, all intended:
 *
 *      · **text only**: v1 exchanged lists of MIME types with the stitcher and
 *        also carried images and `text/html` (`fondamenta/…/scambio.c`).  Here the types
 *        live in `TIPI_TESTO` and do not leave this file;
 *      · **it is read here**, on the clipboard thread, instead of handing over the
 *        types and being called back: the §7.4 announcement carries the length, and the
 *        length is not known without reading;
 *      · **the ceiling and UTF-8 validity are checked here**, where the text
 *        still exists whole — not after crossing a socket;
 *      · **the last text is remembered**, not the last list of types: it is what
 *        whoever reconnects needs, and it is already ready to send.
 */
#include "appunti.h"
#include "appunti_kde.h"

#include <gio/gunixfdlist.h>
#include <glib-unix.h>
#include <string.h>
#include <unistd.h>

#include "registro.h"

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"

#define ATTESA_CHIAMATA_MS 5000

/* How long we wait for a chunk from the descriptor before declaring it lost: the
 * writer at the other end may be slow, but not mute. */
#define ATTESA_LETTURA_MS 5000

/*
 * ⛔ THE ROW OF TYPES, AND IT IS TRIED WHOLE — trap 3 of `appunti.h`.
 *
 * Mutter's internal clipboard manager keeps **a single MIME type**:
 * when the application that copied dies, of all it had announced only one
 * is left, and it is not necessarily the first of our row.
 * ⇒ We ask in order, and take the first that delivers.
 *
 * ⚠ The order is not indifferent: the first is the one that declares the encoding,
 *   and the other two imply it.  `text/plain` without charset is UTF-8 on
 *   Wayland by convention, ⛔ but **it is validated anyway**: a convention
 *   is not a guarantee, and non-UTF-8 text sent as UTF-8 is a
 *   violation of §5.4 on our side of the wire.
 */
static const char *const TIPI_TESTO[] = {
	"text/plain;charset=utf-8",
	"UTF8_STRING",
	"text/plain",
	NULL,
};

struct Appunti
{
	/* ⭐ PHASE 12 — on KDE all the work is done by `appunti_kde.c`, and this
	 *    shell hands over at the top of every public function: the GNOME branch
	 *    below stays as it was, line by line. */
	AppuntiKde *kde;

	GDBusConnection *bus;
	char *controllo;

	GMainContext *contesto;
	GMainLoop *ciclo;
	GThread *thread;

	/* ⛔ The last text the session copied, kept HERE because it must
	 *    survive the connection: whoever reconnects receives no new
	 *    signal (`appunti.h`, `appunti_ultimo_testo`). */
	char *ultimo;
	size_t ultimo_byte;

	guint sottoscrizione_offerta;
	guint sottoscrizione_richiesta;

	/* The callbacks and their owner.  The lock is held while a callback
	 * runs, so `appunti_ascolta(NULL, NULL, NULL)` waits for whoever is
	 * half way instead of freeing the context under their feet. */
	GMutex lucchetto;
	AppuntiSuTesto su_testo;
	AppuntiSuRichiesta su_richiesta;
	void *dati;
};

static GVariant *chiama(Appunti *appunti, const char *metodo, GVariant *argomenti,
                        const GVariantType *tipo, GError **sbaglio)
{
	return g_dbus_connection_call_sync(appunti->bus, NOME_REMOTE,
	                                   appunti->controllo, IFACE_SESSIONE,
	                                   metodo, argomenti, tipo,
	                                   G_DBUS_CALL_FLAGS_NONE,
	                                   ATTESA_CHIAMATA_MS, NULL, sbaglio);
}

/* As above, but the answer carries a descriptor. */
static int chiama_per_descrittore(Appunti *appunti, const char *metodo,
                                  GVariant *argomenti, GError **sbaglio)
{
	g_autoptr(GUnixFDList) elenco = NULL;
	g_autoptr(GVariant) risposta = NULL;
	gint32 indice = -1;

	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    appunti->bus, NOME_REMOTE, appunti->controllo, IFACE_SESSIONE, metodo,
	    argomenti, G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
	    ATTESA_CHIAMATA_MS, NULL, &elenco, NULL, sbaglio);
	if (!risposta)
		return -1;

	g_variant_get(risposta, "(h)", &indice);
	return g_unix_fd_list_get(elenco, indice, sbaglio);
}

/* ------------------------------------------------------------------ *
 * Reading the text from the session
 * ------------------------------------------------------------------ */

/* Reads a descriptor to the end, with a ceiling and without hanging.
 *
 * ⛔ The ceiling is that of §5.4 **plus one**: reading exactly
 *    `APPUNTI_TETTO` one cannot tell "a text as large as the ceiling", which is
 *    LAWFUL, from "a larger text", which must be refused.  One more byte and the
 *    two cases separate.  ⚠ It is the same form as §5.4's 1 000 000 versus 1 MiB:
 *    a ceiling that makes the borderline case illegal is not that ceiling. */
static GBytes *bevi_tutto(int fd, GError **sbaglio)
{
	GByteArray *raccolto = g_byte_array_new();
	guint8 pezzo[16384];

	while (TRUE)
	{
		GPollFD sonda = { .fd = fd, .events = G_IO_IN | G_IO_HUP | G_IO_ERR };
		gssize letti;

		if (g_poll(&sonda, 1, ATTESA_LETTURA_MS) <= 0)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "whoever had to deliver the clipboard wrote "
			            "nothing for %d ms",
			            ATTESA_LETTURA_MS);
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}

		letti = read(fd, pezzo, sizeof pezzo);
		if (letti == 0)
			break; /* end */
		if (letti < 0)
		{
			if (errno == EINTR)
				continue;
			g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
			            "clipboard read failed: %s", g_strerror(errno));
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}

		if (raccolto->len + (guint)letti > APPUNTI_TETTO)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NO_SPACE,
			            "clipboard over the ceiling of %u bytes (§5.4): left "
			            "where it is, and NOT truncated",
			            APPUNTI_TETTO);
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}
		g_byte_array_append(raccolto, pezzo, (guint)letti);
	}

	return g_byte_array_free_to_bytes(raccolto);
}

/*
 * Tries the row of `TIPI_TESTO` and returns the first text that holds, already
 * validated.  NULL if there is none — and the reason is in the log.
 *
 * ⛔ And the reasons are THREE and stay distinct: there was no text type ·
 *    there was one and the read failed · there was one, it was read, and it was not valid UTF-8.
 *    A single `NULL` for all three would be `LEZIONI.md` §1.9 — "empty and
 *    forbidden with the same face".
 */
static char *leggi_il_testo(Appunti *appunti, size_t *quanti)
{
	for (int i = 0; TIPI_TESTO[i]; i++)
	{
		g_autoptr(GError) sbaglio = NULL;
		g_autoptr(GBytes) dati = NULL;
		const char *inizio;
		gsize byte = 0;
		int fd;

		fd = chiama_per_descrittore(appunti, "SelectionRead",
		                            g_variant_new("(s)", TIPI_TESTO[i]),
		                            &sbaglio);
		if (fd < 0)
		{
			/* ⚠ In detail and not in plain: the row is tried on purpose, and a
			 *   type the session does not have is the NORMAL outcome of the first rounds —
			 *   one line for each would cover the log with noise. */
			registro_dettaglio(REG_APPUNTI,
			                   "«%s» cannot be read from the session (%s): trying the "
			                   "next type",
			                   TIPI_TESTO[i],
			                   sbaglio ? sbaglio->message : "no detail");
			continue;
		}

		dati = bevi_tutto(fd, &sbaglio);
		close(fd);
		if (!dati)
		{
			registro_dice(REG_APPUNTI,
			              "⛔ «%s»: the read did not succeed — %s",
			              TIPI_TESTO[i],
			              sbaglio ? sbaglio->message : "no detail");
			continue;
		}

		inizio = (const char *)g_bytes_get_data(dati, &byte);
		if (byte == 0)
		{
			/* ⚠ Zero bytes is NOT a fault: it is an emptied clipboard, and it is
			 *   exactly what the bench does at the start of every round
			 *   (`LEZIONI.md` §2.3-quinquies).  It is declared and we go on. */
			registro_dettaglio(REG_APPUNTI,
			                   "«%s» delivered zero bytes: the clipboard is "
			                   "empty, not broken",
			                   TIPI_TESTO[i]);
			continue;
		}

		/* ⛔ VALID UTF-8, and it is checked HERE.  `RCP.md` §5.4: "the text MUST
		 *    be UTF-8".  Sending it without looking would mean putting on the
		 *    wire a violation **of ours**, and letting the client discover it — which
		 *    per §3 would have to close the session.  ⇒ The symptom would be "the
		 *    session drops when I copy from that program". */
		if (!g_utf8_validate_len(inizio, byte, NULL))
		{
			registro_dice(REG_APPUNTI,
			              "⛔ «%s» delivered %zu bytes that are NOT valid "
			              "UTF-8: not announced (§5.4).  ⚠ It is not a defect "
			              "of ours nor of the client — it is a program that keeps "
			              "bytes in the clipboard that RCP/1 cannot carry",
			              TIPI_TESTO[i], (size_t)byte);
			continue;
		}

		/* ⛔ AND NO ZEROS IN THE MIDDLE.  From here on the text travels as a
		 *    zero-terminated string — in the socket to the parent and in
		 *    `rcp.c` — and a zero in the middle would cut it **silently**: what
		 *    gets pasted would be shorter than what was copied, and the
		 *    announcement would state the whole length.  ⇒ Two truths about the
		 *    same thing, which is the defect §2.2 forbids in those words. */
		if (memchr(inizio, 0, byte))
		{
			registro_dice(REG_APPUNTI,
			              "⛔ «%s»: %zu bytes with a zero in the middle — not "
			              "announced.  Truncating here would give a text shorter "
			              "than the announcement, that is an announcement that lies",
			              TIPI_TESTO[i], (size_t)byte);
			continue;
		}

		registro_dettaglio(REG_APPUNTI, "read %zu bytes of «%s» from the session",
		                   (size_t)byte, TIPI_TESTO[i]);
		if (quanti)
			*quanti = byte;
		return g_strndup(inizio, byte);
	}

	return NULL;
}

/* ------------------------------------------------------------------ *
 * The two signals
 * ------------------------------------------------------------------ */
static void su_padrone_cambiato(GDBusConnection *bus, const char *mittente,
                                const char *percorso, const char *interfaccia,
                                const char *segnale, GVariant *parametri,
                                gpointer dati)
{
	Appunti *appunti = dati;
	g_autoptr(GVariant) opzioni = NULL;
	g_autoptr(GVariant) tipi = NULL;
	g_autofree const char **mime = NULL;
	g_autofree char *testo = NULL;
	gboolean nostro = FALSE;
	gboolean c_e_testo = FALSE;
	size_t byte = 0;

	(void)bus;
	(void)mittente;
	(void)percorso;
	(void)interfaccia;
	(void)segnale;

	g_variant_get(parametri, "(@a{sv})", &opzioni);

	/*
	 * ⛔ THE RETURN IS RECOGNISED HERE, and it is the first thing to look at —
	 *    trap 4 of `appunti.h`.  Without these three lines we would announce to the
	 *    client what the client just gave us, and the two sides would
	 *    chase each other endlessly.
	 * ⭐ And on GNOME it is **labelled**, not to be guessed: `STUDI.md` §gnome §10
	 *    corrects our old line that spoke of "a heuristic".
	 */
	if (g_variant_lookup(opzioni, "session-is-owner", "b", &nostro) && nostro)
	{
		registro_dettaglio(REG_APPUNTI,
		                   "it is the return of our own offer, not a new "
		                   "copy: not announced");
		return;
	}

	/*
	 * ⛔ IN THE SIGNAL THE TYPES ARE INSIDE A TUPLE, AND IN THE METHODS NOT — trap
	 *    2 of `appunti.h`, measured on 5 August 2026 and it cost one test.
	 *
	 *    `SetSelection` wants `mime-types` as `as`; `SelectionOwnerChanged`
	 *    delivers it as `(as)`.  Whoever reads `as` finds nothing and **returns
	 *    silently**: the clipboard works in one direction only, and nothing in
	 *    the log explains it.
	 *
	 *    ⚠ BOTH forms are accepted, because which of the two arrives
	 *      depends on the Mutter version — and getting it wrong costs one direction
	 *      of the clipboard.  The reference works around it too (`grd-session.c`), which
	 *      says it is not a fantasy of ours.
	 */
	tipi = g_variant_lookup_value(opzioni, "mime-types",
	                              G_VARIANT_TYPE_STRING_ARRAY);
	if (!tipi)
	{
		g_autoptr(GVariant) tupla =
		    g_variant_lookup_value(opzioni, "mime-types", G_VARIANT_TYPE("(as)"));

		if (tupla)
			tipi = g_variant_get_child_value(tupla, 0);
	}
	if (!tipi)
	{
		registro_dice(REG_APPUNTI,
		              "⛔ the session announced a copy without readable "
		              "types: neither `as` nor `(as)`.  ⚠ If it is a third "
		              "form, the clipboard from here on goes one way only "
		              "and this line is the only place where it shows");
		return;
	}
	mime = g_variant_get_strv(tipi, NULL);

	/* ⛔ IS THERE TEXT AMONG THE TYPES?  And if not, we say WHAT there was.
	 *
	 * ⚠ It is the normal case of "I copied an image": it is not a fault, and it is
	 *   the line that explains to the user why that copy did not reach the
	 *   phone.  Without it, the symptom would be "the clipboard sometimes does not
	 *   work" — that is the most expensive defect to diagnose there is. */
	for (int i = 0; mime && mime[i] && !c_e_testo; i++)
		for (int k = 0; TIPI_TESTO[k]; k++)
			if (g_ascii_strcasecmp(mime[i], TIPI_TESTO[k]) == 0)
			{
				c_e_testo = TRUE;
				break;
			}
	if (!c_e_testo)
	{
		g_autofree char *elenco = mime ? g_strjoinv(", ", (GStrv)mime) : NULL;

		registro_dice(REG_APPUNTI,
		              "the session copied something that is not text (%s): "
		              "not announced.  ⚠ `DECISIONI.md` §5-ter.1 — text "
		              "only, and it is a decision, not a technical limit",
		              elenco && *elenco ? elenco : "no type");
		return;
	}

	testo = leggi_il_testo(appunti, &byte);
	if (!testo)
	{
		/* ⚠ `leggi_il_testo` has already written WHICH of the three reasons it was: here
		 *   we only say that the announcement does not leave, or "I read and kept quiet"
		 *   would have the face of "nothing happened". */
		registro_dice(REG_APPUNTI,
		              "⛔ the session copied some text but no type of it could be "
		              "read: no announcement to the client");
		return;
	}

	g_mutex_lock(&appunti->lucchetto);
	g_free(appunti->ultimo);
	appunti->ultimo = g_strdup(testo);
	appunti->ultimo_byte = byte;
	if (appunti->su_testo)
		appunti->su_testo(testo, byte, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);
}

/*
 * ⛔⛔⭐ THE CLIPBOARD THAT WAS ALREADY THERE, AND MUST BE **ASKED FOR** — 21 August 2026.
 *
 * ⚠ Next to here it was written that `EnableClipboard` with empty options makes
 *   a `SelectionOwnerChanged` arrive **at once**, "and it is precisely the announcement
 *   that lets whoever reconnects find the clipboard again".  ⛔ **It is not true**, and the
 *   measurement is from 21 August: `wl-copy` alive and owner in the session,
 *   `wl-paste` reading its text before and after — and in the child's log
 *   **no** read line.  Mutter does not tell a new session who
 *   owns the selection: it only tells the CHANGES from then on.
 *
 * ⇒ And the consequence was big: the client, to be found when someone
 *   over there pastes with the mouse, announces its clipboard as soon as it connects — and
 *   not knowing what was in the session it took the selection over it.
 *   `[M]` `wl-paste` said «TESTO-CHE-ERA-GIA-NEL-DESKTOP» before the
 *   connection and «» after: **by connecting the desktop clipboard
 *   was lost**.  ⛔ In a local session the clipboard does not vanish because
 *   someone came in, and here it must not vanish either.
 *
 * ⭐ So it is asked for, once, as soon as the clipboard is on: if there is an
 *    owner its text is read and announced to the client like
 *    any other copy; if there is nobody, `leggi_il_testo` says so in the
 *    log and nothing happens.
 */
void appunti_leggi_adesso(Appunti *appunti)
{
	g_autofree char *testo = NULL;
	size_t byte = 0;

	if (!appunti)
		return;
	if (appunti->kde) {
		appunti_kde_leggi_adesso(appunti->kde);
		return;
	}

	testo = leggi_il_testo(appunti, &byte);
	if (!testo)
	{
		registro_dettaglio(REG_APPUNTI,
		                   "the session had no clipboard to give us at the time "
		                   "of switching on: it is not a fault");
		return;
	}

	registro_dice(REG_APPUNTI,
	              "⭐ the clipboard that was ALREADY in the session: %zu bytes, "
	              "read at switch-on.  ⚠ Whoever connects must not lose "
	              "what they had copied",
	              byte);

	g_mutex_lock(&appunti->lucchetto);
	g_free(appunti->ultimo);
	appunti->ultimo = g_strdup(testo);
	appunti->ultimo_byte = byte;
	if (appunti->su_testo)
		appunti->su_testo(testo, byte, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);
}

static void su_trasferimento(GDBusConnection *bus, const char *mittente,
                             const char *percorso, const char *interfaccia,
                             const char *segnale, GVariant *parametri,
                             gpointer dati)
{
	Appunti *appunti = dati;
	const char *mime = NULL;
	guint32 serial = 0;

	(void)bus;
	(void)mittente;
	(void)percorso;
	(void)interfaccia;
	(void)segnale;

	g_variant_get(parametri, "(&su)", &mime, &serial);
	registro_dettaglio(REG_APPUNTI,
	                   "the session wants to paste «%s» (request %u)", mime,
	                   serial);

	g_mutex_lock(&appunti->lucchetto);
	if (appunti->su_richiesta)
	{
		appunti->su_richiesta((uint32_t)serial, appunti->dati);
		g_mutex_unlock(&appunti->lucchetto);
		return;
	}
	g_mutex_unlock(&appunti->lucchetto);

	/* ⛔ Nobody is listening: we answer NO anyway.  A request without an
	 *    answer leaves the pasting application waiting
	 *    indefinitely, and what the user sees is a hung desktop
	 *    (`appunti.h`, `AppuntiSuRichiesta`). */
	appunti_rispondi(appunti, (uint32_t)serial, NULL, 0);
}

/* ------------------------------------------------------------------ *
 * The thread that runs the context
 * ------------------------------------------------------------------ */
static gpointer thread_appunti(gpointer dati)
{
	Appunti *appunti = dati;

	g_main_context_push_thread_default(appunti->contesto);
	g_main_loop_run(appunti->ciclo);
	g_main_context_pop_thread_default(appunti->contesto);
	return NULL;
}

Appunti *appunti_apri(GDBusConnection *bus, const char *percorso_controllo,
                      GError **sbaglio)
{
	Appunti *appunti;

	if (!bus || !percorso_controllo)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "the clipboard wants a bus and the control session");
		return NULL;
	}

	appunti = g_new0(Appunti, 1);
	appunti->bus = g_object_ref(bus);
	appunti->controllo = g_strdup(percorso_controllo);
	g_mutex_init(&appunti->lucchetto);

	/*
	 * ⛔ The context is created and SUBSCRIBED here, on the calling thread, with the
	 *    context set as default: GDBus binds delivery to the default
	 *    context of the thread that **subscribes**, not to the one that then
	 *    runs it.  Subscribing inside the new thread would be the seemingly
	 *    obvious way, and would leave a window in which signals
	 *    would arrive before the thread is ready.
	 */
	appunti->contesto = g_main_context_new();
	g_main_context_push_thread_default(appunti->contesto);

	appunti->sottoscrizione_offerta = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSIONE, "SelectionOwnerChanged", percorso_controllo,
	    NULL, G_DBUS_SIGNAL_FLAGS_NONE, su_padrone_cambiato, appunti, NULL);
	appunti->sottoscrizione_richiesta = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSIONE, "SelectionTransfer", percorso_controllo, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, su_trasferimento, appunti, NULL);

	g_main_context_pop_thread_default(appunti->contesto);

	/*
	 * ⛔ The loop and the thread start BEFORE `EnableClipboard`, and the order is
	 *    not indifferent: that call can make a
	 *    `SelectionOwnerChanged` arrive **at once**.
	 * ⚠ It was written here that that signal "is precisely the announcement that lets
	 *   whoever reconnects find the clipboard again": **it is false**, measured on 21
	 *   August 2026 — Mutter tells the CHANGES, not the owner that was there.
	 *   The clipboard that was already there is asked for, and
	 *   `appunti_leggi_adesso()` does it.  Switching on the
	 *    clipboard first and then the thread, that signal would fall in the window in which
	 *    nobody runs the context — ⚠ and the symptom would be "the clipboard
	 *    works only from the second copy on", which nobody connects
	 *    to the order of two lines.
	 */
	appunti->ciclo = g_main_loop_new(appunti->contesto, FALSE);
	appunti->thread = g_thread_new("remotix-appunti", thread_appunti, appunti);

	{
		GVariantBuilder vuote;
		g_autoptr(GVariant) risposta = NULL;

		/*
		 * ⭐ Without `mime-types`: so Mutter makes us owners of nothing and
		 *    tells us instead who is the owner now.  See `appunti.h`.
		 */
		g_variant_builder_init(&vuote, G_VARIANT_TYPE("a{sv}"));
		risposta = chiama(appunti, "EnableClipboard",
		                  g_variant_new("(a{sv})", &vuote), NULL, sbaglio);
		if (!risposta)
		{
			g_prefix_error(sbaglio, "Mutter does not grant the clipboard: ");
			appunti_chiudi(appunti);
			return NULL;
		}
	}

	registro_dice(REG_APPUNTI,
	              "⭐ session clipboard switched on (text only, in both directions) "
	              "on %s",
	              percorso_controllo);
	return appunti;
}

Appunti *appunti_apri_kde(GError **sbaglio)
{
	AppuntiKde *kde = appunti_kde_apri(sbaglio);
	Appunti *appunti;

	if (!kde)
		return NULL;
	appunti = g_new0(Appunti, 1);
	appunti->kde = kde;
	return appunti;
}

/* ⭐ PHASE 13 — the same wrapper as `appunti_apri_kde()`: from here on every
 *    function hands over to `appunti_kde_*` as on KDE. */
Appunti *appunti_apri_wlroots(GError **sbaglio)
{
	AppuntiKde *wlr = appunti_kde_apri_wlroots(sbaglio);
	Appunti *appunti;

	if (!wlr)
		return NULL;
	appunti = g_new0(Appunti, 1);
	appunti->kde = wlr;
	return appunti;
}

char *appunti_ultimo_testo(Appunti *appunti, size_t *byte)
{
	char *copia;

	if (!appunti)
		return NULL;
	if (appunti->kde)
		return appunti_kde_ultimo_testo(appunti->kde, byte);
	g_mutex_lock(&appunti->lucchetto);
	copia = appunti->ultimo ? g_strdup(appunti->ultimo) : NULL;
	if (byte)
		*byte = copia ? appunti->ultimo_byte : 0;
	g_mutex_unlock(&appunti->lucchetto);
	return copia;
}

void appunti_ascolta(Appunti *appunti, AppuntiSuTesto su_testo,
                     AppuntiSuRichiesta su_richiesta, void *dati)
{
	if (!appunti)
		return;
	if (appunti->kde) {
		appunti_kde_ascolta(appunti->kde, su_testo, su_richiesta, dati);
		return;
	}
	g_mutex_lock(&appunti->lucchetto);
	appunti->su_testo = su_testo;
	appunti->su_richiesta = su_richiesta;
	appunti->dati = dati;
	g_mutex_unlock(&appunti->lucchetto);
}

void appunti_chiudi(Appunti *appunti)
{
	if (!appunti)
		return;
	if (appunti->kde) {
		appunti_kde_chiudi(appunti->kde);
		g_free(appunti);
		return;
	}

	/* First we stop listening — and the call waits for whoever is half
	 * way — then the loop is stopped, then the subscriptions are removed. */
	appunti_ascolta(appunti, NULL, NULL, NULL);

	/*
	 * ⛔ NO `DisableClipboard`, EVER — not even here, and it is trap 1 of
	 *    `appunti.h`.  In Mutter 48.7 that call leaves the clipboard
	 *    half on, and from then on nobody can switch it on again: whoever
	 *    switched it off at detach would find, at the next connection,
	 *    a dead clipboard **for the rest of the graphical session**.
	 *    ⇒ Closing the control session everything goes away together.
	 */

	if (appunti->ciclo)
		g_main_loop_quit(appunti->ciclo);
	if (appunti->thread)
		g_thread_join(appunti->thread);
	g_clear_pointer(&appunti->ciclo, g_main_loop_unref);

	if (appunti->bus)
	{
		if (appunti->sottoscrizione_offerta)
			g_dbus_connection_signal_unsubscribe(
			    appunti->bus, appunti->sottoscrizione_offerta);
		if (appunti->sottoscrizione_richiesta)
			g_dbus_connection_signal_unsubscribe(
			    appunti->bus, appunti->sottoscrizione_richiesta);
	}

	g_clear_pointer(&appunti->contesto, g_main_context_unref);
	g_free(appunti->ultimo);
	g_clear_object(&appunti->bus);
	g_mutex_clear(&appunti->lucchetto);
	g_free(appunti->controllo);
	g_free(appunti);
}

/* ------------------------------------------------------------------ *
 * The two directions
 * ------------------------------------------------------------------ */
gboolean appunti_offri(Appunti *appunti, GError **sbaglio)
{
	GVariantBuilder opzioni;
	g_autoptr(GVariant) risposta = NULL;

	if (!appunti)
		return FALSE;
	if (appunti->kde)
		return appunti_kde_offri(appunti->kde, sbaglio);

	/* ⛔ `as` and not `(as)`: in METHODS the types are not in a tuple — the other
	 *    half of trap 2, and this is the half that goes wrong silently
	 *    on the other side. */
	g_variant_builder_init(&opzioni, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&opzioni, "{sv}", "mime-types",
	                      g_variant_new_strv(TIPI_TESTO, -1));

	risposta = chiama(appunti, "SetSelection", g_variant_new("(a{sv})", &opzioni),
	                  NULL, sbaglio);
	if (!risposta)
		return FALSE;

	registro_dettaglio(REG_APPUNTI,
	                   "offered the client's text to the session (%d types)",
	                   (int)(sizeof TIPI_TESTO / sizeof *TIPI_TESTO) - 1);
	return TRUE;
}

void appunti_rispondi(Appunti *appunti, uint32_t serial, const char *testo,
                      size_t byte)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *ripiego = NULL;
	gboolean riuscito = FALSE;
	int fd;

	if (!appunti)
		return;
	if (appunti->kde) {
		appunti_kde_rispondi(appunti->kde, serial, testo, byte);
		return;
	}

	/* ⛔⛔⭐ IF THE CLIENT HAS NOTHING, THE DESKTOP GETS BACK WHAT IT HAD —
	 *      21 August 2026, and it comes from the user's directive: "the experience
	 *      must be as close as possible to a local graphical
	 *      session".
	 *
	 * ⚠ To be found when someone on this side pastes with the mouse, the client
	 *   announces itself as soon as it connects — and announcing means taking the
	 *   selection, which is ONE.  ⛔ From that moment whoever pastes in the desktop
	 *   asks US, and if the client has nothing to give the paste came out
	 *   empty: `[M]` `wl-paste` said «TESTO-CHE-ERA-GIA-NEL-DESKTOP» before
	 *   the connection and «» after.  That is, connecting ERASED the desktop's
	 *   clipboard.
	 *
	 * ⭐ The cure is here and does not touch the protocol: the selection changes
	 *    hands, the CONTENT does not.  If the client delivers nothing, we deliver
	 *    the last text the session had given us — which is exactly what
	 *    the user had copied on this side.
	 * ⚠ And it is declared in the log: a silent fallback would have the face of
	 *   a successful delivery. */
	if (!testo || byte == 0)
	{
		size_t quanti = 0;

		ripiego = appunti_ultimo_testo(appunti, &quanti);
		if (ripiego && quanti > 0)
		{
			registro_dice(REG_APPUNTI,
			              "⭐ the client has no clipboard to give for request "
			              "%u: giving back to the session the %zu bytes IT had.  "
			              "⚠ Connecting must not erase the desktop "
			              "clipboard",
			              serial, quanti);
			testo = ripiego;
			byte = quanti;
		}
	}

	if (!testo || byte == 0)
	{
		/* Nothing to deliver, and we say so: it is an answer anyway, and it is
		 * what unblocks whoever is pasting. */
		g_autoptr(GVariant) risposta =
		    chiama(appunti, "SelectionWriteDone",
		           g_variant_new("(ub)", (guint32)serial, FALSE), NULL, &sbaglio);
		if (!risposta)
			registro_dice(REG_APPUNTI,
			              "⛔ SelectionWriteDone(no) for request %u did not "
			              "succeed (%s): whoever pastes may stay hung",
			              serial, sbaglio->message);
		else
			registro_dettaglio(REG_APPUNTI,
			                   "request %u closed with «I do not have it»", serial);
		return;
	}

	fd = chiama_per_descrittore(appunti, "SelectionWrite",
	                            g_variant_new("(u)", (guint32)serial), &sbaglio);
	if (fd < 0)
	{
		registro_dice(REG_APPUNTI,
		              "⛔ SelectionWrite for request %u was refused "
		              "(%s)",
		              serial, sbaglio->message);
		return;
	}

	/* ⭐ And the cache becomes what the session REALLY holds: from here on
	 *    the fallback above gives back this, not an earlier text. */
	g_mutex_lock(&appunti->lucchetto);
	if (!ripiego)
	{
		g_free(appunti->ultimo);
		appunti->ultimo = g_strndup(testo, byte);
		appunti->ultimo_byte = byte;
	}
	g_mutex_unlock(&appunti->lucchetto);

	{
		size_t scritti = 0;

		riuscito = TRUE;
		while (scritti < byte)
		{
			gssize adesso = write(fd, testo + scritti, byte - scritti);

			if (adesso < 0)
			{
				if (errno == EINTR)
					continue;
				registro_dice(REG_APPUNTI,
				              "⛔ write to the session failed at %zu of "
				              "%zu bytes: %s",
				              scritti, byte, g_strerror(errno));
				riuscito = FALSE;
				break;
			}
			scritti += (size_t)adesso;
		}
		if (riuscito)
			registro_dettaglio(REG_APPUNTI,
			                   "delivered %zu bytes to the session (request %u)",
			                   byte, serial);
	}

	/* ⛔ We close BEFORE declaring done: the reader at the other end waits for
	 *    the end of the stream, and a descriptor still open never makes the
	 *    end. */
	close(fd);

	{
		g_autoptr(GVariant) risposta =
		    chiama(appunti, "SelectionWriteDone",
		           g_variant_new("(ub)", (guint32)serial, riuscito), NULL,
		           &sbaglio);
		if (!risposta)
			registro_dice(REG_APPUNTI,
			              "⛔ SelectionWriteDone for request %u did not "
			              "succeed: %s",
			              serial, sbaglio->message);
	}
}
