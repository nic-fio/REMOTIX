/*
 * appunti_kde — vedi `appunti_kde.h`.  I commenti che citano `kde.md` e i file
 * di KWin rimandano allo studio di v1, oggi in `STUDI.md` §kde.
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
#include "wlr-data-control-unstable-v1-client-protocol.h"

/* Quanto si aspetta chi legge o scrive gli appunti: dall'altra parte della
 * pipe c'e' un'applicazione qualunque, e puo' essersi piantata. */
#define ATTESA_TRASFERIMENTO_MS 5000

/* ⛔ IL PASSO MINIMO FRA DUE `set_selection`: klipper, oltre dieci cambi al
 *    secondo, considera la clipboard impazzita e smette di seguirla
 *    (`klipper/systemclipboard.cpp:50`) — senza un errore. */
#define PASSO_MINIMO_US 100000

/* La stessa fila di `appunti.c`, e nello stesso ordine: il primo dichiara la
 * codifica.  ⛔ Mai `application/x-kde-onlyReplaceEmpty`: KWin annullerebbe in
 * silenzio la selezione (`seat.cpp:200-226`). */
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
	struct wl_display *display;
	char socket[64];
	struct wl_registry *registro;
	struct zwlr_data_control_manager_v1 *gestore;
	struct wl_seat *seat;
	uint32_t versione_gestore;
	struct zwlr_data_control_device_v1 *dispositivo;

	GThread *pompa;
	int sveglia[2];

	/* Protegge lo stato qui sotto (i proxy Wayland si sincronizzano da se',
	 * i nostri puntatori no). */
	GMutex stato;
	Offerta *corrente;  /* la selezione della sessione, o NULL */
	Offerta *in_arrivo; /* annunciata, non ancora letta */
	struct zwlr_data_control_source_v1 *nostra;
	gint64 ultimo_set;
	GHashTable *richieste; /* serial → fd */
	guint32 prossimo_serial;

	/* Come in `appunti.c`: il lucchetto e' preso mentre una richiamata gira. */
	GMutex lucchetto;
	char *ultimo;
	size_t ultimo_byte;
	AppuntiSuTesto su_testo;
	AppuntiSuRichiesta su_richiesta;
	void *dati;
};

/* ------------------------------------------------------------------ *
 * Le offerte della sessione
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

/* L'annuncio e' il nostro?  Stessi tipi, tutti e soli. */
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
	/* L'offerta si aggancia a SE STESSA: gli `offer` arrivano prima di sapere
	 * se e' la selezione o la primaria, che arrivano sullo stesso dispositivo. */
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
	 * ⛔ L'ECO, che qui e' certa: `setSelection` di KWin avvisa TUTTI i data
	 *    control device, compreso il nostro (`seat.cpp:1257-1259`).  Il criterio
	 *    di v1 e' di STATO: finche' la sorgente e' ancora nostra (nessun
	 *    `cancelled`), un annuncio coi nostri tipi e' il nostro.  Quando
	 *    qualcun altro copia, il `cancelled` arriva PRIMA dell'annuncio.
	 */
	if (appunti->nostra && tipi_nostri(offerta)) {
		g_mutex_unlock(&appunti->stato);
		registro_dettaglio(REG_APPUNTI, "annuncio di ritorno dopo la nostra copia: ignorato");
		offerta_libera(offerta);
		return;
	}
	g_clear_pointer(&appunti->corrente, offerta_libera);
	appunti->corrente = offerta;
	/* Non si legge da qui: un `offer(mime)` puo' arrivare DOPO `selection`
	 * (`kde.md` §9).  Lo legge la pompa, dopo un giro completo. */
	appunti->in_arrivo = offerta;
	g_mutex_unlock(&appunti->stato);
}

/* La selezione primaria (il tasto centrale di X11) non ha un corrispondente
 * nel protocollo: si accetta e si butta. */
static void su_selezione_primaria(void *dati, struct zwlr_data_control_device_v1 *dispositivo,
                                  struct zwlr_data_control_offer_v1 *proxy)
{
	offerta_libera(offerta_di(proxy));
}

