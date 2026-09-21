/*
 * wlroots.c — la cattura del verso a tiro.  Il perché sta in `wlroots.h`.
 *
 * ⛔⛔ QUESTA PRIMA STESURA PRENDE I PIXEL DALLA MEMORIA (`wl_shm`), NON DALLA
 *     SCHEDA — ed è una scelta dichiarata, non una dimenticanza.
 *
 *     L'evento `linux_dmabuf` esiste (screencopy v3, e labwc lo dà), e la
 *     strada della scheda è quella che vale: `STUDI.md` §xfce §4.4 dice che qui
 *     la copia zero è possibile **in una forma migliore di quella di Mutter**.
 *     ⚠ Ma si misura una cosa per volta: prima si dimostra che i pixel
 *     arrivano e sono quelli giusti, poi si toglie la copia. Invertire l'ordine
 *     vuol dire, il giorno che lo schermo è nero, non sapere se è il protocollo
 *     o la scheda — e quel giorno costa più di questo.
 *
 * ⇒ I conteggi distinguono le due strade, e il registro dice sempre quale è in
 *   vigore: un numero senza la sua strada è un numero che mentirà.
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

/* ⚠ I fourcc di `wl_shm` e quelli di DRM coincidono per tutti i formati che
 *   contano, tranne i due «speciali» che wl_shm numera 0 e 1.  ⛔ Tradurli a
 *   mano invece di assumere: assumere è come si scopre, mesi dopo, che i canali
 *   erano scambiati. */
#define FOURCC(a, b, c, d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | ((uint32_t)(c) << 16) | \
                            ((uint32_t)(d) << 24))
#define DRM_XRGB8888 FOURCC('X', 'R', '2', '4')
#define DRM_ARGB8888 FOURCC('A', 'R', '2', '4')

struct WlrPalco {
	struct wl_display *display;
	struct wl_registry *registry;
	struct wl_shm *shm;
	struct zwlr_screencopy_manager_v1 *manager;
	struct wl_output *uscita;
	char *uscita_nome;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ LA MISURA DELL'USCITA — `zwlr_output_manager_v1`.
	 *
	 * ⛔ Su questa famiglia la tela NON si negozia col flusso: un flusso non
	 *    c'è.  Si cambia la misura dell'USCITA, e poi i fotogrammi arrivano
	 *    così.  ⇒ È la cosa che su KDE non si poteva fare (KWin 6.3.6 non
	 *    ridimensiona `Virtual-0`) e che qui si può.
	 * ------------------------------------------------------------------ */
	struct zwlr_output_manager_v1 *gestore;
	struct zwlr_output_head_v1 *testa;
	char *testa_nome;
	uint32_t serial;
	bool serial_noto;
	/* l'esito dell'ultima configurazione chiesta */
	bool conf_finita, conf_riuscita;

	/* la geometria che l'uscita dichiara — ⛔ quella che HA, non quella voluta */
	uint32_t larghezza, altezza;

	/* il buffer condiviso, riusato fra un fotogramma e l'altro */
	struct wl_buffer *buffer;
	void *pixel;
	gsize byte;
	int fd;
	uint32_t b_larghezza, b_altezza, b_stride, b_formato;
	/*
	 * ⛔⛔ IL BUFFER SPORCO, e non è zelo: è un difetto trovato rileggendo.
	 *
	 * Se si abbandona un fotogramma DOPO aver mandato `copy` (scadenza, filo
	 * caduto), il compositore può scrivere in quel buffer **più tardi** — la
	 * richiesta è partita e nessuno l'ha ritirata.  ⇒ Riusarlo al giro dopo
	 * vorrebbe dire farsi riscrivere l'immagine sotto gli occhi, e il sintomo
	 * sarebbe **un fotogramma vecchio in mezzo ai nuovi**: non un errore, uno
	 * sfarfallio.  È la stessa forma di `LEZIONI.md` §8 (le due schermate che
	 * si alternavano: non era *acquire*, era *release*).
	 * ⇒ Chi abbandona dopo `copy` marca il buffer, e il giro dopo se ne fa uno
	 *   nuovo.  ⚠ Costa una riallocazione ogni scadenza, e le scadenze sono
	 *   rare: il prezzo giusto per non avere fotogrammi che tornano indietro.
	 */
	bool buffer_sporco;

