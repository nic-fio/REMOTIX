/*
 * helper.c — the process that queries PAM in place of the single thread.
 *
 * The reason, the three storeys and invariant I3 are written out in full in
 * `helper.h`.  Here are the choices that can only be seen in the code.
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE /* close_range() */
#endif
#include "helper.h"

#include "log.h"
#include "rootside.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;

/* ⛔ Declared here and not included: `authentication.c` has no header, and the
 *    same line is already in `webtransport.c`.  ⚠ It is the ONLY function that
 *    touches `libpam` in the whole product, and from today it is called **only
 *    by the grandchild**: in the serving process it is never executed again. */
/* ⭐ §11.47 B: 1 admitted, 2 refused while `pam_faillock` had the account
 *    locked, 0 any other refusal — the byte `outcome` below. */
int rcp_authenticate_judged(const char *user, const char *password,
                            const char *rhost);
void rcp_refusal_locked(uint64_t ticket); /* rcp.c / rcp.h */
void rcp_log_tag(const char *user, char out[8]); /* rcp.c / rcp.h (R3); weak: the root side does not link rcp.c */
#pragma weak rcp_log_tag
void rcp_refusal_unchecked(uint64_t ticket); /* rcp.c / rcp.h (D4b) */
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

/* ⛔⭐ AND TWO OF THEM ARE KEPT FOR A KEY THAT LOGGED IN LATELY — 15 Oct 2026,
 *     `DECISIONS.md` §11.39 addendum (ported from 4d9eb72b).  The 16 places are
 *     shared by every address, and a few fresh addresses rotating keep them
 *     full: the owner read `0x0E` for as long as the flood lasted.  ⇒ An unknown
 *     key gets `MAX_IN_FLIGHT - RESERVED_FOR_KNOWN`; a key that `rcp.c` saw
 *     admitted during the last 30 days (`rcp_asking_for_known_key()`) gets all 16. */
#define RESERVED_FOR_KNOWN 2
bool rcp_asking_for_known_key(void); /* rcp.c / rcp.h */

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
	/* ⭐ R3 (25 Oct 2026): the 6-hex tag of `user` (`rcp_log_tag()`), computed by the serving process, which holds the log secret.  The
	 *    grandchild is a fresh image and has none; it puts this in the environment so `why_no()` writes `unknown user [tag]` and never
	 *    the typed name.  Empty = no tag (root side, where rcp.c is not linked). */
	char tag[8];
};

