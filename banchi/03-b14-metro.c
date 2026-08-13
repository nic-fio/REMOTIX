/*
 * 03-b14-metro.c — IL LATO CHE RICEVE del banco B14.
 *
 *   03-b14-metro --nodo <id> --misura 1920x1080 --cadenza 60
 *
 * Legge comandi da standard input, una riga per comando:
 *
 *   M <etichetta>   segna un istante (inizio/fine di una cella)
 *   R <n>           ⭐ RINEGOZIA LA SOLA CADENZA a <n>, misura invariata
 *   C <n>           rinegozia staccando e riattaccando (ripiego, dichiarato)
 *   Q               esce
 *
 * Scrive su standard output, una riga per evento, sempre con i microsecondi
 * monotoni davanti:
 *
 *   f <us> <seq> <cambiato>   un fotogramma CONSEGNATO (cambiato: 0/1/-1)
 *   n <us> <l>x<a> max=<n>/<d> fr=<n>/<d>   formato NEGOZIATO (param_changed)
 *   s <us> <stato>            cambio di stato del flusso
 *   m <us> <etichetta>        marcatore
 *   r <us> <n> rc=<...>       richiesta di rinegoziazione partita
 *   e <us> <testo>            errore
 *
 * ===========================================================================
 * ⛔ PERCHE' NON BASTA `pipewiresrc` DI GSTREAMER
 *
 * Il banco deve fare DUE cose che un `pipewiresrc` non fa:
 *
 *   1. FISSARE `maxFramerate` invece di lasciarlo concordare.  Mutter offre
 *      `SPA_POD_CHOICE_RANGE_Fraction(default 60, [1..1000])` `[R]`
 *      (`meta-screen-cast-stream-src.c:1350`), e chi non fissa si prende il
 *      default senza sapere di averlo preso — due misure sotto la stessa
 *      etichetta, cioe' `LEZIONI.md` §1.8.
 *   2. RINEGOZIARE a flusso vivo, cambiando SOLO la cadenza e lasciando la
 *      misura dov'e'.  E' l'ipotesi stessa del banco.
 *
 * ===========================================================================
 * ⛔ E SI VERIFICA CHE IL COMPOSITORE ABBIA OBBEDITO
 *
 * §1.8: «quando si chiede un componente per nome, si verifica che abbia
 * obbedito».  La riga `n` stampa il formato che PipeWire ha FISSATO — non
 * quello che abbiamo chiesto.  Se chiediamo 120 e la riga dice 60, il numero
 * che segue non e' la misura di 120: e' la misura di 60 con un'etichetta
 * sbagliata addosso.
 *
 * ===========================================================================
 * ⚠ IL BUFFER E' MemFd, NON DMA-BUF, ED E' UNA SCELTA DICHIARATA
 *
 * Non si offrono modificatori: Mutter allora propone solo la forma senza
 * modificatori `[R]`, e i buffer arrivano in memoria condivisa.  Il freno che
 * questo banco misura sta in `maybe_record_frame_with_timestamp`, cioe' PRIMA
 * di qualunque scelta di buffer — ma la copia in memoria costa a Mutter, e se
 * il numero si fermasse li' invece che sul freno lo direbbe il conto dei
 * disegni della scena, che e' il controllo di §1.1.
 *
 * ⭐ E poiche' i buffer si mappano, si legge un pugno di pixel a campione: un
 *    fotogramma consegnato UGUALE al precedente e' un fotogramma che non porta
 *    informazione, e va contato a parte (`LEZIONI.md` §4.6 — il verde non e'
 *    vero).
 */
#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <spa/param/video/format-utils.h>
#include <spa/param/props.h>
#include <spa/debug/types.h>
#include <spa/utils/result.h>
#include <pipewire/pipewire.h>

typedef struct
{
	struct pw_main_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook ascolto;
	struct spa_source *sorgente_stdin;

	uint32_t nodo;
	uint32_t larghezza, altezza;
	uint32_t cadenza;   /* il maxFramerate che stiamo chiedendo adesso */

	struct spa_video_info_raw formato;
	int formato_valido;

	uint64_t impronta_precedente;
	int impronta_valida;
	uint8_t spazio[4096];
} Metro;

