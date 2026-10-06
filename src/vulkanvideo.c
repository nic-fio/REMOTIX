/*
 * vulkanvideo.c — la codifica sulla scheda con Vulkan Video.  Il perche' e le
 * regole stanno in `vulkanvideo.h`.
 *
 * L'ordine del file e' quello di `vadiretta.c`:
 *   1. gli strumenti (errori, tempo, memoria);
 *   2. il livello, come lo indovinava ffmpeg (le stesse tabelle di vadiretta);
 *   3. il dispositivo: istanza, scheda scelta dal nodo DRM, code, estensioni;
 *   4. i profili e le capacita';
 *   5. l'apertura: sessione, parametri (StdVideo*), intestazioni, immagini,
 *      shader, buffer;
 *   6. l'ingresso: dalla memoria e dal DMA-BUF, e la conversione sulla scheda;
 *   7. il giro di un fotogramma: begin/control/encode/end, attesa, byte.
 *
 * ⛔ Le funzioni delle estensioni video NON le esporta il loader: si prendono
 *    con `vkGetInstanceProcAddr` / `vkGetDeviceProcAddr`, una volta, e stanno
 *    nel dispositivo (`f.`).  Il resto e' Vulkan 1.3 di base.
 */
#include "vulkanvideo.h"
#include "registro.h"

#include <errno.h>
#include <fcntl.h>
#include <gbm.h>
#include <unistd.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <time.h>
#include <unistd.h>

#include <drm_fourcc.h>
#include <vulkan/vulkan.h>

#define REG_CODIFICA "video"

/* Lo shader RGB → NV12/P010, in SPIR-V, generato da `19-shader.sh`. */
static const uint32_t SPV_RGB_NV12[] = {
#include "vulkanvideo_rgb_nv12_spv.h"
};

#define INGRESSI 2              /* le immagini d'ingresso, in tondo */
#define SLOT_DPB 2              /* il riferimento e la corrente */
#define CODED_MARGINE (1u << 16)
#define IMPORTAZIONI_MAX 8      /* la cache dei DMA-BUF importati */
#define INTESTAZIONI_MAX 2048

/* ═══════════════════════════════════════════════════════════════════════════
 * 1. STRUMENTI
 * ═══════════════════════════════════════════════════════════════════════════ */

static void di(char *dove, size_t quanto, const char *fmt, ...)
{
	va_list ap;
	if (!dove || !quanto)
		return;
	va_start(ap, fmt);
	vsnprintf(dove, quanto, fmt, ap);
	va_end(ap);
}

static uint64_t adesso_us(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (uint64_t) ts.tv_sec * 1000000u + (uint64_t) ts.tv_nsec / 1000u;
}

static const char *vk_nome(VkResult r)
{
	switch (r) {
	case VK_SUCCESS: return "VK_SUCCESS";
	case VK_NOT_READY: return "VK_NOT_READY";
	case VK_TIMEOUT: return "VK_TIMEOUT";
	case VK_INCOMPLETE: return "VK_INCOMPLETE";
	case VK_ERROR_OUT_OF_HOST_MEMORY: return "VK_ERROR_OUT_OF_HOST_MEMORY";
	case VK_ERROR_OUT_OF_DEVICE_MEMORY: return "VK_ERROR_OUT_OF_DEVICE_MEMORY";
	case VK_ERROR_INITIALIZATION_FAILED: return "VK_ERROR_INITIALIZATION_FAILED";
	case VK_ERROR_DEVICE_LOST: return "VK_ERROR_DEVICE_LOST";
	case VK_ERROR_MEMORY_MAP_FAILED: return "VK_ERROR_MEMORY_MAP_FAILED";
	case VK_ERROR_LAYER_NOT_PRESENT: return "VK_ERROR_LAYER_NOT_PRESENT";
	/* ⭐ 6 ott 2026, `[M]` RTX 4090 driver 595: è il «no» del driver alla
	 *    TREDICESIMA sessione di codifica insieme (il limite delle GeForce) */
	case VK_ERROR_TOO_MANY_OBJECTS: return "VK_ERROR_TOO_MANY_OBJECTS";
	case VK_ERROR_EXTENSION_NOT_PRESENT: return "VK_ERROR_EXTENSION_NOT_PRESENT";
	case VK_ERROR_FEATURE_NOT_PRESENT: return "VK_ERROR_FEATURE_NOT_PRESENT";
	case VK_ERROR_INCOMPATIBLE_DRIVER: return "VK_ERROR_INCOMPATIBLE_DRIVER";
	case VK_ERROR_FORMAT_NOT_SUPPORTED: return "VK_ERROR_FORMAT_NOT_SUPPORTED";
	case VK_ERROR_INVALID_EXTERNAL_HANDLE: return "VK_ERROR_INVALID_EXTERNAL_HANDLE";
	case VK_ERROR_INVALID_DRM_FORMAT_MODIFIER_PLANE_LAYOUT_EXT:
		return "VK_ERROR_INVALID_DRM_FORMAT_MODIFIER_PLANE_LAYOUT_EXT";
	case VK_ERROR_IMAGE_USAGE_NOT_SUPPORTED_KHR: return "VK_ERROR_IMAGE_USAGE_NOT_SUPPORTED_KHR";
	case VK_ERROR_VIDEO_PICTURE_LAYOUT_NOT_SUPPORTED_KHR:
		return "VK_ERROR_VIDEO_PICTURE_LAYOUT_NOT_SUPPORTED_KHR";
	case VK_ERROR_VIDEO_PROFILE_OPERATION_NOT_SUPPORTED_KHR:
		return "VK_ERROR_VIDEO_PROFILE_OPERATION_NOT_SUPPORTED_KHR";
	case VK_ERROR_VIDEO_PROFILE_FORMAT_NOT_SUPPORTED_KHR:
		return "VK_ERROR_VIDEO_PROFILE_FORMAT_NOT_SUPPORTED_KHR";
	case VK_ERROR_VIDEO_PROFILE_CODEC_NOT_SUPPORTED_KHR:
		return "VK_ERROR_VIDEO_PROFILE_CODEC_NOT_SUPPORTED_KHR";
	case VK_ERROR_VIDEO_STD_VERSION_NOT_SUPPORTED_KHR:
		return "VK_ERROR_VIDEO_STD_VERSION_NOT_SUPPORTED_KHR";
	case VK_ERROR_INVALID_VIDEO_STD_PARAMETERS_KHR: return "VK_ERROR_INVALID_VIDEO_STD_PARAMETERS_KHR";
	default: return "VkResult sconosciuto";
	}
}

#define FALLISCI(fmt, ...)                                   \
	do {                                                     \
		di(errore, errore_byte, fmt, ##__VA_ARGS__);         \
		return false;                                        \
	} while (0)

#define VK_O_FALLISCI(chiamata, che)                                            \
	do {                                                                        \
		VkResult _r = (chiamata);                                               \
		if (_r != VK_SUCCESS)                                                   \
			FALLISCI("%s: %s (%d)", che, vk_nome(_r), (int) _r);                \
	} while (0)

static uint32_t allinea(uint32_t x, uint32_t a)
{
	return a ? (x + a - 1) / a * a : x;
}

static int log2_intero(uint64_t x)
{
	int n = -1;
	while (x) {
		x >>= 1;
		n++;
	}
	return n < 0 ? 0 : n;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 2. IL LIVELLO — come lo indovinava ffmpeg quando nessuno lo imponeva.
 *    ⚠ Sono le tabelle di `vadiretta.c` (A-1 di H.264, A.4 di H.265), copiate
 *      e non condivise perche' `vadiretta.c` e' della fase 18 e non si tocca
 *      da questa linea: all'innesto le due copie si uniscono in un file solo.
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct {
	int level_idc, cs3f;
	int max_mbps, max_fs, max_dpb_mbs, max_br;
} LivelloH264;

static const LivelloH264 LIVELLI_H264[] = {
	{ 10, 0, 1485, 99, 396, 64 },          { 11, 1, 1485, 99, 396, 128 },
	{ 9, 0, 1485, 99, 396, 128 },          { 11, 0, 3000, 396, 900, 192 },
	{ 12, 0, 6000, 396, 2376, 384 },       { 13, 0, 11880, 396, 2376, 768 },
	{ 20, 0, 11880, 396, 2376, 2000 },     { 21, 0, 19800, 792, 4752, 4000 },
	{ 22, 0, 20250, 1620, 8100, 4000 },    { 30, 0, 40500, 1620, 8100, 10000 },
	{ 31, 0, 108000, 3600, 18000, 14000 }, { 32, 0, 216000, 5120, 20480, 20000 },
	{ 40, 0, 245760, 8192, 32768, 20000 }, { 41, 0, 245760, 8192, 32768, 50000 },
	{ 42, 0, 522240, 8704, 34816, 50000 }, { 50, 0, 589824, 22080, 110400, 135000 },
	{ 51, 0, 983040, 36864, 184320, 240000 }, { 52, 0, 2073600, 36864, 184320, 240000 },
	{ 60, 0, 4177920, 139264, 696320, 240000 }, { 61, 0, 8355840, 139264, 696320, 480000 },
	{ 62, 0, 16711680, 139264, 696320, 800000 },
};

static int livello_h264(int64_t bitrate, int fps, uint32_t mb_l, uint32_t mb_a, int dpb)
{
	for (size_t i = 0; i < sizeof LIVELLI_H264 / sizeof LIVELLI_H264[0]; i++) {
		const LivelloH264 *L = &LIVELLI_H264[i];
		uint64_t mb = (uint64_t) mb_l * mb_a;

		if (L->cs3f || L->level_idc == 9)
			continue;
		if (bitrate > (int64_t) L->max_br * 1500)
			continue;
		if (mb > (uint64_t) L->max_fs)
			continue;
		if ((uint64_t) mb_l * mb_l > 8u * (uint64_t) L->max_fs)
			continue;
		if ((uint64_t) mb_a * mb_a > 8u * (uint64_t) L->max_fs)
			continue;
		if (mb) {
			int dpb_max = (int) ((uint64_t) L->max_dpb_mbs / mb);
			if (dpb_max > 16)
				dpb_max = 16;
			if (dpb > dpb_max)
				continue;
			if (fps > (int) ((uint64_t) L->max_mbps / mb))
				continue;
		}
		return L->level_idc;
	}
	return 62;
}

typedef struct {
	int level_idc;
	uint32_t max_luma_ps;
	int max_br_main;
} LivelloHEVC;

static const LivelloHEVC LIVELLI_HEVC[] = {
	{ 30, 36864, 128 },       { 60, 122880, 1500 },     { 63, 245760, 3000 },
	{ 90, 552960, 6000 },     { 93, 983040, 10000 },    { 120, 2228224, 12000 },
	{ 123, 2228224, 20000 },  { 150, 8912896, 25000 },  { 153, 8912896, 40000 },
	{ 156, 8912896, 60000 },  { 180, 35651584, 60000 }, { 183, 35651584, 120000 },
	{ 186, 35651584, 240000 },
};

static int livello_hevc(int64_t bitrate, uint32_t l, uint32_t a, int dpb)
{
	uint64_t pic = (uint64_t) l * a;

	for (size_t i = 0; i < sizeof LIVELLI_HEVC / sizeof LIVELLI_HEVC[0]; i++) {
		const LivelloHEVC *L = &LIVELLI_HEVC[i];
		int dpb_max;

		if (pic > L->max_luma_ps)
			continue;
		if ((uint64_t) l * l > 8u * (uint64_t) L->max_luma_ps)
			continue;
		if ((uint64_t) a * a > 8u * (uint64_t) L->max_luma_ps)
			continue;
		if (bitrate > (int64_t) 1100 * L->max_br_main)
			continue;
		if (pic <= (L->max_luma_ps >> 2))
			dpb_max = 16;
		else if (pic <= (L->max_luma_ps >> 1))
			dpb_max = 12;
		else if (pic <= (3u * L->max_luma_ps >> 2))
			dpb_max = 8;
		else
			dpb_max = 6;
		if (dpb > dpb_max)
			continue;
		return L->level_idc;
	}
	/* ffmpeg direbbe 8.5 (255) col tier alto; l'alfabeto di Vulkan si ferma a
	 * 6.2 e qui ci si ferma con lui, dichiarandolo nel registro. */
	return 186;
}

/* Da `level_idc` all'alfabeto di Vulkan (`StdVideoH264LevelIdc`), e ritorno. */
static StdVideoH264LevelIdc h264_livello_enum(int idc)
{
	static const int tabella[] = { 10, 11, 12, 13, 20, 21, 22, 30, 31, 32,
	                               40, 41, 42, 50, 51, 52, 60, 61, 62 };
	for (size_t i = 0; i < sizeof tabella / sizeof tabella[0]; i++)
		if (tabella[i] >= idc)
			return (StdVideoH264LevelIdc) i;
	return STD_VIDEO_H264_LEVEL_IDC_6_2;
}

static int h264_livello_idc(StdVideoH264LevelIdc e)
{
	static const int tabella[] = { 10, 11, 12, 13, 20, 21, 22, 30, 31, 32,
	                               40, 41, 42, 50, 51, 52, 60, 61, 62 };
	return (unsigned) e < 19 ? tabella[e] : 62;
}

static StdVideoH265LevelIdc hevc_livello_enum(int idc)
{
	static const int tabella[] = { 30, 60, 63, 90, 93, 120, 123, 150, 153, 156, 180, 183, 186 };
	for (size_t i = 0; i < sizeof tabella / sizeof tabella[0]; i++)
		if (tabella[i] >= idc)
			return (StdVideoH265LevelIdc) i;
	return STD_VIDEO_H265_LEVEL_IDC_6_2;
}

static int hevc_livello_idc(StdVideoH265LevelIdc e)
{
	static const int tabella[] = { 30, 60, 63, 90, 93, 120, 123, 150, 153, 156, 180, 183, 186 };
	return (unsigned) e < 13 ? tabella[e] : 186;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 3. IL DISPOSITIVO
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct {
	PFN_vkGetPhysicalDeviceVideoCapabilitiesKHR GetPhysicalDeviceVideoCapabilitiesKHR;
	PFN_vkGetPhysicalDeviceVideoFormatPropertiesKHR GetPhysicalDeviceVideoFormatPropertiesKHR;
	PFN_vkCreateVideoSessionKHR CreateVideoSessionKHR;
	PFN_vkDestroyVideoSessionKHR DestroyVideoSessionKHR;
	PFN_vkGetVideoSessionMemoryRequirementsKHR GetVideoSessionMemoryRequirementsKHR;
	PFN_vkBindVideoSessionMemoryKHR BindVideoSessionMemoryKHR;
	PFN_vkCreateVideoSessionParametersKHR CreateVideoSessionParametersKHR;
	PFN_vkDestroyVideoSessionParametersKHR DestroyVideoSessionParametersKHR;
	PFN_vkGetEncodedVideoSessionParametersKHR GetEncodedVideoSessionParametersKHR;
	PFN_vkCmdBeginVideoCodingKHR CmdBeginVideoCodingKHR;
	PFN_vkCmdEndVideoCodingKHR CmdEndVideoCodingKHR;
	PFN_vkCmdControlVideoCodingKHR CmdControlVideoCodingKHR;
	PFN_vkCmdEncodeVideoKHR CmdEncodeVideoKHR;
	PFN_vkGetMemoryFdPropertiesKHR GetMemoryFdPropertiesKHR;
} Funzioni;

struct VulkanVideoDispositivo {
	VkInstance istanza;
	VkPhysicalDevice fisico;
	VkDevice dispositivo;
	VkPhysicalDeviceMemoryProperties memoria;
	uint32_t fam_codifica, fam_calcolo;
	VkQueue coda_codifica, coda_calcolo;
	VkVideoCodecOperationFlagsKHR operazioni;
	bool ha_h264, ha_h265, ha_dmabuf, ha_foreign, ha_maintenance1, ha_drm;
	bool scrive_senza_formato;    /* shaderStorageImageWriteWithoutFormat */
	char nome[256], driver[256], nodo[64];
	uint32_t versione_api;
	Funzioni f;
};

static bool estensione_c_e(const VkExtensionProperties *e, uint32_t n, const char *nome)
{
	for (uint32_t i = 0; i < n; i++)
		if (strcmp(e[i].extensionName, nome) == 0)
			return true;
	return false;
}

/* La scheda che sta dietro al NODO: `VK_EXT_physical_device_drm` da' maggiore e
 * minore del nodo di rendering di ogni dispositivo fisico, e li si confrontano
 * con `stat()` del nodo chiesto.  ⛔ Non «il primo dispositivo»: su questa
 * macchina ce ne sono tre (Radeon, Intel, llvmpipe). */
static bool scegli_fisico(VulkanVideoDispositivo *d, const char *nodo, char *errore,
                          size_t errore_byte)
{
	struct stat st;
	uint32_t quanti = 0;
	VkPhysicalDevice elenco[16];
	char visti[512] = { 0 };

	if (stat(nodo, &st) != 0)
		FALLISCI("il nodo %s non si legge: %s", nodo, strerror(errno));
	VK_O_FALLISCI(vkEnumeratePhysicalDevices(d->istanza, &quanti, NULL), "vkEnumeratePhysicalDevices");
	if (quanti > 16)
		quanti = 16;
	if (!quanti)
		FALLISCI("nessun dispositivo Vulkan");
	vkEnumeratePhysicalDevices(d->istanza, &quanti, elenco);
	for (uint32_t i = 0; i < quanti; i++) {
		uint32_t ne = 0;
		VkExtensionProperties *est;
		VkPhysicalDeviceDrmPropertiesEXT drm = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DRM_PROPERTIES_EXT };
		VkPhysicalDeviceProperties2 p2 = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2 };
		char pezzo[160];

		vkEnumerateDeviceExtensionProperties(elenco[i], NULL, &ne, NULL);
		est = calloc(ne ? ne : 1, sizeof *est);
		if (!est)
			FALLISCI("niente memoria");
		vkEnumerateDeviceExtensionProperties(elenco[i], NULL, &ne, est);
		if (estensione_c_e(est, ne, VK_EXT_PHYSICAL_DEVICE_DRM_EXTENSION_NAME))
			p2.pNext = &drm;
		vkGetPhysicalDeviceProperties2(elenco[i], &p2);
		snprintf(pezzo, sizeof pezzo, "%s«%s»%s", i ? ", " : "", p2.properties.deviceName,
		         p2.pNext ? "" : " (senza VK_EXT_physical_device_drm)");
		strncat(visti, pezzo, sizeof visti - strlen(visti) - 1);
		if (p2.pNext && ((drm.hasRender && drm.renderMajor == (int64_t) major(st.st_rdev)
		                  && drm.renderMinor == (int64_t) minor(st.st_rdev))
		                 || (drm.hasPrimary && drm.primaryMajor == (int64_t) major(st.st_rdev)
		                     && drm.primaryMinor == (int64_t) minor(st.st_rdev)))) {
			d->fisico = elenco[i];
			d->ha_drm = true;
			d->ha_h264 = estensione_c_e(est, ne, VK_KHR_VIDEO_ENCODE_H264_EXTENSION_NAME);
			d->ha_h265 = estensione_c_e(est, ne, VK_KHR_VIDEO_ENCODE_H265_EXTENSION_NAME);
			d->ha_dmabuf = estensione_c_e(est, ne, VK_EXT_EXTERNAL_MEMORY_DMA_BUF_EXTENSION_NAME)
			               && estensione_c_e(est, ne, VK_EXT_IMAGE_DRM_FORMAT_MODIFIER_EXTENSION_NAME)
			               && estensione_c_e(est, ne, VK_KHR_EXTERNAL_MEMORY_FD_EXTENSION_NAME);
			d->ha_foreign = estensione_c_e(est, ne, VK_EXT_QUEUE_FAMILY_FOREIGN_EXTENSION_NAME);
			d->ha_maintenance1 = estensione_c_e(est, ne, VK_KHR_VIDEO_MAINTENANCE_1_EXTENSION_NAME);
			bool coda = estensione_c_e(est, ne, VK_KHR_VIDEO_QUEUE_EXTENSION_NAME)
			            && estensione_c_e(est, ne, VK_KHR_VIDEO_ENCODE_QUEUE_EXTENSION_NAME);
			free(est);
			snprintf(d->nome, sizeof d->nome, "%s", p2.properties.deviceName);
			d->versione_api = p2.properties.apiVersion;
			{
				VkPhysicalDeviceDriverProperties dp = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_DRIVER_PROPERTIES };
				VkPhysicalDeviceProperties2 q = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2, .pNext = &dp };
				vkGetPhysicalDeviceProperties2(elenco[i], &q);
				snprintf(d->driver, sizeof d->driver, "%s %s", dp.driverName, dp.driverInfo);
			}
			if (!coda)
				FALLISCI("«%s» (%s) su %s non ha VK_KHR_video_encode_queue: niente codifica Vulkan",
				         d->nome, d->driver, nodo);
			if (!d->ha_h264 && !d->ha_h265)
				FALLISCI("«%s» (%s) su %s ha la coda video ma nessun codec di codifica "
				         "(ne' VK_KHR_video_encode_h264 ne' _h265)", d->nome, d->driver, nodo);
			if (p2.properties.apiVersion < VK_API_VERSION_1_3)
				FALLISCI("«%s» e' Vulkan %u.%u: serve 1.3", d->nome,
				         VK_API_VERSION_MAJOR(p2.properties.apiVersion),
				         VK_API_VERSION_MINOR(p2.properties.apiVersion));
			return true;
		}
		free(est);
	}
	FALLISCI("nessun dispositivo Vulkan sta dietro a %s (%u:%u); visti: %s", nodo,
	         major(st.st_rdev), minor(st.st_rdev), visti);
}

