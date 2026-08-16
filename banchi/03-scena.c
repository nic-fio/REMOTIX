/*
 * 03-scena.c — LA SCENA DELLA FASE 3.  Un client Wayland a schermo intero,
 * opaco, che ridisegna a OGNI frame callback del compositore, e che dipinge
 * su ogni fotogramma una MARCA leggibile a macchina.
 *
 *   ./03-scena --giro g1                       schermo intero, movimento «barra»
 *   ./03-scena --finestra 1280x720 --secondi 5 per provare senza rubare lo schermo
 *   ./03-scena --istantanee 2 --dopo 120       scarica due fotogrammi consecutivi
 *
 * ===========================================================================
 * ⛔ PERCHE' ESISTE, E PERCHE' NON BASTAVA `weston-simple-egl -f -o`
 *
 * `LEZIONI.md` §1.1 prescrive la forma e la dichiara non negoziabile: *«un
 * client a schermo intero, opaco, che ridisegna a ogni frame callback del
 * compositore»*, e accanto *«va contato quanto disegna il client»*.  Il prezzo
 * gia' pagato per non averla: **tutte** le misure di ritmo delle fasi 3-9 di
 * v1, buttate.
 *
 * `weston-simple-egl -f -o` fa esattamente quella forma — e infatti la forma e'
 * copiata da li'.  Ma due cose mancano, e sono tutte e due misure della fase 3:
 *
 *   1. ⛔ **non c'e'**: su questa macchina `weston-simple-egl` non e'
 *      installato (`command -v` vuoto, 13 agosto 2026) e il pacchetto weston
 *      non c'e'.  Un banco che dipende da un binario assente non e' un ripiego,
 *      e' un banco che non gira;
 *   2. ⛔ **non porta la marca**.  Il triangolo che gira non dice QUALE
 *      fotogramma e'.  Senza quel numero:
 *        · **M6** («il fotogramma e' del giro prima») resta l'unico strumento
 *          che vede quel guasto e non e' mai stato misurato sulla catena vera;
 *        · il controllo `giro` di **M8** resta NON APPLICABILE, perche' il
 *          prodotto non conosce il nome del giro del banco e il protocollo non
 *          ha un campo per dirglielo (`fasi/rapporti/F2-6-giudizio.md`);
 *        · l'anello del ritardo di `PIANO.md` fase 3 non ha un istante da cui
 *          contare.
 *
 * ⇒ la marca porta il numero del disegno **dentro i pixel**.  Il prodotto la
 *   trasporta senza saperlo, e il banco se la rilegge dall'altro capo: non si
 *   chiede all'imputato come si chiama, gli si legge il numero addosso.
 *
 * ===========================================================================
 * ⛔ IL CONTROLLO CHE DICE DI CHI E' IL TETTO
 *
 * §1.1: *«Accanto va contato quanto disegna il client: e' il controllo che dice
 * se il tetto e' del compositore o della scena.  Senza quel controllo, il 7
 * agosto avremmo attribuito a Mutter un tetto che era della scena — e
 * viceversa.»*
 *
 * ⇒ questo programma tiene, in un blocco di memoria condivisa leggibile da
 *   fuori (`/dev/shm/<nome>`), quattro conti distinti che NON sono lo stesso
 *   numero, e tenerli separati e' tutto il punto:
 *
 *     `disegni`     quante volte abbiamo dipinto un buffer
 *     `commit`      quante volte l'abbiamo consegnato al compositore
 *     `presentati`  quante volte il compositore dice di averlo MESSO SULLO
 *                   SCHERMO (wp_presentation).  ⭐ E' l'unico dei quattro che
 *                   arriva dall'altro lato — `LEZIONI.md` §1.7, si verifica
 *                   dal lato che riceve
 *     `attese`      quante volte abbiamo dovuto ASPETTARE un buffer libero,
 *                   cioe' quante volte il tetto e' stato NOSTRO
 *
 *   ⚠ `presentati` puo' non esserci: se il compositore non offre
 *   `wp_presentation` il campo `presentazione_disponibile` vale 0 e il conto
 *   resta a zero.  ⛔ «zero perche' non presentato» e «zero perche' non
 *   misurabile» hanno lo stesso aspetto, ed e' `LEZIONI.md` §1.9: il campo che
 *   li distingue c'e' apposta.
 *
 * ===========================================================================
 * ⛔ PERCHE' MEMORIA CONDIVISA (wl_shm) E NON EGL
 *
 * §1.1 cita `weston-simple-egl` e dice che *«costa niente di GPU»*.  Qui si usa
 * `wl_shm`, e la ragione va scritta invece che lasciata capire:
 *
 *   · ⭐ la marca vuole pixel ESATTI.  Una cella dipinta con OpenGL passa per
 *     il rasterizzatore, e mezzo pixel di differenza fra quel che la C dipinge
 *     e quel che la Python rilegge e' il tipo di scarto che si scopre alla
 *     terza misura sbagliata;
 *   · EGL su un Mutter `--headless` dipende dal backend surfaceless del
 *     driver: ci sono macchine dove funziona e macchine dove no.  Un banco che
 *     non parte non misura niente.  `wl_shm` c'e' sempre;
 *   · ⛔ e il prezzo, che si dichiara: con `wl_shm` il compositore deve
 *     caricare in GPU quel che gli diamo.  ⇒ il danno (`--danno`) di riposo e'
 *     **preciso**, cioe' si dichiarano solo i rettangoli cambiati, e il carico
 *     resta piccolo.  `--danno pieno` esiste per fare il confronto: se il ritmo
 *     cambia fra i due, il tetto e' del trasferimento e non del compositore.
 *
 * ⚠ E il conto `disegni` e' li' apposta per dirlo: se il client disegna 60 al
 *   secondo e il compositore ne presenta 37, il tetto NON e' della scena.  Se
 *   il client ne disegna 37, il tetto e' nostro e Mutter non c'entra.
 *
 * ===========================================================================
 * ⛔ IL MOVIMENTO SI DICHIARA — non e' una decorazione, e non e' «sempre lo
 * stesso»
 *
 * §1.1 dice «si muove sempre».  Ma *quanto* si muove decide che cosa si sta
 * misurando, e un banco che non lo dichiara produce due misure diverse sotto
 * la stessa etichetta (forma E2 di `REVIEWER.md`).  Tre modi, dichiarati nello
 * stato e nel nome del giro:
 *
 *   `marca`   cambia solo il blocco della marca (~83 000 px a 1080p, 4 %).
 *             ⭐ E' gia' abbastanza per M6: bastano ~130 px a piena escursione
 *             perche' il Δ di M6 superi i 3 dB su una catena a 42 dB.
 *   `barra`   ⭐ IL RIPOSO.  La marca piu' una barra verticale larga W/10 che
 *             attraversa lo schermo in ~2 s.  E' il compromesso: si muove
 *             qualcosa di grosso, senza chiedere al codificatore un fotogramma
 *             intero nuovo ogni volta.
 *   `pieno`   tutte le bande verticali cambiano colore a ogni fotogramma.
 *             ⛔ NON e' il riposo: e' lo strobo.  Ogni fotogramma e' un
 *             fotogramma nuovo per intero, e il tetto che ne esce e' il tetto
 *             del codificatore, non quello del compositore.  Serve a fare quel
 *             confronto, non a misurare il ritmo.
 *
 * ===========================================================================
 * ⛔ LA MARCA — la forma, e perche' regge alla codifica con perdita
 *
 * Il mandato: *«non usare una differenza di un livello di grigio che HEVC
 * spiana»*.  Le quattro scelte, ciascuna con la sua ragione:
 *
 *   1. **due soli livelli, ai due estremi**: bit 1 = bianco (255,255,255),
 *      bit 0 = nero (0,0,0).  Escursione 255 su 255.  Un QP che spianasse
 *      questo avrebbe gia' distrutto l'immagine;
 *   2. **celle grandi** (24 px di lato di riposo): un blocco di trasformata
 *      HEVC va da 4 a 32 px.  Una cella da 24 px e' letta al centro, sui 12 px
 *      centrali, cioe' lontano dai bordi dove sta il *ringing*;
 *   3. **niente crominanza**: bianco e nero hanno la stessa crominanza.  ⇒ il
 *      sottocampionamento 4:2:0 non tocca la marca, che vive tutta nella
 *      luminanza;
 *   4. **zona di quiete nera** attorno al blocco: il contenuto vicino non
 *      sanguina dentro la prima e l'ultima cella.
 *
 * ⛔ E il carico utile porta un CRC-16, che e' quel che rende dicibile «la
 *   marca NON c'e'».  Un rilevatore che dice sempre si' misura zero ed e'
 *   felice a torto (`STUDI.md` §web §6.3, controllo P3).
 *
 *   sync      8 bit   0xB2, fisso
 *   versione  8 bit   0x01
 *   giro     32 bit   FNV-1a a 32 bit del nome del giro
 *   disegno  32 bit   ⭐ il contatore: cresce di 1 a ogni disegno
 *   istante  48 bit   CLOCK_MONOTONIC in microsecondi, al momento del disegno
 *   crc      16 bit   CRC-16/CCITT-FALSE sui 15 byte precedenti
 *   ------------------
 *   totale  144 bit = 18 colonne x 8 righe
 *
 * ⚠ L'istante e' quello in cui il fotogramma e' stato COMPOSTO, non quello in
 *   cui e' comparso sullo schermo: fra i due c'e' il commit, il compositore e
 *   il pannello.  Chi misura il ritardo usa questo come istante di partenza e
 *   ci somma il pezzo cieco dichiarato (`STUDI.md` §web §6.3).  ⛔ Chiamarlo «istante
 *   in cui il pixel si e' acceso» sarebbe la forma E1.
 *
 * ---------------------------------------------------------------------------
 * Costruzione: vedi `03-scena-accendi.sh costruisci`.
 * Lettura della marca: `03-marca.py`.  Le due geometrie DEVONO coincidere, e
 * `03-scena-certifica.sh` lo verifica invece di sperarlo.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <wayland-client.h>

#include "xdg-shell-client-protocol.h"
#include "presentation-time-client-protocol.h"

/* ─────────────────────────────────────────────────────────────────────────
 * LA GEOMETRIA DELLA MARCA.  ⛔ Questi otto numeri sono l'interfaccia fra
 * questo file e `03-marca.py`, e non sono negoziabili in silenzio: chi ne
 * cambia uno cambia anche l'altro file, e la certificazione se ne accorge
 * (controllo P6).
 * ───────────────────────────────────────────────────────────────────────── */
