#include "input.h"

#include <errno.h>
#include <fcntl.h>
#include <freerdp/input.h>
#include <gio/gio.h>
#include <glib-unix.h>
#include <libei.h>
#include <math.h>
#include <poll.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#include "registro.h"
#include "tastiera.h"

/* Codici evdev dei bottoni, da `linux/input-event-codes.h`. */
#define BTN_LEFT 0x110
#define BTN_RIGHT 0x111
#define BTN_MIDDLE 0x112
#define BTN_SIDE 0x113
#define BTN_EXTRA 0x114

/* RDP conta la rotella in unita' da 120 per scatto, positive verso l'alto. */
#define UNITA_PER_SCATTO 120.0
/* E uno scatto discreto vale 10 dall'altra parte. */
#define PASSO_ASSE 10.0

/* Tetto agli eventi svuotati in un giro: senza, un client impazzito terrebbe
 * il thread dentro il ciclo di svuotamento a tempo indeterminato. */
#define ACCORPAMENTO_MASSIMO 512

typedef enum
{
	EV_TASTO,
	EV_UNICODE,
	EV_MOUSE,
	EV_MOUSE_ESTESO,
	EV_SINCRONIZZA,
	EV_RILASCIA_TUTTO,
	EV_MISURA,
} TipoEvento;

typedef struct
{
	TipoEvento tipo;
	uint32_t a, b, c;
} Evento;

struct Input
{
	struct ei *ei;
	char *mapping_id;
	/* La rotella si manda come SCATTI invece che come delta continuo: vedi
	 * `manda_scatti`, ed e' la differenza fra i due compositori. */
	gboolean scatti_discreti;

	GThread *thread;
	int sveglia[2]; /* [0] si legge nel thread, [1] ci scrivono le connessioni */
	volatile gint fermare;

	GMutex lucchetto;
	GQueue *coda;

	/* --- da qui in giu' si tocca SOLO dal thread di input --- */
	struct ei_device *puntatore;
	struct ei_device *tastiera_dev;
	gboolean puntatore_attivo;
	gboolean tastiera_attiva;
	uint32_t sequenza;

	Tastiera *tastiera;

	/* La regione su cui riscalare le coordinate assolute. */
	gboolean regione_nota;
	gboolean regione_lamentata;
	double regione_x, regione_y, regione_l, regione_a;

	/* La misura che il client dichiara. */
	uint32_t larghezza, altezza;

	/* Riconciliazione dei lucchetti dopo un ping. */
	struct ei_ping *ping;
	gboolean attesi_noti;
	gboolean atteso_maiusc, atteso_num;

	/*
	 * Lo stato VERO dei lucchetti, quando non arriva da libei.
	 *
	 * Lo scrive un altro thread — quello della pompa Wayland, dentro `kwin.c` —
	 * e lo legge il nostro: si tocca con il lucchetto della coda, che c'e' gia'.
	 */
	gboolean lucchetti_da_fuori;
	gboolean fuori_maiusc, fuori_num;
};

/* ------------------------------------------------------------------ *
 * La coda: si accoda dal thread della connessione, si svuota nel nostro
 * ------------------------------------------------------------------ */
static void accoda(Input *input, TipoEvento tipo, uint32_t a, uint32_t b, uint32_t c)
{
	Evento *evento;

	if (!input)
		return;

	evento = g_new(Evento, 1);
	evento->tipo = tipo;
	evento->a = a;
	evento->b = b;
	evento->c = c;

	g_mutex_lock(&input->lucchetto);
	g_queue_push_tail(input->coda, evento);
	g_mutex_unlock(&input->lucchetto);

	/* Un byte solo, e senza attendere: se la pipe fosse piena il thread ha
	 * comunque gia' di che svegliarsi. */
	if (write(input->sveglia[1], "!", 1) < 0 && errno != EAGAIN)
		traccia("sveglia del thread di input non scritta: %s", g_strerror(errno));
}

void input_tasto(Input *input, uint16_t flags, uint8_t scancode)
{
	accoda(input, EV_TASTO, flags, scancode, 0);
}

void input_tasto_unicode(Input *input, uint16_t flags, uint16_t carattere)
{
	accoda(input, EV_UNICODE, flags, carattere, 0);
}

