/*
 * wlroots.c — la cattura del verso a tiro.  Il perché sta in `wlroots.h`.
 *
 * ⛔⛔ LA PRIMA STESURA PRENDEVA I PIXEL DALLA MEMORIA (`wl_shm`), NON DALLA
 *     SCHEDA — ed era una scelta dichiarata: prima si dimostra che i pixel
 *     arrivano e sono quelli giusti, poi si toglie la copia.  ⭐ Dal 21
 *     settembre 2026 la scheda c'è (il secondo riquadro qui sotto), e la
 *     memoria resta come strada di difetto e come RIPIEGO SEMPRE DICHIARATO.
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
 *
 * ===========================================================================
 * ⭐⭐ LA STRADA DELLA SCHEDA — 21 settembre 2026, dietro `CATTURA_STRADA_SCHEDA`
 * ===========================================================================
 *
 * ⚠ Scritta prima sulla stesura vecchia (commit `d5d7129`) e PORTATA a mano
 *   su questa: nessuno dei sette difetti qui sopra torna dentro con lei.  La
 *   scheda parla la SUA numerazione (difetto 1), vive dentro il fotogramma
 *   pendente (difetto 2) e non aspetta mai senza tetto (difetto 3).
 *
 * ⛔ La memoria resta: è il RIPIEGO, e un ripiego DICHIARATO.  Se si chiede la
 *    scheda e arriva la memoria, il registro lo dice con il perché, e ogni
 *    fotogramma porta `sulla_scheda` — non si deduce mai dalla strada chiesta.
 *
 * ---------------------------------------------------------------------------
 * LE DUE STRADE CHE C'ERANO, E PERCHÉ SI PRENDE LA PRIMA
 *
 *   `[M]` labwc annuncia sia `zwlr_screencopy_manager_v1` v3 (con l'evento
 *   `linux_dmabuf`) sia `zwlr_export_dmabuf_manager_v1` v1.
 *
 *   A · `copy` in un DMA-BUF NOSTRO
 *     chi possiede il buffer   ⭐ NOI: lo allochiamo, lo teniamo finché il
 *                              codificatore non ha finito, lo nominiamo in un
 *                              `copy` solo quando è libero
 *     che cosa costa           un blit sulla GPU (`wlr_screencopy_v1.c`
 *                              0.18.2, `frame_dma_copy`): una copia, ma sulla
 *                              scheda — niente `glReadPixels`, che BLOCCA il
 *                              ciclo del compositore (`STUDI.md` §xfce §4.4)
 *     dipendenze nuove         ⚠ `gbm` per allocare, e l'XML di `linux-dmabuf`
 *
 *   B · `zwlr_export_dmabuf_manager_v1`
 *     chi possiede il buffer   ⛔ IL COMPOSITORE: i buffer della sua catena,
 *                              riusati a ogni giro, e `TRANSIENT` SEMPRE
 *                              (`wlr_export_dmabuf_v1.c:75`): la trappola di
 *                              GNOME R29 in forma pura, senza nessuna leva
 *
 *   ⇒ ⭐ A.  Il costo di una dipendenza (`gbm`, che dove gira labwc c'è già a
 *     tempo di esecuzione) compra un buffer che è NOSTRO.
 *
 * ---------------------------------------------------------------------------
 * LE LASTRE — il buffer della scheda, e le tre regole
 *
 *   Una «lastra» è un buffer `gbm` sul nodo `renderD*` del compositore, il suo
 *   `fd` DMA-BUF, e il `wl_buffer` che lo nomina.  Tre stati: LIBERA, IN VOLO
 *   (nominata nel `copy` del fotogramma in corso), IN MANO (consegnata a
 *   valle, finché non torna con `wlr_rendi()`).
 *
 *   1. ⛔ SOLO UNA LASTRA LIBERA SI NOMINA IN UN `copy`.  Una lastra in mano
 *      torna libera solo con `wlr_rendi()` — nel prodotto da
 *      `cattura_fermo_libera()`, che il ciclo chiama DOPO
 *      `codificatore_comprimi_scheda()`, dove `vaSyncSurface` dice che la GPU
 *      ha FINITO di leggere.  ⇒ «labwc ci ricopia dentro mentre il
 *      codificatore la legge» non è evitato con un tempo: è impossibile per
 *      costruzione.  Se sono tutte in mano il fotogramma si ferma DICENDOLO;
 *      non se ne ricicla una (`LEZIONI.md` §8).
 *   2. ⛔ UNA LASTRA ABBANDONATA DOPO `copy` SENZA CONSEGNA (filo caduto,
 *      `failed`) È SPORCA: si butta e se ne fa un'altra.
 *   3. ⛔ OGNI LASTRA CHE NASCE O MUORE CAMBIA LA GENERAZIONE.  Il
 *      codificatore mette in cache l'importazione per `fd`, e i numeri di
 *      descrittore si riciclano: una lastra nuova col numero di una morta
 *      darebbe a VA-API la superficie vecchia — un'immagine di prima, senza
 *      errore.
 *
 *   ⚠ Tre e non una: il ciclo ne tiene una in mano e una in volo; la terza è
 *     assicurazione a buon mercato (8 MB a 1080p).
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ LA LASTRA E IL FOTOGRAMMA PENDENTE — le domande del revisore
 *
 *   · «Scade l'attesa mentre la copia sulla lastra è in volo, e il giro dopo
 *     ne riprende un altro?»  ⇒ No: il giro dopo riprende LO STESSO
 *     fotogramma (`palco->frame` è vivo) con LA STESSA lastra
 *     (`lastra_del_giro` si conserva).  Un `capture_output` nuovo parte solo
 *     quando `frame` è NULL, e `frame` torna NULL solo quando la sua lastra è
 *     consegnata o buttata.  ⛔ E sulla scadenza la lastra NON si sporca: la
 *     stesura vecchia la buttava, ed era il difetto 2 in forma di scheda.
 *   · «Una lastra resa due volte?»  ⇒ `wlr_rendi()` agisce solo su una lastra
 *     IN MANO e la porta a LIBERA: una seconda chiamata la trova LIBERA (o IN
 *     VOLO, se nel frattempo è ripartita) e non fa niente; e
 *     `cattura_fermo_libera()` azzera il fermo dopo averla resa.  ⚠ `[R]` Il
 *     solo caso scoperto è una COPIA del fermo tenuta da qualcuno dopo il
 *     rilascio: in `figlio.c` il fermo è una variabile locale passata per
 *     indirizzo, e nessuno lo copia.
 *   · «Il codificatore legge una lastra mentre labwc ci ricopia dentro?»  ⇒
 *     Regola 1: una lastra in mano non è mai nominata in un `copy`.
 *   · E la fence che non scatta in tempo dopo `ready`: il fotogramma resta
 *     PENDENTE con `pronto` già vero, la lastra resta IN VOLO, e la chiamata
 *     dopo riaspetta la stessa fence — nessuna consegna di un blit a metà,
 *     nessuna lastra persa.
 *
 * ---------------------------------------------------------------------------
 * IL MODIFICATORE: LINEARE, e si dichiara
 *
 *   ⛔ L'evento `linux_dmabuf` porta formato e misura, NON i modificatori.
 *      ⇒ LINEARE: tutti lo sanno scrivere e leggere, anche fra due schede.
 *   ⚠ `[?]` Il prezzo: blit e lettura lineari sono un po' più lenti che in
 *     tiling.  Si misura prima di comprare altro.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ LA SINCRONIZZAZIONE, SENZA FENCE ESPLICITE — quando si può leggere?
 *
 *   `[R]` wlroots 0.18.2, `render/gles2/pass.c`: il blit finisce con
 *   `glFlush()`, non `glFinish()`, e subito dopo parte `ready`.  ⇒ Quando
 *   `ready` arriva il blit è CONSEGNATO alla GPU, non FINITO.  `[M]`
 *   `wp_linux_drm_syncobj_manager_v1` non c'è: nessuna fence ci viene data.
 *   ⇒ ⭐ Dopo `ready` la si ESTRAE dal DMA-BUF (`DMA_BUF_IOCTL_EXPORT_SYNC_FILE`
 *     con `DMA_BUF_SYNC_READ`) e si aspetta con `poll()` che scatti.
 *   ⚠ Costa: è `us_attesa_gpu`, e sta DENTRO il tempo del fotogramma.
 *   ⛔ Se l'ioctl non c'è (nucleo < 5.20) lo si dice una volta: da lì si conta
 *      sulla sola sincronizzazione implicita, e la riga lo nomina.
 *
 * ---------------------------------------------------------------------------
 * ⚠ LE DUE NUMERAZIONI DEL FORMATO — non si mescolano (difetto 1)
 *
 *   L'evento `buffer` parla `wl_shm.format` (0 e 1 speciali) → `f_shm`, e si
 *   traduce con `shm_a_drm()` SOLO per chi sta a valle.  L'evento
 *   `linux_dmabuf` parla il fourcc DRM vero → `o_scheda_formato`, e NON passa
 *   da `shm_a_drm()`.  La lastra si alloca ESATTAMENTE nel formato e nella
 *   misura di quell'evento: `[R]` wlroots, un formato o una misura diversi
 *   sono `invalid buffer` — un ERRORE DI PROTOCOLLO, e la connessione muore.
 *   ⭐ `[M]` labwc sulla scheda dà `XRGB8888` (B G R x in memoria): l'ordine
 *     che il codificatore legge già.  Se ne arrivasse un altro, la scheda si
 *     salta per quel fotogramma, dicendolo.
 */
