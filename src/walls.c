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
 *      · ⭐ 1.6 (R8 B): the network side is PID 1 of a PID namespace of its own, born by
 *        `walls_fork_pidns()` (a `clone` with CLONE_NEWPID, in the root side): the /proc it
 *        sees is mounted here, new, right after the mounts are made slaves — it lists
 *        that one process, and no desktop, no root-side process, no other server;
 *      · the private /tmp after the step: a new tmpfs is a new mount, born
 *        writable;
 *      · the network namespace of its own while still root (CLONE_NEWNET needs
 *        CAP_SYS_ADMIN), after the mounts and before the identity changes;
 *      · the bounding set dropped while still root (it needs CAP_SETPCAP),
 *        then groups → gid → uid (each step needs the power the next one
 *        takes away), then NO_NEW_PRIVS, then the check of what is left;
 *      · Landlock's abstract-socket scope after NO_NEW_PRIVS (restrict_self
 *        needs it), before the seccomp filter.
 *
 * ⚠ No GLib, no thread, no allocation that outlives the call: it runs in the
 *   root side's fork, right before `execve`.
 */
#include "walls.h"

#include <dirent.h>
#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <inttypes.h>
#include <sched.h>
#include <signal.h>
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
#include <limits.h>
#include <sys/statvfs.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stddef.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/ioctl.h>   /* TIOCSTI, TIOCLINUX, SIOCGIFFLAGS */
#include <net/if.h>
#include <sys/socket.h>

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

/* ⭐ 1.6 (audit split R5/R6): Landlock is called by number (glibc has no wrapper) and the struct under our own name.  The
 *   ABI is asked first: `scoped` exists from ABI 6 (Linux 6.12); a larger struct than the kernel knows with a non-zero
 *   new field is E2BIG, so an older kernel is never given it. */
#ifndef SYS_landlock_create_ruleset
#define SYS_landlock_create_ruleset 444
#define SYS_landlock_restrict_self 446
#endif
#define WALLS_LANDLOCK_VERSION (1U << 0)
#define WALLS_LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET (1ULL << 0)
struct walls_landlock_attr {
	uint64_t handled_access_fs;
	uint64_t handled_access_net;
	uint64_t scoped;
};

/* ⭐ 1.6 (R8 B): `fork()` with CLONE_NEWPID.  The child is PID 1 of a new PID namespace (the root side sees it by its real pid and
 *    can signal and wait for it as for any child); everything it starts in that namespace dies with it, and the kernel kills them
 *    when it exits.  The raw system call, flags + SIGCHLD and the rest zero: the arguments after the flags differ between x86_64
 *    and aarch64 and none is used. */
pid_t walls_fork_pidns(void)
{
	return (pid_t)syscall(SYS_clone, CLONE_NEWPID | SIGCHLD, 0, 0, 0, 0);
}

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
static char notes[1024];

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
	/* ⛔ A trailing «/» makes even lstat() follow a symlink in the last place:
	 *    the walk below would then check the link's parents, not the target's. */
	if (strlen(dir) > 1 && dir[strlen(dir) - 1] == '/')
		return say(why, n, "the %s directory %s ends with «/»: give it without", what, dir);
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
	/* ⛔ 24 Oct 2026 (review of the port): `mount(dir, dir, MS_BIND)` follows
	 *    the path, `lstat` above does not — a parent the network user could
	 *    write would let it swap the directory for a symlink between the two,
	 *    and another host folder would come in writable.  So every ancestor
	 *    must be a real directory of root's that nobody else can write — or a
	 *    sticky one (/var/tmp) whose entry on the path is root's too: there
	 *    only root may rename it.  ⚠ The directory itself directly in a sticky
	 *    folder is refused: its owner, the network user, could rename it. */
	{
		char up[PATH_MAX];
		size_t len = strlen(dir);
		struct stat a;
		uid_t below = st.st_uid; /* the owner of the entry just under `up` */

		if (len >= sizeof up)
			return say(why, n, "the %s directory path is too long", what);
		/* the walk below reads the path as written: no `.` or `..` in it */
		if (strstr(dir, "/./") || strstr(dir, "/../") ||
		    (len >= 2 && strcmp(dir + len - 2, "/.") == 0) ||
		    (len >= 3 && strcmp(dir + len - 3, "/..") == 0))
			return say(why, n, "the %s directory %s has «.» or «..» in it: give it "
			           "plain", what, dir);
		memcpy(up, dir, len + 1);
		while (len > 1 && up[len - 1] == '/')
			up[--len] = '\0';
		for (;;) {
			char *slash = strrchr(up, '/');
			if (!slash)
				break;
			if (slash == up)
				slash[1] = '\0';
			else
				*slash = '\0';
			if (lstat(up, &a) != 0)
				return say(why, n, "lstat(%s) failed (%s)", up, strerror(errno));
			if (!S_ISDIR(a.st_mode) || a.st_uid != 0 ||
			    ((a.st_mode & 022) && !((a.st_mode & S_ISVTX) && below == 0)))
				return say(why, n, "the %s directory %s sits under %s, which is not a "
				           "root directory closed to others (uid %ld, mode %04o): the "
				           "walls refuse a path someone else could rewrite", what, dir,
				           up, (long)a.st_uid, (unsigned)(a.st_mode & 07777));
			below = a.st_uid;
			if (slash == up)
				break;
		}
	}
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

