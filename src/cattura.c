/*
 * cattura.c — vedi cattura.h per il mandato e per le tre regole.
 */
#include "cattura.h"

#include <gio/gio.h> /* solo per il dominio d'errore G_IO_ERROR: qui non si parla al bus */
#include <pipewire/pipewire.h>
#include <spa/buffer/meta.h>
#include <spa/param/video/format-utils.h>
#include <spa/utils/result.h>
#include <drm_fourcc.h>
#include <string.h>

#include "cursore.h"
#include "registro.h"

#define AREA "cattura"

/* Quanto si aspetta che il flusso arrivi a `paused`: e' il momento in cui la
 * negoziazione del formato e' avvenuta e si sa se il compositore ha accettato
 * quel che si e' chiesto.  ⛔ Senza questa attesa un rifiuto — «no more input
 * formats» — sarebbe silenzioso, e si manifesterebbe molto piu' tardi come
 * schermo nero. */
#define ATTESA_AVVIO_S 10

/* Quante regioni danneggiate si portano al massimo.  Oltre, si dichiara che il
 * fotogramma vale tutto: e' il caso sicuro. */
#define REGIONI_MAX 16

#define FD_MAX 8

/*
 * Quanti byte deve avere il metadato del cursore per portare una bitmap di
 * `l x a`.  ⛔ E' la stessa formula di Mutter (`CURSOR_META_SIZE`,
 * `meta-screen-cast-stream-src.c:63`) e sta qui perche' e' una grandezza della
 * NEGOZIAZIONE PipeWire, non del filo: il tetto del filo e' 256 e sta in
 * `cursore.h`.
 */
#define CURSORE_META_BYTE(l, a)                                                                    \
	((int) (sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) + (l) * (a) * 4))

struct Cattura
{
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;

	struct spa_video_info_raw formato;
	gboolean formato_noto;

	CatturaFotogramma su_fotogramma;
	CatturaFine su_fine;
	gpointer dati;

	enum pw_stream_state stato;
	char *guasto;
	gboolean fine_segnalata;
	gboolean detto_il_tipo;

	CatturaStrada strada;
	CatturaColore colore;
	uint32_t chiesta_larghezza, chiesta_altezza;
	/* ⛔ La cadenza CHIESTA all'avvio, tenuta perche' `cattura_ridimensiona()`
	 *    rifa' la stessa proposta: rimetterne una scritta a mano la' dentro
	 *    vorrebbe dire che dopo un ridimensionamento il flusso gira a una cadenza
	 *    diversa da quella con cui e' nato — e nessuna riga lo direbbe. */
	uint32_t chiesti_al_secondo;
	/* ⛔ Che la misura NEGOZIATA sia diversa da quella CHIESTA.  Si dice una
	 *    volta sola e si tiene, perche' il richiamo del formato gira piu' volte.
	 * ⚠ Vive perche' la tela sta per smettere di essere una costante
	 *   (`DECISIONI.md` §5.0-sexies): finche' si chiedeva sempre 1920x1080 una
	 *   divergenza non poteva capitare, e infatti nessuno la guardava. */
	gboolean misura_divergente;

	/* --- i conteggi, che girano sul thread di tempo reale --------------- *
	 * ⚠ SI CONTANO, NON SI STAMPANO: una riga di registro per fotogramma
	 *   falserebbe la cosa che si sta guardando.  Si dice il primo, e poi un
	 *   riassunto ogni trecento. */
	CatturaConteggi conto;
	int fd_visti[FD_MAX];
	uint32_t primo_tipo_grezzo; /* il valore SPA, per chi vuole il numero nudo */

	/* --- il posto di chi aspetta un fotogramma -------------------------- *
	 * ⛔ Il posto esiste solo mentre qualcuno aspetta: un fotogramma che arriva
	 *    quando nessuno lo vuole si conta e basta.  Copiare 8 MB per nessuno
	 *    sarebbe lavoro dentro la richiamata di tempo reale, fatto per niente. */
	GMutex lucchetto;
	GCond novita;
	gboolean qualcuno_aspetta;
	CatturaFermo posto;
	gboolean posto_pieno;

	/* --- ⭐ IL CANALE DEL CURSORE ---------------------------------------- *
	 *
	 * ⛔ `cattura.c` NON conosce il filo: legge il metadato grezzo e lo passa a
	 *    `cursore.c`, che e' il solo posto in cui la forma diventa una
	 *    `CursoreForma` (vedi `cursore.h`).
	 *
	 * ⚠ Il modulo esiste sempre, anche se nessuno ascolta: cosi' i conteggi
	 *   dicono se il metadato arriva DAVVERO, indipendentemente dal fatto che
	 *   qualcuno lo consumi.  Chi ascolta si registra dopo, con
	 *   `cattura_cursore`, e i due campi si leggono sotto il lucchetto perche'
	 *   chi si registra sta su un altro thread. */
	Cursore *cursore;
	CursoreArrivata cursore_fn;
	void *cursore_chi;
	gboolean detto_il_cursore; /* il primo metadato si dice una volta */
};

/* ------------------------------------------------------------------ *
 *  I nomi — un posto solo, perche' chi scrive un manifesto non li reinventi
 * ------------------------------------------------------------------ */

const char *cattura_buffer_nome(CatturaBuffer buffer)
{
	switch (buffer)
	{
	case CATTURA_BUFFER_MEMFD: return "MemFd";
	case CATTURA_BUFFER_MEMPTR: return "MemPtr";
	case CATTURA_BUFFER_MEMID: return "MemId";
	case CATTURA_BUFFER_DMABUF: return "DMA-BUF";
	default: return "IGNOTO";
	}
}

static CatturaBuffer buffer_da_spa(uint32_t tipo)
{
	switch (tipo)
	{
	case SPA_DATA_MemFd: return CATTURA_BUFFER_MEMFD;
	case SPA_DATA_MemPtr: return CATTURA_BUFFER_MEMPTR;
	case SPA_DATA_MemId: return CATTURA_BUFFER_MEMID;
	case SPA_DATA_DmaBuf: return CATTURA_BUFFER_DMABUF;
	default: return CATTURA_BUFFER_IGNOTO;
	}
}

const char *cattura_colore_nome(uint32_t formato_grezzo)
{
	switch (formato_grezzo)
	{
	case SPA_VIDEO_FORMAT_BGRx: return "BGRx";
	case SPA_VIDEO_FORMAT_BGRA: return "BGRA";
	case SPA_VIDEO_FORMAT_RGBx: return "RGBx";
	case SPA_VIDEO_FORMAT_RGBA: return "RGBA";
	case SPA_VIDEO_FORMAT_xRGB: return "xRGB";
	case SPA_VIDEO_FORMAT_ARGB: return "ARGB";
	case SPA_VIDEO_FORMAT_xRGB_210LE: return "xRGB_210LE";
	case SPA_VIDEO_FORMAT_xBGR_210LE: return "xBGR_210LE";
	case SPA_VIDEO_FORMAT_ARGB_210LE: return "ARGB_210LE";
	case SPA_VIDEO_FORMAT_ABGR_210LE: return "ABGR_210LE";
	default: return "ALTRO";
	}
}

const char *cattura_fonte_nome(CatturaFonte fonte)
{
	switch (fonte)
	{
	case CATTURA_FONTE_PRODUTTORE: return "chiesto al produttore (SPA_PARAM_Format)";
	case CATTURA_FONTE_FORMATO: return "discende dal formato negoziato";
	case CATTURA_FONTE_MISURATA: return "[M] misurato da noi sui pixel consegnati";
	default: return "NON DICHIARATO dal produttore";
	}
}

/*
 * ⛔ I QUATTRO `UNKNOWN` DI SPA SONO UNA RISPOSTA, NON UN SILENZIO DA RIEMPIRE.
 *
 * `[M]` 12 agosto 2026: su Mutter 48.7 il flusso di cattura consegna **zero** in
 * tutti e quattro i campi (`color_range`, `color_matrix`, `transfer_function`,
 * `color_primaries`).  Chi li riempisse con quel che si aspetta starebbe
 * deducendo, ed e' la forma E8.
 */
const char *cattura_range_nome(uint32_t grezzo)
{
	switch (grezzo)
	{
	case 1: return "PIENO (0-255)";
	case 2: return "LIMITATO (16-235)";
	default: return "NON DICHIARATO dal produttore";
	}
}

const char *cattura_matrice_nome(uint32_t grezzo)
{
	switch (grezzo)
	{
	case 1: return "RGB (nessuna conversione: i pixel sono RGB)";
	case 2: return "FCC";
	case 3: return "BT.709";
	case 4: return "BT.601";
	case 5: return "SMPTE240M";
	case 6: return "BT.2020";
	default: return "NON DICHIARATA dal produttore";
	}
}

const char *cattura_trasferimento_nome(uint32_t grezzo)
{
	switch (grezzo)
	{
	case 1: return "gamma 1.0 (lineare)";
	case 4: return "gamma 2.2";
	case 5: return "BT.709";
	case 7: return "sRGB";
	case 11: return "BT.2020 12 bit";
	default: return "NON DICHIARATA dal produttore";
	}
}

const char *cattura_primari_nome(uint32_t grezzo)
{
	switch (grezzo)
	{
	case 1: return "BT.709";
	case 4: return "SMPTE170M";
	case 7: return "BT.2020";
	default: return "NON DICHIARATI dal produttore";
	}
}

