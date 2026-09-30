/*
 * 18-software-openh264-vuota.c — una copia VUOTA di OpenH264, per provare che
 * il ripiego la riconosce (fase 18).  Imita `noopenh264` di Fedora/EPEL/
 * openSUSE: stessi nomi, nessuna codifica.
 *
 *   gcc -shared -fPIC -o libopenh264.so.8 18-software-openh264-vuota.c
 *   LD_LIBRARY_PATH=. ./18-software-confronto rifiuti
 *
 * VUOTA=1 (difetto): WelsCreateSVCEncoder fallisce.  VUOTA=0: mancano i simboli.
 */
#include <stddef.h>

typedef struct {
	unsigned int uMajor, uMinor, uRevision, uReserved;
} Versione;

#ifndef VUOTA
#define VUOTA 1
#endif

#if VUOTA
int WelsCreateSVCEncoder(void **p)
{
	if (p)
		*p = NULL;
	return 1;
}
void WelsDestroySVCEncoder(void *p)
{
	(void) p;
}
#endif
void WelsGetCodecVersionEx(Versione *v)
{
	v->uMajor = 2;
	v->uMinor = 6;
	v->uRevision = 0;
	v->uReserved = 0;
}
