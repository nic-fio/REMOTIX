/*
 * 06-b33-testimone.c — ⭐ THE RECEIVING SIDE, without a browser.  Sub-phase 6.1.
 *
 *   ./06-b33-testimone [--misura 1264x800]
 *
 * ⛔ It is `04-b24-testimone.c` COPIED, with **one** addition and not one line
 *    fewer: the `RITELA` line, which says when the window changes size under
 *    it.  It is needed because in this sub-phase the canvas size changes ON
 *    REATTACH, and without that line «the compositor resized the
 *    screen» and «nothing happened» look the same — from the RECEIVING
 *    SIDE, which is the only one that counts (`CODER.md` §3.8).
 *
 * ⚠ The rest is B24's and has already paid its price (the browser that did not
 *   ask for the page, the monitor chosen by name and not hoped for): it is not
 *   rewritten.
 *
 * It opens a fullscreen window **on the monitor of the requested size**,
 * listens to `wl_pointer` and `wl_keyboard`, and prints one JSON line for
 * every event the compositor delivers to it.  Nothing else.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY NOT THE BROWSER, WHICH WAS THE INSTRUMENT ALREADY CERTIFIED (S7)
 *
 * `[M]` 14 Aug 2026, test machine, user `prova`: Firefox `--kiosk`
 * in the headless session **starts and never asks for the page**.  Measured three
 * times: process alive, state `S`, ⛔ **zero HTTP requests after 149 seconds**,
 * Firefox log empty.  With a new profile, with a reused one, with and
 * without a terminal.  ⚠ The cause was NOT found, and nobody pretended
 * otherwise: it is written in the report as something that did not work.
 *
 * ⇒ Another receiving side was needed, and this one is **closer to the truth**,
 *   not a worse fallback: between `libei` and the page there are Mutter *and* the
 *   browser; here there is only Mutter.  What this window sees is
 *   exactly what the compositor delivers to any window.
 *
 * ⚠ AND WHAT IS LOST, said instead of kept quiet: `RCP.md` §7.3 measured the
 *   sign on `deltaY` of a `wheel` event, that is one floor higher.  The
 *   bridge between the two is the convention of `wl_pointer.axis`, which the
 *   specification fixes: *«the value is positive in the direction the content moves»* — that is
 *   positive `axis` ⇔ the content goes down ⇔ positive `deltaY`.  The bridge is
 *   `[S]`, not `[M]`: whoever wants the whole chain should redo S7 with the page.
 *
 * ---------------------------------------------------------------------------
 * ⭐ AND THE MONITOR IS CHOSEN BY NAME, NOT HOPED FOR — form E2
 *
 * `xdg_toplevel_set_fullscreen(NULL)` lets the compositor choose, and with
 * two monitors in the session the window can end up on the one that is not ours:
 * the injection would go elsewhere and this program would print a silence that
 * reads as «the input does not arrive».  ⇒ We scan the `wl_output`s, we
 * take the one of the requested size, and ⛔ **if there is none we exit saying so**.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <wayland-client.h>

#include "xdg-shell-client-protocol.h"

static struct wl_compositor *compositore;
static struct wl_shm *memoria;
static struct xdg_wm_base *guscio;
static struct wl_seat *posto;
static struct wl_surface *superficie;
static struct xdg_surface *xdg_sup;
static struct xdg_toplevel *finestra;
static struct wl_pointer *puntatore;
static struct wl_keyboard *tastiera;

#define OUTPUT_MAX 8
static struct
{
	struct wl_output *output;
	int32_t l, a;
	char nome[64];
} schermi[OUTPUT_MAX];
static int quanti_schermi;

static uint32_t voluta_l = 1600, voluta_a = 900;
static int scelto = -1;
static bool configurata;
static int32_t larghezza = 1600, altezza = 900;
/* The size DECLARED in the last line: it serves to write `RITELA` only when
 * it really changes, and not at every `configure`. */
static int32_t vista_l, vista_a;
static unsigned long contatore;

/* ⛔ One line per event, and ALWAYS with a growing `n`: it is the denominator.
 *    «Nothing arrived» and «I did not print» look the same
 *    without a counter that grows. */
static void riga(const char *forma, ...)
{
	va_list a;

	printf("{\"n\":%lu,", ++contatore);
	va_start(a, forma);
	vprintf(forma, a);
	va_end(a);
	printf("}\n");
	fflush(stdout);
}

/* ------------------------------------------------------------------ *
 *  The pointer
 * ------------------------------------------------------------------ */
