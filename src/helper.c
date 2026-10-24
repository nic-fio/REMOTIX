/*
 * helper.c — the process that queries PAM in place of the single thread.
 *
 * The reason, the three storeys and invariant I3 are written out in full in
 * `helper.h`.  Here are the choices that can only be seen in the code.
 */
#include "helper.h"

#include "log.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

/* ⛔ Declared here and not included: `authentication.c` has no header, and the
 *    same line is already in `webtransport.c`.  ⚠ It is the ONLY function that
 *    touches `libpam` in the whole product, and from today it is called **only
 *    by the grandchild**: in the serving process it is never executed again. */
bool rcp_authenticate_from(const char *user, const char *password,
                      const char *rhost);
bool rcp_rhost_from_provenance(const char *provenance, char *report, size_t cap);

/* ⛔⛔ THIS NUMBER IS NOT THE SESSION CAP, AND MUST NOT FOLLOW IT — 25 Aug
 *      2026, and the line above said the opposite.
 *
 *      It said: *«it is not an arbitrary number: it is the same `MAX_ATTACCATE`
 *      of `rcp.c`»*.  ⛔ **It was not** — they were two independent literals —
 *      and above all **it must not be**: they are two different quantities.
 *
 *        · `RCP_SESSION_CAP` counts the users **served**, and a session
 *          lasts hours;
 *        · this one counts the authentications **in flight at the same
 *          instant**, and a request lasts from 1.0 to 2.2 s (`[M]` B8).
 *
 *      ⇒ With ZERO active sessions there can be seventeen requests in flight
 *        — seventeen people pressing «enter» together are enough — and the
 *        seventeenth would receive `WRONG_CREDENTIALS`, ⛔ **indistinguishable
 *        from a wrong password** (finding **R10-A7**).  And the other way
 *        round: a high session cap has no reason to widen a queue that empties
 *        in two seconds.
 *
 * ⛔ So it stays a number of ITS OWN, written here, and this box exists because
 *    the day `RCP_SESSION_CAP` becomes configurable someone will open this
 *    file to «align it».  It is not aligned: it is sized on the peak of
 *    ARRIVALS, which is another measurement and does not exist today.
 *
 * ⚠ Beyond the ceiling `helper_ask` says no — a no is an answer
 *   compliant with I3, while a bottomless queue would be a way of spawning
 *   processes as long as the machine holds. */
#define MAX_IN_FLIGHT 16

/* ⛔ How long an answer is awaited before calling it «no».  PAM, measured,
 * sits between 1.0 and 2.2 s: eight seconds are four times the worst known
 * case.  ⚠ And there is a SECOND net, in `rcp.c` (`VERDICT_CAP`): two
 * independent nets because this one lives in the process that could be
 * precisely the faulty one. */
#define EXPIRY_MS 8000

/* ⛔ The grandchild cannot live forever: a PAM module stuck on a network that
 * does not answer would keep a process alive at every attempt.  Twenty
 * seconds, that is more than the parent's expiry: this way the «no» always
 * comes from the expiry (which is a fact written in the log) and not from a
 * signal. */
#define GRANDCHILD_ALARM_S 20

struct request {
	uint64_t ticket;
	char user[257];
	char password[1025];
	/* ⭐ PHASE 17 T6: the client's address, bare, for `PAM_RHOST` (like
	 *    sshd).  Empty if unknown: then PAM does not receive it. */
	char rhost[64];
};

struct response {
	uint64_t ticket;
	uint8_t outcome; /* ⛔ 1 and ONLY 1 means admitted */
};

/* ⭐ 24 Oct 2026 (§4.4-bis B): `user` and `rhost` are also what the verdict is
 *    COUNTED with when the connection that asked is gone: the booking made at
 *    `CREDENTIALS` is resolved by name and address, not by session. */
struct flight {
	uint64_t ticket;
	uint64_t expires;
	/* ⛔ The user's NAME, and not their password: the former serves the
	 *    parent to spawn the child when the answer is «yes» (`child.h`), the
	 *    latter is already zeroed by §4.4 before this line exists. */
	char user[257];
	/* ⭐ And the address, which on «yes» goes to the child's PAM session. */
	char rhost[64];
};

struct helper {
	int fd;         /* -1 when the dispatcher is dead or was never born */
	pid_t child;
	uint64_t next_case;
	struct flight flight[MAX_IN_FLIGHT];
	int nflight;
};

/* ------------------------------------------------------------------------ */
/* THE GRANDCHILD — one single PAM transaction, then it dies.               */

