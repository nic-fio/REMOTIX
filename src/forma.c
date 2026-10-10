/*
 * forma.c — the encoded theme and the dictionary.  The why is in `forma.h`,
 *           which is read first.
 *
 * ⛔ TWO HALVES THAT MUST SAY THE SAME THING: the theme is written by the SERVER
 *    (`sessione.c`, before starting the desktop), the colour is read by the CHILD
 *    (`cursore.c`, in the metadata).  ⇒ The table of names and the colour
 *    formula live HERE and nowhere else: it is the same binary on both
 *    sides, and a single list cannot diverge from itself.
 *
 * ⭐ The Xcursor parser is written here and not taken from `libXcursor`: that
 *    library drags in all of X11, and the format is four tables of
 *    little-endian integers (`man 3 Xcursor`, "FILE FORMAT").
 */
#include "forma.h"

#include "registro.h"

#include <glib/gstdio.h>
#include <stdlib.h>
#include <string.h>

#define AREA "forma"

/* The numbers of the Xcursor 1.0 format. */
#define XCUR_MAGIA     0x72756358u /* "Xcur" */
#define XCUR_IMMAGINE  0xfffd0002u
#define XCUR_TESTA     16u
#define XCUR_BLOCCO    36u
#define XCUR_LATO_MAX  0x7fffu     /* the largest the format allows */

/* ⚠ A ceiling on the file BEFORE reading it: a real Adwaita cursor weighs 78 KB
 *   (all sizes, up to 96).  Beyond that, it is not a cursor. */
#define FILE_MAX (8u * 1024u * 1024u)

/* ------------------------------------------------------------------ *
 *  The names, and the aliases they are looked up by in the real theme
 * ------------------------------------------------------------------ */

/*
 * ⛔ THE ORDER IS THE CODE: the index here is the colour in the theme.  One APPENDS
 *    at the end (and raises FORMA_QUANTE), never inserts in the middle — even though
 *    server and child are the same binary, a bench or an old copy of the
 *    theme in `XDG_RUNTIME_DIR` would read shifted colours.
 *
 * The first 68 are the names the invisible theme already had (phase 12): those
 * that programs really ask for, CSS names and X11 names together; the others
 * came later, at the end, each with its why.
 *
 * ⭐ The aliases: the name a program asks for is not always a file of the real
 *    theme (`[M]` Trixie's Adwaita has 62, and lacks `ibeam`, `size_hor`,
 *    `pointing_hand`…).  The name is tried, then the aliases in order, then the
 *    arrow.  ⚠ `size_fdiag` is the "\" diagonal (Qt `SizeFDiagCursor`),
 *    that is `nwse-resize`; `size_bdiag` the "/".
 */
typedef struct {
	const char *nome;
	const char *alias[4];
} Voce;

