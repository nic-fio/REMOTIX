/*
 * 06-b33-testimone.c — ⭐ IL LATO CHE RICEVE, senza browser.  Sottofase 6.1.
 *
 *   ./06-b33-testimone [--misura 1264x800]
 *
 * ⛔ E' `04-b24-testimone.c` COPIATO, con **una** aggiunta e non una riga di
 *    meno: la riga `RITELA`, che dice quando la finestra cambia misura sotto di
 *    se'.  Serve perche' in questa sottofase la misura della tela cambia AL
 *    RIATTACCO, e senza quella riga «il compositore ha ridimensionato lo
 *    schermo» e «non e' successo niente» hanno lo stesso aspetto — dal LATO CHE
 *    RICEVE, che e' l'unico che conta (`CODER.md` §3.8).
 *
 * ⚠ Il resto e' di B24 e ha gia' pagato il suo prezzo (il browser che non
 *   chiedeva la pagina, il monitor scelto per nome e non sperato): non si
 *   riscrive.
 *
 * Apre una finestra a schermo intero **sul monitor della misura chiesta**, si
 * mette in ascolto di `wl_pointer` e `wl_keyboard`, e stampa una riga JSON per
 * ogni evento che il compositore le consegna.  Niente altro.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' NON IL BROWSER, CHE ERA LO STRUMENTO GIA' CERTIFICATO (S7)
 *
 * `[M]` 14 agosto 2026, macchina di prova, utente `prova`: Firefox `--kiosk`
 * nella sessione headless **parte e non chiede mai la pagina**.  Misurato tre
 * volte: processo vivo, stato `S`, ⛔ **zero richieste HTTP dopo 149 secondi**,
 * registro di Firefox vuoto.  Con un profilo nuovo, con uno riusato, con e
 * senza terminale.  ⚠ La causa NON e' stata trovata, e non si e' fatta finta di
 * niente: e' scritta nel rapporto come cosa che non ha funzionato.
 *
 * ⇒ Serviva un altro lato-che-riceve, e questo e' **piu' vicino alla verita'**,
 *   non un ripiego peggiore: fra `libei` e la pagina ci sono Mutter *e* il
 *   browser; qui c'e' solo Mutter.  Quel che questa finestra vede e'
 *   esattamente quel che il compositore consegna a una finestra qualunque.
 *
 * ⚠ E QUEL CHE SI PERDE, detto invece che taciuto: `RCP.md` §7.3 ha misurato il
 *   segno su `deltaY` di un evento `wheel`, cioe' un piano piu' in alto.  Il
 *   ponte fra i due e' la convenzione di `wl_pointer.axis`, che la specifica
 *   fissa: *«the value is positive in the direction the content moves»* — cioe'
 *   `axis` positivo ⇔ il contenuto scende ⇔ `deltaY` positivo.  Il ponte e'
 *   `[S]`, non `[M]`: chi vuole la catena intera rifaccia S7 con la pagina.
 *
 * ---------------------------------------------------------------------------
 * ⭐ E IL MONITOR SI SCEGLIE PER NOME, NON SI SPERA — forma E2
 *
 * `xdg_toplevel_set_fullscreen(NULL)` lascia scegliere al compositore, e con
 * due monitor in sessione la finestra puo' finire su quello che non e' nostro:
 * l'iniezione andrebbe altrove e questo programma stamperebbe un silenzio che
 * si legge come «l'input non arriva».  ⇒ Si scandiscono i `wl_output`, si
 * prende quello della misura chiesta, e ⛔ **se non c'e' si esce dicendolo**.
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
/* La misura DICHIARATA nell'ultima riga: serve a scrivere `RITELA` solo quando
 * cambia davvero, e non a ogni `configure`. */
static int32_t vista_l, vista_a;
static unsigned long contatore;

