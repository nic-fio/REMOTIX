/* 01-b8-prova-ban.c — the three pieces of the ban that go wrong most easily, and
 * that no test on the wire can see by itself.
 *
 *   gcc -std=c11 -Wall -Wextra -Ibanchi/rcp -o /tmp/pb \
 *       banchi/01-b8-prova-ban.c banchi/rcp/rcp.c && /tmp/pb
 *
 * ⛔ It is the CERTIFICATION of a part of B8 (`LEZIONI.md` §1.2): three properties
 *    that on the wire would be seen only by waiting twelve hours, rebooting a
 *    machine, or breaking the permissions of a file run by root — where root
 *    ignores permissions.
 *
 * The FOUR parts, and why each one is here:
 *
 *   1. the conversion between the server's MONOTONIC clock and the ABSOLUTE time
 *      that ends up on disk.  On the wire it would be seen only twelve hours later;
 *   2. ⛔ «zero bans» and «I could not read the file» — `LEZIONI.md` §1.9
 *      rule 1.  The bench on the wire runs as ROOT inside the container, and for
 *      root a file with permissions 000 is readable: that check there would be
 *      green by construction, and it would be the emptiest of all;
 *   3. ⛔ the ban KEY carries square brackets — `[127.0.0.1]` — because the
 *      host's `util::straddr()` puts them on IPv4 too.  Whoever types
 *      `127.0.0.1` at the unblock command must arrive at the same place, or the
 *      command answers «it was not banned» to every address, forever and without
 *      any symptom.
 *   4. ⛔ that the unblock RESETS THE COUNT even when there was no ban
 *      (section 5).  It is the line the whole sampling strategy of B8 rests on —
 *      «unblock between one block and the next» — and it was **written and never
 *      measured** in two files (finding A22).  On the wire it would cost consuming
 *      the §4.4-bis count of the whole machine (B0.3) to test one line.
 *
 * ⛔ And every part carries its check that says NO: without it, «the ban is there»
 *    is satisfied also by a guard that always says yes.
 *
 * ⛔ AND THE EXIT STATUS HAS FIVE VALUES, not two:
 *      0  green — and the verdict says on how many things
 *      1  red — at least one check failed
 *      2  ⛔ no outcome: zero checks run
 *      3  ⛔ the run did not get to the end (sections or checks missing)
 *      4  ⛔ early exit: the verdict was not given at all                  */
#include "rcp.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

/* ⛔ THREE COUNTERS, NOT ONE — finding A20 of review R12-A, 11 Aug 2026.
 *
 * Until tonight there was **only one** here, `test_failures`, and the verdict at
 * the bottom was `printf("%s: %d checks failed")`: zero denominator.  It was
 * enough to have a `return 0;` after section 1 — or an `#if 0` around sections
 * 2-4, or a wrong `#include` that made a block be skipped — for the output to
 * end with **«VERDE: 0 checks failed»** and exit status 0.
 *
 * ⛔ It is the green on an empty set of `LEZIONI.md` §1.9 rule 6 — *«all those
 *    tested went well» is true even when the tested are zero* — inside the file
 *    that certifies the ban, and under the comment of this very file that
 *    declares it prints the denominator of every section.
 *
 * ⭐ The cure is that of the rule: **a verdict too has a denominator, and it is
 *    how many things it approved**.  Here three are counted — checks passed,
 *    checks run, sections that got to the end — and at the bottom they are
 *    required to be the expected ones, which is the only form a stray
 *    `return 0;` cannot satisfy.                                             */
static int test_failures = 0;
static int passed_test = 0;
static int test_sections = 0;

static void demands(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed_test++;
	else
		test_failures++;
}

/* ⚠ The denominator of every section is printed: how many checks, and on what.
 *   A list of OKs without the number of what it looked at is not a
 *   measurement (`LEZIONI.md` §1.9 rule 4). */
static void section(const char *heading)
{
	test_sections++;
	printf("\n  == [section %d] %s\n", test_sections, heading);
}

