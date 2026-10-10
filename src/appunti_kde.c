/*
 * appunti_kde — see `appunti_kde.h`.  The comments citing `kde.md` and KWin's
 * files refer to v1's study, now in `STUDI.md` §kde.
 */
#include "appunti_kde.h"

#include <errno.h>
#include <fcntl.h>
#include <glib-unix.h>
#include <poll.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>

#include "kwin.h"
#include "registro.h"
#include "ext-data-control-v1-client-protocol.h"
#include "wlr-data-control-unstable-v1-client-protocol.h"

/* How long whoever reads or writes the clipboard waits: on the other side of the
 * pipe there is any application at all, and it may have hung. */
#define ATTESA_TRASFERIMENTO_MS 5000

/* ⛔ THE MINIMUM STEP BETWEEN TWO `set_selection`s: klipper, beyond ten changes a
 *    second, considers the clipboard gone mad and stops following it
 *    (`klipper/systemclipboard.cpp:50`) — without an error. */
#define PASSO_MINIMO_US 100000

/* The same row as `appunti.c`, and in the same order: the first declares the
 * encoding.  ⛔ Never `application/x-kde-onlyReplaceEmpty`: KWin would silently
 * cancel the selection (`seat.cpp:200-226`).
 * ⭐ PHASE 13 — on labwc that type does not exist at all (`STUDI.md` §xfce §8.3):
 *    and we never offer it nor read it (this row is the only one), ⇒
 *    no possible damage, `[R]`. */
static const char *const TIPI_TESTO[] = {
	"text/plain;charset=utf-8",
	"UTF8_STRING",
	"text/plain",
	NULL,
};

typedef struct {
	struct zwlr_data_control_offer_v1 *proxy;
	GPtrArray *mime;
} Offerta;

struct AppuntiKde {
	/* ⭐ PHASE 13 — who is on the other side, ONLY for the log lines:
	 *    «KWin» on KDE (the lines stay those of before, letter for letter),
	 *    «labwc» on XFCE.  ⛔ No branch of the protocol looks at it. */
	const char *compositore;
	struct wl_display *display;
	char socket[64];
	struct wl_registry *registro;
	struct zwlr_data_control_manager_v1 *gestore;
	struct wl_seat *seat;
	uint32_t versione_gestore;
	const char *protocollo; /* the name of the bound manager, for the log */
	uint32_t nome_ext, versione_ext; /* ext_data_control_manager_v1, if present */
	struct zwlr_data_control_device_v1 *dispositivo;

	GThread *pompa;
	int sveglia[2];

	/* Protects the state below (Wayland proxies synchronise themselves,
	 * our pointers do not). */
	GMutex stato;
	Offerta *corrente;  /* the session's selection, or NULL */
	Offerta *in_arrivo; /* announced, not yet read */
	struct zwlr_data_control_source_v1 *nostra;
	gint64 ultimo_set;
	GHashTable *richieste; /* serial → fd */
	guint32 prossimo_serial;

	/* As in `appunti.c`: the lock is held while a callback runs. */
	GMutex lucchetto;
	char *ultimo;
	size_t ultimo_byte;
	AppuntiSuTesto su_testo;
	AppuntiSuRichiesta su_richiesta;
	void *dati;
};

/* ------------------------------------------------------------------ *
 * The session's offers
 * ------------------------------------------------------------------ */
static void offerta_libera(Offerta *offerta)
{
	if (!offerta)
		return;
	if (offerta->proxy)
		zwlr_data_control_offer_v1_destroy(offerta->proxy);
	g_ptr_array_unref(offerta->mime);
	g_free(offerta);
}

static bool offerta_ha(const Offerta *offerta, const char *mime)
{
	for (guint i = 0; offerta && i < offerta->mime->len; i++)
		if (g_ascii_strcasecmp(g_ptr_array_index(offerta->mime, i), mime) == 0)
			return true;
	return false;
}

