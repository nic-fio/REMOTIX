/*
 * forma.c — il tema codificato e il dizionario.  Il perche' sta in `forma.h`,
 *           che si legge per primo.
 *
 * ⛔ DUE META' CHE DEVONO DIRE LA STESSA COSA: il tema lo scrive il SERVER
 *    (`sessione.c`, prima di accendere il desktop), il colore lo legge il FIGLIO
 *    (`cursore.c`, nel metadato).  ⇒ La tabella dei nomi e la formula dei
 *    colori stanno QUI e in nessun altro posto: e' lo stesso binario da tutte e
 *    due le parti, e un solo elenco non puo' divergere da se stesso.
 *
 * ⭐ Il parser Xcursor e' scritto qui e non preso da `libXcursor`: quella
 *    libreria porta dietro X11 intera, e il formato sono quattro tabelle di
 *    interi little-endian (`man 3 Xcursor`, «FILE FORMAT»).
 */
#include "forma.h"

#include "registro.h"

#include <glib/gstdio.h>
#include <stdlib.h>
#include <string.h>

#define AREA "forma"

/* I numeri del formato Xcursor 1.0. */
#define XCUR_MAGIA     0x72756358u /* «Xcur» */
#define XCUR_IMMAGINE  0xfffd0002u
#define XCUR_TESTA     16u
#define XCUR_BLOCCO    36u
#define XCUR_LATO_MAX  0x7fffu     /* il massimo che il formato ammette */

/* ⚠ Un tetto sul file PRIMA di leggerlo: un cursore vero di Adwaita pesa 78 KB
 *   (tutte le misure, fino a 96).  Oltre, non e' un cursore. */
#define FILE_MAX (8u * 1024u * 1024u)

/* ------------------------------------------------------------------ *
 *  I nomi, e gli alias con cui si cercano nel tema reale
 * ------------------------------------------------------------------ */

/*
 * ⛔ L'ORDINE E' IL CODICE: l'indice qui e' il colore nel tema.  Si AGGIUNGE in
 *    coda (e si alza FORMA_QUANTE), non si inserisce in mezzo — anche se
 *    server e figlio sono lo stesso binario, un banco o una copia vecchia del
 *    tema in `XDG_RUNTIME_DIR` leggerebbero colori spostati.
 *
 * I primi 68 sono i nomi che il tema invisibile aveva gia' (fase 12): quelli
 * che i programmi chiedono davvero, nomi CSS e nomi X11 insieme; gli altri
 * sono venuti dopo, in coda, ciascuno col suo perche'.
 *
 * ⭐ Gli alias: il nome che il programma chiede non e' sempre un file del tema
 *    reale (`[M]` Adwaita di Trixie ne ha 62, e mancano `ibeam`, `size_hor`,
 *    `pointing_hand`…).  Si prova il nome, poi gli alias in ordine, poi la
 *    freccia.  ⚠ `size_fdiag` e' la diagonale «\» (Qt `SizeFDiagCursor`),
 *    cioe' `nwse-resize`; `size_bdiag` la «/».
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
	 * ⭐ 24 set 2026, per labwc (XFCE e LXQt) — AGGIUNTE IN CODA, e il perche'.
	 *
	 * ⛔ `[M]` labwc 0.8.3 porta nel binario DUE serie di nomi per i suoi
	 *    bordi: quella CSS (`n-resize`, `ne-resize`… `w-resize`, piu' `grab`)
	 *    e quella X11 (`top_side`, `top_right_corner`… `left_side`, piu'
	 *    `grabbing`).  Sceglie la CSS se il tema ha le sue forme — e il
	 *    nostro ha `grab` e `default`: `[M]` 24 set 2026 su rete14-lxqt, il
	 *    bordo destro di qterminal arriva come «e-resize» (indice 68), non
	 *    come `right_side`.  ⇒ Senza queste otto il bordo chiedeva
	 *    un nome che il tema non aveva: nessun pixel colorato sotto il
	 *    puntatore, e la sonda (`wlroots.c`) non poteva riconoscere niente.
	 * ⭐ Le stesse otto sono anche i nomi che wlroots da' alle forme di
	 *   `cursor-shape-v1` (`wlr_cursor_shape_v1_name`), cioe' quel che chiede
	 *   ogni client che usa quel protocollo invece del suo tema.
	 * ⚠ `dnd-ask` e `all-resize` sono le due forme della v2 di
	 *   `cursor-shape-v1`: wlroots 0.18 non le annuncia, ma un nome in piu' nel
	 *   tema costa 68 byte, e un nome che manca costa la forma.
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

/* Se nemmeno un alias c'e': la freccia, che e' meglio di niente — il cliente
 * vedrebbe comunque una freccia, la sua. */
