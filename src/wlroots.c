/*
 * wlroots.c — la cattura del verso a tiro.  Il perché sta in `wlroots.h`.
 *
 * ⛔⛔ QUESTA STESURA PRENDE I PIXEL DALLA MEMORIA (`wl_shm`), NON DALLA
 *     SCHEDA — ed è una scelta dichiarata, non una dimenticanza.  Prima si
 *     dimostra che i pixel arrivano e sono quelli giusti, poi si toglie la
 *     copia: invertire l'ordine vuol dire, il giorno che lo schermo è nero, non
 *     sapere se è il protocollo o la scheda.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ RISCRITTA IL 21 SETTEMBRE 2026, dopo il REVISORE AVVERSARIO.
 *
 * La prima stesura aveva sette difetti, e nessuno lo diceva una prova: C1 era
 * verde e 530 fotogrammi passavano.  Li ha trovati una lettura mandata apposta
 * a smentire.  Quelli che hanno cambiato la forma del file, e perché:
 *
 *   1. ⛔ IL FORMATO.  L'evento `buffer` arriva UNA SOLA VOLTA per fotogramma,
 *      e porta la numerazione di `wl_shm` (ARGB8888 = 0, XRGB8888 = 1, il
 *      resto è il fourcc).  La prima stesura credeva di poter SCEGLIERE fra
 *      più formati offerti, e confrontava con i fourcc DRM: il ramo non poteva
 *      mai scattare, e labwc dà solo `XBGR8888` — cioè `R G B x`.  ⇒ Qui si
 *      TRADUCE (wl_shm → DRM) e si consegna; l'ordine lo legge `figlio.c` e lo
 *      dice al codificatore (`CODIFICATORE_PIXEL_RGBX`).
 *   2. ⛔ LA COPIA BUTTATA A OGNI SCADENZA.  Il ciclo del figlio aspetta 8 ms
 *      (`MOVIMENTO_ATTESA_S`) e il giro intero ne costa 9-15: quasi ogni
 *      chiamata scadeva DOPO `copy`, buttava il fotogramma già in corso e
 *      riallocava 8 MB.  ⇒ Adesso il fotogramma è PENDENTE: se l'attesa
 *      finisce, la richiesta resta viva e la chiamata dopo la riprende.
 *   3. ⛔ TRE `wl_display_roundtrip` SENZA TETTO: un compositore bloccato
 *      fermava il figlio per sempre.  ⇒ `giro()`, con scadenza.
 *   4. ⛔ `failed` E `cancelled` NELLO STESSO RAMO — l'errore esatto che
 *      `DECISIONI.md` §5.0-sexies rimprovera a wayvnc.  ⇒ Tre esiti separati.
 *   5. la testa dell'uscita si trovava solo se i nomi arrivavano in un ordine
 *      preciso ⇒ si tengono tutte, e si sceglie al momento della richiesta;
 *   6. la configurazione abilitava una testa sola: con due uscite il protocollo
 *      muore (`unconfigured_head`) ⇒ le altre si riconfermano come sono;
 *   7. le fughe di oggetti in `wlr_chiudi`.
 */
#include "wlroots.h"

#include "registro.h"

#include "wlr-output-management-unstable-v1-client-protocol.h"
#include "wlr-screencopy-unstable-v1-client-protocol.h"

#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <poll.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>

/* ⚠ La stessa area di `cattura.c` e di `kwin.c`: chi legge il registro cerca i
 *   pixel sotto una parola sola, non sotto il nome del modulo che li ha presi. */
#define AREA "cattura"

#define FOURCC(a, b, c, d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | ((uint32_t)(c) << 16) | \
                            ((uint32_t)(d) << 24))
#define DRM_XRGB8888 FOURCC('X', 'R', '2', '4')
#define DRM_ARGB8888 FOURCC('A', 'R', '2', '4')

/* ⛔ I due formati che `wl_shm` numera 0 e 1 invece che col fourcc.  È l'unica
 *    differenza fra le due numerazioni — ed è bastata a rendere cieco un ramo
 *    intero (difetto 1 del riquadro in cima). */
static uint32_t shm_a_drm(uint32_t shm)
{
	if (shm == WL_SHM_FORMAT_ARGB8888)
		return DRM_ARGB8888;
	if (shm == WL_SHM_FORMAT_XRGB8888)
		return DRM_XRGB8888;
	return shm;
}

typedef struct {
	struct zwlr_output_head_v1 *proxy;
	char *nome;
	bool accesa;
} Testa;