/* Is the announcement ours?  Same types, all and only those.
 *
 * ⭐ PHASE 13 — the caveat of `STUDI.md` §xfce §8.2 ("wlroots drops duplicate
 *    MIME types and the guard fails ⇒ loop") CANNOT trigger here, `[R]`:
 *    · wlroots drops an `offer` only if it is `strcmp`-equal to one already given
 *      (`wlr_data_control_v1.c:38-45`, 0.18.2), and repeats the types at the offer
 *      without filtering (`:346-351`);
 *    · the types we offer are ALWAYS and ONLY `TIPI_TESTO`, three strings
 *      that differ even ignoring case: no duplicate to
 *      drop ⇒ the echo comes back with three types, and the `len == 3` count holds.
 *    The caveat was v1's, which passed on the CLIENT's list of types.
 *    ⚠ And even if the guard failed there would be no loop: reading
 *      our own source from the pump that serves it delivers nothing (5 s of
 *      waiting, then "wrote nothing"), so no text goes back up to the client
 *      to be re-offered. */
static bool tipi_nostri(const Offerta *offerta)
{
	guint quanti = 0;

	for (int i = 0; TIPI_TESTO[i]; i++, quanti++)
		if (!offerta_ha(offerta, TIPI_TESTO[i]))
			return false;
	return offerta && offerta->mime->len == quanti;
}

static void su_tipo_offerto(void *dati, struct zwlr_data_control_offer_v1 *proxy,
                            const char *mime)
{
	Offerta *offerta = dati;

	if (mime && *mime)
		g_ptr_array_add(offerta->mime, g_strdup(mime));
}

static const struct zwlr_data_control_offer_v1_listener ascolto_offerta = { su_tipo_offerto };

static void su_offerta_nuova(void *dati, struct zwlr_data_control_device_v1 *dispositivo,
                             struct zwlr_data_control_offer_v1 *proxy)
{
	Offerta *offerta = g_new0(Offerta, 1);

	offerta->proxy = proxy;
	offerta->mime = g_ptr_array_new_with_free_func(g_free);
	/* The offer hooks onto ITSELF: the `offer`s arrive before knowing
	 * whether it is the selection or the primary, which arrive on the same device. */
	zwlr_data_control_offer_v1_add_listener(proxy, &ascolto_offerta, offerta);
}

static Offerta *offerta_di(struct zwlr_data_control_offer_v1 *proxy)
{
	return proxy ? wl_proxy_get_user_data((struct wl_proxy *)proxy) : NULL;
}

static void su_selezione(void *dati, struct zwlr_data_control_device_v1 *dispositivo,
                         struct zwlr_data_control_offer_v1 *proxy)
{
	AppuntiKde *appunti = dati;
	Offerta *offerta = offerta_di(proxy);

	g_mutex_lock(&appunti->stato);
	/*
	 * ⛔ THE ECHO, which here is certain: KWin's `setSelection` notifies ALL data
	 *    control devices, ours included (`seat.cpp:1257-1259`).  v1's criterion
	 *    is one of STATE: as long as the source is still ours (no
	 *    `cancelled`), an announcement with our types is ours.  When
	 *    someone else copies, the `cancelled` arrives BEFORE the announcement.
	 * ⭐ PHASE 13 — on labwc (wlroots 0.18.2) the same, `[R]` on the source:
	 *    every device is subscribed to `seat->events.set_selection` without a filter
	 *    on the originator (`wlr_data_control_v1.c:459-468`) ⇒ the echo is certain;
	 *    and `wlr_seat_set_selection` DESTROYS the old source (⇒
	 *    `cancelled`, `wlr_data_control_v1.c:145`) before emitting the
	 *    signal, in the same function (`wlr_data_device.c`).  The two
	 *    pieces of news travel on the same connection ⇒ they arrive in that order.
	 * ⚠ When whoever had copied DIES, `selection(NULL)` arrives: below
	 *   `corrente` becomes NULL and `in_arrivo` stays NULL ⇒ nothing is sent to
	 *   the client, and `ultimo` stays the earlier text (it is what is
	 *   given back to the session if the client has nothing).  In XFCE on Wayland
	 *   there is no clipboard manager: the desktop clipboard dies with
	 *   whoever copied, and it is NOT our job to keep it alive.  OUR
	 *   source instead lives as long as the child.
	 */
	if (appunti->nostra && tipi_nostri(offerta)) {
		g_mutex_unlock(&appunti->stato);
		registro_dettaglio(REG_APPUNTI, "return announcement after our own copy: ignored");
		offerta_libera(offerta);
		return;
	}
	g_clear_pointer(&appunti->corrente, offerta_libera);
	appunti->corrente = offerta;
	/* We do not read from here: an `offer(mime)` may arrive AFTER `selection`
	 * (`kde.md` §9).  The pump reads it, after a full roundtrip. */
	appunti->in_arrivo = offerta;
	g_mutex_unlock(&appunti->stato);
}

