/*
 * codificatore.c — HEVC Main10 e AV1, in software **o in hardware via VA-API**,
 * con la confessione letta sui byte.  Il perche' di ogni scelta sta in
 * `codificatore.h`; qui c'e' il come, e accanto a ogni riga strana la misura
 * che l'ha resa necessaria.
 *
 * ⭐ La GPU si tocca dal 13 agosto 2026 (fase 3, anticipata per decisione
 *    dell'utente).  ⛔ Ma **solo per la codifica**: la copia zero — il
 *    fotogramma che dalla cattura va alla GPU senza passare per la memoria di
 *    sistema — resta alla fase 8, e qui il caricamento si paga e **si misura a
 *    parte** (`us_caricamento`), perche' si veda quanto varra' toglierlo.
 */
#include "codificatore.h"
#include "registro.h"

#include <inttypes.h>
#include <limits.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <libavcodec/avcodec.h>
#include <libavutil/hwcontext.h>
#include <libavutil/hwcontext_vaapi.h>
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
#include <libswscale/swscale.h>
#include <va/va.h>
/* ⭐ I tre che nascono con la COPIA ZERO: `va_drmcommon.h` porta il descrittore
 *    con cui si importa un DMA-BUF (`VADRMPRIMESurfaceDescriptor`), `va_vpp.h`
 *    la conversione di colore fatta dalla GPU (`VAProcPipelineParameterBuffer`),
 *    e `drm_fourcc.h` i due soli nomi di formato che questo modulo riconosce.
 * ⚠ `drm_fourcc.h` sono SOLO intestazioni: nessuna libreria da collegare — la
 *   stessa nota che il Makefile ha gia' per `cattura.c`. */
#include <drm_fourcc.h>
#include <va/va_drmcommon.h>
#include <va/va_vpp.h>

/* ⚠ Area propria invece di una delle sei di `registro.h`: quel file non e' di
 *   questa sotto-fase e non si tocca.  La riga per centralizzarla — `#define
 *   REG_VIDEO "video"` — sta nel rapporto, insieme a quelle del Makefile. */
#define REG_CODIFICA "video"

/* `RCP.md` §6.2: «il server NON DEVE produrre un fotogramma piu' lungo di 16
 * MiB.  Se la codifica ne producesse uno piu' grande, DEVE ricodificarlo a
 * qualita' inferiore e SCRIVERLO NEL REGISTRO — mai spedirlo.» */
#define TETTO_FOTOGRAMMA (16u * 1024u * 1024u)

/* ⛔ Quanti giri si concedono a un DELTA.  ⚠ A una CHIAVE non si applica, e la
 *    ragione sta nel riquadro dentro `codificatore_comprimi()`: §5.2 vieta di
 *    abbandonarla. */
#define RICODIFICHE_MASSIME 3

/* Il primo scalino quando il tetto morde, e il passo dei successivi.
 *
 * ⛔⛔ E IL PASSO ERA 6, CIOE' CORTO DI UNO SCALINO — `[M]` 22 agosto 2026,
 *      misurato dall'agente D su 7680x4320 con contenuto quasi incomprimibile,
 *      n=8 per riga:
 *
 *        l'ultimo scalino che c'era   QP 38 → **16,654 MiB**  ⛔ 8 volte su 8
 *                                                                sopra il tetto
 *        quello che NON c'era         QP 44 → 11,056 MiB      ⭐ ce l'avrebbe
 *                                                                fatta
 *
 *      ⇒ Il tetto e' 16 777 216 byte e **QP 38 sta al 104,1 %: si perdeva per
 *        il 4 %**.  Tre tentativi da 6 arrivavano a 38 e si fermavano li'.
 *
 * ⭐ E SI ALZA IL PASSO, NON IL NUMERO DI TENTATIVI: `[M]` ogni tentativo a 8K
 *    costa **91-108 ms in hardware** (e 1,8-3,3 s in software), quindi un passo
 *    piu' largo costa **una frazione** di un tentativo in piu'.  Con 9 la scala
 *    e' 26 → 35 → 44 → 51, e comprende lo scalino che ce la faceva.
 *
 * ⚠ E IL VALORE ESATTO NON E' DECISO QUI: quanto in fretta scendere e' un punto
 *   di lavoro fra qualita' e banda, cioe' **fase 9**.  Qui si dichiara soltanto
 *   che **3 x 6 non bastava**, con il numero che lo dimostra.
 *
 * ⚠ E quanto sia raggiungibile va detto accanto, o il difetto sembra piu' grosso
 *   di quel che e': `[M]` alla tela dell'utente (2560x1080) la chiave piu' grossa
 *   su **404 chiavi vere** e' **21 433 byte**, cioe' lo **0,13 %** del tetto —
 *   margine **782x**.  ⇒ Difetto vero e dimostrato, e **non urgente**. */
#define CRF_DI_EMERGENZA 24
#define CRF_PASSO 9

/* ═══════════════════════════════════════════════════════════════════════════
 * IL LETTORE DI BIT — serve a rileggere quel che abbiamo appena prodotto
 *
 * ⛔ Esiste perche' il secondo testimone di E2 deve essere INDIPENDENTE dal
 *    primo: `AVCodecContext` dice quel che libavcodec crede di aver chiesto, e
 *    questo lettore dice quel che c'e' scritto nei byte.  Se i due divergono, e'
 *    il componente che ha disobbedito — ed e' successo davvero, `[M]` 12 agosto
 *    2026: libsvtav1 stampa «Error parsing option» su un'opzione che non conosce
 *    e **continua, uscendo 0**.
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	const uint8_t *dati;
	size_t byte;
	size_t bit;   /* posizione, in bit */
	bool finito;  /* ⛔ tre esiti, non due: «0» e «non ho potuto leggere» */
} LettoreBit;

static void lb_apri(LettoreBit *l, const uint8_t *dati, size_t byte)
{
	l->dati = dati;
	l->byte = byte;
	l->bit = 0;
	l->finito = false;
}

static uint32_t lb_bit(LettoreBit *l, int quanti)
{
	uint32_t v = 0;
	for (int i = 0; i < quanti; i++) {
		size_t indice = l->bit >> 3;
		if (indice >= l->byte) {
			l->finito = true;
			return v;
		}
		int scarto = 7 - (int) (l->bit & 7);
		v = (v << 1) | (uint32_t) ((l->dati[indice] >> scarto) & 1);
		l->bit++;
	}
	return v;
}

/* ⭐ Exp-Golomb CON SEGNO — serve all'SPS di H.264 (le liste di scala e gli
 *    scostamenti del conteggio d'ordine), e a HEVC qui non serviva.
 * ⛔ La mappatura e' quella dello standard (9.1.1): k → (-1)^(k+1) * ceil(k/2). */
static int32_t lb_se(LettoreBit *l);

