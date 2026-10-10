/*
 * figlio.h — ⭐ ONE PROCESS PER USER, RUNNING AS THAT USER AND HOLDING THE STAGE.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, WITH THE MEASURE NEXT TO IT
 *
 * `DECISIONI.md` §1.10-bis, 12 Aug 2026, from the user, in front of the
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
 * The helper (`aiutante.h`) is a child **less** privileged than the parent
 * that does the thing that blocks; this is a child **differently** privileged
 * that does the thing the parent cannot do.  Hence:
 *
 *   1. ⛔ **It CANNOT be started early.**  The helper is born before
 *      `trasporto_apri()` on purpose, because a `fork()` hands the child all
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
 * |    |                              | `credenziali_combaciano()`, and there
 * |    |                              | is no second place saying yes         |
 * | I4 | the stage belongs to the     | no line of this file ties a child's
 * |    | session                      | life to a connection: it dies through
 * |    |                              | `figli_spegni()` and nothing else     |
 * | I2 | one session per user         | `figli_assicura()` searches BEFORE
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
#ifndef REMOTIX_FIGLIO_H
#define REMOTIX_FIGLIO_H

#include <poll.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>

/* ⛔ The log area lives HERE and not in `registro.h`: that file does not belong
 *    to this mandate, and `registro_dice()` takes any string.  ⚠ The day
 *    `registro.h` can be touched, this line goes there next to the others —
 *    as happened to `REG_SESSIONE`, which lived in `sessione.h` until 12 Aug
 *    2026. */
#define REG_FIGLIO "figlio"

typedef struct figli figli;

/* ⛔ How the parent receives a frame from the child.  ⚠ `utente` and `uid` are
 * BOTH there on purpose: the name is the one with which the RCP session asked
 * to enter, the uid is the one the **kernel** stamped on the message, and
 * whoever delivers must be able to refuse if the two have come apart. */
/* ⛔⭐ `chiave` ARRIVED WITH PHASE 3, AND IT IS NOT AN EXTRA FIELD.
 *
 *     Until phase 2 the receiver marked `chiave = true` **by construction**,
 *     because the frame was a single one and necessarily a keyframe.  ⛔ With
 *     prediction between frames that line becomes **a lie on the wire**: §6.2
 *     writes that value in the `tipo` field, and a delta marked `0x0301` makes
 *     the client reconfigure a decoder on an image that does not decode on its
 *     own.  ⇒ What travels here is what the encoder READ from the stream, not
 *     what one hopes. */
/* ⭐⭐ AND `input` ARRIVED WITH PHASE 4, for the same reason `chiave` arrived
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
typedef void (*FiglioDeposito)(void *ctx, const char *utente, uid_t uid,
                               uint8_t codec, bool chiave, const uint8_t *dati,
                               size_t byte, uint32_t larghezza,
                               uint32_t altezza, uint64_t istante_us,
                               uint32_t input);

/* ⛔ A child has gone.  It serves the parent to release what was its own — for
 * example the video deposit, which today belongs to the PROCESS (see the box
 * of `video_forse()` in `webtransport.c`): a deposit that outlives the child
 * that filled it is the image of a user who stays in the house. */
typedef void (*FiglioCongedo)(void *ctx, const char *utente, uid_t uid);

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
 * `istante_us` the child's monotonic clock, of the FIRST sample of the block.
 *              ⛔ The child sets it for the same reason it sets `input` in
 *              frames: it is the only one that knows **when** the samples were
 *              taken.  The parent would only know when they arrived, which is
 *              a higher number and always in our favour.
 * `dati`       lives ONLY inside the call: whoever wants to keep it copies it.
 */
typedef void (*FiglioBlocco)(void *ctx, const char *utente, uid_t uid,
                             uint8_t codec, uint64_t istante_us,
                             const uint8_t *dati, size_t byte);
void figli_gancio_blocco(figli *f, FiglioBlocco fn, void *ctx);

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
bool figli_audio(figli *f, const char *utente, uint8_t codec);