typedef enum {
	CONF_IN_CORSO = 0,
	CONF_RIUSCITA,
	CONF_FALLITA,  /* `failed`: il compositore ha detto NO            */
	CONF_ANNULLATA /* `cancelled`: il serial era vecchio, si riprova  */
} ConfEsito;

struct WlrPalco {
	struct wl_display *display;
	struct wl_registry *registry;
	struct wl_shm *shm;
	struct zwlr_screencopy_manager_v1 *manager;
	struct wl_output *uscita;
	char *uscita_nome;

	/* la geometria che l'uscita dichiara — ⛔ quella che HA, non quella voluta */
	uint32_t larghezza, altezza;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ LA MISURA DELL'USCITA — `zwlr_output_manager_v1`.
	 *
	 * ⛔ Su questa famiglia la tela NON si negozia col flusso: un flusso non
	 *    c'è.  Si cambia la misura dell'USCITA, e poi i fotogrammi arrivano
	 *    così.  ⇒ È la cosa che su KDE non si poteva fare.
	 * ------------------------------------------------------------------ */
	struct zwlr_output_manager_v1 *gestore;
	GPtrArray *teste; /* di `Testa *` — TUTTE, non solo la nostra (difetto 5) */
	uint32_t serial;
	bool serial_noto;
	ConfEsito conf;

	/* il buffer condiviso, riusato fra un fotogramma e l'altro */
	struct wl_buffer *buffer;
	void *pixel;
	gsize byte;
	int fd;
	uint32_t b_larghezza, b_altezza, b_stride, b_formato;
	/*
	 * ⛔⛔ IL BUFFER SPORCO.  Se si abbandona un fotogramma DOPO aver mandato
	 *     `copy` e senza aspettarne l'esito (filo caduto), il compositore può
	 *     scriverci dentro più tardi: riusarlo darebbe un fotogramma vecchio in
	 *     mezzo ai nuovi — non un errore, uno sfarfallio (`LEZIONI.md` §8).
	 *  ⚠ Con il fotogramma PENDENTE (difetto 2) la scadenza non lo sporca più:
	 *    la copia resta nostra e si aspetta.  Resta solo per il filo caduto.
	 */
	bool buffer_sporco;

	/* ------------------------------------------------------------------ *
	 * IL FOTOGRAMMA IN CORSO — ⭐ e può sopravvivere a una chiamata.
	 * ------------------------------------------------------------------ */
	struct zwlr_screencopy_frame_v1 *frame;
	bool visto_buffer, pronto, fallito, copia_partita, y_invertita;
	uint32_t f_shm; /* il formato come lo dice wl_shm: serve al buffer */
	uint32_t f_larghezza, f_altezza, f_stride;
	uint64_t f_secondi;
	uint32_t f_nanosecondi;

	bool detto_il_formato;
	WlrConteggi conteggi;
};

/* ------------------------------------------------------------------------- */
/* La pompa, con scadenza. */

/*
 * Un giro della pompa, con scadenza.
 *
 * ⛔ `wl_display_dispatch()` BLOCCA senza tetto: un compositore muto
 *    fermerebbe il figlio per sempre — e il sintomo non sarebbe un errore,
 *    sarebbe «è lento», che è la forma d'errore che questo progetto ha già
 *    pagato tre volte.  ⇒ Si aspetta sul descrittore con un tetto vero.
 */
static bool pompa(WlrPalco *p, gint64 scadenza, GError **sbaglio)
{
	struct pollfd pfd;
	gint64 resta;
	int r;

	while (wl_display_prepare_read(p->display) != 0) {
		if (wl_display_dispatch_pending(p->display) < 0) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
			            "il filo con il compositore è caduto (dispatch_pending)");
			return false;
		}
	}
	if (wl_display_flush(p->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(p->display);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "il filo con il compositore è caduto (flush): %s", g_strerror(errno));
		return false;
	}

	resta = (scadenza - g_get_monotonic_time()) / 1000;
	if (resta < 0)
		resta = 0;
	pfd.fd = wl_display_get_fd(p->display);
	pfd.events = POLLIN;
	r = poll(&pfd, 1, (int)resta);
	if (r <= 0) {
		wl_display_cancel_read(p->display);
		if (r == 0)
			return true; /* scaduto: chi chiama guarda l'orologio */
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "poll: %s",
		            g_strerror(errno));
		return false;
	}
	if (wl_display_read_events(p->display) < 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "il filo con il compositore è caduto (read_events)");
		return false;
	}
	if (wl_display_dispatch_pending(p->display) < 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "il filo con il compositore è caduto (dispatch)");
		return false;
	}
	return true;
}

static void giro_fatto(void *dati, struct wl_callback *cb, uint32_t t)
{
	*(bool *)dati = true;
}

