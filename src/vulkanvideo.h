/*
 * vulkanvideo.h — la codifica sulla scheda con VULKAN VIDEO: H.264 e HEVC,
 * con `VK_KHR_video_encode_queue` e le due estensioni di codec, senza libva,
 * senza ffmpeg, senza GStreamer.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ FASE 19 — PERCHE' ESISTE (1 ott 2026, `DECISIONI.md` §10.27)
 *
 * Parola dell'utente: *«la codifica deve avvenire con strumenti standard,
 * preferibilmente con Vulkan, che accomuna tutte e 4 le architetture»*.
 * VA-API (`src/vadiretta.c`, fase 18) parla con Intel e AMD, ma il driver
 * NVIDIA proprietario non codifica via VA-API, e su una 5070 REMOTIX
 * ripiegava sul processore.  Vulkan Video e' l'API che TUTTI i produttori
 * espongono (AMD con RADV, NVIDIA col driver proprietario, Intel con ANV —
 * `[M]` 1 ott 2026 solo dietro `ANV_DEBUG=video-encode` con Mesa 25.0.7 e
 * 26.2.3, cioe' sperimentale).  ⇒ La strada si sceglie PER CAPACITA', non
 * per marca: 1) Vulkan Video se la scheda lo offre, 2) VA-API, 3) niente.
 *
 * ⛔ Licenze: il loader Vulkan e le intestazioni sono Apache-2.0, i driver
 *    stanno nel sistema.  Niente libreria di terzi in mezzo.
 *
 * ⭐ CHE COSA FA, nello stesso ordine di `vadiretta.h`:
 *   1. la SCOPERTA: per un nodo DRM, se la scheda sa codificare H.264 e/o
 *      HEVC in Vulkan, con misura massima, modi di bitrate, QP ammessi —
 *      `vulkanvideo_capacita()`, per scegliere la strada e per il controllo
 *      preliminare dell'installatore;
 *   2. la SESSIONE: profilo, formati, DPB, i parametri (SPS/PPS, e VPS per
 *      HEVC) scritti come `StdVideo*` con gli STESSI valori che
 *      `vadiretta.c` mette nelle sue intestazioni — High a 8 bit, Main /
 *      Main 10, niente B, un solo riferimento, BT.709 limitato nel VUI, il
 *      livello calcolato come ffmpeg o imposto (`RCP.md` §4.3);
 *   3. l'INGRESSO: copia zero da DMA-BUF (`VK_EXT_external_memory_dma_buf` +
 *      `VK_EXT_image_drm_format_modifier`) dei fotogrammi BGRx/RGBx, e la
 *      conversione RGB → NV12 (o P010) BT.709 limitato fatta da uno shader di
 *      calcolo SULLA SCHEDA, con gli stessi coefficienti e lo stesso filtro di
 *      croma di `colori709.c` (bit per bit: i piani che entrano nel
 *      codificatore sono quelli che la strada dalla memoria produce oggi);
 *      e l'ingresso dalla memoria (i pixel in CPU), che sale sulla scheda in
 *      RGB e si converte con lo stesso shader;
 *   4. il giro di ogni fotogramma: conversione, codifica, attesa, lettura dei
 *      byte; uscita Annex-B con SPS/PPS(/VPS) davanti a ogni chiave.
 *
 * ⛔ LE INTESTAZIONI LE SCRIVE IL DRIVER (`vkGetEncodedVideoSessionParametersKHR`)
 *    dai nostri `StdVideo*`: e' lui che sa che cosa codifica davvero, e se
 *    ha dovuto cambiare qualcosa lo dichiara (`hasOverrides`) e lo si scrive
 *    nel registro.  La verifica che il flusso sia dello stesso tipo di ieri
 *    (profilo, livello, misura, colore) la fa il banco con ffprobe e con
 *    Chrome, e nel prodotto `forma_va_bene()` di `codificatore.c` rilegge
 *    l'SPS a ogni chiave, come per VA-API.
 *
 * ⚠ Quel che NON c'e', dichiarato: il SEI identificatore e i SEI di
 *   buffering (ffmpeg li scriveva, `vadiretta.c` li riproduce per H.264):
 *   `[M]` nessun browser li legge e il muxer della pagina pesca solo SPS/PPS.
 *   I fotogrammi B: mai (basso ritardo).  Lo slice unico per fotogramma.
 * ---------------------------------------------------------------------------
 */
#ifndef REMOTIX_VULKANVIDEO_H
#define REMOTIX_VULKANVIDEO_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef enum { VULKANVIDEO_H264 = 3, VULKANVIDEO_HEVC = 1 } VulkanVideoCodec; /* = CodecVideo */

/* I modi di controllo del bitrate che la scheda dichiara (maschera). */
#define VULKANVIDEO_RC_CQP 1u /* VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DISABLED */
#define VULKANVIDEO_RC_CBR 2u
#define VULKANVIDEO_RC_VBR 4u

