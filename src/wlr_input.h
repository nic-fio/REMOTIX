/*
 * wlr_input — the input TRANSPORT on the third family: labwc, and so XFCE.
 *
 * ⛔⛔ AND IT IS NOT A SECOND `input.c`: it is the piece that on GNOME and KDE `libei`
 *     does, and nothing more.
 *
 *     `[✗]` libei on wlroots **does not exist** (`STUDI.md` §xfce §7, searched in
 *     wlroots, labwc, sway, wayfire, weston, xdpw and wayvnc: zero).  ⇒ The way
 *     is two Wayland protocols, both `[M]` announced by labwc:
 *
 *        `zwp_virtual_keyboard_manager_v1`  v1   — the keyboard
 *        `zwlr_virtual_pointer_manager_v1`  v2   — the pointer
 *
 *     and no permission: wlroots does not filter, labwc filters only clients locked
 *     in a sandbox (§7).  The only gate is the uid, as for capture.
 *
 * ⭐ THE DIVISION OF LABOUR, and why it is this way.
 *
 *   `input.c` keeps **the accounts** — what is pressed, the orphans, the
 *   release at detach, the negotiated layout, the letters — and it is the
 *   part GNOME and KDE have already paid for and measured.  ⛔ Rewriting it here
 *   would mean two sets of accounts that one day diverge.
 *
 *   Here is **what on wlroots has no equivalent in libei**:
 *     · the Wayland connection, the globals, the two devices;
 *     · ⛔ the KEYMAP, which here WE present (`no_keymap` otherwise);
 *     · ⛔⛔ the MODIFIERS, which with libei did not exist (§7.2 trap 4);
 *     · the wheel in whole notches and the `frame` after every gesture (§7.2 1-3);
 *     · the duplicate press, which here nobody filters for us.
 *
 * ⛔ A SINGLE THREAD, like `input.h`: all functions from the thread that calls
 *    `wlr_input_gira()`.  `libwayland-client` would bear several threads, but only
 *    with a queue protocol that is not here — and is not needed.
 *
 * ⚠ A CONNECTION OF ITS OWN, and not the capture's (`wlroots.c`).  §7.1
 *   suggested sharing it; ⛔ here we choose not to, declaring it: the
 *   capture pumps the wire **inside** `wlr_fotogramma()` with its deadlines, and
 *   a protocol error on a connection kills it **whole** (it is
 *   `wl_display` that dies, not the object).  ⇒ Separate, an error of ours
 *   on input leaves the video alive, and vice versa.  The price is one more socket
 *   towards labwc.
 */
#pragma once

#include <glib.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct WlrInput WlrInput;

/*
 * Connects to the user's compositor, binds the seat and the two managers, creates the
 * virtual keyboard and pointer, and ⛔ **sends a keymap at once** — without it,
 * the first key is a `no_keymap` protocol error that closes the whole
 * connection (`wlr_virtual_keyboard_v1.c:83-88`, `STUDI.md` §xfce §7.4).
 *
 * The initial keymap: the SESSION's, copied from the wire
 * (`wl_seat.get_keyboard`, §7.4) if the compositor hands it over; otherwise
 * the one `xkbcommon` composes from the environment — ⚠ and the log line says
 * which of the two, because they are two different truths.
 * ⛔ `[M]` 21 Sep 2026, laptop, labwc 0.8.3 headless: the session does **not**
 *    hand it over — without a real keyboard the seat declares capability 0, and the spy
 *    is not born.  ⇒ On a remote session the real way is the ENVIRONMENT, and the
 *    right layout arrives a moment later, with the negotiated one
 *    (`figlio.c` applies it when the channel opens).
 *
 * NULL with `sbaglio` written.
 */
WlrInput *wlr_input_apri(GError **sbaglio);

/* The descriptor to put in the `poll()`; -1 if the wire has dropped. */
int wlr_input_descrittore(WlrInput *w);

/* Serves the wire WITHOUT waiting: reads what there is, sends what is left.
 * Returns the events served, or -1 if the wire has dropped (and says so once). */
int wlr_input_gira(WlrInput *w);

bool wlr_input_caduto(const WlrInput *w);

/*
 * ⛔ THE KEYMAP IN FORCE on our keyboard, as XKB text (without the final
 *    zero in `*lunghezza`).  It is **the one** `input.c` must give to
 *    `tastiera_apri_da_keymap()`: letters are translated into key positions with the
 *    very same keymap with which the compositor will read them back.  Two "equal"
 *    keymaps compiled twice are a promise; the same text is a fact.
 */
const char *wlr_input_keymap(const WlrInput *w, size_t *lunghezza);

/* Where the keymap in force comes from: «session», «environment», or the requested name. */
const char *wlr_input_keymap_origine(const WlrInput *w);

/*
 * ⭐ The negotiated layout (`RCP.md` §4.5: `it`, `us`, `de(neo)`) becomes the
 *    keymap of OUR keyboard.  On this family it is the right form of
 *    `DECISIONI.md` §5-bis.7 and not a fallback: labwc, at every key, does
 *    `wlr_seat_set_keyboard()` with the keyboard that typed it and sends **its
 *    keymap** to all applications (§7.4).  ⇒ The applications read our
 *    keys with our keymap, and the shortcuts match.
 *
 * ⚠ The caller releases what is pressed FIRST: the modifiers depend
 *   on the keymap, and a Shift pressed with the old one and released with the new one
 *   is the fault that gives no error.
 *
 * 0 sent, -1 not (with `sbaglio`).
 */
int wlr_input_keymap_da_nome(WlrInput *w, const char *nome, GError **sbaglio);

/* Sends again an already known XKB text — used at reattach, to put back the same one. */
int wlr_input_keymap_da_testo(WlrInput *w, const char *testo, size_t lunghezza,
                              const char *origine, GError **sbaglio);

/*
 * A key, in evdev (`KEY_A` = 30).  ⛔ The duplicate (pressed twice without
 * release, or released without being pressed) is NOT sent and returns 0: on
 * wlroots nobody filters it for us, and a CapsLock held down that repeats
 * would toggle it at every repetition.
 * 0 delivered (or duplicate ignored), -1 not.
 */
int wlr_input_tasto(WlrInput *w, uint16_t codice, bool premuto);

/* The absolute pointer: `x` in [0, l), `y` in [0, a) — the extent is the canvas. */
int wlr_input_assoluto(WlrInput *w, uint32_t x, uint32_t y, uint32_t l, uint32_t a);

/* A button, in evdev (`BTN_LEFT` = 0x110).  ⛔ Here too the duplicate is not
 * sent: the wlroots seat COUNTS presses, and a double press wants
 * two releases — with the second one that will never arrive. */
int wlr_input_pulsante(WlrInput *w, uint16_t codice, bool premuto);

/*
 * ⛔ The release that is sent EVEN IF this device did not press it:
 *    used only at reattach, to close a button left down on the
 *    device of a dead connection (§7.2 trap 5).  ⚠ `[M]` on the
 *    laptop the headless seat did not need it (see `riattacca_wlr`
 *    in `input.c`); it stays for the case, `[?]`, of another pointer in the seat.
 */
int wlr_input_rilascia_forzato(WlrInput *w, uint16_t codice);

/*
 * The wheel, in units of 120 per notch and ⛔ in WAYLAND's convention
 * (positive = down / right): the direction of `RCP.md` is flipped by `input.c`, once
 * only.  Half notches accumulate (threshold 60, as on GNOME).
 */
int wlr_input_rotella(WlrInput *w, int32_t orizzontale, int32_t verticale);

void wlr_input_chiudi(WlrInput *w);
