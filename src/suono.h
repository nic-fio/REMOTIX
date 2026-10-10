/*
 * suono — the session's sound: the virtual sink and the capture of its monitor.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IN THE SESSION THERE IS NOTHING TO CAPTURE, and it must be created
 *
 * `[M]` 5 August 2026 (v1, `REFERENCE.md` §7.5): in the session without a monitor,
 * with `pipewire`, `pipewire-pulse` and `wireplumber` all three running,
 * `wpctl status` shows ZERO devices, ZERO sinks, ZERO sources.  The machine has
 * no sound card, and that is the NORMAL case for a server (`SPECIFICHE.md` §11).
 *
 * The reference does not help here, and it must be said: `gnome-remote-desktop`
 * opens a capture on the monitor of every node with `media.class = Audio/Sink`
 * it finds in the PipeWire registry, and it never creates a sink.  ⛔ With its
 * code, on this machine, not a single sample would arrive — and without an error
 * anywhere, which is the form of fault that `LEZIONI.md` §2.2 calls by name.
 *
 * ⇒ So the sink is created: a `support.null-audio-sink` node, which becomes the
 *   default because it is the only one, and whose **monitor** is captured — that
 *   is, the mix of what all the session's applications play.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE SINK BELONGS TO THE SESSION, THE CAPTURE TO THE CONNECTION
 *
 * It is the same split as the stage (invariant I4, `CODER.md` §2), and for the
 * same reason.  The device the applications play on cannot appear and
 * disappear at every reconnection: whoever is listening to something would
 * find the sound interrupted, and applications already open would not go back
 * to the new device by themselves — PipeWire leaves them attached to the node
 * they chose when they started.  The capture instead is needed only while
 * someone listens: it belongs to the connection, and is switched on and off
 * as many times as needed.
 *
 * ⇒ `suono_apri()` mounts the sink and KEEPS it for the whole session;
 *   `suono_ascolto_avvia()` / `suono_ascolto_ferma()` belong to the connection.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE FORMAT IS FIXED, AND IT IS NOT AN OPINION OF THIS FILE
 *
 * `RCP.md` §5.3: 48 000 Hz, 2 interleaved channels, `s16`.  The two numbers live
 * in `audio.h` (`AUDIO_FREQUENZA`, `AUDIO_CANALI`) and are taken from there:
 * whoever rewrote them here would create a second truth about the format, and
 * the day the two diverged the symptom would not be an error — it would be
 * **full-scale noise**, the defect of v1 (`LEZIONI.md` §2.2).
 *
 * ⚠ In v1 the rate came from the format negotiated with the RDP client and
 *   this module received it as a parameter.  In V2 nothing is negotiated:
 *   `suono_ascolto_avvia()` no longer has either rate or channels.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ AND BLOCKS ARE NOT ACCUMULATED HERE — the choice, with the reason
 *
 * The encoder wants blocks of FIXED size: 960 frames for Opus, 240
 * for PCM (`audio.h`, `RCP.md` §5.3).  PipeWire delivers as many frames as
 * it likes — with the quantum forced to 256 it delivers 256, which is neither
 * one nor the other.  Someone must accumulate.  ⇒ **Not this module**, and it is
 * not laziness:
 *
 *   1. ⛔ The consumer **must** have its own queue anyway.  The callback
 *      runs on the realtime thread (see below): inside it one cannot
 *      encode — `opus_encode` is computation without a declared time
 *      ceiling, and until 29 Sep 2026 `avcodec_send_frame` even allocated —
 *      nor write to a socket.
 *      So the samples must be copied into a structure that ANOTHER thread
 *      reads, and that structure is necessarily a ring with head and tail: from a
 *      ring one pulls out 960 frames by construction, without a second
 *      accumulator.  Putting one here would mean **two intermediate buffers
 *      for the same job**, and `CODER.md` §1-bis: "every intermediate buffer
 *      you add buys smoothness and sells responsiveness".
 *
 *   2. ⛔ An accumulator here would decide WHEN the sound starts, and that is a
 *      decision of the sender, not of the capturer.
 *
 *   3. ⚠ And the remainder: at shutdown an accumulator would find itself holding
 *      up to 959 frames nobody claims, and would drop them silently.
 *
 * ⇒ ⛔ **So the contract is: `fotogrammi` VARIES at every callback, and the
 *   listener must take nothing for granted about its value.**  The block
 *   size is asked of `audio_cod_blocco()`, which is the single place it lives.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE VOLUME: invariant I5, and a measured trap
 *
 * The volume belongs to the session and whoever connects finds it at MAXIMUM
 * (`SPECIFICHE.md` §10, `CODER.md` §2 I5).  ⚠ And the sink is born with
 * `monitor.channel-volumes = true`, without which the volume slider
 * governs nothing: `STUDI.md` §kde §10.5, `[M]` 8 August 2026.  The long
 * reason, with the table of numbers, is next to the line in `suono.c`.
 */
