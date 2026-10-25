/*
 * test.c — the frequency ceiling of the input channel NEVER leaves a key or a button pressed (audit of 25 Oct 2026, commit "token bucket
 * per client and per kind of message"; asked by the coordinator).
 *
 * The danger: a message over the rate is dropped; if the dropped one is the RELEASE of a key or button whose press went through, the
 * compositor keeps it down until the detach (RCP.md §11: «a Ctrl left down makes the desktop unusable»).  The rule in rcp.c
 * (input_admit): the release of a press that was admitted is never dropped; a press that is dropped leaves no mark, and its release is
 * an ordinary message for the bucket (a release of a key that is not down is harmless).
 *
 * The REAL rcp.c is #included (src/ or the twin, chosen by -I) and the REAL handle_input() is called with hand-made bodies; the hooks
 * keep a model of the compositor (which key codes and button codes are down).
 *
 * What is checked:
 *   1. a flood of presses of 40 keys, 20000 messages in one millisecond, then every release: over the rate many presses are dropped and
 *      the model ends EMPTY (nothing stuck), for keys (T_KEY_POSITION) and for buttons (T_BUTTON);
 *   2. the same with the releases ALSO sent in the middle of the flood, and with repeated presses (auto-repeat) of a key whose first press went
 *      through and the repeats were dropped: the release still clears it;
 *   3. 200 random sequences (seeded) of presses and releases of 12 codes at random times, with bursts far over the rate, for both kinds:
 *      after the client has sent the release of everything it pressed, the model is empty. (A press that was never admitted may have
 *      its release dropped: the model must not need it.);
 *   4. a flood of RELEASES of keys that were never pressed is limited by the bucket (not a free door): at most burst + rate*time pass;
 *   5. the release of an admitted press passes even when the bucket is empty, and costs the bucket nothing;
 *   6. release_on_detach() empties the marks (a new attach starts clean), and a codes above 0x2FF has no mark and is limited by the bucket;
 *   7. a person (a key every 20 ms, down and up, 2 minutes) is never refused: every press and every release reaches the model.
 *
 * BUILD AND RUN (a few seconds; from the root of the tree):
 *   for T in src benches/rcp; do F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Wno-unused-parameter -I$T -Ibenches/fuzz/rcp-msg" &&
 *      gcc $F -c benches/unit/input-no-stuck/test.c -o /tmp/ns-t.o && gcc $F -c benches/fuzz/rcp-msg/stubs_log.c -o /tmp/ns-l.o &&
 *      gcc -fsanitize=address,undefined /tmp/ns-t.o /tmp/ns-l.o -o /tmp/ns-test && /tmp/ns-test || exit 1; done
 * Exit code 0 = every check passed.
 */
#include "rcp.c"

#include <stdio.h>

static int checks, bad;
#define CHECK(cond, what) do { checks++; if (!(cond)) { bad++; printf("  FAIL %s:%d  %s\n", __FILE__, __LINE__, what); } } while (0)

/* the compositor, as a model */
static uint8_t key_down[0x10000 / 8], btn_down[0x10000 / 8];
static unsigned keys_down_n, btns_down_n, reached_press, reached_release;

static void model_set(uint8_t *bits, unsigned *n, uint16_t code, int pressed)
{
	int was = (bits[code >> 3] >> (code & 7)) & 1;

	if (pressed && !was) {
		bits[code >> 3] |= (uint8_t)(1u << (code & 7));
		(*n)++;
	} else if (!pressed && was) {
		bits[code >> 3] &= (uint8_t)~(1u << (code & 7));
		(*n)--;
	}
	if (pressed)
		reached_press++;
	else
		reached_release++;
}
static int h_pointer(void *c, uint32_t x, uint32_t y) { (void)c; (void)x; (void)y; return 0; }
static int h_button(void *c, uint16_t code, int pressed) { (void)c; model_set(btn_down, &btns_down_n, code, pressed); return 0; }
static int h_wheel(void *c, int32_t x, int32_t y) { (void)c; (void)x; (void)y; return 0; }
static int h_letter(void *c, uint32_t ch) { (void)c; (void)ch; return 0; }
static int h_position(void *c, uint16_t code, int pressed) { (void)c; model_set(key_down, &keys_down_n, code, pressed); return 0; }
static int h_release_all(void *c)
{
	int n = (int)(keys_down_n + btns_down_n);

	(void)c;
	memset(key_down, 0, sizeof key_down);
	memset(btn_down, 0, sizeof btn_down);
	keys_down_n = btns_down_n = 0;
	return n;
}
static void h_send(void *c, const uint8_t *d, size_t n) { (void)c; (void)d; (void)n; }
static void h_close(void *c, uint8_t r) { (void)c; (void)r; }
static void h_record(void *c, const char *l) { (void)c; (void)l; }

