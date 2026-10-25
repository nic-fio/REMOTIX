/*
 * 02-rediscover-test.c — ⭐ 1.6 (R8): the search for live REMOTIX desktops, with a FAKE /proc and a FAKE /run/systemd/sessions,
 *                        `src/rediscover.c` INCLUDED (its statics reachable).
 *
 * The root side asks logind's own files (not its bus) and walks /proc itself: `rediscover_search_files_at()` takes the two roots,
 * so this test builds both in a temporary folder and checks the criterion of `rediscover.h` — a process that is leader of its
 * own process session (pid = sid), of the session's user, in the scope of one of that user's `remotix` sessions, whose PARENT is
 * outside that scope — plus the start time (field 22) that the root side later watches the stage with.
 *
 * As an ordinary user the fake processes are owned by the user running it; as root (a privileged container) by `nobody`.
 *
 *   cd src && make test-rediscover
 *
 * Exit 0 all passed · 1 a check failed.  The last line is «N passed, M failed».
 */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "rediscover.c"

#include <ftw.h>
#include <stdarg.h>

static int passed, failed;

#define CHECK(cond, ...)                                                   \
	do {                                                               \
		if (cond) {                                                \
			passed++;                                          \
			printf("  ok   ");                                 \
		} else {                                                   \
			failed++;                                          \
			printf("  FAIL ");                                 \
		}                                                          \
		printf(__VA_ARGS__);                                       \
		printf("\n");                                              \
	} while (0)

static uid_t who;            /* the owner of the fake processes: never 0 */
static char who_name[64];
static char root[PATH_MAX];  /* the world's folder */
static char procd[PATH_MAX + 8], sess[PATH_MAX + 16];

static int rm_cb(const char *p, const struct stat *st, int flag, struct FTW *f)
{
	(void)st; (void)flag; (void)f;
	return remove(p);
}

static void world_new(void)
{
	snprintf(root, sizeof root, "%s/remotix-rediscover-test.XXXXXX", getenv("TMPDIR") ? getenv("TMPDIR") : "/tmp");
	if (!mkdtemp(root)) {
		perror("mkdtemp");
		exit(3);
	}
	snprintf(procd, sizeof procd, "%s/proc", root);
	snprintf(sess, sizeof sess, "%s/sessions", root);
	if (mkdir(procd, 0755) || mkdir(sess, 0755)) {
		perror("mkdir");
		exit(3);
	}
}

static void world_gone(void)
{
	(void)nftw(root, rm_cb, 16, FTW_DEPTH | FTW_PHYS);
}

static void put(const char *path, const char *fmt, ...)
{
	FILE *f = fopen(path, "w");
	va_list ap;

	if (!f) {
		perror(path);
		exit(3);
	}
	va_start(ap, fmt);
	vfprintf(f, fmt, ap);
	va_end(ap);
	fclose(f);
}

/* a logind session file */
static void add_session(const char *id, const char *body_fmt, ...)
{
	char path[PATH_MAX + 64], body[512];
	va_list ap;

	snprintf(path, sizeof path, "%s/%s", sess, id);
	va_start(ap, body_fmt);
	vsnprintf(body, sizeof body, body_fmt, ap);
	va_end(ap);
	put(path, "%s", body);
}

static void add_session_std(const char *id, uid_t uid, const char *service, const char *state, const char *scope)
{
	add_session(id, "UID=%u\nUSER=x\nSERVICE=%s\nSTATE=%s\nSCOPE=%s\n", (unsigned)uid, service, state, scope);
}

/* a fake process: its stat and its cgroup */
static void add_proc(long pid, const char *comm, char state, long ppid, long sid, unsigned long long start, const char *scope)
{
	char d[PATH_MAX + 64], f[PATH_MAX + 96];

	snprintf(d, sizeof d, "%s/%ld", procd, pid);
	if (mkdir(d, 0755)) {
		perror(d);
		exit(3);
	}
	if (geteuid() == 0 && chown(d, who, (gid_t)-1) != 0)
		perror("chown");
	snprintf(f, sizeof f, "%s/stat", d);
	put(f, "%ld (%s) %c %ld %ld %ld 0 0 0 0 0 0 0 0 0 0 0 20 0 1 0 %llu 0 0\n", pid, comm, state, ppid, sid, sid, start);
	snprintf(f, sizeof f, "%s/cgroup", d);
	put(f, "0::/user.slice/user-%u.slice/%s\n", (unsigned)who, scope);
}

