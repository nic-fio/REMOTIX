/*
 * 06-b40-palco-finto.c — ⭐ `src/cattura.c` con un PALCO FINTO, in locale.
 *
 *   06-b40-palco-finto              gira i due casi
 *   06-b40-palco-finto <n>          gira solo il caso n
 *
 * ---------------------------------------------------------------------------
 * ⛔ LA `[?]` CHE ESISTE PER CHIUDERE
 *
 * `fasi/06-la-tela-e-la-vista.md` §7.2: *«codice mai esercitato su Mutter: il
 * ramo “concesso diverso da chiesto” (`figlio.c`) e `MISURA DIVERGENTE`
 * (`cattura.c:543`) — 17 richieste su 17 concesse esatte.  Provabili **solo col
 * palco finto**»*.
 *
 * ⭐ E il palco finto qui e' un **produttore PipeWire vero**, dentro questo
 *    stesso programma: nessun Mutter, nessun D-Bus, nessuna macchina di prova.
 *    Il consumatore e' `src/cattura.c` **intatto**, guidato dalla sua API
 *    pubblica — `cattura_avvia`, `cattura_ridimensiona`, `cattura_risveglia`.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ COME SI ARRIVA A UNA MISURA DIVERGENTE, VISTO CHE `cattura.c` PROPONE UN
 *      RETTANGOLO FISSO
 *
 * `proposta()` (`cattura.c:1069`) dichiara la misura come `SPA_POD_Rectangle`,
 * cioe' **fissa**: la trattativa di PipeWire interseca le due proposte, quindi
 * finche' la trattativa **riesce** il concesso e' per forza uguale al chiesto —
 * ed e' la ragione per cui su Mutter la riga non e' mai comparsa in 17
 * richieste su 17.  ⚠ Chi conclude «allora e' codice morto» si ferma un passo
 * prima.
 *
 * ⭐ La strada c'e', ed e' quella che il prodotto percorre davvero:
 *
 *   1. `cattura_ridimensiona(L, A)` scrive `chiesta_* = L x A` **subito**
 *      (`cattura.c:1354`) e poi rinegozia;
 *   2. se il palco **non regge** quella misura, la trattativa fallisce: nessun
 *      `Format` nuovo arriva, e `formato` resta quello di prima;
 *   3. `cattura_risveglia()` (`cattura.c:1414`) ripropone la misura
 *      **NEGOZIATA**, non la chiesta — e lo dichiara.  Il palco l'accetta,
 *      `su_parametri()` gira, e `chiesta_* != formato`:
 *      ⇒ ⛔ **MISURA DIVERGENTE**.
 *
 * ⚠ E non e' una scena di laboratorio: `cattura_risveglia()` e' chiamata a ogni
 *   risveglio del ciclo (~400 ms su scena ferma, `fasi/06` §7.1).  ⇒ Su Mutter
 *   basta UN ridimensionamento rifiutato perche' la riga compaia al risveglio
 *   dopo.  La riga non e' irraggiungibile: e' non ancora incontrata.
 *
 * ---------------------------------------------------------------------------
 * ⛔ QUEL CHE QUESTO BANCO **NON** PROVA
 *
 *   · **non prova che il puntatore vada al posto giusto**: `misura_divergente`
 *     e' un `gboolean` che **nessuno legge** (`cattura.c` 81, 541, 548, 551,
 *     1358 — cinque occorrenze, tutte scritture).  ⇒ La guardia DICHIARA il
 *     danno e non lo previene, e nessun chiamante puo' nemmeno saperlo:
 *     `cattura.h` non espone un accessore.  Questo banco misura la RIGA;
 *   · **non prova Mutter**: il palco qui e' un `pw_stream` di questo file;
 *   · **non prova i pixel**: qui non si guarda nessun fotogramma.
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
 *  ⇒ si dirotta `stderr` su un file temporaneo e lo si rilegge.  ⚠ E si
 *  dichiara, invece di far credere che ci sia un'API che non c'e'.
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

/* ⛔ E NON SI TRONCA IL FILE: si SEGNA il punto.
 *
 *    `ftruncate()` non sposta l'offset di scrittura di `stderr`: la riga dopo
 *    torna a scriversi dove stava, e davanti resta un buco di byte NUL.  ⇒ Il
 *    `pread` da zero legge uno zero al primo byte, `strstr` si ferma li', e
 *    OGNI `dice()` risponde «no».  ⚠ Un banco che risponde sempre «no» e'
 *    verde su ogni caso che pretende un'assenza — costato un giro. */
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
 * ------------------------------------------------------------------ */