const char *cattura_range_misurato_nome(CatturaRangeMisurato misurato)
{
	switch (misurato)
	{
	case CATTURA_RANGE_COMPATIBILE_PIENO:
		return "[M] i pixel toccano 0 e 255: compatibile con il PIENO";
	case CATTURA_RANGE_NON_CONCLUSIVO:
		return "[M] i pixel non toccano gli estremi: NON CONCLUSIVO — dipende dalla scena, "
		       "e non prova un range limitato";
	default:
		return "non misurato";
	}
}

/*
 * I bit per canale si ricavano dal FORMATO, che e' un fatto del produttore.
 *
 * ⛔ E se arrivasse un formato che non conosciamo si risponde 0 e lo si dichiara:
 *    un numero inventato qui diventerebbe «dieci bit veri» in una tabella di
 *    F2.3, e nessuno risalirebbe fin qui a cercarlo.
 */
static int bit_per_canale(uint32_t formato)
{
	switch (formato)
	{
	case SPA_VIDEO_FORMAT_BGRx:
	case SPA_VIDEO_FORMAT_BGRA:
	case SPA_VIDEO_FORMAT_RGBx:
	case SPA_VIDEO_FORMAT_RGBA:
	case SPA_VIDEO_FORMAT_xRGB:
	case SPA_VIDEO_FORMAT_ARGB:
		return 8;
	case SPA_VIDEO_FORMAT_xRGB_210LE:
	case SPA_VIDEO_FORMAT_xBGR_210LE:
	case SPA_VIDEO_FORMAT_ARGB_210LE:
	case SPA_VIDEO_FORMAT_ABGR_210LE:
	case SPA_VIDEO_FORMAT_RGBx_102LE:
	case SPA_VIDEO_FORMAT_BGRx_102LE:
	case SPA_VIDEO_FORMAT_RGBA_102LE:
	case SPA_VIDEO_FORMAT_BGRA_102LE:
		return 10;
	default:
		return 0;
	}
}

/* L'ordine dei byte, per sapere dove stanno R, G e B quando si misura il range.
 * ⛔ Vale solo per i formati a 8 bit con quattro byte per pixel: sugli altri si
 *    risponde FALSE e la misura NON si fa, invece di farla sui byte sbagliati. */
static gboolean posizioni_rgb(uint32_t formato, int *r, int *g, int *b)
{
	switch (formato)
	{
	case SPA_VIDEO_FORMAT_BGRx:
	case SPA_VIDEO_FORMAT_BGRA:
		*b = 0; *g = 1; *r = 2; return TRUE;
	case SPA_VIDEO_FORMAT_RGBx:
	case SPA_VIDEO_FORMAT_RGBA:
		*r = 0; *g = 1; *b = 2; return TRUE;
	case SPA_VIDEO_FORMAT_xRGB:
	case SPA_VIDEO_FORMAT_ARGB:
		*r = 1; *g = 2; *b = 3; return TRUE;
	default:
		return FALSE;
	}
}

/* ------------------------------------------------------------------ *
 *  Le richiamate di PipeWire
 * ------------------------------------------------------------------ */

static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	Cattura *cattura = dati;

	registro_dettaglio(AREA, "stato del flusso: %s → %s%s%s", pw_stream_state_as_string(vecchio),
	                   pw_stream_state_as_string(nuovo), errore ? " — " : "", errore ? errore : "");
	cattura->stato = nuovo;
	if (errore)
	{
		g_free(cattura->guasto);
		cattura->guasto = g_strdup(errore);
	}

	/*
	 * Il consumatore deve accorgersi da se' quando il flusso si stacca, e la
	 * condizione sullo stato VECCHIO non e' un dettaglio: all'avvio si parte da
	 * `unconnected`, e segnalare la fine li' sarebbe finire prima di cominciare.
	 *
	 * Senza questo, un «Esci» dal menu di sistema lascerebbe il client attaccato
	 * a un'immagine congelata: chi guarda non distinguerebbe «desktop fermo» da
	 * «non c'e' piu' niente da catturare».
	 */
	if ((vecchio == PW_STREAM_STATE_PAUSED || vecchio == PW_STREAM_STATE_STREAMING) &&
	    nuovo == PW_STREAM_STATE_UNCONNECTED && !cattura->fine_segnalata)
	{
		cattura->fine_segnalata = TRUE;
		registro_dice(AREA, "il flusso di cattura si e' staccato");
		if (cattura->su_fine)
			cattura->su_fine(cattura->dati);
	}

	/* Chi aspetta un fotogramma deve svegliarsi anche quando il flusso muore, o
	 * aspetterebbe per tutta l'attesa un fotogramma che non puo' piu' arrivare. */
	g_mutex_lock(&cattura->lucchetto);
	g_cond_broadcast(&cattura->novita);
	g_mutex_unlock(&cattura->lucchetto);

	pw_thread_loop_signal(cattura->ciclo, false);
}

/*
 * ⛔ IL RIMBALZO VERSO CHI ASCOLTA, e non e' una comodita': `cursore_apri` vuole
 *    il destinatario al momento dell'apertura, ma il flusso parte prima che
 *    qualcuno si registri.  Senza rimbalzo la prima forma — quella che arriva
 *    con il primo movimento del puntatore — non avrebbe dove andare.
 *
 * ⚠ Gira sul thread di tempo reale di PipeWire: chi si registra qui non deve
 *   aspettare niente (`cattura.h`, il riquadro del ciclo).
 */
static int cursore_rimbalzo(void *chi, const CursoreForma *forma)
{
	Cattura *cattura = chi;
	CursoreArrivata fn;
	void *dove;

	g_mutex_lock(&cattura->lucchetto);
	fn = cattura->cursore_fn;
	dove = cattura->cursore_chi;
	g_mutex_unlock(&cattura->lucchetto);

	/* ⛔ Nessuno ascolta NON e' un errore: la forma si e' comunque contata, ed
	 *    e' precisamente il caso in cui il banco misura la sorgente senza il
	 *    filo. */
	if (!fn)
		return 0;
	return fn(dove, forma);
}

/*
 * ⛔⭐ I QUATTRO PARAMETRI DI CONSUMO — IN UN POSTO SOLO, e la ragione e' un
 *     difetto trovato refutando, il 15 agosto 2026.
 *
 * `pw_stream_update_params()` NON aggiunge: **sostituisce l'intera lista**.  ⇒
 * Chi rinegozia il formato passando il solo `EnumFormat` cancella `ParamBuffers`
 * e i tre `ParamMeta` — fra cui quello del CURSORE, aggiunto il 14 agosto
 * proprio perche' senza «`CURSORE_FORMA` era un canale senza sorgente».
 *
 * ⚠ Nel caso sano la richiamata del formato li rimette subito.  ⛔ Ma il caso
 *   che `cattura.h` documenta come misurato — «il compositore risponde
 *   *riuscito* e non manda nessun evento» — quella richiamata non la fa girare,
 *   e la dichiarazione resterebbe vuota.  ⇒ Si ripetono TUTTI, sempre, da un
 *   posto solo: due elenchi che devono restare uguali sono due elenchi che
 *   divergono.
 */
