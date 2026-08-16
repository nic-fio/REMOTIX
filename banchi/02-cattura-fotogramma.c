/*
 * 02-cattura-fotogramma — UN fotogramma preso dalla sessione GNOME, consegnato
 * in memoria con il tipo di buffer DICHIARATO.  Banco della sotto-fase F2.2.
 *
 * ⛔ PERCHE' ESISTE, VISTO CHE `misura-cattura` C'E' GIA'
 *
 * Lo strumento della fase 0 (`v1/banchi/banco-compositori/misura-cattura.c`) e'
 * certificato, riproduce i 36 ± 2 fotogrammi di Mutter, e resta il controllo
 * positivo storico di tutto il progetto.  ⛔ Ma non guarda **mai** dentro il
 * buffer: conta i fotogrammi, legge il tipo di dato, il danno, la fence e gli
 * intervalli — e i pixel non li tocca.  Riga per riga: `su_processo` prende
 * `datas[0]`, ne legge `type`, `fd`, `chunk->stride`, e rimette il buffer in
 * coda con `pw_stream_queue_buffer`.  Nessuna lettura di `piano->data`.
 *
 * ⇒ **Un fotogramma completamente NERO passerebbe la fase 0 con il massimo dei
 *   voti**: 36 al secondo, danno parziale, quattro buffer riciclati, zero salti
 *   di sequenza.  Tutto verde, e sullo schermo il nulla.
 *
 * ⛔ E il nero non e' un caso di scuola: `STUDI.md` §gnome §3.1 dice che in headless
 *   `needs_outputs=false`, quindi **senza `--virtual-monitor` la sessione parte
 *   viva, completa e nera**, ed e' la prova guasta M9 del piano di misure di
 *   `STUDI.md` §gnome §13.  Il piano della fase 2 (`PIANO.md`) lo scrive a lettere
 *   intere: *«una sessione nera e perfettamente viva e' la cosa che si scambia
 *   per un difetto di cattura, e si cerca per mezza giornata dalla parte
 *   sbagliata»*.  Il fotogramma NERO E VALIDO e' il guasto peggiore di questa
 *   sotto-fase, e serve uno strumento che sappia vederlo.
 *
 * Questo programma fa quindi la cosa che l'altro non fa, e **solo quella**:
 * prende un fotogramma, lo scrive su disco byte per byte, e accanto ci mette un
 * manifesto con tutto quel che serve per giudicarlo senza doverlo dedurre.  Chi
 * giudica e' un altro programma (`02-cattura-giudica.py`), e la separazione e'
 * voluta: e' l'unico modo di innestare un guasto nei PIXEL — un fotogramma nero
 * al posto di quello vero — senza toccare ne' il produttore ne' il giudice.
 *
 * ---------------------------------------------------------------------------
 * ⛔ QUEL CHE QUESTO PROGRAMMA **NON** DIMOSTRA — scritto qui perche' e' la
 *    forma d'errore E1 di `REVIEWER.md` §2, e questo e' esattamente il punto in
 *    cui e' gia' stata pagata due volte (`LEZIONI.md` §1.11):
 *
 *   | Quel che si legge nel manifesto | Quel che NON prova                    |
 *   |---------------------------------|---------------------------------------|
 *   | `tipo = MemFd`                  | ⛔ **niente sul compositore**: dipende |
 *   |                                 | da quel che il CLIENTE ha chiesto.     |
 *   |                                 | Qui il cliente chiede la memoria       |
 *   |                                 | apposta — servono i pixel leggibili —  |
 *   |                                 | quindi MemFd e' la RISPOSTA A UNA      |
 *   |                                 | NOSTRA DOMANDA, non una scoperta       |
 *   | `tipo = DMA-BUF`                | non prova che Mutter renda in GPU:     |
 *   |                                 | un render node aperto e' necessario,   |
 *   |                                 | non sufficiente (KWin lo apre anche    |
 *   |                                 | quando poi rende in QPainter)          |
 *
 *   Per questo il manifesto porta TRE campi separati e non uno: `chiesto`,
 *   `dichiarato_dal_produttore` e `chi_lo_dice`.  ⭐ Il tipo di buffer **si
 *   chiede e si dichiara**, non si deduce — ed e' il mandato di F2.2.
 *
 * ---------------------------------------------------------------------------
 * ⛔ ZERO, FALLITO E GUASTO SONO TRE COSE DIVERSE (`REVIEWER.md` §1 punto 4)
 *
 *   uscita 0  un fotogramma c'e' ed e' stato scritto
 *   uscita 3  ⭐ ZERO fotogrammi, ma il flusso E' STATO attivo per tutta la
 *             misura: e' uno zero **legittimo** — un desktop fermo non consegna
 *             niente (`LEZIONI.md` §4 trappola 8), ed e' un risultato, non un
 *             guasto.  Nessun `.raw` viene scritto, e il manifesto lo dice
 *   uscita 2  GUASTO: il flusso non e' mai diventato attivo, oppure e' caduto a
 *             misura in corso, oppure si e' chiesta una strada e ne e' arrivata
 *             un'altra.  Non c'e' nessun numero da leggere
 *   uscita 1  l'ambiente: il monitor virtuale non si monta, PipeWire non
 *             risponde, il file non si scrive
 *
 * Le tre guardie di uscita 2 sono le stesse che la fase 0 ha dovuto aggiungere
 * a `misura-cattura` DOPO averlo creduto (voci 1 e 8 di «Che cosa NON ha
 * funzionato» in `fasi/00-ambiente.md`): qui nascono insieme al programma.
 *
 * ---------------------------------------------------------------------------
 * ⛔ L'ORDINE: PRIMA IL MONITOR, POI LA SCENA — e lo dice il programma, non chi
 *    lo lancia.
 *
 * `banco.sh` della fase 0 accende la scena 2,5 secondi DOPO il misuratore, con
 * la ragione scritta accanto: *«senza uno schermo non c'e' dove aprirsi»*.  Qui
 * l'attesa a tempo non basta, perche' questo programma deve poi sapere QUALI
 * fotogrammi sono arrivati prima della scena e quali dopo.  Quindi il programma
 * scrive un file (`--pronto`) nell'istante in cui il flusso diventa attivo, e
 * chi lo lancia accende la scena solo allora.  ⭐ Non e' un'attesa: e' un evento
 * (`LEZIONI.md` §4 trappola 9 — «non si aspetta un silenzio, si aspetta un
 * evento»).
 *
 * ⚠ E la stessa forma morde la fase 2 da un'altra parte, gia' misurata: in una
 *   sessione GNOME senza dispositivi di input, un client aperto PRIMA che il
 *   puntatore virtuale di `libei` esista non riceve nulla (`PIANO.md`, riquadro
 *   «Una domanda che la fase 1 ha trovato e che morde QUI», `[M]` 10 agosto).
 *   Qui non si crea nessun dispositivo — non e' l'area di F2.2 — ma l'ordine e'
 *   lo stesso, e chi montera' l'input dovra' infilarlo fra il `--pronto` e la
 *   scena.
 *
 * ---------------------------------------------------------------------------
 * ⛔ DUE FOTOGRAMMI, NON UNO, E LA RAGIONE E' `CODER.md` §3.5 (forma E9)
 *
 * *Un campione preso all'avvio non dice niente del regime.*  Per un'immagine
 * ferma la regola non sparisce: cambia forma.
 *
 *   `primo`   il primo fotogramma dopo che il flusso e' diventato attivo, prima
 *             che la scena esista.  E' il **ridisegno completo**: su di esso il
 *             danno e' `pieno`, ed e' il fotogramma che l'utente vedrebbe
 *             collegandosi a un desktop appena montato
 *   `regime`  un fotogramma preso dopo `--dopo-scena` secondi di scena viva,
 *             saltandone `--scarta`.  Su Mutter a regime il danno e'
 *             **parziale** nel 98 % dei casi (`fasi/00-ambiente.md`: pieno 15,
 *             parziale 929)
 *
 * ⭐ E il confronto fra i due risponde a una domanda che i documenti oggi si
 *    contraddicono su:
 *
 *   - `v1/remotix-c/src/cattura.h` dice: *«in zero-copy Mutter ricicla i propri
 *     buffer e vi ridipinge dentro SOLO la parte cambiata; fuori da quelle
 *     regioni ci sono i pixel del fotogramma che aveva usato quel buffer
 *     prima»*;
 *   - `STUDI.md` §gnome §8.1, che ha riletto il codice di Mutter, dice il contrario:
 *     *«⛔ falso: blit dell'intero framebuffer, stack di clip svuotato
 *     deliberatamente»*.
 *
 *   Uno dei due e' vecchio.  Un fotogramma `regime` con danno **parziale** che
 *   contiene comunque la scena INTERA decide la questione, e la decide con una
 *   misura invece che con una rilettura.  ⚠ E la decisione conta: se avesse
 *   ragione `cattura.h`, la fase 2 consegnerebbe mezzo desktop e meta' schermata
 *   vecchia, senza un errore da nessuna parte.
 *
 * ---------------------------------------------------------------------------
 * ⚠ QUESTO PROGRAMMA NON MISURA IL RITMO, E NON DEVE.
 *
 * Copia due fotogrammi da 8 MB dentro la richiamata `process`, che gira sul
 * thread di tempo reale di PipeWire.  `misura-cattura` scrive, giustamente, che
 * chi rallenta quel ciclo falsa la propria misura — quindi qui i fotogrammi al
 * secondo **non si stampano affatto**: il ritmo e' della fase 0 (36 ± 2) e della
 * fase 3.  Un numero di ritmo che uscisse da qui sarebbe un numero giusto per
 * una domanda che nessuno ha fatto, ed e' la voce 8 di `fasi/00-ambiente.md`.
 *
 * ---------------------------------------------------------------------------
 * uso:
 *   02-cattura-fotogramma --uscita PREFISSO --pronto FILE
 *        [--larghezza W] [--altezza H] [--fps N] [--bgra] [--dmabuf]
 *        [--dopo-scena S] [--scarta N] [--durata S] [--etichetta T]
 *        [--nodo N]
 *
 * Scrive: PREFISSO-primo.raw, PREFISSO-regime.raw, PREFISSO.json
 */

