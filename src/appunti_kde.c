/*
 * appunti_kde — see `appunti_kde.h`.  The comments citing `kde.md` and KWin's
 * files refer to v1's study, now in `STUDI.md` §kde.
 */
#include "appunti_kde.h"

#include <errno.h>
#include <fcntl.h>
#include <glib-unix.h>
#include <poll.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>

#include "kwin.h"
#include "registro.h"
#include "ext-data-control-v1-client-protocol.h"
#include "wlr-data-control-unstable-v1-client-protocol.h"

/* How long whoever reads or writes the clipboard waits: on the other side of the
 * pipe there is any application at all, and it may have hung. */
#define WAIT_TRANSFER_MS 5000

/* ⛔ THE MINIMUM STEP BETWEEN TWO `set_selection`s: klipper, beyond ten changes a
 *    second, considers the clipboard gone mad and stops following it
 *    (`klipper/systemclipboard.cpp:50`) — without an error. */
#define MIN_STEP_US 100000

/* The same row as `appunti.c`, and in the same order: the first declares the
 * encoding.  ⛔ Never `application/x-kde-onlyReplaceEmpty`: KWin would silently
 * cancel the selection (`seat.cpp:200-226`).
 * ⭐ PHASE 13 — on labwc that type does not exist at all (`STUDI.md` §xfce §8.3):
 *    and we never offer it nor read it (this row is the only one), ⇒
 *    no possible damage, `[R]`. */
static const char *const TEXT_TYPES[] = {
	"text/plain;charset=utf-8",
	"UTF8_STRING",
	"text/plain",
	NULL,
};

typedef struct {
	struct zwlr_data_control_offer_v1 *proxy;
	GPtrArray *mime;
} Offer;

struct ClipboardKde {
	/* ⭐ PHASE 13 — who is on the other side, ONLY for the log lines:
	 *    «KWin» on KDE (the lines stay those of before, letter for letter),
	 *    «labwc» on XFCE.  ⛔ No branch of the protocol looks at it. */
	const char *compositor;
	struct wl_display *display;
	char socket[64];
	struct wl_registry *registry;
	struct zwlr_data_control_manager_v1 *handler;
	struct wl_seat *seat;
	uint32_t handler_version;
	const char *protocol; /* the name of the bound manager, for the log */
	uint32_t ext_name, ext_version; /* ext_data_control_manager_v1, if present */
	struct zwlr_data_control_device_v1 *device;

	GThread *pump;
	int wake[2];

	/* Protects the state below (Wayland proxies synchronise themselves,
	 * our pointers do not). */
	GMutex state;
	Offer *current;  /* the session's selection, or NULL */
	Offer *incoming; /* announced, not yet read */
	struct zwlr_data_control_source_v1 *our;
	gint64 last_set;
	GHashTable *requests; /* serial → fd */
	guint32 next_serial;

	/* As in `appunti.c`: the lock is held while a callback runs. */
	GMutex lock;
	char *last;
	size_t last_byte;
	ClipboardOnText on_text;
	ClipboardOnRequest on_request;
	void *data;
};

/* ------------------------------------------------------------------ *
 * The session's offers
 * ------------------------------------------------------------------ */
static void offer_free(Offer *offer)
{
	if (!offer)
		return;
	if (offer->proxy)
		zwlr_data_control_offer_v1_destroy(offer->proxy);
	g_ptr_array_unref(offer->mime);
	g_free(offer);
}

static bool offer_has(const Offer *offer, const char *mime)
{
	for (guint i = 0; offer && i < offer->mime->len; i++)
		if (g_ascii_strcasecmp(g_ptr_array_index(offer->mime, i), mime) == 0)
			return true;
	return false;
}

