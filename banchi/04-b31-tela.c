/*
 * 04-b31-tela.c — THE BENCH OF THE CHANGING CANVAS, `RCP.md` §7.1 and §6.2.
 *
 *   04-b31-tela            runs all the cases
 *   04-b31-tela <n>        runs only case n
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, AND WHY IT IS NOT A NETWORK BENCH
 *
 * `CODER.md` §3.6: *«when the chain is already narrowed down, do not run another
 * round of benches: write the minimal program that calls only the suspect
 * function on a known input.  It costs less and closes sooner.»*
 *
 * The new chain of 15 Aug 2026 — `ADATTA_TELA` → `figli_ritela()` →
 * `cattura_ridimensiona()` → the frame that comes back — crosses **two
 * processes, a compositor and a graphics card**.  ⛔ Testing all of it needs the
 * test machine with the graphical session alive; ⭐ but the HALF that decides —
 * the state machine of `rcp.c` — needs none of this: it receives bytes, returns
 * bytes, and asks whoever hosts it to act.
 *
 * ⇒ Here `rcp.c` is mounted BARE, with test hooks in place of the stage.  The
 *   «stage» is a variable of this file: it can be made to answer late, grant a
 *   size different from the one asked, or not answer at all.
 *
 * ⛔ AND WHAT THIS BENCH DOES NOT TEST, declared instead of discovered:
 *   · **it does not test that the compositor resizes**: that is `[M]` of
 *     `banchi/04-in8-misura.c` (Mutter 41.6 ms, labwc 5.1 ms);
 *   · **it does not test that the pixels are right**: there is not a pixel here;
 *   · **it does not test the page**: `src/pagina.html` has its own counters
 *     (§6.2), and those are watched from the browser.
 *   ⇒ It tests the one thing that sits in between, and it is the one no bench
 *     was watching: **that every `ADATTA_TELA` gets exactly one `TELA` back, and
 *     that the canvas in force never takes a value nobody granted.**
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE EXPECTATION IS DECLARED FIRST (rule B0.4 of `LEZIONI.md`): every case
 *    below carries its «expected» line, and the bench compares against it.  A
 *    bench that prints what happened and calls it a result measures nothing.
 */
#include "../src/rcp.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 *  The wire, in bytes — §6.0/§6.1: network order (big-endian), no padding
 * ------------------------------------------------------------------ */

static uint8_t fuori[4096];
static size_t out_n;

static void mette(uint8_t **p, uint8_t v) { *(*p)++ = v; }
static void mette16(uint8_t **p, uint16_t v)
{
	mette(p, (uint8_t)(v >> 8));
	mette(p, (uint8_t)v);
}
static void mette32(uint8_t **p, uint32_t v)
{
	mette16(p, (uint16_t)(v >> 16));
	mette16(p, (uint16_t)v);
}
static void putstr(uint8_t **p, const char *s)
{
	size_t n = strlen(s);
	mette16(p, (uint16_t)n);
	memcpy(*p, s, n);
	*p += n;
}

/* A CLIENT message: header (u16 type, u32 length) + body. */
static size_t border(uint8_t *buf, uint16_t tipo, const uint8_t *corpo,
                         size_t len)
{
	uint8_t *p = buf;
	mette16(&p, tipo);
	mette32(&p, (uint32_t)len);
	memcpy(p, corpo, len);
	return 6 + len;
}

/* ------------------------------------------------------------------ *
 *  The fake stage — and its three ways of behaving
 * ------------------------------------------------------------------ */

static struct {
	/* what it has been asked */
	uint32_t requested_w, requested_h;
	int how_many_requests;
	/* how it answers */
	bool accetta;        /* does the `ritela` hook return true?             */
	bool grants_other;  /* grants a size DIFFERENT from the one asked      */
	uint32_t other_w, other_h;
	/* what size it has now, for the `stage_canvas` hook */
	bool size_known;
	uint32_t size_w, size_h;
} palco;

