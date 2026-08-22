/*
 * cattura — i pixel, letti dal nodo PipeWire che Mutter ha aperto.
 *
 * ⛔ IL MANDATO DI QUESTO FILE, IN UNA RIGA: **un fotogramma consegnato in
 *    memoria con il tipo di buffer DICHIARATO, non dedotto.**
 *
 * ⛔ RIPORTATO da `v1/remotix-c/src/cattura.c` (1060 righe) e NON ricopiato.
 *    Quel file portava dentro l'apparato RDP che in V2 non esiste — la strada
 *    che si gira a cattura viva perche' AVC420 vuole la GPU e RemoteFX la CPU,
 *    la misura negoziabile per KWin 6.8, il ridimensionamento della fase 6 — e
 *    qui non c'e' niente di tutto questo.  Sopravvivono le tre regole che erano
 *    il vero valore di quel file, e sono nei tre riquadri qui sotto.
 *
 * ===========================================================================
 * ⛔ 1. LO STRIDE SI LEGGE DAL CHUNK DEL BUFFER, MAI CALCOLATO
 *
 * Il produttore allinea le righe come gli conviene, e dedurre `larghezza × 4`
 * produce immagini oblique.  ⚠ `[M]` 12 agosto 2026: a 1920×1080 lo stride
 * misurato e' **7680**, cioe' esattamente `larghezza × 4` — ⛔ **e proprio per
 * questo la regola va scritta**: oggi coincide, e chi si abitua a calcolarlo non
 * se ne accorgera' il giorno in cui non coincide piu'.  Chi sta a valle legge
 * `stride` da qui, non lo rifa'.
 *
 * ⇒ Se il produttore consegnasse `stride == 0` questo modulo **scarta il
 *   fotogramma e lo conta**, invece di calcolarne uno: un fotogramma obliquo non
 *   da' nessun errore, e viene bene abbastanza da non farsi notare.
 *
 * ===========================================================================
 * ⛔ 2. IL TIPO DI BUFFER SI CHIEDE IN DUE POSTI, E SI DICHIARA
 *
 * Il DMA-BUF si chiede nel campo `modifier` del FORMATO (con
 * `MANDATORY | DONT_FIXATE`) **e** con il bit `SPA_DATA_DmaBuf` in
 * `SPA_PARAM_Buffers`.  Dichiarandone uno solo la negoziazione riesce lo stesso
 * e i buffer continuano ad arrivare in memoria: nessun errore, nessuna riga di
 * registro, e la copia zero semplicemente non c'e' (`[M]` 6 agosto 2026).
 *
 * ⛔ E QUEL CHE IL TIPO **NON** DICE — forma E1 di `REVIEWER.md` §2, gia' pagata
 *    DUE volte (`LEZIONI.md` §1.11):
 *
 *      «consegna MemFd  ⇒ Mutter rende in software»   ⛔ FALSO
 *      «ha aperto un render node ⇒ rende in GPU»      ⛔ FALSO
 *
 *    Il tipo che arriva e' la risposta a quel che **abbiamo chiesto noi**, non
 *    una scoperta sul compositore.  Per questo `CatturaConsegna` porta il tipo
 *    **chiesto** e il tipo **dichiarato** in due campi diversi, e accanto chi lo
 *    dice: sono tre fatti, non uno.
 *
 * ===========================================================================
 * ⛔ 3. LA CADENZA SI DICHIARA A ZERO, con un massimo a intervallo
 *
 * `framerate = 0/1` piu' `maxFramerate` significa «mandami un fotogramma quando
 * cambia qualcosa, non a ritmo fisso» — che e' il comportamento che serve a un
 * desktop remoto.  ⛔ Ne discende che **su un desktop fermo non arriva nulla**:
 * e' un comportamento voluto, non un guasto (`LEZIONI.md` §4 trappola 8), ed e'
 * la ragione per cui `cattura_prendi` distingue **lo zero dal fallimento** con
 * due valori d'uscita diversi (`CODER.md` §3.10).
 *
 * ===========================================================================
 * ⛔ IL DANNO E' UN'INFORMAZIONE SU QUANTO E' CAMBIATO — NON LA CONDIZIONE PER
 *    CUI IL BUFFER SI PUO' LEGGERE
 *
 * ⚠ In `v1/remotix-c/src/cattura.h` c'era scritto il contrario, e la misura lo ha
 *   smentito.  Diceva: *«in zero-copy Mutter ricicla i propri buffer e vi
 *   ridipinge dentro SOLO la parte cambiata; fuori da quelle regioni ci sono i
 *   pixel del fotogramma che aveva usato quel buffer prima»* (7 agosto 2026).
 *
 * `[M]` 12 agosto 2026, F2.2 — NIC-OS, Mutter 48.7 headless, strada MEMORIA,
 * monitor virtuale 1920×1080, scena «bandiera»: il danno e' **parziale su tutti
 * e 410 i fotogrammi**, il primo compreso, e le sette barre SMPTE si leggono
 * **intere** nel fotogramma di regime.  ⇒ **il buffer e' intero anche quando il
 * danno e' parziale.**
 *
 * `[R]` `STUDI.md` §gnome §8.1, Mutter riletto riga per riga, lo diceva gia': blit
 * dell'INTERO framebuffer, stack di clip svuotato deliberatamente, vista
 * virtuale come `CoglOffscreen` persistente.  Le due strade concordano.
 *
 * ⛔ E LA CONSEGUENZA CHE E' ANCORA VIVA NEL CODICE EREDITATO: in
 *    `v1/remotix-c/src/palco.c:598-628` la copia zero nasce **spenta su GNOME**
 *    con questa ragione, e questa ragione **e' morta**.  ⚠ Il che NON dice che
 *    la copia zero su GNOME funzioni: dice che il motivo per cui era spenta non
 *    c'e' piu', e che la decisione va ripresa **su una misura** invece che su
 *    quel commento.  Qui la strada la sceglie chi chiama (`CatturaStrada`), e la
 *    fase 2 chiede la memoria per una ragione sua e dichiarata: **vuole i pixel
 *    leggibili**.
 *
 * ⚠ A che cosa serve allora il danno: a sapere QUANTA parte e' stata ridipinta —
 *   cioe' quanto conviene ricodificare — e a distinguere «il produttore non
 *   dichiara il danno» da «il danno copriva tutto».  Si continua a chiederlo,
 *   perche' non chiederlo significa non riceverlo.
 *
 * ===========================================================================
 * ⚠ IL CICLO DI PIPEWIRE VIVE SU UN THREAD SUO (`pw_thread_loop`).  Le
 *   richiamate qui sotto vengono chiamate DA QUEL THREAD, che e' di tempo reale:
 *   chi le scrive non deve aspettare nulla al loro interno, e in particolare non
 *   deve chiamare `cattura_ferma` da dentro `CatturaFine`.
 *
 *   ⛔ E i pixel vivono SOLO per la durata della chiamata: appena si torna, il
 *      buffer torna a PipeWire.  Chi li vuole se li copia — o usa
 *      `cattura_prendi`, che la copia la fa lui.
 */