static bool scegli_code(VulkanVideoDispositivo *d, char *errore, size_t errore_byte)
{
	uint32_t n = 0;
	VkQueueFamilyProperties2 *fp;
	VkQueueFamilyVideoPropertiesKHR *vp;
	uint32_t codifica = UINT32_MAX, calcolo = UINT32_MAX;

	vkGetPhysicalDeviceQueueFamilyProperties2(d->fisico, &n, NULL);
	if (!n)
		FALLISCI("nessuna famiglia di code");
	fp = calloc(n, sizeof *fp);
	vp = calloc(n, sizeof *vp);
	if (!fp || !vp) {
		free(fp);
		free(vp);
		FALLISCI("niente memoria");
	}
	for (uint32_t i = 0; i < n; i++) {
		fp[i].sType = VK_STRUCTURE_TYPE_QUEUE_FAMILY_PROPERTIES_2;
		vp[i].sType = VK_STRUCTURE_TYPE_QUEUE_FAMILY_VIDEO_PROPERTIES_KHR;
		fp[i].pNext = &vp[i];
	}
	vkGetPhysicalDeviceQueueFamilyProperties2(d->fisico, &n, fp);
	for (uint32_t i = 0; i < n; i++) {
		VkQueueFlags fl = fp[i].queueFamilyProperties.queueFlags;
		if ((fl & VK_QUEUE_VIDEO_ENCODE_BIT_KHR)
		    && (vp[i].videoCodecOperations & (VK_VIDEO_CODEC_OPERATION_ENCODE_H264_BIT_KHR
		                                      | VK_VIDEO_CODEC_OPERATION_ENCODE_H265_BIT_KHR))
		    && codifica == UINT32_MAX) {
			codifica = i;
			d->operazioni = vp[i].videoCodecOperations;
		}
	}
	/* il calcolo: una famiglia con COMPUTE e TRANSFER, preferibilmente non
	 * quella grafica (cosi' la conversione non fa la fila col compositore). */
	for (uint32_t i = 0; i < n; i++) {
		VkQueueFlags fl = fp[i].queueFamilyProperties.queueFlags;
		if (!(fl & VK_QUEUE_COMPUTE_BIT))
			continue;
		if (calcolo == UINT32_MAX || (!(fl & VK_QUEUE_GRAPHICS_BIT)
		                              && (fp[calcolo].queueFamilyProperties.queueFlags & VK_QUEUE_GRAPHICS_BIT)))
			calcolo = i;
	}
	free(fp);
	free(vp);
	if (codifica == UINT32_MAX)
		FALLISCI("«%s»: nessuna famiglia di code con la codifica video H.264/HEVC", d->nome);
	if (calcolo == UINT32_MAX)
		FALLISCI("«%s»: nessuna famiglia di code con il calcolo", d->nome);
	d->fam_codifica = codifica;
	d->fam_calcolo = calcolo;
	return true;
}

#define PRENDI_D(nome)                                                                 \
	do {                                                                               \
		d->f.nome = (PFN_vk##nome) vkGetDeviceProcAddr(d->dispositivo, "vk" #nome);     \
		if (!d->f.nome)                                                                \
			FALLISCI("vkGetDeviceProcAddr(vk" #nome ") e' nulla");                     \
	} while (0)
#define PRENDI_I(nome)                                                                 \
	do {                                                                               \
		d->f.nome = (PFN_vk##nome) vkGetInstanceProcAddr(d->istanza, "vk" #nome);       \
		if (!d->f.nome)                                                                \
			FALLISCI("vkGetInstanceProcAddr(vk" #nome ") e' nulla");                   \
	} while (0)

static bool apri_dispositivo_logico(VulkanVideoDispositivo *d, char *errore, size_t errore_byte)
{
	const char *est[12];
	uint32_t ne = 0;
	float prio = 1.0f;
	VkDeviceQueueCreateInfo code[2] = {
		{ .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, .queueFamilyIndex = d->fam_codifica,
		  .queueCount = 1, .pQueuePriorities = &prio },
		{ .sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO, .queueFamilyIndex = d->fam_calcolo,
		  .queueCount = 1, .pQueuePriorities = &prio },
	};
	VkPhysicalDeviceVulkan13Features f13 = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES };
	VkPhysicalDeviceVulkan11Features f11 = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES, .pNext = &f13 };
	VkPhysicalDeviceFeatures2 f2 = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2, .pNext = &f11 };
	VkDeviceCreateInfo ci = { .sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO };

	vkGetPhysicalDeviceFeatures2(d->fisico, &f2);
	if (!f13.synchronization2)
		FALLISCI("«%s» non ha synchronization2", d->nome);
	if (!f11.samplerYcbcrConversion)
		FALLISCI("«%s» non ha samplerYcbcrConversion (serve per le immagini NV12)", d->nome);
	d->scrive_senza_formato = f2.features.shaderStorageImageWriteWithoutFormat;
	if (!d->scrive_senza_formato)
		FALLISCI("«%s» non ha shaderStorageImageWriteWithoutFormat (lo shader scrive NV12 e P010)", d->nome);
	/* solo quel che serve, acceso: le altre caratteristiche restano spente */
	memset(&f2.features, 0, sizeof f2.features);
	f2.features.shaderStorageImageWriteWithoutFormat = VK_TRUE;
	{
		VkPhysicalDeviceVulkan11Features v11 = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES, .pNext = &f13 };
		VkPhysicalDeviceVulkan13Features v13 = { .sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES };
		v11.samplerYcbcrConversion = VK_TRUE;
		v13.synchronization2 = VK_TRUE;
		f11 = v11;
		f13 = v13;
		f11.pNext = &f13;
	}

	est[ne++] = VK_KHR_VIDEO_QUEUE_EXTENSION_NAME;
	est[ne++] = VK_KHR_VIDEO_ENCODE_QUEUE_EXTENSION_NAME;
	if (d->ha_h264)
		est[ne++] = VK_KHR_VIDEO_ENCODE_H264_EXTENSION_NAME;
	if (d->ha_h265)
		est[ne++] = VK_KHR_VIDEO_ENCODE_H265_EXTENSION_NAME;
	if (d->ha_dmabuf) {
		est[ne++] = VK_KHR_EXTERNAL_MEMORY_FD_EXTENSION_NAME;
		est[ne++] = VK_EXT_EXTERNAL_MEMORY_DMA_BUF_EXTENSION_NAME;
		est[ne++] = VK_EXT_IMAGE_DRM_FORMAT_MODIFIER_EXTENSION_NAME;
	}
	if (d->ha_foreign)
		est[ne++] = VK_EXT_QUEUE_FAMILY_FOREIGN_EXTENSION_NAME;
	if (d->ha_maintenance1)
		est[ne++] = VK_KHR_VIDEO_MAINTENANCE_1_EXTENSION_NAME;

	ci.pNext = &f2;
	ci.queueCreateInfoCount = d->fam_codifica == d->fam_calcolo ? 1 : 2;
	ci.pQueueCreateInfos = code;
	ci.enabledExtensionCount = ne;
	ci.ppEnabledExtensionNames = est;
	VK_O_FALLISCI(vkCreateDevice(d->fisico, &ci, NULL, &d->dispositivo), "vkCreateDevice");
	vkGetDeviceQueue(d->dispositivo, d->fam_codifica, 0, &d->coda_codifica);
	if (d->fam_codifica == d->fam_calcolo)
		d->coda_calcolo = d->coda_codifica;
	else
		vkGetDeviceQueue(d->dispositivo, d->fam_calcolo, 0, &d->coda_calcolo);
	vkGetPhysicalDeviceMemoryProperties(d->fisico, &d->memoria);

	PRENDI_I(GetPhysicalDeviceVideoCapabilitiesKHR);
	PRENDI_I(GetPhysicalDeviceVideoFormatPropertiesKHR);
	PRENDI_D(CreateVideoSessionKHR);
	PRENDI_D(DestroyVideoSessionKHR);
	PRENDI_D(GetVideoSessionMemoryRequirementsKHR);
	PRENDI_D(BindVideoSessionMemoryKHR);
	PRENDI_D(CreateVideoSessionParametersKHR);
	PRENDI_D(DestroyVideoSessionParametersKHR);
	PRENDI_D(GetEncodedVideoSessionParametersKHR);
	PRENDI_D(CmdBeginVideoCodingKHR);
	PRENDI_D(CmdEndVideoCodingKHR);
	PRENDI_D(CmdControlVideoCodingKHR);
	PRENDI_D(CmdEncodeVideoKHR);
	if (d->ha_dmabuf)
		PRENDI_D(GetMemoryFdPropertiesKHR);
	return true;
}

VulkanVideoDispositivo *vulkanvideo_apri_dispositivo(const char *nodo, char *errore, size_t errore_byte)
{
	VulkanVideoDispositivo *d;
	VkApplicationInfo app = {
		.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO,
		.pApplicationName = "remotix",
		.pEngineName = "remotix-vulkanvideo",
		.apiVersion = VK_API_VERSION_1_3,
	};
	VkInstanceCreateInfo ic = { .sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO, .pApplicationInfo = &app };
	VkResult r;

	if (!nodo || !nodo[0]) {
		di(errore, errore_byte, "vulkanvideo: nessun nodo DRM dichiarato — non se ne indovina uno");
		return NULL;
	}
	d = calloc(1, sizeof *d);
	if (!d) {
		di(errore, errore_byte, "niente memoria");
		return NULL;
	}
	snprintf(d->nodo, sizeof d->nodo, "%s", nodo);
	r = vkCreateInstance(&ic, NULL, &d->istanza);
	if (r != VK_SUCCESS) {
		di(errore, errore_byte, "vkCreateInstance: %s", vk_nome(r));
		free(d);
		return NULL;
	}
	if (!scegli_fisico(d, nodo, errore, errore_byte) || !scegli_code(d, errore, errore_byte)
	    || !apri_dispositivo_logico(d, errore, errore_byte)) {
		vulkanvideo_chiudi_dispositivo(d);
		return NULL;
	}
	return d;
}

void vulkanvideo_chiudi_dispositivo(VulkanVideoDispositivo *d)
{
	if (!d)
		return;
	if (d->dispositivo)
		vkDestroyDevice(d->dispositivo, NULL);
	if (d->istanza)
		vkDestroyInstance(d->istanza, NULL);
	free(d);
}

const char *vulkanvideo_nome_scheda(const VulkanVideoDispositivo *d)
{
	return d ? d->nome : "";
}

