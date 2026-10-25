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

	/* review 3, F3: a mount of the host's, unmounted while the walls are up */
	char slave[700];
	int up[2], down[2];
	/* ⚠ under a SHARED mount, as systemd makes / on a host (a container's
	 *   mounts are private, and an unmount propagates through the mount point's
	 *   own mount): base bound onto itself and made shared, the tmpfs inside */
	char shared[640];
	snprintf(shared, sizeof shared, "%s/shared", base);
	CHECK(mkdir(shared, 0755) == 0 && mount(shared, shared, NULL, MS_BIND, NULL) == 0
	          && mount(NULL, shared, NULL, MS_SHARED, NULL) == 0,
	      "a shared mount at %s", shared);
	snprintf(slave, sizeof slave, "%s/slave", shared);
	CHECK(mkdir(slave, 0755) == 0 && mount("tmpfs", slave, "tmpfs", 0, "size=64k") == 0,
	      "a host tmpfs mounted at %s", slave);
	CHECK(pipe(up) == 0 && pipe(down) == 0, "two pipes");

	char cwd0[4096] = "";
	(void)!getcwd(cwd0, sizeof cwd0);
	fflush(stdout);
	pid_t pid = fork();
	if (pid == 0) {
		int bad = 0;
		close(up[0]);
		close(down[1]);
		ino_t ns0 = mnt_ns();
		if (walls_apply(&o, why, sizeof why) != 0) {
			printf("  walls_apply: %s\n", why);
			fflush(stdout);
			_exit(strstr(why, "unshare") || strstr(why, "a slave") ||
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
		/* lane 4's network-side review: what it writes it cannot execute */
		{
			char prog[4200];
			int pf;
			snprintf(prog, sizeof prog, "%s/x.sh", state);
			pf = open(prog, O_CREAT | O_TRUNC | O_WRONLY | O_CLOEXEC, 0755);
			if (pf >= 0) {
				(void)!write(pf, "#!/bin/sh\nexit 0\n", 17);
				close(pf);
			}
			errno = 0;
			char *const av[] = { prog, NULL };
			CC(pf >= 0 && execve(prog, av, environ) == -1 && errno == EACCES,
			   "child: a program written in the state dir does not execute (noexec: %s)",
			   strerror(errno));
			unlink(prog);
		}
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
			char cwd1[4096] = "";
			(void)!getcwd(cwd1, sizeof cwd1);
			CC(strncmp(cwd0, "/tmp", 4) == 0 ? strcmp(cwd1, "/") == 0 : strcmp(cwd1, cwd0) == 0,
			   "child: still in the root side's folder (%s), so a relative --page resolves as in 1.0",
			   cwd1);
		}
		/* review 3, F4 */
		{
			struct statvfs v;
			CC(statvfs("/", &v) == 0 && (v.f_flag & ST_NODEV) && (v.f_flag & ST_NOSUID),
			   "child: / is nodev and nosuid");
			int fd = open("/dev/null", O_RDWR);
			CC(fd >= 0 && write(fd, "x", 1) == 1, "child: /dev/null opens and takes a write");
			if (fd >= 0)
				close(fd);
			unsigned char r[8];
			fd = open("/dev/urandom", O_RDONLY);
			CC(fd >= 0 && read(fd, r, sizeof r) == (ssize_t)sizeof r, "child: /dev/urandom reads");
			if (fd >= 0)
				close(fd);
			CC(access("/dev/kvm", F_OK) != 0 && access("/dev/net/tun", F_OK) != 0
			       && access("/dev/fuse", F_OK) != 0 && access("/dev/sda", F_OK) != 0,
			   "child: no /dev/kvm, /dev/net/tun, /dev/fuse, /dev/sda in its /dev");
			CC(access("/dev/stdout", F_OK) == 0 && access("/dev/fd/0", F_OK) == 0,
			   "child: /dev/stdout and /dev/fd are there");
			CC(open("/dev/evil", O_CREAT | O_WRONLY, 0600) < 0, "child: its /dev is read-only");
			errno = 0;
			CC(unshare(CLONE_NEWUSER) != 0 && errno == EPERM,
			   "child: unshare(CLONE_NEWUSER) refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_clone3, NULL, 0) == -1 && errno == ENOSYS,
			   "child: clone3 says ENOSYS (glibc falls back to clone)");
			/* lane 4's network-side review: the kernel interfaces it never uses */
			errno = 0;
			CC(syscall(__NR_io_uring_setup, 1, NULL) == -1 && errno == ENOSYS,
			   "child: io_uring_setup says ENOSYS (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_userfaultfd, 0) == -1 && errno == EPERM,
			   "child: userfaultfd refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_perf_event_open, NULL, 0, -1, -1, 0) == -1 && errno == EPERM,
			   "child: perf_event_open refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_bpf, 0, NULL, 0) == -1 && errno == EPERM,
			   "child: bpf refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_keyctl, 0, 0, 0, 0, 0) == -1 && errno == EPERM,
			   "child: keyctl refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_add_key, "user", "x", "y", 1, 0) == -1 && errno == EPERM,
			   "child: add_key refused (%s)", strerror(errno));
			errno = 0;
			CC(syscall(__NR_ptrace, 0 /* PTRACE_TRACEME */, 0, 0, 0) == -1 && errno == EPERM,
			   "child: ptrace refused (%s)", strerror(errno));
			{
				char ch = 'x';
				int nf = open("/dev/null", O_RDWR);
				/* on /dev/null the kernel would say ENOTTY: EPERM is the filter's */
				errno = 0;
				CC(nf >= 0 && ioctl(nf, TIOCSTI, &ch) == -1 && errno == EPERM,
				   "child: ioctl TIOCSTI refused by the filter (%s)", strerror(errno));
				errno = 0;
				CC(nf >= 0 && (ioctl(nf, FIONREAD, &ch) == 0 || errno != EPERM),
				   "child: another ioctl still reaches the kernel (FIONREAD on /dev/null: %s, not EPERM)",
				   strerror(errno));
				if (nf >= 0)
					close(nf);
			}
			errno = 0;
			pid_t t = fork();
			if (t == 0)
				_exit(0);
			int fe = errno, ts = -1;
			pid_t w = t > 0 ? waitpid(t, &ts, 0) : -1;
			CC(t > 0 && w == t && WIFEXITED(ts) && WEXITSTATUS(ts) == 0,
			   "child: an ordinary fork still works (fork %ld %s, wait %ld, status %d)",
			   (long)t, strerror(fe), (long)w, ts);
		}
		/* review 3, F3: the host unmounts, the unmount reaches us */
		{
			char c = 1, line[1024];
			bool seen = false;
			FILE *mi;
			(void)!write(up[1], &c, 1);
			(void)!read(down[0], &c, 1);
			mi = fopen("/proc/self/mountinfo", "re");
			while (mi && fgets(line, sizeof line, mi))
				if (strstr(line, slave))
					seen = true;
			if (mi)
				fclose(mi);
			CC(!seen, "child: the host's umount of %s reached the walls (a slave, not private)",
			   slave);
		}
		{
			struct rlimit rl;
			/* 128 since 16 Oct 2026 (the coordinator): every network side of the uid counts */
			CC(getrlimit(RLIMIT_NPROC, &rl) == 0 && rl.rlim_cur == WALLS_NPROC_MAX
			       && rl.rlim_max == WALLS_NPROC_MAX && WALLS_NPROC_MAX == 128,
			   "child: RLIMIT_NPROC %d (review 2, L1; 128 since 16 Oct 2026)", WALLS_NPROC_MAX);
		}
		fflush(stdout);
		_exit(bad > 100 ? 100 : bad);
	}
	close(up[1]);
	close(down[0]);
	{
		char c;
		if (read(up[0], &c, 1) == 1) {
			CHECK(umount(slave) == 0, "the host unmounts %s", slave);
			(void)!write(down[1], &c, 1);
		}
	}
	close(up[0]);
	close(down[1]);
	int st = 0;
	waitpid(pid, &st, 0);
	(void)umount(slave);
	rmdir(slave);
	(void)umount(shared);
	rmdir(shared);
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

/* ⭐ 1.6 (AppArmor): `apparmor_exec_in()` with files in place of /sys and /proc */
static void put(const char *path, const char *text)
{
	FILE *f = fopen(path, "w");

	if (f) {
		fputs(text, f);
		fclose(f);
	}
}

static void slurp(const char *path, char *out, size_t n)
{
	FILE *f = fopen(path, "r");
	size_t k = 0;

	out[0] = '\0';
	if (f) {
		k = fread(out, 1, n - 1, f);
		fclose(f);
	}
	out[k] = '\0';
}

static void case_apparmor(void)
{
	char dir[] = "/tmp/remotix-test-aa.XXXXXX", en[160], pr[160], at[160], ol[160], got[160], why[256];
	int rc;

	if (!mkdtemp(dir)) {
		printf("  ??   no temporary directory for the AppArmor cases\n");
		return;
	}
	snprintf(en, sizeof en, "%s/enabled", dir);
	snprintf(pr, sizeof pr, "%s/profiles", dir);
	snprintf(at, sizeof at, "%s/attr-apparmor-exec", dir);
	snprintf(ol, sizeof ol, "%s/attr-exec", dir);

	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	CHECK(rc == 0 && strstr(walls_in_force(), "AppArmor: off"), "AppArmor: no kernel parameter file: off, go on");
	put(en, "N\n");
	put(at, "");
	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	slurp(at, got, sizeof got);
	CHECK(rc == 0 && !got[0] && strstr(walls_in_force(), "AppArmor: off"), "AppArmor: disabled: off, nothing written");
	put(en, "Y\n");
	put(pr, "remotix_networkx (enforce)\n/usr/bin/man (complain)\n");
	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	slurp(at, got, sizeof got);
	CHECK(rc == 0 && !got[0] && strstr(walls_in_force(), "NOT loaded"),
	      "AppArmor: on, only a profile with a longer name: not loaded, said, nothing written");
	put(pr, "docker-default (enforce)\nremotix_network (complain)\n");
	notes[0] = '\0';
	rc = apparmor_exec_in(en, pr, at, ol, "remotix_network", why, sizeof why);
	slurp(at, got, sizeof got);
	CHECK(rc == 0 && strcmp(got, "exec remotix_network") == 0 && strstr(walls_in_force(), "born in remotix_network"),
	      "AppArmor: loaded: «exec remotix_network» written to the attribute («%s»)", got);
	/* the older kernels: no per-LSM attribute, the generic one */
	{
		char missing[160];

		snprintf(missing, sizeof missing, "%s/no-such-dir/exec", dir);
		put(ol, "");
		notes[0] = '\0';
		rc = apparmor_exec_in(en, pr, missing, ol, "remotix_network", why, sizeof why);
		slurp(ol, got, sizeof got);
		CHECK(rc == 0 && strcmp(got, "exec remotix_network") == 0,
		      "AppArmor: no per-LSM attribute: the generic one is written");
		rc = apparmor_exec_in(en, pr, missing, missing, "remotix_network", why, sizeof why);
		CHECK(rc == -1 && strstr(why, "AppArmor"),
		      "AppArmor: loaded but no attribute to write: refused, the network side does not start (%s)", why);
		/* the write itself refused: the attribute is a directory */
		rc = apparmor_exec_in(en, pr, dir, dir, "remotix_network", why, sizeof why);
		CHECK(rc == -1 && strstr(why, "AppArmor"), "AppArmor: the attribute cannot be written: refused (%s)", why);
	}
	{
		char cmd[400];

		snprintf(cmd, sizeof cmd, "rm -f %s/enabled %s/profiles %s/attr-apparmor-exec %s/attr-exec && rmdir %s",
		         dir, dir, dir, dir, dir);
		if (system(cmd) != 0)
			printf("  (could not remove %s)\n", dir);
	}
	notes[0] = '\0';
}

int main(void)
{
	struct passwd *nb = getpwnam("nobody");
	bool blind = false;

	setvbuf(stdout, NULL, _IOLBF, 0);
	printf("02-walls-test (uid %ld)\n", (long)geteuid());
	case_context();
	case_apparmor();
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
