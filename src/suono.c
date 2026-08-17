/*
 * suono.c — vedi `suono.h` per il mandato, la divisione sessione/connessione e
 * la scelta di NON accumulare i blocchi qui dentro.
 *
 * ⚠ Portato da v1 (`v1/remotix-c/src/suono.c`) il 17 agosto 2026.  Le sole
 *   differenze volute rispetto a quel file:
 *     · niente GLib — `bool` di `<stdbool.h>`, il registro di `registro.h`, e
 *       chi fallisce torna `false`/NULL dopo aver scritto il perche';
 *     · il formato non si negozia piu' (§5.3): viene da `audio.h`;
 *     · il thread di tempo reale non stampa piu' niente (vedi `suono.h`);
 *     · l'attesa promessa da `suono_ascolto_ferma()` e' fatta davvero — v1
 *       la prometteva e non la faceva (il riquadro sta accanto alla funzione).
 */
#include "suono.h"

#include <pipewire/pipewire.h>
#include <spa/debug/types.h>
#include <spa/param/audio/format-utils.h>
#include <spa/param/audio/type-info.h>
#include <spa/param/props.h>
#include <spa/utils/result.h>

#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "audio.h"
#include "registro.h"

/* ⚠ L'area sta qui e non in `registro.h` per la stessa ragione per cui
 *   `REG_AUDIO` sta in `audio.c`: questo file non e' ancora nel `Makefile`, e
 *   una costante messa nell'intestazione comune prima della cucitura e' una
 *   riga che nomina un modulo che il prodotto non compila.  ⇒ Al montaggio si
 *   sposta, come si e' fatto con `REG_SESSIONE`. */
#define REG_SUONO "suono"

/* Quanto si aspetta che il server registri il nodo del sink.  E' una risposta
 * locale su un socket: se non arriva in cinque secondi non arrivera'. */
#define ATTESA_SINK_MS 5000

/* Quanto si aspetta che la cattura arrivi a `paused`, cioe' che il formato sia
 * stato negoziato.  ⛔ E' l'unico punto in cui un rifiuto si vede SUBITO invece
 * di diventare silenzio piu' tardi — la stessa ragione dell'attesa di
 * `cattura.c`, e li' costa dieci secondi perche' li' c'e' un compositore che si
 * sta alzando; qui dall'altra parte c'e' solo PipeWire. */
#define ATTESA_ASCOLTO_MS 5000

/* Quanto si aspetta, al massimo, che un richiamo di tempo reale gia' partito
 * esca (vedi `suono_ascolto_ferma`).  ⚠ In salute costa zero o un quanto —
 * `[?]` 5-6 ms: il tetto e' largo apposta, perche' superarlo significa che
 * PipeWire e' fermo e la riga che lo dice vale piu' del tempo che costa. */
#define ATTESA_BARRIERA_MS 2000

/*
 * Il nome del sink, che e' anche il modo in cui la cattura lo ritrova.
 *
 * `pw_stream_connect()` vuole `PW_ID_ANY` come destinazione e si aggancia a
 * quel che dice `target.object` — dove sta bene un `node.name`.  Cosi' non
 * serve conoscere l'identificativo assegnato dal server, e soprattutto non si
 * finisce a catturare il sink SBAGLIATO il giorno in cui la macchina ne avra'
 * due (una scheda vera, o una seconda sessione servita).
 */
#define NOME_SINK "remotix"

/*
 * ⚠ Il quanto forzato, e il numero e' quello di v1 e del riferimento
 *   (`gnome-remote-desktop`): 256 fotogrammi, cioe' 5,33 ms a 48 kHz.  Un quanto
 *   corto tiene basso il ritardo — `CODER.md` §1-bis, il ritardo pesa piu' dei
 *   fotogrammi — e fa arrivare blocchi piccoli e regolari.
 *
 * `[?]` 240 sarebbe piu' comodo (5 ms tondi: un blocco PCM esatto, un quarto di
 *   blocco Opus esatto), ⛔ ma cambiare un valore che v1 ha misurato sul campo
 *   per una comodita' non misurata e' un debito, non una cura (`CODER.md`,
 *   §1-bis del riquadro dei dieci secondi in `cattura.c`).  Si cambia il giorno
 *   in cui qualcuno misura che conviene.
 */
#define QUANTO_FORZATO "256"

struct suono
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

	/* --- quel che il thread di tempo reale tocca ------------------------ *
	 *
	 * ⛔ `consegna` e `in_richiamo` sono ATOMICI e non `bool` semplici: sono le
	 *    due meta' della barriera di `suono_ascolto_ferma()`, e una barriera
	 *    costruita su letture che il compilatore puo' spostare non e' una
	 *    barriera.  Il perche' del disegno sta accanto a quella funzione. */
	atomic_bool consegna;
	atomic_bool in_richiamo;
	suono_campioni su_campioni;
	void *chi;

	/* I conteggi.  ⚠ Li incrementa il thread di tempo reale e li legge chi
	 *   vuole: atomici per lo stesso motivo di sopra, e `relaxed` basterebbe —
	 *   sono numeri per il registro, non una sincronizzazione. */
	atomic_ullong blocchi;
	atomic_ullong fotogrammi;
	atomic_ullong scartati;
	/* ⭐ Il campione piu' forte visto, in valore assoluto.  Vedi il riquadro in
	 *    `su_processo`: e' quel che distingue «non suonava nessuno» da
	 *    «PipeWire ci consegna buffer vuoti». */
	atomic_ullong picco;
};