/* Is the announcement ours?  Same types, all and only those.
 *
 * ⭐ PHASE 13 — the caveat of `STUDI.md` §xfce §8.2 ("wlroots drops duplicate
 *    MIME types and the guard fails ⇒ loop") CANNOT trigger here, `[R]`:
 *    · wlroots drops an `offer` only if it is `strcmp`-equal to one already given
 *      (`wlr_data_control_v1.c:38-45`, 0.18.2), and repeats the types at the offer
 *      without filtering (`:346-351`);
 *    · the types we offer are ALWAYS and ONLY `TEXT_TYPES`, three strings
 *      that differ even ignoring case: no duplicate to
 *      drop ⇒ the echo comes back with three types, and the `len == 3` count holds.
 *    The caveat was v1's, which passed on the CLIENT's list of types.
 *    ⚠ And even if the guard failed there would be no loop: reading
 *      our own source from the pump that serves it delivers nothing (5 s of
 *      waiting, then "wrote nothing"), so no text goes back up to the client
 *      to be re-offered. */
static bool our_types(const Offer *offer)
{
	guint amount = 0;

	for (int i = 0; TEXT_TYPES[i]; i++, amount++)
		if (!offer_has(offer, TEXT_TYPES[i]))
			return false;
	return offer && offer->mime->len == amount;
}

static void on_type_offered(void *data, struct zwlr_data_control_offer_v1 *proxy,
                            const char *mime)
{
	Offer *offer = data;

	if (mime && *mime)
		g_ptr_array_add(offer->mime, g_strdup(mime));
}

static const struct zwlr_data_control_offer_v1_listener offer_listener = { on_type_offered };

static void on_new_offer(void *data, struct zwlr_data_control_device_v1 *device,
                             struct zwlr_data_control_offer_v1 *proxy)
{
	Offer *offer = g_new0(Offer, 1);

	offer->proxy = proxy;
	offer->mime = g_ptr_array_new_with_free_func(g_free);
	/* The offer hooks onto ITSELF: the `offer`s arrive before knowing
	 * whether it is the selection or the primary, which arrive on the same device. */
	zwlr_data_control_offer_v1_add_listener(proxy, &offer_listener, offer);
}

static Offer *offer_of(struct zwlr_data_control_offer_v1 *proxy)
{
	return proxy ? wl_proxy_get_user_data((struct wl_proxy *)proxy) : NULL;
}

static void on_selection(void *data, struct zwlr_data_control_device_v1 *device,
                         struct zwlr_data_control_offer_v1 *proxy)
{
	ClipboardKde *clipboard = data;
	Offer *offer = offer_of(proxy);

	g_mutex_lock(&clipboard->state);
	/*
	 * ⛔ THE ECHO, which here is certain: KWin's `setSelection` notifies ALL data
	 *    control devices, ours included (`seat.cpp:1257-1259`).  v1's criterion
	 *    is one of STATE: as long as the source is still ours (no
	 *    `cancelled`), an announcement with our types is ours.  When
	 *    someone else copies, the `cancelled` arrives BEFORE the announcement.
	 * ⭐ PHASE 13 — on labwc (wlroots 0.18.2) the same, `[R]` on the source:
	 *    every device is subscribed to `seat->events.set_selection` without a filter
	 *    on the originator (`wlr_data_control_v1.c:459-468`) ⇒ the echo is certain;
	 *    and `wlr_seat_set_selection` DESTROYS the old source (⇒
	 *    `cancelled`, `wlr_data_control_v1.c:145`) before emitting the
	 *    signal, in the same function (`wlr_data_device.c`).  The two
	 *    pieces of news travel on the same connection ⇒ they arrive in that order.
	 * ⚠ When whoever had copied DIES, `selection(NULL)` arrives: below
	 *   `current` becomes NULL and `incoming` stays NULL ⇒ nothing is sent to
	 *   the client, and `last` stays the earlier text (it is what is
	 *   given back to the session if the client has nothing).  In XFCE on Wayland
	 *   there is no clipboard manager: the desktop clipboard dies with
	 *   whoever copied, and it is NOT our job to keep it alive.  OUR
	 *   source instead lives as long as the child.
	 */
	if (clipboard->our && our_types(offer)) {
		g_mutex_unlock(&clipboard->state);
		log_detail(LOG_CLIPBOARD, "return announcement after our own copy: ignored");
		offer_free(offer);
		return;
	}
	g_clear_pointer(&clipboard->current, offer_free);
	clipboard->current = offer;
	/* We do not read from here: an `offer(mime)` may arrive AFTER `selection`
	 * (`kde.md` §9).  The pump reads it, after a full roundtrip. */
	clipboard->incoming = offer;
	g_mutex_unlock(&clipboard->state);
}

