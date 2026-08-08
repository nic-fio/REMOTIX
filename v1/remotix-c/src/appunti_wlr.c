#include "appunti_wlr.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>

#include "kwin.h"
#include "registro.h"
#include "wlr-data-control-unstable-v1-client-protocol.h"

/*
 * Quanto si aspetta chi legge o scrive la clipboard.
 *
 * Dall'altra parte della pipe c'e' un'applicazione qualunque, e un'applicazione
 * qualunque puo' essersi piantata.  Senza tetto, un incolla su un programma
 * bloccato terrebbe fermo un thread nostro per sempre.
 */
#define ATTESA_TRASFERIMENTO_MS 5000

/*
 * ⛔ IL PASSO MINIMO FRA DUE `set_selection`, E NON E' PRUDENZA NOSTRA.
 *    klipper si difende dai cicli contando i cambi: oltre **dieci al secondo**
 *    considera la clipboard impazzita e smette di seguirla
 *    (`klipper/systemclipboard.cpp:50`).  Chi supera quel ritmo non riceve un
 *    errore: si ritrova gli appunti che non si aggiornano piu'.
 */
#define PASSO_MINIMO_US 100000

typedef struct
{
	struct zwlr_data_control_offer_v1 *proxy;
	GPtrArray *mime; /* char*, terminato da NULL quando si consegna */
} Offerta;

struct AppuntiWlr
{
	struct wl_display *display;
	char *socket;
	struct wl_registry *registro;
	struct zwlr_data_control_manager_v1 *gestore;
	struct wl_seat *seat;
	uint32_t versione_gestore;
	struct zwlr_data_control_device_v1 *dispositivo;

	GThread *pompa;
	int sveglia[2];

	/* Protegge tutto quel che segue.  I proxy Wayland si possono usare da piu'
	 * thread — libwayland si sincronizza da se' — ma i NOSTRI puntatori no. */
	GMutex lucchetto;
	Offerta *corrente;   /* la selezione della sessione, o NULL */
	Offerta *in_arrivo;  /* annunciata, non ancora consegnata a chi ascolta */
	GStrv ultimi_tipi;   /* la memoria che sopravvive alla connessione */

	struct zwlr_data_control_source_v1 *nostra;
	GStrv nostri_tipi;
	gint64 ultimo_set;

	GHashTable *richieste; /* serial → fd, i trasferimenti che il client deve servire */
	guint32 prossimo_serial;

	GMutex uso_richiamate;
	AppuntiSuOfferta su_offerta;
	AppuntiSuRichiesta su_richiesta;
	gpointer dati;
};

/* ------------------------------------------------------------------ *
 * Le offerte
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

/* I tipi di un'offerta, nella forma che `appunti.h` promette. */
static GStrv offerta_tipi(const Offerta *offerta)
{
	GPtrArray *copia = g_ptr_array_new();

	if (offerta)
		for (guint i = 0; i < offerta->mime->len; i++)
			g_ptr_array_add(copia, g_strdup(g_ptr_array_index(offerta->mime, i)));
	g_ptr_array_add(copia, NULL);
	return (GStrv) g_ptr_array_free(copia, FALSE);
}

static gboolean tipi_uguali(GStrv a, const Offerta *offerta)
{
	guint quanti_a = a ? g_strv_length(a) : 0;

	if (!offerta)
		return quanti_a == 0;
	if (quanti_a != offerta->mime->len)
		return FALSE;
	for (guint i = 0; i < offerta->mime->len; i++)
		if (!g_strv_contains((const char *const *) a, g_ptr_array_index(offerta->mime, i)))
			return FALSE;
	return TRUE;
}

static void su_tipo_offerto(void *dati, struct zwlr_data_control_offer_v1 *proxy, const char *mime)
{
	Offerta *offerta = dati;

	(void) proxy;
	if (mime && *mime)
		g_ptr_array_add(offerta->mime, g_strdup(mime));
}

static const struct zwlr_data_control_offer_v1_listener ascolto_offerta = { su_tipo_offerto };

/* ------------------------------------------------------------------ *
 * Il dispositivo: quel che la SESSIONE copia
 * ------------------------------------------------------------------ */
static void su_offerta_nuova(void *dati, struct zwlr_data_control_device_v1 *dispositivo,
                             struct zwlr_data_control_offer_v1 *proxy)
{
	Offerta *offerta = g_new0(Offerta, 1);