/* ------------------------------------------------------------------ *
 * Il sink virtuale
 * ------------------------------------------------------------------ */
static void su_sink_legato(void *dati, uint32_t id_globale)
{
	suono *s = dati;

	s->nodo = id_globale;
	pw_thread_loop_signal(s->ciclo, false);
}

static void su_sink_tolto(void *dati)
{
	suono *s = dati;

	/* Il server ha tolto il nodo da sotto i piedi.  Non c'e' niente da rifare
	 * qui: lo si dice, e chi cattura vedra' il flusso staccarsi.  ⚠ Gira sul
	 * thread del CICLO, non su quello di tempo reale: qui si puo' scrivere. */
	registro_dice(REG_SUONO, "⛔ il sink audio della sessione e' stato RIMOSSO: niente piu' suono "
	                         "(nodo %u)", s->nodo);
	s->nodo = 0;
	pw_thread_loop_signal(s->ciclo, false);
}

static void su_sink_sbagliato(void *dati, int seq, int res, const char *messaggio)
{
	suono *s = dati;

	registro_dice(REG_SUONO, "⛔ il sink audio non e' stato creato: %s (%d, %s)",
	              messaggio ? messaggio : "senza spiegazione", res, spa_strerror(res));
	pw_thread_loop_signal(s->ciclo, false);
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
	suono *s = dati;

	registro_dettaglio(REG_SUONO, "stato della cattura audio: %s → %s%s%s",
	                   pw_stream_state_as_string(vecchio), pw_stream_state_as_string(nuovo),
	                   sbaglio ? " — " : "", sbaglio ? sbaglio : "");
	s->stato = nuovo;
	if (sbaglio)
	{
		free(s->guasto);
		s->guasto = strdup(sbaglio);
	}

	/* ⛔ Il distacco si DICE, e non si lascia dedurre dal silenzio: da qui in poi
	 *    non arriva piu' un campione, e senza questa riga chi cerca «perche' non
	 *    si sente niente» non ha modo di distinguerlo da «nessuno sta suonando».
	 *    ⚠ Chi vuole accorgersene nel codice chiama `suono_ascolto_vivo()`. */
	if ((vecchio == PW_STREAM_STATE_PAUSED || vecchio == PW_STREAM_STATE_STREAMING) &&
	    (nuovo == PW_STREAM_STATE_UNCONNECTED || nuovo == PW_STREAM_STATE_ERROR))
		registro_dice(REG_SUONO, "⛔ la cattura audio si e' staccata (%s)%s%s",
		              pw_stream_state_as_string(nuovo), sbaglio ? " — " : "",
		              sbaglio ? sbaglio : "");

	pw_thread_loop_signal(s->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	suono *s = dati;
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
	 * frequenza giusta — cioe' qualcosa che al banco sembra «audio che arriva» e
	 * all'orecchio e' un ronzio.  `[M]` 5 agosto 2026, v1.
	 *
	 * ⛔⭐ E IN V2 SI GUARDA ANCHE LA FREQUENZA, che in v1 non si guardava: li'
	 *     la si era chiesta uguale a quella negoziata con il client RDP, qui e'
	 *     fissa a 48 000 (§5.3) e tutta la catena a valle ci conta — Opus riceve
	 *     un `sample_rate` scritto in `audio.c`, non uno letto da qui.  Se
	 *     PipeWire ne concedesse un'altra, il suono uscirebbe intonato male e
	 *     lungo il tempo sbagliato, **senza un errore da nessuna parte**.
	 */
	if (spa_format_audio_raw_parse(param, &negoziato) >= 0)
	{
		bool giusto = negoziato.format == SPA_AUDIO_FORMAT_S16 &&
		              negoziato.rate == AUDIO_FREQUENZA && negoziato.channels == AUDIO_CANALI;
		/* ⚠ Il nome puo' non esserci — `spa_debug_type_find_short_name()` torna
		 *   NULL per un identificativo che la sua tabella non conosce — e allora
		 *   si stampa il NUMERO nudo: e' la stessa regola di `cattura.c`
		 *   (`primo_tipo_grezzo`), perche' «(null)» in un registro non si puo'
		 *   cercare da nessuna parte. */
		const char *nome = negoziato.format == SPA_AUDIO_FORMAT_S16
		                       ? "S16"
		                       : spa_debug_type_find_short_name(spa_type_audio_format,
		                                                        negoziato.format);

		registro_dice(REG_SUONO,
		              "formato audio negoziato con PipeWire: %s (SPA %u), %u Hz, %u canali%s",
		              nome ? nome : "SENZA NOME", negoziato.format, negoziato.rate,
		              negoziato.channels, giusto ? "" : "  ⛔ NON E' QUEL CHE SI E' CHIESTO");

		if (!giusto)
		{
			registro_dice(REG_SUONO,
			              "⛔ §5.3 vuole S16 a %d Hz su %d canali: i campioni verrebbero letti "
			              "male e l'audio sarebbe RUMORE, non un errore.  Spengo la consegna",
			              (int) AUDIO_FREQUENZA, (int) AUDIO_CANALI);
			atomic_store(&s->consegna, false);
		}
	}
	else
	{
		/* ⛔ Non si va avanti alla cieca — v1 lo faceva («la cattura continua
		 *    alla cieca») ed e' il ripiego silenzioso che `CODER.md` §4.2 vieta:
		 *    un formato che non si sa leggere e' esattamente il caso in cui i
		 *    campioni possono essere qualunque cosa. */
		registro_dice(REG_SUONO, "⛔ formato audio non interpretabile: spengo la consegna invece "
		                         "di leggere campioni di cui non so niente");
		atomic_store(&s->consegna, false);
	}

	/* I campioni si vogliono in memoria ordinaria, mappata: il percorso a copia
	 * zero non c'entra nulla con l'audio, e chiederlo qui significa soltanto
	 * trattare buffer che non si possono leggere direttamente. */
	parametri[0] = spa_pod_builder_add_object(&costruttore, SPA_TYPE_OBJECT_ParamBuffers,
	                                          SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_dataType,
	                                          SPA_POD_Int(1 << SPA_DATA_MemPtr));
	pw_stream_update_params(s->flusso, parametri, 1);
}

/*
 * ⛔⛔ QUESTA FUNZIONE GIRA SUL THREAD DI TEMPO REALE.  Vedi `suono.h`.
 *
 * Dentro ci sono soltanto: una `dequeue`, dei confronti, il richiamo di chi
 * ascolta e una `queue`.  ⛔ Nessuna riga di registro, nessuna allocazione,
 * nessun lucchetto — v1 stampava il primo blocco da qui, e una `write` in
 * questo punto fa saltare il quanto a tutto il grafo, cattura del desktop
 * compresa.
 */
static void su_processo(void *dati)
{
	suono *s = dati;
	struct pw_stream *flusso = s->flusso;
	struct pw_buffer *pacco;

	/*
	 * ⛔ LA PRIMA META' DELLA BARRIERA, e l'ordine e' tutto: si dichiara di
	 *    essere dentro PRIMA di leggere `consegna`.  Chi ferma fa il contrario —
	 *    spegne `consegna` e poi legge `in_richiamo` — e con due scritture
	 *    sequenzialmente coerenti almeno uno dei due vede l'altro.  E' Dekker, ed
	 *    e' quel che rende vera la promessa di `suono_ascolto_ferma()`.
	 */
	atomic_store(&s->in_richiamo, true);

	if (!flusso)
	{
		atomic_store(&s->in_richiamo, false);
		return;
	}

	/*
	 * SI SVUOTA TUTTA LA CODA, in ordine.
	 *
	 * Il riferimento tiene solo l'ultimo pacco e butta i precedenti
	 * (`grd-rdp-audio-output-stream.c`).  ⛔ Qui no, ed e' la differenza fra
	 * l'audio e il video: nel video vince il piu' nuovo, perche' di un
	 * fotogramma vecchio non se ne fa niente nessuno (`cattura.c`, il posto
	 * dell'ultimo fotogramma).  Nel suono un pacco buttato e' un BUCO, e i buchi
	 * si sentono tutti.  Se la coda cresce il rimedio sta a valle — chi accoda i
	 * campioni sa quanti puo' tenerne — non in una perdita silenziosa qui.
	 */
	while ((pacco = pw_stream_dequeue_buffer(flusso)))
	{
		struct spa_data *piano = &pacco->buffer->datas[0];

		if (pacco->buffer->n_datas > 0 && piano->data && piano->chunk && piano->chunk->size > 0)
		{
			const int16_t *campioni =
			    (const int16_t *) ((const uint8_t *) piano->data + piano->chunk->offset);
			uint32_t fotogrammi =
			    (uint32_t) (piano->chunk->size / (sizeof(int16_t) * AUDIO_CANALI));

			if (fotogrammi > 0)
			{
				/* ⛔ `consegna` si legge una volta sola e si tiene: leggerla due
				 *    volte vorrebbe dire poterla trovare accesa nel controllo e
				 *    spenta nel richiamo. */
				if (atomic_load(&s->consegna) && s->su_campioni)
				{
					/*
					 * ⭐ IL PICCO, ED E' L'UNICO NUMERO CHE DISTINGUE LE DUE
					 *    FACCE DEL SILENZIO.  `[M]` 17 agosto 2026, e mi e'
					 *    costato mezza giornata non averlo.
					 *
					 *    Senza, «non si sente niente» ha due cause con la
					 *    stessa identica faccia — 48 000 fotogrammi al secondo
					 *    consegnati, zero scartati, il flusso in `streaming` —
					 *    e sono: **nella sessione non suonava nessuno**, oppure
					 *    **PipeWire ci consegna buffer vuoti**.  E' `CODER.md`
					 *    §3.10 applicata al campione invece che al conteggio:
					 *    un modulo che sa dire «zero» deve saper distinguere lo
					 *    zero dal guasto.
					 *
					 * ⚠ E il prezzo sul thread di tempo reale e' un giro di
					 *   confronti su 512 interi — nessuna allocazione, nessun
					 *   lucchetto, nessuna scrittura: meno lavoro della copia
					 *   che fa chi ascolta, e il contratto di `suono.h` resta
					 *   («dentro si copia e si torna»).
					 */
					uint32_t i;
					unsigned long long pk = 0;

					for (i = 0; i < fotogrammi * AUDIO_CANALI; i++)
					{
						int v = campioni[i] < 0 ? -campioni[i] : campioni[i];
						if ((unsigned long long) v > pk)
							pk = (unsigned long long) v;
					}
					if (pk > atomic_load(&s->picco))
						atomic_store(&s->picco, pk);

					atomic_fetch_add(&s->blocchi, 1u);
					atomic_fetch_add(&s->fotogrammi, fotogrammi);
					s->su_campioni(campioni, fotogrammi, s->chi);
				}
				else
				{
					/* ⛔ «Arrivati e buttati» NON e' «non arrivati»: `CODER.md`
					 *    §3.10.  Senza questo conto, un formato rifiutato e un
					 *    desktop muto hanno la stessa faccia. */
					atomic_fetch_add(&s->scartati, fotogrammi);
				}
			}
		}
		pw_stream_queue_buffer(flusso, pacco);
	}

	atomic_store(&s->in_richiamo, false);
}

static const struct pw_stream_events eventi_flusso = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/* ------------------------------------------------------------------ *
 * Il volume — invariante I5
 * ------------------------------------------------------------------ */
/*
 * Il sink nasce al massimo e non zittito.
 *
 * ⛔ PERCHE' UN LIVELLO BASSO SUL SERVER E' INVISIBILE.
 *    [decisione dell'utente, 8 agosto 2026, dopo la caccia di quella mattina]
 *
 *    Il livello lo decide il server e il client se lo trova nei campioni: e' la
 *    strada che regge su tutti i client e su tutti i desktop, perche' non chiede
 *    niente a nessuno (`STUDI.md` §kde §10.5).  Il prezzo di quella scelta e' che
 *    il cursore del server diventa uno stato NASCOSTO: chi si collega da un
 *    altro apparecchio tre giorni dopo sente piano e non ha modo di sapere
 *    perche'.  E' successo davvero, a noi, con il sink a zero e in mute.
 *
 *    ⇒ Una via audio appena montata parte UDIBILE, sempre (invariante I5).  Se
 *    poi l'utente abbassa, la sua scelta resta finche' resta collegato.
 *
 * ⚠ Non si controlla l'esito: se PipeWire rifiutasse, il rimedio sarebbe
 *   comunque il cursore dentro la sessione, e un errore qui non deve impedire
 *   l'audio.
 */
/* Il comando vero.  ⚠ Lo chiama chi TIENE GIA' il lucchetto del ciclo. */
static void alza(suono *s)
{
	uint8_t memoria[512];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(memoria, sizeof memoria);
	float volumi[AUDIO_CANALI];
	const struct spa_pod *props;
	int seq;
	int i;

	for (i = 0; i < AUDIO_CANALI; i++)
		volumi[i] = 1.0f;

	props = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_Props, SPA_PARAM_Props, SPA_PROP_mute, SPA_POD_Bool(false),
	    SPA_PROP_channelVolumes,
	    SPA_POD_Array(sizeof(float), SPA_TYPE_Float, SPA_N_ELEMENTS(volumi), volumi));

	seq = pw_node_set_param((struct pw_node *) s->sink, SPA_PARAM_Props, 0, props);

	/*
	 * ⚠ QUEL NUMERO E' UNA SEQUENZA ASINCRONA, NON UN ESITO: dice che la
	 *   richiesta e' partita, non che il valore e' cambiato.  Lo si stampa
	 *   proprio per questo — una riga che dicesse «portato al massimo» sarebbe
	 *   una riga che mente, e `CODER.md` §3.8 vuole che il livello si verifichi
	 *   dal lato che lo consuma (un `wpctl get-volume`, non questa riga).
	 */
	registro_dettaglio(REG_SUONO, "volume del sink: massimo CHIESTO al nodo %u (seq %d) — chiesto, "
	                              "non verificato", s->nodo, seq);
}