static const Voce VOCI[FORMA_QUANTE] = {
	{ "left_ptr", { "default", "arrow" } },
	{ "default", { "left_ptr", "arrow" } },
	{ "arrow", { "default", "left_ptr" } },
	{ "top_left_arrow", { "default", "left_ptr" } },
	{ "pointer", { "hand2", "hand1", "pointing_hand" } },
	{ "hand", { "pointer", "hand2", "hand1" } },
	{ "hand1", { "pointer", "hand2" } },
	{ "hand2", { "pointer", "hand1" } },
	{ "pointing_hand", { "pointer", "hand2" } },
	{ "text", { "xterm", "ibeam" } },
	{ "xterm", { "text", "ibeam" } },
	{ "ibeam", { "text", "xterm" } },
	{ "wait", { "watch" } },
	{ "watch", { "wait" } },
	{ "progress", { "left_ptr_watch", "watch", "wait" } },
	{ "left_ptr_watch", { "progress", "watch" } },
	{ "crosshair", { "cross", "tcross" } },
	{ "cross", { "crosshair", "tcross" } },
	{ "tcross", { "crosshair", "cross" } },
	{ "help", { "question_arrow", "whats_this" } },
	{ "question_arrow", { "help", "whats_this" } },
	{ "whats_this", { "help", "question_arrow" } },
	{ "not-allowed", { "forbidden", "crossed_circle" } },
	{ "forbidden", { "not-allowed", "crossed_circle" } },
	{ "crossed_circle", { "not-allowed", "forbidden" } },
	{ "no-drop", { "dnd-none", "not-allowed" } },
	{ "dnd-none", { "no-drop", "not-allowed" } },
	{ "dnd-copy", { "copy" } },
	{ "dnd-move", { "move", "default" } },
	{ "dnd-link", { "alias", "link" } },
	{ "copy", { "dnd-copy" } },
	{ "move", { "dnd-move", "fleur" } },
	{ "link", { "alias", "dnd-link" } },
	{ "alias", { "link", "dnd-link" } },
	{ "grab", { "openhand", "hand1" } },
	{ "grabbing", { "closedhand", "fleur" } },
	{ "openhand", { "grab", "hand1" } },
	{ "closedhand", { "grabbing", "fleur" } },
	{ "all-scroll", { "fleur", "size_all" } },
	{ "fleur", { "all-scroll", "size_all" } },
	{ "size_hor", { "ew-resize", "sb_h_double_arrow", "col-resize" } },
	{ "size_ver", { "ns-resize", "sb_v_double_arrow", "row-resize" } },
	{ "size_fdiag", { "nwse-resize", "bd_double_arrow" } },
	{ "size_bdiag", { "nesw-resize", "fd_double_arrow" } },
	{ "col-resize", { "sb_h_double_arrow", "ew-resize", "split_h" } },
	{ "row-resize", { "sb_v_double_arrow", "ns-resize", "split_v" } },
	{ "ew-resize", { "sb_h_double_arrow", "size_hor" } },
	{ "ns-resize", { "sb_v_double_arrow", "size_ver" } },
	{ "nesw-resize", { "fd_double_arrow", "size_bdiag" } },
	{ "nwse-resize", { "bd_double_arrow", "size_fdiag" } },
	{ "sb_h_double_arrow", { "ew-resize", "size_hor" } },
	{ "sb_v_double_arrow", { "ns-resize", "size_ver" } },
	{ "top_side", { "n-resize", "ns-resize" } },
	{ "bottom_side", { "s-resize", "ns-resize" } },
	{ "left_side", { "w-resize", "ew-resize" } },
	{ "right_side", { "e-resize", "ew-resize" } },
	{ "top_left_corner", { "nw-resize", "nwse-resize" } },
	{ "top_right_corner", { "ne-resize", "nesw-resize" } },
	{ "bottom_left_corner", { "sw-resize", "nesw-resize" } },
	{ "bottom_right_corner", { "se-resize", "nwse-resize" } },
	{ "zoom-in", { "zoom_in" } },
	{ "zoom-out", { "zoom_out" } },
	{ "cell", { "plus", "crosshair" } },
	{ "context-menu", { "default" } },
	{ "vertical-text", { "text", "xterm" } },
	{ "up_arrow", { "default", "left_ptr" } },
	{ "center_ptr", { "default", "left_ptr" } },
	{ "X_cursor", { "not-allowed", "crossed_circle" } },
	/*
	 * ⭐ 24 Sep 2026, for labwc (XFCE and LXQt) — APPENDED AT THE END, and the why.
	 *
	 * ⛔ `[M]` labwc 0.8.3 carries in its binary TWO series of names for its
	 *    borders: the CSS one (`n-resize`, `ne-resize`… `w-resize`, plus `grab`)
	 *    and the X11 one (`top_side`, `top_right_corner`… `left_side`, plus
	 *    `grabbing`).  It picks the CSS one if the theme has its shapes — and
	 *    ours has `grab` and `default`: `[M]` 24 Sep 2026 on rete14-lxqt, the
	 *    right border of qterminal arrives as "e-resize" (index 68), not
	 *    as `right_side`.  ⇒ Without these eight the border asked for
	 *    a name the theme did not have: no coloured pixel under the
	 *    pointer, and the probe (`wlroots.c`) could recognise nothing.
	 * ⭐ The same eight are also the names wlroots gives to the shapes of
	 *   `cursor-shape-v1` (`wlr_cursor_shape_v1_name`), that is what every
	 *   client asks for when it uses that protocol instead of its own theme.
	 * ⚠ `dnd-ask` and `all-resize` are the two shapes of v2 of
	 *   `cursor-shape-v1`: wlroots 0.18 does not announce them, but one more name in
	 *   the theme costs 68 bytes, and a missing name costs the shape.
	 */
	{ "e-resize", { "right_side", "ew-resize", "size_hor" } },
	{ "w-resize", { "left_side", "ew-resize", "size_hor" } },
	{ "n-resize", { "top_side", "ns-resize", "size_ver" } },
	{ "s-resize", { "bottom_side", "ns-resize", "size_ver" } },
	{ "ne-resize", { "top_right_corner", "nesw-resize", "size_bdiag" } },
	{ "nw-resize", { "top_left_corner", "nwse-resize", "size_fdiag" } },
	{ "se-resize", { "bottom_right_corner", "nwse-resize", "size_fdiag" } },
	{ "sw-resize", { "bottom_left_corner", "nesw-resize", "size_bdiag" } },
	{ "dnd-ask", { "dnd-copy", "copy" } },
	{ "all-resize", { "fleur", "all-scroll", "move" } },
};