/* ⛔⛔⭐ THE BIRTH REQUEST — 16 Aug 2026, and it kept this bench
 *      RED FOR A WHOLE DAY without anybody noticing.
 *
 *      On 15 August the cure for the tail of the access times (commit `477d708`)
 *      did one extra, declared thing: the session, as soon as it attaches,
 *      **tells the stage at what size it must be born** instead of letting it be
 *      born at a size of its own and then changing it.  The log writes it at
 *      every access: *«§4.5: I tell the stage that the canvas of this session is
 *      NxM — so it is born that way instead of being born at a size of its own
 *      and having to change it (and the change is a race)»*.
 *
 *      ⇒ Since then `apri_sessione()` leaves **one** request to the stage behind
 *      it, and seven cases out of eighteen were still counting from zero.  ⛔ All
 *      seven with the SAME gap — one request — and four of them also showed
 *      «TELA sent 0», which was not a second defect: they are written
 *      `bene = …; if (bene) { … }`, and once the first condition failed the
 *      second half was never executed.  One defect only, seven faces.
 *
 * ⭐ AND THE CURE IS NOT ADDING ONE.  If this bench merely expected a bigger
 *    number, it would become **blind precisely to the thing that turned it
 *    red**: the day the birth request disappeared — that is, the seventeen
 *    seconds of tail came back — the counts would add up all the same.
 *    ⇒ TWO things are done:
 *
 *      1. the cases count **from after the birth**, with `after_birth()`,
 *         which tells the reader that the birth exists and is another matter;
 *      2. ⭐ **case 19** tests the birth on its own: if it disappears, it is IT
 *         that turns red, and with a message that names the defect. */
static int birth_requests;

static int after_birth(void)
{
	return palco.how_many_requests - birth_requests;
}

static void raccogli(void); /* reads what the server has sent, and empties it */

static bool g_recanvas(void *ctx, uint32_t l, uint32_t a)
{
	(void)ctx;
	palco.how_many_requests++;
	palco.requested_w = l;
	palco.requested_h = a;
	return palco.accetta;
}

static bool g_stage_canvas(void *ctx, uint32_t *l, uint32_t *a)
{
	(void)ctx;
	if (!palco.size_known)
		return false;
	*l = palco.size_w;
	*a = palco.size_h;
	return true;
}

/* ⭐⭐ THE STAGE ANSWERS — and it is the road the first draft did NOT have: there
 *     the parent guessed from the frames «if one of a different size arrives then
 *     the stage has obeyed», and with two chained requests it guessed wrong.
 *
 * `voluta_*` = which request it answers.  ⛔ It is what makes the recognition
 * a FACT instead of a deduction. */
static void stage_replies(rcp_sessione *s, uint32_t intended_w, uint32_t intended_h,
                           uint64_t ora)
{
	uint32_t l = intended_w, a = intended_h;
	if (palco.grants_other) {
		l = palco.other_w;
		a = palco.other_h;
	}
	palco.size_known = true;
	palco.size_w = l;
	palco.size_h = a;
	rcp_tela_dal_palco(s, intended_w, intended_h, l, a, ora);
	raccogli();
}

/* The stage answers the LAST request it received. */
static void palco_consegna(rcp_sessione *s, uint64_t ora)
{
	stage_replies(s, palco.requested_w, palco.requested_h, ora);
}

/* ⛔ «I didn't make it»: `0x0`, which is NOT a size. */
static void stage_gives_up(rcp_sessione *s, uint64_t ora)
{
	rcp_tela_dal_palco(s, palco.requested_w, palco.requested_h, 0, 0, ora);
	raccogli();
}

/* ------------------------------------------------------------------ *
 *  The hooks
 * ------------------------------------------------------------------ */

static bool chiuso;
static uint8_t close_reason;
static bool parlantina;

static void g_send(void *ctx, const uint8_t *dati, size_t len)
{
	(void)ctx;
	if (out_n + len > sizeof fuori)
		return;
	memcpy(fuori + out_n, dati, len);
	out_n += len;
}
static void g_shut(void *ctx, uint8_t motivo)
{
	(void)ctx;
	chiuso = true;
	close_reason = motivo;
}
static void g_record(void *ctx, const char *riga)
{
	(void)ctx;
	if (parlantina)
		printf("      | %s\n", riga);
}
static bool g_verify(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	return strcmp(utente, "prova") == 0 && strcmp(parola, "prova2026") == 0;
}

/* ------------------------------------------------------------------ *
 *  Reading what the server has sent
 * ------------------------------------------------------------------ */

#define T_SESSIONE 0x0007u
#define T_CANVAS 0x000Eu
#define T_FIT_CANVAS 0x000Bu
#define T_HELLO 0x0001u
#define T_CREDENZIALI 0x0003u
#define T_ATTACH 0x0006u

struct seen_canvas {
	uint8_t esito, motivo;
	uint32_t l, a;
};

static int canvas_count;
static struct seen_canvas last_canvas;
static uint32_t session_w, session_h;

/* Reads all the accumulated messages and counts the `TELA`s.  ⛔ It EMPTIES: the
 * count that matters is «how many have gone out since I last looked», not the
 * total. */