#define MARCA_VERSIONE   0x01
#define MARCA_SYNC       0xB2
#define MARCA_COLONNE    18
#define MARCA_RIGHE      8
#define MARCA_BIT        (MARCA_COLONNE * MARCA_RIGHE)   /* 144 */
#define MARCA_CELLA_DEF  24
#define MARCA_MARGINE_DEF 32
#define MARCA_QUIETE_DEF 12

/* Lo stato condiviso.  ⛔ Se cambia questa struttura cambia anche
 * `03-marca.py` (`FORMATO_STATO`), e `magia`+`versione` esistono perche' un
 * lettore rimasto indietro riceva un rifiuto invece di numeri a caso. */
#define STATO_MAGIA    0x524D5853u   /* 'RMXS' */
#define STATO_VERSIONE 2u            /* 2: i campi del rilevatore di corsa a vuoto */

struct stato_condiviso {
	uint32_t magia;
	uint32_t versione;
	uint32_t taglia;
	uint32_t riempi0;

	/* ⛔ Seqlock: chi legge prende `seq` prima e dopo, e se sono uguali e
	 *    pari il campione e' coerente.  Senza, un lettore puo' pescare un
	 *    `disegno` nuovo con un `istante` vecchio e credere a un ritardo
	 *    che non e' mai esistito. */
	uint64_t seq;

	uint64_t disegni;
	uint64_t commit;
	uint64_t presentati;
	uint64_t attese;
	uint64_t scarti_presentazione;

	uint64_t avvio_monotonico_us;
	uint64_t avvio_reale_us;
	uint64_t ultimo_disegno_us;
	uint64_t ultimo_presentato_us;
	uint64_t ultimo_presentato_reale_us;

	uint32_t giro_numero;
	uint32_t larghezza;
	uint32_t altezza;
	uint32_t cella;
	uint32_t colonne;
	uint32_t righe;
	uint32_t margine;
	uint32_t quiete;
	uint32_t movimento;                 /* 0 marca · 1 barra · 2 pieno */
	uint32_t danno;                     /* 0 preciso · 1 pieno */
	int32_t  pid;
	uint32_t presentazione_disponibile; /* ⛔ distingue «zero» da «non misurabile» */
	uint32_t schermo_intero;
	uint32_t riempi1;
	char     nome_giro[64];
	char     versione_scena[32];
	/* ⭐ Su quale uscita il COMPOSITORE dice che la superficie e' finita.
	 *    ⛔ Vuota = nessun `wl_surface.enter` ancora arrivato, che NON vuol
	 *    dire «su nessuna»: vuol dire «non lo so». */
	char     uscita_confermata[64];
	char     uscita_chiesta[64];

	/* ═══════════════════════════════════════════════════════════════════
	 * ⛔⭐ IL RILEVATORE DELLA CORSA A VUOTO — versione 2 del blocco.
	 *
	 * Aggiunto il 13 agosto 2026, dopo che il gruppo dello step 1 ha visto
	 * questa scena fare **13 521 disegni in 25 s = 540/s su un monitor a
	 * 60 Hz** dentro il suo banco, mentre da sola ne fa 60.
	 *
	 * ⛔ IL PUNTO, ed e' la ragione per cui questi campi vengono prima della
	 *    cura: **540 disegni al secondo su un monitor a 60 Hz non e' un
	 *    numero, e' un'accusa.**  Se la scena non aspetta piu' il
	 *    `wl_surface.frame`, il conto `disegni` smette di misurare i
	 *    ridisegni del compositore e `attese` va a zero **per la ragione
	 *    sbagliata** — non «il compositore ci sta dietro» ma «non gli stiamo
	 *    piu' chiedendo il callback».  E' il numero su cui si appoggiano
	 *    tutti gli altri gruppi che diventa **verde per costruzione**:
	 *    `LEZIONI.md` §2.2, la prova verde mentre il difetto e' vivo.
	 *
	 * ⇒ Non si misura il RITMO e poi lo si giudica: si misura **la causa**,
	 *   che e' un invariante di protocollo osservabile e non ha bisogno di
	 *   sapere a che frequenza va il monitor:
	 *
	 *       ⛔ i `wl_surface.frame` IN VOLO non possono mai essere piu' di 1.
	 *
	 *   Un client corretto ne ha esattamente uno fra un commit e il
	 *   successivo.  Due vuol dire che qualcuno ha disegnato senza essere
	 *   stato invitato, e da li' la cosa si moltiplica: con N callback in
	 *   volo, ogni giro del compositore ne consegna N e il ritmo va a N×60.
	 *   ⭐ 540/60 = 9 ⇒ nove callback in volo.  Il numero torna.
	 * ═══════════════════════════════════════════════════════════════════ */
	uint64_t rientri;                  /* `disegna()` chiamata dentro sé stessa */
	uint64_t corse_a_vuoto;            /* quante volte i callback in volo > 1 */
	uint64_t disegni_senza_callback;   /* disegni non nati da un frame callback */
	uint64_t saltati_senza_buffer;     /* ⭐ rinviati, NON disegnati a vuoto */
	uint32_t callback_in_volo;
	uint32_t callback_in_volo_massimo; /* ⛔ > 1 = corsa a vuoto, sempre */
	uint32_t refresh_mhz;              /* dall'uscita, per chi vuole il rapporto */
	uint32_t fidato;                   /* ⭐ 0 = NON consegnare questi numeri */
};

/* ───────────────────────────────────────────────────────────────────────── */

struct riquadro { int32_t x, y, w, h; };

/* ⛔⛔ LE USCITE — buco trovato il 13 agosto 2026 leggendo `03-b14-scena.c`,
 *     che l'altro gruppo della fase 3 aveva scritto in parallelo.
 *
 *     La prima stesura di questo file chiedeva `set_fullscreen(NULL)`, cioe'
 *     **lasciava scegliere il monitor al compositore**.  Sul mio Mutter
 *     headless c'e' un monitor solo e non mordeva; sul palco della fase 3 ce
 *     ne sono tre (quello della sessione, quello del server 7561 dell'utente,
 *     e quello del banco), e una scena finita sul monitor sbagliato e' **un
 *     metro puntato sul buio che pero' dichiara la mira** — il difetto che
 *     F2.2 ha pagato il 12 agosto 2026.
 *
 *     ⇒ due cose, e sono diverse (`LEZIONI.md` §1.8 e §1.11 punto 2):
 *       1. **si CHIEDE** il monitor per nome (`--uscita`), e se quel nome non
 *          c'e' si fallisce dichiarandolo, invece di ripiegare in silenzio;
 *       2. **si VERIFICA che abbia obbedito**, e dal lato che riceve: e'
 *          `wl_surface.enter` a dire su quale uscita la superficie e' finita,
 *          non la nostra intenzione.  Se non arriva nessun `enter` entro il
 *          tetto, `uscita_confermata` resta vuota e lo stato lo dice. */
#define USCITE_MAX 16
struct uscita {
	struct wl_output *wl;
	uint32_t nome_globale;
	char     nome[64];          /* wl_output.name, solo dalla versione 4 */
	char     descrizione[128];  /* wl_output.description, idem */
	int32_t  larghezza, altezza, refresh_mhz;
};

struct buffer {
	struct wl_buffer *wl;
	uint32_t *pixel;
	size_t    byte;
	bool      occupato;
};

#define BUFFER_N 3

static struct {
	struct wl_display    *display;
	struct wl_registry   *registry;
	struct wl_compositor *compositor;
	struct wl_shm        *shm;
	struct xdg_wm_base   *wm_base;
	struct wp_presentation *presentazione;
	struct wl_surface    *superficie;
	struct xdg_surface   *xdg_superficie;
	struct xdg_toplevel  *toplevel;

	struct wl_shm_pool   *pool;
	int                   pool_fd;
	void                 *pool_mem;
	size_t                pool_byte;
	struct buffer         buffer[BUFFER_N];

	uint32_t *sfondo;          /* il fondo, dipinto una volta sola */
	size_t    sfondo_byte;

	int32_t   larghezza, altezza;
	int32_t   conf_larghezza, conf_altezza;
	bool      configurato;
	bool      ridimensiona;
	bool      chiudi;

	/* le opzioni */
	const char *nome_giro;
	uint32_t    giro_numero;
	int         movimento;      /* 0 marca · 1 barra · 2 pieno */
	int         danno;          /* 0 preciso · 1 pieno */
	int         cella, margine, quiete;
	bool        schermo_intero;
	int         fin_secondi;
	long        fin_fotogrammi;
	long        istantanee;
	long        istantanee_dopo;
	const char *istantanea_prefisso;
	const char *nome_shm;
	bool        loquace;
	bool        elenca_uscite;