/* ⛔ Lane 4's network-side review (16 Oct 2026): the kernel interfaces an
 *    unprivileged process still reaches and the network side never uses — the
 *    usual stepping stones of a local kernel exploit from a hijacked, internet-
 *    facing process.  Refused whatever the distribution's sysctls say
 *    (kernel.io_uring_disabled, vm.unprivileged_userfaultfd,
 *    kernel.perf_event_paranoid, kernel.unprivileged_bpf_disabled differ):
 *      · io_uring ⇒ ENOSYS (a library that tries it falls back to read/write);
 *      · userfaultfd, perf_event_open, bpf, the key syscalls, ptrace ⇒ EPERM;
 *      · ioctl TIOCSTI / TIOCLINUX ⇒ EPERM: fds 0-2 are the root side's, and
 *        started by hand from a root shell they are ITS terminal — TIOCSTI
 *        would type commands into it. */
#ifndef __NR_pidfd_getfd
#define __NR_pidfd_getfd 438 /* the same number on every architecture */
#endif
#ifndef __NR_io_uring_setup
#define __NR_io_uring_setup 425
#endif
#ifndef __NR_io_uring_enter
#define __NR_io_uring_enter 426
#endif
#ifndef __NR_io_uring_register
#define __NR_io_uring_register 427
#endif
#define WALLS_DENY(nr, err)                                        \
	BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (nr), 0, 1),            \
	BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (err))

/* ⭐ 1.6 (audit split R5 and R6) — A NETWORK OF ITS OWN.  `unshare(CLONE_NEWNET)`: the network side keeps the descriptors it
 *    was handed (3 the root side, 4 the UDP port, 5 the page's TCP listener: a socket belongs to the namespace where it was
 *    CREATED, so they go on working), and loses everything else of the network:
 *      · it can no longer open a connection to anything — Internet, LAN, the host's own services on 127.0.0.1;
 *      · the ABSTRACT Unix sockets of the machine (`@/tmp/.X11-unix/X0` of every desktop, `@/tmp/dbus-…`, multipathd's) live in
 *        the network namespace: there are none in the new one.  The mounts hid the path ones; this hides these.
 *    Sockets on a PATH (the journal, sssd, nscd, the system bus) are not touched: they follow the mounts.
 *    ⚠ The new namespace has a loopback, DOWN: it is raised, so that a `bind(127.0.0.1)` or a `getaddrinfo("localhost")` of a
 *      library does not find a dead interface.  If that fails it is said, not fatal.  ⚠ `if_indextoname()` and the like open a
 *      socket in the NEW namespace and would not find the host's interfaces: the network side uses only numeric scopes. */
static int own_network(char *why, size_t n)
{
	struct ifreq ifr;
	int s;

	if (unshare(CLONE_NEWNET) != 0)
		return say(why, n, "unshare(CLONE_NEWNET) failed (%s)", strerror(errno));
	s = socket(AF_INET, SOCK_DGRAM | SOCK_CLOEXEC, 0);
	if (s < 0) {
		note("⚠ loopback of the private network not raised (socket: %s)", strerror(errno));
		return 0;
	}
	memset(&ifr, 0, sizeof ifr);
	snprintf(ifr.ifr_name, sizeof ifr.ifr_name, "lo");
	if (ioctl(s, SIOCGIFFLAGS, &ifr) != 0) {
		note("⚠ loopback of the private network not raised (SIOCGIFFLAGS: %s)", strerror(errno));
	} else if (!(ifr.ifr_flags & IFF_UP)) {
		ifr.ifr_flags |= IFF_UP;
		if (ioctl(s, SIOCSIFFLAGS, &ifr) != 0)
			note("⚠ loopback of the private network not raised (SIOCSIFFLAGS: %s)", strerror(errno));
	}
	close(s);
	return 0;
}

