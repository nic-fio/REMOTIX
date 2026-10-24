/*
 * render_grant.c — the card for a stale user manager, without closing
 * anything.  Why, and the measurements: `render_grant.h`.
 *
 * ⚠ It runs in the PARENT, as root, before the `fork` of the child (and at
 *   start-up for the sweep).  It talks to nobody: `/proc`, `/sys/fs/cgroup`,
 *   `/etc/passwd`, `/etc/group`, the ACL of `/dev/dri/renderD*`, and its own
 *   record file.
 */
#include "render_grant.h"
#include "rediscover.h"
#include "log.h"

#include <dirent.h>
#include <endian.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/xattr.h>
#include <unistd.h>

#define LOG_GRANT "child"

#define DRI_DIR "/dev/dri"
#define MAX_NODES 8
#define GRANTS_DIR "/var/lib/remotix"
#define GRANTS_FILE "render-grants"
#define MAX_GRANTS 64

/* ---------------------------------------------------------------------------
 * The render nodes, all of them: one per card, and the machine may have two.
 * --------------------------------------------------------------------------- */
static int render_nodes(char nodes[MAX_NODES][64])
{
	DIR *d = opendir(DRI_DIR);
	struct dirent *e;
	int n = 0;

	if (!d)
		return 0;
	while ((e = readdir(d)) != NULL && n < MAX_NODES) {
		struct stat st;

		if (strncmp(e->d_name, "renderD", 7) != 0)
			continue;
		snprintf(nodes[n], sizeof nodes[n], DRI_DIR "/%.40s", e->d_name);
		if (lstat(nodes[n], &st) == 0 && S_ISCHR(st.st_mode))
			n++;
	}
	closedir(d);
	return n;
}

/* ---------------------------------------------------------------------------
 * 1. IS THE BRIDGE NEEDED?  The user manager's own credentials, read from the
 *    kernel — not the account database, which already says «render».
 * --------------------------------------------------------------------------- */

/* The pid of `systemd --user` for `uid`: the only process of its init.scope.
 * 0 if there is no manager (then pam_systemd will start one with the new
 * groups), -1 if it cannot be read. */
static pid_t manager_pid(uid_t uid)
{
	char path[160];
	FILE *fp;
	long pid = 0;

	snprintf(path, sizeof path,
	         "/sys/fs/cgroup/user.slice/user-%lu.slice/user@%lu.service/init.scope/cgroup.procs",
	         (unsigned long)uid, (unsigned long)uid);
	fp = fopen(path, "re");
	if (!fp)
		return errno == ENOENT ? 0 : -1;
	if (fscanf(fp, "%ld", &pid) != 1)
		pid = 0;
	fclose(fp);
	return (pid_t)pid;
}

/* Its filesystem gid and supplementary groups.  -1 if unreadable or not `uid`'s. */
static int manager_groups(pid_t pid, uid_t uid, gid_t *fsgid, gid_t *v, int cap)
{
	char path[64], line[1024];
	FILE *fp;
	int n = -1;
	bool uid_ok = false;

	snprintf(path, sizeof path, "/proc/%ld/status", (long)pid);
	fp = fopen(path, "re");
	if (!fp)
		return -1;
	while (fgets(line, sizeof line, fp)) {
		unsigned long a, b, c, d;

		if (sscanf(line, "Uid: %lu %lu %lu %lu", &a, &b, &c, &d) == 4)
			uid_ok = a == uid && b == uid && c == uid && d == uid;
		else if (sscanf(line, "Gid: %lu %lu %lu %lu", &a, &b, &c, &d) == 4)
			*fsgid = (gid_t)d;
		else if (strncmp(line, "Groups:", 7) == 0) {
			char *p = line + 7, *end;

			n = 0;
			for (;;) {
				unsigned long g = strtoul(p, &end, 10);

				if (end == p || n >= cap)
					break;
				v[n++] = (gid_t)g;
				p = end;
			}
		}
	}
	fclose(fp);
	return uid_ok ? n : -1;
}

