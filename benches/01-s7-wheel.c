/*
 * 01-s7-wheel.c — the INJECTOR of measurement S7: which way the wheel turns.
 *
 *   ./01-s7-wheel            opens the session, waits for commands on standard input
 *
 * Commands (one per line, the answer always starts with «S7: »):
 *
 *   center            brings the pointer to the centre of the region
 *   scatto <dx> <dy>  ei_device_scroll_discrete(dx, dy)   ← THE measurement
 *   liscio <dx> <dy>  ei_device_scroll_delta(dx, dy)      ← the comparison
 *   state             reprints region, device, capabilities
 *   fine              exits
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY `libei` AND NOT `NotifyPointerAxisDiscrete`
 *
 * Mutter also exposes the old `Notify*` methods on D-Bus, and from there a click
 * is sent in one line of `gdbus`.  ⛔ But the product injects with **libei**
 * (`fondamenta/remotix-c/src/input.c`, `ei_device_scroll_discrete`), and the sign
 * is precisely the thing the two roads might not share: measuring on the road
 * the product does not use would be form **E10** — a number taken on an engine
 * different from the product's.
 *
 * ---------------------------------------------------------------------------
 * ⛔ AND WHAT `libei` DOES NOT SAY, AND IT IS THE REASON S7 EXISTS
 *
 * `libei.h` 1.3.901, documentation of `ei_device_scroll_discrete` read on 10
 * Aug 2026, declares **the magnitude and not the direction**:
 *
 *     «A discrete scroll event is based logical scroll units (equivalent to
 *      one mouse wheel click). The value for one scroll unit is 120 …
 *      @param y The y scroll distance in fractions or multiples of 120»
 *
 * No line says whether `+120` is «up» or «down».  ⭐ It is not an oversight of
 * ours: **the convention is not in the API**, it is in the compositor — which is
 * exactly the reason `RCP.md` §7.3 keeps the line at `[?]` and orders measuring
 * it instead of deciding it.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE POINTER IS BROUGHT TO THE CENTRE BEFORE EVERY CLICK, AND IT IS NOT COURTESY
 *
 * A click goes to the window under the pointer.  An emulated pointer is born at
 * `0,0`, and `0,0` on GNOME is the top bar — that is the Shell, not the page.
 * Without this move the measurement would look like «the page does not move»,
 * which is also the look of «the sign is zero» and of «the injection does not
 * work»: three causes, one single silence (`LESSONS.md` §1.9).
 * ---------------------------------------------------------------------------
 */
#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <libei.h>
#include <poll.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define RD_NAME "org.gnome.Mutter.RemoteDesktop"
#define RD_PATH "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_RD "org.gnome.Mutter.RemoteDesktop"
#define IFACE_RD_SESSION "org.gnome.Mutter.RemoteDesktop.Session"
#define WAIT_MS 5000

static void tell(const char *shape, ...)
{
	va_list call_args;

	fputs("S7: ", stdout);
	va_start(call_args, shape);
	vfprintf(stdout, shape, call_args);
	va_end(call_args);
	fputc('\n', stdout);
	fflush(stdout);
}

/* ------------------------------------------------------------------------ *
 * The state of the program: small, and all in here.
 * ------------------------------------------------------------------------ */
static struct ei *context;
static struct ei_device *pointer;     /* the one that has scrolling */
static bool pointer_ready;
static uint32_t sequence;
static bool region_known;
static double reg_x, reg_y, reg_l, reg_a;
static bool absolute;                   /* the region is there: one goes to the centre */

/*
 * ⛔ The bus connection is OURS, not the shared one of `g_bus_get_sync`.
 *    On the shared one GIO keeps «exit-on-close» on and calls `raise(SIGTERM)`
 *    on our behalf when the bus closes: it is the defect of 4 Aug 2026
 *    quoted in `fondamenta/remotix-c/src/sessione.h`, and here it would produce an
 *    injector that dies by itself halfway through the measurement without anything saying so.
 */
static GDBusConnection *open_bus(GError **mistake)
{
	g_autofree char *address = g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, mistake);

	if (!address)
		return NULL;
	return g_dbus_connection_new_for_address_sync(
	    address, G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT | G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, mistake);
}

/* ------------------------------------------------------------------------ *
 * Mutter's RemoteDesktop session, and the EIS descriptor.
 *
 * ⚠ The order is that of the reference and of `fondamenta/remotix-c/src/mutter.c`:
 *   CreateSession → ConnectToEIS → Start.  `ConnectToEIS` is asked on the
 *   session NOT yet started.
 * ------------------------------------------------------------------------ */
