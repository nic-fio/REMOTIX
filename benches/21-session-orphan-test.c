/* 21-session-orphan-test.c — `orphan_profile_pcmanfm_lxqt()` of `src/session.c`
 * (commit 8124e05c), alone, in a temporary HOME and temporary system folders.
 *
 *   make -C src test-session            (on the test server: in the build container,
 *                                         `server-build.sh test-session`)
 *
 * ⭐ What it checks — the eight states `~/.config/pcmanfm-qt/lxqt/` can be in:
 *     1. no folder                    ⇒ nothing is created
 *     2. an EMPTY folder              ⇒ removed (pcmanfm-qt goes back to the system profile)
 *     3. only `settings.conf.lock`    ⇒ the system `settings.conf` is copied in, the lock stays
 *     4. other files                  ⇒ the same, and the other files are not touched
 *     5. the user's `settings.conf`   ⇒ NEVER touched
 *     6. no system file anywhere      ⇒ nothing is written, nothing is removed
 *     7. a SYMLINK in place of the folder, to a folder OUT of HOME ⇒ nothing is
 *        written or removed through it, and the link stays a link
 *     8. the order of the system folders: the first that has the file wins
 *
 * ⛔ The function is not linked from `session.o` (it is `static`, and session.c pulls
 *    in the whole product): the Makefile cuts it OUT of `src/session.c` with `sed`
 *    — the very text that is built — into `orphan-extract.c`.  If session.c has no
 *    such function (the code before 8124e05c), the Makefile puts an EMPTY one in
 *    its place and says so: that is exactly what the old code did, nothing.
 * ⛔ The system folders come from `-DORPHAN_PROFILE_SYSTEM_DIRS` (the Makefile):
 *    `$(dir)/sys-a` first, `$(dir)/sys-b` second.  The product is built without
 *    the macro and keeps `/etc`, `/etc/xdg`, `/usr/share`.
 *
 * Exit status, as `01-b8-ban-test.c`:
 *      0  green — and the verdict says on how many checks
 *      1  red — at least one check failed
 *      2  ⛔ no outcome: zero checks run
 *      3  ⛔ the run did not get to the end (sections missing)
 *      4  ⛔ early exit: the verdict was not given at all                  */
#include "log.h"
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <glib.h>
#include <glib/gstdio.h>

#ifndef ORPHAN_SYSTEM_A
#error "build it with make -C src test-session"
#endif
#define ORPHAN_PROFILE_SYSTEM_DIRS ORPHAN_SYSTEM_A, ORPHAN_SYSTEM_B

#include "orphan-extract.c"

#define EXPECTED_SECTIONS 8

static int failures = 0, passed = 0, sections = 0;
static bool verdict_given = false;
static char *home, *profile, *folder, *file, *outside;

static const char SYSTEM_A[] = "[Desktop]\nWallpaper=/usr/share/wallpapers/a.png\nWallpaperMode=zoom\n";
static const char SYSTEM_B[] = "[Desktop]\nWallpaper=/usr/share/wallpapers/b.png\nWallpaperMode=stretch\n";
static const char USERS[]    = "[Desktop]\nWallpaperMode=none\nBgColor=#123456\n";
static const char RECENT[]   = "[RecentFiles]\nRecentFiles=/home/x/a.txt\n";

static void require(bool cond, const char *desc)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", desc);
	if (cond)
		passed++;
	else
		failures++;
}

static void section(const char *title)
{
	sections++;
	printf("\n  == [section %d] %s\n", sections, title);
}

static void on_farewell(void)
{
	if (verdict_given)
		return;
	fprintf(stderr, "\n  ⛔ EARLY EXIT: no verdict given (%d checks, %d sections).\n",
	        passed + failures, sections);
	fflush(NULL);
	_exit(4);
}

/* ── small helpers ─────────────────────────────────────────────────────────── */

static void must(bool ok, const char *what)
{
	if (!ok) {
		fprintf(stderr, "  ⛔ setup failed: %s (%s)\n", what, strerror(errno));
		exit(3);
	}
}

static void put(const char *path, const char *text)
{
	must(g_file_set_contents(path, text, -1, NULL), path);
}

static bool has(const char *path, const char *text)
{
	g_autofree char *c = NULL;
	return g_file_get_contents(path, &c, NULL, NULL) && strcmp(c, text) == 0;
}

static bool exists(const char *path) /* lstat: a link counts as itself */
{
	GStatBuf st;
	return g_lstat(path, &st) == 0;
}

static bool is_real_dir(const char *path)
{
	GStatBuf st;
	return g_lstat(path, &st) == 0 && S_ISDIR(st.st_mode);
}

static bool is_link(const char *path)
{
	GStatBuf st;
	return g_lstat(path, &st) == 0 && S_ISLNK(st.st_mode);
}

