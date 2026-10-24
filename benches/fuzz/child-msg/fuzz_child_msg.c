/*
 * fuzz_child_msg.c — libFuzzer harness of the messages the PARENT receives from the CHILD (src/child.c, `handle()` and the
 * four assemblies behind it: FRAME, CURSOR, audio BLOCK, CLIPBOARD_FROM_SESSION; plus INTRO, STAGE, CANVAS,
 * SESSION_FINISHED, CLIPBOARD_REQUEST).  That socket is UNTRUSTED: the child runs the user's session.
 *
 * The REAL src/child.c is `#include`d (never modified).  Everything it links to that is not the parser — PAM, the
 * compositors, the encoders, the sockets — is NOT linked: `stubs_missing.c` is generated from the linker's list of
 * undefined symbols and every one of them TRAPS if called (so a parser path that wanders into them is seen, not hidden).
 * `receive_with_credentials()` and `credentials_match()` (the kernel's SO_PEERCRED, the magic) are the envelope: the harness
 * does what `children_move()` does between them and `handle()` — it hands `handle()` a body of EXACTLY `byte` bytes, in a heap
 * block of that size (ASan sees a read past it), never more than the envelope holds (MAX_ENVELOPE).
 *
 * Input: byte 0 = configuration (which hooks the host connects):
 *    bit0 on_clipboard_request (off: the product answers «I don't have it» through children_clipboard_response)
 *    bit1 on_clipboard_text · bit2 on_block · bit3 deposit (frames) · bit4 cursor · bit5 canvas + on_canvas_wait
 *    bit6 on_session_finished · bit7 the child is already `showed_up` and its uid is the stamped one (INTRO re-check path)
 * then ops (common.h: `u8 op · u16 length · argument`):
 *    0 MESSAGE  a0-1 the type (u16 LE, as in struct head), the rest is the body: handed to handle() as it is
 *    1 PIECES   the child cuts a big message the way it does: a0 kind (0 frame · 1 cursor · 2 clipboard · 3 block),
 *               a1-4 total (u32 LE; anything — the caps are the product's to enforce), a5-6 piece size (u16, clamped to
 *               MAX_PIECE + 1 on purpose), a7 how many pieces, a8 bits: 0 skip a piece (a hole) · 1 repeat one · 2 change the
 *               codec/width/height midway · 3 pieces start at offset 0 each time · 4 the offset overshoots by one;
 *               a9 codec/key byte · a10-11 width · a12-13 height · the data is a pattern
 *    2 NEWCHILD the child dies and a new one takes the slot: assemblies freed as child_free does (a0 bit 0: showed_up)
 *
 * ORACLES.  ASan + UBSan (halt), -rss_limit_mb / -malloc_limit_mb (a frame is at most FRAME_MAX = 16 MiB: nothing bigger is
 * ever allocated), and ASSERTIONS of what the comments of child.c state:
 *    A1 an assembly is either empty (pointer NULL ⇒ total = got = 0) or got ≤ total ≤ its cap (FRAME_MAX · the cursor's
 *       CURSOR_MAX_SIDE² × 4 · CLIPBOARD_CAP)
 *    A2 a clipboard text reaches the hook with the zero AFTER it (`text[byte] == 0`: «one extra byte is allocated and the
 *       zero is put there») and never more than CLIPBOARD_CAP bytes
 *    A3 a frame delivered has exactly the total it announced (≤ FRAME_MAX, > 0) — «a cut frame delivered as whole is a lie»
 *    A4 a cursor delivered is hidden (no bitmap) or has total ≤ the cursor's cap
 *    A5 an audio block delivered has codec 1 or 2 (§6.3) and `byte` bytes readable
 *    A6 nothing is delivered after the child is dismissed (`exiting`)
 */
#include "child.c"

#include <stdio.h>
#include "common.h"

#define FAIL(...) do { fprintf(stderr, "INVARIANT: " __VA_ARGS__); fputc('\n', stderr); __builtin_trap(); } while (0)

static children F;
static struct child G;
static unsigned cfg;
static uint8_t *body;

static void sum(const void *p, size_t n)
{
	volatile uint8_t x = 0;
	const uint8_t *b = p;
	for (size_t i = 0; i < n; i++) x ^= b[i];
}