void input_mouse(Input *input, uint16_t flags, uint16_t x, uint16_t y)
{
	accoda(input, EV_MOUSE, flags, x, y);
}

void input_mouse_esteso(Input *input, uint16_t flags, uint16_t x, uint16_t y)
{
	accoda(input, EV_MOUSE_ESTESO, flags, x, y);
}

void input_sincronizza(Input *input, uint32_t flags)
{
	accoda(input, EV_SINCRONIZZA, flags, 0, 0);
}

void input_rilascia_tutto(Input *input)
{
	accoda(input, EV_RILASCIA_TUTTO, 0, 0, 0);
}

void input_misura(Input *input, uint32_t larghezza, uint32_t altezza)
{
	accoda(input, EV_MISURA, larghezza, altezza, 0);
}

/* ------------------------------------------------------------------ *
 * L'invio, tutto dal thread di input
 * ------------------------------------------------------------------ */
static void manda_tasto(Input *input, uint32_t evdev, gboolean premuto)
{
	if (!input->tastiera_dev || !input->tastiera_attiva)
		return;
	ei_device_keyboard_key(input->tastiera_dev, evdev, premuto);
	ei_device_frame(input->tastiera_dev, ei_now(input->ei));
	traccia("tasto evdev %u %s", evdev, premuto ? "giu'" : "su'");
}

static void batti(Input *input, uint32_t evdev)
{
	manda_tasto(input, evdev, TRUE);
	manda_tasto(input, evdev, FALSE);
}

/*
 * Le coordinate si riscalano sulla regione che libei annuncia, non si passano
 * cosi' come sono: e' la sostituzione elegante del percorso D-Bus dello stream
 * che i metodi `Notify*` volevano.  Col monitor virtuale della misura chiesta
 * la trasformazione e' l'identita', ma scriverla vale per il giorno in cui non
 * lo sara' — la fase 6.
 */
static void manda_puntatore(Input *input, uint16_t x, uint16_t y)
{
	double fx = x, fy = y;

	if (!input->puntatore || !input->puntatore_attivo)
		return;

	if (input->regione_nota && input->larghezza && input->altezza)
	{
		fx = input->regione_x + (double) x * input->regione_l / (double) input->larghezza;
		fy = input->regione_y + (double) y * input->regione_a / (double) input->altezza;
	}
	else if (!input->regione_lamentata)
	{
		input->regione_lamentata = TRUE;
		avviso("nessuna regione del puntatore: le coordinate passano cosi' come sono, e se il "
		       "compositore le riscala il puntatore finira' altrove");
	}

	ei_device_pointer_motion_absolute(input->puntatore, fx, fy);
	ei_device_frame(input->puntatore, ei_now(input->ei));
	traccia("puntatore x=%.1f y=%.1f", fx, fy);
}

static void manda_bottone(Input *input, uint32_t bottone, gboolean premuto)
{
	if (!input->puntatore || !input->puntatore_attivo)
		return;
	ei_device_button_button(input->puntatore, bottone, premuto);
	ei_device_frame(input->puntatore, ei_now(input->ei));
	traccia("bottone %u %s", bottone, premuto ? "giu'" : "su'");
}

static void manda_asse(Input *input, double dx, double dy)
{
	if (!input->puntatore || !input->puntatore_attivo)
		return;
	ei_device_scroll_delta(input->puntatore, dx, dy);
	ei_device_frame(input->puntatore, ei_now(input->ei));
	traccia("asse dx=%.0f dy=%.0f", dx, dy);
}

