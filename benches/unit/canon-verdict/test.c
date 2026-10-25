/*
 * test.c — the CANONICAL NAME travels in the VERDICT (rilettura-fix M1): in the split the network side never asks NSS for it.
 *
 * Before: after PAM's yes the network side called getpwnam_r() (main.c delivery_verdict, rcp_verdict) inside the one loop that serves every user, so a stalled sssd stopped
 * everybody.  Now the ROOT side resolves it and sends it in the VERDICT (struct rxr_verdict.canon, RXR_VERSION 3); the network side keeps it with the grant of that login
 * (single use, 30 s, empty after a restart) and rcp_canonical_user() answers from it ONLY.  No entry = the typed name stays, and NSS is not asked.
 *
 * The REAL src/rootside.c and src/rcp.c are #included (their other symbols are trap stubs, as in benches/unit/key-dedupe).  What is checked:
 *   1. rxr_canon_valid(): all zero is fine; a plausible name is fine (also 256 characters); a space, a '/', a control byte, DEL, a field with no NUL, bytes after the NUL are refused;
 *   2. sizeof(struct rxr_verdict) is the wire size and RXR_VERSION is 3;
 *   3. a VERDICT YES with canon: rootside_canonical("Anna") gives "anna"; rootside_has_grant() and the spawn lookup accept EITHER name; another typed name has no entry;
 *   4. a VERDICT YES with no canon, a NO, and an expired grant: no entry (false) — the typed name stays;
 *   5. the entry goes with the grant: rootside_spawn() consumes it (single use);
 *   5c. the split with an UPPERCASE typed name (ANNA, the system says anna): the spawn finds the grant by the typed name AND by the system's; another spelling does not;
 *   6. rcp.c: with the hook set rcp_canonical_user() answers from the hook ONLY (a name that really exists in the system, «root», is NOT found when the hook says no — NSS is not asked);
 *      without the hook it asks the system as before (the single-process server);
 *   7. source reading: client_recv() refuses a VERDICT whose canon is not valid; main.c installs the hook in the network side only after the root channel is attached.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src -I/albero/benches/fuzz/child-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/canon-verdict/test.c -o t.o && clang $F -c /albero/benches/fuzz/child-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && cd /albero && /tmp/test'
 * Exit code 0 = every check passed.
 */
#include "rootside.c"
#include "rcp.c"

#include <stdio.h>
#include <sys/socket.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static int has(const char *file, const char *needle)
{
	FILE *f = fopen(file, "r");
	static char src[8u << 20];
	size_t n;

	if (!f) return 0;
	n = fread(src, 1, sizeof src - 1, f); src[n] = 0; fclose(f);
	return strstr(src, needle) != NULL;
}

static void field(char *f, const char *s)
{
	memset(f, 0, RXR_USER_MAX);
	if (s)
		memcpy(f, s, strlen(s));
}

/* a VERDICT as the dispatcher sees it, for the AUTH slot 0 that asked with `typed` */
static void verdict(const char *typed, int outcome, const char *canon, uint64_t now)
{
	union rpk pk;

	memset(&C, 0, sizeof C);
	C.fd = -1;
	C.auths[0].used = true;
	C.auths[0].request = 7;
	C.auths[0].at_ms = now;
	snprintf(C.auths[0].user, sizeof C.auths[0].user, "%s", typed);
	snprintf(C.auths[0].rhost, sizeof C.auths[0].rhost, "10.0.0.1");
	memset(&pk, 0, sizeof pk);
	head_fill(&pk.v.h, RXR_VERDICT, 7);
	pk.v.outcome = (uint8_t)outcome;
	if (outcome == RXR_YES)
		memset(pk.v.grant, 0xAB, RXR_GRANT_BYTES);
	field(pk.v.canon, canon);
	dispatch(&pk, -1);
}

/* the system's lookup that a real NSS would do: used only to show it is NOT reached */
static int asked;
static bool hook_yes(const char *typed, char *out, size_t cap)
{
	asked++;
	if (strcmp(typed, "Anna") != 0)
		return false;
	snprintf(out, cap, "anna");
	return true;
}
static bool hook_no(const char *typed, char *out, size_t cap)
{
	(void)typed; (void)out; (void)cap;
	asked++;
	return false;
}

