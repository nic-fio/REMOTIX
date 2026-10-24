/*
 * child.h — ⭐ ONE PROCESS PER USER, RUNNING AS THAT USER AND HOLDING THE STAGE.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, WITH THE MEASURE NEXT TO IT
 *
 * `DECISIONS.md` §1.10-bis, 12 Aug 2026, from the user, in front of the
 * measure of phase 2's assembly (`fasi/rapporti/P2-6-montaggio.md` §5.4):
 *
 *   `[M]` ⛔ **root does not connect to the user's session bus**
 *         sudo env XDG_RUNTIME_DIR=/run/user/1000 \
 *              DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
 *              gdbus call --session --dest org.gnome.Mutter.ScreenCast …
 *         → "Error connecting: The connection is closed", exit 1
 *
 *   `[M]` ⛔ **only root can verify someone else's password with PAM**:
 *         `pam_unix` outside root goes through `unix_chkpwd`, which verifies
 *         only the password of WHOEVER INVOKES IT.
 *
 * ⇒ The two things **do not live in the same process**, and it is not an
 *   implementation detail: without the bus there is no capture, without root
 *   there is no authentication.  The server stays **privileged**, and for
 *   every admitted user it spawns a **child running as that user**, which
 *   holds their session bus, their capture and their devices.
 *
 * ---------------------------------------------------------------------------
 * ⭐ IT IS THE HELPER OF §1.10 THE OTHER WAY ROUND — the same rule, one job per
 *    process.  ⛔ BUT THREE THINGS ARE DIFFERENT, AND THEY MUST BE SAID FIRST
 *
 * The helper (`helper.h`) is a child **less** privileged than the parent
 * that does the thing that blocks; this is a child **differently** privileged
 * that does the thing the parent cannot do.  Hence:
 *
 *   1. ⛔ **It CANNOT be started early.**  The helper is born before
 *      `transport_open()` on purpose, because a `fork()` hands the child all
 *      the descriptors and a helper started later would carry the port along.
 *      The child is born **when a user has been admitted**, that is
 *      necessarily after the listeners.  ⇒ What the helper buys with the
 *      MOMENT, this one buys with `close_range()`: as soon as it is born it
 *      closes **everything** except the three standard ones and its own
 *      socket, and the bench reads it from `/proc/<pid>/fd` — it does not
 *      infer it.
 *
 *   2. ⛔ **Identity is not a promise of the code: it is a fact of the
 *      kernel.**  A helper answering "yes" for a lost message is I3 violated
 *      and it shows; a child running **as the wrong user** is I3 violated
 *      **invisibly** — the pixels arrive, they are beautiful, and they are
 *      someone else's.  ⇒ The parent's socket has `SO_PASSCRED`, and the
 *      kernel stamps **every message** with the sender's **real**
 *      pid/uid/gid (`SCM_CREDENTIALS`).  The parent compares them with the
 *      uid it resolved from the name of the RCP session's user **on every
 *      message**, not at opening.  ⭐ It is the helper's case number, with a
 *      notary: we write the case, the kernel writes the credentials, and an
 *      unprivileged process **cannot declare false ones**.
 *
 *   3. ⛔ **It outlives the detach** (invariant I4).  The helper has no
 *      memory — one transaction and it dies.  This is the STAGE: capture,
 *      virtual monitor, devices.  ⚠ What dies when the network falls is not
 *      it: the child dies when the server dies (`PR_SET_PDEATHSIG` **and** the
 *      EOF on the socket, two independent roads because the first is lost
 *      when the credentials change).
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE INVARIANTS, AND WHERE IT CAN BE READ THAT THEY ARE RESPECTED
 *
 * | I3 | the guard starts from denied | every road that does not lead to a
 * |    |                              | message signed by the kernel with the
 * |    |                              | EXPECTED uid is a no:
 * |    |                              | `credentials_match()`, and there
 * |    |                              | is no second place saying yes         |
 * | I4 | the stage belongs to the     | no line of this file ties a child's
 * |    | session                      | life to a connection: it dies through
 * |    |                              | `children_turn_off()` and nothing else     |
 * | I2 | one session per user         | `children_ensure()` searches BEFORE
 * |    |                              | spawning: two connections of the same
 * |    |                              | user find the same child              |
 * | I7 | the protection lives in the  | the privilege drop is VERIFIED with
 * |    | program                      | `getresuid()` — asked of the kernel —
 * |    |                              | and a child that did not really drop
 * |    |                              | exits                                 |
 *
 * ---------------------------------------------------------------------------
 * ⛔ AND WHAT THIS FILE DOES NOT DO, DECLARED INSTEAD OF DISCOVERED
 *
 *   · **it does not make a graphical session be born**.  If the admitted user
 *     has no `/run/user/<uid>` — that is they never logged in on that machine
 *     — the child SAYS so and stays without a stage.  Making it be born needs
 *     `pam_open_session` (that is `pam_systemd`, which creates the logind
 *     session and the runtime folder), and it is the real login's decision:
 *     not this one's;
 *   · **it sends nothing on the wire**.  It delivers the bytes to the parent,
 *     which is the only one holding the connections;
 *   · **it does not look inside the codec's bytes**: that belongs to the
 *     encoder.
 */
