/*
 * scrittore_bit.h — scrivere bit, un campo alla volta, come li vuole un
 * parameter set di H.264/H.265: `u(n)`, `ue(v)`, `se(v)`, i bit di coda, e il
 * NAL in Annex-B coi byte di emulazione al loro posto.
 *
 * ⭐ FASE 18 (30 set 2026, `DECISIONI.md` §10.25): nasce perche' le
 *    intestazioni del flusso (SPS/PPS/VPS/slice header) non le scrive piu'
 *    `libavcodec` (`cbs_h264`/`cbs_h265`): le scrive REMOTIX, e le passa al
 *    driver come «packed header».  E' lo specchio del LETTORE che
 *    `codificatore.c` ha dal 12 agosto 2026 (`LettoreBit`): quello rilegge i
 *    byte prodotti per la confessione, questo li produce.
 *
 * ⛔ Che cosa NON e': non conosce nessun codec.  Sa i bit, l'Exp-Golomb e la
 *    regola dei `00 00 03`.  Chi decide QUALI campi scrivere, e in che ordine,
 *    e' `vadiretta.c`, con lo standard accanto a ogni riga.
 */
#ifndef REMOTIX_SCRITTORE_BIT_H
#define REMOTIX_SCRITTORE_BIT_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
	uint8_t *dati;
	size_t capacita;   /* in byte */
	size_t bit;        /* posizione di scrittura, in bit */
	/* ⛔ Tre esiti, non due: un campo che non ci sta si RICORDA, e chi chiude
	 *    il NAL lo vede — un'intestazione tronca somiglia a un'intestazione. */
	bool traboccato;
} ScrittoreBit;

void sb_apri(ScrittoreBit *s, uint8_t *dati, size_t capacita);

/* `u(n)`: gli `n` bit bassi di `v`, dal piu' alto.  ⚠ `n` fino a 32. */
void sb_u(ScrittoreBit *s, int n, uint32_t v);
void sb_flag(ScrittoreBit *s, bool v);
/* Exp-Golomb senza segno (H.264 9.1 / H.265 9.2). */
void sb_ue(ScrittoreBit *s, uint32_t v);
/* Exp-Golomb con segno: k → (-1)^(k+1) · ceil(k/2), cioe' il rovescio di
 * `lb_se()` in `codificatore.c`. */
void sb_se(ScrittoreBit *s, int32_t v);

/* `rbsp_trailing_bits()`: un 1 e poi zeri fino al byte.  ⚠ E' anche il
 * `byte_alignment()` di H.265 (7.3.2.12): stessa forma, altro nome. */
void sb_chiudi_rbsp(ScrittoreBit *s);
/* `cabac_alignment_one_bit`: UNI fino al byte — la coda dello slice header di
 * H.264 quando l'entropia e' CABAC (7.3.4).  ⛔ Non zeri: sono uni. */
void sb_allinea_con_uni(ScrittoreBit *s);

/* Copia `quanti` bit da `sorgente` a partire dal bit `da`: serve alla cornice
 * di D-023, che riscrive la testa di un SPS e ricopia la coda tale e quale. */
void sb_copia_bit(ScrittoreBit *s, const uint8_t *sorgente, size_t da, size_t quanti);

/* Quanti byte occupano i bit scritti (arrotondati in su). */
size_t sb_byte(const ScrittoreBit *s);
bool sb_allineato(const ScrittoreBit *s);

/*
 * Un NAL in Annex-B: `00 00 00 01`, l'intestazione del NAL cosi' com'e', poi
 * l'RBSP coi byte di emulazione (`00 00 0x` con x <= 3 → `00 00 03 0x`).
 *
 * ⛔ L'intestazione del NAL (1 byte in H.264, 2 in H.265) si passa A PARTE e
 *    NON riceve emulazione: e' quel che fa anche `cbs_h2645`, e un lettore
 *    che trovasse un `03` dentro l'intestazione non saprebbe che farne.
 * Restituisce i byte scritti, o 0 se `fuori` non basta.
 */
size_t nal_annexb(uint8_t *fuori, size_t capacita, const uint8_t *intestazione,
                  size_t intestazione_byte, const uint8_t *rbsp, size_t rbsp_byte);

#endif
