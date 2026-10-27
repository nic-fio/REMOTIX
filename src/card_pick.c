/*
 * card_pick — see `card_pick.h`.
 */
#include "card_pick.h"

#include <errno.h>
#include <fcntl.h>
#include <gbm.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <glib/gstdio.h>

/*
 * ⭐ PHASE 17 — CAN THE CARD DRAW?  Opening the node is not enough.
 *
 * `[M]` 29 Sep 2026, openSUSE Leap 16 VM with `virtio_gpu` WITHOUT 3D: the node
 *   `renderD128` OPENS (so `card_node()` returns it), but labwc
 *   cannot create the output buffer on it — `gbm_bo_create failed`,
 *   `Failed to allocate buffer` — and draws nothing: black canvas.  With
 *   `WLR_RENDERER=pixman` the desktop arrives.
 *
 * ⇒ Before labwc, the SAME move labwc falls on is made: `gbm` on the node and
 *   an XRGB8888 buffer with the usages wlroots asks for when it creates without
 *   modifiers (`[R]` wlroots `render/allocator/gbm.c`, `create_buffer`:
 *   `GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING`), then with RENDERING only.
 *   ⛔ «No» is said only if BOTH fail: in doubt the card wins,
 *      because on machines with a real card nothing must change.
 * ⛔ No exception per distribution, desktop or driver: the machine is asked
 *    whether it can do the thing, and the answer is written.
 *
 * Returns TRUE if the buffer is born; otherwise FALSE, with the reason in `*why`.
 */
gboolean card_can_draw(const char *node, char **why)
{
	static const uint32_t uses[] = { GBM_BO_USE_SCANOUT | GBM_BO_USE_RENDERING,
		                        GBM_BO_USE_RENDERING };
	struct gbm_device *gbm;
	int fd, error = 0;

	fd = g_open(node, O_RDWR | O_CLOEXEC, 0);
	if (fd < 0) {
		*why = g_strdup_printf("%s does not open: %s", node, g_strerror(errno));
		return FALSE;
	}
	gbm = gbm_create_device(fd);
	if (!gbm) {
		*why = g_strdup_printf("gbm_create_device on %s fails", node);
		g_close(fd, NULL);
		return FALSE;
	}
	for (guint i = 0; i < G_N_ELEMENTS(uses); i++) {
		struct gbm_bo *bo;

		errno = 0;
		bo = gbm_bo_create(gbm, 256, 256, GBM_FORMAT_XRGB8888, uses[i]);
		if (bo) {
			gbm_bo_destroy(bo);
			gbm_device_destroy(gbm);
			g_close(fd, NULL);
			return TRUE;
		}
		error = errno;
	}
	*why = g_strdup_printf("gbm_bo_create on %s (gbm «%s») does not create the buffer: %s", node,
	                          gbm_device_get_backend_name(gbm),
	                          error ? g_strerror(error) : "no errno");
	gbm_device_destroy(gbm);
	g_close(fd, NULL);
	return FALSE;
}

typedef struct {
	char *name;     /* renderD128 */
	char *pci;      /* 0000:03:00.0, or «~renderD128» when sysfs does not say (sorts after every real address) */
	char *driver;   /* i915, amdgpu, ast … or «?» */
	gboolean primary;
} Cand;

static void cand_free(gpointer p)
{
	Cand *c = p;

	g_free(c->name);
	g_free(c->pci);
	g_free(c->driver);
	g_free(c);
}

static char *link_base(const char *path)
{
	g_autofree char *l = g_file_read_link(path, NULL);

	return l ? g_path_get_basename(l) : NULL;
}

static gboolean file_is_one(const char *path)
{
	g_autofree char *s = NULL;

	return g_file_get_contents(path, &s, NULL, NULL) && g_strstrip(s)[0] == '1' && s[1] == 0;
}

