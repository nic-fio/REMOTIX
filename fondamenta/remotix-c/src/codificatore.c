#include "codificatore.h"

#include <freerdp/codec/color.h>
#include <freerdp/codec/region.h>

#include <libavcodec/avcodec.h>
#include <libavutil/hwcontext.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
#include <libswscale/swscale.h>

#include "registro.h"

/*
 * I candidati, in ordine di preferenza, e come si aprono.
 *
 * `dispositivo` dice se serve un contesto hardware di libavutil:
 *
 *   VA-API  lo pretende, e vuole i fotogrammi gia' su una superficie della
 *           scheda (AV_PIX_FMT_VAAPI): li si carica noi;
 *   QSV     lo gradisce ma accetta NV12 in memoria ordinaria, e fa il
 *           trasferimento per conto suo;
 *   NVENC   non lo vuole affatto: prende NV12 e basta;
 *   libx264 e' software e non c'entra niente con tutto questo.
 *
 * L'ordine mette VA-API per primo perche' e' la strada dell'integrata Intel,
 * che e' la scheda verso cui il progetto si e' orientato (§6.2 di
 * SPECIFICA.md).  Nessuna riga qui dentro e' specifica di un costruttore: si
 * cambia una stringa.
 */
static const struct
{
	const char *nome;
	enum AVHWDeviceType dispositivo;
	enum AVPixelFormat formato;
} CANDIDATI[] = {
	{ "h264_vaapi", AV_HWDEVICE_TYPE_VAAPI, AV_PIX_FMT_VAAPI },
	{ "h264_qsv", AV_HWDEVICE_TYPE_QSV, AV_PIX_FMT_NV12 },
	{ "h264_nvenc", AV_HWDEVICE_TYPE_NONE, AV_PIX_FMT_NV12 },
	{ "libx264", AV_HWDEVICE_TYPE_NONE, AV_PIX_FMT_NV12 },
};

struct Codificatore
{
	TipoCodificatore tipo;
	char *nome; /* quel che si scrive nel registro */
	gboolean in_gpu;

	/* ── percorso libavcodec ──────────────────────────────────────────── */
	AVCodecContext *ctx;
	AVBufferRef *dispositivo; /* contesto hardware, se serve */
	AVFrame *sw;              /* NV12 in memoria ordinaria */
	AVFrame *gpu;             /* superficie della scheda, solo VA-API */
	AVPacket *pacchetto;
	struct SwsContext *conversione; /* BGRx → NV12 */
	gboolean pacchetto_pieno;
	int64_t contatore;
	gboolean detto_in_ritardo;
	/* Vero quando i fotogrammi arrivano gia' dalla scheda, dal palco: allora non
	 * si converte e non si carica niente, si codifica e basta. */
	gboolean su_superfici;

	/*
	 * Il tempo speso davvero a codificare, e dove.
	 *
	 * Non e' strumentazione da banco che poi si toglie: senza questi tre numeri
	 * «il ritmo e' calato» non si puo' attribuire a niente — potrebbe essere il
	 * codificatore, la conversione di colore, il caricamento sulla scheda, il
	 * client o la rete.  Costa due letture dell'orologio per fotogramma.
	 */
	int64_t us_conversione;
	int64_t us_caricamento;
	int64_t us_codifica;
	int64_t fotogrammi_misurati;


	/* ── percorso FreeRDP ─────────────────────────────────────────────── */
	H264_CONTEXT *h264;
	gboolean metablock_da_liberare;

	/* La metablock.  Con libavcodec i due array sono NOSTRI e vivono quanto il
	 * codificatore: si riempiono a ogni fotogramma e non si liberano mai a
	 * meta' strada.  Con FreeRDP li alloca lui e si liberano con
	 * free_h264_metablock — le due cose non vanno mescolate. */
	RDPGFX_AVC420_BITMAP_STREAM avc420;
	RECTANGLE_16 rettangolo;
	RDPGFX_H264_QUANT_QUALITY qualita;

	PROGRESSIVE_CONTEXT *progressive;
};

/*
 * Il quantizzatore dichiarato nella metablock.
 *
 * E' informativo — dice al client quanto e' stato compresso quel rettangolo — e
 * non c'e' modo di farselo dire da libavcodec fotogramma per fotogramma senza
 * chiedere statistiche che non tutti i codificatori producono.  Si dichiara il
 * valore del riferimento, che dichiara anche lui una costante (§9.1 di
 * gnome-remote-desktop.md: QP 22, qualityVal 100).
 */
#define QP_DICHIARATO 22
#define QUALITA_DICHIARATA 100

static gboolean spedisci_e_ritira(Codificatore *cod, AVFrame *fotogramma,
                                  RDPGFX_SURFACE_COMMAND *cmd);

/* ------------------------------------------------------------------------ */
/* Apertura del percorso libavcodec                                          */
/* ------------------------------------------------------------------------ */

