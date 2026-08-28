#include "suono.h"

#include <gio/gio.h>
#include <pipewire/pipewire.h>
#include <spa/debug/types.h>
#include <spa/param/audio/format-utils.h>
#include <spa/param/audio/type-info.h>
#include <spa/param/props.h>
#include <spa/utils/result.h>

#include "registro.h"

/* Quanto si aspetta che il server registri il nodo del sink.  E' una risposta
 * locale su un socket: se non arriva in cinque secondi non arrivera'. */
#define ATTESA_SINK_S 5

/* Quanto si aspetta che la cattura arrivi a `paused`, cioe' che il formato sia
 * stato negoziato.  Come per la cattura del desktop: e' l'unico punto in cui un
 * rifiuto si vede subito invece di diventare silenzio piu' tardi. */
#define ATTESA_ASCOLTO_S 5

/*
 * Il nome del sink, che e' anche il modo in cui la cattura lo ritrova.
 *
 * `pw_stream_connect` vuole `PW_ID_ANY` come destinazione e si aggancia a quel
 * che dice `target.object` — dove sta bene un `node.name`.  Cosi' non serve
 * conoscere l'identificativo assegnato dal server, e soprattutto non si finisce
 * a catturare il sink SBAGLIATO il giorno in cui la macchina ne avra' due.
 */
#define NOME_SINK "remotix"

struct Suono
{
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;

	struct pw_proxy *sink;
	struct spa_hook gancio_sink;
	uint32_t nodo;

	struct pw_stream *flusso;
	struct spa_hook gancio_flusso;
	enum pw_stream_state stato;
	char *guasto;

	uint32_t canali;
	SuonoCampioni su_campioni;
	gpointer dati;
	gboolean primo_blocco;
};

/* ------------------------------------------------------------------ *
 * Il sink virtuale
 * ------------------------------------------------------------------ */
static void su_sink_legato(void *dati, uint32_t id_globale)
{
	Suono *suono = dati;

	suono->nodo = id_globale;
	pw_thread_loop_signal(suono->ciclo, false);
}

static void su_sink_tolto(void *dati)
{
	Suono *suono = dati;

	/* Il server ha tolto il nodo da sotto i piedi.  Non c'e' niente da
	 * rifare qui: lo si dice, e chi cattura vedra' il flusso staccarsi. */
	avviso("il sink audio della sessione e' stato rimosso: niente piu' suono");
	suono->nodo = 0;
	pw_thread_loop_signal(suono->ciclo, false);
}

static void su_sink_sbagliato(void *dati, int seq, int res, const char *messaggio)
{
	Suono *suono = dati;

	errore("il sink audio non e' stato creato: %s (%d)", messaggio ? messaggio : "senza spiegazione",
	       res);
	pw_thread_loop_signal(suono->ciclo, false);
}

static const struct pw_proxy_events eventi_sink = {
	PW_VERSION_PROXY_EVENTS,
	.bound = su_sink_legato,
	.removed = su_sink_tolto,
	.error = su_sink_sbagliato,
};

/* ------------------------------------------------------------------ *
 * La cattura del monitor
 * ------------------------------------------------------------------ */