/* ------------------------------------------------------------------------- */
/* ⭐⭐ PHASE 7 — THE CLIPBOARD, and it crosses the boundary for the FOURTH time
 *     for the same reason as video, input and audio:
 *
 *       **the clipboard belongs to the compositor, and the compositor talks to
 *       the user's session, which is in the CHILD**; the messages of `RCP.md`
 *       §7.4 are written by the parent, which holds QUIC.
 *
 * ⛔ TEXT ONLY — `DECISIONI.md` §5-ter.1, decided by the user on 9 Aug 2026
 *    and confirmed again on the 17th.  MIME types do not cross the socket: they
 *    live in `appunti.c` and do not leave it (`src/appunti.h`).
 *
 * ⛔ AND THE TEXT GOES IN PIECES, like the frame and the cursor: the cap of §5.4
 *    is **1 000 000 bytes**, thirty times `PEZZO_MAX`.
 */

/*
 * ⭐ "THE SESSION HAS COPIED THIS TEXT" — the desktop → device direction.
 *
 * ⛔ It arrives ALREADY READ, already validated as UTF-8 and already within the
 *    cap of §5.4: those three checks are in `appunti.c`, where the text still
 *    exists whole and where it is known **which** of the reasons made it fail.
 *    ⚠ A text over the cap does not arrive here at all — §5.4 says "it is not
 *    announced", and the line is in the child's log.
 *
 * `testo` is zero-terminated and lives ONLY inside the call.
 */
typedef void (*FiglioAppuntiTesto)(void *ctx, const char *utente, uid_t uid,
                                   const char *testo, size_t byte);

/*
 * ⭐ "SOMEONE IN THE SESSION IS PASTING" — the device → desktop direction, and
 *    it is the half used most (`DECISIONI.md` §5-ter.1).
 *
 * ⛔⛔ IT MUST ALWAYS BE ANSWERED, with `figli_appunti_risposta()`, even
 *      empty-handed and even if the client never answers.  A
 *      `SelectionTransfer` without an answer leaves the pasting application
 *      hanging **indefinitely**, and what the user sees is a frozen desktop —
 *      a defect nobody connects to the clipboard.  ⇒ Whoever receives this
 *      callback keeps a timeout.
 *
 * `serial` is Mutter's number, and must be returned as is.
 */
typedef void (*FiglioAppuntiRichiesta)(void *ctx, const char *utente, uid_t uid,
                                       uint32_t serial);

/* ⚠ The two hooks are attached together or not at all: a parent that could
 *   receive the session's text and could not serve whoever pastes would leave
 *   the desktop **worse than it found it** — see above. */
void figli_gancio_appunti(figli *f, FiglioAppuntiTesto testo,
                          FiglioAppuntiRichiesta richiesta, void *ctx);

/*
 * "THE CLIENT HAS TEXT IN ITS CLIPBOARD": the child offers it to the session,
 * and from there on someone will be able to paste it.
 *
 * ⛔ It does NOT carry the text, and it is not an oversight: it is §7.4's
 *    "announce first, then pull" applied on this side.  The text is requested
 *    when someone really pastes — that is with `FiglioAppuntiRichiesta` — and
 *    whoever copies a whole document on the phone sends it to nobody until
 *    that moment comes.
 */
bool figli_appunti_offri(figli *f, const char *utente);

/*
 * The answer to a `FiglioAppuntiRichiesta`.  With `testo` NULL it declares not
 * having it — ⛔ **which is still an answer**, and it is the one that unblocks
 * whoever is pasting.
 */
bool figli_appunti_risposta(figli *f, const char *utente, uint32_t serial,
                            const char *testo, size_t byte);

/* ⭐⭐ PHASE 4 — THE CURSOR SHAPE, and it crosses the boundary in the opposite
 *     direction to input: the metadata comes from PipeWire (that is in the
 *     child) and the `CURSORE_FORMA` channel (`RCP.md` §7.2) lives in the
 *     parent.
 *
 * ⛔ `immagine` is premultiplied BGRA, `larghezza x altezza x 4` bytes, and
 *    lives ONLY inside the call: whoever wants to keep it copies it.
 * ⛔ `0x0` with `immagine` NULL = **hidden cursor** (§5.5), and it must be
 *    delivered as a message: it is the only way the client has of knowing the
 *    pointer has vanished, instead of drawing the last shape forever.
 * ⚠ The POSITION does not pass through here and does not pass anywhere in
 *   this direction: it belongs to the client, which draws the pointer itself
 *   (`SPECIFICHE.md` §7.1). */
typedef void (*FiglioCursore)(void *ctx, const char *utente, uid_t uid,
                              uint16_t larghezza, uint16_t altezza,
                              int16_t attivo_x, int16_t attivo_y,
                              const uint8_t *immagine, size_t byte);