/* The primary selection (X11's middle button) has no counterpart
 * in the protocol: it is accepted and dropped. */
static void su_selezione_primaria(void *dati, struct zwlr_data_control_device_v1 *dispositivo,
                                  struct zwlr_data_control_offer_v1 *proxy)
{
	offerta_libera(offerta_di(proxy));
}

static void su_finito(void *dati, struct zwlr_data_control_device_v1 *dispositivo)
{
	const AppuntiKde *appunti = dati;

	registro_dice(REG_APPUNTI, "⛔ %s closed the clipboard channel: no more "
	                           "copy-paste in this session",
	              appunti->compositore);
}

static const struct zwlr_data_control_device_v1_listener ascolto_dispositivo = {
	su_offerta_nuova,
	su_selezione,
	su_finito,
	su_selezione_primaria,
};

/* ------------------------------------------------------------------ *
 * Our source: the CLIENT's text
 * ------------------------------------------------------------------ */
static void su_richiesta_dati(void *dati, struct zwlr_data_control_source_v1 *sorgente,
                              const char *mime, int32_t fd)
{
	AppuntiKde *appunti = dati;
	guint32 serial;
	bool qualcuno;

	/* ⛔ We do not write here: the text is on the client and must be asked for.  We put
	 *    the descriptor aside and return at once — it is the event thread. */
	g_mutex_lock(&appunti->stato);
	serial = ++appunti->prossimo_serial;
	g_hash_table_insert(appunti->richieste, GUINT_TO_POINTER(serial), GINT_TO_POINTER(fd));
	g_mutex_unlock(&appunti->stato);

	g_mutex_lock(&appunti->lucchetto);
	qualcuno = appunti->su_richiesta != NULL;
	if (qualcuno)
		appunti->su_richiesta(serial, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);

	if (!qualcuno)
		/* Nobody is listening: we answer with what there is (or close). */
		appunti_kde_rispondi(appunti, serial, NULL, 0);
}

static void su_annullata(void *dati, struct zwlr_data_control_source_v1 *sorgente)
{
	AppuntiKde *appunti = dati;

	g_mutex_lock(&appunti->stato);
	if (appunti->nostra == sorgente)
		appunti->nostra = NULL; /* from now on the announcements are real */
	g_mutex_unlock(&appunti->stato);
	zwlr_data_control_source_v1_destroy(sorgente);
}

static const struct zwlr_data_control_source_v1_listener ascolto_sorgente = {
	su_richiesta_dati, su_annullata
};

/* ------------------------------------------------------------------ *
 * The Wayland registry
 * ------------------------------------------------------------------ */
static void su_globale(void *dati, struct wl_registry *registro, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	AppuntiKde *appunti = dati;

	if (!g_strcmp0(interfaccia, zwlr_data_control_manager_v1_interface.name)) {
		/* Version 2 adds the primary, which we do not need: we bind what there is. */
		appunti->versione_gestore = MIN(versione, 2u);
		appunti->protocollo = zwlr_data_control_manager_v1_interface.name;
		appunti->gestore = wl_registry_bind(registro, nome,
		                                    &zwlr_data_control_manager_v1_interface,
		                                    appunti->versione_gestore);
	} else if (!g_strcmp0(interfaccia, ext_data_control_manager_v1_interface.name)) {
		/* Bound AFTER the registry roundtrip, and only if zwlr is missing: see
		 * `lega_ext_se_serve`. */
		appunti->nome_ext = nome;
		appunti->versione_ext = versione;
	} else if (!g_strcmp0(interfaccia, wl_seat_interface.name) && !appunti->seat) {
		appunti->seat = wl_registry_bind(registro, nome, &wl_seat_interface, 1);
	}
}

