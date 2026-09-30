/*
 * vadiretta.h — la codifica sulla scheda con libva USATA DIRETTAMENTE: H.264 e
 * HEVC, senza libavcodec in mezzo.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ FASE 18 — PERCHE' ESISTE (30 set 2026, `DECISIONI.md` §10.22 e §10.25)
 *
 * REMOTIX esce sotto PolyForm Noncommercial, e la `libavcodec` delle
 * distribuzioni e' GPL: le due licenze non stanno insieme.  ⇒ ffmpeg esce dal
 * prodotto.  Fino a oggi la codifica in hardware passava da `h264_vaapi` e
 * `hevc_vaapi` di libavcodec, che a loro volta parlano con il driver
 * attraverso libva (MIT): questo modulo parla con libva **da solo**, e fa le
 * quattro cose che facevano loro:
 *
 *   1. la CONFIGURAZIONE del driver (profilo, entrypoint, formato, controllo
 *      del bitrate, quali intestazioni impacchettate il driver vuole da noi);
 *   2. i PARAMETRI di sequenza, immagine e slice (`VAEncSequenceParameterBuffer*`
 *      ecc.), che dicono al driver come codificare;
 *   3. le INTESTAZIONI DEL FLUSSO scritte bit per bit — SPS/PPS (e VPS per
 *      HEVC), gli slice header, il SEI — con `scrittore_bit.c`, passate al
 *      driver come «packed header» e da lui messe nel flusso;
 *   4. il giro di ogni fotogramma: begin/render/end, l'attesa, la lettura dei
 *      byte codificati.
 *
 * ⛔⭐ LA REGOLA CHE GOVERNA OGNI RIGA: **riprodurre ESATTAMENTE quel che
 *     ffmpeg 7.1 faceva per noi**, non «fare un codificatore».  I flussi di
 *     oggi sono stati fotografati (`[M]` 30 set 2026, trace_headers su
 *     `h264_vaapi`/`hevc_vaapi` con le opzioni del prodotto, Intel iHD 25.2.3
 *     e Mesa radeonsi 25.0.7) e ogni campo qui sotto ha accanto il valore che
 *     si e' letto la'.  Le fonti sono `libavcodec/vaapi_encode.c`,
 *     `vaapi_encode_h264.c`, `vaapi_encode_h265.c`, `hw_base_encode_h26{4,5}.c`
 *     di ffmpeg n7.1.1, lette come specifica.  Cambiare un valore «perche'
 *     sembra meglio» e' vietato: il flusso che arriva al browser dev'essere
 *     dello stesso tipo di ieri (profilo, livello, intestazioni), o la fase
 *     18 non entra (`fasi/18-senza-ffmpeg.md` §2).
 *
 * ⚠ QUEL CHE SI E' SCELTO DI NON RIPRODURRE, dichiarato:
 *   - il SEI «identificatore» di ffmpeg (user_data_unregistered col suo UUID e
 *     la stringa `Lavc61.19.101 / VAAPI ...`) sul primo fotogramma: qui c'e'
 *     lo stesso SEI con l'UUID di REMOTIX e la stringa nostra.  `[M]`
 *     `src/pagina.html` non lo legge (il muxer pesca solo SPS e PPS);
 *   - ffmpeg ripete gli stessi parametri del contesto a ogni IDR: anche noi.
 *
 * ⛔ SU MESA (radeonsi) LE INTESTAZIONI LE RISCRIVE IL DRIVER: `[M]` 30 set
 *    2026, la traccia del flusso Radeon di oggi porta `log2_max_mv_length 16`,
 *    `transform_8x8 0` (H.264) e un VPS senza timing, `temporal_mvp 0`, PPS
 *    con `cabac_init_present 1` (HEVC) — nessuno di questi valori e' quello
 *    che ffmpeg gli aveva scritto.  ⇒ Sulla Radeon i nostri packed header sono
 *    letti dal driver e rigenerati, ed e' lo stesso che succedeva a ffmpeg:
 *    il flusso resta quello di ieri perche' il driver e' lo stesso.  E per lo
 *    stesso motivo la cornice di D-023 (la finestra di conformita' che Mesa
 *    25.0.7 non scrive) resta una riscrittura DOPO, in `codificatore.c`.
 * ---------------------------------------------------------------------------
 */
#ifndef REMOTIX_VADIRETTA_H
#define REMOTIX_VADIRETTA_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <va/va.h>

/* Il dispositivo: il nodo DRM aperto e libva inizializzata sopra. */
typedef struct {
	VADisplay display;
	int fd;
	int maggiore, minore;      /* la versione di libva che ha risposto */
	char fornitore[128];       /* `vaQueryVendorString()` */
} VaDispositivo;

/* ⛔ Il nodo si DICHIARA (`codificatore.h`, `nodo_rendering`): qui non se ne
 *    indovina uno.  Fallisce dicendo perche'. */
bool vadiretta_apri_dispositivo(const char *nodo, VaDispositivo *d, char *errore,
                                size_t errore_byte);
void vadiretta_chiudi_dispositivo(VaDispositivo *d);

typedef enum { VADIRETTA_H264 = 3, VADIRETTA_HEVC = 1 } VaDirettaCodec; /* = CodecVideo */