static void raccogli(void)
{
	size_t i = 0;
	canvas_count = 0;
	while (i + 6 <= out_n) {
		uint16_t tipo = (uint16_t)((fuori[i] << 8) | fuori[i + 1]);
		uint32_t len = ((uint32_t)fuori[i + 2] << 24)
		             | ((uint32_t)fuori[i + 3] << 16)
		             | ((uint32_t)fuori[i + 4] << 8) | fuori[i + 5];
		const uint8_t *c = fuori + i + 6;
		if (i + 6 + len > out_n)
			break;
		if (tipo == T_CANVAS && len >= 10) {
			canvas_count++;
			last_canvas.esito = c[0];
			last_canvas.motivo = c[1];
			last_canvas.l = ((uint32_t)c[2] << 24) | ((uint32_t)c[3] << 16)
			              | ((uint32_t)c[4] << 8) | c[5];
			last_canvas.a = ((uint32_t)c[6] << 24) | ((uint32_t)c[7] << 16)
			              | ((uint32_t)c[8] << 8) | c[9];
		}
		if (tipo == T_SESSIONE && len >= 9) {
			session_w = ((uint32_t)c[1] << 24) | ((uint32_t)c[2] << 16)
			           | ((uint32_t)c[3] << 8) | c[4];
			session_h = ((uint32_t)c[5] << 24) | ((uint32_t)c[6] << 16)
			           | ((uint32_t)c[7] << 8) | c[8];
		}
		i += 6 + len;
	}
	out_n = 0;
}

/* ------------------------------------------------------------------ *
 *  The handshake, up to `SESSIONE`
 * ------------------------------------------------------------------ */

static uint64_t orologio;

/* ⛔ Where the next session comes from: case 18 needs it, as it wants TWO —
 *    and the slot of §8.2 is per USER, not per address, so two different
 *    origins of the same user compete for the same slot. */
static const char *next_provenance = "10.0.0.9:5000";

static rcp_sessione *apri_sessione(uint32_t tela_l, uint32_t tela_a,
                                   const char *max_measure, bool with_hooks)
{
	rcp_ganci g;
	rcp_sessione *s;
	uint8_t corpo[512], envelope[600];
	uint8_t *p;
	size_t n;

	memset(&g, 0, sizeof g);
	g.manda = g_send;
	g.chiudi = g_shut;
	g.registra = g_record;
	g.verifica = g_verify;
	if (with_hooks) {
		g.ritela = g_recanvas;
		g.stage_canvas = g_stage_canvas;
	}

	chiuso = false;
	out_n = 0;
	orologio = 1000;
	s = rcp_apri(&g, next_provenance, orologio);
	if (!s)
		return NULL;

	/* CIAO: version + capabilities (§4.3).
	 * ⛔ `audio.codec=pcm` is NOT decoration: §4.3 demands it, and without it the
	 *    server says farewell with `NIENTE_IN_COMUNE` — something this bench
	 *    discovered on its first run, with all cases red and zero `SESSIONE`.
	 *    It is `CODER.md` §3.3: the bench is certified BEFORE pointing it at the
	 *    unknown, or a red does not tell «the unknown does not work» from
	 *    «the bench did not work». */
	p = corpo;
	mette16(&p, 1);                      /* version */
	mette16(&p, max_measure ? 4 : 3);     /* how many capabilities */
	putstr(&p, "video.codec");
	putstr(&p, "hevc");
	putstr(&p, "video.profondita");
	putstr(&p, "8,10");
	putstr(&p, "audio.codec");
	putstr(&p, "pcm");
	if (max_measure) {
		putstr(&p, "video.misura_massima");
		putstr(&p, max_measure);
	}
	n = border(envelope, T_HELLO, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, envelope, n, orologio);

	/* CREDENZIALI */
	p = corpo;
	putstr(&p, "prova");
	putstr(&p, "prova2026");
	n = border(envelope, T_CREDENZIALI, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, envelope, n, orologio);
	/* ⛔ §4.4-bis: the fixed second.  Time is made to flow, which is what the
	 *    server's `poll` loop would do. */
	orologio += 1500;
	rcp_tempo(s, orologio);

	/* ATTACCA */
	p = corpo;
	mette32(&p, tela_l);
	mette32(&p, tela_a);
	mette32(&p, tela_l); /* view: it does not matter here */
	mette32(&p, tela_a);
	putstr(&p, "it");
	n = border(envelope, T_ATTACH, corpo, (size_t)(p - corpo));
	rcp_ricevi(s, envelope, n, orologio);
	raccogli();
	/* ⛔ Here the session has already told the stage at what size to be born
	 *    (§4.5): what the attach left behind is noted, so the cases can count
	 *    from after it.  ⚠ The long reason is at `birth_requests`. */
	birth_requests = palco.how_many_requests;
	return s;
}