/*
 * La rotella come SCATTI, che e' quel che serve su KWin.
 *
 * ⛔ `ei_device_scroll_delta` SU KWIN NON PRODUCE UNO SCATTO.  KWin lo traduce
 *    con `deltaV120 = 0` (`eiscontext.cpp:246-258`), cioe' in un
 *    `wl_pointer.axis` liscio senza `axis_value120` ne' `axis_discrete`: chi
 *    conta gli scatti non ne vede nessuno, e Xwayland deve indovinare i bottoni
 *    4 e 5.  E' la stessa ragione tecnica per cui krfb scorre male su Wayland.
 *
 *    `ei_device_scroll_discrete(±120)` invece KWin lo converte in
 *    `delta = 15` **e** `deltaV120 = ±120` (`eiscontext.cpp:272-286`), cioe' la
 *    rotella vera.  E il valore si passa quasi com'e', perche' RDP conta gia' in
 *    unita' da 120 per scatto: e' **piu' semplice** di quel che facciamo su
 *    Mutter, non piu' complicato (`kde.md` §7.2).
 *
 * ⚠ E il verso resta tutto nostro: KWin non inverte niente e tratta i due assi
 *   con la stessa formula, senza casi particolari — verificato riga per riga
 *   l'8 agosto 2026 (misura M10).  L'inversione del verticale che si vede qui
 *   sotto e' la convenzione di RDP contro quella di `wl_pointer`, non una
 *   stortura del compositore.
 */
static void manda_scatti(Input *input, int32_t dx, int32_t dy)
{
	if (!input->puntatore || !input->puntatore_attivo)
		return;
	ei_device_scroll_discrete(input->puntatore, dx, dy);
	ei_device_frame(input->puntatore, ei_now(input->ei));
	traccia("scatti dx=%d dy=%d", dx, dy);
}

/* ------------------------------------------------------------------ *
 * Il trattamento degli eventi RDP
 * ------------------------------------------------------------------ */
static void tratta_tasto(Input *input, uint16_t flags, uint8_t scancode)
{
	gboolean premuto = !(flags & KBD_FLAGS_RELEASE);
	uint32_t evdev;

	switch (tastiera_pausa(input->tastiera, flags, scancode, premuto))
	{
		case PAUSA_INGOIA:
			return;
		case PAUSA_EMETTI:
			diagnostica("sequenza del tasto Pausa riconosciuta");
			batti(input, TASTIERA_EVDEV_PAUSA);
			return;
		case PAUSA_ESTRANEO:
			break;
	}

	if (!tastiera_evdev(flags, scancode, &evdev))
	{
		traccia("scancode 0x%02X (flag 0x%04X) non traducibile", scancode, flags);
		return;
	}
	if (!tastiera_registra(input->tastiera, evdev, premuto))
		return;
	manda_tasto(input, evdev, premuto);
}

static void tratta_unicode(Input *input, uint16_t flags, uint16_t carattere)
{
	gboolean premuto = !(flags & KBD_FLAGS_RELEASE);
	uint32_t evdev = 0;
	uint32_t modificatori[TASTIERA_MODIFICATORI_MAX];
	guint quanti = 0;

	if (premuto)
	{
		if (!tastiera_unicode_premi(input->tastiera, carattere, &evdev, modificatori, &quanti))
			return;
		for (guint i = 0; i < quanti; i++)
			manda_tasto(input, modificatori[i], TRUE);
		manda_tasto(input, evdev, TRUE);
	}
	else
	{
		if (!tastiera_unicode_rilascia(input->tastiera, carattere, &evdev, modificatori, &quanti))
			return;
		manda_tasto(input, evdev, FALSE);
		for (guint i = quanti; i > 0; i--)
			manda_tasto(input, modificatori[i - 1], FALSE);
	}
}

