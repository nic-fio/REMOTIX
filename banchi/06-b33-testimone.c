/*
 * 06-b33-testimone.c — ⭐ THE RECEIVING SIDE, without a browser.  Sub-phase 6.1.
 *
 *   ./06-b33-testimone [--size 1264x800]
 *
 * ⛔ It is `04-b24-testimone.c` COPIED, with **one** addition and not one line
 *    fewer: the `RITELA` line, which says when the window changes size under
 *    it.  It is needed because in this sub-phase the canvas size changes ON
 *    REATTACH, and without that line «the compositor resized the
 *    screen» and «nothing happened» look the same — from the RECEIVING
 *    SIDE, which is the only one that counts (`CODER.md` §3.8).
 *
 * ⚠ The rest is B24's and has already paid its price (the browser that did not
 *   ask for the page, the monitor chosen by name and not hoped for): it is not
 *   rewritten.
 *
 * It opens a fullscreen window **on the monitor of the requested size**,
 * listens to `wl_pointer` and `wl_keyboard`, and prints one JSON line for
 * every event the compositor delivers to it.  Nothing else.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY NOT THE BROWSER, WHICH WAS THE INSTRUMENT ALREADY CERTIFIED (S7)
 *
 * `[M]` 14 Aug 2026, test machine, user `prova`: Firefox `--kiosk`
 * in the headless session **starts and never asks for the page**.  Measured three
 * times: process alive, state `S`, ⛔ **zero HTTP requests after 149 seconds**,
 * Firefox log empty.  With a new profile, with a reused one, with and
 * without a terminal.  ⚠ The cause was NOT found, and nobody pretended
 * otherwise: it is written in the report as something that did not work.
 *
 * ⇒ Another receiving side was needed, and this one is **closer to the truth**,
 *   not a worse fallback: between `libei` and the page there are Mutter *and* the
 *   browser; here there is only Mutter.  What this window sees is
 *   exactly what the compositor delivers to any window.
 *
 * ⚠ AND WHAT IS LOST, said instead of kept quiet: `RCP.md` §7.3 measured the
 *   sign on `deltaY` of a `wheel` event, that is one floor higher.  The
 *   bridge between the two is the convention of `wl_pointer.axis`, which the
 *   specification fixes: *«the value is positive in the direction the content moves»* — that is
 *   positive `axis` ⇔ the content goes down ⇔ positive `deltaY`.  The bridge is
 *   `[S]`, not `[M]`: whoever wants the whole chain should redo S7 with the page.
 *
 * ---------------------------------------------------------------------------
 * ⭐ AND THE MONITOR IS CHOSEN BY NAME, NOT HOPED FOR — form E2
 *
 * `xdg_toplevel_set_fullscreen(NULL)` lets the compositor choose, and with
 * two monitors in the session the window can end up on the one that is not ours:
 * the injection would go elsewhere and this program would print a silence that
 * reads as «the input does not arrive».  ⇒ We scan the `wl_output`s, we
 * take the one of the requested size, and ⛔ **if there is none we exit saying so**.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>

#include "xdg-shell-client-protocol.h"

static struct wl_compositor *compositor;
static struct wl_shm *mem_buf;
static struct xdg_wm_base *shell;
static struct wl_seat *slot;
static struct wl_surface *surface;
static struct xdg_surface *xdg_sup;
static struct xdg_toplevel *window;
static struct wl_pointer *pointer;
static struct wl_keyboard *keyboard;

#define OUTPUT_MAX 8
static struct
{
	struct wl_output *output;
	int32_t l, a;
	char name[64];
} screens[OUTPUT_MAX];
static int how_many_screens;

static uint32_t intended_w = 1600, intended_h = 900;
static int chosen = -1;
static bool configured;
static int32_t width = 1600, height = 900;
/* The size DECLARED in the last line: it serves to write `RITELA` only when
 * it really changes, and not at every `configure`. */
static int32_t vista_l, vista_a;
static unsigned long counter;

/* ⛔ One line per event, and ALWAYS with a growing `n`: it is the denominator.
 *    «Nothing arrived» and «I did not print» look the same
 *    without a counter that grows. */
static void line(const char *shape, ...)
{
	va_list a;

	printf("{\"n\":%lu,", ++counter);
	va_start(a, shape);
	vprintf(shape, a);
	va_end(a);
	printf("}\n");
	fflush(stdout);
}

