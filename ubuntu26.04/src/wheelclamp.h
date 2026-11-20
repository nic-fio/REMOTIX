/* wheelclamp.h — the wheel amounts of the input channel (audit of the session, S-R9, 25 Oct 2026).
 *
 * The client sends two i32 (RCP.md §7.3, 120 = one notch).  Nothing bounded them: INT32_MIN made `-axis_y` an undefined overflow in input.c, and a huge value
 * asked the compositor for millions of notches in one message.  A real wheel gives a few notches per message even when spun hard: WHEEL_MAX_UNITS is 100 notches.
 * The value is brought into [-WHEEL_MAX_UNITS, +WHEEL_MAX_UNITS] BEFORE any negation, so `-x` can never overflow. Header-only, tested by benches/unit/wheel-clamp. */
#ifndef WHEELCLAMP_H
#define WHEELCLAMP_H

#include <stdint.h>

#define WHEEL_MAX_UNITS 12000

static inline int32_t wheel_clamp(int32_t v)
{
	if (v > WHEEL_MAX_UNITS)
		return WHEEL_MAX_UNITS;
	if (v < -WHEEL_MAX_UNITS)
		return -WHEEL_MAX_UNITS;
	return v;
}

#endif
