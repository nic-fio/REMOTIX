/*
 * card_pick — WHICH CARD THE DESKTOP DRAWS ON, chosen by REMOTIX (1.5, 27 Oct 2026, DECISIONS §11.37 addendum).
 *
 * ⛔ Until now: «the first openable renderD* in NAME order».  The names swap between boots (renderD128 / renderD129), so on
 *    a machine with two cards the desktop could change card by itself.  And the administrator does NOT choose: the user
 *    decided (27 Oct 2026) that the card is the BIOS's.
 *
 * ⭐ The rule, one function for `session.c` (the card given to labwc / KWin's host) and `wlroots.c` (its fallback):
 *      1. the BIOS primary card (PCI `boot_vga` = 1), IF it is capable: it has a render node, the node opens and
 *         `can_draw` holds;
 *      2. otherwise the capable card with the LOWEST PCI ADDRESS (stable between boots), not the lowest node name.
 *    «Capable» = a render node that opens and, when the caller gives `can_draw`, creates the drawing buffer
 *    (`card_can_draw()` of session.c).  NULL `can_draw` = «opens» is enough.
 *    GNOME chooses its own card (Mutter: Boot VGA): it does not go through here.
 *
 * ⚠ The directories are parameters so that the unit test can give a fake tree: in the product `/dev/dri` and
 *   `/sys/class/drm`.  Where sysfs says nothing (some containers) the PCI address is missing and the order falls
 *   back to the node name, as before.
 */
#ifndef REMOTIX_CARD_PICK_H
#define REMOTIX_CARD_PICK_H

#include <glib.h>

typedef gboolean (*card_draw_fn)(const char *node, char **why);

typedef enum {
	CARD_PICK_BIOS_PRIMARY,  /* the BIOS primary card, capable */
	CARD_PICK_PCI_FIRST,     /* the capable card with the lowest PCI address (no primary, or it cannot) */
	CARD_PICK_NONE_CAPABLE,  /* render nodes open but none can draw: NULL, the caller declares pixman */
	CARD_PICK_NO_NODE        /* no renderD* opens: NULL */
} card_pick_how;

/* Returns the chosen node (/dev/dri/renderDN, free with g_free) or NULL.  `*story` (free with g_free) is ONE sentence
 * for the log saying why: «BIOS primary card», «first capable card by PCI address; the BIOS primary 0000:03:00.0
 * (renderD129, driver ast) has no render node», … */
char *card_pick(const char *dev_dir, const char *sys_dir, card_draw_fn can_draw, card_pick_how *how,
                char **story);

/* ⭐ 1.5 (27 Oct 2026): is `driver` a SERVICE / BMC card's — a card that cannot draw or encode on the GPU?  (ast =
 * ASPEED, mgag200 = Matrox G200 of the Dell/HP BMCs, hibmc = HiSilicon's).  Only the classification: «no render node»
 * is another way to be a service card and is decided by whoever has the node.  NULL / unknown driver = FALSE. */
gboolean card_pick_service_driver(const char *driver);

/* the driver (kernel module name) of a render node `/dev/dri/renderDN` through `sys_dir`/renderDN/device/driver; g_free,
 * NULL if sysfs does not say */
char *card_pick_driver_of(const char *sys_dir, const char *node);

#endif
