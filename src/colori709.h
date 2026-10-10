/*
 * colori709.h — from BGRx (or RGBx) to YUV 4:2:0 BT.709 in LIMITED range,
 *               without libswscale.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS — phase 18 (`fasi/18-senza-ffmpeg.md`, `DECISIONI.md` §10.25)
 *
 * Up to phase 17 the conversion was done by `sws_scale` (`prepara_fotogramma()`
 * in `codificatore.c`) with the matrix IMPOSED: `sws_setColorspaceDetails(
 * SWS_CS_ITU709)`, full-range source, limited output.  Removing ffmpeg also
 * removes libswscale, and the conversion has to be redone **identically**:
 * two different matrices at the two ends would measure the matrix, not the
 * image (the colour numbers are declared, not inherited: `COLORE_PRIMARI`… in
 * `vadiretta.c`, `vui264`/`vui265` in `vulkanvideo.c`, and the matrix IMPOSED
 * on the GPU conversion, `converti_sulla_gpu()` in `codificatore.c`).
 *
 * ⛔⛔ AND IT IS NOT libyuv, and the reason is one line of its
 *      `convert_from_argb.h`
 *      `[M]` 30 Sep 2026, libyuv 0.0.1904 (Debian trixie): from ARGB to
 *      4:2:0 there are **only** `ARGBToI420` (**BT.601** limited) and
 *      `ARGBToJ420` (JPEG, BT.601 **full**).  Neither is ours: using one
 *      would mean changing the product's colours without an error anywhere.
 *      ⇒ Our own code, ~200 lines, and no extra dependency for the
 *      installer to find on seven distributions.
 *
 * ---------------------------------------------------------------------------
 * ⭐ THE RULES IT REPRODUCES, and each has its measurement in the bench
 *    `banchi/18-software-confronto.c`:
 *
 *   - the matrix: Kr = 0.2126 · Kb = 0.0722 (BT.709), full-range RGB
 *     (0-255) → Y 16-235, Cb/Cr 16-240 (at 10 bits: 64-940, 64-960);
 *   - chroma halved in both directions, **average of the four pixels** of
 *     the 2x2 square taken in RGB and then converted — the same thing
 *     swscale does horizontally (`rgb32ToUV_half`) and almost the same
 *     vertically (see the box in `colori709.c`);
 *   - rounding to nearest, without dithering.
 *
 * ⚠ The dimensions must be EVEN (4:2:0): the guard is in `codificatore.c`
 *   and is repeated here, because an odd width would read past the row.
 */
#ifndef REMOTIX_COLORI709_H
#define REMOTIX_COLORI709_H

#include <stdbool.h>
#include <stdint.h>

/* Which byte is red: BGRx (GNOME, KDE, …) or RGBx (labwc, phase 13). */
typedef enum {
	COLORI709_BGRX,
	COLORI709_RGBX,
} Colori709Ordine;

/* ⭐ 8 bits, three planes (I420 / `yuv420p`): for OpenH264 and for 8-bit SVT-AV1.
 *    Returns false only if the dimensions are not even or pointers are missing. */
bool colori709_a_i420(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint8_t *y, uint32_t passo_y,
                      uint8_t *u, uint32_t passo_u,
                      uint8_t *v, uint32_t passo_v);

/* ⭐ 10 bits, three 16-bit planes (`yuv420p10le`): for 10-bit SVT-AV1.  ⚠ These
 *    are 8 bits PROMOTED with the matrix computed at 10 bits, not 8 bits shifted
 *    by two: it is what swscale did towards `yuv420p10le`.  Strides are in
 *    BYTES, like libavutil's. */
bool colori709_a_i420_10(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                         uint32_t altezza, Colori709Ordine ordine,
                         uint16_t *y, uint32_t passo_y,
                         uint16_t *u, uint32_t passo_u,
                         uint16_t *v, uint32_t passo_v);

/* ⭐ 8-bit semi-planar (NV12): for the card route when zero copy is not
 *    available and the frame comes up from memory (`c->appoggio` in
 *    `codificatore.c`), which today goes through swscale towards NV12. */
bool colori709_a_nv12(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint8_t *y, uint32_t passo_y,
                      uint8_t *uv, uint32_t passo_uv);

/* ⭐ 10-bit semi-planar (P010: the ten bits in the HIGH bits of sixteen). */
bool colori709_a_p010(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint16_t *y, uint32_t passo_y,
                      uint16_t *uv, uint32_t passo_uv);

#endif
