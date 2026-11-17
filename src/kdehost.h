/* kdehost.h — 1.5.5: THE KDE COMPOSITOR THAT REMOTIX STARTS IS STOPPED WHEN THE REMOTE SESSION IS OVER.
 *
 * ⛔ The problem (`[M]` on the 1.5.4 boxes): on KDE the remote desktop's compositor is the USER unit
 *    `plasma-kwin_wayland.service` (session.c, `write_dropin()`: our drop-in replaces its ExecStart with
 *    `remotix --kwin-nested …`, which starts a screenless labwc and becomes the KWin wrapper).  A user unit lives in the
 *    user manager, outside the logind scope of REMOTIX: when the remote session ends from the outside, when the
 *    user enters locally, or after an update from 1.5.3, the unit stays on — and the user who then logs in KDE at the
 *    computer finds a compositor with no screen already running under that name.
 *
 * ⭐ ONE rule, for every distro: the service is stopped ONLY IF one of the processes of ITS cgroup is recognised as ours:
 *    its command line carries the folder `remotix-kwin-host` (after the exec: `--wayland-display …/remotix-kwin-host/…`) or
 *    the `--kwin-nested` option (before the exec).  Both exist only because REMOTIX wrote them.  A service with the same name
 *    and no mark is a local desktop's: it is SAID and never touched.
 *
 * ⛔ Recognised by the PROCESS, never by name (`comm`) and never with `kill`: the pid is read from /proc together with
 *    the cgroup it sits in (so «the main process of the unit» is a fact, not an inference), re-read just before the
 *    stop, and the stop is `systemctl --user stop <unit>` run as the user — the unit stops with all its cgroup.
 *
 * Where it can run: it only reads /proc (world-readable, no bus), so ROOT can recognise; to STOP it forks and drops to the
 * user's uid (or runs as is if it already is that user: the child).  The network side (uid `remotix`) can do neither and
 * must not call `kdehost_stop()`: in split mode the root side does the periodic sweep (rootside.c).
 *
 * Header only (like reapwait.h): the root side, the single-process server and the child share ONE text. */
#ifndef REMOTIX_KDEHOST_H
#define REMOTIX_KDEHOST_H

#include "log.h"
#include "reapwait.h"

#include <ctype.h>
#include <stdbool.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define KDEHOST_UNIT "plasma-kwin_wayland.service"
#define KDEHOST_MARK "remotix-kwin-host"
#define KDEHOST_OPTION "--kwin-nested"
#define KDEHOST_DROPIN_DIR "plasma-kwin_wayland.service.d"
#define KDEHOST_DROPIN "zz-remotix-monitor.conf"

enum { KDEHOST_NONE = 0, KDEHOST_OURS = 1, KDEHOST_FOREIGN = 2 };

static inline bool kdehost_read(const char *fpath, char *buf, size_t cap)
{
	int fd = open(fpath, O_RDONLY | O_CLOEXEC);
	ssize_t n;

	if (fd < 0)
		return false;
	n = read(fd, buf, cap - 1);
	close(fd);
	if (n < 0)
		return false;
	buf[n] = '\0';
	for (ssize_t i = 0; i < n; i++)
		if (buf[i] == '\0')
			buf[i] = ' '; /* cmdline: NUL-separated */
	return true;
}

/* 0 = this pid is not in the unit's cgroup · 1 = in it and OURS (`how` says why) · 2 = in it, no mark.
 * `uid` receives the owner.  ⛔ Looks at the cgroup (`0::/…/user@UID.service/…/plasma-kwin_wayland.service`), so
 * a process that only SHARES THE NAME of the unit's binary is not mistaken for it. */
