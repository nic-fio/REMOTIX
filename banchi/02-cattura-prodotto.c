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
 *   `tipo = MemFd`   ⛔ says nothing about where Mutter renders: here memory is
 *                    ASKED FOR, because phase 2 wants readable pixels.  It is the
 *                    answer to a question of ours, not a discovery
 *   `tipo = DMA-BUF` does not prove rendering on the GPU: an open render node is
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
	gboolean preso;
	CatturaFermo fermo;
	const char *danno; /* "pieno" | "parziale" | "assente" — the bench's words */
} Voce;

static const char *damage_name(const CatturaFermo *f)
{
	if (!f->declared_damage)
		return "assente";
	return f->damage_covers_all ? "pieno" : "parziale";
}

static void manifest_entry(GString *s, const char *chiave, const Voce *v, const char *file)
{
	if (!v->preso)
	{
		g_string_append_printf(s, "  \"%s\": null,\n", chiave);
		return;
	}
	g_string_append_printf(s,
	                       "  \"%s\": {\n"
	                       "    \"file\": \"%s\",\n"
	                       "    \"byte\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"stride\": %u,\n"
	                       "    \"offset\": 0,\n"
	                       "    \"dimensione_chunk\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"tipo_dichiarato\": \"%s\",\n"
	                       "    \"danno\": \"%s\",\n"
	                       "    \"indice_fra_gli_arrivati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"seq\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"pts\": %" G_GINT64_FORMAT ",\n"
	                       "    \"seq_nota\": %s,\n"
	                       /* ⭐ The measurement the producer does NOT declare, made by us
	                        *    on the delivered pixels — and written as a measurement. */
	                       "    \"range_misurato\": {\"min\": [%u, %u, %u], "
	                       "\"max\": [%u, %u, %u], \"esito\": \"%s\"},\n"
	                       "    \"nero\": %s,\n"
	                       "    \"uniforme\": %s\n"
	                       "  },\n",
	                       chiave, file, v->fermo.byte, v->fermo.stride, v->fermo.byte,
	                       capture_buffer_name(v->fermo.consegna.buffer_dichiarato), v->danno,
	                       v->fermo.indice, v->fermo.seq, v->fermo.pts,
	                       v->fermo.seq_nota ? "true" : "false", v->fermo.consegna.minimo[0],
	                       v->fermo.consegna.minimo[1], v->fermo.consegna.minimo[2],
	                       v->fermo.consegna.massimo[0], v->fermo.consegna.massimo[1],
	                       v->fermo.consegna.massimo[2],
	                       capture_range_measured_name(v->fermo.consegna.range_misurato),
	                       v->fermo.consegna.nero ? "true" : "false",
	                       v->fermo.consegna.uniforme ? "true" : "false");
}

