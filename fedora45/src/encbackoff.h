/* encbackoff.h — how long to wait before making an encoder again after it DIED (audit of 25 Oct 2026, part E, E-R1, review).
 *
 * ⛔ The first version reused `enc_wait_ms`, but a successful creation resets that one: with a permanent cause (VRAM taken, a driver that
 *    always fails the reopening) the encoder opened fine, died at the first quality change, and was made again every 500 ms for the whole
 *    session.  The count of deaths is kept apart: it doubles the wait up to the maximum and goes back to zero ONLY after a frame was
 *    really sent.  Header only, no dependency. */
#ifndef REMOTIX_ENCBACKOFF_H
#define REMOTIX_ENCBACKOFF_H

#include <stdint.h>

/* The wait after the `deaths`-th consecutive death (1 = the first): min, 2·min, 4·min … never above max. */
static inline uint64_t enc_death_wait_ms(unsigned deaths, uint64_t min_ms, uint64_t max_ms)
{
	uint64_t w = min_ms;

	for (unsigned i = 1; i < deaths && w < max_ms; i++)
		w *= 2;
	return w > max_ms ? max_ms : w;
}

#endif
