/*
 * suono.c — see `suono.h` for the mandate, the session/connection split and
 * the choice NOT to accumulate blocks in here.
 *
 * ⚠ Ported from v1 (`fondamenta/remotix-c/src/suono.c`) on 17 August 2026.  The only
 *   intended differences from that file:
 *     · no GLib — `bool` from `<stdbool.h>`, the log from `registro.h`, and
 *       whoever fails returns `false`/NULL after writing the reason;
 *     · the format is no longer negotiated (§5.3): it comes from `audio.h`;
 *     · the realtime thread no longer prints anything (see `suono.h`);
 *     · the wait promised by `suono_ascolto_ferma()` is really done — v1
 *       promised it and did not do it (the box is next to the function).
 */
#include "suono.h"

#include <pipewire/pipewire.h>
#include <spa/debug/types.h>
#include <spa/param/audio/format-utils.h>
#include <spa/param/audio/type-info.h>
#include <spa/param/props.h>
#include <spa/utils/result.h>

#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "audio.h"
#include "registro.h"

/* ⚠ The area lives here and not in `registro.h` for the same reason
 *   `REG_AUDIO` lives in `audio.c`: this file is not yet in the `Makefile`, and
 *   a constant put in the shared header before the seam is a line that names
 *   a module the product does not compile.  ⇒ At assembly it moves, as was
 *   done with `REG_SESSIONE`. */
#define REG_SUONO "suono"

/* How long we wait for the server to register the sink's node.  It is a local
 * answer on a socket: if it does not arrive in five seconds it will not arrive. */
#define ATTESA_SINK_MS 5000

/* How long we wait for the capture to reach `paused`, that is for the format to
 * be negotiated.  ⛔ It is the only point where a refusal shows AT ONCE instead
 * of becoming silence later — the same reason as the wait in `cattura.c`, and
 * there it costs ten seconds because there a compositor is getting up; here on
 * the other side there is only PipeWire. */
#define ATTESA_ASCOLTO_MS 5000

/* How long we wait, at most, for a realtime callback already started to
 * exit (see `suono_ascolto_ferma`).  ⚠ In health it costs zero or one quantum —
 * `[?]` 5-6 ms: the ceiling is wide on purpose, because exceeding it means
 * PipeWire is stuck and the line saying so is worth more than the time it costs. */
#define ATTESA_BARRIERA_MS 2000

/*
 * The sink's name, which is also how the capture finds it again.
 *
 * `pw_stream_connect()` wants `PW_ID_ANY` as target and attaches to what
 * `target.object` says — where a `node.name` fits.  So there is no need to know
 * the id assigned by the server, and above all we do not end up capturing the
 * WRONG sink the day the machine has two (a real card, or a second served
 * session).
 */
#define NOME_SINK "remotix"

/*
 * ⚠ The forced quantum, and the number is that of v1 and of the reference
 *   (`gnome-remote-desktop`): 256 frames, that is 5.33 ms at 48 kHz.  A short
 *   quantum keeps latency low — `CODER.md` §1-bis, latency weighs more than
 *   frames — and makes small, regular blocks arrive.
 *
 * `[?]` 240 would be handier (5 ms round: an exact PCM block, an exact quarter of
 *   an Opus block), ⛔ but changing a value v1 measured in the field for an
 *   unmeasured convenience is a debt, not a cure (`CODER.md`, §1-bis of the
 *   ten-seconds box in `cattura.c`).  It changes the day someone measures
 *   that it pays off.
 */
#define QUANTO_FORZATO "256"

struct suono
{
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;

	struct pw_proxy *sink;
	struct spa_hook gancio_sink;
	uint32_t nodo;

	struct pw_stream *flusso;
	struct spa_hook gancio_flusso;
	enum pw_stream_state stato;
	char *guasto;

	/* --- what the realtime thread touches -------------------------------- *
	 *
	 * ⛔ `consegna` and `in_richiamo` are ATOMIC and not plain `bool`s: they are
	 *    the two halves of the barrier of `suono_ascolto_ferma()`, and a barrier
	 *    built on reads the compiler can move is not a barrier.  The reason for
	 *    the design is next to that function. */
	atomic_bool consegna;
	atomic_bool in_richiamo;
	suono_campioni su_campioni;
	void *chi;

	/* The counts.  ⚠ The realtime thread increments them and whoever wants reads
	 *   them: atomic for the same reason as above, and `relaxed` would do —
	 *   they are numbers for the log, not a synchronisation. */
	atomic_ullong blocchi;
	atomic_ullong fotogrammi;
	atomic_ullong scartati;
	/* ⭐ The loudest sample seen, in absolute value.  See the box in
	 *    `su_processo`: it is what tells "nobody was playing" from
	 *    "PipeWire hands us empty buffers". */
	atomic_ullong picco;
};

/* ------------------------------------------------------------------ *
 * The virtual sink
 * ------------------------------------------------------------------ */
