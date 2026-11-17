/*
 * render_node — which card encodes: the compositor's.  See `render_node.h`.
 */
#include "render_node.h"
#include "kwin.h"
#include "card_pick.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>
#include <wayland-client.h>

#include "linux-dmabuf-unstable-v1-client-protocol.h"

typedef struct {
	struct zwp_linux_dmabuf_v1 *dmabuf;
	uint32_t version;
	dev_t main;
	bool main_known, done;
} Ask;

static void reg_global(void *data, struct wl_registry *r, uint32_t name,
                       const char *interface, uint32_t version)
{
	Ask *a = data;

	if (strcmp(interface, zwp_linux_dmabuf_v1_interface.name) == 0 && !a->dmabuf) {
		/* ⚠ At most v4: it is the one with `main_device` (as `wlroots.c`). */
		a->version = version < 4 ? version : 4;
		a->dmabuf = wl_registry_bind(r, name, &zwp_linux_dmabuf_v1_interface, a->version);
	}
}

static void reg_remove(void *data, struct wl_registry *r, uint32_t name) {}

static const struct wl_registry_listener REG = { reg_global, reg_remove };

static void fb_done(void *data, struct zwp_linux_dmabuf_feedback_v1 *f)
{
	((Ask *)data)->done = true;
}

/* ⛔ The descriptor is ours as soon as it arrives: closed, or one is lost per ask. */
static void fb_table(void *data, struct zwp_linux_dmabuf_feedback_v1 *f, int32_t fd,
                     uint32_t size)
{
	close(fd);
}

static void fb_main(void *data, struct zwp_linux_dmabuf_feedback_v1 *f, struct wl_array *dev)
{
	Ask *a = data;

	/* ⚠ A size that is not a `dev_t` is not guessed: «not known». */
	if (dev->size == sizeof(dev_t)) {
		memcpy(&a->main, dev->data, sizeof(dev_t));
		a->main_known = true;
	}
}

static void fb_tdone(void *d, struct zwp_linux_dmabuf_feedback_v1 *f) {}
static void fb_ttarget(void *d, struct zwp_linux_dmabuf_feedback_v1 *f, struct wl_array *a) {}
static void fb_tformats(void *d, struct zwp_linux_dmabuf_feedback_v1 *f, struct wl_array *a) {}
static void fb_tflags(void *d, struct zwp_linux_dmabuf_feedback_v1 *f, uint32_t b) {}

static const struct zwp_linux_dmabuf_feedback_v1_listener FB = {
	.done = fb_done,
	.format_table = fb_table,
	.main_device = fb_main,
	.tranche_done = fb_tdone,
	.tranche_target_device = fb_ttarget,
	.tranche_formats = fb_tformats,
	.tranche_flags = fb_tflags,
};

static int64_t now_ms(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return (int64_t)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}

/* One round trip with a ceiling: `wl_display_roundtrip()` has none, and a
 * hung compositor would hang the child.  false = wire dropped or expired. */
static bool roundtrip_by(struct wl_display *d, int64_t expiry, bool *flag)
{
	while (!*flag) {
		struct pollfd pfd;
		int64_t left;

		while (wl_display_prepare_read(d) != 0)
			if (wl_display_dispatch_pending(d) < 0)
				return false;
		if (*flag) {
			wl_display_cancel_read(d);
			break;
		}
		if (wl_display_flush(d) < 0 && errno != EAGAIN) {
			wl_display_cancel_read(d);
			return false;
		}
		left = expiry - now_ms();
		if (left <= 0) {
			wl_display_cancel_read(d);
			return false;
		}
		pfd.fd = wl_display_get_fd(d);
		pfd.events = POLLIN;
		int r = poll(&pfd, 1, (int)left);

		if (r <= 0) {
			wl_display_cancel_read(d);
			if (r < 0 && errno == EINTR)
				continue;
			return false;
		}
		if (wl_display_read_events(d) < 0 || wl_display_dispatch_pending(d) < 0)
			return false;
	}
	return true;
}

static void sync_done(void *data, struct wl_callback *cb, uint32_t serial)
{
	*(bool *)data = true;
}

static const struct wl_callback_listener SYNC = { sync_done };

/* The same as `node_from_device()` in `wlroots.c`: the sysfs folder of the
 * `dev_t` (primary or render node) lists the card's `renderD*`. */
static bool node_of_device(dev_t dev, char *out, size_t n)
{
	char folder[96];
	DIR *dir;
	struct dirent *e;
	bool found = false;

	snprintf(folder, sizeof folder, "/sys/dev/char/%u:%u/device/drm", major(dev), minor(dev));
	dir = opendir(folder);
	if (!dir)
		return false;
	while ((e = readdir(dir)))
		if (strncmp(e->d_name, "renderD", 7) == 0) {
			snprintf(out, n, "/dev/dri/%s", e->d_name);
			found = true;
			break;
		}
	closedir(dir);
	return found;
}