/* The primary selection (X11's middle button) has no counterpart
 * in the protocol: it is accepted and dropped. */
static void on_primary_selection(void *data, struct zwlr_data_control_device_v1 *device,
                                  struct zwlr_data_control_offer_v1 *proxy)
{
	offer_free(offer_of(proxy));
}

static void on_finished(void *data, struct zwlr_data_control_device_v1 *device)
{
	const ClipboardKde *clipboard = data;

	registro_dice(LOG_CLIPBOARD, "⛔ %s closed the clipboard channel: no more "
	                           "copy-paste in this session",
	              clipboard->compositor);
}

static const struct zwlr_data_control_device_v1_listener device_listener = {
	on_new_offer,
	on_selection,
	on_finished,
	on_primary_selection,
};

/* ------------------------------------------------------------------ *
 * Our source: the CLIENT's text
 * ------------------------------------------------------------------ */
static void on_data_request(void *data, struct zwlr_data_control_source_v1 *source,
                              const char *mime, int32_t fd)
{
	ClipboardKde *clipboard = data;
	guint32 serial;
	bool someone;

	/* ⛔ We do not write here: the text is on the client and must be asked for.  We put
	 *    the descriptor aside and return at once — it is the event thread. */
	g_mutex_lock(&clipboard->state);
	serial = ++clipboard->next_serial;
	g_hash_table_insert(clipboard->requests, GUINT_TO_POINTER(serial), GINT_TO_POINTER(fd));
	g_mutex_unlock(&clipboard->state);

	g_mutex_lock(&clipboard->lock);
	someone = clipboard->on_request != NULL;
	if (someone)
		clipboard->on_request(serial, clipboard->data);
	g_mutex_unlock(&clipboard->lock);

	if (!someone)
		/* Nobody is listening: we answer with what there is (or close). */
		clipboard_kde_reply(clipboard, serial, NULL, 0);
}

static void on_cancelled(void *data, struct zwlr_data_control_source_v1 *source)
{
	ClipboardKde *clipboard = data;

	g_mutex_lock(&clipboard->state);
	if (clipboard->our == source)
		clipboard->our = NULL; /* from now on the announcements are real */
	g_mutex_unlock(&clipboard->state);
	zwlr_data_control_source_v1_destroy(source);
}

static const struct zwlr_data_control_source_v1_listener source_listener = {
	on_data_request, on_cancelled
};

/* ------------------------------------------------------------------ *
 * The Wayland registry
 * ------------------------------------------------------------------ */
static void on_global(void *data, struct wl_registry *registry, uint32_t name,
                       const char *interfaccia, uint32_t version)
{
	ClipboardKde *clipboard = data;

	if (!g_strcmp0(interfaccia, zwlr_data_control_manager_v1_interface.name)) {
		/* Version 2 adds the primary, which we do not need: we bind what there is. */
		clipboard->handler_version = MIN(version, 2u);
		clipboard->protocol = zwlr_data_control_manager_v1_interface.name;
		clipboard->handler = wl_registry_bind(registry, name,
		                                    &zwlr_data_control_manager_v1_interface,
		                                    clipboard->handler_version);
	} else if (!g_strcmp0(interfaccia, ext_data_control_manager_v1_interface.name)) {
		/* Bound AFTER the registry roundtrip, and only if zwlr is missing: see
		 * `bind_ext_if_needed`. */
		clipboard->ext_name = name;
		clipboard->ext_version = version;
	} else if (!g_strcmp0(interfaccia, wl_seat_interface.name) && !clipboard->seat) {
		clipboard->seat = wl_registry_bind(registry, name, &wl_seat_interface, 1);
	}
}

static void on_global_away(void *data, struct wl_registry *registry, uint32_t name)
{
}

static const struct wl_registry_listener registry_listener = { on_global, on_global_away };