typedef struct {
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;
	uint32_t nodo;
	uint32_t min_l, min_a, max_l, max_a;   /* ⛔ i limiti del palco finto */
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

/* ⛔ La proposta del palco e' un INTERVALLO, e la scelta e' apposta: cosi' il
 *    palco «regge» le misure dentro e **rifiuta** quelle fuori, che e' proprio
 *    la differenza fra un compositore che obbedisce e uno che non puo'. */
static const struct spa_pod *palco_proposta(struct spa_pod_builder *b, Palco *p)
{
	struct spa_rectangle mis  = SPA_RECTANGLE(p->min_l, p->min_a);
	struct spa_rectangle mini = SPA_RECTANGLE(p->min_l, p->min_a);
	struct spa_rectangle maxi = SPA_RECTANGLE(p->max_l, p->max_a);
	/* ⛔ E LA CADENZA E' UN INTERVALLO CHE PARTE DA ZERO, non 30/1 fisso.
	 *
	 *    `cattura.c:1015` propone `SPA_FORMAT_VIDEO_framerate` come frazione
	 *    **fissa 0/1** — «la cadenza la detta il produttore» — e un palco che
	 *    offrisse 30/1 fisso darebbe intersezione VUOTA: PipeWire risponde
	 *    `no more input formats`, il flusso va in `error`, e il sintomo e'
	 *    «negoziata 0x0» che somiglia a un difetto del prodotto.  ⚠ Costato
	 *    un giro il 21 agosto 2026, ed e' un difetto del PALCO FINTO. */
	struct spa_fraction cad   = SPA_FRACTION(0, 1);
	struct spa_fraction cmin  = SPA_FRACTION(0, 1);
	struct spa_fraction cmax  = SPA_FRACTION(120, 1);

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

	p->ciclo = pw_thread_loop_new("palco-finto", NULL);
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
	p->flusso = pw_stream_new(p->nucleo, "palco-finto",
	                          pw_properties_new(PW_KEY_MEDIA_TYPE, "Video",
	                                            PW_KEY_MEDIA_CATEGORY, "Playback",
	                                            PW_KEY_MEDIA_ROLE, "Screen",
	                                            /* ⛔ `media.class = Video/Source`:
	                                             *    senza, il gestore di sessione
	                                             *    non lo tratta come una sorgente
	                                             *    e nessuno lo aggancia — il
	                                             *    sintomo e' «negoziata 0x0». */
	                                            PW_KEY_MEDIA_CLASS, "Video/Source",
	                                            PW_KEY_NODE_NAME, "remotix-palco-finto",
	                                            NULL));
	if (!p->flusso) {
		pw_thread_loop_unlock(p->ciclo);
		goto guasto;
	}
	pw_stream_add_listener(p->flusso, &p->gancio, &palco_eventi, p);
	par[0] = palco_proposta(&b, p);
	if (pw_stream_connect(p->flusso, PW_DIRECTION_OUTPUT, PW_ID_ANY,
	                      PW_STREAM_FLAG_MAP_BUFFERS,
	                      par, 1) < 0) {
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

/* =====================================================================
 *  1 — ⭐ IL CONTROLLO NEGATIVO, e va per primo: quando il palco OBBEDISCE,
 *      la riga NON deve comparire.  ⛔ Senza questo caso, un `cattura.c` che
 *      scrivesse «MISURA DIVERGENTE» a ogni negoziazione passerebbe il caso 2.
 * ===================================================================== */
static void caso1(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	uint32_t nl = 0, na = 0;
	bool bene;
	char visto[512];

	registro_azzera();
	p = palco_apri(320, 240, 4096, 4096);
	if (!p) {
		esito("1 il palco obbedisce: nessuna divergenza", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("1 il palco obbedisce: nessuna divergenza", false,
		      "la cattura si aggancia al nodo del palco finto",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia ha detto no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_rileggi();
	cattura_misura_negoziata(c, &nl, &na);
	bene = nl == 1920 && na == 1080 && !dice("MISURA DIVERGENTE");
	snprintf(visto, sizeof visto,
	         "negoziata %ux%u, il registro %s la divergenza", nl, na,
	         dice("MISURA DIVERGENTE") ? "⛔ LA NOMINA" : "non la nomina");
	esito("1 il palco obbedisce: nessuna divergenza", bene,
	      "negoziata 1920x1080 e NESSUNA riga «MISURA DIVERGENTE»", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

/* =====================================================================
 *  2 — ⛔⛔ IL RAMO `cattura.c:543` **NON SI RAGGIUNGE DALL'ESTERNO**, e questa
 *      e' la misura che lo dice — 21 agosto 2026.
 *
 *      ⚠ Questo caso e' nato per FAR SCATTARE «MISURA DIVERGENTE», e ha
 *        misurato il contrario.  Si tiene com'e', perche' un tentativo
 *        fallito con il motivo accanto vale piu' di una `[?]` ripetuta.
 *
 *      LA SCENA: il palco regge fino a 1920x1080; si chiede 2560x1440.
 *
 *      QUEL CHE SUCCEDE DAVVERO, `[M]` su PipeWire 1.4.2:
 *
 *        · `cattura_ridimensiona()` scrive `chiesta_* = 2560x1440` e torna
 *          **0** — cioe' «chiesta», che il chiamante legge come «e' partita»;
 *        · due millisecondi dopo il flusso va in `paused → error — no more
 *          input formats`: ⛔ la trattativa fallita non lascia il flusso
 *          «fermo alla misura vecchia», lo **uccide**;
 *        · `cattura_risveglia()` guarda lo stato (`cattura.c:1404`) e si
 *          rifiuta: torna `FALSE`.  ⇒ Nessun `Format` nuovo arriva mai, e
 *          `su_parametri()` non gira piu'.
 *
 *      ⇒ Con la proposta a rettangolo FISSO di `cattura.c:1069`, ogni volta che
 *        `su_parametri()` gira il concesso e' per forza uguale al chiesto; e
 *        quando non lo sarebbe, `su_parametri()` non gira.  ⛔ L'unica finestra
 *        che resta e' una CORSA — un `Format` vecchio che arriva dopo che
 *        `chiesta_*` e' gia' cambiato — e una corsa un banco non la
 *        programma.
 *
 *      ⭐ E il difetto vero che questa misura ha trovato non e' li': e' che
 *        `cattura_ridimensiona()` dichiara **successo** su un flusso che muore
 *        subito dopo, e `misura_divergente` e' un campo che **nessuno legge**.
 *        La guardia di `DECISIONI.md` §5.0-sexies dichiara il danno e non lo
 *        previene.  La proposta sta nel rapporto: un accessore in `cattura.h`.
 *
 *      ATTESO, dichiarato prima di questo giro: chiesta 2560x1440, negoziata
 *      ancora 1920x1080, il flusso in `error`, `cattura_risveglia()` che
 *      RIFIUTA, e ⛔ NESSUNA riga «MISURA DIVERGENTE».
 *      ⚠ Se un giorno la riga comparisse, questo caso diventa rosso — ed e'
 *        proprio quello che si vuole: vorrebbe dire che il ramo si raggiunge, e
 *        che va scritto un caso vero.
 * ===================================================================== */
static void caso2(void)
{
	Palco *p;
	Cattura *c;
	GError *sbaglio = NULL;
	uint32_t cl = 0, ca = 0, nl = 0, na = 0;
	CatturaRitela r;
	gboolean risvegliata;
	bool bene, in_errore, divergente;
	char visto[700];

	registro_azzera();
	p = palco_apri(320, 240, 1920, 1080);
	if (!p) {
		esito("2 il ramo MISURA DIVERGENTE non si raggiunge dall'esterno", false,
		      "il palco finto si apre", "⛔ il palco finto NON si e' aperto");
		return;
	}
	c = cattura_avvia(p->nodo, 1920, 1080, 30, CATTURA_STRADA_MEMORIA,
	                  CATTURA_COLORE_BGRX, NULL, NULL, NULL, &sbaglio);
	if (!c) {
		esito("2 il ramo MISURA DIVERGENTE non si raggiunge dall'esterno", false,
		      "la cattura si aggancia al nodo del palco finto",
		      sbaglio ? sbaglio->message : "⛔ cattura_avvia ha detto no");
		g_clear_error(&sbaglio);
		palco_chiudi(p);
		return;
	}
	aspetta(1.0);
	registro_azzera();          /* ⛔ da qui in poi si guarda la divergenza */

	r = cattura_ridimensiona(c, 2560, 1440);
	aspetta(1.0);
	risvegliata = cattura_risveglia(c);
	aspetta(1.0);
	registro_rileggi();

	cattura_misura_chiesta(c, &cl, &ca);
	cattura_misura_negoziata(c, &nl, &na);
	in_errore = dice("→ error");
	divergente = dice("MISURA DIVERGENTE");
	bene = cl == 2560 && ca == 1440 && nl == 1920 && na == 1080
	    && in_errore && !risvegliata && !divergente;
	snprintf(visto, sizeof visto,
	         "ridimensiona -> %d (0 = «chiesta»), chiesta %ux%u, negoziata "
	         "%ux%u; flusso %s; risveglia -> %s; riga MISURA DIVERGENTE: %s",
	         (int)r, cl, ca, nl, na,
	         in_errore ? "in ERROR" : "⛔ NON in error",
	         risvegliata ? "⛔ SI" : "no (lo stato non lo permette)",
	         divergente ? "⭐ COMPARSA — il ramo si raggiunge, va scritto un caso"
	                    : "assente");
	esito("2 il ramo MISURA DIVERGENTE non si raggiunge dall'esterno", bene,
	      "chiesta 2560x1440 · negoziata 1920x1080 · flusso in error · "
	      "risveglia rifiuta · NESSUNA riga «MISURA DIVERGENTE»", visto);
	cattura_ferma(c);
	palco_chiudi(p);
}

int main(int argc, char **argv)
{
	int solo = argc > 1 ? atoi(argv[1]) : 0;
	void (*casi[])(void) = {caso1, caso2};
	const int quanti = (int)(sizeof casi / sizeof casi[0]);

	parlantina = getenv("PARLANTINA") != NULL;
	pw_init(&argc, &argv);
	/* ⛔ La parlantina del REGISTRO si accende SEMPRE, e non e' la stessa cosa
	 *    della parlantina di questo banco (che decide solo se ristampare le
	 *    righe su stdout).  ⚠ «stato del flusso: paused → error» e'
	 *    `registro_dettaglio()` (`cattura.c:318`): a parlantina spenta non si
	 *    scrive affatto, e il caso 2 — che quella riga la PRETENDE — sarebbe
	 *    rosso per un motivo che non c'entra con quel che misura. */
	registro_parlantina(true);
	registro_dirotta();

	printf("\n== 06-b40: `src/cattura.c` con un palco finto (PipeWire vero) ==\n\n");
	for (int i = 0; i < quanti; i++) {
		if (solo && solo != i + 1)
			continue;
		casi[i]();
	}
	printf("\n  passati %d, falliti %d\n\n", passati, falliti);
	return falliti ? 1 : 0;
}
