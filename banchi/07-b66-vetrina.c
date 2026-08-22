/*
 * 07-b66-vetrina.c — mette PIXEL ESATTI sul monitor della sessione remota.
 *
 *   07-b66-vetrina --uscita NOME --immagine scena.xrgb --misura 1280x720
 *                  [--secondi 120] [--pulsa 64] [--loquace]
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA SERVE A MISURARE, e perche' non basta un visualizzatore.
 *
 * La domanda della fase e' una sola: **quel che c'e' sullo schermo della
 * sessione e quel che noi catturiamo sono gli stessi pixel?**  Per rispondere
 * bisogna sapere, byte per byte, che cosa c'e' sullo schermo — e nessun
 * visualizzatore d'immagini lo garantisce:
 *
 *   · `eog`/`loupe` applicano la gestione del colore (ICC dell'immagine verso
 *     ICC dello schermo) ⇒ i pixel disegnati NON sono quelli del file;
 *   · GTK 4.16+ ha una pipeline di colore sua;
 *   · `mpv` converte comunque, e' un lettore video.
 *
 * ⇒ Con uno di quelli, uno scarto misurato a valle avrebbe **due** spiegazioni
 *   — il visualizzatore o il compositore — e il banco non saprebbe dire quale.
 *
 * ⭐ Questo client scrive i byte del file **dentro un `wl_shm` XRGB8888** e
 *    basta: nessuna conversione, nessuna scala, nessun profilo.  Quel che sta
 *    nel file e' quel che sta sulla superficie.  ⇒ L'atteso della misura non e'
 *    una formula ne' una seconda opinione: e' **il file stesso**.
 *
 * ⛔ E NON RIDIMENSIONA MAI.  Se il compositore configura una misura diversa da
 *    quella dell'immagine, il client **muore**: un'immagine riscalata sarebbe un
 *    metro sfocato che pero' continua a dichiarare la mira, ed e' il difetto che
 *    `03-scena.c` §--uscita descrive per il monitor sbagliato.
 *
 * ⛔ IL GUASTO NON STA QUI.  Il guasto innestato lo fabbrica chi genera
 *    l'immagine (`07-b66-dentro.py --guasto`): cosi' questo file resta una
 *    tubatura senza logica, e non c'e' nessun ramo «di prova» che possa
 *    accendersi per sbaglio in un giro sano.
 *
 * ⚠ IL BATTITO (`--pulsa N`) — e serve, non e' un vezzo.  `[M]` 21 agosto 2026
 *   (`07-b63-scena.sh`): su un desktop fermo Mutter consegna una manciata di
 *   fotogrammi e poi **piu' niente**.  Un quadrato di N×N pixel nell'angolo in
 *   basso a destra cambia grigio a ogni disegno e tiene la catena viva.
 *   ⛔ E' DICHIARATO e sta FUORI da ogni riquadro misurato: chi confronta lo
 *      esclude per nome, non per fortuna.
 *
 * Modello: `banchi/03-scena.c` (registro, xdg-shell, pool `memfd`, uscita per
 * nome).  ⛔ Quel file non si tocca — `CODER.md` §4.1: si dipende, non si
 * riscrive; ma la sua scena e' generata, non caricata, e qui serve il contrario.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#include <wayland-client.h>

#include "xdg-shell-client-protocol.h"

#define USCITE_MAX 8
#define BUFFER_N 2

struct uscita {
	struct wl_output *wl;
	char nome[64];
	char descrizione[128];
	int larghezza, altezza;
};

struct buffer {
	struct wl_buffer *wl;
	uint32_t *pixel;
	bool occupato;
};

static struct {
	struct wl_display *display;
	struct wl_registry *registry;
	struct wl_compositor *compositor;
	struct wl_shm *shm;
	struct xdg_wm_base *wm_base;
	struct wl_surface *superficie;
	struct xdg_surface *xdg_superficie;
	struct xdg_toplevel *toplevel;

	struct uscita uscite[USCITE_MAX];
	int quante_uscite;
	struct uscita *scelta;
	char confermata[64];

	struct wl_shm_pool *pool;
	int pool_fd;
	void *pool_mem;
	size_t pool_byte;
	struct buffer buffer[BUFFER_N];

	uint32_t *immagine;          /* i byte del file, XRGB8888 */
	int larghezza, altezza;
	int conf_l, conf_a;
	bool configurato, chiudi;
	bool chiesto_disegno, elenca;
	int pulsa;                   /* lato del quadrato del battito, 0 = niente */
	int secondi;
	bool loquace;
	const char *uscita_chiesta, *percorso;
	unsigned long long disegni;
} S;

