/*
 * colori709.h — da BGRx (o RGBx) a YUV 4:2:0 BT.709 a intervallo LIMITATO, senza
 *               libswscale.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE — fase 18 (`fasi/18-senza-ffmpeg.md`, `DECISIONI.md` §10.25)
 *
 * Fino alla fase 17 la conversione la faceva `sws_scale` (`prepara_fotogramma()`
 * in `codificatore.c`) con la matrice IMPOSTA: `sws_setColorspaceDetails(
 * SWS_CS_ITU709)`, sorgente a intervallo pieno, uscita limitata.  Togliendo
 * ffmpeg se ne va anche libswscale, e la conversione va rifatta **identica**:
 * due matrici diverse ai due capi misurerebbero la matrice, non l'immagine
 * (`codificatore.c`, il riquadro «IL COLORE SI DICHIARA»).
 *
 * ⛔⛔ E NON E' libyuv, e la ragione e' una riga del suo `convert_from_argb.h`
 *      `[M]` 30 settembre 2026, libyuv 0.0.1904 (Debian trixie): da ARGB verso
 *      4:2:0 esistono **solo** `ARGBToI420` (**BT.601** limitato) e
 *      `ARGBToJ420` (JPEG, BT.601 **pieno**).  Nessuna delle due e' la nostra:
 *      usarne una vorrebbe dire cambiare i colori del prodotto senza un errore
 *      da nessuna parte.  ⇒ Codice nostro, ~200 righe, e nessuna dipendenza in
 *      piu' da far trovare all'installatore su sette distribuzioni.
 *
 * ---------------------------------------------------------------------------
 * ⭐ LE REGOLE CHE RIPRODUCE, e ognuna ha la sua misura nel banco
 *    `banchi/18-software-confronto.c`:
 *
 *   - la matrice: Kr = 0,2126 · Kb = 0,0722 (BT.709), RGB a intervallo pieno
 *     (0-255) → Y 16-235, Cb/Cr 16-240 (a 10 bit: 64-940, 64-960);
 *   - il croma a meta' in tutt'e due i versi, **media dei quattro pixel** del
 *     quadrato 2x2 fatta in RGB e poi convertita — la stessa cosa che fa
 *     swscale in orizzontale (`rgb32ToUV_half`) e quasi la stessa in
 *     verticale (vedi il riquadro in `colori709.c`);
 *   - l'arrotondamento al piu' vicino, senza retinatura.
 *
 * ⚠ Le misure devono essere PARI (4:2:0): la guardia sta in `codificatore.c`
 *   e qui si ripete, perche' una larghezza dispari leggerebbe fuori dalla riga.
 */
#ifndef REMOTIX_COLORI709_H
#define REMOTIX_COLORI709_H

#include <stdbool.h>
#include <stdint.h>

/* Quale byte e' il rosso: BGRx (GNOME, KDE, …) o RGBx (labwc, fase 13). */
typedef enum {
	COLORI709_BGRX,
	COLORI709_RGBX,
} Colori709Ordine;

/* ⭐ 8 bit, tre piani (I420 / `yuv420p`): per OpenH264 e per SVT-AV1 a 8 bit.
 *    Torna false solo se le misure non sono pari o i puntatori mancano. */
bool colori709_a_i420(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint8_t *y, uint32_t passo_y,
                      uint8_t *u, uint32_t passo_u,
                      uint8_t *v, uint32_t passo_v);

/* ⭐ 10 bit, tre piani da 16 bit (`yuv420p10le`): per SVT-AV1 a 10 bit.  ⚠ Sono
 *    8 bit PROMOSSI con la matrice calcolata a 10 bit, non 8 bit spostati di
 *    due: e' quel che faceva swscale verso `yuv420p10le`.  I passi sono in
 *    BYTE, come quelli di libavutil. */
bool colori709_a_i420_10(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                         uint32_t altezza, Colori709Ordine ordine,
                         uint16_t *y, uint32_t passo_y,
                         uint16_t *u, uint32_t passo_u,
                         uint16_t *v, uint32_t passo_v);

/* ⭐ 8 bit semi-planare (NV12): per la strada della scheda quando la copia zero
 *    non c'e' e il fotogramma sale dalla memoria (`c->appoggio` in
 *    `codificatore.c`), che oggi passa da swscale verso NV12. */
bool colori709_a_nv12(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint8_t *y, uint32_t passo_y,
                      uint8_t *uv, uint32_t passo_uv);

/* ⭐ 10 bit semi-planare (P010: i dieci bit nei bit ALTI di sedici). */
bool colori709_a_p010(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint16_t *y, uint32_t passo_y,
                      uint16_t *uv, uint32_t passo_uv);

#endif