static void tratta_mouse(Input *input, uint16_t flags, uint16_t x, uint16_t y)
{
	/*
	 * ⛔ Le coordinate degli eventi di rotella sono riempite di zeri da molti
	 *    client: vanno SCARTATE quando i flag rotella sono accesi, altrimenti
	 *    il puntatore salta nell'angolo a ogni scatto.  [M, 2 agosto]
	 */
	if (flags & (PTR_FLAGS_WHEEL | PTR_FLAGS_HWHEEL))
	{
		uint16_t valore = flags & 0x01FF; /* WheelRotationMask */
		double passo;

		if (valore & PTR_FLAGS_WHEEL_NEGATIVE)
			valore = (uint16_t) ((~valore & 0x01FF) + 1);
		passo = -(double) valore / UNITA_PER_SCATTO;
		if (flags & PTR_FLAGS_WHEEL_NEGATIVE)
			passo = -passo;

		/* Il verticale conta in verso opposto fra RDP e Wayland; l'orizzontale
		 * concorda.  Verificato sul riferimento invece di tirare a indovinare. */
		if (input->scatti_discreti)
		{
			/* Il valore di RDP e' gia' in unita' da 120: si passa com'e', e il
			 * segno e' l'unica cosa che si tocca. */
			int32_t v120 = (int32_t) lround(passo * UNITA_PER_SCATTO);

			if (flags & PTR_FLAGS_WHEEL)
				manda_scatti(input, 0, v120);
			else
				manda_scatti(input, -v120, 0);
		}
		else if (flags & PTR_FLAGS_WHEEL)
			manda_asse(input, 0.0, passo * PASSO_ASSE);
		else
			manda_asse(input, -passo * PASSO_ASSE, 0.0);
		return;
	}

	if (flags & PTR_FLAGS_MOVE)
		manda_puntatore(input, x, y);

	if (flags & PTR_FLAGS_BUTTON1)
		manda_bottone(input, BTN_LEFT, (flags & PTR_FLAGS_DOWN) != 0);
	if (flags & PTR_FLAGS_BUTTON2)
		manda_bottone(input, BTN_RIGHT, (flags & PTR_FLAGS_DOWN) != 0);
	if (flags & PTR_FLAGS_BUTTON3)
		manda_bottone(input, BTN_MIDDLE, (flags & PTR_FLAGS_DOWN) != 0);
}

static void tratta_mouse_esteso(Input *input, uint16_t flags, uint16_t x, uint16_t y)
{
	if (!(flags & (PTR_XFLAGS_BUTTON1 | PTR_XFLAGS_BUTTON2)))
	{
		manda_puntatore(input, x, y);
		return;
	}
	if (flags & PTR_XFLAGS_BUTTON1)
		manda_bottone(input, BTN_SIDE, (flags & PTR_XFLAGS_DOWN) != 0);
	if (flags & PTR_XFLAGS_BUTTON2)
		manda_bottone(input, BTN_EXTRA, (flags & PTR_XFLAGS_DOWN) != 0);
}

static void rilascia_tutto(Input *input)
{
	g_autoptr(GArray) codici = tastiera_svuota(input->tastiera);

	if (codici->len == 0)
		return;
	informazione("rilascio quel che era rimasto premuto: %u tasti", codici->len);
	for (guint i = 0; i < codici->len; i++)
		manda_tasto(input, g_array_index(codici, uint32_t, i), FALSE);
}

/*
 * L'evento di sincronizzazione porta lo stato dei tasti a scatto.  Si rilascia
 * tutto e si chiede un ping: la riconciliazione va fatta quando l'input in volo
 * e' stato digerito, altrimenti si confronterebbe lo stato con eventi ancora in
 * coda.
 */
static void tratta_sincronizza(Input *input, uint32_t flags)
{
	rilascia_tutto(input);

	input->atteso_maiusc = (flags & KBD_SYNC_CAPS_LOCK) != 0;
	input->atteso_num = (flags & KBD_SYNC_NUM_LOCK) != 0;
	input->attesi_noti = TRUE;
	diagnostica("sincronizzazione: BlocMaiusc %s, BlocNum %s",
	            input->atteso_maiusc ? "acceso" : "spento",
	            input->atteso_num ? "acceso" : "spento");

	if (!input->ping)
	{
		input->ping = ei_new_ping(input->ei);
		if (input->ping)
			ei_ping(input->ping);
	}
}

/*
 * Confronta lo stato dichiarato dal client con quello vero, e commuta quel che
 * non corrisponde.
 *
 * ⛔ NON ESISTE UN MODO DI IMPORRE UN LUCCHETTO: si preme il tasto.  Da cui la
 *    condizione: si fa **solo** quando si conosce lo stato vero, o si finirebbe
 *    a commutare contro un'ipotesi — cioe' a spegnere il BlocMaiusc di chi lo
 *    aveva acceso apposta.
 */
static void confronta_lucchetti(Input *input, gboolean maiusc, gboolean num)
{
	if (!input->attesi_noti)
		return;

	if (maiusc != input->atteso_maiusc)
	{
		informazione("BlocMaiusc non corrisponde: lo commuto");
		batti(input, TASTIERA_EVDEV_BLOCMAIUSC);
	}
	if (num != input->atteso_num)
	{
		informazione("BlocNum non corrisponde: lo commuto");
		batti(input, TASTIERA_EVDEV_BLOCNUM);
	}
	input->attesi_noti = FALSE;
}

