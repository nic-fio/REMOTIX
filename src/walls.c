/*
 * walls.c — ⭐ 1.5 (DECISIONS.md §11.50): the network side's walls.  The why
 *           and the list are in `walls.h`; here, the order and its reasons.
 *
 * ⛔ THE ORDER IS PART OF THE CURE, and every permutation fails differently:
 *
 *      · the checks that need no power first (the user, root, the two
 *        directories), so that a wrong option says so before anything moves;
 *      · `setexeccon` BEFORE the tree goes read-only: it writes
 *        /proc/thread-self/attr/exec, and on a read-only /proc that is EROFS;
 *      · the two writable directories are bind-mounted onto themselves BEFORE
 *        the recursive read-only step, so that each is a mount of its own
 *        whose read-only bit can be cleared AFTER — a mount made after the
 *        step would copy the bit from its source;
 *      · the private /tmp after the step: a new tmpfs is a new mount, born
 *        writable;
 *      · the bounding set dropped while still root (it needs CAP_SETPCAP),
 *        then groups → gid → uid (each step needs the power the next one
 *        takes away), then NO_NEW_PRIVS, then the check of what is left.
 *
 * ⚠ No GLib, no thread, no allocation that outlives the call: it runs in the
 *   root side's fork, right before `execve`.
 */
#include "walls.h"

#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <inttypes.h>
#include <sched.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/syscall.h>
#include <unistd.h>

/* ⚠ `mount_setattr()` (Linux 5.12) is called by number: glibc has its wrapper
 *   only since 2.36, and the struct under our own name so that a glibc that
 *   does declare `struct mount_attr` does not collide with it. */
#ifndef SYS_mount_setattr
#define SYS_mount_setattr 442
#endif
#ifndef AT_RECURSIVE
#define AT_RECURSIVE 0x8000
#endif
#define WALLS_ATTR_RDONLY 0x00000001ULL

/* ⭐ The SELinux type of the network side (lane 4's module). */
#define WALLS_SELINUX_TYPE "remotix_net_t"

struct walls_mount_attr {
	uint64_t attr_set;
	uint64_t attr_clr;
	uint64_t propagation;
	uint64_t userns_fd;
};

static int say(char *why, size_t n, const char *fmt, ...)
	__attribute__((format(printf, 3, 4)));
static int say(char *why, size_t n, const char *fmt, ...)
{
	va_list ap;
	if (why && n) {
		va_start(ap, fmt);
		vsnprintf(why, n, fmt, ap);
		va_end(ap);
	}
	return -1;
}

static int set_attr(const char *path, unsigned int flags, uint64_t set, uint64_t clr)
{
	struct walls_mount_attr a;
	memset(&a, 0, sizeof a);
	a.attr_set = set;
	a.attr_clr = clr;
	return (int)syscall(SYS_mount_setattr, AT_FDCWD, path, flags, &a, sizeof a);
}

/* `user:role:type[:level]` with the type replaced; false if `ctx` has fewer
 * than three fields or `out` is too small. */
static bool context_with_type(const char *ctx, const char *type, char *out, size_t n)
{
	const char *a, *b;
	int w;
	if (!ctx || !type || !out || !n)
		return false;
	a = strchr(ctx, ':');
	a = a ? strchr(a + 1, ':') : NULL;
	if (!a || a[1] == '\0' || a[1] == ':')
		return false;
	a++;                       /* the start of the type */
	b = strchr(a, ':');        /* the level, or NULL */
	w = snprintf(out, n, "%.*s%s%s", (int)(a - ctx), ctx, type, b ? b : "");
	return w > 0 && (size_t)w < n;
}

/* ⭐ On SELinux the network side is born `remotix_net_t`.  0 = done, or
 *    SELinux is not on; -1 = it is on and the context could not be set. */
