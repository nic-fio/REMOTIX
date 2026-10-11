/*
 * 18-software-openh264-vuota.c — an EMPTY copy of OpenH264, to prove that
 * the fallback recognises it (phase 18).  It mimics `noopenh264` of Fedora/EPEL/
 * openSUSE: same names, no encoding.
 *
 *   gcc -shared -fPIC -o libopenh264.so.8 18-software-openh264-vuota.c
 *   LD_LIBRARY_PATH=. ./18-software-confronto refusals
 *
 * EMPTY=1 (default): WelsCreateSVCEncoder fails.  EMPTY=0: the symbols are missing.
 */
#include <stddef.h>

typedef struct {
	unsigned int uMajor, uMinor, uRevision, uReserved;
} Ver;

#ifndef EMPTY
#define EMPTY 1
#endif

#if EMPTY
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
void WelsGetCodecVersionEx(Ver *v)
{
	v->uMajor = 2;
	v->uMinor = 6;
	v->uRevision = 0;
	v->uReserved = 0;
}
