/*
 * clipboard.c — the SESSION's clipboard, that is Mutter's.
 *
 * ⛔ The four traps, the thread contract and the reason for "text only"
 *    are in `clipboard.h`, and are not repeated here: this file IMPLEMENTS them, and
 *    every point where one of them bites is marked on the spot.
 *
 * ⭐ Descends from `fondamenta/remotix-c/src/appunti_mutter.c` (450 lines, measured on 5
 *    August 2026 against GNOME 48.7).  ⛔ The differences, all intended:
 *
 *      · **text only**: v1 exchanged lists of MIME types with the stitcher and
 *        also carried images and `text/html` (`fondamenta/…/scambio.c`).  Here the types
 *        live in `TEXT_TYPES` and do not leave this file;
 *      · **it is read here**, on the clipboard thread, instead of handing over the
 *        types and being called back: the §7.4 announcement carries the length, and the
 *        length is not known without reading;
 *      · **the ceiling and UTF-8 validity are checked here**, where the text
 *        still exists whole — not after crossing a socket;
 *      · **the last text is remembered**, not the last list of types: it is what
 *        whoever reconnects needs, and it is already ready to send.
 */
#include "clipboard.h"
#include "clipboard_kde.h"

#include <gio/gunixfdlist.h>
#include <glib-unix.h>
#include <string.h>
#include <unistd.h>

#include "log.h"

#define REMOTE_NAME "org.gnome.Mutter.RemoteDesktop"
#define IFACE_SESSION "org.gnome.Mutter.RemoteDesktop.Session"

#define WAIT_CALL_MS 5000

/* How long we wait for a chunk from the descriptor before declaring it lost: the
 * writer at the other end may be slow, but not mute. */
#define WAIT_READ_MS 5000

/*
 * ⛔ THE ROW OF TYPES, AND IT IS TRIED WHOLE — trap 3 of `clipboard.h`.
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
static const char *const TEXT_TYPES[] = {
	"text/plain;charset=utf-8",
	"UTF8_STRING",
	"text/plain",
	NULL,
};

struct Clipboard
{
	/* ⭐ PHASE 12 — on KDE all the work is done by `clipboard_kde.c`, and this
	 *    shell hands over at the top of every public function: the GNOME branch
	 *    below stays as it was, line by line. */
	ClipboardKde *kde;

	GDBusConnection *bus;
	char *check;

	GMainContext *context;
	GMainLoop *cycle;
	GThread *thread;

	/* ⛔ The last text the session copied, kept HERE because it must
	 *    survive the connection: whoever reconnects receives no new
	 *    signal (`clipboard.h`, `clipboard_last_text`). */
	char *last;
	size_t last_byte;

	guint subscription_offer;
	guint subscription_request;

	/* The callbacks and their owner.  The lock is held while a callback
	 * runs, so `clipboard_listen(NULL, NULL, NULL)` waits for whoever is
	 * half way instead of freeing the context under their feet. */
	GMutex lock;
	ClipboardOnText on_text;
	ClipboardOnRequest on_request;
	void *data;
};

static GVariant *call(Clipboard *clipboard, const char *method, GVariant *call_args,
                        const GVariantType *kind, GError **mistake)
{
	return g_dbus_connection_call_sync(clipboard->bus, REMOTE_NAME,
	                                   clipboard->check, IFACE_SESSION,
	                                   method, call_args, kind,
	                                   G_DBUS_CALL_FLAGS_NONE,
	                                   WAIT_CALL_MS, NULL, mistake);
}

/* As above, but the answer carries a descriptor. */
static int call_for_fd(Clipboard *clipboard, const char *method,
                                  GVariant *call_args, GError **mistake)
{
	g_autoptr(GUnixFDList) listing = NULL;
	g_autoptr(GVariant) response = NULL;
	gint32 idx = -1;

	response = g_dbus_connection_call_with_unix_fd_list_sync(
	    clipboard->bus, REMOTE_NAME, clipboard->check, IFACE_SESSION, method,
	    call_args, G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
	    WAIT_CALL_MS, NULL, &listing, NULL, mistake);
	if (!response)
		return -1;

	g_variant_get(response, "(h)", &idx);
	return g_unix_fd_list_get(listing, idx, mistake);
}