static const char *ULTIMI[] = { "default", "left_ptr" };

/* ⭐ I temi reali, in ordine.  ⚠ `[M]` 24 set 2026: Adwaita (62 cursori) c'e'
 *   in TUTTE e quattro le scatole `rete11-*`; `breeze_cursors` solo in KDE. */
static const char *TEMI_REALI[] = { "Adwaita", "breeze_cursors" };

/* ------------------------------------------------------------------ *
 *  I colori
 * ------------------------------------------------------------------ */

/*
 * ⭐ Indice ⇒ colore.  ⛔ Il rosso da solo basta a distinguerli (0x40 + i e'
 *    diverso per ogni i < FORMA_QUANTE), e sta fra 0x40 e 0x8D: lontano dal nero e dal
 *    bianco, che sono i colori di cui sono fatti i cursori veri — nessun
 *    cursore vero di un solo colore puo' essere scambiato per uno dei nostri.
 *    Verde e blu sono il controllo: un pixel col rosso giusto e il resto a caso
 *    NON e' nostro.  Il banco (`banchi/14-f1-forma.sh`) li verifica tutti.
 *    ⚠ Il tetto: fino a 128 forme il rosso resta <= 0xBF, lontano dal
 *      bianco; oltre, la regola va ripensata prima di aggiungere.
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

	/* ⛔ Opaco o niente: il tema e' opaco, e il metadato e' premoltiplicato —
	 *    un'alfa minore vorrebbe dire colori gia' schiacciati, cioe' un
	 *    indice sbagliato con l'aria di uno giusto. */
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
 *  Il tema codificato (lo scrive il server)
 * ------------------------------------------------------------------ */

/* Un cursore Xcursor 1.0 con UNA immagine 1x1: l'intestazione di
 * `scrivi_cursore_vuoto` della fase 12, con il pixel che ora ha un colore. */