static const struct wl_callback_listener ASCOLTO_GIRO = { .done = giro_fatto };

/*
 * ⭐ Un andata-e-ritorno CON TETTO — il posto di `wl_display_roundtrip()`.
 *
 * ⛔ Difetto 3 del riquadro in cima: `wl_display_roundtrip()` non ha tetto, e
 *    girava tre volte dentro il figlio.  Questo fa la stessa cosa (un `sync` e
 *    si aspetta il suo `done`: tutto quel che il compositore ha mandato prima
 *    è arrivato) e smette alla scadenza.
 */
static bool giro(WlrPalco *p, double attesa_s, GError **sbaglio)
{
	bool fatto = false;
	struct wl_callback *cb = wl_display_sync(p->display);
	gint64 scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);

	wl_callback_add_listener(cb, &ASCOLTO_GIRO, &fatto);
	while (!fatto) {
		if (!pompa(p, scadenza, sbaglio)) {
			wl_callback_destroy(cb);
			return false;
		}
		if (!fatto && g_get_monotonic_time() >= scadenza) {
			wl_callback_destroy(cb);
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "in %.1f s il compositore non ha risposto a un giro di "
			            "andata e ritorno",
			            attesa_s);
			return false;
		}
	}
	wl_callback_destroy(cb);
	return true;
}

/* ------------------------------------------------------------------------- */
/* L'uscita (wl_output). */

static void uscita_geometria(void *dati, struct wl_output *o, int32_t x, int32_t y, int32_t lf,
                             int32_t af, int32_t sub, const char *make, const char *model,
                             int32_t trasf)
{
}

static void uscita_modo(void *dati, struct wl_output *o, uint32_t flag, int32_t l, int32_t a,
                        int32_t refresh)
{
	WlrPalco *p = dati;

	/* ⛔ SOLO il modo CORRENTE: un'uscita può annunciarne molti. */
	if (flag & WL_OUTPUT_MODE_CURRENT) {
		p->larghezza = (uint32_t)l;
		p->altezza = (uint32_t)a;
	}
}

static void uscita_fine(void *dati, struct wl_output *o) {}
static void uscita_scala(void *dati, struct wl_output *o, int32_t scala) {}

static void uscita_nome(void *dati, struct wl_output *o, const char *nome)
{
	WlrPalco *p = dati;

	g_free(p->uscita_nome);
	p->uscita_nome = g_strdup(nome);
}

static void uscita_descrizione(void *dati, struct wl_output *o, const char *d) {}

static const struct wl_output_listener ASCOLTO_USCITA = {
	.geometry = uscita_geometria,
	.mode = uscita_modo,
	.done = uscita_fine,
	.scale = uscita_scala,
	.name = uscita_nome,
	.description = uscita_descrizione,
};

/* ------------------------------------------------------------------------- */
/* Il gestore delle uscite e le sue teste. */

/*
 * ⛔⛔ IL SERIAL, E PERCHÉ SI TIENE SEMPRE L'ULTIMO.  Una configurazione creata
 *     con un serial vecchio viene ANNULLATA — e `cancelled` non è `failed`:
 *     vuol dire «la realtà è cambiata sotto», non «no».
 */
static void gestore_testa(void *dati, struct zwlr_output_manager_v1 *m,
                          struct zwlr_output_head_v1 *testa);

static void gestore_fine(void *dati, struct zwlr_output_manager_v1 *m, uint32_t serial)
{
	WlrPalco *p = dati;

	p->serial = serial;
	p->serial_noto = true;
}

static void gestore_finito(void *dati, struct zwlr_output_manager_v1 *m)
{
	WlrPalco *p = dati;

	zwlr_output_manager_v1_destroy(m);
	p->gestore = NULL;
}

static const struct zwlr_output_manager_v1_listener ASCOLTO_GESTORE = {
	.head = gestore_testa,
	.done = gestore_fine,
	.finished = gestore_finito,
};

static Testa *testa_di(WlrPalco *p, struct zwlr_output_head_v1 *proxy)
{
	for (guint i = 0; p->teste && i < p->teste->len; i++) {
		Testa *t = g_ptr_array_index(p->teste, i);

		if (t->proxy == proxy)
			return t;
	}
	return NULL;
}

static void testa_nome(void *dati, struct zwlr_output_head_v1 *proxy, const char *nome)
{
	Testa *t = testa_di(dati, proxy);

	/* ⭐ Difetto 5: il nome si TIENE, e la testa giusta si sceglie quando
	 *    serve.  Prima si confrontava qui con il nome della `wl_output`, e se
	 *    quello non era ancora arrivato la testa non si trovava più. */
	if (t) {
		g_free(t->nome);
		t->nome = g_strdup(nome);
	}
}

