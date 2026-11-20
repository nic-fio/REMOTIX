/* remotix-local-login — «a LOCAL graphical login closes the user's remote desktop FIRST» (DECISIONS-11 §11.57, 18 Nov 2026).
 *
 * Called by PAM (`pam_exec.so`, a line that `pam-auth-update` puts in /etc/pam.d/common-session from
 * /usr/share/pam-configs/remotix) every time ANY service opens or closes a session.  It runs as root, inside the
 * login's own PAM stack, and the login waits for it: that is the point.  GNOME's login screen holds a local login
 * while the same user has another graphical session; SDDM and LightDM do not, and the local desktop starts on the
 * user manager and bus the remote one is still using (KDE and XFCE: back to the login screen).  This program is the
 * hold, the same for every desktop and display manager.
 *
 * WHAT IT DOES: for a session that is graphical, on a seat, of class «user» — the sentinel's own rule for «local» —
 * it leaves a request /run/remotix/prelocal/<uid> and waits until the root side removes it (the user's REMOTIX
 * desktop is completely closed, or there was none), LOCAL_CEIL_MS at most.
 *
 * ⛔ IT NEVER MAKES A LOGIN FAIL: every path returns 0, the PAM line is `optional`, and the wait has a ceiling.
 * ⛔ IT NEVER WAITS FOR NOBODY: the root side holds an exclusive lock on prelocal/.lock for as long as it lives;
 *    if the lock can be taken, the service is not running and this returns at once.
 * ⛔ It decides nothing about any session: it names a uid, and the root side reads logind itself (rootside.c, «PL»).
 *
 * The environment is PAM's (`pam_exec` passes PAM_* and the PAM environment, nothing else): XDG_SEAT,
 * XDG_SESSION_CLASS and XDG_SESSION_TYPE are put there by `pam_systemd` (systemd 257, pam_systemd.c:
 * `update_environment()`), which runs before this line (Priority 0 against our -1), and by the display managers.
 * No XDG_SEAT ⇒ not a local login for us ⇒ nothing is done (ssh, cron, a text console before pam_systemd, REMOTIX). */
#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <errno.h>
#include <fcntl.h>
#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#define LOCAL_DIR     "/run/remotix/prelocal"   /* rootside.c: PL_DIR — root:root 0700, made by the root side */
#define LOCAL_LOCK    ".lock"                   /* rootside.c: PL_LOCK */
#define LOCAL_CEIL_MS 25000                     /* above the root side's own ceiling (PL_CEIL_MS, 20 s) */
#define LOCAL_STEP_MS 50

static int dirfd_ = -1;
static char name_[24];

static void leave(int sig)
{
	(void)sig;
	if (dirfd_ >= 0 && name_[0])
		(void)unlinkat(dirfd_, name_, 0);
	_exit(0);
}

static const char *env(const char *k)
{
	const char *v = getenv(k);

	return v ? v : "";
}

/* Is the root side there?  It holds LOCK_EX on the lock file: a shared lock that can be taken means nobody holds it. */
static int nobody_home(int lockfd)
{
	if (flock(lockfd, LOCK_SH | LOCK_NB) == 0) {
		(void)flock(lockfd, LOCK_UN);
		return 1;
	}
	return errno != EWOULDBLOCK;   /* any other error: do not wait on what cannot be read */
}

int main(void)
{
	const char *type = env("PAM_TYPE"), *service = env("PAM_SERVICE"), *user = env("PAM_USER");
	const char *seat = env("XDG_SEAT"), *class = env("XDG_SESSION_CLASS"), *kind = env("XDG_SESSION_TYPE");
	struct timespec step = { 0, LOCAL_STEP_MS * 1000000L };
	struct sigaction sa;
	struct passwd *pw;
	struct stat st;
	int lockfd, fd;

	/* 1. is this the opening of a LOCAL GRAPHICAL session of a person?  Anything else: not ours, at once. */
	if (strcmp(type, "open_session") != 0 || !user[0] || !seat[0])
		return 0;
	if (strcmp(service, "remotix") == 0)                       /* our own PAM service (seatless anyway) */
		return 0;
	if (class[0] && strcmp(class, "user") != 0)               /* greeter, background, manager, … */
		return 0;
	if (kind[0] && strcmp(kind, "wayland") != 0 && strcmp(kind, "x11") != 0 && strcmp(kind, "mir") != 0)
		return 0;                                             /* tty, unspecified, web */
	if (geteuid() != 0)
		return 0;
	pw = getpwnam(user);
	if (!pw || pw->pw_uid == 0)                                /* root has no REMOTIX desktop (denied-users) */
		return 0;

	/* 2. is the root side there?  The directory is its own (root, not writable by others) and so is the lock. */
	dirfd_ = open(LOCAL_DIR, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
	if (dirfd_ < 0 || fstat(dirfd_, &st) != 0 || st.st_uid != 0 || (st.st_mode & 022))
		return 0;
	lockfd = openat(dirfd_, LOCAL_LOCK, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
	if (lockfd < 0 || nobody_home(lockfd))
		return 0;

	/* 3. the request: an empty file named by the uid.  Removed by the root side when nothing of ours is left for
	 *    that uid; removed here if we stop waiting, whatever the reason. */
	snprintf(name_, sizeof name_, "%lu", (unsigned long)pw->pw_uid);
	memset(&sa, 0, sizeof sa);
	sa.sa_handler = leave;
	sigaction(SIGTERM, &sa, NULL);
	sigaction(SIGINT, &sa, NULL);
	sigaction(SIGHUP, &sa, NULL);
	fd = openat(dirfd_, name_, O_WRONLY | O_CREAT | O_NOFOLLOW | O_CLOEXEC, 0600);
	if (fd < 0) {
		name_[0] = 0;
		return 0;
	}
	close(fd);

	/* 4. the wait */
	for (int waited = 0; waited < LOCAL_CEIL_MS; waited += LOCAL_STEP_MS) {
		struct timespec first = { 0, 5 * 1000000L };

		/* the usual answer («no remote desktop of this user») comes in a millisecond or two: the first look is early */
		(void)nanosleep(waited ? &step : &first, NULL);
		if (faccessat(dirfd_, name_, F_OK, AT_SYMLINK_NOFOLLOW) != 0)
			return 0;                                         /* answered: the login goes on */
		if (waited % 500 == 0 && nobody_home(lockfd))
			break;                                            /* the service stopped meanwhile */
	}
	(void)unlinkat(dirfd_, name_, 0);
	return 0;
}
