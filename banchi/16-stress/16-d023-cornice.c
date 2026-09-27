/*
 * 16-d023-cornice.c — la prova di D-023: il flusso dichiara la misura della TELA.
 *
 * `[M]` 27 set 2026, Radeon RX 6800 (radeonsi 25.0.7): `hevc_vaapi` a 2544x1344
 * dichiarava 2560x1344 — il multiplo di 64, senza finestra di conformita' — e
 * le sessioni con Chrome (HEVC, tele mai multiple di 64) restavano nere.
 *
 * Il programma e' un guscio attorno a `src/codificatore.c` e non contiene
 * logica di codifica: codifica N fotogrammi BGRx della misura chiesta, con due
 * chiavi (la cornice va scritta su OGNI SPS, non solo sul primo), e scrive il
 * flusso.  Il giudizio lo danno `ffprobe` (la misura dichiarata) e il PSNR
 * contro la sorgente (l'immagine dentro e' quella, 1:1): `16-d023-cornice.sh`.
 *
 *   16-d023-cornice --codec hevc|h264 --misura LxA --nodo /dev/dri/renderD128 \
 *       --sorgente F.bgrx --uscita F [--fotogrammi N]
 */
#include "../../src/codificatore.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
	const char *sorgente = NULL, *uscita = NULL, *nodo = "/dev/dri/renderD128";
	CodecVideo codec = CODIFICATORE_HEVC;
	uint32_t l = 0, a = 0, n = 10;

	for (int i = 1; i + 1 < argc; i += 2) {
		const char *k = argv[i], *v = argv[i + 1];
		if (!strcmp(k, "--codec"))
			codec = strcmp(v, "h264") == 0 ? CODIFICATORE_H264 : CODIFICATORE_HEVC;
		else if (!strcmp(k, "--misura"))
			sscanf(v, "%ux%u", &l, &a);
		else if (!strcmp(k, "--nodo"))
			nodo = v;
		else if (!strcmp(k, "--sorgente"))
			sorgente = v;
		else if (!strcmp(k, "--uscita"))
			uscita = v;
		else if (!strcmp(k, "--fotogrammi"))
			n = (uint32_t) strtoul(v, NULL, 10);
	}
	if (!sorgente || !uscita || !l || !a) {
		fprintf(stderr, "uso: 16-d023-cornice --codec hevc|h264 --misura LxA "
		                "--sorgente F.bgrx --uscita F [--nodo N] [--fotogrammi N]\n");
		return 2;
	}

	size_t byte = (size_t) l * a * 4;
	uint8_t *pixel = malloc(byte);
	FILE *f = fopen(sorgente, "rb");
	if (!pixel || !f || fread(pixel, 1, byte, f) != byte) {
		fprintf(stderr, "⛔ %s: non ci sono %zu byte di BGRx %ux%u\n", sorgente, byte, l, a);
		return 2;
	}
	fclose(f);

	CodificatoreRichiesta r = {
		.codec = codec,
		.componente = codec == CODIFICATORE_H264 ? "h264_vaapi" : "hevc_vaapi",
		.nodo_rendering = nodo,
		.potenza = CODIFICATORE_POTENZA_LA_DICHIARATA,
		.larghezza = l,
		.altezza = a,
		.fotogrammi_al_secondo = 30,
		.modo = CODIFICATORE_QUALITA_QP,
		.qualita = 26,
		.profondita = 8,
		.formato = CODIFICATORE_PIXEL_BGRX,
	};
	char errore[512] = { 0 };
	Codificatore *cod = codificatore_nuovo(&r, errore, sizeof(errore));
	if (!cod) {
		fprintf(stderr, "⛔ il codificatore non si e' aperto: %s\n", errore);
		return 1;
	}
	FILE *u = fopen(uscita, "wb");
	if (!u)
		return 2;
	uint32_t spediti = 0, chiavi = 0;
	for (uint32_t k = 0; k < n; k++) {
		if (k == n / 2)
			codificatore_chiedi_chiave(cod);
		CodificatoreFotogramma fg;
		if (!codificatore_comprimi(cod, pixel, l * 4, &fg)) {
			fprintf(stderr, "⛔ fotogramma %u non prodotto (vedi il registro)\n", k);
			break;
		}
		fwrite(fg.dati, 1, fg.byte, u);
		spediti++;
		chiavi += fg.chiave;
		codificatore_rilascia(cod);
	}
	fclose(u);
	printf("%s %ux%u: %u fotogrammi su %u, %u chiavi · %s\n",
	       codec == CODIFICATORE_H264 ? "h264" : "hevc", l, a, spediti, n, chiavi,
	       codificatore_nome(cod));
	codificatore_libera(cod);
	free(pixel);
	return spediti == n ? 0 : 1;
}
