/*
 * test.c — S-R7 (audit of the session, 25 Oct 2026): the per-session ceiling on clipboard ANNOUNCE / ASK of src/rcp.c, and the budget of the keyboard.c line
 * «a character is not producible».  (The ceilings on input and LAYOUT are tested with msgrate.h by the branch tetti-messaggi.)
 *
 * HOW: the REAL src/rcp.c is #included (never modified), like benches/unit/login-ban/test.c; the log is benches/fuzz/rcp-msg/stubs_log.c; the session is built by hand
 * (calloc) with a `record` hook that counts the lines.  handle_clipboard() is called directly with real wire bodies.
 *   1. 1000 CLIPBOARD_ASK in one instant: at most CLIPBOARD_BURST are handled (a handled one writes «no longer there», the session has no text);
 *   2. one summary line says how many were ignored, when the 10 s window closes;
 *   3. later the session is served again; 2 ASK a second for a minute lose nothing;
 *   4. 1000 ANNOUNCE in one instant: the same bucket, the first ones handled (transfer ids 1..), the rest ignored — the last id seen is not 1000;
 *   5. source reading of src/keyboard.c: the «not producible» line is behind a window budget (KB_NOLETTER_LINES per KB_NOLETTER_WINDOW_MS).
 *
 * BUILD AND RUN (from the root of the tree; see the header of benches/unit/login-ban/test.c for the podman form; on the tablet plain gcc/clang):
 *   cc -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -Wno-unused-parameter -I src -I benches/fuzz/rcp-msg \
 *      -c benches/unit/session-caps/test.c -o t.o && cc ... -c benches/fuzz/rcp-msg/stubs_log.c -o l.o && cc -fsanitize=address,undefined t.o l.o -o test && ./test
 */
#include "rcp.c"

#include <stdio.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static unsigned no_text, over_lines;
static void record(void *ctx, const char *line)
{
	(void)ctx;
	if (strstr(line, "no longer there"))
		no_text++;
	if (strstr(line, "ANNOUNCE/ASK over"))
		over_lines++;
}

static rcp_session *session(void)
{
	rcp_session *s = calloc(1, sizeof *s);
	if (!s)
		exit(2);
	s->g.record = record;
	s->state = S_ACTIVE;
	no_text = over_lines = 0;
	return s;
}

static int has(const char *file, const char *needle)
{
	FILE *f = fopen(file, "r");
	static char src[4u << 20];
	size_t n;

	if (!f) return 0;
	n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
	return strstr(src, needle) != NULL;
}

int main(void)
{
	rcp_session *s;
	uint8_t ask[4] = {0, 0, 0, 1};

	s = session();
	s->app_my_id = 1;
	for (int i = 0; i < 1000; i++)
		handle_clipboard(s, T_CLIPBOARD_ASK, ask, 4, 30000);
	CHECK(no_text >= 1 && no_text <= CLIPBOARD_BURST, "1. 1000 ASK in one instant: at most CLIPBOARD_BURST handled");
	handle_clipboard(s, T_CLIPBOARD_ASK, ask, 4, 30000 + MSG_WINDOW_MS + 1);
	CHECK(over_lines == 1, "2. one summary line when the window closes");
	{
		unsigned before = no_text;
		handle_clipboard(s, T_CLIPBOARD_ASK, ask, 4, 30000 + MSG_WINDOW_MS + 2000);
		CHECK(no_text == before + 1, "3. later it is served again");
	}
	free(s);

	s = session();
	s->app_my_id = 1;
	for (int i = 0; i < 120; i++)
		handle_clipboard(s, T_CLIPBOARD_ASK, ask, 4, 100000 + (uint64_t)i * 500);
	CHECK(no_text == 120 && over_lines == 0, "3b. 2 ASK a second for a minute: all handled, nothing said");
	free(s);

	s = session();
	for (uint32_t i = 1; i <= 1000; i++) {
		uint8_t a[8] = {(uint8_t)(i >> 24), (uint8_t)(i >> 16), (uint8_t)(i >> 8), (uint8_t)i, 0, 0, 0, 0};
		handle_clipboard(s, T_CLIPBOARD_ANNOUNCE, a, 8, 50000);
	}
	CHECK(s->app_peer_id >= 1 && s->app_peer_id <= CLIPBOARD_BURST, "4. 1000 ANNOUNCE in one instant: only the first ones were taken in");
	free(s);

	/* the summary of the window comes from msg_flush_all() even if nothing arrives any more */
	s = session();
	s->app_my_id = 1;
	for (int i = 0; i < 100; i++)
		handle_clipboard(s, T_CLIPBOARD_ASK, ask, 4, 200000);
	CHECK(over_lines == 0, "4b. no summary inside the window");
	msg_flush_all(s, 200000 + MSG_WINDOW_MS + 5);
	CHECK(over_lines == 1, "4c. msg_flush_all() writes the clipboard gate's summary when the window has ended");
	free(s);

	CHECK(has("src/keyboard.c", "KB_NOLETTER_LINES") && has("src/keyboard.c", "KB_NOLETTER_WINDOW_MS") && has("src/keyboard.c", "written < KB_NOLETTER_LINES"),
	      "5. keyboard.c: the «not producible» line has a window budget");
	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