/* boot_vga of the PCI device `pci`: first in the renderD's own device, then in any card* with the same device */
static gboolean boot_vga_of(const char *sys_dir, const char *entry, const char *pci)
{
	g_autofree char *own = g_build_filename(sys_dir, entry, "device", "boot_vga", NULL);
	g_autoptr(GDir) d = NULL;
	const char *e;

	if (g_file_test(own, G_FILE_TEST_EXISTS))
		return file_is_one(own);
	d = g_dir_open(sys_dir, 0, NULL);
	while (d && (e = g_dir_read_name(d))) {
		g_autofree char *dev = NULL, *b = NULL, *f = NULL;

		if (!g_str_has_prefix(e, "card") || strchr(e, '-'))
			continue;
		dev = g_build_filename(sys_dir, e, "device", NULL);
		b = link_base(dev);
		if (!b || strcmp(b, pci) != 0)
			continue;
		f = g_build_filename(dev, "boot_vga", NULL);
		if (g_file_test(f, G_FILE_TEST_EXISTS) && file_is_one(f))
			return TRUE;
	}
	return FALSE;
}

static gint cand_cmp(gconstpointer a, gconstpointer b)
{
	const Cand *x = *(Cand *const *)a, *y = *(Cand *const *)b;
	int r = strcmp(x->pci, y->pci);

	return r ? r : strcmp(x->name, y->name);
}

/* the BIOS primary card when no candidate (a render node that OPENS) is on it: a card-N device with boot_vga = 1 whose PCI
 * address no candidate has.  Returns the tail of a sentence, g_free, or NULL:
 *   «0000:05:00.0 (card0, driver ast) has no render node»                       (ASPEED: display only)
 *   «0000:03:00.0 (card1, driver amdgpu): its render node renderD128 is not openable here (not in /dev/dri, or no
 *    permission)»   (sysfs HAS a renderD* of that device and it does not open: a box that does not pass it, a permission)
 * ⛔ The two are different facts, and saying «no render node» for the second would be a false line in every session. */
static char *primary_without_node(const char *sys_dir, GPtrArray *cands)
{
	g_autoptr(GDir) d = g_dir_open(sys_dir, 0, NULL);
	const char *e;

	while (d && (e = g_dir_read_name(d))) {
		g_autofree char *dev = NULL, *pci = NULL, *drv = NULL, *f = NULL, *rname = NULL;
		gboolean has = FALSE;

		if (!g_str_has_prefix(e, "card") || strchr(e, '-'))
			continue;
		dev = g_build_filename(sys_dir, e, "device", NULL);
		f = g_build_filename(dev, "boot_vga", NULL);
		if (!file_is_one(f))
			continue;
		pci = link_base(dev);
		if (!pci)
			continue;
		for (guint i = 0; i < cands->len; i++)
			if (strcmp(((Cand *)cands->pdata[i])->pci, pci) == 0)
				has = TRUE;
		if (has)
			continue;
		{
			g_autofree char *dl = g_build_filename(dev, "driver", NULL);
			g_autoptr(GDir) d2 = g_dir_open(sys_dir, 0, NULL);
			const char *e2;

			drv = link_base(dl);
			while (d2 && (e2 = g_dir_read_name(d2))) {
				g_autofree char *rdev = NULL, *rpci = NULL;

				if (!g_str_has_prefix(e2, "renderD"))
					continue;
				rdev = g_build_filename(sys_dir, e2, "device", NULL);
				rpci = link_base(rdev);
				if (rpci && strcmp(rpci, pci) == 0) {
					rname = g_strdup(e2);
					break;
				}
			}
		}
		if (rname)
			return g_strdup_printf("%s (%s, driver %s): its render node %s is not openable here (not in /dev/dri, or "
			                       "no permission)",
			                       pci, e, drv ? drv : "?", rname);
		return g_strdup_printf("%s (%s, driver %s) has no render node", pci, e, drv ? drv : "?");
	}
	return NULL;
}