#ifndef REMOTIX_CHILD_H
#define REMOTIX_CHILD_H

#include <poll.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

/* ⛔ The log area lives HERE and not in `log.h`: that file does not belong
 *    to this mandate, and `registro_dice()` takes any string.  ⚠ The day
 *    `log.h` can be touched, this line goes there next to the others —
 *    as happened to `LOG_SESSION`, which lived in `session.h` until 12 Aug
 *    2026. */
#define LOG_CHILD "child"

typedef struct children children;

/* ⛔ How the parent receives a frame from the child.  ⚠ `user` and `uid` are
 * BOTH there on purpose: the name is the one with which the RCP session asked
 * to enter, the uid is the one the **kernel** stamped on the message, and
 * whoever delivers must be able to refuse if the two have come apart. */
/* ⛔⭐ `key` ARRIVED WITH PHASE 3, AND IT IS NOT AN EXTRA FIELD.
 *
 *     Until phase 2 the receiver marked `key = true` **by construction**,
 *     because the frame was a single one and necessarily a keyframe.  ⛔ With
 *     prediction between frames that line becomes **a lie on the wire**: §6.2
 *     writes that value in the `kind` field, and a delta marked `0x0301` makes
 *     the client reconfigure a decoder on an image that does not decode on its
 *     own.  ⇒ What travels here is what the encoder READ from the stream, not
 *     what one hopes. */
/* ⭐⭐ AND `input` ARRIVED WITH PHASE 4, for the same reason `key` arrived
 *     with phase 3: without it, the `input` field of §6.2 would be **0 by
 *     construction** — and it is exactly what it was, `input = 0` in 953
 *     frames out of 953 (`README.md`, 13 Aug 2026).
 *
 * ⛔ And the CHILD fills it, not the parent: only the child knows what the
 *    compositor really took, and at what instant it captured.  Filling it here
 *    would say "the last input sent to the stage", which is a higher number
 *    and would make the latency link measure a latency shorter than the real
 *    one — in our favour, which is the direction in which one never errs by
 *    accident. */
typedef void (*ChildRepository)(void *ctx, const char *user, uid_t uid,
                               uint8_t codec, bool key, const uint8_t *data,
                               size_t byte, uint32_t width,
                               uint32_t height, uint64_t instant_us,
                               uint32_t input);

/* ⛔ A child has gone.  It serves the parent to release what was its own — for
 * example the video deposit, which today belongs to the PROCESS (see the box
 * of `video_forse()` in `webtransport.c`): a deposit that outlives the child
 * that filled it is the image of a user who stays in the house. */
typedef void (*ChildFarewell)(void *ctx, const char *user, uid_t uid);

/* ⭐⭐ PHASE 7 — AN ALREADY ENCODED AUDIO BLOCK, from the session to the wire.
 *
 * ⛔ It arrives **encoded**, not raw, and the reason is a number: 20 ms of
 *    stereo PCM are 3840 bytes, the same block in Opus measures `[M]` 241-439.
 *    Shipping raw would cost ten times the socket, fifty times a second — on
 *    a path that `CODER.md` §1-bis says to measure in latency, not in the
 *    writer's convenience.
 *
 * `codec`      1 = Opus, 2 = PCM.  ⚠ They are the numbers of `RCP.md` **§6.3**,
 *              and NOT those of §6.2: there 1 is HEVC.  The coincidence of the
 *              values is a trap, and whoever swapped the two tables would get a
 *              formally valid datagram with the wrong codec inside.
 * `instant_us` the child's monotonic clock, of the FIRST sample of the block.
 *              ⛔ The child sets it for the same reason it sets `input` in
 *              frames: it is the only one that knows **when** the samples were
 *              taken.  The parent would only know when they arrived, which is
 *              a higher number and always in our favour.
 * `data`       lives ONLY inside the call: whoever wants to keep it copies it.
 */
typedef void (*ChildBlock)(void *ctx, const char *user, uid_t uid,
                             uint8_t codec, uint64_t instant_us,
                             const uint8_t *data, size_t byte);
