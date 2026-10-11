/*
 * wlr_input.c — the virtual keyboard and pointer on wlroots.  The why and the
 * division of labour with `input.c` are in `wlr_input.h`.
 *
 * ⛔⛔ THE FIVE SILENT TRAPS of `STUDI.md` §xfce §7.2, and where they are here:
 *
 *   1. the wheel wants ±1 notches, not ±120         → `wlr_input_rotella()`
 *   2. `value` must never be 0                      → same: sent only with
 *                                                      at least one notch
 *   3. without `frame` nothing arrives              → `cornice()` after EVERY
 *                                                      pointer gesture
 *   4. the modifiers are sent by us, always         → `send_modifiers()`
 *   5. `wlr_pointer_finish()` does not release buttons → `wlr_input_close()`
 *
 * ⚠ All five are `[R]` in the study (wlroots 0.18.2, labwc 0.8.3, the
 *   Trixie versions).  ⭐ `[M]` 21 Sep 2026 ON THE LAPTOP — labwc 0.8.3
 *   headless in a private folder, witness `banchi/06-b33-testimone.c`,
 *   ⛔ NOT the test machine and NOT a whole XFCE session:
 *     · Shift+A: the witness sees `MODIFICATORI premuti 1` BEFORE key 30;
 *       the letter `@` (us) arrives as Shift + key 3;
 *     · CapsLock repeated three times: it locks ONCE, the second real
 *       press unlocks;
 *     · wheel +120 from the client ⇒ `v120 -120`, `valore -15` (up); +60 +60 ⇒ one
 *       notch only; horizontal +120 ⇒ `+120`;
 *     · pointer 640,360 and 1279,719 exact; 5000,5000 saturated; canvas 1920×1080
 *       on a 1280×720 output ⇒ 480,270 arrives at 320,180 (the proportion holds);
 *     · double `press` + one `release` ⇒ the witness sees ONE pair;
 *     · layout `de` ⇒ new keymap at the witness and `z` on key 21;
 *     · closing with Ctrl and left down ⇒ the witness sees the two releases.
 *   ⚠ What is NOT measured: a real XFCE session (panel, GTK applications
 *     that look at the frame), labwc's shortcuts (§7.5), and the
 *     whole path from the browser.
 */
#include "wlr_input.h"

#include "registro.h"

#include "virtual-keyboard-unstable-v1-client-protocol.h"
#include "wlr-virtual-pointer-unstable-v1-client-protocol.h"

#include <errno.h>
#include <gio/gio.h>
#include <poll.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>
#include <xkbcommon/xkbcommon.h>

/* ⚠ The same area as `input.c`: whoever reads the log looks for input under
 *   one word, not under the name of the module that transports it. */
#define AREA "input"

/* ⛔ The ceiling of the codes, the same as `input.c` (`MAX_KEY`/`MAX_BOTTONE`):
 *    evdev goes up to `KEY_MAX` = 0x2ff. */
#define MAX_CODE 0x300u

/*
 * ⭐ The value of one notch.  wayvnc uses **15.0**, "magic value measured with
 *    `wev`" (§7.2 trap 2), and it is the step libinput gives a real
 *    wheel: applications that look at `value` and not `discrete` scroll
 *    as with a mouse.  ⛔ Never zero: with `value == 0` wlroots sends an
 *    `axis_stop` and the notch vanishes (`wlr_seat_pointer.c:369-391`).
 */
#define DETENT_VALUE 15.0

/* ⚠ The ceiling of the synchronous waits (opening, reattach).  Whoever makes them is the
 *   child's loop: a mute compositor must not stop it longer than this. */
#define WAIT_US (2 * G_USEC_PER_SEC)

struct WlrInput {
	struct wl_display *display;
	struct wl_registry *registry;
	struct wl_seat *seat;
	struct wl_output *uscita;
	struct zwp_virtual_keyboard_manager_v1 *keyboard_handler;
	struct zwlr_virtual_pointer_manager_v1 *pointer_handler;
	uint32_t pointer_version;

	struct zwp_virtual_keyboard_v1 *tastiera;
	struct zwlr_virtual_pointer_v1 *puntatore;

	/* ⭐ The SPY: a `wl_keyboard` taken once only, to have the session's
	 *    keymap handed over (§7.4) — and then released. */
	struct wl_keyboard *spia;
	char *session_keymap;
	size_t session_keymap_len;

	/* ⛔ The keymap IN FORCE on our keyboard, and the state that follows it. */
	struct xkb_context *ctx;
	struct xkb_keymap *keymap;
	struct xkb_state *stato;
	char *keymap_text; /* with the final zero; `keymap_len` without */
	size_t keymap_len;
	char *keymap_origin;
	bool keymap_sent;

	/* The last modifier state SENT — so as not to send it again unchanged. */
	uint32_t mod_down, mod_latched, mod_blocked, gruppo;

