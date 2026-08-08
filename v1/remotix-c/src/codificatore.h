/*
 * codificatore — i due codec della pipeline EGFX.
 *
 * REMOTIX ne porta due e sceglie fra loro UNA VOLTA, al CapsConfirm, in base
 * ai flag dichiarati dal client (R3 di REFERENCE.md):
 *
 *   AVC disponibile   →  AVC420               Windows, Linux
 *   AVC_DISABLED      →  RemoteFX Progressive  Android
 *
 * Mandare AVC420 a chi ha dichiarato AVC_DISABLED produce schermo nero: il
 * client riscontra i fotogrammi e non disegna.  E' esattamente cio' che fa
 * Remote Desktop Manager, misurato il 3 agosto.
 *
 * ── Chi codifica, dalla fase 9 ──────────────────────────────────────────────
 *
 * L'AVC420 passa da `libavcodec`, con il codificatore scelto PER NOME a
 * runtime (§3.1 di SPECIFICA.md): `h264_vaapi`, `h264_qsv`, `h264_nvenc`, e
 * `libx264` come ripiego sempre disponibile.  Un solo percorso di codice,
 * nessuna riga specifica per costruttore — non si parla ne' a VA-API ne' a
 * NVENC, si parla a libavcodec.
 *
 * Resta raggiungibile anche `avc420_compress` di FreeRDP, con
 * `--codificatore freerdp`: non e' un residuo, e' il termine di paragone con
 * cui si misura il guadagno della fase 9 a parita' di tutto il resto.
 *
 * RemoteFX Progressive resta in CPU e non ha alternative: e' un codec a
 * wavelet e nessuna GPU lo codifica.  E' il percorso di Android, e la fase 9
 * non lo tocca — va detto, perche' significa che sul client Android di
 * riferimento l'accelerazione non porta guadagno diretto.
 */
#pragma once

#include <freerdp/channels/rdpgfx.h>
#include <freerdp/codec/h264.h>
#include <freerdp/codec/progressive.h>
#include <glib.h>
#include <libavutil/buffer.h>
#include <libavutil/frame.h>

typedef enum
{
	CODIFICATORE_AVC420,
	CODIFICATORE_PROGRESSIVE,
} TipoCodificatore;

typedef struct Codificatore Codificatore;

/*
 * `nome_chiesto` decide chi codifica l'AVC420:
 *
 *   NULL o "auto"  prova in ordine h264_vaapi, h264_qsv, h264_nvenc, libx264
 *   "<nome>"       usa quello e basta, e se non c'e' FALLISCE invece di
 *                  ripiegare in silenzio — chi lo chiede sta misurando, e un
 *                  ripiego non dichiarato falserebbe la misura
 *   "freerdp"      il vecchio percorso, `avc420_compress`
 *
 * Vale per AVC420; su RemoteFX Progressive e' ignorato.
 *
 * `superfici` e' il contesto dei fotogrammi che il palco ha gia' sulla scheda
 * (cattura a copia zero), oppure NULL per il percorso di sempre.
 *
 * Passandolo, il codificatore si apre SU QUELLE superfici e non ne alloca di
 * proprie: e' la condizione perche' il fotogramma catturato arrivi alla codifica
 * senza essere copiato.  Vale solo per un codificatore VA-API — con `libx264` o
 * con quello di FreeRDP i pixel servono in CPU, e il contesto viene ignorato.
 */
Codificatore *codificatore_nuovo(TipoCodificatore tipo, const char *nome_chiesto,
                                 AVBufferRef *superfici, uint32_t larghezza_allineata,
                                 uint32_t altezza_allineata, uint32_t bitrate_kbit,
                                 uint32_t fotogrammi_al_secondo);
void codificatore_libera(Codificatore *cod);

/* Per il registro: «AVC420 via h264_vaapi (in GPU)». */
const char *codificatore_nome(const Codificatore *cod);

/* Vero se la codifica avviene su una GPU.  Serve al registro e alle prove: la
 * fase 9 si giudica su un numero, ma prima bisogna sapere quale strada e'
 * stata presa davvero. */
gboolean codificatore_in_gpu(const Codificatore *cod);

/*
 * Comprime la regione utile e riempie `cmd`.
 *
 * `larghezza`/`altezza` sono la misura VERA del desktop, non quella allineata:
 * i rettangoli descrivono il contenuto, non la superficie (R5).  I bordi sono
 * ESCLUSIVI — misurato sui byte il 4 agosto.
 *
 * Restituisce FALSE se non c'e' niente da mandare o se la compressione
 * fallisce; in caso di successo il chiamante deve spedire `cmd` e poi chiamare
 * codificatore_rilascia().
 */
gboolean codificatore_comprimi(Codificatore *cod, const uint8_t *pixel, uint32_t passo,
                               uint32_t larghezza_allineata, uint32_t altezza_allineata,
                               uint32_t larghezza, uint32_t altezza,
                               RDPGFX_SURFACE_COMMAND *cmd);

/*
 * Quanti byte occupa sul filo il fotogramma appena compresso.
 *
 * ⛔ NON basta `cmd->length`: con AVC420 quel campo resta a zero, perche' il
 *    flusso e la metablock viaggiano in `cmd->extra` e li impacchetta FreeRDP al
 *    momento dell'invio.  Chi usasse `cmd->length` per decidere se un fotogramma
 *    e' abbastanza grosso da poterci misurare la banda otterrebbe zero SEMPRE
 *    sul percorso AVC, cioe' su Windows e su Linux: la misura non partirebbe
 *    mai, e il difetto si vedrebbe solo come «la banda resta a zero».
 *
 * Vale fra `codificatore_comprimi` e `codificatore_rilascia`.
 */
uint32_t codificatore_byte(const Codificatore *cod, const RDPGFX_SURFACE_COMMAND *cmd);

/*
 * Comprime un fotogramma che sta GIA' sulla scheda, nella misura allineata.
 *
 * E' la stessa cosa di `codificatore_comprimi`, meno tutto quello che c'era in
 * mezzo: niente copia dalla cattura, niente conversione di colore in CPU,
 * niente caricamento.  Vale solo se il codificatore e' stato aperto sulle
 * superfici del palco.
 */
gboolean codificatore_comprimi_superficie(Codificatore *cod, AVFrame *superficie,
                                          uint32_t larghezza, uint32_t altezza,
                                          RDPGFX_SURFACE_COMMAND *cmd);

/* Vero se il codificatore prende i fotogrammi dalla scheda invece che dalla
 * memoria: e' quel che decide quale delle due `comprimi` va chiamata. */
gboolean codificatore_su_superfici(const Codificatore *cod);

void codificatore_rilascia(Codificatore *cod);
