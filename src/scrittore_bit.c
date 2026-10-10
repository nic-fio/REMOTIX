/*
 * scrittore_bit.c — see `scrittore_bit.h`.  No codec in here: only bits,
 * Exp-Golomb and the emulation prevention byte rule.
 */
#include "scrittore_bit.h"

#include <string.h>

void sb_open(WriterBit *s, uint8_t *data_v, size_t capabilities)
{
	s->data_v = data_v;
	s->capabilities = capabilities;
	s->bit = 0;
	s->overflowed = false;
	if (data_v && capabilities)
		memset(data_v, 0, capabilities);
}

static void sb_bit(WriterBit *s, unsigned v)
{
	size_t idx = s->bit >> 3;

	if (idx >= s->capabilities) {
		s->overflowed = true;
		return;
	}
	if (v)
		s->data_v[idx] |= (uint8_t) (0x80u >> (s->bit & 7));
	s->bit++;
}

void sb_u(WriterBit *s, int n, uint32_t v)
{
	for (int i = n - 1; i >= 0; i--)
		sb_bit(s, (v >> i) & 1u);
}

void sb_flag(WriterBit *s, bool v)
{
	sb_bit(s, v ? 1u : 0u);
}

void sb_ue(WriterBit *s, uint32_t v)
{
	/* codeNum v → (v+1) written with 2·len+1 bits, where len = floor(log2(v+1)):
	 * `len` zeros, then the len+1 bits of (v+1).  ⚠ `v+1` can overflow 32 bits
	 * only for v = 2^32-1, which none of our fields reaches. */
	uint64_t x = (uint64_t) v + 1u;
	int length = 0;

	while ((x >> (length + 1)) != 0)
		length++;
	for (int i = 0; i < length; i++)
		sb_bit(s, 0);
	for (int i = length; i >= 0; i--)
		sb_bit(s, (unsigned) ((x >> i) & 1u));
}

void sb_se(WriterBit *s, int32_t v)
{
	/* H.264 9.1.1, table 9-3: v > 0 → k = 2v-1 · v <= 0 → k = -2v. */
	if (v > 0)
		sb_ue(s, 2u * (uint32_t) v - 1u);
	else
		sb_ue(s, 2u * (uint32_t) (-(int64_t) v));
}

void sb_close_rbsp(WriterBit *s)
{
	sb_bit(s, 1);
	while (s->bit & 7)
		sb_bit(s, 0);
}

void sb_align_with_uni(WriterBit *s)
{
	while (s->bit & 7)
		sb_bit(s, 1);
}

void sb_copy_bit(WriterBit *s, const uint8_t *source, size_t da, size_t how_many)
{
	for (size_t i = 0; i < how_many; i++) {
		size_t b = da + i;
		sb_bit(s, (source[b >> 3] >> (7 - (b & 7))) & 1u);
	}
}

size_t sb_byte(const WriterBit *s)
{
	return (s->bit + 7) >> 3;
}

bool sb_aligned(const WriterBit *s)
{
	return (s->bit & 7) == 0;
}

size_t nal_annexb(uint8_t *outside, size_t capabilities, const uint8_t *header,
                  size_t header_byte, const uint8_t *rbsp, size_t rbsp_byte)
{
	size_t n = 0, zeros = 0;

	if (capabilities < 4 + header_byte)
		return 0;
	outside[n++] = 0;
	outside[n++] = 0;
	outside[n++] = 0;
	outside[n++] = 1;
	memcpy(outside + n, header, header_byte);
	n += header_byte;
	/*
	 * H.264 7.4.1 / H.265 7.4.2: inside the payload the sequence `00 00 0x` with
	 * x in {0,1,2,3} must not appear — a `03` is slipped in.  ⛔ And the zero
	 * count restarts AFTER the emulation prevention byte, not after the byte
	 * that asked for it: `00 00 00 00` becomes `00 00 03 00 00`, and the third
	 * zero starts a new count.
	 */
	for (size_t i = 0; i < rbsp_byte; i++) {
		if (zeros >= 2 && rbsp[i] <= 3) {
			if (n >= capabilities)
				return 0;
			outside[n++] = 3;
			zeros = 0;
		}
		if (n >= capabilities)
			return 0;
		outside[n++] = rbsp[i];
		zeros = (rbsp[i] == 0) ? zeros + 1 : 0;
	}
	return n;
}