typedef struct {
	VaDirettaCodec codec;
	int profondita;                /* 8 o 10 (10 solo HEVC) */
	uint32_t larghezza, altezza;   /* la TELA: quel che il flusso mostra */
	uint32_t fotogrammi_al_secondo;
	/* ⛔ Profilo ed entrypoint gia' SCELTI E VERIFICATI dal chiamante con
	 *    `vaQueryConfigEntrypoints`: qui si usano, non si scoprono. */
	VAProfile profilo;
	VAEntrypoint entrypoint;
	int qp;                        /* 1..51: il QP fisso (CQP) o il fattore di qualita' (QVBR) */
	/* Il tetto di banda (fase 9): tutti zeri = CQP.  Altrimenti QVBR con
	 * `bits_per_second` = filo, `target_percentage` = punto/filo, serbatoio in
	 * bit — esattamente i tre numeri che `codificatore.c` calcola. */
	int64_t banda_punto, banda_filo;
	int serbatoio_bit;
	/* 0 = il livello lo si CALCOLA come faceva ffmpeg (`ff_h264_guess_level`
	 * / `ff_h265_guess_level`); >0 = imposto (`level_idc` o `general_level_idc`). */
	int livello_idc;
	uint32_t chiavi_ogni;          /* 0 = chiavi solo su richiesta */
	unsigned superfici_ingresso;   /* quante superfici nel magazzino d'ingresso */
} VaDirettaRichiesta;

/* ⭐ Quel che si e' letto dal driver e deciso all'apertura: la confessione. */
typedef struct {
	bool p_come_b;                     /* HEVC su iHD: i P sono slice B «GPB» */
	uint32_t larghezza_superficie, altezza_superficie; /* allineate al blocco */
	uint32_t blocco;                   /* 16 (H.264) o il CTB di HEVC */
	int livello_idc;                   /* quello scritto nell'SPS */
	unsigned packed_headers;           /* la maschera in vigore */
	unsigned packed_headers_driver;    /* quella dichiarata dal driver */
	bool hevc_attributi_letti;         /* VAConfigAttribEncHEVCFeatures/BlockSizes */
	uint32_t hevc_features, hevc_blocchi;
	bool sync_buffer;                  /* `vaSyncBuffer` c'e' (se no `vaSyncSurface`) */
	unsigned formato_rt;               /* VA_RT_FORMAT_YUV420 / _YUV420_10BPP */
	unsigned fourcc_ingresso;          /* VA_FOURCC_NV12 / VA_FOURCC_P010 */
	unsigned modo_va;                  /* VA_RC_CQP / VA_RC_QVBR */
} VaDirettaDichiarazione;

typedef struct VaDiretta VaDiretta;

VaDiretta *vadiretta_apri(const VaDispositivo *d, const VaDirettaRichiesta *r,
                          char *errore, size_t errore_byte);
void vadiretta_chiudi(VaDiretta *v);
const VaDirettaDichiarazione *vadiretta_dichiarazione(const VaDiretta *v);

/* La prossima superficie d'ingresso libera (NV12 o P010, alla misura della
 * tela).  ⚠ Il magazzino gira in tondo: dopo `superfici_ingresso` chiamate si
 * riparte dalla prima, e va bene perche' ogni codifica ASPETTA la fine. */
VASurfaceID vadiretta_superficie_ingresso(VaDiretta *v);

/*
 * Codifica `ingresso`, come chiave (IDR) se `chiave`, e rende i byte in
 * Annex-B.  ⛔ I byte appartengono a `v` fino alla chiamata successiva.
 * ⚠ ASPETTA che la scheda abbia finito: quando torna, `ingresso` si puo'
 *   riscrivere.
 */
bool vadiretta_codifica(VaDiretta *v, VASurfaceID ingresso, bool chiave,
                        const uint8_t **dati, size_t *byte, char *errore, size_t errore_byte);

/* ───────────────────────────────────────────────────────────────────────────
 * La strada DALLA MEMORIA: i pixel salgono sulla scheda.
 *
 * - BGRx/RGBx della cattura: `codificatore.c` li converte in CPU con
 *   `colori709.c` (BT.709 limitato, la stessa matrice di ieri) in NV12 o P010
 *   e li carica QUI nella superficie d'ingresso.  ⛔ Non si carica RGB per
 *   farlo convertire alla VPP: misurato peggio della conversione in CPU
 *   (`vadiretta.c`, la nota su `vadiretta_carica_nv12`).  La VPP resta alla
 *   copia zero, dove il fotogramma e' gia' sulla scheda.
 * - yuv420p10le (il banco): direttamente nella superficie P010 d'ingresso,
 *   con lo spostamento dei 10 bit in alto dentro 16 fatto qui.
 * I passi sono in BYTE.
 */
bool vadiretta_carica_nv12(VaDiretta *v, VASurfaceID dest, const uint8_t *y, uint32_t passo_y,
                           const uint8_t *uv, uint32_t passo_uv, char *errore, size_t errore_byte);
bool vadiretta_carica_p010(VaDiretta *v, VASurfaceID dest, const uint16_t *y, uint32_t passo_y,
                           const uint16_t *uv, uint32_t passo_uv, char *errore, size_t errore_byte);
bool vadiretta_carica_yuv420p10(VaDiretta *v, VASurfaceID dest, const uint8_t *pixel,
                                uint32_t passo_y, char *errore, size_t errore_byte);

#endif
