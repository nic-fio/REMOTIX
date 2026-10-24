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

bool rcp_authenticate_from(const char *user, const char *password, const char *rhost)
{
	(void)user; (void)password; (void)rhost;
	return false;
}
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
	g->n++;
	g->ticket = ticket;
	g->admitted = admitted;
	g->lost = lost;
	snprintf(g->user, sizeof g->user, "%s", user);
	snprintf(g->rhost, sizeof g->rhost, "%s", rhost);
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

	printf("\n%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
