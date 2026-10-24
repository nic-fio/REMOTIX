/*
 * fuzz_rcp_msg.c — libFuzzer harness of the messages the server receives from the browser (RCP, `src/rcp.c`).
 *
 * The REAL src/rcp.c is `#include`d (never modified): its parsers are static, and the invariants below read the
 * session's own fields.  The product's log is `stubs_log.c` (formatted, not printed).  Nothing else is linked.
 *
 * ⭐ THE INPUT.  Byte 0 = configuration (which hooks the "host" connects):
 *        bit0 ask_verify (async PAM) · bit1 the five clipboard hooks · bit2 the input hooks
 *        bit3 stage_canvas answers   · bit4 session_local says «yes»  · bit5 layout_exists answers 0 · bit6 -1
 *        bit7 the host refuses to open streams (clipboard_open/video_open false)
 *    byte 1 = the FAILURE MASK (low 8 bits; op 13 sets all 16 later): which hooks answer «no» —
 *        bit0 ask_verify (rcp.c: the question to PAM did not leave) · bit1 video_write · bit2 input_* answer -1
 *        bit3 input_letter answers 1 (cannot be produced) · bit4 recanvas · bit5 layout · bit6 clipboard_write
 *        bit7 clipboard_offer · bit8 verify (sync) · bit9 clipboard_response
 *    then the OP STREAM of common.h (`u8 op · u16 length · argument`), op taken modulo 32:
 *        0 rcp_receive(arg)                       (the control channel, any split of the bytes)
 *        1 rcp_receive_input(stream = arg[0]&3, arg+1)
 *        2 rcp_receive_clipboard(stream = arg[0]&15, fin = arg[1]&1, arg+2)
 *        3 rcp_time(now += u32 ms of arg)         (the fixed delay, the ceilings, the silence)
 *        4 rcp_verdict(last ticket or, if arg[1]&1, a wrong one; admitted = arg[0]&1)
 *        5 rcp_channel_closed · 6 rcp_closed_by_client(arg[0]) · 7 rcp_sign_of_life
 *        8 rcp_clipboard_from_session(arg, n): the text WITH its length, a NUL inside included, as `assemble_clipboard` delivers · 9 rcp_clipboard_ask(serial = u32 of arg)
 *       10 rcp_receive again (a second door for the same bytes) · 11 rcp_dismiss · 12 rcp_violation
 *       13 set the failure mask (u16 of arg) — (the server's clipboard stream is unidirectional: nothing is received on it)
 *       14 rcp_inactivity_set / rcp_eviction_set (u32 ms)   · 15 rcp_free + rcp_open again (a second session, same address)
 *       16 rcp_video_open(key = arg[0]&1, length = u16 of arg[1..2] (arg[0]&2: 17 MiB, arg[0]&4: 1 MiB),
 *          instant = u32 of arg[3..6], input = u32 of arg[7..10], rest of arg = first piece)
 *       17 rcp_video_piece(arg) · 18 rcp_video_finish · 19 rcp_video_send(key = arg[0]&1, arg+1)
 *       20 rcp_video_no_credit(key = arg[0]&1, remain = u32 of arg[1..]) followed by rcp_video_abandon
 *
 * ORACLES.  ASan + UBSan (halt on error), the allocation ceilings (-rss_limit_mb, -malloc_limit_mb), and ASSERTIONS of
 * the documented invariants (a failed one is a `__builtin_trap`, after the message on stderr):
 *    I-a  the accumulation of the control channel never exceeds MAX_ACCUMULATION (1 MiB, §6.1), the input one never
 *         exceeds I_ACCUMULATION, a clipboard slot never holds more body than its declared (and capped) length
 *    I-b  a clipboard body is declared ≤ RCP_CLIPBOARD_CAP+4 and never more bytes are kept than were received
 *    I-c  every message the server SENDS is framed: u16 type · u32 length == the bytes that follow (§6.1) ≤ 1 MiB
 *    I-d  `close` is called at most once per session and with a reason of §8.2 (1..0x10)  (§8.1: one truth)
 *    I-e  a receive that returns false leaves the session finished; a finished session stays finished and answers false
 *    I-f  the paste queue (app_serial_n) never exceeds A_STREAM_MAX; head_n ≤ 6
 */