int main(int argc, char **argv)
{
	uint32_t larghezza = 1920, altezza = 1080, fps = 60, nodo = 0;
	double dopo_scena = 3.0, durata = 12.0, attesa_scena = 25.0;
	guint64 scarta = 10, minimo_dopo_scena = 1;
	CaptureRoute strada = CATTURA_STRADA_MEMORIA;
	CaptureColor colore = CATTURA_COLORE_BGRX;
	const char *etichetta = "senza-nome";
	const char *uscita = NULL, *pronto = NULL, *segnale_scena = NULL;
	const char *requested_color_name = "BGRx";
	MutterSessione *sessione = NULL;
	Cattura *cattura = NULL;
	Voce primo = { 0 }, regime = { 0 };
	CatturaConsegna consegna;
	CatturaConteggi conto;
	guint64 prima_della_scena = 0, dopo_la_scena = 0;
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *first_file = NULL, *file_regime = NULL, *file_json = NULL;
	GString *manifesto;
	gint64 scadenza, fine;
	int codice = 0, i;
	const char *esito;
	char quando[64];
	time_t now_epoch;
	struct tm now_tm;

	for (i = 1; i < argc; i++)
	{
		if (!strcmp(argv[i], "--uscita") && i + 1 < argc)
			uscita = argv[++i];
		else if (!strcmp(argv[i], "--pronto") && i + 1 < argc)
			pronto = argv[++i];
		else if (!strcmp(argv[i], "--segnale-scena") && i + 1 < argc)
			segnale_scena = argv[++i];
		else if (!strcmp(argv[i], "--nodo") && i + 1 < argc)
			nodo = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--larghezza") && i + 1 < argc)
			larghezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--altezza") && i + 1 < argc)
			altezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fps") && i + 1 < argc)
			fps = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--dopo-scena") && i + 1 < argc)
			dopo_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--attesa-scena") && i + 1 < argc)
			attesa_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--durata") && i + 1 < argc)
			durata = atof(argv[++i]);
		else if (!strcmp(argv[i], "--scarta") && i + 1 < argc)
			scarta = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--minimo-dopo-scena") && i + 1 < argc)
			minimo_dopo_scena = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--dmabuf"))
			strada = CATTURA_STRADA_SCHEDA;
		else if (!strcmp(argv[i], "--bgra"))
		{
			colore = CAPTURE_COLOR_BGRA;
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
			colore = CAPTURE_COLOR_10BIT;
			requested_color_name = "10 bits (xBGR_210LE and companions)";
		}
		else if (!strcmp(argv[i], "--etichetta") && i + 1 < argc)
			etichetta = argv[++i];
		else if (!strcmp(argv[i], "--parlantina"))
			registro_parlantina(TRUE);
		else
		{
			/* ⛔ And it says WHICH argument was not understood.  The first draft
			 *    printed only the usage line, and on 12 Aug 2026 it cost a
			 *    whole round: `--etichetta` was missing, the bench read «exit 2»
			 *    and the help line, and from outside it looked like a producer
			 *    that does not start.  It is `FASI.md` §00-ambiente B3 point 2 — *an option
			 *    refused is not a defect of the target*. */
			fprintf(stderr,
			        "⛔ I do not understand the argument «%s».\n"
			        "usage: %s --uscita PREFISSO --pronto FILE --segnale-scena FILE\n"
			        "        [--larghezza W] [--altezza H] [--fps N] [--bgra] [--dmabuf]\n"
			        "        [--10bit] [--dopo-scena S] [--scarta N] [--durata S]\n"
			        "        [--attesa-scena S] [--minimo-dopo-scena N] [--etichetta T]\n"
			        "        [--nodo N] [--parlantina]\n",
			        argv[i], argv[0]);
			return 2;
		}
	}
	if (!uscita || !pronto || !segnale_scena)
	{
		fprintf(stderr, "⛔ --uscita, --pronto and --segnale-scena are needed: the order between the "
		                "monitor and the scene is an EVENT, not a timed wait.\n");
		return 2;
	}

	first_file = g_strdup_printf("%s-primo.raw", uscita);
	file_regime = g_strdup_printf("%s-regime.raw", uscita);
	file_json = g_strdup_printf("%s.json", uscita);

	now_epoch = time(NULL);
	gmtime_r(&now_epoch, &now_tm);
	strftime(quando, sizeof quando, "%Y-%m-%dT%H:%M:%SZ", &now_tm);

	fprintf(stderr, "== %s: requested %ux%u, %s, ceiling %u fps, road %s ==\n", etichetta, larghezza,
	        altezza, requested_color_name, fps,
	        strada == CATTURA_STRADA_SCHEDA ? "card (DMA-BUF)" : "memory");
	fprintf(stderr, "   the producer is THE PRODUCT: src/cattura.c + src/mutter.c\n");

	/* --- the stage ------------------------------------------------------- */
	if (nodo == 0)
	{
		sessione = mutter_apri(&sbaglio);
		if (!sessione)
		{
			fprintf(stderr, "⛔ virtual monitor not mounted: %s\n", sbaglio->message);
			return 1;
		}
		nodo = mutter_nodo(sessione);
	}

	/* --- the capture ----------------------------------------------------- */
	cattura = cattura_avvia(nodo, larghezza, altezza, fps, strada, colore, NULL, NULL, NULL,
	                        &sbaglio);
	if (!cattura)
	{
		printf("GUASTO\t%s\t%s\n", etichetta, sbaglio->message);
		fprintf(stderr, "⛔ FAILED: %s\n", sbaglio->message);
		mutter_chiudi(sessione);
		return 2;
	}

	/* The stream is waited for to be really ACTIVE before saying «pronto»:
	 * writing it before would mean switching the scene on on a monitor that does not
	 * exist yet. */
	scadenza = g_get_monotonic_time() + 10 * G_USEC_PER_SEC;
	while (!capture_active(cattura) && g_get_monotonic_time() < scadenza)
		g_usleep(20000);
	if (!capture_active(cattura))
	{
		printf("GUASTO\t%s\tstream never active\n", etichetta);
		fprintf(stderr, "⛔ FAILED (not «zero»): the stream never became active%s%s.\n",
		        capture_fault(cattura) ? " — " : "",
		        capture_fault(cattura) ? capture_fault(cattura) : "");
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}

	/* ⛔ AND NOW — not before — we ask WHAT our screen IS CALLED.
	 *    The virtual monitor appears when the consumer hooks on, `[M]`, and
	 *    this is also the moment the name is needed: the scene opens after,
	 *    and must be sent to THIS screen by name (`CODER.md` §3.9). */
	if (sessione)
	{
		mutter_monitor_cerca(sessione);
		fprintf(stderr, "   our monitor: %s («%s»)\n",
		        mutter_our_monitor(sessione) ? mutter_our_monitor(sessione) : "I DO NOT KNOW",
		        mutter_monitor_prodotto(sessione) ? mutter_monitor_prodotto(sessione) : "—");
	}

	/* --- the «primo» frame: before the scene exists ---------------------- *
	 * ⛔ E9 (`CODER.md` §3.5) for a still image: the start-up sample is not
	 *    a defect — it is the PRODUCT, what whoever connects now sees. The
	 *    defect would be measuring it and writing the number in a column that
	 *    phase 3 will read as steady state.  ⇒ Two frames, two files, and the manifest
	 *    says for each which it was among those arrived. */
	{
		CaptureTake p = cattura_prendi(cattura, 3.0, &primo.fermo, &sbaglio);

		if (p == CATTURA_PRESA_FATTA)
		{
			primo.preso = TRUE;
			primo.danno = damage_name(&primo.fermo);
		}
		else if (p == CATTURA_PRESA_GUASTO)
		{
			printf("GUASTO\t%s\t%s\n", etichetta, sbaglio->message);
			fprintf(stderr, "⛔ FAILED on the «primo»: %s\n", sbaglio->message);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 2;
		}
		else if (p == CATTURA_PRESA_PIXEL_ALTROVE)
		{
			primo.preso = FALSE; /* the pixels live on the card: it is said, not faked */
		}
		g_clear_error(&sbaglio);
	}

	if (!g_file_set_contents(pronto, "pronto\n", -1, &sbaglio))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", pronto, sbaglio->message);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 1;
	}
	fprintf(stderr, "  pronto: the scene can be switched on now\n");

	/* --- wait for the launcher to declare the scene on ------------------- */
	scadenza = g_get_monotonic_time() + (gint64) (attesa_scena * G_USEC_PER_SEC);
	while (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS) && g_get_monotonic_time() < scadenza)
		g_usleep(50000);
	if (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS))
	{
		printf("GUASTO\t%s\tthe scene was never declared on\n", etichetta);
		fprintf(stderr, "⛔ FAILED: after %.1f s nobody declared the scene on.\n",
		        attesa_scena);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}
	cattura_conteggi(cattura, &conto);
	prima_della_scena = conto.arrivati;
	fine = g_get_monotonic_time() + (gint64) (durata * G_USEC_PER_SEC);
	fprintf(stderr, "  scene on: %" G_GUINT64_FORMAT " frames had already arrived\n",
	        prima_della_scena);

	/* --- the «regime» frame ---------------------------------------------- *
	 * `--dopo-scena` is let pass, `--scarta` frames are thrown away (they are
	 * the switching on of the scene, not the steady state), and then **the last one of the
	 * window** is taken: so the damage it carries is the steady-state one. */
	g_usleep((gulong) (dopo_scena * G_USEC_PER_SEC));
	for (i = 0; (guint64) i < scarta && g_get_monotonic_time() < fine; i++)
	{
		CatturaFermo buttato = { 0 };

		if (cattura_prendi(cattura, 0.5, &buttato, &sbaglio) == CATTURA_PRESA_GUASTO)
			break;
		cattura_fermo_libera(&buttato);
		g_clear_error(&sbaglio);
	}
	g_clear_error(&sbaglio);

	while (g_get_monotonic_time() < fine - (gint64) (0.7 * G_USEC_PER_SEC))
		g_usleep(50000);

	{
		CaptureTake p = cattura_prendi(cattura, 1.5, &regime.fermo, &sbaglio);

		if (p == CATTURA_PRESA_FATTA)
		{
			regime.preso = TRUE;
			regime.danno = damage_name(&regime.fermo);
		}
		else if (p == CATTURA_PRESA_GUASTO)
		{
			printf("GUASTO\t%s\t%s\n", etichetta, sbaglio->message);
			fprintf(stderr, "⛔ FAILED on the «regime»: %s\n", sbaglio->message);
			cattura_fermo_libera(&primo.fermo);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 2;
		}
		g_clear_error(&sbaglio);
	}

	/* --- the guards, BEFORE writing any number --------------------------- */
	if (!capture_active(cattura))
	{
		printf("GUASTO\t%s\tstream dropped during the take\n", etichetta);
		fprintf(stderr, "⛔ FAILED (not «zero»): the stream was active and dropped.\n");
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}
	cattura_conteggi(cattura, &conto);
	dopo_la_scena = conto.arrivati - prima_della_scena;

	/*
	 * ⛔ A LIVE SCENE AND ZERO FRAMES IS NOT A ZERO: IT IS A FAULT.
	 *
	 * On 12 Aug 2026 this bench came out GREEN while the defect was alive:
	 * the session already had a monitor, `mpv --fs` went full screen on
	 * THAT one, and our capture received zero.  With a scene declared alive and
	 * moving, zero frames is the proof that we are looking at a screen
	 * different from the one the scene paints on.
	 */
	if (dopo_la_scena < minimo_dopo_scena)
	{
		printf("GUASTO\t%s\tlive scene and %" G_GUINT64_FORMAT " frames after\n", etichetta,
		       dopo_la_scena);
		fprintf(stderr,
		        "⛔ FAILED (not «zero»): the scene was declared alive and there arrived\n"
		        "   %" G_GUINT64_FORMAT " frames after it (minimum required %" G_GUINT64_FORMAT
		        ").\n   Before the scene %" G_GUINT64_FORMAT
		        " had arrived: the stream works.\n"
		        "   ⇒ It is not the still desktop: it is that the scene paints on a DIFFERENT SCREEN\n"
		        "     from the one we are capturing (ours is %s).\n",
		        dopo_la_scena, minimo_dopo_scena, prima_della_scena,
		        sessione && mutter_our_monitor(sessione) ? mutter_our_monitor(sessione)
		                                                    : "unknown");
		cattura_fermo_libera(&primo.fermo);
		cattura_fermo_libera(&regime.fermo);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}

	/* --- the writing ----------------------------------------------------- */
	if (!cattura_consegna(cattura, &consegna))
	{
		printf("GUASTO\t%s\tno format negotiated\n", etichetta);
		fprintf(stderr, "⛔ FAILED: no format was negotiated: there is nothing to "
		                "declare, and I do not write zeros in its place.\n");
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}

	if (conto.arrivati == 0)
	{
		esito = "ZERO FRAMES";
		codice = 3;
	}
	else if (strada == CATTURA_STRADA_SCHEDA)
	{
		esito = "TYPE DECLARED, PIXELS NOT READ (dmabuf)";
		codice = 0;
	}
	else if (!primo.preso && !regime.preso)
	{
		printf("GUASTO\t%s\tframes arrived but none copyable\n", etichetta);
		fprintf(stderr, "⛔ FAILED: %" G_GUINT64_FORMAT " frames arrived and none "
		                "had readable pixels.\n",
		        conto.arrivati);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 2;
	}
	else
	{
		esito = "ONE FRAME";
		codice = 0;
		if (primo.preso &&
		    !g_file_set_contents(first_file, (const char *) primo.fermo.pixel,
		                         (gssize) primo.fermo.byte, &sbaglio))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", first_file, sbaglio->message);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 1;
		}
		if (regime.preso &&
		    !g_file_set_contents(file_regime, (const char *) regime.fermo.pixel,
		                         (gssize) regime.fermo.byte, &sbaglio))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", file_regime, sbaglio->message);
			cattura_ferma(cattura);
			mutter_chiudi(sessione);
			return 1;
		}
	}

	/* --- the manifest ---------------------------------------------------- */
	manifesto = g_string_new("{\n");
	g_string_append_printf(manifesto,
	                       "  \"strumento\": \"02-cattura-prodotto (src/cattura.c + "
	                       "src/mutter.c)\",\n"
	                       "  \"etichetta\": \"%s\",\n"
	                       "  \"quando_utc\": \"%s\",\n"
	                       "  \"nodo_pipewire\": %u,\n"
	                       "  \"esito\": \"%s\",\n"
	                       "  \"uscita\": %d,\n",
	                       etichetta, quando, nodo, esito, codice);
	g_string_append_printf(manifesto,
	                       "  \"chiesto\": {\n"
	                       "    \"larghezza\": %u, \"altezza\": %u, \"fps_massimi\": %u,\n"
	                       "    \"colore\": \"%s\", \"strada\": \"%s\",\n"
	                       "    \"cadenza\": \"0/1 with maxFramerate at %u — «send me a "
	                       "frame when something changes»\"\n"
	                       "  },\n",
	                       larghezza, altezza, fps,
	                       colore == CAPTURE_COLOR_BGRA ? "BGRA"
	                       : colore == CAPTURE_COLOR_10BIT ? "10bit"
	                                                        : "BGRx",
	                       strada == CATTURA_STRADA_SCHEDA ? "dmabuf" : "memoria", fps);
	g_string_append_printf(manifesto,
	                       "  \"negoziato\": {\n"
	                       "    \"noto\": %s,\n"
	                       "    \"larghezza\": %u, \"altezza\": %u,\n"
	                       "    \"colore\": \"%s\",\n"
	                       "    \"modificatore\": \"0x%" G_GINT64_MODIFIER "x\",\n"
	                       "    \"chi_lo_dice\": \"PipeWire, SPA_PARAM_Format in the param_changed "
	                       "callback — it is not the label we gave it\"\n"
	                       "  },\n",
	                       consegna.noto ? "true" : "false", consegna.larghezza, consegna.altezza,
	                       consegna.formato, (guint64) consegna.modificatore);

	g_string_append_printf(
	    manifesto,
	    "  \"consegna_a_F2_3\": {\n"
	    "    \"bit_per_canale\": %d,\n"
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
	    "    \"matrice\": \"%s\",\n"
	    "    \"trasferimento\": \"%s\",\n"
	    "    \"primari\": \"%s\",\n"
	    "    \"chi_lo_dice\": \"spa_video_info_raw.color_range / .color_matrix / "
	    ".transfer_function / .color_primaries, filled by spa_format_video_raw_parse on the "
	    "producer's SPA_PARAM_Format\",\n"
	    "    \"⚠ sulla matrice\": \"at capture the pixels are RGB: no 601/709 matrix "
	    "was applied by us. The matrix is CHOSEN by F2.3 when converting to YCbCr, and "
	    "F2.6 must compare with the same one — a comparison made with the wrong matrix "
	    "measures the matrix\",\n"
	    "    \"range_misurato_dal_prodotto\": \"%s\",\n"
	    "    \"valori_grezzi\": {\"color_range\": %u, \"color_matrix\": %u, "
	    "\"transfer_function\": %u, \"color_primaries\": %u}\n"
	    "  },\n",
	    consegna.bit_per_canale, consegna.formato, capture_source_name(consegna.source_bit),
	    /* ⛔ The stride is read from WHATEVER frame arrived, even from one
	     *    without pixels: on the card road the pixels are not here, but the
	     *    stride is a fact of the chunk, and it is one of the four that are
	     *    declared downstream.  Writing 0 there would be a silence passed off
	     *    as a number. */
	    regime.fermo.stride ? regime.fermo.stride : primo.fermo.stride,
	    regime.fermo.byte ? regime.fermo.byte
	                      : (guint64) (regime.fermo.stride ? regime.fermo.stride
	                                                       : primo.fermo.stride) *
	                            consegna.altezza,
	    capture_range_name(consegna.raw_range), capture_matrix_name(consegna.raw_matrix),
	    capture_transfer_name(consegna.raw_transfer),
	    capture_primaries_name(consegna.raw_primaries),
	    capture_range_measured_name(regime.preso ? regime.fermo.consegna.range_misurato
	                                             : CAPTURE_RANGE_UNMEASURED),
	    consegna.raw_range, consegna.raw_matrix, consegna.raw_transfer,
	    consegna.raw_primaries);

	g_string_append(manifesto, "  \"buffer\": {\n    \"tipi_visti\": [");
	for (i = 0; (guint) i < conto.how_many_types; i++)
		g_string_append_printf(manifesto, "%s\"%s\"", i ? ", " : "",
		                       capture_buffer_name(conto.tipi_visti[i]));
	g_string_append_printf(manifesto,
	                       "],\n"
	                       "    \"chiesto\": \"%s\",\n"
	                       "    \"distinti_riciclati\": %u,\n"
	                       "    \"chi_lo_dice\": \"PipeWire, spa_data.type of plane 0 of every "
	                       "buffer — asked for in TWO places (the modifier in the format and "
	                       "SPA_PARAM_BUFFERS_dataType)\"\n"
	                       "  },\n",
	                       capture_buffer_name(consegna.buffer_chiesto), conto.buffer_distinti);

	g_string_append_printf(manifesto,
	                       "  \"fotogrammi\": {\n"
	                       "    \"minimo_dopo_la_scena_preteso\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"arrivati_in_tutto\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"prima_della_scena\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"dopo_la_scena\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"danno_pieno\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"danno_parziale\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"danno_assente\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"senza_header\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"solo_cursore_scartati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"stride_zero_scartati\": %" G_GUINT64_FORMAT ",\n"
	                       "    \"senza_pixel_scartati\": %" G_GUINT64_FORMAT "\n"
	                       "  },\n",
	                       minimo_dopo_scena, conto.arrivati, prima_della_scena, dopo_la_scena,
	                       conto.danno_pieno, conto.danno_parziale, conto.danno_assente,
	                       conto.without_header, conto.solo_cursore, conto.stride_zero,
	                       conto.without_pixel);

	g_string_append_printf(manifesto,
	                       "  \"schermo\": {\n"
	                       "    \"connettore\": \"%s\",\n"
	                       "    \"prodotto\": \"%s\",\n"
	                       "    \"chi_lo_dice\": \"DisplayConfig.GetCurrentState before and after "
	                       "RecordVirtual, plus the PRODUCT name: two independent roads "
	                       "that must agree, because the two virtual monitors of the server "
	                       "are BOTH 1920×1080@60\"\n"
	                       "  },\n",
	                       sessione && mutter_our_monitor(sessione)
	                           ? mutter_our_monitor(sessione)
	                           : "I DO NOT KNOW",
	                       sessione && mutter_monitor_prodotto(sessione)
	                           ? mutter_monitor_prodotto(sessione)
	                           : "—");

	manifest_entry(manifesto, "primo", &primo, first_file);
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

	if (!g_file_set_contents(file_json, manifesto->str, -1, &sbaglio))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", file_json, sbaglio->message);
		g_string_free(manifesto, TRUE);
		cattura_ferma(cattura);
		mutter_chiudi(sessione);
		return 1;
	}
	g_string_free(manifesto, TRUE);

	printf("PRESA\t%s\t%s\t%s\t%" G_GUINT64_FORMAT "\t%" G_GUINT64_FORMAT "\t%s\n", etichetta,
	       esito, file_json, conto.arrivati, dopo_la_scena,
	       capture_buffer_name(consegna.buffer_dichiarato));
	fprintf(stderr,
	        "  outcome: %s\n"
	        "  arrived %" G_GUINT64_FORMAT " (before the scene %" G_GUINT64_FORMAT ", after %"
	        G_GUINT64_FORMAT ")\n"
	        "  damage: full %" G_GUINT64_FORMAT ", partial %" G_GUINT64_FORMAT ", absent %"
	        G_GUINT64_FORMAT "\n"
	        "  distinct recycled buffers: %u · declared type: %s\n"
	        "  stride READ: %u · bytes: %" G_GUINT64_FORMAT "\n"
	        "  manifest: %s\n",
	        esito, conto.arrivati, prima_della_scena, dopo_la_scena, conto.danno_pieno,
	        conto.danno_parziale, conto.danno_assente, conto.buffer_distinti,
	        capture_buffer_name(consegna.buffer_dichiarato),
	        regime.fermo.stride ? regime.fermo.stride : primo.fermo.stride, regime.fermo.byte,
	        file_json);

	cattura_fermo_libera(&primo.fermo);
	cattura_fermo_libera(&regime.fermo);
	cattura_ferma(cattura);
	mutter_chiudi(sessione);
	return codice;
}