/* ------------------------------------------------------------------ *
 * Reading the text from the session
 * ------------------------------------------------------------------ */

/* Reads a descriptor to the end, with a ceiling and without hanging.
 *
 * ⛔ The ceiling is that of §5.4 **plus one**: reading exactly
 *    `CLIPBOARD_CAP` one cannot tell "a text as large as the ceiling", which is
 *    LAWFUL, from "a larger text", which must be refused.  One more byte and the
 *    two cases separate.  ⚠ It is the same form as §5.4's 1 000 000 versus 1 MiB:
 *    a ceiling that makes the borderline case illegal is not that ceiling. */
static GBytes *slurp_fd(int fd, GError **mistake)
{
	GByteArray *collected = g_byte_array_new();
	guint8 piece[16384];

	while (TRUE)
	{
		GPollFD probe = { .fd = fd, .events = G_IO_IN | G_IO_HUP | G_IO_ERR };
		gssize readings;

		if (g_poll(&probe, 1, WAIT_READ_MS) <= 0)
		{
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "whoever had to deliver the clipboard wrote "
			            "nothing for %d ms",
			            WAIT_READ_MS);
			g_byte_array_free(collected, TRUE);
			return NULL;
		}

		readings = read(fd, piece, sizeof piece);
		if (readings == 0)
			break; /* end */
		if (readings < 0)
		{
			if (errno == EINTR)
				continue;
			g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno),
			            "clipboard read failed: %s", g_strerror(errno));
			g_byte_array_free(collected, TRUE);
			return NULL;
		}

		if (collected->len + (guint)readings > CLIPBOARD_CAP)
		{
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NO_SPACE,
			            "clipboard over the ceiling of %u bytes (§5.4): left "
			            "where it is, and NOT truncated",
			            CLIPBOARD_CAP);
			g_byte_array_free(collected, TRUE);
			return NULL;
		}
		g_byte_array_append(collected, piece, (guint)readings);
	}

	return g_byte_array_free_to_bytes(collected);
}

/*
 * Tries the row of `TEXT_TYPES` and returns the first text that holds, already
 * validated.  NULL if there is none — and the reason is in the log.
 *
 * ⛔ And the reasons are THREE and stay distinct: there was no text type ·
 *    there was one and the read failed · there was one, it was read, and it was not valid UTF-8.
 *    A single `NULL` for all three would be `LESSONS.md` §1.9 — "empty and
 *    forbidden with the same face".
 */
