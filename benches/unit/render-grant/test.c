/*
 * test.c — unit test of src/render_grant.c: the ACL that lets a stale user manager open /dev/dri/renderD* (render_grant.h).
 * The REAL render_grant.c is #included (never modified).  Everything it touches outside itself is interposed with macros, as
 * in benches/unit/evict/test_orphan.c:
 *   /dev/dri             opendir/readdir/closedir/lstat → a table of virtual nodes (char devices, a symlink, a regular file:
 *                        a container cannot mknod); the ACL of each node lives in the table (lgetxattr/lsetxattr,
 *                        system.posix_acl_access, with a count of the writes per node);
 *   /etc/group, /etc/passwd   fopen → files the test writes in a mkdtemp directory;
 *   /var/lib/remotix     mkdir/open → a subdirectory of the same mkdtemp directory (fstat answers uid 0), so the
 *                        render-grants file is the real code writing a real file.
 * The log is benches/fuzz/rcp-msg/stubs_log.c; anything else reached (rediscover_alive: the sweep is not tested here) TRAPS.
 *
 * ⛔ What it nails down (review of 24 Oct 2026):
 *   (1) 1-6    group_is_private(): a private group yes; a group with another member no; a gid that is another account's
 *                primary no; a duplicate gid in /etc/group no; gid 0 no; a gid not in /etc/group no;
 *   (2) 7-11   render_grant_add() ALL OR NOTHING: if even one renderD* already has an entry for that gid that is not ours,
 *                nothing is written on any node, it returns false, the administrator's entry is byte for byte as it was,
 *                nothing is recorded;
 *   (3) 12-19  a normal add: rw on every renderD*, card* untouched, a symlink and a non-char-device named renderD* ignored,
 *                the row is in the file;
 *   (4) 20-22  MAX_GRANTS reached: false, the ACL just put taken back from every node, the file as it was;
 *   (5) 23-27  render_grant_remove() takes out only OUR gid entries and only our row (another user's grant and an
 *                administrator's entry for another gid stay);
 *   (6) 28-33  acl_read() with an attribute of 0-3 bytes (and of 5) fails with EINVAL and does not look past what the
 *                kernel returned; 4 bytes is an empty ACL.
 *
 * BUILD AND RUN (a few seconds; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=2 --memory=2g -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && PK="gio-2.0" &&
 *     F="-g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wno-unused-parameter \
 *        -I/albero/src -I/albero/benches/fuzz/rcp-msg $(pkg-config --cflags $PK)" &&
 *     L="$(pkg-config --libs $PK) -lpthread -ldl -lm" &&
 *     clang $F -c /albero/benches/unit/render-grant/test.c -o t.o && clang $F -c /albero/benches/fuzz/rcp-msg/stubs_log.c -o l.o &&
 *     { clang -fsanitize=address,undefined t.o l.o $L -o t0 2> link1.log || true; } &&
 *     { echo "#include <stdio.h>"; grep -o "undefined reference to .[A-Za-z_0-9]*" link1.log | sed "s/.*to .//" | sort -u |
 *       while read -r n; do echo "void $n(void); void $n(void) { fputs(\"STUB reached: $n\", stderr); fputc(10, stderr); __builtin_trap(); }"; done; } > s.c &&
 *     clang $F -c s.c -o s.o && clang -fsanitize=address,undefined t.o l.o s.o $L -o test && ./test'
 * Exit status: 0 green, 1 red, 3 not all checks ran.
 */
#define _GNU_SOURCE
/* the system headers first: the macros below must not rename their declarations */
#include <dirent.h>
#include <endian.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/xattr.h>
#include <unistd.h>

