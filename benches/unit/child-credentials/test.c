/*
 * test.c — unit test of the envelope of the messages the PARENT receives from the CHILD (src/child.c):
 *   receive_with_credentials(), magic_ok(), credentials_match(), the «longer than expected» branch (-2),
 *   the «too short for a header» branch and the `readings < sizeof t + t.byte` check, all through the REAL children_move().
 * The fuzz harness (benches/fuzz/child-msg) does NOT cover them: it hands handle() a ready body.
 *
 * HOW: the REAL src/child.c is #included (never modified), exactly like fuzz_child_msg.c.  The log is benches/fuzz/child-msg/stubs_log.c;
 * everything else child.c links to (capture, encoder, PAM, compositors...) is generated as a stub that TRAPS if reached
 * (the `stubs_missing` method of benches/fuzz/child-msg/build-inner.txt).
 * Each scenario forks a real "child" process: it sends its messages on one end of an AF_UNIX SOCK_SEQPACKET socketpair, the other
 * end has SO_PASSCRED, so the KERNEL stamps the sender's real pid/uid/gid (SCM_CREDENTIALS).  The parent side is children_move()
 * with one slot.  The probe message is MSG_SESSION_FINISHED: it reaches the host hook `on_session_finished` only if the whole
 * wall (magic + credentials + length) let it through.
 * Verdicts (from the comments of child.c):
 *   credentials / serial / declared uid that do not match  ⇒ «MESSAGE REFUSED ... The child is killed»: SIGKILL to the pid,
 *                                                            child_dismiss(), the body is NEVER read (hook 0)
 *   wrong magic, longer than expected (-2), too short for a header, header announcing more bytes than arrived
 *                                                          ⇒ «DISCARDED»: the child stays, the next message is read normally
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   podman run --rm -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src -I/albero/benches/fuzz/child-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs gio-2.0) -lpam -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/child-credentials/test.c -o t.o && clang $F -c /albero/benches/fuzz/child-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && ./test'
 * Exit code 0 = every scenario as expected.  RXFUZZ_LOG=1 prints the product's log lines.
 */
#include "child.c"

#include <stdio.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
#include "common.h"

static int hook_finished;   /* how many times on_session_finished was called */
static int hook_dismiss;    /* how many times the host's dismiss hook was called (child_dismiss / child_free) */

static void h_finished(void *c, const char *u, uid_t uid) { (void)c; (void)u; (void)uid; hook_finished++; }
static void h_dismiss(void *c, const char *u, uid_t uid) { (void)c; (void)u; (void)uid; hook_dismiss++; }

enum scenario {
	S_GOOD, S_WRONG_UID, S_WRONG_PID, S_WRONG_SERIAL, S_WRONG_MAGIC, S_TOO_LONG, S_SHORT_BODY, S_SHORT_HEADER, S_N
};
static const char *const NAME[S_N] = {
	"right uid/pid/serial", "wrong uid", "wrong pid", "wrong serial", "wrong magic",
	"longer than expected (-2)", "header announces more bytes than were read", "shorter than a header",
};
/* the expected verdict */
struct want { bool refused; bool killed; int hook; };
static const struct want WANT[S_N] = {
	[S_GOOD]         = {false, false, 1},
	[S_WRONG_UID]    = {true,  true,  0},
	[S_WRONG_PID]    = {true,  true,  0},
	[S_WRONG_SERIAL] = {true,  true,  0},
	[S_WRONG_MAGIC]  = {false, false, 1},   /* discarded; the valid probe sent right after IS delivered */
	[S_TOO_LONG]     = {false, false, 1},
	[S_SHORT_BODY]   = {false, false, 1},
	[S_SHORT_HEADER] = {false, false, 1},
};

#define SERIAL 7

static void make_head(struct head *t, uint64_t serial, uint32_t declared_uid, uint32_t byte)
{
	memset(t, 0, sizeof *t);
	memcpy(t->magic, "FIG1", 4);
	t->kind = MSG_SESSION_FINISHED;
	t->version = CHILD_VERSION;
	t->serial = serial;
	t->declared_uid = declared_uid;
	t->byte = byte;
}

