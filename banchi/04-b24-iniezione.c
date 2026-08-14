/*
 * 04-b24-iniezione.c — IL BANCO dell'anello A4: l'input arriva DAVVERO al
 * desktop?
 *
 *   ./04-b24-iniezione [--tela 1920x1080]     apre e aspetta comandi su stdin
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA E' QUESTO PROGRAMMA, E CHE COSA NON E'
 *
 * ⭐ E' `CODER.md` §3.6 preso alla lettera — *«isola UNA funzione sola, e
 *    chiamala da fuori»*.  Questo programma **linka il modulo del prodotto**
 *    (`src/input.c`, `src/mutter.c`, `src/tastiera.c`) e ne chiama le funzioni
 *    di `src/input.h` una per una, da riga di comando.  ⛔ Non c'e' QUIC, non
 *    c'e' `rcp.c`, non c'e' il formato dei messaggi: se il puntatore non si
 *    muove, la causa sta in due file e non in venti.
 *
 * ⛔ **NON E' LA MISURA.**  Questo e' l'INIETTORE.  Quel che dice — «mandato»,
 *    «pronto», «regione nota» — e' il registro di **chi manda**, e
 *    `CODER.md` §3.8 dice che non vale niente: dice che abbiamo chiamato una
 *    funzione, non che il desktop ha ricevuto qualcosa.
 *
 *    ⇒ La misura la fa **la pagina** (`04-b24-pagina.html`), che gira dentro la
 *      sessione, sul monitor che questo programma monta, e spedisce al
 *      raccoglitore quel che il DESKTOP ha visto: `deltaY`, `scrollY`,
 *      `clientX/Y`, `key`.  Il verdetto lo da' `04-b24-lancia.sh` confrontando
 *      i due lati.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' C'E' DENTRO UN CONSUMATORE PIPEWIRE, CHE COL­L'INPUT NON C'ENTRA
 *
 * `[R]` `meta-screen-cast-virtual-stream-src.c:279-283`: il flusso diventa
 * *configured* — e solo allora Mutter aggiunge il **viewport** da cui nasce il
 * dispositivo assoluto — dentro `..._src_enable`, cioe' **quando qualcuno
 * comincia davvero a leggere i fotogrammi**.
 *
 * ⇒ Senza un consumatore: zero viewport, `add_viewport_devices` esce subito
 *   (`meta-eis-client.c:796-798`, con tanto di `FIXME: should be an error`), e
 *   ⛔ **il dispositivo assoluto non nasce affatto — senza nessun errore**.
 *   Un banco che non consuma misurerebbe un silenzio e lo chiamerebbe difetto.
 *
 * ⚠ E c'e' la seconda meta', che e' quella che l'utente vede: la sessione di
 *   `prova` non ha monitor propri (`fasi/rapporti/F5-desktop-vero.md`), quindi
 *   **finche' non si consuma non c'e' nemmeno un desktop dove iniettare**.
 *
 * ---------------------------------------------------------------------------
 * I COMANDI (uno per riga; ogni risposta comincia con «B24: »)
 *
 *   punta X Y            input_puntatore
 *   pulsante C P         input_pulsante        (C evdev: BTN_LEFT = 272)
 *   rotella DX DY        input_rotella         (unita' da 120 per scatto)
 *   posizione C P        input_posizione       (C evdev: KEY_A = 30)
 *   lettera N            input_lettera         (N = valore scalare Unicode)
 *   rilascia             input_rilascia_tutto  → stampa QUANTI ne ha rilasciati
 *   stato                il conto, i ricambi, la regione
 *   ridimensiona L A     ⛔ il RICAMBIO SILENZIOSO: rinegozia il flusso a una
 *                        misura diversa, cioe' fa cambiare la geometria SOTTO
 *                        un dispositivo assoluto gia' in uso
 *   staccati             ⛔ chiude come farebbe un client che se ne va SENZA
 *                        rilasciare: stampa il conto e esce con 0
 *   fine                 esce pulito
 */
#include <errno.h>
#include <gio/gio.h>
#include <pipewire/pipewire.h>
#include <poll.h>
#include <spa/param/video/format-utils.h>
#include <spa/utils/result.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "input.h"
#include "mutter.h"
#include "registro.h"
#include "tastiera.h"