bool render_node_of_compositor(char *out, size_t n, char *why, size_t wn, bool *reached, char *driver, size_t dn)
{
	char socket[64] = "";
	struct wl_display *d;
	struct wl_registry *reg;
	struct zwp_linux_dmabuf_feedback_v1 *fb = NULL;
	Ask a = { 0 };
	int64_t expiry = now_ms() + 2000;
	bool synced = false, ok = false;
	struct wl_callback *cb;

	*reached = false;
	out[0] = 0;
	if (driver && dn)
		driver[0] = 0;
	d = kwin_display_open(socket, sizeof socket);
	if (!d) {
		snprintf(why, wn, "no Wayland compositor reachable yet");
		return false;
	}
	*reached = true;
	reg = wl_display_get_registry(d);
	wl_registry_add_listener(reg, &REG, &a);
	cb = wl_display_sync(d);
	wl_callback_add_listener(cb, &SYNC, &synced);
	if (!roundtrip_by(d, expiry, &synced)) {
		snprintf(why, wn, "the compositor on %s did not answer the registry in 2 s", socket);
		goto out;
	}
	if (!a.dmabuf) {
		snprintf(why, wn, "the compositor on %s offers no linux-dmabuf", socket);
		goto out;
	}
	if (a.version < 4) {
		snprintf(why, wn, "the compositor on %s offers linux-dmabuf v%u: main_device "
		         "needs v4", socket, a.version);
		goto out;
	}
	fb = zwp_linux_dmabuf_v1_get_default_feedback(a.dmabuf);
	zwp_linux_dmabuf_feedback_v1_add_listener(fb, &FB, &a);
	if (!roundtrip_by(d, expiry, &a.done)) {
		snprintf(why, wn, "the compositor on %s did not close its dmabuf feedback in 2 s",
		         socket);
		goto out;
	}
	if (!a.main_known) {
		snprintf(why, wn, "the compositor on %s did not state its main_device", socket);
		goto out;
	}
	if (driver && dn) {
		char *drv = card_pick_driver_of_chardev("/sys", major(a.main), minor(a.main));

		snprintf(driver, dn, "%s", drv ? drv : "");
		g_free(drv);
	}
	if (!node_of_device(a.main, out, n)) {
		/* ⚠ A display-only card (simpledrm, a KMS-only panel) has no render node. */
		snprintf(why, wn, "the compositor's card (%u:%u) has no renderD* node",
		         major(a.main), minor(a.main));
		goto out;
	}
	{
		int fd = open(out, O_RDWR | O_CLOEXEC);

		if (fd < 0) {
			snprintf(why, wn, "the compositor's card %s does not open: %s", out,
			         strerror(errno));
			out[0] = 0;
			goto out;
		}
		close(fd);
	}
	ok = true;
out:
	if (fb)
		zwp_linux_dmabuf_feedback_v1_destroy(fb);
	if (a.dmabuf)
		zwp_linux_dmabuf_v1_destroy(a.dmabuf);
	wl_registry_destroy(reg);
	wl_callback_destroy(cb); /* the sync callback is ours to destroy (the listener does not) */
	wl_display_disconnect(d);
	return ok;
}

/* The last path component of the link `link`, or «?». */
static void link_name(const char *link, char *out, size_t n)
{
	char target[PATH_MAX];
	ssize_t len = readlink(link, target, sizeof target - 1);
	const char *slash;

	if (len <= 0) {
		snprintf(out, n, "?");
		return;
	}
	target[len] = 0;
	slash = strrchr(target, '/');
	slash = slash ? slash + 1 : target;
	len = (ssize_t)strlen(slash);
	if ((size_t)len >= n)
		len = (ssize_t)n - 1;
	memcpy(out, slash, (size_t)len);
	out[len] = 0;
}

static void first_line(const char *file, char *out, size_t n)
{
	FILE *f = fopen(file, "r");

	snprintf(out, n, "?");
	if (!f)
		return;
	if (fgets(out, (int)n, f))
		out[strcspn(out, "\n")] = 0;
	else
		snprintf(out, n, "?");
	fclose(f);
}

void render_node_describe(const char *node, char *out, size_t n)
{
	const char *base = strrchr(node, '/');
	char p[160], pci[64], drv[64], ven[16], dev[16];

	base = base ? base + 1 : node;
	snprintf(p, sizeof p, "/sys/class/drm/%s/device", base);
	link_name(p, pci, sizeof pci);
	snprintf(p, sizeof p, "/sys/class/drm/%s/device/driver", base);
	link_name(p, drv, sizeof drv);
	snprintf(p, sizeof p, "/sys/class/drm/%s/device/vendor", base);
	first_line(p, ven, sizeof ven);
	snprintf(p, sizeof p, "/sys/class/drm/%s/device/device", base);
	first_line(p, dev, sizeof dev);
	snprintf(out, n, "%s, driver %s, %s:%s", pci, drv,
	         strncmp(ven, "0x", 2) == 0 ? ven + 2 : ven,
	         strncmp(dev, "0x", 2) == 0 ? dev + 2 : dev);
}

bool render_node_is_drm(const char *path, char *why, size_t wn)
{
	struct stat st;

	if (!path || strncmp(path, "/dev/dri/", 9) != 0) {
		snprintf(why, wn, "not under /dev/dri/");
		return false;
	}
	if (stat(path, &st) != 0) {
		snprintf(why, wn, "it does not exist here (%s)", strerror(errno));
		return false;
	}
	if (!S_ISCHR(st.st_mode)) {
		snprintf(why, wn, "not a character device");
		return false;
	}
	if (major(st.st_rdev) != RENDER_NODE_DRM_MAJOR) {
		snprintf(why, wn, "character device %u:%u, not DRM (major %u)", major(st.st_rdev),
		         minor(st.st_rdev), RENDER_NODE_DRM_MAJOR);
		return false;
	}
	if (wn)
		why[0] = 0;
	return true;
}

bool render_node_same(const char *a, const char *b)
{
	struct stat sa, sb;

	if (!a || !b)
		return false;
	if (stat(a, &sa) == 0 && stat(b, &sb) == 0 && S_ISCHR(sa.st_mode) && S_ISCHR(sb.st_mode))
		return sa.st_rdev == sb.st_rdev;
	return strcmp(a, b) == 0;
}