/* ------------------------------------------------------------------ *
 *  The pointer
 * ------------------------------------------------------------------ */
static void p_enter(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sup,
                    wl_fixed_t x, wl_fixed_t y)
{
	line("\"type\":\"PUNTATORE_ENTRA\",\"x\":%.1f,\"y\":%.1f", wl_fixed_to_double(x),
	     wl_fixed_to_double(y));
}
static void p_leave(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sup)
{
	line("\"type\":\"PUNTATORE_ESCE\"");
}
static void p_moves(void *d, struct wl_pointer *p, uint32_t t, wl_fixed_t x, wl_fixed_t y)
{
	/* ⛔ Coordinates LOCAL TO THE SURFACE: with a fullscreen window
	 *    they are the position on the monitor, that is exactly what we
	 *    asked of `input_pointer`.  The comparison is direct. */
	line("\"type\":\"POINTER\",\"x\":%.1f,\"y\":%.1f", wl_fixed_to_double(x),
	     wl_fixed_to_double(y));
}
static void p_button(void *d, struct wl_pointer *p, uint32_t s, uint32_t t, uint32_t button,
                      uint32_t state)
{
	/* ⭐ `wl_pointer.button` carries the **evdev** code: `BTN_LEFT` = 0x110 =
	 *    272, the same number we sent.  No translation in
	 *    between, so the comparison is between the same quantity. */
	line("\"type\":\"BUTTON\",\"button\":%u,\"pressed\":%u", button, state);
}
static void p_axis(void *d, struct wl_pointer *p, uint32_t t, uint32_t axis, wl_fixed_t value)
{
	line("\"type\":\"ASSE\",\"axis\":%u,\"value\":%.2f", axis, wl_fixed_to_double(value));
}
static void p_border(void *d, struct wl_pointer *p) {}
static void p_source(void *d, struct wl_pointer *p, uint32_t s)
{
	line("\"type\":\"ASSE_SORGENTE\",\"sorgente\":%u", s);
}
static void p_stop(void *d, struct wl_pointer *p, uint32_t t, uint32_t axis) {}
static void p_discrete(void *d, struct wl_pointer *p, uint32_t axis, int32_t steps)
{
	line("\"type\":\"ASSE_DISCRETO\",\"axis\":%u,\"steps\":%d", axis, steps);
}
static void p_120(void *d, struct wl_pointer *p, uint32_t axis, int32_t v120)
{
	/* ⭐⭐ THIS IS THE MEASUREMENT OF THE SIGN, and in the same unit as the protocol:
	 *     `RCP.md` §7.3 counts in units of 120, and `axis_value120` carries 120. */
	line("\"type\":\"ASSE_120\",\"axis\":%u,\"v120\":%d", axis, v120);
}
static void p_direction(void *d, struct wl_pointer *p, uint32_t axis, uint32_t dir) {}

static const struct wl_pointer_listener pointer_listener = {
	.enter = p_enter,
	.leave = p_leave,
	.motion = p_moves,
	.button = p_button,
	.axis = p_axis,
	.frame = p_border,
	.axis_source = p_source,
	.axis_stop = p_stop,
	.axis_discrete = p_discrete,
	.axis_value120 = p_120,
	.axis_relative_direction = p_direction,
};

/* ------------------------------------------------------------------ *
 *  The keyboard
 * ------------------------------------------------------------------ */
static void t_keymap(void *d, struct wl_keyboard *k, uint32_t format, int32_t fd, uint32_t measure)
{
	line("\"type\":\"KEYMAP\",\"format\":%u,\"byte\":%u", format, measure);
	close(fd);
}
static void t_enter(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sup,
                    struct wl_array *keys)
{
	line("\"type\":\"FUOCO\",\"inside\":1");
}
static void t_leave(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sup)
{
	line("\"type\":\"FUOCO\",\"inside\":0");
}
static void t_key(void *d, struct wl_keyboard *k, uint32_t s, uint32_t t, uint32_t keystroke,
                    uint32_t state)
{
	/* ⛔ `wl_keyboard.key` carries the **evdev** code, the same one we
	 *    sent to `input_position`.  `KEY_A` = 30 on both sides. */
	line("\"type\":\"KEY\",\"code\":%u,\"pressed\":%u", keystroke, state);
}
static void t_modifiers(void *d, struct wl_keyboard *k, uint32_t s, uint32_t premuti,
                           uint32_t latched, uint32_t blocked, uint32_t group)
{
	line("\"type\":\"MODIFICATORI\",\"premuti\":%u,\"bloccati\":%u,\"gruppo\":%u", premuti,
	     blocked, group);
}
static void t_repetition(void *d, struct wl_keyboard *k, int32_t rate, int32_t delay) {}

