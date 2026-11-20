/*
 * vadirect.h — encoding on the card with libva USED DIRECTLY: H.264 and
 * HEVC, with no libavcodec in between.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ PHASE 18 — WHY IT EXISTS (30 Sep 2026, `DECISIONS.md` §10.22 and §10.25)
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
 *      the slice headers, the SEI — with `bit_writer.c`, handed to the
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
 *     (`phases/18-without-ffmpeg.md` §2).
 *
 * ⚠ WHAT WE CHOSE NOT TO REPRODUCE, declared:
 *   - ffmpeg's «identifier» SEI (user_data_unregistered with its UUID and the
 *     string `Lavc61.19.101 / VAAPI ...`) on the first frame: here there is
 *     the same SEI with REMOTIX's UUID and our own string.  `[M]`
 *     `src/page.html` does not read it (the muxer picks only SPS and PPS);
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
 *    does not write) stays a rewrite AFTERWARDS, in `encoder.c`.
 * ---------------------------------------------------------------------------
 */
#ifndef REMOTIX_VADIRECT_H
#define REMOTIX_VADIRECT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include <va/va.h>

/* The device: the DRM node opened and libva initialised on top of it. */
typedef struct {
	VADisplay display;
	int fd;
	int greater, less;      /* the libva version that answered */
	char vendor[128];       /* `vaQueryVendorString()` */
} VaDevice;

/* ⛔ The node is DECLARED (`encoder.h`, `nodo_rendering`): none is
 *    guessed here.  It fails saying why. */
bool vadirect_open_device(const char *node, VaDevice *d, char *error,
                                size_t error_byte);
void vadirect_close_device(VaDevice *d);

typedef enum { VADIRECT_H264 = 3, VADIRECT_HEVC = 1 } VaDirectCodec; /* = CodecVideo */

typedef struct {
	VaDirectCodec codec;
	int depth;                /* 8 or 10 (10 HEVC only) */
	uint32_t width, height;   /* the CANVAS: what the stream shows */
	uint32_t fotogrammi_al_secondo;
	/* ⛔ Profile and entrypoint already CHOSEN AND VERIFIED by the caller with
	 *    `vaQueryConfigEntrypoints`: here they are used, not discovered. */
	VAProfile profile;
	VAEntrypoint entrypoint;
	int qp;                        /* 1..51: the fixed QP (CQP) or the quality factor (QVBR) */
	/* The bandwidth ceiling (phase 9): all zeros = CQP.  Otherwise QVBR with
	 * `bits_per_second` = wire, `target_percentage` = target/wire, buffer in
	 * bits — exactly the three numbers that `encoder.c` computes. */
	int64_t bandwidth_point, bandwidth_wire;
	int reservoir_bit;
	/* 0 = the level is COMPUTED as ffmpeg did (`ff_h264_guess_level`
	 * / `ff_h265_guess_level`); >0 = imposed (`level_idc` or `general_level_idc`). */
	int level_idc;
	uint32_t chiavi_ogni;          /* 0 = keyframes on request only */
	unsigned input_surfaces;   /* how many surfaces in the input pool */
} VaDirectRequest;

/* ⭐ What was read from the driver and decided at opening: the confession. */
typedef struct {
	bool p_come_b;                     /* HEVC on iHD: P frames are «GPB» B slices */
	uint32_t surface_width, surface_height; /* aligned to the block */
	uint32_t block;                   /* 16 (H.264) or the HEVC CTB */
	int level_idc;                   /* the one written in the SPS */
	unsigned packed_headers;           /* the mask in force */
	unsigned packed_headers_driver;    /* the one declared by the driver */
	bool hevc_attributes_read;         /* VAConfigAttribEncHEVCFeatures/BlockSizes */
	uint32_t hevc_features, hevc_blocks;
	bool sync_buffer;                  /* `vaSyncBuffer` is there (otherwise `vaSyncSurface`) */
	unsigned rt_format;               /* VA_RT_FORMAT_YUV420 / _YUV420_10BPP */
	unsigned input_fourcc;          /* VA_FOURCC_NV12 / VA_FOURCC_P010 */
	unsigned va_mode;                  /* VA_RC_CQP / VA_RC_QVBR */
} VaDirectDeclaration;

typedef struct VaDirect VaDirect;

VaDirect *vadirect_open(const VaDevice *d, const VaDirectRequest *r,
                          char *error, size_t error_byte);
void vadirect_close(VaDirect *v);

/* ⭐ E-R2: the wait for an encode timed out; the context must not be used again (drop and reopen). */
bool vadirect_lost(const VaDirect *v);
const VaDirectDeclaration *vadirect_declaration(const VaDirect *v);

/* The next free input surface (NV12 or P010, at the ALIGNED size
 * `surface_width` x `surface_height`: the rows and columns past the canvas
 * are the padding the card encodes and the SPS crops, and they are filled
 * with copies of the edge by the loads below, or by the VPP on zero copy).
 * ⚠ The pool goes round in a circle: after `input_surfaces` calls it
 * starts again from the first, and that is fine because every encode WAITS
 * for the end. */
VASurfaceID vadirect_input_surface(VaDirect *v);

/*
 * Encodes `ingress`, as a keyframe (IDR) if `key`, and returns the bytes
 * in Annex-B.  ⛔ The bytes belong to `v` until the next call.
 * ⚠ It WAITS for the card to finish: when it returns, `ingress` can be
 *   rewritten.
 */
bool vadirect_encode(VaDirect *v, VASurfaceID ingress, bool key,
                        const uint8_t **data, size_t *byte, char *error, size_t error_byte);

/* ───────────────────────────────────────────────────────────────────────────
 * The route FROM MEMORY: the pixels go up to the card.
 *
 * - BGRx/RGBx from capture: `encoder.c` converts them on the CPU with
 *   `colors709.c` (BT.709 limited, yesterday's same matrix) into NV12 or P010
 *   and uploads them HERE into the input surface.  ⛔ RGB is not uploaded to
 *   have the VPP convert it: measured worse than the CPU conversion
 *   (`vadirect.c`, the note on `vadirect_load_nv12`).  The VPP stays with
 *   zero copy, where the frame is already on the card.
 * - yuv420p10le (the bench): directly into the P010 input surface, with the
 *   shift of the 10 bits to the top of 16 done here.
 * Strides are in BYTES.  The planes are the CANVAS (`width` x `height`); the
 * padding up to the aligned surface is written here, copies of the edge.
 */
bool vadirect_load_nv12(VaDirect *v, VASurfaceID dest, const uint8_t *y, uint32_t stride_y,
                           const uint8_t *uv, uint32_t stride_uv, char *error, size_t error_byte);
bool vadirect_load_p010(VaDirect *v, VASurfaceID dest, const uint16_t *y, uint32_t stride_y,
                           const uint16_t *uv, uint32_t stride_uv, char *error, size_t error_byte);
bool vadirect_load_yuv420p10(VaDirect *v, VASurfaceID dest, const uint8_t *pixel,
                                uint32_t stride_y, char *error, size_t error_byte);

#endif