static void p_entra(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sup,
                    wl_fixed_t x, wl_fixed_t y)
{
	riga("\"tipo\":\"PUNTATORE_ENTRA\",\"x\":%.1f,\"y\":%.1f", wl_fixed_to_double(x),
	     wl_fixed_to_double(y));
}
static void p_esce(void *d, struct wl_pointer *p, uint32_t s, struct wl_surface *sup)
{
	riga("\"tipo\":\"PUNTATORE_ESCE\"");
}
static void p_muove(void *d, struct wl_pointer *p, uint32_t t, wl_fixed_t x, wl_fixed_t y)
{
	/* ⛔ Coordinates LOCAL TO THE SURFACE: with a fullscreen window
	 *    they are the position on the monitor, that is exactly what we
	 *    asked of `input_puntatore`.  The comparison is direct. */
	riga("\"tipo\":\"PUNTATORE\",\"x\":%.1f,\"y\":%.1f", wl_fixed_to_double(x),
	     wl_fixed_to_double(y));
}
static void p_bottone(void *d, struct wl_pointer *p, uint32_t s, uint32_t t, uint32_t bottone,
                      uint32_t stato)
{
	/* ⭐ `wl_pointer.button` carries the **evdev** code: `BTN_LEFT` = 0x110 =
	 *    272, the same number we sent.  No translation in
	 *    between, so the comparison is between the same quantity. */
	riga("\"tipo\":\"BOTTONE\",\"bottone\":%u,\"premuto\":%u", bottone, stato);
}
static void p_asse(void *d, struct wl_pointer *p, uint32_t t, uint32_t asse, wl_fixed_t valore)
{
	riga("\"tipo\":\"ASSE\",\"asse\":%u,\"valore\":%.2f", asse, wl_fixed_to_double(valore));
}
static void p_cornice(void *d, struct wl_pointer *p) {}
static void p_sorgente(void *d, struct wl_pointer *p, uint32_t s)
{
	riga("\"tipo\":\"ASSE_SORGENTE\",\"sorgente\":%u", s);
}
static void p_stop(void *d, struct wl_pointer *p, uint32_t t, uint32_t asse) {}
static void p_discreto(void *d, struct wl_pointer *p, uint32_t asse, int32_t passi)
{
	riga("\"tipo\":\"ASSE_DISCRETO\",\"asse\":%u,\"passi\":%d", asse, passi);
}
static void p_120(void *d, struct wl_pointer *p, uint32_t asse, int32_t v120)
{
	/* ⭐⭐ THIS IS THE MEASUREMENT OF THE SIGN, and in the same unit as the protocol:
	 *     `RCP.md` §7.3 counts in units of 120, and `axis_value120` carries 120. */
	riga("\"tipo\":\"ASSE_120\",\"asse\":%u,\"v120\":%d", asse, v120);
}
static void p_direzione(void *d, struct wl_pointer *p, uint32_t asse, uint32_t dir) {}

static const struct wl_pointer_listener ascolto_puntatore = {
	.enter = p_entra,
	.leave = p_esce,
	.motion = p_muove,
	.button = p_bottone,
	.axis = p_asse,
	.frame = p_cornice,
	.axis_source = p_sorgente,
	.axis_stop = p_stop,
	.axis_discrete = p_discreto,
	.axis_value120 = p_120,
	.axis_relative_direction = p_direzione,
};

/* ------------------------------------------------------------------ *
 *  The keyboard
 * ------------------------------------------------------------------ */
static void t_keymap(void *d, struct wl_keyboard *k, uint32_t formato, int32_t fd, uint32_t misura)
{
	riga("\"tipo\":\"KEYMAP\",\"formato\":%u,\"byte\":%u", formato, misura);
	close(fd);
}
static void t_entra(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sup,
                    struct wl_array *tasti)
{
	riga("\"tipo\":\"FUOCO\",\"dentro\":1");
}
static void t_esce(void *d, struct wl_keyboard *k, uint32_t s, struct wl_surface *sup)
{
	riga("\"tipo\":\"FUOCO\",\"dentro\":0");
}
static void t_tasto(void *d, struct wl_keyboard *k, uint32_t s, uint32_t t, uint32_t tasto,
                    uint32_t stato)
{
	/* ⛔ `wl_keyboard.key` carries the **evdev** code, the same one we
	 *    sent to `input_posizione`.  `KEY_A` = 30 on both sides. */
	riga("\"tipo\":\"TASTO\",\"codice\":%u,\"premuto\":%u", tasto, stato);
}
static void t_modificatori(void *d, struct wl_keyboard *k, uint32_t s, uint32_t premuti,
                           uint32_t agganciati, uint32_t bloccati, uint32_t gruppo)
{
	riga("\"tipo\":\"MODIFICATORI\",\"premuti\":%u,\"bloccati\":%u,\"gruppo\":%u", premuti,
	     bloccati, gruppo);
}
static void t_ripetizione(void *d, struct wl_keyboard *k, int32_t ritmo, int32_t ritardo) {}