static void su_sink_legato(void *dati, uint32_t id_globale)
{
	suono *s = dati;

	s->nodo = id_globale;
	pw_thread_loop_signal(s->ciclo, false);
}

static void su_sink_tolto(void *dati)
{
	suono *s = dati;

	/* The server pulled the node from under our feet.  There is nothing to redo
	 * here: we say so, and the capturer will see the stream detach.  ⚠ It runs on
	 * the LOOP thread, not the realtime one: here we may write. */
	registro_dice(REG_SUONO, "⛔ the session's audio sink was REMOVED: no more sound "
	                         "(node %u)", s->nodo);
	s->nodo = 0;
	pw_thread_loop_signal(s->ciclo, false);
}

static void su_sink_sbagliato(void *dati, int seq, int res, const char *messaggio)
{
	suono *s = dati;

	registro_dice(REG_SUONO, "⛔ the audio sink was not created: %s (%d, %s)",
	              messaggio ? messaggio : "no explanation", res, spa_strerror(res));
	pw_thread_loop_signal(s->ciclo, false);
}

static const struct pw_proxy_events eventi_sink = {
	PW_VERSION_PROXY_EVENTS,
	.bound = su_sink_legato,
	.removed = su_sink_tolto,
	.error = su_sink_sbagliato,
};

/* ------------------------------------------------------------------ *
 * The monitor capture
 * ------------------------------------------------------------------ */
static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *sbaglio)
{
	suono *s = dati;

	registro_dettaglio(REG_SUONO, "audio capture state: %s → %s%s%s",
	                   pw_stream_state_as_string(vecchio), pw_stream_state_as_string(nuovo),
	                   sbaglio ? " — " : "", sbaglio ? sbaglio : "");
	s->stato = nuovo;
	if (sbaglio)
	{
		free(s->guasto);
		s->guasto = strdup(sbaglio);
	}

	/* ⛔ The detachment is SAID, and not left to be deduced from silence: from here
	 *    on not a sample arrives, and without this line whoever looks for "why can
	 *    nothing be heard" has no way to tell it from "nobody is playing".
	 *    ⚠ Whoever wants to notice it in code calls `suono_ascolto_vivo()`. */
	if ((vecchio == PW_STREAM_STATE_PAUSED || vecchio == PW_STREAM_STATE_STREAMING) &&
	    (nuovo == PW_STREAM_STATE_UNCONNECTED || nuovo == PW_STREAM_STATE_ERROR))
		registro_dice(REG_SUONO, "⛔ the audio capture detached (%s)%s%s",
		              pw_stream_state_as_string(nuovo), sbaglio ? " — " : "",
		              sbaglio ? sbaglio : "");

	pw_thread_loop_signal(s->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	suono *s = dati;
	uint8_t spazio[256];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];
	struct spa_audio_info_raw negoziato = { 0 };

	if (!param || id != SPA_PARAM_Format)
		return;

	/*
	 * ⛔ WE LOOK AT THE FORMAT REALLY NEGOTIATED, and it is not pedantry.
	 *
	 * It is the same trap `cattura.c` documents for video, and here it bites
	 * harder: reading floating-point samples as 16-bit integers produces no
	 * error, it produces a full-scale square wave that follows the right
	 * frequency — that is, something that to the bench looks like "audio arriving"
	 * and to the ear is a buzz.  `[M]` 5 August 2026, v1.
	 *
	 * ⛔⭐ AND IN V2 THE RATE IS CHECKED TOO, which v1 did not check: there
	 *     it had been asked equal to the one negotiated with the RDP client, here it
	 *     is fixed at 48 000 (§5.3) and the whole chain downstream relies on it —
	 *     Opus gets a `sample_rate` written in `audio.c`, not one read from here.  If
	 *     PipeWire granted another one, the sound would come out out of tune and
	 *     over the wrong time, **without an error anywhere**.
	 */
	if (spa_format_audio_raw_parse(param, &negoziato) >= 0)
	{
		bool giusto = negoziato.format == SPA_AUDIO_FORMAT_S16 &&
		              negoziato.rate == AUDIO_FREQUENZA && negoziato.channels == AUDIO_CANALI;
		/* ⚠ The name may be missing — `spa_debug_type_find_short_name()` returns
		 *   NULL for an id its table does not know — and then the bare NUMBER is
		 *   printed: it is the same rule as `cattura.c` (`primo_tipo_grezzo`),
		 *   because "(null)" in a log cannot be searched for anywhere. */
		const char *nome = negoziato.format == SPA_AUDIO_FORMAT_S16
		                       ? "S16"
		                       : spa_debug_type_find_short_name(spa_type_audio_format,
		                                                        negoziato.format);

		registro_dice(REG_SUONO,
		              "audio format negotiated with PipeWire: %s (SPA %u), %u Hz, %u channels%s",
		              nome ? nome : "NO NAME", negoziato.format, negoziato.rate,
		              negoziato.channels, giusto ? "" : "  ⛔ IT IS NOT WHAT WAS ASKED");

		if (!giusto)
		{
			registro_dice(REG_SUONO,
			              "⛔ §5.3 wants S16 at %d Hz on %d channels: the samples would be read "
			              "wrong and the audio would be NOISE, not an error.  Switching off delivery",
			              (int) AUDIO_FREQUENZA, (int) AUDIO_CANALI);
			atomic_store(&s->consegna, false);
		}
	}
	else
	{
		/* ⛔ We do not go on blindly — v1 did ("the capture continues
		 *    blindly") and it is the silent fallback `CODER.md` §4.2 forbids:
		 *    a format we cannot read is exactly the case in which the
		 *    samples can be anything. */
		registro_dice(REG_SUONO, "⛔ audio format not interpretable: switching off delivery instead "
		                         "of reading samples I know nothing about");
		atomic_store(&s->consegna, false);
	}

	/* The samples are wanted in ordinary, mapped memory: the zero-copy path has
	 * nothing to do with audio, and asking for it here only means handling
	 * buffers that cannot be read directly. */
	parametri[0] = spa_pod_builder_add_object(&costruttore, SPA_TYPE_OBJECT_ParamBuffers,
	                                          SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_dataType,
	                                          SPA_POD_Int(1 << SPA_DATA_MemPtr));
	pw_stream_update_params(s->flusso, parametri, 1);
}

