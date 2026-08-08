#include "cattura.h"

#include <gio/gio.h>
#include <pipewire/pipewire.h>
#include <spa/buffer/meta.h>
#include <spa/param/video/format-utils.h>
#include <spa/utils/result.h>
#include <drm_fourcc.h>
#include <errno.h>
#include <poll.h>
#include <stdlib.h>

#include "registro.h"

/* Quanto si aspetta che il flusso arrivi a `paused`: e' il momento in cui la
 * negoziazione del formato e' avvenuta e si sa se Mutter ha accettato la misura
 * chiesta.  Senza questa attesa un rifiuto — «no more input formats» — sarebbe
 * silenzioso, e si manifesterebbe molto piu' tardi come schermo nero. */
#define ATTESA_AVVIO_S 10

/* Quante regioni danneggiate si portano al massimo.  Oltre, si dichiara che il
 * fotogramma vale tutto: e' il caso sicuro. */
#define REGIONI_MAX 16

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
	CatturaDmabuf su_dmabuf;
	CatturaFine su_fine;
	gpointer dati;

	enum pw_stream_state stato;
	char *guasto;
	gboolean fine_segnalata;
	gboolean primo_fotogramma;
	gboolean detto_il_tipo;
	gboolean vuole_dmabuf;
	/* La misura si propone come intervallo invece che come rettangolo fisso:
	 * vedi `cattura.h`, ed e' la differenza fra i due compositori. */
	gboolean misura_negoziabile;
	/* L'ultima misura CHIESTA — non quella confermata.  E' il termine di
	 * confronto della guardia contro il ciclo di rinegoziazione: vedi il riquadro
	 * sopra `cattura_ridimensiona`. */
	uint32_t chiesta_larghezza, chiesta_altezza;

	/* ---------------------------------------------------------------- *
	 * La spia dell'alternanza (R29, sesto punto).
	 *
	 * Risponde a una domanda sola: quando prendiamo un buffer, il
	 * compositore ha FINITO di disegnarci dentro?  Se no, ne codifichiamo
	 * il contenuto precedente — cioe' una schermata gia' passata, intera e
	 * pulita, che e' esattamente la forma del difetto misurato il 7 agosto.
	 *
	 * ⚠ SI CONTA, NON SI STAMPA.  Girano sul thread di PipeWire, che e' di
	 *   tempo reale: una riga di registro per fotogramma falserebbe la cosa
	 *   che si sta misurando.  Si dicono i primi, e poi un riassunto ogni
	 *   tanto.
	 * ---------------------------------------------------------------- */
	guint64 fotogrammi;          /* quanti ne sono arrivati                */
	guint64 fence_non_pronta;    /* quanti con il disegno ancora in corso  */
	guint64 fence_scaduta;       /* quanti in cui l'attesa non e' bastata  */
	guint64 danno_parziale;      /* quanti con danno che non copre tutto   */
	guint64 senza_intestazione;  /* quanti senza SPA_META_Header           */
	guint64 solo_cursore;        /* i buffer corrotti di §4.7 di kde.md    */
	int fd_visti[8];             /* i buffer del pool, per contarli        */
	guint quanti_fd;
	int attesa_fence_ms;         /* REMOTIX_FENCE_MS: 0 = misura e basta   */
	gboolean detto_solo_cursore;
};

/*
 * Il buffer e' pronto da leggere?
 *
 * Un DMA-BUF si puo' interrogare con `poll`: la sincronizzazione implicita
 * del kernel rende leggibile il descrittore SOLO quando chi disegna ha
 * finito.  Con timeout zero e' una domanda, non un'attesa — costa niente e
 * si puo' fare sul thread di tempo reale.
 *
 * Ritorna: 1 pronto, 0 non ancora, -1 non si sa (poll fallito).
 */
static int fence_pronta(int fd, int attesa_ms)
{
	struct pollfd p = { .fd = fd, .events = POLLIN };
	int esito;

	do
	{
		esito = poll(&p, 1, attesa_ms);
	} while (esito < 0 && errno == EINTR);

	if (esito < 0)
		return -1;
	return esito > 0 ? 1 : 0;
}