static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *sbaglio)
{
	Suono *suono = dati;

	diagnostica("stato della cattura audio: %s → %s%s%s", pw_stream_state_as_string(vecchio),
	            pw_stream_state_as_string(nuovo), sbaglio ? " — " : "", sbaglio ? sbaglio : "");
	suono->stato = nuovo;
	if (sbaglio)
	{
		g_free(suono->guasto);
		suono->guasto = g_strdup(sbaglio);
	}
	pw_thread_loop_signal(suono->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Suono *suono = dati;
	uint8_t spazio[256];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];
	struct spa_audio_info_raw negoziato = { 0 };

	if (!param || id != SPA_PARAM_Format)
		return;

	/*
	 * ⛔ SI GUARDA IL FORMATO NEGOZIATO DAVVERO, e non e' pignoleria.
	 *
	 * E' la stessa trappola che `cattura.c` documenta per il video, e qui morde
	 * piu' forte: leggere campioni a virgola mobile come interi a 16 bit non
	 * produce nessun errore, produce un'onda quadra a fondo scala che segue la
	 * frequenza giusta — cioe' qualcosa che al banco sembra «audio che arriva»
	 * e all'orecchio e' un ronzio. [M, 5 agosto 2026]
	 */
	if (spa_format_audio_raw_parse(param, &negoziato) >= 0)
	{
		informazione("formato audio negoziato con PipeWire: %s, %u Hz, %u canali",
		             negoziato.format == SPA_AUDIO_FORMAT_S16 ? "S16"
		                                                      : spa_debug_type_find_short_name(
		                                                            spa_type_audio_format,
		                                                            negoziato.format),
		             negoziato.rate, negoziato.channels);

		if (negoziato.format != SPA_AUDIO_FORMAT_S16 || negoziato.channels != suono->canali)
		{
			errore("PipeWire ha negoziato un formato che non e' quello chiesto: i campioni "
			       "verrebbero letti male, e l'audio sarebbe rumore. Spengo la cattura");
			suono->su_campioni = NULL;
		}
	}
	else
	{
		avviso("formato audio non interpretabile: la cattura continua alla cieca");
	}

	/* I campioni si vogliono in memoria ordinaria, mappata: il percorso a
	 * copia zero non c'entra nulla con l'audio, e chiederlo qui significa
	 * soltanto trattare buffer che non si possono leggere direttamente. */
	parametri[0] = spa_pod_builder_add_object(&costruttore, SPA_TYPE_OBJECT_ParamBuffers,
	                                          SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_dataType,
	                                          SPA_POD_Int(1 << SPA_DATA_MemPtr));
	pw_stream_update_params(suono->flusso, parametri, 1);
}

static void su_processo(void *dati)
{
	Suono *suono = dati;
	struct pw_buffer *pacco;

	/*
	 * SI SVUOTA TUTTA LA CODA, in ordine.
	 *
	 * Il riferimento tiene solo l'ultimo pacco e butta i precedenti
	 * (`grd-rdp-audio-output-stream.c`).  Qui no: un pacco buttato e' un buco
	 * nel suono, e i buchi nel suono si sentono tutti.  Se la coda cresce, il
	 * rimedio sta a valle — chi accoda i campioni sa quanti puo' tenerne — non
	 * in una perdita silenziosa qui dentro.
	 */
	while ((pacco = pw_stream_dequeue_buffer(suono->flusso)))
	{
		struct spa_data *piano = &pacco->buffer->datas[0];

		if (pacco->buffer->n_datas > 0 && piano->data && piano->chunk && piano->chunk->size > 0 &&
		    suono->su_campioni)
		{
			const int16_t *campioni =
			    (const int16_t *) ((const uint8_t *) piano->data + piano->chunk->offset);
			uint32_t fotogrammi = piano->chunk->size / (sizeof(int16_t) * suono->canali);

			if (suono->primo_blocco)
			{
				suono->primo_blocco = FALSE;
				informazione("primo blocco di suono dalla sessione: %u fotogrammi", fotogrammi);
			}
			if (fotogrammi > 0)
				suono->su_campioni(campioni, fotogrammi, suono->dati);
		}
		pw_stream_queue_buffer(suono->flusso, pacco);
	}
}

static const struct pw_stream_events eventi_flusso = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/* ------------------------------------------------------------------ *
 * Ciclo di vita
 * ------------------------------------------------------------------ */
