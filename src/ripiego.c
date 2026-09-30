/*
 * ripiego.c — la codifica in software senza ffmpeg.  Il perche' e la forma
 *             stanno in `ripiego.h`; qui le scelte, ognuna con la sua misura.
 *
 * ---------------------------------------------------------------------------
 * ⭐ CHE COSA RIPRODUCE DI `codificatore.c`, riga per riga del ramo software:
 *
 *   `opzioni_h264()`   bframes=0, open-gop=0, repeat-headers=1, rc-lookahead=0,
 *                      chiavi solo su richiesta (keyint -1), crf=N, livello
 *                      imposto  ⇒  OpenH264: niente B per costruzione (non li
 *                      sa fare), IDR con SPS+PPS davanti sempre, nessun
 *                      lookahead, `uiIntraPeriod` 0, QP costante (vedi sotto
 *                      il CRF), `uiLevelIdc`.
 *   `opzioni_av1()`    preset 10, pred-struct=1 (bassa latenza), crf=N, niente
 *                      senza-perdita  ⇒  SVT-AV1 diretta, gli stessi numeri.
 *   `opzioni_hevc()`   ⛔ x265 e' GPL: NON c'e' ripiego HEVC.  Rifiuto dichiarato.
 *   `apri_contesto()`  BT.709 a intervallo limitato DICHIARATO nel flusso (VUI
 *                      per H.264, color_config per AV1): `[M]` 21 agosto 2026
 *                      a 768x480 senza dichiarazione il decodificatore
 *                      hardware indovina BT.601 e sbaglia di 32,41 livelli.
 *   `prepara_fotogramma()`  sws_scale → `colori709.c`.
 */
#include "ripiego.h"
#include "colori709.h"
#include "registro.h"

#include <dlfcn.h>
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <wels/codec_api.h>
#include <wels/codec_ver.h>
#include <svt-av1/EbSvtAv1Enc.h>

#define REG_RIPIEGO "video"

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐ LE SCELTE DI OPENH264, e ognuna ha la sua riga nel banco
 *    (`banchi/18-software-confronto.c`, 30 settembre 2026, i5-13500T).
 *
 * ⛔ Sotto `RIPIEGO_BANCO` si leggono dall'ambiente, per il solo banco che le
 *    tara: il prodotto le ha FISSE, compilate, e il registro le stampa.
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Quanti fili.  ⚠ OpenH264 parallelizza per FETTE (slice), non per
 * fotogrammi: nessun fotogramma in canna, nessun ritardo in piu' — il prezzo e'
 * qualche byte (le fette non si predicono fra loro). */
#ifndef RIPIEGO_H264_FILI
#define RIPIEGO_H264_FILI 4
#endif
/* 1 = CABAC ⇒ il flusso e' Main/High; 0 = CAVLC ⇒ Constrained Baseline. */
#ifndef RIPIEGO_H264_CABAC
#define RIPIEGO_H264_CABAC 1
#endif
/* SCREEN_CONTENT_REAL_TIME (1) o CAMERA_VIDEO_REAL_TIME (0). */
#ifndef RIPIEGO_H264_USO
#define RIPIEGO_H264_USO 1
#endif
/* LOW_COMPLEXITY 0 · MEDIUM 1 · HIGH 2. */
#ifndef RIPIEGO_H264_COMPLESSITA
#define RIPIEGO_H264_COMPLESSITA 1
#endif
/* Il CRF di x264 non esiste in OpenH264: si traduce in un QP costante
 * spostato di questo delta (QP = CRF + delta).  ⇒ Il numero giusto e' quello
 * che da' la stessa qualita' di `libx264 crf=N` sulla stessa scena.
 * `[M]` 30 set 2026, 1920x1080, contro x264 CRF 20 «corretto» (SSIM 0,99743,
 * PSNR-Y 43,22 dB, 3,6 KiB per fotogramma):
 *     delta 0  SSIM 0,99843 · PSNR-Y 50,30 · 4,5 KiB
 *     delta 3  SSIM 0,99800 · PSNR-Y 47,87 · 4,0 KiB
 *   ⭐ delta 5  SSIM 0,99754 · PSNR-Y 46,30 · 3,7 KiB   ← la stessa SSIM
 *     delta 7  SSIM 0,99673 · PSNR-Y 44,16 · 3,4 KiB   ⛔ SSIM sotto
 *     delta 9  SSIM 0,99597 · PSNR-Y 42,52 · 2,9 KiB
 * ⇒ 5: il primo che non e' peggio di x264 in nessuna delle due misure. */
#ifndef RIPIEGO_H264_DELTA_QP
#define RIPIEGO_H264_DELTA_QP 5
#endif
/* Il profilo dichiarato: 100 (High, quel che dice la pagina: `avc1.6400LL`),
 * 77 (Main) o 66 (Baseline). */
#ifndef RIPIEGO_H264_PROFILO
#define RIPIEGO_H264_PROFILO 100
#endif

/* Il rilevatore di cambio scena.  ⚠ Sotto «contenuto schermo» OpenH264 lo
 * vuole acceso (`[M]` avvisa *«screen change detection should be turned on»*)
 * e lo usa per riconoscere lo scorrimento, non solo per mettere IDR. */
#ifndef RIPIEGO_H264_SCD
#define RIPIEGO_H264_SCD 1
#endif

/* SVT-AV1: il preset di `opzioni_av1()`. */
#ifndef RIPIEGO_AV1_PRESET
#define RIPIEGO_AV1_PRESET 10
#endif

/* Quanto si aspetta un pacchetto da SVT-AV1 prima di dichiararlo trattenuto.
 * ⚠ SVT lavora in una catena di fili: il pacchetto arriva DOPO la consegna del
 *   fotogramma, e si chiede finche' non c'e' (mai «subito o niente», che era la
 *   strada di libavcodec: vedi `ripiego_codifica()`). */
#define AV1_ATTESA_US (5u * 1000u * 1000u)

struct Ripiego {
	CodificatoreRichiesta r;
	ModoQualita modo;
	int qualita;

	/* I piani YUV dopo la conversione (8 o 10 bit). */
	uint8_t *piani;
	uint32_t passo_y, passo_c; /* in BYTE */

	uint8_t *uscita;
	size_t uscita_cap;
	int64_t numero;
	char nome[192];

	/* H.264 */
	ISVCEncoder *h264;
	SEncParamExt param_h264; /* i parametri in vigore: servono al cambio a caldo */
	int qp_h264;
	int fili_h264;

	/* AV1 */
	EbComponentType *av1;
};

static void di(char *dove, size_t quanto, const char *fmt, ...)
	__attribute__((format(printf, 3, 4)));
static void di(char *dove, size_t quanto, const char *fmt, ...)
{
	if (!dove || !quanto)
		return;
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(dove, quanto, fmt, ap);
	va_end(ap);
}

static uint64_t adesso_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000u + (uint64_t) t.tv_nsec / 1000u;
}