static volatile sig_atomic_t interrotto = 0;
static void su_segnale(int s) { (void)s; interrotto = 1; }

static void muori(const char *f, ...)
{
	va_list ap;
	va_start(ap, f);
	fputs("⛔ vetrina: ", stderr);
	vfprintf(stderr, f, ap);
	va_end(ap);
	fputc('\n', stderr);
	exit(2);
}

static uint64_t ora_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000000ull + (uint64_t)t.tv_nsec / 1000ull;
}

/* ------------------------------------------------------------------ */
static void su_rilascio(void *d, struct wl_buffer *b)
{
	(void)b;
	((struct buffer *)d)->occupato = false;
}
static const struct wl_buffer_listener ascolta_buffer = { su_rilascio };

static void crea_pool(void)
{
	size_t uno = (size_t)S.larghezza * (size_t)S.altezza * 4;
	size_t tutto = uno * BUFFER_N;
	int fd = memfd_create("remotix-b66-vetrina", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, (off_t)tutto) < 0)
		muori("memfd_create/ftruncate: %s", strerror(errno));
	S.pool_fd = fd;
	S.pool_mem = mmap(NULL, tutto, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (S.pool_mem == MAP_FAILED) muori("mmap: %s", strerror(errno));
	S.pool_byte = tutto;
	S.pool = wl_shm_create_pool(S.shm, fd, (int32_t)tutto);
	for (int i = 0; i < BUFFER_N; i++) {
		S.buffer[i].wl = wl_shm_pool_create_buffer(
		    S.pool, (int32_t)(uno * (size_t)i), S.larghezza, S.altezza,
		    S.larghezza * 4, WL_SHM_FORMAT_XRGB8888);
		S.buffer[i].pixel = (uint32_t *)((uint8_t *)S.pool_mem + uno * (size_t)i);
		S.buffer[i].occupato = false;
		wl_buffer_add_listener(S.buffer[i].wl, &ascolta_buffer, &S.buffer[i]);
	}
}

static void su_frame(void *d, struct wl_callback *cb, uint32_t t)
{
	(void)d; (void)t;
	wl_callback_destroy(cb);
	/* ⛔ Il callback ALZA UNA BANDIERA e non disegna: e' la cura di
	 *    `03-scena.c` §su_frame — un disegno dentro il gestore apre una
	 *    ricorsione e moltiplica i commit. */
	S.chiesto_disegno = true;
}
static const struct wl_callback_listener ascolta_frame = { su_frame };

static void disegna(void)
{
	struct buffer *b = NULL;
	for (int i = 0; i < BUFFER_N; i++)
		if (!S.buffer[i].occupato) { b = &S.buffer[i]; break; }
	if (!b) { S.chiesto_disegno = true; return; }   /* si rinvia, non si aspetta */

	size_t uno = (size_t)S.larghezza * (size_t)S.altezza * 4;
	memcpy(b->pixel, S.immagine, uno);

	/* ⚠ IL BATTITO — dichiarato, e sempre nello stesso posto: l'angolo in
	 *   basso a destra.  Chi misura lo esclude sapendo dov'e'. */
	if (S.pulsa > 0) {
		uint32_t c = (S.disegni & 1) ? 0x00202020u : 0x00d0d0d0u;
		for (int y = S.altezza - S.pulsa; y < S.altezza; y++)
			for (int x = S.larghezza - S.pulsa; x < S.larghezza; x++)
				b->pixel[(size_t)y * S.larghezza + x] = c;
	}

	struct wl_callback *cb = wl_surface_frame(S.superficie);
	wl_callback_add_listener(cb, &ascolta_frame, NULL);
	wl_surface_attach(S.superficie, b->wl, 0, 0);
	/* ⛔ Danno PIENO e non solo il battito: un danno parziale farebbe dipendere
	 *    quel che il compositore ricompone da un'ottimizzazione sua, e la
	 *    misura del colore avrebbe una variabile in piu' che nessuno controlla. */
	wl_surface_damage_buffer(S.superficie, 0, 0, S.larghezza, S.altezza);
	wl_surface_commit(S.superficie);
	b->occupato = true;
	S.disegni++;
}