	/* lo stato del giro in corso */
	struct zwlr_screencopy_frame_v1 *frame;
	bool visto_buffer, visto_buffer_done, pronto, fallito, y_invertita;
	uint32_t f_formato, f_larghezza, f_altezza, f_stride;
	/* ⭐ I formati OFFERTI in questo giro: su v3 il compositore ne propone
	 *    piu' d'uno e chiude con `buffer_done`.  ⛔ Prendere il primo vorrebbe
	 *    dire prendere quello che il caso ha messo davanti. */
	bool offerto_bgrx;
	uint32_t o_bgrx_l, o_bgrx_a, o_bgrx_stride;
	bool detto_il_formato;
	uint64_t f_secondi;
	uint32_t f_nanosecondi;

	WlrConteggi conteggi;
};

/* ------------------------------------------------------------------------- */
/* Il registro dei global. */

static void uscita_geometria(void *dati, struct wl_output *o, int32_t x, int32_t y, int32_t lf,
                             int32_t af, int32_t sub, const char *make, const char *model,
                             int32_t trasf)
{
}

static void uscita_modo(void *dati, struct wl_output *o, uint32_t flag, int32_t l, int32_t a,
                        int32_t refresh)
{
	WlrPalco *p = dati;

	/* ⛔ SOLO il modo CORRENTE: un'uscita può annunciarne molti, e prendere
	 *    l'ultimo che passa vuol dire prendere quello che il caso ha messo in
	 *    fondo. */
	if (flag & WL_OUTPUT_MODE_CURRENT) {
		p->larghezza = (uint32_t)l;
		p->altezza = (uint32_t)a;
	}
}

static void uscita_fine(void *dati, struct wl_output *o)
{
}

static void uscita_scala(void *dati, struct wl_output *o, int32_t scala)
{
}

static void uscita_nome(void *dati, struct wl_output *o, const char *nome)
{
	WlrPalco *p = dati;

	g_free(p->uscita_nome);
	p->uscita_nome = g_strdup(nome);
}

static void uscita_descrizione(void *dati, struct wl_output *o, const char *d)
{
}

static const struct wl_output_listener ASCOLTO_USCITA = {
	.geometry = uscita_geometria,
	.mode = uscita_modo,
	.done = uscita_fine,
	.scale = uscita_scala,
	.name = uscita_nome,
	.description = uscita_descrizione,
};

/* ------------------------------------------------------------------------- */
/*
 * ⛔⛔ IL SERIAL, E PERCHÉ SI TIENE SEMPRE L'ULTIMO.
 *
 * `zwlr_output_manager_v1.done(serial)` fotografa lo stato delle uscite.  Una
 * configurazione creata con un serial **vecchio** viene **annullata** — e
 * `cancelled` non è `failed`: vuol dire «la realtà è cambiata sotto», non «no».
 * ⇒ Si tiene l'ultimo, e si riprova con quello.
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

	p->gestore = NULL;
}

static const struct zwlr_output_manager_v1_listener ASCOLTO_GESTORE = {
	.head = gestore_testa,
	.done = gestore_fine,
	.finished = gestore_finito,
};

static void testa_nome(void *dati, struct zwlr_output_head_v1 *t, const char *nome)
{
	WlrPalco *p = dati;

	/* ⛔ SI TIENE SOLO LA TESTA CHE CORRISPONDE ALL'USCITA CHE STIAMO
	 *    GUARDANDO, per nome.  Prendere «la prima» qui vorrebbe dire
	 *    ridimensionare un'uscita e catturarne un'altra — e il sintomo
	 *    sarebbe «il ridimensionamento non funziona», che è falso. */
	if (p->uscita_nome && g_strcmp0(nome, p->uscita_nome) == 0) {
		p->testa = t;
		g_free(p->testa_nome);
		p->testa_nome = g_strdup(nome);
	}
}