/* Exp-Golomb senza segno, quello di H.265. */
static uint32_t lb_ue(LettoreBit *l)
{
	int zeri = 0;
	while (!l->finito && lb_bit(l, 1) == 0 && zeri < 32)
		zeri++;
	if (l->finito || zeri >= 32)
		return 0;
	return ((1u << zeri) - 1) + (zeri ? lb_bit(l, zeri) : 0);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ANNEX-B — camminare sui NAL, che e' quel che fa anche Chromium
 *
 * `[R]` `video_decoder.cc:206-214` chiama `media::mp4::HEVC::AnalyzeAnnexB()`
 * dopo ogni `configure()`/`flush()` e ⛔ **non si fida della nostra etichetta**:
 * se il chunk marcato `key` non contiene un IDR con i suoi parameter set,
 * rifiuta.  ⇒ Qui si fa la stessa cosa **prima di spedire**, invece di
 * scoprirlo in F2.5 dove il sintomo sarebbe «la pagina resta nera».
 * ═══════════════════════════════════════════════════════════════════════════ */
#define NAL_IDR_W_RADL 19
#define NAL_IDR_N_LP 20
#define NAL_CRA 21
#define NAL_VPS 32
#define NAL_SPS 33
#define NAL_PPS 34
#define NAL_VCL_MASSIMO 31

typedef struct {
	bool ha_vps, ha_sps, ha_pps;
	bool ha_idr;
	bool parametri_prima_dell_idr; /* ⛔ la meta' che si dimentica */
	bool primo_vcl_e_chiave;
	size_t sps_offset, sps_byte;
} FormaAnnexB;

/* Trova il prossimo codice di inizio: restituisce l'offset del primo byte del
 * NAL, o `byte` se non ce n'e' piu'.
 * ⛔ Si riconoscono TUTTI E DUE i codici, `00 00 01` e `00 00 00 01`: un lettore
 *    che ne conoscesse uno solo salterebbe meta' dei NAL **senza lamentarsi**, e
 *    direbbe «questo flusso non ha il PPS» di un flusso che ce l'ha.  Un falso
 *    rosso costa quanto un falso verde. */
static size_t annexb_prossimo(const uint8_t *d, size_t byte, size_t da, size_t *inizio_codice)
{
	for (size_t i = da; i + 2 < byte; i++) {
		if (d[i] == 0 && d[i + 1] == 0 && d[i + 2] == 1) {
			if (inizio_codice)
				*inizio_codice = (i >= 1 && d[i - 1] == 0) ? i - 1 : i;
			return i + 3;
		}
	}
	if (inizio_codice)
		*inizio_codice = byte;
	return byte;
}

static void annexb_leggi(const uint8_t *d, size_t byte, FormaAnnexB *f)
{
	memset(f, 0, sizeof(*f));
	bool visto_vcl = false;
	bool p_vps = false, p_sps = false, p_pps = false;
	size_t corpo = annexb_prossimo(d, byte, 0, NULL);
	while (corpo < byte) {
		size_t dove_dopo;
		size_t prossimo = annexb_prossimo(d, byte, corpo, &dove_dopo);
		size_t fine = (prossimo < byte) ? dove_dopo : byte;
		int tipo = (d[corpo] >> 1) & 0x3F;

		if (tipo == NAL_VPS) {
			f->ha_vps = true;
			p_vps = true;
		} else if (tipo == NAL_SPS) {
			f->ha_sps = true;
			p_sps = true;
			if (!f->sps_byte) {
				f->sps_offset = corpo;
				f->sps_byte = fine - corpo;
			}
		} else if (tipo == NAL_PPS) {
			f->ha_pps = true;
			p_pps = true;
		} else if (tipo <= NAL_VCL_MASSIMO) {
			bool chiave = (tipo == NAL_IDR_W_RADL || tipo == NAL_IDR_N_LP || tipo == NAL_CRA);
			if (!visto_vcl) {
				visto_vcl = true;
				f->primo_vcl_e_chiave = chiave;
			}
			if (chiave) {
				f->ha_idr = true;
				/* ⛔ Il gruppo dev'essere COMPLETO e stare PRIMA di questo
				 *    IDR, non da qualche parte nel flusso. */
				if (p_vps && p_sps && p_pps)
					f->parametri_prima_dell_idr = true;
			}
			p_vps = p_sps = p_pps = false;
		}
		corpo = prossimo;
	}
}

static int32_t lb_se(LettoreBit *l)
{
	uint32_t k = lb_ue(l);
	return (k & 1) ? (int32_t) ((k + 1) / 2) : -(int32_t) (k / 2);
}

/* Toglie gli emulation prevention byte: `00 00 03` → `00 00`.
 * ⛔ Senza questo passo un SPS che contenga quella sequenza si legge storto, e
 *    il numero che ne esce (la profondita' di bit) sarebbe sbagliato SENZA
 *    sembrarlo.  E' la stessa trappola che ISO/IEC 14496-15 mette nell'hvcC —
 *    una delle quattro ragioni per cui D1 sceglie Annex-B. */
static size_t togli_emulazione(const uint8_t *dentro, size_t byte, uint8_t *fuori, size_t massimo)
{
	size_t n = 0, zeri = 0;
	for (size_t i = 0; i < byte && n < massimo; i++) {
		if (zeri >= 2 && dentro[i] == 3) {
			zeri = 0;
			continue;
		}
		fuori[n++] = dentro[i];
		zeri = (dentro[i] == 0) ? zeri + 1 : 0;
	}
	return n;
}

static uint32_t rovescia32(uint32_t v)
{
	uint32_t r = 0;
	for (int i = 0; i < 32; i++) {
		r = (r << 1) | (v & 1);
		v >>= 1;
	}
	return r;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ H.264 — LA STESSA FORMA, CON I NUMERI DI UN ALTRO STANDARD
 *
 * ⛔ E i numeri sono diversi in un punto che si sbaglia una volta sola: in HEVC
 *    il tipo di NAL sta nei **sei bit** dopo il primo (`(b >> 1) & 0x3F`), in
 *    H.264 nei **cinque bit bassi** del primo (`b & 0x1F`).  Un lettore che
 *    usasse la formula sbagliata leggerebbe un IDR (5) come un NAL di tipo 2,
 *    cioe' direbbe «questa chiave non e' una chiave» **di una chiave vera**.
 *
 * ⚠ E i parameter set di H.264 sono DUE, non tre: non c'e' il VPS.  Chiedere
 *   anche quello rifiuterebbe ogni chiave valida.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define NAL264_NON_IDR 1
#define NAL264_IDR 5
#define NAL264_SPS 7
#define NAL264_PPS 8

typedef struct {
	bool ha_sps, ha_pps, ha_idr;
	bool parametri_prima_dell_idr;
	bool primo_vcl_e_chiave;
	size_t sps_offset, sps_byte;
} FormaAnnexB264;

static void annexb264_leggi(const uint8_t *d, size_t byte, FormaAnnexB264 *f)
{
	bool visto_vcl = false;
	bool p_sps = false, p_pps = false;
	size_t corpo;

	memset(f, 0, sizeof(*f));
	corpo = annexb_prossimo(d, byte, 0, NULL);
	while (corpo < byte) {
		size_t dove_dopo;
		size_t prossimo = annexb_prossimo(d, byte, corpo, &dove_dopo);
		size_t fine = (prossimo < byte) ? dove_dopo : byte;
		int tipo = d[corpo] & 0x1F;

		if (tipo == NAL264_SPS) {
			f->ha_sps = true;
			p_sps = true;
			if (!f->sps_byte) {
				f->sps_offset = corpo;
				f->sps_byte = fine - corpo;
			}
		} else if (tipo == NAL264_PPS) {
			f->ha_pps = true;
			p_pps = true;
		} else if (tipo >= NAL264_NON_IDR && tipo <= NAL264_IDR) {
			bool chiave = (tipo == NAL264_IDR);
			if (!visto_vcl) {
				visto_vcl = true;
				f->primo_vcl_e_chiave = chiave;
			}
			if (chiave) {
				f->ha_idr = true;
				if (p_sps && p_pps)
					f->parametri_prima_dell_idr = true;
			}
			p_sps = p_pps = false;
		}
		corpo = prossimo;
	}
}

/* Le liste di scala dell'SPS: non se ne legge il contenuto, si SALTANO — ma si
 * saltano leggendole, perche' sono a lunghezza variabile e chi le contasse a
 * byte sballerebbe tutto quel che viene dopo (cioe' la misura e la profondita').
 */
static void salta_liste_scala(LettoreBit *l, int quante)
{
	for (int i = 0; i < quante && !l->finito; i++) {
		if (!lb_bit(l, 1))
			continue;
		int misura = (i < 6) ? 16 : 64;
		int ultimo = 8, prossimo = 8;
		for (int j = 0; j < misura && !l->finito; j++) {
			if (prossimo)
				prossimo = (ultimo + lb_se(l) + 256) % 256;
			ultimo = prossimo ? prossimo : ultimo;
		}
	}
}

/*
 * ⭐ L'SPS di H.264 — e serve alle stesse due cose dell'SPS di HEVC: la
 *    profondita' VERA (il secondo testimone di E2) e il LIVELLO, che finisce
 *    nella stringa `avc1.<profilo><vincoli><livello>` che il browser riceve.
 *
 * ⛔ E la misura si legge fino al RITAGLIO.  Senza, una tela 1588x914 (non
 *    multipla di 16) si leggerebbe 1600x928 — cioe' il testimone accuserebbe di
 *    misura sbagliata un flusso giusto, che e' il falso rosso di `LEZIONI.md`
 *    §1.2.  ⚠ E le unita' del ritaglio dipendono dal sottocampionamento: 4:2:0
 *    conta due pixel per unita' in orizzontale e due in verticale.
 */
static bool leggi_sps_h264(const uint8_t *nal, size_t byte, CodificatoreConfessione *c)
{
	uint8_t *rbsp;
	size_t n;
	LettoreBit l;
	uint32_t profilo, livello, chroma = 1, largh_mb, alt_mapunit;
	uint32_t sotto_l = 2, sotto_a = 2;
	uint32_t taglio_sx = 0, taglio_dx = 0, taglio_su = 0, taglio_giu = 0;
	int solo_fotogrammi;

	if (byte < 5)
		return false;
	rbsp = malloc(byte);
	if (!rbsp)
		return false;
	/* ⛔ Il byte d'intestazione del NAL si salta PRIMA di togliere l'emulazione:
	 *    non fa parte dell'RBSP, e contarlo sposterebbe ogni bit di otto. */
	n = togli_emulazione(nal + 1, byte - 1, rbsp, byte);
	lb_apri(&l, rbsp, n);

	profilo = lb_bit(&l, 8);
	(void) lb_bit(&l, 8);        /* i vincoli + i bit riservati */
	livello = lb_bit(&l, 8);
	(void) lb_ue(&l);            /* seq_parameter_set_id */

	/* ⚠ Solo i profili «alti» portano il formato del croma e la profondita': su
	 *   Baseline/Main NON ci sono, e leggerli sposterebbe tutto il resto.  E'
	 *   l'elenco dello standard (7.3.2.1.1), scritto per esteso apposta. */
	if (profilo == 100 || profilo == 110 || profilo == 122 || profilo == 244 || profilo == 44
	    || profilo == 83 || profilo == 86 || profilo == 118 || profilo == 128 || profilo == 138
	    || profilo == 139 || profilo == 134 || profilo == 135) {
		chroma = lb_ue(&l);
		if (chroma == 3)
			(void) lb_bit(&l, 1);          /* separate_colour_plane_flag */
		c->profondita_flusso = 8 + (int) lb_ue(&l);   /* luma */
		(void) lb_ue(&l);                  /* croma: si legge e non si usa */
		(void) lb_bit(&l, 1);              /* qpprime_y_zero_transform_bypass */
		if (lb_bit(&l, 1))
			salta_liste_scala(&l, chroma == 3 ? 12 : 8);
	} else {
		/* ⛔ Non e' «8 bit per abitudine»: su questi profili lo standard
		 *    DICE 8 e 4:2:0, quindi e' un fatto letto, non un valore
		 *    predefinito (`CODER.md` §3.10). */
		c->profondita_flusso = 8;
		chroma = 1;
	}
	if (chroma == 0) { sotto_l = 1; sotto_a = 1; }
	else if (chroma == 2) { sotto_l = 2; sotto_a = 1; }
	else if (chroma == 3) { sotto_l = 1; sotto_a = 1; }

	(void) lb_ue(&l);                      /* log2_max_frame_num_minus4 */
	{
		uint32_t tipo_ordine = lb_ue(&l);
		if (tipo_ordine == 0) {
			(void) lb_ue(&l);
		} else if (tipo_ordine == 1) {
			(void) lb_bit(&l, 1);
			(void) lb_se(&l);
			(void) lb_se(&l);
			uint32_t quanti = lb_ue(&l);
			for (uint32_t i = 0; i < quanti && !l.finito && i < 256; i++)
				(void) lb_se(&l);
		}
	}
	(void) lb_ue(&l);                      /* max_num_ref_frames */
	(void) lb_bit(&l, 1);                  /* gaps_in_frame_num_value_allowed */
	largh_mb = lb_ue(&l) + 1;
	alt_mapunit = lb_ue(&l) + 1;
	solo_fotogrammi = (int) lb_bit(&l, 1);
	if (!solo_fotogrammi)
		(void) lb_bit(&l, 1);              /* mb_adaptive_frame_field_flag */
	(void) lb_bit(&l, 1);                  /* direct_8x8_inference_flag */
	if (lb_bit(&l, 1)) {                   /* frame_cropping_flag */
		taglio_sx = lb_ue(&l);
		taglio_dx = lb_ue(&l);
		taglio_su = lb_ue(&l);
		taglio_giu = lb_ue(&l);
	}
	free(rbsp);
	if (l.finito)
		return false;

	c->profilo_flusso = (int) profilo;
	c->livello_flusso = (int) livello;
	{
		uint32_t unita_l = (chroma == 0) ? 1 : sotto_l;
		uint32_t unita_a = (uint32_t) ((chroma == 0 ? 1 : sotto_a) * (2 - solo_fotogrammi));
		uint32_t larghezza = largh_mb * 16;
		uint32_t altezza = alt_mapunit * 16 * (uint32_t) (2 - solo_fotogrammi);
		uint32_t via_l = (taglio_sx + taglio_dx) * unita_l;
		uint32_t via_a = (taglio_su + taglio_giu) * unita_a;

		c->larghezza_flusso = (larghezza > via_l) ? larghezza - via_l : larghezza;
		c->altezza_flusso = (altezza > via_a) ? altezza - via_a : altezza;
	}
	return true;
}

/*
 * ⭐ L'SPS di HEVC, letto per intero fino alla profondita' di bit.
 *
 * ⛔ Perche' non basta `ffprobe`: `ffprobe` non c'e' dentro il server.  E
 *    perche' non basta `ctx->pix_fmt`: quello e' quel che abbiamo CHIESTO.  La
 *    profondita' vera e' scritta nell'SPS, ed e' quella che il decodificatore
 *    del browser leggera'.
 *
 * ⭐ E di passaggio esce il **livello**, che serve per `RCP.md` §4.3
 *    (`video.livello`: il server DEVE emettere un flusso di livello non
 *    superiore a quello dichiarato dal client, e **non lo indovina**) e per la
 *    stringa `hev1.2.4.L93.B0` di `VideoDecoder.configure()`.
 */
static bool leggi_sps_hevc(const uint8_t *nal, size_t byte, CodificatoreConfessione *c)
{
	if (byte < 4)
		return false;
	uint8_t *rbsp = malloc(byte);
	if (!rbsp)
		return false;
	size_t n = togli_emulazione(nal + 2, byte - 2, rbsp, byte); /* 2 = intestazione NAL */

	LettoreBit l;
	lb_apri(&l, rbsp, n);
	lb_bit(&l, 4);                              /* sps_video_parameter_set_id */
	uint32_t max_sub = lb_bit(&l, 3);           /* sps_max_sub_layers_minus1 */
	lb_bit(&l, 1);                              /* sps_temporal_id_nesting_flag */

	/* profile_tier_level(1, max_sub) */
	uint32_t spazio = lb_bit(&l, 2);
	uint32_t tier = lb_bit(&l, 1);
	uint32_t profilo = lb_bit(&l, 5);
	uint32_t compat = lb_bit(&l, 32);
	uint8_t vincoli[6];
	for (int i = 0; i < 6; i++)
		vincoli[i] = (uint8_t) lb_bit(&l, 8); /* 48 bit: i flag di sorgente e i riservati */
	uint32_t livello = lb_bit(&l, 8);

	uint32_t prof_presente[8] = { 0 }, liv_presente[8] = { 0 };
	for (uint32_t i = 0; i < max_sub; i++) {
		prof_presente[i] = lb_bit(&l, 1);
		liv_presente[i] = lb_bit(&l, 1);
	}
	if (max_sub > 0)
		for (uint32_t i = max_sub; i < 8; i++)
			lb_bit(&l, 2); /* reserved_zero_2bits */
	for (uint32_t i = 0; i < max_sub; i++) {
		if (prof_presente[i]) {
			lb_bit(&l, 2); lb_bit(&l, 1); lb_bit(&l, 5);
			lb_bit(&l, 32);
			for (int k = 0; k < 6; k++)
				lb_bit(&l, 8);
		}
		if (liv_presente[i])
			lb_bit(&l, 8);
	}

	lb_ue(&l);                                  /* sps_seq_parameter_set_id */
	uint32_t croma = lb_ue(&l);                 /* chroma_format_idc */
	if (croma == 3)
		lb_bit(&l, 1);                          /* separate_colour_plane_flag */
	uint32_t larghezza = lb_ue(&l);
	uint32_t altezza = lb_ue(&l);
	uint32_t codificata_l = larghezza, codificata_a = altezza;
	/*
	 * ⛔⭐ LA FINESTRA DI CONFORMITA' SI APPLICA — e fino al 13 agosto 2026 questa
	 *     lettura la SALTAVA (quattro `lb_ue()` buttati via).
	 *
	 * ⚠ Non si era mai visto perche' `libx265` a 1920×1080 non ne mette una: 1080
	 *   e' multiplo di 8 e ci sta senza riempimento.  ⛔ `hevc_vaapi` **su AMD**
	 *   (radeonsi, navi21) codifica **1920×1088** e ritaglia a 1080 con la
	 *   finestra — e il controllo di `forma_va_bene()` rifiutava OGNI fotogramma
	 *   dicendo *«il flusso dichiara 1920x1088 e la tela e' 1920x1080»*.
	 *
	 * ⇒ ⭐ Il difetto era del LETTORE, non del codificatore, e si e' visto solo
	 *   perche' il controllo c'era.  ⚠ Le due grandezze restano DUE — quel che si
	 *   codifica e quel che si mostra — e si scrivono tutte e due: un giorno la
	 *   differenza costera' banda, e allora si vorra' sapere che c'e'.
	 *
	 * `[S]` H.265 §7.4.3.2: gli scarti sono in unita' di croma, cioe' vanno
	 * moltiplicati per SubWidthC/SubHeightC.
	 */
	if (lb_bit(&l, 1)) {                        /* conformance_window_flag */
		uint32_t sinistra = lb_ue(&l), destra = lb_ue(&l);
		uint32_t sopra = lb_ue(&l), sotto = lb_ue(&l);
		uint32_t sub_l = (croma == 1 || croma == 2) ? 2 : 1;
		uint32_t sub_a = (croma == 1) ? 2 : 1;
		uint32_t taglio_l = sub_l * (sinistra + destra);
		uint32_t taglio_a = sub_a * (sopra + sotto);
		/* ⚠ Un taglio piu' grande dell'immagine non si sottrae: si lascia stare e
		 *   il chiamante vedra' una misura che non combacia, che e' meglio di un
		 *   numero che va sotto zero e diventa enorme. */
		if (taglio_l < larghezza)
			larghezza -= taglio_l;
		if (taglio_a < altezza)
			altezza -= taglio_a;
	}
	uint32_t bit_luma = lb_ue(&l) + 8;
	uint32_t bit_croma = lb_ue(&l) + 8;
	free(rbsp);

	if (l.finito)
		return false;

	c->profondita_flusso = (int) (bit_luma < bit_croma ? bit_luma : bit_croma);
	c->profilo_flusso = (int) profilo;
	c->livello_flusso = (int) livello;
	c->tier_alto = tier != 0;
	c->larghezza_flusso = larghezza;
	c->altezza_flusso = altezza;
	c->larghezza_codificata = codificata_l;
	c->altezza_codificata = codificata_a;
	c->croma_flusso = (int) croma;

	/* ⭐ La stringa per `VideoDecoder.configure()`, costruita dai byte veri.
	 *   ⛔ `hev1` e non `hvc1`: i parameter set viaggiano in banda.  ⚠ E `[M]`
	 *      F2.5 ha misurato che **il prefisso non conta**: Chromium decide dalla
	 *      presenza della `description`, non dal prefisso.  Si scrive `hev1`
	 *      lo stesso, perche' e' quello che descrive la verita' del flusso. */
	char vincoli_testo[24] = { 0 };
	int ultimo = -1;
	for (int i = 0; i < 6; i++)
		if (vincoli[i])
			ultimo = i;
	for (int i = 0; i <= ultimo; i++) {
		char pezzo[8];
		snprintf(pezzo, sizeof(pezzo), ".%02X", vincoli[i]);
		strncat(vincoli_testo, pezzo, sizeof(vincoli_testo) - strlen(vincoli_testo) - 1);
	}
	char spazio_testo[2] = { 0 };
	if (spazio > 0)
		spazio_testo[0] = (char) ('A' + spazio - 1);
	snprintf(c->stringa_codec, sizeof(c->stringa_codec), "hev1.%s%u.%X.%c%u%s",
	         spazio_testo, profilo, rovescia32(compat), tier ? 'H' : 'L', livello,
	         vincoli_testo);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * AV1 — le unita' temporali di OBU
 *
 * ⚠ Qui non c'e' nessun `hvcC` da cui difendersi: AV1 «prende le unita'
 *   temporali cosi' come sono» (`DECISIONI.md` §1.13).  ⛔ Ma la meta' che si
 *   dimentica e' identica: la **sequence header OBU** deve stare davanti a ogni
 *   fotogramma chiave, o un client che si collega dopo riceve una chiave nuda —
 *   lo stesso schermo nero con i fotogrammi che arrivano.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define OBU_SEQUENCE_HEADER 1
#define OBU_TEMPORAL_DELIMITER 2
#define OBU_FRAME_HEADER 3
#define OBU_FRAME 6

typedef struct {
	bool ha_sequenza;
	bool ha_chiave;
	bool sequenza_prima_della_chiave;
	bool primo_fotogramma_e_chiave;
	size_t seq_offset, seq_byte;
} FormaObu;

static uint64_t leggi_leb128(const uint8_t *d, size_t byte, size_t *dove)
{
	uint64_t v = 0;
	for (int i = 0; i < 8 && *dove < byte; i++) {
		uint8_t b = d[(*dove)++];
		v |= (uint64_t) (b & 0x7F) << (i * 7);
		if (!(b & 0x80))
			break;
	}
	return v;
}

static void obu_leggi(const uint8_t *d, size_t byte, FormaObu *f)
{
	memset(f, 0, sizeof(*f));
	bool visto_fotogramma = false, seq_in_corso = false;
	size_t i = 0;
	while (i < byte) {
		size_t inizio = i;
		uint8_t testa = d[i++];
		int tipo = (testa >> 3) & 0xF;
		bool estensione = (testa >> 2) & 1;
		bool ha_taglia = (testa >> 1) & 1;
		if (estensione && i < byte)
			i++;
		uint64_t taglia;
		if (ha_taglia)
			taglia = leggi_leb128(d, byte, &i);
		else
			taglia = byte - i; /* ⚠ senza campo taglia l'OBU arriva a fine buffer */
		if (i + taglia > byte)
			taglia = byte - i;

		if (tipo == OBU_SEQUENCE_HEADER) {
			f->ha_sequenza = true;
			seq_in_corso = true;
			if (!f->seq_byte) {
				f->seq_offset = i;
				f->seq_byte = (size_t) taglia;
			}
		} else if (tipo == OBU_FRAME || tipo == OBU_FRAME_HEADER) {
			LettoreBit l;
			lb_apri(&l, d + i, (size_t) taglia);
			bool chiave = false;
			if (lb_bit(&l, 1) == 0)                 /* show_existing_frame */
				chiave = (lb_bit(&l, 2) == 0);      /* frame_type: 0 = KEY_FRAME */
			if (!visto_fotogramma) {
				visto_fotogramma = true;
				f->primo_fotogramma_e_chiave = chiave;
			}
			if (chiave) {
				f->ha_chiave = true;
				if (seq_in_corso)
					f->sequenza_prima_della_chiave = true;
			}
			seq_in_corso = false;
		}
		i += (size_t) taglia;
		if (i <= inizio)
			break; /* ⛔ un OBU di taglia zero fermerebbe il giro qui invece che mai */
	}
}

/* La sequence header OBU, fino alla profondita' di bit.  Segue AV1 §5.5. */
static bool leggi_sequenza_av1(const uint8_t *d, size_t byte, CodificatoreConfessione *c)
{
	LettoreBit l;
	lb_apri(&l, d, byte);
	uint32_t profilo = lb_bit(&l, 3);
	lb_bit(&l, 1); /* still_picture */
	uint32_t ridotta = lb_bit(&l, 1);
	uint32_t livello = 0, tier = 0;
	uint32_t modello_decodifica = 0, ritardo_iniziale = 0;

	if (ridotta) {
		livello = lb_bit(&l, 5);
	} else {
		if (lb_bit(&l, 1)) {              /* timing_info_present_flag */
			lb_bit(&l, 32); lb_bit(&l, 32);
			if (lb_bit(&l, 1) == 0) {     /* equal_picture_interval */
				/* uvlc(): niente da conservare */
				int zeri = 0;
				while (!l.finito && lb_bit(&l, 1) == 0 && zeri < 32)
					zeri++;
				if (zeri && zeri < 32)
					lb_bit(&l, zeri);
			}
			modello_decodifica = lb_bit(&l, 1);
			if (modello_decodifica) {
				lb_bit(&l, 5); lb_bit(&l, 32); lb_bit(&l, 5); lb_bit(&l, 5);
			}
		}
		ritardo_iniziale = lb_bit(&l, 1);
		uint32_t quanti = lb_bit(&l, 5);
		for (uint32_t k = 0; k <= quanti; k++) {
			lb_bit(&l, 12);               /* operating_point_idc */
			uint32_t liv = lb_bit(&l, 5);
			uint32_t ti = 0;
			if (liv > 7)
				ti = lb_bit(&l, 1);
			if (k == 0) {
				livello = liv;
				tier = ti;
			}
			if (modello_decodifica && lb_bit(&l, 1)) {
				/* operating_parameters_info: due ritardi e un flag.  ⚠ La
				 * lunghezza dipende da buffer_delay_length, che qui non
				 * conserviamo: se questo ramo si accendesse, la lettura
				 * diventerebbe inaffidabile e il chiamante lo vede da
				 * `letto_dal_flusso = false`. */
				return false;
			}
			if (ritardo_iniziale && lb_bit(&l, 1))
				lb_bit(&l, 4);
		}
	}
	uint32_t bit_l = lb_bit(&l, 4) + 1;
	uint32_t bit_a = lb_bit(&l, 4) + 1;
	uint32_t larghezza = lb_bit(&l, (int) bit_l) + 1;
	uint32_t altezza = lb_bit(&l, (int) bit_a) + 1;

	if (!ridotta && lb_bit(&l, 1)) { /* frame_id_numbers_present_flag */
		lb_bit(&l, 4);
		lb_bit(&l, 3);
	}
	lb_bit(&l, 1); /* use_128x128_superblock */
	lb_bit(&l, 1); /* enable_filter_intra */
	lb_bit(&l, 1); /* enable_intra_edge_filter */
	if (!ridotta) {
		lb_bit(&l, 1); /* enable_interintra_compound */
		lb_bit(&l, 1); /* enable_masked_compound */
		lb_bit(&l, 1); /* enable_warped_motion */
		lb_bit(&l, 1); /* enable_dual_filter */
		uint32_t ordine = lb_bit(&l, 1);
		if (ordine) {
			lb_bit(&l, 1); /* enable_jnt_comp */
			lb_bit(&l, 1); /* enable_ref_frame_mvs */
		}
		uint32_t forza = 2;
		if (lb_bit(&l, 1) == 0)          /* seq_choose_screen_content_tools */
			forza = lb_bit(&l, 1);
		if (forza > 0 && lb_bit(&l, 1) == 0)
			lb_bit(&l, 1);               /* seq_force_integer_mv */
		if (ordine)
			lb_bit(&l, 3);               /* order_hint_bits_minus_1 */
	}
	lb_bit(&l, 1); /* enable_superres */
	lb_bit(&l, 1); /* enable_cdef */
	lb_bit(&l, 1); /* enable_restoration */

	/* color_config() */
	uint32_t alto = lb_bit(&l, 1);
	int profondita;
	if (profilo == 2 && alto)
		profondita = lb_bit(&l, 1) ? 12 : 10;
	else
		profondita = alto ? 10 : 8;

	if (l.finito)
		return false;

	c->profondita_flusso = profondita;
	c->profilo_flusso = (int) profilo;
	c->livello_flusso = (int) livello;
	c->tier_alto = tier != 0;
	c->larghezza_flusso = larghezza;
	c->altezza_flusso = altezza;
	c->croma_flusso = 1; /* ⚠ i due formati che libsvtav1 accetta sono 4:2:0 */

	/* ⚠ `seq_level_idx = 4` NON e' «livello 4»: e' il 3.0 — nella stringa va
	 *   l'INDICE (`DECISIONI.md` §1.13). */
	snprintf(c->stringa_codec, sizeof(c->stringa_codec), "av01.%u.%02u%c.%02d",
	         profilo, livello, tier ? 'H' : 'M', profondita);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════ */

/* ⛔ Quante importazioni di DMA-BUF si tengono in cache.  ⚠ Il numero non e' di
 *    comodo: il produttore ricicla `[M]` **quattro** buffer (`DECISIONI.md`
 *    §2.3-ter) e sulla strada della scheda gliene chiediamo **sei**, perche' la
 *    ritenuta ne toglie due.  Otto tiene tutti i casi con margine, e quando la
 *    cache e' piena si ricomincia da capo invece di sfrattare a caso: una
 *    politica sbagliata su otto voci costerebbe piu' righe di quel che rende. */
#define IMPORTATE_MAX 8

/* ⛔ Il numero sta in UN posto solo, con la misura accanto in `codificatore.h`.
 *    ⚠ Non e' un multiplo scelto per prudenza: e' il confine misurato al pixel
 *    fra 1552 (che legge) e 1544 (che non legge). */
#define ALLINEAMENTO_SCHEDA 64u


struct Codificatore {
	CodificatoreRichiesta richiesta;
	const AVCodec *componente;
	AVCodecContext *ctx;
	AVFrame *fotogramma;
	AVPacket *pacchetto;
	struct SwsContext *conversione;
	CodificatoreConfessione conf;
	/* ⚠ 320 e non 160: dentro ci sta il fornitore VA per esteso — «Intel iHD
	 *   driver for Intel(R) Gen Graphics - 25.2.3 ()» sono gia' 53 byte.  Un nome
	 *   troncato nel registro toglie proprio il pezzo che dice QUALE macchina ha
	 *   fatto il numero. */
	char nome[320];

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐ LA META' IN HARDWARE.  ⚠ Tutti NULL/false quando si codifica in
	 *    software, e il codice che segue lo controlla su `hardware` — non sulla
	 *    presenza di uno di questi, che sarebbe la stessa cosa scritta in un
	 *    posto dove un giorno non lo sara' piu'.
	 */
	bool hardware;
	AVBufferRef *dispositivo;     /* AVHWDeviceContext (VAAPI) */
	AVBufferRef *magazzino;       /* AVHWFramesContext: le superfici della GPU */
	enum AVPixelFormat formato_gpu; /* P010LE a 10 bit, NV12 a 8 */
	AVFrame *appoggio;            /* il fotogramma in memoria di sistema */

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐⭐⭐ LA COPIA ZERO — le tre cose che servono, e nient'altro
	 *
	 *   1. il CONTESTO VPP: la conversione RGB → NV12 fatta dalla GPU, che
	 *      prende il posto di `sws_scale` **e** di `av_hwframe_transfer_data`
	 *      insieme.  ⛔ Vive sul DISPOSITIVO e non sul contesto del
	 *      codificatore: `abbassa_qualita()` richiude e riapre il codificatore
	 *      tre volte di fila per una chiave sopra il tetto, e rifare il VPP a
	 *      ogni giro sarebbe lavoro fatto per niente;
	 *   2. la CACHE delle importazioni: `vaCreateSurfaces` su un DMA-BUF non e'
	 *      gratis, e il produttore ricicla sempre gli stessi pochi buffer.  ⇒ Si
	 *      importa una volta per buffer, non una volta per fotogramma;
	 *   3. la GENERAZIONE con cui la cache e' nata.  ⛔ Senza, dopo una
	 *      rinegoziazione si darebbe a VA-API una superficie che punta a un
	 *      buffer liberato: i numeri di descrittore si riciclano, e il sintomo
	 *      sarebbe **un'immagine vecchia** senza nessun errore.
	 */
	VAConfigID vpp_configurazione;
	VAContextID vpp_contesto;
	bool vpp_aperto;
	uint32_t vpp_l, vpp_a;        /* la misura per cui il VPP e' stato aperto */
	struct {
		int fd;
		uint32_t l, a, stride, offset, formato_drm;
		uint64_t modificatore;
		VASurfaceID superficie;
	} importate[IMPORTATE_MAX];
	unsigned quante_importate;
	uint64_t generazione_cache;
	bool cache_nata;
	bool detto_copia_zero;        /* la riga della prima volta, una volta sola */

	bool prossimo_chiave;         /* ⛔ la prossima e' una chiave VERA */
	bool prima_codifica_fatta;
	bool svuotato;                /* ⚠ e' stato messo in scarico: va riaperto */
	int qualita_corrente;         /* CRF in vigore, dopo le eventuali ricodifiche */
	ModoQualita modo_corrente;
	int64_t numero;               /* il pts, che qui e' il contatore dei fotogrammi */
	bool pacchetto_in_mano;
};

/* ⚠ Dichiarate qui e definite col resto della copia zero, molto piu' sotto:
 *   `codificatore_libera()` sta in mezzo e le deve chiamare.  ⛔ Spostare la
 *   loro definizione qui sopra separerebbe la conversione sulla GPU dal suo
 *   riquadro, che e' il posto in cui e' spiegata. */
static void butta_le_importate(Codificatore *c, const char *perche);
static void chiudi_vpp(Codificatore *c);

static uint64_t adesso_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000u + (uint64_t) t.tv_nsec / 1000u;
}

static void di(char *dove, size_t quanto, const char *fmt, ...)
{
	if (!dove || !quanto)
		return;
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(dove, quanto, fmt, ap);
	va_end(ap);
}

/*
 * ⛔ IL NOME PREDEFINITO E' UN NOME, non «lascia scegliere a libavcodec».
 *
 * `libx265` e' l'unico codificatore HEVC **in software** che ffmpeg di Debian
 * Trixie porta (`--enable-libx265`); gli altri quattro — `hevc_vaapi`,
 * `hevc_qsv`, `hevc_nvenc`, `hevc_vulkan` — sono tutti in hardware, cioe' la
 * fase 8 entrata di soppiatto nella fase 2.
 *
 * `libsvtav1` fra i tre AV1 in software di Trixie, e la ragione e' **misurata**
 * `[M]` 12 agosto 2026, stessa scena 1920×1080 a 10 bit, tutti fotogrammi
 * chiave:
 *
 *     libsvtav1     99–390 ms per fotogramma (preset 12 → 8)
 *     librav1e      2 347 ms per UN fotogramma        ⇒ 15× piu' lento
 *     libaom-av1    ⛔ non ha finito UN fotogramma in 95 s
 *
 * ⛔ E il numero conta perche' `DECISIONI.md` §1.13 lascia aperta proprio quella
 *    `[?]`: *«il ritmo di AV1 in software e' la domanda che decide se il ripiego
 *    e' usabile o solo esistente»*.  Con libaom il ripiego sarebbe **solo
 *    esistente**.
 */
static const char *nome_predefinito(CodecVideo codec)
{
	switch (codec) {
	case CODIFICATORE_HEVC:
		return "libx265";
	/* ⚠ `libx264` come `libx265`: e' il RIPIEGO in software, e sulla macchina
	 *   di prova non si percorre — H.264 va in hardware (`h264_vaapi`).  La
	 *   scelta della licenza e' la stessa gia' fatta per HEVC, non una nuova. */
	case CODIFICATORE_H264:
		return "libx264";
	default:
		return "libsvtav1";
	}
}

static enum AVCodecID id_di(CodecVideo codec)
{
	switch (codec) {
	case CODIFICATORE_HEVC:
		return AV_CODEC_ID_HEVC;
	case CODIFICATORE_H264:
		return AV_CODEC_ID_H264;
	default:
		return AV_CODEC_ID_AV1;
	}
}

/* ⛔ Il nome per il registro sta in UN posto solo: fino al 20 agosto 2026 era
 *    un `? :` ripetuto in sei righe, e col terzo codec ognuna avrebbe detto
 *    «AV1» di un flusso H.264 — sei bugie da correggere una per una. */
static const char *nome_codec(CodecVideo codec)
{
	switch (codec) {
	case CODIFICATORE_HEVC:
		return "HEVC";
	case CODIFICATORE_H264:
		return "H.264";
	case CODIFICATORE_AV1:
		return "AV1";
	default:
		return "codec ignoto";
	}
}

/*
 * ⛔ «E' in hardware?» si CHIEDE AL COMPONENTE, non si legge nel nome.
 *
 * ⚠ Un `strstr(nome, "_vaapi")` sarebbe la stessa cosa scritta male: il giorno
 *   in cui si provasse `hevc_qsv` o `hevc_vulkan` la riga direbbe «software» di
 *   un codificatore in hardware, e il sintomo sarebbe swscale che converte
 *   verso un formato che il componente non accetta — cioe' un errore che non
 *   nomina ne' la GPU ne' il nome.  ⇒ Si guarda quel che DICHIARA: un
 *   codificatore in hardware accetta un formato di superficie, non di pixel.
 */
static bool componente_e_hardware(const AVCodec *c, enum AVPixelFormat *quale)
{
	const enum AVPixelFormat *elenco = NULL;
	if (avcodec_get_supported_config(NULL, c, AV_CODEC_CONFIG_PIX_FORMAT, 0,
	                                 (const void **) &elenco, NULL) < 0 || !elenco)
		return false;
	for (int i = 0; elenco[i] != AV_PIX_FMT_NONE; i++) {
		const AVPixFmtDescriptor *d = av_pix_fmt_desc_get(elenco[i]);
		if (d && (d->flags & AV_PIX_FMT_FLAG_HWACCEL)) {
			if (quale)
				*quale = elenco[i];
			return true;
		}
	}
	return false;
}

static bool accetta_formato(const AVCodec *c, enum AVPixelFormat voluto)
{
	const enum AVPixelFormat *elenco = NULL;
	if (avcodec_get_supported_config(NULL, c, AV_CODEC_CONFIG_PIX_FORMAT, 0,
	                                 (const void **) &elenco, NULL) < 0)
		return false;
	if (!elenco)
		return true; /* «tutti» */
	for (int i = 0; elenco[i] != AV_PIX_FMT_NONE; i++)
		if (elenco[i] == voluto)
			return true;
	return false;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐ LA GPU — E SI APRE SU UN NODO DICHIARATO, CON UN ENTRYPOINT DICHIARATO
 *
 * ⛔ Le due cose che questo blocco NON fa, e sono le due che costerebbero:
 *
 *    1. **non sceglie il nodo**.  `[M]` 13 agosto 2026 i due nodi della
 *       macchina di prova sono di due fornitori diversi (Intel iHD su
 *       `renderD128`, AMD radeonsi su `renderD129`) e con due entrypoint
 *       diversi.  Un codice che aprisse «il primo che c'e'» misurerebbe una
 *       macchina a caso, e il numero non direbbe quale;
 *    2. **non si fida di aver chiesto**.  Fra «ho passato `low_power=1` a
 *       libavcodec» e «il driver ha quell'entrypoint» c'e' la stessa distanza
 *       che fra `-svtav1-params lossless=1` e un flusso senza perdita — cioe'
 *       una stampa di errore e un'uscita 0 (`[M]` 12 agosto).  ⇒ La coppia
 *       (profilo, entrypoint) si legge dal driver con
 *       `vaQueryConfigEntrypoints` **prima** di aprire.
 * ═══════════════════════════════════════════════════════════════════════════ */

static VAProfile profilo_va(CodecVideo codec, int profondita)
{
	if (codec == CODIFICATORE_HEVC)
		return profondita == 10 ? VAProfileHEVCMain10 : VAProfileHEVCMain;
	/* ⛔ H.264 QUI E' A 8 BIT E BASTA, e si dichiara invece di provare:
	 *    `High10` esiste nello standard ma `[M]` `vainfo` su questa macchina
	 *    porta `VAProfileH264High` e non il 10 bit — e chi chiedesse 10 bit
	 *    otterrebbe `VAProfileNone`, cioe' il ripiego in software, con lo
	 *    stesso nome e un ritmo dieci volte peggiore (la forma E2). */
	if (codec == CODIFICATORE_H264)
		return profondita == 10 ? VAProfileNone : VAProfileH264High;
	return VAProfileNone;
}

/*
 * ⛔ TRE ESITI, NON DUE: `c'e'`, `non c'e'`, `non ho potuto guardare`.
 * `LEZIONI.md` §1.9 regola 1 — «vuoto» e «proibito» hanno lo stesso aspetto.
 */
typedef enum { EP_C_E, EP_NON_C_E, EP_NON_GUARDATO } EsitoEntrypoint;

static EsitoEntrypoint entrypoint_c_e(VADisplay d, VAProfile p, VAEntrypoint voluto,
                                      char *visti, size_t visti_byte)
{
	int massimo = vaMaxNumEntrypoints(d);
	if (massimo <= 0)
		return EP_NON_GUARDATO;
	VAEntrypoint *elenco = calloc((size_t) massimo, sizeof(*elenco));
	if (!elenco)
		return EP_NON_GUARDATO;
	int quanti = 0;
	VAStatus st = vaQueryConfigEntrypoints(d, p, elenco, &quanti);
	if (st != VA_STATUS_SUCCESS) {
		free(elenco);
		return EP_NON_GUARDATO;
	}
	EsitoEntrypoint esito = EP_NON_C_E;
	if (visti && visti_byte)
		visti[0] = 0;
	for (int i = 0; i < quanti; i++) {
		if (visti && visti_byte) {
			char pezzo[24];
			snprintf(pezzo, sizeof(pezzo), "%s%d", i ? "," : "", (int) elenco[i]);
			strncat(visti, pezzo, visti_byte - strlen(visti) - 1);
		}
		if (elenco[i] == voluto)
			esito = EP_C_E;
	}
	free(elenco);
	return esito;
}

/*
 * Apre il dispositivo VA-API sul nodo dichiarato, ne legge il FORNITORE, e
 * verifica che (profilo, entrypoint) esista davvero prima di aprire.
 */
static int apri_dispositivo(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;

	if (!r->nodo_rendering || !r->nodo_rendering[0]) {
		di(errore, errore_byte,
		   "«%s» e' un codificatore in HARDWARE e non e' stato dichiarato nessun "
		   "nodo di rendering: ⛔ non se ne indovina uno — su questa macchina i due "
		   "nodi sono di due fornitori diversi [M]", c->componente->name);
		return -1;
	}
	if (r->potenza == CODIFICATORE_POTENZA_NON_DICHIARATA) {
		di(errore, errore_byte,
		   "«%s»: l'entrypoint non e' stato dichiarato.  ⛔ `EncSliceLP` (bassa "
		   "potenza) e `EncSlice` (piena) NON sono equivalenti, e il difetto di "
		   "libavcodec (piena) non si eredita: si chiede PIENA o BASSA",
		   c->componente->name);
		return -1;
	}

	int esito = av_hwdevice_ctx_create(&c->dispositivo, AV_HWDEVICE_TYPE_VAAPI,
	                                   r->nodo_rendering, NULL, 0);
	if (esito < 0) {
		char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
		av_strerror(esito, testo, sizeof(testo));
		di(errore, errore_byte, "VA-API non si e' aperta su «%s»: %s",
		   r->nodo_rendering, testo);
		return -1;
	}

	AVHWDeviceContext *dc = (AVHWDeviceContext *) c->dispositivo->data;
	AVVAAPIDeviceContext *va = dc->hwctx;
	const char *fornitore = vaQueryVendorString(va->display);
	snprintf(c->conf.nodo, sizeof(c->conf.nodo), "%s", r->nodo_rendering);
	snprintf(c->conf.fornitore_va, sizeof(c->conf.fornitore_va), "%s",
	         fornitore ? fornitore : "(il driver non dice il suo nome)");

	VAProfile profilo = profilo_va(r->codec, r->profondita);
	if (profilo == VAProfileNone) {
		di(errore, errore_byte,
		   "in hardware si sa aprire solo HEVC: per AV1 la codifica in hardware su "
		   "questa macchina NON ESISTE [M] — `av1_vaapi` esce 218, «No usable "
		   "encoding profile found», 3 giri su 3");
		return -1;
	}
	VAEntrypoint voluto = (r->potenza == CODIFICATORE_POTENZA_BASSA)
	                          ? VAEntrypointEncSliceLP
	                          : VAEntrypointEncSlice;
	char visti[128] = { 0 };
	switch (entrypoint_c_e(va->display, profilo, voluto, visti, sizeof(visti))) {
	case EP_C_E:
		c->conf.bassa_potenza = (r->potenza == CODIFICATORE_POTENZA_BASSA);
		c->conf.bassa_potenza_verificata = true;
		break;
	case EP_NON_C_E:
		di(errore, errore_byte,
		   "su «%s» (%s) il profilo %d NON ha l'entrypoint %s: il driver ne "
		   "dichiara [%s].  ⛔ Non si ripiega sull'altro — sono due codifiche "
		   "diverse, e ripiegare darebbe due misure sotto la stessa etichetta",
		   r->nodo_rendering, c->conf.fornitore_va, (int) profilo,
		   voluto == VAEntrypointEncSliceLP ? "EncSliceLP (bassa potenza)"
		                                    : "EncSlice (piena)",
		   visti[0] ? visti : "nessuno");
		return -1;
	case EP_NON_GUARDATO:
	default:
		di(errore, errore_byte,
		   "su «%s» NON ho potuto leggere gli entrypoint del profilo %d: ⛔ non e' "
		   "«non ce n'e'», e' «non ho guardato», e non si codifica su una macchina "
		   "che non si e' potuta interrogare",
		   r->nodo_rendering, (int) profilo);
		return -1;
	}

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⭐⭐ E LA MISURA MASSIMA SI CHIEDE **AL DRIVER**, non al primo fotogramma
	 *
	 * ⛔ IL FATTO, `[M]` 22 agosto 2026 (agente D): `h264_vaapi` su `EncSliceLP`
	 *    accetta **32-4096 px per lato** — 4096x2160 si', **4112x2160 no**
	 *    (*«Hardware does not support encoding at size…»*).  `hevc_vaapi` regge
	 *    invece fino a 16384x4320.
	 *    ⚠ E la tela legale di `RCP.md` §4.5 arriva a **7680x4320** ⇒ oltre i
	 *      4096 px il ripiego `libx264` non e' un'eventualita', **e' la regola**,
	 *      e a 8K costa `[M]` **309 ms per chiave**.
	 *
	 * ⇒ Senza questa domanda il rifiuto arriva **al primo fotogramma**, cioe'
	 *   dopo che il palco e' montato e qualcuno sta gia' guardando: e' la forma
	 *   di `LEZIONI.md` §1.8 — *si dichiara invece di subire*.  Qui invece
	 *   `codificatore_nuovo()` fallisce **prima**, dicendo il numero del driver,
	 *   e `figlio.c` scrive il ripiego con la sua riga.
	 *
	 * ⛔⛔ E SI CHIEDE AL DRIVER E NON A FFMPEG, che e' la stessa lezione presa
	 *      dall'altro capo: `[M]` **`-low_power 0` sull'Intel apre lo stesso
	 *      `EncSliceLP`, e ffmpeg NON fallisce** — prende quel che c'e'.  ⇒ Una
	 *      verifica fatta passando dalla riga di comando darebbe due misure
	 *      sotto la stessa etichetta (`LEZIONI.md` §1.11).
	 *
	 * ⚠ TRE ESITI E NON DUE, come per gli entrypoint: se il driver non dichiara
	 *   l'attributo (`VA_ATTRIB_NOT_SUPPORTED`) **non si conclude niente** — non
	 *   e' «non c'e' limite», e' «non l'ho saputo chiedere», e si va avanti
	 *   scrivendolo.  ⛔ Rifiutare qui sarebbe decidere su un silenzio.
	 * ═══════════════════════════════════════════════════════════════════════ */
	{
		VAConfigAttrib attr[2] = { { .type = VAConfigAttribMaxPictureWidth },
			                   { .type = VAConfigAttribMaxPictureHeight } };
		VAStatus st = vaGetConfigAttributes(va->display, profilo, voluto, attr, 2);

		if (st != VA_STATUS_SUCCESS) {
			registro_dice(REG_CODIFICA,
			              "⚠ su «%s» NON ho potuto chiedere al driver la misura massima "
			              "(vaGetConfigAttributes: %d): ⛔ NON e' «non c'e' limite», e' "
			              "«non ho guardato».  Se %ux%u fosse troppo grande lo si "
			              "scoprira' al primo fotogramma",
			              r->nodo_rendering, (int) st, r->larghezza, r->altezza);
		} else if (attr[0].value == VA_ATTRIB_NOT_SUPPORTED ||
		           attr[1].value == VA_ATTRIB_NOT_SUPPORTED) {
			registro_dice(REG_CODIFICA,
			              "⚠ «%s» (%s) non DICHIARA una misura massima per il profilo %d: "
			              "⛔ non si conclude che non ce ne sia una",
			              r->nodo_rendering, c->conf.fornitore_va, (int) profilo);
		} else {
			c->conf.misura_massima_l = attr[0].value;
			c->conf.misura_massima_a = attr[1].value;
			c->conf.misura_massima_letta = true;
			if (r->larghezza > attr[0].value || r->altezza > attr[1].value) {
				di(errore, errore_byte,
				   "«%s» su «%s» (%s) codifica al massimo %ux%u — chiesto %ux%u.  ⛔ Il "
				   "driver lo dice PRIMA, e si dichiara invece di scoprirlo al primo "
				   "fotogramma: chi chiama scenda sul ripiego in software e SCRIVA che "
				   "ci e' sceso",
				   c->componente->name, r->nodo_rendering, c->conf.fornitore_va,
				   attr[0].value, attr[1].value, r->larghezza, r->altezza);
				return -1;
			}
			registro_dice(REG_CODIFICA,
			              "⭐ il driver dichiara al massimo %ux%u per «%s» su %s, e "
			              "%ux%u ci sta — CHIESTO al driver, non dedotto dal nome",
			              attr[0].value, attr[1].value, c->componente->name,
			              c->conf.nodo, r->larghezza, r->altezza);
		}
	}
	return 0;
}

/*
 * Il magazzino delle superfici: quel che il codificatore in hardware consuma.
 * ⚠ `initial_pool_size` non e' un numero di comodo — e' quante superfici la GPU
 *   tiene pronte.  Con `async_depth=1` ne serve poco piu' di una, e si tiene un
 *   margine dichiarato per il caso in cui il componente ne trattenga qualcuna.
 */
#define SUPERFICI_PRONTE 8

static int apri_magazzino(Codificatore *c, char *errore, size_t errore_byte)
{
	av_buffer_unref(&c->magazzino);
	c->magazzino = av_hwframe_ctx_alloc(c->dispositivo);
	if (!c->magazzino) {
		di(errore, errore_byte, "niente memoria per il magazzino delle superfici");
		return -1;
	}
	AVHWFramesContext *fc = (AVHWFramesContext *) c->magazzino->data;
	fc->format = AV_PIX_FMT_VAAPI;
	fc->sw_format = c->formato_gpu;
	fc->width = (int) c->richiesta.larghezza;
	fc->height = (int) c->richiesta.altezza;
	fc->initial_pool_size = SUPERFICI_PRONTE;
	int esito = av_hwframe_ctx_init(c->magazzino);
	if (esito < 0) {
		char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
		av_strerror(esito, testo, sizeof(testo));
		di(errore, errore_byte, "il magazzino %s %ux%u non si e' aperto: %s",
		   av_get_pix_fmt_name(c->formato_gpu), c->richiesta.larghezza,
		   c->richiesta.altezza, testo);
		av_buffer_unref(&c->magazzino);
		return -1;
	}
	return 0;
}

/*
 * ⛔ LE OPZIONI DEL CODIFICATORE IN HARDWARE, DECISE INVECE CHE EREDITATE — e
 *    sono la stessa regola di `opzioni_hevc()`, su un altro componente.
 *
 * ⚠ `[M]` 13 agosto 2026, lette in `ffmpeg -h encoder=hevc_vaapi`: il difetto
 *   di `async_depth` e' **2**.  Nessuno l'aveva chiesto, ed e' esattamente la
 *   stessa forma dei `bframes=4` di x265 — un fotogramma tenuto in canna e' un
 *   fotogramma di ritardo, contro un tetto di 50 ms.  ⛔ Qui vale DOPPIO: il
 *   ciclo di `figlio.c` manda un fotogramma e ne aspetta subito il pacchetto, e
 *   con `async_depth=2` il primo giro tornerebbe `EAGAIN` — cioe' il ramo che
 *   mette il codificatore in scarico e lo fa riaprire, con una chiave in piu' a
 *   ogni fotogramma.
 */
static int opzioni_vaapi(Codificatore *c, char *errore, size_t errore_byte)
{
	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS) {
		/* ⛔ Non si finge, come non si finge su SVT-AV1: `hevc_vaapi` non ha un
		 *    modo senza perdita, e `qp=0` NON lo e' — su VA-API lo zero e' il
		 *    valore che vuol dire «non chiesto» (difetto dell'opzione), che e'
		 *    la stessa sentinella implicita gia' pagata su `crf=0`. */
		di(errore, errore_byte,
		   "in hardware non c'e' un modo senza perdita, e non lo si finge: "
		   "`hevc_vaapi` ha QP costante, e `qp=0` vuol dire «non chiesto», non "
		   "«senza perdita».  ⇒ Il regime senza perdita si chiede a libx265");
		return -1;
	}
	if (c->modo_corrente == CODIFICATORE_QUALITA_CRF) {
		/* ⛔ CRF e QP non sono la stessa grandezza: vedi `ModoQualita`. */
		di(errore, errore_byte,
		   "in hardware non c'e' il CRF: `hevc_vaapi` ha il QP costante.  ⛔ "
		   "Tradurre CRF %d in QP %d e continuare a chiamarlo CRF darebbe due "
		   "misure sotto la stessa etichetta ⇒ si chieda CODIFICATORE_QUALITA_QP",
		   c->qualita_corrente, c->qualita_corrente);
		return -1;
	}
	if (c->qualita_corrente < 1 || c->qualita_corrente > 51) {
		di(errore, errore_byte,
		   "QP %d fuori misura: si chiede fra 1 e 51 — ⛔ e lo ZERO non e' «il "
		   "migliore», e' il valore di difetto che vuol dire «non chiesto»",
		   c->qualita_corrente);
		return -1;
	}
	/* CQP: il quantizzatore fermo.  ⚠ Si chiede PER NOME (`rc_mode=CQP`) e non
	 * si lascia `auto`: `auto` sceglie in base alle altre opzioni, cioe' un
	 * componente che decide da se' — `CODER.md` §3.9. */
	if (av_opt_set_int(c->ctx->priv_data, "rc_mode", 1 /* CQP */, 0) < 0) {
		di(errore, errore_byte, "«%s» ha rifiutato rc_mode=CQP", c->componente->name);
		return -1;
	}
	if (av_opt_set_int(c->ctx->priv_data, "qp", c->qualita_corrente, 0) < 0) {
		di(errore, errore_byte, "«%s» ha rifiutato qp=%d", c->componente->name,
		   c->qualita_corrente);
		return -1;
	}
	if (av_opt_set_int(c->ctx->priv_data, "async_depth", 1, 0) < 0) {
		di(errore, errore_byte, "«%s» ha rifiutato async_depth=1", c->componente->name);
		return -1;
	}
	if (av_opt_set_int(c->ctx->priv_data, "low_power",
	                   c->richiesta.potenza == CODIFICATORE_POTENZA_BASSA ? 1 : 0, 0) < 0) {
		di(errore, errore_byte, "«%s» ha rifiutato low_power", c->componente->name);
		return -1;
	}
	/* ⛔ `idr_interval = 0`: fra due chiavi non ci vanno I non-IDR.  Una I che
	 *    non azzera la predizione non e' una chiave di `RCP.md` §5.2, e un
	 *    client che si collegasse li' resterebbe con lo schermo sfasciato. */
	if (av_opt_set_int(c->ctx->priv_data, "idr_interval", 0, 0) < 0) {
		di(errore, errore_byte, "«%s» ha rifiutato idr_interval=0", c->componente->name);
		return -1;
	}
	/* ⚠ Il profilo si chiede anche qui, per nome e non per numero implicito:
	 *   `ctx->profile` lo dice gia', ma il componente ha un'opzione sua e due
	 *   posti che dicono la stessa cosa vanno detti tutti e due o nessuno. */
	if (av_opt_set_int(c->ctx->priv_data, "profile",
	                   c->richiesta.profondita == 10 ? 2 : 1, 0) < 0) {
		di(errore, errore_byte, "«%s» ha rifiutato il profilo", c->componente->name);
		return -1;
	}
	return 0;
}

/*
 * ⛔ LE OPZIONI CHE SI DECIDONO INVECE DI EREDITARLE.
 *
 * `[M]` 12 agosto 2026, lette nella confessione che x265 scrive nel flusso e
 * nella riga di configurazione che SVT-AV1 stampa: nessuno aveva chiesto
 * `bframes=4`, `open-gop`, ne' `pred struct: random access`.  Le tengono di
 * loro, e comprano compressione **vendendo risposta**.
 */
static int opzioni_hevc(Codificatore *c, char *errore, size_t errore_byte)
{
	char parametri[512];
	char qualita[64] = "";
	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS)
		snprintf(qualita, sizeof(qualita), "lossless=1:");
	else
		snprintf(qualita, sizeof(qualita), "crf=%d:", c->qualita_corrente);

	snprintf(parametri, sizeof(parametri),
	         "%s"
	         /* ⛔ un fotogramma B costringe ad attendere il successivo: un
	          *    fotogramma di ritardo in piu' contro un tetto di 50 ms
	          *    (`SPECIFICHE.md` §3.2).  v1 lo vietava a mano, e la ragione
	          *    non dipendeva dal codec (`codificatore.c:241`). */
	         "bframes=0:"
	         /* ⛔ un GOP aperto ha figure che dipendono da PRIMA della chiave:
	          *    una chiave che non si decodifica da sola contraddice
	          *    `RCP.md` §5.2, che pretende una chiave VERA. */
	         "open-gop=0:"
	         /* ⛔ i parameter set davanti a OGNI chiave — la meta' che si
	          *    dimentica, e che morde quando un client si collega a meta'. */
	         "repeat-headers=1:"
	         /* ⚠ il ritardo non lo fanno solo i fotogrammi B: il lookahead e i
	          *    fili di fotogramma tengono immagini in canna.  Si spengono, e
	          *    si dichiara che il prezzo e' in compressione. */
	         "rc-lookahead=0:frame-threads=1:"
	         "keyint=%d:min-keyint=%d:"
	         /* ⚠ `info=1` e' acceso DI PROPOSITO: e' la confessione che il banco
	          *    legge (§3.4 del rapporto di F2.3).  Costa `[M]` ~2,2 KB per
	          *    chiave, il 2,3 % di una chiave 1080p lossless.  Spegnerlo e'
	          *    una decisione della fase 9, e quando si spegnera' il testimone
	          *    che resta e' il lettore di SPS qui sopra — che non costa
	          *    nemmeno un byte sul filo. */
	         "info=1:log-level=error",
	         qualita,
	         c->richiesta.chiavi_ogni ? (int) c->richiesta.chiavi_ogni : -1,
	         c->richiesta.chiavi_ogni ? (int) c->richiesta.chiavi_ogni : -1);

	if (av_opt_set(c->ctx->priv_data, "x265-params", parametri, 0) < 0) {
		di(errore, errore_byte, "libx265 ha rifiutato i parametri «%s»", parametri);
		return -1;
	}
	/* ⚠ Il preset resta quello predefinito (`medium`) e si DICHIARA: il punto di
	 *   lavoro fra qualita' e tempo e' la fase 9, e sceglierlo qui vorrebbe dire
	 *   fissare un numero senza il regime che lo giustifica (`CODER.md` §3.5). */
	return 0;
}

/*
 * ⭐ H.264 IN SOFTWARE — le stesse cinque scelte di `opzioni_hevc()`, e non e'
 *    una copia per pigrizia: sono scelte che non dipendono dal codec, e i nomi
 *    dei parametri di x264 SI', quindi non si possono condividere.
 *
 * ⛔ E i nomi diversi non sono un dettaglio: `frame-threads` di x265 in x264
 *    NON ESISTE — si chiamano `threads` e `sliced-threads`.  ⚠ E x264
 *    **rifiuta** un parametro che non conosce (a differenza di libsvtav1, che
 *    `[M]` lo ignora e continua): qui uno sbaglio si vede subito, ed e' il
 *    verso buono.
 */
static int opzioni_h264(Codificatore *c, char *errore, size_t errore_byte)
{
	char parametri[512];
	char qualita[64] = "";

	/* ⛔ In x264 il senza-perdita non e' un `lossless=1`: e' `qp=0`. */
	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS)
		snprintf(qualita, sizeof(qualita), "qp=0:");
	else
		snprintf(qualita, sizeof(qualita), "crf=%d:", c->qualita_corrente);

	snprintf(parametri, sizeof(parametri),
	         "%s"
	         "bframes=0:"          /* un fotogramma B = un fotogramma di ritardo */
	         "open-gop=0:"         /* §5.2 vuole una chiave che si decodifichi da sola */
	         "repeat-headers=1:"   /* SPS+PPS davanti a OGNI IDR, per chi entra dopo */
	         "rc-lookahead=0:threads=1:sliced-threads=0:"
	         "keyint=%d:min-keyint=%d:"
	         "log-level=error",
	         qualita,
	         c->richiesta.chiavi_ogni ? (int) c->richiesta.chiavi_ogni : -1,
	         c->richiesta.chiavi_ogni ? (int) c->richiesta.chiavi_ogni : -1);

	if (av_opt_set(c->ctx->priv_data, "x264-params", parametri, 0) < 0) {
		di(errore, errore_byte, "libx264 ha rifiutato i parametri «%s»", parametri);
		return -1;
	}
	return 0;
}

static int opzioni_av1(Codificatore *c, char *errore, size_t errore_byte)
{
	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS) {
		/* ⛔ Non si finge: SVT-AV1 2.3.0 **non ha** un modo senza perdita.
		 *    `[M]` 12 agosto 2026: `-svtav1-params lossless=1` stampa «Error
		 *    parsing option» e **continua uscendo 0**.  Accettare la richiesta e
		 *    dare qualcos'altro sarebbe il ripiego silenzioso che `CODER.md`
		 *    §4.2 vieta.  ⭐ Il regime piu' vicino e' `crf=1`, ed e' misurato:
		 *    877 livelli sulla rampa (come il sorgente) e 220 con 1,000 di
		 *    multipli di 4 sul caso opposto — cioe' l'organo dei 10 bit REGGE. */
		di(errore, errore_byte,
		   "AV1: SVT-AV1 2.3.0 non ha un modo senza perdita, e non lo si finge. "
		   "Il regime piu' vicino e' CRF 1 [M]: si chieda quello");
		return -1;
	}
	/* ⛔ `[M]` **`crf=0` su libsvtav1 vuol dire «non chiesto»**: e' il valore di
	 *    difetto dell'opzione, e l'involucro di ffmpeg lo scarta — il flusso
	 *    esce a CRF 35 senza che nessuno lo dica.  E' un valore sentinella
	 *    implicito, ed e' la forma d'errore E2 dentro una singola opzione. */
	if (c->qualita_corrente < 1) {
		di(errore, errore_byte,
		   "AV1: CRF %d non si chiede — su libsvtav1 lo zero vale «non chiesto» e "
		   "il flusso esce a CRF 35 in silenzio [M]", c->qualita_corrente);
		return -1;
	}
	if (av_opt_set_int(c->ctx->priv_data, "crf", c->qualita_corrente, 0) < 0) {
		di(errore, errore_byte, "libsvtav1 ha rifiutato crf=%d", c->qualita_corrente);
		return -1;
	}
	/* preset 10 e' quello di difetto dell'involucro `[M]` 162 ms per chiave
	 * 1080p10; si scrive lo stesso, perche' un difetto non chiesto che si tiene
	 * si dichiara. */
	if (av_opt_set_int(c->ctx->priv_data, "preset", 10, 0) < 0) {
		di(errore, errore_byte, "libsvtav1 ha rifiutato il preset");
		return -1;
	}
	/* ⛔ `pred-struct=1` = bassa latenza.  Senza, SVT-AV1 dice di suo
	 *    «pred struct: random access» `[M]`, che e' l'equivalente AV1 dei
	 *    fotogrammi B: fotogrammi trattenuti in attesa dei successivi. */
	if (av_opt_set(c->ctx->priv_data, "svtav1-params", "pred-struct=1", 0) < 0) {
		di(errore, errore_byte, "libsvtav1 ha rifiutato svtav1-params");
		return -1;
	}
	return 0;
}