static Metro metro;

static uint64_t ora_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000ull + (uint64_t) (t.tv_nsec / 1000);
}

static void riga(const char *tipo, const char *formato, ...)
{
	va_list a;
	printf("%s %llu ", tipo, (unsigned long long) ora_us());
	va_start(a, formato);
	vprintf(formato, a);
	va_end(a);
	putchar('\n');
	fflush(stdout);
}

/* ------------------------------------------------------------------ *
 *  La proposta: misura FISSA, cadenza FISSA
 * ------------------------------------------------------------------ *
 * ⛔ Tutti e due i valori fissi, e per due ragioni diverse:
 *
 *   · la MISURA fissa perche' un intervallo aperto lascerebbe scegliere
 *     PipeWire, che prenderebbe il default di Mutter (1280x720) — e nessuno se
 *     ne accorgerebbe finche' non guarda i pixel (e' il commento gia' scritto
 *     in `src/cattura.c`);
 *   · la CADENZA fissa perche' e' la grandezza sotto esame: un intervallo
 *     darebbe un numero concordato invece del numero chiesto.
 *
 * ⛔ E la misura resta IDENTICA anche nella rinegoziazione: e' precisamente
 *    quel che fa scattare l'uscita anticipata di `ensure_virtual_monitor`
 *    (`if (mode_info->width == … && mode_info->height == …) return;`), cioe'
 *    l'ipotesi che questo banco esiste per provare.
 */
static const struct spa_pod *proposta(struct spa_pod_builder *b, uint32_t larghezza,
                                      uint32_t altezza, uint32_t cadenza)
{
	struct spa_rectangle misura = SPA_RECTANGLE(larghezza, altezza);
	struct spa_fraction ferma = SPA_FRACTION(0, 1);
	struct spa_fraction massima = SPA_FRACTION(cadenza, 1);

	return spa_pod_builder_add_object(
	    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat,
	    SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
	    SPA_FORMAT_VIDEO_format,
	    SPA_POD_CHOICE_ENUM_Id(3, SPA_VIDEO_FORMAT_BGRx, SPA_VIDEO_FORMAT_BGRx,
	                           SPA_VIDEO_FORMAT_BGRA),
	    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura),
	    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&ferma),
	    SPA_FORMAT_VIDEO_maxFramerate, SPA_POD_Fraction(&massima));
}

/* ------------------------------------------------------------------ *
 *  Eventi del flusso
 * ------------------------------------------------------------------ */
static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *sbaglio)
{
	(void) dati;
	riga("s", "%s->%s%s%s", pw_stream_state_as_string(vecchio),
	     pw_stream_state_as_string(nuovo), sbaglio ? " " : "", sbaglio ? sbaglio : "");
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Metro *m = dati;
	uint8_t spazio[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[2];

	uint32_t tipo, sottotipo;

	if (param == NULL || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &tipo, &sottotipo) < 0)
		return;
	if (tipo != SPA_MEDIA_TYPE_video || sottotipo != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &m->formato) < 0)
		return;
	m->formato_valido = 1;

	/* ⛔ SI STAMPA QUEL CHE E' STATO FISSATO, non quel che si e' chiesto. */
	riga("n", "%ux%u max=%u/%u fr=%u/%u chiesto=%u", m->formato.size.width,
	     m->formato.size.height, m->formato.max_framerate.num, m->formato.max_framerate.denom,
	     m->formato.framerate.num, m->formato.framerate.denom, m->cadenza);

	parametri[0] = spa_pod_builder_add_object(
	    &b, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers,
	    SPA_PARAM_BUFFERS_buffers, SPA_POD_CHOICE_RANGE_Int(8, 2, 16),
	    SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int((1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr)));
	parametri[1] = spa_pod_builder_add_object(
	    &b, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta,
	    SPA_PARAM_META_type, SPA_POD_Id(SPA_META_Header),
	    SPA_PARAM_META_size, SPA_POD_Int(sizeof(struct spa_meta_header)));

	pw_stream_update_params(m->flusso, parametri, 2);
}