static rcp_session *fresh(void)
{
	rcp_hooks g;
	rcp_session *s;

	memset(&g, 0, sizeof g);
	g.send_msg = h_send;
	g.close = h_close;
	g.record = h_record;
	g.input_pointer = h_pointer;
	g.input_button = h_button;
	g.input_wheel = h_wheel;
	g.input_letter = h_letter;
	g.input_position = h_position;
	g.input_release_all = h_release_all;
	s = rcp_open(&g, "192.0.2.7", 1000);
	memset(key_down, 0, sizeof key_down);
	memset(btn_down, 0, sizeof btn_down);
	keys_down_n = btns_down_n = reached_press = reached_release = 0;
	return s;
}

static uint32_t next_id;

/* One BUTTON / KEY_POSITION message, big-endian like the wire: id u32, instant u64, code u16, pressed u8. */
static void send_key(rcp_session *s, uint16_t kind, uint16_t code, int pressed, uint64_t now)
{
	uint8_t b[15];
	uint32_t id = ++next_id;

	b[0] = (uint8_t)(id >> 24); b[1] = (uint8_t)(id >> 16); b[2] = (uint8_t)(id >> 8); b[3] = (uint8_t)id;
	memset(b + 4, 0, 8);
	b[12] = (uint8_t)(code >> 8);
	b[13] = (uint8_t)code;
	b[14] = (uint8_t)pressed;
	(void)handle_input(s, kind, b, sizeof b, now);
}

static uint32_t rng_state = 12345;
static uint32_t rnd(void) { rng_state = rng_state * 1664525u + 1013904223u; return rng_state >> 8; }