static void su_globale_via(void *dati, struct wl_registry *registro, uint32_t nome)
{
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

/* ⛔ [M] 6 Oct 2026, Ubuntu 26.04 / KWin 6.6.6: KWin NO LONGER exposes
 *    `zwlr_data_control_manager_v1`, only the standard `ext_data_control_manager_v1`
 *    (wayland-protocols, staging) ⇒ "the clipboard does NOT open" and F-014/F-014C/
 *    F-015C red.  On KWin 6.3 (Debian 13) the old one was still there.
 *    ⭐ The two protocols are IDENTICAL ON THE WIRE: same requests, same events,
 *    same arguments, in the same order (ext v1 = zwlr v2, primary included;
 *    the XMLs in `protocolli/` compared).  ⇒ We bind the manager with ITS name
 *    (`ext_...`, the one the compositor checks) and drive it with the
 *    zwlr functions: the opcodes and signatures are the same, and the children (device,
 *    source, offer) are born from new_id, where the interface name does not
 *    travel.  One code for both, instead of 800 doubled lines.
 *    zwlr is preferred when both are present: it is the path already tested. */
static void lega_ext_se_serve(AppuntiKde *appunti)
{
	if (appunti->gestore || !appunti->nome_ext)
		return;
	appunti->versione_gestore = 1;
	appunti->protocollo = ext_data_control_manager_v1_interface.name;
	appunti->gestore = (struct zwlr_data_control_manager_v1 *)wl_registry_bind(
	    appunti->registro, appunti->nome_ext, &ext_data_control_manager_v1_interface, 1);
}

/* ------------------------------------------------------------------ *
 * Reading the session's text
 * ------------------------------------------------------------------ */
/* ⛔ `POLLHUP` on read counts as "ready": whoever writes and closes (the normal
 *    case) can make `poll` return with only `POLLHUP`, and the data is
 *    in the pipe (`[M]` v1, 8 August 2026). */
static bool pronto(int fd, short cosa)
{
	struct pollfd sonda = { .fd = fd, .events = cosa, .revents = 0 };
	int esito;

	do
		esito = poll(&sonda, 1, ATTESA_TRASFERIMENTO_MS);
	while (esito < 0 && errno == EINTR);
	if (esito <= 0)
		return false;
	if (sonda.revents & cosa)
		return true;
	return (cosa & POLLIN) && (sonda.revents & POLLHUP);
}

/* One type, read to the end with the ceiling of `appunti.c` (ceiling PLUS ONE: a
 * text as large as the ceiling is lawful).  NULL with `perche` written. */
static GBytes *leggi_un_tipo(AppuntiKde *appunti, struct zwlr_data_control_offer_v1 *proxy,
                             const char *mime, const char **perche)
{
	int tubo[2];
	GByteArray *raccolta;

	if (pipe2(tubo, O_CLOEXEC) != 0) {
		*perche = "pipe not created";
		return NULL;
	}
	zwlr_data_control_offer_v1_receive(proxy, mime, tubo[1]);
	wl_display_flush(appunti->display);
	/* ⛔ Our copy of the write end is closed AT ONCE, or the read
	 *    never ends. */
	close(tubo[1]);

	raccolta = g_byte_array_new();
	for (;;) {
		guint8 pezzo[16384];
		ssize_t quanti;

		if (!pronto(tubo[0], POLLIN)) {
			close(tubo[0]);
			g_byte_array_unref(raccolta);
			*perche = "whoever owns the clipboard wrote nothing for 5 s";
			return NULL;
		}
		quanti = read(tubo[0], pezzo, sizeof pezzo);
		if (quanti < 0 && errno == EINTR)
			continue;
		if (quanti <= 0)
			break;
		if (raccolta->len + (guint)quanti > APPUNTI_TETTO) {
			close(tubo[0]);
			g_byte_array_unref(raccolta);
			*perche = "clipboard over the ceiling (§5.4): left where it is, NOT truncated";
			return NULL;
		}
		g_byte_array_append(raccolta, pezzo, (guint)quanti);
	}
	close(tubo[0]);
	return g_byte_array_free_to_bytes(raccolta);
}

/* The text of the current selection, along the row of types: the first that
 * delivers valid UTF-8.  NULL if there is no text (and it says so). */
static char *leggi_il_testo(AppuntiKde *appunti, size_t *byte)
{
	struct zwlr_data_control_offer_v1 *proxy = NULL;
	Offerta *offerta;
	GPtrArray *tipi = NULL;

	g_mutex_lock(&appunti->stato);
	offerta = appunti->corrente;
	if (offerta) {
		proxy = offerta->proxy;
		tipi = g_ptr_array_ref(offerta->mime);
	}
	g_mutex_unlock(&appunti->stato);

	if (!proxy || !tipi || tipi->len == 0) {
		if (tipi)
			g_ptr_array_unref(tipi);
		registro_dettaglio(REG_APPUNTI, "the session has nothing in the clipboard");
		return NULL;
	}

	for (int i = 0; TIPI_TESTO[i]; i++) {
		bool c_e = false;
		const char *perche = NULL;
		GBytes *dati;
		gsize quanti = 0;
		const char *inizio;

		for (guint k = 0; k < tipi->len && !c_e; k++)
			c_e = g_ascii_strcasecmp(g_ptr_array_index(tipi, k), TIPI_TESTO[i]) == 0;
		if (!c_e)
			continue;
		dati = leggi_un_tipo(appunti, proxy, TIPI_TESTO[i], &perche);
		if (!dati) {
			registro_dice(REG_APPUNTI, "⛔ «%s» cannot be read: %s", TIPI_TESTO[i], perche);
			continue;
		}
		inizio = g_bytes_get_data(dati, &quanti);
		if (!g_utf8_validate_len(inizio, (gssize)quanti, NULL)) {
			registro_dice(REG_APPUNTI, "⛔ «%s» is not valid UTF-8 (%zu bytes): "
			                           "skipping it", TIPI_TESTO[i], (size_t)quanti);
			g_bytes_unref(dati);
			continue;
		}
		*byte = quanti;
		{
			char *testo = g_strndup(inizio, quanti);

			g_bytes_unref(dati);
			g_ptr_array_unref(tipi);
			registro_dettaglio(REG_APPUNTI, "read %zu bytes of «%s» from the session",
			                   (size_t)quanti, TIPI_TESTO[i]);
			return testo;
		}
	}

	{
		GString *elenco = g_string_new(NULL);

		for (guint k = 0; k < tipi->len; k++)
			g_string_append_printf(elenco, "%s%s", k ? ", " : "",
			                       (const char *)g_ptr_array_index(tipi, k));
		registro_dice(REG_APPUNTI,
		              "the session copied something that is not text (%s): not "
		              "announced.  ⚠ `DECISIONI.md` §5-ter.1 — text only",
		              elenco->str);
		g_string_free(elenco, TRUE);
	}
	g_ptr_array_unref(tipi);
	return NULL;
}

/* Hands the listener the text of the last announcement. */
static void consegna_annuncio(AppuntiKde *appunti)
{
	char *testo;
	size_t byte = 0;
	bool c_era;

	g_mutex_lock(&appunti->stato);
	c_era = appunti->in_arrivo != NULL;
	appunti->in_arrivo = NULL;
	g_mutex_unlock(&appunti->stato);
	if (!c_era)
		return;

	testo = leggi_il_testo(appunti, &byte);
	if (!testo)
		return;
	g_mutex_lock(&appunti->lucchetto);
	g_free(appunti->ultimo);
	appunti->ultimo = g_strdup(testo);
	appunti->ultimo_byte = byte;
	if (appunti->su_testo)
		appunti->su_testo(testo, byte, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);
	registro_dice(REG_APPUNTI, "⭐ the session copied %zu bytes of text", byte);
	g_free(testo);
}

/* ------------------------------------------------------------------ *
 * The loop
 * ------------------------------------------------------------------ */
static bool gira(AppuntiKde *appunti, int attesa_ms)
{
	struct pollfd sonda[2];
	int quanti = 1;

	while (wl_display_prepare_read(appunti->display) != 0)
		if (wl_display_dispatch_pending(appunti->display) < 0)
			return false;
	if (wl_display_flush(appunti->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(appunti->display);
		return false;
	}
	sonda[0].fd = wl_display_get_fd(appunti->display);
	sonda[0].events = POLLIN;
	sonda[0].revents = 0;
	if (appunti->sveglia[0] >= 0) {
		sonda[1].fd = appunti->sveglia[0];
		sonda[1].events = POLLIN;
		sonda[1].revents = 0;
		quanti = 2;
	}
	if (poll(sonda, (nfds_t)quanti, attesa_ms) <= 0) {
		wl_display_cancel_read(appunti->display);
		return true;
	}
	if (quanti == 2 && (sonda[1].revents & POLLIN)) {
		wl_display_cancel_read(appunti->display);
		return false;
	}
	if (!(sonda[0].revents & POLLIN)) {
		wl_display_cancel_read(appunti->display);
		return !(sonda[0].revents & (POLLERR | POLLHUP));
	}
	if (wl_display_read_events(appunti->display) < 0)
		return false;
	if (wl_display_dispatch_pending(appunti->display) < 0)
		return false;
	/* ⛔ The full roundtrip BEFORE reading: the `offer(mime)`s may arrive
	 *    after the `selection` they belong to. */
	if (appunti->in_arrivo) {
		wl_display_roundtrip(appunti->display);
		consegna_annuncio(appunti);
	}
	return true;
}

static gpointer thread_pompa(gpointer dati)
{
	AppuntiKde *appunti = dati;

	while (gira(appunti, -1))
		;
	registro_dettaglio(REG_APPUNTI, "the clipboard's Wayland connection closed");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * The door
 * ------------------------------------------------------------------ */
/* ⭐ PHASE 13 — the same opening for the two families: only the name in the
 *    lines changes.  ⚠ `kwin_display_apri()` stays, and on labwc it is fine as
 *    it is: it takes `WAYLAND_DISPLAY` or the first `wayland-0..9` that answers,
 *    WITHOUT looking at who is behind it (`kwin.c`, `[R]`).  Moving it to a
 *    neutral file would mean touching `kwin.c`, which carries KDE's video, to
 *    gain only a name. */
static AppuntiKde *apri_su(const char *compositore, GError **sbaglio)
{
	AppuntiKde *appunti = g_new0(AppuntiKde, 1);

	appunti->compositore = compositore;
	appunti->sveglia[0] = appunti->sveglia[1] = -1;
	g_mutex_init(&appunti->stato);
	g_mutex_init(&appunti->lucchetto);
	appunti->richieste = g_hash_table_new(NULL, NULL);

	appunti->display = kwin_display_apri(appunti->socket, sizeof appunti->socket);
	if (!appunti->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable for the clipboard");
		goto guasto;
	}
	appunti->registro = wl_display_get_registry(appunti->display);
	wl_registry_add_listener(appunti->registro, &ascolto_registro, appunti);
	wl_display_roundtrip(appunti->display);
	wl_display_roundtrip(appunti->display);
	lega_ext_se_serve(appunti);
	if (!appunti->gestore) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "%s exposes neither zwlr_data_control_manager_v1 nor "
		            "ext_data_control_manager_v1", compositore);
		goto guasto;
	}
	if (!appunti->seat) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no wl_seat: without it, there is no clipboard to ask for");
		goto guasto;
	}
	appunti->dispositivo =
	    zwlr_data_control_manager_v1_get_data_device(appunti->gestore, appunti->seat);
	zwlr_data_control_device_v1_add_listener(appunti->dispositivo, &ascolto_dispositivo,
	                                         appunti);
	/* ⭐ KWin sends the current selection AT ONCE (`seat.cpp:228-229`), even
	 *    empty: it is the asymmetry that on Mutter must be asked for (`appunti_leggi_adesso`).
	 *    Here we just take it: the read is done by `appunti_leggi_adesso`, as
	 *    on GNOME, when `figlio.c` is ready to receive it. */
	wl_display_roundtrip(appunti->display);
	wl_display_roundtrip(appunti->display);
	g_mutex_lock(&appunti->stato);
	appunti->in_arrivo = NULL;
	g_mutex_unlock(&appunti->stato);

	if (!g_unix_open_pipe(appunti->sveglia, O_CLOEXEC, NULL))
		appunti->sveglia[0] = appunti->sveglia[1] = -1;
	appunti->pompa = g_thread_new("remotix-appunti", thread_pompa, appunti);

	registro_dice(REG_APPUNTI, "⭐ clipboard hooked to %s on socket «%s» with "
	                           "%s v%u",
	              compositore, appunti->socket, appunti->protocollo,
	              appunti->versione_gestore);
	return appunti;

guasto:
	appunti_kde_chiudi(appunti);
	return NULL;
}