static int selinux_exec_net(char *why, size_t n)
{
	void *l = dlopen("libselinux.so.1", RTLD_NOW | RTLD_LOCAL);
	char *cur = NULL;
	char fresh[512];
	int rc = -1;

	if (!l) {
		/* ⛔ No library is only «no SELinux» if the kernel says so too. */
		if (access("/sys/fs/selinux/enforce", F_OK) == 0)
			return say(why, n, "SELinux is on (/sys/fs/selinux) but libselinux.so.1 "
			           "does not open (%s): the network side cannot be put in %s",
			           dlerror(), WALLS_SELINUX_TYPE);
		return 0;
	}
	int (*enabled)(void) = (int (*)(void))dlsym(l, "is_selinux_enabled");
	int (*get)(char **) = (int (*)(char **))dlsym(l, "getcon");
	int (*set)(const char *) = (int (*)(const char *))dlsym(l, "setexeccon");
	int (*valid)(const char *) = (int (*)(const char *))dlsym(l, "security_check_context");
	void (*free_fn)(char *) = (void (*)(char *))dlsym(l, "freecon");

	if (!enabled || !get || !set || !valid || !free_fn) {
		say(why, n, "libselinux.so.1 lacks one of is_selinux_enabled, getcon, "
		    "setexeccon, security_check_context, freecon");
		goto fine;
	}
	if (enabled() != 1) {
		rc = 0;
		goto fine;
	}
	if (get(&cur) != 0 || !cur) {
		say(why, n, "SELinux: getcon failed (%s)", strerror(errno));
		goto fine;
	}
	if (!context_with_type(cur, WALLS_SELINUX_TYPE, fresh, sizeof fresh)) {
		say(why, n, "SELinux: my context «%s» is not user:role:type[:level]", cur);
		goto fine;
	}
	if (valid(fresh) != 0) {
		say(why, n, "SELinux: «%s» is not a context of the loaded policy — the "
		    "remotix module with %s is not installed (the root side runs «%s»)",
		    fresh, WALLS_SELINUX_TYPE, cur);
		goto fine;
	}
	if (set(fresh) != 0) {
		say(why, n, "SELinux: setexeccon(«%s») refused (%s)", fresh, strerror(errno));
		goto fine;
	}
	rc = 0;
fine:
	if (cur)
		free_fn(cur);
	dlclose(l);
	return rc;
}

/* A directory the network side must write: absolute, there, a directory,
 * and the network user's — otherwise it would fail later with a line that
 * names neither the directory nor the fix. */
static int writable_dir_ok(const char *what, const char *dir, uid_t uid, char *why,
                           size_t n)
{
	struct stat st;
	if (!dir || dir[0] != '/')
		return say(why, n, "the %s directory «%s» is not an absolute path", what,
		           dir ? dir : "(none)");
	/* ⛔ `[M]` 16 Oct 2026, rxtest build's served page: a state dir under /tmp vanished
	 *    under the private tmpfs the walls mount there, and the line said only «not
	 *    writable after the walls». */
	if (strcmp(dir, "/tmp") == 0 || strncmp(dir, "/tmp/", 5) == 0)
		return say(why, n, "the %s directory %s is under /tmp, which the walls replace "
		           "with a private, empty tmpfs: put it elsewhere (e.g. /var/tmp)", what, dir);
	if (lstat(dir, &st) != 0)
		return say(why, n, "the %s directory %s does not exist (%s): the package "
		           "creates it (tmpfiles/upgrade), a bench passes its own with "
		           "--network-%s-dir", what, dir, strerror(errno), what);
	if (!S_ISDIR(st.st_mode))
		return say(why, n, "the %s directory %s is not a directory (mode %06o)", what,
		           dir, (unsigned)st.st_mode);
	if (st.st_uid != uid)
		return say(why, n, "the %s directory %s belongs to uid %ld (mode %04o), not "
		           "to the network side (uid %ld): run the upgrade's chown", what, dir,
		           (long)st.st_uid, (unsigned)(st.st_mode & 07777), (long)uid);
	return 0;
}

static bool status_hex(const char *line, const char *key, uint64_t *v)
{
	size_t k = strlen(key);
	if (strncmp(line, key, k) != 0)
		return false;
	*v = strtoull(line + k, NULL, 16);
	return true;
}

/* ⛔ What the kernel says is left — not what the calls above meant to leave
 *    (`CODER.md` §3.7: asked of the kernel). */
