/*
 * test_helper.c — unit test of how src/helper.c delivers a verdict (§4.4-bis B, 24 Oct 2026): the NAME and the ADDRESS of the
 * request in flight must come with EVERY delivery — answered, expired by the PAM timeout, and the helper dead — because with the
 * connection gone the booking made at CREDENTIALS is resolved with them.  And only the dead helper is `lost` (our defect: nothing
 * counted); the PAM timeout is not (it counts).
 *
 * HOW: the REAL src/helper.c is #included (never modified).  The helper is built by hand over a socketpair (SOCK_SEQPACKET, like
 * helper_turn_on() makes): this test plays the dispatcher on the other end.  rcp_authenticate_from() / rcp_rhost_from_provenance()
 * (authentication.c, which needs PAM) are replaced by two stubs.  The log is benches/fuzz/rcp-msg/stubs_log.c.
 *
 * BUILD AND RUN: see test.c (same image, same flags); compile this file instead of test.c, with stubs_log.c, and run ./test_helper.
 */
#include "helper.c"

#include <stdio.h>
#include "common.h"

int rcp_authenticate_judged(const char *user, const char *password, const char *rhost)
{
	(void)user; (void)password; (void)rhost;
	return 0;
}
static uint64_t locked_mark;
void rcp_refusal_locked(uint64_t ticket) { locked_mark = ticket; }
/* D4b: the bracket of «not checked»; the delivery records what it saw */
static uint64_t unchecked_mark, unchecked_seen;
void rcp_refusal_unchecked(uint64_t ticket) { unchecked_mark = ticket; }
bool rcp_rhost_from_provenance(const char *provenance, char *report, size_t cap)
{
	/* the form of authentication.c: «[address]:port» -> «address» */
	const char *c;
	report[0] = 0;
	if (!provenance || provenance[0] != '[' || !(c = strchr(provenance, ']')))
		return false;
	size_t n = (size_t)(c - provenance - 1);
	if (n >= cap)
		return false;
	memcpy(report, provenance + 1, n);
	report[n] = 0;
	return true;
}

/* the stub of rcp.c's flag (§11.39 addendum): the test decides who is «known» */
static bool stub_known;
bool rcp_asking_for_known_key(void) { return stub_known; }

static uint64_t mark_seen;
static int checks, bad;
#define CHECK(cond, ...)                                                      \
	do {                                                                  \
		checks++;                                                     \
		if (!(cond)) {                                                \
			bad++;                                                \
			printf("  FAIL %s:%d  %s  -- ", __FILE__, __LINE__, #cond); \
			printf(__VA_ARGS__);                                  \
			printf("\n");                                         \
		}                                                             \
	} while (0)

struct got {
	int n;
	uint64_t ticket;
	bool admitted, lost;
	char user[257], rhost[64];
};
static void deliver(void *ctx, uint64_t ticket, bool admitted, const char *user, const char *rhost, bool lost)
{
	struct got *g = ctx;
	mark_seen = locked_mark; /* the mark of §11.47 B, as the delivery sees it */
	unchecked_seen = unchecked_mark; /* D4b: and the mark of «not checked» */
	g->n++;
	g->ticket = ticket;
	g->admitted = admitted;
	g->lost = lost;
	snprintf(g->user, sizeof g->user, "%s", user);
	snprintf(g->rhost, sizeof g->rhost, "%s", rhost);
}

struct root_got {
	int n;
	uint64_t ticket;
	int outcome;
	char user[257], rhost[64];
};
static void on_outcome(void *c, uint64_t ticket, int outcome, const char *user, const char *rhost)
{
	struct root_got *r = c;
	r->n++;
	r->ticket = ticket;
	r->outcome = outcome;
	snprintf(r->user, sizeof r->user, "%s", user);
	snprintf(r->rhost, sizeof r->rhost, "%s", rhost);
}

static void make(helper *h, int *peer)
{
	int sv[2];
	CHECK(socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) == 0, "socketpair");
	int fl = fcntl(sv[0], F_GETFL);
	fcntl(sv[0], F_SETFL, fl | O_NONBLOCK);
	memset(h, 0, sizeof *h);
	h->fd = sv[0];
	h->child = 0;
	*peer = sv[1];
}