const char *vulkanvideo_nome_driver(const VulkanVideoDispositivo *d)
{
	return d ? d->driver : "";
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 4. I PROFILI E LE CAPACITA'
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Il profilo video e' una catena di tre strutture che va passata UGUALE a
 * tutti gli oggetti che lo usano (sessione, immagini, buffer, query): sta in
 * un posto e si copia da li'. */
typedef struct {
	VkVideoProfileInfoKHR profilo;
	VkVideoEncodeUsageInfoKHR uso;
	VkVideoEncodeH264ProfileInfoKHR h264;
	VkVideoEncodeH265ProfileInfoKHR h265;
	VkVideoProfileListInfoKHR lista;
} Profilo;

static void profilo_componi(Profilo *p, VulkanVideoCodec codec, int profondita, bool ritardo_minimo)
{
	memset(p, 0, sizeof *p);
	p->uso = (VkVideoEncodeUsageInfoKHR){
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_USAGE_INFO_KHR,
		.videoUsageHints = VK_VIDEO_ENCODE_USAGE_STREAMING_BIT_KHR,
		.videoContentHints = VK_VIDEO_ENCODE_CONTENT_DESKTOP_BIT_KHR,
		.tuningMode = ritardo_minimo ? VK_VIDEO_ENCODE_TUNING_MODE_ULTRA_LOW_LATENCY_KHR
		                             : VK_VIDEO_ENCODE_TUNING_MODE_DEFAULT_KHR,
	};
	if (codec == VULKANVIDEO_H264) {
		p->h264 = (VkVideoEncodeH264ProfileInfoKHR){
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_PROFILE_INFO_KHR,
			.pNext = &p->uso,
			.stdProfileIdc = STD_VIDEO_H264_PROFILE_IDC_HIGH,
		};
		p->profilo.pNext = &p->h264;
		p->profilo.videoCodecOperation = VK_VIDEO_CODEC_OPERATION_ENCODE_H264_BIT_KHR;
	} else {
		p->h265 = (VkVideoEncodeH265ProfileInfoKHR){
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_PROFILE_INFO_KHR,
			.pNext = &p->uso,
			.stdProfileIdc = profondita == 10 ? STD_VIDEO_H265_PROFILE_IDC_MAIN_10
			                                  : STD_VIDEO_H265_PROFILE_IDC_MAIN,
		};
		p->profilo.pNext = &p->h265;
		p->profilo.videoCodecOperation = VK_VIDEO_CODEC_OPERATION_ENCODE_H265_BIT_KHR;
	}
	p->profilo.sType = VK_STRUCTURE_TYPE_VIDEO_PROFILE_INFO_KHR;
	p->profilo.chromaSubsampling = VK_VIDEO_CHROMA_SUBSAMPLING_420_BIT_KHR;
	p->profilo.lumaBitDepth = profondita == 10 ? VK_VIDEO_COMPONENT_BIT_DEPTH_10_BIT_KHR
	                                            : VK_VIDEO_COMPONENT_BIT_DEPTH_8_BIT_KHR;
	p->profilo.chromaBitDepth = p->profilo.lumaBitDepth;
	p->lista = (VkVideoProfileListInfoKHR){
		.sType = VK_STRUCTURE_TYPE_VIDEO_PROFILE_LIST_INFO_KHR,
		.profileCount = 1,
		.pProfiles = &p->profilo,
	};
}

typedef struct {
	VkVideoCapabilitiesKHR video;
	VkVideoEncodeCapabilitiesKHR codifica;
	VkVideoEncodeH264CapabilitiesKHR h264;
	VkVideoEncodeH265CapabilitiesKHR h265;
	VkFormat formato_ingresso, formato_dpb;
	VkImageUsageFlags usi_ingresso, usi_dpb;
	VkImageCreateFlags flag_ingresso, flag_dpb;
	/* ⛔ `imageUsageFlags` delle proprieta' video NON basta: `[M]` 1 ott 2026
	 *    RADV ci rimette solo l'uso chiesto (0x4000).  Quel che un'immagine
	 *    puo' fare lo dice `vkGetPhysicalDeviceImageFormatProperties2` col
	 *    profilo nella catena, e si chiede per le due strade. */
	bool ingresso_diretto;   /* ENCODE_SRC | STORAGE (coi piani mutabili): lo shader scrive i piani */
	bool ingresso_copia;     /* ENCODE_SRC | TRANSFER_DST: lo shader scrive altrove e si copia */
	bool livello_dichiarato; /* `maxLevelIdc` > 1.0: se e' 0 il driver non lo dice */
} Capacita;

/* Un'immagine con questo formato, uso e flag si puo' creare per questo
 * profilo?  Tre esiti: si', no, e «la chiamata e' fallita» che vale no. */
static bool uso_sostenuto(VulkanVideoDispositivo *d, const Profilo *p, VkFormat f, VkImageUsageFlags uso,
                          VkImageCreateFlags flag)
{
	VkPhysicalDeviceImageFormatInfo2 fi = {
		.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_FORMAT_INFO_2, .pNext = &p->lista, .format = f,
		.type = VK_IMAGE_TYPE_2D, .tiling = VK_IMAGE_TILING_OPTIMAL, .usage = uso, .flags = flag };
	VkImageFormatProperties2 fp = { .sType = VK_STRUCTURE_TYPE_IMAGE_FORMAT_PROPERTIES_2 };
	return vkGetPhysicalDeviceImageFormatProperties2(d->fisico, &fi, &fp) == VK_SUCCESS;
}

static VkFormat formato_voluto(int profondita)
{
	return profondita == 10 ? VK_FORMAT_G10X6_B10X6R10X6_2PLANE_420_UNORM_3PACK16
	                        : VK_FORMAT_G8_B8R8_2PLANE_420_UNORM;
}

static const char *nome_formato(VkFormat f)
{
	switch (f) {
	case VK_FORMAT_G8_B8R8_2PLANE_420_UNORM: return "NV12 (G8_B8R8_2PLANE_420)";
	case VK_FORMAT_G10X6_B10X6R10X6_2PLANE_420_UNORM_3PACK16: return "P010 (G10X6_B10X6R10X6_2PLANE_420)";
	case VK_FORMAT_G8_B8_R8_3PLANE_420_UNORM: return "I420 (3PLANE_420)";
	default: return "altro";
	}
}

static bool formati_del_profilo(VulkanVideoDispositivo *d, const Profilo *p, int profondita,
                                VkImageUsageFlags uso, VkFormat *formato, VkImageUsageFlags *usi,
                                VkImageCreateFlags *flag, char *errore, size_t errore_byte)
{
	VkPhysicalDeviceVideoFormatInfoKHR fi = {
		.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VIDEO_FORMAT_INFO_KHR,
		.pNext = &p->lista,
		.imageUsage = uso,
	};
	uint32_t n = 0;
	VkVideoFormatPropertiesKHR fp[16];
	VkFormat voluto = formato_voluto(profondita);

	VK_O_FALLISCI(d->f.GetPhysicalDeviceVideoFormatPropertiesKHR(d->fisico, &fi, &n, NULL),
	              "vkGetPhysicalDeviceVideoFormatPropertiesKHR");
	if (n > 16)
		n = 16;
	if (!n)
		FALLISCI("il driver non dichiara nessun formato d'immagine per l'uso 0x%x", uso);
	for (uint32_t i = 0; i < n; i++) {
		memset(&fp[i], 0, sizeof fp[i]);
		fp[i].sType = VK_STRUCTURE_TYPE_VIDEO_FORMAT_PROPERTIES_KHR;
	}
	d->f.GetPhysicalDeviceVideoFormatPropertiesKHR(d->fisico, &fi, &n, fp);
	for (uint32_t i = 0; i < n; i++) {
		if (fp[i].format == voluto && fp[i].imageType == VK_IMAGE_TYPE_2D
		    && fp[i].imageTiling == VK_IMAGE_TILING_OPTIMAL) {
			*formato = fp[i].format;
			*usi = fp[i].imageUsageFlags;
			*flag = fp[i].imageCreateFlags;
			return true;
		}
	}
	{
		char visti[256] = { 0 };
		for (uint32_t i = 0; i < n; i++) {
			char pezzo[32];
			snprintf(pezzo, sizeof pezzo, "%s%d", i ? "," : "", (int) fp[i].format);
			strncat(visti, pezzo, sizeof visti - strlen(visti) - 1);
		}
		FALLISCI("il driver non offre %s per l'uso 0x%x (VkFormat visti: %s)", nome_formato(voluto),
		         uso, visti);
	}
}

static bool capacita_del_profilo(VulkanVideoDispositivo *d, Profilo *p, VulkanVideoCodec codec,
                                 int profondita, Capacita *c, char *errore, size_t errore_byte)
{
	VkResult r;

	if (codec == VULKANVIDEO_H264 && !d->ha_h264)
		FALLISCI("«%s» non ha VK_KHR_video_encode_h264", d->nome);
	if (codec == VULKANVIDEO_HEVC && !d->ha_h265)
		FALLISCI("«%s» non ha VK_KHR_video_encode_h265", d->nome);
	if (codec == VULKANVIDEO_H264 && profondita != 8)
		FALLISCI("H.264 a %d bit non si apre (solo High a 8 bit)", profondita);
	if (!(d->operazioni & (codec == VULKANVIDEO_H264 ? VK_VIDEO_CODEC_OPERATION_ENCODE_H264_BIT_KHR
	                                                  : VK_VIDEO_CODEC_OPERATION_ENCODE_H265_BIT_KHR)))
		FALLISCI("la coda di codifica di «%s» non dichiara %s", d->nome,
		         codec == VULKANVIDEO_H264 ? "H.264" : "HEVC");

	memset(c, 0, sizeof *c);
	c->video.sType = VK_STRUCTURE_TYPE_VIDEO_CAPABILITIES_KHR;
	c->codifica.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_CAPABILITIES_KHR;
	c->h264.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_CAPABILITIES_KHR;
	c->h265.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_CAPABILITIES_KHR;
	c->video.pNext = &c->codifica;
	c->codifica.pNext = codec == VULKANVIDEO_H264 ? (void *) &c->h264 : (void *) &c->h265;

	r = d->f.GetPhysicalDeviceVideoCapabilitiesKHR(d->fisico, &p->profilo, &c->video);
	if (r != VK_SUCCESS && p->uso.tuningMode != VK_VIDEO_ENCODE_TUNING_MODE_DEFAULT_KHR) {
		/* il driver non accetta il ritardo minimo: si ritenta col difetto, e
		 * lo si dichiara (il chiamante legge `uso.tuningMode`) */
		p->uso.tuningMode = VK_VIDEO_ENCODE_TUNING_MODE_DEFAULT_KHR;
		r = d->f.GetPhysicalDeviceVideoCapabilitiesKHR(d->fisico, &p->profilo, &c->video);
	}
	if (r != VK_SUCCESS)
		FALLISCI("vkGetPhysicalDeviceVideoCapabilitiesKHR (%s %d bit): %s",
		         codec == VULKANVIDEO_H264 ? "H.264 High" : "HEVC Main", profondita, vk_nome(r));
	if (!formati_del_profilo(d, p, profondita, VK_IMAGE_USAGE_VIDEO_ENCODE_SRC_BIT_KHR,
	                         &c->formato_ingresso, &c->usi_ingresso, &c->flag_ingresso, errore,
	                         errore_byte))
		return false;
	if (!formati_del_profilo(d, p, profondita, VK_IMAGE_USAGE_VIDEO_ENCODE_DPB_BIT_KHR,
	                         &c->formato_dpb, &c->usi_dpb, &c->flag_dpb, errore, errore_byte))
		return false;
	c->ingresso_diretto = uso_sostenuto(d, p, c->formato_ingresso,
	                                    VK_IMAGE_USAGE_VIDEO_ENCODE_SRC_BIT_KHR | VK_IMAGE_USAGE_STORAGE_BIT,
	                                    VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT | VK_IMAGE_CREATE_EXTENDED_USAGE_BIT);
	c->ingresso_copia = uso_sostenuto(d, p, c->formato_ingresso,
	                                  VK_IMAGE_USAGE_VIDEO_ENCODE_SRC_BIT_KHR | VK_IMAGE_USAGE_TRANSFER_DST_BIT, 0);
	c->livello_dichiarato = codec == VULKANVIDEO_H264 ? c->h264.maxLevelIdc != STD_VIDEO_H264_LEVEL_IDC_1_0
	                                                   : c->h265.maxLevelIdc != STD_VIDEO_H265_LEVEL_IDC_1_0;
	return true;
}

static void riempi_profilo_capacita(const VulkanVideoDispositivo *d, VulkanVideoCodec codec,
                                    const Capacita *c, VulkanVideoProfiloCapacita *f)
{
	f->codifica = true;
	f->misura_massima_l = c->video.maxCodedExtent.width;
	f->misura_massima_a = c->video.maxCodedExtent.height;
	f->misura_minima_l = c->video.minCodedExtent.width;
	f->misura_minima_a = c->video.minCodedExtent.height;
	f->modi_bitrate = 0;
	if (c->codifica.rateControlModes & VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DISABLED_BIT_KHR)
		f->modi_bitrate |= VULKANVIDEO_RC_CQP;
	if (c->codifica.rateControlModes & VK_VIDEO_ENCODE_RATE_CONTROL_MODE_CBR_BIT_KHR)
		f->modi_bitrate |= VULKANVIDEO_RC_CBR;
	if (c->codifica.rateControlModes & VK_VIDEO_ENCODE_RATE_CONTROL_MODE_VBR_BIT_KHR)
		f->modi_bitrate |= VULKANVIDEO_RC_VBR;
	if (codec == VULKANVIDEO_H264) {
		f->qp_minimo = c->h264.minQp;
		f->qp_massimo = c->h264.maxQp;
		f->livello_massimo_idc = h264_livello_idc(c->h264.maxLevelIdc);
	} else {
		f->qp_minimo = c->h265.minQp;
		f->qp_massimo = c->h265.maxQp;
		f->livello_massimo_idc = hevc_livello_idc(c->h265.maxLevelIdc);
	}
	f->slot_dpb = c->video.maxDpbSlots;
	f->riferimenti_attivi = c->video.maxActiveReferencePictures;
	f->livelli_qualita = c->codifica.maxQualityLevels;
	f->granularita_l = c->codifica.encodeInputPictureGranularity.width;
	f->granularita_a = c->codifica.encodeInputPictureGranularity.height;
	f->intestazioni_dal_driver = d->f.GetEncodedVideoSessionParametersKHR != NULL;
	snprintf(f->formato_ingresso, sizeof f->formato_ingresso, "%s", nome_formato(c->formato_ingresso));
	f->ingresso_scrivibile_dallo_shader = c->ingresso_diretto;
	f->sintassi = codec == VULKANVIDEO_H264 ? c->h264.stdSyntaxFlags : c->h265.stdSyntaxFlags;
	f->cabac = codec == VULKANVIDEO_H264
	           && (c->h264.stdSyntaxFlags & VK_VIDEO_ENCODE_H264_STD_ENTROPY_CODING_MODE_FLAG_SET_BIT_KHR);
	f->transform_8x8 = codec == VULKANVIDEO_H264
	                   && (c->h264.stdSyntaxFlags & VK_VIDEO_ENCODE_H264_STD_TRANSFORM_8X8_MODE_FLAG_SET_BIT_KHR);
	if (!c->livello_dichiarato)
		f->livello_massimo_idc = 0; /* 0 = il driver non lo dichiara */
}

bool vulkanvideo_capacita(const char *nodo, VulkanVideoCapacita *c, char *errore, size_t errore_byte)
{
	VulkanVideoDispositivo *d;
	char perche[256] = { 0 };

	if (!c)
		return false;
	memset(c, 0, sizeof *c);
	d = vulkanvideo_apri_dispositivo(nodo, perche, sizeof perche);
	if (!d) {
		c->vulkan_c_e = false;
		snprintf(c->perche, sizeof c->perche, "%s", perche);
		di(errore, errore_byte, "%s", perche);
		return false;
	}
	c->vulkan_c_e = true;
	snprintf(c->nome_scheda, sizeof c->nome_scheda, "%s", d->nome);
	snprintf(c->driver, sizeof c->driver, "%s", d->driver);
	c->versione_api = d->versione_api;
	c->dmabuf = d->ha_dmabuf;
	{
		struct {
			VulkanVideoCodec codec;
			int prof;
			VulkanVideoProfiloCapacita *dove;
		} tre[3] = { { VULKANVIDEO_H264, 8, &c->h264 }, { VULKANVIDEO_HEVC, 8, &c->hevc },
			         { VULKANVIDEO_HEVC, 10, &c->hevc10 } };
		for (int i = 0; i < 3; i++) {
			Profilo p;
			Capacita cap;
			char e[256] = { 0 };
			profilo_componi(&p, tre[i].codec, tre[i].prof, true);
			if (capacita_del_profilo(d, &p, tre[i].codec, tre[i].prof, &cap, e, sizeof e))
				riempi_profilo_capacita(d, tre[i].codec, &cap, tre[i].dove);
			else
				tre[i].dove->codifica = false;
		}
	}
	vulkanvideo_chiudi_dispositivo(d);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 5. LO STATO E L'APERTURA
 * ═══════════════════════════════════════════════════════════════════════════ */

typedef struct {
	VkImage immagine;
	VkDeviceMemory memoria;
	VkImageView vista;        /* l'immagine intera (COLOR) */
	VkImageView piano_y, piano_uv; /* per lo shader (STORAGE), solo sulla conversione diretta */
	VkImageLayout layout;
} Immagine;

/* Un DMA-BUF importato, in cache: `codificatore.h` spiega perche' la chiave
 * porta la generazione (i numeri di descrittore si riciclano). */
typedef struct {
	bool usata;
	int fd;
	uint64_t generazione;
	uint32_t larghezza, altezza, stride, offset, formato_drm;
	uint64_t modificatore;
	VkImage immagine;
	VkDeviceMemory memoria;
	VkImageView vista;
	bool acquisita;           /* la prima barriera (FOREIGN → noi) e' stata fatta */
} Importazione;

struct VulkanVideo {
	VulkanVideoDispositivo *d;
	VulkanVideoRichiesta r;
	VulkanVideoDichiarazione dich;
	Profilo profilo;
	Capacita cap;

	VkVideoSessionKHR sessione;
	VkDeviceMemory *memoria_sessione;
	uint32_t memorie_sessione;
	VkVideoSessionParametersKHR parametri;

	/* i parameter set come li abbiamo scritti noi */
	StdVideoH264SequenceParameterSet sps264;
	StdVideoH264SequenceParameterSetVui vui264;
	StdVideoH264PictureParameterSet pps264;
	StdVideoH265VideoParameterSet vps265;
	StdVideoH265SequenceParameterSet sps265;
	StdVideoH265PictureParameterSet pps265;
	StdVideoH265ProfileTierLevel ptl265;
	StdVideoH265DecPicBufMgr dpbm265;
	StdVideoH265SequenceParameterSetVui vui265;
	uint8_t intestazioni[INTESTAZIONI_MAX]; /* SPS+PPS(+VPS) in Annex-B, dal driver */
	size_t intestazioni_byte;

	uint32_t larg_cod, alt_cod;   /* la misura codificata (allineata al blocco) */
	uint32_t larg_img, alt_img;   /* le immagini (allineate anche alla granularita') */
	uint32_t blocco;
	uint32_t ctb;                 /* HEVC */
	bool sao, cu_qp_delta;
	int qp_fisso;                 /* CQP: il QP · VBR: il QP di init_qp come ffmpeg (26/30) */
	int qp_corrente;              /* il QP chiesto (CQP) o il pavimento (VBR) */
	bool rc_da_riprogrammare;     /* VBR: il pavimento e' cambiato */

	Immagine ingresso[INGRESSI];
	unsigned prossimo_ingresso;
	Immagine dpb;                 /* SLOT_DPB strati */
	VkImageView vista_dpb[SLOT_DPB];
	bool dpb_inizializzata;
	/* la conversione indiretta: lo shader scrive qui, poi la copia nei piani */
	Immagine y_tmp, uv_tmp;

	/* i pixel dalla memoria */
	VkBuffer scala;               /* staging */
	VkDeviceMemory scala_memoria;
	void *scala_mappa;
	size_t scala_byte;
	Immagine rgb;                 /* la sorgente RGB sulla scheda */
	VulkanVideoOrdine rgb_ordine;
	bool rgb_c_e;

	Importazione importate[IMPORTAZIONI_MAX];
	uint64_t generazione_vista;

	/* lo shader */
	VkDescriptorSetLayout ds_layout;
	VkPipelineLayout pl_layout;
	VkPipeline pipeline;
	VkDescriptorPool ds_pool;
	VkDescriptorSet ds;
	VkSampler campionatore;

	/* i comandi */
	VkCommandPool pool_calcolo, pool_codifica;
	VkCommandBuffer cb_calcolo, cb_codifica;
	VkFence fence_calcolo, fence_codifica;
	VkQueryPool query;
	bool query_overrides;

	/* i byte */
	VkBuffer bitstream;
	VkDeviceMemory bitstream_memoria;
	void *bitstream_mappa;
	VkDeviceSize bitstream_byte;
	bool bitstream_coerente;
	uint8_t *uscita;
	size_t uscita_capacita, uscita_byte;

	/* la sequenza */
	bool sessione_azzerata;       /* il RESET e' stato dato */
	uint64_t ordine;
	uint32_t nel_gop;
	bool riferimento_valido;
	unsigned slot_rif;            /* lo slot DPB del riferimento */
	uint32_t frame_num, frame_num_rif;
	int32_t poc, poc_rif;
	uint32_t idr_pic_id;
	bool rif_era_idr;
};

static uint32_t tipo_memoria(const VulkanVideoDispositivo *d, uint32_t bits, VkMemoryPropertyFlags voluti)
{
	for (uint32_t i = 0; i < d->memoria.memoryTypeCount; i++)
		if ((bits & (1u << i)) && (d->memoria.memoryTypes[i].propertyFlags & voluti) == voluti)
			return i;
	return UINT32_MAX;
}

static bool memoria_alloca(VulkanVideo *v, const VkMemoryRequirements *req, VkMemoryPropertyFlags voluti,
                   VkMemoryPropertyFlags ripiego, const void *pnext, VkDeviceMemory *mem,
                   VkMemoryPropertyFlags *ottenuti, char *errore, size_t errore_byte)
{
	uint32_t t = tipo_memoria(v->d, req->memoryTypeBits, voluti);
	VkMemoryAllocateInfo ai = { .sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO, .pNext = pnext,
		                        .allocationSize = req->size };
	if (t == UINT32_MAX && ripiego)
		t = tipo_memoria(v->d, req->memoryTypeBits, ripiego);
	if (t == UINT32_MAX)
		t = tipo_memoria(v->d, req->memoryTypeBits, 0);
	if (t == UINT32_MAX)
		FALLISCI("nessun tipo di memoria per bits 0x%x", req->memoryTypeBits);
	ai.memoryTypeIndex = t;
	VK_O_FALLISCI(vkAllocateMemory(v->d->dispositivo, &ai, NULL, mem), "vkAllocateMemory");
	if (ottenuti)
		*ottenuti = v->d->memoria.memoryTypes[t].propertyFlags;
	return true;
}

static void immagine_libera(VulkanVideo *v, Immagine *i)
{
	VkDevice dev = v->d->dispositivo;
	if (i->piano_y)
		vkDestroyImageView(dev, i->piano_y, NULL);
	if (i->piano_uv)
		vkDestroyImageView(dev, i->piano_uv, NULL);
	if (i->vista)
		vkDestroyImageView(dev, i->vista, NULL);
	if (i->immagine)
		vkDestroyImage(dev, i->immagine, NULL);
	if (i->memoria)
		vkFreeMemory(dev, i->memoria, NULL);
	memset(i, 0, sizeof *i);
}

static bool vista(VulkanVideo *v, VkImage img, VkFormat f, VkImageAspectFlags aspetto, uint32_t strato,
                  VkImageView *fuori, char *errore, size_t errore_byte)
{
	VkImageViewCreateInfo vi = {
		.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
		.image = img,
		.viewType = VK_IMAGE_VIEW_TYPE_2D,
		.format = f,
		.subresourceRange = { .aspectMask = aspetto, .levelCount = 1, .baseArrayLayer = strato,
		                      .layerCount = 1 },
	};
	VK_O_FALLISCI(vkCreateImageView(v->d->dispositivo, &vi, NULL, fuori), "vkCreateImageView");
	return true;
}

/* Un'immagine sulla scheda, con la sua memoria.  `profilo` = con la lista dei
 * profili video nella catena (ingresso e DPB). */
static bool immagine_crea(VulkanVideo *v, Immagine *i, VkFormat f, uint32_t l, uint32_t a,
                          uint32_t strati, VkImageUsageFlags uso, VkImageCreateFlags flag,
                          bool profilo, bool condivisa, char *errore, size_t errore_byte)
{
	uint32_t famiglie[2] = { v->d->fam_calcolo, v->d->fam_codifica };
	VkImageCreateInfo ci = {
		.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO,
		.pNext = profilo ? &v->profilo.lista : NULL,
		.flags = flag,
		.imageType = VK_IMAGE_TYPE_2D,
		.format = f,
		.extent = { l, a, 1 },
		.mipLevels = 1,
		.arrayLayers = strati,
		.samples = VK_SAMPLE_COUNT_1_BIT,
		.tiling = VK_IMAGE_TILING_OPTIMAL,
		.usage = uso,
		.sharingMode = (condivisa && v->d->fam_calcolo != v->d->fam_codifica)
		                   ? VK_SHARING_MODE_CONCURRENT : VK_SHARING_MODE_EXCLUSIVE,
		.queueFamilyIndexCount = 2,
		.pQueueFamilyIndices = famiglie,
		.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED,
	};
	VkMemoryRequirements req;

	memset(i, 0, sizeof *i);
	VK_O_FALLISCI(vkCreateImage(v->d->dispositivo, &ci, NULL, &i->immagine), "vkCreateImage");
	vkGetImageMemoryRequirements(v->d->dispositivo, i->immagine, &req);
	if (!memoria_alloca(v, &req, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 0, NULL, &i->memoria, NULL, errore,
	            errore_byte))
		return false;
	VK_O_FALLISCI(vkBindImageMemory(v->d->dispositivo, i->immagine, i->memoria, 0), "vkBindImageMemory");
	i->layout = VK_IMAGE_LAYOUT_UNDEFINED;
	return true;
}

/* ── i parameter set, con i valori di `vadiretta.c` ─────────────────────── */

static void componi_h264(VulkanVideo *v)
{
	uint32_t mb_l = v->larg_cod / 16, mb_a = v->alt_cod / 16;
	uint32_t taglio_dx = (v->larg_cod - v->r.larghezza) / 2;
	uint32_t taglio_giu = (v->alt_cod - v->r.altezza) / 2;
	bool cqp = v->dich.modo_rc == VULKANVIDEO_RC_CQP;

	memset(&v->vui264, 0, sizeof v->vui264);
	v->vui264.flags.video_signal_type_present_flag = 1;
	v->vui264.flags.video_full_range_flag = 0;
	v->vui264.flags.color_description_present_flag = 1;
	v->vui264.flags.timing_info_present_flag = 1;
	v->vui264.flags.fixed_frame_rate_flag = 1;
	v->vui264.flags.bitstream_restriction_flag = 1;
	v->vui264.aspect_ratio_idc = STD_VIDEO_H264_ASPECT_RATIO_IDC_UNSPECIFIED;
	v->vui264.video_format = 5;
	v->vui264.colour_primaries = 1;
	v->vui264.transfer_characteristics = 1;
	v->vui264.matrix_coefficients = 1;
	v->vui264.num_units_in_tick = 1;
	v->vui264.time_scale = 2u * v->r.fotogrammi_al_secondo;
	v->vui264.max_num_reorder_frames = 0;
	v->vui264.max_dec_frame_buffering = 1;

	memset(&v->sps264, 0, sizeof v->sps264);
	v->sps264.flags.constraint_set4_flag = 1;     /* High ⇒ 1 */
	v->sps264.flags.constraint_set5_flag = 1;     /* niente B ⇒ 1 */
	v->sps264.flags.direct_8x8_inference_flag = 1;
	v->sps264.flags.frame_mbs_only_flag = 1;
	v->sps264.flags.frame_cropping_flag = (taglio_dx || taglio_giu) ? 1 : 0;
	v->sps264.flags.vui_parameters_present_flag = 1;
	v->sps264.profile_idc = STD_VIDEO_H264_PROFILE_IDC_HIGH;
	v->sps264.level_idc = h264_livello_enum(v->dich.livello_idc);
	v->sps264.chroma_format_idc = STD_VIDEO_H264_CHROMA_FORMAT_IDC_420;
	v->sps264.seq_parameter_set_id = 0;
	v->sps264.bit_depth_luma_minus8 = 0;
	v->sps264.bit_depth_chroma_minus8 = 0;
	v->sps264.log2_max_frame_num_minus4 = 4;      /* frame_num su 8 bit */
	v->sps264.pic_order_cnt_type = STD_VIDEO_H264_POC_TYPE_2;
	v->sps264.log2_max_pic_order_cnt_lsb_minus4 = 0;
	v->sps264.max_num_ref_frames = 1;
	v->sps264.pic_width_in_mbs_minus1 = mb_l - 1;
	v->sps264.pic_height_in_map_units_minus1 = mb_a - 1;
	v->sps264.frame_crop_right_offset = taglio_dx;
	v->sps264.frame_crop_bottom_offset = taglio_giu;
	v->sps264.pSequenceParameterSetVui = &v->vui264;

	/* ⛔ CABAC e transform_8x8 (High) si scrivono SOLO se il driver dichiara di
	 *    onorarli (`stdSyntaxFlags`): `[M]` 1 ott 2026 su RADV con tutt'e due
	 *    accesi a prescindere il flusso non si decodificava («error while
	 *    decoding MB 0 0») — l'hardware codificava in un modo e il PPS ne
	 *    dichiarava un altro. */
	memset(&v->pps264, 0, sizeof v->pps264);
	v->pps264.flags.transform_8x8_mode_flag =
	    (v->cap.h264.stdSyntaxFlags & VK_VIDEO_ENCODE_H264_STD_TRANSFORM_8X8_MODE_FLAG_SET_BIT_KHR) ? 1 : 0;
	v->pps264.flags.entropy_coding_mode_flag =
	    (v->cap.h264.stdSyntaxFlags & VK_VIDEO_ENCODE_H264_STD_ENTROPY_CODING_MODE_FLAG_SET_BIT_KHR) ? 1 : 0;
	v->pps264.flags.deblocking_filter_control_present_flag = 0;
	v->pps264.seq_parameter_set_id = 0;
	v->pps264.pic_parameter_set_id = 0;
	v->pps264.num_ref_idx_l0_default_active_minus1 = 0;
	v->pps264.num_ref_idx_l1_default_active_minus1 = 0;
	v->pps264.weighted_bipred_idc = STD_VIDEO_H264_WEIGHTED_BIPRED_IDC_DEFAULT;
	v->pps264.pic_init_qp_minus26 = (int8_t) (v->qp_fisso - 26);
	(void) cqp;
}

static void componi_h265(VulkanVideo *v)
{
	uint32_t taglio_dx = (v->larg_cod - v->r.larghezza) >> 1;
	uint32_t taglio_giu = (v->alt_cod - v->r.altezza) >> 1;
	unsigned log2_ctb = (unsigned) log2_intero(v->ctb);
	VkVideoEncodeH265TransformBlockSizeFlagsKHR tb = v->cap.h265.transformBlockSizes;
	unsigned log2_max_tb = (tb & VK_VIDEO_ENCODE_H265_TRANSFORM_BLOCK_SIZE_32_BIT_KHR) ? 5
	                       : (tb & VK_VIDEO_ENCODE_H265_TRANSFORM_BLOCK_SIZE_16_BIT_KHR) ? 4 : 3;
	unsigned log2_min_tb = (tb & VK_VIDEO_ENCODE_H265_TRANSFORM_BLOCK_SIZE_4_BIT_KHR) ? 2 : 3;
	if (log2_max_tb > log2_ctb)
		log2_max_tb = log2_ctb;

	memset(&v->ptl265, 0, sizeof v->ptl265);
	v->ptl265.flags.general_progressive_source_flag = 1;
	v->ptl265.flags.general_non_packed_constraint_flag = 1;
	v->ptl265.flags.general_frame_only_constraint_flag = 1;
	v->ptl265.general_profile_idc = v->r.profondita == 10 ? STD_VIDEO_H265_PROFILE_IDC_MAIN_10
	                                                      : STD_VIDEO_H265_PROFILE_IDC_MAIN;
	v->ptl265.general_level_idc = hevc_livello_enum(v->dich.livello_idc);

	memset(&v->dpbm265, 0, sizeof v->dpbm265);
	v->dpbm265.max_dec_pic_buffering_minus1[0] = 1;
	v->dpbm265.max_num_reorder_pics[0] = 0;
	v->dpbm265.max_latency_increase_plus1[0] = 0;

	memset(&v->vps265, 0, sizeof v->vps265);
	v->vps265.flags.vps_temporal_id_nesting_flag = 1;
	v->vps265.flags.vps_timing_info_present_flag = 1;
	v->vps265.flags.vps_poc_proportional_to_timing_flag = 1;
	v->vps265.vps_video_parameter_set_id = 0;
	v->vps265.vps_max_sub_layers_minus1 = 0;
	v->vps265.vps_num_units_in_tick = 1;
	v->vps265.vps_time_scale = v->r.fotogrammi_al_secondo;
	v->vps265.vps_num_ticks_poc_diff_one_minus1 = 0;
	v->vps265.pDecPicBufMgr = &v->dpbm265;
	v->vps265.pProfileTierLevel = &v->ptl265;

	memset(&v->vui265, 0, sizeof v->vui265);
	v->vui265.flags.video_signal_type_present_flag = 1;
	v->vui265.flags.colour_description_present_flag = 1;
	v->vui265.flags.vui_timing_info_present_flag = 1;
	v->vui265.flags.vui_poc_proportional_to_timing_flag = 1;
	v->vui265.flags.bitstream_restriction_flag = 1;
	v->vui265.flags.motion_vectors_over_pic_boundaries_flag = 1;
	v->vui265.flags.restricted_ref_pic_lists_flag = 1;
	v->vui265.video_format = 5;
	v->vui265.colour_primaries = 1;
	v->vui265.transfer_characteristics = 1;
	v->vui265.matrix_coeffs = 1;
	v->vui265.vui_num_units_in_tick = 1;
	v->vui265.vui_time_scale = v->r.fotogrammi_al_secondo;
	v->vui265.log2_max_mv_length_horizontal = 15;
	v->vui265.log2_max_mv_length_vertical = 15;

	memset(&v->sps265, 0, sizeof v->sps265);
	v->sps265.flags.sps_temporal_id_nesting_flag = 1;
	v->sps265.flags.conformance_window_flag = (taglio_dx || taglio_giu) ? 1 : 0;
	v->sps265.flags.amp_enabled_flag = 1;
	v->sps265.flags.sample_adaptive_offset_enabled_flag = v->sao;
	v->sps265.flags.sps_temporal_mvp_enabled_flag = 0;
	v->sps265.flags.vui_parameters_present_flag = 1;
	v->sps265.chroma_format_idc = STD_VIDEO_H265_CHROMA_FORMAT_IDC_420;
	v->sps265.pic_width_in_luma_samples = v->larg_cod;
	v->sps265.pic_height_in_luma_samples = v->alt_cod;
	v->sps265.sps_video_parameter_set_id = 0;
	v->sps265.sps_max_sub_layers_minus1 = 0;
	v->sps265.sps_seq_parameter_set_id = 0;
	v->sps265.bit_depth_luma_minus8 = (uint8_t) (v->r.profondita - 8);
	v->sps265.bit_depth_chroma_minus8 = (uint8_t) (v->r.profondita - 8);
	v->sps265.log2_max_pic_order_cnt_lsb_minus4 = 8;
	v->sps265.log2_min_luma_coding_block_size_minus3 = 0;             /* CB minimo 8 */
	v->sps265.log2_diff_max_min_luma_coding_block_size = (uint8_t) (log2_ctb - 3);
	v->sps265.log2_min_luma_transform_block_size_minus2 = (uint8_t) (log2_min_tb - 2);
	v->sps265.log2_diff_max_min_luma_transform_block_size = (uint8_t) (log2_max_tb - log2_min_tb);
	v->sps265.max_transform_hierarchy_depth_inter = (uint8_t) (log2_ctb - log2_min_tb);
	v->sps265.max_transform_hierarchy_depth_intra = (uint8_t) (log2_ctb - log2_min_tb);
	v->sps265.num_short_term_ref_pic_sets = 0;
	v->sps265.conf_win_right_offset = taglio_dx;
	v->sps265.conf_win_bottom_offset = taglio_giu;
	v->sps265.pProfileTierLevel = &v->ptl265;
	v->sps265.pDecPicBufMgr = &v->dpbm265;
	v->sps265.pSequenceParameterSetVui = &v->vui265;

	memset(&v->pps265, 0, sizeof v->pps265);
	v->pps265.flags.cu_qp_delta_enabled_flag = v->cu_qp_delta;
	v->pps265.flags.pps_loop_filter_across_slices_enabled_flag = 1;
	v->pps265.flags.transform_skip_enabled_flag =
	    (v->cap.h265.stdSyntaxFlags & VK_VIDEO_ENCODE_H265_STD_TRANSFORM_SKIP_ENABLED_FLAG_SET_BIT_KHR) ? 1 : 0;
	v->pps265.pps_pic_parameter_set_id = 0;
	v->pps265.pps_seq_parameter_set_id = 0;
	v->pps265.sps_video_parameter_set_id = 0;
	v->pps265.init_qp_minus26 = (int8_t) (v->qp_fisso - 26);
	v->pps265.diff_cu_qp_delta_depth = v->cu_qp_delta ? (uint8_t) (log2_ctb - 3) : 0;
	v->pps265.log2_parallel_merge_level_minus2 = 0;
}

/* Le intestazioni dal driver, un parameter set per chiamata, ciascuno con il
 * suo codice di inizio se il driver non lo mette. */
static bool prendi_intestazione(VulkanVideo *v, bool vps, bool sps, bool pps, char *errore,
                                size_t errore_byte)
{
	VkVideoEncodeH264SessionParametersGetInfoKHR g264 = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_GET_INFO_KHR,
		.writeStdSPS = sps, .writeStdPPS = pps, .stdSPSId = 0, .stdPPSId = 0,
	};
	VkVideoEncodeH265SessionParametersGetInfoKHR g265 = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_SESSION_PARAMETERS_GET_INFO_KHR,
		.writeStdVPS = vps, .writeStdSPS = sps, .writeStdPPS = pps,
	};
	VkVideoEncodeSessionParametersGetInfoKHR gi = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_SESSION_PARAMETERS_GET_INFO_KHR,
		.pNext = v->r.codec == VULKANVIDEO_H264 ? (void *) &g264 : (void *) &g265,
		.videoSessionParameters = v->parametri,
	};
	VkVideoEncodeH264SessionParametersFeedbackInfoKHR f264 = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_FEEDBACK_INFO_KHR };
	VkVideoEncodeH265SessionParametersFeedbackInfoKHR f265 = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_SESSION_PARAMETERS_FEEDBACK_INFO_KHR };
	VkVideoEncodeSessionParametersFeedbackInfoKHR fb = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_SESSION_PARAMETERS_FEEDBACK_INFO_KHR,
		.pNext = v->r.codec == VULKANVIDEO_H264 ? (void *) &f264 : (void *) &f265,
	};
	size_t n = 0;
	uint8_t tmp[INTESTAZIONI_MAX];
	VkResult r;

	r = v->d->f.GetEncodedVideoSessionParametersKHR(v->d->dispositivo, &gi, &fb, &n, NULL);
	if (r != VK_SUCCESS)
		FALLISCI("vkGetEncodedVideoSessionParametersKHR (misura): %s", vk_nome(r));
	if (!n || n > sizeof tmp)
		FALLISCI("intestazione di %zu byte: fuori misura", n);
	r = v->d->f.GetEncodedVideoSessionParametersKHR(v->d->dispositivo, &gi, &fb, &n, tmp);
	if (r != VK_SUCCESS)
		FALLISCI("vkGetEncodedVideoSessionParametersKHR: %s", vk_nome(r));
	if (fb.hasOverrides)
		v->dich.driver_ha_cambiato_parametri = true;
	{
		bool con_codice = n >= 4 && tmp[0] == 0 && tmp[1] == 0 && (tmp[2] == 1 || (tmp[2] == 0 && tmp[3] == 1));
		size_t serve = n + (con_codice ? 0 : 4);
		if (v->intestazioni_byte + serve > sizeof v->intestazioni)
			FALLISCI("le intestazioni superano %zu byte", sizeof v->intestazioni);
		if (!con_codice) {
			memcpy(v->intestazioni + v->intestazioni_byte, "\0\0\0\1", 4);
			v->intestazioni_byte += 4;
		}
		memcpy(v->intestazioni + v->intestazioni_byte, tmp, n);
		v->intestazioni_byte += n;
	}
	return true;
}