static void su_finito(void *dati, struct zwlr_data_control_device_v1 *dispositivo)
{
	registro_dice(REG_APPUNTI, "⛔ KWin ha chiuso il canale degli appunti: niente piu' "
	                           "copia-incolla in questa sessione");
}

static const struct zwlr_data_control_device_v1_listener ascolto_dispositivo = {
	su_offerta_nuova,
	su_selezione,
	su_finito,
	su_selezione_primaria,
};

/* ------------------------------------------------------------------ *
 * La nostra sorgente: il testo del CLIENT
 * ------------------------------------------------------------------ */
static void su_richiesta_dati(void *dati, struct zwlr_data_control_source_v1 *sorgente,
                              const char *mime, int32_t fd)
{
	AppuntiKde *appunti = dati;
	guint32 serial;
	bool qualcuno;

	/* ⛔ Qui non si scrive: il testo sta sul client e va chiesto.  Si mette da
	 *    parte il descrittore e si torna subito — e' il thread degli eventi. */
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
		/* Nessuno ascolta: si risponde con quel che c'e' (o si chiude). */
		appunti_kde_rispondi(appunti, serial, NULL, 0);
}

static void su_annullata(void *dati, struct zwlr_data_control_source_v1 *sorgente)
{
	AppuntiKde *appunti = dati;

	g_mutex_lock(&appunti->stato);
	if (appunti->nostra == sorgente)
		appunti->nostra = NULL; /* da adesso gli annunci sono veri */
	g_mutex_unlock(&appunti->stato);
	zwlr_data_control_source_v1_destroy(sorgente);
}

static const struct zwlr_data_control_source_v1_listener ascolto_sorgente = {
	su_richiesta_dati, su_annullata
};

/* ------------------------------------------------------------------ *
 * Il registro Wayland
 * ------------------------------------------------------------------ */
static void su_globale(void *dati, struct wl_registry *registro, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	AppuntiKde *appunti = dati;

	if (!g_strcmp0(interfaccia, zwlr_data_control_manager_v1_interface.name)) {
		/* La 2 aggiunge la primaria, che non ci serve: si lega quel che c'e'. */
		appunti->versione_gestore = MIN(versione, 2u);
		appunti->gestore = wl_registry_bind(registro, nome,
		                                    &zwlr_data_control_manager_v1_interface,
		                                    appunti->versione_gestore);
	} else if (!g_strcmp0(interfaccia, wl_seat_interface.name) && !appunti->seat) {
		appunti->seat = wl_registry_bind(registro, nome, &wl_seat_interface, 1);
	}
}

