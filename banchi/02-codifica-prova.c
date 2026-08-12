/*
 * 02-codifica-prova.c — ⛔ il modo in cui il BANCO DI F2.3 punta sul PRODOTTO.
 *
 * ---------------------------------------------------------------------------
 * ⛔ PERCHE' ESISTE
 *
 * Il banco di F2.3 e' nato prima del prodotto e misurava `ffmpeg` da riga di
 * comando: era l'unica cosa che esistesse.  ⚠ Un banco che resta puntato li'
 * certifica **ffmpeg**, non il nostro codificatore — e sarebbe la forma E10 di
 * `REVIEWER.md` §2, *«una prova verde sul client sbagliato»*, con l'imputato
 * sbagliato.
 *
 * ⇒ Questo programma e' un guscio sottile attorno a `src/codificatore.c`:
 *   legge un file di pixel, chiama **le stesse tre funzioni che chiamera'
 *   `main.c`**, scrive il flusso su disco e la confessione in JSON.  Da qui in
 *   poi `02-codifica-lancia.sh CODIFICATORE=prodotto` misura il prodotto con
 *   gli **stessi** attesi con cui misurava ffmpeg.
 *
 * ⛔ E non contiene nessuna logica di codifica: se ne avesse, misurerebbe se'
 *    stesso.  Ogni decisione — profilo, bframes, Annex-B, il tetto dei 16 MiB —
 *    sta in `codificatore.c` e qui non si ripete.
 *
 *   banchi/02-codifica-prova --codec hevc|av1 --sorgente F --uscita F \
 *       [--formato yuv420p10le|bgrx] [--misura 1920x1080] [--fotogrammi N] \
 *       [--lossless | --crf N] [--componente NOME] [--profondita 8|10] \
 *       [--chiavi-ogni N] [--confessione F.json] [--ridimensiona LxA]
 *
 * ⚠ `--fotogrammi N` rilegge lo stesso fotogramma N volte: e' il modo in cui il
 *   banco pretende **tre gruppi di parameter set su tre chiavi**, che e' la
 *   meta' che si dimentica (un fotogramma solo li ha per forza).
 */
#include "../src/codificatore.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void uso(void)
{
	fprintf(stderr,
	        "uso: 02-codifica-prova --codec hevc|av1 --sorgente F --uscita F\n"
	        "     [--formato yuv420p10le|bgrx] [--misura LxA] [--fotogrammi N]\n"
	        "     [--lossless|--crf N] [--componente NOME] [--profondita 8|10]\n"
	        "     [--chiavi-ogni N] [--confessione F] [--ridimensiona LxA]\n");
}

