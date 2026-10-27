/*
 * render_node — WHICH CARD ENCODES (1.5, SPECS audit 15 Oct 2026).
 *
 * ⛔ Until 1.0 the encoder opened `/dev/dri/renderD128` hard-wired
 *    (`RENDER_NODE`, `child.c`).  On a machine with ONE card that is the
 *    card.  On a machine with TWO (the test server: Intel UHD 770 + AMD
 *    RX 6800) it is the card the KERNEL numbered first — not necessarily the
 *    one the compositor draws on, and then every frame is a cross-card import
 *    (it fails, or it goes through memory and is slow).
 *
 * ⭐ The compositor SAYS which card it draws on: `linux-dmabuf` v4, the
 *    default feedback's `main_device` (a `dev_t`).  wlroots/labwc, Mutter and
 *    KWin all send it; it is the same question `wlroots.c` already asks for
 *    its slabs.  From the `dev_t` to `renderD*` through sysfs, no libdrm.
 *
 * ⚠ The order in `child.c` (`choose_render_node()`): the compositor's card
 *   → `--render-node` → `renderD128`.  On a one-card machine all three name
 *   the same node: nothing changes there.
 */
#ifndef REMOTIX_RENDER_NODE_H
#define REMOTIX_RENDER_NODE_H

#include <stdbool.h>
#include <stddef.h>

/* Asks the compositor of this session (the same socket search as
 * `kwin_display_open()`) for its `main_device` and writes the `renderD*` of
 * that card in `out`.  ⛔ With a 2 s ceiling: a compositor that does not
 * answer does not stop the child.
 *   true                      `out` = an OPENABLE /dev/dri/renderDN
 *   false, *reached == false  no compositor reachable yet (ask again later)
 *   false, *reached == true   it answered but did not name a usable card
 *                             (v < 4, no render node, not openable): `why` */
bool render_node_of_compositor(char *out, size_t n, char *why, size_t wn, bool *reached, char *driver, size_t dn);
/* ⭐ 1.5 (27 Oct 2026): `driver` (may be NULL) = the kernel driver of the compositor's `main_device`, filled as soon as
 * the compositor has stated it — also when that card has NO render node (ast / mgag200: display only), so that the
 * caller can say «the desktop draws on a service card».  "" when unknown. */

/* «0000:00:02.0, driver i915, 8086:4680» for the log; «?» parts when sysfs
 * does not say.  Never fails. */
void render_node_describe(const char *node, char *out, size_t n);

/* ⭐ 1.5 (review of 13422add) — the DRM character-device major (Linux
 *    `DRM_MAJOR`): a `/dev/dri/` path that is not a char device with this
 *    major is not a card, whatever its name. */
#define RENDER_NODE_DRM_MAJOR 226u

/* true if `path` is under /dev/dri/, exists, is a character device and has
 * the DRM major 226 (`st_rdev`).  When false, `why` says which of the four
 * failed (for the one log line of `child_render_node()`). */
bool render_node_is_drm(const char *path, char *why, size_t wn);

/* true if `a` and `b` name the same card: the same `st_rdev` when both
 * stat, otherwise the same string.  ⚠ Two names of one node (a symlink,
 * `/dev/dri/by-path/…`) are the same card: comparing strings alone would
 * run a second test for nothing. */
bool render_node_same(const char *a, const char *b);

#endif
