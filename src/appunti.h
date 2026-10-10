/*
 * appunti.h — THE CLIPBOARD SEAM: from the desktop to the wire, and back.
 *
 * ⛔ THIS FILE BELONGS TO THE COORDINATOR, like `input.h`, and for the same reason
 *    written there: the defect lies BETWEEN two pieces "each correct on its
 *    own", and seams without an owner are watched by no bench.
 *
 * Who reads this file:
 *   · `appunti.c` — implements these functions on **Mutter**, on the
 *                   `RemoteDesktop` session `mutter.c` has already opened.  ⛔ It
 *                   knows NEITHER QUIC nor the message format;
 *   · `figlio.c`  — ⭐ **stitches the two together**: includes this file, writes
 *                   the adapters and makes them travel on the socket to the parent,
 *                   where `rcp.c` translates them into §7.4.
 *
 * ---------------------------------------------------------------------------
 * ⛔ TEXT ONLY, AND IT IS NOT A RENUNCIATION — `DECISIONI.md` §5-ter.1
 *
 * *"For the clipboard I have a precise idea: text only"* (user, 9 August 2026),
 * and confirmed on the 17th.  No images, no files, no rich formats.  ⚠ v1
 * also carried `text/html` and images (`fondamenta/remotix-c/src/scambio.c`): here
 * they are absent **on purpose**, and whoever put them back would first have to
 * reopen §5-ter.1 and `RCP.md` §7.4 — which does not even have a field for the type.
 *
 * ⇒ Hence the shape of this file: no lists of MIME types are exchanged with
 *   the stitcher, **text** is exchanged.  The types live in here and nowhere
 *   else (`TIPI_TESTO`).
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ THE CLIPBOARD BELONGS TO THE COMPOSITOR, NOT TO THE REMOTE SESSION
 *
 * `STUDI.md` §gnome §10 `[R]`, 9 August 2026, which **corrected** what
 * `LEZIONI.md` said before: it is `MetaSelection`, that is Mutter's.  The
 * `RemoteDesktop` session only owns **the door** (`EnableClipboard`).
 *
 * ⭐ And the consequence is a gift for the bench: Mutter's X11 side is
 *    **unconditional in both directions**, zero focus checks ⇒ `xclip`
 *    works **without a session of ours**, and the clipboard bench has an
 *    external referee instead of making two pieces of ours talk to each other
 *    (`PIANO.md` §0.4, `fasi/07-audio-e-appunti.md` §2.4).
 *
 * ---------------------------------------------------------------------------
 * ⛔ MUTTER'S THREE TRAPS, and all three are defused in `appunti.c`
 *
 *   1. `DisableClipboard` is **one-way** (Mutter 48.7): it detaches the manager
 *      and clears the source but does NOT set `is_clipboard_enabled` back to
 *      false, and from then on `EnableClipboard` answers "Already enabled" and the
 *      announcements never come back.  ⇒ **it is never called**: to leave the
 *      clipboard we use `SetSelection` **without** `mime-types`;
 *   2. the signature of `mime-types` is **asymmetric**: `as` going into methods,
 *      `(as)` coming out of the signal.  Whoever reads with the wrong type gets
 *      `NULL` **without an error** — that is, the clipboard works in one direction
 *      only and nothing in the log explains it;
 *   3. the internal clipboard manager keeps **a single MIME type**, so
 *      when the application that copied dies only one is left: we try
 *      **the whole row**, not just the first.
 *
 * ⛔ And the fourth, which is not Mutter's but the return path's: `SelectionOwnerChanged`
 *    arrives **also after one of OUR `SetSelection`s**, with `session-is-owner`
 *    true.  Treating it as a new copy means announcing to the client what
 *    the client just announced to us, and from there the two sides chase each other.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ THE THREAD CONTRACT, and this file has one of ITS OWN
 *
 * GDBus delivers signals to the default context of the thread that
 * **subscribed**, and no REMOTIX thread runs a GLib loop: the child's
 * waits on descriptors, PipeWire's is its own.  ⇒ `appunti.c`
 * opens a private context and runs it on a dedicated thread.
 *
 * ⇒ **The two callbacks below run on THAT thread**, not on the child's
 *   loop.  Whoever receives them **must queue and return**: they are free to write
 *   on the socket to the parent (`send` on a SEQPACKET is atomic per message),
 *   ⛔ but NOT to touch `libei`, which `input.h` declares non-reentrant.
 */
#ifndef REMOTIX_APPUNTI_H
#define REMOTIX_APPUNTI_H

#include <gio/gio.h>
#include <glib.h>
#include <stddef.h>
#include <stdint.h>

/* ⭐ This module's log area.  It lives here and not in `registro.h` for
 *    the same reason as `REG_FIGLIO`: it belongs to the child, and `registro.h` is
 *    shared with the parent. */
#define REG_APPUNTI "appunti"

/* ⛔ The ceiling of `RCP.md` §5.4, and it lives HERE because a larger text must
 *    be neither sent nor announced — that is, the decision is taken
 *    **before** crossing the socket, where the text still exists whole.
 *
 * ⚠ A round million, NOT 1 MiB: `RCP.md` §5.4 chooses 1 000 000 precisely
 *   because the message carrying it has ten bytes of framing, and a ceiling
 *   equal to the message's (§6.1, 1 MiB) would make **illegal a text exactly
 *   as large as the ceiling**.
 *
 * ⛔ And beyond the ceiling we DO NOT TRUNCATE: §5.4 forbids it with the reason
 *    written — "a truncated text pasted into a terminal is worse than a missing
 *    text".  It is not announced at all, and it is written to the log. */
