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
#include <stddef.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>

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
#define WALLS_ATTR_NOSUID 0x00000002ULL
#define WALLS_ATTR_NODEV  0x00000004ULL
#define WALLS_ATTR_NOEXEC 0x00000008ULL

/* ⛔ Review 3, F4: the only device nodes the network side finds in its /dev
 *    (a tmpfs of its own); everything else under /dev — /dev/kvm, /dev/net/tun,
 *    /dev/fuse, world-writable on some distributions — is not there. */
static const char *const walls_devices[] = { "null", "zero", "full", "random", "urandom" };

/* ⛔ Review 3, F4: a raw-BPF seccomp filter, no libseccomp — no user
 *    namespace (`unshare`/`clone` with CLONE_NEWUSER ⇒ EPERM: it would give a
 *    hijacked network side CAP_SYS_ADMIN inside it, the largest kernel
 *    surface), `clone3` ⇒ ENOSYS (its flags are behind a pointer BPF cannot
 *    read; glibc falls back to `clone`), any other ABI on the same kernel
 *    (x32, a foreign arch) ⇒ EPERM. */
#if defined(__x86_64__)
#define WALLS_AUDIT_ARCH AUDIT_ARCH_X86_64
#elif defined(__aarch64__)
#define WALLS_AUDIT_ARCH AUDIT_ARCH_AARCH64
#endif

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

/* ⭐ Review 4 B, findings 5 and 6: what the walls ARE, said once.  The walls
 *    run in the fork, where this file writes no log (no GLib, nothing that
 *    outlives the call): they write here, and the root side writes ONE line
 *    with it before the `execve` (`walls_in_force()`). */
static char notes[640];

static void note(const char *fmt, ...) __attribute__((format(printf, 1, 2)));
static void note(const char *fmt, ...)
{
	size_t used = strlen(notes);
	va_list ap;

	if (used + 2 >= sizeof notes)
		return;
	if (used)
		notes[used++] = ';', notes[used++] = ' ', notes[used] = '\0';
	va_start(ap, fmt);
	vsnprintf(notes + used, sizeof notes - used, fmt, ap);
	va_end(ap);
}

const char *walls_in_force(void)
{
	return notes;
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
		note("SELinux: off (no libselinux, no /sys/fs/selinux)");
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
		goto out;
	}
	if (enabled() != 1) {
		note("SELinux: off (is_selinux_enabled)");
		rc = 0;
		goto out;
	}
	if (get(&cur) != 0 || !cur) {
		say(why, n, "SELinux: getcon failed (%s)", strerror(errno));
		goto out;
	}
	if (!context_with_type(cur, WALLS_SELINUX_TYPE, fresh, sizeof fresh)) {
		say(why, n, "SELinux: my context «%s» is not user:role:type[:level]", cur);
		goto out;
	}
	if (valid(fresh) != 0) {
		say(why, n, "SELinux: «%s» is not a context of the loaded policy — the "
		    "remotix module with %s is not installed (the root side runs «%s»)",
		    fresh, WALLS_SELINUX_TYPE, cur);
		goto out;
	}
	if (set(fresh) != 0) {
		say(why, n, "SELinux: setexeccon(«%s») refused (%s)", fresh, strerror(errno));
		goto out;
	}
	note("SELinux: born %s", fresh);
	rc = 0;
out:
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

/* ⛔ Review 3, F4: /dev is a tmpfs of the network side's own, with the five
 *    harmless nodes bound in from the real /dev (opened BEFORE the tmpfs hides
 *    it, bound through /proc/self/fd), the usual fd links, and then read-only,
 *    nosuid, noexec.  The binds inherit the recursive nodev of step 3: it is
 *    cleared on each of them, and only on them. */
