/*
 * 03-b14-scena.c — LA SCENA DICHIARATA del banco B14, e il suo contatore.
 *
 *   03-b14-scena --uscita Meta-2 [--posizione 3840,0] [--attesa 20]
 *
 * ===========================================================================
 * ⛔ PERCHE' ESISTE, VISTO CHE `LEZIONI.md` §1.1 PRESCRIVE `weston-simple-egl`
 *
 * §1.1 dice: «un client a schermo intero, opaco, che ridisegna a ogni frame
 * callback del compositore (`weston-simple-egl -f -o` fa esattamente questo)».
 * ⛔ Su NIC-OS e su CHUWI **weston non e' installato** — nessun pacchetto,
 *    nessun binario, e la macchina non si tocca per un banco.
 *
 * ⇒ Questo file e' la STESSA FORMA, scritta a mano:
 *      · schermo intero            `xdg_toplevel.set_fullscreen(output)`
 *      · opaco                     `wl_surface.set_opaque_region` su tutta la tela
 *      · ridisegna a ogni callback `wl_surface.frame` + `eglSwapInterval(0)`
 *      · e cambia a ogni fotogramma (il colore ruota: niente scena ferma)
 *
 * ⭐ E fa una cosa che `weston-simple-egl` NON fa, ed e' il motivo per cui vale
 *    la pena averlo scritto: **sceglie il monitor**.  Sul banco B14 sullo stage
 *    ci sono TRE monitor virtuali (quello della sessione, quello del server
 *    7561 dell'utente, e il nostro), e una scena finita sul monitor sbagliato
 *    e' un metro puntato sul buio che pero' dichiara la mira — il difetto che
 *    F2.2 ha pagato il 12 agosto 2026.
 *
 * ===========================================================================
 * ⛔ IL CONTO DEI DISEGNI E' IL CONTROLLO DI §1.1, NON UN ORPELLO
 *
 * «Accanto va contato quanto disegna il client: e' il controllo che dice se il
 * tetto e' del compositore o della scena.»  Senza, un 37 non si sa se e' il
 * freno della cattura o una scena che disegna 37 volte.
 *
 * ⇒ Ogni frame callback stampa una riga `D <microsecondi monotoni>`, e chi
 *   orchestra confronta quelle righe con i fotogrammi che PipeWire consegna.
 *
 * ⚠ Un frame callback NON e' «ho disegnato»: e' «il compositore ha presentato
 *   il fotogramma precedente e mi invita al prossimo».  E' esattamente la
 *   grandezza che serve — la cadenza a cui il compositore compone quella vista.
 *
 * ===========================================================================
 * ⛔ E SI VERIFICA SU QUALE MONITOR SI E' FINITI, invece di dedurlo
 *
 * `wl_surface.enter` dice quale `wl_output` ha preso la superficie.  Lo si
 * stampa (`E <nome>`): e' il lato che riceve (`LEZIONI.md` §1.7), non la nostra
 * intenzione dichiarata.  Se non arriva nessun `enter`, si esce ROSSO — non si
 * misura una scena che non si sa dove sia.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <wayland-client.h>
#include <wayland-egl.h>
#include <EGL/egl.h>
#include <GLES2/gl2.h>

#include "xdg-shell-client-protocol.h"

#define MAX_USCITE 16

typedef struct
{
	struct wl_output *oggetto;
	uint32_t nome_globale;
	char nome[64];    /* wl_output.name, solo dalla versione 4 */
	int32_t x, y;     /* wl_output.geometry, sempre disponibile */
	int32_t larghezza, altezza;
	int refresh_mhz;
} Uscita;

static struct wl_display *display;
static struct wl_registry *registro;
static struct wl_compositor *compositore;
static struct xdg_wm_base *guscio;
static struct wl_surface *superficie;
static struct xdg_surface *xdg_superficie;
static struct xdg_toplevel *xdg_finestra;

static Uscita uscite[MAX_USCITE];
static int quante_uscite;

static EGLDisplay egl_display = EGL_NO_DISPLAY;
static EGLContext egl_contesto = EGL_NO_CONTEXT;
static EGLSurface egl_superficie = EGL_NO_SURFACE;
static EGLConfig egl_config;
static struct wl_egl_window *finestra_egl;