/*
 * Il sink nasce al massimo e non zittito.
 *
 * ⛔ PERCHE' UN LIVELLO BASSO SUL SERVER E' INVISIBILE.
 *    [decisione dell'utente, 8 agosto 2026, dopo la caccia di quella mattina]
 *
 *    Il livello lo decide il server e il client se lo trova nei campioni: e' la
 *    strada che regge su tutti e tre i client e su tutti i desktop, perche' non
 *    chiede niente a nessuno (`kde.md` §10.5).  Il prezzo di quella scelta e'
 *    che il cursore del server diventa uno stato nascosto: chi si collega da un
 *    altro apparecchio tre giorni dopo sente piano e **non ha modo di sapere
 *    perche'** — va a cercare il guasto nella rete, nel codificatore, ovunque
 *    tranne che li'.  E' successo davvero, a noi, con il sink a zero e in mute.
 *
 *    Quindi una via audio appena montata parte **udibile**, sempre.  Se poi
 *    l'utente abbassa, la sua scelta resta finche' resta collegato: il sink vive
 *    quanto il palco, e il palco quanto il primo client.
 *
 * ⚠ Non si controlla l'esito: se PipeWire rifiutasse, il rimedio sarebbe
 *   comunque il cursore dell'utente, e un errore qui non deve impedire l'audio.
 */
/* Il comando vero.  ⚠ Chiama chi TIENE GIA' il lucchetto del ciclo. */
static void alza(Suono *suono)
{
	uint8_t memoria[512];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(memoria, sizeof memoria);
	float volumi[2] = { 1.0f, 1.0f };
	const struct spa_pod *props;

	props = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_Props, SPA_PARAM_Props, SPA_PROP_mute, SPA_POD_Bool(false),
	    SPA_PROP_channelVolumes,
	    SPA_POD_Array(sizeof(float), SPA_TYPE_Float, G_N_ELEMENTS(volumi), volumi));

	{
		int seq = pw_node_set_param((struct pw_node *) suono->sink, SPA_PARAM_Props, 0, props);

		/*
		 * ⚠ QUEL NUMERO E' UNA SEQUENZA ASINCRONA, NON UN ESITO: dice che la
		 *   richiesta e' partita, non che il valore e' cambiato.  Lo si stampa
		 *   proprio per questo — perche' finche' il difetto di §7.5 di
		 *   `REFERENCE.md` e' aperto, «chiesto» e «fatto» qui non coincidono, e
		 *   una riga che dicesse «portato al massimo» sarebbe una riga che mente.
		 */
		diagnostica("volume del sink: massimo CHIESTO al nodo %u (seq %d) — non verificato, "
		            "vedi REFERENCE.md §7.5",
		            suono->nodo, seq);
	}
}

/*
 * ⛔ E IL LUCCHETTO DEL CICLO SI PRENDE, SEMPRE.
 *    [M, 8 agosto 2026, trovato dal banco `prove/fase11-volume.sh`]
 *
 *    libpipewire non e' sincronizzata da se': ogni chiamata va fatta o dal
 *    thread del ciclo, o tenendo `pw_thread_loop_lock`.  Questa funzione la
 *    chiamano DUE thread estranei — quello della connessione, a ogni client che
 *    si collega, e quello che avvia la cattura — e senza lucchetto la richiesta
 *    finiva nella connessione mentre il ciclo la stava usando: **a volte
 *    passava, a volte no**, e il registro diceva comunque «portato al massimo».
 *
 *    Il difetto si vedeva solo nel caso che conta: utente che zittisce, si
 *    scollega, si ricollega — e ritrova il silenzio.  Il banco lo mancava
 *    perche' zittiva a client collegato, cioe' **non riproduceva**
 *    (`LEZIONI.md` §1.3).
 */
void suono_volume_massimo(Suono *suono)
{
	if (!suono || !suono->ciclo || !suono->sink)
		return;
	pw_thread_loop_lock(suono->ciclo);
	alza(suono);
	pw_thread_loop_unlock(suono->ciclo);
}