#define APPUNTI_TETTO 1000000u

typedef struct Appunti Appunti;

/*
 * ⭐ "THE SESSION HAS COPIED SOME TEXT", and it is already read and already validated.
 *
 * ⛔ The text arrives ALREADY READ, and it is not a convenience: the §7.4 announcement
 *    carries `u32 lunghezza`, and nobody can say how long a text is without
 *    having read it.  ⇒ The protocol's "announce and then pull" lives on the
 *    WIRE, where it is needed; on this side the text is already there.
 *
 * ⛔ And if the text exceeds `APPUNTI_TETTO` this callback is NOT called
 *    at all (§5.4: "it is not announced"), and the line is in the log.  ⚠ So
 *    "nothing was copied" and "it was too large" do not have the same
 *    face — `CODER.md` §3.10.
 *
 * `testo` is valid UTF-8, zero-terminated, and valid ONLY inside the call.
 * Runs on the clipboard thread.
 */
typedef void (*AppuntiSuTesto)(const char *testo, size_t byte, void *dati);

/*
 * ⭐ "THE SESSION WANTS TO PASTE what the client has": ask the client,
 *    and when the answer arrives call `appunti_rispondi` with this
 *    `serial`.
 *
 * ⛔⛔ IT MUST ALWAYS BE ANSWERED, even when failing, and even if the client never
 *      answers.  A `SelectionTransfer` left unanswered leaves the
 *      application that is pasting waiting **indefinitely**, and
 *      what the user sees is **a desktop that has hung** — a defect
 *      nobody connects to the clipboard.
 * ⇒ The stitcher keeps a time floor and answers `NULL` when it expires.
 *
 * Runs on the clipboard thread.
 */
typedef void (*AppuntiSuRichiesta)(uint32_t serial, void *dati);

/*
 * Switches the clipboard on, on the given control session, and switches it on **once
 * per graphical session**.
 *
 * ⛔ IT IS NEVER SWITCHED OFF — see trap 1 at the top.  `appunti_chiudi`
 *    dismantles what is ours (thread, context, subscriptions) and **does not
 *    call `DisableClipboard`**: closing the control session everything goes
 *    away together, which is the clean way.
 *
 * ⭐ And it is switched on with EMPTY options, on purpose: so Mutter makes us
 *    owners of nothing and tells us at once who is the owner now, with a
 *    `SelectionOwnerChanged` that arrives **immediately**.  ⛔ It is the line that
 *    lets whoever RECONNECTS find the clipboard again: that signal arrives only
 *    when the owner **changes**, and at a reconnection nothing
 *    changes (`STUDI.md` §gnome §10 — "it was our recipe that lost it").
 */
Appunti *appunti_apri(GDBusConnection *bus, const char *percorso_controllo,
                      GError **sbaglio);
/* ⭐ PHASE 12 — the same clipboard on KDE Plasma (`appunti_kde.h`): no bus
 *    to pass, KWin is reached on the user's Wayland socket.  From there
 *    on the same functions below are used. */
Appunti *appunti_apri_kde(GError **sbaglio);
/* ⭐ PHASE 13 — and on XFCE (labwc): the same module as KDE, which already speaks
 *    the wlroots protocol (`appunti_kde.h`). */
Appunti *appunti_apri_wlroots(GError **sbaglio);

void appunti_chiudi(Appunti *appunti);

/* Who listens to the two callbacks.  With NULL callbacks listening stops,
 * and the call **waits** until no callback is in progress. */
void appunti_ascolta(Appunti *appunti, AppuntiSuTesto su_testo,
                     AppuntiSuRichiesta su_richiesta, void *dati);

/*
 * ⭐ The last text the SESSION copied, or NULL.
 *
 * ⛔ IT IS HERE THAT WHOEVER RECONNECTS FINDS THE CLIPBOARD AGAIN, and it is here and
 *    not in the channel **precisely because it must survive the connection** — like
 *    the rest of the stage (invariant I4).
 *
 * Returns a copy to free with `g_free`; `byte` — if not NULL —
 * receives how many bytes it has.
 */
char *appunti_ultimo_testo(Appunti *appunti, size_t *byte);

/*
 * "THE CLIENT HAS COPIED SOME TEXT": from now on the session can ask for it, and
 * will ask for it with the `AppuntiSuRichiesta` callback.
 *
 * ⛔ It does NOT carry the text, and it is not an oversight: it is §7.4's "announce
 *    and then pull" applied on this side.  Whoever copies a whole document on
 *    the phone sends it to nobody until someone pastes.
 */
/* ⭐ Reads the session's selection NOW and hands it to the callback:
 *    Mutter does not tell a new session who owns the selection, and
 *    without this call the desktop clipboard is lost at connection.
 *    See the box in `appunti.c`. */
void appunti_leggi_adesso(Appunti *appunti);

gboolean appunti_offri(Appunti *appunti, GError **sbaglio);

/*
 * Answers a request of the session.  With `testo` NULL it declares it does not
 * have what was asked — ⛔ **which is an answer anyway**, and it is
 * the one that unblocks whoever is pasting.
 *
 * ⛔ IT WAITS: it opens a descriptor and writes into it.  It must be called from a
 *    thread that can afford it.
 */
void appunti_rispondi(Appunti *appunti, uint32_t serial, const char *testo,
                      size_t byte);

#endif