DIR *fake_opendir(const char *path);
struct dirent *fake_readdir(DIR *d);
int fake_closedir(DIR *d);
int fake_lstat(const char *path, struct stat *st);
ssize_t fake_lgetxattr(const char *path, const char *name, void *value, size_t size);
int fake_lsetxattr(const char *path, const char *name, const void *value, size_t size, int flags);
FILE *fake_fopen(const char *path, const char *mode);
int fake_mkdir(const char *path, mode_t mode);
int fake_open(const char *path, int flags, ...);
int fake_fstat(int fd, struct stat *st);

#define opendir fake_opendir
#define readdir fake_readdir
#define closedir fake_closedir
#define lstat fake_lstat
#define lgetxattr fake_lgetxattr
#define lsetxattr fake_lsetxattr
#define fopen fake_fopen
#define mkdir fake_mkdir
#define open fake_open
#define fstat fake_fstat
#include "render_grant.c"
#undef opendir
#undef readdir
#undef closedir
#undef lstat
#undef lgetxattr
#undef lsetxattr
#undef fopen
#undef mkdir
#undef open
#undef fstat

static int failures = 0, passed = 0;
#define EXPECTED_CHECKS 33

static void require(int cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

/* ---------------------------------------------------------------------------
 * The world: /dev/dri as a table, three files in a temporary directory.
 * --------------------------------------------------------------------------- */
enum { K_CHR, K_LNK, K_REG };

struct vnode {
	const char *name;
	int kind;
	mode_t perm;
	unsigned char acl[4 + 8 * MAX_ENTRIES];
	ssize_t acl_len;                     /* -1: no ACL (ENODATA) */
	int sets;                            /* lsetxattr calls since reset */
};

static struct vnode nodes_tab[] = {
	{ "card0", K_CHR, 0660, {0}, -1, 0 },
	{ "renderD128", K_CHR, 0660, {0}, -1, 0 },
	{ "renderD129", K_CHR, 0660, {0}, -1, 0 },
	{ "renderD130", K_LNK, 0777, {0}, -1, 0 },   /* a symlink: ignored */
	{ "renderD131", K_REG, 0644, {0}, -1, 0 },   /* not a char device: ignored */
};
#define N_TAB ((int)(sizeof nodes_tab / sizeof nodes_tab[0]))
#define V_CARD 0
#define V_R128 1
#define V_R129 2
#define V_LINK 3
#define V_REG 4

static char tmp_root[128], group_path[200], passwd_path[200], grants_dir[200], grants_file[240];
static int readdir_at;
static struct dirent the_dirent;
static char dir_sentinel;
static long force_len = -1;              /* >= 0: lgetxattr answers this many bytes of a fixed pattern */

static struct vnode *find_node(const char *path)
{
	if (strncmp(path, DRI_DIR "/", sizeof DRI_DIR) != 0)
		return NULL;
	for (int i = 0; i < N_TAB; i++)
		if (strcmp(path + sizeof DRI_DIR, nodes_tab[i].name) == 0)
			return &nodes_tab[i];
	return NULL;
}

DIR *fake_opendir(const char *path)
{
	if (strcmp(path, DRI_DIR) != 0) {
		errno = ENOENT;
		return NULL;
	}
	readdir_at = 0;
	return (DIR *)&dir_sentinel;
}
struct dirent *fake_readdir(DIR *d)
{
	(void)d;
	if (readdir_at >= N_TAB)
		return NULL;
	memset(&the_dirent, 0, sizeof the_dirent);
	snprintf(the_dirent.d_name, sizeof the_dirent.d_name, "%s", nodes_tab[readdir_at++].name);
	return &the_dirent;
}
int fake_closedir(DIR *d)
{
	(void)d;
	return 0;
}
int fake_lstat(const char *path, struct stat *st)
{
	struct vnode *v = find_node(path);

	if (!v)
		return lstat(path, st);
	memset(st, 0, sizeof *st);
	st->st_mode = v->perm | (v->kind == K_CHR ? S_IFCHR : v->kind == K_LNK ? S_IFLNK : S_IFREG);
	return 0;
}
ssize_t fake_lgetxattr(const char *path, const char *name, void *value, size_t size)
{
	struct vnode *v = find_node(path);

	if (!v)
		return lgetxattr(path, name, value, size);
	if (force_len >= 0) {
		unsigned char *b = value;
		uint32_t ver = htole32(ACL_VERSION);

		memset(b, 0xAA, size);                       /* garbage beyond what is «returned» */
		memset(b, 0, (size_t)force_len < size ? (size_t)force_len : size);
		if (force_len >= 4)
			memcpy(b, &ver, 4);
		return force_len;
	}
	if (v->acl_len < 0) {
		errno = ENODATA;
		return -1;
	}
	memcpy(value, v->acl, (size_t)v->acl_len < size ? (size_t)v->acl_len : size);
	return v->acl_len;
}
int fake_lsetxattr(const char *path, const char *name, const void *value, size_t size, int flags)
{
	struct vnode *v = find_node(path);

	(void)name;
	(void)flags;
	if (!v) {
		errno = ENOENT;
		return -1;
	}
	memcpy(v->acl, value, size);
	v->acl_len = (ssize_t)size;
	v->sets++;
	return 0;
}
FILE *fake_fopen(const char *path, const char *mode)
{
	if (strcmp(path, "/etc/group") == 0)
		path = group_path;
	else if (strcmp(path, "/etc/passwd") == 0)
		path = passwd_path;
	return fopen(path, mode);
}
int fake_mkdir(const char *path, mode_t mode)
{
	return mkdir(strcmp(path, GRANTS_DIR) == 0 ? grants_dir : path, mode);
}
int fake_open(const char *path, int flags, ...)
{
	mode_t mode = 0;

	if (flags & O_CREAT) {
		va_list ap;

		va_start(ap, flags);
		mode = va_arg(ap, mode_t);
		va_end(ap);
	}
	return open(strcmp(path, GRANTS_DIR) == 0 ? grants_dir : path, flags, mode);
}
int fake_fstat(int fd, struct stat *st)
{
	int r = fstat(fd, st);

	if (r == 0 && S_ISDIR(st->st_mode)) {
		st->st_uid = 0;                  /* «root's folder»: the container may run as anyone */
		st->st_mode &= ~(mode_t)022;
	}
	return r;
}

static void put(const char *path, const char *text)
{
	FILE *fp = fopen(path, "w");

	if (!fp || fputs(text, fp) == EOF || fclose(fp) != 0) {
		perror(path);
		exit(1);
	}
}

/* Two private accounts, no shared groups, an empty record, no ACL anywhere. */
static void reset_world(void)
{
	put(group_path, "root:x:0:\nanna:x:1001:\nbob:x:1002:bob\nwheel:x:10:anna,bob\n");
	put(passwd_path, "root:x:0:0::/root:/bin/sh\nanna:x:1001:1001::/home/anna:/bin/sh\nbob:x:1002:1002::/home/bob:/bin/sh\n");
	unlink(grants_file);
	for (int i = 0; i < N_TAB; i++) {
		nodes_tab[i].acl_len = -1;
		nodes_tab[i].sets = 0;
	}
	force_len = -1;
}

static int total_sets(void)
{
	int n = 0;

	for (int i = 0; i < N_TAB; i++)
		n += nodes_tab[i].sets;
	return n;
}

/* The perm of the T_GROUP entry for `gid` in a node's ACL, or -1. */
static int group_perm(int node, gid_t gid)
{
	static const char *const path[] = { DRI_DIR "/card0", DRI_DIR "/renderD128", DRI_DIR "/renderD129" };
	struct acl_entry v[MAX_ENTRIES];
	int n = acl_read(path[node], v);

	for (int i = 0; i < n; i++)
		if (v[i].tag == T_GROUP && v[i].id == gid)
			return v[i].perm;
	return -1;
}

static int grants_rows(void)
{
	struct grant v[MAX_GRANTS];

	return grants_load(v);
}

static bool row_of(uid_t uid, gid_t gid)
{
	struct grant v[MAX_GRANTS];
	int n = grants_load(v);

	return n > 0 && grants_find(v, n, uid, gid) >= 0;
}

int main(void)
{
	char why[256];

	setvbuf(stdout, NULL, _IONBF, 0);
	snprintf(tmp_root, sizeof tmp_root, "/tmp/render-grant-XXXXXX");
	if (!mkdtemp(tmp_root)) {
		perror("mkdtemp");
		return 1;
	}
	snprintf(group_path, sizeof group_path, "%s/group", tmp_root);
	snprintf(passwd_path, sizeof passwd_path, "%s/passwd", tmp_root);
	snprintf(grants_dir, sizeof grants_dir, "%s/remotix", tmp_root);
	snprintf(grants_file, sizeof grants_file, "%s/" GRANTS_FILE, grants_dir);
	if (mkdir(grants_dir, 0700) != 0) {
		perror(grants_dir);
		return 1;
	}

	printf("  (1) group_is_private\n");
	reset_world();
	require(group_is_private("anna", 1001, why, sizeof why), "1. a private group: yes");
	put(group_path, "anna:x:1001:anna,bob\n");
	require(!group_is_private("anna", 1001, why, sizeof why), "2. a group with another member: no");
	put(group_path, "anna:x:1001:\n");
	put(passwd_path, "anna:x:1001:1001::/home/anna:/bin/sh\nmallory:x:1003:1001::/home/mallory:/bin/sh\n");
	require(!group_is_private("anna", 1001, why, sizeof why), "3. a gid that is another account's primary: no");
	put(group_path, "anna:x:1001:\nannas:x:1001:\n");
	put(passwd_path, "anna:x:1001:1001::/home/anna:/bin/sh\n");
	require(!group_is_private("anna", 1001, why, sizeof why), "4. a duplicate gid in /etc/group: no");
	reset_world();
	require(!group_is_private("root", 0, why, sizeof why), "5. gid 0: no");
	require(!group_is_private("anna", 4242, why, sizeof why), "6. a gid that is not in /etc/group: no");

	printf("  (2) render_grant_add is all or nothing\n");
	reset_world();
	require(acl_add_group(DRI_DIR "/renderD129", 1001) == 0, "7. (setup) the administrator's entry for gid 1001 on renderD129");
	{
		unsigned char before[sizeof nodes_tab[V_R129].acl];
		ssize_t len = nodes_tab[V_R129].acl_len;
		int sets = total_sets();

		memcpy(before, nodes_tab[V_R129].acl, sizeof before);
		require(!render_grant_add("anna", 1001, 1001), "8. render_grant_add() returns false");
		require(total_sets() == sets && nodes_tab[V_R128].acl_len < 0,
		        "9. nothing is written on any node (renderD128 has no ACL at all)");
		require(nodes_tab[V_R129].acl_len == len && memcmp(before, nodes_tab[V_R129].acl, (size_t)len) == 0,
		        "10. the administrator's entry is untouched, byte for byte");
		require(grants_rows() == 0, "11. nothing is recorded in the file");
	}

	printf("  (3) a normal add\n");
	reset_world();
	require(render_grant_add("anna", 1001, 1001), "12. returns true");
	require(group_perm(V_R128, 1001) == 6 && group_perm(V_R129, 1001) == 6, "13. rw on every renderD*");
	require(nodes_tab[V_CARD].sets == 0 && nodes_tab[V_CARD].acl_len < 0, "14. card0 is untouched");
	require(nodes_tab[V_LINK].sets == 0 && nodes_tab[V_LINK].acl_len < 0, "15. the symlink named renderD130 is ignored");
	require(nodes_tab[V_REG].sets == 0 && nodes_tab[V_REG].acl_len < 0, "16. the regular file named renderD131 is ignored");
	require(row_of(1001, 1001) && grants_rows() == 1, "17. its row «1001 1001 anna» is in the file");
	require(nodes_tab[V_R128].sets == 1 && nodes_tab[V_R129].sets == 1, "18. one write per node");
	require(render_grant_add("anna", 1001, 1001) && nodes_tab[V_R128].sets == 1 && grants_rows() == 1,
	        "19. asking again is true and changes nothing (ours, already recorded)");

	printf("  (4) MAX_GRANTS reached\n");
	reset_world();
	{
		FILE *fp = fopen(grants_file, "w");
		char before[8192] = "";
		size_t got;

		for (int i = 0; i < MAX_GRANTS; i++)
			fprintf(fp, "%d %d filler%d\n", 5000 + i, 5000 + i, i);
		fclose(fp);
		fp = fopen(grants_file, "r");
		got = fread(before, 1, sizeof before - 1, fp);
		fclose(fp);
		before[got] = '\0';
		require(!render_grant_add("anna", 1001, 1001), "20. returns false");
		require(group_perm(V_R128, 1001) < 0 && group_perm(V_R129, 1001) < 0,
		        "21. the ACL just put is taken back from every node");
		{
			char after[8192] = "";

			fp = fopen(grants_file, "r");
			got = fread(after, 1, sizeof after - 1, fp);
			fclose(fp);
			after[got] = '\0';
			require(strcmp(before, after) == 0 && grants_rows() == MAX_GRANTS, "22. the file is as it was");
		}
	}

	printf("  (5) render_grant_remove\n");
	reset_world();
	require(render_grant_add("anna", 1001, 1001) && render_grant_add("bob", 1002, 1002), "23. (setup) two grants");
	require(acl_add_group(DRI_DIR "/renderD128", 2000) == 0, "24. (setup) an administrator's entry for another gid");
	render_grant_remove("anna", 1001, 1001);
	require(group_perm(V_R128, 1001) < 0 && group_perm(V_R129, 1001) < 0, "25. our gid entry is gone from every node");
	require(group_perm(V_R128, 1002) == 6 && group_perm(V_R129, 1002) == 6 && group_perm(V_R128, 2000) == 6,
	        "26. another user's grant and the administrator's entry for another gid stay");
	require(grants_rows() == 1 && row_of(1002, 1002) && !row_of(1001, 1001), "27. only our row left the file");

	printf("  (6) acl_read with a tiny attribute\n");
	reset_world();
	for (int n = 0; n <= 3; n++) {
		struct acl_entry v[MAX_ENTRIES];
		char msg[96];
		int r;

		memset(v, 0x5A, sizeof v);
		force_len = n;
		errno = 0;
		r = acl_read(DRI_DIR "/renderD128", v);
		snprintf(msg, sizeof msg, "%d. %d byte(s): -1/EINVAL, no entry written", 28 + n, n);
		require(r == -1 && errno == EINVAL && ((unsigned char *)v)[0] == 0x5A, msg);
	}
	{
		struct acl_entry v[MAX_ENTRIES];

		force_len = 4;
		require(acl_read(DRI_DIR "/renderD128", v) == 0, "32. 4 bytes (the version only) is an empty ACL");
	}
	{
		struct acl_entry v[MAX_ENTRIES];

		force_len = 5;                   /* a version and one stray byte: (5 - 4) % 8 != 0 */
		errno = 0;
		require(acl_read(DRI_DIR "/renderD128", v) == -1 && errno == EINVAL, "33. 5 bytes (not whole entries): -1/EINVAL");
	}
	force_len = -1;

	{
		char cmd[300];

		snprintf(cmd, sizeof cmd, "rm -rf '%s'", tmp_root);
		if (system(cmd) != 0)
			fprintf(stderr, "could not remove %s\n", tmp_root);
	}
	printf("\n  %d/%d checks passed\n", passed, EXPECTED_CHECKS);
	if (failures)
		return 1;
	return passed == EXPECTED_CHECKS ? 0 : 3;
}