#include "rcp.c"

#include <assert.h>
#include <stdio.h>
#include "common.h"

#define FAIL(...) do { fprintf(stderr, "INVARIANT: " __VA_ARGS__); fputc('\n', stderr); __builtin_trap(); } while (0)

typedef struct {
	unsigned cfg;
	unsigned fail;
	uint64_t ticket;
	bool have_ticket;
	int closes;
	int64_t next_stream;
	int64_t last_clip_stream;
	unsigned sent;
} H;

static H h;
static rcp_session *S;
static uint8_t *copy;

static void h_send(void *c, const uint8_t *d, size_t n)
{
	(void)c;
	h.sent++;
	if (n < 6) FAIL("send_msg of %zu bytes (< header)", n);
	uint32_t L = ((uint32_t)d[2] << 24) | ((uint32_t)d[3] << 16) | ((uint32_t)d[4] << 8) | d[5];
	if ((size_t)L != n - 6) FAIL("send_msg: type %02x%02x declares %u body bytes, %zu follow", d[0], d[1], L, n - 6);
	if (n > 1024u * 1024u) FAIL("send_msg of %zu bytes beyond 1 MiB", n);
}
static void h_close(void *c, uint8_t r)
{
	(void)c;
	if (++h.closes > 1) FAIL("close called %d times for the same session", h.closes);
	if (r < 1 || r > 0x10) FAIL("close with reason %#x, not in §8.2", r);
}
static void h_record(void *c, const char *l) { (void)c; (void)l; }
#define FAILS(b) ((h.fail >> (b)) & 1)
static bool h_verify(void *c, const char *u, const char *p) { (void)c; return !FAILS(8) && u && p && (p[0] & 1); }
static bool h_ask_verify(void *c, const char *u, const char *p, uint64_t *t)
{
	(void)c; (void)u; (void)p;
	if (FAILS(0)) return false;
	*t = ++h.ticket;
	h.have_ticket = true;
	return true;
}
static bool h_vopen(void *c, int64_t *st, uint64_t *rem)
{
	(void)c;
	*rem = 5;
	if (h.cfg & 0x80) return false;
	*st = 3 + 4 * (h.next_stream++);
	return true;
}
static bool h_vwrite(void *c, int64_t st, const uint8_t *d, size_t n)
{
	volatile uint8_t x = 0;
	(void)c; (void)st;
	for (size_t i = 0; i < n; i++) x ^= d[i];
	return !FAILS(1);
}
static void h_vfin(void *c, int64_t st) { (void)c; (void)st; }
static int h_ptr(void *c, uint32_t x, uint32_t y) { (void)c; (void)x; (void)y; return FAILS(2) ? -1 : 0; }
static int h_btn(void *c, uint16_t k, int p) { (void)c; (void)k; (void)p; return FAILS(2) ? -1 : 0; }
static int h_whl(void *c, int32_t x, int32_t y) { (void)c; (void)x; (void)y; return FAILS(2) ? -1 : 0; }
static int h_let(void *c, uint32_t k) { (void)c; (void)k; return FAILS(3) ? 1 : FAILS(2) ? -1 : 0; }
static int h_pos(void *c, uint16_t k, int p) { (void)c; (void)k; (void)p; return FAILS(2) ? -1 : 0; }
static int h_rel(void *c) { (void)c; return 0; }
static bool h_recanvas(void *c, uint32_t w, uint32_t hh) { (void)c; (void)w; (void)hh; return !FAILS(4); }
static int h_lexists(void *c, const char *n)
{
	(void)c; (void)n;
	return (h.cfg & 0x40) ? -1 : (h.cfg & 0x20) ? 0 : 1;
}
static bool h_layout(void *c, const char *n) { (void)c; (void)n; return !FAILS(5); }
static bool h_stage(void *c, uint32_t *w, uint32_t *hh) { (void)c; *w = 1912; *hh = 1044; return (h.cfg & 8) != 0; }
static bool h_local(void *c, const char *u, char *d, size_t n) { (void)c; (void)u; if (n) d[0] = 0; return (h.cfg & 0x10) != 0; }
static bool h_copen(void *c, int64_t *st, uint64_t *rem)
{
	(void)c;
	*rem = 3;
	if (h.cfg & 0x80) return false;
	h.last_clip_stream = *st = 3 + 4 * (h.next_stream++);
	return true;
}
static bool h_cwrite(void *c, int64_t st, const uint8_t *d, size_t n)
{
	volatile uint8_t x = 0;
	(void)c; (void)st;
	for (size_t i = 0; i < n; i++) x ^= d[i];
	return !FAILS(6) && n < (2u << 20);
}
static void h_cfin(void *c, int64_t st) { (void)c; (void)st; }
static bool h_coffer(void *c) { (void)c; return !FAILS(7); }
static bool h_cresp(void *c, uint32_t ser, const char *t, size_t n)
{
	(void)c; (void)ser;
	/* (text, byte) is a pointer + length, NOT a C string: read exactly `byte` bytes; no NUL may be inside (§5.4) */
	if (t && n && memchr(t, 0, n)) FAIL("clipboard_response: a NUL inside the %zu announced bytes", n);
	return !FAILS(9);
}
static void h_term(void *c) { (void)c; }
static bool h_resumed(void *c) { (void)c; return false; }
static const char *h_desktop(void *c) { (void)c; return "gnome"; }

