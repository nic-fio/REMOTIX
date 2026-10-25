/*
 * render_grant.h — ⭐ 1.5 (DECISIONS.md §11.4): THE CARD FOR A STALE USER MANAGER,
 *                 WITHOUT CLOSING ANYTHING.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, WITH THE MEASUREMENT NEXT TO IT
 *
 * A process takes its groups when it is born and never again.  If the user
 * already has a `systemd --user` running (an SSH session, lingering) when
 * REMOTIX puts them in `render`/`video`, that manager keeps the OLD list, and
 * so does every unit it starts — gnome-shell on GNOME, kwin on KDE.
 * Until 1.0 the cure was `loginctl terminate-user`: `[M]` 12 Oct 2026, tablet
 * CHUWI, it killed the user's SSH session (SPECS §5.1 broken).
 * `[M]` 13 Oct 2026, tablet and the four boxes: without the cure GNOME and KDE
 * are born but draw in SOFTWARE; with an ACL for the user's PRIMARY group on
 * `renderD*` they open the card again — the stale manager carries that gid —
 * and nothing is closed.  XFCE and LXQt need nothing: labwc is born from our
 * child, with fresh groups.
 *
 * ⛔ WHY THE GROUP AND NOT THE USER: `renderD*` is tagged `uaccess`, and logind
 *    rewrites the named-USER entries of those ACLs when the person in front of
 *    the machine changes.  Named-GROUP entries it does not touch.
 * ⛔ WHY ONLY A PROVABLY PRIVATE GROUP: an ACL for a group shared by several
 *    accounts would give the card to all of them.  Proof is asked of the local
 *    files (`/etc/group`, `/etc/passwd`); a network account cannot give it, and
 *    gets no grant — its desktop is born anyway, in software.
 *
 * ⚠ Declared limits: a device recreated while the desktop lives (driver
 *   reload, hotplug) loses the grant; removing the grant does not close the
 *   descriptors already open (the kernel checks at `open`).
 * ⚠ The grant lives as long as the CHILD, not the desktop: `[M]` 13 Oct 2026,
 *   KDE box, after «Log out» with no client attached the child stays until the
 *   user comes back, and the grant with it.  Harmless — the group is the
 *   user's alone, and the account is already in `render` — and bounded: the
 *   nodes live in devtmpfs, so a reboot clears every ACL, and the start-up
 *   sweep clears what a crash left.
 */
#ifndef REMOTIX_RENDER_GRANT_H
#define REMOTIX_RENDER_GRANT_H

#include <stdbool.h>
#include <sys/types.h>

/*
 * Is the bridge needed for `uid`?  1 yes: its user manager is alive and cannot
 * open a `renderD*` node with its own credentials · 0 no (no manager, or it
 * can, or there is no render node) · -1 unknown.
 */
int render_grant_needed(uid_t uid, const char *user);

/*
 * Grants `rw` on every `renderD*` to the primary group `gid` of `user`, and
 * records it in /var/lib/remotix/render-grants.  `true` if the grant is in
 * place and is OURS (to be removed with `render_grant_remove`); `false` if it
 * was not given — the reason is written in the log, and the desktop is born
 * anyway.  An entry the administrator had already put is never claimed.
 */
bool render_grant_add(const char *user, uid_t uid, gid_t gid);

/* Removes our grant for `gid` from every `renderD*`, and its record line. */
void render_grant_remove(const char *user, uid_t uid, gid_t gid);

/*
 * At start-up: every recorded grant whose user has no live REMOTIX desktop is
 * removed (a crash, a power cut).  When logind cannot tell, it is kept.
 */
void render_grant_sweep(void);

/* ⭐ 1.5 (§11.50) — logind's own files, not its bus (phase D2; same text as port-rootside's
 *    render_grant.h, 614d48e9).
 *    Is there a live logind session of `uid` with the PAM service `remotix` (active, or closing with a process left in
 *    its scope)?  1 yes · 0 no · -1 unknown.  Used by the sweep and by CLOSE_ORPHAN of the root side. */
int render_grant_remotix_session(uid_t uid);
/* The same, on other directories (the tests): `sessions_dir` in place of /run/systemd/sessions, `cgroup_root` in
 * place of /sys/fs/cgroup. */
int render_grant_remotix_session_at(const char *sessions_dir, const char *cgroup_root, uid_t uid);

#endif