/*
 * ⛔ E IL LUCCHETTO DEL CICLO SI PRENDE, SEMPRE.
 *    `[M]` 8 agosto 2026, trovato dal banco `prove/fase11-volume.sh` di v1.
 *
 *    libpipewire non e' sincronizzata da se': ogni chiamata va fatta o dal
 *    thread del ciclo, o tenendo `pw_thread_loop_lock`.  Questa funzione la
 *    chiamano DUE thread estranei — quello della connessione, a ogni client che
 *    si collega, e quello che avvia la cattura — e senza lucchetto la richiesta
 *    finiva nella connessione mentre il ciclo la stava usando: **a volte
 *    passava, a volte no**, e il registro diceva comunque «portato al massimo».
 *
 *    ⚠ Il difetto si vedeva solo nel caso che conta: utente che zittisce, si
 *    scollega, si ricollega — e ritrova il silenzio.  Il banco lo mancava perche'
 *    zittiva a client collegato, cioe' NON RIPRODUCEVA (`CODER.md` §3.4).
 */
void suono_volume_massimo(suono *s)
{
	if (!s || !s->ciclo || !s->sink)
		return;
	pw_thread_loop_lock(s->ciclo);
	alza(s);
	pw_thread_loop_unlock(s->ciclo);
}

/* ------------------------------------------------------------------ *
 * Ciclo di vita
 * ------------------------------------------------------------------ */
