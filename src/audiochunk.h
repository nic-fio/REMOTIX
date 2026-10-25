/* audiochunk.h — is a PipeWire chunk inside its buffer? (audit of the session, S-R8, 25 Oct 2026)
 *
 * sound.c read `data + chunk->offset` for `chunk->size` bytes trusting both: they come from the PipeWire of the session (same uid, no privilege boundary), but a wrong
 * pair read outside the buffer and sent the bytes to the user's own browser.  The chunk is valid only if offset + size fits in `maxsize` (computed in 64 bits, so the
 * sum cannot wrap) and the offset keeps the int16 samples aligned.  Header-only, tested by benches/unit/audio-chunk. */
#ifndef AUDIOCHUNK_H
#define AUDIOCHUNK_H

#include <stdbool.h>
#include <stdint.h>

static inline bool audio_chunk_ok(uint32_t offset, uint32_t size, uint32_t maxsize)
{
	return (offset & 1u) == 0 && (uint64_t)offset + (uint64_t)size <= (uint64_t)maxsize;
}


/* The chunk REDUCED to its buffer, as the SPA convention does (offset taken modulo maxsize, size cut to what is left; review of 7afe4777): a chunk that is a little off keeps its
 * valid part instead of being thrown away — in sound a dropped block is a gap that is heard.  The offset is brought down to even (int16 alignment).  false = nothing left
 * (maxsize 0, or no byte after the offset). */
static inline bool audio_chunk_fit(uint32_t *offset, uint32_t *size, uint32_t maxsize)
{
	uint32_t o, left;

	if (maxsize == 0)
		return false;
	o = (*offset % maxsize) & ~1u;
	left = maxsize - o;
	*offset = o;
	if (*size > left)
		*size = left;
	return *size > 0;
}

#endif