/* ⛔ AND THE HALF OF FINDING A20 THAT NO COUNTER CAN CATCH.
 *
 * The three counters above see an `#if 0` around a block, a wrong `#include`, a
 * section that does not get to the end: the verdict runs anyway and finds the
 * small numbers.  ⛔ But a `return 0;` put in the middle of `main` **skips the
 * verdict together with the rest**, and a program that exits without saying
 * anything exits **0** — that is the concrete case the finding names first
 * would stay green.
 *
 * ⭐ The cure is the only one that does not depend on where someone puts a
 *    `return`: the process's exit goes through here **always**, and if the
 *    verdict was not given the exit status is not zero.  «I did not conclude»
 *    and «I concluded that it is fine» are two different facts, and it is the
 *    same rule of §1.9 applied to the exit status instead of to a count.     */
static bool verdict_given = false;
static void on_farewell(void)
{
	if (verdict_given)
		return;
	fprintf(stderr,
	        "\n  ⛔ EARLY EXIT: this program ended WITHOUT giving a "
	        "verdict.\n     It ran %d checks in %d sections and "
	        "concluded nothing:\n     «I did not conclude» is not «everything "
	        "went well».\n",
	        passed_test + test_failures, test_sections);
	fflush(NULL);
	_exit(4);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔ THE FAKE HOST — it serves section 5, and nothing else.
 *
 * `rcp.h` puts the verification of the credentials among the **hooks**, «so
 * that a bench can replace it, declaring it».  It is the only way to make the
 * §4.4-bis counter go up from here: without a real session the count does not
 * move, and without the count section 5 has nothing to measure.
 * ═══════════════════════════════════════════════════════════════════════════ */
enum { T_HELLO = 0x0001, T_HERE_I_AM = 0x0002, T_CREDENTIALS = 0x0003,
       T_ADMITTED = 0x0004, T_REJECTED = 0x0005 };

struct guest {
	int here_i_am;      /* how many HERE_I_AM went out */
	int admitted;     /* how many ADMITTED */
	int rejected;    /* how many REJECTED */
	uint8_t motivo;  /* the reason of the last REJECTED */
};

static void o_send(void *ctx, const uint8_t *data_v, size_t len)
{
	struct guest *o = ctx;
	if (len < 6)
		return;
	uint16_t kind = (uint16_t)((data_v[0] << 8) | data_v[1]);
	if (kind == T_HERE_I_AM)
		o->here_i_am++;
	else if (kind == T_ADMITTED)
		o->admitted++;
	else if (kind == T_REJECTED) {
		o->rejected++;
		o->motivo = len > 6 ? data_v[6] : 0;
	}
}
static void o_close(void *ctx, uint8_t motivo) { (void)ctx; (void)motivo; }
static void o_log(void *ctx, const char *row) { (void)ctx; (void)row; }
/* ⚠ The right password is only one, and it is declared: this way «wrong» and
 *   «right» are two cases and not two names of the same thing. */
static bool o_verify(void *ctx, const char *username, const char *password)
{
	(void)ctx;
	(void)username;
	return strcmp(password, "parola-giusta") == 0;
}

static size_t put_str(uint8_t *b, size_t i, const char *t)
{
	size_t n = strlen(t);
	b[i++] = (uint8_t)(n >> 8);
	b[i++] = (uint8_t)(n & 0xFF);
	memcpy(b + i, t, n);
	return i + n;
}

static size_t wrap(uint8_t *b, uint16_t kind, const uint8_t *body_el, size_t len)
{
	b[0] = (uint8_t)(kind >> 8);
	b[1] = (uint8_t)(kind & 0xFF);
	b[2] = (uint8_t)((len >> 24) & 0xFF);
	b[3] = (uint8_t)((len >> 16) & 0xFF);
	b[4] = (uint8_t)((len >> 8) & 0xFF);
	b[5] = (uint8_t)(len & 0xFF);
	memcpy(b + 6, body_el, len);
	return 6 + len;
}

/* A whole attempt from `provenance`, with `password`.  Returns:
 *   0x00  ADMITTED
 *   0x07  REJECTED WRONG_CREDENTIALS
 *   0x08  REJECTED TOO_MANY_ATTEMPTS
 *   0xFF  ⛔ no answer arrived — and it is NOT a refusal.  */
static uint8_t attempt(const char *provenance, uint64_t now,
                            const char *password)
{
	static const char *const ENTRIES[] = {
	    "video.codec", "hevc,av1", "video.bit_depth", "8,10",
	    "audio.codec", "opus,pcm", "video.level", "5.1",
	    "video.max_size", "3840x2160", "clipboard_text.body_text", "si",
	    "input.tap", "no", "client.label_name", "01-b8-prova-ban", NULL};
	struct guest o = {0, 0, 0, 0};
	rcp_hooks g = {&o, o_send, o_close, o_log, o_verify};
	rcp_session *s = rcp_open(&g, provenance, now);
	if (!s)
		return 0xFF;

	uint8_t body_el[1024], frame[1100];
	size_t i = 0;
	body_el[i++] = 0;
	body_el[i++] = 1;           /* version 1 */
	int how_many_n = 0;
	for (int k = 0; ENTRIES[k]; k += 2)
		how_many_n++;
	body_el[i++] = (uint8_t)(how_many_n >> 8);
	body_el[i++] = (uint8_t)(how_many_n & 0xFF);
	for (int k = 0; ENTRIES[k]; k += 2) {
		i = put_str(body_el, i, ENTRIES[k]);
		i = put_str(body_el, i, ENTRIES[k + 1]);
	}
	size_t n = wrap(frame, T_HELLO, body_el, i);
	rcp_receive(s, frame, n, now);
	if (o.here_i_am != 1) {
		rcp_free(s);
		return 0xFF;         /* ⛔ without HERE_I_AM the attempt did not happen */
	}

	i = put_str(body_el, 0, "utente-di-prova");
	i = put_str(body_el, i, password);
	n = wrap(frame, T_CREDENTIALS, body_el, i);
	rcp_receive(s, frame, n, now);
	/* ⛔ The fixed second of §4.4-bis: time arrives from outside (`rcp.h`), and
	 *    without making it flow the verdict never comes out. */
	rcp_time(s, now + 1500);
	uint8_t outcome = 0xFF;
	if (o.admitted)
		outcome = 0x00;
	else if (o.rejected)
		outcome = o.motivo;
	rcp_free(s);
	return outcome;
}

int main(void)
{
	/* ⛔ Before anything else: the exit hook that refuses to exit zero without
	 *    a verdict (see `on_farewell`). */
	atexit(on_farewell);
	const uint64_t NOW = 1000000; /* any monotonic clock */
	const char *f = "/tmp/remotix-b8-ban.txt";
	time_t clock = time(NULL);

	/* ═══ 1. the absolute time on disk, and the monotonic time in memory ═════ */
	section("1. the ban file: absolute time on disk, monotonic in memory");
	FILE *w = fopen(f, "w");
	/* ⛔ The brackets are there because they are there in the real key:
	 *    `util::straddr()` writes `[1.2.3.4]:44661`, and the ban file receives
	 *    what `solo_indirizzo()` leaves of it.  Writing `1.2.3.4` here would
	 *    test a form the server never produces. */
	fprintf(w, "[1.2.3.4] %lld\n", (long long)clock + 3600); /* in an hour */
	fprintf(w, "[9.9.9.9] %lld\n", (long long)clock - 10);   /* already expired */
	fclose(w);

	int how_many = rcp_ban_load(f, NOW);
	printf("  loaded: %d  (lines in the file: 2, of which 1 already expired)\n", how_many);
	demands(how_many == 1, "loads ONE line only: the expired one is discarded");

	uint64_t remain = 0;
	demands(rcp_banned("[1.2.3.4]:44661", NOW, &remain),
	      "the banned address is banned — and the PORT does not confuse it");
	printf("  remaining: %llu ms (expected ~3600000)\n",
	       (unsigned long long)remain);
	demands(remain > 3590000 && remain <= 3600000,
	      "the absolute expiry came back monotonic without drift");

	demands(!rcp_banned("[9.9.9.9]:1", NOW, NULL),
	      "⛔ the check that says NO: the expired line was not loaded");
	demands(!rcp_banned("[5.5.5.5]:1", NOW, NULL),
	      "⛔ and an address never seen is not banned (the guard does not invent)");

	/* Twelve hours later, the same ban is over by itself. */
	demands(!rcp_banned("[1.2.3.4]:44661", NOW + 43200000u, NULL),
	      "the ban expires by itself as time passes");

	/* ═══ 2. the ban key, and the four forms in which it arrives ════════════ */
	section("2. ⛔ the KEY carries brackets, and whoever commands types without them");
	{
		struct {
			const char *given;
			const char *expected_val;
		} cases[] = {
		    {"127.0.0.1", "[127.0.0.1]"},
		    {"127.0.0.1:53", "[127.0.0.1]"},
		    {"[127.0.0.1]", "[127.0.0.1]"},
		    {"[127.0.0.1]:55680", "[127.0.0.1]"},
		    {"fe80::1", "[fe80::1]"},
		    {"[fe80::1]:44661", "[fe80::1]"},
		};
		int n = (int)(sizeof cases / sizeof cases[0]);
		printf("  forms tested: %d\n", n);
		for (int i = 0; i < n; i++) {
			char key_id[64];
			rcp_key_address(cases[i].given, key_id, sizeof key_id);
			char desc[160];
			snprintf(desc, sizeof desc, "«%s» → «%s» (expected «%s»)", cases[i].given,
			         key_id, cases[i].expected_val);
			demands(strcmp(key_id, cases[i].expected_val) == 0, desc);
		}
		/* ⛔ And the check that says NO: two DIFFERENT addresses must not end
		 *    up on the same key, or the ban of one would lock out the other
		 *    and no bench would see it. */
		char a[64], b[64];
		rcp_key_address("127.0.0.1", a, sizeof a);
		rcp_key_address("127.0.0.2", b, sizeof b);
		demands(strcmp(a, b) != 0,
		      "⛔ the check that says NO: two different addresses give two "
		      "different keys");
	}

	/* ═══ 3. the unblock, and its TWO answers ════════════════════════════ */
	section("3. the unblock command: «it was not banned» and «I removed it»");
	/* ⛔ It is called with the form A PERSON TYPES — without brackets — which is
	 *    the real case: if this line used `[1.2.3.4]` it would test the road no
	 *    human being travels, and the command would stay broken for everyone
	 *    else.  It is the certification of the certification. */
	{
		char key_id[64];
		rcp_key_address("1.2.3.4", key_id, sizeof key_id);
		demands(rcp_unblock(key_id, NOW),
		      "the unblock says TRUE on a really banned address — and "
		      "the address had been typed WITHOUT the brackets");
		demands(!rcp_banned("[1.2.3.4]:44661", NOW, NULL),
		      "and afterwards it is no longer banned");
		demands(!rcp_unblock(key_id, NOW),
		      "⛔ and unblocking twice says FALSE: «it was not there» and «I removed it» are "
		      "two different facts");
	}

	/* ⛔ AND THE SAME WITH AN IPv6 ADDRESS, which is the only form in which the
	 *    defect shows.  ⚠ This test was born from the CERTIFICATION of this file:
	 *    putting back by hand the old `solo_indirizzo()` — the one that always
	 *    cut at the last colon — the bench stayed GREEN, because with IPv4
	 *    `[1.2.3.4]` has no colon to cut.  The defect lived entirely in
	 *    `[fe80::1]`, which that cut reduced to `[fe80:`, and no check went
	 *    through it.  ⛔ A bench that does not turn red when the defect comes back
	 *    is not a proof of correctness (`LEZIONI.md` §1.3). */
	{
		rcp_reset_session_log();
		FILE *s = fopen(f, "w");
		fprintf(s, "[fe80::1] %lld\n", (long long)clock + 3600);
		fclose(s);
		int n6 = rcp_ban_load(f, NOW);
		printf("  IPv6 bans loaded: %d (expected 1)\n", n6);
		demands(n6 == 1, "an IPv6 ban is read back from the file");
		demands(rcp_banned("[fe80::1]:44661", NOW, NULL),
		      "and with the port on it it is banned (it is the session's form)");
		char key6[64];
		rcp_key_address("fe80::1", key6, sizeof key6);
		demands(rcp_unblock(key6, NOW),
		      "⛔ and the unblock FINDS it even without a port: «[fe80::1]» is not "
		      "cut at the last colon, or it would become «[fe80:»");
		demands(!rcp_banned("[fe80::1]:44661", NOW, NULL),
		      "and afterwards the IPv6 is no longer banned");
	}

	/* ⛔ And the unblock ended up on DISK, not only in memory: if it stayed in
	 *    memory, the restart would put back the ban someone removed. */
	{
		FILE *r = fopen(f, "r");
		char row[128];
		int line_list = 0;
		while (fgets(row, sizeof row, r))
			line_list++;
		fclose(r);
		demands(line_list == 0,
		      "the unblock was written to the file, not only in memory");
	}

	/* ═══ 4. ⛔ «zero bans» and «I could not read» ════════════════════════ */
	section("4. ⛔ zero bans and «I could not look» — LEZIONI.md §1.9");
	{
		rcp_reset_session_log();
		/* a. the file is not there yet: zero, and it is NOT an error */
		const char *never = "/tmp/remotix-b8-ban-che-non-esiste.txt";
		unlink(never);
		int r = rcp_ban_load(never, NOW);
		printf("  missing file         → %d (expected 0)\n", r);
		demands(r == 0, "a file that does not exist yet counts as ZERO bans, not an error");

		/* b. the file is there and empty: zero, and I read it */
		const char *blank = "/tmp/remotix-b8-ban-vuoto.txt";
		FILE *v = fopen(blank, "w");
		fclose(v);
		r = rcp_ban_load(blank, NOW);
		printf("  empty file           → %d (expected 0)\n", r);
		demands(r == 0, "an empty file counts as ZERO bans");

		/* c. ⛔ the file is there and CANNOT be read: -1, never 0.
		 *    ⚠ With permissions at 000 this test is true only for a normal
		 *      user: as root it would be green by construction, and it is the
		 *      reason this check CANNOT be in the bench on the wire, which runs
		 *      as root inside the container. */
		const char *closed = "/tmp/remotix-b8-ban-chiuso.txt";
		FILE *c = fopen(closed, "w");
		fprintf(c, "[7.7.7.7] %lld\n", (long long)clock + 3600);
		fclose(c);
		chmod(closed, 0);
		errno = 0;
		r = rcp_ban_load(closed, NOW);
		int da_root = (geteuid() == 0);
		printf("  file without perms   → %d (expected %s)%s\n", r,
		       da_root ? "1, because you run as ROOT" : "-1",
		       da_root ? "  ⚠ as root permissions stop nobody: this "
		                 "check was NOT run"
		               : "");
		if (da_root) {
			printf("    ??  ⛔ SKIPPED: run this test again as a normal "
			       "user, or it proves nothing\n");
			test_failures++; /* ⛔ a skipped check is not a passed check */
		} else {
			demands(r == -1,
			      "⛔ a file that is there and cannot be read counts as -1, NOT zero: «empty» "
			      "and «forbidden» must not have the same face");
			demands(!rcp_banned("[7.7.7.7]:1", NOW, NULL),
			      "⛔ and the check that says NO: from an unreadable file no "
			      "invented ban comes out");
		}
		chmod(closed, 0600);
		unlink(closed);

		/* d. and a path whose parent is not a directory: -1 */
		const char *wrong = "/tmp/remotix-b8-ban-vuoto.txt/dentro.txt";
		r = rcp_ban_load(wrong, NOW);
		printf("  impossible path      → %d (expected -1)\n", r);
		demands(r == -1,
		      "⛔ and a path that cannot even be opened counts as -1: "
		      "ENOTDIR is not «no ban»");

		unlink(blank);
		/* ⚠ And persistence is switched off before leaving: `rcp_ban_load()`
		 *   remembers the path EVEN when it fails, and the first following ban
		 *   would try to write there. */
		rcp_ban_load(NULL, NOW);
	}

	/* ═══ 5. ⛔ THE UNBLOCK RESETS THE COUNT EVEN WHEN THERE WAS NO BAN ═══ */
	/* ⛔ Finding A22, 11 Aug 2026.  `01-b8-sblocca.py` prints, on
	 *    `NOT-BANNED`, *«and the attempt count of that address restarts from
	 *    zero anyway»*, and `simulate()` of `01-b8-cronometro.py` models the
	 *    unblock as `failed[addr] = 0` **always**.  ⛔ Neither of the two
	 *    verified it, and the WHOLE sampling strategy of B8 rests on that
	 *    behaviour: «unblock between one block and the next».  If `rcp_unblock()`
	 *    reset the entry **only when a ban is there**, the failures would pile up
	 *    between the blocks and the samples would start coming back
	 *    `limiter` — that is the bench would measure the ban believing it is
	 *    measuring PAM.
	 *
	 * ⚠ And it is measured HERE and not on the wire for the usual reason: on the
	 *   wire three real failed authentications would be needed, that is consuming
	 *   the §4.4-bis count of the whole machine (B0.3) to test one line.
	 *
	 * ⛔ And every check has its check that says NO, or «the ban did not
	 *    trigger» would be satisfied also by a module that does not count.     */
	section("5. ⛔ the unblock resets the count even on a NOT banned address");
	{
		rcp_reset_session_log();
		const uint64_t T = 5000000;

		/* ⭐ THE POSITIVE CONTROL OF THE TOOL, FIRST OF ALL: if the fake host
		 *    could not bring an attempt to the end, every «the ban did not
		 *    trigger» that follows would mean «I measured nothing»
		 *    (`REVIEWER.md` §1 question 5). */
		demands(attempt("[10.0.0.1]:1", T, "parola-giusta") == 0x00,
		      "⭐ positive control: an attempt with the RIGHT password gets "
		      "to ADMITTED — the tool can make happen what counts");
		demands(attempt("[10.0.0.1]:2", T, "wrong") == RCP_WRONG_CREDENTIALS,
		      "⭐ and one with the wrong password gets to WRONG_CREDENTIALS: "
		      "the tool can also produce the failures that count");

		/* a. the check that says NO: without unblock, three failures ban */
		rcp_reset_session_log();
		for (int k = 0; k < 3; k++)
			attempt("[10.0.0.2]:9", T, "wrong");
		demands(attempt("[10.0.0.2]:9", T, "parola-giusta")
		          == RCP_TOO_MANY_ATTEMPTS,
		      "⛔ the check that says NO: WITHOUT unblock, three failures "
		      "ban and the fourth — with the RIGHT password — is TOO_MANY_ATTEMPTS");

		/* b. two failures, then the unblock on a NOT banned address */
		rcp_reset_session_log();
		char key_id[64];
		rcp_key_address("10.0.0.3", key_id, sizeof key_id);
		for (int k = 0; k < 2; k++)
			attempt("[10.0.0.3]:9", T, "wrong");
		demands(!rcp_banned("[10.0.0.3]:9", T, NULL),
		      "at two failures the address is NOT banned yet (threshold 3)");
		demands(!rcp_unblock(key_id, T),
		      "⛔ and the unblock answers FALSE — «it was not banned» — which is "
		      "exactly the case in which the line of 01-b8-sblocca.py speaks");

		/* c. ⭐ THE LINE NOBODY HAD MEASURED: the count restarted from
		 *    zero, so the two following failures do NOT ban. */
		attempt("[10.0.0.3]:9", T, "wrong");
		attempt("[10.0.0.3]:9", T, "wrong");
		demands(attempt("[10.0.0.3]:9", T, "parola-giusta") == 0x00,
		      "⭐ THE COUNT RESTARTED FROM ZERO: after an unblock on a "
		      "NOT banned address, two more failures do not make three — and the "
		      "sampling strategy of B8 rests on this line");
		demands(!rcp_banned("[10.0.0.3]:9", T, NULL),
		      "⛔ and the check that says NO: the address is not banned "
		      "even now (if the count had not restarted, 2+2 would make "
		      "four and the ban would have triggered at the third)");
	}

	/* ═══ ⛔ THE VERDICT, AND ITS DENOMINATOR ═════════════════════════════════ */
	/* ⛔ `LEZIONI.md` §1.9 rule 6: «a verdict too has a denominator, and it is
	 *    how many things it approved, and if it is zero no outcome is given».
	 *    ⚠ And here «different from zero» is not enough: a `return 0;` put in the
	 *      middle would leave a small but non-null denominator, and a small
	 *      number alone cannot be told from a short run.  So it is declared HOW
	 *      MANY there had to be, and the comparison is done by the bench (B0.4). */
	{
		int as_root_here = (geteuid() == 0);
		/* ⚠ As root section 4 skips two checks and counts one failed in their
		 *   place: the expected number is different, and it is declared instead
		 *   of being widened when it does not add up. */
		/* ⚠ The two numbers are counted by hand, section by section: 6 + 7 + 8 +
		 *   (5 as a normal user, 3 as root) + 7.  ⛔ Whoever adds an `demands()`
		 *   updates this line in the same commit: it is the price of the
		 *   denominator, and it is lower than a green on an empty set. */
		const int EXPECTED_SECTIONS = 5;
		const int EXPECTED_CHECKS = as_root_here ? 31 : 33;
		printf("\n  == the denominator of THIS verdict\n");
		printf("    sections that got to the end : %d (expected %d)\n",
		       test_sections, EXPECTED_SECTIONS);
		printf("    checks run                   : %d (expected %d%s)\n",
		       passed_test + test_failures, EXPECTED_CHECKS,
		       as_root_here ? ", as root" : "");
		printf("    of which APPROVED            : %d\n", passed_test);
		printf("    of which failed              : %d\n", test_failures);

		if (passed_test + test_failures == 0) {
			printf("\n  ⛔ NO OUTCOME: this run approved ZERO things.\n");
			printf("     «All those tested went well» is true even "
			       "when the tested are zero\n");
			verdict_given = true;
			return 2;
		}
		if (test_sections != EXPECTED_SECTIONS
		    || passed_test + test_failures != EXPECTED_CHECKS) {
			printf("\n  ⛔ RED: the run did not get to the end — %d sections "
			       "out of %d, %d checks out of %d.\n",
			       test_sections, EXPECTED_SECTIONS,
			       passed_test + test_failures, EXPECTED_CHECKS);
			printf("     ⛔ The expected is not widened until it comes back green: either "
			       "a check was added and these two numbers must be "
			       "updated together, or a piece of the file was not "
			       "run.\n");
			verdict_given = true;
			return 3;
		}
		printf("\n  %s: %d checks failed out of %d approved, in %d sections\n",
		       test_failures ? "RED" : "GREEN", test_failures, passed_test,
		       test_sections);
		verdict_given = true;
		return test_failures ? 1 : 0;
	}
}