static inline int kdehost_classify(pid_t pid, uid_t *uid, char *how, size_t how_n)
{
	char fpath[64], cg[1024], cmd[4096];
	struct stat st;
	const char *u, *line;

	snprintf(fpath, sizeof fpath, "/proc/%d/cgroup", (int)pid);
	if (!kdehost_read(fpath, cg, sizeof cg))
		return 0;
	line = strstr(cg, "0::");
	if (!line)
		return 0;
	u = strstr(line, "/" KDEHOST_UNIT);
	if (!u || !strstr(line, "/user@"))
		return 0;
	u += 1 + strlen(KDEHOST_UNIT);
	if (*u != '\0' && *u != '/' && *u != ' ' && *u != '\n')
		return 0;
	snprintf(fpath, sizeof fpath, "/proc/%d", (int)pid);
	if (stat(fpath, &st) != 0)
		return 0;
	*uid = st.st_uid;
	snprintf(fpath, sizeof fpath, "/proc/%d/cmdline", (int)pid);
	if (!kdehost_read(fpath, cmd, sizeof cmd))
		return 0;
	if (strstr(cmd, KDEHOST_MARK)) {
		snprintf(how, how_n, "the command line of pid %d carries «" KDEHOST_MARK "» and it sits in the cgroup of "
		         KDEHOST_UNIT, (int)pid);
		return 1;
	}
	if (strstr(cmd, KDEHOST_OPTION)) {
		snprintf(how, how_n, "the command line of pid %d carries «" KDEHOST_OPTION "» (REMOTIX's own option, the "
		         "host is still starting) and it sits in the cgroup of " KDEHOST_UNIT, (int)pid);
		return 1;
	}
	return 2;
}

/* What `uid` has in that unit: KDEHOST_OURS (pid, how) · KDEHOST_FOREIGN (processes in the unit and none of them ours) ·
 * KDEHOST_NONE.  /proc is read once. */
static inline int kdehost_look(uid_t uid, pid_t *pid, char *how, size_t how_n)
{
	DIR *d = opendir("/proc");
	struct dirent *e;
	int seen = KDEHOST_NONE;

	if (!d)
		return KDEHOST_NONE;
	while ((e = readdir(d))) {
		uid_t o = 0;
		char h[256];
		pid_t p;
		int c;

		if (!isdigit((unsigned char)e->d_name[0]))
			continue;
		p = (pid_t)atoi(e->d_name);
		c = kdehost_classify(p, &o, h, sizeof h);
		if (!c || o != uid)
			continue;
		if (c == 1) {
			*pid = p;
			snprintf(how, how_n, "%s", h);
			closedir(d);
			return KDEHOST_OURS;
		}
		seen = KDEHOST_FOREIGN;
	}
	closedir(d);
	return seen;
}

/* The users that have a host that is OURS (distinct, at most `cap`).  One pass over /proc. */
static inline int kdehost_users(uid_t *out, int cap)
{
	DIR *d = opendir("/proc");
	struct dirent *e;
	int n = 0;

	if (!d)
		return 0;
	while ((e = readdir(d)) && n < cap) {
		uid_t o = 0;
		char h[256];
		bool dup = false;

		if (!isdigit((unsigned char)e->d_name[0]))
			continue;
		if (kdehost_classify((pid_t)atoi(e->d_name), &o, h, sizeof h) != 1)
			continue;
		for (int i = 0; i < n; i++)
			dup |= out[i] == o;
		if (!dup)
			out[n++] = o;
	}
	closedir(d);
	return n;
}

/* Runs `argv` as `uid` — or, with `rm_file` set, UNLINKS `rm_file` and RMDIRs `rm_dir` as `uid` — in a child that has dropped
 * to that user (root: groups, gid, uid, then a check that root cannot be regained; the user itself: as is).  ⛔ The
 * unlink is done AFTER the drop so that the KERNEL applies the user's permissions: a symlink planted in /run/user/A cannot
 * make root delete B's files.  Everything the child needs is prepared BEFORE the fork: after it only async-signal-safe
 * calls.  Waits at most `ms` (then SIGKILL).  true = it EXITED with status 0 (a signal or any other status is false). */
