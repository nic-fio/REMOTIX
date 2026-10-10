/*
 * 01-s7-rotella.c — the INJECTOR of measurement S7: which way the wheel turns.
 *
 *   ./01-s7-rotella            opens the session, waits for commands on standard input
 *
 * Commands (one per line, the answer always starts with «S7: »):
 *
 *   centro            brings the pointer to the centre of the region
 *   scatto <dx> <dy>  ei_device_scroll_discrete(dx, dy)   ← THE measurement
 *   liscio <dx> <dy>  ei_device_scroll_delta(dx, dy)      ← the comparison
 *   stato             reprints region, device, capabilities
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
 * work»: three causes, one single silence (`LEZIONI.md` §1.9).
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

#define NOME_RD "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_RD "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_RD "org.gnome.Mutter.RemoteDesktop"
#define IFACE_RD_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"
#define ATTESA_MS 5000

static void dilo(const char *forma, ...)
{
	va_list argomenti;

	fputs("S7: ", stdout);
	va_start(argomenti, forma);
	vfprintf(stdout, forma, argomenti);
	va_end(argomenti);
	fputc('\n', stdout);
	fflush(stdout);
}

/* ------------------------------------------------------------------------ *
 * The state of the program: small, and all in here.
 * ------------------------------------------------------------------------ */
static struct ei *contesto;
static struct ei_device *puntatore;     /* the one that has scrolling */
static bool puntatore_pronto;
static uint32_t sequenza;
static bool regione_nota;
static double reg_x, reg_y, reg_l, reg_a;
static bool assoluto;                   /* the region is there: one goes to the centre */

/*
 * ⛔ The bus connection is OURS, not the shared one of `g_bus_get_sync`.
 *    On the shared one GIO keeps «exit-on-close» on and calls `raise(SIGTERM)`
 *    on our behalf when the bus closes: it is the defect of 4 Aug 2026
 *    quoted in `fondamenta/remotix-c/src/sessione.h`, and here it would produce an
 *    injector that dies by itself halfway through the measurement without anything saying so.
 */
static GDBusConnection *apri_bus(GError **sbaglio)
{
	g_autofree char *indirizzo = g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);

	if (!indirizzo)
		return NULL;
	return g_dbus_connection_new_for_address_sync(
	    indirizzo, G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT | G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, sbaglio);
}

/* ------------------------------------------------------------------------ *
 * Mutter's RemoteDesktop session, and the EIS descriptor.
 *
 * ⚠ The order is that of the reference and of `fondamenta/remotix-c/src/mutter.c`:
 *   CreateSession → ConnectToEIS → Start.  `ConnectToEIS` is asked on the
 *   session NOT yet started.
 * ------------------------------------------------------------------------ */
static int apri_eis(GDBusConnection *bus, GError **sbaglio)
{
	g_autofree char *sessione = NULL;
	g_autoptr(GUnixFDList) descrittori = NULL;
	g_autoptr(GVariant) risposta = NULL;
	GVariantBuilder vuote;
	gint32 indice = -1;
	int fd;

	{
		g_autoptr(GVariant) r =
		    g_dbus_connection_call_sync(bus, NOME_RD, PERCORSO_RD, IFACE_RD, "CreateSession", NULL,
		                                G_VARIANT_TYPE("(o)"), G_DBUS_CALL_FLAGS_NONE, ATTESA_MS,
		                                NULL, sbaglio);
		if (!r)
		{
			g_prefix_error(sbaglio, "Mutter does not expose RemoteDesktop (is there a graphical "
			                        "session?): ");
			return -1;
		}
		g_variant_get(r, "(o)", &sessione);
	}
	dilo("RemoteDesktop session: %s", sessione);

	g_variant_builder_init(&vuote, G_VARIANT_TYPE("a{sv}"));
	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    bus, NOME_RD, sessione, IFACE_RD_SESSIONE, "ConnectToEIS", g_variant_new("(a{sv})", &vuote),
	    G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE, ATTESA_MS, NULL, &descrittori, NULL, sbaglio);
	if (!risposta)
	{
		g_prefix_error(sbaglio, "ConnectToEIS refused: ");
		return -1;
	}
	g_variant_get(risposta, "(h)", &indice);
	fd = g_unix_fd_list_get(descrittori, indice, sbaglio);
	if (fd < 0)
		return -1;

	{
		g_autoptr(GVariant) r =
		    g_dbus_connection_call_sync(bus, NOME_RD, sessione, IFACE_RD_SESSIONE, "Start", NULL,
		                                NULL, G_DBUS_CALL_FLAGS_NONE, ATTESA_MS, NULL, sbaglio);
		if (!r)
		{
			g_prefix_error(sbaglio, "Start of the RemoteDesktop session: ");
			close(fd);
			return -1;
		}
	}
	dilo("EIS channel open (descriptor %d), session started", fd);
	return fd;
}