static bool crea_sink(suono *s)
{
	struct pw_properties *proprieta;
	uint64_t scadenza;

	proprieta = pw_properties_new(
	    PW_KEY_FACTORY_NAME, "support.null-audio-sink", PW_KEY_NODE_NAME, NOME_SINK,
	    PW_KEY_NODE_DESCRIPTION, "REMOTIX", PW_KEY_MEDIA_CLASS, "Audio/Sink", "audio.position",
	    "[FL,FR]",
	    /*
	     * ⛔⛔ SENZA QUESTA RIGA IL CURSORE DEL VOLUME NON GOVERNA NIENTE.
	     *     `[M]` 8 agosto 2026, `STUDI.md` §kde §10.5 — e l'ha aperto l'utente:
	     *     «se abbasso il volume l'audio resta sempre alto; in pratica audio
	     *     del server e del client sono scollegati».
	     *
	     *     In PipeWire il volume di un nodo si applica DOPO la presa del
	     *     monitor, e `monitor.channel-volumes` — che sposta la presa a valle —
	     *     vale `false` se non la si chiede.  Noi il sink lo creiamo a mano con
	     *     `pw_core_create_object` e quindi ce la scordavamo;
	     *     `module-null-sink` di pipewire-pulse la mette da se', perche' in
	     *     PulseAudio il monitor e' sempre stato a valle del volume.
	     *
	     *     La misura, tono a 440 Hz di ampiezza nota (25,9 % del fondo scala)
	     *     letto sul monitor:
	     *
	     *       volume del sink | senza la riga (com'era) | con la riga (`pactl`)
	     *              100 %    |        25,39 %          |       25,39 %
	     *               25 %    |     ⛔ 25,39 %          |        0,40 %
	     *                0 %    |     ⛔ 25,39 %          |        0,00 %
	     *
	     *     ⚠ La colonna di destra non e' «quasi giusta»: e' ESATTAMENTE la
	     *     curva cubica di PulseAudio (0,25³ = 1,56 %, e 25,9 × 0,0156 = 0,40).
	     *     La colonna di sinistra e' piatta: il volume non arriva, MUTE
	     *     COMPRESO — nella sessione viva il nodo era a `channelVolumes 0.0` e
	     *     `mute true` mentre il client riceveva il segnale intero.
	     *
	     * ⚠ E il verso conta, ed e' il motivo per cui questo e' l'unico cursore
	     *   che puo' funzionare: in RCP il volume NON viaggia (`RCP.md` §5.3,
	     *   invariante I5), quindi l'unico livello che governa davvero e' quello
	     *   che si vede dentro la sessione.
	     */
	    "monitor.channel-volumes", "true",
	    /*
	     * ⛔ E CHE NESSUNO CI RIMETTA I LIVELLI DI IERI.
	     *    WirePlumber salva volume e mute per NOME del nodo e li rimette quando
	     *    il nodo ricompare — `[M]` 8 agosto 2026: il sink NUOVO nasceva a
	     *    `0.008` e `mute true`, cioe' col valore che l'utente aveva messo in
	     *    una sessione finita.  E' esattamente lo stato invisibile che I5 vuole
	     *    rendere impossibile.
	     *
	     * ⚠ La chiave e' un SUGGERIMENTO: se la versione di WirePlumber non la
	     *   conosce non fa niente e non da' errore.  ⇒ Non ci si conta sopra — il
	     *   volume si rialza comunque a ogni collegamento e a ogni avvio della
	     *   cattura (`CODER.md` §I7: la protezione sta nel programma).
	     */
	    "state.restore-props", "false",
	    /* Il nodo muore con la nostra connessione a PipeWire, e va bene cosi':
	     * appartiene alla sessione servita, non alla macchina.  Lasciarlo dietro
	     * significherebbe che un REMOTIX riavviato ne trova due — e allora
	     * `target.object` diventerebbe ambiguo. */
	    PW_KEY_OBJECT_LINGER, "false", NULL);

	if (!proprieta)
	{
		registro_dice(REG_SUONO, "⛔ proprieta' del sink non allocate");
		return false;
	}

	s->sink = pw_core_create_object(s->nucleo, "adapter", PW_TYPE_INTERFACE_Node, PW_VERSION_NODE,
	                                &proprieta->dict, 0);
	pw_properties_free(proprieta);

	if (!s->sink)
	{
		registro_dice(REG_SUONO, "⛔ PipeWire non ha creato il sink virtuale «%s»", NOME_SINK);
		return false;
	}
	pw_proxy_add_listener(s->sink, &s->gancio_sink, &eventi_sink, s);

	/* ⚠ Si aspetta l'identificativo del nodo, non la creazione: `bound` e' il
	 *   momento in cui il server ha DAVVERO registrato l'oggetto.  Chi tornasse
	 *   prima avrebbe in mano un proxy che potrebbe ancora fallire, e il rifiuto
	 *   comparirebbe piu' tardi come silenzio. */
	scadenza = registro_ora_ms() + ATTESA_SINK_MS;
	while (s->nodo == 0 && registro_ora_ms() < scadenza)
		pw_thread_loop_timed_wait(s->ciclo, 1);

	if (s->nodo == 0)
	{
		registro_dice(REG_SUONO, "⛔ il sink virtuale non e' stato registrato entro %d ms",
		              ATTESA_SINK_MS);
		return false;
	}
	alza(s);
	return true;
}