/* ⛔ La finestra di banco di `src/input.c`: NON sta in `input.h`, che e' il
 *    contratto del prodotto e appartiene al coordinatore.  Si dichiara qui. */
extern void input_conto(const Input *, unsigned *tasti, unsigned *pulsanti,
                        unsigned *ricambi_puntatore, unsigned *ricambi_tastiera, int *pronto);

#define ATTESA_FLUSSO_S 15

/*
 * ------------------------------------------------------------------------
 * ⛔⛔ UN RIPIEGO **DEBOLE**, E DICHIARATO — non e' nel prodotto, e' qui.
 *
 * `src/tastiera.h` dichiara `tastiera_apri_da_keymap()` (cucitura del
 * coordinatore, 14 agosto 2026) e `src/input.c` la chiama, com'e' giusto: la
 * disposizione della sessione arriva da `libei`, non da una stringa.
 * ⚠ Ma alla stessa ora l'anello **A5** non l'ha ancora attuata in
 *   `src/tastiera.c`, e il collegamento del banco si ferma su un simbolo
 *   mancante.  ⛔ E' il caso che il mandato prevede — *«se il collegamento non
 *   riesce perche' la sua e' ancora un abbozzo, e' atteso: dichiaralo»*.
 *
 * ⇒ Qui c'e' una definizione **`weak`**: se `tastiera.c` porta la sua, vince
 *   la sua e questa sparisce; se non la porta, il banco gira lo stesso e ⛔
 *   **stampa una riga che marca come RIPIEGO ogni misura sulle lettere**.
 *
 * ⛔ Quel che il ripiego NON fa: non guarda la keymap che gli passi.  ⇒ Le
 *    misure sulle LETTERE fatte con questo ripiego valgono `[?]`, non `[M]`, e
 *    il rapporto lo dice.  Puntatore, pulsanti, rotella e POSIZIONI non
 *    passano di qui e restano `[M]`.
 * ------------------------------------------------------------------------
 */
__attribute__((weak)) Tastiera *tastiera_apri_da_keymap(const char *testo, size_t lunghezza,
                                                        const char *negoziata, char **errore)
{
	static int detto = 0;

	(void) testo;
	(void) negoziata;
	if (!detto)
	{
		detto = 1;
		fprintf(stdout,
		        "B24: ⛔ RIPIEGO DEL BANCO: `tastiera_apri_da_keymap` non e' attuata in "
		        "src/tastiera.c (anello A5).  Apro la disposizione per NOME e IGNORO i %zu byte "
		        "di keymap che libei ha consegnato.  ⇒ ogni misura sulle LETTERE che segue vale "
		        "[?], non [M].\n",
		        lunghezza);
		fflush(stdout);
	}
	return tastiera_apri(NULL, errore);
}

static void dilo(const char *forma, ...)
{
	va_list argomenti;

	fputs("B24: ", stdout);
	va_start(argomenti, forma);
	vfprintf(stdout, forma, argomenti);
	va_end(argomenti);
	fputc('\n', stdout);
	fflush(stdout);
}

/* ------------------------------------------------------------------ *
 *  Il consumatore PipeWire, ridotto all'osso: non guarda i pixel.
 *
 *  ⛔ E infatti NON DEVE guardarli — sarebbe il mestiere di `cattura.c`, che
 *     e' di un altro anello.  Qui serve solo che qualcuno **legga**, perche'
 *     e' la lettura che fa nascere il viewport.
 * ------------------------------------------------------------------ */
typedef struct
{
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;
	enum pw_stream_state stato;
	char *guasto;
	unsigned long fotogrammi;
	uint32_t nodo;
	uint32_t larghezza, altezza;
} Consumo;

static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	Consumo *c = dati;

	(void) vecchio;
	c->stato = nuovo;
	if (errore)
	{
		g_free(c->guasto);
		c->guasto = g_strdup(errore);
	}
	pw_thread_loop_signal(c->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Consumo *c = dati;
	struct spa_video_info_raw formato;
	uint32_t tipo, sottotipo;
	uint8_t spazio[512];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &tipo, &sottotipo) < 0)
		return;
	if (tipo != SPA_MEDIA_TYPE_video || sottotipo != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &formato) < 0)
		return;

	parametri[0] = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int((1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr)));
	pw_stream_update_params(c->flusso, parametri, 1);
	pw_thread_loop_signal(c->ciclo, false);
}

