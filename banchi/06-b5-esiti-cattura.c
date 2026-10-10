/*
 * 06-b5-esiti-cattura.c — ⭐ the THREE proposals of `06-b40`, put to the test
 *                            starting from the hypothesis that they are WRONG.
 *
 *   06-b5-esiti-cattura              runs all cases
 *   06-b5-esiti-cattura <n>          runs only case n
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHERE THIS BENCH COMES FROM
 *
 * `banchi/06-b40-palco-finto.c` exercised `src/cattura.c` with a real PipeWire
 * producer and drew three proposals for the product from it, all `[R]`/`[M]` and
 * none written:
 *
 *   1. `cattura_ridimensiona()` declares SUCCESS on a stream that dies, and
 *      *«`figlio.c` has no way of knowing that the renegotiation KILLED the
 *      capture: today it only finds out from the timeout of `cattura_prendi`»*;
 *   2. `misura_divergente` is **written and never read** ⇒ an accessor is needed;
 *   3. the *«granted different from requested»* branch **cannot be reached from
 *      outside** except with a race, *«and a bench cannot program a race»*.
 *
 * ⭐ The brief of this bench is the opposite of that of `06-b40`: **look for the
 *    proof that the three claims are false.**  Every case is written to
 *    DISPROVE, not to confirm — and the expected result is declared before the run.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT THIS BENCH DOES **NOT** TEST
 *
 *   · **it does not test Mutter**: the stage here is a `pw_stream` of this file, and
 *     I choose its limits.  On Mutter `[M]` (§5.0-sexies) 30 requests out of
 *     30 were granted exactly from 1x1 to 7680x4320, and `rcp_misura_ammessa()`
 *     cuts at 7680x4320: ⇒ the scene «the stage cannot hold the size» on the real
 *     product is `[?]`, not `[M]`.  Here what is measured is the BEHAVIOUR OF `cattura.c`
 *     when that scene happens, not how often it happens;
 *   · **it does not test the pixels**: the fake stage queues no buffer, so
 *     `cattura_prendi()` on a HEALTHY stream answers ZERO.  ⭐ And that is exactly the
 *     positive control case 3 needs: «zero» and «fault» must remain
 *     two different answers (`CODER.md` §3.10);
 *   · **it does not test `figlio.c`**: the timings of the child's loop are quoted
 *     (`MOVIMENTO_ATTESA_S 0.008`), not executed.
 */
#include "../src/cattura.h"
#include "../src/registro.h"

#include <pipewire/pipewire.h>
#include <spa/param/video/format-utils.h>
#include <spa/pod/builder.h>
#include <spa/utils/result.h>

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* ------------------------------------------------------------------ *
 *  ⛔ THE LOG IS CAPTURED — and here it is the MEASUREMENT, not a side dish.
 *
 *  `src/registro.c` writes to `stderr` and has no listening hook:
 *  ⇒ `stderr` is redirected to a temporary file and read back.  ⚠ The technique
 *  is that of `06-b40`, including the trap already paid for: **the file is not
 *  truncated, the point is marked** (an `ftruncate` does not move the write offset,
 *  and a hole of NULs is left in front, on which `strstr` stops ⇒ every `dice()`
 *  would answer «no», that is green on every case that requires an absence).
 * ------------------------------------------------------------------ */
#define REG_CAP 262144
static char registro_visto[REG_CAP];
static FILE *dirottato;
static bool parlantina;

static void registro_dirotta(void)
{
	dirottato = tmpfile();
	if (!dirottato) {
		printf("  ⛔ the temporary file for the log cannot be opened\n");
		exit(2);
	}
	if (dup2(fileno(dirottato), STDERR_FILENO) < 0) {
		printf("  ⛔ stderr cannot be redirected\n");
		exit(2);
	}
	setvbuf(stderr, NULL, _IONBF, 0);
}

static off_t segno;

static void registro_azzera(void)
{
	fflush(stderr);
	segno = lseek(fileno(dirottato), 0, SEEK_CUR);
	if (segno < 0)
		segno = 0;
	registro_visto[0] = 0;
}

static void registro_rileggi(void)
{
	ssize_t n;
	fflush(stderr);
	n = pread(fileno(dirottato), registro_visto, REG_CAP - 1, segno);
	registro_visto[n > 0 ? n : 0] = 0;
	if (parlantina && n > 0)
		printf("      | %s\n", registro_visto);
}

static bool dice(const char *pezzo)
{
	return strstr(registro_visto, pezzo) != NULL;
}