#include "wlroots.h"

#include "forma.h"
#include "registro.h"

#include "linux-dmabuf-unstable-v1-client-protocol.h"
#include "wlr-output-management-unstable-v1-client-protocol.h"
#include "wlr-screencopy-unstable-v1-client-protocol.h"

#include <drm_fourcc.h>
#include <errno.h>
#include <fcntl.h>
#include <gbm.h>
#include <gio/gio.h>
#include <linux/dma-buf.h>
#include <poll.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
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

/* ⭐ Quante lastre — vedi il riquadro in cima, «le tre regole». */
#define WLR_LASTRE 3

/* ⛔ Quanti `failed` DI FILA sulla scheda prima di spegnerla: uno può essere
 *    l'uscita che cambia sotto il giro; tre sono una strada che non va. */
#define WLR_SCHEDA_FALLITI_MAX 3

/* ⚠ Il tetto della nascita di una lastra (la risposta a `create`).  ⛔ Non
 *   l'attesa del fotogramma: il figlio chiama con 8 ms, e una lastra che non
 *   nasce in 8 ms la prima volta spegnerebbe la scheda per sempre per un
 *   ritardo.  Succede tre volte per sessione (e a ogni cambio di misura). */
#define WLR_LASTRA_NASCITA_S 1.0

typedef enum {
	LASTRA_LIBERA = 0,
	LASTRA_IN_VOLO, /* nominata nel `copy` del fotogramma in corso      */
	LASTRA_IN_MANO  /* consegnata: finché non torna con `wlr_rendi()`   */
} LastraStato;

typedef struct {
	struct gbm_bo *bo;
	struct wl_buffer *buffer;
	int fd;
	uint32_t larghezza, altezza, stride, offset, formato; /* formato: fourcc DRM */
	uint64_t modificatore;
	LastraStato stato;
	bool sporca;
} WlrLastra;

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
	bool visto_buffer, visto_buffer_done, pronto, fallito, copia_partita, y_invertita;
	uint32_t f_shm; /* il formato come lo dice wl_shm: serve al buffer */
	uint32_t f_larghezza, f_altezza, f_stride;
	uint64_t f_secondi;
	uint32_t f_nanosecondi;

	bool detto_il_formato;
	/*
	 * ⭐⭐ IL DANNO — 21 settembre 2026, e l'ha trovato la rete.
	 *
	 * `[M]` La prima stesura chiedeva `copy`: il compositore copia l'uscita
	 * SUBITO, cambiata o no.  ⇒ Col desktop fermo il figlio produceva **~60
	 * fotogrammi identici al secondo** (247 nei primi 5 s, prima che la scena
	 * partisse), li codificava e li spediva.  Su GNOME e KDE il prodotto
	 * consegna solo quando qualcosa cambia; qui bruciava banda e scheda per
	 * niente — e la maglia C3 non vedeva più il suo guasto «codificatore
	 * fermo», perché prima del fermo erano già passati mille fotogrammi di
	 * desktop immobile.
	 * ⇒ `copy_with_damage` (screencopy v2+): il compositore risponde solo
	 *   quando l'uscita è CAMBIATA.  È lo stesso contratto della spinta.
	 * ⚠ Ma una CHIAVE a volte serve subito anche su un desktop fermo (un
	 *   cliente che si attacca, una richiesta §5.2): `forza_intero` fa sì che
	 *   il PROSSIMO giro usi `copy`, e lo mette `wlr_forza_intero()`.  Il primo
	 *   giro in assoluto è intero anche lui: chi si attacca deve vedere subito.
	 */
	bool forza_intero, detto_il_danno;
	bool copia_col_danno; /* la copia in volo è `copy_with_damage` */
	WlrConteggi conteggi;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ LA STRADA DELLA SCHEDA — il riquadro in cima.
	 *
	 * ⛔ Tutto qui sotto vale SOLO se `scheda_nata`: prima di
	 *    `wlr_chiedi_la_scheda()` i campi sono gli zeri di `g_new0`, e zero
	 *    per un descrittore vuol dire lo standard input — da cui la bandiera.
	 * ------------------------------------------------------------------ */
	struct zwp_linux_dmabuf_v1 *dmabuf;
	uint32_t dmabuf_versione;
	bool scheda_nata; /* nodo aperto, `gbm` creato, lastre inizializzate */
	bool scheda;      /* ⭐ in vigore ADESSO                              */
	int drm_fd;
	struct gbm_device *gbm;
	char *nodo;
	/* il `main_device` del feedback: il nodo su cui il compositore disegna */
	dev_t principale;
	bool principale_noto, feedback_finito;
	/* l'offerta della scheda in QUESTO fotogramma — ⛔ fourcc DRM, NON wl_shm */
	bool offerto_scheda;
	uint32_t o_scheda_formato, o_scheda_l, o_scheda_a;
	WlrLastra lastre[WLR_LASTRE];
	unsigned prossima;
	/* ⭐ -1: il fotogramma in corso va (o andrà) in memoria.  ⛔ Sopravvive
	 *    alla scadenza insieme a `frame`: è la lastra IN VOLO di QUEL
	 *    fotogramma, e la chiamata dopo la ritrova. */
	int lastra_del_giro;
	uint64_t generazione;
	unsigned falliti_di_fila;
	/* la creazione del `wl_buffer` (`zwp_linux_buffer_params_v1`) */
	struct wl_buffer *creato;
	bool params_finito, params_fallito;
	/* ⚠ le righe che si dicono una volta sola */
	bool detto_senza_offerta, detto_formato_scheda, detta_sync_implicita;
	bool detto_il_formato_scheda;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ LA SONDA DEL PUNTATORE — il riquadro sopra `wlr_sonda_puntatore`.
	 *
	 * ⛔ Tutto suo: un fotogramma, un buffer, un descrittore che NON sono
	 *    quelli del flusso.  Il flusso principale non sa che la sonda esiste.
	 * ------------------------------------------------------------------ */
	struct zwlr_screencopy_frame_v1 *s_frame; /* UNA sola in volo        */
	bool s_visto_buffer, s_copia_partita;
	uint32_t s_f_shm, s_f_l, s_f_a, s_f_stride;
	struct wl_buffer *s_buffer;
	void *s_pixel;
	int s_fd;
	gsize s_byte;
	uint32_t s_b_l, s_b_a, s_b_stride, s_b_shm;
	/* la posizione della richiesta IN VOLO, e quella da rilanciare */
	int32_t s_x, s_y;
	bool s_in_attesa; /* ⭐ coalescente: si ricorda solo l'ULTIMA posizione */
	int32_t s_attesa_x, s_attesa_y;
	/* ⭐ la sonda «di coda»: una in piu', a mano ferma — vedi il riquadro */
	gint64 s_coda_a;
	bool s_coda_fatta;
	gint64 s_ultima_partita; /* per il diradamento */
	int s_forma;             /* l'ultima forma riconosciuta, -1 = nessuna  */
	int s_nuova;             /* da consegnare a `wlr_sonda_forma`, o -1    */
	bool s_spenta;           /* il formato non si legge: detto, e basta   */
	bool s_detto_formato, s_detta_ignota, s_detto_fallito;
	WlrSondaConteggi s_conto;
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

/* ⚠ Sotto la v4 il global manda `format` e `modifier` appena legato: si
 *   ascoltano e si lasciano cadere — il modificatore lo decidiamo noi
 *   (LINEARE, il riquadro in cima), non l'elenco. */
static void dmabuf_formato(void *d, struct zwp_linux_dmabuf_v1 *m, uint32_t f) {}
static void dmabuf_modificatore(void *d, struct zwp_linux_dmabuf_v1 *m, uint32_t f,
                                uint32_t alto, uint32_t basso) {}

static const struct zwp_linux_dmabuf_v1_listener ASCOLTO_DMABUF = {
	.format = dmabuf_formato,
	.modifier = dmabuf_modificatore,
};