static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	Cattura *cattura = dati;

	diagnostica("stato del flusso di cattura: %s → %s%s%s", pw_stream_state_as_string(vecchio),
	            pw_stream_state_as_string(nuovo), errore ? " — " : "", errore ? errore : "");
	cattura->stato = nuovo;
	if (errore)
	{
		g_free(cattura->guasto);
		cattura->guasto = g_strdup(errore);
	}

	/*
	 * Il ciclo deve accorgersi da se' quando il flusso si stacca, e la
	 * condizione sullo stato VECCHIO non e' un dettaglio: all'avvio si parte da
	 * `unconnected`, e uscire li' sarebbe uscire prima di cominciare.
	 *
	 * Senza questo, un «Esci» dal menu di sistema lascerebbe il client
	 * attaccato a un'immagine congelata: chi legge non distinguerebbe «desktop
	 * fermo» da «non c'e' piu' niente da catturare», e sul registro non
	 * comparirebbe nulla.
	 */
	if ((vecchio == PW_STREAM_STATE_PAUSED || vecchio == PW_STREAM_STATE_STREAMING) &&
	    nuovo == PW_STREAM_STATE_UNCONNECTED && !cattura->fine_segnalata)
	{
		cattura->fine_segnalata = TRUE;
		informazione("il flusso di cattura si e' staccato");
		if (cattura->su_fine)
			cattura->su_fine(cattura->dati);
	}

	pw_thread_loop_signal(cattura->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Cattura *cattura = dati;
	uint32_t tipo, sottotipo;

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &tipo, &sottotipo) < 0)
		return;
	if (tipo != SPA_MEDIA_TYPE_video || sottotipo != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &cattura->formato) < 0)
	{
		avviso("formato di cattura non interpretabile");
		return;
	}

	cattura->formato_noto = TRUE;
	/* ⚠ QUESTA RIGA LA LEGGONO I BANCHI (prove/fase3.sh cerca qui la misura
	 *   negoziata): non le si aggiunge niente in coda, e non le si cambia la
	 *   testa.  Il 6 agosto averci messo il modificatore ha fatto estrarre «0x0»
	 *   come misura, e il controllo e' diventato rosso con il codice giusto —
	 *   che e' il difetto piu' costoso che un banco possa avere.
	 *
	 *   ⚠ Dice «Mutter» anche su KWin, ed e' una bugia che si tiene: il nome sta
	 *     dentro il pattern che due banchi cercano, e cambiarlo per esattezza
	 *     costerebbe due controlli rossi su codice giusto.  Chi legge il registro
	 *     ha la riga «compositore: …» in testa, che dice la verita'. */
	informazione("formato negoziato con Mutter: %ux%u, %s", cattura->formato.size.width,
	             cattura->formato.size.height,
	             cattura->formato.format == SPA_VIDEO_FORMAT_BGRx ? "BGRx" : "BGRA");
	diagnostica("modificatore del formato: 0x%" G_GINT64_MODIFIER "x",
	            (guint64) cattura->formato.modifier);

	/*
	 * ⛔ DICHIARARE IL MODIFICATORE NON BASTA: bisogna anche dire che si sanno
	 *    ricevere buffer di tipo DMA-BUF.
	 *
	 *    Il tipo dei dati si concorda con `SPA_PARAM_Buffers`, non con il
	 *    formato; chi tace lascia il valore predefinito, che e' la memoria
	 *    ordinaria — e il risultato e' una negoziazione andata a buon fine con
	 *    dentro esattamente quel che si voleva evitare, senza alcun errore.
	 *    Si elencano tutti e tre i tipi, DMA-BUF per primo: se l'aggancio non
	 *    riesce si ricade sulla memoria invece di restare senza immagine.
	 *
	 * ⛔ E IL BIT DEL DMA-BUF SI ACCENDE SOLO SE LO SI SA LEGGERE.  E' la stessa
	 *    regola del formato, dall'altro lato: qui la si applicava sempre, e
	 *    finche' il modificatore taceva non faceva danno.  Da quando la strada si
	 *    puo' girare a cattura viva (`cattura_dmabuf`) farebbe danno eccome —
	 *    tornare in memoria lasciando acceso il bit significa lasciare a Mutter la
	 *    facolta' di consegnare ancora DMA-BUF, che in memoria nessuno guarda.
	 */
	{
		uint8_t spazio[1024];
		struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
		const struct spa_pod *parametri[3];
		int tipi = (1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr);

		if (cattura->vuole_dmabuf)
			tipi |= (1 << SPA_DATA_DmaBuf);

		parametri[0] = spa_pod_builder_add_object(
		    &costruttore, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
		    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
		    SPA_POD_CHOICE_FLAGS_Int(tipi));

		/*
		 * ⛔ I METADATI SI CHIEDONO, O NON ARRIVANO.  Fino al 7 agosto 2026
		 *    `cattura.c` non ne chiedeva NESSUNO — il riferimento chiede sempre
		 *    `Header` e `Cursor` (§11.2 di gnome-remote-desktop.md) — e senza di
		 *    loro il produttore non ha modo di dirci nulla del fotogramma: ne'
		 *    quale sia (`seq`), ne' quanta parte abbia ridisegnato (`VideoDamage`).
		 *
		 *    In memoria l'omissione non fa danno, perche' Mutter ricopia ogni volta
		 *    il fotogramma intero.  Sulla strada del DMA-BUF invece si prende un
		 *    buffer del pool per un fotogramma intero senza avere modo di sapere se
		 *    lo e' davvero: e' la radice dei due sospetti di R29, sesto punto.
		 *
		 * ⚠ Chiedere un metadato NON obbliga il produttore a darlo: chi legge deve
		 *   reggere la sua assenza.  Per questo qui si chiedono e basta, e chi li
		 *   consuma controlla sempre il puntatore.
		 */
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

		pw_stream_update_params(cattura->flusso, parametri, 3);
	}

	pw_thread_loop_signal(cattura->ciclo, false);
}

/*
 * La spia dell'alternanza: guarda il fotogramma PRIMA di consegnarlo.
 *
 * Tre domande, e nessuna delle tre si poteva porre finche' non si chiedevano i
 * metadati:
 *
 *   1. quale buffer del pool e' arrivato    → `fd`, e quanti distinti se ne vedono
 *   2. che fotogramma dice di essere        → `seq` dell'intestazione
 *   3. il disegno e' finito?                → il `poll` sul DMA-BUF
 *
 * La terza e' quella che decide fra i due sospetti di R29: un buffer preso
 * mentre il compositore ci sta ancora disegnando contiene ancora il fotogramma
 * di prima — intero e pulito, che e' proprio quel che si vede alternarsi.
 */