	/* i conti */
	uint64_t disegni, commit, presentati, attese, scarti_presentazione;
	/* ⛔ il rilevatore — vedi il commentone in `struct stato_condiviso` */
	uint64_t rientri, corse_a_vuoto, disegni_senza_callback, saltati_senza_buffer;
	int      callback_in_volo, callback_in_volo_massimo;
	bool     dentro_disegna;      /* la guardia di rientro */
	bool     chiesto_disegno;     /* ⭐ il callback ha chiesto un disegno */
	bool     nato_da_callback;    /* questo disegno viene da un frame callback? */
	int      guasto;              /* 0 nessuno · 1 rientro (per certificare) */
	uint64_t avvio_us, ultimo_disegno_us, ultimo_presentato_us;
	uint64_t ultimo_presentato_reale_us;
	bool     presentazione_viva;

	struct riquadro barra_ora, barra_prima;
	bool     barra_prima_valida;
	uint32_t versione_compositore;
	bool     danno_in_buffer;      /* wl_surface_damage_buffer, da wl_surface v4 */

	struct uscita uscite[USCITE_MAX];
	int           quante_uscite;
	const char   *uscita_chiesta;
	struct uscita *uscita_scelta;
	char          uscita_confermata[64];   /* ⭐ da wl_surface.enter */

	struct stato_condiviso *stato;
	int                     stato_fd;

	long istantanee_fatte;
} S;

static volatile sig_atomic_t interrotto = 0;

static void su_segnale(int s) { (void)s; interrotto = 1; }

static void muori(const char *fmt, ...)
{
	va_list ap;
	va_start(ap, fmt);
	fputs("⛔ ", stderr);
	vfprintf(stderr, fmt, ap);
	fputc('\n', stderr);
	va_end(ap);
	exit(1);
}

static uint64_t ora_monotonica_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
}

static uint64_t ora_reale_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_REALTIME, &t);
	return (uint64_t)t.tv_sec * 1000000ull + (uint64_t)(t.tv_nsec / 1000);
}

/* FNV-1a a 32 bit.  ⛔ Non e' una firma: e' un nome corto.  Serve solo a far
 * stare il nome del giro in 32 bit di marca, e due nomi diversi che
 * collidessero darebbero un M8 verde a torto — per questo il banco stampa
 * SEMPRE il numero accanto al nome, cosi' una collisione si vede. */
static uint32_t fnv1a32(const char *s)
{
	uint32_t h = 2166136261u;
	for (; *s; s++) { h ^= (unsigned char)*s; h *= 16777619u; }
	return h;
}

/* CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, niente riflessioni. */
static uint16_t crc16(const uint8_t *d, size_t n)
{
	uint16_t c = 0xFFFF;
	for (size_t i = 0; i < n; i++) {
		c ^= (uint16_t)d[i] << 8;
		for (int b = 0; b < 8; b++)
			c = (c & 0x8000) ? (uint16_t)((c << 1) ^ 0x1021) : (uint16_t)(c << 1);
	}
	return c;
}

/* ─────────────────────────────────────────────────────────────────────────
 * LO STATO CONDIVISO
 * ───────────────────────────────────────────────────────────────────────── */
static void stato_apri(void)
{
	char percorso[256];
	snprintf(percorso, sizeof percorso, "/%s", S.nome_shm);

	S.stato_fd = shm_open(percorso, O_CREAT | O_RDWR, 0644);
	if (S.stato_fd < 0)
		muori("shm_open(%s): %s", percorso, strerror(errno));
	if (ftruncate(S.stato_fd, sizeof(struct stato_condiviso)) < 0)
		muori("ftruncate(%s): %s", percorso, strerror(errno));
	S.stato = mmap(NULL, sizeof(struct stato_condiviso),
	               PROT_READ | PROT_WRITE, MAP_SHARED, S.stato_fd, 0);
	if (S.stato == MAP_FAILED)
		muori("mmap(%s): %s", percorso, strerror(errno));

	memset(S.stato, 0, sizeof *S.stato);
	S.stato->magia    = STATO_MAGIA;
	S.stato->versione = STATO_VERSIONE;
	S.stato->taglia   = (uint32_t)sizeof(struct stato_condiviso);
	S.stato->pid      = (int32_t)getpid();
	S.stato->giro_numero = S.giro_numero;
	S.stato->cella    = (uint32_t)S.cella;
	S.stato->colonne  = MARCA_COLONNE;
	S.stato->righe    = MARCA_RIGHE;
	S.stato->margine  = (uint32_t)S.margine;
	S.stato->quiete   = (uint32_t)S.quiete;
	S.stato->movimento = (uint32_t)S.movimento;
	S.stato->danno    = (uint32_t)S.danno;
	S.stato->schermo_intero = S.schermo_intero ? 1u : 0u;
	S.stato->avvio_monotonico_us = S.avvio_us;
	S.stato->avvio_reale_us      = ora_reale_us();
	snprintf(S.stato->nome_giro, sizeof S.stato->nome_giro, "%s", S.nome_giro);
	snprintf(S.stato->versione_scena, sizeof S.stato->versione_scena, "03-scena/2");
	snprintf(S.stato->uscita_chiesta, sizeof S.stato->uscita_chiesta, "%s",
	         S.uscita_chiesta ? S.uscita_chiesta : "");
}

/* ⛔ Il seqlock si scrive dispari-modifica-pari.  Le due barriere non sono
 *    pignoleria: senza, il compilatore puo' spostare l'incremento di `seq`
 *    dopo la scrittura dei campi, e il lettore vedrebbe coerente un campione
 *    che non lo e'. */
static void stato_pubblica(void)
{
	if (!S.stato) return;
	S.stato->seq++;
	__atomic_thread_fence(__ATOMIC_RELEASE);

	S.stato->disegni    = S.disegni;
	S.stato->commit     = S.commit;
	S.stato->presentati = S.presentati;
	S.stato->attese     = S.attese;
	S.stato->scarti_presentazione = S.scarti_presentazione;
	S.stato->ultimo_disegno_us    = S.ultimo_disegno_us;
	S.stato->ultimo_presentato_us = S.ultimo_presentato_us;
	S.stato->ultimo_presentato_reale_us = S.ultimo_presentato_reale_us;
	S.stato->larghezza  = (uint32_t)S.larghezza;
	S.stato->altezza    = (uint32_t)S.altezza;
	S.stato->presentazione_disponibile = S.presentazione_viva ? 1u : 0u;

	S.stato->rientri                  = S.rientri;
	S.stato->corse_a_vuoto            = S.corse_a_vuoto;
	S.stato->disegni_senza_callback   = S.disegni_senza_callback;
	S.stato->saltati_senza_buffer     = S.saltati_senza_buffer;
	S.stato->callback_in_volo         = (uint32_t)S.callback_in_volo;
	S.stato->callback_in_volo_massimo = (uint32_t)S.callback_in_volo_massimo;
	S.stato->refresh_mhz = S.uscita_scelta ? (uint32_t)S.uscita_scelta->refresh_mhz
	                     : (S.quante_uscite > 0 ? (uint32_t)S.uscite[0].refresh_mhz : 0u);

	/* ⛔⭐ `fidato` E' LA RISPOSTA ALLA DOMANDA DEL COORDINATORE.
	 *
	 *    «un conto di 540/s su un monitor a 60 Hz e' un fatto osservabile: va
	 *    ACCUSATO, non consegnato.»  ⇒ chi legge questo blocco non riceve un
	 *    numero da interpretare: riceve **un numero e un verdetto sul numero**.
	 *    Finche' `fidato` e' 0, ogni cella misurata con questa scena e' `[?]`.
	 *
	 * ⚠ E le tre condizioni sono TUTTE cause, non sintomi: nessuna di loro ha
	 *   bisogno di sapere a che frequenza gira il monitor.  Il rapporto col
	 *   refresh lo puo' fare chi legge, e lo fa `03-marca.py` — ma come
	 *   controllo IN PIU', non come unico.  Un rilevatore che guardasse solo
	 *   il ritmo tacerebbe su un monitor a 540 Hz, e mentirebbe su uno a 30. */
	S.stato->fidato = (S.rientri == 0 && S.corse_a_vuoto == 0 &&
	                   S.callback_in_volo_massimo <= 1) ? 1u : 0u;

	__atomic_thread_fence(__ATOMIC_RELEASE);
	S.stato->seq++;
}

/* ─────────────────────────────────────────────────────────────────────────
 * IL DISEGNO
 * ───────────────────────────────────────────────────────────────────────── */
static inline uint32_t colore(uint8_t r, uint8_t g, uint8_t b)
{
	/* XRGB8888: 0xXXRRGGBB in memoria little-endian ⇒ byte B,G,R,X */
	return 0xFF000000u | ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
}

static void riempi(uint32_t *px, int stride, struct riquadro q, uint32_t c)
{
	for (int y = q.y; y < q.y + q.h; y++) {
		uint32_t *riga = px + (size_t)y * stride;
		for (int x = q.x; x < q.x + q.w; x++)
			riga[x] = c;
	}
}

static void ritaglia(struct riquadro *q, int W, int H)
{
	if (q->x < 0) { q->w += q->x; q->x = 0; }
	if (q->y < 0) { q->h += q->y; q->y = 0; }
	if (q->x + q->w > W) q->w = W - q->x;
	if (q->y + q->h > H) q->h = H - q->y;
	if (q->w < 0) q->w = 0;
	if (q->h < 0) q->h = 0;
}

/* Il fondo: una sfumatura diagonale con un reticolo fine sopra.
 *
 * ⚠ Il reticolo NON e' decorazione: una scena tutta morbida rende cieco
 *   qualunque strumento di allineamento (`02-giudizio-mira.py`, punto 1 —
 *   spostare una sfumatura di una riga cambia ogni pixel di un millesimo).
 *   Qui non c'e' un pettine a passo 1 px, perche' questa scena passa per una
 *   codifica 4:2:0 con perdita e un pettine a passo 1 px verrebbe spianato:
 *   il reticolo e' a passo 8 px, che e' il compromesso. */