/* ⭐⭐ §7.1 — THE ANSWER TO THE CANVAS, and it crosses the boundary in the
 *     cursor's direction: the question goes out with `figli_ritela()`, the
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
typedef void (*FiglioTela)(void *ctx, const char *utente, uid_t uid,
                           uint32_t voluta_l, uint32_t voluta_a, uint32_t avuta_l,
                           uint32_t avuta_a);

/* Switches on the children table.  ⛔ It spawns nothing: here it is not yet
 * known who will enter.
 *
 * `tela_l`/`tela_a`  the size with which the child will open capture and
 *                    encoding — the same constant as `main.c`, passed instead
 *                    of copied (`P2-1-sessione.md` §6.3: "or in two weeks they
 *                    will be three places").
 * `dir_rilievo`      where the child writes the raw data and the streams, or
 *                    NULL.  ⚠ **The child** writes there, that is the user: if
 *                    the folder is not theirs, the survey does not come out
 *                    and the line says so. */
/* ⭐⭐ §7.6 — "THIS USER'S GRAPHICAL SESSION IS OVER", and no client asked for
 *     it: the user chose "Log out…" from the desktop menu.
 *
 * ⛔ It is the twin of `TERMINA_SESSIONE` seen from the other direction: there
 *    the order comes from the wire, here the fact comes from the desktop.
 *    ⚠ In both cases whoever is watching must receive `0x10
 *    SESSIONE_TERMINATA` — and not the thirty seconds of silence followed by
 *    "network error", which is what would happen by keeping quiet (finding
 *    B-7).
 *
 * ⚠ It is registered separately instead of lengthening `figli_accendi()`: that
 *   signature already has four callbacks, and a fifth parameter on a line of
 *   six would no longer be read by anyone. */
typedef void (*FiglioSessioneFinita)(void *ctx, const char *utente, uid_t uid);

/* ⭐ §7.1 — "the stage is not there YET": the child SAYS so, and the parent
 * postpones the deadline instead of inferring a failure from silence. */
typedef void (*FiglioTelaAttendi)(void *ctx, const char *utente, uid_t uid,
                                  uint32_t voluta_l, uint32_t voluta_a);
void figli_gancio_tela_attendi(figli *f, FiglioTelaAttendi fn, void *ctx);
void figli_gancio_sessione_finita(figli *f, FiglioSessioneFinita fn, void *ctx);

figli *figli_accendi(uint32_t tela_l, uint32_t tela_a, const char *dir_rilievo,
                     FiglioDeposito deposita, FiglioCongedo congeda,
                     FiglioCursore cursore, FiglioTela tela, void *ctx);

/*
 * ⭐⭐⭐ THE **THREE** CURES OF PHASE 9 THAT LIVE ON THE OTHER SIDE — 23 Aug
 *      2026, and the third (audio silence) arrived on the 24th.
 *
 * ⛔ THE PROBLEM IT SOLVES, and it is the only reason this function exists:
 *    `codificatore_qualita_risale()`, `codificatore_tetto_banda()` and
 *    `audio_silenzio_taci()` are decisions of the **server**, but neither the
 *    video encoder nor the audio one runs in the server — they run in the
 *    CHILD, which is not a `fork` but an `execve` with the environment
 *    composed from scratch (`figlio.c`, point 5 of `diventa_ed_esegui()`).
 *    ⇒ An environment variable **does not arrive**, and calling the setters
 *    here would turn the cure on in the wrong process: the one that never
 *    opens an encoder.
 *
 * ⭐ THE ROAD IS THAT OF `--parlantina`, already paid for dearly on 16 Aug
 *    2026: the value is put on the **child's command line**, and the child
 *    repeats it to itself as soon as it is born.  Nothing else crosses.
 *
 * `qualita_risale`     quality climbs back instead of staying low (I6).
 * `tetto_banda_mbit`   the **floor** in Mbit/s from which the encoder derives
 *                      wire, working point and reservoir; `0` = off.
 * `audio_silenzio`     ⭐ an all-zero audio block does not become a datagram.
 *                      **`true` is the default** since 24 Aug 2026 (the user's
 *                      decision), and it is turned off with
 *                      `--niente-audio-silenzio`.  ⚠ `main.c` calls it with the
 *                      SAME value it passes to `audio_silenzio_taci()` for
 *                      itself: the test tone opens an encoder in the server,
 *                      and two different values would be two different
 *                      products.
 *
 * ⚠ It is registered separately instead of lengthening `figli_accendi()`, for
 *   the reason already written above `FiglioSessioneFinita`: that signature
 *   already has four callbacks.
 * ⛔ It holds for the children born AFTER: it is called at startup, before PAM
 *    can say yes to anyone.  ⚠ And the one declaring the value in force is
 *    neither this file nor `main.c`, but `codificatore.c` when each encoder
 *    opens — that is whoever really uses it.  An option lost in the parent →
 *    child hand-over has exactly the same face as a cure that does not work,
 *    and those lines are the only place where the two separate.
 */