static void h_deposit(void *c, const char *u, uid_t uid, uint8_t codec, bool key, const uint8_t *d, size_t n,
                      uint32_t w, uint32_t hh, uint64_t ins, uint32_t in)
{
	(void)c; (void)u; (void)uid; (void)codec; (void)key; (void)w; (void)hh; (void)ins; (void)in;
	if (G.exiting) FAIL("A6: a frame delivered after the child was dismissed");
	if (n == 0 || n > FRAME_MAX) FAIL("A3: a frame of %zu bytes delivered", n);
	sum(d, n);
}
static void h_dismiss(void *c, const char *u, uid_t uid) { (void)c; (void)u; (void)uid; }
static void h_cursor(void *c, const char *u, uid_t uid, uint16_t w, uint16_t hh, int16_t ax, int16_t ay,
                     const uint8_t *bm, size_t n)
{
	(void)c; (void)u; (void)uid; (void)w; (void)hh; (void)ax; (void)ay;
	if (G.exiting) FAIL("A6: a cursor delivered after the child was dismissed");
	if (n > (size_t)CURSOR_MAX_SIDE * CURSOR_MAX_SIDE * 4u) FAIL("A4: a cursor of %zu bytes delivered", n);
	if ((n != 0) != (bm != NULL)) FAIL("A4: cursor bitmap %p with %zu bytes", (const void *)bm, n);
	if (bm) sum(bm, n);
}
static void h_canvas(void *c, const char *u, uid_t uid, uint32_t a, uint32_t b, uint32_t d, uint32_t e)
{ (void)c; (void)u; (void)uid; (void)a; (void)b; (void)d; (void)e; }
static void h_canvas_wait(void *c, const char *u, uid_t uid, uint32_t a, uint32_t b)
{ (void)c; (void)u; (void)uid; (void)a; (void)b; }
static void h_finished(void *c, const char *u, uid_t uid) { (void)c; (void)u; (void)uid; }
static void h_block(void *c, const char *u, uid_t uid, uint8_t codec, uint64_t ins, const uint8_t *d, size_t n)
{
	(void)c; (void)u; (void)uid; (void)ins;
	if (codec != 1 && codec != 2) FAIL("A5: an audio block with codec %u delivered", codec);
	sum(d, n);
}
static void h_text(void *c, const char *u, uid_t uid, const char *t, size_t n)
{
	(void)c; (void)u; (void)uid;
	if (G.exiting) FAIL("A6: clipboard text delivered after the child was dismissed");
	if (n > CLIPBOARD_CAP) FAIL("A2: clipboard text of %zu bytes (cap %u)", n, CLIPBOARD_CAP);
	if (t[n] != 0) FAIL("A2: clipboard text of %zu bytes not followed by a zero", n);
	sum(t, n + 1);
}
static void h_request(void *c, const char *u, uid_t uid, uint32_t serial) { (void)c; (void)u; (void)uid; (void)serial; }

static void check(const char *where)
{
	if (G.assembly ? (G.assembly_got > G.assembly_total || G.assembly_total > FRAME_MAX || G.assembly_total == 0)
	               : (G.assembly_total || G.assembly_got))
		FAIL("A1 %s: frame assembly ptr=%p got=%zu total=%zu", where, (void *)G.assembly, G.assembly_got, G.assembly_total);
	if (G.cur_mount ? (G.cur_got > G.cur_total || G.cur_total > (size_t)CURSOR_MAX_SIDE * CURSOR_MAX_SIDE * 4u || !G.cur_total)
	                : (G.cur_total || G.cur_got))
		FAIL("A1 %s: cursor assembly ptr=%p got=%zu total=%zu", where, (void *)G.cur_mount, G.cur_got, G.cur_total);
	if (G.app_mount ? (G.app_got > G.app_total || G.app_total > CLIPBOARD_CAP || !G.app_total)
	                : (G.app_total || G.app_got))
		FAIL("A1 %s: clipboard assembly ptr=%p got=%zu total=%zu", where, (void *)G.app_mount, G.app_got, G.app_total);
}

static void new_child(bool showed)
{
	free(G.assembly); free(G.cur_mount);
	if (G.app_mount) explicit_bzero(G.app_mount, G.app_total);
	free(G.app_mount);
	memset(&G, 0, sizeof G);
	G.used = true;
	snprintf(G.user, sizeof G.user, "fuzz");
	G.uid = 1000;
	G.gid = 1000;
	G.pid = 0;  /* never a real process: kill(g->pid) is guarded by pid > 0 */
	G.fd = -1;
	G.showed_up = showed;
}

/* one message to handle(): the body in a heap block of exactly its size, within what the envelope can hold */
static void deliver(uint16_t kind, const uint8_t *b, size_t n)
{
	struct head t;
	if (G.exiting) return; /* children_move() stops reading a child it has dismissed */
	if (n > MAX_ENVELOPE - sizeof t) return; /* receive_with_credentials() says «longer than expected»: discarded */
	memset(&t, 0, sizeof t);
	memcpy(t.magic, "FIG1", 4);
	t.kind = kind;
	t.version = CHILD_VERSION;
	t.byte = (uint32_t)n;
	t.declared_uid = (uint32_t)G.uid;
	free(body);
	body = malloc(n ? n : 1);
	if (n) memcpy(body, b, n);
	(void)handle(&F, &G, &t, body, n);
	check("handle");
}

