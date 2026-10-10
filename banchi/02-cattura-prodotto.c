/*
 * 02-cattura-prodotto — the SAME F2.2 bench, pointed at the PRODUCT.
 *
 * ===========================================================================
 * ⛔ WHY IT EXISTS, AND WHY I DID NOT TOUCH `02-cattura-fotogramma.c`
 *
 * The F2.2 bench was born before the product, and it is certified: `healthy 0 →
 * four faults 1 → healed 0`, `[M]` 12 Aug 2026.  ⛔ But what it
 * certified was the producer WRITTEN INSIDE THE BENCH — a PipeWire
 * consumer of its own, with its D-Bus sequence copied from `mutter.h`.  The product
 * did not exist yet.
 *
 * ⇒ A bench that measures a copy of the product **says nothing about the product**.
 *   It is the most insidious form of `LEZIONI.md` §1.3: green on code nobody
 *   has run yet.
 *
 * ⭐ This file is the same producer — same command line, same
 *    manifest, same four exit statuses, same two `.raw` — but capture
 *    is done by **`src/cattura.c` and `src/mutter.c`**, that is the product.  The judge
 *    (`02-cattura-giudica.py`) and the certification (`02-cattura-certifica.sh`)
 *    do not change by a line: they judge the pixels, and neither know nor want to
 *    know who produced them.
 *
 * ⭐ And the two producers both stay, because together they are a positive
 *    control neither of the two would be alone: **the same judge, the
 *    same scene, two independent producers**.  If the verdict changes
 *    when changing producer, the difference is in the producer — and one knows which.
 *
 * ===========================================================================
 * ⛔ WHAT THIS PROGRAM DOES **NOT** PROVE (form E1, `REVIEWER.md` §2)
 *
 *   `kind = MemFd`   ⛔ says nothing about where Mutter renders: here memory is
 *                    ASKED FOR, because phase 2 wants readable pixels.  It is the
 *                    answer to a question of ours, not a discovery
 *   `kind = DMA-BUF` does not prove rendering on the GPU: an open render node is
 *                    necessary, not sufficient
 *
 * ⚠ And it does not measure RATE, and must not: it copies 8 MB frames inside (and
 *   right out of) PipeWire's real-time callback.  Rate belongs to
 *   phase 0 (36 ± 2 `[M]`) and phase 3.
 *
 * ===========================================================================
 * usage: identical to 02-cattura-fotogramma, plus `--10bit`
 */

#include <glib.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "cattura.h"
#include "mutter.h"
#include "registro.h"

typedef struct
{
	gboolean taken;
	CaptureStopped stopped;
	const char *damage; /* "full" | "partial" | "assente" — the bench's words */
} Entry;

static const char *damage_name(const CaptureStopped *f)
{
	if (!f->declared_damage)
		return "assente";
	return f->damage_covers_all ? "full" : "partial";
}

static void manifest_entry(GString *s, const char *key_id, const Entry *v, const char *file)
{
	if (!v->taken)
	{
		g_string_append_printf(s, "  \"%s\": null,\n", key_id);
		return;
	}
	g_string_append_printf(s,
	                       "  \"%s\": {\n"
	                       "    \"file\": \"%s\",\n"
	                       "    \"byte\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"stride\": %u,\n"
	                       "    \"offset\": 0,\n"
	                       "    \"chunk_size\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"tipo_dichiarato\": \"%s\",\n"
	                       "    \"damage\": \"%s\",\n"
	                       "    \"indice_fra_gli_arrivati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"seq\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"pts\": %" G_GINT64_FORMAT ",\n"
	                       "    \"seq_valid\": %s,\n"
	                       /* ⭐ The measurement the producer does NOT declare, made by us
	                        *    on the delivered pixels — and written as a measurement. */
	                       "    \"measured_range\": {\"min\": [%u, %u, %u], "
	                       "\"max\": [%u, %u, %u], \"outcome\": \"%s\"},\n"
	                       "    \"nero\": %s,\n"
	                       "    \"uniform\": %s\n"
	                       "  },\n",
	                       key_id, file, v->stopped.byte, v->stopped.stride, v->stopped.byte,
	                       capture_buffer_name(v->stopped.delivery.buffer_declared), v->damage,
	                       v->stopped.idx, v->stopped.seq, v->stopped.pts,
	                       v->stopped.seq_valid ? "true" : "false", v->stopped.delivery.minimum[0],
	                       v->stopped.delivery.minimum[1], v->stopped.delivery.minimum[2],
	                       v->stopped.delivery.maximum[0], v->stopped.delivery.maximum[1],
	                       v->stopped.delivery.maximum[2],
	                       capture_range_measured_name(v->stopped.delivery.measured_range),
	                       v->stopped.delivery.nero ? "true" : "false",
	                       v->stopped.delivery.uniform ? "true" : "false");
}

