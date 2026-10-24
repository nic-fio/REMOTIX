/*
 * 02-walls-test.c — ⭐ 1.5 (DECISIONS.md §11.50): the network side's walls,
 *                   `src/walls.c` INCLUDED (its statics reachable), on a desk.
 *
 * Two halves, and the half that runs depends on who runs it:
 *
 *   · as an ordinary user (rxtest build, uid 1000): the failure paths — no
 *     options, an unknown user, not root — each must refuse with its reason
 *     and leave the process as it was (same uid, same mount namespace); and
 *     the SELinux context rewrite;
 *   · as root in a container that may mount (`--privileged`, or
 *     `--cap-add SYS_ADMIN --security-opt seccomp=unconfined`): a missing and
 *     a foreign-owned directory refuse; then, in a fork, the walls for real
 *     with the user `nobody`: / read-only (EROFS even in a directory nobody
 *     owns), the two directories writable, /tmp private and empty, uid/gid
 *     nobody, no supplementary group, every capability set 0, NoNewPrivs 1 —
 *     and the parent's tree untouched afterwards.
 *
 *   cd src && make test-walls                     (either half, by uid)
 *   root: podman run --rm --network=none --privileged -v TREE:/albero \
 *           -w /albero/src localhost/remotix-costruzione make test-walls
 *
 * Exit 0 all passed · 1 a check failed · 3 could not look (root without the
 * power to mount, or no user `nobody`).  The last line is «N passed, M
 * failed, of K».
 */
#include "walls.c"

#include <pwd.h>

#include <sys/wait.h>

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

static ino_t mnt_ns(void)
{
	struct stat st;
	return stat("/proc/self/ns/mnt", &st) == 0 ? st.st_ino : 0;
}

static struct rootside_options opts(uid_t uid, gid_t gid, const char *state, const char *run)
{
	struct rootside_options o;
	memset(&o, 0, sizeof o);
	o.remotix_uid = uid;
	o.remotix_gid = gid;
	o.net_state_dir = state;
	o.net_run_dir = run;
	return o;
}

static void case_context(void)
{
	char out[128];
	CHECK(context_with_type("system_u:system_r:remotix_t:s0", "remotix_net_t", out,
	                        sizeof out) &&
	          strcmp(out, "system_u:system_r:remotix_net_t:s0") == 0,
	      "context: the type is replaced, the level kept («%s»)", out);
	CHECK(context_with_type("system_u:system_r:remotix_t:s0-s0:c0.c1023", "remotix_net_t",
	                        out, sizeof out) &&
	          strcmp(out, "system_u:system_r:remotix_net_t:s0-s0:c0.c1023") == 0,
	      "context: a level with «:» inside is kept whole («%s»)", out);
	CHECK(context_with_type("u:r:t", "x_t", out, sizeof out) && strcmp(out, "u:r:x_t") == 0,
	      "context: no level («%s»)", out);
	CHECK(!context_with_type("u:r", "x_t", out, sizeof out), "context: two fields refused");
	CHECK(!context_with_type("u:r::s0", "x_t", out, sizeof out), "context: empty type refused");
	CHECK(!context_with_type("system_u:system_r:remotix_t:s0", "remotix_net_t", out, 10),
	      "context: a buffer too small refused");
}

static void case_unprivileged(const struct passwd *nb)
{
	char why[512];
	uid_t u0 = getuid();
	ino_t ns0 = mnt_ns();
	struct rootside_options o;

	CHECK(walls_apply(NULL, why, sizeof why) == -1 && why[0], "no options: refused («%s»)",
	      why);
	o = opts(0, 0, "/nonexistent", "/nonexistent");
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "must not be root"),
	      "uid 0 as the network user: refused («%s»)", why);
	o = opts(1234, 0, "/nonexistent", "/nonexistent");
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "must not be root"),
	      "gid 0 as the network group: refused («%s»)", why);
	if (nb && geteuid() != 0) {
		o = opts(nb->pw_uid, nb->pw_gid, "/nonexistent", "/nonexistent");
		CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "must run as root"),
		      "not root: refused, said («%s»)", why);
	}
	CHECK(getuid() == u0 && mnt_ns() == ns0,
	      "after the refusals: same uid (%ld) and same mount namespace", (long)getuid());
}

static bool make_dir(const char *p, uid_t u, gid_t g, mode_t m)
{
	return mkdir(p, m) == 0 && chown(p, u, g) == 0 && chmod(p, m) == 0;
}

static bool write_in(const char *dir, int *err)
{
	char p[600];
	snprintf(p, sizeof p, "%s/w", dir);
	int fd = open(p, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC, 0600);
	*err = fd < 0 ? errno : 0;
	if (fd < 0)
		return false;
	close(fd);
	unlink(p);
	return true;
}

static uint64_t status_value(const char *key)
{
	FILE *f = fopen("/proc/self/status", "re");
	char line[256];
	uint64_t v = UINT64_MAX;
	size_t k = strlen(key);
	while (f && fgets(line, sizeof line, f))
		if (strncmp(line, key, k) == 0)
			v = strtoull(line + k, NULL, strcmp(key, "NoNewPrivs:") == 0 ? 10 : 16);
	if (f)
		fclose(f);
	return v;
}