/* La strada di Mutter: lo stato viaggia dentro l'evento di libei. */
static void riconcilia_lucchetti(Input *input, uint32_t bloccati)
{
	gboolean maiusc = FALSE, num = FALSE;

	if (!input->attesi_noti)
		return;
	if (!tastiera_lucchetti(input->tastiera, bloccati, &maiusc, &num))
		return;
	confronta_lucchetti(input, maiusc, num);
}

/*
 * La strada di KWin: lo stato arriva da un protocollo a parte, su un altro
 * thread.
 *
 * ⚠ Qui si SEGNA e si sveglia, non si manda niente: chi chiama e' la pompa
 *   Wayland, e libei vive su un thread solo.  Il confronto lo fa il thread di
 *   input al giro dopo, che e' anche il momento giusto — dopo che la coda degli
 *   eventi in volo e' stata digerita.
 */
void input_lucchetti_veri(Input *input, gboolean maiusc, gboolean num)
{
	if (!input)
		return;
	g_mutex_lock(&input->lucchetto);
	input->lucchetti_da_fuori = TRUE;
	input->fuori_maiusc = maiusc;
	input->fuori_num = num;
	g_mutex_unlock(&input->lucchetto);
	if (write(input->sveglia[1], "!", 1) < 0 && errno != EAGAIN)
		traccia("sveglia per i lucchetti non scritta: %s", g_strerror(errno));
}

/* ------------------------------------------------------------------ *
 * Svuotamento della coda, con accorpamento degli spostamenti
 * ------------------------------------------------------------------ */
static gboolean e_solo_spostamento(const Evento *evento)
{
	return evento->tipo == EV_MOUSE && (evento->a & PTR_FLAGS_MOVE) &&
	       !(evento->a & (PTR_FLAGS_BUTTON1 | PTR_FLAGS_BUTTON2 | PTR_FLAGS_BUTTON3 |
	                      PTR_FLAGS_WHEEL | PTR_FLAGS_HWHEEL));
}

static void svuota_coda(Input *input)
{
	for (guint giro = 0; giro < ACCORPAMENTO_MASSIMO; giro++)
	{
		Evento *evento;
		gboolean salta = FALSE;

		g_mutex_lock(&input->lucchetto);
		evento = g_queue_pop_head(input->coda);
		if (evento && e_solo_spostamento(evento))
		{
			const Evento *prossimo = g_queue_peek_head(input->coda);

			/* Di una raffica conta dove il puntatore ARRIVA.  Ma si scarta solo
			 * se il successivo e' ancora uno spostamento: se in mezzo c'e' un
			 * clic, la posizione conta eccome. */
			salta = prossimo && e_solo_spostamento(prossimo);
		}
		g_mutex_unlock(&input->lucchetto);

		if (!evento)
			return;
		if (salta)
		{
			g_free(evento);
			continue;
		}

		switch (evento->tipo)
		{
			case EV_TASTO:
				tratta_tasto(input, (uint16_t) evento->a, (uint8_t) evento->b);
				break;
			case EV_UNICODE:
				tratta_unicode(input, (uint16_t) evento->a, (uint16_t) evento->b);
				break;
			case EV_MOUSE:
				tratta_mouse(input, (uint16_t) evento->a, (uint16_t) evento->b,
				             (uint16_t) evento->c);
				break;
			case EV_MOUSE_ESTESO:
				tratta_mouse_esteso(input, (uint16_t) evento->a, (uint16_t) evento->b,
				                    (uint16_t) evento->c);
				break;
			case EV_SINCRONIZZA:
				tratta_sincronizza(input, evento->a);
				break;
			case EV_RILASCIA_TUTTO:
				rilascia_tutto(input);
				break;
			case EV_MISURA:
				input->larghezza = evento->a;
				input->altezza = evento->b;
				break;
		}
		g_free(evento);
	}
}

/* ------------------------------------------------------------------ *
 * Dispositivi, regioni e disposizione
 * ------------------------------------------------------------------ */
