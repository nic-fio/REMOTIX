/*
 * input.h — THE SEAM of the input channel: from the wire to the desktop.
 *
 * ⛔ THIS FILE BELONGS TO THE COORDINATOR, not to the link that implements it.  The reason
 *    is written in `fasi/rapporti/F5-desktop-vero.md`: the defect of phase 3
 *    was not INSIDE a piece, it was BETWEEN two pieces "each correct on its
 *    own" — and the seams, having no owner, were watched by no
 *    bench.  Here they have an owner.
 *
 * Who reads this file:
 *   · `input.c` — implements these functions on `libei`, on the session of
 *                 `mutter.c`.  ⛔ It knows NEITHER QUIC nor the message
 *                 format;
 *   · `figlio.c`— ⭐ **stitches the two together**: it is the one that includes this file, writes the
 *                 six adapters and hangs them on the hooks of `rcp_ganci`.
 *
 * ⛔⛔ AND HERE THERE WAS A WRONG LINE, corrected on 14 August 2026 on a finding
 *      of the link that implemented the wire — which tested it instead of believing it.
 *
 * It said: *"`rcp.c` decodes the messages of §7.3 and **calls these
 * functions**"*.  ⛔ **The build makes it impossible**, and it is not a
 * matter of style: `rcp.c` lives in TWO folders that the `Makefile`
 * (`GEMELLATI`) requires identical byte for byte, and the second copy
 * `banchi/01-b3-rcp-innesta.py` slips into ngtcp2's `examples/`, where
 * `input.h` **is not there**.  An `#include "input.h"` in `rcp.c` does not compile
 * the graft ⇒ **it switches off B3, B5, B6, B8 and B11 in one blow**.
 *
 * ⇒ The right form is the one `rcp.h` already uses for PAM and for the streams:
 *   **six hooks in `rcp_ganci`**, with the signatures of this file field by field.
 *   ⛔ They are connected **all six or none**: a channel that could move the
 *   pointer and could not release a button would leave the desktop
 *   **worse than it found it**.
 *
 * ⛔⛔ THE THREAD CONTRACT, and it is written because it is a defect that GIVES NO
 *      ERROR — asked for by the link that implemented this file, 14 Aug 2026.
 *
 *      **`libei` is not reentrant.**  ALL functions of this file must be
 *      called from the **same thread** that calls `input_gira()`.  Two threads
 *      on one `struct ei` do not give an error: they give a program that at some
 *      point misbehaves, and nobody connects the two things.
 * ⚠ In the product it is the child's loop (`figlio.c`), which is single-threaded.
 *
 * ⛔ The rule governing the types below: the codes are those of **evdev**
 *    (`linux/input-event-codes.h`), because `libei` works in evdev and any
 *    other convention would add a table that goes wrong silently
 *    (`RCP.md` §7.3).
 */
#ifndef REMOTIX_INPUT_H
#define REMOTIX_INPUT_H

#include <stdint.h>
#include <stddef.h>

typedef struct input Input;

/*
 * Opens the channel to the compositor.  `sessione_controllo` is the D-Bus
 * path of the `RemoteDesktop` session already started by `mutter.c`, from which
 * `ConnectToEIS` is requested (see the comment of `src/mutter.c:402`).
 *
 * `tela_l`/`tela_a` are the CANVAS of `RCP.md` §4.5 — not the view.  They serve to
 * map the region of the absolute pointer.
 *
 * ⛔ Returns NULL and fills `*errore` (to be freed with free) if it does not open.
 *    No silent fallback: `CODER.md` §4.2.
 */
Input *input_apri(void *sessione_mutter, uint32_t tela_l, uint32_t tela_a,
                  char **errore);

/* ⭐ PHASE 12 — the same, with the channel asked of KWin (`kwin_eis_fd()`).
 *    `tela_l`/`tela_a` are the size of KWin's output. */
struct KwinSessione;
Input *input_apri_kwin(struct KwinSessione *kwin, uint32_t tela_l, uint32_t tela_a,
                       char **errore);

/*
 * ⭐ PHASE 13, INCREMENT 3 — the same contract on wlroots (labwc, XFCE).
 *
 * ⛔ Here `libei` does NOT exist (`STUDI.md` §xfce §7, `[✗]`): the transport is
 *    Wayland's virtual keyboard and pointer (`wlr_input.h`).  No
 *    session is needed to ask the channel from: we connect to the user's
 *    compositor like any of its clients.
 *
 * ⭐ The other functions of this file do NOT change signature: the stitcher (`figlio.c`)
 *    changes in one place only, the constructor.  Inside, the public functions
 *    hand over at the top, as the clipboard does with `appunti_apri_kde()`.
 *
 * ⚠ And the two differences in behaviour the stitcher must know:
 *   · `input_disposizione()` does NOT touch the session's settings: the
 *     layout becomes the keymap of OUR virtual keyboard, which labwc
 *     hands to the applications together with our keys (§7.4);
 *   · there are no device replacements nor orphans: on wlroots the devices
 *     are ours, and the compositor does not recreate them.
 */