static int count_entries(const char *path)
{
	GDir *d = g_dir_open(path, 0, NULL);
	int n = 0;
	if (!d)
		return -1;
	while (g_dir_read_name(d))
		n++;
	g_dir_close(d);
	return n;
}

static void wipe(const char *path) /* rm -rf, never following links */
{
	GStatBuf st;
	if (g_lstat(path, &st) != 0)
		return;
	if (S_ISDIR(st.st_mode)) {
		GDir *d = g_dir_open(path, 0, NULL);
		const char *name;
		while (d && (name = g_dir_read_name(d))) {
			g_autofree char *child = g_build_filename(path, name, NULL);
			wipe(child);
		}
		if (d)
			g_dir_close(d);
		g_rmdir(path);
	} else {
		g_unlink(path);
	}
}

/* Every section starts from: HOME/.config/pcmanfm-qt/ (no lxqt), sys-a and sys-b
 * with their settings.conf, nothing outside. */
static void fresh(bool with_system_a, bool with_system_b)
{
	g_autofree char *sa = g_build_filename(ORPHAN_SYSTEM_A, "pcmanfm-qt", "lxqt", NULL);
	g_autofree char *sb = g_build_filename(ORPHAN_SYSTEM_B, "pcmanfm-qt", "lxqt", NULL);
	g_autofree char *fa = g_build_filename(sa, "settings.conf", NULL);
	g_autofree char *fb = g_build_filename(sb, "settings.conf", NULL);

	wipe(home);
	wipe(ORPHAN_SYSTEM_A);
	wipe(ORPHAN_SYSTEM_B);
	wipe(outside);
	must(g_mkdir_with_parents(profile, 0700) == 0, profile);
	if (with_system_a) {
		must(g_mkdir_with_parents(sa, 0755) == 0, sa);
		put(fa, SYSTEM_A);
	}
	if (with_system_b) {
		must(g_mkdir_with_parents(sb, 0755) == 0, sb);
		put(fb, SYSTEM_B);
	}
}

static char *in_folder(const char *name)
{
	return g_build_filename(folder, name, NULL);
}