void children_hook_block(children *f, ChildBlock fn, void *ctx);

/*
 * "Capture this user's audio, and encode it like this" — or "stop".
 *
 * `codec` 1 = Opus, 2 = PCM, **0 = off**.  ⛔ Zero is not an implicit sentinel:
 *         it is the value §4.3/§6.3 reserve for "no codec negotiated", and
 *         here it means the same thing — nobody is listening.
 *
 * ⚠ Turning off stops the CAPTURE, not the sink: the device applications play
 *   on belongs to the session (invariant I4, like the stage), and making it
 *   vanish at every detach would cut the sound for whoever is listening inside
 *   the session and leave the applications already open on a dead device.
 */
bool children_audio(children *f, const char *user, uint8_t codec);

/* ------------------------------------------------------------------------- */
/* ⭐⭐ PHASE 7 — THE CLIPBOARD, and it crosses the boundary for the FOURTH time
 *     for the same reason as video, input and audio:
 *
 *       **the clipboard belongs to the compositor, and the compositor talks to
 *       the user's session, which is in the CHILD**; the messages of `RCP.md`
 *       §7.4 are written by the parent, which holds QUIC.
 *
 * ⛔ TEXT ONLY — `DECISIONS.md` §5-ter.1, decided by the user on 9 Aug 2026
 *    and confirmed again on the 17th.  MIME types do not cross the socket: they
 *    live in `clipboard.c` and do not leave it (`src/clipboard.h`).
 *
 * ⛔ AND THE TEXT GOES IN PIECES, like the frame and the cursor: the cap of §5.4
 *    is **1 000 000 bytes**, thirty times `MAX_PIECE`.
 */

/*
 * ⭐ "THE SESSION HAS COPIED THIS TEXT" — the desktop → device direction.
 *
 * ⛔ It arrives ALREADY READ, already validated as UTF-8 and already within the
 *    cap of §5.4: those three checks are in `clipboard.c`, where the text still
 *    exists whole and where it is known **which** of the reasons made it fail.
 *    ⚠ A text over the cap does not arrive here at all — §5.4 says "it is not
 *    announced", and the line is in the child's log.
 *
 * `text` is zero-terminated and lives ONLY inside the call.
 */
typedef void (*ChildClipboardText)(void *ctx, const char *user, uid_t uid,
                                   const char *text, size_t byte);

/*
 * ⭐ "SOMEONE IN THE SESSION IS PASTING" — the device → desktop direction, and
 *    it is the half used most (`DECISIONS.md` §5-ter.1).
 *
 * ⛔⛔ IT MUST ALWAYS BE ANSWERED, with `children_clipboard_response()`, even
 *      empty-handed and even if the client never answers.  A
 *      `SelectionTransfer` without an answer leaves the pasting application
 *      hanging **indefinitely**, and what the user sees is a frozen desktop —
 *      a defect nobody connects to the clipboard.  ⇒ Whoever receives this
 *      callback keeps a timeout.
 *
 * `serial` is Mutter's number, and must be returned as is.
 */
typedef void (*ChildClipboardRequest)(void *ctx, const char *user, uid_t uid,
                                       uint32_t serial);

/* ⚠ The two hooks are attached together or not at all: a parent that could
 *   receive the session's text and could not needs whoever pastes would leave
 *   the desktop **worse than it found it** — see above. */
void children_hook_clipboard(children *f, ChildClipboardText text,
                          ChildClipboardRequest request, void *ctx);

/*
 * "THE CLIENT HAS TEXT IN ITS CLIPBOARD": the child offers it to the session,
 * and from there on someone will be able to paste it.
 *
 * ⛔ It does NOT carry the text, and it is not an oversight: it is §7.4's
 *    "announce first, then pull" applied on this side.  The text is requested
 *    when someone really pastes — that is with `ChildClipboardRequest` — and
 *    whoever copies a whole document on the phone sends it to nobody until
 *    that moment comes.
 */
bool children_clipboard_offer(children *f, const char *user);

/*
 * The answer to a `ChildClipboardRequest`.  With `text` NULL it declares not
 * having it — ⛔ **which is still an answer**, and it is the one that unblocks
 * whoever is pasting.
 */
bool children_clipboard_response(children *f, const char *user, uint32_t serial,
                            const char *text, size_t byte);

