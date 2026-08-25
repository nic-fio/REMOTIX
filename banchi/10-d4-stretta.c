/*
 * 10-d4-stretta.c — ⭐⭐ IL BANCO DELLA STRETTA DI MANO DI `libei`, e chiama
 *                   **il prodotto vero**: `src/input.c`, non una sua imitazione.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA MISURA, in una riga
 *
 *   **Che cosa succede se si chiude il canale di input PRIMA che la stretta di
 *   mano di `libei` sia arrivata.**  `fasi/10-…md` §5.1 lo dichiarava non
 *   provato — *«non si riesce a temporizzare a mano»* — e questo banco toglie
 *   di mezzo il temporismo: **la stretta non arriva perche' il server EIS non
 *   risponde**, non perche' si e' stati abbastanza svelti.
 *
 * ⭐⭐ Ed e' la strada di `CODER.md` §3.6: *isola UNA funzione sola e chiamala da
 *     fuori*.  Qui la funzione e' `input_chiudi()`, e le fa da mondo attorno:
 *
 *   · un **server EIS vero** (`libeis`) al posto di Mutter, sul suo socket:
 *     `eis_backend_fd_add_client()` da' esattamente il descrittore che
 *     `ConnectToEIS` darebbe;
 *   · una `MutterSessione` **finta** di tre righe, che quel descrittore lo
 *     consegna e basta;
 *   · `registro_dice()`/`registro_dettaglio()` finti, che scrivono su `stderr`
 *     — cosi' le righe del prodotto si possono leggere dal lanciatore.
 *
 * ⛔ Niente GPU, niente compositore, niente rete: gira ovunque ci sia `libei`.
 *   ⇒ **Nessun lucchetto**, e nessun numero di prestazioni che si possa falsare.
 *
 * ---------------------------------------------------------------------------
 * ⭐ LE SCENE
 *
 *   `immaturo`   il server EIS **non risponde**: accetta il socket e sta zitto.
 *                Il canale resta nello stato «stretta chiesta, non arrivata»
 *                per tutto il tempo che vogliamo, e li' dentro si chiude.
 *                ⇒ ⛔ Sull'albero **senza la cura** il processo muore di
 *                  **SIGSEGV** dentro `ei_disconnect()`.
 *
 *   `maturo`     il server EIS fa il suo mestiere: approva la connessione, crea
 *                il posto, lega le capacita', crea puntatore e tastiera e li
 *                riprende.  Poi il canale si chiude.
 *                ⇒ ⭐ **La chiusura VERA deve funzionare ancora**: il server
 *                  deve VEDERE il distacco (`EIS_EVENT_CLIENT_DISCONNECT`) e i
 *                  dispositivi virtuali devono sparire.
 *
 * ⛔ E il tempo della finestra si SCEGLIE, non si spera: `--attesa=<ms>` dice
 *    quanti millisecondi passano fra «aperto» e «chiuso».  Serve a far vedere
 *    che nella finestra ci si e' passati davvero (`LEZIONI.md` §1.30), non a
 *    beccarla.
 *
 * ---------------------------------------------------------------------------
 * ⭐ LA RIGA CHE SI LEGGE — una sola, in coda, su `stdout`
 *
 *   10-d4 scena=… attesa_ms=… vissuto_ms=… stretta=si|no abbandoni=N
 *         fd_prima=N fd_dopo=N disconnesso_visto=0|1 dispositivi_creati=N
 *         dispositivi_persi=N esito=vivo
 *
 * ⛔ Se il processo muore, la riga NON c'e': e' il lanciatore a leggere il
 *    **segnale**, che e' il testimone vero del rosso.
 *
 * Compilazione (la fa `10-d4-lancia.sh`):
 *   cc -O1 -g -std=gnu11 -D_GNU_SOURCE $(pkg-config --cflags glib-2.0 libei-1.0) \
 *      -o /tmp/10-d4 banchi/10-d4-stretta.c <ALBERO>/input.c src/tastiera.c \
 *      $(pkg-config --libs glib-2.0 libei-1.0) -lxkbcommon
 */
#define _GNU_SOURCE
#include <execinfo.h>
#include <signal.h>
#include <dirent.h>
#include <errno.h>
#include <gio/gio.h>
#include <libei.h>
#include <libeis.h>
#include <poll.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "../src/input.h"

/* ⭐ La finestra del banco che `input.h` non porta di proposito — vedi il
 *    commento accanto alla sua definizione in `input.c`: `input.h` e' il
 *    contratto del prodotto, questa e' un'occhiata da dentro per il banco. */