static uint32_t parametri_di_consumo(Cattura *cattura, struct spa_pod_builder *costruttore,
                                     const struct spa_pod *parametri[4])
{
	/*
	 * ⛔ IL TIPO DEI DATI SI CONCORDA QUI, non nel formato: chi tace lascia il
	 *    predefinito, che e' la memoria ordinaria.  E' la seconda meta' della
	 *    regola 2 di `cattura.h` — dichiararne uno solo fa riuscire la
	 *    negoziazione con dentro il contrario di quel che si voleva.
	 *
	 * ⛔ E il bit del DMA-BUF si accende SOLO se e' quella la strada chiesta.
	 *    Lasciarlo acceso «per sicurezza» significherebbe lasciare al compositore
	 *    la facolta' di consegnare descrittori che in memoria nessuno guarda:
	 *    ogni fotogramma scartato in silenzio, e nessun errore.
	 */
	int tipi = (1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr);
	if (cattura->strada == CATTURA_STRADA_SCHEDA)
		tipi = (1 << SPA_DATA_DmaBuf);

	parametri[0] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(tipi));

	/*
	 * ⛔ I METADATI SI CHIEDONO, O NON ARRIVANO — e senza di loro il produttore
	 *    non ha modo di dirci nulla del fotogramma: ne' quale sia (`seq`), ne'
	 *    quanta parte abbia ridipinto (`VideoDamage`).
	 *
	 * ⚠ Chiedere un metadato NON obbliga il produttore a darlo: chi legge deve
	 *   reggere la sua assenza, e per questo ogni lettura controlla il puntatore
	 *   e conta le assenze invece di darle per zero.
	 */
	parametri[1] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Header), SPA_PARAM_META_size,
	    SPA_POD_Int(sizeof(struct spa_meta_header)));
	parametri[2] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_VideoDamage), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(sizeof(struct spa_meta_region) * 4,
	                             sizeof(struct spa_meta_region) * 1,
	                             sizeof(struct spa_meta_region) * 16));

	/*
	 * ⭐⭐ IL METADATO DEL CURSORE — e fino al 14 agosto 2026 non si chiedeva.
	 *
	 * ⛔ Il difetto che questa richiesta cura, `gnome.md` §1.1 punto 6 e §5.2:
	 *    a `RecordVirtual` chiediamo `cursor-mode = 2` (`src/mutter.c:439`), cioe'
	 *    «il cursore dammelo come METADATO invece che nei pixel» — e Mutter
	 *    obbedisce in tutt'e due i versi: toglie il puntatore dall'immagine
	 *    (`inhibit_cursor_overlay`) **e** lo mette nel metadato.  ⛔ Ma il
	 *    metadato, come ogni metadato, arriva solo a chi lo chiede: senza questa
	 *    riga si otteneva il PRIMO verso e non il secondo, cioe' nessun cursore
	 *    da nessuna parte.
	 *
	 * ⚠ LA MISURA E' UN INTERVALLO, e i tre numeri sono quelli del client di
	 *   prova di Mutter (`src/tests/remote-desktop-utils.c:218-225`): il metadato
	 *   deve poter contenere `spa_meta_cursor` + `spa_meta_bitmap` + i pixel, e
	 *   chiedendone uno FISSO troppo piccolo il produttore taglierebbe la
	 *   bitmap.  Mutter offre 384x384 (`CURSOR_META_SIZE(384, 384)`).
	 *
	 * ⛔ E 384 > 256, che e' il tetto di `RCP.md` §7.2: il taglio lo fa
	 *    `cursore.c`, DICHIARANDOLO, perche' il posto in cui i limiti del filo si
	 *    fanno rispettare e' uno solo.
	 */
	parametri[3] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Cursor), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(CURSORE_META_BYTE(384, 384), CURSORE_META_BYTE(1, 1),
	                             CURSORE_META_BYTE(384, 384)));
	return 4;
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Cattura *cattura = dati;
	uint32_t tipo, sottotipo;
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[4];

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &tipo, &sottotipo) < 0)
		return;
	if (tipo != SPA_MEDIA_TYPE_video || sottotipo != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &cattura->formato) < 0)
	{
		registro_dice(AREA, "⚠ formato di cattura non interpretabile");
		return;
	}

	cattura->formato_noto = TRUE;
	registro_dice(AREA, "formato negoziato: %ux%u %s (%d bit per canale), modificatore 0x%" G_GINT64_MODIFIER "x",
	              cattura->formato.size.width, cattura->formato.size.height,
	              cattura_colore_nome(cattura->formato.format),
	              bit_per_canale(cattura->formato.format), (guint64) cattura->formato.modifier);

	/* ⛔⛔ LA GUARDIA: chiesto contro concesso.
	 *
	 * ⚠ Fino al 14 agosto 2026 questa riga non c'era, e la riga di registro qui
	 *   sopra diceva la misura negoziata **senza confrontarla con niente**: chi
	 *   la leggeva vedeva un numero e non aveva modo di sapere se fosse quello
	 *   chiesto.  ⛔ Con la tela a 1920x1080 fissa la divergenza non poteva
	 *   capitare; `DECISIONI.md` §5.0-sexies la rende POSSIBILE, ed e' per
	 *   questo che la guardia nasce insieme a quella decisione e non dopo.
	 *
	 * ⛔ E il danno che previene non e' un'immagine storta: e' che il puntatore
	 *   finisca ALTROVE.  Se il compositore concede una misura diversa e nessuno
	 *   lo dice, la conversione delle coordinate nasce sbagliata e il sintomo —
	 *   misurato per due giorni su Samsung DeX — e' «il mouse ha problemi con le
	 *   coordinate degli elementi».  ⇒ Un difetto che si dichiara costa un
	 *   minuto; uno che tace e' costato una settimana.
	 *
	 * ⚠ Si DICE e non si chiude la sessione: chi sceglie che farne e' il
	 *   chiamante, che sa se puo' ancora servire il client (`CODER.md` §4.2 — un
	 *   ripiego silenzioso produce due comportamenti sotto la stessa etichetta). */
	if (cattura->chiesta_larghezza && cattura->chiesta_altezza
	    && (cattura->formato.size.width != cattura->chiesta_larghezza
	        || cattura->formato.size.height != cattura->chiesta_altezza))
	{
		if (!cattura->misura_divergente)
			registro_dice(AREA,
			              "⛔ MISURA DIVERGENTE: chiesti %ux%u, concessi %ux%u — la "
			              "conversione delle coordinate nasce sbagliata e il puntatore "
			              "andra' altrove (`DECISIONI.md` §5.0-sexies)",
			              cattura->chiesta_larghezza, cattura->chiesta_altezza,
			              cattura->formato.size.width, cattura->formato.size.height);
		cattura->misura_divergente = TRUE;
	}
	else
		cattura->misura_divergente = FALSE;

	/* ⛔ E i quattro parametri di consumo li scrive `parametri_di_consumo()`, in
	 *    un posto solo: li ripete anche `cattura_ridimensiona()`, e due elenchi
	 *    che devono restare uguali sono due elenchi che divergono. */
	pw_stream_update_params(cattura->flusso, parametri,
	                        parametri_di_consumo(cattura, &costruttore, parametri));
	pw_thread_loop_signal(cattura->ciclo, false);
}

/*
 * ⭐ Il metadato del cursore, letto e consegnato a `cursore.c`.
 *
 * ⛔ SI LEGGE PRIMA DI OGNI `goto restituisci`, e la ragione era gia' scritta
 *    nel riquadro di `su_processo`: un buffer marcato `CORRUPTED` e' un buffer
 *    SENZA fotogramma, spedito **proprio perche'** il cursore si e' mosso.  Chi
 *    leggesse il cursore dopo lo scarto perderebbe esattamente i buffer che il
 *    cursore li' dentro ce l'hanno.
 *
 * ⚠ E si guarda `spa_meta` e non `spa_buffer_find_meta_data`: serve la
 *   DIMENSIONE vera del metadato, o i controlli di `cursore.c` non hanno un
 *   limite contro cui misurare i pixel della bitmap.
 */
static void guarda_cursore(Cattura *cattura, struct pw_buffer *pacco)
{
	struct spa_meta *meta;

	if (!cattura->cursore)
		return;

	meta = spa_buffer_find_meta(pacco->buffer, SPA_META_Cursor);
	if (!meta || !meta->data)
	{
		/* ⛔ «Non pervenuto» NON e' «nascosto»: si conta, e non si manda
		 *    niente sul filo.  Chi legge zero `CURSORE_FORMA` piu' tardi deve
		 *    poter distinguere «il puntatore non c'era» da «il metadato non
		 *    l'abbiamo chiesto, o il produttore non l'ha dato». */
		cattura->conto.cursore_assente++;
		return;
	}

	cattura->conto.cursore_metadati++;
	if (!cattura->detto_il_cursore)
	{
		cattura->detto_il_cursore = TRUE;
		registro_dice(AREA, "⭐ il metadato del cursore ARRIVA: %u byte per buffer", meta->size);
	}

	if (cursore_metadato(cattura->cursore, meta->data, meta->size) < 0)
		cattura->conto.cursore_malformati++;
}

/* Il danno: si guarda, si conta, e si consegna come INFORMAZIONE. */
static gboolean guarda_danno(Cattura *cattura, struct pw_buffer *pacco, CatturaRegione *regioni,
                             guint *quante, gboolean *copre_tutto)
{
	struct spa_meta *meta = spa_buffer_find_meta(pacco->buffer, SPA_META_VideoDamage);
	struct spa_meta_region *regione;
	gboolean vista = FALSE;

	*quante = 0;
	*copre_tutto = FALSE;

	if (!meta)
	{
		cattura->conto.danno_assente++;
		return FALSE;
	}
	spa_meta_for_each(regione, meta)
	{
		if (!spa_meta_region_is_valid(regione))
			break;
		vista = TRUE;
		if (regione->region.position.x == 0 && regione->region.position.y == 0 &&
		    regione->region.size.width >= cattura->formato.size.width &&
		    regione->region.size.height >= cattura->formato.size.height)
			*copre_tutto = TRUE;
		if (*quante < REGIONI_MAX)
		{
			regioni[*quante].x = (uint32_t) MAX(0, regione->region.position.x);
			regioni[*quante].y = (uint32_t) MAX(0, regione->region.position.y);
			regioni[*quante].larghezza = regione->region.size.width;
			regioni[*quante].altezza = regione->region.size.height;
			(*quante)++;
		}
		else
		{
			/* Si sbaglia dalla parte sicura: piu' regioni di quante se ne portano
			 * ⇒ si dichiara «vale tutto» invece di consegnarne una parte. */
			*quante = 0;
			*copre_tutto = TRUE;
			break;
		}
	}
	if (!vista)
	{
		cattura->conto.danno_assente++;
		return FALSE;
	}
	if (*copre_tutto)
		cattura->conto.danno_pieno++;
	else
		cattura->conto.danno_parziale++;
	return TRUE;
}