#ifndef REMOTIX_CATTURA_H
#define REMOTIX_CATTURA_H

#include <glib.h>
#include <stdint.h>

#include "cursore.h"

typedef struct Cattura Cattura;

/* ------------------------------------------------------------------ *
 *  Il tipo di buffer — si chiede e si dichiara
 * ------------------------------------------------------------------ */

typedef enum
{
	CATTURA_BUFFER_IGNOTO = 0,
	CATTURA_BUFFER_MEMFD,
	CATTURA_BUFFER_MEMPTR,
	CATTURA_BUFFER_MEMID,
	CATTURA_BUFFER_DMABUF
} CatturaBuffer;

/* La strada che si CHIEDE.  ⛔ Non e' la stessa cosa del tipo che arriva, e le
 * due stanno in due campi diversi apposta: se si chiede la scheda e arriva la
 * memoria, `cattura_avvia` FALLISCE dichiarandolo invece di ripiegare in
 * silenzio (`LEZIONI.md` §1.8, corollario). */
typedef enum
{
	CATTURA_STRADA_MEMORIA = 0, /* MemFd/MemPtr: i pixel si leggono            */
	CATTURA_STRADA_SCHEDA       /* DMA-BUF: i pixel NON sono qui, c'e' un fd   */
} CatturaStrada;

/*
 * Il colore che si CHIEDE.
 *
 * ⛔ E `CATTURA_COLORE_10BIT` non e' una speranza: e' **la domanda**, fatta al
 *    produttore invece che dedotta.  `STUDI.md` §gnome §8.3 `[R]`, Mutter 48.7 riletto
 *    riga per riga (`meta-screen-cast-stream-src.c`, `supported_formats[]`):
 *    **due sole voci, BGRx e BGRA**, tutt'e due a 8 bit per canale.  ⇒ Da questa
 *    sorgente dieci bit veri non escono.
 *
 *    Chiedere il formato a 10 bit e ricevere un rifiuto trasforma quella lettura
 *    in una **misura**, e il rifiuto va scritto invece che dedotto: e' l'unico
 *    modo di chiudere la `[?]` senza deduzione (`LEZIONI.md` §1.11).
 */
typedef enum
{
	CATTURA_COLORE_BGRX = 0,
	CATTURA_COLORE_BGRA,
	CATTURA_COLORE_10BIT
} CatturaColore;

/* Da dove viene un valore.  ⛔ «Non dichiarato» E' UNA RISPOSTA, e non un campo
 * da riempire con quel che ci aspettiamo: il silenzio scambiato per un valore e'
 * la forma E8. */
typedef enum
{
	CATTURA_FONTE_NON_DICHIARATA = 0, /* il produttore tace (SPA UNKNOWN)      */
	CATTURA_FONTE_PRODUTTORE,         /* SPA_PARAM_Format, chiesto a lui       */
	CATTURA_FONTE_FORMATO,            /* discende dal formato negoziato        */
	CATTURA_FONTE_MISURATA            /* [M] contata da noi sui pixel          */
} CatturaFonte;

/* L'esito della misura del range fatta sui pixel consegnati.  ⛔ Non c'e' un
 * valore «LIMITATO»: una scena che non arriva a 255 non prova un range
 * limitato — prova solo che quella scena non ci arriva.  Le due risposte oneste
 * sono «compatibile col pieno» e «non conclusivo». */
typedef enum
{
	CATTURA_RANGE_NON_MISURATO = 0,
	CATTURA_RANGE_COMPATIBILE_PIENO, /* i pixel toccano 0 e 255               */
	CATTURA_RANGE_NON_CONCLUSIVO     /* non li toccano: dipende dalla SCENA   */
} CatturaRangeMisurato;

/* ------------------------------------------------------------------ *
 *  ⛔ I QUATTRO FATTI CHE SI DICHIARANO A VALLE
 * ------------------------------------------------------------------ *
 *
 *   1. il TIPO DI BUFFER   chiesto e dichiarato, con chi lo dice
 *   2. i BIT PER CANALE    dal formato negoziato, mai inventati
 *   3. la GEOMETRIA        misura, stride LETTO, byte per fotogramma
 *   4. il COLORE           range · matrice · trasferimento · primari, come li
 *                          dichiara il produttore — «non dichiarato» compreso
 *
 * ⛔ Chi sta a valle legge questi campi.  Non li deduce, non li ricalcola, e in
 *    particolare non ricalcola lo stride.
 */
