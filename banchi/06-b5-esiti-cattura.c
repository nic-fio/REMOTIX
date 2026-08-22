/*
 * 06-b5-esiti-cattura.c — ⭐ le TRE proposte di `06-b40`, messe alla prova
 *                            partendo dall'ipotesi che siano SBAGLIATE.
 *
 *   06-b5-esiti-cattura              gira tutti i casi
 *   06-b5-esiti-cattura <n>          gira solo il caso n
 *
 * ---------------------------------------------------------------------------
 * ⛔ DA DOVE VIENE QUESTO BANCO
 *
 * `banchi/06-b40-palco-finto.c` ha esercitato `src/cattura.c` con un produttore
 * PipeWire vero e ne ha tratto tre proposte al prodotto, tutte `[R]`/`[M]` e
 * nessuna scritta:
 *
 *   1. `cattura_ridimensiona()` dichiara SUCCESSO su un flusso che muore, e
 *      *«`figlio.c` non ha modo di sapere che la rinegoziazione ha UCCISO la
 *      cattura: oggi lo scopre solo dal timeout di `cattura_prendi`»*;
 *   2. `misura_divergente` e' **scritta e mai letta** ⇒ serve un accessore;
 *   3. il ramo *«concesso diverso da chiesto»* **non si raggiunge dall'esterno**
 *      se non con una corsa, *«e una corsa un banco non la programma»*.
 *
 * ⭐ Il mandato di questo banco e' l'opposto di quello di `06-b40`: **cercare la
 *    prova che le tre affermazioni siano false.**  Ogni caso e' scritto per
 *    SMENTIRE, non per confermare — e l'atteso e' dichiarato prima del giro.
 *
 * ---------------------------------------------------------------------------
 * ⛔ QUEL CHE QUESTO BANCO **NON** PROVA
 *
 *   · **non prova Mutter**: il palco qui e' un `pw_stream` di questo file, e i
 *     suoi limiti li scelgo io.  Su Mutter `[M]` (§5.0-sexies) 30 richieste su
 *     30 sono state concesse esatte da 1x1 a 7680x4320, e `rcp_misura_ammessa()`
 *     taglia a 7680x4320: ⇒ la scena «il palco non regge la misura» sul prodotto
 *     vero e' `[?]`, non `[M]`.  Qui si misura il COMPORTAMENTO DI `cattura.c`
 *     quando quella scena capita, non quanto spesso capiti;
 *   · **non prova i pixel**: il palco finto non accoda nessun buffer, quindi
 *     `cattura_prendi()` su un flusso SANO risponde ZERO.  ⭐ Ed e' proprio il
 *     controllo positivo che serve al caso 3: «zero» e «guasto» devono restare
 *     due risposte diverse (`CODER.md` §3.10);
 *   · **non prova `figlio.c`**: i tempi del ciclo del figlio si citano
 *     (`MOVIMENTO_ATTESA_S 0.008`), non si eseguono.
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
 *  ⛔ IL REGISTRO SI CATTURA — e qui e' la MISURA, non un contorno.
 *
 *  `src/registro.c` scrive su `stderr` e non ha nessun gancio d'ascolto:
 *  ⇒ si dirotta `stderr` su un file temporaneo e lo si rilegge.  ⚠ La tecnica
 *  e' quella di `06-b40`, compresa la trappola gia' pagata: **non si tronca il
 *  file, si segna il punto** (un `ftruncate` non sposta l'offset di scrittura,
 *  e davanti resta un buco di NUL su cui `strstr` si ferma ⇒ ogni `dice()`
 *  risponderebbe «no», cioe' verde su ogni caso che pretende un'assenza).
 * ------------------------------------------------------------------ */
#define REG_CAP 262144
static char registro_visto[REG_CAP];
static FILE *dirottato;
static bool parlantina;

