/*
 * 10-b88-flusso.c — UN flusso di codifica del PRODOTTO, misurato da fuori.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COS'E'
 *
 * E' il mattone del **saturatore** (`banchi/10-b88-saturatore.py`): un processo
 * = un flusso, esattamente come nel prodotto un processo figlio = una sessione
 * (`figlio.c`, `MAX_FIGLI`).  Il banco ne accende N insieme e guarda dove cede.
 *
 * ⛔ NON contiene nessuna logica di codifica: chiama `src/codificatore.c`, cioe'
 *    **il codificatore del prodotto**, con le stesse funzioni che chiama
 *    `figlio.c`.  ⚠ Un banco puntato su `ffmpeg` certifica ffmpeg (forma E10 di
 *    `REVIEWER.md` §2): qui l'imputato e' il nostro.  `CODER.md` §3.6 — *isola
 *    UNA funzione sola e chiamala da fuori*.
 *
 * ⛔ Il modello e' `banchi/02-codifica-prova.c`, e questo file gli aggiunge le
 *    quattro cose che alla fase 10 servono e che li' non c'erano:
 *      1. l'hardware chiesto **per nome** (nodo, entrypoint, H.264);
 *      2. il **ritmo**: N fotogrammi al secondo per T secondi, con la partenza
 *         sincronizzata fra i processi (`--parti-a`);
 *      3. la **strada della scheda** (`codificatore_comprimi_scheda`), che e'
 *         quella vera del prodotto dalla fase 8: il fotogramma sta gia' sulla
 *         GPU e la CPU non lo tocca — ⭐ e' l'unico modo di misurare il MOTORE
 *         DI CODIFICA senza misurarci dentro `sws_scale`;
 *      4. i **tre tempi separati** riportati per fotogramma (conversione,
 *         caricamento, codifica), che sono quel che dice **PERCHE'** cede.
 *
 * ---------------------------------------------------------------------------
 * ⛔ LE DUE STRADE, E PERCHE' SONO DUE MISURE DIVERSE
 *
 *   `--strada scheda`   K buffer GBM riempiti UNA volta all'avvio e poi
 *                       ciclati.  Per fotogramma la CPU non copia niente: la
 *                       conversione BGRx→NV12 la fa la GPU (VA-API VPP) e la
 *                       codifica pure.  ⇒ misura **il motore video**.
 *   `--strada memoria`  i pixel arrivano dalla memoria di sistema: `sws_scale`
 *                       in CPU + caricamento sulla GPU + codifica.  ⇒ misura
 *                       **la catena di ripiego**, quella che si percorre quando
 *                       il passo non e' importabile (`codificatore.h`, la
 *                       guardia dei 64 byte).
 *
 * ⛔ I due numeri NON si mediano e non si confrontano come se fossero lo stesso:
 *    sono due tratti diversi, e il banco li tiene in due colonne.
 *
 * ---------------------------------------------------------------------------
 * ⛔ I GUASTI CHE SI INNESTANO DA QUI (`--certifica` del banco li usa)
 *
 *   `--componente libx264`  ⇒ ripiego in SOFTWARE: la confessione dice
 *                             `in_hardware: false` e il banco deve dare ROSSO,
 *                             non un numero plausibile.
 *   `--nodo /dev/dri/renderD127` ⇒ il flusso NON PARTE: `aperto: false` con la
 *                             ragione, e il banco non lo conta come «0 fps».
 *   `--zavorra-us N`        ⇒ N microsecondi di lavoro vero (non `sleep`: un
 *                             `sleep` non occupa la CPU e cambierebbe la
 *                             grandezza misurata) prima di ogni fotogramma ⇒ il
 *                             ritmo non si tiene, e il banco deve DIRLO col
 *                             numero: «chiesti 60, arrivati 41».
 *
 * ---------------------------------------------------------------------------
 * ⛔ `None` NON E' ZERO.  Se il flusso non si apre, il file di uscita esiste lo
 *    stesso e dice `"aperto": false` con la ragione: un file mancante e un
 *    flusso a zero fotogrammi si assomigliano troppo.
 *
 * ---------------------------------------------------------------------------
 * ⭐⭐ LE QUATTRO OPZIONI AGGIUNTE IL 24 AGOSTO 2026 (incarico B4)
 *
 *   `--codec hevc`          c'era gia' e non era mai stato girato.  ⛔ Le due
 *                           colonne H.264 e HEVC **non si mediano mai**: la
 *                           fase 9 §13.5 ha pagato l'errore opposto (21,18
 *                           contro 7,92 Mbit/s sulla stessa scena), e il
 *                           rapporto fra i due **non e' una costante**.
 *   `--profondita 8|10`     HEVC **Main** contro HEVC **Main10**.  ⛔ E il
 *                           predefinito e' **8** perche' e' quel che il
 *                           prodotto NEGOZIA: `rcp.c` offre `8,10` e §4.3
 *                           sceglie nell'ordine del client, che dichiara `8,10`.
 *   `--tetto-banda-mbit N`  il pavimento del tetto della fase 9.  ⛔ **0 =
 *                           spento e' il predefinito del PRODOTTO** (I6): da
 *                           spento il codificatore chiede **CQP**, da acceso
 *                           chiede **QVBR**.  Due modi, due colonne.
 *   `--senza-scadenza`      si codificano esattamente `fps*secondi` fotogrammi
 *                           invece di fermarsi all'orologio.  ⚠ Serve SOLO al
 *                           confronto delle impronte: due flussi con un numero
 *                           diverso di fotogrammi non sono confrontabili.
 */