static char *read_text(Clipboard *clipboard, size_t *amount)
{
	for (int i = 0; TEXT_TYPES[i]; i++)
	{
		g_autoptr(GError) mistake = NULL;
		g_autoptr(GBytes) data = NULL;
		const char *start;
		gsize byte = 0;
		int fd;

		fd = call_for_fd(clipboard, "SelectionRead",
		                            g_variant_new("(s)", TEXT_TYPES[i]),
		                            &mistake);
		if (fd < 0)
		{
			/* ⚠ In detail and not in plain: the row is tried on purpose, and a
			 *   type the session does not have is the NORMAL outcome of the first rounds —
			 *   one line for each would cover the log with noise. */
			log_detail(LOG_CLIPBOARD,
			                   "«%s» cannot be read from the session (%s): trying the "
			                   "next type",
			                   TEXT_TYPES[i],
			                   mistake ? mistake->message : "no detail");
			continue;
		}

		data = slurp_fd(fd, &mistake);
		close(fd);
		if (!data)
		{
			registro_dice(LOG_CLIPBOARD,
			              "⛔ «%s»: the read did not succeed — %s",
			              TEXT_TYPES[i],
			              mistake ? mistake->message : "no detail");
			continue;
		}

		start = (const char *)g_bytes_get_data(data, &byte);
		if (byte == 0)
		{
			/* ⚠ Zero bytes is NOT a fault: it is an emptied clipboard, and it is
			 *   exactly what the bench does at the start of every round
			 *   (`LESSONS.md` §2.3-quinquies).  It is declared and we go on. */
			log_detail(LOG_CLIPBOARD,
			                   "«%s» delivered zero bytes: the clipboard is "
			                   "empty, not broken",
			                   TEXT_TYPES[i]);
			continue;
		}

		/* ⛔ VALID UTF-8, and it is checked HERE.  `RCP.md` §5.4: "the text MUST
		 *    be UTF-8".  Sending it without looking would mean putting on the
		 *    wire a violation **of ours**, and letting the client discover it — which
		 *    per §3 would have to close the session.  ⇒ The symptom would be "the
		 *    session drops when I copy from that program". */
		if (!g_utf8_validate_len(start, byte, NULL))
		{
			registro_dice(LOG_CLIPBOARD,
			              "⛔ «%s» delivered %zu bytes that are NOT valid "
			              "UTF-8: not announced (§5.4).  ⚠ It is not a defect "
			              "of ours nor of the client — it is a program that keeps "
			              "bytes in the clipboard that RCP/1 cannot carry",
			              TEXT_TYPES[i], (size_t)byte);
			continue;
		}

		/* ⛔ AND NO ZEROS IN THE MIDDLE.  From here on the text travels as a
		 *    zero-terminated string — in the socket to the parent and in
		 *    `rcp.c` — and a zero in the middle would cut it **silently**: what
		 *    gets pasted would be shorter than what was copied, and the
		 *    announcement would state the whole length.  ⇒ Two truths about the
		 *    same thing, which is the defect §2.2 forbids in those words. */
		if (memchr(start, 0, byte))
		{
			registro_dice(LOG_CLIPBOARD,
			              "⛔ «%s»: %zu bytes with a zero in the middle — not "
			              "announced.  Truncating here would give a text shorter "
			              "than the announcement, that is an announcement that lies",
			              TEXT_TYPES[i], (size_t)byte);
			continue;
		}

		log_detail(LOG_CLIPBOARD, "read %zu bytes of «%s» from the session",
		                   (size_t)byte, TEXT_TYPES[i]);
		if (amount)
			*amount = byte;
		return g_strndup(start, byte);
	}

	return NULL;
}

/* ------------------------------------------------------------------ *
 * The two signals
 * ------------------------------------------------------------------ */
