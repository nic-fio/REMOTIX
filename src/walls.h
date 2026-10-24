/*
 * walls.h — ⭐ 1.5 (DECISIONS.md §11.11, §11.50): THE NETWORK SIDE'S WALLS.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT IT IS FOR, IN PLAIN WORDS
 *
 * The network side is the process that talks to the internet: if a bug in
 * QUIC, TLS or the page ever lets a stranger run code in it, that code must
 * find itself in a room with no doors.  These are the walls of that room,
 * put up by the root side in the `fork`, still as root, right before the
 * `execve(/proc/self/exe --network-side …)`:
 *
 *   1. a mount namespace of its own, where the WHOLE tree is read-only
 *      (`mount_setattr(AT_RECURSIVE, MOUNT_ATTR_RDONLY)`) except the two
 *      directories it must write — `/var/lib/remotix/net` (certificates,
 *      QUIC secret, ban) and `/run/remotix/net` (the bench's command socket)
 *      — and a private, empty `/tmp`;
 *   2. on SELinux, `setexeccon` to `remotix_net_t` (type replaced in the
 *      current context; libselinux by `dlopen`, as `child.c` does);
 *   3. no supplementary group, `setgid`/`setuid` to `remotix`, checked with
 *      `getresuid`/`getresgid`; no capability left (effective, permitted,
 *      bounding, ambient: read back from /proc/self/status);
 *   4. `PR_SET_NO_NEW_PRIVS`.
 *
 * ⛔ Any step that fails ⇒ -1 and the reason in `why`: the root side does NOT
 *    start the network side.  A network side without its walls is the 1.0
 *    server with extra steps, and that must never happen silently.
 *
 * ⚠ The desktops are NOT behind these walls: their children are forked by
 *   the root side, never from here (the reason of §11.11 — `sudo apt
 *   install` in the remote desktop keeps working).
 * ⚠ /proc is not hidden: the rediscovery of §T7 reads it (`rediscover.c`).
 * ---------------------------------------------------------------------------
 */
#ifndef REMOTIX_WALLS_H
#define REMOTIX_WALLS_H

#include <stddef.h>

#if __has_include("rootside.h")
#include "rootside.h"
#else
#include "rootside_provisional.h"
#endif

/* Applies the walls to the CALLING process (the root side's fork, as root).
 * 0 = all in place, the caller may `execve`; -1 = not, and `why` says which
 * wall and why.  Uses `o->net_user`, `o->net_state_dir`, `o->net_run_dir`. */
int walls_apply(const struct rootside_options *o, char *why, size_t why_len);

#endif