/* If not even an alias is there: the arrow, which is better than nothing — the client
 * would see an arrow anyway, its own. */
static const char *ULTIMI[] = { "default", "left_ptr" };

/* ⭐ The real themes, in order.  ⚠ `[M]` 24 Sep 2026: Adwaita (62 cursors) is
 *   in ALL four `rete11-*` boxes; `breeze_cursors` only in KDE. */
static const char *TEMI_REALI[] = { "Adwaita", "breeze_cursors" };

/* ------------------------------------------------------------------ *
 *  The colours
 * ------------------------------------------------------------------ */

/*
 * ⭐ Index ⇒ colour.  ⛔ Red alone is enough to tell them apart (0x40 + i is
 *    different for every i < FORMA_QUANTE), and it lies between 0x40 and 0x8D: far from black and
 *    white, which are the colours real cursors are made of — no
 *    single-colour real cursor can be mistaken for one of ours.
 *    Green and blue are the check: a pixel with the right red and the rest random
 *    is NOT ours.  The bench (`banchi/14-f1-forma.sh`) checks them all.
 *    ⚠ The ceiling: up to 128 shapes red stays <= 0xBF, far from
 *      white; beyond that, the rule must be rethought before adding.
 */
static void colore(int i, uint8_t *r, uint8_t *g, uint8_t *b)
{
	*r = (uint8_t) (0x40 + i);
	*g = (uint8_t) (0xA5 ^ i);
	*b = (uint8_t) (((unsigned) i * 7u) & 0xFFu) ^ 0x5A;
}

int forma_da_pixel(uint8_t b, uint8_t g, uint8_t r, uint8_t a)
{
	uint8_t er, eg, eb;
	int i;

	/* ⛔ Opaque or nothing: the theme is opaque, and the metadata is premultiplied —
	 *    a lower alpha would mean colours already squashed, that is a
	 *    wrong index that looks like a right one. */
	if (a != 0xFF || r < 0x40 || r >= 0x40 + FORMA_QUANTE)
		return -1;
	i = r - 0x40;
	colore(i, &er, &eg, &eb);
	return (g == eg && b == eb) ? i : -1;
}

const char *forma_nome(int indice)
{
	return (indice >= 0 && indice < FORMA_QUANTE) ? VOCI[indice].nome : "?";
}

/* ------------------------------------------------------------------ *
 *  The encoded theme (written by the server)
 * ------------------------------------------------------------------ */

/* An Xcursor 1.0 cursor with ONE 1x1 image: the header of phase 12's
 * `scrivi_cursore_vuoto`, with the pixel that now has a colour. */