/* ⭐⭐ PHASE 4 — THE CURSOR SHAPE, and it crosses the boundary in the opposite
 *     direction to input: the metadata comes from PipeWire (that is in the
 *     child) and the `CURSOR_SHAPE` channel (`RCP.md` §7.2) lives in the
 *     parent.
 *
 * ⛔ `bitmap` is premultiplied BGRA, `width x height x 4` bytes, and
 *    lives ONLY inside the call: whoever wants to keep it copies it.
 * ⛔ `0x0` with `bitmap` NULL = **hidden cursor** (§5.5), and it must be
 *    delivered as a message: it is the only way the client has of knowing the
 *    pointer has vanished, instead of drawing the last shape forever.
 * ⚠ The POSITION does not pass through here and does not pass anywhere in
 *   this direction: it belongs to the client, which draws the pointer itself
 *   (`SPECS.md` §7.1). */
typedef void (*ChildCursor)(void *ctx, const char *user, uid_t uid,
                              uint16_t width, uint16_t height,
                              int16_t active_x, int16_t active_y,
                              const uint8_t *bitmap, size_t byte);

/* ⭐⭐ §7.1 — THE ANSWER TO THE CANVAS, and it crosses the boundary in the
 *     cursor's direction: the question goes out with `children_recanvas()`, the
 *     answer comes back through here.
 *
 * ⛔ WHY LOOKING AT THE FRAMES WAS NOT ENOUGH, which is what the first draft
 *    of this chain did: from the frame one sees that the size changed,
 *    ⚠ but not **which request it answers** — and the three cases that cannot
 *    be told apart by looking at the pixels are all frequent:
 *
 *      · the stage ALREADY has that size ⇒ no new frame will arrive, and
 *        whoever waits would wait for the three-second deadline for nothing;
 *      · the stage is not there or did not make it ⇒ the fact is known AT
 *        ONCE, over there;
 *      · two chained requests — the user dragging the edge — ⇒ the frame of
 *        the FIRST would be taken as the answer to the SECOND, and the desktop
 *        would settle on the wrong size **without any count noticing**.
 *
 * `voluta_*`  the size that had been asked of the stage: it serves to
 *             recognise the request, not to declare an outcome.
 * `avuta_*`   what the stage really has.  ⛔ `0x0` = **it did not make it**, and
 *             it is a different fact from "it is trying" (`CODER.md` §3.10).
 *
 * ⚠ And it arrives even when nobody had asked for anything: the stage can
 *   change size by itself (a remount after a fall of the graphical session).
 *   The receiver decides what to do with it — here a fact is reported. */
typedef void (*ChildCanvas)(void *ctx, const char *user, uid_t uid,
                           uint32_t intended_w, uint32_t intended_h, uint32_t got_w,
                           uint32_t got_h);

/* Switches on the children table.  ⛔ It spawns nothing: here it is not yet
 * known who will enter.
 *
 * `canvas_w`/`canvas_h`  the size with which the child will open capture and
 *                    encoding — the same constant as `main.c`, passed instead
 *                    of copied (`P2-1-sessione.md` §6.3: "or in two weeks they
 *                    will be three places").
 * `dir_survey`      where the child writes the raw data and the streams, or
 *                    NULL.  ⚠ **The child** writes there, that is the user: if
 *                    the folder is not theirs, the survey does not come out
 *                    and the line says so. */
/* ⭐⭐ §7.6 — "THIS USER'S GRAPHICAL SESSION IS OVER", and no client asked for
 *     it: the user chose "Log out…" from the desktop menu.
 *
 * ⛔ It is the twin of `TERMINATE_SESSION` seen from the other direction: there
 *    the order comes from the wire, here the fact comes from the desktop.
 *    ⚠ In both cases whoever is watching must receive `0x10
 *    SESSION_TERMINATED` — and not the thirty seconds of silence followed by
 *    "network error", which is what would happen by keeping quiet (finding
 *    B-7).
 *
 * ⚠ It is registered separately instead of lengthening `children_turn_on()`: that
 *   signature already has four callbacks, and a fifth parameter on a line of
 *   six would no longer be read by anyone. */
typedef void (*ChildSessionFinished)(void *ctx, const char *user, uid_t uid);

/* ⭐ §7.1 — "the stage is not there YET": the child SAYS so, and the parent
 * postpones the deadline instead of inferring a failure from silence. */
typedef void (*ChildCanvasWait)(void *ctx, const char *user, uid_t uid,
                                  uint32_t intended_w, uint32_t intended_h);
void children_hook_canvas_wait(children *f, ChildCanvasWait fn, void *ctx);
void children_hook_session_finished(children *f, ChildSessionFinished fn, void *ctx);

children *children_turn_on(uint32_t canvas_w, uint32_t canvas_h, const char *dir_survey,
                     ChildRepository deposit, ChildFarewell dismiss,
                     ChildCursor cursor, ChildCanvas canvas, void *ctx);