/*
 * ⛔ IL LIVELLO CHE RADV SCRIVE NELL'HEVC: `[M]` 1 ott 2026, Mesa 25.0.7, per
 *    un livello 4.0 il VPS e l'SPS portano `general_level_idc = 40` invece di
 *    120 (= 4.0 × 30, H.265 A.4): il driver usa l'alfabeto di H.264 (× 10).
 *    ffprobe lo legge come «40», e la stringa per il browser diventerebbe
 *    `hev1.1.6.L40.B0` — un livello che non esiste.  ⇒ Il byte si corregge
 *    QUI, nei byte che il driver ci ha reso, e si dichiara nel registro.
 *
 * Dove sta: il `general_level_idc` e' l'ULTIMO byte del profile_tier_level
 * (7.3.3: 2+1+5 bit, 32 bit di compatibilita', 48 bit di vincoli, 8 bit di
 * livello = 12 byte), che nel VPS comincia al byte 4 dell'RBSP e nell'SPS al
 * byte 1.  ⚠ Si cammina sull'RBSP CONTANDO i byte di emulazione (`00 00 03`):
 * nel VPS ce ne sono, e la posizione nel NAL non e' quella nell'RBSP.
 */
static void correggi_livello_hevc(VulkanVideo *v)
{
	size_t i = 0;
	int corretti = 0;

	while (i + 4 <= v->intestazioni_byte) {
		/* il prossimo NAL: dopo `00 00 00 01` (o `00 00 01`) */
		size_t inizio;
		if (v->intestazioni[i] == 0 && v->intestazioni[i + 1] == 0 && v->intestazioni[i + 2] == 0 && v->intestazioni[i + 3] == 1)
			inizio = i + 4;
		else if (v->intestazioni[i] == 0 && v->intestazioni[i + 1] == 0 && v->intestazioni[i + 2] == 1)
			inizio = i + 3;
		else {
			i++;
			continue;
		}
		{
			unsigned tipo = (v->intestazioni[inizio] >> 1) & 0x3f;
			size_t rbsp_voluto = tipo == 32 ? 4 + 11 : tipo == 33 ? 1 + 11 : 0; /* VPS: 4+11 · SPS: 1+11 */
			size_t pos = inizio + 2, rbsp = 0;
			int zeri = 0;
			if (!rbsp_voluto) {
				i = inizio;
				continue;
			}
			/* cammina sull'RBSP fino al byte voluto, saltando gli `03` di emulazione */
			while (pos < v->intestazioni_byte) {
				uint8_t b = v->intestazioni[pos];
				if (zeri >= 2 && b == 3) {
					zeri = 0;
					pos++;
					continue;
				}
				if (rbsp == rbsp_voluto)
					break;
				zeri = b == 0 ? zeri + 1 : 0;
				rbsp++;
				pos++;
			}
			if (pos < v->intestazioni_byte && rbsp == rbsp_voluto
			    && v->intestazioni[pos] != (uint8_t) v->dich.livello_idc) {
				registro_dice(REG_CODIFICA,
				              "⚠ vulkanvideo HEVC: il driver ha scritto general_level_idc %u nel %s, il livello "
				              "e' %d: corretto nei byte (RADV usa l'alfabeto di H.264)",
				              v->intestazioni[pos], tipo == 32 ? "VPS" : "SPS", v->dich.livello_idc);
				v->intestazioni[pos] = (uint8_t) v->dich.livello_idc;
				corretti++;
			}
			i = inizio;
		}
	}
	v->dich.livello_corretto_nei_byte = corretti > 0;
}

static bool apri_sessione(VulkanVideo *v, char *errore, size_t errore_byte)
{
	VkDevice dev = v->d->dispositivo;
	bool h264 = v->r.codec == VULKANVIDEO_H264;
	VkVideoEncodeH264SessionCreateInfoKHR s264 = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_CREATE_INFO_KHR,
		.useMaxLevelIdc = VK_TRUE, .maxLevelIdc = h264_livello_enum(v->dich.livello_idc),
	};
	VkVideoEncodeH265SessionCreateInfoKHR s265 = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_SESSION_CREATE_INFO_KHR,
		.useMaxLevelIdc = VK_TRUE, .maxLevelIdc = hevc_livello_enum(v->dich.livello_idc),
	};
	VkVideoSessionCreateInfoKHR sc = {
		.sType = VK_STRUCTURE_TYPE_VIDEO_SESSION_CREATE_INFO_KHR,
		.pNext = !v->cap.livello_dichiarato ? NULL : h264 ? (void *) &s264 : (void *) &s265,
		.queueFamilyIndex = v->d->fam_codifica,
		.pVideoProfile = &v->profilo.profilo,
		.pictureFormat = v->cap.formato_ingresso,
		.maxCodedExtent = { v->larg_cod, v->alt_cod },
		.referencePictureFormat = v->cap.formato_dpb,
		.maxDpbSlots = SLOT_DPB,
		.maxActiveReferencePictures = 1,
		.pStdHeaderVersion = &v->cap.video.stdHeaderVersion,
	};
	uint32_t n = 0;
	VkVideoSessionMemoryRequirementsKHR req[8];
	VkBindVideoSessionMemoryInfoKHR bind[8];

	VK_O_FALLISCI(v->d->f.CreateVideoSessionKHR(dev, &sc, NULL, &v->sessione), "vkCreateVideoSessionKHR");
	VK_O_FALLISCI(v->d->f.GetVideoSessionMemoryRequirementsKHR(dev, v->sessione, &n, NULL),
	              "vkGetVideoSessionMemoryRequirementsKHR");
	if (n > 8)
		FALLISCI("la sessione vuole %u legami di memoria: troppi", n);
	for (uint32_t i = 0; i < n; i++) {
		memset(&req[i], 0, sizeof req[i]);
		req[i].sType = VK_STRUCTURE_TYPE_VIDEO_SESSION_MEMORY_REQUIREMENTS_KHR;
	}
	VK_O_FALLISCI(v->d->f.GetVideoSessionMemoryRequirementsKHR(dev, v->sessione, &n, req),
	              "vkGetVideoSessionMemoryRequirementsKHR");
	v->memoria_sessione = calloc(n ? n : 1, sizeof *v->memoria_sessione);
	if (!v->memoria_sessione)
		FALLISCI("niente memoria");
	for (uint32_t i = 0; i < n; i++) {
		if (!memoria_alloca(v, &req[i].memoryRequirements, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 0, NULL,
		            &v->memoria_sessione[i], NULL, errore, errore_byte))
			return false;
		v->memorie_sessione = i + 1;
		bind[i] = (VkBindVideoSessionMemoryInfoKHR){
			.sType = VK_STRUCTURE_TYPE_BIND_VIDEO_SESSION_MEMORY_INFO_KHR,
			.memoryBindIndex = req[i].memoryBindIndex,
			.memory = v->memoria_sessione[i],
			.memoryOffset = 0,
			.memorySize = req[i].memoryRequirements.size,
		};
	}
	if (n)
		VK_O_FALLISCI(v->d->f.BindVideoSessionMemoryKHR(dev, v->sessione, n, bind),
		              "vkBindVideoSessionMemoryKHR");

	/* i parametri */
	if (h264) {
		componi_h264(v);
		VkVideoEncodeH264SessionParametersAddInfoKHR add = {
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_ADD_INFO_KHR,
			.stdSPSCount = 1, .pStdSPSs = &v->sps264, .stdPPSCount = 1, .pStdPPSs = &v->pps264,
		};
		VkVideoEncodeH264SessionParametersCreateInfoKHR pc = {
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_SESSION_PARAMETERS_CREATE_INFO_KHR,
			.maxStdSPSCount = 1, .maxStdPPSCount = 1, .pParametersAddInfo = &add,
		};
		VkVideoSessionParametersCreateInfoKHR ci = {
			.sType = VK_STRUCTURE_TYPE_VIDEO_SESSION_PARAMETERS_CREATE_INFO_KHR,
			.pNext = &pc, .videoSession = v->sessione,
		};
		VK_O_FALLISCI(v->d->f.CreateVideoSessionParametersKHR(dev, &ci, NULL, &v->parametri),
		              "vkCreateVideoSessionParametersKHR (H.264)");
	} else {
		componi_h265(v);
		VkVideoEncodeH265SessionParametersAddInfoKHR add = {
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_SESSION_PARAMETERS_ADD_INFO_KHR,
			.stdVPSCount = 1, .pStdVPSs = &v->vps265, .stdSPSCount = 1, .pStdSPSs = &v->sps265,
			.stdPPSCount = 1, .pStdPPSs = &v->pps265,
		};
		VkVideoEncodeH265SessionParametersCreateInfoKHR pc = {
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_SESSION_PARAMETERS_CREATE_INFO_KHR,
			.maxStdVPSCount = 1, .maxStdSPSCount = 1, .maxStdPPSCount = 1, .pParametersAddInfo = &add,
		};
		VkVideoSessionParametersCreateInfoKHR ci = {
			.sType = VK_STRUCTURE_TYPE_VIDEO_SESSION_PARAMETERS_CREATE_INFO_KHR,
			.pNext = &pc, .videoSession = v->sessione,
		};
		VK_O_FALLISCI(v->d->f.CreateVideoSessionParametersKHR(dev, &ci, NULL, &v->parametri),
		              "vkCreateVideoSessionParametersKHR (HEVC)");
	}
	/* le intestazioni, una per chiamata */
	v->intestazioni_byte = 0;
	if (!h264 && !prendi_intestazione(v, true, false, false, errore, errore_byte))
		return false;
	if (!prendi_intestazione(v, false, true, false, errore, errore_byte))
		return false;
	if (!prendi_intestazione(v, false, false, true, errore, errore_byte))
		return false;
	v->dich.intestazioni_dal_driver = true;
	if (!h264)
		correggi_livello_hevc(v);
	v->dich.intestazioni_byte = v->intestazioni_byte;
	return true;
}

