#include "immagine.h"

#include <string.h>

/* R4: larghezza multipla di 16, altezza multipla di 64. */
#define ALLINEA(v, a) (((v) % (a)) ? ((v) + (a) - ((v) % (a))) : (v))

struct Immagine
{
	uint32_t larghezza, altezza;             /* la misura vera, quella del desktop */
	uint32_t larghezza_all, altezza_all;     /* la misura allineata del buffer     */
	uint32_t passo;
	uint8_t *pixel;
};

/*
 * Un alfabeto minimo 5x7, sufficiente per cifre, due punti, punto e le lettere
 * che servono alle etichette.  Sta qui invece di tirarsi dietro una libreria di
 * font: la scena e' uno strumento di misura, non un'interfaccia.
 */
#define GLIFO_L 5
#define GLIFO_A 7

static const struct
{
	char c;
	uint8_t righe[GLIFO_A];
} alfabeto[] = {
	{ '0', { 0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E } },
	{ '1', { 0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E } },
	{ '2', { 0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F } },
	{ '3', { 0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E } },
	{ '4', { 0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02 } },
	{ '5', { 0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E } },
	{ '6', { 0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E } },
	{ '7', { 0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08 } },
	{ '8', { 0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E } },
	{ '9', { 0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C } },
	{ ':', { 0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00 } },
	{ '.', { 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C } },
	{ ',', { 0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08 } },
	{ '-', { 0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00 } },
	{ 'x', { 0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11 } },
	{ 'R', { 0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11 } },
	{ 'E', { 0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F } },
	{ 'M', { 0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11 } },
	{ 'O', { 0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E } },
	{ 'T', { 0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04 } },
	{ 'I', { 0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E } },
	{ 'X', { 0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11 } },
	{ ' ', { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 } },
};

static inline void punto(Immagine *im, int64_t x, int64_t y, uint32_t colore)
{
	if (x < 0 || y < 0 || (uint32_t) x >= im->larghezza || (uint32_t) y >= im->altezza)
		return;
	*(uint32_t *) (im->pixel + (size_t) y * im->passo + (size_t) x * 4) = colore;
}

static void riempi(Immagine *im, int64_t x, int64_t y, int64_t l, int64_t a, uint32_t colore)
{
	for (int64_t j = y; j < y + a; j++)
		for (int64_t i = x; i < x + l; i++)
			punto(im, i, j, colore);
}

static void glifo(Immagine *im, char c, int64_t x, int64_t y, uint32_t scala, uint32_t colore)
{
	const uint8_t *righe = NULL;

	for (gsize k = 0; k < G_N_ELEMENTS(alfabeto); k++)
	{
		if (alfabeto[k].c == c)
		{
			righe = alfabeto[k].righe;
			break;
		}
	}
	if (!righe)
		return;

	for (uint32_t r = 0; r < GLIFO_A; r++)
		for (uint32_t c2 = 0; c2 < GLIFO_L; c2++)
			if (righe[r] & (1u << (GLIFO_L - 1 - c2)))
				riempi(im, x + (int64_t) c2 * scala, y + (int64_t) r * scala, scala, scala, colore);
}

static void scritta(Immagine *im, const char *testo, int64_t x, int64_t y, uint32_t scala,
                    uint32_t colore)
{
	for (const char *p = testo; *p; p++)
	{
		glifo(im, *p, x, y, scala, colore);
		x += (int64_t) (GLIFO_L + 1) * scala;
	}
}

uint32_t immagine_allinea_larghezza(uint32_t larghezza)
{
	return ALLINEA(larghezza, 16);
}

uint32_t immagine_allinea_altezza(uint32_t altezza)
{
	return ALLINEA(altezza, 64);
}

Immagine *immagine_nuova(uint32_t larghezza, uint32_t altezza)
{
	Immagine *im = g_new0(Immagine, 1);

	im->larghezza = larghezza;
	im->altezza = altezza;
	im->larghezza_all = immagine_allinea_larghezza(larghezza);
	im->altezza_all = immagine_allinea_altezza(altezza);
	im->passo = im->larghezza_all * 4;
	im->pixel = g_malloc0((size_t) im->passo * im->altezza_all);
	return im;
}

void immagine_libera(Immagine *im)
{
	if (!im)
		return;
	g_free(im->pixel);
	g_free(im);
}

/*
 * Il bordo di allineamento si RIEMPIE, non si taglia (R4).  Si replica
 * l'ultima colonna e l'ultima riga invece di lasciare nero: un salto netto sul
 * bordo costa bit al codificatore e non serve a nessuno, visto che quei pixel
 * il client non li mostra.
 */
static void riempi_bordo_allineamento(Immagine *im)
{
	for (uint32_t y = 0; y < im->altezza; y++)
	{
		uint8_t *riga = im->pixel + (size_t) y * im->passo;
		uint32_t ultimo = *(uint32_t *) (riga + (size_t) (im->larghezza - 1) * 4);
		for (uint32_t x = im->larghezza; x < im->larghezza_all; x++)
			*(uint32_t *) (riga + (size_t) x * 4) = ultimo;
	}
	const uint8_t *ultima = im->pixel + (size_t) (im->altezza - 1) * im->passo;
	for (uint32_t y = im->altezza; y < im->altezza_all; y++)
		memcpy(im->pixel + (size_t) y * im->passo, ultima, im->passo);
}