/* ------------------------------------------------------------------ */
static void su_xdg_configure(void *d, struct xdg_surface *s, uint32_t serial)
{
	(void)d;
	xdg_surface_ack_configure(s, serial);
	if (S.configurato) {
		/* ⛔ Una riconfigurazione di misura diversa NON si insegue: si muore.
		 *    Ridisegnare piu' piccolo vorrebbe dire misurare un'immagine che
		 *    non e' quella dichiarata. */
		if (S.conf_l > 0 && S.conf_a > 0 &&
		    (S.conf_l != S.larghezza || S.conf_a != S.altezza))
			muori("il compositore ha riconfigurato a %dx%d, ma l'immagine e' "
			      "%dx%d: NON riscalo", S.conf_l, S.conf_a, S.larghezza, S.altezza);
		return;
	}
	S.configurato = true;
	if (S.conf_l > 0 && S.conf_a > 0 &&
	    (S.conf_l != S.larghezza || S.conf_a != S.altezza))
		muori("a schermo intero il compositore da' %dx%d, l'immagine e' %dx%d.\n"
		      "   ⇒ Rigenera la scena a %dx%d: un'immagine riscalata e' un metro "
		      "sfocato che pero' dichiara la mira",
		      S.conf_l, S.conf_a, S.larghezza, S.altezza, S.conf_l, S.conf_a);
	crea_pool();
	/* ⛔ Opaca e dichiarata: senza la regione opaca il compositore deve fondere
	 *    quel che sta sotto, e allora i pixel catturati non sono piu' i nostri
	 *    ma una miscela — cioe' proprio la domanda che il banco vuole isolare. */
	struct wl_region *r = wl_compositor_create_region(S.compositor);
	wl_region_add(r, 0, 0, S.larghezza, S.altezza);
	wl_surface_set_opaque_region(S.superficie, r);
	wl_region_destroy(r);
	disegna();
}
static const struct xdg_surface_listener ascolta_xdg = { su_xdg_configure };

static void su_tl_configure(void *d, struct xdg_toplevel *t, int32_t w, int32_t h,
                            struct wl_array *a)
{
	(void)d; (void)t; (void)a;
	if (w > 0 && h > 0) { S.conf_l = w; S.conf_a = h; }
}
static void su_tl_chiudi(void *d, struct xdg_toplevel *t) { (void)d; (void)t; S.chiudi = true; }
static void su_tl_limiti(void *d, struct xdg_toplevel *t, int32_t w, int32_t h)
{ (void)d; (void)t; (void)w; (void)h; }
static void su_tl_capacita(void *d, struct xdg_toplevel *t, struct wl_array *a)
{ (void)d; (void)t; (void)a; }
static const struct xdg_toplevel_listener ascolta_tl = {
	su_tl_configure, su_tl_chiudi, su_tl_limiti, su_tl_capacita
};

static void su_ping(void *d, struct xdg_wm_base *b, uint32_t serial)
{ (void)d; xdg_wm_base_pong(b, serial); }
static const struct xdg_wm_base_listener ascolta_wm = { su_ping };

static void usc_geo(void *d, struct wl_output *o, int32_t x, int32_t y, int32_t lf,
                    int32_t af, int32_t sub, const char *marca, const char *modello,
                    int32_t tr)
{
	(void)o; (void)x; (void)y; (void)lf; (void)af; (void)sub; (void)tr;
	struct uscita *u = d;
	if (!u->nome[0])
		snprintf(u->nome, sizeof u->nome, "%s %s", marca ? marca : "?",
		         modello ? modello : "?");
}
static void usc_modo(void *d, struct wl_output *o, uint32_t f, int32_t w, int32_t h,
                     int32_t r)
{
	(void)o; (void)r;
	if (f & WL_OUTPUT_MODE_CURRENT) {
		((struct uscita *)d)->larghezza = w;
		((struct uscita *)d)->altezza = h;
	}
}
static void usc_fatto(void *d, struct wl_output *o) { (void)d; (void)o; }
static void usc_scala(void *d, struct wl_output *o, int32_t s) { (void)d; (void)o; (void)s; }
static void usc_nome(void *d, struct wl_output *o, const char *n)
{ (void)o; snprintf(((struct uscita *)d)->nome, 64, "%s", n); }
static void usc_desc(void *d, struct wl_output *o, const char *t)
{ (void)o; snprintf(((struct uscita *)d)->descrizione, 128, "%s", t); }
static const struct wl_output_listener ascolta_uscita = {
	usc_geo, usc_modo, usc_fatto, usc_scala, usc_nome, usc_desc
};