static void dipingi_sfondo(void)
{
	const int W = S.larghezza, H = S.altezza;
	for (int y = 0; y < H; y++) {
		uint32_t *riga = S.sfondo + (size_t)y * W;
		int fy = (255 * y) / (H > 1 ? H - 1 : 1);
		for (int x = 0; x < W; x++) {
			int fx = (255 * x) / (W > 1 ? W - 1 : 1);
			int v = (fx + fy) / 2;
			int r = 40 + v / 3, g = 60 + v / 3, b = 90 + v / 4;
			if (((x >> 3) + (y >> 3)) & 1) { r += 12; g += 12; b += 12; }
			riga[x] = colore((uint8_t)(r > 255 ? 255 : r),
			                 (uint8_t)(g > 255 ? 255 : g),
			                 (uint8_t)(b > 255 ? 255 : b));
		}
	}
}

/* Le bande del modo `pieno`. */
static void dipingi_bande(uint32_t *px, uint64_t n)
{
	const int W = S.larghezza, H = S.altezza;
	const int larghezza_banda = W / 24 > 8 ? W / 24 : 8;
	static const uint8_t tavolozza[6][3] = {
		{220, 40, 40}, {40, 200, 60}, {40, 80, 220},
		{220, 200, 40}, {200, 40, 200}, {40, 200, 200},
	};
	for (int x0 = 0, i = 0; x0 < W; x0 += larghezza_banda, i++) {
		int w = (x0 + larghezza_banda > W) ? W - x0 : larghezza_banda;
		const uint8_t *c = tavolozza[(size_t)(i + (int)(n % 6)) % 6];
		struct riquadro q = { x0, 0, w, H };
		riempi(px, W, q, colore(c[0], c[1], c[2]));
	}
}

/* La barra del modo `barra`: attraversa lo schermo in ~2 s a 60 fotogrammi. */
static struct riquadro posizione_barra(uint64_t n)
{
	const int W = S.larghezza, H = S.altezza;
	int larghezza = W / 10 > 24 ? W / 10 : 24;
	int corsa = W + larghezza;
	int passo = corsa / 120 > 1 ? corsa / 120 : 1;
	int x = (int)((n * (uint64_t)passo) % (uint64_t)corsa) - larghezza;
	struct riquadro q = { x, 0, larghezza, H };
	return q;
}

/* ⛔ LA MARCA.  Il carico utile si costruisce byte per byte, poi si srotola in
 *    144 bit e ogni bit diventa una cella.  L'ordine e' riga per riga, il bit
 *    piu' significativo per primo: chi legge fa lo stesso cammino al
 *    contrario, e la certificazione lo verifica su valori noti. */
static void componi_carico(uint8_t bit[MARCA_BIT], uint32_t disegno, uint64_t istante_us)
{
	uint8_t corpo[15];
	corpo[0] = MARCA_VERSIONE;
	corpo[1] = (uint8_t)(S.giro_numero >> 24);
	corpo[2] = (uint8_t)(S.giro_numero >> 16);
	corpo[3] = (uint8_t)(S.giro_numero >> 8);
	corpo[4] = (uint8_t)(S.giro_numero);
	corpo[5] = (uint8_t)(disegno >> 24);
	corpo[6] = (uint8_t)(disegno >> 16);
	corpo[7] = (uint8_t)(disegno >> 8);
	corpo[8] = (uint8_t)(disegno);
	uint64_t t = istante_us & 0xFFFFFFFFFFFFull;   /* 48 bit */
	corpo[9]  = (uint8_t)(t >> 40);
	corpo[10] = (uint8_t)(t >> 32);
	corpo[11] = (uint8_t)(t >> 24);
	corpo[12] = (uint8_t)(t >> 16);
	corpo[13] = (uint8_t)(t >> 8);
	corpo[14] = (uint8_t)(t);

	uint16_t c = crc16(corpo, sizeof corpo);

	uint8_t tutto[18];
	tutto[0] = MARCA_SYNC;
	memcpy(tutto + 1, corpo, sizeof corpo);
	tutto[16] = (uint8_t)(c >> 8);
	tutto[17] = (uint8_t)(c);

	for (int i = 0; i < MARCA_BIT; i++)
		bit[i] = (uint8_t)((tutto[i >> 3] >> (7 - (i & 7))) & 1);
}

static struct riquadro riquadro_marca(void)
{
	struct riquadro q = { S.margine, S.margine,
	                      MARCA_COLONNE * S.cella, MARCA_RIGHE * S.cella };
	return q;
}

static struct riquadro riquadro_marca_con_quiete(void)
{
	struct riquadro q = riquadro_marca();
	q.x -= S.quiete; q.y -= S.quiete;
	q.w += 2 * S.quiete; q.h += 2 * S.quiete;
	ritaglia(&q, S.larghezza, S.altezza);
	return q;
}

static void dipingi_marca(uint32_t *px, uint32_t disegno, uint64_t istante_us)
{
	const int W = S.larghezza;
	uint8_t bit[MARCA_BIT];
	componi_carico(bit, disegno, istante_us);

	struct riquadro q = riquadro_marca_con_quiete();
	riempi(px, W, q, colore(0, 0, 0));          /* zona di quiete + fondo nero */

	const uint32_t bianco = colore(255, 255, 255);
	struct riquadro b = riquadro_marca();
	for (int i = 0; i < MARCA_BIT; i++) {
		if (!bit[i]) continue;                  /* il nero c'e' gia' */
		int r = i / MARCA_COLONNE, c = i % MARCA_COLONNE;
		struct riquadro cella = { b.x + c * S.cella, b.y + r * S.cella,
		                          S.cella, S.cella };
		ritaglia(&cella, S.larghezza, S.altezza);
		if (cella.w > 0 && cella.h > 0)
			riempi(px, W, cella, bianco);
	}
}

/* ─────────────────────────────────────────────────────────────────────────
 * LE ISTANTANEE — i pixel che il client ha DIPINTO, scaricati su file.
 *
 * ⛔ Non e' una cattura del compositore, e chiamarla cosi' sarebbe la forma
 *    E1: e' il buffer che abbiamo consegnato.  Serve a due cose che la
 *    certificazione fa e la cattura vera non farebbe meglio:
 *      · avere DUE fotogrammi consecutivi noti, per M6;
 *      · confrontare quel che la C ha dipinto con quel che la Python rilegge,
 *        che e' l'unico controllo incrociato fra i due pittori.
 * ───────────────────────────────────────────────────────────────────────── */
static void scarica_istantanea(const uint32_t *px, uint32_t disegno, uint64_t istante_us)
{
	char nome[512];
	const int W = S.larghezza, H = S.altezza;

	snprintf(nome, sizeof nome, "%s-%06u.rgb24", S.istantanea_prefisso, disegno);
	FILE *f = fopen(nome, "wb");
	if (!f) { fprintf(stderr, "⚠ istantanea «%s»: %s\n", nome, strerror(errno)); return; }
	uint8_t *riga = malloc((size_t)W * 3);
	if (!riga) { fclose(f); return; }
	for (int y = 0; y < H; y++) {
		const uint32_t *src = px + (size_t)y * W;
		for (int x = 0; x < W; x++) {
			uint32_t v = src[x];
			riga[x * 3 + 0] = (uint8_t)(v >> 16);
			riga[x * 3 + 1] = (uint8_t)(v >> 8);
			riga[x * 3 + 2] = (uint8_t)(v);
		}
		fwrite(riga, 1, (size_t)W * 3, f);
	}
	free(riga);
	fclose(f);

	snprintf(nome, sizeof nome, "%s-%06u.json", S.istantanea_prefisso, disegno);
	f = fopen(nome, "w");
	if (!f) return;
	/* ⛔ Quel che la scena DICHIARA di aver dipinto.  La certificazione
	 *    confronta questo con quel che il lettore rilegge dai pixel: se
	 *    coincidono, i due pittori parlano la stessa lingua. */
	fprintf(f,
	    "{\n"
	    "  \"disegno\": %u,\n"
	    "  \"istante_us\": %llu,\n"
	    "  \"giro\": \"%s\",\n"
	    "  \"giro_numero\": %u,\n"
	    "  \"larghezza\": %d,\n"
	    "  \"altezza\": %d,\n"
	    "  \"cella\": %d,\n"
	    "  \"colonne\": %d,\n"
	    "  \"righe\": %d,\n"
	    "  \"margine\": %d,\n"
	    "  \"quiete\": %d,\n"
	    "  \"movimento\": %d,\n"
	    "  \"formato\": \"rgb24\",\n"
	    "  \"chi\": \"03-scena.c — i pixel DIPINTI dal client, non una cattura del compositore\"\n"
	    "}\n",
	    disegno, (unsigned long long)istante_us, S.nome_giro, S.giro_numero,
	    W, H, S.cella, MARCA_COLONNE, MARCA_RIGHE, S.margine, S.quiete,
	    S.movimento);
	fclose(f);
	S.istantanee_fatte++;
}

/* ─────────────────────────────────────────────────────────────────────────
 * WAYLAND — i buffer
 * ───────────────────────────────────────────────────────────────────────── */
static void su_rilascio(void *dati, struct wl_buffer *wl)
{
	(void)wl;
	((struct buffer *)dati)->occupato = false;
}
static const struct wl_buffer_listener ascolta_buffer = { su_rilascio };