#include <gio/gio.h>
#include <pipewire/pipewire.h>
#include <spa/buffer/meta.h>
#include <spa/param/video/format-utils.h>
#include <spa/utils/result.h>
#include <drm_fourcc.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define ATTESA_CHIAMATA_MS 15000
#define ATTESA_NODO_MS 10000
#define ATTESA_AVVIO_S 10
#define FD_MAX 16
#define TIPI_MAX 8

/* ------------------------------------------------------------------ *
 *  Il fotogramma trattenuto
 * ------------------------------------------------------------------ */

typedef struct
{
	gboolean preso;
	uint8_t *pixel;      /* copia nostra: il buffer di PipeWire torna subito */
	size_t byte;
	uint32_t stride;
	uint32_t offset;
	uint32_t dimensione_chunk;
	uint32_t tipo_dati;
	int64_t seq;
	int64_t pts;
	gboolean seq_noto;
	const char *danno;   /* "pieno" | "parziale" | "assente"                */
	guint64 indice;      /* quale fotogramma era, contato dal primo arrivato */
	gint64 quando;
} Fermo;

typedef struct
{
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;

	struct spa_video_info_raw formato;
	gboolean formato_noto;
	enum pw_stream_state stato;
	char *guasto;
	gboolean vuole_dmabuf;

	guint64 arrivati;
	guint64 prima_della_scena;
	guint64 dopo_la_scena;
	guint64 danno_pieno, danno_parziale, danno_assente;
	guint64 senza_header;

	int fd_visti[FD_MAX];
	guint quanti_fd;
	uint32_t tipi_visti[TIPI_MAX];
	guint quanti_tipi;

	/* ⛔ La scena si dichiara viva con una variabile che scrive CHI LANCIA,
	 *    non con un orologio: il programma deve sapere quali fotogrammi sono
	 *    arrivati prima e quali dopo, e un'attesa a tempo non lo distingue. */
	volatile gboolean scena_viva;
	gint64 t_scena;      /* quando la scena e' stata dichiarata viva        */
	gint64 t_regime;     /* da quando si puo' prendere il fotogramma di regime */
	guint64 salta_ancora;

	Fermo primo;
	Fermo regime;

	gint64 t_inizio;
} Presa;

/* ------------------------------------------------------------------ *
 *  Il danno — copiato dalla fase 0 perche' la domanda e' la stessa
 * ------------------------------------------------------------------ */

static const char *guarda_danno(Presa *p, struct pw_buffer *pacco)
{
	struct spa_meta *meta = spa_buffer_find_meta(pacco->buffer, SPA_META_VideoDamage);
	struct spa_meta_region *regione;
	gboolean copre_tutto = FALSE;
	gboolean vista = FALSE;

	if (!meta)
	{
		p->danno_assente++;
		return "assente";
	}
	spa_meta_for_each(regione, meta)
	{
		if (!spa_meta_region_is_valid(regione))
			break;
		vista = TRUE;
		if (regione->region.position.x == 0 && regione->region.position.y == 0 &&
		    regione->region.size.width >= p->formato.size.width &&
		    regione->region.size.height >= p->formato.size.height)
			copre_tutto = TRUE;
	}
	if (!vista)
	{
		p->danno_assente++;
		return "assente";
	}
	if (copre_tutto)
	{
		p->danno_pieno++;
		return "pieno";
	}
	p->danno_parziale++;
	return "parziale";
}

/*
 * ⛔ SI COPIA, NON SI TIENE IL PUNTATORE.
 *
 * `cattura.h` di v1 lo scrive in testa: *«i pixel vivono solo per la durata
 * della chiamata: chi li vuole se li copia»*.  Un puntatore trattenuto verrebbe
 * riscritto dal produttore al giro dopo, e il fotogramma scritto su disco
 * sarebbe un fotogramma diverso da quello di cui il manifesto racconta il danno
 * e la sequenza: due misure sotto la stessa etichetta, che e' la forma E2.
 */
static void trattieni(Fermo *f, struct spa_data *piano, struct spa_meta_header *intestazione,
                      const char *danno, guint64 indice, gint64 adesso)
{
	uint32_t dimensione;
	uint32_t offset = piano->chunk ? piano->chunk->offset : 0;

	dimensione = piano->chunk && piano->chunk->size > 0 ? piano->chunk->size : piano->maxsize;
	if (offset + dimensione > piano->maxsize)
		dimensione = piano->maxsize > offset ? piano->maxsize - offset : 0;
	if (!piano->data || dimensione == 0)
		return;

	g_free(f->pixel);
	f->pixel = g_malloc(dimensione);
	memcpy(f->pixel, (const uint8_t *) piano->data + offset, dimensione);
	f->byte = dimensione;
	f->stride = piano->chunk ? (uint32_t) piano->chunk->stride : 0;
	f->offset = offset;
	f->dimensione_chunk = piano->chunk ? piano->chunk->size : 0;
	f->tipo_dati = piano->type;
	f->danno = danno;
	f->indice = indice;
	f->quando = adesso;
	if (intestazione)
	{
		f->seq = (int64_t) intestazione->seq;
		f->pts = (int64_t) intestazione->pts;
		f->seq_noto = TRUE;
	}
	f->preso = TRUE;
}