int main(int argc, char **argv)
{
	const char *sorgente = NULL, *uscita = NULL, *confessione = NULL;
	const char *componente = NULL;
	const char *ridimensiona = NULL;
	CodecVideo codec = CODIFICATORE_HEVC;
	FormatoPixel formato = CODIFICATORE_PIXEL_YUV420P10LE;
	uint32_t larghezza = 1920, altezza = 1080, fotogrammi = 1, chiavi_ogni = 0;
	int profondita = 10, crf = 20;
	ModoQualita modo = CODIFICATORE_QUALITA_LOSSLESS;

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (!strcmp(a, "--codec") && v) {
			codec = strcmp(v, "av1") == 0 ? CODIFICATORE_AV1 : CODIFICATORE_HEVC;
			i++;
		} else if (!strcmp(a, "--sorgente") && v) {
			sorgente = v; i++;
		} else if (!strcmp(a, "--uscita") && v) {
			uscita = v; i++;
		} else if (!strcmp(a, "--confessione") && v) {
			confessione = v; i++;
		} else if (!strcmp(a, "--componente") && v) {
			componente = v; i++;
		} else if (!strcmp(a, "--formato") && v) {
			formato = strcmp(v, "bgrx") == 0 ? CODIFICATORE_PIXEL_BGRX
			                                 : CODIFICATORE_PIXEL_YUV420P10LE;
			i++;
		} else if (!strcmp(a, "--misura") && v) {
			sscanf(v, "%ux%u", &larghezza, &altezza); i++;
		} else if (!strcmp(a, "--ridimensiona") && v) {
			ridimensiona = v; i++;
		} else if (!strcmp(a, "--fotogrammi") && v) {
			fotogrammi = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--chiavi-ogni") && v) {
			chiavi_ogni = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--profondita") && v) {
			profondita = atoi(v); i++;
		} else if (!strcmp(a, "--crf") && v) {
			modo = CODIFICATORE_QUALITA_CRF; crf = atoi(v); i++;
		} else if (!strcmp(a, "--lossless")) {
			modo = CODIFICATORE_QUALITA_LOSSLESS;
		} else {
			uso();
			return 2;
		}
	}
	if (!sorgente || !uscita) {
		uso();
		return 2;
	}

	/* Il fotogramma in ingresso, letto tutto in memoria: e' il banco, non il
	 * prodotto, e la cattura vera consegna un puntatore alla memoria condivisa. */
	FILE *f = fopen(sorgente, "rb");
	if (!f) {
		fprintf(stderr, "⛔ non si apre %s\n", sorgente);
		return 2;
	}
	size_t attesi = (formato == CODIFICATORE_PIXEL_BGRX)
	                    ? (size_t) larghezza * altezza * 4
	                    : (size_t) larghezza * altezza * 3; /* 4:2:0 a 2 byte = 3 per pixel */
	uint8_t *pixel = malloc(attesi);
	if (!pixel) {
		fclose(f);
		return 2;
	}
	size_t letti = fread(pixel, 1, attesi, f);
	fclose(f);
	if (letti != attesi) {
		/* ⛔ Tre esiti, non due: un file corto non e' «zero pixel», e non lo si
		 *    codifica lo stesso riempiendo di zeri. */
		fprintf(stderr, "⛔ %s: letti %zu byte su %zu attesi per %ux%u\n", sorgente,
		        letti, attesi, larghezza, altezza);
		free(pixel);
		return 2;
	}

	CodificatoreRichiesta r = {
		.codec = codec,
		.componente = componente,
		.larghezza = larghezza,
		.altezza = altezza,
		.fotogrammi_al_secondo = 30,
		.modo = modo,
		.qualita = crf,
		.profondita = profondita,
		.formato = formato,
		.chiavi_ogni = chiavi_ogni,
	};
	char errore[512] = { 0 };
	Codificatore *cod = codificatore_nuovo(&r, errore, sizeof(errore));
	if (!cod) {
		fprintf(stderr, "⛔ il codificatore non si e' aperto: %s\n", errore);
		free(pixel);
		return 1;
	}

	FILE *u = fopen(uscita, "wb");
	if (!u) {
		fprintf(stderr, "⛔ non si scrive %s\n", uscita);
		codificatore_libera(cod);
		free(pixel);
		return 2;
	}

	uint32_t passo = (formato == CODIFICATORE_PIXEL_BGRX) ? larghezza * 4 : larghezza * 2;
	uint64_t tot_conv = 0, tot_cod = 0;
	uint32_t chiavi = 0, spediti = 0;
	int stato = 0;
	for (uint32_t k = 0; k < fotogrammi; k++) {
		if (chiavi_ogni == 0 && k > 0 && fotogrammi > 1)
			codificatore_chiedi_chiave(cod); /* il banco vuole N chiavi */
		CodificatoreFotogramma fg;
		if (!codificatore_comprimi(cod, pixel, passo, &fg)) {
			fprintf(stderr, "⛔ fotogramma %u non prodotto\n", k);
			stato = 1;
			break;
		}
		fwrite(fg.dati, 1, fg.byte, u);
		tot_conv += fg.us_conversione;
		tot_cod += fg.us_codifica;
		chiavi += fg.chiave ? 1 : 0;
		spediti++;
		codificatore_rilascia(cod);
	}

	/* ⛔ Il cambio di tela, quando il banco lo chiede: `RCP.md` §5.2 pretende
	 *    che il primo fotogramma alla misura nuova sia una chiave VERA. */
	if (!stato && ridimensiona) {
		uint32_t l2 = 0, a2 = 0;
		sscanf(ridimensiona, "%ux%u", &l2, &a2);
		if (!codificatore_ridimensiona(cod, l2, a2, errore, sizeof(errore))) {
			fprintf(stderr, "⛔ ridimensionamento fallito: %s\n", errore);
			stato = 1;
		} else {
			size_t attesi2 = (formato == CODIFICATORE_PIXEL_BGRX)
			                     ? (size_t) l2 * a2 * 4 : (size_t) l2 * a2 * 3;
			uint8_t *p2 = calloc(1, attesi2);
			CodificatoreFotogramma fg;
			uint32_t passo2 = (formato == CODIFICATORE_PIXEL_BGRX) ? l2 * 4 : l2 * 2;
			if (!p2 || !codificatore_comprimi(cod, p2, passo2, &fg)) {
				fprintf(stderr, "⛔ nessun fotogramma alla misura nuova\n");
				stato = 1;
			} else {
				fwrite(fg.dati, 1, fg.byte, u);
				chiavi += fg.chiave ? 1 : 0;
				spediti++;
				codificatore_rilascia(cod);
			}
			free(p2);
		}
	}
	fclose(u);

	const CodificatoreConfessione *c = codificatore_confessione(cod);
	FILE *j = confessione ? fopen(confessione, "w") : stdout;
	if (j) {
		fprintf(j,
		        "{\"nome\": \"%s\", \"componente\": \"%s\", \"ha_obbedito\": %s,\n"
		        " \"perche_no\": \"%s\", \"profondita_chiesta\": %d, \"fotogrammi_b\": %d,\n"
		        " \"global_header\": %s, \"letto_dal_flusso\": %s, \"profondita_flusso\": %d,\n"
		        " \"profilo_flusso\": %d, \"livello_flusso\": %d, \"tier_alto\": %s,\n"
		        " \"larghezza_flusso\": %u, \"altezza_flusso\": %u, \"croma_flusso\": %d,\n"
		        " \"stringa_codec\": \"%s\", \"promozione_8_a_10\": %s, \"riordina\": %s,\n"
		        " \"fotogrammi_in_volo\": %u, \"fotogrammi_spediti\": %u, \"chiavi\": %u,\n"
		        " \"us_conversione\": %" PRIu64 ", \"us_codifica\": %" PRIu64 "}\n",
		        codificatore_nome(cod), c->componente ? c->componente : "?",
		        c->ha_obbedito ? "true" : "false", c->perche_no,
		        c->profondita_chiesta, c->fotogrammi_b,
		        c->global_header ? "true" : "false",
		        c->letto_dal_flusso ? "true" : "false", c->profondita_flusso,
		        c->profilo_flusso, c->livello_flusso, c->tier_alto ? "true" : "false",
		        c->larghezza_flusso, c->altezza_flusso, c->croma_flusso,
		        c->stringa_codec, c->promozione_8_a_10 ? "true" : "false",
		        c->riordina ? "true" : "false", c->fotogrammi_in_volo, spediti, chiavi,
		        tot_conv, tot_cod);
		if (j != stdout)
			fclose(j);
	}
	codificatore_libera(cod);
	free(pixel);
	return stato;
}