static void registro_global(void *dati, struct wl_registry *reg, uint32_t nome,
                            const char *interfaccia, uint32_t versione)
{
	WlrPalco *p = dati;

	if (g_strcmp0(interfaccia, wl_shm_interface.name) == 0) {
		p->shm = wl_registry_bind(reg, nome, &wl_shm_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_screencopy_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 3 ? versione : 3;

		p->manager = wl_registry_bind(reg, nome, &zwlr_screencopy_manager_v1_interface, v);
	} else if (g_strcmp0(interfaccia, zwp_linux_dmabuf_v1_interface.name) == 0 &&
	           !p->dmabuf) {
		/* ⭐ La strada della scheda.  ⚠ Al massimo la v4 (`[M]` labwc la dà):
		 *   è quella del `main_device`, cioè del nodo su cui il compositore
		 *   disegna.  ⛔ Si lega sempre, anche se la scheda non si chiede:
		 *   legare non costa niente e non cambia niente. */
		p->dmabuf_versione = versione < 4 ? versione : 4;
		p->dmabuf = wl_registry_bind(reg, nome, &zwp_linux_dmabuf_v1_interface,
		                             p->dmabuf_versione);
		zwp_linux_dmabuf_v1_add_listener(p->dmabuf, &ASCOLTO_DMABUF, p);
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
	WlrPalco *p = dati;

	/* ⭐ La strada della scheda: si ANNOTA l'offerta, e la scelta la fa
	 *    `scheda_destinazione()` a elenco chiuso.  ⛔ E qui il formato è un
	 *    fourcc DRM VERO — un'altra numerazione da quella di `buffer`, in un
	 *    campo suo, e NON passa da `shm_a_drm()` (difetto 1). */
	p->offerto_scheda = true;
	p->o_scheda_formato = formato;
	p->o_scheda_l = larghezza;
	p->o_scheda_a = altezza;
}

static void frame_buffer_done(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	((WlrPalco *)dati)->visto_buffer_done = true;
}

/* ⭐ «L'elenco delle offerte è chiuso?» — sulla v3 lo dice `buffer_done`, e
 *    solo allora si sa se la scheda è stata offerta.  ⚠ Sotto la v3
 *    `buffer_done` non esiste: lì basta `buffer`, che è anche l'unica offerta. */
static bool elenco_chiuso(const WlrPalco *p)
{
	if (p->visto_buffer_done)
		return true;
	return p->visto_buffer && zwlr_screencopy_frame_v1_get_version(p->frame) < 3;
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

/* ========================================================================= */
/* ⭐⭐ LA STRADA DELLA SCHEDA — il riquadro in cima al file.                  */
/*                                                                           */
/* ⛔ Tutto quel che segue sta in funzioni SUE: `wlr_fotogramma()` le chiama  */
/*    in tre punti (la destinazione del `copy`, la consegna, la chiusura del  */
/*    fotogramma), e il giro della memoria resta com'era.                     */
/* ========================================================================= */

/* --- il feedback: il nodo su cui il compositore disegna ------------------ */

static void feedback_fine(void *dati, struct zwp_linux_dmabuf_feedback_v1 *f)
{
	((WlrPalco *)dati)->feedback_finito = true;
}

static void feedback_tabella(void *dati, struct zwp_linux_dmabuf_feedback_v1 *f, int32_t fd,
                             uint32_t quanti)
{
	/* ⛔ Il descrittore è NOSTRO appena arriva, e si chiude: la tabella dei
	 *    formati non serve (il modificatore è LINEARE, deciso), e un `fd`
	 *    tenuto per niente è un `fd` perso a ogni sessione. */
	close(fd);
}

static void feedback_principale(void *dati, struct zwp_linux_dmabuf_feedback_v1 *f,
                                struct wl_array *dispositivo)
{
	WlrPalco *p = dati;

	/* ⚠ Il protocollo lo dà come un `dev_t` in un array: se la misura non
	 *   torna non si indovina, si lascia «non noto» e si ripiega dicendolo. */
	if (dispositivo->size == sizeof(dev_t)) {
		memcpy(&p->principale, dispositivo->data, sizeof(dev_t));
		p->principale_noto = true;
	}
}

static void feedback_tranche_fine(void *d, struct zwp_linux_dmabuf_feedback_v1 *f) {}
static void feedback_tranche_disp(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                  struct wl_array *a) {}
static void feedback_tranche_formati(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                     struct wl_array *a) {}
static void feedback_tranche_bandiere(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                      uint32_t b) {}

static const struct zwp_linux_dmabuf_feedback_v1_listener ASCOLTO_FEEDBACK = {
	.done = feedback_fine,
	.format_table = feedback_tabella,
	.main_device = feedback_principale,
	.tranche_done = feedback_tranche_fine,
	.tranche_target_device = feedback_tranche_disp,
	.tranche_formats = feedback_tranche_formati,
	.tranche_flags = feedback_tranche_bandiere,
};

/*
 * Dal `dev_t` al nodo `renderD*` della stessa scheda.
 *
 * ⚠ Il `main_device` può essere il nodo primario (`card0`) o quello di
 *   rendering: la cartella di sysfs `/sys/dev/char/M:m/device/drm/` li elenca
 *   TUTTI E DUE in entrambi i casi, e da lì si prende il `renderD*`.  ⛔ Niente
 *   `libdrm` da collegare per questo: una libreria in più per una riga di
 *   sysfs.
 */
static char *nodo_da_dispositivo(dev_t d)
{
	g_autofree char *cartella =
	    g_strdup_printf("/sys/dev/char/%u:%u/device/drm", major(d), minor(d));
	g_autoptr(GDir) dir = g_dir_open(cartella, 0, NULL);
	const char *voce;

	if (!dir)
		return NULL;
	while ((voce = g_dir_read_name(dir)))
		if (g_str_has_prefix(voce, "renderD"))
			return g_build_filename("/dev/dri", voce, NULL);
	return NULL;
}

/*
 * ⚠ IL RIPIEGO, quando il compositore non dice il suo nodo (v < 4): la STESSA
 *   regola con cui `sessione.c` sceglie `WLR_RENDER_DRM_DEVICE` — il primo
 *   `renderD*` apribile, in ordine di nome.  ⛔ Una regola diversa qui
 *   vorrebbe dire allocare sull'altra scheda proprio il giorno in cui i nodi
 *   si scambiano.
 */
static char *nodo_come_sessione(void)
{
	g_autoptr(GDir) dri = g_dir_open("/dev/dri", 0, NULL);
	const char *voce;
	g_autofree char *primo = NULL;

	if (!dri)
		return NULL;
	while ((voce = g_dir_read_name(dri))) {
		g_autofree char *percorso = NULL;
		int fd;

		if (!g_str_has_prefix(voce, "renderD"))
			continue;
		percorso = g_build_filename("/dev/dri", voce, NULL);
		fd = open(percorso, O_RDWR | O_CLOEXEC);
		if (fd < 0)
			continue;
		close(fd);
		if (!primo || g_strcmp0(voce, primo) < 0) {
			g_free(primo);
			primo = g_strdup(voce);
		}
	}
	return primo ? g_build_filename("/dev/dri", primo, NULL) : NULL;
}

/* --- le lastre ------------------------------------------------------------ */

/*
 * ⛔⛔ LA GENERAZIONE E' DEL PROCESSO, NON DEL PALCO — 22 set 2026: su KDE il
 *      contatore ripartiva da 0 con ogni cattura nuova, e dopo «Esci» e un
 *      nuovo accesso il codificatore (che resta) ritrovava in cache le
 *      superfici della sessione morta: lo schermo lampeggiava.  Vedi
 *      `generazione_nuova()` in `cattura.c`.  ⇒ Qui lo stesso, perche' un
 *      palco nuovo nasce a ogni rinascita della sessione XFCE.
 * ⚠ Parte da 2^62, e non da 0: `cattura.c` ha il suo contatore (questo file
 *   si lega anche al banco 13-w1, senza `cattura.o`), e i due intervalli non
 *   si toccano.
 */
static uint64_t generazione_nuova(void)
{
	static uint64_t ultima = UINT64_C(1) << 62;

	return __atomic_add_fetch(&ultima, 1, __ATOMIC_RELAXED);
}

/* ⛔ «Il fotogramma in corso è sulla scheda?» — e la bandiera prima
 *    dell'indice: prima di `wlr_chiedi_la_scheda()` l'indice è lo zero di
 *    `g_new0`, cioè una lastra che non esiste. */
static bool scheda_nel_giro(const WlrPalco *p)
{
	return p->scheda_nata && p->lastra_del_giro >= 0;
}

static void lastra_butta(WlrPalco *p, WlrLastra *l)
{
	bool cera = l->bo || l->buffer;

	if (l->buffer)
		wl_buffer_destroy(l->buffer);
	if (l->bo)
		gbm_bo_destroy(l->bo);
	if (l->fd >= 0)
		close(l->fd);
	memset(l, 0, sizeof *l);
	l->fd = -1;
	/* ⛔ Regola 3: una lastra che muore cambia la generazione. */
	if (cera)
		p->generazione = generazione_nuova();
}

/*
 * ⭐ Una lastra torna LIBERA — l'unico posto che lo fa, oltre a `wlr_rendi()`.
 *
 * ⚠ Se nel frattempo la scheda si è spenta, la lastra non serve più: si butta
 *   adesso, che è il primo momento in cui si può.
 */
static void lastra_torna_libera(WlrPalco *p, WlrLastra *l, bool sporca)
{
	l->stato = LASTRA_LIBERA;
	if (sporca)
		l->sporca = true;
	if (!p->scheda)
		lastra_butta(p, l);
}

static void params_creato(void *dati, struct zwp_linux_buffer_params_v1 *pr,
                          struct wl_buffer *buffer)
{
	WlrPalco *p = dati;

	p->creato = buffer;
	p->params_finito = true;
}

static void params_fallito(void *dati, struct zwp_linux_buffer_params_v1 *pr)
{
	WlrPalco *p = dati;

	p->params_fallito = true;
	p->params_finito = true;
}

static const struct zwp_linux_buffer_params_v1_listener ASCOLTO_PARAMS = {
	.created = params_creato,
	.failed = params_fallito,
};

/*
 * Fa nascere (o tiene) la lastra per il formato e la misura di QUESTO
 * fotogramma.
 *
 * ⛔ `create` e non `create_immed`: col secondo un rifiuto del compositore
 *    può essere un errore di PROTOCOLLO, cioè la connessione che muore.  Col
 *    primo è un evento `failed`, e si ripiega dicendolo.
 * ⛔ E si aspetta con un tetto SUO (`WLR_LASTRA_NASCITA_S`), non con quello del
 *    fotogramma: vedi la definizione.
 */
static bool lastra_prepara(WlrPalco *p, WlrLastra *l, uint32_t formato, uint32_t larghezza,
                           uint32_t altezza, GError **sbaglio)
{
	uint64_t lineare = DRM_FORMAT_MOD_LINEAR;
	struct zwp_linux_buffer_params_v1 *params;
	gint64 scadenza;

	if (l->buffer && !l->sporca && l->larghezza == larghezza && l->altezza == altezza &&
	    l->formato == formato)
		return true; /* quella di prima va bene */
	lastra_butta(p, l);

	/* ⭐ LINEARE, chiesto per nome.  ⚠ Se il driver non accetta la lista dei
	 *   modificatori si riprova con la bandiera LINEAR, che dice la stessa
	 *   cosa nel dialetto vecchio. */
	l->bo = gbm_bo_create_with_modifiers2(p->gbm, larghezza, altezza, formato, &lineare, 1,
	                                      GBM_BO_USE_RENDERING);
	if (!l->bo)
		l->bo = gbm_bo_create(p->gbm, larghezza, altezza, formato,
		                      GBM_BO_USE_RENDERING | GBM_BO_USE_LINEAR);
	if (!l->bo) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
		            "gbm non alloca %ux%u fourcc 0x%08x lineare su %s: %s", larghezza,
		            altezza, formato, p->nodo, g_strerror(errno));
		return false;
	}
	if (gbm_bo_get_plane_count(l->bo) != 1) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "gbm ha dato una lastra a %d piani: il codificatore ne sa leggere uno",
		            gbm_bo_get_plane_count(l->bo));
		lastra_butta(p, l);
		return false;
	}
	l->modificatore = gbm_bo_get_modifier(l->bo);
	/* ⚠ Col dialetto vecchio il modificatore può tornare INVALID: la bandiera
	 *   LINEAR però l'ha fissato, e lo si scrive per quel che è. */
	if (l->modificatore == DRM_FORMAT_MOD_INVALID)
		l->modificatore = DRM_FORMAT_MOD_LINEAR;
	if (l->modificatore != DRM_FORMAT_MOD_LINEAR) {
		/* ⛔ Si era chiesto LINEARE: un tiling che nessuno ha scelto è
		 *    un'importazione che nessuno ha provato. */
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "gbm ha dato il modificatore 0x%" G_GINT64_MODIFIER "x invece del "
		            "LINEARE chiesto",
		            (guint64)l->modificatore);
		lastra_butta(p, l);
		return false;
	}
	l->fd = gbm_bo_get_fd(l->bo);
	l->stride = gbm_bo_get_stride_for_plane(l->bo, 0);
	l->offset = gbm_bo_get_offset(l->bo, 0);
	l->larghezza = larghezza;
	l->altezza = altezza;
	l->formato = formato;
	if (l->fd < 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "gbm_bo_get_fd: la lastra non ha un descrittore DMA-BUF");
		lastra_butta(p, l);
		return false;
	}
	/* ⛔ La lastra è già nata qui, anche se il `wl_buffer` non c'è ancora: la
	 *    generazione cambia ADESSO (regola 3). */
	p->generazione = generazione_nuova();

	p->creato = NULL;
	p->params_finito = p->params_fallito = false;
	params = zwp_linux_dmabuf_v1_create_params(p->dmabuf);
	zwp_linux_buffer_params_v1_add_listener(params, &ASCOLTO_PARAMS, p);
	zwp_linux_buffer_params_v1_add(params, l->fd, 0, l->offset, l->stride,
	                               (uint32_t)(l->modificatore >> 32),
	                               (uint32_t)(l->modificatore & 0xffffffffu));
	zwp_linux_buffer_params_v1_create(params, (int32_t)larghezza, (int32_t)altezza, formato, 0);
	scadenza = g_get_monotonic_time() + (gint64)(WLR_LASTRA_NASCITA_S * G_USEC_PER_SEC);
	while (!p->params_finito) {
		if (!pompa(p, scadenza, sbaglio)) {
			zwp_linux_buffer_params_v1_destroy(params);
			lastra_butta(p, l);
			return false;
		}
		if (!p->params_finito && g_get_monotonic_time() >= scadenza)
			break;
	}
	zwp_linux_buffer_params_v1_destroy(params);
	if (!p->params_finito || p->params_fallito || !p->creato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "il compositore %s il DMA-BUF %ux%u lineare (passo %u)",
		            p->params_finito ? "ha RIFIUTATO" : "non ha risposto in tempo per",
		            larghezza, altezza, l->stride);
		/* ⚠ Se `created` arrivasse dopo il tetto il `wl_buffer` resterebbe
		 *   orfano: un oggetto perso, una volta, contro una connessione viva. */
		lastra_butta(p, l);
		return false;
	}
	l->buffer = p->creato;
	p->creato = NULL;
	l->sporca = false;
	return true;
}