void figli_fase9(figli *f, bool qualita_risale, uint32_t tetto_banda_mbit,
                 bool audio_silenzio);

/* ⛔ Shuts down all the children and waits until they are dead.  ⚠ It WAITS,
 * and it must be said: it sits **after** the last round of the `poll` loop,
 * like `aiutante_spegni()` — `CODER.md` §4.4 forbids waiting INSIDE the loop,
 * not after. */
void figli_spegni(figli *f);

/* ⛔⭐ IT IS CALLED WHEN PAM HAS SAID YES, AND NOT AN INSTANT BEFORE (invariant
 *     I3).  A child born on `CREDENZIALI` would run as a user who has not yet
 *     proven to be who they are.
 *
 * ⛔ I2 — "only one graphical session per user": if that user's child already
 *    exists and still answers, this function **does not spawn a second one**
 *    and returns `true` anyway.  Two connections of the same user see the same
 *    stage, which is precisely what I4 says.
 *
 * ⛔ `false` means "there is no child for that user", and the caller must not
 *    treat it as "maybe": no stage, no pixels.  The roads leading here are
 *    listed in `figlio.c`, function `figli_assicura`. */
bool figli_assicura(figli *f, const char *utente);
/* ⭐ PHASE 17 T6: the same, with the client's (bare) address that the child's
 *    PAM session receives as `PAM_RHOST`, like sshd's (logind: `RemoteHost`).
 *    NULL or "" ⇒ "remotix", as before. */
bool figli_assicura_da(figli *f, const char *utente, const char *rhost);

/* The descriptors to put in the `poll`.  Returns how many it wrote. */
size_t figli_descrittori(figli *f, struct pollfd *fds, size_t max);

/* ⛔ Reads what the children have to say, verifying the kernel's credentials
 * **on every message**.  ⚠ It is called even when no descriptor is readable:
 * in here the waits expire and the dead are reaped, and a deadline that waits
 * for a byte is a deadline that never fires — the lesson of `regola_battito`,
 * paid on 11 August with B6 and paid again by the helper. */
void figli_muovi(figli *f, struct pollfd *fds, size_t n, uint64_t ora_ms);

/* How many children are alive now.  For the log and for the bench. */
int figli_quanti(const figli *f);

/* ⭐⭐ The user name of the `quale`-th live stage (0 … `figli_quanti()−1`), or
 *     `NULL`.  ⛔ It serves the BUDGET (phase 10) to know **who is inside**,
 *     and the right set is this one and not the slots of the RCP registry: a
 *     session that left its slot through silence **still encodes** as long as
 *     its stage is alive (§3.2, the *ghost*), and costs as much as the others.
 * ⚠ The index is not stable between two calls: it is scanned once only. */
const char *figli_utente_ennesimo(const figli *f, int quale);

/* ⛔ For the bench: the pid of that user's child, or -1.  ⚠ It serves
 * `banchi/02-figlio-*` to ask the KERNEL who that process is
 * (`/proc/<pid>/status`) instead of inferring it from `pgrep`, which would
 * also find the children of the other benches' servers. */
pid_t figli_pid_di(const figli *f, const char *utente);

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
bool figli_chiedi_palco(figli *f, const char *utente);

/* ⛔⭐ PHASE 3 — "CAPTURE CONTINUOUSLY", AND "THIS ONE MUST BE A KEYFRAME".
 *
 *     It is the parent half of the seam that did not exist at phase 2:
 *     `codificatore_chiedi_chiave()` had **no caller in the product**, so a
 *     client's `RICHIEDI_CHIAVE` turned on a `bool` in `rcp.c` and produced no
 *     keyframe — and with `chiavi_ogni = 0` (infinite GOP) after the first
 *     keyframe not a single one ever arrived again.
 *
 * `codec`  1 = HEVC, 2 = AV1, and ⛔ **0 = stop capturing**.  It is not an
 *          implicit sentinel: it is the value §4.3/§6.2 give to "no codec
 *          negotiated", and here it means the same thing — nobody is watching.
 * `chiave` §5.2: the next frame of that codec MUST be a keyframe.
 *
 * ⚠ The one who decides is neither this file nor `main.c`: it is
 *   `webtransport.c`, which knows when `SESSIONE` went out and when §5.2 opens
 *   the debt.  `main.c` acts as the bridge because it is the only one that
 *   knows both sides. */