/*
 * ⛔⛔ THIS FUNCTION RUNS ON THE REALTIME THREAD.  See `suono.h`.
 *
 * Inside there are only: a `dequeue`, some comparisons, the listener's
 * callback and a `queue`.  ⛔ No log line, no allocation, no lock — v1 printed
 * the first block from here, and a `write` at this point makes the whole graph
 * miss its quantum, desktop capture included.
 */
static void su_processo(void *dati)
{
	suono *s = dati;
	struct pw_stream *flusso = s->flusso;
	struct pw_buffer *pacco;

	/*
	 * ⛔ THE FIRST HALF OF THE BARRIER, and the order is everything: we declare
	 *    we are inside BEFORE reading `consegna`.  Whoever stops does the opposite —
	 *    switches off `consegna` and then reads `in_richiamo` — and with two
	 *    sequentially consistent writes at least one of the two sees the other.  It
	 *    is Dekker, and it is what makes the promise of `suono_ascolto_ferma()` true.
	 */
	atomic_store(&s->in_richiamo, true);

	if (!flusso)
	{
		atomic_store(&s->in_richiamo, false);
		return;
	}

	/*
	 * THE WHOLE QUEUE IS DRAINED, in order.
	 *
	 * The reference keeps only the last packet and drops the earlier ones
	 * (`grd-rdp-audio-output-stream.c`).  ⛔ Not here, and it is the difference between
	 * audio and video: in video the newest wins, because nobody has any use for
	 * an old frame (`cattura.c`, the slot of the last frame).  In sound a dropped
	 * packet is a GAP, and every gap is heard.  If the queue grows the remedy lies
	 * downstream — whoever queues the samples knows how many it can keep — not
	 * in a silent loss here.
	 */
	while ((pacco = pw_stream_dequeue_buffer(flusso)))
	{
		struct spa_data *piano = &pacco->buffer->datas[0];

		if (pacco->buffer->n_datas > 0 && piano->data && piano->chunk && piano->chunk->size > 0)
		{
			const int16_t *campioni =
			    (const int16_t *) ((const uint8_t *) piano->data + piano->chunk->offset);
			uint32_t fotogrammi =
			    (uint32_t) (piano->chunk->size / (sizeof(int16_t) * AUDIO_CANALI));

			if (fotogrammi > 0)
			{
				/* ⛔ `consegna` is read only once and kept: reading it twice
				 *    would mean possibly finding it on in the check and
				 *    off in the callback. */
				if (atomic_load(&s->consegna) && s->su_campioni)
				{
					/*
					 * ⭐ THE PEAK, AND IT IS THE ONLY NUMBER THAT TELLS THE TWO
					 *    FACES OF SILENCE APART.  `[M]` 17 August 2026, and not
					 *    having it cost me half a day.
					 *
					 *    Without it, "nothing can be heard" has two causes with the
					 *    very same face — 48 000 frames per second
					 *    delivered, zero discarded, the stream in `streaming` —
					 *    and they are: **nobody was playing in the session**, or
					 *    **PipeWire hands us empty buffers**.  It is `CODER.md`
					 *    §3.10 applied to the sample instead of the count:
					 *    a module that can say "zero" must be able to tell the
					 *    zero from the fault.
					 *
					 * ⚠ And the price on the realtime thread is a loop of
					 *   comparisons over 512 integers — no allocation, no
					 *   lock, no write: less work than the copy
					 *   the listener does, and the contract of `suono.h` holds
					 *   ("inside one copies and returns").
					 */
					uint32_t i;
					unsigned long long pk = 0;

					for (i = 0; i < fotogrammi * AUDIO_CANALI; i++)
					{
						int v = campioni[i] < 0 ? -campioni[i] : campioni[i];
						if ((unsigned long long) v > pk)
							pk = (unsigned long long) v;
					}
					if (pk > atomic_load(&s->picco))
						atomic_store(&s->picco, pk);

					atomic_fetch_add(&s->blocchi, 1u);
					atomic_fetch_add(&s->fotogrammi, fotogrammi);
					s->su_campioni(campioni, fotogrammi, s->chi);
				}
				else
				{
					/* ⛔ "Arrived and dropped" is NOT "not arrived": `CODER.md`
					 *    §3.10.  Without this count, a refused format and a
					 *    mute desktop have the same face. */
					atomic_fetch_add(&s->scartati, fotogrammi);
				}
			}
		}
		pw_stream_queue_buffer(flusso, pacco);
	}

	atomic_store(&s->in_richiamo, false);
}

