/* 02-logind-async-test.c — the loop's questions to logind no longer wait
 * (15 Oct 2026): the check of the local sessions (`sentinel_locals()`, every
 * 2 s from `wt_watch_locals()`) and the check of the desktops found again
 * (`rediscover_search()`, every 10 s from `found_again_sweep()`) send their
 * question and read the answer at the next check; the ATTACH question
 * (`sentinel_local()`) still waits, 100 ms at most, and not at all for 30 s
 * after logind has been silent.
 *
 * In the build container, from src/:
 *
 *   gcc -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -I. \
 *       $(pkg-config --cflags gio-2.0) -o /tmp/lat \
 *       ../benches/02-logind-async-test.c sentinel.c log.c \
 *       $(pkg-config --libs gio-2.0) && /tmp/lat
 *
 * ⚠ `rediscover.c` is INCLUDED (the seam): the test compares the candidates
 *   the answer of the check that does not wait leaves in `later` with those of
 *   the waiting road (`candidate()`), field by field.
 * ⚠ There is no dbus-daemon in the container: a FAKE logind is a GDBusServer
 *   in a child process, at DBUS_SYSTEM_BUS_ADDRESS.  A filter answers Hello at
 *   once and ListSessions / GetAll after the delays written in a control file
 *   (re-read at every question): «DL ms», «DG ms», and one line per session
 *   «S id uid name seat path type class remote state service scope».
 *
 *   S1  the first check sends the question and answers nothing, < 10 ms;
 *   S2  with checks only (main.c as it is) the answer comes at the third
 *       check (the list, then the GetAll round): the first seated graphical
 *       session in the list, for every position asking that name; with
 *       sentinel_collect() at every loop pass, at the next check;
 *   S3  sentinel_counts(): the cost measured at the bus, round by round
 *       (< 50 ms), not at the next turn of the context (~100 ms later);
 *   S4  logind 2 s slow: every check < 10 ms, all answer false, the silent
 *       line once;
 *   S5  ATTACH while logind is silent: false at once (< 5 ms);
 *   S6  logind fast again: the next check answers, «answering again»;
 *   S7  ATTACH, fast logind: anna local with the description, bob not;
 *   S8  ATTACH, logind 2 s slow: false within ~100 ms, the next one < 5 ms;
 *   S9  an answer older than 7 s is not used;
 *   S10 a name not asked in the question answered reads false;
 *   S11 sentinel_close() with a question in flight returns at once;
 *   R1  the first rediscover_search() waits and keeps its candidates;
 *   R2  the later ones answer < 10 ms; the async candidates equal the
 *       waiting road's, in the same order;
 *       (⚠ the /proc half is still read in the call: its cost is the host's)
 *   R3  logind 2 s slow: every search < 10 ms, the previous answer is used;
 *   R4  a GetAll past the 5 s ceiling: -1 («I don't know»), then 0 again.
 *
 * Exit status: 0 green, 1 red, 3 not all checks ran. */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "rediscover.c"
#include "sentinel.h"

#include <signal.h>
#include <sys/wait.h>
#include <time.h>

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 32

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	fflush(stdout);
	if (cond)
		passed++;
	else
		failures++;
}

static double now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

static char ctl_path[256];

static void sleep_ms(int ms)
{
	struct timespec ts = { ms / 1000, (long)(ms % 1000) * 1000000L };
	nanosleep(&ts, NULL);
}

/* ------------------------------------------------------------- the fake */

struct fake_session {
	char id[32], name[64], seat[32], path[128], type[16], klass[16], state[16],
	     service[32], scope[128];
	unsigned uid;
	int remote;
};