/*
 * Quale regione e' il nostro schermo.
 *
 * Due criteri, e il secondo non e' un ripiego: e' l'unico che esista su KWin.
 *
 *   per CHIAVE     Mutter marca ogni regione con il `mapping-id` dichiarato a
 *                  `RecordVirtual`: e' un'identita', e non si sbaglia.
 *
 *   per GEOMETRIA  ⛔ KWin NON marca le regioni affatto:
 *                  `eis_region_set_mapping_id` non e' chiamato in tutto KWin
 *                  6.3.6 (`kde.md` §7.2, cercato: assente).  Si riconosce
 *                  quindi quella grande come il desktop che stiamo servendo —
 *                  che con un solo schermo e' esatta, e con piu' schermi e'
 *                  comunque molto meglio di «la prima».
 *
 * ⚠ «La prima» resta come ultima spiaggia, e quando scatta lo si DICE: prendere
 *   la prima funziona finche' lo schermo e' uno solo, e smette di funzionare
 *   esattamente quando servirebbe.
 */
static void leggi_regione(Input *input, struct ei_device *dispositivo)
{
	struct ei_region *scelta = NULL;
	struct ei_region *per_geometria = NULL;
	struct ei_region *prima = NULL;

	for (size_t i = 0;; i++)
	{
		struct ei_region *regione = ei_device_get_region(dispositivo, i);
		const char *id;

		if (!regione)
			break;
		if (!prima)
			prima = regione;
		id = ei_region_get_mapping_id(regione);
		if (input->mapping_id && id && g_strcmp0(id, input->mapping_id) == 0)
		{
			scelta = regione;
			break;
		}
		if (!per_geometria && input->larghezza && input->altezza &&
		    (uint32_t) ei_region_get_width(regione) == input->larghezza &&
		    (uint32_t) ei_region_get_height(regione) == input->altezza)
			per_geometria = regione;
	}

	if (!scelta)
		scelta = per_geometria;
	if (!scelta && prima)
	{
		scelta = prima;
		if (!input->regione_lamentata)
		{
			input->regione_lamentata = TRUE;
			avviso("nessuna regione riconosciuta ne' per chiave ne' per geometria (%ux%u): "
			       "prendo la prima, e con piu' di uno schermo sara' quella sbagliata",
			       input->larghezza, input->altezza);
		}
	}

	if (!scelta)
		return;

	input->regione_x = ei_region_get_x(scelta);
	input->regione_y = ei_region_get_y(scelta);
	input->regione_l = ei_region_get_width(scelta);
	input->regione_a = ei_region_get_height(scelta);
	input->regione_nota = input->regione_l > 0 && input->regione_a > 0;
	diagnostica("regione del puntatore: %.0f,%.0f %.0fx%.0f (mapping-id «%s»)", input->regione_x,
	            input->regione_y, input->regione_l, input->regione_a,
	            ei_region_get_mapping_id(scelta) ?: "assente");
}

static void leggi_disposizione(Input *input, struct ei_device *dispositivo)
{
	struct ei_keymap *keymap = ei_device_keyboard_get_keymap(dispositivo);
	int fd;
	size_t misura;
	void *mappata;

	if (!keymap)
	{
		avviso("la sessione non consegna alcuna disposizione di tastiera: "
		       "il percorso Unicode restera' spento");
		return;
	}
	if (ei_keymap_get_type(keymap) != EI_KEYMAP_TYPE_XKB)
	{
		avviso("disposizione di tipo sconosciuto: ignorata");
		return;
	}

	fd = ei_keymap_get_fd(keymap);
	misura = ei_keymap_get_size(keymap);
	if (fd < 0 || misura == 0)
		return;

	mappata = mmap(NULL, misura, PROT_READ, MAP_PRIVATE, fd, 0);
	if (mappata == MAP_FAILED)
	{
		avviso("disposizione non mappabile: %s", g_strerror(errno));
		return;
	}
	tastiera_keymap(input->tastiera, mappata, misura);
	munmap(mappata, misura);
}

