/*
 * input.c — input REALLY reaches the desktop: `input.h` implemented on `libei`.
 *
 * ⛔ The contract is in `input.h`, which belongs to the coordinator: here it is IMPLEMENTED, the
 *    seam is not changed.  Whoever finds the contract wrong SAYS so and
 *    stops — does not work around it.  *(The two points where it was said are in
 *    `fasi/rapporti/F4-A4-iniezione.md` §5.)*
 *
 * ⛔ CARRIED OVER from `fondamenta/remotix-c/src/input.c` (906 lines), and not copied.  Of
 *    v1 there remains ⭐ **the mechanics of libei** — the `poll`/`ei_dispatch` loop, the
 *    taking of the devices, `start_emulating`, `ei_device_frame` after every
 *    event — which is the real heritage.  ⛔ All the RDP surroundings go
 *    (`freerdp/input.h`, the `PTR_FLAGS_*`, the `KBD_FLAGS_*`), which here do not
 *    exist: on the wire there is `RCP.md` §7.3, and the codes are already evdev.
 *
 * ⛔⛔ AND TWO THINGS OF v1 THAT WERE **WRONG**, not just useless, go — and
 *      they are half of this file's work:
 *
 *   1. `compositore_mapping_id`: v1 looked for the region with the UUID **declared
 *      by us** to `RecordVirtual`.  Mutter ignores that property, and
 *      generates the real UUID itself: v1 **never** found the region by key
 *      and fell every time on the fallback "I take the first" — green with one
 *      screen, crooked with two (`mutter.h`, `STUDI.md` §gnome §9);
 *   2. `ei_device_scroll_discrete`: Mutter does an **integer division by
 *      120** on it (`meta-eis-client.c:554`), and the half notches vanish.  Here we
 *      go with `scroll_delta`, where Mutter forces `SOURCE_WHEEL`, skips
 *      the accumulator, and the real threshold of a notch is **60**.
 *
 * ---------------------------------------------------------------------------
 * ⛔ A SINGLE THREAD, AND IT IS THE CALLER'S
 *
 * v1 had a thread of its own and a queue, because FreeRDP's loop was not its own.
 * Not here: `input_run()` exists in the contract precisely so that the child's
 * loop calls this module at every round.  ⇒ **No lock, no
 * queue, no thread** — and no waiting inside the asynchronous loop
 * (`CODER.md` §4.4).
 *
 * ⛔ The price, and it must be told to the coordinator instead of discovered: **all** the
 *    functions of `input.h` must be called from the SAME thread that calls
 *    `input_run()`.  `libei` is not reentrant, and two threads on a `struct ei`
 *    are a defect that gives no error.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ THE COUNT OF WHAT IS PRESSED — `RCP.md` §11
 *
 * *"the rule with the highest damage/cost ratio in the document"*: a Ctrl
 * left down in a session that survives the client makes the desktop
 * unusable at reattach, and nobody connects the two things.
 *
 * ⇒ Every key and every button pressed is MARKED, and every release
 *   clears it.  Two bitmaps, and `input_release_all()` empties them
 *   returning how many it released — so that the bench can count them.
 *
 * ⚠ And Mutter acts as a safety net **only on libei**: `drop_device`
 *   (`meta-eis-client.c:144-168`) releases everything when the EIS client drops.
 *   ⛔ It is not a reason not to count: the net triggers when the channel
 *   closes, and the detach of a client does **not** close the session (invariant
 *   I4 — the stage survives the detach).
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔⛔ THE RELEASE THAT REACHES NOBODY — `[M]` 16 August 2026, bench
 *       `06-b33`, and this file CANNOT cure it
 *
 * ⚠ *This box is the most important thing in the file, and must be read before
 *   touching `device_removed()`: the comment in there said* "at the replacement
 *   we release on the new device, which is the only place where the release
 *   arrives" *— and it was **false**.  The release on the new device arrives
 *   nowhere.*
 *
 * THE SCENE, measured: `BTN_LEFT` is held down, the client asks for an
 * `FIT_CANVAS`, Mutter recreates the absolute devices, and **then** it is released.
 * ⇒ `[M]` the witness inside the session (a real Wayland window) sees the
 *   `pressed:1` and **never sees** the `pressed:0`.  ⛔ And from that moment on
 *   **no click works any more**, forever: the next round, identical to
 *   one that had been green on everything, delivers pointer and keys and **zero**
 *   buttons.  It is *"on Android the mouse gives trouble: it no longer takes clicks"*
 *   (the user, 15 August 2026), in a form no log declared.
 *
 * THE CHAIN, all `[R]` in Mutter's source, and no link is ours:
 *
 *   1. `remove_viewport_devices` (`meta-eis-client.c:197-206`) calls
 *      `eis_device_remove()` and ⛔ **does NOT go through `drop_device()`** — which is
 *      the only place where Mutter releases what was pressed.  The old device
 *      goes away **with the button still down**;
 *   2. `handle_button` (`:612-621`) **silently** swallows a release for a
 *      button that is not pressed on the device receiving it
 *      (*"Duplicate press/release, should've been filtered by libeis"*) — and
 *      after the replacement the device is ANOTHER one, with clean maps;
 *   3. `meta_seat_impl_notify_button_in_impl` (`meta-seat-impl.c:899-908`) keeps
 *      a count **OF THE SEAT**, shared among all devices, and discards
 *      *"any repeated button press (for example from virtual devices)"*.  The
 *      press of the dead device keeps it at **1** forever ⇒ every following press
 *      brings it to 2 and is discarded, every release brings it back to 1 and
 *      is discarded.  ⛔ **It never goes down to zero.**
 *
 * ⇒ ⛔ **From here it cannot be recovered, and it is not giving up**: it is measured.  A
 *   `press`+`release` on the new device goes 1→2→1 and delivers nothing
 *   (`[M]`); a `release` alone is swallowed by step 2.  The only code that
 *   brings the count back to zero is `drop_device()`, that is **the drop of the EIS
 *   channel** — and indeed `[M]` restarting the server unblocks the desktop.
 *
 * ⭐⭐ AND THE CURE EXISTS, IT IS ONE LINE, AND IT IS NOT IN THIS FILE: release
 *     **BEFORE** asking for the resize, while the devices are
 *     still those that received the press.  The function already exists and is
 *     `input_release_all()`; the place to call it is `figlio.c:3964`,
 *     right **before** `capture_resize(cat, canvas_intended_w,
 *     canvas_intended_h)`.  `[M]` Simulated from the wire — releasing before the
 *     replacement — the witness sees the release and the clicks after the replacement
 *     work again, all of them.
 *
 * ⚠ `figlio.c` does not belong to this link (sub-phase 6.3), so here the cure is
 *   MEASURED and WRITTEN, not applied.  ⛔ What falls to this file is
 *   the other half, and it is the one that was missing: **stop saying the release
 *   has left**.  Before, `send_button()` returned 0 and
 *   `input_release_all()` counted a release that happened, that is the log
 *   said "done" while the desktop stayed blocked — the worst form of
 *   `CODER.md` §4.6, *the green is not true*.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔⛔ AND THERE IS A SECOND DOOR — `[M]` 21 August 2026, bench
 *       `banchi/06-b33-risveglio.*`.  ⚠ THE CURE ABOVE **DOES NOT COVER IT**.
 *
 * ⛔ **The replacement does NOT depend on the canvas.**  `[M]` with `banchi/06-b33-risveglio`,
 *    still session and no `FIT_CANVAS`: **three `capture_wake()`, three
 *    pointer replacements** (delta of `pointer_replacements` = 1, 1, 1) and **zero**
 *    calls to `capture_resize()`.
 *
 * `[R]` And Mutter's line that explains it:
 *   `capture_wake()` calls `pw_stream_update_params()` → the producer
 *   renegotiates → `meta_screen_cast_virtual_stream_src_enable()`
 *   (`meta-screen-cast-virtual-stream-src.c:283`) calls
 *   `meta_eis_viewport_notify_changed()` → `viewports-changed`
 *   (`meta-eis.c:319-323`) → `update_viewports()` (`meta-eis-client.c:1049-1062`)
 *   → `remove_viewport_devices()`.  ⇒ **The same chain as the resize,
 *   but without anyone having changed size.**
 *
 * ⛔ And `figlio.c:6365` calls `capture_wake()` **precisely on a still
 *    desktop**, when the take is ZERO and a keyframe is owed — that is at the
 *    exact moment the user may be holding the mouse down on a
 *    scene that does not move.
 *
 * `[M]` The measurement, scene `06-b33-risveglio.sh held` (21 Aug 2026, load
 * 1.58-10.7, Wayland witness inside the session):
 *   · `BTN_LEFT` down → **1** wake-up → the release **NEVER arrives** at the
 *     witness, and **neither does the next fresh click** ⇒ from there the desktop
 *     no longer takes a click;
 *   · ⭐ and the **keyboard keeps working** (Ctrl down+up and a fresh Enter
 *     all arrive): the keyboard is not a viewport device;
 *   · ⭐ the scene with `capture_resize()` in place of the wake-up gives
 *     **exactly the same outcome**: they are two doors to the same room.
 *
 * `[M]` And Mutter's voice, with `MUTTER_DEBUG=eis,input`, aligned to the
 * millisecond (18:41:16-30 of 21 Aug 2026):
 *   `EIS: Updating viewports` — and ⛔ **NO** *"Releasing pressed buttons"*
 *   next to it ⇒ the old device dies with the button down;
 *   then `INPUT: Dropping repeated press of button 0x110, count 2` and
 *   `INPUT: Dropping repeated release of button 0x110, count 1` ⇒ the SEAT's
 *   count never goes back to zero.
 *
 * ⭐⭐ AND WHAT DOES HEAL, `[M]` the same day: **the drop of the
 *     EIS channel**, and that alone.  Detaching and reattaching the EIS client —
 *     ⛔ **with the same `gnome-shell`, verified by pid** — the clicks start
 *     arriving again.  `[R]` The why: `meta_eis_client_disconnect()`
 *     (`:1075`) is the only caller of `drop_device()`, which releases what
 *     was pressed; and in the journal the six lines *"Releasing pressed
 *     buttons while destroying virtual input device"* show right there.
 *
 * ⚠ And to implement that healing **this file is not enough**: after the detach
 *   the descriptor `mutter.c` keeps aside is dead, and a NEW one can only be
 *   asked for by whoever has the bus and the session path.  ⇒ A new
 *   `ConnectToEIS` is needed, that is `mutter_eis_reattach()`.  `[R]`
 *   `meta-remote-desktop-session.c:1943-1969`: `session->eis` is reused, and every
 *   call adds a client ⇒ the session and the stage are NOT touched.
 *
 * ⛔⛔ AND HERE I HAD WRITTEN A WRONG REASON, refuted by a fault
 *      grafted on 21 August 2026 (`06-b33-risveglio-guasti.py`, `RG3`).
 *      It said: *"as long as `mutter.c`'s descriptor stays open the socket is
 *      still connected and Mutter sees no detach"*.  ⛔ `[M]` Removing
 *      that `close()` the healing works **identically**.
 *      ⭐ The detach is sent by **`ei_disconnect()`**, as a protocol
 *        message: `[M]` removing THAT line (`RG4`) the healing stops.
 *      ⚠ The `close()` stays so as not to lose a descriptor at every healing.
 */
#include "input.h"

#include <errno.h>
#include <gio/gio.h>
#include <libei.h>
/* ⛔ Cure D4: needed for ONE question only — "is the compositor still there?" — to be
 *    asked **before** `ei_dispatch()` on a channel not yet mature.  See the
 *    box above `detach_context()`. */
#include <poll.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "kwin.h"
#include "mutter.h"
#include "registro.h"
#include "sessione.h"
#include "tastiera.h"
#include "wlr_input.h"

#define AREA "input"

/*
 * ⛔ Mutter's two ceilings, read in the code (`meta-eis-client.c:30-31` `[R]`):
 *    beyond them, the event is discarded **silently**.  The bitmaps cover them
 *    entirely: so "I marked it" and "I sent it" cannot diverge.
 */
#define MAX_KEY 0x300u
#define MAX_BUTTON 0x300u
#define BIT_BYTE(n) (((n) + 7u) / 8u)

/*
 * ⛔ 120 units of `RCP.md` §7.3 = one notch = **10.0** of `ei_device_scroll_delta`
 *    on Mutter, that is a factor of 12.
 *
 * `[R]` `meta-virtual-input-device-native.c:752-756`: with `SOURCE_WHEEL` Mutter
 * does `dy * (120.0 / 10.0)` and gets the `v120`; `meta-seat-impl.c:1239` emits
 * a discrete notch when the accumulator exceeds **60**, that is half a notch.
 *
 * ⇒ 60 units (half a notch) become `5.0`, which become `v120 = 60`, which
 *   **produce a notch**.  With `ei_device_scroll_discrete` they would have
 *   become `60 / 120 = 0` and would have produced nothing.
 *
 * ⚠ And the 12 is MUTTER's, not the protocol's: on KWin `scroll_delta` does not
 *   produce any notch (`STUDI.md` §kde §7.2) and the way is `scroll_discrete`.
 *   The day `kwin.c` is written this constant is NOT carried over.
 */
#define UNIT_PER_DELTA 12.0

struct input
{
	MutterSession *session;
	/* ⭐ PHASE 12, INCREMENT 3 — on KDE the channel is given by KWin, and `session` is
	 *    NULL.  Only three things change: where the descriptor comes from (and the
	 *    healing), the region (KWin does not set the mapping-id: it is chosen by
	 *    geometry) and the wheel (`scroll_discrete`, see `UNIT_PER_DELTA`). */
	KwinSession *kwin;
	struct ei *ei;

	/* The CANVAS of `RCP.md` §4.5, that is the range in which `rcp.c` has already
	 * verified that the incoming coordinates lie. */
	uint32_t canvas_w, canvas_h;

	/* ⛔ The ABSOLUTE device, and not "the first that can scroll": Mutter
	 *    offers two, and the relative one has NO regions — with the relative one the pointer
	 *    ends up wherever (`banchi/01-s7-rotella.c`, `[M]` 10 August 2026). */
	struct ei_device *pointer;
	struct ei_device *keyboard_dev;
	gboolean pointer_active;
	gboolean keyboard_active;
	uint32_t sequence;

	/* The region the pointer moves on, in global logical coordinates. */
	gboolean region_known;
	gboolean scaled_region_warned;
	double reg_x, reg_y, reg_l, reg_a;
	char *reg_per; /* «key», «geometry», «only»: how we chose it */