/* ⛔ Regola 1: si sceglie SOLO una lastra LIBERA, a rotazione. */
static int lastra_scegli(WlrPalco *p)
{
	for (unsigned i = 0; i < WLR_LASTRE; i++) {
		unsigned k = (p->prossima + i) % WLR_LASTRE;

		if (p->lastre[k].stato == LASTRA_LIBERA) {
			p->prossima = (k + 1) % WLR_LASTRE;
			return (int)k;
		}
	}
	return -1;
}

/*
 * ⛔ La scheda si SPEGNE, e si dice perché.  Da qui ogni fotogramma va in
 *    memoria, e i conteggi lo mostrano.
 * ⚠ Si buttano solo le LIBERE: una IN MANO la butta `wlr_rendi()` quando
 *   torna, una IN VOLO la chiusura del suo fotogramma (`lastra_torna_libera`).
 *   ⛔ Buttare una lastra in volo vorrebbe dire distruggere un `wl_buffer`
 *   nominato in un `copy` ancora aperto.
 */
static void scheda_spegni(WlrPalco *p, const char *perche)
{
	if (!p->scheda)
		return;
	p->scheda = false;
	for (unsigned i = 0; i < WLR_LASTRE; i++)
		if (p->lastre[i].stato == LASTRA_LIBERA)
			lastra_butta(p, &p->lastre[i]);
	registro_dice(AREA,
	              "⛔⛔ wlroots: la strada della SCHEDA si SPEGNE — %s.  ⇒ RIPIEGO "
	              "DICHIARATO: da qui i pixel passano per la MEMORIA (`glReadPixels` "
	              "nel compositore + la nostra copia), e i numeri del tratto sono "
	              "quelli dell'altra strada",
	              perche);
}

/*
 * ⭐ LA DESTINAZIONE DEL `copy` DI QUESTO FOTOGRAMMA — la scheda, o NULL per la
 *    memoria.  Si chiama a elenco chiuso (`elenco_chiuso()`), UNA volta per
 *    fotogramma: dopo, la risposta sta in `lastra_del_giro`.
 *
 * ⛔ Torna NULL anche con `*rotto` vero: tutte le lastre sono in mano a valle.
 *    Lì il fotogramma si FERMA, non si ricicla una lastra in mano e non si
 *    ripiega in silenzio sulla memoria (regola 1).
 */
static struct wl_buffer *scheda_destinazione(WlrPalco *p, bool *rotto, GError **sbaglio)
{
	g_autoptr(GError) perche = NULL;
	WlrLastra *l;
	int k;

	*rotto = false;
	p->lastra_del_giro = -1;
	if (!p->scheda)
		return NULL;
	if (!p->offerto_scheda) {
		/* ⚠ `[R]` wlroots manda `linux_dmabuf` solo se l'allocatore
		 *   dell'uscita sa fare DMA-BUF: senza, il compositore è in SOFTWARE
		 *   (pixman, `STUDI.md` §xfce §5.2).  È una diagnosi, e si scrive. */
		if (!p->detto_senza_offerta) {
			p->detto_senza_offerta = true;
			registro_dice(AREA,
			              "⛔ wlroots: il compositore NON offre DMA-BUF per questo "
			              "fotogramma — di solito vuol dire che disegna in SOFTWARE "
			              "(pixman, `STUDI.md` §xfce §5.2).  RIPIEGO DICHIARATO: il "
			              "fotogramma va in MEMORIA; la riga non si ripete");
		}
		return NULL;
	}
	if (p->o_scheda_formato != DRM_FORMAT_XRGB8888 &&
	    p->o_scheda_formato != DRM_FORMAT_ARGB8888) {
		if (!p->detto_formato_scheda) {
			char nome[5];

			p->detto_formato_scheda = true;
			memcpy(nome, &p->o_scheda_formato, 4);
			nome[4] = 0;
			registro_dice(AREA,
			              "⛔ wlroots: la scheda offre «%s», e il codificatore importa "
			              "solo XRGB8888 e ARGB8888 — ⚠ NON si indovina un fourcc (un "
			              "canale scambiato non dà errore, dà un desktop blu).  "
			              "RIPIEGO DICHIARATO: il fotogramma va in MEMORIA",
			              nome);
		}
		return NULL;
	}

	k = lastra_scegli(p);
	if (k < 0) {
		*rotto = true;
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BUSY,
		            "tutte e %d le lastre della scheda sono IN MANO a valle: qualcuno "
		            "non ha chiamato `wlr_rendi()` (cioè `cattura_fermo_libera()`).  ⛔ "
		            "Non se ne ricicla una: sarebbe riscrivere un'immagine mentre il "
		            "codificatore la legge",
		            WLR_LASTRE);
		return NULL;
	}
	l = &p->lastre[k];
	if (!lastra_prepara(p, l, p->o_scheda_formato, p->o_scheda_l, p->o_scheda_a, &perche)) {
		g_autofree char *motivo =
		    g_strdup_printf("la lastra non è nata (%s)", perche ? perche->message : "?");

		scheda_spegni(p, motivo);
		return NULL;
	}
	l->stato = LASTRA_IN_VOLO;
	p->lastra_del_giro = k;
	return l->buffer;
}