/* ⭐ E' IL COMPOSITORE a dire dove la superficie e' finita (`LEZIONI.md` §1.7):
 *    la richiesta dice che cosa si e' chiesto, questo dice che cosa e'
 *    successo.  Una scena sul monitor sbagliato darebbe «catturato tutto nero»
 *    e il banco accuserebbe la cattura. */
static void sup_entrata(void *d, struct wl_surface *s, struct wl_output *o)
{
	(void)d; (void)s;
	for (int i = 0; i < S.quante_uscite; i++)
		if (S.uscite[i].wl == o) {
			snprintf(S.confermata, sizeof S.confermata, "%s", S.uscite[i].nome);
			return;
		}
	snprintf(S.confermata, sizeof S.confermata, "(ignota)");
}
static void sup_uscita(void *d, struct wl_surface *s, struct wl_output *o)
{ (void)d; (void)s; (void)o; }
static void sup_scala(void *d, struct wl_surface *s, int32_t f) { (void)d; (void)s; (void)f; }
static void sup_trasf(void *d, struct wl_surface *s, uint32_t t) { (void)d; (void)s; (void)t; }
static const struct wl_surface_listener ascolta_superficie = {
	sup_entrata, sup_uscita, sup_scala, sup_trasf
};

static void su_globale(void *d, struct wl_registry *r, uint32_t nome,
                       const char *iface, uint32_t ver)
{
	(void)d;
	if (!strcmp(iface, wl_compositor_interface.name))
		S.compositor = wl_registry_bind(r, nome, &wl_compositor_interface,
		                                ver < 4 ? ver : 4);
	else if (!strcmp(iface, wl_shm_interface.name))
		S.shm = wl_registry_bind(r, nome, &wl_shm_interface, 1);
	else if (!strcmp(iface, xdg_wm_base_interface.name)) {
		S.wm_base = wl_registry_bind(r, nome, &xdg_wm_base_interface, 1);
		xdg_wm_base_add_listener(S.wm_base, &ascolta_wm, NULL);
	} else if (!strcmp(iface, wl_output_interface.name)) {
		if (S.quante_uscite >= USCITE_MAX) return;
		struct uscita *u = &S.uscite[S.quante_uscite++];
		u->wl = wl_registry_bind(r, nome, &wl_output_interface, ver < 4 ? ver : 4);
		wl_output_add_listener(u->wl, &ascolta_uscita, u);
	}
}
static void su_via(void *d, struct wl_registry *r, uint32_t n) { (void)d; (void)r; (void)n; }
static const struct wl_registry_listener ascolta_registro = { su_globale, su_via };

/* ------------------------------------------------------------------ */
static void uso(void)
{
	fputs("uso: 07-b66-vetrina --uscita NOME --immagine F.xrgb --misura LxA\n"
	      "                    [--secondi N] [--pulsa LATO] [--uscite] [--loquace]\n",
	      stderr);
	exit(2);
}