struct response {
	uint64_t ticket;
	/* ⛔ 1 and ONLY 1 means admitted.  ⭐ 2 (§11.47 B, 15 Oct 2026): refused
	 *    while `pam_faillock` had the account locked — a NO like 0, which
	 *    `rcp.c` may leave out of the §4.4-bis count (`rcp_refusal_locked()`);
	 *    every other value is a plain no. */
	uint8_t outcome;
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

/* ⛔⭐ A DEAD HELPER IS STARTED AGAIN — 15 Oct 2026, from review of 963afb42
 *     (ported to 1.5 as step D3 of DECISIONS.md §11.50).
 *
 *     Until D3 `dies()` closed the socket and that was all: the helper was
 *     never started again, and EVERY later login was refused at once
 *     (`helper_ask()` -> false) until the whole server was restarted — one
 *     crash of a PAM module locked everybody out.
 *
 *     Now `helper_expired()`, which the loop calls at every round (at least
 *     once a second), reaps the dead dispatcher and starts a new one after a
 *     pause that doubles at every death in a row: 1 s, 2 s, 4 s … up to
 *     `RESTART_CAP_MS`.  ⚠ The pause is what keeps a helper that dies at once
 *     (a broken PAM stack, no memory) from becoming a fork loop.
 *
 *   · «in a row» = the helper died before living `STABLE_MS`: one that lived
 *     longer starts the count again from 1 s;
 *   · after `LOUD_AFTER` deaths in a row the server says so LOUDLY (⛔) at
 *     every further death, and goes on trying every `RESTART_CAP_MS` — it does
 *     not stop trying, because a PAM stack repaired by the administrator must
 *     be picked up without a restart;
 *   · while the helper is down `helper_ask()` returns false: whoever asked
 *     gets the refusal that is OURS (not counted towards the ban), exactly as
 *     for the checks that were in flight at the death (`lost`, see `dies()`).
 *
 * ⛔ The privilege model does not change: the new dispatcher is started by the
 *    same process, as the same user, with the same anonymous SEQPACKET pair,
 *    and every PAM transaction still lives in a grandchild with its alarm.
 *    ⚠ The only difference is WHEN it is started: late, from a server that by
 *    then holds the listeners, the ban file, the children's sockets.  ⇒ The
 *    new dispatcher closes every descriptor but 0, 1, 2 and its own end
 *    (`close_range`, see `spawn()`) — otherwise it would hold the port after
 *    the server's death, which is exactly what `main.c` starts it early to
 *    avoid.
 *
 * ⛔⭐ AND IT IS RE-EXECUTED, NOT ONLY FORKED — 15 Oct 2026, review of
 *     c7e86ead (finding 1).  A `fork()` copies the whole MEMORY too, and the
 *     descriptors are the small half of it: a dispatcher forked from the
 *     running server carried a copy of its heap — the TLS private keys, the
 *     session secrets, old buffers with other users' passwords, clipboard
 *     text — into itself and into EVERY PAM grandchild, and a PAM module
 *     that crashed would have dumped all of it into a root core file.  At
 *     boot `main.c` forks it before the keys are loaded precisely to avoid
 *     this; a restart cannot choose its moment.
 *   ⇒ `spawn()` forks and at once `execve()`s `/proc/self/exe --pam-helper`
 *     with its end of the pair on descriptor 3: the dispatcher starts from a
 *     FRESH memory image of this same binary, and `main()` sends
 *     `--pam-helper` to `helper_main()` before reading any option,
 *     certificate or key.  ⭐ The boot start takes the same road: one code
 *     path.
 *   · `/proc/self/exe` and not a path: it is the SAME file the server runs
 *     (the same inode, even if a package upgrade replaced it on disk), so
 *     the request/answer layout on the socket is the same on both ends;
 *   · same user, same environment, same pair, same grandchild alarm: only the
 *     memory is new;
 *   · `--journal` / `--verbose` cross the `exec` on the command line, as for
 *     the child (`child.c`): the grandchild's «why PAM said no» lines land
 *     where they did before;
 *   · if the `exec` fails the forked copy exits at once with 127 — it never
 *     goes on as a forked dispatcher — and the death is restarted like any
 *     other, with the pause. */
#define RESTART_FIRST_MS 1000
#define RESTART_CAP_MS 60000
#define STABLE_MS 60000
#define LOUD_AFTER 5

struct helper {
	int fd;         /* -1 when the dispatcher is dead or was never born */
	pid_t child;    /* 0 when there is no process to reap */
	bool reap_hold; /* sigchld.h: true = no SIGCHLD since the last scan: skip `waitpid()` this round (false = always) */
	uint64_t next_case;
	struct flight flight[MAX_IN_FLIGHT];
	int nflight;
	/* ⭐ The restart (box above).  Times are `helper_expired()`'s clock. */
	uint64_t born_ms;     /* when this dispatcher was seen alive first; 0 = not yet */
	uint64_t restart_at;  /* 0 = no restart scheduled */
	int deaths_in_row;
	int restarts;         /* how many times it was started again, for the log */
	bool killed;          /* SIGKILL already sent to a dispatcher not yet reaped */
	/* ⭐ Transient `recv` errors in `helper_move()`, rate-limited in the log. */
	time_t recv_err_logged; /* CLOCK_MONOTONIC seconds of the last line; 0 = never */
	int recv_errors;
	/* ⭐⭐ 1.5 (DECISIONS.md §11.50, step D3) — the ROOT SIDE's shape: the real
	 *    dispatcher, but nothing of `rcp.c` is called; every request in flight
	 *    ends in ONE call of `outcome_cb` (also «not checked»). */
	bool root;
	HelperOutcome outcome_cb;
	void *outcome_ctx;
	/* ⭐ 1.5 (§11.50, D-remote): the NETWORK SIDE's shape — no dispatcher here: the questions go to the root side
	 *    as AUTH and the answers come back as VERDICT (`rootside.h`); the table in flight, the bounds and the
	 *    delivery to `rcp.c` stay as they were.  Set only when `rootside_attached()`: never in the single-process
	 *    server. */
	bool remote;
	HelperVerdict delivery;     /* remote: the delivery of the `helper_move()` in progress */
	void *delivery_ctx;
	bool lost_told;
};

/* ⭐ 1.5: referenced WEAKLY, so the harnesses that `#include` this file without `rootside.c` still link (and there
 *    `remote` is never true). */
#pragma weak rootside_attached
#pragma weak rootside_descriptor
#pragma weak rootside_lost
#pragma weak rootside_move
#pragma weak rootside_auth
#pragma weak rootside_hook_verdict

static void on_root_verdict(void *ctx, uint64_t request, int outcome);

/* ------------------------------------------------------------------------ */
/* THE GRANDCHILD — one single PAM transaction, then it dies.               */

static void grandchild(int fd, struct request *r)
{
	struct response out;
	int judged;

	/* ⛔ The alarm is armed BEFORE calling PAM: arming it after would be
	 *    arming it when the case it exists for has already happened. */
	alarm(GRANDCHILD_ALARM_S);
	/* ⛔ The whole struct zeroed first: its 7 padding bytes went out carrying
	 *    this process's stack. */
	memset(&out, 0, sizeof out);

	/* ⭐ R3: the tag for the log line of `why_no()` (authentication.c); a value that is not 6 hex is ignored there. */
	r->tag[sizeof r->tag - 1] = 0;
	if (r->tag[0])
		(void)setenv("REMOTIX_PAM_LOG_TAG", r->tag, 1);
	else
		(void)unsetenv("REMOTIX_PAM_LOG_TAG"); /* no tag: a value inherited from the server's environment must not be used */
	judged = rcp_authenticate_judged(r->user, r->password, r->rhost);

	out.ticket = r->ticket;
	explicit_bzero(r, sizeof *r);
	/* ⛔ The only place in the program where a «yes» is born, and it is
	 *    written so that a value other than `PAM_SUCCESS` cannot get there:
	 *    `rcp_authenticate()` starts from `admitted = false`. */
	out.outcome = judged == 1 ? 1u : judged == 2 ? 2u : 0u;
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
	int alive = 0;

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
	/* ⚠ And those the parent sets AFTER the first start (`children_turn_on()`
	 *   installs SIGUSR1/SIGUSR2): a restarted dispatcher must be the same
	 *   process as the one started at boot. */
	signal(SIGUSR1, SIG_DFL);
	signal(SIGUSR2, SIG_DFL);
	signal(SIGHUP, SIG_DFL);
	/* ⭐ The grandchildren are COUNTED, so the dispatcher holds its own cap of
	 *    `MAX_IN_FLIGHT` whoever writes on the socket — before, `SIGCHLD` was
	 *    `SIG_IGN` and every request was a fork.  They are reaped here,
	 *    `WNOHANG`, before each new one. */
	signal(SIGCHLD, SIG_DFL);

	for (;;) {
		/* ⭐ The finished grandchildren are reaped within a second, not at
		 *    the next request: an idle server kept the last one a zombie for
		 *    hours (`[M]` 24-privsep-soak.sh, 16 Oct 2026).  Waiting stays in
		 *    `poll`, so the recv below never blocks for long. */
		while (alive > 0 && waitpid(-1, NULL, WNOHANG) > 0)
			alive--;
		{
			struct pollfd pf = { fd, POLLIN, 0 };
			int pr = poll(&pf, 1, alive > 0 ? 1000 : -1);
			if (pr == 0 || (pr < 0 && errno == EINTR))
				continue;
		}
		/* ⛔ `MSG_TRUNC`: the true length, so a request LONGER than one is
		 *    seen as wrong below instead of judged cut (as in `helper_move()`). */
		ssize_t readings = recv(fd, &r, sizeof r, MSG_TRUNC);
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

		while (alive > 0 && waitpid(-1, NULL, WNOHANG) > 0)
			alive--;
		/* ⛔ The cap is TWICE the parent's ceiling, on purpose.  The parent
		 *    never has more than `MAX_IN_FLIGHT` requests in flight, so this
		 *    cap can only be reached by grandchildren the parent has already
		 *    forgotten: those expired at 8 s but still alive (up to 20 s), and
		 *    those that have `send`-ed their answer — the parent freed the
		 *    place — and are not yet past their `_exit()` and reaped here.
		 *    With the cap at 16 that window turned a perfectly legal 16th
		 *    request into «not checked». */
		if (alive >= 2 * MAX_IN_FLIGHT) {
			/* ⛔ Over the cap: answered «not checked» (3), never a «no» —
			 *    a «no» counts towards the ban. */
			struct response full;
			memset(&full, 0, sizeof full);
			full.ticket = r.ticket;
			full.outcome = 3u;
			explicit_bzero(&r, sizeof r);
			(void)send(fd, &full, sizeof full, MSG_NOSIGNAL);
			continue;
		}
		pid_t p = fork();
		if (p == 0)
			grandchild(fd, &r); /* does not return */
		if (p > 0)
			alive++;
		if (p < 0) {
			/* ⛔ No fallback of calling PAM HERE: it would block the
			 *    dispatcher, and with it all the other requests.  And NOT
			 *    silence either: a `fork` that fails is OUR defect (no
			 *    memory, no processes), and silence would become the 8 s
			 *    expiry, which counts as a failed attempt.  Answered «not
			 *    checked» (3), like the cap. */
			struct response failed;
			memset(&failed, 0, sizeof failed);
			failed.ticket = r.ticket;
			failed.outcome = 3u;
			(void)send(fd, &failed, sizeof failed, MSG_NOSIGNAL);
		}
		/* ⛔ §4.4: the password is zeroed as soon as it has served.  This is
		 *    the dispatcher's copy, and it lives the time of a `fork`. */
		explicit_bzero(&r, sizeof r);
	}
}

/* ⭐ The dispatcher's `main()`, after the `exec` of `spawn()` (box above
 * `RESTART_FIRST_MS`).  Nothing of the server has been opened in this process:
 * it checks that descriptor 3 really is the SEQPACKET end it was given, and
 * becomes the dispatcher. */
int helper_main(int argc, char **argv)
{
	int type = 0;
	socklen_t len = sizeof type;

	for (int i = 2; i < argc; i++) {
		if (strcmp(argv[i], "--journal") == 0)
			(void)log_journal(true);
		else if (strcmp(argv[i], "--verbose") == 0)
			log_chatter(true);
	}
	/* ⛔ Run by hand, or by anything that is not `spawn()`, there is no pair
	 *    on 3: say so and stop, rather than read requests from whatever file
	 *    happens to sit there. */
	if (getsockopt(3, SOL_SOCKET, SO_TYPE, &type, &len) != 0
	    || type != SOCK_SEQPACKET) {
		fprintf(stderr, "--pam-helper is started by the REMOTIX server only "
		                "(descriptor 3 is not its socket)\n");
		return 2;
	}
	/* ⚠ So a PAM module that execs a program does not hand it the socket. */
	(void)fcntl(3, F_SETFD, FD_CLOEXEC);
	/* ⚠ `comm` after an `exec` of `/proc/self/exe` would read «exe». */
	(void)prctl(PR_SET_NAME, "remotix-pam");
	dispatcher(3); /* does not return */
	return 1;
}

/* ------------------------------------------------------------------------ */
/* THE PARENT                                                                */

/* ⛔ Closes every descriptor above 3: the dispatcher moves its end of the pair
 * there first.  `close_range` (Linux 5.9), and a loop when the kernel does not
 * have it — never «skip it», a descriptor kept by mistake is a port held after
 * the server's death. */
static void close_the_rest(void)
{
	if (close_range(4, ~0U, 0) == 0)
		return;
	long top = sysconf(_SC_OPEN_MAX);
	if (top < 0 || top > 65536)
		top = 65536;
	for (int d = 4; d < top; d++)
		(void)close(d);
}

/* ⭐ In the forked copy, before its `exec`: every handler back to the default
 * (a handler of the server would run in a process that is about to vanish), but
 * SIGPIPE stays ignored, as the server keeps it. */
static void fork_signals_fresh(void)
{
	for (int s = 1; s < NSIG; s++)
		if (s != SIGKILL && s != SIGSTOP)
			signal(s, SIG_DFL);
	signal(SIGPIPE, SIG_IGN);
}

/* ⭐ The socket pair and the fork, shared by the first start and every
 * restart.  `false` = nothing was started, and `why` says what failed. */
static bool spawn(helper *a, const char **why, int *err)
{
	int sv[2];
	pid_t p;

	/* ⛔ `SOCK_SEQPACKET`: message boundaries are kept by the kernel.  See the
	 *    box in `helper.h` — with a stream the framing would be ours, and a
	 *    defect in there would mean «someone else's answer», that is I3 broken
	 *    by a read error. */
	if (socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) != 0) {
		*why = "socketpair";
		*err = errno;
		return false;
	}
	pid_t parent = getpid();
	/* ⚠ Built BEFORE the `fork()`: the forked copy only makes system calls. */
	char *av[5];
	int ac = 0;
	av[ac++] = (char *)"remotix-pam";
	av[ac++] = (char *)"--pam-helper";
	if (log_to_journal())
		av[ac++] = (char *)"--journal";
	if (log_verbose())
		av[ac++] = (char *)"--verbose";
	av[ac] = NULL;