static const struct pw_stream_events eventi_flusso = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/* ------------------------------------------------------------------ *
 * The volume — invariant I5
 * ------------------------------------------------------------------ */
/*
 * The sink is born at maximum and not muted.
 *
 * ⛔ WHY A LOW LEVEL ON THE SERVER IS INVISIBLE.
 *    [the user's decision, 8 August 2026, after that morning's hunt]
 *
 *    The level is decided by the server and the client finds it in the samples:
 *    it is the way that holds on every client and every desktop, because it asks
 *    nothing of anyone (`STUDI.md` §kde §10.5).  The price of that choice is that
 *    the server's slider becomes a HIDDEN state: whoever connects from another
 *    device three days later hears it quietly and has no way of knowing
 *    why.  It really happened, to us, with the sink at zero and muted.
 *
 *    ⇒ A freshly mounted audio path starts AUDIBLE, always (invariant I5).  If
 *    the user then lowers it, their choice stays while they stay connected.
 *
 * ⚠ The outcome is not checked: if PipeWire refused, the remedy would be
 *   the slider inside the session anyway, and an error here must not prevent
 *   audio.
 */
/* The real command.  ⚠ Called by whoever ALREADY HOLDS the loop lock. */
static void alza(suono *s)
{
	uint8_t memoria[512];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(memoria, sizeof memoria);
	float volumi[AUDIO_CANALI];
	const struct spa_pod *props;
	int seq;
	int i;

	for (i = 0; i < AUDIO_CANALI; i++)
		volumi[i] = 1.0f;

	props = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_Props, SPA_PARAM_Props, SPA_PROP_mute, SPA_POD_Bool(false),
	    SPA_PROP_channelVolumes,
	    SPA_POD_Array(sizeof(float), SPA_TYPE_Float, SPA_N_ELEMENTS(volumi), volumi));

	seq = pw_node_set_param((struct pw_node *) s->sink, SPA_PARAM_Props, 0, props);

	/*
	 * ⚠ THAT NUMBER IS AN ASYNCHRONOUS SEQUENCE, NOT AN OUTCOME: it says the
	 *   request left, not that the value changed.  It is printed precisely
	 *   for this — a line saying "brought to maximum" would be a line that lies,
	 *   and `CODER.md` §3.8 wants the level checked from the side that
	 *   consumes it (a `wpctl get-volume`, not this line).
	 */
	registro_dettaglio(REG_SUONO, "sink volume: maximum ASKED of node %u (seq %d) — asked, "
	                              "not verified", s->nodo, seq);
}

/*
 * ⛔ AND THE LOOP LOCK IS TAKEN, ALWAYS.
 *    `[M]` 8 August 2026, found by v1's bench `prove/fase11-volume.sh`.
 *
 *    libpipewire is not synchronised by itself: every call must be made either
 *    from the loop thread, or holding `pw_thread_loop_lock`.  This function is
 *    called by TWO foreign threads — the connection's, at every client that
 *    connects, and the one that starts the capture — and without the lock the
 *    request ended up in the connection while the loop was using it: **sometimes
 *    it went through, sometimes not**, and the log said "brought to maximum" anyway.
 *
 *    ⚠ The defect showed only in the case that matters: a user who mutes,
 *    disconnects, reconnects — and finds the silence again.  The bench missed it
 *    because it muted with the client connected, that is it DID NOT REPRODUCE (`CODER.md` §3.4).
 */
void suono_volume_massimo(suono *s)
{
	if (!s || !s->ciclo || !s->sink)
		return;
	pw_thread_loop_lock(s->ciclo);
	alza(s);
	pw_thread_loop_unlock(s->ciclo);
}

/* ------------------------------------------------------------------ *
 * Life cycle
 * ------------------------------------------------------------------ */