	/* ⛔ What THIS device has pressed: used to discard duplicates.
	 *    ⚠ It is not the count of `RCP.md` §11: that belongs to `input.c`. */
	uint8_t keys_down[MAX_CODE / 8];
	uint8_t buttons_down[MAX_CODE / 8];

	/* ⛔ The wheel accumulators, one per axis: half notches are not
	 *    lost, they add to the next one (weston does the same, §7.2). */
	int32_t vertical_remainder, horizontal_remainder;

	bool caduto;
	bool drop_logged;
};

/* ------------------------------------------------------------------------- */

static bool bit(const uint8_t *m, uint32_t n)
{
	return (m[n / 8u] & (uint8_t)(1u << (n % 8u))) != 0;
}

static void put_bit(uint8_t *m, uint32_t n, bool acceso)
{
	if (acceso)
		m[n / 8u] |= (uint8_t)(1u << (n % 8u));
	else
		m[n / 8u] &= (uint8_t)~(1u << (n % 8u));
}

/* ⚠ Protocol time is in milliseconds and can wrap: it is a label for
 *   applications, not a clock to do arithmetic on. */
static uint32_t now_ms(void)
{
	return (uint32_t)(g_get_monotonic_time() / 1000);
}

/*
 * ⛔ THE DROPPED WIRE IS SAID ONCE, AND WITH THE CAUSE.  A protocol error
 *    (ours: `no_keymap`, a wrong axis) and a dead compositor have
 *    the same symptom — the connection no longer answers — and only
 *    `wl_display_get_protocol_error()` knows the difference.
 */
static void mark_drop(WlrInput *w, const char *dove)
{
	const struct wl_interface *interfaccia = NULL;
	uint32_t id = 0;
	uint32_t codice = 0;
	int err;

	w->caduto = true;
	if (w->drop_logged)
		return;
	w->drop_logged = true;

	err = w->display ? wl_display_get_error(w->display) : 0;
	if (err == EPROTO)
		codice = wl_display_get_protocol_error(w->display, &interfaccia, &id);
	if (err == EPROTO)
		registro_dice(AREA,
		              "⛔⛔ wlroots: the compositor CLOSED the input connection "
		              "for a PROTOCOL ERROR of ours (%s, object %s@%u, code %u) — "
		              "it is a REMOTIX defect, not the desktop's.  ⚠ From now on keys "
		              "left down are released by the compositor, BUTTONS are not (§7.2 n.5)",
		              dove, interfaccia ? interfaccia->name : "?", id, codice);
	else
		registro_dice(AREA,
		              "⛔ wlroots: the input connection has DROPPED (%s: %s) — the "
		              "compositor has gone away or closed the socket",
		              dove, err ? g_strerror(err) : "no error declared");
}

/*
 * ⛔ It is sent AT ONCE: Wayland requests stay in the client's buffer
 *    until someone does a `flush`, and a key in the buffer is latency given away
 *    to the user — right on the path `CODER.md` §1-bis measures.
 * ⚠ `EAGAIN` is not a drop: the socket is full, and the next round of
 *   `wlr_input_run()` retries.
 */
static int spedisci(WlrInput *w)
{
	if (wl_display_flush(w->display) < 0 && errno != EAGAIN) {
		mark_drop(w, "flush");
		return -1;
	}
	return 0;
}

/*
 * One pump round with a deadline — the same form as `pompa()` in
 * `wlroots.c`, and for the same reason: `wl_display_roundtrip()` waits without
 * a ceiling, and a mute compositor would stop the child forever.
 */
