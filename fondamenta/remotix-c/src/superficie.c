#include "superficie.h"

#include <drm_fourcc.h>
#include <unistd.h>
#include <libavfilter/buffersink.h>
#include <libavfilter/buffersrc.h>
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_drm.h>
#include <libavutil/hwcontext_vaapi.h>
#include <libavutil/error.h>
#include <libavutil/opt.h>

#include "registro.h"

struct Superficie
{
	uint32_t larghezza, altezza;
	uint32_t larghezza_allineata, altezza_allineata;

	AVBufferRef *drm;   /* la scheda vista come dispositivo DRM: importa i DMA-BUF */
	AVBufferRef *vaapi; /* la stessa scheda vista da VA-API: converte e codifica  */

	AVBufferRef *superfici_drm; /* i fotogrammi come li consegna il kernel: DMA-BUF */

	AVFilterGraph *grafo;
	AVFilterContext *sorgente_desktop;
	AVFilterContext *uscita;

	AVFrame *importato;

	/* ------------------------------------------------------------------ *
	 * L'ACCUMULO, e perche' esiste.  [M, 7 agosto 2026 — R29]
	 *
	 * ⛔ IL BUFFER CHE MUTTER PRESTA NON E' UN FOTOGRAMMA: E' UN «DIFF».
	 *
	 *    Il compositore ricicla quattro buffer e vi ridipinge dentro SOLO la
	 *    regione cambiata — misurato: 282 fotogrammi su 300.  Fuori da quella
	 *    regione ci sono i pixel del fotogramma che aveva usato quel buffer
	 *    prima.  Prendendolo per intero si consegna una schermata gia' passata,
	 *    intera e pulita: il difetto che l'utente vedeva come «lampeggio».
	 *
	 *    In memoria non succede perche' li' Mutter ricopia ogni volta tutto il
	 *    fotogramma — ed e' la ragione per cui il difetto e' nato con la copia
	 *    zero: la copia che si e' tolta era anche l'unica cosa che ci
	 *    sincronizzava, per caso.
	 *
	 * Quindi: si tiene una superficie di ACCUMULO, sempre completa, e a ogni
	 * fotogramma vi si depongono le sole regioni danneggiate.  Si codifica da
	 * una COPIA dell'accumulo, non dall'accumulo stesso: la superficie di
	 * partenza continua a cambiare, e il codificatore la tiene fra i propri
	 * reference frame — riscrivergliela sotto farebbe riapparire i fotogrammi
	 * vecchi da un'altra strada.
	 * ------------------------------------------------------------------ */
	VADisplay schermo;   /* la stessa scheda, vista da VA-API */
	VAConfigID vpp_conf;
	VAContextID vpp;
	AVBufferRef *superfici_uscita; /* le NOSTRE superfici NV12 allineate */
	AVFrame *accumulo;
	gboolean accumulo_valido;
	/*
	 * ⛔ SPENTO DI SUO, e il perche' e' una misura. [7 agosto 2026]
	 *
	 *    L'accumulo e' la risposta GIUSTA alla diagnosi di R29 — il buffer di
	 *    Mutter e' un «diff» — ma acceso ha reso il difetto PEGGIORE su mstsc.
	 *    Quindi la diagnosi regge e questa attuazione no: manca ancora qualcosa
	 *    (la sincronizzazione esplicita e' il primo sospetto, vedi R29).
	 *
	 *    Si accende con `REMOTIX_ACCUMULO=1`, e serve a chi riprendera' la
	 *    caccia: cosi' le due strade si confrontano senza ricompilare.
	 */
	gboolean accumula;

	int64_t contatore;
	gboolean detto_guasto;
	gboolean detto_muto;
	gboolean detto_vpp;
};

/*
 * Copia una REGIONE da una superficie all'altra, sulla scheda.
 *
 * ⛔ NON LO SA FARE LIBAVFILTER: i suoi filtri lavorano sul fotogramma intero,
 *    e qui serve deporre un rettangolo dentro una superficie che conserva tutto
 *    il resto.  Si scende quindi a VA-API, che e' esattamente quel che il
 *    filtro usa sotto: una passata di `VideoProc` con regione di origine e
 *    regione di destinazione.
 *
 * ⚠ I RETTANGOLI VANNO ALLINEATI AI PARI.  La destinazione e' NV12, dove la
 *   crominanza vale per due pixel: un rettangolo dispari fa deporre la
 *   crominanza mezzo pixel piu' in la', e il difetto si vede come una frangia
 *   colorata sul bordo della regione — non come un errore.
 */
