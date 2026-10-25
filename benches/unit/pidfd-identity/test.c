/*
 * test.c — the EXACT identity of a child's messages by pidfd (1.5, pidfd-figlio; src/pidfdid.h, src/child.c, src/rootside.c).
 *
 * The network side lives in a PID namespace of its own, so the kernel stamps a child born outside it with pid 0 and the wall in child.c
 * cannot compare pids.  Where the kernel supports it (SO_PASSPIDFD 6.5, pidfs 6.9) the root side hands over a pidfd of the child with its
 * socket, the kernel attaches a pidfd of the SENDER to each message (SCM_PIDFD), and the wall compares the two inodes on pidfs.  Where it does
 * not (6.5-6.8: the pidfd is an anonymous inode, every one the same; older: none), the rule of today stays and nothing is an error.
 *
 * The REAL src/child.c is #included (like benches/unit/child-credentials), with real sockets and real forked processes, on the kernel of the
 * machine that runs the test (the tablet: 7.3, which has pidfs).  The check "this kernel has pidfs" is itself reported.
 *   1. pidfd_compare(): a process against itself via two pidfds = SAME; against another process = DIFFERENT; a missing descriptor = UNKNOWN;
 *      two anonymous inodes (eventfd: what a 6.5-6.8 kernel gives for every pidfd) = UNKNOWN, NEVER "same";
 *   2. receive_with_credentials_pidfd(): a real child writes on a SEQPACKET pair whose parent end has SO_PASSCRED + SO_PASSPIDFD: with the
 *      pidfd of THAT child as expected the verdict is SAME; with the pidfd of ANOTHER process it is DIFFERENT; with none it is UNKNOWN;
 *      the pidfd the kernel attached is closed on every way out (the count of open descriptors does not grow);
 *   3. without SO_PASSPIDFD on the socket nothing is attached: UNKNOWN (the old kernel's face);
 *   4. the wall (child_credentials_pidfd_ok), remote, the kernel's stamp pid 0: SAME passes; DIFFERENT is refused and the reason names the
 *      pidfd; UNKNOWN passes as today; SAME does not excuse a wrong uid, gid or serial; a non-zero pid in the namespace is still refused;
 *   4b. a message that carries DESCRIPTORS (SCM_RIGHTS: the child never sends any) is a violation of the wall: -3, every descriptor the kernel
 *      installed is closed (the open descriptors do not grow) — with and without SO_PASSPIDFD on the socket, one descriptor or four (the control data
 *      does not fit: MSG_CTRUNC), and a plain message after it is read normally; the child-side wrapper just drops it (-2);
 *   4c. (rilettura-fix M3) THIS process out of descriptors: (a) a plain message is read normally with identity UNKNOWN (kernel 7.3: SCM_PIDFD = -EMFILE, no MSG_CTRUNC); (b) one or two SCM_RIGHTS are still -3;
 *   5. by reading the sources (argv[1] = src/rootside.c, argv[2] = src/child.c): SPAWNED carries at most TWO descriptors (socket, then
 *      pidfd) and the client claims the second for the born child; the network side asks for SO_PASSPIDFD on the socket it received, and
 *      closes the pidfd with the socket (reaped, dismissed, turned off).
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree; see benches/unit/child-credentials/test.c for the stubs method):
 *   nice -n 19 ionice -c3 podman run --rm --cpus=1 --memory=2g --network=none -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src -I/albero/benches/fuzz/child-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/pidfd-identity/test.c -o t.o && clang $F -c /albero/benches/fuzz/child-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && ./test /albero/src/rootside.c /albero/src/child.c'
 * Exit code 0 = every check passed.
 */
#include "child.c"

#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <sys/eventfd.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
#include "common.h"

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static int pidfd_of(pid_t pid) { return (int)syscall(SYS_pidfd_open, pid, 0); }

static int open_fds(void)
{
	int n = 0;
	DIR *d = opendir("/proc/self/fd");
	struct dirent *e;

	while (d && (e = readdir(d)) != NULL)
		if (e->d_name[0] != '.')
			n++;
	if (d)
		closedir(d);
	return n;
}

