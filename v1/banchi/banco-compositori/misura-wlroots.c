/*
 * misura-wlroots — quanti fotogrammi al secondo consegna un compositore wlroots.
 *
 * La famiglia wlroots (sway, labwc, wayfire — cioe' XFCE e LXQt, §3.8 di
 * SPECIFICA.md) non ha ne' l'interfaccia D-Bus di Mutter ne' il protocollo di
 * KWin: la sua strada e' `zwlr_screencopy_manager_v1`, e chi la incarta in un
 * nodo PipeWire e' il portale.  Qui si parla al compositore direttamente, che e'
 * il principio 4 di §2 di SPECIFICA.md.
 *
 * ⚠ LA DIFFERENZA CHE VA DICHIARATA LEGGENDO I NUMERI.  Mutter e KWin
 *   *spingono*: aperto il flusso, i fotogrammi arrivano da soli.  wlr-screencopy
 *   invece si *tira*: per ogni fotogramma il consumatore fa una richiesta e
 *   aspetta.  Con `copy_with_damage` la risposta arriva quando qualcosa e'
 *   cambiato — la stessa semantica di Mutter — ma nel conto ci sta anche un
 *   giro di andata e ritorno sul socket per fotogramma.  Non e' un difetto del
 *   compositore: e' la forma del suo protocollo, ed e' quel che pagherebbe
 *   anche REMOTIX.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ ZERO E FALLIMENTO SONO DUE COSE DIVERSE — lacuna L1, curata il 12
 *     agosto 2026, e questo programma non lo sapeva dire da quando esiste.
 *
 * Fino a oggi `main()` finiva in un modo solo: stampava una RIGA e **ritornava
 * 0**.  Qualunque cosa fosse successa.  Il compositore che rifiuta la copia, la
 * pentola che non si alloca, il compositore che muore al terzo secondo: si
 * usciva dal ciclo, si stampavano `0x0`, `0.00` e uno stato d'uscita **buono**.
 * ⛔ E' la forma d'errore **E8** del catalogo (`REVIEWER.md` §2) — *«vuoto» e
 *    «proibito» hanno lo stesso aspetto* — dentro lo strumento che deve
 *    misurare la terza famiglia di compositori.
 *
 * ⚠ E la cura NON era nuova: il gemello `misura-cattura.c` ce l'ha dal 9
 *   agosto 2026 e la porta in quattro guardie, tutte con la stessa faccia —
 *   `printf("GUASTO\t…")` al posto della RIGA, la ragione sullo stderr,
 *   **uscita 2**.  «Una riga di misura che non e' una misura e' peggio di
 *   nessuna riga.»  Qui quella forma non era mai arrivata.
 *
 * ⛔ E il verdetto glielo costruiva attorno `banchi/00-c1-wlroots.sh`, che
 *    rileggeva la RIGA e decideva lui — cioe' la protezione di un difetto noto
 *    fuori dal programma, in un pezzo di script che si puo' perdere copiando
 *    il binario altrove: l'invariante **I7** al contrario (`CODER.md` §2).
 *    Adesso il rifiuto sta qui dentro, e chi lancia questo programma da una
 *    riga di comando qualunque lo riceve lo stesso.
 *
 * ⚠ QUEL CHE RESTA UNO «ZERO» LEGITTIMO, e va detto o si cura troppo: con
 *   `copy_with_damage` una scena FERMA non consegna niente, e zero fotogrammi
 *   su un compositore sano e' la risposta giusta.  Lo discrimina il fatto che
 *   il compositore abbia risposto almeno una volta con un formato
 *   (`formato_noto`): la scena ferma ci arriva, il compositore rotto no.  E'
 *   lo stesso discrimine che nel gemello si chiama `t_inizio`.
 */

#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>
#include <wayland-client.h>

#include "wlr-screencopy-unstable-v1-client-protocol.h"

#define INTERVALLI_MAX 100000

static struct wl_shm *shm;
static struct zwlr_screencopy_manager_v1 *gestore;
static struct wl_output *uscita;
static struct wl_buffer *pentola;
static void *pixel;
static uint32_t larghezza, altezza, passo, formato;
static int finito, in_corso;

