/* test.c — S-R4 for the KEYS (libei path of src/input.c).  The REAL input.c is #included; the libei calls the key path reaches are interposed (they record what
 * would have gone to the compositor); the keymap is the REAL keyboard.c with layout «us».  Linked without libei/libwayland: the other undefined symbols get trap stubs.
 *   1. a key-down repeated: sent once (the second returns 0 and nothing leaves); the up repeated: the same;
 *   2. the bit of an ORPHAN key does not suppress a press (the new device never saw it);
 *   3. input_letter('A') with the user's Shift already DOWN: the letter is pressed and released, Shift is NOT pressed again and NOT released (the old code released it);
 *   4. input_letter('A') with nothing held: Shift down, a down, a up, Shift up — in this order, all released;
 *   5. input_letter('a') right after: nothing is left down (in->keys all clear for the gesture's keys);
 *   6. the skip log carries no code and no time (source reading of the message).
 * Build: see the header of benches/unit/child-flood/test.c for the flags and the trap stubs; run from the root of the tree. */
#include "input.c"

#include <stdio.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

static int events[64][2], n_events;
void ei_device_keyboard_key(struct ei_device *d, uint32_t key, bool is_press);
void ei_device_keyboard_key(struct ei_device *d, uint32_t key, bool is_press)
{
	(void)d;
	if (n_events < 64) { events[n_events][0] = (int)key; events[n_events][1] = is_press; n_events++; }
}
void ei_device_frame(struct ei_device *d, uint64_t t);
void ei_device_frame(struct ei_device *d, uint64_t t) { (void)d; (void)t; }

uint64_t ei_now(struct ei *ei);
uint64_t ei_now(struct ei *ei) { (void)ei; return 1; }

#define LSHIFT 42
#define KEY_A 30

static int has(const char *file, const char *needle)
{
	FILE *f = fopen(file, "r");
	static char src[8u << 20];
	size_t n;

	if (!f) return 0;
	n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
	return strstr(src, needle) != NULL;
}

int main(void)
{
	Input *in = calloc(1, sizeof *in);
	char *err = NULL;

	in->fd_socket = -1;
	in->keyboard_dev = (struct ei_device *)(uintptr_t)0x10;
	in->keyboard_active = TRUE;
	in->kb_layout = keyboard_open("us", &err);
	if (!in->kb_layout) { printf("no keymap: %s\n", err ? err : "?"); return 2; }

	n_events = 0;
	CHECK(send_key(in, KEY_A, 1) == 0 && send_key(in, KEY_A, 1) == 0 && n_events == 1, "1. a repeated key-down is sent once");
	CHECK(send_key(in, KEY_A, 0) == 0 && send_key(in, KEY_A, 0) == 0 && n_events == 2 && events[1][1] == 0, "1b. a repeated key-up too");

	n_events = 0;
	bit_write(in->keys, KEY_A, TRUE);
	bit_write(in->orphan_keys, KEY_A, TRUE);
	send_key(in, KEY_A, 1);
	CHECK(n_events == 1, "2. an orphan's bit does not suppress the press");
	bit_write(in->keys, KEY_A, FALSE);
	bit_write(in->orphan_keys, KEY_A, FALSE);

	/* 3: the user holds Shift */
	n_events = 0;
	send_key(in, LSHIFT, 1);
	n_events = 0;
	CHECK(input_letter(in, 'A') == 0, "3. input_letter('A') with Shift held works");
	{
		int shift_events = 0, a_down = 0, a_up = 0;
		for (int i = 0; i < n_events; i++) {
			if (events[i][0] == LSHIFT) shift_events++;
			if (events[i][0] == KEY_A && events[i][1]) a_down++;
			if (events[i][0] == KEY_A && !events[i][1]) a_up++;
		}
		CHECK(a_down == 1 && a_up == 1 && shift_events == 0, "3b. the letter goes down and up, Shift is neither pressed again nor RELEASED");
		CHECK(bit_read(in->keys, LSHIFT), "3c. the user's Shift is still down");
	}
	send_key(in, LSHIFT, 0);

	/* 4 */
	n_events = 0;
	CHECK(input_letter(in, 'A') == 0, "4. input_letter('A') with nothing held works");
	CHECK(n_events == 4 && events[0][0] == LSHIFT && events[0][1] == 1 && events[1][0] == KEY_A && events[1][1] == 1 &&
	      events[2][0] == KEY_A && events[2][1] == 0 && events[3][0] == LSHIFT && events[3][1] == 0, "4b. Shift down, a down, a up, Shift up");
	CHECK(!bit_read(in->keys, LSHIFT) && !bit_read(in->keys, KEY_A), "5. nothing left down");

	CHECK(has("src/input.c", "a repeated key state was not sent again (%u so far)") && !has("src/input.c", "a repeated key state was not sent again (code"), "6. the skip log is a bare counter");
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