static gboolean vpp_copia(Superficie *sup, AVFrame *da, const VARectangle *sorgente, AVFrame *a,
                          const VARectangle *destinazione)
{
	VAProcPipelineParameterBuffer parametri = { 0 };
	VABufferID buffer = VA_INVALID_ID;
	VAStatus esito;

	parametri.surface = (VASurfaceID) (uintptr_t) da->data[3];
	parametri.surface_region = sorgente;
	parametri.output_region = destinazione;
	parametri.filter_flags = VA_FRAME_PICTURE;

	esito = vaBeginPicture(sup->schermo, sup->vpp, (VASurfaceID) (uintptr_t) a->data[3]);
	if (esito != VA_STATUS_SUCCESS)
		goto guasto;
	esito = vaCreateBuffer(sup->schermo, sup->vpp, VAProcPipelineParameterBufferType,
	                       sizeof parametri, 1, &parametri, &buffer);
	if (esito == VA_STATUS_SUCCESS)
		esito = vaRenderPicture(sup->schermo, sup->vpp, &buffer, 1);
	vaEndPicture(sup->schermo, sup->vpp);
	if (buffer != VA_INVALID_ID)
		vaDestroyBuffer(sup->schermo, buffer);
	if (esito == VA_STATUS_SUCCESS)
		return TRUE;

guasto:
	/* Si dice una volta sola: gira sul thread di tempo reale, e una riga per
	 * fotogramma sarebbe peggio del difetto. */
	if (!sup->detto_vpp)
	{
		sup->detto_vpp = TRUE;
		errore("la copia di regione sulla scheda e' fallita: %s", vaErrorStr(esito));
	}
	return FALSE;
}

/* Il rettangolo, ritagliato dentro il fotogramma e allineato ai pari. */
static gboolean rettangolo_sano(const SuperficieRegione *regione, uint32_t larghezza,
                                uint32_t altezza, VARectangle *fuori)
{
	uint32_t x = regione->x & ~1u;
	uint32_t y = regione->y & ~1u;
	uint32_t w, h;

	if (x >= larghezza || y >= altezza)
		return FALSE;
	w = MIN(regione->larghezza + (regione->x - x), larghezza - x);
	h = MIN(regione->altezza + (regione->y - y), altezza - y);
	w = MIN((w + 1u) & ~1u, larghezza - x);
	h = MIN((h + 1u) & ~1u, altezza - y);
	if (w == 0 || h == 0)
		return FALSE;

	fuori->x = (int16_t) x;
	fuori->y = (int16_t) y;
	fuori->width = (uint16_t) w;
	fuori->height = (uint16_t) h;
	return TRUE;
}

/*
 * Il nodo di rendering su cui aprire tutto.
 *
 * ⛔ NON E' DETTO CHE SIA IL PRIMO: e' la stessa trappola di R27, e qui morde
 *    allo stesso modo.  Si prova finche' uno non regge, e vale quello su cui la
 *    catena si apre davvero.
 */
static const char *NODI[] = {
	"/dev/dri/renderD128", "/dev/dri/renderD129", "/dev/dri/renderD130",
	"/dev/dri/renderD131", "/dev/dri/renderD132",
};

static gboolean apri_dispositivi(Superficie *sup, const char *nodo)
{
	if (av_hwdevice_ctx_create(&sup->drm, AV_HWDEVICE_TYPE_DRM, nodo, NULL, 0) < 0)
		return FALSE;

	/*
	 * La stessa scheda, vista da VA-API.  «Derivata» e non aperta di nuovo: cosi'
	 * le due viste condividono il dispositivo, ed e' la condizione perche' un
	 * fotogramma importato dall'una sia usabile dall'altra senza copiarlo.
	 */
	if (av_hwdevice_ctx_create_derived(&sup->vaapi, AV_HWDEVICE_TYPE_VAAPI, sup->drm, 0) < 0)
	{
		av_buffer_unref(&sup->drm);
		return FALSE;
	}
	return TRUE;
}