typedef struct
{
	gboolean noto; /* FALSE finche' il formato non e' stato negoziato */

	/* --- 1. il tipo di buffer ------------------------------------------- */
	CatturaStrada strada_chiesta;
	CatturaBuffer buffer_chiesto;
	CatturaBuffer buffer_dichiarato; /* CATTURA_BUFFER_IGNOTO fino al 1° fotogramma */
	uint32_t buffer_dichiarato_grezzo;
	guint buffer_distinti; /* quanti buffer diversi ricicla il produttore */

	/* --- 2. il formato e i bit ------------------------------------------ */
	uint32_t formato_grezzo;
	const char *formato; /* "BGRx", "BGRA", … — mai una parola inventata */
	int bit_per_canale;  /* 8; ⛔ 0 = formato ignoto, e 0 si scrive        */
	CatturaFonte fonte_bit;

	/* --- 3. la geometria ------------------------------------------------ */
	uint32_t larghezza, altezza;
	uint32_t stride;         /* ⛔ LETTO dal chunk. 0 = nessun fotogramma ancora */
	gboolean stride_letto;   /* FALSE ⇒ `stride` non e' un fatto, e' un vuoto   */
	guint64 byte;            /* stride × altezza                                */
	uint64_t modificatore;

	/* --- 4. il colore, come lo dichiara il produttore -------------------- */
	uint32_t range_grezzo, matrice_grezza, trasferimento_grezzo, primari_grezzi;
	CatturaFonte fonte_range, fonte_matrice;

	/* --- e la misura che facciamo NOI, perche' il produttore tace -------- */
	uint8_t minimo[3], massimo[3]; /* R, G, B */
	CatturaRangeMisurato range_misurato;
	gboolean nero;    /* ⛔ tutti i pixel a zero: il guasto peggiore di F2.2 */
	gboolean uniforme; /* tutti i pixel uguali fra loro (nero compreso)      */
	/* ⛔⛔ E QUESTO CAMPO E' LA RAGIONE PER CUI I TRE QUI SOPRA SI POSSONO
	 *     ANCORA LEGGERE — `LEZIONI.md` §1.9, «vuoto» e «proibito» hanno lo
	 *     stesso aspetto.
	 *
	 * Dal 22 agosto 2026 il giro sui pixel **non si fa su ogni fotogramma**: `[M]`
	 * costava **5,34 ms** dentro un tratto di **21,6**, cioe' il **25 %**, per
	 * riempire una riga di registro che si scrive **una volta sola**
	 * (`figlio.c`, il montaggio del palco).  ⇒ Adesso si fa sul PRIMO fotogramma
	 * e poi al piu' una volta ogni `MISURA_PIXEL_OGNI_MS`.
	 *
	 * ⛔ Su un fotogramma non misurato `nero` e `uniforme` valgono `FALSE` — e
	 *    `FALSE` qui vorrebbe dire **«non e' nero»**, che e' una BUGIA: vuol dire
	 *    «non ho guardato».  Chi legge quei tre campi **deve** guardare prima
	 *    questo, esattamente come `stride_letto` sta accanto a `stride`.
	 * ⚠ `range_misurato` sa gia' dirlo da se' (`CATTURA_RANGE_NON_MISURATO`);
	 *   `nero` e `uniforme` no, ed e' per loro che questo campo esiste. */
	gboolean pixel_misurati;
} CatturaConsegna;

/* ------------------------------------------------------------------ *
 *  Il fotogramma
 * ------------------------------------------------------------------ */

/* Una regione cambiata (`SPA_META_VideoDamage`).  ⛔ Informazione, non
 * condizione: vedi il riquadro in testa. */
typedef struct
{
	uint32_t x, y, larghezza, altezza;
} CatturaRegione;

typedef struct
{
	/* ⛔ `pixel` e' NULL sulla strada della scheda: li' non c'e' un puntatore,
	 *    c'e' un descrittore che vive sulla GPU.  Chi controlla «niente puntatore
	 *    ⇒ niente fotogramma» senza guardare prima il tipo scarta ogni DMA-BUF in
	 *    silenzio — misurato il 6 agosto 2026, ed e' costato un giro di prove. */
	const uint8_t *pixel;
	guint64 byte;
	int fd; /* -1 se non c'e' */
	uint32_t offset;
	uint32_t stride; /* ⛔ letto dal chunk */

	uint64_t seq;
	int64_t pts;
	gboolean seq_nota;

	const CatturaRegione *danno;
	guint quante_regioni;
	gboolean danno_dichiarato;
	gboolean danno_copre_tutto;

	guint64 indice; /* quale fotogramma era, contato dal primo arrivato */
	const CatturaConsegna *consegna;
} CatturaFotogrammaInfo;

typedef void (*CatturaFotogramma)(const CatturaFotogrammaInfo *fotogramma, gpointer dati);

/* Il flusso si e' staccato: o la sessione grafica e' finita, o Mutter l'ha
 * fermato per conto suo. */
typedef void (*CatturaFine)(gpointer dati);

/* ------------------------------------------------------------------ *
 *  Il fotogramma FERMO — la consegna della fase 2
 * ------------------------------------------------------------------ */

/*
 * Una copia nostra del fotogramma, che vive finche' non la si libera.
 *
 * ⭐ E' il prodotto di F2.2: *un'immagine ferma*, presa dalla sessione e messa
 *    in memoria, con accanto tutto quel che serve a giudicarla senza dedurre
 *    niente.
 */