/*
 * ⛔⛔ L'ATTESA DELLA GPU DOPO `ready` — il riquadro della sincronizzazione.
 *
 * Torna falso solo se la fence c'era e NON è scattata entro la scadenza: lì
 * la lastra non si consegna (chi la leggesse vedrebbe un blit a metà), e il
 * fotogramma resta PENDENTE — la chiamata dopo riaspetta.
 */
static bool scheda_aspetta_la_gpu(WlrPalco *p, WlrLastra *l, gint64 scadenza,
                                  WlrFotogramma *fuori, GError **sbaglio)
{
	struct dma_buf_export_sync_file sf = { .flags = DMA_BUF_SYNC_READ, .fd = -1 };
	gint64 prima = g_get_monotonic_time();
	struct pollfd pfd;
	gint64 resta;
	int r;

	fuori->us_attesa_gpu = 0;
	fuori->attesa_esplicita = false;
	if (ioctl(l->fd, DMA_BUF_IOCTL_EXPORT_SYNC_FILE, &sf) != 0) {
		/* ⚠ Nucleo senza l'ioctl (< 5.20), o un driver che non lo regge: si
		 *   conta sulla sincronizzazione IMPLICITA, e lo si dice una volta. */
		if (!p->detta_sync_implicita) {
			p->detta_sync_implicita = true;
			registro_dice(AREA,
			              "⚠ wlroots: la fence dentro il DMA-BUF non si estrae "
			              "(DMA_BUF_IOCTL_EXPORT_SYNC_FILE: %s) — da qui si conta "
			              "sulla sola sincronizzazione IMPLICITA fra compositore e "
			              "codificatore.  `[?]` Se il desktop mostra righe a metà, "
			              "è QUESTA riga",
			              g_strerror(errno));
		}
		return true;
	}
	fuori->attesa_esplicita = true;
	resta = (scadenza - prima) / 1000;
	pfd.fd = sf.fd;
	pfd.events = POLLIN;
	do {
		r = poll(&pfd, 1, resta > 0 ? (int)resta : 0);
	} while (r < 0 && errno == EINTR);
	close(sf.fd);
	fuori->us_attesa_gpu = (uint64_t)(g_get_monotonic_time() - prima);
	if (r <= 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "il compositore ha detto «ready» ma il blit sulla GPU non è finito "
		            "entro la scadenza (%.1f ms di attesa della fence) — il fotogramma "
		            "resta in corso",
		            fuori->us_attesa_gpu / 1000.0);
		return false;
	}
	return true;
}

/* ⭐ La consegna di un fotogramma della scheda: la lastra passa IN MANO. */
static void scheda_consegna(WlrPalco *p, WlrFotogramma *fuori)
{
	WlrLastra *l = &p->lastre[p->lastra_del_giro];

	p->falliti_di_fila = 0;
	l->stato = LASTRA_IN_MANO;
	p->lastra_del_giro = -1;

	fuori->sulla_scheda = true;
	fuori->pixel = NULL;
	fuori->larghezza = l->larghezza;
	fuori->altezza = l->altezza;
	fuori->stride = l->stride;
	/* ⛔ Il fourcc DRM dell'evento `linux_dmabuf`, così com'è: NON passa da
	 *    `shm_a_drm()` (difetto 1). */
	fuori->formato = l->formato;
	fuori->byte = (gsize)l->stride * l->altezza;
	fuori->fd = l->fd;
	fuori->offset = l->offset;
	fuori->modificatore = l->modificatore;
	fuori->generazione = p->generazione;
	fuori->lastra = l;
	fuori->secondi = p->f_secondi;
	fuori->nanosecondi = p->f_nanosecondi;
	/* ⚠ `[R]` Sulla scheda il compositore manda `flags 0`: il blit scrive già
	 *   dritto.  Si consegna comunque quel che ha detto. */
	fuori->y_invertita = p->y_invertita;

	if (!p->detto_il_formato_scheda) {
		char nome[5];

		p->detto_il_formato_scheda = true;
		memcpy(nome, &l->formato, 4);
		nome[4] = 0;
		registro_dice(AREA,
		              "⭐ wlroots: il PRIMO fotogramma della SCHEDA — «%s» %ux%u passo "
		              "%u, lastra lineare, %s",
		              nome, l->larghezza, l->altezza, l->stride,
		              fuori->attesa_esplicita
		                  ? "fence estratta dal DMA-BUF e aspettata"
		                  : "⚠ senza fence: sincronizzazione implicita");
	}
}

static void scheda_chiudi(WlrPalco *p)
{
	if (!p->scheda_nata)
		return;
	for (unsigned i = 0; i < WLR_LASTRE; i++)
		lastra_butta(p, &p->lastre[i]);
	if (p->gbm)
		gbm_device_destroy(p->gbm);
	if (p->drm_fd >= 0)
		close(p->drm_fd);
	g_free(p->nodo);
	p->nodo = NULL;
	p->scheda_nata = p->scheda = false;
}

/*
 * Chiude il fotogramma in corso.  `copia_viva` = la copia era partita e NON è
 * arrivato né `ready` né `failed`: il buffer non si riusa.
 *
 * ⭐ E la lastra del fotogramma, se c'era e NON è stata consegnata (filo
 *    caduto, `failed`): regola 2, è sporca.  ⚠ Una lastra consegnata ha già
 *    `lastra_del_giro = -1`, e qui non si tocca.
 */
static void chiudi_frame(WlrPalco *p, bool copia_viva)
{
	if (p->frame)
		zwlr_screencopy_frame_v1_destroy(p->frame);
	p->frame = NULL;
	if (scheda_nel_giro(p)) {
		lastra_torna_libera(p, &p->lastre[p->lastra_del_giro], true);
		p->lastra_del_giro = -1;
	} else if (copia_viva) {
		p->buffer_sporco = true;
	}
	p->copia_partita = false;
	p->copia_col_danno = false;
}

/* ========================================================================= */
/* ⭐⭐ LA SONDA DEL PUNTATORE — la forma vera su labwc (XFCE e LXQt).         */
/* ========================================================================= */

/*
 * ⛔ IL FATTO `[M]`: labwc headless non ha un piano del cursore — il puntatore
 *    lo disegna via software DENTRO il buffer dell'uscita, e screencopy non ha
 *    un canale per la sua forma.  ⭐ Ma il tema codificato (`forma.h`) fa si'
 *    che sotto il punto attivo ci sia UN pixel opaco di un colore che e' solo
 *    di quella forma.  ⇒ Basta guardarlo.
 *
 * ⭐ COME SI GUARDA: `capture_output_region` di 3x3 attorno al punto, in un
 *    `wl_shm` di 36 byte, dopo ogni gesto del puntatore.  Il 3x3 e non l'1x1
 *    perche' il punto in coordinate dell'uscita e' frazionario (il puntatore
 *    virtuale e' normalizzato) e `[?]` come wlroots lo porta al pixel non l'ho
 *    letto: con tre pixel per lato non importa.  Si guarda il CENTRO, poi i
 *    vicini.
 *
 * ⛔ LE TRE REGOLE:
 *   1. UNA sola in volo.  Se il puntatore si muove mentre una e' in volo, si
 *      ricorda solo l'ULTIMA posizione, e si rilancia quando la prima torna
 *      (coalescente): a 60 Hz di mano non si accodano 60 sonde.
 *   2. La copia e' `copy`, mai `copy_with_damage`: wlroots la serve al
 *      prossimo commit dell'uscita, e il movimento del puntatore ne provoca
 *      comunque uno (il cursore software e' danno).
 *   3. ⭐ LA SONDA DI CODA.  `[R]` il client cambia forma DOPO aver ricevuto
 *      l'`enter` — cioe' DOPO il movimento che l'ha provocata — e la sonda
 *      di quel movimento puo' tornare prima che il client abbia risposto.
 *      ⇒ A mano ferma, SONDA_CODA_US dopo l'ultima, se ne manda una in piu',
 *      una volta sola.  Senza, chi si ferma su un bordo col primo gesto
 *      terrebbe la freccia.
 *
 * ⛔ IL FILO: tutto gira sul thread del ciclo del figlio — la domanda parte da
 *    `wlr_sonda_puntatore` (dopo l'iniezione del gesto), gli eventi li pompa
 *    `wlr_fotogramma` (la stessa pompa del flusso), e la forma la raccoglie
 *    `wlr_sonda_forma` (da `cattura_prendi`).  ⇒ Nessun lucchetto, e nessuna
 *    consegna da dentro una richiamata di `libwayland`.
 *
 * ⚠ LO SPAZIO: la regione e' in coordinate dell'USCITA; il figlio passa le
 *   coordinate della sua tela, e si scala come fa wlroots col puntatore
 *   virtuale (`motion_absolute` e' normalizzato).  `[?]` scala 1: `wl_output`
 *   dice la scala, qui non si legge, e sulle scatole e' 1.
 * ⚠ I PIXEL: il formato lo dice l'evento `buffer` (numerazione wl_shm).
 *   `[M]` labwc da' `XBGR8888`, cioe' R G B x in memoria; ARGB/XRGB sono
 *   B G R A.  L'alfa del buffer dell'uscita non vuol dire niente (l'uscita e'
 *   opaca): si passa 0xFF, e il controllo lo fanno verde e blu esatti.
 * ⚠ IL COSTO: ogni sonda e' una lettura 3x3 dal renderer del compositore.
 *   `[M]` 24 set 2026, rete14-lxqt (Intel UHD 730, tela 1344x870), puntatore
 *   mosso a ~55 Hz per 30 s sopra qterminal, due giri per caso:
 *       senza sonda      labwc 4,9-5,1%   figlio 11,2%   dipinti 55,1-55,3/s
 *       sonda a 60 Hz    labwc 6,3-6,4%   figlio 11,6-11,8%   55,0-55,2/s
 *       sonda a 30 Hz    labwc 5,7%       figlio 11,6-11,7%   55,1-55,3/s
 *   ⇒ +1,4 punti di CPU di labwc (+0,5 del figlio), fotogrammi invariati:
 *     sotto la soglia dei 2 punti, e il diradamento resta SPENTO.  Se un
 *     giorno servisse: SONDA_MINIMO_US 33333 e' il 30 Hz misurato qui sopra.
 */