static void check(const char *where)
{
	rcp_session *s = S;
	if (s->acc_len > MAX_ACCUMULATION) FAIL("%s: acc_len %zu > MAX_ACCUMULATION", where, s->acc_len);
	if (s->inp_acc_len > I_ACCUMULATION) FAIL("%s: inp_acc_len %zu > I_ACCUMULATION", where, s->inp_acc_len);
	if (s->app_serial_n > A_STREAM_MAX || s->app_serial_n < 0) FAIL("%s: app_serial_n %d", where, s->app_serial_n);
	for (int i = 0; i < A_STREAM_MAX; i++) {
		if (!s->app_in[i].used) continue;
		if (s->app_in[i].head_n > 6) FAIL("%s: clipboard head_n %zu", where, (size_t)s->app_in[i].head_n);
		if (s->app_in[i].body) {
			if (s->app_in[i].lung > RCP_CLIPBOARD_CAP + 4u) FAIL("%s: clipboard body %u over the cap", where, s->app_in[i].lung);
			if (s->app_in[i].body_n > s->app_in[i].lung) FAIL("%s: clipboard body_n %zu > lung %u", where, (size_t)s->app_in[i].body_n, s->app_in[i].lung);
		}
	}
}

static void open_session(void)
{
	rcp_hooks g;
	memset(&g, 0, sizeof g);
	g.send_msg = h_send; g.close = h_close; g.record = h_record; g.verify = h_verify;
	if (h.cfg & 1) g.ask_verify = h_ask_verify;
	g.video_open = h_vopen; g.video_write = h_vwrite; g.video_fin = h_vfin; g.video_reset = h_vfin;
	if (h.cfg & 4) {
		g.input_pointer = h_ptr; g.input_button = h_btn; g.input_wheel = h_whl; g.input_letter = h_let;
		g.input_position = h_pos; g.input_release_all = h_rel;
	}
	g.recanvas = h_recanvas; g.layout_exists = h_lexists; g.layout = h_layout; g.stage_canvas = h_stage;
	g.session_local = h_local;
	if (h.cfg & 2) {
		g.clipboard_open = h_copen; g.clipboard_write = h_cwrite; g.clipboard_fin = h_cfin;
		g.clipboard_offer = h_coffer; g.clipboard_response = h_cresp;
	}
	g.terminate_session = h_term; g.session_resumed = h_resumed; g.desktop = h_desktop;
	h.closes = 0;
	S = rcp_open(&g, "192.0.2.7", rx_now_ms);
	if (!S) FAIL("rcp_open failed");
}

