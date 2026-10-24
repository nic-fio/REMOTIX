/*
 * test_evict.c — unit test of WHO IS EVICTED when the server is full, and of who still waits for a PAM answer
 * (DECISIONS-11 §11.40; port of 24c7b668, adapted from benches/02-transport-evict-test.c of the abandoned attempt).
 * The REAL src/transport.c is #included (never modified); pick_victim() and transport_awaits_verdict() run on a list of
 * fake connections.  The three questions transport.c asks of webtransport.c (wt_rcp_state, wt_refused_without_pam,
 * wt_awaits_verdict) are renamed to fakes below; everything else transport.c links to is generated as a stub that TRAPS if
 * reached (the method of benches/unit/child-credentials).  The log is benches/fuzz/rcp-msg/stubs_log.c.
 *
 * ⛔ pick_victim() once broke a tie between equally crowded places by the EARLIEST state: 128 IPv4 addresses with one
 *    connection each parked in `wait-credentials` (60 s allowed, no password, no ban) made the owner's login in progress
 *    (no session yet, or `wait-hello`) the victim of every new connection of theirs.  Now, on a tie, a PARKED connection
 *    (older than PARKED_S = 5 s, still before its credentials) goes first, the oldest:
 *   1. the owner's fresh `wait-hello` is NOT evicted for parked strangers;   2. the oldest parked one is;
 *   3. a fresh `(none)` owner is not either;   4. the most crowded place still goes first, parked or not;
 *   5. a `finished` connection goes before anything;   6. a `wait-verdict` while PAM judges, or a logged-in one: never (NULL);
 *   7. among fresh ones the earliest state goes first;   8. among parked ones in different states, the oldest;
 *   9-11. transport_awaits_verdict(): true for the ticket a live connection waits for, false for another, false for a closing one.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree).  Same recipe for
 * test_orphan.c (replace the file name):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=2 -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src -I/albero/benches/fuzz/rcp-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/evict/test_evict.c -o t.o && clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && ./test'
 * Exit status: 0 green, 1 red, 3 not all checks ran.
 */
#define _GNU_SOURCE
#define wt_rcp_state fake_wt_rcp_state
#define wt_refused_without_pam fake_wt_refused_without_pam
#define wt_awaits_verdict fake_wt_awaits_verdict
#include "transport.c"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 11

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

struct fake_w {
	const char *state;
	bool refused_ours;
	uint64_t awaits; /* 0 = none */
};

const char *fake_wt_rcp_state(const wt *w)
{
	return ((const struct fake_w *)(const void *)w)->state;
}

bool fake_wt_refused_without_pam(const wt *w)
{
	return w && ((const struct fake_w *)(const void *)w)->refused_ours;
}

bool fake_wt_awaits_verdict(const wt *w, uint64_t ticket)
{
	const struct fake_w *f = (const struct fake_w *)(const void *)w;
	return f && f->awaits && f->awaits == ticket;
}

static transport *tr;
#define NOW (1000ull * NGTCP2_SECONDS)

/* A connection from `place` (one byte of the /48 key), in `state` (NULL = no
 * session yet), born `age_ms` before NOW; pushed at the HEAD (newest first),
 * so the calls go OLDEST FIRST, as `accept_conn()` builds the real list. */
static connection *add(uint8_t place, const char *state, uint64_t age_ms, bool unlogged)
{
	connection *c = calloc(1, sizeof *c);
	struct fake_w *f = state ? calloc(1, sizeof *f) : NULL;
	if (f)
		f->state = state;
	c->w = (wt *)(void *)f;
	c->unlogged = unlogged;
	c->birth_key[0] = c->birth_key48[0] = place;
	c->born = NOW - age_ms * NGTCP2_MILLISECONDS;
	c->upcoming = tr->prime;
	tr->prime = c;
	return c;
}

static void clear(void)
{
	while (tr->prime) {
		connection *c = tr->prime;
		tr->prime = c->upcoming;
		free(c->w);
		free(c);
	}
}

int main(void)
{
	connection *owner, *oldest, *v, *x;

	setvbuf(stdout, NULL, _IONBF, 0);
	tr = calloc(1, sizeof *tr);
	if (!tr)
		return 3;

	printf("  parked strangers, one per address, and the owner logging in\n");
	oldest = add(1, "wait-credentials", 40000, true);
	add(2, "wait-credentials", 30000, true);
	add(3, "wait-credentials", 20000, true);
	owner = add(4, "wait-hello", 300, true);
	v = pick_victim(tr, NOW);
	require(v && v != owner, "1. the owner's fresh wait-hello is NOT the victim of parked strangers");
	require(v == oldest, "2. the oldest parked connection is");
	clear();
	add(1, "wait-credentials", 40000, true);
	add(2, "wait-credentials", 30000, true);
	owner = add(4, NULL, 100, true);
	v = pick_victim(tr, NOW);
	require(v && v != owner, "3. a fresh owner with no session yet is not either");
	clear();

	printf("  the old rules\n");
	add(1, "wait-credentials", 40000, true);
	x = add(2, "wait-credentials", 2000, true);
	add(2, "wait-hello", 1000, true);
	v = pick_victim(tr, NOW);
	require(v && v->birth_key48[0] == 2,
	        "4. the most crowded place still goes first, even with a parked one elsewhere");
	(void)x;
	clear();
	add(1, "wait-credentials", 40000, true);
	x = add(5, "finished", 100, true);
	v = pick_victim(tr, NOW);
	require(v == x, "5. a finished connection still goes before a parked one");
	clear();
	add(1, "wait-verdict", 40000, true);
	add(2, "active", 40000, false);
	v = pick_victim(tr, NOW);
	require(v == NULL, "6. a wait-verdict while PAM judges, or a logged-in one, never — NULL");
	clear();
	add(2, "wait-credentials", 2000, true);
	x = add(1, NULL, 1000, true);
	v = pick_victim(tr, NOW);
	require(v == x, "7. among fresh ones the earliest state still goes first");
	clear();
	x = add(1, "wait-credentials", 50000, true);
	add(3, NULL, 7000, true);
	add(2, "wait-hello", 6000, true);
	v = pick_victim(tr, NOW);
	require(v == x, "8. among parked ones, whatever the state, the oldest");
	clear();

	printf("  transport_awaits_verdict()\n");
	x = add(1, "wait-verdict", 500, true);
	((struct fake_w *)(void *)x->w)->awaits = 9;
	add(2, "wait-credentials", 500, true);
	require(transport_awaits_verdict(tr, 9), "9. a live connection waits for ticket 9");
	require(!transport_awaits_verdict(tr, 8), "10. nobody waits for ticket 8");
	x->dead_run = true;
	require(!transport_awaits_verdict(tr, 9), "11. a closing connection waits for nothing");
	clear();
	free(tr);

	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