Input *input_apri_wlr(uint32_t tela_l, uint32_t tela_a, char **errore);

/*
 * ⛔ The silent replacements of `libei`, which `STUDI.md` §gnome §9 measures: a keymap
 *    change destroys and recreates the keyboard device, a geometry change
 *    all the absolute devices — and the pointer to the old device
 *    stops working WITHOUT AN ERROR.  ⇒ This must be called from the child's loop
 *    at every round: inside it rereads keymap and regions at every `DEVICE_ADDED`.
 *    Returns the number of events served, or -1.
 */
int input_gira(Input *);

/*
 * ⛔⭐ THE DESCRIPTOR TO PUT IN THE `poll()`, and it is not a convenience: it is
 *     milliseconds on the input path.
 *
 *     Without it, the only way is to call `input_gira()` at intervals — that is
 *     **latency added right where the third number of `CODER.md` §1-bis
 *     counts it** (ceiling 50 ms).  ⚠ A bench that polls every 50 ms measures fine;
 *     a product that does it gives away up to 50 ms to the user on every gesture.
 *
 * Returns -1 if the channel is not open: ⛔ and -1 means "nothing to put
 * in the poll", not "error" — the caller tells them apart by looking at whether `Input` exists.
 */
int input_descrittore(Input *);

/*
 * The five actions of `RCP.md` §7.3.  All return 0 if the action was
 * delivered to the compositor, -1 if not.
 *
 * ⛔ `x`/`y` are PIXEL INDICES ON THE CANVAS: `0 <= x < tela_l`.  The caller has
 *    already refused out-of-range coordinates (it is `rcp.c`): here NO
 *    transformation is applied.
 */
int input_puntatore(Input *, uint32_t x, uint32_t y);

/*
 * ⛔ THE CANVAS IN FORCE HAS CHANGED (`RCP.md` §7.1, `TELA(ADATTATA)`).  Remaps
 *    the region of the absolute pointer.  0 if done, -1 if not.
 *
 * ⚠ Added on 14 August 2026, and the reason is a defect *between* two pieces —
 *   the same form phase 3 has already paid for.  `input_apri()` takes the
 *   canvas **once only**; after a `TELA(ADATTATA)` `rcp.c` saturates the
 *   coordinates to the NEW canvas while `input.c` stays mapped on the OLD one:
 *   ⛔ two sides with two truths, and no error anywhere.
 *
 * ⚠ `[?]` Maybe `input_gira()` would already suffice, because it rereads the regions at
 *   every `DEVICE_ADDED` — ⛔ but **it is not measured**, and the moment of the
 *   `DEVICE_ADDED` is not the moment of the `TELA`.  As long as it stays `[?]`, the
 *   explicit call is the way.
 */
int input_ritela(Input *, uint32_t tela_l, uint32_t tela_a);

/*
 * ⭐ PHASE 15, D-007 — AFTER A CHANGE OF THE OUTPUT'S SIZE, THE WINDOWS ARE
 *    BROUGHT BACK INSIDE THE SCREEN (moved as little as possible, shrunk
 *    only if larger than the screen).
 *
 * On GNOME and KDE the compositor does it by itself ⇒ here nothing is done, and
 * 0 is returned.  On labwc (XFCE, LXQt) we TYPE the shortcut
 * `SESSIONE_LABWC_TASTO` that the session wrote into labwc's
 * configuration (`sessione.h`, the box of `SESSIONE_LABWC_TASTIERA`), and then
 * put the pointer back where the user had left it.
 * ⚠ Harmless if there is nothing to bring back: a window already inside stays
 *   where it is, to the pixel.
 * Returns 1 if it typed the shortcut, 0 if not needed, -1 if sending fails.
 */
int input_riporta_dentro(Input *);

/*
 * ⛔⭐⭐ THE NEGOTIATED LAYOUT ENTERS THE SESSION — `DECISIONI.md`
 *      §5-bis.7, decided by the user on 8 August 2026 and CONFIRMED on the 16th.
 *
 * ⛔ And the direction is THIS one, not the other.  The short way would have been: keep
 *    the session as it is and translate the letter with a keymap of OURS, the one
 *    the client asked for.  ⛔ `tastiera.h` explains why it is wrong and
 *    `tastiera.c` measures it: with our keymap and their session
 *    **different characters** come out — we send key 26 for the `[` of `us` and on
 *    screen, on an `it` session, an `è` appears.  That is exactly what
 *    `RCP.md` §7.3 forbids.
 *
 * ⇒ The layout **of the session** is changed, and then it is READ BACK from
 *   `libei` as has always been done.  ⭐ That this trip holds is not a
 *   hope: `[M]` 16 August 2026, bench `06-b34` case 2s — with the session's layout
 *   changed, Mutter destroys and recreates the keyboard
 *   device, `leggi_keymap()` rereads, and the witness inside the session
 *   receives the RIGHT character.
 *
 * ⛔⛔ AND THE DAMAGE THIS FUNCTION CURES IS NOT THE CONVENIENCE OF TWO ACCENTS.
 *     `SPECIFICHE.md` §7.3: letters travel as **letters**, but
 *     shortcuts travel as **key positions** — and key positions match only
 *     if the two layouts are the same.  On a German keyboard `Z`
 *     is where on ours `Y` is (evdev 21 versus 44): without renegotiating,
 *     **`Ctrl+Z` arrives as `Ctrl+Y`**, that is "redo" instead of "undo".
 *     ⚠ The symptom the user describes is "undo does not work", and nobody
 *       connects it to the layout.
 *
 * `nome` is the string of `RCP.md` §4.5: `it`, `us`, `de(neo)`.
 *
 *   returns  0  the request has LEFT.  ⚠ NOT "it is in force": the compositor
 *               takes its time, and whoever ascertains it is the line of
 *               `leggi_keymap()` at the `DEVICE_ADDED` that follows;
 *   returns -1  it has not left, and it is already declared in the log.
 */