void immagine_disegna(Immagine *im, int64_t millisecondi)
{
	const uint32_t L = im->larghezza, A = im->altezza;
	char testo[64];

	/* fondo */
	for (uint32_t y = 0; y < A; y++)
	{
		uint8_t *riga = im->pixel + (size_t) y * im->passo;
		for (uint32_t x = 0; x < L; x++)
			*(uint32_t *) (riga + (size_t) x * 4) = 0x00101418;
	}

	/* barre di colore, in alto */
	{
		static const uint32_t barre[] = { 0x00FFFFFF, 0x00FFFF00, 0x0000FFFF, 0x0000FF00,
			                              0x00FF00FF, 0x00FF0000, 0x000000FF, 0x00000000 };
		uint32_t altezza_barre = A / 8;
		for (gsize b = 0; b < G_N_ELEMENTS(barre); b++)
		{
			uint32_t x0 = (uint32_t) (b * L / G_N_ELEMENTS(barre));
			uint32_t x1 = (uint32_t) ((b + 1) * L / G_N_ELEMENTS(barre));
			riempi(im, x0, 0, x1 - x0, altezza_barre, barre[b]);
		}
	}

	/* griglia da 100 px con le coordinate: dice se la scala e' giusta */
	for (uint32_t x = 100; x < L; x += 100)
	{
		riempi(im, x, 0, 1, A, 0x00303840);
		g_snprintf(testo, sizeof testo, "%u", x);
		scritta(im, testo, x + 3, A / 8 + 4, 1, 0x00808890);
	}
	for (uint32_t y = 100; y < A; y += 100)
	{
		riempi(im, 0, y, L, 1, 0x00303840);
		g_snprintf(testo, sizeof testo, "%u", y);
		scritta(im, testo, 3, y + 3, 1, 0x00808890);
	}

	/*
	 * La cornice di un pixel sui bordi ESATTI.  E' il controllo di geometria
	 * piu' importante della scena: se manca un lato, l'immagine e' spostata o
	 * tagliata, ed e' la firma di §8.3 (ResetGraphics con elenco monitor vuoto,
	 * oppure origine sbagliata di MapSurfaceToOutput).
	 */
	riempi(im, 0, 0, L, 1, 0x0000FF00);
	riempi(im, 0, (int64_t) A - 1, L, 1, 0x0000FF00);
	riempi(im, 0, 0, 1, A, 0x0000FF00);
	riempi(im, (int64_t) L - 1, 0, 1, A, 0x0000FF00);

	/* angoli etichettati con le proprie coordinate */
	scritta(im, "0,0", 4, 4, 2, 0x0000FF00);
	g_snprintf(testo, sizeof testo, "%ux%u", L, A);
	scritta(im, testo, (int64_t) L - (int64_t) strlen(testo) * 12 - 4, (int64_t) A - 18, 2,
	        0x0000FF00);

	/* orologio al millesimo, al centro: dice se i fotogrammi arrivano */
	{
		int64_t s = millisecondi / 1000;
		g_snprintf(testo, sizeof testo, "%02d:%02d:%02d.%03d", (int) (s / 3600 % 24),
		           (int) (s / 60 % 60), (int) (s % 60), (int) (millisecondi % 1000));
		uint32_t scala = L / 200 ? L / 200 : 1;
		int64_t larghezza_testo = (int64_t) strlen(testo) * (GLIFO_L + 1) * scala;
		scritta(im, testo, ((int64_t) L - larghezza_testo) / 2, (int64_t) A / 2 - 20, scala,
		        0x00FFFFFF);
		scritta(im, "REMOTIX", ((int64_t) L - 7 * (GLIFO_L + 1) * scala) / 2,
		        (int64_t) A / 2 - 20 - (int64_t) (GLIFO_A + 3) * scala, scala, 0x0060C0FF);
	}

	/* barra che scorre: si muove anche se l'orologio non si legge da lontano */
	{
		uint32_t larghezza_barra = L / 12 ? L / 12 : 8;
		int64_t x = (millisecondi / 4) % (L + larghezza_barra) - (int64_t) larghezza_barra;
		riempi(im, x, (int64_t) A - (int64_t) A / 10, larghezza_barra, A / 20, 0x00FFC000);
	}

	riempi_bordo_allineamento(im);
}

void immagine_copia_fotogramma(Immagine *im, const uint8_t *pixel, uint32_t passo,
                               uint32_t larghezza, uint32_t altezza)
{
	uint32_t righe = MIN(altezza, im->altezza);
	uint32_t colonne = MIN(larghezza, im->larghezza);
	size_t utili = (size_t) colonne * 4;
	const uint32_t grigio = 0x00303030;

	for (uint32_t y = 0; y < righe; y++)
		memcpy(im->pixel + (size_t) y * im->passo, pixel + (size_t) y * passo, utili);

	/* La parte che il fotogramma non copre: vedi la nota in immagine.h. */
	if (colonne < im->larghezza)
		riempi(im, colonne, 0, (int64_t) im->larghezza - colonne, righe, grigio);
	if (righe < im->altezza)
		riempi(im, 0, righe, im->larghezza, (int64_t) im->altezza - righe, grigio);

	riempi_bordo_allineamento(im);
}

const uint8_t *immagine_pixel(const Immagine *im)
{
	return im->pixel;
}
uint32_t immagine_passo(const Immagine *im)
{
	return im->passo;
}
uint32_t immagine_larghezza(const Immagine *im)
{
	return im->larghezza;
}
uint32_t immagine_altezza(const Immagine *im)
{
	return im->altezza;
}
uint32_t immagine_larghezza_allineata(const Immagine *im)
{
	return im->larghezza_all;
}
uint32_t immagine_altezza_allineata(const Immagine *im)
{
	return im->altezza_all;
}