static void spia_fotogramma(Cattura *cattura, struct pw_buffer *pacco, struct spa_data *piano)
{
	struct spa_meta_header *intestazione;
	struct spa_meta *danno;
	int pronta = -1;
	gboolean copre_tutto = TRUE;
	guint regioni = 0;

	cattura->fotogrammi++;

	intestazione = spa_buffer_find_meta_data(pacco->buffer, SPA_META_Header, sizeof *intestazione);
	if (!intestazione)
		cattura->senza_intestazione++;

	danno = spa_buffer_find_meta(pacco->buffer, SPA_META_VideoDamage);
	if (danno)
	{
		struct spa_meta_region *regione;

		copre_tutto = FALSE;
		spa_meta_for_each(regione, danno)
		{
			if (!spa_meta_region_is_valid(regione))
				break;
			regioni++;
			if (regione->region.position.x == 0 && regione->region.position.y == 0 &&
			    regione->region.size.width >= cattura->formato.size.width &&
			    regione->region.size.height >= cattura->formato.size.height)
				copre_tutto = TRUE;
		}
		if (!copre_tutto)
			cattura->danno_parziale++;
	}

	if (piano->type == SPA_DATA_DmaBuf)
	{
		gboolean nuovo = TRUE;

		pronta = fence_pronta((int) piano->fd, 0);
		if (pronta == 0)
		{
			cattura->fence_non_pronta++;
			/*
			 * ⛔ SI ASPETTA CHE IL DISEGNO FINISCA, e su KWin non e' facoltativo.
			 *
			 *    KWin fa `glFlush()` e non `glFinish()` — che fa solo su NVidia e
			 *    llvmpipe, cioe' dove la fence implicita e' rotta
			 *    (`screencaststream.cpp:637-655`).  `glFlush` SOTTOMETTE il lavoro
			 *    alla scheda, non aspetta che sia finito: misurato l'8 agosto
			 *    2026, su questa macchina **830 buffer su 830** arrivano con il
			 *    disegno in corso (`kde.md` §4.8).  Codificarli significa
			 *    codificare quel che c'era prima.
			 *
			 *    Il costo e' una manciata di millisecondi su un thread di tempo
			 *    reale, e si paga volentieri: l'alternativa e' un'immagine
			 *    sbagliata che non produce alcun errore.
			 *
			 * ⚠ `REMOTIX_FENCE_MS=0` toglie l'attesa e lascia il solo conteggio:
			 *   serve a rimisurare quanto spesso capita, non all'uso normale.
			 */
			if (cattura->attesa_fence_ms > 0 &&
			    fence_pronta((int) piano->fd, cattura->attesa_fence_ms) != 1)
				cattura->fence_scaduta++;
		}

		for (guint i = 0; i < cattura->quanti_fd; i++)
			if (cattura->fd_visti[i] == (int) piano->fd)
				nuovo = FALSE;
		if (nuovo && cattura->quanti_fd < G_N_ELEMENTS(cattura->fd_visti))
			cattura->fd_visti[cattura->quanti_fd++] = (int) piano->fd;
	}

	/* I primi dieci per esteso, poi un riassunto ogni dieci secondi di
	 * fotogrammi: il thread e' di tempo reale, e una riga per fotogramma
	 * falserebbe quel che si sta misurando. */
	if (cattura->fotogrammi <= 10)
		diagnostica("fotogramma %" G_GUINT64_FORMAT ": buffer fd %d, seq %" G_GUINT64_FORMAT
		            ", disegno %s, danno %u regioni%s",
		            cattura->fotogrammi, (int) piano->fd,
		            intestazione ? (guint64) intestazione->seq : (guint64) 0,
		            pronta < 0 ? "non interrogabile" : pronta ? "finito" : "ANCORA IN CORSO",
		            regioni, danno ? (copre_tutto ? ", copre tutto" : ", PARZIALE") : " (assente)");
	else if (cattura->fotogrammi % 300 == 0)
		diagnostica("cattura su %" G_GUINT64_FORMAT " fotogrammi: %u buffer distinti, disegno non "
		            "finito %" G_GUINT64_FORMAT " (attesa scaduta %" G_GUINT64_FORMAT
		            "), danno parziale %" G_GUINT64_FORMAT ", senza intestazione %" G_GUINT64_FORMAT
		            ", di solo cursore %" G_GUINT64_FORMAT,
		            cattura->fotogrammi, cattura->quanti_fd, cattura->fence_non_pronta,
		            cattura->fence_scaduta, cattura->danno_parziale, cattura->senza_intestazione,
		            cattura->solo_cursore);
}