/*
 * ⭐⭐⭐ THE **THREE** CURES OF PHASE 9 THAT LIVE ON THE OTHER SIDE — 23 Aug
 *      2026, and the third (audio silence) arrived on the 24th.
 *
 * ⛔ THE PROBLEM IT SOLVES, and it is the only reason this function exists:
 *    `encoder_quality_rises()`, `codificatore_tetto_banda()` and
 *    `audio_silence_hush()` are decisions of the **server**, but neither the
 *    video encoder nor the audio one runs in the server — they run in the
 *    CHILD, which is not a `fork` but an `execve` with the environment
 *    composed from scratch (`child.c`, point 5 of `become_and_exec()`).
 *    ⇒ An environment variable **does not arrive**, and calling the setters
 *    here would turn the cure on in the wrong process: the one that never
 *    opens an encoder.
 *
 * ⭐ THE ROAD IS THAT OF `--verbose`, already paid for dearly on 16 Aug
 *    2026: the value is put on the **child's command line**, and the child
 *    repeats it to itself as soon as it is born.  Nothing else crosses.
 *
 * `quality_recovery`     quality climbs back instead of staying low (I6).
 * `bandwidth_cap_mbit`   the **floor** in Mbit/s from which the encoder derives
 *                      wire, working point and reservoir; `0` = off.
 * `audio_silence`     ⭐ an all-zero audio block does not become a datagram.
 *                      **`true` is the default** since 24 Aug 2026 (the user's
 *                      decision), and it is turned off with
 *                      `--no-audio-silence`.  ⚠ `main.c` calls it with the
 *                      SAME value it passes to `audio_silence_hush()` for
 *                      itself: the test tone opens an encoder in the server,
 *                      and two different values would be two different
 *                      products.
 *
 * ⚠ It is registered separately instead of lengthening `children_turn_on()`, for
 *   the reason already written above `ChildSessionFinished`: that signature
 *   already has four callbacks.
 * ⛔ It holds for the children born AFTER: it is called at startup, before PAM
 *    can say yes to anyone.  ⚠ And the one declaring the value in force is
 *    neither this file nor `main.c`, but `encoder.c` when each encoder
 *    opens — that is whoever really uses it.  An option lost in the parent →
 *    child hand-over has exactly the same face as a cure that does not work,
 *    and those lines are the only place where the two separate.
 */
void children_phase9(children *f, bool quality_recovery, uint32_t bandwidth_cap_mbit,
                 bool audio_silence);

/* ⛔ Shuts down all the children and waits until they are dead.  ⚠ It WAITS,
 * and it must be said: it sits **after** the last round of the `poll` loop,
 * like `helper_turn_off()` — `CODER.md` §4.4 forbids waiting INSIDE the loop,
 * not after. */
void children_turn_off(children *f);

/* ⛔⭐ IT IS CALLED WHEN PAM HAS SAID YES, AND NOT AN INSTANT BEFORE (invariant
 *     I3).  A child born on `CREDENTIALS` would run as a user who has not yet
 *     proven to be who they are.
 *
 * ⛔ I2 — "only one graphical session per user": if that user's child already
 *    exists and still answers, this function **does not spawn a second one**
 *    and returns `true` anyway.  Two connections of the same user see the same
 *    stage, which is precisely what I4 says.
 *
 * ⛔ `false` means "there is no child for that user", and the caller must not
 *    treat it as "maybe": no stage, no pixels.  The roads leading here are
 *    listed in `child.c`, function `children_ensure`. */
bool children_ensure(children *f, const char *user);
/* ⭐ PHASE 17 T6: the same, with the client's (bare) address that the child's
 *    PAM session receives as `PAM_RHOST`, like sshd's (logind: `RemoteHost`).
 *    NULL or "" ⇒ "remotix", as before. */
bool children_ensure_from(children *f, const char *user, const char *rhost);

/* The descriptors to put in the `poll`.  Returns how many it wrote. */
size_t children_descriptors(children *f, struct pollfd *fds, size_t max);

/* ⛔ Reads what the children have to say, verifying the kernel's credentials
 * **on every message**.  ⚠ It is called even when no descriptor is readable:
 * in here the waits expire and the dead are reaped, and a deadline that waits
 * for a byte is a deadline that never fires — the lesson of `rule_heartbeat`,
 * paid on 11 August with B6 and paid again by the helper. */
void children_move(children *f, struct pollfd *fds, size_t n, uint64_t now_ms);

/* How many children are alive now.  For the log and for the bench. */
int children_count(const children *f);