static AVBufferRef *contesto_superfici(AVBufferRef *dispositivo, enum AVPixelFormat formato,
                                       enum AVPixelFormat formato_software, uint32_t larghezza,
                                       uint32_t altezza, int pool)
{
	AVBufferRef *ref = av_hwframe_ctx_alloc(dispositivo);
	AVHWFramesContext *fc;

	if (!ref)
		return NULL;
	fc = (AVHWFramesContext *) ref->data;
	fc->format = formato;
	fc->sw_format = formato_software;
	fc->width = (int) larghezza;
	fc->height = (int) altezza;
	fc->initial_pool_size = pool;
	if (av_hwframe_ctx_init(ref) < 0)
	{
		av_buffer_unref(&ref);
		return NULL;
	}
	return ref;
}

/*
 * Apre quel che serve all'accumulo: il motore di copia della scheda, le NOSTRE
 * superfici di uscita e la superficie che accumula.
 *
 * ⛔ LE SUPERFICI DI USCITA DIVENTANO LE NOSTRE, non quelle del grafo.  Il
 *    codificatore si apre sul contesto che `superficie_contesto` restituisce
 *    (R30), e da qui in avanti i fotogrammi che gli consegniamo nascono qui:
 *    tenerne due sorgenti significherebbe che il codificatore accetta gli uni e
 *    rifiuta gli altri con «invalid argument», che e' l'unico sintomo.
 */
static gboolean apri_accumulo(Superficie *sup)
{
	AVHWDeviceContext *dispositivo = (AVHWDeviceContext *) sup->vaapi->data;
	AVVAAPIDeviceContext *va = dispositivo->hwctx;
	VAStatus esito;
	const char *acceso = g_getenv("REMOTIX_ACCUMULO");

	sup->accumula = acceso && *acceso == '1';
	if (!sup->accumula)
		return TRUE; /* strada di sempre: il buffer si consegna com'e' */
	informazione("accumulo delle regioni danneggiate ACCESO (REMOTIX_ACCUMULO=1)");

	sup->schermo = va->display;

	esito = vaCreateConfig(sup->schermo, VAProfileNone, VAEntrypointVideoProc, NULL, 0,
	                       &sup->vpp_conf);
	if (esito != VA_STATUS_SUCCESS)
	{
		informazione("questa scheda non sa copiare regioni (%s): niente copia zero",
		             vaErrorStr(esito));
		return FALSE;
	}
	esito = vaCreateContext(sup->schermo, sup->vpp_conf, (int) sup->larghezza_allineata,
	                        (int) sup->altezza_allineata, VA_PROGRESSIVE, NULL, 0, &sup->vpp);
	if (esito != VA_STATUS_SUCCESS)
	{
		informazione("motore di copia non aperto (%s): niente copia zero", vaErrorStr(esito));
		return FALSE;
	}

	/* Il pool: uno per l'accumulo, uno per il fotogramma in consegna, e il resto
	 * di margine perche' il codificatore ne tiene qualcuno fra i reference
	 * frame.  Stringerlo troppo non da' un errore: da' fotogrammi vecchi. */
	sup->superfici_uscita =
	    contesto_superfici(sup->vaapi, AV_PIX_FMT_VAAPI, AV_PIX_FMT_NV12,
	                       sup->larghezza_allineata, sup->altezza_allineata, 16);
	if (!sup->superfici_uscita)
		return FALSE;

	sup->accumulo = av_frame_alloc();
	if (!sup->accumulo || av_hwframe_get_buffer(sup->superfici_uscita, sup->accumulo, 0) < 0)
		return FALSE;
	sup->accumulo_valido = FALSE;
	return TRUE;
}