static const struct wl_keyboard_listener ascolto_tastiera = {
	.keymap = t_keymap,
	.enter = t_entra,
	.leave = t_esce,
	.key = t_tasto,
	.modifiers = t_modificatori,
	.repeat_info = t_ripetizione,
};

/*
 * ⛔⛔⛔ AND THE CAPABILITY GOES AWAY AND COMES BACK — defect of the WITNESS found on 21
 *       Aug 2026, and it made the instrument mute without saying a word.
 *
 * This function hooked `wl_pointer` **only once** (`&& !puntatore`) and
 * never let go of it.  ⇒ When the seat loses the capability and gets it back, the
 * compositor has destroyed its pointer: our object stays there,
 * ⛔ **receives nothing more and gives no error**, and on the return
 * `!puntatore` is false so we never hook again.
 *
 * ⚠ It is **the same defect** that `STUDI.md` §gnome §9 describes for `libei` —
 *   *«the pointer to the old device stops working without an error»* —
 *   but on the Wayland side, and in the instrument instead of the product.  ⭐ It is the
 *   worst way a bench can break: the witness says «I saw
 *   nothing», and whoever reads it blames the product.
 *
 * `[M]` It was seen while working on cure «C»: on reattach of the EIS channel the seat
 *       goes **3 → 1 → 0 → 1 → 3** (on the session without a monitor our
 *       virtual devices are the ONLY ones of the seat), and from then on the
 *       witness did not see a single event.
 *
 * ⇒ We let go when the capability drops, and hook again when it returns.  It is
 *   also what a well-written Wayland client must do.
 */
static void posto_capacita(void *d, struct wl_seat *s, uint32_t cap)
{
	riga("\"tipo\":\"POSTO\",\"capacita\":%u", cap);

	if ((cap & WL_SEAT_CAPABILITY_POINTER) && !puntatore)
	{
		puntatore = wl_seat_get_pointer(s);
		wl_pointer_add_listener(puntatore, &ascolto_puntatore, NULL);
		riga("\"tipo\":\"POSTO_PUNTATORE\",\"stato\":\"agganciato\"");
	}
	else if (!(cap & WL_SEAT_CAPABILITY_POINTER) && puntatore)
	{
		wl_pointer_release(puntatore);
		puntatore = NULL;
		/* ⛔ And it is WRITTEN: without this line «the seat lost the pointer» and
		 *    «nothing arrived» look the same in the file. */
		riga("\"tipo\":\"POSTO_PUNTATORE\",\"stato\":\"mollato\"");
	}

	if ((cap & WL_SEAT_CAPABILITY_KEYBOARD) && !tastiera)
	{
		tastiera = wl_seat_get_keyboard(s);
		wl_keyboard_add_listener(tastiera, &ascolto_tastiera, NULL);
		riga("\"tipo\":\"POSTO_TASTIERA\",\"stato\":\"agganciata\"");
	}
	else if (!(cap & WL_SEAT_CAPABILITY_KEYBOARD) && tastiera)
	{
		wl_keyboard_release(tastiera);
		tastiera = NULL;
		riga("\"tipo\":\"POSTO_TASTIERA\",\"stato\":\"mollata\"");
	}
}
static void posto_nome(void *d, struct wl_seat *s, const char *nome) {}
static const struct wl_seat_listener ascolto_posto = { posto_capacita, posto_nome };

/* ------------------------------------------------------------------ *
 *  The screens
 * ------------------------------------------------------------------ */
static void o_geometria(void *d, struct wl_output *o, int32_t x, int32_t y, int32_t lf, int32_t af,
                        int32_t sub, const char *venditore, const char *modello, int32_t trasf)
{
	int i = (int) (intptr_t) d;

	if (i < OUTPUT_MAX)
		snprintf(schermi[i].nome, sizeof schermi[i].nome, "%s", modello ?: "?");
}
static void o_modo(void *d, struct wl_output *o, uint32_t bandiere, int32_t l, int32_t a,
                   int32_t ritmo)
{
	int i = (int) (intptr_t) d;

	if (i < OUTPUT_MAX && (bandiere & WL_OUTPUT_MODE_CURRENT))
	{
		schermi[i].l = l;
		schermi[i].a = a;
	}
}
static void o_fatto(void *d, struct wl_output *o) {}
static void o_scala(void *d, struct wl_output *o, int32_t s) {}
static void o_nome(void *d, struct wl_output *o, const char *n) {}
static void o_descrizione(void *d, struct wl_output *o, const char *n) {}
static const struct wl_output_listener ascolto_output = { o_geometria, o_modo,  o_fatto,
	                                                      o_scala,     o_nome, o_descrizione };