/* ⭐⭐ The user name of the `which`-th live stage (0 … `children_count()−1`), or
 *     `NULL`.  ⛔ It serves the BUDGET (phase 10) to know **who is inside**,
 *     and the right set is this one and not the slots of the RCP registry: a
 *     session that left its slot through silence **still encodes** as long as
 *     its stage is alive (§3.2, the *ghost*), and costs as much as the others.
 * ⚠ The index is not stable between two calls: it is scanned once only. */
const char *children_nth_user(const children *f, int which);

/* ⛔ For the bench: the pid of that user's child, or -1.  ⚠ It serves
 * `benches/02-child-*` to ask the KERNEL who that process is
 * (`/proc/<pid>/status`) instead of inferring it from `pgrep`, which would
 * also find the children of the other benches' servers. */
pid_t children_pid_of(const children *f, const char *user);

/* ⛔⭐ ASKS THAT USER'S CHILD TO SEND ITS FRAME AGAIN.
 *
 *     ⚠ It is needed because the video deposit, in `webtransport.c`, is **one
 *     per PROCESS**: when another user enters the parent empties it (or it
 *     would deliver the first one's pixels to them), and the first — who still
 *     has their child alive — must be able to have it sent again.
 *
 * ⛔ The child sends **the same** frame again, not a new one: phase 2 is a
 *    still image, and recapturing here would deliver two different images
 *    under the same label.
 *
 * `false` = there is no child for that user, or the request did not go out —
 * and then that session will see nothing, declared. */
bool children_ask_stage(children *f, const char *user);

/* ⛔⭐ PHASE 3 — "CAPTURE CONTINUOUSLY", AND "THIS ONE MUST BE A KEYFRAME".
 *
 *     It is the parent half of the seam that did not exist at phase 2:
 *     `codificatore_chiedi_chiave()` had **no caller in the product**, so a
 *     client's `REQUEST_KEY` turned on a `bool` in `rcp.c` and produced no
 *     keyframe — and with `chiavi_ogni = 0` (infinite GOP) after the first
 *     keyframe not a single one ever arrived again.
 *
 * `codec`  1 = HEVC, 2 = AV1, and ⛔ **0 = stop capturing**.  It is not an
 *          implicit sentinel: it is the value §4.3/§6.2 give to "no codec
 *          negotiated", and here it means the same thing — nobody is watching.
 * `key` §5.2: the next frame of that codec MUST be a keyframe.
 *
 * ⚠ The one who decides is neither this file nor `main.c`: it is
 *   `webtransport.c`, which knows when `SESSION` went out and when §5.2 opens
 *   the debt.  `main.c` acts as the bridge because it is the only one that
 *   knows both sides. */
/* ⛔⭐ `depth` (8 or 10, `0` = not negotiated) arrived on 17 Aug 2026:
 *     without it, the child wrote it by itself and the stream came out at a
 *     depth DIFFERENT from the one declared in `HERE_I_AM` (§4.3).  The full box
 *     is on `struct body_video` in `child.c`. */
/* ⛔⭐ `livello_x10` (in tenths: `5.1` ⇒ 51, `0` = not declared) arrived on
 *     23 Aug 2026 for the twin reason: `[M]` at 3840x2160 the client declared
 *     5.1 and the server produced **5.2** — §4.3 line 701 is a MUST.
 *     ⚠ `0` means "no ceiling", not "low". */
bool children_video(children *f, const char *user, uint8_t codec,
                 uint8_t depth, uint8_t livello_x10, bool key);

/* ⭐⭐ PHASE 4 — INPUT CROSSES THE PROCESS BOUNDARY.
 *
 * ⛔ The reason is a fact of the architecture, not a choice: `libei` talks to
 *    the user's graphical session, and **the child** has that session; QUIC,
 *    RCP and the client's bytes are in the **parent**.  ⇒ Between the key
 *    pressed in the browser and the key pressed on the desktop there is a
 *    process boundary, and this is the function that crosses it.
 *
 * ⚠ The one who decides is not this file: it is `rcp.c`, which has already
 *   validated the message according to `RCP.md` §7.3 — ranges, surrogates,
 *   coordinates on the canvas, increasing `id`.  ⛔ Here nothing is
 *   revalidated and nothing is transformed: two checks on the same value in
 *   two places become two different rules the day one of the two changes.
 *
 * ⛔ AND THE WHEEL'S SIGN IS NOT TOUCHED HERE EITHER: it is inverted only once,
 *    inside `input_wheel()` (`src/input.h`, `RCP.md` §7.3).
 *
 * `id`      §7.3, the message identifier.  ⭐ It is what comes back in the
 *           `input` field of frames (§6.2) — but **only if the compositor takes
 *           it**: the child advances its counter when the injection succeeded,
 *           not when the request went out.
 * `code`  evdev (`BTN_LEFT` = 0x110, `KEY_A` = 30), for button and position.
 * `a`/`b`   pointer: `x`/`y` on the canvas · wheel: the axes in units of 120
 *           · letter: the Unicode scalar value in `a` · recanvas: the new canvas.
 *
 * `false` = there is no child for that user, or the request did not go out —
 * ⛔ and then that input did not reach the desktop, which is DECLARED in the
 * log instead of being hushed up (`CODER.md` §4.2). */