static bool pompa(WlrInput *w, gint64 scadenza)
{
	struct pollfd pfd;
	gint64 resta;
	int r;

	while (wl_display_prepare_read(w->display) != 0) {
		if (wl_display_dispatch_pending(w->display) < 0) {
			mark_drop(w, "dispatch_pending");
			return false;
		}
	}
	if (wl_display_flush(w->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(w->display);
		mark_drop(w, "flush");
		return false;
	}
	resta = (scadenza - g_get_monotonic_time()) / 1000;
	if (resta < 0)
		resta = 0;
	pfd.fd = wl_display_get_fd(w->display);
	pfd.events = POLLIN;
	pfd.revents = 0;
	r = poll(&pfd, 1, (int)resta);
	if (r <= 0) {
		wl_display_cancel_read(w->display);
		if (r < 0 && errno != EINTR) {
			mark_drop(w, "poll");
			return false;
		}
		return true;
	}
	if (wl_display_read_events(w->display) < 0) {
		mark_drop(w, "read_events");
		return false;
	}
	if (wl_display_dispatch_pending(w->display) < 0) {
		mark_drop(w, "dispatch");
		return false;
	}
	return true;
}

static void sync_done(void *dati, struct wl_callback *cb, uint32_t x)
{
	bool *fatto = dati;

	*fatto = true;
	wl_callback_destroy(cb);
}

static const struct wl_callback_listener SYNC_LISTENER = {
	.done = sync_done,
};

/* A `roundtrip` with the ceiling.  false = dropped or expired. */
static bool sincronizza(WlrInput *w, gint64 scadenza)
{
	bool fatto = false;
	struct wl_callback *cb = wl_display_sync(w->display);

	wl_callback_add_listener(cb, &SYNC_LISTENER, &fatto);
	while (!fatto) {
		if (!pompa(w, scadenza)) {
			wl_callback_destroy(cb);
			return false;
		}
		if (!fatto && g_get_monotonic_time() >= scadenza) {
			/* ⚠ The callback stays alive and will arrive at a `fatto` that no longer
			 *   exists: its listener is removed by destroying it. */
			wl_callback_destroy(cb);
			return false;
		}
	}
	return true;
}

/* ------------------------------------------------------------------------- */
/* The spy: the session's keymap, copied from the wire (§7.4). */

static void spy_keymap(void *dati, struct wl_keyboard *k, uint32_t formato, int32_t fd,
                        uint32_t misura)
{
	WlrInput *w = dati;
	void *mappa;

	/* ⛔ The descriptor is OURS as soon as it arrives, and it is closed on every path: labwc
	 *    sends the keymap again at every keyboard change, and a descriptor
	 *    lost at every key runs the child out of descriptors in an hour. */
	if (formato != WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1 || misura == 0 || w->session_keymap) {
		close(fd);
		return;
	}
	mappa = mmap(NULL, misura, PROT_READ, MAP_PRIVATE, fd, 0);
	close(fd);
	if (mappa == MAP_FAILED)
		return;
	/* ⚠ The text is zero-terminated INSIDE `misura` (it is the protocol), but
	 *   we do not trust it: we copy and terminate ourselves. */
	w->session_keymap = g_malloc0(misura + 1);
	memcpy(w->session_keymap, mappa, misura);
	w->session_keymap_len = strnlen(w->session_keymap, misura);
	munmap(mappa, misura);
}

static void spy_enter(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf,
                       struct wl_array *tasti) {}
static void spy_leave(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf) {}
static void spy_key(void *d, struct wl_keyboard *k, uint32_t s, uint32_t t, uint32_t c,
                       uint32_t st) {}
/* ⚠ Here the real LOCKS would arrive (§7.3: labwc sends them to everyone, even
 *   without focus).  ⛔ They are not read in this increment, and it is said: the spy
 *   is released at once, and the feedback loop with our `modifiers` that
 *   §7.3 fears does not even open. */
static void spy_modifiers(void *d, struct wl_keyboard *k, uint32_t s, uint32_t g,
                              uint32_t a, uint32_t b, uint32_t gr) {}
static void spy_repetition(void *d, struct wl_keyboard *k, int32_t r, int32_t ri) {}

static const struct wl_keyboard_listener SPY_LISTENER = {
	.keymap = spy_keymap,
	.enter = spy_enter,
	.leave = spy_leave,
	.key = spy_key,
	.modifiers = spy_modifiers,
	.repeat_info = spy_repetition,
};

static void seat_capabilities(void *dati, struct wl_seat *s, uint32_t capacita)
{
	WlrInput *w = dati;

	/* ⚠ Only once: after our virtual keyboard exists, the seat
	 *   restates its capabilities, and a second spy would read OUR keymap
	 *   believing it the session's. */
	if ((capacita & WL_SEAT_CAPABILITY_KEYBOARD) && !w->spia && !w->session_keymap &&
	    !w->tastiera) {
		w->spia = wl_seat_get_keyboard(s);
		wl_keyboard_add_listener(w->spia, &SPY_LISTENER, w);
	}
}

static void seat_name(void *d, struct wl_seat *s, const char *nome) {}

static const struct wl_seat_listener SEAT_LISTENER = {
	.capabilities = seat_capabilities,
	.name = seat_name,
};

static void spy_away(WlrInput *w)
{
	if (!w->spia)
		return;
	/* ⚠ `release` exists since wl_seat v3; before there is only client-side
	 *   destruction, and the compositor keeps sending events to an object that
	 *   `libwayland` discards (closing its descriptors). */
	if (wl_keyboard_get_version(w->spia) >= WL_KEYBOARD_RELEASE_SINCE_VERSION)
		wl_keyboard_release(w->spia);
	else
		wl_keyboard_destroy(w->spia);
	w->spia = NULL;
}

/* ------------------------------------------------------------------------- */
/* The globals. */

static void registry_global(void *dati, struct wl_registry *reg, uint32_t nome,
                            const char *interfaccia, uint32_t versione)
{
	WlrInput *w = dati;

	if (g_strcmp0(interfaccia, wl_seat_interface.name) == 0) {
		/* ⛔ The FIRST seat.  labwc has one (`seat0`) and does not create
		 *    `ext_transient_seat_v1` (§7.6): we inject into the
		 *    user's, and on XFCE there is no choice. */
		if (!w->seat) {
			uint32_t v = versione < 5 ? versione : 5;

			w->seat = wl_registry_bind(reg, nome, &wl_seat_interface, v);
			wl_seat_add_listener(w->seat, &SEAT_LISTENER, w);
		}
	} else if (g_strcmp0(interfaccia, wl_output_interface.name) == 0) {
		/* ⚠ The FIRST output, like `wlroots.c`: it is the one captured, and it is
		 *   the one on which we ask to map the pointer. */
		if (!w->uscita)
			w->uscita = wl_registry_bind(reg, nome, &wl_output_interface, 1);
	} else if (g_strcmp0(interfaccia, zwp_virtual_keyboard_manager_v1_interface.name) == 0) {
		w->keyboard_handler =
			wl_registry_bind(reg, nome, &zwp_virtual_keyboard_manager_v1_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_virtual_pointer_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 2 ? versione : 2;

		w->pointer_version = v;
		w->pointer_handler =
			wl_registry_bind(reg, nome, &zwlr_virtual_pointer_manager_v1_interface, v);
	}
}

static void registry_remove(void *d, struct wl_registry *r, uint32_t nome) {}

static const struct wl_registry_listener REGISTRY_LISTENER = {
	.global = registry_global,
	.global_remove = registry_remove,
};

/* ------------------------------------------------------------------------- */
/* The keymap and the modifiers. */

/*
 * ⛔⛔ THE MODIFIERS — trap 4, and it is the one where one goes wrong silently.
 *
 * `[R]` `wlr_virtual_keyboard_v1.c:92`: wlroots builds the key event
 * with `update_state = false`, that is it does **not** update its `xkb_state`.  ⇒ The
 * pressed Shift reaches the applications as a key, but the modifier
 * state stays zero: **Shift+A gives `a`**, Ctrl+C does not copy, and no
 * error anywhere.
 *
 * ⇒ WE keep the state, with an `xkb_state` on the same keymap we
 *   sent, and after every key `modifiers` is sent if it changed.  ⭐ It is
 *   wayvnc's form: key first, modifiers after — the application sees
 *   "Shift pressed" and then "now Shift is down", as with a real keyboard.
 *
 * ⚠ `forza`: after a new keymap it is sent anyway, because the compositor has
 *   just thrown away its state and our "last sent" no longer holds.
 */
static void send_modifiers(WlrInput *w, bool forza)
{
	uint32_t giu, agganciati, bloccati, gruppo;

	if (!w->stato || !w->tastiera)
		return;
	giu = xkb_state_serialize_mods(w->stato, XKB_STATE_MODS_DEPRESSED);
	agganciati = xkb_state_serialize_mods(w->stato, XKB_STATE_MODS_LATCHED);
	bloccati = xkb_state_serialize_mods(w->stato, XKB_STATE_MODS_LOCKED);
	gruppo = xkb_state_serialize_layout(w->stato, XKB_STATE_LAYOUT_EFFECTIVE);
	if (!forza && giu == w->mod_down && agganciati == w->mod_latched &&
	    bloccati == w->mod_blocked && gruppo == w->gruppo)
		return;
	w->mod_down = giu;
	w->mod_latched = agganciati;
	w->mod_blocked = bloccati;
	w->gruppo = gruppo;
	zwp_virtual_keyboard_v1_modifiers(w->tastiera, giu, agganciati, bloccati, gruppo);
}

/*
 * Sends `km` as the keymap of our keyboard, and rebuilds the state on it.
 *
 * ⛔ The text sent is `xkb_keymap_get_as_string()` of the ALREADY
 *    COMPILED keymap, with the final zero inside the size: wlroots reads it back with
 *    `xkb_keymap_new_from_string()`, which wants the terminator — and a keymap that
 *    does not compile on the other side does not return a gentle error, it closes the
 *    connection.
 */
static int put_keymap(WlrInput *w, struct xkb_keymap *km, const char *origine,
                        GError **sbaglio)
{
	char *testo;
	size_t len;
	int fd;
	struct xkb_state *stato;

	if (w->caduto || !w->tastiera) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the input connection has dropped: the keymap has nowhere to go");
		xkb_keymap_unref(km);
		return -1;
	}
	testo = xkb_keymap_get_as_string(km, XKB_KEYMAP_FORMAT_TEXT_V1);
	stato = xkb_state_new(km);
	if (!testo || !stato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "xkbcommon did not serialise keymap «%s»", origine);
		free(testo);
		if (stato)
			xkb_state_unref(stato);
		xkb_keymap_unref(km);
		return -1;
	}
	len = strlen(testo);

	fd = memfd_create("remotix-keymap", MFD_CLOEXEC);
	if (fd < 0 || write(fd, testo, len + 1) != (ssize_t)(len + 1)) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
		            "the keymap does not write into the memfd: %s", g_strerror(errno));
		if (fd >= 0)
			close(fd);
		free(testo);
		xkb_state_unref(stato);
		xkb_keymap_unref(km);
		return -1;
	}
	/* ⚠ `libwayland` duplicates the descriptor while packing the request:
	 *   ours is closed right after, and it is not a double close. */
	zwp_virtual_keyboard_v1_keymap(w->tastiera, WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1, fd,
	                               (uint32_t)(len + 1));
	close(fd);

	/* ⛔ The new state TAKES BACK the keys that are still down — as
	 *    wlroots does on its side (`wlr_keyboard_set_keymap`).  The caller has
	 *    already released them, and normally there are none; but if the release had not
	 *    left, a virgin state would say "Shift up" to a compositor
	 *    that holds it down. */
	for (uint32_t c = 0; c < MAX_CODE; c++)
		if (bit(w->keys_down, c))
			xkb_state_update_key(stato, c + 8, XKB_KEY_DOWN);

	if (w->stato)
		xkb_state_unref(w->stato);
	if (w->keymap)
		xkb_keymap_unref(w->keymap);
	w->stato = stato;
	w->keymap = km;
	free(w->keymap_text);
	w->keymap_text = testo;
	w->keymap_len = len;
	g_free(w->keymap_origin);
	w->keymap_origin = g_strdup(origine);
	w->keymap_sent = true;

	send_modifiers(w, true);
	return spedisci(w);
}