static gboolean costruisci_grafo(Superficie *sup)
{
	AVBufferSrcParameters *par = NULL;
	AVFilterContext *scala = NULL;
	AVFilterContext *bordo = NULL;
	AVFilterContext *mappatura = NULL;
	AVFilterContext *ultimo = NULL;
	const AVFilter *buffersrc = avfilter_get_by_name("buffer");
	const AVFilter *buffersink = avfilter_get_by_name("buffersink");
	const AVFilter *scale = avfilter_get_by_name("scale_vaapi");
	const AVFilter *pad = avfilter_get_by_name("pad_vaapi");
	const AVFilter *hwmap = avfilter_get_by_name("hwmap");
	gboolean serve_bordo = sup->larghezza_allineata != sup->larghezza ||
	                       sup->altezza_allineata != sup->altezza;
	char argomenti[256];
	gboolean esito = FALSE;

	if (!buffersrc || !buffersink || !scale || !hwmap)
	{
		avviso("questa libavfilter non ha «scale_vaapi» o «hwmap»: niente cattura a copia zero");
		return FALSE;
	}
	if (serve_bordo && !pad)
	{
		avviso("questa libavfilter non ha «pad_vaapi»: niente cattura a copia zero per %ux%u",
		       sup->larghezza, sup->altezza);
		return FALSE;
	}

	sup->grafo = avfilter_graph_alloc();
	if (!sup->grafo)
		goto fine;

	/*
	 * ⛔ IL DESKTOP ENTRA COME DMA-BUF, e a portarlo sulla scheda ci pensa
	 *    `hwmap`.
	 *
	 *    Mapparlo a mano con `av_hwframe_map` sembra la strada diretta e non lo
	 *    e': rifiuta con «invalid argument» e senza una riga di spiegazione, e
	 *    il 6 agosto e' costato tre giri di prove con tre codici d'errore
	 *    diversi.  `hwmap` e' la strada che percorre ffmpeg stesso quando gli si
	 *    scrive `-vf hwmap=derive_device=vaapi`, ed e' quella che funziona.
	 */
	g_snprintf(argomenti, sizeof argomenti,
	           "video_size=%ux%u:pix_fmt=%d:time_base=1/1000000:pixel_aspect=1/1", sup->larghezza,
	           sup->altezza, AV_PIX_FMT_DRM_PRIME);
	if (avfilter_graph_create_filter(&sup->sorgente_desktop, buffersrc, "desktop", argomenti, NULL,
	                                 sup->grafo) < 0)
		goto fine;
	par = av_buffersrc_parameters_alloc();
	par->hw_frames_ctx = sup->superfici_drm;
	if (av_buffersrc_parameters_set(sup->sorgente_desktop, par) < 0)
		goto fine;
	av_freep(&par);

	/*
	 * ⛔ IL DISPOSITIVO SI DA' AL FILTRO, non al grafo: `AVFilterGraph` non ha un
	 *    campo per questo, e il filtro va quindi allocato, dotato del
	 *    dispositivo e solo dopo inizializzato.  Con `avfilter_graph_create_filter`
	 *    — che alloca e inizializza insieme — non c'e' il momento in cui
	 *    infilarlo, e `hwmap` non saprebbe su quale scheda portare il fotogramma.
	 *
	 *    E dandogli il dispositivo, `derive_device` non serve: la scheda e' gia'
	 *    quella, ed e' la stessa dello sfondo.
	 */
	mappatura = avfilter_graph_alloc_filter(sup->grafo, hwmap, "sulla-scheda");
	if (!mappatura)
		goto fine;
	mappatura->hw_device_ctx = av_buffer_ref(sup->vaapi);
	if (avfilter_init_str(mappatura, NULL) < 0)
		goto fine;
	if (avfilter_link(sup->sorgente_desktop, 0, mappatura, 0) < 0)
		goto fine;
	ultimo = mappatura;

	/*
	 * ⛔ LA CONVERSIONE DI COLORE VA CHIESTA, e prima si otteneva per sbaglio.
	 *
	 *    Il desktop arriva BGRx; il codificatore vuole NV12.  Nella prima
	 *    stesura la conversione la faceva `overlay_vaapi` come effetto
	 *    collaterale — l'uscita di una sovrapposizione prende il formato dello
	 *    SFONDO, che era NV12 — cioe' la si otteneva senza chiederla.  Tolto lo
	 *    sfondo, va chiesta: `scale_vaapi` senza misure cambia il solo formato.
	 */
	g_snprintf(argomenti, sizeof argomenti, "format=nv12");
	if (avfilter_graph_create_filter(&scala, scale, "in-nv12", argomenti, NULL, sup->grafo) < 0)
		goto fine;
	if (avfilter_link(ultimo, 0, scala, 0) < 0)
		goto fine;
	ultimo = scala;

	/*
	 * Il bordo di R4, e SOLO se serve.
	 *
	 * `pad_vaapi` depone l'immagine dentro una superficie piu' grande e riempie
	 * il resto di nero: e' esattamente quel che R4 chiede — «il bordo in eccesso
	 * si riempie, non si riduce lo schermo».  Quando la misura e' gia' allineata
	 * — 1024x768, per dire — non si aggiunge nulla al grafo: un passaggio in
	 * meno sulla scheda, e un filtro in meno che possa sbagliare.
	 */
	if (serve_bordo)
	{
		g_snprintf(argomenti, sizeof argomenti, "w=%u:h=%u:x=0:y=0:color=black",
		           sup->larghezza_allineata, sup->altezza_allineata);
		if (avfilter_graph_create_filter(&bordo, pad, "bordo", argomenti, NULL, sup->grafo) < 0)
			goto fine;
		if (avfilter_link(ultimo, 0, bordo, 0) < 0)
			goto fine;
		ultimo = bordo;
	}

	if (avfilter_graph_create_filter(&sup->uscita, buffersink, "uscita", NULL, NULL, sup->grafo) < 0)
		goto fine;
	if (avfilter_link(ultimo, 0, sup->uscita, 0) < 0)
		goto fine;

	if (avfilter_graph_config(sup->grafo, NULL) < 0)
	{
		avviso("la scheda non sa portare il fotogramma alla misura allineata");
		goto fine;
	}

	esito = TRUE;

fine:
	av_freep(&par);
	if (!esito && sup->grafo)
		avfilter_graph_free(&sup->grafo);
	return esito;
}