static void chiudi_contesto(Codificatore *c)
{
	if (c->pacchetto)
		av_packet_free(&c->pacchetto);
	if (c->ctx)
		avcodec_free_context(&c->ctx); /* ⚠ libera anche `hw_frames_ctx` */
	/* ⚠ Il magazzino si chiude col contesto: `apri_contesto` ne apre uno nuovo,
	 *   e tenerne due vivi vorrebbe dire superfici della GPU che nessuno
	 *   restituisce — una perdita che si vede solo dopo mezz'ora. */
	av_buffer_unref(&c->magazzino);
}

static int apri_contesto(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;
	/*
	 * ⚠ In hardware il formato del CONTESTO e' quello della superficie
	 *   (`AV_PIX_FMT_VAAPI`); il formato dei pixel veri e' quello del magazzino
	 *   (`formato_gpu`), ed e' **P010LE** a 10 bit — non `yuv420p10le`.  ⛔ Sono
	 *   due formati diversi con lo stesso numero di bit: P010 e' semi-planare e
	 *   tiene i 10 bit nei bit ALTI di sedici.  Convertirci dentro come se fosse
	 *   planare darebbe un'immagine buia e nessun errore.
	 */
	enum AVPixelFormat formato;
	if (c->hardware) {
		c->formato_gpu = (r->profondita == 10) ? AV_PIX_FMT_P010LE : AV_PIX_FMT_NV12;
		formato = AV_PIX_FMT_VAAPI;
	} else {
		formato = (r->profondita == 10) ? AV_PIX_FMT_YUV420P10LE : AV_PIX_FMT_YUV420P;
	}

	if (!accetta_formato(c->componente, formato)) {
		di(errore, errore_byte,
		   "«%s» non accetta %s: ⛔ non si ripiega su un altro formato, si dichiara",
		   c->componente->name, av_get_pix_fmt_name(formato));
		return -1;
	}
	if (c->hardware && apri_magazzino(c, errore, errore_byte) < 0)
		return -1;

	c->ctx = avcodec_alloc_context3(c->componente);
	if (!c->ctx) {
		di(errore, errore_byte, "niente memoria per il contesto");
		return -1;
	}
	c->ctx->width = (int) r->larghezza;
	c->ctx->height = (int) r->altezza;
	c->ctx->pix_fmt = formato;
	c->ctx->time_base = (AVRational){ 1, (int) (r->fotogrammi_al_secondo ? r->fotogrammi_al_secondo : 30) };
	c->ctx->framerate = (AVRational){ (int) (r->fotogrammi_al_secondo ? r->fotogrammi_al_secondo : 30), 1 };
	/* ⛔⛔ ZERO, DECISO E NON EREDITATO — e dal 22 agosto 2026 col numero sotto,
	 *      perche' senza il numero la riga era un'opinione e la tentazione
	 *      resta viva.
	 *
	 * `[M]` (agente D, 22 agosto 2026) mettendolo a **1**:
	 *
	 *   ⭐ sembra un affare   **59 figure buttabili su 120**, e **−16 % di banda**
	 *                         a qualita' invariata (PSNR −0,065 dB)
	 *   ⛔ e invece no        **+67 ms di riordino**, che da soli sfondano i
	 *                         **50 ms** che `SPECIFICHE.md` §3.2 da' a **tutto**
	 *                         il pezzo nostro
	 *
	 * ⇒ Comprerebbe banda vendendo risposta, che e' il commercio che §3.2 vieta
	 *   in una riga — *«una scelta che alza il ritmo peggiorando il ritardo non
	 *   si fa»* — ed e' la stessa ragione per cui la fase 8 ha chiuso l'anello
	 *   in parallelo prima di aprirlo.  ⚠ Vedi anche `opzioni_hevc()`. */
	c->ctx->max_b_frames = 0;
	c->ctx->gop_size = r->chiavi_ogni ? (int) r->chiavi_ogni : INT_MAX;
	switch (r->codec) {
	case CODIFICATORE_HEVC:
		c->ctx->profile = (r->profondita == 10) ? AV_PROFILE_HEVC_MAIN_10 : AV_PROFILE_HEVC_MAIN;
		break;
	/* ⭐ High (100), che e' quel che dichiara la stringa gia' verificata sul
	 *    browser: `avc1.640032` — `64` = profile_idc 100, `00` = nessun
	 *    vincolo, `32` = livello 5.0 (`banchi/07-b48`, 300 su 300). */
	case CODIFICATORE_H264:
		c->ctx->profile = AV_PROFILE_H264_HIGH;
		break;
	default:
		c->ctx->profile = AV_PROFILE_AV1_MAIN;
		break;
	}

	/*
	 * ⛔ IL COLORE SI DICHIARA, O F2.6 MISURA LA MATRICE INVECE DEI PIXEL.
	 *
	 * F2.2 `[M]`: Mutter **non dichiara** range, matrice, trasferimento ne'
	 * primari (quattro zeri, cioe' UNKNOWN), e i pixel alla cattura sono RGB —
	 * *«la matrice la sceglie F2.3»*.  Sceglie **BT.709 a range limitato**:
	 *
	 *   - 709 perche' e' quel che un desktop sRGB si aspetta.
	 *
	 *     ⛔⛔ E LA RAGIONE CHE C'ERA SCRITTA QUI ERA FALSA, misurata il 21
	 *     agosto 2026.  Diceva: *«e' quel che i due browser applicano di
	 *     difetto quando il flusso non dice niente, quindi dichiararlo e'
	 *     prudenza»*.  ⚠ A 1280x720 e' vero; **a 768x480 — il MINIMO di §2.1 —
	 *     e' falso**: con la VUI a «non specificato» il decodificatore
	 *     **hardware indovina BT.601**, e letto come 709 sbaglia fino a
	 *     `[M]` **32,41 livelli**.  Con la VUI dichiarata: 0,42.
	 *
	 *     ⇒ La riga era giusta e la sua ragione no, ⭐ e la ragione vera e'
	 *     **piu' forte**: sotto le 576 righe la dichiarazione non e' prudenza,
	 *     e' **portante**.  Chi un giorno volesse togliere queste quattro righe
	 *     «perche' tanto e' il difetto» romperebbe l'immagine solo alle misure
	 *     piccole, cioe' proprio dove nessuno guarda.
	 *
	 *   - range limitato ⛔ e **non e' prudenza nemmeno questo**: `[M]` Firefox
	 *     **IGNORA `video_full_range_flag` per H.264** — dichiarare il range
	 *     pieno dara' numeri identici al limitato, cioe' un'immagine sbagliata
	 *     **senza un errore da nessuna parte**.  ⇒ Il limitato non e' una
	 *     scelta fra due strade: e' l'unica che il decodificatore rispetti.
	 *     ⚠ E non costa precisione: 8 bit pieni sono 256 livelli, l'intervallo
	 *     limitato a 10 bit ne ha 877.
	 *
	 *     `[M]` E la conversione nostra a monte e' esatta: BGRx pieno → YUV 709
	 *     limitato su 259 riquadri da' Y 0,000 · U 0,000 · V 0,004 di
	 *     scostamento, con un controllo negativo che vede 20 livelli.
	 *     ⭐ E il decodificatore in **hardware** e' la strada piu' fedele delle
	 *     due: 0,51 livelli di peggio su 847 canali, contro 9,41 del software.
	 *     ⇒ 📖 `fasi/06-la-tela-e-la-vista.md`, banco `07-b62`.
	 *
	 * ⚠ E si scrive nel flusso (non solo nel nostro registro), perche' F2.5
	 *   converte YUV→RGB per la tela e F2.6 confronta: due matrici diverse ai
	 *   due capi misurerebbero **la matrice**.
	 */
	c->ctx->colorspace = AVCOL_SPC_BT709;
	c->ctx->color_primaries = AVCOL_PRI_BT709;
	c->ctx->color_trc = AVCOL_TRC_BT709;
	c->ctx->color_range = AVCOL_RANGE_MPEG;

	/*
	 * ⛔⛔ QUI NON SI ACCENDE `AV_CODEC_FLAG_GLOBAL_HEADER`, E LA RIGA E'
	 *     SCRITTA IN NEGATIVO DI PROPOSITO.
	 *
	 * v1 l'aveva gia' pagato (`v1/remotix-c/src/codificatore.c:268-272`): coi
	 * parameter set messi da parte il client riceve un flusso che non sa
	 * decodificare, e ⛔ **il sintomo e' schermo nero con i fotogrammi
	 * riscontrati** — cioe' non nomina ne' i parameter set ne' il codificatore.
	 * Li' la ragione era RDP; qui e' che in Annex-B il chunk `key` deve portarli
	 * con se' (`S2-decodifica.md` §3.5).  Stessa regola, stesso sintomo.
	 */
	c->ctx->flags &= ~(unsigned) AV_CODEC_FLAG_GLOBAL_HEADER;

	/* ⛔ Il magazzino si attacca PRIMA di `avcodec_open2`: senza, il componente
	 *    in hardware si apre lo stesso e fallisce al primo fotogramma con «No
	 *    device available», che e' un errore che non nomina questa riga. */
	if (c->hardware) {
		c->ctx->hw_frames_ctx = av_buffer_ref(c->magazzino);
		if (!c->ctx->hw_frames_ctx) {
			di(errore, errore_byte, "niente memoria per legare il magazzino");
			chiudi_contesto(c);
			return -1;
		}
	}

	int esito;
	if (c->hardware)
		esito = opzioni_vaapi(c, errore, errore_byte);
	else if (r->codec == CODIFICATORE_HEVC)
		esito = opzioni_hevc(c, errore, errore_byte);
	else if (r->codec == CODIFICATORE_H264)
		esito = opzioni_h264(c, errore, errore_byte);
	else
		esito = opzioni_av1(c, errore, errore_byte);
	if (esito < 0) {
		chiudi_contesto(c);
		return -1;
	}

	int aperto = avcodec_open2(c->ctx, c->componente, NULL);
	if (aperto < 0) {
		char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
		av_strerror(aperto, testo, sizeof(testo));
		di(errore, errore_byte, "«%s» non si e' aperto: %s", c->componente->name, testo);
		chiudi_contesto(c);
		return -1;
	}

	/* ───────────────────────────────────────────────────────────────────────
	 * ⛔ PRIMO TESTIMONE: HA OBBEDITO, SECONDO LIBAVCODEC?
	 * Non si presume: si rilegge quel che il contesto dice DOPO l'apertura. */
	c->conf.codec = r->codec;
	c->conf.componente = c->ctx->codec->name;
	c->conf.profondita_chiesta = r->profondita;
	c->conf.fotogrammi_b = c->ctx->max_b_frames;
	c->conf.global_header = (c->ctx->flags & AV_CODEC_FLAG_GLOBAL_HEADER) != 0;
	c->conf.in_hardware = c->hardware;
	c->conf.ha_obbedito = true;
	c->conf.perche_no[0] = 0;

	/* ⭐ E in hardware si RILEGGONO le due opzioni che comprano ritardo: quel che
	 *    si e' chiesto e quel che il componente ha tenuto sono due cose diverse
	 *    finche' non si guarda.  ⚠ `av_opt_get_int` sul `priv_data` legge il
	 *    valore in vigore, non quello passato. */
	if (c->hardware) {
		int64_t v = 0;
		c->conf.profondita_asincrona =
		    (av_opt_get_int(c->ctx->priv_data, "async_depth", 0, &v) == 0) ? (int) v : -1;
		if (av_opt_get_int(c->ctx->priv_data, "low_power", 0, &v) == 0)
			c->conf.bassa_potenza = v != 0;
	}

	if (c->ctx->codec->id != id_di(r->codec))
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "«%s» non e' un codificatore %s", c->ctx->codec->name,
		   nome_codec(r->codec));
	else if (strcmp(c->ctx->codec->name, c->componente->name) != 0)
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "chiesto «%s», aperto «%s»", c->componente->name, c->ctx->codec->name);
	else if (c->ctx->pix_fmt != formato)
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "chiesto %s, aperto %s", av_get_pix_fmt_name(formato),
		   av_get_pix_fmt_name(c->ctx->pix_fmt));
	else if (c->conf.global_header)
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "GLOBAL_HEADER acceso: i parameter set uscirebbero dal flusso");
	else if (c->ctx->max_b_frames != 0)
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "fotogrammi B: %d, e ne erano stati chiesti 0", c->ctx->max_b_frames);
	/* ⛔ Un `async_depth` diverso da 1 e' un fotogramma trattenuto, cioe' il
	 *    difetto che questa fase esiste per togliere: non si spedisce. */
	else if (c->hardware && c->conf.profondita_asincrona != 1)
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "async_depth = %d dopo averne chiesto 1: il componente terrebbe "
		   "fotogrammi in canna", c->conf.profondita_asincrona);
	else if (c->hardware &&
	         c->conf.bassa_potenza != (r->potenza == CODIFICATORE_POTENZA_BASSA))
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "chiesta la codifica %s e il componente dice %s",
		   r->potenza == CODIFICATORE_POTENZA_BASSA ? "a bassa potenza" : "piena",
		   c->conf.bassa_potenza ? "bassa potenza" : "piena");

	if (c->conf.perche_no[0]) {
		c->conf.ha_obbedito = false;
		di(errore, errore_byte, "⛔ E2: %s", c->conf.perche_no);
		chiudi_contesto(c);
		return -1;
	}

	c->pacchetto = av_packet_alloc();
	if (!c->pacchetto) {
		di(errore, errore_byte, "niente memoria per il pacchetto");
		chiudi_contesto(c);
		return -1;
	}
	c->prossimo_chiave = true; /* ⛔ dopo ogni apertura il primo e' una chiave */
	return 0;
}