int main(void)
{
	char f[RXR_USER_MAX], out[64];
	uint64_t now = log_now_ms();

	/* 1 */
	field(f, NULL);
	CHECK(rxr_canon_valid(f), "1. all zero is valid (no other spelling)");
	field(f, "anna");
	CHECK(rxr_canon_valid(f), "1b. a plausible name is valid");
	memset(f, 'a', RXR_USER_MAX - 1); f[RXR_USER_MAX - 1] = 0;
	CHECK(rxr_canon_valid(f), "1c. 256 characters and the NUL fill the field: valid");
	field(f, "an na");  CHECK(!rxr_canon_valid(f), "1d. a space is refused");
	field(f, "a/b");    CHECK(!rxr_canon_valid(f), "1e. a '/' is refused");
	field(f, "an\nna"); CHECK(!rxr_canon_valid(f), "1f. a control byte is refused");
	field(f, "an\x7f"); CHECK(!rxr_canon_valid(f), "1g. DEL is refused");
	memset(f, 'a', RXR_USER_MAX);
	CHECK(!rxr_canon_valid(f), "1h. a field with no NUL is refused");
	field(f, "anna"); f[10] = 'x';
	CHECK(!rxr_canon_valid(f), "1i. bytes after the NUL are refused");

	/* 2 */
	CHECK(sizeof(struct rxr_verdict) == 296 && RXR_VERSION == 3, "2. the wire size of the VERDICT and its version");

	/* 3 */
	verdict("Anna", RXR_YES, "anna", now);
	CHECK(rootside_canonical("Anna", out, sizeof out) && strcmp(out, "anna") == 0, "3. the entry of a YES with canon: Anna -> anna");
	CHECK(!rootside_canonical("Bruno", out, sizeof out), "3b. another typed name has none");
	CHECK(!rootside_canonical("anna", out, sizeof out), "3c. and the system's name itself has none (the key is the typed one)");
	CHECK(rootside_has_grant("Anna", "10.0.0.1") && rootside_has_grant("anna", "10.0.0.1"), "3d. the grant is found by the typed OR by the system's name (children are keyed by the latter)");
	CHECK(!rootside_has_grant("anna", "10.0.0.9"), "3e. but not for another address");
	CHECK(!rootside_canonical("Anna", out, 4), "3f. a buffer too small gets nothing, not a cut name");

	/* 4 */
	verdict("Anna", RXR_YES, NULL, now);
	CHECK(!rootside_canonical("Anna", out, sizeof out), "4. a YES with no canon: no entry");
	verdict("Anna", RXR_NO, "anna", now);
	CHECK(!rootside_canonical("Anna", out, sizeof out), "4b. a NO keeps none, whatever the field says");
	verdict("Anna", RXR_YES, "anna", now);
	for (int i = 0; i < CLIENT_GRANTS; i++)
		if (C.grants[i].used)
			C.grants[i].expires_ms = 1;
	CHECK(!rootside_canonical("Anna", out, sizeof out), "4c. an expired grant has none");

	/* 5 */
	verdict("Anna", RXR_YES, "anna", now);
	{
		int sv[2];
		struct rootside_born born;

		socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv);
		close(sv[1]);          /* the other end is gone: the send fails at once (the stub clock of stubs_log.c never advances, so no wait may be entered) */
		C.fd = sv[0];
		CHECK(rootside_spawn("anna", "10.0.0.1", 1280, 720, 10, &born) == ROOTSIDE_NOT_SENT, "5. a spawn asked by the SYSTEM's name finds the grant (it got as far as the send)");
		CHECK(!rootside_canonical("Anna", out, sizeof out) && !rootside_has_grant("Anna", "10.0.0.1"), "5b. and the entry went with the grant: single use");
		close(sv[0]);
		C.fd = -1;
	}

	/* 5c: the SPLIT with an UPPERCASE typed name (rilettura-fix A1 of the main reading): sssd/LDAP/AD without case, or an alias, give «anna» for «ANNA».  Before, delivery_verdict renamed
	 * the login to the system's name and rootside_spawn looked for the grant by the TYPED one: NO_GRANT, and the user was refused 0x0E after PAM's yes. */
	for (int by_system = 0; by_system < 2; by_system++) {
		int sv[2];
		struct rootside_born born;

		verdict("ANNA", RXR_YES, "anna", now);
		CHECK(rootside_canonical("ANNA", out, sizeof out) && strcmp(out, "anna") == 0, "5c: ANNA -> anna from the verdict");
		socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv);
		close(sv[1]);
		C.fd = sv[0];
		CHECK(rootside_spawn(by_system ? "anna" : "ANNA", "10.0.0.1", 1280, 720, 10, &born) == ROOTSIDE_NOT_SENT,
		      by_system ? "5c: the spawn asked by the SYSTEM's name finds the grant of ANNA" : "5c: the spawn asked by the TYPED name finds the grant of ANNA");
		close(sv[0]);
		C.fd = -1;
	}
	verdict("ANNA", RXR_YES, "anna", now);
	{
		int sv[2];
		struct rootside_born born;

		socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv);
		close(sv[1]);
		C.fd = sv[0];
		CHECK(rootside_spawn("Anna", "10.0.0.1", 1280, 720, 10, &born) == ROOTSIDE_NO_GRANT, "5c: another spelling (Anna) of the same person is NOT served by the grant of ANNA");
		close(sv[0]);
		C.fd = -1;
	}

	/* 6 */
	CHECK(rcp_canonical_user("root", out, sizeof out) && strcmp(out, "root") == 0, "6. without the hook the system is asked (the single-process server)");
	rcp_canonical_hook(hook_no);
	asked = 0;
	CHECK(!rcp_canonical_user("root", out, sizeof out) && asked == 1, "6b. with the hook set a name the system KNOWS is not found if the hook has none: NSS is not asked");
	rcp_canonical_hook(hook_yes);
	CHECK(rcp_canonical_user("Anna", out, sizeof out) && strcmp(out, "anna") == 0, "6c. and one the hook knows is answered from it");
	rcp_canonical_hook(NULL);

	/* 7 */
	CHECK(has("src/rootside.c", "(pk->h.kind == RXR_VERDICT && !rxr_canon_valid(pk->v.canon))"), "7. client_recv() refuses a VERDICT with an invalid canon");
	CHECK(has("src/main.c", "rcp_canonical_hook(rootside_canonical);"), "7b. main.c installs the hook in the network side");
	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