int input_disposizione(Input *, const char *nome);

/* `codice` is evdev: `BTN_LEFT` = 0x110.  `premuto` 1 or 0. */
int input_pulsante(Input *, uint16_t codice, int premuto);

/*
 * ⛔ Units of 120 per notch, and THE SIGN OF THE VERTICAL AXIS IS INVERTED IN
 *    HERE — once only, in one place only.  It is `[M]` 10 August 2026
 *    (`RCP.md` §7.3, box «The sign of the wheel»): the client sends +120
 *    when the user turns up, and the two conventions are opposite.
 * ⚠ And half notches exist: 60 is NOT rounded to zero.  `STUDI.md` §gnome §9 says
 *   that `ei_device_scroll_discrete` does an integer division by 120 and
 *   eats them: the way is `scroll_delta`, where the real threshold is 60.
 */
int input_rotella(Input *, int32_t asse_x, int32_t asse_y);

/*
 * A letter, as a Unicode scalar value.  Goes through `tastiera.h`.
 * ⛔ If the character is NOT producible in the session's layout:
 *    returns 1 (not 0 and not -1).  ⛔ NEVER a different letter, NEVER silence
 *    (`RCP.md` §7.3, `SPECIFICHE.md` §7.3).
 *
 * ⚠ CORRECTED ON 14 AUGUST 2026 — here it said "and the caller writes it to the
 *   log", and it was the wrong half of the seam: **the line is already written
 *   by `tastiera.c`**, and it puts in it **which layout** — which is the
 *   only thing useful to whoever reads the log six hours later, and which `rcp.c` does not
 *   know.  ⛔ Hence: **`rcp.c` MUST NOT duplicate it**, or the same characters
 *   are counted twice.
 *
 * ⚠ And for the same reason `input_apri()` does NOT take the layout: the
 *   keymap arrives from `libei` inside `input.c`, at every `DEVICE_ADDED`
 *   (`tastiera_apri_da_keymap()`).  It is not an oversight: it is the right
 *   direction.
 */
int input_lettera(Input *, uint32_t carattere);

/* A key position, in evdev: `KEY_A` = 30.  `premuto` 1 or 0. */
int input_posizione(Input *, uint16_t codice, int premuto);

/*
 * ⛔⛔ THE RELEASE AT DETACH — `RCP.md` §11 calls it "the rule with the highest
 *      damage/cost ratio in the document".  Releases EVERY key and EVERY
 *      button that is pressed.  A Ctrl left down in a session
 *      that survives the client makes the desktop unusable at reattach, and
 *      nobody connects the two things.
 * ⇒ Hence the obligation, for the implementer: the count of what is pressed is KEPT.
 *   Returns how many it released, so that the bench can count them.
 */
int input_rilascia_tutto(Input *);

/*
 * ⛔⛔ HOW MUCH IS DOWN NOW — between keys and buttons, in a single number.
 *      Added on 21 August 2026 for cure "A".  🔸 Derived.
 *
 * ⚠ It is NOT a statistic for the log: it is a **guard**, and the caller
 *   must know what it prevents.
 *
 * ⛔ THE FACT, `[M]` 21 August 2026 (bench `banchi/06-b33-risveglio.*`): every
 *    `cattura_risveglia()` makes Mutter recreate the absolute devices — **3
 *    wake-ups, 3 replacements, with ZERO canvas changes**.  And if at that moment a
 *    button is pressed, that button stays down **in the seat** and ⛔ **the
 *    desktop no longer takes a click for the whole session**.
 *
 * ⛔ And the moment `figlio.c` calls `cattura_risveglia()` is *"the scene
 *    is still and a keyframe is owed"*, that is **exactly** the moment the
 *    user may hold the mouse down on a desktop that does not move.
 *
 * ⇒ Whoever is about to do something that recreates the devices looks here first.
 *
 * ⚠ And the cure of `figlio.c:3964` — releasing before `cattura_ridimensiona()`
 *   — **does not cover this path**: there the release can be done because it is the
 *   client that asked for the change; here not, because the user is
 *   dragging and nobody asked them anything.
 */
unsigned input_premuti(const Input *);

void input_chiudi(Input *);

#endif /* REMOTIX_INPUT_H */
