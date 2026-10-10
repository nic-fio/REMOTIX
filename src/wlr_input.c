/*
 * wlr_input.c — the virtual keyboard and pointer on wlroots.  The why and the
 * division of labour with `input.c` are in `wlr_input.h`.
 *
 * ⛔⛔ THE FIVE SILENT TRAPS of `STUDI.md` §xfce §7.2, and where they are here:
 *
 *   1. the wheel wants ±1 notches, not ±120         → `wlr_input_wheel()`
 *   2. `value` must never be 0                      → same: sent only with
 *                                                      at least one notch
 *   3. without `frame` nothing arrives              → `border()` after EVERY
 *                                                      pointer gesture
 *   4. the modifiers are sent by us, always         → `send_modifiers()`
 *   5. `wlr_pointer_finish()` does not release buttons → `wlr_input_close()`
 *
 * ⚠ All five are `[R]` in the study (wlroots 0.18.2, labwc 0.8.3, the
 *   Trixie versions).  ⭐ `[M]` 21 Sep 2026 ON THE LAPTOP — labwc 0.8.3
 *   headless in a private folder, witness `banchi/06-b33-testimone.c`,
 *   ⛔ NOT the test machine and NOT a whole XFCE session:
 *     · Shift+A: the witness sees `MODIFICATORI pressed 1` BEFORE key 30;
 *       the letter `@` (us) arrives as Shift + key 3;
 *     · CapsLock repeated three times: it locks ONCE, the second real
 *       press unlocks;
 *     · wheel +120 from the client ⇒ `v120 -120`, `value_v -15` (up); +60 +60 ⇒ one
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

/* ⛔ The ceiling of the codes, the same as `input.c` (`MAX_KEY`/`MAX_BUTTON`):
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
	struct wl_output *out_dir;
	struct zwp_virtual_keyboard_manager_v1 *keyboard_handler;
	struct zwlr_virtual_pointer_manager_v1 *pointer_handler;
	uint32_t pointer_version;

	struct zwp_virtual_keyboard_v1 *keyboard;
	struct zwlr_virtual_pointer_v1 *ptr;

	/* ⭐ The SPY: a `wl_keyboard` taken once only, to have the session's
	 *    keymap handed over (§7.4) — and then released. */
	struct wl_keyboard *spy;
	char *session_keymap;
	size_t session_keymap_len;

	/* ⛔ The keymap IN FORCE on our keyboard, and the state that follows it. */
	struct xkb_context *ctx;
	struct xkb_keymap *keymap;
	struct xkb_state *state;
	char *keymap_text; /* with the final zero; `keymap_len` without */
	size_t keymap_len;
	char *keymap_origin;
	bool keymap_sent;

	/* The last modifier state SENT — so as not to send it again unchanged. */
	uint32_t mod_down, mod_latched, mod_blocked, grp;

	/* ⛔ What THIS device has pressed: used to discard duplicates.
	 *    ⚠ It is not the count of `RCP.md` §11: that belongs to `input.c`. */
	uint8_t keys_down[MAX_CODE / 8];
	uint8_t buttons_down[MAX_CODE / 8];

	/* ⛔ The wheel accumulators, one per axis: half notches are not
	 *    lost, they add to the next one (weston does the same, §7.2). */
	int32_t vertical_remainder, horizontal_remainder;

	bool dropped;
	bool drop_logged;
};

/* ------------------------------------------------------------------------- */

static bool bit(const uint8_t *m, uint32_t n)
{
	return (m[n / 8u] & (uint8_t)(1u << (n % 8u))) != 0;
}