static inline bool kdehost_spawn(uid_t uid, gid_t gid, char *const argv[], const char *rm_file, const char *rm_dir,
                                 unsigned ms)
{
	char run[64], bus[96], *envp[5];
	sigset_t all;
	pid_t p;
	int st = 0;
	bool done = false;

	snprintf(run, sizeof run, "XDG_RUNTIME_DIR=/run/user/%u", (unsigned)uid);
	snprintf(bus, sizeof bus, "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%u/bus", (unsigned)uid);
	envp[0] = run;
	envp[1] = bus;
	envp[2] = (char *)"PATH=/usr/sbin:/usr/bin:/sbin:/bin";
	envp[3] = (char *)"LANG=C";
	envp[4] = NULL;
	sigfillset(&all);
	p = fork();
	if (p < 0)
		return false;
	if (p == 0) {
		sigprocmask(SIG_UNBLOCK, &all, NULL);
		if (geteuid() != uid) {
			if (geteuid() != 0 || setgroups(0, NULL) != 0 || setresgid(gid, gid, gid) != 0 ||
			    setresuid(uid, uid, uid) != 0)
				_exit(126);
			/* ⛔ the way back must be closed: if root can be regained the drop did not happen */
			if (uid != 0 && (setuid(0) == 0 || setgid(0) == 0))
				_exit(126);
		}
		/* the root side's channel and PAM descriptors stay behind */
		if (syscall(SYS_close_range, 3u, ~0u, 0u) != 0)
			for (int fd = 3; fd < 1024; fd++)
				close(fd);
		if (rm_file) {
			(void)unlink(rm_file);
			if (rm_dir)
				(void)rmdir(rm_dir);
			_exit(0);
		}
		if (chdir("/") != 0)
			_exit(126);
		execve("/usr/bin/systemctl", argv, envp);
		execve("/bin/systemctl", argv, envp);
		_exit(127);
	}
	for (unsigned w = 0; w <= ms; w += 5) {
		pid_t r = waitpid(p, &st, WNOHANG);

		if (r == p) {
			done = true;
			break;
		}
		if (r < 0 && errno != EINTR) {
			done = false;
			st = -1;
			break;
		}
		usleep(5 * 1000);
	}
	if (!done) {
		kill(p, SIGKILL);
		(void)reap_within(p, 500);
		return false;
	}
	return WIFEXITED(st) && WEXITSTATUS(st) == 0;
}

/* attempts per host (user, pid): after KDEHOST_TRIES a line is written once and nothing more, until the pid changes */
#define KDEHOST_TRIES 3
struct kdehost_tally {
	uid_t uid;
	pid_t pid;
	int tries;
};

/*
 * Stops `uid`'s host IF IT IS OURS.  `tag` is the log's channel, `why` the reason (it ends up in the line).
 * Returns 1 stop REQUESTED (the check that it is gone is the next round's: nothing waits here) · 0 nothing to do (none,
 * not ours — said — or the attempts are used up) · -1 it was ours and the request failed.
 * ⛔ Never touches a unit whose processes carry no mark.  After the request our drop-in is removed and the manager
 *    reloaded, so that the next KDE start (a local login included) reads the distribution's own ExecStart.
 * ⭐ The whole call is bounded (~3 s worst case: stop ≤ 1.5 s, unlink ≤ 0.5 s, reload ≤ 1 s): it runs inside the root
 *    side's single-threaded loop.  `--no-block`: systemctl does not wait for the unit to stop.
 */