static int nothing_left(char *why, size_t n)
{
	FILE *f = fopen("/proc/self/status", "re");
	char line[256];
	uint64_t inh = 1, prm = 1, eff = 1, bnd = 1, amb = 1, nnp = 0;
	int seen = 0;

	if (!f)
		return say(why, n, "cannot read /proc/self/status (%s) to check the "
		           "capabilities", strerror(errno));
	while (fgets(line, sizeof line, f)) {
		uint64_t v;
		if (status_hex(line, "CapInh:", &v)) { inh = v; seen++; }
		else if (status_hex(line, "CapPrm:", &v)) { prm = v; seen++; }
		else if (status_hex(line, "CapEff:", &v)) { eff = v; seen++; }
		else if (status_hex(line, "CapBnd:", &v)) { bnd = v; seen++; }
		else if (status_hex(line, "CapAmb:", &v)) { amb = v; seen++; }
		else if (strncmp(line, "NoNewPrivs:", 11) == 0) {
			nnp = strtoull(line + 11, NULL, 10);
			seen++;
		}
	}
	fclose(f);
	if (seen < 6)
		return say(why, n, "/proc/self/status lacks some of CapInh/CapPrm/CapEff/"
		           "CapBnd/CapAmb/NoNewPrivs (%d of 6 seen)", seen);
	if (inh | prm | eff | bnd | amb)
		return say(why, n, "capabilities left after the drop: CapInh %016" PRIx64
		           " CapPrm %016" PRIx64 " CapEff %016" PRIx64 " CapBnd %016" PRIx64
		           " CapAmb %016" PRIx64, inh, prm, eff, bnd, amb);
	if (nnp != 1)
		return say(why, n, "NoNewPrivs is %" PRIu64 " after PR_SET_NO_NEW_PRIVS", nnp);
	return 0;
}

static int drop_bounding_set(char *why, size_t n)
{
	int last = 63;
	FILE *f = fopen("/proc/sys/kernel/cap_last_cap", "re");
	if (f) {
		if (fscanf(f, "%d", &last) != 1 || last < 0 || last > 63)
			last = 63;
		fclose(f);
	}
	for (int c = 0; c <= last; c++)
		if (prctl(PR_CAPBSET_DROP, c, 0, 0, 0) != 0 && errno != EINVAL)
			return say(why, n, "PR_CAPBSET_DROP(%d) failed (%s)", c, strerror(errno));
	return 0;
}

