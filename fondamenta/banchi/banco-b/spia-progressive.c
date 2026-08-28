/*
 * spia-progressive — controprova della misura A.
 *
 * Intercetta progressive_decompress in un client FreeRDP: se scatta, il server
 * sta mandando RemoteFX Progressive su EGFX.  Serve a certificare che il banco
 * emetta davvero quel codec PRIMA di chiedere all'utente di collegare il
 * telefono: senza questa verifica, un eventuale schermo nero su RDM non si
 * saprebbe se attribuire al client o al banco.
 *
 *   gcc -shared -fPIC -o spia-progressive.so spia-progressive.c -ldl
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef int32_t (*progressive_decompress_t)(void* progressive, const uint8_t* pSrcData,
                                            uint32_t SrcSize, uint8_t* pDstData, uint32_t DstFormat,
                                            uint32_t nDstStep, uint32_t nXDst, uint32_t nYDst,
                                            void* invalidRegion, uint16_t surfaceId,
                                            uint32_t frameId);

static FILE* apri_registro(void)
{
	static FILE* f;
	if (!f)
	{
		const char* percorso = getenv("SPIA_PROGRESSIVE");
		f = percorso ? fopen(percorso, "we") : NULL;
		if (!f)
			f = stderr;
		setvbuf(f, NULL, _IOLBF, 0);
	}
	return f;
}

int32_t progressive_decompress(void* progressive, const uint8_t* pSrcData, uint32_t SrcSize,
                               uint8_t* pDstData, uint32_t DstFormat, uint32_t nDstStep,
                               uint32_t nXDst, uint32_t nYDst, void* invalidRegion,
                               uint16_t surfaceId, uint32_t frameId)
{
	static progressive_decompress_t vero;
	static unsigned long conteggio;

	if (!vero)
		vero = (progressive_decompress_t)dlsym(RTLD_NEXT, "progressive_decompress");

	int32_t esito = vero ? vero(progressive, pSrcData, SrcSize, pDstData, DstFormat, nDstStep, nXDst,
	                            nYDst, invalidRegion, surfaceId, frameId)
	                     : -1;

	fprintf(apri_registro(),
	        "RFX PROGRESSIVE  n.%lu  superficie=%u fotogramma=%u  byte=%u  a (%u,%u)  esito=%d\n",
	        ++conteggio, surfaceId, frameId, SrcSize, nXDst, nYDst, esito);
	return esito;
}
