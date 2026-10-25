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
 *   --journald           ⭐ 1.6 (R8 B): a stand-in for journald (/run/systemd/journal/socket, SO_PASSCRED): it writes
 *                        «pid=<credential pid> <area> <message>» to /tmp/rx-live/journal.txt — the pid is the one the kernel
 *                        stamps, as THIS side sees it;
 *   --logind             ⭐ a stand-in for logind on the "system bus" (a GDBusServer on /run/dbus/system_bus_socket, there is no
 *                        dbus-daemon in the image): ListSessions and the session's properties, so the network side's
 *                        `sentinel_*` has something to ask;
 *   --internal-child …   the child `child_birth()` exec'd: it writes its
 *                        argv, uids and signals to /tmp/rx-live/child-<user>.txt
 *                        and exits 7 (dario's hangs, ignoring SIGTERM).
 */
#define _GNU_SOURCE
#include "rootside.h"
#include "child.h"
#include "helper.h"
#include "log.h"

#include "sentinel.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <grp.h>
#include <poll.h>
#include <pwd.h>
#include <sched.h>
#include <signal.h>
#include <stdarg.h>
#include <sys/mount.h>
#include <sys/un.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>

#define DIR_ "/tmp/rx-live"

/* ⭐ 1.6 (R8 B): the network side is born PID 1 of a PID namespace of its own, as the product's `walls_fork_pidns()` does it */
pid_t walls_fork_pidns(void)
{
	return (pid_t)syscall(SYS_clone, CLONE_NEWPID | SIGCHLD, 0, 0, 0, 0);
}

/* The stand-in walls: a mount namespace with a NEW /proc (the namespace's own, so the network side sees itself only), then the
 * identity.  The product's real walls are tested by 02-walls-test.c. */
int walls_apply(const struct rootside_options *o, char *why, size_t why_len)
{
	if (unshare(CLONE_NEWNS) != 0 || mount(NULL, "/", NULL, MS_REC | MS_SLAVE, NULL) != 0 ||
	    mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, "hidepid=invisible") != 0) {
		snprintf(why, why_len, "the PID namespace's /proc: %s", strerror(errno));
		return -1;
	}
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


/* ── ⭐ 1.6 (R8 B): what the live test adds ────────────────────────────────────────────────────────────────────────── */

static bool gone_seen;
static char gone_user[64];
static void on_gone(void *c, uid_t uid, const char *user)
{
	(void)c;
	(void)uid;
	gone_seen = true;
	snprintf(gone_user, sizeof gone_user, "%s", user);
}

static bool exists_(const char *p)
{
	struct stat st;

	return stat(p, &st) == 0;
}

static int count_procs(char *names, size_t cap)
{
	DIR *d = opendir("/proc");
	struct dirent *e;
	int n = 0;

	if (names && cap)
		names[0] = '\0';
	while (d && (e = readdir(d)) != NULL)
		if (e->d_name[0] >= '1' && e->d_name[0] <= '9') {
			n++;
			if (names && strlen(names) + strlen(e->d_name) + 2 < cap)
				snprintf(names + strlen(names), cap - strlen(names), "%s ", e->d_name);
		}
	if (d)
		closedir(d);
	return n;
}

/* poll the channel for `ms`, dispatching what comes */
static void wait_events(int ms)
{
	struct pollfd p = { rootside_descriptor(), POLLIN, 0 };

	if (p.fd >= 0)
		(void)poll(&p, 1, ms);
	else
		usleep((useconds_t)ms * 1000);
	rootside_move();
}

/* the desktop of fiona: a stage in a scope of its own, born by the root side's process before `rootside_main()` (the stand-in for
 * what `setsid --fork` makes in the product), listed in logind's files as a `remotix` session.  It lives until /tmp/rx-live/stage-die
 * exists.  Its parent is the container's init (a double fork), outside the scope. */
static bool stage_ok;
static void start_stage(void)
{
	struct passwd *f = getpwnam("fiona");
	int p[2];
	pid_t a;
	char c = 0;
	FILE *s;

	if (!f || pipe(p) != 0)
		return;
	if (mkdir("/sys/fs/cgroup/session-c80.scope", 0755) != 0 && errno != EEXIST) {
		s = fopen(DIR_ "/stage.txt", "w");
		if (s) {
			fprintf(s, "NOSTAGE no cgroup (%s)\n", strerror(errno));
			fclose(s);
		}
		return;
	}
	a = fork();
	if (a == 0) {
		pid_t b = fork();

		if (b != 0)
			_exit(0);
		setsid();
		prctl(PR_SET_NAME, "rx-stage");
		{
			FILE *g = fopen("/sys/fs/cgroup/session-c80.scope/cgroup.procs", "w");
			bool ok = g && fprintf(g, "%d\n", (int)getpid()) > 0;

			if (g && fclose(g) != 0)
				ok = false;
			if (!ok || setgroups(0, NULL) != 0 || setgid(f->pw_gid) != 0 || setuid(f->pw_uid) != 0) {
				(void)!write(p[1], "n", 1);
				_exit(1);
			}
		}
		(void)!write(p[1], "y", 1);
		for (int i = 0; i < 1200 && !exists_(DIR_ "/stage-die"); i++)
			usleep(100000);
		_exit(0);
	}
	close(p[1]);
	(void)waitpid(a, NULL, 0);
	{
		struct pollfd pf = { p[0], POLLIN, 0 };

		if (poll(&pf, 1, 5000) == 1 && read(p[0], &c, 1) == 1 && c == 'y') {
			s = fopen("/run/systemd/sessions/c80", "w");
			if (s) {
				fprintf(s, "UID=%u\nUSER=fiona\nSTATE=closing\nSERVICE=remotix\nSCOPE=session-c80.scope\n", (unsigned)f->pw_uid);
				fclose(s);
				stage_ok = true;
			}
		}
	}
	close(p[0]);
	s = fopen(DIR_ "/stage.txt", "w");
	if (s) {
		fprintf(s, stage_ok ? "STAGE ok\n" : "NOSTAGE the stage could not enter its scope\n");
		fclose(s);
	}
}

static bool stage_file_ok(void)
{
	char l[64] = "";
	FILE *f = fopen(DIR_ "/stage.txt", "r");

	if (f && fgets(l, sizeof l, f)) {
		fclose(f);
		return strncmp(l, "STAGE ok", 8) == 0;
	}
	if (f)
		fclose(f);
	return false;
}

/* ── the stand-in for journald ── */
static int journald_part(void)
{
	struct sockaddr_un a = { .sun_family = AF_UNIX, .sun_path = "/run/systemd/journal/socket" };
	int one = 1, s;
	FILE *o;

	(void)mkdir("/run/systemd/journal", 0755);
	unlink(a.sun_path);
	s = socket(AF_UNIX, SOCK_DGRAM, 0);
	if (s < 0 || bind(s, (struct sockaddr *)&a, sizeof a) != 0 || setsockopt(s, SOL_SOCKET, SO_PASSCRED, &one, sizeof one) != 0)
		return 2;
	chmod(a.sun_path, 0666);
	o = fopen(DIR_ "/journal.txt", "w");
	if (!o)
		return 2;
	for (;;) {
		char buf[2048], ctl[CMSG_SPACE(sizeof(struct ucred))], *m;
		struct iovec io = { buf, sizeof buf - 1 };
		struct msghdr h = { .msg_iov = &io, .msg_iovlen = 1, .msg_control = ctl, .msg_controllen = sizeof ctl };
		ssize_t n = recvmsg(s, &h, 0);
		struct ucred cr = { -1, 0, 0 };

		if (n <= 0)
			continue;
		buf[n] = '\0';
		for (struct cmsghdr *c = CMSG_FIRSTHDR(&h); c; c = CMSG_NXTHDR(&h, c))
			if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_CREDENTIALS)
				memcpy(&cr, CMSG_DATA(c), sizeof cr);
		m = memmem(buf, (size_t)n, "MESSAGE\n", 8);
		fprintf(o, "pid=%d uid=%d %.100s\n", (int)cr.pid, (int)cr.uid, m && (size_t)(m - buf) + 16 < (size_t)n ? m + 16 : "?");
		fflush(o);
	}
}