/* ═══════════════════════════════════════════════════════════════════════════
 * 1. LA SCOPERTA — per un nodo DRM, che cosa sa fare la scheda in Vulkan.
 *
 * ⛔ Tre esiti e non due (`LEZIONI.md` §1.9): `vulkan_c_e` dice se il nodo
 *    ha un dispositivo Vulkan con la coda di codifica; se e' falso i campi
 *    dei codec non vogliono dire niente e `perche` spiega.  ⚠ Un nodo senza
 *    Vulkan NON vuol dire «senza scheda»: su Intel oggi la risposta e' «no»
 *    e la strada e' VA-API.
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	bool codifica;                       /* la scheda sa codificare questo profilo */
	uint32_t misura_massima_l, misura_massima_a;
	uint32_t misura_minima_l, misura_minima_a;
	unsigned modi_bitrate;               /* maschera VULKANVIDEO_RC_* */
	int qp_minimo, qp_massimo;
	int livello_massimo_idc;             /* level_idc (H.264) / general_level_idc (HEVC) */
	uint32_t slot_dpb, riferimenti_attivi;
	uint32_t livelli_qualita;
	uint32_t granularita_l, granularita_a; /* l'allineamento che la scheda vuole in ingresso */
	bool intestazioni_dal_driver;        /* `vkGetEncodedVideoSessionParametersKHR` c'e' */
	char formato_ingresso[48];           /* il VkFormat scelto per i piani d'ingresso */
	bool ingresso_scrivibile_dallo_shader; /* STORAGE sul formato d'ingresso: conversione diretta */
	uint32_t sintassi;                   /* `stdSyntaxFlags`: che cosa delle intestazioni il driver onora */
	bool cabac, transform_8x8;           /* H.264: letti da `sintassi` */
} VulkanVideoProfiloCapacita;

typedef struct {
	bool vulkan_c_e;                     /* dispositivo + coda di codifica trovati */
	char perche[256];                    /* se no, perche' */
	char nome_scheda[256];               /* `deviceName` */
	char driver[256];                    /* `driverName` + `driverInfo` */
	uint32_t versione_api;               /* VK_API_VERSION del dispositivo */
	bool dmabuf;                         /* le due estensioni della copia zero ci sono */
	VulkanVideoProfiloCapacita h264;     /* High, 8 bit */
	VulkanVideoProfiloCapacita hevc;     /* Main, 8 bit */
	VulkanVideoProfiloCapacita hevc10;   /* Main 10 */
} VulkanVideoCapacita;

/* Apre e richiude tutto da sola: serve prima di decidere la strada, e
 * all'installatore.  Rende false solo se il nodo non si apre affatto. */
bool vulkanvideo_capacita(const char *nodo, VulkanVideoCapacita *c, char *errore,
                          size_t errore_byte);

/* ═══════════════════════════════════════════════════════════════════════════
 * 2. IL DISPOSITIVO — istanza, dispositivo fisico scelto DAL NODO DRM
 *    (`VK_EXT_physical_device_drm`: non «la prima scheda che c'e'»), dispositivo
 *    logico con una coda di codifica e una di calcolo.
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct VulkanVideoDispositivo VulkanVideoDispositivo;

VulkanVideoDispositivo *vulkanvideo_apri_dispositivo(const char *nodo, char *errore,
                                                     size_t errore_byte);
void vulkanvideo_chiudi_dispositivo(VulkanVideoDispositivo *d);

/* I modificatori (non lineari) che la scheda del nodo sa importare e campionare
 * per `formato_drm`, fino a `quanti`; quanti ne ha scritti (0 = nessuno, o
 * niente Vulkan).  Apre e richiude il dispositivo da sola. */
int vulkanvideo_modificatori(const char *nodo, uint32_t formato_drm, uint64_t *fuori, int quanti);
const char *vulkanvideo_nome_scheda(const VulkanVideoDispositivo *d);
const char *vulkanvideo_nome_driver(const VulkanVideoDispositivo *d);

/* ═══════════════════════════════════════════════════════════════════════════
 * 3. IL CODIFICATORE
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	VulkanVideoCodec codec;
	int profondita;                /* 8 o 10 (10 solo HEVC) */
	uint32_t larghezza, altezza;   /* la TELA: quel che il flusso mostra */
	uint32_t fotogrammi_al_secondo;
	int qp;                        /* 1..51: il QP fisso (CQP) o il pavimento di qualita' (VBR) */
	/* Il tetto di banda (fase 9): tutti zeri = CQP.  Altrimenti VBR con
	 * media = punto, massimo = filo, serbatoio in bit — gli stessi tre numeri
	 * che `codificatore.c` calcola.  ⚠ Vulkan non ha il QVBR di VA-API: il QP
	 * chiesto diventa il QP MINIMO del regolatore (non si spende piu' di
	 * quanto la qualita' chiesta costerebbe), e il regolatore sale di QP solo
	 * quando il tetto morde.  E' dichiarato nella `VulkanVideoDichiarazione`. */
	int64_t banda_punto, banda_filo;
	int serbatoio_bit;
	/* 0 = il livello si CALCOLA come faceva ffmpeg; >0 = imposto
	 * (`level_idc` per H.264, `general_level_idc` per HEVC). */
	int livello_idc;
	uint32_t chiavi_ogni;          /* 0 = chiavi solo su richiesta */
} VulkanVideoRichiesta;