static void sender(int fd, enum scenario sc)
{
	struct head t;
	uint32_t uid = (uint32_t)getuid();
	signal(SIGTERM, SIG_IGN);              /* only SIGKILL (the wall's verdict) can end it */
	alarm(20);
	switch (sc) {
	case S_GOOD:
		make_head(&t, SERIAL, uid, 0);
		send(fd, &t, sizeof t, 0);
		break;
	case S_WRONG_UID:                      /* the parent believes the child has another uid; the message says the same as the parent */
	case S_WRONG_PID:                      /* the parent believes the child is another pid */
		make_head(&t, SERIAL, sc == S_WRONG_UID ? uid + 1000 : uid, 0);
		send(fd, &t, sizeof t, 0);
		break;
	case S_WRONG_SERIAL:
		make_head(&t, SERIAL + 1, uid, 0);
		send(fd, &t, sizeof t, 0);
		break;
	case S_WRONG_MAGIC:
		make_head(&t, SERIAL, uid, 0);
		memcpy(t.magic, "FIGX", 4);
		send(fd, &t, sizeof t, 0);
		make_head(&t, SERIAL, uid, 0);     /* the probe */
		send(fd, &t, sizeof t, 0);
		break;
	case S_TOO_LONG: {
		size_t n = MAX_ENVELOPE + 64;
		uint8_t *big = calloc(1, n);
		make_head(&t, SERIAL, uid, (uint32_t)(n - sizeof t));
		memcpy(big, &t, sizeof t);
		send(fd, big, n, 0);
		free(big);
		make_head(&t, SERIAL, uid, 0);
		send(fd, &t, sizeof t, 0);
		break;
	}
	case S_SHORT_BODY:                     /* the header says 100 body bytes, none follow */
		make_head(&t, SERIAL, uid, 100);
		send(fd, &t, sizeof t, 0);
		make_head(&t, SERIAL, uid, 0);
		send(fd, &t, sizeof t, 0);
		break;
	case S_SHORT_HEADER:
		send(fd, "FIG1", 4, 0);
		make_head(&t, SERIAL, uid, 0);
		send(fd, &t, sizeof t, 0);
		break;
	default:
		break;
	}
	pause();
	_exit(0);
}

static bool dead(pid_t p)     /* gone or zombie, up to 1 s */
{
	for (int i = 0; i < 100; i++) {
		char fp[64], buf[256];
		snprintf(fp, sizeof fp, "/proc/%ld/stat", (long)p);
		FILE *f = fopen(fp, "r");
		if (!f)
			return true;
		char st = '?';
		if (fgets(buf, sizeof buf, f)) {
			char *r = strrchr(buf, ')');
			if (r && r[1] == ' ')
				st = r[2];
		}
		fclose(f);
		if (st == 'Z')
			return true;
		usleep(10000);
	}
	return false;
}

static int run(enum scenario sc)
{
	int sv[2];
	if (socketpair(AF_UNIX, SOCK_SEQPACKET, 0, sv) != 0) { perror("socketpair"); return 1; }
	int on = 1;
	setsockopt(sv[0], SOL_SOCKET, SO_PASSCRED, &on, sizeof on);
	fcntl(sv[0], F_SETFL, fcntl(sv[0], F_GETFL) | O_NONBLOCK);   /* as in production: EAGAIN ends the loop */
	pid_t pid = fork();
	if (pid == 0) { close(sv[0]); sender(sv[1], sc); }
	close(sv[1]);
	pid_t other = 0;
	if (sc == S_WRONG_PID) {               /* the slot says the child is a DIFFERENT process (a sleeper) */
		other = fork();
		if (other == 0) { signal(SIGTERM, SIG_IGN); alarm(20); pause(); _exit(0); }
	}
	/* wait until the sender's messages are queued (poll does not consume) */
	struct pollfd p = {.fd = sv[0], .events = POLLIN};
	if (poll(&p, 1, 3000) != 1) { fprintf(stderr, "no message arrived\n"); return 1; }
	usleep(100000);

	children F;
	struct child G;
	memset(&F, 0, sizeof F);
	memset(&G, 0, sizeof G);
	F.cap = 1; F.v = &G;
	F.on_session_finished = h_finished;
	F.dismiss = h_dismiss;
	G.used = true;
	snprintf(G.user, sizeof G.user, "root");        /* getpwnam_r("root") = uid 0 ... */
	G.uid = getuid(); G.gid = getgid();
	if (G.uid != 0) { fprintf(stderr, "the test must run as root (uid 0) inside the container\n"); return 1; }
	G.pid = (sc == S_WRONG_PID) ? other : pid;
	if (sc == S_WRONG_UID) G.uid = 1000;           /* kernel says 0, the slot says 1000 */
	G.serial = SERIAL;
	G.fd = sv[0];
	G.showed_up = true;
	hook_finished = hook_dismiss = 0;

	struct pollfd fds[1] = {{.fd = sv[0], .revents = POLLIN}};
	children_move(&F, fds, 1, 1000);

	pid_t victim = G.pid > 0 ? G.pid : (sc == S_WRONG_PID ? other : pid);
	if (G.pid == 0) victim = (sc == S_WRONG_PID) ? other : pid;   /* reaped by children_move */
	bool killed = dead(victim);
	bool refused = hook_dismiss > 0 || !G.used || G.exiting;
	const struct want *w = &WANT[sc];
	bool ok = refused == w->refused && killed == w->killed && hook_finished == w->hook;
	printf("%-4s %-46s refused=%d killed=%d hook=%d   (expected %d %d %d)\n", ok ? "PASS" : "FAIL", NAME[sc],
	       refused, killed, hook_finished, w->refused, w->killed, w->hook);
	kill(pid, SIGKILL); waitpid(pid, NULL, 0);
	if (other) { kill(other, SIGKILL); waitpid(other, NULL, 0); }
	if (G.fd >= 0) close(G.fd);
	return ok ? 0 : 1;
}

int main(void)
{
	int bad = 0;
	for (int s = 0; s < S_N; s++)
		bad += run((enum scenario)s);
	printf("%s: %d of %d scenarios as expected\n", bad ? "FAILED" : "OK", S_N - bad, S_N);
	return bad ? 1 : 0;
}