/* ── the stand-in for logind, on a GDBusServer (the image has no dbus-daemon) ── */
static const gchar logind_xml[] =
	"<node>"
	"<interface name='org.freedesktop.DBus'><method name='Hello'><arg type='s' direction='out'/></method></interface>"
	"<interface name='org.freedesktop.login1.Manager'><method name='ListSessions'><arg type='a(susso)' direction='out'/></method></interface>"
	"<interface name='org.freedesktop.login1.Session'>"
	"<property name='Type' type='s' access='read'/><property name='Class' type='s' access='read'/>"
	"<property name='Remote' type='b' access='read'/><property name='State' type='s' access='read'/>"
	"</interface></node>";

static void logind_call(GDBusConnection *c, const gchar *sender, const gchar *path, const gchar *iface, const gchar *method,
                        GVariant *params, GDBusMethodInvocation *inv, gpointer data)
{
	(void)c; (void)sender; (void)path; (void)params; (void)data;
	if (g_strcmp0(method, "Hello") == 0) {
		g_dbus_method_invocation_return_value(inv, g_variant_new("(s)", ":1.77"));
	} else if (g_strcmp0(iface, "org.freedesktop.login1.Manager") == 0 && g_strcmp0(method, "ListSessions") == 0) {
		GVariantBuilder b;
		struct passwd *a = getpwnam("anna");

		g_variant_builder_init(&b, G_VARIANT_TYPE("a(susso)"));
		g_variant_builder_add(&b, "(susso)", "c90", (guint32)(a ? a->pw_uid : 0), "anna", "seat0", "/org/freedesktop/login1/session/c90");
		g_dbus_method_invocation_return_value(inv, g_variant_new("(a(susso))", &b));
	} else {
		g_dbus_method_invocation_return_dbus_error(inv, "org.freedesktop.DBus.Error.UnknownMethod", method);
	}
}