	(void) dati;
	(void) dispositivo;
	offerta->proxy = proxy;
	offerta->mime = g_ptr_array_new_with_free_func(g_free);
	/*
	 * L'offerta si aggancia a SE STESSA come dato dell'ascoltatore: gli eventi
	 * `offer` arrivano prima che si sappia a quale selezione apparterra', e
	 * tenerli in un campo condiviso li mescolerebbe con quelli della selezione
	 * primaria, che arriva sullo stesso dispositivo.
	 */
	zwlr_data_control_offer_v1_add_listener(proxy, &ascolto_offerta, offerta);
}

/* L'offerta che porta questo proxy, staccata dall'ascoltatore. */
static Offerta *offerta_di(struct zwlr_data_control_offer_v1 *proxy)
{
	return proxy ? wl_proxy_get_user_data((struct wl_proxy *) proxy) : NULL;
}

static void su_selezione(void *dati, struct zwlr_data_control_device_v1 *dispositivo,
                         struct zwlr_data_control_offer_v1 *proxy)
{
	AppuntiWlr *appunti = dati;
	Offerta *offerta = offerta_di(proxy);

	(void) dispositivo;

	g_mutex_lock(&appunti->lucchetto);

	/*
	 * ⛔ L'ECO, che qui e' certa e non probabile.
	 *
	 *    `setSelection` di KWin cicla su TUTTI i data control device, compreso
	 *    quello che ha appena messo la selezione (`seat.cpp:1257-1259`).  Quindi
	 *    ogni nostra scrittura ci torna indietro come se qualcuno nella sessione
	 *    avesse copiato — e girarla al client significa entrare nel ciclo, mentre
	 *    leggerla significa chiedere i dati al nostro stesso source, cioe' allo
	 *    stesso thread che sta rispondendo.
	 *
	 * ⛔ IL CRITERIO NON E' «LA PRIMA DOPO LA NOSTRA», ed e' meglio di quello che
	 *    `kde.md` §9 proponeva: si guarda se la sorgente e' ANCORA NOSTRA.
	 *    Finche' nessun altro ha copiato, KWin non ci ha mandato `cancelled`, e
	 *    un annuncio con i nostri stessi tipi non puo' che essere il nostro.
	 *    Quando qualcun altro copia, il `cancelled` arriva PRIMA dell'annuncio —
	 *    e' lo stesso `setSelection` a mandarlo — quindi a quel punto
	 *    `nostra` e' gia' NULL e l'annuncio passa.  Nessun contatore, nessuna
	 *    finestra temporale: solo stato vero.
	 */
	if (appunti->nostra && tipi_uguali(appunti->nostri_tipi, offerta))
	{
		diagnostica("annuncio di ritorno dopo la nostra copia: ignorato");
		g_mutex_unlock(&appunti->lucchetto);
		offerta_libera(offerta);
		return;
	}

	g_clear_pointer(&appunti->corrente, offerta_libera);
	appunti->corrente = offerta;
	/*
	 * Non si annuncia da qui: un `offer(mime)` puo' arrivare DOPO `selection`, e
	 * chi legge l'elenco adesso lo legge incompleto (`kde.md` §9).  Si segna, e
	 * la pompa lo consegna dopo un giro completo.
	 */
	appunti->in_arrivo = offerta;
	g_mutex_unlock(&appunti->lucchetto);
}

/*
 * La selezione primaria — il tasto centrale di X11 — non ha corrispondente in
 * RDP: si accetta l'offerta per non lasciare oggetti appesi, e la si butta.
 */
static void su_selezione_primaria(void *dati, struct zwlr_data_control_device_v1 *dispositivo,
                                  struct zwlr_data_control_offer_v1 *proxy)
{
	(void) dati;
	(void) dispositivo;
	offerta_libera(offerta_di(proxy));
}

static void su_finito(void *dati, struct zwlr_data_control_device_v1 *dispositivo)
{
	(void) dati;
	(void) dispositivo;
	avviso("il compositore ha chiuso il canale degli appunti: niente piu' copia-incolla");
}

static const struct zwlr_data_control_device_v1_listener ascolto_dispositivo = {
	su_offerta_nuova,
	su_selezione,
	su_finito,
	su_selezione_primaria,
};