static void testa_accesa(void *dati, struct zwlr_output_head_v1 *proxy, int32_t accesa)
{
	Testa *t = testa_di(dati, proxy);

	if (t)
		t->accesa = accesa != 0;
}

static void testa_finita(void *dati, struct zwlr_output_head_v1 *proxy)
{
	WlrPalco *p = dati;
	Testa *t = testa_di(p, proxy);

	if (t)
		g_ptr_array_remove(p->teste, t); /* la libera `libera_testa` */
}

static void testa_descrizione(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_misura_fisica(void *d, struct zwlr_output_head_v1 *t, int32_t l, int32_t a) {}
static void testa_modo(void *d, struct zwlr_output_head_v1 *t, struct zwlr_output_mode_v1 *m) {}
static void testa_modo_corrente(void *d, struct zwlr_output_head_v1 *t,
                                struct zwlr_output_mode_v1 *m) {}
static void testa_posizione(void *d, struct zwlr_output_head_v1 *t, int32_t x, int32_t y) {}
static void testa_trasformazione(void *d, struct zwlr_output_head_v1 *t, int32_t x) {}
static void testa_scala(void *d, struct zwlr_output_head_v1 *t, wl_fixed_t s) {}
static void testa_marca(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_modello(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_matricola(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_sincronia(void *d, struct zwlr_output_head_v1 *t, uint32_t x) {}

static const struct zwlr_output_head_v1_listener ASCOLTO_TESTA = {
	.name = testa_nome,
	.description = testa_descrizione,
	.physical_size = testa_misura_fisica,
	.mode = testa_modo,
	.enabled = testa_accesa,
	.current_mode = testa_modo_corrente,
	.position = testa_posizione,
	.transform = testa_trasformazione,
	.scale = testa_scala,
	.finished = testa_finita,
	.make = testa_marca,
	.model = testa_modello,
	.serial_number = testa_matricola,
	.adaptive_sync = testa_sincronia,
};

static void libera_testa(gpointer dati)
{
	Testa *t = dati;

	if (t->proxy)
		zwlr_output_head_v1_destroy(t->proxy);
	g_free(t->nome);
	g_free(t);
}

static void gestore_testa(void *dati, struct zwlr_output_manager_v1 *m,
                          struct zwlr_output_head_v1 *proxy)
{
	WlrPalco *p = dati;
	Testa *t = g_new0(Testa, 1);

	t->proxy = proxy;
	g_ptr_array_add(p->teste, t);
	zwlr_output_head_v1_add_listener(proxy, &ASCOLTO_TESTA, p);
}

static void conf_riuscita(void *dati, struct zwlr_output_configuration_v1 *c)
{
	((WlrPalco *)dati)->conf = CONF_RIUSCITA;
}

static void conf_fallita(void *dati, struct zwlr_output_configuration_v1 *c)
{
	((WlrPalco *)dati)->conf = CONF_FALLITA;
}

static void conf_annullata(void *dati, struct zwlr_output_configuration_v1 *c)
{
	((WlrPalco *)dati)->conf = CONF_ANNULLATA;
}

static const struct zwlr_output_configuration_v1_listener ASCOLTO_CONF = {
	.succeeded = conf_riuscita,
	.failed = conf_fallita,
	.cancelled = conf_annullata,
};

/* ------------------------------------------------------------------------- */
/* Il registro dei global. */

static void registro_global(void *dati, struct wl_registry *reg, uint32_t nome,
                            const char *interfaccia, uint32_t versione)
{
	WlrPalco *p = dati;

	if (g_strcmp0(interfaccia, wl_shm_interface.name) == 0) {
		p->shm = wl_registry_bind(reg, nome, &wl_shm_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_screencopy_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 3 ? versione : 3;

		p->manager = wl_registry_bind(reg, nome, &zwlr_screencopy_manager_v1_interface, v);
	} else if (g_strcmp0(interfaccia, zwlr_output_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 4 ? versione : 4;

		p->gestore = wl_registry_bind(reg, nome, &zwlr_output_manager_v1_interface, v);
		zwlr_output_manager_v1_add_listener(p->gestore, &ASCOLTO_GESTORE, p);
	} else if (g_strcmp0(interfaccia, wl_output_interface.name) == 0) {
		if (!p->uscita) {
			uint32_t v = versione < 4 ? versione : 4;

			p->uscita = wl_registry_bind(reg, nome, &wl_output_interface, v);
			wl_output_add_listener(p->uscita, &ASCOLTO_USCITA, p);
		} else {
			registro_dice(AREA,
			              "⚠ wlroots: il compositore annuncia più di un'uscita — "
			              "guardo la prima, e questa riga esiste perché quel "
			              "giorno non sia una scelta muta");
		}
	}
}

static void registro_via(void *dati, struct wl_registry *reg, uint32_t nome) {}

static const struct wl_registry_listener ASCOLTO_REGISTRO = {
	.global = registro_global,
	.global_remove = registro_via,
};

/* ------------------------------------------------------------------------- */
/* Il fotogramma. */

static void frame_buffer(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t larghezza, uint32_t altezza, uint32_t stride)
{
	WlrPalco *p = dati;

	/* ⛔ UNA volta per fotogramma (difetto 1): non c'è niente da scegliere.
	 *    Il formato è nella numerazione di wl_shm, e si tiene COSÌ per creare
	 *    il buffer; la traduzione in DRM si fa solo per chi sta a valle. */
	p->visto_buffer = true;
	p->f_shm = formato;
	p->f_larghezza = larghezza;
	p->f_altezza = altezza;
	p->f_stride = stride;

	if (!p->detto_il_formato) {
		uint32_t drm = shm_a_drm(formato);
		char nome[5];

		p->detto_il_formato = true;
		memcpy(nome, &drm, 4);
		nome[4] = 0;
		registro_dice(AREA,
		              "wlroots: il compositore dà i pixel in «%s» (%ux%u stride %u) — %s",
		              nome, larghezza, altezza, stride,
		              (drm == FOURCC('X', 'B', '2', '4') || drm == FOURCC('A', 'B', '2', '4'))
		                  ? "cioè R G B x in memoria: l'ordine lo dice al codificatore "
		                    "chi consuma il fotogramma"
		                  : "cioè B G R x in memoria, l'ordine che il codificatore "
		                    "leggeva già");
	}
}

static void frame_flags(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t flags)
{
	((WlrPalco *)dati)->y_invertita = (flags & ZWLR_SCREENCOPY_FRAME_V1_FLAGS_Y_INVERT) != 0;
}

static void frame_pronto(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t sec_alto,
                         uint32_t sec_basso, uint32_t nsec)
{
	WlrPalco *p = dati;

	p->f_secondi = ((uint64_t)sec_alto << 32) | sec_basso;
	p->f_nanosecondi = nsec;
	p->pronto = true;
}

static void frame_fallito(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	((WlrPalco *)dati)->fallito = true;
}

static void frame_danno(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                        uint32_t l, uint32_t a)
{
	/* ⚠ Arriva solo con `copy_with_damage`, che questa stesura non usa. */
}

static void frame_dmabuf(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t larghezza, uint32_t altezza)
{
	/* ⭐ La strada della scheda: offerta, e questa stesura non la usa.
	 *    ⚠ E qui il formato è un fourcc DRM VERO — un'altra numerazione da
	 *      quella di `buffer`, e mescolarle è il difetto 1. */
}

static void frame_buffer_done(void *dati, struct zwlr_screencopy_frame_v1 *f) {}

static const struct zwlr_screencopy_frame_v1_listener ASCOLTO_FRAME = {
	.buffer = frame_buffer,
	.flags = frame_flags,
	.ready = frame_pronto,
	.failed = frame_fallito,
	.damage = frame_danno,
	.linux_dmabuf = frame_dmabuf,
	.buffer_done = frame_buffer_done,
};

static bool prepara_buffer(WlrPalco *p, GError **sbaglio)
{
	struct wl_shm_pool *pool;
	gsize byte = (gsize)p->f_stride * p->f_altezza;

	if (!p->buffer_sporco && p->buffer && p->b_larghezza == p->f_larghezza &&
	    p->b_altezza == p->f_altezza && p->b_stride == p->f_stride &&
	    p->b_formato == p->f_shm)
		return true; /* quello di prima va bene */
	p->buffer_sporco = false;

	if (p->buffer) {
		wl_buffer_destroy(p->buffer);
		p->buffer = NULL;
	}
	if (p->pixel) {
		munmap(p->pixel, p->byte);
		p->pixel = NULL;
	}
	if (p->fd >= 0) {
		close(p->fd);
		p->fd = -1;
	}
	if (!byte) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_DATA,
		            "il compositore ha dichiarato un buffer di 0 byte (%ux%u stride %u)",
		            p->f_larghezza, p->f_altezza, p->f_stride);
		return false;
	}

	p->fd = memfd_create("remotix-wlr", MFD_CLOEXEC);
	if (p->fd < 0) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
		            "memfd_create: %s", g_strerror(errno));
		return false;
	}
	if (ftruncate(p->fd, (off_t)byte) != 0) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "ftruncate(%zu): %s",
		            (size_t)byte, g_strerror(errno));
		return false;
	}
	p->pixel = mmap(NULL, byte, PROT_READ | PROT_WRITE, MAP_SHARED, p->fd, 0);
	if (p->pixel == MAP_FAILED) {
		p->pixel = NULL;
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "mmap: %s",
		            g_strerror(errno));
		return false;
	}
	p->byte = byte;

	pool = wl_shm_create_pool(p->shm, p->fd, (int32_t)byte);
	/* ⛔ Il formato di wl_shm, NON quello tradotto: il buffer lo legge il
	 *    compositore, che parla la numerazione di wl_shm. */
	p->buffer = wl_shm_pool_create_buffer(pool, 0, (int32_t)p->f_larghezza,
	                                      (int32_t)p->f_altezza, (int32_t)p->f_stride,
	                                      p->f_shm);
	wl_shm_pool_destroy(pool);
	p->b_larghezza = p->f_larghezza;
	p->b_altezza = p->f_altezza;
	p->b_stride = p->f_stride;
	p->b_formato = p->f_shm;
	return true;
}