static gboolean crea_sink(Suono *suono, GError **sbaglio)
{
	struct pw_properties *proprieta;
	gint64 scadenza;

	proprieta = pw_properties_new(
	    PW_KEY_FACTORY_NAME, "support.null-audio-sink", PW_KEY_NODE_NAME, NOME_SINK,
	    PW_KEY_NODE_DESCRIPTION, "REMOTIX", PW_KEY_MEDIA_CLASS, "Audio/Sink", "audio.position",
	    "[FL,FR]",
	    /*
	     * ⛔ SENZA QUESTA RIGA IL CURSORE DEL VOLUME NON GOVERNA NIENTE.
	     *    [M, 8 agosto 2026, e l'ha visto l'utente: «se abbasso il volume
	     *    l'audio resta sempre alto»]
	     *
	     *    In PipeWire il volume di un nodo si applica DOPO la presa del
	     *    monitor, e `monitor.channel-volumes` — che sposta la presa a valle —
	     *    vale FALSE se non la si chiede.  Noi il sink lo creiamo a mano, e
	     *    quindi ce la scordavamo; `module-null-sink` di pipewire-pulse la
	     *    mette da se', perche' in PulseAudio il monitor e' sempre stato a
	     *    valle del volume.  Da cui la misura che sembrava assolvere il codice:
	     *    su un sink creato con `pactl` il volume passava (100% -> 25.4%,
	     *    25% -> 0.40%, cioe' la curva cubica di Pulse, esatta), sul NOSTRO
	     *    no — nodo 50 a `channelVolumes 0.0` e `mute true`, e il monitor
	     *    consegnava il segnale intero.
	     *
	     * ⚠ Il verso conta: RDP ha un solo PDU di volume, `SNDC_SETVOLUME`, e va
	     *   dal SERVER al client (`altoparlante.c`).  Il client non ha modo di
	     *   dire al server «abbassa», quindi l'unico cursore che puo' funzionare
	     *   e' quello che si vede DENTRO la sessione: questo.
	     */
	    "monitor.channel-volumes", "true",
	    /*
	     * ⛔ E CHE NESSUNO CI RIMETTA I LIVELLI DI IERI.
	     *    WirePlumber salva volume e mute per nome del nodo e li rimette
	     *    quando il nodo ricompare — misurato l'8 agosto 2026: il sink NUOVO
	     *    nasceva a `0.008` e `mute true`, cioe' col valore che l'utente
	     *    aveva messo in una sessione finita.  E' esattamente lo stato
	     *    invisibile che questa scelta vuole rendere impossibile.
	     *
	     * ⚠ La chiave e' un suggerimento: se la versione di WirePlumber non la
	     *   conosce non fa niente e non da' errore.  Per questo NON ci si conta
	     *   sopra — il volume si rialza comunque a ogni collegamento, e di nuovo
	     *   quando la cattura parte.
	     */
	    "state.restore-props", "false",
	    /* Il nodo muore con la nostra connessione a PipeWire, e va bene cosi':
	     * appartiene alla sessione servita, non alla macchina.  Lasciarlo
	     * dietro significherebbe che un REMOTIX riavviato ne trova due. */
	    PW_KEY_OBJECT_LINGER, "false", NULL);

	suono->sink = pw_core_create_object(suono->nucleo, "adapter", PW_TYPE_INTERFACE_Node,
	                                    PW_VERSION_NODE, &proprieta->dict, 0);
	pw_properties_free(proprieta);

	if (!suono->sink)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "PipeWire non ha creato il sink virtuale");
		return FALSE;
	}
	pw_proxy_add_listener(suono->sink, &suono->gancio_sink, &eventi_sink, suono);

	scadenza = g_get_monotonic_time() + (gint64) ATTESA_SINK_S * G_USEC_PER_SEC;
	while (suono->nodo == 0 && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(suono->ciclo, 1);

	if (suono->nodo == 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "il sink virtuale non e' stato registrato entro %d secondi", ATTESA_SINK_S);
		return FALSE;
	}
	alza(suono);
	return TRUE;
}

