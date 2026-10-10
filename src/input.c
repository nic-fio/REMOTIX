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
 * Not here: `input_gira()` exists in the contract precisely so that the child's
 * loop calls this module at every round.  ⇒ **No lock, no
 * queue, no thread** — and no waiting inside the asynchronous loop
 * (`CODER.md` §4.4).
 *
 * ⛔ The price, and it must be told to the coordinator instead of discovered: **all** the
 *    functions of `input.h` must be called from the SAME thread that calls
 *    `input_gira()`.  `libei` is not reentrant, and two threads on a `struct ei`
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
 *   clears it.  Two bitmaps, and `input_rilascia_tutto()` empties them
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
 *   touching `dispositivo_tolto()`: the comment in there said* "at the replacement
 *   we release on the new device, which is the only place where the release
 *   arrives" *— and it was **false**.  The release on the new device arrives
 *   nowhere.*
 *
 * THE SCENE, measured: `BTN_LEFT` is held down, the client asks for an
 * `ADATTA_TELA`, Mutter recreates the absolute devices, and **then** it is released.
 * ⇒ `[M]` the witness inside the session (a real Wayland window) sees the
 *   `premuto:1` and **never sees** the `premuto:0`.  ⛔ And from that moment on
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
 *     `input_rilascia_tutto()`; the place to call it is `figlio.c:3964`,
 *     right **before** `cattura_ridimensiona(cat, tela_voluta_l,
 *     tela_voluta_a)`.  `[M]` Simulated from the wire — releasing before the
 *     replacement — the witness sees the release and the clicks after the replacement
 *     work again, all of them.
 *
 * ⚠ `figlio.c` does not belong to this link (sub-phase 6.3), so here the cure is
 *   MEASURED and WRITTEN, not applied.  ⛔ What falls to this file is
 *   the other half, and it is the one that was missing: **stop saying the release
 *   has left**.  Before, `manda_bottone()` returned 0 and
 *   `input_rilascia_tutto()` counted a release that happened, that is the log
 *   said "done" while the desktop stayed blocked — the worst form of
 *   `CODER.md` §4.6, *the green is not true*.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔⛔ AND THERE IS A SECOND DOOR — `[M]` 21 August 2026, bench
 *       `banchi/06-b33-risveglio.*`.  ⚠ THE CURE ABOVE **DOES NOT COVER IT**.
 *
 * ⛔ **The replacement does NOT depend on the canvas.**  `[M]` with `banchi/06-b33-risveglio`,
 *    still session and no `ADATTA_TELA`: **three `cattura_risveglia()`, three
 *    pointer replacements** (delta of `ricambi_puntatore` = 1, 1, 1) and **zero**
 *    calls to `cattura_ridimensiona()`.
 *
 * `[R]` And Mutter's line that explains it:
 *   `cattura_risveglia()` calls `pw_stream_update_params()` → the producer
 *   renegotiates → `meta_screen_cast_virtual_stream_src_enable()`
 *   (`meta-screen-cast-virtual-stream-src.c:283`) calls
 *   `meta_eis_viewport_notify_changed()` → `viewports-changed`
 *   (`meta-eis.c:319-323`) → `update_viewports()` (`meta-eis-client.c:1049-1062`)
 *   → `remove_viewport_devices()`.  ⇒ **The same chain as the resize,
 *   but without anyone having changed size.**
 *
 * ⛔ And `figlio.c:6365` calls `cattura_risveglia()` **precisely on a still
 *    desktop**, when the take is ZERO and a keyframe is owed — that is at the
 *    exact moment the user may be holding the mouse down on a
 *    scene that does not move.
 *
 * `[M]` The measurement, scene `06-b33-risveglio.sh tenuto` (21 Aug 2026, load
 * 1.58-10.7, Wayland witness inside the session):
 *   · `BTN_LEFT` down → **1** wake-up → the release **NEVER arrives** at the
 *     witness, and **neither does the next fresh click** ⇒ from there the desktop
 *     no longer takes a click;
 *   · ⭐ and the **keyboard keeps working** (Ctrl down+up and a fresh Enter
 *     all arrive): the keyboard is not a viewport device;
 *   · ⭐ the scene with `cattura_ridimensiona()` in place of the wake-up gives
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
 *   `ConnectToEIS` is needed, that is `mutter_eis_riattacca()`.  `[R]`
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
 *    box above `stacca_il_contesto()`. */
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
#define MAX_TASTO 0x300u
#define MAX_BOTTONE 0x300u
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
#define UNITA_PER_DELTA 12.0

struct input
{
	MutterSessione *sessione;
	/* ⭐ PHASE 12, INCREMENT 3 — on KDE the channel is given by KWin, and `sessione` is
	 *    NULL.  Only three things change: where the descriptor comes from (and the
	 *    healing), the region (KWin does not set the mapping-id: it is chosen by
	 *    geometry) and the wheel (`scroll_discrete`, see `UNITA_PER_DELTA`). */
	KwinSessione *kwin;
	struct ei *ei;

	/* The CANVAS of `RCP.md` §4.5, that is the range in which `rcp.c` has already
	 * verified that the incoming coordinates lie. */
	uint32_t tela_l, tela_a;

	/* ⛔ The ABSOLUTE device, and not "the first that can scroll": Mutter
	 *    offers two, and the relative one has NO regions — with the relative one the pointer
	 *    ends up wherever (`banchi/01-s7-rotella.c`, `[M]` 10 August 2026). */
	struct ei_device *puntatore;
	struct ei_device *tastiera_dev;
	gboolean puntatore_attivo;
	gboolean tastiera_attiva;
	uint32_t sequenza;

	/* The region the pointer moves on, in global logical coordinates. */
	gboolean regione_nota;
	gboolean regione_scalata_lamentata;
	double reg_x, reg_y, reg_l, reg_a;
	char *reg_per; /* «key», «geometry», «only»: how we chose it */

	Tastiera *disposizione;
	char *keymap_nome; /* the name libei publishes, to SEE a replacement */
	/* ⭐ What the CLIENT declared in `ATTACCA` (`RCP.md` §4.5), that is
	 *    the layout §5-bis.7 says to put into the session.  NULL
	 *    until someone has asked for it. */
	char *negoziata;
	/* ⭐ How many times the negotiated layout was REQUESTED from KWin on seeing
	 *    another keymap arrive (see "KWIN DID NOT HEAR" below). */
	int richieste_kwin;

	/* ⛔⛔ THE COUNT.  See the box at the top of the file. */
	uint8_t tasti[BIT_BYTE(MAX_TASTO)];
	uint8_t bottoni[BIT_BYTE(MAX_BOTTONE)];
	unsigned quanti_tasti;
	unsigned quanti_bottoni;

	/* ⛔⛔ THE ORPHANS — what was pressed on a device THAT IS NO LONGER
	 *     THERE.  See the box "THE RELEASE THAT REACHES NOBODY". */
	uint8_t tasti_orfani[BIT_BYTE(MAX_TASTO)];
	uint8_t bottoni_orfani[BIT_BYTE(MAX_BOTTONE)];
	unsigned quanti_orfani;

	/* The silent replacements, counted: the bench reads them instead of deducing them. */
	unsigned ricambi_puntatore;
	unsigned ricambi_tastiera;

	gboolean caduto; /* the compositor has closed the channel */

	/* ⛔⛔ CURE "C" — the reattach that heals the seat.  🔸 Derived, 21
	 *     August 2026, and the box at the top of the file says why there is no
	 *     other: from the client side the seat's count is unrecoverable,
	 *     and the only code that resets it is Mutter's `drop_device()`, which runs
	 *     only at the drop of the EIS channel. */
	gboolean guarigione_dovuta;
	unsigned guarigioni;
	gint64 ultima_guarigione_us;

	/* ⛔⛔ `libei`'s HANDSHAKE — cure D4, 25 August 2026.  The
	 *     box above `stacca_il_contesto()` names the instruction that crashed and
	 *     why these four fields are what is needed not to pass through it.
	 *
	 * ⭐ `stretta_fatta` is NOT a heuristic on the pointers: it is `EI_EVENT_CONNECT`,
	 *    that is the way `libei` has of saying "the server has approved".  The
	 *    devices arrive LATER, and looking at them would say "not yet" even
	 *    on a context that is by now mature. */
	gboolean stretta_fatta;
	gint64 aperto_us;  /* when the channel was opened (monotonic) */
	gint64 stretta_us; /* when the handshake arrived; 0 = never */
	/* ⛔ The descriptor we gave `libei`, kept aside for ONE case only:
	 *    the one in which the context must be **abandoned** instead of freed,
	 *    and then we must close the socket ourselves.  ⚠ In the normal case it is not
	 *    touched: it belongs to `libei`, and closing it in two places is a defect that
	 *    shows at a distance. */
	int fd_socket;

	/* ⭐ PHASE 13, INCREMENT 3 — on wlroots the transport is `wlr_input.c`, and
	 *    `ei`, `sessione`, `kwin`, `puntatore` and `tastiera_dev` stay NULL.
	 *    ⛔ Non-NULL means "this Input is wlroots's" for its WHOLE
	 *    life: after a drop the dead one is kept until the reattach
	 *    replaces it, so no function falls by mistake into the libei branches.
	 *    The "WLROOTS" box at the bottom of the file says the rest. */
	WlrInput *wlr;
	gint64 wlr_ultimo_riattacco_us;
	unsigned wlr_riattacchi;
	gboolean wlr_riattacco_fallito_detto;
	/* ⭐ PHASE 15, D-007 — the last absolute position sent (on the canvas of
	 *    then): `input_riporta_dentro()` puts it back after the shortcut, which
	 *    moves labwc's pointer onto the windows. */
	gboolean wlr_puntatore_noto;
	uint32_t wlr_px, wlr_py, wlr_pl, wlr_pa;
};

/* ⭐ PHASE 13 — the wlroots branches, written at the bottom of the file (box
 *    "WLROOTS").  ⛔ Each one sits at the TOP of the public function and returns: the
 *    GNOME and KDE path below it does not change by one line. */
static int manda_tasto_wlr(Input *in, uint16_t codice, int premuto);
static int manda_bottone_wlr(Input *in, uint16_t codice, int premuto);
static int gira_wlr(Input *in);
static int disposizione_wlr(Input *in, const char *nome);
static int lettera_wlr(Input *in, uint32_t carattere);
static void chiudi_wlr(Input *in);
static void riattacca_wlr(Input *in);

/* ⛔ The count of ABANDONED contexts — the PRICE of cure D4, and a price
 *    that is not counted is a price nobody discovers.  ⚠ It belongs to the process, not
 *    to the channel: the `Input` that paid it is already freed when the bench
 *    reads the number. */