static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	Presa *p = dati;

	p->stato = nuovo;
	if (errore)
	{
		g_free(p->guasto);
		p->guasto = g_strdup(errore);
	}
	if (nuovo == PW_STREAM_STATE_STREAMING && p->t_inizio == 0)
	{
		p->t_inizio = g_get_monotonic_time();
		fprintf(stderr, "  flusso attivo\n");
	}
	pw_thread_loop_signal(p->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Presa *p = dati;
	uint32_t tipo, sottotipo;
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[3];
	int tipi = (1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr);

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &tipo, &sottotipo) < 0)
		return;
	if (tipo != SPA_MEDIA_TYPE_video || sottotipo != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &p->formato) < 0)
		return;

	p->formato_noto = TRUE;
	fprintf(stderr, "  formato negoziato: %ux%u %s, modificatore 0x%" PRIx64 "\n",
	        p->formato.size.width, p->formato.size.height,
	        p->formato.format == SPA_VIDEO_FORMAT_BGRx ? "BGRx"
	        : p->formato.format == SPA_VIDEO_FORMAT_BGRA ? "BGRA"
	                                                     : "ALTRO",
	        (uint64_t) p->formato.modifier);

	/* Il tipo dei dati si concorda QUI, non nel formato: chi tace lascia il
	 * predefinito.  `LEZIONI.md` §4 trappola 4 — il tipo di buffer si chiede in
	 * DUE posti, e dichiararne uno solo fa riuscire la negoziazione con dentro
	 * il contrario di quel che si voleva. */
	if (p->vuole_dmabuf)
		tipi |= (1 << SPA_DATA_DmaBuf);

	parametri[0] = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(tipi));
	parametri[1] = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Header), SPA_PARAM_META_size,
	    SPA_POD_Int(sizeof(struct spa_meta_header)));
	parametri[2] = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_VideoDamage), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(sizeof(struct spa_meta_region) * 4,
	                             sizeof(struct spa_meta_region) * 1,
	                             sizeof(struct spa_meta_region) * 16));
	pw_stream_update_params(p->flusso, parametri, 3);
	pw_thread_loop_signal(p->ciclo, false);
}

static void su_processo(void *dati)
{
	Presa *p = dati;
	struct pw_buffer *pacco;
	struct spa_data *piano;
	struct spa_meta_header *intestazione;
	const char *danno;
	gint64 adesso;
	guint i;
	gboolean noto;

	pacco = pw_stream_dequeue_buffer(p->flusso);
	if (!pacco)
		return;

	adesso = g_get_monotonic_time();
	piano = &pacco->buffer->datas[0];
	p->arrivati++;

	/* Quanti buffer distinti ricicla il produttore: Mutter ne usa quattro, e
	 * saperlo serve a leggere il resto (R29). */
	noto = FALSE;
	for (i = 0; i < p->quanti_fd; i++)
		if (p->fd_visti[i] == (piano->fd >= 0 ? (int) piano->fd : -1))
			noto = TRUE;
	if (!noto && p->quanti_fd < FD_MAX)
		p->fd_visti[p->quanti_fd++] = piano->fd >= 0 ? (int) piano->fd : -1;

	/* ⛔ I TIPI SI COLLEZIONANO TUTTI, non si tiene solo l'ultimo.
	 *    `misura-cattura` stampa `m->tipo_dati` dell'ULTIMO fotogramma: se il
	 *    produttore cambiasse strada a meta' misura, la riga direbbe una strada
	 *    sola per due popolazioni diverse.  Non e' mai stato visto succedere,
	 *    ma «non e' mai stato visto» non e' «non puo'», e costa otto interi. */
	noto = FALSE;
	for (i = 0; i < p->quanti_tipi; i++)
		if (p->tipi_visti[i] == piano->type)
			noto = TRUE;
	if (!noto && p->quanti_tipi < TIPI_MAX)
		p->tipi_visti[p->quanti_tipi++] = piano->type;

	intestazione = spa_buffer_find_meta_data(pacco->buffer, SPA_META_Header, sizeof *intestazione);
	if (!intestazione)
		p->senza_header++;
	danno = guarda_danno(p, pacco);

	if (!p->scena_viva)
	{
		p->prima_della_scena++;
		/* Il PRIMO in assoluto: il ridisegno completo, e il fotogramma che
		 * vedrebbe chi si collega a un desktop appena montato. */
		if (!p->primo.preso)
			trattieni(&p->primo, piano, intestazione, danno, p->arrivati, adesso);
	}
	else
	{
		p->dopo_la_scena++;
		if (p->t_regime == 0)
			p->t_regime = p->t_scena;
		if (adesso >= p->t_regime)
		{
			if (p->salta_ancora > 0)
				p->salta_ancora--;
			else
				/* Si riscrive a ogni giro: il fotogramma di regime che
				 * interessa e' l'ULTIMO della finestra, non il primo — cosi'
				 * il danno che porta e' quello del regime e non quello del
				 * primo ridisegno dopo l'accensione della scena. */
				trattieni(&p->regime, piano, intestazione, danno, p->arrivati, adesso);
		}
	}

	pw_stream_queue_buffer(p->flusso, pacco);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/* ------------------------------------------------------------------ *
 *  La proposta di formato — identica a quella della fase 0
 * ------------------------------------------------------------------ */

static const struct spa_pod *formato_memoria(struct spa_pod_builder *c, uint32_t w, uint32_t h,
                                             uint32_t fps, uint32_t colore)
{
	struct spa_rectangle misura = SPA_RECTANGLE(w, h);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction minima = SPA_FRACTION(1, 1);
	struct spa_fraction massima = SPA_FRACTION(fps > 0 ? fps : 1, 1);

	return spa_pod_builder_add_object(
	    c, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format, SPA_POD_Id(colore),
	    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura), SPA_FORMAT_VIDEO_framerate,
	    SPA_POD_Fraction(&cadenza), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&massima, &minima, &massima));
}

static const struct spa_pod *formato_dmabuf(struct spa_pod_builder *c, uint32_t w, uint32_t h,
                                            uint32_t fps, uint32_t colore)
{
	struct spa_rectangle misura = SPA_RECTANGLE(w, h);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction minima = SPA_FRACTION(1, 1);
	struct spa_fraction massima = SPA_FRACTION(fps > 0 ? fps : 1, 1);
	struct spa_pod_frame cornice[2];

	spa_pod_builder_push_object(c, &cornice[0], SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat);
	spa_pod_builder_add(c, SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	                    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
	                    SPA_FORMAT_VIDEO_format, SPA_POD_Id(colore), 0);
	spa_pod_builder_prop(c, SPA_FORMAT_VIDEO_modifier,
	                     SPA_POD_PROP_FLAG_MANDATORY | SPA_POD_PROP_FLAG_DONT_FIXATE);
	spa_pod_builder_push_choice(c, &cornice[1], SPA_CHOICE_Enum, 0);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_INVALID);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_INVALID);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_LINEAR);
	spa_pod_builder_pop(c, &cornice[1]);
	spa_pod_builder_add(c, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura),
	                    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza),
	                    SPA_FORMAT_VIDEO_maxFramerate,
	                    SPA_POD_CHOICE_RANGE_Fraction(&massima, &minima, &massima), 0);
	return spa_pod_builder_pop(c, &cornice[0]);
}

/* ------------------------------------------------------------------ *
 *  Il monitor virtuale di Mutter — la sequenza che non ammette permute
 * ------------------------------------------------------------------ */

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"
#define NOME_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define PERCORSO_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSIONE "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_FLUSSO "org.gnome.Mutter.ScreenCast.Stream"

typedef struct
{
	GDBusConnection *bus;
	char *controllo;
	char *cattura;
	char *flusso;
	uint32_t nodo;
} Palco;

static void su_nodo(GDBusConnection *bus, const char *mittente, const char *percorso,
                    const char *interfaccia, const char *segnale, GVariant *parametri, gpointer d)
{
	if (g_variant_is_of_type(parametri, G_VARIANT_TYPE("(u)")))
		g_variant_get(parametri, "(u)", (uint32_t *) d);
}

static gboolean sveglia(gpointer d)
{
	return G_SOURCE_CONTINUE;
}