/* ⛔ [M] 6 Oct 2026, Ubuntu 26.04 / KWin 6.6.6: KWin NO LONGER exposes
 *    `zwlr_data_control_manager_v1`, only the standard `ext_data_control_manager_v1`
 *    (wayland-protocols, staging) ⇒ "the clipboard does NOT open" and F-014/F-014C/
 *    F-015C red.  On KWin 6.3 (Debian 13) the old one was still there.
 *    ⭐ The two protocols are IDENTICAL ON THE WIRE: same requests, same events,
 *    same arguments, in the same order (ext v1 = zwlr v2, primary included;
 *    the XMLs in `protocolli/` compared).  ⇒ We bind the manager with ITS name
 *    (`ext_...`, the one the compositor checks) and drive it with the
 *    zwlr functions: the opcodes and signatures are the same, and the children (device,
 *    source, offer) are born from new_id, where the interface name does not
 *    travel.  One code for both, instead of 800 doubled lines.
 *    zwlr is preferred when both are present: it is the path already tested. */
static void bind_ext_if_needed(ClipboardKde *clipboard)
{
	if (clipboard->handler || !clipboard->ext_name)
		return;
	clipboard->handler_version = 1;
	clipboard->protocol = ext_data_control_manager_v1_interface.name;
	clipboard->handler = (struct zwlr_data_control_manager_v1 *)wl_registry_bind(
	    clipboard->registry, clipboard->ext_name, &ext_data_control_manager_v1_interface, 1);
}

/* ------------------------------------------------------------------ *
 * Reading the session's text
 * ------------------------------------------------------------------ */
/* ⛔ `POLLHUP` on read counts as "ready": whoever writes and closes (the normal
 *    case) can make `poll` return with only `POLLHUP`, and the data is
 *    in the pipe (`[M]` v1, 8 August 2026). */
static bool ready(int fd, short what)
{
	struct pollfd probe = { .fd = fd, .events = what, .revents = 0 };
	int outcome;

	do
		outcome = poll(&probe, 1, WAIT_TRANSFER_MS);
	while (outcome < 0 && errno == EINTR);
	if (outcome <= 0)
		return false;
	if (probe.revents & what)
		return true;
	return (what & POLLIN) && (probe.revents & POLLHUP);
}

/* One type, read to the end with the ceiling of `appunti.c` (ceiling PLUS ONE: a
 * text as large as the ceiling is lawful).  NULL with `why` written. */
static GBytes *read_type(ClipboardKde *clipboard, struct zwlr_data_control_offer_v1 *proxy,
                             const char *mime, const char **why)
{
	int pipe_fd[2];
	GByteArray *collection;

	if (pipe2(pipe_fd, O_CLOEXEC) != 0) {
		*why = "pipe not created";
		return NULL;
	}
	zwlr_data_control_offer_v1_receive(proxy, mime, pipe_fd[1]);
	wl_display_flush(clipboard->display);
	/* ⛔ Our copy of the write end is closed AT ONCE, or the read
	 *    never ends. */
	close(pipe_fd[1]);

	collection = g_byte_array_new();
	for (;;) {
		guint8 piece[16384];
		ssize_t amount;

		if (!ready(pipe_fd[0], POLLIN)) {
			close(pipe_fd[0]);
			g_byte_array_unref(collection);
			*why = "whoever owns the clipboard wrote nothing for 5 s";
			return NULL;
		}
		amount = read(pipe_fd[0], piece, sizeof piece);
		if (amount < 0 && errno == EINTR)
			continue;
		if (amount <= 0)
			break;
		if (collection->len + (guint)amount > CLIPBOARD_CAP) {
			close(pipe_fd[0]);
			g_byte_array_unref(collection);
			*why = "clipboard over the ceiling (§5.4): left where it is, NOT truncated";
			return NULL;
		}
		g_byte_array_append(collection, piece, (guint)amount);
	}
	close(pipe_fd[0]);
	return g_byte_array_free_to_bytes(collection);
}

/* The text of the current selection, along the row of types: the first that
 * delivers valid UTF-8.  NULL if there is no text (and it says so). */
