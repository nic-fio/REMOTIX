/*
 * ritrovo.c — live REMOTIX desktops that no child holds.
 *
 * The why and the criterion are in `ritrovo.h`, which is read first.  Here
 * there is only the how.
 */
#include "ritrovo.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define LOGIND_NAME "org.freedesktop.login1"
#define LOGIND_PATH "/org/freedesktop/login1"
#define IFACE_MANAGER "org.freedesktop.login1.Manager"
#define IFACE_SESSION "org.freedesktop.login1.Session"
/* ⚠ The same ceiling as `sentinella.c`, and for the same reason: the question
 *   leaves from the loop that delivers the frames. */
#define WAIT_MS 300
/* How many `remotix` sessions are looked at in one go.  ⚠ Every reattach
 * leaves one more with a dead leader (`[M]` T2, §5.2 point b): 256 is ample. */
#define MAX_CANDIDATES 256

struct candidate_entry {
	uid_t uid;
	char id[32];
	char scope[128];
	char user[257];
};

/* The content of a small /proc file, terminated with '\0'.  -1 if it is missing. */
static ssize_t read_small(const char *fpath, char *buf, size_t cap)
{
	int fd = open(fpath, O_RDONLY | O_CLOEXEC);
	ssize_t n;

	if (fd < 0)
		return -1;
	n = read(fd, buf, cap - 1);
	close(fd);
	if (n < 0)
		return -1;
	buf[n] = '\0';
	return n;
}

/* The unified cgroup (line `0::`) of the process, without the `\n`.  false if it
 * cannot be read (process died meanwhile: the normal /proc race). */
static bool cgroup_di(pid_t pid, char *dove, size_t cap)
{
	char fpath[64], buf[2048];
	char *r;

	snprintf(fpath, sizeof fpath, "/proc/%ld/cgroup", (long)pid);
	if (read_small(fpath, buf, sizeof buf) < 0)
		return false;
	for (r = buf; r && *r; r = strchr(r, '\n') ? strchr(r, '\n') + 1 : NULL) {
		if (strncmp(r, "0::", 3) == 0) {
			size_t n = strcspn(r + 3, "\n");

			if (n >= cap)
				return false;
			memcpy(dove, r + 3, n);
			dove[n] = '\0';
			return true;
		}
	}
	return false;
}

static const char *last_piece(const char *cg)
{
	const char *u = strrchr(cg, '/');
	return u ? u + 1 : cg;
}

/* The logind sessions with the PAM service `remotix`.  -1 if logind does not answer. */
static int candidate(struct candidate_entry *v, int cap, char *why, size_t how_much)
{
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GDBusConnection) bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &mistake);
	g_autoptr(GVariant) listing = NULL;
	g_autoptr(GVariantIter) it = NULL;
	const char *id, *name, *seat_id, *fpath;
	guint32 uid;
	int n = 0;

	if (!bus) {
		snprintf(why, how_much, "system bus: %s",
		         mistake ? mistake->message : "no reason given");
		return -1;
	}
	listing = g_dbus_connection_call_sync(bus, LOGIND_NAME, LOGIND_PATH, IFACE_MANAGER,
	                                     "ListSessions", NULL, G_VARIANT_TYPE("(a(susso))"),
	                                     G_DBUS_CALL_FLAGS_NONE, WAIT_MS, NULL, &mistake);
	if (!listing) {
		snprintf(why, how_much, "logind ListSessions: %s",
		         mistake ? mistake->message : "no reason given");
		return -1;
	}
	g_variant_get(listing, "(a(susso))", &it);
	while (g_variant_iter_next(it, "(&su&s&s&o)", &id, &uid, &name, &seat_id, &fpath)) {
		g_autoptr(GVariant) r = NULL;
		g_autoptr(GVariant) prop = NULL;
		g_autoptr(GVariant) v_serv = NULL;
		g_autoptr(GVariant) v_scope = NULL;

		if (n >= cap)
			break;
		r = g_dbus_connection_call_sync(bus, LOGIND_NAME, fpath,
		                                "org.freedesktop.DBus.Properties", "GetAll",
		                                g_variant_new("(s)", IFACE_SESSION),
		                                G_VARIANT_TYPE("(a{sv})"), G_DBUS_CALL_FLAGS_NONE,
		                                WAIT_MS, NULL, NULL);
		/* ⚠ Gone between the list and the question: the normal logind race. */
		if (!r)
			continue;
		prop = g_variant_get_child_value(r, 0);
		v_serv = g_variant_lookup_value(prop, "Service", G_VARIANT_TYPE_STRING);
		v_scope = g_variant_lookup_value(prop, "Scope", G_VARIANT_TYPE_STRING);
		if (!v_serv || !v_scope ||
		    strcmp(g_variant_get_string(v_serv, NULL), FOUND_AGAIN_PAM_SERVICE) != 0 ||
		    !g_variant_get_string(v_scope, NULL)[0])
			continue;
		v[n].uid = (uid_t)uid;
		snprintf(v[n].id, sizeof v[n].id, "%s", id);
		snprintf(v[n].scope, sizeof v[n].scope, "%s", g_variant_get_string(v_scope, NULL));
		snprintf(v[n].user, sizeof v[n].user, "%s", name);
		n++;
	}
	return n;
}