static const struct wl_keyboard_listener keyboard_listener = {
	.keymap = t_keymap,
	.enter = t_enter,
	.leave = t_leave,
	.key = t_key,
	.modifiers = t_modifiers,
	.repeat_info = t_repetition,
};

/*
 * ⛔⛔⛔ AND THE CAPABILITY GOES AWAY AND COMES BACK — defect of the WITNESS found on 21
 *       Aug 2026, and it made the instrument mute without saying a word.
 *
 * This function hooked `wl_pointer` **only once** (`&& !pointer`) and
 * never let go of it.  ⇒ When the seat loses the capability and gets it back, the
 * compositor has destroyed its pointer: our object stays there,
 * ⛔ **receives nothing more and gives no error**, and on the return
 * `!pointer` is false so we never hook again.
 *
 * ⚠ It is **the same defect** that `STUDI.md` §gnome §9 describes for `libei` —
 *   *«the pointer to the old device stops working without an error»* —
 *   but on the Wayland side, and in the instrument instead of the product.  ⭐ It is the
 *   worst way a bench can break: the witness says «I saw
 *   nothing», and whoever reads it blames the product.
 *
 * `[M]` It was seen while working on cure «C»: on reattach of the EIS channel the seat
 *       goes **3 → 1 → 0 → 1 → 3** (on the session without a monitor our
 *       virtual devices are the ONLY ones of the seat), and from then on the
 *       witness did not see a single event.
 *
 * ⇒ We let go when the capability drops, and hook again when it returns.  It is
 *   also what a well-written Wayland client must do.
 */
static void seat_on_capabilities(void *d, struct wl_seat *s, uint32_t cap)
{
	line("\"type\":\"POSTO\",\"capacita\":%u", cap);

	if ((cap & WL_SEAT_CAPABILITY_POINTER) && !pointer)
	{
		pointer = wl_seat_get_pointer(s);
		wl_pointer_add_listener(pointer, &pointer_listener, NULL);
		line("\"type\":\"POSTO_PUNTATORE\",\"state\":\"agganciato\"");
	}
	else if (!(cap & WL_SEAT_CAPABILITY_POINTER) && pointer)
	{
		wl_pointer_release(pointer);
		pointer = NULL;
		/* ⛔ And it is WRITTEN: without this line «the seat lost the pointer» and
		 *    «nothing arrived» look the same in the file. */
		line("\"type\":\"POSTO_PUNTATORE\",\"state\":\"mollato\"");
	}

	if ((cap & WL_SEAT_CAPABILITY_KEYBOARD) && !keyboard)
	{
		keyboard = wl_seat_get_keyboard(s);
		wl_keyboard_add_listener(keyboard, &keyboard_listener, NULL);
		line("\"type\":\"POSTO_TASTIERA\",\"state\":\"agganciata\"");
	}
	else if (!(cap & WL_SEAT_CAPABILITY_KEYBOARD) && keyboard)
	{
		wl_keyboard_release(keyboard);
		keyboard = NULL;
		line("\"type\":\"POSTO_TASTIERA\",\"state\":\"mollata\"");
	}
}
static void seat_on_name(void *d, struct wl_seat *s, const char *name) {}
static const struct wl_seat_listener seat_listener = { seat_on_capabilities, seat_on_name };

/* ------------------------------------------------------------------ *
 *  The screens
 * ------------------------------------------------------------------ */