static uint64_t arrivati, contati, danno_pieno, danno_parziale, danno_assente;
static int64_t t_scarto, t_primo, t_ultimo, t_fine;
static int conta;
static int32_t *intervalli;
static unsigned n_intervalli;
static int visto_danno_pieno, visto_danno;

/* ⛔ Le due variabili della lacuna L1, e sono due apposta:
 *
 *   formato_noto  il compositore ha risposto almeno una volta con un formato.
 *                 E' il discrimine fra «la scena e' ferma» (zero legittimo) e
 *                 «non ho mai parlato con nessuno» (fallimento).
 *   guasto        la RAGIONE per cui la misura non vale, o NULL.  Una ragione,
 *                 non un booleano: «e' andata male» non dice a chi legge dove
 *                 andare a guardare, e questo programma gira dentro una
 *                 certificazione che deve poter distinguere il rosso del
 *                 compositore dal rosso dello strumento. */
static int formato_noto;
static const char *guasto;

static int64_t adesso_us(void)
{
	struct timespec t;

	clock_gettime(CLOCK_MONOTONIC, &t);
	return (int64_t) t.tv_sec * 1000000 + t.tv_nsec / 1000;
}

static void su_globale(void *d, struct wl_registry *r, uint32_t nome, const char *iface,
                       uint32_t versione)
{
	if (!strcmp(iface, wl_shm_interface.name))
		shm = wl_registry_bind(r, nome, &wl_shm_interface, 1);
	else if (!strcmp(iface, zwlr_screencopy_manager_v1_interface.name))
		gestore = wl_registry_bind(r, nome, &zwlr_screencopy_manager_v1_interface,
		                           versione < 3 ? versione : 3);
	else if (!strcmp(iface, wl_output_interface.name) && !uscita)
		uscita = wl_registry_bind(r, nome, &wl_output_interface, 1);
}