static void grandchild(int fd, struct request *r)
{
	struct response out;
	bool ok;

	/* ⛔ The alarm is armed BEFORE calling PAM: arming it after would be
	 *    arming it when the case it exists for has already happened. */
	alarm(GRANDCHILD_ALARM_S);

	ok = rcp_authenticate_from(r->user, r->password, r->rhost);

	out.ticket = r->ticket;
	explicit_bzero(r, sizeof *r);
	/* ⛔ The only place in the program where a «yes» is born, and it is
	 *    written so that a value other than `PAM_SUCCESS` cannot get there:
	 *    `rcp_authenticate()` starts from `admitted = false`. */
	out.outcome = ok ? 1u : 0u;
	/* ⚠ The outcome is written and that is all: if the `send` fails, the
	 *   parent will receive nothing and the request will expire — that is, a
	 *   «no».  No retry, and no «maybe» outcome is written. */
	(void)send(fd, &out, sizeof out, MSG_NOSIGNAL);
	_exit(0);
}

/* ------------------------------------------------------------------------ */
/* THE DISPATCHER — never calls PAM: reads and forks.                       */

static void dispatcher(int fd)
{
	struct request r;

	/* ⛔ If the parent dies, this process dies with it.  Without this, an
	 *    abrupt shutdown of the server would leave an orphan attached to a
	 *    socket nobody reads any more — and no file would say who it is. */
	prctl(PR_SET_PDEATHSIG, SIGTERM);

	/* ⛔ The parent's handlers do not apply here: the parent leaves its loop
	 *    when `stop_requested` becomes 1, and this process never looks at that
	 *    variable.  With the inherited handler a `SIGTERM` would not stop it,
	 *    and whoever shuts the server down would wait for an immortal child. */
	signal(SIGTERM, SIG_DFL);
	signal(SIGINT, SIG_DFL);
	/* ⭐ And the grandchildren are reaped on their own: with `SIGCHLD` at
	 *    `SIG_IGN` the kernel leaves no zombies (POSIX 2001), and this process
	 *    has no `waitpid` loop to forget. */
	signal(SIGCHLD, SIG_IGN);

	for (;;) {
		ssize_t readings = recv(fd, &r, sizeof r, 0);
		if (readings == 0)
			_exit(0); /* the parent has closed: nothing more to do here */
		if (readings < 0) {
			if (errno == EINTR)
				continue;
			_exit(1);
		}
		/* ⛔ A request of the wrong length is not «fixed»: it is thrown away,
		 *    and the request will expire on the parent's side as a no.
		 *    Guessing what was missing is precisely the leniency that hides. */
		if (readings != (ssize_t)sizeof r) {
			explicit_bzero(&r, sizeof r);
			continue;
		}
		/* ⚠ And the string is forcibly terminated: what arrived must be what
		 *   is judged, and a buffer without a final zero would make PAM read
		 *   bytes that were not in the message. */
		r.user[sizeof r.user - 1] = 0;
		r.password[sizeof r.password - 1] = 0;
		r.rhost[sizeof r.rhost - 1] = 0;

		pid_t p = fork();
		if (p == 0)
			grandchild(fd, &r); /* does not return */
		if (p < 0) {
			/* ⛔ No fallback of calling PAM HERE: it would block the
			 *    dispatcher, and with it all the other requests.  Stay
			 *    silent, and the parent will turn the silence into a no at
			 *    expiry. */
		}
		/* ⛔ §4.4: the password is zeroed as soon as it has served.  This is
		 *    the dispatcher's copy, and it lives the time of a `fork`. */
		explicit_bzero(&r, sizeof r);
	}
}

/* ------------------------------------------------------------------------ */
/* THE PARENT                                                                */

helper *helper_turn_on(void)
{
	int sv[2];
	helper *a;

	/* ⛔ `SOCK_SEQPACKET`: message boundaries are kept by the kernel.  See the
	 *    box in `helper.h` — with a stream the framing would be ours, and a
	 *    defect in there would mean «someone else's answer», that is I3 broken
	 *    by a read error. */
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		registro_dice(LOG_STARTUP,
		              "⛔ the PAM helper does NOT start: socketpair: %s.  "
		              "Every authentication will be a NO (invariant I3), and the "
		              "server will say so at every attempt.",
		              strerror(errno));
		return NULL;
	}

	a = (helper *)calloc(1, sizeof *a);
	if (!a) {
		close(sv[0]);
		close(sv[1]);
		return NULL;
	}

	a->child = fork();
	if (a->child < 0) {
		registro_dice(LOG_STARTUP,
		              "⛔ the PAM helper does NOT start: fork: %s.  Every "
		              "authentication will be a NO (invariant I3).",
		              strerror(errno));
		close(sv[0]);
		close(sv[1]);
		free(a);
		return NULL;
	}
	if (a->child == 0) {
		close(sv[0]);
		dispatcher(sv[1]); /* does not return */
		_exit(1);
	}

	close(sv[1]);
	a->fd = sv[0];
	a->next_case = 1;
	/* ⛔ Non-blocking: it is the whole point of this file.  A `send` that
	 *    waits is a wait inside the asynchronous loop — `CODER.md` §4.4 —
	 *    that is, the defect moved instead of cured. */
	fcntl(a->fd, F_SETFL, O_NONBLOCK);

	registro_dice(LOG_STARTUP,
	              "⭐ PAM helper started: pid %ld, anonymous SEQPACKET "
	              "socketpair.  From here on the poll loop NO LONGER calls PAM "
	              "(DECISIONS.md §1.10)",
	              (long)a->child);
	return a;
}