static void su_processo(void *dati)
{
	Cattura *cattura = dati;
	struct pw_buffer *pacco;
	struct spa_data *piano;
	uint32_t passo, altezza;
	size_t disponibili;

	pacco = pw_stream_dequeue_buffer(cattura->flusso);
	if (!pacco)
		return;

	if (pacco->buffer->n_datas == 0)
		goto restituisci;
	piano = &pacco->buffer->datas[0];

	/* Che cosa ci sta consegnando Mutter, detto una volta e per esteso: e' la
	 * differenza fra una cattura a copia zero e una che passa dalla memoria, e
	 * non si deduce da nessun altro segno. */
	if (!cattura->detto_il_tipo)
	{
		cattura->detto_il_tipo = TRUE;
		informazione("i fotogrammi arrivano come %s (%u piani)",
		             piano->type == SPA_DATA_DmaBuf     ? "DMA-BUF"
		             : piano->type == SPA_DATA_MemFd    ? "memoria condivisa (MemFd)"
		             : piano->type == SPA_DATA_MemPtr   ? "memoria ordinaria (MemPtr)"
		                                                : "tipo sconosciuto",
		             pacco->buffer->n_datas);
	}
	if (!piano->chunk)
		goto restituisci;

	/*
	 * ⛔ IL BUFFER PUO' NON CONTENERE UN FOTOGRAMMA, E LO DICE UN SOLO BIT.
	 *
	 *    Su KWin, con il cursore in modo METADATO — che e' il modo giusto per
	 *    RDP, perche' il puntatore ha un canale suo — OGNI MOVIMENTO DEL MOUSE
	 *    produce un buffer senza `render()`: dentro ci sono i pixel stantii di
	 *    due-quattro fotogrammi prima, e l'unica indicazione e'
	 *    `chunk->flags = SPA_CHUNK_FLAG_CORRUPTED`
	 *    (`kwin/src/plugins/screencast/screencaststream.cpp:659-664`, con il
	 *    commento che spiega che «corrupted» qui significa «non guardare il
	 *    contenuto»).
	 *
	 *    Un consumatore che ignora quel flag mostra un fotogramma vecchio A OGNI
	 *    MOVIMENTO DEL MOUSE — cioe' lo stesso sintomo che su GNOME ci ha fatto
	 *    spegnere la copia zero (R29), da una causa diversa.  kpipewire lo
	 *    gestisce (`pipewiresourcestream.cpp:618-621`); il nostro banco no, ed e'
	 *    la ragione per cui le sue misure di fps si gonfiano muovendo il mouse
	 *    (`kde.md` §4.7).
	 *
	 * ⚠ Si scarta il FOTOGRAMMA, non il buffer: il metadato del cursore che
	 *   viaggia insieme resta valido, ed e' anzi l'unica cosa per cui quel buffer
	 *   e' stato spedito.  Quando il canale puntatore ci sara', si leggera' qui.
	 */
	if (piano->chunk->flags & SPA_CHUNK_FLAG_CORRUPTED)
	{
		cattura->solo_cursore++;
		if (!cattura->detto_solo_cursore)
		{
			cattura->detto_solo_cursore = TRUE;
			diagnostica("arrivano buffer di solo cursore (SPA_CHUNK_FLAG_CORRUPTED): li scarto, "
			            "i pixel che portano sono vecchi");
		}
		goto restituisci;
	}
	{
		/* La stessa cosa dall'altra parte: il produttore puo' marcare corrotta
		 * l'INTESTAZIONE invece del blocco.  In KWin e' il caso patologico «buffer
		 * senza user_data» (`screencaststream.cpp:695-701`), che non dovrebbe mai
		 * capitare — e proprio per questo va scartato invece che ignorato. */
		struct spa_meta_header *testa =
		    spa_buffer_find_meta_data(pacco->buffer, SPA_META_Header, sizeof *testa);

		if (testa && (testa->flags & SPA_META_HEADER_FLAG_CORRUPTED))
		{
			cattura->solo_cursore++;
			goto restituisci;
		}
	}

	spia_fotogramma(cattura, pacco, piano);

	/* Lo stride autorevole e' questo, non `larghezza * 4`. */
	passo = (uint32_t) MAX(0, piano->chunk->stride);
	if (passo == 0)
		goto restituisci;

	/*
	 * Il percorso a copia zero: il fotogramma non si legge, si CONSEGNA.
	 *
	 * ⛔ E VA GUARDATO PRIMA DEL PUNTATORE.  Un DMA-BUF non ha `data`: e' un
	 *    descrittore di memoria che vive sulla scheda, e il puntatore resta
	 *    NULL.  Il controllo «niente puntatore, niente fotogramma» — giusto per
	 *    la memoria ordinaria — qui scarterebbe tutto, in silenzio: il registro
	 *    direbbe «i fotogrammi arrivano come DMA-BUF» e poi piu' niente.
	 *    Misurato il 6 agosto, ed e' costato un giro di prove.
	 *
	 * ⛔ E si consegna dentro la richiamata, non dopo: appena si torna di qui il
	 *    buffer va riaccodato a PipeWire, e il descrittore non vale piu'.  Chi
	 *    lo riceve deve quindi averne gia' fatto qualcosa — nel nostro caso
	 *    importarlo sulla scheda, che costa una chiamata e nessuna copia.
	 */
	if (piano->type == SPA_DATA_DmaBuf && cattura->su_dmabuf)
	{
		CatturaRegione danno[REGIONI_MAX];
		guint quante = 0;
		struct spa_meta *meta;

		if (cattura->primo_fotogramma)
		{
			cattura->primo_fotogramma = FALSE;
			informazione("primo fotogramma dal desktop: %ux%u, passo %u (a copia zero)",
			             cattura->formato.size.width, cattura->formato.size.height, passo);
		}

		/*
		 * Il danno, che qui e' l'unica cosa che rende leggibile il buffer.
		 *
		 * Si sbaglia dalla parte sicura: se le regioni sono piu' di quante se ne
		 * portano, si dichiara «tutto» invece di consegnarne una parte — meglio
		 * una copia in piu' che un fotogramma composto a meta'.
		 */
		meta = spa_buffer_find_meta(pacco->buffer, SPA_META_VideoDamage);
		if (meta)
		{
			struct spa_meta_region *regione;

			spa_meta_for_each(regione, meta)
			{
				if (!spa_meta_region_is_valid(regione))
					break;
				if (quante >= REGIONI_MAX)
				{
					quante = 0;
					break;
				}
				danno[quante].x = (uint32_t) MAX(0, regione->region.position.x);
				danno[quante].y = (uint32_t) MAX(0, regione->region.position.y);
				danno[quante].larghezza = regione->region.size.width;
				danno[quante].altezza = regione->region.size.height;
				quante++;
			}
		}

		cattura->su_dmabuf((int) piano->fd, (uint32_t) piano->chunk->offset, passo,
		                   cattura->formato.modifier, cattura->formato.size.width,
		                   cattura->formato.size.height, danno, quante, cattura->dati);
		goto restituisci;
	}

	/* Da qui in giu' si legge la memoria, e senza puntatore non c'e' niente da
	 * leggere. */
	if (!piano->data || piano->chunk->size == 0)
		goto restituisci;

	altezza = cattura->formato.size.height;
	disponibili = piano->maxsize > (uint32_t) piano->chunk->offset
	                  ? piano->maxsize - (uint32_t) piano->chunk->offset
	                  : 0;
	if ((size_t) passo * altezza > disponibili)
		altezza = (uint32_t) (disponibili / passo);
	if (altezza == 0)
		goto restituisci;

	if (cattura->primo_fotogramma)
	{
		cattura->primo_fotogramma = FALSE;
		informazione("primo fotogramma dal desktop: %ux%u, passo %u",
		             cattura->formato.size.width, altezza, passo);
	}

	cattura->su_fotogramma((const uint8_t *) piano->data + piano->chunk->offset, passo,
	                       cattura->formato.size.width, altezza, cattura->dati);

restituisci:
	pw_stream_queue_buffer(cattura->flusso, pacco);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/*
 * Il formato che REMOTIX dichiara di saper leggere.
 *
 * Solo formati a 32 bit con i canali nell'ordine che il codificatore si
 * aspetta.  Elencarne altri sarebbe un difetto silenzioso: nessun punto della
 * catena guarda il formato davvero negoziato, quindi se Mutter scegliesse una
 * variante RGB, rosso e blu uscirebbero scambiati senza alcun errore.
 *
 * ⚠ SULLA MISURA C'E' UNA DIVERGENZA DA MISURARE (§11.1 di
 *   gnome-remote-desktop.md).  REMOTIX ha misurato che un rettangolo SINGOLO
 *   viene respinto da Mutter con «no more input formats» e ha dovuto dichiarare
 *   un intervallo chiuso (min = pref = max); il riferimento dichiara un valore
 *   singolo e funziona.  Le spiegazioni possibili sono tre: la versione di
 *   Mutter, `is-platform: true` in `RecordVirtual` — che REMOTIX ora dichiara —
 *   oppure il fatto che il riferimento propone due formati e Mutter negozia sul
 *   secondo.
 *
 *   Si parte quindi dalla forma pulita, il valore singolo, e si tiene
 *   l'intervallo chiuso a portata di variabile d'ambiente
 *   (`REMOTIX_MISURA_INTERVALLO=1`) per poterli confrontare senza ricompilare.
 *   Quando la misura sara' fatta, questa nota va sostituita dall'esito.
 */
/*
 * I due estremi dell'intervallo, quando la misura si NEGOZIA.
 *
 * Sono i limiti che KWin 6.8 impone al ridimensionamento per negoziazione
 * (`kde.md` §8.2): dichiararli piu' larghi non serve a niente, e dichiararli
 * piu' stretti significherebbe rifiutare misure che il compositore accetta.
 */
#define MISURA_MINIMA 200u
#define MISURA_MASSIMA 10000u

static const struct spa_pod *formato_richiesto(struct spa_pod_builder *costruttore,
                                               uint32_t larghezza, uint32_t altezza,
                                               uint32_t fotogrammi_al_secondo,
                                               gboolean negoziabile)
{
	struct spa_rectangle misura = SPA_RECTANGLE(larghezza, altezza);
	struct spa_rectangle minima = SPA_RECTANGLE(MISURA_MINIMA, MISURA_MINIMA);
	struct spa_rectangle massima = SPA_RECTANGLE(MISURA_MASSIMA, MISURA_MASSIMA);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction cadenza_minima = SPA_FRACTION(1, 1);
	struct spa_fraction cadenza_massima = SPA_FRACTION(MAX(1u, fotogrammi_al_secondo), 1);
	const char *intervallo = g_getenv("REMOTIX_MISURA_INTERVALLO");

	if (negoziabile)
		return spa_pod_builder_add_object(
		    costruttore, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
		    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
		    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format,
		    SPA_POD_CHOICE_ENUM_Id(3, SPA_VIDEO_FORMAT_BGRx, SPA_VIDEO_FORMAT_BGRx,
		                           SPA_VIDEO_FORMAT_BGRA),
		    SPA_FORMAT_VIDEO_size, SPA_POD_CHOICE_RANGE_Rectangle(&misura, &minima, &massima),
		    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza), SPA_FORMAT_VIDEO_maxFramerate,
		    SPA_POD_CHOICE_RANGE_Fraction(&cadenza_massima, &cadenza_minima, &cadenza_massima));

	if (intervallo && *intervallo == '1')
	{
		diagnostica("misura dichiarata come intervallo chiuso");
		return spa_pod_builder_add_object(
		    costruttore, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
		    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
		    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format,
		    SPA_POD_CHOICE_ENUM_Id(3, SPA_VIDEO_FORMAT_BGRx, SPA_VIDEO_FORMAT_BGRx,
		                           SPA_VIDEO_FORMAT_BGRA),
		    SPA_FORMAT_VIDEO_size, SPA_POD_CHOICE_RANGE_Rectangle(&misura, &misura, &misura),
		    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza), SPA_FORMAT_VIDEO_maxFramerate,
		    SPA_POD_CHOICE_RANGE_Fraction(&cadenza_massima, &cadenza_minima, &cadenza_massima));
	}

	return spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format,
	    SPA_POD_CHOICE_ENUM_Id(3, SPA_VIDEO_FORMAT_BGRx, SPA_VIDEO_FORMAT_BGRx,
	                           SPA_VIDEO_FORMAT_BGRA),
	    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura), SPA_FORMAT_VIDEO_framerate,
	    SPA_POD_Fraction(&cadenza), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&cadenza_massima, &cadenza_minima, &cadenza_massima));
}