/*
 * ⭐ I FOTOGRAMMI E LA CONVERSIONE — in un posto solo, perche' `codificatore_
 *    nuovo()` e `codificatore_ridimensiona()` facevano la stessa cosa in due
 *    stesure, e ⛔ la seconda si era gia' dimenticata la promozione dichiarata.
 *    Due stesure della stessa cosa sono un posto dove divergere in silenzio.
 *
 * ⚠ In hardware i fotogrammi sono DUE: quello in memoria di sistema
 *   (`appoggio`, dove swscale scrive) e la superficie della GPU (`fotogramma`,
 *   che si prende dal magazzino a ogni giro).  In software resta uno solo.
 */
static int apri_fotogrammi(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;
	enum AVPixelFormat destinazione = c->hardware ? c->formato_gpu : c->ctx->pix_fmt;

	if (c->fotogramma)
		av_frame_free(&c->fotogramma);
	if (c->appoggio)
		av_frame_free(&c->appoggio);
	if (c->conversione) {
		sws_freeContext(c->conversione);
		c->conversione = NULL;
	}

	/* Il fotogramma che entra nel codificatore. */
	c->fotogramma = av_frame_alloc();
	if (!c->fotogramma) {
		di(errore, errore_byte, "niente memoria per il fotogramma");
		return -1;
	}
	if (!c->hardware) {
		c->fotogramma->format = c->ctx->pix_fmt;
		c->fotogramma->width = c->ctx->width;
		c->fotogramma->height = c->ctx->height;
		c->fotogramma->colorspace = c->ctx->colorspace;
		c->fotogramma->color_range = c->ctx->color_range;
		if (av_frame_get_buffer(c->fotogramma, 0) < 0) {
			di(errore, errore_byte, "niente memoria per i piani del fotogramma");
			return -1;
		}
	} else {
		/* ⛔ La superficie NON si alloca qui e non si riusa: si prende dal
		 *    magazzino a ogni giro (vedi `prepara_fotogramma`).  Riusarne una
		 *    sola mentre il codificatore ne tiene ancora un riferimento e' una
		 *    scrittura sotto i piedi di chi legge, e il sintomo sarebbe
		 *    un'immagine che ogni tanto si strappa — senza nessun errore. */
		c->appoggio = av_frame_alloc();
		if (!c->appoggio) {
			di(errore, errore_byte, "niente memoria per il fotogramma d'appoggio");
			return -1;
		}
		c->appoggio->format = c->formato_gpu;
		c->appoggio->width = (int) r->larghezza;
		c->appoggio->height = (int) r->altezza;
		c->appoggio->colorspace = c->ctx->colorspace;
		c->appoggio->color_range = c->ctx->color_range;
		if (av_frame_get_buffer(c->appoggio, 0) < 0) {
			di(errore, errore_byte, "niente memoria per i piani d'appoggio");
			return -1;
		}
	}

	/*
	 * La conversione.  ⛔ Serve in DUE casi, e il secondo e' nato con
	 * l'hardware:
	 *   - BGRx → il formato del codificatore: la cattura di GNOME (`[M]` F2.2);
	 *   - yuv420p10le → **P010LE**: l'ingresso del banco su un codificatore in
	 *     hardware.  ⚠ Sono tutti e due «10 bit 4:2:0» e **non sono lo stesso
	 *     formato**: P010 e' semi-planare e tiene i dieci bit in ALTO dentro
	 *     sedici.  Copiarli come se fossero uguali darebbe un'immagine buia e
	 *     nessun errore — la forma di difetto che non nomina la causa.
	 */
	enum AVPixelFormat sorgente;
	if (r->formato == CODIFICATORE_PIXEL_BGRX)
		sorgente = AV_PIX_FMT_BGR0;
	else
		sorgente = AV_PIX_FMT_YUV420P10LE;

	if (sorgente != destinazione) {
		c->conversione = sws_getContext((int) r->larghezza, (int) r->altezza, sorgente,
		                                (int) r->larghezza, (int) r->altezza, destinazione,
		                                SWS_BILINEAR, NULL, NULL, NULL);
		if (!c->conversione) {
			di(errore, errore_byte, "swscale non ha aperto %s → %s",
			   av_get_pix_fmt_name(sorgente), av_get_pix_fmt_name(destinazione));
			return -1;
		}
		/* ⛔ La matrice si IMPONE.  Senza questa chiamata swscale usa il suo
		 *    difetto, che non e' scritto da nessuna parte nel nostro codice: due
		 *    versioni di ffmpeg potrebbero convertire diversamente e nessuno se
		 *    ne accorgerebbe guardando l'immagine.
		 * ⚠ La sorgente e' a intervallo PIENO solo quando e' RGB: un
		 *   `yuv420p10le` che arriva dal banco e' gia' a intervallo limitato, e
		 *   dichiararlo pieno lo schiarirebbe di un passo a ogni giro. */
		const int *tavola = sws_getCoefficients(SWS_CS_ITU709);
		sws_setColorspaceDetails(c->conversione, tavola,
		                         r->formato == CODIFICATORE_PIXEL_BGRX ? 1 : 0,
		                         tavola, 0 /* uscita: limitato */, 0, 1 << 16, 1 << 16);
	}
	/* ⚠ La sorgente ha 8 bit veri (`[M]` F2.2): il Main10 che ne esce e' 8 bit
	 *   PROMOSSI, e la promozione si dichiara invece di subirla. */
	c->conf.promozione_8_a_10 =
	    (r->formato == CODIFICATORE_PIXEL_BGRX && r->profondita == 10);
	return 0;
}