static void su_processo(void *dati)
{
	Cattura *cattura = dati;
	struct pw_buffer *pacco;
	struct spa_data *piano;
	struct spa_meta_header *intestazione;
	CatturaRegione regioni[REGIONI_MAX];
	CatturaFotogrammaInfo info = { 0 };
	CatturaConsegna consegna;
	guint quante = 0;
	gboolean copre_tutto = FALSE, danno_dichiarato;
	uint32_t passo, offset;
	guint64 disponibili, byte;
	guint i;
	gboolean noto;

	pacco = pw_stream_dequeue_buffer(cattura->flusso);
	if (!pacco)
		return;

	/* ⛔ PRIMA DI OGNI SCARTO: vedi il riquadro di `guarda_cursore`. */
	guarda_cursore(cattura, pacco);

	if (pacco->buffer->n_datas == 0)
		goto restituisci;
	piano = &pacco->buffer->datas[0];
	cattura->conto.arrivati++;

	/* Quanti buffer distinti ricicla il produttore: Mutter ne usa quattro, e
	 * saperlo serve a leggere il resto. */
	noto = FALSE;
	for (i = 0; i < cattura->conto.buffer_distinti; i++)
		if (cattura->fd_visti[i] == (int) piano->fd)
			noto = TRUE;
	if (!noto && cattura->conto.buffer_distinti < FD_MAX)
		cattura->fd_visti[cattura->conto.buffer_distinti++] = (int) piano->fd;

	/* ⛔ I TIPI SI COLLEZIONANO TUTTI, non si tiene solo l'ultimo: se il
	 *    produttore cambiasse strada a meta' giro, una riga sola direbbe una
	 *    strada per due popolazioni diverse — che e' la forma E2. */
	noto = FALSE;
	for (i = 0; i < cattura->conto.quanti_tipi; i++)
		if (cattura->conto.tipi_visti[i] == buffer_da_spa(piano->type))
			noto = TRUE;
	if (!noto && cattura->conto.quanti_tipi < G_N_ELEMENTS(cattura->conto.tipi_visti))
	{
		if (cattura->conto.quanti_tipi == 0)
			cattura->primo_tipo_grezzo = piano->type;
		cattura->conto.tipi_visti[cattura->conto.quanti_tipi++] = buffer_da_spa(piano->type);
	}

	if (!cattura->detto_il_tipo)
	{
		cattura->detto_il_tipo = TRUE;
		/* ⛔ Detto UNA volta e per esteso, con accanto quel che NON dimostra. */
		registro_dice(AREA,
		              "i fotogrammi arrivano come %s (%u piani) — ⚠ e questo NON dice dove "
		              "Mutter renda: e' la risposta a quel che abbiamo chiesto noi (E1)",
		              cattura_buffer_nome(buffer_da_spa(piano->type)), pacco->buffer->n_datas);
	}

	if (!piano->chunk)
	{
		cattura->conto.senza_pixel++;
		goto restituisci;
	}

	/*
	 * ⛔ IL BUFFER PUO' NON CONTENERE UN FOTOGRAMMA, E LO DICE UN SOLO BIT.
	 *
	 *    Con il cursore in modo METADATO — che e' il modo giusto, perche' il
	 *    puntatore ha un canale suo — un movimento del mouse produce un buffer
	 *    senza disegno: dentro ci sono i pixel stantii di due-quattro fotogrammi
	 *    prima, e l'unica indicazione e' `SPA_CHUNK_FLAG_CORRUPTED`, che li'
	 *    significa «non guardare il contenuto».  ⛔ `gnome.md` §8.3: i buffer di
	 *    solo cursore stantii **esistono anche su Mutter**.
	 *
	 * ⚠ Si scarta il FOTOGRAMMA, non il buffer: il metadato del cursore che
	 *   viaggia insieme resta valido, ed e' anzi l'unica cosa per cui quel buffer
	 *   e' stato spedito.  Quando il canale del puntatore ci sara', si leggera'
	 *   qui.
	 */
	if (piano->chunk->flags & SPA_CHUNK_FLAG_CORRUPTED)
	{
		cattura->conto.solo_cursore++;
		goto restituisci;
	}
	intestazione = spa_buffer_find_meta_data(pacco->buffer, SPA_META_Header, sizeof *intestazione);
	if (!intestazione)
		cattura->conto.senza_intestazione++;
	else if (intestazione->flags & SPA_META_HEADER_FLAG_CORRUPTED)
	{
		cattura->conto.solo_cursore++;
		goto restituisci;
	}

	danno_dichiarato = guarda_danno(cattura, pacco, regioni, &quante, &copre_tutto);

	/* ⛔ Lo stride autorevole e' questo, e se non c'e' non se ne calcola uno. */
	passo = (uint32_t) MAX(0, piano->chunk->stride);
	if (passo == 0)
	{
		cattura->conto.stride_zero++;
		goto restituisci;
	}
	offset = (uint32_t) piano->chunk->offset;

	/* --- i quattro fatti, congelati per questo fotogramma ---------------- */
	memset(&consegna, 0, sizeof consegna);
	consegna.noto = cattura->formato_noto;
	consegna.strada_chiesta = cattura->strada;
	consegna.buffer_chiesto =
	    cattura->strada == CATTURA_STRADA_SCHEDA ? CATTURA_BUFFER_DMABUF : CATTURA_BUFFER_MEMFD;
	consegna.buffer_dichiarato = buffer_da_spa(piano->type);
	consegna.buffer_dichiarato_grezzo = piano->type;
	consegna.buffer_distinti = cattura->conto.buffer_distinti;
	consegna.formato_grezzo = cattura->formato.format;
	consegna.formato = cattura_colore_nome(cattura->formato.format);
	consegna.bit_per_canale = bit_per_canale(cattura->formato.format);
	consegna.fonte_bit = consegna.bit_per_canale > 0 ? CATTURA_FONTE_FORMATO
	                                                 : CATTURA_FONTE_NON_DICHIARATA;
	consegna.larghezza = cattura->formato.size.width;
	consegna.altezza = cattura->formato.size.height;
	consegna.stride = passo;
	consegna.stride_letto = TRUE;
	consegna.byte = (guint64) passo * cattura->formato.size.height;
	consegna.modificatore = cattura->formato.modifier;
	consegna.range_grezzo = cattura->formato.color_range;
	consegna.matrice_grezza = cattura->formato.color_matrix;
	consegna.trasferimento_grezzo = cattura->formato.transfer_function;
	consegna.primari_grezzi = cattura->formato.color_primaries;
	consegna.fonte_range =
	    cattura->formato.color_range ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;
	consegna.fonte_matrice =
	    cattura->formato.color_matrix ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;

	/* --- quanti byte ci sono davvero ------------------------------------ */
	disponibili = piano->maxsize > offset ? (guint64) piano->maxsize - offset : 0;
	byte = piano->chunk->size > 0 ? (guint64) piano->chunk->size : disponibili;
	if (byte > disponibili)
		byte = disponibili;

	/* ⛔⛔ LA GEOMETRIA DICHIARATA DEVE STARE DENTRO I BYTE CONSEGNATI — la
	 *     guardia nata refutando, la notte del 15 agosto 2026, e prima non
	 *     serviva a niente.
	 *
	 * ⚠ La misura viene dal FORMATO negoziato (`cattura->formato`), il passo e i
	 *   byte vengono dal CHUNK del buffer vero: due fonti, e fra una
	 *   rinegoziazione e i buffer nuovi possono appartenere a due generazioni
	 *   diverse.  ⛔ Con la tela fissa non potevano divergere;
	 *   `cattura_ridimensiona()` lo rende possibile.
	 *
	 * ⛔ E il danno non e' un'immagine storta: chi consuma legge
	 *   `larghezza x 4` byte per riga, per `altezza` righe.  Se il passo e' piu'
	 *   corto della larghezza dichiarata — cioe' nel verso «la tela si ALLARGA» —
	 *   l'ultima riga finisce **oltre la memoria copiata**, e il figlio muore
	 *   portandosi via il palco di un utente.
	 *
	 * ⇒ Si scarta e SI CONTA, che e' la stessa regola dello `stride == 0`: un
	 *   fotogramma in meno costa 16 ms, una lettura fuori dai limiti costa il
	 *   processo. */
	/* ⚠ Solo sulla strada della MEMORIA: sul DMA-BUF i pixel non sono qui — c'e'
	 *   un descrittore che vive sulla scheda — e `chunk->size` non descrive
	 *   nessuna copia da leggere.  Applicare la guardia anche li' scarterebbe
	 *   ogni fotogramma della scheda in silenzio, che e' il difetto opposto. */
	if (cattura->strada == CATTURA_STRADA_MEMORIA
	    && (cattura->formato.size.width == 0 || cattura->formato.size.height == 0
	        || passo < cattura->formato.size.width * 4u
	        || byte < (guint64) passo * cattura->formato.size.height))
	{
		cattura->conto.geometria_incoerente++;
		if (cattura->conto.geometria_incoerente == 1)
			registro_dice(AREA,
			              "⛔ fotogramma SCARTATO: il formato dichiara %ux%u ma il buffer "
			              "porta passo %u e %" G_GUINT64_FORMAT " byte (ne servirebbero %"
			              G_GUINT64_FORMAT ").  ⚠ E' la finestra fra una rinegoziazione e "
			              "i buffer nuovi: chi legge andrebbe oltre la memoria consegnata",
			              cattura->formato.size.width, cattura->formato.size.height, passo,
			              byte, (guint64) passo * cattura->formato.size.height);
		goto restituisci;
	}

	info.pixel = NULL;
	info.byte = byte;
	info.fd = piano->fd >= 0 ? (int) piano->fd : -1;
	info.offset = offset;
	info.stride = passo;
	info.seq = intestazione ? (uint64_t) intestazione->seq : 0;
	info.pts = intestazione ? (int64_t) intestazione->pts : 0;
	info.seq_nota = intestazione != NULL;
	info.danno = quante ? regioni : NULL;
	info.quante_regioni = quante;
	info.danno_dichiarato = danno_dichiarato;
	info.danno_copre_tutto = copre_tutto;
	info.indice = cattura->conto.arrivati;
	info.consegna = &consegna;

	/*
	 * ⛔ E QUI SI GUARDA IL TIPO **PRIMA** DEL PUNTATORE.  Un DMA-BUF non ha
	 *    `data`: e' un descrittore che vive sulla scheda, e il puntatore resta
	 *    NULL.  Il controllo «niente puntatore, niente fotogramma» — giusto per la
	 *    memoria — qui scarterebbe tutto in silenzio.
	 */
	if (piano->type != SPA_DATA_DmaBuf)
	{
		if (!piano->data || byte == 0)
		{
			cattura->conto.senza_pixel++;
			goto restituisci;
		}
		info.pixel = (const uint8_t *) piano->data + offset;
	}

	if (cattura->su_fotogramma)
		cattura->su_fotogramma(&info, cattura->dati);

	/* --- il posto di chi aspetta ----------------------------------------- */
	g_mutex_lock(&cattura->lucchetto);
	if (cattura->qualcuno_aspetta && !cattura->posto_pieno)
	{
		CatturaFermo *f = &cattura->posto;

		f->byte = info.pixel ? byte : 0;
		g_free(f->pixel);
		f->pixel = NULL;
		if (info.pixel)
		{
			/* ⛔ SI COPIA, NON SI TIENE IL PUNTATORE: al giro dopo il produttore
			 *    ci riscrive dentro, e il fotogramma consegnato sarebbe un altro
			 *    da quello di cui si racconta il danno e la sequenza — due misure
			 *    sotto la stessa etichetta. */
			f->pixel = g_malloc(byte);
			memcpy(f->pixel, info.pixel, byte);
		}
		f->stride = passo;
		f->larghezza = consegna.larghezza;
		f->altezza = consegna.altezza;
		f->seq = info.seq;
		f->pts = info.pts;
		f->seq_nota = info.seq_nota;
		f->danno_dichiarato = danno_dichiarato;
		f->danno_copre_tutto = copre_tutto;
		f->indice = info.indice;
		f->consegna = consegna;
		cattura->posto_pieno = TRUE;
		g_cond_broadcast(&cattura->novita);
	}
	g_mutex_unlock(&cattura->lucchetto);

	if (cattura->conto.arrivati % 300 == 0)
		registro_dettaglio(AREA,
		                   "su %" G_GUINT64_FORMAT " fotogrammi: %u buffer distinti, danno "
		                   "pieno %" G_GUINT64_FORMAT " parziale %" G_GUINT64_FORMAT " assente %"
		                   G_GUINT64_FORMAT ", senza intestazione %" G_GUINT64_FORMAT
		                   ", di solo cursore %" G_GUINT64_FORMAT,
		                   cattura->conto.arrivati, cattura->conto.buffer_distinti,
		                   cattura->conto.danno_pieno, cattura->conto.danno_parziale,
		                   cattura->conto.danno_assente, cattura->conto.senza_intestazione,
		                   cattura->conto.solo_cursore);

restituisci:
	pw_stream_queue_buffer(cattura->flusso, pacco);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/* ------------------------------------------------------------------ *
 *  La proposta di formato
 * ------------------------------------------------------------------ */

/*
 * ⛔ SI ELENCA SOLO QUEL CHE SI SA LEGGERE, e in un ordine dichiarato.
 *
 * Elencare formati che il resto della catena non gestisce sarebbe un difetto
 * silenzioso: nessun punto a valle guarda il formato davvero negoziato, quindi
 * se il compositore scegliesse una variante RGB, rosso e blu uscirebbero
 * scambiati senza alcun errore.
 *
 * ⛔ E `CATTURA_COLORE_10BIT` propone **soltanto** i formati a dieci bit.
 *    Mettere BGRx nello stesso elenco farebbe negoziare BGRx e non si
 *    imparerebbe niente: la domanda «esistono dieci bit da questa sorgente?» ha
 *    una risposta solo se il rifiuto e' un rifiuto.
 */
static uint32_t quanti_colori(CatturaColore colore, uint32_t elenco[8])
{
	switch (colore)
	{
	case CATTURA_COLORE_BGRA:
		elenco[0] = SPA_VIDEO_FORMAT_BGRA;
		elenco[1] = SPA_VIDEO_FORMAT_BGRx;
		return 2;
	case CATTURA_COLORE_10BIT:
		elenco[0] = SPA_VIDEO_FORMAT_xBGR_210LE;
		elenco[1] = SPA_VIDEO_FORMAT_xRGB_210LE;
		elenco[2] = SPA_VIDEO_FORMAT_ABGR_210LE;
		elenco[3] = SPA_VIDEO_FORMAT_ARGB_210LE;
		return 4;
	default:
		elenco[0] = SPA_VIDEO_FORMAT_BGRx;
		elenco[1] = SPA_VIDEO_FORMAT_BGRA;
		return 2;
	}
}

static const struct spa_pod *proposta(struct spa_pod_builder *costruttore, uint32_t larghezza,
                                      uint32_t altezza, uint32_t fotogrammi_al_secondo,
                                      CatturaColore colore, gboolean con_modificatori)
{
	struct spa_rectangle misura = SPA_RECTANGLE(larghezza, altezza);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction cadenza_minima = SPA_FRACTION(1, 1);
	struct spa_fraction cadenza_massima = SPA_FRACTION(MAX(1u, fotogrammi_al_secondo), 1);
	struct spa_pod_frame cornice[3];
	uint32_t elenco[8];
	uint32_t quanti = quanti_colori(colore, elenco);
	uint32_t i;

	spa_pod_builder_push_object(costruttore, &cornice[0], SPA_TYPE_OBJECT_Format,
	                            SPA_PARAM_EnumFormat);
	spa_pod_builder_add(costruttore, SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	                    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), 0);

	/* I colori come scelta: il primo valore e' il preferito, e va ripetuto —
	 * e' la forma di `SPA_POD_CHOICE_ENUM_Id`, costruita a mano perche' il
	 * numero di voci cambia. */
	spa_pod_builder_prop(costruttore, SPA_FORMAT_VIDEO_format, 0);
	spa_pod_builder_push_choice(costruttore, &cornice[1], SPA_CHOICE_Enum, 0);
	spa_pod_builder_id(costruttore, elenco[0]);
	for (i = 0; i < quanti; i++)
		spa_pod_builder_id(costruttore, elenco[i]);
	spa_pod_builder_pop(costruttore, &cornice[1]);

	if (con_modificatori)
	{
		/*
		 * ⛔ IL MODIFICATORE VA DICHIARATO `MANDATORY | DONT_FIXATE`, o il valore
		 *    lo sceglie PipeWire invece di lasciarlo concordare con chi alloca.
		 *
		 * `DRM_FORMAT_MOD_LINEAR` per primo, ed e' un regalo di kpipewire: RadeonSI
		 * RIFIUTA i buffer con DCC e iHD — il driver della scheda che Mutter sceglie
		 * qui — li ACCETTA e poi forza LINEAR internamente, cioe' accetta e sbaglia
		 * in silenzio.  `DRM_FORMAT_MOD_INVALID` resta come seconda scelta:
		 * significa «la disposizione la decidi tu e me la dici».
		 *
		 * ⚠ E `[R]` Mutter offre una proposta con modificatori **solo se ne ha per
		 *   quel formato** (`meta-screen-cast-stream-src.c`: se
		 *   `meta_screen_cast_query_modifiers` torna vuoto, quel formato entra solo
		 *   nell'elenco senza modificatori).  ⇒ Se la scheda non ne da', la strada
		 *   della scheda non esiste, e non c'e' nessun errore che lo dica: lo dice
		 *   il tipo di buffer che arriva, ed e' per questo che si verifica.
		 */
		spa_pod_builder_prop(costruttore, SPA_FORMAT_VIDEO_modifier,
		                     SPA_POD_PROP_FLAG_MANDATORY | SPA_POD_PROP_FLAG_DONT_FIXATE);
		spa_pod_builder_push_choice(costruttore, &cornice[2], SPA_CHOICE_Enum, 0);
		spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_LINEAR);
		spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_LINEAR);
		spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_INVALID);
		spa_pod_builder_pop(costruttore, &cornice[2]);
	}

	/* ⛔ La misura come rettangolo FISSO: un intervallo aperto lascerebbe
	 *    scegliere Mutter, che sceglie 1280×720 e nessuno se ne accorge finche'
	 *    non guarda i pixel. */
	spa_pod_builder_add(costruttore, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura),
	                    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza),
	                    SPA_FORMAT_VIDEO_maxFramerate,
	                    SPA_POD_CHOICE_RANGE_Fraction(&cadenza_massima, &cadenza_minima,
	                                                  &cadenza_massima),
	                    0);
	return spa_pod_builder_pop(costruttore, &cornice[0]);
}