/* ------------------------------------------------------------------ *
 * La nostra sorgente: quel che il CLIENT ha copiato
 * ------------------------------------------------------------------ */
static void su_richiesta_dati(void *dati, struct zwlr_data_control_source_v1 *sorgente,
                              const char *mime, int32_t fd)
{
	AppuntiWlr *appunti = dati;
	guint32 serial;
	AppuntiSuRichiesta richiamata;
	gpointer dati_richiamata;

	(void) sorgente;

	/*
	 * ⛔ QUI NON SI SCRIVE NIENTE, e non e' pigrizia: i dati non li abbiamo.
	 *    Stanno sul client, e vanno chiesti sul canale `cliprdr`.  Si mette da
	 *    parte il descrittore, si sveglia chi sa chiedere, e si torna subito —
	 *    perche' questo e' il thread che fa girare gli eventi, e KWin ha gia'
	 *    chiuso la propria copia del descrittore: se ci fermassimo qui, si
	 *    fermerebbe tutto il resto della clipboard.
	 */
	g_mutex_lock(&appunti->lucchetto);
	serial = ++appunti->prossimo_serial;
	g_hash_table_insert(appunti->richieste, GUINT_TO_POINTER(serial), GINT_TO_POINTER(fd));
	g_mutex_unlock(&appunti->lucchetto);

	g_mutex_lock(&appunti->uso_richiamate);
	richiamata = appunti->su_richiesta;
	dati_richiamata = appunti->dati;
	if (richiamata)
		richiamata(mime, serial, dati_richiamata);
	g_mutex_unlock(&appunti->uso_richiamate);

	if (!richiamata)
	{
		/* Nessuno ascolta: si chiude subito, perche' un descrittore lasciato
		 * aperto e' un'applicazione che aspetta per sempre. */
		diagnostica("la sessione chiede «%s» ma nessun client e' collegato: chiudo", mime);
		g_mutex_lock(&appunti->lucchetto);
		if (g_hash_table_steal(appunti->richieste, GUINT_TO_POINTER(serial)))
			close(fd);
		g_mutex_unlock(&appunti->lucchetto);
	}
}

static void su_annullata(void *dati, struct zwlr_data_control_source_v1 *sorgente)
{
	AppuntiWlr *appunti = dati;

	g_mutex_lock(&appunti->lucchetto);
	if (appunti->nostra == sorgente)
	{
		/* Qualcuno nella sessione ha copiato: da adesso la selezione non e'
		 * piu' nostra, e gli annunci che arrivano sono veri. */
		appunti->nostra = NULL;
		g_clear_pointer(&appunti->nostri_tipi, g_strfreev);
	}
	g_mutex_unlock(&appunti->lucchetto);
	zwlr_data_control_source_v1_destroy(sorgente);
}

static const struct zwlr_data_control_source_v1_listener ascolto_sorgente = { su_richiesta_dati,
	                                                                          su_annullata };

/* ------------------------------------------------------------------ *
 * Il registro
 * ------------------------------------------------------------------ */
static void su_globale(void *dati, struct wl_registry *registro, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	AppuntiWlr *appunti = dati;

	if (!g_strcmp0(interfaccia, zwlr_data_control_manager_v1_interface.name))
	{
		/*
		 * ⚠ Si lega la versione che il compositore ANNUNCIA, non quella per cui
		 *   l'XML e' scritto: chiederne una piu' alta e' un errore di protocollo
		 *   che chiude la connessione.  La 2 aggiunge la selezione primaria, che
		 *   non ci serve — quindi la 1 basta e la 2 non fa male.
		 */
		appunti->versione_gestore = MIN(versione, 2u);
		appunti->gestore = wl_registry_bind(registro, nome, &zwlr_data_control_manager_v1_interface,
		                                    appunti->versione_gestore);
	}
	else if (!g_strcmp0(interfaccia, wl_seat_interface.name) && !appunti->seat)
	{
		appunti->seat = wl_registry_bind(registro, nome, &wl_seat_interface, 1);
	}
}