static int larghezza_chiesta = 1920, altezza_chiesta = 1080;
static int larghezza, altezza;
static int configurata;
static int gira = 1;
static uint64_t disegni;
static int entrata_vista;

static char uscita_voluta[64];
static int posizione_voluta_x = -1, posizione_voluta_y = -1;
static int posizione_data;

static uint64_t ora_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000ull + (uint64_t) (t.tv_nsec / 1000);
}

static void fermati(int s)
{
	(void) s;
	gira = 0;
}

/* ------------------------------------------------------------------ *
 *  wl_output — si raccolgono nome e posizione di TUTTE le uscite
 * ------------------------------------------------------------------ */
static void uscita_geometria(void *dati, struct wl_output *o, int32_t x, int32_t y, int32_t pw,
                             int32_t ph, int32_t sub, const char *marca, const char *modello,
                             int32_t trasformazione)
{
	Uscita *u = dati;
	(void) o; (void) pw; (void) ph; (void) sub; (void) marca; (void) modello; (void) trasformazione;
	u->x = x;
	u->y = y;
}

static void uscita_modo(void *dati, struct wl_output *o, uint32_t bandiere, int32_t l, int32_t a,
                        int32_t refresh)
{
	Uscita *u = dati;
	(void) o;
	if (bandiere & WL_OUTPUT_MODE_CURRENT)
	{
		u->larghezza = l;
		u->altezza = a;
		u->refresh_mhz = refresh;
	}
}

static void uscita_fine(void *dati, struct wl_output *o) { (void) dati; (void) o; }
static void uscita_scala(void *dati, struct wl_output *o, int32_t s) { (void) dati; (void) o; (void) s; }

static void uscita_nome(void *dati, struct wl_output *o, const char *nome)
{
	Uscita *u = dati;
	(void) o;
	snprintf(u->nome, sizeof u->nome, "%s", nome);
}

static void uscita_descrizione(void *dati, struct wl_output *o, const char *d)
{
	(void) dati; (void) o; (void) d;
}

static const struct wl_output_listener ascolto_uscita = {
	uscita_geometria, uscita_modo, uscita_fine, uscita_scala, uscita_nome, uscita_descrizione,
};

/* ------------------------------------------------------------------ *
 *  wl_surface.enter — ⛔ il lato che riceve: DOVE siamo finiti davvero
 * ------------------------------------------------------------------ */
static void superficie_entra(void *dati, struct wl_surface *s, struct wl_output *o)
{
	int i;
	(void) dati; (void) s;
	for (i = 0; i < quante_uscite; i++)
	{
		if (uscite[i].oggetto == o)
		{
			printf("E %llu %s %d,%d %dx%d@%d\n", (unsigned long long) ora_us(),
			       uscite[i].nome[0] ? uscite[i].nome : "(senza-nome)", uscite[i].x, uscite[i].y,
			       uscite[i].larghezza, uscite[i].altezza, uscite[i].refresh_mhz);
			fflush(stdout);
			entrata_vista = 1;
			return;
		}
	}
	printf("E %llu (uscita-sconosciuta)\n", (unsigned long long) ora_us());
	fflush(stdout);
	entrata_vista = 1;
}

static void superficie_esce(void *dati, struct wl_surface *s, struct wl_output *o)
{
	(void) dati; (void) s; (void) o;
	printf("L %llu\n", (unsigned long long) ora_us());
	fflush(stdout);
}

static const struct wl_surface_listener ascolto_superficie = {
	superficie_entra, superficie_esce, NULL, NULL,
};

/* ------------------------------------------------------------------ *
 *  xdg-shell
 * ------------------------------------------------------------------ */
static void guscio_ping(void *dati, struct xdg_wm_base *g, uint32_t seriale)
{
	(void) dati;
	xdg_wm_base_pong(g, seriale);
}
static const struct xdg_wm_base_listener ascolto_guscio = { guscio_ping };

static void xdg_configura(void *dati, struct xdg_surface *s, uint32_t seriale)
{
	(void) dati;
	xdg_surface_ack_configure(s, seriale);
	configurata = 1;
}
static const struct xdg_surface_listener ascolto_xdg = { xdg_configura };