/* 0 = blind, else the walls were applied and checked */
static int case_root(const struct passwd *nb)
{
	char base[] = "/var/tmp/remotix-walls-test.XXXXXX";
	char state[600], run[600], outside[600], marker[600], why[512];
	struct rootside_options o;
	int err, rc = 1;

	if (!mkdtemp(base)) {
		printf("  BLIND: mkdtemp (%s)\n", strerror(errno));
		return 0;
	}
	(void)chmod(base, 0755); /* ⚠ mkdtemp makes it 0700: nobody could not even walk in */
	snprintf(state, sizeof state, "%s/state", base);
	snprintf(run, sizeof run, "%s/run", base);
	snprintf(outside, sizeof outside, "%s/outside", base);
	snprintf(marker, sizeof marker, "/tmp/remotix-walls-test-marker.%ld", (long)getpid());

	o = opts(nb->pw_uid, nb->pw_gid, "/tmp/remotix-walls-test-state", run);
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "under /tmp"),
	      "root, state dir under /tmp: refused, named («%s»)", why);
	o = opts(nb->pw_uid, nb->pw_gid, state, run);
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "does not exist") &&
	          strstr(why, state),
	      "root, missing state dir: refused, named («%s»)", why);
	CHECK(mkdir(state, 0700) == 0, "mkdir %s (root-owned)", state);
	CHECK(make_dir(run, nb->pw_uid, nb->pw_gid, 0700), "mkdir %s (nobody)", run);
	CHECK(walls_apply(&o, why, sizeof why) == -1 && strstr(why, "belongs to uid 0") &&
	          strstr(why, "chown"),
	      "root, state dir owned by root: refused with the fix («%s»)", why);
	CHECK(chown(state, nb->pw_uid, nb->pw_gid) == 0, "chown %s to nobody", state);
	CHECK(make_dir(outside, nb->pw_uid, nb->pw_gid, 0700),
	      "mkdir %s (nobody's, but outside the walls)", outside);
	int mfd = open(marker, O_WRONLY | O_CREAT | O_TRUNC, 0644);
	CHECK(mfd >= 0, "a marker in the host's /tmp (%s)", marker);
	if (mfd >= 0)
		close(mfd);

	fflush(stdout);
	pid_t pid = fork();
	if (pid == 0) {
		int bad = 0;
		ino_t ns0 = mnt_ns();
		if (walls_apply(&o, why, sizeof why) != 0) {
			printf("  walls_apply: %s\n", why);
			fflush(stdout);
			_exit(strstr(why, "unshare") || strstr(why, "private") ||
			              strstr(why, "mount_setattr") ? 200 : 1);
		}
#define CC(cond, ...) do { if (!(cond)) bad++; printf((cond) ? "  ok   " : "  FAIL "); \
	printf(__VA_ARGS__); printf("\n"); } while (0)
		CC(mnt_ns() != ns0, "child: a mount namespace of its own");
		CC(getuid() == nb->pw_uid && geteuid() == nb->pw_uid && getgid() == nb->pw_gid &&
		       getegid() == nb->pw_gid,
		   "child: uid/gid %ld/%ld (nobody)", (long)getuid(), (long)getgid());
		CC(getgroups(0, NULL) == 0, "child: no supplementary group");
		CC(!write_in(outside, &err) && err == EROFS,
		   "child: a directory nobody owns but outside the walls is read-only (%s)",
		   strerror(err));
		CC(!write_in("/var/tmp", &err) && err == EROFS, "child: /var/tmp is read-only (%s)",
		   strerror(err));
		CC(write_in(state, &err), "child: the state dir is writable (%s)",
		   err ? strerror(err) : "yes");
		CC(write_in(run, &err), "child: the run dir is writable (%s)",
		   err ? strerror(err) : "yes");
		CC(write_in("/tmp", &err), "child: /tmp is writable (%s)",
		   err ? strerror(err) : "yes");
		CC(access(marker, F_OK) != 0, "child: /tmp is private (the host's marker is not there)");
		CC(status_value("CapEff:") == 0 && status_value("CapPrm:") == 0 &&
		       status_value("CapBnd:") == 0 && status_value("CapAmb:") == 0 &&
		       status_value("CapInh:") == 0,
		   "child: CapEff/CapPrm/CapBnd/CapAmb/CapInh all 0");
		CC(status_value("NoNewPrivs:") == 1, "child: NoNewPrivs 1");
		CC(setuid(0) != 0, "child: setuid(0) refused");
		{
			struct rlimit rl;
			CC(getrlimit(RLIMIT_NPROC, &rl) == 0 && rl.rlim_cur == WALLS_NPROC_MAX
			       && rl.rlim_max == WALLS_NPROC_MAX,
			   "child: RLIMIT_NPROC %d (review 2, L1)", WALLS_NPROC_MAX);
		}
		fflush(stdout);
		_exit(bad > 100 ? 100 : bad);
	}
	int st = 0;
	waitpid(pid, &st, 0);
	if (WIFEXITED(st) && WEXITSTATUS(st) == 200) {
		printf("  BLIND: this root cannot mount (a container without SYS_ADMIN?)\n");
		rc = 0;
	} else {
		CHECK(WIFEXITED(st) && WEXITSTATUS(st) == 0, "child: every wall in place (exit %d)",
		      WIFEXITED(st) ? WEXITSTATUS(st) : -1);
		CHECK(write_in(outside, &err), "parent: its tree is untouched (%s still writable)",
		      outside);
	}
	unlink(marker);
	rmdir(state);
	rmdir(run);
	rmdir(outside);
	rmdir(base);
	return rc;
}

int main(void)
{
	struct passwd *nb = getpwnam("nobody");
	bool blind = false;

	setvbuf(stdout, NULL, _IOLBF, 0);
	printf("02-walls-test (uid %ld)\n", (long)geteuid());
	case_context();
	case_unprivileged(nb);
	if (geteuid() == 0) {
		if (!nb) {
			printf("  BLIND: no user nobody to wall in\n");
			blind = true;
		} else if (!case_root(nb)) {
			blind = true;
		}
	} else {
		printf("  (the walls for real need root: see the header for the command)\n");
	}
	printf("%d passed, %d failed, of %d\n", passed, failed, passed + failed);
	if (failed)
		return 1;
	return blind ? 3 : 0;
}