static int fake_read(int *dl, int *dg, struct fake_session *v, int cap)
{
	FILE *f = fopen(ctl_path, "r");
	char line[1024];
	int n = 0;

	*dl = *dg = 0;
	if (!f)
		return 0;
	while (fgets(line, sizeof line, f)) {
		if (sscanf(line, "DL %d", dl) == 1 || sscanf(line, "DG %d", dg) == 1)
			continue;
		if (n < cap && sscanf(line, "S %31s %u %63s %31s %127s %15s %15s %d %15s %31s %127s",
		                      v[n].id, &v[n].uid, v[n].name, v[n].seat, v[n].path,
		                      v[n].type, v[n].klass, &v[n].remote, v[n].state,
		                      v[n].service, v[n].scope) == 11) {
			if (strcmp(v[n].seat, "-") == 0)
				v[n].seat[0] = '\0';
			n++;
		}
	}
	fclose(f);
	return n;
}

struct pending_reply {
	GDBusConnection *c;
	GDBusMessage *m;
};

static gboolean fake_send_later(gpointer data)
{
	struct pending_reply *p = data;

	g_dbus_connection_send_message(p->c, p->m, G_DBUS_SEND_MESSAGE_FLAGS_NONE, NULL, NULL);
	g_object_unref(p->m);
	g_object_unref(p->c);
	g_free(p);
	return G_SOURCE_REMOVE;
}

static GDBusMessage *fake_filter(GDBusConnection *c, GDBusMessage *m, gboolean incoming,
                                 gpointer data)
{
	struct fake_session v[16];
	const char *member, *path;
	GDBusMessage *reply;
	int dl, dg, n, delay = 0;

	(void)data;
	if (!incoming || g_dbus_message_get_message_type(m) != G_DBUS_MESSAGE_TYPE_METHOD_CALL)
		return m;
	member = g_dbus_message_get_member(m);
	path = g_dbus_message_get_path(m);
	n = fake_read(&dl, &dg, v, 16);
	reply = g_dbus_message_new_method_reply(m);
	if (g_strcmp0(member, "Hello") == 0) {
		g_dbus_message_set_body(reply, g_variant_new("(s)", ":1.42"));
	} else if (g_strcmp0(member, "ListSessions") == 0) {
		GVariantBuilder b;

		g_variant_builder_init(&b, G_VARIANT_TYPE("a(susso)"));
		for (int i = 0; i < n; i++)
			g_variant_builder_add(&b, "(susso)", v[i].id, v[i].uid, v[i].name,
			                      v[i].seat, v[i].path);
		g_dbus_message_set_body(reply, g_variant_new("(a(susso))", &b));
		delay = dl;
	} else if (g_strcmp0(member, "GetAll") == 0) {
		GVariantBuilder b;
		int i;

		for (i = 0; i < n; i++)
			if (g_strcmp0(path, v[i].path) == 0)
				break;
		if (i == n) {
			g_object_unref(reply);
			reply = g_dbus_message_new_method_error(m, "org.freedesktop.DBus.Error.UnknownObject",
			                                        "no such session");
		} else {
			g_variant_builder_init(&b, G_VARIANT_TYPE("a{sv}"));
			g_variant_builder_add(&b, "{sv}", "Type", g_variant_new_string(v[i].type));
			g_variant_builder_add(&b, "{sv}", "Class", g_variant_new_string(v[i].klass));
			g_variant_builder_add(&b, "{sv}", "Remote", g_variant_new_boolean(v[i].remote));
			g_variant_builder_add(&b, "{sv}", "State", g_variant_new_string(v[i].state));
			g_variant_builder_add(&b, "{sv}", "Service", g_variant_new_string(v[i].service));
			g_variant_builder_add(&b, "{sv}", "Scope", g_variant_new_string(v[i].scope));
			g_dbus_message_set_body(reply, g_variant_new("(a{sv})", &b));
		}
		delay = dg;
	} else {
		g_object_unref(reply);
		reply = g_dbus_message_new_method_error(m, "org.freedesktop.DBus.Error.UnknownMethod",
		                                        "fake logind");
	}
	if (delay <= 0) {
		g_dbus_connection_send_message(c, reply, G_DBUS_SEND_MESSAGE_FLAGS_NONE, NULL, NULL);
		g_object_unref(reply);
	} else {
		struct pending_reply *p = g_new0(struct pending_reply, 1);

		p->c = g_object_ref(c);
		p->m = reply;
		g_timeout_add(delay, fake_send_later, p);
	}
	g_object_unref(m);
	return NULL;
}

