/*
 * mutter — the mandatory sequence that opens a virtual monitor and its stream.
 *
 * ⛔ CARRIED OVER FROM `fondamenta/remotix-c/src/mutter.c` (353 lines), not copied:
 *    that file pulled in `sessione.h` and v1's log, and called
 *    `ConnectToEIS` for input — which does not exist yet in phase 2.  What stays here is
 *    ⭐ **the D-Bus sequence**, which is the precious piece, and the two punishments
 *    written next to each step.
 *
 * We talk to the compositor's DIRECT interfaces, not to `xdg-desktop-portal`:
 * the portal asks permission from a user sitting in front of the screen, and in
 * a session without a monitor that interaction cannot happen (`CODER.md`
 * §4.3).  It is also the reference's way (`STUDI.md` §gnome-remote-desktop §5).
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE ORDER ADMITS NO PERMUTATIONS, and each permutation is punished with a
 *    DIFFERENT error that does not say "you got the order wrong" (`LEZIONI.md` §4 trap 1;
 *    the sequence was copied and retried on the hardware by the F2.2 bench):
 *
 *      1. RemoteDesktop.CreateSession      → path, and its SessionId is read
 *                                            WITHOUT starting it
 *      2. ScreenCast.CreateSession         declaring `remote-desktop-session-id`
 *      3. RemoteDesktop.Session.Start      ← NOW, not before
 *      4. ScreenCast.Session.RecordVirtual → path of the stream
 *      5. Stream.Start                     ← the STREAM, not the session
 *
 *    - starting the control before step 2 →
 *      «Remote desktop session already started»;
 *    - starting the capture with `Session.Start` →
 *      «Must be started from remote desktop session».
 *
 *    And at closing it holds in reverse: `ScreenCast.Session.Stop` on an associated
 *    capture answers «Must be stopped from remote desktop session».  ⇒ One
 *    closes by stopping the CONTROL, and the capture follows it.
 *
 * ⛔ THE PIPEWIRE NODE ARRIVES WITH A SIGNAL EMITTED **DURING** `Stream.Start`:
 *    subscribe BEFORE calling it, or wait forever for an announcement already
 *    gone by (`LEZIONI.md` §4 trap 2).
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE VIRTUAL MONITOR IS MOUNTED BY THE PROGRAM, AND THAT IS INVARIANT I7
 *
 * `fondamenta/remotix-c/src/sessione.c:671` is `if (tipo == COMPOSITORE_KWIN && …)`: on the
 * GNOME branch width and height **entered the function and were lost**, and
 * the virtual monitor ended up in a line of `provision-server.sh` — that is, in a
 * configuration that can be lost.  ⛔ And it was lost: `[M]` 12 August 2026,
 * the NIC-OS session ran **two days alive, complete and BLACK**.
 *
 * ⇒ Here `RecordVirtual` mounts the monitor **inside the program**, at every
 *   opening.  It is not a convenience: it is the protection against a known defect placed
 *   where removing it takes a deliberate act.
 *
 * ---------------------------------------------------------------------------
 * ⛔ AND THE MONITOR IS KNOWN BY NAME, NEVER BY INDEX AND NEVER BY SIZE — form E2
 *
 * `[M]` 12 August 2026: on the server there are TWO virtual monitors — `Meta-0` /
 * «MetaVirtualMonitor» (the session's) and `Meta-1` / «Virtual remote
 * monitor» (the one from `RecordVirtual`, that is ours) — and ⛔ **both are
 * 1920×1080@60**.  Only the product name tells them apart.
 *
 * The F2.2 bench paid for this defect head-on: `mpv --fs` went
 * full screen on the FIRST monitor, the scene was live, and the capture received
 * **zero frames** — with the bench GREEN.  ⇒ `mutter_monitor_nostro` exists
 * so that whoever opens a window on this screen can name it
 * (`CODER.md` §3.9: tell it what to do, and verify that it obeyed).
 *
 * ⛔ And if after mounting **exactly one** new monitor does not appear, we do not
 *    guess: we answer NULL and the caller declares it.
 */
#ifndef REMOTIX_MUTTER_H
#define REMOTIX_MUTTER_H

/* ⚠ `gio` and not just `glib`: since phase 7 this file declares `mutter_bus()`,
 *   which returns a `GDBusConnection`.  ⛔ Without it, the type is unknown and
 *   the compiler takes it for `int *` — and the error shows up in `mutter.c`,
 *   not here, that is far from the line that caused it. */
