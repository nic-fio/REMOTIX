/*
 * 01-s7-rotella.c — l'INIETTORE della misura S7: da che parte gira la rotella.
 *
 *   ./01-s7-rotella            apre la sessione, aspetta comandi su standard input
 *
 * Comandi (uno per riga, la risposta comincia sempre con «S7: »):
 *
 *   centro            porta il puntatore al centro della regione
 *   scatto <dx> <dy>  ei_device_scroll_discrete(dx, dy)   ← LA misura
 *   liscio <dx> <dy>  ei_device_scroll_delta(dx, dy)      ← il confronto
 *   stato             ristampa regione, dispositivo, capacita'
 *   fine              esce
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' `libei` E NON `NotifyPointerAxisDiscrete`
 *
 * Mutter espone anche i vecchi metodi `Notify*` su D-Bus, e da li' uno scatto
 * si manda in una riga di `gdbus`.  ⛔ Ma il prodotto inietta con **libei**
 * (`fondamenta/remotix-c/src/input.c`, `ei_device_scroll_discrete`), e il segno e'
 * proprio la cosa che le due strade potrebbero non condividere: misurare sulla
 * strada che il prodotto non usa sarebbe la forma **E10** — un numero preso su
 * un motore diverso da quello del prodotto.
 *
 * ---------------------------------------------------------------------------
 * ⛔ E QUEL CHE `libei` NON DICE, ED E' IL MOTIVO PER CUI S7 ESISTE
 *
 * `libei.h` 1.3.901, documentazione di `ei_device_scroll_discrete` letta il 10
 * agosto 2026, dichiara **la grandezza e non il verso**:
 *
 *     «A discrete scroll event is based logical scroll units (equivalent to
 *      one mouse wheel click). The value for one scroll unit is 120 …
 *      @param y The y scroll distance in fractions or multiples of 120»
 *
 * Nessuna riga dice se `+120` sia «in su» o «in giu'».  ⭐ Non e' una
 * dimenticanza nostra: **la convenzione non sta nell'API**, sta nel
 * compositore — che e' esattamente il motivo per cui `RCP.md` §7.3 tiene la
 * riga a `[?]` e ordina di misurarla invece di deciderla.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL PUNTATORE SI PORTA AL CENTRO PRIMA DI OGNI SCATTO, E NON E' CORTESIA
 *
 * Uno scatto va alla finestra sotto il puntatore.  Un puntatore emulato nasce
 * a `0,0`, e `0,0` su GNOME e' la barra in alto — cioe' la Shell, non la
 * pagina.  Senza questa mossa la misura avrebbe l'aspetto di «la pagina non si
 * muove», che e' anche l'aspetto di «il segno e' zero» e di «l'iniezione non
 * funziona»: tre cause, un solo silenzio (`LEZIONI.md` §1.9).
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
 * Lo stato del programma: piccolo, e tutto qui dentro.
 * ------------------------------------------------------------------------ */
static struct ei *contesto;
static struct ei_device *puntatore;     /* quello che ha lo scorrimento */
static bool puntatore_pronto;
static uint32_t sequenza;
static bool regione_nota;
static double reg_x, reg_y, reg_l, reg_a;
static bool assoluto;                   /* la regione c'e': si va al centro */

/*
 * ⛔ La connessione al bus e' NOSTRA, non quella condivisa di `g_bus_get_sync`.
 *    Sulla condivisa GIO tiene acceso «exit-on-close» e chiama `raise(SIGTERM)`
 *    per conto nostro quando il bus si chiude: e' il difetto del 4 agosto 2026
 *    citato in `fondamenta/remotix-c/src/sessione.h`, e qui produrrebbe un iniettore
 *    che muore da solo a meta' misura senza che niente lo dica.
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
 * La sessione RemoteDesktop di Mutter, e il descrittore EIS.
 *
 * ⚠ L'ordine e' quello del riferimento e di `fondamenta/remotix-c/src/mutter.c`:
 *   CreateSession → ConnectToEIS → Start.  `ConnectToEIS` si chiede sulla
 *   sessione NON ancora avviata.
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
			g_prefix_error(sbaglio, "Mutter non espone RemoteDesktop (c'e' una sessione "
			                        "grafica?): ");
			return -1;
		}
		g_variant_get(r, "(o)", &sessione);
	}
	dilo("sessione RemoteDesktop: %s", sessione);

	g_variant_builder_init(&vuote, G_VARIANT_TYPE("a{sv}"));
	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    bus, NOME_RD, sessione, IFACE_RD_SESSIONE, "ConnectToEIS", g_variant_new("(a{sv})", &vuote),
	    G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE, ATTESA_MS, NULL, &descrittori, NULL, sbaglio);
	if (!risposta)
	{
		g_prefix_error(sbaglio, "ConnectToEIS rifiutata: ");
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
			g_prefix_error(sbaglio, "Start della sessione RemoteDesktop: ");
			close(fd);
			return -1;
		}
	}
	dilo("canale EIS aperto (descrittore %d), sessione avviata", fd);
	return fd;
}

/* ------------------------------------------------------------------------ *
 * La regione: e' lo schermo su cui il puntatore si muove in assoluto.
 *
 * ⛔ Si STAMPA sempre, anche quando non c'e'.  «Nessuna regione» e «regione
 *    0x0» hanno due cure diverse, e un iniettore muto le confonde.
 * ------------------------------------------------------------------------ */