enum {
	CHILDREN_INPUT_POINTER = 1,
	CHILDREN_INPUT_BUTTON = 2,
	CHILDREN_INPUT_WHEEL = 3,
	CHILDREN_INPUT_LETTER = 4,
	CHILDREN_INPUT_POSITION = 5,
	/* ⛔⭐ "The rule with the highest damage/cost ratio of the document"
	 *     (`RCP.md` §11): at detach EVERYTHING is released.  A Ctrl left down
	 *     in a session that outlives the client makes the desktop unusable at
	 *     reattach, and nobody connects the two things. */
	CHILDREN_INPUT_RELEASE_ALL = 6,
	/* ⛔ §7.1: the canvas in force has changed, remap the absolute pointer
	 *    region.  Without it, `rcp.c` saturates on the new canvas and the stage
	 *    stays on the old one — two sides with two truths and no error. */
	CHILDREN_INPUT_RECANVAS = 7,
	/* ⭐ §7.6 of `RCP.md` — "the user asked to LOG OUT".  ⛔ It is not a gesture
	 *    and it is not injected: it travels in this envelope for the same
	 *    reason as `RITELA` — a single envelope between parent and child, a
	 *    single branch to read — and like that one it goes BEFORE the gestures
	 *    guard. */
	CHILDREN_INPUT_TERMINATE = 8
};

/* ⭐⭐ §5-bis.7 — the layout declared by the client enters the session.
 *     ⛔ `true` = the request WENT OUT, not "it is in force": the one
 *     ascertaining it is the child's «KEYMAP CHANGED» line, after Mutter has
 *     destroyed and recreated the keyboard device. */
bool children_layout(children *f, const char *user, const char *name);

/* ⏳ `RCP.md` §13 (PROPOSED, `DECISIONS.md` §11.32) — the frame-rate ceiling
 *    the client's decoder asked for, already clamped by `rcp.c` (0 = none).
 *    ⛔ The child applies it BEFORE encoding: it takes fewer frames from the
 *    capture, so the delta chain stays whole and no keyframe is owed.  A
 *    keyframe owed is never held back.  `true` = the request WENT OUT. */
bool children_pace(children *f, const char *user, uint16_t max_fps);

bool children_input(children *f, const char *user, uint32_t id, uint8_t action,
                 uint16_t code, int pressed, int32_t a, int32_t b);

/* ⭐⭐ "THE SERVER'S CANVAS TAKES THE SIZE OF THE CLIENT'S CANVAS" — the chain
 *     that was missing on 14 Aug 2026, and with it four symptoms
 *     (`DECISIONS.md` §5.0-sexies, `fasi/rapporti/F4-IN-12`):
 *
 *   · the black side bands         the two canvases match ⇒ nothing to lay out
 *   · the interpolated text        scale 1 ⇒ nobody resamples the image
 *   · reattaching at a different   `[M]` Mutter changes live in 41.6 ms,
 *     size                         labwc in 5.1 ms
 *   · ⭐⭐ the 4 seconds between    `pw_stream_update_params()` IS a restart of
 *     login and desktop            the stream, and a restart DELIVERS a buffer:
 *                                  on Wayland the compositor sends only when
 *                                  the scene changes, and a freshly switched-on
 *                                  desktop is still (`[M]` 4.4 s, 659 "empty
 *                                  waits")
 *
 * ⛔ Returns `true` when the QUESTION went out, ⚠ not when the canvas changed:
 *    between the two there is a compositor that can grant something else
 *    (§4.5), say "succeeded" without doing anything (`[M]` labwc) or not make
 *    it.  ⇒ Whoever waits for the outcome reads it in the FRAME: it is the
 *    first one that arrives at the new size, and the `width`/`height`
 *    field of `ChildRepository` carries it. */
/* ⭐ "END THIS USER'S GRAPHICAL SESSION" — `RCP.md` §7.6, the second of the
 * two exits of `DECISIONS.md` §4.1-ter.  ⛔ It is not the detach: here the
 * user's programs are closed, and at the next attach a NEW session is born.
 * `false` = there is no child for that user, or the request did not go out —
 * and then the session will NOT end. */