static void su_globale_via(void *d, struct wl_registry *r, uint32_t nome)
{
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

/* Una pentola sola, riusata: allocarne una per fotogramma misurerebbe
 * l'allocatore invece del compositore. */
static int prepara_pentola(void)
{
	int fd;
	size_t misura = (size_t) passo * altezza;
	struct wl_shm_pool *piscina;

	if (pentola)
		return 0;
	fd = memfd_create("misura-wlroots", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, misura) < 0)
		return -1;
	pixel = mmap(NULL, misura, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (pixel == MAP_FAILED)
		return -1;
	piscina = wl_shm_create_pool(shm, fd, misura);
	pentola = wl_shm_pool_create_buffer(piscina, 0, larghezza, altezza, passo, formato);
	wl_shm_pool_destroy(piscina);
	close(fd);
	return 0;
}

static void chiedi_fotogramma(struct wl_display *display);

static void su_buffer(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t fmt, uint32_t w,
                      uint32_t h, uint32_t stride)
{
	formato = fmt;
	larghezza = w;
	altezza = h;
	passo = stride;
	/* ⛔ Il compositore HA risposto: da qui in poi uno zero e' uno zero. */
	formato_noto = 1;
}

static void su_linux_dmabuf(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t fmt, uint32_t w,
                            uint32_t h)
{
	/* Si dichiara di saperlo ricevere, ma qui si misura la strada in memoria:
	 * il DMA-BUF di wlroots vorrebbe un'allocazione GBM nostra, che e' un
	 * pezzo di fase 11 e non di questa misura. */
}

static void su_buffer_done(void *d, struct zwlr_screencopy_frame_v1 *f)
{
	if (prepara_pentola() < 0)
	{
		guasto = "la pentola non si e' potuta allocare";
		finito = 1;
		return;
	}
	visto_danno = 0;
	visto_danno_pieno = 0;
	zwlr_screencopy_frame_v1_copy_with_damage(f, pentola);
}

static void su_flags(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t flags)
{
}

static void su_danno(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                     uint32_t w, uint32_t h)
{
	visto_danno = 1;
	if (x == 0 && y == 0 && w >= larghezza && h >= altezza)
		visto_danno_pieno = 1;
}

static void su_pronto(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t sec_hi, uint32_t sec_lo,
                      uint32_t nsec)
{
	int64_t ora = adesso_us();

	arrivati++;
	if (!visto_danno)
		danno_assente++;
	else if (visto_danno_pieno)
		danno_pieno++;
	else
		danno_parziale++;

	if (!conta && ora >= t_scarto)
	{
		conta = 1;
		t_primo = ora;
	}
	if (conta)
	{
		if (contati > 0 && n_intervalli < INTERVALLI_MAX)
			intervalli[n_intervalli++] = (int32_t) (ora - t_ultimo);
		contati++;
		t_ultimo = ora;
	}
	zwlr_screencopy_frame_v1_destroy(f);
	in_corso = 0;
}

static void su_fallito(void *d, struct zwlr_screencopy_frame_v1 *f)
{
	/* ⛔ `failed` di wlr-screencopy e' un RIFIUTO, non uno zero: prima di
	 *    oggi finiva in un `fprintf` sullo stderr e la RIGA usciva lo
	 *    stesso, con lo stato d'uscita buono. */
	guasto = "il compositore ha rifiutato la copia (evento `failed`)";
	zwlr_screencopy_frame_v1_destroy(f);
	in_corso = 0;
	finito = 1;
}

static const struct zwlr_screencopy_frame_v1_listener ascolto_fotogramma = {
	su_buffer, su_flags, su_pronto, su_fallito, su_danno, su_linux_dmabuf, su_buffer_done
};

static void chiedi_fotogramma(struct wl_display *display)
{
	/* L'attesa del cambiamento non sta qui ma nella copia: e'
	 * `copy_with_damage` a dire «rispondimi quando qualcosa e' cambiato». */
	struct zwlr_screencopy_frame_v1 *f =
	    zwlr_screencopy_manager_v1_capture_output(gestore, 0, uscita);

	zwlr_screencopy_frame_v1_add_listener(f, &ascolto_fotogramma, NULL);
	in_corso = 1;
}

static int confronta(const void *a, const void *b)
{
	int32_t x = *(const int32_t *) a, y = *(const int32_t *) b;

	return x < y ? -1 : x > y ? 1 : 0;
}

int main(int argc, char **argv)
{
	struct wl_display *display;
	struct wl_registry *registro;
	double durata = 15.0, scarto = 5.0, secondi, fps;
	const char *etichetta = "wlroots";
	int32_t minimo = 0, p50 = 0, p95 = 0, massimo = 0;
	int i;

	for (i = 1; i < argc; i++)
	{
		if (!strcmp(argv[i], "--durata") && i + 1 < argc)
			durata = atof(argv[++i]);
		else if (!strcmp(argv[i], "--scarto") && i + 1 < argc)
			scarto = atof(argv[++i]);
		else if (!strcmp(argv[i], "--etichetta") && i + 1 < argc)
			etichetta = argv[++i];
	}

	intervalli = calloc(INTERVALLI_MAX, sizeof *intervalli);
	display = wl_display_connect(NULL);
	if (!display)
	{
		fprintf(stderr, "nessun display Wayland\n");
		return 1;
	}
	registro = wl_display_get_registry(display);
	wl_registry_add_listener(registro, &ascolto_registro, NULL);
	wl_display_roundtrip(display);
	wl_display_roundtrip(display);

	if (!gestore || !shm || !uscita)
	{
		fprintf(stderr, "manca screencopy, shm o l'uscita\n");
		return 1;
	}

	t_scarto = adesso_us() + (int64_t) (scarto * 1000000);
	t_fine = t_scarto + (int64_t) (durata * 1000000);

	chiedi_fotogramma(display);
	while (!finito && adesso_us() < t_fine)
	{
		if (wl_display_dispatch(display) < 0)
		{
			/* ⛔ La connessione al compositore e' caduta A META' MISURA —
			 *    il caso che la revisione avversariale del 9 agosto 2026
			 *    costrui' sul gemello: si lancia una cella da 20 secondi e
			 *    al terzo si uccide il compositore.  Quel che si e' raccolto
			 *    prima non e' una misura: e' un PEZZO di misura sotto
			 *    l'etichetta di una intera. */
			guasto = "la connessione al compositore e' caduta durante la misura";
			break;
		}
		if (!in_corso)
			chiedi_fotogramma(display);
	}

	/*
	 * ⛔ LE DUE GUARDIE DELLA LACUNA L1 — e sono la stessa forma che
	 *    `misura-cattura.c` ha in corpo dal 9 agosto 2026.
	 *
	 * Al posto della RIGA si stampa un **GUASTO** con la ragione, e si esce
	 * con **2**.  Non si stampa nessuna riga di misura: *«una riga di misura
	 * che non e' una misura e' peggio di nessuna riga»* — se ne uscisse una,
	 * finirebbe in una cella di tabella come «il compositore non consegna
	 * niente», che e' un'accusa a un imputato che non c'entra.
	 *
	 * ⚠ E l'ordine e' voluto: prima la ragione NOTA (`guasto`), poi quella
	 *   muta.  Un compositore che rifiuta la copia e un compositore che non
	 *   c'era mai sono due rossi diversi, e chi legge deve poterli separare
	 *   senza rileggere il proprio codice.
	 */
	if (guasto)
	{
		printf("GUASTO\t%s\t%s\n", etichetta, guasto);
		fprintf(stderr,
		        "⛔ FALLITO (non «zero»): %s.\n"
		        "   fotogrammi raccolti prima di fermarsi: %" PRIu64 " (arrivati %" PRIu64 ").\n"
		        "   Non sono una misura: sono un pezzo di misura sotto l'etichetta\n"
		        "   di una intera, e per questo non esce nessuna RIGA (LEZIONI.md §1.9).\n",
		        guasto, contati, arrivati);
		return 2;
	}
	if (!formato_noto)
	{
		printf("GUASTO\t%s\tnessun formato mai negoziato\n", etichetta);
		fprintf(stderr,
		        "⛔ FALLITO (non «zero»): il compositore non ha mai risposto con un\n"
		        "   formato, quindi non si sa a che misura ne' a che colore sarebbero\n"
		        "   i fotogrammi che non sono arrivati.  Prima di oggi qui usciva\n"
		        "   «RIGA … 0x0 … 0.00 …» con stato 0 — e uno zero cosi' e' la scena\n"
		        "   ferma e il compositore morto insieme, sotto la stessa faccia.\n"
		        "   ⚠ Una scena FERMA su un compositore sano arriva invece fin qui\n"
		        "     con il formato noto, e il suo zero e' un dato: quello si stampa.\n");
		return 2;
	}

	secondi = contati > 1 ? (double) (t_ultimo - t_primo) / 1000000.0 : 0.0;
	fps = secondi > 0.1 ? (double) (contati - 1) / secondi : 0.0;
	if (n_intervalli > 0)
	{
		qsort(intervalli, n_intervalli, sizeof *intervalli, confronta);
		minimo = intervalli[0];
		p50 = intervalli[n_intervalli / 2];
		p95 = intervalli[(n_intervalli * 95) / 100];
		massimo = intervalli[n_intervalli - 1];
	}

	printf("RIGA\t%s\t%ux%u\tshm\t-\tmemoria\twl_shm\t%.2f\t%" PRIu64 "\t%.2f\t1\t%" PRIu64
	       "\t%" PRIu64 "\t%" PRIu64 "\t0\t0\t%.1f\t%.1f\t%.1f\t%.1f\n",
	       etichetta, larghezza, altezza, fps, contati, secondi, danno_pieno, danno_parziale,
	       danno_assente, minimo / 1000.0, p50 / 1000.0, p95 / 1000.0, massimo / 1000.0);
	fprintf(stderr,
	        "  %ux%u, passo %u\n"
	        "  fotogrammi %" PRIu64 " in %.2f s  →  %.2f al secondo\n"
	        "  danno: pieno %" PRIu64 ", parziale %" PRIu64 ", assente %" PRIu64 "\n"
	        "  intervalli ms: min %.1f  mediana %.1f  p95 %.1f  max %.1f\n",
	        larghezza, altezza, passo, contati, secondi, fps, danno_pieno, danno_parziale,
	        danno_assente, minimo / 1000.0, p50 / 1000.0, p95 / 1000.0, massimo / 1000.0);
	return 0;
}