/* ------------------------------------------------------------------ *
 *  ⭐ THE FAKE STAGE — a PipeWire producer, with limits I choose
 *
 *  ⚠ It is the one from `06-b40`, with **one thing more** that case 5 needs: the
 *    stage can REDO its own offer on the fly (`palco_ripropone`), which is the
 *    only way to ask «can a producer IMPOSE its size on a
 *    consumer that offers a fixed one?».
 * ------------------------------------------------------------------ */
typedef struct {
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;
	uint32_t nodo;
	uint32_t min_l, min_a, max_l, max_a;   /* ⛔ the limits of the fake stage */
	bool fissa;                            /* the offer is a FIXED rectangle */
	uint32_t negoziata_l, negoziata_a;
	int quante_negoziazioni;
} Palco;

static void palco_parametro(void *dati, uint32_t id, const struct spa_pod *param)
{
	Palco *p = dati;
	struct spa_video_info_raw info;

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_video_raw_parse(param, &info) < 0)
		return;
	p->negoziata_l = info.size.width;
	p->negoziata_a = info.size.height;
	p->quante_negoziazioni++;
	printf("      [stage] negotiated format: %ux%u  (negotiation no.%d)\n",
	       info.size.width, info.size.height, p->quante_negoziazioni);
}

static const struct pw_stream_events palco_eventi = {
	PW_VERSION_STREAM_EVENTS,
	.param_changed = palco_parametro,
};

/* ⛔ The frame rate is a RANGE starting from zero, not a fixed 30/1: `cattura.c`
 *    offers `framerate` as a fixed fraction 0/1 — «the producer dictates the
 *    frame rate» — and a stage offering a fixed 30/1 would give an EMPTY
 *    intersection.  ⚠ A defect of the STAGE, already paid for by `06-b40` on 21 August 2026. */
static const struct spa_pod *palco_proposta(struct spa_pod_builder *b, Palco *p)
{
	struct spa_rectangle mis  = SPA_RECTANGLE(p->min_l, p->min_a);
	struct spa_rectangle mini = SPA_RECTANGLE(p->min_l, p->min_a);
	struct spa_rectangle maxi = SPA_RECTANGLE(p->max_l, p->max_a);
	struct spa_fraction cad   = SPA_FRACTION(0, 1);
	struct spa_fraction cmin  = SPA_FRACTION(0, 1);
	struct spa_fraction cmax  = SPA_FRACTION(120, 1);

	if (p->fissa)
		return spa_pod_builder_add_object(
		    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
		    SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
		    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
		    SPA_FORMAT_VIDEO_format, SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx),
		    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&mis),
		    SPA_FORMAT_VIDEO_framerate,
		    SPA_POD_CHOICE_RANGE_Fraction(&cad, &cmin, &cmax),
		    SPA_FORMAT_VIDEO_maxFramerate,
		    SPA_POD_CHOICE_RANGE_Fraction(&cmax, &cmin, &cmax));

	return spa_pod_builder_add_object(
	    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
	    SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
	    SPA_FORMAT_VIDEO_format, SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx),
	    SPA_FORMAT_VIDEO_size, SPA_POD_CHOICE_RANGE_Rectangle(&mis, &mini, &maxi),
	    SPA_FORMAT_VIDEO_framerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&cad, &cmin, &cmax),
	    SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&cmax, &cmin, &cmax));
}