/* ⛔ Una riga per evento, e SEMPRE con `n` crescente: e' il denominatore.
 *    «Non e' arrivato niente» e «non ho stampato» hanno lo stesso aspetto
 *    senza un contatore che cresce. */
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
 *  Il puntatore
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
	/* ⛔ Coordinate LOCALI ALLA SUPERFICIE: con una finestra a schermo intero
	 *    sono la posizione sul monitor, cioe' esattamente quel che abbiamo
	 *    chiesto a `input_puntatore`.  Il confronto e' diretto. */
	riga("\"tipo\":\"PUNTATORE\",\"x\":%.1f,\"y\":%.1f", wl_fixed_to_double(x),
	     wl_fixed_to_double(y));
}
static void p_bottone(void *d, struct wl_pointer *p, uint32_t s, uint32_t t, uint32_t bottone,
                      uint32_t stato)
{
	/* ⭐ `wl_pointer.button` porta il codice **evdev**: `BTN_LEFT` = 0x110 =
	 *    272, lo stesso numero che abbiamo mandato.  Nessuna traduzione in
	 *    mezzo, quindi il confronto e' fra la stessa grandezza. */
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
	/* ⭐⭐ QUESTA E' LA MISURA DEL SEGNO, e nella stessa unita' del protocollo:
	 *     `RCP.md` §7.3 conta in unita' da 120, e `axis_value120` porta 120. */
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
 *  La tastiera
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
	/* ⛔ `wl_keyboard.key` porta il codice **evdev**, lo stesso che abbiamo
	 *    mandato a `input_posizione`.  `KEY_A` = 30 di qua e di la'. */
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
 * ⛔⛔⛔ E LA CAPACITA' SE NE VA E TORNA — difetto del TESTIMONE trovato il 21
 *       agosto 2026, e ha reso muto lo strumento senza dire una parola.
 *
 * Questa funzione agganciava `wl_pointer` **una volta sola** (`&& !puntatore`) e
 * non lo mollava mai.  ⇒ Quando il posto perde la capacita' e la riprende, il
 * compositore ha distrutto il suo puntatore: il nostro oggetto resta li',
 * ⛔ **non riceve piu' niente e non da' nessun errore**, e al ritorno il
 * `!puntatore` e' falso quindi non ci si riaggancia mai piu'.
 *
 * ⚠ E' **lo stesso difetto** che `STUDI.md` §gnome §9 descrive per `libei` —
 *   *«il puntatore al dispositivo vecchio smette di funzionare senza errore»* —
 *   ma dal lato Wayland, e nello strumento invece che nel prodotto.  ⭐ E' il
 *   modo peggiore in cui un banco puo' rompersi: il testimone dice «non ho
 *   visto niente», e chi legge accusa il prodotto.
 *
 * `[M]` Si e' visto curando la cura «C»: al riattacco del canale EIS il posto
 *       passa **3 → 1 → 0 → 1 → 3** (sulla sessione senza monitor i nostri
 *       dispositivi virtuali sono gli UNICI del posto), e da li' in poi il
 *       testimone non ha piu' visto un solo evento.
 *
 * ⇒ Si molla quando la capacita' cade, e ci si riaggancia quando torna.  E'
 *   anche quel che un cliente Wayland scritto bene deve fare.
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
		/* ⛔ E si SCRIVE: senza questa riga «il posto ha perso il puntatore» e
		 *    «non e' arrivato niente» hanno lo stesso aspetto nel file. */
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
 *  Gli schermi
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
 *  Il guscio
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
	 * ⭐⭐ L'UNICA AGGIUNTA A B24 — e si scrive dal lato che RICEVE.
	 *
	 * ⛔ Il registro del server dice «tela 1264x800 → 1000x640»: dice che
	 *    abbiamo CHIESTO.  Questa riga dice che il compositore ha davvero
	 *    ridimensionato lo schermo sotto una finestra **gia' aperta**, che e' la
	 *    scena del punto 3 del mandato.  ⚠ E si scrive SOLO quando cambia: una
	 *    riga per ogni `configure` renderebbe indistinguibile un
	 *    ridimensionamento da un ridisegno.
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
 *  Il registro globale
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
		/* ⛔ Versione 8: e' quella che porta `axis_value120`, cioe' l'unita' in
		 *    cui `RCP.md` §7.3 conta la rotella.  Con una versione piu' bassa il
		 *    segno si potrebbe misurare solo sull'asse liscio, che e' un'altra
		 *    grandezza. */
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
		riga("\"tipo\":\"ERRORE\",\"perche\":\"nessun compositore Wayland\"");
		return 2;
	}
	registro = wl_display_get_registry(schermo);
	wl_registry_add_listener(registro, &ascolto_registro, NULL);
	wl_display_roundtrip(schermo);
	wl_display_roundtrip(schermo); /* il secondo giro porta i modi degli output */

	if (!compositore || !memoria || !guscio)
	{
		riga("\"tipo\":\"ERRORE\",\"perche\":\"il compositore non espone shell o memoria\"");
		return 2;
	}

	/* ⛔ IL MONITOR SI SCEGLIE, e se non c'e' si esce dicendolo. */
	for (int i = 0; i < quanti_schermi; i++)
	{
		riga("\"tipo\":\"SCHERMO\",\"i\":%d,\"l\":%d,\"a\":%d,\"nome\":\"%s\"", i, schermi[i].l,
		     schermi[i].a, schermi[i].nome);
		if (scelto < 0 && (uint32_t) schermi[i].l == voluta_l && (uint32_t) schermi[i].a == voluta_a)
			scelto = i;
	}
	if (scelto < 0)
	{
		riga("\"tipo\":\"ERRORE\",\"perche\":\"nessuno schermo %ux%u fra i %d annunciati\"",
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
	xdg_toplevel_set_title(finestra, "B33 testimone");
	xdg_toplevel_set_app_id(finestra, "remotix.b33");
	xdg_toplevel_set_fullscreen(finestra, schermi[scelto].output);
	wl_surface_commit(superficie);

	while (wl_display_dispatch(schermo) != -1)
		;
	riga("\"tipo\":\"FINE\"");
	return 0;
}