int main(void)
{
	helper h;
	int peer;
	struct got g;
	uint64_t t;

	/* 1. answered: the dispatcher answers «no» */
	make(&h, &peer);
	memset(&g, 0, sizeof g);
	CHECK(helper_ask(&h, "alice", "pw", "[2001:db8:1:2::9]:4433", 1000, &t), "ask");
	struct request rq;
	CHECK(recv(peer, &rq, sizeof rq, 0) == (ssize_t)sizeof rq, "the dispatcher gets the request");
	struct response rs = {rq.ticket, 0};
	CHECK(send(peer, &rs, sizeof rs, 0) == (ssize_t)sizeof rs, "answer");
	helper_move(&h, deliver, &g);
	CHECK(g.n == 1 && !g.admitted && !g.lost && strcmp(g.user, "alice") == 0 && strcmp(g.rhost, "2001:db8:1:2::9") == 0,
	      "answered: n=%d user=%s rhost=%s lost=%d", g.n, g.user, g.rhost, g.lost);
	close(peer); close(h.fd);

	/* 2. the PAM timeout: delivered with name AND address, not lost */
	make(&h, &peer);
	memset(&g, 0, sizeof g);
	CHECK(helper_ask(&h, "bob", "pw", "[1.2.3.4]:55", 1000, &t), "ask");
	helper_expired(&h, 1000 + 7999, deliver, &g);
	CHECK(g.n == 0, "not expired yet");
	helper_expired(&h, 1000 + 8000, deliver, &g);
	CHECK(g.n == 1 && g.ticket == t && !g.admitted && !g.lost && strcmp(g.user, "bob") == 0 && strcmp(g.rhost, "1.2.3.4") == 0,
	      "expired: n=%d user=%s rhost=«%s» lost=%d", g.n, g.user, g.rhost, g.lost);
	CHECK(helper_in_flight(&h) == 0, "and the flight record is gone");
	close(peer); close(h.fd);

	/* 3. the helper dies: every request in flight is delivered with its address, and lost */
	make(&h, &peer);
	CHECK(helper_ask(&h, "carol", "pw", "[1.2.3.4]:1", 1000, &t), "ask 1");
	close(peer);                                     /* the dispatcher is gone: recv() gives 0 */
	memset(&g, 0, sizeof g);
	helper_move(&h, deliver, &g);
	CHECK(g.n == 1 && g.lost && !g.admitted && strcmp(g.user, "carol") == 0 && strcmp(g.rhost, "1.2.3.4") == 0,
	      "dead helper: n=%d user=%s rhost=«%s» lost=%d", g.n, g.user, g.rhost, g.lost);
	CHECK(h.fd < 0 && helper_in_flight(&h) == 0, "the helper is closed and nothing stays in flight");

	/* 4. the places kept for a known key (ported from 4d9eb72b): an unknown key gets 14 of the 16, a known one all 16 */
	make(&h, &peer);
	stub_known = false;
	int taken = 0;
	for (int i = 0; i < 16; i++)
		if (helper_ask(&h, "dave", "pw", "[5.6.7.8]:1", 1000, &t))
			taken++;
	CHECK(taken == 14 && helper_in_flight(&h) == 14, "an unknown key takes 14 places (got %d)", taken);
	CHECK(!helper_ask(&h, "dave", "pw", "[5.6.7.8]:1", 1000, &t), "the 15th ask of an unknown key is refused");
	stub_known = true;
	CHECK(helper_ask(&h, "erin", "pw", "[9.9.9.9]:1", 1000, &t), "a known key gets the 15th place");
	CHECK(helper_ask(&h, "erin", "pw", "[9.9.9.9]:1", 1000, &t), "and the 16th");
	CHECK(!helper_ask(&h, "erin", "pw", "[9.9.9.9]:1", 1000, &t), "but not a 17th: 16 is the ceiling for everybody");
	stub_known = false;
	close(peer); close(h.fd);

	/* 5. §11.47 B (ported from 249c534a): outcome 2 = refused while pam_faillock had the account locked — a NO, marked for
	 *    rcp.c for the length of THAT delivery only; outcome 0 is not marked; 1 is the only yes */
	for (int oc = 0; oc <= 3; oc++) {
		struct request rq2;
		make(&h, &peer);
		memset(&g, 0, sizeof g);
		mark_seen = 77;
		unchecked_seen = 77;
		CHECK(helper_ask(&h, "frank", "pw", "[1.2.3.4]:9", 1000, &t), "ask (outcome %d)", oc);
		CHECK(recv(peer, &rq2, sizeof rq2, 0) == (ssize_t)sizeof rq2, "the dispatcher gets the request");
		struct response rs2 = {rq2.ticket, (uint8_t)oc};
		CHECK(send(peer, &rs2, sizeof rs2, 0) == (ssize_t)sizeof rs2, "answer");
		helper_move(&h, deliver, &g);
		CHECK(g.n == 1 && g.admitted == (oc == 1), "outcome %d: admitted only for 1 (n=%d admitted=%d)", oc, g.n, g.admitted);
		CHECK(mark_seen == (oc == 2 ? g.ticket : 0), "outcome %d: the locked mark is %s during the delivery (saw %llu)", oc,
		      oc == 2 ? "the ticket" : "0", (unsigned long long)mark_seen);
		CHECK(locked_mark == 0, "outcome %d: and it is cleared after", oc);
		/* D3: outcome 3 = «not checked» (the dispatcher's own cap): a no that is OURS — delivered `lost`, like the dead helper */
		CHECK(g.lost == (oc == 3), "outcome %d: lost is %d (only 3 is «not checked»)", oc, g.lost);
		/* D4b: only outcome 3 is delivered inside the rcp_refusal_unchecked(ticket) bracket, and it is closed after */
		CHECK(unchecked_seen == (oc == 3 ? g.ticket : 0), "outcome %d: the unchecked mark during the delivery is %s (saw %llu)", oc,
		      oc == 3 ? "the ticket" : "0", (unsigned long long)unchecked_seen);
		CHECK(unchecked_mark == 0, "outcome %d: and the unchecked mark is cleared after", oc);
		close(peer); close(h.fd);
	}

	/* 6. D3 (§11.50): the ROOT SIDE's helper — nothing of rcp.c is touched, every end is ONE call of the callback:
	 *    1 yes, 0 no, 2 locked, 3 not checked (the dispatcher's answer 3, the dead helper), 4 expired (the PAM timeout: counts) */
	{
		struct root_got rg;
		memset(&rg, 0, sizeof rg);
		for (int oc = 0; oc <= 3; oc++) {
			struct request rq3;
			make(&h, &peer);
			h.root = true;
			h.outcome_cb = on_outcome;
			h.outcome_ctx = &rg;
			memset(&rg, 0, sizeof rg);
			mark_seen = 77;
			CHECK(helper_ask_bare(&h, "gina", "pw", "9.9.9.9", 1000, &t), "root: ask_bare (outcome %d)", oc);
			CHECK(recv(peer, &rq3, sizeof rq3, 0) == (ssize_t)sizeof rq3 && strcmp(rq3.rhost, "9.9.9.9") == 0,
			      "root: the dispatcher gets the bare rhost as it is");
			struct response rs3 = {rq3.ticket, (uint8_t)oc};
			CHECK(send(peer, &rs3, sizeof rs3, 0) == (ssize_t)sizeof rs3, "root: answer");
			helper_move(&h, deliver, &g);
			CHECK(rg.n == 1 && rg.outcome == oc && strcmp(rg.user, "gina") == 0 && strcmp(rg.rhost, "9.9.9.9") == 0,
			      "root: outcome %d reaches the callback once (n=%d got %d)", oc, rg.n, rg.outcome);
			CHECK(mark_seen == 77, "root: rcp.c is not touched (no locked mark)");
			close(peer); close(h.fd);
		}
		/* the PAM timeout is outcome 4 (expired, it counts); the dead helper is 3 (not checked, ours) */
		make(&h, &peer);
		h.root = true;
		h.outcome_cb = on_outcome;
		h.outcome_ctx = &rg;
		memset(&rg, 0, sizeof rg);
		CHECK(helper_ask_bare(&h, "hal", "pw", "1.1.1.1", 1000, &t), "root: ask for the timeout");
		helper_expired(&h, 1000 + 8000, NULL, NULL);
		CHECK(rg.n == 1 && rg.outcome == 4 && rg.ticket == t, "root: the PAM timeout is outcome 4 (expired: counts), not 3 (free)");
		CHECK(helper_ask_bare(&h, "ivy", "pw", "2.2.2.2", 1000, &t), "root: ask for the death");
		close(peer);
		helper_move(&h, NULL, NULL);
		CHECK(rg.n == 2 && rg.outcome == 3 && strcmp(rg.user, "ivy") == 0 && h.fd < 0 && helper_in_flight(&h) == 0,
		      "root: the dead helper is outcome 3, once, nothing left in flight");
		/* a root helper has no places kept for a known key: all 16 */
		make(&h, &peer);
		h.root = true;
		stub_known = false;
		taken = 0;
		for (int i = 0; i < 17; i++)
			if (helper_ask_bare(&h, "jo", "pw", "3.3.3.3", 1000, &t))
				taken++;
		CHECK(taken == 16, "root: 16 places for everybody (got %d)", taken);
		close(peer); close(h.fd);
	}

	printf("\n%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