static bool crea_sink(suono *s)
{
	struct pw_properties *proprieta;
	uint64_t scadenza;

	proprieta = pw_properties_new(
	    PW_KEY_FACTORY_NAME, "support.null-audio-sink", PW_KEY_NODE_NAME, NOME_SINK,
	    PW_KEY_NODE_DESCRIPTION, "REMOTIX", PW_KEY_MEDIA_CLASS, "Audio/Sink", "audio.position",
	    "[FL,FR]",
	    /*
	     * ⛔⛔ WITHOUT THIS LINE THE VOLUME SLIDER GOVERNS NOTHING.
	     *     `[M]` 8 August 2026, `STUDI.md` §kde §10.5 — and the user opened it:
	     *     "if I lower the volume the audio always stays loud; in practice the
	     *     server's and the client's audio are disconnected".
	     *
	     *     In PipeWire a node's volume is applied AFTER the monitor
	     *     tap, and `monitor.channel-volumes` — which moves the tap downstream —
	     *     is `false` unless asked for.  We create the sink by hand with
	     *     `pw_core_create_object` and so we forgot it;
	     *     pipewire-pulse's `module-null-sink` sets it by itself, because in
	     *     PulseAudio the monitor has always been downstream of the volume.
	     *
	     *     The measurement, a 440 Hz tone of known amplitude (25.9 % of full scale)
	     *     read on the monitor:
	     *
	     *       sink volume     | without the line (as was) | with the line (`pactl`)
	     *              100 %    |        25.39 %            |       25.39 %
	     *               25 %    |     ⛔ 25.39 %            |        0.40 %
	     *                0 %    |     ⛔ 25.39 %            |        0.00 %
	     *
	     *     ⚠ The right column is not "almost right": it is EXACTLY
	     *     PulseAudio's cubic curve (0.25³ = 1.56 %, and 25.9 × 0.0156 = 0.40).
	     *     The left column is flat: the volume does not arrive, MUTE
	     *     INCLUDED — in the live session the node was at `channelVolumes 0.0` and
	     *     `mute true` while the client received the whole signal.
	     *
	     * ⚠ And the direction matters, and it is why this is the only slider
	     *   that can work: in RCP the volume does NOT travel (`RCP.md` §5.3,
	     *   invariant I5), so the only level that really governs is the one
	     *   seen inside the session.
	     */
	    "monitor.channel-volumes", "true",
	    /*
	     * ⛔ AND LET NOBODY PUT YESTERDAY'S LEVELS BACK.
	     *    WirePlumber saves volume and mute by node NAME and restores them when
	     *    the node reappears — `[M]` 8 August 2026: the NEW sink was born at
	     *    `0.008` and `mute true`, that is with the value the user had set in
	     *    a finished session.  It is exactly the invisible state I5 wants
	     *    to make impossible.
	     *
	     * ⚠ The key is a HINT: if the WirePlumber version does not know it
	     *   it does nothing and gives no error.  ⇒ We do not rely on it — the
	     *   volume is raised again anyway at every connection and every capture
	     *   start (`CODER.md` §I7: the protection lives in the program).
	     */
	    "state.restore-props", "false",
	    /* The node dies with our connection to PipeWire, and that is fine:
	     * it belongs to the served session, not to the machine.  Leaving it behind
	     * would mean that a restarted REMOTIX finds two — and then
	     * `target.object` would become ambiguous. */
	    PW_KEY_OBJECT_LINGER, "false", NULL);

	if (!proprieta)
	{
		registro_dice(REG_SUONO, "⛔ sink properties not allocated");
		return false;
	}

	s->sink = pw_core_create_object(s->nucleo, "adapter", PW_TYPE_INTERFACE_Node, PW_VERSION_NODE,
	                                &proprieta->dict, 0);
	pw_properties_free(proprieta);

	if (!s->sink)
	{
		registro_dice(REG_SUONO, "⛔ PipeWire did not create the virtual sink «%s»", NOME_SINK);
		return false;
	}
	pw_proxy_add_listener(s->sink, &s->gancio_sink, &eventi_sink, s);

	/* ⚠ We wait for the node's id, not the creation: `bound` is the moment the
	 *   server REALLY registered the object.  Whoever returned earlier would hold
	 *   a proxy that could still fail, and the refusal would show up later as
	 *   silence. */
	scadenza = registro_ora_ms() + ATTESA_SINK_MS;
	while (s->nodo == 0 && registro_ora_ms() < scadenza)
		pw_thread_loop_timed_wait(s->ciclo, 1);

	if (s->nodo == 0)
	{
		registro_dice(REG_SUONO, "⛔ the virtual sink was not registered within %d ms",
		              ATTESA_SINK_MS);
		return false;
	}
	alza(s);
	return true;
}

/* ⛔ `pw_init()` only once per process, and `cattura.c` calls it too:
 *    it is not synchronised by itself, and the child opens the stage and the sound
 *    at two different moments.  ⚠ `pthread_once` and not a `bool`, because "it
 *    usually happens first" is not a synchronisation. */
static pthread_once_t una_volta = PTHREAD_ONCE_INIT;

static void inizializza_pipewire(void)
{
	pw_init(NULL, NULL);
}