/*
 * Il contesto delle superfici VA-API.
 *
 * ⛔ IL NODO GIUSTO NON E' IL PRIMO.  Nella VM di runtime `/dev/dri/renderD128`
 *    e' virtio-gpu, che non codifica niente: `vainfo` senza argomenti risponde
 *    «init failed» e chi si fermasse li' concluderebbe che il passthrough non
 *    ha funzionato.  La scheda vera e' il nodo dopo.  Quindi non si sceglie: si
 *    provano tutti, e vale quello su cui il codificatore si APRE davvero —
 *    che e' anche l'unica prova che conti, perche' un nodo puo' inizializzare
 *    VA-API e non avere il motore di codifica.  [M, 6 agosto 2026]
 */
static gboolean apri_superfici_vaapi(Codificatore *cod, const char *nodo, uint32_t larghezza,
                                     uint32_t altezza)
{
	AVBufferRef *superfici;
	AVHWFramesContext *fc;

	if (av_hwdevice_ctx_create(&cod->dispositivo, AV_HWDEVICE_TYPE_VAAPI, nodo, NULL, 0) < 0)
		return FALSE;

	superfici = av_hwframe_ctx_alloc(cod->dispositivo);
	if (!superfici)
	{
		av_buffer_unref(&cod->dispositivo);
		return FALSE;
	}

	fc = (AVHWFramesContext *) superfici->data;
	fc->format = AV_PIX_FMT_VAAPI;
	fc->sw_format = AV_PIX_FMT_NV12;
	fc->width = (int) larghezza;
	fc->height = (int) altezza;
	/* Poche superfici bastano: si spedisce un fotogramma per giro e non se ne
	 * tengono in volo (il controllo di flusso e' altrove, in rete.c). */
	fc->initial_pool_size = 4;

	if (av_hwframe_ctx_init(superfici) < 0)
	{
		av_buffer_unref(&superfici);
		av_buffer_unref(&cod->dispositivo);
		return FALSE;
	}

	cod->ctx->hw_frames_ctx = av_buffer_ref(superfici);
	av_buffer_unref(&superfici);
	return cod->ctx->hw_frames_ctx != NULL;
}

static void applica_opzioni(Codificatore *cod, const char *nome)
{
	AVDictionary *opzioni = NULL;

	if (g_str_equal(nome, "libx264"))
	{
		/* `zerolatency` non e' una preferenza: senza, x264 tiene in canna
		 * qualche fotogramma prima di consegnare il primo, e in un desktop
		 * remoto quel ritardo si vede tutto. */
		av_dict_set(&opzioni, "preset", "veryfast", 0);
		av_dict_set(&opzioni, "tune", "zerolatency", 0);
	}
	else if (g_str_equal(nome, "h264_vaapi"))
	{
		/*
		 * ⛔ `low_power` SERVE, e non e' un risparmio energetico.  Le Intel
		 *    recenti offrono il solo entrypoint VDEnc: sulla scheda di questa
		 *    macchina `vainfo` elenca `VAProfileH264High : VAEntrypointEncSliceLP`
		 *    e nient'altro.  Chiedendo l'entrypoint classico la scheda risponde
		 *    «unsupported», il codificatore non si apre, e senza questa riga il
		 *    ripiego sarebbe silenzioso: si tornerebbe in CPU convinti di essere
		 *    in GPU.  [M, 6 agosto 2026]
		 */
		av_dict_set(&opzioni, "low_power", "1", 0);
		/* Un fotogramma per volta: la profondita' predefinita ne trattiene uno,
		 * e sarebbe un giro di ritardo su ogni battito del ciclo. */
		av_dict_set(&opzioni, "async_depth", "1", 0);
	}
	else if (g_str_equal(nome, "h264_nvenc"))
	{
		av_dict_set(&opzioni, "preset", "p4", 0);
		av_dict_set(&opzioni, "tune", "ll", 0); /* low latency */
		av_dict_set(&opzioni, "delay", "0", 0);
	}
	else if (g_str_equal(nome, "h264_qsv"))
	{
		av_dict_set(&opzioni, "preset", "veryfast", 0);
		av_dict_set(&opzioni, "async_depth", "1", 0);
	}

	if (opzioni)
	{
		av_opt_set_dict2(cod->ctx, &opzioni, AV_OPT_SEARCH_CHILDREN);
		av_dict_free(&opzioni);
	}
}

/*
 * Il contesto, allestito da zero.
 *
 * Sta in una funzione a se' perche' va rifatto DA CAPO a ogni tentativo: una
 * `avcodec_open2` fallita lascia il contesto in uno stato da cui non si
 * riprova, e con VA-API i tentativi sono tanti quanti i nodi di rendering.
 * Riusarlo sembrerebbe funzionare e fallirebbe piu' avanti, che e' il modo
 * peggiore.
 */
