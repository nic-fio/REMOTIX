/*
 * test.c — unit test of the choice of the desktop's card, src/card_pick.c (DECISIONS §11.37 addendum, 27 Oct 2026).
 * The rule: the BIOS primary card (PCI boot_vga = 1) if it is capable; else the capable card with the lowest PCI address
 * (NOT the lowest node name: renderD128 / renderD129 swap between boots).  «Capable» = a render node that opens and, here,
 * a fake `can_draw`.
 *
 * HOW: the REAL card_pick.c is #included; a FAKE /dev/dri and /sys/class/drm are built in a temporary directory
 * (renderD* files; renderDN/device -> a PCI directory with boot_vga and driver; card0/device the same for a card with no
 * render node).  Cases:
 *   1 boot_vga card capable        two cards, the primary one has the higher PCI address and the higher node name: it wins
 *   2 same, node names swapped      the answer is the same CARD (same PCI), under the other name
 *   3 primary without render node   ASPEED «ast» (card0 only, boot_vga = 1): the capable card with the lowest PCI; the story says so
 *   4 no boot_vga anywhere          lowest PCI address, not lowest name; swapped names: same card
 *   5 primary cannot draw           falls to the lowest PCI among the others; the story names the primary and why
 *   6 boot_vga only on card0/device (the renderD's device lacks the file): still found
 *   7 none can draw / no node       NULL, NONE_CAPABLE / NO_NODE
 *   8 one card                      that card; can_draw NULL = «opens» is enough
 *   9 no sysfs at all (a container) falls back to the node name, as before
 *  10 service cards                card_pick_service_driver(): ast, mgag200, hibmc-drm yes; i915, amdgpu, nvidia, virtio_gpu, NULL no;
 *                                  card_pick_driver_of() reads the driver of a render node through sysfs
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-costruzione sh -c '
 *     cd /tmp && gcc -g -O1 -std=gnu11 -D_GNU_SOURCE -Wall -Wextra -I/albero/src $(pkg-config --cflags glib-2.0) \
 *        /albero/benches/unit/card-pick/test.c -o test $(pkg-config --libs glib-2.0) && ./test'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "../../../src/card_pick.c"

#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>

static int failures, passed;

static void check(int cond, const char *what)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", what);
	if (cond)
		passed++;
	else
		failures++;
}

static char root[256];

static void put(const char *rel, const char *text)
{
	char p[512];
	FILE *f;

	snprintf(p, sizeof p, "%s/%s", root, rel);
	f = fopen(p, "w");
	if (f) {
		fputs(text, f);
		fclose(f);
	}
}

static void mkd(const char *rel)
{
	char p[512];

	snprintf(p, sizeof p, "%s/%s", root, rel);
	g_mkdir_with_parents(p, 0755);
}

/* a PCI device: pci/<addr>/{boot_vga,driver -> ../../drivers/<drv>} */
static void pci(const char *addr, const char *drv, int boot)
{
	char rel[256], tgt[256], l[512];

	snprintf(rel, sizeof rel, "pci/%s", addr);
	mkd(rel);
	snprintf(rel, sizeof rel, "drivers/%s", drv);
	mkd(rel);
	if (boot >= 0) {
		snprintf(rel, sizeof rel, "pci/%s/boot_vga", addr);
		put(rel, boot ? "1\n" : "0\n");
	}
	snprintf(l, sizeof l, "%s/pci/%s/driver", root, addr);
	snprintf(tgt, sizeof tgt, "%s/drivers/%s", root, drv);
	(void)!symlink(tgt, l);
}

/* the sysfs entry `name` (renderD129 or card0) of the device `addr`; `dev` = also create dev/<name> */
static void entry(const char *name, const char *addr, int dev)
{
	char rel[256], l[512], tgt[512];

	snprintf(rel, sizeof rel, "sys/%s", name);
	mkd(rel);
	snprintf(l, sizeof l, "%s/sys/%s/device", root, name);
	snprintf(tgt, sizeof tgt, "%s/pci/%s", root, addr);
	(void)!symlink(tgt, l);
	if (dev) {
		snprintf(rel, sizeof rel, "dev/%s", name);
		put(rel, "");
	}
}

static void fresh(void)
{
	snprintf(root, sizeof root, "/tmp/card-pick-test-XXXXXX");
	if (!mkdtemp(root))
		exit(2);
	mkd("dev");
	mkd("sys");
}

static void wipe(void)
{
	char cmd[300];

	snprintf(cmd, sizeof cmd, "rm -rf '%s'", root);
	(void)!system(cmd);
}