static gboolean scrivi_cursore_colorato(const char *percorso, int i)
{
	uint8_t r, g, b;
	guint32 argb;

	colore(i, &r, &g, &b);
	argb = 0xFF000000u | ((guint32) r << 16) | ((guint32) g << 8) | (guint32) b;
	{
		guint32 dati[] = {
			GUINT32_TO_LE(XCUR_MAGIA),
			GUINT32_TO_LE(XCUR_TESTA),  /* how long the header is */
			GUINT32_TO_LE(0x00010000u), /* version 1.0 */
			GUINT32_TO_LE(1u),          /* a single entry in the index */
			GUINT32_TO_LE(XCUR_IMMAGINE), GUINT32_TO_LE((guint32) FORMA_MISURA),
			GUINT32_TO_LE(28u),         /* where the chunk starts */
			GUINT32_TO_LE(XCUR_BLOCCO), /* length of the chunk header */
			GUINT32_TO_LE(XCUR_IMMAGINE),
			GUINT32_TO_LE((guint32) FORMA_MISURA), /* nominal size */
			GUINT32_TO_LE(1u),          /* chunk version */
			GUINT32_TO_LE(1u),          /* width */
			GUINT32_TO_LE(1u),          /* height */
			GUINT32_TO_LE(0u),          /* hotspot x */
			GUINT32_TO_LE(0u),          /* hotspot y */
			GUINT32_TO_LE(0u),          /* delay, for animations */
			GUINT32_TO_LE(argb),        /* the only pixel: OPAQUE, and of its own colour */
		};

		return g_file_set_contents(percorso, (const char *) dati, sizeof dati, NULL);
	}
}

