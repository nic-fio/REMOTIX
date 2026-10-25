/* test.c — S-R4 (audit of the session): send_button() of src/input.c does not resend the state already known.  input.c needs libei and a compositor, so this is a
 * SOURCE-READING check of the integration point (the same method as the other unit tests that cannot link the real file): in the body of send_button(), after the
 * orphan-release branch and BEFORE ei_device_button_button(), there is a test that compares the requested state with in->buttons, and it excludes orphans.
 * Run from the root of the tree:  cc -std=gnu11 benches/unit/button-dedupe/test.c -o t && ./t src/input.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int bad;
#define CHECK(c, w) do { if (!(c)) { bad++; printf("FAIL: %s\n", w); } } while (0)

int main(int argc, char **argv)
{
	FILE *f = fopen(argc > 1 ? argv[1] : "src/input.c", "r");
	static char src[4u << 20];
	size_t n;
	char *fn, *end, *dedupe, *send, *orph;

	if (!f) { puts("cannot open"); return 2; }
	n = fread(src, 1, sizeof src - 1, f);
	src[n] = 0;
	fclose(f);
	fn = strstr(src, "static int send_button(Input *in, uint16_t code, int pressed)\n{");
	CHECK(fn != NULL, "1. send_button() is there");
	if (!fn) return 1;
	end = strstr(fn, "\n}\n");
	orph = strstr(fn, "if (!pressed && bit_read(in->orphan_buttons, code))");
	dedupe = strstr(fn, "if ((pressed != 0) == bit_read(in->buttons, code) && !bit_read(in->orphan_buttons, code))");
	send = strstr(fn, "ei_device_button_button(in->pointer, code, pressed != 0);");
	CHECK(dedupe && dedupe < end, "2. the duplicate test is inside send_button()");
	CHECK(dedupe && send && dedupe < send, "3. it comes BEFORE the event is sent to the compositor");
	CHECK(dedupe && orph && orph < dedupe, "4. it comes after the orphan-release branch (that one stays first)");
	CHECK(dedupe && strstr(dedupe, "return 0;") && strstr(dedupe, "return 0;") < send, "5. a duplicate returns 0 without sending");
	printf("%s\n", bad ? "FAILED" : "OK: all checks passed");
	return bad ? 1 : 0;
}
