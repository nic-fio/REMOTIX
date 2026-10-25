/* 02-rootside-live-test.c — the root side LIVE (DECISIONS §11.50): a real
 * fork of the network side over the real channel, real PAM, a real child
 * born, signalled and reaped by the root side.  Driven by
 * `02-rootside-live.sh`, as root in a privileged container (users `rxnet`
 * — the network side —, `anna` with password `anna-pw`, `bruno` listed in
 * the denied file; PAM service `remotix` = pam_unix).
 *
 * The SAME binary plays three parts, as the product does:
 *   (no argument)        the root side: `rootside_main()` with this file's
 *                        strong `walls_apply()` (setgroups/setgid/setuid
 *                        to rxnet — lane 2's real walls are not tested here);
 *   --net                the network side (`rootside_attach(3)`): it asks,
 *                        and writes one «OK|NO what» line per check to
 *                        /tmp/rx-live/net.txt; the second one started (after
 *                        the malformed packet got the first killed) writes
 *                        «RESTARTED» and waits;
 *   --internal-child …   the child `child_birth()` exec'd: it writes its
 *                        argv, uids and signals to /tmp/rx-live/child-<user>.txt
 *                        and exits 7 (dario's hangs, ignoring SIGTERM).
 */
#define _GNU_SOURCE
#include "rootside.h"
#include "helper.h"
#include "log.h"

#include <errno.h>
#include <grp.h>
#include <poll.h>
#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#define DIR_ "/tmp/rx-live"

int walls_apply(const struct rootside_options *o, char *why, size_t why_len)
{
	if (setgroups(0, NULL) != 0 || setgid(o->remotix_gid) != 0 || setuid(o->remotix_uid) != 0) {
		snprintf(why, why_len, "setuid: %s", strerror(errno));
		return -1;
	}
	return 0;
}

static FILE *out;
static int fails;

static void check(int cond, const char *what)
{
	fprintf(out, "%s %s\n", cond ? "OK" : "NO", what);
	fflush(out);
	if (!cond)
		fails++;
}

static int v_out[64];
static uint64_t base_req;
static void on_verdict(void *c, uint64_t r, int o)
{
	(void)c;
	if (r >= base_req && r < base_req + 64)
		v_out[r - base_req] = o;
}
static uint64_t exited_serial;
static int exited_status;
static void on_exited(void *c, uint64_t s, int st)
{
	(void)c;
	exited_serial = s;
	exited_status = st;
}

static void pump(int ms, bool (*done)(void))
{
	for (int t = 0; t < ms; t += 50) {
		struct pollfd p = { rootside_descriptor(), POLLIN, 0 };
		if (done && done())
			return;
		if (p.fd < 0)
			return;
		(void)poll(&p, 1, 50);
		rootside_move();
	}
}

static uint64_t want;
static bool one_answered(void) { return v_out[want - base_req] >= 0; }

static int ask(uint64_t req, const char *u, const char *p, const char *rh)
{
	want = req;
	if (!rootside_auth(req, u, p, rh))
		return -2;
	pump(15000, one_answered);
	return v_out[req - base_req];
}

static int nbounds;
static bool bounds_answered(void)
{
	for (int i = 0; i < nbounds; i++)
		if (v_out[20 + i] < 0)
			return false;
	return true;
}
static bool child_exited(void) { return exited_serial != 0; }