	Keyboard *kb_layout;
	char *keymap_name; /* the name libei publishes, to SEE a replacement */
	/* ⭐ What the CLIENT declared in `ATTACH` (`RCP.md` §4.5), that is
	 *    the layout §5-bis.7 says to put into the session.  NULL
	 *    until someone has asked for it. */
	char *negotiated;
	/* ⭐ How many times the negotiated layout was REQUESTED from KWin on seeing
	 *    another keymap arrive (see "KWIN DID NOT HEAR" below). */
	int kwin_requests;

	/* ⛔⛔ THE COUNT.  See the box at the top of the file. */
	uint8_t keys[BIT_BYTE(MAX_KEY)];
	uint8_t buttons[BIT_BYTE(MAX_BUTTON)];
	unsigned how_many_keys;
	unsigned how_many_buttons;

	/* ⛔⛔ THE ORPHANS — what was pressed on a device THAT IS NO LONGER
	 *     THERE.  See the box "THE RELEASE THAT REACHES NOBODY". */
	uint8_t orphan_keys[BIT_BYTE(MAX_KEY)];
	uint8_t orphan_buttons[BIT_BYTE(MAX_BUTTON)];
	unsigned how_many_orphans;

	/* The silent replacements, counted: the bench reads them instead of deducing them. */
	unsigned pointer_replacements;
	unsigned keyboard_replacements;

	gboolean dropped; /* the compositor has closed the channel */

	/* ⛔⛔ CURE "C" — the reattach that heals the seat.  🔸 Derived, 21
	 *     August 2026, and the box at the top of the file says why there is no
	 *     other: from the client side the seat's count is unrecoverable,
	 *     and the only code that resets it is Mutter's `drop_device()`, which runs
	 *     only at the drop of the EIS channel. */
	gboolean healing_due;
	unsigned recoveries;
	gint64 last_heal_us;

	/* ⛔⛔ `libei`'s HANDSHAKE — cure D4, 25 August 2026.  The
	 *     box above `detach_context()` names the instruction that crashed and
	 *     why these four fields are what is needed not to pass through it.
	 *
	 * ⭐ `handshake_done` is NOT a heuristic on the pointers: it is `EI_EVENT_CONNECT`,
	 *    that is the way `libei` has of saying "the server has approved".  The
	 *    devices arrive LATER, and looking at them would say "not yet" even
	 *    on a context that is by now mature. */
	gboolean handshake_done;
	gint64 open_us;  /* when the channel was opened (monotonic) */
	gint64 handshake_us; /* when the handshake arrived; 0 = never */
	/* ⛔ The descriptor we gave `libei`, kept aside for ONE case only:
	 *    the one in which the context must be **abandoned** instead of freed,
	 *    and then we must close the socket ourselves.  ⚠ In the normal case it is not
	 *    touched: it belongs to `libei`, and closing it in two places is a defect that
	 *    shows at a distance. */
	int fd_socket;

	/* ⭐ PHASE 13, INCREMENT 3 — on wlroots the transport is `wlr_input.c`, and
	 *    `ei`, `session`, `kwin`, `pointer` and `keyboard_dev` stay NULL.
	 *    ⛔ Non-NULL means "this Input is wlroots's" for its WHOLE
	 *    life: after a drop the dead one is kept until the reattach
	 *    replaces it, so no function falls by mistake into the libei branches.
	 *    The "WLROOTS" box at the bottom of the file says the rest. */
	WlrInput *wlr;
	gint64 wlr_last_reattach_us;
	unsigned wlr_reattaches;
	gboolean wlr_reattach_failed_logged;
	/* ⭐ PHASE 15, D-007 — the last absolute position sent (on the canvas of
	 *    then): `input_bring_back_inside()` puts it back after the shortcut, which
	 *    moves labwc's pointer onto the windows. */
	gboolean wlr_pointer_known;
	uint32_t wlr_px, wlr_py, wlr_pl, wlr_pa;
};

/* ⭐ PHASE 13 — the wlroots branches, written at the bottom of the file (box
 *    "WLROOTS").  ⛔ Each one sits at the TOP of the public function and returns: the
 *    GNOME and KDE path below it does not change by one line. */
static int send_key_wlr(Input *in, uint16_t code, int pressed);
static int send_button_wlr(Input *in, uint16_t code, int pressed);
static int run_wlr(Input *in);
static int layout_wlr(Input *in, const char *name);
static int letter_wlr(Input *in, uint32_t character);
static void close_wlr(Input *in);
static void reattach_wlr(Input *in);

/* ⛔ The count of ABANDONED contexts — the PRICE of cure D4, and a price
 *    that is not counted is a price nobody discovers.  ⚠ It belongs to the process, not
 *    to the channel: the `Input` that paid it is already freed when the bench
 *    reads the number. */
static unsigned abandoned_contexts;

/* ⭐ The window of bench `10-d4`.  ⛔ It is NOT in `input.h` on purpose, like
 *    `input_count()` below: `input.h` is the PRODUCT's contract, and this
 *    is a witness.  The bench declares it `extern` by itself. */
unsigned input_abandons(void);

unsigned input_abandons(void)
{
	return abandoned_contexts;
}

/* ⛔ The floor between two healings.  It is not prudence: a healing that
 *    failed in a repeatable way would run at every round of the child's loop,
 *    that is sixty D-Bus calls a second on an already broken channel.  ⚠ The
 *    flag is NOT switched off: it is retried at the round after the floor. */
#define HEALING_BACKSTOP_US (1000 * 1000)

/* ------------------------------------------------------------------ *
 *  The bitmaps — "marked" and "sent" must not be able to diverge
 * ------------------------------------------------------------------ */
static gboolean bit_read(const uint8_t *map, uint32_t n)
{
	return (map[n / 8u] & (uint8_t) (1u << (n % 8u))) != 0;
}

static void bit_write(uint8_t *map, uint32_t n, gboolean is_on)
{
	if (is_on)
		map[n / 8u] |= (uint8_t) (1u << (n % 8u));
	else
		map[n / 8u] &= (uint8_t) ~(1u << (n % 8u));
}

/* ------------------------------------------------------------------ *
 *  Sending
 * ------------------------------------------------------------------ */

/*
 * ⛔ `ei_device_frame` AFTER EVERY event, and not in groups.
 *
 * On Mutter it is useless — the `FRAME` is ignored, with a FIXME next to it
 * saying "we should be accumulating the above events" (`meta-eis-client.c:1033`
 * `[R]`).  ⛔ On KWin and on wlroots it is **mandatory**: without it, the event does not
 * come out at all.  Sending it here is free, and it is the only portable form.
 */
static void beat_border(Input *in, struct ei_device *device)
{
	ei_device_frame(device, ei_now(in->ei));
}

static int send_key(Input *in, uint16_t code, int pressed)
{
	if (code >= MAX_KEY)
	{
		registro_dice(AREA, "⚠ key code 0x%X beyond Mutter's maximum (0x%X): Mutter would "
		                    "discard it SILENTLY, so I refuse it myself and say so",
		              code, MAX_KEY - 1);
		return -1;
	}
	if (in->wlr)
		return send_key_wlr(in, code, pressed);
	if (!in->keyboard_dev || !in->keyboard_active)
		return -1;

	/* ⛔ As for buttons: a key pressed on a keyboard the
	 *    compositor destroyed (keymap change, `:762-781`) can no longer be
	 *    released — `handle_key` (`:638-645`) has the same guard as
	 *    `handle_button`.  It is said and -1 is returned, instead of writing "done". */
	if (!pressed && bit_read(in->orphan_keys, code))
	{
		bit_write(in->orphan_keys, code, FALSE);
		if (in->how_many_orphans)
			in->how_many_orphans--;
		if (bit_read(in->keys, code))
		{
			bit_write(in->keys, code, FALSE);
			if (in->how_many_keys)
				in->how_many_keys--;
		}
		/* ⛔ Phase 16 §12: the code only if it is a modifier — the other
		 *    keys are typed characters, and in the log they are called «key». */
		char which[24] = "";
		if (log_speakable_key(code))
			g_snprintf(which, sizeof which, " 0x%X", code);
		registro_dice(AREA,
		              "⛔⛔ the release of key%s DOES NOT LEAVE: it was pressed on a keyboard that "
		              "the compositor has already removed (replacement n. %u), and `handle_key` silently "
		              "discards a release on the new device (`meta-eis-client.c:638-645`).  "
		              "⛔ A modifier that stays down makes the desktop unusable (`RCP.md` "
		              "§11): the cure is to release BEFORE the replacement",
		              which, in->keyboard_replacements);
		return -1;
	}

	ei_device_keyboard_key(in->keyboard_dev, code, pressed != 0);
	beat_border(in, in->keyboard_dev);

	/* ⛔ The count is kept AFTER sending: marking a key that did not leave
	 *    would make the detach release something nobody pressed. */
	if ((pressed != 0) != bit_read(in->keys, code))
	{
		bit_write(in->keys, code, pressed != 0);
		if (pressed)
			in->how_many_keys++;
		else if (in->how_many_keys)
			in->how_many_keys--;
	}
	return 0;
}

static int send_button(Input *in, uint16_t code, int pressed)
{
	if (code >= MAX_BUTTON)
	{
		registro_dice(AREA, "⚠ button code 0x%X beyond the maximum: refused", code);
		return -1;
	}
	if (in->wlr)
		return send_button_wlr(in, code, pressed);
	if (!in->pointer || !in->pointer_active)
		return -1;

	/*
	 * ⛔⛔ THE RELEASE OF AN ORPHAN DOES NOT LEAVE, AND IT IS SAID — see the box at
	 *     the top of the file.  ⚠ The count is CLEARED anyway: that button is no
	 *     longer ours to release, and keeping it marked would retry forever
	 *     something that cannot succeed.
	 *
	 * ⭐ And **-1** is returned, not 0: `rcp.c` counts it among the `input_refused`,
	 *   which is the truth.  Returning 0 would mean writing "done" next to
	 *   a desktop left with the button down — and that is six hours of
	 *   diagnosis for whoever reads the log.
	 */
	if (!pressed && bit_read(in->orphan_buttons, code))
	{
		bit_write(in->orphan_buttons, code, FALSE);
		if (in->how_many_orphans)
			in->how_many_orphans--;
		if (bit_read(in->buttons, code))
		{
			bit_write(in->buttons, code, FALSE);
			if (in->how_many_buttons)
				in->how_many_buttons--;
		}
		registro_dice(AREA,
		              "⛔⛔ the release of button 0x%X DOES NOT LEAVE: it was pressed on a "
		              "device the compositor has already removed (replacement n. %u), and Mutter "
		              "silently discards a release on the new device "
		              "(`meta-eis-client.c:612-621`).  ⛔ The SEAT still counts it down "
		              "(`meta-seat-impl.c:899-908`) and from now on NO click arrives any more: the cure "
		              "is to release BEFORE asking for the resize — `figlio.c:3964`, "
		              "before `capture_resize()`",
		              code, in->pointer_replacements);
		return -1;
	}

	ei_device_button_button(in->pointer, code, pressed != 0);
	beat_border(in, in->pointer);

	if ((pressed != 0) != bit_read(in->buttons, code))
	{
		bit_write(in->buttons, code, pressed != 0);
		if (pressed)
			in->how_many_buttons++;
		else if (in->how_many_buttons)
			in->how_many_buttons--;
	}
	return 0;
}

/* ------------------------------------------------------------------ *
 *  The region: which screen is ours
 * ------------------------------------------------------------------ */

/*
 * ⛔ IT IS REREAD AT EVERY `DEVICE_ADDED`, not once at startup.
 *
 * `[R]` `meta-eis-client.c:1048-1062`: any geometry change does
 * `remove_viewport_devices` + recreate.  On our side: `DEVICE_REMOVED` →
 * `DEVICE_ADDED` → `DEVICE_RESUMED`, and ⛔ **the pointer to the old device
 * stops working WITHOUT AN ERROR**.  A bench that reads the region once
 * only stays GREEN while the defect is alive (`CODER.md` §3.4).
 *
 * Three criteria in order, and each one is DECLARED:
 *
 *   by KEY         the `mapping-id` that **Mutter** publishes in the stream's
 *                  `Parameters`.  It is an identity, and it does not go wrong.
 *   by GEOMETRY    the region as large as the canvas.  It is the only criterion that
 *                  exists when the regions are anonymous — the "logical monitor"
 *                  viewports have `mapping_id == NULL` (`[R]` §7.1), and on KWin
 *                  `eis_region_set_mapping_id` is never called.
 *   ONLY           if there is a single region, it is that one.  ⛔ "The first" when
 *                  there are two is not chosen: we declare we do not know, because
 *                  the wrong region sends the pointer to another screen
 *                  **without an error** (`meta-eis-client.c:470-472`).
 */
static void read_region(Input *in, struct ei_device *device)
{
	/* On KWin there is no key (`eis_region_set_mapping_id` is never
	 * called): geometry and "only" remain. */
	const char *key = in->kwin ? NULL : mutter_published_mapping_id(in->session);
	struct ei_region *per_key = NULL, *per_geometry = NULL, *single = NULL;
	size_t how_many = 0;
	struct ei_region *choice = NULL;
	const char *per = NULL;

	in->region_known = FALSE;
	g_clear_pointer(&in->reg_per, g_free);

	for (size_t i = 0;; i++)
	{
		struct ei_region *region = ei_device_get_region(device, i);
		const char *id;

		if (!region)
			break;
		how_many++;
		single = region;
		id = ei_region_get_mapping_id(region);

		/* ⛔ The getters return `uint32_t`, not `double`: passing them to a `%.0f`
		 *    prints garbage that reads like a real diagnosis ("the region
		 *    is 0x0") while the region is 1920x1080.  `[M]` 10 August 2026. */
		log_detail(AREA, "region %zu: %u,%u %ux%u (mapping-id «%s»)", i,
		                   ei_region_get_x(region), ei_region_get_y(region),
		                   ei_region_get_width(region), ei_region_get_height(region),
		                   id ?: "absent");

		if (!per_key && key && id && g_strcmp0(id, key) == 0)
			per_key = region;
		if (!per_geometry && in->canvas_w && in->canvas_h &&
		    ei_region_get_width(region) == in->canvas_w &&
		    ei_region_get_height(region) == in->canvas_h)
			per_geometry = region;
	}

	if (per_key)
	{
		choice = per_key;
		per = "key";
	}
	else if (per_geometry)
	{
		choice = per_geometry;
		per = "geometry";
	}
	else if (how_many == 1)
	{
		choice = single;
		per = "only";
	}

	if (!choice)
	{
		registro_dice(AREA,
		              "⛔ NO region recognised among the %zu announced (key «%s», canvas "
		              "%ux%u): the pointer does NOT move, and I do not guess which one it is",
		              how_many, key ?: "unknown", in->canvas_w, in->canvas_h);
		return;
	}

	in->reg_x = ei_region_get_x(choice);
	in->reg_y = ei_region_get_y(choice);
	in->reg_l = ei_region_get_width(choice);
	in->reg_a = ei_region_get_height(choice);
	in->region_known = in->reg_l > 0 && in->reg_a > 0;
	in->reg_per = g_strdup(per);

	registro_dice(AREA, "pointer region by %s: %.0f,%.0f %.0fx%.0f (of %zu, mapping-id «%s»)",
	              per, in->reg_x, in->reg_y, in->reg_l, in->reg_a, how_many,
	              ei_region_get_mapping_id(choice) ?: "absent");
}