static bool apri_immagini(VulkanVideo *v, char *errore, size_t errore_byte)
{
	bool p10 = v->r.profondita == 10;
	VkFormat f_y = p10 ? VK_FORMAT_R16_UNORM : VK_FORMAT_R8_UNORM;
	VkFormat f_uv = p10 ? VK_FORMAT_R16G16_UNORM : VK_FORMAT_R8G8_UNORM;

	for (unsigned i = 0; i < INGRESSI; i++) {
		Immagine *im = &v->ingresso[i];
		VkImageUsageFlags uso = VK_IMAGE_USAGE_VIDEO_ENCODE_SRC_BIT_KHR
		                        | (v->dich.conversione_diretta ? VK_IMAGE_USAGE_STORAGE_BIT
		                                                       : VK_IMAGE_USAGE_TRANSFER_DST_BIT);
		VkImageCreateFlags flag = v->dich.conversione_diretta
		                              ? (VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT | VK_IMAGE_CREATE_EXTENDED_USAGE_BIT) : 0;
		if (!immagine_crea(v, im, v->cap.formato_ingresso, v->larg_img, v->alt_img, 1, uso, flag, true,
		                   true, errore, errore_byte))
			return false;
		if (!vista(v, im->immagine, v->cap.formato_ingresso, VK_IMAGE_ASPECT_COLOR_BIT, 0, &im->vista,
		           errore, errore_byte))
			return false;
		if (v->dich.conversione_diretta) {
			if (!vista(v, im->immagine, f_y, VK_IMAGE_ASPECT_PLANE_0_BIT, 0, &im->piano_y, errore, errore_byte)
			    || !vista(v, im->immagine, f_uv, VK_IMAGE_ASPECT_PLANE_1_BIT, 0, &im->piano_uv, errore,
			              errore_byte))
				return false;
		}
	}
	if (!v->dich.conversione_diretta) {
		if (!immagine_crea(v, &v->y_tmp, f_y, v->larg_img, v->alt_img, 1,
		                   VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT, 0, false, false,
		                   errore, errore_byte)
		    || !vista(v, v->y_tmp.immagine, f_y, VK_IMAGE_ASPECT_COLOR_BIT, 0, &v->y_tmp.vista, errore,
		              errore_byte))
			return false;
		if (!immagine_crea(v, &v->uv_tmp, f_uv, v->larg_img / 2, v->alt_img / 2, 1,
		                   VK_IMAGE_USAGE_STORAGE_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT, 0, false, false,
		                   errore, errore_byte)
		    || !vista(v, v->uv_tmp.immagine, f_uv, VK_IMAGE_ASPECT_COLOR_BIT, 0, &v->uv_tmp.vista, errore,
		              errore_byte))
			return false;
	}
	/* il DPB: uno strato per slot, nello stesso oggetto (vale con e senza
	 * SEPARATE_REFERENCE_IMAGES) */
	if (!immagine_crea(v, &v->dpb, v->cap.formato_dpb, v->larg_img, v->alt_img, SLOT_DPB,
	                   VK_IMAGE_USAGE_VIDEO_ENCODE_DPB_BIT_KHR, 0, true, false, errore, errore_byte))
		return false;
	for (unsigned i = 0; i < SLOT_DPB; i++)
		if (!vista(v, v->dpb.immagine, v->cap.formato_dpb, VK_IMAGE_ASPECT_COLOR_BIT, i, &v->vista_dpb[i],
		           errore, errore_byte))
			return false;
	return true;
}

static bool apri_shader(VulkanVideo *v, char *errore, size_t errore_byte)
{
	VkDevice dev = v->d->dispositivo;
	VkDescriptorSetLayoutBinding b[3] = {
		{ .binding = 0, .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, .descriptorCount = 1,
		  .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT },
		{ .binding = 1, .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, .descriptorCount = 1,
		  .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT },
		{ .binding = 2, .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, .descriptorCount = 1,
		  .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT },
	};
	VkDescriptorSetLayoutCreateInfo dl = { .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
		                                   .bindingCount = 3, .pBindings = b };
	VkPushConstantRange pc = { .stageFlags = VK_SHADER_STAGE_COMPUTE_BIT, .offset = 0, .size = 20 };
	VkPipelineLayoutCreateInfo pl = { .sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
		                              .setLayoutCount = 1, .pSetLayouts = &v->ds_layout,
		                              .pushConstantRangeCount = 1, .pPushConstantRanges = &pc };
	VkShaderModuleCreateInfo sm = { .sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
		                            .codeSize = sizeof SPV_RGB_NV12, .pCode = SPV_RGB_NV12 };
	VkShaderModule modulo;
	VkComputePipelineCreateInfo cp = {
		.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
		.stage = { .sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
		           .stage = VK_SHADER_STAGE_COMPUTE_BIT, .pName = "main" },
	};
	VkDescriptorPoolSize ps[2] = { { VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1 },
		                           { VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, 2 } };
	VkDescriptorPoolCreateInfo dp = { .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO, .maxSets = 1,
		                              .poolSizeCount = 2, .pPoolSizes = ps };
	VkDescriptorSetAllocateInfo da = { .sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
		                               .descriptorSetCount = 1, .pSetLayouts = &v->ds_layout };
	VkSamplerCreateInfo sa = { .sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
		                       .magFilter = VK_FILTER_NEAREST, .minFilter = VK_FILTER_NEAREST,
		                       .addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
		                       .addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
		                       .addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE };
	VkResult r;

	VK_O_FALLISCI(vkCreateDescriptorSetLayout(dev, &dl, NULL, &v->ds_layout), "vkCreateDescriptorSetLayout");
	VK_O_FALLISCI(vkCreatePipelineLayout(dev, &pl, NULL, &v->pl_layout), "vkCreatePipelineLayout");
	VK_O_FALLISCI(vkCreateShaderModule(dev, &sm, NULL, &modulo), "vkCreateShaderModule");
	cp.stage.module = modulo;
	cp.layout = v->pl_layout;
	r = vkCreateComputePipelines(dev, VK_NULL_HANDLE, 1, &cp, NULL, &v->pipeline);
	vkDestroyShaderModule(dev, modulo, NULL);
	if (r != VK_SUCCESS)
		FALLISCI("vkCreateComputePipelines: %s", vk_nome(r));
	VK_O_FALLISCI(vkCreateDescriptorPool(dev, &dp, NULL, &v->ds_pool), "vkCreateDescriptorPool");
	da.descriptorPool = v->ds_pool;
	VK_O_FALLISCI(vkAllocateDescriptorSets(dev, &da, &v->ds), "vkAllocateDescriptorSets");
	VK_O_FALLISCI(vkCreateSampler(dev, &sa, NULL, &v->campionatore), "vkCreateSampler");
	return true;
}

static bool apri_comandi(VulkanVideo *v, char *errore, size_t errore_byte)
{
	VkDevice dev = v->d->dispositivo;
	VkCommandPoolCreateInfo pc = { .sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
		                           .flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT };
	VkCommandBufferAllocateInfo ca = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
		                               .level = VK_COMMAND_BUFFER_LEVEL_PRIMARY, .commandBufferCount = 1 };
	VkFenceCreateInfo fc = { .sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
	VkQueryPoolVideoEncodeFeedbackCreateInfoKHR qf = {
		.sType = VK_STRUCTURE_TYPE_QUERY_POOL_VIDEO_ENCODE_FEEDBACK_CREATE_INFO_KHR,
		.encodeFeedbackFlags = VK_VIDEO_ENCODE_FEEDBACK_BITSTREAM_BUFFER_OFFSET_BIT_KHR
		                       | VK_VIDEO_ENCODE_FEEDBACK_BITSTREAM_BYTES_WRITTEN_BIT_KHR,
	};
	Profilo pq = v->profilo; /* una copia: la catena del query pool continua dopo l'uso */
	VkQueryPoolCreateInfo qc = { .sType = VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO,
		                         .queryType = VK_QUERY_TYPE_VIDEO_ENCODE_FEEDBACK_KHR, .queryCount = 1 };

	pc.queueFamilyIndex = v->d->fam_calcolo;
	VK_O_FALLISCI(vkCreateCommandPool(dev, &pc, NULL, &v->pool_calcolo), "vkCreateCommandPool (calcolo)");
	pc.queueFamilyIndex = v->d->fam_codifica;
	VK_O_FALLISCI(vkCreateCommandPool(dev, &pc, NULL, &v->pool_codifica), "vkCreateCommandPool (codifica)");
	ca.commandPool = v->pool_calcolo;
	VK_O_FALLISCI(vkAllocateCommandBuffers(dev, &ca, &v->cb_calcolo), "vkAllocateCommandBuffers");
	ca.commandPool = v->pool_codifica;
	VK_O_FALLISCI(vkAllocateCommandBuffers(dev, &ca, &v->cb_codifica), "vkAllocateCommandBuffers");
	VK_O_FALLISCI(vkCreateFence(dev, &fc, NULL, &v->fence_calcolo), "vkCreateFence");
	VK_O_FALLISCI(vkCreateFence(dev, &fc, NULL, &v->fence_codifica), "vkCreateFence");

	if (v->cap.codifica.supportedEncodeFeedbackFlags & VK_VIDEO_ENCODE_FEEDBACK_BITSTREAM_HAS_OVERRIDES_BIT_KHR) {
		qf.encodeFeedbackFlags |= VK_VIDEO_ENCODE_FEEDBACK_BITSTREAM_HAS_OVERRIDES_BIT_KHR;
		v->query_overrides = true;
	}
	/* la catena: QueryPoolCreateInfo → profilo → (codec) → uso → feedback.
	 * ⚠ I puntatori interni della copia vanno rifatti: puntano all'originale. */
	pq.profilo.pNext = v->r.codec == VULKANVIDEO_H264 ? (void *) &pq.h264 : (void *) &pq.h265;
	pq.h264.pNext = &pq.uso;
	pq.h265.pNext = &pq.uso;
	pq.uso.pNext = &qf;
	qc.pNext = &pq.profilo;
	VK_O_FALLISCI(vkCreateQueryPool(dev, &qc, NULL, &v->query), "vkCreateQueryPool (video encode feedback)");
	return true;
}

static bool apri_buffer(VulkanVideo *v, char *errore, size_t errore_byte)
{
	VkDevice dev = v->d->dispositivo;
	VkDeviceSize all = v->cap.video.minBitstreamBufferSizeAlignment ? v->cap.video.minBitstreamBufferSizeAlignment : 1;
	VkBufferCreateInfo bc = {
		.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
		.pNext = &v->profilo.lista,
		.usage = VK_BUFFER_USAGE_VIDEO_ENCODE_DST_BIT_KHR,
		.sharingMode = VK_SHARING_MODE_EXCLUSIVE,
	};
	VkMemoryRequirements req;
	VkMemoryPropertyFlags ottenuti = 0;

	v->bitstream_byte = (VkDeviceSize) 3 * v->larg_cod * v->alt_cod + CODED_MARGINE;
	v->bitstream_byte = (v->bitstream_byte + all - 1) / all * all;
	bc.size = v->bitstream_byte;
	VK_O_FALLISCI(vkCreateBuffer(dev, &bc, NULL, &v->bitstream), "vkCreateBuffer (bitstream)");
	vkGetBufferMemoryRequirements(dev, v->bitstream, &req);
	if (!memoria_alloca(v, &req, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT
	                         | VK_MEMORY_PROPERTY_HOST_CACHED_BIT,
	            VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, NULL,
	            &v->bitstream_memoria, &ottenuti, errore, errore_byte))
		return false;
	if (!(ottenuti & VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT))
		FALLISCI("il buffer dei byte codificati non si puo' leggere dalla CPU (tipi 0x%x)", req.memoryTypeBits);
	v->bitstream_coerente = (ottenuti & VK_MEMORY_PROPERTY_HOST_COHERENT_BIT) != 0;
	VK_O_FALLISCI(vkBindBufferMemory(dev, v->bitstream, v->bitstream_memoria, 0), "vkBindBufferMemory");
	VK_O_FALLISCI(vkMapMemory(dev, v->bitstream_memoria, 0, VK_WHOLE_SIZE, 0, &v->bitstream_mappa), "vkMapMemory");

	v->uscita_capacita = (size_t) v->bitstream_byte + INTESTAZIONI_MAX;
	v->uscita = malloc(v->uscita_capacita);
	if (!v->uscita)
		FALLISCI("niente memoria per l'uscita");
	return true;
}

VulkanVideo *vulkanvideo_apri(VulkanVideoDispositivo *d, const VulkanVideoRichiesta *r, char *errore,
                              size_t errore_byte)
{
	VulkanVideo *v;
	bool hevc;
	uint32_t gran_l, gran_a;

	if (!d || !r || !r->larghezza || !r->altezza) {
		di(errore, errore_byte, "vulkanvideo: richiesta incompleta");
		return NULL;
	}
	hevc = r->codec == VULKANVIDEO_HEVC;
	if (!hevc && r->profondita != 8) {
		di(errore, errore_byte, "vulkanvideo: H.264 a 10 bit non si apre (solo High a 8 bit)");
		return NULL;
	}
	if (r->qp < 1 || r->qp > 51) {
		di(errore, errore_byte, "vulkanvideo: QP %d fuori da 1..51", r->qp);
		return NULL;
	}
	v = calloc(1, sizeof *v);
	if (!v) {
		di(errore, errore_byte, "niente memoria");
		return NULL;
	}
	v->d = d;
	v->r = *r;
	if (!v->r.fotogrammi_al_secondo)
		v->r.fotogrammi_al_secondo = 30;

	profilo_componi(&v->profilo, r->codec, r->profondita, true);
	if (!capacita_del_profilo(d, &v->profilo, r->codec, r->profondita, &v->cap, errore, errore_byte)) {
		vulkanvideo_chiudi(v);
		return NULL;
	}
	v->dich.ritardo_minimo_chiesto = v->profilo.uso.tuningMode == VK_VIDEO_ENCODE_TUNING_MODE_ULTRA_LOW_LATENCY_KHR;
	v->dich.famiglia_codifica = d->fam_codifica;
	v->dich.famiglia_calcolo = d->fam_calcolo;
	snprintf(v->dich.formato_ingresso, sizeof v->dich.formato_ingresso, "%s", nome_formato(v->cap.formato_ingresso));
	v->dich.conversione_diretta = v->cap.ingresso_diretto;
	/* ⚠ Solo per il BANCO: `REMOTIX_VULKAN_CONVERSIONE=copia` forza la strada
	 *   della copia anche dove la diretta c'e', per misurarla e per provare
	 *   il ramo che le altre schede percorreranno.  Non e' un'eccezione per
	 *   scheda: la scelta di serie resta quella letta dal driver. */
	if (getenv("REMOTIX_VULKAN_CONVERSIONE") && strcmp(getenv("REMOTIX_VULKAN_CONVERSIONE"), "copia") == 0)
		v->dich.conversione_diretta = false;
	if (!v->dich.conversione_diretta && !v->cap.ingresso_copia) {
		di(errore, errore_byte, "il formato d'ingresso non si puo' ne' scrivere dallo shader ne' copiare (usi 0x%x)",
		   v->cap.usi_ingresso);
		vulkanvideo_chiudi(v);
		return NULL;
	}

	/* il controllo del bitrate */
	if (r->banda_filo > 0) {
		if (!(v->cap.codifica.rateControlModes & VK_VIDEO_ENCODE_RATE_CONTROL_MODE_VBR_BIT_KHR)) {
			di(errore, errore_byte, "la scheda non dichiara il VBR (modi 0x%x): il tetto di banda non si puo' chiedere",
			   v->cap.codifica.rateControlModes);
			vulkanvideo_chiudi(v);
			return NULL;
		}
		if (r->banda_punto >= r->banda_filo || r->serbatoio_bit <= 0) {
			di(errore, errore_byte, "i numeri del tetto sono guasti: punto %lld, filo %lld, serbatoio %d",
			   (long long) r->banda_punto, (long long) r->banda_filo, r->serbatoio_bit);
			vulkanvideo_chiudi(v);
			return NULL;
		}
		v->dich.modo_rc = VULKANVIDEO_RC_VBR;
		v->qp_fisso = hevc ? 30 : 26;
	} else {
		if (!(v->cap.codifica.rateControlModes & VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DISABLED_BIT_KHR)) {
			di(errore, errore_byte, "la scheda non dichiara il QP costante (modi 0x%x)", v->cap.codifica.rateControlModes);
			vulkanvideo_chiudi(v);
			return NULL;
		}
		v->dich.modo_rc = VULKANVIDEO_RC_CQP;
		v->qp_fisso = r->qp;
	}
	v->qp_corrente = r->qp;
	v->dich.qp_minimo = hevc ? v->cap.h265.minQp : v->cap.h264.minQp;
	v->dich.qp_massimo = hevc ? v->cap.h265.maxQp : v->cap.h264.maxQp;
	if (r->qp < v->dich.qp_minimo || r->qp > v->dich.qp_massimo) {
		di(errore, errore_byte, "QP %d fuori da quel che la scheda dichiara (%d..%d)", r->qp, v->dich.qp_minimo,
		   v->dich.qp_massimo);
		vulkanvideo_chiudi(v);
		return NULL;
	}

	/* le misure: il blocco del codec, poi la granularita' della scheda */
	if (hevc) {
		VkVideoEncodeH265CtbSizeFlagsKHR c = v->cap.h265.ctbSizes;
		v->ctb = (c & VK_VIDEO_ENCODE_H265_CTB_SIZE_64_BIT_KHR) ? 64
		         : (c & VK_VIDEO_ENCODE_H265_CTB_SIZE_32_BIT_KHR) ? 32 : 16;
		v->blocco = v->ctb;
		v->sao = (v->cap.h265.stdSyntaxFlags & VK_VIDEO_ENCODE_H265_STD_SAMPLE_ADAPTIVE_OFFSET_ENABLED_FLAG_SET_BIT_KHR) != 0;
		v->cu_qp_delta = v->dich.modo_rc != VULKANVIDEO_RC_CQP;
		/* la misura codificata: multipla di 16 come fa radeonsi (1920x1088),
		 * con la finestra di conformita' per il resto */
		v->larg_cod = allinea(r->larghezza, 16);
		v->alt_cod = allinea(r->altezza, 16);
	} else {
		v->blocco = 16;
		v->larg_cod = allinea(r->larghezza, 16);
		v->alt_cod = allinea(r->altezza, 16);
	}
	gran_l = v->cap.codifica.encodeInputPictureGranularity.width;
	gran_a = v->cap.codifica.encodeInputPictureGranularity.height;
	/* ⛔⭐ LA MISURA CODIFICATA SI ALLINEA ANCHE ALLA GRANULARITA' DELLA SCHEDA
	 *      (1 ott 2026, il verde di Chrome).  Prima si allineava a 16 e basta:
	 *      a 2544x1344 l'SPS diceva 2544 di larghezza, ma la RX 6800 (RADV,
	 *      granularita' 64x16) codifica a blocchi di 64 ⇒ il flusso da 2544 e'
	 *      ROTTO: `[M]` ffmpeg lo decodifica giusto per poche righe e poi
	 *      verde, Chrome (VA-API Intel) da' la tela tutta (0,136,0).  A 3840 e
	 *      3776 (multipli di 64) non si vedeva.  ⇒ La misura nell'SPS e' quella
	 *      allineata (2560), e il resto lo taglia la finestra di conformita',
	 *      come fa radeonsi in VA-API (1920x1088). */
	if (gran_l > 1 && gran_l % 16 == 0)
		v->larg_cod = allinea(v->larg_cod, gran_l);
	if (gran_a > 1 && gran_a % 16 == 0)
		v->alt_cod = allinea(v->alt_cod, gran_a);
	v->larg_img = allinea(v->larg_cod, gran_l ? gran_l : 1);
	v->alt_img = allinea(v->alt_cod, gran_a ? gran_a : 1);
	v->larg_img = allinea(v->larg_img, v->cap.video.pictureAccessGranularity.width ? v->cap.video.pictureAccessGranularity.width : 1);
	v->alt_img = allinea(v->alt_img, v->cap.video.pictureAccessGranularity.height ? v->cap.video.pictureAccessGranularity.height : 1);
	v->dich.larghezza_codificata = v->larg_cod;
	v->dich.altezza_codificata = v->alt_cod;
	v->dich.blocco = v->blocco;
	if (v->larg_cod > v->cap.video.maxCodedExtent.width || v->alt_cod > v->cap.video.maxCodedExtent.height
	    || v->larg_cod < v->cap.video.minCodedExtent.width || v->alt_cod < v->cap.video.minCodedExtent.height) {
		di(errore, errore_byte, "la misura %ux%u e' fuori da quel che la scheda dichiara (%ux%u … %ux%u)",
		   v->larg_cod, v->alt_cod, v->cap.video.minCodedExtent.width, v->cap.video.minCodedExtent.height,
		   v->cap.video.maxCodedExtent.width, v->cap.video.maxCodedExtent.height);
		vulkanvideo_chiudi(v);
		return NULL;
	}

	/* il livello */
	if (hevc)
		v->dich.livello_idc = r->livello_idc > 0 ? r->livello_idc
		                      : livello_hevc(v->dich.modo_rc == VULKANVIDEO_RC_CQP ? 0 : r->banda_punto,
		                                     v->larg_cod, v->alt_cod, 1);
	else
		v->dich.livello_idc = r->livello_idc > 0 ? r->livello_idc
		                      : livello_h264(v->dich.modo_rc == VULKANVIDEO_RC_CQP ? 0 : r->banda_filo,
		                                     (int) v->r.fotogrammi_al_secondo, v->larg_cod / 16, v->alt_cod / 16, 1);
	if (v->cap.livello_dichiarato) {
		int massimo = hevc ? hevc_livello_idc(v->cap.h265.maxLevelIdc) : h264_livello_idc(v->cap.h264.maxLevelIdc);
		if (v->dich.livello_idc > massimo) {
			di(errore, errore_byte, "livello %d chiesto, la scheda arriva a %d", v->dich.livello_idc, massimo);
			vulkanvideo_chiudi(v);
			return NULL;
		}
	}

	if (!apri_sessione(v, errore, errore_byte) || !apri_immagini(v, errore, errore_byte)
	    || !apri_shader(v, errore, errore_byte) || !apri_comandi(v, errore, errore_byte)
	    || !apri_buffer(v, errore, errore_byte)) {
		vulkanvideo_chiudi(v);
		return NULL;
	}
	v->generazione_vista = 0;
	registro_dice(REG_CODIFICA,
	              "vulkanvideo aperta su «%s» (%s): %s %d bit %ux%u (codificata %ux%u, immagini %ux%u, blocco %u) · "
	              "%s (qp %d) · livello %d%s · intestazioni dal driver %zu byte%s · conversione %s · "
	              "code codifica %u / calcolo %u · ritardo minimo %s · ingresso %s · DPB %u slot",
	              d->nome, d->driver, hevc ? "HEVC" : "H.264", r->profondita, r->larghezza, r->altezza,
	              v->larg_cod, v->alt_cod, v->larg_img, v->alt_img, v->blocco,
	              v->dich.modo_rc == VULKANVIDEO_RC_CQP ? "CQP" : "VBR (QP minimo = qualita' chiesta)", r->qp,
	              v->dich.livello_idc, r->livello_idc > 0 ? " (imposto)" : " (calcolato come ffmpeg)",
	              v->intestazioni_byte, v->dich.driver_ha_cambiato_parametri ? " ⚠ il driver li ha CAMBIATI" : "",
	              v->dich.conversione_diretta ? "diretta nei piani" : "via copia", d->fam_codifica, d->fam_calcolo,
	              v->dich.ritardo_minimo_chiesto ? "chiesto" : "non accettato dal driver",
	              v->dich.formato_ingresso, (unsigned) SLOT_DPB);
	return v;
}