#include <gio/gio.h>
#include <glib.h>
#include <stdint.h>

typedef struct MutterSessione MutterSessione;

/*
 * Runs the whole sequence and returns the session ready, with the PipeWire
 * node already announced.
 *
 * ⚠ THE SIZE IS NOT DECLARED HERE: `RecordVirtual` does not take it.  The monitor is
 *   requested, and the resolution is agreed in the PipeWire negotiation — see
 *   `cattura.h`.  Whoever looks here for a width is looking in the wrong
 *   place, and that is why this line exists.
 */
MutterSessione *mutter_apri(GError **sbaglio);

/* The PipeWire node to read frames from. */
uint32_t mutter_nodo(const MutterSessione *sessione);

/* The D-Bus path of the stream and that of the control: they are the addresses
 * phase 4 will talk to in order to move the pointer. */
const char *mutter_percorso_flusso(const MutterSessione *sessione);
const char *mutter_percorso_controllo(const MutterSessione *sessione);

/*
 * ⭐ PHASE 7 — the session bus on which this session was opened.
 *
 * ⛔ It is ASKED of whoever has it instead of opening a second one, and the reason is not
 *    economy: the clipboard lives on the **same** `RemoteDesktop` session
 *    as the stage (`EnableClipboard` on `mutter_percorso_controllo()`), and a
 *    second connection to the bus would mean a second name on the bus — that is
 *    a sender that Mutter does not recognise as the owner of the session.
 *
 * ⚠ It stays owned by the `MutterSessione`, which closes it in
 *   `mutter_chiudi()`: whoever uses it uses it **while the session lives**.
 */
GDBusConnection *mutter_bus(const MutterSessione *sessione);

/*
 * The identifier declared to `RecordVirtual`.
 *
 * ⛔⛔ AND IT IS GOOD FOR NOTHING — `[M]` 14 August 2026, and the line below said
 *      the opposite: *"it is the key by which, among the regions that
 *      libei announces, our monitor's one is recognised"*.
 *
 *      `handle_record_virtual` reads **`cursor-mode` and `is-platform` and nothing else**:
 *      our `mapping-id` property is ignored **silently**.  The
 *      real key is generated by Mutter (UUID) and published in the stream's
 *      `Parameters`: it is read with `mutter_mapping_id_pubblicato`, and the direction is
 *      **Mutter → us**.  (`STUDI.md` §gnome §9, `reference-gnome/rapporti/06-mutter-input.md`
 *      §7.2.)
 *
 * ⚠ It stays exposed because the bench compares the two values: it is the way to
 *   SHOW that they differ, instead of only writing it.
 */
const char *mutter_mapping_id(const MutterSessione *sessione);

/*
 * ⭐ The REAL key of the pointer region: the UUID that Mutter generates and
 *    publishes in the stream's `Parameters`.
 *
 * ⛔ NULL means "I don't know", and those are TWO cases the log separates: the
 *    reading of the property failed, or the `Parameters` do not carry the
 *    key.  Whoever receives it recognises the region by geometry and DECLARES it.
 *
 * It can be called only after `mutter_apri` (the stream path is needed).
 */
const char *mutter_mapping_id_pubblicato(MutterSessione *sessione);

/*
 * ⭐ The descriptor of the EIS channel, opened by `ConnectToEIS` inside
 *    `mutter_apri` — at the point of the sequence the reference imposes.
 *
 * ⛔ -1 means that the channel did NOT open, and the log says why.
 *    The session is alive anyway (one watches, one does not command): it is the
 *    declared degradation of `CODER.md` §4.2, not a fault.
 *
 * ⚠ The descriptor stays with this session, which closes it in `mutter_chiudi`.
 *   Whoever gives it to `libei` — which takes ownership of it — passes a `dup`.
 */
int mutter_eis_fd(const MutterSessione *sessione);

