/* dimcheck.h — the arithmetic on the sizes of a frame, in 64 bits (audit of 25 Oct 2026, part E, E-R6 and E-R3).
 *
 * ⛔ Why: `width * 4u`, `stride * height`, `offset + stride * height` were computed in `uint32_t`: a producer announcing a
 *    width of 2^30 made `width * 4u` wrap to 0 and a stride check pass; a `stride * height` over 2^32 made the size the DMA-BUF
 *    import declares to the driver SMALLER than the real one.  The driver and the kernel check the object, so the realistic outcome
 *    is an error or a crash of the user's own child, not a read beyond — but the check must not depend on the driver.
 * Header only, no dependency: benches/unit/dim-check tests it alone and also reads the sources that must use it. */
#ifndef REMOTIX_DIMCHECK_H
#define REMOTIX_DIMCHECK_H

#include <stdbool.h>
#include <stdint.h>

/* Does a row of `width` pixels of 4 bytes fit in `stride`?  False for a zero width. */
static inline bool dim_stride_ok(uint32_t stride, uint32_t width)
{
	return width != 0 && (uint64_t)stride >= (uint64_t)width * 4u;
}

/* `offset + stride * height` as the 32-bit size the VA DMA-BUF import takes: false (and *size untouched) when it does not fit in
 * 32 bits or when a dimension is zero. */
static inline bool dim_object_size(uint32_t offset, uint32_t stride, uint32_t height, uint32_t *size)
{
	uint64_t s = (uint64_t)offset + (uint64_t)stride * height;

	if (stride == 0 || height == 0 || s > UINT32_MAX)
		return false;
	*size = (uint32_t)s;
	return true;
}

/* A frame is consistent with what it declares: non-zero sizes, `stride >= width * 4`, `byte >= stride * height`, and — E-R3 — no
 * larger than the canvas maximum (`max_w` x `max_h`; 0 = no maximum).  The sizes of a frame that comes from a wlroots compositor are
 * the compositor's, not the RCP request's, so nothing else bounds them. */
static inline bool dim_frame_ok(uint32_t width, uint32_t height, uint32_t stride, uint64_t byte, uint32_t max_w, uint32_t max_h)
{
	if (!width || !height || !stride || !dim_stride_ok(stride, width))
		return false;
	if ((max_w && width > max_w) || (max_h && height > max_h))
		return false;
	return byte >= (uint64_t)stride * height;
}

#endif