	/* ⛔ Every signal blocked across the `fork()`, and the copy back to the
	 *    defaults before it unblocks — a handler of the server must not run in
	 *    it until its `exec`. */
	sigset_t all, before;
	sigfillset(&all);
	sigprocmask(SIG_SETMASK, &all, &before);
	p = fork();
	if (p != 0)
		sigprocmask(SIG_SETMASK, &before, NULL);
	if (p < 0) {
		*why = "fork";
		*err = errno;
		close(sv[0]);
		close(sv[1]);
		return false;
	}
	if (p == 0) {
		fork_signals_fresh();
		close(sv[0]);
		/* ⛔ Its end goes to descriptor 3 and everything above is closed:
		 *    at boot that closes nothing (only 0-2 and the pair are open
		 *    there), on a restart it closes the listeners and the rest. */
		if (sv[1] != 3) {
			if (dup2(sv[1], 3) < 0) /* `dup2` clears CLOEXEC on 3 */
				_exit(127);
			close(sv[1]);
		} else if (fcntl(3, F_SETFD, 0) != 0) {
			_exit(127);
		}
		close_the_rest();
		/* ⛔ Parent's death -> this one's death: armed BEFORE the `exec` (it
		 *    survives it), and checked against a parent that died in between. */
		prctl(PR_SET_PDEATHSIG, SIGTERM);
		if (getppid() != parent)
			_exit(127);
		/* ⚠ The signal mask crosses an `exec`, the handlers do not: unblock
		 *   everything, so the dispatcher starts as a fresh process. */
		sigset_t none;
		sigemptyset(&none);
		sigprocmask(SIG_SETMASK, &none, NULL);
		/* ⛔⭐ A fresh memory image (box above `RESTART_FIRST_MS`).  ⛔ And if
		 *     it fails, NO fallback to `dispatcher(3)` here: that is exactly
		 *     the forked copy of the server's heap this exec exists to avoid. */
		execve("/proc/self/exe", av, environ);
		_exit(127);
	}
	close(sv[1]);
	a->fd = sv[0];
	a->child = p;
	a->killed = false;
	/* ⛔ Non-blocking: it is the whole point of this file.  A `send` that
	 *    waits is a wait inside the asynchronous loop — `CODER.md` §4.4 —
	 *    that is, the defect moved instead of cured. */
	fcntl(a->fd, F_SETFL, O_NONBLOCK);
	return true;
}