/*
 * `de(neo)` → layout `de`, variant `neo`.  ⛔ The same `RCP.md` §4.5 form
 * that `tastiera.c` accepts; and the characters are checked, because this string
 * comes from the wire.
 */
static bool split_name(const char *nome, char *layout, size_t nl, char *variante, size_t nv)
{
	const char *par = strchr(nome, '(');
	size_t ll = par ? (size_t)(par - nome) : strlen(nome);
	size_t lv = 0;

	for (const char *c = nome; *c; c++)
		if (!g_ascii_isalnum(*c) && *c != '_' && *c != '-' && *c != '(' && *c != ')')
			return false;
	if (ll == 0 || ll >= nl)
		return false;
	memcpy(layout, nome, ll);
	layout[ll] = 0;
	variante[0] = 0;
	if (par) {
		const char *chiusa = strchr(par + 1, ')');

		if (!chiusa || chiusa[1] != 0)
			return false;
		lv = (size_t)(chiusa - par - 1);
		if (lv >= nv)
			return false;
		memcpy(variante, par + 1, lv);
		variante[lv] = 0;
	}
	return true;
}

int wlr_input_keymap_da_nome(WlrInput *w, const char *nome, GError **sbaglio)
{
	char layout[72], variante[72];
	struct xkb_rule_names nomi;
	struct xkb_keymap *km;

	g_return_val_if_fail(w != NULL && nome != NULL, -1);

	if (!split_name(nome, layout, sizeof layout, variante, sizeof variante)) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "«%.64s» is not an XKB layout name (RCP.md §4.5)", nome);
		return -1;
	}
	/* ⚠ All five fields, like `tastiera.c`: a NULL field is filled by
	 *   the environment (`XKB_DEFAULT_*`), and the REQUESTED layout must not
	 *   depend on whoever started the service. */
	nomi.rules = "evdev";
	nomi.model = "pc105";
	nomi.layout = layout;
	nomi.variant = variante;
	nomi.options = "";
	km = xkb_keymap_new_from_names(w->ctx, &nomi, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!km) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "xkbcommon does not compile layout «%s»", nome);
		return -1;
	}
	return put_keymap(w, km, nome, sbaglio);
}