static void finestra_configura(void *dati, struct xdg_toplevel *t, int32_t l, int32_t a,
                               struct wl_array *stati)
{
	(void) dati; (void) t; (void) stati;
	if (l > 0 && a > 0)
	{
		larghezza = l;
		altezza = a;
	}
}
static void finestra_chiudi(void *dati, struct xdg_toplevel *t)
{
	(void) dati; (void) t;
	gira = 0;
}
static void finestra_limiti(void *dati, struct xdg_toplevel *t, int32_t l, int32_t a)
{
	(void) dati; (void) t; (void) l; (void) a;
}
static void finestra_stati(void *dati, struct xdg_toplevel *t, struct wl_array *a)
{
	(void) dati; (void) t; (void) a;
}
static const struct xdg_toplevel_listener ascolto_finestra = {
	finestra_configura, finestra_chiudi, finestra_limiti, finestra_stati,
};

/* ------------------------------------------------------------------ *
 *  registry
 * ------------------------------------------------------------------ */
static void registro_aggiungi(void *dati, struct wl_registry *r, uint32_t nome,
                              const char *interfaccia, uint32_t versione)
{
	(void) dati;
	if (strcmp(interfaccia, "wl_compositor") == 0)
	{
		compositore = wl_registry_bind(r, nome, &wl_compositor_interface, versione < 4 ? versione : 4);
	}
	else if (strcmp(interfaccia, "xdg_wm_base") == 0)
	{
		guscio = wl_registry_bind(r, nome, &xdg_wm_base_interface, 1);
		xdg_wm_base_add_listener(guscio, &ascolto_guscio, NULL);
	}
	else if (strcmp(interfaccia, "wl_output") == 0 && quante_uscite < MAX_USCITE)
	{
		/* ⛔ Si chiede la 4 SOLO se il server ce l'ha: la 4 porta l'evento
		 *    `name` (cioe' «Meta-2»), che e' la sola strada per nominare il
		 *    monitor invece di indovinarlo per indice.  Se il server sta piu'
		 *    indietro, resta la posizione — e il chiamante la sa da
		 *    DisplayConfig. */
		uint32_t v = versione < 4 ? versione : 4;
		Uscita *u = &uscite[quante_uscite++];
		memset(u, 0, sizeof *u);
		u->nome_globale = nome;
		u->oggetto = wl_registry_bind(r, nome, &wl_output_interface, v);
		wl_output_add_listener(u->oggetto, &ascolto_uscita, u);
	}
}

static void registro_togli(void *dati, struct wl_registry *r, uint32_t nome)
{
	(void) dati; (void) r; (void) nome;
}
static const struct wl_registry_listener ascolto_registro = { registro_aggiungi, registro_togli };

/* ------------------------------------------------------------------ *
 *  Il ciclo di disegno — una callback, un disegno, una riga
 * ------------------------------------------------------------------ */
static void disegna(void);

static void su_callback(void *dati, struct wl_callback *c, uint32_t tempo)
{
	(void) dati; (void) tempo;
	wl_callback_destroy(c);
	disegna();
}
static const struct wl_callback_listener ascolto_callback = { su_callback };

static void disegna(void)
{
	struct wl_callback *c;
	float f;

	disegni++;
	printf("D %llu\n", (unsigned long long) ora_us());

	/* ⛔ La richiesta del PROSSIMO callback si fa PRIMA dello swap, o si perde
	 *    il giro: `eglSwapBuffers` fa il commit, e un `frame` chiesto dopo
	 *    finirebbe nel commit successivo. */
	c = wl_surface_frame(superficie);
	wl_callback_add_listener(c, &ascolto_callback, NULL);

	/* La scena SI MUOVE, e si muove a OGNI ridisegno: il colore ruota, quindi
	 * non esiste un fotogramma uguale al precedente e il compositore non ha
	 * mai la scusa di non comporre (`LEZIONI.md` §1.1). */
	f = (float) (disegni % 256) / 255.0f;
	glClearColor(f, 1.0f - f, (float) ((disegni / 256) % 256) / 255.0f, 1.0f);
	glClear(GL_COLOR_BUFFER_BIT);

	eglSwapBuffers(egl_display, egl_superficie);
}

/* ------------------------------------------------------------------ *
 *  main
 * ------------------------------------------------------------------ */