int render_grant_needed(uid_t uid, const char *user)
{
	char nodes[MAX_NODES][64];
	gid_t groups[128], fsgid = (gid_t)-1;
	int nn = render_nodes(nodes);
	int ng;
	pid_t pid;

	if (nn == 0)
		return 0;
	pid = manager_pid(uid);
	if (pid == 0)
		return 0;
	if (pid < 0)
		return -1;
	ng = manager_groups(pid, uid, &fsgid, groups, (int)(sizeof groups / sizeof groups[0]));
	if (ng < 0)
		return -1;
	for (int i = 0; i < nn; i++) {
		struct stat st;
		bool in = false;

		if (stat(nodes[i], &st) != 0)
			continue;
		if ((st.st_mode & 006) == 006)
			continue; /* open to everyone: nothing to bridge */
		in = st.st_gid == fsgid;
		for (int k = 0; k < ng && !in; k++)
			in = groups[k] == st.st_gid;
		if (!in) {
			log_says_of(LOG_GRANT, user,
			            "⚠ the user manager of «%s» (pid %ld) is ALIVE and was born "
			            "without the group of %s (gid %ld): the desktop it starts would "
			            "draw in software",
			            user, (long)pid, nodes[i], (long)st.st_gid);
			return 1;
		}
	}
	return 0;
}

/* ---------------------------------------------------------------------------
 * 2. IS THE PRIMARY GROUP PROVABLY THE USER'S ALONE?  Asked of the local files
 *    only: NSS cannot prove that nobody else has a gid (enumeration of network
 *    accounts is usually off), and «I did not see anyone» is not a proof.
 * --------------------------------------------------------------------------- */
/* The first `n` colon-separated fields of a line of /etc/group or /etc/passwd,
 * empty ones kept (`strsep`, not `strtok`); the last one runs to the end of the
 * line.  Returns how many were found. */
static int fields(char *line, char **f, int n)
{
	int k = 0;

	line[strcspn(line, "\n")] = '\0';
	while (k < n - 1 && line && (f[k] = strsep(&line, ":")) != NULL)
		k++;
	if (line && k == n - 1)
		f[k++] = line;
	for (int i = k; i < n; i++)
		f[i] = NULL;
	return k;
}

/* Is the decimal text `s` exactly the id `id`? */
static bool same_id(const char *s, unsigned long id)
{
	char *end;
	unsigned long v;

	if (!s || !*s)
		return false;
	errno = 0;
	v = strtoul(s, &end, 10);
	return errno == 0 && *end == '\0' && v == id;
}

static bool group_is_private(const char *user, gid_t gid, char *why, size_t how_much)
{
	char line[4096];
	FILE *fp;
	int found = 0;
	bool ok = true;

	if (gid == 0) {
		snprintf(why, how_much, "the primary group is gid 0");
		return false;
	}
	fp = fopen("/etc/group", "re");
	if (!fp) {
		snprintf(why, how_much, "/etc/group: %s", strerror(errno));
		return false;
	}
	while (ok && fgets(line, sizeof line, fp)) {
		char *f[4];

		if (fields(line, f, 4) < 3 || !same_id(f[2], gid))
			continue;
		found++;
		if (strcmp(f[0], user) != 0) {
			snprintf(why, how_much, "gid %ld is the group «%s», not «%s»", (long)gid, f[0], user);
			ok = false;
		}
		for (char *rest = f[3], *m; ok && rest && (m = strsep(&rest, ",")) != NULL;) {
			if (*m && strcmp(m, user) != 0) {
				snprintf(why, how_much, "the group «%s» has another member, «%s»", f[0], m);
				ok = false;
			}
		}
	}
	fclose(fp);
	if (!ok)
		return false;
	if (found != 1) {
		snprintf(why, how_much,
		         found ? "gid %ld appears %d times in /etc/group"
		               : "gid %ld is not in /etc/group (a network account?): its being private cannot be proved",
		         (long)gid, found);
		return false;
	}
	fp = fopen("/etc/passwd", "re");
	if (!fp) {
		snprintf(why, how_much, "/etc/passwd: %s", strerror(errno));
		return false;
	}
	while (ok && fgets(line, sizeof line, fp)) {
		char *f[5];

		if (fields(line, f, 5) == 5 && same_id(f[3], gid) && strcmp(f[0], user) != 0) {
			snprintf(why, how_much, "the account «%s» too has gid %ld as primary group", f[0],
			         (long)gid);
			ok = false;
		}
	}
	fclose(fp);
	return ok;
}