suono *suono_apri(void)
{
	suono *s = calloc(1, sizeof *s);

	if (!s)
		return NULL;
	pthread_once(&una_volta, inizializza_pipewire);

	atomic_init(&s->consegna, false);
	atomic_init(&s->in_richiamo, false);
	atomic_init(&s->blocchi, 0);
	atomic_init(&s->fotogrammi, 0);
	atomic_init(&s->scartati, 0);
	atomic_init(&s->picco, 0);

	s->ciclo = pw_thread_loop_new("remotix-suono", NULL);
	if (!s->ciclo)
	{
		registro_dice(REG_SUONO, "⛔ PipeWire loop not created");
		goto guasto;
	}
	s->contesto = pw_context_new(pw_thread_loop_get_loop(s->ciclo), NULL, 0);
	if (!s->contesto)
	{
		registro_dice(REG_SUONO, "⛔ PipeWire context not created");
		goto guasto;
	}

	pw_thread_loop_lock(s->ciclo);
	if (pw_thread_loop_start(s->ciclo) < 0)
	{
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ PipeWire thread not started");
		goto guasto;
	}

	s->nucleo = pw_context_connect(s->contesto, NULL, 0);
	if (!s->nucleo)
	{
		pw_thread_loop_unlock(s->ciclo);
		/* ⚠ The normal case in which this fails: `PIPEWIRE_RUNTIME_DIR` /
		 *   `XDG_RUNTIME_DIR` not pointing to the served session.  It is said
		 *   by name, or the diagnosis starts over from zero (`CODER.md` §3.7). */
		registro_dice(REG_SUONO, "⛔ connection to PipeWire failed: check XDG_RUNTIME_DIR "
		                         "and whether the service runs in the session");
		goto guasto;
	}

	if (!crea_sink(s))
	{
		pw_thread_loop_unlock(s->ciclo);
		goto guasto;
	}
	pw_thread_loop_unlock(s->ciclo);

	registro_dice(REG_SUONO, "⭐ audio sink «%s» mounted in the session: node %u, %d Hz, %d channels "
	                         "— it belongs to the SESSION, it survives detach (I4)",
	              NOME_SINK, s->nodo, (int) AUDIO_FREQUENZA, (int) AUDIO_CANALI);
	return s;

guasto:
	suono_chiudi(s);
	return NULL;
}

bool suono_ascolto_avvia(suono *s, suono_campioni su_campioni, void *chi)
{
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];
	struct spa_audio_info_raw formato = { 0 };
	struct pw_properties *proprieta;
	uint64_t scadenza;

	if (!s || !s->nucleo || !su_campioni)
		return false;

	/*
	 * ⛔ HERE, AND NOT ONLY AT CREATION.  Whoever restores saved levels does so
	 *    when the node APPEARS, that is right after we raised it: at
	 *    creation the race is lost, and the first connection after a restart
	 *    arrives mute.  The capture start is the latest moment we have
	 *    available, and by then the race is over.  `[M]` 8 August 2026.
	 */
	suono_volume_massimo(s);

	pw_thread_loop_lock(s->ciclo);

	if (s->flusso)
	{
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ the audio capture is already on: the second one does not open");
		return false;
	}

	s->su_campioni = su_campioni;
	s->chi = chi;
	s->stato = PW_STREAM_STATE_UNCONNECTED;
	atomic_store(&s->blocchi, 0);
	atomic_store(&s->fotogrammi, 0);
	atomic_store(&s->scartati, 0);
	atomic_store(&s->picco, 0);
	/* ⚠ On BEFORE connecting the stream, and switched off by `su_parametri` if the
	 *   negotiated format is not that of §5.3: the first callback may arrive
	 *   before this function returns. */
	atomic_store(&s->consegna, true);

	proprieta = pw_properties_new(PW_KEY_MEDIA_TYPE, "Audio", PW_KEY_MEDIA_CATEGORY, "Capture",
	                              /* The two lines that decide WHERE we capture from: the
	                               * MONITOR (the output) of our sink, and not
	                               * the input of a microphone that does not exist here. */
	                              PW_KEY_STREAM_CAPTURE_SINK, "true", PW_KEY_TARGET_OBJECT,
	                              NOME_SINK, PW_KEY_NODE_FORCE_QUANTUM, QUANTO_FORZATO, NULL);
	s->flusso = proprieta ? pw_stream_new(s->nucleo, "remotix-suono", proprieta) : NULL;
	if (!s->flusso)
	{
		atomic_store(&s->consegna, false);
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ PipeWire stream not created");
		return false;
	}
	pw_stream_add_listener(s->flusso, &s->gancio_flusso, &eventi_flusso, s);

	/*
	 * ⛔ THE FORMAT IS ASKED FIXED, and it is not a preference: `RCP.md` §5.3.
	 *    PipeWire resamples on its own between the sink and this stream, so between
	 *    the monitor and the wire no conversion is left to do — the
	 *    encoder already gets the right samples, and we need no resampler
	 *    of our own.  ⚠ Until 29 Sep 2026 the sentence said "we do not
	 *    depend on which resamplers `libavcodec` was built with":
	 *    since phase 18 libavcodec is gone, and `libopus` (`audio.c`)
	 *    has no resamplers — ⇒ the reason counts even more.
	 */
	formato.format = SPA_AUDIO_FORMAT_S16;
	formato.rate = AUDIO_FREQUENZA;
	formato.channels = AUDIO_CANALI;
	formato.position[0] = SPA_AUDIO_CHANNEL_FL;
	formato.position[1] = SPA_AUDIO_CHANNEL_FR;
	parametri[0] = spa_format_audio_raw_build(&costruttore, SPA_PARAM_EnumFormat, &formato);

	/* ⛔ `PW_STREAM_FLAG_RT_PROCESS`: the callback runs on the realtime
	 *    thread.  It is wanted — a hop through the main loop would be one more
	 *    quantum of latency on a link that has 50 in all — and the
	 *    price is the contract written in `suono.h`: inside one copies and returns. */
	if (pw_stream_connect(s->flusso, PW_DIRECTION_INPUT, PW_ID_ANY,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, 1) < 0)
	{
		pw_stream_destroy(s->flusso);
		s->flusso = NULL;
		atomic_store(&s->consegna, false);
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ attaching to the monitor of sink «%s» failed", NOME_SINK);
		return false;
	}

	/* ⛔ We wait for `paused`: it is the moment the format was negotiated,
	 *    that is the only one in which a refusal shows at once. */
	scadenza = registro_ora_ms() + ATTESA_ASCOLTO_MS;
	while (s->stato != PW_STREAM_STATE_PAUSED && s->stato != PW_STREAM_STATE_STREAMING &&
	       s->stato != PW_STREAM_STATE_ERROR && registro_ora_ms() < scadenza)
		pw_thread_loop_timed_wait(s->ciclo, 1);
	pw_thread_loop_unlock(s->ciclo);

	if (s->stato == PW_STREAM_STATE_ERROR)
	{
		registro_dice(REG_SUONO, "⛔ audio capture refused: %s",
		              s->guasto ? s->guasto : "no explanation");
		suono_ascolto_ferma(s);
		return false;
	}
	if (s->stato != PW_STREAM_STATE_PAUSED && s->stato != PW_STREAM_STATE_STREAMING)
	{
		registro_dice(REG_SUONO, "⛔ the audio capture gave no sign of life within %d ms",
		              ATTESA_ASCOLTO_MS);
		suono_ascolto_ferma(s);
		return false;
	}

	registro_dice(REG_SUONO,
	              "⭐ audio capture started from the monitor of «%s»: %d Hz, %d channels, s16, quantum %s "
	              "— ⚠ blocks have VARIABLE size, the listener accumulates (suono.h)",
	              NOME_SINK, (int) AUDIO_FREQUENZA, (int) AUDIO_CANALI, QUANTO_FORZATO);
	return true;
}