static int net_side(void)
{
	struct rxr_ready r;
	struct rootside_born b;
	struct stat st;

	if (stat(DIR_ "/restarted.txt", &st) == 0) { /* the third network side */
		FILE *f = fopen(DIR_ "/restarted2.txt", "w");
		if (f) {
			fprintf(f, "RESTARTED2 uid=%d attached=%d\n", (int)getuid(),
			        (int)rootside_attach(3, 5000, &r));
			fclose(f);
		}
		for (;;)
			pause();
	}
	if (stat(DIR_ "/net.txt", &st) == 0) { /* the second network side */
		FILE *f = fopen(DIR_ "/restarted.txt", "w");
		if (f) {
			fprintf(f, "RESTARTED uid=%d attached=%d\n", (int)getuid(),
			        (int)rootside_attach(3, 5000, &r));
			fclose(f);
		}
		/* finding 10: it closes its channel and does not exit on SIGTERM —
		 * the root side must SIGKILL it and start a third one */
		sleep(1);
		signal(SIGTERM, SIG_IGN);
		close(3);
		/* review 2, L1: a leftover of uid rxnet — the root side must kill it
		 * before it starts the third network side */
		if (fork() == 0) {
			FILE *g = fopen(DIR_ "/leftover.pid", "w");
			if (g) {
				fprintf(g, "%d\n", (int)getpid());
				fclose(g);
			}
			for (;;)
				pause();
		}
		for (;;)
			pause();
	}
	out = fopen(DIR_ "/net.txt", "w");
	if (!out)
		return 2;
	check(rootside_attach(3, 30000, &r), "attached: READY from the root side");
	check(getuid() != 0 && r.remotix_uid == getuid(), "the network side runs as rxnet, READY says so");
	/* lane 4's review M4: the environment is an allow-list (02-rootside-live.sh sets both) */
	check(getenv("RX_LIVE_SECRET") == NULL && getenv("HOME_OF_ROOT") == NULL,
	      "a variable of the root side's environment outside the allow-list does not cross the exec");
	check(getenv("LANG") && strcmp(getenv("LANG"), "C.UTF-8") == 0 && getenv("TZ")
	      && strcmp(getenv("TZ"), "UTC") == 0 && getenv("REMOTIX_LIVE_SWITCH")
	      && getenv("DBUS_SYSTEM_BUS_ADDRESS")
	      && strcmp(getenv("DBUS_SYSTEM_BUS_ADDRESS"), "unix:path=/run/dbus/system_bus_socket") == 0
	      && getenv("PATH") && strcmp(getenv("PATH"), "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin") == 0,
	      "LANG, TZ, REMOTIX_* and DBUS_SYSTEM_BUS_ADDRESS cross it; PATH is the fixed one");
	rootside_hook_verdict(on_verdict, NULL);
	rootside_hook_child_exited(on_exited, NULL);
	for (int i = 0; i < 64; i++)
		v_out[i] = -1;
	base_req = 100;
	check(ask(100, "root", "x", "192.0.2.1") == RXR_NO, "AUTH root: NO before PAM (uid 0)");
	check(ask(101, "rx-nobody-77", "x", "192.0.2.1") == RXR_NO, "AUTH unknown name: NO before PAM");
	check(ask(102, "bruno", "bruno-pw", "192.0.2.1") == RXR_NO, "AUTH bruno (denied-users): NO before PAM");
	check(ask(103, "anna", "wrong", "192.0.2.1") == RXR_NO, "AUTH anna wrong password: NO (PAM)");
	check(ask(106, "elena", "wrong", "192.0.2.1") == RXR_NO,
	      "AUTH elena (a 6000-byte passwd entry): NO from PAM, not «not checked» (finding 7)");
	check(ask(104, "anna", "anna-pw", "192.0.2.1") == RXR_YES, "AUTH anna right password: YES (PAM)");
	check(rootside_has_grant("anna", "192.0.2.1") && !rootside_has_grant("anna", "192.0.2.9")
	      && !rootside_has_grant("bruno", "192.0.2.1"),
	      "the grant is kept for (anna, 192.0.2.1) only");
	check(rootside_spawn("anna", "192.0.2.9", 1280, 720, 5000, &b) == ROOTSIDE_NO_GRANT,
	      "SPAWN for anna from another address: no grant");
	uint64_t t0 = log_now_ms();
	int sp = rootside_spawn("anna", "192.0.2.1", 1280, 720, 10000, &b);
	uint64_t ms_first = log_now_ms() - t0;
	check(sp == 0 && b.fd >= 0 && strcmp(b.user, "anna") == 0 && b.uid != 0 && b.pid > 0,
	      "SPAWN anna: SPAWNED with pid, uid and the socket end");
	check(!rootside_has_grant("anna", "192.0.2.1")
	      && rootside_spawn("anna", "192.0.2.1", 1280, 720, 2000, &b) == ROOTSIDE_NO_GRANT,
	      "the grant is single use");
	pump(10000, child_exited);
	check(exited_serial != 0 && WIFEXITED(exited_status) && WEXITSTATUS(exited_status) == 7,
	      "CHILD_EXITED from the root side, with the child's status (exit 7)");
	/* ⭐ the cost of the synchronous SPAWN wait: the first birth enrols anna in the
	 *    card's groups (usermod) when this machine has a render node, the second
	 *    finds her already enrolled */
	{
		uint64_t ms_second = 0;
		exited_serial = 0;
		check(ask(107, "anna", "anna-pw", "192.0.2.1") == RXR_YES, "AUTH anna again: YES");
		t0 = log_now_ms();
		sp = rootside_spawn("anna", "192.0.2.1", 1280, 720, 10000, &b);
		ms_second = log_now_ms() - t0;
		check(sp == 0, "SPAWN anna a second time: SPAWNED");
		if (sp == 0)
			close(b.fd);
		pump(10000, child_exited);
		fprintf(out, "SPAWN_MS first=%llu second=%llu\n", (unsigned long long)ms_first,
		        (unsigned long long)ms_second);
		fflush(out);
	}
	check(rootside_close_orphan("anna", 5000, &b) == RXR_REF_NO_ORPHAN,
	      "CLOSE_ORPHAN anna with no remotix session in logind: refused");
	check(rootside_close_orphan("elena", 5000, &b) == RXR_REF_NO_ORPHAN,
	      "CLOSE_ORPHAN elena: refused — bruno's session files only LOOK like hers to a "
	      "chunked reader (finding 9)");
	/* finding 1: carla has a remotix session file (written by the .sh) — the
	 * birth without a password is a CLOSE-ONLY child (its argv, child.txt) */
	{
		int r;

		pump(1300, NULL); /* R1: the root side has now been up for more than abandon_s */
		r = rootside_close_orphan("carla", 10000, &b);
		check(r == 0 && b.fd >= 0 && strcmp(b.user, "carla") == 0,
		      "CLOSE_ORPHAN carla (a live remotix session in logind): SPAWNED");
		if (r == 0) {
			close(b.fd);
			exited_serial = 0;
			pump(10000, child_exited);
			check(exited_serial == b.serial, "… and its CHILD_EXITED");
		}
		/* R1: carla's child has only just left, so the root side's own clock says she is not
		 * abandoned yet — TOO_SOON now, before the per-uid hold (RATE) is even asked */
		check(rootside_close_orphan("carla", 5000, &b) == RXR_REF_TOO_SOON,
		      "a second CLOSE_ORPHAN for carla right after her child left: refused TOO_SOON, no birth (R1)");
		pump(1300, NULL);
		check(rootside_close_orphan("carla", 5000, &b) == RXR_REF_RATE,
		      "after abandon_s but within 30 s of the first birth: refused RATE, no birth (review 2 M1, review 4 B 22)");
	}
	/* finding 2: dario's child hangs (ignores SIGTERM, never reads): it must be
	 * SIGTERMed then SIGKILLed by the root side once this network side dies */
	check(ask(105, "dario", "dario-pw", "192.0.2.1") == RXR_YES, "AUTH dario: YES");
	check(rootside_spawn("dario", "192.0.2.1", 1280, 720, 10000, &b) == 0,
	      "SPAWN dario: SPAWNED (a child that will hang)");
	check(rootside_signal(424242, SIGKILL), "SIGNAL for a serial that is not the root side's: sent");
	pump(500, NULL);
	check(!rootside_lost(), "… ignored, and the channel is still up");

	/* the bounds: 25 AUTH at once */
	nbounds = 25;
	for (int i = 0; i < nbounds; i++)
		(void)rootside_auth(base_req + 20 + i, "anna", "wrong", "192.0.2.1");
	pump(20000, bounds_answered);
	{
		int nc = 0, no = 0;
		for (int i = 0; i < nbounds; i++) {
			nc += v_out[20 + i] == RXR_NOT_CHECKED;
			no += v_out[20 + i] == RXR_NO;
		}
		char d[160];
		snprintf(d, sizeof d, "25 AUTH at once: %d NO, %d not checked (16 in flight max)", no, nc);
		check(no <= 16 && nc >= 9 && no + nc == 25, d);
	}
	fprintf(out, "%s\n", fails ? "RED" : "GREEN");
	fprintf(out, "MALFORMED_SENT\n");
	fflush(out);
	/* the malformed packet: 3 bytes — the root side must kill us */
	(void)send(rootside_descriptor(), "abc", 3, MSG_NOSIGNAL);
	sleep(10);
	fprintf(out, "NO still alive 10 s after a malformed packet\n");
	fflush(out);
	return 1;
}