/* ------------------------------------------------------------------ *
 *  The keyboard layout
 * ------------------------------------------------------------------ */

/*
 * ⛔⛔ THE LAYOUT ARRIVES FROM `libei`, AND IT IS REOPENED AT EVERY `DEVICE_ADDED`.
 *
 * ⭐ The direction is this one, and not the other: **we do not choose** the session's
 *    layout — GNOME chooses it, and `libei` hands it to us with the
 *    keyboard device, as XKB text on a descriptor.  *(The contract
 *    said "`keyboard_open("it")`"; link A5 refused that piece and
 *    was right — `input.h`/`tastiera.h`, 14 August 2026.)*
 *
 * ⛔ And AT EVERY `DEVICE_ADDED`, not once at startup: `on_keymap_changed`
 *    (`meta-eis-client.c:761-781` `[R]`) does `eis_device_remove` +
 *    `add_device` with the new keymap, with the comment *"Changing the keymap
 *    means we have to remove our device and recreate it"*.  Whoever opens the
 *    layout once only stays with the old one after a change, and
 *    ⛔ **the letters come out different without anything giving an error**.
 */
static void read_keymap(Input *in, struct ei_device *device)
{
	struct ei_keymap *keymap = ei_device_keyboard_get_keymap(device);
	g_autofree char *text = NULL;
	g_autofree char *fingerprint = NULL;
	g_autofree char *mistake = NULL;
	Keyboard *new_one;
	int fd;
	size_t measure;

	if (!keymap)
	{
		/* ⛔ The device exists, the keymap does not: `configure_keyboard` exits
		 *    AFTER having declared the keyboard capability if
		 *    `meta_backend_get_keymap` gives NULL (`:242-246` `[R]`).  It must be borne,
		 *    and it is declared instead of falling back silently. */
		registro_dice(AREA, "⚠ the keyboard device carries no keymap: LETTERS "
		                    "stay off (KEY POSITIONS do not)");
		g_clear_pointer(&in->kb_layout, keyboard_close);
		g_clear_pointer(&in->keymap_name, g_free);
		return;
	}
	if (ei_keymap_get_type(keymap) != EI_KEYMAP_TYPE_XKB)
	{
		registro_dice(AREA, "⚠ keymap of unknown type (%d): ignored",
		              (int) ei_keymap_get_type(keymap));
		return;
	}

	fd = ei_keymap_get_fd(keymap);
	measure = ei_keymap_get_size(keymap);
	if (fd < 0 || measure == 0)
		return;

	/* ⛔ `pread` and not `read`: the keymap descriptor is shared, and
	 *    consuming its position would break it for whoever rereads it later. */
	text = g_malloc0(measure + 1);
	if (pread(fd, text, measure, 0) < 0)
	{
		registro_dice(AREA, "⚠ the keymap cannot be read: %s", g_strerror(errno));
		return;
	}

	/*
	 * The keymap's FINGERPRINT, and not its name.
	 *
	 * ⛔ `[M]` 14 August 2026, on the test machine: the keymap Mutter
	 *    serialises carries `xkb_symbols "(unnamed)"` — **the name is not there**.  A
	 *    bench looking for a change of NAME would see «(unnamed)» before and
	 *    after, that is it would stay green while the layout has changed: it is
	 *    `CODER.md` §3.4 in action.  ⇒ Size in bytes plus a
	 *    checksum, which necessarily change if the layout changes.
	 */
	fingerprint = g_strdup_printf("%zu bytes, fingerprint %08x", measure, (unsigned) g_str_hash(text));

	/*
	 * ⛔ The layout is REOPENED, not updated: `tastiera.h` has no
	 *    way to change the keymap under a live `Keyboard`, and that is right
	 *    — an object that changes identity under whoever holds it is the
	 *    defect we are measuring, not the cure.
	 *
	 * ⚠ And the old one is closed ONLY if the new one opens: if the new keymap
	 *   does not compile, staying with the previous one is better than staying without
	 *   — and the line says so, so the fallback is not silent.
	 */
	/*
	 * ⚠ `negotiated` is **NULL, and for now that is right** — but it must be said, because
	 *   it has a consequence that reads like a defect:
	 *
	 *   `tastiera.c` compares the layout declared by the client in
	 *   `ATTACH` (`RCP.md` §4.5) with the session's real one, and if they do not
	 *   match it uses the SESSION's, writing `FALLBACK DICHIARATO`.
	 *   ⛔ With `NULL` that comparison **is never made**, so that line will never
	 *   come out: whoever looked for it in the log would conclude "they always
	 *   match", which is a different thing from "I did not look".
	 *
	 * ⇒ The day the negotiated layout arrives here (today `input.h`
	 *   does not carry it: `input_open` does not take it, and it is a choice of the
	 *   coordinator), **that one** is passed in place of this NULL and nothing
	 *   else is needed.  *(Line left by A5, 14 August 2026.)*
	 */
	/*
	 * ⭐ AND NOW THE NEGOTIATED ONE ARRIVES HERE — 16 August 2026, and until
	 *    tonight it was `NULL`.
	 *
	 * ⛔ The comment that stood here said that the NULL "for now is right", and
	 *    declared the consequence: `tastiera.c` compares the layout
	 *    declared by the client with the session's real one and writes
	 *    `FALLBACK DICHIARATO` if they do not match — and with `NULL` that comparison
	 *    **was never made**.  `[M]` bench `06-b34`, first round: that line
	 *    appears in NONE of the rounds, not even reattaching declaring
	 *    `us` to an `it` session.  ⇒ Whoever looked for it in the log would conclude
	 *    "they always match", which is a different thing from "I did not look"
	 *    (`LEZIONI.md` §1.9 rule 1).
	 *
	 * ⚠ And now it is needed twice over: with §5-bis.7 implemented WE ask the session
	 *   to set that layout, and this line is the only one saying whether
	 *   we really got it.  ⛔ If `gsd-keyboard` overwrote it on us
	 *   — it is the "surroundings" of `CODER.md` §4.1-bis, the ones not chased —
	 *   the fallback would appear HERE, instead of leaving the user with `Ctrl+Z`
	 *   on the wrong key and no line explaining it.
	 */
	new_one = keyboard_open_from_keymap(text, measure, in->negotiated, &mistake);
	if (!new_one)
	{
		registro_dice(AREA, "⚠ the keymap handed over by libei does not open (%s): %s",
		              mistake ?: "no reason declared",
		              in->kb_layout ? "keeping the previous one" : "LETTERS stay off");
	}
	else
	{
		g_clear_pointer(&in->kb_layout, keyboard_close);
		in->kb_layout = new_one;
	}

	if (g_strcmp0(fingerprint, in->keymap_name) != 0)
	{
		registro_dice(AREA, "KEYMAP CHANGED: %s (was: %s) → layout «%s»", fingerprint,
		              in->keymap_name ?: "none",
		              in->kb_layout ? kbd_layout(in->kb_layout) : "none");
		g_free(in->keymap_name);
		in->keymap_name = g_steal_pointer(&fingerprint);
	}
	else
		log_detail(AREA, "keymap unchanged: %s", fingerprint);

	/*
	 * ⛔ KWIN DID NOT HEAR — `[M]` 6 Oct 2026, Ubuntu 26.04 / KWin 6.6.6:
	 *    the negotiated `it` requested 1 s after the session start (kxkbrc +
	 *    `reloadConfig`), and the first keymap that arrived was `English (US)`, for
	 *    the whole session ⇒ F-009 red on Chrome and Firefox.  The signal has
	 *    no reply: if KWin does not yet have the `/Layouts` object listening
	 *    it is lost, and kxkbrc had already been read before we wrote it.
	 *    ⇒ The REAL keymap is the confirmation: if it is not the negotiated one, it is requested again,
	 *    at most 3 times (a KWin that never sets it stays with the FALLBACK
	 *    DECLARED of `tastiera.c`, not with an endless loop).
	 */
	if (in->kwin && in->negotiated && in->kb_layout &&
	    keyboard_is_this(in->kb_layout, in->negotiated) == 0 && in->kwin_requests < 3)
	{
		g_autoptr(GError) err_kwin = NULL;

		in->kwin_requests++;
		input_release_all(in); /* KWin redoes the keyboard device */
		if (kwin_layout(in->negotiated, &err_kwin) == 0)
			registro_dice(AREA,
			              "⚠ KWin set «%s» and not the negotiated «%s»: REQUESTING it again (%d of 3)",
			              kbd_layout(in->kb_layout), in->negotiated,
			              in->kwin_requests);
		else
			registro_dice(AREA, "⚠ KWin set «%s» and not «%s», and requesting it does not succeed: %s",
			              kbd_layout(in->kb_layout), in->negotiated,
			              err_kwin ? err_kwin->message : "no reason");
	}
}

/* ------------------------------------------------------------------ *
 *  libei's events
 * ------------------------------------------------------------------ */
static void device_added(Input *in, struct ei_device *device)
{
	gboolean absolute = ei_device_has_capability(device, EI_DEVICE_CAP_POINTER_ABSOLUTE);
	gboolean keys = ei_device_has_capability(device, EI_DEVICE_CAP_KEYBOARD);

	log_detail(AREA, "device «%s»: absolute=%d scroll=%d buttons=%d keyboard=%d",
	                   ei_device_get_name(device) ?: "?", absolute,
	                   ei_device_has_capability(device, EI_DEVICE_CAP_SCROLL),
	                   ei_device_has_capability(device, EI_DEVICE_CAP_BUTTON), keys);

	/*
	 * ⛔ THE LAST ARRIVED IS ALWAYS TAKEN, and not "the first that will do".
	 *
	 * It is the difference between bearing a replacement and not bearing it: after a change
	 * of geometry Mutter sends `DEVICE_REMOVED` + `DEVICE_ADDED`, and whoever keeps
	 * the first stays attached to a dead object **that gives no error**.
	 */
	if (absolute)
	{
		/* ⚠ The replacement is NOT counted here: `device_removed` counts it, which
		 *   arrives first.  Counting it in both places would double it. */
		if (in->pointer)
			ei_device_unref(in->pointer);
		in->pointer = ei_device_ref(device);
		in->pointer_active = FALSE;
		read_region(in, device);
	}
	if (keys)
	{
		if (in->keyboard_dev)
			ei_device_unref(in->keyboard_dev);
		in->keyboard_dev = ei_device_ref(device);
		in->keyboard_active = FALSE;
		read_keymap(in, device);
	}
}

/*
 * ⛔⛔ What was pressed on a device that goes away becomes an ORPHAN.
 *
 * The box at the top of the file says why: its release will reach
 * nobody, neither on the old device (which is gone) nor on the new one (where
 * Mutter discards it silently).  ⇒ It is MARKED, and the line is written **at once**,
 * at the instant the damage happens — not at the release, which is half a
 * second later and which whoever reads the log no longer connects to the replacement.
 *
 * ⚠ And it is written ONLY if something was pressed: a line at every replacement
 *   would drown the one that matters (`[M]` 15 replacements in three minutes on a bench).
 */
static void mark_orphans(Input *in, const uint8_t *map, uint8_t *orphans, uint32_t maximum,
                         unsigned amount, const char *what)
{
	if (!amount)
		return;
	for (uint32_t c = 0; c < maximum; c++)
		if (bit_read(map, c) && !bit_read(orphans, c))
		{
			bit_write(orphans, c, TRUE);
			in->how_many_orphans++;
		}
	registro_dice(AREA,
	              "⛔⛔ %u %s were PRESSED on the device the compositor has just removed: their "
	              "release will reach NOBODY, and the seat still counts them down.  ⇒ From "
	              "now on what passes through them is broken until the EIS channel drops.  The cure "
	              "is to release BEFORE asking for the resize (`figlio.c:3964`)",
	              amount, what);

	/*
	 * ⛔⛔ AND HERE THE HEALING IS ASKED FOR — cure "C".  🔸 Derived, 21 Aug 2026.
	 *
	 * ⭐ This is the exact instant the damage happens, and it is the only
	 *    place in the program that knows it.  ⚠ We do not heal NOW: we are inside
	 *    `ei_dispatch()`, and destroying the `libei` context while it is
	 *    delivering events to us is a defect that gives no error.  ⇒ It is marked, and
	 *    `input_run()` heals when the queue is empty.
	 *
	 * ⛔ And it is marked for ANY door: the resize, the wake-up
	 *    of the capture (§7.1), a Mutter `monitors-changed`, a keymap
	 *    change.  ⚠ It is the reason cure "C" exists next to "A":
	 *    "A" closes the door we control, "C" repairs those we do not
	 *    control — and `meta_eis_viewport_notify_changed()` entered
	 *    GNOME 48.5, that is it is NEW: others will come.
	 */
	in->healing_due = TRUE;
}