static gboolean fake_new_connection(GDBusServer *srv, GDBusConnection *c, gpointer data)
{
	(void)srv;
	(void)data;
	g_object_ref(c);
	g_dbus_connection_add_filter(c, fake_filter, NULL, NULL);
	return TRUE;
}

static void fake_run(const char *address)
{
	g_autofree char *guid = g_dbus_generate_guid();
	GError *e = NULL;
	GDBusServer *srv = g_dbus_server_new_sync(address, G_DBUS_SERVER_FLAGS_NONE, guid,
	                                          NULL, NULL, &e);
	GMainLoop *loop;

	if (!srv) {
		fprintf(stderr, "fake logind: %s\n", e->message);
		_exit(2);
	}
	g_signal_connect(srv, "new-connection", G_CALLBACK(fake_new_connection), NULL);
	g_dbus_server_start(srv);
	loop = g_main_loop_new(NULL, FALSE);
	g_main_loop_run(loop);
	_exit(0);
}

static void fake_set(int dl, int dg)
{
	char tmp[300];
	FILE *f;

	/* ⚠ Written aside and renamed: the fake re-reads it at every question,
	 *   and must never see it half written. */
	snprintf(tmp, sizeof tmp, "%s.new", ctl_path);
	f = fopen(tmp, "w");

	fprintf(f, "DL %d\nDG %d\n", dl, dg);
	/* seated sessions: a greeter (not the user at work), anna twice
	 * (graphical, the first one wins), bob on a tty, carol remote-on-seat;
	 * ours: no seat, PAM service remotix */
	fprintf(f, "S c1 120 gdm seat0 /s/c1 wayland greeter 0 active gdm-launch -\n");
	fprintf(f, "S c2 1001 anna seat0 /s/c2 wayland user 0 active gdm x\n");
	fprintf(f, "S c3 1001 anna seat0 /s/c3 x11 user 0 active gdm y\n");
	fprintf(f, "S c4 1002 bob seat0 /s/c4 tty user 0 active login z\n");
	fprintf(f, "S c5 1003 carol seat0 /s/c5 wayland user 1 active gdm w\n");
	fprintf(f, "S 7 1004 dave - /s/7 wayland user 1 closing remotix session-7.scope\n");
	fprintf(f, "S 9 1005 erin - /s/9 wayland user 1 active remotix session-9.scope\n");
	fprintf(f, "S 8 1004 dave - /s/8 wayland user 1 active remotix session-8.scope\n");
	fprintf(f, "S 10 1006 fred - /s/10 wayland user 1 active sshd session-10.scope\n");
	fclose(f);
	rename(tmp, ctl_path);
}

/* ------------------------------------------------------------- the test */

static int count_in_log(const char *log, const char *needle)
{
	FILE *f = fopen(log, "r");
	char line[4096];
	int n = 0;

	if (!f)
		return -1;
	while (fgets(line, sizeof line, f))
		if (strstr(line, needle))
			n++;
	fclose(f);
	return n;
}

/* Checks 100 ms apart until one answers; how many it took (99: never). */
static int checks_until(sentinel *s, const char *const *users, size_t amount, bool *local,
                        char *which)
{
	for (int k = 1; k <= 6; k++) {
		sleep_ms(100);
		if (sentinel_locals(s, users, amount, local, which, which ? 160 : 0) > 0)
			return k;
	}
	return 99;
}

