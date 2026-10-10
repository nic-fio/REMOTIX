/*
 * scrittore_bit.c — see `scrittore_bit.h`.  No codec in here: only bits,
 * Exp-Golomb and the emulation prevention byte rule.
 */
#include "scrittore_bit.h"

#include <string.h>

void sb_apri(ScrittoreBit *s, uint8_t *dati, size_t capacita)
{
	s->dati = dati;
	s->capacita = capacita;
	s->bit = 0;
	s->traboccato = false;
	if (dati && capacita)
		memset(dati, 0, capacita);
}

static void sb_bit(ScrittoreBit *s, unsigned v)
{
	size_t indice = s->bit >> 3;

	if (indice >= s->capacita) {
		s->traboccato = true;
		return;
	}
	if (v)
		s->dati[indice] |= (uint8_t) (0x80u >> (s->bit & 7));
	s->bit++;
}

void sb_u(ScrittoreBit *s, int n, uint32_t v)
{
	for (int i = n - 1; i >= 0; i--)
		sb_bit(s, (v >> i) & 1u);
}

void sb_flag(ScrittoreBit *s, bool v)
{
	sb_bit(s, v ? 1u : 0u);
}

void sb_ue(ScrittoreBit *s, uint32_t v)
{
	/* codeNum v → (v+1) written with 2·len+1 bits, where len = floor(log2(v+1)):
	 * `len` zeros, then the len+1 bits of (v+1).  ⚠ `v+1` can overflow 32 bits
	 * only for v = 2^32-1, which none of our fields reaches. */
	uint64_t x = (uint64_t) v + 1u;
	int lunghezza = 0;

	while ((x >> (lunghezza + 1)) != 0)
		lunghezza++;
	for (int i = 0; i < lunghezza; i++)
		sb_bit(s, 0);
	for (int i = lunghezza; i >= 0; i--)
		sb_bit(s, (unsigned) ((x >> i) & 1u));
}

void sb_se(ScrittoreBit *s, int32_t v)
{
	/* H.264 9.1.1, table 9-3: v > 0 → k = 2v-1 · v <= 0 → k = -2v. */
	if (v > 0)
		sb_ue(s, 2u * (uint32_t) v - 1u);
	else
		sb_ue(s, 2u * (uint32_t) (-(int64_t) v));
}

void sb_chiudi_rbsp(ScrittoreBit *s)
{
	sb_bit(s, 1);
	while (s->bit & 7)
		sb_bit(s, 0);
}

void sb_allinea_con_uni(ScrittoreBit *s)
{
	while (s->bit & 7)
		sb_bit(s, 1);
}

void sb_copia_bit(ScrittoreBit *s, const uint8_t *sorgente, size_t da, size_t quanti)
{
	for (size_t i = 0; i < quanti; i++) {
		size_t b = da + i;
		sb_bit(s, (sorgente[b >> 3] >> (7 - (b & 7))) & 1u);
	}
}

size_t sb_byte(const ScrittoreBit *s)
{
	return (s->bit + 7) >> 3;
}

bool sb_allineato(const ScrittoreBit *s)
{
	return (s->bit & 7) == 0;
}

size_t nal_annexb(uint8_t *fuori, size_t capacita, const uint8_t *intestazione,
                  size_t intestazione_byte, const uint8_t *rbsp, size_t rbsp_byte)
{
	size_t n = 0, zeri = 0;

	if (capacita < 4 + intestazione_byte)
		return 0;
	fuori[n++] = 0;
	fuori[n++] = 0;
	fuori[n++] = 0;
	fuori[n++] = 1;
	memcpy(fuori + n, intestazione, intestazione_byte);
	n += intestazione_byte;
	/*
	 * H.264 7.4.1 / H.265 7.4.2: inside the payload the sequence `00 00 0x` with
	 * x in {0,1,2,3} must not appear — a `03` is slipped in.  ⛔ And the zero
	 * count restarts AFTER the emulation prevention byte, not after the byte
	 * that asked for it: `00 00 00 00` becomes `00 00 03 00 00`, and the third
	 * zero starts a new count.
	 */
	for (size_t i = 0; i < rbsp_byte; i++) {
		if (zeri >= 2 && rbsp[i] <= 3) {
			if (n >= capacita)
				return 0;
			fuori[n++] = 3;
			zeri = 0;
		}
		if (n >= capacita)
			return 0;
		fuori[n++] = rbsp[i];
		zeri = (rbsp[i] == 0) ? zeri + 1 : 0;
	}
	return n;
}