/* ---------------------------------------------------------------------------
 * 3. THE ACL, WRITTEN DIRECTLY — the `system.posix_acl_access` attribute, so
 *    that the package needs neither `setfacl` nor libacl.  Format: a 4-byte
 *    version (2), then 8-byte entries {tag, perm, id}, little endian, sorted by
 *    tag and id; the mask is the union of the group class.
 * --------------------------------------------------------------------------- */
#define ACL_XATTR "system.posix_acl_access"
#define ACL_VERSION 2
#define MAX_ENTRIES 64
#define ACL_UNDEFINED 0xFFFFFFFFu

enum { T_USER_OBJ = 0x01, T_USER = 0x02, T_GROUP_OBJ = 0x04, T_GROUP = 0x08,
       T_MASK = 0x10, T_OTHER = 0x20 };

struct acl_entry {
	uint16_t tag, perm;
	uint32_t id;
};

/* The entries of `path`; from its mode if it has no ACL.  -1 with errno. */
static int acl_read(const char *path, struct acl_entry *v)
{
	unsigned char buf[4 + 8 * MAX_ENTRIES];
	ssize_t n = lgetxattr(path, ACL_XATTR, buf, sizeof buf);
	uint32_t version;
	int k = 0;

	if (n < 0) {
		struct stat st;

		if (errno != ENODATA || lstat(path, &st) != 0)
			return -1;
		v[0] = (struct acl_entry){ T_USER_OBJ, (st.st_mode >> 6) & 7, ACL_UNDEFINED };
		v[1] = (struct acl_entry){ T_GROUP_OBJ, (st.st_mode >> 3) & 7, ACL_UNDEFINED };
		v[2] = (struct acl_entry){ T_OTHER, st.st_mode & 7, ACL_UNDEFINED };
		return 3;
	}
	if (n < 4) {
		errno = EINVAL;
		return -1;
	}
	memcpy(&version, buf, 4);
	if ((n - 4) % 8 != 0 || le32toh(version) != ACL_VERSION) {
		errno = EINVAL;
		return -1;
	}
	for (ssize_t off = 4; off < n; off += 8, k++) {
		uint16_t t, p;
		uint32_t id;

		memcpy(&t, buf + off, 2);
		memcpy(&p, buf + off + 2, 2);
		memcpy(&id, buf + off + 4, 4);
		v[k] = (struct acl_entry){ le16toh(t), le16toh(p), le32toh(id) };
	}
	return k;
}

static int acl_order(const void *a, const void *b)
{
	const struct acl_entry *x = a, *y = b;

	if (x->tag != y->tag)
		return x->tag < y->tag ? -1 : 1;
	return x->id < y->id ? -1 : x->id > y->id;
}