#ifdef RIPIEGO_BANCO
static int regola(const char *nome, int difetto)
{
	const char *v = getenv(nome);
	return v && *v ? atoi(v) : difetto;
}
#else
#define regola(nome, difetto) (difetto)
#endif

const char *ripiego_componente(CodecVideo codec)
{
	switch (codec) {
	case CODIFICATORE_H264:
		return "openh264";
	case CODIFICATORE_AV1:
		return "svt-av1";
	default:
		return NULL; /* ⛔ HEVC: non c'e' */
	}
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐ H.264 — OpenH264, APERTA con `dlopen` e non collegata
 *
 * ⛔ Perche' non si collega (fase 18, 30 set 2026, i fatti dell'agente
 *    dell'installatore):
 *    1. su Fedora (`noopenh264`), AlmaLinux (EPEL) e openSUSE (repo-oss) esiste
 *       una copia VUOTA di OpenH264 — stesso nome, 11-14 KB, non codifica — e
 *       il gestore dei pacchetti puo' sceglierla al posto di quella vera.
 *       Collegati, partiremmo lo stesso e scopriremmo il vuoto solo al primo
 *       fotogramma; aperti, lo si riconosce all'apertura e lo si DICE, e chi
 *       sceglie il codec passa ad AV1;
 *    2. col `dlopen` si puo' usare il binario di Cisco (quello scaricato da
 *       Firefox e GStreamer), l'unico coperto dalla licenza di brevetto di
 *       Cisco.  E' la stessa strada di Firefox e di GStreamer.
 *
 * ⚠ DUE ABI, e non e' un'ipotesi: `libopenh264.so.7` e' la 2.5.x (AlmaLinux 10)
 *   e `.so.8` la 2.6.0 (Debian, Ubuntu, openSUSE, Arch).  La 2.6.0 ha aggiunto
 *   `rPsnr[3]` in coda a `SLayerBSInfo` (e `bPsnr*` a `SEncParamExt` e
 *   `SSourcePicture`): i due ultimi la 2.5 li legge solo in parte e va bene,
 *   ma `SFrameBSInfo` lo SCRIVE lei — un array di 128 strati — e letto con la
 *   forma della 2.6 darebbe lo strato 1 (la IDR) ai byte sbagliati.  ⇒ La
 *   forma della 2.5 sta qui sotto, copiata dalle intestazioni v2.5.0 di Cisco,
 *   e si sceglie dalla VERSIONE che la libreria dichiara, non dal nome.
 * ⛔ Altre versioni si rifiutano dicendolo: una forma che non si e' guardata e'
 *    una forma che non si usa.
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct {
	unsigned char uiTemporalId, uiSpatialId, uiQualityId;
	EVideoFrameType eFrameType;
	unsigned char uiLayerType;
	int iSubSeqId;
	int iNalCount;
	int *pNalLengthInByte;
	unsigned char *pBsBuf;
} StratoV25; /* `SLayerBSInfo` della 2.5.x: senza `rPsnr[3]` */

typedef struct {
	int iLayerNum;
	StratoV25 sLayerInfo[MAX_LAYER_NUM_OF_FRAME];
	EVideoFrameType eFrameType;
	int iFrameSizeInBytes;
	long long uiTimeStamp;
} FotogrammaV25;

static struct Oh {
	bool provato, pronto;
	bool forma_26;               /* true = la forma delle intestazioni (2.6) */
	void *lib;
	int (*crea)(ISVCEncoder **);
	void (*distruggi)(ISVCEncoder *);
	OpenH264Version v;
	char quale[64];              /* il file aperto davvero */
	char perche[320];
	uint64_t us_carico;
} oh;