/*
 * ⛔⛔ REDOES THE EIS CHANNEL, LEAVING THE SESSION STANDING — cure "C" of
 *      `fasi/06-la-tela-e-la-vista.md` §7.1.  🔸 Derived, 21 August 2026.
 *
 * ⭐ It is the ONLY thing that heals the *dying click*: when Mutter recreates the
 *    absolute devices while a button is pressed, that button stays
 *    down in the seat and the desktop no longer takes a click (`[M]` bench
 *    `06-b33-risveglio`).  `[R]` The only code that releases it is
 *    `drop_device()`, and it runs only on the **fall of the EIS channel**.
 *
 * ⛔ The real detach is sent by `ei_disconnect()` in `input.c`, as a protocol
 *    message — `[M]` 21 Aug 2026, faults `RG3` and `RG4`.  ⚠ **The first
 *    version of this comment said something else** ("as long as the
 *    `mutter.c` descriptor stays open Mutter does not see the detach") and
 *    it was false: it was discovered by injecting the fault.
 *
 * ⭐ What is REALLY needed from here: after the detach the descriptor set
 *   aside is dead, and only whoever has the bus and the session path can
 *   ask for a new one.  ⚠ And the `close()` inside is not the cure: it avoids
 *   leaking a descriptor at every healing.
 *
 * ⇒ If the second `ConnectToEIS` fails, the channel is gone and we return
 *   -1 saying so — `CODER.md` §4.2: degrade by declaring, not silently.
 *
 * Returns the new descriptor (which stays with this session, like the other), or
 * -1 with `sbaglio` filled in.
 */
int mutter_eis_riattacca(MutterSessione *sessione, GError **sbaglio);

/*
 * ⭐ Looks for the monitor we mounted ourselves, and says whether it found it.
 *
 * ⛔ IT MUST BE CALLED WHEN THE CAPTURE IS ALREADY ACTIVE, and the reason is measured —
 *    `[M]` 12 August 2026, and the bench found it for me on its first run against
 *    this code, not a rereading:
 *
 *      after `RecordVirtual`     ⛔ the monitor is NOT there yet
 *      after `Stream.Start`      ⛔ it is NOT there EVEN NOW, not even waiting
 *                                  three seconds
 *      when the CONSUMER has hooked on and the stream is active  ⭐ it is there
 *
 *    ⇒ Mutter creates the virtual monitor when someone really starts
 *      reading, not when it is asked.  Whoever looked for the name right after
 *      the D-Bus sequence would read "no monitor appeared" on a
 *      perfectly healthy session — which is a red on a healthy bench.
 *
 * ⚠ And the moment the name IS NEEDED is exactly this one: the scene (or
 *   the user's application) opens after the capture is live, and must be
 *   sent to THIS screen by name.
 *
 * Returns TRUE if the name is known (even if it already was), FALSE if it does not know it.
 */
gboolean mutter_monitor_cerca(MutterSessione *sessione);

/*
 * The connector of the monitor WE mounted (`Meta-1`, …) and the product
 * name Mutter gives it («Virtual remote monitor»).
 *
 * It is NULL if the two roads do not agree — the before/after diff and the product
 * name — or if the new monitors are not exactly one.  ⛔ NULL means
 * "I don't know", not "it is not there": whoever receives it declares it instead of picking
 * the most convenient one.
 */
const char *mutter_monitor_nostro(const MutterSessione *sessione);
const char *mutter_monitor_prodotto(const MutterSessione *sessione);

/*
 * How many monitors there were BEFORE mounting and how many AFTER.  They are two numbers and
 * not one: `dopo - prima != 1` is precisely the case in which the name of our
 * screen cannot be known, and must be written instead of deduced.
 */
void mutter_monitor_conteggi(const MutterSessione *sessione, guint *prima, guint *dopo);

/* ⛔⭐⭐ THE SCALE OF OUR LOGICAL MONITOR — guard 2 of `DECISIONI.md`
 *     §5.0-sexies, and it is not a diagnostic datum: it is a condition of service.
 *
 * `[M]` 14 August 2026: with `org.gnome.desktop.interface scaling-factor = 2` the
 * stream's pixels stay those requested but the LOGICAL monitor takes scale 2.0,
 * and the layout becomes `roundf(2133/2) x 2 = 2134 != 2133`.  ⛔ That layout **is
 * the coordinate space of input**: the pointer ends up elsewhere, and
 * no line says so.  It is the symptom the user described for two days.
 *
 * ⚠ We look at OUR monitor and not at the machine's worst: a laptop
 *   with a hi-dpi internal screen has no defect, and the worst would say
 *   2.0.
 * ⛔ `-1` = it could not be read, and it does NOT mean 1.0. */
double mutter_scala_nostra(const MutterSessione *sessione);

/* Stops the CONTROL — and with it the capture — and frees everything.  ⛔ Every virtual
 * monitor not unmounted stays attached to Mutter. */
void mutter_chiudi(MutterSessione *sessione);

#endif