AppuntiKde *appunti_kde_apri(GError **sbaglio)
{
	return apri_su("KWin", sbaglio);
}

AppuntiKde *appunti_kde_apri_wlroots(GError **sbaglio)
{
	return apri_su("labwc", sbaglio);
}

void appunti_kde_chiudi(AppuntiKde *appunti)
{
	GHashTableIter giro;
	gpointer chiave, valore;

	if (!appunti)
		return;
	appunti_kde_ascolta(appunti, NULL, NULL, NULL);

	if (appunti->sveglia[1] >= 0) {
		ssize_t scritti = write(appunti->sveglia[1], "x", 1);

		(void)scritti;
	}
	if (appunti->pompa)
		g_thread_join(appunti->pompa);

	/* Transfers left half way are closed: whoever waits sees an end. */
	g_hash_table_iter_init(&giro, appunti->richieste);
	while (g_hash_table_iter_next(&giro, &chiave, &valore))
		close(GPOINTER_TO_INT(valore));
	g_hash_table_unref(appunti->richieste);

	g_clear_pointer(&appunti->corrente, offerta_libera);
	if (appunti->nostra)
		zwlr_data_control_source_v1_destroy(appunti->nostra);
	if (appunti->dispositivo)
		zwlr_data_control_device_v1_destroy(appunti->dispositivo);
	if (appunti->gestore)
		zwlr_data_control_manager_v1_destroy(appunti->gestore);
	if (appunti->seat)
		wl_seat_destroy(appunti->seat);
	if (appunti->registro)
		wl_registry_destroy(appunti->registro);
	if (appunti->display)
		wl_display_disconnect(appunti->display);
	for (int i = 0; i < 2; i++)
		if (appunti->sveglia[i] >= 0)
			close(appunti->sveglia[i]);
	g_free(appunti->ultimo);
	g_mutex_clear(&appunti->stato);
	g_mutex_clear(&appunti->lucchetto);
	g_free(appunti);
}