static void on_owner_changed(GDBusConnection *bus, const char *sender,
                                const char *fpath, const char *interfaccia,
                                const char *send_signal, GVariant *parameters,
                                gpointer data)
{
	Clipboard *clipboard = data;
	g_autoptr(GVariant) options = NULL;
	g_autoptr(GVariant) types = NULL;
	g_autofree const char **mime = NULL;
	g_autofree char *text = NULL;
	gboolean our = FALSE;
	gboolean has_text = FALSE;
	size_t byte = 0;

	(void)bus;
	(void)sender;
	(void)fpath;
	(void)interfaccia;
	(void)send_signal;

	g_variant_get(parameters, "(@a{sv})", &options);

	/*
	 * ⛔ THE RETURN IS RECOGNISED HERE, and it is the first thing to look at —
	 *    trap 4 of `clipboard.h`.  Without these three lines we would announce to the
	 *    client what the client just gave us, and the two sides would
	 *    chase each other endlessly.
	 * ⭐ And on GNOME it is **labelled**, not to be guessed: `STUDIES.md` §gnome §10
	 *    corrects our old line that spoke of "a heuristic".
	 */
	if (g_variant_lookup(options, "session-is-owner", "b", &our) && our)
	{
		log_detail(LOG_CLIPBOARD,
		                   "it is the return of our own offer, not a new "
		                   "copy: not announced");
		return;
	}

	/*
	 * ⛔ IN THE SIGNAL THE TYPES ARE INSIDE A TUPLE, AND IN THE METHODS NOT — trap
	 *    2 of `clipboard.h`, measured on 5 August 2026 and it cost one test.
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
	types = g_variant_lookup_value(options, "mime-types",
	                              G_VARIANT_TYPE_STRING_ARRAY);
	if (!types)
	{
		g_autoptr(GVariant) tuple =
		    g_variant_lookup_value(options, "mime-types", G_VARIANT_TYPE("(as)"));

		if (tuple)
			types = g_variant_get_child_value(tuple, 0);
	}
	if (!types)
	{
		registro_dice(LOG_CLIPBOARD,
		              "⛔ the session announced a copy without readable "
		              "types: neither `as` nor `(as)`.  ⚠ If it is a third "
		              "form, the clipboard from here on goes one way only "
		              "and this line is the only place where it shows");
		return;
	}
	mime = g_variant_get_strv(types, NULL);

	/* ⛔ IS THERE TEXT AMONG THE TYPES?  And if not, we say WHAT there was.
	 *
	 * ⚠ It is the normal case of "I copied an image": it is not a fault, and it is
	 *   the line that explains to the user why that copy did not reach the
	 *   phone.  Without it, the symptom would be "the clipboard sometimes does not
	 *   work" — that is the most expensive defect to diagnose there is. */
	for (int i = 0; mime && mime[i] && !has_text; i++)
		for (int k = 0; TEXT_TYPES[k]; k++)
			if (g_ascii_strcasecmp(mime[i], TEXT_TYPES[k]) == 0)
			{
				has_text = TRUE;
				break;
			}
	if (!has_text)
	{
		g_autofree char *listing = mime ? g_strjoinv(", ", (GStrv)mime) : NULL;

		registro_dice(LOG_CLIPBOARD,
		              "the session copied something that is not text (%s): "
		              "not announced.  ⚠ `DECISIONS.md` §5-ter.1 — text "
		              "only, and it is a decision, not a technical limit",
		              listing && *listing ? listing : "no type");
		return;
	}

	text = read_text(clipboard, &byte);
	if (!text)
	{
		/* ⚠ `read_text` has already written WHICH of the three reasons it was: here
		 *   we only say that the announcement does not leave, or "I read and kept quiet"
		 *   would have the face of "nothing happened". */
		registro_dice(LOG_CLIPBOARD,
		              "⛔ the session copied some text but no type of it could be "
		              "read: no announcement to the client");
		return;
	}

	g_mutex_lock(&clipboard->lock);
	g_free(clipboard->last);
	clipboard->last = g_strdup(text);
	clipboard->last_byte = byte;
	if (clipboard->on_text)
		clipboard->on_text(text, byte, clipboard->data);
	g_mutex_unlock(&clipboard->lock);
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
 *    any other copy; if there is nobody, `read_text` says so in the
 *    log and nothing happens.
 */
void clipboard_read_now(Clipboard *clipboard)
{
	g_autofree char *text = NULL;
	size_t byte = 0;

	if (!clipboard)
		return;
	if (clipboard->kde) {
		clipboard_kde_read_now(clipboard->kde);
		return;
	}

	text = read_text(clipboard, &byte);
	if (!text)
	{
		log_detail(LOG_CLIPBOARD,
		                   "the session had no clipboard to give us at the time "
		                   "of switching on: it is not a fault");
		return;
	}

	registro_dice(LOG_CLIPBOARD,
	              "⭐ the clipboard that was ALREADY in the session: %zu bytes, "
	              "read at switch-on.  ⚠ Whoever connects must not lose "
	              "what they had copied",
	              byte);

	g_mutex_lock(&clipboard->lock);
	g_free(clipboard->last);
	clipboard->last = g_strdup(text);
	clipboard->last_byte = byte;
	if (clipboard->on_text)
		clipboard->on_text(text, byte, clipboard->data);
	g_mutex_unlock(&clipboard->lock);
}

static void on_transfer(GDBusConnection *bus, const char *sender,
                             const char *fpath, const char *interfaccia,
                             const char *send_signal, GVariant *parameters,
                             gpointer data)
{
	Clipboard *clipboard = data;
	const char *mime = NULL;
	guint32 serial = 0;

	(void)bus;
	(void)sender;
	(void)fpath;
	(void)interfaccia;
	(void)send_signal;

	g_variant_get(parameters, "(&su)", &mime, &serial);
	log_detail(LOG_CLIPBOARD,
	                   "the session wants to paste «%s» (request %u)", mime,
	                   serial);

	g_mutex_lock(&clipboard->lock);
	if (clipboard->on_request)
	{
		clipboard->on_request((uint32_t)serial, clipboard->data);
		g_mutex_unlock(&clipboard->lock);
		return;
	}
	g_mutex_unlock(&clipboard->lock);

	/* ⛔ Nobody is listening: we answer NO anyway.  A request without an
	 *    answer leaves the pasting application waiting
	 *    indefinitely, and what the user sees is a hung desktop
	 *    (`clipboard.h`, `ClipboardOnRequest`). */
	clipboard_reply(clipboard, (uint32_t)serial, NULL, 0);
}

/* ------------------------------------------------------------------ *
 * The thread that runs the context
 * ------------------------------------------------------------------ */
static gpointer thread_clipboard(gpointer data)
{
	Clipboard *clipboard = data;

	g_main_context_push_thread_default(clipboard->context);
	g_main_loop_run(clipboard->cycle);
	g_main_context_pop_thread_default(clipboard->context);
	return NULL;
}

Clipboard *clipboard_open(GDBusConnection *bus, const char *check_path,
                      GError **mistake)
{
	Clipboard *clipboard;

	if (!bus || !check_path)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "the clipboard wants a bus and the control session");
		return NULL;
	}

	clipboard = g_new0(Clipboard, 1);
	clipboard->bus = g_object_ref(bus);
	clipboard->check = g_strdup(check_path);
	g_mutex_init(&clipboard->lock);

	/*
	 * ⛔ The context is created and SUBSCRIBED here, on the calling thread, with the
	 *    context set as default: GDBus binds delivery to the default
	 *    context of the thread that **subscribes**, not to the one that then
	 *    runs it.  Subscribing inside the new thread would be the seemingly
	 *    obvious way, and would leave a window in which signals
	 *    would arrive before the thread is ready.
	 */
	clipboard->context = g_main_context_new();
	g_main_context_push_thread_default(clipboard->context);

	clipboard->subscription_offer = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSION, "SelectionOwnerChanged", check_path,
	    NULL, G_DBUS_SIGNAL_FLAGS_NONE, on_owner_changed, clipboard, NULL);
	clipboard->subscription_request = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSION, "SelectionTransfer", check_path, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, on_transfer, clipboard, NULL);

	g_main_context_pop_thread_default(clipboard->context);

	/*
	 * ⛔ The loop and the thread start BEFORE `EnableClipboard`, and the order is
	 *    not indifferent: that call can make a
	 *    `SelectionOwnerChanged` arrive **at once**.
	 * ⚠ It was written here that that signal "is precisely the announcement that lets
	 *   whoever reconnects find the clipboard again": **it is false**, measured on 21
	 *   August 2026 — Mutter tells the CHANGES, not the owner that was there.
	 *   The clipboard that was already there is asked for, and
	 *   `clipboard_read_now()` does it.  Switching on the
	 *    clipboard first and then the thread, that signal would fall in the window in which
	 *    nobody runs the context — ⚠ and the symptom would be "the clipboard
	 *    works only from the second copy on", which nobody connects
	 *    to the order of two lines.
	 */
	clipboard->cycle = g_main_loop_new(clipboard->context, FALSE);
	clipboard->thread = g_thread_new("remotix-appunti", thread_clipboard, clipboard);

	{
		GVariantBuilder blanks;
		g_autoptr(GVariant) response = NULL;

		/*
		 * ⭐ Without `mime-types`: so Mutter makes us owners of nothing and
		 *    tells us instead who is the owner now.  See `clipboard.h`.
		 */
		g_variant_builder_init(&blanks, G_VARIANT_TYPE("a{sv}"));
		response = call(clipboard, "EnableClipboard",
		                  g_variant_new("(a{sv})", &blanks), NULL, mistake);
		if (!response)
		{
			g_prefix_error(mistake, "Mutter does not grant the clipboard: ");
			clipboard_close(clipboard);
			return NULL;
		}
	}

	registro_dice(LOG_CLIPBOARD,
	              "⭐ session clipboard switched on (text only, in both directions) "
	              "on %s",
	              check_path);
	return clipboard;
}