static bool openh264_carica(void)
{
	if (oh.provato)
		return oh.pronto;
	oh.provato = true;
	uint64_t t0 = adesso_us();
	static const char *nomi[] = { "libopenh264.so.8", "libopenh264.so.7" };
	for (size_t i = 0; i < sizeof nomi / sizeof *nomi && !oh.lib; i++) {
		oh.lib = dlopen(nomi[i], RTLD_NOW | RTLD_LOCAL);
		if (oh.lib)
			snprintf(oh.quale, sizeof oh.quale, "%s", nomi[i]);
	}
	if (!oh.lib) {
		di(oh.perche, sizeof oh.perche,
		   "OpenH264 non c'e' (ne' libopenh264.so.8 ne' .so.7): %s", dlerror());
		return false;
	}
	void (*versione)(OpenH264Version *) =
	    (void (*)(OpenH264Version *)) dlsym(oh.lib, "WelsGetCodecVersionEx");
	oh.crea = (int (*)(ISVCEncoder **)) dlsym(oh.lib, "WelsCreateSVCEncoder");
	oh.distruggi = (void (*)(ISVCEncoder *)) dlsym(oh.lib, "WelsDestroySVCEncoder");
	if (!versione || !oh.crea || !oh.distruggi) {
		di(oh.perche, sizeof oh.perche,
		   "%s non ha le funzioni del codificatore: e' la copia VUOTA (noopenh264), "
		   "non OpenH264", oh.quale);
		return false;
	}
	versione(&oh.v);
	if (oh.v.uMajor == 2 && oh.v.uMinor >= 6 && oh.v.uMinor <= 6)
		oh.forma_26 = true;
	else if (oh.v.uMajor == 2 && oh.v.uMinor == 5)
		oh.forma_26 = false;
	else {
		di(oh.perche, sizeof oh.perche,
		   "%s e' la versione %u.%u.%u: si conoscono le forme della 2.5 e della 2.6, e "
		   "una forma non guardata non si usa", oh.quale, oh.v.uMajor, oh.v.uMinor,
		   oh.v.uRevision);
		return false;
	}
	/* ⭐ La prova che codifica davvero: la copia vuota ha i simboli ma non
	 *    crea il codificatore (o non lo inizializza).  Un 64x64 e basta. */
	ISVCEncoder *e = NULL;
	bool vivo = oh.crea(&e) == 0 && e;
	if (vivo) {
		int zitto = WELS_LOG_QUIET; /* l'avviso sul profilo della prova non serve a nessuno */
		(*e)->SetOption(e, ENCODER_OPTION_TRACE_LEVEL, &zitto);
		SEncParamBase b;
		memset(&b, 0, sizeof b);
		b.iUsageType = CAMERA_VIDEO_REAL_TIME;
		b.iPicWidth = b.iPicHeight = 64;
		b.iTargetBitrate = 100000;
		b.iRCMode = RC_QUALITY_MODE;
		b.fMaxFrameRate = 30.f;
		vivo = (*e)->Initialize(e, &b) == cmResultSuccess;
		if (vivo)
			(*e)->Uninitialize(e);
	}
	if (e)
		oh.distruggi(e);
	if (!vivo) {
		di(oh.perche, sizeof oh.perche,
		   "%s (%u.%u.%u) non crea un codificatore: e' la copia VUOTA (noopenh264 o "
		   "simile) che il gestore dei pacchetti ha messo al posto di quella vera",
		   oh.quale, oh.v.uMajor, oh.v.uMinor, oh.v.uRevision);
		return false;
	}
	oh.us_carico = adesso_us() - t0;
	oh.pronto = true;
	registro_dice(REG_RIPIEGO,
	              "OpenH264 %u.%u.%u aperto da %s (forma %s) in %.1f ms, prova 64x64 compresa",
	              oh.v.uMajor, oh.v.uMinor, oh.v.uRevision, oh.quale,
	              oh.forma_26 ? "2.6" : "2.5", oh.us_carico / 1000.0);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔ I RIFIUTI, in UN posto solo — `ripiego_sa_fare()` e `ripiego_apri()`
 *    dicono le stesse cose perche' chiamano questa.
 * ═══════════════════════════════════════════════════════════════════════════ */
static bool rifiuti(const CodificatoreRichiesta *r, char *perche, size_t n)
{
	if (!r || !r->larghezza || !r->altezza) {
		di(perche, n, "misura nulla");
		return false;
	}
	if ((r->larghezza & 1) || (r->altezza & 1)) {
		di(perche, n, "%ux%u: 4:2:0 vuole misure pari", r->larghezza, r->altezza);
		return false;
	}
	switch (r->codec) {
	case CODIFICATORE_HEVC:
		/* ⛔⛔ Il rifiuto che conta.  Chi arriva qui con HEVC ha sbagliato
		 *      scelta a monte: `figlio.c` non deve mai chiedere HEVC al
		 *      software (vedi il rapporto della fase 18). */
		di(perche, n,
		   "HEVC in software non c'e': x265 e' GPL e REMOTIX e' PolyForm "
		   "Noncommercial (fase 18, DECISIONI.md §10.25).  ⛔ Non si ripiega in "
		   "silenzio su un altro codec: chi chiama ne scelga uno (H.264 o AV1)");
		return false;
	case CODIFICATORE_H264:
		if (r->profondita != 8) {
			di(perche, n,
			   "H.264 a %d bit: OpenH264 codifica solo 8 bit (niente High10), e "
			   "la pagina dichiara High a 8 bit (`avc1.6400LL`)", r->profondita);
			return false;
		}
		if (r->modo == CODIFICATORE_QUALITA_LOSSLESS) {
			/* ⛔ x264 lo faceva con `qp=0` (profilo High 4:4:4 Predictive, 244).
			 *    OpenH264 non ha il transform bypass: accettare e dare
			 *    qualcos'altro sarebbe il ripiego silenzioso di CODER.md §4.2. */
			di(perche, n,
			   "H.264 senza perdita: OpenH264 non ha il transform bypass "
			   "(x264 lo faceva con qp=0, profilo 244).  Non lo si finge: il "
			   "regime piu' vicino e' QP basso — si chieda quello");
			return false;
		}
		if (!FORMATO_PIXEL_IMPACCHETTATO(r->formato)) {
			di(perche, n, "H.264 a 8 bit si entra da BGRx o RGBx");
			return false;
		}
		if (!openh264_carica()) {
			di(perche, n, "%s", oh.perche);
			return false;
		}
		/* ⚠ Il tetto di OpenH264 e' quello del livello 5.2, il piu' alto che
		 *   conosce: 36 864 macroblocchi per fotogramma (4096x2304, o
		 *   3840x2160 = 32 400).  Oltre, l'encoder rifiuta o scrive un livello
		 *   bugiardo: si dice prima.  `[M]` la riga «8K» del banco. */
		{
			uint32_t mb = ((r->larghezza + 15) / 16) * ((r->altezza + 15) / 16);
			if (mb > 36864u && !regola("RIPIEGO_H264_SENZA_TETTO", 0)) {
				di(perche, n,
				   "H.264 %ux%u = %u macroblocchi: oltre i 36 864 del livello 5.2, "
				   "l'ultimo che OpenH264 conosce (x264 arrivava ai livelli 6.x)",
				   r->larghezza, r->altezza, mb);
				return false;
			}
		}
		return true;
	case CODIFICATORE_AV1:
		if (r->profondita != 8 && r->profondita != 10) {
			di(perche, n, "AV1 a %d bit: si chiede 8 o 10", r->profondita);
			return false;
		}
		if (r->modo == CODIFICATORE_QUALITA_LOSSLESS) {
			/* ⛔ La stessa riga di `opzioni_av1()`: SVT-AV1 2.3.0 non ha un
			 *    modo senza perdita, e non lo si finge. */
			di(perche, n,
			   "AV1: SVT-AV1 %s non ha un modo senza perdita, e non lo si finge. "
			   "Il regime piu' vicino e' CRF 1 [M]: si chieda quello",
			   svt_av1_get_version());
			return false;
		}
		if (r->qualita < 1 || r->qualita > 63) {
			di(perche, n, "AV1: %s %d fuori da 1-63", r->modo == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
			   r->qualita);
			return false;
		}
		if (r->formato == CODIFICATORE_PIXEL_YUV420P10LE && r->profondita != 10) {
			di(perche, n, "l'ingresso e' yuv420p10le e si chiedono %d bit", r->profondita);
			return false;
		}
		if (r->larghezza < 64 || r->altezza < 64 || r->larghezza > 16384 || r->altezza > 8704) {
			di(perche, n, "AV1 %ux%u: SVT-AV1 vuole da 64x64 a 16384x8704",
			   r->larghezza, r->altezza);
			return false;
		}
		return true;
	default:
		di(perche, n, "codec %d ignoto", (int) r->codec);
		return false;
	}
}

bool ripiego_sa_fare(const CodificatoreRichiesta *r, char *perche, size_t perche_byte)
{
	return rifiuti(r, perche, perche_byte);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * I PIANI — un blocco solo, allineato a 64 byte (le istruzioni vettoriali
 * delle due librerie leggono a blocchi).
 * ═══════════════════════════════════════════════════════════════════════════ */
static bool apri_piani(Ripiego *rp)
{
	free(rp->piani);
	rp->piani = NULL;
	if (!FORMATO_PIXEL_IMPACCHETTATO(rp->r.formato))
		return true; /* yuv420p10le: si passano i piani del chiamante */
	uint32_t b = rp->r.profondita == 10 ? 2u : 1u;
	rp->passo_y = ((rp->r.larghezza * b) + 63u) & ~63u;
	rp->passo_c = ((rp->r.larghezza / 2u * b) + 63u) & ~63u;
	size_t tot = (size_t) rp->passo_y * rp->r.altezza
	             + 2u * (size_t) rp->passo_c * (rp->r.altezza / 2u);
	rp->piani = aligned_alloc(64, (tot + 63u) & ~(size_t) 63u);
	return rp->piani != NULL;
}

static uint8_t *piano(Ripiego *rp, int i)
{
	size_t y = (size_t) rp->passo_y * rp->r.altezza;
	size_t c = (size_t) rp->passo_c * (rp->r.altezza / 2u);
	return rp->piani + (i == 0 ? 0 : i == 1 ? y : y + c);
}

static bool tieni(Ripiego *rp, size_t byte)
{
	if (byte <= rp->uscita_cap)
		return true;
	size_t nuova = rp->uscita_cap ? rp->uscita_cap : 1u << 20;
	while (nuova < byte)
		nuova *= 2u;
	uint8_t *p = realloc(rp->uscita, nuova);
	if (!p)
		return false;
	rp->uscita = p;
	rp->uscita_cap = nuova;
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐ H.264 — OpenH264
 * ═══════════════════════════════════════════════════════════════════════════ */

/* ⚠ I messaggi di OpenH264 vanno nel registro e non su stderr nudo: una riga
 *   senza area ne' ora e' una riga che nessun banco sa attribuire. */
static void openh264_parla(void *ctx, int livello, const char *msg)
{
	(void) ctx;
	size_t n = strlen(msg);
	while (n && (msg[n - 1] == '\n' || msg[n - 1] == '\r'))
		n--;
	registro_dice(REG_RIPIEGO, "OpenH264 (%s): %.*s",
	              livello <= WELS_LOG_ERROR ? "errore" : "avviso", (int) n, msg);
}

static int qp_da_qualita(ModoQualita modo, int qualita)
{
	int qp = modo == CODIFICATORE_QUALITA_QP
	             ? qualita
	             : qualita + regola("RIPIEGO_H264_DELTA_QP", RIPIEGO_H264_DELTA_QP);
	return qp < 0 ? 0 : qp > 51 ? 51 : qp;
}

static void chiudi_h264(Ripiego *rp)
{
	if (!rp->h264)
		return;
	(*rp->h264)->Uninitialize(rp->h264);
	oh.distruggi(rp->h264);
	rp->h264 = NULL;
}

/*
 * ⛔⭐ IL LIVELLO IMPOSTO — `RCP.md` §4.3, e OpenH264 non lo tiene da solo.
 *
 * `[M]` 30 set 2026, 3840x2160 a 60/s con 5.1 imposto: x264 scrive
 * `level_idc = 51` (avvisando *«MB rate (1944000) > level limit (983040)»*) e
 * continua a 60; **OpenH264 lo alza da se' a 5.2**, perche' il ritmo di
 * macroblocchi del 5.1 (983 040 al secondo) a 4K vale ~30 fotogrammi, e la
 * riga «§4.3 — LIVELLO» del figlio direbbe ⛔ 5.2 > 5.1.
 *
 * ⭐ La cura: a OpenH264 si DICHIARA la cadenza che sta nel livello chiesto.
 *    Col QP costante (`RC_OFF_MODE`) e i salti spenti la cadenza dichiarata
 *    non tocca ne' la qualita' ne' il ritmo vero — serve solo al conto del
 *    livello e del bitrate, che qui e' spento.  ⇒ Il flusso dice 5.1 e va a
 *    60, esattamente come faceva x264: e' quel che il client ha CHIESTO (vedi
 *    `figlio.c`, il riquadro del livello).
 * ⚠ Se a non starci e' la MISURA (MaxFS) e non la cadenza, non c'e' cadenza
 *   che tenga: OpenH264 alza il livello, e la riga del figlio lo dice.
 */
static const struct {
	int x10;
	uint32_t mbps, fs;
} livelli_h264[] = {
	{ 10, 1485, 99 },     { 11, 3000, 396 },    { 12, 6000, 396 },     { 13, 11880, 396 },
	{ 20, 11880, 396 },   { 21, 19800, 792 },   { 22, 20250, 1620 },   { 30, 40500, 1620 },
	{ 31, 108000, 3600 }, { 32, 216000, 5120 }, { 40, 245760, 8192 },  { 41, 245760, 8192 },
	{ 42, 522240, 8704 }, { 50, 589824, 22080 }, { 51, 983040, 36864 }, { 52, 2073600, 36864 },
};

static float cadenza_nel_livello(const CodificatoreRichiesta *r, uint32_t fps)
{
	if (r->livello_x10 <= 0)
		return (float) fps;
	uint32_t mb = ((r->larghezza + 15) / 16) * ((r->altezza + 15) / 16);
	for (size_t i = 0; i < sizeof livelli_h264 / sizeof *livelli_h264; i++) {
		if (livelli_h264[i].x10 != r->livello_x10)
			continue;
		if (mb > livelli_h264[i].fs) {
			/* `[M]` 4.2 imposto a 3840x2160: OpenH264 scrive 5.1 (x264 scriveva
			 * 4.2, cioe' un livello che la misura non rispetta). */
			registro_dice(REG_RIPIEGO,
			              "⛔ §4.3: livello %d.%d imposto a %ux%u, ma la MISURA (%u "
			              "macroblocchi) supera i %u del livello: nessuna cadenza lo "
			              "tiene, e OpenH264 scrivera' il livello che la misura vuole",
			              r->livello_x10 / 10, r->livello_x10 % 10, r->larghezza,
			              r->altezza, mb, livelli_h264[i].fs);
			return (float) fps;
		}
		uint32_t max = livelli_h264[i].mbps / mb;
		if (max >= fps || max < 1)
			return (float) fps;
		registro_dice(REG_RIPIEGO,
		              "⚠ §4.3: livello %d.%d imposto a %ux%u — il suo ritmo di macroblocchi "
		              "ne concede %u al secondo e se ne fanno %u.  ⇒ A OpenH264 si dichiara "
		              "%u (solo il conto del livello: QP costante, niente salti) perche' "
		              "scriva %d.%d come faceva x264, invece di alzarlo da se'",
		              r->livello_x10 / 10, r->livello_x10 % 10, r->larghezza, r->altezza,
		              max, fps, max, r->livello_x10 / 10, r->livello_x10 % 10);
		return (float) max;
	}
	return (float) fps;
}

static bool apri_h264(Ripiego *rp, char *errore, size_t n)
{
	if (!openh264_carica()) {
		di(errore, n, "%s", oh.perche);
		return false;
	}
	if (oh.crea(&rp->h264) != 0 || !rp->h264) {
		di(errore, n, "OpenH264: WelsCreateSVCEncoder e' fallita");
		rp->h264 = NULL;
		return false;
	}
	ISVCEncoder *e = rp->h264;
	int traccia = WELS_LOG_WARNING;
	WelsTraceCallback parla = openh264_parla;
	(*e)->SetOption(e, ENCODER_OPTION_TRACE_LEVEL, &traccia);
	(*e)->SetOption(e, ENCODER_OPTION_TRACE_CALLBACK, (void *) &parla);

	SEncParamExt p;
	memset(&p, 0, sizeof p);
	(*e)->GetDefaultParams(e, &p);

	const uint32_t fps = rp->r.fotogrammi_al_secondo ? rp->r.fotogrammi_al_secondo : 30;
	rp->qp_h264 = qp_da_qualita(rp->modo, rp->qualita);
	rp->fili_h264 = regola("RIPIEGO_H264_FILI", RIPIEGO_H264_FILI);
	const int cabac = regola("RIPIEGO_H264_CABAC", RIPIEGO_H264_CABAC);
	const int profilo = regola("RIPIEGO_H264_PROFILO", RIPIEGO_H264_PROFILO);

	p.iUsageType = regola("RIPIEGO_H264_USO", RIPIEGO_H264_USO) ? SCREEN_CONTENT_REAL_TIME
	                                                             : CAMERA_VIDEO_REAL_TIME;
	p.iPicWidth = (int) rp->r.larghezza;
	p.iPicHeight = (int) rp->r.altezza;
	/* ⭐ Il QP costante: il controllo del bitrate SPENTO, come CQP.  ⛔ E
	 *    niente salti di fotogramma: un fotogramma saltato e' un fotogramma
	 *    che il client non riceve, e nessuno glielo dice. */
	p.iRCMode = RC_OFF_MODE;
	p.bEnableFrameSkip = false;
	p.iTargetBitrate = 0;
	p.iMaxBitrate = UNSPECIFIED_BIT_RATE;
	p.iMinQp = 0;
	p.iMaxQp = 51;
	p.fMaxFrameRate = cadenza_nel_livello(&rp->r, fps);
	p.iTemporalLayerNum = 1; /* ⛔ uno strato: niente gerarchia, niente ritardo */
	p.iSpatialLayerNum = 1;
	p.iComplexityMode = (ECOMPLEXITY_MODE) regola("RIPIEGO_H264_COMPLESSITA",
	                                              RIPIEGO_H264_COMPLESSITA);
	/* ⛔ Chiavi solo su richiesta, come `keyint=-1`: 0 = «solo la prima». */
	p.uiIntraPeriod = rp->r.chiavi_ogni;
	p.iNumRefFrame = 1;
	/* ⚠ ID costanti: ogni IDR porta di nuovo SPS e PPS con gli stessi numeri,
	 *   cioe' la forma di `repeat-headers=1`. */
	p.eSpsPpsIdStrategy = CONSTANT_ID;
	p.bPrefixNalAddingCtrl = false;
	p.bEnableSSEI = false;
	p.bSimulcastAVC = false;
	p.iPaddingFlag = 0;
	p.iEntropyCodingModeFlag = cabac;
	p.bEnableLongTermReference = false;
	p.iMultipleThreadIdc = (unsigned short) rp->fili_h264;
	p.bUseLoadBalancing = false; /* ⚠ con true il risultato cambia da giro a giro */
	p.iLoopFilterDisableIdc = 0;
	p.bEnableDenoise = false;          /* ⛔ il desktop non ha rumore da togliere */
	/* ⚠ Sotto «contenuto schermo» OpenH264 li spegne da se' avvisando
	 *   (`[M]` *«not supported yet for screen content, auto turned off»*): si
	 *   spengono qui, o sono due righe d'avviso a ogni riapertura. */
	p.bEnableBackgroundDetection = p.iUsageType != SCREEN_CONTENT_REAL_TIME;
	p.bEnableAdaptiveQuant = p.iUsageType != SCREEN_CONTENT_REAL_TIME;
	p.bEnableFrameCroppingFlag = true; /* ⛔ la misura VERA nell'SPS (1080 non e' multiplo di 16) */
	p.bEnableSceneChangeDetect = regola("RIPIEGO_H264_SCD", RIPIEGO_H264_SCD);

	SSpatialLayerConfig *s = &p.sSpatialLayers[0];
	s->iVideoWidth = p.iPicWidth;
	s->iVideoHeight = p.iPicHeight;
	s->fFrameRate = p.fMaxFrameRate;
	s->iSpatialBitrate = 0;
	s->iMaxSpatialBitrate = UNSPECIFIED_BIT_RATE;
	s->uiProfileIdc = (EProfileIdc) profilo;
	s->uiLevelIdc = rp->r.livello_x10 > 0 ? (ELevelIdc) rp->r.livello_x10 : LEVEL_UNKNOWN;
	s->iDLayerQp = rp->qp_h264;
	memset(&s->sSliceArgument, 0, sizeof s->sSliceArgument);
	if (rp->fili_h264 > 1) {
		s->sSliceArgument.uiSliceMode = SM_FIXEDSLCNUM_SLICE;
		s->sSliceArgument.uiSliceNum = (unsigned) rp->fili_h264;
	} else {
		s->sSliceArgument.uiSliceMode = SM_SINGLE_SLICE;
	}
	/* ⛔ Il colore DICHIARATO nella VUI: BT.709, intervallo limitato. */
	s->bVideoSignalTypePresent = true;
	s->uiVideoFormat = VF_UNDEF;
	s->bFullRange = false;
	s->bColorDescriptionPresent = true;
	s->uiColorPrimaries = CP_BT709;
	s->uiTransferCharacteristics = TRC_BT709;
	s->uiColorMatrix = CM_BT709;

	int esito = (*e)->InitializeExt(e, &p);
	if (esito != cmResultSuccess) {
		di(errore, n, "OpenH264 non si e' aperto a %ux%u QP %d (InitializeExt = %d)",
		   rp->r.larghezza, rp->r.altezza, rp->qp_h264, esito);
		chiudi_h264(rp);
		return false;
	}
	int formato = videoFormatI420;
	(*e)->SetOption(e, ENCODER_OPTION_DATAFORMAT, &formato);
	rp->param_h264 = p;

	OpenH264Version v = oh.v;
	snprintf(rp->nome, sizeof rp->nome,
	         "H.264 8 bit via OpenH264 %u.%u.%u (in software · QP %d costante%s · %s · "
	         "%s · %d fil%s)",
	         v.uMajor, v.uMinor, v.uRevision, rp->qp_h264,
	         rp->modo == CODIFICATORE_QUALITA_CRF ? ", dal CRF" : "",
	         cabac ? "CABAC" : "CAVLC",
	         p.iUsageType == SCREEN_CONTENT_REAL_TIME ? "contenuto schermo" : "camera",
	         rp->fili_h264, rp->fili_h264 == 1 ? "o" : "i");
	return true;
}

static bool codifica_h264(Ripiego *rp, bool chiave, RipiegoUscita *fuori)
{
	ISVCEncoder *e = rp->h264;
	SSourcePicture pic;
	/* ⚠ Le due forme dell'uscita (vedi sopra): si legge con quella della
	 *   versione aperta. */
	union {
		SFrameBSInfo v26;
		FotogrammaV25 v25;
	} info;
	memset(&pic, 0, sizeof pic);
	memset(&info, 0, sizeof info);
	pic.iColorFormat = videoFormatI420;
	pic.iPicWidth = (int) rp->r.larghezza;
	pic.iPicHeight = (int) rp->r.altezza;
	for (int i = 0; i < 3; i++) {
		pic.pData[i] = piano(rp, i);
		pic.iStride[i] = (int) (i ? rp->passo_c : rp->passo_y);
	}
	const uint32_t fps = rp->r.fotogrammi_al_secondo ? rp->r.fotogrammi_al_secondo : 30;
	pic.uiTimeStamp = rp->numero * 1000 / fps;

	if (chiave)
		(*e)->ForceIntraFrame(e, true);
	uint64_t t0 = adesso_us();
	int esito = (*e)->EncodeFrame(e, &pic, &info.v26);
	fuori->us_codifica = adesso_us() - t0;
	if (esito != cmResultSuccess) {
		registro_dice(REG_RIPIEGO, "⛔ OpenH264: EncodeFrame = %d", esito);
		return false;
	}
	const EVideoFrameType tipo = oh.forma_26 ? info.v26.eFrameType : info.v25.eFrameType;
	const int strati = oh.forma_26 ? info.v26.iLayerNum : info.v25.iLayerNum;
#define STRATO(l, campo) (oh.forma_26 ? info.v26.sLayerInfo[l].campo : info.v25.sLayerInfo[l].campo)
	if (tipo == videoFrameTypeSkip || tipo == videoFrameTypeInvalid) {
		/* ⛔ Col controllo del bitrate spento e i salti spenti non deve
		 *    succedere: se succede, lo si dice invece di spedire niente. */
		fuori->trattenuto = true;
		registro_dice(REG_RIPIEGO,
		              "⚠ OpenH264 ha %s il fotogramma %lld: nessun byte in uscita",
		              tipo == videoFrameTypeSkip ? "SALTATO" : "rifiutato",
		              (long long) rp->numero);
		return false;
	}

	/* I NAL arrivano gia' col codice d'inizio (Annex B), strato per strato:
	 * SPS e PPS sono uno strato «non VCL» davanti alla IDR. */
	size_t tot = 0;
	for (int l = 0; l < strati; l++)
		for (int k = 0; k < STRATO(l, iNalCount); k++)
			tot += (size_t) STRATO(l, pNalLengthInByte)[k];
	if (!tieni(rp, tot))
		return false;
	size_t at = 0;
	for (int l = 0; l < strati; l++) {
		size_t b = 0;
		for (int k = 0; k < STRATO(l, iNalCount); k++)
			b += (size_t) STRATO(l, pNalLengthInByte)[k];
		memcpy(rp->uscita + at, STRATO(l, pBsBuf), b);
		at += b;
	}
#undef STRATO
	fuori->dati = rp->uscita;
	fuori->byte = at;
	fuori->chiave = tipo == videoFrameTypeIDR;
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐ AV1 — SVT-AV1 chiamata diretta
 * ═══════════════════════════════════════════════════════════════════════════ */
static void chiudi_av1(Ripiego *rp)
{
	if (!rp->av1)
		return;
	/* ⚠ Prima la fine del flusso, poi la chiusura: senza, SVT scrive
	 *   *«deinit called without sending EOS!»* fra gli errori (`[M]` lo faceva
	 *   anche la strada di libavcodec) — una riga d'errore a ogni riapertura
	 *   che non e' un errore, cioe' rumore che copre quelle vere.  Non c'e'
	 *   niente in canna (un fotogramma dentro, un pacchetto fuori): esce solo
	 *   il pacchetto che dice «fine». */
	EbBufferHeaderType fine;
	memset(&fine, 0, sizeof fine);
	fine.size = sizeof fine;
	fine.flags = EB_BUFFERFLAG_EOS;
	if (svt_av1_enc_send_picture(rp->av1, &fine) == EB_ErrorNone) {
		for (int giri = 0; giri < 64; giri++) {
			EbBufferHeaderType *pk = NULL;
			if (svt_av1_enc_get_packet(rp->av1, &pk, 1) != EB_ErrorNone || !pk)
				break;
			bool ultimo = (pk->flags & EB_BUFFERFLAG_EOS) != 0;
			svt_av1_enc_release_out_buffer(&pk);
			if (ultimo)
				break;
		}
	}
	svt_av1_enc_deinit(rp->av1);
	svt_av1_enc_deinit_handle(rp->av1);
	rp->av1 = NULL;
}

static bool apri_av1(Ripiego *rp, char *errore, size_t n)
{
	EbSvtAv1EncConfiguration cfg;
	memset(&cfg, 0, sizeof cfg);
	EbErrorType esito = svt_av1_enc_init_handle(&rp->av1, NULL, &cfg);
	if (esito != EB_ErrorNone || !rp->av1) {
		di(errore, n, "SVT-AV1: init_handle = 0x%x", (unsigned) esito);
		rp->av1 = NULL;
		return false;
	}
	const uint32_t fps = rp->r.fotogrammi_al_secondo ? rp->r.fotogrammi_al_secondo : 30;
	cfg.enc_mode = (int8_t) regola("RIPIEGO_AV1_PRESET", RIPIEGO_AV1_PRESET);
	cfg.source_width = rp->r.larghezza;
	cfg.source_height = rp->r.altezza;
	cfg.frame_rate_numerator = fps;
	cfg.frame_rate_denominator = 1;
	cfg.encoder_bit_depth = (uint32_t) rp->r.profondita;
	cfg.encoder_color_format = EB_YUV420;
	cfg.profile = MAIN_PROFILE;
	/* ⛔⭐ Il livello in DECIMI (51 = 5.1), che e' quel che SVT vuole.
	 *     ⚠ La strada di libavcodec ci passava `seq_level_idx` (13 per il 5.1,
	 *       `livello_imposto()`): due alfabeti diversi sotto lo stesso campo. */
	cfg.level = rp->r.livello_x10 > 0 ? (uint32_t) rp->r.livello_x10 : 0;
	/* ⭐ La qualita': CRF = QP costante con la quantizzazione adattiva (il
	 *    difetto, 2); QP vero = la stessa senza adattiva (e' il `qp=` di
	 *    libsvtav1).  ⚠ `opzioni_av1()` mandava sempre `crf`, anche a QP. */
	cfg.rate_control_mode = SVT_AV1_RC_MODE_CQP_OR_CRF;
	cfg.qp = (uint32_t) rp->qualita;
	if (rp->modo == CODIFICATORE_QUALITA_QP)
		cfg.enable_adaptive_quantization = 0;
	/* ⛔ `pred-struct=1`: bassa latenza, niente fotogrammi dal futuro. */
	cfg.pred_structure = SVT_AV1_PRED_LOW_DELAY_B;
	/* ⛔ Chiavi solo su richiesta (−1 = «nessun rinfresco»), e CHIUSE (2 = KEY
	 *    con GOP chiuso): §5.2 vuole una chiave che si decodifichi da sola. */
	cfg.intra_period_length = rp->r.chiavi_ogni ? (int32_t) rp->r.chiavi_ogni - 1 : -1;
	cfg.intra_refresh_type = SVT_AV1_KF_REFRESH;
	/* ⚠ La chiave su richiesta (`pic_type = EB_AV1_KEY_PICTURE`) in bassa
	 *   latenza NON vuole `force_key_frames`: `[M]` 30 set 2026 SVT 2.3.0 con
	 *   il flag acceso avvisa *«force_key_frames does not need to be set»* e lo
	 *   rimette a 0 da se', e la chiave esce lo stesso (banco, «chiave chiesta
	 *   al 45 uscita», vecchia e nuova). */
	cfg.force_key_frames = 0;
	cfg.color_description_present_flag = 1;
	cfg.color_primaries = EB_CICP_CP_BT_709;
	cfg.transfer_characteristics = EB_CICP_TC_BT_709;
	cfg.matrix_coefficients = EB_CICP_MC_BT_709;
	cfg.color_range = EB_CR_STUDIO_RANGE;

	esito = svt_av1_enc_set_parameter(rp->av1, &cfg);
	if (esito != EB_ErrorNone) {
		di(errore, n, "SVT-AV1 ha rifiutato i parametri (%ux%u, %d bit, %s %d): 0x%x",
		   rp->r.larghezza, rp->r.altezza, rp->r.profondita,
		   rp->modo == CODIFICATORE_QUALITA_QP ? "QP" : "CRF", rp->qualita,
		   (unsigned) esito);
		svt_av1_enc_deinit_handle(rp->av1);
		rp->av1 = NULL;
		return false;
	}
	esito = svt_av1_enc_init(rp->av1);
	if (esito != EB_ErrorNone) {
		di(errore, n, "SVT-AV1 non si e' aperto: 0x%x", (unsigned) esito);
		svt_av1_enc_deinit_handle(rp->av1);
		rp->av1 = NULL;
		return false;
	}
	snprintf(rp->nome, sizeof rp->nome,
	         "AV1 %d bit via SVT-AV1 %s (in software · preset %d · %s %d · bassa latenza)",
	         rp->r.profondita, svt_av1_get_version(), cfg.enc_mode,
	         rp->modo == CODIFICATORE_QUALITA_QP ? "QP" : "CRF", rp->qualita);
	return true;
}

static bool codifica_av1(Ripiego *rp, const uint8_t *pixel, uint32_t passo, bool chiave,
                         RipiegoUscita *fuori)
{
	EbSvtIOFormat io;
	EbBufferHeaderType in;
	memset(&io, 0, sizeof io);
	memset(&in, 0, sizeof in);
	const uint32_t b = rp->r.profondita == 10 ? 2u : 1u;
	const uint32_t l = rp->r.larghezza, a = rp->r.altezza;
	if (rp->piani) {
		io.luma = piano(rp, 0);
		io.cb = piano(rp, 1);
		io.cr = piano(rp, 2);
		io.y_stride = rp->passo_y / b; /* ⚠ SVT vuole i passi in CAMPIONI */
		io.cb_stride = io.cr_stride = rp->passo_c / b;
	} else {
		/* yuv420p10le del chiamante: i piani si passano come sono (SVT li
		 * copia dentro `send_picture`). */
		uint32_t py = passo ? passo : l * 2u;
		io.luma = (uint8_t *) pixel;
		io.cb = io.luma + (size_t) py * a;
		io.cr = io.cb + (size_t) (py / 2u) * (a / 2u);
		io.y_stride = py / 2u;
		io.cb_stride = io.cr_stride = py / 4u;
	}
	io.width = l;
	io.height = a;
	io.color_fmt = EB_YUV420;
	io.bit_depth = rp->r.profondita == 10 ? EB_TEN_BIT : EB_EIGHT_BIT;

	in.size = sizeof in;
	in.p_buffer = (uint8_t *) &io;
	in.n_filled_len = (uint32_t) ((size_t) l * a * b * 3u / 2u);
	in.n_alloc_len = in.n_filled_len;
	in.pts = rp->numero;
	in.pic_type = chiave ? EB_AV1_KEY_PICTURE : EB_AV1_INVALID_PICTURE;

	uint64_t t0 = adesso_us();
	EbErrorType esito = svt_av1_enc_send_picture(rp->av1, &in);
	if (esito != EB_ErrorNone) {
		registro_dice(REG_RIPIEGO, "⛔ SVT-AV1: send_picture = 0x%x", (unsigned) esito);
		return false;
	}
	/*
	 * ⛔⭐ SI ASPETTA IL PACCHETTO, e qui sta la differenza con libavcodec.
	 *
	 * `svt_av1_enc_get_packet(…, 0)` NON aspetta: se la catena di fili non ha
	 * ancora finito torna «coda vuota», e libavcodec lo traduce in EAGAIN —
	 * cioe' il ramo «trattenuto» di `comprimi_comune()`, che svuota e RIAPRE il
	 * codificatore.  ⇒ Si chiede di nuovo finche' il pacchetto non c'e', con un
	 * tetto: in bassa latenza un fotogramma dentro e' un pacchetto fuori, e
	 * chiedere con `pic_send_done = 1` (bloccante) resterebbe appeso per sempre
	 * il giorno in cui non lo fosse.
	 */
	EbBufferHeaderType *pk = NULL;
	for (;;) {
		esito = svt_av1_enc_get_packet(rp->av1, &pk, 0);
		if (esito == EB_ErrorNone && pk)
			break;
		if (esito != EB_NoErrorEmptyQueue) {
			registro_dice(REG_RIPIEGO, "⛔ SVT-AV1: get_packet = 0x%x", (unsigned) esito);
			return false;
		}
		if (adesso_us() - t0 > AV1_ATTESA_US) {
			fuori->trattenuto = true;
			registro_dice(REG_RIPIEGO,
			              "⚠ SVT-AV1 ha trattenuto il fotogramma %lld per piu' di %u ms: "
			              "e' un fotogramma di RITARDO, e la bassa latenza non e' bastata",
			              (long long) rp->numero, AV1_ATTESA_US / 1000u);
			return false;
		}
		struct timespec poco = { 0, 10 * 1000 }; /* 10 µs */
		nanosleep(&poco, NULL);
	}
	fuori->us_codifica = adesso_us() - t0;
	bool ok = true;
	if (pk->flags & EB_BUFFERFLAG_ERROR_MASK) {
		registro_dice(REG_RIPIEGO, "⛔ SVT-AV1: pacchetto con errore (flags 0x%x)", pk->flags);
		ok = false;
	} else if (!tieni(rp, pk->n_filled_len)) {
		ok = false;
	} else {
		memcpy(rp->uscita, pk->p_buffer, pk->n_filled_len);
		fuori->dati = rp->uscita;
		fuori->byte = pk->n_filled_len;
		fuori->chiave = pk->pic_type == EB_AV1_KEY_PICTURE;
	}
	svt_av1_enc_release_out_buffer(&pk);
	return ok;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐ L'INTERFACCIA
 * ═══════════════════════════════════════════════════════════════════════════ */
static void chiudi_libreria(Ripiego *rp)
{
	chiudi_h264(rp);
	chiudi_av1(rp);
}

static bool apri_libreria(Ripiego *rp, char *errore, size_t n)
{
	if (!apri_piani(rp)) {
		di(errore, n, "niente memoria per i piani %ux%u", rp->r.larghezza, rp->r.altezza);
		return false;
	}
	rp->numero = 0;
	return rp->r.codec == CODIFICATORE_H264 ? apri_h264(rp, errore, n)
	                                        : apri_av1(rp, errore, n);
}

Ripiego *ripiego_apri(const CodificatoreRichiesta *r, char *errore, size_t errore_byte)
{
	if (!rifiuti(r, errore, errore_byte))
		return NULL;
	Ripiego *rp = calloc(1, sizeof *rp);
	if (!rp) {
		di(errore, errore_byte, "niente memoria");
		return NULL;
	}
	rp->r = *r;
	rp->r.componente = NULL;
	rp->r.nodo_rendering = NULL;
	rp->modo = r->modo;
	rp->qualita = r->qualita;
	if (!apri_libreria(rp, errore, errore_byte)) {
		ripiego_chiudi(rp);
		return NULL;
	}
	return rp;
}

bool ripiego_codifica(Ripiego *rp, const uint8_t *pixel, uint32_t passo, bool chiave,
                      RipiegoUscita *fuori)
{
	if (!rp || !pixel || !fuori)
		return false;
	memset(fuori, 0, sizeof *fuori);
	if (!rp->h264 && !rp->av1) {
		/* ⚠ Una riapertura (qualita', misura) e' fallita e non e' stata rifatta:
		 *   chi chiama l'ha gia' saputo dal suo `false`. */
		registro_dice(REG_RIPIEGO, "⛔ il ripiego e' chiuso: una riapertura e' fallita");
		return false;
	}

	uint64_t t0 = adesso_us();
	if (rp->piani) {
		Colori709Ordine ordine = rp->r.formato == CODIFICATORE_PIXEL_RGBX ? COLORI709_RGBX
		                                                                   : COLORI709_BGRX;
		bool ok = rp->r.profondita == 10
		              ? colori709_a_i420_10(pixel, passo, rp->r.larghezza, rp->r.altezza,
		                                    ordine, (uint16_t *) piano(rp, 0), rp->passo_y,
		                                    (uint16_t *) piano(rp, 1), rp->passo_c,
		                                    (uint16_t *) piano(rp, 2), rp->passo_c)
		              : colori709_a_i420(pixel, passo, rp->r.larghezza, rp->r.altezza,
		                                 ordine, piano(rp, 0), rp->passo_y, piano(rp, 1),
		                                 rp->passo_c, piano(rp, 2), rp->passo_c);
		if (!ok) {
			registro_dice(REG_RIPIEGO, "⛔ la conversione dei colori ha rifiutato %ux%u",
			              rp->r.larghezza, rp->r.altezza);
			return false;
		}
	}
	fuori->us_conversione = adesso_us() - t0;

	/* ⛔ Il primo fotogramma dopo un'apertura e' una chiave comunque: lo si
	 *    chiede anche se chi chiama non l'ha chiesto, e l'uscita lo dice. */
	bool chiedi = chiave || rp->numero == 0;
	bool ok = rp->h264 ? codifica_h264(rp, chiedi, fuori)
	                   : codifica_av1(rp, pixel, passo, chiedi, fuori);
	if (!ok)
		return false;
	if (chiedi && !fuori->chiave)
		registro_dice(REG_RIPIEGO,
		              "⛔ chiesta una CHIAVE al fotogramma %lld e %s ha prodotto un delta",
		              (long long) rp->numero, rp->h264 ? "OpenH264" : "SVT-AV1");
	rp->numero++;
	return true;
}

bool ripiego_ridimensiona(Ripiego *rp, uint32_t larghezza, uint32_t altezza,
                          char *errore, size_t errore_byte)
{
	if (!rp)
		return false;
	CodificatoreRichiesta nuova = rp->r;
	nuova.larghezza = larghezza;
	nuova.altezza = altezza;
	nuova.modo = rp->modo;
	nuova.qualita = rp->qualita;
	if (!rifiuti(&nuova, errore, errore_byte))
		return false;
	chiudi_libreria(rp);
	rp->r.larghezza = larghezza;
	rp->r.altezza = altezza;
	return apri_libreria(rp, errore, errore_byte);
}

bool ripiego_qualita(Ripiego *rp, ModoQualita modo, int qualita, char *errore,
                     size_t errore_byte)
{
	if (!rp)
		return false;
	CodificatoreRichiesta nuova = rp->r;
	nuova.modo = modo;
	nuova.qualita = qualita;
	if (!rifiuti(&nuova, errore, errore_byte))
		return false;
	/*
	 * ⭐ H.264: il QP si cambia A CALDO, senza richiudere.  `[M]` 30 set 2026:
	 *    richiudere e riaprire OpenH264 costa 20 ms a 1080p e **60 ms a 4K**
	 *    (x264 ne costava 1-2), e la scala di `abbassa_qualita()` per una chiave
	 *    sopra il tetto ne fa fino a tre di fila.  Con i parametri nuovi passati
	 *    a `SetOption` il QP cambia al fotogramma dopo — il banco lo verifica
	 *    dai byte, non dal ritorno della chiamata.
	 * ⚠ Il prossimo fotogramma resta una CHIAVE lo stesso: chi chiama lo
	 *   chiede (`c->prossimo_chiave`), ed e' quel che la scala si aspetta.
	 */
	if (rp->h264 && regola("RIPIEGO_H264_CALDO", 1)) {
		SEncParamExt p = rp->param_h264;
		int qp = qp_da_qualita(modo, qualita);
		p.sSpatialLayers[0].iDLayerQp = qp;
		int esito = (*rp->h264)->SetOption(rp->h264, ENCODER_OPTION_SVC_ENCODE_PARAM_EXT, &p);
		if (esito == cmResultSuccess) {
			rp->param_h264 = p;
			rp->modo = modo;
			rp->qualita = qualita;
			char *q = strstr(rp->nome, "QP ");
			if (q) {
				/* il nome dice il QP in vigore */
				char coda[160];
				const char *dopo = strchr(q + 3, ' ');
				snprintf(coda, sizeof coda, "%s", dopo ? dopo : "");
				snprintf(q, sizeof rp->nome - (size_t) (q - rp->nome), "QP %d%s", qp, coda);
			}
			rp->qp_h264 = qp;
			return true;
		}
		registro_dice(REG_RIPIEGO,
		              "⚠ OpenH264 non ha preso il QP %d a caldo (%d): si richiude e riapre",
		              qp, esito);
	}
	chiudi_libreria(rp);
	rp->modo = modo;
	rp->qualita = qualita;
	return apri_libreria(rp, errore, errore_byte);
}

const char *ripiego_nome(const Ripiego *rp)
{
	return rp ? rp->nome : "(nessuno)";
}

void ripiego_chiudi(Ripiego *rp)
{
	if (!rp)
		return;
	chiudi_libreria(rp);
	free(rp->piani);
	free(rp->uscita);
	free(rp);
}