Codificatore *codificatore_nuovo(const CodificatoreRichiesta *richiesta,
                                 char *errore, size_t errore_byte)
{
	if (!richiesta || richiesta->larghezza == 0 || richiesta->altezza == 0) {
		di(errore, errore_byte, "misura nulla");
		return NULL;
	}
	if (richiesta->profondita != 8 && richiesta->profondita != 10) {
		di(errore, errore_byte, "profondita' %d: si chiede 8 o 10", richiesta->profondita);
		return NULL;
	}
	/*
	 * ⛔ Un ingresso a 10 bit dentro un codificatore a 8 non e' una conversione:
	 *    e' una lettura fuori misura.  ⚠ E il sintomo sarebbe **la memoria
	 *    sfondata**, non un'immagine brutta — cioe' un difetto che non nomina
	 *    ne' il colore ne' la profondita'.  Chi vuole 8 bit passa da BGRx, che
	 *    ha una conversione dichiarata.
	 */
	if (richiesta->formato == CODIFICATORE_PIXEL_YUV420P10LE && richiesta->profondita != 10) {
		di(errore, errore_byte,
		   "l'ingresso e' yuv420p10le e si chiedono %d bit: non si mescolano — "
		   "per 8 bit si entra da BGRx", richiesta->profondita);
		return NULL;
	}
	/* ⚠ 4:2:0 vuole misure pari: una larghezza dispari darebbe un croma di
	 *   mezzo campione, e il codificatore lo arrotonderebbe **in silenzio**. */
	if ((richiesta->larghezza & 1) || (richiesta->altezza & 1)) {
		di(errore, errore_byte, "%ux%u: 4:2:0 vuole misure pari",
		   richiesta->larghezza, richiesta->altezza);
		return NULL;
	}

	Codificatore *c = calloc(1, sizeof(*c));
	if (!c) {
		di(errore, errore_byte, "niente memoria");
		return NULL;
	}
	c->richiesta = *richiesta;
	c->modo_corrente = richiesta->modo;
	c->qualita_corrente = richiesta->qualita;

	const char *nome = richiesta->componente ? richiesta->componente
	                                         : nome_predefinito(richiesta->codec);
	/*
	 * ⛔ CHIESTO PER NOME, NESSUN RIPIEGO — la riga di v1
	 * (`codificatore.c:550-566`) che questo file eredita per intero:
	 *   «Chi indica un codificatore sta misurando: ripiegare su un altro darebbe
	 *    due misure diverse con la stessa etichetta, che e' peggio di non
	 *    misurare.»
	 * ⚠ `avcodec_find_encoder_by_name` e non `avcodec_find_encoder(ID)`: il
	 *   secondo lascia scegliere a libavcodec fra cinque codificatori HEVC, e
	 *   quattro sono in hardware.
	 */
	c->componente = avcodec_find_encoder_by_name(nome);
	if (!c->componente) {
		di(errore, errore_byte,
		   "il codificatore «%s» non c'e' in questa libavcodec: ⛔ non se ne prende "
		   "un altro, si fallisce dicendolo", nome);
		free(c);
		return NULL;
	}
	if (c->componente->id != id_di(richiesta->codec)) {
		di(errore, errore_byte, "«%s» non e' un codificatore %s", nome,
		   nome_codec(richiesta->codec));
		free(c);
		return NULL;
	}

	/*
	 * ⛔ «E' in hardware?» si chiede al componente PRIMA di aprire: da quella
	 *    risposta dipendono il formato del contesto, il magazzino e la
	 *    conversione — cioe' tre cose che dopo non si possono cambiare.
	 */
	c->hardware = componente_e_hardware(c->componente, NULL);
	if (c->hardware && apri_dispositivo(c, errore, errore_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}

	if (apri_contesto(c, errore, errore_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}
	if (apri_fotogrammi(c, errore, errore_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}

	/*
	 * ⛔ Il nome porta DENTRO il nodo e la potenza, non a fianco: e' la riga che
	 *    finisce nel registro accanto a ogni numero, e un ritmo di 3 ms senza
	 *    «quale scheda» e «quale entrypoint» accanto e' un numero che vale per
	 *    una macchina che non si sa quale sia (`LEZIONI.md` §1.1).
	 */
	if (c->hardware)
		snprintf(c->nome, sizeof(c->nome),
		         "%s %s via %s (in HARDWARE · %s · %s · %s)",
		         nome_codec(richiesta->codec),
		         richiesta->profondita == 10 ? "10 bit" : "8 bit",
		         c->componente->name, c->conf.nodo, c->conf.fornitore_va,
		         c->conf.bassa_potenza ? "⚠ EncSliceLP, bassa potenza — NON e' la "
		                                 "codifica piena"
		                               : "EncSlice, piena");
	else
		snprintf(c->nome, sizeof(c->nome), "%s %s via %s (in software)",
		         nome_codec(richiesta->codec),
		         richiesta->profondita == 10 ? "10 bit" : "8 bit",
		         c->componente->name);

	registro_dice(REG_CODIFICA, "aperto: %s · %ux%u · %s · chiavi %s%s", c->nome,
	              richiesta->larghezza, richiesta->altezza,
	              richiesta->modo == CODIFICATORE_QUALITA_LOSSLESS ? "senza perdita"
	              : richiesta->modo == CODIFICATORE_QUALITA_QP     ? "QP costante"
	                                                               : "CRF",
	              richiesta->chiavi_ogni ? "periodiche" : "solo su richiesta",
	              c->conf.promozione_8_a_10
	                  ? " · ⚠ 8 bit della cattura PROMOSSI a 10: il desiderato di "
	                    "SPECIFICHE.md §3.1 non passa da questa sorgente"
	                  : "");
	return c;
}

void codificatore_libera(Codificatore *c)
{
	if (!c)
		return;
	if (c->pacchetto_in_mano)
		av_packet_unref(c->pacchetto);
	if (c->conversione)
		sws_freeContext(c->conversione);
	if (c->fotogramma)
		av_frame_free(&c->fotogramma);
	if (c->appoggio)
		av_frame_free(&c->appoggio);
	/* ⛔ Prima del dispositivo, e in quest'ordine: le superfici importate e il
	 *    contesto della conversione vivono SUL dispositivo, e liberarli dopo
	 *    vorrebbe dire chiederlo a un display che non c'e' piu'. */
	butta_le_importate(c, "il codificatore si chiude");
	chiudi_vpp(c);
	chiudi_contesto(c);
	/* ⚠ Il dispositivo si chiude per ULTIMO: il magazzino e le superfici ne
	 *   tengono un riferimento, e chiuderlo prima lascerebbe il driver a
	 *   liberare superfici su un display che non c'e' piu'. */
	av_buffer_unref(&c->dispositivo);
	free(c);
}

const char *codificatore_nome(const Codificatore *c)
{
	return c ? c->nome : "(nessuno)";
}

const char *codificatore_ripiego_software(CodecVideo codec)
{
	return nome_predefinito(codec);
}

const CodificatoreConfessione *codificatore_confessione(const Codificatore *c)
{
	return c ? &c->conf : NULL;
}

void codificatore_chiedi_chiave(Codificatore *c)
{
	if (c)
		c->prossimo_chiave = true;
}

bool codificatore_ridimensiona(Codificatore *c, uint32_t larghezza, uint32_t altezza,
                               char *errore, size_t errore_byte)
{
	if (!c)
		return false;
	if (larghezza == c->richiesta.larghezza && altezza == c->richiesta.altezza)
		return true;
	if ((larghezza & 1) || (altezza & 1)) {
		di(errore, errore_byte, "%ux%u: 4:2:0 vuole misure pari", larghezza, altezza);
		return false;
	}

	/* ⛔ Si riapre davvero.  Un codificatore aperto a una misura e alimentato a
	 *    un'altra non protesta: taglia o riempie, e il difetto si vede solo
	 *    nell'immagine.
	 * ⚠ In hardware si riapre anche il MAGAZZINO — le superfici hanno la misura
	 *   dentro, e riusarle vorrebbe dire caricare 1920 righe dentro 1280. */
	chiudi_contesto(c);
	c->richiesta.larghezza = larghezza;
	c->richiesta.altezza = altezza;
	c->prima_codifica_fatta = false;
	c->conf.letto_dal_flusso = false;

	if (apri_contesto(c, errore, errore_byte) < 0)
		return false;
	if (apri_fotogrammi(c, errore, errore_byte) < 0)
		return false;

	/* ⛔ `RCP.md` §5.2: il primo fotogramma alla misura nuova DEVE essere una
	 *    chiave, e una chiave VERA.  `apri_contesto` l'ha gia' preteso; la riga
	 *    resta perche' la regola sta scritta qui, non altrove. */
	c->prossimo_chiave = true;
	registro_dice(REG_CODIFICA,
	              "tela nuova %ux%u: riaperto, e il prossimo fotogramma e' una chiave "
	              "(RCP.md §5.2)", larghezza, altezza);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ LA COPIA ZERO — dal DMA-BUF del compositore alla superficie del
 *      codificatore, senza passare dalla memoria di sistema
 *
 * ⛔ QUEL CHE QUESTA STRADA TOGLIE, e sono tre tratti misurati `[M]` il 22
 *    agosto 2026 dentro il prodotto (agente C, mediane su 512 fotogrammi):
 *
 *      la copia (`memcpy` nel posto della cattura)   1,65 ms
 *      la conversione (`sws_scale`, in CPU)          8,15 ms
 *      il caricamento (memoria → GPU)                1,16 ms
 *
 * ⛔⛔ E QUEL CHE **NON** TOGLIE, ed e' la meta' che nessuno si aspetta: la
 *      conversione di colore **va fatta lo stesso**.  Il compositore consegna
 *      BGRx; il codificatore in hardware vuole NV12.  ⇒ La differenza non e'
 *      «non si converte»: e' **chi converte** — la GPU invece della CPU, sulla
 *      memoria che ha gia' sotto invece che su otto megabyte fatti passare due
 *      volte per il bus.
 *
 * ⇒ Il costo della conversione sulla GPU finisce in `us_conversione`, sotto la
 *   stessa etichetta di prima, **apposta**: e' la stessa grandezza fatta in un
 *   altro posto, e metterla in una voce nuova renderebbe impossibile il
 *   confronto col «prima».  ⛔ `us_caricamento` invece va a **0**, e li' lo zero
 *   vuol dire «questo tratto non c'e' piu'», non «e' gratis».
 *
 * ⚠ E C'E' UNA SINCRONIZZAZIONE ESPLICITA (`vaSyncSurface`) dopo la
 *   conversione, che si potrebbe togliere: senza, la chiamata tornerebbe prima
 *   che la GPU abbia finito e il numero sarebbe piu' bello.  ⛔ Sta li' per due
 *   ragioni, e la seconda vale piu' della prima:
 *     1. il tempo misurato e' quello VERO, non quello dell'ordine impartito;
 *     2. ⭐⭐ **e' il rilascio**: quando questa funzione torna, la GPU ha finito
 *        di leggere il DMA-BUF del compositore, e solo allora chi ha catturato
 *        puo' renderlo.  Togliere la sincronizzazione qui rimetterebbe in piedi
 *        il difetto di `LEZIONI.md` §8 — due schermate che si alternano, e
 *        nessun errore.
 * ═══════════════════════════════════════════════════════════════════════════ */

static VADisplay display_di(Codificatore *c)
{
	AVHWDeviceContext *dc;
	AVVAAPIDeviceContext *va;

	if (!c->dispositivo)
		return NULL;
	dc = (AVHWDeviceContext *) c->dispositivo->data;
	va = dc->hwctx;
	return va ? va->display : NULL;
}

/* Butta tutte le superfici importate.  ⛔ Si chiama quando la generazione dei
 * buffer del produttore cambia, e alla chiusura: una superficie che sopravvive
 * al `pw_buffer` che descriveva punta a memoria di qualcun altro. */
static void butta_le_importate(Codificatore *c, const char *perche)
{
	VADisplay dpy = display_di(c);

	if (!c->quante_importate)
		return;
	if (dpy)
		for (unsigned i = 0; i < c->quante_importate; i++)
			vaDestroySurfaces(dpy, &c->importate[i].superficie, 1);
	registro_dice(REG_CODIFICA,
	              "⭐ butto le %u superfici importate: %s.  ⛔ Tenerle sarebbe dare a "
	              "VA-API un descrittore che non descrive piu' niente — e il sintomo "
	              "sarebbe un'immagine VECCHIA, senza nessun errore",
	              c->quante_importate, perche);
	c->quante_importate = 0;
}

/*
 * Importa il DMA-BUF come superficie VA-API, o rende quella gia' importata.
 *
 * ⛔ La cache si confronta su TUTTO quel che descrive il buffer — descrittore,
 *    misura, passo, scostamento, formato e modificatore — e non sul solo `fd`.
 *    ⚠ Due buffer diversi con lo stesso numero di descrittore esistono (i numeri
 *    si riciclano), e la generazione li separa; ma se anche il resto non
 *    combaciasse, importare di nuovo costa una volta e sbagliare costa tutta la
 *    sessione.
 */
static VASurfaceID importa_dmabuf(Codificatore *c, const CodificatoreSuperficie *s)
{
	VADisplay dpy = display_di(c);
	VADRMPRIMESurfaceDescriptor d;
	VASurfaceAttrib attributi[2];
	VASurfaceID superficie = VA_INVALID_ID;
	VAStatus stato;
	unsigned i;

	if (!dpy)
		return VA_INVALID_ID;

	/* ⛔ La generazione PRIMA di tutto: se il produttore ha rifatto i buffer,
	 *    quel che c'e' in cache non descrive piu' niente. */
	if (c->cache_nata && c->generazione_cache != s->generazione)
		butta_le_importate(c, "il produttore ha rifatto i suoi buffer");
	c->generazione_cache = s->generazione;
	c->cache_nata = true;

	for (i = 0; i < c->quante_importate; i++)
		if (c->importate[i].fd == s->fd && c->importate[i].l == s->larghezza
		    && c->importate[i].a == s->altezza && c->importate[i].stride == s->stride
		    && c->importate[i].offset == s->offset
		    && c->importate[i].formato_drm == s->formato_drm
		    && c->importate[i].modificatore == s->modificatore)
			return c->importate[i].superficie;

	memset(&d, 0, sizeof d);
	/*
	 * ⛔ IL FOURCC DI VA-API NON E' QUELLO DI DRM, e i due si somigliano
	 *    abbastanza da farsi scambiare.  ⚠ `VA_FOURCC_BGRX` e' quel che ffmpeg
	 *    accoppia a `AV_PIX_FMT_BGR0` e a `DRM_FORMAT_XRGB8888`
	 *    (`hwcontext_vaapi.c`), cioe' B,G,R,ignorato **nell'ordine dei byte in
	 *    memoria** — lo stesso che `cattura.c` negozia come `BGRx`.  ⛔ Sbagliarlo
	 *    non da' nessun errore: da' rosso e blu scambiati.
	 * ⚠ Qui si dichiarano i due che questo modulo sa ricevere; per gli altri si
	 *   rifiuta invece di indovinare.
	 */
	if (s->formato_drm == DRM_FORMAT_XRGB8888)
		d.fourcc = VA_FOURCC_BGRX;
	else if (s->formato_drm == DRM_FORMAT_ARGB8888)
		d.fourcc = VA_FOURCC_BGRA;
	else {
		registro_dice(REG_CODIFICA,
		              "⛔ formato DRM 0x%08x non importabile: questa strada sa BGRx e "
		              "BGRA.  ⚠ NON si indovina un fourcc — un fourcc sbagliato non da' "
		              "errore, da' i colori scambiati",
		              s->formato_drm);
		return VA_INVALID_ID;
	}
	d.width = s->larghezza;
	d.height = s->altezza;
	d.num_objects = 1;
	d.objects[0].fd = s->fd;
	d.objects[0].size = s->offset + s->stride * s->altezza;
	d.objects[0].drm_format_modifier = s->modificatore;
	d.num_layers = 1;
	d.layers[0].drm_format = s->formato_drm;
	d.layers[0].num_planes = 1;
	d.layers[0].object_index[0] = 0;
	d.layers[0].offset[0] = s->offset;
	d.layers[0].pitch[0] = s->stride;

	attributi[0].type = VASurfaceAttribMemoryType;
	attributi[0].flags = VA_SURFACE_ATTRIB_SETTABLE;
	attributi[0].value.type = VAGenericValueTypeInteger;
	attributi[0].value.value.i = VA_SURFACE_ATTRIB_MEM_TYPE_DRM_PRIME_2;
	attributi[1].type = VASurfaceAttribExternalBufferDescriptor;
	attributi[1].flags = VA_SURFACE_ATTRIB_SETTABLE;
	attributi[1].value.type = VAGenericValueTypePointer;
	attributi[1].value.value.p = &d;

	stato = vaCreateSurfaces(dpy, VA_RT_FORMAT_RGB32, s->larghezza, s->altezza, &superficie, 1,
	                         attributi, 2);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA,
		              "⛔ il DMA-BUF non si e' importato (vaCreateSurfaces: %s) — fd %d, "
		              "%ux%u, passo %u, scostamento %u, modificatore 0x%llx.  ⚠ NON si "
		              "ripiega sulla copia in silenzio: chi chiama lo scrive",
		              vaErrorStr(stato), s->fd, s->larghezza, s->altezza, s->stride,
		              s->offset, (unsigned long long) s->modificatore);
		return VA_INVALID_ID;
	}

	if (c->quante_importate >= IMPORTATE_MAX)
		butta_le_importate(c, "la cache e' piena e si ricomincia");
	i = c->quante_importate++;
	c->importate[i].fd = s->fd;
	c->importate[i].l = s->larghezza;
	c->importate[i].a = s->altezza;
	c->importate[i].stride = s->stride;
	c->importate[i].offset = s->offset;
	c->importate[i].formato_drm = s->formato_drm;
	c->importate[i].modificatore = s->modificatore;
	c->importate[i].superficie = superficie;
	return superficie;
}

/* Apre il contesto della conversione sulla GPU, alla misura in vigore.
 * ⛔ Si riapre quando la misura cambia: un contesto VPP porta la misura dentro,
 *    esattamente come il magazzino delle superfici. */
static bool apri_vpp(Codificatore *c, uint32_t larghezza, uint32_t altezza)
{
	VADisplay dpy = display_di(c);
	VAStatus stato;

	if (!dpy)
		return false;
	if (c->vpp_aperto && c->vpp_l == larghezza && c->vpp_a == altezza)
		return true;
	if (c->vpp_aperto) {
		vaDestroyContext(dpy, c->vpp_contesto);
		vaDestroyConfig(dpy, c->vpp_configurazione);
		c->vpp_aperto = false;
	}
	/*
	 * ⛔ E QUI SI CHIEDE AL DRIVER, non a ffmpeg: `VAEntrypointVideoProc` c'e' o
	 *    non c'e', e se non c'e' questa strada **non esiste su questa macchina**.
	 *    ⚠ E' la stessa regola con cui `apri_dispositivo()` chiede gli entrypoint
	 *    di codifica: «gliel'ho chiesto» e «ce l'ha» hanno lo stesso aspetto
	 *    finche' non si guarda (`LEZIONI.md` §1.11).
	 */
	stato = vaCreateConfig(dpy, VAProfileNone, VAEntrypointVideoProc, NULL, 0,
	                       &c->vpp_configurazione);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA,
		              "⛔ questa scheda non ha la conversione sulla GPU (VAProfileNone / "
		              "VAEntrypointVideoProc: %s): la copia zero NON e' percorribile qui, "
		              "e si dichiara invece di ripiegare in silenzio",
		              vaErrorStr(stato));
		return false;
	}
	stato = vaCreateContext(dpy, c->vpp_configurazione, (int) larghezza, (int) altezza,
	                        VA_PROGRESSIVE, NULL, 0, &c->vpp_contesto);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA,
		              "⛔ il contesto della conversione %ux%u non si e' aperto: %s",
		              larghezza, altezza, vaErrorStr(stato));
		vaDestroyConfig(dpy, c->vpp_configurazione);
		return false;
	}
	c->vpp_aperto = true;
	c->vpp_l = larghezza;
	c->vpp_a = altezza;
	return true;
}