/* A child that sleeps until killed. */
static pid_t sleeper(void)
{
	pid_t p = fork();

	if (p == 0) {
		for (;;)
			pause();
	}
	return p;
}

static void reap(pid_t p)
{
	kill(p, SIGKILL);
	waitpid(p, NULL, 0);
}

/* A child that writes one message on `fd` WITH `n` descriptors attached (pipe ends) and exits. */
static pid_t writer_with_fds(int fd, int n)
{
	pid_t p = fork();

	if (p == 0) {
		int fds[8], k = 0;
		char m[16] = "hello";
		struct iovec io = { m, sizeof m };
		union { struct cmsghdr c; char b[CMSG_SPACE(8 * sizeof(int))]; } ctl;
		struct msghdr mh;

		for (int i = 0; i < n; i += 2) {
			int pp[2];

			if (pipe(pp) != 0)
				_exit(1);
			fds[k++] = pp[0];
			if (k < n)
				fds[k++] = pp[1];
		}
		memset(&ctl, 0, sizeof ctl);
		memset(&mh, 0, sizeof mh);
		mh.msg_iov = &io;
		mh.msg_iovlen = 1;
		mh.msg_control = ctl.b;
		mh.msg_controllen = CMSG_SPACE(n * sizeof(int));
		ctl.c.cmsg_level = SOL_SOCKET;
		ctl.c.cmsg_type = SCM_RIGHTS;
		ctl.c.cmsg_len = CMSG_LEN(n * sizeof(int));
		memcpy(CMSG_DATA(&ctl.c), fds, n * sizeof(int));
		(void)sendmsg(fd, &mh, 0);
		_exit(0);
	}
	return p;
}

/* A child that writes one message on `fd` and exits. */
static pid_t writer(int fd)
{
	pid_t p = fork();

	if (p == 0) {
		char m[16] = "hello";

		(void)send(fd, m, sizeof m, 0);
		_exit(0);
	}
	return p;
}

static char *slurp(const char *path)
{
	FILE *f = fopen(path, "r");
	long n;
	char *b;

	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	fseek(f, 0, SEEK_SET);
	b = malloc((size_t)n + 1);
	if (b && fread(b, 1, (size_t)n, f) != (size_t)n) {
		free(b);
		b = NULL;
	}
	if (b)
		b[n] = 0;
	fclose(f);
	return b;
}