static void su_globale_via(void *dati, struct wl_registry *registro, uint32_t nome)
{
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

/* ------------------------------------------------------------------ *
 * Leggere il testo della sessione
 * ------------------------------------------------------------------ */
/* ⛔ `POLLHUP` in lettura vale come «pronto»: chi scrive e chiude (il caso
 *    normale) puo' far tornare la `poll` col solo `POLLHUP`, e i dati sono
 *    nel tubo (`[M]` v1, 8 agosto 2026). */
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

/* Un tipo, letto fino alla fine col tetto di `appunti.c` (tetto PIU' UNO: il
 * testo grande quanto il tetto e' lecito).  NULL con `perche` scritto. */
static GBytes *leggi_un_tipo(AppuntiKde *appunti, struct zwlr_data_control_offer_v1 *proxy,
                             const char *mime, const char **perche)
{
	int tubo[2];
	GByteArray *raccolta;

	if (pipe2(tubo, O_CLOEXEC) != 0) {
		*perche = "pipe non creata";
		return NULL;
	}
	zwlr_data_control_offer_v1_receive(proxy, mime, tubo[1]);
	wl_display_flush(appunti->display);
	/* ⛔ La nostra copia del lato di scrittura si chiude SUBITO, o la lettura
	 *    non finisce mai. */
	close(tubo[1]);

	raccolta = g_byte_array_new();
	for (;;) {
		guint8 pezzo[16384];
		ssize_t quanti;

		if (!pronto(tubo[0], POLLIN)) {
			close(tubo[0]);
			g_byte_array_unref(raccolta);
			*perche = "chi possiede gli appunti non ha scritto niente per 5 s";
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
			*perche = "appunti oltre il tetto (§5.4): lasciati dove sono, NON troncati";
			return NULL;
		}
		g_byte_array_append(raccolta, pezzo, (guint)quanti);
	}
	close(tubo[0]);
	return g_byte_array_free_to_bytes(raccolta);
}

/* Il testo della selezione corrente, per la fila dei tipi: il primo che
 * consegna un UTF-8 valido.  NULL se non c'e' testo (e lo dice). */
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
		registro_dettaglio(REG_APPUNTI, "la sessione non ha niente negli appunti");
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
			registro_dice(REG_APPUNTI, "⛔ «%s» non si legge: %s", TIPI_TESTO[i], perche);
			continue;
		}
		inizio = g_bytes_get_data(dati, &quanti);
		if (!g_utf8_validate_len(inizio, (gssize)quanti, NULL)) {
			registro_dice(REG_APPUNTI, "⛔ «%s» non e' UTF-8 valido (%zu byte): lo "
			                           "salto", TIPI_TESTO[i], (size_t)quanti);
			g_bytes_unref(dati);
			continue;
		}
		*byte = quanti;
		{
			char *testo = g_strndup(inizio, quanti);

			g_bytes_unref(dati);
			g_ptr_array_unref(tipi);
			registro_dettaglio(REG_APPUNTI, "letti %zu byte di «%s» dalla sessione",
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
		              "la sessione ha copiato qualcosa che non e' testo (%s): non si "
		              "annuncia.  ⚠ `DECISIONI.md` §5-ter.1 — solo testo",
		              elenco->str);
		g_string_free(elenco, TRUE);
	}
	g_ptr_array_unref(tipi);
	return NULL;
}

/* Consegna a chi ascolta il testo dell'ultimo annuncio. */
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
	registro_dice(REG_APPUNTI, "⭐ la sessione ha copiato %zu byte di testo", byte);
	g_free(testo);
}

/* ------------------------------------------------------------------ *
 * Il ciclo
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
	/* ⛔ Il giro completo PRIMA di leggere: gli `offer(mime)` possono arrivare
	 *    dopo il `selection` che li riguarda. */
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
	registro_dettaglio(REG_APPUNTI, "la connessione Wayland degli appunti si e' chiusa");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * La porta
 * ------------------------------------------------------------------ */
AppuntiKde *appunti_kde_apri(GError **sbaglio)
{
	AppuntiKde *appunti = g_new0(AppuntiKde, 1);

	appunti->sveglia[0] = appunti->sveglia[1] = -1;
	g_mutex_init(&appunti->stato);
	g_mutex_init(&appunti->lucchetto);
	appunti->richieste = g_hash_table_new(NULL, NULL);

	appunti->display = kwin_display_apri(appunti->socket, sizeof appunti->socket);
	if (!appunti->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun compositore Wayland raggiungibile per gli appunti");
		goto guasto;
	}
	appunti->registro = wl_display_get_registry(appunti->display);
	wl_registry_add_listener(appunti->registro, &ascolto_registro, appunti);
	wl_display_roundtrip(appunti->display);
	wl_display_roundtrip(appunti->display);
	if (!appunti->gestore) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "KWin non espone zwlr_data_control_manager_v1");
		goto guasto;
	}
	if (!appunti->seat) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun wl_seat: senza, non c'e' clipboard da chiedere");
		goto guasto;
	}
	appunti->dispositivo =
	    zwlr_data_control_manager_v1_get_data_device(appunti->gestore, appunti->seat);
	zwlr_data_control_device_v1_add_listener(appunti->dispositivo, &ascolto_dispositivo,
	                                         appunti);
	/* ⭐ KWin manda SUBITO la selezione corrente (`seat.cpp:228-229`), anche
	 *    vuota: e' l'asimmetria che su Mutter va chiesta (`appunti_leggi_adesso`).
	 *    Qui la si prende e basta: la lettura la fa `appunti_leggi_adesso`, come
	 *    su GNOME, quando `figlio.c` e' pronto a riceverla. */
	wl_display_roundtrip(appunti->display);
	wl_display_roundtrip(appunti->display);
	g_mutex_lock(&appunti->stato);
	appunti->in_arrivo = NULL;
	g_mutex_unlock(&appunti->stato);

	if (!g_unix_open_pipe(appunti->sveglia, O_CLOEXEC, NULL))
		appunti->sveglia[0] = appunti->sveglia[1] = -1;
	appunti->pompa = g_thread_new("remotix-appunti", thread_pompa, appunti);

	registro_dice(REG_APPUNTI, "⭐ appunti agganciati a KWin sul socket «%s» con "
	                           "zwlr_data_control_manager_v1 v%u",
	              appunti->socket, appunti->versione_gestore);
	return appunti;