/*
 * ⛔⛔ THE PROMISED WAIT, AND DONE — v1 promised it and did NOT do it.
 *
 * v1's comment said: "The loop lock IS the wait promised in the header:
 * PipeWire holds it while it calls `su_processo`".  ⛔ It is FALSE
 * when the stream is connected with `PW_STREAM_FLAG_RT_PROCESS`, which is
 * precisely our case: `[R]` `pipewire/stream.h:150` and `:466` — the
 * callback comes from the **data thread**, which is another thread, and the
 * loop lock does not stop it at all.
 *
 * ⚠ The defect would almost never have shown: the window is microseconds, at
 *   every detach.  ⛔ And when it shows it is a segfault inside a thread that
 *   does not bear our name, holding the context of the connection just
 *   freed — that is the most expensive form of error there is, because nobody
 *   connects it to the reconnection that produced it.
 *
 * ⇒ The wait is in two steps, and the first does NOT depend on how
 *   `pw_stream_destroy()` is made inside:
 *
 *   1. `consegna` is switched off and we wait for `in_richiamo` to go back false.
 *      From here on no listener callback is in flight, and none will start
 *      again (the two sequentially consistent writes see each other: see
 *      `su_processo`).  ⭐ This, and only this, is what entitles the
 *      caller to free its context;
 *   2. the stream is destroyed holding the loop lock.  ⚠ That no
 *      `dequeue` is half way when the stream dies is the responsibility of
 *      `pw_stream_destroy()`, which removes the node from the data loop **between
 *      one quantum and the next** — it is the same guarantee every program
 *      using PipeWire rests on, and not something we can redo from outside.
 *
 * ⚠ The wait of step 1 is OUTSIDE the lock: taking it while waiting for the
 *   data thread would be the way to end up in the middle of a deadlock
 *   the day PipeWire changed its mind about who holds what.
 */
