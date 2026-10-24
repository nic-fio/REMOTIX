/*
 * test_orphan.c — a yes nobody waits for starts no desktop (DECISIONS-11 §11.40 / §11.39; port of 24c7b668, adapted from
 * benches/02-main-orphan-yes-test.c of the abandoned attempt).
 * The REAL src/main.c is #included (its `main` renamed, never modified) and delivery_verdict() runs against fakes of the
 * children, the transport, the budget and wt_dismiss_user (the real ones stay in their objects, unused: here they are never
 * linked and anything else reached TRAPS).  The log is benches/fuzz/rcp-msg/stubs_log.c.
 *
 * ⛔ delivery_verdict() once looked up, spawned or woke the user's desktop for every PAM yes, and only then asked who was
 *    waiting: a client that hung up while PAM judged left a desktop started for nobody.  Now it asks
 *    transport_awaits_verdict() first:
 *   1-3. a yes nobody waits for: the user's desktop is not looked at, none is spawned, and the verdict still goes to
 *        transport_verdict_from() (which counts it as an orphan and logs «nobody»);
 *   4-6. a yes somebody waits for: the child is made, once, the verdict is delivered, nobody is sent away;
 *   7-8. a no: no child, the verdict delivered.
 *
 * BUILD AND RUN: the same command as test_evict.c (header of that file) with test_orphan.c in place of test_evict.c; the
 * link needs the same libraries and the same generated trap stubs.
 * Exit status: 0 green, 1 red, 3 not all checks ran.
 */
#define _GNU_SOURCE
#define main remotix_main
#define rcp_cap fake_rcp_cap
#define budget_verdict_line fake_budget_verdict_line
#define children_pid_of fake_children_pid_of
#define children_ensure_from fake_children_ensure_from
#define children_count fake_children_count
#define children_ask_stage fake_children_ask_stage
#define transport_verdict_from fake_transport_verdict_from
#define transport_awaits_verdict fake_transport_awaits_verdict
#define wt_dismiss_user fake_wt_dismiss_user
#define budget_on fake_budget_on
#include "main.c"
#undef main

#include <stdio.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 8

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

static int n_pid, n_ensure, n_verdict, n_dismiss;
static bool awaits;
static uint8_t last_resumed = 0xFF;

pid_t fake_children_pid_of(const children *f, const char *user)
{
	(void)f;
	(void)user;
	n_pid++;                      /* "the user's desktop is looked at" */
	return 0;
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
	(void)ticket;
	(void)admitted;
	(void)user;
	(void)rhost;
	(void)lost;
	n_verdict++;
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
	n_dismiss++;
	return 0;
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

static void reset(bool waiting)
{
	n_pid = n_ensure = n_verdict = n_dismiss = 0;
	last_resumed = 0xFF;
	awaits = waiting;
}

int main(void)
{
	struct bridge br = {NULL, NULL};   /* t, f: only the fakes see them */

	setvbuf(stdout, NULL, _IONBF, 0);

	printf("  a yes nobody waits for\n");
	reset(false);
	delivery_verdict(&br, 41, true, "anna", "10.0.0.9", false);
	require(n_ensure == 0, "1. no child is spawned for it");
	require(n_pid == 0, "2. the user's desktop is not even looked at");
	require(n_verdict == 1, "3. the verdict still goes to transport_verdict() (it logs «nobody»)");

	printf("  a yes somebody waits for\n");
	reset(true);
	delivery_verdict(&br, 42, true, "anna", "10.0.0.9", false);
	require(n_ensure == 1, "4. the child is made, once");
	require(n_verdict == 1 && !last_resumed, "5. the verdict is delivered (not RESUMED: the child was just made)");
	require(n_dismiss == 0, "6. nobody is sent away (no farewell)");

	printf("  a no\n");
	reset(true);
	delivery_verdict(&br, 43, false, "anna", "10.0.0.9", false);
	require(n_ensure == 0, "7. no child for a no");
	require(n_verdict == 1, "8. the no is delivered");

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