/* ⛔⭐ `profondita` (8 or 10, `0` = not negotiated) arrived on 17 Aug 2026:
 *     without it, the child wrote it by itself and the stream came out at a
 *     depth DIFFERENT from the one declared in `ECCOMI` (§4.3).  The full box
 *     is on `struct corpo_video` in `figlio.c`. */
/* ⛔⭐ `livello_x10` (in tenths: `5.1` ⇒ 51, `0` = not declared) arrived on
 *     23 Aug 2026 for the twin reason: `[M]` at 3840x2160 the client declared
 *     5.1 and the server produced **5.2** — §4.3 line 701 is a MUST.
 *     ⚠ `0` means "no ceiling", not "low". */
bool figli_video(figli *f, const char *utente, uint8_t codec,
                 uint8_t profondita, uint8_t livello_x10, bool chiave);

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
 *    inside `input_rotella()` (`src/input.h`, `RCP.md` §7.3).
 *
 * `id`      §7.3, the message identifier.  ⭐ It is what comes back in the
 *           `input` field of frames (§6.2) — but **only if the compositor takes
 *           it**: the child advances its counter when the injection succeeded,
 *           not when the request went out.
 * `codice`  evdev (`BTN_LEFT` = 0x110, `KEY_A` = 30), for button and position.
 * `a`/`b`   pointer: `x`/`y` on the canvas · wheel: the axes in units of 120
 *           · letter: the Unicode scalar value in `a` · ritela: the new canvas.
 *
 * `false` = there is no child for that user, or the request did not go out —
 * ⛔ and then that input did not reach the desktop, which is DECLARED in the
 * log instead of being hushed up (`CODER.md` §4.2). */
enum {
	FIGLI_INPUT_PUNTATORE = 1,
	FIGLI_INPUT_PULSANTE = 2,
	FIGLI_INPUT_ROTELLA = 3,
	FIGLI_INPUT_LETTERA = 4,
	FIGLI_INPUT_POSIZIONE = 5,
	/* ⛔⭐ "The rule with the highest damage/cost ratio of the document"
	 *     (`RCP.md` §11): at detach EVERYTHING is released.  A Ctrl left down
	 *     in a session that outlives the client makes the desktop unusable at
	 *     reattach, and nobody connects the two things. */
	FIGLI_INPUT_RILASCIA_TUTTO = 6,
	/* ⛔ §7.1: the canvas in force has changed, remap the absolute pointer
	 *    region.  Without it, `rcp.c` saturates on the new canvas and the stage
	 *    stays on the old one — two sides with two truths and no error. */
	FIGLI_INPUT_RITELA = 7,
	/* ⭐ §7.6 of `RCP.md` — "the user asked to LOG OUT".  ⛔ It is not a gesture
	 *    and it is not injected: it travels in this envelope for the same
	 *    reason as `RITELA` — a single envelope between parent and child, a
	 *    single branch to read — and like that one it goes BEFORE the gestures
	 *    guard. */
	FIGLI_INPUT_TERMINA = 8
};

/* ⭐⭐ §5-bis.7 — the layout declared by the client enters the session.
 *     ⛔ `true` = the request WENT OUT, not "it is in force": the one
 *     ascertaining it is the child's «KEYMAP CHANGED» line, after Mutter has
 *     destroyed and recreated the keyboard device. */
bool figli_disposizione(figli *f, const char *utente, const char *nome);

bool figli_input(figli *f, const char *utente, uint32_t id, uint8_t azione,
                 uint16_t codice, int premuto, int32_t a, int32_t b);

/* ⭐⭐ "THE SERVER'S CANVAS TAKES THE SIZE OF THE CLIENT'S CANVAS" — the chain
 *     that was missing on 14 Aug 2026, and with it four symptoms
 *     (`DECISIONI.md` §5.0-sexies, `fasi/rapporti/F4-IN-12`):
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
 *    first one that arrives at the new size, and the `larghezza`/`altezza`
 *    field of `FiglioDeposito` carries it. */