int wlr_input_keymap_da_testo(WlrInput *w, const char *testo, size_t lunghezza,
                              const char *origine, GError **sbaglio)
{
	struct xkb_keymap *km;

	g_return_val_if_fail(w != NULL && testo != NULL, -1);
	km = xkb_keymap_new_from_buffer(w->ctx, testo, lunghezza, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!km) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_DATA,
		            "keymap «%s» does not compile", origine ? origine : "?");
		return -1;
	}
	return put_keymap(w, km, origine ? origine : "?", sbaglio);
}

const char *wlr_input_keymap(const WlrInput *w, size_t *lunghezza)
{
	if (lunghezza)
		*lunghezza = w && w->keymap_text ? w->keymap_len : 0;
	return w ? w->keymap_text : NULL;
}

const char *wlr_input_keymap_origin(const WlrInput *w)
{
	return w && w->keymap_origin ? w->keymap_origin : "none";
}

/* ------------------------------------------------------------------------- */

WlrInput *wlr_input_open(GError **sbaglio)
{
	WlrInput *w = g_new0(WlrInput, 1);
	const char *nome = g_getenv("WAYLAND_DISPLAY");
	gint64 scadenza;
	g_autoptr(GError) sb_keymap = NULL;
	int esito;

	w->display = wl_display_connect(nome);
	if (!w->display && !nome) {
		/* ⚠ The same search as `wlr_apri()`: the child does not inherit
		 *   `WAYLAND_DISPLAY` from the compositor it has just brought to life. */
		for (int i = 0; i < 10 && !w->display; i++) {
			g_autofree char *tenta = g_strdup_printf("wayland-%d", i);

			w->display = wl_display_connect(tenta);
		}
	}
	if (!w->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable in XDG_RUNTIME_DIR=%s",
		            g_getenv("XDG_RUNTIME_DIR") ?: "(not set)");
		wlr_input_close(w);
		return NULL;
	}
	w->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!w->ctx) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "xkbcommon context not created");
		wlr_input_close(w);
		return NULL;
	}

	w->registry = wl_display_get_registry(w->display);
	wl_registry_add_listener(w->registry, &REGISTRY_LISTENER, w);

	/* ⚠ THREE rounds: the globals; the seat capabilities (which ask for the spy); the
	 *   keymap the spy receives.  With a single ceiling for all three. */
	scadenza = g_get_monotonic_time() + WAIT_US;
	if (!sincronizza(w, scadenza) || !sincronizza(w, scadenza)) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the compositor did not answer the list of globals within %d s",
		            (int)(WAIT_US / G_USEC_PER_SEC));
		wlr_input_close(w);
		return NULL;
	}
	if (w->spia)
		(void)sincronizza(w, scadenza); /* ⚠ without keymap we go on: below there is the fallback */
	spy_away(w);

	if (!w->seat || !w->keyboard_handler || !w->pointer_handler) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce %s%s%s: on this desktop input does not "
		            "pass through here",
		            w->seat ? "" : "wl_seat ",
		            w->keyboard_handler ? "" : "zwp_virtual_keyboard_manager_v1 ",
		            w->pointer_handler ? "" : "zwlr_virtual_pointer_manager_v1");
		wlr_input_close(w);
		return NULL;
	}

	w->tastiera = zwp_virtual_keyboard_manager_v1_create_virtual_keyboard(w->keyboard_handler,
	                                                                       w->seat);
	/*
	 * ⭐ The pointer is BOUND TO THE OUTPUT when the manager is v2: absolute
	 *    coordinates are then relative to it, and not to the space of all
	 *    outputs.  ⚠ With a single output it is the same thing; with two, without this,
	 *    the pointer would end up spread over both.  `[?]` That labwc honours
	 *    the suggested output (`wlr_cursor_map_input_to_output`) is read in the
	 *    study, not measured.
	 */
	if (w->pointer_version >= 2 && w->uscita)
		w->puntatore = zwlr_virtual_pointer_manager_v1_create_virtual_pointer_with_output(
			w->pointer_handler, w->seat, w->uscita);
	else
		w->puntatore = zwlr_virtual_pointer_manager_v1_create_virtual_pointer(
			w->pointer_handler, w->seat);

	/* ⛔ The keymap BEFORE any key — and so before returning. */
	if (w->session_keymap)
		esito = wlr_input_keymap_da_testo(w, w->session_keymap, w->session_keymap_len,
		                                  "session", &sb_keymap);
	else
		esito = -1;
	if (esito != 0) {
		/*
		 * ⚠ THE FALLBACK, DECLARED: the session did not give us its keymap
		 *   (`[M]` it happens on headless labwc: without a real keyboard the seat
		 *   declares capability 0 and the spy is not born — `wlr_input.h`).  Then
		 *   `xkbcommon` composes it from the child's environment (`XKB_DEFAULT_*`, or
		 *   `us`).  ⛔ It may NOT be the session's layout: the
		 *   layout negotiated with the client (`input_disposizione()`), which
		 *   arrives right after the opening, replaces it.
		 */
		struct xkb_rule_names vuoti = { 0 };
		struct xkb_keymap *km;

		if (sb_keymap)
			registro_dice(AREA, "⚠ wlroots: the session's keymap is not used (%s)",
			              sb_keymap->message);
		g_clear_error(&sb_keymap);
		km = xkb_keymap_new_from_names(w->ctx, &vuoti, XKB_KEYMAP_COMPILE_NO_FLAGS);
		if (!km || put_keymap(w, km, "environment", &sb_keymap) != 0) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
			            "no keymap to present to the virtual keyboard (%s): without one, "
			            "the first key would close the connection (no_keymap)",
			            sb_keymap ? sb_keymap->message : "xkbcommon does not compose even "
			                                             "the environment's one");
			wlr_input_close(w);
			return NULL;
		}
		registro_dice(AREA,
		              "⚠ DECLARED FALLBACK: the session did not hand over its keymap — "
		              "presenting the ENVIRONMENT's (layout «%s»).  ⛔ It may not be "
		              "the session's: the layout negotiated with the client corrects it",
		              xkb_keymap_layout_get_name(w->keymap, 0) ?: "unnamed");
	}

	/* ⛔ And we check that the compositor accepted everything: a protocol
	 *    error arrives AFTER the request, and without this round it would be
	 *    discovered at the user's first key. */
	if (!sincronizza(w, g_get_monotonic_time() + WAIT_US) || w->caduto) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the compositor did not accept the virtual devices (the log "
		            "says why)");
		wlr_input_close(w);
		return NULL;
	}

	registro_dice(AREA,
	              "⭐ wlroots: virtual keyboard and pointer created (pointer v%u%s), keymap "
	              "from %s, %zu bytes",
	              w->pointer_version,
	              w->pointer_version >= 2 && w->uscita ? ", bound to the output" : "",
	              w->keymap_origin, w->keymap_len);
	return w;
}