/* ⛔⭐ AND THE REASON TRAVELS WITH THE MESSAGE — 16 Aug 2026, and before it did
 *     not.
 *
 *     The child wrote "⭐ §7.6: the user asked to LOG OUT" **for every**
 *     closing, because the only one asking it was §7.6.  ⛔ From the moment
 *     the abandonment clock (§5.3) also asks it, that line asserts a cause it
 *     does not know — and `[M]` it asserted it at the first round of the test,
 *     with no user having asked for anything.
 *
 * ⚠ No new message is needed: field `a` of the envelope was free. */
enum {
	CHILDREN_EXIT_USER = 0,   /* §7.6: a person asked for it */
	CHILDREN_EXIT_ABANDON = 1 /* §5.3: the ceiling expired, nobody asked for it */
};

bool children_terminate_session(children *f, const char *user, int why);

bool children_recanvas(children *f, const char *user, uint32_t width,
                  uint32_t height);

/* ⛔⭐ ASKS EVERY CHILD "WHO ARE YOU", at most once a minute.
 *
 *     ⚠ It is needed so that "verified on every message" is a protection even
 *     when there are no messages: a child that delivered its frame and then
 *     falls silent would stay verified **only once, at the start** — that is
 *     exactly what §1.10-bis forbids.  ⭐ The answer goes through
 *     `credentials_match()` like all the others, and a child that in the
 *     meantime were no longer that uid would be killed there.
 *
 * ⚠ The OK outcome line is in the chatter (`log_detail`): one per
 *   minute per child would fill the log with green.  The disagreement does
 *   not: that one is always written. */
void children_recheck(children *f, uint64_t now_ms);

/* ⛔⭐ THE CHILD'S ENTRY POINT — `main.c` gets here as the FIRST thing, when
 *     `argv[1]` is `--internal-child`, and it never returns.
 *
 *     ⚠ It is an INTERNAL command line: `children_ensure()` writes it and
 *     `child_alive()` reads it.  Whoever typed it by hand would get a process
 *     talking on a descriptor 3 that does not exist, and it would die there —
 *     there is nothing to gain, because the child has no privilege to give
 *     away: it is the user themselves. */
void child_alive(int argc, char **argv);

/* ⭐ PHASE 17 — `remotix --encoding-test` (the certification, §6.0 phase 7a):
 *    a synthetic 256x256 frame in H.264 with the same choice as a real session
 *    (VA-API on the session's node; ⛔ since phase 19 no software fallback).
 *    It writes ONE JSON line on stdout —
 *    {"outcome":"hardware"|"none","encoder":…,"node":…,"reason":…,
 *     "codec":…,"offered":…,"hevc":…,"h264":…}
 *    — and returns the exit code: 0 the card encodes · 1 the card opens but
 *    the frame does not come out · 2 usage error · 3 NO CARD can encode
 *    (declared refusal).  No network, no sessions; root is not needed (but the
 *    node's groups are).
 * ⭐ PHASE 18: the arguments following `--encoding-test` (all optional):
 *    `h264`|`hevc`, `--node /dev/dri/renderDN`, and ⭐ phase 19
 *    `--encoding-route card|vulkan|vaapi`.  The JSON also carries `route`,
 *    `hevc_strada` and `h264_strada` ("vulkan"/"vaapi"): WHICH route of the
 *    card encoded. */
int child_test_encoding(int argc, char **argv);

/* ⭐ PHASE 19 (`DECISIONS.md` §10.27) — the card's route: "card" (by
 *    capability: Vulkan Video if available for that codec, otherwise VA-API —
 *    the default and what the product does), "vulkan" or "vaapi" (forced, for
 *    tests and diagnosis).  Returns false on a name that is not one of the
 *    three, and then nothing changes.  The parent passes it to the child on
 *    the command line (`--encoding-route`), like the phase 9 cures. */
bool child_encoding_route(const char *route);
const char *child_encoding_route_requested(void);

/* ⭐ PHASE 18 — the test AT THE PARENT'S STARTUP: what this machine can
 *    encode, in a separate process (a crashing driver does not bring down the
 *    server).  `offered` is the list for HERE_I_AM's `video.codec` ("hevc,h264"
 *    · "hevc" · "h264" · "" = nothing), `explanation` the line for the log
 *    with the reason for each "no".  Returns false if nothing is offered. */
bool child_video_capabilities(char *offered, size_t offered_bytes, char *explanation,
                           size_t explanation_byte);

#endif