static void put_bit(uint8_t *m, uint32_t n, bool lit)
{
	if (lit)
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
	uint32_t code_v = 0;
	int err;

	w->dropped = true;
	if (w->drop_logged)
		return;
	w->drop_logged = true;

	err = w->display ? wl_display_get_error(w->display) : 0;
	if (err == EPROTO)
		code_v = wl_display_get_protocol_error(w->display, &interfaccia, &id);
	if (err == EPROTO)
		log_says(AREA,
		              "⛔⛔ wlroots: the compositor CLOSED the input connection "
		              "for a PROTOCOL ERROR of ours (%s, object %s@%u, code %u) — "
		              "it is a REMOTIX defect, not the desktop's.  ⚠ From now on keys "
		              "left down are released by the compositor, BUTTONS are not (§7.2 n.5)",
		              dove, interfaccia ? interfaccia->name : "?", id, code_v);
	else
		log_says(AREA,
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
static int ship(WlrInput *w)
{
	if (wl_display_flush(w->display) < 0 && errno != EAGAIN) {
		mark_drop(w, "flush");
		return -1;
	}
	return 0;
}

/*
 * One pump round with a deadline — the same form as `pump()` in
 * `wlroots.c`, and for the same reason: `wl_display_roundtrip()` waits without
 * a ceiling, and a mute compositor would stop the child forever.
 */
static bool pump(WlrInput *w, gint64 expiry)
{
	struct pollfd pfd;
	gint64 stays;
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
	stays = (expiry - g_get_monotonic_time()) / 1000;
	if (stays < 0)
		stays = 0;
	pfd.fd = wl_display_get_fd(w->display);
	pfd.events = POLLIN;
	pfd.revents = 0;
	r = poll(&pfd, 1, (int)stays);
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

static void sync_done(void *data_v, struct wl_callback *cb, uint32_t x)
{
	bool *finished = data_v;

	*finished = true;
	wl_callback_destroy(cb);
}

static const struct wl_callback_listener SYNC_LISTENER = {
	.done = sync_done,
};

/* A `roundtrip` with the ceiling.  false = dropped or expired. */
static bool synchronize(WlrInput *w, gint64 expiry)
{
	bool finished = false;
	struct wl_callback *cb = wl_display_sync(w->display);

	wl_callback_add_listener(cb, &SYNC_LISTENER, &finished);
	while (!finished) {
		if (!pump(w, expiry)) {
			wl_callback_destroy(cb);
			return false;
		}
		if (!finished && g_get_monotonic_time() >= expiry) {
			/* ⚠ The callback stays alive and will arrive at a `finished` that no longer
			 *   exists: its listener is removed by destroying it. */
			wl_callback_destroy(cb);
			return false;
		}
	}
	return true;
}

/* ------------------------------------------------------------------------- */
/* The spy: the session's keymap, copied from the wire (§7.4). */

static void spy_keymap(void *data_v, struct wl_keyboard *k, uint32_t schema, int32_t fd,
                        uint32_t gauge)
{
	WlrInput *w = data_v;
	void *map;

	/* ⛔ The descriptor is OURS as soon as it arrives, and it is closed on every path: labwc
	 *    sends the keymap again at every keyboard change, and a descriptor
	 *    lost at every key runs the child out of descriptors in an hour. */
	if (schema != WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1 || gauge == 0 || w->session_keymap) {
		close(fd);
		return;
	}
	map = mmap(NULL, gauge, PROT_READ, MAP_PRIVATE, fd, 0);
	close(fd);
	if (map == MAP_FAILED)
		return;
	/* ⚠ The text is zero-terminated INSIDE `gauge` (it is the protocol), but
	 *   we do not trust it: we copy and terminate ourselves. */
	w->session_keymap = g_malloc0(gauge + 1);
	memcpy(w->session_keymap, map, gauge);
	w->session_keymap_len = strnlen(w->session_keymap, gauge);
	munmap(map, gauge);
}

static void spy_enter(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf,
                       struct wl_array *keys) {}
static void spy_exits(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sf) {}
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
	.leave = spy_exits,
	.key = spy_key,
	.modifiers = spy_modifiers,
	.repeat_info = spy_repetition,
};

static void seat_capabilities(void *data_v, struct wl_seat *s, uint32_t capabilities)
{
	WlrInput *w = data_v;

	/* ⚠ Only once: after our virtual keyboard exists, the seat
	 *   restates its capabilities, and a second spy would read OUR keymap
	 *   believing it the session's. */
	if ((capabilities & WL_SEAT_CAPABILITY_KEYBOARD) && !w->spy && !w->session_keymap &&
	    !w->keyboard) {
		w->spy = wl_seat_get_keyboard(s);
		wl_keyboard_add_listener(w->spy, &SPY_LISTENER, w);
	}
}

static void seat_name(void *d, struct wl_seat *s, const char *label_name) {}

static const struct wl_seat_listener SEAT_LISTENER = {
	.capabilities = seat_capabilities,
	.name = seat_name,
};

static void spy_away(WlrInput *w)
{
	if (!w->spy)
		return;
	/* ⚠ `release` exists since wl_seat v3; before there is only client-side
	 *   destruction, and the compositor keeps sending events to an object that
	 *   `libwayland` discards (closing its descriptors). */
	if (wl_keyboard_get_version(w->spy) >= WL_KEYBOARD_RELEASE_SINCE_VERSION)
		wl_keyboard_release(w->spy);
	else
		wl_keyboard_destroy(w->spy);
	w->spy = NULL;
}

/* ------------------------------------------------------------------------- */
/* The globals. */

static void registry_global(void *data_v, struct wl_registry *reg, uint32_t label_name,
                            const char *interfaccia, uint32_t version_v)
{
	WlrInput *w = data_v;

	if (g_strcmp0(interfaccia, wl_seat_interface.name) == 0) {
		/* ⛔ The FIRST seat.  labwc has one (`seat0`) and does not create
		 *    `ext_transient_seat_v1` (§7.6): we inject into the
		 *    user's, and on XFCE there is no choice. */
		if (!w->seat) {
			uint32_t v = version_v < 5 ? version_v : 5;

			w->seat = wl_registry_bind(reg, label_name, &wl_seat_interface, v);
			wl_seat_add_listener(w->seat, &SEAT_LISTENER, w);
		}
	} else if (g_strcmp0(interfaccia, wl_output_interface.name) == 0) {
		/* ⚠ The FIRST output, like `wlroots.c`: it is the one captured, and it is
		 *   the one on which we ask to map the pointer. */
		if (!w->out_dir)
			w->out_dir = wl_registry_bind(reg, label_name, &wl_output_interface, 1);
	} else if (g_strcmp0(interfaccia, zwp_virtual_keyboard_manager_v1_interface.name) == 0) {
		w->keyboard_handler =
			wl_registry_bind(reg, label_name, &zwp_virtual_keyboard_manager_v1_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_virtual_pointer_manager_v1_interface.name) == 0) {
		uint32_t v = version_v < 2 ? version_v : 2;

		w->pointer_version = v;
		w->pointer_handler =
			wl_registry_bind(reg, label_name, &zwlr_virtual_pointer_manager_v1_interface, v);
	}
}

static void registry_remove(void *d, struct wl_registry *r, uint32_t label_name) {}

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
 * ⚠ `force`: after a new keymap it is sent anyway, because the compositor has
 *   just thrown away its state and our "last sent" no longer holds.
 */
static void send_modifiers(WlrInput *w, bool force)
{
	uint32_t down, latched, blocked, grp;

	if (!w->state || !w->keyboard)
		return;
	down = xkb_state_serialize_mods(w->state, XKB_STATE_MODS_DEPRESSED);
	latched = xkb_state_serialize_mods(w->state, XKB_STATE_MODS_LATCHED);
	blocked = xkb_state_serialize_mods(w->state, XKB_STATE_MODS_LOCKED);
	grp = xkb_state_serialize_layout(w->state, XKB_STATE_LAYOUT_EFFECTIVE);
	if (!force && down == w->mod_down && latched == w->mod_latched &&
	    blocked == w->mod_blocked && grp == w->grp)
		return;
	w->mod_down = down;
	w->mod_latched = latched;
	w->mod_blocked = blocked;
	w->grp = grp;
	zwp_virtual_keyboard_v1_modifiers(w->keyboard, down, latched, blocked, grp);
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
static int put_keymap(WlrInput *w, struct xkb_keymap *km, const char *origin,
                        GError **mistake)
{
	char *body_text;
	size_t len;
	int fd;
	struct xkb_state *state;

	if (w->dropped || !w->keyboard) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the input connection has dropped: the keymap has nowhere to go");
		xkb_keymap_unref(km);
		return -1;
	}
	body_text = xkb_keymap_get_as_string(km, XKB_KEYMAP_FORMAT_TEXT_V1);
	state = xkb_state_new(km);
	if (!body_text || !state) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "xkbcommon did not serialise keymap «%s»", origin);
		free(body_text);
		if (state)
			xkb_state_unref(state);
		xkb_keymap_unref(km);
		return -1;
	}
	len = strlen(body_text);

	fd = memfd_create("remotix-keymap", MFD_CLOEXEC);
	if (fd < 0 || write(fd, body_text, len + 1) != (ssize_t)(len + 1)) {
		g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno),
		            "the keymap does not write into the memfd: %s", g_strerror(errno));
		if (fd >= 0)
			close(fd);
		free(body_text);
		xkb_state_unref(state);
		xkb_keymap_unref(km);
		return -1;
	}
	/* ⚠ `libwayland` duplicates the descriptor while packing the request:
	 *   ours is closed right after, and it is not a double close. */
	zwp_virtual_keyboard_v1_keymap(w->keyboard, WL_KEYBOARD_KEYMAP_FORMAT_XKB_V1, fd,
	                               (uint32_t)(len + 1));
	close(fd);

	/* ⛔ The new state TAKES BACK the keys that are still down — as
	 *    wlroots does on its side (`wlr_keyboard_set_keymap`).  The caller has
	 *    already released them, and normally there are none; but if the release had not
	 *    left, a virgin state would say "Shift up" to a compositor
	 *    that holds it down. */
	for (uint32_t c = 0; c < MAX_CODE; c++)
		if (bit(w->keys_down, c))
			xkb_state_update_key(state, c + 8, XKB_KEY_DOWN);

	if (w->state)
		xkb_state_unref(w->state);
	if (w->keymap)
		xkb_keymap_unref(w->keymap);
	w->state = state;
	w->keymap = km;
	free(w->keymap_text);
	w->keymap_text = body_text;
	w->keymap_len = len;
	g_free(w->keymap_origin);
	w->keymap_origin = g_strdup(origin);
	w->keymap_sent = true;

	send_modifiers(w, true);
	return ship(w);
}