typedef struct
{
	uint8_t *pixel;
	guint64 byte;
	uint32_t stride, larghezza, altezza;
	uint64_t seq;
	int64_t pts;
	gboolean seq_nota;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ LA COPIA ZERO — il fotogramma che NON e' stato copiato
	 * ------------------------------------------------------------------ *
	 *
	 * ⛔ Sulla strada della SCHEDA `pixel` resta **NULL** e questi campi sono
	 *    l'unico modo di arrivare all'immagine: non e' un puntatore, e' un
	 *    descrittore che vive sulla GPU.  Chi legge deve guardare
	 *    `sulla_scheda` PRIMA di `pixel`, o scartera' ogni fotogramma della
	 *    scheda in silenzio (`[M]` 6 agosto 2026, ed e' costato un giro di
	 *    prove).
	 *
	 * ⛔⛔ E IL BUFFER E' **TRATTENUTO** FINCHE' NON SI CHIAMA
	 *      `cattura_fermo_libera()` — vedi il riquadro della RITENUTA in
	 *      `cattura.c`.  Chi tiene questo `CatturaFermo` piu' a lungo del
	 *      necessario toglie un buffer al produttore; chi lo libera prima di
	 *      aver finito di leggere si fa riscrivere l'immagine sotto gli occhi
	 *      (`LEZIONI.md` §8: le due schermate che si alternavano non erano un
	 *      problema di *acquire*, erano di *release*).
	 */
	gboolean sulla_scheda;
	int fd;              /* ⛔ NON e' nostro: lo possiede PipeWire, non si chiude */
	uint32_t offset;
	uint32_t formato_drm; /* `DRM_FORMAT_XRGB8888` … — quel che VA-API vuole  */
	uint64_t modificatore;
	/* ⛔ La GENERAZIONE dei buffer del produttore: cambia ogni volta che
	 *    PipeWire li rialloca (una rinegoziazione, un risveglio).  ⚠ Serve a
	 *    chi mette in cache l'importazione di un `fd`: **i numeri di
	 *    descrittore si riciclano**, e una cache che guardasse il solo `fd`
	 *    darebbe a VA-API una superficie che punta a un buffer liberato — cioe'
	 *    un'immagine di prima, o peggio.  Due misure sotto la stessa etichetta,
	 *    nella forma che non da' nessun errore. */
	uint64_t generazione;
	/* ⛔ Opachi: il `pw_buffer` trattenuto e chi lo restituira'.  Non si
	 *    leggono da fuori — esistono perche' `cattura_fermo_libera()` sappia a
	 *    chi rendere il buffer senza che il chiamante debba tenersi la
	 *    `Cattura` accanto al fotogramma. */
	void *ritenuta;
	void *padrone;
	gboolean danno_dichiarato, danno_copre_tutto;
	guint64 indice;          /* quale fotogramma era fra gli arrivati */
	CatturaConsegna consegna; /* i quattro fatti, congelati con lui   */

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ I TRATTI DELLA PRESA — la strumentazione della fase 8
	 * ------------------------------------------------------------------ *
	 *
	 * ⛔ IL FATTO CHE LI FA NASCERE: `[M]` fase 4, il tratto `cattura → primo
	 *    byte` vale **30,37 ms** e i tre tempi che il codificatore gia'
	 *    dichiarava — conversione 5,6 · caricamento 2,9 · codifica 5,3 — ne
	 *    spiegano **13,8**.  ⇒ **~16 ms non avevano un proprietario**, e un
	 *    margine senza nome non si cura: si strumenta prima.
	 *
	 * ⛔ E QUESTI QUATTRO SONO IL PEZZO DI TRATTO CHE STA **PRIMA** DEL
	 *    CODIFICATORE, cioe' l'unico che nessuno guardava.  Sono microsecondi, e
	 *    sono quattro perche' rispondono a quattro domande diverse:
	 *
	 *      `us_arrivo`      l'istante (CLOCK_MONOTONIC) in cui il fotogramma e'
	 *                       stato messo nel posto.  ⛔ Non e' un costo: e' il
	 *                       riferimento da cui gli altri si sottraggono, e
	 *                       accanto al `pts` di Mutter dice quanto ci mette il
	 *                       produttore ad arrivare fino a noi;
	 *      `us_copia`       la `memcpy` dentro la richiamata di tempo reale;
	 *      `us_allocazione` la `g_malloc` del posto — ⛔ **0 quando il buffer si
	 *                       e' riusato**, ed e' precisamente il numero che dice
	 *                       se il riuso di `posto_capienza` sta funzionando o se
	 *                       si rialloca a ogni giro;
	 *      `us_nel_posto`   ⭐ **quanto il fotogramma e' rimasto FERMO nel posto**
	 *                       prima che qualcuno lo prendesse.  ⛔ E' tempo in cui
	 *                       nessuno lavora e il fotogramma invecchia: non e'
	 *                       lavoro da ottimizzare, e' **attesa**, ed e' l'unica
	 *                       voce del tratto che cala se il ciclo si accorcia;
	 *      `us_misura`      il giro di `misura_i_pixel()` — ⛔ lavoro
	 *                       DIAGNOSTICO, non di prodotto: legge ogni pixel del
	 *                       fotogramma sul thread di chi chiama.
	 *
	 * ⚠ `us_nel_posto` e `us_misura` si riempiono in `cattura_prendi()`; gli
	 *   altri due nella richiamata di tempo reale.  ⛔ Un fotogramma consegnato
	 *   a `su_fotogramma` (la strada senza copia) NON li porta: li' non c'e'
	 *   nessun posto e nessuna copia. */
	uint64_t us_arrivo;
	uint64_t us_copia;
	uint64_t us_allocazione;
	uint64_t us_nel_posto;
	uint64_t us_misura;
} CatturaFermo;