static void send_fit(rcp_sessione *s, uint32_t l, uint32_t a)
{
	uint8_t corpo[8], envelope[32];
	uint8_t *p = corpo;
	size_t n;
	mette32(&p, l);
	mette32(&p, a);
	n = border(envelope, T_FIT_CANVAS, corpo, 8);
	rcp_ricevi(s, envelope, n, orologio);
	raccogli();
}

/* ------------------------------------------------------------------ *
 *  The cases
 * ------------------------------------------------------------------ */

static int falliti, passati;

static void esito(const char *caso, bool bene, const char *atteso,
                  const char *visto)
{
	if (bene) {
		passati++;
		printf("  \033[1;32mOK\033[0m  %-34s %s\n", caso, visto);
	} else {
		falliti++;
		printf("  \033[1;31mNO\033[0m  %-34s\n        expected: %s\n        seen:     %s\n",
		       caso, atteso, visto);
	}
}

static char detto[256];
static const char *dillo(void)
{
	snprintf(detto, sizeof detto,
	         "TELA sent %d (outcome %u reason %u -> %ux%u), requests to the stage "
	         "%d (of which %d at birth, §4.5), canvas in force %ux%u",
	         canvas_count, last_canvas.esito, last_canvas.motivo, last_canvas.l,
	         last_canvas.a, palco.how_many_requests, birth_requests,
	         last_canvas.l, last_canvas.a);
	return detto;
}

static void reset_stage(void)
{
	memset(&palco, 0, sizeof palco);
	palco.accetta = true;
	memset(&last_canvas, 0, sizeof last_canvas);
	canvas_count = 0;
}

/* 1 — the good road: it is asked, the stage delivers, ONE `TELA` goes out. */
static void case1(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* ⛔ EXPECTED: no `TELA` yet — the answer is the frame. */
	bene = canvas_count == 0 && after_birth() == 1
	    && palco.requested_w == 1600 && palco.requested_h == 900;
	if (bene) {
		palco_consegna(s, orologio);
		rcp_canvas_in_effect(s, &l, &a);
		bene = canvas_count == 1 && last_canvas.esito == 1
		    && last_canvas.l == 1600 && last_canvas.a == 900 && l == 1600
		    && a == 900 && !chiuso;
	}
	esito("1 the good road", bene,
	      "no TELA before the frame, then only ONE with 1600x900",
	      dillo());
	rcp_libera(s);
}

/* 2 — the size that is already there: answer AT ONCE and do not touch the stage. */
static void case2(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1920, 1080);
	bene = canvas_count == 1 && last_canvas.esito == 1 && last_canvas.motivo == 0
	    && last_canvas.l == 1920 && last_canvas.a == 1080
	    && after_birth() == 0 && !chiuso;
	esito("2 the size already there", bene,
	      "ONE TELA(ADATTATA 1920x1080) at once, ZERO requests to the stage",
	      dillo());
	rcp_libera(s);
}

/* 3 — two `ADATTA_TELA` in a row: TWO `TELA`s, or the client's count never gets
 *     back to zero and the page holds back frames forever (§6.2). */
static void case3(void)
{
	rcp_sessione *s;
	int primi, secondi;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	primi = canvas_count;
	send_fit(s, 1280, 720);
	secondi = canvas_count;
	/* ⛔ EXPECTED: the second request sends out the `TELA` that answers the
	 *    FIRST (NON_ORA), and then the frame sends out the one of the second. */
	bene = primi == 0 && secondi == 1 && last_canvas.esito == 2
	    && last_canvas.motivo == 3;
	if (bene) {
		palco_consegna(s, orologio);
		bene = canvas_count == 1 && last_canvas.esito == 1
		    && last_canvas.l == 1280 && last_canvas.a == 720 && !chiuso;
	}
	esito("3 two ADATTA_TELA in a row", bene,
	      "two TELA in all: NON_ORA to the first, ADATTATA 1280x720 to the second",
	      dillo());
	rcp_libera(s);
}

/* 4 — the stage does not deliver: after the deadline the answer is `NON_ORA`
 *     (§7.1: «a silence leaves the client waiting forever»). */
static void case4(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* one clock tick BEFORE the deadline: nothing must go out */
	orologio += RCP_TELA_ATTESA_MS - 1;
	rcp_tempo(s, orologio);
	raccogli();
	bene = canvas_count == 0;
	if (bene) {
		orologio += 2;
		rcp_tempo(s, orologio);
		raccogli();
		rcp_canvas_in_effect(s, &l, &a);
		bene = canvas_count == 1 && last_canvas.esito == 2
		    && last_canvas.motivo == 3 && l == 1920 && a == 1080 && !chiuso;
	}
	esito("4 the stage does not deliver", bene,
	      "nothing before the deadline, then ONE TELA(RIFIUTATA, NON_ORA), canvas 1920x1080",
	      dillo());
	rcp_libera(s);
}