int main(int argc, char **argv)
{
	int pfs_self, pfs_self2, pfs_other, anon1, anon2;
	pid_t other = sleeper();
	int on_pidfs;

	/* 1 */
	pfs_self = pidfd_of(getpid());
	pfs_self2 = pidfd_of(getpid());
	pfs_other = pidfd_of(other);
	on_pidfs = pidfd_on_pidfs(pfs_self);
	printf("kernel: this machine %s pidfs\n", on_pidfs ? "HAS" : "does NOT have");
	if (on_pidfs) {
		CHECK(pidfd_compare(pfs_self, pfs_self2) == PIDFD_SAME, "1: two pidfds of one process are SAME");
		CHECK(pidfd_compare(pfs_self, pfs_other) == PIDFD_DIFFERENT, "1: the pidfd of another process is DIFFERENT");
	}
	CHECK(pidfd_compare(-1, pfs_self) == PIDFD_UNKNOWN && pidfd_compare(pfs_self, -1) == PIDFD_UNKNOWN, "1: a missing descriptor is UNKNOWN");
	anon1 = eventfd(0, 0);
	anon2 = eventfd(0, 0);
	CHECK(pidfd_compare(anon1, anon2) == PIDFD_UNKNOWN, "1: two anonymous inodes (a 6.5-6.8 kernel's pidfds) are UNKNOWN, never SAME");
	CHECK(pidfd_compare(anon1, pfs_self) == PIDFD_UNKNOWN, "1: an anonymous inode against a pidfd is UNKNOWN");
	close(anon1);
	close(anon2);

	/* 2, 3 */
	{
		int sv[2], one = 1, before, got;
		struct ucred chi;
		bool c_e;
		char buf[64];
		enum pidfd_same same;
		pid_t w;
		ssize_t r;

		/* SAME */
		CHECK(socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv) == 0, "2: socketpair");
		setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &one, sizeof one);
		got = setsockopt(sv[0], SOL_SOCKET, SO_PASSPIDFD, &one, sizeof one);
		CHECK(got == 0, "2: this kernel takes SO_PASSPIDFD (6.5+)");
		w = writer(sv[1]);
		waitpid(w, NULL, WNOHANG); /* the message is queued whether it has exited or not */
		{
			int expected = pidfd_of(w);
			/* the child may already be reaped by us: pidfd_open of a zombie still works until waitpid; re-fork to be exact */
			if (expected < 0) {
				w = writer(sv[1]);
				expected = pidfd_of(w);
			}
			usleep(20000);
			before = open_fds();
			same = PIDFD_DIFFERENT;
			r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, expected, &same);
			CHECK(r > 0 && c_e, "2: a message with credentials arrived");
			CHECK(!on_pidfs || same == PIDFD_SAME || r <= 0, "2: with the pidfd of THAT child as expected the verdict is SAME");
			CHECK(open_fds() == before, "2: the pidfd the kernel attached is closed (no descriptor left)");
			close(expected);
		}
		waitpid(w, NULL, 0);
		close(sv[0]);
		close(sv[1]);

		/* DIFFERENT, UNKNOWN */
		socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv);
		setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &one, sizeof one);
		setsockopt(sv[0], SOL_SOCKET, SO_PASSPIDFD, &one, sizeof one);
		w = writer(sv[1]);
		usleep(20000);
		before = open_fds();
		same = PIDFD_SAME;
		r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, pfs_other, &same);
		CHECK(r > 0, "2: second message arrived");
		CHECK(!on_pidfs || same == PIDFD_DIFFERENT, "2: with the pidfd of ANOTHER process the verdict is DIFFERENT");
		CHECK(open_fds() == before, "2: and nothing is left open");
		waitpid(w, NULL, 0);

		w = writer(sv[1]);
		usleep(20000);
		same = PIDFD_SAME;
		r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, -1, &same);
		CHECK(r > 0 && same == PIDFD_UNKNOWN, "2: with no pidfd handed over the verdict is UNKNOWN (the rule of today)");
		waitpid(w, NULL, 0);
		close(sv[0]);
		close(sv[1]);

		/* 3: no SO_PASSPIDFD */
		socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv);
		setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &one, sizeof one);
		w = writer(sv[1]);
		usleep(20000);
		same = PIDFD_SAME;
		r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, pfs_other, &same);
		CHECK(r > 0 && c_e && same == PIDFD_UNKNOWN, "3: without SO_PASSPIDFD nothing is attached: UNKNOWN, and the credentials still come");
		waitpid(w, NULL, 0);
		close(sv[0]);
		close(sv[1]);
	}

	/* 4b */
	{
		int sv[2], one = 1;
		int cases[4][2] = { {0, 1}, {1, 1}, {0, 4}, {1, 4} }; /* {SO_PASSPIDFD on?, descriptors attached} */

		for (int k = 0; k < 4; k++) {
			struct ucred chi;
			bool c_e;
			char buf[64];
			enum pidfd_same same;
			pid_t w;
			ssize_t r;
			int before;

			socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv);
			setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &one, sizeof one);
			if (cases[k][0])
				setsockopt(sv[0], SOL_SOCKET, SO_PASSPIDFD, &one, sizeof one);
			w = writer_with_fds(sv[1], cases[k][1]);
			usleep(30000);
			before = open_fds();
			r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, pfs_other, &same);
			CHECK(r == -3, "4b: a message with descriptors is a violation of the wall (-3)");
			CHECK(open_fds() == before, "4b: and every descriptor the kernel installed is closed (the open descriptors do not grow)");
			waitpid(w, NULL, 0);
			/* a plain message afterwards is read normally */
			w = writer(sv[1]);
			usleep(30000);
			r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, -1, &same);
			CHECK(r > 0 && c_e, "4b: and the next plain message is read normally");
			waitpid(w, NULL, 0);
			/* the child-side wrapper drops it */
			w = writer_with_fds(sv[1], cases[k][1]);
			usleep(30000);
			before = open_fds();
			r = receive_with_credentials(sv[0], buf, sizeof buf, &chi, &c_e);
			CHECK(r == -2 && open_fds() == before, "4b: the child-side wrapper drops it (-2) and closes the descriptors too");
			waitpid(w, NULL, 0);
			close(sv[0]);
			close(sv[1]);
		}
	}

	/* 4c (rilettura-fix M3): THIS process out of descriptors (RLIMIT_NOFILE at the highest open fd).  VERIFIED on kernel 7.3 with a probe: the kernel does not cut the control data for the
	 * sender's pidfd — SCM_PIDFD arrives with the value -EMFILE and no MSG_CTRUNC.  So (a) a plain message of an honest child is read normally and the identity is UNKNOWN (never
	 * "different"); (b) a child that sends one or two SCM_RIGHTS gets MSG_CTRUNC and no SCM_RIGHTS cmsg: still -3, the wall; no descriptor stays open. */
	{
		int sv[2], one = 1, maxfd = 0, before;
		struct rlimit old, low;
		struct ucred chi;
		bool c_e;
		char buf[64];
		enum pidfd_same same;
		pid_t w;
		ssize_t r;
		DIR *d;
		struct dirent *e;

		socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, sv);
		setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &one, sizeof one);
		setsockopt(sv[0], SOL_SOCKET, SO_PASSPIDFD, &one, sizeof one);
		d = opendir("/proc/self/fd");
		while (d && (e = readdir(d)) != NULL)
			if (e->d_name[0] != '.' && atoi(e->d_name) > maxfd)
				maxfd = atoi(e->d_name);
		if (d)
			closedir(d);
		getrlimit(RLIMIT_NOFILE, &old);
		low = old;
		low.rlim_cur = (rlim_t)maxfd;      /* what the kernel would install next is over the limit (opendir's own fd is gone) */

		/* (a) a plain message */
		w = writer(sv[1]);
		usleep(30000);
		before = open_fds();
		setrlimit(RLIMIT_NOFILE, &low);
		r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, pfs_other, &same);
		setrlimit(RLIMIT_NOFILE, &old);
		CHECK(r > 0 && c_e, "4c(a): out of descriptors, a plain message is read normally");
		CHECK(same == PIDFD_UNKNOWN, "4c(a): and its identity is UNKNOWN (the pidfd could not be installed), never DIFFERENT");
		CHECK(open_fds() == before, "4c(a): no descriptor left open");
		waitpid(w, NULL, 0);

		/* (b) one and two SCM_RIGHTS */
		for (int n = 1; n <= 2; n++) {
			w = writer_with_fds(sv[1], n);
			usleep(30000);
			before = open_fds();
			setrlimit(RLIMIT_NOFILE, &low);
			r = receive_with_credentials_pidfd(sv[0], buf, sizeof buf, &chi, &c_e, pfs_other, &same);
			setrlimit(RLIMIT_NOFILE, &old);
			CHECK(r == -3, n == 1 ? "4c(b): out of descriptors, ONE SCM_RIGHTS is still -3 (the wall)" : "4c(b): out of descriptors, TWO SCM_RIGHTS are still -3 (the wall)");
			CHECK(open_fds() == before, "4c(b): and no descriptor stays open");
			waitpid(w, NULL, 0);
		}
		close(sv[0]);
		close(sv[1]);
	}

	/* 4 */
	{
		char why[256];

		CHECK(child_credentials_pidfd_ok(1001, 1001, 94513, 7, true, true, 0, 1001, 1001, pfs_self, pfs_self2, why, sizeof why) || !on_pidfs,
		      "4: remote, stamp pid 0, SAME: passes");
		if (on_pidfs) {
			CHECK(!child_credentials_pidfd_ok(1001, 1001, 94513, 7, true, true, 0, 1001, 1001, pfs_self, pfs_other, why, sizeof why),
			      "4: DIFFERENT is refused");
			CHECK(strstr(why, "pidfd") != NULL, "4: and the reason names the pidfd");
			CHECK(!child_credentials_pidfd_ok(1001, 1001, 94513, 7, true, true, 0, 1002, 1001, pfs_self, pfs_self2, why, sizeof why),
			      "4: SAME does not excuse a wrong uid");
			CHECK(!child_credentials_pidfd_ok(1001, 1001, 94513, 7, true, true, 77, 1001, 1001, pfs_self, pfs_self2, why, sizeof why),
			      "4: nor a pid inside the namespace");
		}
		CHECK(child_credentials_pidfd_ok(1001, 1001, 94513, 7, true, true, 0, 1001, 1001, -1, -1, why, sizeof why),
		      "4: UNKNOWN (no pidfd) passes as today");
		anon1 = eventfd(0, 0);
		anon2 = eventfd(0, 0);
		CHECK(child_credentials_pidfd_ok(1001, 1001, 94513, 7, true, true, 0, 1001, 1001, anon1, anon2, why, sizeof why),
		      "4: two anonymous inodes (old kernel) pass as today, never refused");
		close(anon1);
		close(anon2);
		CHECK(child_credentials_ok(1001, 1001, 94513, 7, true, true, 0, 1001, 1001, why, sizeof why),
		      "4: the old entry point (no pidfd) is unchanged");
		CHECK(!child_credentials_ok(1001, 1001, 94513, 7, true, false, 0, 1001, 1001, why, sizeof why),
		      "4: and still refuses a message with no credentials");
	}

	/* 5 */
	if (argc > 2) {
		char *r = slurp(argv[1]), *c = slurp(argv[2]);

		CHECK(r && c, "5: sources readable");
		if (r && c) {
			CHECK(strstr(r, "nfds > 2") != NULL && strstr(r, "nfds > 1)") == NULL, "5: the root channel admits at most two descriptors with SPAWNED");
			CHECK(strstr(r, "syscall(SYS_pidfd_open, c.pid, 0)") != NULL && strstr(r, "chan_try2(&s, sizeof s, c.fd, child_pidfd)") != NULL,
			      "5: the root side hands over a pidfd of the child with the socket");
			CHECK(strstr(r, "out->pidfd = C.has_pidfd ? C.pidfd : -1;") != NULL, "5: and rootside_spawn() claims it");
			CHECK(strstr(c, "SO_PASSPIDFD") != NULL, "5: the network side asks the kernel for the sender's pidfd");
			{
				const char *mv = strstr(c, "if (readings == -3) {");
				const char *kill_ = mv ? strstr(mv, "child_signal(f, g, SIGKILL);") : NULL;
				const char *dis = mv ? strstr(mv, "child_dismiss(f, g, \"it sent descriptors on its socket\");") : NULL;

				CHECK(mv && kill_ && dis && kill_ < dis && dis - mv < 1200, "5: children_move refuses a -3 message: the child is killed and dismissed");
			}
			CHECK(strstr(c, "exact via pidfd (pidfs)") != NULL && strstr(c, "the socket's rule") != NULL,
			      "5: one log line per child says whether its identity is exact via pidfd or the socket's rule");
			CHECK(strstr(c, "if (carried_descriptors || (m.msg_flags & MSG_CTRUNC))") != NULL && strstr(c, "return -4;") == NULL, "5: MSG_CTRUNC is the same violation as SCM_RIGHTS (-3), no -4 branch");
			CHECK(strstr(c, "g->pidfd = b.pidfd;") != NULL, "5: and keeps the pidfd in the child");
			{
				int closes = 0;
				const char *p = c;

				while ((p = strstr(p, "child_pidfd_close(g);")) != NULL) {
					closes++;
					p++;
				}
				CHECK(closes >= 3, "5: the pidfd is closed with the socket (reaped, dismissed, turned off)");
			}
		}
		free(r);
		free(c);
	}
	reap(other);
	close(pfs_self);
	close(pfs_self2);
	close(pfs_other);
	printf("%d checks, %d failed\n", checks, bad);
	return bad ? 1 : 0;
}