/* ⛔ `pw_init()` una volta sola per processo, e la chiama anche `cattura.c`:
 *    non e' sincronizzata da se', e il figlio apre il palco e il suono da due
 *    momenti diversi.  ⚠ `pthread_once` e non un `bool`, perche' «di solito
 *    succede prima» non e' una sincronizzazione. */
static pthread_once_t una_volta = PTHREAD_ONCE_INIT;

static void inizializza_pipewire(void)
{
	pw_init(NULL, NULL);
}

suono *suono_apri(void)
{
	suono *s = calloc(1, sizeof *s);

	if (!s)
		return NULL;
	pthread_once(&una_volta, inizializza_pipewire);

	atomic_init(&s->consegna, false);
	atomic_init(&s->in_richiamo, false);
	atomic_init(&s->blocchi, 0);
	atomic_init(&s->fotogrammi, 0);
	atomic_init(&s->scartati, 0);
	atomic_init(&s->picco, 0);

	s->ciclo = pw_thread_loop_new("remotix-suono", NULL);
	if (!s->ciclo)
	{
		registro_dice(REG_SUONO, "⛔ ciclo PipeWire non creato");
		goto guasto;
	}
	s->contesto = pw_context_new(pw_thread_loop_get_loop(s->ciclo), NULL, 0);
	if (!s->contesto)
	{
		registro_dice(REG_SUONO, "⛔ contesto PipeWire non creato");
		goto guasto;
	}

	pw_thread_loop_lock(s->ciclo);
	if (pw_thread_loop_start(s->ciclo) < 0)
	{
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ thread di PipeWire non avviato");
		goto guasto;
	}

	s->nucleo = pw_context_connect(s->contesto, NULL, 0);
	if (!s->nucleo)
	{
		pw_thread_loop_unlock(s->ciclo);
		/* ⚠ Il caso normale in cui questa fallisce: `PIPEWIRE_RUNTIME_DIR` /
		 *   `XDG_RUNTIME_DIR` che non punta alla sessione servita.  Lo si dice
		 *   per nome, o la diagnosi ricomincia da zero (`CODER.md` §3.7). */
		registro_dice(REG_SUONO, "⛔ connessione a PipeWire fallita: si guarda XDG_RUNTIME_DIR "
		                         "e se il servizio gira nella sessione");
		goto guasto;
	}

	if (!crea_sink(s))
	{
		pw_thread_loop_unlock(s->ciclo);
		goto guasto;
	}
	pw_thread_loop_unlock(s->ciclo);

	registro_dice(REG_SUONO, "⭐ sink audio «%s» montato nella sessione: nodo %u, %d Hz, %d canali "
	                         "— e' della SESSIONE, sopravvive al distacco (I4)",
	              NOME_SINK, s->nodo, (int) AUDIO_FREQUENZA, (int) AUDIO_CANALI);
	return s;

guasto:
	suono_chiudi(s);
	return NULL;
}