static void o_geometry(void *d, struct wl_output *o, int32_t x, int32_t y, int32_t lf, int32_t af,
                        int32_t sub, const char *vendor, const char *model, int32_t xform)
{
	int i = (int) (intptr_t) d;

	if (i < OUTPUT_MAX)
		snprintf(screens[i].name, sizeof screens[i].name, "%s", model ?: "?");
}
static void o_mode(void *d, struct wl_output *o, uint32_t flags, int32_t l, int32_t a,
                   int32_t rate)
{
	int i = (int) (intptr_t) d;

	if (i < OUTPUT_MAX && (flags & WL_OUTPUT_MODE_CURRENT))
	{
		screens[i].l = l;
		screens[i].a = a;
	}
}
static void o_done(void *d, struct wl_output *o) {}
static void o_scale(void *d, struct wl_output *o, int32_t s) {}
static void o_name(void *d, struct wl_output *o, const char *n) {}
static void o_description(void *d, struct wl_output *o, const char *n) {}
static const struct wl_output_listener output_listener = { o_geometry, o_mode,  o_done,
	                                                      o_scale,     o_name, o_description };

/* ------------------------------------------------------------------ *
 *  The shell
 * ------------------------------------------------------------------ */
static void shell_ping(void *d, struct xdg_wm_base *g, uint32_t s)
{
	xdg_wm_base_pong(g, s);
}
static const struct xdg_wm_base_listener wm_base_listener = { shell_ping };

static int new_memory(size_t byte)
{
	int fd = memfd_create("b33-testimone", MFD_CLOEXEC);

	if (fd < 0)
		return -1;
	if (ftruncate(fd, (off_t) byte) < 0)
	{
		close(fd);
		return -1;
	}
	return fd;
}