/* 5 — the size ABOVE THE MAXIMUM: since 1 Oct 2026 (`RCP.md` §4.5, canvas at
 *     most 4096x2304, user decision) it is NOT refused: it is REDUCED to the
 *     maximum — the side that overflows to the maximum, the other as it is — and
 *     passed to the stage like any size, with the «DECLARED FALLBACK» line in
 *     the log.  ⛔ And the session stays alive, as before: 100000x100000 was the
 *     number «capable of killing the compositor», and here it becomes 4096x2304
 *     BEFORE reaching the stage.  (Until 30 Sep it was `TELA(RIFIUTATA,
 *     MISURA_FUORI_LIMITI)`; the refusal stays BELOW the minimum: case 17.) */
static void case5(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 100000, 100000);
	bene = canvas_count == 0 && after_birth() == 1
	    && palco.requested_w == RCP_TELA_L_MASSIMA
	    && palco.requested_h == RCP_TELA_A_MASSIMA && !chiuso;
	esito("5 size above the maximum: reduced", bene,
	      "no TELA at once, ONE request to the stage at 4096x2304 (the maximum of "
	      "§4.5), session ALIVE",
	      dillo());
	rcp_libera(s);
}

/* 6 — the odd size is truncated down and IT IS SAID (§5.0-sexies: «a pixel
 *     stated is worth more than a pixel hidden in a scale»). */
static void case6(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 2133, 1201);
	bene = after_birth() == 1 && palco.requested_w == 2132
	    && palco.requested_h == 1200;
	if (bene) {
		palco_consegna(s, orologio);
		bene = canvas_count == 1 && last_canvas.l == 2132
		    && last_canvas.a == 1200;
	}
	esito("6 the odd size, truncated", bene,
	      "to the stage 2132x1200 (truncated to even), and the TELA carries that",
	      dillo());
	rcp_libera(s);
}

/* 7 — §4.5: the stage grants a size DIFFERENT from the one asked.  The `TELA`
 *     must carry the REAL one, not the one asked. */
static void case7(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	palco.grants_other = true;
	palco.other_w = 1366;
	palco.other_h = 768;
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	palco_consegna(s, orologio);
	rcp_canvas_in_effect(s, &l, &a);
	bene = canvas_count == 1 && last_canvas.esito == 1 && last_canvas.l == 1366
	    && last_canvas.a == 768 && l == 1366 && a == 768 && !chiuso;
	esito("7 the stage grants other (§4.5)", bene,
	      "ONE TELA(ADATTATA 1366x768), and the canvas in force is the REAL one",
	      dillo());
	rcp_libera(s);
}

/* 8 — ⭐ THE RE-ATTACH: the stage already has 1912x1044, the page asks 1920x1080.
 *     `SESSIONE` must grant the STAGE's, or not a pixel arrives. */
static void case8(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	palco.size_known = true;
	palco.size_w = 1912;
	palco.size_h = 1044;
	s = apri_sessione(1920, 1080, NULL, true);
	bene = session_w == 1912 && session_h == 1044 && !chiuso;
	snprintf(detto, sizeof detto, "SESSIONE grants %ux%u", session_w,
	         session_h);
	esito("8 the re-attach", bene,
	      "SESSIONE grants 1912x1044 (the stage's, §4.5), not 1920x1080",
	      detto);
	rcp_libera(s);
}

/* 9 — ⭐⭐ THE STAGE GOES ITS OWN WAY — and here the first draft got the
 *      SEVERITY wrong: it adopted the stage's size and sent a `TELA` nobody had
 *      asked for.  ⛔ §6.2 says the client holds back a never-announced size
 *      **only while it has an unanswered `ADATTA_TELA`**: without one, it is
 *      `ERRORE_PROTOCOLLO` — and the frame, which travels on a stream of its
 *      own, arrives before the `TELA` half of the time.  ⇒ The server would have
 *      made a session close in which nobody had made a mistake.
 *
 *      ⇒ EXPECTED NOW: **no `TELA`, ever**, and the stage CALLED BACK to the
 *      canvas in force with a growing wait. */
static void case9(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	int primi;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	/* the stage says it is at 1280x720 without anybody having asked */
	rcp_tela_dal_palco(s, 0, 0, 1280, 720, orologio);
	raccogli();
	primi = after_birth();
	bene = canvas_count == 0 && primi == 1 && palco.requested_w == 1920
	    && palco.requested_h == 1080;
	if (bene) {
		/* it insists: and the call-back repeats, but not at every message */
		rcp_tela_dal_palco(s, 0, 0, 1280, 720, orologio);
		raccogli();
		bene = canvas_count == 0 && after_birth() == 1;
	}
	if (bene) {
		orologio += RCP_TELA_RICHIAMO_MS + 1;
		rcp_tela_dal_palco(s, 0, 0, 1280, 720, orologio);
		raccogli();
		rcp_canvas_in_effect(s, &l, &a);
		bene = canvas_count == 0 && after_birth() == 2 && l == 1920
		    && a == 1080 && !chiuso;
	}
	esito("9 the stage goes its own way", bene,
	      "ZERO TELA (an unrequested one would make the client close), the stage "
	      "called back to 1920x1080 with the growing wait",
	      dillo());
	rcp_libera(s);
}