bool suono_ascolto_avvia(suono *s, suono_campioni su_campioni, void *chi)
{
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];
	struct spa_audio_info_raw formato = { 0 };
	struct pw_properties *proprieta;
	uint64_t scadenza;

	if (!s || !s->nucleo || !su_campioni)
		return false;

	/*
	 * ⛔ QUI, E NON SOLO ALLA CREAZIONE.  Chi ripristina i livelli salvati lo fa
	 *    quando il nodo COMPARE, cioe' subito dopo che l'abbiamo alzato noi: alla
	 *    creazione si perde la corsa, e il primo collegamento dopo un riavvio
	 *    arriva muto.  L'avvio della cattura e' il momento piu' tardi di cui
	 *    disponiamo, e a quel punto la corsa e' finita.  `[M]` 8 agosto 2026.
	 */
	suono_volume_massimo(s);

	pw_thread_loop_lock(s->ciclo);

	if (s->flusso)
	{
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ la cattura audio e' gia' accesa: la seconda non si apre");
		return false;
	}

	s->su_campioni = su_campioni;
	s->chi = chi;
	s->stato = PW_STREAM_STATE_UNCONNECTED;
	atomic_store(&s->blocchi, 0);
	atomic_store(&s->fotogrammi, 0);
	atomic_store(&s->scartati, 0);
	atomic_store(&s->picco, 0);
	/* ⚠ Accesa PRIMA di collegare il flusso, e spenta da `su_parametri` se il
	 *   formato negoziato non e' quello di §5.3: il primo richiamo puo' arrivare
	 *   prima che questa funzione torni. */
	atomic_store(&s->consegna, true);

	proprieta = pw_properties_new(PW_KEY_MEDIA_TYPE, "Audio", PW_KEY_MEDIA_CATEGORY, "Capture",
	                              /* Le due righe che decidono DA DOVE si cattura: il
	                               * MONITOR (l'uscita) del nostro sink, e non
	                               * l'ingresso di un microfono che qui non esiste. */
	                              PW_KEY_STREAM_CAPTURE_SINK, "true", PW_KEY_TARGET_OBJECT,
	                              NOME_SINK, PW_KEY_NODE_FORCE_QUANTUM, QUANTO_FORZATO, NULL);
	s->flusso = proprieta ? pw_stream_new(s->nucleo, "remotix-suono", proprieta) : NULL;
	if (!s->flusso)
	{
		atomic_store(&s->consegna, false);
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ flusso PipeWire non creato");
		return false;
	}
	pw_stream_add_listener(s->flusso, &s->gancio_flusso, &eventi_flusso, s);

	/*
	 * ⛔ IL FORMATO SI CHIEDE FISSO, e non e' una preferenza: `RCP.md` §5.3.
	 *    PipeWire ricampiona per conto suo fra il sink e questo flusso, cosi' fra
	 *    il monitor e il filo non resta nessuna conversione da fare — il
	 *    codificatore riceve gia' i campioni giusti, e non si dipende da quali
	 *    ricampionatori sia stata compilata `libavcodec`.
	 */
	formato.format = SPA_AUDIO_FORMAT_S16;
	formato.rate = AUDIO_FREQUENZA;
	formato.channels = AUDIO_CANALI;
	formato.position[0] = SPA_AUDIO_CHANNEL_FL;
	formato.position[1] = SPA_AUDIO_CHANNEL_FR;
	parametri[0] = spa_format_audio_raw_build(&costruttore, SPA_PARAM_EnumFormat, &formato);

	/* ⛔ `PW_STREAM_FLAG_RT_PROCESS`: la richiamata gira sul thread di tempo
	 *    reale.  E' voluto — un salto in mezzo al ciclo principale sarebbe un
	 *    quanto di ritardo in piu' su un anello che ne ha 50 in tutto — e il
	 *    prezzo e' il contratto scritto in `suono.h`: dentro si copia e si torna. */
	if (pw_stream_connect(s->flusso, PW_DIRECTION_INPUT, PW_ID_ANY,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, 1) < 0)
	{
		pw_stream_destroy(s->flusso);
		s->flusso = NULL;
		atomic_store(&s->consegna, false);
		pw_thread_loop_unlock(s->ciclo);
		registro_dice(REG_SUONO, "⛔ aggancio al monitor del sink «%s» fallito", NOME_SINK);
		return false;
	}

	/* ⛔ Si aspetta `paused`: e' il momento in cui il formato e' stato negoziato,
	 *    cioe' l'unico in cui un rifiuto si vede subito. */
	scadenza = registro_ora_ms() + ATTESA_ASCOLTO_MS;
	while (s->stato != PW_STREAM_STATE_PAUSED && s->stato != PW_STREAM_STATE_STREAMING &&
	       s->stato != PW_STREAM_STATE_ERROR && registro_ora_ms() < scadenza)
		pw_thread_loop_timed_wait(s->ciclo, 1);
	pw_thread_loop_unlock(s->ciclo);

	if (s->stato == PW_STREAM_STATE_ERROR)
	{
		registro_dice(REG_SUONO, "⛔ cattura audio rifiutata: %s",
		              s->guasto ? s->guasto : "senza spiegazione");
		suono_ascolto_ferma(s);
		return false;
	}
	if (s->stato != PW_STREAM_STATE_PAUSED && s->stato != PW_STREAM_STATE_STREAMING)
	{
		registro_dice(REG_SUONO, "⛔ la cattura audio non ha dato segno di vita entro %d ms",
		              ATTESA_ASCOLTO_MS);
		suono_ascolto_ferma(s);
		return false;
	}

	registro_dice(REG_SUONO,
	              "⭐ cattura audio avviata dal monitor di «%s»: %d Hz, %d canali, s16, quanto %s "
	              "— ⚠ i blocchi hanno misura VARIABILE, chi ascolta accumula (suono.h)",
	              NOME_SINK, (int) AUDIO_FREQUENZA, (int) AUDIO_CANALI, QUANTO_FORZATO);
	return true;
}

