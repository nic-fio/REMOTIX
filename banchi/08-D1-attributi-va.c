/*
 * D.1 — che cosa DICHIARA il driver su (profilo, entrypoint) del nodo chiesto.
 *
 * ⛔ Questo programma NON risponde alla domanda: dichiarare non e' produrre.
 *    Serve a sapere DOVE puntare la prova vera (`d1-strati.c`).
 *
 * Uso:  d1-attributi /dev/dri/renderD128
 */
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <va/va.h>
#include <va/va_drm.h>

struct Voce { VAProfile p; const char *nome; };

static const struct Voce PROFILI[] = {
	{ VAProfileH264ConstrainedBaseline, "H264ConstrainedBaseline" },
	{ VAProfileH264Main,                "H264Main" },
	{ VAProfileH264High,                "H264High" },
	{ VAProfileHEVCMain,                "HEVCMain" },
	{ VAProfileHEVCMain10,              "HEVCMain10" },
	{ VAProfileHEVCMain444,             "HEVCMain444" },
	{ VAProfileHEVCMain444_10,          "HEVCMain444_10" },
	{ VAProfileVP9Profile0,             "VP9Profile0" },
	{ VAProfileVP9Profile2,             "VP9Profile2" },
};

static const struct { VAEntrypoint e; const char *nome; } ENTRY[] = {
	{ VAEntrypointEncSlice,   "EncSlice"   },
	{ VAEntrypointEncSliceLP, "EncSliceLP" },
};

static void guarda(VADisplay d, VAProfile p, const char *np, VAEntrypoint e, const char *ne)
{
	int massimo = vaMaxNumEntrypoints(d);
	VAEntrypoint *el = calloc((size_t) massimo, sizeof *el);
	int quanti = 0;
	if (vaQueryConfigEntrypoints(d, p, el, &quanti) != VA_STATUS_SUCCESS) { free(el); return; }
	int c_e = 0;
	for (int i = 0; i < quanti; i++) if (el[i] == e) c_e = 1;
	free(el);
	if (!c_e) return;

	VAConfigAttrib a[] = {
		{ VAConfigAttribRateControl,        0 },
		{ VAConfigAttribEncRateControlExt,  0 },
		{ VAConfigAttribEncMaxRefFrames,    0 },
		{ VAConfigAttribEncQualityRange,    0 },
		{ VAConfigAttribEncMaxSlices,       0 },
		{ VAConfigAttribEncIntraRefresh,    0 },
		{ VAConfigAttribEncSkipFrame,       0 },
		{ VAConfigAttribMaxPictureWidth,    0 },
		{ VAConfigAttribMaxPictureHeight,   0 },
		{ VAConfigAttribEncPackedHeaders,   0 },
	};
	int n = (int) (sizeof a / sizeof a[0]);
	VAStatus st = vaGetConfigAttributes(d, p, e, a, n);
	printf("== %-24s %-10s  (vaGetConfigAttributes=%d)\n", np, ne, st);
	for (int i = 0; i < n; i++) {
		const char *nome = "?";
		switch (a[i].type) {
		case VAConfigAttribRateControl:       nome = "RateControl"; break;
		case VAConfigAttribEncRateControlExt: nome = "EncRateControlExt"; break;
		case VAConfigAttribEncMaxRefFrames:   nome = "EncMaxRefFrames"; break;
		case VAConfigAttribEncQualityRange:   nome = "EncQualityRange"; break;
		case VAConfigAttribEncMaxSlices:      nome = "EncMaxSlices"; break;
		case VAConfigAttribEncIntraRefresh:   nome = "EncIntraRefresh"; break;
		case VAConfigAttribEncSkipFrame:      nome = "EncSkipFrame"; break;
		case VAConfigAttribMaxPictureWidth:   nome = "MaxPictureWidth"; break;
		case VAConfigAttribMaxPictureHeight:  nome = "MaxPictureHeight"; break;
		case VAConfigAttribEncPackedHeaders:  nome = "EncPackedHeaders"; break;
		default: break;
		}
		if (a[i].value == VA_ATTRIB_NOT_SUPPORTED) {
			printf("   %-20s NON SUPPORTATO\n", nome);
			continue;
		}
		printf("   %-20s 0x%08x (%u)", nome, a[i].value, a[i].value);
		if (a[i].type == VAConfigAttribEncRateControlExt) {
			unsigned strati = (a[i].value & 0xFF) + 1;
			unsigned bitrate_per_strato = (a[i].value >> 8) & 1;
			printf("   ⇒ max_num_temporal_layers = %u, "
			       "temporal_layer_bitrate_control_flag = %u",
			       strati, bitrate_per_strato);
		}
		if (a[i].type == VAConfigAttribEncMaxRefFrames)
			printf("   ⇒ L0=%u L1=%u", a[i].value & 0xFFFF, (a[i].value >> 16) & 0xFFFF);
		printf("\n");
	}
}

int main(int argc, char **argv)
{
	const char *nodo = argc > 1 ? argv[1] : "/dev/dri/renderD128";
	int fd = open(nodo, O_RDWR);
	if (fd < 0) { perror(nodo); return 1; }
	VADisplay d = vaGetDisplayDRM(fd);
	int ma = 0, mi = 0;
	VAStatus st = vaInitialize(d, &ma, &mi);
	if (st != VA_STATUS_SUCCESS) { fprintf(stderr, "vaInitialize %d\n", st); return 1; }
	printf("nodo %s — driver «%s», VA-API %d.%d\n\n", nodo, vaQueryVendorString(d), ma, mi);
	for (size_t i = 0; i < sizeof PROFILI / sizeof PROFILI[0]; i++)
		for (size_t j = 0; j < sizeof ENTRY / sizeof ENTRY[0]; j++)
			guarda(d, PROFILI[i].p, PROFILI[i].nome, ENTRY[j].e, ENTRY[j].nome);
	vaTerminate(d);
	close(fd);
	return 0;
}