void appunti_kde_ascolta(AppuntiKde *appunti, AppuntiSuTesto su_testo,
                         AppuntiSuRichiesta su_richiesta, void *dati)
{
	if (!appunti)
		return;
	g_mutex_lock(&appunti->lucchetto);
	appunti->su_testo = su_testo;
	appunti->su_richiesta = su_richiesta;
	appunti->dati = dati;
	g_mutex_unlock(&appunti->lucchetto);
}

char *appunti_kde_ultimo_testo(AppuntiKde *appunti, size_t *byte)
{
	char *copia;

	if (!appunti)
		return NULL;
	g_mutex_lock(&appunti->lucchetto);
	copia = appunti->ultimo ? g_strdup(appunti->ultimo) : NULL;
	if (byte)
		*byte = appunti->ultimo ? appunti->ultimo_byte : 0;
	g_mutex_unlock(&appunti->lucchetto);
	return copia;
}

void appunti_kde_leggi_adesso(AppuntiKde *appunti)
{
	char *testo;
	size_t byte = 0;

	if (!appunti)
		return;
	testo = leggi_il_testo(appunti, &byte);
	if (!testo) {
		registro_dettaglio(REG_APPUNTI, "the session had no clipboard to give us at the "
		                                "time of switching on: it is not a fault");
		return;
	}
	registro_dice(REG_APPUNTI, "⭐ the session already had %zu bytes in the clipboard: "
	                           "announcing them to the client", byte);
	g_mutex_lock(&appunti->lucchetto);
	g_free(appunti->ultimo);
	appunti->ultimo = g_strdup(testo);
	appunti->ultimo_byte = byte;
	if (appunti->su_testo)
		appunti->su_testo(testo, byte, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);
	g_free(testo);
}

