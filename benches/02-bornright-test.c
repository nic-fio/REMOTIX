/*
 * 02-bornright-test.c — ⭐ 1.6 (R8 B): `network_side_born_right()` of src/main.c, the check the network side makes of how it was started,
 *                       each case in a fork, in a privileged container as root (users `rxnet`).  main.c is INCLUDED (its statics
 *                       reachable, its main() renamed).  Driven by `02-rootside-live.sh`, which links it with the product's objects
 *                       except main.o and walls.o.
 *
 * The function wants: not root; PID 1 of a PID namespace of its own with parent 0 (the root side starts it with
 * `walls_fork_pidns()`); PR_SET_PDEATHSIG; the other end of fd 3 owned by uid 0 (`SO_PEERCRED`, a failing call said apart from a
 * wrong uid); fds 3, 4, 5 sockets of the right type (SEQPACKET, DGRAM, STREAM), then they are marked close-on-exec.
 *
 * Exit 0 all passed · 1 a check failed · 3 could not run (no user rxnet, no PID namespace).
 */
#define main remotix_product_main
#include "main.c"
#undef main

#include <grp.h>
#include <pwd.h>
#include <sched.h>
#include <sys/syscall.h>
#include <sys/wait.h>

static int passed, failed;

static void report(bool ok, const char *what)
{
	printf("  %s %s\n", ok ? "ok  " : "FAIL", what);
	if (ok)
		passed++;
	else
		failed++;
}

enum { DEFAULT, AS_ROOT, NOT_PID1, PEER_NOT_ROOT, PEER_FAILS, FD4_PIPE, FD5_DGRAM };

/* Runs the function in a child that is PID 1 of a new PID namespace (or a plain fork for NOT_PID1 and AS_ROOT), with the
 * descriptors the case wants.  Returns 1 = the function said true, 0 = false, -1 = could not run. */
static int run_case(int how, bool want_cloexec_check, bool *cloexec_ok)
{
	struct passwd *rx = getpwnam("rxnet");
	int sv[2] = { -1, -1 }, u = -1, t = -1, pipefd[2] = { -1, -1 }, st, res[2];
	pid_t p;
	uid_t rxuid;

	if (!rx || pipe(res) != 0)
		return -1;
	rxuid = rx->pw_uid;
	/* the descriptors, made by root (the root side), or by rxnet for the wrong-peer case */
	if (how == PEER_NOT_ROOT && seteuid(rxuid) != 0)
		return -1;
	if (how == PEER_FAILS) {
		if (pipe(sv) != 0)
			return -1; /* fd 3 will not be a socket: SO_PEERCRED fails */
	} else if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) != 0) {
		return -1;
	}
	if (how == PEER_NOT_ROOT && seteuid(0) != 0)
		return -1;
	u = socket(AF_INET, SOCK_DGRAM, 0);
	t = how == FD5_DGRAM ? socket(AF_INET, SOCK_DGRAM, 0) : socket(AF_INET, SOCK_STREAM, 0);
	if (how == FD4_PIPE) {
		if (pipe(pipefd) != 0)
			return -1;
		close(u);
		u = pipefd[0];
	}
	p = how == AS_ROOT || how == NOT_PID1 ? fork() : (pid_t)syscall(SYS_clone, CLONE_NEWPID | SIGCHLD, 0, 0, 0, 0);
	if (p < 0)
		return -1;
	if (p == 0) {
		int ok;

		if (dup2(sv[0], FD_ROOT) < 0 || dup2(u, FD_UDP) < 0 || dup2(t, FD_TCP) < 0)
			_exit(90);
		if (how != AS_ROOT && (setgroups(0, NULL) != 0 || setgid(rx->pw_gid) != 0 || setuid(rxuid) != 0))
			_exit(91);
		ok = network_side_born_right();
		if (want_cloexec_check && ok) {
			bool all = true;

			for (int fd = FD_ROOT; fd <= FD_TCP; fd++)
				all = all && (fcntl(fd, F_GETFD) & FD_CLOEXEC);
			(void)!write(res[1], all ? "y" : "n", 1);
		}
		_exit(ok ? 0 : 1);
	}
	close(res[1]);
	if (waitpid(p, &st, 0) != p || !WIFEXITED(st) || WEXITSTATUS(st) > 1)
		return -1;
	if (cloexec_ok) {
		char c = 0;

		*cloexec_ok = read(res[0], &c, 1) == 1 && c == 'y';
	}
	close(res[0]);
	return WEXITSTATUS(st) == 0 ? 1 : 0;
}

int main(void)
{
	bool cx = false;
	int r;

	setvbuf(stdout, NULL, _IOLBF, 0);
	if (geteuid() != 0 || !getpwnam("rxnet")) {
		printf("  BLIND: needs root and the user rxnet\n");
		return 3;
	}
	printf("02-bornright-test\n");
	r = run_case(DEFAULT, true, &cx);
	if (r < 0) {
		printf("  BLIND: could not run the case (no PID namespace?)\n");
		return 3;
	}
	report(r == 1, "pid 1 of its own PID namespace, parent 0, rxnet, fd 3 SEQPACKET with uid 0 at the other end, fd 4 DGRAM, fd 5 STREAM: accepted");
	report(cx, "...and fds 3, 4, 5 are marked close-on-exec");
	report(run_case(AS_ROOT, false, NULL) == 0, "as root: refused");
	report(run_case(NOT_PID1, false, NULL) == 0, "not pid 1 (a plain fork): refused");
	report(run_case(PEER_NOT_ROOT, false, NULL) == 0, "the other end of fd 3 made by rxnet (uid != 0): refused");
	report(run_case(PEER_FAILS, false, NULL) == 0, "fd 3 not a socket (SO_PEERCRED fails): refused");
	report(run_case(FD4_PIPE, false, NULL) == 0, "fd 4 a pipe, not a socket: refused");
	report(run_case(FD5_DGRAM, false, NULL) == 0, "fd 5 a datagram socket, not a stream: refused");
	printf("%d passed, %d failed\n", passed, failed);
	return failed ? 1 : 0;
}