static int open_eis(GDBusConnection *bus, GError **mistake)
{
	g_autofree char *session = NULL;
	g_autoptr(GUnixFDList) descriptors = NULL;
	g_autoptr(GVariant) response = NULL;
	GVariantBuilder blanks;
	gint32 idx = -1;
	int fd;

	{
		g_autoptr(GVariant) r =
		    g_dbus_connection_call_sync(bus, RD_NAME, RD_PATH, IFACE_RD, "CreateSession", NULL,
		                                G_VARIANT_TYPE("(o)"), G_DBUS_CALL_FLAGS_NONE, WAIT_MS,
		                                NULL, mistake);
		if (!r)
		{
			g_prefix_error(mistake, "Mutter does not expose RemoteDesktop (is there a graphical "
			                        "session?): ");
			return -1;
		}
		g_variant_get(r, "(o)", &session);
	}
	tell("RemoteDesktop session: %s", session);

	g_variant_builder_init(&blanks, G_VARIANT_TYPE("a{sv}"));
	response = g_dbus_connection_call_with_unix_fd_list_sync(
	    bus, RD_NAME, session, IFACE_RD_SESSION, "ConnectToEIS", g_variant_new("(a{sv})", &blanks),
	    G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE, WAIT_MS, NULL, &descriptors, NULL, mistake);
	if (!response)
	{
		g_prefix_error(mistake, "ConnectToEIS refused: ");
		return -1;
	}
	g_variant_get(response, "(h)", &idx);
	fd = g_unix_fd_list_get(descriptors, idx, mistake);
	if (fd < 0)
		return -1;

	{
		g_autoptr(GVariant) r =
		    g_dbus_connection_call_sync(bus, RD_NAME, session, IFACE_RD_SESSION, "Start", NULL,
		                                NULL, G_DBUS_CALL_FLAGS_NONE, WAIT_MS, NULL, mistake);
		if (!r)
		{
			g_prefix_error(mistake, "Start of the RemoteDesktop session: ");
			close(fd);
			return -1;
		}
	}
	tell("EIS channel open (descriptor %d), session started", fd);
	return fd;
}

/* ------------------------------------------------------------------------ *
 * The region: it is the screen on which the pointer moves in absolute terms.
 *
 * ⛔ It is always PRINTED, even when it is not there.  «No region» and «region
 *    0x0» have two different cures, and a mute injector confuses them.
 * ------------------------------------------------------------------------ */
static void read_region(struct ei_device *device)
{
	region_known = false;
	for (size_t i = 0;; i++)
	{
		struct ei_region *region = ei_device_get_region(device, i);

		if (!region)
			break;
		/* ⛔ The four getters return `uint32_t`, not `double`: passing them to a
		 *    `%.0f` prints garbage.  `[M]` 10 Aug 2026, and the garbage
		 *    was «0,0 0x0» — that is it looked like a real diagnosis («the
		 *    region is degenerate») while the region was 1920x1080.  A
		 *    PRINTING defect that reads as a defect of the compositor. */
		tell("region %zu: %u,%u  %ux%u  (mapping-id «%s»)", i, ei_region_get_x(region),
		     ei_region_get_y(region), ei_region_get_width(region), ei_region_get_height(region),
		     ei_region_get_mapping_id(region) ?: "absent");
		if (!region_known && ei_region_get_width(region) > 0 && ei_region_get_height(region) > 0)
		{
			reg_x = ei_region_get_x(region);
			reg_y = ei_region_get_y(region);
			reg_l = ei_region_get_width(region);
			reg_a = ei_region_get_height(region);
			region_known = true;
		}
	}
	if (!region_known)
		tell("NO region: the pointer will move in RELATIVE mode, and the final "
		     "position is not guaranteed");
}

