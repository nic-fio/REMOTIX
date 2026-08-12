/*
 * codificatore.c — HEVC Main10 e AV1, in software, con la confessione letta sui
 * byte.  Il perche' di ogni scelta sta in `codificatore.h`; qui c'e' il come, e
 * accanto a ogni riga strana la misura che l'ha resa necessaria.
 *
 * ⛔ Non si tocca nessuna GPU: l'accelerazione e' la fase 8.
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
#include <libavutil/imgutils.h>
#include <libavutil/opt.h>
#include <libswscale/swscale.h>

/* ⚠ Area propria invece di una delle sei di `registro.h`: quel file non e' di
 *   questa sotto-fase e non si tocca.  La riga per centralizzarla — `#define
 *   REG_VIDEO "video"` — sta nel rapporto, insieme a quelle del Makefile. */
#define REG_CODIFICA "video"

/* `RCP.md` §6.2: «il server NON DEVE produrre un fotogramma piu' lungo di 16
 * MiB.  Se la codifica ne producesse uno piu' grande, DEVE ricodificarlo a
 * qualita' inferiore e SCRIVERLO NEL REGISTRO — mai spedirlo.» */
#define TETTO_FOTOGRAMMA (16u * 1024u * 1024u)
#define RICODIFICHE_MASSIME 3

/* ⚠ Il primo scalino quando il tetto morde, e il passo dei successivi.  Sono
 *   numeri di comodo dichiarati: il punto di lavoro del bitrate e' la fase 9. */
#define CRF_DI_EMERGENZA 24
#define CRF_PASSO 6

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
	if (lb_bit(&l, 1)) {                        /* conformance_window_flag */
		lb_ue(&l); lb_ue(&l); lb_ue(&l); lb_ue(&l);
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

struct Codificatore {
	CodificatoreRichiesta richiesta;
	const AVCodec *componente;
	AVCodecContext *ctx;
	AVFrame *fotogramma;
	AVPacket *pacchetto;
	struct SwsContext *conversione;
	CodificatoreConfessione conf;
	char nome[96];

	bool prossimo_chiave;         /* ⛔ la prossima e' una chiave VERA */
	bool prima_codifica_fatta;
	bool svuotato;                /* ⚠ e' stato messo in scarico: va riaperto */
	int qualita_corrente;         /* CRF in vigore, dopo le eventuali ricodifiche */
	ModoQualita modo_corrente;
	int64_t numero;               /* il pts, che qui e' il contatore dei fotogrammi */
	bool pacchetto_in_mano;
};

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
	return codec == CODIFICATORE_HEVC ? "libx265" : "libsvtav1";
}

static enum AVCodecID id_di(CodecVideo codec)
{
	return codec == CODIFICATORE_HEVC ? AV_CODEC_ID_HEVC : AV_CODEC_ID_AV1;
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
		avcodec_free_context(&c->ctx);
}

