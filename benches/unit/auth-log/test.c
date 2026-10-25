/*
 * test.c — R3 (audit of 25 Oct 2026): the PAM refusal lines (`why_no()` of src/authentication.c) never carry a name that is not a user
 * of this machine, and no control character.  A person who types the password in the user field must not leave it in the journal
 * (DECISIONS §11.1, §4.4-bis D); before the fix `why_no()` wrote the raw name between «...».
 *
 * HOW: the REAL src/authentication.c is #included (never modified) and `why_no()` is called with stderr sent to a file.  Checked:
 *   · a user of this machine (root) → «user «root»» (the name is shown);
 *   · a name that is not a user (a "password", 300 bytes of it, one with newline and ESC) → «unknown user [tag]» where tag is the
 *     6 hex of REMOTIX_PAM_LOG_TAG when valid, `??????` when missing or malformed; the typed text appears NOWHERE in the output;
 *   · exactly one line per call (a newline in the name does not split it), no byte below 0x20 except the final newline;
 *   · both branches («PAM REFUSED» and «PAM COULD NOT JUDGE») and the locked variant.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=1g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src /albero/benches/unit/auth-log/test.c -lpam -o test && ./test'
 * Exit code 0 = every check passed.
 */
#include "authentication.c"

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; fprintf(stdout, "FAIL: %s\n", what); } } while (0)

static char out[4096];

/* Runs why_no() with stderr in a file, returns what it wrote in `out`. */
static void run(const char *user, int rv, bool locked)
{
	FILE *f = freopen("/tmp/auth-log.out", "w", stderr);
	(void)f;
	why_no(user, "pam_authenticate", NULL, rv, locked);
	fflush(stderr);
	FILE *r = fopen("/tmp/auth-log.out", "r");
	size_t n = r ? fread(out, 1, sizeof out - 1, r) : 0;
	out[n] = 0;
	if (r)
		fclose(r);
}

static int lines(void)
{
	int n = 0;
	for (const char *p = out; *p; p++)
		if (*p == '\n')
			n++;
	return n;
}

static bool no_control(void)
{
	for (const char *p = out; p[0] && p[1]; p++)   /* all but the last byte (the newline) */
		if ((unsigned char)*p < 0x20 || *p == 0x7f)
			return false;
	return true;
}

int main(void)
{
	/* 1. a user of this machine: named */
	unsetenv("REMOTIX_PAM_LOG_TAG");
	run("root", PAM_AUTH_ERR, false);
	CHECK(strstr(out, "PAM REFUSED user «root» in pam_authenticate"), "a real user is named");
	CHECK(lines() == 1 && no_control(), "one line, no control byte (real user)");

	/* 2. a typed password in the user field, with the tag the server computed */
	setenv("REMOTIX_PAM_LOG_TAG", "a1b2c3", 1);
	run("Tr0ub4dor&3-hunter2", PAM_USER_UNKNOWN, false);
	CHECK(strstr(out, "PAM REFUSED unknown user [a1b2c3] in pam_authenticate"), "unknown name → unknown user [tag]");
	CHECK(!strstr(out, "Tr0ub4dor") && !strstr(out, "hunter2"), "the typed text is nowhere in the line");
	CHECK(lines() == 1 && no_control(), "one line, no control byte (unknown)");

	/* 3. no tag, or a malformed one */
	unsetenv("REMOTIX_PAM_LOG_TAG");
	run("secret-pw", PAM_AUTH_ERR, false);
	CHECK(strstr(out, "unknown user [??????]") && !strstr(out, "secret-pw"), "no tag → ??????");
	setenv("REMOTIX_PAM_LOG_TAG", "zz\n\x1b[31m", 1);
	run("secret-pw", PAM_AUTH_ERR, false);
	CHECK(strstr(out, "unknown user [??????]") && lines() == 1 && no_control(), "malformed tag → ??????, still one clean line");
	setenv("REMOTIX_PAM_LOG_TAG", "a1b2c3d4", 1);
	run("secret-pw", PAM_AUTH_ERR, false);
	CHECK(strstr(out, "unknown user [??????]"), "a tag of the wrong length → ??????");

	/* 4. a name with a newline and an escape, and a very long one */
	setenv("REMOTIX_PAM_LOG_TAG", "0f0f0f", 1);
	run("alice\nRCP: forged line\x1b[2J", PAM_AUTH_ERR, false);
	CHECK(lines() == 1 && no_control() && !strstr(out, "forged") && strstr(out, "unknown user [0f0f0f]"), "newline/ESC in the name: nothing leaks, one line");
	char big[301];
	memset(big, 'x', 300);
	big[300] = 0;
	run(big, PAM_AUTH_ERR, false);
	CHECK(!strstr(out, "xxxxxxxx") && strstr(out, "unknown user [0f0f0f]"), "300-byte name: not in the line");

	/* 5. the other branch and the locked variant */
	run("hunter2", PAM_ABORT, false);
	CHECK(strstr(out, "PAM COULD NOT JUDGE unknown user [0f0f0f] in pam_authenticate") && !strstr(out, "hunter2"), "COULD NOT JUDGE: tag, not the name");
	run("hunter2", PAM_AUTH_ERR, true);
	CHECK(strstr(out, "pam_faillock had the account LOCKED") && !strstr(out, "hunter2"), "locked variant keeps the text and not the name");
	run("root", PAM_ABORT, false);
	CHECK(strstr(out, "PAM COULD NOT JUDGE user «root»"), "COULD NOT JUDGE with a real user");

	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