int walls_apply(const struct rootside_options *o, char *why, size_t why_len)
{
	struct statvfs vs;
	uid_t ru, eu, su;
	gid_t rg, eg, sg;
	uid_t uid;
	gid_t gid;

	if (why && why_len)
		why[0] = '\0';
	if (!o)
		return say(why, why_len, "no options");

	/* ⛔ 1 — the checks that need no power.  The user was resolved by
	 *    `main.c` (`--network-user`, default remotix): its uid and gid. */
	uid = o->remotix_uid;
	gid = o->remotix_gid;
	if (uid == 0 || gid == 0)
		return say(why, why_len, "the network user is uid %ld gid %ld: it must "
		           "not be root", (long)uid, (long)gid);
	if (geteuid() != 0)
		return say(why, why_len, "the walls are put up by root, and this process is "
		           "uid %ld: the root side must run as root", (long)geteuid());
	if (writable_dir_ok("state", o->net_state_dir, uid, why, why_len) != 0 ||
	    writable_dir_ok("run", o->net_run_dir, uid, why, why_len) != 0)
		return -1;

	/* ⛔ 2 — SELinux, while /proc can still be written. */
	if (selinux_exec_net(why, why_len) != 0)
		return -1;

	/* ⛔ 3 — the read-only tree. */
	if (unshare(CLONE_NEWNS) != 0)
		return say(why, why_len, "unshare(CLONE_NEWNS) failed (%s)", strerror(errno));
	if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) != 0)
		return say(why, why_len, "making / recursively private failed (%s)",
		           strerror(errno));
	if (mount(o->net_state_dir, o->net_state_dir, NULL, MS_BIND | MS_REC, NULL) != 0)
		return say(why, why_len, "bind of %s onto itself failed (%s)",
		           o->net_state_dir, strerror(errno));
	if (mount(o->net_run_dir, o->net_run_dir, NULL, MS_BIND | MS_REC, NULL) != 0)
		return say(why, why_len, "bind of %s onto itself failed (%s)",
		           o->net_run_dir, strerror(errno));
	if (set_attr("/", AT_RECURSIVE, WALLS_ATTR_RDONLY, 0) != 0)
		return say(why, why_len, "mount_setattr(/, AT_RECURSIVE, RDONLY) failed (%s)%s",
		           strerror(errno),
		           errno == ENOSYS ? ": the kernel is older than 5.12" : "");
	if (set_attr(o->net_state_dir, 0, 0, WALLS_ATTR_RDONLY) != 0)
		return say(why, why_len, "making %s writable again failed (%s)",
		           o->net_state_dir, strerror(errno));
	if (set_attr(o->net_run_dir, 0, 0, WALLS_ATTR_RDONLY) != 0)
		return say(why, why_len, "making %s writable again failed (%s)",
		           o->net_run_dir, strerror(errno));
	if (mount("tmpfs", "/tmp", "tmpfs", MS_NOSUID | MS_NODEV | MS_NOEXEC,
	          "mode=1777,size=16m") != 0)
		return say(why, why_len, "the private tmpfs on /tmp failed (%s)", strerror(errno));
	/* ⭐ asked back of the kernel, not assumed */
	if (statvfs("/", &vs) != 0 || !(vs.f_flag & ST_RDONLY))
		return say(why, why_len, "/ is not read-only after mount_setattr");
	if (statvfs(o->net_state_dir, &vs) != 0 || (vs.f_flag & ST_RDONLY))
		return say(why, why_len, "%s is not writable after the walls", o->net_state_dir);
	if (statvfs(o->net_run_dir, &vs) != 0 || (vs.f_flag & ST_RDONLY))
		return say(why, why_len, "%s is not writable after the walls", o->net_run_dir);
	if (chdir("/") != 0)
		return say(why, why_len, "chdir(/) failed (%s)", strerror(errno));

	/* ⛔ 4 — the identity, and nothing left. */
	if (drop_bounding_set(why, why_len) != 0)
		return -1;
	if (setgroups(0, NULL) != 0)
		return say(why, why_len, "setgroups(0) failed (%s)", strerror(errno));
	if (setresgid(gid, gid, gid) != 0)
		return say(why, why_len, "setresgid(%ld) failed (%s)", (long)gid, strerror(errno));
	/* ⛔ Review 2, L1: a process cap for the network user, BEFORE the uid
	 *    changes — a hijacked network side forking without end would fill the
	 *    unit's TasksMax, and the root side could fork no child, no PAM
	 *    grandchild: no login.  It counts threads (GDBus's): 64 is wide. */
	{
		struct rlimit nproc = { WALLS_NPROC_MAX, WALLS_NPROC_MAX };

		if (setrlimit(RLIMIT_NPROC, &nproc) != 0)
			return say(why, why_len, "setrlimit(RLIMIT_NPROC, %d) failed (%s)",
			           WALLS_NPROC_MAX, strerror(errno));
	}
	if (setresuid(uid, uid, uid) != 0)
		return say(why, why_len, "setresuid(%ld) failed (%s)", (long)uid, strerror(errno));
	if (getresuid(&ru, &eu, &su) != 0 || ru != uid || eu != uid || su != uid)
		return say(why, why_len, "getresuid says %ld/%ld/%ld, not %ld", (long)ru,
		           (long)eu, (long)su, (long)uid);
	if (getresgid(&rg, &eg, &sg) != 0 || rg != gid || eg != gid || sg != gid)
		return say(why, why_len, "getresgid says %ld/%ld/%ld, not %ld", (long)rg,
		           (long)eg, (long)sg, (long)gid);
	if (getgroups(0, NULL) != 0)
		return say(why, why_len, "%d supplementary groups left", getgroups(0, NULL));
	if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0)
		return say(why, why_len, "PR_SET_NO_NEW_PRIVS failed (%s)", strerror(errno));
	return nothing_left(why, why_len);
}