static gboolean prepara_contesto(Codificatore *cod, const AVCodec *codificatore, const char *nome,
                                 enum AVPixelFormat formato, uint32_t larghezza, uint32_t altezza,
                                 uint32_t bitrate_kbit, uint32_t fps)
{
	if (cod->ctx)
		avcodec_free_context(&cod->ctx);

	cod->ctx = avcodec_alloc_context3(codificatore);
	if (!cod->ctx)
		return FALSE;

	cod->ctx->width = (int) larghezza;
	cod->ctx->height = (int) altezza;
	cod->ctx->pix_fmt = formato;
	cod->ctx->time_base = (AVRational){ 1, (int) MAX(1u, fps) };
	cod->ctx->framerate = (AVRational){ (int) MAX(1u, fps), 1 };

	/*
	 * R11 — mai fotogrammi B, mai codifica di campo: cioe' Constrained High.
	 *
	 * Un fotogramma B costringe ad attendere il successivo, che in un desktop
	 * remoto e' un fotogramma di latenza in piu'; e il decodificatore software
	 * piu' diffuso su Android (OpenH264) rende Constrained Baseline e
	 * Constrained High e nient'altro.  CABAC e trasformata 8x8 invece restano
	 * accesi: sono dentro Constrained High e valgono 5-10 % di banda.
	 */
	cod->ctx->max_b_frames = 0;
	cod->ctx->has_b_frames = 0;
	cod->ctx->profile = AV_PROFILE_H264_HIGH;

	/*
	 * Il controllo del bitrate, che e' il motivo per cui §3.1 di SPECIFICA.md
	 * sceglie libavcodec: si dichiara un obiettivo invece di lasciare il
	 * quantizzatore costante come fa gnome-remote-desktop.  Il punto di lavoro
	 * vero — dove mettere quel numero — e' materia della fase 10.
	 */
	cod->ctx->bit_rate = (int64_t) bitrate_kbit * 1000;
	cod->ctx->rc_max_rate = cod->ctx->bit_rate;
	/* Un buffer da mezzo secondo: piu' corto strozza le scene difficili, piu'
	 * lungo lascia crescere il ritardo proprio quando la rete e' gia' in
	 * affanno. */
	cod->ctx->rc_buffer_size = (int) (cod->ctx->bit_rate / 2);

	/*
	 * Fotogrammi chiave radi, non frequenti.
	 *
	 * Su EGFX non servono per l'accesso casuale — non c'e' nessuno che «entra a
	 * meta' film»: chi si collega trova una superficie nuova e un codificatore
	 * nuovo, quindi un IDR.  Uno ogni dieci secondi e' solo la rete di
	 * sicurezza contro un errore di decodifica che si trascina.
	 */
	cod->ctx->gop_size = (int) MAX(1u, fps) * 10;

	/* ⛔ NIENTE `AV_CODEC_FLAG_GLOBAL_HEADER`: su RDP i parametri di sequenza
	 *    devono viaggiare NEL flusso, davanti all'IDR.  Metterli da parte
	 *    darebbe un flusso che il client riceve e non sa decodificare — e il
	 *    sintomo sarebbe schermo nero con i fotogrammi riscontrati, cioe' §8.1
	 *    n.2 di REFERENCE.md con una causa nuova. */

	applica_opzioni(cod, nome);
	return TRUE;
}

/* Apre un candidato per nome.  Restituisce FALSE senza lasciare niente dietro
 * di se': il chiamante prova il successivo. */