static GVariant *logind_prop(GDBusConnection *c, const gchar *sender, const gchar *path, const gchar *iface, const gchar *prop,
                             GError **err, gpointer data)
{
	(void)c; (void)sender; (void)path; (void)iface; (void)err; (void)data;
	if (g_strcmp0(prop, "Type") == 0)
		return g_variant_new_string("wayland");
	if (g_strcmp0(prop, "Class") == 0)
		return g_variant_new_string("user");
	if (g_strcmp0(prop, "Remote") == 0)
		return g_variant_new_boolean(FALSE);
	return g_variant_new_string("active");
}

static gboolean logind_new_connection(GDBusServer *srv, GDBusConnection *c, gpointer data)
{
	static const GDBusInterfaceVTable vt = { logind_call, logind_prop, NULL, { 0 } };
	GDBusNodeInfo *n = g_dbus_node_info_new_for_xml(logind_xml, NULL);

	(void)srv; (void)data;
	g_object_ref(c);
	g_dbus_connection_register_object(c, "/org/freedesktop/DBus", n->interfaces[0], &vt, NULL, NULL, NULL);
	g_dbus_connection_register_object(c, "/org/freedesktop/login1", n->interfaces[1], &vt, NULL, NULL, NULL);
	g_dbus_connection_register_object(c, "/org/freedesktop/login1/session/c90", n->interfaces[2], &vt, NULL, NULL, NULL);
	return TRUE;
}

static int logind_part(void)
{
	GError *err = NULL;
	gchar *guid = g_dbus_generate_guid();
	GDBusServer *srv;

	(void)mkdir("/run/dbus", 0755);
	unlink("/run/dbus/system_bus_socket");
	srv = g_dbus_server_new_sync("unix:path=/run/dbus/system_bus_socket", G_DBUS_SERVER_FLAGS_AUTHENTICATION_ALLOW_ANONYMOUS, guid,
	                             NULL, NULL, &err);
	if (!srv) {
		fprintf(stderr, "fake logind: %s\n", err ? err->message : "?");
		return 2;
	}
	chmod("/run/dbus/system_bus_socket", 0666);
	g_signal_connect(srv, "new-connection", G_CALLBACK(logind_new_connection), NULL);
	g_dbus_server_start(srv);
	g_main_loop_run(g_main_loop_new(NULL, FALSE));
	return 0;
}

static int net_nologind(void)
{
	struct rxr_ready r;
	RediscoveredDesktop v[4];
	char why[200] = "";
	uint64_t t0;
	int n;

	out = fopen(DIR_ "/net.txt", "w");
	if (!out)
		return 2;
	check(rootside_attach(3, 30000, &r), "attached: READY from the root side");
	t0 = log_now_ms();
	n = rootside_wait_found(v, 4, 5000, why, sizeof why);
	check(n == -1 && strstr(why, "could not look"), "no logind sessions folder: the list says «could not look» (FOUND_END UNKNOWN)");
	check(log_now_ms() - t0 < 3000, "... at once, not at the end of its wait");
	fprintf(out, "%s\n", fails ? "RED" : "GREEN");
	fflush(out);
	for (;;)
		pause();
}