static int find_all(RediscoveredDesktop *v, int cap, char *why, size_t n)
{
	return rediscover_search_files_at(sess, procd, v, cap, why, n);
}

static void case_basic(void)
{
	RediscoveredDesktop v[8];
	char why[256] = "";
	int n;

	world_new();
	add_session_std("c1", who, "remotix", "closing", "session-c1.scope");
	add_proc(100, "gnome-session-b", 'S', 1, 100, 4242, "session-c1.scope");
	memset(v, 0, sizeof v);
	n = find_all(v, 8, why, sizeof why);
	CHECK(n == 1, "a stage (pid = sid, parent outside the scope) in a CLOSING remotix session is found (n=%d, «%s»)", n, why);
	if (n == 1) {
		CHECK(strcmp(v[0].user, who_name) == 0 && v[0].uid == who, "its user and uid are the owner's (%s/%u)", v[0].user, (unsigned)v[0].uid);
		CHECK(v[0].stage == 100 && strcmp(v[0].comm, "gnome-session-b") == 0, "stage pid %ld, name «%s»", (long)v[0].stage, v[0].comm);
		CHECK(strcmp(v[0].session, "c1") == 0 && v[0].sessions == 1, "session «%s», %u in all", v[0].session, v[0].sessions);
		CHECK(v[0].starttime == 4242, "start time %llu (field 22 of the stat)", v[0].starttime);
	}
	world_gone();
}