static int apri_contesto(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;
	enum AVPixelFormat formato = (r->profondita == 10) ? AV_PIX_FMT_YUV420P10LE
	                                                   : AV_PIX_FMT_YUV420P;

	if (!accetta_formato(c->componente, formato)) {
		di(errore, errore_byte,
		   "«%s» non accetta %s: ⛔ non si ripiega su un altro formato, si dichiara",
		   c->componente->name, av_get_pix_fmt_name(formato));
		return -1;
	}

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
	c->ctx->max_b_frames = 0;   /* ⛔ deciso, non ereditato: vedi opzioni_hevc() */
	c->ctx->gop_size = r->chiavi_ogni ? (int) r->chiavi_ogni : INT_MAX;
	c->ctx->profile = (r->codec == CODIFICATORE_HEVC)
	                      ? (r->profondita == 10 ? AV_PROFILE_HEVC_MAIN_10 : AV_PROFILE_HEVC_MAIN)
	                      : AV_PROFILE_AV1_MAIN;

	/*
	 * ⛔ IL COLORE SI DICHIARA, O F2.6 MISURA LA MATRICE INVECE DEI PIXEL.
	 *
	 * F2.2 `[M]`: Mutter **non dichiara** range, matrice, trasferimento ne'
	 * primari (quattro zeri, cioe' UNKNOWN), e i pixel alla cattura sono RGB —
	 * *«la matrice la sceglie F2.3»*.  Sceglie **BT.709 a range limitato**:
	 *
	 *   - 709 perche' e' quel che un desktop sRGB si aspetta, ed e' quel che i
	 *     due browser applicano di difetto quando il flusso non dice niente:
	 *     scrivere una cosa diversa dal difetto senza necessita' vorrebbe dire
	 *     scommettere che tutti leggano la VUI;
	 *   - range limitato perche' e' il difetto che ogni decodificatore azzecca,
	 *     ⛔ e **non costa precisione qui**: 8 bit pieni sono 256 livelli, e
	 *     l'intervallo limitato a 10 bit ne ha 877.  Il range pieno comprerebbe
	 *     un margine che questa sorgente non ha, al prezzo di una VUI che
	 *     qualcuno potrebbe ignorare.
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

	int esito = (r->codec == CODIFICATORE_HEVC) ? opzioni_hevc(c, errore, errore_byte)
	                                            : opzioni_av1(c, errore, errore_byte);
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
	c->conf.ha_obbedito = true;
	c->conf.perche_no[0] = 0;

	if (c->ctx->codec->id != id_di(r->codec))
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "«%s» non e' un codificatore %s", c->ctx->codec->name,
		   r->codec == CODIFICATORE_HEVC ? "HEVC" : "AV1");
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
		   richiesta->codec == CODIFICATORE_HEVC ? "HEVC" : "AV1");
		free(c);
		return NULL;
	}

	if (apri_contesto(c, errore, errore_byte) < 0) {
		free(c);
		return NULL;
	}

	c->fotogramma = av_frame_alloc();
	if (!c->fotogramma) {
		di(errore, errore_byte, "niente memoria per il fotogramma");
		codificatore_libera(c);
		return NULL;
	}
	c->fotogramma->format = c->ctx->pix_fmt;
	c->fotogramma->width = c->ctx->width;
	c->fotogramma->height = c->ctx->height;
	c->fotogramma->colorspace = c->ctx->colorspace;
	c->fotogramma->color_range = c->ctx->color_range;
	if (av_frame_get_buffer(c->fotogramma, 0) < 0) {
		di(errore, errore_byte, "niente memoria per i piani del fotogramma");
		codificatore_libera(c);
		return NULL;
	}

	if (richiesta->formato == CODIFICATORE_PIXEL_BGRX) {
		/*
		 * ⛔ La conversione la fa `libswscale`, non noi: `CODER.md` §4.1 —
		 *    «ogni componente che scriviamo e' un componente da mantenere per
		 *    sempre», e di RGB→YUV esiste **una** implementazione standard.
		 * ⚠ E il conto di v1 va rimisurato, non ricopiato: li' la conversione
		 *   era il collo di bottiglia **misurato** (12,5 ms contro 3,8 di
		 *   codifica, a 2560×1024 in NV12).  A 10 bit i byte in uscita
		 *   raddoppiano.
		 */
		c->conversione = sws_getContext((int) richiesta->larghezza, (int) richiesta->altezza,
		                                AV_PIX_FMT_BGR0,
		                                (int) richiesta->larghezza, (int) richiesta->altezza,
		                                c->ctx->pix_fmt, SWS_BILINEAR, NULL, NULL, NULL);
		if (!c->conversione) {
			di(errore, errore_byte, "swscale non ha aperto BGRx → %s",
			   av_get_pix_fmt_name(c->ctx->pix_fmt));
			codificatore_libera(c);
			return NULL;
		}
		/* ⛔ La matrice si IMPONE.  Senza questa chiamata swscale usa il suo
		 *    difetto, che non e' scritto da nessuna parte nel nostro codice: due
		 *    versioni di ffmpeg potrebbero convertire diversamente e nessuno se
		 *    ne accorgerebbe guardando l'immagine. */
		const int *tavola = sws_getCoefficients(SWS_CS_ITU709);
		sws_setColorspaceDetails(c->conversione, tavola, 1 /* sorgente: RGB pieno */,
		                         tavola, 0 /* uscita: limitato */, 0, 1 << 16, 1 << 16);
		/* ⚠ La sorgente ha 8 bit veri (`[M]` F2.2): il Main10 che ne esce e' 8
		 *   bit PROMOSSI, e la promozione si dichiara invece di subirla. */
		c->conf.promozione_8_a_10 = (richiesta->profondita == 10);
	}

	snprintf(c->nome, sizeof(c->nome), "%s %s via %s (in software)",
	         richiesta->codec == CODIFICATORE_HEVC ? "HEVC" : "AV1",
	         richiesta->profondita == 10 ? "10 bit" : "8 bit",
	         c->componente->name);

	registro_dice(REG_CODIFICA, "aperto: %s · %ux%u · %s · chiavi %s%s", c->nome,
	              richiesta->larghezza, richiesta->altezza,
	              richiesta->modo == CODIFICATORE_QUALITA_LOSSLESS ? "senza perdita" : "CRF",
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
	chiudi_contesto(c);
	free(c);
}