guasto:
	appunti_kde_chiudi(appunti);
	return NULL;
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

	/* I trasferimenti rimasti a meta' si chiudono: chi aspetta vede una fine. */
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
		registro_dettaglio(REG_APPUNTI, "la sessione non aveva appunti da darci al "
		                                "momento dell'accensione: non e' un guasto");
		return;
	}
	registro_dice(REG_APPUNTI, "⭐ la sessione aveva gia' %zu byte negli appunti: li "
	                           "annuncio al client", byte);
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
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED, "appunti non aperti");
		return FALSE;
	}
	/* Il passo minimo verso klipper: si aspetta, non si salta. */
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

	/* ⚠ La sorgente vecchia NON si distrugge qui: KWin le manda `cancelled`, e
	 *   la distrugge quella richiamata. */
	g_mutex_lock(&appunti->stato);
	appunti->nostra = sorgente;
	g_mutex_unlock(&appunti->stato);

	zwlr_data_control_device_v1_set_selection(appunti->dispositivo, sorgente);
	wl_display_flush(appunti->display);
	registro_dettaglio(REG_APPUNTI, "offerto alla sessione il testo del client (%d tipi)",
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
		registro_dice(REG_APPUNTI, "⚠ risposta a una richiesta di appunti che non esiste "
		                           "(serial %u)", serial);
		return;
	}
	g_mutex_unlock(&appunti->stato);
	fd = GPOINTER_TO_INT(valore);

	/* ⭐ Come su GNOME: se il client non ha niente, si rende alla sessione il
	 *    testo che aveva LEI — collegarsi non cancella la clipboard del desktop. */
	if (!testo || byte == 0) {
		size_t quanti = 0;

		ripiego = appunti_kde_ultimo_testo(appunti, &quanti);
		if (ripiego && quanti > 0) {
			registro_dice(REG_APPUNTI, "⭐ il client non ha appunti per la richiesta %u: "
			                           "rendo alla sessione i %zu byte che aveva LEI",
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

	/* ⛔ Si chiude SEMPRE, anche senza dati: la fine del flusso e' la `close`. */
	while (testo && scritti < byte) {
		ssize_t fatti;

		if (!pronto(fd, POLLOUT)) {
			registro_dice(REG_APPUNTI, "⛔ chi sta incollando non legge: %zu byte su %zu, "
			                           "poi rinuncio", scritti, byte);
			break;
		}
		fatti = write(fd, testo + scritti, byte - scritti);
		if (fatti < 0 && (errno == EINTR || errno == EAGAIN))
			continue;
		if (fatti <= 0)
			break; /* EPIPE: chi incollava se n'e' andato */
		scritti += (size_t)fatti;
	}
	close(fd);
	if (testo)
		registro_dettaglio(REG_APPUNTI, "consegnati %zu byte alla sessione (richiesta %u)",
		                   scritti, serial);
	else
		registro_dettaglio(REG_APPUNTI, "richiesta %u chiusa con «non ce l'ho»", serial);
	g_free(ripiego);
}
