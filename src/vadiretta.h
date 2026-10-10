/*
 * vadiretta.h — encoding on the card with libva USED DIRECTLY: H.264 and
 * HEVC, with no libavcodec in between.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ PHASE 18 — WHY IT EXISTS (30 Sep 2026, `DECISIONI.md` §10.22 and §10.25)
 *
 * REMOTIX ships under PolyForm Noncommercial, and the distributions'
 * `libavcodec` is GPL: the two licences do not go together.  ⇒ ffmpeg leaves
 * the product.  Until today hardware encoding went through libavcodec's
 * `h264_vaapi` and `hevc_vaapi`, which in turn talk to the driver through
 * libva (MIT): this module talks to libva **on its own**, and does the four
 * things they did:
 *
 *   1. the driver CONFIGURATION (profile, entrypoint, format, bitrate
 *      control, which packed headers the driver wants from us);
 *   2. the sequence, picture and slice PARAMETERS (`VAEncSequenceParameterBuffer*`
 *      etc.), which tell the driver how to encode;
 *   3. the STREAM HEADERS written bit by bit — SPS/PPS (and VPS for HEVC),
 *      the slice headers, the SEI — with `scrittore_bit.c`, handed to the
 *      driver as «packed header» and put by it into the stream;
 *   4. the round of every frame: begin/render/end, the wait, reading the
 *      encoded bytes.
 *
 * ⛔⭐ THE RULE THAT GOVERNS EVERY LINE: **reproduce EXACTLY what ffmpeg 7.1
 *     did for us**, not «write an encoder».  Today's streams were
 *     photographed (`[M]` 30 Sep 2026, trace_headers on
 *     `h264_vaapi`/`hevc_vaapi` with the product's options, Intel iHD 25.2.3
 *     and Mesa radeonsi 25.0.7) and every field below has next to it the
 *     value read there.  The sources are ffmpeg n7.1.1's
 *     `libavcodec/vaapi_encode.c`, `vaapi_encode_h264.c`,
 *     `vaapi_encode_h265.c`, `hw_base_encode_h26{4,5}.c`, read as a
 *     specification.  Changing a value «because it looks better» is
 *     forbidden: the stream reaching the browser must be of the same kind as
 *     yesterday's (profile, level, headers), or phase 18 does not get in
 *     (`fasi/18-senza-ffmpeg.md` §2).
 *
 * ⚠ WHAT WE CHOSE NOT TO REPRODUCE, declared:
 *   - ffmpeg's «identifier» SEI (user_data_unregistered with its UUID and the
 *     string `Lavc61.19.101 / VAAPI ...`) on the first frame: here there is
 *     the same SEI with REMOTIX's UUID and our own string.  `[M]`
 *     `src/pagina.html` does not read it (the muxer picks only SPS and PPS);
 *   - ffmpeg repeats the same context parameters at every IDR: so do we.
 *
 * ⛔ ON MESA (radeonsi) THE DRIVER REWRITES THE HEADERS: `[M]` 30 Sep
 *    2026, the trace of today's Radeon stream carries `log2_max_mv_length 16`,
 *    `transform_8x8 0` (H.264) and a VPS without timing, `temporal_mvp 0`, PPS
 *    with `cabac_init_present 1` (HEVC) — none of these values is the one
 *    ffmpeg had written to it.  ⇒ On the Radeon our packed headers are read
 *    by the driver and regenerated, and the same happened to ffmpeg: the
 *    stream stays yesterday's because the driver is the same.  And for the
 *    same reason the D-023 frame (the conformance window that Mesa 25.0.7
 *    does not write) stays a rewrite AFTERWARDS, in `codificatore.c`.
 * ---------------------------------------------------------------------------
 */
#ifndef REMOTIX_VADIRETTA_H
#define REMOTIX_VADIRETTA_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <va/va.h>

/* The device: the DRM node opened and libva initialised on top of it. */
typedef struct {
	VADisplay display;
	int fd;
	int maggiore, minore;      /* the libva version that answered */
	char fornitore[128];       /* `vaQueryVendorString()` */
} VaDispositivo;

/* ⛔ The node is DECLARED (`codificatore.h`, `nodo_rendering`): none is
 *    guessed here.  It fails saying why. */
bool vadiretta_apri_dispositivo(const char *nodo, VaDispositivo *d, char *errore,
                                size_t errore_byte);
void vadiretta_chiudi_dispositivo(VaDispositivo *d);

typedef enum { VADIRETTA_H264 = 3, VADIRETTA_HEVC = 1 } VaDirettaCodec; /* = CodecVideo */