#ifndef REMOTIX_SUONO_H
#define REMOTIX_SUONO_H

#include <stdbool.h>
#include <stdint.h>

typedef struct suono suono;

/*
 * The captured samples: interleaved, `s16` in machine order, and
 * `fotogrammi` samples PER CHANNEL (so `fotogrammi * AUDIO_CANALI` integers).
 *
 * ⛔⛔ RUNS ON PIPEWIRE'S REALTIME THREAD: here one COPIES and RETURNS.
 *
 *     `[R]` `pipewire/stream.h:150` — with `PW_STREAM_FLAG_RT_PROCESS` this
 *     callback "will be called from a realtime thread and it is not safe to
 *     call non-realtime functions such as doing file operations, blocking
 *     operations or any of the PipeWire functions that are not explicitly
 *     marked as being RT safe".
 *
 *     ⛔ And the damage does not stop at audio: whoever writes inside it a call
 *     that waits — a contended lock, a socket write, an unlucky `malloc`,
 *     **a log line** — makes the WHOLE PipeWire graph miss its quantum, desktop
 *     capture included.  The symptom would not be "the audio crackles", it
 *     would be "the video stutters", and nobody would trace it back
 *     here.
 *
 * ⚠ `campioni` is valid only for the duration of the callback: on the next
 *   round PipeWire writes into it again.
 */
typedef void (*suono_campioni)(const int16_t *campioni, uint32_t fotogrammi, void *chi);

/*
 * Mounts the virtual sink in the session, and brings it to maximum.
 *
 * ⛔ Returns NULL and writes the reason to the log (`CODER.md` §4.2: a fallback
 *    is declared).  The node dies with this object — `object.linger = false` —
 *    because it belongs to the served session and not to the machine: leaving it
 *    behind would mean that a restarted REMOTIX finds two.
 */
suono *suono_apri(void);
void suono_chiudi(suono *s);

/*
 * Switches on the capture of the sink's monitor.
 *
 * ⛔ The format is that of §5.3 and is not passed: 48 000 Hz, 2 channels, `s16`.
 *    If PipeWire negotiated another one the delivery SWITCHES OFF and it is
 *    declared, instead of reading the samples blindly — reading `f32` as `s16`
 *    does not produce an error, it produces a full-scale square wave that to the
 *    bench looks like "audio arriving" and to the ear is a buzz (`[M]` 5 Aug 2026).
 *
 * ⚠ One capture at a time: the second returns `false` and says so.
 */
bool suono_ascolto_avvia(suono *s, suono_campioni su_campioni, void *chi);

/*
 * Switches off the capture, and WAITS for the realtime thread to finish.
 *
 * ⛔ It must wait: `su_campioni` carries the connection's pointer, and whoever
 *    returns from here is entitled to free it.  A frame left half
 *    way would be a segfault inside a thread that does not bear our name.
 *    How it really waits — and why the loop lock is NOT enough — is
 *    written next to the function in `suono.c`.
 */
void suono_ascolto_ferma(suono *s);

/* The sink's node, for the log and for diagnosis.  0 = not there (any more). */
uint32_t suono_nodo(const suono *s);

/*
 * The sink's volume at maximum, and not muted — invariant I5.
 *
 * Called at creation, at capture start and AT EVERY CONNECTION.
 * `[the user's decision, 8 August 2026]` The level is carried by the server inside
 * the samples, so a slider left low is a state the client can neither
 * see nor explain: whoever connects from another device three
 * days later hears it quietly and goes looking for the fault in the network, in
 * the encoder, anywhere except there.  It really happened, to us.
 *
 * ⚠ It can be called from any thread: it takes the loop lock.
 */
void suono_volume_massimo(suono *s);

/*
 * ⭐ THE TWO FUNCTIONS MORE THAN v1, and the reason is a single one.
 *
 * ⛔ v1 printed from the realtime thread — "primo blocco di suono dalla
 *    sessione: %u fotogrammi" was inside `su_processo`.  A log line
 *    is a `vsnprintf` plus a `write`: it is exactly the waiting call
 *    mentioned above.  ⇒ Here the realtime thread **writes nothing**
 *    and just counts; what v1 printed, here is ASKED from outside.
 *
 * ⚠ And it is needed, not ornament: `CODER.md` §3.10 — "a denied reading is not a
 *   reading that says zero".  Without these two, "nothing can be heard" has at
 *   least four causes with the same face: nobody plays, the stream is dead, the
 *   format was refused, the volume is at zero.  With these two, the first
 *   three are told apart in one line.
 */
bool suono_ascolto_vivo(const suono *s);
void suono_conti(const suono *s, uint64_t *blocchi, uint64_t *fotogrammi, uint64_t *scartati);

#endif