/* ⭐ Quel che si e' letto dal driver e deciso all'apertura: la confessione. */
typedef struct {
	uint32_t larghezza_codificata, altezza_codificata; /* allineate al blocco */
	uint32_t blocco;                   /* 16 (H.264) o il CTB di HEVC */
	int livello_idc;                   /* quello scritto nell'SPS */
	unsigned modo_rc;                  /* VULKANVIDEO_RC_CQP / _VBR */
	bool intestazioni_dal_driver;      /* SPS/PPS presi dal driver (se no scritti da noi) */
	bool driver_ha_cambiato_parametri; /* `hasOverrides` sui parameter set */
	bool livello_corretto_nei_byte;    /* HEVC: il driver aveva scritto il livello nell'alfabeto sbagliato */
	bool conversione_diretta;          /* lo shader scrive NEI piani d'ingresso (STORAGE) */
	bool ritardo_minimo_chiesto;       /* VK_VIDEO_ENCODE_TUNING_MODE_ULTRA_LOW_LATENCY */
	uint32_t famiglia_codifica, famiglia_calcolo;
	char formato_ingresso[48];
	int qp_minimo, qp_massimo;         /* dichiarati dalla scheda */
	size_t intestazioni_byte;          /* quanti byte di SPS/PPS(/VPS) davanti a ogni chiave */
} VulkanVideoDichiarazione;

typedef struct VulkanVideo VulkanVideo;

VulkanVideo *vulkanvideo_apri(VulkanVideoDispositivo *d, const VulkanVideoRichiesta *r,
                              char *errore, size_t errore_byte);
void vulkanvideo_chiudi(VulkanVideo *v);
const VulkanVideoDichiarazione *vulkanvideo_dichiarazione(const VulkanVideo *v);

/* I tempi di un fotogramma, in microsecondi, separati come li tiene
 * `CodificatoreFotogramma`: lo zero in `caricamento` sulla copia zero vuol
 * dire «questo tratto non c'e'», non «e' gratis». */
typedef struct {
	uint64_t us_caricamento;  /* memoria di sistema → scheda (solo dalla memoria) */
	uint64_t us_conversione;  /* lo shader RGB → NV12 sulla scheda (e la copia GPU dei pixel caricati) */
	uint64_t us_codifica;     /* dalla consegna al codificatore ai byte letti */
} VulkanVideoTempi;

/* L'ordine dei byte dei pixel in ingresso. */
typedef enum { VULKANVIDEO_BGRX, VULKANVIDEO_RGBX } VulkanVideoOrdine;

/*
 * Codifica un fotogramma DALLA MEMORIA: `pixel` e' BGRx/RGBx, 4 byte per
 * pixel, `passo` in byte.  Chiave (IDR) se `chiave`.  ⛔ I byte resi
 * appartengono a `v` fino alla chiamata successiva.  ⚠ ASPETTA che la scheda
 * abbia finito.
 */
bool vulkanvideo_codifica_memoria(VulkanVideo *v, const uint8_t *pixel, uint32_t passo,
                                  VulkanVideoOrdine ordine, bool chiave,
                                  const uint8_t **dati, size_t *byte, VulkanVideoTempi *t,
                                  char *errore, size_t errore_byte);

/* Lo stesso DMA-BUF che `codificatore.h` descrive (`CodificatoreSuperficie`):
 * il descrittore resta del produttore e non si chiude; `generazione` butta la
 * cache delle importazioni quando i buffer del produttore cambiano. */
typedef struct {
	int fd;
	uint32_t offset;
	uint32_t stride;
	uint32_t larghezza, altezza;
	uint32_t formato_drm;          /* DRM_FORMAT_XRGB8888 / XBGR8888 (e le varianti con alfa) */
	uint64_t modificatore;
	uint64_t generazione;
} VulkanVideoSuperficie;

/* Codifica un fotogramma che sta GIA' sulla scheda: copia zero.  ⛔ Il
 * descrittore deve restare valido per tutta la chiamata; quando torna, la
 * scheda ha FINITO di leggerlo. */
bool vulkanvideo_codifica_dmabuf(VulkanVideo *v, const VulkanVideoSuperficie *s, bool chiave,
                                 const uint8_t **dati, size_t *byte, VulkanVideoTempi *t,
                                 char *errore, size_t errore_byte);

/* Il cambio di qualita' A CALDO: in CQP e' il QP del prossimo fotogramma; in
 * VBR e' il pavimento del regolatore, e il regolatore si riprogramma.  ⚠ Non
 * fa da sola una chiave: la chiede il chiamante se la vuole. */
bool vulkanvideo_qualita(VulkanVideo *v, int qp, char *errore, size_t errore_byte);

/* Il cambio di tela: si richiude e si riapre alla misura nuova, e il primo
 * fotogramma dopo e' una chiave (`codificatore.h`, `codificatore_ridimensiona`). */
bool vulkanvideo_ridimensiona(VulkanVideo *v, uint32_t larghezza, uint32_t altezza,
                              char *errore, size_t errore_byte);

#endif