static void device_removed(Input *in, struct ei_device *device)
{
	if (in->pointer == device)
	{
		/* ⛔ And the count of what was pressed is NOT reset: the device has
		 *    gone, the user's buttons have not.  ⚠ But we NO LONGER hope to
		 *    release them on the new device — `[M]` 16 August 2026, it does not
		 *    arrive: they become ORPHANS, and it is said. */
		mark_orphans(in, in->buttons, in->orphan_buttons, MAX_BUTTON, in->how_many_buttons,
		             "buttons");
		ei_device_unref(in->pointer);
		in->pointer = NULL;
		in->pointer_active = FALSE;
		in->region_known = FALSE;
		/* ⛔ THE REPLACEMENT IS COUNTED HERE, NOT ONLY ON ADDITION — `[M]` 14 August
		 *    2026, and the bench paid for it: Mutter sends `DEVICE_REMOVED` **and
		 *    then** `DEVICE_ADDED`, so at the moment of the addition the old one
		 *    is already NULL and a counter that looks only there stays at **zero**.
		 *    ⚠ The bench printed "the replacement was NOT reproduced" while the
		 *    witness saw the seat lose keyboard and pointer: an
		 *    instrument blind precisely in the case it must see (`CODER.md` §3.4). */
		in->pointer_replacements++;
		registro_dice(AREA, "the pointer was REMOVED by the compositor (replacement n. %u)",
		              in->pointer_replacements);
	}
	if (in->keyboard_dev == device)
	{
		/* ⚠ At a GEOMETRY change the keyboard is not replaced — `[R]`
		 *   `remove_viewport_devices` looks only at TOUCH and POINTER_ABSOLUTE
		 *   (`meta-eis-client.c:197-206`), and `[M]` 16 August 2026: **zero**
		 *   keyboard replacements out of fifteen of the pointer.  ⛔ But at a
		 *   KEYMAP change yes, `on_keymap_changed` (`:762-781`) destroys and
		 *   recreates it — and there the orphan defect has the same form.  It is
		 *   sub-phase 6.2: here it is marked, so when it measures it the count
		 *   is already there. */
		mark_orphans(in, in->keys, in->orphan_keys, MAX_KEY, in->how_many_keys, "keys");
		ei_device_unref(in->keyboard_dev);
		in->keyboard_dev = NULL;
		in->keyboard_active = FALSE;
		in->keyboard_replacements++;
		registro_dice(AREA, "the keyboard was REMOVED by the compositor (replacement n. %u)",
		              in->keyboard_replacements);
	}
}

static void handle_event(Input *in, struct ei_event *event)
{
	enum ei_event_type kind = ei_event_get_type(event);
	struct ei_device *device = ei_event_get_device(event);

	switch (kind)
	{
		case EI_EVENT_CONNECT:
			/*
			 * ⛔⛔ THIS IS THE LINE THAT MAKES THE CLOSING SAFE — cure D4, 25
			 *     August 2026.  The box above `detach_context()` names the
			 *     instruction that crashed; here we mark the only fact that
			 *     tells a channel that can be disconnected from one that
			 *     kills the child.
			 *
			 * ⭐ `EI_EVENT_CONNECT` arrives **once only** after the connection
			 *    request (`libei.h`: *"This event is only sent once after
			 *    the initial connection request"*), and where the server does NOT approve
			 *    `EI_EVENT_DISCONNECT` arrives in its place.  ⇒ It is the
			 *    PROTOCOL's predicate, not a symptom.
			 */
			in->handshake_done = TRUE;
			in->handshake_us = g_get_monotonic_time();
			log_detail(AREA,
			                   "libei's handshake has ARRIVED after %.1f ms: from now on the "
			                   "channel can be closed the normal way",
			                   (double) (in->handshake_us - in->open_us) / 1000.0);
			break;

		case EI_EVENT_SEAT_ADDED:
			/*
			 * ⛔ The capabilities are ASKED for, and the devices are created by the
			 *    compositor.  ⚠ `POINTER` (relative) is asked for anyway though
			 *    not used: without it, does Mutter not even create the absolute one?  No —
			 *    `[R]` `meta-eis-client.c:1108-1114` binds them separately.  It is
			 *    asked for because `RCP.md` §7.3 keeps the relative pointer open
			 *    for the page's `Pointer Lock` (phase 4, link A7),
			 *    and the `MetaEis` is created **once only per session**: what
			 *    is not asked for now can never be asked for again.
			 */
			ei_seat_bind_capabilities(ei_event_get_seat(event), EI_DEVICE_CAP_POINTER,
			                          EI_DEVICE_CAP_POINTER_ABSOLUTE, EI_DEVICE_CAP_BUTTON,
			                          EI_DEVICE_CAP_SCROLL, EI_DEVICE_CAP_KEYBOARD, NULL);
			log_detail(AREA, "seat «%s»: capabilities requested",
			                   ei_seat_get_name(ei_event_get_seat(event)) ?: "?");
			break;

		case EI_EVENT_DEVICE_ADDED:
			device_added(in, device);
			break;

		case EI_EVENT_DEVICE_REMOVED:
			device_removed(in, device);
			break;

		case EI_EVENT_DEVICE_RESUMED:
			ei_device_start_emulating(device, ++in->sequence);
			if (device == in->pointer)
			{
				in->pointer_active = TRUE;
				/* ⛔ And it is reread HERE TOO: between `DEVICE_ADDED` and the resume the
				 *    compositor may have redone the viewports. */
				read_region(in, device);
			}
			if (device == in->keyboard_dev)
				in->keyboard_active = TRUE;
			log_detail(AREA, "device «%s» ready (sequence %u)",
			                   ei_device_get_name(device) ?: "?", in->sequence);
			break;

		case EI_EVENT_DEVICE_PAUSED:
			if (device == in->pointer)
				in->pointer_active = FALSE;
			if (device == in->keyboard_dev)
				in->keyboard_active = FALSE;
			break;

		case EI_EVENT_DISCONNECT:
			registro_dice(AREA, "⛔ the compositor CLOSED the input channel");
			in->dropped = TRUE;
			break;

		default:
			break;
	}
}

/* ------------------------------------------------------------------ *
 *  The contract
 * ------------------------------------------------------------------ */
static Input *do_open(MutterSession *session, KwinSession *kwin, uint32_t canvas_w,
                   uint32_t canvas_h, char **error)
{
	Input *in;
	int fd;

	if (error)
		*error = NULL;
	if (!session && !kwin)
	{
		if (error)
			*error = g_strdup("no Mutter session: the input channel has nobody to talk to");
		return NULL;
	}
	if (canvas_w == 0 || canvas_h == 0)
	{
		if (error)
			*error = g_strdup_printf("degenerate canvas %ux%u: the absolute coordinates would have "
			                          "no range",
			                          canvas_w, canvas_h);
		return NULL;
	}

	if (kwin)
	{
		GError *mistake = NULL;

		fd = kwin_eis_fd(kwin, &mistake);
		if (fd < 0)
		{
			if (error)
				*error = g_strdup_printf("KWin did not grant the input channel "
				                          "(connectToEIS): %s",
				                          mistake ? mistake->message : "no reason");
			g_clear_error(&mistake);
			return NULL;
		}
	}
	else
		fd = mutter_eis_fd(session);
	if (fd < 0)
	{
		/* ⛔ And we say WHY, not "it does not open": the `mutter.c` line that
		 *    declares the refusal of `ConnectToEIS` is already in the log, and
		 *    this one recalls it instead of adding a second mystery. */
		if (error)
			*error = g_strdup("ConnectToEIS gave no descriptor (the log of the "
			                   "«capture» area says why): no input can reach the desktop");
		return NULL;
	}

	in = g_new0(Input, 1);
	in->session = session;
	in->kwin = kwin;
	in->canvas_w = canvas_w;
	in->canvas_h = canvas_h;
	/* ⛔ Cure D4: the instant of the opening is marked HERE, because it is the only way
	 *    to say how long the dangerous window lasted when it closes. */
	in->open_us = g_get_monotonic_time();
	in->fd_socket = -1;

	in->ei = ei_new_sender(in);
	if (!in->ei)
	{
		if (error)
			*error = g_strdup("libei context not created");
		g_free(in);
		return NULL;
	}
	/* The name shows in the devices Mutter creates («remotix virtual
	 * keyboard», …) and in its log: it is the way to recognise ourselves from outside. */
	ei_configure_name(in->ei, "remotix");

	/*
	 * ⛔ A `dup`, and not `mutter.c`'s descriptor: `ei_setup_backend_fd`
	 *    TAKES OWNERSHIP of it, and closing it in two places is a defect that shows
	 *    at a distance — a descriptor recycled by another `open`.
	 */
	fd = dup(fd);
	if (fd < 0 || ei_setup_backend_fd(in->ei, fd) != 0)
	{
		if (error)
			*error = g_strdup("ConnectToEIS's descriptor was not accepted by libei");
		if (fd >= 0)
			close(fd);
		ei_unref(in->ei);
		g_free(in);
		return NULL;
	}
	/* ⛔ Cure D4: from here on the socket belongs to `libei` — it is kept aside
	 *    for the ONLY case in which the context must be abandoned.  ⚠ The `dup` is
	 *    already done: this is the number `libei` owns, not that of
	 *    `mutter.c`. */
	in->fd_socket = fd;

	/*
	 * ⛔ HERE NO LAYOUT IS OPENED, and it is intended.
	 *
	 * The keymap is not something we know at opening: it arrives from `libei`
	 * with the keyboard device, and changes under us.  ⇒ It is opened by
	 * `read_keymap`, at the first `DEVICE_ADDED` and at every replacement.  Until
	 * that moment `input_letter` answers -1, and says so.
	 */
	registro_dice(AREA, "input channel open to the compositor (libei), canvas %ux%u", canvas_w,
	              canvas_h);
	return in;
}

/*
 * ⛔⭐ THE DESCRIPTOR FOR THE CHILD'S `poll()` — see `input.h`.
 *
 * ⚠ It is a descriptor to WATCH, not to read: whoever puts it in the `poll()`
 *   does not `read()` on it.  When it becomes readable it calls `input_run()`,
 *   which is the only place `ei_dispatch()` can be — `libei` is not
 *   reentrant, and a byte taken by hand from under the library's feet would be
 *   a defect that gives no error.
 *
 * ⛔ -1 means "nothing to put in the poll", not "error".
 */
Input *input_open(void *session_mutter, uint32_t canvas_w, uint32_t canvas_h, char **error)
{
	return do_open(session_mutter, NULL, canvas_w, canvas_h, error);
}

Input *input_open_kwin(KwinSession *kwin, uint32_t canvas_w, uint32_t canvas_h, char **error)
{
	if (!kwin)
	{
		if (error)
			*error = g_strdup("no KWin stage: the input channel has nobody to talk to");
		return NULL;
	}
	return do_open(NULL, kwin, canvas_w, canvas_h, error);
}