Clipboard *clipboard_open_kde(GError **mistake)
{
	ClipboardKde *kde = clipboard_kde_open(mistake);
	Clipboard *clipboard;

	if (!kde)
		return NULL;
	clipboard = g_new0(Clipboard, 1);
	clipboard->kde = kde;
	return clipboard;
}

/* ⭐ PHASE 13 — the same wrapper as `clipboard_open_kde()`: from here on every
 *    function hands over to `appunti_kde_*` as on KDE. */
Clipboard *clipboard_open_wlroots(GError **mistake)
{
	ClipboardKde *wlr = clipboard_kde_open_wlroots(mistake);
	Clipboard *clipboard;

	if (!wlr)
		return NULL;
	clipboard = g_new0(Clipboard, 1);
	clipboard->kde = wlr;
	return clipboard;
}

char *clipboard_last_text(Clipboard *clipboard, size_t *byte)
{
	char *copied;

	if (!clipboard)
		return NULL;
	if (clipboard->kde)
		return clipboard_kde_last_text(clipboard->kde, byte);
	g_mutex_lock(&clipboard->lock);
	copied = clipboard->last ? g_strdup(clipboard->last) : NULL;
	if (byte)
		*byte = copied ? clipboard->last_byte : 0;
	g_mutex_unlock(&clipboard->lock);
	return copied;
}