/*
 * ⛔⛔ L'ATTESA PROMESSA, E FATTA — v1 la prometteva e NON la faceva.
 *
 * Il commento di v1 diceva: «Il lucchetto del ciclo E' l'attesa promessa
 * nell'intestazione: PipeWire lo tiene mentre chiama `su_processo`».  ⛔ E' FALSO
 * quando il flusso e' collegato con `PW_STREAM_FLAG_RT_PROCESS`, che e'
 * precisamente il nostro caso: `[R]` `pipewire/stream.h:150` e `:466` — la
 * richiamata arriva dal **thread dei dati**, che e' un altro thread, e il
 * lucchetto del ciclo non lo ferma affatto.
 *
 * ⚠ Il difetto non si sarebbe quasi mai visto: la finestra e' di microsecondi, a
 *   ogni distacco.  ⛔ E quando si vede e' un segfault dentro un thread che non
 *   ha il nostro nome, con in mano il contesto della connessione appena
 *   liberata — cioe' la forma d'errore piu' cara che ci sia, perche' nessuno la
 *   collega alla riconnessione che l'ha prodotta.
 *
 * ⇒ L'attesa e' in due tempi, e il primo NON dipende da come sia fatta
 *   `pw_stream_destroy()` dentro:
 *
 *   1. si spegne `consegna` e si aspetta che `in_richiamo` torni falso.  Da qui
 *      in poi nessun richiamo di chi ascolta e' in volo, e nessuno ne partira'
 *      piu' (le due scritture sequenzialmente coerenti si vedono a vicenda: vedi
 *      `su_processo`).  ⭐ Questo, e solo questo, e' cio' che autorizza il
 *      chiamante a liberare il suo contesto;
 *   2. si distrugge il flusso tenendo il lucchetto del ciclo.  ⚠ Che nessuna
 *      `dequeue` sia a meta' strada quando il flusso muore e' responsabilita' di
 *      `pw_stream_destroy()`, che toglie il nodo dal ciclo dei dati **fra un
 *      quanto e l'altro** — e' la stessa garanzia su cui poggia ogni programma
 *      che usa PipeWire, e non e' una cosa che possiamo rifare noi da fuori.
 *
 * ⚠ L'attesa del punto 1 sta FUORI dal lucchetto: prenderlo mentre si aspetta il
 *   thread dei dati sarebbe il modo di trovarsi in mezzo a un abbraccio mortale
 *   il giorno in cui PipeWire cambiasse idea su chi tiene che cosa.
 */