static void chiudi_pool(void)
{
	for (int i = 0; i < BUFFER_N; i++) {
		if (S.buffer[i].wl) wl_buffer_destroy(S.buffer[i].wl);
		S.buffer[i].wl = NULL;
		S.buffer[i].pixel = NULL;
		S.buffer[i].occupato = false;
	}
	if (S.pool) { wl_shm_pool_destroy(S.pool); S.pool = NULL; }
	if (S.pool_mem) { munmap(S.pool_mem, S.pool_byte); S.pool_mem = NULL; }
	if (S.pool_fd >= 0) { close(S.pool_fd); S.pool_fd = -1; }
	S.pool_byte = 0;
}

static int file_anonimo(size_t byte)
{
	int fd = memfd_create("remotix-scena", MFD_CLOEXEC);
	if (fd < 0) return -1;
	if (ftruncate(fd, (off_t)byte) < 0) { close(fd); return -1; }
	return fd;
}

static void crea_pool(void)
{
	const int W = S.larghezza, H = S.altezza;
	size_t uno = (size_t)W * (size_t)H * 4;
	size_t tutto = uno * BUFFER_N;

	chiudi_pool();
	S.pool_fd = file_anonimo(tutto);
	if (S.pool_fd < 0) muori("memfd_create/ftruncate: %s", strerror(errno));
	S.pool_mem = mmap(NULL, tutto, PROT_READ | PROT_WRITE, MAP_SHARED, S.pool_fd, 0);
	if (S.pool_mem == MAP_FAILED) muori("mmap del pool: %s", strerror(errno));
	S.pool_byte = tutto;
	S.pool = wl_shm_create_pool(S.shm, S.pool_fd, (int32_t)tutto);

	for (int i = 0; i < BUFFER_N; i++) {
		S.buffer[i].wl = wl_shm_pool_create_buffer(
		    S.pool, (int32_t)(uno * (size_t)i), W, H, W * 4,
		    WL_SHM_FORMAT_XRGB8888);
		S.buffer[i].pixel = (uint32_t *)((uint8_t *)S.pool_mem + uno * (size_t)i);
		S.buffer[i].byte = uno;
		S.buffer[i].occupato = false;
		wl_buffer_add_listener(S.buffer[i].wl, &ascolta_buffer, &S.buffer[i]);
	}

	free(S.sfondo);
	S.sfondo = malloc(uno);
	if (!S.sfondo) muori("niente memoria per il fondo");
	S.sfondo_byte = uno;
	dipingi_sfondo();
}

/* ⛔⛔ QUESTA FUNZIONE ERA IL DIFETTO, ED ERA SCRITTA COSI':
 *
 *        for (giro = 0; giro < 200; giro++) {
 *            …cerca un buffer libero…
 *            if (wl_display_dispatch(S.display) < 0) return NULL;   ⛔
 *        }
 *
 *    `disegna()` viene chiamata **da dentro un gestore di eventi**
 *    (`su_frame`).  Chiamare `wl_display_dispatch()` li' dentro e' un
 *    dispatch **rientrante**: libwayland puo' consegnare, in quel momento, un
 *    ALTRO `frame done` gia' in coda.  Quello richiama `su_frame` → `disegna()`
 *    annidata, che fa il suo commit e chiede **un nuovo** `wl_surface.frame`;
 *    poi la `disegna()` esterna riprende e ne chiede **un altro**.
 *
 *    ⇒ da UN callback in volo se ne ottengono DUE, e la cosa si moltiplica:
 *      con N in volo il compositore ne consegna N a ogni giro, e il ritmo va a
 *      N×60.  ⭐ Da qui i **540 disegni al secondo** su un monitor a 60 Hz.
 *
 * ⚠ E si accende SOLO fuori da casa: serve che almeno una volta tutti e tre i
 *   buffer siano occupati insieme, cioe' che il compositore li tenga piu' a
 *   lungo — che e' quel che succede quando accanto gira una cattura PipeWire e
 *   non quando la scena e' sola. **Da sola andava. Nel banco d'altri no.**
 *
 * ⭐ LA CURA NON E' UN DISPATCH PIU' FURBO: e' non aspettare affatto qui.
 *    Se non c'e' un buffer libero si RINVIA — `chiesto_disegno` resta acceso e
 *    il ciclo principale riprova appena arriva un `wl_buffer.release`.  Niente
 *    ricorsione, e l'attesa si conta lo stesso (che era il motivo per cui
 *    quella funzione esisteva).
 */
static struct buffer *buffer_libero(void)
{
	for (int i = 0; i < BUFFER_N; i++)
		if (!S.buffer[i].occupato)
			return &S.buffer[i];
	return NULL;
}

/* ─────────────────────────────────────────────────────────────────────────
 * WAYLAND — la presentazione (wp_presentation)
 * ───────────────────────────────────────────────────────────────────────── */
static void pres_sincronizzato(void *d, struct wp_presentation_feedback *f,
                               struct wl_output *o)
{ (void)d; (void)f; (void)o; }

static void pres_presentato(void *d, struct wp_presentation_feedback *f,
                            uint32_t alto, uint32_t basso, uint32_t nsec,
                            uint32_t rifresco, uint32_t seq_alto,
                            uint32_t seq_basso, uint32_t bandiere)
{
	(void)d; (void)rifresco; (void)seq_alto; (void)seq_basso; (void)bandiere;
	uint64_t sec = ((uint64_t)alto << 32) | basso;
	S.presentati++;
	S.ultimo_presentato_us = sec * 1000000ull + nsec / 1000ull;
	S.ultimo_presentato_reale_us = ora_reale_us();
	wp_presentation_feedback_destroy(f);
	stato_pubblica();
}

static void pres_scartato(void *d, struct wp_presentation_feedback *f)
{
	(void)d;
	/* ⛔ «scartato» NON e' «presentato»: il compositore dice che quel
	 *    fotogramma non e' mai comparso.  Contarlo fra i presentati sarebbe
	 *    esattamente il conto gonfiato che la fase 9 di v1 ha pagato. */
	S.scarti_presentazione++;
	wp_presentation_feedback_destroy(f);
	stato_pubblica();
}

static const struct wp_presentation_feedback_listener ascolta_presentazione = {
	pres_sincronizzato, pres_presentato, pres_scartato
};

/* ─────────────────────────────────────────────────────────────────────────
 * IL CICLO: un disegno per ogni frame callback
 * ───────────────────────────────────────────────────────────────────────── */
static void disegna(void);

static void danneggia(int32_t x, int32_t y, int32_t w, int32_t h)
{
	if (S.danno_in_buffer)
		wl_surface_damage_buffer(S.superficie, x, y, w, h);
	else
		wl_surface_damage(S.superficie, x, y, w, h);
}

/* ⭐ IL CALLBACK NON DISEGNA PIU': ALZA UNA BANDIERA.
 *
 * ⛔ E' la meta' della cura che vale piu' dell'altra.  Finche' `su_frame`
 *    chiamava `disegna()` direttamente, ogni dispatch annidato che passava di
 *    qui apriva una ricorsione.  Adesso il disegno avviene in **un posto solo**
 *    — il ciclo principale — e nessun percorso di evento puo' piu' aggiungere
 *    un commit di nascosto.
 *
 * ⚠ E il conto dei callback in volo si tiene QUI e nel punto in cui si
 *   chiedono: e' un invariante, non una statistica. */
static void su_frame(void *d, struct wl_callback *cb, uint32_t t)
{
	(void)d; (void)t;
	wl_callback_destroy(cb);
	if (S.callback_in_volo > 0) S.callback_in_volo--;
	S.chiesto_disegno = true;
	S.nato_da_callback = true;
	/* ⛔ IL GUASTO DA INNESTARE — `--guasto rientro` rimette **esattamente** il
	 *    codice del 13 agosto: il callback che disegna da sé, dentro il
	 *    gestore.  Senza un modo di RIACCENDERE il difetto, «il rilevatore
	 *    funziona» non e' dimostrabile: sarebbe un banco verde che non
	 *    riproduce (`LEZIONI.md` §1.3), che e' la peggiore delle prove. */
	if (S.guasto == 1) disegna();
}
static const struct wl_callback_listener ascolta_frame = { su_frame };

/* Ritorna `true` se ha disegnato, `false` se ha RINVIATO (nessun buffer). */
static bool disegna_una_volta(void);

static void disegna(void)
{
	/* ⛔⭐ LA GUARDIA DI RIENTRO — ed e' il rilevatore, non la cura.
	 *
	 *    La cura vera e' che nessun gestore di eventi chiama piu' `disegna()`.
	 *    Ma una cura che si fida di sé stessa non e' una cura: se un giorno
	 *    qualcuno rimettesse un dispatch dentro un percorso di disegno, questa
	 *    guardia lo **conta** e lo **rifiuta**, e `fidato` va a zero.
	 *    ⚠ Senza, quel ritorno sarebbe di nuovo silenzioso. */
	if (S.dentro_disegna) {
		S.rientri++;
		/* ⚠ Sotto guasto la guardia CONTA ma non ferma: se fermasse, il
		 *   difetto non si riprodurrebbe e il rilevatore verrebbe certificato
		 *   contro un guasto che la cura stessa ha gia' tolto. */
		if (S.guasto != 1) return;
	}
	S.dentro_disegna = true;
	if (!disegna_una_volta())
		S.chiesto_disegno = true;   /* rinviato: si riprova al prossimo giro */
	S.dentro_disegna = false;
}