int wlr_input_descriptor(WlrInput *w)
{
	if (!w || w->caduto || !w->display)
		return -1;
	return wl_display_get_fd(w->display);
}

bool wlr_input_dropped(const WlrInput *w)
{
	return !w || w->caduto;
}

int wlr_input_run(WlrInput *w)
{
	struct pollfd pfd;
	int n;

	if (!w || w->caduto)
		return -1;
	/* ⛔ It NEVER waits: it is the child's loop that calls, and this is
	 *    its safety net at every round — `poll` with zero. */
	while (wl_display_prepare_read(w->display) != 0) {
		if (wl_display_dispatch_pending(w->display) < 0) {
			mark_drop(w, "dispatch_pending");
			return -1;
		}
	}
	if (wl_display_flush(w->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(w->display);
		mark_drop(w, "flush");
		return -1;
	}
	pfd.fd = wl_display_get_fd(w->display);
	pfd.events = POLLIN;
	pfd.revents = 0;
	if (poll(&pfd, 1, 0) > 0) {
		if (wl_display_read_events(w->display) < 0) {
			mark_drop(w, "read_events");
			return -1;
		}
	} else {
		wl_display_cancel_read(w->display);
	}
	n = wl_display_dispatch_pending(w->display);
	if (n < 0) {
		mark_drop(w, "dispatch");
		return -1;
	}
	return n;
}

/* ------------------------------------------------------------------------- */
/* The gestures. */

int wlr_input_key(WlrInput *w, uint16_t codice, bool premuto)
{
	if (!w || w->caduto || !w->tastiera || codice >= MAX_CODE)
		return -1;
	/* ⛔ `no_keymap`: without a keymap the key is a protocol error, and a
	 *    protocol error closes the whole connection. */
	if (!w->keymap_sent)
		return -1;
	if (bit(w->keys_down, codice) == premuto)
		return 0; /* duplicate: see `wlr_input.h` */

	zwp_virtual_keyboard_v1_key(w->tastiera, now_ms(), codice,
	                            premuto ? WL_KEYBOARD_KEY_STATE_PRESSED
	                                    : WL_KEYBOARD_KEY_STATE_RELEASED);
	put_bit(w->keys_down, codice, premuto);
	/* ⚠ The evdev → XKB offset is 8 in both directions (§7.1). */
	xkb_state_update_key(w->stato, (xkb_keycode_t)codice + 8, premuto ? XKB_KEY_DOWN : XKB_KEY_UP);
	send_modifiers(w, false);
	return spedisci(w);
}

/*
 * ⛔ `frame` AFTER EVERY pointer gesture (trap 3): wlroots keeps the axes
 *    pending until it arrives, and applications gather events per
 *    frame — a click without a frame is a click the application has not yet
 *    finished receiving.
 */
static int cornice(WlrInput *w)
{
	zwlr_virtual_pointer_v1_frame(w->puntatore);
	return spedisci(w);
}

int wlr_input_absolute(WlrInput *w, uint32_t x, uint32_t y, uint32_t l, uint32_t a)
{
	if (!w || w->caduto || !w->puntatore || l == 0 || a == 0)
		return -1;
	/*
	 * ⚠ The coordinates have already been saturated by `rcp.c` on its canvas; here we saturate
	 *   again on the EXTENT, because between an `ADATTA_TELA` and the `input_recanvas`
	 *   that follows it the two may differ for one frame.  ⭐ And the
	 *   protocol is NORMALISED (wlroots divides by the extent): if the output
	 *   changes size under us, the point stays in the same proportion
	 *   instead of leaving the screen.
	 */
	if (x >= l)
		x = l - 1;
	if (y >= a)
		y = a - 1;
	zwlr_virtual_pointer_v1_motion_absolute(w->puntatore, now_ms(), x, y, l, a);
	return cornice(w);
}

int wlr_input_button(WlrInput *w, uint16_t codice, bool premuto)
{
	if (!w || w->caduto || !w->puntatore || codice >= MAX_CODE)
		return -1;
	if (bit(w->buttons_down, codice) == premuto)
		return 0; /* duplicate: the seat would count two presses */
	zwlr_virtual_pointer_v1_button(w->puntatore, now_ms(), codice,
	                               premuto ? WL_POINTER_BUTTON_STATE_PRESSED
	                                       : WL_POINTER_BUTTON_STATE_RELEASED);
	put_bit(w->buttons_down, codice, premuto);
	return cornice(w);
}

int wlr_input_force_release(WlrInput *w, uint16_t codice)
{
	if (!w || w->caduto || !w->puntatore || codice >= MAX_CODE)
		return -1;
	zwlr_virtual_pointer_v1_button(w->puntatore, now_ms(), codice,
	                               WL_POINTER_BUTTON_STATE_RELEASED);
	put_bit(w->buttons_down, codice, false);
	return cornice(w);
}

/*
 * ⛔ Units of 120 → whole notches, with the accumulator.
 *
 * The threshold is 60, that is half a notch, as on GNOME (`input.c`,
 * `UNITA_PER_DELTA`): 60 makes one notch and leaves -60 in the accumulator, and a
 * second 60 brings it back to zero without a notch.  ⇒ Two half notches make one
 * notch, a single one makes one — as the user expects from a fine wheel.
 */
static int32_t scatti(int32_t *resto, int32_t unita)
{
	int32_t n = 0;

	*resto += unita;
	while (*resto >= 60) {
		n++;
		*resto -= 120;
	}
	while (*resto <= -60) {
		n--;
		*resto += 120;
	}
	return n;
}

int wlr_input_rotella(WlrInput *w, int32_t orizzontale, int32_t verticale)
{
	int32_t sv, so;

	if (!w || w->caduto || !w->puntatore)
		return -1;
	sv = scatti(&w->vertical_remainder, verticale);
	so = scatti(&w->horizontal_remainder, orizzontale);
	if (sv == 0 && so == 0)
		return 0; /* ⛔ no `value = 0`: trap 2 */

	zwlr_virtual_pointer_v1_axis_source(w->puntatore, WL_POINTER_AXIS_SOURCE_WHEEL);
	/* ⛔ `discrete` in NOTCHES, not in 120: wlroots multiplies by 120 itself
	 *    (`wlr_virtual_pointer_v1.c:183-184`, trap 1). */
	if (sv)
		zwlr_virtual_pointer_v1_axis_discrete(w->puntatore, now_ms(),
		                                      WL_POINTER_AXIS_VERTICAL_SCROLL,
		                                      wl_fixed_from_double(sv * DETENT_VALUE), sv);
	if (so)
		zwlr_virtual_pointer_v1_axis_discrete(w->puntatore, now_ms(),
		                                      WL_POINTER_AXIS_HORIZONTAL_SCROLL,
		                                      wl_fixed_from_double(so * DETENT_VALUE), so);
	return cornice(w);
}

/* ------------------------------------------------------------------------- */

void wlr_input_close(WlrInput *w)
{
	if (!w)
		return;

	if (w->display && !w->caduto) {
		/*
		 * ⛔⛔ TRAP 5: `wlr_pointer_finish()` does NOT release the buttons
		 *     (`types/wlr_pointer.c:38-42`).  Destroying the pointer with the
		 *     left down leaves the desktop with the left down.  ⇒ They are released
		 *     here, with the frame, BEFORE destroying.
		 * ⚠ Normally there is nothing: `input_chiudi()` has already released with the
		 *   count of `RCP.md` §11.  This is the net under the net.
		 * ⭐ Not the keyboard: `wlr_keyboard_finish()` releases by itself (§7.2).
		 */
		if (w->puntatore)
			for (uint32_t c = 0; c < MAX_CODE; c++)
				if (bit(w->buttons_down, c))
					(void)wlr_input_force_release(w, (uint16_t)c);
		if (w->puntatore)
			zwlr_virtual_pointer_v1_destroy(w->puntatore);
		if (w->tastiera)
			zwp_virtual_keyboard_v1_destroy(w->tastiera);
		w->puntatore = NULL;
		w->tastiera = NULL;
		/* ⛔ `wl_display_disconnect()` does NOT send what is queued: without
		 *    this, the release above would stay in our buffer. */
		(void)wl_display_flush(w->display);
	}
	spy_away(w);
	if (w->puntatore)
		zwlr_virtual_pointer_v1_destroy(w->puntatore);
	if (w->tastiera)
		zwp_virtual_keyboard_v1_destroy(w->tastiera);
	if (w->pointer_handler)
		zwlr_virtual_pointer_manager_v1_destroy(w->pointer_handler);
	if (w->keyboard_handler)
		zwp_virtual_keyboard_manager_v1_destroy(w->keyboard_handler);
	if (w->uscita)
		wl_output_destroy(w->uscita);
	if (w->seat)
		wl_seat_destroy(w->seat);
	if (w->registry)
		wl_registry_destroy(w->registry);
	if (w->display)
		wl_display_disconnect(w->display);
	if (w->stato)
		xkb_state_unref(w->stato);
	if (w->keymap)
		xkb_keymap_unref(w->keymap);
	if (w->ctx)
		xkb_context_unref(w->ctx);
	free(w->keymap_text);
	g_free(w->keymap_origin);
	g_free(w->session_keymap);
	g_free(w);
}