/* ⭐ The heart: a single pass over /proc for all the candidates.  `solo_uid`
 * (if not (uid_t)-1) restricts to one user. */
static int search(FindingAgainDesktop *v, int cap, uid_t solo_uid, char *why, size_t how_much)
{
	struct candidate_entry *c = calloc(MAX_CANDIDATES, sizeof *c);
	int nc, matches = 0;
	DIR *proc;
	struct dirent *e;

	if (!c) {
		snprintf(why, how_much, "out of memory");
		return -1;
	}
	nc = candidate(c, MAX_CANDIDATES, why, how_much);
	if (nc <= 0) {
		free(c);
		return nc;
	}
	proc = opendir("/proc");
	if (!proc) {
		snprintf(why, how_much, "/proc: %s", strerror(errno));
		free(c);
		return -1;
	}
	while ((e = readdir(proc)) != NULL) {
		char fpath[64], stat_buf[1024], cg[1024], cg_padre[1024];
		const char *is_closed;
		long pid, ppid = 0, pgrp = 0, sid = 0;
		char state;
		struct stat st;
		int which = -1;

		if (e->d_name[0] < '1' || e->d_name[0] > '9')
			continue;
		pid = strtol(e->d_name, NULL, 10);
		snprintf(fpath, sizeof fpath, "/proc/%ld/stat", pid);
		if (read_small(fpath, stat_buf, sizeof stat_buf) < 0)
			continue;
		/* ⚠ The name is in parentheses and may contain some: start from the LAST one. */
		is_closed = strrchr(stat_buf, ')');
		if (!is_closed || sscanf(is_closed + 1, " %c %ld %ld %ld", &state, &ppid, &pgrp, &sid) != 4)
			continue;
		/* 1. leader of its own process session — the setsid signature */
		if (sid != pid || state == 'Z')
			continue;
		snprintf(fpath, sizeof fpath, "/proc/%ld", pid);
		if (stat(fpath, &st) != 0 || st.st_uid == 0)
			continue;
		if (solo_uid != (uid_t)-1 && st.st_uid != solo_uid)
			continue;
		/* 2. inside the scope of a `remotix` session of the same user */
		if (!cgroup_di((pid_t)pid, cg, sizeof cg))
			continue;
		for (int i = 0; i < nc; i++)
			if (c[i].uid == st.st_uid && strcmp(last_piece(cg), c[i].scope) == 0) {
				which = i;
				break;
			}
		if (which < 0)
			continue;
		/* 3. and the parent OUTSIDE that scope: orphan of `setsid --fork`, not the
		 *    shell of a terminal opened in the desktop */
		if (ppid > 0 && cgroup_di((pid_t)ppid, cg_padre, sizeof cg_padre) &&
		    strcmp(cg_padre, cg) == 0)
			continue;
		/* one per user: the first found; the others are only counted */
		{
			int already = -1;

			for (int k = 0; k < matches; k++)
				if (v[k].uid == st.st_uid)
					already = k;
			if (already >= 0 || matches >= cap)
				continue;
			memset(&v[matches], 0, sizeof v[matches]);
			snprintf(v[matches].user, sizeof v[matches].user, "%s", c[which].user);
			v[matches].uid = st.st_uid;
			snprintf(v[matches].session, sizeof v[matches].session, "%s", c[which].id);
			v[matches].stage = (pid_t)pid;
			{
				const char *is_open = strchr(stat_buf, '(');
				size_t n = is_open ? (size_t)(is_closed - is_open - 1) : 0;

				if (n >= sizeof v[matches].comm)
					n = sizeof v[matches].comm - 1;
				if (is_open)
					memcpy(v[matches].comm, is_open + 1, n);
				v[matches].comm[n] = '\0';
			}
			matches++;
		}
	}
	closedir(proc);
	for (int k = 0; k < matches; k++)
		for (int i = 0; i < nc; i++)
			if (c[i].uid == v[k].uid)
				v[k].sessions++;
	free(c);
	return matches;
}

int finding_again_search(FindingAgainDesktop *v, int cap, char *why, size_t how_much)
{
	if (why && how_much)
		why[0] = '\0';
	if (!v || cap <= 0)
		return 0;
	return search(v, cap, (uid_t)-1, why, how_much);
}

int finding_again_alive(uid_t uid, FindingAgainDesktop *d)
{
	FindingAgainDesktop uno;
	char why[256] = "";
	int n = search(&uno, 1, uid, why, sizeof why);

	if (n < 0)
		return -1;
	if (n > 0 && d)
		*d = uno;
	return n > 0 ? 1 : 0;
}