/* Chiude il fotogramma in corso.  `copia_viva` = la copia era partita e NON è
 * arrivato né `ready` né `failed`: il buffer non si riusa. */
static void chiudi_frame(WlrPalco *p, bool copia_viva)
{
	if (p->frame)
		zwlr_screencopy_frame_v1_destroy(p->frame);
	p->frame = NULL;
	if (copia_viva)
		p->buffer_sporco = true;
	p->copia_partita = false;
}

/* ------------------------------------------------------------------------- */

WlrPalco *wlr_apri(GError **sbaglio)
{
	WlrPalco *p = g_new0(WlrPalco, 1);
	const char *nome = g_getenv("WAYLAND_DISPLAY");

	p->fd = -1;
	p->teste = g_ptr_array_new_with_free_func(libera_testa);
	p->display = wl_display_connect(nome);
	if (!p->display && !nome) {
		for (int i = 0; i < 10 && !p->display; i++) {
			g_autofree char *tenta = g_strdup_printf("wayland-%d", i);

			p->display = wl_display_connect(tenta);
			if (p->display)
				registro_dice(AREA,
				              "wlroots: WAYLAND_DISPLAY non c'era, trovato «%s» "
				              "in XDG_RUNTIME_DIR", tenta);
		}
	}
	if (!p->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun compositore Wayland raggiungibile in XDG_RUNTIME_DIR=%s",
		            g_getenv("XDG_RUNTIME_DIR") ?: "(non impostata)");
		wlr_chiudi(p);
		return NULL;
	}

	p->registry = wl_display_get_registry(p->display);
	wl_registry_add_listener(p->registry, &ASCOLTO_REGISTRO, p);
	/* ⚠ DUE giri, non uno: il primo porta i global, il secondo gli eventi che i
	 *   global mandano appena legati.  ⛔ E con tetto (difetto 3). */
	if (!giro(p, 2.0, sbaglio) || !giro(p, 2.0, sbaglio)) {
		wlr_chiudi(p);
		return NULL;
	}

	if (!p->manager) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "il compositore non annuncia zwlr_screencopy_manager_v1: su questo "
		            "desktop la cattura non passa di qui");
		wlr_chiudi(p);
		return NULL;
	}
	if (!p->shm) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "il compositore non annuncia wl_shm: non ho dove farmi scrivere i "
		            "pixel");
		wlr_chiudi(p);
		return NULL;
	}
	if (!p->uscita) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "il compositore non annuncia nessuna wl_output: non c'è niente da "
		            "catturare (la sessione è viva ma senza schermo?)");
		wlr_chiudi(p);
		return NULL;
	}

	registro_dice(AREA,
	              "⭐ wlroots: cattura pronta sull'uscita «%s», %ux%u — ⚠ e la misura è "
	              "quella che l'uscita HA, non quella chiesta",
	              p->uscita_nome ?: "senza nome", p->larghezza, p->altezza);
	return p;
}