static void su_globale_via(void *dati, struct wl_registry *registro, uint32_t nome)
{
	(void) dati;
	(void) registro;
	(void) nome;
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

/* ------------------------------------------------------------------ *
 * Il ciclo
 * ------------------------------------------------------------------ */
/* Consegna a chi ascolta l'annuncio messo da parte, se ce n'e' uno. */
static void consegna_annuncio(AppuntiWlr *appunti)
{
	g_auto(GStrv) tipi = NULL;
	AppuntiSuOfferta richiamata;
	gpointer dati;

	g_mutex_lock(&appunti->lucchetto);
	if (!appunti->in_arrivo)
	{
		g_mutex_unlock(&appunti->lucchetto);
		return;
	}
	tipi = offerta_tipi(appunti->in_arrivo);
	appunti->in_arrivo = NULL;
	g_strfreev(appunti->ultimi_tipi);
	appunti->ultimi_tipi = g_strdupv(tipi);
	g_mutex_unlock(&appunti->lucchetto);

	informazione("la sessione ha copiato qualcosa: %u tipi", g_strv_length(tipi));

	g_mutex_lock(&appunti->uso_richiamate);
	richiamata = appunti->su_offerta;
	dati = appunti->dati;
	if (richiamata)
		richiamata((const char *const *) tipi, dati);
	g_mutex_unlock(&appunti->uso_richiamate);
}

/* Un giro di eventi, con scadenza.  Copiato da `kwin.c` e per la stessa
 * ragione: `wl_display_dispatch` senza tetto non si sveglia mai. */
static gboolean gira(AppuntiWlr *appunti, int attesa_ms)
{
	struct pollfd sonda[2];
	int quanti = 1;

	while (wl_display_prepare_read(appunti->display) != 0)
		if (wl_display_dispatch_pending(appunti->display) < 0)
			return FALSE;
	if (wl_display_flush(appunti->display) < 0 && errno != EAGAIN)
	{
		wl_display_cancel_read(appunti->display);
		return FALSE;
	}

	sonda[0].fd = wl_display_get_fd(appunti->display);
	sonda[0].events = POLLIN;
	sonda[0].revents = 0;
	if (appunti->sveglia[0] >= 0)
	{
		sonda[1].fd = appunti->sveglia[0];
		sonda[1].events = POLLIN;
		sonda[1].revents = 0;
		quanti = 2;
	}

	if (poll(sonda, (nfds_t) quanti, attesa_ms) <= 0)
	{
		wl_display_cancel_read(appunti->display);
		return TRUE;
	}
	if (quanti == 2 && (sonda[1].revents & POLLIN))
	{
		wl_display_cancel_read(appunti->display);
		return FALSE;
	}
	if (!(sonda[0].revents & POLLIN))
	{
		wl_display_cancel_read(appunti->display);
		return !(sonda[0].revents & (POLLERR | POLLHUP));
	}

	if (wl_display_read_events(appunti->display) < 0)
		return FALSE;
	if (wl_display_dispatch_pending(appunti->display) < 0)
		return FALSE;

	/*
	 * ⛔ IL GIRO COMPLETO PRIMA DI ANNUNCIARE, e serve davvero.
	 *    Gli `offer(mime)` possono arrivare dopo il `selection` che li riguarda:
	 *    consegnare l'elenco appena arriva l'evento significa consegnarlo
	 *    monco, e un client che riceve «testo semplice» quando c'era anche
	 *    «HTML» incolla la cosa sbagliata senza che nessuno se ne accorga.
	 */
	if (appunti->in_arrivo)
	{
		wl_display_roundtrip(appunti->display);
		consegna_annuncio(appunti);
	}
	return TRUE;
}

static gpointer thread_pompa(gpointer dati)
{
	AppuntiWlr *appunti = dati;

	while (gira(appunti, -1))
		;
	diagnostica("la connessione Wayland degli appunti si e' chiusa");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * Apertura e chiusura
 * ------------------------------------------------------------------ */
AppuntiWlr *appunti_wlr_apri(GError **sbaglio)
{
	AppuntiWlr *appunti = g_new0(AppuntiWlr, 1);

	appunti->sveglia[0] = -1;
	appunti->sveglia[1] = -1;
	g_mutex_init(&appunti->lucchetto);
	g_mutex_init(&appunti->uso_richiamate);
	appunti->richieste = g_hash_table_new(NULL, NULL);

	appunti->display = kwin_display_apri(&appunti->socket);
	if (!appunti->display)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun compositore Wayland raggiungibile per gli appunti");
		goto guasto;
	}

	appunti->registro = wl_display_get_registry(appunti->display);
	wl_registry_add_listener(appunti->registro, &ascolto_registro, appunti);
	/* Due giri: il primo porta i globali, il secondo le risposte ai bind. */
	wl_display_roundtrip(appunti->display);
	wl_display_roundtrip(appunti->display);

	if (!appunti->gestore)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "questo compositore non espone zwlr_data_control_manager_v1");
		goto guasto;
	}
	if (!appunti->seat)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun wl_seat: senza, non c'e' clipboard da chiedere");
		goto guasto;
	}

	appunti->dispositivo = zwlr_data_control_manager_v1_get_data_device(appunti->gestore,
	                                                                   appunti->seat);
	zwlr_data_control_device_v1_add_listener(appunti->dispositivo, &ascolto_dispositivo, appunti);

	/*
	 * ⭐ E QUI ARRIVA GIA' LA SELEZIONE CORRENTE, senza chiederla.
	 *    `registerDataControlDevice` manda subito selezione e selezione primaria
	 *    (`seat.cpp:228-229`): e' l'asimmetria che su Mutter ci era costata, la'
	 *    chi si ricollegava non riceveva alcun annuncio e la memoria dei tipi
	 *    dovevamo tenerla noi.  ⚠ Se non c'e' selezione l'annuncio arriva
	 *    comunque, VUOTO: «nessuna selezione» e «non l'ho ancora saputo» qui si
	 *    somigliano, e vanno distinti guardando l'offerta, non l'evento.
	 */
	wl_display_roundtrip(appunti->display);
	consegna_annuncio(appunti);

	if (pipe(appunti->sveglia) != 0)
	{
		appunti->sveglia[0] = -1;
		appunti->sveglia[1] = -1;
	}
	appunti->pompa = g_thread_new("remotix-appunti", thread_pompa, appunti);

	informazione("appunti agganciati a «%s» con zwlr_data_control_manager_v1 v%u",
	             appunti->socket, appunti->versione_gestore);
	return appunti;