/*
 * ⛔ ZERO E FALLIMENTO SONO DUE COSE DIVERSE, e qui sono quattro.
 *    (`CODER.md` §3.10, `REVIEWER.md` §1 punto 4.)
 */
typedef enum
{
	CATTURA_PRESA_FATTA = 0,
	/* ⭐ Zero LEGITTIMO: il flusso e' stato attivo per tutta l'attesa e non e'
	 *    arrivato niente.  Su Mutter e' il desktop fermo, ed e' un risultato. */
	CATTURA_PRESA_ZERO,
	/* ⛔ Il flusso non e' mai stato attivo, o e' caduto: non c'e' nessun numero
	 *    da leggere, e nessuno zero da scrivere in una tabella. */
	CATTURA_PRESA_GUASTO,
	/* ⛔ Strada della scheda: il tipo di buffer e' DICHIARATO, ma i pixel non
	 *    sono qui.  Non e' un guasto e non e' uno zero.
	 *
	 * ⭐⭐ E DAL 22 AGOSTO 2026 QUESTO E' **UN FOTOGRAMMA CONSEGNATO**, non un
	 *     nulla di fatto: dentro `CatturaFermo` ci sono `fd`, `offset`,
	 *     `stride`, `modificatore` e `formato_drm`, e il `pw_buffer` e'
	 *     TRATTENUTO fino a `cattura_fermo_libera()`.  ⇒ Chi chiama lo tratta
	 *     come `FATTA` **cambiando strada di lettura**, non lo butta.
	 * ⚠ Ed e' rimasto un esito a parte invece di diventare `FATTA` proprio
	 *   perche' la strada di lettura E' diversa: un chiamante che non sa della
	 *   scheda deve inciampare qui, non leggere un `pixel` NULL. */
	CATTURA_PRESA_PIXEL_ALTROVE
} CatturaPresa;

/* ------------------------------------------------------------------ *
 *  Le chiamate
 * ------------------------------------------------------------------ */

/*
 * Avvia la lettura dal nodo indicato, chiedendo misura, colore e strada.
 *
 * La misura si dichiara perche' si sta riprendendo un MONITOR VIRTUALE: non
 * esiste uno schermo da cui dedurla, ed e' il consumatore a dire quanto grande
 * lo vuole.  ⛔ E si dichiara come rettangolo FISSO, non come intervallo: un
 * intervallo aperto lascerebbe scegliere a Mutter, che sceglie 1280×720.
 *
 * `su_fotogramma` puo' essere NULL: allora i fotogrammi si contano soltanto, e
 * si prendono con `cattura_prendi`.
 *
 * ⛔ Fallisce — dichiarandolo — se il compositore rifiuta il formato chiesto.
 *    E' l'unico punto in cui un rifiuto si vede subito invece di diventare uno
 *    schermo nero molto piu' tardi.
 */
Cattura *cattura_avvia(uint32_t nodo, uint32_t larghezza, uint32_t altezza,
                       uint32_t fotogrammi_al_secondo, CatturaStrada strada, CatturaColore colore,
                       CatturaFotogramma su_fotogramma, CatturaFine su_fine, gpointer dati,
                       GError **sbaglio);

/* ------------------------------------------------------------------ *
 *  ⭐⭐ IL CAMBIO DI MISURA A CALDO — `DECISIONI.md` §5.0-sexies
 * ------------------------------------------------------------------ */

/*
 * L'esito della RICHIESTA, che ⛔ non e' l'esito del cambio.
 *
 * ⛔⭐ «LA VERITA' LA DICE IL FOTOGRAMMA, NON L'ESITO DELLA RICHIESTA» — la
 *     regola di forma rubata a neatvnc, `DECISIONI.md` §5.0-sexies.  `[M]` 14
 *     agosto 2026: chiedere a labwc la misura che l'output HA GIA' risponde
 *     «riuscito» e non manda nessun evento; un serial vecchio risponde
 *     «annullato» e non fa niente.  ⛔ `wayvnc` tratta *riuscito*, *fallito* e
 *     *annullato* nello stesso ramo — da non copiare.
 *
 * ⇒ Qui si dice soltanto se la RICHIESTA e' partita.  Che il compositore abbia
 *   obbedito lo dira' il formato negoziato (`cattura_consegna`) e, prima
 *   ancora, il primo fotogramma alla misura nuova.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ E «PARTITA» INCLUDE «E PUO' AVER UCCISO IL FLUSSO» — `[M]` 22 agosto
 *      2026, banco `banchi/06-b5-esiti-cattura.c` caso 2, PipeWire 1.4.2
 *
 * Chiedendo una misura che il produttore non regge, `cattura_ridimensiona()`
 * torna `CHIESTA` e **due millisecondi dopo** il flusso va in
 * `paused → error — no more input formats`: la trattativa fallita non lascia il
 * flusso «fermo alla misura vecchia», lo **uccide**.
 *
 * ⭐ E NON SERVE UN ESITO NUOVO PER SAPERLO, perche' la strada c'e' gia' ed e'
 *    quella che il chiamante percorre comunque: `cattura_prendi()` guarda lo
 *    stato **prima** di aspettare, quindi torna `CATTURA_PRESA_GUASTO` **senza
 *    spendere l'attesa**, e il `GError` nomina lo stato e il guasto del
 *    produttore.  `[M]` col ciclo del figlio (`MOVIMENTO_ATTESA_S 0.008`) il
 *    guasto arriva a **8,1 ms**, in **un** giro solo e con **zero** ZERO in
 *    mezzo — cioe' un giro del ciclo, non un timeout.
 *
 * ⛔ Un esito «MORTO» restituito da qui sarebbe invece **verde per
 *    costruzione**: la morte arriva 2 ms DOPO il ritorno, quindi leggerla
 *    subito vorrebbe dire leggerla prima che accada, e la meta' delle volte
 *    direbbe «viva».
 *
 * ⚠ `[?]` E questa scena, sul prodotto vero, non e' misurata: `[M]`
 *   (§5.0-sexies) Mutter ha concesso 30 richieste su 30 da 1x1 a 7680x4320, e
 *   `rcp_misura_ammessa()` taglia proprio a 7680x4320.  ⇒ Qui si dichiara che
 *   cosa succede SE capita, non quanto spesso capiti.
 */
