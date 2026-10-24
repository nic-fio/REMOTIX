/* 02-rootside-sweep-test.c — the sweep of a dead network side's leftovers stays in its
 * OWN cgroup (DECISIONS §11.50, review 2 L1 and its fix of 16 Oct 2026).  Driven by
 * `02-rootside-sweep.sh`, as root in a privileged container: two root sides with the
 * SAME network user (rxnet), each in a cgroup of its own.
 *
 *   root <tag>      a root side (`rootside_main()`, this file's walls: setuid rxnet)
 *   --net <tag>     its network side: attaches, writes /tmp/rx-sweep/<tag>.net.<pid>; the
 *                   first one of root side A also forks a LEFTOVER (setsid, sleeps for
 *                   ever, /tmp/rx-sweep/A.leftover) — what a hijacked network side would
 *                   leave behind holding the port
 *   --pam-helper    the PAM helper the root side re-executes
 */
#define _GNU_SOURCE
#include "helper.h"
#include "log.h"
#include "rootside.h"

#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define DIR_ "/tmp/rx-sweep"

int walls_apply(const struct rootside_options *o, char *why, size_t why_len)
{
	if (setgroups(0, NULL) != 0 || setgid(o->remotix_gid) != 0 || setuid(o->remotix_uid) != 0) {
		snprintf(why, why_len, "setuid: %s", strerror(errno));
		return -1;
	}
	return 0;
}

static void note(const char *name, long v)
{
	char p[128];
	FILE *f;

	snprintf(p, sizeof p, DIR_ "/%s", name);
	f = fopen(p, "w");
	if (f) {
		fprintf(f, "%ld\n", v);
		fclose(f);
	}
}

static int net_side(const char *tag)
{
	struct rxr_ready r;
	char n[64];
	struct stat st;

	if (!rootside_attach(3, 10000, &r))
		return 2;
	snprintf(n, sizeof n, "%s.net.%ld", tag, (long)getpid());
	note(n, (long)getpid());
	if (strcmp(tag, "A") == 0 && stat(DIR_ "/A.forked", &st) != 0) {
		note("A.forked", 1);
		pid_t p = fork();
		if (p == 0) {
			setsid();
			note("A.leftover", (long)getpid());
			for (;;)
				pause();
		}
	}
	for (;;)
		pause();
}

int main(int argc, char **argv)
{
	static char *net_argv[4] = { "rx-sweep-net", "--net", NULL, NULL };
	struct rootside_options o;
	struct passwd *pw;

	if (argc >= 3 && strcmp(argv[1], "--net") == 0)
		return net_side(argv[2]);
	if (argc >= 2 && strcmp(argv[1], "--pam-helper") == 0)
		return helper_main(argc, argv);
	if (argc < 3 || strcmp(argv[1], "root") != 0)
		return 2;
	pw = getpwnam("rxnet");
	if (!pw)
		return 2;
	net_argv[2] = argv[2];
	memset(&o, 0, sizeof o);
	o.udp_fd = -1;
	o.tcp_fd = -1;
	o.remotix_uid = pw->pw_uid;
	o.remotix_gid = pw->pw_gid;
	o.cap = 2;
	o.canvas_w = 1280;
	o.canvas_h = 720;
	o.audio_silence = true;
	o.net_argv = net_argv;
	o.denied_users_path = DIR_ "/denied";
	return rootside_main(&o);
}