static gboolean scrivi_cursore_colorato(const char *percorso, int i)
{
	uint8_t r, g, b;
	guint32 argb;

	colore(i, &r, &g, &b);
	argb = 0xFF000000u | ((guint32) r << 16) | ((guint32) g << 8) | (guint32) b;
	{
		guint32 dati[] = {
			GUINT32_TO_LE(XCUR_MAGIA),
			GUINT32_TO_LE(XCUR_TESTA),  /* quanto e' lunga l'intestazione */
			GUINT32_TO_LE(0x00010000u), /* versione 1.0 */
			GUINT32_TO_LE(1u),          /* un solo elemento nell'indice */
			GUINT32_TO_LE(XCUR_IMMAGINE), GUINT32_TO_LE((guint32) FORMA_MISURA),
			GUINT32_TO_LE(28u),         /* dove comincia il blocco */
			GUINT32_TO_LE(XCUR_BLOCCO), /* lunghezza dell'intestazione del blocco */
			GUINT32_TO_LE(XCUR_IMMAGINE),
			GUINT32_TO_LE((guint32) FORMA_MISURA), /* misura nominale */
			GUINT32_TO_LE(1u),          /* versione del blocco */
			GUINT32_TO_LE(1u),          /* larghezza */
			GUINT32_TO_LE(1u),          /* altezza */
			GUINT32_TO_LE(0u),          /* punto caldo x */
			GUINT32_TO_LE(0u),          /* punto caldo y */
			GUINT32_TO_LE(0u),          /* ritardo, per le animazioni */
			GUINT32_TO_LE(argb),        /* l'unico pixel: OPACO, e del suo colore */
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
	/* ⚠ Niente `Inherits=`: ereditare da un tema vero rimetterebbe nell'immagine
	 *   il cursore VERO per ogni forma che qui non c'e' — e ⛔ quello non
	 *   porterebbe un colore nostro, il dizionario non lo riconoscerebbe. */
	if (!g_file_set_contents(indice,
	                         "[Icon Theme]\n"
	                         "Name=REMOTIX (codificato)\n"
	                         "Comment=Ogni forma e' un pixel opaco di un colore suo: "
	                         "il server lo legge e manda al client la forma vera\n",
	                         -1, NULL)) {
		registro_dice(AREA, "⚠ tema del cursore NON scritto in %s", tema);
		return FALSE;
	}
	for (int i = 0; i < FORMA_QUANTE; i++) {
		g_autofree char *percorso = g_build_filename(cursori, VOCI[i].nome, NULL);

		if (scrivi_cursore_colorato(percorso, i))
			scritte++;
	}
	if (scritte == 0) {
		registro_dice(AREA, "⚠ nessuna forma del cursore scritta in %s", tema);
		return FALSE;
	}
	registro_dice(AREA, "⭐ tema «%s»: %u forme su %d, ciascuna un pixel opaco di un colore "
	              "suo, in %s",
	              FORMA_TEMA, scritte, FORMA_QUANTE, tema);
	return TRUE;
}

/* ------------------------------------------------------------------ *
 *  Il dizionario: le immagini vere, dal tema reale (le legge il figlio)
 * ------------------------------------------------------------------ */

typedef struct {
	gboolean pronta;
	uint16_t larghezza, altezza;
	int16_t attivo_x, attivo_y;
	uint8_t *pixel; /* BGRA premoltiplicato, vive per tutto il processo */
	const char *da; /* il nome del file da cui e' venuta (per il registro) */
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
 * Un file Xcursor ⇒ la prima immagine della misura nominale piu' vicina a
 * FORMA_MISURA.  ⛔ Ogni lunghezza si controlla PRIMA di usarla: il file e'
 * di un altro pacchetto, e un file troncato non deve diventare memoria letta
 * fuori dal secchio.  ⚠ Delle animazioni (`wait`, `progress`) si prende il
 * primo fotogramma: il filo porta un'immagine sola.
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
		if (dist < scelta_dist) { /* ⚠ «<»: a pari misura vince il PRIMO fotogramma */
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

	/* ⛔ RCP §7.2: oltre 256 il ricevente chiude.  Si taglia l'angolo in alto a
	 *    sinistra, come fa `cursore.c` — e con FORMA_MISURA 24 non scatta. */
	lt = MIN(l, (guint32) CURSORE_MAX_LATO);
	at = MIN(a, (guint32) CURSORE_MAX_LATO);
	out->pixel = g_malloc((gsize) lt * at * 4u);
	/* ⭐ I pixel Xcursor sono ARGB premoltiplicato in interi little-endian:
	 *    in memoria sono GIA' i byte B, G, R, A che il filo vuole. */
	for (guint32 y = 0; y < at; y++)
		memcpy(out->pixel + (gsize) y * lt * 4u, d + XCUR_BLOCCO + (gsize) y * l * 4u,
		       (gsize) lt * 4u);
	out->larghezza = (uint16_t) lt;
	out->altezza = (uint16_t) at;
	/* ⛔ Il punto attivo DENTRO l'immagine (RCP §5.5), o il ricevente chiude. */
	out->attivo_x = (int16_t) MIN(hx, lt - 1u);
	out->attivo_y = (int16_t) MIN(hy, at - 1u);
	out->pronta = TRUE;
	return TRUE;
}

/*
 * Un tema reale e' buono se il suo `index.theme` e' davvero un indice di tema
 * e la cartella `cursors` c'e'.  ⛔ «Il file c'e'» non basta: un indice
 * corrotto e' un tema installato a meta', e i suoi cursori non si prendono
 * (il banco lo innesta).
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
 * ⛔ PRIMA GLI ALIAS NELLO STESSO TEMA, POI L'ALTRO TEMA.  `[M]` 24 set 2026,
 *    sulla scatola KDE: konsole chiede `size_hor`, che Adwaita non ha e
 *    `breeze_cursors` si'.  Col giro «un nome in tutti i temi, poi l'alias»
 *    arrivava la freccia di Breeze (32x32) in mezzo alle forme di Adwaita —
 *    due disegni diversi nello stesso desktop.  ⇒ Il tema e' il giro di
 *    fuori, e un tema ripiega sull'altro solo se nessun alias c'e'.
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

/* Carica le FORMA_QUANTE immagini UNA volta.  Chiamata con la chiave presa. */
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
			              "⛔ nessun tema reale del cursore leggibile in %s (Adwaita, "
			              "breeze_cursors; indice assente o corrotto): le forme NON si "
			              "mandano, e il client tiene la sua freccia",
			              radice);
		}
		return;
	}
	for (int i = 0; i < FORMA_QUANTE; i++) {
		if (prova_voce(cartelle, &VOCI[i], &immagini[i]))
			pronte++;
	}
	registro_dice(AREA, "⭐ dizionario del cursore: %d forme su %d dal tema reale in %s "
	              "(primo: %s, misura nominale %d)",
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
