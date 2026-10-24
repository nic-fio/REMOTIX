/*
 * test.c — the «desktop still closing» path of delivery_verdict() (src/main.c): the 0x0E goes to THIS login only.
 * Same method as benches/unit/evict/test_orphan.c: the REAL src/main.c is #included (its `main` renamed, never modified)
 * and delivery_verdict() runs against fakes of the children, the transport, the budget and wt_dismiss_user/wt_dismiss_ticket
 * (anything else reached TRAPS: the generated stubs).  The log is benches/fuzz/rcp-msg/stubs_log.c.
 *
 * ⛔ A PAM yes whose user's desktop is still CLOSING (a pid, but not alive) used to dismiss every session of that name:
 *    other connections of the same name may be strangers still trying passwords, and would learn that the account exists
 *    (§4.4).  Now only the session of this ticket is sent away, through wt_dismiss_ticket():
 *   (a) 1-3.  the admitted, awaited login of a closing desktop gets 0x0E through wt_dismiss_ticket(ticket…) only;
 *   (b) 4-6.  a second login of the same user in flight, with another ticket, is NOT dismissed and gets its own verdict;
 *   (c) 7-9.  transport_verdict_from() gets admitted=true (not counted as a failure), not RESUMED, and no child is created;
 *   (d) 10-12. a not-admitted verdict (wrong password) on a closing desktop gets the normal refusal, NOT the closing
 *             message (it must not reveal that the account exists), and the desktop is not even looked at;
 *   (e) 13-15. nobody waits for the answer: no closing branch, no dismiss, no child, the verdict still delivered.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src -I/albero/benches/fuzz/rcp-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/closing-ticket/test.c -o t.o && clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && ./test'
 * Exit code 0 green, 1 red, 3 not all checks ran.
 */
#define _GNU_SOURCE
#define main remotix_main
#define rcp_cap fake_rcp_cap
#define budget_verdict_line fake_budget_verdict_line
#define children_pid_of fake_children_pid_of
#define children_alive_of fake_children_alive_of
#define children_ensure_from fake_children_ensure_from
#define children_count fake_children_count
#define children_ask_stage fake_children_ask_stage
#define transport_verdict_from fake_transport_verdict_from
#define transport_awaits_verdict fake_transport_awaits_verdict
#define wt_dismiss_user fake_wt_dismiss_user
#define wt_dismiss_ticket fake_wt_dismiss_ticket
#define budget_on fake_budget_on
#include "main.c"
#undef main

#include <stdio.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 15

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

static int n_pid, n_ensure, n_verdict, n_dismiss_user, n_dismiss_ticket;
static bool awaits, alive;
static pid_t pid;                        /* what the fake children_pid_of() answers */
static uint64_t dismissed_ticket;        /* the last ticket wt_dismiss_ticket() was asked about */
static uint8_t dismissed_reason;
static char dismissed_detail[320];
static uint64_t verdict_ticket;          /* the last verdict */
static bool verdict_admitted;
static uint8_t last_resumed = 0xFF;