static gboolean apri_libav(Codificatore *cod, const char *nome, AVBufferRef *superfici,
                           uint32_t larghezza, uint32_t altezza, uint32_t bitrate_kbit,
                           uint32_t fps)
{
	const AVCodec *codificatore = avcodec_find_encoder_by_name(nome);
	enum AVPixelFormat formato = AV_PIX_FMT_NV12;
	enum AVHWDeviceType dispositivo = AV_HWDEVICE_TYPE_NONE;
	gsize i;

	if (!codificatore)
		return FALSE;

	for (i = 0; i < G_N_ELEMENTS(CANDIDATI); i++)
		if (g_str_equal(CANDIDATI[i].nome, nome))
		{
			formato = CANDIDATI[i].formato;
			dispositivo = CANDIDATI[i].dispositivo;
		}

	/*
	 * Il caso della cattura a copia zero: le superfici sono gia' fatte, e sono
	 * quelle del palco.  Non se ne allocano altre e non si sceglie alcun nodo —
	 * il dispositivo e' gia' deciso da chi le ha create, ed e' proprio questo
	 * che permette al fotogramma di non essere mai copiato.
	 */
	if (dispositivo == AV_HWDEVICE_TYPE_VAAPI && superfici)
	{
		AVHWFramesContext *fc = (AVHWFramesContext *) superfici->data;

		if (fc->width != (int) larghezza || fc->height != (int) altezza)
		{
			/*
			 * ⛔ SI RINUNCIA ALLE SUPERFICI, NON AL CODIFICATORE.
			 *
			 *    `return FALSE` qui vuol dire «questo nome non va», e chi chiama
			 *    passa al CANDIDATO SUCCESSIVO: da `h264_vaapi` si finiva su
			 *    `libx264`, cioe' in CPU, quando la scheda era li' e funzionava.
			 *    Misurato il 6 agosto ridimensionando a video in corso: un
			 *    ridimensionamento buttava la sessione dalla GPU alla CPU, e
			 *    l'avviso diceva «si torna al percorso in memoria» — vero per i
			 *    pixel, falso per il codificatore.
			 *
			 *    Le superfici del palco e il codificatore in GPU sono due cose
			 *    diverse: perdere le prime costa una copia per fotogramma,
			 *    perdere il secondo costa un core.
			 */
			avviso("le superfici del palco sono %dx%d ma il codificatore le vuole %ux%u: "
			       "resto su %s, ma i pixel torneranno a passare dalla memoria",
			       fc->width, fc->height, larghezza, altezza, nome);
			superfici = NULL;
			goto senza_superfici;
		}
		if (!prepara_contesto(cod, codificatore, nome, formato, larghezza, altezza, bitrate_kbit,
		                      fps))
			return FALSE;
		cod->ctx->hw_frames_ctx = av_buffer_ref(superfici);
		if (avcodec_open2(cod->ctx, codificatore, NULL) != 0)
		{
			avcodec_free_context(&cod->ctx);
			return FALSE;
		}
		cod->su_superfici = TRUE;
		cod->in_gpu = TRUE;
		cod->nome = g_strdup_printf("AVC420 via %s (in GPU, a copia zero)", nome);
		cod->pacchetto = av_packet_alloc();
		return cod->pacchetto != NULL;
	}

senza_superfici:
	if (dispositivo == AV_HWDEVICE_TYPE_VAAPI)
	{
		static const char *NODI[] = {
			"/dev/dri/renderD128", "/dev/dri/renderD129", "/dev/dri/renderD130",
			"/dev/dri/renderD131", "/dev/dri/renderD132",
		};
		gboolean aperto = FALSE;

		for (i = 0; i < G_N_ELEMENTS(NODI) && !aperto; i++)
		{
			if (!g_file_test(NODI[i], G_FILE_TEST_EXISTS))
				continue;
			if (!prepara_contesto(cod, codificatore, nome, formato, larghezza, altezza,
			                      bitrate_kbit, fps))
				return FALSE;
			if (!apri_superfici_vaapi(cod, NODI[i], larghezza, altezza))
				continue;
			if (avcodec_open2(cod->ctx, codificatore, NULL) == 0)
			{
				diagnostica("codificatore %s aperto su %s", nome, NODI[i]);
				aperto = TRUE;
			}
			else
			{
				av_buffer_unref(&cod->dispositivo);
			}
		}
		if (!aperto)
		{
			av_buffer_unref(&cod->dispositivo);
			avcodec_free_context(&cod->ctx);
			return FALSE;
		}
	}
	else
	{
		if (!prepara_contesto(cod, codificatore, nome, formato, larghezza, altezza, bitrate_kbit,
		                      fps))
			return FALSE;

		if (dispositivo != AV_HWDEVICE_TYPE_NONE &&
		    av_hwdevice_ctx_create(&cod->dispositivo, dispositivo, NULL, NULL, 0) >= 0)
			cod->ctx->hw_device_ctx = av_buffer_ref(cod->dispositivo);

		if (avcodec_open2(cod->ctx, codificatore, NULL) != 0)
		{
			av_buffer_unref(&cod->dispositivo);
			avcodec_free_context(&cod->ctx);
			return FALSE;
		}
	}

	/* Il fotogramma in memoria ordinaria: e' sempre NV12, anche quando poi si
	 * carica su una superficie della scheda. */
	cod->sw = av_frame_alloc();
	cod->pacchetto = av_packet_alloc();
	if (!cod->sw || !cod->pacchetto)
		goto guasto;
	cod->sw->format = AV_PIX_FMT_NV12;
	cod->sw->width = (int) larghezza;
	cod->sw->height = (int) altezza;
	if (av_frame_get_buffer(cod->sw, 32) < 0)
		goto guasto;

	if (formato == AV_PIX_FMT_VAAPI)
	{
		cod->gpu = av_frame_alloc();
		if (!cod->gpu)
			goto guasto;
	}

	/*
	 * BGRx → NV12.
	 *
	 * ⚠ E' l'unico pezzo che resta in CPU su un percorso «in GPU», e si vede nel
	 *   conto: la conversione di colore costa, molto meno della codifica ma non
	 *   nulla.  Toglierla e' il secondo passo della fase 9 — la cattura
	 *   zero-copy con DMA-BUF, che consegna il fotogramma gia' sulla scheda e
	 *   lascia fare la conversione a lei.
	 *
	 * SWS_POINT e non un filtro migliore perche' qui non si scala nulla: le
	 * misure coincidono, e ogni interpolazione sarebbe lavoro sprecato.
	 */
	/*
	 * ⛔ ED E' LEI IL COLLO DI BOTTIGLIA, non la codifica.
	 *
	 *    Misurato il 6 agosto 2026 sul banco della fase 9, con la GPU gia' in
	 *    funzione, su fotogrammi 2560x1024:
	 *
	 *        conversione  12,5 ms      ← qui
	 *        caricamento   3,1 ms
	 *        codifica      3,8 ms
	 *
	 *    Cioe' togliendo la codifica dalla CPU il tempo se lo prende il pezzo
	 *    rimasto: il consumo di CPU crolla e il RITMO cala, da 29 a 22,7
	 *    fotogrammi al secondo.  Un guadagno che si paga in fluidita' non e' un
	 *    guadagno, e questa riga e' il prossimo bersaglio della fase 9 — la
	 *    cattura zero-copy con DMA-BUF, che consegna il fotogramma gia' sulla
	 *    scheda e lascia la conversione a lei.
	 *
	 *    ⚠ PROVATO E SCARTATO: darle piu' thread (`sws_alloc_context` +
	 *      `threads`) non cambia niente — 13,8 ms contro 12,5, cioe' rumore.
	 *      Questa conversione non ha un percorso parallelo per BGRx → NV12, e
	 *      il tempo non e' di calcolo: e' di memoria.  Non si rifaccia.
	 *
	 *    SWS_POINT e non un filtro migliore perche' qui non si scala nulla: le
	 *    misure coincidono, e ogni interpolazione sarebbe lavoro sprecato.
	 */
	cod->conversione = sws_getContext((int) larghezza, (int) altezza, AV_PIX_FMT_BGR0,
	                                  (int) larghezza, (int) altezza, AV_PIX_FMT_NV12, SWS_POINT,
	                                  NULL, NULL, NULL);
	if (!cod->conversione)
		goto guasto;

	cod->in_gpu = (dispositivo != AV_HWDEVICE_TYPE_NONE) || g_str_has_suffix(nome, "_nvenc");
	cod->nome = g_strdup_printf("AVC420 via %s%s", nome, cod->in_gpu ? " (in GPU)" : " (in CPU)");
	return TRUE;

guasto:
	av_frame_free(&cod->sw);
	av_frame_free(&cod->gpu);
	av_packet_free(&cod->pacchetto);
	av_buffer_unref(&cod->dispositivo);
	avcodec_free_context(&cod->ctx);
	return FALSE;
}