static int scegli_uscita(void)
{
	int i;

	if (uscita_voluta[0])
	{
		for (i = 0; i < quante_uscite; i++)
			if (strcmp(uscite[i].nome, uscita_voluta) == 0)
				return i;
	}
	if (posizione_data)
	{
		for (i = 0; i < quante_uscite; i++)
			if (uscite[i].x == posizione_voluta_x && uscite[i].y == posizione_voluta_y)
				return i;
	}
	return -1;
}

int main(int argc, char **argv)
{
	static const EGLint attributi_config[] = {
		EGL_SURFACE_TYPE, EGL_WINDOW_BIT,
		EGL_RENDERABLE_TYPE, EGL_OPENGL_ES2_BIT,
		EGL_RED_SIZE, 8, EGL_GREEN_SIZE, 8, EGL_BLUE_SIZE, 8, EGL_ALPHA_SIZE, 0,
		EGL_NONE,
	};
	static const EGLint attributi_contesto[] = { EGL_CONTEXT_CLIENT_VERSION, 2, EGL_NONE };
	EGLint quante_config;
	struct wl_region *opaca;
	int scelta, i;
	double secondi_attesa = 20.0;
	uint64_t scadenza;

	for (i = 1; i < argc; i++)
	{
		if (strcmp(argv[i], "--uscita") == 0 && i + 1 < argc)
			snprintf(uscita_voluta, sizeof uscita_voluta, "%s", argv[++i]);
		else if (strcmp(argv[i], "--posizione") == 0 && i + 1 < argc)
		{
			if (sscanf(argv[++i], "%d,%d", &posizione_voluta_x, &posizione_voluta_y) == 2)
				posizione_data = 1;
		}
		else if (strcmp(argv[i], "--misura") == 0 && i + 1 < argc)
			sscanf(argv[++i], "%dx%d", &larghezza_chiesta, &altezza_chiesta);
		else if (strcmp(argv[i], "--attesa") == 0 && i + 1 < argc)
			secondi_attesa = atof(argv[++i]);
		else
		{
			fprintf(stderr, "uso: %s --uscita NOME [--posizione X,Y] [--misura LxA]\n", argv[0]);
			return 2;
		}
	}

	signal(SIGINT, fermati);
	signal(SIGTERM, fermati);
	setvbuf(stdout, NULL, _IOLBF, 0);

	display = wl_display_connect(NULL);
	if (!display)
	{
		fprintf(stderr, "⛔ nessun display Wayland (WAYLAND_DISPLAY / XDG_RUNTIME_DIR)\n");
		return 1;
	}
	registro = wl_display_get_registry(display);
	wl_registry_add_listener(registro, &ascolto_registro, NULL);
	wl_display_roundtrip(display); /* i globali */
	wl_display_roundtrip(display); /* gli eventi delle uscite */

	if (!compositore || !guscio)
	{
		fprintf(stderr, "⛔ manca wl_compositor o xdg_wm_base\n");
		return 1;
	}

	fprintf(stderr, "uscite viste: %d\n", quante_uscite);
	for (i = 0; i < quante_uscite; i++)
		fprintf(stderr, "  [%d] nome=%s pos=%d,%d modo=%dx%d@%d\n", i,
		        uscite[i].nome[0] ? uscite[i].nome : "(senza-nome)", uscite[i].x, uscite[i].y,
		        uscite[i].larghezza, uscite[i].altezza, uscite[i].refresh_mhz);

	scelta = scegli_uscita();
	if (scelta < 0)
	{
		/* ⛔ Non si ripiega sulla prima uscita: una scena sul monitor sbagliato
		 *    misura il monitor sbagliato e non lo dice (`LEZIONI.md` §1.8 —
		 *    si fallisce DICHIARANDOLO, non si ripiega in silenzio). */
		fprintf(stderr, "⛔ nessuna uscita corrisponde a «%s» / posizione %d,%d — NON ripiego\n",
		        uscita_voluta, posizione_voluta_x, posizione_voluta_y);
		return 3;
	}
	printf("U %llu %s %d,%d %dx%d@%d\n", (unsigned long long) ora_us(),
	       uscite[scelta].nome[0] ? uscite[scelta].nome : "(senza-nome)", uscite[scelta].x,
	       uscite[scelta].y, uscite[scelta].larghezza, uscite[scelta].altezza,
	       uscite[scelta].refresh_mhz);

	larghezza = larghezza_chiesta;
	altezza = altezza_chiesta;

	superficie = wl_compositor_create_surface(compositore);
	wl_surface_add_listener(superficie, &ascolto_superficie, NULL);
	xdg_superficie = xdg_wm_base_get_xdg_surface(guscio, superficie);
	xdg_surface_add_listener(xdg_superficie, &ascolto_xdg, NULL);
	xdg_finestra = xdg_surface_get_toplevel(xdg_superficie);
	xdg_toplevel_add_listener(xdg_finestra, &ascolto_finestra, NULL);
	xdg_toplevel_set_title(xdg_finestra, "03-b14-scena");
	xdg_toplevel_set_app_id(xdg_finestra, "it.remotix.banco.b14");
	/* ⭐ Schermo intero SU QUELL'USCITA: e' la riga che sposta la scena sul
	 *    monitor giusto invece di sperare che il compositore la metta li'. */
	xdg_toplevel_set_fullscreen(xdg_finestra, uscite[scelta].oggetto);
	wl_surface_commit(superficie);

	scadenza = ora_us() + 5000000ull;
	while (!configurata && ora_us() < scadenza)
		if (wl_display_dispatch(display) < 0)
			break;
	if (!configurata)
	{
		fprintf(stderr, "⛔ nessun configure entro 5 s\n");
		return 4;
	}

	egl_display = eglGetDisplay((EGLNativeDisplayType) display);
	if (egl_display == EGL_NO_DISPLAY || !eglInitialize(egl_display, NULL, NULL))
	{
		fprintf(stderr, "⛔ EGL non si inizializza\n");
		return 5;
	}
	eglBindAPI(EGL_OPENGL_ES_API);
	if (!eglChooseConfig(egl_display, attributi_config, &egl_config, 1, &quante_config) ||
	    quante_config < 1)
	{
		fprintf(stderr, "⛔ nessuna EGLConfig\n");
		return 5;
	}
	egl_contesto = eglCreateContext(egl_display, egl_config, EGL_NO_CONTEXT, attributi_contesto);
	finestra_egl = wl_egl_window_create(superficie, larghezza, altezza);
	egl_superficie = eglCreateWindowSurface(egl_display, egl_config,
	                                        (EGLNativeWindowType) finestra_egl, NULL);
	if (egl_superficie == EGL_NO_SURFACE ||
	    !eglMakeCurrent(egl_display, egl_superficie, egl_superficie, egl_contesto))
	{
		fprintf(stderr, "⛔ EGL surface/context non si attivano\n");
		return 5;
	}
	/* ⛔ Intervallo 0: il ritmo lo detta il frame callback del compositore, non
	 *    l'attesa di EGL.  Con l'intervallo a 1 si misurerebbero due freni
	 *    sovrapposti e non si saprebbe quale ha vinto. */
	eglSwapInterval(egl_display, 0);

	printf("R %llu %s %dx%d\n", (unsigned long long) ora_us(),
	       (const char *) glGetString(GL_RENDERER), larghezza, altezza);

	/* Opaca su tutta la tela: §1.1 lo pretende — una superficie con alfa
	 * costringe il compositore a fondere, e la misura cambia natura. */
	opaca = wl_compositor_create_region(compositore);
	wl_region_add(opaca, 0, 0, larghezza, altezza);
	wl_surface_set_opaque_region(superficie, opaca);
	wl_region_destroy(opaca);

	disegna(); /* il primo giro innesca la catena dei callback */

	scadenza = ora_us() + (uint64_t) (secondi_attesa * 1000000.0);
	while (gira)
	{
		if (wl_display_dispatch(display) < 0)
		{
			fprintf(stderr, "⛔ il display Wayland e' caduto: %s\n", strerror(errno));
			break;
		}
		if (!entrata_vista && ora_us() > scadenza)
		{
			fprintf(stderr, "⛔ nessun wl_surface.enter entro %.0f s: non so su quale "
			                "monitor sto disegnando, e non lo indovino\n", secondi_attesa);
			return 6;
		}
	}

	printf("F %llu %llu\n", (unsigned long long) ora_us(), (unsigned long long) disegni);
	fflush(stdout);
	return 0;
}