/* ------------------------------------------------------------------------ *
 * The region: it is the screen on which the pointer moves in absolute terms.
 *
 * ⛔ It is always PRINTED, even when it is not there.  «No region» and «region
 *    0x0» have two different cures, and a mute injector confuses them.
 * ------------------------------------------------------------------------ */
static void leggi_regione(struct ei_device *dispositivo)
{
	regione_nota = false;
	for (size_t i = 0;; i++)
	{
		struct ei_region *regione = ei_device_get_region(dispositivo, i);

		if (!regione)
			break;
		/* ⛔ The four getters return `uint32_t`, not `double`: passing them to a
		 *    `%.0f` prints garbage.  `[M]` 10 Aug 2026, and the garbage
		 *    was «0,0 0x0» — that is it looked like a real diagnosis («the
		 *    region is degenerate») while the region was 1920x1080.  A
		 *    PRINTING defect that reads as a defect of the compositor. */
		dilo("region %zu: %u,%u  %ux%u  (mapping-id «%s»)", i, ei_region_get_x(regione),
		     ei_region_get_y(regione), ei_region_get_width(regione), ei_region_get_height(regione),
		     ei_region_get_mapping_id(regione) ?: "absent");
		if (!regione_nota && ei_region_get_width(regione) > 0 && ei_region_get_height(regione) > 0)
		{
			reg_x = ei_region_get_x(regione);
			reg_y = ei_region_get_y(regione);
			reg_l = ei_region_get_width(regione);
			reg_a = ei_region_get_height(regione);
			regione_nota = true;
		}
	}
	if (!regione_nota)
		dilo("NO region: the pointer will move in RELATIVE mode, and the final "
		     "position is not guaranteed");
}

static void al_centro(void)
{
	if (!puntatore_pronto)
	{
		dilo("ERROR: no pointing device ready");
		return;
	}
	if (regione_nota && assoluto)
	{
		ei_device_pointer_motion_absolute(puntatore, reg_x + reg_l / 2, reg_y + reg_a / 2);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("pointer at %.0f,%.0f (absolute)", reg_x + reg_l / 2, reg_y + reg_a / 2);
	}
	else
	{
		/* ⛔ First to the corner, THEN back by half a screen: the compositor
		 *    stops the pointer at the edge, so the first move gives a
		 *    KNOWN position even without knowing where it was before. */
		ei_device_pointer_motion(puntatore, 20000, 20000);
		ei_device_frame(puntatore, ei_now(contesto));
		ei_device_pointer_motion(puntatore, -960, -540);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("pointer moved in RELATIVE mode towards the centre (corner, then -960,-540)");
	}
}

/* ------------------------------------------------------------------------ *
 * The libei events.  Names and order are those already tested in
 * `fondamenta/remotix-c/src/input.c`, which runs on this same Mutter.
 * ------------------------------------------------------------------------ */
static void tratta_evento(struct ei_event *evento)
{
	enum ei_event_type tipo = ei_event_get_type(evento);
	struct ei_device *dispositivo = ei_event_get_device(evento);

	switch (tipo)
	{
		case EI_EVENT_CONNECT:
			dilo("connected");
			break;
		case EI_EVENT_SEAT_ADDED:
			ei_seat_bind_capabilities(ei_event_get_seat(evento), EI_DEVICE_CAP_POINTER,
			                          EI_DEVICE_CAP_POINTER_ABSOLUTE, EI_DEVICE_CAP_BUTTON,
			                          EI_DEVICE_CAP_SCROLL, NULL);
			dilo("seat «%s»: requested the pointing and scrolling capabilities",
			     ei_seat_get_name(ei_event_get_seat(evento)) ?: "?");
			break;
		case EI_EVENT_DEVICE_ADDED:
			dilo("device «%s»: pointer=%d absolute=%d scroll=%d buttons=%d",
			     ei_device_get_name(dispositivo) ?: "?",
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER),
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE),
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_SCROLL),
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_BUTTON));
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
			if (!ei_device_has_capability(dispositivo, EI_DEVICE_CAP_SCROLL))
				break;
			if (!puntatore || (!assoluto &&
			                   ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE)))
			{
				if (puntatore)
				{
					dilo("switching device: the previous one did not have absolute mode");
					ei_device_unref(puntatore);
					puntatore_pronto = false;
				}
				puntatore = ei_device_ref(dispositivo);
				assoluto = ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE);
				leggi_regione(dispositivo);
			}
			break;
		case EI_EVENT_DEVICE_RESUMED:
			ei_device_start_emulating(dispositivo, ++sequenza);
			if (dispositivo == puntatore)
			{
				leggi_regione(dispositivo);
				puntatore_pronto = true;
				/* ⛔ Two different words for two different situations: whoever launches
				 *    the bench must be able to wait for the good one instead of
				 *    starting with the first that arrives. */
				dilo(assoluto ? "PRONTO" : "PRONTO-RELATIVO");
			}
			break;
		case EI_EVENT_DEVICE_PAUSED:
			if (dispositivo == puntatore)
			{
				puntatore_pronto = false;
				dilo("the device was SUSPENDED by the compositor");
			}
			break;
		case EI_EVENT_DEVICE_REMOVED:
			if (dispositivo == puntatore)
			{
				puntatore_pronto = false;
				dilo("the device was REMOVED by the compositor");
			}
			break;
		case EI_EVENT_DISCONNECT:
			dilo("DISCONNECTED by the compositor");
			exit(4);
		default:
			break;
	}
}