/* Il vecchio percorso, tenuto come termine di paragone (--codificatore freerdp). */
static gboolean apri_freerdp(Codificatore *cod, uint32_t larghezza, uint32_t altezza,
                             uint32_t bitrate_kbit, uint32_t fps)
{
	UINT32 valore;

	cod->h264 = h264_context_new(TRUE);
	if (!cod->h264)
		return FALSE;

	valore = H264_SCREEN_CONTENT_REAL_TIME;
	h264_context_set_option(cod->h264, H264_CONTEXT_OPTION_USAGETYPE, valore);
	valore = H264_RATECONTROL_VBR;
	h264_context_set_option(cod->h264, H264_CONTEXT_OPTION_RATECONTROL, valore);
	valore = bitrate_kbit * 1000;
	h264_context_set_option(cod->h264, H264_CONTEXT_OPTION_BITRATE, valore);
	valore = fps;
	h264_context_set_option(cod->h264, H264_CONTEXT_OPTION_FRAMERATE, valore);

	if (!h264_context_reset(cod->h264, larghezza, altezza))
	{
		h264_context_free(cod->h264);
		cod->h264 = NULL;
		return FALSE;
	}

	cod->nome = g_strdup("AVC420 via FreeRDP (in CPU)");
	return TRUE;
}