static char *read_text(ClipboardKde *clipboard, size_t *byte)
{
	struct zwlr_data_control_offer_v1 *proxy = NULL;
	Offer *offer;
	GPtrArray *types = NULL;

	g_mutex_lock(&clipboard->state);
	offer = clipboard->current;
	if (offer) {
		proxy = offer->proxy;
		types = g_ptr_array_ref(offer->mime);
	}
	g_mutex_unlock(&clipboard->state);

	if (!proxy || !types || types->len == 0) {
		if (types)
			g_ptr_array_unref(types);
		log_detail(LOG_CLIPBOARD, "the session has nothing in the clipboard");
		return NULL;
	}

	for (int i = 0; TEXT_TYPES[i]; i++) {
		bool c_e = false;
		const char *why = NULL;
		GBytes *data;
		gsize amount = 0;
		const char *start;

		for (guint k = 0; k < types->len && !c_e; k++)
			c_e = g_ascii_strcasecmp(g_ptr_array_index(types, k), TEXT_TYPES[i]) == 0;
		if (!c_e)
			continue;
		data = read_type(clipboard, proxy, TEXT_TYPES[i], &why);
		if (!data) {
			registro_dice(LOG_CLIPBOARD, "⛔ «%s» cannot be read: %s", TEXT_TYPES[i], why);
			continue;
		}
		start = g_bytes_get_data(data, &amount);
		if (!g_utf8_validate_len(start, (gssize)amount, NULL)) {
			registro_dice(LOG_CLIPBOARD, "⛔ «%s» is not valid UTF-8 (%zu bytes): "
			                           "skipping it", TEXT_TYPES[i], (size_t)amount);
			g_bytes_unref(data);
			continue;
		}
		*byte = amount;
		{
			char *text = g_strndup(start, amount);

			g_bytes_unref(data);
			g_ptr_array_unref(types);
			log_detail(LOG_CLIPBOARD, "read %zu bytes of «%s» from the session",
			                   (size_t)amount, TEXT_TYPES[i]);
			return text;
		}
	}

	{
		GString *listing = g_string_new(NULL);

		for (guint k = 0; k < types->len; k++)
			g_string_append_printf(listing, "%s%s", k ? ", " : "",
			                       (const char *)g_ptr_array_index(types, k));
		registro_dice(LOG_CLIPBOARD,
		              "the session copied something that is not text (%s): not "
		              "announced.  ⚠ `DECISIONI.md` §5-ter.1 — text only",
		              listing->str);
		g_string_free(listing, TRUE);
	}
	g_ptr_array_unref(types);
	return NULL;
}

/* Hands the listener the text of the last announcement. */
static void delivery_announcement(ClipboardKde *clipboard)
{
	char *text;
	size_t byte = 0;
	bool c_era;

	g_mutex_lock(&clipboard->state);
	c_era = clipboard->incoming != NULL;
	clipboard->incoming = NULL;
	g_mutex_unlock(&clipboard->state);
	if (!c_era)
		return;

	text = read_text(clipboard, &byte);
	if (!text)
		return;
	g_mutex_lock(&clipboard->lock);
	g_free(clipboard->last);
	clipboard->last = g_strdup(text);
	clipboard->last_byte = byte;
	if (clipboard->on_text)
		clipboard->on_text(text, byte, clipboard->data);
	g_mutex_unlock(&clipboard->lock);
	registro_dice(LOG_CLIPBOARD, "⭐ the session copied %zu bytes of text", byte);
	g_free(text);
}

/* ------------------------------------------------------------------ *
 * The loop
 * ------------------------------------------------------------------ */