static void aspetta_richiamo(suono *s)
{
	uint64_t inizio = registro_ora_ms();

	while (atomic_load(&s->in_richiamo))
	{
		struct timespec pausa = { 0, 200 * 1000 }; /* 200 µs: un quanto e' 5 ms */

		nanosleep(&pausa, NULL);
		if (registro_ora_ms() - inizio > ATTESA_BARRIERA_MS)
		{
			/* ⛔ Si esce lo stesso, e SI DICHIARA.  Restare qui per sempre
			 *    vorrebbe dire una sessione congelata, e «una sessione brutta
			 *    vale piu' di una sessione chiusa» (`CODER.md` §1) non arriva
			 *    fino a «una sessione appesa».  ⚠ Ma chi legge questa riga sa che
			 *    il contesto della connessione NON si puo' liberare: PipeWire e'
			 *    fermo dentro un richiamo da due secondi. */
			registro_dice(REG_SUONO,
			              "⛔⛔ il thread di tempo reale non e' uscito dal richiamo entro %d ms: "
			              "NON liberare il contesto dell'ascolto — PipeWire e' bloccato",
			              ATTESA_BARRIERA_MS);
			return;
		}
	}
}

void suono_ascolto_ferma(suono *s)
{
	if (!s || !s->ciclo)
		return;

	/* 1. la barriera verso chi ascolta (vedi il riquadro). */
	atomic_store(&s->consegna, false);
	aspetta_richiamo(s);

	/* 2. il flusso, sotto il lucchetto del ciclo. */
	pw_thread_loop_lock(s->ciclo);
	if (s->flusso)
	{
		struct pw_stream *flusso = s->flusso;
		uint64_t blocchi = atomic_load(&s->blocchi);
		uint64_t fotogrammi = atomic_load(&s->fotogrammi);
		uint64_t scartati = atomic_load(&s->scartati);

		s->flusso = NULL;
		pw_stream_destroy(flusso);
		/* ⭐ Il riassunto si stampa QUI, dal thread di chi ferma, e non dal
		 *    thread di tempo reale che l'ha contato.  ⚠ «zero blocchi» e' un
		 *    fatto, non un vuoto: dice che il monitor non ha consegnato niente,
		 *    e va distinto dai fotogrammi SCARTATI (formato rifiutato).
		 *
		 * ⛔⭐ E IL PICCO SI LEGGE PRIMA DI OGNI ALTRA COSA quando qualcuno dice
		 *     «non si sente niente»:
		 *       · picco 0  con blocchi > 0  ⇒ i campioni arrivano VUOTI —
		 *         nella sessione non suonava nessuno, oppure il monitor non e'
		 *         collegato.  Si guarda il grafo (`pw-link -l`), e lo si
		 *         guarda MENTRE la sessione e' viva;
		 *       · picco > 0                 ⇒ il suono e' entrato in REMOTIX, e
		 *         chi lo perde sta piu' avanti (l'anello, il codificatore, i
		 *         datagram).  `[M]` 17 agosto 2026: 16383 su 32767 con un tono
		 *         a 440 Hz — cioe' esattamente quel che `pw-record` legge dallo
		 *         stesso monitor nello stesso istante. */
		registro_dice(REG_SUONO,
		              "cattura audio fermata: %llu blocchi, %llu fotogrammi consegnati "
		              "(%llu s di suono), %llu fotogrammi scartati, PICCO %llu su 32767",
		              (unsigned long long) blocchi, (unsigned long long) fotogrammi,
		              (unsigned long long) (fotogrammi / AUDIO_FREQUENZA),
		              (unsigned long long) scartati,
		              (unsigned long long) atomic_load(&s->picco));
	}
	s->su_campioni = NULL;
	s->chi = NULL;
	pw_thread_loop_unlock(s->ciclo);
}

uint32_t suono_nodo(const suono *s)
{
	return s ? s->nodo : 0;
}

bool suono_ascolto_vivo(const suono *s)
{
	bool vivo;

	if (!s || !s->ciclo || !s->flusso)
		return false;
	/* ⚠ Sotto il lucchetto perche' `stato` lo scrive il thread del ciclo.  Il
	 *   `const` e' del puntatore a `suono`, non del ciclo di PipeWire: qui non si
	 *   cambia niente di nostro. */
	pw_thread_loop_lock(s->ciclo);
	vivo = s->flusso && (s->stato == PW_STREAM_STATE_PAUSED ||
	                     s->stato == PW_STREAM_STATE_STREAMING);
	pw_thread_loop_unlock(s->ciclo);
	return vivo;
}

void suono_conti(const suono *s, uint64_t *blocchi, uint64_t *fotogrammi, uint64_t *scartati)
{
	if (blocchi)
		*blocchi = s ? atomic_load(&s->blocchi) : 0;
	if (fotogrammi)
		*fotogrammi = s ? atomic_load(&s->fotogrammi) : 0;
	if (scartati)
		*scartati = s ? atomic_load(&s->scartati) : 0;
}

void suono_chiudi(suono *s)
{
	if (!s)
		return;

	/* ⛔ Prima la barriera e il flusso, poi il thread, poi il resto — e l'ordine
	 *    e' quello di `cattura.c`, per lo stesso motivo: cosi' non si tocca
	 *    niente che una richiamata stia usando.  ⚠ `suono_ascolto_ferma()` regge
	 *    l'oggetto mezzo costruito (il caso `goto guasto` di `suono_apri`) perche'
	 *    guarda `ciclo` e `flusso` prima di ogni cosa. */
	suono_ascolto_ferma(s);

	if (s->ciclo)
		pw_thread_loop_stop(s->ciclo);
	if (s->sink)
		pw_proxy_destroy(s->sink);
	if (s->nucleo)
		pw_core_disconnect(s->nucleo);
	if (s->contesto)
		pw_context_destroy(s->contesto);
	if (s->ciclo)
		pw_thread_loop_destroy(s->ciclo);

	free(s->guasto);
	free(s);
}
