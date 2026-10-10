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
 * Until tonight there was **only one** here, `falliti_prova`, and the verdict at
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
static int falliti_prova = 0;
static int passati_prova = 0;
static int sezioni_prova = 0;

static void esige(int cond, const char *che)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", che);
	if (cond)
		passati_prova++;
	else
		falliti_prova++;
}

/* ⚠ The denominator of every section is printed: how many checks, and on what.
 *   A list of OKs without the number of what it looked at is not a
 *   measurement (`LEZIONI.md` §1.9 rule 4). */
static void sezione(const char *titolo)
{
	sezioni_prova++;
	printf("\n  == [section %d] %s\n", sezioni_prova, titolo);
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
static bool verdetto_dato = false;
static void al_congedo(void)
{
	if (verdetto_dato)
		return;
	fprintf(stderr,
	        "\n  ⛔ EARLY EXIT: this program ended WITHOUT giving a "
	        "verdict.\n     It ran %d checks in %d sections and "
	        "concluded nothing:\n     «I did not conclude» is not «everything "
	        "went well».\n",
	        passati_prova + falliti_prova, sezioni_prova);
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
enum { T_CIAO = 0x0001, T_ECCOMI = 0x0002, T_CREDENZIALI = 0x0003,
       T_AMMESSO = 0x0004, T_RESPINTO = 0x0005 };

struct ospite {
	int eccomi;      /* how many ECCOMI went out */
	int ammesso;     /* how many AMMESSO */
	int respinto;    /* how many RESPINTO */
	uint8_t motivo;  /* the reason of the last RESPINTO */
};

static void o_manda(void *ctx, const uint8_t *dati, size_t len)
{
	struct ospite *o = ctx;
	if (len < 6)
		return;
	uint16_t tipo = (uint16_t)((dati[0] << 8) | dati[1]);
	if (tipo == T_ECCOMI)
		o->eccomi++;
	else if (tipo == T_AMMESSO)
		o->ammesso++;
	else if (tipo == T_RESPINTO) {
		o->respinto++;
		o->motivo = len > 6 ? dati[6] : 0;
	}
}
static void o_chiudi(void *ctx, uint8_t motivo) { (void)ctx; (void)motivo; }
static void o_registra(void *ctx, const char *riga) { (void)ctx; (void)riga; }
/* ⚠ The right password is only one, and it is declared: this way «wrong» and
 *   «right» are two cases and not two names of the same thing. */
static bool o_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	(void)utente;
	return strcmp(parola, "parola-giusta") == 0;
}

static size_t metti_str(uint8_t *b, size_t i, const char *t)
{
	size_t n = strlen(t);
	b[i++] = (uint8_t)(n >> 8);
	b[i++] = (uint8_t)(n & 0xFF);
	memcpy(b + i, t, n);
	return i + n;
}

static size_t inquadra(uint8_t *b, uint16_t tipo, const uint8_t *corpo, size_t len)
{
	b[0] = (uint8_t)(tipo >> 8);
	b[1] = (uint8_t)(tipo & 0xFF);
	b[2] = (uint8_t)((len >> 24) & 0xFF);
	b[3] = (uint8_t)((len >> 16) & 0xFF);
	b[4] = (uint8_t)((len >> 8) & 0xFF);
	b[5] = (uint8_t)(len & 0xFF);
	memcpy(b + 6, corpo, len);
	return 6 + len;
}

/* A whole attempt from `provenienza`, with `parola`.  Returns:
 *   0x00  AMMESSO
 *   0x07  RESPINTO CREDENZIALI_ERRATE
 *   0x08  RESPINTO TROPPI_TENTATIVI
 *   0xFF  ⛔ no answer arrived — and it is NOT a refusal.  */
static uint8_t un_tentativo(const char *provenienza, uint64_t ora,
                            const char *parola)
{
	static const char *const VOCI[] = {
	    "video.codec", "hevc,av1", "video.profondita", "8,10",
	    "audio.codec", "opus,pcm", "video.livello", "5.1",
	    "video.misura_massima", "3840x2160", "appunti.testo", "si",
	    "input.tocco", "no", "client.nome", "01-b8-prova-ban", NULL};
	struct ospite o = {0, 0, 0, 0};
	rcp_ganci g = {&o, o_manda, o_chiudi, o_registra, o_verifica};
	rcp_sessione *s = rcp_apri(&g, provenienza, ora);
	if (!s)
		return 0xFF;

	uint8_t corpo[1024], frame[1100];
	size_t i = 0;
	corpo[i++] = 0;
	corpo[i++] = 1;           /* version 1 */
	int quante = 0;
	for (int k = 0; VOCI[k]; k += 2)
		quante++;
	corpo[i++] = (uint8_t)(quante >> 8);
	corpo[i++] = (uint8_t)(quante & 0xFF);
	for (int k = 0; VOCI[k]; k += 2) {
		i = metti_str(corpo, i, VOCI[k]);
		i = metti_str(corpo, i, VOCI[k + 1]);
	}
	size_t n = inquadra(frame, T_CIAO, corpo, i);
	rcp_ricevi(s, frame, n, ora);
	if (o.eccomi != 1) {
		rcp_libera(s);
		return 0xFF;         /* ⛔ without ECCOMI the attempt did not happen */
	}

	i = metti_str(corpo, 0, "utente-di-prova");
	i = metti_str(corpo, i, parola);
	n = inquadra(frame, T_CREDENZIALI, corpo, i);
	rcp_ricevi(s, frame, n, ora);
	/* ⛔ The fixed second of §4.4-bis: time arrives from outside (`rcp.h`), and
	 *    without making it flow the verdict never comes out. */
	rcp_tempo(s, ora + 1500);
	uint8_t esito = 0xFF;
	if (o.ammesso)
		esito = 0x00;
	else if (o.respinto)
		esito = o.motivo;
	rcp_libera(s);
	return esito;
}

int main(void)
{
	/* ⛔ Before anything else: the exit hook that refuses to exit zero without
	 *    a verdict (see `al_congedo`). */
	atexit(al_congedo);
	const uint64_t ORA = 1000000; /* any monotonic clock */
	const char *f = "/tmp/remotix-b8-ban.txt";
	time_t adesso = time(NULL);

	/* ═══ 1. the absolute time on disk, and the monotonic time in memory ═════ */
	sezione("1. the ban file: absolute time on disk, monotonic in memory");
	FILE *w = fopen(f, "w");
	/* ⛔ The brackets are there because they are there in the real key:
	 *    `util::straddr()` writes `[1.2.3.4]:44661`, and the ban file receives
	 *    what `solo_indirizzo()` leaves of it.  Writing `1.2.3.4` here would
	 *    test a form the server never produces. */
	fprintf(w, "[1.2.3.4] %lld\n", (long long)adesso + 3600); /* in an hour */
	fprintf(w, "[9.9.9.9] %lld\n", (long long)adesso - 10);   /* already expired */
	fclose(w);

	int quanti = rcp_ban_carica(f, ORA);
	printf("  loaded: %d  (lines in the file: 2, of which 1 already expired)\n", quanti);
	esige(quanti == 1, "loads ONE line only: the expired one is discarded");

	uint64_t restano = 0;
	esige(rcp_bannato("[1.2.3.4]:44661", ORA, &restano),
	      "the banned address is banned — and the PORT does not confuse it");
	printf("  remaining: %llu ms (expected ~3600000)\n",
	       (unsigned long long)restano);
	esige(restano > 3590000 && restano <= 3600000,
	      "the absolute expiry came back monotonic without drift");

	esige(!rcp_bannato("[9.9.9.9]:1", ORA, NULL),
	      "⛔ the check that says NO: the expired line was not loaded");
	esige(!rcp_bannato("[5.5.5.5]:1", ORA, NULL),
	      "⛔ and an address never seen is not banned (the guard does not invent)");

	/* Twelve hours later, the same ban is over by itself. */
	esige(!rcp_bannato("[1.2.3.4]:44661", ORA + 43200000u, NULL),
	      "the ban expires by itself as time passes");

	/* ═══ 2. the ban key, and the four forms in which it arrives ════════════ */
	sezione("2. ⛔ the KEY carries brackets, and whoever commands types without them");
	{
		struct {
			const char *dato;
			const char *atteso;
		} casi[] = {
		    {"127.0.0.1", "[127.0.0.1]"},
		    {"127.0.0.1:53", "[127.0.0.1]"},
		    {"[127.0.0.1]", "[127.0.0.1]"},
		    {"[127.0.0.1]:55680", "[127.0.0.1]"},
		    {"fe80::1", "[fe80::1]"},
		    {"[fe80::1]:44661", "[fe80::1]"},
		};
		int n = (int)(sizeof casi / sizeof casi[0]);
		printf("  forms tested: %d\n", n);
		for (int i = 0; i < n; i++) {
			char chiave[64];
			rcp_chiave_indirizzo(casi[i].dato, chiave, sizeof chiave);
			char che[160];
			snprintf(che, sizeof che, "«%s» → «%s» (expected «%s»)", casi[i].dato,
			         chiave, casi[i].atteso);
			esige(strcmp(chiave, casi[i].atteso) == 0, che);
		}
		/* ⛔ And the check that says NO: two DIFFERENT addresses must not end
		 *    up on the same key, or the ban of one would lock out the other
		 *    and no bench would see it. */
		char a[64], b[64];
		rcp_chiave_indirizzo("127.0.0.1", a, sizeof a);
		rcp_chiave_indirizzo("127.0.0.2", b, sizeof b);
		esige(strcmp(a, b) != 0,
		      "⛔ the check that says NO: two different addresses give two "
		      "different keys");
	}

	/* ═══ 3. the unblock, and its TWO answers ════════════════════════════ */
	sezione("3. the unblock command: «it was not banned» and «I removed it»");
	/* ⛔ It is called with the form A PERSON TYPES — without brackets — which is
	 *    the real case: if this line used `[1.2.3.4]` it would test the road no
	 *    human being travels, and the command would stay broken for everyone
	 *    else.  It is the certification of the certification. */
	{
		char chiave[64];
		rcp_chiave_indirizzo("1.2.3.4", chiave, sizeof chiave);
		esige(rcp_sblocca(chiave, ORA),
		      "the unblock says TRUE on a really banned address — and "
		      "the address had been typed WITHOUT the brackets");
		esige(!rcp_bannato("[1.2.3.4]:44661", ORA, NULL),
		      "and afterwards it is no longer banned");
		esige(!rcp_sblocca(chiave, ORA),
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
		rcp_azzera_registro_sessioni();
		FILE *s = fopen(f, "w");
		fprintf(s, "[fe80::1] %lld\n", (long long)adesso + 3600);
		fclose(s);
		int n6 = rcp_ban_carica(f, ORA);
		printf("  IPv6 bans loaded: %d (expected 1)\n", n6);
		esige(n6 == 1, "an IPv6 ban is read back from the file");
		esige(rcp_bannato("[fe80::1]:44661", ORA, NULL),
		      "and with the port on it it is banned (it is the session's form)");
		char chiave6[64];
		rcp_chiave_indirizzo("fe80::1", chiave6, sizeof chiave6);
		esige(rcp_sblocca(chiave6, ORA),
		      "⛔ and the unblock FINDS it even without a port: «[fe80::1]» is not "
		      "cut at the last colon, or it would become «[fe80:»");
		esige(!rcp_bannato("[fe80::1]:44661", ORA, NULL),
		      "and afterwards the IPv6 is no longer banned");
	}

	/* ⛔ And the unblock ended up on DISK, not only in memory: if it stayed in
	 *    memory, the restart would put back the ban someone removed. */
	{
		FILE *r = fopen(f, "r");
		char riga[128];
		int righe = 0;
		while (fgets(riga, sizeof riga, r))
			righe++;
		fclose(r);
		esige(righe == 0,
		      "the unblock was written to the file, not only in memory");
	}

	/* ═══ 4. ⛔ «zero bans» and «I could not read» ════════════════════════ */
	sezione("4. ⛔ zero bans and «I could not look» — LEZIONI.md §1.9");
	{
		rcp_azzera_registro_sessioni();
		/* a. the file is not there yet: zero, and it is NOT an error */
		const char *mai = "/tmp/remotix-b8-ban-che-non-esiste.txt";
		unlink(mai);
		int r = rcp_ban_carica(mai, ORA);
		printf("  missing file         → %d (expected 0)\n", r);
		esige(r == 0, "a file that does not exist yet counts as ZERO bans, not an error");

		/* b. the file is there and empty: zero, and I read it */
		const char *vuoto = "/tmp/remotix-b8-ban-vuoto.txt";
		FILE *v = fopen(vuoto, "w");
		fclose(v);
		r = rcp_ban_carica(vuoto, ORA);
		printf("  empty file           → %d (expected 0)\n", r);
		esige(r == 0, "an empty file counts as ZERO bans");

		/* c. ⛔ the file is there and CANNOT be read: -1, never 0.
		 *    ⚠ With permissions at 000 this test is true only for a normal
		 *      user: as root it would be green by construction, and it is the
		 *      reason this check CANNOT be in the bench on the wire, which runs
		 *      as root inside the container. */
		const char *chiuso = "/tmp/remotix-b8-ban-chiuso.txt";
		FILE *c = fopen(chiuso, "w");
		fprintf(c, "[7.7.7.7] %lld\n", (long long)adesso + 3600);
		fclose(c);
		chmod(chiuso, 0);
		errno = 0;
		r = rcp_ban_carica(chiuso, ORA);
		int da_root = (geteuid() == 0);
		printf("  file without perms   → %d (expected %s)%s\n", r,
		       da_root ? "1, because you run as ROOT" : "-1",
		       da_root ? "  ⚠ as root permissions stop nobody: this "
		                 "check was NOT run"
		               : "");
		if (da_root) {
			printf("    ??  ⛔ SKIPPED: run this test again as a normal "
			       "user, or it proves nothing\n");
			falliti_prova++; /* ⛔ a skipped check is not a passed check */
		} else {
			esige(r == -1,
			      "⛔ a file that is there and cannot be read counts as -1, NOT zero: «empty» "
			      "and «forbidden» must not have the same face");
			esige(!rcp_bannato("[7.7.7.7]:1", ORA, NULL),
			      "⛔ and the check that says NO: from an unreadable file no "
			      "invented ban comes out");
		}
		chmod(chiuso, 0600);
		unlink(chiuso);

		/* d. and a path whose parent is not a directory: -1 */
		const char *storto = "/tmp/remotix-b8-ban-vuoto.txt/dentro.txt";
		r = rcp_ban_carica(storto, ORA);
		printf("  impossible path      → %d (expected -1)\n", r);
		esige(r == -1,
		      "⛔ and a path that cannot even be opened counts as -1: "
		      "ENOTDIR is not «no ban»");

		unlink(vuoto);
		/* ⚠ And persistence is switched off before leaving: `rcp_ban_carica()`
		 *   remembers the path EVEN when it fails, and the first following ban
		 *   would try to write there. */
		rcp_ban_carica(NULL, ORA);
	}

	/* ═══ 5. ⛔ THE UNBLOCK RESETS THE COUNT EVEN WHEN THERE WAS NO BAN ═══ */
	/* ⛔ Finding A22, 11 Aug 2026.  `01-b8-sblocca.py` prints, on
	 *    `NON-BANNATO`, *«and the attempt count of that address restarts from
	 *    zero anyway»*, and `simula()` of `01-b8-cronometro.py` models the
	 *    unblock as `falliti[ind] = 0` **always**.  ⛔ Neither of the two
	 *    verified it, and the WHOLE sampling strategy of B8 rests on that
	 *    behaviour: «unblock between one block and the next».  If `rcp_sblocca()`
	 *    reset the entry **only when a ban is there**, the failures would pile up
	 *    between the blocks and the samples would start coming back
	 *    `limitatore` — that is the bench would measure the ban believing it is
	 *    measuring PAM.
	 *
	 * ⚠ And it is measured HERE and not on the wire for the usual reason: on the
	 *   wire three real failed authentications would be needed, that is consuming
	 *   the §4.4-bis count of the whole machine (B0.3) to test one line.
	 *
	 * ⛔ And every check has its check that says NO, or «the ban did not
	 *    trigger» would be satisfied also by a module that does not count.     */
	sezione("5. ⛔ the unblock resets the count even on a NOT banned address");
	{
		rcp_azzera_registro_sessioni();
		const uint64_t T = 5000000;

		/* ⭐ THE POSITIVE CONTROL OF THE TOOL, FIRST OF ALL: if the fake host
		 *    could not bring an attempt to the end, every «the ban did not
		 *    trigger» that follows would mean «I measured nothing»
		 *    (`REVIEWER.md` §1 question 5). */
		esige(un_tentativo("[10.0.0.1]:1", T, "parola-giusta") == 0x00,
		      "⭐ positive control: an attempt with the RIGHT password gets "
		      "to AMMESSO — the tool can make happen what counts");
		esige(un_tentativo("[10.0.0.1]:2", T, "sbagliata") == RCP_CREDENZIALI_ERRATE,
		      "⭐ and one with the wrong password gets to CREDENZIALI_ERRATE: "
		      "the tool can also produce the failures that count");

		/* a. the check that says NO: without unblock, three failures ban */
		rcp_azzera_registro_sessioni();
		for (int k = 0; k < 3; k++)
			un_tentativo("[10.0.0.2]:9", T, "sbagliata");
		esige(un_tentativo("[10.0.0.2]:9", T, "parola-giusta")
		          == RCP_TROPPI_TENTATIVI,
		      "⛔ the check that says NO: WITHOUT unblock, three failures "
		      "ban and the fourth — with the RIGHT password — is TROPPI_TENTATIVI");

		/* b. two failures, then the unblock on a NOT banned address */
		rcp_azzera_registro_sessioni();
		char chiave[64];
		rcp_chiave_indirizzo("10.0.0.3", chiave, sizeof chiave);
		for (int k = 0; k < 2; k++)
			un_tentativo("[10.0.0.3]:9", T, "sbagliata");
		esige(!rcp_bannato("[10.0.0.3]:9", T, NULL),
		      "at two failures the address is NOT banned yet (threshold 3)");
		esige(!rcp_sblocca(chiave, T),
		      "⛔ and the unblock answers FALSE — «it was not banned» — which is "
		      "exactly the case in which the line of 01-b8-sblocca.py speaks");

		/* c. ⭐ THE LINE NOBODY HAD MEASURED: the count restarted from
		 *    zero, so the two following failures do NOT ban. */
		un_tentativo("[10.0.0.3]:9", T, "sbagliata");
		un_tentativo("[10.0.0.3]:9", T, "sbagliata");
		esige(un_tentativo("[10.0.0.3]:9", T, "parola-giusta") == 0x00,
		      "⭐ THE COUNT RESTARTED FROM ZERO: after an unblock on a "
		      "NOT banned address, two more failures do not make three — and the "
		      "sampling strategy of B8 rests on this line");
		esige(!rcp_bannato("[10.0.0.3]:9", T, NULL),
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
		int da_root_qui = (geteuid() == 0);
		/* ⚠ As root section 4 skips two checks and counts one failed in their
		 *   place: the expected number is different, and it is declared instead
		 *   of being widened when it does not add up. */
		/* ⚠ The two numbers are counted by hand, section by section: 6 + 7 + 8 +
		 *   (5 as a normal user, 3 as root) + 7.  ⛔ Whoever adds an `esige()`
		 *   updates this line in the same commit: it is the price of the
		 *   denominator, and it is lower than a green on an empty set. */
		const int SEZIONI_ATTESE = 5;
		const int CONTROLLI_ATTESI = da_root_qui ? 31 : 33;
		printf("\n  == the denominator of THIS verdict\n");
		printf("    sections that got to the end : %d (expected %d)\n",
		       sezioni_prova, SEZIONI_ATTESE);
		printf("    checks run                   : %d (expected %d%s)\n",
		       passati_prova + falliti_prova, CONTROLLI_ATTESI,
		       da_root_qui ? ", as root" : "");
		printf("    of which APPROVED            : %d\n", passati_prova);
		printf("    of which failed              : %d\n", falliti_prova);

		if (passati_prova + falliti_prova == 0) {
			printf("\n  ⛔ NO OUTCOME: this run approved ZERO things.\n");
			printf("     «All those tested went well» is true even "
			       "when the tested are zero\n");
			verdetto_dato = true;
			return 2;
		}
		if (sezioni_prova != SEZIONI_ATTESE
		    || passati_prova + falliti_prova != CONTROLLI_ATTESI) {
			printf("\n  ⛔ ROSSO: the run did not get to the end — %d sections "
			       "out of %d, %d checks out of %d.\n",
			       sezioni_prova, SEZIONI_ATTESE,
			       passati_prova + falliti_prova, CONTROLLI_ATTESI);
			printf("     ⛔ The expected is not widened until it comes back green: either "
			       "a check was added and these two numbers must be "
			       "updated together, or a piece of the file was not "
			       "run.\n");
			verdetto_dato = true;
			return 3;
		}
		printf("\n  %s: %d checks failed out of %d approved, in %d sections\n",
		       falliti_prova ? "ROSSO" : "VERDE", falliti_prova, passati_prova,
		       sezioni_prova);
		verdetto_dato = true;
		return falliti_prova ? 1 : 0;
	}
}