static bool disegna_una_volta(void)
{
	if (S.chiudi || interrotto) return true;
	if (S.ridimensiona) {
		S.larghezza = S.conf_larghezza;
		S.altezza   = S.conf_altezza;
		crea_pool();
		S.ridimensiona = false;
		S.barra_prima_valida = false;
	}

	struct buffer *b = buffer_libero();
	/* ⛔ IL GUASTO, seconda meta': l'attesa RIENTRANTE di prima.  E' questa
	 *    che accende la moltiplicazione, e vuole che i buffer siano occupati
	 *    tutti insieme — cioe' un compositore carico, cioe' il banco di
	 *    qualcun altro e non il mio da solo. */
	if (!b && S.guasto == 1) {
		for (int giro = 0; giro < 200 && !b; giro++) {
			if (wl_display_dispatch(S.display) < 0) break;
			b = buffer_libero();
			if (b) S.attese++;
		}
	}
	if (!b) {
		/* ⛔ NON si aspetta, e NON si muore: si rinvia.  ⭐ E si conta, perche'
		 *    e' il numero che dice «il tetto e' NOSTRO»: era la ragione per
		 *    cui la vecchia `buffer_libero()` aspettava, e non si perde.
		 *    ⚠ `attese` e `saltati_senza_buffer` sono la stessa grandezza
		 *    contata una volta sola: `attese` resta il nome che gli altri
		 *    banchi leggono gia'. */
		S.attese++;
		S.saltati_senza_buffer++;
		return false;
	}

	const int W = S.larghezza, H = S.altezza;
	uint64_t n = S.disegni;                 /* il numero di QUESTO disegno */
	uint64_t istante = ora_monotonica_us();

	/* ⛔ L'istante si prende PRIMA di dipingere, perche' e' l'istante che
	 *    finisce dentro la marca e chi lo rilegge lo usa come partenza del
	 *    ritardo.  Prenderlo dopo lo farebbe sembrare piu' fresco di quel
	 *    che e', cioe' abbasserebbe un ritardo che non e' calato. */

	memcpy(b->pixel, S.sfondo, S.sfondo_byte);
	if (S.movimento == 2) dipingi_bande(b->pixel, n);

	struct riquadro barra = { 0, 0, 0, 0 };
	if (S.movimento == 1) {
		barra = posizione_barra(n);
		struct riquadro q = barra;
		ritaglia(&q, W, H);
		if (q.w > 0 && q.h > 0)
			riempi(b->pixel, W, q, colore(250, 250, 250));
	}

	dipingi_marca(b->pixel, (uint32_t)n, istante);

	/* Il danno.  ⛔ Dichiarato, non dedotto: `--danno pieno` e
	 *    `--danno preciso` producono due misure diverse e vanno tenute
	 *    separate (`REVIEWER.md` E2). */
	if (S.danno == 1 || S.movimento == 2) {
		danneggia(0, 0, W, H);
	} else {
		struct riquadro m = riquadro_marca_con_quiete();
		danneggia(m.x, m.y, m.w, m.h);
		if (S.movimento == 1) {
			struct riquadro q = barra; ritaglia(&q, W, H);
			if (q.w > 0 && q.h > 0)
				danneggia(q.x, q.y, q.w, q.h);
			if (S.barra_prima_valida) {
				struct riquadro p = S.barra_prima; ritaglia(&p, W, H);
				if (p.w > 0 && p.h > 0)
					danneggia(p.x, p.y, p.w, p.h);
			}
		}
	}
	S.barra_prima = barra;
	S.barra_prima_valida = (S.movimento == 1);

	if (S.istantanee > 0 && (long)n >= S.istantanee_dopo &&
	    S.istantanee_fatte < S.istantanee)
		scarica_istantanea(b->pixel, (uint32_t)n, istante);

	/* ⭐ Il feedback di presentazione si chiede PRIMA del commit, perche'
	 *    riguarda il contenuto che il commit rende corrente. */
	if (S.presentazione) {
		struct wp_presentation_feedback *f =
		    wp_presentation_feedback(S.presentazione, S.superficie);
		wp_presentation_feedback_add_listener(f, &ascolta_presentazione, NULL);
	}

	struct wl_callback *cb = wl_surface_frame(S.superficie);
	wl_callback_add_listener(cb, &ascolta_frame, NULL);
	S.callback_in_volo++;
	/* ⛔⭐ L'INVARIANTE, E L'ACCUSA.  Un client corretto ha ESATTAMENTE un
	 *     `wl_surface.frame` in volo fra un commit e il successivo.  Due vuol
	 *     dire che qualcuno ha disegnato senza essere stato invitato, e da li'
	 *     il ritmo si moltiplica.  ⇒ non si aspetta di vedere «540 al
	 *     secondo»: si vede QUI, alla prima volta, e si dichiara. */
	if (S.callback_in_volo > S.callback_in_volo_massimo)
		S.callback_in_volo_massimo = S.callback_in_volo;
	if (S.callback_in_volo > 1) {
		if (S.corse_a_vuoto == 0)
			fprintf(stderr, "⛔ CORSA A VUOTO: %d `wl_surface.frame` in volo "
			        "insieme (ne e' ammesso 1).  Da questo momento «disegni» "
			        "NON misura piu' i ridisegni del compositore e «attese» va "
			        "a zero per la ragione sbagliata.  ⇒ il blocco condiviso "
			        "esce con fidato=0: questi numeri NON si consegnano\n",
			        S.callback_in_volo);
		S.corse_a_vuoto++;
	}
	if (!S.nato_da_callback) S.disegni_senza_callback++;
	S.nato_da_callback = false;

	wl_surface_attach(S.superficie, b->wl, 0, 0);
	wl_surface_commit(S.superficie);
	b->occupato = true;

	S.disegni++;
	S.commit++;
	S.ultimo_disegno_us = istante;
	stato_pubblica();

	return true;
}

/* ─────────────────────────────────────────────────────────────────────────
 * WAYLAND — superficie, shell, registro
 * ───────────────────────────────────────────────────────────────────────── */
static void su_xdg_configure(void *d, struct xdg_surface *s, uint32_t serial)
{
	(void)d;
	xdg_surface_ack_configure(s, serial);
	if (!S.configurato) {
		S.configurato = true;
		if (S.conf_larghezza > 0 && S.conf_altezza > 0) {
			S.larghezza = S.conf_larghezza;
			S.altezza   = S.conf_altezza;
		}
		crea_pool();

		/* ⛔ OPACO, e si dichiara: senza la regione opaca il compositore
		 *    deve trattare la superficie come traslucida e fondere quel
		 *    che sta sotto — che e' lavoro in piu' che noi non abbiamo
		 *    chiesto e che finirebbe nel tetto misurato. */
		struct wl_region *r = wl_compositor_create_region(S.compositor);
		wl_region_add(r, 0, 0, S.larghezza, S.altezza);
		wl_surface_set_opaque_region(S.superficie, r);
		wl_region_destroy(r);

		S.ridimensiona = false;
		/* ⚠ Il PRIMO disegno non nasce da un frame callback — non ce n'e'
		 *   ancora nessuno — e va contato come tale invece di sporcare il
		 *   rilevatore: `disegni_senza_callback` deve valere 1, non 0 e non 9. */
		S.nato_da_callback = false;
		disegna();
	} else if (S.conf_larghezza > 0 && S.conf_altezza > 0 &&
	           (S.conf_larghezza != S.larghezza || S.conf_altezza != S.altezza)) {
		S.ridimensiona = true;
	}
}
static const struct xdg_surface_listener ascolta_xdg = { su_xdg_configure };

static void su_toplevel_configure(void *d, struct xdg_toplevel *t,
                                  int32_t w, int32_t h, struct wl_array *stati)
{
	(void)d; (void)t; (void)stati;
	if (w > 0 && h > 0) { S.conf_larghezza = w; S.conf_altezza = h; }
}
static void su_toplevel_chiudi(void *d, struct xdg_toplevel *t)
{ (void)d; (void)t; S.chiudi = true; }
static void su_toplevel_limiti(void *d, struct xdg_toplevel *t, int32_t w, int32_t h)
{ (void)d; (void)t; (void)w; (void)h; }
static void su_toplevel_capacita(void *d, struct xdg_toplevel *t, struct wl_array *a)
{ (void)d; (void)t; (void)a; }

static const struct xdg_toplevel_listener ascolta_toplevel = {
	su_toplevel_configure, su_toplevel_chiudi,
	su_toplevel_limiti, su_toplevel_capacita
};

static void su_ping(void *d, struct xdg_wm_base *b, uint32_t serial)
{ (void)d; xdg_wm_base_pong(b, serial); }
static const struct xdg_wm_base_listener ascolta_wm = { su_ping };

static void su_orologio(void *d, struct wp_presentation *p, uint32_t id)
{
	(void)d; (void)p;
	/* ⛔ Se il compositore presenta con un orologio che non e'
	 *    CLOCK_MONOTONIC, l'istante della marca e quello della presentazione
	 *    non sono confrontabili, e sottrarli darebbe un ritardo inventato. */
	if (id != CLOCK_MONOTONIC) {
		fprintf(stderr, "⚠ wp_presentation usa l'orologio %u, non CLOCK_MONOTONIC "
		        "(%d): gli istanti presentati NON sono confrontabili con quelli "
		        "della marca, e il conto dei presentati resta valido ma i tempi no\n",
		        id, CLOCK_MONOTONIC);
		S.presentazione_viva = false;
	}
}
static const struct wp_presentation_listener ascolta_pres_globale = { su_orologio };

/* ─────────────────────────────────────────────────────────────────────────
 * LE USCITE — si chiedono per nome, e si verifica dal lato che riceve
 * ───────────────────────────────────────────────────────────────────────── */