static void case_exclusions(void)
{
	RediscoveredDesktop v[8];
	char why[256] = "";

	/* the terminal's shell: a session leader, but its parent is in the scope */
	world_new();
	add_session_std("c1", who, "remotix", "active", "session-c1.scope");
	add_proc(200, "foot", 'S', 1, 5, 10, "session-c1.scope");
	add_proc(201, "bash", 'S', 200, 201, 11, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "the shell of a terminal opened in the desktop is NOT a stage (parent in the scope)");
	world_gone();

	/* the parent is outside, in another cgroup: that is the setsid --fork signature */
	world_new();
	add_session_std("c1", who, "remotix", "active", "session-c1.scope");
	add_proc(300, "init-ish", 'S', 1, 1, 1, "init.scope");
	add_proc(301, "labwc", 'S', 300, 301, 12, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 1, "a parent in ANOTHER cgroup: the stage is found");
	world_gone();

	world_new();
	add_session_std("c1", who, "remotix", "active", "session-c1.scope");
	add_proc(400, "x", 'S', 1, 7, 1, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "pid != sid: not a leader of its own session");
	world_gone();

	world_new();
	add_session_std("c1", who, "remotix", "active", "session-c1.scope");
	add_proc(500, "defunct", 'Z', 1, 500, 1, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "a zombie is not a stage");
	world_gone();

	world_new();
	add_session_std("c1", who, "remotix", "active", "session-c1.scope");
	add_proc(600, "elsewhere", 'S', 1, 600, 1, "session-c9.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "a leader in the scope of ANOTHER session is not this session's stage");
	world_gone();

	world_new();
	add_session_std("c1", who, "gdm-password", "active", "session-c1.scope");
	add_proc(700, "gnome-shell", 'S', 1, 700, 1, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "a session of another PAM service (not «remotix») does not count");
	world_gone();

	/* the FIRST key wins: a later SERVICE=remotix cannot turn another service into ours */
	world_new();
	add_session("c1", "UID=%u\nSERVICE=sshd\nSERVICE=remotix\nSCOPE=session-c1.scope\n", (unsigned)who);
	add_proc(800, "x", 'S', 1, 800, 1, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "the first SERVICE= counts: a second one does not override it");
	world_gone();

	world_new();
	add_session("c1", "UID=%ux\nSERVICE=remotix\nSCOPE=session-c1.scope\n", (unsigned)who);
	add_session("c2", "UID=%u\nSERVICE=remotix\n", (unsigned)who);
	add_proc(900, "x", 'S', 1, 900, 1, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "a UID that is not all digits, and a session with no scope, give nothing");
	world_gone();

	/* `.ref` pipes and temporary files are not sessions */
	world_new();
	add_session("c1.ref", "UID=%u\nSERVICE=remotix\nSCOPE=session-c1.scope\n", (unsigned)who);
	add_proc(950, "x", 'S', 1, 950, 1, "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "a file with a dot in its name is not a session");
	world_gone();
}

static void case_shape(void)
{
	RediscoveredDesktop v[8];
	char why[256] = "";
	int n;

	/* a name with parentheses and spaces: the LAST «)» ends it, and field 22 is still the start time */
	world_new();
	add_session_std("c1", who, "remotix", "active", "session-c1.scope");
	add_proc(1000, "a b) (c", 'S', 1, 1000, 987654321ULL, "session-c1.scope");
	memset(v, 0, sizeof v);
	n = find_all(v, 8, why, sizeof why);
	CHECK(n == 1 && v[0].starttime == 987654321ULL && strcmp(v[0].comm, "a b) (c") == 0,
	      "a name with «)» and spaces: name «%s», start time %llu", n == 1 ? v[0].comm : "?", n == 1 ? v[0].starttime : 0);
	world_gone();

	/* two stages of the same user in two sessions: ONE result, two sessions counted */
	world_new();
	add_session_std("c1", who, "remotix", "closing", "session-c1.scope");
	add_session_std("c2", who, "remotix", "active", "session-c2.scope");
	add_proc(1100, "s1", 'S', 1, 1100, 1, "session-c1.scope");
	add_proc(1101, "s2", 'S', 1, 1101, 2, "session-c2.scope");
	n = find_all(v, 8, why, sizeof why);
	CHECK(n == 1 && v[0].sessions == 2, "one per user, and both sessions counted (n=%d, sessions=%u)", n, n == 1 ? v[0].sessions : 0);
	world_gone();

	/* nothing running: 0, not an error */
	world_new();
	add_session_std("c1", who, "remotix", "closing", "session-c1.scope");
	CHECK(find_all(v, 8, why, sizeof why) == 0, "a session with no live process: 0");
	world_gone();

	/* the roots that are not there: -1 with the reason */
	world_new();
	rmdir(sess);
	n = find_all(v, 8, why, sizeof why);
	CHECK(n == -1 && strstr(why, "sessions"), "no sessions folder: -1 (%s)", why);
	world_gone();

	world_new();
	add_session_std("c1", who, "remotix", "closing", "session-c1.scope");
	rmdir(procd);
	n = find_all(v, 8, why, sizeof why);
	CHECK(n == -1 && strstr(why, "proc"), "no /proc: -1 (%s)", why);
	world_gone();
}

static void case_starttime(void)
{
	unsigned long long a = 0, b = 0;

	CHECK(rediscover_starttime("/proc", getpid(), &a) && a > 0, "the real /proc/self/stat has a start time (%llu)", a);
	CHECK(rediscover_starttime("/proc", getpid(), &b) && b == a, "and it does not change between two readings");
	CHECK(!rediscover_starttime("/proc", 0x7ffffff0, &a), "a pid that is not there: false");
	world_new();
	{
		char d[PATH_MAX + 32], f[PATH_MAX + 64];

		snprintf(d, sizeof d, "%s/5", procd);
		mkdir(d, 0755);
		snprintf(f, sizeof f, "%s/stat", d);
		put(f, "5 (short) S 1 5 5 0 0\n");
		CHECK(!rediscover_starttime(procd, 5, &a), "a stat with fewer than 22 fields: false");
		put(f, "5 (bad) S 1 5 5 0 0 0 0 0 0 0 0 0 0 0 20 0 1 0 12x 0 0\n");
		CHECK(!rediscover_starttime(procd, 5, &a), "a start time that is not all digits: false");
		put(f, "garbage with no parenthesis\n");
		CHECK(!rediscover_starttime(procd, 5, &a), "no «)» at all: false");
	}
	world_gone();
}

int main(void)
{
	struct passwd *pw;

	setvbuf(stdout, NULL, _IOLBF, 0);
	if (geteuid() == 0) {
		pw = getpwnam("nobody");
		if (!pw) {
			printf("  BLIND: no user nobody\n");
			return 3;
		}
	} else {
		pw = getpwuid(geteuid());
	}
	who = pw->pw_uid;
	snprintf(who_name, sizeof who_name, "%s", pw->pw_name);
	printf("02-rediscover-test (uid %ld, fake owner %s)\n", (long)geteuid(), who_name);
	case_basic();
	case_exclusions();
	case_shape();
	case_starttime();
	printf("%d passed, %d failed\n", passed, failed);
	return failed ? 1 : 0;
}
