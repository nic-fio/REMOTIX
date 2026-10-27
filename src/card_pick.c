/*
 * card_pick — see `card_pick.h`.
 */
#include "card_pick.h"

#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <glib/gstdio.h>

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

/* the BIOS primary card when it has NO render node (ASPEED «ast» on a server): a card-N device with boot_vga = 1 whose
 * PCI address no candidate has.  Returns «pci (driver)» or NULL. */
static char *primary_without_node(const char *sys_dir, GPtrArray *cands)
{
	g_autoptr(GDir) d = g_dir_open(sys_dir, 0, NULL);
	const char *e;

	while (d && (e = g_dir_read_name(d))) {
		g_autofree char *dev = NULL, *pci = NULL, *drv = NULL, *f = NULL;
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

			drv = link_base(dl);
		}
		return g_strdup_printf("%s (%s, driver %s)", pci, e, drv ? drv : "?");
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
		*story = no_node_primary ? g_strdup_printf("no openable render node (the BIOS primary card %s has none)",
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
		g_string_append_printf(notes, "the BIOS primary card %s has no render node", no_node_primary);
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