int main(void)
{
	char dir[] = "/tmp/lat-XXXXXX";
	char sock[300], address[320], log[300];
	pid_t fake;
	sentinel *s;
	const char *u_ab[3] = { "anna", "bob", "anna" };
	const char *u_a[1] = { "anna" };
	const char *u_b[1] = { "bob" };
	bool local[3];
	char which[3][160];
	double t0, worst;
	size_t n;
	int logfd;

	if (!mkdtemp(dir))
		return 2;
	snprintf(ctl_path, sizeof ctl_path, "%s/ctl", dir);
	snprintf(sock, sizeof sock, "%s/bus", dir);
	snprintf(address, sizeof address, "unix:path=%s", sock);
	snprintf(log, sizeof log, "%s/log", dir);
	fake_set(0, 0);

	fake = fork();
	if (fake == 0)
		fake_run(address);
	for (int i = 0; i < 100 && access(sock, F_OK) != 0; i++)
		sleep_ms(20);
	setenv("DBUS_SYSTEM_BUS_ADDRESS", address, 1);
	/* the product's log goes to a file the test reads */
	logfd = open(log, O_WRONLY | O_CREAT | O_TRUNC | O_APPEND, 0600);
	dup2(logfd, 2);

	printf("sentinel — the check of the local sessions\n");
	s = sentinel_open();
	require(s != NULL, "S0 sentinel_open() on the fake logind");
	if (!s)
		goto end;

	t0 = now_ms();
	n = sentinel_locals(s, u_ab, 3, local, &which[0][0], 160);
	require(n == 0 && !local[0] && !local[1] && !local[2] && now_ms() - t0 < 10,
	        "S1 the first check sends the question, answers nothing, < 10 ms");
	/* S2a: checks only (main.c as it is): list, then GetAll, then the answer */
	worst = 0;
	{
		int k = 0;

		do {
			sleep_ms(100);
			t0 = now_ms();
			n = sentinel_locals(s, u_ab, 3, local, &which[0][0], 160);
			if (now_ms() - t0 > worst)
				worst = now_ms() - t0;
			k++;
		} while (n == 0 && k < 5);
		require(n == 2 && local[0] && !local[1] && local[2] && worst < 10 && k == 2,
		        "S2 checks only: the answer at the third check (list, GetAll round): "
		        "anna local at both positions, bob not (tty); every check < 10 ms");
	}
	require(strcmp(which[0], "session c2, wayland on seat0") == 0 &&
	        strcmp(which[2], which[0]) == 0 && which[1][0] == '\0',
	        "S2 the first graphical session in the list wins: «session c2, wayland on seat0»");
	/* S2b: with sentinel_collect() at every loop pass (the optional main.c line) */
	sentinel_locals(s, u_ab, 3, local, &which[0][0], 160); /* asks */
	for (int i = 0; i < 5; i++) {
		sleep_ms(20);
		sentinel_collect(s);
	}
	n = sentinel_locals(s, u_ab, 3, local, &which[0][0], 160);
	require(n == 2 && local[0] && local[2],
	        "S2 with sentinel_collect() at every pass: the answer at the NEXT check");
	{
		uint64_t calls = 0, worst_ms = 0;

		sentinel_counts(s, &calls, &worst_ms);
		require(calls == 2 && worst_ms < 50,
		        "S3 sentinel_counts(): 2 calls, cost measured at the bus (< 50 ms, not ~100)");
		printf("        (calls=%llu worst=%llu ms)\n", (unsigned long long)calls,
		       (unsigned long long)worst_ms);
	}

	/* S4: logind 2 s slow — the loop never waits */
	fake_set(2000, 2000);
	worst = 0;
	for (int i = 0; i < 5; i++) {
		t0 = now_ms();
		n = sentinel_locals(s, u_ab, 3, local, &which[0][0], 160);
		if (now_ms() - t0 > worst)
			worst = now_ms() - t0;
		sleep_ms(400);
	}
	require(n == 0 && !local[0] && !local[2],
	        "S4 logind silent: anna reads false (I1: «I don't know» = no)");
	require(worst < 10, "S4 logind 2 s slow: every check < 10 ms");
	printf("        (slowest check: %.2f ms)\n", worst);
	require(count_in_log(log, "logind did not answer within 300 ms") == 1,
	        "S4 the silent line written once");

	t0 = now_ms();
	require(!sentinel_local(s, "anna", NULL, 0) && now_ms() - t0 < 5,
	        "S5 ATTACH while logind is silent: false at once (< 5 ms)");

	/* S6: fast again */
	fake_set(0, 0);
	sleep_ms(2100); /* the slow answers come back (late) */
	require(checks_until(s, u_ab, 3, local, &which[0][0]) <= 4 && local[0] && local[2],
	        "S6 logind fast again: anna local again");
	require(count_in_log(log, "logind is answering again") == 1,
	        "S6 «logind is answering again» written");

	/* S7: ATTACH, fast logind (the pause ends at the first answer of the check) */
	{
		char d[160];

		t0 = now_ms();
		require(sentinel_local(s, "anna", d, sizeof d) &&
		        strcmp(d, "session c2, wayland on seat0") == 0,
		        "S7 ATTACH, fast logind: anna has a local session (c2)");
		require(!sentinel_local(s, "bob", d, sizeof d) && d[0] == '\0',
		        "S7 ATTACH, fast logind: bob has none (tty)");
		require(!sentinel_local(s, "carol", d, sizeof d),
		        "S7 ATTACH: carol's seated session is Remote=yes, not local");
		require(now_ms() - t0 < 50, "S7 the three ATTACH questions < 50 ms");
	}

	/* S8: ATTACH with logind 2 s slow — waits ≤ ~100 ms, then not at all */
	fake_set(2000, 2000);
	t0 = now_ms();
	require(!sentinel_local(s, "anna", NULL, 0), "S8 ATTACH, logind slow: false");
	worst = now_ms() - t0;
	require(worst >= 90 && worst < 150, "S8 … after the 100 ms ceiling, not 300");
	printf("        (that ATTACH: %.1f ms)\n", worst);
	t0 = now_ms();
	require(!sentinel_local(s, "anna", NULL, 0) && now_ms() - t0 < 5,
	        "S8 the next ATTACH within 30 s: false at once (< 5 ms)");

	/* S9: an answer older than 7 s is not used */
	fake_set(0, 0);
	sleep_ms(2100);
	sentinel_locals(s, u_a, 1, local, NULL, 0);   /* collects what is left, asks */
	for (int i = 0; i < 5; i++) {
		sleep_ms(20);
		sentinel_collect(s);                  /* the answer is complete */
	}
	sleep_ms(7200);
	n = sentinel_locals(s, u_a, 1, local, NULL, 0);
	require(n == 0 && !local[0], "S9 an answer 7.3 s old is not used");
	require(checks_until(s, u_a, 1, local, NULL) <= 3 && local[0], "S9 … a fresh one is");

	/* S10: a name the question did not ask reads false */
	for (int i = 0; i < 5; i++) {
		sleep_ms(20);
		sentinel_collect(s);                  /* the question in flight ends */
	}
	sentinel_locals(s, u_b, 1, local, NULL, 0);   /* uses it; asks for bob only */
	for (int i = 0; i < 5; i++) {
		sleep_ms(20);
		sentinel_collect(s);
	}
	n = sentinel_locals(s, u_a, 1, local, NULL, 0);
	require(n == 0 && !local[0], "S10 anna was not in the question answered: false");
	require(checks_until(s, u_a, 1, local, NULL) <= 3 && local[0],
	        "S10 … and true at a later check");

	/* S11: close with a question in flight */
	fake_set(2000, 2000);
	sentinel_locals(s, u_a, 1, local, NULL, 0);
	t0 = now_ms();
	sentinel_close(s);
	require(now_ms() - t0 < 50, "S11 sentinel_close() with a question in flight < 50 ms");

	printf("rediscover — the check of the desktops found again\n");
	{
		RediscoveredDesktop v[8];
		struct candidate_entry sync_c[MAX_CANDIDATES];
		char why[256];
		int nc, r;
		bool same;

		fake_set(0, 0);
		r = rediscover_search(v, 8, why, sizeof why);
		require(r == 0 && later.ever && !later.failed && later.nc == 3,
		        "R1 the first search waits: 3 remotix sessions (no live stage here: 0)");
		nc = candidate(sync_c, MAX_CANDIDATES, why, sizeof why);
		require(nc == 3 && strcmp(sync_c[0].scope, "session-7.scope") == 0 &&
		        strcmp(sync_c[1].scope, "session-9.scope") == 0 &&
		        strcmp(sync_c[2].scope, "session-8.scope") == 0,
		        "R1 the waiting road: 7, 9, 8 in list order (sshd and seated left out)");

		t0 = now_ms();
		r = rediscover_search(v, 8, why, sizeof why);
		require(r == 0 && now_ms() - t0 < 10, "R2 a later search: answered < 10 ms");
		later.nc = 0; /* forget it: the next answer must come from the async road */
		for (int i = 0; i < 5; i++) {
			sleep_ms(20);
			rediscover_collect();
		}
		r = rediscover_search(v, 8, why, sizeof why);
		same = later.nc == nc;
		for (int i = 0; same && i < nc; i++)
			same = later.c[i].uid == sync_c[i].uid &&
			       strcmp(later.c[i].id, sync_c[i].id) == 0 &&
			       strcmp(later.c[i].scope, sync_c[i].scope) == 0 &&
			       strcmp(later.c[i].user, sync_c[i].user) == 0;
		require(r == 0 && same, "R2 the async candidates equal the waiting road's, same order");

		fake_set(2000, 2000);
		worst = 0;
		for (int i = 0; i < 4; i++) {
			t0 = now_ms();
			r = rediscover_search(v, 8, why, sizeof why);
			if (now_ms() - t0 > worst)
				worst = now_ms() - t0;
			if (r != 0)
				break;
			sleep_ms(300);
		}
		require(r == 0 && worst < 10, "R3 logind 2 s slow: every search < 10 ms, previous answer used");
		printf("        (slowest search: %.2f ms)\n", worst);

		fake_set(0, 6000);
		worst = 0;
		for (int i = 0; i < 60; i++) {
			t0 = now_ms();
			r = rediscover_search(v, 8, why, sizeof why);
			if (now_ms() - t0 > worst)
				worst = now_ms() - t0;
			if (r == -1)
				break;
			sleep_ms(300);
		}
		require(r == -1 && strstr(why, "GetAll") && worst < 10,
		        "R4 a GetAll past the 5 s ceiling: -1, «I don't know»; every search < 10 ms");
		printf("        (why: %s)\n", why);
		fake_set(0, 0);
		for (int i = 0; i < 60; i++) {
			r = rediscover_search(v, 8, why, sizeof why);
			if (r == 0 && later.nc == 3)
				break;
			sleep_ms(300);
		}
		if (r != 0 || later.nc != 3)
			printf("        (r=%d nc=%d why=%s)\n", r, later.nc, why);
		require(r == 0 && later.nc == 3, "R4 … and 0 with 3 candidates once logind answers");
		require(rediscover_alive(1004, NULL) == 0, "R5 rediscover_alive() (waiting road) still answers");
	}

end:
	kill(fake, SIGTERM);
	waitpid(fake, NULL, 0);
	printf("--- log of the product ---\n");
	fflush(stdout);
	{
		char cmd[400];
		snprintf(cmd, sizeof cmd, "cat %s", log);
		if (system(cmd) != 0)
			printf("(no log)\n");
	}
	printf("%d/%d passed, %d failed\n", passed, EXPECTED_CHECKS, failures);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