/* ⭐ The dead root side reaches this process TWICE, a few microseconds apart: the channel's other end closing is an EOF on fd 3 (the file table is
 *    released first), and PR_SET_PDEATHSIG (armed in the fork before the exec by rootside.c; it survives the exec of a normal binary) sends SIGTERM
 *    when the parent's exit is announced.  The product stops on either (main.c's SIGTERM handler; rootside_lost()).  The EOF is what this case
 *    proves, so SIGTERM is BLOCKED here — it stays pending, and `sigpending()` tells afterwards whether the second route also fired: no race
 *    between the two decides the case. */

static int net_rootdeath(void)
{
	struct rxr_ready r;
	uint64_t t0;

	out = fopen(DIR_ "/net.txt", "w");
	if (!out)
		return 2;
	{
		sigset_t only_term;

		sigemptyset(&only_term);
		sigaddset(&only_term, SIGTERM);
		sigprocmask(SIG_BLOCK, &only_term, NULL);
	}
	check(rootside_attach(3, 30000, &r), "attached: READY from the root side");
	fprintf(out, "ATTACHED\n");
	fflush(out);
	t0 = log_now_ms();
	while (!rootside_lost() && log_now_ms() - t0 < 30000)
		wait_events(200);
	fprintf(out, "%s after %llu ms\n", rootside_lost() ? "ROOT_EOF" : "ROOT_EOF_NOT_SEEN", (unsigned long long)(log_now_ms() - t0));
	{
		sigset_t pend;

		sigpending(&pend);
		fprintf(out, "SIGTERM_PENDING=%d (PDEATHSIG of the dead root side)\n", sigismember(&pend, SIGTERM) == 1);
	}
	fflush(out);
	return rootside_lost() ? 0 : 1;
}

static void found_line(FILE *f, const char *tag)
{
	RediscoveredDesktop v[4];
	char why[160] = "";
	int n = rootside_wait_found(v, 4, 5000, why, sizeof why);

	fprintf(f, "%s n=%d user=%s\n", tag, n, n > 0 ? v[0].user : "-");
	fflush(f);
}

/* ⭐ main() installs a SIGTERM handler before anything else (as PID 1 the default action would be IGNORED): so do the network sides of
 *    this test — except the second, which ignores it on purpose (finding 10) */
static void live_term(int sig)
{
	(void)sig;
	_exit(0);
}

