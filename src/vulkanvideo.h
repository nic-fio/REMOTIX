/*
 * vulkanvideo.h — encoding on the card with VULKAN VIDEO: H.264 and HEVC,
 * with `VK_KHR_video_encode_queue` and the two codec extensions, without
 * libva, without ffmpeg, without GStreamer.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ PHASE 19 — WHY IT EXISTS (1 Oct 2026, `DECISIONI.md` §10.27)
 *
 * The user's words: *«encoding must happen with standard tools, preferably
 * with Vulkan, which is common to all 4 architectures»*.  VA-API
 * (`src/vadiretta.c`, phase 18) talks to Intel and AMD, but the proprietary
 * NVIDIA driver does not encode via VA-API, and on a 5070 REMOTIX fell back
 * to the processor.  Vulkan Video is the API that ALL vendors expose (AMD
 * with RADV, NVIDIA with the proprietary driver, Intel with ANV — `[M]`
 * 1 Oct 2026 only behind `ANV_DEBUG=video-encode` with Mesa 25.0.7 and
 * 26.2.3, that is experimental).  ⇒ The route is chosen BY CAPABILITY, not
 * by brand: 1) Vulkan Video if the card offers it, 2) VA-API, 3) nothing.
 *
 * ⛔ Licences: the Vulkan loader and the headers are Apache-2.0, the drivers
 *    are in the system.  No third-party library in between.
 *
 * ⭐ WHAT IT DOES, in the same order as `vadiretta.h`:
 *   1. DISCOVERY: for a DRM node, whether the card can encode H.264 and/or
 *      HEVC in Vulkan, with maximum size, bitrate modes, allowed QPs —
 *      `vulkanvideo_capacita()`, to choose the route and for the installer's
 *      preliminary check;
 *   2. the SESSION: profile, formats, DPB, the parameters (SPS/PPS, and VPS
 *      for HEVC) written as `StdVideo*` with the SAME values that
 *      `vadiretta.c` puts in its headers — High at 8 bits, Main /
 *      Main 10, no B, a single reference, BT.709 limited in the VUI, the
 *      level computed as ffmpeg did or imposed (`RCP.md` §4.3);
 *   3. the INPUT: zero copy from DMA-BUF (`VK_EXT_external_memory_dma_buf` +
 *      `VK_EXT_image_drm_format_modifier`) of BGRx/RGBx frames, and the
 *      RGB → NV12 (or P010) BT.709 limited conversion done by a compute
 *      shader ON THE CARD, with the same coefficients and the same chroma
 *      filter as `colori709.c` (bit for bit: the planes entering the
 *      encoder are those the route from memory produces today);
 *      and input from memory (pixels on the CPU), which goes up to the card
 *      in RGB and is converted with the same shader;
 *   4. the round of every frame: conversion, encoding, wait, reading the
 *      bytes; Annex-B output with SPS/PPS(/VPS) in front of every keyframe.
 *
 * ⛔ THE DRIVER WRITES THE HEADERS (`vkGetEncodedVideoSessionParametersKHR`)
 *    from our `StdVideo*`: it is the one that knows what it really encodes,
 *    and if it had to change something it declares it (`hasOverrides`) and
 *    that is written to the log.  The check that the stream is of the same
 *    kind as yesterday's (profile, level, size, colour) is done by the bench
 *    with ffprobe and with Chrome, and in the product `forma_va_bene()` in
 *    `codificatore.c` rereads the SPS at every keyframe, as for VA-API.
 *
 * ⚠ What is NOT there, declared: the identifier SEI and the buffering SEIs
 *   (ffmpeg wrote them, `vadiretta.c` reproduces them for H.264):
 *   `[M]` no browser reads them and the page's muxer picks only SPS/PPS.
 *   B frames: never (low latency).  A single slice per frame.
 * ---------------------------------------------------------------------------
 */
#ifndef REMOTIX_VULKANVIDEO_H
#define REMOTIX_VULKANVIDEO_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum { VULKANVIDEO_H264 = 3, VULKANVIDEO_HEVC = 1 } VulkanVideoCodec; /* = CodecVideo */

/* The bitrate control modes the card declares (mask). */
#define VULKANVIDEO_RC_CQP 1u /* VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DISABLED */
#define VULKANVIDEO_RC_CBR 2u
#define VULKANVIDEO_RC_VBR 4u