int main(int argc, char **argv)
{
	uint32_t width_px = 1920, height_px = 1080, fps = 60, node = 0;
	double post_scene = 3.0, duration = 12.0, wait_scene = 25.0;
	guint64 discard = 10, min_after_scene = 1;
	CaptureRoute route = CAPTURE_ROUTE_MEMORY;
	CaptureColor color = CAPTURE_COLOR_BGRX;
	const char *label = "senza-nome";
	const char *out_dir = NULL, *ready = NULL, *scene_signal = NULL;
	const char *requested_color_name = "BGRx";
	MutterSession *session_v = NULL;
	Capture *capture_v = NULL;
	Entry first = { 0 }, regime = { 0 };
	CaptureDelivery delivery;
	CaptureCounts count;
	guint64 before_scene = 0, after_scene = 0;
	g_autoptr(GError) mistake = NULL;
	g_autofree char *first_file = NULL, *file_regime = NULL, *file_json = NULL;
	GString *manifesto;
	gint64 expiry, fine;
	int code_v = 0, i;
	const char *outcome;
	char when[64];
	time_t now_epoch;
	struct tm now_tm;

	for (i = 1; i < argc; i++)
	{
		if (!strcmp(argv[i], "--out_dir") && i + 1 < argc)
			out_dir = argv[++i];
		else if (!strcmp(argv[i], "--ready") && i + 1 < argc)
			ready = argv[++i];
		else if (!strcmp(argv[i], "--scene-signal") && i + 1 < argc)
			scene_signal = argv[++i];
		else if (!strcmp(argv[i], "--node") && i + 1 < argc)
			node = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--width_px") && i + 1 < argc)
			width_px = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--height_px") && i + 1 < argc)
			height_px = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fps") && i + 1 < argc)
			fps = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--post-scene") && i + 1 < argc)
			post_scene = atof(argv[++i]);
		else if (!strcmp(argv[i], "--wait-scene") && i + 1 < argc)
			wait_scene = atof(argv[++i]);
		else if (!strcmp(argv[i], "--duration") && i + 1 < argc)
			duration = atof(argv[++i]);
		else if (!strcmp(argv[i], "--discard") && i + 1 < argc)
			discard = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--min-after-scene") && i + 1 < argc)
			min_after_scene = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--dmabuf"))
			route = CAPTURE_ROUTE_CARD;
		else if (!strcmp(argv[i], "--bgra"))
		{
			color = CAPTURE_COLOR_BGRA;
			requested_color_name = "BGRA";
		}
		else if (!strcmp(argv[i], "--10bit"))
		{
			/* ⭐ THE TEN-BIT QUESTION, PUT TO THE PRODUCER.
			 *
			 * `STUDI.md` §gnome §8.3 `[R]` says Mutter delivers only BGRx and BGRA.
			 * Asking for a ten-bit format and receiving a refusal turns
			 * that reading into a MEASUREMENT — and the refusal must be written, not
			 * deduced (`LEZIONI.md` §1.11). */
			color = CAPTURE_COLOR_10BIT;
			requested_color_name = "10 bits (xBGR_210LE and companions)";
		}
		else if (!strcmp(argv[i], "--label") && i + 1 < argc)
			label = argv[++i];
		else if (!strcmp(argv[i], "--chatter"))
			log_chatter(TRUE);
		else
		{
			/* ⛔ And it says WHICH argument was not understood.  The first draft
			 *    printed only the usage line, and on 12 Aug 2026 it cost a
			 *    whole round: `--label` was missing, the bench read «exit 2»
			 *    and the help line, and from outside it looked like a producer
			 *    that does not start.  It is `FASI.md` §00-ambiente B3 point 2 — *an option
			 *    refused is not a defect of the target*. */
			fprintf(stderr,
			        "⛔ I do not understand the argument «%s».\n"
			        "usage: %s --out_dir PFX --ready FILE --scene-signal FILE\n"
			        "        [--width_px W] [--height_px H] [--fps N] [--bgra] [--dmabuf]\n"
			        "        [--10bit] [--post-scene S] [--discard N] [--duration S]\n"
			        "        [--wait-scene S] [--min-after-scene N] [--label T]\n"
			        "        [--node N] [--chatter]\n",
			        argv[i], argv[0]);
			return 2;
		}
	}
	if (!out_dir || !ready || !scene_signal)
	{
		fprintf(stderr, "⛔ --out_dir, --ready and --scene-signal are needed: the order between the "
		                "monitor and the scene is an EVENT, not a timed wait.\n");
		return 2;
	}

	first_file = g_strdup_printf("%s-primo.raw", out_dir);
	file_regime = g_strdup_printf("%s-regime.raw", out_dir);
	file_json = g_strdup_printf("%s.json", out_dir);

	now_epoch = time(NULL);
	gmtime_r(&now_epoch, &now_tm);
	strftime(when, sizeof when, "%Y-%m-%dT%H:%M:%SZ", &now_tm);

	fprintf(stderr, "== %s: requested %ux%u, %s, ceiling %u fps, road %s ==\n", label, width_px,
	        height_px, requested_color_name, fps,
	        route == CAPTURE_ROUTE_CARD ? "card (DMA-BUF)" : "memory");
	fprintf(stderr, "   the producer is THE PRODUCT: src/cattura.c + src/mutter.c\n");

	/* --- the stage ------------------------------------------------------- */
	if (node == 0)
	{
		session_v = mutter_open(&mistake);
		if (!session_v)
		{
			fprintf(stderr, "⛔ virtual monitor not mounted: %s\n", mistake->message);
			return 1;
		}
		node = mutter_node(session_v);
	}

	/* --- the capture ----------------------------------------------------- */
	capture_v = capture_start(node, width_px, height_px, fps, route, color, NULL, NULL, NULL,
	                        &mistake);
	if (!capture_v)
	{
		printf("FAULT\t%s\t%s\n", label, mistake->message);
		fprintf(stderr, "⛔ FAILED: %s\n", mistake->message);
		mutter_close(session_v);
		return 2;
	}

	/* The stream is waited for to be really ACTIVE before saying «pronto»:
	 * writing it before would mean switching the scene on on a monitor that does not
	 * exist yet. */
	expiry = g_get_monotonic_time() + 10 * G_USEC_PER_SEC;
	while (!capture_active(capture_v) && g_get_monotonic_time() < expiry)
		g_usleep(20000);
	if (!capture_active(capture_v))
	{
		printf("FAULT\t%s\tstream never active\n", label);
		fprintf(stderr, "⛔ FAILED (not «zero»): the stream never became active%s%s.\n",
		        capture_fault(capture_v) ? " — " : "",
		        capture_fault(capture_v) ? capture_fault(capture_v) : "");
		capture_stop(capture_v);
		mutter_close(session_v);
		return 2;
	}

	/* ⛔ AND NOW — not before — we ask WHAT our screen IS CALLED.
	 *    The virtual monitor appears when the consumer hooks on, `[M]`, and
	 *    this is also the moment the name is needed: the scene opens after,
	 *    and must be sent to THIS screen by name (`CODER.md` §3.9). */
	if (session_v)
	{
		mutter_find_monitor(session_v);
		fprintf(stderr, "   our monitor: %s («%s»)\n",
		        mutter_our_monitor(session_v) ? mutter_our_monitor(session_v) : "I DO NOT KNOW",
		        mutter_monitor_product(session_v) ? mutter_monitor_product(session_v) : "—");
	}

	/* --- the «primo» frame: before the scene exists ---------------------- *
	 * ⛔ E9 (`CODER.md` §3.5) for a still image: the start-up sample is not
	 *    a defect — it is the PRODUCT, what whoever connects now sees. The
	 *    defect would be measuring it and writing the number in a column that
	 *    phase 3 will read as steady state.  ⇒ Two frames, two files, and the manifest
	 *    says for each which it was among those arrived. */
	{
		CaptureTake p = capture_take(capture_v, 3.0, &first.stopped, &mistake);

		if (p == CAPTURE_TAKE_DONE)
		{
			first.taken = TRUE;
			first.damage = damage_name(&first.stopped);
		}
		else if (p == CAPTURE_TAKE_FAULT)
		{
			printf("FAULT\t%s\t%s\n", label, mistake->message);
			fprintf(stderr, "⛔ FAILED on the «first»: %s\n", mistake->message);
			capture_stop(capture_v);
			mutter_close(session_v);
			return 2;
		}
		else if (p == CAPTURE_TAKE_PIXEL_ELSEWHERE)
		{
			first.taken = FALSE; /* the pixels live on the card: it is said, not faked */
		}
		g_clear_error(&mistake);
	}

	if (!g_file_set_contents(ready, "ready\n", -1, &mistake))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", ready, mistake->message);
		capture_stop(capture_v);
		mutter_close(session_v);
		return 1;
	}
	fprintf(stderr, "  ready: the scene can be switched on now\n");

	/* --- wait for the launcher to declare the scene on ------------------- */
	expiry = g_get_monotonic_time() + (gint64) (wait_scene * G_USEC_PER_SEC);
	while (!g_file_test(scene_signal, G_FILE_TEST_EXISTS) && g_get_monotonic_time() < expiry)
		g_usleep(50000);
	if (!g_file_test(scene_signal, G_FILE_TEST_EXISTS))
	{
		printf("FAULT\t%s\tthe scene was never declared on\n", label);
		fprintf(stderr, "⛔ FAILED: after %.1f s nobody declared the scene on.\n",
		        wait_scene);
		capture_stop(capture_v);
		mutter_close(session_v);
		return 2;
	}
	capture_counts(capture_v, &count);
	before_scene = count.arrived;
	fine = g_get_monotonic_time() + (gint64) (duration * G_USEC_PER_SEC);
	fprintf(stderr, "  scene on: %" G_GUINT64_FORMAT " frames had already arrived\n",
	        before_scene);

	/* --- the «regime» frame ---------------------------------------------- *
	 * `--post-scene` is let pass, `--discard` frames are thrown away (they are
	 * the switching on of the scene, not the steady state), and then **the last one of the
	 * window** is taken: so the damage it carries is the steady-state one. */
	g_usleep((gulong) (post_scene * G_USEC_PER_SEC));
	for (i = 0; (guint64) i < discard && g_get_monotonic_time() < fine; i++)
	{
		CaptureStopped discarded = { 0 };

		if (capture_take(capture_v, 0.5, &discarded, &mistake) == CAPTURE_TAKE_FAULT)
			break;
		capture_stopped_free(&discarded);
		g_clear_error(&mistake);
	}
	g_clear_error(&mistake);

	while (g_get_monotonic_time() < fine - (gint64) (0.7 * G_USEC_PER_SEC))
		g_usleep(50000);

	{
		CaptureTake p = capture_take(capture_v, 1.5, &regime.stopped, &mistake);

		if (p == CAPTURE_TAKE_DONE)
		{
			regime.taken = TRUE;
			regime.damage = damage_name(&regime.stopped);
		}
		else if (p == CAPTURE_TAKE_FAULT)
		{
			printf("FAULT\t%s\t%s\n", label, mistake->message);
			fprintf(stderr, "⛔ FAILED on the «regime»: %s\n", mistake->message);
			capture_stopped_free(&first.stopped);
			capture_stop(capture_v);
			mutter_close(session_v);
			return 2;
		}
		g_clear_error(&mistake);
	}

	/* --- the guards, BEFORE writing any number --------------------------- */
	if (!capture_active(capture_v))
	{
		printf("FAULT\t%s\tstream dropped during the take\n", label);
		fprintf(stderr, "⛔ FAILED (not «zero»): the stream was active and dropped.\n");
		capture_stop(capture_v);
		mutter_close(session_v);
		return 2;
	}
	capture_counts(capture_v, &count);
	after_scene = count.arrived - before_scene;

	/*
	 * ⛔ A LIVE SCENE AND ZERO FRAMES IS NOT A ZERO: IT IS A FAULT.
	 *
	 * On 12 Aug 2026 this bench came out GREEN while the defect was alive:
	 * the session already had a monitor, `mpv --fs` went full screen on
	 * THAT one, and our capture received zero.  With a scene declared alive and
	 * moving, zero frames is the proof that we are looking at a screen
	 * different from the one the scene paints on.
	 */
	if (after_scene < min_after_scene)
	{
		printf("FAULT\t%s\tlive scene and %" G_GUINT64_FORMAT " frames after\n", label,
		       after_scene);
		fprintf(stderr,
		        "⛔ FAILED (not «zero»): the scene was declared alive and there arrived\n"
		        "   %" G_GUINT64_FORMAT " frames after it (minimum required %" G_GUINT64_FORMAT
		        ").\n   Before the scene %" G_GUINT64_FORMAT
		        " had arrived: the stream works.\n"
		        "   ⇒ It is not the still desktop: it is that the scene paints on a DIFFERENT SCREEN\n"
		        "     from the one we are capturing (ours is %s).\n",
		        after_scene, min_after_scene, before_scene,
		        session_v && mutter_our_monitor(session_v) ? mutter_our_monitor(session_v)
		                                                    : "unknown");
		capture_stopped_free(&first.stopped);
		capture_stopped_free(&regime.stopped);
		capture_stop(capture_v);
		mutter_close(session_v);
		return 2;
	}

	/* --- the writing ----------------------------------------------------- */
	if (!capture_delivery(capture_v, &delivery))
	{
		printf("FAULT\t%s\tno format negotiated\n", label);
		fprintf(stderr, "⛔ FAILED: no format was negotiated: there is nothing to "
		                "declare, and I do not write zeros in its place.\n");
		capture_stop(capture_v);
		mutter_close(session_v);
		return 2;
	}

	if (count.arrived == 0)
	{
		outcome = "ZERO FRAMES";
		code_v = 3;
	}
	else if (route == CAPTURE_ROUTE_CARD)
	{
		outcome = "TYPE DECLARED, PIXELS NOT READ (dmabuf)";
		code_v = 0;
	}
	else if (!first.taken && !regime.taken)
	{
		printf("FAULT\t%s\tframes arrived but none copyable\n", label);
		fprintf(stderr, "⛔ FAILED: %" G_GUINT64_FORMAT " frames arrived and none "
		                "had readable pixels.\n",
		        count.arrived);
		capture_stop(capture_v);
		mutter_close(session_v);
		return 2;
	}
	else
	{
		outcome = "ONE FRAME";
		code_v = 0;
		if (first.taken &&
		    !g_file_set_contents(first_file, (const char *) first.stopped.pixel,
		                         (gssize) first.stopped.byte, &mistake))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", first_file, mistake->message);
			capture_stop(capture_v);
			mutter_close(session_v);
			return 1;
		}
		if (regime.taken &&
		    !g_file_set_contents(file_regime, (const char *) regime.stopped.pixel,
		                         (gssize) regime.stopped.byte, &mistake))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", file_regime, mistake->message);
			capture_stop(capture_v);
			mutter_close(session_v);
			return 1;
		}
	}

	/* --- the manifest ---------------------------------------------------- */
	manifesto = g_string_new("{\n");
	g_string_append_printf(manifesto,
	                       "  \"instrument\": \"02-cattura-prodotto (src/cattura.c + "
	                       "src/mutter.c)\",\n"
	                       "  \"label\": \"%s\",\n"
	                       "  \"quando_utc\": \"%s\",\n"
	                       "  \"nodo_pipewire\": %u,\n"
	                       "  \"outcome\": \"%s\",\n"
	                       "  \"out_dir\": %d,\n",
	                       label, when, node, outcome, code_v);
	g_string_append_printf(manifesto,
	                       "  \"requested\": {\n"
	                       "    \"width_px\": %u, \"height_px\": %u, \"fps_massimi\": %u,\n"
	                       "    \"color\": \"%s\", \"route\": \"%s\",\n"
	                       "    \"cadence\": \"0/1 with maxFramerate at %u — «send me a "
	                       "frame when something changes»\"\n"
	                       "  },\n",
	                       width_px, height_px, fps,
	                       color == CAPTURE_COLOR_BGRA ? "BGRA"
	                       : color == CAPTURE_COLOR_10BIT ? "10bit"
	                                                        : "BGRx",
	                       route == CAPTURE_ROUTE_CARD ? "dmabuf" : "mem_buf", fps);
	g_string_append_printf(manifesto,
	                       "  \"negotiated\": {\n"
	                       "    \"known\": %s,\n"
	                       "    \"width_px\": %u, \"height_px\": %u,\n"
	                       "    \"color\": \"%s\",\n"
	                       "    \"modifier\": \"0x%" G_GINT64_MODIFIER "x\",\n"
	                       "    \"chi_lo_dice\": \"PipeWire, SPA_PARAM_Format in the param_changed "
	                       "callback — it is not the label we gave it\"\n"
	                       "  },\n",
	                       delivery.known ? "true" : "false", delivery.width_px, delivery.height_px,
	                       delivery.schema, (guint64) delivery.modifier);

	g_string_append_printf(
	    manifesto,
	    "  \"consegna_a_F2_3\": {\n"
	    "    \"bit_per_channel\": %d,\n"
	    "    \"bit_per_canale_chi_lo_dice\": \"the negotiated FORMAT (%s), %s. STUDI.md §gnome §8.3 "
	    "[R]: supported_formats[] of Mutter 48.7 has TWO entries, BGRx and BGRA — from this "
	    "capture ten real bits do NOT come out\",\n"
	    "    \"⛔ F2.3-A\": \"an HEVC Main10 fed from here carries 8 bits promoted to 10: "
	    "the label says Main10, the image comes out fine anyway, and the defendant is THE "
	    "CAPTURE, not the encoder\",\n"
	    "    \"stride\": %u,\n"
	    "    \"stride_chi_lo_dice\": \"⛔ READ from the buffer chunk, never computed as "
	    "width×4 — today it coincides, and precisely for this the rule must be written\",\n"
	    "    \"byte_per_fotogramma\": %" G_GUINT64_FORMAT ",\n"
	    "    \"range\": \"%s\",\n"
	    "    \"matrix\": \"%s\",\n"
	    "    \"transfer\": \"%s\",\n"
	    "    \"primari\": \"%s\",\n"
	    "    \"chi_lo_dice\": \"spa_video_info_raw.color_range / .color_matrix / "
	    ".transfer_function / .color_primaries, filled by spa_format_video_raw_parse on the "
	    "producer's SPA_PARAM_Format\",\n"
	    "    \"⚠ sulla matrix\": \"at capture the pixels are RGB: no 601/709 matrix "
	    "was applied by us. The matrix is CHOSEN by F2.3 when converting to YCbCr, and "
	    "F2.6 must compare with the same one — a comparison made with the wrong matrix "
	    "measures the matrix\",\n"
	    "    \"range_misurato_dal_prodotto\": \"%s\",\n"
	    "    \"valori_grezzi\": {\"color_range\": %u, \"color_matrix\": %u, "
	    "\"transfer_function\": %u, \"color_primaries\": %u}\n"
	    "  },\n",
	    delivery.bit_per_channel, delivery.schema, capture_source_name(delivery.source_bit),
	    /* ⛔ The stride is read from WHATEVER frame arrived, even from one
	     *    without pixels: on the card road the pixels are not here, but the
	     *    stride is a fact of the chunk, and it is one of the four that are
	     *    declared downstream.  Writing 0 there would be a silence passed off
	     *    as a number. */
	    regime.stopped.stride ? regime.stopped.stride : first.stopped.stride,
	    regime.stopped.byte ? regime.stopped.byte
	                      : (guint64) (regime.stopped.stride ? regime.stopped.stride
	                                                       : first.stopped.stride) *
	                            delivery.height_px,
	    capture_range_name(delivery.raw_range), capture_matrix_name(delivery.raw_matrix),
	    capture_transfer_name(delivery.raw_transfer),
	    capture_primaries_name(delivery.raw_primaries),
	    capture_range_measured_name(regime.taken ? regime.stopped.delivery.measured_range
	                                             : CAPTURE_RANGE_UNMEASURED),
	    delivery.raw_range, delivery.raw_matrix, delivery.raw_transfer,
	    delivery.raw_primaries);

	g_string_append(manifesto, "  \"buffer\": {\n    \"seen_types\": [");
	for (i = 0; (guint) i < count.how_many_types; i++)
		g_string_append_printf(manifesto, "%s\"%s\"", i ? ", " : "",
		                       capture_buffer_name(count.seen_types[i]));
	g_string_append_printf(manifesto,
	                       "],\n"
	                       "    \"requested\": \"%s\",\n"
	                       "    \"distinti_riciclati\": %u,\n"
	                       "    \"chi_lo_dice\": \"PipeWire, spa_data.type of plane 0 of every "
	                       "buffer — asked for in TWO places (the modifier in the format and "
	                       "SPA_PARAM_BUFFERS_dataType)\"\n"
	                       "  },\n",
	                       capture_buffer_name(delivery.buffer_requested), count.distinct_buffers);

	g_string_append_printf(manifesto,
	                       "  \"frames\": {\n"
	                       "    \"minimo_dopo_la_scena_preteso\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"arrivati_in_tutto\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"before_scene\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"after_scene\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"full_damage\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"partial_damage\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"missing_damage\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"without_header\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"solo_cursore_scartati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"stride_zero_scartati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"senza_pixel_scartati\": %" G_GUINT64_FORMAT "\n"
	                       "  },\n",
	                       min_after_scene, count.arrived, before_scene, after_scene,
	                       count.full_damage, count.partial_damage, count.missing_damage,
	                       count.without_header, count.cursor_only, count.stride_zero,
	                       count.without_pixel);

	g_string_append_printf(manifesto,
	                       "  \"display_screen\": {\n"
	                       "    \"connector\": \"%s\",\n"
	                       "    \"product\": \"%s\",\n"
	                       "    \"chi_lo_dice\": \"DisplayConfig.GetCurrentState before and after "
	                       "RecordVirtual, plus the PRODUCT name: two independent roads "
	                       "that must agree, because the two virtual monitors of the server "
	                       "are BOTH 1920×1080@60\"\n"
	                       "  },\n",
	                       session_v && mutter_our_monitor(session_v)
	                           ? mutter_our_monitor(session_v)
	                           : "I DO NOT KNOW",
	                       session_v && mutter_monitor_product(session_v)
	                           ? mutter_monitor_product(session_v)
	                           : "—");

	manifest_entry(manifesto, "first", &first, first_file);
	manifest_entry(manifesto, "regime", &regime, file_regime);

	g_string_append(manifesto,
	                "  \"avvertenze\": [\n"
	                "    \"⛔ E1 — the buffer type does NOT say where Mutter renders. A MemFd here is "
	                "the answer to what WE ASKED for (readable pixels are needed), not "
	                "a discovery about the compositor. LEZIONI.md §1.11.\",\n"
	                "    \"⛔ E1 — nor the opposite: a DMA-BUF does not prove rendering on the "
	                "GPU. An open render node is necessary, not sufficient.\",\n"
	                "    \"⚠ this tool does NOT measure rate: it copies 8 MB frames "
	                "inside the real-time callback. Rate belongs to phase 0 (36 ± 2) and "
	                "phase 3.\",\n"
	                "    \"⚠ the 0-255 range is MEASURED by us on the pixels, not declared by the "
	                "producer, and it depends on the scene: a scene without full black and white does not "
	                "reach the extremes, and that would NOT prove a limited range.\",\n"
	                "    \"⚠ the machine has TWO GPUs: a buffer of the wrong card cannot be "
	                "imported, and the symptom is software composition without an error "
	                "anywhere. On the memory road the pixels arrive anyway: this "
	                "round would NOT see it.\"\n"
	                "  ]\n}\n");

	if (!g_file_set_contents(file_json, manifesto->str, -1, &mistake))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", file_json, mistake->message);
		g_string_free(manifesto, TRUE);
		capture_stop(capture_v);
		mutter_close(session_v);
		return 1;
	}
	g_string_free(manifesto, TRUE);

	printf("PRESA\t%s\t%s\t%s\t%" G_GUINT64_FORMAT "\t%" G_GUINT64_FORMAT "\t%s\n", label,
	       outcome, file_json, count.arrived, after_scene,
	       capture_buffer_name(delivery.buffer_declared));
	fprintf(stderr,
	        "  outcome: %s\n"
	        "  arrived %" G_GUINT64_FORMAT " (before the scene %" G_GUINT64_FORMAT ", after %"
	        G_GUINT64_FORMAT ")\n"
	        "  damage: full %" G_GUINT64_FORMAT ", partial %" G_GUINT64_FORMAT ", absent %"
	        G_GUINT64_FORMAT "\n"
	        "  distinct recycled buffers: %u · declared type: %s\n"
	        "  stride READ: %u · bytes: %" G_GUINT64_FORMAT "\n"
	        "  manifest: %s\n",
	        outcome, count.arrived, before_scene, after_scene, count.full_damage,
	        count.partial_damage, count.missing_damage, count.distinct_buffers,
	        capture_buffer_name(delivery.buffer_declared),
	        regime.stopped.stride ? regime.stopped.stride : first.stopped.stride, regime.stopped.byte,
	        file_json);

	capture_stopped_free(&first.stopped);
	capture_stopped_free(&regime.stopped);
	capture_stop(capture_v);
	mutter_close(session_v);
	return code_v;
}