/*
 * `de(neo)` → layout `de`, variant `neo`.  ⛔ The same `RCP.md` §4.5 form
 * that `tastiera.c` accepts; and the characters are checked, because this string
 * comes from the wire.
 */
static bool split_name(const char *label_name, char *layout, size_t nl, char *variant, size_t nv)
{
	const char *par = strchr(label_name, '(');
	size_t ll = par ? (size_t)(par - label_name) : strlen(label_name);
	size_t lv = 0;

	for (const char *c = label_name; *c; c++)
		if (!g_ascii_isalnum(*c) && *c != '_' && *c != '-' && *c != '(' && *c != ')')
			return false;
	if (ll == 0 || ll >= nl)
		return false;
	memcpy(layout, label_name, ll);
	layout[ll] = 0;
	variant[0] = 0;
	if (par) {
		const char *is_closed = strchr(par + 1, ')');

		if (!is_closed || is_closed[1] != 0)
			return false;
		lv = (size_t)(is_closed - par - 1);
		if (lv >= nv)
			return false;
		memcpy(variant, par + 1, lv);
		variant[lv] = 0;
	}
	return true;
}

int wlr_input_keymap_from_name(WlrInput *w, const char *label_name, GError **mistake)
{
	char layout[72], variant[72];
	struct xkb_rule_names names;
	struct xkb_keymap *km;

	g_return_val_if_fail(w != NULL && label_name != NULL, -1);

	if (!split_name(label_name, layout, sizeof layout, variant, sizeof variant)) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "«%.64s» is not an XKB layout name (RCP.md §4.5)", label_name);
		return -1;
	}
	/* ⚠ All five fields, like `tastiera.c`: a NULL field is filled by
	 *   the environment (`XKB_DEFAULT_*`), and the REQUESTED layout must not
	 *   depend on whoever started the service. */
	names.rules = "evdev";
	names.model = "pc105";
	names.layout = layout;
	names.variant = variant;
	names.options = "";
	km = xkb_keymap_new_from_names(w->ctx, &names, XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!km) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "xkbcommon does not compile layout «%s»", label_name);
		return -1;
	}
	return put_keymap(w, km, label_name, mistake);
}