static bool runs(ClipboardKde *clipboard, int wait_ms)
{
	struct pollfd probe[2];
	int amount = 1;

	while (wl_display_prepare_read(clipboard->display) != 0)
		if (wl_display_dispatch_pending(clipboard->display) < 0)
			return false;
	if (wl_display_flush(clipboard->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(clipboard->display);
		return false;
	}
	probe[0].fd = wl_display_get_fd(clipboard->display);
	probe[0].events = POLLIN;
	probe[0].revents = 0;
	if (clipboard->wake[0] >= 0) {
		probe[1].fd = clipboard->wake[0];
		probe[1].events = POLLIN;
		probe[1].revents = 0;
		amount = 2;
	}
	if (poll(probe, (nfds_t)amount, wait_ms) <= 0) {
		wl_display_cancel_read(clipboard->display);
		return true;
	}
	if (amount == 2 && (probe[1].revents & POLLIN)) {
		wl_display_cancel_read(clipboard->display);
		return false;
	}
	if (!(probe[0].revents & POLLIN)) {
		wl_display_cancel_read(clipboard->display);
		return !(probe[0].revents & (POLLERR | POLLHUP));
	}
	if (wl_display_read_events(clipboard->display) < 0)
		return false;
	if (wl_display_dispatch_pending(clipboard->display) < 0)
		return false;
	/* ⛔ The full roundtrip BEFORE reading: the `offer(mime)`s may arrive
	 *    after the `selection` they belong to. */
	if (clipboard->incoming) {
		wl_display_roundtrip(clipboard->display);
		delivery_announcement(clipboard);
	}
	return true;
}

static gpointer thread_pump(gpointer data)
{
	ClipboardKde *clipboard = data;

	while (runs(clipboard, -1))
		;
	log_detail(LOG_CLIPBOARD, "the clipboard's Wayland connection closed");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * The door
 * ------------------------------------------------------------------ */
/* ⭐ PHASE 13 — the same opening for the two families: only the name in the
 *    lines changes.  ⚠ `kwin_display_open()` stays, and on labwc it is fine as
 *    it is: it takes `WAYLAND_DISPLAY` or the first `wayland-0..9` that answers,
 *    WITHOUT looking at who is behind it (`kwin.c`, `[R]`).  Moving it to a
 *    neutral file would mean touching `kwin.c`, which carries KDE's video, to
 *    gain only a name. */
static ClipboardKde *open_on(const char *compositor, GError **mistake)
{
	ClipboardKde *clipboard = g_new0(ClipboardKde, 1);

	clipboard->compositor = compositor;
	clipboard->wake[0] = clipboard->wake[1] = -1;
	g_mutex_init(&clipboard->state);
	g_mutex_init(&clipboard->lock);
	clipboard->requests = g_hash_table_new(NULL, NULL);

	clipboard->display = kwin_display_open(clipboard->socket, sizeof clipboard->socket);
	if (!clipboard->display) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable for the clipboard");
		goto fault;
	}
	clipboard->registry = wl_display_get_registry(clipboard->display);
	wl_registry_add_listener(clipboard->registry, &registry_listener, clipboard);
	wl_display_roundtrip(clipboard->display);
	wl_display_roundtrip(clipboard->display);
	bind_ext_if_needed(clipboard);
	if (!clipboard->handler) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "%s exposes neither zwlr_data_control_manager_v1 nor "
		            "ext_data_control_manager_v1", compositor);
		goto fault;
	}
	if (!clipboard->seat) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no wl_seat: without it, there is no clipboard to ask for");
		goto fault;
	}
	clipboard->device =
	    zwlr_data_control_manager_v1_get_data_device(clipboard->handler, clipboard->seat);
	zwlr_data_control_device_v1_add_listener(clipboard->device, &device_listener,
	                                         clipboard);
	/* ⭐ KWin sends the current selection AT ONCE (`seat.cpp:228-229`), even
	 *    empty: it is the asymmetry that on Mutter must be asked for (`clipboard_read_now`).
	 *    Here we just take it: the read is done by `clipboard_read_now`, as
	 *    on GNOME, when `figlio.c` is ready to receive it. */
	wl_display_roundtrip(clipboard->display);
	wl_display_roundtrip(clipboard->display);
	g_mutex_lock(&clipboard->state);
	clipboard->incoming = NULL;
	g_mutex_unlock(&clipboard->state);

	if (!g_unix_open_pipe(clipboard->wake, O_CLOEXEC, NULL))
		clipboard->wake[0] = clipboard->wake[1] = -1;
	clipboard->pump = g_thread_new("remotix-appunti", thread_pump, clipboard);

	registro_dice(LOG_CLIPBOARD, "⭐ clipboard hooked to %s on socket «%s» with "
	                           "%s v%u",
	              compositor, clipboard->socket, clipboard->protocol,
	              clipboard->handler_version);
	return clipboard;