int main(int argc, char **argv)
{
	S.pulsa = 64;
	S.secondi = 180;
	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		#define SEGUE() (i + 1 < argc ? argv[++i] : (uso(), (char *)NULL))
		if (!strcmp(a, "--uscita")) S.uscita_chiesta = SEGUE();
		else if (!strcmp(a, "--immagine")) S.percorso = SEGUE();
		else if (!strcmp(a, "--misura")) {
			const char *m = SEGUE();
			if (sscanf(m, "%dx%d", &S.larghezza, &S.altezza) != 2) uso();
		}
		else if (!strcmp(a, "--secondi")) S.secondi = atoi(SEGUE());
		else if (!strcmp(a, "--pulsa")) S.pulsa = atoi(SEGUE());
		else if (!strcmp(a, "--uscite")) S.elenca = true;
		else if (!strcmp(a, "--loquace")) S.loquace = true;
		else uso();
	}

	signal(SIGINT, su_segnale);
	signal(SIGTERM, su_segnale);

	S.display = wl_display_connect(NULL);
	if (!S.display) muori("nessun compositore (WAYLAND_DISPLAY=%s)",
	                      getenv("WAYLAND_DISPLAY") ? getenv("WAYLAND_DISPLAY") : "(vuoto)");
	S.registry = wl_display_get_registry(S.display);
	wl_registry_add_listener(S.registry, &ascolta_registro, NULL);
	wl_display_roundtrip(S.display);
	wl_display_roundtrip(S.display);   /* i nomi delle uscite arrivano dopo */

	fprintf(stderr, "uscite viste dal compositore: %d\n", S.quante_uscite);
	for (int i = 0; i < S.quante_uscite; i++)
		fprintf(stderr, "    «%s»  %dx%d  %s\n", S.uscite[i].nome,
		        S.uscite[i].larghezza, S.uscite[i].altezza, S.uscite[i].descrizione);
	if (S.elenca) return 0;

	if (!S.compositor || !S.shm || !S.wm_base)
		muori("il compositore non offre wl_compositor/wl_shm/xdg_wm_base");
	if (!S.uscita_chiesta) muori("--uscita e' obbligatoria: NON scelgo io il monitor");
	if (!S.percorso) muori("--immagine e' obbligatoria");
	for (int i = 0; i < S.quante_uscite; i++)
		if (!strcmp(S.uscite[i].nome, S.uscita_chiesta)) { S.scelta = &S.uscite[i]; break; }
	/* ⛔ Nessun ripiego su «una qualunque»: su questa macchina i monitor
	 *    virtuali sono piu' d'uno, e due terzi delle volte sarebbe quello di un
	 *    altro banco. */
	if (!S.scelta) muori("--uscita «%s» non esiste fra le %d elencate qui sopra",
	                     S.uscita_chiesta, S.quante_uscite);
	if (S.larghezza <= 0 || S.altezza <= 0) {
		S.larghezza = S.scelta->larghezza;
		S.altezza = S.scelta->altezza;
	}

	/* l'immagine: dev'essere ESATTAMENTE W*H*4 byte */
	size_t uno = (size_t)S.larghezza * (size_t)S.altezza * 4;
	int fd = open(S.percorso, O_RDONLY);
	if (fd < 0) muori("non apro %s: %s", S.percorso, strerror(errno));
	struct stat st;
	if (fstat(fd, &st) < 0) muori("fstat: %s", strerror(errno));
	if ((size_t)st.st_size != uno)
		muori("%s e' %lld byte, ma %dx%d XRGB8888 ne vuole %zu: "
		      "l'immagine non e' quella di questo monitor",
		      S.percorso, (long long)st.st_size, S.larghezza, S.altezza, uno);
	S.immagine = malloc(uno);
	if (!S.immagine) muori("niente memoria");
	if (read(fd, S.immagine, uno) != (ssize_t)uno) muori("lettura corta di %s", S.percorso);
	close(fd);

	S.superficie = wl_compositor_create_surface(S.compositor);
	wl_surface_add_listener(S.superficie, &ascolta_superficie, NULL);
	S.xdg_superficie = xdg_wm_base_get_xdg_surface(S.wm_base, S.superficie);
	xdg_surface_add_listener(S.xdg_superficie, &ascolta_xdg, NULL);
	S.toplevel = xdg_surface_get_toplevel(S.xdg_superficie);
	xdg_toplevel_add_listener(S.toplevel, &ascolta_tl, NULL);
	xdg_toplevel_set_title(S.toplevel, "remotix-07-b66-vetrina");
	xdg_toplevel_set_app_id(S.toplevel, "it.remotix.b66.vetrina");
	xdg_toplevel_set_fullscreen(S.toplevel, S.scelta->wl);
	wl_surface_commit(S.superficie);
	wl_display_roundtrip(S.display);

	uint64_t scadenza = ora_us() + (uint64_t)S.secondi * 1000000ull;
	while (!S.chiudi && !interrotto) {
		if (wl_display_dispatch(S.display) < 0) break;
		if (S.chiesto_disegno) { S.chiesto_disegno = false; disegna(); }
		if (ora_us() >= scadenza) break;
	}
	fprintf(stderr, "vetrina: %llu disegni · %dx%d · uscita chiesta «%s» "
	        "confermata «%s» · battito %d\n",
	        S.disegni, S.larghezza, S.altezza, S.uscita_chiesta,
	        S.confermata[0] ? S.confermata : "(nessuna!)", S.pulsa);
	/* ⛔ Se il compositore non ha MAI confermato l'uscita, i pixel potrebbero
	 *    essere finiti altrove: si dichiara con un codice d'uscita diverso, e
	 *    chi guida il banco non chiama «misura» un giro alla cieca. */
	if (!S.confermata[0]) return 3;
	if (strcmp(S.confermata, S.uscita_chiesta) != 0) {
		fprintf(stderr, "⛔ la superficie e' finita su «%s», non su «%s»\n",
		        S.confermata, S.uscita_chiesta);
		return 4;
	}
	return 0;
}