/* 10 — the client's decoder ceiling (§4.5): `ADATTA_TELA` beyond
 *      `video.misura_massima` is REDUCED in proportion, as in `ATTACCA`. */
static void case10(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	/* ⚠ The ceiling is 2560x1440 and not 1920x1080 on purpose: with the latter
	 *   the reduction would give **exactly the canvas in force**, and the case
	 *   would end up in the «the size that is already there» branch — which is
	 *   right, but does not test the reduction.  (The first draft of this case
	 *   fell for it: the expectation was wrong, not the code.) */
	s = apri_sessione(1920, 1080, "2560x1440", true);
	/* the hi-dpi client asks for the size of its window in PHYSICAL pixels */
	send_fit(s, 3840, 2160);
	bene = after_birth() == 1 && palco.requested_w == 2560
	    && palco.requested_h == 1440;
	if (bene) {
		palco_consegna(s, orologio);
		rcp_canvas_in_effect(s, &l, &a);
		bene = canvas_count == 1 && last_canvas.esito == 1 && l == 2560
		    && a == 1440 && !chiuso;
	}
	esito("10 beyond the client's ceiling", bene,
	      "reduced to 2560x1440 (proportions kept) and granted, NEVER 3840x2160",
	      dillo());
	rcp_libera(s);
}

/* 11 — no hook (the host has no stage): `COMPOSITORE_INCAPACE`, which is the
 *      true answer and does not close the session (§7.1). */
static void case11(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, false);
	send_fit(s, 1600, 900);
	bene = canvas_count == 1 && last_canvas.esito == 2 && last_canvas.motivo == 1
	    && last_canvas.l == 1920 && last_canvas.a == 1080 && !chiuso;
	esito("11 host without a stage", bene,
	      "ONE TELA(RIFIUTATA, COMPOSITORE_INCAPACE), session alive", dillo());
	rcp_libera(s);
}

/* 12 — the request that does not leave: `NON_ORA` at once, and nothing hangs. */
static void case12(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	palco.accetta = false;
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	bene = canvas_count == 1 && last_canvas.esito == 2 && last_canvas.motivo == 3
	    && last_canvas.l == 1920 && last_canvas.a == 1080 && !chiuso;
	esito("12 the request does not leave", bene,
	      "ONE TELA(RIFIUTATA, NON_ORA) at once", dillo());
	rcp_libera(s);
}

/* 13 — ⛔ THE OLD FRAME that arrives while a request is in flight: the
 *      stage is still delivering the previous size.  It must NOT close the
 *      request, or the client would receive `TELA(ADATTATA, the old size)`
 *      as the answer to a request that was about to succeed. */
static void case13(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* the stage still states the previous size: it is renegotiating */
	rcp_tela_dal_palco(s, 0, 0, 1920, 1080, orologio);
	raccogli();
	bene = canvas_count == 0;
	if (bene) {
		palco_consegna(s, orologio);
		rcp_canvas_in_effect(s, &l, &a);
		bene = canvas_count == 1 && last_canvas.l == 1600
		    && last_canvas.a == 900 && l == 1600 && a == 900;
	}
	esito("13 the old frame in flight", bene,
	      "the OLD size does not close the request; then TELA(1600x900)",
	      dillo());
	rcp_libera(s);
}

/* 14 — ⭐⭐ TWO CHAINED REQUESTS, and the answer to the FIRST arriving later:
 *      it is the gesture of someone dragging the edge of the window.  ⛔ The first
 *      draft took the frame of the first request for the answer to the
 *      second — and the desktop settled on the wrong size **with the message
 *      counts in order**, that is without anything saying so. */