int wlr_input_keymap_from_text(WlrInput *w, const char *body_text, size_t length,
                              const char *origin, GError **mistake)
{
	struct xkb_keymap *km;

	g_return_val_if_fail(w != NULL && body_text != NULL, -1);
	km = xkb_keymap_new_from_buffer(w->ctx, body_text, length, XKB_KEYMAP_FORMAT_TEXT_V1,
	                                XKB_KEYMAP_COMPILE_NO_FLAGS);
	if (!km) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_DATA,
		            "keymap «%s» does not compile", origin ? origin : "?");
		return -1;
	}
	return put_keymap(w, km, origin ? origin : "?", mistake);
}

const char *wlr_input_keymap(const WlrInput *w, size_t *length)
{
	if (length)
		*length = w && w->keymap_text ? w->keymap_len : 0;
	return w ? w->keymap_text : NULL;
}

const char *wlr_input_keymap_origin(const WlrInput *w)
{
	return w && w->keymap_origin ? w->keymap_origin : "none";
}

/* ------------------------------------------------------------------------- */

WlrInput *wlr_input_open(GError **mistake)
{
	WlrInput *w = g_new0(WlrInput, 1);
	const char *label_name = g_getenv("WAYLAND_DISPLAY");
	gint64 expiry;
	g_autoptr(GError) sb_keymap = NULL;
	int outcome;

	w->display = wl_display_connect(label_name);
	if (!w->display && !label_name) {
		/* ⚠ The same search as `wlr_open()`: the child does not inherit
		 *   `WAYLAND_DISPLAY` from the compositor it has just brought to life. */
		for (int i = 0; i < 10 && !w->display; i++) {
			g_autofree char *attempt = g_strdup_printf("wayland-%d", i);

			w->display = wl_display_connect(attempt);
		}
	}
	if (!w->display) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable in XDG_RUNTIME_DIR=%s",
		            g_getenv("XDG_RUNTIME_DIR") ?: "(not set)");
		wlr_input_close(w);
		return NULL;
	}
	w->ctx = xkb_context_new(XKB_CONTEXT_NO_FLAGS);
	if (!w->ctx) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "xkbcommon context not created");
		wlr_input_close(w);
		return NULL;
	}

	w->registry = wl_display_get_registry(w->display);
	wl_registry_add_listener(w->registry, &REGISTRY_LISTENER, w);

	/* ⚠ THREE rounds: the globals; the seat capabilities (which ask for the spy); the
	 *   keymap the spy receives.  With a single ceiling for all three. */
	expiry = g_get_monotonic_time() + WAIT_US;
	if (!synchronize(w, expiry) || !synchronize(w, expiry)) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the compositor did not answer the list of globals within %d s",
		            (int)(WAIT_US / G_USEC_PER_SEC));
		wlr_input_close(w);
		return NULL;
	}
	if (w->spy)
		(void)synchronize(w, expiry); /* ⚠ without keymap we go on: below there is the fallback */
	spy_away(w);

	if (!w->seat || !w->keyboard_handler || !w->pointer_handler) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce %s%s%s: on this desktop input does not "
		            "pass through here",
		            w->seat ? "" : "wl_seat ",
		            w->keyboard_handler ? "" : "zwp_virtual_keyboard_manager_v1 ",
		            w->pointer_handler ? "" : "zwlr_virtual_pointer_manager_v1");
		wlr_input_close(w);
		return NULL;
	}

	w->keyboard = zwp_virtual_keyboard_manager_v1_create_virtual_keyboard(w->keyboard_handler,
	                                                                       w->seat);
	/*
	 * ⭐ The pointer is BOUND TO THE OUTPUT when the manager is v2: absolute
	 *    coordinates are then relative to it, and not to the space of all
	 *    outputs.  ⚠ With a single output it is the same thing; with two, without this,
	 *    the pointer would end up spread over both.  `[?]` That labwc honours
	 *    the suggested output (`wlr_cursor_map_input_to_output`) is read in the
	 *    study, not measured.
	 */
	if (w->pointer_version >= 2 && w->out_dir)
		w->ptr = zwlr_virtual_pointer_manager_v1_create_virtual_pointer_with_output(
			w->pointer_handler, w->seat, w->out_dir);
	else
		w->ptr = zwlr_virtual_pointer_manager_v1_create_virtual_pointer(
			w->pointer_handler, w->seat);

	/* ⛔ The keymap BEFORE any key — and so before returning. */
	if (w->session_keymap)
		outcome = wlr_input_keymap_from_text(w, w->session_keymap, w->session_keymap_len,
		                                  "session", &sb_keymap);
	else
		outcome = -1;
	if (outcome != 0) {
		/*
		 * ⚠ THE FALLBACK, DECLARED: the session did not give us its keymap
		 *   (`[M]` it happens on headless labwc: without a real keyboard the seat
		 *   declares capability 0 and the spy is not born — `wlr_input.h`).  Then
		 *   `xkbcommon` composes it from the child's environment (`XKB_DEFAULT_*`, or
		 *   `us`).  ⛔ It may NOT be the session's layout: the
		 *   layout negotiated with the client (`input_layout()`), which
		 *   arrives right after the opening, replaces it.
		 */
		struct xkb_rule_names empty = { 0 };
		struct xkb_keymap *km;

		if (sb_keymap)
			log_says(AREA, "⚠ wlroots: the session's keymap is not used (%s)",
			              sb_keymap->message);
		g_clear_error(&sb_keymap);
		km = xkb_keymap_new_from_names(w->ctx, &empty, XKB_KEYMAP_COMPILE_NO_FLAGS);
		if (!km || put_keymap(w, km, "environment", &sb_keymap) != 0) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
			            "no keymap to present to the virtual keyboard (%s): without one, "
			            "the first key would close the connection (no_keymap)",
			            sb_keymap ? sb_keymap->message : "xkbcommon does not compose even "
			                                             "the environment's one");
			wlr_input_close(w);
			return NULL;
		}
		log_says(AREA,
		              "⚠ DECLARED FALLBACK: the session did not hand over its keymap — "
		              "presenting the ENVIRONMENT's (layout «%s»).  ⛔ It may not be "
		              "the session's: the layout negotiated with the client corrects it",
		              xkb_keymap_layout_get_name(w->keymap, 0) ?: "unnamed");
	}

	/* ⛔ And we check that the compositor accepted everything: a protocol
	 *    error arrives AFTER the request, and without this round it would be
	 *    discovered at the user's first key. */
	if (!synchronize(w, g_get_monotonic_time() + WAIT_US) || w->dropped) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the compositor did not accept the virtual devices (the log "
		            "says why)");
		wlr_input_close(w);
		return NULL;
	}

	log_says(AREA,
	              "⭐ wlroots: virtual keyboard and pointer created (pointer v%u%s), keymap "
	              "from %s, %zu bytes",
	              w->pointer_version,
	              w->pointer_version >= 2 && w->out_dir ? ", bound to the output" : "",
	              w->keymap_origin, w->keymap_len);
	return w;
}