typedef enum
{
	CATTURA_RITELA_CHIESTA = 0, /* la richiesta e' partita: aspetta il fotogramma */
	/* ⭐ La misura chiesta e' gia' quella in vigore: NON si rinegozia.
	 * ⛔ La guardia e' obbligatoria — `STUDI.md` §kde §8.2-bis: senza,
	 *    «la rinegoziazione si morde la coda». */
	CATTURA_RITELA_GIA_COSI,
	CATTURA_RITELA_GUASTO /* niente flusso, flusso morto, o misura vuota */
} CatturaRitela;

/*
 * Chiede al produttore una misura NUOVA sul flusso GIA' APERTO.
 *
 * ⛔ NON rifa' la sessione e non tocca il monitor virtuale: rifa' la proposta di
 *    formato e chiama `pw_stream_update_params()`, che e' il modo in cui
 *    gnome-remote-desktop ridimensiona (`F4-IN-2`) ed e' quel che il banco
 *    `banchi/04-in8-misura.c` ha misurato il 14 agosto 2026:
 *
 *      Mutter  `[M]` primo fotogramma nuovo a **41,6 ms**, nessun nero, sessione
 *              ed EIS intatti; **20 ridimensionamenti in 2 s, 20 esatti**
 *      labwc   `[M]` **5,1 ms**, **0 fotogrammi persi su 25**
 *      KWin    ⛔ solo su `master` — vale il ripiego di `DECISIONI.md` §5.0-bis
 *
 * ⭐⭐ E C'E' UN SECONDO EFFETTO, MISURATO, CHE NON SI VEDE DAL NOME: **riavviare
 *     il flusso fa arrivare un fotogramma**.  `[M]` 14 agosto 2026, registro
 *     delle 21:32:55: fra il login e il primo fotogramma passavano **4,4
 *     secondi** di richieste di chiave ogni 200 ms e **659 «attese a vuoto»**,
 *     perche' su Wayland il compositore consegna solo quando la scena cambia e
 *     un desktop appena acceso e' fermo.  ⛔ Xpra lo risolve con
 *     `buffer_refresh` («ridipingi adesso») e a noi non serve: qui la leva e'
 *     questa, e la cura del ritardo e' un effetto collaterale della cura delle
 *     bande.
 *
 * ⚠ NON aspetta: torna subito.  Aspettare qui fermerebbe il ciclo del figlio,
 *   che e' l'unico che ha (`CODER.md` §4.4).
 *
 * ⛔ E LA MISURA AMMESSA NON SI CONTROLLA QUI: la regola («200..8192, ed
 *    entrambe PARI») vive in `rcp_misura_ammessa()` e la applica chi legge
 *    `ADATTA_TELA` dal filo — vedi il riquadro in fondo a questo file.  Qui si
 *    rifiuta solo lo ZERO, che e' un fatto diverso: una misura vuota non e'
 *    «fuori dai limiti», e' una richiesta senza contenuto.
 */
CatturaRitela cattura_ridimensiona(Cattura *cattura, uint32_t larghezza, uint32_t altezza);