static void case14(void)
{
	rcp_sessione *s;
	uint32_t l = 0, a = 0;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);      /* first */
	send_fit(s, 1280, 720);      /* second: NON_ORA to the first */
	bene = canvas_count == 1 && last_canvas.esito == 2 && last_canvas.motivo == 3;
	if (bene) {
		/* ⛔ the answer to the FIRST request arrives, late */
		stage_replies(s, 1600, 900, orologio);
		rcp_canvas_in_effect(s, &l, &a);
		bene = canvas_count == 0 && l == 1920 && a == 1080;
	}
	if (bene) {
		/* and then the one to the second, which is the only one that counts */
		stage_replies(s, 1280, 720, orologio);
		rcp_canvas_in_effect(s, &l, &a);
		bene = canvas_count == 1 && last_canvas.esito == 1
		    && last_canvas.l == 1280 && last_canvas.a == 720 && l == 1280
		    && a == 720 && !chiuso;
	}
	esito("14 two chained requests", bene,
	      "the answer to the FIRST does not close the SECOND: the canvas ends at "
	      "1280x720, the one the user asked for last",
	      dillo());
	rcp_libera(s);
}

/* 15 — ⭐ the stage says «I didn't make it»: `NON_ORA` AT ONCE, without waiting
 *      the three seconds of the deadline for news that is already there. */
static void case15(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	bene = canvas_count == 0;
	if (bene) {
		stage_gives_up(s, orologio);
		bene = canvas_count == 1 && last_canvas.esito == 2
		    && last_canvas.motivo == 3 && last_canvas.l == 1920
		    && last_canvas.a == 1080 && !chiuso;
	}
	esito("15 the stage gives up", bene,
	      "ONE TELA(RIFIUTATA, NON_ORA) at once, not after the deadline", dillo());
	rcp_libera(s);
}

/* 16 — ⭐ the stage answers «I already have that size»: the request is closed
 *      with `TELA(ADATTATA)` without waiting for a frame that will not come,
 *      because whoever is watching already has the frames of that size in front of them. */
static void case16(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* the stage really changes */
	palco_consegna(s, orologio);
	bene = canvas_count == 1 && last_canvas.l == 1600;
	if (bene) {
		/* now the client asks again for a size the stage ALREADY HAS: the child
		 * answers at once, without any new frame */
		send_fit(s, 1280, 720);
		bene = canvas_count == 0;
	}
	if (bene) {
		rcp_tela_dal_palco(s, 1280, 720, 1280, 720, orologio);
		raccogli();
		bene = canvas_count == 1 && last_canvas.esito == 1
		    && last_canvas.l == 1280 && last_canvas.a == 720 && !chiuso;
	}
	esito("16 the stage already had it", bene,
	      "TELA(ADATTATA 1280x720) at the stage's answer, without deadline",
	      dillo());
	rcp_libera(s);
}

/* 17 — ⛔ the limits of §4.5 PER SIDE: 1600x230 is out (the height), and must be
 *      refused — or at the re-attach `ATTACCA` would refuse a canvas that this
 *      same server had granted. */
static void case17(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1920, 1080, NULL, true);
	send_fit(s, 1600, 230);
	bene = canvas_count == 1 && last_canvas.esito == 2 && last_canvas.motivo == 2
	    && last_canvas.l == 1920 && last_canvas.a == 1080
	    && after_birth() == 0 && !chiuso;
	esito("17 below the minimum of §4.5", bene,
	      "ONE TELA(RIFIUTATA, MISURA_FUORI_LIMITI): 230 < 240", dillo());
	rcp_libera(s);
}

/* 18 — ⛔⛔ THE PING-PONG BETWEEN TWO SESSIONS OF THE SAME USER, and it is not a
 *      textbook case: it is the defect the user saw on the morning of 15 Aug
 *      2026, and told me like this — «on Android the mouse no longer takes the
 *      clicks».
 *
 *      `[M]` from the log of his real session:
 *        05:10  the laptop attaches, canvas 2544x926
 *        05:12  silent for thirty seconds ⇒ DETACHED for silence, leaves the slot —
 *               ⛔ but the session stays ALIVE, with the video channel on
 *        05:14  the phone attaches, canvas 2560x926
 *        05:14  **seventeen requests per second**, forever: the laptop
 *               asks 2544, the phone 2560, the laptop 2544 …
 *      ⇒ every round restarts the stream, Mutter recreates the `libei` devices
 *        (`[M]` 640 replacements) and the input region never agrees with the
 *        canvas ⇒ **the clicks land elsewhere**.
 *
 *      ⇒ EXPECTED: whoever does NOT have the slot asks nothing of the stage, and
 *      an `ADATTA_TELA` of theirs is answered with `NON_ORA` (I2: the stage is
 *      commanded by whoever is attached). */