/*
 * La stessa proposta, ma con i MODIFICATORI dichiarati: e' il modo con cui si
 * chiede a Mutter un DMA-BUF invece di un buffer in memoria ordinaria.
 *
 * §7.3 di REFERENCE.md dice l'altra meta' della regola: tacendo sul campo
 * `modifier` si resta in memoria ordinaria, ed e' quello che REMOTIX ha fatto
 * fino alla fase 8.  Dichiarandolo si avvia la negoziazione DMA-BUF, e va
 * dichiarato con `MANDATORY | DONT_FIXATE`, altrimenti il valore lo sceglie
 * PipeWire invece di lasciarlo concordare con chi alloca.
 *
 * `DRM_FORMAT_MOD_INVALID` significa «la disposizione la decidi tu e me la
 * dici»: e' la forma piu' larga, e ora che dentro la VM c'e' una sola scheda —
 * quella su cui disegna Mutter ed e' la stessa che codifica — non c'e' il
 * rischio di un buffer di un altro dispositivo.
 *
 * ⚠ La proposta con i modificatori si offre PER PRIMA e quella senza resta in
 *   elenco: se la negoziazione DMA-BUF non va a buon fine si ricade sulla
 *   memoria ordinaria invece di restare senza immagine — che e' la stessa
 *   prudenza del riferimento (§11.2 di gnome-remote-desktop.md).
 */