static const char *bad_node; /* can_draw says no to this node name */
static gboolean draw(const char *node, char **why)
{
	if (bad_node && g_str_has_suffix(node, bad_node)) {
		*why = g_strdup("gbm_bo_create fails");
		return FALSE;
	}
	return TRUE;
}
static gboolean never(const char *node, char **why)
{
	(void)node;
	*why = g_strdup("nothing draws");
	return FALSE;
}

static char *pick(card_draw_fn f, card_pick_how *how, char **story)
{
	char dev[300], sys[300];

	snprintf(dev, sizeof dev, "%s/dev", root);
	snprintf(sys, sizeof sys, "%s/sys", root);
	return card_pick(dev, sys, f, how, story);
}

static int is(const char *node, const char *name)
{
	return node && g_str_has_suffix(node, name);
}

int main(void)
{
	card_pick_how how;
	char *node, *story;

	puts("1 · the BIOS primary card is capable: it wins over the lower PCI address");
	fresh();
	pci("0000:00:02.0", "i915", 0);
	pci("0000:03:00.0", "amdgpu", 1);
	entry("renderD128", "0000:00:02.0", 1);
	entry("renderD129", "0000:03:00.0", 1);
	bad_node = NULL;
	node = pick(draw, &how, &story);
	check(is(node, "/renderD129") && how == CARD_PICK_BIOS_PRIMARY, "renderD129 (amdgpu, boot_vga) is chosen, BIOS_PRIMARY");
	check(story && strstr(story, "BIOS primary") && strstr(story, "0000:03:00.0") && strstr(story, "amdgpu"),
	      "the story says BIOS primary, PCI and driver");
	g_free(node);
	g_free(story);
	wipe();

	puts("2 · the same machine after the node names swapped");
	fresh();
	pci("0000:00:02.0", "i915", 0);
	pci("0000:03:00.0", "amdgpu", 1);
	entry("renderD129", "0000:00:02.0", 1);
	entry("renderD128", "0000:03:00.0", 1);
	node = pick(draw, &how, &story);
	check(is(node, "/renderD128") && how == CARD_PICK_BIOS_PRIMARY, "now renderD128: the same CARD (0000:03:00.0)");
	check(story && strstr(story, "0000:03:00.0"), "the story names the same PCI address");
	g_free(node);
	g_free(story);
	wipe();

	puts("3 · the BIOS primary card has no render node (ASPEED ast, a server's service card)");
	fresh();
	pci("0000:05:00.0", "ast", 1);
	pci("0000:0a:00.0", "amdgpu", 0);
	pci("0000:00:02.0", "i915", 0);
	entry("card0", "0000:05:00.0", 0);
	entry("renderD128", "0000:0a:00.0", 1);
	entry("renderD129", "0000:00:02.0", 1);
	node = pick(draw, &how, &story);
	check(is(node, "/renderD129") && how == CARD_PICK_PCI_FIRST, "renderD129 (i915, 00:02.0) is chosen, PCI_FIRST");
	check(story && strstr(story, "first capable card by PCI") && strstr(story, "0000:05:00.0") &&
	          strstr(story, "no render node"),
	      "the story says: by PCI, and that the BIOS primary 05:00.0 has no render node");
	g_free(node);
	g_free(story);
	wipe();

	puts("4 · no boot_vga anywhere: the lowest PCI address, not the lowest name");
	fresh();
	pci("0000:0a:00.0", "amdgpu", -1);
	pci("0000:00:02.0", "i915", -1);
	entry("renderD128", "0000:0a:00.0", 1);
	entry("renderD129", "0000:00:02.0", 1);
	node = pick(draw, &how, &story);
	check(is(node, "/renderD129") && how == CARD_PICK_PCI_FIRST, "renderD129 (00:02.0), not renderD128");
	g_free(node);
	g_free(story);
	wipe();
	fresh(); /* swapped */
	pci("0000:0a:00.0", "amdgpu", -1);
	pci("0000:00:02.0", "i915", -1);
	entry("renderD129", "0000:0a:00.0", 1);
	entry("renderD128", "0000:00:02.0", 1);
	node = pick(draw, &how, &story);
	check(is(node, "/renderD128"), "swapped names: renderD128 now, the same card (00:02.0)");
	g_free(node);
	g_free(story);
	wipe();

	puts("5 · the BIOS primary card cannot draw");
	fresh();
	pci("0000:00:02.0", "i915", 0);
	pci("0000:0a:00.0", "amdgpu", 0);
	pci("0000:03:00.0", "virtio-pci", 1);
	entry("renderD128", "0000:03:00.0", 1);
	entry("renderD129", "0000:0a:00.0", 1);
	entry("renderD130", "0000:00:02.0", 1);
	bad_node = "/renderD128";
	node = pick(draw, &how, &story);
	check(is(node, "/renderD130") && how == CARD_PICK_PCI_FIRST, "renderD130 (00:02.0) chosen, PCI_FIRST");
	check(story && strstr(story, "0000:03:00.0") && strstr(story, "cannot draw") && strstr(story, "gbm_bo_create fails"),
	      "the story names the primary card and why it cannot draw");
	g_free(node);
	g_free(story);
	bad_node = NULL;
	wipe();

	puts("6 · boot_vga found only through card1/device");
	fresh();
	pci("0000:00:02.0", "i915", 0);
	pci("0000:03:00.0", "amdgpu", -1); /* the renderD's device has NO boot_vga file */
	entry("renderD128", "0000:00:02.0", 1);
	entry("renderD129", "0000:03:00.0", 1);
	/* card1 reaches the same PCI address through another path, and that directory has the file */
	mkd("other/0000:03:00.0");
	put("other/0000:03:00.0/boot_vga", "1\n");
	mkd("sys/card1");
	{
		char l[512], tgt[512];

		snprintf(l, sizeof l, "%s/sys/card1/device", root);
		snprintf(tgt, sizeof tgt, "%s/other/0000:03:00.0", root);
		(void)!symlink(tgt, l);
	}
	node = pick(draw, &how, &story);
	check(is(node, "/renderD129") && how == CARD_PICK_BIOS_PRIMARY, "renderD129 chosen as the BIOS primary card");
	g_free(node);
	g_free(story);
	wipe();

	puts("7 · nothing draws / nothing opens");
	fresh();
	pci("0000:00:02.0", "i915", 1);
	entry("renderD128", "0000:00:02.0", 1);
	node = pick(never, &how, &story);
	check(node == NULL && how == CARD_PICK_NONE_CAPABLE && story && strstr(story, "cannot draw"),
	      "NULL, NONE_CAPABLE, the story says why");
	g_free(story);
	wipe();
	fresh();
	node = pick(draw, &how, &story);
	check(node == NULL && how == CARD_PICK_NO_NODE && story, "no node at all: NULL, NO_NODE");
	g_free(story);
	wipe();
	fresh();
	pci("0000:05:00.0", "ast", 1);
	entry("card0", "0000:05:00.0", 0);
	node = pick(draw, &how, &story);
	check(node == NULL && how == CARD_PICK_NO_NODE && story && strstr(story, "0000:05:00.0"),
	      "only an ast card with no render node: NO_NODE, the story names it");
	g_free(story);
	wipe();

	puts("8 · one card; can_draw NULL");
	fresh();
	pci("0000:00:02.0", "i915", 1);
	entry("renderD128", "0000:00:02.0", 1);
	node = pick(NULL, &how, &story);
	check(is(node, "/renderD128") && how == CARD_PICK_BIOS_PRIMARY, "the only card, NULL can_draw");
	g_free(node);
	g_free(story);
	wipe();

	puts("9 · no sysfs at all (a container): by node name, as before");
	fresh();
	put("dev/renderD129", "");
	put("dev/renderD128", "");
	node = pick(NULL, &how, &story);
	check(is(node, "/renderD128") && how == CARD_PICK_PCI_FIRST, "renderD128 (lowest name)");
	g_free(node);
	g_free(story);
	wipe();

	puts("10 · service / BMC cards");
	check(card_pick_service_driver("ast") && card_pick_service_driver("mgag200") && card_pick_service_driver("hibmc-drm"),
	      "ast, mgag200, hibmc-drm are service cards");
	check(!card_pick_service_driver("i915") && !card_pick_service_driver("amdgpu") && !card_pick_service_driver("nvidia") &&
	          !card_pick_service_driver("virtio_gpu") && !card_pick_service_driver("") && !card_pick_service_driver(NULL),
	      "i915, amdgpu, nvidia, virtio_gpu, empty and NULL are not");
	fresh();
	pci("0000:05:00.0", "mgag200", 1);
	entry("renderD128", "0000:05:00.0", 1);
	{
		char sys[300], *d;

		snprintf(sys, sizeof sys, "%s/sys", root);
		d = card_pick_driver_of(sys, "/dev/dri/renderD128");
		check(d && strcmp(d, "mgag200") == 0 && card_pick_service_driver(d), "driver of renderD128 is mgag200, a service card");
		g_free(d);
		d = card_pick_driver_of(sys, "/dev/dri/renderD999");
		check(d == NULL, "an unknown node has no driver");
		g_free(d);
	}
	wipe();

	printf("%d passed, %d failed\n", passed, failures);
	return failures ? 1 : 0;
}
