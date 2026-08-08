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
		fprintf(stderr, "pentola non allocata\n");
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
	fprintf(stderr, "il compositore ha rifiutato la copia\n");
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
			break;
		if (!in_corso)
			chiedi_fotogramma(display);
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
