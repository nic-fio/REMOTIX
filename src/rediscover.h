/*
 * rediscover.h — ⭐ PHASE 17, T7: LIVE REMOTIX DESKTOPS THAT NO CHILD HOLDS.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, WITH THE MEASUREMENT NEXT TO IT
 *
 * `[M]` T2, 29 Sep 2026 (`phases/17-the-installer.md` §5.2): stopping the service
 * **does not kill the desktops**.  Parent, PAM helper and child die; the stage,
 * born with `setsid --fork` (`session.c`, `start()`), lives outside the unit and
 * survives with its programs.  ⛔ But the new parent restarted with
 * «tenants=0»: nobody counted those desktops — neither the session cap,
 * nor the budget, nor the abandonment clock — and the first new user
 * without the card groups could have had them knocked down by
 * `loginctl terminate-user`.  It is the xrdp case: live sessions nobody finds again.
 *
 * ---------------------------------------------------------------------------
 * ⭐ THE CRITERION — one for all desktops, no per-compositor exceptions
 *
 *   1. a **logind** session with the PAM service `remotix` (`Service=remotix`:
 *      the child opens it with `pam_start("remotix", …)`), in ANY state —
 *      `[M]` T2: it is «closing» 24 ms after birth, because the child calls
 *      `pam_end` without `pam_close_session`, and it stays so while it has processes;
 *   2. in its scope, a process of the user that is **leader of its own
 *      process session** (pid = sid) and whose parent is **not** in the
 *      same scope.  It is the signature of `setsid --fork`, that is of how the product
 *      starts the stage on ALL desktops.  `[M]` T2, after the stop:
 *      `gnome-session-binary` (GNOME), `startplasma-wayland` (KDE), `labwc`
 *      (XFCE, LXQt), all with pid = sid and parent 1.  ⚠ A terminal opened in the
 *      desktop makes its shell a session leader, but its parent (the terminal)
 *      is in the scope: no confusion.
 *
 * ⚠ The user's session bus is not used: the parent is root and root cannot
 *   join it (`child.h`, §1.10-bis).  Nor are files written by the
 *   child used: desktops born with the PREVIOUS binary (the upgrade) would not
 *   have them.  Every version has logind and `/proc`.
 */
#ifndef REMOTIX_FINDING_AGAIN_H
#define REMOTIX_FINDING_AGAIN_H

#include <stdbool.h>
#include <stddef.h>
#include <sys/types.h>

/* The PAM service the child opens: `pam_start("remotix", …)`. */
#define FOUND_AGAIN_PAM_SERVICE "remotix"

typedef struct {
	char user[257];
	uid_t uid;
	char session[32]; /* the logind id of the session that contains the stage */
	pid_t stage;       /* the leader of the stage (pid = sid) */
	char comm[20];     /* its name, for the log */
	unsigned sessions; /* how many `remotix` logind sessions the user has */
	/* ⭐ 1.6 (R8): the stage's start time (field 22 of /proc/<pid>/stat, clock ticks since boot): a pid alone can be reused, the
	 *    pair (pid, starttime) cannot.  The root side watches the stage with it (`pidfd_open` + this check). */
	unsigned long long starttime;
} RediscoveredDesktop;

/*
 * Looks for live REMOTIX desktops: at most `cap`, ONE per user.  Returns how many
 * it wrote, or -1 if logind did not answer (the reason in `why`).
 * ⚠ The FIRST call of the process waits for logind (300 ms ceiling per call)
 *   and reads `/proc`: it is the startup's.  ⭐ Every later one (15 Oct 2026)
 *   does NOT wait: it uses logind's answer to the PREVIOUS call (≤ 45 s old,
 *   or -1), reads `/proc` now, and sends the next question — the box is in
 *   `rediscover.c`, above `struct question`.
 */
int rediscover_search(RediscoveredDesktop *v, int cap, char *why, size_t how_much);

/*
 * ⭐ 1.6 (R8, DECISIONS.md §11.50) — THE SAME QUESTION, FOR THE ROOT SIDE.  The root side is single-threaded and
 * has no GDBus (a fork of a process with a GDBus worker thread runs PAM and NSS in a copy whose locks may be held
 * by a thread that is not there), so it asks logind's own files instead of its bus: /run/systemd/sessions/<id>
 * (`UID=`, `SERVICE=`, `SCOPE=`, the first of each key, as `render_grant.c` reads them; a «closing» session counts,
 * as it does on the bus), then the same single pass over /proc and the same criterion.  Returns how many it
 * wrote (at most `cap`, one per user), or -1 if the sessions' directory or /proc cannot be read (`why`).
 * Never waits, never touches GLib.  The `_at` form takes the two roots so a desk test can give it a fake /proc.
 */
int rediscover_search_files(RediscoveredDesktop *v, int cap, char *why, size_t how_much);
int rediscover_search_files_at(const char *sessions_dir, const char *proc_root, RediscoveredDesktop *v, int cap,
                               char *why, size_t how_much);

/* The start time (field 22 of `<proc_root>/<pid>/stat`).  false if the file is missing or malformed. */
bool rediscover_starttime(const char *proc_root, pid_t pid, unsigned long long *out);

/*
 * Turns the GLib context of the check that does not wait, never blocking:
 * what logind answered is collected, a round out longer than 5 s is cut.
 * `rediscover_search()` calls it itself; calling it at every pass of the loop
 * as well only makes the answer ready sooner.
 */
void rediscover_collect(void);

/*
 * ⚠ It always WAITS for logind: it is for startup (`render_grant_sweep()`),
 *   never for the loop.
 * Does user `uid` have a live REMOTIX desktop?  1 yes (and `d`, if not NULL,
 * describes it) · 0 no · -1 unknown (logind silent).  ⛔ Whoever must decide whether
 * to knock something down treats -1 as «yes».
 */
int rediscover_alive(uid_t uid, RediscoveredDesktop *d);

#endif