/* ⭐ 1.6 (audit split R6) — A SECOND LEVEL, where the kernel has it: Landlock's scope on abstract Unix sockets (Linux 6.12, ABI
 *    6) forbids connecting to one created OUTSIDE this process's domain.  The private network already hides them all; this
 *    holds if that ever does not.  It never fails the walls: a kernel without Landlock (or with it off) is a line in the notes.
 *    ⚠ Needs NO_NEW_PRIVS (set by then). */
static void scope_abstract_sockets(void)
{
	struct walls_landlock_attr a = { 0, 0, WALLS_LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET };
	long abi, fd;

	abi = syscall(SYS_landlock_create_ruleset, NULL, (size_t)0, WALLS_LANDLOCK_VERSION);
	if (abi < 0) {
		note("landlock not available (%s)", strerror(errno));
		return;
	}
	if (abi < 6) {
		note("landlock ABI %ld: abstract sockets not scoped (needs 6)", abi);
		return;
	}
	fd = syscall(SYS_landlock_create_ruleset, &a, sizeof a, 0U);
	if (fd < 0) {
		note("⚠ landlock ruleset refused (%s)", strerror(errno));
		return;
	}
	if (syscall(SYS_landlock_restrict_self, (int)fd, 0U) != 0)
		note("⚠ landlock restrict_self refused (%s)", strerror(errno));
	else
		note("landlock ABI %ld: abstract unix sockets scoped", abi);
	close((int)fd);
}

/* ⭐ 1.6 (R8 B) — A /PROC OF ITS OWN.  Mounted in the PID namespace the network side is pid 1 of: it lists that process and nothing
 *    else (no desktop, no root-side process, no other server), so `/proc/<pid>/{environ,cmdline,maps,fd,...}` of anyone else is not
 *    there to read.  `hidepid=invisible` (Linux 5.8) is a belt on top; where the kernel does not know it the mount is made without.
 *    ⚠ `hidepid` alone, in the host's PID namespace, would not do: it is an option of the namespace's one /proc superblock and
 *      would hide processes from every user of the host.  ⛔ Asked back of the kernel: more than one numeric entry in the new /proc
 *      means this process is not alone in its namespace, and the walls are refused. */