gboolean forma_tema_scrivi(const char *runtime)
{
	g_autofree char *tema = g_build_filename(runtime, "remotix", "icons", FORMA_TEMA, NULL);
	g_autofree char *cursori = g_build_filename(tema, "cursors", NULL);
	g_autofree char *indice = g_build_filename(tema, "index.theme", NULL);
	unsigned scritte = 0;

	g_mkdir_with_parents(cursori, 0700);
	/* ⚠ No `Inherits=`: inheriting from a real theme would put back into the image
	 *   the REAL cursor for every shape missing here — and ⛔ that one would not
	 *   carry a colour of ours, the dictionary would not recognise it. */
	if (!g_file_set_contents(indice,
	                         "[Icon Theme]\n"
	                         "Name=REMOTIX (encoded)\n"
	                         "Comment=Each shape is an opaque pixel of its own colour: "
	                         "the server reads it and sends the client the real shape\n",
	                         -1, NULL)) {
		registro_dice(AREA, "⚠ cursor theme NOT written in %s", tema);
		return FALSE;
	}
	for (int i = 0; i < FORMA_QUANTE; i++) {
		g_autofree char *percorso = g_build_filename(cursori, VOCI[i].nome, NULL);

		if (scrivi_cursore_colorato(percorso, i))
			scritte++;
	}
	if (scritte == 0) {
		registro_dice(AREA, "⚠ no cursor shape written in %s", tema);
		return FALSE;
	}
	registro_dice(AREA, "⭐ theme «%s»: %u shapes of %d, each an opaque pixel of its own "
	              "colour, in %s",
	              FORMA_TEMA, scritte, FORMA_QUANTE, tema);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 *  The dictionary: the real images, from the real theme (read by the child)
 * ------------------------------------------------------------------ */

typedef struct {
	gboolean pronta;
	uint16_t larghezza, altezza;
	int16_t attivo_x, attivo_y;
	uint8_t *pixel; /* premultiplied BGRA, lives for the whole process */
	const char *da; /* the name of the file it came from (for the log) */
} Immagine;

static GMutex chiave;
static gboolean caricato;
static gboolean detto_assente;
static char *cartella_temi; /* NULL = /usr/share/icons */
static Immagine immagini[FORMA_QUANTE];

static guint32 le32(const guint8 *p)
{
	return (guint32) p[0] | ((guint32) p[1] << 8) | ((guint32) p[2] << 16) |
	       ((guint32) p[3] << 24);
}

/*
 * An Xcursor file ⇒ the first image of the nominal size closest to
 * FORMA_MISURA.  ⛔ Every length is checked BEFORE it is used: the file belongs
 * to another package, and a truncated file must not turn into memory read
 * outside the bucket.  ⚠ Of animations (`wait`, `progress`) the first
 * frame is taken: the wire carries a single image.
 */
static gboolean leggi_xcursor(const char *percorso, Immagine *out)
{
	g_autofree char *contenuto = NULL;
	gsize n = 0;
	const guint8 *d;
	guint32 testa, voci, scelta_pos = 0, scelta_dist = G_MAXUINT32;
	guint32 l, a, hx, hy, lt, at;

	if (!g_file_get_contents(percorso, &contenuto, &n, NULL) || n > FILE_MAX || n < XCUR_TESTA)
		return FALSE;
	d = (const guint8 *) contenuto;
	if (le32(d) != XCUR_MAGIA)
		return FALSE;
	testa = le32(d + 4);
	voci = le32(d + 12);
	if (testa < XCUR_TESTA || testa > n || voci == 0 || voci > (n - testa) / 12u)
		return FALSE;
	for (guint32 k = 0; k < voci; k++) {
		const guint8 *v = d + testa + (gsize) k * 12u;
		guint32 tipo = le32(v), misura = le32(v + 4), pos = le32(v + 8);
		guint32 dist = misura > FORMA_MISURA ? misura - FORMA_MISURA : FORMA_MISURA - misura;

		if (tipo != XCUR_IMMAGINE)
			continue;
		if (dist < scelta_dist) { /* ⚠ "<": at equal size the FIRST frame wins */
			scelta_dist = dist;
			scelta_pos = pos;
		}
	}
	if (scelta_dist == G_MAXUINT32 || scelta_pos > n || n - scelta_pos < XCUR_BLOCCO)
		return FALSE;
	d += scelta_pos;
	if (le32(d) != XCUR_BLOCCO || le32(d + 4) != XCUR_IMMAGINE)
		return FALSE;
	l = le32(d + 16);
	a = le32(d + 20);
	hx = le32(d + 24);
	hy = le32(d + 28);
	if (l == 0 || a == 0 || l > XCUR_LATO_MAX || a > XCUR_LATO_MAX ||
	    (n - scelta_pos - XCUR_BLOCCO) / 4u / l < a)
		return FALSE;

	/* ⛔ RCP §7.2: beyond 256 the receiver closes.  The top-left corner is
	 *    cut out, as `cursore.c` does — and with FORMA_MISURA 24 it never triggers. */
	lt = MIN(l, (guint32) CURSORE_MAX_LATO);
	at = MIN(a, (guint32) CURSORE_MAX_LATO);
	out->pixel = g_malloc((gsize) lt * at * 4u);
	/* ⭐ Xcursor pixels are premultiplied ARGB in little-endian integers:
	 *    in memory they are ALREADY the bytes B, G, R, A the wire wants. */
	for (guint32 y = 0; y < at; y++)
		memcpy(out->pixel + (gsize) y * lt * 4u, d + XCUR_BLOCCO + (gsize) y * l * 4u,
		       (gsize) lt * 4u);
	out->larghezza = (uint16_t) lt;
	out->altezza = (uint16_t) at;
	/* ⛔ The hotspot INSIDE the image (RCP §5.5), or the receiver closes. */
	out->attivo_x = (int16_t) MIN(hx, lt - 1u);
	out->attivo_y = (int16_t) MIN(hy, at - 1u);
	out->pronta = TRUE;
	return TRUE;
}

/*
 * A real theme is good if its `index.theme` really is a theme index
 * and the `cursors` folder is there.  ⛔ "The file is there" is not enough: a corrupt
 * index is a half-installed theme, and its cursors are not taken
 * (the bench injects it).
 */
static char *tema_buono(const char *radice, const char *tema)
{
	g_autofree char *indice = g_build_filename(radice, tema, "index.theme", NULL);
	g_autofree char *testo = NULL;
	char *cursori = g_build_filename(radice, tema, "cursors", NULL);

	if (!g_file_get_contents(indice, &testo, NULL, NULL) ||
	    !g_str_has_prefix(testo, "[Icon Theme]") ||
	    !g_file_test(cursori, G_FILE_TEST_IS_DIR)) {
		g_free(cursori);
		return NULL;
	}
	return cursori;
}

static gboolean prova_nome(const char *cartella, const char *nome, Immagine *out)
{
	g_autofree char *p = g_build_filename(cartella, nome, NULL);

	if (!leggi_xcursor(p, out))
		return FALSE;
	out->da = nome;
	return TRUE;
}

/*
 * ⛔ FIRST THE ALIASES IN THE SAME THEME, THEN THE OTHER THEME.  `[M]` 24 Sep 2026,
 *    on the KDE box: konsole asks for `size_hor`, which Adwaita lacks and
 *    `breeze_cursors` has.  With the loop "one name in every theme, then the alias"
 *    Breeze's arrow (32x32) arrived among Adwaita's shapes —
 *    two different drawings on the same desktop.  ⇒ The theme is the outer
 *    loop, and one theme falls back on the other only if no alias is there.
 */
static gboolean prova_voce(char **cartelle, const Voce *v, Immagine *out)
{
	for (int t = 0; cartelle[t]; t++) {
		if (prova_nome(cartelle[t], v->nome, out))
			return TRUE;
		for (int k = 0; k < 4 && v->alias[k]; k++)
			if (prova_nome(cartelle[t], v->alias[k], out))
				return TRUE;
	}
	for (int t = 0; cartelle[t]; t++)
		for (unsigned k = 0; k < G_N_ELEMENTS(ULTIMI); k++)
			if (prova_nome(cartelle[t], ULTIMI[k], out))
				return TRUE;
	return FALSE;
}

/* Loads the FORMA_QUANTE images ONCE.  Called with the lock held. */
static void carica(void)
{
	const char *radice = cartella_temi ? cartella_temi : "/usr/share/icons";
	char *cartelle[G_N_ELEMENTS(TEMI_REALI) + 1] = { NULL };
	int quanti_temi = 0, pronte = 0;

	caricato = TRUE;
	for (unsigned t = 0; t < G_N_ELEMENTS(TEMI_REALI); t++) {
		char *c = tema_buono(radice, TEMI_REALI[t]);

		if (c)
			cartelle[quanti_temi++] = c;
	}
	if (quanti_temi == 0) {
		if (!detto_assente) {
			detto_assente = TRUE;
			registro_dice(AREA,
			              "⛔ no readable real cursor theme in %s (Adwaita, "
			              "breeze_cursors; index missing or corrupt): shapes are NOT "
			              "sent, and the client keeps its own arrow",
			              radice);
		}
		return;
	}
	for (int i = 0; i < FORMA_QUANTE; i++) {
		if (prova_voce(cartelle, &VOCI[i], &immagini[i]))
			pronte++;
	}
	registro_dice(AREA, "⭐ cursor dictionary: %d shapes of %d from the real theme in %s "
	              "(first: %s, nominal size %d)",
	              pronte, FORMA_QUANTE, radice, cartelle[0], FORMA_MISURA);
	for (int t = 0; t < quanti_temi; t++)
		g_free(cartelle[t]);
}

gboolean forma_immagine(int indice, CursoreForma *out)
{
	Immagine *im;
	gboolean esito;

	if (indice < 0 || indice >= FORMA_QUANTE || !out)
		return FALSE;
	g_mutex_lock(&chiave);
	if (!caricato)
		carica();
	im = &immagini[indice];
	esito = im->pronta;
	if (esito) {
		out->larghezza = im->larghezza;
		out->altezza = im->altezza;
		out->attivo_x = im->attivo_x;
		out->attivo_y = im->attivo_y;
		out->immagine = im->pixel;
	}
	g_mutex_unlock(&chiave);
	return esito;
}

void forma_prova_cartella_temi(const char *cartella)
{
	g_mutex_lock(&chiave);
	for (int i = 0; i < FORMA_QUANTE; i++)
		g_free(immagini[i].pixel);
	memset(immagini, 0, sizeof immagini);
	g_free(cartella_temi);
	cartella_temi = g_strdup(cartella);
	caricato = FALSE;
	detto_assente = FALSE;
	g_mutex_unlock(&chiave);
}