/* ⭐ "END THIS USER'S GRAPHICAL SESSION" — `RCP.md` §7.6, the second of the
 * two exits of `DECISIONI.md` §4.1-ter.  ⛔ It is not the detach: here the
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
	FIGLI_USCITA_UTENTE = 0,   /* §7.6: a person asked for it */
	FIGLI_USCITA_ABBANDONO = 1 /* §5.3: the ceiling expired, nobody asked for it */
};

bool figli_termina_sessione(figli *f, const char *utente, int perche);

bool figli_ritela(figli *f, const char *utente, uint32_t larghezza,
                  uint32_t altezza);

/* ⛔⭐ ASKS EVERY CHILD "WHO ARE YOU", at most once a minute.
 *
 *     ⚠ It is needed so that "verified on every message" is a protection even
 *     when there are no messages: a child that delivered its frame and then
 *     falls silent would stay verified **only once, at the start** — that is
 *     exactly what §1.10-bis forbids.  ⭐ The answer goes through
 *     `credenziali_combaciano()` like all the others, and a child that in the
 *     meantime were no longer that uid would be killed there.
 *
 * ⚠ The OK outcome line is in the chatter (`registro_dettaglio`): one per
 *   minute per child would fill the log with green.  The disagreement does
 *   not: that one is always written. */
void figli_ricontrolla(figli *f, uint64_t ora_ms);

/* ⛔⭐ THE CHILD'S ENTRY POINT — `main.c` gets here as the FIRST thing, when
 *     `argv[1]` is `--figlio-interno`, and it never returns.
 *
 *     ⚠ It is an INTERNAL command line: `figli_assicura()` writes it and
 *     `figlio_vive()` reads it.  Whoever typed it by hand would get a process
 *     talking on a descriptor 3 that does not exist, and it would die there —
 *     there is nothing to gain, because the child has no privilege to give
 *     away: it is the user themselves. */
void figlio_vive(int argc, char **argv);

/* ⭐ PHASE 17 — `remotix --prova-codifica` (the certification, §6.0 phase 7a):
 *    a synthetic 256x256 frame in H.264 with the same choice as a real session
 *    (VA-API on the session's node; ⛔ since phase 19 no software fallback).
 *    It writes ONE JSON line on stdout —
 *    {"esito":"hardware"|"nessuno","codificatore":…,"nodo":…,"motivo":…,
 *     "codec":…,"offerti":…,"hevc":…,"h264":…}
 *    — and returns the exit code: 0 the card encodes · 1 the card opens but
 *    the frame does not come out · 2 usage error · 3 NO CARD can encode
 *    (declared refusal).  No network, no sessions; root is not needed (but the
 *    node's groups are).
 * ⭐ PHASE 18: the arguments following `--prova-codifica` (all optional):
 *    `h264`|`hevc`, `--nodo /dev/dri/renderDN`, and ⭐ phase 19
 *    `--codifica scheda|vulkan|vaapi`.  The JSON also carries `strada`,
 *    `hevc_strada` and `h264_strada` ("vulkan"/"vaapi"): WHICH route of the
 *    card encoded. */
int figlio_prova_codifica(int argc, char **argv);

/* ⭐ PHASE 19 (`DECISIONI.md` §10.27) — the card's route: "scheda" (by
 *    capability: Vulkan Video if available for that codec, otherwise VA-API —
 *    the default and what the product does), "vulkan" or "vaapi" (forced, for
 *    tests and diagnosis).  Returns false on a name that is not one of the
 *    three, and then nothing changes.  The parent passes it to the child on
 *    the command line (`--codifica`), like the phase 9 cures. */
bool figlio_codifica_strada(const char *strada);
const char *figlio_codifica_strada_chiesta(void);

/* ⭐ PHASE 18 — the test AT THE PARENT'S STARTUP: what this machine can
 *    encode, in a separate process (a crashing driver does not bring down the
 *    server).  `offerti` is the list for ECCOMI's `video.codec` ("hevc,h264"
 *    · "hevc" · "h264" · "" = nothing), `spiegazione` the line for the log
 *    with the reason for each "no".  Returns false if nothing is offered. */
bool figlio_capacita_video(char *offerti, size_t offerti_byte, char *spiegazione,
                           size_t spiegazione_byte);

#endif