static int private_dev(char *why, size_t n)
{
	enum { ND = sizeof walls_devices / sizeof walls_devices[0] };
	int fds[ND];
	int rc = 0;

	for (int i = 0; i < ND; i++) {
		char p[64];
		snprintf(p, sizeof p, "/dev/%s", walls_devices[i]);
		fds[i] = open(p, O_PATH | O_CLOEXEC);
		if (fds[i] < 0) {
			for (int j = 0; j < i; j++)
				close(fds[j]);
			return say(why, n, "%s cannot be opened for the private /dev (%s)", p,
			           strerror(errno));
		}
	}
	if (mount("tmpfs", "/dev", "tmpfs", MS_NOSUID | MS_NOEXEC, "mode=0755,size=64k") != 0) {
		rc = say(why, n, "the private tmpfs on /dev failed (%s)", strerror(errno));
		goto out;
	}
	for (int i = 0; i < ND && rc == 0; i++) {
		char p[64], src[64];
		int f;
		snprintf(p, sizeof p, "/dev/%s", walls_devices[i]);
		snprintf(src, sizeof src, "/proc/self/fd/%d", fds[i]);
		f = open(p, O_CREAT | O_EXCL | O_WRONLY | O_CLOEXEC, 0666);
		if (f < 0) {
			rc = say(why, n, "%s cannot be made in the private /dev (%s)", p, strerror(errno));
			break;
		}
		close(f);
		if (mount(src, p, NULL, MS_BIND, NULL) != 0)
			rc = say(why, n, "the bind of %s into the private /dev failed (%s)", p,
			         strerror(errno));
		else if (set_attr(p, 0, WALLS_ATTR_NOSUID | WALLS_ATTR_NOEXEC, WALLS_ATTR_NODEV) != 0)
			rc = say(why, n, "%s: nodev could not be cleared on its bind (%s)", p,
			         strerror(errno));
	}
	if (rc == 0 && (symlink("/proc/self/fd", "/dev/fd") != 0
	                || symlink("/proc/self/fd/0", "/dev/stdin") != 0
	                || symlink("/proc/self/fd/1", "/dev/stdout") != 0
	                || symlink("/proc/self/fd/2", "/dev/stderr") != 0))
		rc = say(why, n, "the fd links of the private /dev failed (%s)", strerror(errno));
	if (rc == 0 && set_attr("/dev", 0, WALLS_ATTR_RDONLY | WALLS_ATTR_NODEV | WALLS_ATTR_NOSUID
	                                       | WALLS_ATTR_NOEXEC, 0) != 0)
		rc = say(why, n, "the private /dev could not be made read-only (%s)", strerror(errno));
out:
	for (int i = 0; i < ND; i++)
		close(fds[i]);
	return rc;
}

static int no_user_namespaces(char *why, size_t n)
{
#ifndef WALLS_AUDIT_ARCH
	return say(why, n, "no seccomp filter for this architecture (only x86_64 and aarch64): "
	           "the network side is not started without one");
#else
	struct sock_filter f[] = {
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, WALLS_AUDIT_ARCH, 1, 0),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
#if defined(__x86_64__)
		/* x32 on an x86_64 kernel: another table, refused whole */
		BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000u, 0, 1),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
#endif
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clone3, 0, 1),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | ENOSYS),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_unshare, 1, 0),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_clone, 0, 3),
		/* the flags: the first argument of both, its low word (little endian) */
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, args[0])),
		BPF_JUMP(BPF_JMP | BPF_JSET | BPF_K, CLONE_NEWUSER, 0, 1),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
	};
	struct sock_fprog prog = { (unsigned short)(sizeof f / sizeof f[0]), f };

	if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog, 0, 0) != 0)
		return say(why, n, "the seccomp filter (no user namespaces) was refused (%s)",
		           strerror(errno));
	return 0;
#endif
}