gboolean appunti_kde_offri(AppuntiKde *appunti, GError **sbaglio)
{
	struct zwlr_data_control_source_v1 *sorgente;
	gint64 adesso;

	if (!appunti || !appunti->gestore) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED, "clipboard not open");
		return FALSE;
	}
	/* The minimum step towards klipper: we wait, we do not skip. */
	g_mutex_lock(&appunti->stato);
	adesso = g_get_monotonic_time();
	if (appunti->ultimo_set && adesso - appunti->ultimo_set < PASSO_MINIMO_US) {
		gint64 resta = PASSO_MINIMO_US - (adesso - appunti->ultimo_set);

		g_mutex_unlock(&appunti->stato);
		g_usleep((gulong)resta);
		g_mutex_lock(&appunti->stato);
	}
	appunti->ultimo_set = g_get_monotonic_time();
	g_mutex_unlock(&appunti->stato);

	sorgente = zwlr_data_control_manager_v1_create_data_source(appunti->gestore);
	zwlr_data_control_source_v1_add_listener(sorgente, &ascolto_sorgente, appunti);
	for (int i = 0; TIPI_TESTO[i]; i++)
		zwlr_data_control_source_v1_offer(sorgente, TIPI_TESTO[i]);

	/* ⚠ The old source is NOT destroyed here: KWin sends it `cancelled`, and
	 *   that callback destroys it. */
	g_mutex_lock(&appunti->stato);
	appunti->nostra = sorgente;
	g_mutex_unlock(&appunti->stato);

	zwlr_data_control_device_v1_set_selection(appunti->dispositivo, sorgente);
	wl_display_flush(appunti->display);
	registro_dettaglio(REG_APPUNTI, "offered the client's text to the session (%d types)",
	                   (int)(sizeof TIPI_TESTO / sizeof *TIPI_TESTO) - 1);
	return TRUE;
}