static int private_proc(char *why, size_t n)
{
	const unsigned long fl = MS_NOSUID | MS_NODEV | MS_NOEXEC;
	struct dirent *e;
	DIR *d;
	int pids = 0;

	if (mount("proc", "/proc", "proc", fl, "hidepid=invisible") != 0 &&
	    (errno != EINVAL || mount("proc", "/proc", "proc", fl, NULL) != 0))
		return say(why, n, "the private /proc failed (%s)", strerror(errno));
	d = opendir("/proc");
	if (!d)
		return say(why, n, "the private /proc cannot be listed (%s)", strerror(errno));
	while ((e = readdir(d)) != NULL)
		if (e->d_name[0] >= '1' && e->d_name[0] <= '9')
			pids++;
	closedir(d);
	if (pids != 1)
		return say(why, n, "the private /proc lists %d processes, not 1: this process is not alone "
		           "in its PID namespace", pids);
	return 0;
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
		/* ⭐ 1.6 (audit split R7): socket families on an ALLOW list — AF_UNIX, AF_INET, AF_INET6 and nothing else (netlink, packet,
		 *    vsock, alg, bluetooth, … ⇒ EAFNOSUPPORT, what a kernel without the family says: glibc's AI_ADDRCONFIG falls back on it).
		 *    `socket` and `socketpair` both take the family as their first argument. */
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_socket, 1, 0),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_socketpair, 0, 6),
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, args[0])),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AF_UNIX, 3, 0),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AF_INET, 2, 0),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AF_INET6, 1, 0),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EAFNOSUPPORT),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
		WALLS_DENY(__NR_io_uring_setup, ENOSYS),
		WALLS_DENY(__NR_io_uring_enter, ENOSYS),
		WALLS_DENY(__NR_io_uring_register, ENOSYS),
		WALLS_DENY(__NR_userfaultfd, EPERM),
		WALLS_DENY(__NR_perf_event_open, EPERM),
		WALLS_DENY(__NR_bpf, EPERM),
		WALLS_DENY(__NR_keyctl, EPERM),
		WALLS_DENY(__NR_add_key, EPERM),
		WALLS_DENY(__NR_request_key, EPERM),
		WALLS_DENY(__NR_ptrace, EPERM),
		/* ⛔ 24 Oct 2026: every network side runs as the same uid — without these
		 *    a hijacked one could read or write another's memory past ptrace. */
		WALLS_DENY(__NR_process_vm_readv, EPERM),
		WALLS_DENY(__NR_process_vm_writev, EPERM),
		WALLS_DENY(__NR_kcmp, EPERM),
		WALLS_DENY(__NR_pidfd_getfd, EPERM),
		/* ioctl: the request is an unsigned int in the kernel — its low word is all of it */
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_ioctl, 0, 5),
		BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, args[1])),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, TIOCSTI, 1, 0),
		BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, TIOCLINUX, 0, 1),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
		BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
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

	/* ⭐ 1.6 (R8 B): born by `walls_fork_pidns()`, so PID 1 of its own PID namespace — a network side that shares the host's
	 *    would read the host's /proc.  No silent fallback. */
	if (getpid() != 1)
		return say(why, why_len, "this process is pid %ld: the network side must be PID 1 of a PID "
		           "namespace of its own (walls_fork_pidns)", (long)getpid());

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
	/* ⭐ 1.6 (R8 B): the /proc of this PID namespace, before the tree goes read-only (it becomes read-only with the rest) */
	if (private_proc(why, why_len) != 0)
		return -1;
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
	/* ⛔ Lane 4's network-side review: writable, but noexec — what a hijacked
	 *    network side writes there it cannot run (it never runs anything). */
	if (set_attr(o->net_state_dir, 0, WALLS_ATTR_NOEXEC, WALLS_ATTR_RDONLY) != 0)
		return say(why, why_len, "making %s writable again failed (%s)",
		           o->net_state_dir, strerror(errno));
	if (set_attr(o->net_run_dir, 0, WALLS_ATTR_NOEXEC, WALLS_ATTR_RDONLY) != 0)
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
	if (!(vs.f_flag & ST_RDONLY) || !(vs.f_flag & ST_NOSUID) || !(vs.f_flag & ST_NODEV))
		return say(why, why_len, "/ is not read-only, nosuid and nodev after mount_setattr "
		           "(flags %#lx)", (unsigned long)vs.f_flag);
	if (statvfs(o->net_state_dir, &vs) != 0)
		return say(why, why_len, "statvfs(%s) after the walls failed (%s)", o->net_state_dir,
		           strerror(errno));
	if (vs.f_flag & ST_RDONLY)
		return say(why, why_len, "%s is not writable after the walls", o->net_state_dir);
	if (!(vs.f_flag & ST_NOEXEC) || !(vs.f_flag & ST_NOSUID) || !(vs.f_flag & ST_NODEV))
		return say(why, why_len, "%s is not noexec, nosuid and nodev after the walls "
		           "(flags %#lx)", o->net_state_dir, (unsigned long)vs.f_flag);
	if (statvfs(o->net_run_dir, &vs) != 0)
		return say(why, why_len, "statvfs(%s) after the walls failed (%s)", o->net_run_dir,
		           strerror(errno));
	if (vs.f_flag & ST_RDONLY)
		return say(why, why_len, "%s is not writable after the walls", o->net_run_dir);
	if (!(vs.f_flag & ST_NOEXEC) || !(vs.f_flag & ST_NOSUID) || !(vs.f_flag & ST_NODEV))
		return say(why, why_len, "%s is not noexec, nosuid and nodev after the walls "
		           "(flags %#lx)", o->net_run_dir, (unsigned long)vs.f_flag);
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

	/* ⛔ 3-bis — a network of its own, still as root (audit split R5 and R6). */
	if (own_network(why, why_len) != 0)
		return -1;

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
	scope_abstract_sockets(); /* before the filter, and after NO_NEW_PRIVS; never fatal */
	if (no_user_namespaces(why, why_len) != 0)
		return -1;
	note("PID 1 of its own PID namespace, /proc of its own; own network namespace (loopback only; the inherited sockets work); tree read-only, nosuid, nodev but %s and %s; private /tmp and /dev; uid/gid %ld/%ld, "
	     "no groups, no capabilities, no_new_privs; RLIMIT_NPROC %d; seccomp: no user "
	     "namespaces, sockets only AF_UNIX/AF_INET/AF_INET6, no io_uring/userfaultfd/perf/bpf/keys/ptrace/TIOCSTI", o->net_state_dir,
	     o->net_run_dir, (long)uid, (long)gid, WALLS_NPROC_MAX);
	return 0;
}