static void usc_geometria(void *d, struct wl_output *o, int32_t x, int32_t y,
                          int32_t lf, int32_t af, int32_t sub, const char *marca,
                          const char *modello, int32_t trasf)
{
	(void)o; (void)x; (void)y; (void)lf; (void)af; (void)sub; (void)trasf;
	struct uscita *u = d;
	/* ⚠ Ripiego per i compositori sotto la versione 4, che non mandano
	 *    `name`: marca+modello e' l'unico nome che si ha.  Si DICHIARA che e'
	 *    un ripiego, perche' due uscite dello stesso modello sarebbero
	 *    indistinguibili e la scelta diventerebbe un sorteggio. */
	if (!u->nome[0])
		snprintf(u->nome, sizeof u->nome, "%s %s", marca ? marca : "?",
		         modello ? modello : "?");
}
static void usc_modo(void *d, struct wl_output *o, uint32_t bandiere,
                     int32_t w, int32_t h, int32_t refresh)
{
	(void)o;
	struct uscita *u = d;
	if (bandiere & WL_OUTPUT_MODE_CURRENT) {
		u->larghezza = w; u->altezza = h; u->refresh_mhz = refresh;
	}
}
static void usc_fatto(void *d, struct wl_output *o) { (void)d; (void)o; }
static void usc_scala(void *d, struct wl_output *o, int32_t s) { (void)d; (void)o; (void)s; }
static void usc_nome(void *d, struct wl_output *o, const char *nome)
{
	(void)o;
	snprintf(((struct uscita *)d)->nome, sizeof ((struct uscita *)d)->nome, "%s", nome);
}
static void usc_descrizione(void *d, struct wl_output *o, const char *t)
{
	(void)o;
	snprintf(((struct uscita *)d)->descrizione,
	         sizeof ((struct uscita *)d)->descrizione, "%s", t);
}
static const struct wl_output_listener ascolta_uscita = {
	usc_geometria, usc_modo, usc_fatto, usc_scala, usc_nome, usc_descrizione
};

/* ⭐ `wl_surface.enter`: e' IL COMPOSITORE a dire su quale uscita la superficie
 *    e' finita.  E' il lato che riceve (`LEZIONI.md` §1.7): la nostra richiesta
 *    dice che cosa abbiamo chiesto, questo dice che cosa e' successo. */
static void sup_entrata(void *d, struct wl_surface *s, struct wl_output *o)
{
	(void)d; (void)s;
	for (int i = 0; i < S.quante_uscite; i++)
		if (S.uscite[i].wl == o) {
			snprintf(S.uscita_confermata, sizeof S.uscita_confermata,
			         "%s", S.uscite[i].nome);
			if (S.stato)
				snprintf(S.stato->uscita_confermata,
				         sizeof S.stato->uscita_confermata, "%s",
				         S.uscite[i].nome);
			return;
		}
	snprintf(S.uscita_confermata, sizeof S.uscita_confermata, "(ignota)");
}
static void sup_uscita(void *d, struct wl_surface *s, struct wl_output *o)
{ (void)d; (void)s; (void)o; }
static void sup_scala_preferita(void *d, struct wl_surface *s, int32_t f)
{ (void)d; (void)s; (void)f; }
static void sup_trasf_preferita(void *d, struct wl_surface *s, uint32_t t)
{ (void)d; (void)s; (void)t; }
static const struct wl_surface_listener ascolta_superficie = {
	sup_entrata, sup_uscita, sup_scala_preferita, sup_trasf_preferita
};

static void su_globale(void *d, struct wl_registry *r, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	(void)d;
	if (!strcmp(interfaccia, wl_compositor_interface.name)) {
		S.versione_compositore = versione < 4 ? versione : 4;
		S.compositor = wl_registry_bind(r, nome, &wl_compositor_interface,
		                                S.versione_compositore);
		/* ⛔ `wl_surface_damage_buffer` esiste da wl_surface v4.  Sotto, il
		 *    ripiego e' `wl_surface_damage`, che prende le coordinate della
		 *    SUPERFICIE invece che del buffer — uguali finche' il fattore di
		 *    scala e' 1.  ⚠ Si DICHIARA (CODER.md §4.2): un ripiego silenzioso
		 *    produce due comportamenti sotto la stessa etichetta. */
		S.danno_in_buffer = (S.versione_compositore >= 4);
		if (!S.danno_in_buffer)
			fprintf(stderr, "⚠ wl_compositor e' alla versione %u (< 4): niente "
			        "wl_surface_damage_buffer.  RIPIEGO DICHIARATO su "
			        "wl_surface_damage, che vale solo a fattore di scala 1\n",
			        versione);
	}
	else if (!strcmp(interfaccia, wl_shm_interface.name))
		S.shm = wl_registry_bind(r, nome, &wl_shm_interface, 1);
	else if (!strcmp(interfaccia, xdg_wm_base_interface.name))
		S.wm_base = wl_registry_bind(r, nome, &xdg_wm_base_interface, 1);
	else if (!strcmp(interfaccia, wl_output_interface.name)) {
		if (S.quante_uscite < USCITE_MAX) {
			struct uscita *u = &S.uscite[S.quante_uscite++];
			memset(u, 0, sizeof *u);
			u->nome_globale = nome;
			u->wl = wl_registry_bind(r, nome, &wl_output_interface,
			                         versione < 4 ? versione : 4);
			wl_output_add_listener(u->wl, &ascolta_uscita, u);
		} else {
			/* ⛔ Un'uscita persa in silenzio e' un monitor su cui la scena
			 *    non potra' mai andare, e nessuno saprebbe perche'. */
			fprintf(stderr, "⚠ piu' di %d uscite: la %u non e' stata presa, e "
			        "--uscita non la trovera'\n", USCITE_MAX, nome);
		}
	}
	else if (!strcmp(interfaccia, wp_presentation_interface.name)) {
		S.presentazione = wl_registry_bind(r, nome, &wp_presentation_interface, 1);
		S.presentazione_viva = true;
	}
}
static void su_globale_via(void *d, struct wl_registry *r, uint32_t nome)
{ (void)d; (void)r; (void)nome; }
static const struct wl_registry_listener ascolta_registro = { su_globale, su_globale_via };

/* ───────────────────────────────────────────────────────────────────────── */
static void uso(void)
{
	fputs(
	  "uso: 03-scena [opzioni]\n"
	  "  --giro NOME            il nome del giro (finisce NELLA MARCA, 32 bit FNV-1a)\n"
	  "  --movimento M          marca | barra (riposo) | pieno\n"
	  "  --danno D              preciso (riposo) | pieno\n"
	  "  --finestra WxH         invece dello schermo intero (per non rubare lo schermo)\n"
	  "  --secondi N            si ferma dopo N secondi\n"
	  "  --fotogrammi N         si ferma dopo N disegni\n"
	  "  --istantanee N         scarica N fotogrammi consecutivi\n"
	  "  --dopo N               ...ma solo dal disegno N in poi (riposo 120: NON l'avvio)\n"
	  "  --istantanea-prefisso P\n"
	  "  --cella N              lato della cella della marca (riposo 24)\n"
	  "  --margine N            (riposo 32)   --quiete N  (riposo 12)\n"
	  "  --uscita NOME          ⛔ IL MONITOR, per nome.  Se non c'e' si FALLISCE:\n"
	  "                         una scena sul monitor sbagliato e' un metro sul buio\n"
	  "  --uscite               elenca i monitor e esce\n"
	  "  --guasto rientro       ⛔ SOLO PER CERTIFICARE: rimette il dispatch\n"
	  "                         rientrante del 13 agosto (la corsa a vuoto)\n"
	  "  --shm NOME             il blocco di stato in /dev/shm (riposo remotix-scena)\n"
	  "  --loquace\n", stderr);
	exit(2);
}