#include "../src/codificatore.h"
#include "../src/registro.h"

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <gbm.h>
#include <drm_fourcc.h>

#define BUFFER_MAX 8 /* ⛔ = IMPORTATE_MAX di codificatore.c: oltre, la cache
                      *    delle superfici importate si butta a ogni giro e si
                      *    misurerebbe l'importazione invece della codifica. */

static uint64_t adesso_ns(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000000ull + (uint64_t) t.tv_nsec;
}

static uint64_t adesso_reale_ns(void)
{
	struct timespec t;
	clock_gettime(CLOCK_REALTIME, &t);
	return (uint64_t) t.tv_sec * 1000000000ull + (uint64_t) t.tv_nsec;
}

static void dormi_fino_reale(uint64_t quando_ns)
{
	for (;;) {
		uint64_t ora = adesso_reale_ns();
		if (ora >= quando_ns)
			return;
		uint64_t manca = quando_ns - ora;
		struct timespec t = { (time_t) (manca / 1000000000ull),
			              (long) (manca % 1000000000ull) };
		if (nanosleep(&t, NULL) == 0)
			return;
	}
}

/* ⛔ Zavorra che MORDE la CPU: un `sleep` lascerebbe il processore libero e il
 *    guasto innestato non somiglierebbe a un flusso lento davvero. */