static void chiudi_vpp(Codificatore *c)
{
	VADisplay dpy = display_di(c);

	if (!c->vpp_aperto || !dpy)
		return;
	vaDestroyContext(dpy, c->vpp_contesto);
	vaDestroyConfig(dpy, c->vpp_configurazione);
	c->vpp_aperto = false;
}

/*
 * La conversione RGB → NV12 sulla GPU, e ⛔ **la matrice si IMPONE**, come la
 * imponeva `sws_setColorspaceDetails` sulla strada della memoria.
 *
 * ⛔ Senza queste quattro righe il driver userebbe il suo difetto, che non e'
 *    scritto da nessuna parte nel nostro codice: due versioni di iHD potrebbero
 *    convertire diversamente e nessuno se ne accorgerebbe guardando l'immagine.
 *    ⚠ E la coppia giusta e' quella che la strada vecchia dichiarava:
 *    **sorgente RGB a intervallo PIENO, destinazione BT.709 a intervallo
 *    LIMITATO**.  Sbagliare il verso non da' errore: da' un'immagine slavata o
 *    contrastata, cioe' un difetto che nessuna riga di registro nomina.
 */
static bool converti_sulla_gpu(Codificatore *c, VASurfaceID sorgente, VASurfaceID destinazione)
{
	VADisplay dpy = display_di(c);
	VAProcPipelineParameterBuffer p;
	VABufferID buffer = VA_INVALID_ID;
	VAStatus stato, fine;
	VARectangle regione;

	if (!dpy || !c->vpp_aperto)
		return false;

	memset(&p, 0, sizeof p);
	p.surface = sorgente;
	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔⛔ LE DUE REGIONI SI DICHIARANO, E LASCIARLE A `NULL` E' UN DIFETTO
	 *       VERO — trovato refutando, il 22 agosto 2026, e i millisecondi erano
	 *       gia' bellissimi.
	 *
	 * `NULL` non vuol dire «1:1»: vuol dire **tutta la superficie**.  ⛔ E la
	 * superficie di destinazione **non e' 1920x1080**: `av_hwframe_ctx` la
	 * alloca allineata, e su iHD a 1920x1080 esce **1920x1088**.  ⇒ Con le
	 * regioni a `NULL` il VPP **SCALA** l'immagine da 1080 a 1088 righe — un
	 * ingrandimento dello 0,74 %, che a occhio non si vede e che
	 * **distrugge ogni struttura a livello di pixel**.
	 *
	 * ⭐⭐ E IL BANCO L'HA VISTO E IL COLORE NO: `[M]` le statistiche di colore
	 *     dei due flussi combaciavano entro **0,17 livelli su 255** (una scala
	 *     dello 0,7 % non sposta una media), mentre il banco del trascinamento
	 *     leggeva **0 marche su 903** contro 870 su 870 dell'altra strada, con
	 *     il contrasto fra le celle sceso a 0,245 sotto il minimo di 0,25.
	 *     ⇒ Due strumenti, e solo uno dei due sapeva vedere questo difetto.
	 *
	 * ⚠ E il sintomo per l'utente sarebbe stato **un desktop leggermente
	 *   sfocato e leggermente stirato**, senza nessuna riga di registro.
	 * ═══════════════════════════════════════════════════════════════════════ */
	regione.x = 0;
	regione.y = 0;
	regione.width = (unsigned short) c->vpp_l;
	regione.height = (unsigned short) c->vpp_a;
	p.surface_region = &regione;
	p.output_region = &regione;
	p.output_background_color = 0xff000000;
	p.filter_flags = VA_FRAME_PICTURE;
	p.filters = NULL;
	p.num_filters = 0;
	p.surface_color_standard = VAProcColorStandardNone; /* la sorgente e' RGB */
	p.output_color_standard = VAProcColorStandardBT709;
	p.input_color_properties.color_range = VA_SOURCE_RANGE_FULL;
	p.output_color_properties.color_range = VA_SOURCE_RANGE_REDUCED;

	stato = vaBeginPicture(dpy, c->vpp_contesto, destinazione);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA, "⛔ vaBeginPicture: %s", vaErrorStr(stato));
		return false;
	}
	stato = vaCreateBuffer(dpy, c->vpp_contesto, VAProcPipelineParameterBufferType, sizeof p, 1,
	                       &p, &buffer);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA, "⛔ vaCreateBuffer: %s", vaErrorStr(stato));
		vaEndPicture(dpy, c->vpp_contesto);
		return false;
	}
	stato = vaRenderPicture(dpy, c->vpp_contesto, &buffer, 1);
	if (stato != VA_STATUS_SUCCESS)
		registro_dice(REG_CODIFICA, "⛔ vaRenderPicture: %s", vaErrorStr(stato));
	fine = vaEndPicture(dpy, c->vpp_contesto);
	vaDestroyBuffer(dpy, buffer);
	if (stato != VA_STATUS_SUCCESS || fine != VA_STATUS_SUCCESS) {
		if (fine != VA_STATUS_SUCCESS)
			registro_dice(REG_CODIFICA, "⛔ vaEndPicture: %s", vaErrorStr(fine));
		return false;
	}
	/* ⛔⭐ E QUI SI ASPETTA DAVVERO — vedi il riquadro in cima: questa riga E' il
	 *     rilascio.  Quando torna, la GPU ha finito di leggere il buffer del
	 *     compositore, e chi ha catturato lo puo' rendere. */
	stato = vaSyncSurface(dpy, destinazione);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA, "⛔ vaSyncSurface: %s", vaErrorStr(stato));
		return false;
	}
	return true;
}