void input_conto(const Input *in, unsigned *tasti, unsigned *pulsanti,
                 unsigned *ricambi_puntatore, unsigned *ricambi_tastiera, int *pronto);

/*
 * ⭐ Il testimone che `input.c` tiene fuori dal contratto, come `input_conto()`:
 *    lo si dichiara da qui, che e' la convenzione di questo progetto.
 *
 * ⛔ Ed e' DEBOLE apposta: sull'albero **pristino** — quello senza la cura, cioe'
 *    quello su cui il banco deve dare il ROSSO — questa funzione non esiste, e
 *    un banco che non si compila sul binario malato non puo' misurare niente.
 *    ⇒ Se `input.c` la porta vince la sua; se non la porta, vale questa e dice
 *    zero, che sul pristino e' anche la verita': non abbandona mai niente.
 */
unsigned input_abbandoni(void);
__attribute__((weak)) unsigned input_abbandoni(void)
{
	return 0;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * I FINTI — registro e Mutter.  ⛔ Sono finti QUESTI, non il prodotto.
 * ═══════════════════════════════════════════════════════════════════════════ */

void registro_dice(const char *area, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
void registro_dettaglio(const char *area, const char *fmt, ...)
	__attribute__((format(printf, 2, 3)));
bool registro_parla_molto(void);

void registro_dice(const char *area, const char *fmt, ...)
{
	va_list ap;
	fprintf(stderr, "[%s] ", area);
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fputc('\n', stderr);
}

void registro_dettaglio(const char *area, const char *fmt, ...)
{
	va_list ap;
	fprintf(stderr, "[%s·d] ", area);
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fputc('\n', stderr);
}

bool registro_parla_molto(void)
{
	return true;
}

/* ⚠ La `MutterSessione` finta: `input.c` la tratta come opaca e le chiede una
 *   cosa sola — il descrittore del canale EIS. */
struct MutterSessione
{
	int fd;
};
typedef struct MutterSessione MutterSessione;

int mutter_eis_fd(const MutterSessione *sessione);
int mutter_eis_riattacca(MutterSessione *sessione, GError **sbaglio);
const char *mutter_mapping_id_pubblicato(MutterSessione *sessione);

int mutter_eis_fd(const MutterSessione *sessione)
{
	return sessione ? sessione->fd : -1;
}

/* ⛔ La guarigione non e' di questo banco: qui si dichiara che non si sa fare,
 *    invece di far finta di riuscirci — `CODER.md` §4.2. */
int mutter_eis_riattacca(MutterSessione *sessione, GError **sbaglio)
{
	(void) sessione;
	g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
	            "10-d4: la guarigione non e' nel campo di questo banco");
	return -1;
}

const char *mutter_mapping_id_pubblicato(MutterSessione *sessione)
{
	(void) sessione;
	/* ⚠ NULL vuol dire «non lo so», ed e' il caso vero quando la proprieta' non
	 *   c'e': `input.c` cade sulla regione per geometria e lo dichiara. */
	return NULL;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * IL SERVER EIS — al posto di Mutter
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct
{
	struct eis *eis;
	struct eis_client *cliente;
	struct eis_seat *posto;
	struct eis_device *puntatore;
	struct eis_device *tastiera;
	unsigned creati;
	unsigned persi;      /* `EIS_EVENT_DEVICE_CLOSED` */
	bool connesso_visto; /* il cliente si e' presentato */
	bool disconnesso_visto;
} Server;

static void server_crea_dispositivi(Server *s, struct eis_seat *posto)
{
	struct eis_device *d;
	struct eis_region *r;

	if (!s->puntatore)
	{
		d = eis_seat_new_device(posto);
		eis_device_configure_name(d, "10-d4 puntatore");
		eis_device_configure_capability(d, EIS_DEVICE_CAP_POINTER_ABSOLUTE);
		eis_device_configure_capability(d, EIS_DEVICE_CAP_BUTTON);
		eis_device_configure_capability(d, EIS_DEVICE_CAP_SCROLL);
		/* ⛔ La regione serve DAVVERO: senza, `input.c` non segna
		 *    `regione_nota` e il puntatore non e' mai «pronto». */
		r = eis_device_new_region(d);
		eis_region_set_size(r, 1920, 1080);
		eis_region_set_offset(r, 0, 0);
		eis_region_set_physical_scale(r, 1.0);
		eis_region_add(r);
		eis_region_unref(r);
		eis_device_add(d);
		eis_device_resume(d);
		s->puntatore = d;
		s->creati++;
	}
	if (!s->tastiera)
	{
		d = eis_seat_new_device(posto);
		eis_device_configure_name(d, "10-d4 tastiera");
		eis_device_configure_capability(d, EIS_DEVICE_CAP_KEYBOARD);
		eis_device_add(d);
		eis_device_resume(d);
		s->tastiera = d;
		s->creati++;
	}
}

static void server_gira(Server *s)
{
	struct eis_event *e;

	eis_dispatch(s->eis);
	while ((e = eis_get_event(s->eis)) != NULL)
	{
		switch (eis_event_get_type(e))
		{
			case EIS_EVENT_CLIENT_CONNECT:
				s->cliente = eis_event_get_client(e);
				eis_client_connect(s->cliente);
				s->connesso_visto = true;
				s->posto = eis_client_new_seat(s->cliente, "10-d4");
				eis_seat_configure_capability(s->posto, EIS_DEVICE_CAP_POINTER);
				eis_seat_configure_capability(s->posto, EIS_DEVICE_CAP_POINTER_ABSOLUTE);
				eis_seat_configure_capability(s->posto, EIS_DEVICE_CAP_BUTTON);
				eis_seat_configure_capability(s->posto, EIS_DEVICE_CAP_SCROLL);
				eis_seat_configure_capability(s->posto, EIS_DEVICE_CAP_KEYBOARD);
				eis_seat_add(s->posto);
				break;

			case EIS_EVENT_CLIENT_DISCONNECT:
				/* ⭐⭐ IL TESTIMONE DELLA CHIUSURA VERA: e' questo evento che
				 *     dice che il distacco di protocollo e' arrivato, cioe' che
				 *     `ei_disconnect()` e' stato chiamato davvero. */
				s->disconnesso_visto = true;
				break;

			case EIS_EVENT_SEAT_BIND:
				if (eis_event_seat_has_capability(e, EIS_DEVICE_CAP_POINTER_ABSOLUTE)
				    || eis_event_seat_has_capability(e, EIS_DEVICE_CAP_KEYBOARD))
					server_crea_dispositivi(s, eis_event_get_seat(e));
				break;

			case EIS_EVENT_DEVICE_CLOSED:
				s->persi++;
				eis_device_remove(eis_event_get_device(e));
				break;

			default:
				break;
		}
		eis_event_unref(e);
	}
}

/* ═══════════════════════════════════════════════════════════════════════════
 * GLI ATTREZZI
 * ═══════════════════════════════════════════════════════════════════════════ */

/* ⭐ Quanti descrittori ha aperto questo processo.  E' il metro del PREZZO
 *    della cura: abbandonare un contesto senza chiudere i suoi due descrittori
 *    li perderebbe uno per palco morto giovane.
 * ⛔ Torna -1 se non si e' potuto guardare: `None` non e' zero. */
static int quanti_descrittori(void)
{
	DIR *d = opendir("/proc/self/fd");
	struct dirent *v;
	int quanti = 0;

	if (!d)
		return -1;
	while ((v = readdir(d)) != NULL)
		if (v->d_name[0] != '.')
			quanti++;
	closedir(d);
	/* ⚠ Uno di troppo: il descrittore della `opendir` stessa.  Si toglie qui
	 *   invece di ricordarselo a ogni confronto. */
	return quanti > 0 ? quanti - 1 : quanti;
}

static gint64 adesso_ms(void)
{
	return g_get_monotonic_time() / 1000;
}

/*
 * ⭐⭐ LA PILA, SENZA GDB — e la ragione per cui c'e'.
 *
 * `fasi/10-…md` §5.1 ha il core letto con `gdb` sulla macchina di prova.  Questo
 * banco gira ovunque, anche dove `gdb` non c'e', e **il segnale da solo non
 * basta**: un SIGSEGV qualsiasi non e' *questo* SIGSEGV.  ⇒ Si stampa la pila,
 * che deve nominare `ei_disconnect`.
 *
 * ⛔ E poi si MUORE davvero: si rimette la disposizione predefinita e si rilancia
 *    il segnale, cosi' chi ci ha lanciati legge ancora **segnale 11**.  Un
 *    gestore che assorbisse la morte trasformerebbe il rosso in un verde.
 */
static void la_pila_e_poi_muori(int segnale)
{
	void *pile[24];
	int quante = backtrace(pile, 24);

	(void) write(2, "⛔ 10-d4 SIGSEGV — la pila:\n", 30);
	backtrace_symbols_fd(pile, quante, 2);
	signal(segnale, SIG_DFL);
	raise(segnale);
}

int main(int argc, char **argv)
{
	const char *scena = NULL;
	long attesa_ms = 60;
	long pazienza_ms = 3000;
	Server s;
	MutterSessione sessione;
	Input *in = NULL;
	char *errore = NULL;
	int fd_cliente;
	int fd_prima, fd_dopo;
	gint64 t0, vissuto_ms;
	bool stretta = false;
	bool maturo;
	bool caduta;
	int gira_esito = 0;

	memset(&s, 0, sizeof s);
	signal(SIGSEGV, la_pila_e_poi_muori);

	for (int i = 1; i < argc; i++)
	{
		if (strncmp(argv[i], "--attesa=", 9) == 0)
			attesa_ms = strtol(argv[i] + 9, NULL, 10);
		else if (strncmp(argv[i], "--pazienza=", 11) == 0)
			pazienza_ms = strtol(argv[i] + 11, NULL, 10);
		else if (argv[i][0] != '-')
			scena = argv[i];
	}
	if (!scena
	    || (strcmp(scena, "immaturo") != 0 && strcmp(scena, "maturo") != 0
	        && strcmp(scena, "caduta-immatura") != 0))
	{
		fprintf(stderr, "uso: %s immaturo|maturo|caduta-immatura [--attesa=<ms>] "
		                "[--pazienza=<ms>]\n",
		        argv[0]);
		return 2;
	}
	maturo = strcmp(scena, "maturo") == 0;
	caduta = strcmp(scena, "caduta-immatura") == 0;

	/* ⛔ Il server EIS si apre SEMPRE, anche nella scena immatura: quel che
	 *    cambia e' che li' non lo si fa mai girare.  ⚠ Un socket senza nessuno
	 *    dall'altra parte non e' la stessa cosa: `libei` vedrebbe il distacco. */
	s.eis = eis_new(NULL);
	if (!s.eis || eis_setup_backend_fd(s.eis) != 0)
	{
		fprintf(stderr, "⛔ 10-d4: il server EIS finto non si e' aperto\n");
		return 3;
	}
	fd_cliente = eis_backend_fd_add_client(s.eis);
	if (fd_cliente < 0)
	{
		fprintf(stderr, "⛔ 10-d4: nessun descrittore per il cliente (%s)\n",
		        strerror(-fd_cliente));
		return 3;
	}
	sessione.fd = fd_cliente;

	fd_prima = quanti_descrittori();

	/* ══ IL PRODOTTO, chiamato per nome ══ */
	in = input_apri(&sessione, 1920, 1080, &errore);
	if (!in)
	{
		fprintf(stderr, "⛔ 10-d4: input_apri e' fallita: %s\n", errore ? errore : "senza motivo");
		return 3;
	}
	t0 = adesso_ms();

	if (maturo)
	{
		/* ⛔ Si aspetta la MATURITA' VERA — il puntatore pronto — e non un
		 *   tempo: un'attesa a tempo direbbe «maturo» anche quando non lo e'. */
		gint64 fine = t0 + pazienza_ms;
		int pronto = 0;
		while (adesso_ms() < fine && !pronto)
		{
			struct pollfd p[2];
			unsigned tasti, puls, rp, rt;

			server_gira(&s);
			p[0].fd = eis_get_fd(s.eis);
			p[0].events = POLLIN;
			p[1].fd = input_descrittore(in);
			p[1].events = POLLIN;
			p[0].revents = p[1].revents = 0;
			(void) poll(p, 2, 20);
			if (input_gira(in) < 0)
				break;
			input_conto(in, &tasti, &puls, &rp, &rt, &pronto);
		}
		if (!pronto)
		{
			fprintf(stderr, "⛔ 10-d4: il canale non e' MAI maturato entro %ld ms: la scena "
			                "«maturo» non ha morso, e non giudico\n",
			        pazienza_ms);
			return 4;
		}
		stretta = true;
	}
	else if (caduta)
	{
		/*
		 * ⛔⛔⛔ IL COMPOSITORE MUORE MENTRE IL PALCO E' APPENA NATO — la scena
		 *      che `fasi/10-…md` §5.1 nomina *«il palco se n'e' andato»*.
		 *
		 * ⚠ Qui NON si prova la cura di `input_chiudi()`: si prova quel che
		 *   succede **prima**, cioe' dentro `ei_dispatch()`.  `libei` chiama
		 *   `ei_disconnect()` da se' quando la lettura dal socket fallisce, e se
		 *   in quel momento la stretta non e' arrivata cade **nello stesso
		 *   posto** — e da fuori non c'e' niente da fare.
		 *
		 * ⇒ Questa scena esiste per MISURARE quel buco, non per curarlo: e' la
		 *   differenza fra un `[?]` e un `[M]`.
		 */
		gint64 fine;
		eis_unref(s.eis); /* ⛔ il «compositore» muore: il socket si chiude */
		s.eis = NULL;
		fine = t0 + attesa_ms;
		while (adesso_ms() < fine)
		{
			struct pollfd p;
			p.fd = input_descrittore(in);
			p.events = POLLIN;
			p.revents = 0;
			(void) poll(&p, 1, 5);
			gira_esito = input_gira(in);
			if (gira_esito < 0)
				break;
		}
	}
	else
	{
		/* ⛔⛔ LA FINESTRA PERICOLOSA, TENUTA APERTA APPOSTA.
		 *
		 * ⚠ Il server EIS **non gira**: la stretta non puo' arrivare.  E
		 *   `input_gira()` si chiama lo stesso, perche' e' quel che il figlio
		 *   vero fa a ogni giro del suo ciclo — se la stretta arrivasse, la
		 *   vedremmo, e la scena si dichiarerebbe non mordente. */
		gint64 fine = t0 + attesa_ms;
		while (adesso_ms() < fine)
		{
			struct pollfd p;
			p.fd = input_descrittore(in);
			p.events = POLLIN;
			p.revents = 0;
			(void) poll(&p, 1, 5);
			if (input_gira(in) < 0)
				break;
		}
		/* ⚠ Un puntatore pronto qui vorrebbe dire che il server finto ha
		 *   risposto per sbaglio: la scena non morderebbe piu'. */
		{
			unsigned tasti, puls, rp, rt;
			int pronto = 0;
			input_conto(in, &tasti, &puls, &rp, &rt, &pronto);
			if (pronto)
			{
				fprintf(stderr, "⛔ 10-d4: nella scena «immaturo» il canale e' MATURATO: la "
				                "finestra non e' stata attraversata, e non giudico\n");
				return 4;
			}
		}
	}

	vissuto_ms = adesso_ms() - t0;

	/* ══ ⛔⛔ LO SMONTAGGIO, NELL'ORDINE ESATTO DI `smonta_il_palco()` ══
	 *
	 * ⭐ Le due righe sono quelle di `figlio.c`, nello stesso ordine: prima il
	 *    rilascio di quel che era rimasto giu' (`RCP.md` §11), poi la chiusura.
	 *    ⛔ Copiare la sola `input_chiudi()` proverebbe una sequenza che nel
	 *      prodotto non esiste — e i **quattro** chiamanti di `smonta_il_palco()`
	 *      passano tutti di qui. */
	(void) input_rilascia_tutto(in);
	input_chiudi(in);
	in = NULL;

	/* ⭐ Dopo la chiusura si lascia respirare il server: e' li' che arriva il
	 *    distacco di protocollo, e senza questo giro «non l'ho visto» vorrebbe
	 *    dire «non ho guardato». */
	if (maturo)
	{
		gint64 fine = adesso_ms() + 500;
		while (adesso_ms() < fine && !s.disconnesso_visto)
		{
			struct pollfd p;
			p.fd = eis_get_fd(s.eis);
			p.events = POLLIN;
			p.revents = 0;
			(void) poll(&p, 1, 20);
			server_gira(&s);
		}
	}

	fd_dopo = quanti_descrittori();

	printf("10-d4 scena=%s attesa_ms=%ld vissuto_ms=%lld stretta=%s abbandoni=%u "
	       "fd_prima=%d fd_dopo=%d connesso_visto=%d disconnesso_visto=%d "
	       "dispositivi_creati=%u dispositivi_persi=%u gira=%d esito=vivo\n",
	       scena, attesa_ms, (long long) vissuto_ms, stretta ? "si" : "no", input_abbandoni(),
	       fd_prima, fd_dopo, s.connesso_visto ? 1 : 0, s.disconnesso_visto ? 1 : 0, s.creati,
	       s.persi, gira_esito);
	fflush(stdout);

	if (s.eis)
		eis_unref(s.eis);
	return 0;
}