/* ------------------------------------------------------------------ *
 *  Ciclo di vita
 * ------------------------------------------------------------------ */

Cattura *cattura_avvia(uint32_t nodo, uint32_t larghezza, uint32_t altezza,
                       uint32_t fotogrammi_al_secondo, CatturaStrada strada, CatturaColore colore,
                       CatturaFotogramma su_fotogramma, CatturaFine su_fine, gpointer dati,
                       GError **sbaglio)
{
	static gsize inizializzato = 0;
	Cattura *cattura = g_new0(Cattura, 1);
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];
	gint64 scadenza;

	if (g_once_init_enter(&inizializzato))
	{
		pw_init(NULL, NULL);
		g_once_init_leave(&inizializzato, 1);
	}

	cattura->su_fotogramma = su_fotogramma;
	cattura->su_fine = su_fine;
	cattura->dati = dati;
	cattura->strada = strada;
	cattura->colore = colore;
	cattura->chiesta_larghezza = larghezza;
	cattura->chiesta_altezza = altezza;
	cattura->chiesti_al_secondo = fotogrammi_al_secondo;
	g_mutex_init(&cattura->lucchetto);
	g_cond_init(&cattura->novita);

	/* ⭐ Il modulo del cursore nasce SEMPRE, anche se nessuno ascolta: cosi' i
	 *    conteggi rispondono a «il metadato arriva?» senza dipendere da chi lo
	 *    consuma.  ⚠ Se non nasce non si fallisce: i pixel valgono piu' del
	 *    puntatore (`CODER.md` §4.2), ma il ripiego si DICE. */
	cattura->cursore = cursore_apri(cursore_rimbalzo, cattura);
	if (!cattura->cursore)
		registro_dice(AREA, "⛔ RIPIEGO: il modulo del cursore non si e' aperto — la forma del "
		                    "puntatore non partira' (i fotogrammi si', tutti)");

	cattura->ciclo = pw_thread_loop_new("remotix-cattura", NULL);
	if (!cattura->ciclo)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "ciclo PipeWire non creato");
		goto guasto;
	}
	cattura->contesto = pw_context_new(pw_thread_loop_get_loop(cattura->ciclo), NULL, 0);
	if (!cattura->contesto)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "contesto PipeWire non creato");
		goto guasto;
	}

	pw_thread_loop_lock(cattura->ciclo);
	if (pw_thread_loop_start(cattura->ciclo) < 0)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "thread di PipeWire non avviato");
		goto guasto;
	}
	cattura->nucleo = pw_context_connect(cattura->contesto, NULL, 0);
	if (!cattura->nucleo)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "connessione a PipeWire fallita");
		goto guasto;
	}
	cattura->flusso = pw_stream_new(cattura->nucleo, "remotix-cattura",
	                                pw_properties_new(PW_KEY_MEDIA_TYPE, "Video",
	                                                  PW_KEY_MEDIA_CATEGORY, "Capture",
	                                                  PW_KEY_MEDIA_ROLE, "Screen", NULL));
	if (!cattura->flusso)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "flusso PipeWire non creato");
		goto guasto;
	}
	pw_stream_add_listener(cattura->flusso, &cattura->gancio, &eventi, cattura);

	/* ⛔ UNA proposta sola, e dichiarata.  Offrirne due — una con i modificatori
	 *    e una senza — significa «prendo la scheda, ma se non c'e' va bene la
	 *    memoria»: e' un ripiego, e un ripiego silenzioso produce due
	 *    comportamenti sotto la stessa etichetta (`CODER.md` §4.2).  Chi vuole il
	 *    ripiego lo chiede due volte, e sa quale delle due gli e' toccata. */
	parametri[0] = proposta(&costruttore, larghezza, altezza, fotogrammi_al_secondo, colore,
	                        strada == CATTURA_STRADA_SCHEDA);

	if (pw_stream_connect(cattura->flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, 1) < 0)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "aggancio al nodo %u fallito", nodo);
		goto guasto;
	}

	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (cattura->stato != PW_STREAM_STATE_PAUSED &&
	       cattura->stato != PW_STREAM_STATE_STREAMING &&
	       cattura->stato != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(cattura->ciclo, 1);
	pw_thread_loop_unlock(cattura->ciclo);

	if (cattura->stato == PW_STREAM_STATE_ERROR)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "il compositore ha rifiutato quel che si e' chiesto (%s, strada %s): %s",
		            colore == CATTURA_COLORE_10BIT   ? "10 bit"
		            : colore == CATTURA_COLORE_BGRA ? "BGRA"
		                                            : "BGRx",
		            strada == CATTURA_STRADA_SCHEDA ? "scheda" : "memoria",
		            cattura->guasto ? cattura->guasto : "senza spiegazione");
		goto guasto;
	}
	if (cattura->stato != PW_STREAM_STATE_PAUSED && cattura->stato != PW_STREAM_STATE_STREAMING)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "la cattura non ha dato segno di vita entro %d secondi", ATTESA_AVVIO_S);
		goto guasto;
	}

	registro_dice(AREA, "cattura avviata sul nodo %u: chiesti %ux%u, strada %s", nodo, larghezza,
	              altezza, strada == CATTURA_STRADA_SCHEDA ? "scheda (DMA-BUF)" : "memoria");
	return cattura;