pid_t fake_children_pid_of(const children *f, const char *user)
{
	(void)f;
	(void)user;
	n_pid++;
	return pid;
}
bool fake_children_alive_of(const children *f, const char *user)
{
	(void)f;
	(void)user;
	return alive;
}
bool fake_children_ensure_from(children *f, const char *user, const char *rhost)
{
	(void)f;
	(void)user;
	(void)rhost;
	n_ensure++;
	return true;
}
int fake_children_count(const children *f)
{
	(void)f;
	return 0;
}
bool fake_children_ask_stage(children *f, const char *user)
{
	(void)f;
	(void)user;
	return true;
}
void fake_transport_verdict_from(transport *t, uint64_t ticket, bool admitted, bool resumed,
                                 const char *user, const char *rhost, bool lost)
{
	(void)t;
	(void)user;
	(void)rhost;
	(void)lost;
	n_verdict++;
	verdict_ticket = ticket;
	verdict_admitted = admitted;
	last_resumed = resumed;
}
bool fake_transport_awaits_verdict(const transport *t, uint64_t ticket)
{
	(void)t;
	(void)ticket;
	return awaits;
}
size_t fake_wt_dismiss_user(const char *user, uint8_t reason, const char *detail,
                            const wt *except)
{
	(void)user;
	(void)reason;
	(void)detail;
	(void)except;
	n_dismiss_user++;
	return 0;
}
size_t fake_wt_dismiss_ticket(uint64_t ticket, uint8_t reason, const char *detail)
{
	n_dismiss_ticket++;
	dismissed_ticket = ticket;
	dismissed_reason = reason;
	snprintf(dismissed_detail, sizeof dismissed_detail, "%s", detail ? detail : "");
	return 1;
}
bool fake_budget_on(void) { return false; }
int fake_rcp_cap(void) { return 8; }
void fake_budget_verdict_line(const char *user, bool admitted, uint8_t reason, int session_cap, const char *why)
{
	(void)user;
	(void)admitted;
	(void)reason;
	(void)session_cap;
	(void)why;
}

/* The desktop is closing: a pid, but not alive. */
static void reset(bool waiting)
{
	n_pid = n_ensure = n_verdict = n_dismiss_user = n_dismiss_ticket = 0;
	dismissed_ticket = 0;
	dismissed_reason = 0;
	dismissed_detail[0] = '\0';
	verdict_ticket = 0;
	verdict_admitted = false;
	last_resumed = 0xFF;
	awaits = waiting;
	alive = false;
	pid = 4242;
}

int main(void)
{
	struct bridge br = {NULL, NULL};   /* t, f: only the fakes see them */

	setvbuf(stdout, NULL, _IONBF, 0);

	printf("  an admitted, awaited login on a closing desktop\n");
	reset(true);
	delivery_verdict(&br, 51, true, "anna", "10.0.0.9", false);
	require(n_dismiss_ticket == 1 && dismissed_ticket == 51 && dismissed_reason == RCP_SESSION_UNSERVABLE,
	        "1. 0x0E goes out through wt_dismiss_ticket(51), once");
	require(n_dismiss_user == 0, "2. wt_dismiss_user() is never called");
	require(strstr(dismissed_detail, "still closing") != NULL, "3. the detail says the desktop is still closing");
	require(verdict_admitted && verdict_ticket == 51, "7. transport_verdict_from() gets admitted=true (not counted as a failure)");
	require(n_ensure == 0, "8. no child is created");
	require(last_resumed == 0, "9. the verdict is not RESUMED");

	printf("  a second login of the same user, in flight, another ticket (wrong password)\n");
	delivery_verdict(&br, 52, false, "anna", "10.0.0.7", false);
	require(n_dismiss_ticket == 1 && dismissed_ticket == 51, "4. ticket 52 is NOT dismissed (still only 51)");
	require(n_verdict == 2 && verdict_ticket == 52 && !verdict_admitted, "5. ticket 52 receives its own verdict (a refusal)");
	require(n_dismiss_user == 0, "6. nobody of the name is dismissed");

	printf("  a no on a closing desktop\n");
	reset(true);
	delivery_verdict(&br, 53, false, "anna", "10.0.0.9", false);
	require(n_dismiss_ticket == 0 && n_dismiss_user == 0, "10. no «still closing» farewell: it would reveal the account exists");
	require(n_verdict == 1 && verdict_ticket == 53 && !verdict_admitted, "11. the normal refusal is delivered");
	require(n_pid == 0 && n_ensure == 0, "12. the closing desktop is not even looked at, no child");

	printf("  nobody waits for the answer\n");
	reset(false);
	delivery_verdict(&br, 54, true, "anna", "10.0.0.9", false);
	require(n_dismiss_ticket == 0 && n_dismiss_user == 0, "13. no dismiss at all (no closing branch)");
	require(n_pid == 0 && n_ensure == 0, "14. the desktop is not looked at, no child");
	require(n_verdict == 1 && verdict_ticket == 54, "15. the verdict still goes to transport_verdict_from()");

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
