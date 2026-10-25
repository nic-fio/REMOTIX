/*
 * test.c — the name of a logged-in session is the NAME OF THE SYSTEM, not the one typed (audit of 25 Oct 2026, P-R6 / Q-R8).
 * The registry of slots (rcp.c), the children, the stages and the budget (main.c) are keyed by the name string.  Where the system does
 * not tell «Anna» from «anna» (sssd / LDAP with case_sensitive = false) one user got a slot, a child and a desktop PER SPELLING, and
 * could take every slot of the server by varying the capitals.  Now rcp_canonical_user() brings the name to pw_name once PAM has admitted
 * it, in rcp_verdict() (the slot and the session) and in delivery_verdict() of main.c (the child, the stage, the budget).
 *
 * What is checked, on the REAL rcp.c (linked) with a getpwnam_r that behaves like a case-insensitive directory (defined here: it
 * replaces the library's in this executable):
 *   1. «Anna», «ANNA» and «anna» all give «anna»; the canonical name comes back unchanged;
 *   2. a name the system does not know gives false and leaves `out` alone; an empty or NULL name too;
 *   3. a buffer too small for the name gives false (never a cut name);
 *   4. a lookup that FAILS (the directory is down) gives false: the typed name stays, the login is not refused;
 *   5. by reading the sources (argv[1] = src/rcp.c, argv[2] = src/main.c): rcp_verdict() canonicalises only when ADMITTED and AFTER the
 *      ban booking (login_resolve / login_report are keyed by what was typed); delivery_verdict() canonicalises only for a verdict
 *      somebody waits for, before it uses the name for the child, and its final transport_verdict_from() still gets the name it was
 *      handed when nobody waits.
 *
 * BUILD AND RUN (a few seconds; from the root of the tree):
 *   F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter -Isrc -Ibenches/fuzz/rcp-msg" &&
 *   gcc $F -c benches/unit/user-canonical/test.c -o /tmp/uc-t.o && gcc $F -c src/rcp.c -o /tmp/uc-r.o &&
 *   gcc $F -c benches/fuzz/rcp-msg/stubs_log.c -o /tmp/uc-l.o && gcc -fsanitize=address,undefined /tmp/uc-t.o /tmp/uc-r.o /tmp/uc-l.o -o /tmp/uc-test &&
 *   /tmp/uc-test src/rcp.c src/main.c
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "rcp.h"

#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static int directory_down;

/* A directory that does not tell the capitals apart: «anna» exists, whatever the case. */
int getpwnam_r(const char *name, struct passwd *pwd, char *buf, size_t buflen, struct passwd **result)
{
	static const char real[] = "anna";

	*result = NULL;
	if (directory_down)
		return 5; /* EIO */
	if (strcasecmp(name, real) != 0)
		return 0;
	if (buflen < sizeof real)
		return 34; /* ERANGE */
	memcpy(buf, real, sizeof real);
	memset(pwd, 0, sizeof *pwd);
	pwd->pw_name = buf;
	pwd->pw_uid = 1000;
	*result = pwd;
	return 0;
}

static char *slurp(const char *path)
{
	FILE *f = fopen(path, "r");
	long n;
	char *b;

	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	b = malloc((size_t)n + 1);
	if (b && fread(b, 1, (size_t)n, f) != (size_t)n) {
		free(b);
		b = NULL;
	}
	if (b)
		b[n] = 0;
	fclose(f);
	return b;
}

static const char *body_of(const char *src, const char *sig, size_t *len)
{
	const char *p = strstr(src, sig);
	const char *e;

	if (!p)
		return NULL;
	e = strstr(p + 1, "\n}\n");
	*len = e ? (size_t)(e - p) : strlen(p);
	return p;
}

int main(int argc, char **argv)
{
	char out[64];

	/* 1 */
	memset(out, 'x', sizeof out);
	CHECK(rcp_canonical_user("Anna", out, sizeof out) && strcmp(out, "anna") == 0, "1: «Anna» gives «anna»");
	CHECK(rcp_canonical_user("ANNA", out, sizeof out) && strcmp(out, "anna") == 0, "1: «ANNA» gives «anna»");
	CHECK(rcp_canonical_user("anna", out, sizeof out) && strcmp(out, "anna") == 0, "1: «anna» stays «anna»");
	/* 2 */
	strcpy(out, "untouched");
	CHECK(!rcp_canonical_user("bruno", out, sizeof out) && strcmp(out, "untouched") == 0, "2: an unknown name gives false and leaves out alone");
	CHECK(!rcp_canonical_user("", out, sizeof out), "2: an empty name gives false");
	CHECK(!rcp_canonical_user(NULL, out, sizeof out), "2: a NULL name gives false");
	CHECK(!rcp_canonical_user("Anna", NULL, 10) && !rcp_canonical_user("Anna", out, 0), "2: no output buffer gives false");
	/* 3 */
	strcpy(out, "untouched");
	CHECK(!rcp_canonical_user("Anna", out, 4) && strcmp(out, "untouched") == 0, "3: a buffer too small for «anna» gives false, the name is never cut");
	CHECK(rcp_canonical_user("Anna", out, 5) && strcmp(out, "anna") == 0, "3: exactly enough works");
	/* 4 */
	directory_down = 1;
	strcpy(out, "untouched");
	CHECK(!rcp_canonical_user("Anna", out, sizeof out) && strcmp(out, "untouched") == 0, "4: a directory that is down gives false (the typed name stays)");
	directory_down = 0;
	/* 5 */
	if (argc > 2) {
		char *r = slurp(argv[1]), *m = slurp(argv[2]);
		size_t n;
		const char *p;

		CHECK(r && m, "5: sources readable");
		if (r && m) {
			p = body_of(r, "bool rcp_verdict(rcp_session *s, uint64_t ticket, bool admitted,\n                  uint64_t now)\n{", &n);
			CHECK(p != NULL, "5: rcp_verdict found");
			if (p) {
				const char *rep = memmem(p, n, "login_report(&k", strlen("login_report(&k"));
				const char *can = memmem(p, n, "rcp_canonical_user(s->user, canon, sizeof canon)", strlen("rcp_canonical_user(s->user, canon, sizeof canon)"));
				const char *adm = can ? memmem(p, (size_t)(can - p), "if (admitted) {", strlen("if (admitted) {")) : NULL;

				CHECK(rep && can && rep < can, "5: rcp_verdict: the ban booking (typed name) comes BEFORE the name is changed");
				CHECK(adm != NULL, "5: rcp_verdict: only when ADMITTED");
			}
			p = body_of(m, "static void delivery_verdict(void *ctx, uint64_t ticket, bool admitted,", &n);
			CHECK(p != NULL, "5: delivery_verdict found");
			if (p) {
				const char *can = memmem(p, n, "rcp_canonical_user(user_typed, user_buf, sizeof user_buf)", strlen("rcp_canonical_user(user_typed, user_buf, sizeof user_buf)"));
				const char *aw = memmem(p, n, "transport_awaits_verdict(p->t, ticket) &&", strlen("transport_awaits_verdict(p->t, ticket) &&"));
				const char *child = memmem(p, n, "children_alive_of(p->f, user)", strlen("children_alive_of(p->f, user)"));

				CHECK(can && aw && child && aw < can && can < child, "5: delivery_verdict: only for a verdict somebody waits for, and BEFORE the child is looked at");
				CHECK(memmem(p, n, "admitted && !lost", strlen("admitted && !lost")) != NULL, "5: delivery_verdict: only for an admitted, not lost, verdict");
			}
		}
		free(r);
		free(m);
	}
	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