char *card_pick(const char *dev_dir, const char *sys_dir, card_draw_fn can_draw, card_pick_how *how,
                char **story)
{
	g_autoptr(GPtrArray) cands = g_ptr_array_new_with_free_func(cand_free);
	g_autoptr(GDir) dri = g_dir_open(dev_dir, 0, NULL);
	g_autofree char *no_node_primary = NULL;
	g_autoptr(GString) notes = g_string_new(NULL);
	const char *entry;
	Cand *primary = NULL;

	*story = NULL;
	*how = CARD_PICK_NO_NODE;
	while (dri && (entry = g_dir_read_name(dri))) {
		g_autofree char *fpath = NULL, *dev = NULL, *dl = NULL, *pci = NULL, *drv = NULL;
		Cand *c;
		gboolean real;
		int fd;

		if (!g_str_has_prefix(entry, "renderD"))
			continue;
		fpath = g_build_filename(dev_dir, entry, NULL);
		fd = g_open(fpath, O_RDWR | O_CLOEXEC, 0);
		if (fd < 0)
			continue;
		g_close(fd, NULL);
		dev = g_build_filename(sys_dir, entry, "device", NULL);
		pci = link_base(dev);
		dl = g_build_filename(dev, "driver", NULL);
		drv = link_base(dl);
		real = pci != NULL;
		c = g_new0(Cand, 1);
		c->name = g_strdup(entry);
		c->pci = real ? g_steal_pointer(&pci) : g_strdup_printf("~%s", entry);
		c->driver = drv ? g_steal_pointer(&drv) : g_strdup("?");
		c->primary = real && boot_vga_of(sys_dir, entry, c->pci);
		g_ptr_array_add(cands, c);
	}
	g_ptr_array_sort(cands, cand_cmp);
	if (cands->len == 0) {
		no_node_primary = primary_without_node(sys_dir, cands);
		*story = no_node_primary ? g_strdup_printf("no openable render node (the BIOS primary card %s)",
		                                          no_node_primary)
		                         : g_strdup("no openable /dev/dri/renderD* node");
		return NULL;
	}
	*how = CARD_PICK_NONE_CAPABLE;
	for (guint i = 0; i < cands->len; i++)
		if (((Cand *)cands->pdata[i])->primary) {
			primary = cands->pdata[i];
			break;
		}
	if (!primary)
		no_node_primary = primary_without_node(sys_dir, cands);

	/* 1 · the BIOS primary card, if it draws */
	if (primary) {
		g_autofree char *node = g_build_filename(dev_dir, primary->name, NULL);
		g_autofree char *why = NULL;

		if (!can_draw || can_draw(node, &why)) {
			*how = CARD_PICK_BIOS_PRIMARY;
			*story = g_strdup_printf("BIOS primary card (boot_vga), %s, driver %s", primary->pci,
			                         primary->driver);
			return g_steal_pointer(&node);
		}
		g_string_append_printf(notes, "the BIOS primary card %s (%s, driver %s) cannot draw: %s", primary->pci,
		                       primary->name, primary->driver, why ? why : "?");
	} else if (no_node_primary) {
		g_string_append_printf(notes, "the BIOS primary card %s", no_node_primary);
	}

	/* 2 · the capable card with the lowest PCI address */
	for (guint i = 0; i < cands->len; i++) {
		Cand *c = cands->pdata[i];
		g_autofree char *node = NULL, *why = NULL;

		if (c == primary)
			continue;
		node = g_build_filename(dev_dir, c->name, NULL);
		if (!can_draw || can_draw(node, &why)) {
			*how = CARD_PICK_PCI_FIRST;
			*story = g_strdup_printf("first capable card by PCI address, %s, driver %s%s%s", c->pci, c->driver,
			                         notes->len ? "; " : "", notes->str);
			return g_steal_pointer(&node);
		}
		if (notes->len)
			g_string_append(notes, "; ");
		g_string_append_printf(notes, "%s (%s) cannot draw: %s", c->pci, c->name, why ? why : "?");
	}
	*story = g_strdup_printf("no capable card: %s", notes->len ? notes->str : "?");
	return NULL;
}

gboolean card_pick_service_driver(const char *driver)
{
	static const char *const service[] = { "ast", "mgag200", "hibmc-drm", "hibmc", NULL };

	for (guint i = 0; driver && service[i]; i++)
		if (strcmp(driver, service[i]) == 0)
			return TRUE;
	return FALSE;
}

char *card_pick_driver_of(const char *sys_dir, const char *node)
{
	g_autofree char *base = node ? g_path_get_basename(node) : NULL;
	g_autofree char *p = base ? g_build_filename(sys_dir, base, "device", "driver", NULL) : NULL;

	return p ? link_base(p) : NULL;
}

char *card_pick_desktop(card_pick_how *how, char **story)
{
	return card_pick("/dev/dri", "/sys/class/drm", card_can_draw, how, story);
}

char *card_pick_driver_of_chardev(const char *sys_root, unsigned major, unsigned minor)
{
	g_autofree char *p = g_strdup_printf("%s/dev/char/%u:%u/device/driver", sys_root, major, minor);

	return link_base(p);
}