helper *helper_turn_on(void)
{
	helper *a;
	const char *why = "";
	int err = 0;

	a = (helper *)calloc(1, sizeof *a);
	if (!a)
		return NULL;
	a->fd = -1;
	a->next_case = 1;
	/* ⭐⭐ 1.5 (§11.50): the network side starts no dispatcher — the PAM helper is the root side's child, and this
	 *     object only asks it. */
	if (rootside_attached && rootside_attached()) {
		a->remote = true;
		a->fd = rootside_descriptor();
		rootside_hook_verdict(on_root_verdict, a);
		registro_dice(LOG_STARTUP,
		              "⭐ PAM is asked through the ROOT SIDE (AUTH → VERDICT, DECISIONS.md §11.50): the helper is "
		              "its child, this process never sees it");
		return a;
	}
	if (!spawn(a, &why, &err)) {
		/* ⭐ A failed start at boot is a death like the others — the object
		 *    comes back with no process, and `helper_expired()` starts it with
		 *    the pause that doubles.  Before D3, NULL went back to `main.c`,
		 *    which fell for good to the synchronous check (1-2 s of loop
		 *    stopped at every login) and never tried again. */
		registro_dice(LOG_STARTUP,
		              "⛔ the PAM helper does NOT start: %s: %s.  It will be "
		              "tried again (1 s, 2 s, 4 s … up to 60 s); until then every "
		              "login is refused after the fixed second, NOT counted "
		              "towards the ban (invariant I3).",
		              why, strerror(err));
		return a;
	}

	registro_dice(LOG_STARTUP,
	              "⭐ PAM helper started: pid %ld, anonymous SEQPACKET "
	              "socketpair.  From here on the poll loop NO LONGER calls PAM "
	              "(DECISIONS.md §1.10)",
	              (long)a->child);
	return a;
}