Suono *suono_apri(GError **sbaglio)
{
	static gsize inizializzato = 0;
	Suono *suono = g_new0(Suono, 1);

	if (g_once_init_enter(&inizializzato))
	{
		pw_init(NULL, NULL);
		g_once_init_leave(&inizializzato, 1);
	}

	suono->ciclo = pw_thread_loop_new("remotix-suono", NULL);
	if (!suono->ciclo)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "ciclo PipeWire non creato");
		goto guasto;
	}
	suono->contesto = pw_context_new(pw_thread_loop_get_loop(suono->ciclo), NULL, 0);
	if (!suono->contesto)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "contesto PipeWire non creato");
		goto guasto;
	}

	pw_thread_loop_lock(suono->ciclo);
	if (pw_thread_loop_start(suono->ciclo) < 0)
	{
		pw_thread_loop_unlock(suono->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "thread di PipeWire non avviato");
		goto guasto;
	}

	suono->nucleo = pw_context_connect(suono->contesto, NULL, 0);
	if (!suono->nucleo)
	{
		pw_thread_loop_unlock(suono->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "connessione a PipeWire fallita");
		goto guasto;
	}

	if (!crea_sink(suono, sbaglio))
	{
		pw_thread_loop_unlock(suono->ciclo);
		goto guasto;
	}
	pw_thread_loop_unlock(suono->ciclo);

	informazione("sink audio «%s» montato nella sessione: nodo %u", NOME_SINK, suono->nodo);
	return suono;

guasto:
	suono_chiudi(suono);
	return NULL;
}

gboolean suono_ascolto_avvia(Suono *suono, uint32_t frequenza, uint32_t canali,
                             SuonoCampioni su_campioni, gpointer dati, GError **sbaglio)
{
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];
	struct spa_audio_info_raw formato = { 0 };
	gint64 scadenza;

	if (!suono)
		return FALSE;

	/*
	 * ⛔ QUI, E NON SOLO ALLA CREAZIONE.  Chi ripristina i livelli salvati lo fa
	 *    quando il nodo compare, cioe' subito DOPO che l'abbiamo alzato noi: alla
	 *    creazione si perde la corsa, e il primo collegamento dopo un riavvio
	 *    arriva muto.  L'avvio della cattura e' il momento piu' tardi di cui
	 *    disponiamo, e a quel punto la corsa e' finita.
	 */
	suono_volume_massimo(suono);

	if (canali < 1 || canali > 2)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
		            "solo mono o stereo, non %u canali", canali);
		return FALSE;
	}

	pw_thread_loop_lock(suono->ciclo);

	if (suono->flusso)
	{
		pw_thread_loop_unlock(suono->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BUSY, "la cattura audio e' gia' accesa");
		return FALSE;
	}

	suono->canali = canali;
	suono->su_campioni = su_campioni;
	suono->dati = dati;
	suono->primo_blocco = TRUE;
	suono->stato = PW_STREAM_STATE_UNCONNECTED;

	suono->flusso = pw_stream_new(
	    suono->nucleo, "remotix-suono",
	    pw_properties_new(PW_KEY_MEDIA_TYPE, "Audio", PW_KEY_MEDIA_CATEGORY, "Capture",
	                      /* Le due righe che decidono DA DOVE si cattura: il
	                       * monitor (l'uscita) del nostro sink, e non l'ingresso
	                       * di un microfono che qui non esiste. */
	                      PW_KEY_STREAM_CAPTURE_SINK, "true", PW_KEY_TARGET_OBJECT, NOME_SINK,
	                      /* Un quanto corto tiene bassa la latenza e fa arrivare
	                       * blocchi piccoli e regolari, che e' quel che serve a
	                       * chi li deve accodare.  E' il valore del riferimento. */
	                      PW_KEY_NODE_FORCE_QUANTUM, "256", NULL));
	if (!suono->flusso)
	{
		pw_thread_loop_unlock(suono->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "flusso PipeWire non creato");
		return FALSE;
	}
	pw_stream_add_listener(suono->flusso, &suono->gancio_flusso, &eventi_flusso, suono);

	/*
	 * Si cattura DIRETTAMENTE nel formato che il client ha negoziato.
	 *
	 * PipeWire ricampiona per conto suo fra il sink e questo flusso, e cosi'
	 * fra il monitor e il filo non resta nessuna conversione: `SendSamples`
	 * riceve gia' i campioni giusti.  Il vantaggio vero e' che non si dipende
	 * da quali ricampionatori sia stata compilata FreeRDP.
	 */
	formato.format = SPA_AUDIO_FORMAT_S16;
	formato.rate = frequenza;
	formato.channels = canali;
	formato.position[0] = canali == 1 ? SPA_AUDIO_CHANNEL_MONO : SPA_AUDIO_CHANNEL_FL;
	if (canali == 2)
		formato.position[1] = SPA_AUDIO_CHANNEL_FR;
	parametri[0] = spa_format_audio_raw_build(&costruttore, SPA_PARAM_EnumFormat, &formato);

	if (pw_stream_connect(suono->flusso, PW_DIRECTION_INPUT, PW_ID_ANY,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, 1) < 0)
	{
		pw_stream_destroy(suono->flusso);
		suono->flusso = NULL;
		pw_thread_loop_unlock(suono->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "aggancio al monitor del sink «%s» fallito", NOME_SINK);
		return FALSE;
	}

	scadenza = g_get_monotonic_time() + (gint64) ATTESA_ASCOLTO_S * G_USEC_PER_SEC;
	while (suono->stato != PW_STREAM_STATE_PAUSED && suono->stato != PW_STREAM_STATE_STREAMING &&
	       suono->stato != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(suono->ciclo, 1);
	pw_thread_loop_unlock(suono->ciclo);

	if (suono->stato == PW_STREAM_STATE_ERROR)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "cattura audio rifiutata: %s",
		            suono->guasto ? suono->guasto : "senza spiegazione");
		suono_ascolto_ferma(suono);
		return FALSE;
	}
	if (suono->stato != PW_STREAM_STATE_PAUSED && suono->stato != PW_STREAM_STATE_STREAMING)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "la cattura audio non ha dato segno di vita entro %d secondi",
		            ATTESA_ASCOLTO_S);
		suono_ascolto_ferma(suono);
		return FALSE;
	}

	informazione("cattura audio avviata: %u Hz, %u canali, dal monitor di «%s»", frequenza, canali,
	             NOME_SINK);
	return TRUE;
}

