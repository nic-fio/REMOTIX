/*
 * spia-avc420 — microscopio per la misura B della fase 0.
 *
 * Si innesta con LD_PRELOAD in un client FreeRDP e intercetta
 * avc420_decompress, stampando i rettangoli della metablock AVC420 COSI' COME
 * ARRIVANO DAL FILO, insieme alla misura della superficie di destinazione.
 *
 * Perche' questo e non un analizzatore di pacchetti: fra i byte del filo e
 * questi valori c'e' un solo passaggio, rdpgfx_read_rect16, che legge quattro
 * UINT16 in fila e non applica alcun aggiustamento (verificato sul sorgente di
 * FreeRDP 3.22, channels/rdpgfx/rdpgfx_common.c).  Niente TLS da decifrare,
 * niente framing da ricostruire, nessun privilegio.
 *
 * La lettura si fa cosi': se il bordo destro di un rettangolo che copre tutto
 * lo schermo vale ESATTAMENTE la larghezza, i bordi sono esclusivi; se vale
 * larghezza-1, sono inclusivi.
 *
 *   gcc -shared -fPIC -o spia-avc420.so spia-avc420.c -ldl
 *   LD_PRELOAD=./spia-avc420.so SPIA_AVC420=/tmp/rect.txt xfreerdp3 ...
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct
{
	uint16_t left;
	uint16_t top;
	uint16_t right;
	uint16_t bottom;
} RECT16;

typedef int32_t (*avc420_decompress_t)(void* h264, const uint8_t* pSrcData, uint32_t SrcSize,
                                       uint8_t* pDstData, uint32_t DstFormat, uint32_t nDstStep,
                                       uint32_t nDstWidth, uint32_t nDstHeight,
                                       const RECT16* regionRects, uint32_t numRegionRects);

static FILE* apri_registro(void)
{
	static FILE* f;
	if (!f)
	{
		const char* percorso = getenv("SPIA_AVC420");
		f = percorso ? fopen(percorso, "we") : NULL;
		if (!f)
			f = stderr;
		setvbuf(f, NULL, _IOLBF, 0);
	}
	return f;
}

int32_t avc420_decompress(void* h264, const uint8_t* pSrcData, uint32_t SrcSize, uint8_t* pDstData,
                          uint32_t DstFormat, uint32_t nDstStep, uint32_t nDstWidth,
                          uint32_t nDstHeight, const RECT16* regionRects, uint32_t numRegionRects)
{
	static avc420_decompress_t vero;
	static unsigned long fotogramma;

	if (!vero)
		vero = (avc420_decompress_t)dlsym(RTLD_NEXT, "avc420_decompress");

	FILE* f = apri_registro();
	fprintf(f, "fotogramma %lu  superficie %ux%u  byte %u  rettangoli %u\n", ++fotogramma,
	        nDstWidth, nDstHeight, SrcSize, numRegionRects);

	for (uint32_t i = 0; i < numRegionRects && regionRects; i++)
	{
		const RECT16* r = &regionRects[i];
		fprintf(f, "   rect[%u]  left=%u top=%u right=%u bottom=%u   (right-left=%d, bottom-top=%d)",
		        i, r->left, r->top, r->right, r->bottom, (int)r->right - (int)r->left,
		        (int)r->bottom - (int)r->top);
		if (r->left == 0 && r->right == nDstWidth)
			fprintf(f, "   <-- right == larghezza: ESCLUSIVI");
		else if (r->left == 0 && r->right + 1 == nDstWidth)
			fprintf(f, "   <-- right == larghezza-1: INCLUSIVI");
		fprintf(f, "\n");
	}

	return vero ? vero(h264, pSrcData, SrcSize, pDstData, DstFormat, nDstStep, nDstWidth,
	                   nDstHeight, regionRects, numRegionRects)
	            : -1;
}