static void op_pieces(const uint8_t *a, size_t n)
{
	uint8_t z[14] = {0};
	memcpy(z, a, n < sizeof z ? n : sizeof z);
	uint32_t total = z[1] | z[2] << 8 | z[3] << 16 | (uint32_t)z[4] << 24;
	size_t piece = (z[5] | z[6] << 8);
	unsigned count = z[7] % 40 + 1, bits = z[8];
	if (piece > MAX_PIECE + 1) piece = MAX_PIECE + 1;
	uint32_t off = 0;
	uint16_t kinds[4] = {MSG_FRAME, MSG_CURSOR, MSG_CLIPBOARD_FROM_SESSION, MSG_BLOCK};
	uint16_t kind = kinds[z[0] & 3];
	uint8_t *buf = malloc(sizeof(struct body_frame) + piece + 1);
	for (unsigned i = 0; i < count; i++) {
		size_t hl;
		uint32_t pc = (uint32_t)piece;
		if (pc > total - off && off <= total && !(bits & 16)) pc = total - off;
		if (kind == MSG_FRAME) {
			struct body_frame c;
			memset(&c, 0, sizeof c);
			c.codec = z[9] + ((bits & 4) && i == 1);
			c.key = z[9] >> 7;
			c.width = z[10] | z[11] << 8;
			c.height = z[12] | z[13] << 8;
			c.total = total; c.offset = (bits & 8) ? 0 : off; c.piece = pc;
			if ((bits & 4) && i == 1) c.width++;
			memcpy(buf, &c, hl = sizeof c);
		} else if (kind == MSG_CURSOR) {
			struct body_cursor c;
			memset(&c, 0, sizeof c);
			c.width = z[10] | z[11] << 8; c.height = z[12] | z[13] << 8;
			if ((bits & 4) && i == 1) c.width++;
			c.total = total; c.offset = (bits & 8) ? 0 : off; c.piece = pc;
			memcpy(buf, &c, hl = sizeof c);
		} else if (kind == MSG_CLIPBOARD_FROM_SESSION) {
			struct body_clipboard c;
			memset(&c, 0, sizeof c);
			c.total = total; c.offset = (bits & 8) ? 0 : off; c.piece = pc;
			memcpy(buf, &c, hl = sizeof c);
		} else {
			struct body_block c;
			memset(&c, 0, sizeof c);
			c.codec = z[9] & 3; c.byte = pc;
			memcpy(buf, &c, hl = sizeof c);
		}
		for (size_t k = 0; k < pc && k < piece; k++) buf[hl + k] = (uint8_t)(k * 7 + i + (z[9] == 0xAA ? 0 : 1) * 0);
		if ((bits & 16) && pc < piece) { /* the piece claims more than it carries */ }
		size_t carry = pc < piece ? pc : piece;
		if (!((bits & 1) && i == 1)) deliver(kind, buf, hl + carry);
		if (bits & 2) deliver(kind, buf, hl + carry);
		off += pc + ((bits & 32) ? 1 : 0);
		if (off > total && !(bits & 32)) break;
	}
	free(buf);
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	if (size < 1) return 0;
	cfg = data[0];
	memset(&F, 0, sizeof F);
	F.cap = 1;
	F.v = &G;
	if (cfg & 1) F.on_clipboard_request = h_request;
	F.ctx_clipboard = NULL;
	if (cfg & 2) F.on_clipboard_text = h_text;
	if (cfg & 4) F.on_block = h_block;
	if (cfg & 8) F.deposit = h_deposit;
	if (cfg & 16) F.cursor = h_cursor;
	if (cfg & 32) { F.canvas = h_canvas; F.on_canvas_wait = h_canvas_wait; }
	if (cfg & 64) F.on_session_finished = h_finished;
	F.dismiss = h_dismiss;
	new_child((cfg & 128) != 0);

	rx_ops o = {data + 1, size - 1, 0};
	uint8_t op;
	const uint8_t *arg;
	size_t n;
	while (rx_next(&o, &op, &arg, &n)) {
		switch (op % 3) {
		case 0:
			if (n >= 2) deliver((uint16_t)(arg[0] | arg[1] << 8), arg + 2, n - 2);
			break;
		case 1: op_pieces(arg, n); break;
		case 2: new_child(n && (arg[0] & 1)); break;
		}
	}
	new_child(false);
	free(body);
	body = NULL;
	return 0;
}