static volatile uint64_t zavorra_pozzo;
static void zavorra(uint32_t microsecondi)
{
	if (!microsecondi)
		return;
	uint64_t fine = adesso_ns() + (uint64_t) microsecondi * 1000ull;
	uint64_t x = 1;
	while (adesso_ns() < fine)
		for (int i = 0; i < 512; i++)
			x = x * 6364136223846793005ull + 1442695040888963407ull;
	zavorra_pozzo = x;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ L'IMPRONTA DEL FLUSSO — e si dichiara per quel che E'.
 *
 * Serve a UNA domanda sola, quella di `fasi/10-…md` §6.6 portata sul nostro
 * codificatore: *«a parita' di richiesta, N codifiche insieme danno lo stesso
 * flusso di una sola?»*.  Se cambia, qualcuno ha deciso al posto nostro.
 *
 * ⛔ E' **FNV-1a a 64 bit**, NON un md5: si chiama `impronta` e non `md5`
 *    proprio per non dare due grandezze sotto la stessa etichetta
 *    (`LEZIONI.md` §1.11).  ⚠ Per «sono lo stesso flusso?» basta, e si legge
 *    **insieme** a `byte_totali` e a `fotogrammi_prodotti`: tre numeri uguali
 *    su tre e' quel che il banco chiama «identico».
 * ⭐ E costa quanto una passata di memoria: nessun file, nessuna scrittura su
 *    disco dentro il ciclo cronometrato — che avrebbe cambiato la grandezza
 *    misurata.
 */
#define FNV_BASE 1469598103934665603ull
#define FNV_PRIMO 1099511628211ull

static uint64_t impronta_avanza(uint64_t h, const uint8_t *dati, size_t byte)
{
	for (size_t i = 0; i < byte; i++) {
		h ^= (uint64_t) dati[i];
		h *= FNV_PRIMO;
	}
	return h;
}

static int confronta_u64(const void *a, const void *b)
{
	uint64_t x = *(const uint64_t *) a, y = *(const uint64_t *) b;
	return x < y ? -1 : (x > y ? 1 : 0);
}

/* ⚠ Mediana, 95° e peggiore su una copia ordinata: si scrive una volta sola e
 *   si usa per tutti e quattro i tempi. */
typedef struct {
	uint64_t mediana, p95, peggiore, somma;
} Riassunto;

static Riassunto riassumi(const uint64_t *v, size_t n)
{
	Riassunto r = { 0, 0, 0, 0 };
	if (!n)
		return r;
	uint64_t *c = malloc(n * sizeof(uint64_t));
	if (!c)
		return r;
	memcpy(c, v, n * sizeof(uint64_t));
	for (size_t i = 0; i < n; i++)
		r.somma += c[i];
	qsort(c, n, sizeof(uint64_t), confronta_u64);
	r.mediana = c[n / 2];
	r.p95 = c[(size_t) ((double) (n - 1) * 0.95)];
	r.peggiore = c[n - 1];
	free(c);
	return r;
}

static void uso(void)
{
	fprintf(stderr,
	        "uso: 10-b88-flusso --scena F --misura LxA --fps N --secondi N\n"
	        "     --uscita F.json --nonce S [--strada scheda|memoria]\n"
	        "     [--codec h264|hevc] [--componente NOME] [--nodo N] [--qp N]\n"
	        "     [--potenza bassa|piena] [--scena-fotogrammi K] [--parti-a NS]\n"
	        "     [--zavorra-us N] [--flusso N] [--libero]\n"
	        "     [--profondita 8|10] [--tetto-banda-mbit N] [--senza-scadenza]\n");
}

int main(int argc, char **argv)
{
	const char *scena = NULL, *uscita = NULL, *nonce = "senza-nonce";
	const char *componente = "h264_vaapi", *nodo = "/dev/dri/renderD128";
	const char *strada = "scheda";
	CodecVideo codec = CODIFICATORE_H264;
	PotenzaEntrypoint potenza = CODIFICATORE_POTENZA_BASSA;
	uint32_t larghezza = 1920, altezza = 1080, fps = 30, secondi = 15;
	uint32_t scena_fotogrammi = 4, zavorra_us = 0, flusso = 0;
	uint64_t parti_a_ns = 0;
	int qp = 26;
	bool libero = false;
	/* ⛔ 8, come il prodotto: `rcp.c` offre `NOSTRA_PROFONDITA "8,10"` e §4.3
	 *    sceglie nell'ordine del CLIENT, che dichiara `8,10` ⇒ la profondita'
	 *    negoziata e' **8**, cioe' HEVC **Main**, non Main10.  Il 10 si chiede a
	 *    mano e resta una COLONNA SUA: le due non si mediano. */
	int profondita = 8;
	/* ⛔⭐ IL PAVIMENTO in Mbit/s del tetto di banda della fase 9, e **0 = spento
	 *     e' il predefinito del prodotto** (`main.c`, invariante I6: il tetto NON
	 *     e' fra le cinque cure che si accendono).  ⇒ Spento il codificatore
	 *     chiede **CQP**; acceso chiede **QVBR**.  Sono due modi diversi e due
	 *     colonne diverse. */
	uint32_t tetto_banda_mbit = 0;
	/* ⚠ Toglie la scadenza a orologio: si codificano ESATTAMENTE `fps*secondi`
	 *   fotogrammi, quanto tempo ci vogliano.  ⛔ Serve a una cosa sola —
	 *   confrontare l'impronta di N flussi: due flussi con un numero DIVERSO di
	 *   fotogrammi non sono confrontabili, e il confronto darebbe «diversi»
	 *   quando la risposta vera e' «non ho misurato la stessa cosa». */
	bool senza_scadenza = false;

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i], *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (!strcmp(a, "--scena") && v) { scena = v; i++; }
		else if (!strcmp(a, "--uscita") && v) { uscita = v; i++; }
		else if (!strcmp(a, "--nonce") && v) { nonce = v; i++; }
		else if (!strcmp(a, "--componente") && v) { componente = v; i++; }
		else if (!strcmp(a, "--nodo") && v) { nodo = v; i++; }
		else if (!strcmp(a, "--strada") && v) { strada = v; i++; }
		else if (!strcmp(a, "--codec") && v) {
			codec = !strcmp(v, "hevc") ? CODIFICATORE_HEVC : CODIFICATORE_H264;
			i++;
		} else if (!strcmp(a, "--potenza") && v) {
			potenza = !strcmp(v, "piena") ? CODIFICATORE_POTENZA_PIENA
			                              : CODIFICATORE_POTENZA_BASSA;
			i++;
		} else if (!strcmp(a, "--misura") && v) {
			if (sscanf(v, "%ux%u", &larghezza, &altezza) != 2) { uso(); return 2; }
			i++;
		} else if (!strcmp(a, "--fps") && v) { fps = (uint32_t) strtoul(v, NULL, 10); i++; }
		else if (!strcmp(a, "--secondi") && v) { secondi = (uint32_t) strtoul(v, NULL, 10); i++; }
		else if (!strcmp(a, "--scena-fotogrammi") && v) {
			scena_fotogrammi = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--parti-a") && v) {
			parti_a_ns = strtoull(v, NULL, 10); i++;
		} else if (!strcmp(a, "--zavorra-us") && v) {
			zavorra_us = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--flusso") && v) {
			flusso = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--qp") && v) { qp = atoi(v); i++; }
		else if (!strcmp(a, "--profondita") && v) { profondita = atoi(v); i++; }
		else if (!strcmp(a, "--tetto-banda-mbit") && v) {
			tetto_banda_mbit = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--senza-scadenza")) { senza_scadenza = true; }
		else if (!strcmp(a, "--libero")) { libero = true; }
		else { uso(); return 2; }
	}
	if (!scena || !uscita || !fps || !secondi) { uso(); return 2; }
	if (profondita != 8 && profondita != 10) {
		fprintf(stderr, "⛔ --profondita vuole 8 o 10, non %d\n", profondita);
		return 2;
	}
	if (scena_fotogrammi < 1 || scena_fotogrammi > BUFFER_MAX) {
		fprintf(stderr, "⛔ --scena-fotogrammi dev'essere fra 1 e %d\n", BUFFER_MAX);
		return 2;
	}
	bool sulla_scheda = !strcmp(strada, "scheda");

	/* ⛔ Il file di uscita si apre SUBITO: se da qui in poi qualcosa non va, il
	 *    banco trova un file che dice perche', non un file che manca. */
	FILE *j = fopen(uscita, "w");
	if (!j) {
		fprintf(stderr, "⛔ non si scrive %s: %s\n", uscita, strerror(errno));
		return 2;
	}
#define MUORI(...)                                                                       \
	do {                                                                             \
		char _m[512];                                                            \
		snprintf(_m, sizeof(_m), __VA_ARGS__);                                   \
		fprintf(stderr, "⛔ %s\n", _m);                                          \
		fprintf(j,                                                               \
		        "{\"nonce\": \"%s\", \"flusso\": %u, \"pid\": %d, \"aperto\": "   \
		        "false, \"errore\": \"%s\", \"scritto_ns\": %" PRIu64 "}\n",      \
		        nonce, flusso, (int) getpid(), _m, adesso_reale_ns());            \
		fclose(j);                                                               \
		return 1;                                                                \
	} while (0)

	/* ───────────────────────────────────────────────────────────────────────
	 * La scena: K fotogrammi BGRx, letti UNA volta.  ⚠ `mmap` in sola lettura,
	 * cosi' N processi che leggono lo stesso file dividono la stessa cache di
	 * pagine invece di moltiplicarla per N.
	 */
	size_t byte_fotogramma = (size_t) larghezza * altezza * 4;
	size_t byte_scena = byte_fotogramma * scena_fotogrammi;
	int fs = open(scena, O_RDONLY);
	if (fs < 0)
		MUORI("non si apre la scena %s: %s", scena, strerror(errno));
	struct stat st;
	if (fstat(fs, &st) < 0 || (size_t) st.st_size < byte_scena) {
		close(fs);
		MUORI("la scena %s ha %lld byte, ne servono %zu per %ux%u x%u", scena,
		      (long long) st.st_size, byte_scena, larghezza, altezza, scena_fotogrammi);
	}
	const uint8_t *pixel_scena = mmap(NULL, byte_scena, PROT_READ, MAP_PRIVATE, fs, 0);
	close(fs);
	if (pixel_scena == MAP_FAILED)
		MUORI("mmap della scena fallito: %s", strerror(errno));

	/* ───────────────────────────────────────────────────────────────────────
	 * La strada della scheda: K buffer GBM riempiti ORA, una volta sola.
	 * ⛔ Riempirli a ogni fotogramma metterebbe una `memcpy` da 33 MB nel
	 *    cammino misurato — cioe' misurerebbe la CPU credendo di misurare la GPU.
	 */
	struct gbm_device *gbm = NULL;
	struct gbm_bo *bo[BUFFER_MAX] = { 0 };
	CodificatoreSuperficie sup[BUFFER_MAX];
	int fd_drm = -1;
	uint32_t passo_scheda = 0;
	memset(sup, 0, sizeof(sup));

	if (sulla_scheda) {
		fd_drm = open(nodo, O_RDWR | O_CLOEXEC);
		if (fd_drm < 0)
			MUORI("il nodo %s non si apre: %s", nodo, strerror(errno));
		gbm = gbm_create_device(fd_drm);
		if (!gbm)
			MUORI("gbm_create_device su %s non riesce", nodo);
		for (uint32_t k = 0; k < scena_fotogrammi; k++) {
			bo[k] = gbm_bo_create(gbm, larghezza, altezza, GBM_FORMAT_XRGB8888,
			                      GBM_BO_USE_LINEAR | GBM_BO_USE_RENDERING);
			if (!bo[k])
				MUORI("gbm_bo_create %ux%u fallito al buffer %u", larghezza,
				      altezza, k);
			uint32_t passo = 0;
			void *dati = NULL;
			void *p = gbm_bo_map(bo[k], 0, 0, larghezza, altezza,
			                     GBM_BO_TRANSFER_WRITE, &passo, &dati);
			if (!p)
				MUORI("gbm_bo_map fallito al buffer %u", k);
			for (uint32_t y = 0; y < altezza; y++)
				memcpy((uint8_t *) p + (size_t) y * passo,
				       pixel_scena + (size_t) k * byte_fotogramma
				           + (size_t) y * larghezza * 4,
				       (size_t) larghezza * 4);
			gbm_bo_unmap(bo[k], dati);
			passo_scheda = passo;
			/* ⛔ La guardia dei 64 byte di `codificatore.h`: se il passo non
			 *    e' importabile NON si prosegue di nascosto sulla strada della
			 *    memoria — sarebbe un'altra grandezza sotto la stessa
			 *    etichetta. */
			if (!codificatore_stride_importabile(passo))
				MUORI("passo GBM %u non multiplo di %u: questa tela non e' "
				      "importabile e NON si ripiega in silenzio",
				      passo, codificatore_allineamento_scheda());
			sup[k].fd = gbm_bo_get_fd(bo[k]);
			if (sup[k].fd < 0)
				MUORI("gbm_bo_get_fd fallito al buffer %u", k);
			sup[k].offset = gbm_bo_get_offset(bo[k], 0);
			sup[k].stride = passo;
			sup[k].larghezza = larghezza;
			sup[k].altezza = altezza;
			sup[k].formato_drm = DRM_FORMAT_XRGB8888;
			sup[k].modificatore = gbm_bo_get_modifier(bo[k]);
			sup[k].generazione = 1;
		}
	}

	/* ───────────────────────────────────────────────────────────────────────
	 * ⛔⭐⭐ IL TETTO DI BANDA — e con lui il MODO DI CONTROLLO DEL BITRATE.
	 *
	 * ⛔ Si chiama la **stessa** funzione che chiama il prodotto
	 *    (`figlio.c:5999`, `codificatore_tetto_banda()`), e non si riscrivono i
	 *    tre numeri qui: filo, punto di lavoro e serbatoio si derivano dal
	 *    pavimento **dentro `codificatore.c`**, in un posto solo.  Riscriverli
	 *    qui sarebbe misurare un secondo prodotto e chiamarlo il primo.
	 *
	 * ⛔ E si chiama PRIMA di `codificatore_nuovo()`: la variabile e' statica del
	 *    codificatore e decide `modo_bitrate_voluto()`, che gira dentro
	 *    l'apertura.  Chiamarla dopo darebbe **CQP** con l'etichetta «QVBR».
	 */
	codificatore_tetto_banda(tetto_banda_mbit);

	/* ───────────────────────────────────────────────────────────────────────
	 * Il codificatore DEL PRODOTTO, chiesto per nome.
	 */
	CodificatoreRichiesta r = {
		.codec = codec,
		.componente = componente,
		.nodo_rendering = nodo,
		.potenza = potenza,
		.larghezza = larghezza,
		.altezza = altezza,
		.fotogrammi_al_secondo = fps,
		.modo = CODIFICATORE_QUALITA_QP,
		.qualita = qp,
		.profondita = profondita,
		.livello_x10 = 0, /* ⚠ nessun tetto: qui si misura il ritmo, non §4.3 */
		.formato = CODIFICATORE_PIXEL_BGRX,
		.chiavi_ogni = 0,
	};
	char errore[512] = { 0 };
	Codificatore *cod = codificatore_nuovo(&r, errore, sizeof(errore));
	if (!cod)
		MUORI("il codificatore non si e' aperto: %s", errore);
	if (sulla_scheda && !codificatore_in_hardware(cod))
		MUORI("«%s» non e' in hardware: la strada della scheda non esiste, e NON "
		      "si ripiega sulla memoria in silenzio",
		      componente);

	uint32_t richiesti = fps * secondi;
	uint64_t *t_cod = calloc(richiesti + 1, sizeof(uint64_t));
	uint64_t *t_conv = calloc(richiesti + 1, sizeof(uint64_t));
	uint64_t *t_car = calloc(richiesti + 1, sizeof(uint64_t));
	uint64_t *t_tot = calloc(richiesti + 1, sizeof(uint64_t));
	uint64_t *t_rit = calloc(richiesti + 1, sizeof(uint64_t));
	if (!t_cod || !t_conv || !t_car || !t_tot || !t_rit)
		MUORI("memoria finita per le tracce di %u fotogrammi", richiesti);

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐ LA PARTENZA SINCRONIZZATA.  N processi che partono quando gli pare non
	 *    saturano insieme: il primo finirebbe mentre l'ultimo apre.  ⇒ Ci si da'
	 *    un istante di orologio, e chi arriva tardi **lo dichiara**
	 *    (`in_orario: false`) invece di far finta di niente.
	 */
	uint64_t pronto_ns = adesso_reale_ns();
	bool in_orario = true;
	if (parti_a_ns) {
		if (pronto_ns > parti_a_ns)
			in_orario = false;
		else
			dormi_fino_reale(parti_a_ns);
	}

	uint64_t t0_mono = adesso_ns();
	uint64_t periodo_ns = 1000000000ull / fps;
	uint64_t fine_mono = t0_mono + (uint64_t) secondi * 1000000000ull;
	uint32_t prodotti = 0, chiavi = 0, trattenuti = 0, ricodifiche = 0;
	uint64_t byte_totali = 0;
	uint64_t impronta = FNV_BASE;
	int stato = 0;
	char guasto[256] = { 0 };

	for (uint32_t k = 0; k < richiesti; k++) {
		if (!libero) {
			uint64_t quando = t0_mono + (uint64_t) k * periodo_ns;
			uint64_t ora = adesso_ns();
			if (ora < quando) {
				uint64_t manca = quando - ora;
				struct timespec t = { (time_t) (manca / 1000000000ull),
					              (long) (manca % 1000000000ull) };
				nanosleep(&t, NULL);
			}
		}
		if (!senza_scadenza && adesso_ns() >= fine_mono)
			break; /* ⚠ il tempo e' finito: quel che manca e' il ritardo */

		zavorra(zavorra_us);

		uint64_t a = adesso_ns();
		CodificatoreFotogramma fg;
		bool ok;
		uint32_t quale = k % scena_fotogrammi;
		if (sulla_scheda)
			ok = codificatore_comprimi_scheda(cod, &sup[quale], &fg);
		else
			ok = codificatore_comprimi(cod,
			                           pixel_scena + (size_t) quale * byte_fotogramma,
			                           larghezza * 4, &fg);
		uint64_t b = adesso_ns();
		if (!ok) {
			snprintf(guasto, sizeof(guasto),
			         "il fotogramma %u non e' stato prodotto", k);
			stato = 1;
			break;
		}
		t_conv[prodotti] = fg.us_conversione;
		t_car[prodotti] = fg.us_caricamento;
		t_cod[prodotti] = fg.us_codifica;
		t_tot[prodotti] = (b - a) / 1000;
		/* ⭐ Il ritardo di CONSEGNA: quanto e' uscito dopo l'istante in cui
		 *    l'orologio lo voleva.  E' il sintomo che l'utente sente; i tre
		 *    tempi qui sopra sono il meccanismo. */
		uint64_t voluto = t0_mono + (uint64_t) k * periodo_ns + periodo_ns;
		t_rit[prodotti] = b > voluto ? (b - voluto) / 1000 : 0;
		byte_totali += fg.byte;
		impronta = impronta_avanza(impronta, fg.dati, fg.byte);
		chiavi += fg.chiave ? 1 : 0;
		trattenuti += fg.trattenuto ? 1 : 0;
		ricodifiche += fg.ricodifiche;
		prodotti++;
		codificatore_rilascia(cod);
	}
	uint64_t t1_mono = adesso_ns();
	double durata = (double) (t1_mono - t0_mono) / 1e9;

	Riassunto r_cod = riassumi(t_cod, prodotti), r_conv = riassumi(t_conv, prodotti);
	Riassunto r_car = riassumi(t_car, prodotti), r_tot = riassumi(t_tot, prodotti);
	Riassunto r_rit = riassumi(t_rit, prodotti);

	struct rusage ru;
	getrusage(RUSAGE_SELF, &ru);
	double cpu_u = (double) ru.ru_utime.tv_sec + (double) ru.ru_utime.tv_usec / 1e6;
	double cpu_s = (double) ru.ru_stime.tv_sec + (double) ru.ru_stime.tv_usec / 1e6;

	const CodificatoreConfessione *c = codificatore_confessione(cod);
	double fps_eff = durata > 0 ? (double) prodotti / durata : 0.0;

	fprintf(j,
	        "{\"nonce\": \"%s\", \"flusso\": %u, \"pid\": %d, \"aperto\": true,\n"
	        " \"errore\": \"%s\", \"strada\": \"%s\", \"nodo\": \"%s\",\n"
	        " \"misura\": \"%ux%u\", \"passo_scheda\": %u, \"qp\": %d,\n"
	        /* ⛔ Quel che si e' CHIESTO, scritto accanto a quel che e' uscito: il
	         *    banco confronta i due e non si fida di nessuno dei due da solo. */
	        " \"codec_chiesto\": \"%s\", \"profondita_chiesta\": %d,\n"
	        " \"tetto_banda_mbit\": %u, \"senza_scadenza\": %s,\n"
	        " \"impronta\": \"%016llx\", \"impronta_che_cos_e\": \"FNV-1a 64 bit sui "
	        "byte del flusso — ⛔ NON e' un md5\",\n"
	        " \"fps_richiesti\": %u, \"secondi_richiesti\": %u, \"libero\": %s,\n"
	        " \"zavorra_us\": %u, \"pronto_ns\": %" PRIu64 ", \"parti_a_ns\": %" PRIu64 ",\n"
	        " \"in_orario\": %s, \"scritto_ns\": %" PRIu64 ",\n"
	        " \"fotogrammi_richiesti\": %u, \"fotogrammi_prodotti\": %u,\n"
	        " \"durata_s\": %.4f, \"fps_effettivi\": %.3f,\n"
	        " \"mpixel_s\": %.3f, \"byte_totali\": %" PRIu64 ", \"mbit_s\": %.3f,\n"
	        " \"chiavi\": %u, \"trattenuti\": %u, \"ricodifiche\": %u,\n"
	        " \"us_codifica\": {\"mediana\": %" PRIu64 ", \"p95\": %" PRIu64
	        ", \"peggiore\": %" PRIu64 ", \"somma\": %" PRIu64 "},\n"
	        " \"us_conversione\": {\"mediana\": %" PRIu64 ", \"p95\": %" PRIu64
	        ", \"peggiore\": %" PRIu64 ", \"somma\": %" PRIu64 "},\n"
	        " \"us_caricamento\": {\"mediana\": %" PRIu64 ", \"p95\": %" PRIu64
	        ", \"peggiore\": %" PRIu64 ", \"somma\": %" PRIu64 "},\n"
	        " \"us_totale\": {\"mediana\": %" PRIu64 ", \"p95\": %" PRIu64
	        ", \"peggiore\": %" PRIu64 ", \"somma\": %" PRIu64 "},\n"
	        " \"us_ritardo\": {\"mediana\": %" PRIu64 ", \"p95\": %" PRIu64
	        ", \"peggiore\": %" PRIu64 ", \"somma\": %" PRIu64 "},\n"
	        " \"cpu_utente_s\": %.3f, \"cpu_sistema_s\": %.3f, \"rss_kb\": %ld,\n"
	        " \"confessione\": {\"nome\": \"%s\", \"componente\": \"%s\",\n"
	        "   \"ha_obbedito\": %s, \"perche_no\": \"%s\", \"in_hardware\": %s,\n"
	        "   \"nodo\": \"%s\", \"fornitore_va\": \"%s\", \"bassa_potenza\": %s,\n"
	        "   \"bassa_potenza_verificata\": %s, \"stringa_codec\": \"%s\",\n"
	        "   \"profilo_flusso\": %d, \"livello_flusso\": %d, \"profondita_flusso\": %d,\n"
	        "   \"larghezza_flusso\": %u, \"altezza_flusso\": %u,\n"
	        "   \"larghezza_codificata\": %u, \"altezza_codificata\": %u,\n"
	        "   \"letto_dal_flusso\": %s, \"riordina\": %s, \"fotogrammi_b\": %d,\n"
	        "   \"profondita_asincrona\": %d, \"modo_bitrate\": %d,\n"
	        /* ⭐⭐ I DUE TESTIMONI DEL BITRATE che stanno in un campo (il terzo
	         *     sono i byte, ed e' `mbit_s` qui sopra).  ⚠ `modi_bitrate_letti
	         *     == false` vuol dire «non ho saputo chiedere», NON «c'e' solo il
	         *     CQP»; e a tetto spento i `banda_*` sono zeri che vogliono dire
	         *     «non chiesto», non «nessun limite». */
	        "   \"modi_bitrate\": %u, \"modi_bitrate_letti\": %s,\n"
	        "   \"banda_punto\": %lld, \"banda_filo\": %lld,\n"
	        "   \"banda_serbatoio\": %d, \"banda_serbatoio_ms\": %u,\n"
	        "   \"global_header\": %s, \"promozione_8_a_10\": %s}}\n",
	        nonce, flusso, (int) getpid(), guasto, strada, nodo, larghezza, altezza,
	        passo_scheda, qp,
	        codec == CODIFICATORE_HEVC ? "hevc" : "h264", profondita,
	        tetto_banda_mbit, senza_scadenza ? "true" : "false",
	        (unsigned long long) impronta,
	        fps, secondi, libero ? "true" : "false", zavorra_us,
	        pronto_ns, parti_a_ns, in_orario ? "true" : "false", adesso_reale_ns(),
	        richiesti, prodotti, durata, fps_eff,
	        fps_eff * (double) larghezza * (double) altezza / 1e6, byte_totali,
	        durata > 0 ? (double) byte_totali * 8.0 / durata / 1e6 : 0.0, chiavi,
	        trattenuti, ricodifiche, r_cod.mediana, r_cod.p95, r_cod.peggiore, r_cod.somma,
	        r_conv.mediana, r_conv.p95, r_conv.peggiore, r_conv.somma, r_car.mediana,
	        r_car.p95, r_car.peggiore, r_car.somma, r_tot.mediana, r_tot.p95,
	        r_tot.peggiore, r_tot.somma, r_rit.mediana, r_rit.p95, r_rit.peggiore,
	        r_rit.somma, cpu_u, cpu_s, ru.ru_maxrss, codificatore_nome(cod),
	        c->componente ? c->componente : "?", c->ha_obbedito ? "true" : "false",
	        c->perche_no, c->in_hardware ? "true" : "false", c->nodo, c->fornitore_va,
	        c->bassa_potenza ? "true" : "false",
	        c->bassa_potenza_verificata ? "true" : "false", c->stringa_codec,
	        c->profilo_flusso, c->livello_flusso, c->profondita_flusso, c->larghezza_flusso,
	        c->altezza_flusso, c->larghezza_codificata, c->altezza_codificata,
	        c->letto_dal_flusso ? "true" : "false", c->riordina ? "true" : "false",
	        c->fotogrammi_b, c->profondita_asincrona, c->modo_bitrate,
	        c->modi_bitrate, c->modi_bitrate_letti ? "true" : "false",
	        (long long) c->banda_punto, (long long) c->banda_filo,
	        c->banda_serbatoio, c->banda_serbatoio_ms,
	        c->global_header ? "true" : "false", c->promozione_8_a_10 ? "true" : "false");
	fclose(j);

	codificatore_libera(cod);
	for (uint32_t k = 0; k < scena_fotogrammi; k++) {
		if (sup[k].fd > 0)
			close(sup[k].fd);
		if (bo[k])
			gbm_bo_destroy(bo[k]);
	}
	if (gbm)
		gbm_device_destroy(gbm);
	if (fd_drm >= 0)
		close(fd_drm);
	free(t_cod); free(t_conv); free(t_car); free(t_tot); free(t_rit);
	munmap((void *) pixel_scena, byte_scena);
	return stato;
}