void wlr_misura(const WlrPalco *palco, uint32_t *larghezza, uint32_t *altezza)
{
	if (larghezza)
		*larghezza = palco ? palco->larghezza : 0;
	if (altezza)
		*altezza = palco ? palco->altezza : 0;
}

const char *wlr_uscita_nome(const WlrPalco *palco)
{
	return palco && palco->uscita_nome ? palco->uscita_nome : "";
}

void wlr_conteggi(const WlrPalco *palco, WlrConteggi *fuori)
{
	if (fuori)
		*fuori = palco ? palco->conteggi : (WlrConteggi){ 0 };
}

WlrMisuraEsito wlr_misura_chiedi(WlrPalco *palco, uint32_t larghezza, uint32_t altezza,
                                 double attesa_s, GError **sbaglio)
{
	struct zwlr_output_configuration_v1 *conf;
	struct zwlr_output_configuration_head_v1 *ct;
	Testa *nostra = NULL;
	gint64 scadenza;

	g_return_val_if_fail(palco != NULL, WLR_MISURA_IMPOSSIBILE);

	for (guint i = 0; palco->teste && i < palco->teste->len; i++) {
		Testa *t = g_ptr_array_index(palco->teste, i);

		if (palco->uscita_nome && g_strcmp0(t->nome, palco->uscita_nome) == 0)
			nostra = t;
	}
	if (!palco->gestore || !nostra || !palco->serial_noto) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED, "%s",
		            !palco->gestore ? "il compositore non annuncia "
		                              "zwlr_output_manager_v1: la misura non si può "
		                              "cambiare"
		            : !nostra ? "nessuna testa del gestore delle uscite ha il nome "
		                        "dell'uscita che si cattura"
		                      : "il gestore delle uscite non ha ancora mandato il suo "
		                        "serial");
		return WLR_MISURA_IMPOSSIBILE;
	}
	if (palco->larghezza == larghezza && palco->altezza == altezza)
		return WLR_MISURA_GIA_COSI;

	palco->conf = CONF_IN_CORSO;
	conf = zwlr_output_manager_v1_create_configuration(palco->gestore, palco->serial);
	zwlr_output_configuration_v1_add_listener(conf, &ASCOLTO_CONF, palco);

	/*
	 * ⛔ Difetto 6: OGNI testa va configurata, o il compositore chiude il filo
	 *    con `unconfigured_head`.  ⇒ La nostra prende la misura nuova; le
	 *    altre si riconfermano esattamente come sono — accese restano accese,
	 *    spente restano spente.  ⚠ Mai spegnerne una per semplificare: su una
	 *    macchina vera sarebbe lo schermo di qualcuno.
	 */
	for (guint i = 0; i < palco->teste->len; i++) {
		Testa *t = g_ptr_array_index(palco->teste, i);

		if (t == nostra) {
			ct = zwlr_output_configuration_v1_enable_head(conf, t->proxy);
			/* ⚠ `refresh = 0`: su un'uscita senza schermo la cadenza è una
			 *   finzione, e zero vuol dire «scegli tu». */
			zwlr_output_configuration_head_v1_set_custom_mode(ct, (int32_t)larghezza,
			                                                  (int32_t)altezza, 0);
		} else if (t->accesa) {
			zwlr_output_configuration_v1_enable_head(conf, t->proxy);
		} else {
			zwlr_output_configuration_v1_disable_head(conf, t->proxy);
		}
	}
	zwlr_output_configuration_v1_apply(conf);

	scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);
	while (palco->conf == CONF_IN_CORSO) {
		if (!pompa(palco, scadenza, sbaglio)) {
			zwlr_output_configuration_v1_destroy(conf);
			return WLR_MISURA_RIFIUTATA;
		}
		if (palco->conf == CONF_IN_CORSO && g_get_monotonic_time() >= scadenza) {
			zwlr_output_configuration_v1_destroy(conf);
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "in %.1f s il compositore non ha risposto alla richiesta di "
			            "misura — e NON è un «no»: non so",
			            attesa_s);
			return WLR_MISURA_RIFIUTATA;
		}
	}
	zwlr_output_configuration_v1_destroy(conf);

	/* ⛔ Difetto 4: tre esiti, tre rami. */
	if (palco->conf == CONF_FALLITA)
		return WLR_MISURA_RIFIUTATA;
	if (palco->conf == CONF_ANNULLATA)
		return WLR_MISURA_ANNULLATA;

	/*
	 * ⛔⛔ E QUI NON SI SCRIVE `palco->larghezza = larghezza`: il compositore ha
	 *     detto sì alla RICHIESTA, e che l'uscita sia cambiata lo dirà l'evento
	 *     `mode` della `wl_output` (`DECISIONI.md` §5.0-sexies).  Un giro, con
	 *     tetto, per lasciarlo arrivare.
	 */
	(void)giro(palco, attesa_s, NULL);
	return WLR_MISURA_CHIESTA;
}