/* Non si usa mai g_bus_get_sync sul bus di sessione: GIO vi tiene acceso
 * `exit-on-close` e ci ammazza al logout (`LEZIONI.md` §5, «il bus di
 * sessione»). */
static GDBusConnection *bus_di_sessione(GError **sbaglio)
{
	g_autofree char *indirizzo = g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);
	GDBusConnection *bus;

	if (!indirizzo)
		return NULL;
	bus = g_dbus_connection_new_for_address_sync(
	    indirizzo,
	    G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
	        G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, sbaglio);
	if (bus)
		g_dbus_connection_set_exit_on_close(bus, FALSE);
	return bus;
}

static GVariant *chiama(GDBusConnection *bus, const char *nome, const char *percorso,
                        const char *iface, const char *metodo, GVariant *arg,
                        const GVariantType *risposta, GError **sbaglio)
{
	return g_dbus_connection_call_sync(bus, nome, percorso, iface, metodo, arg, risposta,
	                                   G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS, NULL, sbaglio);
}

/*
 * ⛔ L'ORDINE E' QUELLO DI `mutter.h`, e ogni permuta e' punita con un errore
 *    diverso che non dice «hai sbagliato l'ordine» (`LEZIONI.md` §4 trappola 1):
 *
 *      1. RemoteDesktop.CreateSession      → si legge SessionId SENZA avviarla
 *      2. ScreenCast.CreateSession         dichiarando remote-desktop-session-id
 *      3. RemoteDesktop.Session.Start      ← ADESSO, non prima
 *      4. ScreenCast.Session.RecordVirtual → il flusso
 *      5. Stream.Start                     ← il FLUSSO, non la sessione
 *
 * ⛔ E ci si iscrive a `PipeWireStreamAdded` PRIMA di `Stream.Start`: l'annuncio
 *    arriva DURANTE la chiamata, e chi si iscrive dopo aspetta per sempre
 *    qualcosa di gia' passato (trappola 2).
 *
 * ⚠ E la sessione si chiude fermando il CONTROLLO, non la cattura: un
 *   `ScreenCast.Session.Stop` su una cattura associata risponde «Must be stopped
 *   from remote desktop session», e ogni monitor virtuale non smontato resta
 *   attaccato a Mutter.  Sul server ci sono altri due giri accesi: un monitor
 *   dimenticato da questo banco sarebbe un difetto che pagano gli altri.
 */
static Palco *palco_monta(uint32_t larghezza, uint32_t altezza, GError **sbaglio)
{
	Palco *p = g_new0(Palco, 1);
	g_autofree char *id = NULL;
	GVariantBuilder prop;
	guint sottoscrizione;
	GMainContext *contesto;
	GSource *battito;
	gint64 scadenza;

	p->bus = bus_di_sessione(sbaglio);
	if (!p->bus)
		goto guasto;

	{
		g_autoptr(GVariant) r = chiama(p->bus, NOME_REMOTE, PERCORSO_REMOTE, IFACE_REMOTE,
		                               "CreateSession", NULL, G_VARIANT_TYPE("(o)"), sbaglio);
		if (!r)
		{
			g_prefix_error(sbaglio, "Mutter non espone RemoteDesktop (c'e' una sessione?): ");
			goto guasto;
		}
		g_variant_get(r, "(o)", &p->controllo);
	}
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_REMOTE, p->controllo, "org.freedesktop.DBus.Properties", "Get",
		           g_variant_new("(ss)", IFACE_REMOTE_SESSIONE, "SessionId"),
		           G_VARIANT_TYPE("(v)"), sbaglio);
		g_autoptr(GVariant) v = NULL;
		if (!r)
			goto guasto;
		g_variant_get(r, "(v)", &v);
		id = g_variant_dup_string(v, NULL);
	}

	g_variant_builder_init(&prop, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&prop, "{sv}", "remote-desktop-session-id", g_variant_new_string(id));
	g_variant_builder_add(&prop, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_SCREENCAST, PERCORSO_SCREENCAST, IFACE_SCREENCAST, "CreateSession",
		           g_variant_new("(a{sv})", &prop), G_VARIANT_TYPE("(o)"), sbaglio);
		if (!r)
			goto guasto;
		g_variant_get(r, "(o)", &p->cattura);
	}
	{
		g_autoptr(GVariant) r = chiama(p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE,
		                               "Start", NULL, NULL, sbaglio);
		if (!r)
			goto guasto;
	}

	g_variant_builder_init(&prop, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&prop, "{sv}", "cursor-mode", g_variant_new_uint32(2));
	g_variant_builder_add(&prop, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	{
		g_autofree char *mapping = g_uuid_string_random();
		g_autoptr(GVariant) r = NULL;

		g_variant_builder_add(&prop, "{sv}", "mapping-id", g_variant_new_string(mapping));
		r = chiama(p->bus, NOME_SCREENCAST, p->cattura, IFACE_SC_SESSIONE, "RecordVirtual",
		           g_variant_new("(a{sv})", &prop), G_VARIANT_TYPE("(o)"), sbaglio);
		if (!r)
			goto guasto;
		g_variant_get(r, "(o)", &p->flusso);
	}

	contesto = g_main_context_new();
	g_main_context_push_thread_default(contesto);
	sottoscrizione = g_dbus_connection_signal_subscribe(p->bus, NULL, IFACE_SC_FLUSSO,
	                                                    "PipeWireStreamAdded", p->flusso, NULL,
	                                                    G_DBUS_SIGNAL_FLAGS_NONE, su_nodo, &p->nodo,
	                                                    NULL);
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_SCREENCAST, p->flusso, IFACE_SC_FLUSSO, "Start", NULL, NULL, sbaglio);
		if (!r)
		{
			g_dbus_connection_signal_unsubscribe(p->bus, sottoscrizione);
			g_main_context_pop_thread_default(contesto);
			g_main_context_unref(contesto);
			goto guasto;
		}
	}
	battito = g_timeout_source_new(50);
	g_source_set_callback(battito, sveglia, NULL, NULL);
	g_source_attach(battito, contesto);
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_NODO_MS * 1000;
	while (p->nodo == 0 && g_get_monotonic_time() < scadenza)
		g_main_context_iteration(contesto, TRUE);
	g_source_destroy(battito);
	g_source_unref(battito);
	g_dbus_connection_signal_unsubscribe(p->bus, sottoscrizione);
	g_main_context_pop_thread_default(contesto);
	g_main_context_unref(contesto);

	if (p->nodo == 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT, "nessun nodo PipeWire annunciato");
		goto guasto;
	}
	fprintf(stderr, "  monitor virtuale %ux%u chiesto, nodo PipeWire %u\n", larghezza, altezza,
	        p->nodo);
	return p;

guasto:
	if (p->bus && p->controllo)
	{
		g_autoptr(GError) x = NULL;
		g_autoptr(GVariant) r = g_dbus_connection_call_sync(
		    p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL, NULL,
		    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &x);
	}
	g_clear_object(&p->bus);
	g_free(p->controllo);
	g_free(p->cattura);
	g_free(p->flusso);
	g_free(p);
	return NULL;
}

static void palco_smonta(Palco *p)
{
	if (!p)
		return;
	if (p->bus && p->controllo)
	{
		g_autoptr(GError) x = NULL;
		g_autoptr(GVariant) r = g_dbus_connection_call_sync(
		    p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL, NULL,
		    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &x);
	}
	g_clear_object(&p->bus);
	g_free(p->controllo);
	g_free(p->cattura);
	g_free(p->flusso);
	g_free(p);
}

/* ------------------------------------------------------------------ *
 *  Il manifesto
 * ------------------------------------------------------------------ */

static const char *nome_tipo(uint32_t t)
{
	return t == SPA_DATA_DmaBuf   ? "DMA-BUF"
	       : t == SPA_DATA_MemFd  ? "MemFd"
	       : t == SPA_DATA_MemPtr ? "MemPtr"
	       : t == SPA_DATA_MemId  ? "MemId"
	                              : "SCONOSCIUTO";
}