static void to_center(void)
{
	if (!pointer_ready)
	{
		tell("ERROR: no pointing device ready");
		return;
	}
	if (region_known && absolute)
	{
		ei_device_pointer_motion_absolute(pointer, reg_x + reg_l / 2, reg_y + reg_a / 2);
		ei_device_frame(pointer, ei_now(context));
		tell("pointer at %.0f,%.0f (absolute)", reg_x + reg_l / 2, reg_y + reg_a / 2);
	}
	else
	{
		/* ⛔ First to the corner, THEN back by half a screen: the compositor
		 *    stops the pointer at the edge, so the first move gives a
		 *    KNOWN position even without knowing where it was before. */
		ei_device_pointer_motion(pointer, 20000, 20000);
		ei_device_frame(pointer, ei_now(context));
		ei_device_pointer_motion(pointer, -960, -540);
		ei_device_frame(pointer, ei_now(context));
		tell("pointer moved in RELATIVE mode towards the centre (corner, then -960,-540)");
	}
}

/* ------------------------------------------------------------------------ *
 * The libei events.  Names and order are those already tested in
 * `fondamenta/remotix-c/src/input.c`, which runs on this same Mutter.
 * ------------------------------------------------------------------------ */
static void handle_event(struct ei_event *event)
{
	enum ei_event_type kind = ei_event_get_type(event);
	struct ei_device *device = ei_event_get_device(event);

	switch (kind)
	{
		case EI_EVENT_CONNECT:
			tell("connected");
			break;
		case EI_EVENT_SEAT_ADDED:
			ei_seat_bind_capabilities(ei_event_get_seat(event), EI_DEVICE_CAP_POINTER,
			                          EI_DEVICE_CAP_POINTER_ABSOLUTE, EI_DEVICE_CAP_BUTTON,
			                          EI_DEVICE_CAP_SCROLL, NULL);
			tell("seat «%s»: requested the pointing and scrolling capabilities",
			     ei_seat_get_name(ei_event_get_seat(event)) ?: "?");
			break;
		case EI_EVENT_DEVICE_ADDED:
			tell("device «%s»: pointer=%d absolute=%d scroll=%d buttons=%d",
			     ei_device_get_name(device) ?: "?",
			     ei_device_has_capability(device, EI_DEVICE_CAP_POINTER),
			     ei_device_has_capability(device, EI_DEVICE_CAP_POINTER_ABSOLUTE),
			     ei_device_has_capability(device, EI_DEVICE_CAP_SCROLL),
			     ei_device_has_capability(device, EI_DEVICE_CAP_BUTTON));
			/*
			 * ⛔ THE ABSOLUTE ONE IS TAKEN, AND IT IS NOT A PREFERENCE.
			 *
			 * `[M]` 10 Aug 2026: Mutter offers TWO devices, and they are
			 * different where it counts.  «remotix-s7 virtual pointer» can scroll but
			 * moves only in RELATIVE mode and **has no region**; «remotix-s7
			 * shared virtual absolute pointer» has the regions, that is it is the only
			 * one with which one knows WHERE one is putting the pointer.
			 *
			 * The first run of this bench took «the first one that can
			 * scroll», that is the relative one, pushed the pointer towards the
			 * centre by eye, and recorded **nothing five times**: the
			 * clicks really left (the injector said so) and reached
			 * no window.  ⭐ «It did not move» and «there was nothing
			 * under the pointer» look the same, and it is the reason why
			 * the bench now also asks GNOME Shell where the window is.
			 */
			if (!ei_device_has_capability(device, EI_DEVICE_CAP_SCROLL))
				break;
			if (!pointer || (!absolute &&
			                   ei_device_has_capability(device, EI_DEVICE_CAP_POINTER_ABSOLUTE)))
			{
				if (pointer)
				{
					tell("switching device: the previous one did not have absolute mode");
					ei_device_unref(pointer);
					pointer_ready = false;
				}
				pointer = ei_device_ref(device);
				absolute = ei_device_has_capability(device, EI_DEVICE_CAP_POINTER_ABSOLUTE);
				read_region(device);
			}
			break;
		case EI_EVENT_DEVICE_RESUMED:
			ei_device_start_emulating(device, ++sequence);
			if (device == pointer)
			{
				read_region(device);
				pointer_ready = true;
				/* ⛔ Two different words for two different situations: whoever launches
				 *    the bench must be able to wait for the good one instead of
				 *    starting with the first that arrives. */
				tell(absolute ? "PRONTO" : "PRONTO-RELATIVO");
			}
			break;
		case EI_EVENT_DEVICE_PAUSED:
			if (device == pointer)
			{
				pointer_ready = false;
				tell("the device was SUSPENDED by the compositor");
			}
			break;
		case EI_EVENT_DEVICE_REMOVED:
			if (device == pointer)
			{
				pointer_ready = false;
				tell("the device was REMOVED by the compositor");
			}
			break;
		case EI_EVENT_DISCONNECT:
			tell("DISCONNECTED by the compositor");
			exit(4);
		default:
			break;
	}
}