int walls_apply(const struct rootside_options *o, char *why, size_t why_len)
{
	struct statvfs vs;
	uid_t ru, eu, su;
	gid_t rg, eg, sg;
	uid_t uid;
	gid_t gid;
	char cwd[4096];

	if (why && why_len)
		why[0] = '\0';
	notes[0] = '\0';
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
	if (!getcwd(cwd, sizeof cwd)) {
		note("⚠ the root side's folder is unknown (getcwd: %s)", strerror(errno));
		cwd[0] = '\0';
	}
	if (unshare(CLONE_NEWNS) != 0)
		return say(why, why_len, "unshare(CLONE_NEWNS) failed (%s)", strerror(errno));
	/* ⛔ SLAVE, not PRIVATE (review 3, F3): a private copy pinned every host
	 *    mount for the network side's life — `umount` of a USB disk, an NFS or
	 *    LUKS volume «succeeded» on the host while the superblock stayed busy
	 *    here.  As a slave, unmounts propagate in and nothing goes out.  ⚠ A
	 *    mount made on the host LATER arrives without the read-only bit: DAC
	 *    still applies, and remotix owns nothing there (systemd's
	 *    ProtectSystem= makes the same choice). */
	if (mount(NULL, "/", NULL, MS_REC | MS_SLAVE, NULL) != 0)
		return say(why, why_len, "making / recursively a slave failed (%s)",
		           strerror(errno));
	if (mount(o->net_state_dir, o->net_state_dir, NULL, MS_BIND | MS_REC, NULL) != 0)
		return say(why, why_len, "bind of %s onto itself failed (%s)",
		           o->net_state_dir, strerror(errno));
	if (mount(o->net_run_dir, o->net_run_dir, NULL, MS_BIND | MS_REC, NULL) != 0)
		return say(why, why_len, "bind of %s onto itself failed (%s)",
		           o->net_run_dir, strerror(errno));
	/* ⛔ nosuid and nodev too (review 3, F4): read-only does not stop opening
	 *    a device node for writing. */
	if (set_attr("/", AT_RECURSIVE, WALLS_ATTR_RDONLY | WALLS_ATTR_NOSUID | WALLS_ATTR_NODEV,
	             0) != 0)
		return say(why, why_len, "mount_setattr(/, AT_RECURSIVE, RDONLY|NOSUID|NODEV) failed (%s)%s",
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
	if (private_dev(why, why_len) != 0)
		return -1;
	/* ⭐ asked back of the kernel, not assumed */
	if (statvfs("/", &vs) != 0)
		return say(why, why_len, "statvfs(/) after mount_setattr failed (%s)", strerror(errno));
	if (!(vs.f_flag & ST_RDONLY))
		return say(why, why_len, "/ is not read-only after mount_setattr");
	if (statvfs(o->net_state_dir, &vs) != 0)
		return say(why, why_len, "statvfs(%s) after the walls failed (%s)", o->net_state_dir,
		           strerror(errno));
	if (vs.f_flag & ST_RDONLY)
		return say(why, why_len, "%s is not writable after the walls", o->net_state_dir);
	if (statvfs(o->net_run_dir, &vs) != 0)
		return say(why, why_len, "statvfs(%s) after the walls failed (%s)", o->net_run_dir,
		           strerror(errno));
	if (vs.f_flag & ST_RDONLY)
		return say(why, why_len, "%s is not writable after the walls", o->net_run_dir);
	/* ⚠ Back to the root side's own folder, by its path, in the NEW tree: a
	 *   relative --page (the default «page.html», next to the binary the way
	 *   02-pam-start.sh starts it) is resolved there, as in 1.0 — found by
	 *   running that bench, 16 Oct 2026.  A folder the walls hid (under /tmp) or
	 *   that is gone: «/». */
	if (cwd[0] == '\0' || chdir(cwd) != 0) {
		/* ⛔ review 4 B, finding 5: said — a relative --page resolves from «/»
		 *    now, the defect of 16 Oct, and the line must name it */
		if (cwd[0])
			note("⚠ folder %s not reachable inside the walls (%s): the network side "
			     "works from «/» — a relative --page or --certificates resolves there",
			     cwd, strerror(errno));
		if (chdir("/") != 0)
			return say(why, why_len, "chdir(/) failed (%s)", strerror(errno));
	} else {
		note("folder %s", cwd);
	}

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
	if (nothing_left(why, why_len) != 0)
		return -1;
	/* ⛔ 5 — no user namespace, ever (review 3, F4): after NO_NEW_PRIVS, which
	 *    an unprivileged filter needs. */
	if (no_user_namespaces(why, why_len) != 0)
		return -1;
	note("tree read-only, nosuid, nodev but %s and %s; private /tmp and /dev; uid/gid %ld/%ld, "
	     "no groups, no capabilities, no_new_privs; RLIMIT_NPROC %d; seccomp: no user "
	     "namespaces", o->net_state_dir, o->net_run_dir, (long)uid, (long)gid, WALLS_NPROC_MAX);
	return 0;
}