int main(int argc, char **argv)
{
	memset(&S, 0, sizeof S);
	S.pool_fd = -1;
	S.stato_fd = -1;
	S.nome_giro = "senza-nome";
	S.movimento = 1;                 /* barra */
	S.danno = 0;                     /* preciso */
	S.cella = MARCA_CELLA_DEF;
	S.margine = MARCA_MARGINE_DEF;
	S.quiete = MARCA_QUIETE_DEF;
	S.schermo_intero = true;
	S.larghezza = 1280; S.altezza = 720;
	S.istantanee_dopo = 120;
	S.istantanea_prefisso = "scena";
	S.nome_shm = "remotix-scena";
	S.avvio_us = ora_monotonica_us();

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		#define SEGUE() (i + 1 < argc ? argv[++i] : (uso(), (char *)NULL))
		if (!strcmp(a, "--giro")) S.nome_giro = SEGUE();
		else if (!strcmp(a, "--movimento")) {
			const char *m = SEGUE();
			if (!strcmp(m, "marca")) S.movimento = 0;
			else if (!strcmp(m, "barra")) S.movimento = 1;
			else if (!strcmp(m, "pieno")) S.movimento = 2;
			else muori("--movimento «%s» non esiste: marca | barra | pieno", m);
		}
		else if (!strcmp(a, "--danno")) {
			const char *m = SEGUE();
			if (!strcmp(m, "preciso")) S.danno = 0;
			else if (!strcmp(m, "pieno")) S.danno = 1;
			else muori("--danno «%s» non esiste: preciso | pieno", m);
		}
		else if (!strcmp(a, "--finestra")) {
			const char *m = SEGUE();
			int w, h;
			if (sscanf(m, "%dx%d", &w, &h) != 2 || w < 640 || h < 480)
				muori("--finestra vuole WxH, almeno 640x480 (la marca non ci sta sotto)");
			S.schermo_intero = false;
			S.larghezza = w; S.altezza = h;
			S.conf_larghezza = w; S.conf_altezza = h;
		}
		else if (!strcmp(a, "--secondi")) S.fin_secondi = atoi(SEGUE());
		else if (!strcmp(a, "--fotogrammi")) S.fin_fotogrammi = atol(SEGUE());
		else if (!strcmp(a, "--istantanee")) S.istantanee = atol(SEGUE());
		else if (!strcmp(a, "--dopo")) S.istantanee_dopo = atol(SEGUE());
		else if (!strcmp(a, "--istantanea-prefisso")) S.istantanea_prefisso = SEGUE();
		else if (!strcmp(a, "--cella")) S.cella = atoi(SEGUE());
		else if (!strcmp(a, "--margine")) S.margine = atoi(SEGUE());
		else if (!strcmp(a, "--quiete")) S.quiete = atoi(SEGUE());
		else if (!strcmp(a, "--shm")) S.nome_shm = SEGUE();
		else if (!strcmp(a, "--uscita")) S.uscita_chiesta = SEGUE();
		else if (!strcmp(a, "--uscite")) S.elenca_uscite = true;
		else if (!strcmp(a, "--guasto")) {
			const char *g = SEGUE();
			if (!strcmp(g, "nessuno")) S.guasto = 0;
			else if (!strcmp(g, "rientro")) S.guasto = 1;
			else muori("--guasto «%s» non esiste: nessuno | rientro", g);
		}
		else if (!strcmp(a, "--loquace")) S.loquace = true;
		else uso();
		#undef SEGUE
	}
	S.giro_numero = fnv1a32(S.nome_giro);

	if (S.cella < 8)
		muori("--cella %d: sotto gli 8 px la lettura al centro della cella prende "
		      "meno di 4 px e la codifica la spiana.  Questo e' il confine, non un "
		      "consiglio", S.cella);

	signal(SIGINT, su_segnale);
	signal(SIGTERM, su_segnale);

	S.display = wl_display_connect(NULL);
	if (!S.display)
		muori("wl_display_connect: %s.  ⚠ WAYLAND_DISPLAY=«%s», XDG_RUNTIME_DIR=«%s»",
		      strerror(errno), getenv("WAYLAND_DISPLAY") ? getenv("WAYLAND_DISPLAY") : "(niente)",
		      getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(niente)");

	S.registry = wl_display_get_registry(S.display);
	wl_registry_add_listener(S.registry, &ascolta_registro, NULL);
	wl_display_roundtrip(S.display);

	if (!S.compositor) muori("il compositore non offre wl_compositor");
	if (!S.shm)        muori("il compositore non offre wl_shm");
	if (!S.wm_base)    muori("il compositore non offre xdg_wm_base");
	if (S.presentazione) {
		wp_presentation_add_listener(S.presentazione, &ascolta_pres_globale, NULL);
		wl_display_roundtrip(S.display);
	} else {
		/* ⛔ Si DICHIARA, e non si tace: senza questa riga «presentati = 0»
		 *    vorrebbe dire due cose diverse. */
		fprintf(stderr, "⚠ il compositore NON offre wp_presentation: il conto dei "
		        "fotogrammi PRESENTATI non e' misurabile su questo compositore, e "
		        "resta a zero.  ⛔ Zero-perche'-non-misurabile, non "
		        "zero-perche'-non-presentati\n");
	}

	xdg_wm_base_add_listener(S.wm_base, &ascolta_wm, NULL);

	/* ⛔ LE USCITE: si stampano SEMPRE, non solo quando la scelta fallisce.
	 *    Un elenco che compare solo nell'errore non aiuta chi deve scrivere
	 *    la riga di comando la prima volta. */
	if (S.loquace || S.uscita_chiesta || S.elenca_uscite) {
		fprintf(stderr, "uscite viste dal compositore: %d\n", S.quante_uscite);
		for (int i = 0; i < S.quante_uscite; i++)
			fprintf(stderr, "    «%s»  %dx%d @ %.3f Hz  %s\n",
			        S.uscite[i].nome, S.uscite[i].larghezza, S.uscite[i].altezza,
			        S.uscite[i].refresh_mhz / 1000.0, S.uscite[i].descrizione);
	}
	if (S.elenca_uscite) { wl_display_disconnect(S.display); return 0; }

	if (S.uscita_chiesta) {
		for (int i = 0; i < S.quante_uscite; i++)
			if (!strcmp(S.uscite[i].nome, S.uscita_chiesta)) {
				S.uscita_scelta = &S.uscite[i];
				break;
			}
		/* ⛔ NON si ripiega su «una qualunque»: `CODER.md` §3.9 — un
		 *    componente che sceglie da se' produce due misure diverse sotto la
		 *    stessa etichetta.  Su un palco a tre monitor «una qualunque» e'
		 *    il monitor sbagliato due volte su tre, e il metro direbbe
		 *    «la scena non c'e'» accusando il prodotto. */
		if (!S.uscita_scelta)
			muori("--uscita «%s» non esiste fra le %d che il compositore offre "
			      "(elencate qui sopra).  Non ripiego su un'altra: una scena sul "
			      "monitor sbagliato e' un metro puntato sul buio che pero' "
			      "dichiara la mira", S.uscita_chiesta, S.quante_uscite);
	}

	S.superficie = wl_compositor_create_surface(S.compositor);
	wl_surface_add_listener(S.superficie, &ascolta_superficie, NULL);
	S.xdg_superficie = xdg_wm_base_get_xdg_surface(S.wm_base, S.superficie);
	xdg_surface_add_listener(S.xdg_superficie, &ascolta_xdg, NULL);
	S.toplevel = xdg_surface_get_toplevel(S.xdg_superficie);
	xdg_toplevel_add_listener(S.toplevel, &ascolta_toplevel, NULL);
	xdg_toplevel_set_title(S.toplevel, "remotix-03-scena");
	xdg_toplevel_set_app_id(S.toplevel, "it.remotix.scena");
	if (S.schermo_intero)
		xdg_toplevel_set_fullscreen(S.toplevel,
		                            S.uscita_scelta ? S.uscita_scelta->wl : NULL);

	stato_apri();
	wl_surface_commit(S.superficie);
	wl_display_roundtrip(S.display);

	if (S.loquace)
		fprintf(stderr, "scena: giro «%s» (0x%08x) · %dx%d · movimento %d · "
		        "danno %d · shm /dev/shm/%s\n",
		        S.nome_giro, S.giro_numero, S.larghezza, S.altezza,
		        S.movimento, S.danno, S.nome_shm);

	uint64_t scadenza = S.fin_secondi > 0
	    ? S.avvio_us + (uint64_t)S.fin_secondi * 1000000ull : 0;

	while (!S.chiudi && !interrotto) {
		if (wl_display_dispatch(S.display) < 0) break;
		/* ⭐ IL DISEGNO AVVIENE IN UN POSTO SOLO, e questo e' il posto.
		 *    Nessun gestore di eventi disegna piu': alzano una bandiera, e
		 *    qui la si abbassa.  ⇒ nessun percorso di evento puo' aggiungere
		 *    un commit — e senza commit in piu' non nascono callback in piu'. */
		if (S.chiesto_disegno) {
			S.chiesto_disegno = false;
			disegna();
		}
		if (scadenza && ora_monotonica_us() >= scadenza) break;
		if (S.fin_fotogrammi > 0 && (long)S.disegni >= S.fin_fotogrammi) break;
		if (S.istantanee > 0 && S.istantanee_fatte >= S.istantanee &&
		    S.fin_secondi == 0 && S.fin_fotogrammi == 0)
			break;
	}

	stato_pubblica();
	double durata = (double)(ora_monotonica_us() - S.avvio_us) / 1e6;
	printf("{\"disegni\": %llu, \"commit\": %llu, \"presentati\": %llu, "
	       "\"scarti_presentazione\": %llu, \"attese\": %llu, "
	       "\"presentazione_disponibile\": %s, \"secondi\": %.3f, "
	       "\"disegni_al_secondo\": %.2f, \"larghezza\": %d, \"altezza\": %d, "
	       "\"giro\": \"%s\", \"giro_numero\": %u, \"istantanee\": %ld, "
	       "\"uscita_chiesta\": \"%s\", \"uscita_confermata\": \"%s\", "
	       "\"fidato\": %s, \"rientri\": %llu, \"corse_a_vuoto\": %llu, "
	       "\"callback_in_volo_massimo\": %d, \"disegni_senza_callback\": %llu, "
	       "\"saltati_senza_buffer\": %llu, \"refresh_mhz\": %d}\n",
	       (unsigned long long)S.disegni, (unsigned long long)S.commit,
	       (unsigned long long)S.presentati,
	       (unsigned long long)S.scarti_presentazione,
	       (unsigned long long)S.attese,
	       S.presentazione_viva ? "true" : "false",
	       durata, durata > 0 ? (double)S.disegni / durata : 0.0,
	       S.larghezza, S.altezza, S.nome_giro, S.giro_numero,
	       S.istantanee_fatte,
	       S.uscita_chiesta ? S.uscita_chiesta : "",
	       /* ⛔ Vuota vuol dire «nessun wl_surface.enter e' arrivato», cioe'
	        *    NON LO SO — non «su nessuna».  Chi legge deve poterli
	        *    distinguere (`LEZIONI.md` §1.9). */
	       S.uscita_confermata[0] ? S.uscita_confermata : "(nessun enter ricevuto)",
	       (S.rientri == 0 && S.corse_a_vuoto == 0 &&
	        S.callback_in_volo_massimo <= 1) ? "true" : "false",
	       (unsigned long long)S.rientri, (unsigned long long)S.corse_a_vuoto,
	       S.callback_in_volo_massimo,
	       (unsigned long long)S.disegni_senza_callback,
	       (unsigned long long)S.saltati_senza_buffer,
	       S.uscita_scelta ? S.uscita_scelta->refresh_mhz
	                       : (S.quante_uscite > 0 ? S.uscite[0].refresh_mhz : 0));

	chiudi_pool();
	free(S.sfondo);
	if (S.stato) munmap(S.stato, sizeof(struct stato_condiviso));
	if (S.stato_fd >= 0) close(S.stato_fd);
	wl_display_disconnect(S.display);
	return 0;
}