int main(void)
{
	g_autofree char *base = NULL;

	atexit(on_farewell);
	/* ⚠ HOME before the first g_get_home_dir(): glib reads it once and keeps it. */
	base = g_dir_make_tmp("remotix-orphan-XXXXXX", NULL);
	must(base != NULL, "temporary folder");
	home = g_build_filename(base, "home", NULL);
	outside = g_build_filename(base, "outside", NULL);
	must(g_setenv("HOME", home, TRUE), "HOME");
	profile = g_build_filename(home, ".config", "pcmanfm-qt", NULL);
	folder = g_build_filename(profile, "lxqt", NULL);
	file = g_build_filename(folder, "settings.conf", NULL);
	printf("  HOME=%s\n  system folders: %s, %s\n  function under test: %s\n",
	       home, ORPHAN_SYSTEM_A, ORPHAN_SYSTEM_B,
	       ORPHAN_EXTRACTED ? "cut from src/session.c"
	                        : "⛔ NOT in src/session.c — an empty one (the code before 8124e05c)");
	fresh(true, true);
	must(strcmp(g_get_home_dir(), home) == 0, "g_get_home_dir() is not the temporary HOME");

	section("no folder ⇒ nothing is created");
	fresh(true, true);
	orphan_profile_pcmanfm_lxqt();
	require(!exists(folder), "~/.config/pcmanfm-qt/lxqt still does not exist");
	require(count_entries(profile) == 0, "~/.config/pcmanfm-qt still empty");

	section("an EMPTY folder ⇒ removed");
	fresh(true, true);
	must(g_mkdir(folder, 0700) == 0, folder);
	orphan_profile_pcmanfm_lxqt();
	require(!exists(folder), "the empty lxqt folder was removed");
	require(is_real_dir(profile), "~/.config/pcmanfm-qt itself stays");

	section("only settings.conf.lock ⇒ the system settings.conf is copied in");
	{
		g_autofree char *lock = in_folder("settings.conf.lock");
		fresh(true, true);
		must(g_mkdir(folder, 0700) == 0, folder);
		put(lock, "");
		orphan_profile_pcmanfm_lxqt();
		require(is_real_dir(folder), "the folder stays");
		require(has(file, SYSTEM_A), "settings.conf = the system one");
		require(has(lock, ""), "settings.conf.lock untouched");
		require(count_entries(folder) == 2, "nothing else written (2 entries)");
	}

	section("other files ⇒ the system settings.conf is copied in, the rest untouched");
	{
		g_autofree char *recent = in_folder("recent-files.conf");
		g_autofree char *sub = in_folder("sub");
		fresh(true, true);
		must(g_mkdir(folder, 0700) == 0, folder);
		put(recent, RECENT);
		must(g_mkdir(sub, 0700) == 0, sub);
		orphan_profile_pcmanfm_lxqt();
		require(has(file, SYSTEM_A), "settings.conf = the system one");
		require(has(recent, RECENT), "recent-files.conf untouched");
		require(is_real_dir(sub), "the sub-folder untouched");
		require(count_entries(folder) == 3, "nothing else written (3 entries)");
	}

	section("the user's settings.conf ⇒ NEVER touched");
	{
		g_autofree char *recent = in_folder("recent-files.conf");
		GStatBuf before = { 0 }, after = { 0 };
		fresh(true, true);
		must(g_mkdir(folder, 0700) == 0, folder);
		put(file, USERS);
		put(recent, RECENT);
		must(g_lstat(file, &before) == 0, file);
		orphan_profile_pcmanfm_lxqt();
		must(g_lstat(file, &after) == 0, file);
		require(has(file, USERS), "settings.conf still the user's");
		require(before.st_ino == after.st_ino && before.st_mtime == after.st_mtime,
		        "same inode, same mtime (not rewritten)");
		require(has(recent, RECENT), "recent-files.conf untouched");
		/* and an EMPTY user settings.conf is still the user's */
		put(file, "");
		orphan_profile_pcmanfm_lxqt();
		require(has(file, ""), "an empty user settings.conf stays empty");
		/* and a dangling link named settings.conf is the user's too */
		g_unlink(file);
		must(symlink("/nonexistent/remotix-orphan-settings.conf", file) == 0, "symlink");
		orphan_profile_pcmanfm_lxqt();
		require(is_link(file), "a dangling settings.conf link stays a link");
	}

	section("no system file anywhere ⇒ nothing written, nothing removed");
	{
		g_autofree char *recent = in_folder("recent-files.conf");
		fresh(false, false);
		must(g_mkdir(folder, 0700) == 0, folder);
		put(recent, RECENT);
		orphan_profile_pcmanfm_lxqt();
		require(is_real_dir(folder), "the folder stays");
		require(!exists(file), "no settings.conf invented");
		require(has(recent, RECENT), "recent-files.conf untouched");
		require(count_entries(folder) == 1, "still 1 entry");
	}

	section("a SYMLINK in place of the folder, to a folder out of HOME ⇒ not followed");
	{
		g_autofree char *out_recent = g_build_filename(outside, "recent-files.conf", NULL);
		g_autofree char *out_file = g_build_filename(outside, "settings.conf", NULL);
		/* (a) the target holds a file: nothing must be written into it */
		fresh(true, true);
		must(g_mkdir(outside, 0700) == 0, outside);
		put(out_recent, RECENT);
		must(symlink(outside, folder) == 0, "symlink");
		orphan_profile_pcmanfm_lxqt();
		require(is_link(folder), "lxqt is still the link");
		require(!exists(out_file), "no settings.conf written OUT of HOME");
		require(has(out_recent, RECENT) && count_entries(outside) == 1,
		        "the outside folder untouched");
		/* (b) the target is empty: it must not be removed, nor the link */
		fresh(true, true);
		must(g_mkdir(outside, 0700) == 0, outside);
		must(symlink(outside, folder) == 0, "symlink");
		orphan_profile_pcmanfm_lxqt();
		require(is_link(folder), "lxqt is still the link (empty target)");
		require(is_real_dir(outside) && count_entries(outside) == 0,
		        "the empty outside folder still there, still empty");
	}

	section("the order of the system folders: the first that has the file wins");
	{
		g_autofree char *recent = in_folder("recent-files.conf");
		fresh(true, true);
		must(g_mkdir(folder, 0700) == 0, folder);
		put(recent, RECENT);
		orphan_profile_pcmanfm_lxqt();
		require(has(file, SYSTEM_A), "both there ⇒ the FIRST one's (sys-a)");
		fresh(false, true);
		must(g_mkdir(folder, 0700) == 0, folder);
		put(recent, RECENT);
		orphan_profile_pcmanfm_lxqt();
		require(has(file, SYSTEM_B), "the first missing ⇒ the second one's (sys-b)");
	}

	wipe(base);
	wipe(ORPHAN_SYSTEM_A);
	wipe(ORPHAN_SYSTEM_B);

	verdict_given = true;
	printf("\n  verdict: %d/%d checks passed, %d/%d sections\n",
	       passed, passed + failures, sections, EXPECTED_SECTIONS);
	if (passed + failures == 0) {
		printf("  ⛔ NO OUTCOME: zero checks run\n");
		return 2;
	}
	if (sections != EXPECTED_SECTIONS) {
		printf("  ⛔ INCOMPLETE: %d sections out of %d\n", sections, EXPECTED_SECTIONS);
		return 3;
	}
	if (failures) {
		printf("  RED: %d checks failed\n", failures);
		return 1;
	}
	printf("  GREEN\n");
	return 0;
}