int input_descriptor(Input *in)
{
	/* ⭐ wlroots: the descriptor of the Wayland wire, and -1 if it has dropped. */
	if (in && in->wlr)
		return wlr_input_descriptor(in->wlr);
	if (!in || !in->ei)
		return -1;
	return ei_get_fd(in->ei);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔⛔⛔ THE CHANNEL JUST BORN IS NOT DETACHED — cure **D4**, 25 August 2026.
 *
 * ⛔ THE FACT, `[M]` read from the core on 25 August 2026 (`fasi/10-…md` §5.1):
 *
 *       #0  ei_disconnect ()          from libei.so.1
 *       #2  input_close (…)          at input.c
 *       #3  unmount_stage (…)       at figlio.c
 *
 *   and from the same core the **when**: the EIS channel had been opened **33 ms
 *   earlier** and the handshake had not yet arrived.  The instruction that
 *   crashed is `mov 0x50(%rdi),%rdi` with `%rdi = 0`.
 *
 * ⭐⭐ AND THE MECHANISM IS EXACT, not deduced — `libei 1.3.901`, disassembled:
 *
 *     `struct ei` keeps the **state** at +0xc8 and the **connection** at +0x18.
 *       0 = just created · 1 = socket set, handshake REQUESTED and not yet
 *       arrived · 2 = the server sent `connection` · 3 = connected
 *       (⇒ `EI_EVENT_CONNECT`) · 4/5 = closing / closed.
 *
 *     `ei_disconnect()` returns at once if the state is 4 or 5, and skips the
 *     disconnection if the state is **0**.  For 1, 2 and 3 it calls
 *
 *         ei_connection_request_disconnect(ei->connection);   ⭐ checks NULL
 *         ei_connection_remove_pending_callbacks(ei->connection);  ⛔ does NOT
 *
 *     and the second begins precisely with `mov 0x50(%rdi),%rdi`.
 *   ⇒ ⛔⛔ **The hole is state 1, and only that**: connection still NULL, and the
 *     check present on the line above is missing on the one below.
 *
 * ⛔⛔ AND `ei_unref()` IS NOT A WAY OUT: the destructor `ei_destroy()`
 *      calls `ei_disconnect()` as its **first instruction**.  ⇒ On a context
 *      in state 1, `ei_unref()` alone kills the child exactly like
 *      `ei_disconnect()`.  There is no way to FREE it without going through there.
 *
 * ⇒ ⭐ THE CURE, in two half lines and a price:
 *
 *   · **the predicate is `EI_EVENT_CONNECT`** — the way `libei` has of saying
 *     "the server has approved" (`libei.h`).  ⛔ NOT the pointers `pointer` /
 *     `keyboard_dev` / `region_known` read in the core: those are **symptoms**,
 *     they arrive much later, and on a mature channel without devices they would say
 *     "nothing ever appeared" on a context that must instead be disconnected.
 *     ⚠ It is deliberately **more prudent than necessary**: between state 2 and 3
 *       there is a `sync` round in which `ei_disconnect()` would already be safe, and
 *       there it is abandoned anyway.  In that window no device
 *       exists, so nothing visible is lost;
 *
 *   · **mature context ⇒ REAL close, unchanged**: `ei_disconnect()` +
 *     `ei_unref()`, which is the protocol message that makes
 *     `drop_device()` run in Mutter and makes the virtual devices disappear.  ⛔ Without
 *     this branch the clean exit would be lost, which is half of the contract;
 *
 *   · **immature context ⇒ it is ABANDONED**, and the price is declared: the
 *     `struct ei` is lost (a few hundred bytes, once per stage dead
 *     in its first milliseconds), ⭐ but the **two descriptors are closed by hand** —
 *     the socket, which is what tells the compositor "the client has
 *     gone", and `libei`'s `epoll`.  ⚠ They can be closed precisely because
 *     the context is abandoned: nobody will touch them again, so there is
 *     no double close.
 *
 * ⛔ WHAT THIS CURE DOES **NOT** CURE, and it must be said: the same hole is also
 *    INSIDE `libei`.  `connection_dispatch()` calls `ei_disconnect()` by itself
 *    when reading from the socket fails ⇒ if the compositor dies while the
 *    state is 1, it is `ei_dispatch()` that crashes, and from outside it cannot be prevented.
 *    ⚠ Outside the mandate: the real cure is in `libei`.
 * ═══════════════════════════════════════════════════════════════════════════ */
static void detach_context(Input *in, const char *chi)
{
	double lived_ms;
	int epoll_di_libei;

	if (!in || !in->ei)
		return;

	lived_ms = (double) (g_get_monotonic_time() - in->open_us) / 1000.0;

	if (in->handshake_done)
	{
		/* ⭐ THE REAL CLOSE — this line is the usual one, and must
		 *    stay: it is `ei_disconnect()` that sends the protocol detach,
		 *    and it is that message (not the closing of the socket) that makes
		 *    `drop_device()` run in Mutter.  `[M]` faults `RG3`/`RG4`, 21 Aug 2026. */
		ei_disconnect(in->ei);
		ei_unref(in->ei);
		in->ei = NULL;
		in->fd_socket = -1; /* `libei` closed it together with the context */
		log_detail(AREA,
		                   "input channel detached by «%s»: handshake arrived after %.1f ms, "
		                   "lived %.1f ms, REAL close (ei_disconnect + ei_unref)",
		                   chi, (double) (in->handshake_us - in->open_us) / 1000.0, lived_ms);
		return;
	}

	/* ⛔⛔ THE DANGEROUS WINDOW — and it is declared with `registro_dice`, not with
	 *     `log_detail`: it is a rare event with a price, and whoever reads the
	 *     log after a stage that died young must find it written. */
	epoll_di_libei = ei_get_fd(in->ei);
	abandoned_contexts++;
	registro_dice(AREA,
	              "⛔ input channel ABANDONED by «%s» after %.1f ms: libei's handshake "
	              "had never arrived, and disconnecting (or freeing) such a context "
	              "makes the library crash.  ⇒ The descriptors are closed and the context is lost "
	              "(abandonments so far: %u).  ⚠ No virtual device is left hanging: at "
	              "this point none had been born yet",
	              chi, lived_ms, abandoned_contexts);

	/* ⛔ The order: first the reference is dropped, then the descriptors are closed.
	 *    The other way round there would be an instant in which the context is still
	 *    reachable with its descriptors already closed. */
	in->ei = NULL;
	if (epoll_di_libei >= 0)
		close(epoll_di_libei);
	if (in->fd_socket >= 0)
		close(in->fd_socket);
	in->fd_socket = -1;
}

/*
 * ⛔⛔⛔ CURE "C", IMPLEMENTED — the EIS channel is redone and the seat unblocks.
 *       🔸 Derived by the coordinator on 21 August 2026 (not decided by the user).
 *
 * ⚠ IT IS CALLED ONLY FROM `input_run()`, with an empty queue: destroying the `libei`
 *   context inside `ei_dispatch()` is a defect that gives no error.
 *
 * ⛔ THE PRICE, DECLARED: **the drag in progress is cut** —
 *    `drop_device()` sends a clean release for everything that was pressed.
 *    ⭐ But that drag **was already dead** (`[M]` 21 Aug 2026, bench
 *    `06-b33-risveglio.sh held`: after the replacement the release does not arrive and
 *    neither does the next click).  ⇒ A broken thing is cut and made to
 *    start again, which is a net gain.
 *    ⚠ It also costs a D-Bus round and the recreation of the devices, and in
 *      that window no input arrives.
 *
 * ⛔ What is NOT lost: the `RemoteDesktop` session, the virtual monitor and
 *    the PipeWire stream.  `[R]` `meta-remote-desktop-session.c:1943-1969`: the
 *    second `ConnectToEIS` reuses `session->eis` and adds a client.
 */
static void heal(Input *in)
{
	g_autoptr(GError) mistake = NULL;
	gint64 t_now = g_get_monotonic_time();
	int fd, fresh;

	if (in->last_heal_us && t_now - in->last_heal_us < HEALING_BACKSTOP_US)
		return; /* ⚠ and the flag STAYS on: retried after the floor */
	in->last_heal_us = t_now;

	registro_dice(AREA,
	              "⭐⭐ HEALING (n. %u): redoing the EIS channel.  The seat still counts down "
	              "%u orphan keys and buttons, and from the client side it is NOT recovered "
	              "(`meta-eis-client.c:612-621` swallows the release on the new device).  "
	              "⛔ The price: the drag in progress is CUT — but it was already dead",
	              in->recoveries + 1, in->how_many_orphans);

	/* ⛔ The devices are let go BEFORE the context: they hold a reference to
	 *    `struct ei`, and a context freed under a live device is a
	 *    defect that shows elsewhere. */
	if (in->pointer)
		ei_device_unref(in->pointer);
	if (in->keyboard_dev)
		ei_device_unref(in->keyboard_dev);
	in->pointer = NULL;
	in->keyboard_dev = NULL;
	in->pointer_active = FALSE;
	in->keyboard_active = FALSE;
	in->region_known = FALSE;
	in->scaled_region_warned = FALSE;
	g_clear_pointer(&in->reg_per, g_free);
	g_clear_pointer(&in->keymap_name, g_free);

	/* ⛔ Cure D4: the same door as `input_close()`, and not a copy.  ⚠ Here
	 *    the handshake has almost always arrived (we heal after a device
	 *    replacement, which necessarily comes after the handshake), but "almost always"
	 *    is exactly the way this hole was born. */
	detach_context(in, "healing");

	/* ⛔ AND THE DETACH HAS ALREADY BEEN SENT BY `ei_disconnect()` above — `[M]` 21
	 *    Aug 2026, faults `RG3`/`RG4`: it is that protocol message that makes
	 *    `drop_device()` run in Mutter, not the closing of the socket.
	 * ⇒ What is needed from `mutter.c` is a NEW descriptor: after the detach
	 *   the one put aside is dead, and a `ConnectToEIS` wants the bus and the
	 *   session path, which this file does not have (and must not have). */
	fresh = in->kwin ? kwin_eis_reattach(in->kwin, &mistake)
	                 : mutter_eis_reattach(in->session, &mistake);
	if (fresh < 0)
	{
		registro_dice(AREA,
		              "⛔⛔ the healing did NOT succeed (%s): the input channel is gone. "
		              "⚠ The seat is unblocked anyway — the closing already did it — but from "
		              "now on the user WATCHES and does not control",
		              mistake ? mistake->message : "no reason declared");
		in->dropped = TRUE;
		in->healing_due = FALSE;
		return;
	}

	/* ⛔ Cure D4: the NEW channel starts from scratch — handshake not yet arrived,
	 *    and the clock of the dangerous window reset.  ⚠ Forgetting it
	 *    would make a connection just born look mature, that is it would put back
	 *    the hole at the first teardown after a healing. */
	in->handshake_done = FALSE;
	in->handshake_us = 0;
	in->open_us = g_get_monotonic_time();
	in->fd_socket = -1;

	in->ei = ei_new_sender(in);
	if (!in->ei)
	{
		registro_dice(AREA, "⛔⛔ libei context not recreated: the input channel is over");
		in->dropped = TRUE;
		in->healing_due = FALSE;
		return;
	}
	ei_configure_name(in->ei, "remotix");
	/* ⛔ A `dup`, as in `input_open()`: `ei_setup_backend_fd` takes ownership of it
	 *    and closing it in two places is a defect that shows at a distance. */
	fd = dup(fresh);
	if (fd < 0 || ei_setup_backend_fd(in->ei, fd) != 0)
	{
		if (fd >= 0)
			close(fd);
		ei_unref(in->ei);
		in->ei = NULL;
		registro_dice(AREA, "⛔⛔ the new descriptor was not accepted by libei: the input "
		                    "channel is over");
		in->dropped = TRUE;
		in->healing_due = FALSE;
		return;
	}
	in->fd_socket = fd; /* ⛔ Cure D4, as in `input_open()`: needed if it must be abandoned */

	/*
	 * ⛔⛔ AND THE COUNT IS RESET, ORPHANS INCLUDED, because now it is TRUE:
	 *     `drop_device()` has just sent the seat the release of everything
	 *     that was pressed.  ⚠ Keeping them marked would make the detach
	 *     release things nobody holds down, and would keep on forever the
	 *     «DOES NOT LEAVE» line on a channel that instead works.
	 */
	memset(in->keys, 0, sizeof in->keys);
	memset(in->buttons, 0, sizeof in->buttons);
	memset(in->orphan_keys, 0, sizeof in->orphan_keys);
	memset(in->orphan_buttons, 0, sizeof in->orphan_buttons);
	in->how_many_keys = 0;
	in->how_many_buttons = 0;
	in->how_many_orphans = 0;
	in->sequence = 0;

	in->recoveries++;
	in->healing_due = FALSE;
	registro_dice(AREA,
	              "⭐⭐ EIS channel REDONE (healing n. %u): the devices are reborn and the seat's "
	              "count is back to zero.  ⚠ Keymap and region are reread at the next "
	              "`DEVICE_ADDED`, as always.  ⛔ The session, the monitor and the stream were NOT "
	              "touched",
	              in->recoveries);
}

int input_run(Input *in)
{
	struct ei_event *event;
	int amount = 0;

	if (!in)
		return -1;
	if (in->wlr)
		return run_wlr(in);
	if (in->dropped)
		return -1;

	/*
	 * ⛔⛔⛔ THE THIRD PATH — *"the stage has gone away"*, cure D4, 25 Aug 2026.
	 *
	 * `[M]` **Measured, not feared** (bench `10-d4`, scene `caduta-immatura`):
	 * if the compositor dies while the handshake has not yet arrived,
	 * the child dies **inside `ei_dispatch()`**, and the stack is the same:
	 *
	 *     ei_disconnect+0xda ← connection_dispatch ← ei_dispatch
	 *
	 * ⇒ `libei` calls `ei_disconnect()` **by itself** when reading from the socket
	 *   fails, and falls in the same place.  ⛔ The cure of `input_close()` does not
	 *   reach here: here one does not even get to `input_close()`.
	 *
	 * ⭐ The only possible defence from outside is NOT TO ENTER: we ask the socket —
	 *    the real one, not the `epoll` that `ei_get_fd()` returns — whether the
	 *    compositor is still there, and if it has gone the channel is abandoned
	 *    instead of dispatched.
	 *
	 * ⚠ `events = 0` is intended: `POLLHUP`/`POLLERR`/`POLLNVAL` always come back,
	 *   whatever is asked, and here we do NOT want to wake up for data —
	 *   the caller takes care of that as it always has.
	 * ⚠ And the price, declared: if the handshake had arrived **together** with the
	 *   closing, it would be thrown away.  ⛔ But a channel whose compositor is dead
	 *   is dead anyway: a connection already lost is lost.
	 * ⛔ And the question is asked ONLY until the handshake has arrived: afterwards,
	 *   `libei` handles the drop well by itself, and interfering would be a
	 *   second way of doing the same thing.
	 */
	if (!in->handshake_done && in->ei && in->fd_socket >= 0)
	{
		struct pollfd probe;

		probe.fd = in->fd_socket;
		probe.events = 0;
		probe.revents = 0;
		if (poll(&probe, 1, 0) > 0 && (probe.revents & (POLLHUP | POLLERR | POLLNVAL)))
		{
			registro_dice(AREA,
			              "⛔⛔ the compositor closed the EIS channel BEFORE the "
			              "handshake (after %.1f ms): NOT dispatching it, because libei would crash "
			              "inside its own ei_disconnect().  ⚠ From now on the user WATCHES "
			              "and does not control, and the stage is torn down the normal way",
			              (double) (g_get_monotonic_time() - in->open_us) / 1000.0);
			detach_context(in, "drop before the handshake");
			in->dropped = TRUE;
			return -1;
		}
	}

	ei_dispatch(in->ei);
	while ((event = ei_get_event(in->ei)) != NULL)
	{
		handle_event(in, event);
		ei_event_unref(event);
		amount++;
	}
	/* ⛔ The healing is HERE and not inside `handle_event`: with an empty queue, and
	 *    after `device_removed()` has already marked the orphans. */
	if (in->healing_due && !in->dropped)
		heal(in);
	return in->dropped ? -1 : amount;
}

int input_pointer(Input *in, uint32_t x, uint32_t y)
{
	double fx, fy;

	/* ⭐ wlroots: the protocol is NORMALISED on the extent it is given
	 *    (the canvas), and the output is the one the pointer is bound to — no
	 *    region to look for.  ⛔ And no transformation: the coordinates go
	 *    as they arrive, with the canvas as yardstick. */
	if (in && in->wlr) {
		in->wlr_pointer_known = TRUE;
		in->wlr_px = x;
		in->wlr_py = y;
		in->wlr_pl = in->canvas_w;
		in->wlr_pa = in->canvas_h;
		return wlr_input_absolute(in->wlr, x, y, in->canvas_w, in->canvas_h);
	}
	if (!in || !in->pointer || !in->pointer_active)
		return -1;
	if (!in->region_known)
		return -1;

	/*
	 * ⛔ NO TRANSFORMATION when the region is as large as the canvas — which
	 *    is the normal case, and then this is a SUM and not a scale:
	 *    the region's origin is where our screen sits in the compositor's global
	 *    space, and without it the pointer would end up
	 *    on the other monitor.  `RCP.md` §7.3 forbids **transforming the
	 *    received coordinates**, not knowing where the screen is.
	 *
	 * ⚠ And if the region is NOT as large as the canvas, we scale **and say so**:
	 *   it is open question n.1 of phase 4 — who decides the size of the
	 *   monitor now that the session no longer gives it (`RCP.md` §4.5).  A
	 *   silent resize here would be the wrong answer given by
	 *   someone without the authority to give it.
	 */
	if (in->reg_l == (double) in->canvas_w && in->reg_a == (double) in->canvas_h)
	{
		fx = in->reg_x + (double) x;
		fy = in->reg_y + (double) y;
	}
	else
	{
		if (!in->scaled_region_warned)
		{
			in->scaled_region_warned = TRUE;
			registro_dice(AREA,
			              "⚠ the region (%.0fx%.0f) is NOT as large as the canvas (%ux%u): scaling the "
			              "coordinates, and it is a decision this module should not "
			              "take — RCP.md §4.5, the granted canvas",
			              in->reg_l, in->reg_a, in->canvas_w, in->canvas_h);
		}
		fx = in->reg_x + (double) x * in->reg_l / (double) in->canvas_w;
		fy = in->reg_y + (double) y * in->reg_a / (double) in->canvas_h;
	}

	ei_device_pointer_motion_absolute(in->pointer, fx, fy);
	beat_border(in, in->pointer);
	return 0;
}

/*
 * ⛔ THE CANVAS CHANGES ON THE FLY — `CANVAS(FITTED)` of `RCP.md` §7.1.
 *
 * The defect this function exists not to have: `rcp.c` saturates the
 * coordinates on the NEW canvas while `input.c` stays mapped on the OLD one.
 * Two sides with two truths, and ⛔ **no error anywhere** — the same
 * form phase 3 already paid for with the codec string.
 *
 * ⛔ And the region is REREAD at once, instead of waiting for the next
 *    `DEVICE_ADDED`: the moment of the `CANVAS` is not the moment of the `DEVICE_ADDED`,
 *    and between the two there would be a window in which the pointer goes elsewhere.
 *
 * ⚠ Whoever changes the canvas, though, **is not whoever changes the monitor**: if
 *   `libei`'s region stays as large as it was, this function will find it different from the
 *   canvas and will say so (see `input_pointer`).  It is open question n.1 of
 *   phase 4 — who decides the size of the monitor (`RCP.md` §4.5) — and this
 *   module DECLARES it instead of answering it on its own.
 */
int input_recanvas(Input *in, uint32_t canvas_w, uint32_t canvas_h)
{
	if (!in)
		return -1;
	if (canvas_w == 0 || canvas_h == 0)
	{
		registro_dice(AREA, "⛔ degenerate canvas %ux%u refused: keeping %ux%u", canvas_w, canvas_h,
		              in->canvas_w, in->canvas_h);
		return -1;
	}
	if (canvas_w == in->canvas_w && canvas_h == in->canvas_h)
		return 0;

	registro_dice(AREA, "the canvas changes: %ux%u → %ux%u", in->canvas_w, in->canvas_h, canvas_w, canvas_h);
	in->canvas_w = canvas_w;
	in->canvas_h = canvas_h;
	/* ⛔ And the complaint about the scale is re-armed: the previous region may have been
	 *    as large as the previous canvas, and no longer be. */
	in->scaled_region_warned = FALSE;
	if (in->pointer)
		read_region(in, in->pointer);
	return 0;
}

/*
 * ⭐ PHASE 15, D-007 — `input.h`, and the why in `sessione.h` (the box of
 *    `SESSION_LABWC_KEYBOARD`).
 *
 * ⛔ The codes are evdev (`linux/input-event-codes.h`), and the keys are the
 *    LEFT ones: in every pc105 layout they are Super_L, Control_L, Alt_L and
 *    Shift_L, while the RIGHT Alt is AltGr (ISO_Level3_Shift) in half of Europe.
 *    F12 stays F12 even with Shift.  ⚠ `SESSION_LABWC_KEY` and these
 *    five numbers say the same thing: if one changes, the others change.
 */
#define RETURN_SUPER 125 /* KEY_LEFTMETA */
#define RETURN_CTRL 29   /* KEY_LEFTCTRL */
#define RETURN_ALT 56    /* KEY_LEFTALT */
#define RETURN_SHIFT 42 /* KEY_LEFTSHIFT */
#define RETURN_F12 88    /* KEY_F12 */

int input_bring_back_inside(Input *in)
{
	static const uint16_t combination[] = { RETURN_SUPER, RETURN_CTRL, RETURN_ALT,
		                                 RETURN_SHIFT, RETURN_F12 };
	const size_t amount = G_N_ELEMENTS(combination);
	size_t down = 0;
	int outcome = 1;

	/* GNOME and KDE: the compositor brings the windows back inside by itself. */
	if (!in || !in->wlr)
		return 0;

	/* ⛔ We start from an EMPTY keyboard: a modifier left down would make
	 *    a combination labwc does not recognise (or, worse, another one). */
	input_release_all(in);
	for (down = 0; down < amount; down++)
		if (send_key(in, combination[down], 1) < 0) {
			outcome = -1;
			break;
		}
	/* ⛔ And EVERYTHING that left is released in reverse, even if the
	 *    combination stayed half way. */
	while (down > 0)
		send_key(in, combination[--down], 0);

	/* The pointer goes back where the user had it, on the canvas of NOW. */
	if (in->wlr_pointer_known && in->wlr_pl && in->wlr_pa && in->canvas_w && in->canvas_h) {
		uint32_t x = (uint32_t)((uint64_t)in->wlr_px * in->canvas_w / in->wlr_pl);
		uint32_t y = (uint32_t)((uint64_t)in->wlr_py * in->canvas_h / in->wlr_pa);

		if (x >= in->canvas_w)
			x = in->canvas_w - 1;
		if (y >= in->canvas_h)
			y = in->canvas_h - 1;
		input_pointer(in, x, y);
	}

	if (outcome < 0)
		registro_dice(AREA,
		              "⛔ D-007: the «bring back inside» shortcut (%s) did NOT leave: "
		              "large windows may stay partly outside the screen "
		              "%ux%u",
		              SESSION_LABWC_KEY, in->canvas_w, in->canvas_h);
	else
		registro_dice(AREA,
		              "⭐ D-007: typed the «bring back inside» shortcut (%s) — labwc "
		              "brings the windows back inside the screen %ux%u",
		              SESSION_LABWC_KEY, in->canvas_w, in->canvas_h);
	return outcome;
}

/*
 * ⛔⭐⭐ THE NEGOTIATED LAYOUT ENTERS THE SESSION — §5-bis.7 implemented.
 *
 * ⛔⛔ AND THIS IS THE MOST DEBATABLE LINE OF THE FILE: IT GOES THROUGH `GSettings`,
 *     THAT IS THROUGH THE "SURROUNDINGS" THAT `CODER.md` §4.1-bis SAYS NOT TO CHASE.
 *
 * The rule says: the **compositor** must be chased, the surroundings not.  And
 * `org.gnome.desktop.input-sources` is surroundings through and through — it is the key
 * read by **`gsd-keyboard`**, that is a GNOME daemon, not Mutter.
 *
 * ⇒ Why it is done anyway, and the test of §4.1-bis applied in full
 *   *("how many different implementations would I have to chase, and how much does it cost to do it
 *   myself?")*:
 *
 *   · **doing it ourselves is not possible.**  The session's layout is applied by
 *     the compositor, and ⛔ `libei` **has no client→server direction for the
 *     keymap**: `ei_device_keyboard_get_keymap()` HANDS it over and that is all.  There
 *     is no `ei_device_keyboard_set_keymap()`.  ⇒ It is not "it costs a lot": it is
 *     that the lever on our side **does not exist**;
 *   · **and Mutter does not offer it either** on its `RemoteDesktop` D-Bus: there are
 *     `NotifyKeyboardKeycode` and `NotifyKeyboardKeysym`, that is two ways to
 *     TYPE a key, none to change the layout;
 *   · ⇒ what remains is the only lever that exists on GNOME, and it is this one.
 *
 * ⛔ And so the price of §4.1-bis is paid **by declaring it**, which is the part
 *    that rule does not allow to skip: **this function is GNOME's,
 *    and on KDE it will not work** (there the key is `kxkbrc`, and phase 11 will have to
 *    write another one).  ⇒ The right place for it to live is `mutter.c`, with
 *    its twin in `kwin.c` — ⚠ but `mutter.c` is not mine tonight (sub-phase
 *    6.3 is working on it), and the report hands over the move
 *    as a seam instead of doing it on the sly.
 *
 * ⚠ And there is a second reason why the fallback must be declared and not deduced:
 *   `gsd-keyboard` can **overwrite us again**.  It is not prevented — it would be
 *   chasing the surroundings — it is MEASURED: the line saying whether we
 *   got it is that of `read_keymap()` at the `DEVICE_ADDED` that follows, where
 *   the negotiated one now also passes (see the box there).
 */
int input_layout(Input *in, const char *name)
{
	g_autofree char *value = NULL;
	g_autofree char *xkb = NULL;
	GSettingsSchemaSource *source;
	g_autoptr(GSettingsSchema) schema = NULL;
	g_autoptr(GSettings) settings = NULL;
	const char *par;

	if (!in || !name || !*name)
		return -1;
	/* ⭐ wlroots: no GSettings — the layout becomes the keymap of our
	 *    virtual keyboard.  ⛔ The branch below is GNOME's (its box
	 *    says so) and on XFCE it would write into a schema nobody reads. */
	if (in->wlr)
		return layout_wlr(in, name);

	/*
	 * ⛔⛔ THE SAME THING IS NOT ASKED TWICE — ⚠ AND THE RIGHT QUESTION IS
	 *     "WHAT IS THERE NOW?", NOT "WHAT DID I ASK FOR?".
	 *
	 * Not asking needlessly matters: a keymap replacement costs Mutter the
	 * DESTRUCTION and recreation of the keyboard device (`STUDI.md` §gnome
	 * §9), and doing it for nothing shows.
	 *
	 * ⛔ But the first draft remembered **what it had asked for**
	 *    (`g_strcmp0(in->negotiated, name)`), and it was form **E1**: between one
	 *    request and the next the session's layout can change at the
	 *    hand of **someone else** — the user from the settings, `gsd-keyboard`,
	 *    or a bench.  `[M]` 16 August 2026: session brought back to `it` from outside,
	 *    client reattaching declaring `de`, and the log said
	 *    *«layout «de»: already requested, I do not request it again»* — with the session
	 *    Italian.  ⇒ **`Ctrl+Z` arrived as `Ctrl+Y`**, that is exactly
	 *    the fault this function exists to cure.
	 *
	 * ⇒ We ask the REAL keymap, the one `libei` handed over to us.
	 * ⚠ And we skip ONLY on a clean `1`: `-1` means "I could not say", and
	 *   on a don't-know we ASK — better one replacement too many than a session
	 *   with misaligned shortcuts and no line explaining it.
	 */
	if (in->kb_layout && keyboard_is_this(in->kb_layout, name) == 1)
	{
		g_free(in->negotiated);
		in->negotiated = g_strdup(name);
		log_detail(AREA,
		                   "layout «%s»: the session ALREADY has it (verified on the keymap, "
		                   "not on memory), not requesting it",
		                   name);
		return 0;
	}

	/*
	 * ⭐ PHASE 15, D-008 — KWin has its own way (`kwin_layout()`, and the
	 *    box there).  ⛔ And BEFORE GNOME's schema: a KDE machine
	 *    may have the schemas installed (any GTK program brings them),
	 *    and then the negotiated layout ended up in a key nobody reads on Plasma,
	 *    without even the fallback line.
	 */
	if (in->kwin)
	{
		g_autoptr(GError) err_kwin = NULL;

		/* ⛔ First everything is released: KWin redoes the keyboard device (see
		 *    the box below, "AND BEFORE ASKING FOR THE CHANGE"). */
		input_release_all(in);
		g_free(in->negotiated);
		in->negotiated = g_strdup(name);
		in->kwin_requests = 0;
		if (kwin_layout(name, &err_kwin) != 0)
		{
			registro_dice(AREA,
			              "⚠ DECLARED FALLBACK: layout «%s» was NOT requested "
			              "from KWin (%s) — the session keeps «%s».  ⛔ The letters that "
			              "layout does not have do NOT come out, and the SHORTCUTS go on the keys "
			              "of that one (RCP.md §7.3)",
			              name, err_kwin ? err_kwin->message : "no reason",
			              in->kb_layout ? kbd_layout(in->kb_layout)
			                               : "none");
			return -1;
		}
		registro_dice(AREA,
		              "layout «%s» REQUESTED from KWin (the session's kxkbrc + "
		              "reloadConfig + kconfig ConfigChanged) — §5-bis.7. ⚠ requested, not yet in "
		              "force: «KEYMAP CHANGED» will say so",
		              name);
		return 0;
	}

	/*
	 * ⚠ The two syntaxes are not the same, and confusing them is a mute fault:
	 *   `RCP.md` §4.5 writes the variant in **parentheses** — `de(neo)` — and
	 *   `org.gnome.desktop.input-sources` writes it with a **plus** — `de+neo`.
	 *   ⛔ Passing `de(neo)` to GNOME does not give an error: it gives a
	 *   source that does not exist, and the session stays with the previous one —
	 *   that is a silent fallback.
	 */
	par = strchr(name, '(');
	if (par)
	{
		const char *is_closed = strchr(par + 1, ')');
		if (!is_closed)
			return -1;
		xkb = g_strdup_printf("%.*s+%.*s", (int) (par - name), name,
		                      (int) (is_closed - par - 1), par + 1);
	}
	else
		xkb = g_strdup(name);

	/*
	 * ⛔ THE SCHEMA IS LOOKED UP, NOT TAKEN FOR GRANTED.  `g_settings_new()` on
	 *    a schema that is not there **aborts the process** — and the process is
	 *    the child, that is the user's stage.  ⇒ On a machine without the
	 *    GNOME schemas (a container, a different desktop) the service must
	 *    degrade, not die: `CODER.md` §4.2.
	 */
	source = g_settings_schema_source_get_default();
	schema = source ? g_settings_schema_source_lookup(source, "org.gnome.desktop.input-sources",
	                                                 TRUE)
	               : NULL;
	if (!schema)
	{
		registro_dice(AREA,
		              "⚠ DECLARED FALLBACK: the schema «org.gnome.desktop.input-sources» is not "
		              "on this machine — layout «%s» is NOT applied, and the "
		              "session keeps its own. ⛔ The letters that one does not have do NOT come out "
		              "(D-008: the earlier sentence, «they will come out right anyway», was false), "
		              "and the SHORTCUTS go on its keys (RCP.md §7.3)",
		              name);
		return -1;
	}

	/*
	 * ⛔⛔ PHASE 15, D-015 — THE USER'S SETTINGS ARE NOT TOUCHED
	 *     (the user's decision of 25 Sep 2026).
	 *
	 * Until today this write ended up in the USER's dconf
	 * (`~/.config/dconf/user`) and stayed there: whoever then logged in at the monitor
	 * found the keyboard changed.  ⭐ Now the child reads and writes
	 * through the SESSION's dconf (`session_dconf_prepare()`: an
	 * in-memory database on top, the user's below read-only),
	 * and so does the Shell.
	 * ⛔ And if that dconf is not there, we do NOT write: better a layout not
	 *    applied, and said, than one written where the user does not want it.
	 */
	if (!session_dconf_of_session())
	{
		registro_dice(AREA,
		              "⚠ DECLARED FALLBACK: the session's dconf is not in force — "
		              "layout «%s» is NOT written (it would end up in the USER's "
		              "settings, D-015), and the session keeps «%s».  ⛔ The letters that "
		              "one does not have do NOT come out, and the SHORTCUTS go on its keys "
		              "(RCP.md §7.3)",
		              name, in->kb_layout ? kbd_layout(in->kb_layout)
		                                     : "none");
		return -1;
	}

	/*
	 * ⛔⛔⭐ AND BEFORE ASKING FOR THE CHANGE, EVERYTHING IS RELEASED.
	 *
	 * ⭐ It is not prudence: it is the cure the POINTER link (subphase 6.1)
	 *    measured and wrote a few lines above, applied to the place where
	 *    this function makes it necessary.
	 *
	 * ⛔ The fact, `[R]` `meta-eis-client.c:638-645`: a release sent on the
	 *    NEW device for a key pressed on the OLD one is **discarded
	 *    silently**.  ⇒ A key that is down at the instant of the replacement becomes
	 *    an ORPHAN: its release does not leave, and never will.
	 *
	 * ⛔ And this function **causes the replacement on purpose**: changing the
	 *    layout destroys and recreates the keyboard device (`STUDI.md`
	 *    §gnome §9).  ⇒ If the user is holding a modifier while
	 *    the layout changes — and it happens: one reattaches from another keyboard
	 *    **while typing** — that modifier stays down and the desktop becomes
	 *    unusable, which is exactly the damage of `RCP.md` §11.
	 *
	 * ⇒ The line of the cure, from the pointer link: *"the cure is to release
	 *   BEFORE the replacement"*.  Here is the only place where the "before" still
	 *   exists — afterwards, the device is already another one.
	 *
	 * ⚠ And it is done even when nothing is pressed: `input_release_all()`
	 *   **always** writes its line, and a declared zero is worth more than a
	 *   silence (it is the reason that function is made that way).
	 */
	input_release_all(in);

	settings = g_settings_new("org.gnome.desktop.input-sources");
	value = g_strdup_printf("[('xkb','%s')]", xkb);

	if (!g_settings_set_value(settings, "sources", g_variant_new_parsed(value)))
	{
		registro_dice(AREA, "⚠ layout «%s» was NOT written into input-sources", name);
		return -1;
	}
	/* ⛔ And `current` too, or GNOME stays on the previous index when the list
	 *    gets shorter — and an index outside the list means "none". */
	g_settings_set_uint(settings, "current", 0);
	g_settings_sync();

	g_free(in->negotiated);
	in->negotiated = g_strdup(name);

	/*
	 * ⛔ AND HERE WE DO NOT SAY IT IS IN FORCE, because we do not know it yet.
	 *    Between this line and the applied layout there is `gsd-keyboard`
	 *    reading the key, Mutter recompiling the keymap, the keyboard
	 *    device destroyed and recreated, and `read_keymap()` rereading.
	 *    ⚠ "I asked for it" and "it is in force" are two different facts (form E1), and
	 *      the line that ascertains the second is «KEYMAP CHANGED», a few
	 *      milliseconds further down.
	 */
	registro_dice(AREA,
	              "layout «%s» REQUESTED from the session (input-sources = %s, in the "
	              "SESSION's dconf: the user's is not touched, D-015) — §5-bis.7. "
	              "⚠ requested, not yet in force: «KEYMAP CHANGED» will say so",
	              name, value);
	return 0;
}

int input_button(Input *in, uint16_t code, int pressed)
{
	if (!in)
		return -1;
	return send_button(in, code, pressed);
}

int input_wheel(Input *in, int32_t axis_x, int32_t axis_y)
{
	/* ⭐ wlroots: same direction as below — the vertical is inverted HERE, once
	 *    only (see the box), and `wlr_input_wheel()` receives the
	 *    Wayland convention.  It makes the whole notches itself (§7.2 n.1). */
	if (in && in->wlr)
		return wlr_input_wheel(in->wlr, axis_x, -axis_y);
	if (!in || !in->pointer || !in->pointer_active)
		return -1;

	/*
	 * ⛔⛔ THE SIGN OF THE VERTICAL AXIS IS INVERTED HERE, ONCE ONLY.
	 *
	 * `[M]` 10 August 2026 (`RCP.md` §7.3, box «The sign of the wheel»):
	 * injecting `+120` the remote page **goes down** — `deltaY = +114`, that is the
	 * content moves towards the end of the document.  And `RCP.md` §7.3 fixes the other
	 * half: the client sends `+120` when the user turns the wheel **up**.
	 * ⇒ The two conventions are OPPOSITE.  Without this minus, the remote screen
	 *   would scroll backwards for **every** user.
	 *
	 * ⚠ And the horizontal is NOT touched: `+120` = "to the right" on both
	 *   sides.  It is not a deduced symmetry — it is measured by the bench
	 *   `04-b24-iniezione` in both directions, like the vertical.
	 */
	/* ⭐ On KWin the notch is `scroll_discrete` in units of 120, that is those
	 *    of `RCP.md` §7.3 just as they arrive: `scroll_delta` KWin translates
	 *    with `deltaV120 = 0` and no notch (`STUDI.md` §kde §7.2, v1
	 *    `input.c:227-251`).  The direction is the same convention as below. */
	if (in->kwin)
		ei_device_scroll_discrete(in->pointer, axis_x, -axis_y);
	else
	ei_device_scroll_delta(in->pointer, (double) axis_x / UNIT_PER_DELTA,
	                       (double) -axis_y / UNIT_PER_DELTA);
	beat_border(in, in->pointer);
	return 0;
}

int input_letter(Input *in, uint32_t character)
{
	uint16_t codes[KEYBOARD_MAX_POSITIONS];
	size_t how_many = 0;
	int outcome;

	if (!in)
		return -1;
	if (in->wlr)
		return letter_wlr(in, character);
	if (!in->kb_layout)
	{
		/* ⛔ And it is NOT the "not producible" case: that one is 1, and means the
		 *    layout exists and does not make that letter.  Here the layout
		 *    does not exist at all, and it is a fault — confusing them would take away from whoever
		 *    reads the log the only difference that matters. */
		/* ⛔ Phase 16 §12: the typed character is NOT written. */
		registro_dice(AREA, "⚠ LETTER not sent: no layout (libei has not "
		                    "yet handed over a keymap)");
		return -1;
	}
	if (!in->keyboard_dev || !in->keyboard_active)
		return -1;

	outcome = keyboard_positions_for(in->kb_layout, character, codes, &how_many);
	if (outcome < 0)
		return -1;
	if (outcome == 0 || how_many == 0)
	{
		/*
		 * ⛔ NOT producible: a different letter is NOT sent and we do NOT keep quiet
		 *    (`RCP.md` §7.3).  The return is 1 — neither 0 nor -1 — because the
		 *    caller must be able to tell it from a fault.
		 *
		 * ⚠ AND THE LINE IS NOT WRITTEN HERE: `tastiera.c` already writes it, and
		 *   puts in it WHICH layout — the only thing useful to whoever reads the
		 *   log six hours later.  Writing it here too would mean counting
		 *   the same characters twice (`input.h`, 14 August 2026).
		 */
		return 1;
	}

	/* The modifiers first, the key last; released in reverse. */
	for (size_t i = 0; i < how_many; i++)
		if (send_key(in, codes[i], 1) < 0)
		{
			/* ⛔ Half way, what was pressed is released: a Shift
			 *    left down because of a send error is the same damage as the
			 *    Ctrl left down at detach. */
			for (size_t j = i; j > 0; j--)
				send_key(in, codes[j - 1], 0);
			return -1;
		}
	for (size_t i = how_many; i > 0; i--)
		send_key(in, codes[i - 1], 0);
	return 0;
}

int input_position(Input *in, uint16_t code, int pressed)
{
	if (!in)
		return -1;
	return send_key(in, code, pressed);
}

int input_release_all(Input *in)
{
	int amount = 0;
	int orphans = 0;

	if (!in)
		return -1;

	for (uint32_t c = 0; c < MAX_KEY; c++)
		if (bit_read(in->keys, c))
		{
			/* ⛔ The bit is switched off EVEN IF the send fails: if the device
			 *    is no longer there, that key is no longer ours to release, and
			 *    keeping it marked would make the bench count a release that cannot
			 *    happen.  ⚠ And only what LEFT is counted.
			 *
			 * ⛔⛔ And the ORPHAN is counted separately: `send_key()` has already switched off the
			 *     bit and lowered the count, so here NOTHING is touched — doing it
			 *     twice would bring the counter below zero, and an `unsigned`
			 *     below zero is four billion. */
			if (bit_read(in->orphan_keys, c))
			{
				(void) send_key(in, (uint16_t) c, 0);
				orphans++;
			}
			else if (send_key(in, (uint16_t) c, 0) == 0)
				amount++;
			else
			{
				bit_write(in->keys, c, FALSE);
				if (in->how_many_keys)
					in->how_many_keys--;
			}
		}
	for (uint32_t c = 0; c < MAX_BUTTON; c++)
		if (bit_read(in->buttons, c))
		{
			if (bit_read(in->orphan_buttons, c))
			{
				(void) send_button(in, (uint16_t) c, 0);
				orphans++;
			}
			else if (send_button(in, (uint16_t) c, 0) == 0)
				amount++;
			else
			{
				bit_write(in->buttons, c, FALSE);
				if (in->how_many_buttons)
					in->how_many_buttons--;
			}
		}

	/* ⛔ It is ALWAYS written, even when they are zero: "nothing was pressed" and
	 *    "I did not look" have the same look in the log, and this is the
	 *    rule with the highest damage/cost ratio in `RCP.md`.
	 *
	 * ⛔⛔ AND THE ORPHANS ARE DECLARED SEPARATELY, because they are another thing: they
	 *     are not "released", they are "not releasable".  Until 16 August 2026
	 *     they ended up inside `amount` and this line stated a number that
	 *     absolved. */
	registro_dice(AREA, "release at detach: %d keys and buttons (still marked: %u keys and "
	                    "%u buttons)%s",
	              amount, in->how_many_keys, in->how_many_buttons,
	              orphans ? " — ⛔ and see the line about the ORPHANS above" : "");
	if (orphans)
		registro_dice(AREA,
		              "⛔⛔ %d keys and buttons could NOT be released: they were pressed "
		              "on devices the compositor removed.  The seat still counts them down "
		              "and there they stay until the EIS channel drops",
		              orphans);
	return amount;
}

unsigned input_pressed(const Input *in)
{
	/* ⛔ The ORPHANS are not counted here, and it is intended: an orphan is NOT "the user
	 *    is holding something down", it is "the damage is already done".  Counting it
	 *    would forever prevent the wake-up on an already broken session — that is
	 *    precisely when the user is looking at a white page and waiting for a
	 *    frame.  ⚠ That case is handled by cure "C", which repairs it. */
	return in ? in->how_many_keys + in->how_many_buttons : 0;
}

void input_close(Input *in)
{
	if (!in)
		return;
	if (in->wlr)
	{
		close_wlr(in);
		return;
	}

	/* ⚠ A net, not the rule: the stitcher calls `input_release_all()` at
	 *   detach (it is in the contract).  If it has not done so, here the count is still
	 *   full and the log line says so — that is, the defect SHOWS. */
	if (in->how_many_keys || in->how_many_buttons)
	{
		registro_dice(AREA, "⛔ closing with %u keys and %u buttons STILL PRESSED: the stitcher did not "
		                    "call input_release_all()",
		              in->how_many_keys, in->how_many_buttons);
		input_release_all(in);
	}

	if (in->pointer)
		ei_device_unref(in->pointer);
	if (in->keyboard_dev)
		ei_device_unref(in->keyboard_dev);
	/* ⛔⛔ HERE WAS THE HOLE — until 25 August 2026 these lines were
	 *     `ei_disconnect(in->ei); ei_unref(in->ei);` without questions, and on an
	 *     EIS channel opened a few tens of milliseconds earlier they killed the
	 *     child with SIGSEGV **before the first frame**.
	 * ⭐ The cure is HERE and not in the three `unmount_stage()` of `figlio.c`: the hole
	 *    belongs to the channel, and whoever put it in the callers would leave it uncovered for the
	 *    fourth caller to be born.  The box above `detach_context()`
	 *    carries the mechanism, read in the library. */
	detach_context(in, "closing");
	g_clear_pointer(&in->kb_layout, keyboard_close);
	g_free(in->keymap_name);
	g_free(in->negotiated);
	g_free(in->reg_per);
	g_free(in);
}

/* ------------------------------------------------------------------ *
 *  ⭐ The bench window — it is NOT part of the contract, and that is intended
 *
 *  `CODER.md` §6: "make the code verifiable: every invariant must have
 *  a point where the reviewer can read whether it is respected or violated".  The
 *  bench `04-b24` reads from here the count of what is pressed and the number of
 *  replacements, instead of deducing them from the log.
 *
 *  ⛔ It is NOT in `input.h` on purpose: `input.h` belongs to the coordinator and is the
 *     PRODUCT's contract.  The bench declares it `extern` by itself.
 * ------------------------------------------------------------------ */
void input_count(const Input *in, unsigned *keys, unsigned *mouse_buttons, unsigned *pointer_replacements,
                 unsigned *keyboard_replacements, int *ready);

/* ⛔ The count of the ORPHANS, for bench `06-b33`: what stayed pressed
 *    on a device the compositor removed.  ⚠ It is in a separate function
 *    and not in the signature above because `04-b24` declares it `extern` with
 *    that signature: changing it under it would break a bench of another phase,
 *    which is exactly the kind of silent breakage this file fights. */
unsigned input_orphans(const Input *in);

unsigned input_orphans(const Input *in)
{
	return in ? in->how_many_orphans : 0;
}

void input_count(const Input *in, unsigned *keys, unsigned *mouse_buttons, unsigned *pointer_replacements,
                 unsigned *keyboard_replacements, int *ready)
{
	if (keys)
		*keys = in ? in->how_many_keys : 0;
	if (mouse_buttons)
		*mouse_buttons = in ? in->how_many_buttons : 0;
	if (pointer_replacements)
		*pointer_replacements = in ? in->pointer_replacements : 0;
	if (keyboard_replacements)
		*keyboard_replacements = in ? in->keyboard_replacements : 0;
	if (ready && in && in->wlr)
	{
		*ready = !wlr_input_dropped(in->wlr);
		return;
	}
	if (ready)
		*ready = in && in->pointer_active && in->region_known;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ WLROOTS — PHASE 13, INCREMENT 3: the same contract, another transport.
 *
 * ⛔ `libei` on wlroots does NOT exist (`STUDI.md` §xfce §7, `[✗]`).  The transport
 *    is `wlr_input.c` — Wayland's virtual keyboard and pointer — and here stays
 *    what on GNOME and KDE has already been paid for and measured: **the count** of
 *    `RCP.md` §11, the release at detach, the letters, the layout.
 *
 * ⭐ THE FORM: every public function hands over AT THE TOP and returns (like the
 *    clipboard with `clipboard_open_kde()`, like the capture with
 *    `capture_start_wlr()`).  ⛔ No GNOME or KDE branch has been
 *    transformed: the new branches sit on top and do not fall into them.
 *
 * ⚠ THE DIFFERENCES, counted, with respect to libei:
 *
 *   · **no replacements, no orphans**: the devices are OURS, the
 *     compositor does not destroy them for a geometry or keymap change.  ⇒
 *     `orphan_keys`/`orphan_buttons` stay at zero by construction;
 *   · **the layout does not go through GSettings**: it becomes the keymap of
 *     our keyboard, and labwc hands it to the applications with our keys
 *     (§7.4).  ⭐ It is §5-bis.7 in its most direct form: the shortcuts
 *     match because the keymap that interprets them is the one that translates them;
 *   · **a dropped wire is repaired by reattaching** (see `reattach_wlr`),
 *     and it is the analogue of cure "C": with the wire our pointer dies, and
 *     ⛔ `wlr_pointer_finish()` does NOT release the buttons (§7.2 n.5) — the
 *     release is brought by the new device.
 *
 * ⛔ And what stays uncovered, said: labwc's shortcuts apply
 *    to virtual keys too (§7.5, `match_keybinding(..., is_virtual)`) — an
 *    `Alt+F4` or a `Super` sent from the browser are taken by labwc, not by
 *    the application.  `[M]` 21 Sep 2026, laptop, headless labwc: `Alt+F4`
 *    from our channel CLOSES the witness's window, which sees the Alt and never
 *    the F4.  It is not a defect of this file: it is the desktop, and on XFCE it is also
 *    what the user expects.
 * ═══════════════════════════════════════════════════════════════════════════ */

/*
 * ⛔ The letters' `Keyboard` is opened from the SAME text the compositor
 *    received (`wlr_input_keymap()`): key positions are computed on the keymap
 *    with which they will be read back.  It is the rule of `read_keymap()`, and the log
 *    line is the same, so that whoever looks for «KEYMAP CHANGED» finds it on
 *    all three desktops.
 */
static void reopen_layout_wlr(Input *in)
{
	size_t measure = 0;
	const char *text = wlr_input_keymap(in->wlr, &measure);
	g_autofree char *mistake = NULL;
	g_autofree char *fingerprint = NULL;
	Keyboard *new_one;

	if (!text || measure == 0)
		return;
	fingerprint = g_strdup_printf("%zu bytes, fingerprint %08x", measure, (unsigned) g_str_hash(text));
	new_one = keyboard_open_from_keymap(text, measure, in->negotiated, &mistake);
	if (!new_one)
		registro_dice(AREA, "⚠ the virtual keyboard's keymap does not open for letters (%s): %s",
		              mistake ?: "no reason declared",
		              in->kb_layout ? "keeping the previous one" : "LETTERS stay off");
	else
	{
		g_clear_pointer(&in->kb_layout, keyboard_close);
		in->kb_layout = new_one;
	}
	if (g_strcmp0(fingerprint, in->keymap_name) != 0)
	{
		registro_dice(AREA, "KEYMAP CHANGED: %s (was: %s) → layout «%s», from %s (wlroots)",
		              fingerprint, in->keymap_name ?: "none",
		              in->kb_layout ? kbd_layout(in->kb_layout) : "none",
		              wlr_input_keymap_origin(in->wlr));
		g_free(in->keymap_name);
		in->keymap_name = g_steal_pointer(&fingerprint);
	}
}

Input *input_open_wlr(uint32_t canvas_w, uint32_t canvas_h, char **error)
{
	GError *mistake = NULL;
	WlrInput *w;
	Input *in;

	if (error)
		*error = NULL;
	if (canvas_w == 0 || canvas_h == 0)
	{
		if (error)
			*error = g_strdup_printf("degenerate canvas %ux%u: the absolute coordinates would have "
			                          "no range",
			                          canvas_w, canvas_h);
		return NULL;
	}
	w = wlr_input_open(&mistake);
	if (!w)
	{
		if (error)
			*error = g_strdup_printf("wlroots: %s", mistake ? mistake->message : "no reason");
		g_clear_error(&mistake);
		return NULL;
	}

	in = g_new0(Input, 1);
	in->wlr = w;
	in->canvas_w = canvas_w;
	in->canvas_h = canvas_h;
	in->open_us = g_get_monotonic_time();
	in->fd_socket = -1;
	reopen_layout_wlr(in);

	registro_dice(AREA,
	              "input channel open to the compositor (wlroots: virtual keyboard and "
	              "pointer), canvas %ux%u",
	              canvas_w, canvas_h);
	return in;
}

/* ⛔ The count is kept as in `send_key()`: AFTER sending, and only if it
 *    left — marking a key that did not leave would make the detach release
 *    something nobody pressed. */
static int send_key_wlr(Input *in, uint16_t code, int pressed)
{
	/* ⛔ Wire dropped ⇒ we try to reattach BEFORE saying -1.  It is not
	 *    zeal: `input_release_all()` on a failed send CLEARS the bit, and
	 *    a button cleared from the count is a button the reattach will no longer
	 *    release.  ⚠ With a floor of one second: within that second the
	 *    hole stays, and it is said. */
	if (wlr_input_dropped(in->wlr))
		reattach_wlr(in);
	if (wlr_input_key(in->wlr, code, pressed != 0) != 0)
		return -1;
	if ((pressed != 0) != bit_read(in->keys, code))
	{
		bit_write(in->keys, code, pressed != 0);
		if (pressed)
			in->how_many_keys++;
		else if (in->how_many_keys)
			in->how_many_keys--;
	}
	return 0;
}

static int send_button_wlr(Input *in, uint16_t code, int pressed)
{
	if (wlr_input_dropped(in->wlr))
		reattach_wlr(in); /* see `send_key_wlr()` */
	if (wlr_input_button(in->wlr, code, pressed != 0) != 0)
		return -1;
	if ((pressed != 0) != bit_read(in->buttons, code))
	{
		bit_write(in->buttons, code, pressed != 0);
		if (pressed)
			in->how_many_buttons++;
		else if (in->how_many_buttons)
			in->how_many_buttons--;
	}
	return 0;
}

/* The same as `input_letter()`, without libei's device. */
static int letter_wlr(Input *in, uint32_t character)
{
	uint16_t codes[KEYBOARD_MAX_POSITIONS];
	size_t how_many = 0;
	int outcome;

	if (!in->kb_layout)
	{
		/* ⛔ Phase 16 §12: the typed character is NOT written. */
		registro_dice(AREA, "⚠ LETTER not sent: no layout (the virtual keyboard's "
		                    "keymap did not open)");
		return -1;
	}
	if (wlr_input_dropped(in->wlr))
		return -1;

	outcome = keyboard_positions_for(in->kb_layout, character, codes, &how_many);
	if (outcome < 0)
		return -1;
	if (outcome == 0 || how_many == 0)
		return 1; /* ⛔ not producible: the line is written by `tastiera.c` */

	/* The modifiers first, the key last; released in reverse.
	 * ⭐ It is here that the modifiers of `wlr_input.c` do their job: the
	 *    pressed Shift updates OUR state, and the compositor receives it
	 *    as `modifiers` before the letter. */
	for (size_t i = 0; i < how_many; i++)
		if (send_key(in, codes[i], 1) < 0)
		{
			for (size_t j = i; j > 0; j--)
				send_key(in, codes[j - 1], 0);
			return -1;
		}
	for (size_t i = how_many; i > 0; i--)
		send_key(in, codes[i - 1], 0);
	return 0;
}

static int layout_wlr(Input *in, const char *name)
{
	g_autoptr(GError) mistake = NULL;

	/* ⛔ The question is "what is there now?", as in the GNOME branch: the
	 *    real keymap is the one the virtual keyboard carries, not the memory. */
	if (in->kb_layout && keyboard_is_this(in->kb_layout, name) == 1)
	{
		g_free(in->negotiated);
		in->negotiated = g_strdup(name);
		log_detail(AREA,
		                   "layout «%s»: the virtual keyboard ALREADY has it (verified on the "
		                   "keymap), not sending it again",
		                   name);
		return 0;
	}

	/* ⚠ The negotiated one is recorded BEFORE the outcome: if the wire has dropped, it is the
	 *   reattach that puts it back — and it must know which. */
	g_free(in->negotiated);
	in->negotiated = g_strdup(name);

	/* ⛔⛔ FIRST everything is released: the modifiers depend on the keymap, and a
	 *     Shift pressed with the old one and released with the new one stays down
	 *     in the compositor's state (`RCP.md` §11).  And the line is written
	 *     even with zero, as always. */
	input_release_all(in);

	if (wlr_input_keymap_from_name(in->wlr, name, &mistake) != 0)
	{
		registro_dice(AREA,
		              "⚠ DECLARED FALLBACK: layout «%s» was NOT sent to the "
		              "virtual keyboard (%s) — «%s» stays.  ⛔ The letters that one does not have "
		              "do NOT come out, and the SHORTCUTS go on its keys (RCP.md §7.3)",
		              name, mistake ? mistake->message : "no reason",
		              in->kb_layout ? kbd_layout(in->kb_layout) : "none");
		return -1;
	}
	reopen_layout_wlr(in);
	/* ⚠ "Sent", not "in force": that labwc passed it on to the applications
	 *   only a witness inside the session can say.  `[?]` Not measured. */
	registro_dice(AREA,
	              "layout «%s» SENT to the compositor as the virtual keyboard's "
	              "keymap — §5-bis.7 on wlroots, without touching the session's settings",
	              name);
	return 0;
}

/*
 * ⛔⛔ THE REATTACH — when the wire with labwc drops and the compositor is still there.
 *
 * Without it, a dropped wire means a desktop that can be SEEN and not CONTROLLED until
 * the next remount of the stage.  With it, it comes back by itself within a second.
 *
 * `[M]` 21 September 2026, ON THE LAPTOP (private headless labwc 0.8.3, the
 * same as Trixie; witness `banchi/06-b33-testimone.c`), cutting ONLY
 * our socket with `shutdown()` while `BTN_LEFT` and Shift were down:
 *   · ⭐ Shift is released by labwc by itself at the drop (the witness sees
 *     `TASTO 42 pressed 0`): the keyboard is fine without us (§7.2 n.5);
 *   · the button is released by NOBODY — but with our only pointer the
 *     seat loses the "pointer" capability (`POSTO_PUNTATORE mollato`), and after
 *     the reattach a fresh click arrives whole;
 *   · ⛔ and it arrives whole **even removing** the forced release below
 *     (grafted fault, same outcome).  ⇒ In THIS configuration — no
 *     other pointer in the seat, which is the headless remote session — the
 *     trap 5 at the drop does not bite.
 * ⚠ The forced release stays anyway, and it is `[?]`: it serves only if in the seat
 *   there is ANOTHER pointer keeping the capability alive (a real mouse), a case
 *   that has not been measured.  It costs one event; removing it would cost a
 *   diagnosis the day that case exists.
 *
 * ⚠ The floor is that of cure "C" (`HEALING_BACKSTOP_US`): if the compositor
 *   is really gone, the attempt costs one failed `connect()` per
 *   second, and the line comes out once only.
 */
static void reattach_wlr(Input *in)
{
	gint64 now = g_get_monotonic_time();
	g_autoptr(GError) mistake = NULL;
	WlrInput *fresh;
	unsigned mouse_buttons = 0, keys = 0;

	if (in->wlr_last_reattach_us && now - in->wlr_last_reattach_us < HEALING_BACKSTOP_US)
		return;
	in->wlr_last_reattach_us = now;

	fresh = wlr_input_open(&mistake);
	if (!fresh)
	{
		if (!in->wlr_reattach_failed_logged)
			registro_dice(AREA,
			              "⛔ wlroots: the input reattach does not succeed (%s) — retrying every "
			              "second, and this line does not repeat.  ⚠ Meanwhile the desktop can be "
			              "SEEN and not CONTROLLED",
			              mistake ? mistake->message : "no reason");
		in->wlr_reattach_failed_logged = TRUE;
		return;
	}

	/* The negotiated layout goes back to the previous one; without it, the one
	 * the session gave back at the reattach stays. */
	if (in->negotiated)
	{
		g_autoptr(GError) sb = NULL;

		if (wlr_input_keymap_from_name(fresh, in->negotiated, &sb) != 0)
			registro_dice(AREA, "⚠ at reattach layout «%s» is not put back (%s)",
			              in->negotiated, sb ? sb->message : "no reason");
	}

	for (uint32_t c = 0; c < MAX_BUTTON; c++)
		if (bit_read(in->buttons, c))
		{
			(void) wlr_input_force_release(fresh, (uint16_t) c);
			bit_write(in->buttons, c, FALSE);
			if (in->how_many_buttons)
				in->how_many_buttons--;
			mouse_buttons++;
		}
	for (uint32_t c = 0; c < MAX_KEY; c++)
		if (bit_read(in->keys, c))
		{
			bit_write(in->keys, c, FALSE);
			if (in->how_many_keys)
				in->how_many_keys--;
			keys++;
		}

	wlr_input_close(in->wlr);
	in->wlr = fresh;
	in->wlr_reattaches++;
	in->wlr_reattach_failed_logged = FALSE;
	reopen_layout_wlr(in);
	registro_dice(AREA,
	              "⭐ wlroots: input REATTACHED (n. %u).  %u buttons left down released by the "
	              "new device (`[?]` not measured that the seat accepts them), %u keys already "
	              "released by the compositor at the drop",
	              in->wlr_reattaches, mouse_buttons, keys);
}

static int run_wlr(Input *in)
{
	if (!wlr_input_dropped(in->wlr))
	{
		int n = wlr_input_run(in->wlr);

		if (n >= 0)
			return n;
	}
	reattach_wlr(in);
	return wlr_input_dropped(in->wlr) ? -1 : 0;
}

static void close_wlr(Input *in)
{
	/* ⚠ The same net as `input_close()`: the stitcher has already released; if it has not
	 *   done it, the line says so and we release here. */
	if (in->how_many_keys || in->how_many_buttons)
	{
		registro_dice(AREA, "⛔ closing with %u keys and %u buttons STILL PRESSED: the stitcher did not "
		                    "call input_release_all()",
		              in->how_many_keys, in->how_many_buttons);
		input_release_all(in);
	}
	wlr_input_close(in->wlr);
	g_clear_pointer(&in->kb_layout, keyboard_close);
	g_free(in->keymap_name);
	g_free(in->negotiated);
	g_free(in->reg_per);
	g_free(in);
}