static void dispatch_all(void)
{
	struct ei_event *event;

	ei_dispatch(context);
	while ((event = ei_get_event(context)) != NULL)
	{
		handle_event(event);
		ei_event_unref(event);
	}
}

/* ------------------------------------------------------------------------ */
static void command(char *line)
{
	int dx, dy;

	g_strstrip(line);
	if (!*line)
		return;
	if (g_str_equal(line, "end"))
	{
		tell("end");
		exit(0);
	}
	if (g_str_equal(line, "centro"))
	{
		to_center();
		return;
	}
	if (g_str_equal(line, "state"))
	{
		tell("device ready=%d  absolute=%d  region=%d (%.0f,%.0f %.0fx%.0f)",
		     pointer_ready, absolute, region_known, reg_x, reg_y, reg_l, reg_a);
		return;
	}
	if (sscanf(line, "scatto %d %d", &dx, &dy) == 2)
	{
		if (!pointer_ready)
		{
			tell("ERROR: no device ready, the click was NOT sent");
			return;
		}
		ei_device_scroll_discrete(pointer, dx, dy);
		ei_device_frame(pointer, ei_now(context));
		tell("CLICK dx=%d dy=%d sent", dx, dy);
		return;
	}
	/* The movement by hand: it serves the positive control — if the page sees
	 * the pointer move, the road from the injector to the page is open. */
	if (sscanf(line, "muovi %d %d", &dx, &dy) == 2)
	{
		if (!pointer_ready)
		{
			tell("ERROR: no device ready");
			return;
		}
		if (region_known && absolute)
			ei_device_pointer_motion_absolute(pointer, reg_x + dx, reg_y + dy);
		else
			ei_device_pointer_motion(pointer, dx, dy);
		ei_device_frame(pointer, ei_now(context));
		tell("MOVED to %d,%d", dx, dy);
		return;
	}
	if (sscanf(line, "bottone %d %d", &dx, &dy) == 2)
	{
		if (!pointer_ready)
		{
			tell("ERROR: no device ready");
			return;
		}
		ei_device_button_button(pointer, (uint32_t) dx, dy != 0);
		ei_device_frame(pointer, ei_now(context));
		tell("BUTTON %d %s", dx, dy ? "down" : "up");
		return;
	}
	if (sscanf(line, "liscio %d %d", &dx, &dy) == 2)
	{
		if (!pointer_ready)
		{
			tell("ERROR: no device ready, the smooth scroll was NOT sent");
			return;
		}
		ei_device_scroll_delta(pointer, dx, dy);
		ei_device_frame(pointer, ei_now(context));
		tell("SMOOTH dx=%d dy=%d sent", dx, dy);
		return;
	}
	tell("unknown command: «%s»", line);
}

int main(void)
{
	g_autoptr(GError) mistake = NULL;
	GDBusConnection *bus;
	int fd_eis;
	struct pollfd watch[2];
	char line[256];

	setvbuf(stdout, NULL, _IOLBF, 0);

	bus = open_bus(&mistake);
	if (!bus)
	{
		tell("ERROR: session bus not reachable: %s", mistake->message);
		return 2;
	}
	fd_eis = open_eis(bus, &mistake);
	if (fd_eis < 0)
	{
		tell("ERROR: %s", mistake->message);
		return 3;
	}

	context = ei_new_sender(NULL);
	ei_configure_name(context, "remotix-s7");
	if (ei_setup_backend_fd(context, fd_eis) != 0)
	{
		tell("ERROR: libei did not accept the ConnectToEIS descriptor");
		return 3;
	}

	watch[0].fd = ei_get_fd(context);
	watch[0].events = POLLIN;
	watch[1].fd = STDIN_FILENO;
	watch[1].events = POLLIN;

	dispatch_all();
	for (;;)
	{
		if (poll(watch, 2, 1000) < 0)
			break;
		if (watch[0].revents & POLLIN)
			dispatch_all();
		if (watch[1].revents & POLLIN)
		{
			if (!fgets(line, sizeof line, stdin))
			{
				tell("standard input closed: exiting");
				break;
			}
			command(line);
			dispatch_all();
		}
		if (watch[1].revents & POLLHUP)
			break;
	}
	return 0;
}