void helper_turn_off(helper *a)
{
	if (!a)
		return;
	if (a->fd >= 0)
		close(a->fd);
	if (a->child > 0) {
		/* ⚠ Closing the socket would be enough (the dispatcher reads 0 and
		 *   exits), but «would be enough» is not «I did it»: the signal and
		 *   the reaping make the shutdown an observable fact instead of a race. */
		kill(a->child, SIGTERM);
		waitpid(a->child, NULL, 0);
	}
	free(a);
}

int helper_descriptor(const helper *a)
{
	return a ? a->fd : -1;
}

int helper_in_flight(const helper *a)
{
	return a ? a->nflight : 0;
}

static void flight_remove(helper *a, int i)
{
	a->flight[i] = a->flight[a->nflight - 1];
	a->nflight--;
}

bool helper_ask(helper *a, const char *user, const char *password,
                     const char *provenance, uint64_t now_ms,
                     uint64_t *ticket)
{
	struct request r;
	ssize_t written;
	uint64_t my;

	*ticket = 0;
	if (!a || a->fd < 0 || !user || !password)
		return false;
	if (a->nflight >= MAX_IN_FLIGHT) {
		registro_dice(REG_RCP,
		              "⛔ %d PAM checks already in flight: this one does NOT leave, and "
		              "whoever asked will receive a NO (I3: failure is a "
		              "no, not a maybe)",
		              a->nflight);
		return false;
	}

	my = a->next_case;
	memset(&r, 0, sizeof r);
	r.ticket = my;
	/* ⛔ `snprintf` and not `strcpy`: the ranges have already been enforced by
	 *    `rcp.c` (§4.4: user 1..256, password 1..1024), and this is the second
	 *    wall — the one that holds even if the first changes. */
	snprintf(r.user, sizeof r.user, "%s", user);
	snprintf(r.password, sizeof r.password, "%s", password);
	(void)rcp_rhost_from_provenance(provenance, r.rhost, sizeof r.rhost);

	written = send(a->fd, &r, sizeof r, MSG_NOSIGNAL);
	/* ⛔ §4.4: the password is zeroed as soon as it has served.  This is the
	 *    sender's copy, and it lives the time of a `send`.  ⚠ And the request
	 *    number is already safe in `my`: reading it again from `r` after the
	 *    `explicit_bzero` would be reading the zero we have just put there — and the
	 *    answer would no longer find its request in flight. */
	explicit_bzero(&r, sizeof r);

	if (written != (ssize_t)sizeof r) {
		registro_dice(REG_RCP,
		              "⛔ the question to PAM did not leave (%zd bytes of %zu: "
		              "%s): NO waiting and no guessing — whoever asked "
		              "receives a NO",
		              written, sizeof r, strerror(errno));
		return false;
	}

	a->flight[a->nflight].ticket = my;
	a->flight[a->nflight].expires = now_ms + EXPIRY_MS;
	snprintf(a->flight[a->nflight].user, sizeof a->flight[a->nflight].user, "%s",
	         user);
	(void)rcp_rhost_from_provenance(provenance, a->flight[a->nflight].rhost,
	                               sizeof a->flight[a->nflight].rhost);
	a->nflight++;
	*ticket = my;
	a->next_case++;
	return true;
}

/* ⛔ The answer is accepted ONLY if it belongs to a request really in flight.
 * An answer for an unknown request — or the second answer for the same one —
 * is discarded and written: it is the only way for «I received two verdicts»
 * not to become «the last one wins». */
static bool flight_consumes(helper *a, uint64_t ticket, char *user,
                         size_t cap, char *rhost, size_t rcap)
{
	for (int i = 0; i < a->nflight; i++) {
		if (a->flight[i].ticket == ticket) {
			/* ⛔ The name is copied BEFORE removing the request: `flight_remove()`
			 *    writes the last one of the table over it, and reading it
			 *    afterwards would mean delivering another user's name — which
			 *    here is the worst possible defect. */
			if (user && cap)
				snprintf(user, cap, "%s", a->flight[i].user);
			if (rhost && rcap)
				snprintf(rhost, rcap, "%s", a->flight[i].rhost);
			flight_remove(a, i);
			return true;
		}
	}
	if (user && cap)
		user[0] = 0;
	if (rhost && rcap)
		rhost[0] = 0;
	return false;
}