/* ⭐ Quanto dopo l'ultima sonda si manda quella di coda. */
#define SONDA_CODA_US (120 * 1000)
/* ⚠ Il diradamento: 0 = una per gesto (coalescente).  Vedi il costo, sopra. */
#define SONDA_MINIMO_US 0

static void sonda_lancia(WlrPalco *p, int32_t x, int32_t y);

static void sonda_chiudi_frame(WlrPalco *p)
{
	if (p->s_frame)
		zwlr_screencopy_frame_v1_destroy(p->s_frame);
	p->s_frame = NULL;
	p->s_visto_buffer = p->s_copia_partita = false;
}

/* Il buffer della sonda: si rifa' solo se il compositore ne chiede un altro. */
static bool sonda_buffer(WlrPalco *p)
{
	struct wl_shm_pool *pool;
	gsize byte = (gsize)p->s_f_stride * p->s_f_a;

	if (p->s_buffer && p->s_b_l == p->s_f_l && p->s_b_a == p->s_f_a &&
	    p->s_b_stride == p->s_f_stride && p->s_b_shm == p->s_f_shm)
		return true;
	if (p->s_buffer)
		wl_buffer_destroy(p->s_buffer);
	p->s_buffer = NULL;
	if (p->s_pixel)
		munmap(p->s_pixel, p->s_byte);
	p->s_pixel = NULL;
	if (p->s_fd >= 0)
		close(p->s_fd);
	p->s_fd = -1;
	/* ⛔ Un tetto: la regione e' 3x3, e un compositore che chiede di piu' non
	 *    sta rispondendo a questa domanda. */
	if (byte == 0 || byte > 4096 || p->s_f_stride < p->s_f_l * 4u)
		return false;
	p->s_fd = memfd_create("remotix-sonda", MFD_CLOEXEC);
	if (p->s_fd < 0 || ftruncate(p->s_fd, (off_t)byte) != 0)
		return false;
	p->s_pixel = mmap(NULL, byte, PROT_READ | PROT_WRITE, MAP_SHARED, p->s_fd, 0);
	if (p->s_pixel == MAP_FAILED) {
		p->s_pixel = NULL;
		return false;
	}
	p->s_byte = byte;
	pool = wl_shm_create_pool(p->shm, p->s_fd, (int32_t)byte);
	p->s_buffer = wl_shm_pool_create_buffer(pool, 0, (int32_t)p->s_f_l, (int32_t)p->s_f_a,
	                                        (int32_t)p->s_f_stride, p->s_f_shm);
	wl_shm_pool_destroy(pool);
	p->s_b_l = p->s_f_l;
	p->s_b_a = p->s_f_a;
	p->s_b_stride = p->s_f_stride;
	p->s_b_shm = p->s_f_shm;
	return true;
}

/* La fine di una sonda (tornata o fallita): se ce n'e' una in attesa, parte. */
static void sonda_prossima(WlrPalco *p)
{
	sonda_chiudi_frame(p);
	if (p->s_in_attesa && g_get_monotonic_time() - p->s_ultima_partita >= SONDA_MINIMO_US) {
		p->s_in_attesa = false;
		sonda_lancia(p, p->s_attesa_x, p->s_attesa_y);
	}
}

static void sonda_parti(WlrPalco *p)
{
	if (p->s_copia_partita)
		return;
	if (!sonda_buffer(p)) {
		if (!p->s_detto_fallito) {
			p->s_detto_fallito = true;
			registro_dice(AREA, "⚠ wlroots: la sonda del puntatore non ha un buffer "
			                    "(%ux%u stride %u): la forma non si guarda, e il client "
			                    "tiene la sua freccia",
			              p->s_f_l, p->s_f_a, p->s_f_stride);
		}
		p->s_conto.fallite++;
		sonda_prossima(p);
		return;
	}
	zwlr_screencopy_frame_v1_copy(p->s_frame, p->s_buffer);
	p->s_copia_partita = true;
}

static void sonda_buffer_ev(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                            uint32_t l, uint32_t a, uint32_t stride)
{
	WlrPalco *p = dati;

	p->s_visto_buffer = true;
	p->s_f_shm = formato;
	p->s_f_l = l;
	p->s_f_a = a;
	p->s_f_stride = stride;
	/* ⚠ Sotto la v3 `buffer_done` non c'e': l'unica offerta e' questa. */
	if (zwlr_screencopy_frame_v1_get_version(f) < 3)
		sonda_parti(p);
}

static void sonda_buffer_done(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	WlrPalco *p = dati;

	if (p->s_visto_buffer)
		sonda_parti(p);
}

/*
 * Un pixel della sonda ⇒ B G R, secondo il formato dichiarato.  FALSE = un
 * formato che qui non si legge (detto una volta, e la sonda si spegne).
 */
static bool sonda_bgr(uint32_t shm, const uint8_t *q, uint8_t *b, uint8_t *g, uint8_t *r)
{
	switch (shm) {
	case WL_SHM_FORMAT_ARGB8888:
	case WL_SHM_FORMAT_XRGB8888:
		*b = q[0], *g = q[1], *r = q[2];
		return true;
	case WL_SHM_FORMAT_ABGR8888:
	case WL_SHM_FORMAT_XBGR8888:
		*r = q[0], *g = q[1], *b = q[2];
		return true;
	default:
		return false;
	}
}

static void sonda_pronta(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t sa,
                         uint32_t sb, uint32_t ns)
{
	WlrPalco *p = dati;
	const uint8_t *px = p->s_pixel;
	/* ⭐ Il centro della regione, in pixel del buffer: al bordo dell'uscita la
	 *    regione e' tagliata, e il centro si sposta con lei. */
	int32_t cx = p->s_x - MAX(p->s_x - 1, 0), cy = p->s_y - MAX(p->s_y - 1, 0);
	int trovata = -1;
	uint8_t b = 0, g = 0, r = 0;

	p->s_conto.tornate++;
	if (!px) {
		sonda_prossima(p);
		return;
	}
	if (!sonda_bgr(p->s_f_shm, px, &b, &g, &r)) {
		if (!p->s_detto_formato) {
			p->s_detto_formato = true;
			registro_dice(AREA,
			              "⛔ wlroots: la sonda del puntatore riceve il formato wl_shm "
			              "0x%08x, che qui non si legge: la sonda SI SPEGNE, e il "
			              "client tiene la sua freccia",
			              p->s_f_shm);
		}
		p->s_spenta = true;
		sonda_chiudi_frame(p);
		return;
	}
	/* ⭐ Prima il centro, poi i vicini — `forma_da_pixel` e' esatto al byte,
	 *    e un vicino di un altro colore non e' mai una forma nostra. */
	for (int giro = 0; giro < 2 && trovata < 0; giro++)
		for (uint32_t y = 0; y < p->s_f_a && trovata < 0; y++)
			for (uint32_t x = 0; x < p->s_f_l && trovata < 0; x++) {
				bool centro = (int32_t)x == cx && (int32_t)y == cy;

				if (centro != (giro == 0))
					continue;
				sonda_bgr(p->s_f_shm, px + (gsize)y * p->s_f_stride + x * 4u, &b, &g,
				          &r);
				trovata = forma_da_pixel(b, g, r, 0xFF);
				if (trovata >= 0 && !centro)
					p->s_conto.dai_vicini++;
			}
	if (trovata < 0) {
		/* ⚠ Nessun colore nostro: un'applicazione che nasconde il puntatore, o
		 *   che disegna una superficie sua.  Si tiene la forma di prima. */
		p->s_conto.ignote++;
		if (!p->s_detta_ignota) {
			p->s_detta_ignota = true;
			registro_dice(AREA,
			              "⚠ wlroots: sotto il puntatore (%d,%d) nessun colore del tema "
			              "codificato: si tiene la forma di prima.  La riga non si "
			              "ripete; il conto e' nella chiusura",
			              p->s_x, p->s_y);
		}
	} else if (trovata != p->s_forma) {
		p->s_forma = trovata;
		p->s_nuova = trovata;
		p->s_conto.cambi++;
	}
	sonda_prossima(p);
}

static void sonda_fallita(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	WlrPalco *p = dati;

	p->s_conto.fallite++;
	sonda_prossima(p);
}