static Palco *palco_apri(uint32_t min_l, uint32_t min_a,
                         uint32_t max_l, uint32_t max_a)
{
	Palco *p = calloc(1, sizeof *p);
	uint8_t spazio[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *par[1];

	p->min_l = min_l; p->min_a = min_a;
	p->max_l = max_l; p->max_a = max_a;

	p->ciclo = pw_thread_loop_new("palco-finto-b5", NULL);
	if (!p->ciclo)
		goto guasto;
	p->contesto = pw_context_new(pw_thread_loop_get_loop(p->ciclo), NULL, 0);
	if (!p->contesto)
		goto guasto;
	pw_thread_loop_lock(p->ciclo);
	if (pw_thread_loop_start(p->ciclo) < 0) {
		pw_thread_loop_unlock(p->ciclo);
		goto guasto;
	}
	p->nucleo = pw_context_connect(p->contesto, NULL, 0);
	if (!p->nucleo) {
		pw_thread_loop_unlock(p->ciclo);
		goto guasto;
	}
	p->flusso = pw_stream_new(p->nucleo, "palco-finto-b5",
	                          pw_properties_new(PW_KEY_MEDIA_TYPE, "Video",
	                                            PW_KEY_MEDIA_CATEGORY, "Playback",
	                                            PW_KEY_MEDIA_ROLE, "Screen",
	                                            PW_KEY_MEDIA_CLASS, "Video/Source",
	                                            PW_KEY_NODE_NAME, "remotix-palco-b5",
	                                            NULL));
	if (!p->flusso) {
		pw_thread_loop_unlock(p->ciclo);
		goto guasto;
	}
	pw_stream_add_listener(p->flusso, &p->gancio, &palco_eventi, p);
	par[0] = palco_proposta(&b, p);
	if (pw_stream_connect(p->flusso, PW_DIRECTION_OUTPUT, PW_ID_ANY,
	                      PW_STREAM_FLAG_MAP_BUFFERS, par, 1) < 0) {
		pw_thread_loop_unlock(p->ciclo);
		goto guasto;
	}
	pw_thread_loop_unlock(p->ciclo);

	/* ⛔ The node identifier is WAITED for: before registration on the
	 *    server it is `SPA_ID_INVALID`, and attaching to it would mean attaching
	 *    to nothing — with the symptom «capture does not start» and no error. */
	for (int i = 0; i < 200; i++) {
		p->nodo = pw_stream_get_node_id(p->flusso);
		if (p->nodo != SPA_ID_INVALID && p->nodo != 0)
			break;
		usleep(25000);
	}
	if (p->nodo == SPA_ID_INVALID || p->nodo == 0)
		goto guasto;
	printf("      [stage] node %u, holds from %ux%u to %ux%u\n",
	       p->nodo, min_l, min_a, max_l, max_a);
	return p;

guasto:
	printf("      [stage] ⛔ does not open\n");
	return NULL;
}

/* ⭐ THE STAGE REDOES ITS OFFER ON THE FLY — it is the lever of case 5.
 *
 * ⛔ If `fissa`, the stage demands EXACTLY `l x a`: it is the producer that
 *    tries to impose its own size on a consumer that offers a fixed and
 *    different one.  If not `fissa`, it is a new range. */
static int palco_ripropone(Palco *p, uint32_t min_l, uint32_t min_a,
                           uint32_t max_l, uint32_t max_a, bool fissa)
{
	uint8_t spazio[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *par[1];
	int esito;

	p->min_l = min_l; p->min_a = min_a;
	p->max_l = max_l; p->max_a = max_a;
	p->fissa = fissa;

	pw_thread_loop_lock(p->ciclo);
	par[0] = palco_proposta(&b, p);
	esito = pw_stream_update_params(p->flusso, par, 1);
	pw_thread_loop_unlock(p->ciclo);
	printf("      [stage] re-offers %s %ux%u..%ux%u → %d\n",
	       fissa ? "FIXED" : "range", min_l, min_a, max_l, max_a, esito);
	return esito;
}

static void palco_chiudi(Palco *p)
{
	if (!p)
		return;
	if (p->ciclo)
		pw_thread_loop_stop(p->ciclo);
	if (p->flusso)
		pw_stream_destroy(p->flusso);
	if (p->nucleo)
		pw_core_disconnect(p->nucleo);
	if (p->contesto)
		pw_context_destroy(p->contesto);
	if (p->ciclo)
		pw_thread_loop_destroy(p->ciclo);
	free(p);
}

/* ------------------------------------------------------------------ *
 *  The outcomes
 * ------------------------------------------------------------------ */
static int passati, falliti;

static void esito(const char *nome, bool bene, const char *atteso, const char *visto)
{
	if (bene) {
		printf("  \033[1;32mOK\033[0m  %s\n        %s\n", nome, visto);
		passati++;
	} else {
		printf("  \033[1;31mNO\033[0m  %s\n        expected: %s\n        seen:     %s\n",
		       nome, atteso, visto);
		falliti++;
	}
}

static void aspetta(double secondi)
{
	usleep((useconds_t)(secondi * 1000000.0));
}

static double ora_ms(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return t.tv_sec * 1000.0 + t.tv_nsec / 1000000.0;
}

/* =====================================================================
 *  1 — ⭐ THE POSITIVE CONTROL OF THE INSTRUMENT, and it goes first.
 *
 *  ⛔ Case 3 requires `cattura_prendi()` to answer **FAULT** on a
 *     dead stream.  A `cattura_prendi()` that answered FAULT **always** would
 *     make it green by construction.  ⇒ Here the stream is HEALTHY and no
 *     frame arrives (the fake stage queues no buffer): the right answer
 *     is **ZERO**, not FAULT (`CODER.md` §3.10 — «a denied reading is not a
 *     reading that says zero»).
 *
 *  ⚠ And the same case certifies `dice()`: the log MUST contain the line
 *    «capture started on node», which is certainly there.  If it did not find it,
 *    every other case that requires an absence would be green through a defect of the
 *    instrument.
 * ===================================================================== */
static void caso1(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	CatturaFermo fo;
	CatturaPresa presa;
	uint32_t nl = 0, na = 0;
	bool bene, strumento;
	char visto[600];

	registro_azzera();
	p = palco_apri(320, 240, 4096, 4096);
	if (!p) {
		esito("1 positive control: healthy stream ⇒ ZERO, and the instrument sees", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("1 positive control: healthy stream ⇒ ZERO, and the instrument sees", false,
		      "the capture attaches to the fake stage's node",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia said no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_rileggi();
	strumento = dice("capture started on node");
	cattura_misura_negoziata(c, &nl, &na);
	presa = cattura_prendi(c, 0.008, &fo, &sbaglio);
	cattura_fermo_libera(&fo);

	bene = strumento && nl == 1920 && na == 1080 && presa == CATTURA_PRESA_ZERO
	    && !dice("DIVERGENT SIZE");
	snprintf(visto, sizeof visto,
	         "the instrument %s the start line; negotiated %ux%u; cattura_prendi → "
	         "%s (%s); DIVERGENT SIZE line: %s",
	         strumento ? "SEES" : "⛔ does NOT see", nl, na,
	         presa == CATTURA_PRESA_ZERO ? "ZERO" :
	         presa == CATTURA_PRESA_FATTA ? "DONE" : "⛔ FAULT",
	         sbaglio ? sbaglio->message : "no error",
	         dice("DIVERGENT SIZE") ? "⛔ NAMES IT" : "absent");
	g_clear_error(&sbaglio);
	esito("1 positive control: healthy stream ⇒ ZERO, and the instrument sees", bene,
	      "start line SEEN · negotiated 1920x1080 · cattura_prendi = ZERO (NOT "
	      "fault) · no DIVERGENT SIZE", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  2 — ⛔ PROPOSAL 1 PUT TO THE TEST: *«`figlio.c` has no way of knowing
 *      that the renegotiation KILLED the capture: today it only finds out from the
 *      TIMEOUT of `cattura_prendi`»*.
 *
 *  ⭐ The hypothesis to DISPROVE is that one: that the route is not there, and that when
 *     it is there it costs a timeout.  ⇒ It is timed.
 *
 *  THE SCENE: stage up to 1920x1080; 2560x1440 is requested; then
 *  `cattura_prendi()` is called with **the same wait as the child's loop**
 *  (`MOVIMENTO_ATTESA_S 0.008`, `figlio.c:3136`), in a loop, timing it.
 *
 *  EXPECTED, declared before the run — and it is the expected result of the PROPOSAL, that is
 *  the one to be disproved: `cattura_prendi()` must either not notice, or
 *  notice by spending the whole wait (>= 8 ms per round).
 * ===================================================================== */
static void caso2(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	CatturaFermo fo;
	CatturaRitela r;
	double t0, t_guasto = -1.0;
	int giri = 0, giri_zero = 0;
	char messaggio[300] = "";
	bool nomina_lo_stato, bene;
	char visto[900];

	registro_azzera();
	p = palco_apri(320, 240, 1920, 1080);
	if (!p) {
		esito("2 the dead stream is KNOWN, and what knowing it costs", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("2 the dead stream is KNOWN, and what knowing it costs", false,
		      "the capture attaches to the fake stage's node",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia said no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_azzera();

	r = cattura_ridimensiona(c, 2560, 1440);
	t0 = ora_ms();

	/* ⛔ The child's loop, reproduced: `cattura_prendi(MOVIMENTO_ATTESA_S)`
	 *    until it says something other than ZERO.  ⚠ The ceiling is 2 seconds:
	 *    beyond it, the proposal is right and this case is red. */
	while (ora_ms() - t0 < 2000.0) {
		CatturaPresa presa = cattura_prendi(c, 0.008, &fo, &sbaglio);
		giri++;
		if (presa == CATTURA_PRESA_ZERO) {
			giri_zero++;
			g_clear_error(&sbaglio);
			cattura_fermo_libera(&fo);
			continue;
		}
		if (presa == CATTURA_PRESA_GUASTO) {
			t_guasto = ora_ms() - t0;
			snprintf(messaggio, sizeof messaggio, "%s",
			         sbaglio ? sbaglio->message : "no detail");
			g_clear_error(&sbaglio);
			cattura_fermo_libera(&fo);
			break;
		}
		cattura_fermo_libera(&fo);
		g_clear_error(&sbaglio);
	}
	registro_rileggi();

	/* ⛔ «It says so» is not enough: it must ALSO say WHY.  A FAULT without the state
	 *    and without the producer's fault would leave the caller to deduce. */
	nomina_lo_stato = strstr(messaggio, "error") != NULL;

	bene = r == CATTURA_RITELA_CHIESTA && t_guasto >= 0.0 && t_guasto < 100.0
	    && nomina_lo_stato;
	snprintf(visto, sizeof visto,
	         "resize → %d (0 = «requested»); then %d rounds of 8 ms (%d ZERO) and "
	         "the FAULT arrives at %.1f ms; the message %s the state: «%s»",
	         (int)r, giri, giri_zero, t_guasto,
	         nomina_lo_stato ? "NAMES" : "⛔ does NOT name", messaggio);
	esito("2 the dead stream is KNOWN, and what knowing it costs", bene,
	      "⇒ to DISPROVE proposal 1: FAULT within 100 ms (not a timeout) and "
	      "a message that names the state «error»", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  3 — ⛔⛔ THE REAL DEFECT BEHIND PROPOSAL 1, and it is not in
 *      `cattura.c`: **the remount at the size that has just killed the stage**.
 *
 *  `figlio.c:6299` remounts with `prendi_il_palco(tela_voluta_l, tela_voluta_a, …)`
 *  — that is with **the size the client wants**, which is exactly the one that
 *  killed the stream.  And `figlio.c:6385` chooses the SHORT wait when
 *  `codec_chiesto && tela_voluta_l`, that is precisely when someone is watching.
 *
 *  ⇒ The question that decides whether it is a loop or a noose: **does a new
 *    `cattura_avvia()` at the same size, on the same stage, produce a LIVE stage?**
 *
 *  ⛔⛔ AND THE QUESTION COMES IN TWO STEPS, because the first draft of this case
 *      looked only at the return value and would have been **green the wrong way round**:
 *      `[M]` `cattura_avvia()` at 2560x1440 on a stage that reaches 1920x1080
 *      **SUCCEEDS 3 times out of 3** — a good pointer comes back.  ⇒ Looking at the
 *      return means concluding «it is not a noose» when it is: the
 *      negotiation is not yet over when the stream is already `paused`.
 *      ⇒ The stage is looked at **shortly after**, with the same `cattura_prendi()` as the
 *      child's loop.
 *
 *  EXPECTED, declared before the run: if every remount dies at once,
 *  `figlio.c:6299` retries the same size forever and does not get out by itself.
 * ===================================================================== */
static void caso3(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	CatturaFermo fo;
	int tentativi = 3, montati = 0, vivi = 0;
	char primo[300] = "";
	bool bene;
	char visto[800];

	registro_azzera();
	p = palco_apri(320, 240, 1920, 1080);
	if (!p) {
		esito("3 the remount at the size that killed the stage", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	for (int i = 0; i < tentativi; i++) {
		CatturaPresa presa;

		c = cattura_avvia(p->nodo, 2560, 1440, 30, CATTURA_STRADA_MEMORIA,
		                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
		if (!c) {
			if (!primo[0])
				snprintf(primo, sizeof primo, "cattura_avvia: %s",
				         sbaglio ? sbaglio->message : "no detail");
			g_clear_error(&sbaglio);
			continue;
		}
		montati++;
		g_clear_error(&sbaglio);
		/* ⛔ 300 ms: the death measured by case 2 arrives within 10 ms, and this is
		 *    thirty times that — it is not a wait tuned to the result. */
		aspetta(0.3);
		presa = cattura_prendi(c, 0.008, &fo, &sbaglio);
		cattura_fermo_libera(&fo);
		if (presa != CATTURA_PRESA_GUASTO)
			vivi++;
		else if (!primo[0])
			snprintf(primo, sizeof primo, "%s",
			         sbaglio ? sbaglio->message : "no detail");
		g_clear_error(&sbaglio);
		cattura_ferma(c);
	}
	registro_rileggi();

	bene = vivi == 0;
	snprintf(visto, sizeof visto,
	         "%d `cattura_avvia()` out of %d RETURNED a stage at 2560x1440 "
	         "(a size the stage cannot hold), but only %d were still ALIVE 300 "
	         "ms later: %s.  The refusal: «%s»",
	         montati, tentativi, vivi,
	         vivi == 0 ? "⛔ none ⇒ `figlio.c:6299` would retry the same "
	                     "size forever, with the SHORT wait of `:6385`"
	                   : "⭐ some hold ⇒ it is not a noose",
	         primo);
	esito("3 the remount at the size that killed the stage", bene,
	      "0 live stages out of 3 (⇒ the loop of `figlio.c:6299` does not get out by itself), "
	      "and `cattura_avvia()` that SUCCEEDS all the same", visto);
	palco_chiudi(p);
}

/* =====================================================================
 *  4 — ⭐⭐ PROPOSAL 3 PUT TO THE TEST: *«only a RACE is left, and a bench
 *      cannot program a race»*.
 *
 *  ⛔ The hypothesis to disprove.  The scene is not a laboratory race: it is
 *     **two chained `ADATTA_TELA`**, that is the user DRAGGING the edge
 *     of the window — the same scene that `DECISIONI.md` §5.0-sexies names
 *     («among which two chained `ADATTA_TELA`»).
 *
 *  THE MECHANICS, and that is why it is programmable rather than random:
 *    · `cattura_ridimensiona(A)` writes `chiesta_* = A` **on the caller's
 *      thread** and then renegotiates; the answer (`su_parametri`) arrives **later**,
 *      on the PipeWire thread;
 *    · `cattura_ridimensiona(B)` right after, without waiting, rewrites
 *      `chiesta_* = B`;
 *    · if the `Format` of A arrives when `chiesta_*` is already B ⇒ granted A,
 *      requested B ⇒ ⛔ **DIVERGENT SIZE**.
 *
 *  ⚠ The stage holds both sizes: there is no refusal in between, the
 *    scene is completely HEALTHY.
 *
 *  EXPECTED, declared before the run: if the line appears, proposal 3 is
 *  DISPROVED and the branch must be tested, not declared dead.  ⚠ If it does not appear, the
 *  chain is repeated several times before concluding: a race that does not fire at the
 *  first shot is not a race that does not exist.
 * ===================================================================== */
static void caso4(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	uint32_t cl = 0, ca = 0, nl = 0, na = 0;
	int catene = 160, scattata = -1;
	char riga[300] = "";
	bool bene;
	char visto[700];

	registro_azzera();
	p = palco_apri(320, 240, 4096, 4096);
	if (!p) {
		esito("4 two chained resizes ⇒ DIVERGENT SIZE?", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("4 two chained resizes ⇒ DIVERGENT SIZE?", false,
		      "the capture attaches to the fake stage's node",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia said no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_azzera();

	/* ⛔⛔ THE DELAY BETWEEN THE TWO CALLS IS SWEPT, and it is not a detail:
	 *     with the two calls BACK TO BACK (delay 0) the line appears `[M]` **2
	 *     times out of 10 rounds of 40 chains** — that is, it is a real race, and a bench
	 *     that stopped there would be green or red at random.
	 *
	 * ⭐ The window has a physical width: it is the time the `Format` of A
	 *    takes to come back from the server.  If the second call arrives BEFORE
	 *    A leaves, the server answers only once (with B) and there is nothing to
	 *    diverge; if it arrives AFTER A has been delivered, `chiesta_*` was
	 *    still A and neither.  ⇒ The delay that falls in between is searched for.
	 *
	 * ⚠ And it is swept instead of guessed: a delay chosen by hand would be a
	 *   number tuned to the machine of whoever wrote it. */
	{
		static const int ritardi_us[] = {0, 50, 100, 200, 400, 800, 1600, 3200};
		const int quanti_r = (int)(sizeof ritardi_us / sizeof ritardi_us[0]);
		const int per_ritardo = catene / quanti_r;

		/* ⛔ AND IT DOES NOT STOP AT THE FIRST HIT: EVERYTHING is swept.  Stopping
		 *    would give «fired» and no profile, that is the number that is needed —
		 *    which delay makes it fire — would remain unknown. */
		for (int r = 0; r < quanti_r; r++) {
			int colpi = 0;
			for (int k = 0; k < per_ritardo; k++) {
				int i = r * per_ritardo + k;
				uint32_t a_l = 1200 + (uint32_t)(i % 7) * 2u;
				uint32_t a_a =  800 + (uint32_t)(i % 5) * 2u;
				uint32_t b_l = 1600 + (uint32_t)(i % 3) * 2u;
				uint32_t b_a = 1000 + (uint32_t)(i % 11) * 2u;

				/* ⛔ The log is reset AT EVERY CHAIN, or from the first hit
				 *    on `dice()` would answer «yes» forever and every later
				 *    delay would come out as a hit. */
				registro_azzera();
				cattura_ridimensiona(c, a_l, a_a);
				if (ritardi_us[r])
					usleep((useconds_t)ritardi_us[r]);
				cattura_ridimensiona(c, b_l, b_a);
				aspetta(0.03);
				registro_rileggi();
				if (dice("DIVERGENT SIZE")) {
					colpi++;
					if (scattata < 0) {
						const char *q = strstr(registro_visto,
						                       "DIVERGENT SIZE");
						/* ⛔ Cut at the first full stop: the rest of the
						 *    line is the explanation, and here the
						 *    NUMBERS are what matters. */
						const char *fine = strstr(q, ".  ");
						scattata = ritardi_us[r];
						snprintf(riga, sizeof riga, "%.*s",
						         (int)(fine ? (size_t)(fine - q)
						                    : strlen(q)), q);
						printf("      [chain] requested A=%ux%u then B=%ux%u "
						       "⇒ «%s»\n", a_l, a_a, b_l, b_a, riga);
					}
				}
			}
			printf("      [chain] delay %5d us: %d hits out of %d\n",
			       ritardi_us[r], colpi, per_ritardo);
		}
	}

	cattura_misura_chiesta(c, &cl, &ca);
	cattura_misura_negoziata(c, &nl, &na);

	/* ⛔ This case is GREEN when the line APPEARS: it is a bench written to
	 *    disprove, and its green is the disproof. */
	bene = scattata >= 0;
	snprintf(visto, sizeof visto,
	         "over %d chains of two resizes (8 delays swept) the "
	         "DIVERGENT SIZE line %s%d; final requested %ux%u, negotiated %ux%u",
	         catene,
	         scattata >= 0 ? "⭐ APPEARED ⇒ proposal 3 is DISPROVED, the branch "
	                         "is reachable from outside — first hit with the delay "
	                         "in us "
	                       : "⛔ does NOT appear ⇒ proposal 3 HOLDS; chains spent: ",
	         scattata >= 0 ? scattata : catene,
	         cl, ca, nl, na);
	esito("4 two chained resizes ⇒ DIVERGENT SIZE?", bene,
	      "the line APPEARS (⇒ proposal 3 disproved)", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  5 — ⭐ THE OTHER ROUTE TO DISPROVE PROPOSAL 3: **the producer tries to
 *      IMPOSE its size**.
 *
 *  `cattura.c:~1069` offers the size as `SPA_POD_Rectangle`, that is FIXED.
 *  The argument of proposal 3 is structural: the intersection of a fixed
 *  rectangle with anything is either that rectangle or the empty set.  ⇒ It is put
 *  to the test by asking the stage to **redo its own offer** with a
 *  DIFFERENT fixed rectangle, with the stream live.
 *
 *  EXPECTED, declared before the run: either the consumer receives a `Format` at the
 *  PRODUCER's size (⇒ divergence, proposal 3 disproved by this route),
 *  or the negotiation fails and the stream dies (⇒ the structural argument holds).
 *
 *  ⛔ MEASURED, 22 August 2026, PipeWire 1.4.2: **the stream dies**
 *     (`paused → error — no more input formats`), no new `Format`, no
 *     divergence.  ⇒ By THIS route proposal 3 holds, and the disproof is
 *     all case 4's — which goes through another door: not «the producer imposes
 *     another size», but «`chiesta_*` has already changed when the answer
 *     arrives».  ⚠ The green of this case is therefore the death of the stream: it is the
 *     control that keeps case 4 honest, because it shows that the divergence
 *     of case 4 **cannot** come from the producer.
 * ===================================================================== */
static void caso5(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	uint32_t nl = 0, na = 0, cl = 0, ca = 0;
	bool divergente, in_errore, bene;
	char visto[800];

	registro_azzera();
	p = palco_apri(320, 240, 4096, 4096);
	if (!p) {
		esito("5 the producer tries to IMPOSE its size", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("5 the producer tries to IMPOSE its size", false,
		      "the capture attaches to the fake stage's node",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia said no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_azzera();

	/* ⛔ The stage demands a FIXED 1600x900, while the consumer has 1920x1080. */
	palco_ripropone(p, 1600, 900, 1600, 900, true);
	aspetta(1.0);
	registro_rileggi();

	cattura_misura_chiesta(c, &cl, &ca);
	cattura_misura_negoziata(c, &nl, &na);
	divergente = dice("DIVERGENT SIZE");
	in_errore = dice("→ error");

	/* ⛔ Green = the producer did NOT manage it.  ⚠ If one day the divergence
	 *    appeared from here, this case turns red — and that is what is wanted:
	 *    it would mean that the fixed rectangle is no longer a guarantee, and that
	 *    case 4 has a second source to tell apart. */
	bene = !divergente && in_errore && nl == 1920 && na == 1080;
	snprintf(visto, sizeof visto,
	         "the stage demanded a fixed 1600x900; requested %ux%u, negotiated %ux%u; "
	         "stream %s; DIVERGENT SIZE: %s",
	         cl, ca, nl, na, in_errore ? "in ERROR" : "⛔ alive",
	         divergente ? "⛔ APPEARED ⇒ the producer IMPOSES, and case 4 has a "
	                      "second source"
	                    : "absent ⇒ the FIXED rectangle holds: either that value, or "
	                      "the empty set");
	esito("5 the producer tries to IMPOSE its size", bene,
	      "still negotiated 1920x1080 · stream in error · NO divergence "
	      "(⇒ the producer cannot impose)", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  6 — ⛔ PROPOSAL 2 PUT TO THE TEST: is an accessor for the divergence needed?
 *
 *  The argument of the proposal: `misura_divergente` is written and never read, and
 *  `cattura.h` does not expose it ⇒ no caller can know it.
 *
 *  ⭐ The hypothesis to disprove: that the caller CANNOT know it.  `cattura.h`
 *     already exposes **two** accessors — `cattura_misura_chiesta()` and
 *     `cattura_misura_negoziata()` — and the divergence is their inequality.
 *     ⇒ It is checked that the two are enough to reconstruct it, including the case in which the
 *     format is not yet known (where the third field would lie: it is `FALSE`
 *     because there is nothing to compare yet, not because everything is
 *     fine — `CODER.md` §3.10).
 * ===================================================================== */
static void caso6(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	uint32_t cl = 0, ca = 0, nl = 0, na = 0;
	gboolean noto_prima, noto_dopo;
	/* ⛔ The BEFORE numbers are kept in their own variables: the first draft of
	 *    this case reprinted them as `0` written by hand in the `printf`, that is
	 *    the bench STATED a number it had not read — the author's defect,
	 *    found by rereading the output. */
	uint32_t cl0 = 0, ca0 = 0, nl0 = 0, na0 = 0;
	bool bene;
	char visto[800];

	registro_azzera();
	p = palco_apri(320, 240, 1920, 1080);
	if (!p) {
		esito("6 the two accessors are enough to reconstruct the divergence", false,
		      "the fake stage opens", "⛔ the fake stage did NOT open");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("6 the two accessors are enough to reconstruct the divergence", false,
		      "the capture attaches to the fake stage's node",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia said no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	cattura_misura_chiesta(c, &cl0, &ca0);
	noto_prima = cattura_misura_negoziata(c, &nl0, &na0);

	/* ⛔ The request the stage cannot hold: from here on «requested» and
	 *    «negotiated» diverge, and the two PUBLIC accessors say so. */
	cattura_ridimensiona(c, 2560, 1440);
	aspetta(0.5);
	cattura_misura_chiesta(c, &cl, &ca);
	noto_dopo = cattura_misura_negoziata(c, &nl, &na);

	bene = noto_prima && cl0 == 1920 && ca0 == 1080 && nl0 == 1920 && na0 == 1080
	    && noto_dopo && cl == 2560 && ca == 1440 && nl == 1920 && na == 1080;
	snprintf(visto, sizeof visto,
	         "before: requested %ux%u, negotiated %s%ux%u.  After the request the "
	         "stage cannot hold: requested %ux%u, negotiated %s%ux%u ⇒ the divergence "
	         "%s from the two public accessors, and without the private field",
	         cl0, ca0, noto_prima ? "" : "⛔ UNKNOWN ", nl0, na0,
	         cl, ca, noto_dopo ? "" : "⛔ UNKNOWN ", nl, na,
	         (cl != nl || ca != na) ? "CAN BE READ" : "⛔ cannot be read");
	esito("6 the two accessors are enough to reconstruct the divergence", bene,
	      "requested 2560x1440 · negotiated 1920x1080, both readable from "
	      "`cattura.h` without a third accessor", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

int main(int argc, char **argv)
{
	int solo = argc > 1 ? atoi(argv[1]) : 0;
	void (*casi[])(void) = {caso1, caso2, caso3, caso4, caso5, caso6};
	const int quanti = (int)(sizeof casi / sizeof casi[0]);

	parlantina = getenv("PARLANTINA") != NULL;
	pw_init(&argc, &argv);
	/* ⛔ The LOG's verbosity is ALWAYS switched on: «stream state: paused
	 *    → error» is `registro_dettaglio()` (`cattura.c:318`) and with verbosity
	 *    off it is not written at all — the cases that REQUIRE that line
	 *    would be red for a reason unrelated to what they measure. */
	registro_parlantina(true);
	registro_dirotta();

	printf("\n== 06-b5: the three proposals of 06-b40, put to the test to DISPROVE them ==\n\n");
	for (int i = 0; i < quanti; i++) {
		if (solo && solo != i + 1)
			continue;
		casi[i]();
	}
	printf("\n  passed %d, failed %d\n\n", passati, falliti);
	return falliti ? 1 : 0;
}