static void dispositivo_aggiunto(Input *input, struct ei_device *dispositivo)
{
	gboolean puntatore = ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE);
	gboolean tasti = ei_device_has_capability(dispositivo, EI_DEVICE_CAP_KEYBOARD);

	diagnostica("dispositivo «%s»: puntatore %s, tastiera %s",
	            ei_device_get_name(dispositivo) ?: "?", puntatore ? "si" : "no",
	            tasti ? "si" : "no");

	if (puntatore && !input->puntatore)
	{
		input->puntatore = ei_device_ref(dispositivo);
		leggi_regione(input, dispositivo);
	}
	if (tasti && !input->tastiera_dev)
	{
		input->tastiera_dev = ei_device_ref(dispositivo);
		leggi_disposizione(input, dispositivo);
	}
}

static void dispositivo_tolto(Input *input, struct ei_device *dispositivo)
{
	if (input->puntatore == dispositivo)
	{
		ei_device_unref(input->puntatore);
		input->puntatore = NULL;
		input->puntatore_attivo = FALSE;
		input->regione_nota = FALSE;
	}
	if (input->tastiera_dev == dispositivo)
	{
		ei_device_unref(input->tastiera_dev);
		input->tastiera_dev = NULL;
		input->tastiera_attiva = FALSE;
	}
}

static void tratta_evento_ei(Input *input, struct ei_event *evento)
{
	enum ei_event_type tipo = ei_event_get_type(evento);
	struct ei_device *dispositivo = ei_event_get_device(evento);

	switch (tipo)
	{
		case EI_EVENT_SEAT_ADDED:
			/* Si chiedono le capacita' che servono; i dispositivi arrivano
			 * dopo, e li crea il compositore.  E' la differenza con i metodi
			 * `Notify*`, dove i dispositivi li si imponeva. */
			ei_seat_bind_capabilities(ei_event_get_seat(evento), EI_DEVICE_CAP_POINTER,
			                          EI_DEVICE_CAP_POINTER_ABSOLUTE, EI_DEVICE_CAP_KEYBOARD,
			                          EI_DEVICE_CAP_BUTTON, EI_DEVICE_CAP_SCROLL, NULL);
			diagnostica("posto «%s»: capacita' richieste",
			            ei_seat_get_name(ei_event_get_seat(evento)) ?: "?");
			break;

		case EI_EVENT_DEVICE_ADDED:
			dispositivo_aggiunto(input, dispositivo);
			break;

		case EI_EVENT_DEVICE_REMOVED:
			dispositivo_tolto(input, dispositivo);
			break;

		case EI_EVENT_DEVICE_RESUMED:
			ei_device_start_emulating(dispositivo, ++input->sequenza);
			if (dispositivo == input->puntatore)
			{
				input->puntatore_attivo = TRUE;
				leggi_regione(input, dispositivo);
			}
			if (dispositivo == input->tastiera_dev)
				input->tastiera_attiva = TRUE;
			diagnostica("dispositivo «%s» pronto", ei_device_get_name(dispositivo) ?: "?");
			break;

		case EI_EVENT_DEVICE_PAUSED:
			if (dispositivo == input->puntatore)
				input->puntatore_attivo = FALSE;
			if (dispositivo == input->tastiera_dev)
				input->tastiera_attiva = FALSE;
			break;

		case EI_EVENT_KEYBOARD_MODIFIERS:
			tastiera_gruppo(input->tastiera, ei_event_keyboard_get_xkb_group(evento));
			riconcilia_lucchetti(input, ei_event_keyboard_get_xkb_mods_locked(evento));
			break;

		case EI_EVENT_PONG:
			g_clear_pointer(&input->ping, ei_ping_unref);
			break;

		case EI_EVENT_DISCONNECT:
			avviso("il compositore ha chiuso il canale di input");
			g_atomic_int_set(&input->fermare, 1);
			break;

		default:
			break;
	}
}

/* ------------------------------------------------------------------ *
 * Il thread
 * ------------------------------------------------------------------ */