typedef struct {
	VaDirettaCodec codec;
	int profondita;                /* 8 or 10 (10 HEVC only) */
	uint32_t larghezza, altezza;   /* the CANVAS: what the stream shows */
	uint32_t fotogrammi_al_secondo;
	/* ⛔ Profile and entrypoint already CHOSEN AND VERIFIED by the caller with
	 *    `vaQueryConfigEntrypoints`: here they are used, not discovered. */
	VAProfile profilo;
	VAEntrypoint entrypoint;
	int qp;                        /* 1..51: the fixed QP (CQP) or the quality factor (QVBR) */
	/* The bandwidth ceiling (phase 9): all zeros = CQP.  Otherwise QVBR with
	 * `bits_per_second` = wire, `target_percentage` = target/wire, buffer in
	 * bits — exactly the three numbers that `codificatore.c` computes. */
	int64_t banda_punto, banda_filo;
	int serbatoio_bit;
	/* 0 = the level is COMPUTED as ffmpeg did (`ff_h264_guess_level`
	 * / `ff_h265_guess_level`); >0 = imposed (`level_idc` or `general_level_idc`). */
	int livello_idc;
	uint32_t chiavi_ogni;          /* 0 = keyframes on request only */
	unsigned superfici_ingresso;   /* how many surfaces in the input pool */
} VaDirettaRichiesta;

/* ⭐ What was read from the driver and decided at opening: the confession. */
typedef struct {
	bool p_come_b;                     /* HEVC on iHD: P frames are «GPB» B slices */
	uint32_t larghezza_superficie, altezza_superficie; /* aligned to the block */
	uint32_t blocco;                   /* 16 (H.264) or the HEVC CTB */
	int livello_idc;                   /* the one written in the SPS */
	unsigned packed_headers;           /* the mask in force */
	unsigned packed_headers_driver;    /* the one declared by the driver */
	bool hevc_attributi_letti;         /* VAConfigAttribEncHEVCFeatures/BlockSizes */
	uint32_t hevc_features, hevc_blocchi;
	bool sync_buffer;                  /* `vaSyncBuffer` is there (otherwise `vaSyncSurface`) */
	unsigned formato_rt;               /* VA_RT_FORMAT_YUV420 / _YUV420_10BPP */
	unsigned fourcc_ingresso;          /* VA_FOURCC_NV12 / VA_FOURCC_P010 */
	unsigned modo_va;                  /* VA_RC_CQP / VA_RC_QVBR */
} VaDirettaDichiarazione;

typedef struct VaDiretta VaDiretta;

VaDiretta *vadiretta_apri(const VaDispositivo *d, const VaDirettaRichiesta *r,
                          char *errore, size_t errore_byte);
void vadiretta_chiudi(VaDiretta *v);
const VaDirettaDichiarazione *vadiretta_dichiarazione(const VaDiretta *v);

/* The next free input surface (NV12 or P010, at the size of the canvas).
 * ⚠ The pool goes round in a circle: after `superfici_ingresso` calls it
 * starts again from the first, and that is fine because every encode WAITS
 * for the end. */
VASurfaceID vadiretta_superficie_ingresso(VaDiretta *v);

/*
 * Encodes `ingresso`, as a keyframe (IDR) if `chiave`, and returns the bytes
 * in Annex-B.  ⛔ The bytes belong to `v` until the next call.
 * ⚠ It WAITS for the card to finish: when it returns, `ingresso` can be
 *   rewritten.
 */
bool vadiretta_codifica(VaDiretta *v, VASurfaceID ingresso, bool chiave,
                        const uint8_t **dati, size_t *byte, char *errore, size_t errore_byte);

/* ───────────────────────────────────────────────────────────────────────────
 * The route FROM MEMORY: the pixels go up to the card.
 *
 * - BGRx/RGBx from capture: `codificatore.c` converts them on the CPU with
 *   `colori709.c` (BT.709 limited, yesterday's same matrix) into NV12 or P010
 *   and uploads them HERE into the input surface.  ⛔ RGB is not uploaded to
 *   have the VPP convert it: measured worse than the CPU conversion
 *   (`vadiretta.c`, the note on `vadiretta_carica_nv12`).  The VPP stays with
 *   zero copy, where the frame is already on the card.
 * - yuv420p10le (the bench): directly into the P010 input surface, with the
 *   shift of the 10 bits to the top of 16 done here.
 * Strides are in BYTES.
 */
bool vadiretta_carica_nv12(VaDiretta *v, VASurfaceID dest, const uint8_t *y, uint32_t passo_y,
                           const uint8_t *uv, uint32_t passo_uv, char *errore, size_t errore_byte);
bool vadiretta_carica_p010(VaDiretta *v, VASurfaceID dest, const uint16_t *y, uint32_t passo_y,
                           const uint16_t *uv, uint32_t passo_uv, char *errore, size_t errore_byte);
bool vadiretta_carica_yuv420p10(VaDiretta *v, VASurfaceID dest, const uint8_t *pixel,
                                uint32_t passo_y, char *errore, size_t errore_byte);

#endif
