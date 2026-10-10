/*
 * webtransport.c — see webtransport.h.
 *
 * ⭐ Ported from `banchi/01-b2-ngtcp2-wt-innesta.py`, which kept it as a `git
 *    diff` on the ngtcp2 tree.  The decisions and cures the graft's comments
 *    documented are in here **with their reason**: they are defects already
 *    paid for, and rewriting them without the reason means paying for them again.
 */
#include "webtransport.h"
/* ⭐ §5-bis.7: the question «does this layout exist?» is answered by `tastiera.c`. */
#include "tastiera.h"

/* ⛔ Only for the `FIGLI_INPUT_*`: the action numbers live in one place only
 *    (`figlio.h`), or in two weeks they will be three places with three values. */
#include "figlio.h"

#include "aiutante.h"
#include "audio.h"
#include "rcp.h"
#include "registro.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool rcp_autentica_da(const char *utente, const char *parola,
                      const char *rhost);
bool rcp_rhost_da_provenienza(const char *provenienza, char *fuori, size_t cap);

/* ------------------------------------------------------------------------ */
/* The two things C does not bring as dowry: a byte vector and a list.       */

typedef struct {
	uint8_t *d;
	size_t n, cap;
} bytes;

static bool bytes_aggiungi(bytes *b, const uint8_t *d, size_t n)
{
	if (n == 0)
		return true;
	if (b->n + n > b->cap) {
		size_t c = b->cap ? b->cap * 2 : 64;
		uint8_t *nuovo;
		while (c < b->n + n)
			c *= 2;
		nuovo = realloc(b->d, c);
		if (!nuovo)
			return false;
		b->d = nuovo;
		b->cap = c;
	}
	memcpy(b->d + b->n, d, n);
	b->n += n;
	return true;
}

static void bytes_togli_testa(bytes *b, size_t n)
{
	if (n >= b->n) {
		b->n = 0;
		return;
	}
	memmove(b->d, b->d + n, b->n - n);
	b->n -= n;
}

static void bytes_libera(bytes *b)
{
	free(b->d);
	b->d = NULL;
	b->n = b->cap = 0;
}

/* ------------------------------------------------------------------------ */

/* How a client stream is classified. */
enum genere {
	G_INCERTO, /* not yet known what it is: the first bytes are missing */
	G_WT,      /* it is a bidirectional WebTransport stream */
	G_NONWT,   /* it is not: it belongs to nghttp3 */
	G_UNI_OK,  /* unidirectional WebTransport, lawful channel but not served */
	G_UNI_KO,  /* unidirectional WebTransport, violation already judged */
	G_UNI_INPUT, /* ⭐ the INPUT channel (0x01), served since phase 4: its
	              *    bytes go to `rcp_ricevi_input()`.  ⛔ It is kept apart from
	              *    `G_UNI_OK` on purpose — inside that verdict the bytes are
	              *    counted against the credit and DISCARDED, and that is exactly
	              *    what input did until 14 Aug 2026. */
	G_UNI_APPUNTI, /* ⭐ the CLIPBOARD channel (0x02), served since phase 7: its
	                *    bytes go to `rcp_ricevi_appunti()`.  ⛔ It is kept apart from
	                *    `G_UNI_INPUT` for a reason that is not tidiness: here
	                *    streams are **one per transfer** (§2.5), so more than one
	                *    is alive at once and the END of each one is a fact —
	                *    while the input stream is a single one and stays
	                *    open. */
};

typedef struct {
	int64_t id;
	enum genere genere;
	bytes pref;
} stream_giudizio;

typedef struct {
	int64_t id;
	bytes dati;
	size_t off;
	bool fin;
	/* ⛔⭐ PHASE 3 — «DEAD» INSTEAD OF «REMOVED FROM THE HEAD».
	 *
	 *     Until phase 2 **only the head** was removed from this queue, and it
	 *     was enough: a single frame was sent per session.  ⛔ With one
	 *     stream per frame the head is no longer the only element that can
	 *     finish — an element **in the middle** is chosen when the ones ahead
	 *     belong to a blocked stream — and removing from the middle of an array
	 *     would mean moving all the rest at every frame.
	 *
	 *     ⇒ Whoever finishes is marked dead; `testa` slides over the dead at the head. */
	bool morto;
	/* ⛔⛔⭐ PHASE 9 — «HANDED OVER» IS NOT «CONFIRMED», and the difference between
	 *      the two words is the crash of 23 Aug 2026 (`fasi/09-la-qualita-e-la-degradazione.md` §4).
	 *
	 *      `ngtcp2_conn_writev_stream()` **does not copy the bytes**: it keeps
	 *      OUR pointer in the list of packets in flight, and when a packet is
	 *      declared lost it **rereads** it to retransmit.  The contract says
	 *      so in one line
	 *      (`ngtcp2.h`, `ngtcp2_conn_writev_stream`):
	 *
	 *        «The caller must keep the portion of data covered by |*pdatalen|
	 *         bytes **in tact** until `acked_stream_data_offset` indicates that
	 *         they are acknowledged by a remote endpoint **or the stream is
	 *         closed**.»
	 *
	 * ⛔ Here memory was freed at SERIALISATION — `off >= dati.n` ⇒ `free()` —
	 *    which is exactly the instant the contract forbids.  `[M]` 23 Aug 2026,
	 *    08:28:09: `SEGV`, `error 4`, inside `__memmove_avx_unaligned_erms`,
	 *    source `0x7f148e056fc2` — a frame of 525 298 bytes, the first block of
	 *    the run big enough to be served with `mmap`, hence the first whose
	 *    `free()` really **unmapped** the region.
	 *
	 * ⚠ And the other 45 004 frames of the same run had the SAME defect
	 *   without making noise: below 128 KiB glibc serves from the heap, the
	 *   reread succeeds and ngtcp2 retransmits **garbage bytes instead of
	 *   pixels**, silently and without an error.  ⛔ The crash was the rare
	 *   symptom; the mute corruption was the real defect.
	 *
	 * ⭐ Hence the two states, which used to be one:
	 *
	 *      `consegnato` — all the bytes are inside ngtcp2.  It is no longer
	 *                     chosen for writing (`coda_scegli()`), it no longer
	 *                     counts as «to send» (`coda_vuota()`,
	 *                     `byte_in_coda`), ⛔ **but the bytes remain ours and
	 *                     remain allocated**;
	 *      `morto`      — the bytes are freed.  One gets there ONLY from an
	 *                     acknowledgement covering them (`coda_conferma()`), from
	 *                     the stream's closure (`wt_stream_chiuso()`) or from its
	 *                     reset (`coda_butta_stream()`, always next to a
	 *                     `RESET_STREAM`).  They are the two conditions of the
	 *                     contract, and there is no third one.
	 *
	 * ⚠ `confermati` counts the bytes of THIS element already acknowledged: acks
	 *   arrive in pieces — a half-megabyte frame is ~370 packets — and an
	 *   element is freed only when the count covers `dati.n`. */
	bool consegnato;
	size_t confermati;
} uscita;

/* ⛔⭐ PHASE 3 — THE BLOCKED STREAMS OF **THIS PASS**, AND WHY IT IS NO LONGER
 *     A `bool`.
 *
 * Until phase 2 here there was `bool coda_bloccata`: at the first
 * `NGTCP2_ERR_STREAM_DATA_BLOCKED` **the whole queue** stopped for the pass.
 * ⛔ With one stream per frame that `bool` cancels exactly the benefit
 *    `RCP.md` §5.1 buys: «streams are independent, so a late frame does not
 *    touch the following ones» is true at the QUIC level and became **false
 *    one floor up**, inside our own house — a slow frame at the head blocked
 *    all the ones after it, that is the head-of-line blocking §5.1 exists to
 *    remove, redone by hand.
 *
 * ⇒ **The stream** is blocked, not the queue.  The order WITHIN a stream
 *   stays as it is: the first eligible element in insertion order is always
 *   chosen, so the first of an unblocked stream is its
 *   oldest.
 *
 * ⚠ And the cap is declared: beyond `WT_BLOCCATI_MAX` blocked streams in the
 *   same pass we stop as before and **it is written**.  A cap that is
 *   exceeded silently is a cap that is not there. */
#define WT_BLOCCATI_MAX 64

/* ⛔ How many frames can be in flight together on a session.  ⚠ The
 *    number is not arbitrary: `RCP.md` §2.3 declares **16** unidirectional
 *    streams available to RCP as normative, and input takes one.  Beyond that
 *    number the credit is exhausted anyway, and this table is not the cap that
 *    bites. */
#define WT_INVOLO_MAX 32

/* ⛔⭐ THE AUDIO DATAGRAM — phase 7, and the two numbers have a measurement behind them.
 *
 * `WT_DGRAM_BYTE` — how long the payload of one of our datagrams can be.
 *    The biggest RCP/1 provides for is **PCM**: `RCP.md` §5.3 fixes it at
 *    5 ms = 480 samples = 960 bytes, plus the 12 of the §6.3 header =
 *    **972**, plus the RFC 9297 prefix (at most 8) = **980**.
 *    ⚠ `[M]` 17 Aug 2026, probe `banchi/07-b40`: the datagram browsers
 *    really accept against our server is **1024 bytes on Chrome 151**
 *    (fixed) and **1024 → 1214 on Firefox 140esr**.  ⇒ PCM fits by **52
 *    bytes** on the tightest engine, and this cap is not a round
 *    number picked at random: it is that measured 1024.
 *
 * `WT_DGRAM_MAX` — how many blocks can wait.  ⛔ It is not a memory for
 *    smoothness: it is **the space between two write passes**.  Eight blocks
 *    are 40 ms of PCM and 160 of Opus; beyond that, the oldest is no use to
 *    anyone and §6.3 says it is thrown away.
 *
 * ⛔⭐ AND THIS NUMBER WAS CHANGED TO 32 AND PUT BACK TO 8 IN THE SAME RUN,
 *     because the diagnosis that had raised it was WRONG — 17 Aug 2026.
 *
 *     The first run gave **402 blocks out of 600** in 3 s (yield 67 %), with
 *     zero blocks lost.  I read «the queue is the rate cap» and raised it:
 *     at 32 the yield went to **80 %** — that is it improved, which seemed
 *     to confirm.  ⛔ It confirmed nothing: 2.01 s out of 3 and 4.01 out of 5
 *     are **(T − 1)**, not a fraction.  The third run decided it: **9.01 s out
 *     of 10**.  ⇒ It was not a yield: it was **one fixed second at the start**,
 *     and the queue had nothing to do with it.
 *
 * ⚠ The lesson is about method: two points lay on a straight line by chance,
 *   and «the number improved» almost bought a wrong change.  The third
 *   point cost thirty seconds.  ⭐ The number went back to 8 because
 *   `[M]` at 8 the lost blocks were already **zero**: it was enough, and a
 *   higher value would have stayed here without a reason. */
#define WT_DGRAM_BYTE 1024
#define WT_DGRAM_MAX 8

/* ⛔⛔⛔ A BLOCK'S CAP IS ITS AGE, AND UNTIL 24 AUG 2026 IT WAS NOT.
 *
 *      Here there was `WT_DGRAM_RIMANDI_MAX 4096`, and next to it a comment saying
 *      *«how many PASSES in a row **the block at the head** has been deferred»*.
 *      ⛔ It was not true, and not because of an imprecise word: the counter
 *      (`dgram_rimandi`) lived on **`struct wt`**, that is on the CONNECTION.
 *      It went up at every refused pass and went back to zero only on a success —
 *      and meanwhile the head had been replaced, because `dgram_accoda()`
 *      overtakes the oldest when the ring is full **without touching that
 *      counter**.  ⇒ It did not measure the block's age: it measured **how long
 *      the connection has sent nothing**.
 *
 * ⛔⛔ AND THE DIFFERENCE WAS NOT ACADEMIC: that number had no STABLE unit.
 *
 *      `[M]` 24 Aug 2026, bench NR12, port 7981, 25 s per run:
 *
 *        healthy line (smooth `lo`, PCM):  0 deferrals          in 26 s
 *        `casa-cattiva` (40±20 ms, 2 %): **2 201 582 deferrals** in 26.2 s
 *
 *      ⇒ **84 700 write passes per second.**  A «pass» is a call of
 *      `scrivi_connessione()` (`trasporto.c:445`), and the event loop
 *      repeats it as long as there is something to write: under pressure it
 *      runs four hundred times more often than at rest.  ⇒ The same `4096` was
 *      worth **~48 ms** on the bad network and **tens of seconds** on the healthy line.
 *      ⚠ A cap that changes meaning with the load is not a cap: it is a
 *      number someone will read as a policy without knowing which one.
 *
 * ⛔⛔ AND IT REALLY WAS THE POLICY, against what the comment declared
 *      (*«stays high only so as not to leave a bottomless loop»*).  `[M]`
 *      same run on `casa-cattiva`: **2 258 blocks dropped by this cap**
 *      against **9 dropped by the full queue** — 99.6 % of the discards came
 *      from here.  ⚠ And that is why the first refusal observed happened **with
 *      the window open** (`cwnd_left` = 7 424, and the line itself said «it is
 *      NOT congestion»): it was not the network deciding, it was the rev counter.
 *
 * ⛔⛔⛔ AND THE FIRST CURE I WROTE WAS THE WRONG ONE — it is written down
 *       because it is the part that teaches something, and because without
 *       the measurement I would have shipped it.
 *
 *       The obvious road was to carry the count **on the element**: stamp each
 *       block when it enters the queue and drop it when its AGE passes a
 *       cap.  It is what the old comment promised.  ⛔ Tried, and the
 *       measurement refused it twice — `[M]` 24 Aug 2026, `casa-cattiva`
 *       (40±20 ms, 2 %), PCM, four paired runs on the same `netem`:
 *
 *         cap on age        sent     dropped(queue) refused    kbit/s  useful/wire
 *         ---------------   -------  -------------  ---------  ------  ----------
 *         250 ms              4 169        845           0     1 847     35 %
 *          50 ms              4 194        819           3     1 838     35 %
 *         (the product)       3 203         14       1 781     1 415     42 %
 *
 *       ⇒ **At 50 ms it fires no more than at 250**, and it is the QUEUE that
 *       does all the work (14 → 830 discards).  ⭐ The reason is a sum the
 *       file already stated and that I had not believed: the queue holds EIGHT
 *       blocks, and eight PCM blocks are **40 ms**.  ⇒ The head can almost
 *       never be older than 40 ms, so a cap on AGE above 40 ms is a cap
 *       that touches nothing.
 *       ⚠ And the price of that «touches nothing» shows: 30 % more bytes
 *         on the wire (1 415 → 1 840 kbit/s), stolen from the same window as
 *         the video (⇒ «DATAGRAMS BEFORE STREAMS» in `wt_scrivi()`), to
 *         carry 11 % more useful blocks (1 290 → 1 430) — because the
 *         rest arrives **already old** and the client drops it (`scartati
 *         vecchi` 1 800 → 2 650).
 *
 * ⭐⭐ THE RIGHT CURE IS THE OTHER ONE: **keep the quantity, change its UNIT**.
 *
 *      What the code governs here is not the age of a block: it is **how long
 *      the connection has been unable to put a datagram in a packet**.  It is
 *      a sensible quantity — if NOTHING has left in N ms, the oldest in the
 *      queue will not leave in time (§6.3) — and it is exactly what the
 *      code did.  ⇒ The defect was not the policy: it was that the policy
 *      had a false name and a unit that moved.
 *      ⇒ The name says the thing (`dgram_zitto_da`, «since when I am mute») and
 *        the cap is in MILLISECONDS.
 *
 * ⛔⛔⭐ AND `4096` DOES NOT CONVERT TO MILLISECONDS WITH A DIVISION — I
 *       tried and the measurement proved me wrong a second time.  The reason is
 *       that the number was **self-referential**: how many passes are made per
 *       second depends on how often we DROP, and how often we drop
 *       depends on the cap.  `[M]` same runs: with the product 2.1 million
 *       deferrals in 25 s, with the cap at 50 ms **20 million** — ten times
 *       as many, because no longer dropping the loop spins idle.  ⇒ 4096 was
 *       not worth «46 ms»: it was worth no fixed time at all.
 *
 * ⭐⭐⭐ THE VALUE WAS TUNED ON THE MEASUREMENT, and green is «indistinguishable
 *      from the product».  `[M]` 24 Aug 2026, `casa-cattiva`, PCM, paired runs
 *      on the same `netem`, two runs for the product to get the SPREAD:
 *
 *        cap          sent     drop.(queue) refus.   kbit/s  useful useful/wire
 *        -----------  -------  -----------  -------  ------  -----  ----------
 *        product       3 242        14       1 753   1 433   1 273    0.401
 *        product       2 912        16       2 084   1 312   1 223    0.432
 *        10 ms         2 947        16       2 039   1 286   1 246    0.435
 *         5 ms         2 999        15       1 995   1 327   1 246    0.424
 *        50 ms         3 955       797         263   1 743   1 390    0.360
 *
 *      ⇒ **10 ms is within the product's spread on every column**, 5 ms
 *      too, and at 50 ms the cap has already stopped biting.  ⇒ The cure changes
 *      what the number MEANS, not what the product DOES — and it is
 *      exactly what was wanted.
 *
 * ⭐ And 10 ms also has a reason that is not fitting: it is **two PCM
 *    blocks** (5 ms each).  If nothing has left in the time of two blocks, the
 *    oldest will not make it.
 *
 * ⚠ AND THE TUNING IS NOT MINE.  This number reproduces the measured product,
 *   it does not improve it.  `[M]` the table says loosening it buys 8-11 % more
 *   useful blocks at the price of 20-30 % of bandwidth taken from video: it is a
 *   choice with two numbers next to it, and whoever decides the product makes it — not me here.
 *
 * ⭐ AND THE BLOCK'S AGE IS NOT THROWN AWAY: `dgram[].nato` stays, and ends up in
 *    the discard's log line.  ⛔ It decides nothing — `zitto` decides —
 *    but it is the quantity the old comment PROMISED and nobody had ever
 *    read: now whoever reads the log sees both, «I have been mute for N ms» and
 *    «the block I drop is M old», and can notice if one day they diverge.
 *
 * ⚠ And the congestion guard stays OUT of here: `cwnd_left` high or low
 *   does not change what is best to do with a block that has not left yet.
 *   It was a condition that dropped the block **precisely when the window was
 *   narrow**, that is when waiting was most needed. */
#define WT_DGRAM_ZITTO_MAX_MS 10

/* ⛔ The test tone (`--audio-prova`), `0` = off.  It sits at the top and not
 *    next to its function because `wt_battito_ns()` reads it too, and that
 *    comes much earlier — see the clock box there. */
static uint32_t audio_prova_hz;

/* ⭐ The hook towards the child, for the same reason: `audio_regola()` calls it,
 *    and it comes much earlier than `wt_audio_gancio()`. */
static wt_audio_richiesta gancio_audio;
static void *gancio_audio_ctx;

/* HTTP/3 requests: only one thing is needed from them here — telling the
 * WebTransport extended CONNECT from everything else. */
typedef struct {
	int64_t id;
	char metodo[16];
	char protocollo[24];
	char uri[192];
	bool usato;
} richiesta;

/* ⭐ How many datagram losses are remembered in order to recognise the
 *    FALSE ones — that is reordering.  See the field `dgram_anello` further below: it
 *    is short on purpose, and the reason is there. */
#define WT_DGRAM_ANELLO 512

struct wt {
	ngtcp2_conn *conn;
	/* ⭐ D-001: this user's stage already existed at PAM's verdict ⇒
	 *    `SESSIONE` says `2 = RIPRESA`.  `wt_verdetto()` writes it. */
	bool ripresa;
	ngtcp2_ccerr *ultimo_errore;
	nghttp3_conn *h3;
	char provenienza[80];
	/* ⭐ THE PAM HELPER — `DECISIONI.md` §1.10.  ⛔ This layer does not own
	 *    it: there is a single one for the whole server, started by `main.c` before
	 *    any connection exists, and it comes through here because RCP's
	 *    `chiedi_verifica` hook is the only place that uses it.
	 * ⚠ NULL is allowed and means «synchronous check»: it is the declared
	 *   fallback, and it is the fault that `banchi/02-pam-*` injects. */
	aiutante *aiuto;

	/* HTTP/3's control stream: it is needed to recognise it when writing,
	 * which is the only instant in which one can tell the browser we speak
	 * WebTransport */
	int64_t ctrl_id;
	bool impostazioni_scritte;
	bool guasto;
	uint8_t impbuf[256];
	size_t impbuf_len;
	/* ⛔ How many bytes of the rewritten SETTINGS have ALREADY GONE OUT, and how
	 *    many bytes of nghttp3 that buffer replaces.  They are needed because a
	 *    PARTIAL write is a normal outcome of `ngtcp2_conn_writev_stream` — not
	 *    a fault — and in the graft, before the cure, it killed the
	 *    connection: now one resumes from the point reached,
	 *    as has always been done for the output queue. */
	size_t impbuf_off, impbuf_orig;

	stream_giudizio *giudizi;
	size_t ngiudizi, capgiudizi;

	uscita *coda;
	size_t ncoda, capcoda, testa;
	/* ⛔ The streams blocked for THIS write pass: ngtcp2 said
	 *    STREAM_DATA_BLOCKED, and retrying within the same pass would be a
	 *    loop that does not advance.  ⚠ They were a `bool` until phase 2 — see the
	 *    box of `WT_BLOCCATI_MAX`: that `bool` redid by hand the head-of-line
	 *    blocking that `RCP.md` §5.1 exists to remove. */
	int64_t bloccati[WT_BLOCCATI_MAX];
	size_t nbloccati;
	/* ⛔ The cap has been touched and the queue really stops: it is kept in order
	 *    to write it ONCE instead of at every pass. */
	bool troppi_bloccati;

	int64_t sessione; /* the stream of the extended CONNECT: it IS the session */

	/* the CONNECT bytes that do not yet make up a whole capsule */
	bytes capsbuf;
	/* ⛔ How many bytes of a capsule already judged TOO BIG remain to be
	 *    thrown away as they pass. */
	uint64_t capsalta;

	richiesta *richieste;
	size_t nrichieste, caprichieste;

	/* ═══ RCP over WebTransport ═════════════════════════════════════════ */
	struct rcp_sessione *rcp;
	int64_t rcp_stream;

	/* ═══ THIS SESSION'S VIDEO — phase 3 ═══════════════════════════════ */
	/*
	 * ⛔⭐ HERE THERE WAS `bool video_fatto`, AND IT IS THE BRAKE OF PHASE 2.
	 *
	 *     The comment said: «it is a `bool` and not a counter because phase
	 *     2 delivers ONE STILL IMAGE: the frame loop belongs to phase
	 *     3».  ⇒ Now it is phase 3, and the brake comes off: in its place
	 *     there is the state of the **channel**, which is switched on once and stays on,
	 *     and the frame counters, which grow.
	 *
	 * ⚠ The reason the `bool` existed remains valid and must be honoured all
	 *   the same: without a backstop, `video_regola()` would rewrite the same log
	 *   line at every heartbeat of every session, and a log that repeats itself
	 *   is no longer read.  ⇒ `video_detto` is that backstop, and it is only for the
	 *   log: it no longer stops frames.
	 */
	/* This session's video channel is on: `SESSIONE` has left, the
	 * codec is negotiated, and the child has been asked to capture. */
	bool video_acceso;
	uint8_t video_codec;
	/* ⛔⭐⭐ THE STAGE HAS ALREADY BEEN TOLD TO STOP — and it is NOT the opposite
	 *      of `video_acceso`: they are two different facts, and one field for two
	 *      facts switches one of them off (it is the lesson written on `tela_detta_*`
	 *      twenty lines below, and here it holds identically).
	 *
	 *      `video_acceso`  = «this session HAS a video channel».  It stays true
	 *                        until the end, because it is what lets the
	 *                        FINAL COUNT out in `wt_libera()`: switching it off at the
	 *                        farewell would mean losing that line.
	 *      `video_fermo`   = «I have already asked the child to capture NO MORE».
	 *
	 * ⛔ And it goes back to `false` in `video_regola()` when a new session
	 *    restarts the loop: without that return the cure for waste
	 *    would break the REATTACH — a new session on the same
	 *    connection (a state foreseen twice in this file) would find
	 *    `video_acceso` already true, would ask the stage nothing, and
	 *    the user would be left in front of a frozen screen forever.  ⚠ It is
	 *    much worse than the waste being cured. */
	bool video_fermo;
	/* ⛔ «I have already explained why this session has no video»: once
	 *    only, and the why is in the line written then. */
	bool video_detto;
	/* ⛔ The last frame size for which «it is not the canvas in force» has already
	 *    been written.  ⚠ It is a SIZE and not a `bool` on purpose: so the backstop
	 *    rearms when the fact changes, instead of keeping quiet forever after the first
	 *    time — and it is a field of its own, because `video_detto` tells another
	 *    fact and one flag for two facts switches one of them off. */
	uint32_t tela_detta_l, tela_detta_a;
	/* ⛔⭐ HOW MANY MISMATCH ANNOUNCEMENTS HAVE BEEN WRITTEN — and it is not the same
	 *     number as the frames not sent, which is precisely the point.
	 *
	 *     `[M]` B2, 22 Aug 2026: under a fault that makes ALL frames
	 *     inadmissible, **799 discarded** and in the log **a single
	 *     announcement** — because the backstop above rearms only when the
	 *     pair (canvas in force, frame size) changes, and under that
	 *     fault it never changes.  ⇒ Whoever counted the lines read **1** and
	 *     called it «not sent»: the name promised 799.  It is shape **E2**,
	 *     and nobody had seen it **because 1 is a number that looks healthy**.
	 *
	 * ⛔ The backstop is NOT touched — 799 identical lines would make the log
	 *    unusable.  What was missing is the COUNT next to it, and they are two
	 *    distinct numbers because they count two distinct things. */
	uint32_t video_annunci_tela;
	/* When the last keyframe was requested from the child, so as not to request one at
	 * every heartbeat while the first is still on its way.  ⛔ It is not the grace
	 * of §5.2 (that one belongs to `rcp.c` and counts from the last keyframe SENT): it is the
	 * backstop of a repeated request towards the stage. */
	uint64_t chiave_chiesta_ms;
	/* ⛔⭐ THE SECOND BELT of 23 Sep 2026 (see `batti_fra()` and
	 *     `video_rifiutato_per_chiave()`): the §5.2 debt that has been on for too
	 *     long is said ONCE per episode, not 45 278 times.  It is switched off when
	 *     a keyframe leaves again. */
	bool debito_detto;
	/* ⭐ How big the last keyframe SENT was, in bytes, and the last interval
	 *    applied to it — they serve `chiave_intervallo_ms()`, and the
	 *    second exists only so as not to repeat the same log line
	 *    fifty times a second. */
	uint64_t chiave_byte, chiave_attesa_detta_ms;
	uint32_t video_diffusi, video_saltati;

	/* ⭐⭐ PHASE 9 — THE QUEUE THRESHOLD, and the three counts that make it
	 *     READABLE from the log instead of deduced.
	 *
	 * `sgombra_tenuti` — how many times a delta stayed in the queue because the
	 *    queue empties within the threshold.  It is counted **per delta**, not per
	 *    pass, because `sgombra_abbandoni` counts per delta: two numbers that
	 *    must be subtractable.
	 * `sgombra_abbandoni` — how many times the threshold was exceeded all the same
	 *    and the delta went away.
	 * ⛔ `sgombra_credito` — the deltas that did not even ENTER the queue
	 *    because §2.3 had no credit (`rcp.c:3441`, cause 4 of the debt of
	 *    §5.2).  ⚠ IT IS THE SHAPE INVISIBLE TO THE RECEIVER, and it is here for a
	 *    precise reason: this phase's cure touches **cause 3**, not
	 *    4.  If under congestion it were 4 keeping the debt on, the cure
	 *    would spin idle and the frames would all stay keyframes — with
	 *    this number next to the other two the bench knows **to whom** to attribute it;
	 *    without it it would see «the cure did not work» and that would be false.
	 *
	 * ⚠ `sgombra_sopra` is the backstop of the log lines: it is written when
	 *   the STATE changes (below→above and above→below), not thirty times a
	 *   second.  ⛔ And the startup line with the value in force is written by
	 *   `wt_sgombra_soglia()`, which `main.c` always calls: «off» and «never
	 *   fired» must not look the same. */
	uint32_t sgombra_tenuti, sgombra_abbandoni, sgombra_credito;
	bool sgombra_sopra;
	/* ⛔ 22 Sep 2026 — deltas KEPT because ahead there is a KEYFRAME still in
	 *    the queue (see `video_sgombra()`, «THE KEYFRAME SPIRAL»), and the backstop
	 *    of the line that says so once per keyframe. */
	uint32_t sgombra_dietro_chiave;
	uint32_t sgombra_chiave_detta;

	/* ⭐⭐ PHASE 9 — THE RATE REGULATOR, and its numbers.
	 *
	 * `video_ritmo_scesi` — how many frames did NOT leave because the queue
	 *    was not emptying.  ⛔ It does not go into `video_saltati`: that one counts
	 *    INADMISSIBLE frames (wrong canvas, credit exhausted, refusal by
	 *    rcp), this one counts a RATE DROP decided by us.  It is the lesson
	 *    of `video_annunci_tela` (:331-343): two numbers for two facts, or one
	 *    of the two lies with a value that looks healthy.
	 *
	 * `ritmo_giu` / `ritmo_da_ms` / `ritmo_da_n` — whether a drop episode is
	 *    in progress, since when and from what count: they serve to write TWO lines per
	 *    episode instead of one per skipped frame.  ⛔ At thirty a second
	 *    the second shape is the defect of the 30.8 GB of log.
	 *
	 * ⛔⭐ AND THE FOLLOWING FOUR DECIDE NOTHING: they are the INSTRUMENT with which
	 *     one proves that the rate does not drop on a still scene.  `LEZIONI.md` §1.9:
	 *     a counter at zero on a branch never reached proves nothing —
	 *     «empty» and «forbidden» look the same.  ⇒ We count how many times
	 *     `arretrato` was READ in each second, besides what it was worth:
	 *     zero reads means the stage delivered nothing (still
	 *     scene), and NOT «arretrato zero».  The line is written by `ritmo_ciclo()`,
	 *     which runs with the heartbeat and so comes out even when no
	 *     frames arrive at all. */
	uint32_t video_ritmo_scesi;
	bool     ritmo_giu;
	uint64_t ritmo_da_ms;
	uint32_t ritmo_da_n;
	uint32_t ritmo_letture;
	unsigned ritmo_max, ritmo_ultimo;
	uint32_t ritmo_detti_n;
	uint64_t ritmo_detto_ms;

	/* ⛔⭐⭐ PHASE 9 — THE SNAPSHOT OF THE NETWORK OF THE PREVIOUS SECOND, and it serves to
	 *      answer the only question that counts under loss: **is it the line
	 *      or is it us?**
	 *
	 *      Until now the log could count only OUR half of the
	 *      delay — `sgombra_tenuti` (we kept it in the queue),
	 *      `sgombra_abbandoni` (we threw it away), `video_ritmo_scesi` (we did not
	 *      even send it).  ⛔ The NETWORK's half — a packet
	 *      lost and resent by QUIC, the congestion window that has
	 *      closed — nobody could count, and every measurement under loss
	 *      ended in a discussion instead of an attribution.
	 *
	 * ⚠ These fields DECIDE NOTHING: they are the snapshot of the last line
	 *   written, and serve only to make the difference («how many in the interval»)
	 *   and to keep quiet when nothing has changed.  No threshold, no
	 *   rate, no switch: `rete_ciclo()` is pure observation.
	 *
	 * ⛔ `rete_detto_ms` at 0 means «never said», and the first line comes out
	 *    anyway: «the session has not spoken yet» and «nothing has
	 *    changed» must not look the same (`LEZIONI.md` §1.9). */
	uint64_t rete_detto_ms;
	uint64_t rete_pkt_lost, rete_bytes_lost;
	uint64_t rete_pkt_sent, rete_pkt_recv, rete_pkt_discarded;
	/* The verdict of the last line: if it changes, the line comes out even with counters
	 * still — going from «the window is closed» to «nothing to report» is
	 * precisely the fact one wants to see. */
	int rete_giudizio;

	/* ⭐⭐⭐ LOST DATAGRAMS — AND THE MEASURE OF REORDERING THAT NGTCP2 DOES NOT GIVE.
	 *
	 *     `ngtcp2.h:3442` says something worth more than the counter it
	 *     announces: *«Note that the loss might be spurious, and DATAGRAM frame
	 *     might be acknowledged later»*.  ⇒ If for the same `dgram_id` there arrives
	 *     first `lost_datagram` and THEN `ack_datagram`, that loss **was not
	 *     a loss**: it was a packet that arrived OUT OF ORDER, declared
	 *     lost by the three-packet threshold and acknowledged afterwards.
	 *
	 * ⭐ It is the signature of reordering, taken from the server's side, without patches to
	 *   ngtcp2 and without deducing it from the application's sequence numbers — which
	 *   was the only road visible before reading that line.
	 *   ⚠ It is partial by construction: it holds for **datagrams**, that is for audio;
	 *   on QUIC streams there is no identifier per piece and this road
	 *   does not exist.  The price is declared instead of letting one believe the
	 *   number covers all the traffic.
	 *
	 * ⛔ The ring is short ON PURPOSE: an acknowledgement arriving after 512 declared
	 *    losses is no longer a reordering, and counting it as such would inflate the
	 *    number precisely in the case — the line that really loses — in which it must
	 *    stay honest.  ⇒ Whatever falls out of the ring stays lost. */
	uint64_t dgram_persi;        /* `lost_datagram` said: lost */
	uint64_t dgram_riscontrati;  /* `ack_datagram` said: arrived */
	uint64_t dgram_falsi;        /* lost AND THEN acknowledged = REORDERING */
	uint64_t dgram_anello[WT_DGRAM_ANELLO];
	unsigned dgram_anello_i;
	uint64_t rete_dgram_persi, rete_dgram_falsi;

	/* ⛔⭐⭐ PHASE 9 — THE DEAD LINE: the fields on which the most visible
	 *      DECISION of the whole product is taken — throwing a session out.
	 *
	 *      ⚠ They are SEPARATE from the `rete_*` above on purpose, and not out of laziness:
	 *        those are the snapshot of the last LINE WRITTEN and move
	 *        only when the line comes out (that is when something has changed).
	 *        These move when A VERDICT WINDOW CLOSES, which
	 *        is another rhythm.  ⛔ Reusing the former would tie the decision to the
	 *        log's anti-noise filter: a session that loses
	 *        steadily lets few lines out, and the window would lengthen by
	 *        itself — that is the threshold would change without anybody having
	 *        written it.
	 *
	 * ⛔ `lm_finestra_ms == 0` means «never opened»: the first round takes a snapshot
	 *    and does not judge.  A verdict taken on the difference with the totals of the whole
	 *    connection would be a fraction over a window as long as the
	 *    session, that is another quantity. */
	uint64_t lm_finestra_ms;    /* when the current window opened            */
	uint64_t lm_pkt_sent;       /* `pkt_sent` when the window opened          */
	uint64_t lm_pkt_lost;       /* `pkt_lost` when the window opened          */
	/* ⛔⛔⭐ THE LOSS FRACTION IS A WITNESS, NO LONGER A JUDGE — 23
	 *      Aug 2026, and the reason is in full in the box above
	 *      `WT_LM_STALLO_MS`.  These three fields keep the snapshot
	 *      of the last CLOSED window, so the firing line carries the
	 *      number even when another cause decided. */
	unsigned lm_permille;       /* the fraction of the last closed window     */
	uint64_t lm_persi_v, lm_spediti_v; /* the two counts of that window       */
	uint64_t lm_durata_v;       /* and how long it really lasted, in ms       */
	/* ⛔⭐⭐ THE OUTPUT STALL — the quantity on which we DECIDE from today.
	 *
	 *      They are two monotonic counters plus an instant, and each of the three carries
	 *      one half of the sentence «how long has no frame left while
	 *      having some to send»:
	 *
	 *        · `lm_usciti`  — VIDEO bytes handed to ngtcp2 (`coda_consegna`):
	 *                         if it rises, the wire carries, and the count restarts;
	 *        · `lm_offerti` — frames the stage gave us for this
	 *                         session, counted BEFORE any brake, clear-out or
	 *                         refusal: if it does not rise and the queue is empty, there
	 *                         was nothing to send and the count DOES NOT START;
	 *        · `lm_uscita_ms` — the instant the count last restarted,
	 *                         for one of the two reasons above.
	 *
	 * ⛔ The two `_visti` are the values at the last verdict round: the quantity
	 *    is a DIFFERENCE between two samples, not a total.  A total
	 *    would say «since the session began», which is another thing. */
	uint64_t lm_usciti, lm_usciti_visti;
	uint64_t lm_offerti, lm_offerti_visti;
	uint64_t lm_uscita_ms;
	/* ⛔ Silence is not a free clock: it is «since when the client has not shown
	 *    a packet any more», and next to it there is the number of times
	 *    WE have sent it one since then.  Without the second, a
	 *    session in which neither of the two speaks would declare itself dead
	 *    on its own — and it is instead a still desktop. */
	uint64_t lm_vivo_ms;        /* the last time `pkt_recv` rose              */
	uint64_t lm_pkt_recv;       /* `pkt_recv` at that time                    */
	uint64_t lm_pkt_sent_vivo;  /* `pkt_sent` at that time = the PROBES       */
	bool lm_scattata;           /* ⛔ once only: afterwards, the wire drops   */
	/* ⛔⭐⭐ HOW BLIND WE HAVE BEEN, and how much of it THIS session has already
	 *      taken into account.  The two quantities the dead line decides on — the bytes
	 *      sent and the packets received — move ONLY while the parent's loop
	 *      runs: if the loop stopped, it was not the client that stopped,
	 *      **we stopped**, and counting that gap as its silence
	 *      means blaming its network for a blindness of ours.
	 * ⭐ The snapshot of the GLOBAL counter is kept instead of a flag: between two
	 *    verdicts there may have been several gaps, and a flag would lose some. */
	uint64_t lm_fermo_visto;    /* `giro_fermo_ms` at the last verdict        */
	/* ⛔⛔ THIS SESSION'S ZERO POINT — 25 Aug 2026, finding R5.
	 *
	 *     `giro_fermo_ms` is a GLOBAL counter that grows from when the
	 *     server is switched on, and the eviction line printed it as
	 *     `fermo_ms=` with a comment next to it saying *«since this
	 *     session was born»*.  ⛔ `[M]` §5.5 R5: a line attributed **54.5
	 *     seconds** of our blindness to a session **that at the time had not
	 *     been born yet**.  ⇒ Whoever reads ACQUITS the network when the network was involved,
	 *     that is the EXACTLY OPPOSITE error of the one the cure exists to
	 *     remove.  A witness accusing someone who was not there is worse than no
	 *     witness: it sends the diagnosis the wrong way (`LEZIONI.md`
	 *     §1.37).
	 *
	 * ⭐ We note what the global counter was worth at the FIRST round in which
	 *    this session was looked at, and the line prints the difference. */
	uint64_t lm_fermo_nato;     /* `giro_fermo_ms` at the first round of THIS  */
	uint64_t lm_fermo_saltati;  /* how many verdicts it skipped for a gap     */

	/* ⛔⭐ FRAMES IN FLIGHT — §5.1, «a more recent one has already left».
	 *
	 *     A frame RCP has already closed with FIN can still have all
	 *     its bytes stuck in this queue: for RCP it has left, on the wire it has
	 *     not.  §5.1 says that one MAY be reset — «the bytes not yet
	 *     sent do not leave at all» — and it is the only road by which an
	 *     abandonment really shows on the receiving side.
	 *
	 * ⚠ It is kept here and not in `rcp.c` because it is a fact of the QUEUE; and the three
	 *   consequences (the log line, the count, the keyframe debt)
	 *   are in `rcp.c`, which is the only one owning them. */
	struct {
		int64_t stream;
		uint32_t numero;
		bool chiave;
		bool vivo;
		bool detto; /* the keyframe holding back the queue is said once */
	} involo[WT_INVOLO_MAX];
	size_t ninvolo;
	/* ⛔ The stream `gancio_video_apri()` has just opened: `rcp.c` does not
	 *    return it, and deducing it from «the last opened on the connection» would be
	 *    guessing. */
	int64_t video_stream_ultimo;

	/* ═══ THIS SESSION'S AUDIO — phase 7 ═══════════════════════════════ */
	/*
	 * ⛔⭐ AUDIO IS NOT VIDEO, AND THE DIFFERENCE IS ALL BELOW.
	 *
	 *     Video lives on (reliable) streams: bytes that do not fit in a
	 *     packet STAY in the queue and leave later, and it is mandatory —
	 *     sealing a message with truncated bytes would fabricate a violation
	 *     by the client (see `NGTCP2_ERR_STREAM_DATA_BLOCKED` in `wt_scrivi`).
	 *
	 *     Audio lives on datagrams, and `RCP.md` §6.3 says the opposite in its own
	 *     words: «no retransmission, no reordering».  ⇒ A block that does not
	 *     leave is NOT kept: it is THROWN AWAY, and counted.
	 *
	 * ⭐ And the OLDEST are thrown away, not the newest — it is the rule v1
	 *    had already found (`fondamenta/remotix-c/src/altoparlante.h`): «late
	 *    sound is of no use to anyone, and a queue that grows forever
	 *    would end up eating the server's memory to play a noise
	 *    from half a minute ago».
	 */
	struct {
		uint8_t d[WT_DGRAM_BYTE];
		size_t n;
		/* ⛔⭐ WHEN IT ENTERED THE QUEUE — and it sits on the ELEMENT on purpose.
		 *
		 *     A block's age is a fact OF ITS OWN, and the counter that lived
		 *     on the connection could not tell it: the head changes under it
		 *     without it noticing (⇒ the box of
		 *     `WT_DGRAM_ZITTO_MAX_MS`).
		 * ⛔ AND THIS FIELD DECIDES NOTHING: it only ends up in the log
		 *    line of the discard.  ⚠ It is there on purpose to be proved wrong — if
		 *    one day the age of the dropped block diverged from the connection's
		 *    silence, the queue would have stopped refreshing and one would
		 *    read it instead of deducing it.
		 * ⚠ The `ngtcp2_tstamp` is the same one that then judges it
		 *   (`dgram_scrivi_uno`): two different clocks would give a
		 *   difference that is not a time. */
		ngtcp2_tstamp nato;
	} dgram[WT_DGRAM_MAX];
	size_t ndgram, dgram_testa;
	uint64_t dgram_id; /* the identifier ngtcp2 reports in the outcomes */

	bool audio_acceso;
	uint8_t audio_codec;
	/* ⛔ The twin of `video_fermo`, and the box is there: «I have already asked
	 *    the child to capture no more».  ⚠ It is cured HERE together with video and not
	 *    another day because the defect is the same and the shape is the
	 *    same — it is lesson §1.20 written in this file on the counts
	 *    of audio and video: *«a cure is looked for wherever it applies, not where
	 *    it was found»*, and that time the twin stayed behind for five
	 *    days. */
	bool audio_fermo;
	/* ⛔ «I have already explained why this session has no audio»: once
	 *    only, like `video_detto`, and for the same reason. */
	bool audio_detto;
	/* ⛔ «The peer does not accept datagrams»: said once.  ⚠ `RCP.md` §2.2
	 *    DEMANDS them, but §6.3 forbids closing the connection over a datagram
	 *    fact — so it is declared and then kept quiet, not killed. */
	bool dgram_negati_detto;
	uint64_t audio_spediti, audio_buttati, audio_rifiutati;
	/* ⛔ DEFERRED and REFUSED are two different facts and are not added: the
	 *    first is «the pacer said not now» and the block leaves all the same a
	 *    moment later; the second is «thrown away».  A single counter for two opposite
	 *    outcomes would say audio is lost even when everything arrives. */
	uint64_t audio_rimandati;
	/* The instant of the last deferral: within the same pass it is not retried. */
	ngtcp2_tstamp dgram_rimando_ts;
	/* ⛔⭐ SINCE WHEN THIS CONNECTION HAS NOT PUT A DATAGRAM IN A PACKET
	 *     — `0` means «right now I am not mute» (⇒ `WT_DGRAM_ZITTO_MAX_MS`).
	 *
	 * ⚠ It is the field that replaces `dgram_rimandi`, and the difference is all
	 *   in the unit: that one counted PASSES (85 000 a second under load,
	 *   200 at rest), this one counts milliseconds.  ⛔ Zero and «an instant ago»
	 *   must not look the same: it is reset at every success and restarts
	 *   at the first refusal, so a clock that has not started is not a clock
	 *   that has expired. */
	ngtcp2_tstamp dgram_zitto_da;
	/* ⛔⭐ THE SESSION CLOCK, and it serves a single thing: stamping the
	 *    audio blocks when they enter the queue (`dgram_accoda()`, which
	 *    receives no `ts` from its caller).
	 *
	 * ⚠ It is written by `wt_batti()` and `wt_scrivi()`, which are the only two places
	 *   where the authoritative `ngtcp2_tstamp` enters this file — and
	 *   `audio_regola()`, which enqueues, runs INSIDE `wt_batti()`, three lines after
	 *   this field has been brought up to date.
	 * ⛔ A `clock_gettime()` called in here would be a SECOND clock, and
	 *   the difference between two clocks is not a time. */
	ngtcp2_tstamp ts_ora;

	/* The test tone (`--audio-prova`), which normally does not exist. */
	audio_cod *tono_cod;
	uint64_t tono_prossimo_us; /* the instant of the next block */
	uint64_t tono_i;           /* the sample index: the phase is continuous */

	/* The list of live sessions, for broadcasting frames. */
	wt *viva_dopo;

	/* ⛔ The session's closure WAITS for the output queue to have
	 *    emptied, and then a little more: see `chiudi_sessione()`. */
	int chiusura;
	ngtcp2_tstamp chiusura_da;
	/* ⛔⭐ AND THE WAIT HAS A BACKSTOP — finding B-3, night of 10 Aug 2026.
	 *
	 *     «Wait for the queue to empty» is a condition someone must
	 *     make happen.  Until the queue empties, `wt_batti()` resets
	 *     `chiusura_da` at every heartbeat and the capsule of §3.1 point 3 NEVER
	 *     LEAVES: the reason, which is «what saves the diagnoses», stays inside the
	 *     server.  ⚠ A job deferred to a condition nobody makes happen any more
	 *     is not deferred: it is lost.
	 *
	 * ⭐ Hence the deadline: once past it, the capsule leaves all the same and the
	 *    giving-up is WRITTEN. */
	ngtcp2_tstamp chiusura_scadenza;

	/* ⛔⭐ §4.6 — THE CAP OF THE SESSION THAT NEVER OPENS THE CHANNEL.
	 *
	 * ✅ `DECISIONI.md` §7.17, decided by the user on 11 Aug 2026: **5 s**
	 *    from the opening of the WebTransport session to the opening of the control
	 *    channel, then `TEMPO_SCADUTO`.
	 *
	 * ⛔ Why one more clock was needed: those of §4.6 start
	 *    from the opening of the CHANNEL, so whoever opened the session and never
	 *    opened the channel **had no cap on them at all**.  `[M]` 11 Aug
	 *    2026, bench B6: the session without a channel stayed alive 20 014 ms
	 *    without anything happening.
	 *
	 * ⚠ And QUIC's idle timeout did not cover it: that one counts
	 *   SILENCE, and a session writing on another stream is not
	 *   silent — it held the slot indefinitely.
	 *
	 * ⛔ Zero when the channel is already there (or the session is not there yet): a
	 *    clock that has not started and one that has expired must not look
	 *    the same. */
	ngtcp2_tstamp canale_entro;

	/* ⛔ How many bytes are in the queue, for the cap of `coda_metti()`.
	 * ⚠ PHASE 9: it counts the bytes that must STILL LEAVE.  An element
	 *   handed to ngtcp2 leaves this count even if its memory is
	 *   still ours — the cap of `coda_metti()` regulates the BACKLOG, and
	 *   putting the bytes in flight inside it would make good frames be refused
	 *   because of stuff that is already on the wire. */
	size_t byte_in_coda;
	/* ⛔⭐ PHASE 9 — THE MEMORY PRICE OF THE CURE, MEASURED AND NOT ESTIMATED.
	 *
	 *     The bytes HANDED to ngtcp2 and not yet confirmed: out of the queue's
	 *     count (they no longer have to leave) but still allocated, because the
	 *     contract of `writev_stream` demands they stay so until
	 *     the ack arrives or the stream closes.
	 *
	 * ⭐ HOW MUCH IT IS — and this file does not decide the number: it is the bytes in flight
	 *    on QUIC, that is at most the congestion window plus what is
	 *    lost and not yet redeclared.  On a line that carries it is in the order
	 *    of tens to hundreds of KB per session; the hard cap is not ours but
	 *    the peer's — it cannot grant us more credit than `initial_max_data`.
	 * ⛔ `byte_in_volo_max` is the PEAK, and it is written at closure: it is the
	 *    quantity that says whether the cure holds or is hoarding memory. */
	size_t byte_in_volo, byte_in_volo_max;
	/* How many surplus streams (§2.5) have already been written: so as not to fill the
	 * log with one line per packet. */
	uint64_t scartati_stream, scartati_byte;

	/* ⭐ OUR clock, in place of the graft's keep-alive. */
	ngtcp2_tstamp battito;
	uint64_t battito_ms;
	/* ⛔ §4.6: the TRANSPORT PINGs while the credentials are awaited.  Whether
	 *    they are on is kept here, so as not to call ngtcp2 back at every heartbeat and
	 *    to be able to WRITE it in the log when it changes. */
	bool tienila_viva;
};

/* ⛔⛔⭐ WHOSE LINE IT IS, IN THE PARENT — 25 Aug 2026, finding R4 of §5.5.
 *
 *     The cure of 25 August (R10-A4) gave a name to **163 lines out of 163** of
 *     `rcp.c`, which go through a single funnel (`gancio_registra`).  ⛔ But the
 *     lines `webtransport.c` writes ON ITS OWN do not go through there: they were
 *     **93 mute calls against a single one that named**, and among the mute ones was
 *     the most important of phase 9 — **the eviction line**, the one that
 *     says who was thrown out and why.
 *
 * ⇒ ⭐ *Nobody knew whom the most important line of the phase was talking about.*
 *
 * ⭐ The identity was already in hand, as in `gancio_registra`: the `wt` carries the
 *    RCP session, and `rcp_utente()` has always existed.  Here is the only road
 *    to take it, so the print points do not each compose it in their own
 *    way — the same reason the parenthesis is written in `registro.c`.
 *
 * ⚠ AND WHOEVER DOES NOT KNOW KEEPS QUIET (`registro.h`): before authentication `w->rcp`
 *   does not yet have a user, `rcp_utente()` returns `""`, and `registro_dice_di()`
 *   writes the line **without parenthesis**.  ⛔ The origin is not put in its
 *   place: the body of those lines already carries it (`w->provenienza`), and a
 *   second field saying the same thing is volume, not diagnosis.
 * ⚠ `NULL` holds on purpose: `wt_libera()` writes lines with the RCP session already
 *   unhooked, and there the name is no longer there — better mute than wrong.
 *
 * ⛔ AND ELEVEN LINES OF THIS FILE STAY MUTE ON PURPOSE, and must be left so:
 *    the ten of `REG_AVVIO` (the three phase-9 cures that declare the value
 *    in force, on AND off) and the one of the test tone.  ⭐ They speak of the
 *    SERVER, not of a tenant: attaching a name to them would mean promising
 *    the reader that the line concerns a single session, and it would be the same
 *    lie as `fermo_ms=` — a witness pointing at the wrong person. */
static const char *wt_chi(const wt *w)
{
	return (w && w->rcp) ? rcp_utente(w->rcp) : NULL;
}

/* ------------------------------------------------------------------------ */
/* QUIC variable-length integers (RFC 9000 §16).  They are needed three times   */
/* and are in neither library: nghttp3 keeps its own to itself.               */

static size_t varint_scrivi(uint8_t *dest, uint64_t v)
{
	if (v < 64) {
		dest[0] = (uint8_t)v;
		return 1;
	}
	if (v < 16384) {
		dest[0] = (uint8_t)(0x40 | (v >> 8));
		dest[1] = (uint8_t)(v & 0xff);
		return 2;
	}
	if (v < 1073741824) {
		dest[0] = (uint8_t)(0x80 | (v >> 24));
		dest[1] = (uint8_t)((v >> 16) & 0xff);
		dest[2] = (uint8_t)((v >> 8) & 0xff);
		dest[3] = (uint8_t)(v & 0xff);
		return 4;
	}
	dest[0] = (uint8_t)(0xc0 | (v >> 56));
	for (size_t i = 1; i < 8; i++)
		dest[i] = (uint8_t)((v >> (8 * (7 - i))) & 0xff);
	return 8;
}

/* ⛔ Returns 0 if the bytes are not enough: «I don't know yet» and «zero» are two
 *    different things, and confusing them is `LEZIONI.md` §1.9. */
static size_t varint_leggi(uint64_t *v, const uint8_t *src, size_t len)
{
	size_t n;
	if (len == 0)
		return 0;
	n = (size_t)1 << (src[0] >> 6);
	if (len < n)
		return 0;
	*v = src[0] & 0x3f;
	for (size_t i = 1; i < n; i++)
		*v = (*v << 8) | src[i];
	return n;
}

/* ⛔ The two numbers with which a server declares WebTransport, and they are TWO because
 *    the drafts in circulation are two:
 *
 *      0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   draft 02
 *      0xc671706a  SETTINGS_WT_MAX_SESSIONS       draft 07 and later
 *
 * ⚠ And the difference is not academic: `aioquic` 1.2 — the test client —
 *   implements 02 `[R]`, while today's browsers look for 07.  A server
 *   that sent only one would work with half of our tools and not
 *   with the other half, and the half that works would be the wrong one from which
 *   to draw conclusions.  Both are sent: an unknown setting is
 *   ignored. */
#define WT_ENABLE_WEBTRANSPORT 0x2b603742ULL
#define WT_MAX_SESSIONS 0xc671706aULL

/* ⛔⭐ THE CAP OF A CAPSULE, AND IT IS CHECKED BEFORE KEEPING THE BYTES.
 *
 * `RCP.md` §6.1: «a receiver that allocates `lunghezza` bytes and then checks has
 * already given away a megabyte to anyone who can write six bytes».  ⚠ Waiting for
 * the bytes instead of allocating them is the same gift, made more slowly.
 *
 * ⭐ The number is what the only capsule that concerns us needs:
 * `CLOSE_WEBTRANSPORT_SESSION` carries a 32-bit code and a reason that
 * WebTransport limits to 1024 bytes. */
#define WT_CAPSULA_MAX (1024 + 4)

/* How long we wait, after the queue has emptied, before sending the
 * capsule that closes the session.  ⭐ In the graft it was «five write
 * passes» with keep-alive at 100 ms, that is half a second: here time is
 * measured instead of counted, and nothing goes on the wire. */
#define WT_ATTESA_CHIUSURA_NS (500ULL * NGTCP2_MILLISECONDS)

/* ⛔ §4.6, the missing line: from the opening of the WebTransport session
 *    to the opening of the control channel, **5 s**.
 * ✅ `DECISIONI.md` §7.17, decided by the user on 11 Aug 2026.
 * ⭐ The same number as the first cap of §4.6, and not for symmetry: opening the
 *    channel is the first mandatory act of the session (§2.5), it does not depend
 *    on how fast a person types and does not depend on the network any more
 *    than `CIAO` does. */
#define WT_TETTO_CANALE_NS (5000ULL * NGTCP2_MILLISECONDS)

/* ------------------------------------------------------------------------ */
/* The lists.                                                                 */

static stream_giudizio *giudizio_trova(wt *w, int64_t id)
{
	for (size_t i = 0; i < w->ngiudizi; i++)
		if (w->giudizi[i].id == id)
			return &w->giudizi[i];
	return NULL;
}

static stream_giudizio *giudizio_crea(wt *w, int64_t id)
{
	stream_giudizio *g = giudizio_trova(w, id);
	if (g)
		return g;
	if (w->ngiudizi == w->capgiudizi) {
		size_t c = w->capgiudizi ? w->capgiudizi * 2 : 8;
		stream_giudizio *n = realloc(w->giudizi, c * sizeof *n);
		if (!n)
			return NULL;
		w->giudizi = n;
		w->capgiudizi = c;
	}
	g = &w->giudizi[w->ngiudizi++];
	memset(g, 0, sizeof *g);
	g->id = id;
	g->genere = G_INCERTO;
	return g;
}

static richiesta *richiesta_trova(wt *w, int64_t id, bool crea)
{
	for (size_t i = 0; i < w->nrichieste; i++)
		if (w->richieste[i].usato && w->richieste[i].id == id)
			return &w->richieste[i];
	if (!crea)
		return NULL;
	for (size_t i = 0; i < w->nrichieste; i++)
		if (!w->richieste[i].usato) {
			memset(&w->richieste[i], 0, sizeof w->richieste[i]);
			w->richieste[i].id = id;
			w->richieste[i].usato = true;
			return &w->richieste[i];
		}
	if (w->nrichieste == w->caprichieste) {
		size_t c = w->caprichieste ? w->caprichieste * 2 : 8;
		richiesta *n = realloc(w->richieste, c * sizeof *n);
		if (!n)
			return NULL;
		w->richieste = n;
		w->caprichieste = c;
	}
	{
		richiesta *r = &w->richieste[w->nrichieste++];
		memset(r, 0, sizeof *r);
		r->id = id;
		r->usato = true;
		return r;
	}
}

/* ⛔⭐ PHASE 9 — DOES THIS STREAM CARRY A FRAME?  It serves ONE thing only: to
 *     count the VIDEO bytes going out towards the wire, which is the
 *     «has gone out» half of the dead line's quantity (the box above
 *     `WT_LM_STALLO_MS`).
 *
 * ⛔ The list `involo[]` is the only place where the fact is written: the
 *    video streams are opened by US and nobody declares them to us elsewhere.
 *    Telling them apart by exclusion — «everything that is not the control
 *    channel» — would put the clipboard in too, and a clipboard transfer
 *    succeeding while video is stopped would reset the stall
 *    count precisely in the round in which it must run.
 *
 * ⚠ THE PRICE, DECLARED: a frame that did not enter the list because
 *   `WT_INVOLO_MAX` was full is not counted, so its bytes do not
 *   reset the stall.  ⛔ It errs on the STRICT side — but a full list
 *   means thirty-two frames in flight together, that is a queue that does not
 *   empty: it is already the stall, not a healthy case mistaken for broken.  And the
 *   line of `involo_aggiungi()` declares it when it happens. */
static bool stream_di_un_fotogramma(const wt *w, int64_t id)
{
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo && w->involo[i].stream == id)
			return true;
	return false;
}

/* ⛔ An element dies here and nowhere else: it is the only point where
 *    `byte_in_coda` (and now `byte_in_volo`) goes down, and two points that
 *    lowered it would diverge.
 *
 * ⛔⭐ PHASE 9 — AND «DYING» MEANS `free()`, that is «from now on ngtcp2 MUST NO
 *     longer be able to reread these bytes».  The only three lawful callers are the
 *     two conditions of the contract plus the end of the connection:
 *
 *       1. `coda_conferma()`     — the ack covers the bytes;
 *       2. `wt_stream_chiuso()`  — the stream is closed (ngtcp2 says literally
 *          that «after stream_close ... application can free all unacknowledged
 *          stream data»);
 *       3. `coda_butta_stream()` — the stream was RESET a moment before
 *          (`ngtcp2_conn_shutdown_stream_write()`), and after a `RESET_STREAM`
 *          ngtcp2 does not requeue the frames of that stream.
 *
 * ⛔ «Serialised» is NOT among these, and it was the defect of 23 August. */
static void coda_uccidi(wt *w, size_t i)
{
	uscita *u;
	if (i >= w->ncoda)
		return;
	u = &w->coda[i];
	if (u->morto)
		return;
	/* ⚠ The two counts are EXCLUSIVE: whoever is handed over has already left
	 *   `byte_in_coda` and entered `byte_in_volo`.  Lowering both
	 *   would remove the same bytes twice from different quantities. */
	if (u->consegnato) {
		if (w->byte_in_volo >= u->dati.n)
			w->byte_in_volo -= u->dati.n;
		else
			w->byte_in_volo = 0;
	} else if (w->byte_in_coda >= u->dati.n) {
		w->byte_in_coda -= u->dati.n;
	} else {
		w->byte_in_coda = 0;
	}
	bytes_libera(&u->dati);
	u->morto = true;
	/* The dead at the head are of no use to anyone: the head slides. */
	while (w->testa < w->ncoda && w->coda[w->testa].morto)
		w->testa++;
	if (w->testa == w->ncoda)
		w->testa = w->ncoda = 0;
}

/* ⛔⭐ PHASE 9 — «HANDED OVER»: all the bytes are inside ngtcp2, and they are NOT
 *     FREED.  It is what `coda_uccidi()` used to do at this point.
 *
 *     The element leaves the choice (`coda_scegli()`) and the backlog count
 *     (`byte_in_coda`, `coda_vuota()`) — it has nothing more to offer — but
 *     stays in the queue with its bytes, because they are the ones ngtcp2 will reread
 *     if a packet is lost. */
static void coda_consegna(wt *w, size_t i)
{
	uscita *u;
	if (i >= w->ncoda)
		return;
	u = &w->coda[i];
	if (u->morto || u->consegnato)
		return;
	/* ⭐ An element WITHOUT bytes — the FIN of §6.2, which is a queue element
	 *    like the others — gives no pointer to ngtcp2: there is nothing to
	 *    keep alive.  ⛔ And keeping it would leave it in the queue FOREVER: it
	 *    occupies no offset of the stream, so no ack could ever
	 *    cover it, and `coda_vuota()` would never become true again. */
	if (u->dati.n == 0) {
		coda_uccidi(w, i);
		return;
	}
	if (w->byte_in_coda >= u->dati.n)
		w->byte_in_coda -= u->dati.n;
	else
		w->byte_in_coda = 0;
	u->consegnato = true;
	w->byte_in_volo += u->dati.n;
	if (w->byte_in_volo > w->byte_in_volo_max)
		w->byte_in_volo_max = w->byte_in_volo;
	/* ⛔⭐⭐ PHASE 9 — AND IT IS HERE THAT «A FRAME GOES OUT», at the only point of the
	 *      file where the fact happens: `ndatalen` has covered the whole
	 *      element, that is those bytes have ended up INSIDE A PACKET.
	 *
	 *      ⚠ It is not «the client has seen them»: it is «they have left».  And it is intended —
	 *        the dead line's quantity must be LOCAL and monotonic (the
	 *        P20 shape of `RCP.md:398`), or the decision to throw a session out
	 *        would depend on what the peer says.
	 *
	 * ⛔ BYTES are counted and not whole frames, and the reason is the
	 *    direction of the error: a 60 000-byte keyframe on a narrow line
	 *    can take seconds to go out entirely, and counting frames those
	 *    seconds would be a «stall» while the wire is working.  A byte
	 *    that leaves is a wire that carries. */
	if (stream_di_un_fotogramma(w, u->id))
		w->lm_usciti += u->dati.n;
}

/* ⛔⭐ PHASE 9 — THE ACK FREES, and before nobody did.
 *
 *     `acked_stream_data_offset` arrives, says `ngtcp2.h`, «sequentially in
 *     increasing order of offset without any overlap»: it is the CONTIGUOUS
 *     ADVANCE of the acknowledgement on that stream, and it is the same quantity
 *     `nghttp3_conn_add_ack_offset()` expects.  ⇒ Adding up the `datalen` gives
 *     how many bytes of the stream are confirmed, and they are consumed against the
 *     elements of that stream in INSERTION ORDER — which is the order in
 *     which they went out, because `coda_scegli()` scans in that order.
 *
 * ⛔ AND THE CONNECT STREAM (`w->sessione`) IS EXCLUDED — the reason shows
 *    only when writing it down: there **we are not the only ones writing**.  nghttp3 puts
 *    the response headers there, at the lowest offsets, and their acks
 *    would enter this count: our closing capsule would be
 *    freed BEFORE being confirmed, that is it would redo in small the defect
 *    of 23 August.  ⇒ On that stream we wait for the OTHER half of the contract,
 *    the closure (`wt_stream_chiuso()`).  It is nine bytes, and when they enter
 *    the queue the session is already ending.
 *
 * ⭐ On all the others exclusivity is true and can be proved: the video streams
 *    and the clipboard streams are OPENED BY US (`ngtcp2_conn_open_uni_stream()`, and nobody
 *    else writes on them), and the control channel (`rcp_stream`) is judged
 *    `G_WT` — its bytes come back `E_MIO` from `smista()` and never reach
 *    nghttp3.  ⇒ On those streams our first byte is at offset 0 and
 *    the sum of the `datalen` is our count, exactly. */
static void coda_conferma(wt *w, int64_t id, uint64_t quanti)
{
	size_t i = w->testa;

	if (id == w->sessione)
		return;
	while (quanti > 0 && i < w->ncoda) {
		uscita *u = &w->coda[i];
		size_t apertura;

		if (u->morto || u->id != id) {
			i++;
			continue;
		}
		/* ⛔ No more is confirmed than was handed over: the acknowledgement
		 *    cannot run ahead of the writing.  ⚠ Zero here means
		 *    we have reached the frontier of that stream, and further on
		 *    there is nothing older: we stop. */
		apertura = u->off - u->confermati;
		if (apertura == 0)
			break;
		if ((uint64_t)apertura > quanti) {
			u->confermati += (size_t)quanti;
			return;
		}
		u->confermati += apertura;
		quanti -= apertura;
		if (u->consegnato && u->confermati >= u->dati.n) {
			coda_uccidi(w, i);
			/* ⚠ `coda_uccidi()` slides the head and can reset the whole
			 *   queue: the loop's end must be reread, not remembered. */
			if (w->ncoda == 0)
				return;
		}
		i++;
	}
}

/* ⛔⭐ PHASE 9 — «EMPTY» MEANS «NOTHING TO SEND», not «nothing in memory».
 *
 *     An element handed over and not yet confirmed no longer has a byte to
 *     send: counting it here would keep `wt_ha_da_dire()` on forever — the
 *     server would spin idle — and above all the `!coda_vuota` branch of
 *     `wt_batti()` would reset `chiusura_da` at every heartbeat, that is the capsule
 *     of §3.1 point 3 would NEVER leave.  ⛔ It is defect B-3, redone from
 *     another side. */
static bool coda_vuota(const wt *w)
{
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto && !w->coda[i].consegnato)
			return false;
	return true;
}

/* ⛔ How many elements STILL HAVE TO LEAVE — and it serves the two log
 *    lines that tell of a closure that does not mature.  ⚠ `ncoda - testa`,
 *    which is what they used to write, would from today also count the handed-over ones:
 *    it would send people looking for a backlog that is not there precisely at the point where
 *    someone is looking for why the capsule does not leave. */
static size_t coda_da_spedire(const wt *w)
{
	size_t n = 0;
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto && !w->coda[i].consegnato)
			n++;
	return n;
}

/* ⛔ How many bytes of THIS stream have not gone out yet.  ⚠ Zero does not mean
 *    «it has arrived»: it means «it is no longer our stuff» — we handed it
 *    to ngtcp2.  The difference is declared here because §5.1 uses it: a
 *    frame that no longer has bytes in the queue is not abandoned, because
 *    abandoning it would no longer save anything. */
static size_t coda_byte_stream(const wt *w, int64_t id)
{
	size_t n = 0;
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto && w->coda[i].id == id)
			n += w->coda[i].dati.n - w->coda[i].off;
	return n;
}

/* ⛔⭐ PHASE 9 — THE VIDEO BYTES THAT STILL HAVE TO LEAVE, and they are the
 *     «I had something to send» half of the dead line's quantity.
 *
 *     It is the same sum `video_sgombra()` and `ritmo_frena()` make, with two
 *     declared differences: here KEYFRAMES count too (a keyframe stuck in the
 *     queue is stuff to send as much as a delta — §5.2 forbids abandoning it, not
 *     counting it), and no `arretrato` is counted, because here the question
 *     is not «how many frames» but «is there something».
 *
 * ⚠ Zero does NOT mean «it has arrived»: it means «it is no longer our stuff».
 *   It is exactly the meaning needed — if we have nothing left at
 *   home, there is nothing the wire is holding back from us. */
static size_t coda_byte_video(const wt *w)
{
	size_t n = 0;
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo)
			n += coda_byte_stream(w, w->involo[i].stream);
	return n;
}

/* ⛔ §5.1: the bytes not yet sent **do not leave at all**.  It is called only
 *    next to a `RESET_STREAM`: throwing the bytes away without resetting the stream
 *    would leave the client waiting for an end that does not come.
 *
 * ⛔⭐ PHASE 9 — AND IT IS ALSO THE PLACE WHERE THE HANDED-OVER ONES ARE FREED, which
 *     makes that rule stricter than before, not looser: resetting the stream
 *     is what **takes from ngtcp2 the right to reread them** — after a
 *     `RESET_STREAM` the frames of that stream do not go back in the
 *     retransmission queue — and it is the other half of the contract of `writev_stream`.
 *     ⚠ `video_sgombra()` already had this discipline («FIRST the
 *       stream is reset, THEN the bytes are thrown away»), and it is the line that proves the
 *       rule was known: it was missing where the bytes went away at the end of
 *       sending.  ⛔ Calling this function without a `shutdown_stream_write`
 *       (or a closure already happened) next to it redoes the defect of 23 August. */
static size_t coda_butta_stream(wt *w, int64_t id)
{
	size_t buttati = 0;
	for (size_t i = w->testa; i < w->ncoda; i++) {
		if (w->coda[i].morto || w->coda[i].id != id)
			continue;
		buttati += w->coda[i].dati.n - w->coda[i].off;
		coda_uccidi(w, i);
	}
	return buttati;
}

static bool stream_bloccato(const wt *w, int64_t id)
{
	for (size_t i = 0; i < w->nbloccati; i++)
		if (w->bloccati[i] == id)
			return true;
	return false;
}

/* ⛔ The first eligible element in INSERTION ORDER, skipping the streams
 *    already blocked in this pass.  ⚠ Scanning in order is what keeps
 *    the order WITHIN each stream: the first element of an unblocked stream
 *    is by construction its oldest. */
static uscita *coda_scegli(wt *w, size_t *fuori)
{
	for (size_t i = w->testa; i < w->ncoda; i++) {
		/* ⛔ PHASE 9: the HANDED-OVER ones are skipped too.  They are still in the queue
		 *    because their bytes are needed by ngtcp2 to retransmit, but they
		 *    have nothing more to offer: choosing them would mean proposing a
		 *    zero-length vector at every pass, and with `MORE` on
		 *    that is a pass that never ends. */
		if (w->coda[i].morto || w->coda[i].consegnato)
			continue;
		if (stream_bloccato(w, w->coda[i].id))
			continue;
		if (fuori)
			*fuori = i;
		return &w->coda[i];
	}
	return NULL;
}

/* ⛔ THE OUTPUT QUEUE CAP — finding B-3 point 4, night of 10 Aug 2026.
 *
 * `coda_metti()` and `bytes_aggiungi()` doubled without limit: the memory
 * of the process grew as much as the client wanted, and grew **on a session
 * already declared dead**.  ⚠ A cap that is not there is not a high cap: it is
 * an absent limiter, and nobody sees it until the machine runs out
 * of memory.
 *
 * ⭐ The number: two RCP messages at most (§6.1, 1 MiB each) plus a little
 *    margin.  This phase's control channel sends `ECCOMI`,
 *    `AMMESSO`/`RESPINTO`, `SESSIONE` and `CONGEDO`, which all fit in
 *    a few hundred bytes: if this cap is touched, something has
 *    happened that must be looked at — and indeed it is written.  ⛔ And whoever touches it does NOT
 *    go on silently: see `accoda()` and finding B-15.
 *
 * ⛔⭐ AND ON 12 AUG 2026 THE NUMBER CHANGED, with phase 2 — from 2 MiB to
 *     17.  The reason is not «more space was needed»:
 *
 *     `RCP.md` §6.2 declares a frame up to **16 MiB** **legal**, and
 *     `rcp_video_apri()` refuses exactly above that number.  ⛔ With the queue
 *     at 2 MiB a perfectly legal 3 MiB frame would have been
 *     refused **by our limiter** instead of by the protocol's cap:
 *     two different caps for the same quantity, and the one that bites first
 *     is not the one written in the referee.
 *
 *     ⚠ And the symptom would have been a **silent degradation** — the
 *       frame does not leave, the client sees a hole and asks for a keyframe, the
 *       keyframe is even bigger: the spiral of §5.2, caused by a
 *       constant of this file.  It is invariant **I1** as read by
 *       `REVIEWER.md` §3.
 *
 *     ⭐ 16 MiB (the biggest frame §6.2 admits) + 1 MiB for the
 *        control channel messages, which take a few hundred
 *        bytes each.  ⚠ The price is declared: over 16 sessions the theoretical
 *        worst is 272 MiB, and it is the price §6.2 has already chosen — not a
 *        new one. */
#define WT_CODA_MAX (17u * 1024u * 1024u)

static bool coda_metti(wt *w, int64_t id, const uint8_t *d, size_t n, bool fin)
{
	uscita *u;
	if (w->byte_in_coda + n > WT_CODA_MAX) {
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ the output queue has touched the cap (%zu bytes in "
		                 "queue + %zu, cap %u): not enqueuing",
		                 w->byte_in_coda, n, WT_CODA_MAX);
		return false;
	}
	if (w->ncoda == w->capcoda) {
		if (w->testa > 0) {
			memmove(w->coda, w->coda + w->testa,
			        (w->ncoda - w->testa) * sizeof *w->coda);
			w->ncoda -= w->testa;
			w->testa = 0;
		}
		if (w->ncoda == w->capcoda) {
			size_t c = w->capcoda ? w->capcoda * 2 : 8;
			uscita *nu = realloc(w->coda, c * sizeof *nu);
			if (!nu)
				return false;
			w->coda = nu;
			w->capcoda = c;
		}
	}
	u = &w->coda[w->ncoda++];
	memset(u, 0, sizeof *u);
	u->id = id;
	u->fin = fin;
	if (!bytes_aggiungi(&u->dati, d, n)) {
		w->ncoda--;
		return false;
	}
	w->byte_in_coda += n;
	return true;
}

/* ⛔⭐ AND THE BYTES ARE NOT THROWN AWAY: THIS IS A RELIABLE CHANNEL — finding B-15,
 *     night of 10 Aug 2026.
 *
 *     This function wrote a line in the log and **went on**.  The
 *     caller — `manda_controllo()`, that is the road of ALL RCP messages
 *     — received no outcome: RCP believed it had sent `ECCOMI`,
 *     moved on to `attesa-credenziali`, and the next message would have
 *     been welded to the void left by the first.  ⛔ The client would have read
 *     a framing the server never meant to write: it would have been
 *     the SERVER fabricating the client's violation.
 *
 *     ⚠ It is the same lesson as the box of `STREAM_DATA_BLOCKED` further below,
 *       applied to the other of the two roads by which bytes can be
 *       lost.  The cure back then had been put on only one.
 *
 * ⭐ The cure: whoever cannot enqueue does NOT go on.  The layer is declared
 *    faulty, and `wt_scrivi()` makes the QUIC connection die at the first pass.
 *    ⛔ A connection that dies is unequivocal; a message welded halfway
 *    sends people looking for the defect in the client.  ⚠ The reason of §3.1 cannot
 *    travel: if the queue does not take six bytes it does not take the
 *    capsule either, and this log line is the only place where the fact
 *    appears.  It is written because it is the only one. */
static bool accoda(wt *w, int64_t id, const uint8_t *d, size_t n)
{
	if (coda_metti(w, id, d, n, false))
		return true;
	registro_dice_di(REG_WT, wt_chi(w),
	                 "⛔⛔ %zu bytes for stream %ld do NOT enter the queue: the "
	                 "session does NOT go on.  A reliable channel does not throw away "
	                 "bytes, and half a message on the wire would be a violation "
	                 "fabricated by the server (§6.1)",
	                 n, (long)id);
	w->guasto = true;
	return false;
}

/* ------------------------------------------------------------------------ */

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔⛔⭐⭐ THE HEARTBEAT IS A DEADLINE, NOT A POSTPONEMENT — 23 Sep 2026, and this
 *         single line is worth **698 seconds of frozen screen out of 1199**.
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * `[M]` A REAL 20-minute session, visible Firefox on `rete11-kde`, moving
 *       scene, binary `cd8a3aec`:
 *
 *         · 698 s out of 1199 (**58 %**) without a single new frame;
 *         · seven blocks above 20 s: 74 · 56 · 62 · 25 · **370** · 53 · 56;
 *         · inside the blocks **45 278** frames captured, composed,
 *           encoded and thrown away before the wire (~13 GB of encoding for
 *           nobody, on an integrated Intel UHD 770);
 *         · the image NEVER breaks (1146 snapshots, zero faulty cells):
 *           ⇒ it was not corruption, it was a **block**.
 *
 * ⛔ AND THE CAUSE IS NOT WHERE IT WAS LOOKED FOR.  The hypothesis in the field was a race
 *    between two keyframe requests («the keyframe that goes out pays the wrong debt»).
 *    **False**: in the log every request has its keyframe, the child
 *    always answers within ~17 ms, and §5.2 behaves as declared.
 *
 * ⭐⭐ THE CAUSE IS HERE.  `batti_fra()` **moved the deadline forward** at
 *     every call, and `regola_battito()` — which calls it — sits at the end of
 *     `rcp_passa_input()`, that is it runs **at every client input message**.
 *     A real browser following the mouse sends ~40 a second.
 *
 *       ⇒ deadline at 1000 ms, postponed 40 times a second ⇒ **it NEVER matures**
 *
 *     And with it `wt_batti()` does not run, that is these do NOT run:
 *       · `video_regola()`  — the only one that REquests the keyframe from the stage (§5.2);
 *       · `rcp_tempo()`     — the §5.3 silence clock and the caps of §4.6;
 *       · `audio_regola()`, `ritmo_ciclo()`, `rete_ciclo()`.
 *
 * `[M]` THE PROOF, from the real session's log, and it leaves no way out:
 *
 *         13:26:29.990  a braked delta switches the §5.2 debt back on
 *                       (`rcp_video_scartato_prima_del_filo()`), and the request
 *                       in line falls into the 150 ms backstop — 35 ms too early
 *         13:26:30 → 13:32:39   **no** `rete-quic` line, **no**
 *                       `rate of` line, **no** keyframe request: the heartbeat
 *                       never matured.  Input, meanwhile, flows at ~40/s
 *         13:32:38.615  **last** input message from the client
 *         13:32:39.615  heartbeat, **exactly 1000 ms later** — and with it
 *                       `rete-quic … da_ms=370927`, the keyframe request, and
 *                       13:32:39.640 frame 7975 SENT: KEYFRAME
 *
 *       ⇒ The block did not end «by itself»: it ended when the user
 *         stopped moving the mouse for one second.  ⭐ `da_ms=370927` is
 *         the heartbeat confessing in writing how long it was stopped.
 *
 * ⛔ AND THE NET HAD NOT SEEN IT — a green pass on the same binary: the
 *    Python client does not send 40 inputs a second, and the runs are short.
 *    ⇒ A green is not a proof when the bench does not do the thing that breaks.
 *
 * ⭐ THE CURE: whoever asks «beat me in X» sets a CAP, not an appointment.
 *    A deadline already set and NEARER stays where it is; only a nearer
 *    one can move it.  So no sequence of events, however dense it
 *    may be, can push the heartbeat away forever.
 *
 * ⚠ And the «it has just fired» case is not lost: when `wt_batti()` calls
 *   `regola_battito()`, the old deadline is <= now — so it is NOT in the
 *   future, it does not win, and the heartbeat rearms regularly.  Without that
 *   condition the deadline would stay in the past and the loop would spin
 *   idle at 100 % CPU (it is the same defect written in `wt_battito_ns()`).
 *
 * ⛔ Whoever touches this function should ask one thing only: *«can an event the
 *    client can repeat at will prevent this deadline from
 *    maturing?»*  If yes, the defect is back.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⭐⭐ THE BEFORE/AFTER, MEASURED — 23 Sep 2026, bench `prova-battito.py`
 * ───────────────────────────────────────────────────────────────────────────
 *
 * ⛔ The bench does THE THING THAT BREAKS, and it is the reason the net was green:
 *    moves the mouse continuously (20 `pointerMove` a second, REAL and visible
 *    Firefox).  Without that the measurement is green and says nothing.
 *
 * | binary               | input | heartbeats | LONGEST `da_ms` |
 * |---|---|---|---|
 * | `cd8a3aec` (before), gnome, 3 min | 14 639 | **22** | **46 192 ms** |
 * | `3fa352a2` (after),  kde,  8 min | 27 797 | **508** | **1 102 ms** |
 *
 * ⚠ The two `da_ms=2000` of the cured run are not a skipped heartbeat: it is the
 *   once-a-second line falling at 999 ms and being postponed by one (`ritmo_ciclo()` wants
 *   `>= 1000`).  The heartbeat was there.
 *
 * ⭐ And the number the user looks at: **0 seconds out of 340** without a new
 *    frame (28 844 delivered, 3.5 % missed), against **698 out of 1199 (58 %)**
 *    of the session that opened the hunt.  Longest block: **0 s**.
 *
 * ⭐ The second belt is not decorative: in 8 minutes it came in **2 times**
 *    («the debt … has been on for 1004 ms»), and the keyframe went out **19 ms later**
 *    instead of waiting for the heartbeat.
 *
 * ⚠ And the control run did NOT freeze the screen: the §5.2 debt did not
 *   come on in those 3 minutes.  ⛔ It is the point of the defect — TWO
 *   things are needed together, and that is why a green is never enough to exclude it.  What
 *   the control proves is the MECHANISM: 46 seconds without a heartbeat, that is 46
 *   seconds in which nobody could request a keyframe (nor make §5.3
 *   or §4.6 expire). */
static void batti_fra(wt *w, uint64_t ms)
{
	ngtcp2_tstamp ora = ngtcp2_conn_get_timestamp(w->conn);
	ngtcp2_tstamp quando = ora + ms * NGTCP2_MILLISECONDS;

	if (w->battito_ms && w->battito > ora && w->battito < quando)
		quando = w->battito;

	w->battito_ms = ms;
	w->battito = quando;
}

ngtcp2_tstamp wt_battito_ns(const wt *w)
{
	ngtcp2_tstamp b = w->battito_ms ? w->battito : UINT64_MAX;

	/* ⛔⭐ AND THE TEST TONE HAS A CLOCK OF ITS OWN — `[M]` 17 Aug 2026.
	 *
	 *     First run against the test client: **9 blocks in 3 seconds**,
	 *     where PCM at 5 ms wants 600.  ⚠ The content was right (960 bytes,
	 *     codec 2, zero discards): what was wrong was the RATE, because the blocks are
	 *     generated by `wt_batti()` and `wt_batti()` wakes up with QUIC's heartbeat —
	 *     which is hundreds of milliseconds long.
	 *
	 * ⭐ The cure is NOT raising the per-pass cap: that would produce a
	 *    burst followed by a silence, that is the same number of blocks with
	 *    one more defect.  It is telling the loop WHEN the next block is
	 *    due.
	 *
	 * ⚠ And it dies with the test source: real audio is paced by **PipeWire**,
	 *   which sits in the `poll` with a descriptor of its own and wakes the loop by itself.
	 */
	/* ⛔⛔ THE CONDITIONS ARE THE SAME AS `tono_passo()`, AND IT IS A CURE —
	 *      finding 4 of the adversarial review of 17 Aug 2026.
	 *
	 *      Here there was `audio_prova_hz && w->audio_acceso`, and there there are also
	 *      `w->chiusura < 0` and `w->rcp`.  ⛔ **In every case covered by one
	 *      guard and not by the other this function returned an instant IN THE
	 *      PAST and nobody moved it any more** — because the only one moving it is
	 *      `tono_passo`, which instead returned at once.
	 *
	 *      ⇒ `trasporto_attesa_ms()` read «already expired», `poll()` returned
	 *      with **timeout 0**, `wt_batti()` changed nothing, and it all
	 *      started again: **tight loop at 100 % CPU**.
	 *
	 * ⚠ And the case is not a lab one: a BROWSER closes the WebTransport
	 *   session and **keeps the QUIC connection alive** — it is written in
	 *   this very file — and there `w->rcp` becomes NULL while `audio_acceso`
	 *   stays on, because no line switches it off.  ⛔ The server would have
	 *   spun idle until QUIC's idle cap, and longer if
	 *   the browser kept it alive with PINGs.
	 *
	 * ⭐ And the lesson is that two guards for the same fact diverge: whoever
	 *    touches `tono_passo` must touch this one too. */
	/* ⛔⛔ AND A DATAGRAM IN THE QUEUE WANTS TO BE RETRIED AT ONCE — `[M]` 17 Aug
	 *      2026, from the user's REAL session: *«it's as awful as before»*.
	 *
	 *      With congestion in order (`cwnd_left` 40 KB) **22 %** of the
	 *      blocks did not leave all the same.  ⛔ The reason was not the refusal: it was
	 *      that **nobody scheduled a second attempt**.  A refused
	 *      block stayed in the queue until something else made the
	 *      connection write — that is the arrival of the NEXT block, 20 ms later.
	 *      ⇒ The retry was there, its clock was not.
	 *
	 * ⚠ One millisecond, no more: it is the order of magnitude in which the pacer
	 *   changes its mind, and it is 1/20 of an Opus block.  ⛔ And the cap on
	 *   wake-ups is set by the queue: when it is empty this line does not fire.
	 *
	 * ⭐ And it is the same cure the test tone already had — written there and
	 *    not here, because back then real audio did not exist.  The defect was
	 *    inside that asymmetry. */
	if (w->ndgram > 0 && w->chiusura < 0) {
		ngtcp2_tstamp t = ngtcp2_conn_get_timestamp(w->conn) + NGTCP2_MILLISECONDS;
		if (t < b)
			b = t;
	}

	if (audio_prova_hz && w->audio_acceso && w->chiusura < 0 && w->rcp) {
		/* ⛔ The first block is DUE AT ONCE.  `[M]` 17 Aug 2026: without
		 *    this line the tone waited for the normal heartbeat before
		 *    starting, and **exactly one second** was missing at the head of every
		 *    take — 2.01 s out of 3, 4.01 out of 5, 9.01 out of 10.  ⚠ The symptom
		 *    looked like a yield (67 %, 80 %, 90 %), and a yield makes one look for the
		 *    defect in the RATE; it was instead a start-up delay, which sits in a
		 *    completely different place. */
		if (!w->tono_prossimo_us)
			return 0;
		ngtcp2_tstamp t = w->tono_prossimo_us * NGTCP2_MICROSECONDS;
		if (t < b)
			b = t;
	}
	return b;
}

const char *wt_stato_rcp(const wt *w)
{
	return w->rcp ? rcp_stato_nome(w->rcp) : "(none)";
}

/* ⛔ WHY it still has something to say — and it is not a luxury: without this line
 *    «the closing capsule is not mature yet» and «the bytes do not go out» look
 *    the same, and whoever stops the service reads «1 sessions still have
 *    bytes in the queue» without knowing which of the two it is.
 * ⚠ `[M]` 11 Aug 2026: the `server-in-chiusura` case of B7 is red precisely
 *   here — §3.1 point 3 absent at shutdown — and the diagnosis stopped
 *   in front of this ambiguity. */
const char *wt_perche_ha_da_dire(const wt *w)
{
	if (!w)
		return "(no session)";
	if (w->chiusura >= 0 && !coda_vuota(w))
		return "closing capsule pending AND queue not empty";
	if (w->chiusura >= 0) {
		/* ⛔ AND HOW MUCH IS LEFT, or the diagnosis stops here — 11 Aug 2026.
		 *    «Not mature yet» after 2 s, when 0.5 are enough, has two
		 *    opposite explanations: the clock does not run, or it runs and gets
		 *    RESET.  The number separates them; the adjective does not. */
		static char detto[220];
		ngtcp2_tstamp ora = ngtcp2_conn_get_timestamp(w->conn);
		snprintf(detto, sizeof detto,
		         "closing capsule not mature yet (queue empty) — "
		         "chiusura=%#04x · chiusura_da=%s · %lld ms left · "
		         "heartbeat in %lld ms",
		         (unsigned)w->chiusura,
		         w->chiusura_da ? "armed" : "⛔ NEVER ARMED",
		         w->chiusura_da
		             ? (long long)(((long long)w->chiusura_da - (long long)ora)
		                           / (long long)NGTCP2_MILLISECONDS) : 0LL,
		         w->battito_ms
		             ? (long long)(((long long)w->battito - (long long)ora)
		                           / (long long)NGTCP2_MILLISECONDS) : -1LL);
		return detto;
	}
	if (!coda_vuota(w))
		return "output queue not empty";
	return "nothing";
}

bool wt_ha_da_dire(const wt *w)
{
	/* ⛔ And datagrams count: without this line the audio blocks
	 *    would stay in the queue until the next thing to send, that is the
	 *    sound would come out **in jerks dictated by the video**.  ⚠ It is the same shape
	 *    as the defect of `MOVIMENTO_ATTESA_S` (`CODER.md` §1-bis): the rhythm of
	 *    one link becoming the delay of another link. */
	return w->chiusura >= 0 || !coda_vuota(w) || w->ndgram > 0;
}

/* ------------------------------------------------------------------------ */
/* ⭐ DATAGRAMS — the audio of §6.3.                                          */

/* ⭐ The variable-length integer for the RFC 9297 prefix is the one that
 *    already exists — `varint_scrivi()`, at the top of this file.  ⛔ A second
 *    copy had been written here, and it was the compiler that noticed:
 *    two implementations of the same rule diverge, and it is the shape of the
 *    defect the three-copy check (R12.3) exists to prevent between
 *    files — there is no reason to admit it within the same file. */

/* How many bytes the peer accepts in a DATAGRAM, `0` = it accepts none at all. */
static uint64_t dgram_tetto_del_pari(const wt *w)
{
	const ngtcp2_transport_params *p;
	if (!w->conn)
		return 0;
	p = ngtcp2_conn_get_remote_transport_params(w->conn);
	return p ? p->max_datagram_frame_size : 0;
}

/*
 * Enqueues an already composed payload (RFC 9297 prefix included).
 *
 * ⛔ When the queue is full THE OLDEST is thrown away — §6.3 and the lesson of
 *    v1.  ⚠ And it is counted: «audio does not arrive» and «audio arrives and I drop it»
 *    must have two different lines, which is exactly the reason why
 *    `trasporto.c` wrote the incoming discard since phase 1.
 */
static bool dgram_accoda(wt *w, const uint8_t *d, size_t n)
{
	size_t coda;

	if (n > WT_DGRAM_BYTE) {
		/* ⛔ AND IT IS COUNTED AND WRITTEN, instead of returning `false` and hoping
		 *    the caller looks — finding 13 of the review of 17 Aug
		 *    2026.  Today this road is unreachable because `audio_a_una`
		 *    checks the same cap three lines earlier: ⚠ **two checks for
		 *    a single rule, and only one of the two could say it had
		 *    fired**.  The day the second caller arrives — and with
		 *    `figlio.c` it is arriving — a block would vanish without a trace. */
		w->audio_buttati++;
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ %s: audio block of %zu bytes beyond the cap of %u — "
		                 "DROPPED.  ⚠ If this line appears, the cap has been "
		                 "checked in two places and one of the two is wrong",
		                 w->provenienza, n, (unsigned)WT_DGRAM_BYTE);
		return false;
	}

	if (w->ndgram == WT_DGRAM_MAX) {
		w->dgram_testa = (w->dgram_testa + 1) % WT_DGRAM_MAX;
		w->ndgram--;
		w->audio_buttati++;
	}
	coda = (w->dgram_testa + w->ndgram) % WT_DGRAM_MAX;
	memcpy(w->dgram[coda].d, d, n);
	w->dgram[coda].n = n;
	/* ⭐ THE STAMP — see `WT_DGRAM_ZITTO_MAX_MS`.  ⛔ It is here and not elsewhere
	 *    because «when it entered the queue» is a fact that exists only at
	 *    this point: afterwards, the slot is reused and memory does not remember. */
	w->dgram[coda].nato = w->ts_ora;
	w->ndgram++;
	return true;
}

static void dgram_togli_testa(wt *w)
{
	if (w->ndgram == 0)
		return;
	w->dgram_testa = (w->dgram_testa + 1) % WT_DGRAM_MAX;
	w->ndgram--;
}

/*
 * Writes ONE datagram in a packet of its own.
 *
 * ⛔ One per packet, and it is not laziness: `RCP.md` §6.3 says «one datagram, one
 *    Opus block», so the packet has nothing to coalesce that is
 *    worth the risk.  ⚠ Mixing `writev_datagram` and `writev_stream` in the
 *    same packet demands the discipline of the `MORE` flag on both, and
 *    a mistake there does not produce a fault: it produces valid bytes in the wrong
 *    order.
 *
 * Returns `true` when the packet has been composed and must be sent.
 */
static bool dgram_scrivi_uno(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi,
                             uint8_t *dest, size_t destlen, ngtcp2_tstamp ts,
                             ngtcp2_ssize *nfuori)
{
	int accettato = 0;
	ngtcp2_vec v;
	ngtcp2_ssize nw;
	uint64_t eta_ms, zitto_ms;

	if (w->ndgram == 0)
		return false;

	/* ⛔⭐ THE TWO QUANTITIES, AND ONLY ONE OF THE TWO DECIDES — ⇒ the box of
	 *     `WT_DGRAM_ZITTO_MAX_MS`, which says why it is not the one it seems.
	 *
	 *   · `zitto_ms` — how long the CONNECTION has not put a datagram in a
	 *     packet.  It is the one on which we drop.
	 *   · `eta_ms`   — how many ms old the BLOCK AT THE HEAD is.  It decides nothing: it goes
	 *     in the log line, and it is the quantity the old comment
	 *     promised and nobody had ever read.
	 *
	 * ⚠ Both are worth ZERO when their clock has not started (`nato`
	 *   or `dgram_zitto_da` at zero).  ⛔ A clock that has not started and one that has expired
	 *   must not look the same: the wrong look would drop the
	 *   first audio block of every session. */
	eta_ms = (w->dgram[w->dgram_testa].nato && ts > w->dgram[w->dgram_testa].nato)
	             ? (ts - w->dgram[w->dgram_testa].nato) / NGTCP2_MILLISECONDS
	             : 0;
	zitto_ms = (w->dgram_zitto_da && ts > w->dgram_zitto_da)
	               ? (ts - w->dgram_zitto_da) / NGTCP2_MILLISECONDS
	               : 0;

	/* ⛔⭐ AND IT IS NOT RETRIED WITHIN THE SAME PASS — `[M]` 17 Aug 2026.
	 *
	 *     `ngtcp2_conn_write_aggregate_pkt2` calls this function back several
	 *     times to compose a batch of packets, **with the same `ts`**.  The
	 *     first cap on deferrals was all used up in there, in one
	 *     microsecond: eight deferrals and then the block dropped, without
	 *     **an instant** having passed in which the pacer could change its mind.
	 *     ⇒ 1064 datagrams dropped all the same, with 8008 «successful» deferrals in a
	 *     count that seemed to say the opposite.
	 *
	 * ⭐ The pacer decides on TIME: if it refused at this `ts`, it will refuse
	 *    now too.  We return at once, without asking — and the deferral holds
	 *    for a whole pass, which is the unit in which the pacer moves. */
	if (w->dgram_rimando_ts == ts)
		return false;

	/* ⭐ PHASE 9 — AND HERE THE DEFECT OF 23 AUGUST IS NOT PRESENT, for two reasons that
	 *    must be written down so they are not lost:
	 *
	 *      1. `w->dgram[]` is a ring of FIXED arrays inside `wt`: there is
	 *         no `free()` that could come before ngtcp2 — the memory
	 *         dies with the session;
	 *      2. §6.3: a datagram is NOT RETRANSMITTED.  ngtcp2 serialises it
	 *         into the packet during THIS call (`WRITE_MORE` means
	 *         «it is already inside») and does not reread the source any more.
	 *
	 * ⚠ The slot is reused (`dgram_accoda()` overtakes the oldest when
	 *   the ring is full), and it holds only because of point 2: the day
	 *   datagrams became retransmittable, this would be the same defect
	 *   as `coda_uccidi()` with another face. */
	v.base = w->dgram[w->dgram_testa].d;
	v.len = w->dgram[w->dgram_testa].n;

	/* ⛔⛔ `MORE` AND NOT `NONE`, AND IT IS THE CURE FOR THE DEFECT THE USER HEARD.
	 *
	 *      `[M]` 17 Aug 2026, the user's REAL session from another machine:
	 *      **1578 blocks sent and 1606 REFUSED** — more than half
	 *      of the audio did not leave — and the diagnostic line stated the cause without
	 *      leaving margins: **`cwnd_left = 0`**.
	 *
	 *      ⇒ It was not the network and it was not the pacer: it was **the video eating
	 *      the whole congestion window**.  A 230-byte datagram did not
	 *      find room because it asked for **a packet of its own**, and a packet
	 *      of its own the window never granted.
	 *
	 * ⭐ With `MORE` the datagram does not ask for a packet: **it enters the one the
	 *    video is already writing**.  A 1452-byte packet carrying pixels
	 *    has room to spare for 230 bytes of sound, and that packet the
	 *    window is already granting.  ⇒ Audio travels where video passes
	 *    instead of contending the place with it.
	 *
	 * ⛔⛔⛔ AND `PADDING` IS NOT A DETAIL: IT IS THE CURE — the insight is the user's
	 *       («maybe the datagram is too small?»), and ngtcp2's manual
	 *       proves it right in one line:
	 *
	 *         «This function only writes multiple packets if **the first packet
	 *          is path_max_tx_udp_payload_size bytes long**.»
	 *         «Because GSO requires that the aggregated packets have the same
	 *          length, NGTCP2_WRITE_DATAGRAM_FLAG_PADDING is recommended.»
	 *
	 *       Our datagram is the **first** packet of every pass, and it is
	 *       ~250 bytes instead of full.  ⇒ **It collapses the whole GSO batch
	 *       to a single packet**: it is not audio that does not fit, it is audio that
	 *       — small and first — **chokes the whole writing, its own and the video's**.
	 *
	 * ⚠ `[M]` 17 Aug 2026, the user's real session: `cwnd_left` 33-56 KB
	 *   free, `pacer quantum` 14440 constant, and **839 blocks refused out of
	 *   2278**.  Neither congestion nor buffer: it was the geometry of the batch.
	 *
	 * ⭐ With `MORE` the video fills the packet; with `PADDING` it gets
	 *    filled anyway when the video has nothing to put in it.  The two
	 *    together: audio does not pay for the filling when there is traffic, and does not
	 *    choke the batch when there is none.
	 *
	 * ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔⛔ MAKING THIS `PADDING` CONDITIONAL WAS TRIED ON 24 AUG 2026, AND
	 *       **IT IS NOT DONE**.  Here is why, with the numbers, for the next one who
	 *       thinks it over — who will be someone with the same good idea.
	 * ═══════════════════════════════════════════════════════════════════════
	 *
	 * The idea: when the queue holds ONE datagram only and no stream byte, the
	 * GSO batch is one packet by construction, and filling it protects
	 * nothing — it just costs.  ⚠ The sum looked big: an Opus block is
	 * ~290 bytes inside a 1 441-byte packet, that is 1 150 bytes thrown away 50 times
	 * a second.  ⇒ Written (`w->ndgram > 1 || !coda_vuota(w)`), built,
	 * measured paired.  `[M]` 24 Aug 2026, bench NR12, port 7981, smooth
	 * `lo`, STILL desktop with the tone at 440 Hz — that is REAL audio and motionless
	 * video, the only case in which the condition can bite — 25 s per run,
	 * two runs per arm, same binary except for this line:
	 *
	 *   codec  filling       kbit/s on wire    bytes/packet     blocks lost
	 *   -----  ------------  ---------------   --------------   -------------
	 *   Opus   always          557.7 / 556.5        1 441              0
	 *   Opus   conditional     556.9 / 555.8        1 441 / 1 442      0
	 *   Opus   **NEVER**       556.4                1 441              0
	 *   PCM    always        2 221.7 / 2 222.0      1 443 / 1 442      0
	 *   PCM    conditional   1 988.0 / 1 987.4      1 292 / 1 290      0
	 *
	 * ⛔⛔ **ON OPUS THE GAIN IS ZERO — and not «small»: ZERO.**  The line that
	 *      proves it is the third: with `PADDING` **never** requested the packet
	 *      stays at 1 441 bytes.  ⇒ It is not this line that fills it.
	 *
	 * ⭐⭐⭐ AND WE KNOW WHO FILLS IT — `[R]`, and it is the discovery this test
	 *      bought: `wt_scrivi()` requests
	 *      **`NGTCP2_WRITE_STREAM_FLAG_PADDING` at EVERY stream write**.
	 *      When the datagram returns `NGTCP2_ERR_WRITE_MORE` the packet stays
	 *      OPEN, this function returns `false`, and the stream loop
	 *      right after closes it — filling it.  ⇒ The filling of a
	 *      still session **is not the datagram's: it is the stream's**, and whoever
	 *      wanted to remove it must go there, not here.
	 *      ⚠ `09-b84-audio-silenzio.py` attributed it to this line: it was a
	 *        deduction, and it has been disproved.
	 *
	 * ⭐ On PCM instead the condition bites (−10.5 %), and one sees why: at 200
	 *    blocks a second the datagram CLOSES the packet by itself (`nw > 0`),
	 *    this function returns `true` and the stream loop never runs.
	 *    ⚠ But PCM is not what the product negotiates (`[M]` the user's real session
	 *      says `audio.codec=opus` four times out of four), and the
	 *      new default — audio silence ON — removes datagrams
	 *      altogether on a still desktop: **0.0 datagrams a second**, `[M]` 09-b84.
	 *    ⇒ One more condition to maintain, inside the most delicate box
	 *      of the file, for a gain that on the real codec is zero and on the other is worth
	 *      a tenth of a bandwidth that on a still desktop is not there.  **It is not done.**
	 *
	 * ⛔ `NGTCP2_ERR_WRITE_MORE` here is not an error: it means «the datagram is
	 *    inside, keep filling the packet».  Whoever read it as a
	 *    fault would drop a block already sent. */
	nw = ngtcp2_conn_writev_datagram(w->conn, path, pi, dest, destlen, &accettato,
	                                 NGTCP2_WRITE_DATAGRAM_FLAG_MORE |
	                                     NGTCP2_WRITE_DATAGRAM_FLAG_PADDING,
	                                 ++w->dgram_id, &v, 1, ts);
	if (nw == NGTCP2_ERR_WRITE_MORE) {
		/* ⭐ The block is in the packet being composed: it is removed from the queue. */
		w->audio_spediti++;
		w->dgram_zitto_da = 0; /* ⭐ I am no longer mute */
		dgram_togli_testa(w);

		/* ⛔⛔⛔ AND WE KEEP SLIPPING THEM IN, as long as they fit — `[M]` 17
		 *       Aug 2026, from the user's session with real video:
		 *       the child produces **50 blocks a second** and the server
		 *       refuses **25 a second**.  ⚠ Exactly half, and the
		 *       precision of that number is the clue: it is not congestion,
		 *       it is **arithmetic**.
		 *
		 *       I was sending **a single datagram per write pass**, and the
		 *       passes are ~25 a second.  ⇒ One went through and one stayed in the
		 *       queue, forever, until I dropped it after 64 deferrals.
		 *       ⛔ The cap was neither the network nor the pacer: it was **my
		 *       loop**, which offered them one at a time.
		 *
		 * ⚠ And there was room to spare: a packet is **1452 bytes** and an
		 *   Opus block measures **230**.  Six fit in it, and the video frames
		 *   of this scene are 70-1300 bytes — that is the packet
		 *   stayed half empty while audio was being dropped. */
		while (w->ndgram > 0) {
			ngtcp2_vec v2;
			int acc2 = 0;
			ngtcp2_ssize nw2;

			v2.base = w->dgram[w->dgram_testa].d;
			v2.len = w->dgram[w->dgram_testa].n;
			nw2 = ngtcp2_conn_writev_datagram(
				w->conn, path, pi, dest, destlen, &acc2,
				NGTCP2_WRITE_DATAGRAM_FLAG_MORE |
					NGTCP2_WRITE_DATAGRAM_FLAG_PADDING,
				++w->dgram_id, &v2, 1, ts);
			if (nw2 == NGTCP2_ERR_WRITE_MORE) {
				w->audio_spediti++;
				w->dgram_zitto_da = 0;
				dgram_togli_testa(w);
				continue; /* there is still room: go on */
			}
			if (nw2 > 0) {
				/* The packet has closed.  ⛔ If it also took this
				 *    block it is removed; in any case the packet MUST BE
				 *    SENT — dropping it would take the acknowledgements away. */
				if (acc2) {
					w->audio_spediti++;
					w->dgram_zitto_da = 0;
					dgram_togli_testa(w);
				}
				*nfuori = nw2;
				return true;
			}
			break; /* `0` or an error: retry at the next pass */
		}
		return false;
	}
	if (nw < 0) {
		/* ⛔ AND HERE THE CONNECTION IS NOT KILLED.  §6.3 is explicit in the
		 *    opposite direction — «closing the connection for a corrupt packet
		 *    would be a punishment of the network, not of the sender» — and the same
		 *    reason holds outgoing: an audio block that does not leave is not a
		 *    reason to take the desktop away from whoever is using it. */
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ %s: datagram of %zu bytes NOT written (%s) — the block "
		                 "is DROPPED (§6.3: no retransmission).  Sent %llu, "
		                 "dropped %llu",
		                 w->provenienza, v.len, ngtcp2_strerror((int)nw),
		                 (unsigned long long)w->audio_spediti,
		                 (unsigned long long)(w->audio_buttati + 1));
		w->audio_buttati++;
		dgram_togli_testa(w);
		return false;
	}

	if (accettato) {
		w->audio_spediti++;
		w->dgram_zitto_da = 0;
		dgram_togli_testa(w);
	} else if (zitto_ms < WT_DGRAM_ZITTO_MAX_MS) {
		/* ⛔⛔ IT IS NOT DROPPED: IT IS DEFERRED — and the difference is worth 38 % of the audio.
		 *
		 *      `[M]` 17 Aug 2026, REAL audio in PCM with video on:
		 *      **1163 datagrams refused out of 3001**, and the judge read
		 *      **464 Hz instead of 440** with purity 0.29 — because concatenating
		 *      what is left makes the phase jump every two blocks.  ⚠ The sound
		 *      was not «with a few holes»: it was **another sound**.
		 *
		 * ⛔⭐ AND THE CAUSE WAS NOT THE ONE WRITTEN HERE.  The comment said «it did not
		 *     fit in the packet, so it would never fit».  The measurement
		 *     says the opposite: `cwnd_left` = **12 198 bytes** against 973
		 *     requested, destlen 1452.  ⇒ It is neither the buffer nor
		 *     congestion: it is QUIC's **pacer**, which says «not now».
		 *     And «not now» becomes «never» only if we drop it ourselves.
		 *
		 * ⚠ And the cap stays: the queue holds eight blocks, and whoever does not fit is
		 *   dropped anyway (§6.3).  Deferring is not accumulating — it moves the
		 *   block by a few hundred microseconds, not by half a second.
		 *
		 * ⭐ AND SINCE 24 AUG 2026 THE CONDITION ABOVE IS A TIME, not a
		 *    rev counter of passes (⇒ `WT_DGRAM_ZITTO_MAX_MS`).
		 *    `audio_rimandati` stays what it always was — how many times the
		 *    pacer said «not now» — and ⚠ it is NOT a quantity to
		 *    judge by: `[M]` 24 August, `casa-cattiva`, **2.2 million in 26 s**,
		 *    because it counts the passes of the event loop, not the blocks. */
		w->audio_rimandati++;
		w->dgram_rimando_ts = ts;
		/* ⛔ The silence clock starts at the FIRST refusal, not at every
		 *    refusal: here a duration is measured, not an instant. */
		if (!w->dgram_zitto_da)
			w->dgram_zitto_da = ts;
		/* ⛔⛔⛔ AND WE DO NOT RETURN AT ONCE: IF THERE IS A PACKET, IT MUST BE SENT.
		 *
		 *       `[M]` 17 Aug 2026, and this was the defect that held
		 *       up all the others.  ngtcp2's manual says it and I
		 *       had read it wrong:
		 *
		 *         «The function returns the written length of packet … because
		 *          packet is nearly full and the library decided to make a
		 *          complete packet.  **|*paccepted| might be zero or nonzero**.»
		 *
		 *       ⇒ `nw > 0` with `accettato == 0` means: **the datagram did not
		 *       get in, BUT A COMPLETE PACKET HAS BEEN WRITTEN** — with
		 *       the acknowledgements and the video bytes inside.  ⛔ Returning `false` here
		 *       that packet was **thrown away**: the pass went on and
		 *       rewrote `dest` from scratch.
		 *
		 * ⛔⛔ The price was not the audio: it was **the ACKNOWLEDGEMENTS**.  Throwing away one
		 *      packet in five that carries ACKs makes QUIC get the measurement
		 *      of the path wrong — and from there come the pacer that does not open, the
		 *      window that does not grow and the hiccuping rate.  ⚠ That is the
		 *      defect **fabricated** the symptoms I was chasing. */
	} else {
		/* ⛔⭐ HERE THE DEFERRAL CAN NO LONGER BE DONE, AND NOW WE KNOW WHY.
		 *
		 *     Until 23 Aug 2026 this branch was reached when a
		 *     rev counter OF THE CONNECTION had gone past 4096, and the comment
		 *     said «the block is old» without anyone having looked at
		 *     the age of that block (⇒ the box of `WT_DGRAM_ZITTO_MAX_MS`).
		 * ⭐ Now one gets here for a fact MEASURED IN MILLISECONDS: for
		 *    `WT_DGRAM_ZITTO_MAX_MS` this connection has not managed to put
		 *    a single datagram in a single packet.  ⇒ The oldest in the queue
		 *    will not leave in time, and it is dropped — and that is what §6.3 wants:
		 *    late sound is of no use to anyone.
		 * ⚠ And the line below ALSO carries the block's true age, which does not
		 *   decide: it is there to be proved wrong (⇒ the box of the cap). */
		w->audio_rifiutati++;
		/* ⛔ `registro_dice` and not `registro_dettaglio`: the second is
		 *    SUPPRESSED when chatter is off, that is in every
		 *    normal installation — and then «audio dropped» and «audio never
		 *    arrived» look the same again, which is exactly
		 *    what the two counters exist to prevent (finding 6).
		 * ⚠ With a backstop: one line every 100 discards, or a continuous fault
		 *   would fill the log instead of telling it. */
		if (w->audio_rifiutati == 1 || w->audio_rifiutati % 100 == 0)
			/* ⛔⭐ AND THE CAUSE IS ASKED, instead of listing three.
			 *
			 *     ngtcp2 gives `0` for three different reasons — congestion
			 *     control, buffer space, amplification limit — and
			 *     the first draft of this line listed all three,
			 *     that is it named none of them (finding 10 of the review).
			 *     ⚠ `LEZIONI.md` §1.9: a deduction written next to a
			 *     number nobody measured.
			 *
			 * ⭐ `cwnd_left` separates them: if it is **zero** it is congestion, and
			 *    then dropping is the wrong thing to do — that block
			 *    would get in within a few hundred microseconds.  If it is
			 *    **large**, the cause is another and must be looked for elsewhere. */
			registro_dice_di(REG_WT, wt_chi(w),
			                 "⚠ %s: datagram of %zu bytes NOT put in the packet "
			                 "(destlen %zu) — dropped because no datagram has gone out for "
			                 "%llu ms, and the cap is %u (§6.3).  ⚠ and the block I "
			                 "drop is %llu ms old: if the two numbers diverge, the "
			                 "queue is not refreshing.  Refused %llu.  "
			                 "⛔ cwnd_left = %llu bytes, pacer quantum = %zu%s",
			                 w->provenienza, v.len, destlen,
			                 (unsigned long long)zitto_ms,
			                 (unsigned)WT_DGRAM_ZITTO_MAX_MS,
			                 (unsigned long long)eta_ms,
			                 (unsigned long long)w->audio_rifiutati,
			                 (unsigned long long)ngtcp2_conn_get_cwnd_left(w->conn),
			                 ngtcp2_conn_get_send_quantum(w->conn),
			                 ngtcp2_conn_get_cwnd_left(w->conn) < v.len
			                     ? " ⇒ IT IS CONGESTION: the block does not fit NOW"
			                     : " ⇒ it is NOT congestion: look at the quantum");
		dgram_togli_testa(w);
	}

	if (nw > 0) {
		*nfuori = nw;
		return true;
	}
	return false;
}

/* ------------------------------------------------------------------------ */
/* 1. Rewriting the SETTINGS.                                                */

static size_t riscrivi_impostazioni(wt *w, const nghttp3_vec *vec, size_t veccnt)
{
	uint8_t orig[512];
	size_t origlen = 0;
	uint64_t tipo_stream = 0, tipo_frame = 0, lung = 0;
	size_t n, p, o;
	uint8_t aggiunta[64], testa[16];
	size_t a = 0, t = 0;

	for (size_t i = 0; i < veccnt; i++) {
		if (origlen + vec[i].len > sizeof orig) {
			registro_dice_di(REG_WT, wt_chi(w),
			                 "⛔ nghttp3's SETTINGS is longer than "
			                 "%zu bytes: not rewriting it",
			                 sizeof orig);
			return 0;
		}
		memcpy(orig + origlen, vec[i].base, vec[i].len);
		origlen += vec[i].len;
	}
	if (origlen < 3)
		return 0;

	/* ⛔ Every step has a foothold, and if the foothold is not there we do NOT rewrite
	 *    blindly: we say so and leave it alone.  The server will stay without
	 *    WebTransport, and the measurement will see it at once — which is what
	 *    `DECISIONI.md` §6.4 asks to re-test at every update of
	 *    nghttp3. */
	n = varint_leggi(&tipo_stream, orig, origlen);
	if (n == 0 || tipo_stream != 0x00) {
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ the control stream does not start with 0x00 (it is "
		                 "%llu): touching nothing",
		                 (unsigned long long)tipo_stream);
		return 0;
	}
	p = n;

	n = varint_leggi(&tipo_frame, orig + p, origlen - p);
	if (n == 0 || tipo_frame != 0x04) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ the first frame is not SETTINGS (it is %llu)",
		                 (unsigned long long)tipo_frame);
		return 0;
	}
	p += n;

	n = varint_leggi(&lung, orig + p, origlen - p);
	if (n == 0)
		return 0;
	p += n;

	if (p + lung != origlen) {
		/* There is something else after SETTINGS, or SETTINGS arrived in pieces. */
		registro_dice_di(REG_WT, wt_chi(w), "⛔ SETTINGS is not all here (%zu + %llu != %zu)",
		                 p, (unsigned long long)lung, origlen);
		return 0;
	}

	a += varint_scrivi(aggiunta + a, WT_ENABLE_WEBTRANSPORT);
	a += varint_scrivi(aggiunta + a, 1);
	a += varint_scrivi(aggiunta + a, WT_MAX_SESSIONS);
	a += varint_scrivi(aggiunta + a, 1);

	t += varint_scrivi(testa + t, 0x00); /* the stream type */
	t += varint_scrivi(testa + t, 0x04); /* SETTINGS */
	t += varint_scrivi(testa + t, lung + a);

	if (t + lung + a > sizeof w->impbuf) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ SETTINGS too big for the buffer");
		return 0;
	}

	o = 0;
	memcpy(w->impbuf + o, testa, t);
	o += t;
	memcpy(w->impbuf + o, orig + p, (size_t)lung);
	o += (size_t)lung;
	memcpy(w->impbuf + o, aggiunta, a);
	o += a;
	w->impbuf_len = o;

	registro_dice_di(REG_WT, wt_chi(w),
	                 "⭐ SETTINGS rewritten — %zu bytes of nghttp3 + %zu of ours "
	                 "(ENABLE_WEBTRANSPORT and WT_MAX_SESSIONS)",
	                 origlen, a);
	return origlen;
}

/* ------------------------------------------------------------------------ */
/* RCP: the four hooks, which are the only thing the protocol knows of the     */
/* world below.                                                               */

static void manda_controllo(wt *w, const uint8_t *dati, size_t len);
static void chiudi_sessione(wt *w, uint8_t motivo);
/* ⛔ Declared here because `regola_battito()` calls it and the body comes after the
 *    census of who is watching (`video_guarda_qualcuno()`), which it needs. */
static void cattura_spegni_se_sola(wt *w, const char *perche);

static void gancio_manda(void *ctx, const uint8_t *dati, size_t len)
{
	manda_controllo((wt *)ctx, dati, len);
}

static void gancio_chiudi(void *ctx, uint8_t motivo)
{
	chiudi_sessione((wt *)ctx, motivo);
}

/* ⛔⭐ HERE WE STOP THROWING THE CONTEXT AWAY — 25 Aug 2026, R10-A4 / P6.
 *
 *     Until yesterday this function did `(void)ctx;`: `rcp.c` handed it the
 *     session and it threw it away.  ⛔ And **163 lines out of 163** of `rcp.c` go
 *     through here (`reg(rcp_sessione *s, …)` is the only funnel), among them the most
 *     voluminous of the product — `fotogramma N SPEDITO`, ~38/s **per session**.
 *     `[M]` §6.7: with four real desktops they were attributable at **0.0 %**,
 *     and the blind test — switch off a scene, ask the log who stopped
 *     — gave the right name **0 times out of 4**.
 *
 * ⇒ The identity was already in hand: `ctx` **is** the `wt`, the `wt` carries the
 *   RCP session, and `rcp_utente()` had always existed.  It was thrown away at a single
 *   point, and it is put back at a single point.
 *
 * ⚠ And before authentication the name is NOT there: there the line comes out **mute**.
 *   The origin is not put in its place — not because it is not known, but
 *   because the body of those lines already carries it, and a second field saying
 *   the same thing is volume, not diagnosis. */
static void gancio_registra(void *ctx, const char *riga)
{
	wt *w = (wt *)ctx;
	const char *chi = (w && w->rcp) ? rcp_utente(w->rcp) : NULL;
	registro_dice_di(REG_RCP, chi, "%s", riga);
}

/* ⛔⭐ THIS HOOK IS THE FALLBACK, SINCE 12 AUG 2026 — `DECISIONI.md` §1.10.
 *
 *     ⚠ PAM BLOCKS, and here it blocked the whole loop: one user's
 *       handshake stopped everybody else's and delayed the packets of
 *       whoever was already connected.  `[M]` B8, 11 Aug 2026: **from 1.0 to
 *       2.2 seconds**, and PAM was the one adding them (+1034 ms on the refused against
 *       +84 ms on the admitted — the signature of `pam_faildelay`).
 *
 * ⛔ Now the good road is `gancio_chiedi`, below.  This one stays
 *    connected because `rcp.c` uses it when the helper is not there — and then it is
 *    right that the server works all the same, with less (`CODER.md` §4.2).
 * ⚠ But the fallback IS DECLARED: whoever takes it finds it written in the log
 *   by `rcp.c`, «SYNCHRONOUSLY — the wire stood still». */
static bool gancio_verifica(void *ctx, const char *utente, const char *parola)
{
	wt *w = (wt *)ctx;
	char rhost[64];
	(void)rcp_rhost_da_provenienza(w ? w->provenienza : NULL, rhost,
	                               sizeof rhost);
	return rcp_autentica_da(utente, parola, rhost);
}

/* ⭐⭐ THE GOOD ROAD: one asks, one does not wait — `DECISIONI.md` §1.10.
 *
 * ⛔ Returns `false` when the request has not left, and `rcp.c` treats it
 *    as an immediate NO: invariant I3, failure is a no and not a
 *    maybe. */
static bool gancio_chiedi(void *ctx, const char *utente, const char *parola,
                          uint64_t *pratica)
{
	wt *w = (wt *)ctx;
	if (!w->aiuto)
		return false;
	return aiutante_chiedi(w->aiuto, utente, parola, w->provenienza,
	                       ngtcp2_conn_get_timestamp(w->conn)
	                           / NGTCP2_MILLISECONDS,
	                       pratica);
}

/* ========================================================================== */
/* ⭐⭐ THE FOUR VIDEO CHANNEL HOOKS — `RCP.md` §2.5, §5.1, §6.2.             */
/*                                                                            */
/* Grafted on 12 Aug 2026 by the phase 2 assembly.  The lines had been        */
/* written by `fasi/rapporti/P2-4-filo.md` §5, and ⛔ **they are not in `main.c`**: */
/* `main.c` does not know `rcp_ganci`, the structure is filled by `rcp_avvia()` in */
/* here — the correction to the brief that P2.4 put on record.               */
/*                                                                            */
/* ⛔ THEY ARE FOUR AND NOT ONE because §6.2 says that **how the stream ends is */
/*    part of the message**: FIN ⇒ complete frame, `RESET_STREAM` ⇒           */
/*    incomplete, it is thrown away.  A single hook that «sends a frame» could  */
/*    not tell the difference (shape E8, finding R1.7).                       */
/*                                                                            */
/* ⛔⭐ AND THE WEBTRANSPORT PREAMBLE IS NOT A DETAIL — proposal P18.          */
/*                                                                            */
/*     A WebTransport unidirectional stream starts with the **stream type**   */
/*     (`0x54`) followed by the **session number**, both QUIC                 */
/*     variable-length integers (RFC 9000 §16): on the wire `0x54` is the two  */
/*     bytes `40 54`.  The 28 bytes of §6.2 start AFTER.                       */
/*                                                                            */
/*     ⚠ §2.5 says «the first two bytes of the stream are read, which are in any */
/*       case a `tipo` field» — and on WebTransport it is not true.  A reader who */
/*       applied it to the letter would derive channel `0x40` from EVERY        */
/*       frame and would close with `ERRORE_PROTOCOLLO`.  ⛔ The first live    */
/*       run of `02-filo-cliente.py` ended red exactly there.                 */
/*                                                                            */
/*     ⭐ This file already knew it for INCOMING streams (`smista_uni`,       */
/*        line ~1164): here is the other half, and it is the same `varint_scrivi` */
/*        — not a copy of the two bytes by hand, which the day the session      */
/*        number goes past 63 would become mute and wrong.                    */

/* ⭐⭐ THE SIX INPUT HOOKS — PHASE 4, 14 Aug 2026.
 *
 * ⛔ WHY THEY ARE HOOKS AND NOT DIRECT CALLS, and it is not style: `rcp.c` lives in
 *    TWO folders that the `Makefile` (`GEMELLATI`) demands identical byte for
 *    byte, and the second copy `banchi/01-b3-rcp-innesta.py` slips it inside
 *    ngtcp2's `examples/`, where `input.h` **does not exist**.  An `#include` in
 *    there would switch off B3, B5, B6, B8 and B11 in one go.
 *
 * ⛔ AND WHY THEY GO THROUGH HERE AND NOT STRAIGHT TO THE STAGE: the stage is in
 *    ANOTHER PROCESS (`figlio.c`), which runs as the user and is the only one holding
 *    the graphical session.  These six carry the message up to the bridge of
 *    `main.c`, which is the only one that knows both sides.
 *
 * ⚠ And the return value is the one of `input.h`, THREE states: 0 delivered,
 *   -1 no, 1 «not producible» (the letter only).  ⛔ Here however the third cannot
 *   be told apart — the injection happens beyond the process boundary, and
 *   the answer does not come back.  ⇒ **We answer 0 = «delivered to the
 *   stage»**, and whoever really counts what the compositor TOOK is the
 *   child, which stamps it on the frame (§6.2).  This asymmetry is
 *   declared and not hidden: it is the price of the process boundary. */
static wt_input_richiesta gancio_palco_input;
static void *gancio_palco_input_ctx;

void wt_input_gancio(wt_input_richiesta f, void *ctx)
{
	gancio_palco_input = f;
	gancio_palco_input_ctx = ctx;
}

static int input_al_palco(wt *w, uint32_t id, uint8_t azione, uint16_t codice,
                          int premuto, int32_t a, int32_t b)
{
	const char *mio;
	if (!gancio_palco_input || !w->rcp)
		return -1;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return -1;
	return gancio_palco_input(gancio_palco_input_ctx, mio, id, azione, codice,
	                          premuto, a, b)
	           ? 0
	           : -1;
}

static int gancio_input_puntatore(void *ctx, uint32_t x, uint32_t y)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_PUNTATORE,
	                      0, 0, (int32_t)x, (int32_t)y);
}

static int gancio_input_pulsante(void *ctx, uint16_t codice, int premuto)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_PULSANTE,
	                      codice, premuto, 0, 0);
}

static int gancio_input_rotella(void *ctx, int32_t asse_x, int32_t asse_y)
{
	wt *w = (wt *)ctx;
	/* ⛔ The sign is NOT touched here, and half notches pass whole: `RCP.md`
	 *    §7.3 puts the inversion inside `input_rotella()`, once only.
	 *    Inverting it here too would cancel it. */
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_ROTELLA, 0,
	                      0, asse_x, asse_y);
}

static int gancio_input_lettera(void *ctx, uint32_t carattere)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_LETTERA, 0,
	                      0, (int32_t)carattere, 0);
}

static int gancio_input_posizione(void *ctx, uint16_t codice, int premuto)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_POSIZIONE,
	                      codice, premuto, 0, 0);
}

static int gancio_input_rilascia_tutto(void *ctx)
{
	wt *w = (wt *)ctx;
	/* ⛔⭐ «The rule with the highest damage/cost ratio of the document»
	 *     (`RCP.md` §11).  ⚠ And the count of how many it released stays with the
	 *     CHILD: it does not come back here.
	 *
	 * ⛔⛔ And until 16 Aug 2026 here we answered `0` meaning «the
	 *      request has left» — but the caller wrote it in the log
	 *      as «0 were pressed», which is the face of green on a release
	 *      that never happened.  ⇒ Now we answer `SENZA_CONTO`, which is the
	 *      truth: «done, and ask for the number whoever knows it». */
	return input_al_palco(w, 0, FIGLI_INPUT_RILASCIA_TUTTO, 0, 0, 0, 0) == 0
	           ? RCP_RILASCIO_SENZA_CONTO
	           : RCP_RILASCIO_IMPOSSIBILE;
}

/* ⭐⭐ THE CANVAS HOOK — §7.1, and the whole chain in one line:
 *
 *     `rcp.c` (T_ADATTA_TELA) → this → `main.c` → `figli_ritela()` →
 *     `MSG_INPUT/RITELA` → `cattura_ridimensiona()` → `pw_stream_update_params()`
 *
 * ⛔ And the answer does NOT come back from here: it comes back with a frame at the new size,
 *    which `video_a_una()` reports to `rcp_tela_concessa()`.  ⚠ Whoever read this
 *    `true` as «the canvas has changed» would repeat the mistake `wayvnc` makes with
 *    the outcome of the request (`DECISIONI.md` §5.0-sexies, «the shape rule
 *    stolen from neatvnc»). */
static wt_ritela_richiesta gancio_palco_ritela;
static void *gancio_palco_ritela_ctx;

void wt_ritela_gancio(wt_ritela_richiesta f, void *ctx)
{
	gancio_palco_ritela = f;
	gancio_palco_ritela_ctx = ctx;
}

static wt_disposizione_richiesta gancio_palco_disposizione;
static void *gancio_palco_disposizione_ctx;

void wt_disposizione_gancio(wt_disposizione_richiesta f, void *ctx)
{
	gancio_palco_disposizione = f;
	gancio_palco_disposizione_ctx = ctx;
}

/* ⭐⭐ §5-bis.7 — «set this layout», and it goes to the stage of WHOEVER
 *     ASKED.  ⛔ Invariant I3, identical to the re-canvas: the user's name
 *     is the one PAM admitted on THIS session, never a parameter that
 *     comes from the wire.  A user who could change another's keyboard
 *     would be a small defect with a big face — the other's
 *     desktop that stops answering shortcuts. */
static bool gancio_disposizione(void *ctx, const char *nome)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_disposizione || !w->rcp)
		return false;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_disposizione(gancio_palco_disposizione_ctx, mio, nome);
}

/* ⭐⭐ «DOES THIS MACHINE KNOW THIS LAYOUT?» — and the answer is given by
 *     **XKB**, not by a list written by hand.
 *
 * ⛔ The defect it closes, `[M]` bench `06-b34` case 5, 16 Aug 2026:
 *    `hu`, `tr`, `gr` and `ua` exist in `/usr/share/X11/xkb/symbols/` on
 *    this machine and were refused with `SESSIONE_NON_SERVIBILE`,
 *    with the line «layout unknown to this machine» — a
 *    FALSE sentence.  ⇒ A Hungarian user could not get in.
 *
 * ⭐ And the question is forwarded to `tastiera.c`, which is already the only place of the
 *    product that can compile a layout: asking the same thing twice
 *    in two different ways produces two answers under the same
 *    label (shape E2).  ⚠ It also covers the VARIANT — `it(nonesiste)`
 *    does not compile — which the fixed list did not look at at all. */
static int gancio_disposizione_esiste(void *ctx, const char *nome)
{
	wt *w = (wt *)ctx;
	Tastiera *t;
	char *sbaglio = NULL;

	if (!nome || !*nome)
		return 0;
	/* ⭐ WHOSE LINE IT IS — 27 Aug 2026, the red of C9.  Compiling a
	 *   layout makes `tastiera.c` write two lines of area `tastiera`, and
	 *   here we are in the PARENT: without a name those two lines are identical for
	 *   every tenant attaching, ⛔ and with two live sessions they cannot be
	 *   attributed.  ⚠ The name is the usual one — `wt_chi()`, that is the one
	 *   PAM admitted on this session, never one coming from the wire. */
	t = tastiera_apri_per(nome, wt_chi(w), &sbaglio);
	if (!t) {
		free(sbaglio);
		return 0;
	}
	tastiera_chiudi(t);
	return 1;
}

static bool gancio_ritela(void *ctx, uint32_t larghezza, uint32_t altezza)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_ritela || !w->rcp)
		return false;
	/* ⛔ Invariant I3: the canvas is changed on the stage of WHOEVER ASKED, and the name
	 *    is the one PAM admitted on this session — not a parameter that
	 *    comes from the wire.  A user who could resize another's monitor
	 *    would be a small defect with a big face: the other's
	 *    desktop changing size by itself. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_ritela(gancio_palco_ritela_ctx, mio, larghezza, altezza);
}

/* ⭐⭐ §5.1 — «DOES THIS USER ALREADY HAVE A LOCAL GRAPHICAL SESSION?»
 *
 * ⛔ The hook towards `sentinella.c`, and it lives here for the same reason as the
 *    others: `rcp.c` exists in two copies and the one grafted into ngtcp2 has no
 *    system bus.  Whoever does not connect it does not apply the rule, and `rcp.c`
 *    writes so in the log instead of keeping quiet. */
static wt_locale_richiesta gancio_locale;
static void *gancio_locale_ctx;

void wt_locale_gancio(wt_locale_richiesta f, void *ctx)
{
	gancio_locale = f;
	gancio_locale_ctx = ctx;
}

/* ⭐⭐ AND THE SWEEP HAS ITS OWN, which asks for EVERYONE at once: the why —
 *     with the numbers — is in `webtransport.h` above `wt_locali_ripasso`. */
static wt_locali_ripasso gancio_locali;
static void *gancio_locali_ctx;

void wt_locali_gancio(wt_locali_ripasso f, void *ctx)
{
	gancio_locali = f;
	gancio_locali_ctx = ctx;
}

static bool gancio_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	(void)ctx;
	if (!gancio_locale)
		return false;
	return gancio_locale(gancio_locale_ctx, utente, quale, quanto);
}

/* ⭐ D-001 — the desktop name of this machine for `SESSIONE` (§4.5).
 *    One per PROCESS, like the desktop choice (`sessione.h`): `main.c`
 *    sets it at startup, because `sessione.h` (glib) does not get in here. */
static const char *desktop_nome = "unknown";

void wt_desktop(const char *nome)
{
	desktop_nome = (nome && nome[0]) ? nome : "unknown";
}

static bool gancio_sessione_ripresa(void *ctx)
{
	return ((wt *)ctx)->ripresa;
}

static const char *gancio_desktop(void *ctx)
{
	(void)ctx;
	return desktop_nome;
}

/* ⭐⭐ §7.6 — «the user asked to log out». */
static wt_termina_richiesta gancio_termina;
static void *gancio_termina_ctx;

void wt_termina_gancio(wt_termina_richiesta f, void *ctx)
{
	gancio_termina = f;
	gancio_termina_ctx = ctx;
}

static void gancio_termina_sessione(void *ctx)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_termina || !w->rcp)
		return;
	/* ⛔ Invariant I3: the session of WHOEVER ASKED is terminated, and the name is
	 *    the one PAM admitted on this session — not a parameter that
	 *    comes from the wire.  A user who could close another's
	 *    session would be the dearest defect of the document. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return;
	gancio_termina(gancio_termina_ctx, mio);
}

static bool gancio_video_apri(void *ctx, int64_t *stream, uint64_t *restano)
{
	wt *w = (wt *)ctx;
	uint8_t pre[16];
	size_t n = 0;
	int64_t id = -1;

	if (restano)
		*restano = 0;
	if (!w->conn || w->sessione == -1 || w->guasto)
		return false;
	if (restano)
		*restano = ngtcp2_conn_get_streams_uni_left2(w->conn);

	/* ⚠ `false` here means «not now», and `rcp.c` translates it into «not a
	 *   byte has left» — which is better than half a frame.  ⛔ The most
	 *   likely reason is that the client does not grant more unidirectional
	 *   streams, and then we say how many it has left instead of
	 *   writing «it could not be done». */
	if (ngtcp2_conn_open_uni_stream(w->conn, &id, NULL) != 0) {
		registro_dettaglio_di(REG_WT, wt_chi(w),
		                      "no unidirectional stream for the frame: the "
		                      "client still grants %llu (§2.5 wants one PER "
		                      "frame).  ⚠ The line that decides — delta is dropped, "
		                      "keyframe waits — is written by `rcp.c` (§2.3)",
		                      (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
			                      w->conn));
		return false;
	}

	/* ⛔ How much credit ngtcp2 BELIEVES it has, asked of it and not deduced
	 *    (`LEZIONI.md` §1.6).  ⚠ It serves to tell «the peer gave us no
	 *    credit» from «it gave it and one of the two counts wrong»: on 13 Aug 2026
	 *    a client declaring `initial_max_streams_uni = 6` closed with
	 *    `STREAM_LIMIT_ERROR` after we had opened 11 streams, and without this
	 *    line whose count was wrong could only be guessed. */
	registro_dettaglio_di(REG_WT, wt_chi(w),
	                           "uni stream %ld opened for a frame; ngtcp2 says "
	                           "%llu are left",
	                           (long)id,
	                           (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
		                           w->conn));

	n += varint_scrivi(pre + n, 0x54);
	n += varint_scrivi(pre + n, (uint64_t)w->sessione);

	if (!coda_metti(w, id, pre, n, false)) {
		/* ⛔ The stream has been opened and the preamble is not there: it is RESET
		 *    instead of left open and mute.  A unidirectional stream
		 *    opened and never written holds a place in the client's count and never
		 *    becomes a frame: it is the shape «empty and forbidden look
		 *    the same», from the side of whoever waits. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, id, 0);
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ the WebTransport preamble (%zu bytes) does not fit in the "
		                 "queue: stream %ld reset, no frame",
		                 n, (long)id);
		return false;
	}
	*stream = id;
	/* ⛔ Here and nowhere else: `rcp.c` does not return the identifier
	 *    of the stream it opened, and deriving it from «the last opened on the
	 *    connection» would be guessing.  ⭐ Without this, §5.1 has no
	 *    way of saying WHICH stream to reset when a more recent one leaves. */
	w->video_stream_ultimo = id;
	return true;
}

static bool gancio_video_scrivi(void *ctx, int64_t stream, const uint8_t *dati,
                                size_t len)
{
	/* ⛔ `false` = «they did not get in», and the caller RESETS: `rcp.c` never
	 *    closes with FIN a stream missing a piece, because FIN is
	 *    an assertion (§6.2). */
	return coda_metti((wt *)ctx, stream, dati, len, false);
}

static void gancio_video_fin(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	/* ⛔ The FIN is a queue element like the others, and it is NOT written
	 *    at once: it must go out AFTER the bytes preceding it, and the queue is what
	 *    keeps the order.  ⚠ A `shutdown_stream_write` here would close the
	 *    stream while its bytes are still in the queue — that is it would deliver
	 *    a truncated frame marked «complete». */
	if (!coda_metti(w, stream, NULL, 0, true))
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ the FIN of stream %ld does not fit in the queue: the "
		                 "frame has gone out but is not declared complete",
		                 (long)stream);
}

static void gancio_video_azzera(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	if (!w->conn)
		return;
	/* ⛔ §5.1/§6.2: `RESET_STREAM` ⇒ the client THROWS AWAY what has arrived and
	 *    treats it as a hole. */
	ngtcp2_conn_shutdown_stream_write(w->conn, 0, stream, 0);
	/* ⛔⭐ AND THE BYTES STILL IN THE QUEUE ARE THROWN AWAY HERE, NOT «at the next pass».
	 *
	 *     The previous comment said `wt_scrivi()` would discard them on the
	 *     `NGTCP2_ERR_STREAM_SHUT_WR` branch, and with a single frame per
	 *     session that was true and enough.  ⛔ At sixty a second it is not: those bytes
	 *     stay counted in `byte_in_coda` until the next pass, that is the
	 *     queue cap bites on stuff it has already been decided not to send —
	 *     and §5.1 says **«the bytes not yet sent do not leave at all»**, not
	 *     «they leave later».  ⚠ The count does not go out of step: `coda_butta_stream()` goes
	 *     through `coda_uccidi()`, which is the only point where `byte_in_coda` goes down. */
	coda_butta_stream(w, stream);
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ PHASE 7 — THE THREE CLIPBOARD CHANNEL HOOKS TOWARDS THE CLIENT (§2.5, §7.4). */
/*                                                                            */
/* ⛔⭐ AND THEY ARE NOT THE `video_*` ONES REUSED, although they open the same kind of */
/*     stream: `gancio_video_apri()` REMEMBERS which stream it opened          */
/*     (`video_stream_ultimo`), because §5.1 makes it reset **the previous one** */
/*     when a more recent one leaves.  A clipboard transfer that              */
/*     went through there would become «the previous frame» of the next       */
/*     frame — ⛔ that is it would be reset halfway by a rule that does not    */
/*     concern it, and the symptom would be «the clipboard arrives cut when the */
/*     desktop moves».                                                         */

static bool gancio_appunti_apri(void *ctx, int64_t *stream, uint64_t *restano)
{
	wt *w = (wt *)ctx;
	uint8_t pre[16];
	size_t n = 0;
	int64_t id = -1;

	if (restano)
		*restano = 0;
	if (!w->conn || w->sessione == -1 || w->guasto)
		return false;
	if (restano)
		*restano = ngtcp2_conn_get_streams_uni_left2(w->conn);

	if (ngtcp2_conn_open_uni_stream(w->conn, &id, NULL) != 0) {
		registro_dettaglio_di(REG_WT, wt_chi(w),
		                           "no unidirectional stream for the clipboard: the "
		                           "client still grants %llu (§2.5 wants one per "
		                           "transfer)",
		                           (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
			                           w->conn));
		return false;
	}

	n += varint_scrivi(pre + n, 0x54);
	n += varint_scrivi(pre + n, (uint64_t)w->sessione);

	if (!coda_metti(w, id, pre, n, false)) {
		/* ⛔ Same treatment as video: an opened and mute stream holds a
		 *    place in the client's count and never becomes a message. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, id, 0);
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ the WebTransport preamble (%zu bytes) does not fit in the "
		                 "queue: stream %ld reset, no clipboard transfer",
		                 n, (long)id);
		return false;
	}
	*stream = id;
	return true;
}

static bool gancio_appunti_scrivi(void *ctx, int64_t stream, const uint8_t *dati,
                                  size_t len)
{
	return coda_metti((wt *)ctx, stream, dati, len, false);
}

static void gancio_appunti_fin(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	/* ⛔ The FIN is a queue element like the others, and it is NOT written
	 *    at once: it must go out AFTER the bytes preceding it. */
	if (!coda_metti(w, stream, NULL, 0, true))
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ the FIN of clipboard stream %ld does not fit in the "
		                 "queue: the message has gone out and the stream stays open",
		                 (long)stream);
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ AND THE TWO HOOKS TOWARDS THE SESSION — «offer» and «answer».          */
/*                                                                            */
/* ⛔ They go through `main.c` like the input ones, and for the same reason:   */
/*    `webtransport.c` knows the wire and does not know the children, and whoever sews the two */
/*    worlds together is the only one who knows both sides.                   */

static wt_appunti_offerta gancio_palco_appunti_offri;
static wt_appunti_consegna gancio_palco_appunti_risposta;
static void *gancio_palco_appunti_ctx;

void wt_appunti_gancio(wt_appunti_offerta offri, wt_appunti_consegna risposta,
                       void *ctx)
{
	gancio_palco_appunti_offri = offri;
	gancio_palco_appunti_risposta = risposta;
	gancio_palco_appunti_ctx = ctx;
}

static bool gancio_appunti_offri(void *ctx)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_appunti_offri || !w->rcp)
		return false;
	/* ⛔ Invariant I3: it is offered to the session OF WHOEVER ASKED, and the name is
	 *    the one PAM admitted on this connection — not a parameter that
	 *    comes from the wire.  A user who could put text in another's clipboard
	 *    would be a communication channel between sessions that nobody
	 *    asked for. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_appunti_offri(gancio_palco_appunti_ctx, mio);
}

static bool gancio_appunti_risposta(void *ctx, uint32_t serial,
                                    const char *testo, size_t byte)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_appunti_risposta || !w->rcp)
		return false;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_appunti_risposta(gancio_palco_appunti_ctx, mio, serial,
	                                     testo, byte);
}


/* ⛔⭐ TRANSPORT PINGS WHILE THE CREDENTIALS ARE AWAITED — `RCP.md` §4.6,
 *     box R1.8, which is normative and starts with a ⛔.  Finding B-2, cured
 *     on the night of 10 Aug 2026.
 *
 * ⛔ THE DEFECT, in full, because the document describes it word for
 *    word.  §4.6 gives 60 seconds between `ECCOMI` sent and `CREDENZIALI`
 *    received — «it is the time in which a person types the password».  In
 *    those 60 seconds NOTHING GOES on the wire: §2.2 forbids the application
 *    heartbeat, and before attach there is no other active channel.  At the
 *    thirtieth second QUIC idleness (`IDLE_MS`) matures, the
 *    connection dies IN SILENCE — no `CONGEDO`, no code, no
 *    reason of §8.2 — and `TETTO_CREDENZIALI` never expires, because the RCP
 *    session was already freed thirty seconds earlier.
 *
 *    ⚠ Who falls into it: whoever types slowly, that is whoever types on a phone.  An
 *      intermittent defect, the worst to diagnose — and the bench would measure 30
 *      where the document says 60, blaming the bench.
 *
 * ⛔ And `wt_battito_ns()` IS NOT THE CURE, and that is the point: it moves OUR
 *    clock forward every 100 ms and for the caps of §4.6 it is perfectly fine, ⛔ but it does not put a
 *    byte on the wire — and the clock that kills the connection is QUIC's,
 *    which looks at bytes.  The box of `webtransport.h` presented the absence
 *    of keep-alive as an improvement over the graft citing §2.2: §4.6
 *    explicitly tells the two apart — transport PINGs «carry no
 *    information, have no answer to interpret, and do not create a
 *    second truth about silence» — and the ban of §2.2 does NOT cover them.
 *
 * ⭐ 10 seconds, and not 25: the PING must have time to be retransmitted
 *    at least once before the 30 mature.  A keep-alive tuned to a hair
 *    of the cap is a keep-alive the first lost packet makes useless.
 *
 * ⚠ And a DEAD client dies all the same: RFC 9000 §10.1 restarts the
 *   idle stopwatch when a packet is RECEIVED, not when one is
 *   sent.  Our PINGs keep alive a connection with someone who
 *   answers, not one with nobody.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔⭐ AND SINCE 16 AUG 2026 THEY STAY ON FOR THE WHOLE SESSION.  Below
 *      the opposite was written, and the reason was this:
 *
 *        ~~«Keeping the connection alive ALWAYS would change the meaning of the 30
 *        seconds of §2.2 — the silence clock: once expired, the client is
 *        detached»~~
 *
 *      ⇒ It fell in two steps, both measured.
 *
 *   1. ⛔ **The semantics had already changed**, and not because of these PINGs: since this morning
 *      §5.3 counts PACKETS and not RCP bytes (`rcp.c`, `ultima_vita`),
 *      because counting bytes a user who was READING lost the slot after
 *      thirty seconds and a second device took it away.  ⇒ «The client
 *      is there» already means «it answers on the wire».  These PINGs do not add
 *      that semantics: they make it **reliable**.
 *
 *   2. ⛔⛔ **Without them, the margin is the BROWSER's and not ours.**  `[M]` With a
 *      still session, packets arrive every **15002 · 15005 · 15002 ms** —
 *      exactly fifteen seconds, a clean half of the cap.  A number that regular
 *      is not traffic: it is Chrome's keep-alive.  ⚠ A different browser, or
 *      Chrome changing that number, and the slots start falling again under the
 *      nose of whoever is reading.
 *
 * ⚠ AND THE PREDICTION OF `SPECIFICHE.md` §5.3 ABOUT THE FROZEN TAB DOES NOT
 *   COME TRUE — «a background tab is frozen after about five
 *   minutes, so it goes quiet, so it is detached».  `[M]` 16 August, the user's real
 *   browser without automation attached, tab in the background for
 *   **eleven minutes**: zero detaches, packets on time at 15 s until the last.
 *   ⛔ That line is `[S]`, a prediction about browser behaviour, and the
 *   measurement disproves it.
 *
 * ⚠ THE PRICE, DECLARED: a client whose PAGE is dead but whose NETWORK
 *   answers keeps the slot.  ⛔ But it already kept it — see point 1 — and whoever
 *   returns to that tab finds their session again, which is invariant I4.  The
 *   case left uncovered is the client that stops answering ALSO on the
 *   wire, and that one is detached at thirty seconds as always. */
#define WT_TIENILA_VIVA_NS (10ULL * NGTCP2_SECONDS)

/* ========================================================================== */
/* ⛔⭐⭐⭐ PHASE 9 — THE DEAD LINE, and since 24 Aug 2026 it is born ON (the  */
/*          user's decision; until the 23rd it was born off because of I6).    */
/*                                                                            */
/* THE DECISION IS THE USER'S, 23 Aug 2026: *«if no more packets arrive in 10 */
/* seconds it is clear the connection is dead [...] if within an interval    */
/* of 1-2 seconds there is a rather copious packet loss I would say to treat  */
/* it as the case in which the connection has dropped»*.  And asked what the  */
/* user sees when it fires, the user                                          */
/* chose: **the wire drops and the user comes back in by hand**.              */
/*                                                                            */
/* ⛔ WHERE IT COMES FROM, and they are two ugly behaviours both — `[M]` 23    */
/*    Aug, same machine, profile `raffica-forte` (11.10 % INJECTED in          */
/*    197 bursts): WITHOUT the phase's cures the image freezes for up to       */
/*    **14.26 s** (7 seconds out of 25 saw a frame); WITH the cures it         */
/*    moves but with **4.5 s of delay**.  ⇒ The user decided neither of the    */
/*    two is to be served: such a line is DECLARED dead.                       */
/*                                                                            */
/* ⛔⛔⭐⭐ THE QUANTITY CHANGED ON 23 AUG 2026, AND THE OLD ONE WAS            */
/*       REFUTED BY ITS OWN BENCH.  It is written here in full, because        */
/*       whoever reads later must find the REASON and not the absence.         */
/*                                                                            */
/* ⛔ WHAT THERE WAS: `pkt_lost / pkt_sent` within a window, with threshold at */
/*    50‰.  ⛔⛔ AND IT ORDERS THE TWO CASES THE WRONG WAY ROUND — `[M]` 23 Aug 2026, */
/*    `banchi/09-b81-linea-morta.py`:                                         */
/*                                                                            */
/*      · `casa-cattiva`  — loss INJECTED 1.86-2.15 %, loss DECLARED           */
/*        by ngtcp2 **512‰** (51.2 %).  And the line HOLDS: ten minutes, 9.60  */
/*        frames/s, coverage 1.00, largest gap 0.50 s, and the client is       */
/*        still attached at 599.99 s.                                          */
/*      · `raffica-forte` — loss INJECTED 12.28-14.00 %, DECLARED              */
/*        **123‰** (12.3 %).  And the line does NOT hold: coverage 0.20, largest */
/*        gap 30.06 s.                                                         */
/*                                                                            */
/*    ⇒ The one that WORKS declares FOUR TIMES more loss than the one          */
/*      that does not work.  ⛔ No value separates them: a threshold that lets */
/*      `casa-cattiva` through (≥512‰) lets `raffica-forte` through too;       */
/*      one that stops `raffica-forte` (≤123‰) stops `casa-cattiva` first.     */
/*      It is not a tuning to redo: it is the wrong quantity.                  */
/*                                                                            */
/* ⭐ THE CAUSE, MEASURED: `casa-cattiva` carries `delay 40ms 20ms distribution */
/*    normal`, and the probe measures **93.5 % of packets out of order** there */
/*    with 1.9 % of true loss.  **ngtcp2 counts an overtaken packet           */
/*    as lost.**  ⇒ On a line that REORDERS, `pkt_lost/pkt_sent` measures      */
/*    REORDERING and not loss — which is the central fact of this              */
/*    phase, and it came back at us.  ⚠ And it is not the start of the        */
/*    connection: leaving out the first ten windows, 399 out of 399 stay above */
/*    threshold, median 524‰, uninterrupted for ten minutes.                   */
/*                                                                            */
/* ⭐⭐ AND THE NUMBER IS NOT THROWN AWAY, IT CHANGES JOB: from JUDGE to WITNESS. */
/*     It stays in the firing line as `permille=`, and it is the best          */
/*     measure of REORDERING the server has ON STREAMS — where                 */
/*     `dgram_falsi` (§17.3) does not reach, because that one holds on datagrams, */
/*     that is on audio only.  ⇒ A `permille=512` next to a `stallo_ms=0`      */
/*     is not a fault: it is jitter, and now the line SHOWS it instead of      */
/*     deciding it.                                                            */
/*                                                                            */
/* ⛔⭐⭐⭐ THE NEW QUANTITY, AND THE DATA POINT TO IT BY THEMSELVES: **HOW LONG */
/*        NO FRAME HAS LEFT WHILE HAVING SOME TO SEND.**  What                 */
/*        separates the two cases is not how much is lost, it is whether frames */
/*        LEAVE — `casa-cattiva` largest gap 0.50 s, `raffica-forte`           */
/*        30.06 s: sixty times, and in the right direction.                    */
/*                                                                            */
/*   ⛔ AND BOTH HALVES COUNT.  «Nothing leaves» alone is                      */
/*      also the STILL SCENE, which `[M]` in this phase is normal and          */
/*      costs nothing: Mutter's `RecordVirtual` delivers only on               */
/*      change, and the wake-up is worth 13 ms.  ⇒ If we have nothing to       */
/*      send nothing is broken, and the count must not even                    */
/*      START.                                                                 */
/*                                                                            */
/*   ⭐ HOW IT IS COMPUTED — two LOCAL and MONOTONIC counters, the P8→P20 shape */
/*      of `RCP.md:398` (the same as `arretrato`), and not a free              */
/*      clock: time enters only as the distance between two samples.           */
/*                                                                            */
/*        «it went out»  `lm_usciti` — the VIDEO bytes handed to ngtcp2        */
/*                      (`coda_consegna()`).  If it rises, the count RESTARTS. */
/*        «I had some   `coda_byte_video() > 0` — frame bytes still            */
/*         to send»     in our house — OR `lm_offerti` risen, that is          */
/*                      the stage gave us a frame.  If neither of the          */
/*                      two, the count restarts all the same: there was nothing */
/*                      to send, and nothing is broken.                        */
/*                                                                            */
/*      ⛔ THE SECOND TERM IS NOT AN EXTRA: without `lm_offerti` the            */
/*         RATE REGULATOR would hide the stall.  That one stops                */
/*         PRODUCING when the queue does not empty, `video_sgombra()`          */
/*         abandons old deltas, and «I have nothing to send»                   */
/*         would become true precisely while the screen is frozen.  ⇒ We       */
/*         count the frame the stage gives us, BEFORE any brake,               */
/*         clear-out or refusal.                                               */
/*      ⛔ AND BYTES ARE COUNTED, not whole frames: a keyframe of              */
/*         ~60 000 bytes on a narrow line can take seconds to go out           */
/*         entirely, and in frames those seconds would be a «stall» while      */
/*         the wire is working.  A byte that leaves is a wire that carries.    */
/*                                                                            */
/* ⛔⛔ THE NUMBER, WITH THE TWO MARGINS — `[M]` 23 Aug 2026, same bench.       */
/*      ⛔ And the INTERMEDIATE cases count as much as the extremes:           */
/*                                                                            */
/*        thirteen healthy profiles gap 0.04-0.35 s     hold                   */
/*        `casa-cattiva`          gap **0.50 s**       HOLDS, and must not     */
/*                                                     be declared dead        */
/*        `raffica-1` (1.07 %     ⚠ **1.00 s** whole   holds, and delivers     */
/*         in clusters)             without a frame    23.94 frames/s          */
/*        `raffica-forte`         **30.06 s**, and     does NOT hold           */
/*                                 14.26 s in another                          */
/*                                 run                                         */
/*                                                                            */
/*     ⚠ `raffica-1` IS THE CASE THAT KEEPS THE THRESHOLD HONEST: a line that  */
/*       delivers 24 frames a second still had **one whole                    */
/*       empty second**.  A threshold below that would throw out a             */
/*       perfectly usable session.                                             */
/*                                                                            */
/*     ⇒ The threshold lies **between 1.00 s and 14.26 s** — and the tight side is the */
/*       SHORTER of the two stalls of `raffica-forte`, not the longer, or      */
/*       the margin would be written on a lucky number.  The geometric         */
/*       centre is 3.78 s (√(1.00·14.26)); ⭐ **5.0 s** is chosen, and it is   */
/*       chosen ABOVE the centre on purpose:                                   */
/*                                                                            */
/*         margin above the worst that HOLDS:     5.00 / 1.00 = **5.0×**       */
/*         margin below the one that is NO USE:  14.26 / 5.00 = **2.9×**       */
/*         (and above `casa-cattiva`, which holds with 0.50 s, it is **10×**)  */
/*                                                                            */
/*     ⚠ THE ASYMMETRY IS INTENDED and declared — and it is the only thing the */
/*       old cure had right: the two errors do NOT cost the same.             */
/*       Erring high means a few more seconds of frozen screen                 */
/*       and then one comes back in by hand; erring low means                  */
/*       **throwing out someone who was working**, and that cannot be          */
/*       undone.                                                               */
/*                                                                            */
/* ⚠ AND THE SAMPLING ERRS ON THE GOOD SIDE, which must be said because it is */
/*   a real error: the count restarts from the INSTANT OF THE ROUND in which   */
/*   progress was SEEN, not from the one in which the bytes really             */
/*   went out.  The round is at most one a second (`rete_ciclo()`), so         */
/*   the measured `stallo_ms` can be up to ~1 s SHORTER than the truth.        */
/*   ⇒ It fires later, never earlier — which is the side on which              */
/*   the asymmetry above wants to err.                                         */
/* ========================================================================== */

/* ⛔ THE TWO DEFAULTS — `WT_LM_STALLO_MS` (5 000 ms) and `WT_LM_SILENZIO_S`
 *    (10 s) — are in `webtransport.h`, and there is A SINGLE COPY of them: `main.c`
 *    initialises its variables with them, so «the server's default» and «the
 *    transport's default» cannot become two different numbers.
 *    ⚠ The stall in MILLISECONDS, like `--sgombra-soglia-ms`: it is a delay one
 *      SEES, and whoever tunes it chooses how many seconds of frozen screen they bear
 *      before the wire drops. */
/* ⚠ `[?]` The three numbers below are tuned by the bench, like `WT_RITMO_POSTI`: the
 *   tuning is falsifiable — at 20 Mbit/s with `casa-cattiva` on for
 *   ten minutes the firings must be ZERO, and with `raffica-1` too. */
#define WT_LM_MIN_PACCHETTI 200u  /* below, the WITNESS window lengthens        */
#define WT_LM_FINESTRA_MS 1000u   /* the minimum window: the rhythm of rete_ciclo*/
/* ⛔ The PROBES of silence: how many of OUR packets have gone out since the
 *    client last showed itself.  Two, not two hundred: on a still
 *    desktop the traffic is made of transport PINGs and nothing else, and asking for
 *    two hundred packets would mean never judging precisely the case in which
 *    the client no longer answers. */
#define WT_LM_MIN_PROVE 2u

/* ⛔⭐ The switch is STATIC and not per session: it is a decision of the
 *     server, like `ritmo_adattivo`.  ⭐ Since 24 Aug 2026 it is born ON
 *     (the user's decision), and the value is brought by `main.c`, which is the only
 *     place where the default is written; the two numbers are born with the
 *     defaults above — `main.c` ALWAYS calls `wt_linea_morta()`, so
 *     the startup line comes out in both cases by construction. */
static bool linea_morta_accesa;
static uint64_t linea_morta_stallo_ms = WT_LM_STALLO_MS;
static uint64_t linea_morta_silenzio_ms = WT_LM_SILENZIO_S * 1000ULL;

/* ========================================================================== */
/* ⛔⭐⭐⭐ THE GAP IN THE PARENT'S LOOP — «our silence is not theirs».        */
/*         Phase 10, 25 Aug 2026, findings P2/P4/P5 of §8.2.                  */
/*                                                                            */
/* ⛔ THE FACT, and it fits in one line: the TWO quantities the dead line      */
/*    decides on are not quantities of the wire, they are quantities of OUR LOOP. */
/*                                                                            */
/*      `lm_usciti`  rises in `coda_consegna()`, that is when we WRITE;       */
/*      `pkt_recv`   rises when `trasporto_leggi()` READS the socket.         */
/*                                                                            */
/*    ⇒ A stopped loop freezes both, and the client's packets, which           */
/*      are arriving perfectly well, stay in the kernel buffer without         */
/*      anybody counting them.  ⛔⛔ The dead line read that freeze as         */
/*      *«the client has not shown a packet for too long»* and closed          */
/*      the session with `persi=0` next to it — that is **with the proof, in the */
/*      line itself, that the network had nothing to do with it**.             */
/*                                                                            */
/* ⛔ AND THE THREE MEASURED ROADS ALL LEAD HERE:                             */
/*                                                                            */
/*    · `[M]` §6.7 — a `SIGSTOP` of **5 s to ONE child** killed **all          */
/*      four** sessions: `causa=stallo usciti_byte=0 coda_video=8862           */
/*      persi=0`.  A stopped child leaves bytes stuck in the PARENT's queue.   */
/*    · `[M]` §6.13 — the synchronous logind guard in the loop: at N=7 with    */
/*      D=286 ms the loop stands still **longer than the sweep lasts**.        */
/*    · `[M]` §6.15 — **five clients evicted in 1.3 s** with five sessions:    */
/*      five independent sessions do not go quiet in the same second for       */
/*      five different reasons.  ⚠ Whether this is the mechanism will be said by */
/*      `fermo_ms=` in the line, not by this comment: if it came out ZERO, the */
/*      cause is another and this cure does not cover it.                      */
/*                                                                            */
/* ⭐⭐ THE SHAPE OF THE CURE: a gap counts as PROGRESS — the counts           */
/*     RESTART.  ⛔ And NOT «the lost time is subtracted», which looks more    */
/*     precise and is not: a steadily slow loop would keep the service         */
/*     clock behind **forever**, and then a really dead client                 */
/*     would **never** be recognised.  Restarting costs at most ONE            */
/*     threshold of delay on the dead one, and it is a bounded and declared price. */
/*                                                                            */
/* ⛔ THE BUDGET, and why 1100 and not 1000: the `poll` of `main.c` sleeps at   */
/*    most **1000 ms** (`attesa`), so two passes are normally up to            */
/*    one second apart.  ⭐ The 100 ms of margin serve to not count as         */
/*    «gap» the ORDINARY work of a full pass — if it were exactly 1000,        */
/*    this counter would say «gap» on a healthy machine and the cure           */
/*    would always fire, that is it would secretly switch off the dead line.   */
/*    ⚠ It is a number TUNED ON THE LOOP, not on the network: if one day `attesa` */
/*      changed, it must be changed with it.                                   */
/* ========================================================================== */
#define WT_GIRO_ATTESO_MS 1100

static uint64_t giro_ultimo_ms;    /* when the parent's loop passed           */
static uint64_t giro_fermo_ms;     /* ⛔ the milliseconds of gap, in total     */
static uint64_t giro_fermi;        /* how many gaps                           */
static uint64_t giro_fermo_peggiore_ms;

void wt_giro_del_padre(uint64_t ora_ms)
{
	uint64_t distanza;

	/* ⛔ The first pass is not a gap: before there was nothing to compare,
	 *    and «never passed» is not «passed a long time ago» (`LEZIONI.md` §1.9). */
	if (!giro_ultimo_ms || ora_ms <= giro_ultimo_ms) {
		giro_ultimo_ms = ora_ms;
		return;
	}
	distanza = ora_ms - giro_ultimo_ms;
	giro_ultimo_ms = ora_ms;
	if (distanza <= WT_GIRO_ATTESO_MS)
		return;
	giro_fermo_ms += distanza - WT_GIRO_ATTESO_MS;
	giro_fermi++;
	if (distanza > giro_fermo_peggiore_ms)
		giro_fermo_peggiore_ms = distanza;
	/* ⚠ No line here: it is written by whoever suffers the effect, with the
	 *   session and its numbers next to it.  One line per gap, without context, would be
	 *   noise on a loaded machine — and the number is there all the same, it is carried by
	 *   `wt_giri_fermi()` once a minute. */
}

void wt_giri_fermi(uint64_t *quanti, uint64_t *peggiore_ms)
{
	if (quanti)
		*quanti = giro_fermi;
	if (peggiore_ms)
		*peggiore_ms = giro_fermo_peggiore_ms;
}

/* ⛔⛔⭐⭐ HOW OFTEN THE CLIENT IS ASKED TO SHOW ITSELF — and with the dead line
 *       on it is NO longer 10 s.  It is the line that makes the rule of the
 *       10 seconds of silence HONEST: without it, that rule is dangerous.
 *
 * ⭐ FIRST OF ALL, WHAT IT ALREADY DOES TODAY, because it is the question
 *    anyone reading «an active-session PING is needed» asks: it already has one, since 16
 *    Aug 2026 (the box above).  `regola_tienila_viva()` switches on
 *    ngtcp2's keep-alive in ALL states except `finita` — not only while
 *    credentials are awaited.  ⇒ `FASI.md` §05 §6-bis is done, and the measurement
 *    `[M]` of **15 004 / 15 005 / 15 002 ms** between two packets of a still
 *    browser is what was seen BEFORE: it was Chrome's keep-alive, and it is
 *    precisely the measurement that got ours switched on.  ⚠ Today that number is no
 *    longer 15 s: it is **10**, and they are ours.
 *
 * ⛔ BUT 10 ARE NOT ENOUGH FOR A SILENCE THRESHOLD OF 10 s, and the defect is the
 *    same as before with a smaller number: a HEALTHY but still client shows
 *    itself every ~10 s + RTT, because before then nobody asked it
 *    anything.  A threshold at 10 s would measure THAT — and would throw out whoever is
 *    reading a page, which is the regression already paid on 16 August («a
 *    second tab came in and took the first one's desktop»).
 *
 * ⇒ With the switch on the interval becomes **HALF** the silence
 *   threshold: at a 10 s threshold we ask every 5 s, and when the 10 s expire there are
 *   **two unanswered questions**, not one that maybe was still on its way.
 *   ⭐ It is the minimum number that makes the rule true: with the interval equal
 *      to the threshold the verdict would depend on the RTT, that is on the network being
 *      judged.
 *
 * ⚠ AND IT IS NOT AN APPLICATION HEARTBEAT, which §2.2 forbids: they are TRANSPORT PINGs, and
 *   §4.6 tells the two apart word for word — «they carry no information,
 *   have no answer to interpret, and do not create a second truth
 *   about silence».  ⛔ The boundary is not the period, it is the nature: below one
 *   second it would become something else, and we do not go there.
 *
 * ⛔⛔ THE PRICE THAT WAS WRITTEN HERE — «~26 bytes/s, 0.21 kbit/s per session» —
 *      DESCRIBED A CASE THE PRODUCT NEVER ENTERS, and it is corrected instead of
 *      left: a price declared for a case that does not exist is worse than
 *      no price.  `[M]` 23 Aug 2026, bench `09-b81`:
 *
 *      1. ⛔ **ngtcp2's keep-alive sends a PING only after its interval
 *         WITHOUT OTHER TRAFFIC.**  And on a live session traffic never
 *         stops: the counter does not stand still even for **0.6 s**.  ⇒ On a
 *         session that is working these PINGs **never get a chance to
 *         fire**, and their cost there is **zero**.  The ~26 bytes/s are a
 *         CAP touched only with traffic completely stopped — that is after
 *         the client has stopped speaking, which is the case they exist for.
 *      2. ⛔ **And the bench COULD NOT ISOLATE IT, and refused to give an
 *         empty green.**  A «still» session costs **2 463 kbit/s** all the same
 *         of PCM audio (§4.3, which does not switch off): that is **11 727 times** the 0.21
 *         kbit/s this line declared.  The measured difference between cure
 *         on and cure off is **+0.539 kbit/s** — within the noise, that is
 *         a number that proves nothing in either direction.
 *
 *   ⇒ What stays true, and is enough to decide: a PING is a short packet
 *     (short header + a PING frame + the 16 bytes of the seal, `[?]` ~40
 *     bytes of payload plus 28 of IP/UDP) and the answer is an
 *     equally short acknowledgement.  With traffic stopped and one round every 5 s it is a CAP of
 *     ~26 bytes/s per session, against the declared floor of 20 Mbit/s
 *     (`DECISIONI.md` §3.1-bis).  The cost is not an argument; the period is
 *     chosen by the rule, not by the bandwidth.
 *
 * ⭐ AND IT ALSO HOLDS FOR GHOST EVICTION (`rcp.c`, `--sfratto-ms`): that one
 *    is tuned at 15 s because below 15 s a dead client could not be told from
 *    a still one — and the 15 s were Chrome's keep-alive.  With PINGs at 5 s
 *    the `ultima_vita` of a live client is never older than ~5 s + RTT, and
 *    eviction can go down to **~10 s** without risking anything.  ⛔ But NOT to 3:
 *    for 3 a PING every ~1 s would be needed, that is sixteen times the traffic
 *    above and a period that starts to look like a heartbeat.  ⚠ And the choice
 *    is not this file's: here we declare the number this file makes
 *    possible.
 */
static uint64_t tienila_viva_ns(void)
{
	if (linea_morta_accesa && linea_morta_silenzio_ms)
		return (linea_morta_silenzio_ms / 2) * NGTCP2_MILLISECONDS;
	return WT_TIENILA_VIVA_NS;
}

static void regola_tienila_viva(wt *w, const char *stato)
{
	/* ⚠ The state name is the contract: `rcp.h` lists all seven of them
	 *   in writing, and says whoever compares them must know it.  ⛔ Here
	 *   only the state in which they are NOT needed is named: after the end there is
	 *   nothing left to keep alive, and insisting would be noise on a connection
	 *   that is closing. */
	bool serve = stato && strcmp(stato, "finita") != 0;

	if (serve == w->tienila_viva)
		return;
	w->tienila_viva = serve;
	ngtcp2_conn_set_keep_alive_timeout(w->conn,
	                                   serve ? tienila_viva_ns() : UINT64_MAX);
	/* ⛔ Two calls and not one with `?:` inside the format: the two formats have
	 *    a DIFFERENT number of arguments since the interval is printed, and a
	 *    `%llu` that is not there is a defect that shows only at the first detach. */
	if (serve)
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⭐ transport PINGs ON every %llu s with %s: the sign "
		                 "of life of §5.3 is produced by US, not by the browser's "
		                 "keep-alive (which gave 15 s out of a 30 cap)%s",
		                 (unsigned long long)(tienila_viva_ns() / NGTCP2_SECONDS),
		                 w->provenienza,
		                 linea_morta_accesa && linea_morta_silenzio_ms
		                     ? ".  ⚠ They are HALF the silence threshold of the "
		                       "dead line: when it expires, the unanswered questions "
		                       "are two"
		                     : "");
	else
		registro_dice_di(REG_WT, wt_chi(w),
		                 "transport PINGs off with %s: the session is over, "
		                 "there is nothing left to keep alive",
		                 w->provenienza);
}

static void regola_battito(wt *w)
{
	const char *stato = w->rcp ? rcp_stato_nome(w->rcp) : NULL;

	regola_tienila_viva(w, stato);

	/* ⛔⛔⭐⭐ AND ON THE SAME STATE THE FRAME LOOP IS SWITCHED OFF TOO.
	 *
	 *        `fasi/13-xfce.md`, 23 Sep 2026: *«the stage stops capturing
	 *        when the TRANSPORT dies, not when the client says FAREWELL»*.  At
	 *        farewell the SLOT was given up at once (§4.2, `chiusa_dal_client()`)
	 *        but capture went on: every frame was captured,
	 *        composed, encoded, offered and **refused** by
	 *        `rcp_video_apri()` (`RCP_VIDEO_PRIMA_DI_SESSIONE`), with on record
	 *        «⛔ NO VIDEO: `SESSIONE` has not been sent (state finita)».
	 *        ⇒ Graphics card work for NOBODY, and a red line that
	 *        looks like a fault.
	 *
	 * `[M]` The window lasted **~30 s** — the `max_idle_timeout`, that is how long
	 *       the transport takes to die by itself after the PINGs are off.
	 *       On a still desktop that is 11 frames; at 58 frames/s it is **twenty
	 *       seconds of wasted encoding for every client that leaves**, on a
	 *       machine that meanwhile serves other tenants.
	 *
	 * ⭐ WHY RIGHT HERE, next to the PINGs, and not inside `fin_dal_client()`,
	 *    `chiusa_dal_client()` and `wt_stream_chiuso()`: the roads leading to
	 *    `"finita"` are SEVEN in `rcp.c` (the closing capsule, the FIN on the
	 *    control channel, the server's farewell, the ban, the three caps of
	 *    §4.6...).  Sewing the cure onto three of those seven would mean four
	 *    uncovered roads and a policy written in three places — *«a count
	 *    written in three different places is a count that one day will
	 *    forget one»*.  ⇒ We hook onto the STATE, which is the point where
	 *    all seven converge, and which this function already looks at at
	 *    every heartbeat.  `regola_tienila_viva()` is the proof that the event exists
	 *    and is already recognised: it switches off the PINGs on the same `"finita"`, and
	 *    `[M]` does so **100 ms** after the farewell (22 Sep, 10:30:11.698 →
	 *    10:30:11.798).  ⇒ The waste window goes from ~30 s to ~0.1 s.
	 *
	 * ⛔ AND IT DOES NOT DISMANTLE THE STAGE — invariant **I4**.  What is switched off is the
	 *    request for frames to the child (`figli_video()` with codec 0, which
	 *    `figlio.h` declares as «stop capturing»); the child, the
	 *    graphical session and the open windows stay exactly where they are,
	 *    and whoever reconnects finds their desktop again.  It is the same distinction
	 *    already written for audio: *«what switches off is the monitor's consumption, not
	 *    the device on which applications play»*.
	 *
	 * ⚠ And `"staccata-per-silenzio"` does NOT get in here, and it is a choice: that
	 *   state too gives up the slot, but from there `torna_a_parlare()` can
	 *   resurrect the same session, and in ghost eviction the client
	 *   that ARRIVES has not yet sent `SESSIONE` — switching off there would
	 *   mean stopping and restarting capture in the middle of a hand-over.
	 *   The cost of the 30 s is paid only by whoever says FAREWELL, and that is
	 *   the measured case. */
	if (stato && strcmp(stato, "finita") == 0)
		cattura_spegni_se_sola(w, "the client said farewell");

	if (!stato) {
		/* No RCP session: we beat if there is a closure to let
		 * mature — ⛔ **or if the cap of §7.17 is armed**.
		 *
		 * ⛔ It is here that the first draft of the cap died, `[M]` 11 Aug
		 *    2026 with bench B6: `cb_end_headers` armed `canale_entro` and
		 *    called `batti_fra`, and then the first pass of this function
		 *    set `battito_ms = 0` back.  The cap fired only if the client
		 *    did something else that woke the heartbeat up — that is
		 *    **precisely in the case where it is not needed**: `ciao-sessione-tardiva`
		 *    expired at 5.10 s, `ciao-senza-controllo` stayed hanging for 20 s.
		 *
		 * ⚠ It is the lesson written thirty lines further below, caught red-handed
		 *   in the very run in which it was being applied: **whoever sets a cap must
		 *   also switch on what will make it expire** — and switching it on is not
		 *   enough, nobody else must switch it off. */
		if (w->chiusura >= 0 || w->canale_entro)
			batti_fra(w, 100);
		else
			w->battito_ms = 0;
		return;
	}
	if (strcmp(stato, "attiva") == 0) {
		/* ⭐ The silence clock of `SPECIFICHE.md` §5.3 must be evaluated
		 *    WHILE the client is quiet, and while it is quiet nobody would walk
		 *    the write path.  One second of granularity out of
		 *    thirty is plenty. */
		batti_fra(w, 1000);
		return;
	}
	/* ⛔ `attesa-verdetto` wants the heartbeat because the fixed delay of
	 *    §4.4-bis lasts one second and in that second there is nothing to
	 *    send; the other handshake states because the three caps
	 *    of §4.6 must be able to expire even if the client is quiet.
	 *
	 * ⛔⭐ AND THIS IS THE DEAREST LESSON OF THE GRAFT, in two guises:
	 *      `[M]` 10 Aug 2026, B6 and B5.  Whoever sets a cap must also switch on
	 *      what will make it expire, AT THE INSTANT the cap
	 *      starts — not at the first useful occasion that comes along afterwards.  A
	 *      job deferred to a condition nobody makes happen any more
	 *      is not deferred: it is lost, and in the log it looks like a job
	 *      never asked for. */
	batti_fra(w, 100);
}

/* ========================================================================== */
/* ⭐⭐ THE FRAME LOOP — PHASE 3, «the desktop that moves»                    */
/*                                                                            */
/* ⛔⭐ WHAT WAS HERE BEFORE, AND WHY IT WAS REMOVED                           */
/*                                                                            */
/*    Until phase 2 this place contained a PER-PROCESS DEPOSIT:               */
/*    `struct video_deposito video_dep[3]`, filled once at power-on           */
/*    and read by every session that reached `SESSIONE`.  It had three        */
/*    declared defects, and all three belong to this phase:                   */
/*                                                                            */
/*      1. it was per PROCESS and not per session — `main.c` §«the deposit and the */
/*         leak» declares it: «the real cure is a per-session deposit».  The  */
/*         fallback was an OWNER of the deposit, and the declared price was   */
/*         that two users connected together could not both see their         */
/*         own desktop;                                                        */
/*      2. it marked `chiave = true` **by construction**, and with real       */
/*         keyframes/deltas that line becomes **a lie on the wire** (§6.2, field */
/*         `tipo`);                                                            */
/*      3. it served ONE frame per session, and the brake was `bool           */
/*         video_fatto`.                                                       */
/*                                                                            */
/* ⇒ In its place there is a BROADCAST: the user's child captures and        */
/*   encodes continuously, `main.c` forwards every frame in here, and this    */
/*   function delivers it **to that user's sessions and to no other**.        */
/*   ⛔ The comparison on the user's name is invariant I3 on the wire, and it is */
/*   the same guard as before put where it was needed: no longer «whose is the */
/*   deposit», but «whose is this session».  Two users connected together    */
/*   now each see their own.                                                   */
/*                                                                            */
/* ⚠ AND WHAT IS NOT DONE, DECLARED: the bytes are NOT copied.  The frame     */
/*   arrives from `main.c`, is put in each session's queue (which copies it   */
/*   itself, in `coda_metti`) and then the caller can free it.  An intermediate */
/*   deposit here would be one more copy per frame, that is up to 60           */
/*   copies a second of a few hundred KiB.                                     */

/* ⛔ The list of live sessions.  It is needed because frames arrive from
 *    OUTSIDE (from the child, by the hand of `main.c`) and not from an event of this
 *    connection: without a list, whoever broadcasts would have to keep the
 *    pointers itself, and two lists of the same set diverge. */
static wt *vive_prima;

static wt_video_richiesta gancio_palco;
static void *gancio_palco_ctx;

void wt_video_gancio(wt_video_richiesta f, void *ctx)
{
	gancio_palco = f;
	gancio_palco_ctx = ctx;
}

/* ⛔ How often a keyframe can be REquested from the stage while the debt is
 *    still on.  ⚠ It is not the grace of §5.2 — that one belongs to `rcp.c` and counts
 *    from the last keyframe SENT: this is the backstop of a request that still has
 *    to cross a socket, a process and an encoder.  Without it,
 *    every heartbeat would send one and the child would encode only keyframes. */
#define WT_CHIAVE_RICHIESTA_MS 150

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔⛔⛔ AND 150 ms ARE NOT ENOUGH WHEN THE LINE IS NARROW — 21 Aug 2026,
 *       bench `07-b65`, and the defect is a self-feeding loop.
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * `[M]` The measurement, and the scene is declared: real session, tone in the sink,
 * desktop that moves, `netem` at **3 Mbit/s** on the bench port only,
 * thirty seconds.
 *
 *   | scene (same bandwidth, same audio) | audio sent    | purity  |
 *   |---|---|---|
 *   | **still** desktop                  | **6 009** / 6 000 | **1.000** |
 *   | desktop **that moves**             | **397**           | **0.18**  |
 *
 * ⛔ It is not the bandwidth and it is not what audio costs: with **Opus**, that is **1/32**
 *    of PCM's bandwidth, at the same step **58 %** of it is still lost.
 *
 * ⭐⭐ IT IS THIS CONSTANT.  In the narrow runs video delivers **only keyframes**
 *     (144 out of 144, 148 out of 148, 149 out of 149; at 15 Mbit it was 2 out of 1 019), the
 *     log counts **806 keyframe requests** and **173 lines** «KEYFRAME N
 *     still holds ~60 000 bytes in the queue and §5.2 forbids abandoning it».
 *
 *       a 60 KB keyframe on 3 Mbit occupies the window for  **160 ms**
 *       this constant grants one every                       **150 ms**
 *
 *     ⇒ **We ask for the new keyframe before the previous one has gone out.**  In
 *     those 160 ms 32 PCM blocks are born (8 Opus ones) and each finds
 *     `cwnd_left = 0`: the datagram does not split, is not retransmitted and cannot
 *     wait, so it is the only one that can pay.
 *
 * ⛔ And the cure is NOT moving audio ahead of video: `07-b65` tried
 *    FOUR transport variants (no early return per pass ·
 *    no `PADDING` · no `MORE` · the reserve, that is video yielding the
 *    pass when there are datagrams in the queue) and the blocks sent stay at
 *    278-514 against the starting 397, that is within the variance.
 *    ⭐ **The window is not contended: it is already full** of video bytes in flight,
 *    and giving up writing more does not free what has already left and has not
 *    yet been acknowledged.  Only an acknowledgement frees the place.
 *
 * ⇒ **The interval becomes a function of the measured bandwidth**: a new keyframe
 *   is not requested before a keyframe the size of the last one has had
 *   time to go out.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * 🔸 DERIVED, AND THE PRICE IS VISIBLE TO THE USER — it is declared, not
 *    implied (`LEZIONI.md` §2.3-quater, `CODER.md` I6)
 * ───────────────────────────────────────────────────────────────────────────
 *
 * ⛔ **On a narrow line the image stays broken longer after a loss.**
 *    It is exactly what is bought: before, the desktop asked for a keyframe
 *    every 150 ms and the line did not let it out (so it stayed broken
 *    ALL THE SAME, and on top of that it destroyed the audio); now it waits for the time the
 *    keyframe really takes, and in exchange the sound gets through.
 *
 * ⚠ The judgement is the user's: these two numbers — the cap and the margin — are not
 *   proved, they are derived.  They go into `DECISIONI.md` the day
 *   he listens to them and looks at them together.
 *
 * ⛔ THE CAP EXISTS BECAUSE A KEYFRAME NO LONGER REQUESTED IS A SCREEN
 *    FROZEN FOREVER.  `SPECIFICHE.md` I1: «an ugly session is worth more than
 *    a closed session» — but **frozen** is not **ugly**, it is half closed.
 *    Two seconds is the longest we accept to stay broken.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⭐ THE BEFORE/AFTER, MEASURED — `07-b65`, 21 Aug 2026, evening
 * ───────────────────────────────────────────────────────────────────────────
 *
 * ⛔ The two binaries differ by ONE line (`chiave_intervallo_ms()` always returning
 *    the constant), and the runs are ALTERNATED: with the variance seen here
 *    — 397 against 1372 blocks between two identical runs — two runs in a row of the
 *    same side would prove nothing.
 *
 * | scene (30 s, PCM)          | wait   | audio BEFORE | audio AFTER | video BEFORE | video AFTER |
 * |---|---|---|---|---|---|
 * | 3 Mbit, **still** desktop  | 150 (inert) | 6 009 | **6 002** | 1 | 1 |
 * | 15 Mbit, moving desktop    | 150 (inert) | 4 076 · 3 944 | 3 984 · 3 830 | 743 · 742 | 683 · 677 |
 * | 3 Mbit, moving desktop     | ~171   | 371 · 462 | **1 552 · 1 595 · 1 725** | 115 · 99 | 89 · 128 |
 * | 1 Mbit, moving desktop     | 600-1000 | **15** | **577** | 57 | **47** |
 *
 * ⭐ **Where there is bandwidth the cure declares itself INERT**: at 15 Mbit it wrote «the
 *    measured bandwidth is enough: the 150 ms backstop remains» **100 times out of 101**, and the
 *    two binaries behave the same — the 8 % difference on frames
 *    there is scene variance, not a price.
 *
 * ⛔⛔ **THE PRICE, MEASURED AND NOT DEDUCED**: at 1 Mbit keyframe requests
 *      go down from **178 to 68** (−62 %) and video delivers **57 → 47**
 *      frames, **−18 %** — and they are all keyframes, so the image
 *      updates less often.  ⇒ It is exactly «on a narrow line the image
 *      stays broken longer after a loss», in numbers.  In exchange
 *      audio goes from **15 to 577** blocks.
 *
 * ⚠ AND WHAT THE CURE DOES **NOT** DO, declared so that no more is taken from it
 *   than it gives: at 3 Mbit audio stays at **27 %** and the frames
 *   delivered are still **all keyframes**.  ⇒ The spiral is not switched off, it is only
 *   slower.  The real engine is upstream, and it is written next to
 *   `video_sgombra()`. */
#define WT_CHIAVE_TETTO_MS 2000

/* ⛔ The margin: the keyframe must have GONE OUT, not «almost gone out».  A fifth
 *    more than the computed time covers the fact that the bandwidth estimate is an
 *    estimate and that audio passes meanwhile too. */
#define WT_CHIAVE_MARGINE_PC 120

/* ⛔⭐⭐ THE SECOND BELT — «the debt has been on for too long, and nobody asks for
 *       anything any more» — 23 Sep 2026.
 *
 *       The real cure for the 370 s block is in `batti_fra()`: the heartbeat can
 *       no longer be postponed forever, so `video_regola()` runs again
 *       **at least once a second** and the keyframe is requested by itself.
 *
 * ⛔ But that cure depends on ONE single link — the heartbeat.  And today's
 *    lesson is exactly this: *a system that depends on two
 *    events never overlapping is a system that hangs.*  ⇒ A
 *    road that does NOT go through the heartbeat is needed.
 *
 * ⭐ And there is a perfect one: refused frames.  While the debt is
 *    on the child keeps delivering (`[M]` ~123 Mbit/s of encoding
 *    thrown away), and every refusal is an occasion to notice.  ⇒ If since
 *    the last request to the stage more than this time has passed and the debt
 *    is still on, the keyframe is requested FROM THERE.
 *
 * ⚠ One second, not 150 ms: it is the heartbeat's step in the `attiva` state, that is
 *   the rhythm the keyframe request ALREADY has today when everything works.
 *   Making it tighter would make keyframes be requested 6-7 times a second under
 *   congestion, which is the spiral of §5.2 measured on bench `07-b65`.
 *   ⇒ This belt does not change the rhythm: it only changes the «forever». */
#define WT_CHIAVE_DEBITO_TETTO_MS 1000

/* ⛔ How many uni streams video needs BEFORE saying «without credit»: `RCP.md`
 *    §2.3 wants input always to find one, and video must not eat up
 *    the last slot.  ⚠ The number is the minimum §2.3 reserves for RCP divided
 *    in half: it is declared here because it is our choice, not a line
 *    of the referee. */
#define WT_UNI_RISERVA 2

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ PHASE 9 — WHEN A DELTA IS «REALLY HOPELESS»: THE THRESHOLD.
 *
 * ⛔ §5.1 says **MAY**, not MUST (`RCP.md:1156`): abandoning at every
 *    more recent frame is OUR choice, and the field measurement says
 *    it is the one that fabricates keyframes.
 *
 * `[M]` 23 Aug 2026, step on the test machine (wide line → 3 s at
 *       10 Mbit/s → wide), scene `barra`, canvas 1920x1080:
 *
 *       | second       | 7  | 8  | 9  | 10 | 11 | 12 |
 *       | frames/s     | 40 | 14 | 14 | 13 | 32 | 42 |
 *       | of which KEY |  0 |  6 |  7 |  7 |  2 |  0 |
 *       | abandonments |  0 |  7 |  6 |  7 |  2 |  0 |
 *
 *       ⛔ Abandonments and keyframes go **one to one**, even on the wide line
 *       (3↔3, 1↔1).  ⇒ It is not the poor line that fabricates keyframes: it is
 *       this function.  The poor line only adds occasions.
 *       ⚠ Control: the same step with a scene costing 3.7 Mbit/s —
 *       below the hole — gives 0 keyframes, 0 abandonments, 40/s in all phases: the
 *       instrument can tell the difference.
 *
 * ⭐ THE NEW RULE: a delta is abandoned **only if the video queue does not
 *    empty within the threshold**, that is only if it would not arrive in time anyway
 *    to be of any use.  Below the threshold it is KEPT: streams are
 *    independent (`RCP.md:1155`), so keeping it does not block the later ones.
 *
 * ⛔ THE NUMBER, AND ITS REASON — four constraints, not a taste:
 *
 *    1. it must be **more than one frame period**, or it is today's rule
 *       with a new name: `[M]` phase 8, the user's real content runs at
 *       20.9 frames/s = **47.8 ms** period (33.3 ms at 30/s);
 *    2. it must be **less than the backstop with which a keyframe is already requested** —
 *       `WT_CHIAVE_RICHIESTA_MS` = 150 ms: beyond that number the queue
 *       would delay more than the rhythm the product has already accepted;
 *    3. it must **let a KEYFRAME plus a few deltas through** where the defect
 *       bites: `[M]` phase 8 a keyframe measures ~20 800 bytes (median, QP 26); at
 *       3 Mbit/s (375 bytes/ms) it goes out in 56 ms, and in the remaining 44 ms
 *       three deltas fit;
 *    4. the price adds up along the chain: `[M]` phase 8 the whole chain measures
 *       **55.20 ms**, and 100 + 55 stays below a fifth of a second.
 *
 * ⇒ **100 ms**, and it is the DEFAULT since 24 Aug 2026 (the user's decision:
 *    the phase 9 cures are switched on in the product).  ⚠ `[?]` The number is not
 *    proved: it is derived from the four constraints above and then MEASURED —
 *    `[M]` 23-24 Aug 2026, bench `09-b79`, three arms on the healthy line: 39.85 /
 *    40.19 / 39.63 frames/s, **zero keyframes** in all three, final drift
 *    0.1 / 0.2 / 0.9 ms.  ⇒ On the healthy line the cure COSTS NOTHING; on a bad
 *    network the price is up to **+160 ms** of drift, and it is what
 *    the user looked at and accepted.
 *
 * ⛔ The number is in `webtransport.h` (`WT_SGOMBRA_SOGLIA_MS`), not here: `main.c`
 *    initialises its variable with it, and a second copy would be «the
 *    server's default» different from «the transport's default» the
 *    day one of the two is tuned. */

/* ⛔ The fallback when ngtcp2 has neither `smoothed_rtt` nor `cwnd` yet: we
 *    assume **the declared floor**, 20 Mbit/s = 2 500 bytes/ms
 *    (`DECISIONI.md` §3.1-bis).  ⚠ It is DECLARED instead of guessed: an invented
 *    number passing for measured is shape E1.  ⚠ And if the real line is
 *    narrower the fallback UNDERESTIMATES the wait and keeps one delta too
 *    many: it lasts until ngtcp2 has a measurement, that is one network round trip. */
#define WT_PAVIMENTO_BYTE_MS 2500u

/* ⛔⭐⭐ IT IS BORN ON AT `WT_SGOMBRA_SOGLIA_MS` SINCE 24 AUG 2026 — the
 *      user's decision.  ⚠ Until the 23rd it was born OFF because of invariant I6, which wants
 *      whatever changes what one SEES behind a switch that is off **until
 *      the user has looked at it**: they looked at it (§19.6, §20.3) and decided.
 *      ⇒ The premise of I6 is satisfied, not circumvented.
 *
 * ⛔ `0` remains the way to switch it off (`--sgombra-soglia-ms 0`): it abandons at
 *    every more recent frame, that is yesterday's product **byte for byte**.
 *
 * ⚠ A second boolean «somebody touched it» is NOT needed: `main.c` calls
 *   `wt_sgombra_soglia()` **always**, at startup, with the value in force ⇒ the startup
 *   line comes out in both cases by construction, not because of a guard to
 *   remember.  ⛔ And the number is not repeated here: the single copy is in the .h, and
 *   the value arrives from `main.c`. */
static uint64_t sgombra_soglia_ms;

/* ⛔⭐ THE LINE THAT DECLARES THE VALUE IN FORCE, AND IT IS WRITTEN ON AND OFF.
 *
 *     «Off» and «never fired» must not look the same: it is
 *     exactly shape E1 («written is not in force»), the same reason
 *     the three clocks of §5.3 are written at startup.
 *
 * ⛔⛔ AND SINCE 24 AUG 2026 IT MUST SAY **THE TRUE STATE AND THE REASON**, no longer
 *      «OFF (I6)».  A line still saying «off (I6)» about a cure
 *      that is on is worse than no line: whoever rereads a bench would believe they had
 *      measured yesterday's product.  ⇒ Three things in every line: whether it is on, the
 *      NUMBER in force, and HOW it is switched off. */
static void sgombra_dichiara(const char *da_dove)
{
	/* ⚠ And the head piece — «video queue threshold (§5.1): N ms» — is NOT
	 *   to be touched: it is what the phase 9 benches read to verify the
	 *   arm (`09-b79-cure.py:582`).  The TAIL of the line changes, that is what
	 *   the line says; the hook stays where it was. */
	if (sgombra_soglia_ms)
		registro_dice(REG_AVVIO,
		              "⭐ PHASE 9, video queue threshold (§5.1): %llu ms — "
		              "ON: above the threshold a stuck delta is abandoned, below "
		              "it is KEPT.  ⭐ It is the DEFAULT since 24 Aug 2026 "
		              "(the user's decision: the phase 9 cures are switched on "
		              "in the product; the user looked at them on the real desktop, §19.6 and "
		              "§20.3).  ⚠ The price, `[M]` 09-b79: up to +160 ms of "
		              "drift on a bad network, ZERO on the healthy line (39.85 / "
		              "40.19 / 39.63 frames/s, zero keyframes in all three "
		              "arms).  ⛔ It is SWITCHED OFF with `--sgombra-soglia-ms 0`, and that is "
		              "the only way.  Set by: %s",
		              (unsigned long long)sgombra_soglia_ms, da_dove);
	else
		registro_dice(REG_AVVIO,
		              "⛔ PHASE 9, video queue threshold (§5.1): 0 ms — OFF: "
		              "it abandons at every more recent frame, that is the "
		              "product up to 23 Aug 2026 byte for byte.  ⚠ And it is NOT "
		              "the default: since 24 August it is born ON at %u ms, so "
		              "someone typed `--sgombra-soglia-ms 0` on purpose.  "
		              "Set by: %s",
		              (unsigned)WT_SGOMBRA_SOGLIA_MS, da_dove);
}

/* ⛔ `main.c` calls it at startup, ALWAYS — even with 0, which is the case in which
 *    someone switched it off on purpose.  ⚠ The provisional bridge that read
 *    `REMOTIX_SGOMBRA_SOGLIA_MS` from the environment was declared temporary and was
 *    REMOVED on 23 Aug 2026, when `--sgombra-soglia-ms` really
 *    arrived: two ways of switching on the same cure are two numbers that
 *    can diverge. */
void wt_sgombra_soglia(uint64_t ms)
{
	sgombra_soglia_ms = ms;
	sgombra_dichiara("main.c, from the command line (--sgombra-soglia-ms; "
	                 "the default is 100, and 0 switches it off)");
}

uint64_t wt_sgombra_soglia_letta(void)
{
	return sgombra_soglia_ms;
}

/* ⛔⭐⭐ PHASE 9 — THE RATE REGULATOR: the switch, and since 24 Aug 2026
 *      it is born **ON** (the user's decision; until the 23rd it was born off because of
 *      invariant I6, and I6 did its job: the user looked at §19.6 and §20.3
 *      before deciding).  It is switched off with `--niente-ritmo-adattivo`.
 *    Static and not per session: it is a decision of the server, not of the client.
 * ⚠ The value is brought by `main.c`, which is the only place where the default is
 *   written: no second copy is kept here. */
static bool ritmo_adattivo;

/* ⛔ How many delta frames it allows itself to have behind before skipping one.
 *
 * ⭐ AND THE NUMBER IS NOT A DISGUISED CLOCK: it is the depth of the pipe.
 *    With `POSTI = 1` one would skip every time the previous frame had not
 *    gone out ENTIRELY by the arrival of the next — at 60/s that is 16 ms, and a
 *    10 KB delta on a healthy line takes longer: it would be a cautious
 *    heuristic, that is I1 broken.  With `POSTI = 2` exactly ONE
 *    frame of overlap is allowed, and one skips only when two have been left
 *    behind.
 * ⚠ `[?]` The value must be tuned on the bench, and the tuning is falsifiable: at
 *   20 Mbit/s with a moving scene `POSTI = 2` must give ZERO drops. */
#define WT_RITMO_POSTI 2

/* ⛔⛔⭐ `main.c` CALLS IT AT STARTUP, ALWAYS — on and off — and the line that
 *      comes out of here is half the value of this cure.
 *
 *      A regulator that is OFF and a regulator that never had to fire
 *      produce THE SAME LOG, that is no line.  Whoever rereads a bench
 *      without this line does not know which of the two they measured: it is shape E1
 *      («written is not in force»), and it is the same reason why
 *      `chiave_intervallo_ms()` carries `*come` and why `sgombra_dichiara()`
 *      speaks even at zero.
 *
 * ⛔⛔ AND HERE THE DEPENDENCY BETWEEN THE TWO SWITCHES IS ALSO DECLARED, which is the
 *      fact easiest to measure wrong in the whole phase.
 *
 *      `video_sgombra()` with the threshold OFF abandons every delta that
 *      still has bytes in the queue, at every more recent frame.  ⇒ When
 *      frame N+1 arrives, the only delta that can still have bytes of ours
 *      is N: `arretrato` is **0 or 1, never 2**, by construction — and with
 *      `WT_RITMO_POSTI = 2` this regulator **never fires**.
 *
 *      ⛔ A bench that left only the regulator on (that is that typed
 *      `--sgombra-soglia-ms 0` without `--niente-ritmo-adattivo`) would measure zero
 *      drops and would read «the line carries».  They are two facts with the same
 *      face, and the line below is what separates them BEFORE the measurement
 *      instead of after.
 *
 * ⭐ Since 24 Aug 2026 the normal case is that BOTH are on by themselves:
 *      remotix                       (the defaults: threshold 100 ms + regulator)
 *   and the pair that measures nothing must be ASKED for on purpose.
 *
 * ⚠ And the order in `main.c` is not by chance: `wt_sgombra_soglia()` comes FIRST,
 *   so this line reads the value in force instead of promising one.
 *
 * ⚠⚠ And the CONGESTION ALGORITHM has never been chosen — `trasporto.c`
 *     calls `ngtcp2_settings_default()` and does not touch `cc_algo`, so
 *     ngtcp2's default (CUBIC) is taken.  ⛔ It is NOT changed in this
 *     round, because it would be a second variable in the same bench; but it must be
 *     named, because it bites precisely here: on WiFi a LOSS-BASED algorithm
 *     reads a radio loss as congestion and halves the window —
 *     that is it fabricates the backlog this regulator then measures.  `[?]` To be
 *     tried as a separate experiment, behind a switch of its own. */
void wt_ritmo_adattivo(bool acceso)
{
	ritmo_adattivo = acceso;
	if (!acceso) {
		registro_dice(REG_AVVIO,
		              "⛔ the rate regulator is OFF by whoever launched the "
		              "server (`--niente-ritmo-adattivo`): no frame "
		              "will ever be skipped because of the line, that is the product up to "
		              "23 Aug 2026 byte for byte.  ⚠ And it is NOT the default: "
		              "since 24 August it is born ON (the user's decision), so "
		              "someone switched it off on purpose.  ⚠ And this line IS the "
		              "reason — it is not that it never had to fire");
		return;
	}
	registro_dice(REG_AVVIO,
	              "⭐ PHASE 9: the rate regulator is ON — a frame "
	              "does NOT leave when %u deltas in flight still have bytes in my "
	              "output queue.  ⭐ It is the DEFAULT since 24 Aug 2026 "
	              "(the user's decision: the phase 9 cures are switched on in the "
	              "product; the user looked at them on the real desktop, §19.6 and §20.3).  ⚠ The "
	              "price, `[M]` 09-b79: threshold plus regulator cost up to "
	              "+160 ms of drift on a bad network, ZERO on the healthy line "
	              "(39.85 / 40.19 / 39.63 frames/s, zero keyframes in all three "
	              "arms).  ⛔ It is SWITCHED OFF with `--niente-ritmo-adattivo`, and that is "
	              "the only way — the old name `--ritmo-adattivo` no longer "
	              "exists.  ⚠ Every drop ends up in the log (I1), and there is "
	              "no rise to remember: `arretrato` is reread at every "
	              "frame",
	              (unsigned)WT_RITMO_POSTI);
	if (!sgombra_soglia_ms)
		registro_dice(REG_AVVIO,
		              "⛔⛔ BUT THE VIDEO QUEUE THRESHOLD IS OFF "
		              "(`--sgombra-soglia-ms 0`), and then this regulator WILL NEVER "
		              "FIRE: `video_sgombra()` empties the delta queue at "
		              "every frame, so `arretrato` cannot exceed 1 and the "
		              "slots are %u.  ⚠ A bench made like this measures ZERO drops and "
		              "seems to say «the line carries»: they are two facts with the same "
		              "face.  ⇒ With the defaults of 24 Aug 2026 BOTH are born "
		              "on: whoever sees this line switched the threshold off by hand "
		              "and left the regulator on, which is the combination "
		              "that measures nothing",
		              (unsigned)WT_RITMO_POSTI);
	else
		registro_dice(REG_AVVIO,
		              "⭐ and the video queue threshold is on at %llu ms: it is its "
		              "prerequisite — it is what lets `arretrato` rise to "
		              "2-3, that is into the range in which the %u slots discriminate",
		              (unsigned long long)sgombra_soglia_ms,
		              (unsigned)WT_RITMO_POSTI);
}

/* ⛔⛔⭐ `main.c` CALLS IT AT STARTUP, ALWAYS — on and off — and the line that
 *      comes out of here is half the value of this cure, for the same reason
 *      as `wt_ritmo_adattivo()`: a cure that is off and a cure that never
 *      had to fire produce THE SAME LOG, that is no line.
 *
 * ⛔⛔ AND THIS IS THE MOST VISIBLE OF ALL — it throws a session out.  I6 was not
 *      a formality here: it is the step that in v1 cost
 *      the reset of a whole phase.  ⇒ It was born off, the user watched it
 *      on the real desktop (§19.6, §20.3), and on **24 Aug 2026**
 *      decided it becomes the normal behaviour.  ⭐ The premise of I6 is
 *      satisfied — not circumvented: the switch is still there, it is only turned
 *      the other way (`--niente-linea-morta`).
 *
 * `stallo_ms`  the milliseconds without a video byte leaving WHILE HAVING some to
 *              send.  `0` = off, and then no stall, however long it
 *              may be, declares the line dead (silence alone remains).
 * `silenzio_s` the seconds without a packet from the client.  `0` = off.
 *
 * ⚠ AND THERE IS NO ENVIRONMENT VARIABLE, on purpose: the bridge
 *   `REMOTIX_SGOMBRA_SOGLIA_MS` was removed on 23 Aug 2026 with the
 *   reason written next to `wt_sgombra_soglia()` — two ways of switching on
 *   the same cure are two numbers that can diverge.  The bench uses the
 *   options, which are the only way.
 */
void wt_linea_morta(bool accesa, uint64_t stallo_ms, uint64_t silenzio_s)
{
	linea_morta_accesa = accesa;
	linea_morta_stallo_ms = stallo_ms;
	linea_morta_silenzio_ms = silenzio_s * 1000;
	if (!accesa) {
		registro_dice(REG_AVVIO,
		              "⛔ the DEAD LINE is OFF by whoever launched the server "
		              "(`--niente-linea-morta`): no session will ever be "
		              "closed for output stall or for client silence "
		              "before QUIC's 30 s (§5.3) — that is the product up to "
		              "23 Aug 2026 byte for byte.  ⚠ And it is NOT the default: "
		              "since 24 August it is born ON (the user's decision), so "
		              "someone switched it off on purpose.  ⚠ And this line IS the "
		              "reason — it is not that it never had to fire");
		return;
	}
	registro_dice(REG_AVVIO,
	              "⛔⭐ PHASE 9: the DEAD LINE is ON — the "
	              "wire drops and the user comes back in BY HAND (the user's decision, 23 "
	              "Aug 2026).  ⭐ It is the DEFAULT since 24 Aug 2026, and it is "
	              "SWITCHED OFF with `--niente-linea-morta` (only way; the old "
	              "name `--linea-morta` no longer exists).  ⛔⛔ IT IS THE CURE THAT "
	              "CLOSES A SESSION: if the threshold were badly tuned it would throw "
	              "out someone who is working — `[M]` 23-24 Aug the margin is >10x "
	              "above `casa-cattiva`, the WORST line that holds (largest "
	              "stall < 500 ms over ten minutes, zero firings), and 2.9x below the "
	              "14.26 s of `raffica-forte`, which serves nobody.  TWO causes, "
	              "and each writes its own "
	              "`linea-morta` line with the count it decided on (I1):  (1) STALL: "
	              "%llu ms without a video byte leaving while we had some to "
	              "send — and «I had some to send» means frame bytes "
	              "still in the queue OR a new frame from the stage: on a still "
	              "scene the count does not even start;  (2) SILENCE: %llu s without "
	              "a packet from the client with at least %u of our packets sent "
	              "in the meantime.  ⚠ Margins of the stall threshold, `[M]` 23 "
	              "Aug: 5.0× above the empty whole second of `raffica-1` (which "
	              "HOLDS, 23.94 frames/s) and 2.9× below the 14.26 s of "
	              "`raffica-forte` (which serves nobody).  ⛔⛔ AND THE LOSS "
	              "FRACTION NO LONGER JUDGES: `permille=` stays in the line as a "
	              "WITNESS of reordering — `casa-cattiva` declared 512‰ and "
	              "HELD for ten minutes, `raffica-forte` 123‰ and did not hold",
	              (unsigned long long)linea_morta_stallo_ms,
	              (unsigned long long)(linea_morta_silenzio_ms / 1000),
	              (unsigned)WT_LM_MIN_PROVE);
	if (!linea_morta_stallo_ms)
		registro_dice(REG_AVVIO,
		              "⚠ but the STALL threshold is at 0 ms: silence alone "
		              "remains.  A frozen image will close nothing");
	if (!linea_morta_silenzio_ms)
		registro_dice(REG_AVVIO,
		              "⚠ but the SILENCE threshold is at 0 s: loss alone "
		              "remains, and a client that goes quiet waits for QUIC's 30 s "
		              "(§5.3) as always");
}

/* ⛔ How many ms the MEASURED bandwidth takes to carry away `byte` — the same two
 *    numbers as `chiave_intervallo_ms()`, which are the ones with which ngtcp2 decides
 *    how much to send.  ⚠ It is not the bandwidth «of the line»: it is the one the
 *    congestion control is granting now.
 *
 * ⛔⛔ AND THIS ESTIMATE IS A MINIMUM, not a promise — three reasons, declared
 *     because it is the most important falsifier of §5.3 of the proposal:
 *     (a) it does not count the bytes already handed to ngtcp2 and not yet acknowledged,
 *         which the queue no longer sees;
 *     (b) the window is shared with audio too, which travels on datagrams;
 *     (c) a retransmission pays the same bandwidth twice.
 *     ⇒ If the measured delay of the chain exceeds 55 + threshold ms, it is HERE that
 *     it gave way: it would be a number that *looks* measured. */
static uint64_t coda_svuotamento_ms(const wt *w, size_t byte, const char **come)
{
	ngtcp2_conn_info info;

	if (byte == 0) {
		*come = "the video queue is empty";
		return 0;
	}
	memset(&info, 0, sizeof info);
	if (w->conn)
		ngtcp2_conn_get_conn_info(w->conn, &info);
	if (info.smoothed_rtt == 0 || info.cwnd == 0) {
		*come = "fallback: ngtcp2 has neither rtt nor window yet, the "
		        "declared floor of 20 Mbit/s is assumed (DECISIONI.md §3.1-bis)";
		return (uint64_t)byte / WT_PAVIMENTO_BYTE_MS;
	}
	*come = "from the measured bandwidth (cwnd/rtt)";
	return (uint64_t)byte * info.smoothed_rtt / info.cwnd / NGTCP2_MILLISECONDS;
}

/* ------------------------------------------------------------------------ */
/* ⭐ §5.1 — ABANDONMENT, AND IT IS WHAT SHOWS ON THE RECEIVING SIDE.        */

static void involo_pulisci(wt *w)
{
	size_t j = 0;
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo)
			w->involo[j++] = w->involo[i];
	w->ninvolo = j;
}

/* ⛔ §5.1: «the server MAY call `RESET_STREAM` on a frame that is no longer
 *    needed — because a more recent one has already left — and the bytes not
 *    yet sent do not leave at all».
 *
 * ⚠ «Not yet sent» means «still in OUR queue»: what has already
 *   passed to ngtcp2 we do not take back, and resetting there would no longer save
 *   anything.  ⇒ A frame without bytes in the queue leaves the list without anything
 *   being written: it was not abandoned, it was sent. */
/*
 * ⛔⛔⛔ AND HERE IS THE ENGINE OF THE SPIRAL — found on 21 Aug 2026 measuring
 *       the cure of `WT_CHIAVE_TETTO_MS`, and it is NOT what I believed.
 *
 *       This function is called at EVERY frame that arrives from the stage, and
 *       abandons the deltas still stuck in the queue because «a more
 *       recent one has left» (§5.1).  On a wide line it almost never abandons.  ⛔ On
 *       a narrow line a delta does not have time to go out in 33 ms, so
 *       it is abandoned **always**, and every abandonment switches on the debt of
 *       §5.2 inside `rcp.c`.
 *
 *       `[M]` The log of a run at 3 Mbit says it **28 times a second**:
 *       «⛔ FRAME NOT SENT: it is a delta and §5.2 wants a KEYFRAME (a
 *       delta was abandoned in the queue (§5.1))».  ⇒ The debt never
 *       switches off, every delivered frame is a KEYFRAME (115 out of 115, 99 out of
 *       99, 128 out of 128), every keyframe fills the window and the audio
 *       datagrams find `cwnd_left = 0`.
 *
 * ⚠⚠ AND MY FIRST DIAGNOSIS COUNTED THE WRONG LINE: I had searched for «wants
 *     a KEYFRAME», which appears in TWO different messages — the REQUEST leaving
 *     from `video_regola()` and the REFUSAL `rcp.c` writes.  The «806 keyframe
 *     requests» of the first report were mostly refusals.  ⇒ Counted
 *     separately: **105 requests against 346 refusals** in the same run.
 *     The line that looks alike is counted apart, or the diagnosis points upstream of
 *     where the defect is.
 *
 * ⇒ ⭐ **THE CURE IS BELOW, since 23 Aug 2026** (phase 9): abandon a
 *   delta only when it is really hopeless — a **threshold on the queue** —
 *   instead of at every more recent frame.  §5.1 **allows** it, it does not
 *   **impose** it.  So under congestion video drops RATE while remaining made
 *   of deltas, instead of becoming a stream of keyframes only.
 *   ⭐ And since 24 Aug 2026 it is born ON at 100 ms (the user's decision; until
 *   the 23rd it was born off because of invariant I6).  ⛔ With `--sgombra-soglia-ms 0`
 *   this function goes back to doing what it always did, byte for byte.
 */
/*
 * ⛔⭐⭐ THE FALSIFIABLE PREDICTION — written BEFORE measuring, 23 Aug 2026.
 *
 *       Same step as the table above (wide line → 3 s at 10 Mbit/s →
 *       wide), scene `barra`, 1920x1080, with `--sgombra-soglia-ms 100`:
 *
 *       | quantity                     | today (off)   | prediction at 100 ms|
 *       | frames/s in seconds 8-10     | 13-14         | **>= 25**           |
 *       | of which KEYFRAME, per second| 6-7           | **<= 2**            |
 *       | §5.1 abandonments per second | 6-7           | **<= 2**            |
 *       | seconds 7 and 12 (wide line) | 40-42/s, 0 kf | **identical** (inert)|
 *       | return, second 11            | 32/s          | **>= 32/s**         |
 *       | final count                  | —             | KEPT >> 0           |
 *
 *       ⭐ And outside the step the cure must be INERT: at 20 Mbit/s — the
 *       floor of `DECISIONI.md` §3.1-bis — the queue never reaches 100 ms,
 *       so `abbandonati per soglia` = 0 and the chain's delay stays
 *       the one of phase 8 (55.20 ms `[M]`).
 *
 * ⛔ THE FOUR REDS THAT WOULD PROVE ME WRONG — and each says where to look:
 *
 *    1. **keyframes stay at 6-7/s while §5.1 abandonments go down to <= 2.**
 *       ⇒ The §5.2 debt is switched on by ANOTHER of the seven causes, almost
 *       certainly 4 (`rcp.c:3441`, the missing credit — the shape invisible
 *       to the receiver), and the cure spins idle.  ⚠ The final count tells the
 *       two apart on purpose: `abbandonati per soglia` against `non accettati per credito
 *       mancato`.  It is the lesson already paid for («105 requests against 346
 *       refusals in the same run»);
 *    2. **frames/s in seconds 8-10 do not rise, or drop below 13.**
 *       ⇒ The kept deltas arrive too late to be of use: the threshold is too
 *       high and the queue is buying smoothness by selling responsiveness
 *       (`SPECIFICHE.md:128-130`).  We go down to 50 ms and measure again;
 *    3. ⛔ **the measured delay of the chain exceeds 55 + threshold ms** (155 ms at
 *       100).  ⇒ `coda_svuotamento_ms()` UNDERESTIMATES the emptying for one
 *       of the three reasons declared next to it, and the threshold does not limit what
 *       it promises.  ⭐ It is the most important red, because it would be **a
 *       number that looks measured**;
 *    4. **the return stops being under one second** (second 11 below
 *       32/s).  ⇒ The kept queue delays the RECOVERY, that is the cure pays for the
 *       transient with the return: it is the opposite of its purpose, and at that point
 *       the threshold must be switched off instead of tuned.
 *
 * ⚠⚠ THE PRICE, IN MILLISECONDS — it is the thing the user must judge, not
 *     a measurement: for a fraction of a second, under congestion, the image is
 *     **slightly old** instead of smashed.
 *
 *     | when the line carries (>= 20 Mbit/s)      | **0 ms** — never at threshold |
 *     | at worst, by construction                 | **100 ms** (the threshold) |
 *     | + the control's grain (at every frame)    | **+33 … +48 ms**         |
 *     | ⇒ declared worst, only during the drop    | **~150 ms**              |
 *     | + the phase 8 chain (55.20 ms `[M]`)      | **~205 ms** gesture→pixel |
 *     | **today**, at the same instant            | 0 ms added, but          |
 *     |                                           | 100 % keyframes and the deltas |
 *     |                                           | do not arrive at all     |
 *
 *     ⚠ Concretely: dragging a window while the line drops, the
 *     window follows the pointer with up to a fifth of a second of delay
 *     for a moment — instead of jumping from one image to the next at keyframe
 *     rhythm.  ⛔ Which of the two is worse is not decided by a measurement: it is
 *     decided by him.
 *
 * ⭐⭐ AND THIS CURE IS THE PREREQUISITE OF THE RATE REGULATOR
 *     (`fasi/09-la-qualita-e-la-degradazione.md` §6).  That design hooks onto
 *     `arretrato` = how many live DELTAS still have bytes in our queue, and
 *     ⛔ today that quantity is **zero by construction**, because this
 *     function empties everything at every round: a regulator installed now would never
 *     fire and the bench would read it as «the line carries».
 *     ⇒ Here `arretrato` is counted with the definition of §3.1 — alive, NOT keyframe,
 *     bytes in the queue > 0 — and it is WRITTEN in every line next to the threshold, so
 *     the regulator's quantity becomes readable instead of becoming
 *     yet another thing.  ⚠ At 100 ms and 20.9-30 frames/s `arretrato` can
 *     rise to **2-3**, which is exactly the range in which the `POSTI = 2`
 *     of that design discriminates.
 */
static void video_sgombra(wt *w, const char *perche)
{
	size_t resto[WT_INVOLO_MAX];
	size_t in_coda = 0;
	unsigned arretrato = 0;
	uint64_t attesa = 0;
	const char *come = "the threshold is at 0 (switched off by hand: since 24 Aug 2026 the default is 100 ms)";
	char motivo[400];

	if (!w->rcp || !w->conn)
		return;

	/* ⛔ FIRST PASS — and it is not one round too many: whoever has no more bytes leaves
	 * the list (it was not abandoned, it was SENT), and what
	 * remains is added up.  The sum is the VIDEO queue — not `w->byte_in_coda`,
	 * which would also contain the control channel and audio.
	 * ⚠ The bytes are kept in `resto[]` instead of being reread: between the two
	 *   passes nothing changes, and `coda_byte_stream()` scans the whole queue
	 *   every time. */
	bool chiave_in_coda = false;
	uint32_t chiave_numero = 0;

	for (size_t i = 0; i < w->ninvolo; i++) {
		resto[i] = 0;
		if (!w->involo[i].vivo)
			continue;
		resto[i] = coda_byte_stream(w, w->involo[i].stream);
		if (resto[i] == 0) {
			w->involo[i].vivo = false;
			continue;
		}
		in_coda += resto[i];
		if (w->involo[i].chiave) {
			chiave_in_coda = true;
			chiave_numero = w->involo[i].numero;
		}
		/* ⭐ `arretrato` excludes KEYFRAMES, and it is the definition of §3.1 of the
		 *    regulator's design: a slow keyframe in the queue must not stop
		 *    delta production, it already has its own regulator in
		 *    `chiave_intervallo_ms()`.  ⚠ But its BYTES count in the sum:
		 *    they really occupy the pipe, and the price in ms must say so. */
		if (!w->involo[i].chiave)
			arretrato++;
	}

	if (sgombra_soglia_ms) {
		attesa = coda_svuotamento_ms(w, in_coda, &come);
		/* ⛔⛔ THE KEYFRAME SPIRAL — 22 Sep 2026, the user's test with a
		 *     4K video on KDE, Chrome and Firefox.  A ~300 KB keyframe in the queue
		 *     takes the wait above the threshold BY ITSELF; abandoning the deltas that
		 *     come behind it does not shorten it (the keyframe is not abandoned,
		 *     §5.2), but opens a hole ⇒ RICHIEDI_CHIAVE ⇒ another big
		 *     keyframe ⇒ another abandoned delta.  `[M]` «abbandonati» rose
		 *     by one at every keyframe, 7→13 in 6 s, and then dead line: the spiral
		 *     `RCP.md` §5.2 names.  ⇒ As long as a keyframe is in the queue the
		 *     deltas are KEPT: braking production is the job of the rate
		 *     regulator, not of abandonment. */
		if (attesa > sgombra_soglia_ms && chiave_in_coda) {
			w->sgombra_tenuti += arretrato;
			w->sgombra_dietro_chiave += arretrato;
			if (w->sgombra_chiave_detta != chiave_numero + 1) {
				w->sgombra_chiave_detta = chiave_numero + 1;
				registro_dice_di(REG_RCP, wt_chi(w),
				                 "⭐ %s: the video queue is above the threshold "
				                 "(%zu bytes = %llu ms, threshold %llu ms) but there is "
				                 "KEYFRAME %u ahead: the %u deltas behind "
				                 "it are KEPT — abandoning them would open a "
				                 "hole and ask for another keyframe (the "
				                 "spiral of RCP.md §5.2)",
				                 w->provenienza, in_coda,
				                 (unsigned long long)attesa,
				                 (unsigned long long)sgombra_soglia_ms,
				                 chiave_numero, arretrato);
			}
			involo_pulisci(w);
			return;
		}
		if (attesa <= sgombra_soglia_ms) {
			/* ⭐ IT IS KEPT — and no line is written per frame: it is counted,
			 * and the line comes out only when the STATE changes.  ⚠ Thirty lines a
			 * second would make the log unreadable precisely where it is needed:
			 * it is the same reason as the backstop of `chiave_intervallo_ms()`. */
			w->sgombra_tenuti += arretrato;
			if (w->sgombra_sopra) {
				w->sgombra_sopra = false;
				registro_dice_di(REG_RCP, wt_chi(w),
				                 "⭐ %s: the video queue goes back BELOW the threshold "
				                 "(%zu bytes = %llu ms, threshold %llu ms, %s): the %u "
				                 "backlogged deltas are KEPT — §5.1 says MAY, not "
				                 "MUST",
				                 w->provenienza, in_coda,
				                 (unsigned long long)attesa,
				                 (unsigned long long)sgombra_soglia_ms, come,
				                 arretrato);
			}
			involo_pulisci(w);
			return;
		}
		if (!w->sgombra_sopra) {
			w->sgombra_sopra = true;
			registro_dice_di(REG_RCP, wt_chi(w),
			                 "⛔ %s: the video queue goes ABOVE the threshold (%zu "
			                 "bytes = %llu ms, threshold %llu ms, %s), backlog %u "
			                 "deltas: from here the oldest are abandoned (§5.1), "
			                 "the minimum needed to get back",
			                 w->provenienza, in_coda, (unsigned long long)attesa,
			                 (unsigned long long)sgombra_soglia_ms, come,
			                 arretrato);
		}
	}

	for (size_t i = 0; i < w->ninvolo; i++) {
		size_t rimasti = resto[i];
		if (!w->involo[i].vivo || rimasti == 0)
			continue;
		if (w->involo[i].chiave) {
			/* ⛔ §5.2: «the server MUST NOT abandon a keyframe.
			 * Abandoning the cure is not a cure».  ⚠ And it is said ONCE,
			 * because it is something that lasts until the line carries it away:
			 * repeating it at every frame would make the log unreadable
			 * precisely when it is needed. */
			if (!w->involo[i].detto) {
				w->involo[i].detto = true;
				registro_dice_di(REG_RCP, wt_chi(w),
				                 "⚠ %s: KEYFRAME %u still holds %zu bytes in the queue "
				                 "and §5.2 forbids abandoning it: WAITING.  ⭐ And the "
				                 "deltas coming after are not blocked by it — "
				                 "streams are independent (§5.1)",
				                 w->provenienza, w->involo[i].numero, rimasti);
			}
			continue;
		}
		/* ⛔ §5.1: «every abandonment MUST be written in the log» — a
		 * frame lost silently and one abandoned on purpose look the
		 * same from the receiving side.  ⭐ And the REASON carries THE MEASUREMENT
		 * NEXT TO THE THRESHOLD: if the measurement is below the threshold, that drop
		 * was out of caution, and the line itself proves it.  Without it, the
		 * log would say «a more recent one has left» even when the
		 * real reason is another, and it would tell the old rule.
		 * ⚠ The line, the count and the debt stay with `rcp.c`: two copies of the
		 * same state diverge. */
		snprintf(motivo, sizeof motivo,
		         "%s — and the video queue does not empty in time: %zu bytes = "
		         "%llu ms (%s), threshold %llu ms, backlog %u deltas",
		         perche, in_coda, (unsigned long long)attesa, come,
		         (unsigned long long)sgombra_soglia_ms, arretrato);
		if (!rcp_video_abbandonato_a_valle(w->rcp, w->involo[i].numero, false,
		                                   rimasti,
		                                   sgombra_soglia_ms ? motivo : perche))
			continue;
		/* ⛔ FIRST the stream is reset, THEN the bytes are thrown away.  The other way round
		 * there would be a window — short but real — in which the stream is alive and
		 * its bytes are no longer there: `wt_scrivi()` would find it mute instead
		 * of reset, and the client would wait for an end that does not come. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, w->involo[i].stream, 0);
		coda_butta_stream(w, w->involo[i].stream);
		w->involo[i].vivo = false;
		w->sgombra_abbandoni++;
		/* ⭐ THE MINIMUM IS ABANDONED, scanning from the OLDEST: the list is
		 * in insertion order (`involo_aggiungi()`), so the first live one
		 * is the oldest and it is the one that serves least.  ⛔ As soon as the queue
		 * gets back below the threshold we STOP: abandoning the others too
		 * would cost a keyframe for nothing, and it is precisely the spiral
		 * `RCP.md:1284` names — «one keyframe for every abandoned
		 * delta is the spiral».
		 *
		 * ⚠ AND WE EXIT SILENTLY, without an «it was enough» line: the state has NOT
		 *   changed — the threshold is still biting, and the return is the work of
		 *   this abandonment, not of the line.  Writing it here would mean
		 *   two lines per frame, that is sixty a second while the
		 *   step lasts: it is the defect the backstop of `chiave_intervallo_ms()`
		 *   exists not to commit.  ⭐ `sgombra_sopra` goes back to false only when a
		 *   WHOLE pass finds the queue below the threshold without abandoning
		 *   anything: that is indeed a change of state. */
		if (sgombra_soglia_ms) {
			arretrato--;
			in_coda -= rimasti;
			attesa = coda_svuotamento_ms(w, in_coda, &come);
			if (attesa <= sgombra_soglia_ms)
				break;
		}
	}
	involo_pulisci(w);
}

static void involo_aggiungi(wt *w, int64_t stream, uint32_t numero, bool chiave)
{
	if (stream < 0)
		return;
	involo_pulisci(w);
	if (w->ninvolo >= WT_INVOLO_MAX) {
		/* ⚠ It is said instead of slipping by: from here on that frame will not
		 *   be abandonable, and whoever reads the log must know it — an
		 *   abandonment that does not happen because a table is full looks in
		 *   every way like an abandonment nobody asked for. */
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⚠ %s: %u frames already in flight: frame %u does not enter "
		                 "the list and can NOT be abandoned (§5.1)",
		                 w->provenienza, WT_INVOLO_MAX, numero);
		return;
	}
	w->involo[w->ninvolo].stream = stream;
	w->involo[w->ninvolo].numero = numero;
	w->involo[w->ninvolo].chiave = chiave;
	w->involo[w->ninvolo].vivo = true;
	w->involo[w->ninvolo].detto = false;
	w->ninvolo++;
}

/* ------------------------------------------------------------------------ */
/* ⭐ THE SEAM BETWEEN THE REQUESTED KEYFRAME AND THE ENCODER — point 4.      */

/* ⛔ `rcp_video_serve_chiave()` was READ and served no purpose:
 *    `codificatore_chiedi_chiave()` had **no caller in the product**.
 *    ⇒ A client `RICHIEDI_CHIAVE` switched on a `bool` in `rcp.c`, the
 *    next frame was a delta, `rcp_video_apri()` refused it with
 *    `RCP_VIDEO_SERVE_UNA_CHIAVE`, and **the screen stayed frozen forever** —
 *    because `chiavi_ogni = 0` gives an infinite GOP and after the first keyframe not one
 *    ever arrives again by itself.
 *
 * ⇒ The hook: the stage is in ANOTHER PROCESS (the user's child), and
 *   this is the line that crosses the boundary.  ⚠ It is here and not in `rcp.c`
 *   because `rcp.c` does not know the children, and not in `main.c` because `main.c` does not
 *   know the session state. */
/*
 * ⭐ THE AUDIO CHANNEL SWITCHES ON, and it does NOT go through the video codec.
 *
 * ⛔ It is in a function of its own and not inside `video_regola()` for a reason that
 *    shows only when writing it: that one returns at once when `video.codec` is not
 *    negotiated — which is the legitimate case of a phase 1 client — and
 *    audio would end up in there by chance.  The two negotiations are
 *    independent in `RCP.md` §4.3, and must be read as independent here too.
 */
/*
 * ⭐⭐ HOW OFTEN A KEYFRAME CAN BE REQUESTED — and the bandwidth is MEASURED.
 *
 * ⛔ The rule: a new keyframe is not requested before a keyframe the
 *    size of the last one has had time to **really go out**.  The why
 *    and the numbers are next to `WT_CHIAVE_TETTO_MS`.
 *
 * ⛔⭐ AND THE BANDWIDTH IS NOT GUESSED: it is given by two numbers ngtcp2 measures by itself,
 *     and they are the same ones with which it decides how much to send —
 *
 *         bandwidth ≈ cwnd / smoothed_rtt    (bytes per second)
 *         time of a keyframe = bytes × smoothed_rtt / cwnd
 *
 *     ⚠ It is not a bandwidth «of the line»: it is **the bandwidth the congestion
 *       control is granting now**, which is precisely the speed
 *       at which the keyframe will go out.  Using the link capacity
 *       would give a nicer and wrong number.
 *
 * ⛔ AND IF THE ESTIMATE IS NOT THERE YET, THE FALLBACK IS DECLARED — `CODER.md` §4.2 and
 *    §3.10: at the start of the connection `smoothed_rtt` and `cwnd` do not have
 *    a value yet, and the size of a keyframe does not exist until one has
 *    left.  ⇒ In those cases we go back to the previous constant and write
 *    **which** of the three cases it is, instead of passing an invented number off as
 *    a measured number.  ⚠ `*come` is not an ornament of the log: it is
 *    the only thing that tells «the cure is working» from «the cure is not
 *    on yet», and without it the two look the same.
 */
static uint64_t chiave_intervallo_ms(wt *w, const char **come)
{
	ngtcp2_conn_info info;
	uint64_t ms;
	size_t in_coda = 0;

	if (!w->conn) {
		*come = "fallback: there is no connection";
		return WT_CHIAVE_RICHIESTA_MS;
	}

	/* ⛔⭐⭐ BEFORE ANY ESTIMATE: IF THE PREVIOUS KEYFRAME IS STILL HERE, THE
	 *       ANSWER IS NOT AN ESTIMATE — IT IS A FACT.
	 *
	 *       The sentence of the defect is «we ask for a new keyframe before the
	 *       previous one has left», and this loop knows **whether it has left**: they are
	 *       the same bytes `video_sgombra()` counts to say «KEYFRAME N
	 *       still holds %zu bytes in the queue and §5.2 forbids abandoning it».
	 *
	 * ⭐ Looking here instead of computing is better for a reason that holds
	 *    beyond this line: an estimate can be wrong, a byte in the queue cannot.  The
	 *    measured bandwidth stays below, as a **backstop** for the bytes already handed
	 *    to ngtcp2 and not yet acknowledged — those the queue no longer sees.
	 *
	 * ⛔ And the cap holds HERE TOO, and it is the reason it exists: if the
	 *    line does not carry the keyframe away, after two seconds one is requested
	 *    all the same.  A screen frozen forever is not «ugly», it is half
	 *    closed (I1). */
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo && w->involo[i].chiave)
			in_coda += coda_byte_stream(w, w->involo[i].stream);
	if (in_coda > 0) {
		*come = "🔸 the previous KEYFRAME has not gone out yet (bytes in the queue)";
		/* ⚠ The log backstop is the same as the computed road's: the line
		 *   is written by that branch, here the cap is enough. */
		return WT_CHIAVE_TETTO_MS;
	}

	if (!w->chiave_byte) {
		*come = "fallback: no KEYFRAME sent yet, its size does not exist";
		return WT_CHIAVE_RICHIESTA_MS;
	}
	memset(&info, 0, sizeof info);
	ngtcp2_conn_get_conn_info(w->conn, &info);
	if (info.smoothed_rtt == 0 || info.cwnd == 0) {
		*come = "fallback: ngtcp2 has neither rtt nor window yet";
		return WT_CHIAVE_RICHIESTA_MS;
	}

	/* time (ns) = bytes × rtt(ns) / cwnd(bytes) → ms, plus the margin.
	 * ⚠ The order of the factors is the one that does not overflow: 60 000 × 30 000 000 =
	 *   1.8e12, well within a `uint64_t`. */
	ms = w->chiave_byte * info.smoothed_rtt / info.cwnd / NGTCP2_MILLISECONDS;
	ms = ms * WT_CHIAVE_MARGINE_PC / 100u;

	if (ms <= WT_CHIAVE_RICHIESTA_MS) {
		*come = "the measured bandwidth is enough: the 150 ms backstop remains";
		return WT_CHIAVE_RICHIESTA_MS;
	}
	if (ms > WT_CHIAVE_TETTO_MS) {
		*come = "⛔ the bandwidth would not be enough even for the cap: held at 2 s, "
		        "and the image stays broken longer";
		ms = WT_CHIAVE_TETTO_MS;
	} else {
		*come = "🔸 from the measured bandwidth (cwnd/rtt)";
	}

	/* ⛔ THE PRICE IS WRITTEN, and once only for every time it changes: it is
	 *    visible to the user (the image stays broken longer) and visible
	 *    prices are judged by him.  ⚠ With a backstop, or at fifty heartbeats a
	 *    second this line would fill the log instead of telling it. */
	if (w->chiave_attesa_detta_ms == 0
	    || (ms > w->chiave_attesa_detta_ms
	        ? ms - w->chiave_attesa_detta_ms
	        : w->chiave_attesa_detta_ms - ms) >= 100) {
		w->chiave_attesa_detta_ms = ms;
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "🔸 %s: the KEYFRAME can be requested every %llu ms instead "
		                 "of %u — the last one measured %llu bytes and the MEASURED bandwidth is "
		                 "%llu kbit/s (cwnd %llu bytes / rtt %llu ms, the two numbers "
		                 "ngtcp2 uses to decide how much to send).  ⛔ THE PRICE: "
		                 "on a narrow line the image stays broken longer after "
		                 "a loss.  ⭐ In exchange audio gets through: asking for the "
		                 "new keyframe before the old one had gone out kept "
		                 "`cwnd_left` at zero and destroyed the datagrams (bench 07-b65)",
		                 w->provenienza, (unsigned long long)ms,
		                 (unsigned)WT_CHIAVE_RICHIESTA_MS,
		                 (unsigned long long)w->chiave_byte,
		                 (unsigned long long)(info.cwnd * 8ull * NGTCP2_SECONDS
		                                      / info.smoothed_rtt / 1000ull),
		                 (unsigned long long)info.cwnd,
		                 (unsigned long long)(info.smoothed_rtt / NGTCP2_MILLISECONDS));
	}
	return ms;
}

static void audio_regola(wt *w)
{
	uint32_t l, a;
	uint8_t codec;
	const char *utente;

	/* ⚠ `audio_fermo` does here the same job `video_fermo` does in the
	 *   twin: if capture had been switched off because nobody was listening
	 *   any more, a new session must be able to restart it.  Without it, the
	 *   reattach would be mute. */
	if (!w->rcp || w->chiusura >= 0 || (w->audio_acceso && !w->audio_fermo))
		return;
	/* ⛔ The same trap as the twin, and the box is on `video_regola()`:
	 *    `rcp_tela_in_vigore()` does not look at the state, so without this line
	 *    a finished session would switch capture back on at every heartbeat. */
	if (rcp_e_finita(w->rcp))
		return;

	/* ⛔ Invariant I3: no sound before `SESSIONE` has left.  It is the
	 *    same guard as video, for the same reason — whoever has not gone
	 *    through the validator does not receive a pixel, nor a sample. */
	if (!rcp_tela_in_vigore(w->rcp, &l, &a))
		return;

	codec = rcp_audio_negoziato(w->rcp);
	if (codec == 0) {
		if (!w->audio_detto) {
			w->audio_detto = true;
			registro_dice_di(REG_RCP, wt_chi(w),
			                 "%s: no audio codec negotiated (§4.3) — this "
			                 "session has no audio",
			                 w->provenienza);
		}
		return;
	}

	utente = rcp_utente(w->rcp);
	if (!utente || !utente[0])
		return;

	w->audio_acceso = true;
	w->audio_fermo = false;
	w->audio_codec = codec;
	/* ⛔ AND THE TEST TONE IS NAMED HERE, at every session — finding 8.
	 *    `wt_audio_prova()` writes a single line, at startup: whoever read the
	 *    log an hour later saw «audio channel on» and **had no way
	 *    of knowing that what the user hears is a bench signal**.
	 *    The I6 switch was there; the declaration that must follow it was not. */
	registro_dice_di(REG_RCP, wt_chi(w),
	                 "⭐ PHASE 7: audio channel ON for «%s» from %s — codec %u (%s), "
	                 "48 000 Hz, 2 channels (§5.3).  The peer accepts datagrams of %llu "
	                 "bytes%s",
	                 utente, w->provenienza, codec,
	                 codec == 1 ? "Opus" : "PCM",
	                 (unsigned long long)dgram_tetto_del_pari(w),
	                 audio_prova_hz
	                     ? "  ⚠⚠ AND WHAT WILL BE HEARD IS THE TEST TONE, not the "
	                       "desktop: `--audio-prova` is on (bench function, I6)"
	                     : "");

	/* ⛔ And the child is asked to capture — but NOT with the test tone on:
	 *    there the source is this process, and switching on real capture too
	 *    would mean two sources on the same channel.  ⚠ The client would hear
	 *    the two mixed and the bench would measure a scene the product will never
	 *    have. */
	if (gancio_audio && !audio_prova_hz)
		gancio_audio(gancio_audio_ctx, utente, codec);
}

static void video_regola(wt *w, uint64_t ora_ms)
{
	uint32_t l = 0, a = 0;
	uint8_t codec;
	const char *utente;

	if (!w->rcp || w->chiusura >= 0)
		return;

	/* ⛔⛔⭐⭐ AND A FINISHED SESSION SWITCHES NOTHING BACK ON — 23 Sep 2026, and it is
	 *        the line without which the cure for waste BECOMES A WORSE
	 *        WASTE.  Found by reading, not by measuring, and it is worth
	 *        writing it out in full because the trap is made on purpose not to be
	 *        seen:
	 *
	 *        `rcp_tela_in_vigore()` below does NOT look at the state — it looks at
	 *        `sessione_spedita`, which once true **stays true even after the
	 *        end**.  ⇒ On a «finished» session this function goes all the way to
	 *        the bottom as if nothing were wrong.  Before it did no harm (`video_acceso`
	 *        was already true and the switch-on branch was not taken); from
	 *        today, with `video_fermo` on, it would take it — and in `wt_batti()`
	 *        `video_regola()` comes BEFORE `regola_battito()`.
	 *
	 *        ⇒ Every heartbeat: switch on, switch off again.  Two messages to the child and two
	 *        log lines a second, for all the 30 s of the
	 *        `max_idle_timeout` — that is exactly the defect being
	 *        cured, with an unreadable log on top.
	 *
	 * ⚠ And it takes nothing away from REATTACH: a new session on the same
	 *   connection has a NEW `w->rcp` (`rcp_avvia()` runs only with
	 *   `rcp_stream == -1`, and `wt_stream_chiuso()` resets both together),
	 *   so `rcp_e_finita()` is false and capture restarts as it should.
	 *   ⛔ `S_FINITA` is terminal: there is no going back from there — only
	 *   `S_STACCATA` can resurrect (`torna_a_parlare()`), and that one does not go
	 *   through here. */
	if (rcp_e_finita(w->rcp))
		return;

	/* ⛔ P1 / §2.5 / invariant I3 — «no video stream before having
	 *    SENT `SESSIONE`».  `rcp_tela_in_vigore()` answers `false` until
	 *    `SESSIONE` has left, and writes nothing in the log: calling
	 *    `rcp_video_apri()` to find out would fill the log with one line a
	 *    second for every session waiting for the password. */
	if (!rcp_tela_in_vigore(w->rcp, &l, &a))
		return;

	codec = rcp_codec_negoziato(w->rcp);
	if (codec == 0) {
		if (!w->video_detto) {
			/* ⚠ It is not a defect: a phase 1 client declares no
			 *   codec, and §4.3 proves it right. */
			w->video_detto = true;
			registro_dice_di(REG_RCP, wt_chi(w),
			                 "%s: no codec negotiated (§4.3) — this session "
			                 "has no video, and it is what phase 1 did",
			                 w->provenienza);
		}
		return;
	}

	utente = rcp_utente(w->rcp);
	if (!utente || !utente[0])
		return;

	/* ⛔⭐⭐ AND `video_fermo` IS THE HALF THAT RESTARTS CAPTURE.
	 *
	 *      Since the loop switches off at farewell (see `regola_battito()`),
	 *      «the channel is on» no longer implies «the stage is capturing».
	 *      ⛔ Without this condition the cure for waste would break the
	 *      REATTACH: a new session on the same connection — a state
	 *      foreseen twice in this file, and `wt_stream_chiuso()` puts
	 *      `w->sessione` back to -1 on purpose so that it can open — would find
	 *      `video_acceso` already true, would skip this branch, and would NEVER ask the child
	 *      to start again.  The user would be left in front of a
	 *      frozen screen.
	 *
	 * ⚠ We go through here as soon as the new session's `SESSIONE` has left
	 *   (`rcp_tela_in_vigore()` above), and we start again with a KEYFRAME —
	 *   which is what §5.2 wants anyway from the first frame. */
	if (!w->video_acceso || w->video_fermo) {
		bool ripartenza = w->video_fermo;
		w->video_acceso = true;
		w->video_fermo = false;
		w->video_codec = codec;
		w->chiave_chiesta_ms = ora_ms;
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⭐ PHASE 3: video channel %s for «%s» from %s — codec %u, "
		                 "canvas %ux%u.  Asking the stage to capture continuously, and "
		                 "§5.2 wants the FIRST to be a KEYFRAME",
		                 ripartenza ? "SWITCHED BACK ON (the loop was stopped: nobody was "
		                              "watching it any more)"
		                            : "ON",
		                 utente, w->provenienza, codec, l, a);
		if (gancio_palco)
			gancio_palco(gancio_palco_ctx, utente, codec,
			             rcp_profondita_negoziata(w->rcp),
			             rcp_livello_negoziato(w->rcp), true);
		return;
	}

	/* ⛔ And here the requested keyframe really reaches the encoder. */
	{
		const char *come = NULL;
		uint64_t attesa = chiave_intervallo_ms(w, &come);

		if (rcp_video_serve_chiave(w->rcp)
		    && ora_ms - w->chiave_chiesta_ms >= attesa) {
			w->chiave_chiesta_ms = ora_ms;
			if (gancio_palco)
				gancio_palco(gancio_palco_ctx, utente, codec,
				             rcp_profondita_negoziata(w->rcp),
				             rcp_livello_negoziato(w->rcp), true);
			registro_dettaglio_di(REG_RCP, wt_chi(w),
			                           "%s: §5.2 wants a KEYFRAME — request forwarded to the "
			                           "stage of «%s» (codec %u), after %llu ms of waiting "
			                           "(%s)",
			                           w->provenienza, utente, codec,
			                           (unsigned long long)attesa, come);
		}
	}
}

/* ⛔⭐⭐ THE SECOND BELT, and it is called by whoever PAYS for the block: the refused
 *       frame.  The why and the numbers are on `WT_CHIAVE_DEBITO_TETTO_MS`
 *       and on `batti_fra()`.
 *
 * ⚠ It does not request anything by itself: it calls `video_regola()`, which is the only place
 *   where the request to the stage is made — so the backstop of
 *   `chiave_intervallo_ms()` keeps holding and two policies for
 *   the same thing are not born.
 *
 * ⛔ And the line is written ONCE per episode: the log of the measured
 *    session had **45 278** of the same refusal, that is 40 MB in which the
 *    block was invisible precisely because it was always shouting. */
static void video_rifiutato_per_chiave(wt *w, uint64_t ora_ms)
{
	if (ora_ms - w->chiave_chiesta_ms < WT_CHIAVE_DEBITO_TETTO_MS)
		return;
	if (!w->debito_detto) {
		w->debito_detto = true;
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⛔ %s: the KEYFRAME debt (§5.2) has been on for %llu ms "
		                 "and no keyframe has arrived — every delta is refused, "
		                 "that is the SCREEN IS FROZEN.  ⭐ Requesting the keyframe from the stage "
		                 "from here, without waiting for the heartbeat: it is the second belt "
		                 "of 23 Sep 2026, and the first (`batti_fra()`) evidently "
		                 "was not enough",
		                 w->provenienza,
		                 (unsigned long long)(ora_ms - w->chiave_chiesta_ms));
	}
	video_regola(w, ora_ms);
}

/* ------------------------------------------------------------------------ */
/* ⭐⭐ THE RATE REGULATOR — phase 9, and the rate drops HERE.               */
/*
 * ⛔ THE RULE, IN FULL: `arretrato == 0` ⇒ send; `arretrato >= POSTI`
 *    ⇒ this frame does NOT leave.  Nothing else.  There is no target
 *    rate, no computed bandwidth, no client acknowledgement, and
 *    above all no number that has to rise back.
 *
 * ⛔ AND THE DROP IS NOT A NUMBER GOING DOWN: it is a frame that does not
 *    leave.  The rate drops by itself, as much as the queue does not empty, and
 *    rises by itself when it empties — because the quantity is REREAD, not
 *    remembered.  ⭐ No ratchet: it is the mistake `qualita_corrente`
 *    made (it went down and never came back up) and it cost a cure of its own.
 *
 * ⛔ WHY IT IS NOT A STOPWATCH — and it is the family of errors
 *    P8 → P11 → P13 → P14 → P19 → P20 of `RCP.md`, avoided instead of
 *    repeated.  P13 said «for one second» and was corrected two hours later:
 *    *«the second was the wrong quantity: what must empty is a
 *    QUEUE, and how long a frame already in flight takes depends on the BANDWIDTH,
 *    not on the clock»*.  P20 said «whoever receives a frame before
 *    SESSIONE», and the cure was to look at what the peer had SENT ITSELF:
 *    local, monotonic, independent of delivery.  ⇒ `arretrato` has
 *    exactly that shape on our side: it is BYTES PRODUCED BY US AND
 *    STILL IN OUR HOUSE.  No lost packet, no reordering and no
 *    client silence can distort it, because nothing coming
 *    from outside is looked at.  ⭐ And the sentence is already in the code, written for the same
 *    reason: *«an estimate can be wrong, a byte in the queue cannot»*.
 *
 * ⛔ GNOME'S QUANTITY (the client's frame acknowledgements) IS REJECTED,
 *    and for three independent reasons: (1) here they DO NOT EXIST — the table of
 *    messages of `RCP.md` has no frame acknowledgement, and adding one
 *    would mean a network round trip INSIDE the control loop, that is
 *    buying reaction by paying for it in delay (`SPECIFICHE.md:128-131` asks to
 *    justify it in ms; `arretrato` costs **0 ms**, it is already in our
 *    memory); (2) the peer CAN FREEZE THEM and the regulator would stop for
 *    ever — and a loop the peer can freeze does not become safe
 *    because an `if` is added; (3) their threshold
 *    (`rtt * refresh_rate / 1e6`) is a disguised clock, that is P13 in
 *    another dress.
 *
 * ⛔ AND KEYFRAMES DO NOT COUNT — `RCP.md` §5.2 forbids abandoning them, §5.1 says
 *    that the deltas coming after are not blocked by them (streams are
 *    independent), and their rhythm is already handled by `chiave_intervallo_ms()`.
 *    Counting them here would stop delta production for the whole duration of a
 *    slow keyframe, which is exactly the opposite of `SPECIFICHE.md` §8.3.
 *
 * ⚠ THE PRICE IN MILLISECONDS, declared: **0**.  This regulator does not
 *   add any intermediate memory, so it does not buy smoothness and does not
 *   sell responsiveness (`SPECIFICHE.md:128-131`).  It removes work, it does not postpone it.
 *
 * ⚠ THE PRICE THAT IS THERE INSTEAD: it cuts DOWNSTREAM of the encoder, so the
 *   skipped frame has already paid for the child's GPU.  The real lever — not
 *   capturing it at all — is in the child, and ⛔ it is NOT done in phase 9 for an
 *   architectural reason: the stage is ONE per user and the sessions are N,
 *   so a rate imposed on the stage would impose it on all of them and the session on the
 *   good line would pay for the one on the bad line.  `[?]` open.
 *
 * ⛔ THE BOTTOM OF THE SCALE IS A VERDICT, NOT A BRAKE.  `DECISIONI.md` §2.1:
 *    the line is 20 Mbit/s, the image 480p·25.  Below 25/s on a
 *    20 Mbit/s line it is a DEFECT, not a successful degradation — and the cure is NOT
 *    forcing a frame into a queue that does not empty, because that
 *    only makes the queue worse.  ⇒ There is no floor in this code:
 *    there is the count `video_ritmo_scesi` next to the delivered frames, and whoever
 *    reads the log DECLARES the defect instead of fighting it.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⛔⭐⭐ THE FALSIFIABLE PREDICTION — written BEFORE any measurement.
 * ───────────────────────────────────────────────────────────────────────────
 *
 * ⭐ THIS IS A GUARDRAIL, AND ITS CORRECT BEHAVIOUR IS TO DO
 *    NOTHING.  A bench that proved only that it does not fire would have proved
 *    half the work; the other half is proving the loop was
 *    WALKED while it did not fire.
 *
 * 1. IN STEADY STATE, at 20 Mbit/s on the real path, moving scene, 1080p, hardware
 *    H.264, with the defaults of 24 Aug 2026 (threshold 100 ms + regulator):
 *
 *      | frames delivered      | **20-37/s** — those the scene produces    |
 *      | bytes going out       | **3-12 Mbit/s**, between a sixth and half |
 *      | `arretrato`           | **0, now and then 1.  Never 2**           |
 *      | `video_ritmo_scesi`   | ⭐ **0** — zero drops                     |
 *
 * 2. ON THE STEP — and it is where it must fire.  Same step already measured:
 *    wide line → **3 s at 10 Mbit/s** → wide, scene `barra`, 1920x1080.
 *
 *      | `arretrato` during the 3 s  | rises to **2-3**                   |
 *      | drops (`ritmo_scesi`)       | **> 0**, and concentrated in the 3 s |
 *      | log lines                   | **2 per episode** (DROPS/RISES),   |
 *      |                             | NOT one per frame                  |
 *      | frames/s in the 3 s         | **>= 25** and made of DELTAS       |
 *      | of which KEYFRAME, per second | **<= 2** (without regulator: 6-7) |
 *      | seconds of wide line        | **identical** to today: inert      |
 *      | the RISE, after the step    | within **1 s** of the return       |
 *
 * 3. ⛔ THAT IT DOES NOT DROP ON A STILL SCENE — and the control can NOT be «the
 *    counter is zero»: empty and forbidden look the same
 *    (`LEZIONI.md` §1.9), and a zero on a branch never reached proves
 *    nothing.  ⭐ The structural proof comes first: `arretrato` is
 *    read ONLY when a frame arrives from the stage, and on a still scene a
 *    Wayland compositor delivers none — `video_a_una()` is not even
 *    called.  A quantity measuring bytes/s, or CPU ms, or
 *    «how long I have not sent» would instead be perfectly capable of dropping
 *    on a motionless desktop, and it is v1's wound (*«on a barely moving desktop
 *    it went down to 2-6 Mbit/s, happy to save»*).
 *
 *    ⇒ THE EXPERIMENTAL CONTROL IS DONE IN PAIRS, IN THE SAME RUN: half
 *    still scene and half moving scene, ALTERNATED, not two separate runs.  And the
 *    line that makes it readable is the one of `ritmo_ciclo()`, one a second,
 *    which comes out even when no frames arrive at all.  ⭐ The exact
 *    shape, and it is a contract on the text:
 *
 *      rate of IND:PORTA: arretrato READ 0 times in the last second,
 *      maximum 0, last 0, slots 2 — 0 frames not sent in this
 *      second, 0 in total.  ⚠ ZERO READS = the stage delivered
 *      nothing (still scene), and NOT «arretrato zero»
 *
 *    Green is: `video_ritmo_scesi` UNCHANGED for the whole still half —
 *    with the lines saying «READ 0 times», that is that the branch was not
 *    walked — AND `arretrato` read at least once a second in the moving
 *    half.  ⛔ A run that does not satisfy the second point HAS MEASURED
 *    NOTHING, and must be thrown away instead of interpreted.
 *
 * ⛔ THE REDS THAT WOULD PROVE ME WRONG, and each says where to look:
 *
 *  a. **drops at 20 Mbit/s with a normal desktop** ⇒ either `POSTI = 2` is
 *     too tight, or a frame costs much more than measured.  The line
 *     carries `cwnd`, `cwnd_left`, bytes in flight and bytes in the queue: it says by itself
 *     which of the two;
 *  b. ⛔⛔ **drops with a WIDE congestion window** (`cwnd_left` high)
 *     ⇒ IT IS NOT THE LINE, it is the BROWSER: it is its flow window
 *     (`initial_max_stream_data_uni` / `initial_max_data`, which it decides and
 *     we do not touch) or the pacer.  The cure would be elsewhere and this
 *     regulator would be braking for a defect that is not its own.  It is the most
 *     important red, because it produces a loop that SEEMS to work well;
 *  c. **`video_saltati` growing while `arretrato` stays 0** ⇒ the bottleneck is
 *     stream credit (§2.3, cause 4 of the debt), not bandwidth, and
 *     this regulator has nothing to do with it: look at `sgombra_credito`;
 *  d. **zero drops and ZERO READS in the moving half** ⇒ it is not a
 *     confirmed prediction, it is a loop never walked.  Almost certainly the
 *     queue threshold is off (see `wt_ritmo_adattivo()`);
 *  e. **the RISE never arrives after the line comes back** ⇒ something
 *     holds bytes in the queue that do not go away, and it is not the rate: look at
 *     the peak of `byte_in_volo` and the streams never closed.
 *
 * ⇒ Returns `true` when this frame must NOT leave.
 */
static bool ritmo_frena(wt *w, bool chiave, uint64_t ora_ms)
{
	unsigned arretrato = 0;
	size_t in_coda = 0;

	if (!ritmo_adattivo)
		return false;
	/* ⛔ Keyframes do not go through here: §5.2 and `chiave_intervallo_ms()`. */
	if (chiave)
		return false;

	/* ⛔ IT IS READ BEFORE `video_sgombra()`, which a few lines below empties that
	 *    queue: afterwards, `arretrato` would always be zero and this loop
	 *    would never fire.  ⚠ `coda_byte_stream()` counts the bytes that have NOT
	 *    YET left our house — an element already handed to ngtcp2 has
	 *    `off == dati.n` and is worth zero, even if after the cure of 23 August its
	 *    memory is still ours.  ⇒ The quantity stayed the same. */
	for (size_t i = 0; i < w->ninvolo; i++) {
		size_t resto;
		if (!w->involo[i].vivo || w->involo[i].chiave)
			continue;
		resto = coda_byte_stream(w, w->involo[i].stream);
		if (resto == 0)
			continue;
		in_coda += resto;
		arretrato++;
	}

	/* ⭐ THE READ IS COUNTED, always, even when it is worth zero: it is what
	 *    tells «the loop was walked and the backlog was zero» from
	 *    «the loop was not walked at all» (`LEZIONI.md` §1.9). */
	w->ritmo_letture++;
	w->ritmo_ultimo = arretrato;
	if (arretrato > w->ritmo_max)
		w->ritmo_max = arretrato;

	if (arretrato >= WT_RITMO_POSTI) {
		if (!w->ritmo_giu) {
			ngtcp2_conn_info in;
			uint64_t rtt_ms;
			char rete[96];

			memset(&in, 0, sizeof in);
			ngtcp2_conn_get_conn_info(w->conn, &in);
			rtt_ms = in.smoothed_rtt / NGTCP2_MILLISECONDS;
			/* ⛔⭐ `smoothed_rtt - min_rtt` IS THE QUEUE INSIDE THE NETWORK, IN
			 *     MILLISECONDS: it is the number with which `SPECIFICHE.md:128` —
			 *     «every intermediate memory buys smoothness and sells responsiveness» —
			 *     is honoured instead of quoted.  ⚠ And it is the first time
			 *     `min_rtt` is read: `ngtcp2_conn_get_conn_info()` has always filled it
			 *     and we looked at two fields out of seven.
			 *
			 * ⛔ BUT `min_rtt` IS `UINT64_MAX` UNTIL A SAMPLE HAS ARRIVED, and the
			 *    subtraction would give a huge number that LOOKS
			 *    measured — shape E1, the worst.  ⇒ «not yet
			 *    known» is declared instead of printing garbage. */
			if (in.min_rtt != UINT64_MAX && in.min_rtt != 0
			    && in.smoothed_rtt >= in.min_rtt)
				snprintf(rete, sizeof rete,
				         "%llu ms of queue inside the network (rtt %llu - min %llu)",
				         (unsigned long long)((in.smoothed_rtt - in.min_rtt)
				                              / NGTCP2_MILLISECONDS),
				         (unsigned long long)rtt_ms,
				         (unsigned long long)(in.min_rtt / NGTCP2_MILLISECONDS));
			else
				snprintf(rete, sizeof rete,
				         "queue inside the network NOT YET KNOWN (min_rtt missing)");
			w->ritmo_giu   = true;
			w->ritmo_da_ms = ora_ms;
			w->ritmo_da_n  = w->video_ritmo_scesi;
			/* ⛔⭐ INVARIANT I1: «the rate never drops out of caution, to
			 *     save, or because the scene is still.  It drops only when the
			 *     MEASUREMENT proves the line does not carry, and every drop is
			 *     declared in the log».
			 *
			 * ⭐ AND THE LINE CARRIES THE MEASUREMENT NEXT TO THE THRESHOLD: `arretrato` and the
			 *    slots, one next to the other.  If the measurement were below the
			 *    threshold, that drop would have been out of caution — and the line
			 *    itself would prove it, instead of leaving it to be deduced.
			 *
			 * ⚠ ONE LINE PER EPISODE, not per frame: at 60/s the second
			 *   shape is the defect of the 30.8 GB of log. */
			registro_dice_di(REG_RCP, wt_chi(w),
			                 "⛔ %s: the rate DROPS — backlog %u deltas against %u "
			                 "slots, %zu bytes stuck in the video queue (%zu in "
			                 "total).  cwnd %llu, cwnd_left %llu, in flight for ngtcp2 "
			                 "%llu, mine handed over and not acknowledged %zu, rtt %llu "
			                 "ms, %s.  ⭐ It is not caution and it is not a clock: it is the "
			                 "queue that does not empty (I1).  ⚠ If cwnd_left is HIGH "
			                 "it is not the line, it is the browser's window",
			                 w->provenienza, arretrato, (unsigned)WT_RITMO_POSTI,
			                 in_coda, w->byte_in_coda,
			                 (unsigned long long)in.cwnd,
			                 (unsigned long long)ngtcp2_conn_get_cwnd_left(w->conn),
			                 (unsigned long long)in.bytes_in_flight,
			                 w->byte_in_volo,
			                 (unsigned long long)rtt_ms, rete);
		}
		w->video_ritmo_scesi++;
		/* ⛔⛔⭐ AND THE DROP PAYS FOR THE KEYFRAME — 23 Sep 2026, and without this
		 *      line the phase 9 regulator smashed the image silently.
		 *
		 *      The frame thrown away here has **already been encoded** by the child:
		 *      it arrives from `wt_video_diffondi()` as stream bytes, and the
		 *      encoder has already moved its references forward.  ⇒ The
		 *      delta that comes after leans on a frame the client will
		 *      never receive, and the decoder raises no error: it just
		 *      produces images more and more smashed (§5.2).
		 *
		 * ⛔ AND NOBODY NOTICES, on either side: the `numero`
		 *    is born in `rcp_video_apri()`, which is not reached from here, so the
		 *    numbering that reaches the client stays CONTINUOUS and §5.2 makes it
		 *    ask for a keyframe only on a hole.  `[M]` 23 Sep 2026,
		 *    `due-inquilini` on `rete11-gnome`: 27 and 38 frames thrown away here,
		 *    **0 holes** in the numbering, **1 single keyframe** in the whole
		 *    session, **0** `RICHIEDI_CHIAVE` — and the user seeing the image
		 *    in tiles with all counters green.
		 *
		 * ⚠ And the comment at the top of this function PROMISED the opposite —
		 *   «the regulator stops PRODUCING; it does not throw away what is already there» —
		 *   but the brake is downstream, after encoding, and `ritmo_giu` never leaves
		 *   this file.  ⏳ Carrying it as far as the child is the cure of the COST
		 *   (fewer discards ⇒ fewer keyframes) and it is a second step: here we buy
		 *   CORRECTNESS, which is not negotiable.
		 *
		 * ⭐ The price is NOT one keyframe per braked frame: `serve_chiave` is
		 *    a boolean (`rcp.c`), it switches off only when the keyframe has gone out
		 *    whole, so a braking episode costs ONE keyframe.  And the deltas
		 *    behind that keyframe are not abandoned (the cure of the spiral,
		 *    a50b389), which is precisely the case of the keyframe sent under
		 *    congestion. */
		rcp_video_scartato_prima_del_filo(
		    w->rcp, chiave,
		    "the rate regulator braked it (phase 9: the backlog has "
		    "reached the slots) — but the child had already ENCODED it, and the "
		    "encoder's references moved on without it");
		/* ⛔⛔⭐ AND THE KEYFRAME IS REQUESTED NOW, NOT AT THE NEXT HEARTBEAT — 23 Sep
		 *      2026, and it is the price of this morning's cure measured and removed.
		 *
		 *      With the debt on `rcp_video_apri()` refuses EVERY delta
		 *      (`rcp.c`, the `RCP_VIDEO_SERVE_UNA_CHIAVE` branch): until the
		 *      keyframe goes out, the user's screen is FROZEN.  ⇒ How long
		 *      that darkness lasts is not a detail, it is the rate. */
		video_regola(w, ora_ms);
		return true; /* ⛔ this frame does NOT leave: it IS the drop */
	}

	/* ⭐ AND NOBODY DECIDES THE END OF THE EPISODE: the queue has emptied
	 *    and the backlog is back to zero.  There is no number to raise back,
	 *    no hysteresis and no rise delay — it is the merit of the
	 *    quantity that is reread instead of remembered. */
	if (w->ritmo_giu && arretrato == 0) {
		w->ritmo_giu = false;
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⭐ %s: the rate RISES — the episode lasted %llu ms and "
		                 "%u frames were left behind.  ⚠ Nobody decided it: "
		                 "the queue emptied and the backlog is zero",
		                 w->provenienza,
		                 (unsigned long long)(ora_ms - w->ritmo_da_ms),
		                 w->video_ritmo_scesi - w->ritmo_da_n);
	}
	return false;
}

/* ⛔⭐ THE ONCE-A-SECOND LINE THAT MAKES «it does not drop on a still scene» FALSIFIABLE.
 *
 *     It runs with the HEARTBEAT and not with the frames, on purpose: if it ran with
 *     frames, on a still scene nothing would come out — and «the loop was not
 *     walked» would again look the same as «the backlog was
 *     zero», which is precisely the defect this line exists to remove
 *     (`LEZIONI.md` §1.9; and it is the same cure as the child's `ciclo:` line,
 *     which is written BEFORE looking at the outcome of the capture).
 *
 * ⚠ It comes out only with the switch on: it is the instrument of a bench, not a
 *   product line, and with a still session it would be one line a second for
 *   ever. */
static void ritmo_ciclo(wt *w, uint64_t ora_ms)
{
	if (!ritmo_adattivo || !w->rcp || w->chiusura >= 0)
		return;
	if (ora_ms - w->ritmo_detto_ms < 1000)
		return;
	w->ritmo_detto_ms = ora_ms;
	registro_dice_di(REG_RCP, wt_chi(w),
	                 "rate of %s: backlog READ %u times in the last second, "
	                 "maximum %u, last %u, slots %u — %u frames not sent in "
	                 "this second, %u in total.  ⚠ ZERO READS = the stage delivered "
	                 "nothing (still scene), and NOT «backlog zero»",
	                 w->provenienza, w->ritmo_letture, w->ritmo_max, w->ritmo_ultimo,
	                 (unsigned)WT_RITMO_POSTI,
	                 w->video_ritmo_scesi - w->ritmo_detti_n, w->video_ritmo_scesi);
	w->ritmo_letture = 0;
	w->ritmo_max = 0;
	w->ritmo_detti_n = w->video_ritmo_scesi;
}

/* ========================================================================== */
/* ⛔⭐⭐ PHASE 9 — THE LINE THAT ATTRIBUTES THE DELAY TO WHOEVER TOOK IT.      */
/*                                                                            */
/*      THE HOLE IT CLOSES.  A frame arriving late has four possible          */
/*      fathers, and until this line the log could recognise                  */
/*      only two:                                                             */
/*                                                                            */
/*        (a) a packet lost and resent by QUIC            ⛔ IT DID NOT SHOW   */
/*        (b) the congestion window that closed           ⛔ IT DID NOT SHOW   */
/*        (c) us keeping it in the queue                  ✅ `sgombra_tenuti`  */
/*        (d) us abandoning it                            ✅ `sgombra_abbandoni`*/
/*                                                                            */
/*      ⇒ Without (a) and (b) every measurement under loss ends in a discussion*/
/*      — «is it the line or is it us?» — instead of an attribution.  And the  */
/*      project has a rule: every number must be attributed by itself.        */
/*                                                                            */
/* ⛔⛔ IT IS ONLY OBSERVATION.  This function READS and WRITES, and that is all: */
/*      no decision, no threshold, no rate, no transport state                */
/*      touched.  ⇒ There is nothing to put behind a                         */
/*      switch (invariant I6), because it changes nothing of what             */
/*      the user SEES.  If one day something had to change to be able to      */
/*      write it, that is another cure and goes behind a switch that is off.  */
/*                                                                            */
/* ⭐ THE EXAMPLE LINE — AND IT IS A CONTRACT ON THE TEXT, because it is the one */
/*    a bench will look for with a `grep` and split with a `split`:            */
/*                                                                            */
/*      rete-quic 192.168.1.9:52344 da_ms=1002 persi=7 persi_d=3              */
/*      byte_persi=9856 byte_persi_d=4224 spediti=48210 spediti_d=812         */
/*      byte_spediti=59284410 ricevuti=3011 ricevuti_d=61 scartati=0          */
/*      scartati_d=0 cwnd=48000 cwnd_left=0 ssthresh=32000 involo=47180       */
/*      srtt_us=41230 latest_us=52980 rttvar_us=11400 min_rtt_us=22100        */
/*      coda_rete_us=19130 pto_us=132000 dgram_persi=n/d                      */
/*      giudizio=⛔ the line is losing                                        */
/*                                                                            */
/*    (in the log it is ALL ON ONE LINE: here it wraps only to fit in the     */
/*    box.)  The format rules, and they are three:                            */
/*                                                                            */
/*      1. the prefix `rete-quic` is STABLE and it is the first word of the body: */
/*         `grep 'rete-quic '` takes all the lines and nothing else;          */
/*      2. every field is `nome=valore` without spaces in the value, separated by ONE */
/*         space — `split()` and then `split('=', 1)` are enough.  The second field */
/*         has no `=` and it is the origin (IND:PORTA), which has no spaces;  */
/*      3. ⛔ `giudizio=` IS THE LAST FIELD, and its value runs to the END OF  */
/*         THE LINE spaces included: it is the only one containing them, on purpose, because */
/*         it must be readable by a human without fake dashes.  A bench takes */
/*         it with `riga.split('giudizio=', 1)[1]`.                           */
/*                                                                            */
/* ⚠ THE UNITS ARE IN THE NAMES, and the rtt is in MICROseconds while the rest */
/*   of the file prints it in milliseconds.  It is not absent-mindedness: the target */
/*   of the phase is jitter, and `rttvar` on a local network is below one     */
/*   millisecond — rounded to ms it would be `0` and would hide precisely the */
/*   fact being looked for.  ⇒ `_us` on the name, and the reader does not err. */
/*                                                                            */
/* ⚠ `da_ms` IS THE REAL INTERVAL, and the `_d` fields hold OVER IT — not «per */
/*   second».  The line comes out at most once a second, but keeps quiet when nothing */
/*   has changed: after a 12 s silence `da_ms` says 12000 and the             */
/*   differences cover 12 s.  ⛔ Calling them `_1s` would have been a number that */
/*   LOOKS measured and is not — shape E1.  On the FIRST line `da_ms=0` and   */
/*   the differences are worth the totals, that is the whole connection.      */
/*                                                                            */
/* ⛔ WHAT IS NOT THERE, and it must be said here because an absent field is noticed and a */
/*    missing field is not:                                                   */
/*                                                                            */
/*    · **RETRANSMITTED ones do not exist in ngtcp2 1.25** `[S]`.  QUIC does not */
/*      retransmit packets — it retransmits the FRAMES inside new packets —   */
/*      and `ngtcp2_conn_info` has no resend counter.  `pkt_lost`             */
/*      (`persi`) is as close as one gets: the packets DECLARED lost.         */
/*    · **reordering is not counted ON STREAMS** `[S]`: no field,             */
/*      no callback, and ngtcp2 uses the 3-packet threshold internally        */
/*      without exposing it.  ⇒ There `rttvar_us` remains the only clue of    */
/*      jitter, and this line carries it without judging it.                  */
/*    · ⭐⭐⭐ **BUT ON DATAGRAMS REORDERING IS MEASURED** — 23 Aug 2026.      */
/*      `ngtcp2.h:3442`: *«the loss might be spurious, and DATAGRAM frame     */
/*      might be acknowledged later»*.  ⇒ Same `dgram_id` first in            */
/*      `lost_datagram` and then in `ack_datagram` = FALSE loss = packet      */
/*      arrived out of order.  It is `dgram_falsi`, and it is the only number */
/*      the server can give on phase 9's «out of order» target.               */
/*      ⚠ It holds for AUDIO only: streams have no identifier                 */
/*      per piece, and this road is not there.  The price is declared.        */
/*    · **`delivery_rate` does not exist** `[S]` in ngtcp2 1.25: bandwidth is */
/*      estimated from `cwnd`/`smoothed_rtt` as `chiave_intervallo_ms()` already does. */
/* ========================================================================== */

/* ⭐ THE THREE VERDICTS, and the rule that chooses them is all in `rete_ciclo()`.
 *    They are numbers and not strings only to be able to say «the verdict has changed»
 *    with counters still, which is a fact worth a line. */
#define WT_RETE_NULLA    0
#define WT_RETE_FINESTRA 1
#define WT_RETE_PERDE    2

/* ⭐⭐ THE TWO OUTCOMES OF A DATAGRAM, AND `trasporto.c` CALLS THEM FROM NGTCP2.
 *
 *    ⛔ Until 23 Aug 2026 `ngtcp2_callbacks` registered neither
 *       `lost_datagram` nor `ack_datagram`: audio left and its fate
 *       was **mute**.  «Audio does not arrive» and «audio arrives and the client
 *       throws it away» looked the same — which is the same finding B-10 that
 *       had already made incoming datagrams be counted.
 *
 * ⚠ THEY DECIDE NOTHING: they only count.  No threshold, no rate,
 *   no switch to keep off (I6), because nothing changes of
 *   what the user sees.
 */
void wt_dgram_perso(wt *w, uint64_t id)
{
	if (!w)
		return;
	w->dgram_persi++;
	/* ⛔ It is always written, even over an identifier not yet
	 *    acknowledged: the ring is a RECENT memory, not a list. */
	w->dgram_anello[w->dgram_anello_i] = id;
	w->dgram_anello_i = (w->dgram_anello_i + 1) % WT_DGRAM_ANELLO;
}

void wt_dgram_riscontrato(wt *w, uint64_t id)
{
	unsigned i;

	if (!w)
		return;
	w->dgram_riscontrati++;
	/* ⭐ The fact that counts: it had been DECLARED lost, and here it is.
	 *    ⇒ It was not lost: it was late.  It is reordering, measured. */
	for (i = 0; i < WT_DGRAM_ANELLO; i++) {
		if (w->dgram_anello[i] != id)
			continue;
		w->dgram_falsi++;
		/* ⛔ It is consumed, or a second acknowledgement of the same
		 *    identifier would count it twice. */
		w->dgram_anello[i] = 0;
		return;
	}
}

/* ========================================================================== */
/* ⛔⭐⭐ THE DEAD LINE VERDICT — the derivation of the numbers is above        */
/*      `WT_LM_STALLO_MS`, and here there is only the mechanism.              */
/*                                                                            */
/* ⛔ THE LOG LINE IS A CONTRACT — invariant I1, «every drop is               */
/*    declared», and this is not a drop: it is a CLOSED session.  A            */
/*    session that disappears without a line carrying the numbers it was       */
/*    decided on is indistinguishable from a defect OF OURS.  The format rules */
/*    are the same as `rete-quic` (the box above):                             */
/*                                                                            */
/*      1. the prefix `linea-morta` is STABLE and it is the first word of the  */
/*         body; the second field is the origin (IND:PORTA), without `=`;      */
/*      2. every field is `nome=valore` without spaces in the value;           */
/*      3. ⛔ `giudizio=` IS THE LAST and runs to the end of the line, spaces included. */
/*                                                                            */
/*    ⛔ AND THE FIELDS ARE ALWAYS ALL THERE, even those the current cause does */
/*       not use: a bench doing `split('=')` on a line of variable              */
/*       geometry would read the wrong field without noticing.  Which          */
/*       of the two causes decided is said by `causa=`, which is the FIRST field. */
/*                                                                            */
/* ⛔⛔ THE CONTRACT CHANGED ON 23 AUG 2026, and bench `09-b81` must be       */
/*      redone on it.  Two fields have DISAPPEARED and the why is not kept quiet: */
/*                                                                            */
/*      · `soglia_permille=` — there is no longer any threshold on loss.       */
/*        `permille=` instead STAYS, and it is the observation of reordering.  A */
/*        `soglia_` field next to a number that does not judge would be a      */
/*        decision nobody takes, that is shape E1.                             */
/*      · `finestre=N/M` — there are no longer bad windows to count in         */
/*        a row: the stall is a continuous duration, and its evidence is the   */
/*        duration itself, not the repetition.                                 */
/*                                                                            */
/*    ⭐ And four came in: `stallo_ms=` `soglia_stallo_ms=`                    */
/*       `offerti=` `usciti_byte=` `coda_video=` `cwnd_left=`.  The three in the middle */
/*       are the three numbers on which the stall is proved or disproved: how many */
/*       frames the stage gave us, how many video bytes really went            */
/*       out, and how many stayed in our house.                                */
/*                                                                            */
/* ⭐⭐ AND ON 25 AUG 2026 THREE MORE CAME IN, all on the same                 */
/*     question — *«was it the wire, or was it us?»*:                          */
/*                                                                            */
/*      · `fermo_ms=`      the milliseconds in which the parent's loop did NOT */
/*                         run since this session was born.  ⛔ If            */
/*                         it is not zero, the two numbers decided on were    */
/*                         frozen through our fault for that long.            */
/*        ⛔⛔ AND UNTIL 25 AUG 2026 THIS LINE WAS LYING — finding R5 of       */
/*           §5.5.  The comment said «since this session was born»            */
/*           and the code printed `giro_fermo_ms`, that is the                */
/*           **GLOBAL** counter since the server was switched on.  `[M]` a line */
/*           attributed **54.5 s** of our blindness to a session that         */
/*           at the time **had not been born yet**.  ⇒ On a server on for a   */
/*           day, an eviction after ten seconds would have said               */
/*           `fermo_ms=40000` and the reader would have **acquitted the network when */
/*           the network was involved** — the OPPOSITE error of the one the cure */
/*           exists to remove.                                                */
/*        ⭐ WE CHOSE TO CHANGE THE CODE, not the name, and the reason is     */
/*           that this field is in the line of ONE session and answers        */
/*           «was it the wire, or was it us, **while it was alive**?».  A     */
/*           `fermo_globale_ms=` would have told the truth without answering  */
/*           the question — and the global number is not lost: it is carried by */
/*           `giri_fermi=` below, and by the once-a-minute line of `main.c`.  */
/*      · `giri_fermi=`    how many gaps, in total.  ⚠ It is GLOBAL, on purpose — */
/*                         the loop is a single one and its health is a fact  */
/*                         of the MACHINE.  ⇒ The two are read as a pair:     */
/*                         `fermo_ms=` says how much fell to it,              */
/*                         `giri_fermi=` how much the server saw.             */
/*      · `saltati=`       how many verdicts this session SKIPPED because     */
/*                         there had been a gap.  ⭐ It is the count that makes the */
/*                         cure falsifiable: `saltati=0` in an evicted        */
/*                         session means the gap had nothing to do with it.   */
/*                                                                            */
/*   ⛔ They are WITNESSES, not judges — the same promotion `permille=`       */
/*      got on 23 August: the decision stays with the two causes.             */
/*                                                                            */
/* ⭐⭐ AND FOUR MORE, FOR THE §6.15 LOOP — `ritmo_giu=`                        */
/*     `ritmo_arretrato=` `ritmo_posti=` `ritmo_scesi=`.                      */
/*                                                                            */
/*   ⛔ §6.15 had to put side by side TWO lines written from two different     */
/*      points of the program, and pair them by eye on the time, to say *«the regulator */
/*      was holding everything back when the dead line evicted»*.  ⇒ With      */
/*      these fields the eviction line says it BY ITSELF: `ritmo_giu=1` with   */
/*      `usciti_byte=0` means that **we were the ones** letting nothing out.   */
/*   ⚠ And here too they are witnesses: the decision does not change one bit.  */
/*     ⭐ But the next time the loop reproduces, the reader no longer has to   */
/*        deduce it — and that is what is needed to cure it at the root.       */
/* ========================================================================== */

static void linea_morta_scatta(wt *w, const ngtcp2_conn_info *in,
                               const char *causa, uint64_t stallo_ms,
                               uint64_t offerti, uint64_t usciti,
                               uint64_t coda_video, uint64_t silenzio_ms,
                               uint64_t prove, const char *detto)
{
	static const uint8_t motivo[] = "linea morta";

	w->lm_scattata = true;
	registro_dice_di(REG_WT, wt_chi(w),
	                 "linea-morta %s causa=%s stallo_ms=%llu soglia_stallo_ms=%llu "
	                 "offerti=%llu usciti_byte=%llu coda_video=%llu "
	                 "silenzio_ms=%llu soglia_silenzio_ms=%llu prove=%llu "
	                 "minimo_prove=%u persi=%llu spediti=%llu permille=%u "
	                 "finestra_ms=%llu minimo_pacchetti=%u cwnd=%llu "
	                 "cwnd_left=%llu srtt_us=%llu fermo_ms=%llu giri_fermi=%llu "
	                 "saltati=%llu ritmo_giu=%d ritmo_arretrato=%u ritmo_posti=%u "
	                 "ritmo_scesi=%llu giudizio=%s",
	                 w->provenienza, causa,
	                 (unsigned long long)stallo_ms,
	                 (unsigned long long)linea_morta_stallo_ms,
	                 (unsigned long long)offerti, (unsigned long long)usciti,
	                 (unsigned long long)coda_video,
	                 (unsigned long long)silenzio_ms,
	                 (unsigned long long)linea_morta_silenzio_ms,
	                 (unsigned long long)prove, (unsigned)WT_LM_MIN_PROVE,
	                 (unsigned long long)w->lm_persi_v,
	                 (unsigned long long)w->lm_spediti_v, w->lm_permille,
	                 (unsigned long long)w->lm_durata_v,
	                 (unsigned)WT_LM_MIN_PACCHETTI,
	                 (unsigned long long)in->cwnd,
	                 (unsigned long long)ngtcp2_conn_get_cwnd_left(w->conn),
	                 (unsigned long long)(in->smoothed_rtt / NGTCP2_MICROSECONDS),
	                 /* ⛔ R5, 25 Aug 2026: the DIFFERENCE, not the global
	                  *    counter — see `lm_fermo_nato` and the field `fermo_ms=`
	                  *    in the box above. */
	                 (unsigned long long)(giro_fermo_ms - w->lm_fermo_nato),
	                 (unsigned long long)giro_fermi,
	                 (unsigned long long)w->lm_fermo_saltati,
	                 w->ritmo_giu ? 1 : 0, w->ritmo_ultimo,
	                 (unsigned)WT_RITMO_POSTI,
	                 (unsigned long long)w->video_ritmo_scesi,
	                 detto);
	/* ⛔⭐ THE REASON IS WRITTEN IN THE CONNECTION ERROR, and a new RCP reason
	 *     is not INVENTED: `RCP.md` §9 forbids adding a code to
	 *     §8.2 within a major version, and none of the sixteen says «the
	 *     line is dead».  ⇒ Code `H3_NO_ERROR` (0x0100) — at the HTTP/3 level
	 *     there is no error, it is the WIRE that no longer carries — and the
	 *     reason travels in the string, which is the place QUIC gives it.
	 *
	 * ⚠ And it is not the road of §3.1 point 3 (the closing capsule of the
	 *   WebTransport session) on purpose: that one wants the queue to empty and
	 *   waits up to 3 s on a line that by hypothesis DOES NOT CARRY.  Here the wire
	 *   drops — it is what the user chose to show. */
	if (w->ultimo_errore)
		ngtcp2_ccerr_set_application_error(w->ultimo_errore,
		                                   NGHTTP3_H3_NO_ERROR, motivo,
		                                   sizeof motivo - 1);
}

static void linea_morta_giudica(wt *w, const ngtcp2_conn_info *in,
                                uint64_t ora_ms)
{
	uint64_t spediti, persi, prove, fermo_da, stallo;
	uint64_t coda_video, offerti, usciti;
	bool avevo_da_mandare;

	/* ⛔ Off = yesterday's product byte for byte (I6).  And once fired
	 *    it no longer judges: the connection is already dropping, and a second
	 *    line would say the same thing twice. */
	if (!linea_morta_accesa || w->lm_scattata)
		return;
	/* ⛔ Only with a live RCP session: before there is nothing to throw
	 *    out, and at closure someone else has already chosen the reason. */
	if (!w->rcp || w->chiusura >= 0)
		return;
	/* ⛔⭐ AND «ALIVE» IS NOT `w->rcp != NULL`: A FINISHED SESSION IS STILL THERE.
	 *
	 *    `w->rcp` is reset only in `wt_stream_chiuso()`, that is when the
	 *    CLIENT closes the CONNECT stream or the control channel.  If
	 *    the client says farewell and then **disappears** — the tab closes and the
	 *    browser process exits, which is the normal case — that stream never
	 *    closes: `rcp_chiusa_dal_client()` takes the session to
	 *    `"finita"` and frees the slot, but the pointer stays.  ⇒ Here we
	 *    kept judging a connection that WE ourselves had just
	 *    declared concluded, and ten seconds later a ⛔ `LINEA MORTA` came out
	 *    on a client that had said goodbye properly.
	 *
	 * ⛔ It is exactly the state on which `regola_tienila_viva()` switches off the PINGs
	 *    writing «the session is over, there is nothing left to keep
	 *    alive»: two opposite verdicts on the same fact, ten seconds
	 *    apart, in the same log.  ⇒ This line realigns them, and it is not
	 *    a new policy: it is the comment above becoming true.
	 *
	 * `[M]` 22 Sep 2026, 10:30:11.698-10:30:22.330 UTC (`registri-22set/
	 *       kde-1045.log`): farewell `motivo=0x01` «the tab was closed»
	 *       → PINGs off at 10:30:11.798 → closing capsule at 10:30:12.199
	 *       → ⛔ `LINEA MORTA causa=silenzio` at 10:30:22.330, with
	 *       `offerti=0 usciti_byte=0 coda_video=0 persi=0`.  The tablet's
	 *       journal dates the exit of the Chrome process at 12:30:11 local time,
	 *       that is BEFORE the silence.
	 *
	 * ⚠ AND IT TAKES NOTHING AWAY FROM THE CURE, because whoever dies does not say goodbye: a client
	 *   killed (`kill -9`, the browser closed by force, the network dropping) leaves
	 *   the session `"attiva"` and the dead line fires as before — it is
	 *   TEST 3 of `banchi/09-b81-linea-morta.py`, and they are two of the three episodes
	 *   of 22 September (12:41 and 12:42), which remain RIGHT firings.
	 *
	 * ⛔ And the connection is NOT closed here: «session finished, connection
	 *    still alive» is a state FORESEEN twice in this file —
	 *    `fin_dal_client()` («the page that closes the writing side of the
	 *    channel and keeps the connection alive») and `chiusa_dal_client()` («the
	 *    slot is given up now ... waiting for the transport teardown means
	 *    keeping it occupied against whoever reconnects at once»).  In both
	 *    the choice was to free the SLOT and leave the transport standing,
	 *    and `wt_stream_chiuso()` puts `w->sessione` back to -1 on purpose so that a
	 *    new session can open on top of it.  ⇒ Closing the connection
	 *    would undo that decision; and the PINGs are already off, so the
	 *    transport goes away by itself with the 30 s `max_idle_timeout`. */
	if (rcp_e_finita(w->rcp))
		return;

	/* ⛔ The first round TAKES A SNAPSHOT and does not judge: without this line the first
	 *    window would be as long as the whole connection, and the stall
	 *    would start from an instant that was never looked at. */
	if (!w->lm_finestra_ms) {
		w->lm_finestra_ms = ora_ms;
		w->lm_pkt_sent = in->pkt_sent;
		w->lm_pkt_lost = in->pkt_lost;
		w->lm_vivo_ms = ora_ms;
		w->lm_pkt_recv = in->pkt_recv;
		w->lm_pkt_sent_vivo = in->pkt_sent;
		w->lm_uscita_ms = ora_ms;
		w->lm_usciti_visti = w->lm_usciti;
		w->lm_offerti_visti = w->lm_offerti;
		w->lm_fermo_visto = giro_fermo_ms;
		/* ⛔ R5: the zero point of `fermo_ms=`, and it is noted HERE because here is
		 *    the first instant in which this session was looked at — before
		 *    this round there was nothing to attribute to it. */
		w->lm_fermo_nato = giro_fermo_ms;
		return;
	}

	/* ── 0. ⛔⛔⭐ THE GAP IN THE LOOP — «our silence is not theirs» ──
	 *
	 * The box above `WT_GIRO_ATTESO_MS` carries the fact and the three measurements that
	 * lead to it.  Here there is the rule, and it is two lines: if since the last verdict
	 * the parent's loop fell behind, **the bytes could not go out and the
	 * client's packets could not be read** — so there is nothing
	 * to judge, and the counts restart from now as if a
	 * progress had arrived.  Because there has been a progress: the loop has started running again.
	 *
	 * ⛔ And `lm_scattata` is NOT touched, nothing is switched off and no
	 *    threshold is widened: the cure holds **only** for the time in which we did not
	 *    look.  At the next round, if the client is really quiet, the ten seconds
	 *    start again and the dead line does its job.
	 * ⚠ THE PRICE, declared: a client dead during a gap is recognised
	 *   up to one threshold later.  ⭐ It is the right side of the usual
	 *   asymmetry (above `WT_LM_STALLO_MS`): erring high costs seconds of
	 *   frozen screen, erring low throws out someone who is working. */
	if (giro_fermo_ms != w->lm_fermo_visto) {
		uint64_t buco = giro_fermo_ms - w->lm_fermo_visto;

		w->lm_fermo_visto = giro_fermo_ms;
		w->lm_fermo_saltati++;
		w->lm_vivo_ms = ora_ms;
		w->lm_pkt_recv = in->pkt_recv;
		w->lm_pkt_sent_vivo = in->pkt_sent;
		w->lm_uscita_ms = ora_ms;
		w->lm_usciti_visti = w->lm_usciti;
		w->lm_offerti_visti = w->lm_offerti;
		/* ⛔ ONE LINE, and it is not noise: it is the only trace of a defect that
		 *    otherwise leaves none — the SILENT degradation of
		 *    `CODER.md` §1-bis.  ⭐ And it carries the gap next to the threshold, so
		 *    the reader sees at once whether the loop fell behind by a hair or
		 *    by ten seconds. */
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⚠ %s: the parent's loop fell behind by %llu ms "
		                 "(%llu gaps in total, the worst %llu ms): the dead line "
		                 "does NOT judge this round and its counts restart.  ⛔ In "
		                 "that time no byte could go out and no client packet "
		                 "could be READ: counting it as its silence "
		                 "would mean blaming its network for a blindness of ours "
		                 "(skipped %llu times by this session)",
		                 w->provenienza, (unsigned long long)buco,
		                 (unsigned long long)giro_fermi,
		                 (unsigned long long)giro_fermo_peggiore_ms,
		                 (unsigned long long)w->lm_fermo_saltati);
		return;
	}

	/* ── 1. THE WITNESS: THE LOSS FRACTION ────────────────────────────────
	 * ⛔⛔ AND IT NO LONGER JUDGES ANYTHING — 23 Aug 2026, the refutation is written in
	 *      full in the box above `WT_LM_STALLO_MS`.  The number is still COMPUTED,
	 *      with the same guards as before, and ends up in the firing
	 *      line as `permille=`: on a line that reorders it is the best
	 *      measure of REORDERING the server has on streams, where
	 *      `dgram_falsi` (§17.3) does not reach.
	 *
	 * ⚠ The guards stay because a witness that lies is worse than a
	 *   witness that keeps quiet: below `WT_LM_MIN_PACCHETTI` sent the window
	 *   does NOT close, it lengthens — a fraction over twenty packets is not a
	 *   fraction, it is noise.  ⭐ And the minimum is on the packets WE send,
	 *   which is the abundant direction of this session (video downwards, almost
	 *   nothing upwards). */
	if (ora_ms - w->lm_finestra_ms >= WT_LM_FINESTRA_MS) {
		spediti = in->pkt_sent - w->lm_pkt_sent;
		if (spediti >= WT_LM_MIN_PACCHETTI) {
			persi = in->pkt_lost - w->lm_pkt_lost;
			/* ⛔ The REAL duration of the window, taken before closing it: it is the
			 *    number that says whether the packet minimum lengthened it, and
			 *    with the constant in its place that line would always say 1000 —
			 *    that is a number that LOOKS measured (shape E1). */
			w->lm_durata_v = ora_ms - w->lm_finestra_ms;
			w->lm_persi_v = persi;
			w->lm_spediti_v = spediti;
			w->lm_permille = (unsigned)(persi * 1000 / spediti);
			/* The window closes here, and the next one starts from now. */
			w->lm_finestra_ms = ora_ms;
			w->lm_pkt_sent = in->pkt_sent;
			w->lm_pkt_lost = in->pkt_lost;
		}
	}

	/* ── 2. THE TWO HALVES OF THE STALL, READ ONCE ONLY ──────────────────
	 * ⛔ They are read BEFORE any firing and before their own reset,
	 *    because the SILENCE line carries them too: a session closed for
	 *    silence with `offerti=` and `usciti_byte=` taken after the reset
	 *    would always say zero, that is a number that looks measured and is not.
	 *
	 * ⭐ `offerti` and `usciti_byte` are DIFFERENCES since the stall count
	 *    last restarted, not session totals: the
	 *    quantity is «how long», and the totals would answer another
	 *    question. */
	coda_video = coda_byte_video(w);
	offerti = w->lm_offerti - w->lm_offerti_visti;
	usciti = w->lm_usciti - w->lm_usciti_visti;
	/* ⛔⭐ «I HAD SOMETHING TO SEND» — and it is the half that holds the other one up.
	 *     Two terms, and each covers a hole of the other:
	 *       · `coda_video > 0` — frame bytes are still in our
	 *         house, so the wire is holding them back;
	 *       · `offerti > 0` — the stage gave us a frame since the
	 *         count restarted.  ⛔ Without this, the RATE REGULATOR
	 *         would hide the stall: it stops producing, `video_sgombra()`
	 *         abandons old deltas, the queue empties, and «I have nothing to
	 *         send» would become true while the screen is frozen. */
	avevo_da_mandare = coda_video > 0 || offerti > 0;
	stallo = ora_ms - w->lm_uscita_ms;

	/* ── 3. SILENCE ──────────────────────────────────────────────────────
	 * ⛔ The quantity is NOT «how much time has passed»: it is «how many of our
	 *    packets went out without ONE coming back».  Time is only the
	 *    window in which one looks, and alone it would not be enough — a still desktop
	 *    in which neither of the two speaks is legitimately quiet.
	 * ⚠ And this cure is NOT to be touched: `[M]` 23 Aug 2026 it passed its
	 *   test — `kill -9` on the client, firing at `silenzio_ms=10002` with
	 *   `prove=10`, 10.36 s after the blow; with the cure off, zero firings. */
	if (in->pkt_recv > w->lm_pkt_recv) {
		w->lm_vivo_ms = ora_ms;
		w->lm_pkt_recv = in->pkt_recv;
		w->lm_pkt_sent_vivo = in->pkt_sent;
	} else if (linea_morta_silenzio_ms) {
		fermo_da = ora_ms - w->lm_vivo_ms;
		prove = in->pkt_sent - w->lm_pkt_sent_vivo;
		if (fermo_da >= linea_morta_silenzio_ms && prove >= WT_LM_MIN_PROVE) {
			linea_morta_scatta(
				w, in, "silenzio", stallo, offerti, usciti, coda_video,
				fermo_da, prove,
				"⛔ the line is DEAD: the client has not shown a packet for "
				"too long and the questions we asked it meanwhile "
				"have all remained unanswered.  The wire drops, and to "
				"come back one has to reconnect by hand (the user's decision, 23 "
				"Aug 2026)");
			return;
		}
	}

	/* ── 4. THE OUTPUT STALL ─────────────────────────────────────────────
	 * ⛔ The count RESTARTS for two different reasons that must be treated the same:
	 *      1. something went out (`usciti > 0`) — the wire carries;
	 *      2. there was nothing to send — and then nothing is broken.
	 *    ⭐ The second is the case of the STILL SCENE, which in this phase is
	 *       normal and costs nothing (`RecordVirtual` delivers only on
	 *       change, the wake-up is worth 13 ms).  A count that started
	 *       anyway would throw out whoever is reading a page.
	 * ⚠ And the instant is the ROUND's, not the one in which the bytes went out:
	 *   the measured `stallo_ms` can be up to ~1 s shorter than the truth.
	 *   It fires later, never earlier — which is the right side. */
	if (usciti > 0 || !avevo_da_mandare) {
		w->lm_uscita_ms = ora_ms;
		w->lm_usciti_visti = w->lm_usciti;
		w->lm_offerti_visti = w->lm_offerti;
		return;
	}
	if (!linea_morta_stallo_ms || stallo < linea_morta_stallo_ms)
		return;
	linea_morta_scatta(
		w, in, "stallo", stallo, offerti, usciti, coda_video,
		ora_ms - w->lm_vivo_ms, in->pkt_sent - w->lm_pkt_sent_vivo,
		"⛔ the line is DEAD: for too long no frame has gone out while "
		"having some to send — the user's image is FROZEN, and at this "
		"point the product either freezes it or shows it seconds late "
		"(`[M]` 23 Aug 2026: up to 30.06 s of gap on `raffica-forte`).  "
		"Neither of the two is to be served: the wire drops, and to come back one has to "
		"reconnect by hand (the user's decision)");
}

bool wt_linea_morta_scattata(const wt *w)
{
	return w && w->lm_scattata;
}

static void rete_ciclo(wt *w, uint64_t ora_ms)
{
	ngtcp2_conn_info in;
	uint64_t cwnd_left, da_ms;
	char minimo[24], coda[24];
	const char *detto;
	int g;

	if (!w->conn || w->chiusura >= 0)
		return;
	/* ⚠ At most one a second.  ⛔ And the FIRST always comes out, without waiting:
	 *   `rete_detto_ms == 0` means «never spoken», which is not «nothing has
	 *   changed» (`LEZIONI.md` §1.9). */
	if (w->rete_detto_ms && ora_ms - w->rete_detto_ms < 1000)
		return;

	memset(&in, 0, sizeof in);
	ngtcp2_conn_get_conn_info(w->conn, &in);
	cwnd_left = ngtcp2_conn_get_cwnd_left(w->conn);

	/* ⛔⭐ AND HERE THE VERDICT IS TAKEN, BEFORE the «only if something changed» filter:
	 *     client silence IS the case in which nothing changes, and placed
	 *     after that filter this verdict would NEVER be walked precisely
	 *     when it is needed.  ⚠ The rhythm is that of `rete_ciclo()`, once a
	 *     second, and it is also the minimum window. */
	linea_morta_giudica(w, &in, ora_ms);

	/* ⛔⭐ THE VERDICT RULE, and it is read from the top: the first that fires
	 *     wins, and the order is NOT arbitrary.
	 *
	 *  1. `persi_d > 0` — ngtcp2 has DECLARED packets lost in this
	 *     interval ⇒ «⛔ the line is losing».  It comes before everything because the
	 *     closed window is almost always the CONSEQUENCE of loss: with
	 *     the order inverted the cause would hide behind its effect.
	 *  2. `cwnd_left == 0` with a window that exists (`cwnd > 0`) — there is no
	 *     room to send ⇒ «⚠ the window is closed».  Without losses
	 *     in the interval it is the echo of a past loss, or it is slow
	 *     start that has not opened yet: the line carries `ssthresh` next to it and
	 *     the reader tells the two apart (below threshold = slow start).
	 *  3. otherwise «-- nothing to report».
	 *
	 * ⚠ AND THE VERDICT DOES NOT SPEAK OF JITTER OR REORDERING, on purpose: those two
	 *   numbers ngtcp2 does not give (see the box above), and a verdict
	 *   deduced from `rttvar` would have wanted a THRESHOLD — that is a decision, and
	 *   here none is taken. */
	if (in.pkt_lost > w->rete_pkt_lost)
		g = WT_RETE_PERDE;
	else if (in.cwnd > 0 && cwnd_left == 0)
		g = WT_RETE_FINESTRA;
	else
		g = WT_RETE_NULLA;

	/* ⛔⭐ ONLY WHEN SOMETHING HAS CHANGED.  A line a second repeating
	 *     the same numbers is noise that HIDES the lines that count — and it is
	 *     the lesson of the 30.8 GB of log, in a new guise: there it was one
	 *     line per frame, here it would be one line per still session.
	 *
	 * ⚠ The check is on the COUNTERS (sent, received, lost, discarded) and
	 *   on the VERDICT, not on `cwnd`/`rtt`: those always oscillate by a byte or
	 *   a microsecond, and comparing them the line would never keep quiet —
	 *   that is the filter would be written and would not work.  If the four
	 *   counters are STILL, nothing went over the wire: and then
	 *   `cwnd` and `rtt` are the previous ones too, by construction. */
	/* ⛔ And datagrams enter the comparison: a session losing ONLY
	 *    audio — packets with DATAGRAMS inside are packets like the
	 *    others, but a reordering may not move `pkt_lost` — would stay mute
	 *    precisely in the case phase 9 is looking for. */
	if (w->rete_detto_ms
	    && in.pkt_lost == w->rete_pkt_lost
	    && in.pkt_sent == w->rete_pkt_sent
	    && in.pkt_recv == w->rete_pkt_recv
	    && in.pkt_discarded == w->rete_pkt_discarded
	    && w->dgram_persi == w->rete_dgram_persi
	    && w->dgram_falsi == w->rete_dgram_falsi
	    && g == w->rete_giudizio)
		return;

	/* ⛔ `min_rtt` is `UINT64_MAX` until a sample has arrived, and the
	 *    subtraction would give a huge number that LOOKS measured — shape E1,
	 *    the worst.  ⇒ `n/d` is declared instead of printing garbage.  It is
	 *    the same guard as `ritmo_frena()`, and it holds for both fields
	 *    that depend on `min_rtt`. */
	if (in.min_rtt != UINT64_MAX && in.min_rtt != 0) {
		snprintf(minimo, sizeof minimo, "%llu",
		         (unsigned long long)(in.min_rtt / NGTCP2_MICROSECONDS));
		/* ⭐ `smoothed_rtt - min_rtt` IS THE QUEUE INSIDE THE NETWORK: it is the number
		 *    with which `SPECIFICHE.md:128` — «every intermediate memory buys
		 *    smoothness and sells responsiveness» — is honoured instead of quoted. */
		if (in.smoothed_rtt >= in.min_rtt)
			snprintf(coda, sizeof coda, "%llu",
			         (unsigned long long)((in.smoothed_rtt - in.min_rtt)
			                              / NGTCP2_MICROSECONDS));
		else
			snprintf(coda, sizeof coda, "0");
	} else {
		snprintf(minimo, sizeof minimo, "n/d");
		snprintf(coda, sizeof coda, "n/d");
	}

	switch (g) {
	case WT_RETE_PERDE:
		detto = "⛔ the line is losing";
		break;
	case WT_RETE_FINESTRA:
		detto = "⚠ the window is closed";
		break;
	default:
		detto = "-- nothing to report";
		break;
	}

	da_ms = w->rete_detto_ms ? ora_ms - w->rete_detto_ms : 0;

	registro_dice_di(REG_WT, wt_chi(w),
	                 "rete-quic %s da_ms=%llu persi=%llu persi_d=%llu "
	                 "byte_persi=%llu byte_persi_d=%llu spediti=%llu spediti_d=%llu "
	                 "byte_spediti=%llu ricevuti=%llu ricevuti_d=%llu "
	                 "scartati=%llu scartati_d=%llu cwnd=%llu cwnd_left=%llu "
	                 "ssthresh=%llu involo=%llu srtt_us=%llu latest_us=%llu "
	                 "rttvar_us=%llu min_rtt_us=%s coda_rete_us=%s pto_us=%llu "
	                 "dgram_persi=%llu dgram_persi_d=%llu dgram_ok=%llu "
	                 "dgram_falsi=%llu dgram_falsi_d=%llu giudizio=%s",
	                 w->provenienza,
	                 (unsigned long long)da_ms,
	                 (unsigned long long)in.pkt_lost,
	                 (unsigned long long)(in.pkt_lost - w->rete_pkt_lost),
	                 (unsigned long long)in.bytes_lost,
	                 (unsigned long long)(in.bytes_lost - w->rete_bytes_lost),
	                 (unsigned long long)in.pkt_sent,
	                 (unsigned long long)(in.pkt_sent - w->rete_pkt_sent),
	                 (unsigned long long)in.bytes_sent,
	                 (unsigned long long)in.pkt_recv,
	                 (unsigned long long)(in.pkt_recv - w->rete_pkt_recv),
	                 (unsigned long long)in.pkt_discarded,
	                 (unsigned long long)(in.pkt_discarded - w->rete_pkt_discarded),
	                 (unsigned long long)in.cwnd,
	                 (unsigned long long)cwnd_left,
	                 (unsigned long long)in.ssthresh,
	                 (unsigned long long)in.bytes_in_flight,
	                 (unsigned long long)(in.smoothed_rtt / NGTCP2_MICROSECONDS),
	                 (unsigned long long)(in.latest_rtt / NGTCP2_MICROSECONDS),
	                 (unsigned long long)(in.rttvar / NGTCP2_MICROSECONDS),
	                 minimo, coda,
	                 (unsigned long long)(ngtcp2_conn_get_pto(w->conn)
	                                      / NGTCP2_MICROSECONDS),
	                 (unsigned long long)w->dgram_persi,
	                 (unsigned long long)(w->dgram_persi - w->rete_dgram_persi),
	                 (unsigned long long)w->dgram_riscontrati,
	                 (unsigned long long)w->dgram_falsi,
	                 (unsigned long long)(w->dgram_falsi - w->rete_dgram_falsi),
	                 detto);

	w->rete_detto_ms      = ora_ms;
	w->rete_pkt_lost      = in.pkt_lost;
	w->rete_bytes_lost    = in.bytes_lost;
	w->rete_pkt_sent      = in.pkt_sent;
	w->rete_pkt_recv      = in.pkt_recv;
	w->rete_pkt_discarded = in.pkt_discarded;
	w->rete_dgram_persi   = w->dgram_persi;
	w->rete_dgram_falsi   = w->dgram_falsi;
	w->rete_giudizio      = g;
}

/* ------------------------------------------------------------------------ */
/* ⭐ THE FRAME ARRIVING FROM THE STAGE, DELIVERED TO ONE SESSION.          */

static void video_a_una(wt *w, const char *utente, uint8_t codec, bool chiave,
                        const uint8_t *dati, size_t byte, uint32_t l, uint32_t a,
                        uint64_t istante_us, uint32_t input)
{
	uint32_t tl = 0, ta = 0;
	uint64_t ora_ms;
	const char *mio;
	int e;

	/* ⚠ `video_fermo` = I have already told the stage to stop, and what arrives
	 *   now is the TAIL of what was already in flight when I told it.
	 *   ⛔ Without this condition those two or three frames would walk
	 *   the whole way to get refused by `rcp_video_apri()` with
	 *   `RCP_VIDEO_PRIMA_DI_SESSIONE`, that is with the same ⛔ line the cure
	 *   of 23 Sep exists to remove — only three times instead of a thousand. */
	if (!w->video_acceso || w->video_fermo || w->video_codec != codec)
		return;
	if (!w->rcp || !w->conn || w->chiusura >= 0)
		return;

	/* ⛔⭐ INVARIANT I3 ON THE WIRE, AND IT IS NOT ONE MORE PRECAUTION.
	 *
	 *     `[M]` 12 Aug 2026: with a per-process deposit, «prova» (uid 1001,
	 *     without a graphical session) received **a conforming frame**, and that
	 *     frame was «nicfio»'s desktop.  Not «you receive nothing»:
	 *     **you receive somebody else's desktop**, and neither of the two notices.
	 *     ⇒ Here the comparison is between the user who CAPTURED and the user
	 *     PAM admitted on this session, and they are two different facts both
	 *     asked of whoever knows them. */
	mio = rcp_utente(w->rcp);
	if (!mio || !utente || strcmp(mio, utente) != 0)
		return;

	if (!rcp_tela_in_vigore(w->rcp, &tl, &ta))
		return;

	/* ⛔⭐ AND THE CANVAS MUST BE THAT ONE, not «more or less that one» — §6.2, P5.
	 *
	 *     The 28 bytes carry `largh.`/`altezza` = the canvas IN FORCE, and they are written by
	 *     `rcp.c` from its own.  If the captured frame carried another,
	 *     the header would say one size and the pixels would carry another:
	 *     two truths about the same thing, and the client would have no way to
	 *     notice — the decoder takes the size from the stream.
	 *     ⛔ Better no frame than a frame that lies. */
	if (tl != l || ta != a) {
		w->video_saltati++;
		/* ⚠ A backstop OF ITS OWN, and no longer `video_detto`: that field is the backstop of the
		 *   message «no codec negotiated», and one flag for two different facts
		 *   switches one off when the other speaks.  ⛔ And here the backstop REARMS at
		 *   every canvas change, because the fact has changed. */
		if (w->tela_detta_l != l || w->tela_detta_a != a) {
			w->tela_detta_l = l;
			w->tela_detta_a = a;
			/* ⭐ The ANNOUNCEMENT is counted, not the frame: the frame has
			 *    already been counted by `video_saltati` three lines above.  Two numbers for
			 *    two facts, and the closing line writes both. */
			w->video_annunci_tela++;
			registro_dice_di(REG_RCP, wt_chi(w),
			                 "⛔ %s: canvas in force %ux%u but the captured frame "
			                 "is %ux%u — NOT sending it (§6.2): the header "
			                 "would say one size and the pixels would carry another.  "
			                 "⚠ The canvas in force is being requested from the stage",
			                 w->provenienza, tl, ta, l, a);
		}
		/* ⛔⛔⭐ AND THIS ALSO PAYS FOR THE KEYFRAME — 23 Sep 2026, and it is the
		 *      SAME defect as the rate regulator, found next to it.
		 *
		 *      The frame thrown away here has **already been encoded** by the child
		 *      and the encoder's references have moved on; the `numero`
		 *      however was not consumed — `rcp_video_apri()` is not reached
		 *      from here — so the client gets a CONTINUOUS numbering and
		 *      §5.2 gives it no foothold to ask for the cure.
		 *
		 * ⚠ AND IT WAS NOT ENOUGH FOR THE CANVAS TO MATCH AGAIN: the frames
		 *   thrown away meanwhile are missing forever, and with the infinite GOP the
		 *   next keyframe never arrives by itself.  ⇒ Without this line, a
		 *   window resize under load left the image in
		 *   tiles for the whole rest of the session.
		 *
		 * ⭐ It sits INSIDE the announcement backstop on purpose: `serve_chiave` is a
		 *    latch that switches off only once the keyframe HAS GONE OUT, and until the canvas
		 *    matches no frame goes out — so not even the keyframe, and
		 *    so the debt stays on by itself.  ⛔ Calling it outside the backstop
		 *    would mean walking it at 60/s for nothing. */
		rcp_video_scartato_prima_del_filo(
		    w->rcp, chiave,
		    "the captured frame does not carry the canvas in force (§6.2) — but "
		    "it was already ENCODED, and the encoder's references moved "
		    "on without it");
		/* ⛔ The keyframe is requested NOW, for the same reason as the twin in
		 *    `ritmo_frena()`: with the debt on every delta is refused, and
		 *    waiting for the heartbeat means keeping the screen frozen.
		 * ⚠ And `ora_ms` has not been read here yet — it is read now
		 *   instead of moving the line further up: that one sits AFTER the three
		 *   «is this frame mine?» checks on purpose (see the box of
		 *   `lm_offerti`), and moving it would change something else. */
		video_regola(w, ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);
		return;
	}
	/* ⭐ Canvas and frame agree: the backstop of the message above is
	 *    disarmed, so the next mismatch will be seen instead of being
	 *    mistaken for the tail of the previous one. */
	w->tela_detta_l = w->tela_detta_a = 0;

	ora_ms = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;

	/* ⛔⭐⭐ PHASE 9 — «I HAD SOMETHING TO SEND», AND IT IS COUNTED HERE, BEFORE EVERYTHING.
	 *
	 *      From this line on the frame can be braked by the
	 *      rate regulator, cleared out by §5.1, refused for lack of
	 *      credit (§2.3) or not enter the list of frames in flight: in
	 *      ALL those cases the stage had given it to us all the same, and for the dead
	 *      line that is the fact.
	 *
	 * ⛔ Counting it further on — after the brake, for example — would mean that
	 *    the rate regulator HIDES the stall: it stops producing, the
	 *    queue empties through abandonments, and «I have nothing to send» would become
	 *    true precisely while the user's screen is frozen.
	 *
	 * ⚠ And it sits AFTER the three checks above — codec, user (I3), canvas — which
	 *   are not steps of sending: they are the answer to the question «is this
	 *   frame MINE?».  A frame of another user is not stuff we
	 *   had to send. */
	w->lm_offerti++;

	/* ⛔⭐⭐ PHASE 9 — THE RATE REGULATOR, and it sits HERE for two reasons that
	 *      must both be written down:
	 *
	 *      1. BEFORE `video_sgombra()`, which three lines below empties that
	 *         queue.  Afterwards, `arretrato` would be zero by construction and this
	 *         loop would never fire — and a mute regulator and a healthy line
	 *         look the same;
	 *      2. and the braked frame does NOT even do the clear-out.  ⭐ It is intended:
	 *         clearing out would mean abandoning a delta, and every abandonment
	 *         switches on the debt of §5.2 inside `rcp.c`, that is it fabricates a
	 *         KEYFRAME — which is precisely the spiral this phase cures.  The
	 *         regulator stops PRODUCING; it does not throw away what is already there.
	 *
	 * ⚠ And `involo[]` does not get dirty: the elements whose bytes have gone away
	 *   stay marked alive until a pass of `video_sgombra()` removes
	 *   them, but `ritmo_frena()` counts them by rereading the BYTES — so
	 *   `arretrato` goes down all the same, and the braking ends by itself. */
	if (ritmo_frena(w, chiave, ora_ms))
		return;

	/* ⛔ §5.1 — «a more recent one has already left»: the deltas still stuck
	 * in the queue are reset BEFORE enqueuing this one, or the queue would grow
	 * with the past instead of carrying the present. */
	video_sgombra(w, "a more recent one has left (§5.1)");

	/* ⛔ §2.3 — and the credit is checked BEFORE asking for the stream, to be able to
	 * tell «there was no room» from «the stream broke».  ⚠ The reserve
	 * is for input: §2.3 exists because without credit «input would not leave
	 * at all and the symptom would be the desktop does not respond». */
	if (!chiave
	    && ngtcp2_conn_get_streams_uni_left2(w->conn) <= WT_UNI_RISERVA) {
		w->video_saltati++;
		/* ⛔⭐ PHASE 9 — and this is counted APART from the §5.1 abandonments.
		 *     It is CAUSE 4 of the §5.2 debt (`rcp.c:3441`), shape **C**
		 *     of abandonment: no stream, no hole, no signal — the
		 *     receiver does not see it at all.  ⚠ The threshold cure touches
		 *     cause 3, not this one: if under congestion this were what kept the
		 *     debt on, the cure would spin idle and the numbers would not
		 *     move.  ⇒ Two counters, or the bench cannot attribute. */
		w->sgombra_credito++;
		rcp_video_niente_credito(w->rcp, false,
		                         ngtcp2_conn_get_streams_uni_left2(w->conn));
		return;
	}

	w->video_stream_ultimo = -1;
	e = rcp_video_spedisci(w->rcp, chiave, dati, byte, istante_us, input, ora_ms);
	if (e == RCP_VIDEO_SPEDITO) {
		w->video_diffusi++;
		/* ⭐ The size of the last KEYFRAME, and it serves `chiave_intervallo_ms()`:
		 *    it is the number from which how long it takes to go out is computed.  ⛔ It is
		 *    taken HERE, where it is a fact, instead of estimating it from an average —
		 *    `[M]` on bench 07-b65 a keyframe at 1080p measures ~60 000 bytes, but
		 *    it depends on the scene and a constant would lie about half of them. */
		if (chiave) {
			w->chiave_byte = (uint64_t)byte;
			/* ⭐ The debt episode is closed: next time the ⛔ line
			 *    of the second belt can be written again. */
			w->debito_detto = false;
		}
		involo_aggiungi(w, w->video_stream_ultimo,
		                rcp_video_ultimo_numero(w->rcp), chiave);
		return;
	}

	w->video_saltati++;
	/* ⛔⭐⭐ AND IF THE REFUSAL IS «a KEYFRAME is needed», THIS IS THE ROAD THAT DOES NOT
	 *       GO THROUGH THE HEARTBEAT.  `[M]` 23 Sep 2026: 370 s of frozen screen and
	 *       45 278 frames thrown away while the heartbeat never matured —
	 *       the whole story is on `batti_fra()`. */
	if (e == RCP_VIDEO_SERVE_UNA_CHIAVE)
		video_rifiutato_per_chiave(w, ora_ms);
	/* ⛔ And the refusal is NOT a fatal error: §2.3 — «the server MUST withstand
	 * the refusal to open a stream instead of considering it a fatal
	 * error».  ⚠ The lines have already been written by `rcp.c`, which knows which of the seven
	 * reasons it is: here we count and keep quiet, or the same thing would end up twice
	 * in the log with two different words. */
}

/* ⭐⭐ §7.2 — the cursor shape to all the sessions of that user.
 *
 * ⛔ And the name comparison is NOT a formality: the deposit is per process and
 *    the sessions belong to different users.  Sending the cursor shape of
 *    another is not a graphical defect — it is the image of what
 *    another person is doing ending up on the wrong screen. */
void wt_cursore_diffondi(const char *utente, uint16_t larghezza,
                         uint16_t altezza, int16_t attivo_x, int16_t attivo_y,
                         const uint8_t *immagine, size_t byte)
{
	if (!utente || !utente[0])
		return;
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || strcmp(mio, utente) != 0)
			continue;
		/* ⚠ The return is not looked at here: `rcp.c` has already written in the log
		 *   which of its reasons it is — and looking at it ourselves too would put the
		 *   same thing twice with two different words. */
		rcp_cursore_forma(w->rcp, larghezza, altezza, attivo_x, attivo_y,
		                  immagine, byte);
	}
}

/* ⛔⭐⭐ THE SIZE THE STAGE HAS NOW, per user — and it outlives the
 *     connection, like the stage (invariant I4).
 *
 * ⛔ IT SERVES THE REATTACH, and it is the only place in the parent where that number
 *    exists: `rcp.c` knows the GRANTED canvas, the child knows the REAL one, and
 *    between the two only frames pass.  ⇒ It is read from the frame — which is
 *    also the only source that does not lie (`DECISIONI.md` §5.0-sexies).
 *
 * ⚠ It is not a cache to keep fresh: it is a FACT dated at the last frame
 *   delivered.  If the stage dies and is reborn at another size, the first line of
 *   `rcp_tela_concessa()` notices and asks the stage to come to where the
 *   canvas in force is.
 *
 * ⛔⭐ ONE ENTRY PER USER, AND THE NUMBER COMES FROM `rcp.h` — 25 Aug 2026.
 *
 *     They were **eight** with the excuse that *«`MAX_ATTACCATE` is of the same
 *     order»*, and ⛔ «of the same order» means **that it bit at nine**,
 *     that is before the ten `SPECIFICHE.md` §5.5 promises (finding
 *     **R10-A6**).  The ninth and tenth users lost the reattach
 *     cure, and ⛔ **silently**, because the fallback below is
 *     declared **once only** and the eighth had already spent it.
 *
 * ⇒ Now it is the session cap: it is the same quantity — «one per served
 *   user» — and by construction it can no longer run out before the slots.
 *
 * ⭐⭐ And since the evening of 25 Aug 2026 it is **allocated** on `rcp_tetto()`, which
 *     `--tetto-sessioni` moves at startup: the `WT_PALCHI` that was here has
 *     disappeared, and was not left next to it as a «maximum». */
static struct palco_misura {
	/* ⛔ 257 and not 64: it is the size of the `utente` field of `rcp.c`.  ⚠ With a
	 *    shorter field `snprintf` truncated on writing and `strcmp` compared
	 *    the WHOLE name with the truncated one: the entry was never found again, a
	 *    new one was taken at every frame, and in eight rounds the table was full
	 *    of the same name — switched off **for all the users of the machine**.
	 *    Defect found by refuting, 15 Aug 2026. */
	char utente[257];
	uint32_t l, a;
} *palchi;
static int quanti_palchi;
static bool palchi_pieni_detto;

/* ⛔ It is allocated at the first size to note, once only.  ⚠ If the memory
 *    is not there, the fallback is the one this table already declares: at
 *    reattach the canvas is granted as the client asks for it.  Nobody dies
 *    because of this, but it is written. */
static bool palchi_pronti(void)
{
	if (palchi)
		return true;
	quanti_palchi = rcp_tetto();
	palchi = (struct palco_misura *)calloc((size_t)quanti_palchi,
	                                       sizeof *palchi);
	if (!palchi) {
		quanti_palchi = 0;
		return false;
	}
	return true;
}

static void palco_misura_segna(const char *utente, uint32_t l, uint32_t a)
{
	int libero = -1;

	if (!utente || !utente[0] || !l || !a)
		return;
	if (!palchi_pronti())
		return;
	for (int i = 0; i < quanti_palchi; i++) {
		if (palchi[i].utente[0] == '\0') {
			if (libero < 0)
				libero = i;
			continue;
		}
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		palchi[i].l = l;
		palchi[i].a = a;
		return;
	}
	if (libero < 0) {
		/* ⛔ The fallback is DECLARED (`CODER.md` §4.2), and once only: without
		 *    this line the ninth user lost the reattach cure
		 *    silently, and the symptom would have been «for me the desktop on reattach
		 *    does not come back» for that one user. */
		if (!palchi_pieni_detto) {
			palchi_pieni_detto = true;
			registro_dice_di(REG_RCP, utente,
			                 "⚠ DECLARED FALLBACK: the table of stage canvases "
			                 "is full (%d): «%s» does not fit, and on its reattach the "
			                 "canvas will be granted as the client asks for it instead "
			                 "of as the stage has it",
			                 quanti_palchi, utente);
		}
		return;
	}
	snprintf(palchi[libero].utente, sizeof palchi[libero].utente, "%s", utente);
	palchi[libero].l = l;
	palchi[libero].a = a;
}

/* ⛔⭐ THE STAGE IS DEAD: its size is no longer a fact, it is a memory.
 *
 * ⚠ Defect found by refuting: without this line the entry stayed, and on
 *   reattach `SESSIONE` granted **yesterday's size** — that of a stage
 *   that no longer exists.  The new stage delivers another one, the session is born
 *   in disagreement, and the reattach cure turned against itself.
 * ⛔ «I don't know» and «it was 1920x1080» are two different facts, and the second, when
 *    it is false, is worse than the first. */
void wt_palco_dimentica(const char *utente)
{
	if (!utente || !utente[0])
		return;
	for (int i = 0; i < quanti_palchi; i++) {
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		registro_dice_di(REG_RCP, utente,
		                 "the canvas of the stage of «%s» (%ux%u) is forgotten: that stage "
		                 "is gone, and an old number passed off as a fact is "
		                 "worse than no number",
		                 utente, palchi[i].l, palchi[i].a);
		memset(&palchi[i], 0, sizeof palchi[i]);
		palchi_pieni_detto = false;
		return;
	}
}

/* ⭐⭐ THE STAGE'S ANSWER ABOUT THE CANVAS — §7.1, and it arrives from the CHILD.
 *
 * ⛔ It goes to ALL the sessions of that user, and not only to whoever asked: the
 *    stage's canvas is a single one, and a session that did not know it would keep
 *    discarding every frame for wrong size.  ⚠ `rcp.c` decides by itself
 *    whether that message answers a request OF ITS OWN — here we do not choose. */
void wt_tela_dal_palco(const char *utente, uint32_t voluta_l, uint32_t voluta_a,
                       uint32_t avuta_l, uint32_t avuta_a)
{
	/* ⛔ And the table is updated HERE and not only from frames: this is the
	 *    freshest news the parent has about the stage's size, and it arrives
	 *    even when no frame leaves. */
	palco_misura_segna(utente, avuta_l, avuta_a);
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		rcp_tela_dal_palco(w->rcp, voluta_l, voluta_a, avuta_l, avuta_a,
		                   w->conn ? ngtcp2_conn_get_timestamp(w->conn)
		                                 / NGTCP2_MILLISECONDS
		                           : 0);
	}
}

static bool wt_palco_misura(const char *utente, uint32_t *l, uint32_t *a)
{
	if (!utente || !utente[0])
		return false;
	for (int i = 0; i < quanti_palchi; i++) {
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		if (!palchi[i].l || !palchi[i].a)
			return false;
		if (l)
			*l = palchi[i].l;
		if (a)
			*a = palchi[i].a;
		return true;
	}
	return false;
}

/* ⛔ The hook `rcp.c` calls in `ATTACCA`.  ⚠ The user is the one PAM
 *    admitted on THIS session: asking for another's stage would mean telling
 *    this client the size of somebody else's desktop. */
static bool gancio_tela_del_palco(void *ctx, uint32_t *l, uint32_t *a)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!w->rcp)
		return false;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return wt_palco_misura(mio, l, a);
}

/* ⛔⭐⭐ HOW MANY SESSIONS FIT IN **ONE** QUESTION TO THE GUARD — and ⛔ it is NOT the
 *      session cap, however much it resembles it.  Finding R8 of §5.5,
 *      looked at and **decided** on 25 Aug 2026.
 *
 * ⛔ THE FINDING WAS: *«it is the FIFTH hand copy of the cap, born precisely in the
 *    round that unified four of them»*.  ⇒ The right question is not «can it be
 *    unified», it is **«is it the same quantity?»**.
 *
 * ⭐⭐ THE ANSWER IS NO, and for two independent reasons — so **it is not
 *     unified**, exactly like `MAX_IN_VOLO` in `aiutante.c` (finding
 *     R10-A7), which was left separate for the same reason:
 *
 *   1. ⛔ **It is the size of a BATCH, not of a capacity.**  `RCP_TETTO_SESSIONI`
 *      says *«how many users are served»*: whoever does not fit **is refused**
 *      (`0x0E`).  This one says *«how many names fit in one question to logind»*:
 *      whoever does not fit **enters the next round** — the `while (dal)` below
 *      exists for this.  ⇒ Exceeding it takes nothing away from anyone; and the
 *      property the code defends is not «one call», it is **a FIXED number
 *      of calls instead of `N`**: at 64 tenants it is two, not 64.
 *   2. ⛔ **It must be a compile-time constant**, and the cap no longer is
 *      one: `--tetto-sessioni N` moves it at startup (`rcp_tetto()`), while
 *      below there are four arrays **on the stack** — among them
 *      `quali[][160]`, which at 32 already weighs 5 KiB.  Tying them to a number that
 *      arrives at run time would mean a VLA of a size chosen by the command
 *      line inside the loop that delivers frames: a NEW defect,
 *      not a cure.  ⚠ *Unifying for symmetry when it is another thing
 *      makes the code worse and makes it look better.*
 *
 * ⭐ BUT THE PREVIOUS COMMENT WAS LYING, and that half is cured: it said «32 is
 *    above the **sixteen** slots of `rcp.c`» — ⛔ a **literal**, and on top of that
 *    one day out of date (since 25 August the default is **10**).  ⇒ The
 *    link that really exists is an **inequality in one direction only**, and it is
 *    written below where the compiler can enforce it instead of in a
 *    comment nobody rereads. */
#define WT_RIPASSO_INSIEME 32

/* ⛔ The only thing that must hold: with the DEFAULT cap the second round never
 *    happens, that is one sweep = one call.  ⚠ If one day
 *    `RCP_TETTO_SESSIONI` exceeded this number, the code would stay
 *    CORRECT (two rounds, two calls) but the count of §6.13 would have to be redone:
 *    ⭐ better to notice here, at compile time, than by reading `chiamate=` at
 *    twice the expected value six months later. */
_Static_assert(WT_RIPASSO_INSIEME >= RCP_TETTO_SESSIONI,
               "the sweep batch is smaller than the default session "
               "cap: a sweep would cost more than ONE call to "
               "logind already in the stock configuration (§6.13)");
#define WT_RIPASSO_QUALE 160

size_t wt_sorveglia_locali(void)
{
	size_t congedate = 0;
	wt *dal = vive_prima;

	/* ⛔ Without the SWEEP hook we do not fall back on the `ATTACCA` one, and
	 *    it is not laziness: falling back would mean silently putting back
	 *    the per-tenant question this code exists to
	 *    remove — that is the defect would come back the day someone
	 *    forgets to connect the hook, **without a red line**.  ⭐ Whoever does not
	 *    connect it does not apply the «watched» half of §5.1, and it is `main.c`
	 *    that writes so in the log at startup.
	 * ⛔⛔ AND UNTIL 25 AUG 2026 THIS SENTENCE WAS FALSE (finding R7 of §5.5):
	 *      `main.c` **wrote nothing**, and the net this comment
	 *      declared did not exist.  ⭐ Now the line is really there — look for
	 *      «the WATCHED half» in the startup log — and it says the value in
	 *      force **on AND off**.  ⚠ A comment promising a nonexistent
	 *      guard is worse than no guard: whoever reads stops
	 *      looking for it. */
	if (!gancio_locali)
		return 0;

	/* ⛔ The list is looked at every round instead of keeping a list of users:
	 *    a session can be born and die between two sweeps, and a list that
	 *    updates itself is a second state to keep in agreement with the first —
	 *    that is the way two truths get into a program. */
	while (dal) {
		const char *nomi[WT_RIPASSO_INSIEME];
		wt *chi[WT_RIPASSO_INSIEME];
		bool locale[WT_RIPASSO_INSIEME];
		char quali[WT_RIPASSO_INSIEME][WT_RIPASSO_QUALE];
		size_t quanti = 0;
		wt *w;

		/* ── 1. WHO IS THERE, in memory and without asking anybody anything ── */
		for (w = dal; w && quanti < WT_RIPASSO_INSIEME; w = w->viva_dopo) {
			const char *mio;

			if (!w->rcp || w->chiusura >= 0)
				continue;
			mio = rcp_utente(w->rcp);
			if (!mio || !mio[0])
				continue;
			nomi[quanti] = mio;
			chi[quanti] = w;
			quanti++;
		}
		dal = w;
		if (!quanti)
			break;

		/* ── 2. ⭐⭐ THE QUESTION, and there is ONE for all of them ────────
		 * ⛔ It used to be one per tenant, and the cost was `N × D` inside the loop that
		 *    delivers frames: `[M]` §6.13, the frontier narrowed
		 *    as 1/N and cut the 300 ms `sentinella.c` already allows itself at
		 *    ~4 tenants.  Here the cost is `D`, and it no longer depends on N. */
		gancio_locali(gancio_locali_ctx, nomi, quanti, locale,
		              &quali[0][0], WT_RIPASSO_QUALE);

		/* ── 3. AND THEN THE FAREWELL, which costs nobody anything ─────── */
		for (size_t k = 0; k < quanti; k++) {
			if (!locale[k])
				continue;
			/* ⛔⭐ §5.1: «it has an active REMOTE graphical session and opens a
			 *     LOCAL one ⇒ **the local one wins**: the remote one is closed».
			 *
			 * ⭐ And it is the only point of the product where the server takes away a
			 *    HEALTHY session — `DECISIONI.md` §4.1-bis admits it **only** with
			 *    a reason that can be told, and that is why `0x04` exists. */
			registro_dice_di(REG_WT, nomi[k],
			                 "⛔ «%s» has opened a LOCAL graphical session (%s): the "
			                 "remote session is being closed — §5.1, reason 0x04",
			                 nomi[k], quali[k][0] ? quali[k] : "no detail");
			wt_congeda(chi[k], RCP_SESSIONE_LOCALE_PREVALSA,
			           "a local graphical session has been opened on this "
			           "machine");
			congedate++;
		}
	}
	return congedate;
}

/* ⛔ The box is in `webtransport.h`: it is the DENOMINATOR that was missing from the
 *    guard's line (finding R7).  ⚠ The same three guards as the sweep
 *    above, in the same order: whoever is not a served tenant is not counted. */
size_t wt_inquilini_serviti(void)
{
	size_t quanti = 0;

	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;

		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !mio[0])
			continue;
		quanti++;
	}
	return quanti;
}

void wt_tela_rimanda(const char *utente, uint32_t voluta_l, uint32_t voluta_a)
{
	uint64_t ora = registro_ora_ms();

	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		rcp_tela_rimanda(w->rcp, voluta_l, voluta_a, ora);
	}
}

size_t wt_congeda_utente(const char *utente, uint8_t motivo, const char *dettaglio,
                         const wt *tranne)
{
	size_t quante = 0;

	if (!utente || !utente[0])
		return 0;
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;

		if (w == tranne || !w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || strcmp(mio, utente) != 0)
			continue;
		wt_congeda(w, motivo, dettaglio);
		quante++;
	}
	return quante;
}

/* ⛔⭐ THE CANVAS CAP OF WHOEVER IS KNOCKING — phase 10, and it serves the BUDGET.
 *
 *     At `consegna_verdetto()` the session's canvas **is not yet decided**
 *     (it is decided at `SESSIONE`), but its cap is known from `CIAO` on:
 *     `video.misura_massima` of §4.3, which §4.5 requires to be respected.  ⇒ The
 *     cost of the newcomer is counted on that cap — an **upper bound**, that is the
 *     uncomfortable direction, that is the right one (`LEZIONI.md` §1.33).
 *
 * ⚠ It goes through here and not through `rcp.h` directly because `webtransport.c` is the one
 *   that knows **which sessions belong to that user** — the same reason, and the
 *   same road, as `wt_congeda_utente()` above.
 * ⚠ And if that user's sessions are more than one **the widest** is taken:
 *   counting the narrowest would be choosing the convenient number.
 * ⛔ `false` = none of its sessions declared it, and it is not «zero»: the
 *    caller falls back on the stage's canvas. */
bool wt_misura_massima_di(const char *utente, uint32_t *l, uint32_t *a)
{
	uint32_t ml = 0, ma = 0;

	if (!utente || !utente[0])
		return false;
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		uint32_t sl, sa;

		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || strcmp(mio, utente) != 0)
			continue;
		if (!rcp_misura_massima(w->rcp, &sl, &sa))
			continue;
		if ((uint64_t)sl * sa > (uint64_t)ml * ma) {
			ml = sl;
			ma = sa;
		}
	}
	if (!ml || !ma)
		return false;
	if (l)
		*l = ml;
	if (a)
		*a = ma;
	return true;
}

void wt_video_diffondi(const char *utente, uint8_t codec, bool chiave,
                       const uint8_t *dati, size_t byte, uint32_t larghezza,
                       uint32_t altezza, uint64_t istante_us, uint32_t input)
{
	/* ⛔⛔ THIS LINE SILENTLY THREW AWAY EVERY H.264 FRAME — 20 Aug
	 *     2026, and it took half an hour to find it.
	 *
	 * Codec 3 entered `RCP.md` §6.2 and this guard knew two of them:
	 * the child encoded (5 940 bytes, KEYFRAME, 1.6 ms in hardware), the parent
	 * received («frame from «prova»: codec 3»), and here **the frame
	 * vanished without a line**.  ⇒ Live session, counters at zero, and no
	 * log naming the cause.
	 *
	 * ⭐ Now the maximum number comes from ONE place — `RCP_CODEC_VIDEO_MAX` —
	 *    and the refusal **is declared** (a single line, not one per frame:
	 *    at sixty a second it would be the defect of the 30.8 GB). */
	if (codec < 1 || codec > RCP_CODEC_VIDEO_MAX) {
		static uint8_t detto;

		if (detto != codec) {
			detto = codec;
			registro_dice_di(REG_WT, utente,
			                 "⛔ frame with codec %u DROPPED: §6.2 defines "
			                 "%u of them (1 = HEVC, 2 = AV1, 3 = H.264).  ⚠ The line is "
			                 "written once per number, not once per frame",
			                 codec, (unsigned) RCP_CODEC_VIDEO_MAX);
		}
		return;
	}
	/* ⛔ It is noted BEFORE delivering, and it holds even if there is no session
	 *    to deliver to: it is a fact of the stage, not of the connection — and it is
	 *    exactly the reattach case, where the session that will see that
	 *    number **does not exist yet**. */
	palco_misura_segna(utente, larghezza, altezza);
	for (wt *w = vive_prima; w; w = w->viva_dopo)
		video_a_una(w, utente, codec, chiave, dati, byte, larghezza, altezza,
		            istante_us, input);
}

/* ------------------------------------------------------------------------ */
/* ⭐ THE AUDIO BLOCK ARRIVING FROM THE SESSION, DELIVERED TO ONE SESSION.    */

static void audio_a_una(wt *w, const char *utente, uint8_t codec,
                        uint64_t istante_us, const uint8_t *dati, size_t byte)
{
	uint8_t buf[WT_DGRAM_BYTE];
	size_t p = 0;
	uint64_t tetto;
	const char *mio;

	/* ⚠ The twin of `video_fermo` in `video_a_una()`: the tail of what was
	 *   already in flight when the child was told to stop. */
	if (!w->audio_acceso || w->audio_fermo || w->audio_codec != codec)
		return;
	if (!w->rcp || !w->conn || w->chiusura >= 0)
		return;

	/* ⛔⭐ INVARIANT I3, AND IT HOLDS FOR SOUND EXACTLY AS FOR PIXELS.
	 *
	 *     `[M]` 12 Aug 2026 the defect showed up on video: «prova» received
	 *     a conforming frame, and the frame was «nicfio»'s desktop.
	 *     ⛔ On audio the same defect is WORSE to notice: a wrong desktop
	 *     is recognised by looking at it, a wrong phone call is not. */
	mio = rcp_utente(w->rcp);
	if (!mio || !utente || strcmp(mio, utente) != 0)
		return;

	tetto = dgram_tetto_del_pari(w);
	if (tetto == 0) {
		if (!w->dgram_negati_detto) {
			w->dgram_negati_detto = true;
			registro_dice_di(REG_RCP, wt_chi(w),
			                 "⛔ %s: the peer does NOT accept datagrams "
			                 "(`max_datagram_frame_size` = 0) — this session will not "
			                 "have audio.  ⚠ `RCP.md` §2.2 DEMANDS them, but §6.3 "
			                 "forbids closing over a datagram fact: it is "
			                 "declared and then kept quiet",
			                 w->provenienza);
		}
		return;
	}

	/* The RFC 9297 prefix: a quarter of the identifier of the stream on
	 * which the WebTransport session lives.  ⛔ Without it, the browser discards the
	 * datagram **without an error**: it is not a field of ours, it is the envelope. */
	p = varint_scrivi(buf, (uint64_t)w->sessione / 4);

	/* The framing of `RCP.md` §6.3, in network order. */
	if (p + 12 + byte > sizeof buf || (uint64_t)(p + 12 + byte) > tetto) {
		w->audio_buttati++;
		if (w->audio_buttati == 1 || w->audio_buttati % 100 == 0)
			registro_dice_di(REG_WT, wt_chi(w),
			                 "⛔ %s: audio block of %zu bytes too big "
			                 "(prefix %zu + 12 + %zu, peer's cap %llu) — "
			                 "dropped.  Dropped %llu",
			                 w->provenienza, byte, p, byte,
			                 (unsigned long long)tetto,
			                 (unsigned long long)w->audio_buttati);
		return;
	}
	buf[p++] = 0x04;
	buf[p++] = 0x01; /* type `0x0401`, the only one defined in RCP/1 */
	buf[p++] = 0x00;
	buf[p++] = codec; /* `codec` u16: 1 = Opus, 2 = PCM */
	for (int i = 7; i >= 0; i--)
		buf[p++] = (uint8_t)(istante_us >> (8 * i)); /* `istante` u64 */
	memcpy(buf + p, dati, byte);
	p += byte;

	dgram_accoda(w, buf, p);
}

/* ------------------------------------------------------------------------ */
/* ⭐ THE TEST TONE — the source that certifies the wire, and NOTHING ELSE.   */
/*
 * ⛔⭐ WHY IT EXISTS, AND WHY IT IS NOT A SHORTCUT
 *
 *     The audio chain has five links: the sink in the session, the
 *     capture of the monitor, the encoder, the datagram, the browser that plays.
 *     Switching them all on together and then hearing nothing leaves **five
 *     suspects** — and it is exactly the way this project lost
 *     its worst days (`LEZIONI.md` §10).
 *
 *     This source puts **only three** of them under test — encoder, datagram,
 *     browser — with a signal of which **every sample is known in advance**.
 *     ⇒ If the tone comes out at 440 Hz at the other end, the wire is acquitted and what
 *     remains is the capture.  If it does not come out, the capture has nothing to do with it.
 *
 * ⛔ IT IS OFF if nobody switches it on (`--audio-prova`), and it is invariant I6:
 *    whatever changes what the user hears stays behind a switch that is off
 *    until they have looked at it.  ⚠ When it is on it WRITES so, at every session:
 *    a server playing a tone without saying so would be a defect disguised
 *    as a feature.
 *
 * ⚠ And what this source does NOT test, declared: the rhythm.  The blocks
 *   come out in bursts when the heartbeat is long, instead of one every 20 ms —
 *   it is the defect v1 paid for on `SendSamples2` (`altoparlante.h`, «the client
 *   THROWS AWAY short blocks»).  The rhythm will come from capture, which has a clock
 *   of its own; here one looks at the CONTENT, not the cadence.
 */
void wt_audio_gancio(wt_audio_richiesta f, void *ctx)
{
	gancio_audio = f;
	gancio_audio_ctx = ctx;
}

void wt_audio_prova(uint32_t hz)
{
	audio_prova_hz = hz;
	if (hz)
		registro_dice(REG_WT,
		              "⚠ TEST TONE ON at %u Hz — every admitted session "
		              "will hear a tone instead of the desktop.  ⛔ It is a bench "
		              "function (I6): in a normal installation it is not switched on",
		              hz);
}

static void tono_passo(wt *w, ngtcp2_tstamp ts)
{
	/* ⛔ A cap per pass: without it, a long heartbeat would generate a hundred
	 *    blocks in one go, the queue would throw away ninety-two of them and the log
	 *    would say «dropped» for a defect that is not the network's. */
	int quanti = 0;
	uint64_t ora_us;
	const char *utente;

	if (!audio_prova_hz || !w->audio_acceso || w->chiusura >= 0 || !w->rcp)
		return;

	utente = rcp_utente(w->rcp);
	if (!utente || !utente[0])
		return;

	if (!w->tono_cod) {
		w->tono_cod = audio_cod_apri(w->audio_codec);
		if (!w->tono_cod) {
			/* ⛔ This session is switched off, not the server: the log has
			 *    already said so inside `audio_cod_apri`. */
			w->audio_acceso = false;
			return;
		}
	}

	ora_us = ts / NGTCP2_MICROSECONDS;
	if (w->tono_prossimo_us == 0)
		w->tono_prossimo_us = ora_us;

	while (ora_us >= w->tono_prossimo_us && quanti < WT_DGRAM_MAX) {
		int16_t campioni[AUDIO_BLOCCO_OPUS * AUDIO_CANALI];
		uint8_t fuori[AUDIO_FUORI_MAX];
		size_t n = 0;
		uint32_t blocco = audio_cod_blocco(w->tono_cod);

		for (uint32_t i = 0; i < blocco; i++) {
			/* ⭐ The phase is CONTINUOUS between one block and the next (`tono_i` is not
			 *    reset): restarting from zero at every block would produce a
			 *    click every 20 ms, that is an audible defect fabricated by the
			 *    bench and blamed on the encoder. */
			double t = (double)(w->tono_i + i) / (double)AUDIO_FREQUENZA;
			double v = 0.5 * sin(2.0 * M_PI * (double)audio_prova_hz * t);
			int16_t s = (int16_t)(v * 32767.0);
			campioni[i * AUDIO_CANALI] = s;
			campioni[i * AUDIO_CANALI + 1] = s;
		}
		w->tono_i += blocco;

		if (audio_cod_passa(w->tono_cod, campioni, fuori, &n))
			audio_a_una(w, utente, w->audio_codec, w->tono_prossimo_us, fuori, n);

		w->tono_prossimo_us += (uint64_t)blocco * 1000000ULL / AUDIO_FREQUENZA;
		quanti++;
	}
}

void wt_audio_diffondi(const char *utente, uint8_t codec, uint64_t istante_us,
                       const uint8_t *dati, size_t byte)
{
	if (codec != 1 && codec != 2)
		return;
	for (wt *w = vive_prima; w; w = w->viva_dopo)
		audio_a_una(w, utente, codec, istante_us, dati, byte);
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ AND THE TWO DOORS FROM THE CHILD TOWARDS THE WIRE.                    */

static void appunti_a_una(wt *w, const char *utente, const char *testo,
                          size_t byte)
{
	const char *mio;

	if (!w->rcp)
		return;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0] || strcmp(mio, utente) != 0)
		return;
	rcp_appunti_dalla_sessione(w->rcp, testo, byte);
}

void wt_appunti_dalla_sessione(const char *utente, const char *testo,
                               size_t byte)
{
	if (!utente || !testo)
		return;
	for (wt *w = vive_prima; w; w = w->viva_dopo)
		appunti_a_una(w, utente, testo, byte);
}

bool wt_appunti_richiesta(const char *utente, uint32_t serial)
{
	if (!utente)
		return false;
	/* ⛔ It stops at the FIRST that answers yes, and it is not an optimisation: by
	 *    invariant I2 a user has **a single** live remote connection at a
	 *    time (§5.1, `GIA_ATTIVA_REMOTA`), so the first is the only one.  ⚠ If
	 *    one day I2 changed, this line would be the place where it is decided
	 *    WHOM to ask — and then the choice would have to be written, not left
	 *    to the order of a list. */
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		uint64_t ora;

		if (!w->rcp || !w->conn)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !mio[0] || strcmp(mio, utente) != 0)
			continue;
		/* ⛔ The clock is asked of ngtcp2, which is the one with which `rcp_tempo()`
		 *    will measure the backstop: two different clocks on the same quantity
		 *    would give a backstop that expires earlier or later than it says. */
		ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
		if (rcp_appunti_chiedi(w->rcp, serial, ora))
			return true;
	}
	return false;
}

/* ⛔⭐⭐ THE CENSUS OF WHO IS LISTENING, and the THREE exclusions that make it true.
 *
 *      1. `tranne` — the session for which the decision is being made.  Before it was enough
 *         to call the census AFTER leaving the list of live ones (the
 *         box in `wt_libera()` says so: *«or it would find itself and would never
 *         switch off»*), but from today the decision is also made at FAREWELL, and there the
 *         session is still fully in the list.  ⇒ The exclusion is
 *         written instead of depending on the order of two distant lines.
 *      2. `rcp_e_finita()` — ⛔ a finished session does NOT listen.  The pointer
 *         `w->rcp` stays standing until the client closes the stream — and
 *         if the browser says goodbye and disappears that stream never closes —
 *         so without this line a GHOST would keep the desktop's microphone on
 *         for everybody else.  It is the same line, for the same
 *         reason, that `linea_morta_giudica()` already has.
 *      3. `audio_fermo` — whoever has already said «stop» is not asked again.
 *
 * ⚠ The LIVE sessions of the same user on OTHER connections stay inside:
 *   it is the case I2 provides for, and if one of those is watching, capture does not
 *   stop.  It is precisely the reason why this is not «switch off at
 *   farewell» but «switch off if you are left alone». */
static bool audio_ascolta_qualcuno(const char *utente, const wt *tranne,
                                   uint8_t *codec)
{
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (w == tranne)
			continue;
		if (!w->audio_acceso || w->audio_fermo || !w->rcp || w->chiusura >= 0)
			continue;
		if (rcp_e_finita(w->rcp))
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		if (codec)
			*codec = w->audio_codec;
		return true;
	}
	return false;
}

bool wt_audio_qualcuno_ascolta(const char *utente, uint8_t *codec)
{
	return audio_ascolta_qualcuno(utente, NULL, codec);
}

void wt_audio_conti(const wt *w, uint64_t *spediti, uint64_t *buttati,
                    uint64_t *rifiutati, size_t *in_coda)
{
	if (spediti)
		*spediti = w ? w->audio_spediti : 0;
	if (buttati)
		*buttati = w ? w->audio_buttati : 0;
	if (rifiutati)
		*rifiutati = w ? w->audio_rifiutati : 0;
	if (in_coda)
		*in_coda = w ? w->ndgram : 0;
}

/* ⚠ The twin of the audio census, and the three exclusions are the same:
 *   the box is there, and the two are read together. */
static bool video_guarda_qualcuno(const char *utente, const wt *tranne,
                                  uint8_t *codec)
{
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (w == tranne)
			continue;
		if (!w->video_acceso || w->video_fermo || !w->rcp || w->chiusura >= 0)
			continue;
		if (rcp_e_finita(w->rcp))
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		if (codec)
			*codec = w->video_codec;
		return true;
	}
	return false;
}

bool wt_video_qualcuno_guarda(const char *utente, uint8_t *codec)
{
	return video_guarda_qualcuno(utente, NULL, codec);
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐⭐ CAPTURE STOPS WHEN NOBODY WATCHES OR LISTENS ANY MORE.            */
/*
 * ⭐ IT IS A SINGLE FUNCTION FOR THREE OCCASIONS, and they are three because a session
 *    can end in three ways that do not go through one another:
 *
 *      1. `regola_battito()` — the session is `"finita"`: the client said
 *         FAREWELL.  It is the new occasion, the one that pays the ~30 s, and it covers
 *         all seven roads by which `rcp.c` reaches that state.
 *      2. `wt_stream_chiuso()` — the client closes the CONNECT stream or the
 *         control channel.  ⛔ There `w->rcp` is FREED and reset: from
 *         that moment the user's name can no longer be asked of
 *         anyone, and indeed before today that road NEVER switched off
 *         capture — not even at the death of the connection, because the
 *         block in `wt_libera()` demands a non-null `w->rcp`.  ⇒ It is called
 *         BEFORE `rcp_libera()`, while the name is still there.
 *      3. `wt_libera()` — the connection goes away without the client having
 *         said goodbye (`kill -9`, the network dropping, the `max_idle_timeout`).  It is
 *         the occasion that already existed, and it stays: whoever dies does not say farewell.
 *
 * ⛔ In all three the STAGE STAYS UP — invariant **I4**.  What is switched off is the
 *    consumption, not the graphical session: `figli_video()` with codec 0 and
 *    `figli_audio()` with codec 0 mean «stop capturing», not
 *    «dismantle».  The child, the windows and the sink stay where they are, and whoever
 *    reconnects finds their desktop again — which is the whole point of I4.
 *
 * ⚠ And it is idempotent by construction (`video_fermo` / `audio_fermo`): the three
 *   occasions may well fire in a row on the same session — a
 *   farewell, then the stream closed, then the connection dying — and the child
 *   gets the «enough» only once.
 */
static void cattura_spegni_se_sola(wt *w, const char *perche)
{
	const char *mio;

	if (!w->rcp)
		return;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return;

	if (w->audio_acceso && !w->audio_fermo && gancio_audio
	    && !audio_ascolta_qualcuno(mio, w, NULL)) {
		w->audio_fermo = true;
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "%s and nobody listens to «%s» any more: audio "
		                 "capture stops (the sink stays, it is invariant "
		                 "I4)",
		                 perche, mio);
		gancio_audio(gancio_audio_ctx, mio, 0);
	}
	if (w->video_acceso && !w->video_fermo && gancio_palco
	    && !video_guarda_qualcuno(mio, w, NULL)) {
		w->video_fermo = true;
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "%s and nobody watches «%s» any more: the stage stops "
		                 "capturing (the child stays, it is invariant I4)",
		                 perche, mio);
		/* ⚠ «Stop capturing»: the codec is 0, and the depth with
		 *   it means nothing. */
		gancio_palco(gancio_palco_ctx, mio, 0, 0, 0, false);
	}
}

void wt_video_conti(const wt *w, uint32_t *diffusi, uint32_t *saltati,
                    uint32_t *spediti, uint32_t *abbandonati,
                    uint32_t *ritmo_scesi)
{
	if (diffusi)
		*diffusi = w ? w->video_diffusi : 0;
	if (saltati)
		*saltati = w ? w->video_saltati : 0;
	/* ⭐ PHASE 9 — the fifth number, and it is here and not in `rcp.c` because it is a
	 *    decision of the TRANSPORT: rcp knows nothing of this frame, it was
	 *    never offered to it. */
	if (ritmo_scesi)
		*ritmo_scesi = w ? w->video_ritmo_scesi : 0;
	rcp_video_conti(w ? w->rcp : NULL, spediti, abbandonati);
}

static void rcp_avvia(wt *w, int64_t stream_id)
{
	rcp_ganci g;

	w->rcp_stream = stream_id;

	memset(&g, 0, sizeof g);
	g.ctx = w;
	g.manda = gancio_manda;
	g.chiudi = gancio_chiudi;
	g.registra = gancio_registra;
	g.verifica = gancio_verifica;
	/* ⛔ And it is connected ONLY if the helper is there: `rcp.c` looks at this pointer
	 *    to decide which of the two roads to take, and connecting it to nothing
	 *    would mean telling it «ask nobody». */
	if (w->aiuto)
		g.chiedi_verifica = gancio_chiedi;

	/* ⛔ §2.5: the video channel lives on unidirectional server streams.
	 *
	 * ⚠ And ALL FOUR are connected: `rcp.c` refuses to open if one is
	 *   missing, because a host that could open and not reset could not
	 *   honour §5.1 — and it would notice halfway through a frame.
	 * ⭐ Compatibility with the graft of `banchi/rcp/` comes free: there the
	 *   `memset` above leaves them NULL, and `rcp_video_apri()` returns
	 *   `RCP_VIDEO_NIENTE_CANALE` instead of keeping quiet. */
	g.video_apri = gancio_video_apri;
	g.video_scrivi = gancio_video_scrivi;
	g.video_fin = gancio_video_fin;
	g.video_azzera = gancio_video_azzera;

	/* ⭐⭐ §7.4 — THE CLIPBOARD CHANNEL, and ALL FIVE are connected or none.
	 *
	 * ⛔ And the condition is the bridge towards the stage, as for input: without it,
	 *    `rcp.c` would validate the messages (that is protocol) and then
	 *    declare it served nothing.  ⚠ But the three of the WIRE
	 *    depend only on the transport, not on the stage: hooking them all together
	 *    is a choice, and the reason is that half a channel is of no use to anyone —
	 *    announcing to the client a text that then cannot be sent, or sending it
	 *    what the session copied without being able to serve whoever pastes, are
	 *    two halves the user sees as «the clipboard does not work». */
	if (gancio_palco_appunti_offri && gancio_palco_appunti_risposta) {
		g.appunti_apri = gancio_appunti_apri;
		g.appunti_scrivi = gancio_appunti_scrivi;
		g.appunti_fin = gancio_appunti_fin;
		g.appunti_offri = gancio_appunti_offri;
		g.appunti_risposta = gancio_appunti_risposta;
	}

	/* ⭐⭐ §7.3 — THE INPUT CHANNEL.  ⛔ And ALL SIX are connected or none:
	 *     `rcp.c` looks at the first and if it is there demands the others, because a
	 *     channel that could move the pointer and could not release a
	 *     button would leave the desktop **worse than it found it**.
	 * ⚠ And they are connected only if the bridge towards the stage is there: without it,
	 *   `rcp.c` validates the message all the same (that is protocol) and
	 *   writes that it did not inject it.  «I have no input channel» and «the
	 *   client made a mistake» are two different facts. */
	if (gancio_palco_input) {
		g.input_puntatore = gancio_input_puntatore;
		g.input_pulsante = gancio_input_pulsante;
		g.input_rotella = gancio_input_rotella;
		g.input_lettera = gancio_input_lettera;
		g.disposizione = gancio_disposizione;
		g.disposizione_esiste = gancio_disposizione_esiste;
		g.input_posizione = gancio_input_posizione;
		g.input_rilascia_tutto = gancio_input_rilascia_tutto;
	}

	/* ⭐⭐ §7.1 — THE CANVAS HOOK, and it is connected ON ITS OWN: it does not belong to the
	 *     six of input, and the reason is that without it `rcp.c` has a
	 *     right answer to give — `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` —
	 *     while without the six of input it has none.
	 * ⚠ And like those, it is connected only if the bridge towards the stage is there: a
	 *   hook connected to nothing would tell `rcp.c` «I can resize» and then
	 *   would leave the client waiting for a frame nobody asked
	 *   anybody for. */
	if (gancio_palco_ritela)
		g.ritela = gancio_ritela;

	/* ⛔⭐ AND THIS ONE IS ALWAYS CONNECTED, even without the bridge towards the stage: it
	 *     asks nobody anything — it reads a number this module already has,
	 *     the last size delivered by that user's stage.  ⚠ If it is not there
	 *     yet (first attach, no frame) it answers `false`, and `rcp.c`
	 *     grants what the client asks: the previous behaviour. */
	g.tela_del_palco = gancio_tela_del_palco;

	/* ⛔⭐ §5.1 — and it is connected ONLY if the guard is there, like all the others:
	 *     a hook connected to nothing would tell `rcp.c` «I looked, there is
	 *     no local session», which is the worse lie of the two — because
	 *     it is indistinguishable from the truth. */
	if (gancio_locale)
		g.sessione_locale = gancio_sessione_locale;

	/* ⭐ §7.6 — and it is connected only if there is someone who can really terminate the
	 *    session: without it, `rcp.c` says farewell with `0x10` and writes that the desktop
	 *    was not touched, instead of making believe it has ended. */
	if (gancio_termina)
		g.termina_sessione = gancio_termina_sessione;

	/* ⭐ D-001 — `SESSIONE` says whether the stage was there and which desktop it is. */
	g.sessione_ripresa = gancio_sessione_ripresa;
	g.desktop = gancio_desktop;

	/* ⛔ And the cap of §7.17 is SWITCHED OFF here: the channel has been opened, which is
	 *    the thing that clock was waiting for.  ⚠ Zero and not «past»: a
	 *    disarmed clock and an expired one must not look the same. */
	w->canale_entro = 0;

	w->rcp = rcp_apri(&g, w->provenienza,
	                  ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);

	/* ⛔ AND HERE THE CLOCK OF THE FIRST CAP IS ARMED — §4.6 line 1.  `rcp_apri`
	 *    sets the state to `attesa-ciao` and starts the stopwatch: the
	 *    stopwatch and the clock that will make it expire start from the same
	 *    line.  In the graft this was missing, and a client that opened the channel
	 *    and then went quiet stayed hanging forever (`[M]` B6). */
	regola_battito(w);
	registro_dice_di(REG_RCP, wt_chi(w), "control channel = stream %ld", (long)stream_id);
}

static void rcp_passa(wt *w, const uint8_t *dati, size_t len)
{
	uint64_t ora;
	if (!w->rcp)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi(w->rcp, dati, len, ora)) {
		/* The session is over.  The heartbeat that matures the closing
		 * capsule has already been armed by `chiudi_sessione()`, which is
		 * the only point crossed by ALL the roads of closure —
		 * including the two that do not come through here at all. */
		return;
	}
	/* ⭐ AND HERE, not one round later: `rcp_ricevi()` is the line that may have
	 *    just sent `SESSIONE`, and waiting for the heartbeat would cost up to one
	 *    whole second before the desktop appears — that is the number
	 *    the user looks at. */
	video_regola(w, ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);
	audio_regola(w);
	regola_battito(w);
}

/* ⭐⭐ THE INPUT CHANNEL — the seam of phase 4, 14 Aug 2026.
 *
 * ⛔ Before today the input bytes really arrived and ended up in
 *    `conta_credito()` **and that was all**: the channel was lawful, the log line
 *    declared it («this phase does not serve it»), and the client could move the
 *    mouse for an hour without anything reaching the desktop.  ⇒ Here that
 *    declared tolerance is CLOSED.
 *
 * ⚠ `stream` travels with the bytes and it is not an extra: `RCP.md` §2.5 admits
 *   **a single** input stream, and without the identifier `rcp.c` cannot
 *   tell the second stream from the continuation of the first.  ⛔ And whoever
 *   hosts cannot judge it in its place: it sees the streams, but does not know what
 *   is «input» until it has read the first two bytes of the payload.
 *
 * ⚠ And the `false` return is treated as in `rcp_passa()`: the session is
 *   over, and the closing capsule has already been armed by `chiudi_sessione()`. */
static void rcp_passa_input(wt *w, int64_t stream, const uint8_t *dati,
                            size_t len)
{
	uint64_t ora;
	if (!w->rcp || len == 0)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi_input(w->rcp, stream, dati, len, ora))
		return;
	/* ⛔ And the heartbeat is put back in line from here too: an input may have
	 *    triggered a farewell (a violation of §7.3), and waiting for the
	 *    next round would leave the reason stuck in the queue. */
	regola_battito(w);
}

/* ⭐⭐ PHASE 7 — the bytes of the CLIPBOARD channel (0x02), §2.5 and §7.4.
 *
 * ⛔ And `fin` arrives all the way here, while for input it did not: there the stream is
 *    a single one and stays open, here it is **one per transfer** and its end
 *    is the only way `rcp.c` has to free the slot in the table.  ⚠ Without it,
 *    the channel would work for the first eight transfers and then stop
 *    — that is the worst defect to diagnose: the one that shows up later. */
static void rcp_passa_appunti(wt *w, int64_t stream, const uint8_t *dati,
                              size_t len, bool fin)
{
	uint64_t ora;
	if (!w->rcp)
		return;
	if (len == 0 && !fin)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi_appunti(w->rcp, stream, dati, len, fin, ora))
		return;
	regola_battito(w);
}

/* ------------------------------------------------------------------------ */
/* Closing the WebTransport session.                                         */

static void chiudi_adesso(wt *w, uint8_t motivo)
{
	uint8_t b[16];
	size_t n = 0;

	/* ⛔⭐ THE CAPSULE GOES INSIDE A `DATA` FRAME, AND IN THE GRAFT IT WENT OUT NAKED.
	 *
	 *    The body of an extended CONNECT is a stream of capsules (RFC 9297),
	 *    but in HTTP/3 the body of a message travels inside `DATA` frames:
	 *    the capsule does NOT sit naked on the stream.  ⭐ And that the client
	 *    encapsulates them is proved by our own READING side: the capsule
	 *    reaches us from `recv_data`, which nghttp3 invokes only on the payload
	 *    of a `DATA`.
	 *
	 * ⛔ Written naked, the seven bytes `68 43 04 00 00 00 mm` are read by the browser
	 *    with its own HTTP/3 layer: `0x68` has the two high bits at `01`,
	 *    so it is a two-byte variable-length integer, and the frame type
	 *    becomes `0x2843` — which is not a known HTTP/3 frame type, and RFC
	 *    9114 §9 requires it to be IGNORED.  The page saw no capsule:
	 *    it saw only the FIN arriving right behind, and a FIN on the
	 *    CONNECT stream without `CLOSE_WEBTRANSPORT_SESSION` closes the session
	 *    with code 0 — that is the only value `RCP.md` §3.1 forbids. */
	b[n++] = 0x00; /* frame DATA */
	b[n++] = 7;    /* 2 bytes of type + 1 of length + 4 of code */
	b[n++] = 0x68; /* 0x2843, first byte of the variable-length integer */
	b[n++] = 0x43;
	b[n++] = 4; /* the capsule's length: only the code */
	b[n++] = 0;
	b[n++] = 0;
	b[n++] = 0;
	b[n++] = motivo;

	if (!coda_metti(w, w->sessione, b, n, true)) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ the closing capsule does not fit in the queue");
		return;
	}
	registro_dice_di(REG_WT, wt_chi(w),
	                 "closed the WebTransport session, code 0x%02x (%zu bytes: "
	                 "2 of DATA frame + 7 of capsule)",
	                 motivo, n);
}

static void chiudi_sessione(wt *w, uint8_t motivo)
{
	/* ⛔ `RCP.md` §3.1 point 3: the WebTransport SESSION is closed with the
	 *    application error code equal to the reason code — not the
	 *    QUIC connection, which can carry other things. */
	if (w->sessione == -1)
		return;

	/* ⛔⭐ AND THE CAPSULE IS DEFERRED, instead of being enqueued now — found by
	 *     B11 on 10 Aug 2026, with real browsers.
	 *
	 *     `respingi()` sends `RESPINTO` on the control channel and closes the
	 *     session on the next line.  The two ended up in the same write
	 *     pass, that is often in the same flight of packets — and the
	 *     browser processes the `CLOSE_WEBTRANSPORT_SESSION` capsule BEFORE the
	 *     stream bytes, which at that point it throws away.  ⛔ The page never
	 *     saw `RESPINTO`: it saw silence.
	 *
	 * ⛔ AND ENQUEUING THE CAPSULE BEHIND THE `CONGEDO`, IN THE SAME QUEUE, IS NOT
	 *    THE CURE: the order on the wire would be there, ⚠ but the order on the wire is not
	 *    what is missing.  What is needed is TIME between the two. */
	w->chiusura = motivo;
	/* ⛔⭐ THE WAIT STARTS NOW, not «when a heartbeat sees the queue empty»
	 *     — measured by bench B7 on 11 Aug 2026, case `server-in-chiusura`.
	 *
	 *     Here there was `w->chiusura_da = 0`, that is «not armed»: arming it was
	 *     the branch of `wt_batti` that finds the queue already empty.  ⛔ At
	 *     shutdown that branch was never taken — the server's log
	 *     said it in these words: «closing capsule not
	 *     mature yet (queue empty) — chiusura_da = NEVER ARMED» after 200
	 *     rounds, when fifty were enough.
	 *
	 * ⛔ What the client saw: the `CONGEDO 0x0c` arrived, and the session
	 *    closed WITHOUT a code — QUIC terminated with `code 0, no
	 *    reason`.  That is the SECOND road of §3.1 point 3 was missing, which the
	 *    decisions of 11 August (§7.14, §7.15) make the only one that always
	 *    arrives — on Firefox, which resets the channel, it was the ONLY one.
	 *
	 * ⚠ And the meaning does not change: if the queue is NOT empty, the `!coda_vuota`
	 *   branch of `wt_batti` resets this field and the wait starts over, as
	 *   before.  What changes is that now the wait exists even when
	 *   nobody comes back to say «the queue is empty». */
	w->chiusura_da = ngtcp2_conn_get_timestamp(w->conn)
	                 + WT_ATTESA_CHIUSURA_NS;
	/* ⛔ AND THE WAIT HAS A BACKSTOP — finding B-3.  «When the queue has
	 *    emptied» is a condition someone else must make happen; if
	 *    it does not happen, point 3 of §3.1 is never executed and the reason stays
	 *    inside the server.  Three seconds is six times the normal wait. */
	w->chiusura_scadenza =
	    ngtcp2_conn_get_timestamp(w->conn) + 3ULL * NGTCP2_SECONDS;
	/* ⛔ And whoever postpones a job must also switch on what will make it
	 *    mature: without this heartbeat, on a violation found at the first
	 *    message the client goes quiet, nobody comes back here and the capsule never
	 *    leaves.  ⚠ It is the defect measured by B5 — 22 out of 36. */
	batti_fra(w, 100);
	registro_dice_di(REG_WT, wt_chi(w),
	                 "session closure DEFERRED, code 0x%02x (in the queue: "
	                 "%zu elements still to send)",
	                 motivo, coda_da_spedire(w));
}

static void manda_controllo(wt *w, const uint8_t *dati, size_t len)
{
	if (w->rcp_stream == -1)
		return;
	(void)accoda(w, w->rcp_stream, dati, len);
}

/* ⛔⭐ THE BYTES OF A SURPLUS STREAM ARE THROWN AWAY, AND NOT SENT BACK
 *     — finding B-3, night of 10 Aug 2026.
 *
 *     Here there was `accoda(w, stream_id, dati, len)`, that is the server sent back
 *     to the client its own bytes on a stream that two lines above it had
 *     just judged a **violation of §2.5**.  ⛔ An echo no line
 *     of `RCP.md` provides for, and three consequences each worse than the other:
 *
 *       1. `coda_vuota()` never became true, so the closing capsule
 *          of §3.1 point 3 never left (see `chiusura_scadenza`);
 *       2. `conta_credito()` reopened the window at every round, so the
 *          client could write without end — and the 30 s idleness did not
 *          fire, because it was writing;
 *       3. the queue grew as much as the client wanted, on a session already
 *          declared dead (see `WT_CODA_MAX`).
 *
 * ⭐ What is done instead: they are thrown away, the credit is NOT reopened, and §3 requires it
 *    — «and every tolerance must be written in the log».  ⚠ The lines are counted and
 *    not one per packet: a client writing without end would fill the
 *    log, which is another way of losing the information. */
static void scarta_stream_di_troppo(wt *w, int64_t stream_id, size_t len)
{
	w->scartati_stream++;
	w->scartati_byte += len;
	if (w->scartati_stream <= 3 || (w->scartati_stream % 256) == 0)
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ %zu bytes DROPPED from stream %ld: it is not the control "
		                 "channel (§2.5, the violation is already on record) — "
		                 "%llu blocks, %llu bytes in total, and the credit is NOT "
		                 "reopened",
		                 len, (long)stream_id,
		                 (unsigned long long)w->scartati_stream,
		                 (unsigned long long)w->scartati_byte);
}

/* ------------------------------------------------------------------------ */
/* The capsules arriving from the client.                                    */

static void chiusa_dal_client(wt *w, uint32_t codice)
{
	bool valido;
	uint8_t motivo;

	/* ⛔⭐ AND FIRST OF ALL WE CHECK WHETHER THAT CODE EXISTS.
	 *
	 *    `RCP.md` §3.1: code 0 means «closure without reason» and MUST NOT
	 *    be used — every closure has a reason of §8.2.  And §3 — the
	 *    rigor rule — asks to write IN THE LOG what was not
	 *    understood, not to make up for it silently.
	 *
	 * ⛔ AND THE CODE ARRIVES ON 32 BITS, NOT ON 8: truncating it to the low byte
	 *    put `0x0100` on record as `0x00`, that is as the only
	 *    value §3.1 forbids, and the two logs of the SAME closure
	 *    contradicted each other two lines apart. */
	valido = codice >= (uint32_t)RCP_CHIUSO_DALL_UTENTE &&
	         codice <= (uint32_t)RCP_GIA_ATTIVA_REMOTA;
	if (!valido)
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⛔ VIOLATION §3.1 — the page closed the session "
		                 "with code 0x%x, which is not a reason of §8.2 "
		                 "(0 = «without reason», and it is forbidden).  On record goes "
		                 "ERRORE_PROTOCOLLO",
		                 codice);
	motivo = (uint8_t)(valido ? codice : (uint32_t)RCP_ERRORE_PROTOCOLLO);

	if (w->rcp && rcp_e_finita(w->rcp))
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⭐ the reason arrived by the second road of "
		                 "§3.1 (the close code): 0x%02x — the bytes on the "
		                 "channel could no longer be sent",
		                 motivo);
	/* ⛔ And the SLOT is given up now: §4.2, the session is over because the
	 *    client says so.  Waiting for the transport teardown means
	 *    keeping it occupied against whoever reconnects at once. */
	if (w->rcp)
		rcp_chiusa_dal_client(w->rcp, motivo);
}

/* ⛔⭐ The body of an extended CONNECT is a stream of capsules (RFC 9297):
 * varint type, varint length, body.  Of all of them, only ONE is looked at here:
 * `CLOSE_WEBTRANSPORT_SESSION` (0x2843).  ⚠ It is accumulated, because a capsule
 * can arrive in pieces; and the rest is discarded without noise, because a stream
 * of unknown capsules is not an error (RFC 9297 §3.2). */
static void capsula(wt *w, int64_t stream_id, const uint8_t *dati, size_t len)
{
	if (stream_id != w->sessione || len == 0)
		return;

	/* ⛔ The bytes of a capsule already judged too big are thrown away
	 *    AS THEY PASS, without keeping them: it is the only way not to get one's
	 *    memory filled by whoever can write two variable-length integers. */
	if (w->capsalta > 0) {
		uint64_t n = w->capsalta < len ? w->capsalta : (uint64_t)len;
		w->capsalta -= n;
		dati += n;
		len -= (size_t)n;
		if (len == 0)
			return;
	}
	if (!bytes_aggiungi(&w->capsbuf, dati, len))
		return;

	for (;;) {
		uint64_t tipo = 0, lung = 0;
		size_t a, b;
		const uint8_t *corpo;

		/* ⚠ Here the buffer cannot grow without end: a variable-length
		 *   integer is at most 8 bytes, so with 16 bytes type and
		 *   length are always read. */
		a = varint_leggi(&tipo, w->capsbuf.d, w->capsbuf.n);
		if (a == 0)
			return;
		b = varint_leggi(&lung, w->capsbuf.d + a, w->capsbuf.n - a);
		if (b == 0)
			return;

		/* ⛔⭐ AND THE LENGTH IS CHECKED HERE, BEFORE WAITING FOR THE BYTES.
		 *
		 *    The entry point this closes: the page sends, on the
		 *    CONNECT stream, an unknown capsule type and a
		 *    length of 2^62-1, then sends data forever.  No
		 *    capsule ever completed, the buffer grew by every byte
		 *    that arrived — and the credit kept widening, so
		 *    the client could send without end.  ⛔ On a connection
		 *    that has not yet passed the RCP handshake. */
		if (lung > WT_CAPSULA_MAX) {
			uint64_t qui = w->capsbuf.n - a - b;
			uint64_t presi = qui < lung ? qui : lung;
			registro_dice_di(REG_WT, wt_chi(w),
			                 "capsule 0x%llx %llu bytes long, beyond the "
			                 "cap of %d: SKIPPED without keeping it (RFC "
			                 "9297 §3.2; RCP.md §6.1)",
			                 (unsigned long long)tipo,
			                 (unsigned long long)lung, WT_CAPSULA_MAX);
			w->capsalta = lung - presi;
			bytes_togli_testa(&w->capsbuf, a + b + (size_t)presi);
			if (w->capsalta > 0)
				return;
			continue;
		}
		if (w->capsbuf.n < a + b + lung)
			return; /* it is below the cap: we can wait */

		corpo = w->capsbuf.d + a + b;
		if (tipo == 0x2843 && lung >= 4) {
			uint32_t codice = ((uint32_t)corpo[0] << 24) |
			                  ((uint32_t)corpo[1] << 16) |
			                  ((uint32_t)corpo[2] << 8) |
			                  (uint32_t)corpo[3];
			registro_dice_di(REG_WT, wt_chi(w),
			                 "the page CLOSED the "
			                 "WebTransport session: code 0x%x",
			                 codice);
			chiusa_dal_client(w, codice);
		}
		bytes_togli_testa(&w->capsbuf, a + b + (size_t)lung);
	}
}

/* ------------------------------------------------------------------------ */
/* The sorting: what is WebTransport and what belongs to nghttp3.           */

/* ⛔ `RCP.md` §4.2: «a FIN on that stream, from either of the two sides,
 *    closes the session.  Whoever receives it MUST consider it over».  ⚠ It was
 *    the only one of the two directions nobody had walked: the page that
 *    closes the writing side of the channel and keeps the connection alive left
 *    the registry slot occupied until the connection died — and a
 *    connection, a browser keeps alive. */
static void fin_dal_client(wt *w, int64_t stream_id)
{
	if (!w->rcp || stream_id != w->rcp_stream)
		return;
	registro_dice_di(REG_RCP, wt_chi(w),
	                 "⛔ CLIENT FIN on the control channel (stream %ld): "
	                 "§4.2, the session is over",
	                 (long)stream_id);
	rcp_canale_chiuso(w->rcp);
}

static void conta_credito(wt *w, int64_t stream_id, size_t n)
{
	if (n == 0)
		return;
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, n);
	ngtcp2_conn_extend_max_offset(w->conn, n);
}

enum esito { E_MIO, E_ATTENDI, E_HTTP3 };

/* ⛔ `RCP.md` §2.5 — the unidirectional streams opened by the CLIENT.
 *
 * ⭐ How the channel is recognised: «the first two bytes of the stream are read,
 *    which are in any case a `tipo` field».  The high byte says the channel, and of
 *    five lawful values THREE are violations when they arrive from here:
 *
 *    0x00  control    ⛔ control lives only on the first bidirectional one
 *    0x01  input      ✓  lawful: it is the only unidirectional one the client opens
 *    0x02  clipboard  ✓  lawful, one per transfer
 *    0x03  video      ⛔ wrong direction: video goes from server to client
 *    0x04  audio      ⛔ «only on datagrams.  On a stream it is ERRORE_PROTOCOLLO»
 *
 * ⚠ And even before that one must know whether the stream is OURS: among the
 *   client's unidirectional ones there are HTTP/3's control channel and the two
 *   of QPACK, which belong to nghttp3.  A WebTransport stream is recognised by its
 *   type, 0x54 — which like 0x41 does not fit in a byte: on the wire it is 0x40 0x54. */
static enum esito smista_uni(wt *w, int64_t stream_id, const uint8_t *dati,
                             size_t len, bool fin, bytes *riunito)
{
	stream_giudizio *g = giudizio_trova(w, stream_id);
	uint64_t sessione = 0;
	size_t n, consumati;
	uint16_t tipo;
	uint8_t canale;
	const uint8_t *carico = NULL;
	size_t carico_n = 0;
	const char *guasto = NULL;

	if (g) {
		switch (g->genere) {
		case G_NONWT:
			return E_HTTP3;
		case G_UNI_OK:
		case G_UNI_KO:
			/* ⚠ The two verdicts are NOT the same thing:
			 *   G_UNI_KO  violation, the session has already dropped;
			 *   G_UNI_OK  LAWFUL §2.5 channel that this phase does not
			 *             serve yet (input arrives in phase 4,
			 *             the clipboard in 7).
			 *   ⛔ In the graft both were marked «violation»,
			 *      and a conforming client opening the input channel
			 *      saw EVERY byte discarded forever, without a
			 *      log line.
			 *   In both cases the bytes are counted against the credit:
			 *   not counting them would leave the client without credit on
			 *   a live connection (§2.3). */
			conta_credito(w, stream_id, len);
			return E_MIO;
		case G_UNI_INPUT:
			/* ⭐ The input channel, already recognised: the bytes are
			 *    counted against the credit **and delivered**.  ⛔ The
			 *    credit before delivery: if delivery made the
			 *    session drop, those bytes have arrived anyway
			 *    and the count of §2.3 must not fall behind. */
			conta_credito(w, stream_id, len);
			rcp_passa_input(w, stream_id, dati, len);
			return E_MIO;
		case G_UNI_APPUNTI:
			/* ⭐ The clipboard channel, already recognised.  ⛔ The credit BEFORE
			 *    delivery, as for input, and for the same reason: if
			 *    delivery made the session drop, those bytes have
			 *    arrived anyway and the count of §2.3 must not fall
			 *    behind. */
			conta_credito(w, stream_id, len);
			rcp_passa_appunti(w, stream_id, dati, len, fin);
			return E_MIO;
		default:
			break;
		}
	} else {
		g = giudizio_crea(w, stream_id);
		if (!g)
			return E_HTTP3;
	}

	if (!bytes_aggiungi(&g->pref, dati, len))
		return E_HTTP3;
	if (g->pref.n < 2)
		return E_ATTENDI;

	if (!(g->pref.d[0] == 0x40 && g->pref.d[1] == 0x54)) {
		/* It is not WebTransport: it belongs to nghttp3, and the bytes must be delivered
		 * whole — including those we held back. */
		bytes_aggiungi(riunito, g->pref.d, g->pref.n);
		bytes_libera(&g->pref);
		g->genere = G_NONWT;
		return E_HTTP3;
	}
	n = varint_leggi(&sessione, g->pref.d + 2, g->pref.n - 2);
	if (n == 0 || g->pref.n < 2 + n + 2)
		return E_ATTENDI; /* the `tipo` field has not fully arrived yet */

	consumati = g->pref.n;
	tipo = (uint16_t)((g->pref.d[2 + n] << 8) | g->pref.d[2 + n + 1]);
	canale = (uint8_t)(tipo >> 8);
	/* ⛔ THE RCP PAYLOAD STARTS HERE, and it starts **with `tipo`**: the two bytes we
	 *    have just peeked at to know which channel it is belong to the
	 *    message, not to the preamble.  ⚠ Peeking at them and then not delivering them
	 *    would give `rcp.c` a message without a header — and the symptom
	 *    would be «the first input of every session is malformed».
	 * ⚠ And `bytes_libera()` was moved to the end on purpose: until that
	 *   moment `carico` points inside `g->pref`. */
	carico = g->pref.d + 2 + n;
	carico_n = g->pref.n - (2 + n);
	conta_credito(w, stream_id, consumati);

	switch (canale) {
	case 0x00:
		guasto = "the CONTROL channel on a unidirectional stream: control "
		         "lives only on the first bidirectional stream (§2.5)";
		break;
	case 0x03:
		guasto = "the VIDEO channel from the client: it belongs to the server, wrong direction "
		         "(§2.5)";
		break;
	case 0x04:
		guasto = "the AUDIO channel on a stream: audio lives only on "
		         "datagrams (§2.5, §6.3)";
		break;
	case 0x01:
	case 0x02:
		break;
	default:
		guasto = "unknown high byte of the type on a unidirectional "
		         "stream (§2.5)";
		break;
	}
	g->genere = guasto           ? G_UNI_KO
	            : canale == 0x01 ? G_UNI_INPUT
	            : canale == 0x02 ? G_UNI_APPUNTI
	                             : G_UNI_OK;
	registro_dice_di(REG_WT, wt_chi(w),
	                 "client unidirectional stream %ld, session %llu, type "
	                 "0x%04x, channel 0x%02x — %s",
	                 (long)stream_id, (unsigned long long)sessione, tipo, canale,
	                 guasto ? "VIOLATION"
	                 : canale == 0x01
	                        ? "⭐ INPUT, and from today it is SERVED: the bytes go to "
	                          "rcp_ricevi_input() (§7.3)"
	                 : canale == 0x02
	                        ? "⭐ CLIPBOARD, and since phase 7 it is SERVED: the bytes go "
	                          "to rcp_ricevi_appunti() (§7.4).  ⚠ One stream per "
	                          "transfer, so of these there is more than one"
	                        : "lawful (§2.5).  ⚠ But this phase does not serve it: the "
	                          "bytes are counted against the credit and discarded, and "
	                          "this line is the declared tolerance (§3)");
	if (guasto) {
		if (w->rcp) {
			rcp_violazione(w->rcp, guasto);
		} else {
			/* ⚠ No control channel open yet: the `CONGEDO`
			 *   has no road, and point 3 of §3.1 remains — the
			 *   reason inside the session closure.  ⭐ It is the
			 *   second conditional of §3.1 at work: demanding
			 *   all three points always would give red on the
			 *   right code. */
			registro_dice_di(REG_WT, wt_chi(w),
			                 "⚠ no control channel: the reason "
			                 "travels only in the session closure");
			chiudi_sessione(w, RCP_ERRORE_PROTOCOLLO);
		}
	} else if (canale == 0x01) {
		/* ⭐ The first piece of the input channel arrives together with the
		 *    preamble that made it recognisable: it is delivered AT ONCE.
		 *    ⛔ Waiting for the next packet would lose the first
		 *    message of every session — and the first message is
		 *    precisely the one the user feels as «the first click
		 *    did nothing». */
		rcp_passa_input(w, stream_id, carico, carico_n);
	} else if (canale == 0x02) {
		/* ⭐ As for input: the first piece arrives together with the preamble that
		 *    made it recognisable, and it is delivered AT ONCE.  ⛔ Waiting for the
		 *    next packet would lose the first message of every
		 *    transfer — and on this channel a transfer is often ONE
		 *    message only, so the whole transfer would be lost.
		 * ⚠ And the `fin` travels with it: a stream carrying a short message
		 *   can arrive all together, preamble and FIN included. */
		rcp_passa_appunti(w, stream_id, carico, carico_n, fin);
	}
	bytes_libera(&g->pref);
	return E_MIO;
}

static enum esito smista(wt *w, int64_t stream_id, const uint8_t *dati,
                         size_t len, bool fin, bytes *riunito)
{
	stream_giudizio *g;
	uint64_t sessione = 0;
	size_t n, consumati;

	/* ⛔ The unidirectional ones OPENED BY THE CLIENT (§2.5) go through here first of
	 *    all: among them there are HTTP/3's control channel and the two of
	 *    QPACK, which belong to nghttp3 and not to us. */
	if ((stream_id & 0x03) == 0x02)
		return smista_uni(w, stream_id, dati, len, fin, riunito);

	/* Only the bidirectional streams opened by the client: the extended CONNECT and
	 * the WebTransport streams all arrive from there. */
	if ((stream_id & 0x03) != 0x00)
		return E_HTTP3;

	g = giudizio_trova(w, stream_id);
	if (g && g->genere == G_NONWT)
		return E_HTTP3;

	if (g && g->genere == G_WT) {
		/* ⭐ A WebTransport stream already recognised. */
		if (len > 0) {
			if (stream_id == w->rcp_stream) {
				rcp_passa(w, dati, len);
				conta_credito(w, stream_id, len);
			} else {
				/* ⛔ They are NOT sent back and the credit is NOT
				 *    reopened: see `scarta_stream_di_troppo()`. */
				scarta_stream_di_troppo(w, stream_id, len);
			}
		}
		/* ⛔ AND THE FIN IS LOOKED AT AFTER THE BYTES, not before: the last bytes
		 *    arrived TOGETHER with it and must be delivered while the
		 *    session is still alive, or whoever receives them would read them as
		 *    bytes sent after the end — that is as a client violation
		 *    that never happened. */
		if (fin)
			fin_dal_client(w, stream_id);
		return E_MIO;
	}

	if (!g) {
		g = giudizio_crea(w, stream_id);
		if (!g)
			return E_HTTP3;
	}
	if (!bytes_aggiungi(&g->pref, dati, len))
		return E_HTTP3;
	if (g->pref.n < 2) {
		/* ⚠ AND the window is NOT widened: those bytes have not been
		 *   taken by anyone yet, and counting them now and then again would distort the
		 *   credit. */
		return E_ATTENDI;
	}

	/* ⛔ The WEBTRANSPORT_STREAM frame type is 0x41 — but a variable-length
	 *    integer does not write it in one byte: 0x41 is 65, and one byte holds
	 *    63.  On the wire it is TWO bytes, 0x40 0x41, and that is why
	 *    two are enough to decide.  A HEADERS frame starts with 0x01,
	 *    a DATA one with 0x00. */
	if (!(g->pref.d[0] == 0x40 && g->pref.d[1] == 0x41)) {
		bytes_aggiungi(riunito, g->pref.d, g->pref.n);
		bytes_libera(&g->pref);
		g->genere = G_NONWT;
		return E_HTTP3;
	}

	n = varint_leggi(&sessione, g->pref.d + 2, g->pref.n - 2);
	if (n == 0)
		return E_ATTENDI;

	consumati = g->pref.n;
	g->genere = G_WT;

	/* ⭐ `RCP.md` §4.2: the FIRST bidirectional stream the client opens
	 *    in the session is the control channel.
	 *
	 * ⚠ And «the first» HERE is the first RECOGNISED, not the first OPENED: the
	 *   two streams travel in different packets, and between different streams the
	 *   network promises no order. */
	if (w->rcp_stream == -1) {
		rcp_avvia(w, stream_id);
	} else {
		/* ⛔ `RCP.md` §2.5: «the client MUST NOT open bidirectional
		 *    streams beyond 0».  A second bidirectional one is not
		 *    a new channel: it is a violation.
		 *
		 * ⛔ AND THE DIAGNOSIS MUST NOT BLAME THE ORDER OF ARRIVAL.  If
		 *    this stream has a LOWER number than the elected one, the
		 *    first opened was this one, and it was the network that swapped them: the
		 *    streams stay two — and two is the violation, however they
		 *    arrived — but «a second stream» said of the lower
		 *    number sends people looking for the defect in the client, which there got
		 *    nothing wrong. */
		if (stream_id < w->rcp_stream)
			registro_dice_di(REG_WT, wt_chi(w),
			                 "⛔ two bidirectional streams from the client inside "
			                 "the session: %ld and %ld — and the FIRST OPENED "
			                 "was %ld, which arrived second: the control "
			                 "channel was elected by order of "
			                 "arrival, not by number",
			                 (long)w->rcp_stream, (long)stream_id,
			                 (long)stream_id);
		else
			registro_dice_di(REG_WT, wt_chi(w),
			                 "⛔ two bidirectional streams from the client inside "
			                 "the session: control is %ld, and %ld "
			                 "is one too many",
			                 (long)w->rcp_stream, (long)stream_id);
		if (w->rcp)
			rcp_violazione(w->rcp,
			               "two bidirectional streams from the client inside "
			               "the session (§2.5)");
	}
	registro_dice_di(REG_WT, wt_chi(w), "stream %ld is WebTransport, session %llu",
	                 (long)stream_id, (unsigned long long)sessione);

	if (consumati > 2 + n) {
		const uint8_t *resto = g->pref.d + 2 + n;
		size_t rn = consumati - 2 - n;
		if (stream_id == w->rcp_stream)
			rcp_passa(w, resto, rn);
		else
			scarta_stream_di_troppo(w, stream_id, rn);
	}
	bytes_libera(&g->pref);
	/* ⚠ The credit of the PREFIX bytes is reopened anyway: those bytes
	 *   we consumed ourselves to judge the stream, and not counting them
	 *   would block the legitimate control channel too.  ⛔ What is NOT
	 *   reopened is the credit of the bytes of a surplus channel — see the
	 *   branch above and `scarta_stream_di_troppo()`. */
	conta_credito(w, stream_id, consumati);

	/* ⛔ Here too: the stream can be recognised and finished in the same
	 *    packet (§4.2, the FIN from either of the two sides). */
	if (fin)
		fin_dal_client(w, stream_id);
	return E_MIO;
}

/* ------------------------------------------------------------------------ */
/* The nghttp3 callbacks.                                                    */

static int cb_acked(nghttp3_conn *conn, int64_t stream_id, uint64_t datalen,
                    void *cud, void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)datalen;
	(void)cud;
	(void)sud;
	return 0;
}

static int cb_recv_data(nghttp3_conn *conn, int64_t stream_id,
                        const uint8_t *data, size_t datalen, void *cud,
                        void *sud)
{
	wt *w = cud;
	(void)sud;
	(void)conn;
	/* ⭐ The body of the CONNECT is a stream of capsules. */
	capsula(w, stream_id, data, datalen);
	/* The body bytes are counted against the credit: without it, the client is left without
	 * a window on a live connection (§2.3). */
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, datalen);
	ngtcp2_conn_extend_max_offset(w->conn, datalen);
	return 0;
}

static int cb_deferred_consume(nghttp3_conn *conn, int64_t stream_id,
                               size_t consumed, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, consumed);
	ngtcp2_conn_extend_max_offset(w->conn, consumed);
	return 0;
}

static int cb_begin_headers(nghttp3_conn *conn, int64_t stream_id, void *cud,
                            void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	if (!richiesta_trova(w, stream_id, true))
		return NGHTTP3_ERR_CALLBACK_FAILURE;
	return 0;
}

static void copia(char *fuori, size_t cap, nghttp3_rcbuf *v)
{
	nghttp3_vec b = nghttp3_rcbuf_get_buf(v);
	size_t n = b.len < cap - 1 ? b.len : cap - 1;
	memcpy(fuori, b.base, n);
	fuori[n] = 0;
}

static int cb_recv_header(nghttp3_conn *conn, int64_t stream_id, int32_t token,
                          nghttp3_rcbuf *name, nghttp3_rcbuf *value,
                          uint8_t flags, void *cud, void *sud)
{
	wt *w = cud;
	richiesta *r = richiesta_trova(w, stream_id, true);
	(void)conn;
	(void)name;
	(void)flags;
	(void)sud;
	if (!r)
		return 0;
	switch (token) {
	case NGHTTP3_QPACK_TOKEN__PATH:
		copia(r->uri, sizeof r->uri, value);
		break;
	case NGHTTP3_QPACK_TOKEN__METHOD:
		copia(r->metodo, sizeof r->metodo, value);
		break;
	/* ⭐ The header that tells an extended CONNECT from a normal
	 *    CONNECT (RFC 9220). */
	case NGHTTP3_QPACK_TOKEN__PROTOCOL:
		copia(r->protocollo, sizeof r->protocollo, value);
		break;
	default:
		break;
	}
	return 0;
}

/* The extended CONNECT stream is NOT closed: it IS the session.  A reader that
 * said «I have finished» would put the FIN on it, and the session would die
 * the instant it opens. */
static nghttp3_ssize cb_niente_dati(nghttp3_conn *conn, int64_t stream_id,
                                    nghttp3_vec *vec, size_t veccnt,
                                    uint32_t *pflags, void *cud, void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)vec;
	(void)veccnt;
	(void)pflags;
	(void)cud;
	(void)sud;
	return NGHTTP3_ERR_WOULDBLOCK;
}

static int risposta_secca(wt *w, int64_t stream_id, const char *stato)
{
	nghttp3_nv nv[2];
	int rv;

	nv[0].name = (uint8_t *)":status";
	nv[0].namelen = 7;
	nv[0].value = (uint8_t *)stato;
	nv[0].valuelen = strlen(stato);
	nv[0].flags = NGHTTP3_NV_FLAG_NONE;
	nv[1].name = (uint8_t *)"server";
	nv[1].namelen = 6;
	nv[1].value = (uint8_t *)"remotix";
	nv[1].valuelen = 7;
	nv[1].flags = NGHTTP3_NV_FLAG_NONE;

	rv = nghttp3_conn_submit_response(w->h3, stream_id, nv, 2, NULL);
	if (rv != 0)
		registro_dice_di(REG_WT, wt_chi(w), "⛔ nghttp3_conn_submit_response: %s",
		                 nghttp3_strerror(rv));
	return rv;
}

static int apri_sessione(wt *w, richiesta *r)
{
	nghttp3_nv nv[2];
	nghttp3_data_reader dr;
	int rv;

	/* ⛔ `RCP.md` §2.2: the server MUST NOT accept a WebTransport
	 *    session on a different path, and the refusal is 404 (finding
	 *    R1.24, which chose one of the three statuses that were all lawful).  And
	 *    it is written in the log: it is §3 applied to the first byte, before
	 *    RCP even starts. */
	if (strcmp(r->uri, "/rcp/1") != 0) {
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ WebTransport session REFUSED, path «%s» "
		                 "(expected /rcp/1 — §2.2): 404",
		                 r->uri);
		return risposta_secca(w, r->id, "404");
	}

	nv[0].name = (uint8_t *)":status";
	nv[0].namelen = 7;
	nv[0].value = (uint8_t *)"200";
	nv[0].valuelen = 3;
	nv[0].flags = NGHTTP3_NV_FLAG_NONE;
	nv[1].name = (uint8_t *)"server";
	nv[1].namelen = 6;
	nv[1].value = (uint8_t *)"remotix";
	nv[1].valuelen = 7;
	nv[1].flags = NGHTTP3_NV_FLAG_NONE;

	memset(&dr, 0, sizeof dr);
	dr.read_data = cb_niente_dati;

	rv = nghttp3_conn_submit_response(w->h3, r->id, nv, 2, &dr);
	if (rv != 0) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ nghttp3_conn_submit_response: %s",
		                 nghttp3_strerror(rv));
		return rv;
	}

	w->sessione = r->id;

	/* ⛔⭐ AND HERE STARTS THE §4.6 CAP FOR OPENING THE CHANNEL — 5 s.
	 *
	 * ✅ `DECISIONI.md` §7.17, from the user on 11 Aug 2026.  Whoever opens the
	 *    session and never opens the control channel had NO cap
	 *    on them: `[M]` B6, 20 014 ms without anything happening.
	 *
	 * ⛔ And what will make it expire is armed too, at the same instant — it is
	 *    the dearest lesson of the graft, written thirty lines further below in
	 *    `rcp_avvia`: a cap without a heartbeat is a cap that does not expire. */
	w->canale_entro = ngtcp2_conn_get_timestamp(w->conn)
	                  + WT_TETTO_CANALE_NS;
	batti_fra(w, 100);

	registro_dice_di(REG_WT, wt_chi(w), "⭐ WebTransport session OPENED on %s (stream %ld) — "
	                 "the control channel must be opened within %llu ms (§4.6, "
	                 "DECISIONI.md §7.17)",
	                 r->uri, (long)r->id,
	                 (unsigned long long)(WT_TETTO_CANALE_NS / NGTCP2_MILLISECONDS));
	return 0;
}

static int cb_end_headers(nghttp3_conn *conn, int64_t stream_id, int fin,
                          void *cud, void *sud)
{
	wt *w = cud;
	richiesta *r = richiesta_trova(w, stream_id, false);
	(void)conn;
	(void)fin;
	(void)sud;
	if (!r)
		return 0;
	/* ⭐ It is here that the WebTransport session is born. */
	if (strcmp(r->metodo, "CONNECT") == 0 &&
	    strcmp(r->protocollo, "webtransport") == 0)
		return apri_sessione(w, r) == 0 ? 0 : NGHTTP3_ERR_CALLBACK_FAILURE;

	/* ⚠ Everything else is NOT served by this listener: the page is
	 *   served by TCP (`RCP.md` §2.4).  A 404 is the exact answer, and it is
	 *   declared instead of leaving the request hanging. */
	registro_dice_di(REG_WT, wt_chi(w),
	                 "HTTP/3 request %s %s on stream %ld: 404 (over UDP only "
	                 "the WebTransport session is served)",
	                 r->metodo, r->uri, (long)stream_id);
	return risposta_secca(w, stream_id, "404") == 0
	         ? 0
	         : NGHTTP3_ERR_CALLBACK_FAILURE;
}

static int cb_stop_sending(nghttp3_conn *conn, int64_t stream_id,
                           uint64_t app_error_code, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_shutdown_stream_read(w->conn, 0, stream_id, app_error_code);
	return 0;
}

static int cb_reset_stream(nghttp3_conn *conn, int64_t stream_id,
                           uint64_t app_error_code, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_shutdown_stream_write(w->conn, 0, stream_id, app_error_code);
	return 0;
}

static int cb_end_stream(nghttp3_conn *conn, int64_t stream_id, void *cud,
                         void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)cud;
	(void)sud;
	return 0;
}

static void cb_rand(uint8_t *dest, size_t destlen)
{
	for (size_t i = 0; i < destlen; i++)
		dest[i] = (uint8_t)(rand() & 0xff);
}

/* ------------------------------------------------------------------------ */

static int apri_http3(wt *w)
{
	static const nghttp3_callbacks callbacks = {
		.acked_stream_data = cb_acked,
		.recv_data = cb_recv_data,
		.deferred_consume = cb_deferred_consume,
		.begin_headers = cb_begin_headers,
		.recv_header = cb_recv_header,
		.end_headers = cb_end_headers,
		.stop_sending = cb_stop_sending,
		.end_stream = cb_end_stream,
		.reset_stream = cb_reset_stream,
		.rand = cb_rand,
	};
	nghttp3_settings settings;
	const ngtcp2_transport_params *params;
	int64_t ctrl, enc, dec;
	int rv;

	if (w->h3)
		return 0;
	if (ngtcp2_conn_get_streams_uni_left2(w->conn) < 3) {
		registro_dice_di(REG_WT, wt_chi(w),
		                 "⛔ the client does not grant even 3 "
		                 "unidirectional streams: HTTP/3 does not open");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	nghttp3_settings_default(&settings);
	settings.qpack_max_dtable_capacity = 4096;
	settings.qpack_blocked_streams = 100;
	/* ⭐ The two nghttp3 can do by itself, and they are in the RFCs. */
	settings.enable_connect_protocol = 1; /* RFC 9220, the extended CONNECT */
	settings.h3_datagram = 1;             /* RFC 9297 (RCP.md §2.2) */

	rv = nghttp3_conn_server_new(&w->h3, &callbacks, &settings,
	                             nghttp3_mem_default(), w);
	if (rv != 0) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ nghttp3_conn_server_new: %s",
		                 nghttp3_strerror(rv));
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	params = ngtcp2_conn_get_local_transport_params2(w->conn);
	nghttp3_conn_set_max_client_streams_bidi(w->h3,
	                                         params->initial_max_streams_bidi);

	if (ngtcp2_conn_open_uni_stream(w->conn, &ctrl, NULL) != 0 ||
	    ngtcp2_conn_open_uni_stream(w->conn, &enc, NULL) != 0 ||
	    ngtcp2_conn_open_uni_stream(w->conn, &dec, NULL) != 0) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ cannot open the three HTTP/3 service streams");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	/* ⭐ The number is kept: when nghttp3 writes its SETTINGS on
	 *    this stream it will be the only occasion to add the two
	 *    WebTransport declarations to it. */
	w->ctrl_id = ctrl;

	if (nghttp3_conn_bind_control_stream(w->h3, ctrl) != 0 ||
	    nghttp3_conn_bind_qpack_streams(w->h3, enc, dec) != 0) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ cannot bind the service streams to nghttp3");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}
	registro_dettaglio_di(REG_WT, wt_chi(w), "HTTP/3 open: control=%ld qpack=%ld/%ld",
	                           (long)ctrl, (long)enc, (long)dec);
	return 0;
}

/* ------------------------------------------------------------------------ */

wt *wt_nuovo(ngtcp2_conn *conn, ngtcp2_ccerr *ultimo_errore,
             const char *provenienza, aiutante *aiuto)
{
	wt *w = calloc(1, sizeof *w);
	if (!w)
		return NULL;
	w->conn = conn;
	w->ultimo_errore = ultimo_errore;
	w->aiuto = aiuto;
	w->ctrl_id = -1;
	w->sessione = -1;
	w->rcp_stream = -1;
	w->chiusura = -1;
	w->video_stream_ultimo = -1;
	snprintf(w->provenienza, sizeof w->provenienza, "%s",
	         provenienza ? provenienza : "");
	/* ⛔ In the list of live ones BEFORE returning: a frame can
	 *    arrive from the stage between two `poll` rounds, and a session that is not
	 *    in the list does not receive it — without anybody noticing. */
	w->viva_dopo = vive_prima;
	vive_prima = w;
	return w;
}

void wt_libera(wt *w)
{
	if (!w)
		return;
	/* ⛔ Out of the list of live ones BEFORE freeing anything: from here
	 *    on `wt_video_diffondi()` must no longer find it. */
	if (vive_prima == w) {
		vive_prima = w->viva_dopo;
	} else {
		for (wt *p = vive_prima; p; p = p->viva_dopo)
			if (p->viva_dopo == w) {
				p->viva_dopo = w->viva_dopo;
				break;
			}
	}
	/* ⛔⭐ AND THE STAGE IS SWITCHED OFF IF NOBODY IS WATCHING ANY MORE.
	 *
	 *     The child captures and encodes only because someone is watching: a stage
	 *     left on for a closed session would spend a GPU and a CPU
	 *     for nobody, forever.  ⚠ And it is not invariant I1 in reverse —
	 *     I1 forbids lowering the rate **out of caution while someone is watching**;
	 *     here nobody is watching any more, and the stage (I4) stays up: only
	 *     the frame loop stops. */
	/* ⛔⭐ THE AUDIO COUNTS ARE WRITTEN, and before NOBODY read them —
	 *     finding 6 of the review of 17 Aug 2026: `wt_audio_conti()` did not
	 *     have a single caller in all of `src/`, so `audio_spediti`,
	 *     `audio_buttati` and `audio_rifiutati` never reached a line.
	 *     ⚠ On a normal server «audio dropped» and «audio never arrived»
	 *     looked exactly the same — which is the defect those
	 *     counters exist to remove.
	 * ⭐ It is written at the end of the session because it is the instant at which the
	 *    count is complete, and with the ZEROS in it: `CODER.md` §3.10. */
	if (w->audio_acceso) {
		uint64_t sp, bu, ri;
		size_t coda;
		wt_audio_conti(w, &sp, &bu, &ri, &coda);
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "audio of %s, final count: %llu blocks sent, %llu "
		                 "dropped (queue full or too big), %llu refused by "
		                 "ngtcp2, %llu DEFERRED by the pacer and then sent, %zu "
		                 "still in the queue — codec %u",
		                 w->provenienza, (unsigned long long)sp,
		                 (unsigned long long)bu, (unsigned long long)ri,
		                 (unsigned long long)w->audio_rimandati, coda,
		                 w->audio_codec);
	}
	/* ⛔⛔⭐ AND THE VIDEO COUNTS, WHICH NOBODY READ — 22 Aug 2026,
	 *       found by B2, and it is **the same defect as the box above on the
	 *       twin**: `wt_video_conti()` was defined, declared in
	 *       `webtransport.h`, and without **a single caller in all of `src/`**.
	 *
	 *       ⚠ The audio cure was written on 17 August, five days earlier,
	 *       for the twin function and with these same words.  ⇒ It is §1.20: the
	 *       cure had been applied to **one of the two twins**, and nobody had
	 *       looked at the other.  The lesson is not about counters, it is that a cure
	 *       is looked for **wherever it applies**, not where it was found.
	 *
	 * ⛔⛔ AND THE PRICE OF THAT SILENCE WAS A NUMBER THAT LIED.  `[M]` B2:
	 *      **799 frames discarded** and **a single announcement** in the log; whoever
	 *      counted the lines read **1** and called it «not sent».  The
	 *      value was 1, the name promised 799: shape **E2**, and invisible
	 *      because **1 is a number that looks healthy**.
	 *
	 * ⇒ Here ALL FIVE come out, and with the ZEROS in them (`CODER.md` §3.10):
	 *   a zero written and a count never written must have two different faces.
	 *
	 * ⚠ `saltati` adds up **three** causes — the canvas that does not match, the stream
	 *   credit exhausted (§2.3) and the refusal by `rcp.c`.  ⏳ Splitting it in three is
	 *   possible and has NOT been done: it would be a second cure, and this
	 *   line exists to let one out.  The name however does not lie: they are
	 *   really the frames that did not leave.
	 *
	 * ⛔ And nothing of video behaviour is touched: here a diagnostic
	 *    output is added, a policy is not moved.
	 *
	 * ───────────────────────────────────────────────────────────────────────
	 * ⭐ THE PROOF THAT THE TWO NUMBERS ARE REALLY TWO — `[M]` 22 Aug 2026
	 * ───────────────────────────────────────────────────────────────────────
	 *
	 * Same scene in both runs: session of `provar8` on 7802,
	 * `04-b30-scena` moving on the captured monitor, 16 s, three `ADATTA_TELA`
	 * (1264x800 → 1920x1080 → 1264x800).  ⛔ And the fault is INJECTED on purpose
	 * only in the build tree — the declared canvas mismatched for every
	 * frame — because on a healthy product this road is not walked:
	 * the compositor reconfigures in 44-67 ms and no frame has time to
	 * carry the old size.
	 *
	 * | binary  | delivered | NOT SENT    | sent    | ANNOUNCEMENTS |
	 * |---|---|---|---|---|
	 * | healthy             | 1016 | **0**    | 1016 | **0** |
	 * | fault injected      | 0    | **1017** | 0    | **4** |
	 *
	 * ⇒ **1017 against 4: a factor of 254.**  Before the call below the
	 *   only number a bench could read was that of the announcements, and it
	 *   called it «not sent».
	 *
	 * ⚠ And the expectation written beforehand said «ANNOUNCEMENTS = 1», as in B2's run: there
	 *   came out **4**, and it is right so — the backstop rearms at every
	 *   new (canvas, size) pair, and this scene changes it three times.  ⇒ The
	 *   number of announcements follows the DISTINCT SIZES, not the frames: which is
	 *   exactly the reason it could not act as a count. */
	if (w->video_acceso) {
		uint32_t diffusi = 0, saltati = 0, spediti = 0, abbandonati = 0;
		uint32_t ritmo_scesi = 0;
		wt_video_conti(w, &diffusi, &saltati, &spediti, &abbandonati,
		               &ritmo_scesi);
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "video of %s, final count: %u frames delivered to "
		                 "RCP, %u NOT SENT (canvas mismatch + credit "
		                 "exhausted + refusal by rcp), %u sent on the wire, %u "
		                 "abandoned downstream (§5.1) — ⚠ and %u ANNOUNCEMENTS of mismatched "
		                 "canvas, which is a DIFFERENT NUMBER from the not sent: the "
		                 "log writes one for every new size, not one "
		                 "per frame (§E2, B2 22 Aug 2026) — codec %u",
		                 w->provenienza, diffusi, saltati, spediti, abbandonati,
		                 w->video_annunci_tela, w->video_codec);
		/* ⛔⭐ PHASE 9 — and the THRESHOLD count is kept apart, for the reason of
		 *     this whole phase: «zero abandonments» and «the cure is off» must not
		 *     look the same.  ⚠ And the three numbers count three
		 *     different facts: the deltas KEPT say the cure worked,
		 *     those abandoned by threshold that it was not enough, and those without
		 *     credit that the §5.2 debt was kept on by ANOTHER cause —
		 *     4, invisible to the receiver.  Without the third, a cure spinning
		 *     idle looks in every way like a cure that is not needed. */
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⭐ PHASE 9, the video queue threshold: %s (%llu ms) — "
		                 "deltas KEPT %u, abandoned by threshold %u, and NOT "
		                 "ACCEPTED for missing credit %u (§2.3, cause 4: the "
		                 "shape the receiver does not see) — of the kept, %u "
		                 "behind a KEYFRAME still in the queue",
		                 sgombra_soglia_ms ? "ON (default since 24 Aug 2026)"
		                                   : "OFF by hand (--sgombra-soglia-ms 0)",
		                 (unsigned long long)sgombra_soglia_ms,
		                 w->sgombra_tenuti, w->sgombra_abbandoni,
		                 w->sgombra_credito, w->sgombra_dietro_chiave);
		/* ⛔⭐ PHASE 9 — AND THE RATE REGULATOR'S COUNT, which is kept apart
		 *     from the other two for the reason of this whole phase: «zero
		 *     drops» and «the regulator is off» must not look
		 *     the same.  ⚠ And the bottom of the scale is DECLARED here instead of being
		 *     deduced: `DECISIONI.md` §2.1 says 480p·25, and below 25/s on a
		 *     20 Mbit/s line it is a DEFECT — not a successful degradation.
		 *     ⛔ The regulator has no floor to enforce, because
		 *     forcing a frame into a queue that does not empty makes
		 *     the queue worse: here the two numbers are written side by side and the reader
		 *     judges. */
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⭐ PHASE 9, the rate regulator: %s — %u frames that did NOT "
		                 "LEAVE because the backlog had reached the %u slots, out of "
		                 "%u delivered to RCP.  ⚠ It is a number OF ITS OWN: it is not among the «not "
		                 "sent» above.  ⛔ Declared bottom of the scale: 480p "
		                 "25/s on 20 Mbit/s (DECISIONI.md §2.1) — below that it is a "
		                 "DEFECT to look at, not a successful degradation",
		                 ritmo_adattivo ? "ON (default since 24 Aug 2026)"
		                                : "OFF by hand (--niente-ritmo-adattivo)",
		                 ritmo_scesi, (unsigned)WT_RITMO_POSTI, diffusi);
	}
	/* ⛔⛔⭐ PHASE 9 — THE PRICE OF THE USE-AFTER-FREE CURE, AND THE
	 *      CHECK THAT WOULD MAKE IT FALL.
	 *
	 *      It is written ALWAYS, even without video: the bytes held for
	 *      retransmission belong to all the streams, not only to frames.
	 *
	 * ⭐ HOW TO READ IT, and they are two numbers with two different jobs:
	 *
	 *    · the PEAK is the memory price.  It must be in the order of the
	 *      congestion window — tens or hundreds of KB, at worst a
	 *      whole frame (525 KB measured on 23 August) — and with sixteen
	 *      sessions it is multiplied by sixteen.  ⛔ If it grows for the whole
	 *      session instead of oscillating, the cure is HOARDING memory: it is
	 *      exactly the fault that would make it fall.
	 *
	 *    · the RESIDUE at closure must be **zero or nearly**.  If it is not,
	 *      there is a stream that closed without going through
	 *      `wt_stream_chiuso()`, that is the cure's backstop did not hold and
	 *      we bartered a use-after-free for a memory
	 *      leak.  ⚠ A non-zero residue here is NOT a real leak — the
	 *      memory is taken back by `wt_libera()` twenty lines further below — but it is the
	 *      sign that the backstop did not work, and it must be looked at.
	 *
	 * ⭐⭐ AND HOW TO REPRODUCE THE CURED DEFECT, so that the bench can do it
	 *     (`fasi/09-la-qualita-e-la-degradazione.md` §4.5-4.6), on a binary WITHOUT this cure:
	 *
	 *       1. `Environment=MALLOC_MMAP_THRESHOLD_=32768` in the unit.  ⭐
	 *          Setting it from the environment SWITCHES OFF glibc's dynamic adaptation
	 *          (`no_dyn_threshold`): from that moment every block above 32 KiB
	 *          is `mmap`/`munmap` and the defect stops being silent
	 *          FOREVER, not only the first time.  ⛔ Without this line the defect
	 *          hides by itself: after the first big block freed the
	 *          threshold rises and the corruption goes mute again.
	 *       2. a big frame (a film with grain, full screen), and
	 *          packet loss: `tc qdisc add dev X root netem loss 5%`,
	 *          or `kill -STOP` to the browser for one second (no ack ⇒ PTO
	 *          ⇒ retransmission).
	 *       3. prediction on the sick binary: `SEGV`, `error 4`, `ip` inside
	 *          `libc`, in `__memmove_avx_unaligned_erms`.  With
	 *          `-fsanitize=address -g -fno-omit-frame-pointer` there comes out
	 *          `heap-use-after-free READ` with TWO stacks: the one reading (inside
	 *          `ngtcp2_pkt_encode_stream_frame`) and the one that freed.
	 *       4. with this cure, the same bench must hold and this line must
	 *          say residue zero.  ⛔ If it dies all the same, the cure is wrong. */
	registro_dice_di(REG_WT, wt_chi(w),
	                 "⭐ PHASE 9, the bytes HELD for retransmission (contract of "
	                 "ngtcp2_conn_writev_stream): peak %zu bytes, residue at "
	                 "closure %zu, and %zu bytes still to send in the queue",
	                 w->byte_in_volo_max, w->byte_in_volo, w->byte_in_coda);
	/* ⛔⛔ AND CAPTURE IS SWITCHED OFF — OF AUDIO AND OF PIXELS — IF NOBODY
	 *     IS LEFT.
	 *
	 *     `[M]` 17 Aug 2026, first power-on of real audio: the session had
	 *     closed at 07:49:58 — «final count: 397 blocks» — and the child
	 *     at **07:50:10 was still capturing and encoding**, 50 blocks a
	 *     second, for nobody.  ⚠ No error said so: the
	 *     child's summary line said so, which exists on purpose.
	 *
	 * ⛔ Capture and encoding exist only because someone watches or listens.  ⚠ And
	 *    the SINK stays up (I4), like the child: what switches off is the
	 *    monitor's consumption, not the device on which applications play.
	 *
	 * ⛔⭐ AND SINCE 23 SEP 2026 THIS IS NO LONGER THE FIRST OCCASION, IT IS THE LAST.
	 *     The two policies were here in two twin blocks; now they are
	 *     both in `cattura_spegni_se_sola()`, which `regola_battito()`
	 *     already calls at FAREWELL — that is ~30 s before here.  ⇒ One gets here
	 *     only for whoever leaves WITHOUT saying goodbye (`kill -9`, the network dropping, the
	 *     `max_idle_timeout`), and the call is idempotent: if the farewell
	 *     had already done it, this one tells nobody anything.
	 *
	 * ⭐ And it sits AFTER leaving the list of live ones, at the top of this function:
	 *    it is no longer needed — the census excludes `w` by its own name — but
	 *    the order stays that one, and the reason why it was necessary is written
	 *    on the census. */
	cattura_spegni_se_sola(w, "the connection is going away without a farewell");
	/* The test tone's encoder, if this session had one. */
	if (w->tono_cod) {
		/* ⭐ And the ENCODER's counts, which answer a question the
		 *    wire counters do not ask: `RCP.md` §6.3 says the `istante`
		 *    is that of the first sample of the block, and `audio.h` declares that
		 *    Opus «may not produce a packet for every block offered».
		 *    ⛔ If the two things were true together, the instant written on the wire
		 *    would belong to a block different from the one sent.  These two
		 *    numbers say so. */
		uint64_t entrati = 0, usciti = 0;
		audio_cod_conti(w->tono_cod, &entrati, &usciti);
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "audio encoder of %s: %llu blocks in, %llu "
		                 "out%s",
		                 w->provenienza, (unsigned long long)entrati,
		                 (unsigned long long)usciti,
		                 entrati == usciti
		                     ? " — ⭐ one for one: the `istante` of §6.3 belongs "
		                       "to the block that leaves"
		                     : " — ⛔ NOT one for one: the `istante` written on the wire "
		                       "may not be that of the block sent");
		audio_cod_chiudi(w->tono_cod);
		w->tono_cod = NULL;
	}
	/* ⛔ Here there was the twin of the stage switch-off: now it is done by the
	 *    single call above, together with audio.  ⚠ They were two blocks that
	 *    said the same thing in two ways, and one of the two did not go through the
	 *    farewell — which is exactly the defect cured today. */
	if (w->rcp)
		rcp_libera(w->rcp);
	if (w->h3)
		nghttp3_conn_del(w->h3);
	for (size_t i = 0; i < w->ngiudizi; i++)
		bytes_libera(&w->giudizi[i].pref);
	free(w->giudizi);
	for (size_t i = 0; i < w->ncoda; i++)
		bytes_libera(&w->coda[i].dati);
	free(w->coda);
	bytes_libera(&w->capsbuf);
	free(w->richieste);
	free(w);
}

int wt_app_pronta(wt *w) { return apri_http3(w); }

int wt_ricevi_stream(wt *w, uint32_t flags, int64_t stream_id,
                     const uint8_t *dati, size_t len)
{
	bytes riunito = {0};
	nghttp3_ssize nconsumed;
	bool fin = (flags & NGTCP2_STREAM_DATA_FLAG_FIN) != 0;
	int esito = 0;

	if (!w->h3)
		return 0;

	/* ⛔ WebTransport streams are none of nghttp3's business: it would read 0x41
	 *    as an unknown frame type and then the session number
	 *    as a LENGTH, throwing off all the rest.
	 *    ⛔ And the FIN travels with them: §4.2 makes it the end of the session,
	 *       and for a stream we handle ourselves here is the LAST place where it
	 *       can be seen — below we return before `nghttp3_conn_read_stream2`,
	 *       so not even nghttp3 meets it. */
	switch (smista(w, stream_id, dati, len, fin, &riunito)) {
	case E_MIO:
	case E_ATTENDI:
		bytes_libera(&riunito);
		return 0;
	case E_HTTP3:
		break;
	}

	if (riunito.n > 0) {
		dati = riunito.d;
		len = riunito.n;
	}

	nconsumed = nghttp3_conn_read_stream2(w->h3, stream_id, dati, len, fin,
	                                      ngtcp2_conn_get_timestamp(w->conn));
	if (nconsumed < 0) {
		registro_dice_di(REG_WT, wt_chi(w), "⛔ nghttp3_conn_read_stream2: %s",
		                 nghttp3_strerror((int)nconsumed));
		ngtcp2_ccerr_set_application_error(
			w->ultimo_errore,
			nghttp3_err_infer_quic_app_error_code((int)nconsumed), NULL, 0);
		esito = NGTCP2_ERR_CALLBACK_FAILURE;
	} else {
		conta_credito(w, stream_id, (size_t)nconsumed);
	}
	bytes_libera(&riunito);
	return esito;
}

int wt_stream_chiuso(wt *w, int64_t stream_id, uint64_t codice, bool con_codice)
{
	richiesta *r;

	/* ⛔⛔⭐ PHASE 9 — AND HERE THE BYTES HELD FOR RETRANSMISSION ARE FREED.
	 *
	 *      It is the OTHER HALF of the contract of `ngtcp2_conn_writev_stream()`
	 *      («... or the stream is closed»), and `ngtcp2.h` writes it in full
	 *      under `acked_stream_data_offset`: «After stream_close is called for a
	 *      particular stream, conn does not touch data for the closed stream
	 *      again, and application can free all unacknowledged stream data».
	 *
	 * ⛔⛔ AND IT IS THE BACKSTOP THAT DECIDES WHETHER THE CURE IS PROGRESS OR A BARTER.
	 *      Without this line, the last bytes of every stream closed abruptly —
	 *      a `STOP_SENDING`, a reset from the client, a stream that ends before
	 *      the ack arrives — would NEVER receive their acknowledgement: the same
	 *      page of `ngtcp2.h` says that «if a stream is closed prematurely, and
	 *      stream data is still in-flight, this callback function is not called
	 *      for those data».  ⇒ They would stay allocated until the death of the
	 *      connection, and a memory leak in place of a use-after-free
	 *      **is not progress**.
	 *
	 * ⚠ It also holds for the NOT yet sent bytes of that stream, and that is fine:
	 *   the stream is closed, they will never go out again.  Before they were thrown away by
	 *   the next pass, on the `NGTCP2_ERR_STREAM_SHUT_WR` branch of `wt_scrivi()`.
	 *
	 * ⛔ And it sits BEFORE everything else, because twenty lines further below
	 *    `w->sessione` becomes `-1`: afterwards, the identifier to look for in the queue
	 *    would no longer be there — and it is precisely the CONNECT stream that
	 *    `coda_conferma()` leaves on purpose to this function. */
	coda_butta_stream(w, stream_id);

	/* ⛔⭐ `RCP.md` §4.2: the control channel closes, and ITS
	 *     CLOSING IS THE END OF THE SESSION.  The registry slot (§8.2
	 *     reason 0x0F) must be freed HERE — and also when what closes is the
	 *     extended CONNECT stream, which CARRIES the WebTransport session.
	 *
	 * ⚠ In the graft the slot was freed only at the death of the CONNECTION.
	 *   With a test client the two instants coincide, and B3 stayed
	 *   green for five runs.  ⛔ A BROWSER does not: it closes the session and keeps
	 *   the connection alive, and from that moment the slot stays occupied by a
	 *   session that no longer exists — SEVEN `posto NEGATO` out of nine
	 *   attempts, `[M]` B11 with Chrome. */
	if (w->rcp && (stream_id == w->rcp_stream || stream_id == w->sessione)) {
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "closed stream %ld: the session is over, the slot "
		                 "is freed",
		                 (long)stream_id);
		/* ⛔⭐ AND CAPTURE IS SWITCHED OFF NOW, BEFORE `rcp_libera()`, because
		 *     afterwards NOBODY knows the user's name any more: `w->rcp`
		 *     becomes null two lines below, and the block of `wt_libera()`
		 *     demands a non-null `w->rcp`.  ⇒ Before today this road —
		 *     the client properly closing the CONNECT stream — never
		 *     stopped the stage, not even at the death of the connection: the
		 *     child kept capturing until the user logged out.
		 * ⚠ It is not the case of the measured ~30 s (that one goes through `"finita"` and
		 *   the heartbeat): it is a WORSE case that is closed by the same
		 *   line, and it came out while writing it. */
		cattura_spegni_se_sola(w, "the client closed the control channel");
		rcp_libera(w->rcp);
		w->rcp = NULL;
		w->rcp_stream = -1;
		regola_battito(w);
	}
	if (stream_id == w->sessione)
		w->sessione = -1;

	r = richiesta_trova(w, stream_id, false);
	if (r)
		r->usato = false;

	if (!w->h3)
		return 0;
	if (con_codice) {
		int rv = nghttp3_conn_close_stream(w->h3, stream_id, codice);
		if (rv != 0 && rv != NGHTTP3_ERR_STREAM_NOT_FOUND) {
			registro_dice_di(REG_WT, wt_chi(w), "⛔ nghttp3_conn_close_stream: %s",
			                 nghttp3_strerror(rv));
			ngtcp2_ccerr_set_application_error(
				w->ultimo_errore,
				nghttp3_err_infer_quic_app_error_code(rv), NULL, 0);
			return NGTCP2_ERR_CALLBACK_FAILURE;
		}
	}
	return 0;
}

int wt_stream_reset(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_shutdown_stream_read(w->h3, stream_id);
	return 0;
}

int wt_stream_stop_sending(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_shutdown_stream_read(w->h3, stream_id);
	return 0;
}

/* ⛔⛔⭐ PHASE 9 — OUR BYTES FIRST, THEN nghttp3.
 *
 *      This function forwarded to nghttp3 **and that was all**, and it is there that
 *      the whole defect of 23 Aug 2026 shows in two lines: the acknowledgement served
 *      THEM — nghttp3 keeps its buffers until the ack, as the contract of
 *      `ngtcp2_conn_writev_stream()` demands — and not US, because ours we
 *      freed at serialisation.  Two opposite policies for the same
 *      contract, in the same module, on the same call.
 *
 * ⚠ And `!w->h3` no longer returns at once: OUR elements must be confirmed even
 *   when the HTTP/3 layer is not there (or is no longer there), or the last bytes of
 *   a closing session would be freed by nobody. */
int wt_ack_stream_data(wt *w, int64_t stream_id, uint64_t len)
{
	coda_conferma(w, stream_id, len);
	if (!w->h3)
		return 0;
	nghttp3_conn_add_ack_offset(w->h3, stream_id, len);
	return 0;
}

int wt_estendi_max_stream_data(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_unblock_stream(w->h3, stream_id);
	return 0;
}

int wt_estendi_max_streams_bidi(wt *w, uint64_t max_streams)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_set_max_client_streams_bidi(w->h3, max_streams);
	return 0;
}

/* ------------------------------------------------------------------------ */

/* ⛔⭐ §8.1 — «NEVER WITH A SILENCE».  Finding B-7, night of 10 Aug 2026.
 *
 *     `trasporto_congeda_tutte()` calls it when the server shuts down.  The two
 *     roads of §3.1 are walked by `rcp_congeda()`: `CONGEDO(0x0C)` on the
 *     control channel, and the same `0x0C` in the session close code.
 *
 * ⚠ And if the RCP session does not exist yet — a QUIC connection open but without a
 *   control channel — the second road remains, which is precisely the case for
 *   which §3.1 wanted two of them. */
void wt_congeda(wt *w, uint8_t motivo, const char *dettaglio)
{
	if (!w)
		return;
	if (w->rcp && !rcp_e_finita(w->rcp)) {
		rcp_congeda(w->rcp, motivo, dettaglio);
		return;
	}
	if (w->sessione != -1 && w->chiusura < 0) {
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⚠ %s: no live RCP session, reason %#04x "
		                 "travels only in the session close code "
		                 "(§3.1, second road)",
		                 w->provenienza, motivo);
		chiudi_sessione(w, motivo);
	}
}

/* ⭐ PAM'S VERDICT COMING BACK — `DECISIONI.md` §1.10.
 *
 * ⛔ The transport hands it to all live connections and only one takes it:
 *    the request is a PROCESS number, and whoever recognises it is `rcp.c`.  ⚠ And
 *    if nobody takes it that is fine — it means the connection
 *    died while PAM was answering, and there is nobody left to admit. */
bool wt_verdetto(wt *w, uint64_t pratica, bool ammesso, bool ripresa)
{
	if (!w || !w->rcp)
		return false;
	if (!rcp_verdetto(w->rcp, pratica, ammesso,
	                  ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS))
		return false;
	/* ⛔ Only on the connection that took the request: the others have
	 *    nothing to do with it, and the fact belongs to this admission. */
	w->ripresa = ammesso && ripresa;
	return true;
}


/* ⛔⭐ §5.3 — the sign of life that comes from the wire.  A bridge line, and the
 *     reason it exists is on `rcp_segno_di_vita()`.
 *
 * ⚠ It goes through BEFORE the RCP session exists (the QUIC connection is there, the control
 *   channel is not): then there is nothing to note and that is fine — whoever
 *   is not attached yet holds no slot. */
void wt_segno_di_vita(wt *w, ngtcp2_tstamp ts)
{
	if (w && w->rcp)
		rcp_segno_di_vita(w->rcp, ts / NGTCP2_MILLISECONDS);
}

void wt_batti(wt *w, ngtcp2_tstamp ts)
{
	/* ⛔ FIRST of all: `audio_regola()` below enqueues audio blocks, and
	 *    `dgram_accoda()` stamps them with this field.  A stamp one
	 *    heartbeat old would give every block a false age. */
	w->ts_ora = ts;

	if (w->rcp)
		rcp_tempo(w->rcp, ts / NGTCP2_MILLISECONDS);

	/* ⭐ The second of the two roads: `SESSIONE` can leave also from
	 *    `rcp_tempo()` — the fixed delay of §4.4-bis makes it mature here, not
	 *    on arrival of the credentials.  ⛔ With only the call in `rcp_passa`
	 *    the frame would have left only for the sessions that still say
	 *    something afterwards, and on a client that goes quiet after the credentials it would
	 *    never have left. */
	video_regola(w, ts / NGTCP2_MILLISECONDS);
	audio_regola(w);
	tono_passo(w, ts);

	/* ⛔⭐ PHASE 9 — the regulator's once-a-second line, and it runs with the HEARTBEAT
	 *     on purpose: on a still scene frames do not arrive, and a line that
	 *     came out only with frames would leave «the loop was not
	 *     walked» looking the same as «the backlog was zero». */
	ritmo_ciclo(w, ts / NGTCP2_MILLISECONDS);

	/* ⛔⭐ PHASE 9 — and next to the rate one, the NETWORK one: the two
	 *     halves of the same question.  `ritmo_ciclo()` says what WE
	 *     did, `rete_ciclo()` what the LINE did — and they both run
	 *     with the heartbeat, for the same reason: on a still scene frames
	 *     do not arrive, but packets can be lost all the same. */
	rete_ciclo(w, ts / NGTCP2_MILLISECONDS);

	/* ⛔⭐ §4.6 — THE SESSION THAT NEVER OPENS THE CONTROL CHANNEL.
	 *
	 * ✅ `DECISIONI.md` §7.17, 11 Aug 2026: 5 s, then `TEMPO_SCADUTO`.
	 *
	 * ⚠ And the `CONGEDO` is NOT sent: the control channel was never born,
	 *   so there is nowhere to send it.  It is the condition decided the same
	 *   day in §7.15 — «if the channel is still usable» — and here it is
	 *   not.  The reason travels ONLY in the session close code, which
	 *   is the second road of §3.1 point 3.
	 *
	 * ⭐ The two decisions interlock precisely here, and it is the first place in
	 *    which it happens: without §7.15 this line would have to send a byte on a
	 *    channel never born. */
	if (w->canale_entro && ts >= w->canale_entro && w->chiusura < 0) {
		registro_dice_di(REG_RCP, wt_chi(w),
		                 "⛔ %s: WebTransport session open and control "
		                 "channel NEVER opened within %llu ms — farewell "
		                 "%#04x TEMPO_SCADUTO (§4.6, DECISIONI.md §7.17).  "
		                 "⚠ no CONGEDO on the channel: the channel does not exist, "
		                 "the reason travels in the close code (§3.1 point "
		                 "3, and §7.15 allows it)",
		                 w->provenienza,
		                 (unsigned long long)(WT_TETTO_CANALE_NS
		                                      / NGTCP2_MILLISECONDS),
		                 RCP_TEMPO_SCADUTO);
		w->canale_entro = 0;
		chiudi_sessione(w, RCP_TEMPO_SCADUTO);
	}

	/* ⛔ The closing capsule leaves ONLY when the output queue is empty:
	 *    the `CONGEDO` must have already left, or the browser throws it away together
	 *    with the session.  ⚠ And being empty is not enough: «handed to ngtcp2»
	 *    is not «gone out on the wire», so we wait another half second. */
	if (w->chiusura >= 0) {
		/* ⛔ The deadline is looked at BEFORE the queue — finding B-3.  If it
		 *    were looked at after, the «queue not empty» branch would reset
		 *    `chiusura_da` forever and one would never get here: it is
		 *    exactly the defect this line removes. */
		if (w->chiusura_scadenza && ts >= w->chiusura_scadenza) {
			uint8_t m = (uint8_t)w->chiusura;
			registro_dice_di(REG_WT, wt_chi(w),
			                 "⛔ the output queue did not empty in 3 s "
			                 "(%zu elements to send, %zu bytes; and %zu bytes "
			                 "handed to ngtcp2 awaiting acknowledgement): the "
			                 "closing capsule leaves ALL THE SAME with code "
			                 "0x%02x — §3.1 point 3 is the reason that saves the "
			                 "diagnoses, and waiting forever means never "
			                 "executing it",
			                 coda_da_spedire(w), w->byte_in_coda,
			                 w->byte_in_volo, m);
			w->chiusura = -1;
			w->chiusura_da = 0;
			w->chiusura_scadenza = 0;
			chiudi_adesso(w, m);
		} else if (!coda_vuota(w)) {
			w->chiusura_da = 0;
		} else if (w->chiusura_da == 0) {
			w->chiusura_da = ts + WT_ATTESA_CHIUSURA_NS;
		} else if (ts >= w->chiusura_da) {
			uint8_t m = (uint8_t)w->chiusura;
			w->chiusura = -1;
			w->chiusura_da = 0;
			w->chiusura_scadenza = 0;
			chiudi_adesso(w, m);
		}
	}

	regola_battito(w);
	if (w->battito_ms && w->battito <= ts) {
		/* Time has not advanced as much as needed: it is postponed forward anyway,
		 * or the loop would spin idle. */
		w->battito = ts + w->battito_ms * NGTCP2_MILLISECONDS;
	}
}

/* ------------------------------------------------------------------------ */
/* ⭐ Writing: it is here that the two things nghttp3 cannot do get done.     */

ngtcp2_ssize wt_scrivi(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi,
                       uint8_t *dest, size_t destlen, ngtcp2_tstamp ts)
{
	nghttp3_vec vec[16];

	/* ⛔ The session clock: see `wt_batti()`.  ⚠ Here it is needed because a
	 *   write can arrive between one heartbeat and the next. */
	w->ts_ora = ts;

	/* ⭐ A write pass starts here, and the streams all start again
	 *    UNBLOCKED: the list holds for one pass only.  ⚠ It sits outside the loop
	 *    on purpose — resetting it inside would put the same element back in play at
	 *    every round, which is precisely the loop that does not advance. */
	w->nbloccati = 0;
	w->troppi_bloccati = false;

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔⭐ DATAGRAMS BEFORE STREAMS — THAT IS **AUDIO WINS OVER VIDEO**
	 *       WHEN THE WINDOW NARROWS.  IT IS A DECISION, not an order of
	 *       lines: it is here because it is written in no document.
	 * ═══════════════════════════════════════════════════════════════════════
	 *
	 * ⛔ WHAT IT DECIDES.  A write pass has a single `dest` and a single
	 *    congestion window.  Whoever writes first takes them.  This
	 *    line gives first place to DATAGRAMS: if there is even a single audio
	 *    block in the queue, it enters the packet before any byte of
	 *    video, and on a window of two or three packets (`[M]` the user's real
	 *    session: `cwnd` 2 888 - 5 704 bytes) «before» means «instead».
	 *
	 * ⭐ WHY.  The two payloads do not degrade in the same way, and the
	 *    difference is in `RCP.md` §6.3 against §5.1:
	 *      · a late audio block **is of no use to anyone any more** — it is not
	 *        retransmitted, not reordered, and whoever listens has a cushion of
	 *        250 ms and then a hole one HEARS;
	 *      · a late frame is still a frame: streams are
	 *        reliable, the bytes stay in the queue and leave at the next pass, and
	 *        the eye forgives a frame one more step late much more than
	 *        the ear forgives a hole.
	 *    ⇒ Giving precedence to the payload that expires is the only one of the two choices in
	 *      which the delay is paid with something that can still be recovered.
	 *
	 * ⛔ THE DISCARDED ALTERNATIVE, and it was not absurd: **streams first**,
	 *    that is audio travelling in the space video leaves free.
	 *    ⚠ It is exactly what the `MORE` flag does inside
	 *    `dgram_scrivi_uno()`, and there it works; but as an ORDER it was tried and
	 *    has a measurement against it: `[M]` 17 Aug 2026, the user's real session,
	 *    **1 578 blocks sent and 1 606 refused** with `cwnd_left = 0` — more
	 *    than half of the audio did not leave, because video took the
	 *    whole window and audio was left without a packet of its own.
	 *    ⚠ The third road — a fixed quota for each — was discarded
	 *      without measuring it: it would be a number to tune per scene, and §6.3
	 *      gives no criterion for choosing it.
	 *
	 * ⚠ THE PRICE, AND IT IS NOT THEORETICAL: it is bandwidth taken from video precisely when there
	 *   is little.  ⭐ But it is BOUNDED by construction — the datagram queue is
	 *   eight long, so at most eight packets go ahead, then
	 *   `w->ndgram` is zero and we go on with the streams.
	 *
	 * ⭐⭐ AND HOW MUCH THIS PRECEDENCE WEIGHS DEPENDS ON WHAT HAPPENS ON THE SCREEN,
	 *     `[M]`:
	 *       · STILL desktop — the wire is **all audio**: 48.0 datagrams out of 48.4
	 *         packets a second (`09-b84`, 24 Aug 2026, silence cure
	 *         off).  ⇒ There is no video to take anything from;
	 *       · REAL session in motion — audio is between **25 and 33 %**
	 *         of the packets.  ⇒ A good two thirds of the window stay with video
	 *         even in the worst case.
	 *     ⚠ The first number is also the reason why audio silence
	 *       (`audio.c`) became a default: the precedence costs little
	 *       as long as audio does not speak to say nothing. */
	{
		ngtcp2_ssize ndg = 0;
		if (dgram_scrivi_uno(w, path, pi, dest, destlen, ts, &ndg))
			return ndg;
	}

	for (;;) {
		int64_t stream_id = -1;
		int fin = 0;
		nghttp3_ssize sveccnt = 0;
		nghttp3_vec wtvec[1];
		size_t wt_orig = 0;
		bool wt_mio = false;
		size_t mio_i = 0;
		ngtcp2_ssize ndatalen = -1, nwrite;
		const nghttp3_vec *v;
		size_t vcnt;
		uint32_t flags;

		/* ⭐ If the rewriting of the settings has lost count, we
		 *    stop: a control stream out of step is worse than a
		 *    closed connection.  ⚠ It is NOT the case of the PARTIAL
		 *    write, which is a normal outcome and is resumed later. */
		if (w->guasto)
			return NGTCP2_ERR_CALLBACK_FAILURE;

		if (w->h3 && ngtcp2_conn_get_max_data_left2(w->conn)) {
			sveccnt = nghttp3_conn_writev_stream(w->h3, &stream_id, &fin,
			                                     vec, 16);
			if (sveccnt < 0) {
				registro_dice_di(REG_WT, wt_chi(w), "⛔ nghttp3_conn_writev_stream: %s",
				                 nghttp3_strerror((int)sveccnt));
				ngtcp2_ccerr_set_application_error(
					w->ultimo_errore,
					nghttp3_err_infer_quic_app_error_code((int)sveccnt),
					NULL, 0);
				return NGTCP2_ERR_CALLBACK_FAILURE;
			}
		}

		/* ── 1. the settings ────────────────────────────────────────── */
		if (sveccnt > 0 && stream_id == w->ctrl_id && !w->impostazioni_scritte) {
			/* ⛔ The rewriting is done ONCE ONLY.  If the previous pass
			 *    sent only a piece of it, nghttp3 offers us
			 *    the same bytes again — we have not yet told it we
			 *    consumed them — and recomposing the buffer from scratch
			 *    would resend the piece already gone out. */
			if (w->impbuf_off == 0)
				w->impbuf_orig =
					riscrivi_impostazioni(w, vec, (size_t)sveccnt);
			wt_orig = w->impbuf_orig;
		}

		/* ── 2. our own queue ───────────────────────────────────────── */
		/* ⛔ `coda_scegli()` and not «the head»: the head can belong to a
		 *    blocked stream, and stopping there would redo the head-of-line blocking that
		 *    §5.1 exists to remove. */
		if (sveccnt <= 0 && !w->troppi_bloccati) {
			uscita *u = coda_scegli(w, &mio_i);
			if (u) {
				stream_id = u->id;
				fin = u->fin ? 1 : 0;
				wtvec[0].base = u->dati.d + u->off;
				wtvec[0].len = u->dati.n - u->off;
				wt_mio = true;
			}
		}

		v = vec;
		vcnt = (size_t)(sveccnt > 0 ? sveccnt : 0);

		if (wt_orig) {
			/* ⭐ PHASE 9 — and not even here is the defect of 23 August present:
			 *    `impbuf` is a FIXED array inside `wt` (256 bytes), written
			 *    ONCE ONLY (`impostazioni_scritte`) and alive as long as the
			 *    connection.  ⛔ If one day the settings were
			 *    rewritten, rewriting it while ngtcp2 still holds this
			 *    pointer would be the same silent corruption. */
			wtvec[0].base = w->impbuf + w->impbuf_off;
			wtvec[0].len = w->impbuf_len - w->impbuf_off;
			v = wtvec;
			vcnt = 1;
		} else if (wt_mio) {
			v = wtvec;
			vcnt = 1;
		}

		flags = NGTCP2_WRITE_STREAM_FLAG_MORE |
		        NGTCP2_WRITE_STREAM_FLAG_PADDING;
		if (fin)
			flags |= NGTCP2_WRITE_STREAM_FLAG_FIN;

		nwrite = ngtcp2_conn_writev_stream(w->conn, path, pi, dest, destlen,
		                                   &ndatalen, flags, stream_id,
		                                   (const ngtcp2_vec *)v, vcnt, ts);
		if (nwrite < 0) {
			switch (nwrite) {
			case NGTCP2_ERR_STREAM_DATA_BLOCKED:
				/* ⛔⭐ AND THE BYTES ARE NOT THROWN AWAY: THIS IS A RELIABLE
				 *     CHANNEL.  In the graft here the WHOLE element
				 *     was discarded — including the case in which a
				 *     part had already gone out on the wire: the next message
				 *     was welded to those truncated bytes and the client read
				 *     an invented `tipo`/`lunghezza`.  ⛔ It was the
				 *     SERVER fabricating the client's violation.
				 *
				 * ⚠ And STREAM_DATA_BLOCKED is not a fault: it is the
				 *   normal and transient condition that dissolves with the
				 *   first MAX_STREAM_DATA. */
				if (wt_mio) {
					uscita *u = &w->coda[mio_i];
					registro_dettaglio(
						REG_WT,
						"stream %ld blocked: %zu bytes STAY in the "
						"queue (%zu already gone out) — ⭐ the OTHER streams "
						"go on (§5.1)",
						(long)stream_id, u->dati.n - u->off, u->off);
					/* ⛔⭐ THE STREAM IS BLOCKED, NOT THE QUEUE — and it is the
					 *     cure of point 5 of phase 3.  Until phase 2
					 *     here `coda_bloccata` was raised, which stopped
					 *     THE WHOLE queue for the pass: a slow
					 *     frame at the head blocked the following ones **at
					 *     application level**, cancelling exactly the
					 *     benefit §5.1 buys at the QUIC level. */
					if (w->nbloccati < WT_BLOCCATI_MAX) {
						w->bloccati[w->nbloccati++] = stream_id;
					} else {
						/* ⚠ The cap is declared instead of slipping by:
						 *   from here on the pass really stops, and
						 *   whoever reads knows it is not §5.1 that does not
						 *   work, it is this table that is
						 *   full. */
						w->troppi_bloccati = true;
						registro_dice_di(REG_WT, wt_chi(w),
						                 "⚠ %u streams blocked in the same "
						                 "pass: the queue stops here.  It is "
						                 "not §5.1 that does not hold, it is the cap "
						                 "of WT_BLOCCATI_MAX",
						                 WT_BLOCCATI_MAX);
					}
					continue;
				}
				nghttp3_conn_block_stream(w->h3, stream_id);
				continue;
			case NGTCP2_ERR_STREAM_SHUT_WR:
				if (wt_mio) {
					/* The stream is already closed for writing — normally
					 * because WE RESET it (§5.1): the bytes that
					 * remained do not leave, which is what was wanted. */
					coda_uccidi(w, mio_i);
					continue;
				}
				nghttp3_conn_shutdown_stream_write(w->h3, stream_id);
				continue;
			case NGTCP2_ERR_WRITE_MORE:
				break;
			default:
				registro_dice_di(REG_WT, wt_chi(w), "⛔ ngtcp2_conn_writev_stream: %s",
				                 ngtcp2_strerror((int)nwrite));
				ngtcp2_ccerr_set_liberr(w->ultimo_errore, (int)nwrite,
				                        NULL, 0);
				return NGTCP2_ERR_CALLBACK_FAILURE;
			}
		}

		if (nwrite == NGTCP2_ERR_WRITE_MORE || ndatalen >= 0) {
			/* How many bytes OF NGHTTP3 have been consumed.  If its
			 * buffer was replaced, the number ngtcp2
			 * returns is OURS, and telling it would throw off its
			 * counts. */
			if (wt_mio) {
				uscita *u = &w->coda[mio_i];
				u->off += (size_t)ndatalen;
				if (u->off >= u->dati.n) {
					/* ⛔⭐ `RCP.md` §4.2: the control channel
					 *     closing is the end of the session,
					 *     ALSO on our side.  The slot must be
					 *     given up HERE, because from now on no
					 *     byte will arrive that frees it. */
					if (u->fin && w->rcp &&
					    (u->id == w->rcp_stream || u->id == w->sessione))
						rcp_canale_chiuso(w->rcp);
					/* ⛔⛔⭐ PHASE 9 — HERE THERE WAS `coda_uccidi()`, AND IT IS THE LINE
					 *      THAT KILLED THE SERVER ON 23 AUG 2026 at
					 *      08:28:09.
					 *
					 *      `ndatalen` says how many bytes ended up **in a
					 *      packet**, not how many were **confirmed**.
					 *      Freeing them here is freeing them while ngtcp2 still holds
					 *      our pointer for a possible
					 *      retransmission: `fasi/09-la-qualita-e-la-degradazione.md` §4.2 follows the
					 *      chain line by line down to the `ngtcp2_cpymem()` that
					 *      rereads the freed source.
					 *
					 * ⭐ Now it is only HANDED OVER: the element leaves the
					 *    choice and the backlog, the bytes stay.  Freeing them
					 *    is the job of the ack (`coda_conferma()`) or of the closure of the
					 *    stream (`wt_stream_chiuso()`) — the only two conditions
					 *    ngtcp2's contract admits. */
					coda_consegna(w, mio_i);
				}
			} else if (wt_orig) {
				uint64_t c = (uint64_t)ndatalen;
				/* ⛔⭐ AND A PARTIAL WRITE IS NOT A FAULT.
				 *
				 *    `ndatalen` smaller than the length offered is a
				 *    NORMAL outcome: what fits in the packet goes into the
				 *    stream frame.  The ~24 bytes of the rewritten
				 *    SETTINGS travel in the first flight after the
				 *    handshake, the one that also carries
				 *    HANDSHAKE_DONE and the NEW_CONNECTION_IDs: in there
				 *    24 bytes may not fit.
				 *
				 * ⛔ In the graft here THE CONNECTION DIED, while
				 *    ten lines further up our own queue handled the same
				 *    partial write with `off`.  Two
				 *    opposite policies for the same outcome, in the
				 *    same module. */
				if (c > w->impbuf_len - w->impbuf_off) {
					registro_dice_di(REG_WT, wt_chi(w),
					                 "⛔ settings, impossible count "
					                 "(%llu taken out of %zu offered)",
					                 (unsigned long long)c,
					                 w->impbuf_len - w->impbuf_off);
					w->guasto = true;
					return NGTCP2_ERR_CALLBACK_FAILURE;
				}
				w->impbuf_off += (size_t)c;
				if (w->impbuf_off < w->impbuf_len) {
					registro_dettaglio(
						REG_WT,
						"settings, %zu bytes out of %zu — the rest "
						"at the next pass",
						w->impbuf_off, w->impbuf_len);
				} else {
					w->impostazioni_scritte = true;
					if (nghttp3_conn_add_write_offset(
						    w->h3, stream_id, w->impbuf_orig) != 0) {
						w->guasto = true;
						return NGTCP2_ERR_CALLBACK_FAILURE;
					}
				}
			} else if (stream_id >= 0) {
				int rv = nghttp3_conn_add_write_offset(w->h3, stream_id,
				                                       (uint64_t)ndatalen);
				if (rv != 0) {
					registro_dice_di(REG_WT, wt_chi(w),
					                 "⛔ nghttp3_conn_add_write_offset: %s",
					                 nghttp3_strerror(rv));
					ngtcp2_ccerr_set_application_error(
						w->ultimo_errore,
						nghttp3_err_infer_quic_app_error_code(rv), NULL,
						0);
					return NGTCP2_ERR_CALLBACK_FAILURE;
				}
			}
		}

		if (nwrite == NGTCP2_ERR_WRITE_MORE)
			continue;

		return nwrite;
	}
}