static void aspetta_richiamo(suono *s)
{
	uint64_t inizio = registro_ora_ms();

	while (atomic_load(&s->in_richiamo))
	{
		struct timespec pausa = { 0, 200 * 1000 }; /* 200 µs: a quantum is 5 ms */

		nanosleep(&pausa, NULL);
		if (registro_ora_ms() - inizio > ATTESA_BARRIERA_MS)
		{
			/* ⛔ We exit anyway, and it IS DECLARED.  Staying here forever
			 *    would mean a frozen session, and "an ugly session
			 *    is worth more than a closed session" (`CODER.md` §1) does not stretch
			 *    to "a hung session".  ⚠ But whoever reads this line knows that
			 *    the connection's context must NOT be freed: PipeWire has been
			 *    stuck inside a callback for two seconds. */
			registro_dice(REG_SUONO,
			              "⛔⛔ the realtime thread did not leave the callback within %d ms: "
			              "do NOT free the listening context — PipeWire is blocked",
			              ATTESA_BARRIERA_MS);
			return;
		}
	}
}

void suono_ascolto_ferma(suono *s)
{
	if (!s || !s->ciclo)
		return;

	/* 1. the barrier towards the listener (see the box). */
	atomic_store(&s->consegna, false);
	aspetta_richiamo(s);

	/* 2. the stream, under the loop lock. */
	pw_thread_loop_lock(s->ciclo);
	if (s->flusso)
	{
		struct pw_stream *flusso = s->flusso;
		uint64_t blocchi = atomic_load(&s->blocchi);
		uint64_t fotogrammi = atomic_load(&s->fotogrammi);
		uint64_t scartati = atomic_load(&s->scartati);

		s->flusso = NULL;
		pw_stream_destroy(flusso);
		/* ⭐ The summary is printed HERE, from the stopper's thread, and not from
		 *    the realtime thread that counted it.  ⚠ "zero blocks" is a
		 *    fact, not a void: it says the monitor delivered nothing,
		 *    and must be told apart from DISCARDED frames (refused format).
		 *
		 * ⛔⭐ AND THE PEAK IS READ BEFORE ANYTHING ELSE when someone says
		 *     "nothing can be heard":
		 *       · peak 0  with blocks > 0  ⇒ the samples arrive EMPTY —
		 *         nobody was playing in the session, or the monitor is not
		 *         connected.  Look at the graph (`pw-link -l`), and look at it
		 *         WHILE the session is alive;
		 *       · peak > 0                 ⇒ the sound entered REMOTIX, and
		 *         whoever loses it is further on (the ring, the encoder, the
		 *         datagrams).  `[M]` 17 August 2026: 16383 of 32767 with a 440 Hz
		 *         tone — that is exactly what `pw-record` reads from the
		 *         same monitor at the same instant. */
		registro_dice(REG_SUONO,
		              "audio capture stopped: %llu blocks, %llu frames delivered "
		              "(%llu s of sound), %llu frames discarded, PEAK %llu of 32767",
		              (unsigned long long) blocchi, (unsigned long long) fotogrammi,
		              (unsigned long long) (fotogrammi / AUDIO_FREQUENZA),
		              (unsigned long long) scartati,
		              (unsigned long long) atomic_load(&s->picco));
	}
	s->su_campioni = NULL;
	s->chi = NULL;
	pw_thread_loop_unlock(s->ciclo);
}

uint32_t suono_nodo(const suono *s)
{
	return s ? s->nodo : 0;
}

bool suono_ascolto_vivo(const suono *s)
{
	bool vivo;

	if (!s || !s->ciclo || !s->flusso)
		return false;
	/* ⚠ Under the lock because `stato` is written by the loop thread.  The
	 *   `const` is on the pointer to `suono`, not on the PipeWire loop: nothing
	 *   of ours changes here. */
	pw_thread_loop_lock(s->ciclo);
	vivo = s->flusso && (s->stato == PW_STREAM_STATE_PAUSED ||
	                     s->stato == PW_STREAM_STATE_STREAMING);
	pw_thread_loop_unlock(s->ciclo);
	return vivo;
}

void suono_conti(const suono *s, uint64_t *blocchi, uint64_t *fotogrammi, uint64_t *scartati)
{
	if (blocchi)
		*blocchi = s ? atomic_load(&s->blocchi) : 0;
	if (fotogrammi)
		*fotogrammi = s ? atomic_load(&s->fotogrammi) : 0;
	if (scartati)
		*scartati = s ? atomic_load(&s->scartati) : 0;
}

void suono_chiudi(suono *s)
{
	if (!s)
		return;

	/* ⛔ First the barrier and the stream, then the thread, then the rest — and the
	 *    order is that of `cattura.c`, for the same reason: so nothing a
	 *    callback is using is touched.  ⚠ `suono_ascolto_ferma()` copes with the
	 *    half-built object (the `goto guasto` case of `suono_apri`) because it
	 *    looks at `ciclo` and `flusso` before anything else. */
	suono_ascolto_ferma(s);

	if (s->ciclo)
		pw_thread_loop_stop(s->ciclo);
	if (s->sink)
		pw_proxy_destroy(s->sink);
	if (s->nucleo)
		pw_core_disconnect(s->nucleo);
	if (s->contesto)
		pw_context_destroy(s->contesto);
	if (s->ciclo)
		pw_thread_loop_destroy(s->ciclo);

	free(s->guasto);
	free(s);
}