static void su_processo(void *dati)
{
	Consumo *c = dati;
	struct pw_buffer *pacco = pw_stream_dequeue_buffer(c->flusso);

	if (!pacco)
		return;
	c->fotogrammi++;
	pw_stream_queue_buffer(c->flusso, pacco);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

static const struct spa_pod *formato_di(struct spa_pod_builder *b, uint32_t l, uint32_t a)
{
	struct spa_rectangle misura = SPA_RECTANGLE(l, a);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction minima = SPA_FRACTION(1, 1);
	struct spa_fraction massima = SPA_FRACTION(60, 1);

	return spa_pod_builder_add_object(
	    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format,
	    SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx), SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura),
	    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&massima, &minima, &massima));
}

static gboolean aggancia(Consumo *c, uint32_t l, uint32_t a)
{
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1] = { formato_di(&costruttore, l, a) };
	gint64 scadenza;

	c->larghezza = l;
	c->altezza = a;
	pw_thread_loop_lock(c->ciclo);
	if (pw_stream_connect(c->flusso, PW_DIRECTION_INPUT, c->nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS, parametri,
	                      1) < 0)
	{
		pw_thread_loop_unlock(c->ciclo);
		dilo("ERRORE: aggancio al nodo %u fallito", c->nodo);
		return FALSE;
	}
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_FLUSSO_S * G_USEC_PER_SEC;
	while (c->stato != PW_STREAM_STATE_STREAMING && c->stato != PW_STREAM_STATE_ERROR &&
	       g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(c->ciclo, 1);
	pw_thread_loop_unlock(c->ciclo);

	if (c->stato != PW_STREAM_STATE_STREAMING)
	{
		/* ⛔ «Non attivo» e «attivo ma fermo» sono due cose diverse: si stampa
		 *    lo stato, non un verdetto. */
		dilo("ERRORE: il flusso non e' attivo (stato %d, %s)", (int) c->stato,
		     c->guasto ?: "senza spiegazione");
		return FALSE;
	}
	dilo("flusso attivo a %ux%u sul nodo %u", l, a, c->nodo);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 *  Il programma
 * ------------------------------------------------------------------ */
static MutterSessione *sessione;
static Input *canale;
static Consumo consumo;
static uint32_t tela_l = 1920, tela_a = 1080;

static void stampa_stato(void)
{
	unsigned tasti = 0, pulsanti = 0, rp = 0, rt = 0;
	int pronto = 0;

	input_conto(canale, &tasti, &pulsanti, &rp, &rt, &pronto);
	dilo("STATO pronto=%d tasti_premuti=%u pulsanti_premuti=%u ricambi_puntatore=%u "
	     "ricambi_tastiera=%u fotogrammi=%lu",
	     pronto, tasti, pulsanti, rp, rt, consumo.fotogrammi);
}

static void comando(char *riga)
{
	long a1, a2;

	g_strstrip(riga);
	if (!*riga)
		return;

	if (g_str_equal(riga, "fine"))
	{
		dilo("fine");
		input_chiudi(canale);
		mutter_chiudi(sessione);
		exit(0);
	}
	if (g_str_equal(riga, "stato"))
	{
		stampa_stato();
		return;
	}
	if (g_str_equal(riga, "rilascia"))
	{
		int quanti = input_rilascia_tutto(canale);

		/* ⛔ IL NUMERO, perche' il banco possa contarlo — `RCP.md` §11. */
		dilo("RILASCIATI %d", quanti);
		return;
	}
	if (g_str_equal(riga, "staccati"))
	{
		/*
		 * ⛔ Il distacco SENZA rilascio: e' il caso che `RCP.md` §11 chiama «il
		 *    rapporto danno/costo piu' alto del documento».  Qui si esce
		 *    lasciando il conto pieno, e chi guarda vede quanti erano.
		 */
		stampa_stato();
		dilo("STACCATO senza rilasciare: esco");
		exit(0);
	}
	if (sscanf(riga, "punta %ld %ld", &a1, &a2) == 2)
	{
		dilo("punta %ld %ld -> %d", a1, a2,
		     input_puntatore(canale, (uint32_t) a1, (uint32_t) a2));
		return;
	}
	if (sscanf(riga, "pulsante %ld %ld", &a1, &a2) == 2)
	{
		dilo("pulsante %ld %ld -> %d", a1, a2,
		     input_pulsante(canale, (uint16_t) a1, (int) a2));
		return;
	}
	if (sscanf(riga, "rotella %ld %ld", &a1, &a2) == 2)
	{
		dilo("rotella %ld %ld -> %d", a1, a2,
		     input_rotella(canale, (int32_t) a1, (int32_t) a2));
		return;
	}
	if (sscanf(riga, "posizione %ld %ld", &a1, &a2) == 2)
	{
		dilo("posizione %ld %ld -> %d", a1, a2,
		     input_posizione(canale, (uint16_t) a1, (int) a2));
		return;
	}
	if (sscanf(riga, "lettera %ld", &a1) == 1)
	{
		/* ⛔ Tre esiti, tre numeri: 0 mandata, 1 NON producibile, -1 guasto.
		 *    Confonderli e' precisamente quel che `RCP.md` §7.3 vieta. */
		dilo("lettera %ld -> %d", a1, input_lettera(canale, (uint32_t) a1));
		return;
	}
	if (sscanf(riga, "ritela %ld %ld", &a1, &a2) == 2)
	{
		/* ⛔ `TELA(ADATTATA)` di `RCP.md` §7.1, chiamata da fuori: e' il caso in
		 *    cui il CLIENT cambia tela senza che il monitor cambi. */
		dilo("ritela %ld %ld -> %d", a1, a2,
		     input_ritela(canale, (uint32_t) a1, (uint32_t) a2));
		tela_l = (uint32_t) a1;
		tela_a = (uint32_t) a2;
		return;
	}
	if (sscanf(riga, "ridimensiona %ld %ld", &a1, &a2) == 2)
	{
		/*
		 * ⛔⛔ IL BANCO DEI RICAMBI.  `[R]` `meta-eis-client.c:1048-1062`: un
		 *      cambio di geometria **rimuove e ricrea** tutti i dispositivi
		 *      assoluti, e il puntatore al dispositivo vecchio smette di
		 *      funzionare SENZA ERRORE.
		 *
		 *      Qui la geometria si cambia **mentre il dispositivo e' in uso**,
		 *      rinegoziando il flusso: Mutter rifa' il monitor virtuale alla
		 *      misura nuova, e da li' `monitors-changed` →
		 *      `meta_eis_viewport_notify_changed` → `update_viewports`.
		 *
		 * ⚠ Se dopo questo comando `ricambi_puntatore` resta a 0, il difetto
		 *   NON e' stato riprodotto — e il banco lo DICHIARA invece di
		 *   scrivere «verde».
		 */
		pw_thread_loop_lock(consumo.ciclo);
		pw_stream_disconnect(consumo.flusso);
		consumo.stato = PW_STREAM_STATE_UNCONNECTED;
		pw_thread_loop_unlock(consumo.ciclo);
		g_usleep(500 * 1000);
		if (!aggancia(&consumo, (uint32_t) a1, (uint32_t) a2))
			dilo("ERRORE: il flusso non si e' riagganciato a %ldx%ld", a1, a2);
		else
			dilo("RIDIMENSIONATO a %ldx%ld", a1, a2);
		return;
	}
	dilo("comando ignoto: «%s»", riga);
}

int main(int argc, char **argv)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *errore = NULL;
	struct pollfd sonda;
	char riga[256];

	setvbuf(stdout, NULL, _IOLBF, 0);
	registro_parlantina(TRUE);

	for (int i = 1; i < argc; i++)
		if (!strcmp(argv[i], "--tela") && i + 1 < argc)
			sscanf(argv[++i], "%ux%u", &tela_l, &tela_a);

	/* --- 1. la sessione del PRODOTTO, ConnectToEIS compreso ---------------- */
	sessione = mutter_apri(&sbaglio);
	if (!sessione)
	{
		dilo("ERRORE: mutter_apri: %s", sbaglio->message);
		return 2;
	}
	dilo("sessione aperta: nodo %u, descrittore EIS %d", mutter_nodo(sessione),
	     mutter_eis_fd(sessione));

	/* ⭐ LA TESI 4, MISURATA E NON DEDOTTA: i due mapping-id, stampati vicini. */
	dilo("mapping-id DICHIARATO da noi a RecordVirtual: «%s»", mutter_mapping_id(sessione) ?: "?");
	dilo("mapping-id PUBBLICATO da Mutter nei Parameters: «%s»",
	     mutter_mapping_id_pubblicato(sessione) ?: "assente");

	/* --- 2. il consumatore: senza, il viewport non nasce ------------------- */
	pw_init(&argc, &argv);
	consumo.nodo = mutter_nodo(sessione);
	consumo.ciclo = pw_thread_loop_new("b24", NULL);
	consumo.contesto = pw_context_new(pw_thread_loop_get_loop(consumo.ciclo), NULL, 0);
	pw_thread_loop_lock(consumo.ciclo);
	if (pw_thread_loop_start(consumo.ciclo) < 0)
	{
		pw_thread_loop_unlock(consumo.ciclo);
		dilo("ERRORE: thread PipeWire non avviato");
		return 2;
	}
	consumo.nucleo = pw_context_connect(consumo.contesto, NULL, 0);
	if (!consumo.nucleo)
	{
		pw_thread_loop_unlock(consumo.ciclo);
		dilo("ERRORE: PipeWire non risponde");
		return 2;
	}
	consumo.flusso =
	    pw_stream_new(consumo.nucleo, "04-b24",
	                  pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY,
	                                    "Capture", PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(consumo.flusso, &consumo.gancio, &eventi, &consumo);
	pw_thread_loop_unlock(consumo.ciclo);

	if (!aggancia(&consumo, tela_l, tela_a))
		return 2;

	/* ⭐ E ADESSO il monitor c'e': lo si dichiara per nome, perche' chi apre il
	 *    browser sappia DOVE mandarlo (`mutter.h`, forma E2). */
	if (mutter_monitor_cerca(sessione))
		dilo("MONITOR %s («%s»)", mutter_monitor_nostro(sessione),
		     mutter_monitor_prodotto(sessione));
	else
		dilo("⚠ il nostro monitor non si sa per nome: NON dico quale sia");

	/* --- 3. il modulo sotto prova ----------------------------------------- */
	canale = input_apri(sessione, tela_l, tela_a, &errore);
	if (!canale)
	{
		dilo("ERRORE: input_apri: %s", errore ?: "senza motivo dichiarato");
		return 3;
	}

	/*
	 * ⛔ SI ASPETTA CHE IL DISPOSITIVO SIA PRONTO, e si dice quando lo e'.
	 *    `add_viewport_devices` esce in silenzio se i viewport non ci sono
	 *    ancora: iniettare prima di «PRONTO» vorrebbe dire misurare un silenzio
	 *    che non e' un difetto.
	 */
	{
		gint64 scadenza = g_get_monotonic_time() + 20 * G_USEC_PER_SEC;
		int pronto = 0;

		while (g_get_monotonic_time() < scadenza && !pronto)
		{
			if (input_gira(canale) < 0)
			{
				dilo("ERRORE: il canale di input e' caduto");
				return 3;
			}
			input_conto(canale, NULL, NULL, NULL, NULL, &pronto);
			if (!pronto)
				g_usleep(50 * 1000);
		}
		if (!pronto)
		{
			dilo("ERRORE: nessun dispositivo ASSOLUTO con una regione dopo 20 s");
			stampa_stato();
			return 3;
		}
	}
	dilo("PRONTO");

	/* --- 4. i comandi ----------------------------------------------------- */
	sonda.fd = STDIN_FILENO;
	sonda.events = POLLIN;
	for (;;)
	{
		sonda.revents = 0;
		if (poll(&sonda, 1, 50) < 0 && errno != EINTR)
			break;
		if (input_gira(canale) < 0)
		{
			dilo("ERRORE: il compositore ha chiuso il canale di input");
			return 4;
		}
		if (sonda.revents & POLLIN)
		{
			if (!fgets(riga, sizeof riga, stdin))
			{
				dilo("standard input chiuso: esco");
				break;
			}
			comando(riga);
			input_gira(canale);
		}
		if (sonda.revents & POLLHUP)
			break;
	}

	input_chiudi(canale);
	mutter_chiudi(sessione);
	return 0;
}