guasto:
	appunti_wlr_chiudi(appunti);
	return NULL;
}

void appunti_wlr_chiudi(AppuntiWlr *appunti)
{
	GHashTableIter giro;
	gpointer chiave, valore;

	if (!appunti)
		return;

	/* Prima si ferma la pompa, poi si tocca il display: sono lo stesso oggetto
	 * e la pompa lo sta leggendo. */
	if (appunti->sveglia[1] >= 0)
	{
		ssize_t scritti = write(appunti->sveglia[1], "x", 1);

		(void) scritti;
	}
	if (appunti->pompa)
		g_thread_join(appunti->pompa);

	/* I trasferimenti rimasti a meta' si chiudono: chi aspetta deve vedere una
	 * fine, foss'anche vuota. */
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

	g_strfreev(appunti->ultimi_tipi);
	g_strfreev(appunti->nostri_tipi);
	g_free(appunti->socket);
	g_mutex_clear(&appunti->lucchetto);
	g_mutex_clear(&appunti->uso_richiamate);
	g_free(appunti);
}

/* ------------------------------------------------------------------ *
 * La porta
 * ------------------------------------------------------------------ */
GStrv appunti_wlr_ultimi_tipi(AppuntiWlr *appunti)
{
	GStrv copia;

	if (!appunti)
		return NULL;
	g_mutex_lock(&appunti->lucchetto);
	copia = appunti->ultimi_tipi ? g_strdupv(appunti->ultimi_tipi) : NULL;
	g_mutex_unlock(&appunti->lucchetto);
	return copia;
}

void appunti_wlr_ascolta(AppuntiWlr *appunti, AppuntiSuOfferta su_offerta,
                         AppuntiSuRichiesta su_richiesta, gpointer dati)
{
	if (!appunti)
		return;
	/* Il lucchetto e' preso mentre le richiamate girano: chi le stacca aspetta
	 * che finiscano, ed e' la promessa scritta in `appunti.h`. */
	g_mutex_lock(&appunti->uso_richiamate);
	appunti->su_offerta = su_offerta;
	appunti->su_richiesta = su_richiesta;
	appunti->dati = dati;
	g_mutex_unlock(&appunti->uso_richiamate);
}