static inline int kdehost_stop(const char *tag, uid_t uid, const char *why)
{
	static struct kdehost_tally tally[16];
	struct kdehost_tally *t = NULL;
	struct passwd pw, *r = NULL;
	char buf[2048], how[300], how2[300], name[64], dir[160], file[220];
	pid_t pid = 0, pid2 = 0;
	int look;
	gid_t gid = (gid_t)uid;

	if (getpwuid_r(uid, &pw, buf, sizeof buf, &r) == 0 && r) {
		snprintf(name, sizeof name, "%s", r->pw_name);
		gid = r->pw_gid;
	} else {
		snprintf(name, sizeof name, "uid %u", (unsigned)uid);
	}
	look = kdehost_look(uid, &pid, how, sizeof how);
	if (look != KDEHOST_OURS) /* nothing of ours any more: its place in the table is free */
		for (size_t i = 0; i < sizeof tally / sizeof tally[0]; i++)
			if (tally[i].uid == uid) {
				tally[i].tries = 0;
				tally[i].pid = 0;
			}
	if (look == KDEHOST_NONE) {
		log_detail(tag, "1.5.5: «%s» has no " KDEHOST_UNIT " running (%s)", name, why);
		return 0;
	}
	if (look == KDEHOST_FOREIGN) {
		registro_dice(tag, "⭐ 1.5.5: " KDEHOST_UNIT " of «%s» is active but NOT stopped — no process of it carries our mark "
		              "(«" KDEHOST_MARK "» / «" KDEHOST_OPTION "»): not ours, a local desktop's (%s)", name, why);
		return 0;
	}
	/* ⛔ read AGAIN just before the stop: if the service was restarted in between, only a host that is still ours is stopped */
	if (kdehost_look(uid, &pid2, how2, sizeof how2) != KDEHOST_OURS) {
		registro_dice(tag, "⭐ 1.5.5: " KDEHOST_UNIT " of «%s» NOT stopped — the second reading just before the stop no longer "
		              "finds it as ours (%s)", name, why);
		return 0;
	}
	/* the attempts for THIS host (user, pid) */
	for (size_t i = 0; i < sizeof tally / sizeof tally[0]; i++)
		if (tally[i].uid == uid && tally[i].tries > 0) {
			t = &tally[i];
			break;
		}
	if (!t)
		for (size_t i = 0; i < sizeof tally / sizeof tally[0]; i++)
			if (tally[i].tries == 0) {
				t = &tally[i];
				t->uid = uid;
				break;
			}
	if (!t) {
		/* full table: first reuse a place whose user has no host of ours any more */
		for (size_t i = 0; i < sizeof tally / sizeof tally[0] && !t; i++) {
			pid_t other = 0;
			char h[8];

			if (tally[i].tries > 0 && kdehost_look(tally[i].uid, &other, h, sizeof h) != KDEHOST_OURS) {
				t = &tally[i];
				t->uid = uid;
				t->pid = 0;
				t->tries = 0;
			}
		}
	}
	if (!t) {
		/* ⛔ no place: NEVER a stop without the ceiling.  Said at most once every 30 s; the round goes on to the next user */
		static time_t said_at;
		time_t now = time(NULL);

		if (now - said_at >= 30) {
			said_at = now;
			registro_dice(tag, "⛔ 1.5.5: the table of stop attempts is full (%zu hosts that do not go away): «%s» NOT "
			              "tried this round (%s)", sizeof tally / sizeof tally[0], name, why);
		}
		return 0;
	}
	{
		if (t->pid != pid2) {
			t->pid = pid2;
			t->tries = 0;
		}
		if (t->tries > KDEHOST_TRIES)
			return 0;
		if (t->tries == KDEHOST_TRIES) {
			t->tries++;
			registro_dice(tag, "⛔ 1.5.5: " KDEHOST_UNIT " of «%s» (pid %d) is still there after %d stop requests: I stop "
			              "trying until its pid changes (%s)", name, (int)pid2, KDEHOST_TRIES, why);
			return 0;
		}
		t->tries++;
	}
	{
		char *stop[] = { "systemctl", "--user", "--no-block", "stop", (char *)KDEHOST_UNIT, NULL };
		char *reload[] = { "systemctl", "--user", "daemon-reload", NULL };
		bool ok = kdehost_spawn(uid, gid, stop, NULL, NULL, 1500);
		bool had = false, reloaded = false;

		snprintf(dir, sizeof dir, "/run/user/%u/systemd/user.control/" KDEHOST_DROPIN_DIR, (unsigned)uid);
		snprintf(file, sizeof file, "%s/" KDEHOST_DROPIN, dir);
		if (geteuid() == uid) {
			had = unlink(file) == 0;
			(void)rmdir(dir);
		} else {
			struct stat sb;

			had = lstat(file, &sb) == 0; /* only to say it in the log: the removal is the user's */
			(void)kdehost_spawn(uid, gid, NULL, file, dir, 500);
		}
		if (had || ok)
			reloaded = kdehost_spawn(uid, gid, reload, NULL, NULL, 1000);
		registro_dice(tag, "⭐ 1.5.5: " KDEHOST_UNIT " of «%s»: stop %s (pid %d, recognised as ours because %s; reason: %s); "
		              "drop-in %s, daemon-reload %s; whether it is gone is checked at the next round", name,
		              ok ? "REQUESTED" : "⛔ FAILED", (int)pid2, how2, why, had ? "removed" : "already absent",
		              reloaded ? "done" : "not done");
		return ok ? 1 : -1;
	}
}

#endif