static int net_side(void)
{
	struct rxr_ready r;
	struct rootside_born b;
	struct stat st;

	signal(SIGTERM, live_term);
	/* ⚠ REMOTIX_LIVE_*: only REMOTIX_* crosses the allow-list of the network side's environment */
	if (getenv("REMOTIX_LIVE_MODE") && strcmp(getenv("REMOTIX_LIVE_MODE"), "nologind") == 0)
		return net_nologind();
	if (getenv("REMOTIX_LIVE_MODE") && strcmp(getenv("REMOTIX_LIVE_MODE"), "rootdeath") == 0)
		return net_rootdeath();
	if (stat(DIR_ "/restarted2.txt", &st) == 0) { /* the fourth: after the kill -9 of the third alone */
		FILE *f = fopen(DIR_ "/restarted3.txt", "w");
		if (f) {
			fprintf(f, "RESTARTED3 uid=%d attached=%d\n", (int)getuid(), (int)rootside_attach(3, 5000, &r));
			found_line(f, "FOUND4");
			fclose(f);
		}
		for (;;)
			pause();
	}
	if (stat(DIR_ "/restarted.txt", &st) == 0) { /* the third network side */
		FILE *f = fopen(DIR_ "/restarted2.txt", "w");
		if (f) {
			fprintf(f, "RESTARTED2 uid=%d attached=%d\n", (int)getuid(),
			        (int)rootside_attach(3, 5000, &r));
			found_line(f, "FOUND3");
			fclose(f);
		}
		for (;;)
			pause();
	}
	if (stat(DIR_ "/net.txt", &st) == 0) { /* the second network side */
		FILE *f = fopen(DIR_ "/restarted.txt", "w");
		if (f) {
			RediscoveredDesktop v[4];
			char why[160] = "";
			int n;

			fprintf(f, "RESTARTED uid=%d attached=%d\n", (int)getuid(),
			        (int)rootside_attach(3, 5000, &r));
			/* ⭐ the desktop of fiona is still alive across the restart: the root side finds it again and says so */
			n = rootside_wait_found(v, 4, 5000, why, sizeof why);
			fprintf(f, "FOUND_AGAIN_AFTER_RESTART n=%d user=%s\n", n, n > 0 ? v[0].user : "-");
			fflush(f);
			if (n == 1) { /* … and when it dies, FOUND_GONE */
				rootside_hook_found_gone(on_gone, NULL);
				close(open(DIR_ "/stage-die", O_CREAT | O_WRONLY, 0666));
				for (int i = 0; i < 100 && !gone_seen; i++)
					wait_events(100);
				fprintf(f, "GONE_SEEN=%d user=%s\n", gone_seen, gone_seen ? gone_user : "-");
			}
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

			prctl(PR_SET_NAME, "rx-leftover"); /* seen from OUTSIDE the PID namespace by its name */
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
	/* ⭐ 1.6 (R8 B): PID 1 of its own PID namespace, a /proc that lists only itself — and the channel works across it (the root side's
	 *    pid is not visible here: READY was accepted with the kernel's stamp pid 0) */
	{
		char names[128];

		check(getpid() == 1 && getppid() == 0, "the network side is PID 1 of its own PID namespace, parent 0");
		check(count_procs(names, sizeof names) == 1 && strcmp(names, "1 ") == 0, "its /proc lists one process: itself (1)");
		fprintf(out, "INSIDE pid=%d procs=%s\n", (int)getpid(), names);
	}
	/* ⭐ the desktops the root side found, over FOUND_AGAIN/FOUND_END (fiona's stage, set up by the harness before the root side) */
	{
		RediscoveredDesktop v[4];
		char why[160] = "";
		int n = rootside_wait_found(v, 4, 5000, why, sizeof why);

		if (stage_file_ok())
			check(n == 1 && strcmp(v[0].user, "fiona") == 0 && v[0].stage > 0 && v[0].sessions == 1,
			      "FOUND_AGAIN: the root side found fiona's live desktop and told this network side (pid 1 here, no /proc to read)");
		else
			fprintf(out, "?? no desktop of fiona in this container (%s): FOUND_AGAIN not looked at\n", why);
	}
	/* ⭐ the journal: the line this side writes reaches the stand-in journald with the pid the kernel stamps (the real pid, not 1) */
	if (getenv("REMOTIX_LIVE_JOURNAL") && strcmp(getenv("REMOTIX_LIVE_JOURNAL"), "1") == 0) {
		(void)log_journal(true);
		registro_dice("livenet", "LIVE-NET-JOURNAL-MARK from the network side");
	}
	/* ⭐ the sentinel, over the "system bus" (a path socket: the walls leave it): the stand-in logind answers ListSessions and GetAll */
	if (getenv("REMOTIX_LIVE_LOGIND") && strcmp(getenv("REMOTIX_LIVE_LOGIND"), "1") == 0) {
		sentinel *g = sentinel_open();
		char w[128] = "";

		check(g != NULL, "sentinel_open(): the system bus (a path socket) is reachable from the network side");
		check(g && sentinel_local(g, "anna", w, sizeof w) && strstr(w, "c90"),
		      "sentinel_local(anna): her seated graphical session is found over the bus");
		check(g && !sentinel_local(g, "carla", w, sizeof w), "sentinel_local(carla): none");
	}
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
	/* ⭐ 1.6 (R8 B) — `[M]` boxes on v15c: after a login «MESSAGE REFUSED … written by pid 0, and the child is pid 94513», the child killed:
	 *    the child is born in the HOST's PID namespace, and this process is PID 1 of its own, where the kernel stamps every sender from
	 *    outside with pid 0.  A REAL child (born by the root side, exec'd as `--internal-child`, a different PID namespace) writes to its
	 *    socket; this side reads the kernel's stamp and asks the product's rules (`child_credentials_ok`, the wall of child.c). */
	{
		struct rootside_born cb;
		int r3;

		close(open(DIR_ "/child-send", O_CREAT | O_WRONLY, 0666));
		check(ask(108, "anna", "anna-pw", "192.0.2.1") == RXR_YES, "AUTH anna once more: YES (for the child that writes to this side)");
		r3 = rootside_spawn("anna", "192.0.2.1", 1280, 720, 10000, &cb);
		check(r3 == 0 && cb.pid > 1 && getpid() == 1, "SPAWN anna: a real child outside this PID namespace (its pid there is not 1 or ours)");
		if (r3 == 0) {
			char buf[64], ctl[CMSG_SPACE(sizeof(struct ucred))], why[256] = "";
			struct iovec io = { buf, sizeof buf };
			struct msghdr h = { .msg_iov = &io, .msg_iovlen = 1, .msg_control = ctl, .msg_controllen = sizeof ctl };
			struct pollfd pf = { cb.fd, POLLIN, 0 };
			struct ucred cr = { -1, 0, 0 };
			bool have = false;
			ssize_t n = poll(&pf, 1, 8000) == 1 ? recvmsg(cb.fd, &h, 0) : -1;

			for (struct cmsghdr *c = n > 0 ? CMSG_FIRSTHDR(&h) : NULL; c; c = CMSG_NXTHDR(&h, c))
				if (c->cmsg_level == SOL_SOCKET && c->cmsg_type == SCM_CREDENTIALS) {
					memcpy(&cr, CMSG_DATA(c), sizeof cr);
					have = true;
				}
			check(n > 0 && have && cr.pid == 0 && cr.uid == cb.uid,
			      "the real child's message arrives stamped pid 0 (outside the namespace) and anna's uid — the stamp the old rule could not compare");
			check(child_credentials_ok(cb.uid, cb.gid, cb.pid, cb.serial, true, have, cr.pid, cr.uid, cr.gid, why, sizeof why),
			      "… and the product's wall accepts it inside the namespace (remote rules)");
			check(!child_credentials_ok(cb.uid, cb.gid, cb.pid, cb.serial, false, have, cr.pid, cr.uid, cr.gid, why, sizeof why),
			      "… while the single-process rule (pid == the child's) refuses it: the defect of the boxes, now not applied here");
			close(cb.fd);
			exited_serial = 0;
			pump(10000, child_exited);
		}
		unlink(DIR_ "/child-send");
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
		snprintf(d, sizeof d, "25 AUTH at once for anna: %d NO, %d not checked (burst 8; 5 refused-or-in-flight per user and address)", no, nc);
		check(no <= ROOTSIDE_LOGIN_PAIR_LIMIT && no + nc == 25, d);
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
	/* ⭐ 1.6 (R8 B): a child that writes to its parent (fd 3, the agreed place) when the network side asks for it with a file */
	if (argc > 2 && strcmp(argv[2], "anna") == 0 && exists_(DIR_ "/child-send"))
		(void)!send(3, "live-child-hello", 16, MSG_NOSIGNAL);
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
	if (argc >= 2 && strcmp(argv[1], "--journald") == 0)
		return journald_part();
	if (argc >= 2 && strcmp(argv[1], "--logind") == 0)
		return logind_part();
	if (argc >= 2 && strcmp(argv[1], "--probe-sentinel") == 0) { /* what the network side asks the bus, alone (debugging aid) */
		sentinel *g = sentinel_open();
		char w[128] = "";

		printf("open=%d anna=%d carla=%d (%s)\n", g != NULL, g && sentinel_local(g, "anna", w, sizeof w),
		       g && sentinel_local(g, "carla", w, sizeof w), w);
		return g ? 0 : 1;
	}
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
	/* ⭐ 1.5: the root side started the way a careless launcher starts it — SIGHUP, SIGQUIT and SIGWINCH ignored, SIGURG
	 *    blocked: the children must still be born with all at their default (child.c, before the execve). */
	{
		sigset_t blk;

		signal(SIGHUP, SIG_IGN);
		signal(SIGQUIT, SIG_IGN);
		signal(SIGWINCH, SIG_IGN);
		sigemptyset(&blk);
		sigaddset(&blk, SIGURG);
		sigprocmask(SIG_BLOCK, &blk, NULL);
	}
	/* ⭐ 1.6 (R8 B): the live desktop of fiona, before the root side looks for the desktops found again */
	if (!getenv("RX_LIVE_MODE") || strcmp(getenv("RX_LIVE_MODE"), "plain") == 0 || strcmp(getenv("RX_LIVE_MODE"), "journal") == 0)
		start_stage();
	return rootside_main(&o);
}