Codificatore *codificatore_nuovo(TipoCodificatore tipo, const char *nome_chiesto,
                                 AVBufferRef *superfici, uint32_t larghezza_allineata,
                                 uint32_t altezza_allineata, uint32_t bitrate_kbit,
                                 uint32_t fotogrammi_al_secondo)
{
	Codificatore *cod = g_new0(Codificatore, 1);
	gboolean automatico = !nome_chiesto || !*nome_chiesto || g_str_equal(nome_chiesto, "auto");
	gsize i;

	cod->tipo = tipo;

	if (tipo == CODIFICATORE_PROGRESSIVE)
	{
		cod->progressive = progressive_context_new(TRUE);
		if (!cod->progressive || !progressive_context_reset(cod->progressive))
		{
			errore("nessun codificatore RemoteFX Progressive disponibile");
			g_clear_pointer(&cod->progressive, progressive_context_free);
			g_free(cod);
			return NULL;
		}
		cod->nome = g_strdup("RemoteFX Progressive (in CPU)");
		return cod;
	}

	/* La metablock: un rettangolo, il contenuto vero.  Gli array sono nostri e
	 * vivono quanto il codificatore. */
	cod->avc420.meta.numRegionRects = 1;
	cod->avc420.meta.regionRects = &cod->rettangolo;
	cod->avc420.meta.quantQualityVals = &cod->qualita;
	cod->qualita.qp = QP_DICHIARATO;
	cod->qualita.r = 0;
	cod->qualita.qualityVal = QUALITA_DICHIARATA;

	if (!automatico && g_str_equal(nome_chiesto, "freerdp"))
	{
		if (apri_freerdp(cod, larghezza_allineata, altezza_allineata, bitrate_kbit,
		                 fotogrammi_al_secondo))
			return cod;
		errore("il codificatore H.264 di FreeRDP non e' disponibile");
		g_free(cod);
		return NULL;
	}

	if (!automatico)
	{
		/* ⛔ CHIESTO PER NOME, NESSUN RIPIEGO.  Chi indica un codificatore sta
		 *    misurando: ripiegare su un altro darebbe due misure diverse con la
		 *    stessa etichetta, che e' peggio di non misurare. */
		if (apri_libav(cod, nome_chiesto, superfici, larghezza_allineata, altezza_allineata,
		               bitrate_kbit, fotogrammi_al_secondo))
		{
			informazione("codificatore: %s, come chiesto", cod->nome);
			return cod;
		}
		errore("il codificatore «%s» non si e' aperto, e non si ripiega su un altro: "
		       "era stato chiesto per nome",
		       nome_chiesto);
		g_free(cod);
		return NULL;
	}

	for (i = 0; i < G_N_ELEMENTS(CANDIDATI); i++)
	{
		if (apri_libav(cod, CANDIDATI[i].nome, superfici, larghezza_allineata, altezza_allineata,
		               bitrate_kbit, fotogrammi_al_secondo))
		{
			informazione("codificatore: %s", cod->nome);
			return cod;
		}
		diagnostica("codificatore %s non disponibile, provo il prossimo", CANDIDATI[i].nome);
	}

	/* Ultima spiaggia: il percorso di FreeRDP.  Se manca anche quello, la
	 * macchina non ha alcun modo di produrre H.264 e tacere sarebbe la cosa
	 * peggiore — il client vedrebbe nero senza che nessuno spieghi perche'. */
	if (apri_freerdp(cod, larghezza_allineata, altezza_allineata, bitrate_kbit,
	                 fotogrammi_al_secondo))
	{
		avviso("nessun codificatore di libavcodec disponibile: si usa quello di FreeRDP");
		return cod;
	}

	errore("nessun codificatore H.264 disponibile");
	g_free(cod);
	return NULL;
}

void codificatore_libera(Codificatore *cod)
{
	if (!cod)
		return;
	codificatore_rilascia(cod);

	if (cod->conversione)
		sws_freeContext(cod->conversione);
	av_frame_free(&cod->sw);
	av_frame_free(&cod->gpu);
	av_packet_free(&cod->pacchetto);
	if (cod->ctx)
		avcodec_free_context(&cod->ctx);
	av_buffer_unref(&cod->dispositivo);

	if (cod->h264)
		h264_context_free(cod->h264);
	if (cod->progressive)
		progressive_context_free(cod->progressive);
	g_free(cod->nome);
	g_free(cod);
}

const char *codificatore_nome(const Codificatore *cod)
{
	return cod->nome ? cod->nome : "sconosciuto";
}

gboolean codificatore_in_gpu(const Codificatore *cod)
{
	return cod->in_gpu;
}

/* ------------------------------------------------------------------------ */
/* Compressione                                                              */
/* ------------------------------------------------------------------------ */