static void importazione_libera(VulkanVideo *v, Importazione *i)
{
	VkDevice dev = v->d->dispositivo;
	if (!i->usata)
		return;
	if (i->vista)
		vkDestroyImageView(dev, i->vista, NULL);
	if (i->immagine)
		vkDestroyImage(dev, i->immagine, NULL);
	if (i->memoria)
		vkFreeMemory(dev, i->memoria, NULL);
	memset(i, 0, sizeof *i);
}

void vulkanvideo_chiudi(VulkanVideo *v)
{
	VkDevice dev;
	if (!v)
		return;
	dev = v->d->dispositivo;
	vkDeviceWaitIdle(dev);
	for (unsigned i = 0; i < IMPORTAZIONI_MAX; i++)
		importazione_libera(v, &v->importate[i]);
	if (v->uscita)
		free(v->uscita);
	if (v->bitstream_mappa)
		vkUnmapMemory(dev, v->bitstream_memoria);
	if (v->bitstream)
		vkDestroyBuffer(dev, v->bitstream, NULL);
	if (v->bitstream_memoria)
		vkFreeMemory(dev, v->bitstream_memoria, NULL);
	if (v->scala_mappa)
		vkUnmapMemory(dev, v->scala_memoria);
	if (v->scala)
		vkDestroyBuffer(dev, v->scala, NULL);
	if (v->scala_memoria)
		vkFreeMemory(dev, v->scala_memoria, NULL);
	if (v->query)
		vkDestroyQueryPool(dev, v->query, NULL);
	if (v->fence_calcolo)
		vkDestroyFence(dev, v->fence_calcolo, NULL);
	if (v->fence_codifica)
		vkDestroyFence(dev, v->fence_codifica, NULL);
	if (v->pool_calcolo)
		vkDestroyCommandPool(dev, v->pool_calcolo, NULL);
	if (v->pool_codifica)
		vkDestroyCommandPool(dev, v->pool_codifica, NULL);
	if (v->campionatore)
		vkDestroySampler(dev, v->campionatore, NULL);
	if (v->ds_pool)
		vkDestroyDescriptorPool(dev, v->ds_pool, NULL);
	if (v->pipeline)
		vkDestroyPipeline(dev, v->pipeline, NULL);
	if (v->pl_layout)
		vkDestroyPipelineLayout(dev, v->pl_layout, NULL);
	if (v->ds_layout)
		vkDestroyDescriptorSetLayout(dev, v->ds_layout, NULL);
	for (unsigned i = 0; i < SLOT_DPB; i++)
		if (v->vista_dpb[i])
			vkDestroyImageView(dev, v->vista_dpb[i], NULL);
	immagine_libera(v, &v->dpb);
	immagine_libera(v, &v->y_tmp);
	immagine_libera(v, &v->uv_tmp);
	immagine_libera(v, &v->rgb);
	for (unsigned i = 0; i < INGRESSI; i++)
		immagine_libera(v, &v->ingresso[i]);
	if (v->parametri)
		v->d->f.DestroyVideoSessionParametersKHR(dev, v->parametri, NULL);
	if (v->sessione)
		v->d->f.DestroyVideoSessionKHR(dev, v->sessione, NULL);
	for (uint32_t i = 0; i < v->memorie_sessione; i++)
		vkFreeMemory(dev, v->memoria_sessione[i], NULL);
	free(v->memoria_sessione);
	free(v);
}

const VulkanVideoDichiarazione *vulkanvideo_dichiarazione(const VulkanVideo *v)
{
	return v ? &v->dich : NULL;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 6. L'INGRESSO — dalla memoria e dal DMA-BUF, e la conversione sulla scheda
 * ═══════════════════════════════════════════════════════════════════════════ */

static VkImageMemoryBarrier2 barriera_immagine(VkImage img, VkImageAspectFlags aspetto, uint32_t strati,
                                               VkPipelineStageFlags2 s0, VkAccessFlags2 a0,
                                               VkPipelineStageFlags2 s1, VkAccessFlags2 a1,
                                               VkImageLayout l0, VkImageLayout l1)
{
	VkImageMemoryBarrier2 b = {
		.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2,
		.srcStageMask = s0, .srcAccessMask = a0, .dstStageMask = s1, .dstAccessMask = a1,
		.oldLayout = l0, .newLayout = l1,
		.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
		.image = img,
		.subresourceRange = { .aspectMask = aspetto, .levelCount = 1, .layerCount = strati },
	};
	return b;
}

static void barriere(VkCommandBuffer cb, const VkImageMemoryBarrier2 *b, uint32_t n,
                     const VkBufferMemoryBarrier2 *bb, uint32_t nb)
{
	VkDependencyInfo d = { .sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO, .imageMemoryBarrierCount = n,
		                   .pImageMemoryBarriers = b, .bufferMemoryBarrierCount = nb, .pBufferMemoryBarriers = bb };
	vkCmdPipelineBarrier2(cb, &d);
}

static bool manda_e_aspetta(VulkanVideo *v, VkQueue coda, VkCommandBuffer cb, VkFence fence, char *errore,
                            size_t errore_byte)
{
	VkCommandBufferSubmitInfo ci = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_SUBMIT_INFO, .commandBuffer = cb };
	VkSubmitInfo2 si = { .sType = VK_STRUCTURE_TYPE_SUBMIT_INFO_2, .commandBufferInfoCount = 1,
		                 .pCommandBufferInfos = &ci };
	VK_O_FALLISCI(vkEndCommandBuffer(cb), "vkEndCommandBuffer");
	VK_O_FALLISCI(vkResetFences(v->d->dispositivo, 1, &fence), "vkResetFences");
	VK_O_FALLISCI(vkQueueSubmit2(coda, 1, &si, fence), "vkQueueSubmit2");
	VK_O_FALLISCI(vkWaitForFences(v->d->dispositivo, 1, &fence, VK_TRUE, UINT64_MAX), "vkWaitForFences");
	return true;
}

/*
 * La conversione: lo shader legge `sorgente` (una vista RGB, gia' in layout
 * GENERAL e leggibile) e scrive i piani dell'immagine d'ingresso `n`.  Il
 * comando e' gia' cominciato dal chiamante, che ci ha messo in testa le sue
 * barriere (l'acquisizione del DMA-BUF, o la copia dei pixel caricati).
 */