static void leggi_regione(struct ei_device *dispositivo)
{
	regione_nota = false;
	for (size_t i = 0;; i++)
	{
		struct ei_region *regione = ei_device_get_region(dispositivo, i);

		if (!regione)
			break;
		/* ⛔ I quattro getter tornano `uint32_t`, non `double`: passarli a un
		 *    `%.0f` stampa spazzatura.  `[M]` 10 agosto 2026, e la spazzatura
		 *    era «0,0 0x0» — cioe' aveva l'aspetto di una diagnosi vera («la
		 *    regione e' degenere») mentre la regione era 1920x1080.  Un
		 *    difetto di STAMPA che si legge come un difetto del compositore. */
		dilo("regione %zu: %u,%u  %ux%u  (mapping-id «%s»)", i, ei_region_get_x(regione),
		     ei_region_get_y(regione), ei_region_get_width(regione), ei_region_get_height(regione),
		     ei_region_get_mapping_id(regione) ?: "assente");
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
		dilo("NESSUNA regione: il puntatore si muovera' in RELATIVO, e la posizione "
		     "finale non e' garantita");
}

static void al_centro(void)
{
	if (!puntatore_pronto)
	{
		dilo("ERRORE: nessun dispositivo di puntamento pronto");
		return;
	}
	if (regione_nota && assoluto)
	{
		ei_device_pointer_motion_absolute(puntatore, reg_x + reg_l / 2, reg_y + reg_a / 2);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("puntatore in %.0f,%.0f (assoluto)", reg_x + reg_l / 2, reg_y + reg_a / 2);
	}
	else
	{
		/* ⛔ Prima all'angolo, POI indietro di meta' schermo: il compositore
		 *    ferma il puntatore al bordo, quindi la prima mossa da' una
		 *    posizione NOTA anche senza sapere dov'era prima. */
		ei_device_pointer_motion(puntatore, 20000, 20000);
		ei_device_frame(puntatore, ei_now(contesto));
		ei_device_pointer_motion(puntatore, -960, -540);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("puntatore mosso in RELATIVO verso il centro (angolo, poi -960,-540)");
	}
}

/* ------------------------------------------------------------------------ *
 * Gli eventi di libei.  Nomi e ordine sono quelli gia' provati in
 * `fondamenta/remotix-c/src/input.c`, che gira su questo stesso Mutter.
 * ------------------------------------------------------------------------ */
static void tratta_evento(struct ei_event *evento)
{
	enum ei_event_type tipo = ei_event_get_type(evento);
	struct ei_device *dispositivo = ei_event_get_device(evento);

	switch (tipo)
	{
		case EI_EVENT_CONNECT:
			dilo("connesso");
			break;
		case EI_EVENT_SEAT_ADDED:
			ei_seat_bind_capabilities(ei_event_get_seat(evento), EI_DEVICE_CAP_POINTER,
			                          EI_DEVICE_CAP_POINTER_ABSOLUTE, EI_DEVICE_CAP_BUTTON,
			                          EI_DEVICE_CAP_SCROLL, NULL);
			dilo("seggio «%s»: chieste le capacita' di puntamento e scorrimento",
			     ei_seat_get_name(ei_event_get_seat(evento)) ?: "?");
			break;
		case EI_EVENT_DEVICE_ADDED:
			dilo("dispositivo «%s»: puntatore=%d assoluto=%d scorrimento=%d bottoni=%d",
			     ei_device_get_name(dispositivo) ?: "?",
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER),
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE),
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_SCROLL),
			     ei_device_has_capability(dispositivo, EI_DEVICE_CAP_BUTTON));
			/*
			 * ⛔ SI PRENDE QUELLO ASSOLUTO, E NON E' UNA PREFERENZA.
			 *
			 * `[M]` 10 agosto 2026: Mutter offre DUE dispositivi, e sono
			 * diversi dove conta.  «remotix-s7 virtual pointer» sa scorrere ma
			 * si muove solo in RELATIVO e **non ha nessuna regione**; «remotix-s7
			 * shared virtual absolute pointer» ha le regioni, cioe' e' l'unico
			 * con cui si sa DOVE si sta mettendo il puntatore.
			 *
			 * Il primo giro di questo banco ha preso «il primo che sa
			 * scorrere», cioe' il relativo, ha spinto il puntatore verso il
			 * centro a occhio, e ha registrato **cinque volte niente**: gli
			 * scatti partivano davvero (l'iniettore lo diceva) e non arrivavano
			 * a nessuna finestra.  ⭐ «Non si e' mossa» e «non c'era niente
			 * sotto il puntatore» hanno lo stesso aspetto, ed e' la ragione per
			 * cui adesso il banco chiede anche a GNOME Shell dov'e' la finestra.
			 */
			if (!ei_device_has_capability(dispositivo, EI_DEVICE_CAP_SCROLL))
				break;
			if (!puntatore || (!assoluto &&
			                   ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE)))
			{
				if (puntatore)
				{
					dilo("scambio il dispositivo: quello di prima non aveva l'assoluto");
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
				/* ⛔ Due parole diverse per due situazioni diverse: chi lancia
				 *    il banco deve poter aspettare quella buona invece di
				 *    partire con la prima che arriva. */
				dilo(assoluto ? "PRONTO" : "PRONTO-RELATIVO");
			}
			break;
		case EI_EVENT_DEVICE_PAUSED:
			if (dispositivo == puntatore)
			{
				puntatore_pronto = false;
				dilo("il dispositivo e' stato SOSPESO dal compositore");
			}
			break;
		case EI_EVENT_DEVICE_REMOVED:
			if (dispositivo == puntatore)
			{
				puntatore_pronto = false;
				dilo("il dispositivo e' stato TOLTO dal compositore");
			}
			break;
		case EI_EVENT_DISCONNECT:
			dilo("DISCONNESSO dal compositore");
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
		dilo("dispositivo pronto=%d  assoluto=%d  regione=%d (%.0f,%.0f %.0fx%.0f)",
		     puntatore_pronto, assoluto, regione_nota, reg_x, reg_y, reg_l, reg_a);
		return;
	}
	if (sscanf(riga, "scatto %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERRORE: nessun dispositivo pronto, lo scatto NON e' stato mandato");
			return;
		}
		ei_device_scroll_discrete(puntatore, dx, dy);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("SCATTO dx=%d dy=%d mandato", dx, dy);
		return;
	}
	/* Il movimento a mano: serve al controllo positivo — se la pagina vede
	 * muoversi il puntatore, la strada dall'iniettore alla pagina e' aperta. */
	if (sscanf(riga, "muovi %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERRORE: nessun dispositivo pronto");
			return;
		}
		if (regione_nota && assoluto)
			ei_device_pointer_motion_absolute(puntatore, reg_x + dx, reg_y + dy);
		else
			ei_device_pointer_motion(puntatore, dx, dy);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("MOSSO a %d,%d", dx, dy);
		return;
	}
	if (sscanf(riga, "bottone %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERRORE: nessun dispositivo pronto");
			return;
		}
		ei_device_button_button(puntatore, (uint32_t) dx, dy != 0);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("BOTTONE %d %s", dx, dy ? "giu'" : "su'");
		return;
	}
	if (sscanf(riga, "liscio %d %d", &dx, &dy) == 2)
	{
		if (!puntatore_pronto)
		{
			dilo("ERRORE: nessun dispositivo pronto, il liscio NON e' stato mandato");
			return;
		}
		ei_device_scroll_delta(puntatore, dx, dy);
		ei_device_frame(puntatore, ei_now(contesto));
		dilo("LISCIO dx=%d dy=%d mandato", dx, dy);
		return;
	}
	dilo("comando ignoto: «%s»", riga);
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
		dilo("ERRORE: bus di sessione non raggiungibile: %s", sbaglio->message);
		return 2;
	}
	fd_eis = apri_eis(bus, &sbaglio);
	if (fd_eis < 0)
	{
		dilo("ERRORE: %s", sbaglio->message);
		return 3;
	}

	contesto = ei_new_sender(NULL);
	ei_configure_name(contesto, "remotix-s7");
	if (ei_setup_backend_fd(contesto, fd_eis) != 0)
	{
		dilo("ERRORE: libei non ha accettato il descrittore di ConnectToEIS");
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
				dilo("standard input chiuso: esco");
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