static void registro_dirotta(void)
{
	dirottato = tmpfile();
	if (!dirottato) {
		printf("  ⛔ non si apre il file temporaneo per il registro\n");
		exit(2);
	}
	if (dup2(fileno(dirottato), STDERR_FILENO) < 0) {
		printf("  ⛔ non si dirotta stderr\n");
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
 *  ⭐ IL PALCO FINTO — un produttore PipeWire, con i limiti che scelgo io
 *
 *  ⚠ E' quello di `06-b40`, con **una cosa in piu'** che serve al caso 5: il
 *    palco sa RIFARE la propria proposta a caldo (`palco_ripropone`), che e' il
 *    solo modo di chiedersi «un produttore puo' IMPORRE la sua misura a un
 *    consumatore che ne propone una fissa?».
 * ------------------------------------------------------------------ */
typedef struct {
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;
	uint32_t nodo;
	uint32_t min_l, min_a, max_l, max_a;   /* ⛔ i limiti del palco finto */
	bool fissa;                            /* la proposta e' un rettangolo FISSO */
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
	printf("      [palco] formato negoziato: %ux%u  (negoziazione n.%d)\n",
	       info.size.width, info.size.height, p->quante_negoziazioni);
}

static const struct pw_stream_events palco_eventi = {
	PW_VERSION_STREAM_EVENTS,
	.param_changed = palco_parametro,
};

/* ⛔ La cadenza e' un INTERVALLO che parte da zero, non 30/1 fisso: `cattura.c`
 *    propone `framerate` come frazione fissa 0/1 — «la cadenza la detta il
 *    produttore» — e un palco che offrisse 30/1 fisso darebbe intersezione
 *    VUOTA.  ⚠ Difetto del PALCO, gia' pagato da `06-b40` il 21 agosto 2026. */
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

	/* ⛔ L'identificatore del nodo si ASPETTA: prima della registrazione sul
	 *    server e' `SPA_ID_INVALID`, e agganciarcisi vorrebbe dire agganciarsi
	 *    a niente — con il sintomo «cattura non parte» e nessun errore. */
	for (int i = 0; i < 200; i++) {
		p->nodo = pw_stream_get_node_id(p->flusso);
		if (p->nodo != SPA_ID_INVALID && p->nodo != 0)
			break;
		usleep(25000);
	}
	if (p->nodo == SPA_ID_INVALID || p->nodo == 0)
		goto guasto;
	printf("      [palco] nodo %u, regge da %ux%u a %ux%u\n",
	       p->nodo, min_l, min_a, max_l, max_a);
	return p;

guasto:
	printf("      [palco] ⛔ non si apre\n");
	return NULL;
}

/* ⭐ IL PALCO RIFA' LA SUA PROPOSTA A CALDO — e' la leva del caso 5.
 *
 * ⛔ Se `fissa`, il palco pretende ESATTAMENTE `l x a`: e' il produttore che
 *    prova a imporre la propria misura a un consumatore che ne propone una
 *    fissa e diversa.  Se non `fissa`, e' un intervallo nuovo. */
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
	printf("      [palco] ripropone %s %ux%u..%ux%u → %d\n",
	       fissa ? "FISSA" : "intervallo", min_l, min_a, max_l, max_a, esito);
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
 *  Gli esiti
 * ------------------------------------------------------------------ */
static int passati, falliti;

static void esito(const char *nome, bool bene, const char *atteso, const char *visto)
{
	if (bene) {
		printf("  \033[1;32mOK\033[0m  %s\n        %s\n", nome, visto);
		passati++;
	} else {
		printf("  \033[1;31mNO\033[0m  %s\n        atteso: %s\n        visto:  %s\n",
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
 *  1 — ⭐ IL CONTROLLO POSITIVO DELLO STRUMENTO, e va per primo.
 *
 *  ⛔ Il caso 3 pretende che `cattura_prendi()` risponda **GUASTO** su un
 *     flusso morto.  Un `cattura_prendi()` che rispondesse GUASTO **sempre** lo
 *     renderebbe verde per costruzione.  ⇒ Qui il flusso e' SANO e non arriva
 *     nessun fotogramma (il palco finto non accoda buffer): la risposta giusta
 *     e' **ZERO**, non GUASTO (`CODER.md` §3.10 — «una lettura negata non e' una
 *     lettura che dice zero»).
 *
 *  ⚠ E lo stesso caso certifica `dice()`: il registro DEVE contenere la riga
 *    «cattura avviata sul nodo», che c'e' di sicuro.  Se non la trovasse, ogni
 *    altro caso che pretende un'assenza sarebbe verde per un difetto dello
 *    strumento.
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
		esito("1 controllo positivo: flusso sano ⇒ ZERO, e lo strumento vede", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("1 controllo positivo: flusso sano ⇒ ZERO, e lo strumento vede", false,
		      "la cattura si aggancia al nodo del palco finto",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia ha detto no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_rileggi();
	strumento = dice("cattura avviata sul nodo");
	cattura_misura_negoziata(c, &nl, &na);
	presa = cattura_prendi(c, 0.008, &fo, &sbaglio);
	cattura_fermo_libera(&fo);

	bene = strumento && nl == 1920 && na == 1080 && presa == CATTURA_PRESA_ZERO
	    && !dice("MISURA DIVERGENTE");
	snprintf(visto, sizeof visto,
	         "lo strumento %s la riga d'avvio; negoziata %ux%u; cattura_prendi → "
	         "%s (%s); riga MISURA DIVERGENTE: %s",
	         strumento ? "VEDE" : "⛔ NON vede", nl, na,
	         presa == CATTURA_PRESA_ZERO ? "ZERO" :
	         presa == CATTURA_PRESA_FATTA ? "FATTA" : "⛔ GUASTO",
	         sbaglio ? sbaglio->message : "senza errore",
	         dice("MISURA DIVERGENTE") ? "⛔ LA NOMINA" : "assente");
	g_clear_error(&sbaglio);
	esito("1 controllo positivo: flusso sano ⇒ ZERO, e lo strumento vede", bene,
	      "riga d'avvio VISTA · negoziata 1920x1080 · cattura_prendi = ZERO (NON "
	      "guasto) · nessuna MISURA DIVERGENTE", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  2 — ⛔ LA PROPOSTA 1 MESSA ALLA PROVA: *«`figlio.c` non ha modo di sapere
 *      che la rinegoziazione ha UCCISO la cattura: oggi lo scopre solo dal
 *      TIMEOUT di `cattura_prendi`»*.
 *
 *  ⭐ L'ipotesi da SMENTIRE e' quella: che la strada non ci sia, e che quando
 *     c'e' costi un timeout.  ⇒ Si cronometra.
 *
 *  LA SCENA: palco fino a 1920x1080; si chiede 2560x1440; poi si chiama
 *  `cattura_prendi()` con **la stessa attesa del ciclo del figlio**
 *  (`MOVIMENTO_ATTESA_S 0.008`, `figlio.c:3136`), in un ciclo, cronometrando.
 *
 *  ATTESO, dichiarato prima del giro — ed e' l'atteso della PROPOSTA, cioe'
 *  quello che va smentito: `cattura_prendi()` deve o non accorgersene, o
 *  accorgersene spendendo l'attesa intera (>= 8 ms per giro).
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
		esito("2 il flusso morto si SA, e quanto costa saperlo", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("2 il flusso morto si SA, e quanto costa saperlo", false,
		      "la cattura si aggancia al nodo del palco finto",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia ha detto no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_azzera();

	r = cattura_ridimensiona(c, 2560, 1440);
	t0 = ora_ms();

	/* ⛔ Il ciclo del figlio, riprodotto: `cattura_prendi(MOVIMENTO_ATTESA_S)`
	 *    finche' non dice qualcosa di diverso da ZERO.  ⚠ Il tetto e' 2 secondi:
	 *    oltre, la proposta ha ragione e questo caso e' rosso. */
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
			         sbaglio ? sbaglio->message : "senza dettaglio");
			g_clear_error(&sbaglio);
			cattura_fermo_libera(&fo);
			break;
		}
		cattura_fermo_libera(&fo);
		g_clear_error(&sbaglio);
	}
	registro_rileggi();

	/* ⛔ «Lo dice» non basta: deve dire ANCHE PERCHE'.  Un GUASTO senza lo stato
	 *    e senza il guasto del produttore lascerebbe il chiamante a dedurre. */
	nomina_lo_stato = strstr(messaggio, "error") != NULL;

	bene = r == CATTURA_RITELA_CHIESTA && t_guasto >= 0.0 && t_guasto < 100.0
	    && nomina_lo_stato;
	snprintf(visto, sizeof visto,
	         "ridimensiona → %d (0 = «chiesta»); poi %d giri da 8 ms (%d ZERO) e "
	         "il GUASTO arriva a %.1f ms; il messaggio %s lo stato: «%s»",
	         (int)r, giri, giri_zero, t_guasto,
	         nomina_lo_stato ? "NOMINA" : "⛔ NON nomina", messaggio);
	esito("2 il flusso morto si SA, e quanto costa saperlo", bene,
	      "⇒ per SMENTIRE la proposta 1: GUASTO entro 100 ms (non un timeout) e "
	      "un messaggio che nomina lo stato «error»", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  3 — ⛔⛔ IL DIFETTO VERO CHE STA DIETRO ALLA PROPOSTA 1, e non e' in
 *      `cattura.c`: **il rimontaggio alla misura che ha appena ucciso il palco**.
 *
 *  `figlio.c:6299` rimonta con `prendi_il_palco(tela_voluta_l, tela_voluta_a, …)`
 *  — cioe' con **la misura che il client vuole**, che e' esattamente quella che
 *  ha ucciso il flusso.  E `figlio.c:6385` sceglie l'attesa CORTA quando
 *  `codec_chiesto && tela_voluta_l`, cioe' proprio quando qualcuno guarda.
 *
 *  ⇒ La domanda che decide se e' un anello o un cappio: **un `cattura_avvia()`
 *    nuovo alla stessa misura, sullo stesso palco, produce un palco VIVO?**
 *
 *  ⛔⛔ E LA DOMANDA E' IN DUE TEMPI, perche' la prima stesura di questo caso
 *      guardava solo il valore di ritorno e sarebbe stata **verde al contrario**:
 *      `[M]` `cattura_avvia()` a 2560x1440 su un palco che arriva a 1920x1080
 *      **RIESCE 3 volte su 3** — torna un puntatore buono.  ⇒ Guardare il
 *      ritorno vuol dire concludere «non e' un cappio» quando lo e': la
 *      trattativa non e' ancora finita quando il flusso e' gia' `paused`.
 *      ⇒ Si guarda il palco **poco dopo**, con lo stesso `cattura_prendi()` del
 *      ciclo del figlio.
 *
 *  ATTESO, dichiarato prima del giro: se ogni rimontaggio muore subito,
 *  `figlio.c:6299` riprova la stessa misura all'infinito e non ne esce da solo.
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
		esito("3 il rimontaggio alla misura che ha ucciso il palco", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	for (int i = 0; i < tentativi; i++) {
		CatturaPresa presa;

		c = cattura_avvia(p->nodo, 2560, 1440, 30, CATTURA_STRADA_MEMORIA,
		                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
		if (!c) {
			if (!primo[0])
				snprintf(primo, sizeof primo, "cattura_avvia: %s",
				         sbaglio ? sbaglio->message : "senza dettaglio");
			g_clear_error(&sbaglio);
			continue;
		}
		montati++;
		g_clear_error(&sbaglio);
		/* ⛔ 300 ms: la morte misurata dal caso 2 arriva entro 10 ms, e questo e'
		 *    trenta volte tanto — non e' un'attesa tarata sul risultato. */
		aspetta(0.3);
		presa = cattura_prendi(c, 0.008, &fo, &sbaglio);
		cattura_fermo_libera(&fo);
		if (presa != CATTURA_PRESA_GUASTO)
			vivi++;
		else if (!primo[0])
			snprintf(primo, sizeof primo, "%s",
			         sbaglio ? sbaglio->message : "senza dettaglio");
		g_clear_error(&sbaglio);
		cattura_ferma(c);
	}
	registro_rileggi();

	bene = vivi == 0;
	snprintf(visto, sizeof visto,
	         "%d `cattura_avvia()` su %d hanno RESTITUITO un palco a 2560x1440 "
	         "(misura che il palco non regge), ma solo %d erano ancora VIVI 300 "
	         "ms dopo: %s.  Il rifiuto: «%s»",
	         montati, tentativi, vivi,
	         vivi == 0 ? "⛔ nessuno ⇒ `figlio.c:6299` riproverebbe la stessa "
	                     "misura all'infinito, con l'attesa CORTA di `:6385`"
	                   : "⭐ qualcuno regge ⇒ non e' un cappio",
	         primo);
	esito("3 il rimontaggio alla misura che ha ucciso il palco", bene,
	      "0 palchi vivi su 3 (⇒ il ciclo di `figlio.c:6299` non ne esce da solo), "
	      "e `cattura_avvia()` che RIESCE lo stesso", visto);
	palco_chiudi(p);
}

/* =====================================================================
 *  4 — ⭐⭐ LA PROPOSTA 3 MESSA ALLA PROVA: *«resta solo una CORSA, e una corsa
 *      un banco non la programma»*.
 *
 *  ⛔ L'ipotesi da smentire.  La scena non e' una corsa di laboratorio: e'
 *     **due `ADATTA_TELA` incatenate**, cioe' l'utente che TRASCINA il bordo
 *     della finestra — la stessa scena che `DECISIONI.md` §5.0-sexies nomina
 *     («fra cui due `ADATTA_TELA` incatenate»).
 *
 *  LA MECCANICA, e per questo e' programmabile invece che casuale:
 *    · `cattura_ridimensiona(A)` scrive `chiesta_* = A` **sul thread del
 *      chiamante** e poi rinegozia; la risposta (`su_parametri`) arriva **dopo**,
 *      sul thread di PipeWire;
 *    · `cattura_ridimensiona(B)` subito dopo, senza attesa, riscrive
 *      `chiesta_* = B`;
 *    · se il `Format` di A arriva quando `chiesta_*` e' gia' B ⇒ concesso A,
 *      chiesto B ⇒ ⛔ **MISURA DIVERGENTE**.
 *
 *  ⚠ Il palco regge tutt'e due le misure: non c'e' nessun rifiuto in mezzo, la
 *    scena e' completamente SANA.
 *
 *  ATTESO, dichiarato prima del giro: se la riga compare, la proposta 3 e'
 *  SMENTITA e il ramo va provato, non dichiarato morto.  ⚠ Se non compare, si
 *  ripete la catena piu' volte prima di concludere: una corsa che non scatta al
 *  primo colpo non e' una corsa che non esiste.
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
		esito("4 due ridimensionamenti incatenati ⇒ MISURA DIVERGENTE?", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("4 due ridimensionamenti incatenati ⇒ MISURA DIVERGENTE?", false,
		      "la cattura si aggancia al nodo del palco finto",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia ha detto no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_azzera();

	/* ⛔⛔ IL RITARDO FRA LE DUE CHIAMATE SI SPAZZOLA, e non e' un dettaglio:
	 *     con le due chiamate ATTACCATE (ritardo 0) la riga compare `[M]` **2
	 *     volte su 10 giri da 40 catene** — cioe' e' una corsa vera, e un banco
	 *     che si fermasse li' sarebbe verde o rosso a caso.
	 *
	 * ⭐ La finestra ha una larghezza fisica: e' il tempo che il `Format` di A
	 *    impiega a tornare dal server.  Se la seconda chiamata arriva PRIMA che
	 *    A parta, il server risponde una volta sola (con B) e non c'e' niente da
	 *    divergere; se arriva DOPO che A e' stato consegnato, `chiesta_*` era
	 *    ancora A e nemmeno.  ⇒ Si cerca il ritardo che casca in mezzo.
	 *
	 * ⚠ E si spazzola invece di indovinarlo: un ritardo scelto a mano sarebbe un
	 *   numero tarato sulla macchina di chi l'ha scritto. */
	{
		static const int ritardi_us[] = {0, 50, 100, 200, 400, 800, 1600, 3200};
		const int quanti_r = (int)(sizeof ritardi_us / sizeof ritardi_us[0]);
		const int per_ritardo = catene / quanti_r;

		/* ⛔ E NON CI SI FERMA AL PRIMO COLPO: si spazzola TUTTO.  Fermarsi
		 *    darebbe «scattata» e niente profilo, cioe' il numero che serve —
		 *    quale ritardo la fa scattare — resterebbe ignoto. */
		for (int r = 0; r < quanti_r; r++) {
			int colpi = 0;
			for (int k = 0; k < per_ritardo; k++) {
				int i = r * per_ritardo + k;
				uint32_t a_l = 1200 + (uint32_t)(i % 7) * 2u;
				uint32_t a_a =  800 + (uint32_t)(i % 5) * 2u;
				uint32_t b_l = 1600 + (uint32_t)(i % 3) * 2u;
				uint32_t b_a = 1000 + (uint32_t)(i % 11) * 2u;

				/* ⛔ Il registro si azzera A OGNI CATENA, o dal primo colpo in
				 *    poi `dice()` risponderebbe «si» per sempre e ogni ritardo
				 *    successivo risulterebbe un colpo. */
				registro_azzera();
				cattura_ridimensiona(c, a_l, a_a);
				if (ritardi_us[r])
					usleep((useconds_t)ritardi_us[r]);
				cattura_ridimensiona(c, b_l, b_a);
				aspetta(0.03);
				registro_rileggi();
				if (dice("MISURA DIVERGENTE")) {
					colpi++;
					if (scattata < 0) {
						const char *q = strstr(registro_visto,
						                       "MISURA DIVERGENTE");
						/* ⛔ Si taglia al primo punto: il resto della
						 *    riga e' la spiegazione, e qui interessano i
						 *    NUMERI. */
						const char *fine = strstr(q, ".  ");
						scattata = ritardi_us[r];
						snprintf(riga, sizeof riga, "%.*s",
						         (int)(fine ? (size_t)(fine - q)
						                    : strlen(q)), q);
						printf("      [catena] chieste A=%ux%u poi B=%ux%u "
						       "⇒ «%s»\n", a_l, a_a, b_l, b_a, riga);
					}
				}
			}
			printf("      [catena] ritardo %5d us: %d colpi su %d\n",
			       ritardi_us[r], colpi, per_ritardo);
		}
	}

	cattura_misura_chiesta(c, &cl, &ca);
	cattura_misura_negoziata(c, &nl, &na);

	/* ⛔ Questo caso e' VERDE quando la riga COMPARE: e' un banco scritto per
	 *    smentire, e il suo verde e' la smentita. */
	bene = scattata >= 0;
	snprintf(visto, sizeof visto,
	         "su %d catene di due ridimensionamenti (8 ritardi spazzolati) la riga "
	         "MISURA DIVERGENTE %s%d; chiesta finale %ux%u, negoziata %ux%u",
	         catene,
	         scattata >= 0 ? "⭐ E' COMPARSA ⇒ la proposta 3 e' SMENTITA, il ramo "
	                         "si raggiunge dall'esterno — primo colpo col ritardo "
	                         "di us "
	                       : "⛔ NON compare ⇒ la proposta 3 REGGE; catene spese: ",
	         scattata >= 0 ? scattata : catene,
	         cl, ca, nl, na);
	esito("4 due ridimensionamenti incatenati ⇒ MISURA DIVERGENTE?", bene,
	      "la riga COMPARE (⇒ proposta 3 smentita)", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  5 — ⭐ L'ALTRA STRADA PER SMENTIRE LA PROPOSTA 3: **il produttore prova a
 *      IMPORRE la sua misura**.
 *
 *  `cattura.c:~1069` propone la misura come `SPA_POD_Rectangle`, cioe' FISSA.
 *  L'argomento della proposta 3 e' strutturale: l'intersezione di un rettangolo
 *  fisso con qualunque cosa e' o quel rettangolo o l'insieme vuoto.  ⇒ Si mette
 *  alla prova chiedendo al palco di **rifare la propria proposta** con un
 *  rettangolo fisso DIVERSO, a flusso vivo.
 *
 *  ATTESO, dichiarato prima del giro: o il consumatore riceve un `Format` alla
 *  misura del PRODUTTORE (⇒ divergenza, proposta 3 smentita per questa strada),
 *  o la trattativa fallisce e il flusso muore (⇒ l'argomento strutturale regge).
 *
 *  ⛔ MISURATO, 22 agosto 2026, PipeWire 1.4.2: **il flusso muore**
 *     (`paused → error — no more input formats`), nessun `Format` nuovo, nessuna
 *     divergenza.  ⇒ Per QUESTA strada la proposta 3 regge, e la smentita e'
 *     tutta del caso 4 — che passa da un'altra porta: non «il produttore impone
 *     un'altra misura», ma «`chiesta_*` e' gia' cambiata quando la risposta
 *     arriva».  ⚠ Il verde di questo caso e' quindi la morte del flusso: e' il
 *     controllo che tiene onesto il caso 4, perche' dimostra che la divergenza
 *     del caso 4 **non** puo' venire dal produttore.
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
		esito("5 il produttore prova a IMPORRE la sua misura", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("5 il produttore prova a IMPORRE la sua misura", false,
		      "la cattura si aggancia al nodo del palco finto",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia ha detto no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_azzera();

	/* ⛔ Il palco pretende 1600x900 FISSI, mentre il consumatore ha 1920x1080. */
	palco_ripropone(p, 1600, 900, 1600, 900, true);
	aspetta(1.0);
	registro_rileggi();

	cattura_misura_chiesta(c, &cl, &ca);
	cattura_misura_negoziata(c, &nl, &na);
	divergente = dice("MISURA DIVERGENTE");
	in_errore = dice("→ error");

	/* ⛔ Verde = il produttore NON ce l'ha fatta.  ⚠ Se un giorno la divergenza
	 *    comparisse di qui, questo caso diventa rosso — ed e' quel che si vuole:
	 *    vorrebbe dire che il rettangolo fisso non e' piu' una garanzia, e che il
	 *    caso 4 ha una seconda sorgente da distinguere. */
	bene = !divergente && in_errore && nl == 1920 && na == 1080;
	snprintf(visto, sizeof visto,
	         "il palco ha preteso 1600x900 fissi; chiesta %ux%u, negoziata %ux%u; "
	         "flusso %s; MISURA DIVERGENTE: %s",
	         cl, ca, nl, na, in_errore ? "in ERROR" : "⛔ vivo",
	         divergente ? "⛔ COMPARSA ⇒ il produttore IMPONE, e il caso 4 ha una "
	                      "seconda sorgente"
	                    : "assente ⇒ il rettangolo FISSO regge: o quel valore, o "
	                      "l'insieme vuoto");
	esito("5 il produttore prova a IMPORRE la sua misura", bene,
	      "negoziata ancora 1920x1080 · flusso in error · NESSUNA divergenza "
	      "(⇒ il produttore non puo' imporre)", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  6 — ⛔ LA PROPOSTA 2 MESSA ALLA PROVA: serve un accessore per la divergenza?
 *
 *  L'argomento della proposta: `misura_divergente` e' scritta e mai letta, e
 *  `cattura.h` non la espone ⇒ nessun chiamante puo' saperlo.
 *
 *  ⭐ L'ipotesi da smentire: che il chiamante NON possa saperlo.  `cattura.h`
 *     espone gia' **due** accessori — `cattura_misura_chiesta()` e
 *     `cattura_misura_negoziata()` — e la divergenza e' la loro disuguaglianza.
 *     ⇒ Si verifica che i due bastino a ricostruirla, compreso il caso in cui il
 *     formato non e' ancora noto (dove il terzo campo mentirebbe: e' `FALSE`
 *     perche' non c'e' ancora niente da confrontare, non perche' vada tutto
 *     bene — `CODER.md` §3.10).
 * ===================================================================== */
static void caso6(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	uint32_t cl = 0, ca = 0, nl = 0, na = 0;
	gboolean noto_prima, noto_dopo;
	/* ⛔ I numeri di PRIMA si tengono in variabili loro: la prima stesura di
	 *    questo caso li ristampava come `0` scritti a mano nella `printf`, cioe'
	 *    il banco DICEVA un numero che non aveva letto — difetto dell'autore,
	 *    trovato rileggendo l'uscita. */
	uint32_t cl0 = 0, ca0 = 0, nl0 = 0, na0 = 0;
	bool bene;
	char visto[800];

	registro_azzera();
	p = palco_apri(320, 240, 1920, 1080);
	if (!p) {
		esito("6 i due accessori bastano a ricostruire la divergenza", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("6 i due accessori bastano a ricostruire la divergenza", false,
		      "la cattura si aggancia al nodo del palco finto",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia ha detto no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	cattura_misura_chiesta(c, &cl0, &ca0);
	noto_prima = cattura_misura_negoziata(c, &nl0, &na0);

	/* ⛔ La richiesta che il palco non regge: da qui in poi «chiesta» e
	 *    «negoziata» divergono, e lo dicono i due accessori PUBBLICI. */
	cattura_ridimensiona(c, 2560, 1440);
	aspetta(0.5);
	cattura_misura_chiesta(c, &cl, &ca);
	noto_dopo = cattura_misura_negoziata(c, &nl, &na);

	bene = noto_prima && cl0 == 1920 && ca0 == 1080 && nl0 == 1920 && na0 == 1080
	    && noto_dopo && cl == 2560 && ca == 1440 && nl == 1920 && na == 1080;
	snprintf(visto, sizeof visto,
	         "prima: chiesta %ux%u, negoziata %s%ux%u.  Dopo la richiesta che il "
	         "palco non regge: chiesta %ux%u, negoziata %s%ux%u ⇒ la divergenza "
	         "%s dai due accessori pubblici, e senza il campo privato",
	         cl0, ca0, noto_prima ? "" : "⛔ IGNOTA ", nl0, na0,
	         cl, ca, noto_dopo ? "" : "⛔ IGNOTA ", nl, na,
	         (cl != nl || ca != na) ? "SI LEGGE" : "⛔ non si legge");
	esito("6 i due accessori bastano a ricostruire la divergenza", bene,
	      "chiesta 2560x1440 · negoziata 1920x1080, tutt'e due leggibili da "
	      "`cattura.h` senza un terzo accessore", visto);
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
	/* ⛔ La parlantina del REGISTRO si accende SEMPRE: «stato del flusso: paused
	 *    → error» e' `registro_dettaglio()` (`cattura.c:318`) e a parlantina
	 *    spenta non si scrive affatto — i casi che quella riga la PRETENDONO
	 *    sarebbero rossi per un motivo che non c'entra con quel che misurano. */
	registro_parlantina(true);
	registro_dirotta();

	printf("\n== 06-b5: le tre proposte di 06-b40, messe alla prova per SMENTIRLE ==\n\n");
	for (int i = 0; i < quanti; i++) {
		if (solo && solo != i + 1)
			continue;
		casi[i]();
	}
	printf("\n  passati %d, falliti %d\n\n", passati, falliti);
	return falliti ? 1 : 0;
}
