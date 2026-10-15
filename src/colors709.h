/*
 * colors709.h — from BGRx (or RGBx) to YUV 4:2:0 BT.709 in LIMITED range,
 *               without libswscale.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS — phase 18 (`phases/18-without-ffmpeg.md`, `DECISIONS.md` §10.25)
 *
 * Up to phase 17 the conversion was done by `sws_scale` (`prepare_frame()`
 * in `encoder.c`) with the matrix IMPOSED: `sws_setColorspaceDetails(
 * SWS_CS_ITU709)`, full-range source, limited output.  Removing ffmpeg also
 * removes libswscale, and the conversion has to be redone **identically**:
 * two different matrices at the two ends would measure the matrix, not the
 * image (the colour numbers are declared, not inherited: `COLOR_PRIMARIES`… in
 * `vadirect.c`, `vui264`/`vui265` in `vulkanvideo.c`, and the matrix IMPOSED
 * on the GPU conversion, `convert_on_gpu()` in `encoder.c`).
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
 *    `benches/18-software-confronto.c`:
 *
 *   - the matrix: Kr = 0.2126 · Kb = 0.0722 (BT.709), full-range RGB
 *     (0-255) → Y 16-235, Cb/Cr 16-240 (at 10 bits: 64-940, 64-960);
 *   - chroma halved in both directions, **average of the four pixels** of
 *     the 2x2 square taken in RGB and then converted — the same thing
 *     swscale does horizontally (`rgb32ToUV_half`) and almost the same
 *     vertically (see the box in `colors709.c`);
 *   - rounding to nearest, without dithering.
 *
 * ⚠ The dimensions must be EVEN (4:2:0): the guard is in `encoder.c`
 *   and is repeated here, because an odd width would read past the row.
 */
#ifndef REMOTIX_COLORS709_H
#define REMOTIX_COLORS709_H

#include <stdbool.h>
#include <stdint.h>

/* Which byte is red: BGRx (GNOME, KDE, …) or RGBx (labwc, phase 13). */
typedef enum {
	COLORI709_BGRX,
	COLORI709_RGBX,
} Colori709Ordine;

/* ⭐ 8 bits, three planes (I420 / `yuv420p`): for OpenH264 and for 8-bit SVT-AV1.
 *    Returns false only if the dimensions are not even or pointers are missing. */
bool colori709_a_i420(const uint8_t *pixel, uint32_t step, uint32_t width,
                      uint32_t height, Colori709Ordine order,
                      uint8_t *y, uint32_t stride_y,
                      uint8_t *u, uint32_t stride_u,
                      uint8_t *v, uint32_t stride_v);

/* ⭐ 10 bits, three 16-bit planes (`yuv420p10le`): for 10-bit SVT-AV1.  ⚠ These
 *    are 8 bits PROMOTED with the matrix computed at 10 bits, not 8 bits shifted
 *    by two: it is what swscale did towards `yuv420p10le`.  Strides are in
 *    BYTES, like libavutil's. */
bool colori709_a_i420_10(const uint8_t *pixel, uint32_t step, uint32_t width,
                         uint32_t height, Colori709Ordine order,
                         uint16_t *y, uint32_t stride_y,
                         uint16_t *u, uint32_t stride_u,
                         uint16_t *v, uint32_t stride_v);

/* ⭐ 8-bit semi-planar (NV12): for the card route when zero copy is not
 *    available and the frame comes up from memory (`c->staging` in
 *    `encoder.c`), which today goes through swscale towards NV12. */
bool colors709_to_nv12(const uint8_t *pixel, uint32_t step, uint32_t width,
                      uint32_t height, Colori709Ordine order,
                      uint8_t *y, uint32_t stride_y,
                      uint8_t *uv, uint32_t stride_uv);

/* ⭐ 10-bit semi-planar (P010: the ten bits in the HIGH bits of sixteen). */
bool colors709_to_p010(const uint8_t *pixel, uint32_t step, uint32_t width,
                      uint32_t height, Colori709Ordine order,
                      uint16_t *y, uint32_t stride_y,
                      uint16_t *uv, uint32_t stride_uv);

/*
 * ⭐ THE PADDING OF THE CARD'S SURFACE (15 Oct 2026, the question of 4b194bbc).
 *
 * The card encodes a picture ALIGNED to its block (1920x1080 → 1920x1088 in
 * H.264) and the SPS crops the extra rows and columns away.  ⛔ They are
 * cropped from the SHOWN picture, not from the coding: the encoder predicts,
 * transforms and deblocks them together with the visible ones, so what they
 * hold reaches the last visible row (deblocking across the 8x8 edge at row
 * 1080, the motion search near the edge) and costs bits (a step from the
 * picture to zero is an edge to code on every key).  ⇒ They are filled the
 * way the Vulkan route's shader already did (`vulkanvideo_rgb_nv12.comp`,
 * the `clamp()`): COPIES OF THE EDGE, the last sample of every row to the
 * right, the last row (padded) downwards.
 *
 * Copies ONE plane of `rows` rows of `row_bytes` into a destination of
 * `dst_rows` rows of `dst_row_bytes`, replicating the last `unit` bytes of
 * each row to the right and the last row downwards.  `unit` is what one
 * column is made of: NV12 Y 1, NV12 UV 2 (the U,V pair), P010 Y 2, P010 UV 4.
 * ⚠ The source rows are re-read for the padding, never the destination: the
 *   destination is the card's mapping (write-combined), slow to read.
 * Returns false (and writes nothing) on a geometry that does not hold.
 */
bool colors709_copy_padded(uint8_t *dst, uint32_t dst_stride, uint32_t dst_row_bytes,
                           uint32_t dst_rows, const uint8_t *src, uint32_t src_stride,
                           uint32_t row_bytes, uint32_t rows, uint32_t unit);

#endif