static void dies(helper *a, const char *why, HelperVerdict delivery,
                  void *ctx)
{
	registro_dice(REG_RCP,
	              "⛔ the PAM helper is gone (%s): the %d checks in "
	              "flight become NO, and every following attempt will be a NO "
	              "(invariant I3).  ⚠ It is not «wrong password»: it is «PAM "
	              "could not judge», and the server does not keep it to itself.",
	              why, a->nflight);
	if (a->fd >= 0) {
		close(a->fd);
		a->fd = -1;
	}
	/* ⛔⭐ AND IT IS REAPED, AT ONCE — found on 12 Aug 2026 by the bench
	 *     `02-pam-i3.py`, which killed the helper and then got the answer
	 *     «the pid is still alive after SIGKILL».
	 *
	 *     It was not alive: it was a **zombie**.  The parent did not reap it
	 *     until `helper_turn_off()`, that is until the server's shutdown, and
	 *     in `/proc` a zombie and a live process have **the same face**.
	 *
	 * ⚠ The damage was not the extra entry in the process table: it was that
	 *   whoever diagnoses — or a bench — could not tell «the helper is dead»
	 *   from «the helper does not die».  It is `LESSONS.md` §1.9 applied to
	 *   processes: two different facts with the same look.
	 *
	 * ⛔ `WNOHANG`: here we are inside the asynchronous loop, and `CODER.md`
	 *    §4.4 forbids waiting.  If it had not finished yet we retry at the
	 *    next round, and in any case `helper_turn_off()` settles the account. */
	if (a->child > 0 && waitpid(a->child, NULL, WNOHANG) == a->child) {
		registro_dice(REG_RCP,
		              "⭐ and helper %ld has been reaped: from now on «dead» "
		              "and «alive» no longer have the same face in /proc",
		              (long)a->child);
		a->child = 0;
	}
	while (a->nflight > 0) {
		uint64_t p = a->flight[0].ticket;
		char chi[257];
		snprintf(chi, sizeof chi, "%s", a->flight[0].user);
		flight_remove(a, 0);
		if (delivery)
			delivery(ctx, p, false, chi, "");
	}
}

void helper_move(helper *a, HelperVerdict delivery, void *ctx)
{
	if (!a || a->fd < 0)
		return;
	for (;;) {
		struct response ri;
		char chi[257];
		char da[64];
		ssize_t readings = recv(a->fd, &ri, sizeof ri, 0);
		if (readings == 0) {
			dies(a, "the socket was closed from its side", delivery, ctx);
			return;
		}
		if (readings < 0) {
			if (errno == EINTR)
				continue;
			if (errno == EAGAIN || errno == EWOULDBLOCK)
				return; /* nothing else to read now */
			dies(a, strerror(errno), delivery, ctx);
			return;
		}
		if (readings != (ssize_t)sizeof ri) {
			/* ⛔ A message of the wrong length is not interpreted.  The
			 *    request will stay in flight and expire: that is, a no. */
			registro_dice(REG_RCP,
			              "⛔ helper answer %zd bytes long instead of "
			              "%zu: DISCARDED.  The request will expire, and the expiry is "
			              "a NO",
			              readings, sizeof ri);
			continue;
		}
		if (!flight_consumes(a, ri.ticket, chi, sizeof chi, da, sizeof da)) {
			registro_dice(REG_RCP,
			              "⛔ answer for request %llu, which is not in flight "
			              "(already expired, or already answered): DISCARDED",
			              (unsigned long long)ri.ticket);
			continue;
		}
		/* ⛔⭐ HERE, AND ONLY HERE, A «YES» CAN ENTER THE SERVER — and it goes
		 *     through a comparison with `1`, not through a `!= 0`: a dirty
		 *     byte, a memory leftover or a 255 are a NO. */
		if (delivery)
			delivery(ctx, ri.ticket, ri.outcome == 1u, chi, da);
	}
}

void helper_expired(helper *a, uint64_t now_ms, HelperVerdict delivery,
                      void *ctx)
{
	if (!a)
		return;
	for (int i = 0; i < a->nflight;) {
		if (now_ms >= a->flight[i].expires) {
			uint64_t p = a->flight[i].ticket;
			char chi[257];
			snprintf(chi, sizeof chi, "%s", a->flight[i].user);
			flight_remove(a, i);
			registro_dice(REG_RCP,
			              "⛔ request %llu received no answer in %d ms: "
			              "the grandchild died or PAM got stuck.  ⭐ The "
			              "expiry counts as NO (invariant I3), and since 24 Oct "
			              "2026 it COUNTS as a failed attempt of §4.4-bis (B): an "
			              "attempt without a verdict is not a free attempt",
			              (unsigned long long)p, EXPIRY_MS);
			if (delivery)
				delivery(ctx, p, false, chi, "");
		} else {
			i++;
		}
	}
}