/* ═══════════════════════════════════════════════════════════════════════════
 * 1. DISCOVERY — for a DRM node, what the card can do in Vulkan.
 *
 * ⛔ Three outcomes and not two (`LEZIONI.md` §1.9): `vulkan_c_e` says whether
 *    the node has a Vulkan device with the encode queue; if it is false the
 *    codec fields mean nothing and `perche` explains.  ⚠ A node without
 *    Vulkan does NOT mean «no card»: on Intel today the answer is «no» and
 *    the route is VA-API.
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	bool codifica;                       /* the card can encode this profile */
	uint32_t misura_massima_l, misura_massima_a;
	uint32_t misura_minima_l, misura_minima_a;
	unsigned modi_bitrate;               /* VULKANVIDEO_RC_* mask */
	int qp_minimo, qp_massimo;
	int livello_massimo_idc;             /* level_idc (H.264) / general_level_idc (HEVC) */
	uint32_t slot_dpb, riferimenti_attivi;
	uint32_t livelli_qualita;
	uint32_t granularita_l, granularita_a; /* the alignment the card wants on input */
	bool intestazioni_dal_driver;        /* `vkGetEncodedVideoSessionParametersKHR` is there */
	char formato_ingresso[48];           /* the VkFormat chosen for the input planes */
	bool ingresso_scrivibile_dallo_shader; /* STORAGE on the input format: direct conversion */
	uint32_t sintassi;                   /* `stdSyntaxFlags`: which header fields the driver honours */
	bool cabac, transform_8x8;           /* H.264: read from `sintassi` */
} VulkanVideoProfiloCapacita;

typedef struct {
	bool vulkan_c_e;                     /* device + encode queue found */
	char perche[256];                    /* if not, why */
	char nome_scheda[256];               /* `deviceName` */
	char driver[256];                    /* `driverName` + `driverInfo` */
	uint32_t versione_api;               /* the device's VK_API_VERSION */
	bool dmabuf;                         /* the two zero-copy extensions are there */
	VulkanVideoProfiloCapacita h264;     /* High, 8 bits */
	VulkanVideoProfiloCapacita hevc;     /* Main, 8 bits */
	VulkanVideoProfiloCapacita hevc10;   /* Main 10 */
} VulkanVideoCapacita;

/* Opens and closes everything by itself: needed before deciding the route,
 * and by the installer.  Returns false only if the node does not open at all. */
bool vulkanvideo_capacita(const char *nodo, VulkanVideoCapacita *c, char *errore,
                          size_t errore_byte);

/* ═══════════════════════════════════════════════════════════════════════════
 * 2. THE DEVICE — instance, physical device chosen BY THE DRM NODE
 *    (`VK_EXT_physical_device_drm`: not «the first card around»), logical
 *    device with one encode queue and one compute queue.
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct VulkanVideoDispositivo VulkanVideoDispositivo;

VulkanVideoDispositivo *vulkanvideo_apri_dispositivo(const char *nodo, char *errore,
                                                     size_t errore_byte);
void vulkanvideo_chiudi_dispositivo(VulkanVideoDispositivo *d);

/* The (non-linear) modifiers that the node's card can import and sample
 * for `formato_drm`, up to `quanti`; returns how many it wrote (0 = none, or
 * no Vulkan).  Opens and closes the device by itself. */
int vulkanvideo_modificatori(const char *nodo, uint32_t formato_drm, uint64_t *fuori, int quanti);
/* ⭐ 6 Oct 2026: does the node's card refuse a LINEAR slab that is drawn on
 * (`gbm_bo_create` LINEAR|RENDERING)?  `[M]` The NVIDIA (driver 595) does,
 * Intel and Radeon do not.  ⚠ false also if the node does not open: the
 * caller stays on the usual linear. */
bool vulkanvideo_scheda_rifiuta_il_lineare(const char *nodo);
const char *vulkanvideo_nome_scheda(const VulkanVideoDispositivo *d);
const char *vulkanvideo_nome_driver(const VulkanVideoDispositivo *d);

/* ═══════════════════════════════════════════════════════════════════════════
 * 3. THE ENCODER
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	VulkanVideoCodec codec;
	int profondita;                /* 8 or 10 (10 HEVC only) */
	uint32_t larghezza, altezza;   /* the CANVAS: what the stream shows */
	uint32_t fotogrammi_al_secondo;
	int qp;                        /* 1..51: the fixed QP (CQP) or the quality floor (VBR) */
	/* The bandwidth ceiling (phase 9): all zeros = CQP.  Otherwise VBR with
	 * average = target, maximum = wire, buffer in bits — the same three
	 * numbers that `codificatore.c` computes.  ⚠ Vulkan does not have VA-API's
	 * QVBR: the requested QP becomes the regulator's MINIMUM QP (no more is
	 * spent than the requested quality would cost), and the regulator raises
	 * the QP only when the ceiling bites.  It is declared in the
	 * `VulkanVideoDichiarazione`. */
	int64_t banda_punto, banda_filo;
	int serbatoio_bit;
	/* 0 = the level is COMPUTED as ffmpeg did; >0 = imposed
	 * (`level_idc` for H.264, `general_level_idc` for HEVC). */
	int livello_idc;
	uint32_t chiavi_ogni;          /* 0 = keyframes on request only */
} VulkanVideoRichiesta;