guasto:
	cattura_ferma(cattura);
	return NULL;
}

/* ------------------------------------------------------------------ *
 *  ⭐⭐ IL CAMBIO DI MISURA A CALDO — vedi `cattura.h`
 * ------------------------------------------------------------------ */

CatturaRitela cattura_ridimensiona(Cattura *cattura, uint32_t larghezza, uint32_t altezza)
{
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[5];
	uint32_t quanti;
	int esito;

	if (!cattura || !cattura->flusso || !cattura->ciclo)
		return CATTURA_RITELA_GUASTO;
	/* ⛔ Lo zero non e' «fuori dai limiti»: e' una richiesta senza contenuto, e
	 *    passarla al produttore vorrebbe dire chiedergli un monitor di area
	 *    nulla.  ⚠ Il resto della regola — 200..8192 e la parita' — sta in
	 *    `rcp_misura_ammessa()`, in un posto solo. */
	if (!larghezza || !altezza)
	{
		registro_dice(AREA, "⛔ ridimensionamento a %ux%u: una misura vuota non si chiede",
		              larghezza, altezza);
		return CATTURA_RITELA_GUASTO;
	}

	pw_thread_loop_lock(cattura->ciclo);

	/* ⛔⭐ LA GUARDIA OBBLIGATORIA — `kde.md` §8.2-bis: «senza, la rinegoziazione
	 *     si morde la coda», e il difetto NON si vede su Trixie.
	 *
	 * ⛔⛔ E SI CONFRONTA CON LA MISURA CHE IL FLUSSO **HA**, NON CON QUELLA CHE
	 *     GLI E' STATA CHIESTA — difetto trovato refutando, la notte del 15
	 *     agosto 2026, e la prima stesura aveva sbagliato proprio qui.
	 *
	 *     `kde.md` §8.2-bis scrive la guardia come `misura_attuale ==
	 *     misura_richiesta`, e **attuale** non e' **chiesta**: §4.5 dichiara
	 *     normale che il compositore conceda una misura diversa da quella
	 *     chiesta.  ⇒ Confrontando col chiesto, questa sequenza spegneva la
	 *     funzione per sempre:
	 *
	 *       si chiede 1920x1080, il compositore non obbedisce (o concede altro)
	 *       ⇒ `chiesta_*` = 1920x1080, il flusso e' rimasto dov'era
	 *       ⇒ l'utente riprova la STESSA misura
	 *       ⇒ «e' gia' chiesta»: nessuna richiesta parte, MAI PIU'.
	 *
	 *     E il registro avrebbe accusato la guardia giusta del difetto sbagliato.
	 *
	 * ⚠ Finche' il formato non e' noto non c'e' un «attuale»: allora si guarda il
	 *   chiesto, che e' l'unica cosa che c'e' — e si dichiara qui invece di
	 *   lasciarlo dedurre. */
	if (cattura->formato_noto ? (larghezza == cattura->formato.size.width
	                             && altezza == cattura->formato.size.height)
	                          : (larghezza == cattura->chiesta_larghezza
	                             && altezza == cattura->chiesta_altezza))
	{
		pw_thread_loop_unlock(cattura->ciclo);
		registro_dettaglio(AREA,
		                   "ridimensionamento a %ux%u: e' la misura che il flusso HA "
		                   "gia', NON rinegozio (kde.md §8.2-bis)",
		                   larghezza, altezza);
		return CATTURA_RITELA_GIA_COSI;
	}

	/* ⛔ Un flusso morto non si rinegozia, e «morto» si CHIEDE allo stato invece
	 *    di dedurlo dal silenzio: su un flusso in errore `update_params`
	 *    riuscirebbe e non arriverebbe mai un fotogramma — cioe' il ripiego
	 *    silenzioso che `CODER.md` §4.2 vieta. */
	if (cattura->stato != PW_STREAM_STATE_PAUSED && cattura->stato != PW_STREAM_STATE_STREAMING)
	{
		enum pw_stream_state stato = cattura->stato;
		/* ⛔ IL GUASTO SI COPIA PRIMA DI MOLLARE IL LUCCHETTO — difetto trovato
		 *    refutando: `su_stato()` gira sul thread del ciclo e fa
		 *    `g_free(guasto); guasto = g_strdup(...)`, quindi fra la `g_free` e
		 *    l'assegnazione il campo e' un puntatore penzolante.  ⚠ E questo ramo
		 *    si percorre **proprio mentre** il flusso sta morendo, cioe'
		 *    nell'istante in cui `su_stato` sta girando: leggerlo dopo l'unlock e'
		 *    leggere memoria liberata, e per una riga di registro. */
		char *guasto = cattura->guasto ? g_strdup(cattura->guasto) : NULL;
		pw_thread_loop_unlock(cattura->ciclo);
		registro_dice(AREA,
		              "⛔ ridimensionamento a %ux%u NON chiesto: il flusso e' «%s»%s%s",
		              larghezza, altezza, pw_stream_state_as_string(stato),
		              guasto ? " — " : "", guasto ? guasto : "");
		g_free(guasto);
		return CATTURA_RITELA_GUASTO;
	}

	/* ⛔ La misura CHIESTA si aggiorna PRIMA della richiesta, e sotto il lucchetto
	 *    del ciclo: `su_parametri` gira sul thread di PipeWire e ci confronta
	 *    contro il formato negoziato (la guardia «chiesto contro concesso»).
	 *    Aggiornarla dopo vorrebbe dire far confrontare la risposta nuova con la
	 *    domanda vecchia, cioe' dichiarare una divergenza che non c'e'. */
	cattura->chiesta_larghezza = larghezza;
	cattura->chiesta_altezza = altezza;
	/* ⚠ E la divergenza si azzera: e' un fatto della negoziazione che sta per
	 *   rifarsi, non una cicatrice della precedente. */
	cattura->misura_divergente = FALSE;

	/* ⛔ La stessa `proposta()` dell'avvio, con gli stessi colore e strada: una
	 *    proposta scritta a mano qui sarebbe una seconda regola sul formato, e il
	 *    giorno in cui una delle due cambiasse il flusso si riaprirebbe con un
	 *    colore diverso da quello negoziato — senza nessun errore. */
	parametri[0] = proposta(&costruttore, larghezza, altezza, cattura->chiesti_al_secondo,
	                        cattura->colore, cattura->strada == CATTURA_STRADA_SCHEDA);
	/* ⛔⭐ E CON LUI I QUATTRO PARAMETRI DI CONSUMO — difetto trovato refutando:
	 *     `pw_stream_update_params()` NON aggiunge, **sostituisce l'intera
	 *     lista**.  Passando il solo `EnumFormat` si cancellerebbero
	 *     `ParamBuffers` e i tre `ParamMeta`, fra cui quello del CURSORE.  ⚠ Nel
	 *     caso sano la richiamata del formato li rimette; ⛔ ma nel caso che
	 *     `cattura.h` documenta — il compositore che risponde «riuscito» e non
	 *     manda nessun evento — quella richiamata non gira, e il canale del
	 *     puntatore resterebbe senza sorgente senza che nessuno lo dica. */
	quanti = 1 + parametri_di_consumo(cattura, &costruttore, parametri + 1);
	esito = pw_stream_update_params(cattura->flusso, parametri, quanti);
	pw_thread_loop_unlock(cattura->ciclo);

	if (esito < 0)
	{
		registro_dice(AREA, "⛔ `pw_stream_update_params()` a %ux%u ha risposto %d (%s)",
		              larghezza, altezza, esito, spa_strerror(esito));
		return CATTURA_RITELA_GUASTO;
	}
	registro_dice(AREA,
	              "⭐ tela CHIESTA al produttore: %ux%u (`pw_stream_update_params`).  ⚠ E' la "
	              "richiesta, non l'esito: la verita' la dice il fotogramma (DECISIONI.md "
	              "§5.0-sexies)",
	              larghezza, altezza);
	return CATTURA_RITELA_CHIESTA;
}