static const struct spa_pod *formato_dmabuf(struct spa_pod_builder *costruttore,
                                            uint32_t larghezza, uint32_t altezza,
                                            uint32_t fotogrammi_al_secondo, gboolean negoziabile)
{
	struct spa_rectangle misura = SPA_RECTANGLE(larghezza, altezza);
	struct spa_rectangle minima = SPA_RECTANGLE(MISURA_MINIMA, MISURA_MINIMA);
	struct spa_rectangle massima = SPA_RECTANGLE(MISURA_MASSIMA, MISURA_MASSIMA);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction cadenza_minima = SPA_FRACTION(1, 1);
	struct spa_fraction cadenza_massima = SPA_FRACTION(MAX(1u, fotogrammi_al_secondo), 1);
	struct spa_pod_frame cornice[2];

	spa_pod_builder_push_object(costruttore, &cornice[0], SPA_TYPE_OBJECT_Format,
	                            SPA_PARAM_EnumFormat);
	spa_pod_builder_add(costruttore, SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	                    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
	                    SPA_FORMAT_VIDEO_format,
	                    SPA_POD_CHOICE_ENUM_Id(3, SPA_VIDEO_FORMAT_BGRx, SPA_VIDEO_FORMAT_BGRx,
	                                           SPA_VIDEO_FORMAT_BGRA),
	                    0);

	/*
	 * ⛔ LINEARE PER PRIMO, ED E' UN REGALO DI KPIPEWIRE.
	 *
	 *    Per la codifica in GPU si chiede **solo** `DRM_FORMAT_MOD_LINEAR`
	 *    (`kpipewire/src/vaapiutils.cpp:119-135`): RadeonSI RIFIUTA i buffer con
	 *    DCC, e iHD — il driver delle Intel, cioe' la scheda che il prodotto usa
	 *    — li ACCETTA e poi forza LINEAR internamente.  Cioe' accetta e sbaglia
	 *    in silenzio, che e' la nostra forma di guasto preferita (R27, R30).
	 *    Giorni risparmiati, e non sono nostri.
	 *
	 *    Il primo valore dell'enum e' il PREDEFINITO: mettendo li' il lineare, se
	 *    il compositore ce l'ha in elenco lo prende.  `INVALID` resta come
	 *    seconda scelta — significa «la disposizione la decidi tu e me la dici» —
	 *    perche' un DMA-BUF con un modificatore che il driver sa leggere e' molto
	 *    meglio del ripiego in memoria, che a 4K dimezza i fotogrammi.
	 */
	spa_pod_builder_prop(costruttore, SPA_FORMAT_VIDEO_modifier,
	                     SPA_POD_PROP_FLAG_MANDATORY | SPA_POD_PROP_FLAG_DONT_FIXATE);
	spa_pod_builder_push_choice(costruttore, &cornice[1], SPA_CHOICE_Enum, 0);
	spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_LINEAR);
	spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_LINEAR);
	spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_INVALID);
	spa_pod_builder_pop(costruttore, &cornice[1]);

	if (negoziabile)
		spa_pod_builder_add(costruttore, SPA_FORMAT_VIDEO_size,
		                    SPA_POD_CHOICE_RANGE_Rectangle(&misura, &minima, &massima), 0);
	else
		spa_pod_builder_add(costruttore, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura), 0);

	spa_pod_builder_add(costruttore, SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza),
	                    SPA_FORMAT_VIDEO_maxFramerate,
	                    SPA_POD_CHOICE_RANGE_Fraction(&cadenza_massima, &cadenza_minima,
	                                                  &cadenza_massima),
	                    0);
	return spa_pod_builder_pop(costruttore, &cornice[0]);
}

Cattura *cattura_avvia(uint32_t nodo, uint32_t larghezza, uint32_t altezza,
                       uint32_t fotogrammi_al_secondo, gboolean misura_negoziabile,
                       CatturaFotogramma su_fotogramma, CatturaDmabuf su_dmabuf,
                       CatturaFine su_fine, gpointer dati, GError **sbaglio)
{
	static gsize inizializzato = 0;
	Cattura *cattura = g_new0(Cattura, 1);
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[2];
	uint32_t n_parametri;
	gint64 scadenza;

	if (g_once_init_enter(&inizializzato))
	{
		pw_init(NULL, NULL);
		g_once_init_leave(&inizializzato, 1);
	}

	cattura->su_fotogramma = su_fotogramma;
	cattura->su_dmabuf = su_dmabuf;
	cattura->su_fine = su_fine;
	cattura->dati = dati;
	cattura->primo_fotogramma = TRUE;
	cattura->vuole_dmabuf = su_dmabuf != NULL;
	cattura->misura_negoziabile = misura_negoziabile;
	cattura->chiesta_larghezza = larghezza;
	cattura->chiesta_altezza = altezza;

	/*
	 * Quanto si aspetta che il compositore finisca di disegnare, in ms.
	 *
	 * ⛔ IL PREDEFINITO E' «ASPETTA», e il 7 agosto era il contrario.  Allora si
	 *    misurava soltanto, perche' su Mutter aspettare la fence implicita e' un
	 *    vicolo cieco gia' percorso (`LEZIONI.md` §8): li' il difetto e' che il
	 *    buffer e' un «diff», non che il disegno sia in corso.
	 *
	 *    Su KWin e' l'opposto: i fotogrammi sono INTERI (`kde.md` §4.6) e l'unica
	 *    cosa che manca e' l'attesa — KWin fa `glFlush` e non `glFinish`, e l'8
	 *    agosto 2026 sono stati contati 830 buffer su 830 arrivati col disegno in
	 *    corso.  Non aspettare significa codificare il fotogramma di prima.
	 *
	 * Il tetto: un fotogramma a 60 al secondo dura 17 ms, e cinquanta sono tre
	 * fotogrammi.  Non si aspetta per sempre perche' un descrittore che non
	 * diventa mai leggibile fermerebbe la cattura invece di degradarla, e le
	 * scadenze si contano — se comparissero, sarebbero una misura, non un
	 * dettaglio.
	 */
	cattura->attesa_fence_ms = 50;
	if (g_getenv("REMOTIX_FENCE_MS"))
		cattura->attesa_fence_ms = atoi(g_getenv("REMOTIX_FENCE_MS"));
	diagnostica("attesa del disegno del compositore: %d ms%s", cattura->attesa_fence_ms,
	            cattura->attesa_fence_ms > 0 ? "" : " (spenta: si conta e basta)");

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

	cattura->flusso = pw_stream_new(
	    cattura->nucleo, "remotix-cattura",
	    pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY, "Capture",
	                      PW_KEY_MEDIA_ROLE, "Screen", NULL));
	if (!cattura->flusso)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "flusso PipeWire non creato");
		goto guasto;
	}
	pw_stream_add_listener(cattura->flusso, &cattura->gancio, &eventi, cattura);

	/*
	 * ⛔ IL DMA-BUF SI CHIEDE SOLO SE C'E' CHI LO SA CONSUMARE.
	 *
	 *    Chiederlo e non saperlo leggere non da' un errore: la negoziazione
	 *    riesce, i fotogrammi arrivano come DMA-BUF, e chi si aspetta un
	 *    puntatore li scarta tutti — cioe' schermo fermo, senza una riga di
	 *    registro che lo spieghi.  Misurato il 6 agosto, ed e' il motivo per cui
	 *    questa strada sta dietro un interruttore finche' l'importazione nel
	 *    codificatore non e' finita.
	 */
	n_parametri = 0;
	if (cattura->vuole_dmabuf)
		parametri[n_parametri++] = formato_dmabuf(&costruttore, larghezza, altezza,
		                                          fotogrammi_al_secondo, misura_negoziabile);
	parametri[n_parametri++] = formato_richiesto(&costruttore, larghezza, altezza,
	                                             fotogrammi_al_secondo, misura_negoziabile);
	if (pw_stream_connect(cattura->flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, n_parametri) < 0)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "aggancio al nodo %u fallito", nodo);
		goto guasto;
	}

	/* Si aspetta la negoziazione: e' l'unico punto in cui un rifiuto del
	 * formato si vede subito invece di diventare uno schermo nero piu' tardi. */
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (cattura->stato != PW_STREAM_STATE_PAUSED &&
	       cattura->stato != PW_STREAM_STATE_STREAMING &&
	       cattura->stato != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(cattura->ciclo, 1);
	pw_thread_loop_unlock(cattura->ciclo);

	if (cattura->stato == PW_STREAM_STATE_ERROR)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "cattura rifiutata da Mutter: %s",
		            cattura->guasto ? cattura->guasto : "senza spiegazione");
		goto guasto;
	}
	if (cattura->stato != PW_STREAM_STATE_PAUSED && cattura->stato != PW_STREAM_STATE_STREAMING)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "la cattura non ha dato segno di vita entro %d secondi", ATTESA_AVVIO_S);
		goto guasto;
	}

	informazione("cattura avviata sul nodo %u", nodo);
	return cattura;