static void sonda_flags(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t flags) {}
static void sonda_danno(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                        uint32_t l, uint32_t a) {}
static void sonda_dmabuf(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t l, uint32_t a) {}

/* ⛔ TUTTI gli eventi hanno una funzione: `libwayland` chiama senza guardare,
 *    e un buco qui e' un salto a NULL alla prima versione che lo manda. */
static const struct zwlr_screencopy_frame_v1_listener ASCOLTO_SONDA = {
	.buffer = sonda_buffer_ev,
	.flags = sonda_flags,
	.ready = sonda_pronta,
	.failed = sonda_fallita,
	.damage = sonda_danno,
	.linux_dmabuf = sonda_dmabuf,
	.buffer_done = sonda_buffer_done,
};

static void sonda_lancia(WlrPalco *p, int32_t x, int32_t y)
{
	int32_t rx = MAX(x - 1, 0), ry = MAX(y - 1, 0);
	int32_t rl = MIN(x + 2, (int32_t)p->larghezza) - rx;
	int32_t ra = MIN(y + 2, (int32_t)p->altezza) - ry;

	if (rl <= 0 || ra <= 0)
		return;
	p->s_x = x;
	p->s_y = y;
	p->s_visto_buffer = p->s_copia_partita = false;
	p->s_frame = zwlr_screencopy_manager_v1_capture_output_region(p->manager, 1, p->uscita,
	                                                             rx, ry, rl, ra);
	if (!p->s_frame) {
		p->s_conto.fallite++;
		return;
	}
	zwlr_screencopy_frame_v1_add_listener(p->s_frame, &ASCOLTO_SONDA, p);
	p->s_conto.lanciate++;
	p->s_ultima_partita = g_get_monotonic_time();
	p->s_coda_a = p->s_ultima_partita + SONDA_CODA_US;
	/* ⭐ Subito sul filo: la pompa del flusso gira fra 8 ms, e la forma arriva
	 *    prima se la domanda parte adesso.  ⚠ EAGAIN non e' un guasto: parte
	 *    col prossimo `flush` della pompa. */
	wl_display_flush(p->display);
}

void wlr_sonda_puntatore(WlrPalco *p, uint32_t x, uint32_t y, uint32_t l, uint32_t a)
{
	int32_t ux, uy;

	if (!p || p->s_spenta || !p->manager || !p->uscita || !p->shm || l == 0 || a == 0 ||
	    p->larghezza == 0 || p->altezza == 0)
		return;
	/* ⭐ Dalla tela all'uscita, come wlroots fa col puntatore virtuale. */
	if (x >= l)
		x = l - 1;
	if (y >= a)
		y = a - 1;
	ux = (int32_t)((uint64_t)x * p->larghezza / l);
	uy = (int32_t)((uint64_t)y * p->altezza / a);
	p->s_conto.chieste++;
	p->s_coda_fatta = false;
	if (p->s_frame || (SONDA_MINIMO_US > 0 &&
	                   g_get_monotonic_time() - p->s_ultima_partita < SONDA_MINIMO_US)) {
		/* ⭐ coalescente: si ricorda solo l'ULTIMA posizione */
		p->s_in_attesa = true;
		p->s_attesa_x = ux;
		p->s_attesa_y = uy;
		return;
	}
	sonda_lancia(p, ux, uy);
}

int wlr_sonda_forma(WlrPalco *p)
{
	int nuova;

	if (!p || p->s_spenta)
		return -1;
	/* ⭐ la sonda di coda (regola 3), e quella rimasta indietro dal
	 *    diradamento: partono da qui, che il ciclo del figlio chiama sempre */
	if (!p->s_frame) {
		gint64 ora = g_get_monotonic_time();

		if (p->s_in_attesa && ora - p->s_ultima_partita >= SONDA_MINIMO_US) {
			p->s_in_attesa = false;
			sonda_lancia(p, p->s_attesa_x, p->s_attesa_y);
		} else if (!p->s_in_attesa && !p->s_coda_fatta && p->s_conto.lanciate > 0 &&
		           ora >= p->s_coda_a) {
			p->s_coda_fatta = true;
			p->s_conto.di_coda++;
			sonda_lancia(p, p->s_x, p->s_y);
		}
	}
	nuova = p->s_nuova;
	p->s_nuova = -1;
	return nuova;
}

void wlr_sonda_conteggi(const WlrPalco *p, WlrSondaConteggi *fuori)
{
	if (fuori)
		*fuori = p ? p->s_conto : (WlrSondaConteggi){ 0 };
}

/* ------------------------------------------------------------------------- */

WlrPalco *wlr_apri(GError **sbaglio)
{
	WlrPalco *p = g_new0(WlrPalco, 1);
	const char *nome = g_getenv("WAYLAND_DISPLAY");

	p->fd = -1;
	p->s_fd = -1;
	p->s_forma = p->s_nuova = -1;
	p->forza_intero = true; /* il primo giro: chi si attacca deve vedere subito */
	/* ⛔ I descrittori della scheda a -1 SUBITO: lo zero di `g_new0` è lo
	 *    standard input, e una chiusura per sbaglio lo chiuderebbe. */
	p->drm_fd = -1;
	p->lastra_del_giro = -1;
	for (unsigned i = 0; i < WLR_LASTRE; i++)
		p->lastre[i].fd = -1;
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

void wlr_forza_intero(WlrPalco *palco)
{
	if (palco)
		palco->forza_intero = true;
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

/* ------------------------------------------------------------------------- */
/* ⭐⭐ La scheda: le funzioni pubbliche. */

bool wlr_chiedi_la_scheda(WlrPalco *p, GError **sbaglio)
{
	const char *come = NULL;
	gint64 scadenza;

	g_return_val_if_fail(p != NULL, false);
	if (p->scheda)
		return true;
	if (p->scheda_nata) {
		/* ⛔ Era nata e si è spenta: non si riaccende a ogni richiesta, o un
		 *    compositore che rifiuta i DMA-BUF la farebbe spegnere e
		 *    riaccendere a ogni giro. */
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "la strada della scheda si era già spenta in questa sessione");
		return false;
	}
	if (!p->dmabuf) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "il compositore non annuncia zwp_linux_dmabuf_v1: non ho come "
		            "dargli un buffer della scheda");
		return false;
	}
	if (zwlr_screencopy_manager_v1_get_version(p->manager) < 3) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "zwlr_screencopy_manager_v1 v%u: l'evento `linux_dmabuf` arriva "
		            "dalla v3",
		            zwlr_screencopy_manager_v1_get_version(p->manager));
		return false;
	}

	/* 1 · il nodo su cui il compositore disegna — chiesto a lui (v4).
	 *     ⛔ Con tetto (difetto 3): un feedback che non chiude non ferma il
	 *     figlio, fa solo prendere il ripiego del nodo, dicendolo. */
	if (p->dmabuf_versione >= 4) {
		struct zwp_linux_dmabuf_feedback_v1 *fb =
		    zwp_linux_dmabuf_v1_get_default_feedback(p->dmabuf);

		zwp_linux_dmabuf_feedback_v1_add_listener(fb, &ASCOLTO_FEEDBACK, p);
		scadenza = g_get_monotonic_time() + 2 * G_USEC_PER_SEC;
		while (!p->feedback_finito) {
			if (!pompa(p, scadenza, sbaglio)) {
				zwp_linux_dmabuf_feedback_v1_destroy(fb);
				return false;
			}
			if (!p->feedback_finito && g_get_monotonic_time() >= scadenza)
				break;
		}
		zwp_linux_dmabuf_feedback_v1_destroy(fb);
	}
	if (p->principale_noto) {
		p->nodo = nodo_da_dispositivo(p->principale);
		come = "detto dal compositore (`main_device`)";
	}
	if (!p->nodo) {
		p->nodo = nodo_come_sessione();
		come = "⚠ NON detto dal compositore: preso con la regola di `sessione.c` "
		       "(il primo renderD* apribile), la stessa di WLR_RENDER_DRM_DEVICE";
	}
	if (!p->nodo) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun nodo /dev/dri/renderD* su cui allocare il buffer della scheda");
		return false;
	}

	/* 2 · il nodo si apre e `gbm` nasce */
	p->drm_fd = open(p->nodo, O_RDWR | O_CLOEXEC);
	if (p->drm_fd < 0) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "%s: %s", p->nodo,
		            g_strerror(errno));
		g_clear_pointer(&p->nodo, g_free);
		return false;
	}
	p->gbm = gbm_create_device(p->drm_fd);
	if (!p->gbm) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "gbm_create_device su %s non è riuscita", p->nodo);
		close(p->drm_fd);
		p->drm_fd = -1;
		g_clear_pointer(&p->nodo, g_free);
		return false;
	}
	for (unsigned i = 0; i < WLR_LASTRE; i++) {
		memset(&p->lastre[i], 0, sizeof p->lastre[i]);
		p->lastre[i].fd = -1;
	}
	/* ⚠ Se c'è già un fotogramma pendente, il suo `copy` (se partito) va in
	 *   memoria: `lastra_del_giro` resta -1 e la scheda comincia dal prossimo. */
	p->lastra_del_giro = -1;
	p->scheda_nata = true;
	p->scheda = true;
	registro_dice(AREA,
	              "⭐ wlroots: strada della SCHEDA accesa — le lastre (%d, DMA-BUF "
	              "LINEARI) si allocano su %s, %s; backend gbm «%s».  ⚠ Ogni "
	              "fotogramma dice da sé dove è finito: la strada chiesta non è la "
	              "strada presa",
	              WLR_LASTRE, p->nodo, come, gbm_device_get_backend_name(p->gbm));
	return true;
}

