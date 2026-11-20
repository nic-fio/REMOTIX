/*
 * bit_writer.h — writing bits, one field at a time, the way an H.264/H.265
 * parameter set wants them: `u(n)`, `ue(v)`, `se(v)`, the trailing bits, and
 * the NAL in Annex-B with the emulation prevention bytes in place.
 *
 * ⭐ PHASE 18 (30 Sep 2026, `DECISIONS.md` §10.25): born because the stream
 *    headers (SPS/PPS/VPS/slice header) are no longer written by
 *    `libavcodec` (`cbs_h264`/`cbs_h265`): REMOTIX writes them, and hands them
 *    to the driver as "packed headers".  It is the mirror of the READER that
 *    `encoder.c` has had since 12 August 2026 (`BitReader`): that one
 *    reads back the bytes produced for the confession, this one produces them.
 *
 * ⛔ What it is NOT: it knows no codec.  It knows bits, Exp-Golomb and the
 *    `00 00 03` rule.  Who decides WHICH fields to write, and in what order,
 *    is `vadirect.c`, with the standard next to every line.
 */
#ifndef REMOTIX_BIT_WRITER_H
#define REMOTIX_BIT_WRITER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
	uint8_t *data;
	size_t capabilities;   /* in bytes */
	size_t bit;        /* write position, in bits */
	/* ⛔ Three outcomes, not two: a field that does not fit is REMEMBERED, and
	 *    whoever closes the NAL sees it — a truncated header looks like a header. */
	bool overflowed;
} BitWriter;

void bw_open(BitWriter *s, uint8_t *data, size_t capabilities);

/* `u(n)`: the low `n` bits of `v`, highest first.  ⚠ `n` up to 32. */
void bw_u(BitWriter *s, int n, uint32_t v);
void bw_flag(BitWriter *s, bool v);
/* Unsigned Exp-Golomb (H.264 9.1 / H.265 9.2). */
void bw_ue(BitWriter *s, uint32_t v);
/* Signed Exp-Golomb: k → (-1)^(k+1) · ceil(k/2), that is the inverse of
 * `lb_se()` in `encoder.c`. */
void bw_se(BitWriter *s, int32_t v);

/* `rbsp_trailing_bits()`: a 1 and then zeros up to the byte.  ⚠ It is also
 * H.265's `byte_alignment()` (7.3.2.12): same form, another name. */
void bw_close_rbsp(BitWriter *s);
/* `cabac_alignment_one_bit`: ONES up to the byte — the tail of the H.264 slice
 * header when the entropy coding is CABAC (7.3.4).  ⛔ Not zeros: ones. */
void bw_align_with_uni(BitWriter *s);

/* Copies `amount` bits from `source` starting at bit `da`: used by the D-023
 * frame, which rewrites the head of an SPS and copies the tail back as it is. */
void bw_copy_bit(BitWriter *s, const uint8_t *source, size_t da, size_t amount);

/* How many bytes the written bits take (rounded up). */
size_t bw_byte(const BitWriter *s);
bool bw_aligned(const BitWriter *s);

/*
 * A NAL in Annex-B: `00 00 00 01`, the NAL header as it is, then the RBSP with
 * the emulation prevention bytes (`00 00 0x` with x <= 3 → `00 00 03 0x`).
 *
 * ⛔ The NAL header (1 byte in H.264, 2 in H.265) is passed SEPARATELY and gets
 *    NO emulation prevention: that is what `cbs_h2645` does too, and a reader
 *    that found a `03` inside the header would not know what to do with it.
 * Returns the bytes written, or 0 if `report` is too small.
 */
size_t nal_annexb(uint8_t *report, size_t capabilities, const uint8_t *header,
                  size_t header_byte, const uint8_t *rbsp, size_t rbsp_byte);

#endif