/*
 * Prepara il fotogramma del codificatore a partire dal DMA-BUF — la meta' della
 * copia zero che sta dentro il ciclo dei tentativi.
 *
 * ⛔ Si rifa' a ogni tentativo, e non e' spreco: se il fotogramma sfonda il
 *    tetto dei 16 MiB, `abbassa_qualita()` **richiude e riapre il contesto e il
 *    magazzino**, quindi la superficie di destinazione del giro prima non esiste
 *    piu'.  ⚠ La superficie SORGENTE invece resta: e' importata sul dispositivo,
 *    che nessuno chiude.
 */
static bool prepara_dalla_scheda(Codificatore *c, const CodificatoreSuperficie *s, uint64_t *us,
                                 uint64_t *us_carico)
{
	uint64_t t0 = adesso_us();
	VASurfaceID sorgente, destinazione;
	int esito;

	/* ⛔ Il caricamento sulla GPU NON C'E' su questa strada, e lo zero lo dice.
	 *    ⚠ Chi legge la tabella dei tratti deve poter distinguere «gratis» da
	 *    «non esiste», e qui la riga di registro della prima volta lo scrive. */
	*us_carico = 0;

	if (!apri_vpp(c, c->richiesta.larghezza, c->richiesta.altezza))
		return false;
	sorgente = importa_dmabuf(c, s);
	if (sorgente == VA_INVALID_ID)
		return false;

	av_frame_unref(c->fotogramma);
	esito = av_hwframe_get_buffer(c->magazzino, c->fotogramma, 0);
	if (esito < 0) {
		char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
		av_strerror(esito, testo, sizeof(testo));
		registro_dice(REG_CODIFICA, "⛔ nessuna superficie libera nel magazzino (%d pronte): %s",
		              SUPERFICI_PRONTE, testo);
		return false;
	}
	destinazione = (VASurfaceID) (uintptr_t) c->fotogramma->data[3];
	if (!converti_sulla_gpu(c, sorgente, destinazione))
		return false;

	c->fotogramma->colorspace = c->ctx->colorspace;
	c->fotogramma->color_range = c->ctx->color_range;
	*us = adesso_us() - t0;

	c->fotogramma->pts = c->numero;
	c->fotogramma->pict_type = c->prossimo_chiave ? AV_PICTURE_TYPE_I : AV_PICTURE_TYPE_NONE;
	if (c->prossimo_chiave)
		c->fotogramma->flags |= AV_FRAME_FLAG_KEY;
	else
		c->fotogramma->flags &= ~(unsigned) AV_FRAME_FLAG_KEY;

	if (!c->detto_copia_zero) {
		c->detto_copia_zero = true;
		registro_dice(REG_CODIFICA,
		              "⭐⭐ COPIA ZERO in vigore: il DMA-BUF del compositore (fd %d, %ux%u, "
		              "passo %u, modificatore 0x%llx) e' importato come superficie VA-API e "
		              "convertito in %s DALLA GPU — nessuna `memcpy`, nessun `sws_scale`, "
		              "nessun `av_hwframe_transfer_data`.  ⚠ La conversione resta e costa "
		              "%llu us: e' cambiato CHI la fa, non che vada fatta",
		              s->fd, s->larghezza, s->altezza, s->stride,
		              (unsigned long long) s->modificatore,
		              av_get_pix_fmt_name(c->formato_gpu), (unsigned long long) *us);
	}
	return true;
}

/*
 * Riempie il fotogramma che entra nel codificatore, dai pixel del chiamante.
 *
 * ⭐ In hardware sono DUE passi e si cronometrano SEPARATI:
 *      `us_conversione`  swscale, in memoria di sistema — il tratto che c'era
 *                        gia';
 *      `us_caricamento`  memoria di sistema → GPU — ⛔ il tratto NUOVO, ed e'
 *                        esattamente quello che la copia zero della fase 8
 *                        esiste per togliere.  Sommarlo alla codifica renderebbe
 *                        invisibile quanto varra' quel lavoro.
 */
static bool prepara_fotogramma(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                               uint64_t *us, uint64_t *us_carico)
{
	uint64_t t0 = adesso_us();
	AVFrame *dove = c->hardware ? c->appoggio : c->fotogramma;

	*us_carico = 0;
	if (av_frame_make_writable(dove) < 0)
		return false;

	if (c->conversione) {
		const uint8_t *piani[4] = { NULL, NULL, NULL, NULL };
		int passi[4] = { 0, 0, 0, 0 };
		if (c->richiesta.formato == CODIFICATORE_PIXEL_BGRX) {
			piani[0] = pixel;
			passi[0] = (int) passo;
		} else {
			/* ⚠ Il passo del chiamante vale per il piano Y; i due di croma sono
			 *   la meta', ed e' la convenzione del formato — non una deduzione. */
			uint32_t l = c->richiesta.larghezza, a = c->richiesta.altezza;
			uint32_t passo_y = passo ? passo : l * 2;
			piani[0] = pixel;
			piani[1] = pixel + (size_t) passo_y * a;
			piani[2] = piani[1] + (size_t) (passo_y / 2) * (a / 2);
			passi[0] = (int) passo_y;
			passi[1] = (int) (passo_y / 2);
			passi[2] = (int) (passo_y / 2);
		}
		int righe = sws_scale(c->conversione, piani, passi, 0, (int) c->richiesta.altezza,
		                      dove->data, dove->linesize);
		if (righe != (int) c->richiesta.altezza) {
			registro_dice(REG_CODIFICA,
			              "⛔ la conversione ha reso %d righe su %u: non si codifica mezzo "
			              "fotogramma", righe, c->richiesta.altezza);
			return false;
		}
	} else {
		/* yuv420p10le → yuv420p10le: tre piani gia' pronti, 2 byte per campione. */
		uint32_t l = c->richiesta.larghezza, a = c->richiesta.altezza;
		uint32_t passo_y = passo ? passo : l * 2;
		const uint8_t *y = pixel;
		const uint8_t *u = y + (size_t) passo_y * a;
		const uint8_t *v = u + (size_t) (passo_y / 2) * (a / 2);
		for (uint32_t r = 0; r < a; r++)
			memcpy(dove->data[0] + (size_t) r * dove->linesize[0],
			       y + (size_t) r * passo_y, (size_t) l * 2);
		for (uint32_t r = 0; r < a / 2; r++) {
			memcpy(dove->data[1] + (size_t) r * dove->linesize[1],
			       u + (size_t) r * (passo_y / 2), (size_t) (l / 2) * 2);
			memcpy(dove->data[2] + (size_t) r * dove->linesize[2],
			       v + (size_t) r * (passo_y / 2), (size_t) (l / 2) * 2);
		}
	}
	*us = adesso_us() - t0;

	if (c->hardware) {
		uint64_t t1 = adesso_us();
		/* ⛔ Una superficie NUOVA a ogni giro: vedi `apri_fotogrammi()`.  Il
		 *    magazzino ne tiene `SUPERFICI_PRONTE` e le riusa da se' quando
		 *    nessuno le guarda piu'. */
		av_frame_unref(c->fotogramma);
		int esito = av_hwframe_get_buffer(c->magazzino, c->fotogramma, 0);
		if (esito < 0) {
			char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
			av_strerror(esito, testo, sizeof(testo));
			registro_dice(REG_CODIFICA,
			              "⛔ nessuna superficie libera nel magazzino (%d pronte): %s",
			              SUPERFICI_PRONTE, testo);
			return false;
		}
		esito = av_hwframe_transfer_data(c->fotogramma, c->appoggio, 0);
		if (esito < 0) {
			char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
			av_strerror(esito, testo, sizeof(testo));
			registro_dice(REG_CODIFICA,
			              "⛔ il fotogramma non e' salito sulla GPU (%s → %s): %s",
			              av_get_pix_fmt_name(c->formato_gpu), c->conf.nodo, testo);
			return false;
		}
		c->fotogramma->colorspace = c->ctx->colorspace;
		c->fotogramma->color_range = c->ctx->color_range;
		*us_carico = adesso_us() - t1;
	}

	c->fotogramma->pts = c->numero;
	c->fotogramma->pict_type = c->prossimo_chiave ? AV_PICTURE_TYPE_I : AV_PICTURE_TYPE_NONE;
	if (c->prossimo_chiave)
		c->fotogramma->flags |= AV_FRAME_FLAG_KEY;
	else
		c->fotogramma->flags &= ~(unsigned) AV_FRAME_FLAG_KEY;
	return true;
}

/*
 * ⛔ LA FORMA DEI BYTE SI CONTROLLA PRIMA DI SPEDIRLI.
 *
 * ⚠ E non e' prudenza in piu': `[M]` 12 agosto 2026 il decodificatore **non
 *   protesta** quando la forma e' sbagliata — dipinge nero, o dipinge alla
 *   misura vecchia.  Il sintomo arriva tre anelli piu' in la' e non nomina la
 *   causa.  Qui invece il fotogramma non parte, e il registro dice perche'.
 */
static bool forma_va_bene(Codificatore *c, const uint8_t *dati, size_t byte, bool *chiave)
{
	if (c->richiesta.codec == CODIFICATORE_HEVC) {
		FormaAnnexB f;
		annexb_leggi(dati, byte, &f);
		*chiave = f.primo_vcl_e_chiave;
		if (byte >= 4 && !(dati[0] == 0 && dati[1] == 0 && (dati[2] == 1 || (dati[2] == 0 && dati[3] == 1)))) {
			registro_dice(REG_CODIFICA,
			              "⛔ il fotogramma non comincia con un codice di inizio: sembra a "
			              "prefisso di lunghezza (hvcC), e D1 dice Annex-B");
			return false;
		}
		if (f.primo_vcl_e_chiave && !f.parametri_prima_dell_idr) {
			registro_dice(REG_CODIFICA,
			              "⛔ chiave senza VPS+SPS+PPS davanti: in Annex-B il chunk «key» "
			              "deve portarli, o il sintomo e' schermo nero coi fotogrammi che "
			              "arrivano (v1 codificatore.c:268-272)");
			return false;
		}
		if (!c->conf.letto_dal_flusso && f.sps_byte)
			c->conf.letto_dal_flusso =
			    leggi_sps_hevc(dati + f.sps_offset, f.sps_byte, &c->conf);
	} else if (c->richiesta.codec == CODIFICATORE_H264) {
		FormaAnnexB264 f;

		annexb264_leggi(dati, byte, &f);
		*chiave = f.primo_vcl_e_chiave;
		if (byte >= 4
		    && !(dati[0] == 0 && dati[1] == 0
		         && (dati[2] == 1 || (dati[2] == 0 && dati[3] == 1)))) {
			registro_dice(REG_CODIFICA,
			              "⛔ il fotogramma H.264 non comincia con un codice di inizio: "
			              "sembra a prefisso di lunghezza (avcC), e il browser senza "
			              "`description` vuole Annex-B");
			return false;
		}
		if (f.primo_vcl_e_chiave && !f.parametri_prima_dell_idr) {
			registro_dice(REG_CODIFICA,
			              "⛔ chiave H.264 senza SPS+PPS davanti: in Annex-B il chunk "
			              "«key» deve portarli, o chi si collega dopo resta nero");
			return false;
		}
		if (!c->conf.letto_dal_flusso && f.sps_byte)
			c->conf.letto_dal_flusso =
			    leggi_sps_h264(dati + f.sps_offset, f.sps_byte, &c->conf);
	} else {
		FormaObu f;
		obu_leggi(dati, byte, &f);
		*chiave = f.primo_fotogramma_e_chiave;
		if (f.ha_chiave && !f.sequenza_prima_della_chiave) {
			registro_dice(REG_CODIFICA,
			              "⛔ chiave AV1 senza sequence header davanti: un client che si "
			              "collega dopo riceve una chiave nuda");
			return false;
		}
		if (!c->conf.letto_dal_flusso && f.seq_byte)
			c->conf.letto_dal_flusso =
			    leggi_sequenza_av1(dati + f.seq_offset, f.seq_byte, &c->conf);
	}

	/* ⛔ SECONDO TESTIMONE: la profondita' e la misura lette NEI BYTE. */
	if (c->conf.letto_dal_flusso) {
		if (c->conf.profondita_flusso != c->richiesta.profondita) {
			registro_dice(REG_CODIFICA,
			              "⛔ E2: chiesti %d bit, e il flusso ne dichiara %d",
			              c->richiesta.profondita, c->conf.profondita_flusso);
			c->conf.ha_obbedito = false;
			di(c->conf.perche_no, sizeof(c->conf.perche_no),
			   "il flusso porta %d bit invece di %d", c->conf.profondita_flusso,
			   c->richiesta.profondita);
			return false;
		}
		if (c->conf.larghezza_flusso != c->richiesta.larghezza ||
		    c->conf.altezza_flusso != c->richiesta.altezza) {
			registro_dice(REG_CODIFICA,
			              "⛔ il flusso MOSTRA %ux%u (ne codifica %ux%u) e la tela e' "
			              "%ux%u: RCP.md §6.2 vuole la misura della tela in vigore",
			              c->conf.larghezza_flusso, c->conf.altezza_flusso,
			              c->conf.larghezza_codificata, c->conf.altezza_codificata,
			              c->richiesta.larghezza, c->richiesta.altezza);
			return false;
		}
	}
	return true;
}

/* Riapre a qualita' inferiore, per il tetto dei 16 MiB. */
static bool abbassa_qualita(Codificatore *c)
{
	char errore[256] = { 0 };
	int prima = c->qualita_corrente;
	ModoQualita modo_prima = c->modo_corrente;
	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS) {
		/* ⚠ Il senza perdita esiste solo in software: il ripiego resta CRF. */
		c->modo_corrente = CODIFICATORE_QUALITA_CRF;
		c->qualita_corrente = CRF_DI_EMERGENZA;
	} else {
		/* ⚠ Il modo NON cambia: chi era a QP resta a QP.  Passare a CRF sotto il
		 *   tetto vorrebbe dire cambiare grandezza a meta' sessione, cioe' due
		 *   misure sotto la stessa etichetta. */
		c->qualita_corrente += CRF_PASSO;
		if (c->qualita_corrente > 51)
			c->qualita_corrente = 51;
	}
	if (c->qualita_corrente == prima && c->modo_corrente == modo_prima)
		return false;

	chiudi_contesto(c);
	if (apri_contesto(c, errore, sizeof(errore)) < 0) {
		registro_dice(REG_CODIFICA, "⛔ non si e' riaperto a qualita' inferiore: %s", errore);
		return false;
	}
	/* ⛔ In hardware il magazzino e' stato riaperto insieme al contesto: i
	 *    fotogrammi vanno rilegati, o il prossimo giro caricherebbe su superfici
	 *    di un magazzino chiuso. */
	if (apri_fotogrammi(c, errore, sizeof(errore)) < 0) {
		registro_dice(REG_CODIFICA, "⛔ i fotogrammi non si sono riaperti: %s", errore);
		return false;
	}
	return true;
}