/* ⭐ What was read from the driver and decided at opening: the confession. */
typedef struct {
	uint32_t larghezza_codificata, altezza_codificata; /* aligned to the block */
	uint32_t blocco;                   /* 16 (H.264) or the HEVC CTB */
	int livello_idc;                   /* the one written in the SPS */
	unsigned modo_rc;                  /* VULKANVIDEO_RC_CQP / _VBR */
	bool intestazioni_dal_driver;      /* SPS/PPS taken from the driver (otherwise written by us) */
	bool driver_ha_cambiato_parametri; /* `hasOverrides` on the parameter sets */
	bool livello_corretto_nei_byte;    /* HEVC: the driver had written the level in the wrong alphabet */
	bool conversione_diretta;          /* the shader writes INTO the input planes (STORAGE) */
	bool ritardo_minimo_chiesto;       /* VK_VIDEO_ENCODE_TUNING_MODE_ULTRA_LOW_LATENCY */
	uint32_t famiglia_codifica, famiglia_calcolo;
	char formato_ingresso[48];
	int qp_minimo, qp_massimo;         /* declared by the card */
	size_t intestazioni_byte;          /* how many bytes of SPS/PPS(/VPS) in front of every keyframe */
} VulkanVideoDichiarazione;

typedef struct VulkanVideo VulkanVideo;

VulkanVideo *vulkanvideo_apri(VulkanVideoDispositivo *d, const VulkanVideoRichiesta *r,
                              char *errore, size_t errore_byte);
void vulkanvideo_chiudi(VulkanVideo *v);
const VulkanVideoDichiarazione *vulkanvideo_dichiarazione(const VulkanVideo *v);

/* The times of a frame, in microseconds, split the way
 * `CodificatoreFotogramma` keeps them: zero in `caricamento` on zero copy
 * means «this stretch is not there», not «it is free». */
typedef struct {
	uint64_t us_caricamento;  /* system memory → card (from memory only) */
	uint64_t us_conversione;  /* the RGB → NV12 shader on the card (and the GPU copy of the uploaded pixels) */
	uint64_t us_codifica;     /* from handing to the encoder to the bytes read */
} VulkanVideoTempi;

/* The byte order of the input pixels. */
typedef enum { VULKANVIDEO_BGRX, VULKANVIDEO_RGBX } VulkanVideoOrdine;

/*
 * Encodes a frame FROM MEMORY: `pixel` is BGRx/RGBx, 4 bytes per
 * pixel, `passo` in bytes.  Keyframe (IDR) if `chiave`.  ⛔ The returned
 * bytes belong to `v` until the next call.  ⚠ It WAITS for the card to
 * finish.
 */
bool vulkanvideo_codifica_memoria(VulkanVideo *v, const uint8_t *pixel, uint32_t passo,
                                  VulkanVideoOrdine ordine, bool chiave,
                                  const uint8_t **dati, size_t *byte, VulkanVideoTempi *t,
                                  char *errore, size_t errore_byte);

/* The same DMA-BUF that `codificatore.h` describes (`CodificatoreSuperficie`):
 * the descriptor stays the producer's and is not closed; `generazione` drops
 * the import cache when the producer's buffers change. */
typedef struct {
	int fd;
	uint32_t offset;
	uint32_t stride;
	uint32_t larghezza, altezza;
	uint32_t formato_drm;          /* DRM_FORMAT_XRGB8888 / XBGR8888 (and the alpha variants) */
	uint64_t modificatore;
	uint64_t generazione;
} VulkanVideoSuperficie;

/* Encodes a frame that is ALREADY on the card: zero copy.  ⛔ The
 * descriptor must stay valid for the whole call; when it returns, the
 * card has FINISHED reading it. */
bool vulkanvideo_codifica_dmabuf(VulkanVideo *v, const VulkanVideoSuperficie *s, bool chiave,
                                 const uint8_t **dati, size_t *byte, VulkanVideoTempi *t,
                                 char *errore, size_t errore_byte);

/* The LIVE quality change: in CQP it is the QP of the next frame; in VBR it
 * is the regulator's floor, and the regulator is reprogrammed.  ⚠ It does
 * not make a keyframe by itself: the caller asks for one if it wants it. */
bool vulkanvideo_qualita(VulkanVideo *v, int qp, char *errore, size_t errore_byte);

/* The canvas change: it closes and reopens at the new size, and the first
 * frame afterwards is a keyframe (`codificatore.h`, `codificatore_ridimensiona`). */
bool vulkanvideo_ridimensiona(VulkanVideo *v, uint32_t larghezza, uint32_t altezza,
                              char *errore, size_t errore_byte);

#endif