gboolean cattura_risveglia(Cattura *cattura)
{
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[5];
	uint32_t l, a, quanti;
	int esito;

	if (!cattura || !cattura->flusso || !cattura->ciclo)
		return FALSE;

	pw_thread_loop_lock(cattura->ciclo);
	if (cattura->stato != PW_STREAM_STATE_PAUSED && cattura->stato != PW_STREAM_STATE_STREAMING)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		return FALSE;
	}
	/* ⛔ La misura e' quella NEGOZIATA, non quella chiesta: qui non si sta
	 *    cambiando niente — si sta ripetendo la stessa domanda per far ripartire
	 *    il flusso.  ⚠ Rifare la proposta con la misura CHIESTA, in un momento in
	 *    cui il compositore ne ha concessa un'altra (§4.5), sarebbe un
	 *    ridimensionamento travestito da risveglio. */
	l = cattura->formato_noto ? cattura->formato.size.width : cattura->chiesta_larghezza;
	a = cattura->formato_noto ? cattura->formato.size.height : cattura->chiesta_altezza;
	if (!l || !a)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		return FALSE;
	}
	parametri[0] = proposta(&costruttore, l, a, cattura->chiesti_al_secondo, cattura->colore,
	                        cattura->strada == CATTURA_STRADA_SCHEDA);
	quanti = 1 + parametri_di_consumo(cattura, &costruttore, parametri + 1);
	esito = pw_stream_update_params(cattura->flusso, parametri, quanti);
	pw_thread_loop_unlock(cattura->ciclo);

	if (esito < 0)
	{
		registro_dice(AREA, "⛔ risveglio del flusso a %ux%u: %s", l, a, spa_strerror(esito));
		return FALSE;
	}
	registro_dice(AREA,
	              "⭐ flusso RIAVVIATO alla stessa misura (%ux%u) per farsi consegnare un "
	              "fotogramma: su Wayland non si puo' chiedere «ridipingi», e questa e' la "
	              "sola leva che abbiamo (`cattura.h`)",
	              l, a);
	return TRUE;
}

void cattura_misura_chiesta(Cattura *cattura, uint32_t *larghezza, uint32_t *altezza)
{
	if (larghezza)
		*larghezza = cattura ? cattura->chiesta_larghezza : 0;
	if (altezza)
		*altezza = cattura ? cattura->chiesta_altezza : 0;
}

gboolean cattura_misura_negoziata(Cattura *cattura, uint32_t *larghezza, uint32_t *altezza)
{
	if (!cattura || !cattura->formato_noto)
		return FALSE; /* ⛔ «non e' stato negoziato», non «e' 0x0» */
	if (larghezza)
		*larghezza = cattura->formato.size.width;
	if (altezza)
		*altezza = cattura->formato.size.height;
	return TRUE;
}

/* ------------------------------------------------------------------ *
 *  La presa di un fotogramma
 * ------------------------------------------------------------------ */

/*
 * ⛔ LA MISURA DEL RANGE SI FA QUI, NON DENTRO LA RICHIAMATA.
 *
 * Mutter non dichiara il range (`[M]` 12 agosto 2026: `color_range` vale 0, cioe'
 * UNKNOWN), e chi lo desse per pieno starebbe deducendo.  ⇒ Lo si **misura** sui
 * pixel che ha consegnato, e si scrive che e' una misura nostra.
 *
 * ⚠ E la misura dipende dalla SCENA: un desktop che non ha ne' nero pieno ne'
 *   bianco pieno non arriva agli estremi, e cio' NON prova un range limitato.
 *   Per questo l'esito ha due valori e non tre.
 *
 * ⭐ E lo stesso giro risponde alla domanda peggiore di questa fase: il
 *    fotogramma e' NERO?  Un fotogramma nero e valido — misura giusta, stride
 *    giusto, danno giusto, e dentro il nulla — e' quel che consegna una sessione
 *    senza monitor virtuale, e ogni altro strumento del progetto lo
 *    promuoverebbe.  ⛔ Qui non si rifiuta: si DICHIARA.  Un desktop puo'
 *    legittimamente essere nero, e rifiutarlo sarebbe decidere al posto
 *    dell'utente; tacerlo sarebbe consegnare il nulla senza una riga.
 */
static void misura_i_pixel(CatturaFermo *fermo)
{
	CatturaConsegna *c = &fermo->consegna;
	int r = 0, g = 1, b = 2;
	guint64 riga, colonna;
	const uint8_t *base = fermo->pixel;
	uint8_t primo[4] = { 0, 0, 0, 0 };
	gboolean uniforme = TRUE;

	c->range_misurato = CATTURA_RANGE_NON_MISURATO;
	if (!fermo->pixel || fermo->byte == 0)
		return;
	if (c->bit_per_canale != 8 || !posizioni_rgb(c->formato_grezzo, &r, &g, &b))
	{
		/* ⛔ Non si misura sui byte sbagliati: un numero preso da una disposizione
		 *    che non conosciamo sarebbe peggio di nessun numero. */
		return;
	}

	c->minimo[0] = c->minimo[1] = c->minimo[2] = 255;
	c->massimo[0] = c->massimo[1] = c->massimo[2] = 0;
	memcpy(primo, base, 4);

	for (riga = 0; riga < fermo->altezza; riga++)
	{
		const uint8_t *p = base + riga * (guint64) fermo->stride;

		if ((riga + 1) * (guint64) fermo->stride > fermo->byte)
			break;
		for (colonna = 0; colonna < fermo->larghezza; colonna++, p += 4)
		{
			uint8_t v[3] = { p[r], p[g], p[b] };
			int i;

			for (i = 0; i < 3; i++)
			{
				if (v[i] < c->minimo[i])
					c->minimo[i] = v[i];
				if (v[i] > c->massimo[i])
					c->massimo[i] = v[i];
			}
			if (uniforme && (p[0] != primo[0] || p[1] != primo[1] || p[2] != primo[2]))
				uniforme = FALSE;
		}
	}

	c->uniforme = uniforme;
	c->nero = (c->massimo[0] == 0 && c->massimo[1] == 0 && c->massimo[2] == 0);
	if (c->minimo[0] == 0 && c->minimo[1] == 0 && c->minimo[2] == 0 && c->massimo[0] == 255 &&
	    c->massimo[1] == 255 && c->massimo[2] == 255)
		c->range_misurato = CATTURA_RANGE_COMPATIBILE_PIENO;
	else
		c->range_misurato = CATTURA_RANGE_NON_CONCLUSIVO;
}