void suono_ascolto_ferma(Suono *suono)
{
	if (!suono || !suono->ciclo)
		return;

	/*
	 * Il lucchetto del ciclo E' l'attesa promessa nell'intestazione: PipeWire
	 * lo tiene mentre chiama `su_processo`, quindi prenderlo qui significa che
	 * nessuna richiamata e' a meta' strada, e distruggere il flusso da dentro
	 * significa che non ne partira' un'altra.
	 */
	pw_thread_loop_lock(suono->ciclo);
	if (suono->flusso)
	{
		pw_stream_destroy(suono->flusso);
		suono->flusso = NULL;
		informazione("cattura audio fermata");
	}
	suono->su_campioni = NULL;
	suono->dati = NULL;
	pw_thread_loop_unlock(suono->ciclo);
}

uint32_t suono_nodo(const Suono *suono)
{
	return suono ? suono->nodo : 0;
}

void suono_chiudi(Suono *suono)
{
	if (!suono)
		return;

	/* Prima si ferma il thread, poi si distrugge il resto: e' la stessa regola
	 * della cattura del desktop, e per lo stesso motivo — cosi' non si tocca
	 * niente che una richiamata stia usando. */
	if (suono->ciclo)
		pw_thread_loop_stop(suono->ciclo);
	if (suono->flusso)
		pw_stream_destroy(suono->flusso);
	if (suono->sink)
		pw_proxy_destroy(suono->sink);
	if (suono->nucleo)
		pw_core_disconnect(suono->nucleo);
	if (suono->contesto)
		pw_context_destroy(suono->contesto);
	if (suono->ciclo)
		pw_thread_loop_destroy(suono->ciclo);

	g_free(suono->guasto);
	g_free(suono);
}