static void paint(void)
{
	size_t step = (size_t) width * 4;
	size_t byte = step * (size_t) height;
	int fd = new_memory(byte);
	uint32_t *pixel;
	struct wl_shm_pool *pool;
	struct wl_buffer *bundle;

	if (fd < 0)
		return;
	pixel = mmap(NULL, byte, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (pixel == MAP_FAILED)
	{
		close(fd);
		return;
	}
	for (size_t i = 0; i < byte / 4; i++)
		pixel[i] = 0xFF101014;
	pool = wl_shm_create_pool(mem_buf, fd, (int32_t) byte);
	bundle = wl_shm_pool_create_buffer(pool, 0, width, height, (int32_t) step,
	                                  WL_SHM_FORMAT_ARGB8888);
	wl_shm_pool_destroy(pool);
	munmap(pixel, byte);
	close(fd);

	wl_surface_attach(surface, bundle, 0, 0);
	wl_surface_damage_buffer(surface, 0, 0, width, height);
	wl_surface_commit(surface);
}

static void sup_configure(void *d, struct xdg_surface *s, uint32_t serial)
{
	xdg_surface_ack_configure(s, serial);
	paint();
	if (!configured)
	{
		configured = true;
		vista_l = width;
		vista_a = height;
		line("\"type\":\"READY\",\"width\":%d,\"height\":%d,\"screen\":\"%s\"", width,
		     height, chosen >= 0 ? screens[chosen].name : "?");
	}
	/*
	 * ⭐⭐ THE ONLY ADDITION TO B24 — and it is written from the side that RECEIVES.
	 *
	 * ⛔ The server log says «canvas 1264x800 → 1000x640»: it says that we
	 *    ASKED.  This line says that the compositor really
	 *    resized the screen under a window **already open**, which is the
	 *    scene of point 3 of the mandate.  ⚠ And it is written ONLY when it changes: one
	 *    line for every `configure` would make a resize
	 *    indistinguishable from a redraw.
	 */
	else if (width != vista_l || height != vista_a)
	{
		line("\"type\":\"RITELA\",\"da_l\":%d,\"da_a\":%d,\"a_l\":%d,\"a_a\":%d", vista_l, vista_a,
		     width, height);
		vista_l = width;
		vista_a = height;
	}
}
static const struct xdg_surface_listener surface_listener = { sup_configure };

static void fin_configure(void *d, struct xdg_toplevel *f, int32_t l, int32_t a,
                          struct wl_array *states)
{
	if (l > 0 && a > 0)
	{
		width = l;
		height = a;
	}
}
static void fin_close(void *d, struct xdg_toplevel *f)
{
	line("\"type\":\"CHIUSA\"");
	exit(0);
}
static void fin_limits(void *d, struct xdg_toplevel *f, int32_t l, int32_t a) {}
static void fin_states(void *d, struct xdg_toplevel *f, struct wl_array *c) {}
static const struct xdg_toplevel_listener window_listener = { fin_configure, fin_close, fin_limits,
	                                                      fin_states };

/* ------------------------------------------------------------------ *
 *  The global registry
 * ------------------------------------------------------------------ */
static void registry_on_global(void *d, struct wl_registry *r, uint32_t name, const char *interfaccia,
                             uint32_t version)
{
	if (!strcmp(interfaccia, wl_compositor_interface.name))
		compositor = wl_registry_bind(r, name, &wl_compositor_interface, 4);
	else if (!strcmp(interfaccia, wl_shm_interface.name))
		mem_buf = wl_registry_bind(r, name, &wl_shm_interface, 1);
	else if (!strcmp(interfaccia, xdg_wm_base_interface.name))
	{
		shell = wl_registry_bind(r, name, &xdg_wm_base_interface, 1);
		xdg_wm_base_add_listener(shell, &wm_base_listener, NULL);
	}
	else if (!strcmp(interfaccia, wl_seat_interface.name))
	{
		/* ⛔ Version 8: it is the one that carries `axis_value120`, that is the unit in
		 *    which `RCP.md` §7.3 counts the wheel.  With a lower version the
		 *    sign could be measured only on the smooth axis, which is another
		 *    quantity. */
		uint32_t v = version < 8 ? version : 8;

		slot = wl_registry_bind(r, name, &wl_seat_interface, v);
		wl_seat_add_listener(slot, &seat_listener, NULL);
		line("\"type\":\"POSTO_LEGATO\",\"version\":%u", v);
	}
	else if (!strcmp(interfaccia, wl_output_interface.name) && how_many_screens < OUTPUT_MAX)
	{
		int i = how_many_screens++;

		screens[i].output = wl_registry_bind(r, name, &wl_output_interface, 2);
		wl_output_add_listener(screens[i].output, &output_listener, (void *) (intptr_t) i);
	}
}
static void registry_remove(void *d, struct wl_registry *r, uint32_t name) {}
static const struct wl_registry_listener registry_listener = { registry_on_global, registry_remove };

int main(int argc, char **argv)
{
	struct wl_display *screen;
	struct wl_registry *log;

	setvbuf(stdout, NULL, _IOLBF, 0);
	for (int i = 1; i < argc; i++)
		if (!strcmp(argv[i], "--size") && i + 1 < argc)
			sscanf(argv[++i], "%ux%u", &intended_w, &intended_h);

	screen = wl_display_connect(NULL);
	if (!screen)
	{
		line("\"type\":\"ERRORE\",\"why\":\"no Wayland compositor\"");
		return 2;
	}
	log = wl_display_get_registry(screen);
	wl_registry_add_listener(log, &registry_listener, NULL);
	wl_display_roundtrip(screen);
	wl_display_roundtrip(screen); /* the second round brings the modes of the outputs */

	if (!compositor || !mem_buf || !shell)
	{
		line("\"type\":\"ERRORE\",\"why\":\"the compositor does not expose shell or memory\"");
		return 2;
	}

	/* ⛔ THE MONITOR IS CHOSEN, and if there is none we exit saying so. */
	for (int i = 0; i < how_many_screens; i++)
	{
		line("\"type\":\"SCHERMO\",\"i\":%d,\"l\":%d,\"a\":%d,\"name\":\"%s\"", i, screens[i].l,
		     screens[i].a, screens[i].name);
		if (chosen < 0 && (uint32_t) screens[i].l == intended_w && (uint32_t) screens[i].a == intended_h)
			chosen = i;
	}
	if (chosen < 0)
	{
		line("\"type\":\"ERRORE\",\"why\":\"no %ux%u screen among the %d announced\"",
		     intended_w, intended_h, how_many_screens);
		return 3;
	}
	width = screens[chosen].l;
	height = screens[chosen].a;

	surface = wl_compositor_create_surface(compositor);
	xdg_sup = xdg_wm_base_get_xdg_surface(shell, surface);
	xdg_surface_add_listener(xdg_sup, &surface_listener, NULL);
	window = xdg_surface_get_toplevel(xdg_sup);
	xdg_toplevel_add_listener(window, &window_listener, NULL);
	xdg_toplevel_set_title(window, "B33 witness");
	xdg_toplevel_set_app_id(window, "remotix.b33");
	xdg_toplevel_set_fullscreen(window, screens[chosen].output);
	wl_surface_commit(surface);

	while (wl_display_dispatch(screen) != -1)
		;
	line("\"type\":\"FINE\"");
	return 0;
}