const char *codificatore_nome(const Codificatore *c)
{
	return c ? c->nome : "(nessuno)";
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
	 *    nell'immagine. */
	chiudi_contesto(c);
	if (c->fotogramma)
		av_frame_free(&c->fotogramma);
	if (c->conversione) {
		sws_freeContext(c->conversione);
		c->conversione = NULL;
	}
	c->richiesta.larghezza = larghezza;
	c->richiesta.altezza = altezza;
	c->prima_codifica_fatta = false;
	c->conf.letto_dal_flusso = false;

	if (apri_contesto(c, errore, errore_byte) < 0)
		return false;
	c->fotogramma = av_frame_alloc();
	if (!c->fotogramma) {
		di(errore, errore_byte, "niente memoria per il fotogramma");
		return false;
	}
	c->fotogramma->format = c->ctx->pix_fmt;
	c->fotogramma->width = c->ctx->width;
	c->fotogramma->height = c->ctx->height;
	c->fotogramma->colorspace = c->ctx->colorspace;
	c->fotogramma->color_range = c->ctx->color_range;
	if (av_frame_get_buffer(c->fotogramma, 0) < 0) {
		di(errore, errore_byte, "niente memoria per i piani");
		return false;
	}
	if (c->richiesta.formato == CODIFICATORE_PIXEL_BGRX) {
		c->conversione = sws_getContext((int) larghezza, (int) altezza, AV_PIX_FMT_BGR0,
		                                (int) larghezza, (int) altezza, c->ctx->pix_fmt,
		                                SWS_BILINEAR, NULL, NULL, NULL);
		if (!c->conversione) {
			di(errore, errore_byte, "swscale non ha riaperto alla misura nuova");
			return false;
		}
		const int *tavola = sws_getCoefficients(SWS_CS_ITU709);
		sws_setColorspaceDetails(c->conversione, tavola, 1, tavola, 0, 0, 1 << 16, 1 << 16);
	}

	/* ⛔ `RCP.md` §5.2: il primo fotogramma alla misura nuova DEVE essere una
	 *    chiave, e una chiave VERA.  `apri_contesto` l'ha gia' preteso; la riga
	 *    resta perche' la regola sta scritta qui, non altrove. */
	c->prossimo_chiave = true;
	registro_dice(REG_CODIFICA,
	              "tela nuova %ux%u: riaperto, e il prossimo fotogramma e' una chiave "
	              "(RCP.md §5.2)", larghezza, altezza);
	return true;
}