guasto:
	cattura_ferma(cattura);
	return NULL;
}

void cattura_misura_negoziata(const Cattura *cattura, uint32_t *larghezza, uint32_t *altezza)
{
	*larghezza = cattura->formato_noto ? cattura->formato.size.width : 0;
	*altezza = cattura->formato_noto ? cattura->formato.size.height : 0;
}

/*
 * Rimanda a Mutter la proposta di formato e aspetta che la confermi.
 *
 * E' la porta unica del ridimensionamento e del cambio di strada: le due cose
 * viaggiano nella stessa proposta — misura e modificatori stanno nello stesso
 * `EnumFormat` — e tenerle in due funzioni diverse significherebbe due copie
 * della stessa attesa, che e' la parte delicata.
 *
 * Va chiamata con il lucchetto del ciclo LIBERO: se lo prende lei.
 */
static gboolean rinegozia(Cattura *cattura, uint32_t larghezza, uint32_t altezza,
                          uint32_t fotogrammi_al_secondo, uint32_t *confermata_larghezza,
                          uint32_t *confermata_altezza, GError **sbaglio)
{
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[2];
	uint32_t n_parametri;
	gint64 scadenza;
	gboolean arrivata;

	pw_thread_loop_lock(cattura->ciclo);

	/*
	 * Si dimentica il formato di prima PRIMA di chiedere quello nuovo.
	 *
	 * Senza, l'attesa qui sotto troverebbe subito vera la condizione se la
	 * misura chiesta fosse quella corrente — e soprattutto non saprebbe
	 * distinguere «Mutter ha confermato» da «Mutter non ha ancora risposto».
	 * Il campo si tocca con il lucchetto del ciclo preso: e' lo stesso che
	 * PipeWire tiene mentre chiama `su_parametri`.
	 */
	cattura->formato_noto = FALSE;

	n_parametri = 0;
	if (cattura->vuole_dmabuf)
		parametri[n_parametri++] = formato_dmabuf(&costruttore, larghezza, altezza,
		                                          fotogrammi_al_secondo,
		                                          cattura->misura_negoziabile);
	parametri[n_parametri++] = formato_richiesto(&costruttore, larghezza, altezza,
	                                             fotogrammi_al_secondo,
	                                             cattura->misura_negoziabile);
	if (pw_stream_update_params(cattura->flusso, parametri, n_parametri) < 0)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "PipeWire ha rifiutato la misura %ux%u", larghezza, altezza);
		return FALSE;
	}

	/*
	 * Si aspetta UNA conferma, non LA conferma.
	 *
	 * Fino al 7 agosto qui si aspettava esattamente la misura chiesta, e con
	 * Mutter e' giusto: chi non la conferma non la fara' mai.  Su KWin sarebbe un
	 * difetto — il compositore risponde con la PROPRIA misura, che e' la risposta
	 * normale finche' non arriva la 6.8 — e si andrebbe a sbattere contro i dieci
	 * secondi del tetto a ogni tentativo.  Si aspetta quindi che il formato
	 * arrivi, e chi ha chiamato giudica.
	 */
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (TRUE)
	{
		arrivata = cattura->formato_noto;
		if (arrivata || cattura->stato == PW_STREAM_STATE_ERROR ||
		    cattura->stato == PW_STREAM_STATE_UNCONNECTED || g_get_monotonic_time() >= scadenza)
			break;
		pw_thread_loop_timed_wait(cattura->ciclo, 1);
	}
	if (arrivata)
	{
		*confermata_larghezza = cattura->formato.size.width;
		*confermata_altezza = cattura->formato.size.height;
	}
	pw_thread_loop_unlock(cattura->ciclo);

	if (!arrivata)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "il compositore non ha confermato nessun formato entro %d secondi dopo la "
		            "richiesta di %ux%u",
		            ATTESA_AVVIO_S, larghezza, altezza);
		return FALSE;
	}

	return TRUE;
}