static void dispatcia(void)
{
	struct ei_event *evento;

	ei_dispatch(contesto);
	while ((evento = ei_get_event(contesto)) != NULL)
	{
		tratta_evento(evento);
		ei_event_unref(evento);
	}
}

/* ------------------------------------------------------------------------ */
static void comando(char *riga)
{
	int dx, dy;

	g_strstrip(riga);
	if (!*riga)
		return;
	if (g_str_equal(riga, "fine"))
	{
		dilo("fine");
		exit(0);
	}
	if (g_str_equal(riga, "centro"))
	{
		al_centro();
		return;
	}
	if (g_str_equal(riga, "stato"))
	{
		dilo("device ready=%d  absolute=%d  region=%d (%.0f,%.0f %.0fx%.0f)",
		     puntatore_pronto, assoluto, regione_nota, reg_x, reg_y, reg_l, reg_a);
		return;
	}
	if (sscanf(riga, "scatto %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERROR: no device ready, the click was NOT sent");
			return;
		}
		ei_device_scroll_discrete(puntatore, dx, dy);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("CLICK dx=%d dy=%d sent", dx, dy);
		return;
	}
	/* The movement by hand: it serves the positive control — if the page sees
	 * the pointer move, the road from the injector to the page is open. */
	if (sscanf(riga, "muovi %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERROR: no device ready");
			return;
		}
		if (regione_nota && assoluto)
			ei_device_pointer_motion_absolute(puntatore, reg_x + dx, reg_y + dy);
		else
			ei_device_pointer_motion(puntatore, dx, dy);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("MOVED to %d,%d", dx, dy);
		return;
	}
	if (sscanf(riga, "bottone %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERROR: no device ready");
			return;
		}
		ei_device_button_button(puntatore, (uint32_t) dx, dy != 0);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("BUTTON %d %s", dx, dy ? "down" : "up");
		return;
	}
	if (sscanf(riga, "liscio %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERROR: no device ready, the smooth scroll was NOT sent");
			return;
		}
		ei_device_scroll_delta(puntatore, dx, dy);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("SMOOTH dx=%d dy=%d sent", dx, dy);
		return;
	}
	dilo("unknown command: «%s»", riga);
}

int main(void)
{
	g_autoptr(GError) sbaglio = NULL;
	GDBusConnection *bus;
	int fd_eis;
	struct pollfd sorveglianza[2];
	char riga[256];

	setvbuf(stdout, NULL, _IOLBF, 0);

	bus = apri_bus(&sbaglio);
	if (!bus)
	{
		dilo("ERROR: session bus not reachable: %s", sbaglio->message);
		return 2;
	}
	fd_eis = apri_eis(bus, &sbaglio);
	if (fd_eis < 0)
	{
		dilo("ERROR: %s", sbaglio->message);
		return 3;
	}

	contesto = ei_new_sender(NULL);
	ei_configure_name(contesto, "remotix-s7");
	if (ei_setup_backend_fd(contesto, fd_eis) != 0)
	{
		dilo("ERROR: libei did not accept the ConnectToEIS descriptor");
		return 3;
	}

	sorveglianza[0].fd = ei_get_fd(contesto);
	sorveglianza[0].events = POLLIN;
	sorveglianza[1].fd = STDIN_FILENO;
	sorveglianza[1].events = POLLIN;

	dispatcia();
	for (;;)
	{
		if (poll(sorveglianza, 2, 1000) < 0)
			break;
		if (sorveglianza[0].revents & POLLIN)
			dispatcia();
		if (sorveglianza[1].revents & POLLIN)
		{
			if (!fgets(riga, sizeof riga, stdin))
			{
				dilo("standard input closed: exiting");
				break;
			}
			comando(riga);
			dispatcia();
		}
		if (sorveglianza[1].revents & POLLHUP)
			break;
	}
	return 0;
}
