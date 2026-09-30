/*
 * ripiego.h — la codifica IN SOFTWARE senza ffmpeg: H.264 con OpenH264, AV1
 *             con SVT-AV1 chiamata diretta, e i colori con `colori709.c`.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE — fase 18 (`fasi/18-senza-ffmpeg.md`, `DECISIONI.md` §10.22
 *    e §10.25): REMOTIX va sotto PolyForm Noncommercial, che non convive con la
 *    libavcodec GPL delle distribuzioni.  Il ripiego in software di oggi
 *    (`libx264`, `libx265`, `libsvtav1` via libavcodec, i colori via
 *    libswscale) esce, e al suo posto entrano librerie BSD:
 *
 *      H.264   OpenH264 (Cisco, BSD-2)       `WelsCreateSVCEncoder`
 *      AV1     SVT-AV1 (BSD-3-Clause-Clear)   `svt_av1_enc_*`
 *      HEVC    ⛔ NIENTE — x265 e' GPL, e un codificatore HEVC in software con
 *              licenza permissiva non c'e'.  Chi lo chiede riceve un errore
 *              DICHIARATO (`ripiego_apri()` torna NULL con la ragione), e chi
 *              chiama sceglie un altro codec: mai HEVC-software in silenzio.
 *
 * ---------------------------------------------------------------------------
 * ⭐ LA FORMA — piccola apposta, perche' `codificatore.c` la innesti al posto di
 *    `apri_contesto()`/`prepara_fotogramma()`/`avcodec_send_frame()` del solo
 *    ramo software, e tenga TUTTO il resto (il tetto dei 16 MiB, la scala della
 *    degradazione, la risalita, `forma_va_bene()`, la lettura dell'SPS):
 *
 *      apri → codifica* → [chiave | ridimensiona | qualita']* → chiudi
 *
 *   - l'uscita e' quella di oggi: **Annex B** per H.264 (SPS+PPS davanti a ogni
 *     IDR), **OBU** con temporal delimiter per AV1 (sequence header davanti a
 *     ogni chiave).  La pagina non cambia;
 *   - i byte restano di proprieta' del ripiego e valgono fino alla chiamata
 *     successiva (qualunque) o a `ripiego_chiudi()`: e' lo stesso contratto
 *     di `fuori->dati` in `codificatore.h`;
 *   - un fotogramma dentro, un fotogramma fuori: niente fotogrammi B, niente
 *     riordino, niente trattenuti.  ⛔ Se il codificatore ne trattiene uno lo si
 *     DICHIARA (`trattenuto`) come fa `comprimi_comune()` oggi.
 */
#ifndef REMOTIX_RIPIEGO_H
#define REMOTIX_RIPIEGO_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "codificatore.h" /* CodecVideo, ModoQualita, FormatoPixel, CodificatoreRichiesta */

typedef struct Ripiego Ripiego;

typedef struct {
	const uint8_t *dati;          /* Annex B (H.264) o OBU (AV1) */
	size_t byte;
	bool chiave;                  /* IDR (H.264) · KEY_FRAME (AV1), detto dal codificatore */
	uint64_t us_conversione;      /* BGRx → YUV, `colori709.c` */
	uint64_t us_codifica;         /* la sola libreria */
	bool trattenuto;              /* ⚠ un fotogramma entrato e non uscito */
} RipiegoUscita;

/*
 * ⭐ Dice PRIMA di aprire se il ripiego sa fare quel che si chiede, e se no
 *    perche' — per chi sceglie il codec (`figlio.c`) senza dover aprire e
 *    chiudere un codificatore per saperlo.  I rifiuti sono gli stessi di
 *    `ripiego_apri()`, scritti in UN posto solo.
 */
bool ripiego_sa_fare(const CodificatoreRichiesta *r, char *perche, size_t perche_byte);

/* Apre il codificatore.  `r->componente`, `r->nodo_rendering` e `r->potenza`
 * sono ignorati (sono della strada della scheda).  NULL con la ragione. */
Ripiego *ripiego_apri(const CodificatoreRichiesta *r, char *errore, size_t errore_byte);

/*
 * Converte e codifica UN fotogramma.  `pixel`/`passo` come
 * `codificatore_comprimi()`: BGRx o RGBx a 4 byte per pixel, oppure
 * yuv420p10le a tre piani (solo AV1 a 10 bit).  `chiave` = la chiede chi chiama
 * (`prossimo_chiave` in `codificatore.c`): con `true` esce una chiave VERA
 * (IDR / KEY_FRAME), mai un intra qualunque.
 */
bool ripiego_codifica(Ripiego *rp, const uint8_t *pixel, uint32_t passo, bool chiave,
                      RipiegoUscita *fuori);

/* Tela nuova: si riapre, e il prossimo fotogramma e' una chiave (RCP.md §5.2). */
bool ripiego_ridimensiona(Ripiego *rp, uint32_t larghezza, uint32_t altezza,
                          char *errore, size_t errore_byte);

/*
 * Cambia la qualita' a caldo — la leva di `abbassa_qualita()` e
 * `risali_qualita()`.  ⚠ Si riapre il codificatore, come oggi: il prossimo e'
 * una chiave, e chi chiama lo sa gia' (`c->prossimo_chiave = true`).
 */
bool ripiego_qualita(Ripiego *rp, ModoQualita modo, int qualita,
                     char *errore, size_t errore_byte);

/* «OpenH264 2.6.0 · QP 24 · CABAC · 4 fili» — per il registro, accanto a ogni numero. */
const char *ripiego_nome(const Ripiego *rp);

/* Il nome del componente, per `codificatore_ripiego_software()`:
 * "openh264", "svt-av1", o NULL per HEVC (che non c'e'). */
const char *ripiego_componente(CodecVideo codec);

void ripiego_chiudi(Ripiego *rp);

#endif