bool wlr_sulla_scheda(const WlrPalco *p)
{
	return p && p->scheda;
}

void wlr_rendi(WlrPalco *p, void *lastra)
{
	WlrLastra *l = lastra;

	if (!p || !l)
		return;
	/* ⛔ Il puntatore si CONTROLLA: deve essere una delle nostre lastre.  Un
	 *    fermo di un altro palco qui non tocca niente. */
	if (l < &p->lastre[0] || l >= &p->lastre[WLR_LASTRE])
		return;
	/* ⛔ Solo una lastra IN MANO torna libera: una resa due volte trova LIBERA
	 *    (o IN VOLO, se è già ripartita) e non succede niente.  ⚠ Mai una IN
	 *    VOLO: quella la chiude il suo fotogramma. */
	if (l->stato != LASTRA_IN_MANO)
		return;
	lastra_torna_libera(p, l, false);
}

void wlr_lettura_cpu(int fd, bool inizio)
{
	struct dma_buf_sync s = {
		.flags = (inizio ? DMA_BUF_SYNC_START : DMA_BUF_SYNC_END) | DMA_BUF_SYNC_READ,
	};

	if (fd < 0)
		return;
	/* ⚠ Se fallisce non c'è niente da fare di meglio che leggere lo stesso:
	 *   la lettura della CPU qui è diagnostica (il primo fotogramma), non
	 *   prodotto.  ⛔ E il giro ha un tetto: solo EINTR/EAGAIN, mai altro. */
	for (int i = 0; i < 100 && ioctl(fd, DMA_BUF_IOCTL_SYNC, &s) != 0 &&
	                (errno == EINTR || errno == EAGAIN);
	     i++)
		;
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
	/*
	 * ⛔⛔ UNA COPIA COL DANNO IN ATTESA NON FA PASSARE UNA RICHIESTA INTERA —
	 *     21 settembre 2026, `[M]` C4(xfce) «non ho potuto guardare».
	 *
	 * `wlr_forza_intero()` alza la bandiera per la copia che PARTE; ma se una
	 * copia col danno è già in volo, su uno schermo fermo non torna mai, e
	 * la copia intera non parte mai: il cliente che si attacca aspetta un
	 * fotogramma che non arriva (C4: *«il dopo non si è fatto guardare:
	 * nessun fotogramma in 8 s»*).  ⇒ Si abbandona quella in attesa — col buffer
	 * marcato, perché la copia era partita — e se ne apre una intera.
	 */
	if (palco->frame && palco->forza_intero && palco->copia_col_danno)
		chiudi_frame(palco, true);

	if (!palco->frame) {
		palco->visto_buffer = palco->visto_buffer_done = false;
		palco->pronto = palco->fallito = false;
		palco->copia_partita = palco->y_invertita = false;
		/* ⭐ la scheda: l'offerta è di QUESTO fotogramma, e la lastra pure */
		palco->offerto_scheda = false;
		palco->lastra_del_giro = -1;
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
			bool sulla_scheda = scheda_nel_giro(palco);

			/* ⚠ Prima si chiude (la lastra torna libera, sporca), POI si
			 *   conta: se il conto spegne la scheda, la lastra è già libera e
			 *   `scheda_spegni` la butta con le altre. */
			chiudi_frame(palco, false);
			palco->conteggi.falliti++;
			if (sulla_scheda && ++palco->falliti_di_fila >= WLR_SCHEDA_FALLITI_MAX)
				scheda_spegni(palco, "tre `failed` di fila del compositore sui DMA-BUF");
			return WLR_FOTOGRAMMA_FALLITO;
		}
		if (palco->pronto)
			break;
		/*
		 * L'elenco delle offerte è chiuso e la copia non è ancora partita: si
		 * sceglie la destinazione e si parte.  ⭐ Una volta sola per
		 * fotogramma — `copia_partita` sopravvive alla scadenza insieme a
		 * `frame` e a `lastra_del_giro`, quindi la chiamata che riprende un
		 * fotogramma pendente NON sceglie un'altra lastra.
		 */
		if (elenco_chiuso(palco) && !palco->copia_partita) {
			bool rotto = false;
			struct wl_buffer *dove = scheda_destinazione(palco, &rotto, sbaglio);

			if (rotto) {
				/* ⛔ Nessun `copy` è partito: chiudere il fotogramma qui non
				 *    lascia niente di sporco. */
				chiudi_frame(palco, false);
				return WLR_FOTOGRAMMA_ROTTO;
			}
			if (!dove) {
				/* la MEMORIA: di difetto, o ripiego già dichiarato */
				if (!prepara_buffer(palco, sbaglio)) {
					chiudi_frame(palco, false);
					return WLR_FOTOGRAMMA_ROTTO;
				}
				dove = palco->buffer;
			}
			/* ⭐ Col danno, se il compositore lo sa fare e nessuno ha chiesto un
			 *    fotogramma intero: vedi `forza_intero` nella struttura. */
			if (!palco->forza_intero &&
			    zwlr_screencopy_frame_v1_get_version(palco->frame) >= 2) {
				zwlr_screencopy_frame_v1_copy_with_damage(palco->frame, dove);
				palco->copia_col_danno = true;
				if (!palco->detto_il_danno) {
					palco->detto_il_danno = true;
					registro_dice(AREA,
					              "⭐ wlroots: da qui i fotogrammi si chiedono COL "
					              "DANNO — il compositore risponde solo quando lo "
					              "schermo è cambiato, come sulla spinta di GNOME e KDE");
				}
			} else {
				zwlr_screencopy_frame_v1_copy(palco->frame, dove);
				palco->forza_intero = false;
			}
			palco->copia_partita = true;
		}
		if (g_get_monotonic_time() >= scadenza) {
			/* ⭐ Scaduto, ma il fotogramma RESTA pendente: la chiamata dopo lo
			 *    riprende.  Non è un guasto e non è un fallimento.
			 * ⛔ E la lastra in volo RESTA in volo: non si sporca, non si
			 *    libera, non se ne sceglie un'altra (il riquadro in cima). */
			palco->conteggi.scaduti++;
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "il fotogramma non è ancora pronto dopo %.3f s — resta in corso",
			            attesa_s);
			return WLR_FOTOGRAMMA_SCADUTO;
		}
		if (!pompa(palco, scadenza, sbaglio)) {
			/* ⛔ Il filo è caduto: se la copia era partita, il buffer (o la
			 *    lastra) non si riusa. */
			chiudi_frame(palco, palco->copia_partita);
			return WLR_FOTOGRAMMA_ROTTO;
		}
	}

	/*
	 * ⭐ LA CONSEGNA DELLA SCHEDA: la fence, poi la lastra passa IN MANO.
	 *
	 * ⛔ Se la fence non scatta in tempo il fotogramma NON si chiude: resta
	 *    pendente con `pronto` vero e la lastra IN VOLO, e la chiamata dopo
	 *    rientra nel ciclo qui sopra, trova `pronto`, e riaspetta la stessa
	 *    fence.  Nessun blit a metà consegnato, nessuna lastra persa.
	 */
	if (scheda_nel_giro(palco)) {
		if (!scheda_aspetta_la_gpu(palco, &palco->lastre[palco->lastra_del_giro], scadenza,
		                           fuori, sbaglio)) {
			palco->conteggi.scaduti++;
			return WLR_FOTOGRAMMA_SCADUTO;
		}
		scheda_consegna(palco, fuori); /* ⚠ azzera `lastra_del_giro` */
		chiudi_frame(palco, false);
		palco->conteggi.presi++;
		palco->conteggi.sulla_scheda++;
		return WLR_FOTOGRAMMA_PRESO;
	}

	chiudi_frame(palco, false);
	palco->conteggi.presi++;
	palco->conteggi.in_memoria++;
	/* ⛔ I campi della scheda si scrivono anche qui, a vuoto: `fuori` può
	 *    venire da un giro sulla scheda, e un `fd` rimasto lì sarebbe una
	 *    lastra che non è di questo fotogramma. */
	fuori->sulla_scheda = false;
	fuori->fd = -1;
	fuori->offset = 0;
	fuori->modificatore = DRM_FORMAT_MOD_LINEAR;
	fuori->generazione = 0;
	fuori->lastra = NULL;
	fuori->us_attesa_gpu = 0;
	fuori->attesa_esplicita = false;
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
	/* ⭐ la sonda: il suo fotogramma prima del suo buffer, come il flusso */
	sonda_chiudi_frame(palco);
	if (palco->s_buffer)
		wl_buffer_destroy(palco->s_buffer);
	if (palco->s_pixel)
		munmap(palco->s_pixel, palco->s_byte);
	if (palco->s_fd >= 0)
		close(palco->s_fd);
	if (palco->buffer)
		wl_buffer_destroy(palco->buffer);
	if (palco->pixel)
		munmap(palco->pixel, palco->byte);
	if (palco->fd >= 0)
		close(palco->fd);
	/* ⭐ le lastre, `gbm`, il nodo — DOPO il fotogramma, che poteva nominarne
	 *    una in un `copy` */
	scheda_chiudi(palco);
	if (palco->dmabuf)
		zwp_linux_dmabuf_v1_destroy(palco->dmabuf);
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