Superficie *superficie_nuova(uint32_t larghezza, uint32_t altezza, uint32_t larghezza_allineata,
                             uint32_t altezza_allineata)
{
	Superficie *sup = g_new0(Superficie, 1);
	gsize i;

	sup->larghezza = larghezza;
	sup->altezza = altezza;
	sup->larghezza_allineata = larghezza_allineata;
	sup->altezza_allineata = altezza_allineata;

	for (i = 0; i < G_N_ELEMENTS(NODI); i++)
	{
		if (!g_file_test(NODI[i], G_FILE_TEST_EXISTS))
			continue;
		if (!apri_dispositivi(sup, NODI[i]))
			continue;

		/* I fotogrammi in ingresso: quelli che il kernel consegna, descritti come
		 * DMA-BUF.  Nessuna superficie viene allocata — il contesto serve solo a
		 * dire al grafo che forma hanno. */
		sup->superfici_drm = contesto_superfici(sup->drm, AV_PIX_FMT_DRM_PRIME, AV_PIX_FMT_BGR0,
		                                        larghezza, altezza, 0);
		if (sup->superfici_drm && costruisci_grafo(sup) && apri_accumulo(sup))
		{
			sup->importato = av_frame_alloc();
			if (sup->importato)
			{
				informazione("cattura a copia zero pronta su %s: %ux%u → superficie %ux%u",
				             NODI[i], larghezza, altezza, larghezza_allineata, altezza_allineata);
				return sup;
			}
		}

		/* Non ha retto: si smonta tutto e si prova il nodo dopo. */
		if (sup->grafo)
			avfilter_graph_free(&sup->grafo);
		av_buffer_unref(&sup->superfici_drm);
		av_buffer_unref(&sup->vaapi);
		av_buffer_unref(&sup->drm);
	}

	diagnostica("nessuna scheda sa importare i DMA-BUF: si resta sul percorso in CPU");
	g_free(sup);
	return NULL;
}

void superficie_libera(Superficie *sup)
{
	if (!sup)
		return;
	av_frame_free(&sup->importato);
	av_frame_free(&sup->accumulo);
	av_buffer_unref(&sup->superfici_uscita);
	if (sup->schermo)
	{
		if (sup->vpp)
			vaDestroyContext(sup->schermo, sup->vpp);
		if (sup->vpp_conf)
			vaDestroyConfig(sup->schermo, sup->vpp_conf);
	}
	if (sup->grafo)
		avfilter_graph_free(&sup->grafo);
	av_buffer_unref(&sup->superfici_drm);
	av_buffer_unref(&sup->vaapi);
	av_buffer_unref(&sup->drm);
	g_free(sup);
}

AVBufferRef *superficie_contesto(Superficie *sup)
{
	/* Con l'accumulo acceso i fotogrammi nascono dalle NOSTRE superfici, e il
	 * codificatore va aperto su quelle (R30); spento, restano quelle del grafo. */
	return sup->accumula ? sup->superfici_uscita : av_buffersink_get_hw_frames_ctx(sup->uscita);
}

void superficie_misura(const Superficie *sup, uint32_t *larghezza_allineata,
                       uint32_t *altezza_allineata)
{
	*larghezza_allineata = sup->larghezza_allineata;
	*altezza_allineata = sup->altezza_allineata;
}