/*
 * ⭐⭐ «CONSEGNAMI UN FOTOGRAMMA ADESSO» — e su Wayland non si puo' chiedere.
 *
 * ⛔ IL FATTO, misurato: un compositore Wayland consegna un fotogramma **solo
 *    quando qualcosa cambia** (`cattura.h`, regola 3), e un desktop appena
 *    acceso e' fermo.  `[M]` 14 agosto 2026, registro del server: fra il login e
 *    il primo fotogramma sono passati **4,4 secondi**, con una richiesta di
 *    chiave ogni 200 ms e **659 «attese a vuoto»** — e in quei 4,4 secondi
 *    l'utente guarda una pagina bianca.
 *
 * ⛔ Xpra lo risolve con `buffer_refresh` («ridipingi adesso») e a noi non
 *    serve: su Wayland non si puo' ordinare a un compositore di ridipingere.
 * ⭐ Ma la leva c'e' ed e' la stessa del ridimensionamento: **riavviare il flusso
 *    fa arrivare un buffer**, ed e' precisamente quel che
 *    `pw_stream_update_params()` E'.  Qui si rifanno gli stessi parametri, con
 *    la stessa misura: non cambia niente, e il fotogramma arriva.
 *
 * ⚠ `[?]` E la marca e' questa, non `[M]`: che la rinegoziazione consegni un
 *   buffer **su una scena ferma** e' dedotto dal meccanismo (il flusso riparte,
 *   e ripartire vuol dire riallocare i buffer e ridipingere il primo), non
 *   misurato.  La prova e' una sessione in cui il tempo fra il login e il primo
 *   fotogramma scende sotto il secondo, e va fatta sulla macchina di prova.
 *
 * ⛔ Chi chiama deve METTERCI UN FONDO: a chiamarla a ogni giro si
 *    rinegozierebbe sessanta volte al secondo — e ogni rinegoziazione costa il
 *    fotogramma che si sta cercando di ottenere.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔⛔ E IL PREZZO NASCOSTO, che il nome non lascia sospettare — `[M]` 21
 *       agosto 2026, banco `banchi/06-b33-risveglio.*`
 *
 * **QUESTA CHIAMATA DISTRUGGE E RICREA I DISPOSITIVI DI INPUT.**  Non e' un
 * effetto collaterale piccolo: e' la **seconda porta** del *clic che muore*
 * (`fasi/06-la-tela-e-la-vista.md` §4.6 e §7.1).
 *
 * `[M]` Tre risvegli su scena ferma, **zero** `ADATTA_TELA`: tre ricambi del
 * puntatore (delta 1, 1, 1, letto da `input_conto()`).
 *
 * `[R]` La catena, tutta dentro Mutter 48.7:
 *   `pw_stream_update_params()` → il produttore rinegozia →
 *   `meta_screen_cast_virtual_stream_src_enable()`
 *   (`meta-screen-cast-virtual-stream-src.c:283`) chiama
 *   `meta_eis_viewport_notify_changed()` → `viewports-changed` →
 *   `update_viewports()` → `remove_viewport_devices()`, che ⛔ **non passa da
 *   `drop_device()`** e quindi non rilascia niente.
 *
 * ⇒ ⛔⛔ **Se un pulsante e' premuto quando questa funzione parte, il desktop
 *   non prende piu' un clic per tutta la sessione** — `[M]`, e si guarisce solo
 *   facendo cadere il canale EIS.  ⚠ Il momento in cui `figlio.c:6365` la
 *   chiama e' *«la scena e' ferma e una chiave e' dovuta»*, cioe' **esattamente
 *   il momento in cui l'utente puo' tenere giu' il mouse su un desktop fermo**.
 *
 * ⇒ Chi chiama deve **guardare se c'e' qualcosa di premuto** prima di
 *   risvegliare.  ⛔ La cura di `figlio.c:3964` — rilasciare prima di
 *   `cattura_ridimensiona()` — **non copre questa strada**.
 *
 * `FALSE` = non si e' potuto chiedere (niente flusso, o flusso non attivo).
 */
gboolean cattura_risveglia(Cattura *cattura);

/* La misura CHIESTA al produttore adesso — ⛔ non quella concessa: quella sta in
 * `CatturaConsegna.larghezza/altezza` e vale solo dopo la negoziazione.  ⚠ Le due
 * si confrontano, e chi le confonde riscrive il difetto che la guardia «chiesto
 * contro concesso» esiste per vedere.
 *
 * ⛔⛔ E QUESTI DUE SONO **TUTTO** QUEL CHE SI ESPORTA SULLA DIVERGENZA: non
 *     c'e' — e non si aggiunge — un `cattura_divergente()`.  La ragione e'
 *     misurata e sta accanto al campo `misura_divergente` in `cattura.c`: `[M]`
 *     (banco `06-b5` caso 4) la sola scena che lo accende sono **due
 *     ridimensionamenti incatenati**, dove il valore e' un **falso allarme** che
 *     si spegne da se'; e `[M]` (caso 6) la divergenza vera si ricostruisce da
 *     questi due accessori, che distinguono anche il «non ancora negoziato» —
 *     cosa che un `gboolean` non saprebbe fare (`CODER.md` §3.10). */
void cattura_misura_chiesta(Cattura *cattura, uint32_t *larghezza, uint32_t *altezza);

/* La misura NEGOZIATA, cioe' quella che i pixel hanno davvero.  ⛔ `FALSE` = il
 * formato non e' stato ancora negoziato, che NON e' «e' 0x0» (`CODER.md` §3.10).
 *
 * ⚠ Serve a rispondere «la tela che chiedi ce l'ho gia'» senza aspettare un
 *   fotogramma che non arriverebbe: e' l'unico caso in cui la richiesta si puo'
 *   chiudere senza vedere i pixel, perche' i pixel di quella misura chi guarda
 *   li ha gia' davanti. */
gboolean cattura_misura_negoziata(Cattura *cattura, uint32_t *larghezza, uint32_t *altezza);

/*
 * Aspetta il PROSSIMO fotogramma e ne consegna una copia.
 *
 * ⛔ La copia si fa dentro la richiamata di tempo reale — non c'e' altro modo,
 *    i pixel vivono solo li' — e la MISURA sui pixel (range, nero, uniforme) si
 *    fa qui, sul thread di chi chiama: rallentare il ciclo di PipeWire
 *    falserebbe la cosa che si sta guardando.
 *
 * ⚠ I fotogrammi che arrivano quando nessuno sta aspettando si contano e basta:
 *   non si accumulano copie da 8 MB che nessuno ha chiesto.
 */
CatturaPresa cattura_prendi(Cattura *cattura, double attesa_s, CatturaFermo *fuori,
                            GError **sbaglio);

/*
 * Rende il fotogramma.
 *
 * ⛔⛔ E SULLA STRADA DELLA SCHEDA QUESTA CHIAMATA E' **IL RILASCIO**, cioe' la
 *      cura di `LEZIONI.md` §8: finche' non si chiama, il `pw_buffer` e'
 *      nostro e il produttore non ci puo' ridipingere dentro.  ⇒ Si chiama
 *      **dopo** che l'ultimo lettore ha finito — dopo la conversione sulla GPU,
 *      non dopo averla ordinata — e **non prima**.
 * ⚠ Chiamarla due volte e' innocuo (il fermo si azzera); non chiamarla affatto
 *   toglie un buffer al produttore per sempre.
 */
void cattura_fermo_libera(CatturaFermo *fermo);

/* I quattro fatti, quando sono noti.  FALSE ⇒ il formato non e' stato ancora
 * negoziato, e non c'e' niente da dichiarare (non «e' tutto a zero»). */