void clipboard_listen(Clipboard *clipboard, ClipboardOnText on_text,
                     ClipboardOnRequest on_request, void *data)
{
	if (!clipboard)
		return;
	if (clipboard->kde) {
		clipboard_kde_listen(clipboard->kde, on_text, on_request, data);
		return;
	}
	g_mutex_lock(&clipboard->lock);
	clipboard->on_text = on_text;
	clipboard->on_request = on_request;
	clipboard->data = data;
	g_mutex_unlock(&clipboard->lock);
}

void clipboard_close(Clipboard *clipboard)
{
	if (!clipboard)
		return;
	if (clipboard->kde) {
		clipboard_kde_close(clipboard->kde);
		g_free(clipboard);
		return;
	}

	/* First we stop listening — and the call waits for whoever is half
	 * way — then the loop is stopped, then the subscriptions are removed. */
	clipboard_listen(clipboard, NULL, NULL, NULL);

	/*
	 * ⛔ NO `DisableClipboard`, EVER — not even here, and it is trap 1 of
	 *    `clipboard.h`.  In Mutter 48.7 that call leaves the clipboard
	 *    half on, and from then on nobody can switch it on again: whoever
	 *    switched it off at detach would find, at the next connection,
	 *    a dead clipboard **for the rest of the graphical session**.
	 *    ⇒ Closing the control session everything goes away together.
	 */

	if (clipboard->cycle)
		g_main_loop_quit(clipboard->cycle);
	if (clipboard->thread)
		g_thread_join(clipboard->thread);
	g_clear_pointer(&clipboard->cycle, g_main_loop_unref);

	if (clipboard->bus)
	{
		if (clipboard->subscription_offer)
			g_dbus_connection_signal_unsubscribe(
			    clipboard->bus, clipboard->subscription_offer);
		if (clipboard->subscription_request)
			g_dbus_connection_signal_unsubscribe(
			    clipboard->bus, clipboard->subscription_request);
	}

	g_clear_pointer(&clipboard->context, g_main_context_unref);
	g_free(clipboard->last);
	g_clear_object(&clipboard->bus);
	g_mutex_clear(&clipboard->lock);
	g_free(clipboard->check);
	g_free(clipboard);
}

/* ------------------------------------------------------------------ *
 * The two directions
 * ------------------------------------------------------------------ */