WlrEsito wlr_fotogramma(WlrPalco *palco, double attesa_s, WlrFotogramma *fuori, GError **sbaglio)
{
	gint64 scadenza;

	g_return_val_if_fail(palco != NULL, WLR_FOTOGRAMMA_ROTTO);
	g_return_val_if_fail(fuori != NULL, WLR_FOTOGRAMMA_ROTTO);

	scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);

	/*
	 * ⭐⭐ IL FOTOGRAMMA PENDENTE — difetto 2 del riquadro in cima.
	 *
	 * Se la chiamata di prima è scaduta, la sua richiesta è ANCORA VIVA: il
	 * compositore la sta servendo.  ⇒ Non se ne apre un'altra — si riprende
	 * quella.  Buttarla voleva dire gettare un fotogramma quasi pronto e
	 * riallocare 8 MB, a ogni scadenza, cioè quasi sempre.
	 */
	if (!palco->frame) {
		palco->visto_buffer = palco->pronto = palco->fallito = false;
		palco->copia_partita = palco->y_invertita = false;
		palco->conteggi.chiesti++;
		/* ⭐ `overlay_cursor = 1`: su questa famiglia il puntatore sta DENTRO
		 *    l'immagine, e non c'è un canale per la sua forma. */
		palco->frame = zwlr_screencopy_manager_v1_capture_output(palco->manager, 1,
		                                                         palco->uscita);
		if (!palco->frame) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
			            "capture_output non ha prodotto un fotogramma");
			return WLR_FOTOGRAMMA_ROTTO;
		}
		zwlr_screencopy_frame_v1_add_listener(palco->frame, &ASCOLTO_FRAME, palco);
	}

	for (;;) {
		if (palco->fallito) {
			chiudi_frame(palco, false);
			palco->conteggi.falliti++;
			return WLR_FOTOGRAMMA_FALLITO;
		}
		if (palco->pronto)
			break;
		/* il buffer è noto e la copia non è ancora partita: si parte */
		if (palco->visto_buffer && !palco->copia_partita) {
			if (!prepara_buffer(palco, sbaglio)) {
				chiudi_frame(palco, false);
				return WLR_FOTOGRAMMA_ROTTO;
			}
			zwlr_screencopy_frame_v1_copy(palco->frame, palco->buffer);
			palco->copia_partita = true;
		}
		if (g_get_monotonic_time() >= scadenza) {
			/* ⭐ Scaduto, ma il fotogramma RESTA pendente: la chiamata dopo lo
			 *    riprende.  Non è un guasto e non è un fallimento. */
			palco->conteggi.scaduti++;
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "il fotogramma non è ancora pronto dopo %.3f s — resta in corso",
			            attesa_s);
			return WLR_FOTOGRAMMA_SCADUTO;
		}
		if (!pompa(palco, scadenza, sbaglio)) {
			/* ⛔ Il filo è caduto: se la copia era partita, il buffer non si
			 *    riusa. */
			chiudi_frame(palco, palco->copia_partita);
			return WLR_FOTOGRAMMA_ROTTO;
		}
	}

	chiudi_frame(palco, false);
	palco->conteggi.presi++;
	fuori->larghezza = palco->f_larghezza;
	fuori->altezza = palco->f_altezza;
	fuori->stride = palco->f_stride;
	/* ⭐ Tradotto in DRM per chi sta a valle (difetto 1). */
	fuori->formato = shm_a_drm(palco->f_shm);
	fuori->pixel = palco->pixel;
	fuori->byte = palco->byte;
	fuori->secondi = palco->f_secondi;
	fuori->nanosecondi = palco->f_nanosecondi;
	fuori->y_invertita = palco->y_invertita;
	return WLR_FOTOGRAMMA_PRESO;
}

void wlr_chiudi(WlrPalco *palco)
{
	if (!palco)
		return;
	/* ⛔ Difetto 7: tutto quel che si è creato si distrugge. */
	if (palco->frame)
		zwlr_screencopy_frame_v1_destroy(palco->frame);
	if (palco->buffer)
		wl_buffer_destroy(palco->buffer);
	if (palco->pixel)
		munmap(palco->pixel, palco->byte);
	if (palco->fd >= 0)
		close(palco->fd);
	if (palco->teste)
		g_ptr_array_free(palco->teste, TRUE);
	if (palco->gestore)
		zwlr_output_manager_v1_destroy(palco->gestore);
	if (palco->manager)
		zwlr_screencopy_manager_v1_destroy(palco->manager);
	if (palco->uscita)
		wl_output_destroy(palco->uscita);
	if (palco->shm)
		wl_shm_destroy(palco->shm);
	if (palco->registry)
		wl_registry_destroy(palco->registry);
	if (palco->display)
		wl_display_disconnect(palco->display);
	g_free(palco->uscita_nome);
	g_free(palco);
}
