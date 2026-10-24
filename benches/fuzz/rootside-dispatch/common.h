/*
 * common.h — what the REMOTIX fuzz harnesses share (DECISIONS §11.13).
 *
 * ⭐ THE OP STREAM.  The stateful harnesses (`fuzz_rcp.c`, `fuzz_wt.c`) do not read the
 *    fuzzer's bytes as ONE message: they read them as a little script of operations —
 *
 *        u8 op · u16 length (big-endian) · `length` bytes of argument
 *
 *    so that the fuzzer can split a message in two, make time pass between two
 *    messages, deliver the PAM verdict, open a second stream … that is, reach the states
 *    a real client reaches, and not only the first parser.  A truncated last op gets
 *    what is left: no input is «invalid» for the harness, only for the product.
 *
 * ⛔ The log of the product is NOT thrown away unread: every log call is formatted with
 *    `vsnprintf` into a buffer (`stubs_log.c`).  A `%s` fed with a bad pointer, a line
 *    built on a string that is not terminated — those are bugs too, and a stub that
 *    returned at once would hide them.
 */
#ifndef RXFUZZ_COMMON_H
#define RXFUZZ_COMMON_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
	const uint8_t *d;
	size_t n, i;
} rx_ops;

/* Next op: false when the input is over.  `arg`/`argn` point INSIDE the input. */
static inline int rx_next(rx_ops *o, uint8_t *op, const uint8_t **arg, size_t *argn)
{
	size_t want;
	if (o->i >= o->n)
		return 0;
	*op = o->d[o->i++];
	if (o->i + 2 <= o->n) {
		want = ((size_t)o->d[o->i] << 8) | o->d[o->i + 1];
		o->i += 2;
	} else {
		want = o->n - o->i;
		o->i = o->n;
	}
	if (want > o->n - o->i)
		want = o->n - o->i;
	*arg = o->d + o->i;
	*argn = want;
	o->i += want;
	return 1;
}

static inline uint32_t rx_u32(const uint8_t *a, size_t n)
{
	uint32_t v = 0;
	for (size_t k = 0; k < 4 && k < n; k++)
		v = (v << 8) | a[k];
	return v;
}

/* The harness's clock, in milliseconds: the product's `log_now_ms()` reads it too. */
extern uint64_t rx_now_ms;

#endif