int main(void)
{
	const uint16_t kinds[2] = {T_KEY_POSITION, T_BUTTON};

	for (int k = 0; k < 2; k++) {
		uint16_t kind = kinds[k];
		unsigned *down_n = k == 0 ? &keys_down_n : &btns_down_n;
		rcp_session *s;
		uint64_t t = 100000;

		/* 1 */
		s = fresh();
		next_id = 0;
		for (int i = 0; i < 20000; i++)
			send_key(s, kind, (uint16_t)(0x10 + i % 40), 1, t);
		CHECK(*down_n > 0 && *down_n <= 40, "1: some presses went through");
		CHECK(reached_press < 20000, "1: and many were dropped (the flood is over the rate)");
		for (int c = 0; c < 40; c++)
			send_key(s, kind, (uint16_t)(0x10 + c), 0, t);
		CHECK(*down_n == 0, "1: after every release the model is EMPTY: nothing stuck");
		free(s);

		/* 2: releases in the middle, repeats of one key */
		s = fresh();
		send_key(s, kind, 0x1d, 1, t); /* Ctrl down: admitted (bucket full) */
		CHECK(*down_n == 1, "2: the first press goes through");
		for (int i = 0; i < 20000; i++)
			send_key(s, kind, 0x1d, 1, t); /* auto-repeat: most are dropped, the first press stays marked */
		for (int i = 0; i < 20000; i++)
			send_key(s, kind, (uint16_t)(0x20 + i % 30), (i & 1) ? 0 : 1, t); /* a storm of other presses and releases */
		send_key(s, kind, 0x1d, 0, t);
		CHECK(!((k == 0 ? key_down : btn_down)[0x1d >> 3] & (1u << (0x1d & 7))), "2: the release of the key whose first press went through ALWAYS arrives");
		for (int c = 0; c < 30; c++)
			send_key(s, kind, (uint16_t)(0x20 + c), 0, t);
		CHECK(*down_n == 0, "2: and nothing else is left down");
		free(s);

		/* 3: random sequences */
		unsigned dropped_in_random = 0;
		for (int seq = 0; seq < 100; seq++) {
			int pressed_by_client[12] = {0};

			s = fresh();
			next_id = 0;
			t = 5000000u + (uint64_t)seq * 100000u;
			rng_state = 777u + (uint32_t)seq;
			for (int i = 0; i < 12000; i++) { /* more than the burst of 4000, so that many are dropped */
				int c = (int)(rnd() % 12);
				int p = (int)(rnd() & 1);

				if (rnd() % 3000 == 0)
					t += rnd() % 400; /* a pause now and then */
				send_key(s, kind, (uint16_t)(0x30 + c), p, t);
				pressed_by_client[c] = p ? 1 : pressed_by_client[c];
				if (!p)
					pressed_by_client[c] = 0;
			}
			dropped_in_random += 12000u - (reached_press + reached_release);
			for (int c = 0; c < 12; c++)
				send_key(s, kind, (uint16_t)(0x30 + c), 0, t); /* the client releases everything */
			if (*down_n != 0) {
				CHECK(0, "3: a random sequence left something pressed");
				free(s);
				break;
			}
			free(s);
		}
		CHECK(1, "3: 100 random sequences ended with nothing pressed");
		CHECK(dropped_in_random > 100, "3: and the bucket really dropped messages in them (the test is not trivial)");

		/* 4: a flood of releases of keys never pressed */
		s = fresh();
		next_id = 0;
		t = 9000000;
		for (int i = 0; i < 100000; i++)
			send_key(s, kind, (uint16_t)(0x40 + i % 50), 0, t);
		{
			unsigned per_s, burst;

			msg_class_rate(k == 0 ? MC_KEY_POSITION : MC_BUTTON, &per_s, &burst);
			CHECK(reached_release <= burst, "4: a flood of releases of nothing pressed is limited to the burst");
		}
		free(s);

		/* 5: a release of an admitted press passes with the bucket empty and costs it nothing */
		s = fresh();
		next_id = 0;
		t = 9500000;
		send_key(s, kind, 0x1e, 1, t); /* admitted and marked */
		for (int i = 0; i < 5000; i++)
			send_key(s, kind, 0x50, 1, t); /* empties the bucket */
		{
			unsigned before = s->gate[k == 0 ? MC_KEY_POSITION : MC_BUTTON].dropped;

			send_key(s, kind, 0x1e, 0, t);
			CHECK(!((k == 0 ? key_down : btn_down)[0x1e >> 3] & (1u << (0x1e & 7))), "5: the release passes with an empty bucket");
			CHECK(s->gate[k == 0 ? MC_KEY_POSITION : MC_BUTTON].dropped == before, "5: and it was not counted as a drop");
		}
		free(s);

		/* 6: detach clears the marks; a code above 0x2FF has no mark */
		s = fresh();
		next_id = 0;
		t = 9700000;
		send_key(s, kind, 0x21, 1, t);
		release_on_detach(s, "test");
		{
			int any = 0;

			for (size_t i = 0; i < sizeof s->inp_down_key; i++)
				any |= s->inp_down_key[i] | s->inp_down_btn[i];
			CHECK(any == 0, "6: release_on_detach empties the marks");
		}
		for (int i = 0; i < 5000; i++)
			send_key(s, kind, 0x400, 0, t);
		CHECK(reached_release < 5000, "6: a code above 0x2FF has no mark and is limited like any message");
		free(s);

		/* 7: a person */
		s = fresh();
		next_id = 0;
		for (t = 20000000; t < 20000000 + 120000; t += 20) {
			send_key(s, kind, (uint16_t)(0x10 + (t / 20) % 26), 1, t);
			send_key(s, kind, (uint16_t)(0x10 + (t / 20) % 26), 0, t + 10);
		}
		CHECK(reached_press == 6000 && reached_release == 6000, "7: every press and every release of a person reaches the model");
		CHECK(*down_n == 0, "7: and nothing is left down");
		free(s);
	}
	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