/* The mask again, then sorted and written. */
static int acl_write(const char *path, struct acl_entry *v, int n)
{
	unsigned char buf[4 + 8 * MAX_ENTRIES];
	uint32_t version = htole32(ACL_VERSION);
	uint16_t unite = 0;
	int mask = -1;
	bool named = false;

	for (int i = 0; i < n; i++) {
		if (v[i].tag == T_GROUP_OBJ || v[i].tag == T_USER || v[i].tag == T_GROUP)
			unite |= v[i].perm;
		if (v[i].tag == T_USER || v[i].tag == T_GROUP)
			named = true;
		if (v[i].tag == T_MASK)
			mask = i;
	}
	if (mask < 0 && named && n < MAX_ENTRIES)
		v[mask = n++] = (struct acl_entry){ T_MASK, 0, ACL_UNDEFINED };
	if (mask >= 0)
		v[mask].perm = unite;
	qsort(v, (size_t)n, sizeof *v, acl_order);
	memcpy(buf, &version, 4);
	for (int i = 0; i < n; i++) {
		uint16_t t = htole16(v[i].tag), p = htole16(v[i].perm);
		uint32_t id = htole32(v[i].id);

		memcpy(buf + 4 + 8 * i, &t, 2);
		memcpy(buf + 4 + 8 * i + 2, &p, 2);
		memcpy(buf + 4 + 8 * i + 4, &id, 4);
	}
	return lsetxattr(path, ACL_XATTR, buf, 4 + 8 * (size_t)n, 0);
}

/* 1 the node already has an entry for `gid` · 0 no · -1 unreadable. */
static int acl_has_group(const char *path, gid_t gid)
{
	struct acl_entry v[MAX_ENTRIES];
	int n = acl_read(path, v);

	if (n < 0)
		return -1;
	for (int i = 0; i < n; i++)
		if (v[i].tag == T_GROUP && v[i].id == gid)
			return 1;
	return 0;
}

static int acl_add_group(const char *path, gid_t gid)
{
	struct acl_entry v[MAX_ENTRIES];
	int n = acl_read(path, v);

	if (n < 0 || n >= MAX_ENTRIES - 1)
		return -1;
	v[n++] = (struct acl_entry){ T_GROUP, 6, gid };
	return acl_write(path, v, n);
}

static int acl_remove_group(const char *path, gid_t gid)
{
	struct acl_entry v[MAX_ENTRIES];
	int n = acl_read(path, v), k = 0;

	if (n < 0)
		return -1;
	for (int i = 0; i < n; i++)
		if (!(v[i].tag == T_GROUP && v[i].id == gid))
			v[k++] = v[i];
	if (k == n)
		return 0;
	return acl_write(path, v, k);
}

/* ---------------------------------------------------------------------------
 * 4. THE RECORD — what REMOTIX granted, so that a crash or a power cut does
 *    not leave a grant behind.  `[M]` 13 Oct 2026: an ACL outlives the account
 *    (`userdel` left `group:1001:rw-`), and the next account would inherit it.
 *    One line per grant: «uid gid user».  Rewritten whole, through a temporary
 *    file and `rename`.
 * --------------------------------------------------------------------------- */
struct grant {
	uid_t uid;
	gid_t gid;
	char user[257];
};