static int child_part(int argc, char **argv)
{
	char path[128];
	FILE *f;

	/* one file per user: each child runs as its own uid */
	snprintf(path, sizeof path, DIR_ "/child-%s.txt", argc > 2 ? argv[2] : "?");
	f = fopen(path, "w");
	uid_t r, e, s;

	if (f) {
		getresuid(&r, &e, &s);
		fprintf(f, "uid %d %d %d ppid %d argv", (int)r, (int)e, (int)s, (int)getppid());
		for (int i = 0; i < argc; i++)
			fprintf(f, " %s", argv[i]);
		fprintf(f, "\n");
		/* finding 3: the dispositions and the mask that crossed the exec */
		{
			FILE *st = fopen("/proc/self/status", "re");
			char l[256];
			while (st && fgets(l, sizeof l, st))
				if (strncmp(l, "SigIgn:", 7) == 0 || strncmp(l, "SigBlk:", 7) == 0
				    || strncmp(l, "SigCgt:", 7) == 0)
					fprintf(f, "%s", l);
			if (st)
				fclose(st);
		}
		fclose(f);
	}
	if (argc > 2 && strcmp(argv[2], "dario") == 0) { /* the hung child of finding 2 */
		signal(SIGTERM, SIG_IGN);
		for (;;)
			pause();
	}
	return 7;
}