gboolean appunti_wlr_offri(AppuntiWlr *appunti, const char *const *mime, GError **sbaglio)
{
	struct zwlr_data_control_source_v1 *sorgente;
	gint64 adesso;

	if (!appunti || !appunti->gestore)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED, "appunti non aperti");
		return FALSE;
	}
	if (!mime || !mime[0])
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "un annuncio senza tipi non e' un annuncio");
		return FALSE;
	}

	/* Il passo minimo verso klipper: si aspetta, non si salta.  Saltare
	 * significherebbe perdere una copia dell'utente. */
	g_mutex_lock(&appunti->lucchetto);
	adesso = g_get_monotonic_time();
	if (appunti->ultimo_set && adesso - appunti->ultimo_set < PASSO_MINIMO_US)
	{
		gint64 resta = PASSO_MINIMO_US - (adesso - appunti->ultimo_set);

		g_mutex_unlock(&appunti->lucchetto);
		g_usleep((gulong) resta);
		g_mutex_lock(&appunti->lucchetto);
	}
	appunti->ultimo_set = g_get_monotonic_time();
	g_mutex_unlock(&appunti->lucchetto);

	sorgente = zwlr_data_control_manager_v1_create_data_source(appunti->gestore);
	zwlr_data_control_source_v1_add_listener(sorgente, &ascolto_sorgente, appunti);
	for (guint i = 0; mime[i]; i++)
	{
		/*
		 * ⛔ MAI DICHIARARE `application/x-kde-onlyReplaceEmpty`.  E' il tipo con
		 *    cui klipper marca il proprio ripristino, e KWin ha un aggiramento
		 *    dedicato (`seat.cpp:200-226`) che ANNULLA IN SILENZIO un
		 *    `set_selection` che lo dichiari: la copia sparirebbe senza un
		 *    errore da nessuna parte.  Il client non lo manderebbe mai da se',
		 *    ma un giorno qualcuno inoltrera' un elenco di tipi senza guardarlo.
		 */
		if (!g_strcmp0(mime[i], "application/x-kde-onlyReplaceEmpty"))
		{
			avviso("tipo «%s» non dichiarato: KWin annullerebbe l'intera selezione", mime[i]);
			continue;
		}
		zwlr_data_control_source_v1_offer(sorgente, mime[i]);
	}

	g_mutex_lock(&appunti->lucchetto);
	/* ⚠ La vecchia sorgente NON si distrugge qui: il compositore le manda
	 * `cancelled`, ed e' quella richiamata a distruggerla.  Distruggerla adesso
	 * significherebbe farlo due volte. */
	appunti->nostra = sorgente;
	g_strfreev(appunti->nostri_tipi);
	appunti->nostri_tipi = g_strdupv((GStrv) mime);
	g_mutex_unlock(&appunti->lucchetto);

	zwlr_data_control_device_v1_set_selection(appunti->dispositivo, sorgente);
	wl_display_flush(appunti->display);
	diagnostica("annunciata alla sessione la copia del client: %u tipi", g_strv_length((GStrv) mime));
	return TRUE;
}

/*
 * Aspetta che un descrittore sia pronto, con tetto.  TRUE se lo e'.
 *
 * ⛔ `POLLHUP` VALE COME «PRONTO», e trattarlo come un guasto costa una diagnosi
 *    sbagliata.  Quando chi possiede gli appunti scrive e chiude — cioe' nel
 *    caso NORMALE, e in quello dei dati corti sempre — la `poll` puo' tornare
 *    con `POLLHUP` e basta: i dati sono nel tubo, ma nessuno li ha ancora letti.
 *    Chi guarda solo `POLLIN` conclude «non ha risposto» **subito**, e scrive a
 *    registro una scadenza di cinque secondi che non e' mai passata.  E' quel
 *    che questo banco ha visto al primo giro. [M, 8 agosto 2026]
 */
static gboolean pronto(int fd, short cosa)
{
	struct pollfd sonda = { .fd = fd, .events = cosa, .revents = 0 };
	int esito;

	do
	{
		esito = poll(&sonda, 1, ATTESA_TRASFERIMENTO_MS);
	} while (esito < 0 && errno == EINTR);
	if (esito <= 0)
		return FALSE;
	if (sonda.revents & cosa)
		return TRUE;
	/* In lettura la chiusura e' un esito, non un guasto: si torna pronti, e la
	 * `read` che segue dira' zero.  In scrittura invece non c'e' piu' nessuno. */
	return (cosa & POLLIN) && (sonda.revents & POLLHUP);
}