/* a receive that says false must have finished the session; a finished one stays so */
static void verdict_of_receive(bool alive, const char *where)
{
	if (!alive && !rcp_is_finished(S)) FAIL("%s returned false but the session is not finished (%s)", where, rcp_state_name(S));
	if (alive && S->state == S_FINISHED) FAIL("%s returned true on a finished session", where);
	check(where);
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
	if (size < 2) return 0;
	memset(&h, 0, sizeof h);
	h.cfg = data[0];
	h.fail = data[1];
	rx_now_ms = 1000000;
	rcp_reset_session_log();
	rcp_cap_set(RCP_SESSION_CAP);
	rcp_video_codec_set("hevc,h264");
	rcp_inactivity_set(30u * 60u * 1000u);
	rcp_eviction_set(15000);
	open_session();

	rx_ops o = {data + 2, size - 2, 0};
	uint8_t op;
	const uint8_t *arg;
	size_t n;
	while (rx_next(&o, &op, &arg, &n)) {
		/* the argument is copied to a heap block of EXACTLY its size: ASan sees a read past it */
		free(copy);
		copy = malloc(n ? n : 1);
		if (n) memcpy(copy, arg, n);
		arg = copy;
		switch (op & 31) {
		case 0: case 10:
			verdict_of_receive(rcp_receive(S, arg, n, rx_now_ms), "rcp_receive");
			break;
		case 1:
			if (n) verdict_of_receive(rcp_receive_input(S, arg[0] & 3, arg + 1, n - 1, rx_now_ms), "rcp_receive_input");
			break;
		case 2:
			if (n >= 2) verdict_of_receive(rcp_receive_clipboard(S, arg[0] & 15, arg + 2, n - 2, arg[1] & 1, rx_now_ms),
			                              "rcp_receive_clipboard");
			break;
		case 3:
			rx_now_ms += rx_u32(arg, n);
			verdict_of_receive(rcp_time(S, rx_now_ms), "rcp_time");
			break;
		case 4:
			rcp_verdict(S, (n > 1 && (arg[1] & 1)) ? h.ticket + 7 : h.ticket, n && (arg[0] & 1), rx_now_ms);
			check("verdict");
			break;
		case 5: rcp_channel_closed(S); check("channel_closed"); break;
		case 6: rcp_closed_by_client(S, n ? arg[0] : 0); check("closed_by_client"); break;
		case 7: rcp_sign_of_life(S, rx_now_ms); break;
		case 8: {
			char *t = malloc(n + 1);
			memcpy(t, arg, n);
			t[n] = 0;
			rcp_clipboard_from_session(S, t, n); /* (t, n): a NUL inside reaches rcp.c */
			free(t);
			check("from_session");
			break;
		}
		case 9: rcp_clipboard_ask(S, rx_u32(arg, n), rx_now_ms); check("clipboard_ask"); break;
		case 11: rcp_dismiss(S, n ? (uint8_t)(1 + arg[0] % 16) : 0x0C, "x"); check("dismiss"); break;
		case 12: rcp_violation(S, "x"); check("violation"); break;
		case 13: if (n >= 2) h.fail = (arg[0] << 8) | arg[1]; break;
		case 14: if (n && (arg[0] & 1)) rcp_inactivity_set(rx_u32(arg, n)); else rcp_eviction_set(rx_u32(arg, n)); break;
		case 15:
			rcp_free(S);
			open_session();
			break;
		case 16:
			if (n >= 11) {
				size_t len = (arg[0] & 2) ? 17u << 20 : (arg[0] & 4) ? 1u << 20 : (size_t)((arg[1] << 8) | arg[2]);
				uint32_t ins = ((uint32_t)arg[7] << 24) | (arg[8] << 16) | (arg[9] << 8) | arg[10];
				rcp_video_open(S, arg[0] & 1, len, rx_u32(arg + 3, 4), ins, rx_now_ms);
				if (n > 11) rcp_video_piece(S, arg + 11, n - 11);
				check("video_open");
			}
			break;
		case 17: rcp_video_piece(S, arg, n); check("video_piece"); break;
		case 18: rcp_video_finish(S); check("video_finish"); break;
		case 19: if (n) { rcp_video_send(S, arg[0] & 1, arg + 1, n - 1, rx_now_ms, 1, rx_now_ms); check("video_send"); } break;
		case 20: if (n) { rcp_video_no_credit(S, arg[0] & 1, rx_u32(arg + 1, n - 1)); rcp_video_abandon(S, "x"); check("video_no_credit"); } break;
		}
	}
	rcp_free(S);
	S = NULL;
	free(copy);
	copy = NULL;
	return 0;
}