static bool converti(VulkanVideo *v, VkImageView sorgente, unsigned n, char *errore, size_t errore_byte)
{
	VkCommandBuffer cb = v->cb_calcolo;
	Immagine *in = &v->ingresso[n];
	bool p10 = v->r.profondita == 10;
	VkImageView vy = v->dich.conversione_diretta ? in->piano_y : v->y_tmp.vista;
	VkImageView vuv = v->dich.conversione_diretta ? in->piano_uv : v->uv_tmp.vista;
	VkDescriptorImageInfo di_src = { .sampler = v->campionatore, .imageView = sorgente,
		                             .imageLayout = VK_IMAGE_LAYOUT_GENERAL };
	VkDescriptorImageInfo di_y = { .imageView = vy, .imageLayout = VK_IMAGE_LAYOUT_GENERAL };
	VkDescriptorImageInfo di_uv = { .imageView = vuv, .imageLayout = VK_IMAGE_LAYOUT_GENERAL };
	VkWriteDescriptorSet w[3] = {
		{ .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, .dstSet = v->ds, .dstBinding = 0, .descriptorCount = 1,
		  .descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, .pImageInfo = &di_src },
		{ .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, .dstSet = v->ds, .dstBinding = 1, .descriptorCount = 1,
		  .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, .pImageInfo = &di_y },
		{ .sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET, .dstSet = v->ds, .dstBinding = 2, .descriptorCount = 1,
		  .descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, .pImageInfo = &di_uv },
	};
	uint32_t pc[5] = { v->r.larghezza, v->r.altezza, v->larg_img, v->alt_img, p10 ? 1u : 0u };
	VkImageMemoryBarrier2 b[3];
	uint32_t nb = 0;

	(void) errore;
	(void) errore_byte;
	vkUpdateDescriptorSets(v->d->dispositivo, 3, w, 0, NULL);

	/* i piani che lo shader scrive: UNDEFINED → GENERAL (si riscrivono tutti) */
	if (v->dich.conversione_diretta) {
		b[nb++] = barriera_immagine(in->immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1, VK_PIPELINE_STAGE_2_NONE, 0,
		                            VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT,
		                            VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL);
	} else {
		b[nb++] = barriera_immagine(v->y_tmp.immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1, VK_PIPELINE_STAGE_2_NONE, 0,
		                            VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT,
		                            VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL);
		b[nb++] = barriera_immagine(v->uv_tmp.immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1, VK_PIPELINE_STAGE_2_NONE, 0,
		                            VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT,
		                            VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_GENERAL);
	}
	barriere(cb, b, nb, NULL, 0);

	vkCmdBindPipeline(cb, VK_PIPELINE_BIND_POINT_COMPUTE, v->pipeline);
	vkCmdBindDescriptorSets(cb, VK_PIPELINE_BIND_POINT_COMPUTE, v->pl_layout, 0, 1, &v->ds, 0, NULL);
	vkCmdPushConstants(cb, v->pl_layout, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof pc, pc);
	vkCmdDispatch(cb, (v->larg_img / 2 + 15) / 16, (v->alt_img / 2 + 15) / 16, 1);

	if (!v->dich.conversione_diretta) {
		/* la copia dei due piani nell'immagine d'ingresso */
		VkImageCopy2 regioni[2];
		VkCopyImageInfo2 ci = { .sType = VK_STRUCTURE_TYPE_COPY_IMAGE_INFO_2 };
		nb = 0;
		b[nb++] = barriera_immagine(v->y_tmp.immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1,
		                            VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT,
		                            VK_PIPELINE_STAGE_2_COPY_BIT, VK_ACCESS_2_TRANSFER_READ_BIT,
		                            VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
		b[nb++] = barriera_immagine(v->uv_tmp.immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1,
		                            VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT, VK_ACCESS_2_SHADER_STORAGE_WRITE_BIT,
		                            VK_PIPELINE_STAGE_2_COPY_BIT, VK_ACCESS_2_TRANSFER_READ_BIT,
		                            VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL);
		b[nb++] = barriera_immagine(in->immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1, VK_PIPELINE_STAGE_2_NONE, 0,
		                            VK_PIPELINE_STAGE_2_COPY_BIT, VK_ACCESS_2_TRANSFER_WRITE_BIT,
		                            VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
		barriere(cb, b, nb, NULL, 0);
		memset(regioni, 0, sizeof regioni);
		regioni[0].sType = VK_STRUCTURE_TYPE_IMAGE_COPY_2;
		regioni[0].srcSubresource = (VkImageSubresourceLayers){ VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 };
		regioni[0].dstSubresource = (VkImageSubresourceLayers){ VK_IMAGE_ASPECT_PLANE_0_BIT, 0, 0, 1 };
		regioni[0].extent = (VkExtent3D){ v->larg_img, v->alt_img, 1 };
		ci.srcImage = v->y_tmp.immagine;
		ci.srcImageLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
		ci.dstImage = in->immagine;
		ci.dstImageLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
		ci.regionCount = 1;
		ci.pRegions = &regioni[0];
		vkCmdCopyImage2(cb, &ci);
		regioni[1] = regioni[0];
		regioni[1].dstSubresource.aspectMask = VK_IMAGE_ASPECT_PLANE_1_BIT;
		regioni[1].extent = (VkExtent3D){ v->larg_img / 2, v->alt_img / 2, 1 };
		ci.srcImage = v->uv_tmp.immagine;
		ci.pRegions = &regioni[1];
		vkCmdCopyImage2(cb, &ci);
		in->layout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
	} else {
		in->layout = VK_IMAGE_LAYOUT_GENERAL;
	}
	return true;
}

static bool comincia(VkCommandBuffer cb, char *errore, size_t errore_byte)
{
	VkCommandBufferBeginInfo bi = { .sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
		                            .flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT };
	VK_O_FALLISCI(vkResetCommandBuffer(cb, 0), "vkResetCommandBuffer");
	VK_O_FALLISCI(vkBeginCommandBuffer(cb, &bi), "vkBeginCommandBuffer");
	return true;
}

/* ── dalla memoria ──────────────────────────────────────────────────────── */

static bool prepara_rgb(VulkanVideo *v, VulkanVideoOrdine ordine, uint32_t passo, char *errore, size_t errore_byte)
{
	VkDevice dev = v->d->dispositivo;
	VkFormat f = ordine == VULKANVIDEO_BGRX ? VK_FORMAT_B8G8R8A8_UNORM : VK_FORMAT_R8G8B8A8_UNORM;
	size_t byte = (size_t) passo * v->r.altezza;

	if (v->rgb_c_e && v->rgb_ordine == ordine && v->scala_byte >= byte)
		return true;
	vkDeviceWaitIdle(dev);
	immagine_libera(v, &v->rgb);
	v->rgb_c_e = false;
	if (v->scala_mappa)
		vkUnmapMemory(dev, v->scala_memoria);
	if (v->scala)
		vkDestroyBuffer(dev, v->scala, NULL);
	if (v->scala_memoria)
		vkFreeMemory(dev, v->scala_memoria, NULL);
	v->scala = VK_NULL_HANDLE;
	v->scala_memoria = VK_NULL_HANDLE;
	v->scala_mappa = NULL;
	{
		VkBufferCreateInfo bc = { .sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO, .size = byte,
			                      .usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT, .sharingMode = VK_SHARING_MODE_EXCLUSIVE };
		VkMemoryRequirements req;
		VK_O_FALLISCI(vkCreateBuffer(dev, &bc, NULL, &v->scala), "vkCreateBuffer (scala)");
		vkGetBufferMemoryRequirements(dev, v->scala, &req);
		if (!memoria_alloca(v, &req, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, 0, NULL,
		            &v->scala_memoria, NULL, errore, errore_byte))
			return false;
		VK_O_FALLISCI(vkBindBufferMemory(dev, v->scala, v->scala_memoria, 0), "vkBindBufferMemory (scala)");
		VK_O_FALLISCI(vkMapMemory(dev, v->scala_memoria, 0, VK_WHOLE_SIZE, 0, &v->scala_mappa), "vkMapMemory (scala)");
		v->scala_byte = byte;
	}
	if (!immagine_crea(v, &v->rgb, f, v->r.larghezza, v->r.altezza, 1,
	                   VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT, 0, false, false, errore, errore_byte)
	    || !vista(v, v->rgb.immagine, f, VK_IMAGE_ASPECT_COLOR_BIT, 0, &v->rgb.vista, errore, errore_byte))
		return false;
	v->rgb_ordine = ordine;
	v->rgb_c_e = true;
	return true;
}

static bool codifica(VulkanVideo *v, unsigned n, bool chiave, const uint8_t **dati, size_t *byte,
                     VulkanVideoTempi *t, char *errore, size_t errore_byte);

bool vulkanvideo_codifica_memoria(VulkanVideo *v, const uint8_t *pixel, uint32_t passo, VulkanVideoOrdine ordine,
                                  bool chiave, const uint8_t **dati, size_t *byte, VulkanVideoTempi *t,
                                  char *errore, size_t errore_byte)
{
	uint64_t t0, t1;
	unsigned n;
	VkCommandBuffer cb;

	if (!v || !pixel)
		FALLISCI("vulkanvideo: niente da codificare");
	if (!passo)
		passo = v->r.larghezza * 4;
	memset(t, 0, sizeof *t);
	if (!prepara_rgb(v, ordine, passo, errore, errore_byte))
		return false;

	/* 1. il caricamento: i pixel nel buffer di scala (una copia, in CPU) */
	t0 = adesso_us();
	memcpy(v->scala_mappa, pixel, (size_t) passo * (v->r.altezza - 1) + (size_t) v->r.larghezza * 4);
	t1 = adesso_us();
	t->us_caricamento = t1 - t0;

	/* 2. la conversione: buffer → immagine RGB → shader → piani */
	n = v->prossimo_ingresso;
	v->prossimo_ingresso = (n + 1) % INGRESSI;
	cb = v->cb_calcolo;
	if (!comincia(cb, errore, errore_byte))
		return false;
	{
		VkImageMemoryBarrier2 b = barriera_immagine(v->rgb.immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1,
		                                            VK_PIPELINE_STAGE_2_NONE, 0, VK_PIPELINE_STAGE_2_COPY_BIT,
		                                            VK_ACCESS_2_TRANSFER_WRITE_BIT, VK_IMAGE_LAYOUT_UNDEFINED,
		                                            VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL);
		VkBufferImageCopy2 reg = {
			.sType = VK_STRUCTURE_TYPE_BUFFER_IMAGE_COPY_2,
			.bufferOffset = 0, .bufferRowLength = passo / 4, .bufferImageHeight = v->r.altezza,
			.imageSubresource = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 },
			.imageExtent = { v->r.larghezza, v->r.altezza, 1 },
		};
		VkCopyBufferToImageInfo2 ci = { .sType = VK_STRUCTURE_TYPE_COPY_BUFFER_TO_IMAGE_INFO_2,
			                            .srcBuffer = v->scala, .dstImage = v->rgb.immagine,
			                            .dstImageLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, .regionCount = 1,
			                            .pRegions = &reg };
		barriere(cb, &b, 1, NULL, 0);
		vkCmdCopyBufferToImage2(cb, &ci);
		b = barriera_immagine(v->rgb.immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1, VK_PIPELINE_STAGE_2_COPY_BIT,
		                      VK_ACCESS_2_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT,
		                      VK_ACCESS_2_SHADER_SAMPLED_READ_BIT, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
		                      VK_IMAGE_LAYOUT_GENERAL);
		barriere(cb, &b, 1, NULL, 0);
	}
	if (!converti(v, v->rgb.vista, n, errore, errore_byte))
		return false;
	if (!manda_e_aspetta(v, v->d->coda_calcolo, cb, v->fence_calcolo, errore, errore_byte))
		return false;
	t->us_conversione = adesso_us() - t1;

	return codifica(v, n, chiave, dati, byte, t, errore, errore_byte);
}

/* ── dal DMA-BUF ────────────────────────────────────────────────────────── */

static VkFormat formato_vulkan_di(uint32_t drm)
{
	switch (drm) {
	case DRM_FORMAT_XRGB8888:
	case DRM_FORMAT_ARGB8888:
		return VK_FORMAT_B8G8R8A8_UNORM;
	case DRM_FORMAT_XBGR8888:
	case DRM_FORMAT_ABGR8888:
		return VK_FORMAT_R8G8B8A8_UNORM;
	default:
		return VK_FORMAT_UNDEFINED;
	}
}

/*
 * ⭐ I modificatori che questa scheda sa IMPORTARE (e campionare) per un
 *   formato DRM — 5 ottobre 2026, NVIDIA.  `[M]` RTX 4090, driver 595: lasciato
 *   libero, il GBM della NVIDIA sceglie `0x300000000e08014`, che Vulkan
 *   rifiuta (`VK_ERROR_FORMAT_NOT_SUPPORTED`); Vulkan dichiara invece
 *   `0x300000000606010…15` e il LINEARE.  ⇒ Chi alloca la lastra chiede a GBM
 *   SOLO questi.  Il LINEARE si lascia fuori: chi chiama l'ha già provato.
 *   Apre e richiude il dispositivo da sola (si chiama una volta per palco).
 */
int vulkanvideo_modificatori(const char *nodo, uint32_t formato_drm, uint64_t *fuori, int quanti)
{
	VkFormat f = formato_vulkan_di(formato_drm);
	VulkanVideoDispositivo *d;
	char perche[256] = { 0 };
	int n = 0;

	if (f == VK_FORMAT_UNDEFINED || !fuori || quanti <= 0)
		return 0;
	d = vulkanvideo_apri_dispositivo(nodo, perche, sizeof perche);
	if (!d)
		return 0;
	if (d->ha_dmabuf) {
		VkDrmFormatModifierPropertiesListEXT l = {
			.sType = VK_STRUCTURE_TYPE_DRM_FORMAT_MODIFIER_PROPERTIES_LIST_EXT };
		VkFormatProperties2 p = { .sType = VK_STRUCTURE_TYPE_FORMAT_PROPERTIES_2, .pNext = &l };
		vkGetPhysicalDeviceFormatProperties2(d->fisico, f, &p);
		if (l.drmFormatModifierCount > 0) {
			l.pDrmFormatModifierProperties = calloc(l.drmFormatModifierCount,
			                                        sizeof *l.pDrmFormatModifierProperties);
			if (l.pDrmFormatModifierProperties) {
				vkGetPhysicalDeviceFormatProperties2(d->fisico, f, &p);
				for (uint32_t i = 0; i < l.drmFormatModifierCount && n < quanti; i++) {
					const VkDrmFormatModifierPropertiesEXT *m = &l.pDrmFormatModifierProperties[i];
					if (m->drmFormatModifier == 0 /* LINEARE */ || m->drmFormatModifierPlaneCount != 1
					    || !(m->drmFormatModifierTilingFeatures & VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT))
						continue;
					fuori[n++] = m->drmFormatModifier;
				}
				free(l.pDrmFormatModifierProperties);
			}
		}
	}
	vulkanvideo_chiudi_dispositivo(d);
	return n;
}

bool vulkanvideo_scheda_rifiuta_il_lineare(const char *nodo)
{
	struct gbm_device *g;
	struct gbm_bo *bo;
	int fd;

	if (!nodo || (fd = open(nodo, O_RDWR | O_CLOEXEC)) < 0)
		return false;
	g = gbm_create_device(fd);
	if (!g) {
		close(fd);
		return false;
	}
	bo = gbm_bo_create(g, 64, 64, GBM_FORMAT_XRGB8888, GBM_BO_USE_RENDERING | GBM_BO_USE_LINEAR);
	if (bo)
		gbm_bo_destroy(bo);
	gbm_device_destroy(g);
	close(fd);
	return bo == NULL;
}

static Importazione *importa(VulkanVideo *v, const VulkanVideoSuperficie *s, char *errore, size_t errore_byte)
{
	VkDevice dev = v->d->dispositivo;
	Importazione *libera = NULL;
	VkFormat f = formato_vulkan_di(s->formato_drm);

	if (!v->d->ha_dmabuf) {
		di(errore, errore_byte, "«%s» non ha le estensioni del DMA-BUF", v->d->nome);
		return NULL;
	}
	if (f == VK_FORMAT_UNDEFINED) {
		di(errore, errore_byte, "formato DRM 0x%08x non previsto (XRGB8888/XBGR8888)", s->formato_drm);
		return NULL;
	}
	if (s->generazione != v->generazione_vista) {
		for (unsigned i = 0; i < IMPORTAZIONI_MAX; i++)
			importazione_libera(v, &v->importate[i]);
		v->generazione_vista = s->generazione;
	}
	for (unsigned i = 0; i < IMPORTAZIONI_MAX; i++) {
		Importazione *im = &v->importate[i];
		if (im->usata && im->fd == s->fd && im->larghezza == s->larghezza && im->altezza == s->altezza
		    && im->stride == s->stride && im->offset == s->offset && im->formato_drm == s->formato_drm
		    && im->modificatore == s->modificatore)
			return im;
		if (!im->usata && !libera)
			libera = im;
	}
	if (!libera) {
		/* la cache e' piena: si butta la prima (nessun comando in volo: si aspetta ogni giro) */
		importazione_libera(v, &v->importate[0]);
		libera = &v->importate[0];
	}
	{
		/* il formato e il modificatore: la scheda li accetta? */
		VkPhysicalDeviceExternalImageFormatInfo ext = {
			.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_EXTERNAL_IMAGE_FORMAT_INFO,
			.handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT };
		VkPhysicalDeviceImageDrmFormatModifierInfoEXT mod = {
			.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_DRM_FORMAT_MODIFIER_INFO_EXT, .pNext = &ext,
			.drmFormatModifier = s->modificatore, .sharingMode = VK_SHARING_MODE_EXCLUSIVE };
		VkPhysicalDeviceImageFormatInfo2 fi = {
			.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_IMAGE_FORMAT_INFO_2, .pNext = &mod, .format = f,
			.type = VK_IMAGE_TYPE_2D, .tiling = VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT,
			.usage = VK_IMAGE_USAGE_SAMPLED_BIT };
		VkExternalImageFormatProperties ep = { .sType = VK_STRUCTURE_TYPE_EXTERNAL_IMAGE_FORMAT_PROPERTIES };
		VkImageFormatProperties2 fp = { .sType = VK_STRUCTURE_TYPE_IMAGE_FORMAT_PROPERTIES_2, .pNext = &ep };
		VkResult r = vkGetPhysicalDeviceImageFormatProperties2(v->d->fisico, &fi, &fp);
		if (r != VK_SUCCESS) {
			di(errore, errore_byte, "la scheda non importa questo DMA-BUF (formato %d, modificatore 0x%llx): %s",
			   (int) f, (unsigned long long) s->modificatore, vk_nome(r));
			return NULL;
		}
		if (!(ep.externalMemoryProperties.externalMemoryFeatures & VK_EXTERNAL_MEMORY_FEATURE_IMPORTABLE_BIT)) {
			di(errore, errore_byte, "la scheda dichiara il formato ma non l'importazione del DMA-BUF");
			return NULL;
		}
	}
	{
		VkSubresourceLayout piano = { .offset = s->offset, .size = 0, .rowPitch = s->stride };
		VkImageDrmFormatModifierExplicitCreateInfoEXT mod = {
			.sType = VK_STRUCTURE_TYPE_IMAGE_DRM_FORMAT_MODIFIER_EXPLICIT_CREATE_INFO_EXT,
			.drmFormatModifier = s->modificatore, .drmFormatModifierPlaneCount = 1, .pPlaneLayouts = &piano };
		VkExternalMemoryImageCreateInfo ext = { .sType = VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_IMAGE_CREATE_INFO,
			                                    .pNext = &mod,
			                                    .handleTypes = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT };
		VkImageCreateInfo ci = {
			.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO, .pNext = &ext, .imageType = VK_IMAGE_TYPE_2D, .format = f,
			.extent = { s->larghezza, s->altezza, 1 }, .mipLevels = 1, .arrayLayers = 1,
			.samples = VK_SAMPLE_COUNT_1_BIT, .tiling = VK_IMAGE_TILING_DRM_FORMAT_MODIFIER_EXT,
			.usage = VK_IMAGE_USAGE_SAMPLED_BIT, .sharingMode = VK_SHARING_MODE_EXCLUSIVE,
			.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED };
		VkMemoryRequirements req;
		VkMemoryFdPropertiesKHR fdp = { .sType = VK_STRUCTURE_TYPE_MEMORY_FD_PROPERTIES_KHR };
		int fd2;
		VkResult r;

		memset(libera, 0, sizeof *libera);
		libera->usata = true;
		libera->fd = s->fd;
		libera->generazione = s->generazione;
		libera->larghezza = s->larghezza;
		libera->altezza = s->altezza;
		libera->stride = s->stride;
		libera->offset = s->offset;
		libera->formato_drm = s->formato_drm;
		libera->modificatore = s->modificatore;
		r = vkCreateImage(dev, &ci, NULL, &libera->immagine);
		if (r != VK_SUCCESS) {
			di(errore, errore_byte, "vkCreateImage (DMA-BUF %ux%u passo %u): %s", s->larghezza, s->altezza, s->stride,
			   vk_nome(r));
			importazione_libera(v, libera);
			return NULL;
		}
		vkGetImageMemoryRequirements(dev, libera->immagine, &req);
		r = v->d->f.GetMemoryFdPropertiesKHR(dev, VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, s->fd, &fdp);
		if (r != VK_SUCCESS) {
			di(errore, errore_byte, "vkGetMemoryFdPropertiesKHR(fd %d): %s", s->fd, vk_nome(r));
			importazione_libera(v, libera);
			return NULL;
		}
		/* ⛔ il descrittore non e' nostro: si duplica, e il duplicato lo chiude Vulkan */
		fd2 = fcntl(s->fd, F_DUPFD_CLOEXEC, 0);
		if (fd2 < 0) {
			di(errore, errore_byte, "dup del DMA-BUF: %s", strerror(errno));
			importazione_libera(v, libera);
			return NULL;
		}
		{
			VkMemoryDedicatedAllocateInfo ded = { .sType = VK_STRUCTURE_TYPE_MEMORY_DEDICATED_ALLOCATE_INFO,
				                                  .image = libera->immagine };
			VkImportMemoryFdInfoKHR imp = { .sType = VK_STRUCTURE_TYPE_IMPORT_MEMORY_FD_INFO_KHR, .pNext = &ded,
				                            .handleType = VK_EXTERNAL_MEMORY_HANDLE_TYPE_DMA_BUF_BIT_EXT, .fd = fd2 };
			VkMemoryRequirements req2 = req;
			req2.memoryTypeBits &= fdp.memoryTypeBits;
			if (!req2.memoryTypeBits) {
				close(fd2);
				di(errore, errore_byte, "nessun tipo di memoria comune fra l'immagine (0x%x) e il DMA-BUF (0x%x)",
				   req.memoryTypeBits, fdp.memoryTypeBits);
				importazione_libera(v, libera);
				return NULL;
			}
			if (!memoria_alloca(v, &req2, 0, 0, &imp, &libera->memoria, NULL, errore, errore_byte)) {
				close(fd2);
				importazione_libera(v, libera);
				return NULL;
			}
		}
		r = vkBindImageMemory(dev, libera->immagine, libera->memoria, 0);
		if (r != VK_SUCCESS) {
			di(errore, errore_byte, "vkBindImageMemory (DMA-BUF): %s", vk_nome(r));
			importazione_libera(v, libera);
			return NULL;
		}
		if (!vista(v, libera->immagine, f, VK_IMAGE_ASPECT_COLOR_BIT, 0, &libera->vista, errore, errore_byte)) {
			importazione_libera(v, libera);
			return NULL;
		}
	}
	return libera;
}

bool vulkanvideo_codifica_dmabuf(VulkanVideo *v, const VulkanVideoSuperficie *s, bool chiave,
                                 const uint8_t **dati, size_t *byte, VulkanVideoTempi *t, char *errore,
                                 size_t errore_byte)
{
	uint64_t t0;
	unsigned n;
	Importazione *im;
	VkCommandBuffer cb;
	uint32_t estranea;

	if (!v || !s || s->fd < 0)
		FALLISCI("vulkanvideo: niente da codificare");
	estranea = v->d->ha_foreign ? VK_QUEUE_FAMILY_FOREIGN_EXT : VK_QUEUE_FAMILY_EXTERNAL;
	if (s->larghezza != v->r.larghezza || s->altezza != v->r.altezza)
		FALLISCI("il DMA-BUF e' %ux%u e la tela %ux%u", s->larghezza, s->altezza, v->r.larghezza, v->r.altezza);
	memset(t, 0, sizeof *t);
	t0 = adesso_us();
	im = importa(v, s, errore, errore_byte);
	if (!im)
		return false;
	n = v->prossimo_ingresso;
	v->prossimo_ingresso = (n + 1) % INGRESSI;
	cb = v->cb_calcolo;
	if (!comincia(cb, errore, errore_byte))
		return false;
	{
		/* l'acquisizione dall'esterno: il compositore ha scritto, noi leggiamo */
		VkImageMemoryBarrier2 b = barriera_immagine(im->immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1,
		                                            VK_PIPELINE_STAGE_2_NONE, 0, VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT,
		                                            VK_ACCESS_2_SHADER_SAMPLED_READ_BIT,
		                                            im->acquisita ? VK_IMAGE_LAYOUT_GENERAL : VK_IMAGE_LAYOUT_UNDEFINED,
		                                            VK_IMAGE_LAYOUT_GENERAL);
		b.srcQueueFamilyIndex = estranea;
		b.dstQueueFamilyIndex = v->d->fam_calcolo;
		barriere(cb, &b, 1, NULL, 0);
		im->acquisita = true;
	}
	if (!converti(v, im->vista, n, errore, errore_byte))
		return false;
	{
		/* e il rilascio: la scheda ha finito di leggere quando la fence scatta */
		VkImageMemoryBarrier2 b = barriera_immagine(im->immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1,
		                                            VK_PIPELINE_STAGE_2_COMPUTE_SHADER_BIT,
		                                            VK_ACCESS_2_SHADER_SAMPLED_READ_BIT, VK_PIPELINE_STAGE_2_NONE, 0,
		                                            VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_GENERAL);
		b.srcQueueFamilyIndex = v->d->fam_calcolo;
		b.dstQueueFamilyIndex = estranea;
		barriere(cb, &b, 1, NULL, 0);
	}
	if (!manda_e_aspetta(v, v->d->coda_calcolo, cb, v->fence_calcolo, errore, errore_byte))
		return false;
	t->us_conversione = adesso_us() - t0;
	t->us_caricamento = 0; /* ⛔ questo tratto NON C'E' sulla copia zero */
	return codifica(v, n, chiave, dati, byte, t, errore, errore_byte);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * 7. IL GIRO DI UN FOTOGRAMMA
 * ═══════════════════════════════════════════════════════════════════════════ */

/* Lo stato del regolatore, come lo si dichiara a ogni `begin` e nel `control`. */
typedef struct {
	VkVideoEncodeRateControlInfoKHR rc;
	VkVideoEncodeRateControlLayerInfoKHR strato;
	VkVideoEncodeH264RateControlInfoKHR rc264;
	VkVideoEncodeH264RateControlLayerInfoKHR strato264;
	VkVideoEncodeH265RateControlInfoKHR rc265;
	VkVideoEncodeH265RateControlLayerInfoKHR strato265;
} Regolatore;

static void regolatore_componi(VulkanVideo *v, Regolatore *g)
{
	bool h264 = v->r.codec == VULKANVIDEO_H264;
	uint32_t gop = v->r.chiavi_ogni ? v->r.chiavi_ogni : UINT32_MAX;

	memset(g, 0, sizeof *g);
	g->rc264 = (VkVideoEncodeH264RateControlInfoKHR){
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_RATE_CONTROL_INFO_KHR,
		.gopFrameCount = gop, .idrPeriod = gop, .consecutiveBFrameCount = 0, .temporalLayerCount = 1 };
	g->rc265 = (VkVideoEncodeH265RateControlInfoKHR){
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_RATE_CONTROL_INFO_KHR,
		.gopFrameCount = gop, .idrPeriod = gop, .consecutiveBFrameCount = 0, .subLayerCount = 1 };
	g->rc = (VkVideoEncodeRateControlInfoKHR){
		.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_RATE_CONTROL_INFO_KHR,
		.pNext = h264 ? (void *) &g->rc264 : (void *) &g->rc265,
		.rateControlMode = VK_VIDEO_ENCODE_RATE_CONTROL_MODE_DISABLED_BIT_KHR };
	if (v->dich.modo_rc == VULKANVIDEO_RC_VBR) {
		int q = v->qp_corrente;
		g->strato264 = (VkVideoEncodeH264RateControlLayerInfoKHR){
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_RATE_CONTROL_LAYER_INFO_KHR,
			.useMinQp = VK_TRUE, .minQp = { q, q, q }, .useMaxQp = VK_FALSE };
		g->strato265 = (VkVideoEncodeH265RateControlLayerInfoKHR){
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_RATE_CONTROL_LAYER_INFO_KHR,
			.useMinQp = VK_TRUE, .minQp = { q, q, q }, .useMaxQp = VK_FALSE };
		g->strato = (VkVideoEncodeRateControlLayerInfoKHR){
			.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_RATE_CONTROL_LAYER_INFO_KHR,
			.pNext = h264 ? (void *) &g->strato264 : (void *) &g->strato265,
			.averageBitrate = (uint64_t) v->r.banda_punto, .maxBitrate = (uint64_t) v->r.banda_filo,
			.frameRateNumerator = v->r.fotogrammi_al_secondo, .frameRateDenominator = 1 };
		g->rc.rateControlMode = VK_VIDEO_ENCODE_RATE_CONTROL_MODE_VBR_BIT_KHR;
		g->rc.layerCount = 1;
		g->rc.pLayers = &g->strato;
		g->rc.virtualBufferSizeInMs = (uint32_t) ((int64_t) v->r.serbatoio_bit * 1000 / v->r.banda_filo);
		g->rc.initialVirtualBufferSizeInMs = g->rc.virtualBufferSizeInMs * 3 / 4;
	}
}

static bool codifica(VulkanVideo *v, unsigned n, bool chiave, const uint8_t **dati, size_t *byte,
                     VulkanVideoTempi *t, char *errore, size_t errore_byte)
{
	uint64_t t0 = adesso_us();
	VkCommandBuffer cb = v->cb_codifica;
	Immagine *in = &v->ingresso[n];
	bool h264 = v->r.codec == VULKANVIDEO_H264;
	bool idr;
	unsigned slot_cur;
	Regolatore reg;
	VkImageMemoryBarrier2 b[2];
	uint32_t nb = 0;

	/* ── chi e' questo fotogramma ──────────────────────────────────────── */
	idr = chiave || !v->riferimento_valido || v->ordine == 0
	      || (v->r.chiavi_ogni && v->nel_gop >= v->r.chiavi_ogni);
	if (idr) {
		v->nel_gop = 0;
		v->frame_num = 0;
		v->poc = 0;
		if (v->ordine)
			v->idr_pic_id = (v->idr_pic_id + 1) & 0xFFFFu;
	} else {
		v->frame_num = v->frame_num_rif + 1;
		v->poc = v->poc_rif + 1;
	}
	v->nel_gop++;
	slot_cur = v->riferimento_valido ? (v->slot_rif + 1) % SLOT_DPB : 0;
	regolatore_componi(v, &reg);

	if (!comincia(cb, errore, errore_byte))
		return false;
	vkCmdResetQueryPool(cb, v->query, 0, 1);

	/* ── le barriere: l'ingresso verso il codificatore, il DPB ─────────── */
	b[nb++] = barriera_immagine(in->immagine, VK_IMAGE_ASPECT_COLOR_BIT, 1, VK_PIPELINE_STAGE_2_NONE, 0,
	                            VK_PIPELINE_STAGE_2_VIDEO_ENCODE_BIT_KHR, VK_ACCESS_2_VIDEO_ENCODE_READ_BIT_KHR,
	                            in->layout, VK_IMAGE_LAYOUT_VIDEO_ENCODE_SRC_KHR);
	b[nb++] = barriera_immagine(v->dpb.immagine, VK_IMAGE_ASPECT_COLOR_BIT, SLOT_DPB,
	                            v->dpb_inizializzata ? VK_PIPELINE_STAGE_2_VIDEO_ENCODE_BIT_KHR : VK_PIPELINE_STAGE_2_NONE,
	                            v->dpb_inizializzata ? VK_ACCESS_2_VIDEO_ENCODE_WRITE_BIT_KHR : 0,
	                            VK_PIPELINE_STAGE_2_VIDEO_ENCODE_BIT_KHR,
	                            VK_ACCESS_2_VIDEO_ENCODE_READ_BIT_KHR | VK_ACCESS_2_VIDEO_ENCODE_WRITE_BIT_KHR,
	                            v->dpb_inizializzata ? VK_IMAGE_LAYOUT_VIDEO_ENCODE_DPB_KHR : VK_IMAGE_LAYOUT_UNDEFINED,
	                            VK_IMAGE_LAYOUT_VIDEO_ENCODE_DPB_KHR);
	barriere(cb, b, nb, NULL, 0);
	in->layout = VK_IMAGE_LAYOUT_VIDEO_ENCODE_SRC_KHR;
	v->dpb_inizializzata = true;

	{
		/* ── le risorse del DPB: il riferimento (se c'e') e la corrente ── */
		VkVideoPictureResourceInfoKHR res_dpb[SLOT_DPB];
		VkVideoReferenceSlotInfoKHR slot_begin[2], slot_rif, slot_setup;
		uint32_t n_begin = 0;
		StdVideoEncodeH264ReferenceInfo ri264_cur, ri264_rif;
		StdVideoEncodeH265ReferenceInfo ri265_cur, ri265_rif;
		VkVideoEncodeH264DpbSlotInfoKHR dpb264_cur, dpb264_rif;
		VkVideoEncodeH265DpbSlotInfoKHR dpb265_cur, dpb265_rif;
		VkVideoBeginCodingInfoKHR inizio = { .sType = VK_STRUCTURE_TYPE_VIDEO_BEGIN_CODING_INFO_KHR,
			                                 .videoSession = v->sessione, .videoSessionParameters = v->parametri };
		VkVideoEncodeInfoKHR enc = { .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_INFO_KHR };
		/* H.264 */
		StdVideoEncodeH264ReferenceListsInfo liste264;
		StdVideoEncodeH264PictureInfo pic264;
		StdVideoEncodeH264SliceHeader slice264;
		VkVideoEncodeH264NaluSliceInfoKHR nalu264;
		VkVideoEncodeH264PictureInfoKHR vk264;
		/* HEVC */
		StdVideoEncodeH265ReferenceListsInfo liste265;
		StdVideoH265ShortTermRefPicSet rps265;
		StdVideoEncodeH265PictureInfo pic265;
		StdVideoEncodeH265SliceSegmentHeader slice265;
		VkVideoEncodeH265NaluSliceSegmentInfoKHR nalu265;
		VkVideoEncodeH265PictureInfoKHR vk265;
		int qp = v->dich.modo_rc == VULKANVIDEO_RC_CQP ? v->qp_corrente : 0;

		memset(&slot_rif, 0, sizeof slot_rif);
		for (unsigned i = 0; i < SLOT_DPB; i++)
			res_dpb[i] = (VkVideoPictureResourceInfoKHR){
				.sType = VK_STRUCTURE_TYPE_VIDEO_PICTURE_RESOURCE_INFO_KHR,
				.codedExtent = { v->larg_cod, v->alt_cod }, .baseArrayLayer = 0, .imageViewBinding = v->vista_dpb[i] };

		memset(&ri264_cur, 0, sizeof ri264_cur);
		ri264_cur.primary_pic_type = idr ? STD_VIDEO_H264_PICTURE_TYPE_IDR : STD_VIDEO_H264_PICTURE_TYPE_P;
		ri264_cur.FrameNum = v->frame_num;
		ri264_cur.PicOrderCnt = 2 * (int32_t) v->frame_num;
		memset(&ri265_cur, 0, sizeof ri265_cur);
		ri265_cur.pic_type = idr ? STD_VIDEO_H265_PICTURE_TYPE_IDR : STD_VIDEO_H265_PICTURE_TYPE_P;
		ri265_cur.PicOrderCntVal = v->poc;
		dpb264_cur = (VkVideoEncodeH264DpbSlotInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_DPB_SLOT_INFO_KHR,
			                                             .pStdReferenceInfo = &ri264_cur };
		dpb265_cur = (VkVideoEncodeH265DpbSlotInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_DPB_SLOT_INFO_KHR,
			                                             .pStdReferenceInfo = &ri265_cur };
		slot_setup = (VkVideoReferenceSlotInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_REFERENCE_SLOT_INFO_KHR,
			                                         .pNext = h264 ? (void *) &dpb264_cur : (void *) &dpb265_cur,
			                                         .slotIndex = (int32_t) slot_cur, .pPictureResource = &res_dpb[slot_cur] };
		if (!idr) {
			memset(&ri264_rif, 0, sizeof ri264_rif);
			ri264_rif.primary_pic_type = v->rif_era_idr ? STD_VIDEO_H264_PICTURE_TYPE_IDR : STD_VIDEO_H264_PICTURE_TYPE_P;
			ri264_rif.FrameNum = v->frame_num_rif;
			ri264_rif.PicOrderCnt = 2 * (int32_t) v->frame_num_rif;
			memset(&ri265_rif, 0, sizeof ri265_rif);
			ri265_rif.pic_type = v->rif_era_idr ? STD_VIDEO_H265_PICTURE_TYPE_IDR : STD_VIDEO_H265_PICTURE_TYPE_P;
			ri265_rif.PicOrderCntVal = v->poc_rif;
			dpb264_rif = (VkVideoEncodeH264DpbSlotInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_DPB_SLOT_INFO_KHR,
				                                             .pStdReferenceInfo = &ri264_rif };
			dpb265_rif = (VkVideoEncodeH265DpbSlotInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_DPB_SLOT_INFO_KHR,
				                                             .pStdReferenceInfo = &ri265_rif };
			slot_rif = (VkVideoReferenceSlotInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_REFERENCE_SLOT_INFO_KHR,
				                                       .pNext = h264 ? (void *) &dpb264_rif : (void *) &dpb265_rif,
				                                       .slotIndex = (int32_t) v->slot_rif, .pPictureResource = &res_dpb[v->slot_rif] };
			slot_begin[n_begin++] = slot_rif;
		}
		/* la corrente: legata al giro, ancora senza slot (-1); lo slot lo attiva l'encode */
		slot_begin[n_begin] = (VkVideoReferenceSlotInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_REFERENCE_SLOT_INFO_KHR,
			                                                  .slotIndex = -1, .pPictureResource = &res_dpb[slot_cur] };
		n_begin++;
		inizio.referenceSlotCount = n_begin;
		inizio.pReferenceSlots = slot_begin;
		if (v->sessione_azzerata)
			inizio.pNext = &reg.rc;
		v->d->f.CmdBeginVideoCodingKHR(cb, &inizio);

		if (!v->sessione_azzerata || v->rc_da_riprogrammare) {
			VkVideoCodingControlInfoKHR ctrl = { .sType = VK_STRUCTURE_TYPE_VIDEO_CODING_CONTROL_INFO_KHR,
				                                 .pNext = &reg.rc,
				                                 .flags = VK_VIDEO_CODING_CONTROL_ENCODE_RATE_CONTROL_BIT_KHR };
			if (!v->sessione_azzerata)
				ctrl.flags |= VK_VIDEO_CODING_CONTROL_RESET_BIT_KHR;
			v->d->f.CmdControlVideoCodingKHR(cb, &ctrl);
			v->sessione_azzerata = true;
			v->rc_da_riprogrammare = false;
		}

		/* ── l'immagine, lo slice ──────────────────────────────────────── */
		if (h264) {
			memset(&liste264, 0, sizeof liste264);
			memset(liste264.RefPicList0, STD_VIDEO_H264_NO_REFERENCE_PICTURE, sizeof liste264.RefPicList0);
			memset(liste264.RefPicList1, STD_VIDEO_H264_NO_REFERENCE_PICTURE, sizeof liste264.RefPicList1);
			if (!idr)
				liste264.RefPicList0[0] = (uint8_t) v->slot_rif;
			memset(&pic264, 0, sizeof pic264);
			pic264.flags.IdrPicFlag = idr;
			pic264.flags.is_reference = 1;
			pic264.idr_pic_id = (uint16_t) v->idr_pic_id;
			pic264.primary_pic_type = idr ? STD_VIDEO_H264_PICTURE_TYPE_IDR : STD_VIDEO_H264_PICTURE_TYPE_P;
			pic264.frame_num = v->frame_num;
			pic264.PicOrderCnt = 2 * (int32_t) v->frame_num;
			pic264.pRefLists = &liste264;
			memset(&slice264, 0, sizeof slice264);
			slice264.flags.direct_spatial_mv_pred_flag = 1;
			slice264.slice_type = idr ? STD_VIDEO_H264_SLICE_TYPE_I : STD_VIDEO_H264_SLICE_TYPE_P;
			slice264.cabac_init_idc = STD_VIDEO_H264_CABAC_INIT_IDC_0;
			slice264.disable_deblocking_filter_idc = STD_VIDEO_H264_DISABLE_DEBLOCKING_FILTER_IDC_DISABLED;
			slice264.slice_qp_delta = (int8_t) (v->dich.modo_rc == VULKANVIDEO_RC_CQP ? qp - v->qp_fisso : 0);
			nalu264 = (VkVideoEncodeH264NaluSliceInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_NALU_SLICE_INFO_KHR,
				                                            .constantQp = qp, .pStdSliceHeader = &slice264 };
			vk264 = (VkVideoEncodeH264PictureInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H264_PICTURE_INFO_KHR,
				                                        .naluSliceEntryCount = 1, .pNaluSliceEntries = &nalu264,
				                                        .pStdPictureInfo = &pic264, .generatePrefixNalu = VK_FALSE };
			enc.pNext = &vk264;
		} else {
			memset(&liste265, 0, sizeof liste265);
			memset(liste265.RefPicList0, STD_VIDEO_H265_NO_REFERENCE_PICTURE, sizeof liste265.RefPicList0);
			memset(liste265.RefPicList1, STD_VIDEO_H265_NO_REFERENCE_PICTURE, sizeof liste265.RefPicList1);
			if (!idr)
				liste265.RefPicList0[0] = (uint8_t) v->slot_rif;
			memset(&rps265, 0, sizeof rps265);
			if (!idr) {
				rps265.num_negative_pics = 1;
				rps265.delta_poc_s0_minus1[0] = (uint16_t) (v->poc - v->poc_rif - 1);
				rps265.used_by_curr_pic_s0_flag = 1;
			}
			memset(&pic265, 0, sizeof pic265);
			pic265.flags.is_reference = 1;
			pic265.flags.IrapPicFlag = idr;
			pic265.flags.pic_output_flag = 1;
			pic265.flags.short_term_ref_pic_set_sps_flag = 0;
			pic265.pic_type = idr ? STD_VIDEO_H265_PICTURE_TYPE_IDR : STD_VIDEO_H265_PICTURE_TYPE_P;
			pic265.PicOrderCntVal = v->poc;
			pic265.pRefLists = &liste265;
			pic265.pShortTermRefPicSet = &rps265;
			memset(&slice265, 0, sizeof slice265);
			slice265.flags.first_slice_segment_in_pic_flag = 1;
			slice265.flags.slice_sao_luma_flag = v->sao;
			slice265.flags.slice_sao_chroma_flag = v->sao;
			slice265.flags.collocated_from_l0_flag = 1;
			slice265.slice_type = idr ? STD_VIDEO_H265_SLICE_TYPE_I : STD_VIDEO_H265_SLICE_TYPE_P;
			slice265.MaxNumMergeCand = 5;
			slice265.slice_qp_delta = (int8_t) (v->dich.modo_rc == VULKANVIDEO_RC_CQP ? qp - v->qp_fisso : 0);
			nalu265 = (VkVideoEncodeH265NaluSliceSegmentInfoKHR){
				.sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_NALU_SLICE_SEGMENT_INFO_KHR,
				.constantQp = qp, .pStdSliceSegmentHeader = &slice265 };
			vk265 = (VkVideoEncodeH265PictureInfoKHR){ .sType = VK_STRUCTURE_TYPE_VIDEO_ENCODE_H265_PICTURE_INFO_KHR,
				                                        .naluSliceSegmentEntryCount = 1, .pNaluSliceSegmentEntries = &nalu265,
				                                        .pStdPictureInfo = &pic265 };
			enc.pNext = &vk265;
		}
		enc.dstBuffer = v->bitstream;
		enc.dstBufferOffset = 0;
		enc.dstBufferRange = v->bitstream_byte;
		enc.srcPictureResource = (VkVideoPictureResourceInfoKHR){
			.sType = VK_STRUCTURE_TYPE_VIDEO_PICTURE_RESOURCE_INFO_KHR,
			.codedExtent = { v->larg_cod, v->alt_cod }, .baseArrayLayer = 0, .imageViewBinding = in->vista };
		enc.pSetupReferenceSlot = &slot_setup;
		enc.referenceSlotCount = idr ? 0 : 1;
		enc.pReferenceSlots = idr ? NULL : &slot_rif;
		enc.precedingExternallyEncodedBytes =
		    (idr && (v->cap.codifica.flags & VK_VIDEO_ENCODE_CAPABILITY_PRECEDING_EXTERNALLY_ENCODED_BYTES_BIT_KHR))
		        ? (uint32_t) v->intestazioni_byte : 0;

		vkCmdBeginQuery(cb, v->query, 0, 0);
		v->d->f.CmdEncodeVideoKHR(cb, &enc);
		vkCmdEndQuery(cb, v->query, 0);
		{
			VkVideoEndCodingInfoKHR fine = { .sType = VK_STRUCTURE_TYPE_VIDEO_END_CODING_INFO_KHR };
			v->d->f.CmdEndVideoCodingKHR(cb, &fine);
		}
		{
			VkBufferMemoryBarrier2 bb = {
				.sType = VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER_2,
				.srcStageMask = VK_PIPELINE_STAGE_2_VIDEO_ENCODE_BIT_KHR, .srcAccessMask = VK_ACCESS_2_VIDEO_ENCODE_WRITE_BIT_KHR,
				.dstStageMask = VK_PIPELINE_STAGE_2_HOST_BIT, .dstAccessMask = VK_ACCESS_2_HOST_READ_BIT,
				.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED, .dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED,
				.buffer = v->bitstream, .offset = 0, .size = VK_WHOLE_SIZE };
			barriere(cb, NULL, 0, &bb, 1);
		}
		if (!manda_e_aspetta(v, v->d->coda_codifica, cb, v->fence_codifica, errore, errore_byte))
			return false;
	}

	/* ── i byte ──────────────────────────────────────────────────────── */
	{
		uint32_t ris[4] = { 0, 0, 0, 0 };
		uint32_t campi = v->query_overrides ? 3 : 2;
		size_t offset, scritti;
		int32_t stato;
		VkResult r = vkGetQueryPoolResults(v->d->dispositivo, v->query, 0, 1, sizeof ris, ris,
		                                   sizeof(uint32_t) * (campi + 1),
		                                   VK_QUERY_RESULT_WAIT_BIT | VK_QUERY_RESULT_WITH_STATUS_BIT_KHR);
		if (r != VK_SUCCESS)
			FALLISCI("vkGetQueryPoolResults: %s", vk_nome(r));
		stato = (int32_t) ris[campi];
		if (stato <= 0)
			FALLISCI("la codifica non e' riuscita: stato della query %d%s", stato,
			         stato == VK_QUERY_RESULT_STATUS_INSUFFICIENT_BITSTREAM_BUFFER_RANGE_KHR
			             ? " (il buffer dei byte codificati non basta)" : "");
		offset = ris[0];
		scritti = ris[1];
		if (!scritti)
			FALLISCI("il driver ha reso zero byte");
		if (offset + scritti > v->bitstream_byte)
			FALLISCI("la query dichiara %zu+%zu byte in un buffer di %llu", offset, scritti,
			         (unsigned long long) v->bitstream_byte);
		if (!v->bitstream_coerente) {
			VkMappedMemoryRange mr = { .sType = VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE, .memory = v->bitstream_memoria,
				                       .offset = 0, .size = VK_WHOLE_SIZE };
			vkInvalidateMappedMemoryRanges(v->d->dispositivo, 1, &mr);
		}
		if (v->query_overrides && ris[2])
			v->dich.driver_ha_cambiato_parametri = true;
		v->uscita_byte = 0;
		if (idr) {
			memcpy(v->uscita, v->intestazioni, v->intestazioni_byte);
			v->uscita_byte = v->intestazioni_byte;
		}
		if (v->uscita_byte + scritti > v->uscita_capacita)
			FALLISCI("uscita di %zu byte oltre la capacita' %zu", v->uscita_byte + scritti, v->uscita_capacita);
		memcpy(v->uscita + v->uscita_byte, (const uint8_t *) v->bitstream_mappa + offset, scritti);
		v->uscita_byte += scritti;
	}

	/* ── questo fotogramma e' il riferimento del prossimo ──────────────── */
	v->riferimento_valido = true;
	v->slot_rif = slot_cur;
	v->frame_num_rif = v->frame_num;
	v->poc_rif = v->poc;
	v->rif_era_idr = idr;
	v->ordine++;
	t->us_codifica = adesso_us() - t0;
	*dati = v->uscita;
	*byte = v->uscita_byte;
	return true;
}

bool vulkanvideo_qualita(VulkanVideo *v, int qp, char *errore, size_t errore_byte)
{
	if (!v)
		FALLISCI("vulkanvideo: niente da regolare");
	if (qp < v->dich.qp_minimo || qp > v->dich.qp_massimo)
		FALLISCI("QP %d fuori da quel che la scheda dichiara (%d..%d)", qp, v->dich.qp_minimo, v->dich.qp_massimo);
	if (qp != v->qp_corrente) {
		v->qp_corrente = qp;
		if (v->dich.modo_rc == VULKANVIDEO_RC_VBR)
			v->rc_da_riprogrammare = true;
		registro_dice(REG_CODIFICA, "vulkanvideo: QP %d a caldo (%s)", qp,
		              v->dich.modo_rc == VULKANVIDEO_RC_CQP ? "il QP del prossimo fotogramma"
		                                                     : "il pavimento del regolatore, riprogrammato");
	}
	return true;
}

/*
 * ⛔ FASE 19 (la caccia al GPU hang, 1 ott 2026) — LE CATENE DENTRO LA
 *    STRUTTURA.  `Profilo`, `Capacita` e i parameter set puntano a campi della
 *    STESSA `VulkanVideo` (`profilo.pNext = &profilo.h264`, `lista.pProfiles`,
 *    `sps.pSequenceParameterSetVui`, ...).  `vulkanvideo_ridimensiona()`
 *    travasa la struttura per copia: senza questa riga quei puntatori
 *    resterebbero nella struttura di prima, che subito dopo si LIBERA.
 *    ⚠ Oggi dopo l'apertura nessuno li segue (il prodotto ridimensiona
 *    chiudendo e riaprendo, `codificatore.c`), quindi non e' la causa del
 *    page fault; ma e' un uso dopo la liberazione pronto a scattare al primo
 *    `immagine_crea(..., profilo=true)` fatto dopo un travaso.
 */
static void ripunta(VulkanVideo *v)
{
	bool h264 = v->r.codec == VULKANVIDEO_H264;

	v->profilo.h264.pNext = &v->profilo.uso;
	v->profilo.h265.pNext = &v->profilo.uso;
	v->profilo.profilo.pNext = h264 ? (void *) &v->profilo.h264 : (void *) &v->profilo.h265;
	v->profilo.lista.pProfiles = &v->profilo.profilo;
	v->cap.video.pNext = &v->cap.codifica;
	v->cap.codifica.pNext = h264 ? (void *) &v->cap.h264 : (void *) &v->cap.h265;
	if (v->sps264.pSequenceParameterSetVui)
		v->sps264.pSequenceParameterSetVui = &v->vui264;
	if (v->vps265.pDecPicBufMgr)
		v->vps265.pDecPicBufMgr = &v->dpbm265;
	if (v->vps265.pProfileTierLevel)
		v->vps265.pProfileTierLevel = &v->ptl265;
	if (v->sps265.pProfileTierLevel)
		v->sps265.pProfileTierLevel = &v->ptl265;
	if (v->sps265.pDecPicBufMgr)
		v->sps265.pDecPicBufMgr = &v->dpbm265;
	if (v->sps265.pSequenceParameterSetVui)
		v->sps265.pSequenceParameterSetVui = &v->vui265;
}

bool vulkanvideo_ridimensiona(VulkanVideo *v, uint32_t larghezza, uint32_t altezza, char *errore, size_t errore_byte)
{
	VulkanVideoRichiesta r;
	VulkanVideo *nuovo;

	if (!v)
		FALLISCI("vulkanvideo: niente da ridimensionare");
	r = v->r;
	r.larghezza = larghezza;
	r.altezza = altezza;
	r.qp = v->qp_corrente;
	/* ⛔ si apre il nuovo PRIMA di chiudere il vecchio: se non si apre, il
	 *    vecchio resta com'era e il chiamante lo sa */
	nuovo = vulkanvideo_apri(v->d, &r, errore, errore_byte);
	if (!nuovo)
		return false;
	{
		VulkanVideo vecchio = *v;
		*v = *nuovo;
		*nuovo = vecchio;
		ripunta(v);
		ripunta(nuovo);
		vulkanvideo_chiudi(nuovo); /* e' il vecchio, travasato */
	}
	return true;
}