GBytes *appunti_wlr_leggi(AppuntiWlr *appunti, const char *mime, GError **sbaglio)
{
	int tubo[2];
	GByteArray *raccolta;
	struct zwlr_data_control_offer_v1 *proxy = NULL;

	if (!appunti)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED, "appunti non aperti");
		return NULL;
	}

	g_mutex_lock(&appunti->lucchetto);
	if (appunti->corrente)
		proxy = appunti->corrente->proxy;
	g_mutex_unlock(&appunti->lucchetto);

	if (!proxy)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "la sessione non ha niente negli appunti");
		return NULL;
	}
	if (pipe(tubo) != 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "pipe non creata: %s",
		            g_strerror(errno));
		return NULL;
	}

	/*
	 * ⛔ LA PROPRIA COPIA DEL DESCRITTORE DI SCRITTURA SI CHIUDE SUBITO, e se non
	 *    lo si fa la lettura non finisce MAI: la fine del flusso e' l'ultimo
	 *    descrittore di scrittura che si chiude, e uno di quelli e' il nostro.
	 *    Il sintomo sarebbe un incolla che riesce e si pianta all'ultimo byte.
	 */
	zwlr_data_control_offer_v1_receive(proxy, mime, tubo[1]);
	if (wl_display_flush(appunti->display) < 0 && errno != EAGAIN)
		avviso("la richiesta degli appunti non e' partita: %s", g_strerror(errno));
	close(tubo[1]);

	raccolta = g_byte_array_new();
	for (;;)
	{
		guint8 pezzo[4096];
		ssize_t quanti;

		if (!pronto(tubo[0], POLLIN))
		{
			close(tubo[0]);
			g_byte_array_unref(raccolta);
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "chi possiede gli appunti non ha risposto entro %d ms",
			            ATTESA_TRASFERIMENTO_MS);
			return NULL;
		}
		quanti = read(tubo[0], pezzo, sizeof pezzo);
		if (quanti < 0 && errno == EINTR)
			continue;
		if (quanti <= 0)
			break;
		g_byte_array_append(raccolta, pezzo, (guint) quanti);
	}
	close(tubo[0]);

	diagnostica("letti %u byte di «%s» dagli appunti della sessione", raccolta->len, mime);
	return g_byte_array_free_to_bytes(raccolta);
}

void appunti_wlr_rispondi(AppuntiWlr *appunti, guint32 serial, GBytes *dati)
{
	gpointer valore;
	int fd;
	const guint8 *inizio;
	gsize quanti = 0;
	gsize scritti = 0;

	if (!appunti)
		return;

	g_mutex_lock(&appunti->lucchetto);
	if (!g_hash_table_steal_extended(appunti->richieste, GUINT_TO_POINTER(serial), NULL, &valore))
	{
		g_mutex_unlock(&appunti->lucchetto);
		avviso("risposta a una richiesta di appunti che non esiste (serial %u)", serial);
		return;
	}
	g_mutex_unlock(&appunti->lucchetto);
	fd = GPOINTER_TO_INT(valore);

	/*
	 * ⛔ SI CHIUDE SEMPRE, anche senza dati.  Chi sta incollando aspetta la fine
	 *    del flusso, e la fine del flusso e' questa `close`: un descrittore
	 *    dimenticato non da' un errore, da' un'applicazione ferma.
	 */
	inizio = dati ? g_bytes_get_data(dati, &quanti) : NULL;
	while (inizio && scritti < quanti)
	{
		ssize_t fatti;

		if (!pronto(fd, POLLOUT))
		{
			avviso("chi sta incollando non legge: %" G_GSIZE_FORMAT " byte su %" G_GSIZE_FORMAT
			       " consegnati, poi rinuncio",
			       scritti, quanti);
			break;
		}
		fatti = write(fd, inizio + scritti, quanti - scritti);
		if (fatti < 0 && (errno == EINTR || errno == EAGAIN))
			continue;
		if (fatti <= 0)
		{
			/* EPIPE: chi incollava se n'e' andato.  Non e' un guasto nostro. */
			diagnostica("il trasferimento degli appunti si e' chiuso dall'altra parte");
			break;
		}
		scritti += (gsize) fatti;
	}
	close(fd);
	if (inizio)
		diagnostica("consegnati %" G_GSIZE_FORMAT " byte alla sessione", scritti);
}