AVFrame *superficie_importa(Superficie *sup, int fd, uint32_t offset, uint32_t passo,
                            uint64_t modificatore, uint32_t larghezza, uint32_t altezza,
                            const SuperficieRegione *danno, guint quante)
{
	AVFrame *convertito;
	AVFrame *fuori;
	int esito;

	if (larghezza != sup->larghezza || altezza != sup->altezza)
	{
		/* La misura e' cambiata sotto i piedi: il grafo e' costruito su quella di
		 * prima e non si adatta.  Chi chiama rifara' il convertitore. */
		return NULL;
	}

	/*
	 * Il descrittore: un oggetto, un piano.  E' la forma che Mutter consegna —
	 * BGRx lineare — e non si indovina, la si legge dal formato negoziato.
	 *
	 * ⛔ E VA DENTRO UN RIFERIMENTO SUO, non in un campo del convertitore.
	 *
	 *    Un fotogramma che il grafo riceve dev'essere contato per riferimenti:
	 *    se non lo e', libavfilter prova a COPIARLO, e per un fotogramma che
	 *    vive sulla scheda non ha dove — risponde «Cannot allocate memory», che
	 *    e' l'ultimo posto in cui si andrebbe a cercare un problema di
	 *    proprieta'.  Costa un'allocazione da poche decine di byte per
	 *    fotogramma, e toglie di mezzo la domanda.  [M, 6 agosto 2026]
	 */
	{
		AVBufferRef *riferimento = av_buffer_allocz(sizeof(AVDRMFrameDescriptor));
		AVDRMFrameDescriptor *descrittore;
		off_t quanto;

		if (!riferimento)
			return NULL;
		descrittore = (AVDRMFrameDescriptor *) riferimento->data;

		descrittore->nb_objects = 1;
		descrittore->objects[0].fd = fd;
		/* La dimensione va dichiarata: il driver la usa per costruire la
		 * superficie, e con zero rifiuta senza nominare la causa.  La si chiede
		 * al descrittore di file — e' l'unico che sappia quanto e' stato
		 * allocato davvero, che qui e' piu' di `passo x altezza`. */
		quanto = lseek(fd, 0, SEEK_END);
		descrittore->objects[0].size = quanto > 0 ? (size_t) quanto : (size_t) passo * altezza;
		descrittore->objects[0].format_modifier = modificatore;
		descrittore->nb_layers = 1;
		descrittore->layers[0].format = DRM_FORMAT_XRGB8888;
		descrittore->layers[0].nb_planes = 1;
		descrittore->layers[0].planes[0].object_index = 0;
		descrittore->layers[0].planes[0].offset = offset;
		descrittore->layers[0].planes[0].pitch = passo;

		av_frame_unref(sup->importato);
		sup->importato->format = AV_PIX_FMT_DRM_PRIME;
		sup->importato->width = (int) larghezza;
		sup->importato->height = (int) altezza;
		sup->importato->buf[0] = riferimento;
		sup->importato->data[0] = riferimento->data;
		sup->importato->hw_frames_ctx = av_buffer_ref(sup->superfici_drm);
	}

	sup->contatore++;
	sup->importato->pts = sup->contatore;

	/*
	 * ⛔ IL DESKTOP INVECE SI CEDE, e non e' una scelta di stile.
	 *
	 *    `KEEP_REF` fa prendere al grafo un riferimento in piu', e prendere un
	 *    riferimento a un fotogramma pretende che sia contato per riferimenti.
	 *    Questo non lo e': e' un descrittore costruito a mano attorno a un
	 *    DMA-BUF che appartiene a PipeWire.  Chiedendo `KEEP_REF` il grafo lo
	 *    rifiuta — e il messaggio dice soltanto «non accettato».  Cedendolo, il
	 *    grafo lo prende per spostamento e non c'e' niente da contare.
	 *
	 *    Si puo' fare perche' il fotogramma si consegna e si ritira NELLO STESSO
	 *    respiro: il descrittore resta valido per tutto il tempo in cui serve.
	 *    [M, 6 agosto 2026]
	 */
	esito = av_buffersrc_add_frame_flags(sup->sorgente_desktop, sup->importato, 0);
	if (esito < 0)
	{
		if (!sup->detto_guasto)
		{
			char nome[AV_ERROR_MAX_STRING_SIZE] = { 0 };

			sup->detto_guasto = TRUE;
			av_strerror(esito, nome, sizeof nome);
			errore("il grafo non ha accettato il fotogramma catturato: %s (%d)", nome, esito);
			errore("  quel che le si e' passato: fd %d, scarto %u, passo %u, modificatore 0x%"
			       G_GINT64_MODIFIER "x, %ux%u → %ux%u",
			       fd, offset, passo, (guint64) modificatore, larghezza, altezza,
			       sup->larghezza_allineata, sup->altezza_allineata);
		}
		return NULL;
	}

	convertito = av_frame_alloc();
	if (!convertito)
		return NULL;

	/* ⛔ E QUI NON SI TACE.  Un grafo che non consegna nulla e' indistinguibile
	 *    da un desktop fermo: entrambi si presentano come «nessun fotogramma
	 *    nuovo».  Il 6 agosto e' costato mezz'ora di esperimenti di controllo
	 *    per scoprire che la scena si muoveva e i fotogrammi sparivano qui. */
	esito = av_buffersink_get_frame(sup->uscita, convertito);
	if (esito < 0)
	{
		if (!sup->detto_muto)
		{
			char nome[AV_ERROR_MAX_STRING_SIZE] = { 0 };

			sup->detto_muto = TRUE;
			av_strerror(esito, nome, sizeof nome);
			errore("il grafo ha preso il fotogramma e non ne ha reso nessuno: %s (%d)", nome,
			       esito);
		}
		av_frame_free(&convertito);
		return NULL;
	}

	if (!sup->accumula)
		return convertito;

	/*
	 * L'ACCUMULO (R29).  Quel che il grafo ha appena convertito e' il buffer di
	 * Mutter per intero — cioe' le regioni fresche PIU' quel che era rimasto nel
	 * buffer dal giro precedente.  Sull'accumulo si depongono le sole regioni
	 * fresche, e tutto il resto resta quel che era: completo e aggiornato.
	 */
	{
		VARectangle tutto = { 0, 0, (uint16_t) sup->larghezza_allineata,
			                  (uint16_t) sup->altezza_allineata };
		gboolean intero = !sup->accumulo_valido || quante == 0;
		guint fatte = 0;

		if (intero)
		{
			if (!vpp_copia(sup, convertito, &tutto, sup->accumulo, &tutto))
			{
				av_frame_free(&convertito);
				return NULL;
			}
			sup->accumulo_valido = TRUE;
		}
		else
		{
			for (guint i = 0; i < quante; i++)
			{
				VARectangle r;

				/* Le regioni sono in coordinate del FLUSSO, e la superficie ha il
				 * desktop all'angolo (0,0) senza scalature: coincidono.  Si
				 * ritagliano comunque sul desktop — non sulla superficie
				 * allineata — perche' oltre il desktop c'e' il bordo di R4, che
				 * e' nero e non va toccato. */
				if (!rettangolo_sano(&danno[i], sup->larghezza, sup->altezza, &r))
					continue;
				if (!vpp_copia(sup, convertito, &r, sup->accumulo, &r))
				{
					av_frame_free(&convertito);
					return NULL;
				}
				fatte++;
			}
			/* Nessuna regione valida: non e' cambiato niente di visibile, e
			 * l'accumulo va gia' bene com'e'. */
			(void) fatte;
		}
	}
	av_frame_free(&convertito);

	/*
	 * Si consegna una COPIA, non l'accumulo.  L'accumulo continua a cambiare a
	 * ogni fotogramma, e il codificatore tiene i propri ingressi fra i reference
	 * frame: dargli la superficie viva significherebbe riscrivergliela sotto —
	 * e i fotogrammi vecchi tornerebbero da un'altra strada.
	 */
	fuori = av_frame_alloc();
	if (!fuori)
		return NULL;
	if (av_hwframe_get_buffer(sup->superfici_uscita, fuori, 0) < 0)
	{
		av_frame_free(&fuori);
		return NULL;
	}
	{
		VARectangle tutto = { 0, 0, (uint16_t) sup->larghezza_allineata,
			                  (uint16_t) sup->altezza_allineata };

		if (!vpp_copia(sup, sup->accumulo, &tutto, fuori, &tutto))
		{
			av_frame_free(&fuori);
			return NULL;
		}
	}
	fuori->width = (int) sup->larghezza_allineata;
	fuori->height = (int) sup->altezza_allineata;
	return fuori;
}