static gboolean comprimi_libav(Codificatore *cod, const uint8_t *pixel, uint32_t passo,
                               uint32_t larghezza_allineata, uint32_t altezza_allineata,
                               RDPGFX_SURFACE_COMMAND *cmd)
{
	const uint8_t *piani[4] = { pixel, NULL, NULL, NULL };
	const int passi[4] = { (int) passo, 0, 0, 0 };
	AVFrame *da_spedire;

	if (av_frame_make_writable(cod->sw) < 0)
	{
		errore("il fotogramma NV12 non e' scrivibile");
		return FALSE;
	}

	int64_t t0 = g_get_monotonic_time(), t1, t2;

	sws_scale(cod->conversione, piani, passi, 0, (int) altezza_allineata, cod->sw->data,
	          cod->sw->linesize);
	cod->sw->pts = cod->contatore++;
	t1 = g_get_monotonic_time();

	if (cod->gpu)
	{
		av_frame_unref(cod->gpu);
		if (av_hwframe_get_buffer(cod->ctx->hw_frames_ctx, cod->gpu, 0) < 0)
		{
			errore("nessuna superficie libera sulla scheda");
			return FALSE;
		}
		if (av_hwframe_transfer_data(cod->gpu, cod->sw, 0) < 0)
		{
			errore("trasferimento del fotogramma sulla scheda fallito");
			return FALSE;
		}
		cod->gpu->pts = cod->sw->pts;
		da_spedire = cod->gpu;
	}
	else
	{
		da_spedire = cod->sw;
	}
	t2 = g_get_monotonic_time();

	/*
	 * Il codificatore puo' non avere ancora niente da dare, e non e' un guasto:
	 * il fotogramma esce al giro dopo, e il ciclo ne produce trenta al secondo.
	 */
	if (!spedisci_e_ritira(cod, da_spedire, cmd))
		return FALSE;

	cod->us_conversione += t1 - t0;
	cod->us_caricamento += t2 - t1;
	cod->us_codifica += g_get_monotonic_time() - t2;
	/*
	 * Ogni trecento fotogrammi — dieci secondi a ritmo pieno — si dice dove e'
	 * finito il tempo.  I tre numeri stanno accanto, non sommati: e' la
	 * differenza fra «codificare costa» e «costa il caricamento sulla scheda»,
	 * e sono due diagnosi opposte.
	 */
	if (++cod->fotogrammi_misurati >= 300)
	{
		diagnostica("tempo per fotogramma: conversione %.1f ms, caricamento %.1f ms, "
		            "codifica %.1f ms (media su %" G_GINT64_FORMAT ")",
		            cod->us_conversione / 1000.0 / cod->fotogrammi_misurati,
		            cod->us_caricamento / 1000.0 / cod->fotogrammi_misurati,
		            cod->us_codifica / 1000.0 / cod->fotogrammi_misurati,
		            cod->fotogrammi_misurati);
		cod->us_conversione = cod->us_caricamento = cod->us_codifica = 0;
		cod->fotogrammi_misurati = 0;
	}
	return TRUE;
}

gboolean codificatore_comprimi(Codificatore *cod, const uint8_t *pixel, uint32_t passo,
                               uint32_t larghezza_allineata, uint32_t altezza_allineata,
                               uint32_t larghezza, uint32_t altezza, RDPGFX_SURFACE_COMMAND *cmd)
{
	/* Bordi ESCLUSIVI, e sul contenuto vero: la superficie e' allineata, i
	 * rettangoli no.  Misurato sui byte il 4 agosto (R5). */
	RECTANGLE_16 regione = {
		.left = 0,
		.top = 0,
		.right = (UINT16) larghezza,
		.bottom = (UINT16) altezza,
	};

	cmd->left = 0;
	cmd->top = 0;
	cmd->right = larghezza;
	cmd->bottom = altezza;
	cmd->format = PIXEL_FORMAT_BGRX32;

	if (cod->tipo == CODIFICATORE_AVC420)
	{
		INT32 esito;

		cod->rettangolo = regione;

		if (cod->ctx)
			return comprimi_libav(cod, pixel, passo, larghezza_allineata, altezza_allineata, cmd);

		memset(&cod->avc420, 0, sizeof cod->avc420);
		esito = avc420_compress(cod->h264, pixel, cmd->format, passo, larghezza_allineata,
		                        altezza_allineata, &regione, &cod->avc420.data, &cod->avc420.length,
		                        &cod->avc420.meta);
		if (esito < 0)
		{
			errore("avc420_compress fallita");
			return FALSE;
		}
		cod->metablock_da_liberare = TRUE;
		if (esito == 0)
			return FALSE; /* niente di nuovo da mandare */

		cmd->codecId = RDPGFX_CODECID_AVC420;
		cmd->extra = &cod->avc420;
		return TRUE;
	}
	else
	{
		REGION16 regione16;
		INT32 esito;

		region16_init(&regione16);
		region16_union_rect(&regione16, &regione16, &regione);
		esito = progressive_compress(cod->progressive, pixel, passo * altezza_allineata,
		                             cmd->format, larghezza_allineata, altezza_allineata, passo,
		                             &regione16, &cmd->data, &cmd->length);
		region16_uninit(&regione16);

		if (esito < 0)
		{
			errore("progressive_compress fallita");
			return FALSE;
		}
		if (esito == 0)
			return FALSE;

		cmd->codecId = RDPGFX_CODECID_CAPROGRESSIVE;
		return TRUE;
	}
}

gboolean codificatore_su_superfici(const Codificatore *cod)
{
	return cod->su_superfici;
}