helper *helper_turn_on_root(HelperOutcome cb, void *ctx)
{
	helper *a;
	const char *why = "";
	int err = 0;

	a = (helper *)calloc(1, sizeof *a);
	if (!a)
		return NULL;
	a->fd = -1;
	a->next_case = 1;
	a->root = true;
	a->outcome_cb = cb;
	a->outcome_ctx = ctx;
	if (!spawn(a, &why, &err)) {
		registro_dice(LOG_STARTUP,
		              "⛔ the PAM helper does NOT start: %s: %s.  It will be "
		              "tried again (1 s, 2 s, 4 s … up to 60 s); until then every "
		              "login is answered «not checked», NOT counted towards the "
		              "ban (invariant I3).",
		              why, strerror(err));
		return a;
	}
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
	/* ⚠ Network mode: the channel is the root side's client's, and `children_turn_off()` still needs it after this
	 *   line. */
	if (a->remote) {
		free(a);
		return;
	}
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
	if (a && a->remote)
		return rootside_descriptor();
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

static bool ask(helper *a, const char *user, const char *password,
                const char *rhost, uint64_t now_ms, uint64_t *ticket);

bool helper_ask(helper *a, const char *user, const char *password,
                     const char *provenance, uint64_t now_ms,
                     uint64_t *ticket)
{
	char rhost[64];

	*ticket = 0;
	if (!a || !user || !password)
		return false;
	(void)rcp_rhost_from_provenance(provenance, rhost, sizeof rhost);
	return ask(a, user, password, rhost, now_ms, ticket);
}

bool helper_ask_bare(helper *a, const char *user, const char *password,
                     const char *rhost, uint64_t now_ms, uint64_t *ticket)
{
	*ticket = 0;
	if (!a || !user || !password)
		return false;
	return ask(a, user, password, rhost ? rhost : "", now_ms, ticket);
}

static bool ask(helper *a, const char *user, const char *password,
                const char *rhost, uint64_t now_ms, uint64_t *ticket)
{
	struct request r;
	ssize_t written;
	uint64_t my;

	if (a->remote && rootside_lost()) {
		registro_dice(REG_RCP,
		              "⛔ the root side is gone: this check does NOT leave — the login is refused after the fixed "
		              "second and does NOT count towards the ban");
		return false;
	}
	if (!a->remote && a->fd < 0) {
		/* ⭐ Down, waiting for its restart (`helper_expired()`): refused after
		 *    the fixed second, NOT counted — the defect is ours. */
		registro_dice(REG_RCP,
		              "⛔ the PAM helper is down, waiting to be started again: "
		              "this check does NOT leave — whoever asked receives the "
		              "refusal that is OURS, not counted towards the ban");
		return false;
	}
	{
		/* ⚠ The root side's bounds are its own (§11.50): no `rcp.c` to ask,
		 *   and no places kept for a known key. */
		bool known = a->root || rcp_asking_for_known_key();
		int limit = known ? MAX_IN_FLIGHT : MAX_IN_FLIGHT - RESERVED_FOR_KNOWN;
		if (a->nflight >= limit) {
			registro_dice(REG_RCP,
			              "⛔ %d PAM checks already in flight (%d places for %s): "
			              "this one does NOT leave, and whoever asked will "
			              "receive a NO (I3: failure is a no, not a maybe)",
			              a->nflight, limit,
			              known ? "a key that logged in lately"
			                    : "an unknown key, 2 kept for known ones");
			return false;
		}
	}

	my = a->next_case;
	memset(&r, 0, sizeof r);
	r.ticket = my;
	/* ⛔ `snprintf` and not `strcpy`: the ranges have already been enforced by
	 *    `rcp.c` (§4.4: user 1..256, password 1..1024), and this is the second
	 *    wall — the one that holds even if the first changes. */
	snprintf(r.user, sizeof r.user, "%s", user);
	snprintf(r.password, sizeof r.password, "%s", password);
	snprintf(r.rhost, sizeof r.rhost, "%s", rhost);
	if (rcp_log_tag)
		rcp_log_tag(user, r.tag);

	/* ⭐ 1.5: network mode, the same request as AUTH to the root side. */
	if (a->remote) {
		/* ⛔ rootside_auth() writes its own line for every refusal (table full, channel, send): one line, the true
		 *    reason. */
		if (!rootside_auth(my, r.user, r.password, r.rhost)) {
			explicit_bzero(&r, sizeof r);
			return false;
		}
		written = (ssize_t)sizeof r;
	} else {
		written = send(a->fd, &r, sizeof r, MSG_NOSIGNAL);
	}
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
	/* ⚠ The root side expires at `EXPIRY_MS` and answers by itself: this side waits a little longer, so it is that
	 *   answer that arrives (this expiry is only the backstop). */
	if (a->remote)
		a->flight[a->nflight].expires += 4000;
	snprintf(a->flight[a->nflight].user, sizeof a->flight[a->nflight].user, "%s",
	         user);
	snprintf(a->flight[a->nflight].rhost, sizeof a->flight[a->nflight].rhost, "%s",
	         rhost);
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

/* ⭐ Reaps the dispatcher if it has finished, without waiting.  `true` = there
 * is no process left (reaped now, or already gone). */
static bool reap(helper *a, int *status)
{
	*status = -1;
	if (a->child <= 0)
		return true;
	/* ⭐ sigchld.h: «not looked at» is not «alive» nor «dead»: false, and the next scan (a SIGCHLD, or a second at most) looks. */
	if (a->reap_hold)
		return false;
	pid_t r = waitpid(a->child, status, WNOHANG);
	if (r == a->child || (r < 0 && errno == ECHILD)) {
		a->child = 0;
		return true;
	}
	return false;
}

/* ⭐ «Not checked»: the check was NOT made (the dispatcher's own cap, or its
 * death).  ⛔ Delivered as `lost`, like the death of the helper: our defect,
 * which `rcp.c` refuses as OURS and never counts towards the ban.  In the root
 * side's shape it goes to the callback as outcome 3. */
static void not_checked(helper *a, uint64_t ticket, const char *user,
                        const char *rhost, HelperVerdict delivery, void *ctx)
{
	if (a->root) {
		if (a->outcome_cb)
			a->outcome_cb(a->outcome_ctx, ticket, 3, user, rhost);
		return;
	}
	registro_dice(REG_RCP,
	              "⛔ request %llu was NOT checked (the dispatcher could not start "
	              "the check: its cap of %d reached, or a fork failed): refused as "
	              "OURS and NOT counted towards the ban",
	              (unsigned long long)ticket, 2 * MAX_IN_FLIGHT);
	/* ⭐ D4b: the bracket of `rcp_refusal_unchecked()` — `rcp.c` refuses this
	 *    ticket as ours (0x0E, nothing counted, the booking given back) whether
	 *    it is a live session's or an orphan's.  `lost` goes with it: same
	 *    meaning, kept for the callers that read only the flag. */
	rcp_refusal_unchecked(ticket);
	if (delivery)
		delivery(ctx, ticket, false, user, rhost, true);
	rcp_refusal_unchecked(0);
}

static void dies(helper *a, const char *why, HelperVerdict delivery,
                  void *ctx)
{
	int status;

	registro_dice(REG_RCP,
	              "⛔ the PAM helper is gone (%s): the %d checks in "
	              "flight become NO, and every following attempt will be a NO "
	              "until it is started again (invariant I3).  ⚠ It is not «wrong "
	              "password»: it is «PAM could not judge», and the server does not "
	              "keep it to itself.  Our defect: since 24 Oct 2026 it does NOT "
	              "count as a failed attempt of §4.4-bis (the bookings are given "
	              "back).",
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
	 *    §4.4 forbids waiting.  If it had not finished yet, `helper_expired()`
	 *    tries again at every round (D3: before, it stayed a zombie until the
	 *    server's shutdown), and the new helper is not started until the old
	 *    one is reaped. */
	if (reap(a, &status))
		registro_dice(REG_RCP,
		              "⭐ and the dead helper has been reaped: from now on «dead» "
		              "and «alive» no longer have the same face in /proc");
	/* ⛔⭐ Every request in flight is given back with ITS name and address — the
	 *     booking of `login_reserve` is released by the delivery, never left
	 *     behind, and a request is delivered ONCE: it leaves the table here, so
	 *     a late answer is discarded (the socket is closed anyway). */
	while (a->nflight > 0) {
		uint64_t p = a->flight[0].ticket;
		char chi[257], da[64];
		snprintf(chi, sizeof chi, "%s", a->flight[0].user);
		/* ⛔ The address too, BEFORE `flight_remove()` (as `flight_consumes()`
		 *    does): with the connection gone, a verdict without address cannot
		 *    be resolved and the booking would stay in flight for ever. */
		snprintf(da, sizeof da, "%s", a->flight[0].rhost);
		flight_remove(a, 0);
		if (a->root) {
			if (a->outcome_cb)
				a->outcome_cb(a->outcome_ctx, p, 3, chi, da);
		} else if (delivery) {
			delivery(ctx, p, false, chi, da, true);
		}
	}
	a->restart_at = 0; /* scheduled by `recover()`, which has the clock */
}

/* ⭐ The restart (box at `RESTART_FIRST_MS`).  Called at every round while
 * the helper is down; never waits. */
static void recover(helper *a, uint64_t now_ms)
{
	int status;
	const char *why = "";
	int err = 0;

	/* ⛔ 1. The old dispatcher first: two dispatchers would be harmless for
	 *       I3 (the old socket is closed) but a process nobody accounts for.
	 *       If it is still alive (the socket broke but it did not exit) it is
	 *       killed once, and reaped at a following round. */
	if (!reap(a, &status)) {
		if (a->reap_hold)
			return;      /* not looked at this round: no kill on a guess, the next scan decides */
		if (!a->killed) {
			kill(a->child, SIGKILL);
			a->killed = true;
		}
		return;
	}

	/* 2. Schedule, once per death. */
	if (a->restart_at == 0) {
		uint64_t pause = RESTART_FIRST_MS;
		bool rapid = a->born_ms == 0 || now_ms - a->born_ms < STABLE_MS;
		a->deaths_in_row = rapid ? a->deaths_in_row + 1 : 1;
		for (int i = 1; i < a->deaths_in_row && pause < RESTART_CAP_MS; i++)
			pause *= 2;
		if (pause > RESTART_CAP_MS)
			pause = RESTART_CAP_MS;
		a->restart_at = now_ms + pause;
		if (a->deaths_in_row >= LOUD_AFTER)
			registro_dice(REG_RCP,
			              "⛔⛔ the PAM helper has died %d times in a row (each "
			              "time within %d s of its start): something is BROKEN "
			              "in the PAM stack or in the machine, and NOBODY can log "
			              "in while it lasts.  It is tried again every %llu s; "
			              "the log lines above say how it died",
			              a->deaths_in_row, STABLE_MS / 1000,
			              (unsigned long long)(pause / 1000));
		else
			registro_dice(REG_RCP,
			              "⚠ the PAM helper will be started again in %llu ms "
			              "(death %d in a row)",
			              (unsigned long long)pause, a->deaths_in_row);
		return;
	}
	if (now_ms < a->restart_at)
		return;

	/* 3. Start it again. */
	a->restart_at = 0;
	a->born_ms = now_ms;
	if (!spawn(a, &why, &err)) {
		/* ⚠ It counts as one more death in a row: `born_ms` is now, so the
		 *   next round schedules a longer pause. */
		registro_dice(REG_RCP,
		              "⛔ the PAM helper could NOT be started again: %s: %s",
		              why, strerror(err));
		return;
	}
	a->restarts++;
	/* ⛔ The words «PAM helper started: pid» are the same as at boot ON
	 *    PURPOSE: the benches (`02-pam-start.sh kill-helper`) read the LAST such
	 *    line of the log to find the live helper. */
	registro_dice(REG_RCP,
	              "⭐ PAM helper started: pid %ld — RESTART %d, after death %d in a "
	              "row.  Logins are judged by PAM again",
	              (long)a->child, a->restarts, a->deaths_in_row);
}

/* ⭐ The «yes / no / locked» of one answer.  `outcome` 1 admitted, 2 refused
 * while locked, anything else refused. */
static void deliver_outcome(helper *a, uint64_t ticket, uint8_t outcome, const char *user,
                    const char *rhost, HelperVerdict delivery, void *ctx)
{
	/* ⛔⭐ HERE, AND ONLY HERE, A «YES» CAN ENTER THE SERVER — and it goes
	 *     through a comparison with `1`, not through a `!= 0`: a dirty
	 *     byte, a memory leftover or a 255 are a NO. */
	bool admitted = outcome == 1u;

	if (a->root) {
		if (a->outcome_cb)
			a->outcome_cb(a->outcome_ctx, ticket,
			              admitted ? 1 : outcome == 2u ? 2 : 0, user, rhost);
		return;
	}
	/* ⭐ §11.47 B: a no given while `pam_faillock` had the account locked
	 *    is marked for `rcp.c` for the length of THIS delivery only (the
	 *    verdict travels through `main.c` and `transport.c` with its bool,
	 *    unchanged — live session or orphan); `rcp.c` decides whether it
	 *    counts. */
	rcp_refusal_locked(outcome == 2u ? ticket : 0);
	if (delivery)
		delivery(ctx, ticket, admitted, user, rhost, false);
	rcp_refusal_locked(0);
}

/* ⭐ 1.5: network mode — a VERDICT from the root side (`rootside_move()`).  RXR_NO_LOCKED is the faillock refusal
 *    (marked for `rcp.c` by `deliver_outcome()`), RXR_NOT_CHECKED the root side's «not checked» (its bounds, helper
 *    down, timeout): refused as OURS and never counted (`not_checked()`); RXR_NO counts. */
static void on_root_verdict(void *ctx, uint64_t request, int outcome)
{
	helper *a = (helper *)ctx;
	char user[257];
	char rhost[64];

	if (!flight_consumes(a, request, user, sizeof user, rhost, sizeof rhost)) {
		registro_dice(REG_RCP,
		              "⛔ VERDICT for request %llu, which is not in flight (already expired, or already answered): "
		              "DISCARDED",
		              (unsigned long long)request);
		return;
	}
	if (outcome == RXR_NOT_CHECKED) {
		not_checked(a, request, user, rhost, a->delivery, a->delivery_ctx);
		return;
	}
	deliver_outcome(a, request,
	                outcome == RXR_YES ? 1u : outcome == RXR_NO_LOCKED ? 2u : 0u,
	                user, rhost, a->delivery, a->delivery_ctx);
}

void helper_move(helper *a, HelperVerdict delivery, void *ctx)
{
	if (a && a->remote) {
		a->delivery = delivery;
		a->delivery_ctx = ctx;
		rootside_move();
		a->delivery = NULL;
		a->delivery_ctx = NULL;
		return;
	}
	if (!a || a->fd < 0)
		return;
	for (;;) {
		struct response ri;
		char chi[257];
		char da[64];
		/* ⛔ `MSG_TRUNC`: the TRUE length of the message, not what fitted.
		 *    Without it a SEQPACKET message LONGER than the answer is cut to
		 *    `sizeof ri` and reads as a well-formed answer — the «wrong
		 *    length is not interpreted» below held only for short ones. */
		ssize_t readings = recv(a->fd, &ri, sizeof ri, MSG_TRUNC);
		if (readings == 0) {
			dies(a, "the socket was closed from its side", delivery, ctx);
			return;
		}
		if (readings < 0) {
			int e = errno;
			if (e == EINTR)
				continue;
			if (e == EAGAIN || e == EWOULDBLOCK)
				return; /* nothing else to read now */
			/* ⛔ Only an error that says the SOCKET is gone kills the helper.
			 *    ENOBUFS, ENOMEM and the like are the machine short of memory
			 *    for a moment: restarting a healthy helper for them would
			 *    give back the checks in flight for nothing.  Written (at
			 *    most one line every 10 s, with the count) and read again at
			 *    the next round; a dispatcher that really died is seen by
			 *    `helper_expired()`. */
			if (e == ECONNRESET || e == EBADF || e == ENOTCONN
			    || e == ENOTSOCK || e == EPIPE || e == EINVAL) {
				dies(a, strerror(e), delivery, ctx);
				return;
			}
			struct timespec ts;
			clock_gettime(CLOCK_MONOTONIC, &ts);
			a->recv_errors++;
			if (a->recv_err_logged == 0
			    || ts.tv_sec - a->recv_err_logged >= 10) {
				registro_dice(REG_RCP,
				              "⚠ reading the PAM helper's answers failed: %s "
				              "(%d time(s) since the last line): transient, the "
				              "helper is kept and read again at the next round",
				              strerror(e), a->recv_errors);
				a->recv_err_logged = ts.tv_sec ? ts.tv_sec : 1;
				a->recv_errors = 0;
			}
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
		if (ri.outcome == 3u)
			not_checked(a, ri.ticket, chi, da, delivery, ctx);
		else
			deliver_outcome(a, ri.ticket, ri.outcome, chi, da, delivery, ctx);
	}
}

void helper_reap_hold(helper *a, bool hold)
{
	if (a)
		a->reap_hold = hold;
}

void helper_expired(helper *a, uint64_t now_ms, HelperVerdict delivery,
                      void *ctx)
{
	if (!a)
		return;
	for (int i = 0; i < a->nflight;) {
		if (now_ms >= a->flight[i].expires) {
			uint64_t p = a->flight[i].ticket;
			char chi[257], da[64];
			snprintf(chi, sizeof chi, "%s", a->flight[i].user);
			snprintf(da, sizeof da, "%s", a->flight[i].rhost);
			flight_remove(a, i);
			registro_dice(REG_RCP,
			              "⛔ request %llu received no answer in %d ms: "
			              "the grandchild died or PAM got stuck.  ⭐ The "
			              "expiry counts as NO (invariant I3), and since 24 Oct "
			              "2026 it COUNTS as a failed attempt of §4.4-bis (B): an "
			              "attempt without a verdict is not a free attempt",
			              (unsigned long long)p, EXPIRY_MS);
			/* ⭐ The root side's helper hands it back as outcome 4 = «expired»,
			 *    which is NOT «not checked» (3): the 24 Oct 2026 decision is
			 *    that an attempt without a verdict is not a free one, so the
			 *    network side counts it as a failed attempt (as `delivery(...,
			 *    lost=false)` does above).  3 stays for the cap, the death
			 *    and the helper being down. */
			if (a->root) {
				if (a->outcome_cb)
					a->outcome_cb(a->outcome_ctx, p, 4, chi, da);
			} else if (delivery) {
				delivery(ctx, p, false, chi, da, false);
			}
		} else {
			i++;
		}
	}

	/* ⭐⭐ 1.5 (§11.50): network mode — no dispatcher to watch here.  The root side gone is the end of this process:
	 *     systemd restarts the unit, the desktops stay.  ⇒ SIGTERM to ourselves, once, so the loop's own farewell runs. */
	if (a->remote) {
		/* ⛔ The VERDICTs a wait put aside (a CLOSE_ORPHAN from the abandonment clock, a turn-off) are delivered HERE,
		 *    every round, with the delivery — not at the next byte on the channel, which may never come. */
		helper_move(a, delivery, ctx);
		/* ⚠ The LINE is main.c's loop («the root side is gone»), written once; here only the stop. */
		if (rootside_lost() && !a->lost_told) {
			a->lost_told = true;
			raise(SIGTERM);
		}
		return;
	}

	/* ⭐ And the dispatcher is watched here too: this function runs at every
	 *    round, and a dispatcher that exited is seen within a round even while
	 *    one of its grandchildren still holds the socket open — the EOF in
	 *    `helper_move()` would come only when the last grandchild has
	 *    finished.  ⚠ Only for a process this object started (`child > 0`). */
	if (a->fd >= 0 && a->child > 0) {
		int status;
		if (a->born_ms == 0)
			a->born_ms = now_ms;
		if (reap(a, &status)) {
			char why[96];
			if (status >= 0 && WIFSIGNALED(status))
				snprintf(why, sizeof why, "the dispatcher was killed by signal %d",
				         WTERMSIG(status));
			else if (status >= 0 && WIFEXITED(status) && WEXITSTATUS(status) == 127)
				snprintf(why, sizeof why, "the dispatcher could not exec "
				         "/proc/self/exe --pam-helper (status 127)");
			else if (status >= 0 && WIFEXITED(status))
				snprintf(why, sizeof why, "the dispatcher exited with status %d",
				         WEXITSTATUS(status));
			else
				snprintf(why, sizeof why, "the dispatcher is gone");
			dies(a, why, delivery, ctx);
		}
	}
	if (a->fd < 0)
		recover(a, now_ms);
}