static void case18(void)
{
	rcp_sessione *uno, *due;
	int richieste_prima;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();

	/* The laptop: attaches and takes the canvas. */
	next_provenance = "10.0.0.9:5000";
	uno = apri_sessione(1920, 1080, NULL, true);
	send_fit(uno, 1600, 900);
	palco_consegna(uno, orologio);

	/* Silent for thirty seconds: §5.3 takes its slot away, the session stays alive. */
	orologio += 31000;
	rcp_tempo(uno, orologio);
	raccogli();
	bene = strcmp(rcp_stato_nome(uno), "staccata-per-silenzio") == 0;

	/* The phone attaches and TAKES the slot, with a window of another
	 * size.  ⚠ `apri_sessione` resets the clock: it is put back where it was, or
	 * the laptop's silence would trigger again. */
	if (bene) {
		uint64_t quando = orologio;
		next_provenance = "10.0.0.24:34583";
		due = apri_sessione(1920, 1080, NULL, true);
		orologio = quando;
		send_fit(due, 1280, 720);
		palco_consegna(due, orologio);
		richieste_prima = palco.how_many_requests;

		/* The stage is now at 1280x720, and its frames also reach the
		 * LAPTOP, which still has 1600x900 as the canvas in force. */
		rcp_tela_dal_palco(uno, 0, 0, 1280, 720, orologio);
		rcp_tela_dal_palco(uno, 0, 0, 1280, 720, orologio);
		raccogli();
		bene = palco.how_many_requests == richieste_prima && canvas_count == 0;

		/* ⭐ And if the laptop speaks again, it is not answered «not now»:
		 *    it is given FAREWELL with §8.2 `0x0F` — «you already have an active
		 *    session elsewhere», and this time it is true.  ⚠ `torna_a_parlare()`
		 *    does it at the top of `rcp_ricevi()`, before the message gets
		 *    anywhere: that is why a guard on the slot in `T_FIT_CANVAS` would
		 *    be dead code.  ⛔ What matters is that the stage is not
		 *    touched. */
		if (bene) {
			chiuso = false;
			send_fit(uno, 1024, 768);
			bene = palco.how_many_requests == richieste_prima && chiuso
			    && close_reason == 0x0F;
		}
		/* ⭐ And the phone, which does have the slot, commands all right. */
		if (bene) {
			chiuso = false;
			send_fit(due, 1152, 648);
			bene = palco.how_many_requests == richieste_prima + 1
			    && palco.requested_w == 1152 && !chiuso;
		}
		rcp_libera(due);
	}
	esito("18 two sessions, one stage only", bene,
	      "whoever lacks the slot does NOT command (zero requests to the stage, and "
	      "if it speaks again it is 0x0F); whoever has it does",
	      dillo());
	rcp_libera(uno);
	next_provenance = "10.0.0.9:5000";
}

/* 19 — ⭐⭐ THE CANVAS IS DECLARED AT BIRTH, and this case exists because without
 *      it the bench would be BLIND precisely where it was red for a day.
 *
 *      `477d708`, 15 Aug 2026: the session that attaches tells the stage at
 *      once at what size to be born, instead of letting it be born at a size of
 *      its own and changing it afterwards.  ⭐ It is the cure that removed
 *      **seventeen seconds** of tail from the access times — «the change is a
 *      race», and the race was lost against a still scene.
 *
 * ⛔ The other cases now count with `after_birth()`, that is they SKIP
 *    this request.  ⇒ If it disappeared, they would all stay green and the tail
 *    would come back silently.  This case is the only one that would notice.
 *
 *    EXPECTED: the attach leaves **one** request to the stage, and it is at the
 *    size the client asked in `ATTACCA` — not a fallback one, not zero. */
static void case19(void)
{
	rcp_sessione *s;
	bool bene;

	rcp_azzera_registro_sessioni();
	reset_stage();
	s = apri_sessione(1600, 900, NULL, true);
	bene = birth_requests == 1 && palco.requested_w == 1600
	    && palco.requested_h == 900 && canvas_count == 0 && !chiuso;
	esito("19 the canvas is declared at birth", bene,
	      "ONE request to the stage already with ATTACCA, at 1600x900 (§4.5: it is "
	      "born that way instead of having to change it — those are the 17 s of tail)",
	      dillo());
	rcp_libera(s);
}

int main(int argc, char **argv)
{
	int solo = argc > 1 ? atoi(argv[1]) : 0;
	void (*casi[])(void) = { case1,  case2,  case3,  case4,  case5,  case6,
		                     case7,  case8,  case9,  case10, case11, case12,
		                     case13, case14, case15, case16, case17,
		                     case18, case19 };
	const int quanti = (int)(sizeof casi / sizeof casi[0]);

	parlantina = getenv("PARLANTINA") != NULL;
	printf("\n== 04-b31: the changing canvas (RCP.md §7.1, §6.2) ==\n\n");
	for (int i = 0; i < quanti; i++) {
		if (solo && solo != i + 1)
			continue;
		casi[i]();
	}
	printf("\n  passed %d, failed %d\n\n", passati, falliti);
	return falliti ? 1 : 0;
}