int wlr_input_descriptor(WlrInput *w)
{
	if (!w || w->dropped || !w->display)
		return -1;
	return wl_display_get_fd(w->display);
}

bool wlr_input_dropped(const WlrInput *w)
{
	return !w || w->dropped;
}

int wlr_input_run(WlrInput *w)
{
	struct pollfd pfd;
	int n;

	if (!w || w->dropped)
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

int wlr_input_key(WlrInput *w, uint16_t code_v, bool pressed)
{
	if (!w || w->dropped || !w->keyboard || code_v >= MAX_CODE)
		return -1;
	/* ⛔ `no_keymap`: without a keymap the key is a protocol error, and a
	 *    protocol error closes the whole connection. */
	if (!w->keymap_sent)
		return -1;
	if (bit(w->keys_down, code_v) == pressed)
		return 0; /* duplicate: see `wlr_input.h` */

	zwp_virtual_keyboard_v1_key(w->keyboard, now_ms(), code_v,
	                            pressed ? WL_KEYBOARD_KEY_STATE_PRESSED
	                                    : WL_KEYBOARD_KEY_STATE_RELEASED);
	put_bit(w->keys_down, code_v, pressed);
	/* ⚠ The evdev → XKB offset is 8 in both directions (§7.1). */
	xkb_state_update_key(w->state, (xkb_keycode_t)code_v + 8, pressed ? XKB_KEY_DOWN : XKB_KEY_UP);
	send_modifiers(w, false);
	return ship(w);
}

/*
 * ⛔ `frame` AFTER EVERY pointer gesture (trap 3): wlroots keeps the axes
 *    pending until it arrives, and applications gather events per
 *    frame — a click without a frame is a click the application has not yet
 *    finished receiving.
 */
static int border(WlrInput *w)
{
	zwlr_virtual_pointer_v1_frame(w->ptr);
	return ship(w);
}

int wlr_input_absolute(WlrInput *w, uint32_t x, uint32_t y, uint32_t l, uint32_t a)
{
	if (!w || w->dropped || !w->ptr || l == 0 || a == 0)
		return -1;
	/*
	 * ⚠ The coordinates have already been saturated by `rcp.c` on its canvas; here we saturate
	 *   again on the EXTENT, because between an `FIT_CANVAS` and the `input_recanvas`
	 *   that follows it the two may differ for one frame.  ⭐ And the
	 *   protocol is NORMALISED (wlroots divides by the extent): if the output
	 *   changes size under us, the point stays in the same proportion
	 *   instead of leaving the screen.
	 */
	if (x >= l)
		x = l - 1;
	if (y >= a)
		y = a - 1;
	zwlr_virtual_pointer_v1_motion_absolute(w->ptr, now_ms(), x, y, l, a);
	return border(w);
}

int wlr_input_button(WlrInput *w, uint16_t code_v, bool pressed)
{
	if (!w || w->dropped || !w->ptr || code_v >= MAX_CODE)
		return -1;
	if (bit(w->buttons_down, code_v) == pressed)
		return 0; /* duplicate: the seat would count two presses */
	zwlr_virtual_pointer_v1_button(w->ptr, now_ms(), code_v,
	                               pressed ? WL_POINTER_BUTTON_STATE_PRESSED
	                                       : WL_POINTER_BUTTON_STATE_RELEASED);
	put_bit(w->buttons_down, code_v, pressed);
	return border(w);
}

int wlr_input_force_release(WlrInput *w, uint16_t code_v)
{
	if (!w || w->dropped || !w->ptr || code_v >= MAX_CODE)
		return -1;
	zwlr_virtual_pointer_v1_button(w->ptr, now_ms(), code_v,
	                               WL_POINTER_BUTTON_STATE_RELEASED);
	put_bit(w->buttons_down, code_v, false);
	return border(w);
}

/*
 * ⛔ Units of 120 → whole notches, with the accumulator.
 *
 * The threshold is 60, that is half a notch, as on GNOME (`input.c`,
 * `UNIT_PER_DELTA`): 60 makes one notch and leaves -60 in the accumulator, and a
 * second 60 brings it back to zero without a notch.  ⇒ Two half notches make one
 * notch, a single one makes one — as the user expects from a fine wheel.
 */
static int32_t notches(int32_t *rest, int32_t unit)
{
	int32_t n = 0;

	*rest += unit;
	while (*rest >= 60) {
		n++;
		*rest -= 120;
	}
	while (*rest <= -60) {
		n--;
		*rest += 120;
	}
	return n;
}

int wlr_input_wheel(WlrInput *w, int32_t horizontal, int32_t vertical)
{
	int32_t sv, so;

	if (!w || w->dropped || !w->ptr)
		return -1;
	sv = notches(&w->vertical_remainder, vertical);
	so = notches(&w->horizontal_remainder, horizontal);
	if (sv == 0 && so == 0)
		return 0; /* ⛔ no `value = 0`: trap 2 */

	zwlr_virtual_pointer_v1_axis_source(w->ptr, WL_POINTER_AXIS_SOURCE_WHEEL);
	/* ⛔ `discrete` in NOTCHES, not in 120: wlroots multiplies by 120 itself
	 *    (`wlr_virtual_pointer_v1.c:183-184`, trap 1). */
	if (sv)
		zwlr_virtual_pointer_v1_axis_discrete(w->ptr, now_ms(),
		                                      WL_POINTER_AXIS_VERTICAL_SCROLL,
		                                      wl_fixed_from_double(sv * DETENT_VALUE), sv);
	if (so)
		zwlr_virtual_pointer_v1_axis_discrete(w->ptr, now_ms(),
		                                      WL_POINTER_AXIS_HORIZONTAL_SCROLL,
		                                      wl_fixed_from_double(so * DETENT_VALUE), so);
	return border(w);
}

/* ------------------------------------------------------------------------- */

void wlr_input_close(WlrInput *w)
{
	if (!w)
		return;

	if (w->display && !w->dropped) {
		/*
		 * ⛔⛔ TRAP 5: `wlr_pointer_finish()` does NOT release the buttons
		 *     (`types/wlr_pointer.c:38-42`).  Destroying the pointer with the
		 *     left down leaves the desktop with the left down.  ⇒ They are released
		 *     here, with the frame, BEFORE destroying.
		 * ⚠ Normally there is nothing: `input_close()` has already released with the
		 *   count of `RCP.md` §11.  This is the net under the net.
		 * ⭐ Not the keyboard: `wlr_keyboard_finish()` releases by itself (§7.2).
		 */
		if (w->ptr)
			for (uint32_t c = 0; c < MAX_CODE; c++)
				if (bit(w->buttons_down, c))
					(void)wlr_input_force_release(w, (uint16_t)c);
		if (w->ptr)
			zwlr_virtual_pointer_v1_destroy(w->ptr);
		if (w->keyboard)
			zwp_virtual_keyboard_v1_destroy(w->keyboard);
		w->ptr = NULL;
		w->keyboard = NULL;
		/* ⛔ `wl_display_disconnect()` does NOT send what is queued: without
		 *    this, the release above would stay in our buffer. */
		(void)wl_display_flush(w->display);
	}
	spy_away(w);
	if (w->ptr)
		zwlr_virtual_pointer_v1_destroy(w->ptr);
	if (w->keyboard)
		zwp_virtual_keyboard_v1_destroy(w->keyboard);
	if (w->pointer_handler)
		zwlr_virtual_pointer_manager_v1_destroy(w->pointer_handler);
	if (w->keyboard_handler)
		zwp_virtual_keyboard_manager_v1_destroy(w->keyboard_handler);
	if (w->out_dir)
		wl_output_destroy(w->out_dir);
	if (w->seat)
		wl_seat_destroy(w->seat);
	if (w->registry)
		wl_registry_destroy(w->registry);
	if (w->display)
		wl_display_disconnect(w->display);
	if (w->state)
		xkb_state_unref(w->state);
	if (w->keymap)
		xkb_keymap_unref(w->keymap);
	if (w->ctx)
		xkb_context_unref(w->ctx);
	free(w->keymap_text);
	g_free(w->keymap_origin);
	g_free(w->session_keymap);
	g_free(w);
}