/* Riempie `c->fotogramma` dai pixel del chiamante. */
static bool prepara_fotogramma(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                               uint64_t *us)
{
	uint64_t t0 = adesso_us();
	if (av_frame_make_writable(c->fotogramma) < 0)
		return false;

	if (c->richiesta.formato == CODIFICATORE_PIXEL_BGRX) {
		const uint8_t *piani[4] = { pixel, NULL, NULL, NULL };
		int passi[4] = { (int) passo, 0, 0, 0 };
		int righe = sws_scale(c->conversione, piani, passi, 0, (int) c->richiesta.altezza,
		                      c->fotogramma->data, c->fotogramma->linesize);
		if (righe != (int) c->richiesta.altezza) {
			registro_dice(REG_CODIFICA,
			              "⛔ la conversione ha reso %d righe su %u: non si codifica mezzo "
			              "fotogramma", righe, c->richiesta.altezza);
			return false;
		}
	} else {
		/* yuv420p10le: tre piani gia' pronti, 2 byte per campione.
		 * ⚠ Il passo del chiamante vale per il piano Y; i due di croma sono la
		 *   meta', ed e' la convenzione del formato — non una deduzione. */
		uint32_t l = c->richiesta.larghezza, a = c->richiesta.altezza;
		uint32_t passo_y = passo ? passo : l * 2;
		const uint8_t *y = pixel;
		const uint8_t *u = y + (size_t) passo_y * a;
		const uint8_t *v = u + (size_t) (passo_y / 2) * (a / 2);
		for (uint32_t r = 0; r < a; r++)
			memcpy(c->fotogramma->data[0] + (size_t) r * c->fotogramma->linesize[0],
			       y + (size_t) r * passo_y, (size_t) l * 2);
		for (uint32_t r = 0; r < a / 2; r++) {
			memcpy(c->fotogramma->data[1] + (size_t) r * c->fotogramma->linesize[1],
			       u + (size_t) r * (passo_y / 2), (size_t) (l / 2) * 2);
			memcpy(c->fotogramma->data[2] + (size_t) r * c->fotogramma->linesize[2],
			       v + (size_t) r * (passo_y / 2), (size_t) (l / 2) * 2);
		}
	}
	c->fotogramma->pts = c->numero;
	c->fotogramma->pict_type = c->prossimo_chiave ? AV_PICTURE_TYPE_I : AV_PICTURE_TYPE_NONE;
	if (c->prossimo_chiave)
		c->fotogramma->flags |= AV_FRAME_FLAG_KEY;
	*us = adesso_us() - t0;
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
			              "⛔ il flusso dichiara %ux%u e la tela e' %ux%u: RCP.md §6.2 vuole "
			              "la misura della tela in vigore",
			              c->conf.larghezza_flusso, c->conf.altezza_flusso,
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
	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS) {
		c->modo_corrente = CODIFICATORE_QUALITA_CRF;
		c->qualita_corrente = CRF_DI_EMERGENZA;
	} else {
		c->qualita_corrente += CRF_PASSO;
		if (c->qualita_corrente > 51)
			c->qualita_corrente = 51;
	}
	if (c->qualita_corrente == prima && c->modo_corrente == CODIFICATORE_QUALITA_CRF)
		return false;

	chiudi_contesto(c);
	if (apri_contesto(c, errore, sizeof(errore)) < 0) {
		registro_dice(REG_CODIFICA, "⛔ non si e' riaperto a qualita' inferiore: %s", errore);
		return false;
	}
	return true;
}

bool codificatore_comprimi(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                           CodificatoreFotogramma *fuori)
{
	if (!c || !pixel || !fuori)
		return false;
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
		c->svuotato = false;
		registro_dice(REG_CODIFICA, "riaperto dopo lo scarico: il prossimo e' una chiave");
	}
	memset(fuori, 0, sizeof(*fuori));

	for (uint32_t tentativo = 0;; tentativo++) {
		uint64_t us_conv = 0;
		if (!prepara_fotogramma(c, pixel, passo, &us_conv))
			return false;
		fuori->us_conversione = us_conv;

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
			if (tentativo + 1 >= RICODIFICHE_MASSIME || !abbassa_qualita(c)) {
				registro_dice(REG_CODIFICA,
				              "⛔ nemmeno dopo %u ricodifiche sta sotto i 16 MiB: il "
				              "fotogramma NON parte", tentativo + 1);
				return false;
			}
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
		              "livello %d, %ux%u · conversione %" PRIu64 " µs, codifica %" PRIu64 " µs",
		              c->conf.stringa_codec[0] ? c->conf.stringa_codec : "(non letto)",
		              c->pacchetto->size, chiave ? "si" : "no",
		              c->conf.letto_dal_flusso ? "letto" : "⛔ NON letto",
		              c->conf.profondita_flusso, c->conf.livello_flusso,
		              c->conf.larghezza_flusso, c->conf.altezza_flusso,
		              fuori->us_conversione, fuori->us_codifica);
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

void codificatore_rilascia(Codificatore *c)
{
	if (!c || !c->pacchetto_in_mano)
		return;
	av_packet_unref(c->pacchetto);
	c->pacchetto_in_mano = false;
}