static int grants_folder(void)
{
	struct stat st;
	int dfd;

	if (mkdir(GRANTS_DIR, 0700) != 0 && errno != EEXIST)
		return -1;
	dfd = open(GRANTS_DIR, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
	if (dfd < 0)
		return -1;
	if (fstat(dfd, &st) != 0 || st.st_uid != 0 || (st.st_mode & 022)) {
		close(dfd);
		errno = EPERM;
		return -1;
	}
	return dfd;
}

static int grants_load(struct grant *v)
{
	int dfd = grants_folder(), fd, n = 0;
	char line[400];
	FILE *fp;

	if (dfd < 0)
		return -1;
	fd = openat(dfd, GRANTS_FILE, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
	close(dfd);
	if (fd < 0)
		return errno == ENOENT ? 0 : -1;
	fp = fdopen(fd, "r");
	if (!fp) {
		close(fd);
		return -1;
	}
	while (n < MAX_GRANTS && fgets(line, sizeof line, fp)) {
		unsigned long u, g;
		char name[257];

		if (sscanf(line, "%lu %lu %256s", &u, &g, name) == 3) {
			v[n].uid = (uid_t)u;
			v[n].gid = (gid_t)g;
			snprintf(v[n].user, sizeof v[n].user, "%s", name);
			n++;
		}
	}
	fclose(fp);
	return n;
}

static int grants_save(const struct grant *v, int n)
{
	int dfd = grants_folder(), fd;
	FILE *fp;
	bool ok;

	if (dfd < 0)
		return -1;
	fd = openat(dfd, GRANTS_FILE ".new", O_WRONLY | O_CREAT | O_TRUNC | O_NOFOLLOW | O_CLOEXEC, 0600);
	if (fd < 0) {
		close(dfd);
		return -1;
	}
	fp = fdopen(fd, "w");
	if (!fp) {
		close(fd);
		close(dfd);
		return -1;
	}
	for (int i = 0; i < n; i++)
		fprintf(fp, "%lu %lu %s\n", (unsigned long)v[i].uid, (unsigned long)v[i].gid, v[i].user);
	ok = fflush(fp) == 0 && fsync(fd) == 0;
	ok = fclose(fp) == 0 && ok;
	ok = ok && renameat(dfd, GRANTS_FILE ".new", dfd, GRANTS_FILE) == 0;
	if (ok)
		(void)fsync(dfd);
	close(dfd);
	return ok ? 0 : -1;
}

static int grants_find(const struct grant *v, int n, uid_t uid, gid_t gid)
{
	for (int i = 0; i < n; i++)
		if (v[i].uid == uid && v[i].gid == gid)
			return i;
	return -1;
}

/* ---------------------------------------------------------------------------
 * The three entry points.
 * --------------------------------------------------------------------------- */
bool render_grant_add(const char *user, uid_t uid, gid_t gid)
{
	char nodes[MAX_NODES][64];
	char why[256] = "";
	struct grant v[MAX_GRANTS];
	int nn, ng, mine, added = 0, theirs = 0;

	if (!group_is_private(user, gid, why, sizeof why)) {
		log_says_of(LOG_GRANT, user,
		            "⚠ NO card grant for «%s»: %s.  ⇒ The desktop is born anyway and draws "
		            "in SOFTWARE until the user manager is born again (the user leaves "
		            "every session); nothing is closed",
		            user, why);
		return false;
	}
	nn = render_nodes(nodes);
	ng = grants_load(v);
	if (ng < 0) {
		log_says_of(LOG_GRANT, user,
		            "⛔ NO card grant for «%s»: %s/%s cannot be read (%s), and a grant that "
		            "is not recorded could not be taken back",
		            user, GRANTS_DIR, GRANTS_FILE, strerror(errno));
		return false;
	}
	mine = grants_find(v, ng, uid, gid);
	/* ⛔ ALL OR NOTHING (review of 24 Oct 2026, decided by the project lead): if even ONE
	 *    render node already carries an entry for this gid that is not ours, the
	 *    administrator has put it, and nothing is granted on any node.  Otherwise a
	 *    machine with two cards would be left half granted, and the removal at the end of
	 *    the desktop (which takes the gid out of EVERY node) would take the
	 *    administrator's entry too.  "The administrator's: never claimed, never removed." */
	if (mine < 0) {
		for (int i = 0; i < nn; i++)
			if (acl_has_group(nodes[i], gid) > 0)
				theirs++;
		if (theirs) {
			log_says_of(LOG_GRANT, user,
			            "⭐ NO card grant for «%s»: %d render node(s) already have an entry for "
			            "its group (gid %ld) that REMOTIX did not put.  Left as it is, nothing "
			            "added on any node and nothing will be removed; the desktop is born "
			            "anyway",
			            user, theirs, (long)gid);
			return false;
		}
	}
	for (int i = 0; i < nn; i++) {
		int has = acl_has_group(nodes[i], gid);

		if (has > 0)
			continue; /* ours, from an earlier line of the record */
		if (has == 0 && acl_add_group(nodes[i], gid) == 0) {
			added++;
			continue;
		}
		log_says_of(LOG_GRANT, user, "⛔ the card grant on %s for gid %ld did not work: %s",
		            nodes[i], (long)gid, strerror(errno));
	}
	if (!added && mine < 0)
		return false;
	if (mine < 0 && ng < MAX_GRANTS) {
		v[ng].uid = uid;
		v[ng].gid = gid;
		snprintf(v[ng].user, sizeof v[ng].user, "%s", user);
		ng++;
		if (grants_save(v, ng) != 0) {
			log_says_of(LOG_GRANT, user,
			            "⛔ the card grant for «%s» could not be recorded (%s): taken back",
			            user, strerror(errno));
			for (int i = 0; i < nn; i++)
				(void)acl_remove_group(nodes[i], gid);
			return false;
		}
	}
	log_says_of(LOG_GRANT, user,
	            "⭐ CARD GRANT: «%s»'s private group (gid %ld) may open %d render node(s) "
	            "(%d added now) — its stale user manager draws on the card, and NOTHING "
	            "is closed.  Removed when the desktop ends (%s/%s)",
	            user, (long)gid, nn, added, GRANTS_DIR, GRANTS_FILE);
	return true;
}

void render_grant_remove(const char *user, uid_t uid, gid_t gid)
{
	char nodes[MAX_NODES][64];
	struct grant v[MAX_GRANTS];
	int nn = render_nodes(nodes);
	int ng = grants_load(v);
	int at = ng > 0 ? grants_find(v, ng, uid, gid) : -1;

	for (int i = 0; i < nn; i++)
		if (acl_remove_group(nodes[i], gid) != 0)
			log_says_of(LOG_GRANT, user, "⛔ the card grant on %s for gid %ld was NOT removed: %s",
			            nodes[i], (long)gid, strerror(errno));
	if (at >= 0) {
		v[at] = v[--ng];
		if (grants_save(v, ng) != 0)
			log_says_of(LOG_GRANT, user,
			            "⚠ the card grant of «%s» is removed, but its line stays in %s/%s (%s): "
			            "the next start-up will try again",
			            user, GRANTS_DIR, GRANTS_FILE, strerror(errno));
	}
	log_says_of(LOG_GRANT, user, "⭐ card grant of «%s» (gid %ld) REMOVED: the desktop has ended",
	            user, (long)gid);
}

/* ⭐ What the sweep does and does NOT do (review of 24 Oct 2026).  It runs at start-up and
 *   takes back a grant only when no REMOTIX desktop of that user is alive.  A desktop that
 *   SURVIVED the shutdown of the service is alive (`children_turn_off()` deliberately leaves
 *   its ACL in place): its grant is KEPT here, without a child, and the same sweep takes it
 *   back at a later start when the desktop is gone.  When logind cannot tell, it is kept too.
 *   The uninstaller removes whatever is still recorded (`remove-render-grants`). */
void render_grant_sweep(void)
{
	char nodes[MAX_NODES][64];
	struct grant v[MAX_GRANTS];
	int nn = render_nodes(nodes);
	int ng = grants_load(v);
	int k = 0;

	if (ng <= 0)
		return;
	for (int i = 0; i < ng; i++) {
		int alive = rediscover_alive(v[i].uid, NULL);

		if (alive != 0) {
			log_says_of(LOG_GRANT, v[i].user,
			            "⭐ card grant of «%s» (gid %ld) KEPT at start-up: %s",
			            v[i].user, (long)v[i].gid,
			            alive > 0 ? "its REMOTIX desktop is alive"
			                      : "logind does not say whether its desktop is alive");
			v[k++] = v[i];
			continue;
		}
		for (int j = 0; j < nn; j++)
			(void)acl_remove_group(nodes[j], v[i].gid);
		log_says_of(LOG_GRANT, v[i].user,
		            "⭐ card grant of «%s» (gid %ld) left by a previous run REMOVED: no "
		            "REMOTIX desktop of it is alive",
		            v[i].user, (long)v[i].gid);
	}
	if (k != ng && grants_save(v, k) != 0)
		registro_dice(LOG_GRANT, "⚠ %s/%s could not be rewritten after the sweep: %s",
		              GRANTS_DIR, GRANTS_FILE, strerror(errno));
}