/* ------------------------------------------------------------------ *
 *  The shell
 * ------------------------------------------------------------------ */
static void guscio_ping(void *d, struct xdg_wm_base *g, uint32_t s)
{
	xdg_wm_base_pong(g, s);
}
static const struct xdg_wm_base_listener ascolto_guscio = { guscio_ping };

static int memoria_nuova(size_t byte)
{
	int fd = memfd_create("b33-testimone", MFD_CLOEXEC);

	if (fd < 0)
		return -1;
	if (ftruncate(fd, (off_t) byte) < 0)
	{
		close(fd);
		return -1;
	}
	return fd;
}

static void dipingi(void)
{
	size_t passo = (size_t) larghezza * 4;
	size_t byte = passo * (size_t) altezza;
	int fd = memoria_nuova(byte);
	uint32_t *pixel;
	struct wl_shm_pool *piscina;
	struct wl_buffer *pacco;

	if (fd < 0)
		return;
	pixel = mmap(NULL, byte, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (pixel == MAP_FAILED)
	{
		close(fd);
		return;
	}
	for (size_t i = 0; i < byte / 4; i++)
		pixel[i] = 0xFF101014;
	piscina = wl_shm_create_pool(memoria, fd, (int32_t) byte);
	pacco = wl_shm_pool_create_buffer(piscina, 0, larghezza, altezza, (int32_t) passo,
	                                  WL_SHM_FORMAT_ARGB8888);
	wl_shm_pool_destroy(piscina);
	munmap(pixel, byte);
	close(fd);

	wl_surface_attach(superficie, pacco, 0, 0);
	wl_surface_damage_buffer(superficie, 0, 0, larghezza, altezza);
	wl_surface_commit(superficie);
}

static void sup_configura(void *d, struct xdg_surface *s, uint32_t serie)
{
	xdg_surface_ack_configure(s, serie);
	dipingi();
	if (!configurata)
	{
		configurata = true;
		vista_l = larghezza;
		vista_a = altezza;
		riga("\"tipo\":\"PRONTA\",\"larghezza\":%d,\"altezza\":%d,\"schermo\":\"%s\"", larghezza,
		     altezza, scelto >= 0 ? schermi[scelto].nome : "?");
	}
	/*
	 * ⭐⭐ THE ONLY ADDITION TO B24 — and it is written from the side that RECEIVES.
	 *
	 * ⛔ The server log says «canvas 1264x800 → 1000x640»: it says that we
	 *    ASKED.  This line says that the compositor really
	 *    resized the screen under a window **already open**, which is the
	 *    scene of point 3 of the mandate.  ⚠ And it is written ONLY when it changes: one
	 *    line for every `configure` would make a resize
	 *    indistinguishable from a redraw.
	 */
	else if (larghezza != vista_l || altezza != vista_a)
	{
		riga("\"tipo\":\"RITELA\",\"da_l\":%d,\"da_a\":%d,\"a_l\":%d,\"a_a\":%d", vista_l, vista_a,
		     larghezza, altezza);
		vista_l = larghezza;
		vista_a = altezza;
	}
}
static const struct xdg_surface_listener ascolto_sup = { sup_configura };

static void fin_configura(void *d, struct xdg_toplevel *f, int32_t l, int32_t a,
                          struct wl_array *stati)
{
	if (l > 0 && a > 0)
	{
		larghezza = l;
		altezza = a;
	}
}
static void fin_chiudi(void *d, struct xdg_toplevel *f)
{
	riga("\"tipo\":\"CHIUSA\"");
	exit(0);
}
static void fin_limiti(void *d, struct xdg_toplevel *f, int32_t l, int32_t a) {}
static void fin_stati(void *d, struct xdg_toplevel *f, struct wl_array *c) {}
static const struct xdg_toplevel_listener ascolto_fin = { fin_configura, fin_chiudi, fin_limiti,
	                                                      fin_stati };

/* ------------------------------------------------------------------ *
 *  The global registry
 * ------------------------------------------------------------------ */
static void registro_globale(void *d, struct wl_registry *r, uint32_t nome, const char *interfaccia,
                             uint32_t versione)
{
	if (!strcmp(interfaccia, wl_compositor_interface.name))
		compositore = wl_registry_bind(r, nome, &wl_compositor_interface, 4);
	else if (!strcmp(interfaccia, wl_shm_interface.name))
		memoria = wl_registry_bind(r, nome, &wl_shm_interface, 1);
	else if (!strcmp(interfaccia, xdg_wm_base_interface.name))
	{
		guscio = wl_registry_bind(r, nome, &xdg_wm_base_interface, 1);
		xdg_wm_base_add_listener(guscio, &ascolto_guscio, NULL);
	}
	else if (!strcmp(interfaccia, wl_seat_interface.name))
	{
		/* ⛔ Version 8: it is the one that carries `axis_value120`, that is the unit in
		 *    which `RCP.md` §7.3 counts the wheel.  With a lower version the
		 *    sign could be measured only on the smooth axis, which is another
		 *    quantity. */
		uint32_t v = versione < 8 ? versione : 8;

		posto = wl_registry_bind(r, nome, &wl_seat_interface, v);
		wl_seat_add_listener(posto, &ascolto_posto, NULL);
		riga("\"tipo\":\"POSTO_LEGATO\",\"versione\":%u", v);
	}
	else if (!strcmp(interfaccia, wl_output_interface.name) && quanti_schermi < OUTPUT_MAX)
	{
		int i = quanti_schermi++;

		schermi[i].output = wl_registry_bind(r, nome, &wl_output_interface, 2);
		wl_output_add_listener(schermi[i].output, &ascolto_output, (void *) (intptr_t) i);
	}
}
static void registro_via(void *d, struct wl_registry *r, uint32_t nome) {}
static const struct wl_registry_listener ascolto_registro = { registro_globale, registro_via };

int main(int argc, char **argv)
{
	struct wl_display *schermo;
	struct wl_registry *registro;

	setvbuf(stdout, NULL, _IOLBF, 0);
	for (int i = 1; i < argc; i++)
		if (!strcmp(argv[i], "--misura") && i + 1 < argc)
			sscanf(argv[++i], "%ux%u", &voluta_l, &voluta_a);

	schermo = wl_display_connect(NULL);
	if (!schermo)
	{
		riga("\"tipo\":\"ERRORE\",\"perche\":\"no Wayland compositor\"");
		return 2;
	}
	registro = wl_display_get_registry(schermo);
	wl_registry_add_listener(registro, &ascolto_registro, NULL);
	wl_display_roundtrip(schermo);
	wl_display_roundtrip(schermo); /* the second round brings the modes of the outputs */

	if (!compositore || !memoria || !guscio)
	{
		riga("\"tipo\":\"ERRORE\",\"perche\":\"the compositor does not expose shell or memory\"");
		return 2;
	}

	/* ⛔ THE MONITOR IS CHOSEN, and if there is none we exit saying so. */
	for (int i = 0; i < quanti_schermi; i++)
	{
		riga("\"tipo\":\"SCHERMO\",\"i\":%d,\"l\":%d,\"a\":%d,\"nome\":\"%s\"", i, schermi[i].l,
		     schermi[i].a, schermi[i].nome);
		if (scelto < 0 && (uint32_t) schermi[i].l == voluta_l && (uint32_t) schermi[i].a == voluta_a)
			scelto = i;
	}
	if (scelto < 0)
	{
		riga("\"tipo\":\"ERRORE\",\"perche\":\"no %ux%u screen among the %d announced\"",
		     voluta_l, voluta_a, quanti_schermi);
		return 3;
	}
	larghezza = schermi[scelto].l;
	altezza = schermi[scelto].a;

	superficie = wl_compositor_create_surface(compositore);
	xdg_sup = xdg_wm_base_get_xdg_surface(guscio, superficie);
	xdg_surface_add_listener(xdg_sup, &ascolto_sup, NULL);
	finestra = xdg_surface_get_toplevel(xdg_sup);
	xdg_toplevel_add_listener(finestra, &ascolto_fin, NULL);
	xdg_toplevel_set_title(finestra, "B33 witness");
	xdg_toplevel_set_app_id(finestra, "remotix.b33");
	xdg_toplevel_set_fullscreen(finestra, schermi[scelto].output);
	wl_surface_commit(superficie);

	while (wl_display_dispatch(schermo) != -1)
		;
	riga("\"tipo\":\"FINE\"");
	return 0;
}