gboolean cattura_consegna(Cattura *cattura, CatturaConsegna *fuori);

/* I conteggi del giro.  Servono a chi scrive un manifesto o una riga di
 * registro, e sono separati dai fatti apposta: un conteggio non e' una
 * dichiarazione sul formato. */
typedef struct
{
	guint64 arrivati;
	guint64 danno_pieno, danno_parziale, danno_assente;
	guint64 senza_intestazione;
	guint64 solo_cursore;   /* buffer marcati CORRUPTED: pixel stantii */
	guint64 stride_zero;    /* ⛔ scartati invece che calcolati        */
	guint64 senza_pixel;    /* mappatura assente o chunk vuoto         */
	/* ⛔⭐ La geometria dichiarata dal FORMATO non sta dentro i byte del CHUNK:
	 *     scartati, perche' chi li consuma leggerebbe oltre la copia.  ⚠ E' la
	 *     finestra fra una rinegoziazione e i buffer nuovi, e prima di
	 *     `cattura_ridimensiona()` non poteva esistere. */
	guint64 geometria_incoerente;
	/* ⭐ Il canale del cursore.  ⛔ I due primi sono DUE e non uno, ed e' la
	 *    stessa regola dello zero e del fallimento: «il metadato non c'era» e
	 *    «il metadato c'era» sono i due fatti che distinguono un puntatore
	 *    assente da un canale senza sorgente (`STUDI.md` §gnome §1.1 punto 6). */
	guint64 cursore_assente;
	guint64 cursore_metadati;
	guint64 cursore_malformati;
	guint buffer_distinti;
	CatturaBuffer tipi_visti[4]; /* ⛔ TUTTI i tipi visti, non solo l'ultimo */
	guint quanti_tipi;
} CatturaConteggi;

void cattura_conteggi(Cattura *cattura, CatturaConteggi *fuori);

/*
 * ⭐⭐ LA CUCITURA DEL CURSORE — chi vuole la FORMA del puntatore si registra qui.
 *
 * ⛔ Questa e' l'UNICA riga che il canale del cursore aggiunge all'interfaccia
 *    della cattura, e ci sta per una ragione precisa: `cattura.c` legge il
 *    metadato grezzo di PipeWire ma **non conosce il filo**, e `cursore.h` vuole
 *    il destinatario al momento dell'apertura — che avviene dentro
 *    `cattura_avvia`, cioe' prima che chiunque possa registrarsi.
 *
 * ⚠ `quando_cambia` viene chiamata DAL THREAD DI TEMPO REALE di PipeWire, e vale
 *   il riquadro in cima a questo file: non si aspetta niente li' dentro, e
 *   l'immagine vive solo per la durata della chiamata (`cursore.h`).
 *
 * ⚠ Si puo' chiamare in qualsiasi momento, anche a cattura viva: le forme che
 *   arrivano prima della registrazione si contano e non si mandano — ⛔ che NON
 *   e' «non sono arrivate».  Chi si registra dopo il primo movimento del
 *   puntatore riceve comunque la forma successiva.
 *
 * ⛔ E il taglio a 256, il «nascosto» e il «non e' cambiato» NON sono qui: sono
 *    in `cursore.c`, che e' il posto che `cursore.h` gli assegna.
 */
void cattura_cursore(Cattura *cattura, CursoreArrivata quando_cambia, void *chi);

/* Il flusso e' attivo ADESSO?  ⛔ «E' STATO attivo» non e' «lo e' ancora»: la
 * morte a meta' misura ha gia' prodotto una riga di tabella con dentro cinque
 * secondi sotto l'etichetta di venti. */
gboolean cattura_attiva(Cattura *cattura);

/* Il guasto dichiarato dal produttore, o NULL. */
const char *cattura_guasto(Cattura *cattura);

void cattura_ferma(Cattura *cattura);

/* --- la misura ammessa: NON sta qui, e la ragione va detta ------------ *
 *
 * ⛔ La regola («200..8192, e larghezza e altezza PARI») vive in `rcp.h`, come
 *    `rcp_misura_ammessa()`, e NON qui — anche se il motivo per cui il tetto
 *    esiste e' tutto di questo livello: `[M]` 14 agosto 2026, oltre **16384**
 *    per lato `gnome-shell` muore, e su labwc `32768x32768` uccide il
 *    compositore **con zero righe di registro**.
 *
 * ⚠ Sta di la' perche' a doverla applicare e' chi legge `ADATTA_TELA` dal filo,
 *   e `rcp.h` e' **volutamente autosufficiente** — include solo `stdbool`,
 *   `stddef` e `stdint` — perche' la sua copia gemella compili dentro
 *   `bsslserver` senza il resto dell'albero.  ⇒ Mettere la regola qui
 *   costringerebbe `rcp.c` a includere questo file, cioe' a rompere quella
 *   proprieta'.
 * ⛔ E averla in DUE posti sarebbe peggio di tutt'e due: il giorno in cui una
 *   cambia, il server accetta una misura che il compositore non regge, e la
 *   sessione di chi ci ospita muore in silenzio. */

/* --- i nomi, perche' chi scrive un manifesto non li reinventi --------- */
const char *cattura_buffer_nome(CatturaBuffer buffer);
const char *cattura_colore_nome(uint32_t formato_grezzo);
const char *cattura_fonte_nome(CatturaFonte fonte);
const char *cattura_range_nome(uint32_t grezzo);
const char *cattura_matrice_nome(uint32_t grezzo);
const char *cattura_trasferimento_nome(uint32_t grezzo);
const char *cattura_primari_nome(uint32_t grezzo);
const char *cattura_range_misurato_nome(CatturaRangeMisurato misurato);

#endif