gboolean clipboard_offer(Clipboard *clipboard, GError **mistake)
{
	GVariantBuilder options;
	g_autoptr(GVariant) response = NULL;

	if (!clipboard)
		return FALSE;
	if (clipboard->kde)
		return clipboard_kde_offer(clipboard->kde, mistake);

	/* ⛔ `as` and not `(as)`: in METHODS the types are not in a tuple — the other
	 *    half of trap 2, and this is the half that goes wrong silently
	 *    on the other side. */
	g_variant_builder_init(&options, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&options, "{sv}", "mime-types",
	                      g_variant_new_strv(TEXT_TYPES, -1));

	response = call(clipboard, "SetSelection", g_variant_new("(a{sv})", &options),
	                  NULL, mistake);
	if (!response)
		return FALSE;

	log_detail(LOG_CLIPBOARD,
	                   "offered the client's text to the session (%d types)",
	                   (int)(sizeof TEXT_TYPES / sizeof *TEXT_TYPES) - 1);
	return TRUE;
}

void clipboard_reply(Clipboard *clipboard, uint32_t serial, const char *text,
                      size_t byte)
{
	g_autoptr(GError) mistake = NULL;
	g_autofree char *fallback = NULL;
	gboolean succeeded = FALSE;
	int fd;

	if (!clipboard)
		return;
	if (clipboard->kde) {
		clipboard_kde_reply(clipboard->kde, serial, text, byte);
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
	if (!text || byte == 0)
	{
		size_t amount = 0;

		fallback = clipboard_last_text(clipboard, &amount);
		if (fallback && amount > 0)
		{
			registro_dice(LOG_CLIPBOARD,
			              "⭐ the client has no clipboard to give for request "
			              "%u: giving back to the session the %zu bytes IT had.  "
			              "⚠ Connecting must not erase the desktop "
			              "clipboard",
			              serial, amount);
			text = fallback;
			byte = amount;
		}
	}

	if (!text || byte == 0)
	{
		/* Nothing to deliver, and we say so: it is an answer anyway, and it is
		 * what unblocks whoever is pasting. */
		g_autoptr(GVariant) response =
		    call(clipboard, "SelectionWriteDone",
		           g_variant_new("(ub)", (guint32)serial, FALSE), NULL, &mistake);
		if (!response)
			registro_dice(LOG_CLIPBOARD,
			              "⛔ SelectionWriteDone(no) for request %u did not "
			              "succeed (%s): whoever pastes may stay hung",
			              serial, mistake->message);
		else
			log_detail(LOG_CLIPBOARD,
			                   "request %u closed with «I do not have it»", serial);
		return;
	}

	fd = call_for_fd(clipboard, "SelectionWrite",
	                            g_variant_new("(u)", (guint32)serial), &mistake);
	if (fd < 0)
	{
		registro_dice(LOG_CLIPBOARD,
		              "⛔ SelectionWrite for request %u was refused "
		              "(%s)",
		              serial, mistake->message);
		return;
	}

	/* ⭐ And the cache becomes what the session REALLY holds: from here on
	 *    the fallback above gives back this, not an earlier text. */
	g_mutex_lock(&clipboard->lock);
	if (!fallback)
	{
		g_free(clipboard->last);
		clipboard->last = g_strndup(text, byte);
		clipboard->last_byte = byte;
	}
	g_mutex_unlock(&clipboard->lock);

	{
		size_t written = 0;

		succeeded = TRUE;
		while (written < byte)
		{
			gssize t_now = write(fd, text + written, byte - written);

			if (t_now < 0)
			{
				if (errno == EINTR)
					continue;
				registro_dice(LOG_CLIPBOARD,
				              "⛔ write to the session failed at %zu of "
				              "%zu bytes: %s",
				              written, byte, g_strerror(errno));
				succeeded = FALSE;
				break;
			}
			written += (size_t)t_now;
		}
		if (succeeded)
			log_detail(LOG_CLIPBOARD,
			                   "delivered %zu bytes to the session (request %u)",
			                   byte, serial);
	}

	/* ⛔ We close BEFORE declaring done: the reader at the other end waits for
	 *    the end of the stream, and a descriptor still open never makes the
	 *    end. */
	close(fd);

	{
		g_autoptr(GVariant) response =
		    call(clipboard, "SelectionWriteDone",
		           g_variant_new("(ub)", (guint32)serial, succeeded), NULL,
		           &mistake);
		if (!response)
			registro_dice(LOG_CLIPBOARD,
			              "⛔ SelectionWriteDone for request %u did not "
			              "succeed: %s",
			              serial, mistake->message);
	}
}