/*
 * ⭐ IL CORPO COMUNE ALLE DUE STRADE — e ce n'e' UNO perche' quel che viene dopo
 *    il fotogramma preparato e' identico: la codifica, il tetto dei 16 MiB, le
 *    ricodifiche, la forma dei byte, la chiave che deve essere una chiave.
 *
 * ⛔ Averlo in due copie sarebbe la forma peggiore di tutte: il giorno in cui
 *    una regola cambia — e in questo file sono cambiate tutte, almeno una volta
 *    — una delle due copie resta indietro **e nessun banco lo vede**, perche'
 *    ciascuna e' verde per conto suo.  ⇒ Cambia SOLO come si riempie
 *    `c->fotogramma`, e quello e' l'unico `if` che le distingue.
 *
 * ⚠ Uno solo fra `pixel` e `superficie` e' non-NULL, e non e' una convenzione
 *   implicita: la guardia lo pretende e lo scrive.
 */
static bool comprimi_comune(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                            const CodificatoreSuperficie *superficie,
                            CodificatoreFotogramma *fuori)
{
	if (!c || !fuori)
		return false;
	if ((pixel == NULL) == (superficie == NULL)) {
		registro_dice(REG_CODIFICA,
		              "⛔ si comprime O dai pixel O dalla superficie, e qui ne sono "
		              "arrivati %s: non si indovina quale delle due strade voleva chi "
		              "chiama",
		              pixel ? "tutt'e due" : "nessuno");
		return false;
	}
	if (!c->conf.ha_obbedito) {
		registro_dice(REG_CODIFICA, "⛔ non ha obbedito (%s): non si spedisce niente",
		              c->conf.perche_no);
		return false;
	}
	if (c->pacchetto_in_mano) {
		registro_dice(REG_CODIFICA, "⛔ il fotogramma precedente non e' stato rilasciato");
		return false;
	}
	if (c->svuotato) {
		/* ⛔ Un contesto in scarico non accetta piu' fotogrammi: si riapre, e la
		 *    riapertura fa del prossimo una chiave.  Meglio una chiave in piu'
		 *    dichiarata che un video che si ferma al secondo fotogramma. */
		char errore[256] = { 0 };
		chiudi_contesto(c);
		if (apri_contesto(c, errore, sizeof(errore)) < 0) {
			registro_dice(REG_CODIFICA, "⛔ non si e' riaperto dopo lo scarico: %s", errore);
			return false;
		}
		if (apri_fotogrammi(c, errore, sizeof(errore)) < 0) {
			registro_dice(REG_CODIFICA, "⛔ i fotogrammi non si sono riaperti: %s", errore);
			return false;
		}
		c->svuotato = false;
		registro_dice(REG_CODIFICA, "riaperto dopo lo scarico: il prossimo e' una chiave");
	}
	memset(fuori, 0, sizeof(*fuori));

	for (uint32_t tentativo = 0;; tentativo++) {
		uint64_t us_conv = 0, us_carico = 0;
		bool pronto = superficie
		                  ? prepara_dalla_scheda(c, superficie, &us_conv, &us_carico)
		                  : prepara_fotogramma(c, pixel, passo, &us_conv, &us_carico);
		if (!pronto)
			return false;
		fuori->us_conversione = us_conv;
		fuori->us_caricamento = us_carico;

		uint64_t t0 = adesso_us();
		int esito = avcodec_send_frame(c->ctx, c->fotogramma);
		if (esito < 0) {
			char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
			av_strerror(esito, testo, sizeof(testo));
			registro_dice(REG_CODIFICA, "⛔ il fotogramma non e' entrato: %s", testo);
			return false;
		}
		esito = avcodec_receive_packet(c->ctx, c->pacchetto);
		uint32_t in_volo = 0;
		if (esito == AVERROR(EAGAIN)) {
			/*
			 * ⚠ IL CODIFICATORE HA TRATTENUTO IL FOTOGRAMMA — ed e' esattamente
			 *   il ritardo che `bframes=0` e `pred-struct=1` esistono per
			 *   togliere.  ⛔ Non si finge che non sia successo e non lo si
			 *   aggira svuotando: `avcodec_send_frame(ctx, NULL)` mette il
			 *   codificatore in scarico e **non si torna indietro** — la fase 3
			 *   si troverebbe un codificatore chiuso al secondo fotogramma, e il
			 *   sintomo sarebbe «il video si ferma dopo il primo».
			 *   ⇒ Si conta, si dichiara, e si riapre: dopo la riapertura il
			 *     fotogramma successivo e' una chiave, che RCP.md §5.2 ammette
			 *     sempre.
			 */
			in_volo = 1;
			c->conf.fotogrammi_in_volo = 1;
			registro_dice(REG_CODIFICA,
			              "⚠ «%s» ha trattenuto il fotogramma invece di consegnarlo: e' "
			              "un fotogramma di RITARDO contro i 50 ms di SPECIFICHE.md §3.2, "
			              "e le opzioni di bassa latenza non sono bastate",
			              c->componente->name);
			avcodec_send_frame(c->ctx, NULL);
			esito = avcodec_receive_packet(c->ctx, c->pacchetto);
			c->svuotato = true;
		}
		if (esito < 0) {
			char testo[AV_ERROR_MAX_STRING_SIZE] = { 0 };
			av_strerror(esito, testo, sizeof(testo));
			registro_dice(REG_CODIFICA, "⛔ nessun pacchetto: %s", testo);
			return false;
		}
		fuori->us_codifica = adesso_us() - t0;
		fuori->trattenuto = in_volo != 0;
		c->pacchetto_in_mano = true;
		/* ⭐ Il testimone del riordino, e vale identico sui due codec: un
		 *    codificatore che riordina lo dichiara qui, qualunque cosa abbia
		 *    fatto delle opzioni che gli abbiamo passato. */
		if (c->pacchetto->dts != AV_NOPTS_VALUE && c->pacchetto->pts != AV_NOPTS_VALUE &&
		    c->pacchetto->dts != c->pacchetto->pts) {
			c->conf.riordina = true;
			registro_dice(REG_CODIFICA,
			              "⚠ dts %" PRId64 " ≠ pts %" PRId64 ": il codificatore riordina, "
			              "e ogni riordino e' un fotogramma di ritardo",
			              c->pacchetto->dts, c->pacchetto->pts);
		}

		/* ───────────────────────────────────────────────────────────────────
		 * ⛔ IL TETTO DEI 16 MiB — `RCP.md` §6.2, e vincola CHI SPEDISCE. */
		if ((uint32_t) c->pacchetto->size > TETTO_FOTOGRAMMA) {
			/* ⚠ Il tetto nel messaggio si STAMPA, non si scrive a mano: una
			 *   riga di registro che dicesse «16 MiB» mentre la costante ne
			 *   dice altri manderebbe la caccia dalla parte sbagliata. */
			registro_dice(REG_CODIFICA,
			              "⛔ fotogramma di %d byte, oltre i %u del tetto di RCP.md §6.2: "
			              "si RICODIFICA a qualita' inferiore (tentativo %u), non si spedisce",
			              c->pacchetto->size, TETTO_FOTOGRAMMA, tentativo + 1);
			av_packet_unref(c->pacchetto);
			c->pacchetto_in_mano = false;

			/* ═══════════════════════════════════════════════════════════════
			 * ⛔⛔ E SU UNA **CHIAVE** NON CI SI ARRENDE — `RCP.md` §5.2, e
			 *      fino al 22 agosto 2026 questo ramo la abbandonava.
			 *
			 * §5.2 dice che il server **NON DEVE** abbandonare un fotogramma
			 * chiave, e la ragione e' che un client senza chiave **non ha un
			 * passato**: non puo' dipingere niente, ne' adesso ne' dopo.
			 *
			 * ⛔ E IL DIFETTO NON ERA «un fotogramma perso»: era una SPIRALE.
			 *    Il client resta rotto ⇒ manda `RICHIEDI_CHIAVE` ⇒ noi rifacciamo
			 *    le stesse tre ricodifiche ⇒ falliamo di nuovo ⇒ lui richiede.
			 *    `[M]` (agente D, 22 agosto 2026) ogni tentativo a 8K costa
			 *    **91-108 ms in hardware** e **1,8-3,3 s in software** ⇒
			 *    **~300 ms** ovvero **~7,8 s** buttati per ogni richiesta, a
			 *    ripetizione, e la sessione non guarisce da se'.
			 *
			 * ⭐ E LA CURA E' SICURA PERCHE' HA UN NUMERO SOTTO: `[M]` a 8K
			 *    **QP 51 da' 1,771 MiB**, cioe' il **10,6 %** del tetto.  ⇒ In
			 *    fondo alla scala una chiave **entra sempre**.
			 *
			 * ⇒ Per una chiave si continua a scendere finche' la scala ha
			 *   scalini, e quando esce brutta **lo si scrive**.  ⚠ E' l'invariante
			 *   I1 alla lettera: **brutta e viva** batte bella e morta.  Una
			 *   immagine brutta dura un fotogramma; un client rotto dura tutta
			 *   la sessione.
			 * ═══════════════════════════════════════════════════════════════ */
			if (!abbassa_qualita(c)) {
				/* ⛔ Il fondo della scala: qui non e' «mi arrendo per un conto
				 *    di tentativi», e' «non c'e' piu' niente da abbassare».  E'
				 *    l'unico caso in cui una chiave non parte, e la riga dice
				 *    QUALE dei due e'. */
				registro_dice(REG_CODIFICA,
				              "⛔⛔ nemmeno in fondo alla scala (%s %d) il fotogramma sta "
				              "sotto i %u byte: NON parte.  ⚠ E questo NON e' «mi sono "
				              "arreso dopo %u tentativi»: e' «non c'e' piu' niente da "
				              "abbassare»",
				              c->modo_corrente == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
				              c->qualita_corrente, TETTO_FOTOGRAMMA, tentativo + 1);
				return false;
			}
			if (!c->prossimo_chiave && tentativo + 1 >= RICODIFICHE_MASSIME) {
				/* ⚠ Un DELTA si abbandona, e va bene: chi lo perde ha ancora il
				 *   suo passato e il prossimo delta lo raggiunge.  ⛔ Il conto
				 *   dei tentativi vale QUI e solo qui. */
				registro_dice(REG_CODIFICA,
				              "⚠ delta abbandonato dopo %u ricodifiche: sta ancora sopra "
				              "i %u byte.  ⭐ Non e' una chiave, quindi chi guarda ha "
				              "ancora il suo passato",
				              tentativo + 1, TETTO_FOTOGRAMMA);
				return false;
			}
			if (c->prossimo_chiave)
				registro_dice(REG_CODIFICA,
				              "⚠ CHIAVE sopra il tetto: scendo a %s %d e RIPROVO "
				              "(tentativo %u).  ⛔ Una chiave non si abbandona (§5.2): "
				              "l'immagine uscira' piu' brutta, e questa riga e' la "
				              "dichiarazione.  ⭐ `[M]` in fondo alla scala (51) una "
				              "chiave 8K vale 1,771 MiB, cioe' il 10,6 %% del tetto",
				              c->modo_corrente == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
				              c->qualita_corrente, tentativo + 2);
			fuori->ricodifiche = tentativo + 1;
			continue;
		}
		break;
	}

	bool chiave = false;
	if (!forma_va_bene(c, c->pacchetto->data, (size_t) c->pacchetto->size, &chiave)) {
		av_packet_unref(c->pacchetto);
		c->pacchetto_in_mano = false;
		return false;
	}

	/* ⛔ `RCP.md` §5.2: il primo fotogramma dopo `SESSIONE`, e il primo dopo un
	 *    cambio di tela, DEVONO essere una chiave.  Se lo avevamo chiesto e non
	 *    lo e', non si spedisce: un delta marcato chiave e' quel che Chromium
	 *    scopre rileggendo il bitstream, e la nostra etichetta non lo salva. */
	if (c->prossimo_chiave && !chiave) {
		registro_dice(REG_CODIFICA,
		              "⛔ era stata chiesta una CHIAVE e il codificatore ha prodotto un "
		              "delta: non si spedisce (RCP.md §5.2)");
		av_packet_unref(c->pacchetto);
		c->pacchetto_in_mano = false;
		return false;
	}

	if (!c->prima_codifica_fatta) {
		c->prima_codifica_fatta = true;
		registro_dice(REG_CODIFICA,
		              "primo fotogramma: %s · %d byte · chiave %s · flusso: %s, %d bit, "
		              "livello %d, %ux%u · conversione %" PRIu64 " µs, caricamento "
		              "%" PRIu64 " µs, codifica %" PRIu64 " µs · %s",
		              c->conf.stringa_codec[0] ? c->conf.stringa_codec : "(non letto)",
		              c->pacchetto->size, chiave ? "si" : "no",
		              c->conf.letto_dal_flusso ? "letto" : "⛔ NON letto",
		              c->conf.profondita_flusso, c->conf.livello_flusso,
		              c->conf.larghezza_flusso, c->conf.altezza_flusso,
		              fuori->us_conversione, fuori->us_caricamento, fuori->us_codifica,
		              c->nome);
		if (c->conf.promozione_8_a_10)
			registro_dice(REG_CODIFICA,
			              "⚠ e i 10 bit sono OTTO PROMOSSI: la cattura di GNOME consegna "
			              "BGRx [M], e l'etichetta del flusso dira' «Main 10» lo stesso");
	}

	fuori->dati = c->pacchetto->data;
	fuori->byte = (size_t) c->pacchetto->size;
	fuori->chiave = chiave;
	c->prossimo_chiave = false;
	c->numero++;
	return true;
}

bool codificatore_comprimi(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                           CodificatoreFotogramma *fuori)
{
	if (!pixel) {
		registro_dice(REG_CODIFICA, "⛔ nessun pixel da comprimere");
		return false;
	}
	return comprimi_comune(c, pixel, passo, NULL, fuori);
}

bool codificatore_comprimi_scheda(Codificatore *c, const CodificatoreSuperficie *superficie,
                                  CodificatoreFotogramma *fuori)
{
	if (!c || !superficie)
		return false;
	/* ⛔ IN SOFTWARE QUESTA STRADA NON ESISTE, e lo si dice invece di produrre
	 *    un'immagine vuota: non c'e' nessun puntatore da leggere, e un
	 *    codificatore in CPU non sa che farsene di un descrittore.  ⚠ Chi chiama
	 *    deve aver guardato `codificatore_in_hardware()` PRIMA di chiedere la
	 *    scheda al produttore — qui e' gia' tardi, e questa riga serve solo a
	 *    non far passare il difetto in silenzio. */
	if (!c->hardware) {
		registro_dice(REG_CODIFICA,
		              "⛔⛔ chiesta la COPIA ZERO su «%s», che codifica in SOFTWARE: non "
		              "c'e' nessun pixel da leggere.  ⚠ Chi cattura deve chiedere la "
		              "MEMORIA quando il codificatore non e' in hardware — la strada si "
		              "sceglie prima, non qui",
		              c->componente ? c->componente->name : "(nessuno)");
		return false;
	}
	if (superficie->fd < 0 || !superficie->larghezza || !superficie->altezza
	    || !superficie->stride || !superficie->formato_drm) {
		registro_dice(REG_CODIFICA,
		              "⛔ descrittore incompleto (fd %d, %ux%u, passo %u, formato 0x%08x): "
		              "non si importa a meta'",
		              superficie->fd, superficie->larghezza, superficie->altezza,
		              superficie->stride, superficie->formato_drm);
		return false;
	}
	/* ⛔⛔ E IL PASSO DEVE ESSERE IMPORTABILE — vedi il riquadro in
	 *      `codificatore.h`.  ⚠ Chi chiama lo sa gia' e sceglie la strada
	 *      prima: questa e' l'ULTIMA linea di difesa, e serve perche' il difetto
	 *      che ferma **non da' nessun errore** — da' un'immagine inclinata che
	 *      passa ogni controllo sui millisecondi e ogni controllo sul colore. */
	if (!codificatore_stride_importabile(superficie->stride)) {
		registro_dice(REG_CODIFICA,
		              "⛔⛔ passo %u: NON e' multiplo di %u, e il driver importando il "
		              "DMA-BUF leggerebbe le righe a un passo suo — `[M]` 22 agosto 2026 "
		              "la marca non si legge piu' su 0 fotogrammi di 869, mentre le medie "
		              "di colore restano identiche entro 0,17 livelli su 255.  ⇒ NON si "
		              "comprime: meglio la copia che un'immagine sbagliata in silenzio",
		              superficie->stride, ALLINEAMENTO_SCHEDA);
		return false;
	}
	/* ⛔ E la misura del descrittore deve essere quella per cui il codificatore
	 *    e' aperto: `comprimi_comune` non la guarda — riceve una superficie e si
	 *    fida.  ⚠ Alimentare un codificatore aperto a 1920 con una superficie da
	 *    2560 non protesta: taglia o riempie, e il difetto si vede solo
	 *    nell'immagine (e' la stessa nota di `codificatore_ridimensiona`). */
	if (superficie->larghezza != c->richiesta.larghezza
	    || superficie->altezza != c->richiesta.altezza) {
		registro_dice(REG_CODIFICA,
		              "⛔ la superficie e' %ux%u e il codificatore e' aperto a %ux%u: non "
		              "si comprime un'immagine che non e' la sua",
		              superficie->larghezza, superficie->altezza, c->richiesta.larghezza,
		              c->richiesta.altezza);
		return false;
	}
	return comprimi_comune(c, NULL, 0, superficie, fuori);
}

bool codificatore_in_hardware(const Codificatore *c)
{
	return c ? c->hardware : false;
}

uint32_t codificatore_allineamento_scheda(void)
{
	return ALLINEAMENTO_SCHEDA;
}

bool codificatore_stride_importabile(uint32_t stride)
{
	return stride != 0 && (stride % ALLINEAMENTO_SCHEDA) == 0;
}

void codificatore_rilascia(Codificatore *c)
{
	if (!c || !c->pacchetto_in_mano)
		return;
	av_packet_unref(c->pacchetto);
	c->pacchetto_in_mano = false;
}