/* Un'impronta a campione: 64 punti sparsi.  Non e' un checksum del fotogramma
 * e non pretende di esserlo — serve solo a distinguere «consegnato e diverso»
 * da «consegnato uguale», che sono due cose che il conto dei fotogrammi
 * confonde. */
static uint64_t impronta(const uint8_t *pixel, size_t quanti)
{
	uint64_t h = 1469598103934665603ull;
	size_t passo = quanti / 64 ? quanti / 64 : 1;
	size_t i;

	for (i = 0; i + 4 <= quanti; i += passo)
	{
		uint32_t v;
		memcpy(&v, pixel + i, sizeof v);
		h = (h ^ v) * 1099511628211ull;
	}
	return h;
}

static void su_fotogramma(void *dati)
{
	Metro *m = dati;
	struct pw_buffer *b;
	struct spa_buffer *sb;
	struct spa_meta_header *intestazione;
	int cambiato = -1;
	uint64_t seq = 0;

	b = pw_stream_dequeue_buffer(m->flusso);
	if (!b)
		return;
	sb = b->buffer;

	intestazione = spa_buffer_find_meta_data(sb, SPA_META_Header, sizeof *intestazione);
	if (intestazione)
		seq = intestazione->seq;

	if (sb->n_datas > 0 && sb->datas[0].data && sb->datas[0].chunk &&
	    sb->datas[0].chunk->size > 0)
	{
		uint64_t h = impronta(sb->datas[0].data, sb->datas[0].chunk->size);
		cambiato = m->impronta_valida ? (h != m->impronta_precedente) : 1;
		m->impronta_precedente = h;
		m->impronta_valida = 1;
	}

	riga("f", "%llu %d", (unsigned long long) seq, cambiato);
	pw_stream_queue_buffer(m->flusso, b);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_fotogramma,
};

/* ------------------------------------------------------------------ *
 *  Attacco e rinegoziazione
 * ------------------------------------------------------------------ */
static int attacca(Metro *m)
{
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(m->spazio, sizeof m->spazio);
	const struct spa_pod *parametri[1];

	parametri[0] = proposta(&b, m->larghezza, m->altezza, m->cadenza);
	return pw_stream_connect(m->flusso, PW_DIRECTION_INPUT, m->nodo,
	                         PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS,
	                         parametri, 1);
}

/* ⭐ LA RIGA CHE E' TUTTO IL BANCO: cambia la sola `maxFramerate`, con la
 *    misura identica, sul flusso GIA' ATTACCATO.  Se `ensure_virtual_monitor`
 *    esce prima come il codice dice, il monitor non si muove e il freno si'. */
static void rinegozia(Metro *m, uint32_t cadenza)
{
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(m->spazio, sizeof m->spazio);
	const struct spa_pod *parametri[1];
	int rc;

	m->cadenza = cadenza;
	parametri[0] = proposta(&b, m->larghezza, m->altezza, cadenza);
	rc = pw_stream_update_params(m->flusso, parametri, 1);
	riga("r", "%u rc=%d(%s)", cadenza, rc, rc < 0 ? spa_strerror(rc) : "ok");
}

/* Il ripiego, e si dichiara: stacca e riattacca.  ⚠ Non e' la stessa cosa —
 * prova un'ipotesi piu' debole («riattaccarsi con un'altra cadenza non ricrea
 * il monitor») invece di quella vera («rinegoziare a caldo non lo ricrea»). */
static void riattacca(Metro *m, uint32_t cadenza)
{
	int rc;

	pw_stream_disconnect(m->flusso);
	m->cadenza = cadenza;
	m->formato_valido = 0;
	rc = attacca(m);
	riga("r", "%u rc=%d(%s) STACCA-RIATTACCA", cadenza, rc, rc < 0 ? spa_strerror(rc) : "ok");
}

/* ------------------------------------------------------------------ *
 *  I comandi, letti dentro il ciclo di PipeWire
 * ------------------------------------------------------------------ */