int main(int argc, char **argv)
{
	struct passwd *pw;
	static char *net_argv[] = { "remotix-net", "--net", NULL };
	struct rootside_options o;

	if (argc >= 2 && strcmp(argv[1], "--net") == 0)
		return net_side();
	if (argc >= 2 && strcmp(argv[1], "--internal-child") == 0)
		return child_part(argc, argv);
	/* the PAM helper re-executes this binary, as it does the product's main() */
	if (argc >= 2 && strcmp(argv[1], "--pam-helper") == 0)
		return helper_main(argc, argv);
	pw = getpwnam("rxnet");
	if (!pw) {
		fprintf(stderr, "no user rxnet\n");
		return 2;
	}
	memset(&o, 0, sizeof o);
	o.udp_fd = -1;
	o.tcp_fd = -1;
	o.remotix_uid = pw->pw_uid;
	o.remotix_gid = pw->pw_gid;
	o.cap = 4;
	o.canvas_w = 1920;
	o.canvas_h = 1080;
	o.audio_silence = true;
	o.abandon_s = 1; /* R1: CLOSE_ORPHAN only after 1 s without a child of that uid */
	o.net_argv = net_argv;
	o.denied_users_path = DIR_ "/denied-users";
	/* ⭐ RX_LIVE_JOURNAL=1: the root side with --journal, as every package unit runs it —
	 *    opened FIRST, as main.c does, so its socket takes the lowest free fd (3): the
	 *    case 676af717 cured (the fork wrote its lines into the root channel). */
	if (getenv("RX_LIVE_JOURNAL") && strcmp(getenv("RX_LIVE_JOURNAL"), "1") == 0)
		(void)log_journal(true);
	return rootside_main(&o);
}