fault:
	clipboard_kde_close(clipboard);
	return NULL;
}

ClipboardKde *clipboard_kde_open(GError **mistake)
{
	return open_on("KWin", mistake);
}

ClipboardKde *clipboard_kde_open_wlroots(GError **mistake)
{
	return open_on("labwc", mistake);
}

void clipboard_kde_close(ClipboardKde *clipboard)
{
	GHashTableIter cur_round;
	gpointer key, value;

	if (!clipboard)
		return;
	clipboard_kde_listen(clipboard, NULL, NULL, NULL);

	if (clipboard->wake[1] >= 0) {
		ssize_t written = write(clipboard->wake[1], "x", 1);

		(void)written;
	}
	if (clipboard->pump)
		g_thread_join(clipboard->pump);

	/* Transfers left half way are closed: whoever waits sees an end. */
	g_hash_table_iter_init(&cur_round, clipboard->requests);
	while (g_hash_table_iter_next(&cur_round, &key, &value))
		close(GPOINTER_TO_INT(value));
	g_hash_table_unref(clipboard->requests);

	g_clear_pointer(&clipboard->current, offer_free);
	if (clipboard->our)
		zwlr_data_control_source_v1_destroy(clipboard->our);
	if (clipboard->device)
		zwlr_data_control_device_v1_destroy(clipboard->device);
	if (clipboard->handler)
		zwlr_data_control_manager_v1_destroy(clipboard->handler);
	if (clipboard->seat)
		wl_seat_destroy(clipboard->seat);
	if (clipboard->registry)
		wl_registry_destroy(clipboard->registry);
	if (clipboard->display)
		wl_display_disconnect(clipboard->display);
	for (int i = 0; i < 2; i++)
		if (clipboard->wake[i] >= 0)
			close(clipboard->wake[i]);
	g_free(clipboard->last);
	g_mutex_clear(&clipboard->state);
	g_mutex_clear(&clipboard->lock);
	g_free(clipboard);
}

void clipboard_kde_listen(ClipboardKde *clipboard, ClipboardOnText on_text,
                         ClipboardOnRequest on_request, void *data)
{
	if (!clipboard)
		return;
	g_mutex_lock(&clipboard->lock);
	clipboard->on_text = on_text;
	clipboard->on_request = on_request;
	clipboard->data = data;
	g_mutex_unlock(&clipboard->lock);
}

char *clipboard_kde_last_text(ClipboardKde *clipboard, size_t *byte)
{
	char *copied;

	if (!clipboard)
		return NULL;
	g_mutex_lock(&clipboard->lock);
	copied = clipboard->last ? g_strdup(clipboard->last) : NULL;
	if (byte)
		*byte = clipboard->last ? clipboard->last_byte : 0;
	g_mutex_unlock(&clipboard->lock);
	return copied;
}

void clipboard_kde_read_now(ClipboardKde *clipboard)
{
	char *text;
	size_t byte = 0;

	if (!clipboard)
		return;
	text = read_text(clipboard, &byte);
	if (!text) {
		log_detail(LOG_CLIPBOARD, "the session had no clipboard to give us at the "
		                                "time of switching on: it is not a fault");
		return;
	}
	registro_dice(LOG_CLIPBOARD, "⭐ the session already had %zu bytes in the clipboard: "
	                           "announcing them to the client", byte);
	g_mutex_lock(&clipboard->lock);
	g_free(clipboard->last);
	clipboard->last = g_strdup(text);
	clipboard->last_byte = byte;
	if (clipboard->on_text)
		clipboard->on_text(text, byte, clipboard->data);
	g_mutex_unlock(&clipboard->lock);
	g_free(text);
}