static const char *nome_colore(uint32_t c)
{
	return c == SPA_VIDEO_FORMAT_BGRx   ? "BGRx"
	       : c == SPA_VIDEO_FORMAT_BGRA ? "BGRA"
	                                    : "ALTRO";
}

/*
 * ===========================================================================
 * ⛔ LE TRE COSE CHE F2.3 (LA CODIFICA) CHIEDE DICHIARATE, NON DEDOTTE
 * ===========================================================================
 *
 * La profondita' di bit vera, il RANGE (limitato o pieno) e la MATRICE (601 o
 * 709).  ⛔ E la ragione della terza e' che *un confronto di pixel fatto con la
 * matrice sbagliata misura la matrice* — e F2.6 confrontera' i pixel.  Senza
 * queste tre dichiarazioni il rosso della fase 2 non avrebbe un imputato.
 *
 * ⭐ E NON SI DEDUCONO: SPA le porta.  `struct spa_video_info_raw` ha
 *    `color_range`, `color_matrix`, `transfer_function` e `color_primaries`,
 *    e `spa_format_video_raw_parse` le riempie.  Si CHIEDONO al produttore
 *    (`CODER.md` §3.7 — non si deduce il mittente, lo si chiede) e si scrive
 *    quel che risponde, **compreso «non lo dichiaro»**: un `UNKNOWN` e' una
 *    risposta, e va scritta come tale invece di essere riempita con quel che ci
 *    aspettiamo.  Il silenzio scambiato per un valore e' la forma E8.
 *
 * ⛔ E LA PRIMA DELLE TRE HA GIA' UNA RISPOSTA CHE PESA SULL'INTERA FASE 2:
 *
 *    `STUDI.md` §gnome §8.3 `[R]`, letto riga per riga nel codice di Mutter 48.7:
 *    **«Solo BGRx e BGRA»**.  Sono formati a **8 bit per canale**.
 *
 *    ⇒ Da questa cattura NON possono uscire dieci bit veri.  Un HEVC Main10
 *      alimentato da qui porta 8 bit promossi a 10, e l'etichetta continua a
 *      dire Main10 mentre l'immagine viene bene lo stesso: e' il guasto che
 *      F2.3 chiama **F2.3-A**, e ⛔ **l'imputato e' qui, non nel codificatore**.
 *      Per questo il numero si misura gia' alla cattura.
 */
static const char *nome_range(uint32_t r)
{
	switch (r)
	{
	case 1: return "PIENO (0-255)";
	case 2: return "LIMITATO (16-235)";
	default: return "NON DICHIARATO dal produttore";
	}
}