/*
 * ⛔ LA GUARDIA CHE RENDE LA RINEGOZIAZIONE SICURA, E NON E' UN'OTTIMIZZAZIONE.
 *
 *    Chiedere la misura che si e' gia' chiesta mette in moto un cambio di
 *    formato, che a sua volta richiama chi chiede la misura, che richiede…  Il
 *    difetto non e' nostro e non e' un'ipotesi: e' stato TROVATO DA ALTRI
 *    durante la revisione di `kwin!7932`, cioe' proprio del lavoro che portera'
 *    il ridimensionamento in 6.8 — «the ScreencastLayer gets destroyed/recreated
 *    many times per session, PipeWire toggles streaming ↔ paused repeatedly, and
 *    video freezes intermittently».  La cura, dai due lati, e' una riga:
 *    kpipewire la applica in `pipewiresourcestream.cpp:467-475`, KWin in
 *    `outputscreencastsource.cpp:170-181`.  (`kde.md` §8.2-bis)
 *
 *    Chi la dimentica NON vede il difetto su Trixie, dove il ridimensionamento
 *    non funziona affatto, e lo scopre il giorno dell'aggiornamento a KWin 6.8.
 */
gboolean cattura_ridimensiona(Cattura *cattura, uint32_t larghezza, uint32_t altezza,
                              uint32_t fotogrammi_al_secondo, uint32_t *confermata_larghezza,
                              uint32_t *confermata_altezza, GError **sbaglio)
{
	uint32_t chiesta_l, chiesta_a;

	pw_thread_loop_lock(cattura->ciclo);
	chiesta_l = cattura->chiesta_larghezza;
	chiesta_a = cattura->chiesta_altezza;
	pw_thread_loop_unlock(cattura->ciclo);

	if (chiesta_l == larghezza && chiesta_a == altezza)
	{
		cattura_misura_negoziata(cattura, confermata_larghezza, confermata_altezza);
		diagnostica("la misura %ux%u e' gia' quella chiesta: non si rinegozia", larghezza,
		            altezza);
		return TRUE;
	}

	if (!rinegozia(cattura, larghezza, altezza, fotogrammi_al_secondo, confermata_larghezza,
	               confermata_altezza, sbaglio))
		return FALSE;

	pw_thread_loop_lock(cattura->ciclo);
	cattura->chiesta_larghezza = larghezza;
	cattura->chiesta_altezza = altezza;
	pw_thread_loop_unlock(cattura->ciclo);

	if (*confermata_larghezza == larghezza && *confermata_altezza == altezza)
		informazione("misura cambiata a %ux%u senza rifare la cattura", larghezza, altezza);
	else
		informazione("chiesti %ux%u, il compositore ha confermato %ux%u: la misura la decide lui",
		             larghezza, altezza, *confermata_larghezza, *confermata_altezza);
	return TRUE;
}

gboolean cattura_dmabuf(Cattura *cattura, gboolean vuole, uint32_t larghezza, uint32_t altezza,
                        uint32_t fotogrammi_al_secondo, GError **sbaglio)
{
	if (vuole && !cattura->su_dmabuf)
	{
		/* Non e' una condizione normale: significa che qualcuno chiede la copia
		 * zero a una cattura nata senza consumatore.  Chiederla comunque
		 * vorrebbe dire scartare ogni fotogramma in silenzio. */
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "questa cattura non ha un consumatore di DMA-BUF");
		return FALSE;
	}
	if (cattura->vuole_dmabuf == !!vuole)
		return TRUE;

	/* I tre campi li legge il thread di PipeWire — `su_parametri` e `su_processo`
	 * girano con il lucchetto del ciclo preso — quindi si scrivono tenendolo. */
	pw_thread_loop_lock(cattura->ciclo);
	cattura->vuole_dmabuf = !!vuole;
	/* Il tipo dei buffer e il primo fotogramma si ridicono: da qui in poi
	 * arrivano per un'altra strada, e il registro deve poterlo mostrare invece
	 * di far credere che nulla sia cambiato. */
	cattura->detto_il_tipo = FALSE;
	cattura->primo_fotogramma = TRUE;
	pw_thread_loop_unlock(cattura->ciclo);

	{
		/* Qui la misura non cambia: e' quella corrente, che viaggia dentro la
		 * stessa proposta.  La conferma si legge e si butta — a giudicarla e' il
		 * ridimensionamento, non il cambio di strada. */
		uint32_t confermata_l = 0, confermata_a = 0;

		if (!rinegozia(cattura, larghezza, altezza, fotogrammi_al_secondo, &confermata_l,
		               &confermata_a, sbaglio))
		{
			pw_thread_loop_lock(cattura->ciclo);
			cattura->vuole_dmabuf = !vuole;
			pw_thread_loop_unlock(cattura->ciclo);
			return FALSE;
		}
	}

	informazione("i pixel adesso passano %s", vuole ? "dalla scheda (copia zero)" : "dalla memoria");
	return TRUE;
}

void cattura_ferma(Cattura *cattura)
{
	if (!cattura)
		return;

	/*
	 * Prima si ferma il thread, poi si distrugge il resto.
	 *
	 * Fermandolo per primo non serve piu' prendere il lucchetto per toccare gli
	 * oggetti di PipeWire, e soprattutto non si rischia di distruggere il flusso
	 * mentre una richiamata lo sta usando.
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

	g_free(cattura->guasto);
	g_free(cattura);
}