gboolean clipboard_kde_offer(ClipboardKde *clipboard, GError **mistake)
{
	struct zwlr_data_control_source_v1 *source;
	gint64 t_now;

	if (!clipboard || !clipboard->handler) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED, "clipboard not open");
		return FALSE;
	}
	/* The minimum step towards klipper: we wait, we do not skip. */
	g_mutex_lock(&clipboard->state);
	t_now = g_get_monotonic_time();
	if (clipboard->last_set && t_now - clipboard->last_set < MIN_STEP_US) {
		gint64 stays = MIN_STEP_US - (t_now - clipboard->last_set);

		g_mutex_unlock(&clipboard->state);
		g_usleep((gulong)stays);
		g_mutex_lock(&clipboard->state);
	}
	clipboard->last_set = g_get_monotonic_time();
	g_mutex_unlock(&clipboard->state);

	source = zwlr_data_control_manager_v1_create_data_source(clipboard->handler);
	zwlr_data_control_source_v1_add_listener(source, &source_listener, clipboard);
	for (int i = 0; TEXT_TYPES[i]; i++)
		zwlr_data_control_source_v1_offer(source, TEXT_TYPES[i]);

	/* ⚠ The old source is NOT destroyed here: KWin sends it `cancelled`, and
	 *   that callback destroys it. */
	g_mutex_lock(&clipboard->state);
	clipboard->our = source;
	g_mutex_unlock(&clipboard->state);

	zwlr_data_control_device_v1_set_selection(clipboard->device, source);
	wl_display_flush(clipboard->display);
	log_detail(LOG_CLIPBOARD, "offered the client's text to the session (%d types)",
	                   (int)(sizeof TEXT_TYPES / sizeof *TEXT_TYPES) - 1);
	return TRUE;
}

void clipboard_kde_reply(ClipboardKde *clipboard, uint32_t serial, const char *text,
                          size_t byte)
{
	gpointer value;
	char *fallback = NULL;
	size_t written = 0;
	int fd;

	if (!clipboard)
		return;
	g_mutex_lock(&clipboard->state);
	if (!g_hash_table_steal_extended(clipboard->requests, GUINT_TO_POINTER(serial), NULL,
	                                 &value)) {
		g_mutex_unlock(&clipboard->state);
		registro_dice(LOG_CLIPBOARD, "⚠ answer to a clipboard request that does not exist "
		                           "(serial %u)", serial);
		return;
	}
	g_mutex_unlock(&clipboard->state);
	fd = GPOINTER_TO_INT(value);

	/* ⭐ As on GNOME: if the client has nothing, the session gets back the
	 *    text IT had — connecting does not erase the desktop clipboard. */
	if (!text || byte == 0) {
		size_t amount = 0;

		fallback = clipboard_kde_last_text(clipboard, &amount);
		if (fallback && amount > 0) {
			registro_dice(LOG_CLIPBOARD, "⭐ the client has no clipboard for request %u: "
			                           "giving back to the session the %zu bytes IT had",
			              serial, amount);
			text = fallback;
			byte = amount;
		}
	} else {
		g_mutex_lock(&clipboard->lock);
		g_free(clipboard->last);
		clipboard->last = g_strndup(text, byte);
		clipboard->last_byte = byte;
		g_mutex_unlock(&clipboard->lock);
	}

	/* ⛔ It is ALWAYS closed, even without data: the end of the stream is the `close`. */
	while (text && written < byte) {
		ssize_t done_ones;

		if (!ready(fd, POLLOUT)) {
			registro_dice(LOG_CLIPBOARD, "⛔ whoever is pasting does not read: %zu bytes of %zu, "
			                           "then I give up", written, byte);
			break;
		}
		done_ones = write(fd, text + written, byte - written);
		if (done_ones < 0 && (errno == EINTR || errno == EAGAIN))
			continue;
		if (done_ones <= 0)
			break; /* EPIPE: whoever was pasting has gone */
		written += (size_t)done_ones;
	}
	close(fd);
	if (text)
		log_detail(LOG_CLIPBOARD, "delivered %zu bytes to the session (request %u)",
		                   written, serial);
	else
		log_detail(LOG_CLIPBOARD, "request %u closed with «I do not have it»", serial);
	g_free(fallback);
}