static gpointer thread_input(gpointer dati)
{
	Input *input = dati;
	struct pollfd sonde[2];

	sonde[0].fd = ei_get_fd(input->ei);
	sonde[0].events = POLLIN;
	sonde[1].fd = input->sveglia[0];
	sonde[1].events = POLLIN;

	while (!g_atomic_int_get(&input->fermare))
	{
		struct ei_event *evento;
		char scarto[256];

		sonde[0].revents = sonde[1].revents = 0;
		if (poll(sonde, 2, 200) < 0 && errno != EINTR)
		{
			errore("poll del thread di input: %s", g_strerror(errno));
			break;
		}

		if (sonde[1].revents & POLLIN)
			while (read(input->sveglia[0], scarto, sizeof scarto) > 0)
				;

		ei_dispatch(input->ei);
		while ((evento = ei_get_event(input->ei)) != NULL)
		{
			tratta_evento_ei(input, evento);
			ei_event_unref(evento);
		}

		svuota_coda(input);

		/* Lo stato vero, se e' arrivato da fuori mentre svuotavamo.  Dopo la coda
		 * e non prima: confrontarlo con eventi ancora da mandare significherebbe
		 * misurare uno stato che sta per cambiare. */
		{
			gboolean c_e, maiusc, num;

			g_mutex_lock(&input->lucchetto);
			c_e = input->lucchetti_da_fuori;
			maiusc = input->fuori_maiusc;
			num = input->fuori_num;
			input->lucchetti_da_fuori = FALSE;
			g_mutex_unlock(&input->lucchetto);
			if (c_e)
				confronta_lucchetti(input, maiusc, num);
		}
	}

	diagnostica("thread di input chiuso");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * Ciclo di vita
 * ------------------------------------------------------------------ */
static void spia_libei(struct ei *ei, enum ei_log_priority priorita, const char *messaggio,
                       struct ei_log_context *contesto)
{
	if (priorita >= EI_LOG_PRIORITY_ERROR)
		errore("libei: %s", messaggio);
	else if (priorita >= EI_LOG_PRIORITY_WARNING)
		avviso("libei: %s", messaggio);
	else
		traccia("libei: %s", messaggio);
}

Input *input_avvia(int fd_eis, const char *mapping_id, gboolean scatti_discreti, GError **sbaglio)
{
	Input *input = g_new0(Input, 1);

	input->sveglia[0] = input->sveglia[1] = -1;
	input->mapping_id = g_strdup(mapping_id);
	input->scatti_discreti = scatti_discreti;
	input->tastiera = tastiera_nuova();
	input->coda = g_queue_new();
	g_mutex_init(&input->lucchetto);

	input->ei = ei_new_sender(input);
	if (!input->ei)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "contesto libei non creato");
		goto guasto;
	}
	ei_log_set_handler(input->ei, spia_libei);
	ei_configure_name(input->ei, "remotix");

	if (ei_setup_backend_fd(input->ei, fd_eis) != 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "il descrittore di ConnectToEIS non e' stato accettato da libei");
		goto guasto;
	}

	if (!g_unix_open_pipe(input->sveglia, O_CLOEXEC, sbaglio))
		goto guasto;
	g_unix_set_fd_nonblocking(input->sveglia[0], TRUE, NULL);
	g_unix_set_fd_nonblocking(input->sveglia[1], TRUE, NULL);

	input->thread = g_thread_new("remotix-input", thread_input, input);
	informazione("canale di input aperto verso il compositore (libei)");
	return input;

guasto:
	input_ferma(input);
	return NULL;
}

void input_ferma(Input *input)
{
	if (!input)
		return;

	g_atomic_int_set(&input->fermare, 1);
	if (input->thread)
	{
		/* Se la scrittura non riesce non importa: il poll ha comunque un
		 * timeout, quindi il thread si accorge della fermata entro un istante. */
		if (input->sveglia[1] >= 0)
			(void) !write(input->sveglia[1], "!", 1);
		g_thread_join(input->thread);
		input->thread = NULL;
	}

	if (input->puntatore)
		ei_device_unref(input->puntatore);
	if (input->tastiera_dev)
		ei_device_unref(input->tastiera_dev);
	if (input->ping)
		ei_ping_unref(input->ping);
	if (input->ei)
	{
		ei_disconnect(input->ei);
		ei_unref(input->ei);
	}
	if (input->sveglia[0] >= 0)
		close(input->sveglia[0]);
	if (input->sveglia[1] >= 0)
		close(input->sveglia[1]);

	if (input->coda)
	{
		g_queue_free_full(input->coda, g_free);
		input->coda = NULL;
	}
	g_mutex_clear(&input->lucchetto);
	g_clear_pointer(&input->tastiera, tastiera_libera);
	g_free(input->mapping_id);
	g_free(input);
}