void appunti_kde_rispondi(AppuntiKde *appunti, uint32_t serial, const char *testo,
                          size_t byte)
{
	gpointer valore;
	char *ripiego = NULL;
	size_t scritti = 0;
	int fd;

	if (!appunti)
		return;
	g_mutex_lock(&appunti->stato);
	if (!g_hash_table_steal_extended(appunti->richieste, GUINT_TO_POINTER(serial), NULL,
	                                 &valore)) {
		g_mutex_unlock(&appunti->stato);
		registro_dice(REG_APPUNTI, "⚠ answer to a clipboard request that does not exist "
		                           "(serial %u)", serial);
		return;
	}
	g_mutex_unlock(&appunti->stato);
	fd = GPOINTER_TO_INT(valore);

	/* ⭐ As on GNOME: if the client has nothing, the session gets back the
	 *    text IT had — connecting does not erase the desktop clipboard. */
	if (!testo || byte == 0) {
		size_t quanti = 0;

		ripiego = appunti_kde_ultimo_testo(appunti, &quanti);
		if (ripiego && quanti > 0) {
			registro_dice(REG_APPUNTI, "⭐ the client has no clipboard for request %u: "
			                           "giving back to the session the %zu bytes IT had",
			              serial, quanti);
			testo = ripiego;
			byte = quanti;
		}
	} else {
		g_mutex_lock(&appunti->lucchetto);
		g_free(appunti->ultimo);
		appunti->ultimo = g_strndup(testo, byte);
		appunti->ultimo_byte = byte;
		g_mutex_unlock(&appunti->lucchetto);
	}

	/* ⛔ It is ALWAYS closed, even without data: the end of the stream is the `close`. */
	while (testo && scritti < byte) {
		ssize_t fatti;

		if (!pronto(fd, POLLOUT)) {
			registro_dice(REG_APPUNTI, "⛔ whoever is pasting does not read: %zu bytes of %zu, "
			                           "then I give up", scritti, byte);
			break;
		}
		fatti = write(fd, testo + scritti, byte - scritti);
		if (fatti < 0 && (errno == EINTR || errno == EAGAIN))
			continue;
		if (fatti <= 0)
			break; /* EPIPE: whoever was pasting has gone */
		scritti += (size_t)fatti;
	}
	close(fd);
	if (testo)
		registro_dettaglio(REG_APPUNTI, "delivered %zu bytes to the session (request %u)",
		                   scritti, serial);
	else
		registro_dettaglio(REG_APPUNTI, "request %u closed with «I do not have it»", serial);
	g_free(ripiego);
}