static unsigned contesti_abbandonati;

/* ⭐ The window of bench `10-d4`.  ⛔ It is NOT in `input.h` on purpose, like
 *    `input_conto()` below: `input.h` is the PRODUCT's contract, and this
 *    is a witness.  The bench declares it `extern` by itself. */
unsigned input_abbandoni(void);

unsigned input_abbandoni(void)
{
	return contesti_abbandonati;
}

/* ⛔ The floor between two healings.  It is not prudence: a healing that
 *    failed in a repeatable way would run at every round of the child's loop,
 *    that is sixty D-Bus calls a second on an already broken channel.  ⚠ The
 *    flag is NOT switched off: it is retried at the round after the floor. */
#define GUARIGIONE_FONDO_US (1000 * 1000)

/* ------------------------------------------------------------------ *
 *  The bitmaps — "marked" and "sent" must not be able to diverge
 * ------------------------------------------------------------------ */
static gboolean bit_leggi(const uint8_t *mappa, uint32_t n)
{
	return (mappa[n / 8u] & (uint8_t) (1u << (n % 8u))) != 0;
}

static void bit_scrivi(uint8_t *mappa, uint32_t n, gboolean acceso)
{
	if (acceso)
		mappa[n / 8u] |= (uint8_t) (1u << (n % 8u));
	else
		mappa[n / 8u] &= (uint8_t) ~(1u << (n % 8u));
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
static void batti_cornice(Input *in, struct ei_device *dispositivo)
{
	ei_device_frame(dispositivo, ei_now(in->ei));
}

static int manda_tasto(Input *in, uint16_t codice, int premuto)
{
	if (codice >= MAX_TASTO)
	{
		registro_dice(AREA, "⚠ key code 0x%X beyond Mutter's maximum (0x%X): Mutter would "
		                    "discard it SILENTLY, so I refuse it myself and say so",
		              codice, MAX_TASTO - 1);
		return -1;
	}
	if (in->wlr)
		return manda_tasto_wlr(in, codice, premuto);
	if (!in->tastiera_dev || !in->tastiera_attiva)
		return -1;

	/* ⛔ As for buttons: a key pressed on a keyboard the
	 *    compositor destroyed (keymap change, `:762-781`) can no longer be
	 *    released — `handle_key` (`:638-645`) has the same guard as
	 *    `handle_button`.  It is said and -1 is returned, instead of writing "done". */
	if (!premuto && bit_leggi(in->tasti_orfani, codice))
	{
		bit_scrivi(in->tasti_orfani, codice, FALSE);
		if (in->quanti_orfani)
			in->quanti_orfani--;
		if (bit_leggi(in->tasti, codice))
		{
			bit_scrivi(in->tasti, codice, FALSE);
			if (in->quanti_tasti)
				in->quanti_tasti--;
		}
		/* ⛔ Phase 16 §12: the code only if it is a modifier — the other
		 *    keys are typed characters, and in the log they are called «key». */
		char quale[24] = "";
		if (registro_tasto_dicibile(codice))
			g_snprintf(quale, sizeof quale, " 0x%X", codice);
		registro_dice(AREA,
		              "⛔⛔ the release of key%s DOES NOT LEAVE: it was pressed on a keyboard that "
		              "the compositor has already removed (replacement n. %u), and `handle_key` silently "
		              "discards a release on the new device (`meta-eis-client.c:638-645`).  "
		              "⛔ A modifier that stays down makes the desktop unusable (`RCP.md` "
		              "§11): the cure is to release BEFORE the replacement",
		              quale, in->ricambi_tastiera);
		return -1;
	}

	ei_device_keyboard_key(in->tastiera_dev, codice, premuto != 0);
	batti_cornice(in, in->tastiera_dev);

	/* ⛔ The count is kept AFTER sending: marking a key that did not leave
	 *    would make the detach release something nobody pressed. */
	if ((premuto != 0) != bit_leggi(in->tasti, codice))
	{
		bit_scrivi(in->tasti, codice, premuto != 0);
		if (premuto)
			in->quanti_tasti++;
		else if (in->quanti_tasti)
			in->quanti_tasti--;
	}
	return 0;
}

static int manda_bottone(Input *in, uint16_t codice, int premuto)
{
	if (codice >= MAX_BOTTONE)
	{
		registro_dice(AREA, "⚠ button code 0x%X beyond the maximum: refused", codice);
		return -1;
	}
	if (in->wlr)
		return manda_bottone_wlr(in, codice, premuto);
	if (!in->puntatore || !in->puntatore_attivo)
		return -1;

	/*
	 * ⛔⛔ THE RELEASE OF AN ORPHAN DOES NOT LEAVE, AND IT IS SAID — see the box at
	 *     the top of the file.  ⚠ The count is CLEARED anyway: that button is no
	 *     longer ours to release, and keeping it marked would retry forever
	 *     something that cannot succeed.
	 *
	 * ⭐ And **-1** is returned, not 0: `rcp.c` counts it among the `input_rifiutati`,
	 *   which is the truth.  Returning 0 would mean writing "done" next to
	 *   a desktop left with the button down — and that is six hours of
	 *   diagnosis for whoever reads the log.
	 */
	if (!premuto && bit_leggi(in->bottoni_orfani, codice))
	{
		bit_scrivi(in->bottoni_orfani, codice, FALSE);
		if (in->quanti_orfani)
			in->quanti_orfani--;
		if (bit_leggi(in->bottoni, codice))
		{
			bit_scrivi(in->bottoni, codice, FALSE);
			if (in->quanti_bottoni)
				in->quanti_bottoni--;
		}
		registro_dice(AREA,
		              "⛔⛔ the release of button 0x%X DOES NOT LEAVE: it was pressed on a "
		              "device the compositor has already removed (replacement n. %u), and Mutter "
		              "silently discards a release on the new device "
		              "(`meta-eis-client.c:612-621`).  ⛔ The SEAT still counts it down "
		              "(`meta-seat-impl.c:899-908`) and from now on NO click arrives any more: the cure "
		              "is to release BEFORE asking for the resize — `figlio.c:3964`, "
		              "before `cattura_ridimensiona()`",
		              codice, in->ricambi_puntatore);
		return -1;
	}

	ei_device_button_button(in->puntatore, codice, premuto != 0);
	batti_cornice(in, in->puntatore);

	if ((premuto != 0) != bit_leggi(in->bottoni, codice))
	{
		bit_scrivi(in->bottoni, codice, premuto != 0);
		if (premuto)
			in->quanti_bottoni++;
		else if (in->quanti_bottoni)
			in->quanti_bottoni--;
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
static void leggi_regione(Input *in, struct ei_device *dispositivo)
{
	/* On KWin there is no key (`eis_region_set_mapping_id` is never
	 * called): geometry and "only" remain. */
	const char *chiave = in->kwin ? NULL : mutter_mapping_id_pubblicato(in->sessione);
	struct ei_region *per_chiave = NULL, *per_geometria = NULL, *unica = NULL;
	size_t quante = 0;
	struct ei_region *scelta = NULL;
	const char *per = NULL;

	in->regione_nota = FALSE;
	g_clear_pointer(&in->reg_per, g_free);

	for (size_t i = 0;; i++)
	{
		struct ei_region *regione = ei_device_get_region(dispositivo, i);
		const char *id;

		if (!regione)
			break;
		quante++;
		unica = regione;
		id = ei_region_get_mapping_id(regione);

		/* ⛔ The getters return `uint32_t`, not `double`: passing them to a `%.0f`
		 *    prints garbage that reads like a real diagnosis ("the region
		 *    is 0x0") while the region is 1920x1080.  `[M]` 10 August 2026. */
		registro_dettaglio(AREA, "region %zu: %u,%u %ux%u (mapping-id «%s»)", i,
		                   ei_region_get_x(regione), ei_region_get_y(regione),
		                   ei_region_get_width(regione), ei_region_get_height(regione),
		                   id ?: "absent");

		if (!per_chiave && chiave && id && g_strcmp0(id, chiave) == 0)
			per_chiave = regione;
		if (!per_geometria && in->tela_l && in->tela_a &&
		    ei_region_get_width(regione) == in->tela_l &&
		    ei_region_get_height(regione) == in->tela_a)
			per_geometria = regione;
	}

	if (per_chiave)
	{
		scelta = per_chiave;
		per = "key";
	}
	else if (per_geometria)
	{
		scelta = per_geometria;
		per = "geometry";
	}
	else if (quante == 1)
	{
		scelta = unica;
		per = "only";
	}

	if (!scelta)
	{
		registro_dice(AREA,
		              "⛔ NO region recognised among the %zu announced (key «%s», canvas "
		              "%ux%u): the pointer does NOT move, and I do not guess which one it is",
		              quante, chiave ?: "unknown", in->tela_l, in->tela_a);
		return;
	}

	in->reg_x = ei_region_get_x(scelta);
	in->reg_y = ei_region_get_y(scelta);
	in->reg_l = ei_region_get_width(scelta);
	in->reg_a = ei_region_get_height(scelta);
	in->regione_nota = in->reg_l > 0 && in->reg_a > 0;
	in->reg_per = g_strdup(per);

	registro_dice(AREA, "pointer region by %s: %.0f,%.0f %.0fx%.0f (of %zu, mapping-id «%s»)",
	              per, in->reg_x, in->reg_y, in->reg_l, in->reg_a, quante,
	              ei_region_get_mapping_id(scelta) ?: "absent");
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
 *    said "`tastiera_apri("it")`"; link A5 refused that piece and
 *    was right — `input.h`/`tastiera.h`, 14 August 2026.)*
 *
 * ⛔ And AT EVERY `DEVICE_ADDED`, not once at startup: `on_keymap_changed`
 *    (`meta-eis-client.c:761-781` `[R]`) does `eis_device_remove` +
 *    `add_device` with the new keymap, with the comment *"Changing the keymap
 *    means we have to remove our device and recreate it"*.  Whoever opens the
 *    layout once only stays with the old one after a change, and
 *    ⛔ **the letters come out different without anything giving an error**.
 */
static void leggi_keymap(Input *in, struct ei_device *dispositivo)
{
	struct ei_keymap *keymap = ei_device_keyboard_get_keymap(dispositivo);
	g_autofree char *testo = NULL;
	g_autofree char *impronta = NULL;
	g_autofree char *sbaglio = NULL;
	Tastiera *nuova;
	int fd;
	size_t misura;

	if (!keymap)
	{
		/* ⛔ The device exists, the keymap does not: `configure_keyboard` exits
		 *    AFTER having declared the keyboard capability if
		 *    `meta_backend_get_keymap` gives NULL (`:242-246` `[R]`).  It must be borne,
		 *    and it is declared instead of falling back silently. */
		registro_dice(AREA, "⚠ the keyboard device carries no keymap: LETTERS "
		                    "stay off (KEY POSITIONS do not)");
		g_clear_pointer(&in->disposizione, tastiera_chiudi);
		g_clear_pointer(&in->keymap_nome, g_free);
		return;
	}
	if (ei_keymap_get_type(keymap) != EI_KEYMAP_TYPE_XKB)
	{
		registro_dice(AREA, "⚠ keymap of unknown type (%d): ignored",
		              (int) ei_keymap_get_type(keymap));
		return;
	}

	fd = ei_keymap_get_fd(keymap);
	misura = ei_keymap_get_size(keymap);
	if (fd < 0 || misura == 0)
		return;

	/* ⛔ `pread` and not `read`: the keymap descriptor is shared, and
	 *    consuming its position would break it for whoever rereads it later. */
	testo = g_malloc0(misura + 1);
	if (pread(fd, testo, misura, 0) < 0)
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
	impronta = g_strdup_printf("%zu bytes, fingerprint %08x", misura, (unsigned) g_str_hash(testo));

	/*
	 * ⛔ The layout is REOPENED, not updated: `tastiera.h` has no
	 *    way to change the keymap under a live `Tastiera`, and that is right
	 *    — an object that changes identity under whoever holds it is the
	 *    defect we are measuring, not the cure.
	 *
	 * ⚠ And the old one is closed ONLY if the new one opens: if the new keymap
	 *   does not compile, staying with the previous one is better than staying without
	 *   — and the line says so, so the fallback is not silent.
	 */
	/*
	 * ⚠ `negoziata` is **NULL, and for now that is right** — but it must be said, because
	 *   it has a consequence that reads like a defect:
	 *
	 *   `tastiera.c` compares the layout declared by the client in
	 *   `ATTACCA` (`RCP.md` §4.5) with the session's real one, and if they do not
	 *   match it uses the SESSION's, writing `RIPIEGO DICHIARATO`.
	 *   ⛔ With `NULL` that comparison **is never made**, so that line will never
	 *   come out: whoever looked for it in the log would conclude "they always
	 *   match", which is a different thing from "I did not look".
	 *
	 * ⇒ The day the negotiated layout arrives here (today `input.h`
	 *   does not carry it: `input_apri` does not take it, and it is a choice of the
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
	 *    `RIPIEGO DICHIARATO` if they do not match — and with `NULL` that comparison
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
	nuova = tastiera_apri_da_keymap(testo, misura, in->negoziata, &sbaglio);
	if (!nuova)
	{
		registro_dice(AREA, "⚠ the keymap handed over by libei does not open (%s): %s",
		              sbaglio ?: "no reason declared",
		              in->disposizione ? "keeping the previous one" : "LETTERS stay off");
	}
	else
	{
		g_clear_pointer(&in->disposizione, tastiera_chiudi);
		in->disposizione = nuova;
	}

	if (g_strcmp0(impronta, in->keymap_nome) != 0)
	{
		registro_dice(AREA, "KEYMAP CHANGED: %s (was: %s) → layout «%s»", impronta,
		              in->keymap_nome ?: "none",
		              in->disposizione ? tastiera_disposizione(in->disposizione) : "none");
		g_free(in->keymap_nome);
		in->keymap_nome = g_steal_pointer(&impronta);
	}
	else
		registro_dettaglio(AREA, "keymap unchanged: %s", impronta);

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
	if (in->kwin && in->negoziata && in->disposizione &&
	    tastiera_e_questa(in->disposizione, in->negoziata) == 0 && in->richieste_kwin < 3)
	{
		g_autoptr(GError) sbaglio_kwin = NULL;

		in->richieste_kwin++;
		input_rilascia_tutto(in); /* KWin redoes the keyboard device */
		if (kwin_disposizione(in->negoziata, &sbaglio_kwin) == 0)
			registro_dice(AREA,
			              "⚠ KWin set «%s» and not the negotiated «%s»: REQUESTING it again (%d of 3)",
			              tastiera_disposizione(in->disposizione), in->negoziata,
			              in->richieste_kwin);
		else
			registro_dice(AREA, "⚠ KWin set «%s» and not «%s», and requesting it does not succeed: %s",
			              tastiera_disposizione(in->disposizione), in->negoziata,
			              sbaglio_kwin ? sbaglio_kwin->message : "no reason");
	}
}

/* ------------------------------------------------------------------ *
 *  libei's events
 * ------------------------------------------------------------------ */
static void dispositivo_aggiunto(Input *in, struct ei_device *dispositivo)
{
	gboolean assoluto = ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE);
	gboolean tasti = ei_device_has_capability(dispositivo, EI_DEVICE_CAP_KEYBOARD);

	registro_dettaglio(AREA, "device «%s»: absolute=%d scroll=%d buttons=%d keyboard=%d",
	                   ei_device_get_name(dispositivo) ?: "?", assoluto,
	                   ei_device_has_capability(dispositivo, EI_DEVICE_CAP_SCROLL),
	                   ei_device_has_capability(dispositivo, EI_DEVICE_CAP_BUTTON), tasti);

	/*
	 * ⛔ THE LAST ARRIVED IS ALWAYS TAKEN, and not "the first that will do".
	 *
	 * It is the difference between bearing a replacement and not bearing it: after a change
	 * of geometry Mutter sends `DEVICE_REMOVED` + `DEVICE_ADDED`, and whoever keeps
	 * the first stays attached to a dead object **that gives no error**.
	 */
	if (assoluto)
	{
		/* ⚠ The replacement is NOT counted here: `dispositivo_tolto` counts it, which
		 *   arrives first.  Counting it in both places would double it. */
		if (in->puntatore)
			ei_device_unref(in->puntatore);
		in->puntatore = ei_device_ref(dispositivo);
		in->puntatore_attivo = FALSE;
		leggi_regione(in, dispositivo);
	}
	if (tasti)
	{
		if (in->tastiera_dev)
			ei_device_unref(in->tastiera_dev);
		in->tastiera_dev = ei_device_ref(dispositivo);
		in->tastiera_attiva = FALSE;
		leggi_keymap(in, dispositivo);
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
static void segna_orfani(Input *in, const uint8_t *mappa, uint8_t *orfani, uint32_t massimo,
                         unsigned quanti, const char *cosa)
{
	if (!quanti)
		return;
	for (uint32_t c = 0; c < massimo; c++)
		if (bit_leggi(mappa, c) && !bit_leggi(orfani, c))
		{
			bit_scrivi(orfani, c, TRUE);
			in->quanti_orfani++;
		}
	registro_dice(AREA,
	              "⛔⛔ %u %s were PRESSED on the device the compositor has just removed: their "
	              "release will reach NOBODY, and the seat still counts them down.  ⇒ From "
	              "now on what passes through them is broken until the EIS channel drops.  The cure "
	              "is to release BEFORE asking for the resize (`figlio.c:3964`)",
	              quanti, cosa);

	/*
	 * ⛔⛔ AND HERE THE HEALING IS ASKED FOR — cure "C".  🔸 Derived, 21 Aug 2026.
	 *
	 * ⭐ This is the exact instant the damage happens, and it is the only
	 *    place in the program that knows it.  ⚠ We do not heal NOW: we are inside
	 *    `ei_dispatch()`, and destroying the `libei` context while it is
	 *    delivering events to us is a defect that gives no error.  ⇒ It is marked, and
	 *    `input_gira()` heals when the queue is empty.
	 *
	 * ⛔ And it is marked for ANY door: the resize, the wake-up
	 *    of the capture (§7.1), a Mutter `monitors-changed`, a keymap
	 *    change.  ⚠ It is the reason cure "C" exists next to "A":
	 *    "A" closes the door we control, "C" repairs those we do not
	 *    control — and `meta_eis_viewport_notify_changed()` entered
	 *    GNOME 48.5, that is it is NEW: others will come.
	 */
	in->guarigione_dovuta = TRUE;
}

static void dispositivo_tolto(Input *in, struct ei_device *dispositivo)
{
	if (in->puntatore == dispositivo)
	{
		/* ⛔ And the count of what was pressed is NOT reset: the device has
		 *    gone, the user's buttons have not.  ⚠ But we NO LONGER hope to
		 *    release them on the new device — `[M]` 16 August 2026, it does not
		 *    arrive: they become ORPHANS, and it is said. */
		segna_orfani(in, in->bottoni, in->bottoni_orfani, MAX_BOTTONE, in->quanti_bottoni,
		             "buttons");
		ei_device_unref(in->puntatore);
		in->puntatore = NULL;
		in->puntatore_attivo = FALSE;
		in->regione_nota = FALSE;
		/* ⛔ THE REPLACEMENT IS COUNTED HERE, NOT ONLY ON ADDITION — `[M]` 14 August
		 *    2026, and the bench paid for it: Mutter sends `DEVICE_REMOVED` **and
		 *    then** `DEVICE_ADDED`, so at the moment of the addition the old one
		 *    is already NULL and a counter that looks only there stays at **zero**.
		 *    ⚠ The bench printed "the replacement was NOT reproduced" while the
		 *    witness saw the seat lose keyboard and pointer: an
		 *    instrument blind precisely in the case it must see (`CODER.md` §3.4). */
		in->ricambi_puntatore++;
		registro_dice(AREA, "the pointer was REMOVED by the compositor (replacement n. %u)",
		              in->ricambi_puntatore);
	}
	if (in->tastiera_dev == dispositivo)
	{
		/* ⚠ At a GEOMETRY change the keyboard is not replaced — `[R]`
		 *   `remove_viewport_devices` looks only at TOUCH and POINTER_ABSOLUTE
		 *   (`meta-eis-client.c:197-206`), and `[M]` 16 August 2026: **zero**
		 *   keyboard replacements out of fifteen of the pointer.  ⛔ But at a
		 *   KEYMAP change yes, `on_keymap_changed` (`:762-781`) destroys and
		 *   recreates it — and there the orphan defect has the same form.  It is
		 *   sub-phase 6.2: here it is marked, so when it measures it the count
		 *   is already there. */
		segna_orfani(in, in->tasti, in->tasti_orfani, MAX_TASTO, in->quanti_tasti, "keys");
		ei_device_unref(in->tastiera_dev);
		in->tastiera_dev = NULL;
		in->tastiera_attiva = FALSE;
		in->ricambi_tastiera++;
		registro_dice(AREA, "the keyboard was REMOVED by the compositor (replacement n. %u)",
		              in->ricambi_tastiera);
	}
}

static void tratta_evento(Input *in, struct ei_event *evento)
{
	enum ei_event_type tipo = ei_event_get_type(evento);
	struct ei_device *dispositivo = ei_event_get_device(evento);

	switch (tipo)
	{
		case EI_EVENT_CONNECT:
			/*
			 * ⛔⛔ THIS IS THE LINE THAT MAKES THE CLOSING SAFE — cure D4, 25
			 *     August 2026.  The box above `stacca_il_contesto()` names the
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
			in->stretta_fatta = TRUE;
			in->stretta_us = g_get_monotonic_time();
			registro_dettaglio(AREA,
			                   "libei's handshake has ARRIVED after %.1f ms: from now on the "
			                   "channel can be closed the normal way",
			                   (double) (in->stretta_us - in->aperto_us) / 1000.0);
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
			ei_seat_bind_capabilities(ei_event_get_seat(evento), EI_DEVICE_CAP_POINTER,
			                          EI_DEVICE_CAP_POINTER_ABSOLUTE, EI_DEVICE_CAP_BUTTON,
			                          EI_DEVICE_CAP_SCROLL, EI_DEVICE_CAP_KEYBOARD, NULL);
			registro_dettaglio(AREA, "seat «%s»: capabilities requested",
			                   ei_seat_get_name(ei_event_get_seat(evento)) ?: "?");
			break;

		case EI_EVENT_DEVICE_ADDED:
			dispositivo_aggiunto(in, dispositivo);
			break;

		case EI_EVENT_DEVICE_REMOVED:
			dispositivo_tolto(in, dispositivo);
			break;

		case EI_EVENT_DEVICE_RESUMED:
			ei_device_start_emulating(dispositivo, ++in->sequenza);
			if (dispositivo == in->puntatore)
			{
				in->puntatore_attivo = TRUE;
				/* ⛔ And it is reread HERE TOO: between `DEVICE_ADDED` and the resume the
				 *    compositor may have redone the viewports. */
				leggi_regione(in, dispositivo);
			}
			if (dispositivo == in->tastiera_dev)
				in->tastiera_attiva = TRUE;
			registro_dettaglio(AREA, "device «%s» ready (sequence %u)",
			                   ei_device_get_name(dispositivo) ?: "?", in->sequenza);
			break;

		case EI_EVENT_DEVICE_PAUSED:
			if (dispositivo == in->puntatore)
				in->puntatore_attivo = FALSE;
			if (dispositivo == in->tastiera_dev)
				in->tastiera_attiva = FALSE;
			break;

		case EI_EVENT_DISCONNECT:
			registro_dice(AREA, "⛔ the compositor CLOSED the input channel");
			in->caduto = TRUE;
			break;

		default:
			break;
	}
}

/* ------------------------------------------------------------------ *
 *  The contract
 * ------------------------------------------------------------------ */
static Input *apri(MutterSessione *sessione, KwinSessione *kwin, uint32_t tela_l,
                   uint32_t tela_a, char **errore)
{
	Input *in;
	int fd;

	if (errore)
		*errore = NULL;
	if (!sessione && !kwin)
	{
		if (errore)
			*errore = g_strdup("no Mutter session: the input channel has nobody to talk to");
		return NULL;
	}
	if (tela_l == 0 || tela_a == 0)
	{
		if (errore)
			*errore = g_strdup_printf("degenerate canvas %ux%u: the absolute coordinates would have "
			                          "no range",
			                          tela_l, tela_a);
		return NULL;
	}

	if (kwin)
	{
		GError *sbaglio = NULL;

		fd = kwin_eis_fd(kwin, &sbaglio);
		if (fd < 0)
		{
			if (errore)
				*errore = g_strdup_printf("KWin did not grant the input channel "
				                          "(connectToEIS): %s",
				                          sbaglio ? sbaglio->message : "no reason");
			g_clear_error(&sbaglio);
			return NULL;
		}
	}
	else
		fd = mutter_eis_fd(sessione);
	if (fd < 0)
	{
		/* ⛔ And we say WHY, not "it does not open": the `mutter.c` line that
		 *    declares the refusal of `ConnectToEIS` is already in the log, and
		 *    this one recalls it instead of adding a second mystery. */
		if (errore)
			*errore = g_strdup("ConnectToEIS gave no descriptor (the log of the "
			                   "«cattura» area says why): no input can reach the desktop");
		return NULL;
	}

	in = g_new0(Input, 1);
	in->sessione = sessione;
	in->kwin = kwin;
	in->tela_l = tela_l;
	in->tela_a = tela_a;
	/* ⛔ Cure D4: the instant of the opening is marked HERE, because it is the only way
	 *    to say how long the dangerous window lasted when it closes. */
	in->aperto_us = g_get_monotonic_time();
	in->fd_socket = -1;

	in->ei = ei_new_sender(in);
	if (!in->ei)
	{
		if (errore)
			*errore = g_strdup("libei context not created");
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
		if (errore)
			*errore = g_strdup("ConnectToEIS's descriptor was not accepted by libei");
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
	 * `leggi_keymap`, at the first `DEVICE_ADDED` and at every replacement.  Until
	 * that moment `input_lettera` answers -1, and says so.
	 */
	registro_dice(AREA, "input channel open to the compositor (libei), canvas %ux%u", tela_l,
	              tela_a);
	return in;
}

/*
 * ⛔⭐ THE DESCRIPTOR FOR THE CHILD'S `poll()` — see `input.h`.
 *
 * ⚠ It is a descriptor to WATCH, not to read: whoever puts it in the `poll()`
 *   does not `read()` on it.  When it becomes readable it calls `input_gira()`,
 *   which is the only place `ei_dispatch()` can be — `libei` is not
 *   reentrant, and a byte taken by hand from under the library's feet would be
 *   a defect that gives no error.
 *
 * ⛔ -1 means "nothing to put in the poll", not "error".
 */
Input *input_apri(void *sessione_mutter, uint32_t tela_l, uint32_t tela_a, char **errore)
{
	return apri(sessione_mutter, NULL, tela_l, tela_a, errore);
}

Input *input_apri_kwin(KwinSessione *kwin, uint32_t tela_l, uint32_t tela_a, char **errore)
{
	if (!kwin)
	{
		if (errore)
			*errore = g_strdup("no KWin stage: the input channel has nobody to talk to");
		return NULL;
	}
	return apri(NULL, kwin, tela_l, tela_a, errore);
}

int input_descrittore(Input *in)
{
	/* ⭐ wlroots: the descriptor of the Wayland wire, and -1 if it has dropped. */
	if (in && in->wlr)
		return wlr_input_descrittore(in->wlr);
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
 *       #2  input_chiudi (…)          at input.c
 *       #3  smonta_il_palco (…)       at figlio.c
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
 *     "the server has approved" (`libei.h`).  ⛔ NOT the pointers `puntatore` /
 *     `tastiera_dev` / `regione_nota` read in the core: those are **symptoms**,
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
static void stacca_il_contesto(Input *in, const char *chi)
{
	double vissuto_ms;
	int epoll_di_libei;

	if (!in || !in->ei)
		return;

	vissuto_ms = (double) (g_get_monotonic_time() - in->aperto_us) / 1000.0;

	if (in->stretta_fatta)
	{
		/* ⭐ THE REAL CLOSE — this line is the usual one, and must
		 *    stay: it is `ei_disconnect()` that sends the protocol detach,
		 *    and it is that message (not the closing of the socket) that makes
		 *    `drop_device()` run in Mutter.  `[M]` faults `RG3`/`RG4`, 21 Aug 2026. */
		ei_disconnect(in->ei);
		ei_unref(in->ei);
		in->ei = NULL;
		in->fd_socket = -1; /* `libei` closed it together with the context */
		registro_dettaglio(AREA,
		                   "input channel detached by «%s»: handshake arrived after %.1f ms, "
		                   "lived %.1f ms, REAL close (ei_disconnect + ei_unref)",
		                   chi, (double) (in->stretta_us - in->aperto_us) / 1000.0, vissuto_ms);
		return;
	}

	/* ⛔⛔ THE DANGEROUS WINDOW — and it is declared with `registro_dice`, not with
	 *     `registro_dettaglio`: it is a rare event with a price, and whoever reads the
	 *     log after a stage that died young must find it written. */
	epoll_di_libei = ei_get_fd(in->ei);
	contesti_abbandonati++;
	registro_dice(AREA,
	              "⛔ input channel ABANDONED by «%s» after %.1f ms: libei's handshake "
	              "had never arrived, and disconnecting (or freeing) such a context "
	              "makes the library crash.  ⇒ The descriptors are closed and the context is lost "
	              "(abandonments so far: %u).  ⚠ No virtual device is left hanging: at "
	              "this point none had been born yet",
	              chi, vissuto_ms, contesti_abbandonati);

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
 * ⚠ IT IS CALLED ONLY FROM `input_gira()`, with an empty queue: destroying the `libei`
 *   context inside `ei_dispatch()` is a defect that gives no error.
 *
 * ⛔ THE PRICE, DECLARED: **the drag in progress is cut** —
 *    `drop_device()` sends a clean release for everything that was pressed.
 *    ⭐ But that drag **was already dead** (`[M]` 21 Aug 2026, bench
 *    `06-b33-risveglio.sh tenuto`: after the replacement the release does not arrive and
 *    neither does the next click).  ⇒ A broken thing is cut and made to
 *    start again, which is a net gain.
 *    ⚠ It also costs a D-Bus round and the recreation of the devices, and in
 *      that window no input arrives.
 *
 * ⛔ What is NOT lost: the `RemoteDesktop` session, the virtual monitor and
 *    the PipeWire stream.  `[R]` `meta-remote-desktop-session.c:1943-1969`: the
 *    second `ConnectToEIS` reuses `session->eis` and adds a client.
 */
static void guarisci(Input *in)
{
	g_autoptr(GError) sbaglio = NULL;
	gint64 adesso = g_get_monotonic_time();
	int fd, nuovo;

	if (in->ultima_guarigione_us && adesso - in->ultima_guarigione_us < GUARIGIONE_FONDO_US)
		return; /* ⚠ and the flag STAYS on: retried after the floor */
	in->ultima_guarigione_us = adesso;

	registro_dice(AREA,
	              "⭐⭐ HEALING (n. %u): redoing the EIS channel.  The seat still counts down "
	              "%u orphan keys and buttons, and from the client side it is NOT recovered "
	              "(`meta-eis-client.c:612-621` swallows the release on the new device).  "
	              "⛔ The price: the drag in progress is CUT — but it was already dead",
	              in->guarigioni + 1, in->quanti_orfani);

	/* ⛔ The devices are let go BEFORE the context: they hold a reference to
	 *    `struct ei`, and a context freed under a live device is a
	 *    defect that shows elsewhere. */
	if (in->puntatore)
		ei_device_unref(in->puntatore);
	if (in->tastiera_dev)
		ei_device_unref(in->tastiera_dev);
	in->puntatore = NULL;
	in->tastiera_dev = NULL;
	in->puntatore_attivo = FALSE;
	in->tastiera_attiva = FALSE;
	in->regione_nota = FALSE;
	in->regione_scalata_lamentata = FALSE;
	g_clear_pointer(&in->reg_per, g_free);
	g_clear_pointer(&in->keymap_nome, g_free);

	/* ⛔ Cure D4: the same door as `input_chiudi()`, and not a copy.  ⚠ Here
	 *    the handshake has almost always arrived (we heal after a device
	 *    replacement, which necessarily comes after the handshake), but "almost always"
	 *    is exactly the way this hole was born. */
	stacca_il_contesto(in, "healing");

	/* ⛔ AND THE DETACH HAS ALREADY BEEN SENT BY `ei_disconnect()` above — `[M]` 21
	 *    Aug 2026, faults `RG3`/`RG4`: it is that protocol message that makes
	 *    `drop_device()` run in Mutter, not the closing of the socket.
	 * ⇒ What is needed from `mutter.c` is a NEW descriptor: after the detach
	 *   the one put aside is dead, and a `ConnectToEIS` wants the bus and the
	 *   session path, which this file does not have (and must not have). */
	nuovo = in->kwin ? kwin_eis_riattacca(in->kwin, &sbaglio)
	                 : mutter_eis_riattacca(in->sessione, &sbaglio);
	if (nuovo < 0)
	{
		registro_dice(AREA,
		              "⛔⛔ the healing did NOT succeed (%s): the input channel is gone. "
		              "⚠ The seat is unblocked anyway — the closing already did it — but from "
		              "now on the user WATCHES and does not control",
		              sbaglio ? sbaglio->message : "no reason declared");
		in->caduto = TRUE;
		in->guarigione_dovuta = FALSE;
		return;
	}

	/* ⛔ Cure D4: the NEW channel starts from scratch — handshake not yet arrived,
	 *    and the clock of the dangerous window reset.  ⚠ Forgetting it
	 *    would make a connection just born look mature, that is it would put back
	 *    the hole at the first teardown after a healing. */
	in->stretta_fatta = FALSE;
	in->stretta_us = 0;
	in->aperto_us = g_get_monotonic_time();
	in->fd_socket = -1;

	in->ei = ei_new_sender(in);
	if (!in->ei)
	{
		registro_dice(AREA, "⛔⛔ libei context not recreated: the input channel is over");
		in->caduto = TRUE;
		in->guarigione_dovuta = FALSE;
		return;
	}
	ei_configure_name(in->ei, "remotix");
	/* ⛔ A `dup`, as in `input_apri()`: `ei_setup_backend_fd` takes ownership of it
	 *    and closing it in two places is a defect that shows at a distance. */
	fd = dup(nuovo);
	if (fd < 0 || ei_setup_backend_fd(in->ei, fd) != 0)
	{
		if (fd >= 0)
			close(fd);
		ei_unref(in->ei);
		in->ei = NULL;
		registro_dice(AREA, "⛔⛔ the new descriptor was not accepted by libei: the input "
		                    "channel is over");
		in->caduto = TRUE;
		in->guarigione_dovuta = FALSE;
		return;
	}
	in->fd_socket = fd; /* ⛔ Cure D4, as in `input_apri()`: needed if it must be abandoned */

	/*
	 * ⛔⛔ AND THE COUNT IS RESET, ORPHANS INCLUDED, because now it is TRUE:
	 *     `drop_device()` has just sent the seat the release of everything
	 *     that was pressed.  ⚠ Keeping them marked would make the detach
	 *     release things nobody holds down, and would keep on forever the
	 *     «NON PARTE» line on a channel that instead works.
	 */
	memset(in->tasti, 0, sizeof in->tasti);
	memset(in->bottoni, 0, sizeof in->bottoni);
	memset(in->tasti_orfani, 0, sizeof in->tasti_orfani);
	memset(in->bottoni_orfani, 0, sizeof in->bottoni_orfani);
	in->quanti_tasti = 0;
	in->quanti_bottoni = 0;
	in->quanti_orfani = 0;
	in->sequenza = 0;

	in->guarigioni++;
	in->guarigione_dovuta = FALSE;
	registro_dice(AREA,
	              "⭐⭐ EIS channel REDONE (healing n. %u): the devices are reborn and the seat's "
	              "count is back to zero.  ⚠ Keymap and region are reread at the next "
	              "`DEVICE_ADDED`, as always.  ⛔ The session, the monitor and the stream were NOT "
	              "touched",
	              in->guarigioni);
}

int input_gira(Input *in)
{
	struct ei_event *evento;
	int quanti = 0;

	if (!in)
		return -1;
	if (in->wlr)
		return gira_wlr(in);
	if (in->caduto)
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
	 *   fails, and falls in the same place.  ⛔ The cure of `input_chiudi()` does not
	 *   reach here: here one does not even get to `input_chiudi()`.
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
	if (!in->stretta_fatta && in->ei && in->fd_socket >= 0)
	{
		struct pollfd sonda;

		sonda.fd = in->fd_socket;
		sonda.events = 0;
		sonda.revents = 0;
		if (poll(&sonda, 1, 0) > 0 && (sonda.revents & (POLLHUP | POLLERR | POLLNVAL)))
		{
			registro_dice(AREA,
			              "⛔⛔ the compositor closed the EIS channel BEFORE the "
			              "handshake (after %.1f ms): NOT dispatching it, because libei would crash "
			              "inside its own ei_disconnect().  ⚠ From now on the user WATCHES "
			              "and does not control, and the stage is torn down the normal way",
			              (double) (g_get_monotonic_time() - in->aperto_us) / 1000.0);
			stacca_il_contesto(in, "drop before the handshake");
			in->caduto = TRUE;
			return -1;
		}
	}

	ei_dispatch(in->ei);
	while ((evento = ei_get_event(in->ei)) != NULL)
	{
		tratta_evento(in, evento);
		ei_event_unref(evento);
		quanti++;
	}
	/* ⛔ The healing is HERE and not inside `tratta_evento`: with an empty queue, and
	 *    after `dispositivo_tolto()` has already marked the orphans. */
	if (in->guarigione_dovuta && !in->caduto)
		guarisci(in);
	return in->caduto ? -1 : quanti;
}

int input_puntatore(Input *in, uint32_t x, uint32_t y)
{
	double fx, fy;

	/* ⭐ wlroots: the protocol is NORMALISED on the extent it is given
	 *    (the canvas), and the output is the one the pointer is bound to — no
	 *    region to look for.  ⛔ And no transformation: the coordinates go
	 *    as they arrive, with the canvas as yardstick. */
	if (in && in->wlr) {
		in->wlr_puntatore_noto = TRUE;
		in->wlr_px = x;
		in->wlr_py = y;
		in->wlr_pl = in->tela_l;
		in->wlr_pa = in->tela_a;
		return wlr_input_assoluto(in->wlr, x, y, in->tela_l, in->tela_a);
	}
	if (!in || !in->puntatore || !in->puntatore_attivo)
		return -1;
	if (!in->regione_nota)
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
	if (in->reg_l == (double) in->tela_l && in->reg_a == (double) in->tela_a)
	{
		fx = in->reg_x + (double) x;
		fy = in->reg_y + (double) y;
	}
	else
	{
		if (!in->regione_scalata_lamentata)
		{
			in->regione_scalata_lamentata = TRUE;
			registro_dice(AREA,
			              "⚠ the region (%.0fx%.0f) is NOT as large as the canvas (%ux%u): scaling the "
			              "coordinates, and it is a decision this module should not "
			              "take — RCP.md §4.5, the granted canvas",
			              in->reg_l, in->reg_a, in->tela_l, in->tela_a);
		}
		fx = in->reg_x + (double) x * in->reg_l / (double) in->tela_l;
		fy = in->reg_y + (double) y * in->reg_a / (double) in->tela_a;
	}

	ei_device_pointer_motion_absolute(in->puntatore, fx, fy);
	batti_cornice(in, in->puntatore);
	return 0;
}

/*
 * ⛔ THE CANVAS CHANGES ON THE FLY — `TELA(ADATTATA)` of `RCP.md` §7.1.
 *
 * The defect this function exists not to have: `rcp.c` saturates the
 * coordinates on the NEW canvas while `input.c` stays mapped on the OLD one.
 * Two sides with two truths, and ⛔ **no error anywhere** — the same
 * form phase 3 already paid for with the codec string.
 *
 * ⛔ And the region is REREAD at once, instead of waiting for the next
 *    `DEVICE_ADDED`: the moment of the `TELA` is not the moment of the `DEVICE_ADDED`,
 *    and between the two there would be a window in which the pointer goes elsewhere.
 *
 * ⚠ Whoever changes the canvas, though, **is not whoever changes the monitor**: if
 *   `libei`'s region stays as large as it was, this function will find it different from the
 *   canvas and will say so (see `input_puntatore`).  It is open question n.1 of
 *   phase 4 — who decides the size of the monitor (`RCP.md` §4.5) — and this
 *   module DECLARES it instead of answering it on its own.
 */
int input_ritela(Input *in, uint32_t tela_l, uint32_t tela_a)
{
	if (!in)
		return -1;
	if (tela_l == 0 || tela_a == 0)
	{
		registro_dice(AREA, "⛔ degenerate canvas %ux%u refused: keeping %ux%u", tela_l, tela_a,
		              in->tela_l, in->tela_a);
		return -1;
	}
	if (tela_l == in->tela_l && tela_a == in->tela_a)
		return 0;

	registro_dice(AREA, "the canvas changes: %ux%u → %ux%u", in->tela_l, in->tela_a, tela_l, tela_a);
	in->tela_l = tela_l;
	in->tela_a = tela_a;
	/* ⛔ And the complaint about the scale is re-armed: the previous region may have been
	 *    as large as the previous canvas, and no longer be. */
	in->regione_scalata_lamentata = FALSE;
	if (in->puntatore)
		leggi_regione(in, in->puntatore);
	return 0;
}

/*
 * ⭐ PHASE 15, D-007 — `input.h`, and the why in `sessione.h` (the box of
 *    `SESSIONE_LABWC_TASTIERA`).
 *
 * ⛔ The codes are evdev (`linux/input-event-codes.h`), and the keys are the
 *    LEFT ones: in every pc105 layout they are Super_L, Control_L, Alt_L and
 *    Shift_L, while the RIGHT Alt is AltGr (ISO_Level3_Shift) in half of Europe.
 *    F12 stays F12 even with Shift.  ⚠ `SESSIONE_LABWC_TASTO` and these
 *    five numbers say the same thing: if one changes, the others change.
 */
#define RIPORTA_SUPER 125 /* KEY_LEFTMETA */
#define RIPORTA_CTRL 29   /* KEY_LEFTCTRL */
#define RIPORTA_ALT 56    /* KEY_LEFTALT */
#define RIPORTA_MAIUSC 42 /* KEY_LEFTSHIFT */
#define RIPORTA_F12 88    /* KEY_F12 */

int input_riporta_dentro(Input *in)
{
	static const uint16_t combinazione[] = { RIPORTA_SUPER, RIPORTA_CTRL, RIPORTA_ALT,
		                                 RIPORTA_MAIUSC, RIPORTA_F12 };
	const size_t quanti = G_N_ELEMENTS(combinazione);
	size_t giu = 0;
	int esito = 1;

	/* GNOME and KDE: the compositor brings the windows back inside by itself. */
	if (!in || !in->wlr)
		return 0;

	/* ⛔ We start from an EMPTY keyboard: a modifier left down would make
	 *    a combination labwc does not recognise (or, worse, another one). */
	input_rilascia_tutto(in);
	for (giu = 0; giu < quanti; giu++)
		if (manda_tasto(in, combinazione[giu], 1) < 0) {
			esito = -1;
			break;
		}
	/* ⛔ And EVERYTHING that left is released in reverse, even if the
	 *    combination stayed half way. */
	while (giu > 0)
		manda_tasto(in, combinazione[--giu], 0);

	/* The pointer goes back where the user had it, on the canvas of NOW. */
	if (in->wlr_puntatore_noto && in->wlr_pl && in->wlr_pa && in->tela_l && in->tela_a) {
		uint32_t x = (uint32_t)((uint64_t)in->wlr_px * in->tela_l / in->wlr_pl);
		uint32_t y = (uint32_t)((uint64_t)in->wlr_py * in->tela_a / in->wlr_pa);

		if (x >= in->tela_l)
			x = in->tela_l - 1;
		if (y >= in->tela_a)
			y = in->tela_a - 1;
		input_puntatore(in, x, y);
	}

	if (esito < 0)
		registro_dice(AREA,
		              "⛔ D-007: the «bring back inside» shortcut (%s) did NOT leave: "
		              "large windows may stay partly outside the screen "
		              "%ux%u",
		              SESSIONE_LABWC_TASTO, in->tela_l, in->tela_a);
	else
		registro_dice(AREA,
		              "⭐ D-007: typed the «bring back inside» shortcut (%s) — labwc "
		              "brings the windows back inside the screen %ux%u",
		              SESSIONE_LABWC_TASTO, in->tela_l, in->tela_a);
	return esito;
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
 *   got it is that of `leggi_keymap()` at the `DEVICE_ADDED` that follows, where
 *   the negotiated one now also passes (see the box there).
 */
int input_disposizione(Input *in, const char *nome)
{
	g_autofree char *valore = NULL;
	g_autofree char *xkb = NULL;
	GSettingsSchemaSource *fonte;
	g_autoptr(GSettingsSchema) schema = NULL;
	g_autoptr(GSettings) impostazioni = NULL;
	const char *par;

	if (!in || !nome || !*nome)
		return -1;
	/* ⭐ wlroots: no GSettings — the layout becomes the keymap of our
	 *    virtual keyboard.  ⛔ The branch below is GNOME's (its box
	 *    says so) and on XFCE it would write into a schema nobody reads. */
	if (in->wlr)
		return disposizione_wlr(in, nome);

	/*
	 * ⛔⛔ THE SAME THING IS NOT ASKED TWICE — ⚠ AND THE RIGHT QUESTION IS
	 *     "WHAT IS THERE NOW?", NOT "WHAT DID I ASK FOR?".
	 *
	 * Not asking needlessly matters: a keymap replacement costs Mutter the
	 * DESTRUCTION and recreation of the keyboard device (`STUDI.md` §gnome
	 * §9), and doing it for nothing shows.
	 *
	 * ⛔ But the first draft remembered **what it had asked for**
	 *    (`g_strcmp0(in->negoziata, nome)`), and it was form **E1**: between one
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
	if (in->disposizione && tastiera_e_questa(in->disposizione, nome) == 1)
	{
		g_free(in->negoziata);
		in->negoziata = g_strdup(nome);
		registro_dettaglio(AREA,
		                   "layout «%s»: the session ALREADY has it (verified on the keymap, "
		                   "not on memory), not requesting it",
		                   nome);
		return 0;
	}

	/*
	 * ⭐ PHASE 15, D-008 — KWin has its own way (`kwin_disposizione()`, and the
	 *    box there).  ⛔ And BEFORE GNOME's schema: a KDE machine
	 *    may have the schemas installed (any GTK program brings them),
	 *    and then the negotiated layout ended up in a key nobody reads on Plasma,
	 *    without even the fallback line.
	 */
	if (in->kwin)
	{
		g_autoptr(GError) sbaglio_kwin = NULL;

		/* ⛔ First everything is released: KWin redoes the keyboard device (see
		 *    the box below, "AND BEFORE ASKING FOR THE CHANGE"). */
		input_rilascia_tutto(in);
		g_free(in->negoziata);
		in->negoziata = g_strdup(nome);
		in->richieste_kwin = 0;
		if (kwin_disposizione(nome, &sbaglio_kwin) != 0)
		{
			registro_dice(AREA,
			              "⚠ DECLARED FALLBACK: layout «%s» was NOT requested "
			              "from KWin (%s) — the session keeps «%s».  ⛔ The letters that "
			              "layout does not have do NOT come out, and the SHORTCUTS go on the keys "
			              "of that one (RCP.md §7.3)",
			              nome, sbaglio_kwin ? sbaglio_kwin->message : "no reason",
			              in->disposizione ? tastiera_disposizione(in->disposizione)
			                               : "none");
			return -1;
		}
		registro_dice(AREA,
		              "layout «%s» REQUESTED from KWin (the session's kxkbrc + "
		              "reloadConfig + kconfig ConfigChanged) — §5-bis.7. ⚠ requested, not yet in "
		              "force: «KEYMAP CHANGED» will say so",
		              nome);
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
	par = strchr(nome, '(');
	if (par)
	{
		const char *chiusa = strchr(par + 1, ')');
		if (!chiusa)
			return -1;
		xkb = g_strdup_printf("%.*s+%.*s", (int) (par - nome), nome,
		                      (int) (chiusa - par - 1), par + 1);
	}
	else
		xkb = g_strdup(nome);

	/*
	 * ⛔ THE SCHEMA IS LOOKED UP, NOT TAKEN FOR GRANTED.  `g_settings_new()` on
	 *    a schema that is not there **aborts the process** — and the process is
	 *    the child, that is the user's stage.  ⇒ On a machine without the
	 *    GNOME schemas (a container, a different desktop) the service must
	 *    degrade, not die: `CODER.md` §4.2.
	 */
	fonte = g_settings_schema_source_get_default();
	schema = fonte ? g_settings_schema_source_lookup(fonte, "org.gnome.desktop.input-sources",
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
		              nome);
		return -1;
	}

	/*
	 * ⛔⛔ PHASE 15, D-015 — THE USER'S SETTINGS ARE NOT TOUCHED
	 *     (the user's decision of 25 Sep 2026).
	 *
	 * Until today this write ended up in the USER's dconf
	 * (`~/.config/dconf/user`) and stayed there: whoever then logged in at the monitor
	 * found the keyboard changed.  ⭐ Now the child reads and writes
	 * through the SESSION's dconf (`sessione_dconf_prepara()`: an
	 * in-memory database on top, the user's below read-only),
	 * and so does the Shell.
	 * ⛔ And if that dconf is not there, we do NOT write: better a layout not
	 *    applied, and said, than one written where the user does not want it.
	 */
	if (!sessione_dconf_di_sessione())
	{
		registro_dice(AREA,
		              "⚠ DECLARED FALLBACK: the session's dconf is not in force — "
		              "layout «%s» is NOT written (it would end up in the USER's "
		              "settings, D-015), and the session keeps «%s».  ⛔ The letters that "
		              "one does not have do NOT come out, and the SHORTCUTS go on its keys "
		              "(RCP.md §7.3)",
		              nome, in->disposizione ? tastiera_disposizione(in->disposizione)
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
	 * ⚠ And it is done even when nothing is pressed: `input_rilascia_tutto()`
	 *   **always** writes its line, and a declared zero is worth more than a
	 *   silence (it is the reason that function is made that way).
	 */
	input_rilascia_tutto(in);

	impostazioni = g_settings_new("org.gnome.desktop.input-sources");
	valore = g_strdup_printf("[('xkb','%s')]", xkb);

	if (!g_settings_set_value(impostazioni, "sources", g_variant_new_parsed(valore)))
	{
		registro_dice(AREA, "⚠ layout «%s» was NOT written into input-sources", nome);
		return -1;
	}
	/* ⛔ And `current` too, or GNOME stays on the previous index when the list
	 *    gets shorter — and an index outside the list means "none". */
	g_settings_set_uint(impostazioni, "current", 0);
	g_settings_sync();

	g_free(in->negoziata);
	in->negoziata = g_strdup(nome);

	/*
	 * ⛔ AND HERE WE DO NOT SAY IT IS IN FORCE, because we do not know it yet.
	 *    Between this line and the applied layout there is `gsd-keyboard`
	 *    reading the key, Mutter recompiling the keymap, the keyboard
	 *    device destroyed and recreated, and `leggi_keymap()` rereading.
	 *    ⚠ "I asked for it" and "it is in force" are two different facts (form E1), and
	 *      the line that ascertains the second is «KEYMAP CHANGED», a few
	 *      milliseconds further down.
	 */
	registro_dice(AREA,
	              "layout «%s» REQUESTED from the session (input-sources = %s, in the "
	              "SESSION's dconf: the user's is not touched, D-015) — §5-bis.7. "
	              "⚠ requested, not yet in force: «KEYMAP CHANGED» will say so",
	              nome, valore);
	return 0;
}

int input_pulsante(Input *in, uint16_t codice, int premuto)
{
	if (!in)
		return -1;
	return manda_bottone(in, codice, premuto);
}

int input_rotella(Input *in, int32_t asse_x, int32_t asse_y)
{
	/* ⭐ wlroots: same direction as below — the vertical is inverted HERE, once
	 *    only (see the box), and `wlr_input_rotella()` receives the
	 *    Wayland convention.  It makes the whole notches itself (§7.2 n.1). */
	if (in && in->wlr)
		return wlr_input_rotella(in->wlr, asse_x, -asse_y);
	if (!in || !in->puntatore || !in->puntatore_attivo)
		return -1;

	/*
	 * ⛔⛔ THE SIGN OF THE VERTICAL AXIS IS INVERTED HERE, ONCE ONLY.
	 *
	 * `[M]` 10 August 2026 (`RCP.md` §7.3, box «Il segno della rotella»):
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
		ei_device_scroll_discrete(in->puntatore, asse_x, -asse_y);
	else
	ei_device_scroll_delta(in->puntatore, (double) asse_x / UNITA_PER_DELTA,
	                       (double) -asse_y / UNITA_PER_DELTA);
	batti_cornice(in, in->puntatore);
	return 0;
}

int input_lettera(Input *in, uint32_t carattere)
{
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t quante = 0;
	int esito;

	if (!in)
		return -1;
	if (in->wlr)
		return lettera_wlr(in, carattere);
	if (!in->disposizione)
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
	if (!in->tastiera_dev || !in->tastiera_attiva)
		return -1;

	esito = tastiera_posizioni_per(in->disposizione, carattere, codici, &quante);
	if (esito < 0)
		return -1;
	if (esito == 0 || quante == 0)
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
	for (size_t i = 0; i < quante; i++)
		if (manda_tasto(in, codici[i], 1) < 0)
		{
			/* ⛔ Half way, what was pressed is released: a Shift
			 *    left down because of a send error is the same damage as the
			 *    Ctrl left down at detach. */
			for (size_t j = i; j > 0; j--)
				manda_tasto(in, codici[j - 1], 0);
			return -1;
		}
	for (size_t i = quante; i > 0; i--)
		manda_tasto(in, codici[i - 1], 0);
	return 0;
}

int input_posizione(Input *in, uint16_t codice, int premuto)
{
	if (!in)
		return -1;
	return manda_tasto(in, codice, premuto);
}

int input_rilascia_tutto(Input *in)
{
	int quanti = 0;
	int orfani = 0;

	if (!in)
		return -1;

	for (uint32_t c = 0; c < MAX_TASTO; c++)
		if (bit_leggi(in->tasti, c))
		{
			/* ⛔ The bit is switched off EVEN IF the send fails: if the device
			 *    is no longer there, that key is no longer ours to release, and
			 *    keeping it marked would make the bench count a release that cannot
			 *    happen.  ⚠ And only what LEFT is counted.
			 *
			 * ⛔⛔ And the ORPHAN is counted separately: `manda_tasto()` has already switched off the
			 *     bit and lowered the count, so here NOTHING is touched — doing it
			 *     twice would bring the counter below zero, and an `unsigned`
			 *     below zero is four billion. */
			if (bit_leggi(in->tasti_orfani, c))
			{
				(void) manda_tasto(in, (uint16_t) c, 0);
				orfani++;
			}
			else if (manda_tasto(in, (uint16_t) c, 0) == 0)
				quanti++;
			else
			{
				bit_scrivi(in->tasti, c, FALSE);
				if (in->quanti_tasti)
					in->quanti_tasti--;
			}
		}
	for (uint32_t c = 0; c < MAX_BOTTONE; c++)
		if (bit_leggi(in->bottoni, c))
		{
			if (bit_leggi(in->bottoni_orfani, c))
			{
				(void) manda_bottone(in, (uint16_t) c, 0);
				orfani++;
			}
			else if (manda_bottone(in, (uint16_t) c, 0) == 0)
				quanti++;
			else
			{
				bit_scrivi(in->bottoni, c, FALSE);
				if (in->quanti_bottoni)
					in->quanti_bottoni--;
			}
		}

	/* ⛔ It is ALWAYS written, even when they are zero: "nothing was pressed" and
	 *    "I did not look" have the same look in the log, and this is the
	 *    rule with the highest damage/cost ratio in `RCP.md`.
	 *
	 * ⛔⛔ AND THE ORPHANS ARE DECLARED SEPARATELY, because they are another thing: they
	 *     are not "released", they are "not releasable".  Until 16 August 2026
	 *     they ended up inside `quanti` and this line stated a number that
	 *     absolved. */
	registro_dice(AREA, "release at detach: %d keys and buttons (still marked: %u keys and "
	                    "%u buttons)%s",
	              quanti, in->quanti_tasti, in->quanti_bottoni,
	              orfani ? " — ⛔ and see the line about the ORPHANS above" : "");
	if (orfani)
		registro_dice(AREA,
		              "⛔⛔ %d keys and buttons could NOT be released: they were pressed "
		              "on devices the compositor removed.  The seat still counts them down "
		              "and there they stay until the EIS channel drops",
		              orfani);
	return quanti;
}

unsigned input_premuti(const Input *in)
{
	/* ⛔ The ORPHANS are not counted here, and it is intended: an orphan is NOT "the user
	 *    is holding something down", it is "the damage is already done".  Counting it
	 *    would forever prevent the wake-up on an already broken session — that is
	 *    precisely when the user is looking at a white page and waiting for a
	 *    frame.  ⚠ That case is handled by cure "C", which repairs it. */
	return in ? in->quanti_tasti + in->quanti_bottoni : 0;
}

void input_chiudi(Input *in)
{
	if (!in)
		return;
	if (in->wlr)
	{
		chiudi_wlr(in);
		return;
	}

	/* ⚠ A net, not the rule: the stitcher calls `input_rilascia_tutto()` at
	 *   detach (it is in the contract).  If it has not done so, here the count is still
	 *   full and the log line says so — that is, the defect SHOWS. */
	if (in->quanti_tasti || in->quanti_bottoni)
	{
		registro_dice(AREA, "⛔ closing with %u keys and %u buttons STILL PRESSED: the stitcher did not "
		                    "call input_rilascia_tutto()",
		              in->quanti_tasti, in->quanti_bottoni);
		input_rilascia_tutto(in);
	}

	if (in->puntatore)
		ei_device_unref(in->puntatore);
	if (in->tastiera_dev)
		ei_device_unref(in->tastiera_dev);
	/* ⛔⛔ HERE WAS THE HOLE — until 25 August 2026 these lines were
	 *     `ei_disconnect(in->ei); ei_unref(in->ei);` without questions, and on an
	 *     EIS channel opened a few tens of milliseconds earlier they killed the
	 *     child with SIGSEGV **before the first frame**.
	 * ⭐ The cure is HERE and not in the three `smonta_il_palco()` of `figlio.c`: the hole
	 *    belongs to the channel, and whoever put it in the callers would leave it uncovered for the
	 *    fourth caller to be born.  The box above `stacca_il_contesto()`
	 *    carries the mechanism, read in the library. */
	stacca_il_contesto(in, "closing");
	g_clear_pointer(&in->disposizione, tastiera_chiudi);
	g_free(in->keymap_nome);
	g_free(in->negoziata);
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
void input_conto(const Input *in, unsigned *tasti, unsigned *pulsanti, unsigned *ricambi_puntatore,
                 unsigned *ricambi_tastiera, int *pronto);

/* ⛔ The count of the ORPHANS, for bench `06-b33`: what stayed pressed
 *    on a device the compositor removed.  ⚠ It is in a separate function
 *    and not in the signature above because `04-b24` declares it `extern` with
 *    that signature: changing it under it would break a bench of another phase,
 *    which is exactly the kind of silent breakage this file fights. */
unsigned input_orfani(const Input *in);

unsigned input_orfani(const Input *in)
{
	return in ? in->quanti_orfani : 0;
}

void input_conto(const Input *in, unsigned *tasti, unsigned *pulsanti, unsigned *ricambi_puntatore,
                 unsigned *ricambi_tastiera, int *pronto)
{
	if (tasti)
		*tasti = in ? in->quanti_tasti : 0;
	if (pulsanti)
		*pulsanti = in ? in->quanti_bottoni : 0;
	if (ricambi_puntatore)
		*ricambi_puntatore = in ? in->ricambi_puntatore : 0;
	if (ricambi_tastiera)
		*ricambi_tastiera = in ? in->ricambi_tastiera : 0;
	if (pronto && in && in->wlr)
	{
		*pronto = !wlr_input_caduto(in->wlr);
		return;
	}
	if (pronto)
		*pronto = in && in->puntatore_attivo && in->regione_nota;
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
 *    clipboard with `appunti_apri_kde()`, like the capture with
 *    `cattura_avvia_wlr()`).  ⛔ No GNOME or KDE branch has been
 *    transformed: the new branches sit on top and do not fall into them.
 *
 * ⚠ THE DIFFERENCES, counted, with respect to libei:
 *
 *   · **no replacements, no orphans**: the devices are OURS, the
 *     compositor does not destroy them for a geometry or keymap change.  ⇒
 *     `tasti_orfani`/`bottoni_orfani` stay at zero by construction;
 *   · **the layout does not go through GSettings**: it becomes the keymap of
 *     our keyboard, and labwc hands it to the applications with our keys
 *     (§7.4).  ⭐ It is §5-bis.7 in its most direct form: the shortcuts
 *     match because the keymap that interprets them is the one that translates them;
 *   · **a dropped wire is repaired by reattaching** (see `riattacca_wlr`),
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
 * ⛔ The letters' `Tastiera` is opened from the SAME text the compositor
 *    received (`wlr_input_keymap()`): key positions are computed on the keymap
 *    with which they will be read back.  It is the rule of `leggi_keymap()`, and the log
 *    line is the same, so that whoever looks for «KEYMAP CHANGED» finds it on
 *    all three desktops.
 */
static void riapri_disposizione_wlr(Input *in)
{
	size_t misura = 0;
	const char *testo = wlr_input_keymap(in->wlr, &misura);
	g_autofree char *sbaglio = NULL;
	g_autofree char *impronta = NULL;
	Tastiera *nuova;

	if (!testo || misura == 0)
		return;
	impronta = g_strdup_printf("%zu bytes, fingerprint %08x", misura, (unsigned) g_str_hash(testo));
	nuova = tastiera_apri_da_keymap(testo, misura, in->negoziata, &sbaglio);
	if (!nuova)
		registro_dice(AREA, "⚠ the virtual keyboard's keymap does not open for letters (%s): %s",
		              sbaglio ?: "no reason declared",
		              in->disposizione ? "keeping the previous one" : "LETTERS stay off");
	else
	{
		g_clear_pointer(&in->disposizione, tastiera_chiudi);
		in->disposizione = nuova;
	}
	if (g_strcmp0(impronta, in->keymap_nome) != 0)
	{
		registro_dice(AREA, "KEYMAP CHANGED: %s (was: %s) → layout «%s», from %s (wlroots)",
		              impronta, in->keymap_nome ?: "none",
		              in->disposizione ? tastiera_disposizione(in->disposizione) : "none",
		              wlr_input_keymap_origine(in->wlr));
		g_free(in->keymap_nome);
		in->keymap_nome = g_steal_pointer(&impronta);
	}
}

Input *input_apri_wlr(uint32_t tela_l, uint32_t tela_a, char **errore)
{
	GError *sbaglio = NULL;
	WlrInput *w;
	Input *in;

	if (errore)
		*errore = NULL;
	if (tela_l == 0 || tela_a == 0)
	{
		if (errore)
			*errore = g_strdup_printf("degenerate canvas %ux%u: the absolute coordinates would have "
			                          "no range",
			                          tela_l, tela_a);
		return NULL;
	}
	w = wlr_input_apri(&sbaglio);
	if (!w)
	{
		if (errore)
			*errore = g_strdup_printf("wlroots: %s", sbaglio ? sbaglio->message : "no reason");
		g_clear_error(&sbaglio);
		return NULL;
	}

	in = g_new0(Input, 1);
	in->wlr = w;
	in->tela_l = tela_l;
	in->tela_a = tela_a;
	in->aperto_us = g_get_monotonic_time();
	in->fd_socket = -1;
	riapri_disposizione_wlr(in);

	registro_dice(AREA,
	              "input channel open to the compositor (wlroots: virtual keyboard and "
	              "pointer), canvas %ux%u",
	              tela_l, tela_a);
	return in;
}

/* ⛔ The count is kept as in `manda_tasto()`: AFTER sending, and only if it
 *    left — marking a key that did not leave would make the detach release
 *    something nobody pressed. */
static int manda_tasto_wlr(Input *in, uint16_t codice, int premuto)
{
	/* ⛔ Wire dropped ⇒ we try to reattach BEFORE saying -1.  It is not
	 *    zeal: `input_rilascia_tutto()` on a failed send CLEARS the bit, and
	 *    a button cleared from the count is a button the reattach will no longer
	 *    release.  ⚠ With a floor of one second: within that second the
	 *    hole stays, and it is said. */
	if (wlr_input_caduto(in->wlr))
		riattacca_wlr(in);
	if (wlr_input_tasto(in->wlr, codice, premuto != 0) != 0)
		return -1;
	if ((premuto != 0) != bit_leggi(in->tasti, codice))
	{
		bit_scrivi(in->tasti, codice, premuto != 0);
		if (premuto)
			in->quanti_tasti++;
		else if (in->quanti_tasti)
			in->quanti_tasti--;
	}
	return 0;
}

static int manda_bottone_wlr(Input *in, uint16_t codice, int premuto)
{
	if (wlr_input_caduto(in->wlr))
		riattacca_wlr(in); /* see `manda_tasto_wlr()` */
	if (wlr_input_pulsante(in->wlr, codice, premuto != 0) != 0)
		return -1;
	if ((premuto != 0) != bit_leggi(in->bottoni, codice))
	{
		bit_scrivi(in->bottoni, codice, premuto != 0);
		if (premuto)
			in->quanti_bottoni++;
		else if (in->quanti_bottoni)
			in->quanti_bottoni--;
	}
	return 0;
}

/* The same as `input_lettera()`, without libei's device. */
static int lettera_wlr(Input *in, uint32_t carattere)
{
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t quante = 0;
	int esito;

	if (!in->disposizione)
	{
		/* ⛔ Phase 16 §12: the typed character is NOT written. */
		registro_dice(AREA, "⚠ LETTER not sent: no layout (the virtual keyboard's "
		                    "keymap did not open)");
		return -1;
	}
	if (wlr_input_caduto(in->wlr))
		return -1;

	esito = tastiera_posizioni_per(in->disposizione, carattere, codici, &quante);
	if (esito < 0)
		return -1;
	if (esito == 0 || quante == 0)
		return 1; /* ⛔ not producible: the line is written by `tastiera.c` */

	/* The modifiers first, the key last; released in reverse.
	 * ⭐ It is here that the modifiers of `wlr_input.c` do their job: the
	 *    pressed Shift updates OUR state, and the compositor receives it
	 *    as `modifiers` before the letter. */
	for (size_t i = 0; i < quante; i++)
		if (manda_tasto(in, codici[i], 1) < 0)
		{
			for (size_t j = i; j > 0; j--)
				manda_tasto(in, codici[j - 1], 0);
			return -1;
		}
	for (size_t i = quante; i > 0; i--)
		manda_tasto(in, codici[i - 1], 0);
	return 0;
}

static int disposizione_wlr(Input *in, const char *nome)
{
	g_autoptr(GError) sbaglio = NULL;

	/* ⛔ The question is "what is there now?", as in the GNOME branch: the
	 *    real keymap is the one the virtual keyboard carries, not the memory. */
	if (in->disposizione && tastiera_e_questa(in->disposizione, nome) == 1)
	{
		g_free(in->negoziata);
		in->negoziata = g_strdup(nome);
		registro_dettaglio(AREA,
		                   "layout «%s»: the virtual keyboard ALREADY has it (verified on the "
		                   "keymap), not sending it again",
		                   nome);
		return 0;
	}

	/* ⚠ The negotiated one is recorded BEFORE the outcome: if the wire has dropped, it is the
	 *   reattach that puts it back — and it must know which. */
	g_free(in->negoziata);
	in->negoziata = g_strdup(nome);

	/* ⛔⛔ FIRST everything is released: the modifiers depend on the keymap, and a
	 *     Shift pressed with the old one and released with the new one stays down
	 *     in the compositor's state (`RCP.md` §11).  And the line is written
	 *     even with zero, as always. */
	input_rilascia_tutto(in);

	if (wlr_input_keymap_da_nome(in->wlr, nome, &sbaglio) != 0)
	{
		registro_dice(AREA,
		              "⚠ DECLARED FALLBACK: layout «%s» was NOT sent to the "
		              "virtual keyboard (%s) — «%s» stays.  ⛔ The letters that one does not have "
		              "do NOT come out, and the SHORTCUTS go on its keys (RCP.md §7.3)",
		              nome, sbaglio ? sbaglio->message : "no reason",
		              in->disposizione ? tastiera_disposizione(in->disposizione) : "none");
		return -1;
	}
	riapri_disposizione_wlr(in);
	/* ⚠ "Sent", not "in force": that labwc passed it on to the applications
	 *   only a witness inside the session can say.  `[?]` Not measured. */
	registro_dice(AREA,
	              "layout «%s» SENT to the compositor as the virtual keyboard's "
	              "keymap — §5-bis.7 on wlroots, without touching the session's settings",
	              nome);
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
 *     `TASTO 42 premuto 0`): the keyboard is fine without us (§7.2 n.5);
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
 * ⚠ The floor is that of cure "C" (`GUARIGIONE_FONDO_US`): if the compositor
 *   is really gone, the attempt costs one failed `connect()` per
 *   second, and the line comes out once only.
 */
static void riattacca_wlr(Input *in)
{
	gint64 ora = g_get_monotonic_time();
	g_autoptr(GError) sbaglio = NULL;
	WlrInput *nuovo;
	unsigned pulsanti = 0, tasti = 0;

	if (in->wlr_ultimo_riattacco_us && ora - in->wlr_ultimo_riattacco_us < GUARIGIONE_FONDO_US)
		return;
	in->wlr_ultimo_riattacco_us = ora;

	nuovo = wlr_input_apri(&sbaglio);
	if (!nuovo)
	{
		if (!in->wlr_riattacco_fallito_detto)
			registro_dice(AREA,
			              "⛔ wlroots: the input reattach does not succeed (%s) — retrying every "
			              "second, and this line does not repeat.  ⚠ Meanwhile the desktop can be "
			              "SEEN and not CONTROLLED",
			              sbaglio ? sbaglio->message : "no reason");
		in->wlr_riattacco_fallito_detto = TRUE;
		return;
	}

	/* The negotiated layout goes back to the previous one; without it, the one
	 * the session gave back at the reattach stays. */
	if (in->negoziata)
	{
		g_autoptr(GError) sb = NULL;

		if (wlr_input_keymap_da_nome(nuovo, in->negoziata, &sb) != 0)
			registro_dice(AREA, "⚠ at reattach layout «%s» is not put back (%s)",
			              in->negoziata, sb ? sb->message : "no reason");
	}

	for (uint32_t c = 0; c < MAX_BOTTONE; c++)
		if (bit_leggi(in->bottoni, c))
		{
			(void) wlr_input_rilascia_forzato(nuovo, (uint16_t) c);
			bit_scrivi(in->bottoni, c, FALSE);
			if (in->quanti_bottoni)
				in->quanti_bottoni--;
			pulsanti++;
		}
	for (uint32_t c = 0; c < MAX_TASTO; c++)
		if (bit_leggi(in->tasti, c))
		{
			bit_scrivi(in->tasti, c, FALSE);
			if (in->quanti_tasti)
				in->quanti_tasti--;
			tasti++;
		}

	wlr_input_chiudi(in->wlr);
	in->wlr = nuovo;
	in->wlr_riattacchi++;
	in->wlr_riattacco_fallito_detto = FALSE;
	riapri_disposizione_wlr(in);
	registro_dice(AREA,
	              "⭐ wlroots: input REATTACHED (n. %u).  %u buttons left down released by the "
	              "new device (`[?]` not measured that the seat accepts them), %u keys already "
	              "released by the compositor at the drop",
	              in->wlr_riattacchi, pulsanti, tasti);
}

static int gira_wlr(Input *in)
{
	if (!wlr_input_caduto(in->wlr))
	{
		int n = wlr_input_gira(in->wlr);

		if (n >= 0)
			return n;
	}
	riattacca_wlr(in);
	return wlr_input_caduto(in->wlr) ? -1 : 0;
}

static void chiudi_wlr(Input *in)
{
	/* ⚠ The same net as `input_chiudi()`: the stitcher has already released; if it has not
	 *   done it, the line says so and we release here. */
	if (in->quanti_tasti || in->quanti_bottoni)
	{
		registro_dice(AREA, "⛔ closing with %u keys and %u buttons STILL PRESSED: the stitcher did not "
		                    "call input_rilascia_tutto()",
		              in->quanti_tasti, in->quanti_bottoni);
		input_rilascia_tutto(in);
	}
	wlr_input_chiudi(in->wlr);
	g_clear_pointer(&in->disposizione, tastiera_chiudi);
	g_free(in->keymap_nome);
	g_free(in->negoziata);
	g_free(in->reg_per);
	g_free(in);
}