static void testa_descrizione(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_misura_fisica(void *d, struct zwlr_output_head_v1 *t, int32_t l, int32_t a) {}
static void testa_modo(void *d, struct zwlr_output_head_v1 *t, struct zwlr_output_mode_v1 *m) {}
static void testa_accesa(void *d, struct zwlr_output_head_v1 *t, int32_t x) {}
static void testa_modo_corrente(void *d, struct zwlr_output_head_v1 *t,
                                struct zwlr_output_mode_v1 *m) {}
static void testa_posizione(void *d, struct zwlr_output_head_v1 *t, int32_t x, int32_t y) {}
static void testa_trasformazione(void *d, struct zwlr_output_head_v1 *t, int32_t x) {}
static void testa_scala(void *d, struct zwlr_output_head_v1 *t, wl_fixed_t s) {}
static void testa_finita(void *dati, struct zwlr_output_head_v1 *t)
{
	WlrPalco *p = dati;

	if (p->testa == t)
		p->testa = NULL;
}
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

static void gestore_testa(void *dati, struct zwlr_output_manager_v1 *m,
                          struct zwlr_output_head_v1 *testa)
{
	zwlr_output_head_v1_add_listener(testa, &ASCOLTO_TESTA, dati);
}

static void conf_riuscita(void *dati, struct zwlr_output_configuration_v1 *c)
{
	WlrPalco *p = dati;

	p->conf_finita = true;
	p->conf_riuscita = true;
}

static void conf_fallita(void *dati, struct zwlr_output_configuration_v1 *c)
{
	WlrPalco *p = dati;

	p->conf_finita = true;
	p->conf_riuscita = false;
}

static void conf_annullata(void *dati, struct zwlr_output_configuration_v1 *c)
{
	WlrPalco *p = dati;

	/* ⚠ «Annullata» NON è «fallita»: il serial era vecchio, cioè la realtà è
	 *   cambiata mentre chiedevamo.  Chi chiama può riprovare col serial nuovo. */
	p->conf_finita = true;
	p->conf_riuscita = false;
}

static const struct zwlr_output_configuration_v1_listener ASCOLTO_CONF = {
	.succeeded = conf_riuscita,
	.failed = conf_fallita,
	.cancelled = conf_annullata,
};

static void registro_global(void *dati, struct wl_registry *reg, uint32_t nome,
                            const char *interfaccia, uint32_t versione)
{
	WlrPalco *p = dati;

	if (g_strcmp0(interfaccia, wl_shm_interface.name) == 0) {
		p->shm = wl_registry_bind(reg, nome, &wl_shm_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_screencopy_manager_v1_interface.name) == 0) {
		/* ⚠ Si chiede al massimo 3 e non di più: la v3 è quella che porta
		 *   `linux_dmabuf` e `buffer_done`, ed è quella che `[M]` labwc dà.
		 *   Chiedere più di quel che si sa gestire è come dire «ho capito» a
		 *   qualcuno che non si è ascoltato. */
		uint32_t v = versione < 3 ? versione : 3;

		p->manager = wl_registry_bind(reg, nome, &zwlr_screencopy_manager_v1_interface, v);
	} else if (g_strcmp0(interfaccia, zwlr_output_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 4 ? versione : 4;

		p->gestore = wl_registry_bind(reg, nome, &zwlr_output_manager_v1_interface, v);
		zwlr_output_manager_v1_add_listener(p->gestore, &ASCOLTO_GESTORE, p);
	} else if (g_strcmp0(interfaccia, wl_output_interface.name) == 0) {
		/* ⛔ LA PRIMA, e si dichiara.  Una sessione remota ha UN'uscita
		 *    (l'headless che il compositore crea); il giorno che ne avesse due,
		 *    prendere «la prima» diventerebbe una scelta silenziosa — e il
		 *    registro qui sotto la rende almeno visibile. */
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

static void registro_via(void *dati, struct wl_registry *reg, uint32_t nome)
{
}

static const struct wl_registry_listener ASCOLTO_REGISTRO = {
	.global = registro_global,
	.global_remove = registro_via,
};

/* ------------------------------------------------------------------------- */
/* Il giro di un fotogramma. */

static void frame_buffer(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t larghezza, uint32_t altezza, uint32_t stride)
{
	WlrPalco *p = dati;

	/*
	 * ⛔⛔ SI SCEGLIE, NON SI PRENDE IL PRIMO — e la ragione è un difetto
	 *     trovato rileggendo, il 21 settembre 2026, prima che si vedesse.
	 *
	 * `figlio.c` dichiara al codificatore `CODIFICATORE_PIXEL_BGRX`, cioè
	 * **B G R x in memoria**, ed è inchiodato lì dalla fase 2.  ⛔ labwc offre
	 * per primo **XBGR8888**, che in memoria è `R G B x`: darglielo vorrebbe
	 * dire consegnare all'utente un desktop **con il rosso e il blu
	 * scambiati**, senza una riga che lo spieghi — la stessa trappola che il
	 * banco `13-w1` aveva già pagato, arrivata fino in fondo alla catena.
	 *
	 * ⭐ E la cura giusta NON è insegnare un formato nuovo al codificatore, che
	 *   GNOME e KDE usano: è **chiedere quello che si sa già leggere**.  Su v3
	 *   il compositore ne offre più d'uno apposta, e `buffer_done` esiste per
	 *   questo: si raccolgono tutti, poi si sceglie.
	 */
	if (formato == DRM_XRGB8888 || formato == DRM_ARGB8888) {
		p->offerto_bgrx = true;
		p->o_bgrx_l = larghezza;
		p->o_bgrx_a = altezza;
		p->o_bgrx_stride = stride;
	}
	if (!p->visto_buffer) {
		p->visto_buffer = true;
		p->f_formato = formato;
		p->f_larghezza = larghezza;
		p->f_altezza = altezza;
		p->f_stride = stride;
	}
	/* ⚠ L'ELENCO SI SCRIVE, una volta per sessione: il giorno che i canali
	 *   escono scambiati, la prima domanda è «che cosa offriva il
	 *   compositore?» — e senza questa riga non c'è modo di saperlo dopo. */
	if (!p->detto_il_formato) {
		char nome[8];

		memcpy(nome, &formato, 4);
		nome[4] = 0;
		registro_dice(AREA, "wlroots: formato offerto «%s» (%ux%u stride %u)",
		              nome, larghezza, altezza, stride);
	}
}

static void frame_flags(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t flags)
{
	WlrPalco *p = dati;

	p->y_invertita = (flags & ZWLR_SCREENCOPY_FRAME_V1_FLAGS_Y_INVERT) != 0;
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
	WlrPalco *p = dati;

	p->fallito = true;
}

static void frame_danno(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                        uint32_t l, uint32_t a)
{
	/* ⚠ Il danno arriva solo con `copy_with_damage`, che questa stesura non
	 *   usa: il libro del danno è una cura della fase 9 e si porta qui quando
	 *   si porta, non per analogia. */
}

static void frame_dmabuf(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t larghezza, uint32_t altezza)
{
	/* ⭐ La strada della scheda: l'evento c'è, e questa stesura NON lo usa —
	 *    vedi il riquadro in cima al file.  ⛔ Non si tace: si conta, così il
	 *    giorno che la si accende si sa che era offerta da sempre. */
}

static void frame_buffer_done(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	WlrPalco *p = dati;

	p->visto_buffer_done = true;
	/* ⭐ Adesso che l'elenco è chiuso si sceglie: `B G R x` se c'è, perché è
	 *    quel che il codificatore sa leggere senza scambiare i canali. */
	if (p->offerto_bgrx) {
		p->f_formato = DRM_XRGB8888;
		p->f_larghezza = p->o_bgrx_l;
		p->f_altezza = p->o_bgrx_a;
		p->f_stride = p->o_bgrx_stride;
	}
	if (!p->detto_il_formato) {
		p->detto_il_formato = true;
		registro_dice(AREA,
		              "wlroots: formato scelto %s — %s.  ⛔ E si SCEGLIE: il primo "
		              "offerto è quello che il caso mette davanti, e un canale "
		              "scambiato non dà nessun errore, dà un desktop blu",
		              p->offerto_bgrx ? "XRGB8888 (B G R x)" : "il primo offerto",
		              p->offerto_bgrx
		                  ? "è quel che il codificatore legge senza conversioni"
		                  : "⚠ XRGB8888 NON era fra gli offerti: i canali potrebbero "
		                    "uscire scambiati, e questa è la riga che lo dice");
	}
}

static const struct zwlr_screencopy_frame_v1_listener ASCOLTO_FRAME = {
	.buffer = frame_buffer,
	.flags = frame_flags,
	.ready = frame_pronto,
	.failed = frame_fallito,
	.damage = frame_danno,
	.linux_dmabuf = frame_dmabuf,
	.buffer_done = frame_buffer_done,
};

/* ------------------------------------------------------------------------- */

static bool prepara_buffer(WlrPalco *p, GError **sbaglio)
{
	struct wl_shm_pool *pool;
	gsize byte = (gsize)p->f_stride * p->f_altezza;

	if (!p->buffer_sporco && p->buffer && p->b_larghezza == p->f_larghezza &&
	    p->b_altezza == p->f_altezza && p->b_stride == p->f_stride &&
	    p->b_formato == p->f_formato)
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
		            "il compositore ha dichiarato un buffer di 0 byte "
		            "(%ux%u stride %u)",
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
	p->buffer = wl_shm_pool_create_buffer(pool, 0, (int32_t)p->f_larghezza,
	                                      (int32_t)p->f_altezza, (int32_t)p->f_stride,
	                                      p->f_formato);
	wl_shm_pool_destroy(pool);
	p->b_larghezza = p->f_larghezza;
	p->b_altezza = p->f_altezza;
	p->b_stride = p->f_stride;
	p->b_formato = p->f_formato;
	return true;
}

/*
 * Un giro della pompa, con scadenza.
 *
 * ⛔ `wl_display_dispatch()` BLOCCA senza tetto: usarla qui vorrebbe dire che un
 *    compositore muto ferma il figlio per sempre — e il sintomo non sarebbe un
 *    errore, sarebbe «è lento», che è la forma d'errore che questo progetto ha
 *    già pagato tre volte.  ⇒ Si aspetta sul descrittore con un tetto vero.
 */
static bool pompa(WlrPalco *p, gint64 scadenza, GError **sbaglio)
{
	struct pollfd pfd;
	int fd = wl_display_get_fd(p->display);
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
	pfd.fd = fd;
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

/* ------------------------------------------------------------------------- */

WlrPalco *wlr_apri(GError **sbaglio)
{
	WlrPalco *p = g_new0(WlrPalco, 1);
	const char *nome = g_getenv("WAYLAND_DISPLAY");

	p->fd = -1;
	p->display = wl_display_connect(nome);
	if (!p->display && !nome) {
		/* ⚠ La stessa ricerca di `kwin_display_apri()`: il figlio non eredita
		 *   `WAYLAND_DISPLAY` dal compositore che ha appena fatto nascere. */
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
	 *   global mandano appena legati (il `mode` e il `name` dell'uscita). */
	wl_display_roundtrip(p->display);
	wl_display_roundtrip(p->display);

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
	              "quella che l'uscita HA, non quella chiesta: su questa famiglia "
	              "l'uscita nasce cablata e si ridimensiona dopo",
	              p->uscita_nome ?: "senza nome", p->larghezza, p->altezza);
	return p;
}

WlrMisuraEsito wlr_misura_chiedi(WlrPalco *palco, uint32_t larghezza, uint32_t altezza,
                                 double attesa_s, GError **sbaglio)
{
	struct zwlr_output_configuration_v1 *conf;
	struct zwlr_output_configuration_head_v1 *ct;
	gint64 scadenza;

	g_return_val_if_fail(palco != NULL, WLR_MISURA_IMPOSSIBILE);

	if (!palco->gestore || !palco->testa || !palco->serial_noto) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "il compositore non annuncia zwlr_output_manager_v1 (o non ho "
		            "trovato la testa dell'uscita «%s»): la misura non si può cambiare",
		            palco->uscita_nome ?: "senza nome");
		return WLR_MISURA_IMPOSSIBILE;
	}
	if (palco->larghezza == larghezza && palco->altezza == altezza)
		return WLR_MISURA_GIA_COSI;

	palco->conf_finita = false;
	palco->conf_riuscita = false;

	conf = zwlr_output_manager_v1_create_configuration(palco->gestore, palco->serial);
	zwlr_output_configuration_v1_add_listener(conf, &ASCOLTO_CONF, palco);
	ct = zwlr_output_configuration_v1_enable_head(conf, palco->testa);
	/* ⚠ `refresh = 0`: su un'uscita senza schermo la cadenza è una finzione, e
	 *   zero vuol dire «scegli tu».  ⛔ Metterci un numero tondo qui vorrebbe
	 *   dire dichiarare una cadenza che nessuno rispetta. */
	zwlr_output_configuration_head_v1_set_custom_mode(ct, (int32_t)larghezza,
	                                                  (int32_t)altezza, 0);
	zwlr_output_configuration_v1_apply(conf);

	scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);
	while (!palco->conf_finita) {
		if (!pompa(palco, scadenza, sbaglio)) {
			zwlr_output_configuration_v1_destroy(conf);
			return WLR_MISURA_RIFIUTATA;
		}
		if (g_get_monotonic_time() >= scadenza)
			break;
	}
	zwlr_output_configuration_v1_destroy(conf);

	if (!palco->conf_finita) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "in %.1f s il compositore non ha risposto alla richiesta di misura",
		            attesa_s);
		return WLR_MISURA_RIFIUTATA;
	}
	if (!palco->conf_riuscita)
		return WLR_MISURA_ANNULLATA;

	/* ⛔⛔ E QUI NON SI SCRIVE `palco->larghezza = larghezza`.
	 *
	 *     Il compositore ha detto sì alla RICHIESTA; che l'uscita sia davvero
	 *     cambiata lo dirà l'evento `mode` della `wl_output`, che arriva per
	 *     conto suo.  ⇒ Scriverlo qui vorrebbe dire credere all'esito invece
	 *     che al fatto, ed è esattamente l'errore che `DECISIONI.md`
	 *     §5.0-sexies vieta.
	 */
	wl_display_roundtrip(palco->display);
	return WLR_MISURA_CHIESTA;
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

WlrEsito wlr_fotogramma(WlrPalco *palco, double attesa_s, WlrFotogramma *fuori, GError **sbaglio)
{
	gint64 scadenza;

	g_return_val_if_fail(palco != NULL, WLR_FOTOGRAMMA_ROTTO);
	g_return_val_if_fail(fuori != NULL, WLR_FOTOGRAMMA_ROTTO);

	palco->visto_buffer = palco->visto_buffer_done = false;
	palco->pronto = palco->fallito = palco->y_invertita = false;
	palco->conteggi.chiesti++;

	/* ⭐ `overlay_cursor = 1`: su questa famiglia il puntatore sta DENTRO
	 *    l'immagine, e non c'è un canale per la sua forma — `wlroots.h`.  ⛔ È
	 *    una scelta dichiarata, non il predefinito preso per pigrizia. */
	palco->frame = zwlr_screencopy_manager_v1_capture_output(palco->manager, 1, palco->uscita);
	if (!palco->frame) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "capture_output non ha prodotto un fotogramma");
		return WLR_FOTOGRAMMA_ROTTO;
	}
	zwlr_screencopy_frame_v1_add_listener(palco->frame, &ASCOLTO_FRAME, palco);

	scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);

	/* 1 · si aspetta l'ELENCO CHIUSO (`buffer_done`), non il primo `buffer`:
	 *     la scelta del formato si fa sull'elenco intero.  ⚠ Su un compositore
	 *     che desse solo v1/v2 `buffer_done` non arriva mai: lì si accetta il
	 *     primo, e si esce per scadenza con quello già in mano. */
	while (!palco->visto_buffer_done && !palco->fallito) {
		if (palco->visto_buffer &&
		    zwlr_screencopy_frame_v1_get_version(palco->frame) < 3)
			break;
		if (!pompa(palco, scadenza, sbaglio)) {
			zwlr_screencopy_frame_v1_destroy(palco->frame);
			palco->frame = NULL;
			return WLR_FOTOGRAMMA_ROTTO;
		}
		if (g_get_monotonic_time() >= scadenza)
			break;
	}
	if (palco->fallito) {
		zwlr_screencopy_frame_v1_destroy(palco->frame);
		palco->frame = NULL;
		palco->conteggi.falliti++;
		return WLR_FOTOGRAMMA_FALLITO;
	}
	if (!palco->visto_buffer) {
		zwlr_screencopy_frame_v1_destroy(palco->frame);
		palco->frame = NULL;
		palco->conteggi.scaduti++;
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "in %.1f s il compositore non ha detto in che formato vuole il "
		            "buffer",
		            attesa_s);
		return WLR_FOTOGRAMMA_SCADUTO;
	}

	/* 2 · si prepara il buffer e si chiede la copia */
	if (!prepara_buffer(palco, sbaglio)) {
		zwlr_screencopy_frame_v1_destroy(palco->frame);
		palco->frame = NULL;
		return WLR_FOTOGRAMMA_ROTTO;
	}
	zwlr_screencopy_frame_v1_copy(palco->frame, palco->buffer);

	/* 3 · si aspetta `ready` o `failed` */
	while (!palco->pronto && !palco->fallito) {
		if (!pompa(palco, scadenza, sbaglio)) {
			/* ⛔ La copia era partita: il buffer non si riusa. */
			palco->buffer_sporco = true;
			zwlr_screencopy_frame_v1_destroy(palco->frame);
			palco->frame = NULL;
			return WLR_FOTOGRAMMA_ROTTO;
		}
		if (g_get_monotonic_time() >= scadenza)
			break;
	}

	zwlr_screencopy_frame_v1_destroy(palco->frame);
	palco->frame = NULL;

	if (palco->fallito) {
		palco->conteggi.falliti++;
		return WLR_FOTOGRAMMA_FALLITO;
	}
	if (!palco->pronto) {
		/* ⛔ Scaduti DOPO `copy`: vedi il riquadro del buffer sporco. */
		palco->buffer_sporco = true;
		palco->conteggi.scaduti++;
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "in %.1f s il compositore non ha detto «ready»", attesa_s);
		return WLR_FOTOGRAMMA_SCADUTO;
	}

	palco->conteggi.presi++;
	fuori->larghezza = palco->f_larghezza;
	fuori->altezza = palco->f_altezza;
	fuori->stride = palco->f_stride;
	fuori->formato = palco->f_formato;
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
	if (palco->frame)
		zwlr_screencopy_frame_v1_destroy(palco->frame);
	if (palco->buffer)
		wl_buffer_destroy(palco->buffer);
	if (palco->pixel)
		munmap(palco->pixel, palco->byte);
	if (palco->fd >= 0)
		close(palco->fd);
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