static void su_stdin(void *dati, int fd, uint32_t maschera)
{
	Metro *m = dati;
	static char resto[512];
	static size_t quanto;
	char pezzo[512];
	ssize_t letti;
	(void) maschera;

	letti = read(fd, pezzo, sizeof pezzo);
	if (letti <= 0)
	{
		riga("e", "stdin chiuso: esco");
		pw_main_loop_quit(m->ciclo);
		return;
	}
	for (ssize_t i = 0; i < letti; i++)
	{
		if (pezzo[i] != '\n')
		{
			if (quanto + 1 < sizeof resto)
				resto[quanto++] = pezzo[i];
			continue;
		}
		resto[quanto] = 0;
		quanto = 0;

		if (resto[0] == 'M')
			riga("m", "%s", resto + 2);
		else if (resto[0] == 'R')
			rinegozia(m, (uint32_t) atoi(resto + 2));
		else if (resto[0] == 'C')
			riattacca(m, (uint32_t) atoi(resto + 2));
		else if (resto[0] == 'Q')
		{
			pw_main_loop_quit(m->ciclo);
			return;
		}
		else if (resto[0])
			riga("e", "comando ignoto: %s", resto);
	}
}

int main(int argc, char **argv)
{
	int i;

	metro.nodo = PW_ID_ANY;
	metro.larghezza = 1920;
	metro.altezza = 1080;
	metro.cadenza = 60;

	for (i = 1; i < argc; i++)
	{
		if (strcmp(argv[i], "--nodo") == 0 && i + 1 < argc)
			metro.nodo = (uint32_t) strtoul(argv[++i], NULL, 10);
		else if (strcmp(argv[i], "--misura") == 0 && i + 1 < argc)
			sscanf(argv[++i], "%ux%u", &metro.larghezza, &metro.altezza);
		else if (strcmp(argv[i], "--cadenza") == 0 && i + 1 < argc)
			metro.cadenza = (uint32_t) strtoul(argv[++i], NULL, 10);
		else
		{
			fprintf(stderr, "uso: %s --nodo N [--misura LxA] [--cadenza N]\n", argv[0]);
			return 2;
		}
	}
	if (metro.nodo == PW_ID_ANY)
	{
		fprintf(stderr, "⛔ --nodo e' obbligatorio: non si indovina il flusso\n");
		return 2;
	}

	setvbuf(stdout, NULL, _IOLBF, 0);
	signal(SIGPIPE, SIG_IGN);
	pw_init(&argc, &argv);

	metro.ciclo = pw_main_loop_new(NULL);
	metro.contesto = pw_context_new(pw_main_loop_get_loop(metro.ciclo), NULL, 0);
	metro.nucleo = pw_context_connect(metro.contesto, NULL, 0);
	if (!metro.nucleo)
	{
		riga("e", "non mi collego a PipeWire: %s", strerror(errno));
		return 1;
	}
	metro.flusso = pw_stream_new(metro.nucleo, "03-b14-metro",
	                             pw_properties_new(PW_KEY_MEDIA_TYPE, "Video",
	                                               PW_KEY_MEDIA_CATEGORY, "Capture",
	                                               PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(metro.flusso, &metro.ascolto, &eventi, &metro);

	metro.sorgente_stdin = pw_loop_add_io(pw_main_loop_get_loop(metro.ciclo), STDIN_FILENO,
	                                      SPA_IO_IN, false, su_stdin, &metro);

	if (attacca(&metro) < 0)
	{
		riga("e", "pw_stream_connect fallita");
		return 1;
	}
	riga("m", "attaccato al nodo %u, chiesti %ux%u @ max %u", metro.nodo, metro.larghezza,
	     metro.altezza, metro.cadenza);

	pw_main_loop_run(metro.ciclo);

	pw_stream_destroy(metro.flusso);
	pw_core_disconnect(metro.nucleo);
	pw_context_destroy(metro.contesto);
	pw_main_loop_destroy(metro.ciclo);
	return 0;
}