CatturaPresa cattura_prendi(Cattura *cattura, double attesa_s, CatturaFermo *fuori,
                            GError **sbaglio)
{
	gint64 scadenza;
	gboolean preso = FALSE;

	g_return_val_if_fail(cattura != NULL && fuori != NULL, CATTURA_PRESA_GUASTO);
	memset(fuori, 0, sizeof *fuori);

	if (cattura->stato != PW_STREAM_STATE_STREAMING && cattura->stato != PW_STREAM_STATE_PAUSED)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "il flusso non e' attivo (stato %s%s%s): non c'e' nessun fotogramma da "
		            "aspettare, e questo NON e' uno zero",
		            pw_stream_state_as_string(cattura->stato), cattura->guasto ? ", guasto: " : "",
		            cattura->guasto ? cattura->guasto : "");
		return CATTURA_PRESA_GUASTO;
	}

	g_mutex_lock(&cattura->lucchetto);
	cattura->qualcuno_aspetta = TRUE;
	cattura->posto_pieno = FALSE;
	scadenza = g_get_monotonic_time() + (gint64) (attesa_s * G_USEC_PER_SEC);
	while (!cattura->posto_pieno)
	{
		if (!g_cond_wait_until(&cattura->novita, &cattura->lucchetto, scadenza))
			break;
	}
	if (cattura->posto_pieno)
	{
		*fuori = cattura->posto;
		memset(&cattura->posto, 0, sizeof cattura->posto);
		cattura->posto_pieno = FALSE;
		preso = TRUE;
	}
	cattura->qualcuno_aspetta = FALSE;
	g_mutex_unlock(&cattura->lucchetto);

	/* ⛔ «E' STATO attivo» non e' «lo e' ancora»: la morte a meta' presa. */
	if (cattura->stato != PW_STREAM_STATE_STREAMING && cattura->stato != PW_STREAM_STATE_PAUSED)
	{
		cattura_fermo_libera(fuori);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "il flusso era vivo ed e' caduto durante la presa (stato %s%s%s)",
		            pw_stream_state_as_string(cattura->stato), cattura->guasto ? ", guasto: " : "",
		            cattura->guasto ? cattura->guasto : "");
		return CATTURA_PRESA_GUASTO;
	}

	if (!preso)
	{
		/* ⭐ ZERO LEGITTIMO: il flusso e' stato attivo per tutta l'attesa e non e'
		 *    arrivato niente.  Su Mutter e' il desktop fermo — la cadenza e' 0/1,
		 *    «mandami un fotogramma quando cambia qualcosa» — ed e' un risultato,
		 *    non un guasto. */
		return CATTURA_PRESA_ZERO;
	}

	/* ⛔ LA STRADA SI VERIFICA, NON SI DA' PER CHIESTA (`LEZIONI.md` §1.8). */
	if (cattura->strada == CATTURA_STRADA_SCHEDA &&
	    fuori->consegna.buffer_dichiarato != CATTURA_BUFFER_DMABUF)
	{
		CatturaBuffer arrivato = fuori->consegna.buffer_dichiarato;

		cattura_fermo_libera(fuori);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "si e' chiesta la scheda (DMA-BUF) e il produttore ha consegnato %s: non si "
		            "ripiega in silenzio",
		            cattura_buffer_nome(arrivato));
		return CATTURA_PRESA_GUASTO;
	}
	if (cattura->strada == CATTURA_STRADA_MEMORIA &&
	    fuori->consegna.buffer_dichiarato == CATTURA_BUFFER_DMABUF)
	{
		cattura_fermo_libera(fuori);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "si e' chiesta la memoria e sono arrivati DMA-BUF: i pixel non sono qui");
		return CATTURA_PRESA_GUASTO;
	}

	if (!fuori->pixel)
	{
		/* Strada della scheda: il tipo e' dichiarato, i pixel vivono altrove.
		 * ⛔ Non e' un guasto e non e' uno zero, ed e' la terza uscita. */
		return CATTURA_PRESA_PIXEL_ALTROVE;
	}

	misura_i_pixel(fuori);
	if (fuori->consegna.nero)
		registro_dice(AREA, "⛔ il fotogramma consegnato e' NERO (massimo 0 su tutti e tre i "
		                    "canali): e' quel che consegna una sessione senza monitor virtuale "
		                    "— gnome.md §3.1, guasto M9");
	else if (fuori->consegna.uniforme)
		registro_dice(AREA, "⚠ il fotogramma consegnato e' UNIFORME: tutti i pixel uguali, e "
		                    "questo non e' nero — e' un buffer mai dipinto");
	return CATTURA_PRESA_FATTA;
}

void cattura_fermo_libera(CatturaFermo *fermo)
{
	if (!fermo)
		return;
	g_free(fermo->pixel);
	memset(fermo, 0, sizeof *fermo);
}

/* ------------------------------------------------------------------ *
 *  Quel che si dichiara a valle
 * ------------------------------------------------------------------ */

gboolean cattura_consegna(Cattura *cattura, CatturaConsegna *fuori)
{
	g_return_val_if_fail(cattura != NULL && fuori != NULL, FALSE);

	memset(fuori, 0, sizeof *fuori);
	if (!cattura->formato_noto)
		return FALSE; /* ⛔ «non lo so ancora», e non «e' tutto a zero» */

	fuori->noto = TRUE;
	fuori->strada_chiesta = cattura->strada;
	fuori->buffer_chiesto =
	    cattura->strada == CATTURA_STRADA_SCHEDA ? CATTURA_BUFFER_DMABUF : CATTURA_BUFFER_MEMFD;
	fuori->buffer_dichiarato =
	    cattura->conto.quanti_tipi > 0 ? cattura->conto.tipi_visti[0] : CATTURA_BUFFER_IGNOTO;
	fuori->buffer_dichiarato_grezzo = cattura->primo_tipo_grezzo;
	fuori->buffer_distinti = cattura->conto.buffer_distinti;
	fuori->formato_grezzo = cattura->formato.format;
	fuori->formato = cattura_colore_nome(cattura->formato.format);
	fuori->bit_per_canale = bit_per_canale(cattura->formato.format);
	fuori->fonte_bit =
	    fuori->bit_per_canale > 0 ? CATTURA_FONTE_FORMATO : CATTURA_FONTE_NON_DICHIARATA;
	fuori->larghezza = cattura->formato.size.width;
	fuori->altezza = cattura->formato.size.height;
	fuori->modificatore = cattura->formato.modifier;
	fuori->range_grezzo = cattura->formato.color_range;
	fuori->matrice_grezza = cattura->formato.color_matrix;
	fuori->trasferimento_grezzo = cattura->formato.transfer_function;
	fuori->primari_grezzi = cattura->formato.color_primaries;
	fuori->fonte_range =
	    cattura->formato.color_range ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;
	fuori->fonte_matrice =
	    cattura->formato.color_matrix ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;
	/* ⛔ Lo stride NON si mette qui: finche' non e' arrivato un fotogramma non
	 *    e' un fatto, ed e' il campo che a valle non va ricalcolato.  Lo porta il
	 *    fotogramma. */
	fuori->stride = 0;
	fuori->stride_letto = FALSE;
	fuori->byte = 0;
	return TRUE;
}

void cattura_conteggi(Cattura *cattura, CatturaConteggi *fuori)
{
	g_return_if_fail(cattura != NULL && fuori != NULL);
	*fuori = cattura->conto;
}

gboolean cattura_attiva(Cattura *cattura)
{
	return cattura && cattura->stato == PW_STREAM_STATE_STREAMING;
}

const char *cattura_guasto(Cattura *cattura)
{
	return cattura ? cattura->guasto : NULL;
}

void cattura_cursore(Cattura *cattura, CursoreArrivata quando_cambia, void *chi)
{
	if (!cattura)
		return;
	g_mutex_lock(&cattura->lucchetto);
	cattura->cursore_fn = quando_cambia;
	cattura->cursore_chi = chi;
	g_mutex_unlock(&cattura->lucchetto);
}

void cattura_ferma(Cattura *cattura)
{
	if (!cattura)
		return;

	/*
	 * Prima si ferma il thread, poi si distrugge il resto: fermandolo per primo
	 * non serve piu' prendere il lucchetto per toccare gli oggetti di PipeWire, e
	 * soprattutto non si rischia di distruggere il flusso mentre una richiamata
	 * lo sta usando.
	 */
	if (cattura->ciclo)
		pw_thread_loop_stop(cattura->ciclo);
	if (cattura->flusso)
		pw_stream_destroy(cattura->flusso);
	if (cattura->nucleo)
		pw_core_disconnect(cattura->nucleo);
	if (cattura->contesto)
		pw_context_destroy(cattura->contesto);
	if (cattura->ciclo)
		pw_thread_loop_destroy(cattura->ciclo);

	/* ⛔ DOPO il thread, non prima: `guarda_cursore` gira di la'. */
	cursore_chiudi(cattura->cursore);

	g_free(cattura->posto.pixel);
	g_mutex_clear(&cattura->lucchetto);
	g_cond_clear(&cattura->novita);
	g_free(cattura->guasto);
	g_free(cattura);
}