static const char *nome_matrice(uint32_t m)
{
	switch (m)
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

static const char *nome_trasferimento(uint32_t t)
{
	switch (t)
	{
	case 1: return "gamma 1.0 (lineare)";
	case 4: return "gamma 2.2";
	case 5: return "BT.709";
	case 7: return "sRGB";
	case 11: return "BT.2020 12 bit";
	default: return "NON DICHIARATA dal produttore";
	}
}

static const char *nome_primari(uint32_t p)
{
	switch (p)
	{
	case 1: return "BT.709";
	case 4: return "SMPTE170M";
	case 7: return "BT.2020";
	default: return "NON DICHIARATI dal produttore";
	}
}

/* I bit per canale si ricavano dal FORMATO, che e' un fatto del produttore, non
 * una nostra ipotesi.  ⛔ E se un giorno arrivasse un formato che non
 * conosciamo, si risponde 0 e lo si dichiara: un valore inventato qui
 * diventerebbe «10 bit veri» in una tabella di F2.3. */
static int bit_per_canale(uint32_t c)
{
	switch (c)
	{
	case SPA_VIDEO_FORMAT_BGRx:
	case SPA_VIDEO_FORMAT_BGRA:
	case SPA_VIDEO_FORMAT_RGBx:
	case SPA_VIDEO_FORMAT_RGBA:
	case SPA_VIDEO_FORMAT_xRGB:
	case SPA_VIDEO_FORMAT_ARGB:
		return 8;
	default:
		return 0;
	}
}

static gboolean scrivi_raw(const char *percorso, const Fermo *f, GError **sbaglio)
{
	return g_file_set_contents(percorso, (const char *) f->pixel, (gssize) f->byte, sbaglio);
}

static void manifesto_fermo(GString *s, const char *chiave, const Fermo *f, const char *file)
{
	if (!f->preso)
	{
		g_string_append_printf(s, "  \"%s\": null,\n", chiave);
		return;
	}
	g_string_append_printf(s,
	                       "  \"%s\": {\n"
	                       "    \"file\": \"%s\",\n"
	                       "    \"byte\": %zu,\n"
	                       "    \"stride\": %u,\n"
	                       "    \"offset\": %u,\n"
	                       "    \"dimensione_chunk\": %u,\n"
	                       "    \"tipo_dichiarato\": \"%s\",\n"
	                       "    \"danno\": \"%s\",\n"
	                       "    \"indice_fra_gli_arrivati\": %" PRIu64 ",\n"
	                       "    \"seq\": %" PRId64 ",\n"
	                       "    \"pts\": %" PRId64 ",\n"
	                       "    \"seq_nota\": %s\n"
	                       "  },\n",
	                       chiave, file, f->byte, f->stride, f->offset, f->dimensione_chunk,
	                       nome_tipo(f->tipo_dati), f->danno, f->indice, f->seq, f->pts,
	                       f->seq_noto ? "true" : "false");
}

/* ------------------------------------------------------------------ *
 *  Il programma
 * ------------------------------------------------------------------ */

int main(int argc, char **argv)
{
	uint32_t larghezza = 1920, altezza = 1080, fps = 60, nodo = 0;
	double dopo_scena = 3.0, durata = 12.0, attesa_scena = 25.0;
	guint64 scarta = 10;
	/* ⛔ Quanti fotogrammi si PRETENDONO dopo che la scena e' stata dichiarata
	 *    viva.  Uno basta: la domanda e' «la scena dipinge sullo schermo che
	 *    stiamo catturando, si' o no?».  Con `0` si dichiara di voler misurare
	 *    lo zero legittimo (scena «fermo»). */
	guint64 minimo_dopo_scena = 1;
	gboolean vuole_dmabuf = FALSE;
	uint32_t colore = SPA_VIDEO_FORMAT_BGRx;
	const char *etichetta = "senza-nome";
	const char *uscita = NULL, *pronto = NULL, *segnale_scena = NULL;
	Presa p = { 0 };
	Palco *palco = NULL;
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[2];
	uint32_t n_parametri = 0;
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *file_primo = NULL, *file_regime = NULL, *file_json = NULL;
	GString *manifesto;
	gint64 scadenza, fine;
	int codice = 0;
	const char *esito;
	char quando[64];
	time_t adesso_epoch;
	struct tm adesso_tm;
	guint i;

	for (i = 1; (int) i < argc; i++)
	{
		if (!strcmp(argv[i], "--uscita") && (int) i + 1 < argc)
			uscita = argv[++i];
		else if (!strcmp(argv[i], "--pronto") && (int) i + 1 < argc)
			pronto = argv[++i];
		else if (!strcmp(argv[i], "--segnale-scena") && (int) i + 1 < argc)
			segnale_scena = argv[++i];
		else if (!strcmp(argv[i], "--nodo") && (int) i + 1 < argc)
			nodo = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--larghezza") && (int) i + 1 < argc)
			larghezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--altezza") && (int) i + 1 < argc)
			altezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fps") && (int) i + 1 < argc)
			fps = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--dopo-scena") && (int) i + 1 < argc)
			dopo_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--attesa-scena") && (int) i + 1 < argc)
			attesa_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--durata") && (int) i + 1 < argc)
			durata = atof(argv[++i]);
		else if (!strcmp(argv[i], "--scarta") && (int) i + 1 < argc)
			scarta = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--minimo-dopo-scena") && (int) i + 1 < argc)
			minimo_dopo_scena = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--dmabuf"))
			vuole_dmabuf = TRUE;
		else if (!strcmp(argv[i], "--bgra"))
			colore = SPA_VIDEO_FORMAT_BGRA;
		else if (!strcmp(argv[i], "--etichetta") && (int) i + 1 < argc)
			etichetta = argv[++i];
		else
		{
			fprintf(stderr,
			        "uso: %s --uscita PREFISSO --pronto FILE --segnale-scena FILE\n"
			        "        [--larghezza W] [--altezza H] [--fps N] [--bgra] [--dmabuf]\n"
			        "        [--dopo-scena S] [--scarta N] [--durata S] [--attesa-scena S]\n"
			        "        [--minimo-dopo-scena N] [--etichetta T] [--nodo N]\n",
			        argv[0]);
			return 2;
		}
	}
	if (!uscita || !pronto || !segnale_scena)
	{
		fprintf(stderr, "⛔ servono --uscita, --pronto e --segnale-scena.\n"
		                "   Il file --pronto dice a chi lancia che il monitor virtuale c'e' e\n"
		                "   che la scena si puo' accendere; il file --segnale-scena e' la\n"
		                "   risposta: «la scena e' accesa».  Senza questi due l'ordine fra\n"
		                "   monitor e scena tornerebbe a essere un'attesa a tempo.\n");
		return 2;
	}

	file_primo = g_strdup_printf("%s-primo.raw", uscita);
	file_regime = g_strdup_printf("%s-regime.raw", uscita);
	file_json = g_strdup_printf("%s.json", uscita);

	adesso_epoch = time(NULL);
	gmtime_r(&adesso_epoch, &adesso_tm);
	strftime(quando, sizeof quando, "%Y-%m-%dT%H:%M:%SZ", &adesso_tm);

	p.vuole_dmabuf = vuole_dmabuf;

	fprintf(stderr, "== %s: chiesti %ux%u, %s, tetto %u fps, strada %s ==\n", etichetta, larghezza,
	        altezza, nome_colore(colore), fps, vuole_dmabuf ? "DMA-BUF" : "memoria");

	if (nodo == 0)
	{
		palco = palco_monta(larghezza, altezza, &sbaglio);
		if (!palco)
		{
			fprintf(stderr, "⛔ monitor virtuale non montato: %s\n", sbaglio->message);
			return 1;
		}
		nodo = palco->nodo;
	}

	pw_init(NULL, NULL);
	p.ciclo = pw_thread_loop_new("presa", NULL);
	p.contesto = pw_context_new(pw_thread_loop_get_loop(p.ciclo), NULL, 0);
	pw_thread_loop_lock(p.ciclo);
	if (pw_thread_loop_start(p.ciclo) < 0)
	{
		pw_thread_loop_unlock(p.ciclo);
		fprintf(stderr, "⛔ thread PipeWire non avviato\n");
		palco_smonta(palco);
		return 1;
	}
	p.nucleo = pw_context_connect(p.contesto, NULL, 0);
	if (!p.nucleo)
	{
		pw_thread_loop_unlock(p.ciclo);
		fprintf(stderr, "⛔ connessione a PipeWire fallita\n");
		palco_smonta(palco);
		return 1;
	}
	p.flusso = pw_stream_new(p.nucleo, "02-cattura-fotogramma",
	                         pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY,
	                                           "Capture", PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(p.flusso, &p.gancio, &eventi, &p);

	if (vuole_dmabuf)
		parametri[n_parametri++] = formato_dmabuf(&costruttore, larghezza, altezza, fps, colore);
	parametri[n_parametri++] = formato_memoria(&costruttore, larghezza, altezza, fps, colore);

	if (pw_stream_connect(p.flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, n_parametri) < 0)
	{
		pw_thread_loop_unlock(p.ciclo);
		fprintf(stderr, "⛔ aggancio al nodo %u fallito\n", nodo);
		palco_smonta(palco);
		return 1;
	}
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (p.stato != PW_STREAM_STATE_PAUSED && p.stato != PW_STREAM_STATE_STREAMING &&
	       p.stato != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(p.ciclo, 1);
	pw_thread_loop_unlock(p.ciclo);

	if (p.stato == PW_STREAM_STATE_ERROR)
	{
		printf("GUASTO\t%s\tcattura rifiutata\n", etichetta);
		fprintf(stderr, "⛔ FALLITO: cattura rifiutata: %s\n",
		        p.guasto ? p.guasto : "senza spiegazione");
		palco_smonta(palco);
		return 2;
	}

	/* ⛔ Il file «pronto» si scrive SOLO quando il flusso e' davvero attivo.
	 *    Scriverlo prima significherebbe accendere la scena su un monitor che
	 *    non esiste ancora, e la scena si aprirebbe su niente — che e' proprio
	 *    l'ordine che `banco.sh` della fase 0 aveva dovuto imparare. */
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (p.stato != PW_STREAM_STATE_STREAMING && g_get_monotonic_time() < scadenza)
		g_usleep(20000);
	if (p.stato != PW_STREAM_STATE_STREAMING)
	{
		printf("GUASTO\t%s\tflusso mai attivo\n", etichetta);
		fprintf(stderr,
		        "⛔ FALLITO (non «zero»): il flusso non e' mai diventato attivo.\n"
		        "   stato finale %d%s%s.  Non c'e' nessun fotogramma da giudicare qui:\n"
		        "   la cattura non e' mai cominciata (LEZIONI.md §1.9).\n",
		        (int) p.stato, p.guasto ? ", guasto: " : "", p.guasto ? p.guasto : "");
		palco_smonta(palco);
		return 2;
	}
	if (!g_file_set_contents(pronto, "pronto\n", -1, &sbaglio))
	{
		fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", pronto, sbaglio->message);
		palco_smonta(palco);
		return 1;
	}
	fprintf(stderr, "  pronto: la scena si puo' accendere adesso\n");

	/* Si aspetta che chi lancia dichiari la scena accesa.  ⛔ E se non arriva
	 * mai non si misura lo stesso: si dichiara.  Una scena che non parte e un
	 * compositore muto hanno lo stesso aspetto — voce 8 di
	 * `fasi/00-ambiente.md`, e la terza faccia di uno stesso difetto. */
	scadenza = g_get_monotonic_time() + (gint64) (attesa_scena * G_USEC_PER_SEC);
	while (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS) && g_get_monotonic_time() < scadenza)
		g_usleep(50000);
	if (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS))
	{
		printf("GUASTO\t%s\tla scena non e' mai stata dichiarata accesa\n", etichetta);
		fprintf(stderr,
		        "⛔ FALLITO: dopo %.1f s nessuno ha dichiarato la scena accesa (%s).\n"
		        "   Un fotogramma preso adesso sarebbe il desktop vuoto sotto\n"
		        "   l'etichetta della scena: due cose diverse sotto lo stesso nome.\n",
		        attesa_scena, segnale_scena);
		palco_smonta(palco);
		return 2;
	}
	p.t_scena = g_get_monotonic_time();
	p.t_regime = p.t_scena + (gint64) (dopo_scena * G_USEC_PER_SEC);
	p.salta_ancora = scarta;
	p.scena_viva = TRUE;
	fprintf(stderr, "  scena dichiarata accesa: il regime comincia fra %.1f s\n", dopo_scena);

	fine = p.t_scena + (gint64) (durata * G_USEC_PER_SEC);
	while (g_get_monotonic_time() < fine)
		g_usleep(50000);

	/* ⛔ «E' STATO attivo» non e' «lo e' ancora»: la morte a meta' misura. */
	if (p.stato != PW_STREAM_STATE_STREAMING)
	{
		printf("GUASTO\t%s\tflusso caduto durante la presa\n", etichetta);
		fprintf(stderr,
		        "⛔ FALLITO (non «zero»): il flusso era attivo ed e' caduto.\n"
		        "   stato finale %d%s%s.  Fotogrammi arrivati prima di cadere: %" PRIu64 ".\n",
		        (int) p.stato, p.guasto ? ", guasto: " : "", p.guasto ? p.guasto : "", p.arrivati);
		palco_smonta(palco);
		return 2;
	}

	/* ⛔ LA STRADA SI VERIFICA, NON SI DA' PER CHIESTA — `LEZIONI.md` §1.8. */
	if (vuole_dmabuf && p.quanti_tipi > 0 && p.tipi_visti[0] != SPA_DATA_DmaBuf)
	{
		printf("GUASTO\t%s\tchiesto DMA-BUF, ottenuta memoria\n", etichetta);
		fprintf(stderr,
		        "⛔ FALLITO: si e' chiesto DMA-BUF e il produttore ha consegnato %s.\n"
		        "   Non si ripiega in silenzio (LEZIONI.md §1.8, corollario).\n",
		        nome_tipo(p.tipi_visti[0]));
		palco_smonta(palco);
		return 2;
	}

	/*
	 * ⛔ SCENA VIVA E ZERO FOTOGRAMMI NON E' UNO ZERO: E' UN GUASTO.
	 *
	 * Trovato il 12 agosto 2026, al PRIMO giro vero di questo banco, e trovato
	 * perche' il banco e' uscito **VERDE** mentre il difetto era vivo — cioe' la
	 * cosa peggiore che un banco possa fare (`REVIEWER.md` §1).
	 *
	 * Che cosa era successo: la sessione GNOME aveva GIA' un monitor virtuale
	 * (`Meta-0`), il nostro `RecordVirtual` ne aggiungeva un secondo (`Meta-1`),
	 * e `mpv --fs` andava a schermo intero sul PRIMO — che non e' quello che
	 * stavamo catturando.  La scena era viva, dipingeva a 60 fotogrammi al
	 * secondo, `ps` diceva `Sl`, e la nostra cattura riceveva **zero**.
	 *
	 * ⇒ Con una scena DICHIARATA VIVA E IN MOVIMENTO, zero fotogrammi non e' il
	 *   comportamento legittimo della trappola 8: e' la prova che stiamo
	 *   guardando uno schermo diverso da quello su cui dipinge la scena.  E' il
	 *   controllo di `LEZIONI.md` §1.1 — *«quanto disegna il client, contato
	 *   accanto a quanto consegna la cattura: senza, un tetto della scena viene
	 *   attribuito al compositore, e viceversa»*.
	 *
	 * ⚠ Chi vuole misurare lo zero legittimo — il desktop fermo — passa
	 *   `--minimo-dopo-scena 0` e lo dichiara.  Non lo si ottiene per caso.
	 */
	if (p.scena_viva && p.dopo_la_scena < minimo_dopo_scena)
	{
		printf("GUASTO\t%s\tscena viva e %" PRIu64 " fotogrammi dopo\n", etichetta,
		       p.dopo_la_scena);
		fprintf(stderr,
		        "⛔ FALLITO (non «zero»): la scena era dichiarata viva e sono arrivati\n"
		        "   %" PRIu64 " fotogrammi dopo di lei (minimo preteso %" PRIu64 ").\n"
		        "   Prima della scena ne erano arrivati %" PRIu64 ": il flusso funziona.\n"
		        "\n"
		        "   ⇒ Non e' il desktop fermo. E' che la scena dipinge su uno SCHERMO\n"
		        "     DIVERSO da quello che stiamo catturando: se la sessione ha gia'\n"
		        "     un monitor, una finestra a schermo intero va su quello e non sul\n"
		        "     monitor virtuale appena montato da noi.\n"
		        "     Si dichiara lo schermo alla scena (mpv `--fs-screen-name`), e si\n"
		        "     verifica che abbia obbedito (CODER.md §3.9).\n",
		        p.dopo_la_scena, minimo_dopo_scena, p.prima_della_scena);
		palco_smonta(palco);
		return 2;
	}

	/* --- la scrittura -------------------------------------------------- */
	if (p.arrivati == 0)
	{
		/* ⭐ ZERO LEGITTIMO, e si distingue dal fallimento con l'uscita 3.
		 *    Il flusso e' stato attivo per tutta la presa: se nessun fotogramma
		 *    e' arrivato, il desktop non e' cambiato — che su Mutter e' il
		 *    comportamento dichiarato, non un guasto (trappola 8). */
		esito = "ZERO FOTOGRAMMI";
		codice = 3;
	}
	else if (vuole_dmabuf)
	{
		/* ⛔ CON IL DMA-BUF I PIXEL NON SI LEGGONO DA QUI, E LO SI DICE.
		 *    Il descrittore vive sulla scheda: leggerlo vorrebbe dire
		 *    importarlo, cioe' meta' del palco.  Questo giro serve a DICHIARARE
		 *    il tipo di buffer, non a giudicare l'immagine, e un `.raw` scritto
		 *    da qui sarebbe vuoto sotto l'etichetta di un fotogramma. */
		esito = "TIPO DICHIARATO, PIXEL NON LETTI (dmabuf)";
		codice = 0;
	}
	else if (!p.regime.preso && !p.primo.preso)
	{
		printf("GUASTO\t%s\tfotogrammi arrivati ma nessuno copiabile\n", etichetta);
		fprintf(stderr,
		        "⛔ FALLITO: sono arrivati %" PRIu64 " fotogrammi e nessuno aveva pixel\n"
		        "   mappati (data nullo o chunk vuoto).  Non e' uno zero: e' un buffer\n"
		        "   che non si e' potuto leggere.\n",
		        p.arrivati);
		palco_smonta(palco);
		return 2;
	}
	else
	{
		esito = "UN FOTOGRAMMA";
		codice = 0;
		if (p.primo.preso && !scrivi_raw(file_primo, &p.primo, &sbaglio))
		{
			fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", file_primo, sbaglio->message);
			palco_smonta(palco);
			return 1;
		}
		if (p.regime.preso && !scrivi_raw(file_regime, &p.regime, &sbaglio))
		{
			fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", file_regime, sbaglio->message);
			palco_smonta(palco);
			return 1;
		}
	}

	manifesto = g_string_new("{\n");
	g_string_append_printf(manifesto,
	                       "  \"strumento\": \"02-cattura-fotogramma\",\n"
	                       "  \"etichetta\": \"%s\",\n"
	                       "  \"quando_utc\": \"%s\",\n"
	                       "  \"nodo_pipewire\": %u,\n"
	                       "  \"esito\": \"%s\",\n"
	                       "  \"uscita\": %d,\n",
	                       etichetta, quando, nodo, esito, codice);
	g_string_append_printf(manifesto,
	                       "  \"chiesto\": {\n"
	                       "    \"larghezza\": %u, \"altezza\": %u, \"fps_massimi\": %u,\n"
	                       "    \"colore\": \"%s\", \"strada\": \"%s\",\n"
	                       "    \"cadenza\": \"0/1 con maxFramerate a %u — «mandami un fotogramma "
	                       "quando cambia qualcosa»\"\n"
	                       "  },\n",
	                       larghezza, altezza, fps, nome_colore(colore),
	                       vuole_dmabuf ? "dmabuf" : "memoria", fps);
	g_string_append_printf(manifesto,
	                       "  \"negoziato\": {\n"
	                       "    \"noto\": %s,\n"
	                       "    \"larghezza\": %u, \"altezza\": %u,\n"
	                       "    \"colore\": \"%s\",\n"
	                       "    \"modificatore\": \"0x%" PRIx64 "\",\n"
	                       "    \"chi_lo_dice\": \"PipeWire, SPA_PARAM_Format nella richiamata "
	                       "param_changed — non e' l'etichetta che gli abbiamo dato noi\"\n"
	                       "  },\n",
	                       p.formato_noto ? "true" : "false", p.formato.size.width,
	                       p.formato.size.height, nome_colore(p.formato.format),
	                       (uint64_t) p.formato.modifier);

	/* ⛔ LE TRE COSE CHE F2.3 CHIEDE DICHIARATE — chieste al produttore, non
	 *    dedotte, e scritte com'egli risponde, «non lo dichiaro» compreso. */
	g_string_append_printf(
	    manifesto,
	    "  \"consegna_a_F2_3\": {\n"
	    "    \"bit_per_canale\": %d,\n"
	    "    \"bit_per_canale_chi_lo_dice\": \"il FORMATO negoziato (%s). "
	    "STUDI.md §gnome §8.3 [R]: Mutter consegna SOLO BGRx e BGRA, che sono 8 bit per "
	    "canale — da questa cattura NON escono dieci bit veri\",\n"
	    "    \"⛔ F2.3-A\": \"un HEVC Main10 alimentato da qui porta 8 bit promossi a "
	    "10: l'etichetta dice Main10, l'immagine viene bene lo stesso, e l'imputato e' "
	    "LA CATTURA, non il codificatore\",\n"
	    "    \"range\": \"%s\",\n"
	    "    \"matrice\": \"%s\",\n"
	    "    \"trasferimento\": \"%s\",\n"
	    "    \"primari\": \"%s\",\n"
	    "    \"chi_lo_dice\": \"spa_video_info_raw.color_range / .color_matrix / "
	    ".transfer_function / .color_primaries, riempiti da "
	    "spa_format_video_raw_parse sul SPA_PARAM_Format del produttore\",\n"
	    "    \"⚠ sulla matrice\": \"alla cattura i pixel sono RGB: nessuna matrice "
	    "601/709 e' stata applicata da noi. La matrice la SCEGLIE F2.3 nel convertire "
	    "in YCbCr, e F2.6 deve confrontare con la stessa — un confronto fatto con la "
	    "matrice sbagliata misura la matrice\",\n"
	    "    \"valori_grezzi\": {\"color_range\": %u, \"color_matrix\": %u, "
	    "\"transfer_function\": %u, \"color_primaries\": %u}\n"
	    "  },\n",
	    bit_per_canale(p.formato.format), nome_colore(p.formato.format),
	    nome_range(p.formato.color_range), nome_matrice(p.formato.color_matrix),
	    nome_trasferimento(p.formato.transfer_function),
	    nome_primari(p.formato.color_primaries), p.formato.color_range,
	    p.formato.color_matrix, p.formato.transfer_function, p.formato.color_primaries);

	g_string_append(manifesto, "  \"buffer\": {\n    \"tipi_visti\": [");
	for (i = 0; i < p.quanti_tipi; i++)
		g_string_append_printf(manifesto, "%s\"%s\"", i ? ", " : "", nome_tipo(p.tipi_visti[i]));
	g_string_append_printf(manifesto,
	                       "],\n"
	                       "    \"distinti_riciclati\": %u,\n"
	                       "    \"chi_lo_dice\": \"PipeWire, spa_data.type del piano 0 di ogni "
	                       "buffer — chiesto in due posti (formato e SPA_PARAM_Buffers)\"\n"
	                       "  },\n",
	                       p.quanti_fd);

	g_string_append_printf(manifesto,
	                       "  \"fotogrammi\": {\n"
	                       "    \"minimo_dopo_la_scena_preteso\": %" PRIu64 ",\n"
	                       "    \"arrivati_in_tutto\": %" PRIu64 ",\n"
	                       "    \"prima_della_scena\": %" PRIu64 ",\n"
	                       "    \"dopo_la_scena\": %" PRIu64 ",\n"
	                       "    \"danno_pieno\": %" PRIu64 ",\n"
	                       "    \"danno_parziale\": %" PRIu64 ",\n"
	                       "    \"danno_assente\": %" PRIu64 ",\n"
	                       "    \"senza_header\": %" PRIu64 "\n"
	                       "  },\n",
	                       minimo_dopo_scena, p.arrivati, p.prima_della_scena, p.dopo_la_scena,
	                       p.danno_pieno, p.danno_parziale, p.danno_assente, p.senza_header);

	manifesto_fermo(manifesto, "primo", &p.primo, file_primo);
	manifesto_fermo(manifesto, "regime", &p.regime, file_regime);

	/*
	 * ⛔ LE AVVERTENZE STANNO NEL MANIFESTO, NON IN UN DOCUMENTO.
	 *
	 * Invariante I7: la protezione di un difetto noto sta nel programma, non in
	 * una riga che si puo' perdere.  Chi legge questo manifesto fra sei mesi non
	 * avra' letto `REVIEWER.md` §2, e la deduzione «MemFd dunque software» e'
	 * gia' costata due volte.
	 */
	g_string_append(manifesto,
	                "  \"avvertenze\": [\n"
	                "    \"⛔ E1 — il tipo di buffer NON dice dove Mutter renda. Un MemFd qui e' "
	                "la risposta a quel che ABBIAMO CHIESTO noi (servono i pixel leggibili), non "
	                "una scoperta sul compositore. LEZIONI.md §1.11.\",\n"
	                "    \"⛔ E1 — e nemmeno il contrario: un DMA-BUF non prova che si renda in "
	                "GPU. Un render node aperto e' necessario, non sufficiente.\",\n"
	                "    \"⚠ questo strumento NON misura il ritmo: copia due fotogrammi dentro la "
	                "richiamata di tempo reale, e un numero di fotogrammi al secondo che uscisse "
	                "da qui sarebbe falsato da noi. Il ritmo e' della fase 0 (36 ± 2) e della "
	                "fase 3.\",\n"
	                "    \"⚠ 'negoziato' e 'chiesto' sono due campi diversi apposta: la voce "
	                "12-bis di fasi/00-ambiente.md e' un'etichetta che dichiarava una misura che "
	                "il compositore non aveva mai onorato.\"\n"
	                "  ]\n}\n");

	if (!g_file_set_contents(file_json, manifesto->str, -1, &sbaglio))
	{
		fprintf(stderr, "⛔ non riesco a scrivere %s: %s\n", file_json, sbaglio->message);
		g_string_free(manifesto, TRUE);
		palco_smonta(palco);
		return 1;
	}
	g_string_free(manifesto, TRUE);

	printf("PRESA\t%s\t%s\t%s\t%" PRIu64 "\t%" PRIu64 "\t%s\n", etichetta, esito, file_json,
	       p.arrivati, p.dopo_la_scena,
	       p.quanti_tipi > 0 ? nome_tipo(p.tipi_visti[0]) : "NESSUNO");
	fprintf(stderr,
	        "  esito: %s\n"
	        "  arrivati %" PRIu64 " (prima della scena %" PRIu64 ", dopo %" PRIu64 ")\n"
	        "  danno: pieno %" PRIu64 ", parziale %" PRIu64 ", assente %" PRIu64 "\n"
	        "  buffer distinti riciclati: %u\n"
	        "  manifesto: %s\n",
	        esito, p.arrivati, p.prima_della_scena, p.dopo_la_scena, p.danno_pieno,
	        p.danno_parziale, p.danno_assente, p.quanti_fd, file_json);

	pw_thread_loop_lock(p.ciclo);
	pw_stream_disconnect(p.flusso);
	pw_stream_destroy(p.flusso);
	pw_thread_loop_unlock(p.ciclo);
	pw_thread_loop_stop(p.ciclo);
	pw_core_disconnect(p.nucleo);
	pw_context_destroy(p.contesto);
	pw_thread_loop_destroy(p.ciclo);
	palco_smonta(palco);
	g_free(p.primo.pixel);
	g_free(p.regime.pixel);
	g_free(p.guasto);
	return codice;
}