/* Il pezzo comune alle due `comprimi` del percorso libavcodec: si consegna un
 * fotogramma e si ritira un pacchetto.  Sta a parte perche' la differenza fra
 * le due e' tutta PRIMA di qui — e non deve diventare due copie della stessa
 * cosa che un giorno divergono. */
static gboolean spedisci_e_ritira(Codificatore *cod, AVFrame *fotogramma,
                                  RDPGFX_SURFACE_COMMAND *cmd)
{
	int esito = avcodec_send_frame(cod->ctx, fotogramma);

	if (esito < 0)
	{
		errore("avcodec_send_frame fallita (%d)", esito);
		return FALSE;
	}

	esito = avcodec_receive_packet(cod->ctx, cod->pacchetto);
	if (esito == AVERROR(EAGAIN))
	{
		if (!cod->detto_in_ritardo)
		{
			cod->detto_in_ritardo = TRUE;
			diagnostica("il codificatore trattiene il primo fotogramma: esce al giro dopo");
		}
		return FALSE;
	}
	if (esito < 0)
	{
		errore("avcodec_receive_packet fallita (%d)", esito);
		return FALSE;
	}

	cod->pacchetto_pieno = TRUE;
	cod->qualita.p = (cod->pacchetto->flags & AV_PKT_FLAG_KEY) ? 0 : 1;
	cod->avc420.data = cod->pacchetto->data;
	cod->avc420.length = (UINT32) cod->pacchetto->size;

	cmd->codecId = RDPGFX_CODECID_AVC420;
	cmd->extra = &cod->avc420;
	return TRUE;
}

gboolean codificatore_comprimi_superficie(Codificatore *cod, AVFrame *superficie,
                                          uint32_t larghezza, uint32_t altezza,
                                          RDPGFX_SURFACE_COMMAND *cmd)
{
	int64_t t0 = g_get_monotonic_time();

	/* Bordi ESCLUSIVI, sul contenuto vero e non sulla superficie (R5): la
	 * superficie e' allineata, il desktop no. */
	cod->rettangolo.left = 0;
	cod->rettangolo.top = 0;
	cod->rettangolo.right = (UINT16) larghezza;
	cod->rettangolo.bottom = (UINT16) altezza;

	cmd->left = 0;
	cmd->top = 0;
	cmd->right = larghezza;
	cmd->bottom = altezza;
	cmd->format = PIXEL_FORMAT_BGRX32;

	superficie->pts = cod->contatore++;
	if (!spedisci_e_ritira(cod, superficie, cmd))
		return FALSE;

	/* Lo stesso conto di prima, con le prime due voci a zero: e' il modo di far
	 * vedere nel registro che sono sparite, invece di far sparire la riga. */
	cod->us_codifica += g_get_monotonic_time() - t0;
	if (++cod->fotogrammi_misurati >= 300)
	{
		diagnostica("tempo per fotogramma: conversione 0.0 ms (sulla scheda), caricamento 0.0 ms "
		            "(niente da caricare), codifica %.1f ms (media su %" G_GINT64_FORMAT ")",
		            cod->us_codifica / 1000.0 / cod->fotogrammi_misurati, cod->fotogrammi_misurati);
		cod->us_conversione = cod->us_caricamento = cod->us_codifica = 0;
		cod->fotogrammi_misurati = 0;
	}
	return TRUE;
}

uint32_t codificatore_byte(const Codificatore *cod, const RDPGFX_SURFACE_COMMAND *cmd)
{
	if (cod->tipo != CODIFICATORE_AVC420)
		return cmd->length;

	/*
	 * Il conto della metablock, come lo fa il riferimento: quattro byte per il
	 * numero di rettangoli, dieci per ciascun rettangolo e uno per ciascun
	 * valore di quantizzazione, piu' il flusso H.264 vero.  Non serve che sia
	 * esatto al byte — serve a decidere se il fotogramma supera i 10 KB.
	 */
	return 4 + cod->avc420.meta.numRegionRects * 11 + cod->avc420.length;
}

void codificatore_rilascia(Codificatore *cod)
{
	if (cod->metablock_da_liberare)
	{
		free_h264_metablock(&cod->avc420.meta);
		cod->metablock_da_liberare = FALSE;
		/* Gli array tornano a essere i nostri: il percorso di FreeRDP li ha
		 * sostituiti con i suoi, e lasciarli penzolare significherebbe che il
		 * giro dopo si scrive dentro memoria appena liberata. */
		cod->avc420.meta.numRegionRects = 1;
		cod->avc420.meta.regionRects = &cod->rettangolo;
		cod->avc420.meta.quantQualityVals = &cod->qualita;
	}
	if (cod->pacchetto_pieno)
	{
		av_packet_unref(cod->pacchetto);
		cod->pacchetto_pieno = FALSE;
	}
}
