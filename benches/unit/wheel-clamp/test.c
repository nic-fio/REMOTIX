/* test.c — wheelclamp.h (audit of the session, S-R9).  Build: cc -std=gnu11 -fsanitize=address,undefined -fno-sanitize-recover=undefined -I src benches/unit/wheel-clamp/test.c -o t && ./t */
#include "wheelclamp.h"
#include <stdio.h>
#include <limits.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

int main(void)
{
	CHECK(wheel_clamp(0) == 0 && wheel_clamp(120) == 120 && wheel_clamp(-120) == -120 && wheel_clamp(60) == 60, "1. normal values (a notch, half a notch) pass whole");
	CHECK(wheel_clamp(WHEEL_MAX_UNITS) == WHEEL_MAX_UNITS && wheel_clamp(-WHEEL_MAX_UNITS) == -WHEEL_MAX_UNITS, "2. the limits themselves pass");
	CHECK(wheel_clamp(WHEEL_MAX_UNITS + 1) == WHEEL_MAX_UNITS && wheel_clamp(-WHEEL_MAX_UNITS - 1) == -WHEEL_MAX_UNITS, "3. one over is brought back");
	CHECK(wheel_clamp(INT32_MAX) == WHEEL_MAX_UNITS && wheel_clamp(INT32_MIN) == -WHEEL_MAX_UNITS, "4. INT32_MAX / INT32_MIN are brought back");
	{
		int32_t v = wheel_clamp(INT32_MIN);
		int32_t n = -v;   /* the minus of input.c: with the sanitizer, an overflow would abort here */
		CHECK(n == WHEEL_MAX_UNITS, "5. the negation after the clamp cannot overflow");
	}
	for (int64_t x = INT32_MIN; x <= INT32_MAX; x += 65537) {
		int32_t v = wheel_clamp((int32_t)x);
		CHECK(v >= -WHEEL_MAX_UNITS && v <= WHEEL_MAX_UNITS, "6. every value ends in range");
		(void)-v;
	}
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
