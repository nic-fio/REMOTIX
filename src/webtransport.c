/*
 * webtransport.c — vedi webtransport.h.
 *
 * ⭐ Portato da `banchi/01-b2-ngtcp2-wt-innesta.py`, che lo teneva come `git
 *    diff` sull'albero di ngtcp2.  Le decisioni e le cure che i commenti
 *    dell'innesto documentavano sono qui dentro **con la loro ragione**: sono
 *    difetti gia' pagati, e riscriverli senza la ragione significa ripagarli.
 */
#include "webtransport.h"
/* ⭐ §5-bis.7: la domanda «questa disposizione esiste?» la sa `tastiera.c`. */
#include "tastiera.h"

/* ⛔ Solo per i `FIGLI_INPUT_*`: i numeri delle azioni stanno in un posto solo
 *    (`figlio.h`), o fra due settimane saranno tre posti con tre valori. */
#include "figlio.h"

#include "aiutante.h"
#include "audio.h"
#include "rcp.h"
#include "registro.h"

#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool rcp_autentica(const char *utente, const char *parola);

/* ------------------------------------------------------------------------ */
/* Le due cose che il C non porta in dote: un vettore di byte e un elenco.    */

typedef struct {
	uint8_t *d;
	size_t n, cap;
} bytes;

static bool bytes_aggiungi(bytes *b, const uint8_t *d, size_t n)
{
	if (n == 0)
		return true;
	if (b->n + n > b->cap) {
		size_t c = b->cap ? b->cap * 2 : 64;
		uint8_t *nuovo;
		while (c < b->n + n)
			c *= 2;
		nuovo = realloc(b->d, c);
		if (!nuovo)
			return false;
		b->d = nuovo;
		b->cap = c;
	}
	memcpy(b->d + b->n, d, n);
	b->n += n;
	return true;
}

static void bytes_togli_testa(bytes *b, size_t n)
{
	if (n >= b->n) {
		b->n = 0;
		return;
	}
	memmove(b->d, b->d + n, b->n - n);
	b->n -= n;
}

static void bytes_libera(bytes *b)
{
	free(b->d);
	b->d = NULL;
	b->n = b->cap = 0;
}

/* ------------------------------------------------------------------------ */

/* Come si classifica uno stream del client. */
enum genere {
	G_INCERTO, /* non si sa ancora che cosa sia: mancano i primi byte */
	G_WT,      /* e' uno stream WebTransport bidirezionale */
	G_NONWT,   /* non lo e': e' di nghttp3 */
	G_UNI_OK,  /* unidirezionale WebTransport, canale lecito ma non servito */
	G_UNI_KO,  /* unidirezionale WebTransport, violazione gia' giudicata */
	G_UNI_INPUT, /* ⭐ il canale di INPUT (0x01), servito dalla fase 4: i suoi
	              *    byte vanno a `rcp_ricevi_input()`.  ⛔ Sta separato da
	              *    `G_UNI_OK` apposta — dentro quel giudizio i byte si
	              *    contano nel credito e SI SCARTANO, ed e' esattamente
	              *    quel che l'input faceva fino al 14 agosto 2026. */
	G_UNI_APPUNTI, /* ⭐ il canale APPUNTI (0x02), servito dalla fase 7: i suoi
	                *    byte vanno a `rcp_ricevi_appunti()`.  ⛔ Sta separato da
	                *    `G_UNI_INPUT` per una ragione che non e' di ordine: qui
	                *    gli stream sono **uno per trasferimento** (§2.5), quindi
	                *    ce n'e' piu' d'uno vivo insieme e la FINE di ciascuno
	                *    e' un fatto — mentre lo stream di input e' uno solo e
	                *    resta aperto. */
};

typedef struct {
	int64_t id;
	enum genere genere;
	bytes pref;
} stream_giudizio;

typedef struct {
	int64_t id;
	bytes dati;
	size_t off;
	bool fin;
	/* ⛔⭐ FASE 3 — «MORTO» INVECE DI «TOLTO DALLA TESTA».
	 *
	 *     Fino alla fase 2 da questa coda si toglieva **solo la testa**, e
	 *     bastava: si spediva un fotogramma solo per sessione.  ⛔ Con uno
	 *     stream per fotogramma la testa non e' piu' l'unico elemento che puo'
	 *     finire — si sceglie un elemento **in mezzo** quando quelli davanti
	 *     appartengono a uno stream bloccato — e togliere dal mezzo un array
	 *     vorrebbe dire spostare tutto il resto a ogni fotogramma.
	 *
	 *     ⇒ Chi finisce si marca morto; `testa` scorre sui morti in testa. */
	bool morto;
	/* ⛔⛔⭐ FASE 9 — «CONSEGNATO» NON E' «CONFERMATO», e la differenza fra le
	 *      due parole e' il crollo del 23 agosto 2026 (`fasi/09-la-qualita-e-la-degradazione.md` §4).
	 *
	 *      `ngtcp2_conn_writev_stream()` **non copia i byte**: si tiene il
	 *      NOSTRO puntatore nell'elenco dei pacchetti in volo, e quando un
	 *      pacchetto viene dichiarato perduto lo **rilegge** per
	 *      ritrasmettere.  Il contratto lo dice in una riga
	 *      (`ngtcp2.h`, `ngtcp2_conn_writev_stream`):
	 *
	 *        «The caller must keep the portion of data covered by |*pdatalen|
	 *         bytes **in tact** until `acked_stream_data_offset` indicates that
	 *         they are acknowledged by a remote endpoint **or the stream is
	 *         closed**.»
	 *
	 * ⛔ Qui si liberava alla SERIALIZZAZIONE — `off >= dati.n` ⇒ `free()` — che
	 *    e' esattamente l'istante che il contratto vieta.  `[M]` 23 agosto 2026,
	 *    08:28:09: `SEGV`, `error 4`, dentro `__memmove_avx_unaligned_erms`,
	 *    sorgente `0x7f148e056fc2` — un fotogramma da 525 298 byte, il primo
	 *    blocco del giro abbastanza grosso da essere servito con `mmap`, quindi
	 *    il primo il cui `free()` abbia davvero **smappato** la regione.
	 *
	 * ⚠ E gli altri 45 004 fotogrammi dello stesso giro avevano lo STESSO
	 *   difetto senza far rumore: sotto i 128 KiB glibc serve dal mucchio, la
	 *   rilettura riesce e ngtcp2 ritrasmette **byte di spazzatura al posto dei
	 *   pixel**, in silenzio e senza un errore.  ⛔ Il crollo era il sintomo
	 *   raro; la corruzione muta era il difetto vero.
	 *
	 * ⭐ Da cui i due stati, che prima erano uno solo:
	 *
	 *      `consegnato` — tutti i byte sono dentro a ngtcp2.  Non si sceglie
	 *                     piu' per la scrittura (`coda_scegli()`), non conta
	 *                     piu' come «da spedire» (`coda_vuota()`,
	 *                     `byte_in_coda`), ⛔ **ma i byte restano nostri e
	 *                     restano allocati**;
	 *      `morto`      — i byte sono liberati.  Ci si arriva SOLO da un
	 *                     riscontro che li copre (`coda_conferma()`), dalla
	 *                     chiusura dello stream (`wt_stream_chiuso()`) o dal suo
	 *                     azzeramento (`coda_butta_stream()`, sempre accanto a
	 *                     un `RESET_STREAM`).  Sono le due condizioni del
	 *                     contratto, e non ce n'e' una terza.
	 *
	 * ⚠ `confermati` conta i byte di QUESTO elemento gia' riscontrati: gli ack
	 *   arrivano a pezzi — un fotogramma da mezzo megabyte sono ~370 pacchetti
	 *   — e un elemento si libera solo quando il conto copre `dati.n`. */
	bool consegnato;
	size_t confermati;
} uscita;

/* ⛔⭐ FASE 3 — GLI STREAM BLOCCATI DI **QUESTA PASSATA**, E PERCHE' NON E' PIU'
 *     UN `bool`.
 *
 * Fino alla fase 2 qui c'era `bool coda_bloccata`: al primo
 * `NGTCP2_ERR_STREAM_DATA_BLOCKED` si fermava **tutta la coda** per la passata.
 * ⛔ Con uno stream per fotogramma quel `bool` annulla esattamente il beneficio
 *    che `RCP.md` §5.1 compra: «gli stream sono indipendenti, quindi un
 *    fotogramma in ritardo non tocca i successivi» e' vero al livello di QUIC e
 *    diventava **falso un piano sopra**, dentro casa nostra — un fotogramma
 *    lento bloccava in testa tutti quelli dopo, cioe' il blocco di testa che
 *    §5.1 esiste per togliere, rifatto a mano.
 *
 * ⇒ Si blocca **lo stream**, non la coda.  L'ordine DENTRO uno stream resta
 *   quello: si sceglie sempre il primo elemento eleggibile in ordine di
 *   inserimento, quindi il primo di uno stream non bloccato e' il suo piu'
 *   vecchio.
 *
 * ⚠ E il tetto e' dichiarato: oltre `WT_BLOCCATI_MAX` stream bloccati nella
 *   stessa passata ci si ferma come prima e **si scrive**.  Un tetto che si
 *   supera in silenzio e' un tetto che non c'e'. */
#define WT_BLOCCATI_MAX 64

/* ⛔ Quanti fotogrammi possono essere in volo insieme su una sessione.  ⚠ Il
 *    numero non e' arbitrario: `RCP.md` §2.3 dichiara normativi **16** stream
 *    unidirezionali disponibili a RCP, e uno lo prende l'input.  Oltre quel
 *    numero il credito e' finito comunque, e questa tabella non e' il tetto che
 *    morde. */
#define WT_INVOLO_MAX 32

/* ⛔⭐ IL DATAGRAM DELL'AUDIO — fase 7, e i due numeri hanno una misura dietro.
 *
 * `WT_DGRAM_BYTE` — quanto puo' essere lungo il carico di un datagram nostro.
 *    Il piu' grosso che RCP/1 preveda e' il **PCM**: `RCP.md` §5.3 lo fissa a
 *    5 ms = 480 campioni = 960 byte, piu' i 12 dell'intestazione di §6.3 =
 *    **972**, piu' il prefisso di RFC 9297 (al massimo 8) = **980**.
 *    ⚠ `[M]` 17 agosto 2026, sonda `banchi/07-b40`: il datagram che i browser
 *    accettano davvero contro il nostro server e' **1024 byte su Chrome 151**
 *    (fisso) e **1024 → 1214 su Firefox 140esr**.  ⇒ Il PCM ci sta per **52
 *    byte** sul motore piu' stretto, e questo tetto non e' un numero tondo
 *    scelto a caso: e' quel 1024 misurato.
 *
 * `WT_DGRAM_MAX` — quanti blocchi possono aspettare.  ⛔ Non e' una memoria per
 *    la fluidita': e' **lo spazio fra due passate di scrittura**.  Otto blocchi
 *    sono 40 ms di PCM e 160 di Opus; oltre, il piu' vecchio non serve piu' a
 *    nessuno e §6.3 dice che si butta.
 *
 * ⛔⭐ E QUESTO NUMERO E' STATO CAMBIATO A 32 E RIMESSO A 8 NELLO STESSO GIRO,
 *     perche' la diagnosi che lo aveva alzato era SBAGLIATA — 17 agosto 2026.
 *
 *     Il primo giro dava **402 blocchi su 600** in 3 s (resa 67 %), con zero
 *     blocchi persi.  Ho letto «la coda e' il tetto del ritmo» e l'ho alzata:
 *     a 32 la resa e' passata a **80 %** — cioe' e' migliorata, il che sembrava
 *     confermare.  ⛔ Non confermava niente: 2,01 s su 3 e 4,01 su 5 sono
 *     **(T − 1)**, non una frazione.  Il terzo giro l'ha deciso: **9,01 s su
 *     10**.  ⇒ Non era una resa: era **un secondo fisso all'inizio**, e la coda
 *     non c'entrava.
 *
 * ⚠ La lezione e' di metodo: due punti stavano su una retta per il caso, e
 *   «il numero e' migliorato» ha quasi comprato una modifica sbagliata.  Il
 *   terzo punto costava trenta secondi.  ⭐ Il numero e' tornato a 8 perche'
 *   `[M]` a 8 i blocchi persi erano gia' **zero**: era sufficiente, e un
 *   valore piu' alto sarebbe rimasto qui senza una ragione. */
#define WT_DGRAM_BYTE 1024
#define WT_DGRAM_MAX 8

/* ⛔⛔ IL TETTO DEI RIMANDI NON E' PIU' UN TEMPO: E' LA CODA, e basta.
 *
 *      `[M]` 17 agosto 2026, dai contatori della PAGINA dell'utente — i primi
 *      che questo progetto abbia avuto dal lato che ascolta:
 *
 *        ricevuti 1149 · suonati 1149 · BUCHI 23 · coda 191 ms
 *
 *      ⭐ `ricevuti == suonati` sempre: la pagina suona tutto quel che le
 *      arriva, e non e' lei il difetto.  ⛔ Ma le arrivano **39,8 blocchi al
 *      secondo invece di 50**, e con quel deficit un cuscino di 250 ms si
 *      svuota in 1,25 s: **23 buchi in 30 secondi**, uno ogni 1,3 s.  Il conto
 *      chiude al decimale, e dice che il difetto e' tutto sul FILO.
 *
 *      ⇒ Un blocco buttato dopo N rinvii e' un buco garantito.  Il solo tetto
 *      onesto e' **la coda**: otto blocchi = 160 ms di Opus, e oltre quelli il
 *      piu' vecchio non serve piu' a nessuno (§6.3).  ⚠ Questo numero resta
 *      alto solo per non lasciare un ciclo senza fondo — non e' una politica.
 *
 * ⛔ E la guardia sulla congestione e' uscita da qui: `cwnd_left` alto o basso
 *    non cambia che cosa conviene fare con un blocco che non e' ancora partito.
 *    ⚠ Era una condizione che buttava il blocco **proprio quando la finestra
 *    era stretta**, cioe' quando serviva di piu' aspettare.
 *
 * ⛔ Quante PASSATE di scrittura un blocco si puo' rimandare prima di buttarlo.
 *
 * ⚠ Era **8**, e non bastava: `[M]` 17 agosto 2026 il giudice leggeva ancora
 *   **465 Hz invece di 440** — e quel numero E' la perdita, perche' concatenare
 *   i blocchi superstiti comprime il tempo (440 / (1 − 0,054) ≈ 465).
 *
 * ⛔ Il tetto vero non e' questo numero: e' **la coda**.  Otto blocchi di PCM
 *    sono 40 ms, e oltre quelli il piu' vecchio si butta comunque (§6.3).  ⇒ Un
 *    tetto basso sui rimandi non protegge da niente e butta un blocco che
 *    sarebbe partito: il ritardo lo governa gia' la coda. */
#define WT_DGRAM_RIMANDI_MAX 4096

/* ⛔ Il tono di prova (`--audio-prova`), `0` = spento.  Sta in cima e non
 *    accanto alla sua funzione perche' lo legge anche `wt_battito_ns()`, che
 *    viene molto prima — vedi il riquadro dell'orologio li'. */
static uint32_t audio_prova_hz;

/* ⭐ Il gancio verso il figlio, per la stessa ragione: lo chiama `audio_regola()`,
 *    che sta molto prima di `wt_audio_gancio()`. */
static wt_audio_richiesta gancio_audio;
static void *gancio_audio_ctx;

/* Le richieste HTTP/3: qui ne serve una sola cosa — distinguere la CONNECT
 * estesa di WebTransport da tutto il resto. */
typedef struct {
	int64_t id;
	char metodo[16];
	char protocollo[24];
	char uri[192];
	bool usato;
} richiesta;

/* ⭐ Quante perdite di datagram si tengono a mente per riconoscere quelle
 *    FALSE — cioe' il riordino.  Vedi il campo `dgram_anello` piu' sotto: e'
 *    corto apposta, e la ragione sta li'. */
#define WT_DGRAM_ANELLO 512

struct wt {
	ngtcp2_conn *conn;
	ngtcp2_ccerr *ultimo_errore;
	nghttp3_conn *h3;
	char provenienza[80];
	/* ⭐ L'AIUTANTE DI PAM — `DECISIONI.md` §1.10.  ⛔ Non lo possiede questo
	 *    strato: e' uno solo per tutto il server, acceso da `main.c` prima
	 *    che esista una connessione, e arriva di qui perche' il gancio
	 *    `chiedi_verifica` di RCP e' l'unico posto che lo usa.
	 * ⚠ NULL e' lecito e vuol dire «verifica sincrona»: e' il ripiego
	 *   dichiarato, ed e' il guasto che `banchi/02-pam-*` innesta. */
	aiutante *aiuto;

	/* lo stream di controllo di HTTP/3: serve a riconoscerlo in scrittura,
	 * che e' l'unico istante in cui si possa dire al browser che parliamo
	 * WebTransport */
	int64_t ctrl_id;
	bool impostazioni_scritte;
	bool guasto;
	uint8_t impbuf[256];
	size_t impbuf_len;
	/* ⛔ Quanti byte del SETTINGS riscritto sono GIA' USCITI, e quanti byte
	 *    di nghttp3 quel buffer sostituisce.  Servono perche' una scrittura
	 *    PARZIALE e' un esito normale di `ngtcp2_conn_writev_stream` — non
	 *    un guasto — e nell'innesto, prima della cura, uccideva la
	 *    connessione: adesso si riprende dal punto in cui si era arrivati,
	 *    come si fa da sempre per la coda d'uscita. */
	size_t impbuf_off, impbuf_orig;

	stream_giudizio *giudizi;
	size_t ngiudizi, capgiudizi;

	uscita *coda;
	size_t ncoda, capcoda, testa;
	/* ⛔ Gli stream bloccati per QUESTA passata di scrittura: ngtcp2 ha detto
	 *    STREAM_DATA_BLOCKED, e riprovare dentro la stessa passata sarebbe un
	 *    ciclo che non avanza.  ⚠ Erano un `bool` fino alla fase 2 — vedi il
	 *    riquadro di `WT_BLOCCATI_MAX`: quel `bool` rifaceva a mano il blocco
	 *    di testa che `RCP.md` §5.1 esiste per togliere. */
	int64_t bloccati[WT_BLOCCATI_MAX];
	size_t nbloccati;
	/* ⛔ Il tetto e' stato toccato e la coda si ferma davvero: si tiene per
	 *    scriverlo UNA volta invece che a ogni passata. */
	bool troppi_bloccati;

	int64_t sessione; /* lo stream della CONNECT estesa: E' la sessione */

	/* i byte della CONNECT che non compongono ancora una capsula intera */
	bytes capsbuf;
	/* ⛔ Quanti byte di una capsula gia' giudicata TROPPO GRANDE restano da
	 *    buttare mentre passano. */
	uint64_t capsalta;

	richiesta *richieste;
	size_t nrichieste, caprichieste;

	/* ═══ RCP sopra WebTransport ════════════════════════════════════════ */
	struct rcp_sessione *rcp;
	int64_t rcp_stream;

	/* ═══ IL VIDEO DI QUESTA SESSIONE — fase 3 ═════════════════════════ */
	/*
	 * ⛔⭐ QUI C'ERA `bool video_fatto`, ED E' IL FRENO DELLA FASE 2.
	 *
	 *     Il commento diceva: «e' un `bool` e non un contatore perche' la fase
	 *     2 consegna UN'IMMAGINE FERMA: il ciclo dei fotogrammi e' della fase
	 *     3».  ⇒ Adesso e' la fase 3, e il freno si toglie: al suo posto ci
	 *     sta lo stato del **canale**, che si accende una volta e resta acceso,
	 *     e i contatori dei fotogrammi, che crescono.
	 *
	 * ⚠ La ragione per cui il `bool` esisteva resta valida e va onorata lo
	 *   stesso: senza un fondo, `video_regola()` riscriverebbe la stessa riga
	 *   di registro a ogni battito di ogni sessione, e un registro che ripete
	 *   non si legge piu'.  ⇒ `video_detto` e' quel fondo, ed e' solo per il
	 *   registro: non ferma piu' i fotogrammi.
	 */
	/* Il canale video di questa sessione e' acceso: `SESSIONE` e' partita, il
	 * codec e' negoziato, e al figlio e' stato chiesto di catturare. */
	bool video_acceso;
	uint8_t video_codec;
	/* ⛔ «Ho gia' spiegato perche' questa sessione non ha video»: una volta
	 *    sola, e il perche' e' nella riga scritta allora. */
	bool video_detto;
	/* ⛔ L'ultima misura di fotogramma per cui si e' gia' scritto «non e' la tela
	 *    in vigore».  ⚠ E' una MISURA e non un `bool` apposta: cosi' il fondo si
	 *    riarma quando il fatto cambia, invece di tacere per sempre dopo la prima
	 *    volta — ed e' un campo suo, perche' `video_detto` racconta un altro
	 *    fatto e un flag per due fatti ne spegne uno. */
	uint32_t tela_detta_l, tela_detta_a;
	/* ⛔⭐ QUANTI ANNUNCI DI DISACCORDO SONO STATI SCRITTI — e non e' lo stesso
	 *     numero dei fotogrammi non spediti, che e' precisamente il punto.
	 *
	 *     `[M]` B2, 22 agosto 2026: sotto un guasto che rende inammissibili
	 *     TUTTI i fotogrammi, **799 scartati** e nel registro **un annuncio
	 *     solo** — perche' il fondo qui sopra si riarma soltanto quando cambia
	 *     la coppia (tela in vigore, misura del fotogramma), e sotto quel
	 *     guasto non cambia mai.  ⇒ Chi contava le righe leggeva **1** e lo
	 *     chiamava «non spediti»: il nome prometteva 799.  E' la forma **E2**,
	 *     e non l'aveva vista nessuno **perche' 1 e' un numero che sembra sano**.
	 *
	 * ⛔ Il fondo NON si tocca — 799 righe identiche renderebbero il registro
	 *    inutilizzabile.  Quel che mancava e' il CONTO accanto, e sono due
	 *    numeri distinti perche' contano due cose distinte. */
	uint32_t video_annunci_tela;
	/* Quando si e' chiesta l'ultima chiave al figlio, per non chiederne una a
	 * ogni battito mentre la prima e' ancora in viaggio.  ⛔ Non e' la grazia
	 * di §5.2 (quella e' di `rcp.c` e conta dall'ultima chiave SPEDITA): e' il
	 * fondo di una richiesta ripetuta verso il palco. */
	uint64_t chiave_chiesta_ms;
	/* ⭐ Quanto misurava l'ultima CHIAVE spedita, in byte, e l'ultimo intervallo
	 *    che le e' stato applicato — servono a `chiave_intervallo_ms()`, e il
	 *    secondo esiste solo per non ripetere la stessa riga di registro
	 *    cinquanta volte al secondo. */
	uint64_t chiave_byte, chiave_attesa_detta_ms;
	uint32_t video_diffusi, video_saltati;

	/* ⭐⭐ FASE 9 — LA SOGLIA SULLA CODA, e i tre conti che la rendono
	 *     LEGGIBILE dal registro invece che dedotta.
	 *
	 * `sgombra_tenuti` — quante volte un delta e' rimasto in coda perche' la
	 *    coda si svuota entro la soglia.  Si conta **per delta**, non per
	 *    passata, perche' `sgombra_abbandoni` conta per delta: due numeri che
	 *    si devono poter sottrarre.
	 * `sgombra_abbandoni` — quante volte la soglia e' stata superata lo stesso
	 *    e il delta se n'e' andato.
	 * ⛔ `sgombra_credito` — i delta che non sono nemmeno ENTRATI in coda
	 *    perche' §2.3 non aveva credito (`rcp.c:3441`, la causa 4 del debito di
	 *    §5.2).  ⚠ E' LA FORMA INVISIBILE AL RICEVENTE, e sta qui per una
	 *    ragione precisa: la cura di questa fase tocca **la causa 3**, non la
	 *    4.  Se sotto congestione a tenere acceso il debito fosse la 4, la cura
	 *    girerebbe a vuoto e i fotogrammi resterebbero tutti chiavi — con
	 *    questo numero accanto agli altri due il banco sa **a chi** attribuire,
	 *    senza di lui vedrebbe «la cura non ha funzionato» e sarebbe falso.
	 *
	 * ⚠ `sgombra_sopra` e' il fondo delle righe di registro: si scrive quando
	 *   lo STATO cambia (sotto→sopra e sopra→sotto), non a trenta volte al
	 *   secondo.  ⛔ E la riga d'avvio col valore in vigore la scrive
	 *   `wt_sgombra_soglia()`, che `main.c` chiama sempre: «spento» e «non e'
	 *   mai scattato» non devono avere la stessa faccia. */
	uint32_t sgombra_tenuti, sgombra_abbandoni, sgombra_credito;
	bool sgombra_sopra;

	/* ⭐⭐ FASE 9 — IL REGOLATORE DEL RITMO, e i suoi numeri.
	 *
	 * `video_ritmo_scesi` — quanti fotogrammi NON sono partiti perche' la coda
	 *    non si svuotava.  ⛔ Non entra in `video_saltati`: quello conta i
	 *    fotogrammi INAMMISSIBILI (tela sbagliata, credito finito, rifiuto di
	 *    rcp), questo conta una DISCESA DI RITMO decisa da noi.  E' la lezione
	 *    di `video_annunci_tela` (:331-343): due numeri per due fatti, o uno
	 *    dei due mente con un valore che sembra sano.
	 *
	 * `ritmo_giu` / `ritmo_da_ms` / `ritmo_da_n` — se un episodio di discesa e'
	 *    in corso, da quando e da che conto: servono a scrivere DUE righe per
	 *    episodio invece di una per fotogramma saltato.  ⛔ A trenta al secondo
	 *    la seconda forma e' il difetto dei 30,8 GB di registro.
	 *
	 * ⛔⭐ E I QUATTRO SEGUENTI NON DECIDONO NIENTE: sono lo STRUMENTO con cui
	 *     si dimostra che il ritmo non cala a scena ferma.  `LEZIONI.md` §1.9:
	 *     un contatore a zero su un ramo mai raggiunto non dimostra niente —
	 *     «vuoto» e «proibito» hanno la stessa faccia.  ⇒ Si conta quante volte
	 *     `arretrato` e' stato LETTO in ogni secondo, oltre a quanto valeva:
	 *     zero letture vuol dire che il palco non ha consegnato niente (scena
	 *     ferma), e NON «arretrato zero».  La riga la scrive `ritmo_ciclo()`,
	 *     che gira col battito e quindi esce anche quando di fotogrammi non ne
	 *     arriva nessuno. */
	uint32_t video_ritmo_scesi;
	bool     ritmo_giu;
	uint64_t ritmo_da_ms;
	uint32_t ritmo_da_n;
	uint32_t ritmo_letture;
	unsigned ritmo_max, ritmo_ultimo;
	uint32_t ritmo_detti_n;
	uint64_t ritmo_detto_ms;

	/* ⛔⭐⭐ FASE 9 — LA FOTOGRAFIA DELLA RETE DEL SECONDO PRIMA, e serve a
	 *      rispondere all'unica domanda che sotto perdita conta: **e' la linea
	 *      o siamo noi?**
	 *
	 *      Fino a qui il registro sapeva contare solo la meta' NOSTRA del
	 *      ritardo — `sgombra_tenuti` (l'abbiamo tenuto in coda),
	 *      `sgombra_abbandoni` (l'abbiamo buttato), `video_ritmo_scesi` (non
	 *      l'abbiamo nemmeno spedito).  ⛔ La meta' della RETE — un pacchetto
	 *      perduto e rimandato da QUIC, la finestra di congestione che si e'
	 *      chiusa — non la sapeva contare nessuno, e ogni misura sotto perdita
	 *      finiva in una discussione invece che in un'attribuzione.
	 *
	 * ⚠ Questi campi NON DECIDONO NIENTE: sono la fotografia dell'ultima riga
	 *   scritta, e servono solo a fare la differenza («quanti nell'intervallo»)
	 *   e a tacere quando non e' cambiato niente.  Nessuna soglia, nessun
	 *   ritmo, nessun interruttore: `rete_ciclo()` e' pura osservazione.
	 *
	 * ⛔ `rete_detto_ms` a 0 vuol dire «mai detta», e la prima riga esce
	 *    comunque: «la sessione non ha ancora parlato» e «non e' cambiato
	 *    niente» non devono avere la stessa faccia (`LEZIONI.md` §1.9). */
	uint64_t rete_detto_ms;
	uint64_t rete_pkt_lost, rete_bytes_lost;
	uint64_t rete_pkt_sent, rete_pkt_recv, rete_pkt_discarded;
	/* Il giudizio dell'ultima riga: se cambia, la riga esce anche a contatori
	 * fermi — passare da «la finestra e' chiusa» a «niente da segnalare» e'
	 * precisamente il fatto che si vuole vedere. */
	int rete_giudizio;

	/* ⭐⭐⭐ I DATAGRAM PERSI — E LA MISURA DEL RIORDINO CHE NGTCP2 NON DA'.
	 *
	 *     `ngtcp2.h:3442` dice una cosa che vale piu' del contatore che
	 *     annuncia: *«Note that the loss might be spurious, and DATAGRAM frame
	 *     might be acknowledged later»*.  ⇒ Se per lo stesso `dgram_id` arriva
	 *     prima `lost_datagram` e POI `ack_datagram`, quella perdita **non era
	 *     una perdita**: era un pacchetto arrivato FUORI SEQUENZA, dichiarato
	 *     perduto dalla soglia dei tre pacchetti e riscontrato dopo.
	 *
	 * ⭐ E' la firma del riordino, presa dal lato del server, senza patch a
	 *   ngtcp2 e senza dedurla dai numeri di sequenza dell'applicazione — che
	 *   era l'unica strada che si vedeva prima di leggere quella riga.
	 *   ⚠ E' parziale per costruzione: vale sui **datagram**, cioe' sull'audio;
	 *   sugli stream QUIC non c'e' un identificativo per pezzo e questa strada
	 *   non c'e'.  Il prezzo si dichiara invece di lasciar credere che il
	 *   numero copra tutto il traffico.
	 *
	 * ⛔ L'anello e' corto APPOSTA: un riscontro che arriva dopo 512 perdite
	 *    dichiarate non e' piu' un riordino, e contarlo tale gonfierebbe il
	 *    numero proprio nel caso — la linea che perde davvero — in cui deve
	 *    restare onesto.  ⇒ Quel che esce dall'anello resta perduto. */
	uint64_t dgram_persi;        /* `lost_datagram` ha detto: perduto */
	uint64_t dgram_riscontrati;  /* `ack_datagram` ha detto: arrivato */
	uint64_t dgram_falsi;        /* perduto E POI riscontrato = RIORDINO */
	uint64_t dgram_anello[WT_DGRAM_ANELLO];
	unsigned dgram_anello_i;
	uint64_t rete_dgram_persi, rete_dgram_falsi;

	/* ⛔⭐⭐ FASE 9 — LA LINEA MORTA: i campi su cui si prende la DECISIONE
	 *      piu' visibile di tutto il prodotto — buttare fuori una sessione.
	 *
	 *      ⚠ Sono SEPARATI dai `rete_*` qui sopra apposta, e non per pigrizia:
	 *        quelli sono la fotografia dell'ultima RIGA SCRITTA e si muovono
	 *        solo quando la riga esce (cioe' quando qualcosa e' cambiato).
	 *        Questi si muovono quando si CHIUDE UNA FINESTRA DI GIUDIZIO, che
	 *        e' un altro ritmo.  ⛔ Riusare i primi legherebbe la decisione al
	 *        filtro anti-rumore del registro: una sessione che perde in modo
	 *        costante fa uscire poche righe, e la finestra si allungherebbe da
	 *        se' — cioe' la soglia cambierebbe senza che nessuno l'abbia
	 *        scritto.
	 *
	 * ⛔ `lm_finestra_ms == 0` vuol dire «mai aperta»: il primo giro fotografa
	 *    e non giudica.  Un giudizio preso sulla differenza coi totali di tutta
	 *    la connessione sarebbe una frazione su una finestra lunga quanto la
	 *    sessione, cioe' un'altra grandezza. */
	uint64_t lm_finestra_ms;    /* quando si e' aperta la finestra in corso   */
	uint64_t lm_pkt_sent;       /* `pkt_sent` all'apertura della finestra     */
	uint64_t lm_pkt_lost;       /* `pkt_lost` all'apertura della finestra     */
	/* ⛔⛔⭐ LA FRAZIONE DI PERDITA E' UN TESTIMONE, NON PIU' UN GIUDICE — 23
	 *      agosto 2026, e la ragione sta per intero nel riquadro sopra
	 *      `WT_LM_STALLO_MS`.  Questi tre campi tengono la fotografia
	 *      dell'ultima finestra CHIUSA, cosi' la riga dello scatto porta il
	 *      numero anche quando a decidere e' stata un'altra causa. */
	unsigned lm_permille;       /* la frazione dell'ultima finestra chiusa    */
	uint64_t lm_persi_v, lm_spediti_v; /* i due conti di quella finestra      */
	uint64_t lm_durata_v;       /* e quanto e' durata davvero, in ms          */
	/* ⛔⭐⭐ LO STALLO DELL'USCITA — la grandezza su cui si DECIDE da oggi.
	 *
	 *      Sono due contatori monotoni piu' un istante, e ognuno dei tre porta
	 *      una meta' della frase «da quanto tempo non esce un fotogramma pur
	 *      avendone da mandare»:
	 *
	 *        · `lm_usciti`  — byte di VIDEO consegnati a ngtcp2 (`coda_consegna`):
	 *                         se sale, il filo porta, e il conto riparte;
	 *        · `lm_offerti` — fotogrammi che il palco ci ha dato per questa
	 *                         sessione, contati PRIMA di ogni freno, sgombero o
	 *                         rifiuto: se non sale e la coda e' vuota, non
	 *                         c'era niente da mandare e il conto NON PARTE;
	 *        · `lm_uscita_ms` — l'istante in cui il conto e' ripartito l'ultima
	 *                         volta, per una delle due ragioni qui sopra.
	 *
	 * ⛔ I due `_visti` sono i valori all'ultimo giro di giudizio: la grandezza
	 *    e' una DIFFERENZA fra due campionamenti, non un totale.  Un totale
	 *    direbbe «da inizio sessione», che e' un'altra cosa. */
	uint64_t lm_usciti, lm_usciti_visti;
	uint64_t lm_offerti, lm_offerti_visti;
	uint64_t lm_uscita_ms;
	/* ⛔ Il silenzio non e' un orologio libero: e' «da quando il client non fa
	 *    piu' vedere un pacchetto», e accanto ci sta il numero delle volte che
	 *    NOI gliene abbiamo mandato uno da allora.  Senza il secondo, una
	 *    sessione in cui non parla nessuno dei due si dichiarerebbe morta da
	 *    sola — ed e' invece un desktop fermo. */
	uint64_t lm_vivo_ms;        /* l'ultima volta che `pkt_recv` e' salito    */
	uint64_t lm_pkt_recv;       /* `pkt_recv` di quella volta                 */
	uint64_t lm_pkt_sent_vivo;  /* `pkt_sent` di quella volta = le PROVE      */
	bool lm_scattata;           /* ⛔ una volta sola: dopo, il filo cade      */

	/* ⛔⭐ I FOTOGRAMMI IN VOLO — §5.1, «uno piu' recente e' gia' partito».
	 *
	 *     Un fotogramma che RCP ha gia' chiuso con FIN puo' avere ancora tutti
	 *     i suoi byte fermi in questa coda: per RCP e' partito, sul filo non
	 *     e'.  §5.1 dice che quello si PUO' azzerare — «i byte non ancora
	 *     spediti non partono affatto» — ed e' l'unica strada per cui un
	 *     abbandono si veda davvero dal lato che riceve.
	 *
	 * ⚠ Si tiene qui e non in `rcp.c` perche' e' un fatto della CODA; e le tre
	 *   conseguenze (la riga di registro, il conto, il debito della chiave)
	 *   stanno in `rcp.c`, che e' l'unico a possederle. */
	struct {
		int64_t stream;
		uint32_t numero;
		bool chiave;
		bool vivo;
		bool detto; /* la chiave che trattiene la coda si dice una volta */
	} involo[WT_INVOLO_MAX];
	size_t ninvolo;
	/* ⛔ Lo stream che `gancio_video_apri()` ha appena aperto: `rcp.c` non lo
	 *    restituisce, e dedurlo da «l'ultimo aperto sulla connessione» sarebbe
	 *    indovinare. */
	int64_t video_stream_ultimo;

	/* ═══ L'AUDIO DI QUESTA SESSIONE — fase 7 ══════════════════════════ */
	/*
	 * ⛔⭐ L'AUDIO NON E' IL VIDEO, E LA DIFFERENZA E' TUTTA QUI SOTTO.
	 *
	 *     Il video vive su stream (affidabili): i byte che non entrano in un
	 *     pacchetto RESTANO in coda e partono dopo, ed e' obbligatorio —
	 *     saldare un messaggio a byte monchi fabbricherebbe una violazione
	 *     del client (vedi `NGTCP2_ERR_STREAM_DATA_BLOCKED` in `wt_scrivi`).
	 *
	 *     L'audio vive su datagram, e `RCP.md` §6.3 dice l'opposto con parole
	 *     sue: «nessuna ritrasmissione, nessun riordino».  ⇒ Un blocco che non
	 *     parte NON si conserva: si BUTTA, e si conta.
	 *
	 * ⭐ E si buttano i PIU' VECCHI, non i piu' nuovi — e' la regola che v1
	 *    aveva gia' trovato (`v1/remotix-c/src/altoparlante.h`): «il suono in
	 *    ritardo non serve a nessuno, e una coda che cresce all'infinito
	 *    finirebbe per mangiare la memoria del server per riprodurre un rumore
	 *    di mezzo minuto fa».
	 */
	struct {
		uint8_t d[WT_DGRAM_BYTE];
		size_t n;
	} dgram[WT_DGRAM_MAX];
	size_t ndgram, dgram_testa;
	uint64_t dgram_id; /* l'identificativo che ngtcp2 riporta negli esiti */

	bool audio_acceso;
	uint8_t audio_codec;
	/* ⛔ «Ho gia' spiegato perche' questa sessione non ha audio»: una volta
	 *    sola, come `video_detto`, e per la stessa ragione. */
	bool audio_detto;
	/* ⛔ «Il pari non accetta datagram»: detto una volta.  ⚠ `RCP.md` §2.2 li
	 *    PRETENDE, ma §6.3 vieta di chiudere la connessione per un fatto dei
	 *    datagram — quindi si dichiara e si tace, non si uccide. */
	bool dgram_negati_detto;
	uint64_t audio_spediti, audio_buttati, audio_rifiutati;
	/* ⛔ RIMANDATI e RIFIUTATI sono due fatti diversi e non si sommano: il
	 *    primo e' «il pacer ha detto non adesso» e il blocco parte lo stesso un
	 *    attimo dopo; il secondo e' «buttato».  Un contatore solo per due esiti
	 *    opposti direbbe che l'audio si perde anche quando arriva tutto. */
	uint64_t audio_rimandati;
	/* Quante PASSATE di fila il blocco in testa e' stato rimandato. */
	unsigned dgram_rimandi;
	/* L'istante dell'ultimo rimando: dentro la stessa passata non si richiede. */
	ngtcp2_tstamp dgram_rimando_ts;

	/* Il tono di prova (`--audio-prova`), che di norma non esiste. */
	audio_cod *tono_cod;
	uint64_t tono_prossimo_us; /* l'istante del prossimo blocco */
	uint64_t tono_i;           /* l'indice del campione: la fase e' continua */

	/* La lista delle sessioni vive, per la diffusione dei fotogrammi. */
	wt *viva_dopo;

	/* ⛔ La chiusura della sessione ASPETTA che la coda d'uscita si sia
	 *    svuotata, e poi ancora un po': vedi `chiudi_sessione()`. */
	int chiusura;
	ngtcp2_tstamp chiusura_da;
	/* ⛔⭐ E L'ATTESA HA UN FONDO — rilievo B-3, 10 agosto 2026 notte.
	 *
	 *     «Aspetta che la coda si svuoti» e' una condizione che qualcuno deve
	 *     far avvenire.  Finche' la coda non si svuota, `wt_batti()` riazzera
	 *     `chiusura_da` a ogni battito e la capsula di §3.1 punto 3 NON PARTE
	 *     MAI: il motivo, che e' «quel che salva le diagnosi», resta dentro il
	 *     server.  ⚠ Un lavoro rimandato a una condizione che nessuno fa piu'
	 *     avvenire non e' rimandato: e' perduto.
	 *
	 * ⭐ Da qui la scadenza: passata quella, la capsula parte lo stesso e la
	 *    rinuncia si SCRIVE. */
	ngtcp2_tstamp chiusura_scadenza;

	/* ⛔⭐ §4.6 — IL TETTO DELLA SESSIONE CHE NON APRE MAI IL CANALE.
	 *
	 * ✅ `DECISIONI.md` §7.17, deciso dall'utente l'11 agosto 2026: **5 s**
	 *    dall'apertura della sessione WebTransport all'apertura del canale di
	 *    controllo, poi `TEMPO_SCADUTO`.
	 *
	 * ⛔ Perche' serviva un orologio in piu': quelli di §4.6 partono
	 *    dall'apertura del CANALE, quindi chi apriva la sessione e il canale
	 *    non lo apriva mai **non aveva addosso nessun tetto**.  `[M]` 11 agosto
	 *    2026, banco B6: la sessione senza canale e' rimasta viva 20 014 ms
	 *    senza che succedesse niente.
	 *
	 * ⚠ E il tempo d'inattivita' di QUIC non lo copriva: quello conta il
	 *   SILENZIO, e una sessione che scrive su un altro stream non e'
	 *   silenziosa — teneva il posto a tempo indeterminato.
	 *
	 * ⛔ Zero quando il canale c'e' gia' (o non c'e' ancora la sessione): un
	 *    orologio che non e' partito e uno che e' scaduto non devono avere la
	 *    stessa faccia. */
	ngtcp2_tstamp canale_entro;

	/* ⛔ Quanti byte ci sono in coda, per il tetto di `coda_metti()`.
	 * ⚠ FASE 9: conta i byte che devono ANCORA PARTIRE.  Un elemento
	 *   consegnato a ngtcp2 esce da questo conto anche se la sua memoria e'
	 *   ancora nostra — il tetto di `coda_metti()` regola l'ARRETRATO, e
	 *   metterci dentro i byte in volo farebbe rifiutare fotogrammi buoni per
	 *   colpa di roba che e' gia' sul filo. */
	size_t byte_in_coda;
	/* ⛔⭐ FASE 9 — IL PREZZO IN MEMORIA DELLA CURA, MISURATO E NON STIMATO.
	 *
	 *     I byte CONSEGNATI a ngtcp2 e non ancora confermati: fuori dal conto
	 *     della coda (non devono piu' partire) ma ancora allocati, perche' il
	 *     contratto di `writev_stream` pretende che lo siano finche' non
	 *     arriva l'ack o non si chiude lo stream.
	 *
	 * ⭐ QUANTO E' — e il numero non lo decide questo file: sono i byte in volo
	 *    su QUIC, cioe' al piu' la finestra di congestione piu' quel che e'
	 *    perduto e non ancora ridichiarato.  Su una linea che porta e' l'ordine
	 *    di decine-centinaia di KB per sessione; il tetto duro non e' nostro ma
	 *    del pari — non puo' concederci piu' credito di `initial_max_data`.
	 * ⛔ `byte_in_volo_max` e' la PUNTA, e si scrive alla chiusura: e' la
	 *    grandezza che dice se la cura tiene o se sta trattenendo memoria. */
	size_t byte_in_volo, byte_in_volo_max;
	/* Quanti stream di troppo (§2.5) hanno gia' scritto: per non riempire il
	 * registro con una riga per pacchetto. */
	uint64_t scartati_stream, scartati_byte;

	/* ⭐ Il NOSTRO orologio, al posto del keep-alive dell'innesto. */
	ngtcp2_tstamp battito;
	uint64_t battito_ms;
	/* ⛔ §4.6: i PING del TRASPORTO mentre si aspettano le credenziali.  Si
	 *    tiene qui se sono accesi, per non richiamare ngtcp2 a ogni battito e
	 *    per poterlo SCRIVERE nel registro quando cambia. */
	bool tienila_viva;
};

/* ------------------------------------------------------------------------ */
/* Gli interi variabili di QUIC (RFC 9000 §16).  Servono tre volte e non ci   */
/* sono in nessuna delle due librerie: nghttp3 il suo se lo tiene per se'.    */

static size_t varint_scrivi(uint8_t *dest, uint64_t v)
{
	if (v < 64) {
		dest[0] = (uint8_t)v;
		return 1;
	}
	if (v < 16384) {
		dest[0] = (uint8_t)(0x40 | (v >> 8));
		dest[1] = (uint8_t)(v & 0xff);
		return 2;
	}
	if (v < 1073741824) {
		dest[0] = (uint8_t)(0x80 | (v >> 24));
		dest[1] = (uint8_t)((v >> 16) & 0xff);
		dest[2] = (uint8_t)((v >> 8) & 0xff);
		dest[3] = (uint8_t)(v & 0xff);
		return 4;
	}
	dest[0] = (uint8_t)(0xc0 | (v >> 56));
	for (size_t i = 1; i < 8; i++)
		dest[i] = (uint8_t)((v >> (8 * (7 - i))) & 0xff);
	return 8;
}

/* ⛔ Restituisce 0 se i byte non bastano: «non lo so ancora» e «zero» sono due
 *    cose diverse, e confonderle e' `LEZIONI.md` §1.9. */
static size_t varint_leggi(uint64_t *v, const uint8_t *src, size_t len)
{
	size_t n;
	if (len == 0)
		return 0;
	n = (size_t)1 << (src[0] >> 6);
	if (len < n)
		return 0;
	*v = src[0] & 0x3f;
	for (size_t i = 1; i < n; i++)
		*v = (*v << 8) | src[i];
	return n;
}

/* ⛔ I due numeri con cui un server dichiara WebTransport, e sono DUE perche'
 *    le bozze in circolazione sono due:
 *
 *      0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   bozza 02
 *      0xc671706a  SETTINGS_WT_MAX_SESSIONS       bozza 07 e oltre
 *
 * ⚠ E la differenza non e' accademica: `aioquic` 1.2 — il cliente di prova —
 *   implementa la 02 `[R]`, mentre i browser di oggi cercano la 07.  Un server
 *   che ne mandasse una sola funzionerebbe con meta' dei nostri strumenti e non
 *   con l'altra meta', e la meta' che funziona sarebbe quella sbagliata da cui
 *   trarre conclusioni.  Si mandano tutt'e due: un'impostazione sconosciuta si
 *   ignora. */
#define WT_ENABLE_WEBTRANSPORT 0x2b603742ULL
#define WT_MAX_SESSIONS 0xc671706aULL

/* ⛔⭐ IL TETTO DI UNA CAPSULA, E SI CONTROLLA PRIMA DI TENERE I BYTE.
 *
 * `RCP.md` §6.1: «un ricevente che alloca `lunghezza` byte e poi verifica ha
 * gia' regalato un megabyte a chiunque sappia scrivere sei byte».  ⚠ Aspettare
 * i byte invece di allocarli e' lo stesso regalo, fatto piu' lentamente.
 *
 * ⭐ Il numero e' quel che serve alla sola capsula che ci riguarda:
 * `CLOSE_WEBTRANSPORT_SESSION` porta un codice a 32 bit e una ragione che
 * WebTransport limita a 1024 byte. */
#define WT_CAPSULA_MAX (1024 + 4)

/* Quanto si aspetta, dopo che la coda si e' svuotata, prima di mandare la
 * capsula che chiude la sessione.  ⭐ Nell'innesto erano «cinque passate di
 * scrittura» col keep-alive a 100 ms, cioe' mezzo secondo: qui il tempo si
 * misura invece di contarlo, e sul filo non va niente. */
#define WT_ATTESA_CHIUSURA_NS (500ULL * NGTCP2_MILLISECONDS)

/* ⛔ §4.6, la riga che mancava: dall'apertura della sessione WebTransport
 *    all'apertura del canale di controllo, **5 s**.
 * ✅ `DECISIONI.md` §7.17, deciso dall'utente l'11 agosto 2026.
 * ⭐ Lo stesso numero del primo tetto di §4.6, e non per simmetria: aprire il
 *    canale e' il primo atto obbligatorio della sessione (§2.5), non dipende
 *    da quanto e' veloce a digitare una persona e non dipende dalla rete piu'
 *    di quanto ne dipenda il `CIAO`. */
#define WT_TETTO_CANALE_NS (5000ULL * NGTCP2_MILLISECONDS)

/* ------------------------------------------------------------------------ */
/* Gli elenchi.                                                              */

static stream_giudizio *giudizio_trova(wt *w, int64_t id)
{
	for (size_t i = 0; i < w->ngiudizi; i++)
		if (w->giudizi[i].id == id)
			return &w->giudizi[i];
	return NULL;
}

static stream_giudizio *giudizio_crea(wt *w, int64_t id)
{
	stream_giudizio *g = giudizio_trova(w, id);
	if (g)
		return g;
	if (w->ngiudizi == w->capgiudizi) {
		size_t c = w->capgiudizi ? w->capgiudizi * 2 : 8;
		stream_giudizio *n = realloc(w->giudizi, c * sizeof *n);
		if (!n)
			return NULL;
		w->giudizi = n;
		w->capgiudizi = c;
	}
	g = &w->giudizi[w->ngiudizi++];
	memset(g, 0, sizeof *g);
	g->id = id;
	g->genere = G_INCERTO;
	return g;
}

static richiesta *richiesta_trova(wt *w, int64_t id, bool crea)
{
	for (size_t i = 0; i < w->nrichieste; i++)
		if (w->richieste[i].usato && w->richieste[i].id == id)
			return &w->richieste[i];
	if (!crea)
		return NULL;
	for (size_t i = 0; i < w->nrichieste; i++)
		if (!w->richieste[i].usato) {
			memset(&w->richieste[i], 0, sizeof w->richieste[i]);
			w->richieste[i].id = id;
			w->richieste[i].usato = true;
			return &w->richieste[i];
		}
	if (w->nrichieste == w->caprichieste) {
		size_t c = w->caprichieste ? w->caprichieste * 2 : 8;
		richiesta *n = realloc(w->richieste, c * sizeof *n);
		if (!n)
			return NULL;
		w->richieste = n;
		w->caprichieste = c;
	}
	{
		richiesta *r = &w->richieste[w->nrichieste++];
		memset(r, 0, sizeof *r);
		r->id = id;
		r->usato = true;
		return r;
	}
}

/* ⛔⭐ FASE 9 — QUESTO STREAM PORTA UN FOTOGRAMMA?  Serve a UNA cosa sola: a
 *     contare i byte di VIDEO che escono verso il filo, che e' la meta'
 *     «e' uscito» della grandezza della linea morta (il riquadro sopra
 *     `WT_LM_STALLO_MS`).
 *
 * ⛔ L'elenco `involo[]` e' l'unico posto in cui il fatto e' scritto: gli
 *    stream del video li apriamo NOI e nessuno ce li dichiara altrove.
 *    Distinguerli per esclusione — «tutto quel che non e' il canale di
 *    controllo» — ci metterebbe dentro anche gli appunti, e un trasferimento di
 *    appunti riuscito mentre il video e' fermo azzererebbe il conto dello
 *    stallo proprio nel giro in cui deve correre.
 *
 * ⚠ IL PREZZO, DICHIARATO: un fotogramma che non e' entrato nell'elenco perche'
 *   `WT_INVOLO_MAX` era pieno non viene contato, quindi i suoi byte non
 *   azzerano lo stallo.  ⛔ Sbaglia dalla parte SEVERA — ma un elenco pieno
 *   vuol dire trentadue fotogrammi in volo insieme, cioe' una coda che non si
 *   svuota: e' gia' lo stallo, non un caso sano scambiato per rotto.  E la
 *   riga di `involo_aggiungi()` lo dichiara quando succede. */
static bool stream_di_un_fotogramma(const wt *w, int64_t id)
{
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo && w->involo[i].stream == id)
			return true;
	return false;
}

/* ⛔ Un elemento muore qui e in nessun altro posto: e' l'unico punto in cui
 *    `byte_in_coda` (e adesso `byte_in_volo`) cala, e due punti che lo
 *    calassero divergerebbero.
 *
 * ⛔⭐ FASE 9 — E «MORIRE» VUOL DIRE `free()`, cioe' «da adesso ngtcp2 NON DEVE
 *     piu' poter rileggere questi byte».  I tre soli chiamanti leciti sono le
 *     due condizioni del contratto piu' la fine della connessione:
 *
 *       1. `coda_conferma()`     — l'ack copre i byte;
 *       2. `wt_stream_chiuso()`  — lo stream e' chiuso (ngtcp2 dice testualmente
 *          che «after stream_close ... application can free all unacknowledged
 *          stream data»);
 *       3. `coda_butta_stream()` — lo stream e' stato AZZERATO un attimo prima
 *          (`ngtcp2_conn_shutdown_stream_write()`), e dopo un `RESET_STREAM`
 *          ngtcp2 non rimette in coda i frame di quello stream.
 *
 * ⛔ «Serializzato» NON e' fra questi, ed era il difetto del 23 agosto. */
static void coda_uccidi(wt *w, size_t i)
{
	uscita *u;
	if (i >= w->ncoda)
		return;
	u = &w->coda[i];
	if (u->morto)
		return;
	/* ⚠ I due conti sono ESCLUSIVI: chi e' consegnato e' gia' uscito da
	 *   `byte_in_coda` ed e' entrato in `byte_in_volo`.  Calarli tutt'e due
	 *   toglierebbe due volte gli stessi byte da grandezze diverse. */
	if (u->consegnato) {
		if (w->byte_in_volo >= u->dati.n)
			w->byte_in_volo -= u->dati.n;
		else
			w->byte_in_volo = 0;
	} else if (w->byte_in_coda >= u->dati.n) {
		w->byte_in_coda -= u->dati.n;
	} else {
		w->byte_in_coda = 0;
	}
	bytes_libera(&u->dati);
	u->morto = true;
	/* I morti in testa non servono a nessuno: la testa scorre. */
	while (w->testa < w->ncoda && w->coda[w->testa].morto)
		w->testa++;
	if (w->testa == w->ncoda)
		w->testa = w->ncoda = 0;
}

/* ⛔⭐ FASE 9 — «CONSEGNATO»: tutti i byte sono dentro a ngtcp2, e NON SI
 *     LIBERANO.  E' quel che prima faceva `coda_uccidi()` a questo punto.
 *
 *     L'elemento esce dalla scelta (`coda_scegli()`) e dal conto dell'arretrato
 *     (`byte_in_coda`, `coda_vuota()`) — non ha piu' niente da offrire — ma
 *     resta in coda con i suoi byte, perche' sono quelli che ngtcp2 rileggera'
 *     se un pacchetto va perduto. */
static void coda_consegna(wt *w, size_t i)
{
	uscita *u;
	if (i >= w->ncoda)
		return;
	u = &w->coda[i];
	if (u->morto || u->consegnato)
		return;
	/* ⭐ Un elemento SENZA byte — il FIN di §6.2, che e' un elemento della coda
	 *    come gli altri — non da' nessun puntatore a ngtcp2: non c'e' niente da
	 *    tenere in vita.  ⛔ E tenerlo lo lascerebbe in coda PER SEMPRE: non
	 *    occupa nessun offset dello stream, quindi nessun ack potrebbe mai
	 *    coprirlo, e `coda_vuota()` non tornerebbe piu' vera. */
	if (u->dati.n == 0) {
		coda_uccidi(w, i);
		return;
	}
	if (w->byte_in_coda >= u->dati.n)
		w->byte_in_coda -= u->dati.n;
	else
		w->byte_in_coda = 0;
	u->consegnato = true;
	w->byte_in_volo += u->dati.n;
	if (w->byte_in_volo > w->byte_in_volo_max)
		w->byte_in_volo_max = w->byte_in_volo;
	/* ⛔⭐⭐ FASE 9 — ED E' QUI CHE «UN FOTOGRAMMA ESCE», nell'unico punto del
	 *      file in cui il fatto avviene: `ndatalen` ha coperto tutto
	 *      l'elemento, cioe' quei byte sono finiti DENTRO UN PACCHETTO.
	 *
	 *      ⚠ Non e' «il client li ha visti»: e' «sono partiti».  Ed e' voluto —
	 *        la grandezza della linea morta dev'essere LOCALE e monotona (la
	 *        forma P20 di `RCP.md:398`), o la decisione di buttare fuori una
	 *        sessione dipenderebbe da quel che dice il pari.
	 *
	 * ⛔ Si contano i BYTE e non i fotogrammi interi, e la ragione e' la
	 *    direzione dell'errore: una chiave da 60 000 byte su una linea stretta
	 *    puo' metterci secondi a uscire tutta, e contando i fotogrammi quei
	 *    secondi sarebbero uno «stallo» mentre il filo sta lavorando.  Un byte
	 *    che parte e' un filo che porta. */
	if (stream_di_un_fotogramma(w, u->id))
		w->lm_usciti += u->dati.n;
}

/* ⛔⭐ FASE 9 — L'ACK LIBERA, e prima non lo faceva nessuno.
 *
 *     `acked_stream_data_offset` arriva, dice `ngtcp2.h`, «sequentially in
 *     increasing order of offset without any overlap»: e' l'AVANZAMENTO
 *     CONTIGUO del riscontro su quello stream, ed e' la stessa grandezza che
 *     `nghttp3_conn_add_ack_offset()` si aspetta.  ⇒ Sommare i `datalen` da'
 *     quanti byte del flusso sono confermati, e si consumano contro gli
 *     elementi di quello stream in ORDINE D'INSERIMENTO — che e' l'ordine in
 *     cui sono usciti, perche' `coda_scegli()` scorre in quell'ordine.
 *
 * ⛔ E LO STREAM DELLA CONNECT (`w->sessione`) E' ESCLUSO — la ragione si vede
 *    solo scrivendola: li' **non siamo gli unici a scrivere**.  nghttp3 ci mette
 *    le intestazioni della risposta, agli offset piu' bassi, e i loro ack
 *    entrerebbero in questo conto: la nostra capsula di chiusura verrebbe
 *    liberata PRIMA di essere confermata, cioe' rifarebbe in piccolo il difetto
 *    del 23 agosto.  ⇒ Su quello stream si aspetta l'ALTRA meta' del contratto,
 *    la chiusura (`wt_stream_chiuso()`).  Sono nove byte, e quando entrano in
 *    coda la sessione sta gia' finendo.
 *
 * ⭐ Su tutti gli altri l'esclusiva e' vera e si dimostra: gli stream del video
 *    e degli appunti li APRIAMO NOI (`ngtcp2_conn_open_uni_stream()`, e nessun
 *    altro ci scrive), e il canale di controllo (`rcp_stream`) e' giudicato
 *    `G_WT` — i suoi byte tornano `E_MIO` da `smista()` e a nghttp3 non
 *    arrivano mai.  ⇒ Su quegli stream il nostro primo byte sta all'offset 0 e
 *    la somma dei `datalen` e' il nostro conto, esatto. */
static void coda_conferma(wt *w, int64_t id, uint64_t quanti)
{
	size_t i = w->testa;

	if (id == w->sessione)
		return;
	while (quanti > 0 && i < w->ncoda) {
		uscita *u = &w->coda[i];
		size_t apertura;

		if (u->morto || u->id != id) {
			i++;
			continue;
		}
		/* ⛔ Non si conferma piu' di quel che si e' consegnato: il riscontro
		 *    non puo' correre davanti alla scrittura.  ⚠ Zero qui vuol dire
		 *    che siamo arrivati alla frontiera di quello stream, e piu' avanti
		 *    non c'e' niente di piu' vecchio: si smette. */
		apertura = u->off - u->confermati;
		if (apertura == 0)
			break;
		if ((uint64_t)apertura > quanti) {
			u->confermati += (size_t)quanti;
			return;
		}
		u->confermati += apertura;
		quanti -= apertura;
		if (u->consegnato && u->confermati >= u->dati.n) {
			coda_uccidi(w, i);
			/* ⚠ `coda_uccidi()` fa scorrere la testa e puo' azzerare la coda
			 *   intera: il fondo del ciclo va riletto, non ricordato. */
			if (w->ncoda == 0)
				return;
		}
		i++;
	}
}

/* ⛔⭐ FASE 9 — «VUOTA» VUOL DIRE «NIENTE DA SPEDIRE», non «niente in memoria».
 *
 *     Un elemento consegnato e non ancora confermato non ha piu' un byte da
 *     mandare: contarlo qui terrebbe acceso `wt_ha_da_dire()` per sempre — il
 *     server girerebbe a vuoto — e soprattutto il ramo `!coda_vuota` di
 *     `wt_batti()` riazzererebbe `chiusura_da` a ogni battito, cioe' la capsula
 *     di §3.1 punto 3 non partirebbe MAI.  ⛔ E' il difetto B-3, rifatto da
 *     un'altra parte. */
static bool coda_vuota(const wt *w)
{
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto && !w->coda[i].consegnato)
			return false;
	return true;
}

/* ⛔ Quanti elementi hanno ANCORA DA PARTIRE — e serve alle due righe di
 *    registro che raccontano una chiusura che non matura.  ⚠ `ncoda - testa`,
 *    che e' quel che scrivevano prima, da oggi conterebbe anche i consegnati:
 *    manderebbe a cercare un arretrato che non c'e' proprio nel punto in cui
 *    qualcuno sta cercando perche' la capsula non parte. */
static size_t coda_da_spedire(const wt *w)
{
	size_t n = 0;
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto && !w->coda[i].consegnato)
			n++;
	return n;
}

/* ⛔ Quanti byte di QUESTO stream non sono ancora usciti.  ⚠ Zero non vuol dire
 *    «e' arrivato»: vuol dire «non e' piu' roba nostra» — l'abbiamo consegnato
 *    a ngtcp2.  La differenza si dichiara qui perche' §5.1 la usa: un
 *    fotogramma che non ha piu' byte in coda non si abbandona, perche'
 *    l'abbandono non risparmierebbe piu' niente. */
static size_t coda_byte_stream(const wt *w, int64_t id)
{
	size_t n = 0;
	for (size_t i = w->testa; i < w->ncoda; i++)
		if (!w->coda[i].morto && w->coda[i].id == id)
			n += w->coda[i].dati.n - w->coda[i].off;
	return n;
}

/* ⛔⭐ FASE 9 — I BYTE DI VIDEO CHE DEVONO ANCORA PARTIRE, e sono la meta'
 *     «avevo da mandare» della grandezza della linea morta.
 *
 *     E' la stessa somma che fanno `video_sgombra()` e `ritmo_frena()`, con due
 *     differenze dichiarate: qui entrano anche le CHIAVI (una chiave ferma in
 *     coda e' roba da mandare quanto un delta — §5.2 vieta di abbandonarla, non
 *     di contarla), e non si conta nessun `arretrato`, perche' qui la domanda
 *     non e' «quanti fotogrammi» ma «c'e' qualcosa».
 *
 * ⚠ Zero NON vuol dire «e' arrivato»: vuol dire «non e' piu' roba nostra».
 *   E' esattamente il significato che serve — se non abbiamo piu' niente in
 *   casa, non c'e' niente che il filo ci stia trattenendo. */
static size_t coda_byte_video(const wt *w)
{
	size_t n = 0;
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo)
			n += coda_byte_stream(w, w->involo[i].stream);
	return n;
}

/* ⛔ §5.1: i byte non ancora spediti **non partono affatto**.  Si chiama solo
 *    accanto a un `RESET_STREAM`: buttare i byte senza azzerare lo stream
 *    lascerebbe il client ad aspettare una fine che non arriva.
 *
 * ⛔⭐ FASE 9 — ED E' ANCHE IL POSTO IN CUI SI LIBERANO I CONSEGNATI, il che
 *     rende quella regola piu' stretta di prima, non meno: azzerare lo stream
 *     e' quel che **toglie a ngtcp2 il diritto di rileggerli** — dopo un
 *     `RESET_STREAM` i frame di quello stream non tornano in coda di
 *     ritrasmissione — ed e' l'altra meta' del contratto di `writev_stream`.
 *     ⚠ `video_sgombra()` questa disciplina ce l'aveva gia' («PRIMA si azzera
 *       lo stream, POI si buttano i byte»), ed e' la riga che dimostra che la
 *       regola era conosciuta: mancava dove i byte se ne andavano per fine
 *       spedizione.  ⛔ Chiamare questa funzione senza un `shutdown_stream_write`
 *       (o una chiusura gia' avvenuta) accanto rifa' il difetto del 23 agosto. */
static size_t coda_butta_stream(wt *w, int64_t id)
{
	size_t buttati = 0;
	for (size_t i = w->testa; i < w->ncoda; i++) {
		if (w->coda[i].morto || w->coda[i].id != id)
			continue;
		buttati += w->coda[i].dati.n - w->coda[i].off;
		coda_uccidi(w, i);
	}
	return buttati;
}

static bool stream_bloccato(const wt *w, int64_t id)
{
	for (size_t i = 0; i < w->nbloccati; i++)
		if (w->bloccati[i] == id)
			return true;
	return false;
}

/* ⛔ Il primo elemento eleggibile in ORDINE DI INSERIMENTO, saltando gli stream
 *    gia' bloccati in questa passata.  ⚠ Scorrere in ordine e' quel che tiene
 *    l'ordine DENTRO ogni stream: il primo elemento di uno stream non bloccato
 *    e' per costruzione il suo piu' vecchio. */
static uscita *coda_scegli(wt *w, size_t *fuori)
{
	for (size_t i = w->testa; i < w->ncoda; i++) {
		/* ⛔ FASE 9: si saltano anche i CONSEGNATI.  Sono ancora in coda
		 *    perche' i loro byte servono a ngtcp2 per ritrasmettere, ma non
		 *    hanno piu' niente da offrire: sceglierli vorrebbe dire proporre un
		 *    vettore di lunghezza zero a ogni passata, e con `MORE` acceso
		 *    quella e' una passata che non finisce. */
		if (w->coda[i].morto || w->coda[i].consegnato)
			continue;
		if (stream_bloccato(w, w->coda[i].id))
			continue;
		if (fuori)
			*fuori = i;
		return &w->coda[i];
	}
	return NULL;
}

/* ⛔ IL TETTO DELLA CODA D'USCITA — rilievo B-3 punto 4, 10 agosto 2026 notte.
 *
 * `coda_metti()` e `bytes_aggiungi()` raddoppiavano senza limite: la memoria
 * del processo cresceva quanto il client voleva, e cresceva **su una sessione
 * gia' dichiarata morta**.  ⚠ Un tetto che non c'e' non e' un tetto alto: e'
 * un limitatore assente, e non lo vede nessuno finche' la macchina non finisce
 * la memoria.
 *
 * ⭐ Il numero: due messaggi RCP al massimo (§6.1, 1 MiB l'uno) piu' un po' di
 *    margine.  Il canale di controllo di questa fase manda `ECCOMI`,
 *    `AMMESSO`/`RESPINTO`, `SESSIONE` e `CONGEDO`, che stanno tutti in
 *    qualche centinaio di byte: se questo tetto viene toccato, e' successo
 *    qualcosa che va guardato — e infatti si scrive.  ⛔ E chi lo tocca NON
 *    prosegue in silenzio: vedi `accoda()` e il rilievo B-15.
 *
 * ⛔⭐ E IL 12 AGOSTO 2026 IL NUMERO E' CAMBIATO, con la fase 2 — da 2 MiB a
 *     17.  La ragione non e' «serviva piu' spazio»:
 *
 *     `RCP.md` §6.2 dichiara **legale** un fotogramma fino a **16 MiB**, e
 *     `rcp_video_apri()` rifiuta esattamente sopra quel numero.  ⛔ Con la coda
 *     a 2 MiB un fotogramma perfettamente legale da 3 MiB sarebbe stato
 *     rifiutato **dal nostro limitatore** invece che dal tetto del protocollo:
 *     due tetti diversi per la stessa grandezza, e quello che morde per primo
 *     non e' quello scritto nell'arbitro.
 *
 *     ⚠ E il sintomo sarebbe stato una **degradazione silenziosa** — il
 *       fotogramma non parte, il client vede un buco e chiede una chiave, la
 *       chiave e' ancora piu' grossa: la spirale di §5.2, provocata da una
 *       costante di questo file.  E' l'invariante **I1** letta da
 *       `REVIEWER.md` §3.
 *
 *     ⭐ 16 MiB (il fotogramma piu' grande che §6.2 ammette) + 1 MiB per i
 *        messaggi del canale di controllo, che stanno in qualche centinaio di
 *        byte l'uno.  ⚠ Il prezzo si dichiara: su 16 sessioni il peggio
 *        teorico e' 272 MiB, ed e' il prezzo che §6.2 ha gia' scelto — non uno
 *        nuovo. */
#define WT_CODA_MAX (17u * 1024u * 1024u)

static bool coda_metti(wt *w, int64_t id, const uint8_t *d, size_t n, bool fin)
{
	uscita *u;
	if (w->byte_in_coda + n > WT_CODA_MAX) {
		registro_dice(REG_WT,
		              "⛔ la coda d'uscita ha toccato il tetto (%zu byte in "
		              "coda + %zu, tetto %u): non accodo",
		              w->byte_in_coda, n, WT_CODA_MAX);
		return false;
	}
	if (w->ncoda == w->capcoda) {
		if (w->testa > 0) {
			memmove(w->coda, w->coda + w->testa,
			        (w->ncoda - w->testa) * sizeof *w->coda);
			w->ncoda -= w->testa;
			w->testa = 0;
		}
		if (w->ncoda == w->capcoda) {
			size_t c = w->capcoda ? w->capcoda * 2 : 8;
			uscita *nu = realloc(w->coda, c * sizeof *nu);
			if (!nu)
				return false;
			w->coda = nu;
			w->capcoda = c;
		}
	}
	u = &w->coda[w->ncoda++];
	memset(u, 0, sizeof *u);
	u->id = id;
	u->fin = fin;
	if (!bytes_aggiungi(&u->dati, d, n)) {
		w->ncoda--;
		return false;
	}
	w->byte_in_coda += n;
	return true;
}

/* ⛔⭐ E I BYTE NON SI BUTTANO: QUESTO E' UN CANALE AFFIDABILE — rilievo B-15,
 *     10 agosto 2026 notte.
 *
 *     Questa funzione scriveva una riga nel registro e **proseguiva**.  Il
 *     chiamante — `manda_controllo()`, cioe' la strada di TUTTI i messaggi RCP
 *     — non riceveva nessun esito: RCP credeva di aver mandato `ECCOMI`,
 *     passava a `attesa-credenziali`, e il messaggio successivo si sarebbe
 *     saldato al nulla lasciato dal primo.  ⛔ Il client avrebbe letto
 *     un'inquadratura che il server non ha mai voluto scrivere: sarebbe stato
 *     il SERVER a fabbricare la violazione del client.
 *
 *     ⚠ E' la stessa lezione del riquadro di `STREAM_DATA_BLOCKED` piu' sotto,
 *       applicata all'altra delle due strade per cui i byte si possono
 *       perdere.  La cura di allora era stata messa su una sola.
 *
 * ⭐ La cura: chi non riesce ad accodare NON prosegue.  Si dichiara guasto lo
 *    strato, e `wt_scrivi()` fa morire la connessione QUIC alla prima passata.
 *    ⛔ Una connessione che muore e' inequivocabile; un messaggio saldato a
 *    meta' manda a cercare il difetto nel client.  ⚠ Il motivo di §3.1 non
 *    puo' viaggiare: se la coda non prende sei byte non prende nemmeno la
 *    capsula, e questa riga di registro e' l'unico posto in cui il fatto
 *    compare.  Si scrive perche' e' l'unico. */
static bool accoda(wt *w, int64_t id, const uint8_t *d, size_t n)
{
	if (coda_metti(w, id, d, n, false))
		return true;
	registro_dice(REG_WT,
	              "⛔⛔ %zu byte per lo stream %ld NON entrano in coda: la "
	              "sessione NON prosegue.  Un canale affidabile non butta i "
	              "byte, e mezzo messaggio sul filo sarebbe una violazione "
	              "fabbricata dal server (§6.1)",
	              n, (long)id);
	w->guasto = true;
	return false;
}

/* ------------------------------------------------------------------------ */

static void batti_fra(wt *w, uint64_t ms)
{
	w->battito_ms = ms;
	w->battito = ngtcp2_conn_get_timestamp(w->conn) + ms * NGTCP2_MILLISECONDS;
}

ngtcp2_tstamp wt_battito_ns(const wt *w)
{
	ngtcp2_tstamp b = w->battito_ms ? w->battito : UINT64_MAX;

	/* ⛔⭐ E IL TONO DI PROVA HA UN OROLOGIO SUO — `[M]` 17 agosto 2026.
	 *
	 *     Primo giro contro il cliente di prova: **9 blocchi in 3 secondi**,
	 *     dove il PCM a 5 ms ne vuole 600.  ⚠ Il contenuto era giusto (960 byte,
	 *     codec 2, zero scarti): sbagliato era il RITMO, perche' i blocchi li
	 *     genera `wt_batti()` e `wt_batti()` si sveglia col battito di QUIC —
	 *     che e' lungo centinaia di millisecondi.
	 *
	 * ⭐ La cura NON e' alzare il tetto per passata: quello produrrebbe una
	 *    raffica seguita da un silenzio, cioe' lo stesso numero di blocchi con
	 *    un difetto in piu'.  E' dire al ciclo QUANDO il prossimo blocco e'
	 *    dovuto.
	 *
	 * ⚠ E muore con la sorgente di prova: l'audio vero lo ritma **PipeWire**,
	 *   che nel `poll` ci sta con un descrittore suo e sveglia il ciclo da se'.
	 */
	/* ⛔⛔ LE CONDIZIONI SONO LE STESSE DI `tono_passo()`, ED E' UNA CURA —
	 *      rilievo 4 della revisione avversariale del 17 agosto 2026.
	 *
	 *      Qui c'era `audio_prova_hz && w->audio_acceso`, e li' ci sono anche
	 *      `w->chiusura < 0` e `w->rcp`.  ⛔ **In ogni caso coperto da una
	 *      guardia e non dall'altra questa funzione tornava un istante NEL
	 *      PASSATO e nessuno lo spostava piu'** — perche' a spostarlo e' solo
	 *      `tono_passo`, che invece usciva subito.
	 *
	 *      ⇒ `trasporto_attesa_ms()` leggeva «gia' scaduto», `poll()` tornava
	 *      con **timeout 0**, `wt_batti()` non cambiava niente, e si
	 *      ricominciava: **ciclo stretto al 100 % di CPU**.
	 *
	 * ⚠ E il caso non e' di laboratorio: un BROWSER chiude la sessione
	 *   WebTransport e **tiene viva la connessione QUIC** — e' scritto in
	 *   questo stesso file — e li' `w->rcp` diventa NULL mentre `audio_acceso`
	 *   resta acceso, perche' nessuna riga lo spegne.  ⛔ Il server avrebbe
	 *   girato a vuoto fino al tetto d'inattivita' di QUIC, e piu' a lungo se
	 *   il browser lo teneva vivo con dei PING.
	 *
	 * ⭐ E la lezione e' che due guardie per lo stesso fatto divergono: chi
	 *    tocchera' `tono_passo` deve toccare anche questa. */
	/* ⛔⛔ E UN DATAGRAM IN CODA VUOLE ESSERE RIPROVATO SUBITO — `[M]` 17 agosto
	 *      2026, dalla sessione VERA dell'utente: *«fa schifo come prima»*.
	 *
	 *      Con la congestione a posto (`cwnd_left` 40 KB) il **22 %** dei
	 *      blocchi non partiva lo stesso.  ⛔ La ragione non era il rifiuto: era
	 *      che **nessuno programmava un secondo tentativo**.  Un blocco
	 *      rifiutato restava in coda finche' qualcos'altro non faceva scrivere
	 *      la connessione — cioe' l'arrivo del blocco DOPO, 20 ms piu' tardi.
	 *      ⇒ Il ritentativo c'era, il suo orologio no.
	 *
	 * ⚠ Un millisecondo, non di piu': e' l'ordine di grandezza in cui il pacer
	 *   cambia idea, ed e' 1/20 di un blocco di Opus.  ⛔ E il tetto ai
	 *   risvegli lo pone la coda: quando e' vuota questa riga non scatta.
	 *
	 * ⭐ Ed e' la stessa cura che il tono di prova aveva gia' — scritta li' e
	 *    non qui, perche' allora l'audio vero non esisteva.  Il difetto era
	 *    dentro quella asimmetria. */
	if (w->ndgram > 0 && w->chiusura < 0) {
		ngtcp2_tstamp t = ngtcp2_conn_get_timestamp(w->conn) + NGTCP2_MILLISECONDS;
		if (t < b)
			b = t;
	}

	if (audio_prova_hz && w->audio_acceso && w->chiusura < 0 && w->rcp) {
		/* ⛔ Il primo blocco e' DOVUTO SUBITO.  `[M]` 17 agosto 2026: senza
		 *    questa riga il tono aspettava il battito normale prima di
		 *    partire, e mancava **esattamente un secondo** in testa a ogni
		 *    presa — 2,01 s su 3, 4,01 su 5, 9,01 su 10.  ⚠ Il sintomo
		 *    sembrava una resa (67 %, 80 %, 90 %), e una resa fa cercare il
		 *    difetto nel RITMO; era invece un ritardo d'avvio, che sta in un
		 *    posto completamente diverso. */
		if (!w->tono_prossimo_us)
			return 0;
		ngtcp2_tstamp t = w->tono_prossimo_us * NGTCP2_MICROSECONDS;
		if (t < b)
			b = t;
	}
	return b;
}

const char *wt_stato_rcp(const wt *w)
{
	return w->rcp ? rcp_stato_nome(w->rcp) : "(nessuna)";
}

/* ⛔ PERCHE' ha ancora da dire — e non e' un lusso: senza questa riga
 *    «la capsula di chiusura non e' ancora matura» e «i byte non escono» hanno
 *    la stessa faccia, e chi spegne il servizio legge «1 sessioni hanno ancora
 *    byte in coda» senza sapere quale delle due sia.
 * ⚠ `[M]` 11 agosto 2026: il caso `server-in-chiusura` di B7 e' rosso proprio
 *   qui — §3.1 punto 3 assente allo spegnimento — e la diagnosi si e' fermata
 *   davanti a questa ambiguita'. */
const char *wt_perche_ha_da_dire(const wt *w)
{
	if (!w)
		return "(nessuna sessione)";
	if (w->chiusura >= 0 && !coda_vuota(w))
		return "capsula di chiusura in attesa E coda non vuota";
	if (w->chiusura >= 0) {
		/* ⛔ E QUANTO MANCA, o la diagnosi si ferma qui — 11 agosto 2026.
		 *    «Non ancora matura» dopo 2 s, quando ne bastano 0,5, ha due
		 *    spiegazioni opposte: l'orologio non gira, oppure gira e viene
		 *    RIAZZERATO.  Il numero le separa; l'aggettivo no. */
		static char detto[220];
		ngtcp2_tstamp ora = ngtcp2_conn_get_timestamp(w->conn);
		snprintf(detto, sizeof detto,
		         "capsula di chiusura non ancora matura (coda vuota) — "
		         "chiusura=%#04x · chiusura_da=%s · mancano %lld ms · "
		         "battito fra %lld ms",
		         (unsigned)w->chiusura,
		         w->chiusura_da ? "armato" : "⛔ MAI ARMATO",
		         w->chiusura_da
		             ? (long long)(((long long)w->chiusura_da - (long long)ora)
		                           / (long long)NGTCP2_MILLISECONDS) : 0LL,
		         w->battito_ms
		             ? (long long)(((long long)w->battito - (long long)ora)
		                           / (long long)NGTCP2_MILLISECONDS) : -1LL);
		return detto;
	}
	if (!coda_vuota(w))
		return "coda d'uscita non vuota";
	return "niente";
}

bool wt_ha_da_dire(const wt *w)
{
	/* ⛔ E i datagram contano: senza questa riga i blocchi dell'audio
	 *    resterebbero in coda fino alla prossima cosa da spedire, cioe' il
	 *    suono uscirebbe **a scatti dettati dal video**.  ⚠ E' la stessa forma
	 *    del difetto di `MOVIMENTO_ATTESA_S` (`CODER.md` §1-bis): il ritmo di
	 *    un anello che diventa il ritardo di un altro anello. */
	return w->chiusura >= 0 || !coda_vuota(w) || w->ndgram > 0;
}

/* ------------------------------------------------------------------------ */
/* ⭐ I DATAGRAM — l'audio di §6.3.                                          */

/* ⭐ L'intero a lunghezza variabile per il prefisso di RFC 9297 e' quello che
 *    c'e' gia' — `varint_scrivi()`, in cima a questo file.  ⛔ Ne era stata
 *    scritta una seconda copia qui, ed e' stato il compilatore ad accorgersene:
 *    due implementazioni della stessa regola divergono, ed e' la forma del
 *    difetto che il controllo delle tre copie (R12.3) esiste per impedire fra
 *    file — non c'e' ragione di ammetterla dentro lo stesso file. */

/* Quanti byte accetta il pari in un DATAGRAM, `0` = non ne accetta affatto. */
static uint64_t dgram_tetto_del_pari(const wt *w)
{
	const ngtcp2_transport_params *p;
	if (!w->conn)
		return 0;
	p = ngtcp2_conn_get_remote_transport_params(w->conn);
	return p ? p->max_datagram_frame_size : 0;
}

/*
 * Accoda un carico gia' composto (prefisso RFC 9297 compreso).
 *
 * ⛔ Quando la coda e' piena si butta IL PIU' VECCHIO — §6.3 e la lezione di
 *    v1.  ⚠ E si conta: «l'audio non arriva» e «l'audio arriva e lo butto»
 *    devono avere due righe diverse, che e' esattamente la ragione per cui
 *    `trasporto.c` scriveva lo scarto in ingresso fin dalla fase 1.
 */
static bool dgram_accoda(wt *w, const uint8_t *d, size_t n)
{
	size_t coda;

	if (n > WT_DGRAM_BYTE) {
		/* ⛔ E SI CONTA E SI SCRIVE, invece di tornare `false` e sperare che
		 *    il chiamante guardi — rilievo 13 della revisione del 17 agosto
		 *    2026.  Oggi questa strada e' irraggiungibile perche' `audio_a_una`
		 *    controlla lo stesso tetto tre righe prima: ⚠ **due controlli per
		 *    una regola sola, e solo uno dei due sapeva dire di essere
		 *    scattato**.  Il giorno in cui arriva il secondo chiamante — e con
		 *    `figlio.c` sta arrivando — un blocco sparirebbe senza traccia. */
		w->audio_buttati++;
		registro_dice(REG_WT,
		              "⛔ %s: blocco d'audio di %zu byte oltre il tetto di %u — "
		              "BUTTATO.  ⚠ Se questa riga compare, il tetto e' stato "
		              "controllato in due posti e uno dei due sbaglia",
		              w->provenienza, n, (unsigned)WT_DGRAM_BYTE);
		return false;
	}

	if (w->ndgram == WT_DGRAM_MAX) {
		w->dgram_testa = (w->dgram_testa + 1) % WT_DGRAM_MAX;
		w->ndgram--;
		w->audio_buttati++;
	}
	coda = (w->dgram_testa + w->ndgram) % WT_DGRAM_MAX;
	memcpy(w->dgram[coda].d, d, n);
	w->dgram[coda].n = n;
	w->ndgram++;
	return true;
}

static void dgram_togli_testa(wt *w)
{
	if (w->ndgram == 0)
		return;
	w->dgram_testa = (w->dgram_testa + 1) % WT_DGRAM_MAX;
	w->ndgram--;
}

/*
 * Scrive UN datagram in un pacchetto suo.
 *
 * ⛔ Uno per pacchetto, e non e' pigrizia: `RCP.md` §6.3 dice «un datagram, un
 *    blocco di Opus», quindi il pacchetto non ha niente da coalizzare che
 *    valga il rischio.  ⚠ Mescolare `writev_datagram` e `writev_stream` nello
 *    stesso pacchetto pretende la disciplina del flag `MORE` su tutt'e due, e
 *    un errore li' non produce un guasto: produce byte validi nell'ordine
 *    sbagliato.
 *
 * Torna `true` quando il pacchetto e' stato composto e va spedito.
 */
static bool dgram_scrivi_uno(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi,
                             uint8_t *dest, size_t destlen, ngtcp2_tstamp ts,
                             ngtcp2_ssize *nfuori)
{
	int accettato = 0;
	ngtcp2_vec v;
	ngtcp2_ssize nw;

	if (w->ndgram == 0)
		return false;

	/* ⛔⭐ E NON SI RIPROVA DENTRO LA STESSA PASSATA — `[M]` 17 agosto 2026.
	 *
	 *     `ngtcp2_conn_write_aggregate_pkt2` richiama questa funzione piu'
	 *     volte per comporre un lotto di pacchetti, **con lo stesso `ts`**.  Il
	 *     primo tetto sui rimandi si consumava tutto li' dentro, in un
	 *     microsecondo: otto rimandi e poi il blocco buttato, senza che fosse
	 *     passato **un istante** in cui il pacer potesse cambiare idea.
	 *     ⇒ 1064 datagram buttati lo stesso, con 8008 rimandi «riusciti» in un
	 *     conto che sembrava dire il contrario.
	 *
	 * ⭐ Il pacer decide sul TEMPO: se ha rifiutato a questo `ts`, rifiutera'
	 *    anche adesso.  Si torna subito, senza chiedere — e il rimando vale
	 *    per una passata intera, che e' l'unita' in cui il pacer si muove. */
	if (w->dgram_rimando_ts == ts)
		return false;

	/* ⭐ FASE 9 — E QUI IL DIFETTO DEL 23 AGOSTO NON C'E', per due ragioni che
	 *    vanno scritte perche' non si perdano:
	 *
	 *      1. `w->dgram[]` e' un anello di array FISSI dentro `wt`: non c'e'
	 *         nessun `free()` che possa arrivare prima di ngtcp2 — la memoria
	 *         muore con la sessione;
	 *      2. §6.3: un datagram NON SI RITRASMETTE.  ngtcp2 lo serializza
	 *         dentro il pacchetto durante QUESTA chiamata (`WRITE_MORE` vuol
	 *         dire «e' gia' dentro») e non rilegge piu' la sorgente.
	 *
	 * ⚠ La casella si riusa (`dgram_accoda()` scavalca la piu' vecchia quando
	 *   l'anello e' pieno), e regge solo per il punto 2: il giorno in cui i
	 *   datagram diventassero ritrasmissibili, questo sarebbe lo stesso difetto
	 *   di `coda_uccidi()` con un'altra faccia. */
	v.base = w->dgram[w->dgram_testa].d;
	v.len = w->dgram[w->dgram_testa].n;

	/* ⛔⛔ `MORE` E NON `NONE`, ED E' LA CURA DEL DIFETTO CHE L'UTENTE HA SENTITO.
	 *
	 *      `[M]` 17 agosto 2026, sessione VERA dell'utente da un'altra macchina:
	 *      **1578 blocchi spediti e 1606 RIFIUTATI** — piu' della meta'
	 *      dell'audio non partiva — e la riga di diagnosi diceva la causa senza
	 *      lasciare margini: **`cwnd_left = 0`**.
	 *
	 *      ⇒ Non era la rete e non era il pacer: era **il video che si mangia
	 *      tutta la finestra di congestione**.  Un datagram da 230 byte non
	 *      trovava posto perche' chiedeva **un pacchetto suo**, e un pacchetto
	 *      suo la finestra non lo concedeva mai.
	 *
	 * ⭐ Con `MORE` il datagram non chiede un pacchetto: **entra in quello che il
	 *    video sta gia' scrivendo**.  Un pacchetto da 1452 byte che porta pixel
	 *    ha spazio da vendere per 230 byte di suono, e quel pacchetto la
	 *    finestra lo sta gia' concedendo.  ⇒ L'audio viaggia dove passa il video
	 *    invece di contendergli il posto.
	 *
	 * ⛔⛔⛔ E `PADDING` NON E' UN DETTAGLIO: E' LA CURA — l'intuizione e' dell'utente
	 *       («forse il datagram e' troppo piccolo?»), e il manuale di ngtcp2 le
	 *       da' ragione in una riga:
	 *
	 *         «This function only writes multiple packets if **the first packet
	 *          is path_max_tx_udp_payload_size bytes long**.»
	 *         «Because GSO requires that the aggregated packets have the same
	 *          length, NGTCP2_WRITE_DATAGRAM_FLAG_PADDING is recommended.»
	 *
	 *       Il nostro datagram e' il **primo** pacchetto di ogni passata, ed e'
	 *       da ~250 byte invece che pieno.  ⇒ **Fa collassare l'intero lotto GSO
	 *       a un pacchetto solo**: non e' l'audio che non entra, e' l'audio che
	 *       — piccolo e primo — **strozza tutta la scrittura, sua e del video**.
	 *
	 * ⚠ `[M]` 17 agosto 2026, sessione vera dell'utente: `cwnd_left` 33-56 KB
	 *   liberi, `quanto del pacer` 14440 costante, e **839 blocchi rifiutati su
	 *   2278**.  Ne' congestione ne' buffer: era la geometria del lotto.
	 *
	 * ⭐ Con `MORE` il pacchetto lo riempie il video; con `PADDING` viene
	 *    riempito comunque quando il video non ha niente da metterci.  Le due
	 *    insieme: l'audio non paga il riempimento quando c'e' traffico, e non
	 *    strozza il lotto quando non ce n'e'.
	 *
	 * ⛔ `NGTCP2_ERR_WRITE_MORE` qui non e' un errore: vuol dire «il datagram e'
	 *    dentro, continua a riempire il pacchetto».  Chi lo leggesse come un
	 *    guasto butterebbe un blocco gia' spedito. */
	nw = ngtcp2_conn_writev_datagram(w->conn, path, pi, dest, destlen, &accettato,
	                                 NGTCP2_WRITE_DATAGRAM_FLAG_MORE |
	                                     NGTCP2_WRITE_DATAGRAM_FLAG_PADDING,
	                                 ++w->dgram_id, &v, 1, ts);
	if (nw == NGTCP2_ERR_WRITE_MORE) {
		/* ⭐ Il blocco e' nel pacchetto in composizione: si toglie dalla coda. */
		w->audio_spediti++;
		w->dgram_rimandi = 0;
		dgram_togli_testa(w);

		/* ⛔⛔⛔ E SI CONTINUA A INFILARNE, finche' ce ne stanno — `[M]` 17
		 *       agosto 2026, dalla sessione dell'utente con un video vero:
		 *       il figlio produce **50 blocchi al secondo** e il server ne
		 *       rifiuta **25 al secondo**.  ⚠ Esattamente la meta', e la
		 *       precisione di quel numero e' l'indizio: non e' congestione,
		 *       e' **aritmetica**.
		 *
		 *       Spedivo **un solo datagram per passata di scrittura**, e le
		 *       passate sono ~25 al secondo.  ⇒ Uno passava e uno restava in
		 *       coda, per sempre, finche' non lo buttavo dopo 64 rinvii.
		 *       ⛔ Il tetto non era ne' la rete ne' il pacer: era **il mio
		 *       ciclo**, che ne offriva uno per volta.
		 *
		 * ⚠ E lo spazio c'era da vendere: un pacchetto e' **1452 byte** e un
		 *   blocco di Opus ne misura **230**.  Ce ne stanno sei, e i fotogrammi
		 *   video di questa scena sono da 70-1300 byte — cioe' il pacchetto
		 *   restava mezzo vuoto mentre l'audio veniva buttato. */
		while (w->ndgram > 0) {
			ngtcp2_vec v2;
			int acc2 = 0;
			ngtcp2_ssize nw2;

			v2.base = w->dgram[w->dgram_testa].d;
			v2.len = w->dgram[w->dgram_testa].n;
			nw2 = ngtcp2_conn_writev_datagram(
				w->conn, path, pi, dest, destlen, &acc2,
				NGTCP2_WRITE_DATAGRAM_FLAG_MORE |
					NGTCP2_WRITE_DATAGRAM_FLAG_PADDING,
				++w->dgram_id, &v2, 1, ts);
			if (nw2 == NGTCP2_ERR_WRITE_MORE) {
				w->audio_spediti++;
				dgram_togli_testa(w);
				continue; /* ce n'e' ancora posto: si prosegue */
			}
			if (nw2 > 0) {
				/* Il pacchetto si e' chiuso.  ⛔ Se ha preso anche questo
				 *    blocco lo si toglie; in ogni caso il pacchetto VA
				 *    SPEDITO — buttarlo porterebbe via i riscontri. */
				if (acc2) {
					w->audio_spediti++;
					dgram_togli_testa(w);
				}
				*nfuori = nw2;
				return true;
			}
			break; /* `0` o un errore: si riprova alla passata dopo */
		}
		return false;
	}
	if (nw < 0) {
		/* ⛔ E QUI NON SI UCCIDE LA CONNESSIONE.  §6.3 e' esplicito nel verso
		 *    opposto — «chiudere la connessione per un pacchetto corrotto
		 *    sarebbe una punizione della rete, non del mittente» — e la stessa
		 *    ragione vale in uscita: un blocco d'audio che non parte non e' un
		 *    motivo per togliere il desktop a chi lo sta usando. */
		registro_dice(REG_WT,
		              "⛔ %s: datagram di %zu byte NON scritto (%s) — il blocco "
		              "si BUTTA (§6.3: nessuna ritrasmissione).  Spediti %llu, "
		              "buttati %llu",
		              w->provenienza, v.len, ngtcp2_strerror((int)nw),
		              (unsigned long long)w->audio_spediti,
		              (unsigned long long)(w->audio_buttati + 1));
		w->audio_buttati++;
		dgram_togli_testa(w);
		return false;
	}

	if (accettato) {
		w->audio_spediti++;
		w->dgram_rimandi = 0;
		dgram_togli_testa(w);
	} else if (w->dgram_rimandi < WT_DGRAM_RIMANDI_MAX) {
		/* ⛔⛔ NON SI BUTTA: SI RIMANDA — e la differenza vale il 38 % dell'audio.
		 *
		 *      `[M]` 17 agosto 2026, audio VERO in PCM con il video acceso:
		 *      **1163 datagram rifiutati su 3001**, e il giudice leggeva
		 *      **464 Hz invece di 440** con purezza 0,29 — perche' concatenare
		 *      quel che resta fa saltare la fase ogni due blocchi.  ⚠ Il suono
		 *      non era «con qualche buco»: era **un altro suono**.
		 *
		 * ⛔⭐ E LA CAUSA NON ERA QUELLA SCRITTA QUI.  Il commento diceva «nel
		 *     pacchetto non ci stava, quindi non ci starebbe mai».  La misura
		 *     dice il contrario: `cwnd_left` = **12 198 byte** contro 973
		 *     chiesti, destlen 1452.  ⇒ Non e' ne' il buffer ne' la
		 *     congestione: e' il **pacer** di QUIC, che dice «non adesso».
		 *     E «non adesso» diventa «mai» solo se lo buttiamo noi.
		 *
		 * ⚠ E il tetto resta: la coda tiene otto blocchi, e chi non ci sta si
		 *   butta comunque (§6.3).  Rimandare non e' accumulare — sposta il
		 *   blocco di qualche centinaio di microsecondi, non di mezzo secondo. */
		w->dgram_rimandi++;
		w->audio_rimandati++;
		w->dgram_rimando_ts = ts;
		/* ⛔⛔⛔ E NON SI TORNA SUBITO: SE UN PACCHETTO C'E', VA SPEDITO.
		 *
		 *       `[M]` 17 agosto 2026, e questo era il difetto che teneva in
		 *       piedi tutti gli altri.  Il manuale di ngtcp2 lo dice e io
		 *       l'avevo letto male:
		 *
		 *         «The function returns the written length of packet … because
		 *          packet is nearly full and the library decided to make a
		 *          complete packet.  **|*paccepted| might be zero or nonzero**.»
		 *
		 *       ⇒ `nw > 0` con `accettato == 0` vuol dire: **il datagram non e'
		 *       entrato, MA UN PACCHETTO COMPLETO E' STATO SCRITTO** — con
		 *       dentro i riscontri e i byte del video.  ⛔ Tornando `false` qui
		 *       quel pacchetto veniva **buttato**: la passata proseguiva e
		 *       riscriveva `dest` da capo.
		 *
		 * ⛔⛔ Il prezzo non era l'audio: erano **i RISCONTRI**.  Buttare un
		 *      pacchetto su cinque che porta ACK fa sbagliare a QUIC la misura
		 *      del percorso — e da li' vengono il pacer che non apre, la
		 *      finestra che non cresce e il ritmo a singhiozzo.  ⚠ Cioe' il
		 *      difetto **fabbricava** i sintomi che stavo inseguendo. */
	} else {
		/* ⚠ Qui il rimando non si puo' piu' fare: o la congestione e' vera
		 *   (`cwnd_left` sotto la misura del blocco), o si e' gia' rimandato
		 *   troppe volte e il blocco e' vecchio.  ⛔ Allora si butta davvero,
		 *   ed e' quel che §6.3 vuole: il suono in ritardo non serve. */
		w->audio_rifiutati++;
		/* ⛔ `registro_dice` e non `registro_dettaglio`: il secondo e'
		 *    SOPPRESSO quando la parlantina e' spenta, cioe' in ogni
		 *    installazione normale — e allora «l'audio buttato» e «l'audio mai
		 *    arrivato» tornano ad avere la stessa faccia, che e' esattamente
		 *    quel che i due contatori esistono per impedire (rilievo 6).
		 * ⚠ Con un fondo: una riga ogni 100 scarti, o un guasto continuo
		 *   riempirebbe il registro invece di raccontarlo. */
		if (w->audio_rifiutati == 1 || w->audio_rifiutati % 100 == 0)
			/* ⛔⭐ E LA CAUSA SI CHIEDE, invece di elencarne tre.
			 *
			 *     ngtcp2 da' `0` per tre motivi diversi — controllo di
			 *     congestione, spazio nel buffer, limite di amplificazione — e
			 *     la prima stesura di questa riga li elencava tutti e tre,
			 *     cioe' non ne nominava nessuno (rilievo 10 della revisione).
			 *     ⚠ `LEZIONI.md` §1.9: una deduzione scritta accanto a un
			 *     numero che nessuno ha misurato.
			 *
			 * ⭐ `cwnd_left` la separa: se e' **zero** e' la congestione, e
			 *    allora buttare e' la cosa sbagliata da fare — quel blocco
			 *    entrerebbe fra qualche centinaio di microsecondi.  Se e'
			 *    **grande**, la causa e' un'altra e va cercata altrove. */
			registro_dice(REG_WT,
			              "⚠ %s: datagram di %zu byte NON messo nel pacchetto "
			              "(destlen %zu) — buttato (§6.3).  Rifiutati %llu.  "
			              "⛔ cwnd_left = %llu byte, quanto del pacer = %zu%s",
			              w->provenienza, v.len, destlen,
			              (unsigned long long)w->audio_rifiutati,
			              (unsigned long long)ngtcp2_conn_get_cwnd_left(w->conn),
			              ngtcp2_conn_get_send_quantum(w->conn),
			              ngtcp2_conn_get_cwnd_left(w->conn) < v.len
			                  ? " ⇒ E' LA CONGESTIONE: il blocco non ci sta ADESSO"
			                  : " ⇒ NON e' la congestione: guarda il quanto");
		dgram_togli_testa(w);
	}

	if (nw > 0) {
		*nfuori = nw;
		return true;
	}
	return false;
}

/* ------------------------------------------------------------------------ */
/* 1. La riscrittura del SETTINGS.                                           */

static size_t riscrivi_impostazioni(wt *w, const nghttp3_vec *vec, size_t veccnt)
{
	uint8_t orig[512];
	size_t origlen = 0;
	uint64_t tipo_stream = 0, tipo_frame = 0, lung = 0;
	size_t n, p, o;
	uint8_t aggiunta[64], testa[16];
	size_t a = 0, t = 0;

	for (size_t i = 0; i < veccnt; i++) {
		if (origlen + vec[i].len > sizeof orig) {
			registro_dice(REG_WT,
			              "⛔ il SETTINGS di nghttp3 e' piu' lungo di "
			              "%zu byte: non lo riscrivo",
			              sizeof orig);
			return 0;
		}
		memcpy(orig + origlen, vec[i].base, vec[i].len);
		origlen += vec[i].len;
	}
	if (origlen < 3)
		return 0;

	/* ⛔ Ogni passo ha un appiglio, e se l'appiglio non c'e' NON si riscrive
	 *    alla cieca: si dice e si lascia stare.  Il server restera' senza
	 *    WebTransport, e la misura lo vedra' subito — che e' quel che
	 *    `DECISIONI.md` §6.4 chiede di riprovare a ogni aggiornamento di
	 *    nghttp3. */
	n = varint_leggi(&tipo_stream, orig, origlen);
	if (n == 0 || tipo_stream != 0x00) {
		registro_dice(REG_WT,
		              "⛔ lo stream di controllo non comincia per 0x00 (e' "
		              "%llu): non tocco niente",
		              (unsigned long long)tipo_stream);
		return 0;
	}
	p = n;

	n = varint_leggi(&tipo_frame, orig + p, origlen - p);
	if (n == 0 || tipo_frame != 0x04) {
		registro_dice(REG_WT, "⛔ il primo frame non e' SETTINGS (e' %llu)",
		              (unsigned long long)tipo_frame);
		return 0;
	}
	p += n;

	n = varint_leggi(&lung, orig + p, origlen - p);
	if (n == 0)
		return 0;
	p += n;

	if (p + lung != origlen) {
		/* C'e' altro dopo SETTINGS, oppure SETTINGS e' arrivato a pezzi. */
		registro_dice(REG_WT, "⛔ SETTINGS non e' tutto qui (%zu + %llu != %zu)",
		              p, (unsigned long long)lung, origlen);
		return 0;
	}

	a += varint_scrivi(aggiunta + a, WT_ENABLE_WEBTRANSPORT);
	a += varint_scrivi(aggiunta + a, 1);
	a += varint_scrivi(aggiunta + a, WT_MAX_SESSIONS);
	a += varint_scrivi(aggiunta + a, 1);

	t += varint_scrivi(testa + t, 0x00); /* il tipo dello stream */
	t += varint_scrivi(testa + t, 0x04); /* SETTINGS */
	t += varint_scrivi(testa + t, lung + a);

	if (t + lung + a > sizeof w->impbuf) {
		registro_dice(REG_WT, "⛔ SETTINGS troppo grande per il buffer");
		return 0;
	}

	o = 0;
	memcpy(w->impbuf + o, testa, t);
	o += t;
	memcpy(w->impbuf + o, orig + p, (size_t)lung);
	o += (size_t)lung;
	memcpy(w->impbuf + o, aggiunta, a);
	o += a;
	w->impbuf_len = o;

	registro_dice(REG_WT,
	              "⭐ SETTINGS riscritto — %zu byte di nghttp3 + %zu nostri "
	              "(ENABLE_WEBTRANSPORT e WT_MAX_SESSIONS)",
	              origlen, a);
	return origlen;
}

/* ------------------------------------------------------------------------ */
/* RCP: i quattro ganci, che sono l'unica cosa che il protocollo sa del mondo */
/* di sotto.                                                                  */

static void manda_controllo(wt *w, const uint8_t *dati, size_t len);
static void chiudi_sessione(wt *w, uint8_t motivo);

static void gancio_manda(void *ctx, const uint8_t *dati, size_t len)
{
	manda_controllo((wt *)ctx, dati, len);
}

static void gancio_chiudi(void *ctx, uint8_t motivo)
{
	chiudi_sessione((wt *)ctx, motivo);
}

static void gancio_registra(void *ctx, const char *riga)
{
	(void)ctx;
	registro_dice(REG_RCP, "%s", riga);
}

/* ⛔⭐ QUESTO GANCIO E' IL RIPIEGO, DAL 12 AGOSTO 2026 — `DECISIONI.md` §1.10.
 *
 *     ⚠ PAM BLOCCA, e qui bloccava il ciclo intero: la stretta di mano di un
 *       utente fermava quella di tutti gli altri e ritardava i pacchetti di
 *       chiunque fosse gia' collegato.  `[M]` B8, 11 agosto 2026: **da 1,0 a
 *       2,2 secondi**, e a metterceli era PAM (+1034 ms sui respinti contro
 *       +84 ms sugli ammessi — la firma di `pam_faildelay`).
 *
 * ⛔ Adesso la strada buona e' `gancio_chiedi`, qui sotto.  Questa resta
 *    collegata perche' `rcp.c` la usa quando l'aiutante non c'e' — e allora e'
 *    giusto che il server funzioni lo stesso, con meno (`CODER.md` §4.2).
 * ⚠ Ma il ripiego SI DICHIARA: chi lo percorre lo trova scritto nel registro
 *   da `rcp.c`, «per via SINCRONA — il filo e' rimasto fermo». */
static bool gancio_verifica(void *ctx, const char *utente, const char *parola)
{
	(void)ctx;
	return rcp_autentica(utente, parola);
}

/* ⭐⭐ LA STRADA BUONA: si chiede, non si aspetta — `DECISIONI.md` §1.10.
 *
 * ⛔ Restituisce `false` quando la domanda non e' partita, e `rcp.c` lo tratta
 *    come un NO immediato: invariante I3, il fallimento e' un no e non un
 *    forse. */
static bool gancio_chiedi(void *ctx, const char *utente, const char *parola,
                          uint64_t *pratica)
{
	wt *w = (wt *)ctx;
	if (!w->aiuto)
		return false;
	return aiutante_chiedi(w->aiuto, utente, parola,
	                       ngtcp2_conn_get_timestamp(w->conn)
	                           / NGTCP2_MILLISECONDS,
	                       pratica);
}

/* ========================================================================== */
/* ⭐⭐ I QUATTRO GANCI DEL CANALE VIDEO — `RCP.md` §2.5, §5.1, §6.2.          */
/*                                                                            */
/* Innestati il 12 agosto 2026 dal montaggio della fase 2.  Le righe le aveva */
/* scritte `fasi/rapporti/P2-4-filo.md` §5, e ⛔ **non stanno in `main.c`**:   */
/* `main.c` non conosce `rcp_ganci`, la struttura la riempie `rcp_avvia()` qui */
/* dentro — la correzione al mandato che P2.4 ha messo a verbale.             */
/*                                                                            */
/* ⛔ SONO QUATTRO E NON UNO perche' §6.2 dice che **come lo stream finisce e' */
/*    parte del messaggio**: FIN ⇒ fotogramma completo, `RESET_STREAM` ⇒       */
/*    incompleto, si butta.  Un gancio solo che «manda un fotogramma» non      */
/*    saprebbe dire la differenza (forma E8, rilievo R1.7).                    */
/*                                                                            */
/* ⛔⭐ E IL PREAMBOLO DI WEBTRANSPORT NON E' UN DETTAGLIO — proposta P18.     */
/*                                                                            */
/*     Uno stream unidirezionale di WebTransport comincia con il **tipo dello  */
/*     stream** (`0x54`) seguito dal **numero della sessione**, tutt'e due     */
/*     interi variabili di QUIC (RFC 9000 §16): sul filo `0x54` sono i due     */
/*     byte `40 54`.  I 28 byte di §6.2 cominciano DOPO.                       */
/*                                                                            */
/*     ⚠ §2.5 dice «si leggono i primi due byte dello stream, che sono in ogni */
/*       caso un campo `tipo`» — e su WebTransport non e' vero.  Un lettore che */
/*       lo applicasse alla lettera ricaverebbe il canale `0x40` da OGNI       */
/*       fotogramma e chiuderebbe con `ERRORE_PROTOCOLLO`.  ⛔ Il primo giro   */
/*       dal vivo di `02-filo-cliente.py` e' finito rosso esattamente li'.     */
/*                                                                            */
/*     ⭐ Questo file lo sapeva gia' per gli stream IN ARRIVO (`smista_uni`,   */
/*        riga ~1164): qui c'e' l'altra meta', ed e' lo stesso `varint_scrivi` */
/*        — non una copia dei due byte a mano, che il giorno in cui il numero  */
/*        di sessione supera 63 diventerebbe muta e sbagliata.                 */

/* ⭐⭐ I SEI GANCI DELL'INPUT — FASE 4, 14 agosto 2026.
 *
 * ⛔ PERCHE' SONO GANCI E NON CHIAMATE DIRETTE, e non e' stile: `rcp.c` vive in
 *    DUE cartelle che il `Makefile` (`GEMELLATI`) pretende identiche byte per
 *    byte, e la seconda copia `banchi/01-b3-rcp-innesta.py` la infila dentro
 *    `examples/` di ngtcp2, dove `input.h` **non esiste**.  Un `#include` la'
 *    dentro spegnerebbe B3, B5, B6, B8 e B11 in un colpo solo.
 *
 * ⛔ E PERCHE' PASSANO DI QUI E NON VANNO DRITTI AL PALCO: il palco e' in un
 *    ALTRO PROCESSO (`figlio.c`), che gira come l'utente ed e' l'unico ad avere
 *    la sessione grafica.  Questi sei portano il messaggio fino al ponte di
 *    `main.c`, che e' l'unico che conosce tutt'e due i lati.
 *
 * ⚠ E il valore di ritorno e' quello di `input.h`, TRE stati: 0 consegnato,
 *   -1 no, 1 «non producibile» (solo la lettera).  ⛔ Qui pero' il terzo non
 *   si puo' distinguere — l'iniezione avviene oltre il confine di processo, e
 *   la risposta non torna indietro.  ⇒ **Si risponde 0 = «consegnato al
 *   palco»**, e chi conta davvero quel che il compositore ha PRESO e' il
 *   figlio, che lo timbra sul fotogramma (§6.2).  Questa asimmetria e'
 *   dichiarata e non nascosta: e' il prezzo del confine di processo. */
static wt_input_richiesta gancio_palco_input;
static void *gancio_palco_input_ctx;

void wt_input_gancio(wt_input_richiesta f, void *ctx)
{
	gancio_palco_input = f;
	gancio_palco_input_ctx = ctx;
}

static int input_al_palco(wt *w, uint32_t id, uint8_t azione, uint16_t codice,
                          int premuto, int32_t a, int32_t b)
{
	const char *mio;
	if (!gancio_palco_input || !w->rcp)
		return -1;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return -1;
	return gancio_palco_input(gancio_palco_input_ctx, mio, id, azione, codice,
	                          premuto, a, b)
	           ? 0
	           : -1;
}

static int gancio_input_puntatore(void *ctx, uint32_t x, uint32_t y)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_PUNTATORE,
	                      0, 0, (int32_t)x, (int32_t)y);
}

static int gancio_input_pulsante(void *ctx, uint16_t codice, int premuto)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_PULSANTE,
	                      codice, premuto, 0, 0);
}

static int gancio_input_rotella(void *ctx, int32_t asse_x, int32_t asse_y)
{
	wt *w = (wt *)ctx;
	/* ⛔ Il segno NON si tocca qui, e i mezzi scatti passano interi: `RCP.md`
	 *    §7.3 mette l'inversione dentro `input_rotella()`, una volta sola.
	 *    Invertirlo anche qui lo annullerebbe. */
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_ROTELLA, 0,
	                      0, asse_x, asse_y);
}

static int gancio_input_lettera(void *ctx, uint32_t carattere)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_LETTERA, 0,
	                      0, (int32_t)carattere, 0);
}

static int gancio_input_posizione(void *ctx, uint16_t codice, int premuto)
{
	wt *w = (wt *)ctx;
	return input_al_palco(w, rcp_input_ultimo_id(w->rcp), FIGLI_INPUT_POSIZIONE,
	                      codice, premuto, 0, 0);
}

static int gancio_input_rilascia_tutto(void *ctx)
{
	wt *w = (wt *)ctx;
	/* ⛔⭐ «La regola col rapporto danno/costo piu' alto del documento»
	 *     (`RCP.md` §11).  ⚠ E il conto di quanti ne ha rilasciati resta al
	 *     FIGLIO: qui non torna indietro.
	 *
	 * ⛔⛔ E fino al 16 agosto 2026 qui si rispondeva `0` intendendo «la
	 *      richiesta e' partita» — ma il chiamante lo scriveva nel registro
	 *      come «0 erano premuti», che e' la faccia del verde su un rilascio
	 *      mai avvenuto.  ⇒ Adesso si risponde `SENZA_CONTO`, che e' la
	 *      verita': «fatto, e il numero chiedilo a chi lo sa». */
	return input_al_palco(w, 0, FIGLI_INPUT_RILASCIA_TUTTO, 0, 0, 0, 0) == 0
	           ? RCP_RILASCIO_SENZA_CONTO
	           : RCP_RILASCIO_IMPOSSIBILE;
}

/* ⭐⭐ IL GANCIO DELLA TELA — §7.1, e la catena intera in una riga:
 *
 *     `rcp.c` (T_ADATTA_TELA) → questo → `main.c` → `figli_ritela()` →
 *     `MSG_INPUT/RITELA` → `cattura_ridimensiona()` → `pw_stream_update_params()`
 *
 * ⛔ E la risposta NON torna da qui: torna con un fotogramma alla misura nuova,
 *    che `video_a_una()` riporta a `rcp_tela_concessa()`.  ⚠ Chi leggesse questo
 *    `true` come «la tela e' cambiata» rifarebbe l'errore che `wayvnc` fa con
 *    l'esito della richiesta (`DECISIONI.md` §5.0-sexies, «la regola di forma
 *    rubata a neatvnc»). */
static wt_ritela_richiesta gancio_palco_ritela;
static void *gancio_palco_ritela_ctx;

void wt_ritela_gancio(wt_ritela_richiesta f, void *ctx)
{
	gancio_palco_ritela = f;
	gancio_palco_ritela_ctx = ctx;
}

static wt_disposizione_richiesta gancio_palco_disposizione;
static void *gancio_palco_disposizione_ctx;

void wt_disposizione_gancio(wt_disposizione_richiesta f, void *ctx)
{
	gancio_palco_disposizione = f;
	gancio_palco_disposizione_ctx = ctx;
}

/* ⭐⭐ §5-bis.7 — «metti questa disposizione», e va al palco di CHI HA
 *     CHIESTO.  ⛔ Invariante I3, identica alla ritela: il nome dell'utente
 *     e' quello che PAM ha ammesso su QUESTA sessione, mai un parametro che
 *     viene dal filo.  Un utente che potesse cambiare la tastiera di un
 *     altro sarebbe un difetto piccolo con una faccia grossa — il desktop
 *     dell'altro che smette di rispondere alle scorciatoie. */
static bool gancio_disposizione(void *ctx, const char *nome)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_disposizione || !w->rcp)
		return false;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_disposizione(gancio_palco_disposizione_ctx, mio, nome);
}

/* ⭐⭐ «QUESTA MACCHINA CONOSCE QUESTA DISPOSIZIONE?» — e la risposta la da'
 *     **XKB**, non un elenco scritto a mano.
 *
 * ⛔ Il difetto che chiude, `[M]` banco `06-b34` caso 5, 16 agosto 2026:
 *    `hu`, `tr`, `gr` e `ua` esistono in `/usr/share/X11/xkb/symbols/` su
 *    questa macchina e venivano rifiutate con `SESSIONE_NON_SERVIBILE`,
 *    con la riga «disposizione sconosciuta a questa macchina» — una frase
 *    FALSA.  ⇒ Un utente ungherese non entrava.
 *
 * ⭐ E la domanda si gira a `tastiera.c`, che e' gia' l'unico posto del
 *    prodotto che sa compilare una disposizione: chiedere due volte la
 *    stessa cosa in due modi diversi produce due risposte sotto la stessa
 *    etichetta (forma E2).  ⚠ Copre anche la VARIANTE — `it(nonesiste)`
 *    non compila — che l'elenco fisso non guardava affatto. */
static int gancio_disposizione_esiste(void *ctx, const char *nome)
{
	Tastiera *t;
	char *sbaglio = NULL;

	(void)ctx;
	if (!nome || !*nome)
		return 0;
	t = tastiera_apri(nome, &sbaglio);
	if (!t) {
		free(sbaglio);
		return 0;
	}
	tastiera_chiudi(t);
	return 1;
}

static bool gancio_ritela(void *ctx, uint32_t larghezza, uint32_t altezza)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_ritela || !w->rcp)
		return false;
	/* ⛔ Invariante I3: la tela si cambia al palco di CHI HA CHIESTO, e il nome
	 *    e' quello che PAM ha ammesso su questa sessione — non un parametro che
	 *    viene dal filo.  Un utente che potesse ridimensionare il monitor di un
	 *    altro sarebbe un difetto piccolo con una faccia grossa: il desktop
	 *    dell'altro che cambia misura da solo. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_ritela(gancio_palco_ritela_ctx, mio, larghezza, altezza);
}

/* ⭐⭐ §5.1 — «QUEST'UTENTE HA GIA' UNA SESSIONE GRAFICA LOCALE?»
 *
 * ⛔ Il gancio verso `sentinella.c`, e vive qui per la stessa ragione degli
 *    altri: `rcp.c` esiste in due copie e quella innestata in ngtcp2 non ha un
 *    bus di sistema.  Chi non lo collega non applica la regola, e `rcp.c` lo
 *    scrive nel registro invece di tacere. */
static wt_locale_richiesta gancio_locale;
static void *gancio_locale_ctx;

void wt_locale_gancio(wt_locale_richiesta f, void *ctx)
{
	gancio_locale = f;
	gancio_locale_ctx = ctx;
}

static bool gancio_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	(void)ctx;
	if (!gancio_locale)
		return false;
	return gancio_locale(gancio_locale_ctx, utente, quale, quanto);
}

/* ⭐⭐ §7.6 — «l'utente ha chiesto di uscire». */
static wt_termina_richiesta gancio_termina;
static void *gancio_termina_ctx;

void wt_termina_gancio(wt_termina_richiesta f, void *ctx)
{
	gancio_termina = f;
	gancio_termina_ctx = ctx;
}

static void gancio_termina_sessione(void *ctx)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_termina || !w->rcp)
		return;
	/* ⛔ Invariante I3: si termina la sessione di CHI HA CHIESTO, e il nome e'
	 *    quello che PAM ha ammesso su questa sessione — non un parametro che
	 *    viene dal filo.  Un utente che potesse chiudere la sessione di un
	 *    altro sarebbe il difetto piu' caro del documento. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return;
	gancio_termina(gancio_termina_ctx, mio);
}

static bool gancio_video_apri(void *ctx, int64_t *stream, uint64_t *restano)
{
	wt *w = (wt *)ctx;
	uint8_t pre[16];
	size_t n = 0;
	int64_t id = -1;

	if (restano)
		*restano = 0;
	if (!w->conn || w->sessione == -1 || w->guasto)
		return false;
	if (restano)
		*restano = ngtcp2_conn_get_streams_uni_left2(w->conn);

	/* ⚠ `false` qui vuol dire «non adesso», e `rcp.c` lo traduce in «non e'
	 *   partito un byte» — che e' meglio di mezzo fotogramma.  ⛔ La ragione
	 *   piu' probabile e' che il client non conceda altri stream
	 *   unidirezionali, e allora si dice quanti gliene restano invece di
	 *   scrivere «non si e' potuto». */
	if (ngtcp2_conn_open_uni_stream(w->conn, &id, NULL) != 0) {
		registro_dettaglio(REG_WT,
		              "nessuno stream unidirezionale per il fotogramma: il "
		              "client ne concede ancora %llu (§2.5 ne vuole uno PER "
		              "fotogramma).  ⚠ La riga che decide — delta si butta, "
		              "chiave si aspetta — la scrive `rcp.c` (§2.3)",
		              (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
			              w->conn));
		return false;
	}

	/* ⛔ Quanto credito ngtcp2 CREDE di avere, chiesto a lui e non dedotto
	 *    (`LEZIONI.md` §1.6).  ⚠ Serve a distinguere «il pari non ci ha dato
	 *    credito» da «ce l'ha dato e uno dei due conta male»: il 13 agosto 2026
	 *    un cliente che dichiarava `initial_max_streams_uni = 6` ha chiuso con
	 *    `STREAM_LIMIT_ERROR` dopo che avevamo aperto 11 stream, e senza questa
	 *    riga di chi fosse il conto sbagliato si poteva solo indovinare. */
	registro_dettaglio(REG_WT,
	                   "stream uni %ld aperto per un fotogramma; ngtcp2 dice che "
	                   "ne restano %llu",
	                   (long)id,
	                   (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
		                   w->conn));

	n += varint_scrivi(pre + n, 0x54);
	n += varint_scrivi(pre + n, (uint64_t)w->sessione);

	if (!coda_metti(w, id, pre, n, false)) {
		/* ⛔ Lo stream e' stato aperto e il preambolo non c'e': si AZZERA
		 *    invece di lasciarlo aperto e muto.  Uno stream unidirezionale
		 *    aperto e mai scritto tiene un posto nel conto del client e non
		 *    diventa mai un fotogramma: e' la forma «vuoto e proibito hanno la
		 *    stessa faccia», dal lato di chi aspetta. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, id, 0);
		registro_dice(REG_WT,
		              "⛔ il preambolo di WebTransport (%zu byte) non entra in "
		              "coda: stream %ld azzerato, nessun fotogramma",
		              n, (long)id);
		return false;
	}
	*stream = id;
	/* ⛔ Qui e in nessun altro posto: `rcp.c` non restituisce l'identificatore
	 *    dello stream che ha aperto, e ricavarlo da «l'ultimo aperto sulla
	 *    connessione» sarebbe indovinare.  ⭐ Senza questo, §5.1 non ha nessun
	 *    modo di dire QUALE stream azzerare quando ne parte uno piu' recente. */
	w->video_stream_ultimo = id;
	return true;
}

static bool gancio_video_scrivi(void *ctx, int64_t stream, const uint8_t *dati,
                                size_t len)
{
	/* ⛔ `false` = «non sono entrati», e chi chiama AZZERA: `rcp.c` non chiude
	 *    mai con FIN uno stream a cui manca un pezzo, perche' FIN e'
	 *    un'affermazione (§6.2). */
	return coda_metti((wt *)ctx, stream, dati, len, false);
}

static void gancio_video_fin(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	/* ⛔ Il FIN e' un elemento della coda come gli altri, e NON si scrive
	 *    subito: deve uscire DOPO i byte che lo precedono, e la coda e' quel
	 *    che tiene l'ordine.  ⚠ Un `shutdown_stream_write` qui chiuderebbe lo
	 *    stream mentre i suoi byte sono ancora in coda — cioe' consegnerebbe
	 *    un fotogramma troncato marcato «completo». */
	if (!coda_metti(w, stream, NULL, 0, true))
		registro_dice(REG_WT,
		              "⛔ il FIN dello stream %ld non entra in coda: il "
		              "fotogramma e' uscito ma non e' dichiarato completo",
		              (long)stream);
}

static void gancio_video_azzera(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	if (!w->conn)
		return;
	/* ⛔ §5.1/§6.2: `RESET_STREAM` ⇒ il client BUTTA quel che e' arrivato e lo
	 *    tratta come un buco. */
	ngtcp2_conn_shutdown_stream_write(w->conn, 0, stream, 0);
	/* ⛔⭐ E I BYTE ANCORA IN CODA SI BUTTANO QUI, NON «alla prossima passata».
	 *
	 *     Il commento di prima diceva che li avrebbe scartati `wt_scrivi()` sul
	 *     ramo `NGTCP2_ERR_STREAM_SHUT_WR`, e con un fotogramma solo per
	 *     sessione era vero e bastava.  ⛔ A sessanta al secondo no: quei byte
	 *     restano contati in `byte_in_coda` fino alla passata dopo, cioe' il
	 *     tetto della coda morde su roba che si e' gia' deciso di non spedire —
	 *     e §5.1 dice **«i byte non ancora spediti non partono affatto»**, non
	 *     «partono dopo».  ⚠ Il conto non si sfasa: `coda_butta_stream()` passa
	 *     da `coda_uccidi()`, che e' l'unico punto in cui `byte_in_coda` cala. */
	coda_butta_stream(w, stream);
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ FASE 7 — I TRE GANCI DEL CANALE APPUNTI VERSO IL CLIENT (§2.5, §7.4).  */
/*                                                                            */
/* ⛔⭐ E NON SONO I `video_*` RIUSATI, benche' aprano lo stesso genere di      */
/*     stream: `gancio_video_apri()` RICORDA quale stream ha aperto            */
/*     (`video_stream_ultimo`), perche' §5.1 gli fa azzerare **il precedente** */
/*     quando ne parte uno piu' recente.  Un trasferimento di appunti che      */
/*     passasse di li' diventerebbe «il fotogramma precedente» del prossimo    */
/*     fotogramma — ⛔ cioe' verrebbe azzerato a meta' da una regola che non lo */
/*     riguarda, e il sintomo sarebbe «gli appunti arrivano tagliati quando il */
/*     desktop si muove».                                                      */

static bool gancio_appunti_apri(void *ctx, int64_t *stream, uint64_t *restano)
{
	wt *w = (wt *)ctx;
	uint8_t pre[16];
	size_t n = 0;
	int64_t id = -1;

	if (restano)
		*restano = 0;
	if (!w->conn || w->sessione == -1 || w->guasto)
		return false;
	if (restano)
		*restano = ngtcp2_conn_get_streams_uni_left2(w->conn);

	if (ngtcp2_conn_open_uni_stream(w->conn, &id, NULL) != 0) {
		registro_dettaglio(REG_WT,
		                   "nessuno stream unidirezionale per gli appunti: il "
		                   "client ne concede ancora %llu (§2.5 ne vuole uno per "
		                   "trasferimento)",
		                   (unsigned long long)ngtcp2_conn_get_streams_uni_left2(
			                   w->conn));
		return false;
	}

	n += varint_scrivi(pre + n, 0x54);
	n += varint_scrivi(pre + n, (uint64_t)w->sessione);

	if (!coda_metti(w, id, pre, n, false)) {
		/* ⛔ Stesso trattamento del video: uno stream aperto e muto tiene un
		 *    posto nel conto del client e non diventa mai un messaggio. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, id, 0);
		registro_dice(REG_WT,
		              "⛔ il preambolo di WebTransport (%zu byte) non entra in "
		              "coda: stream %ld azzerato, nessun trasferimento di appunti",
		              n, (long)id);
		return false;
	}
	*stream = id;
	return true;
}

static bool gancio_appunti_scrivi(void *ctx, int64_t stream, const uint8_t *dati,
                                  size_t len)
{
	return coda_metti((wt *)ctx, stream, dati, len, false);
}

static void gancio_appunti_fin(void *ctx, int64_t stream)
{
	wt *w = (wt *)ctx;
	/* ⛔ Il FIN e' un elemento della coda come gli altri, e NON si scrive
	 *    subito: deve uscire DOPO i byte che lo precedono. */
	if (!coda_metti(w, stream, NULL, 0, true))
		registro_dice(REG_WT,
		              "⛔ il FIN dello stream %ld degli appunti non entra in "
		              "coda: il messaggio e' uscito e lo stream resta aperto",
		              (long)stream);
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ E I DUE GANCI VERSO LA SESSIONE — «offri» e «rispondi».                */
/*                                                                            */
/* ⛔ Passano da `main.c` come quelli dell'input, e per la stessa ragione:     */
/*    `webtransport.c` conosce il filo e non conosce i figli, e chi cuce i due */
/*    mondi e' l'unico che conosce tutt'e due i lati.                         */

static wt_appunti_offerta gancio_palco_appunti_offri;
static wt_appunti_consegna gancio_palco_appunti_risposta;
static void *gancio_palco_appunti_ctx;

void wt_appunti_gancio(wt_appunti_offerta offri, wt_appunti_consegna risposta,
                       void *ctx)
{
	gancio_palco_appunti_offri = offri;
	gancio_palco_appunti_risposta = risposta;
	gancio_palco_appunti_ctx = ctx;
}

static bool gancio_appunti_offri(void *ctx)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_appunti_offri || !w->rcp)
		return false;
	/* ⛔ Invariante I3: si offre alla sessione DI CHI HA CHIESTO, e il nome e'
	 *    quello che PAM ha ammesso su questa connessione — non un parametro che
	 *    viene dal filo.  Un utente che potesse mettere del testo negli appunti
	 *    di un altro sarebbe una via di comunicazione fra sessioni che nessuno
	 *    ha chiesto. */
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_appunti_offri(gancio_palco_appunti_ctx, mio);
}

static bool gancio_appunti_risposta(void *ctx, uint32_t serial,
                                    const char *testo, size_t byte)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!gancio_palco_appunti_risposta || !w->rcp)
		return false;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return gancio_palco_appunti_risposta(gancio_palco_appunti_ctx, mio, serial,
	                                     testo, byte);
}


/* ⛔⭐ I PING DEL TRASPORTO MENTRE SI ASPETTANO LE CREDENZIALI — `RCP.md` §4.6,
 *     riquadro R1.8, che e' normativo e comincia con un ⛔.  Rilievo B-2, curato
 *     il 10 agosto 2026 notte.
 *
 * ⛔ IL DIFETTO, per esteso, perche' e' il documento a descriverlo parola per
 *    parola.  §4.6 da' 60 secondi fra `ECCOMI` spedito e `CREDENZIALI`
 *    ricevute — «e' il tempo in cui una persona digita la parola d'ordine».  In
 *    quei 60 secondi sul filo NON PASSA NIENTE: §2.2 vieta il battito
 *    applicativo, e prima dell'attacco non c'e' nessun altro canale attivo.  Al
 *    trentesimo secondo matura l'inattivita' di QUIC (`IDLE_MS`), la
 *    connessione muore IN SILENZIO — nessun `CONGEDO`, nessun codice, nessun
 *    motivo di §8.2 — e `TETTO_CREDENZIALI` non scade mai, perche' la sessione
 *    RCP e' gia' stata liberata trenta secondi prima.
 *
 *    ⚠ Chi ci cade: chi digita piano, cioe' chi digita su un telefono.  Difetto
 *      intermittente, il peggiore da diagnosticare — e il banco misurerebbe 30
 *      dove il documento dice 60, dando la colpa al banco.
 *
 * ⛔ E `wt_battito_ns()` NON E' LA CURA, ed e' il punto: fa scorrere l'orologio
 *    NOSTRO ogni 100 ms e per i tetti di §4.6 va benissimo, ⛔ ma non mette un
 *    byte sul filo — e l'orologio che uccide la connessione e' quello di QUIC,
 *    che guarda i byte.  Il riquadro di `webtransport.h` presentava l'assenza
 *    del keep-alive come un miglioramento sull'innesto citando §2.2: §4.6
 *    distingue esplicitamente le due cose — i PING del trasporto «non portano
 *    informazione, non hanno una risposta da interpretare, e non creano una
 *    seconda verita' sul silenzio» — e il divieto di §2.2 NON li copre.
 *
 * ⭐ 10 secondi, e non 25: il PING deve avere il tempo di essere ritrasmesso
 *    almeno una volta prima che i 30 maturino.  Un keep-alive tarato al pelo
 *    del tetto e' un keep-alive che il primo pacchetto perso rende inutile.
 *
 * ⚠ E un client MORTO muore lo stesso: RFC 9000 §10.1 rimette in moto il
 *   cronometro dell'inattivita' quando si RICEVE un pacchetto, non quando lo si
 *   manda.  I nostri PING tengono viva una connessione con qualcuno che
 *   risponde, non una con nessuno.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔⭐ E DAL 16 AGOSTO 2026 RESTANO ACCESI PER TUTTA LA SESSIONE.  Qui sotto
 *      c'era scritto il contrario, e la ragione era questa:
 *
 *        ~~«Tenere viva la connessione SEMPRE cambierebbe il significato dei 30
 *        secondi di §2.2 — l'orologio del silenzio: scaduto, il client e'
 *        staccato»~~
 *
 *      ⇒ E' caduta in due passi, tutt'e due misurati.
 *
 *   1. ⛔ **La semantica era gia' cambiata**, e non da questi PING: da stamattina
 *      §5.3 conta i PACCHETTI e non i byte di RCP (`rcp.c`, `ultima_vita`),
 *      perche' contando i byte un utente che LEGGEVA perdeva il posto dopo
 *      trenta secondi e un secondo dispositivo glielo portava via.  ⇒ «Il client
 *      c'e'» vuol dire gia' «risponde sul filo».  Questi PING non aggiungono
 *      quella semantica: la rendono **affidabile**.
 *
 *   2. ⛔⛔ **Senza, il margine e' del BROWSER e non nostro.**  `[M]` Con una
 *      sessione ferma, i pacchetti arrivano ogni **15002 · 15005 · 15002 ms** —
 *      quindici secondi esatti, meta' netta del tetto.  Un numero cosi' regolare
 *      non e' traffico: e' il keep-alive di Chrome.  ⚠ Un browser diverso, o
 *      Chrome che cambia quel numero, e i posti ricominciano a cadere sotto il
 *      naso di chi legge.
 *
 * ⚠ E LA PREVISIONE DI `SPECIFICHE.md` §5.3 SULLA SCHEDA CONGELATA NON SI
 *   AVVERA — «una scheda in secondo piano viene congelata dopo circa cinque
 *   minuti, quindi tace, quindi si stacca».  `[M]` 16 agosto, browser vero
 *   dell'utente senza automazione attaccata, scheda in secondo piano per
 *   **undici minuti**: zero stacchi, pacchetti puntuali a 15 s fino all'ultimo.
 *   ⛔ Quella riga e' `[S]`, una previsione sul comportamento dei browser, e la
 *   misura la smentisce.
 *
 * ⚠ IL PREZZO, DICHIARATO: un client la cui PAGINA e' morta ma la cui RETE
 *   risponde tiene il posto.  ⛔ Ma lo teneva gia' — vedi il punto 1 — e chi
 *   torna su quella scheda ritrova la sua sessione, che e' l'invariante I4.  Il
 *   caso che resta scoperto e' il client che smette di rispondere ANCHE sul
 *   filo, e quello si stacca ai trenta secondi come sempre. */
#define WT_TIENILA_VIVA_NS (10ULL * NGTCP2_SECONDS)

/* ========================================================================== */
/* ⛔⭐⭐⭐ FASE 9 — LA LINEA MORTA, e dal 24 ago 2026 nasce ACCESA (decisione */
/*          dell'utente; fino al 23 nasceva spenta per l'invariante I6).      */
/*                                                                            */
/* LA DECISIONE E' DELL'UTENTE, 23 agosto 2026: *«se in 10 secondi non         */
/* arrivano piu' pacchetti e' chiaro che la connessione e' morta [...] se      */
/* all'interno di un intervallo di 1-2 secondi c'e' una perdita di pacchetti   */
/* piuttosto copiosa direi di trattarla come il caso in cui la connessione e'  */
/* caduta»*.  E alla domanda su che cosa veda l'utente quando scatta ha        */
/* scelto: **il filo cade e l'utente rientra a mano**.                        */
/*                                                                            */
/* ⛔ DA DOVE NASCE, e sono due comportamenti brutti tutt'e due — `[M]` 23     */
/*    agosto, stessa macchina, profilo `raffica-forte` (11,10 % INIETTATO in   */
/*    197 raffiche): SENZA le cure della fase l'immagine si congela fino a     */
/*    **14,26 s** (7 secondi su 25 hanno visto un fotogramma); CON le cure si  */
/*    muove ma con **4,5 s di ritardo**.  ⇒ L'utente ha deciso che nessuno dei */
/*    due va servito: una linea cosi' si DICHIARA morta.                      */
/*                                                                            */
/* ⛔⛔⭐⭐ LA GRANDEZZA E' CAMBIATA IL 23 AGOSTO 2026, E LA VECCHIA E' STATA     */
/*       REFUTATA DAL SUO STESSO BANCO.  Si scrive qui per intero, perche'    */
/*       chi legge dopo deve trovare la RAGIONE e non l'assenza.              */
/*                                                                            */
/* ⛔ QUEL CHE C'ERA: `pkt_lost / pkt_sent` dentro una finestra, con soglia a  */
/*    50‰.  ⛔⛔ E ORDINA I DUE CASI AL CONTRARIO — `[M]` 23 agosto 2026,       */
/*    `banchi/09-b81-linea-morta.py`:                                         */
/*                                                                            */
/*      · `casa-cattiva`  — perdita INIETTATA 1,86-2,15 %, perdita DICHIARATA */
/*        da ngtcp2 **512‰** (51,2 %).  E la linea REGGE: dieci minuti, 9,60  */
/*        fotogrammi/s, copertura 1,00, buco massimo 0,50 s, e il cliente e'  */
/*        ancora attaccato a 599,99 s.                                        */
/*      · `raffica-forte` — perdita INIETTATA 12,28-14,00 %, DICHIARATA       */
/*        **123‰** (12,3 %).  E la linea NON regge: copertura 0,20, buco      */
/*        massimo 30,06 s.                                                    */
/*                                                                            */
/*    ⇒ Quella che FUNZIONA dichiara QUATTRO VOLTE piu' perdita di quella     */
/*      che non funziona.  ⛔ Nessun valore le separa: una soglia che lasci    */
/*      passare `casa-cattiva` (≥512‰) lascia passare anche `raffica-forte`;  */
/*      una che fermi `raffica-forte` (≤123‰) ferma prima `casa-cattiva`.     */
/*      Non e' una taratura da rifare: e' la grandezza sbagliata.             */
/*                                                                            */
/* ⭐ LA CAUSA, MISURATA: `casa-cattiva` porta `delay 40ms 20ms distribution   */
/*    normal`, e la sonda ci misura il **93,5 % di pacchetti fuori ordine**   */
/*    con l'1,9 % di perdita vera.  **ngtcp2 conta un pacchetto sorpassato    */
/*    come perso.**  ⇒ Su una linea che RIORDINA, `pkt_lost/pkt_sent` misura  */
/*    il RIORDINO e non la perdita — che e' il fatto centrale di questa       */
/*    fase, e ci e' tornato addosso.  ⚠ E non e' la partenza della            */
/*    connessione: tolte le prime dieci finestre, 399 su 399 restano sopra    */
/*    soglia, mediana 524‰, ininterrotto per dieci minuti.                    */
/*                                                                            */
/* ⭐⭐ E IL NUMERO NON SI BUTTA, CAMBIA MESTIERE: da GIUDICE a TESTIMONE.      */
/*     Resta nella riga dello scatto come `permille=`, ed e' la miglior       */
/*     misura di RIORDINO che il server abbia SUGLI STREAM — dove             */
/*     `dgram_falsi` (§17.3) non arriva, perche' quello vale sui datagram,    */
/*     cioe' sul solo audio.  ⇒ Un `permille=512` accanto a uno `stallo_ms=0` */
/*     non e' un guasto: e' jitter, e adesso la riga lo fa VEDERE invece di   */
/*     deciderlo.                                                             */
/*                                                                            */
/* ⛔⭐⭐⭐ LA GRANDEZZA NUOVA, E I DATI LA INDICANO DA SOLI: **DA QUANTO         */
/*        TEMPO NON ESCE UN FOTOGRAMMA PUR AVENDONE DA MANDARE.**  Quel che   */
/*        separa i due casi non e' quanto si perde, e' se i fotogrammi        */
/*        ESCONO — `casa-cattiva` buco massimo 0,50 s, `raffica-forte`        */
/*        30,06 s: sessanta volte, e nella direzione giusta.                  */
/*                                                                            */
/*   ⛔ E LE DUE META' CONTANO TUTT'E DUE.  «Non esce niente» da solo e'       */
/*      anche la SCENA FERMA, che `[M]` in questa fase e' normale e non       */
/*      costa niente: `RecordVirtual` di Mutter consegna solo sul             */
/*      cambiamento, e il risveglio vale 13 ms.  ⇒ Se non abbiamo niente da   */
/*      mandare non c'e' niente di rotto, e il conto non deve nemmeno         */
/*      PARTIRE.                                                              */
/*                                                                            */
/*   ⭐ COME SI CALCOLA — due contatori LOCALI e MONOTONI, la forma P8→P20     */
/*      di `RCP.md:398` (la stessa di `arretrato`), e non un orologio         */
/*      libero: il tempo entra solo come distanza fra due campionamenti.      */
/*                                                                            */
/*        «e' uscito»   `lm_usciti` — i byte di VIDEO consegnati a ngtcp2     */
/*                      (`coda_consegna()`).  Se sale, il conto RIPARTE.      */
/*        «avevo da     `coda_byte_video() > 0` — byte di fotogrammi ancora   */
/*         mandare»     in casa nostra — OPPURE `lm_offerti` salito, cioe'    */
/*                      il palco ci ha dato un fotogramma.  Se nessuno dei    */
/*                      due, il conto riparte lo stesso: non c'era niente     */
/*                      da mandare, e non c'e' niente di rotto.               */
/*                                                                            */
/*      ⛔ IL SECONDO TERMINE NON E' UN DI PIU': senza `lm_offerti` il         */
/*         REGOLATORE DEL RITMO nasconderebbe lo stallo.  Quello smette di    */
/*         PRODURRE quando la coda non si svuota, `video_sgombra()`           */
/*         abbandona i delta vecchi, e «non ho niente da mandare»             */
/*         diventerebbe vero proprio mentre lo schermo e' fermo.  ⇒ Si        */
/*         conta il fotogramma che il palco ci da', PRIMA di ogni freno,      */
/*         sgombero o rifiuto.                                                */
/*      ⛔ E SI CONTANO I BYTE, non i fotogrammi interi: una chiave da         */
/*         ~60 000 byte su una linea stretta puo' metterci secondi a uscire   */
/*         tutta, e a fotogrammi quei secondi sarebbero uno «stallo» mentre   */
/*         il filo sta lavorando.  Un byte che parte e' un filo che porta.    */
/*                                                                            */
/* ⛔⛔ IL NUMERO, COI DUE MARGINI — `[M]` 23 agosto 2026, stesso banco.        */
/*      ⛔ E i casi INTERMEDI contano quanto gli estremi:                      */
/*                                                                            */
/*        tredici profili sani    buco 0,04-0,35 s     reggono                */
/*        `casa-cattiva`          buco **0,50 s**      REGGE, e non va        */
/*                                                     dichiarata morta       */
/*        `raffica-1` (1,07 %     ⚠ **1,00 s** pieno   regge, e consegna      */
/*         a grappoli)              senza un fotogr.   23,94 fotogrammi/s     */
/*        `raffica-forte`         **30,06 s**, e       NON regge              */
/*                                 14,26 s in un                              */
/*                                 altro giro                                 */
/*                                                                            */
/*     ⚠ `raffica-1` E' IL CASO CHE TIENE ONESTA LA SOGLIA: una linea che     */
/*       consegna 24 fotogrammi al secondo ha comunque avuto **un secondo     */
/*       intero vuoto**.  Una soglia sotto quello butterebbe fuori una        */
/*       sessione perfettamente usabile.                                      */
/*                                                                            */
/*     ⇒ La soglia sta **fra 1,00 s e 14,26 s** — e il lato stretto e' il     */
/*       piu' CORTO dei due stalli di `raffica-forte`, non il piu' lungo, o   */
/*       il margine sarebbe scritto su un numero fortunato.  Il centro        */
/*       geometrico e' 3,78 s (√(1,00·14,26)); ⭐ si sceglie **5,0 s**, e si   */
/*       sceglie SOPRA il centro apposta:                                     */
/*                                                                            */
/*         margine sopra il peggiore che REGGE:   5,00 / 1,00 = **5,0×**      */
/*         margine sotto quello che NON SERVE:   14,26 / 5,00 = **2,9×**      */
/*         (e sopra `casa-cattiva`, che regge con 0,50 s, sono **10×**)       */
/*                                                                            */
/*     ⚠ L'ASIMMETRIA E' VOLUTA e si dichiara — ed e' l'unica cosa che la     */
/*       cura vecchia aveva giusta: i due errori NON costano uguale.          */
/*       Sbagliare in alto vuol dire qualche secondo di schermo fermo in      */
/*       piu' e poi si rientra a mano; sbagliare in basso vuol dire           */
/*       **buttare fuori uno che stava lavorando**, e quello non e'           */
/*       rimediabile.                                                         */
/*                                                                            */
/* ⚠ E IL CAMPIONAMENTO SBAGLIA DALLA PARTE BUONA, che va detto perche' e'    */
/*   un errore vero: il conto riparte dall'ISTANTE DEL GIRO in cui il         */
/*   progresso si e' VISTO, non da quello in cui i byte sono usciti           */
/*   davvero.  Il giro e' al piu' uno al secondo (`rete_ciclo()`), quindi     */
/*   lo `stallo_ms` misurato puo' essere fino a ~1 s PIU' CORTO del vero.     */
/*   ⇒ Si scatta piu' tardi, mai piu' presto — che e' il lato su cui          */
/*   l'asimmetria qui sopra vuole sbagliare.                                  */
/* ========================================================================== */

/* ⛔ I DUE PREDEFINITI — `WT_LM_STALLO_MS` (5 000 ms) e `WT_LM_SILENZIO_S`
 *    (10 s) — stanno in `webtransport.h`, e ce n'e' UNA COPIA SOLA: `main.c` ci
 *    inizializza le sue variabili, cosi' «il predefinito del server» e «il
 *    predefinito del trasporto» non possono diventare due numeri diversi.
 *    ⚠ Lo stallo in MILLISECONDI, come `--sgombra-soglia-ms`: e' un ritardo che
 *      si VEDE, e chi lo tara sceglie quanti secondi di schermo fermo sopporta
 *      prima che il filo cada. */
/* ⚠ `[?]` I tre numeri qui sotto li tara il banco, come `WT_RITMO_POSTI`: la
 *   taratura e' falsificabile — a 20 Mbit/s con `casa-cattiva` acceso per
 *   dieci minuti gli scatti devono essere ZERO, e con `raffica-1` pure. */
#define WT_LM_MIN_PACCHETTI 200u  /* sotto, la finestra del TESTIMONE si allunga*/
#define WT_LM_FINESTRA_MS 1000u   /* la finestra minima: il ritmo di rete_ciclo*/
/* ⛔ Le PROVE del silenzio: quanti pacchetti NOSTRI sono usciti da quando il
 *    client si e' fatto vedere l'ultima volta.  Due, non duecento: a desktop
 *    fermo il traffico e' fatto dai PING del trasporto e basta, e chiedere
 *    duecento pacchetti vorrebbe dire non giudicare mai proprio il caso in cui
 *    il client non risponde piu'. */
#define WT_LM_MIN_PROVE 2u

/* ⛔⭐ L'interruttore e' STATICO e non per sessione: e' una decisione del
 *     server, come `ritmo_adattivo`.  ⭐ Dal 24 agosto 2026 nasce ACCESO
 *     (decisione dell'utente), e il valore lo porta `main.c`, che e' l'unico
 *     posto in cui il predefinito e' scritto; i due numeri nascono coi
 *     predefiniti qui sopra — `main.c` chiama `wt_linea_morta()` SEMPRE, cosi'
 *     la riga d'avvio esce in tutt'e due i casi per costruzione. */
static bool linea_morta_accesa;
static uint64_t linea_morta_stallo_ms = WT_LM_STALLO_MS;
static uint64_t linea_morta_silenzio_ms = WT_LM_SILENZIO_S * 1000ULL;

/* ⛔⛔⭐⭐ QUANTO SPESSO SI CHIEDE AL CLIENT DI FARSI VEDERE — e con la linea
 *       morta accesa NON sono piu' 10 s.  E' la riga che rende ONESTA la regola
 *       dei 10 secondi di silenzio: senza, quella regola e' pericolosa.
 *
 * ⭐ PRIMA DI TUTTO, CHE COSA FA GIA' OGGI, perche' e' la domanda che si fa
 *    chiunque legga «serve un PING a sessione attiva»: ce l'ha gia', dal 16
 *    agosto 2026 (il riquadro qui sopra).  `regola_tienila_viva()` accende il
 *    keep-alive di ngtcp2 in TUTTI gli stati tranne `finita` — non solo mentre
 *    si aspettano le credenziali.  ⇒ `FASI.md` §05 §6-bis e' fatto, e la misura
 *    `[M]` dei **15 004 / 15 005 / 15 002 ms** fra due pacchetti di un browser
 *    fermo e' quel che si vedeva PRIMA: era il keep-alive di Chrome, ed e'
 *    proprio la misura che ha fatto accendere i nostri.  ⚠ Oggi quel numero non
 *    e' piu' 15 s: e' **10**, e sono i nostri.
 *
 * ⛔ MA 10 NON BASTANO PER UNA SOGLIA DI SILENZIO DI 10 s, e il difetto e' lo
 *    stesso di prima con un numero piu' piccolo: un client SANO ma fermo si fa
 *    vedere ogni ~10 s + RTT, perche' prima di allora nessuno gli ha chiesto
 *    niente.  Una soglia a 10 s misurerebbe QUELLO — e butterebbe fuori chi sta
 *    leggendo una pagina, che e' la regressione gia' pagata il 16 agosto («una
 *    seconda scheda e' entrata e ha preso il desktop del primo»).
 *
 * ⇒ Con l'interruttore acceso l'intervallo diventa **META'** della soglia del
 *   silenzio: a soglia 10 s si chiede ogni 5 s, e quando i 10 s scadono ci sono
 *   **due domande senza risposta**, non una che forse era ancora per strada.
 *   ⭐ E' il numero minimo che rende vera la regola: con l'intervallo uguale
 *      alla soglia il giudizio dipenderebbe dall'RTT, cioe' dalla rete che si
 *      sta giudicando.
 *
 * ⚠ E NON E' UN BATTITO APPLICATIVO, che §2.2 vieta: sono PING del TRASPORTO, e
 *   §4.6 distingue le due cose parola per parola — «non portano informazione,
 *   non hanno una risposta da interpretare, e non creano una seconda verita'
 *   sul silenzio».  ⛔ Il confine non e' il periodo, e' la natura: sotto il
 *   secondo diventerebbe un'altra cosa, e li' non si va.
 *
 * ⛔⛔ IL PREZZO CHE QUI ERA SCRITTO — «~26 byte/s, 0,21 kbit/s per sessione» —
 *      DESCRIVEVA UN CASO IN CUI IL PRODOTTO NON ENTRA, e si corregge invece di
 *      lasciarlo: un prezzo dichiarato per un caso che non esiste e' peggio di
 *      nessun prezzo.  `[M]` 23 agosto 2026, banco `09-b81`:
 *
 *      1. ⛔ **Il keep-alive di ngtcp2 manda un PING solo dopo il suo intervallo
 *         SENZA ALTRO TRAFFICO.**  E su una sessione viva il traffico non si
 *         ferma mai: il contatore non sta fermo nemmeno **0,6 s**.  ⇒ Su una
 *         sessione che sta lavorando questi PING **non hanno mai occasione di
 *         scattare**, e il loro costo li' e' **zero**.  I ~26 byte/s sono un
 *         TETTO che si tocca solo a traffico completamente fermo — cioe' dopo
 *         che il client ha smesso di parlare, che e' il caso per cui esistono.
 *      2. ⛔ **E il banco NON HA POTUTO ISOLARLO, e si e' rifiutato di dare un
 *         verde vuoto.**  Una sessione «ferma» costa lo stesso **2 463 kbit/s**
 *         di audio PCM (§4.3, che non si spegne): sono **11 727 volte** i 0,21
 *         kbit/s che questa riga dichiarava.  La differenza misurata fra cura
 *         accesa e cura spenta e' **+0,539 kbit/s** — dentro il rumore, cioe'
 *         un numero che non dimostra niente in nessuna delle due direzioni.
 *
 *   ⇒ Quel che resta vero, e basta a decidere: un PING e' un pacchetto corto
 *     (intestazione corta + un frame PING + i 16 byte del sigillo, `[?]` ~40
 *     byte di carico piu' 28 di IP/UDP) e la risposta e' un riscontro
 *     altrettanto corto.  A traffico fermo e un giro ogni 5 s e' un TETTO di
 *     ~26 byte/s per sessione, contro il pavimento dichiarato di 20 Mbit/s
 *     (`DECISIONI.md` §3.1-bis).  Il costo non e' un argomento; il periodo lo
 *     sceglie la regola, non la banda.
 *
 * ⭐ E VALE ANCHE PER LO SFRATTO DEL FANTASMA (`rcp.c`, `--sfratto-ms`): quello
 *    e' tarato a 15 s perche' sotto i 15 s non si distingueva un client morto da
 *    uno fermo — e i 15 s erano il keep-alive di Chrome.  Con i PING a 5 s
 *    `ultima_vita` di un client vivo non e' mai piu' vecchia di ~5 s + RTT, e lo
 *    sfratto puo' scendere a **~10 s** senza rischiare niente.  ⛔ Ma NON a 3:
 *    per i 3 servirebbe un PING ogni ~1 s, cioe' sedici volte il traffico qui
 *    sopra e un periodo che comincia a somigliare a un battito.  ⚠ E la scelta
 *    non e' di questo file: qui si dichiara il numero che questo file rende
 *    possibile.
 */
static uint64_t tienila_viva_ns(void)
{
	if (linea_morta_accesa && linea_morta_silenzio_ms)
		return (linea_morta_silenzio_ms / 2) * NGTCP2_MILLISECONDS;
	return WT_TIENILA_VIVA_NS;
}

static void regola_tienila_viva(wt *w, const char *stato)
{
	/* ⚠ Il nome dello stato e' il contratto: `rcp.h` li elenca tutti e sette
	 *   per iscritto, e dice che chi li confronta deve saperlo.  ⛔ Qui si
	 *   nomina il solo stato in cui NON servono: dopo la fine non c'e' piu'
	 *   niente da tenere vivo, e insistere sarebbe rumore su una connessione
	 *   che sta chiudendo. */
	bool serve = stato && strcmp(stato, "finita") != 0;

	if (serve == w->tienila_viva)
		return;
	w->tienila_viva = serve;
	ngtcp2_conn_set_keep_alive_timeout(w->conn,
	                                   serve ? tienila_viva_ns() : UINT64_MAX);
	/* ⛔ Due chiamate e non una col `?:` dentro il formato: i due formati hanno
	 *    un numero DIVERSO di argomenti da quando l'intervallo si stampa, e un
	 *    `%llu` che non c'e' e' un difetto che si vede solo al primo stacco. */
	if (serve)
		registro_dice(REG_WT,
		              "⭐ PING del trasporto ACCESI ogni %llu s con %s: il segno "
		              "di vita di §5.3 lo produciamo NOI, non il keep-alive del "
		              "browser (che dava 15 s su 30 di tetto)%s",
		              (unsigned long long)(tienila_viva_ns() / NGTCP2_SECONDS),
		              w->provenienza,
		              linea_morta_accesa && linea_morta_silenzio_ms
		                  ? ".  ⚠ Sono la META' della soglia del silenzio della "
		                    "linea morta: quando scade, le domande senza risposta "
		                    "sono due"
		                  : "");
	else
		registro_dice(REG_WT,
		              "PING del trasporto spenti con %s: la sessione e' finita, "
		              "non c'e' piu' niente da tenere vivo",
		              w->provenienza);
}

static void regola_battito(wt *w)
{
	const char *stato = w->rcp ? rcp_stato_nome(w->rcp) : NULL;

	regola_tienila_viva(w, stato);

	if (!stato) {
		/* Nessuna sessione RCP: si batte se c'e' una chiusura da far
		 * maturare — ⛔ **oppure se il tetto di §7.17 e' armato**.
		 *
		 * ⛔ E' qui che la prima stesura del tetto moriva, `[M]` 11 agosto
		 *    2026 col banco B6: `cb_end_headers` armava `canale_entro` e
		 *    chiamava `batti_fra`, e poi la prima passata di questa funzione
		 *    rimetteva `battito_ms = 0`.  Il tetto scattava solo se il client
		 *    faceva qualcos'altro che risvegliasse il battito — cioe'
		 *    **proprio nel caso che non serve**: `ciao-sessione-tardiva`
		 *    scadeva a 5,10 s, `ciao-senza-controllo` restava appeso 20 s.
		 *
		 * ⚠ E' la lezione scritta trenta righe piu' sotto, presa in flagrante
		 *   nel giro stesso in cui la si applicava: **chi mette un tetto deve
		 *   accendere anche cio' che lo fara' scadere** — e non basta
		 *   accenderlo, bisogna che nessun altro lo spenga. */
		if (w->chiusura >= 0 || w->canale_entro)
			batti_fra(w, 100);
		else
			w->battito_ms = 0;
		return;
	}
	if (strcmp(stato, "attiva") == 0) {
		/* ⭐ L'orologio del silenzio di `SPECIFICHE.md` §5.3 va valutato
		 *    MENTRE il client tace, e mentre tace nessuno percorrerebbe
		 *    il percorso di scrittura.  Un secondo di granularita' su
		 *    trenta e' abbondante. */
		batti_fra(w, 1000);
		return;
	}
	/* ⛔ `attesa-verdetto` vuole il battito perche' il ritardo fisso di
	 *    §4.4-bis dura un secondo e in quel secondo non c'e' niente da
	 *    spedire; gli altri stati della stretta di mano perche' i tre tetti
	 *    di §4.6 devono poter scadere anche se il client tace.
	 *
	 * ⛔⭐ E QUESTA E' LA LEZIONE PIU' CARA DELL'INNESTO, in due vesti:
	 *      `[M]` 10 agosto 2026, B6 e B5.  Chi mette un tetto deve accendere
	 *      anche cio' che lo fara' scadere, NELL'ISTANTE in cui il tetto
	 *      comincia — non alla prima occasione utile che capita dopo.  Un
	 *      lavoro rimandato a una condizione che nessuno fa piu' avvenire
	 *      non e' rimandato: e' perduto, e nel registro somiglia a un lavoro
	 *      non chiesto. */
	batti_fra(w, 100);
}

/* ========================================================================== */
/* ⭐⭐ IL CICLO DEI FOTOGRAMMI — FASE 3, «il desktop che si muove»            */
/*                                                                            */
/* ⛔⭐ CHE COSA C'ERA QUI PRIMA, E PERCHE' E' STATO TOLTO                     */
/*                                                                            */
/*    Fino alla fase 2 questo posto conteneva un DEPOSITO DI PROCESSO:        */
/*    `struct video_deposito video_dep[3]`, riempito una volta all'accensione */
/*    e letto da ogni sessione che arrivasse a `SESSIONE`.  Aveva tre difetti */
/*    dichiarati, e tutt'e tre sono di questa fase:                            */
/*                                                                            */
/*      1. era di PROCESSO e non di sessione — `main.c` §«il deposito e la    */
/*         fuga» lo dichiara: «la cura vera e' un deposito per sessione».  Il */
/*         ripiego era un PADRONE del deposito, e il prezzo dichiarato era    */
/*         che due utenti collegati insieme non potevano vedere tutt'e due il */
/*         proprio desktop;                                                    */
/*      2. marcava `chiave = true` **per costruzione**, e con chiave/delta    */
/*         veri quella riga diventa **una bugia sul filo** (§6.2, campo       */
/*         `tipo`);                                                            */
/*      3. serviva UN fotogramma per sessione, e il freno era `bool           */
/*         video_fatto`.                                                       */
/*                                                                            */
/* ⇒ Al suo posto c'e' una DIFFUSIONE: il figlio dell'utente cattura e        */
/*   codifica di continuo, `main.c` gira ogni fotogramma qui dentro, e questa */
/*   funzione lo consegna **alle sessioni di quell'utente e a nessun'altra**. */
/*   ⛔ Il confronto sul nome dell'utente e' l'invariante I3 sul filo, ed e'  */
/*   la stessa guardia di prima messa dove serviva: non piu' «di chi e' il    */
/*   deposito», ma «di chi e' questa sessione».  Due utenti collegati insieme */
/*   adesso vedono ciascuno il proprio.                                        */
/*                                                                            */
/* ⚠ E QUEL CHE NON SI FA, DICHIARATO: i byte NON si copiano.  Il fotogramma  */
/*   arriva da `main.c`, viene messo in coda a ciascuna sessione (che lo copia */
/*   lei, in `coda_metti`) e poi il chiamante puo' liberarlo.  Un deposito     */
/*   intermedio qui sarebbe una copia in piu' per fotogramma, cioe' fino a 60  */
/*   copie al secondo di qualche centinaio di KiB.                             */

/* ⛔ L'elenco delle sessioni vive.  Serve perche' i fotogrammi arrivano da
 *    FUORI (dal figlio, per la mano di `main.c`) e non da un evento di questa
 *    connessione: senza un elenco, chi diffonde dovrebbe tenersi lui i
 *    puntatori, e due elenchi dello stesso insieme divergono. */
static wt *vive_prima;

static wt_video_richiesta gancio_palco;
static void *gancio_palco_ctx;

void wt_video_gancio(wt_video_richiesta f, void *ctx)
{
	gancio_palco = f;
	gancio_palco_ctx = ctx;
}

/* ⛔ Ogni quanto si puo' RIchiedere una chiave al palco mentre il debito e'
 *    ancora acceso.  ⚠ Non e' la grazia di §5.2 — quella e' di `rcp.c` e conta
 *    dall'ultima chiave SPEDITA: questo e' il fondo di una richiesta che deve
 *    ancora attraversare un socket, un processo e un codificatore.  Senza,
 *    ogni battito ne manderebbe una e il figlio codificherebbe solo chiavi. */
#define WT_CHIAVE_RICHIESTA_MS 150

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔⛔⛔ E 150 ms NON BASTANO QUANDO LA LINEA E' STRETTA — 21 agosto 2026,
 *       banco `07-b65`, e il difetto e' un ciclo che si autoalimenta.
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * `[M]` La misura, e la scena e' dichiarata: sessione vera, tono nel sink,
 * desktop che si muove, `netem` a **3 Mbit/s** sulla sola porta del banco,
 * trenta secondi.
 *
 *   | scena (stessa banda, stesso audio) | audio spedito | purezza |
 *   |---|---|---|
 *   | desktop **fermo**                  | **6 009** / 6 000 | **1,000** |
 *   | desktop **che si muove**           | **397**           | **0,18**  |
 *
 * ⛔ Non e' la banda e non e' quanto costa l'audio: con **Opus**, cioe' **1/32**
 *    della banda del PCM, allo stesso gradino se ne perde ancora il **58 %**.
 *
 * ⭐⭐ E' QUESTA COSTANTE.  Nei giri stretti il video consegna **solo chiavi**
 *     (144 su 144, 148 su 148, 149 su 149; a 15 Mbit erano 2 su 1 019), il
 *     registro conta **806 richieste di chiave** e **173 righe** «la CHIAVE N
 *     tiene ancora ~60 000 byte in coda e §5.2 vieta di abbandonarla».
 *
 *       una chiave da 60 KB su 3 Mbit occupa la finestra per  **160 ms**
 *       questa costante ne concede una ogni                   **150 ms**
 *
 *     ⇒ **Chiediamo la chiave nuova prima che la precedente sia uscita.**  In
 *     quei 160 ms nascono 32 blocchi di PCM (8 di Opus) e ognuno trova
 *     `cwnd_left = 0`: il datagram non si spezza, non si ritrasmette e non puo'
 *     aspettare, quindi e' l'unico che puo' pagare.
 *
 * ⛔ E la cura NON e' spostare l'audio davanti al video: `07-b65` ha provato
 *    QUATTRO varianti del trasporto (niente ritorno anticipato per passata ·
 *    niente `PADDING` · niente `MORE` · la riserva, cioe' il video che cede la
 *    passata quando ci sono datagram in coda) e i blocchi spediti restano
 *    278-514 contro i 397 di partenza, cioe' dentro la varianza.
 *    ⭐ **La finestra non e' contesa: e' gia' piena** di byte di video in volo,
 *    e rinunciare a scriverne altri non libera quel che e' gia' partito e non e'
 *    ancora stato riscontrato.  Il posto lo libera solo un riscontro.
 *
 * ⇒ **L'intervallo diventa una funzione della banda misurata**: non si chiede
 *   una chiave nuova prima che una chiave della misura dell'ultima abbia avuto
 *   il tempo di uscire.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * 🔸 DERIVATA, E IL PREZZO E' VISIBILE ALL'UTENTE — si dichiara, non si
 *    sottintende (`LEZIONI.md` §2.3-quater, `CODER.md` I6)
 * ───────────────────────────────────────────────────────────────────────────
 *
 * ⛔ **Su linea stretta l'immagine resta rotta piu' a lungo dopo una perdita.**
 *    E' esattamente quel che si compra: prima il desktop chiedeva una chiave
 *    ogni 150 ms e la linea non gliela lasciava uscire (quindi restava rotto
 *    LO STESSO, e in piu' distruggeva l'audio); adesso aspetta il tempo che la
 *    chiave impiega davvero, e in cambio il suono passa.
 *
 * ⚠ Il giudizio e' dell'utente: questi due numeri — il tetto e il margine — non
 *   sono dimostrati, sono derivati.  Vanno in `DECISIONI.md` il giorno in cui
 *   lui li ascolta e li guarda insieme.
 *
 * ⛔ IL TETTO ESISTE PERCHE' UNA CHIAVE CHE NON SI CHIEDE PIU' E' UNO SCHERMO
 *    FERMO PER SEMPRE.  `SPECIFICHE.md` I1: «una sessione brutta vale piu' di
 *    una sessione chiusa» — ma **ferma** non e' **brutta**, e' chiusa a meta'.
 *    Due secondi e' il piu' lungo che si accetti di restare rotti.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⭐ IL PRIMA/DOPO, MISURATO — `07-b65`, 21 agosto 2026, sera
 * ───────────────────────────────────────────────────────────────────────────
 *
 * ⛔ I due binari differiscono per UNA riga (`chiave_intervallo_ms()` che torna
 *    sempre la costante), e i giri sono ALTERNATI: con la varianza vista qui
 *    — 397 contro 1372 blocchi fra due giri identici — due giri di fila della
 *    stessa parte non dimostrerebbero niente.
 *
 * | scena (30 s, PCM)          | attesa | audio PRIMA | audio DOPO | video PRIMA | video DOPO |
 * |---|---|---|---|---|---|
 * | 3 Mbit, desktop **fermo**  | 150 (inerte) | 6 009 | **6 002** | 1 | 1 |
 * | 15 Mbit, desktop mosso     | 150 (inerte) | 4 076 · 3 944 | 3 984 · 3 830 | 743 · 742 | 683 · 677 |
 * | 3 Mbit, desktop mosso      | ~171   | 371 · 462 | **1 552 · 1 595 · 1 725** | 115 · 99 | 89 · 128 |
 * | 1 Mbit, desktop mosso      | 600-1000 | **15** | **577** | 57 | **47** |
 *
 * ⭐ **Dove c'e' banda la cura si dichiara INERTE**: a 15 Mbit ha scritto «la
 *    banda misurata basta: resta il fondo di 150 ms» **100 volte su 101**, e i
 *    due binari si comportano uguale — la differenza dell'8 % sui fotogrammi
 *    li' e' varianza della scena, non un prezzo.
 *
 * ⛔⛔ **IL PREZZO, MISURATO E NON DEDOTTO**: a 1 Mbit le richieste di chiave
 *      scendono da **178 a 68** (−62 %) e il video consegna **57 → 47**
 *      fotogrammi, **−18 %** — e sono tutti chiavi, quindi l'immagine si
 *      aggiorna meno spesso.  ⇒ E' esattamente «su linea stretta l'immagine
 *      resta rotta piu' a lungo dopo una perdita», in numeri.  In cambio
 *      l'audio passa da **15 a 577** blocchi.
 *
 * ⚠ E QUEL CHE LA CURA **NON** FA, dichiarato perche' non se ne prenda di piu'
 *   di quel che da': a 3 Mbit l'audio resta al **27 %** e i fotogrammi
 *   consegnati sono ancora **tutti chiavi**.  ⇒ La spirale non e' spenta, e' solo
 *   piu' lenta.  Il motore vero sta a monte, ed e' scritto accanto a
 *   `video_sgombra()`. */
#define WT_CHIAVE_TETTO_MS 2000

/* ⛔ Il margine: la chiave dev'essere USCITA, non «quasi uscita».  Un quinto
 *    in piu' del tempo calcolato copre il fatto che la stima della banda e' una
 *    stima e che nel frattempo passa anche l'audio. */
#define WT_CHIAVE_MARGINE_PC 120

/* ⛔ Quanti stream uni servono al video PRIMA di dire «senza credito»: `RCP.md`
 *    §2.3 vuole che l'input ne trovi sempre uno, e il video non deve mangiarsi
 *    l'ultimo posto.  ⚠ Il numero e' il minimo che §2.3 riserva a RCP diviso a
 *    meta': si dichiara qui perche' e' una scelta nostra, non una riga
 *    dell'arbitro. */
#define WT_UNI_RISERVA 2

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ FASE 9 — QUANDO UN DELTA E' «DAVVERO SENZA SPERANZA»: LA SOGLIA.
 *
 * ⛔ §5.1 dice **PUO'**, non DEVE (`RCP.md:1156`): abbandonare a ogni
 *    fotogramma piu' recente e' una scelta NOSTRA, e la misura sul campo dice
 *    che e' quella che fabbrica le chiavi.
 *
 * `[M]` 23 agosto 2026, gradino sulla macchina di prova (linea larga → 3 s a
 *       10 Mbit/s → larga), scena `barra`, tela 1920x1080:
 *
 *       | secondo      | 7  | 8  | 9  | 10 | 11 | 12 |
 *       | fotogrammi/s | 40 | 14 | 14 | 13 | 32 | 42 |
 *       | di cui CHIAVE|  0 |  6 |  7 |  7 |  2 |  0 |
 *       | abbandoni    |  0 |  7 |  6 |  7 |  2 |  0 |
 *
 *       ⛔ Abbandoni e chiavi stanno **uno a uno**, anche sulla linea larga
 *       (3↔3, 1↔1).  ⇒ Non e' la linea povera a fabbricare le chiavi: e'
 *       questa funzione.  La linea povera aggiunge solo occasioni.
 *       ⚠ Controllo: lo stesso gradino con una scena che costa 3,7 Mbit/s —
 *       sotto il buco — da' 0 chiavi, 0 abbandoni, 40/s in tutte le fasi: lo
 *       strumento sa distinguere.
 *
 * ⭐ LA REGOLA NUOVA: un delta si abbandona **solo se la coda del video non si
 *    svuota entro la soglia**, cioe' solo se non arriverebbe comunque in tempo
 *    per servire a qualcosa.  Sotto la soglia si TIENE: gli stream sono
 *    indipendenti (`RCP.md:1155`), quindi tenerlo non blocca quelli dopo.
 *
 * ⛔ IL NUMERO, E LA SUA RAGIONE — quattro vincoli, non un gusto:
 *
 *    1. dev'essere **piu' di un periodo di fotogramma**, o e' la regola di oggi
 *       con un nome nuovo: `[M]` fase 8, il contenuto vero dell'utente va a
 *       20,9 fotogrammi/s = **47,8 ms** di periodo (33,3 ms a 30/s);
 *    2. dev'essere **meno del fondo con cui gia' si richiede una chiave** —
 *       `WT_CHIAVE_RICHIESTA_MS` = 150 ms: oltre quel numero la coda
 *       ritarderebbe piu' del ritmo che il prodotto ha gia' accettato;
 *    3. deve **lasciar passare una CHIAVE piu' qualche delta** dove il difetto
 *       morde: `[M]` fase 8 una chiave misura ~20 800 byte (mediana, QP 26); a
 *       3 Mbit/s (375 byte/ms) esce in 56 ms, e nei 44 ms che restano ci
 *       stanno tre delta;
 *    4. il prezzo si somma all'anello: `[M]` fase 8 l'anello intero misura
 *       **55,20 ms**, e 100 + 55 sta sotto il quinto di secondo.
 *
 * ⇒ **100 ms**, ed e' il PREDEFINITO dal 24 agosto 2026 (decisione dell'utente:
 *    le cure della fase 9 si accendono nel prodotto).  ⚠ `[?]` Il numero non e'
 *    dimostrato: e' derivato dai quattro vincoli qui sopra e poi MISURATO —
 *    `[M]` 23-24 ago 2026, banco `09-b79`, tre bracci sulla linea sana: 39,85 /
 *    40,19 / 39,63 fotogrammi/s, **zero chiavi** in tutt'e tre, deriva finale
 *    0,1 / 0,2 / 0,9 ms.  ⇒ Sulla linea sana la cura NON COSTA NIENTE; su rete
 *    cattiva il prezzo e' fino a **+160 ms** di deriva, ed e' quello che
 *    l'utente ha guardato e accettato.
 *
 * ⛔ Il numero sta in `webtransport.h` (`WT_SGOMBRA_SOGLIA_MS`), non qui: `main.c`
 *    ci inizializza la sua variabile, e una seconda copia sarebbe «il
 *    predefinito del server» diverso da «il predefinito del trasporto» il
 *    giorno che uno dei due si tara. */

/* ⛔ Il ripiego quando ngtcp2 non ha ancora ne' `smoothed_rtt` ne' `cwnd`: si
 *    assume **il pavimento dichiarato**, 20 Mbit/s = 2 500 byte/ms
 *    (`DECISIONI.md` §3.1-bis).  ⚠ Si DICHIARA invece di indovinare: un numero
 *    inventato che passa per misurato e' la forma E1.  ⚠ E se la linea vera e'
 *    piu' stretta il ripiego SOTTOSTIMA l'attesa e si tiene un delta di
 *    troppo: dura finche' ngtcp2 non ha una misura, cioe' un giro di rete. */
#define WT_PAVIMENTO_BYTE_MS 2500u

/* ⛔⭐⭐ NASCE ACCESA A `WT_SGOMBRA_SOGLIA_MS` DAL 24 AGOSTO 2026 — decisione
 *      dell'utente.  ⚠ Fino al 23 nasceva SPENTA per l'invariante I6, che vuole
 *      cio' che cambia quel che si VEDE dietro un interruttore spento **finche'
 *      l'utente non l'ha guardato**: l'ha guardato (§19.6, §20.3) e ha deciso.
 *      ⇒ Il presupposto di I6 e' soddisfatto, non aggirato.
 *
 * ⛔ `0` resta la strada per spegnerla (`--sgombra-soglia-ms 0`): si abbandona a
 *    ogni fotogramma piu' recente, cioe' il prodotto di ieri **byte per byte**.
 *
 * ⚠ NON serve un secondo booleano «qualcuno l'ha toccata»: `main.c` chiama
 *   `wt_sgombra_soglia()` **sempre**, all'avvio, col valore in vigore ⇒ la riga
 *   d'avvio esce in tutt'e due i casi per costruzione, non per una guardia da
 *   ricordarsi.  ⛔ E qui non si ripete il numero: la copia sola sta nel .h, e
 *   il valore arriva da `main.c`. */
static uint64_t sgombra_soglia_ms;

/* ⛔⭐ LA RIGA CHE DICHIARA IL VALORE IN VIGORE, E SI SCRIVE ACCESA E SPENTA.
 *
 *     «Spenta» e «non e' mai scattata» non devono avere la stessa faccia: e'
 *     esattamente la forma E1 («scritto non e' in vigore»), la stessa ragione
 *     per cui i tre orologi di §5.3 si scrivono all'avvio.
 *
 * ⛔⛔ E DAL 24 AGOSTO 2026 DEVE DIRE **LO STATO VERO E LA RAGIONE**, non piu'
 *      «SPENTA (I6)».  Una riga che dicesse ancora «spenta (I6)» su una cura
 *      accesa e' peggio di nessuna riga: chi rilegge un banco crederebbe di aver
 *      misurato il prodotto di ieri.  ⇒ Tre cose in ogni riga: se e' accesa, il
 *      NUMERO in vigore, e COME si spegne. */
static void sgombra_dichiara(const char *da_dove)
{
	/* ⚠ E il pezzo di testa — «soglia della coda video (§5.1): N ms» — NON si
	 *   tocca: e' quel che i banchi della fase 9 leggono per verificare il
	 *   braccio (`09-b79-cure.py:582`).  Cambia la CODA della riga, cioe' quel
	 *   che la riga dice; il gancio resta dov'era. */
	if (sgombra_soglia_ms)
		registro_dice(REG_AVVIO,
		              "⭐ FASE 9, soglia della coda video (§5.1): %llu ms — "
		              "ACCESA: sopra la soglia un delta fermo si abbandona, sotto "
		              "si TIENE.  ⭐ E' il PREDEFINITO dal 24 agosto 2026 "
		              "(decisione dell'utente: le cure della fase 9 si accendono "
		              "nel prodotto; l'ha guardate sul desktop vero, §19.6 e "
		              "§20.3).  ⚠ Il prezzo, `[M]` 09-b79: fino a +160 ms di "
		              "deriva su rete cattiva, ZERO sulla linea sana (39,85 / "
		              "40,19 / 39,63 fotogrammi/s, zero chiavi in tutt'e tre i "
		              "bracci).  ⛔ Si SPEGNE con `--sgombra-soglia-ms 0`, ed e' "
		              "l'unica strada.  Impostata da: %s",
		              (unsigned long long)sgombra_soglia_ms, da_dove);
	else
		registro_dice(REG_AVVIO,
		              "⛔ FASE 9, soglia della coda video (§5.1): 0 ms — SPENTA: "
		              "si abbandona a ogni fotogramma piu' recente, cioe' il "
		              "prodotto fino al 23 agosto 2026 byte per byte.  ⚠ E NON E' "
		              "il predefinito: dal 24 agosto nasce ACCESA a %u ms, quindi "
		              "qualcuno ha battuto `--sgombra-soglia-ms 0` apposta.  "
		              "Impostata da: %s",
		              (unsigned)WT_SGOMBRA_SOGLIA_MS, da_dove);
}

/* ⛔ La chiama `main.c` all'avvio, SEMPRE — anche con 0, che e' il caso in cui
 *    qualcuno l'ha spenta apposta.  ⚠ Il ponte provvisorio che leggeva
 *    `REMOTIX_SGOMBRA_SOGLIA_MS` dall'ambiente era dichiarato temporaneo ed e'
 *    stato TOLTO il 23 agosto 2026, quando `--sgombra-soglia-ms` e' arrivata
 *    davvero: due strade per accendere la stessa cura sono due numeri che
 *    possono divergere. */
void wt_sgombra_soglia(uint64_t ms)
{
	sgombra_soglia_ms = ms;
	sgombra_dichiara("main.c, dalla riga di comando (--sgombra-soglia-ms; "
	                 "il predefinito e' 100, e 0 la spegne)");
}

uint64_t wt_sgombra_soglia_letta(void)
{
	return sgombra_soglia_ms;
}

/* ⛔⭐⭐ FASE 9 — IL REGOLATORE DEL RITMO: l'interruttore, e dal 24 agosto 2026
 *      nasce **ACCESO** (decisione dell'utente; fino al 23 nasceva spento per
 *      l'invariante I6, e I6 e' servita: l'utente ha guardato §19.6 e §20.3
 *      prima di decidere).  Si spegne con `--niente-ritmo-adattivo`.
 *    Statico e non per sessione: e' una decisione del server, non del client.
 * ⚠ Il valore lo porta `main.c`, che e' l'unico posto in cui il predefinito e'
 *   scritto: qui non se ne tiene una seconda copia. */
static bool ritmo_adattivo;

/* ⛔ Quanti fotogrammi delta si concede di avere indietro prima di saltarne uno.
 *
 * ⭐ E IL NUMERO NON E' UN OROLOGIO TRAVESTITO: e' la profondita' del tubo.
 *    Con `POSTI = 1` si salterebbe ogni volta che il fotogramma di prima non e'
 *    uscito INTERAMENTE entro l'arrivo del successivo — a 60/s sono 16 ms, e un
 *    delta da 10 KB su una linea sana ne impiega di piu': sarebbe euristica
 *    prudente, cioe' I1 rotta.  Con `POSTI = 2` si concede esattamente UN
 *    fotogramma di sovrapposizione, e si salta solo quando ne sono rimasti
 *    indietro due.
 * ⚠ `[?]` Il valore va tarato sul banco, e la taratura e' falsificabile: a
 *   20 Mbit/s con scena mossa `POSTI = 2` deve dare ZERO discese. */
#define WT_RITMO_POSTI 2

/* ⛔⛔⭐ LA CHIAMA `main.c` ALL'AVVIO, SEMPRE — acceso e spento — e la riga che
 *      esce di qui e' meta' del valore di questa cura.
 *
 *      Un regolatore SPENTO e un regolatore che non ha mai dovuto scattare
 *      producono LO STESSO REGISTRO, cioe' nessuna riga.  Chi rilegge un banco
 *      senza questa riga non sa quale dei due ha misurato: e' la forma E1
 *      («scritto non e' in vigore»), ed e' la stessa ragione per cui
 *      `chiave_intervallo_ms()` porta `*come` e per cui `sgombra_dichiara()`
 *      parla anche a zero.
 *
 * ⛔⛔ E QUI SI DICHIARA ANCHE LA DIPENDENZA FRA I DUE INTERRUTTORI, che e' il
 *      fatto piu' facile da misurare male di tutta la fase.
 *
 *      `video_sgombra()` con la soglia SPENTA abbandona ogni delta che ha
 *      ancora byte in coda, a ogni fotogramma piu' recente.  ⇒ Quando il
 *      fotogramma N+1 arriva, l'unico delta che puo' avere ancora byte nostri
 *      e' N: `arretrato` vale **0 o 1, mai 2**, per costruzione — e con
 *      `WT_RITMO_POSTI = 2` questo regolatore **non scatta mai**.
 *
 *      ⛔ Un banco che lasciasse acceso il solo regolatore (cioe' che battesse
 *      `--sgombra-soglia-ms 0` senza `--niente-ritmo-adattivo`) misurerebbe zero
 *      discese e leggerebbe «la linea porta».  Sono due fatti con la stessa
 *      faccia, e la riga qui sotto e' quel che li separa PRIMA della misura
 *      invece che dopo.
 *
 * ⭐ Dal 24 agosto 2026 il caso normale e' che siano accesi TUTT'E DUE di suo:
 *      remotix                       (i predefiniti: soglia 100 ms + regolatore)
 *   e la coppia che non misura niente va CHIESTA apposta.
 *
 * ⚠ E l'ordine in `main.c` non e' un caso: `wt_sgombra_soglia()` viene PRIMA,
 *   cosi' questa riga legge il valore in vigore invece di prometterne uno.
 *
 * ⚠⚠ E l'ALGORITMO DI CONGESTIONE non e' mai stato scelto — `trasporto.c`
 *     chiama `ngtcp2_settings_default()` e non tocca `cc_algo`, quindi si
 *     prende il predefinito di ngtcp2 (CUBIC).  ⛔ NON si cambia in questo
 *     giro, perche' sarebbe una seconda variabile nello stesso banco; ma va
 *     nominato, perche' morde proprio qui: su WiFi un algoritmo A PERDITA
 *     legge una perdita da radio come una congestione e dimezza la finestra —
 *     cioe' fabbrica l'arretrato che questo regolatore poi misura.  `[?]` Da
 *     provare come esperimento separato, dietro un interruttore suo. */
void wt_ritmo_adattivo(bool acceso)
{
	ritmo_adattivo = acceso;
	if (!acceso) {
		registro_dice(REG_AVVIO,
		              "⛔ il regolatore del ritmo e' SPENTO da chi ha lanciato il "
		              "server (`--niente-ritmo-adattivo`): nessun fotogramma "
		              "verra' mai saltato per la linea, cioe' il prodotto fino al "
		              "23 agosto 2026 byte per byte.  ⚠ E NON E' il predefinito: "
		              "dal 24 agosto nasce ACCESO (decisione dell'utente), quindi "
		              "qualcuno l'ha spento apposta.  ⚠ E questa riga E' il "
		              "perche' — non e' che non ha dovuto scattare");
		return;
	}
	registro_dice(REG_AVVIO,
	              "⭐ FASE 9: il regolatore del ritmo e' ACCESO — un fotogramma "
	              "NON parte quando %u delta in volo hanno ancora byte nella mia "
	              "coda d'uscita.  ⭐ E' il PREDEFINITO dal 24 agosto 2026 "
	              "(decisione dell'utente: le cure della fase 9 si accendono nel "
	              "prodotto; l'ha guardate sul desktop vero, §19.6 e §20.3).  ⚠ Il "
	              "prezzo, `[M]` 09-b79: soglia piu' regolatore costano fino a "
	              "+160 ms di deriva su rete cattiva, ZERO sulla linea sana "
	              "(39,85 / 40,19 / 39,63 fotogrammi/s, zero chiavi in tutt'e tre "
	              "i bracci).  ⛔ Si SPEGNE con `--niente-ritmo-adattivo`, ed e' "
	              "l'unica strada — il nome vecchio `--ritmo-adattivo` non esiste "
	              "piu'.  ⚠ Ogni discesa finisce nel registro (I1), e non c'e' "
	              "nessuna risalita da ricordare: `arretrato` si rilegge a ogni "
	              "fotogramma",
	              (unsigned)WT_RITMO_POSTI);
	if (!sgombra_soglia_ms)
		registro_dice(REG_AVVIO,
		              "⛔⛔ MA LA SOGLIA DELLA CODA VIDEO E' SPENTA "
		              "(`--sgombra-soglia-ms 0`), e allora questo regolatore NON "
		              "SCATTERA' MAI: `video_sgombra()` svuota la coda dei delta a "
		              "ogni fotogramma, quindi `arretrato` non puo' superare 1 e i "
		              "posti sono %u.  ⚠ Un banco fatto cosi' misura ZERO discese e "
		              "sembra dire «la linea porta»: sono due fatti con la stessa "
		              "faccia.  ⇒ Coi predefiniti del 24 agosto 2026 nascono accesi "
		              "TUTT'E DUE: chi vede questa riga ha spento la soglia a mano "
		              "e ha lasciato acceso il regolatore, che e' la combinazione "
		              "che non misura niente",
		              (unsigned)WT_RITMO_POSTI);
	else
		registro_dice(REG_AVVIO,
		              "⭐ e la soglia della coda video e' accesa a %llu ms: e' il "
		              "suo prerequisito — e' lei che lascia salire `arretrato` a "
		              "2-3, cioe' nell'intervallo in cui i %u posti discriminano",
		              (unsigned long long)sgombra_soglia_ms,
		              (unsigned)WT_RITMO_POSTI);
}

/* ⛔⛔⭐ LA CHIAMA `main.c` ALL'AVVIO, SEMPRE — accesa e spenta — e la riga che
 *      esce di qui e' la meta' del valore di questa cura, per la stessa ragione
 *      di `wt_ritmo_adattivo()`: una cura spenta e una cura che non ha mai
 *      dovuto scattare producono LO STESSO REGISTRO, cioe' nessuna riga.
 *
 * ⛔⛔ E QUESTA E' LA PIU' VISIBILE DI TUTTE — butta fuori una sessione.  I6 non
 *      e' stata una formalita' qui: e' il passo che in v1 e' costato
 *      l'azzeramento di una fase intera.  ⇒ E' nata spenta, l'utente l'ha
 *      guardata sul desktop vero (§19.6, §20.3), e il **24 agosto 2026** ha
 *      deciso che diventa il comportamento normale.  ⭐ Il presupposto di I6 e'
 *      soddisfatto — non aggirato: l'interruttore c'e' ancora, e' solo girato
 *      dall'altra parte (`--niente-linea-morta`).
 *
 * `stallo_ms`  i millisecondi senza che esca un byte di video PUR AVENDONE da
 *              mandare.  `0` = spento, e allora nessuno stallo, per lungo che
 *              sia, dichiara morta la linea (resta il solo silenzio).
 * `silenzio_s` i secondi senza un pacchetto dal client.  `0` = spento.
 *
 * ⚠ E NON C'E' NESSUNA VARIABILE D'AMBIENTE, apposta: il ponte
 *   `REMOTIX_SGOMBRA_SOGLIA_MS` e' stato tolto il 23 agosto 2026 con la
 *   ragione scritta accanto a `wt_sgombra_soglia()` — due strade per accendere
 *   la stessa cura sono due numeri che possono divergere.  Il banco usa le
 *   opzioni, che sono l'unica strada.
 */
void wt_linea_morta(bool accesa, uint64_t stallo_ms, uint64_t silenzio_s)
{
	linea_morta_accesa = accesa;
	linea_morta_stallo_ms = stallo_ms;
	linea_morta_silenzio_ms = silenzio_s * 1000;
	if (!accesa) {
		registro_dice(REG_AVVIO,
		              "⛔ la LINEA MORTA e' SPENTA da chi ha lanciato il server "
		              "(`--niente-linea-morta`): nessuna sessione verra' mai "
		              "chiusa per stallo dell'uscita ne' per silenzio del client "
		              "prima dei 30 s di QUIC (§5.3) — cioe' il prodotto fino al "
		              "23 agosto 2026 byte per byte.  ⚠ E NON E' il predefinito: "
		              "dal 24 agosto nasce ACCESA (decisione dell'utente), quindi "
		              "qualcuno l'ha spenta apposta.  ⚠ E questa riga E' il "
		              "perche' — non e' che non ha dovuto scattare");
		return;
	}
	registro_dice(REG_AVVIO,
	              "⛔⭐ FASE 9: la LINEA MORTA e' ACCESA — il "
	              "filo cade e l'utente rientra A MANO (decisione dell'utente, 23 "
	              "agosto 2026).  ⭐ E' il PREDEFINITO dal 24 agosto 2026, e si "
	              "SPEGNE con `--niente-linea-morta` (unica strada; il nome "
	              "vecchio `--linea-morta` non esiste piu').  ⛔⛔ E' LA CURA CHE "
	              "CHIUDE UNA SESSIONE: se la soglia fosse tarata male butterebbe "
	              "fuori chi sta lavorando — `[M]` 23-24 ago il margine e' >10x "
	              "sopra `casa-cattiva`, la linea PEGGIORE che regge (stallo "
	              "massimo < 500 ms su dieci minuti, zero scatti), e 2,9x sotto i "
	              "14,26 s di `raffica-forte`, che non serve nessuno.  DUE cause, "
	              "e ognuna scrive la sua riga "
	              "`linea-morta` col conto su cui ha deciso (I1):  (1) STALLO: "
	              "%llu ms senza che esca un byte di video mentre ne avevamo da "
	              "mandare — e «avevo da mandare» vuol dire byte di fotogrammi "
	              "ancora in coda OPPURE un fotogramma nuovo dal palco: a scena "
	              "ferma il conto non parte nemmeno;  (2) SILENZIO: %llu s senza "
	              "un pacchetto dal client con almeno %u pacchetti nostri usciti "
	              "nel frattempo.  ⚠ Margini della soglia dello stallo, `[M]` 23 "
	              "ago: 5,0× sopra il secondo intero vuoto di `raffica-1` (che "
	              "REGGE, 23,94 fotogrammi/s) e 2,9× sotto i 14,26 s di "
	              "`raffica-forte` (che non serve nessuno).  ⛔⛔ E LA FRAZIONE DI "
	              "PERDITA NON GIUDICA PIU': `permille=` resta nella riga come "
	              "TESTIMONE del riordino — `casa-cattiva` ne dichiarava 512‰ e "
	              "REGGEVA dieci minuti, `raffica-forte` 123‰ e non reggeva",
	              (unsigned long long)linea_morta_stallo_ms,
	              (unsigned long long)(linea_morta_silenzio_ms / 1000),
	              (unsigned)WT_LM_MIN_PROVE);
	if (!linea_morta_stallo_ms)
		registro_dice(REG_AVVIO,
		              "⚠ ma la soglia dello STALLO e' a 0 ms: resta il solo "
		              "silenzio.  Un'immagine ferma non chiudera' niente");
	if (!linea_morta_silenzio_ms)
		registro_dice(REG_AVVIO,
		              "⚠ ma la soglia del SILENZIO e' a 0 s: resta la sola "
		              "perdita, e un client che tace aspetta i 30 s di QUIC "
		              "(§5.3) come sempre");
}

/* ⛔ Quanti ms ci mette la banda MISURATA a portare via `byte` — gli stessi due
 *    numeri di `chiave_intervallo_ms()`, che sono quelli con cui ngtcp2 decide
 *    quanto spedire.  ⚠ Non e' la banda «della linea»: e' quella che il
 *    controllo di congestione sta concedendo adesso.
 *
 * ⛔⛔ E QUESTA STIMA E' UN MINIMO, non una promessa — tre ragioni, dichiarate
 *     perche' e' il falsificatore piu' importante del §5.3 della proposta:
 *     (a) non conta i byte gia' consegnati a ngtcp2 e non ancora riscontrati,
 *         che la coda non vede piu';
 *     (b) la finestra la divide anche l'audio, che passa su datagram;
 *     (c) una ritrasmissione ripaga la stessa banda due volte.
 *     ⇒ Se il ritardo misurato dell'anello supera 55 + soglia ms, e' QUI che
 *     ha ceduto: sarebbe un numero che *sembra* misurato. */
static uint64_t coda_svuotamento_ms(const wt *w, size_t byte, const char **come)
{
	ngtcp2_conn_info info;

	if (byte == 0) {
		*come = "la coda del video e' vuota";
		return 0;
	}
	memset(&info, 0, sizeof info);
	if (w->conn)
		ngtcp2_conn_get_conn_info(w->conn, &info);
	if (info.smoothed_rtt == 0 || info.cwnd == 0) {
		*come = "ripiego: ngtcp2 non ha ancora ne' rtt ne' finestra, si assume "
		        "il pavimento dichiarato di 20 Mbit/s (DECISIONI.md §3.1-bis)";
		return (uint64_t)byte / WT_PAVIMENTO_BYTE_MS;
	}
	*come = "dalla banda misurata (cwnd/rtt)";
	return (uint64_t)byte * info.smoothed_rtt / info.cwnd / NGTCP2_MILLISECONDS;
}

/* ------------------------------------------------------------------------ */
/* ⭐ §5.1 — L'ABBANDONO, ED E' QUELLO CHE SI VEDE DAL LATO CHE RICEVE.       */

static void involo_pulisci(wt *w)
{
	size_t j = 0;
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo)
			w->involo[j++] = w->involo[i];
	w->ninvolo = j;
}

/* ⛔ §5.1: «il server PUO' chiamare `RESET_STREAM` su un fotogramma che non
 *    serve piu' — perche' ne e' gia' partito uno piu' recente — e i byte non
 *    ancora spediti non partono affatto».
 *
 * ⚠ «Non ancora spediti» vuol dire «ancora nella NOSTRA coda»: quel che e' gia'
 *   passato a ngtcp2 non lo riprendiamo, e azzerare li' non risparmierebbe piu'
 *   niente.  ⇒ Un fotogramma senza byte in coda esce dall'elenco senza che si
 *   scriva niente: non e' stato abbandonato, e' stato spedito. */
/*
 * ⛔⛔⛔ E QUI STA IL MOTORE DELLA SPIRALE — trovato il 21 agosto 2026 misurando
 *       la cura di `WT_CHIAVE_TETTO_MS`, e NON e' quel che credevo.
 *
 *       Questa funzione si chiama a OGNI fotogramma che arriva dal palco, e
 *       abbandona i delta ancora fermi in coda perche' «ne e' partito uno piu'
 *       recente» (§5.1).  Su una linea larga non abbandona quasi mai.  ⛔ Su
 *       una linea stretta un delta non fa in tempo a uscire in 33 ms, quindi
 *       viene abbandonato **sempre**, e ogni abbandono accende il debito di
 *       §5.2 dentro `rcp.c`.
 *
 *       `[M]` Il registro di un giro a 3 Mbit lo dice **28 volte al secondo**:
 *       «⛔ FOTOGRAMMA NON SPEDITO: e' un delta e §5.2 vuole una CHIAVE (un
 *       delta e' stato abbandonato nella coda (§5.1))».  ⇒ Il debito non si
 *       spegne mai, ogni fotogramma consegnato e' una CHIAVE (115 su 115, 99 su
 *       99, 128 su 128), ogni chiave riempie la finestra e i datagram
 *       dell'audio trovano `cwnd_left = 0`.
 *
 * ⚠⚠ E LA MIA PRIMA DIAGNOSI CONTAVA LA RIGA SBAGLIATA: avevo cercato «vuole
 *     una CHIAVE», che compare in DUE messaggi diversi — la RICHIESTA che parte
 *     da `video_regola()` e il RIFIUTO che scrive `rcp.c`.  Le «806 richieste di
 *     chiave» del primo rapporto erano in gran parte rifiuti.  ⇒ Contate
 *     separatamente: **105 richieste contro 346 rifiuti** nello stesso giro.
 *     La riga che si somiglia si conta a parte, o la diagnosi punta a monte di
 *     dove sta il difetto.
 *
 * ⇒ ⭐ **LA CURA E' QUI SOTTO, dal 23 agosto 2026** (fase 9): abbandonare un
 *   delta solo quando e' davvero senza speranza — una **soglia sulla coda** —
 *   invece che a ogni fotogramma piu' recente.  §5.1 lo **permette**, non lo
 *   **impone**.  Cosi' sotto congestione il video cala di RITMO restando fatto
 *   di delta, invece di diventare un flusso di sole chiavi.
 *   ⭐ E dal 24 agosto 2026 nasce ACCESA a 100 ms (decisione dell'utente; fino
 *   al 23 nasceva spenta per l'invariante I6).  ⛔ Con `--sgombra-soglia-ms 0`
 *   questa funzione torna a fare quel che ha sempre fatto, byte per byte.
 */
/*
 * ⛔⭐⭐ LA PREVISIONE FALSIFICABILE — scritta PRIMA di misurare, 23 ago 2026.
 *
 *       Stesso gradino della tabella qui sopra (linea larga → 3 s a 10 Mbit/s →
 *       larga), scena `barra`, 1920x1080, con `--sgombra-soglia-ms 100`:
 *
 *       | grandezza                    | oggi (spenta) | previsione a 100 ms |
 *       | fotogrammi/s nei secondi 8-10| 13-14         | **>= 25**           |
 *       | di cui CHIAVE, al secondo    | 6-7           | **<= 2**            |
 *       | abbandoni §5.1 al secondo    | 6-7           | **<= 2**            |
 *       | secondi 7 e 12 (linea larga) | 40-42/s, 0 ch | **identici** (inerte)|
 *       | ritorno, secondo 11          | 32/s          | **>= 32/s**         |
 *       | conto finale                 | —             | TENUTI >> 0         |
 *
 *       ⭐ E fuori dal gradino la cura dev'essere INERTE: a 20 Mbit/s — il
 *       pavimento di `DECISIONI.md` §3.1-bis — la coda non arriva mai a 100 ms,
 *       quindi `abbandonati per soglia` = 0 e il ritardo dell'anello resta
 *       quello di fase 8 (55,20 ms `[M]`).
 *
 * ⛔ I QUATTRO ROSSI CHE MI SMENTIREBBERO — e ognuno dice dove guardare:
 *
 *    1. **le chiavi restano 6-7/s mentre gli abbandoni §5.1 scendono a <= 2.**
 *       ⇒ Il debito di §5.2 lo accende un'ALTRA delle sette cause, quasi
 *       certamente la 4 (`rcp.c:3441`, il credito mancato — la forma invisibile
 *       al ricevente), e la cura gira a vuoto.  ⚠ Il conto finale distingue le
 *       due apposta: `abbandonati per soglia` contro `non accettati per credito
 *       mancato`.  E' la lezione gia' pagata («105 richieste contro 346
 *       rifiuti nello stesso giro»);
 *    2. **i fotogrammi/s nei secondi 8-10 non salgono, o scendono sotto 13.**
 *       ⇒ I delta tenuti arrivano troppo tardi per servire: la soglia e' troppo
 *       alta e la coda sta comprando fluidita' vendendo risposta
 *       (`SPECIFICHE.md:128-130`).  Si scende a 50 ms e si rimisura;
 *    3. ⛔ **il ritardo misurato dell'anello supera 55 + soglia ms** (155 ms a
 *       100).  ⇒ `coda_svuotamento_ms()` SOTTOSTIMA lo svuotamento per una
 *       delle tre ragioni dichiarate accanto a lei, e la soglia non limita quel
 *       che promette.  ⭐ E' il rosso piu' importante, perche' sarebbe **un
 *       numero che sembra misurato**;
 *    4. **il ritorno smette di essere sotto il secondo** (secondo 11 sotto
 *       32/s).  ⇒ La coda tenuta ritarda la RIPRESA, cioe' la cura paga il
 *       transitorio col ritorno: e' il contrario del suo scopo, e a quel punto
 *       la soglia va spenta invece che tarata.
 *
 * ⚠⚠ IL PREZZO, IN MILLISECONDI — e' la cosa che l'utente deve giudicare, non
 *     una misura: per una frazione di secondo, sotto congestione, l'immagine e'
 *     **leggermente vecchia** invece che sfasciata.
 *
 *     | quando la linea porta (>= 20 Mbit/s)      | **0 ms** — mai a soglia  |
 *     | al peggio, per costruzione                | **100 ms** (la soglia)   |
 *     | + la grana del controllo (a ogni fotogr.) | **+33 … +48 ms**         |
 *     | ⇒ peggio dichiarato, solo durante il calo | **~150 ms**              |
 *     | + l'anello di fase 8 (55,20 ms `[M]`)     | **~205 ms** gesto→pixel  |
 *     | **oggi**, nello stesso istante            | 0 ms aggiunti, ma il     |
 *     |                                           | 100 % chiavi e i delta   |
 *     |                                           | non arrivano affatto     |
 *
 *     ⚠ Concretamente: trascinando una finestra mentre la linea cala, la
 *     finestra segue il puntatore con fino a un quinto di secondo di ritardo
 *     per un attimo — invece di scattare da un'immagine all'altra a ritmo di
 *     chiave.  ⛔ Quale delle due sia peggio non lo decide una misura: lo
 *     decide lui.
 *
 * ⭐⭐ E QUESTA CURA E' IL PREREQUISITO DEL REGOLATORE DEL RITMO
 *     (`fasi/09-la-qualita-e-la-degradazione.md` §6).  Quel disegno si aggancia ad
 *     `arretrato` = quanti DELTA vivi hanno ancora byte nella nostra coda, e
 *     ⛔ oggi quella grandezza e' **zero per costruzione**, perche' questa
 *     funzione svuota tutto a ogni giro: un regolatore installato adesso non
 *     scatterebbe mai e il banco lo leggerebbe come «la linea porta».
 *     ⇒ Qui `arretrato` si conta con la definizione di §3.1 — vivo, NON chiave,
 *     byte in coda > 0 — e si SCRIVE in ogni riga accanto alla soglia, cosi'
 *     la grandezza del regolatore diventa leggibile invece di diventare
 *     un'altra cosa ancora.  ⚠ A 100 ms e 20,9-30 fotogrammi/s `arretrato` puo'
 *     salire a **2-3**, che e' esattamente l'intervallo in cui il `POSTI = 2`
 *     di quel disegno discrimina.
 */
static void video_sgombra(wt *w, const char *perche)
{
	size_t resto[WT_INVOLO_MAX];
	size_t in_coda = 0;
	unsigned arretrato = 0;
	uint64_t attesa = 0;
	const char *come = "la soglia e' a 0 (spenta a mano: dal 24 ago 2026 il predefinito e' 100 ms)";
	char motivo[400];

	if (!w->rcp || !w->conn)
		return;

	/* ⛔ PRIMA PASSATA — e non e' un giro in piu': chi non ha piu' byte esce
	 * dall'elenco (non e' stato abbandonato, e' stato SPEDITO), e quel che
	 * resta si somma.  La somma e' la coda del VIDEO — non `w->byte_in_coda`,
	 * che conterrebbe anche il canale di controllo e l'audio.
	 * ⚠ I byte si tengono in `resto[]` invece di rileggerli: fra le due
	 *   passate non cambia niente, e `coda_byte_stream()` scorre tutta la coda
	 *   ogni volta. */
	for (size_t i = 0; i < w->ninvolo; i++) {
		resto[i] = 0;
		if (!w->involo[i].vivo)
			continue;
		resto[i] = coda_byte_stream(w, w->involo[i].stream);
		if (resto[i] == 0) {
			w->involo[i].vivo = false;
			continue;
		}
		in_coda += resto[i];
		/* ⭐ `arretrato` esclude le CHIAVI, ed e' la definizione di §3.1 del
		 *    disegno del regolatore: una chiave lenta in coda non deve fermare
		 *    la produzione di delta, ha gia' il suo regolatore in
		 *    `chiave_intervallo_ms()`.  ⚠ Ma i suoi BYTE contano nella somma:
		 *    occupano il tubo davvero, e il prezzo in ms deve dirlo. */
		if (!w->involo[i].chiave)
			arretrato++;
	}

	if (sgombra_soglia_ms) {
		attesa = coda_svuotamento_ms(w, in_coda, &come);
		if (attesa <= sgombra_soglia_ms) {
			/* ⭐ SI TIENE — e non si scrive una riga per fotogramma: si conta,
			 * e la riga esce solo quando lo STATO cambia.  ⚠ Trenta righe al
			 * secondo renderebbero illeggibile il registro proprio dove serve:
			 * e' la stessa ragione del fondo di `chiave_intervallo_ms()`. */
			w->sgombra_tenuti += arretrato;
			if (w->sgombra_sopra) {
				w->sgombra_sopra = false;
				registro_dice(REG_RCP,
				              "⭐ %s: la coda del video torna SOTTO la soglia "
				              "(%zu byte = %llu ms, soglia %llu ms, %s): i %u "
				              "delta arretrati si TENGONO — §5.1 dice PUO', non "
				              "DEVE",
				              w->provenienza, in_coda,
				              (unsigned long long)attesa,
				              (unsigned long long)sgombra_soglia_ms, come,
				              arretrato);
			}
			involo_pulisci(w);
			return;
		}
		if (!w->sgombra_sopra) {
			w->sgombra_sopra = true;
			registro_dice(REG_RCP,
			              "⛔ %s: la coda del video passa SOPRA la soglia (%zu "
			              "byte = %llu ms, soglia %llu ms, %s), arretrato %u "
			              "delta: da qui i piu' vecchi si abbandonano (§5.1), "
			              "il minimo per rientrare",
			              w->provenienza, in_coda, (unsigned long long)attesa,
			              (unsigned long long)sgombra_soglia_ms, come,
			              arretrato);
		}
	}

	for (size_t i = 0; i < w->ninvolo; i++) {
		size_t rimasti = resto[i];
		if (!w->involo[i].vivo || rimasti == 0)
			continue;
		if (w->involo[i].chiave) {
			/* ⛔ §5.2: «il server NON DEVE abbandonare un fotogramma chiave.
			 * Abbandonare la cura non e' una cura».  ⚠ E si dice UNA volta,
			 * perche' e' una cosa che dura finche' la linea non la porta via:
			 * ripeterla a ogni fotogramma renderebbe illeggibile il registro
			 * proprio quando serve. */
			if (!w->involo[i].detto) {
				w->involo[i].detto = true;
				registro_dice(REG_RCP,
				              "⚠ %s: la CHIAVE %u tiene ancora %zu byte in coda "
				              "e §5.2 vieta di abbandonarla: si ASPETTA.  ⭐ E i "
				              "delta che vengono dopo non sono bloccati da lei — "
				              "gli stream sono indipendenti (§5.1)",
				              w->provenienza, w->involo[i].numero, rimasti);
			}
			continue;
		}
		/* ⛔ §5.1: «ogni abbandono DEVE essere scritto nel registro» — un
		 * fotogramma perso in silenzio e uno abbandonato di proposito hanno lo
		 * stesso aspetto dal lato che riceve.  ⭐ E il MOTIVO porta LA MISURA
		 * ACCANTO ALLA SOGLIA: se la misura e' sotto la soglia, quella discesa
		 * e' stata per prudenza, e la riga stessa lo dimostra.  Senza, il
		 * registro direbbe «ne e' partito uno piu' recente» anche quando la
		 * ragione vera e' un'altra, e racconterebbe la regola vecchia.
		 * ⚠ La riga, il conto e il debito restano di `rcp.c`: due copie dello
		 * stesso stato divergono. */
		snprintf(motivo, sizeof motivo,
		         "%s — e la coda del video non si svuota in tempo: %zu byte = "
		         "%llu ms (%s), soglia %llu ms, arretrato %u delta",
		         perche, in_coda, (unsigned long long)attesa, come,
		         (unsigned long long)sgombra_soglia_ms, arretrato);
		if (!rcp_video_abbandonato_a_valle(w->rcp, w->involo[i].numero, false,
		                                   rimasti,
		                                   sgombra_soglia_ms ? motivo : perche))
			continue;
		/* ⛔ PRIMA si azzera lo stream, POI si buttano i byte.  Al contrario
		 * resterebbe una finestra — corta ma vera — in cui lo stream e' vivo e
		 * i suoi byte non ci sono piu': `wt_scrivi()` lo troverebbe muto invece
		 * che azzerato, e il client aspetterebbe una fine che non arriva. */
		ngtcp2_conn_shutdown_stream_write(w->conn, 0, w->involo[i].stream, 0);
		coda_butta_stream(w, w->involo[i].stream);
		w->involo[i].vivo = false;
		w->sgombra_abbandoni++;
		/* ⭐ SI ABBANDONA IL MINIMO, e si scorre dal PIU' VECCHIO: l'elenco e'
		 * in ordine d'inserimento (`involo_aggiungi()`), quindi il primo vivo
		 * e' il piu' vecchio ed e' quello che serve meno.  ⛔ Appena la coda
		 * rientra sotto la soglia si SMETTE: abbandonare anche gli altri
		 * costerebbe una chiave per niente, ed e' precisamente la spirale che
		 * `RCP.md:1284` nomina — «un fotogramma chiave per ogni delta
		 * abbandonato e' la spirale».
		 *
		 * ⚠ E SI ESCE IN SILENZIO, senza una riga «bastava»: lo stato NON e'
		 *   cambiato — la soglia sta ancora mordendo, e il rientro e' opera di
		 *   questo abbandono, non della linea.  Scriverla qui vorrebbe dire
		 *   due righe per fotogramma, cioe' sessanta al secondo mentre il
		 *   gradino dura: e' il difetto che il fondo di `chiave_intervallo_ms()`
		 *   esiste per non fare.  ⭐ `sgombra_sopra` torna falso solo quando una
		 *   passata INTERA trova la coda sotto la soglia senza abbandonare
		 *   niente: quello si' e' un cambio di stato. */
		if (sgombra_soglia_ms) {
			arretrato--;
			in_coda -= rimasti;
			attesa = coda_svuotamento_ms(w, in_coda, &come);
			if (attesa <= sgombra_soglia_ms)
				break;
		}
	}
	involo_pulisci(w);
}

static void involo_aggiungi(wt *w, int64_t stream, uint32_t numero, bool chiave)
{
	if (stream < 0)
		return;
	involo_pulisci(w);
	if (w->ninvolo >= WT_INVOLO_MAX) {
		/* ⚠ Si dice invece di scivolare: da qui in poi quel fotogramma non
		 *   sara' abbandonabile, e chi legge il registro deve saperlo — un
		 *   abbandono che non avviene perche' una tabella e' piena somiglia in
		 *   tutto a un abbandono che nessuno ha chiesto. */
		registro_dice(REG_WT,
		              "⚠ %s: %u fotogrammi gia' in volo: il %u non entra "
		              "nell'elenco e NON potra' essere abbandonato (§5.1)",
		              w->provenienza, WT_INVOLO_MAX, numero);
		return;
	}
	w->involo[w->ninvolo].stream = stream;
	w->involo[w->ninvolo].numero = numero;
	w->involo[w->ninvolo].chiave = chiave;
	w->involo[w->ninvolo].vivo = true;
	w->involo[w->ninvolo].detto = false;
	w->ninvolo++;
}

/* ------------------------------------------------------------------------ */
/* ⭐ LA CUCITURA FRA LA CHIAVE CHIESTA E IL CODIFICATORE — punto 4.          */

/* ⛔ `rcp_video_serve_chiave()` era LETTA e non serviva a niente:
 *    `codificatore_chiedi_chiave()` non aveva **nessun chiamante nel prodotto**.
 *    ⇒ Un `RICHIEDI_CHIAVE` del client accendeva un `bool` in `rcp.c`, il
 *    fotogramma dopo era un delta, `rcp_video_apri()` lo rifiutava con
 *    `RCP_VIDEO_SERVE_UNA_CHIAVE`, e **lo schermo restava fermo per sempre** —
 *    perche' `chiavi_ogni = 0` da' GOP infinito e dopo la prima chiave non ne
 *    arriva mai piu' una da sola.
 *
 * ⇒ Il gancio: il palco sta in un ALTRO PROCESSO (il figlio dell'utente), e
 *   questa e' la riga che attraversa il confine.  ⚠ Sta qui e non in `rcp.c`
 *   perche' `rcp.c` non conosce i figli, e non in `main.c` perche' `main.c` non
 *   conosce lo stato della sessione. */
/*
 * ⭐ IL CANALE AUDIO SI ACCENDE, e NON passa dal codec del video.
 *
 * ⛔ Sta in una funzione sua e non dentro `video_regola()` per un motivo che
 *    si vede solo scrivendolo: quella torna subito quando `video.codec` non e'
 *    negoziato — che e' il caso legittimo di un client della fase 1 — e
 *    l'audio ci finirebbe dentro per caso.  Le due negoziazioni sono
 *    indipendenti in `RCP.md` §4.3, e vanno lette indipendenti anche qui.
 */
/*
 * ⭐⭐ OGNI QUANTO SI PUO' RICHIEDERE UNA CHIAVE — e la banda si MISURA.
 *
 * ⛔ La regola: non si chiede una chiave nuova prima che una chiave della
 *    misura dell'ultima abbia avuto il tempo di **uscire davvero**.  Il perche'
 *    e i numeri stanno accanto a `WT_CHIAVE_TETTO_MS`.
 *
 * ⛔⭐ E LA BANDA NON SI INDOVINA: la danno due numeri che ngtcp2 misura da se',
 *     e sono gli stessi con cui decide quanto spedire —
 *
 *         banda ≈ cwnd / smoothed_rtt        (byte per secondo)
 *         tempo di una chiave = byte × smoothed_rtt / cwnd
 *
 *     ⚠ Non e' una banda «della linea»: e' **la banda che il controllo di
 *       congestione sta concedendo adesso**, che e' precisamente la velocita'
 *       con cui la chiave uscira'.  Usare la capacita' del collegamento
 *       darebbe un numero piu' bello e sbagliato.
 *
 * ⛔ E SE LA STIMA NON C'E' ANCORA, IL RIPIEGO SI DICHIARA — `CODER.md` §4.2 e
 *    §3.10: all'inizio della connessione `smoothed_rtt` e `cwnd` non hanno
 *    ancora un valore, e la misura di una chiave non esiste finche' non ne e'
 *    partita una.  ⇒ In quei casi si torna alla costante di prima e si scrive
 *    **quale** dei tre casi e', invece di far passare un numero inventato per
 *    un numero misurato.  ⚠ `*come` non e' un ornamento del registro: e'
 *    l'unica cosa che distingue «la cura sta lavorando» da «la cura non e'
 *    ancora accesa», e senza di lei le due hanno la stessa faccia.
 */
static uint64_t chiave_intervallo_ms(wt *w, const char **come)
{
	ngtcp2_conn_info info;
	uint64_t ms;
	size_t in_coda = 0;

	if (!w->conn) {
		*come = "ripiego: non c'e' connessione";
		return WT_CHIAVE_RICHIESTA_MS;
	}

	/* ⛔⭐⭐ PRIMA DI OGNI STIMA: SE LA CHIAVE PRECEDENTE E' ANCORA QUI, LA
	 *       RISPOSTA NON E' UNA STIMA — E' UN FATTO.
	 *
	 *       La frase del difetto e' «chiediamo una chiave nuova prima che la
	 *       precedente sia partita», e questo ciclo sa **se e' partita**: sono
	 *       gli stessi byte che `video_sgombra()` conta per dire «la CHIAVE N
	 *       tiene ancora %zu byte in coda e §5.2 vieta di abbandonarla».
	 *
	 * ⭐ Guardare qui invece di calcolare e' meglio per una ragione che vale
	 *    oltre questa riga: una stima puo' sbagliare, un byte in coda no.  La
	 *    banda misurata resta sotto, come **fondo** per i byte gia' consegnati
	 *    a ngtcp2 e non ancora riscontrati — quelli la coda non li vede piu'.
	 *
	 * ⛔ E il tetto vale ANCHE qui, ed e' la ragione per cui esiste: se la
	 *    linea non porta via la chiave, dopo due secondi se ne richiede una
	 *    lo stesso.  Uno schermo fermo per sempre non e' «brutto», e' chiuso a
	 *    meta' (I1). */
	for (size_t i = 0; i < w->ninvolo; i++)
		if (w->involo[i].vivo && w->involo[i].chiave)
			in_coda += coda_byte_stream(w, w->involo[i].stream);
	if (in_coda > 0) {
		*come = "🔸 la CHIAVE precedente non e' ancora uscita (byte in coda)";
		/* ⚠ Il fondo del registro e' lo stesso della strada calcolata: la riga
		 *   la scrive quel ramo, qui basta il tetto. */
		return WT_CHIAVE_TETTO_MS;
	}

	if (!w->chiave_byte) {
		*come = "ripiego: nessuna CHIAVE ancora spedita, la sua misura non esiste";
		return WT_CHIAVE_RICHIESTA_MS;
	}
	memset(&info, 0, sizeof info);
	ngtcp2_conn_get_conn_info(w->conn, &info);
	if (info.smoothed_rtt == 0 || info.cwnd == 0) {
		*come = "ripiego: ngtcp2 non ha ancora ne' rtt ne' finestra";
		return WT_CHIAVE_RICHIESTA_MS;
	}

	/* tempo (ns) = byte × rtt(ns) / cwnd(byte) → ms, piu' il margine.
	 * ⚠ L'ordine dei fattori e' quello che non trabocca: 60 000 × 30 000 000 =
	 *   1,8e12, largamente dentro un `uint64_t`. */
	ms = w->chiave_byte * info.smoothed_rtt / info.cwnd / NGTCP2_MILLISECONDS;
	ms = ms * WT_CHIAVE_MARGINE_PC / 100u;

	if (ms <= WT_CHIAVE_RICHIESTA_MS) {
		*come = "la banda misurata basta: resta il fondo di 150 ms";
		return WT_CHIAVE_RICHIESTA_MS;
	}
	if (ms > WT_CHIAVE_TETTO_MS) {
		*come = "⛔ la banda non basterebbe nemmeno per il tetto: fermo a 2 s, "
		        "e l'immagine resta rotta piu' a lungo";
		ms = WT_CHIAVE_TETTO_MS;
	} else {
		*come = "🔸 dalla banda misurata (cwnd/rtt)";
	}

	/* ⛔ IL PREZZO SI SCRIVE, e una volta sola per ogni volta che cambia: e'
	 *    visibile all'utente (l'immagine resta rotta piu' a lungo) e i prezzi
	 *    visibili li giudica lui.  ⚠ Con un fondo, o a cinquanta battiti al
	 *    secondo questa riga riempirebbe il registro invece di raccontarlo. */
	if (w->chiave_attesa_detta_ms == 0
	    || (ms > w->chiave_attesa_detta_ms
	        ? ms - w->chiave_attesa_detta_ms
	        : w->chiave_attesa_detta_ms - ms) >= 100) {
		w->chiave_attesa_detta_ms = ms;
		registro_dice(REG_RCP,
		              "🔸 %s: la CHIAVE si potra' richiedere ogni %llu ms invece "
		              "di %u — l'ultima misurava %llu byte e la banda MISURATA e' "
		              "%llu kbit/s (cwnd %llu byte / rtt %llu ms, i due numeri "
		              "che ngtcp2 usa per decidere quanto spedire).  ⛔ IL PREZZO: "
		              "su linea stretta l'immagine resta rotta piu' a lungo dopo "
		              "una perdita.  ⭐ In cambio l'audio passa: chiedere la "
		              "chiave nuova prima che la vecchia sia uscita teneva "
		              "`cwnd_left` a zero e distruggeva i datagram (banco 07-b65)",
		              w->provenienza, (unsigned long long)ms,
		              (unsigned)WT_CHIAVE_RICHIESTA_MS,
		              (unsigned long long)w->chiave_byte,
		              (unsigned long long)(info.cwnd * 8ull * NGTCP2_SECONDS
		                                   / info.smoothed_rtt / 1000ull),
		              (unsigned long long)info.cwnd,
		              (unsigned long long)(info.smoothed_rtt / NGTCP2_MILLISECONDS));
	}
	return ms;
}

static void audio_regola(wt *w)
{
	uint32_t l, a;
	uint8_t codec;
	const char *utente;

	if (!w->rcp || w->chiusura >= 0 || w->audio_acceso)
		return;

	/* ⛔ Invariante I3: niente suono prima che `SESSIONE` sia partita.  E' la
	 *    stessa guardia del video, per la stessa ragione — chi non e' passato
	 *    dal validatore non riceve un pixel, e nemmeno un campione. */
	if (!rcp_tela_in_vigore(w->rcp, &l, &a))
		return;

	codec = rcp_audio_negoziato(w->rcp);
	if (codec == 0) {
		if (!w->audio_detto) {
			w->audio_detto = true;
			registro_dice(REG_RCP,
			              "%s: nessun codec audio negoziato (§4.3) — questa "
			              "sessione non ha audio",
			              w->provenienza);
		}
		return;
	}

	utente = rcp_utente(w->rcp);
	if (!utente || !utente[0])
		return;

	w->audio_acceso = true;
	w->audio_codec = codec;
	/* ⛔ E IL TONO DI PROVA SI NOMINA QUI, a ogni sessione — rilievo 8.
	 *    `wt_audio_prova()` scrive una riga sola, all'avvio: chi legge il
	 *    registro un'ora dopo vedeva «canale audio acceso» e **non aveva modo
	 *    di sapere che quel che l'utente sente e' un segnale di banco**.
	 *    L'interruttore di I6 c'era; la dichiarazione che deve seguirlo no. */
	registro_dice(REG_RCP,
	              "⭐ FASE 7: canale audio ACCESO per «%s» da %s — codec %u (%s), "
	              "48 000 Hz, 2 canali (§5.3).  Il pari accetta datagram di %llu "
	              "byte%s",
	              utente, w->provenienza, codec,
	              codec == 1 ? "Opus" : "PCM",
	              (unsigned long long)dgram_tetto_del_pari(w),
	              audio_prova_hz
	                  ? "  ⚠⚠ E QUEL CHE SI SENTIRA' E' IL TONO DI PROVA, non il "
	                    "desktop: `--audio-prova` e' acceso (funzione di banco, I6)"
	                  : "");

	/* ⛔ E si chiede al figlio di catturare — ma NON col tono di prova acceso:
	 *    li' la sorgente e' questo processo, e accendere anche la cattura vera
	 *    vorrebbe dire due sorgenti sullo stesso canale.  ⚠ Il client sentirebbe
	 *    le due mescolate e il banco misurerebbe una scena che il prodotto non
	 *    avra' mai. */
	if (gancio_audio && !audio_prova_hz)
		gancio_audio(gancio_audio_ctx, utente, codec);
}

static void video_regola(wt *w, uint64_t ora_ms)
{
	uint32_t l = 0, a = 0;
	uint8_t codec;
	const char *utente;

	if (!w->rcp || w->chiusura >= 0)
		return;

	/* ⛔ P1 / §2.5 / invariante I3 — «nessuno stream video prima di aver
	 *    SPEDITO `SESSIONE`».  `rcp_tela_in_vigore()` risponde `false` finche'
	 *    `SESSIONE` non e' partita, e non scrive niente nel registro: chiamare
	 *    `rcp_video_apri()` per saperlo riempirebbe il registro di una riga al
	 *    secondo per ogni sessione in attesa della parola d'ordine. */
	if (!rcp_tela_in_vigore(w->rcp, &l, &a))
		return;

	codec = rcp_codec_negoziato(w->rcp);
	if (codec == 0) {
		if (!w->video_detto) {
			/* ⚠ Non e' un difetto: un client della fase 1 non dichiara nessun
			 *   codec, e §4.3 gli da' ragione. */
			w->video_detto = true;
			registro_dice(REG_RCP,
			              "%s: nessun codec negoziato (§4.3) — questa sessione "
			              "non ha video, ed e' quel che la fase 1 faceva",
			              w->provenienza);
		}
		return;
	}

	utente = rcp_utente(w->rcp);
	if (!utente || !utente[0])
		return;

	if (!w->video_acceso) {
		w->video_acceso = true;
		w->video_codec = codec;
		w->chiave_chiesta_ms = ora_ms;
		registro_dice(REG_RCP,
		              "⭐ FASE 3: canale video ACCESO per «%s» da %s — codec %u, "
		              "tela %ux%u.  Chiedo al palco di catturare di continuo, e "
		              "§5.2 vuole che il PRIMO sia una CHIAVE",
		              utente, w->provenienza, codec, l, a);
		if (gancio_palco)
			gancio_palco(gancio_palco_ctx, utente, codec,
			             rcp_profondita_negoziata(w->rcp),
			             rcp_livello_negoziato(w->rcp), true);
		return;
	}

	/* ⛔ E qui la chiave chiesta arriva davvero al codificatore. */
	{
		const char *come = NULL;
		uint64_t attesa = chiave_intervallo_ms(w, &come);

		if (rcp_video_serve_chiave(w->rcp)
		    && ora_ms - w->chiave_chiesta_ms >= attesa) {
			w->chiave_chiesta_ms = ora_ms;
			if (gancio_palco)
				gancio_palco(gancio_palco_ctx, utente, codec,
				             rcp_profondita_negoziata(w->rcp),
				             rcp_livello_negoziato(w->rcp), true);
			registro_dettaglio(REG_RCP,
			                   "%s: §5.2 vuole una CHIAVE — richiesta girata al "
			                   "palco di «%s» (codec %u), dopo %llu ms di attesa "
			                   "(%s)",
			                   w->provenienza, utente, codec,
			                   (unsigned long long)attesa, come);
		}
	}
}

/* ------------------------------------------------------------------------ */
/* ⭐⭐ IL REGOLATORE DEL RITMO — fase 9, e il ritmo scende QUI.              */
/*
 * ⛔ LA REGOLA, INTERA: `arretrato == 0` ⇒ si spedisce; `arretrato >= POSTI`
 *    ⇒ questo fotogramma NON parte.  Nient'altro.  Non c'e' nessun ritmo
 *    target, nessuna banda calcolata, nessun riscontro del client, e
 *    soprattutto nessun numero che debba risalire.
 *
 * ⛔ E LA DISCESA NON E' UN NUMERO CHE SI ABBASSA: e' un fotogramma che non
 *    parte.  Il ritmo cala da se', tanto quanto la coda non si svuota, e
 *    risale da se' quando si svuota — perche' la grandezza si RILEGGE, non si
 *    ricorda.  ⭐ Nessun cricchetto: e' l'errore che `qualita_corrente` ha
 *    fatto (scendeva e non risaliva piu') ed e' costato una cura a parte.
 *
 * ⛔ PERCHE' NON E' UN CRONOMETRO — ed e' la famiglia di errori
 *    P8 → P11 → P13 → P14 → P19 → P20 di `RCP.md`, evitata invece che
 *    ripetuta.  P13 diceva «per un secondo» e fu corretto due ore dopo:
 *    *«il secondo era la grandezza sbagliata: quel che deve svuotarsi e' una
 *    CODA, e quanto ci mette un fotogramma gia' in volo dipende dalla BANDA,
 *    non dall'orologio»*.  P20 diceva «chi riceve un fotogramma prima di
 *    SESSIONE», e la cura fu guardare quel che il pari aveva SPEDITO LUI:
 *    locale, monotono, indipendente dalla consegna.  ⇒ `arretrato` ha
 *    esattamente quella forma dal nostro lato: sono BYTE PRODOTTI DA NOI E
 *    ANCORA IN CASA NOSTRA.  Nessun pacchetto perso, nessun riordino e nessun
 *    silenzio del client possono falsarlo, perche' non si guarda niente che
 *    venga da fuori.  ⭐ E la frase e' gia' nel codice, scritta per la stessa
 *    ragione: *«una stima puo' sbagliare, un byte in coda no»*.
 *
 * ⛔ RIFIUTATA LA GRANDEZZA DI GNOME (i riscontri di fotogramma del client),
 *    e sono tre ragioni indipendenti: (1) da noi NON ESISTONO — la tabella dei
 *    messaggi di `RCP.md` non ha nessun riscontro di fotogramma, e aggiungerlo
 *    vorrebbe dire un giro di rete DENTRO l'anello di controllo, cioe'
 *    comprare reazione pagandola in ritardo (`SPECIFICHE.md:128-131` chiede di
 *    giustificarlo in ms; `arretrato` costa **0 ms**, e' gia' in memoria
 *    nostra); (2) il pari PUO' CONGELARLI e il regolatore si fermerebbe per
 *    sempre — e un anello che il pari puo' congelare non diventa sicuro
 *    perche' si aggiunge un `if`; (3) la loro soglia
 *    (`rtt * refresh_rate / 1e6`) e' un orologio travestito, cioe' P13 con un
 *    altro vestito.
 *
 * ⛔ E LE CHIAVI NON CONTANO — `RCP.md` §5.2 vieta di abbandonarle, §5.1 dice
 *    che i delta che vengono dopo non sono bloccati da loro (gli stream sono
 *    indipendenti), e il loro ritmo ce l'ha gia' `chiave_intervallo_ms()`.
 *    Contarle qui fermerebbe la produzione di delta per tutta la durata di una
 *    chiave lenta, che e' esattamente il contrario di `SPECIFICHE.md` §8.3.
 *
 * ⚠ IL PREZZO IN MILLISECONDI, dichiarato: **0**.  Questo regolatore non
 *   aggiunge nessuna memoria intermedia, quindi non compra fluidita' e non
 *   vende risposta (`SPECIFICHE.md:128-131`).  Toglie lavoro, non lo rimanda.
 *
 * ⚠ IL PREZZO CHE INVECE C'E': si taglia A VALLE del codificatore, quindi il
 *   fotogramma saltato ha gia' pagato la GPU del figlio.  La leva vera — non
 *   catturarlo affatto — sta nel figlio, e ⛔ NON si fa in fase 9 per una
 *   ragione d'architettura: il palco e' UNO per utente e le sessioni sono N,
 *   quindi un ritmo imposto al palco lo imporrebbe a tutte e la sessione sulla
 *   linea buona pagherebbe per quella sulla linea cattiva.  `[?]` aperta.
 *
 * ⛔ IL FONDO DELLA SCALA E' UN VERDETTO, NON UN FRENO.  `DECISIONI.md` §2.1:
 *    la linea e' 20 Mbit/s, l'immagine 480p·25.  Sotto i 25/s su una linea da
 *    20 Mbit/s e' un DIFETTO, non una degradazione riuscita — e la cura NON e'
 *    forzare un fotogramma dentro una coda che non si svuota, perche' quello
 *    peggiora la coda e basta.  ⇒ Non c'e' nessun pavimento in questo codice:
 *    c'e' il conto `video_ritmo_scesi` accanto ai fotogrammi consegnati, e chi
 *    legge il registro DICHIARA il difetto invece di combatterlo.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⛔⭐⭐ LA PREVISIONE FALSIFICABILE — scritta PRIMA di qualunque misura.
 * ───────────────────────────────────────────────────────────────────────────
 *
 * ⭐ QUESTO E' UN PARAPETTO, E IL SUO COMPORTAMENTO CORRETTO E' NON FARE
 *    NIENTE.  Un banco che dimostrasse solo che non scatta avrebbe dimostrato
 *    meta' del lavoro; l'altra meta' e' dimostrare che l'anello e' stato
 *    PERCORSO mentre non scattava.
 *
 * 1. IN REGIME, a 20 Mbit/s sul percorso vero, scena mossa, 1080p, H.264
 *    hardware, coi predefiniti del 24 ago 2026 (soglia 100 ms + regolatore):
 *
 *      | fotogrammi consegnati | **20-37/s** — quelli che la scena produce |
 *      | byte in uscita        | **3-12 Mbit/s**, fra un sesto e la meta'  |
 *      | `arretrato`           | **0, ogni tanto 1.  Mai 2**               |
 *      | `video_ritmo_scesi`   | ⭐ **0** — zero discese                   |
 *
 * 2. SUL GRADINO — ed e' dove deve scattare.  Stesso gradino gia' misurato:
 *    linea larga → **3 s a 10 Mbit/s** → larga, scena `barra`, 1920x1080.
 *
 *      | `arretrato` durante i 3 s   | sale a **2-3**                     |
 *      | discese (`ritmo_scesi`)     | **> 0**, e concentrate nei 3 s     |
 *      | righe di registro           | **2 per episodio** (SCENDE/RISALE),|
 *      |                             | NON una per fotogramma             |
 *      | fotogrammi/s nei 3 s        | **>= 25** e fatti di DELTA         |
 *      | di cui CHIAVE, al secondo   | **<= 2** (senza regolatore: 6-7)   |
 *      | secondi di linea larga      | **identici** a oggi: inerte        |
 *      | il RISALE, dopo il gradino  | entro **1 s** dal ritorno          |
 *
 * 3. ⛔ CHE NON CALA A SCENA FERMA — e il controllo NON puo' essere «il
 *    contatore e' zero»: vuoto e proibito hanno la stessa faccia
 *    (`LEZIONI.md` §1.9), e uno zero su un ramo mai raggiunto non dimostra
 *    niente.  ⭐ La dimostrazione strutturale viene prima: `arretrato` si
 *    legge SOLO all'arrivo di un fotogramma dal palco, e a scena ferma un
 *    compositore Wayland non ne consegna nessuno — `video_a_una()` non viene
 *    nemmeno chiamata.  Una grandezza che misurasse byte/s, o ms di CPU, o
 *    «da quanto non spedisco» sarebbe invece perfettamente capace di scendere
 *    su un desktop immobile, ed e' la ferita di v1 (*«su un desktop poco mosso
 *    scendeva a 2-6 Mbit/s, contento di risparmiare»*).
 *
 *    ⇒ IL CONTROLLO SPERIMENTALE SI FA A COPPIE, NELLO STESSO GIRO: meta'
 *    scena ferma e meta' scena mossa, ALTERNATE, non due giri separati.  E la
 *    riga che lo rende leggibile e' quella di `ritmo_ciclo()`, una al secondo,
 *    che esce anche quando di fotogrammi non ne arriva nessuno.  ⭐ La forma
 *    esatta, ed e' un contratto sul testo:
 *
 *      ritmo di IND:PORTA: arretrato LETTO 0 volte in quest'ultimo secondo,
 *      massimo 0, ultimo 0, posti 2 — 0 fotogrammi non partiti in questo
 *      secondo, 0 in tutto.  ⚠ ZERO LETTURE = il palco non ha consegnato
 *      niente (scena ferma), e NON «arretrato zero»
 *
 *    Il verde e': `video_ritmo_scesi` INVARIATO per tutta la meta' ferma —
 *    con le righe che dicono «LETTO 0 volte», cioe' che il ramo non e' stato
 *    percorso — E `arretrato` letto almeno una volta al secondo nella meta'
 *    mossa.  ⛔ Un giro che non soddisfa il secondo punto NON HA MISURATO
 *    NIENTE, e va buttato invece che interpretato.
 *
 * ⛔ I ROSSI CHE MI SMENTIREBBERO, e ognuno dice dove guardare:
 *
 *  a. **discese a 20 Mbit/s con un desktop normale** ⇒ o `POSTI = 2` e'
 *     troppo stretto, o un fotogramma costa molto piu' del misurato.  La riga
 *     porta `cwnd`, `cwnd_left`, byte in volo e byte in coda: dice da se'
 *     quale dei due;
 *  b. ⛔⛔ **discese con la finestra di congestione LARGA** (`cwnd_left` alto)
 *     ⇒ NON E' LA LINEA, e' il BROWSER: e' la sua finestra di flusso
 *     (`initial_max_stream_data_uni` / `initial_max_data`, che decide lui e
 *     noi non tocchiamo) oppure il pacer.  La cura sarebbe altrove e questo
 *     regolatore starebbe frenando per un difetto che non e' suo.  E' il rosso
 *     piu' importante, perche' produce un anello che SEMBRA lavorare bene;
 *  c. **`video_saltati` che cresce mentre `arretrato` resta 0** ⇒ il collo e'
 *     il credito di stream (§2.3, la causa 4 del debito), non la banda, e
 *     questo regolatore non c'entra: si guarda `sgombra_credito`;
 *  d. **zero discese e ZERO LETTURE nella meta' mossa** ⇒ non e' una
 *     previsione confermata, e' un anello mai percorso.  Quasi certamente la
 *     soglia della coda e' spenta (vedi `wt_ritmo_adattivo()`);
 *  e. **il RISALE non arriva mai dopo il ritorno della linea** ⇒ qualcosa
 *     trattiene byte in coda che non se ne vanno, e non e' il ritmo: si guarda
 *     la punta di `byte_in_volo` e gli stream mai chiusi.
 *
 * ⇒ Ritorna `true` quando questo fotogramma NON deve partire.
 */
static bool ritmo_frena(wt *w, bool chiave, uint64_t ora_ms)
{
	unsigned arretrato = 0;
	size_t in_coda = 0;

	if (!ritmo_adattivo)
		return false;
	/* ⛔ Le chiavi non passano di qui: §5.2 e `chiave_intervallo_ms()`. */
	if (chiave)
		return false;

	/* ⛔ SI LEGGE PRIMA DI `video_sgombra()`, che poche righe piu' sotto quella
	 *    coda la svuota: dopo, `arretrato` sarebbe sempre zero e questo anello
	 *    non scatterebbe mai.  ⚠ `coda_byte_stream()` conta i byte che non sono
	 *    ANCORA usciti da casa nostra — un elemento gia' consegnato a ngtcp2 ha
	 *    `off == dati.n` e vale zero, anche se dopo la cura del 23 agosto la sua
	 *    memoria e' ancora nostra.  ⇒ La grandezza e' rimasta quella. */
	for (size_t i = 0; i < w->ninvolo; i++) {
		size_t resto;
		if (!w->involo[i].vivo || w->involo[i].chiave)
			continue;
		resto = coda_byte_stream(w, w->involo[i].stream);
		if (resto == 0)
			continue;
		in_coda += resto;
		arretrato++;
	}

	/* ⭐ LA LETTURA SI CONTA, sempre, anche quando vale zero: e' quel che
	 *    distingue «l'anello e' stato percorso e l'arretrato era zero» da
	 *    «l'anello non e' stato percorso affatto» (`LEZIONI.md` §1.9). */
	w->ritmo_letture++;
	w->ritmo_ultimo = arretrato;
	if (arretrato > w->ritmo_max)
		w->ritmo_max = arretrato;

	if (arretrato >= WT_RITMO_POSTI) {
		if (!w->ritmo_giu) {
			ngtcp2_conn_info in;
			uint64_t rtt_ms;
			char rete[96];

			memset(&in, 0, sizeof in);
			ngtcp2_conn_get_conn_info(w->conn, &in);
			rtt_ms = in.smoothed_rtt / NGTCP2_MILLISECONDS;
			/* ⛔⭐ `smoothed_rtt - min_rtt` E' LA CODA DENTRO LA RETE, IN
			 *     MILLISECONDI: e' il numero con cui `SPECIFICHE.md:128` —
			 *     «ogni memoria intermedia compra fluidita' e vende risposta» —
			 *     si onora invece di citarlo.  ⚠ Ed e' la prima volta che
			 *     `min_rtt` viene letto: `ngtcp2_conn_get_conn_info()` la
			 *     riempie da sempre e noi ne guardavamo due campi su sette.
			 *
			 * ⛔ MA `min_rtt` VALE `UINT64_MAX` FINCHE' NON E' ARRIVATO UN
			 *    CAMPIONE, e la sottrazione darebbe un numero enorme che SEMBRA
			 *    misurato — forma E1, la peggiore.  ⇒ Si dichiara «non ancora
			 *    noto» invece di stampare spazzatura. */
			if (in.min_rtt != UINT64_MAX && in.min_rtt != 0
			    && in.smoothed_rtt >= in.min_rtt)
				snprintf(rete, sizeof rete,
				         "%llu ms di coda dentro la rete (rtt %llu - min %llu)",
				         (unsigned long long)((in.smoothed_rtt - in.min_rtt)
				                              / NGTCP2_MILLISECONDS),
				         (unsigned long long)rtt_ms,
				         (unsigned long long)(in.min_rtt / NGTCP2_MILLISECONDS));
			else
				snprintf(rete, sizeof rete,
				         "coda dentro la rete NON ANCORA NOTA (min_rtt manca)");
			w->ritmo_giu   = true;
			w->ritmo_da_ms = ora_ms;
			w->ritmo_da_n  = w->video_ritmo_scesi;
			/* ⛔⭐ INVARIANTE I1: «il ritmo non cala mai per prudenza, per
			 *     risparmio o perche' la scena e' ferma.  Cala solo quando la
			 *     MISURA dimostra che la linea non porta, e ogni discesa e'
			 *     dichiarata nel registro».
			 *
			 * ⭐ E LA RIGA PORTA LA MISURA ACCANTO ALLA SOGLIA: `arretrato` e i
			 *    posti, uno accanto all'altro.  Se la misura fosse sotto la
			 *    soglia, quella discesa sarebbe stata per prudenza — e la riga
			 *    stessa lo dimostrerebbe, invece di lasciarlo dedurre.
			 *
			 * ⚠ UNA RIGA PER EPISODIO, non per fotogramma: a 60/s la seconda
			 *   forma e' il difetto dei 30,8 GB di registro. */
			registro_dice(REG_RCP,
			              "⛔ %s: il ritmo SCENDE — arretrato %u delta contro %u "
			              "posti, %zu byte fermi nella coda del video (%zu in "
			              "tutto).  cwnd %llu, cwnd_left %llu, in volo per ngtcp2 "
			              "%llu, miei consegnati e non riscontrati %zu, rtt %llu "
			              "ms, %s.  ⭐ Non e' prudenza e non e' un orologio: e' la "
			              "coda che non si svuota (I1).  ⚠ Se cwnd_left e' ALTO "
			              "non e' la linea, e' la finestra del browser",
			              w->provenienza, arretrato, (unsigned)WT_RITMO_POSTI,
			              in_coda, w->byte_in_coda,
			              (unsigned long long)in.cwnd,
			              (unsigned long long)ngtcp2_conn_get_cwnd_left(w->conn),
			              (unsigned long long)in.bytes_in_flight,
			              w->byte_in_volo,
			              (unsigned long long)rtt_ms, rete);
		}
		w->video_ritmo_scesi++;
		return true; /* ⛔ questo fotogramma NON parte: E' la discesa */
	}

	/* ⭐ E LA FINE DELL'EPISODIO NON LA DECIDE NESSUNO: la coda si e' svuotata
	 *    e l'arretrato e' tornato a zero.  Non c'e' nessun numero da rialzare,
	 *    nessuna isteresi e nessun ritardo di risalita — e' il pregio della
	 *    grandezza che si rilegge invece di ricordarsi. */
	if (w->ritmo_giu && arretrato == 0) {
		w->ritmo_giu = false;
		registro_dice(REG_RCP,
		              "⭐ %s: il ritmo RISALE — l'episodio e' durato %llu ms e sono "
		              "restati indietro %u fotogrammi.  ⚠ Non l'ha deciso nessuno: "
		              "la coda si e' svuotata e l'arretrato e' zero",
		              w->provenienza,
		              (unsigned long long)(ora_ms - w->ritmo_da_ms),
		              w->video_ritmo_scesi - w->ritmo_da_n);
	}
	return false;
}

/* ⛔⭐ LA RIGA AL SECONDO CHE RENDE FALSIFICABILE «non cala a scena ferma».
 *
 *     Gira col BATTITO e non coi fotogrammi, apposta: se girasse coi
 *     fotogrammi, a scena ferma non uscirebbe niente — e «l'anello non e'
 *     stato percorso» avrebbe di nuovo la stessa faccia di «l'arretrato era
 *     zero», che e' precisamente il difetto che questa riga esiste per togliere
 *     (`LEZIONI.md` §1.9; ed e' la stessa cura della riga `ciclo:` del figlio,
 *     che si scrive PRIMA di guardare l'esito della cattura).
 *
 * ⚠ Esce solo con l'interruttore acceso: e' lo strumento di un banco, non una
 *   riga di prodotto, e a sessione ferma sarebbe una riga al secondo per
 *   sempre. */
static void ritmo_ciclo(wt *w, uint64_t ora_ms)
{
	if (!ritmo_adattivo || !w->rcp || w->chiusura >= 0)
		return;
	if (ora_ms - w->ritmo_detto_ms < 1000)
		return;
	w->ritmo_detto_ms = ora_ms;
	registro_dice(REG_RCP,
	              "ritmo di %s: arretrato LETTO %u volte in quest'ultimo secondo, "
	              "massimo %u, ultimo %u, posti %u — %u fotogrammi non partiti in "
	              "questo secondo, %u in tutto.  ⚠ ZERO LETTURE = il palco non ha "
	              "consegnato niente (scena ferma), e NON «arretrato zero»",
	              w->provenienza, w->ritmo_letture, w->ritmo_max, w->ritmo_ultimo,
	              (unsigned)WT_RITMO_POSTI,
	              w->video_ritmo_scesi - w->ritmo_detti_n, w->video_ritmo_scesi);
	w->ritmo_letture = 0;
	w->ritmo_max = 0;
	w->ritmo_detti_n = w->video_ritmo_scesi;
}

/* ========================================================================== */
/* ⛔⭐⭐ FASE 9 — LA RIGA CHE ATTRIBUISCE IL RITARDO A CHI SE L'E' PRESO.     */
/*                                                                            */
/*      IL BUCO CHE CHIUDE.  Un fotogramma che arriva tardi ha quattro padri  */
/*      possibili, e fino a questa riga il registro ne sapeva riconoscere     */
/*      solo due:                                                             */
/*                                                                            */
/*        (a) un pacchetto perduto e rimandato da QUIC   ⛔ NON SI VEDEVA     */
/*        (b) la finestra di congestione che si e' chiusa ⛔ NON SI VEDEVA    */
/*        (c) noi che l'abbiamo tenuto in coda            ✅ `sgombra_tenuti`  */
/*        (d) noi che l'abbiamo abbandonato               ✅ `sgombra_abbandoni`*/
/*                                                                            */
/*      ⇒ Senza (a) e (b) ogni misura sotto perdita finisce in una discussione*/
/*      — «e' la linea o siamo noi?» — invece che in un'attribuzione.  E il   */
/*      progetto ha una regola: ogni numero va attribuito da se'.             */
/*                                                                            */
/* ⛔⛔ E' SOLO OSSERVAZIONE.  Questa funzione LEGGE e SCRIVE, e basta:       */
/*      nessuna decisione, nessuna soglia, nessun ritmo, nessuno stato di     */
/*      trasporto toccato.  ⇒ Non c'e' niente da mettere dietro un            */
/*      interruttore (invariante I6), perche' non cambia niente di quel che   */
/*      l'utente VEDE.  Se un giorno servisse cambiare qualcosa per poterla   */
/*      scrivere, quella e' un'altra cura e va dietro un interruttore spento. */
/*                                                                            */
/* ⭐ LA RIGA D'ESEMPIO — ED E' UN CONTRATTO SUL TESTO, perche' e' quella che */
/*    un banco cerchera' con un `grep` e spezzera' con uno `split`:           */
/*                                                                            */
/*      rete-quic 192.168.1.9:52344 da_ms=1002 persi=7 persi_d=3              */
/*      byte_persi=9856 byte_persi_d=4224 spediti=48210 spediti_d=812         */
/*      byte_spediti=59284410 ricevuti=3011 ricevuti_d=61 scartati=0          */
/*      scartati_d=0 cwnd=48000 cwnd_left=0 ssthresh=32000 involo=47180       */
/*      srtt_us=41230 latest_us=52980 rttvar_us=11400 min_rtt_us=22100        */
/*      coda_rete_us=19130 pto_us=132000 dgram_persi=n/d                      */
/*      giudizio=⛔ la linea perde                                            */
/*                                                                            */
/*    (nel registro e' TUTTA SU UNA RIGA: qui va a capo solo per starci nel   */
/*    riquadro.)  Le regole del formato, e sono tre:                          */
/*                                                                            */
/*      1. il prefisso `rete-quic` e' STABILE ed e' la prima parola del corpo:*/
/*         `grep 'rete-quic '` prende tutte le righe e nient'altro;           */
/*      2. ogni campo e' `nome=valore` senza spazi nel valore, separato da UNO*/
/*         spazio — `split()` e poi `split('=', 1)` bastano.  Il secondo campo*/
/*         non ha `=` ed e' la provenienza (IND:PORTA), che di spazi non ne ha;*/
/*      3. ⛔ `giudizio=` E' L'ULTIMO CAMPO, e il suo valore arriva a FINE     */
/*         RIGA spazi compresi: e' l'unico che ne contiene, apposta, perche'  */
/*         dev'essere leggibile da un umano senza trattini finti.  Un banco lo*/
/*         prende con `riga.split('giudizio=', 1)[1]`.                        */
/*                                                                            */
/* ⚠ LE UNITA' STANNO NEI NOMI, e l'rtt e' in MICROsecondi mentre il resto    */
/*   del file lo stampa in millisecondi.  Non e' distrazione: il bersaglio    */
/*   della fase e' il jitter, e `rttvar` su una rete locale sta sotto il      */
/*   millisecondo — arrotondato a ms varrebbe `0` e nasconderebbe proprio il  */
/*   fatto che si sta cercando.  ⇒ `_us` sul nome, e chi legge non sbaglia.   */
/*                                                                            */
/* ⚠ `da_ms` E' L'INTERVALLO VERO, e i campi `_d` valgono SU QUELLO — non «al */
/*   secondo».  La riga esce al piu' una volta al secondo, ma tace quando non */
/*   e' cambiato niente: dopo un silenzio di 12 s il `da_ms` dice 12000 e le  */
/*   differenze coprono 12 s.  ⛔ Chiamarli `_1s` sarebbe stato un numero che */
/*   SEMBRA misurato e non lo e' — la forma E1.  Sulla PRIMA riga `da_ms=0` e */
/*   le differenze valgono i totali, cioe' tutta la connessione.              */
/*                                                                            */
/* ⛔ CHE COSA NON C'E', e va detto qui perche' un campo assente si nota e un */
/*    campo mancante no:                                                      */
/*                                                                            */
/*    · **i RITRASMESSI non esistono in ngtcp2 1.25** `[S]`.  QUIC non        */
/*      ritrasmette pacchetti — ritrasmette i FRAME dentro pacchetti nuovi —  */
/*      e `ngtcp2_conn_info` non ha nessun contatore di rimandi.  `pkt_lost`  */
/*      (`persi`) e' quanto ci si avvicina: i pacchetti DICHIARATI perduti.   */
/*    · **il riordino non si conta SUGLI STREAM** `[S]`: nessun campo,        */
/*      nessun callback, e ngtcp2 usa la soglia dei 3 pacchetti al suo        */
/*      interno senza esporla.  ⇒ Li' `rttvar_us` resta l'unico indizio di    */
/*      jitter, e questa riga lo porta senza giudicarlo.                      */
/*    · ⭐⭐⭐ **MA SUI DATAGRAM IL RIORDINO SI MISURA** — 23 agosto 2026.      */
/*      `ngtcp2.h:3442`: *«the loss might be spurious, and DATAGRAM frame     */
/*      might be acknowledged later»*.  ⇒ Stesso `dgram_id` prima in          */
/*      `lost_datagram` e poi in `ack_datagram` = perdita FALSA = pacchetto   */
/*      arrivato fuori sequenza.  E' `dgram_falsi`, ed e' il solo numero che  */
/*      il server sappia dare sul bersaglio «fuori sequenza» della fase 9.    */
/*      ⚠ Vale sull'AUDIO soltanto: gli stream non hanno un identificativo    */
/*      per pezzo, e questa strada li' non c'e'.  Il prezzo si dichiara.      */
/*    · **`delivery_rate` non esiste** `[S]` in ngtcp2 1.25: la banda si      */
/*      stima da `cwnd`/`smoothed_rtt` come gia' fa `chiave_intervallo_ms()`. */
/* ========================================================================== */

/* ⭐ I TRE GIUDIZI, e la regola che li sceglie sta tutta in `rete_ciclo()`.
 *    Sono numeri e non stringhe solo per poter dire «il giudizio e' cambiato»
 *    a contatori fermi, che e' un fatto che merita una riga. */
#define WT_RETE_NULLA    0
#define WT_RETE_FINESTRA 1
#define WT_RETE_PERDE    2

/* ⭐⭐ I DUE ESITI DI UN DATAGRAM, E LI CHIAMA `trasporto.c` DA NGTCP2.
 *
 *    ⛔ Fino al 23 agosto 2026 `ngtcp2_callbacks` non registrava ne'
 *       `lost_datagram` ne' `ack_datagram`: l'audio partiva e il suo destino
 *       era **muto**.  «L'audio non arriva» e «l'audio arriva e il cliente lo
 *       butta» avevano la stessa faccia — che e' lo stesso rilievo B-10 che
 *       aveva gia' fatto contare i datagram in ENTRATA.
 *
 * ⚠ NON DECIDONO NIENTE: contano e basta.  Nessuna soglia, nessun ritmo,
 *   nessun interruttore da tenere spento (I6), perche' non cambia niente di
 *   quel che l'utente vede.
 */
void wt_dgram_perso(wt *w, uint64_t id)
{
	if (!w)
		return;
	w->dgram_persi++;
	/* ⛔ Si scrive sempre, anche sopra un identificativo non ancora
	 *    riscontrato: l'anello e' una memoria RECENTE, non un elenco. */
	w->dgram_anello[w->dgram_anello_i] = id;
	w->dgram_anello_i = (w->dgram_anello_i + 1) % WT_DGRAM_ANELLO;
}

void wt_dgram_riscontrato(wt *w, uint64_t id)
{
	unsigned i;

	if (!w)
		return;
	w->dgram_riscontrati++;
	/* ⭐ Il fatto che conta: era stato DICHIARATO perduto, ed eccolo.
	 *    ⇒ Non era perduto: era in ritardo.  E' riordino, misurato. */
	for (i = 0; i < WT_DGRAM_ANELLO; i++) {
		if (w->dgram_anello[i] != id)
			continue;
		w->dgram_falsi++;
		/* ⛔ Si consuma, o un secondo riscontro dello stesso
		 *    identificativo lo conterebbe due volte. */
		w->dgram_anello[i] = 0;
		return;
	}
}

/* ========================================================================== */
/* ⛔⭐⭐ IL GIUDIZIO SULLA LINEA MORTA — la derivazione dei numeri sta sopra   */
/*      `WT_LM_STALLO_MS`, e qui c'e' solo il meccanismo.                     */
/*                                                                            */
/* ⛔ LA RIGA DEL REGISTRO E' UN CONTRATTO — invariante I1, «ogni discesa e'   */
/*    dichiarata», e questa non e' una discesa: e' una sessione CHIUSA.  Una   */
/*    sessione che sparisce senza una riga che porti i numeri su cui si e'     */
/*    deciso e' indistinguibile da un difetto NOSTRO.  Le regole del formato   */
/*    sono le stesse di `rete-quic` (il riquadro sopra):                       */
/*                                                                            */
/*      1. il prefisso `linea-morta` e' STABILE ed e' la prima parola del      */
/*         corpo; il secondo campo e' la provenienza (IND:PORTA), senza `=`;   */
/*      2. ogni campo e' `nome=valore` senza spazi nel valore;                 */
/*      3. ⛔ `giudizio=` E' L'ULTIMO e arriva a fine riga, spazi compresi.    */
/*                                                                            */
/*    ⛔ E I CAMPI CI SONO SEMPRE TUTTI, anche quelli che la causa in corso non */
/*       usa: un banco che facesse `split('=')` su una riga a geometria        */
/*       variabile leggerebbe il campo sbagliato senza accorgersene.  Quale    */
/*       delle due cause ha deciso lo dice `causa=`, che e' il PRIMO campo.    */
/*                                                                            */
/* ⛔⛔ IL CONTRATTO E' CAMBIATO IL 23 AGOSTO 2026, e il banco `09-b81` va      */
/*      rifatto su questo.  Due campi sono SPARITI e non si tace sul perche':  */
/*                                                                            */
/*      · `soglia_permille=` — non esiste piu' nessuna soglia sulla perdita.   */
/*        `permille=` invece RESTA, ed e' l'osservazione del riordino.  Un     */
/*        campo `soglia_` accanto a un numero che non giudica sarebbe una      */
/*        decisione che nessuno prende, cioe' la forma E1.                     */
/*      · `finestre=N/M` — non ci sono piu' finestre cattive da contare di     */
/*        fila: lo stallo e' una durata continua, e la sua evidenza e' la      */
/*        durata stessa, non la ripetizione.                                   */
/*                                                                            */
/*    ⭐ E ne sono entrati quattro: `stallo_ms=` `soglia_stallo_ms=`           */
/*       `offerti=` `usciti_byte=` `coda_video=` `cwnd_left=`.  I tre di mezzo */
/*       sono i tre numeri su cui lo stallo si dimostra o si smentisce: quanti */
/*       fotogrammi il palco ci ha dato, quanti byte di video sono usciti      */
/*       davvero, e quanti sono rimasti in casa nostra.                        */
/* ========================================================================== */

static void linea_morta_scatta(wt *w, const ngtcp2_conn_info *in,
                               const char *causa, uint64_t stallo_ms,
                               uint64_t offerti, uint64_t usciti,
                               uint64_t coda_video, uint64_t silenzio_ms,
                               uint64_t prove, const char *detto)
{
	static const uint8_t motivo[] = "linea morta";

	w->lm_scattata = true;
	registro_dice(REG_WT,
	              "linea-morta %s causa=%s stallo_ms=%llu soglia_stallo_ms=%llu "
	              "offerti=%llu usciti_byte=%llu coda_video=%llu "
	              "silenzio_ms=%llu soglia_silenzio_ms=%llu prove=%llu "
	              "minimo_prove=%u persi=%llu spediti=%llu permille=%u "
	              "finestra_ms=%llu minimo_pacchetti=%u cwnd=%llu "
	              "cwnd_left=%llu srtt_us=%llu giudizio=%s",
	              w->provenienza, causa,
	              (unsigned long long)stallo_ms,
	              (unsigned long long)linea_morta_stallo_ms,
	              (unsigned long long)offerti, (unsigned long long)usciti,
	              (unsigned long long)coda_video,
	              (unsigned long long)silenzio_ms,
	              (unsigned long long)linea_morta_silenzio_ms,
	              (unsigned long long)prove, (unsigned)WT_LM_MIN_PROVE,
	              (unsigned long long)w->lm_persi_v,
	              (unsigned long long)w->lm_spediti_v, w->lm_permille,
	              (unsigned long long)w->lm_durata_v,
	              (unsigned)WT_LM_MIN_PACCHETTI,
	              (unsigned long long)in->cwnd,
	              (unsigned long long)ngtcp2_conn_get_cwnd_left(w->conn),
	              (unsigned long long)(in->smoothed_rtt / NGTCP2_MICROSECONDS),
	              detto);
	/* ⛔⭐ IL MOTIVO SI SCRIVE NELL'ERRORE DELLA CONNESSIONE, e non si INVENTA
	 *     un motivo RCP nuovo: `RCP.md` §9 vieta di aggiungere un codice a
	 *     §8.2 dentro una versione maggiore, e nessuno dei sedici dice «la
	 *     linea e' morta».  ⇒ Codice `H3_NO_ERROR` (0x0100) — al livello di
	 *     HTTP/3 non c'e' nessun errore, e' il FILO che non porta piu' — e la
	 *     ragione viaggia nella stringa, che e' il posto che QUIC le da'.
	 *
	 * ⚠ E non e' la strada di §3.1 punto 3 (la capsula di chiusura della
	 *   sessione WebTransport) apposta: quella vuole che la coda si svuoti e
	 *   aspetta fino a 3 s su una linea che per ipotesi NON PORTA.  Qui il filo
	 *   cade — e' quel che l'utente ha scelto di far vedere. */
	if (w->ultimo_errore)
		ngtcp2_ccerr_set_application_error(w->ultimo_errore,
		                                   NGHTTP3_H3_NO_ERROR, motivo,
		                                   sizeof motivo - 1);
}

static void linea_morta_giudica(wt *w, const ngtcp2_conn_info *in,
                                uint64_t ora_ms)
{
	uint64_t spediti, persi, prove, fermo_da, stallo;
	uint64_t coda_video, offerti, usciti;
	bool avevo_da_mandare;

	/* ⛔ Spenta = il prodotto di ieri byte per byte (I6).  E una volta scattata
	 *    non si giudica piu': la connessione sta gia' cadendo, e una seconda
	 *    riga direbbe la stessa cosa due volte. */
	if (!linea_morta_accesa || w->lm_scattata)
		return;
	/* ⛔ Solo con una sessione RCP viva: prima non c'e' niente da buttare
	 *    fuori, e in chiusura il motivo l'ha gia' scelto qualcun altro. */
	if (!w->rcp || w->chiusura >= 0)
		return;

	/* ⛔ Il primo giro FOTOGRAFA e non giudica: senza questa riga la prima
	 *    finestra sarebbe lunga quanto tutta la connessione, e lo stallo
	 *    partirebbe da un istante che non e' mai stato guardato. */
	if (!w->lm_finestra_ms) {
		w->lm_finestra_ms = ora_ms;
		w->lm_pkt_sent = in->pkt_sent;
		w->lm_pkt_lost = in->pkt_lost;
		w->lm_vivo_ms = ora_ms;
		w->lm_pkt_recv = in->pkt_recv;
		w->lm_pkt_sent_vivo = in->pkt_sent;
		w->lm_uscita_ms = ora_ms;
		w->lm_usciti_visti = w->lm_usciti;
		w->lm_offerti_visti = w->lm_offerti;
		return;
	}

	/* ── 1. IL TESTIMONE: LA FRAZIONE DI PERDITA ─────────────────────────
	 * ⛔⛔ E NON GIUDICA PIU' NIENTE — 23 agosto 2026, la refuta e' scritta per
	 *      intero nel riquadro sopra `WT_LM_STALLO_MS`.  Il numero si CALCOLA
	 *      ancora, con le stesse guardie di prima, e finisce nella riga dello
	 *      scatto come `permille=`: su una linea che riordina e' la miglior
	 *      misura di RIORDINO che il server abbia sugli stream, dove
	 *      `dgram_falsi` (§17.3) non arriva.
	 *
	 * ⚠ Le guardie restano perche' un testimone che mente e' peggio di un
	 *   testimone che tace: sotto `WT_LM_MIN_PACCHETTI` spediti la finestra
	 *   NON si chiude, si allunga — una frazione su venti pacchetti non e' una
	 *   frazione, e' rumore.  ⭐ E il minimo e' sui pacchetti che mandiamo NOI,
	 *   che e' la direzione abbondante di questa sessione (video in giu', quasi
	 *   niente in su). */
	if (ora_ms - w->lm_finestra_ms >= WT_LM_FINESTRA_MS) {
		spediti = in->pkt_sent - w->lm_pkt_sent;
		if (spediti >= WT_LM_MIN_PACCHETTI) {
			persi = in->pkt_lost - w->lm_pkt_lost;
			/* ⛔ La durata VERA della finestra, presa prima di chiuderla: e' il
			 *    numero che dice se il minimo dei pacchetti l'ha allungata, e
			 *    con la costante al suo posto quella riga direbbe sempre 1000 —
			 *    cioe' un numero che SEMBRA misurato (forma E1). */
			w->lm_durata_v = ora_ms - w->lm_finestra_ms;
			w->lm_persi_v = persi;
			w->lm_spediti_v = spediti;
			w->lm_permille = (unsigned)(persi * 1000 / spediti);
			/* La finestra si chiude qui, e la prossima parte da adesso. */
			w->lm_finestra_ms = ora_ms;
			w->lm_pkt_sent = in->pkt_sent;
			w->lm_pkt_lost = in->pkt_lost;
		}
	}

	/* ── 2. LE DUE META' DELLO STALLO, LETTE UNA VOLTA SOLA ───────────────
	 * ⛔ Si leggono PRIMA di qualunque scatto e prima del proprio azzeramento,
	 *    perche' le porta anche la riga del SILENZIO: una sessione chiusa per
	 *    silenzio con `offerti=` e `usciti_byte=` presi dopo l'azzeramento
	 *    direbbe sempre zero, cioe' un numero che sembra misurato e non lo e'.
	 *
	 * ⭐ `offerti` e `usciti_byte` sono DIFFERENZE da quando il conto dello
	 *    stallo e' ripartito l'ultima volta, non totali di sessione: la
	 *    grandezza e' «da quanto tempo», e i totali risponderebbero a un'altra
	 *    domanda. */
	coda_video = coda_byte_video(w);
	offerti = w->lm_offerti - w->lm_offerti_visti;
	usciti = w->lm_usciti - w->lm_usciti_visti;
	/* ⛔⭐ «AVEVO DA MANDARE» — ed e' la meta' che tiene in piedi l'altra.
	 *     Due termini, e ognuno copre un buco dell'altro:
	 *       · `coda_video > 0` — dei byte di fotogrammi sono ancora in casa
	 *         nostra, quindi il filo li sta trattenendo;
	 *       · `offerti > 0` — il palco ci ha dato un fotogramma da quando il
	 *         conto e' ripartito.  ⛔ Senza questo, il REGOLATORE DEL RITMO
	 *         nasconderebbe lo stallo: smette di produrre, `video_sgombra()`
	 *         abbandona i delta vecchi, la coda si svuota, e «non ho niente da
	 *         mandare» diventerebbe vero mentre lo schermo e' fermo. */
	avevo_da_mandare = coda_video > 0 || offerti > 0;
	stallo = ora_ms - w->lm_uscita_ms;

	/* ── 3. IL SILENZIO ──────────────────────────────────────────────────
	 * ⛔ La grandezza NON e' «quanto tempo e' passato»: e' «quanti pacchetti
	 *    nostri sono usciti senza che ne tornasse UNO».  Il tempo e' solo la
	 *    finestra in cui si guarda, e da solo non basterebbe — un desktop fermo
	 *    in cui non parla nessuno dei due tace legittimamente.
	 * ⚠ E questa cura NON si tocca: `[M]` 23 agosto 2026 ha passato la sua
	 *   prova — `kill -9` sul cliente, scatto a `silenzio_ms=10002` con
	 *   `prove=10`, 10,36 s dopo il colpo; a cura spenta, zero scatti. */
	if (in->pkt_recv > w->lm_pkt_recv) {
		w->lm_vivo_ms = ora_ms;
		w->lm_pkt_recv = in->pkt_recv;
		w->lm_pkt_sent_vivo = in->pkt_sent;
	} else if (linea_morta_silenzio_ms) {
		fermo_da = ora_ms - w->lm_vivo_ms;
		prove = in->pkt_sent - w->lm_pkt_sent_vivo;
		if (fermo_da >= linea_morta_silenzio_ms && prove >= WT_LM_MIN_PROVE) {
			linea_morta_scatta(
				w, in, "silenzio", stallo, offerti, usciti, coda_video,
				fermo_da, prove,
				"⛔ la linea e' MORTA: il client non fa vedere un pacchetto da "
				"troppo tempo e le domande che gli abbiamo fatto nel frattempo "
				"sono rimaste tutte senza risposta.  Il filo cade, e per "
				"tornare bisogna rientrare a mano (decisione dell'utente, 23 "
				"agosto 2026)");
			return;
		}
	}

	/* ── 4. LO STALLO DELL'USCITA ────────────────────────────────────────
	 * ⛔ Il conto RIPARTE per due ragioni diverse che vanno trattate uguale:
	 *      1. e' uscito qualcosa (`usciti > 0`) — il filo porta;
	 *      2. non c'era niente da mandare — e allora non c'e' niente di rotto.
	 *    ⭐ La seconda e' il caso della SCENA FERMA, che in questa fase e'
	 *       normale e non costa niente (`RecordVirtual` consegna solo sul
	 *       cambiamento, il risveglio vale 13 ms).  Un conto che partisse
	 *       comunque butterebbe fuori chi sta leggendo una pagina.
	 * ⚠ E l'istante e' quello del GIRO, non quello in cui i byte sono usciti:
	 *   lo `stallo_ms` misurato puo' essere fino a ~1 s piu' corto del vero.
	 *   Si scatta piu' tardi, mai piu' presto — che e' il lato giusto. */
	if (usciti > 0 || !avevo_da_mandare) {
		w->lm_uscita_ms = ora_ms;
		w->lm_usciti_visti = w->lm_usciti;
		w->lm_offerti_visti = w->lm_offerti;
		return;
	}
	if (!linea_morta_stallo_ms || stallo < linea_morta_stallo_ms)
		return;
	linea_morta_scatta(
		w, in, "stallo", stallo, offerti, usciti, coda_video,
		ora_ms - w->lm_vivo_ms, in->pkt_sent - w->lm_pkt_sent_vivo,
		"⛔ la linea e' MORTA: da troppo tempo non esce un fotogramma pur "
		"avendone da mandare — l'immagine dell'utente e' FERMA, e a questo "
		"punto il prodotto o la congela o la mostra con secondi di ritardo "
		"(`[M]` 23 agosto 2026: fino a 30,06 s di buco su `raffica-forte`).  "
		"Nessuno dei due va servito: il filo cade, e per tornare bisogna "
		"rientrare a mano (decisione dell'utente)");
}

bool wt_linea_morta_scattata(const wt *w)
{
	return w && w->lm_scattata;
}

static void rete_ciclo(wt *w, uint64_t ora_ms)
{
	ngtcp2_conn_info in;
	uint64_t cwnd_left, da_ms;
	char minimo[24], coda[24];
	const char *detto;
	int g;

	if (!w->conn || w->chiusura >= 0)
		return;
	/* ⚠ Al piu' una al secondo.  ⛔ E la PRIMA esce sempre, senza aspettare:
	 *   `rete_detto_ms == 0` vuol dire «mai parlato», che non e' «non e'
	 *   cambiato niente» (`LEZIONI.md` §1.9). */
	if (w->rete_detto_ms && ora_ms - w->rete_detto_ms < 1000)
		return;

	memset(&in, 0, sizeof in);
	ngtcp2_conn_get_conn_info(w->conn, &in);
	cwnd_left = ngtcp2_conn_get_cwnd_left(w->conn);

	/* ⛔⭐ E QUI SI GIUDICA, PRIMA del filtro «solo se e' cambiato qualcosa»:
	 *     il silenzio del client E' il caso in cui non cambia niente, e messo
	 *     dopo quel filtro questo giudizio non verrebbe percorso MAI proprio
	 *     quando serve.  ⚠ Il ritmo e' quello di `rete_ciclo()`, una volta al
	 *     secondo, ed e' anche la finestra minima. */
	linea_morta_giudica(w, &in, ora_ms);

	/* ⛔⭐ LA REGOLA DEL GIUDIZIO, e si legge dall'alto: il primo che scatta
	 *     vince, e l'ordine NON e' arbitrario.
	 *
	 *  1. `persi_d > 0` — ngtcp2 ha DICHIARATO perduti dei pacchetti in questo
	 *     intervallo ⇒ «⛔ la linea perde».  Viene prima di tutto perche' la
	 *     finestra chiusa e' quasi sempre la CONSEGUENZA della perdita: con
	 *     l'ordine invertito la causa si nasconderebbe dietro il suo effetto.
	 *  2. `cwnd_left == 0` con una finestra che esiste (`cwnd > 0`) — non c'e'
	 *     posto per spedire ⇒ «⚠ la finestra e' chiusa».  Senza perdite
	 *     nell'intervallo e' l'eco di una perdita passata, oppure e' l'avvio
	 *     lento che non ha ancora aperto: la riga porta `ssthresh` accanto e
	 *     chi legge distingue i due (sotto soglia = avvio lento).
	 *  3. altrimenti «-- niente da segnalare».
	 *
	 * ⚠ E IL GIUDIZIO NON PARLA DI JITTER NE' DI RIORDINO, apposta: quei due
	 *   numeri ngtcp2 non li da' (vedi il riquadro sopra), e un giudizio
	 *   dedotto da `rttvar` avrebbe voluto una SOGLIA — cioe' una decisione, e
	 *   qui non se ne prende nessuna. */
	if (in.pkt_lost > w->rete_pkt_lost)
		g = WT_RETE_PERDE;
	else if (in.cwnd > 0 && cwnd_left == 0)
		g = WT_RETE_FINESTRA;
	else
		g = WT_RETE_NULLA;

	/* ⛔⭐ SOLO QUANDO QUALCOSA E' CAMBIATO.  Una riga al secondo che ripete
	 *     gli stessi numeri e' rumore che NASCONDE le righe che contano — ed e'
	 *     la lezione dei 30,8 GB di registro, in una veste nuova: li' era una
	 *     riga per fotogramma, qui sarebbe una riga per sessione ferma.
	 *
	 * ⚠ Il controllo e' sui CONTATORI (spediti, ricevuti, persi, scartati) e
	 *   sul GIUDIZIO, non su `cwnd`/`rtt`: quelli oscillano sempre di un byte o
	 *   di un microsecondo, e col loro confronto la riga non tacerebbe mai —
	 *   cioe' il filtro sarebbe scritto e non funzionerebbe.  Se i quattro
	 *   contatori sono FERMI, sul filo non e' passato niente: e allora anche
	 *   `cwnd` e `rtt` sono quelli di prima, per costruzione. */
	/* ⛔ E i datagram entrano nel confronto: una sessione che perde SOLO
	 *    audio — i pacchetti con dentro i DATAGRAM sono pacchetti come gli
	 *    altri, ma un riordino puo' non muovere `pkt_lost` — resterebbe muta
	 *    proprio nel caso che la fase 9 va a cercare. */
	if (w->rete_detto_ms
	    && in.pkt_lost == w->rete_pkt_lost
	    && in.pkt_sent == w->rete_pkt_sent
	    && in.pkt_recv == w->rete_pkt_recv
	    && in.pkt_discarded == w->rete_pkt_discarded
	    && w->dgram_persi == w->rete_dgram_persi
	    && w->dgram_falsi == w->rete_dgram_falsi
	    && g == w->rete_giudizio)
		return;

	/* ⛔ `min_rtt` vale `UINT64_MAX` finche' non e' arrivato un campione, e la
	 *    sottrazione darebbe un numero enorme che SEMBRA misurato — forma E1,
	 *    la peggiore.  ⇒ Si dichiara `n/d` invece di stampare spazzatura.  E'
	 *    la stessa guardia di `ritmo_frena()`, e vale per tutt'e due i campi
	 *    che da `min_rtt` dipendono. */
	if (in.min_rtt != UINT64_MAX && in.min_rtt != 0) {
		snprintf(minimo, sizeof minimo, "%llu",
		         (unsigned long long)(in.min_rtt / NGTCP2_MICROSECONDS));
		/* ⭐ `smoothed_rtt - min_rtt` E' LA CODA DENTRO LA RETE: e' il numero
		 *    con cui `SPECIFICHE.md:128` — «ogni memoria intermedia compra
		 *    fluidita' e vende risposta» — si onora invece di citarlo. */
		if (in.smoothed_rtt >= in.min_rtt)
			snprintf(coda, sizeof coda, "%llu",
			         (unsigned long long)((in.smoothed_rtt - in.min_rtt)
			                              / NGTCP2_MICROSECONDS));
		else
			snprintf(coda, sizeof coda, "0");
	} else {
		snprintf(minimo, sizeof minimo, "n/d");
		snprintf(coda, sizeof coda, "n/d");
	}

	switch (g) {
	case WT_RETE_PERDE:
		detto = "⛔ la linea perde";
		break;
	case WT_RETE_FINESTRA:
		detto = "⚠ la finestra e' chiusa";
		break;
	default:
		detto = "-- niente da segnalare";
		break;
	}

	da_ms = w->rete_detto_ms ? ora_ms - w->rete_detto_ms : 0;

	registro_dice(REG_WT,
	              "rete-quic %s da_ms=%llu persi=%llu persi_d=%llu "
	              "byte_persi=%llu byte_persi_d=%llu spediti=%llu spediti_d=%llu "
	              "byte_spediti=%llu ricevuti=%llu ricevuti_d=%llu "
	              "scartati=%llu scartati_d=%llu cwnd=%llu cwnd_left=%llu "
	              "ssthresh=%llu involo=%llu srtt_us=%llu latest_us=%llu "
	              "rttvar_us=%llu min_rtt_us=%s coda_rete_us=%s pto_us=%llu "
	              "dgram_persi=%llu dgram_persi_d=%llu dgram_ok=%llu "
	              "dgram_falsi=%llu dgram_falsi_d=%llu giudizio=%s",
	              w->provenienza,
	              (unsigned long long)da_ms,
	              (unsigned long long)in.pkt_lost,
	              (unsigned long long)(in.pkt_lost - w->rete_pkt_lost),
	              (unsigned long long)in.bytes_lost,
	              (unsigned long long)(in.bytes_lost - w->rete_bytes_lost),
	              (unsigned long long)in.pkt_sent,
	              (unsigned long long)(in.pkt_sent - w->rete_pkt_sent),
	              (unsigned long long)in.bytes_sent,
	              (unsigned long long)in.pkt_recv,
	              (unsigned long long)(in.pkt_recv - w->rete_pkt_recv),
	              (unsigned long long)in.pkt_discarded,
	              (unsigned long long)(in.pkt_discarded - w->rete_pkt_discarded),
	              (unsigned long long)in.cwnd,
	              (unsigned long long)cwnd_left,
	              (unsigned long long)in.ssthresh,
	              (unsigned long long)in.bytes_in_flight,
	              (unsigned long long)(in.smoothed_rtt / NGTCP2_MICROSECONDS),
	              (unsigned long long)(in.latest_rtt / NGTCP2_MICROSECONDS),
	              (unsigned long long)(in.rttvar / NGTCP2_MICROSECONDS),
	              minimo, coda,
	              (unsigned long long)(ngtcp2_conn_get_pto(w->conn)
	                                   / NGTCP2_MICROSECONDS),
	              (unsigned long long)w->dgram_persi,
	              (unsigned long long)(w->dgram_persi - w->rete_dgram_persi),
	              (unsigned long long)w->dgram_riscontrati,
	              (unsigned long long)w->dgram_falsi,
	              (unsigned long long)(w->dgram_falsi - w->rete_dgram_falsi),
	              detto);

	w->rete_detto_ms      = ora_ms;
	w->rete_pkt_lost      = in.pkt_lost;
	w->rete_bytes_lost    = in.bytes_lost;
	w->rete_pkt_sent      = in.pkt_sent;
	w->rete_pkt_recv      = in.pkt_recv;
	w->rete_pkt_discarded = in.pkt_discarded;
	w->rete_dgram_persi   = w->dgram_persi;
	w->rete_dgram_falsi   = w->dgram_falsi;
	w->rete_giudizio      = g;
}

/* ------------------------------------------------------------------------ */
/* ⭐ IL FOTOGRAMMA CHE ARRIVA DAL PALCO, CONSEGNATO A UNA SESSIONE.          */

static void video_a_una(wt *w, const char *utente, uint8_t codec, bool chiave,
                        const uint8_t *dati, size_t byte, uint32_t l, uint32_t a,
                        uint64_t istante_us, uint32_t input)
{
	uint32_t tl = 0, ta = 0;
	uint64_t ora_ms;
	const char *mio;
	int e;

	if (!w->video_acceso || w->video_codec != codec)
		return;
	if (!w->rcp || !w->conn || w->chiusura >= 0)
		return;

	/* ⛔⭐ INVARIANTE I3 SUL FILO, E NON E' UNA PRUDENZA IN PIU'.
	 *
	 *     `[M]` 12 agosto 2026: con un deposito di processo, «prova» (uid 1001,
	 *     senza sessione grafica) ha ricevuto **un fotogramma conforme**, e quel
	 *     fotogramma era il desktop di «nicfio».  Non «non ricevi niente»:
	 *     **ricevi il desktop di un altro**, e nessuno dei due se ne accorge.
	 *     ⇒ Qui il confronto e' fra l'utente che ha CATTURATO e l'utente che
	 *     PAM ha ammesso su questa sessione, e sono due fatti diversi tutti e
	 *     due chiesti a chi li sa. */
	mio = rcp_utente(w->rcp);
	if (!mio || !utente || strcmp(mio, utente) != 0)
		return;

	if (!rcp_tela_in_vigore(w->rcp, &tl, &ta))
		return;

	/* ⛔⭐ E LA TELA DEV'ESSERE QUELLA, non «piu' o meno quella» — §6.2, P5.
	 *
	 *     I 28 byte portano `largh.`/`altezza` = la tela IN VIGORE, e li scrive
	 *     `rcp.c` dalla sua.  Se il fotogramma catturato ne portasse un'altra,
	 *     l'intestazione direbbe una misura e i pixel ne porterebbero un'altra:
	 *     due verita' sulla stessa cosa, e il client non avrebbe modo di
	 *     accorgersene — il decodificatore prende la misura dal flusso.
	 *     ⛔ Meglio nessun fotogramma che un fotogramma che mente. */
	if (tl != l || ta != a) {
		w->video_saltati++;
		/* ⚠ Un fondo SUO, e non piu' `video_detto`: quel campo e' il fondo del
		 *   messaggio «nessun codec negoziato», e un flag per due fatti diversi
		 *   ne spegne uno quando l'altro parla.  ⛔ E qui il fondo si RIARMA a
		 *   ogni cambio di tela, perche' il fatto e' cambiato. */
		if (w->tela_detta_l != l || w->tela_detta_a != a) {
			w->tela_detta_l = l;
			w->tela_detta_a = a;
			/* ⭐ Si conta l'ANNUNCIO, non il fotogramma: il fotogramma l'ha
			 *    gia' contato `video_saltati` tre righe sopra.  Due numeri per
			 *    due fatti, e la riga di chiusura li scrive tutt'e due. */
			w->video_annunci_tela++;
			registro_dice(REG_RCP,
			              "⛔ %s: tela in vigore %ux%u ma il fotogramma catturato "
			              "e' %ux%u — NON lo spedisco (§6.2): l'intestazione "
			              "direbbe una misura e i pixel ne porterebbero un'altra.  "
			              "⚠ Al palco si sta richiedendo la tela in vigore",
			              w->provenienza, tl, ta, l, a);
		}
		return;
	}
	/* ⭐ Tela e fotogramma sono d'accordo: il fondo del messaggio di sopra si
	 *    disarma, cosi' il prossimo disaccordo si vedra' invece di essere
	 *    scambiato per la coda di quello di prima. */
	w->tela_detta_l = w->tela_detta_a = 0;

	ora_ms = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;

	/* ⛔⭐⭐ FASE 9 — «AVEVO DA MANDARE», E SI CONTA QUI, PRIMA DI TUTTO.
	 *
	 *      Da questa riga in poi il fotogramma puo' essere frenato dal
	 *      regolatore del ritmo, sgomberato da §5.1, rifiutato per mancanza di
	 *      credito (§2.3) o non entrare nell'elenco dei fotogrammi in volo: in
	 *      TUTTI quei casi il palco ce l'aveva dato lo stesso, e per la linea
	 *      morta il fatto e' quello.
	 *
	 * ⛔ Contarlo piu' avanti — dopo il freno, per esempio — vorrebbe dire che
	 *    il regolatore del ritmo NASCONDE lo stallo: smette di produrre, la
	 *    coda si svuota di abbandoni, e «non ho niente da mandare» diventerebbe
	 *    vero proprio mentre lo schermo dell'utente e' fermo.
	 *
	 * ⚠ E sta DOPO i tre controlli di sopra — codec, utente (I3), tela — che
	 *   non sono passi della spedizione: sono la risposta alla domanda «questo
	 *   fotogramma e' MIO?».  Un fotogramma di un altro utente non e' roba che
	 *   avevamo da mandare. */
	w->lm_offerti++;

	/* ⛔⭐⭐ FASE 9 — IL REGOLATORE DEL RITMO, e sta QUI per due ragioni che
	 *      vanno tutt'e due scritte:
	 *
	 *      1. PRIMA di `video_sgombra()`, che tre righe sotto quella coda la
	 *         svuota.  Dopo, `arretrato` sarebbe zero per costruzione e questo
	 *         anello non scatterebbe mai — e un regolatore muto e una linea
	 *         sana hanno la stessa faccia;
	 *      2. e il fotogramma frenato NON fa nemmeno lo sgombero.  ⭐ E' voluto:
	 *         sgomberare vorrebbe dire abbandonare un delta, e ogni abbandono
	 *         accende il debito di §5.2 dentro `rcp.c`, cioe' fabbrica una
	 *         CHIAVE — che e' precisamente la spirale che questa fase cura.  Il
	 *         regolatore smette di PRODURRE; non butta quel che c'e' gia'.
	 *
	 * ⚠ E l'`involo[]` non si sporca: gli elementi i cui byte se ne sono andati
	 *   restano marcati vivi finche' una passata di `video_sgombra()` non li
	 *   toglie, ma `ritmo_frena()` li conta rileggendo i BYTE — quindi
	 *   `arretrato` cala lo stesso, e la frenata finisce da se'. */
	if (ritmo_frena(w, chiave, ora_ms))
		return;

	/* ⛔ §5.1 — «ne e' gia' partito uno piu' recente»: i delta ancora fermi
	 * nella coda si azzerano PRIMA di accodare questo, o la coda crescerebbe
	 * col passato invece di portare il presente. */
	video_sgombra(w, "ne e' partito uno piu' recente (§5.1)");

	/* ⛔ §2.3 — e il credito si guarda PRIMA di chiedere lo stream, per poter
	 * distinguere «non c'era posto» da «lo stream si e' rotto».  ⚠ La riserva
	 * e' per l'input: §2.3 esiste perche' senza credito «l'input non partirebbe
	 * affatto e il sintomo sarebbe il desktop non risponde». */
	if (!chiave
	    && ngtcp2_conn_get_streams_uni_left2(w->conn) <= WT_UNI_RISERVA) {
		w->video_saltati++;
		/* ⛔⭐ FASE 9 — e questo si conta A PARTE dagli abbandoni di §5.1.
		 *     E' la CAUSA 4 del debito di §5.2 (`rcp.c:3441`), la forma **C**
		 *     dell'abbandono: nessuno stream, nessun buco, nessun segnale — il
		 *     ricevente non la vede affatto.  ⚠ La cura della soglia tocca la
		 *     causa 3, non questa: se sotto congestione a tenere acceso il
		 *     debito fosse questa, la cura girerebbe a vuoto e i numeri non si
		 *     muoverebbero.  ⇒ Due contatori, o il banco non sa attribuire. */
		w->sgombra_credito++;
		rcp_video_niente_credito(w->rcp, false,
		                         ngtcp2_conn_get_streams_uni_left2(w->conn));
		return;
	}

	w->video_stream_ultimo = -1;
	e = rcp_video_spedisci(w->rcp, chiave, dati, byte, istante_us, input, ora_ms);
	if (e == RCP_VIDEO_SPEDITO) {
		w->video_diffusi++;
		/* ⭐ La misura dell'ultima CHIAVE, e serve a `chiave_intervallo_ms()`:
		 *    e' il numero da cui si calcola quanto ci mette a uscire.  ⛔ Si
		 *    prende QUI, dov'e' un fatto, invece di stimarla da una media —
		 *    `[M]` sul banco 07-b65 una chiave a 1080p misura ~60 000 byte, ma
		 *    dipende dalla scena e una costante mentirebbe sulla meta' di esse. */
		if (chiave)
			w->chiave_byte = (uint64_t)byte;
		involo_aggiungi(w, w->video_stream_ultimo,
		                rcp_video_ultimo_numero(w->rcp), chiave);
		return;
	}

	w->video_saltati++;
	/* ⛔ E il rifiuto NON e' un errore fatale: §2.3 — «il server DEVE reggere
	 * il rifiuto di aprire uno stream invece di considerarlo un errore
	 * fatale».  ⚠ Le righe le ha gia' scritte `rcp.c`, che sa quale delle sette
	 * ragioni e': qui si conta e si tace, o la stessa cosa finirebbe due volte
	 * nel registro con due parole diverse. */
}

/* ⭐⭐ §7.2 — la forma del cursore a tutte le sessioni di quell'utente.
 *
 * ⛔ E il confronto del nome NON e' una formalita': il deposito e' di processo e
 *    le sessioni sono di utenti diversi.  Mandare la forma del cursore di un
 *    altro non e' un difetto grafico — e' l'immagine di quel che sta facendo
 *    un'altra persona che finisce sullo schermo sbagliato. */
void wt_cursore_diffondi(const char *utente, uint16_t larghezza,
                         uint16_t altezza, int16_t attivo_x, int16_t attivo_y,
                         const uint8_t *immagine, size_t byte)
{
	if (!utente || !utente[0])
		return;
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || strcmp(mio, utente) != 0)
			continue;
		/* ⚠ Il ritorno non si guarda qui: `rcp.c` ha gia' scritto nel registro
		 *   quale delle sue ragioni e' — e guardarlo anche noi metterebbe la
		 *   stessa cosa due volte con due parole diverse. */
		rcp_cursore_forma(w->rcp, larghezza, altezza, attivo_x, attivo_y,
		                  immagine, byte);
	}
}

/* ⛔⭐⭐ LA MISURA CHE IL PALCO HA ADESSO, per utente — e sopravvive alla
 *     connessione, come il palco (invariante I4).
 *
 * ⛔ SERVE AL RI-ATTACCO, ed e' l'unico posto del padre in cui quel numero
 *    esiste: `rcp.c` conosce la tela CONCESSA, il figlio conosce quella VERA, e
 *    fra i due passano solo fotogrammi.  ⇒ Si legge dal fotogramma — che e'
 *    anche l'unica fonte che non mente (`DECISIONI.md` §5.0-sexies).
 *
 * ⚠ Non e' una cache da tenere fresca: e' un FATTO datato all'ultimo fotogramma
 *   consegnato.  Se il palco muore e rinasce a un'altra misura, la prima riga di
 *   `rcp_tela_concessa()` se ne accorge e chiede al palco di venire dov'e' la
 *   tela in vigore.
 *
 * ⚠ Otto voci: `MAX_ATTACCATE` in `rcp.c` e' dello stesso ordine, e un utente
 *   in piu' che non trova posto perde solo questa comodita' — riparte come
 *   prima del 15 agosto 2026, cioe' concedendo quel che il client chiede. */
#define WT_PALCHI 8
static struct {
	/* ⛔ 257 e non 64: e' la misura del campo `utente` di `rcp.c`.  ⚠ Con un
	 *    campo piu' corto `snprintf` troncava in scrittura e `strcmp` confrontava
	 *    il nome INTERO con quello troncato: la voce non si ritrovava mai, se ne
	 *    prendeva una nuova a ogni fotogramma, e in otto giri la tabella era piena
	 *    dello stesso nome — spenta **per tutti gli utenti della macchina**.
	 *    Difetto trovato refutando, 15 agosto 2026. */
	char utente[257];
	uint32_t l, a;
} palchi[WT_PALCHI];
static bool palchi_pieni_detto;

static void palco_misura_segna(const char *utente, uint32_t l, uint32_t a)
{
	int libero = -1;

	if (!utente || !utente[0] || !l || !a)
		return;
	for (int i = 0; i < WT_PALCHI; i++) {
		if (palchi[i].utente[0] == '\0') {
			if (libero < 0)
				libero = i;
			continue;
		}
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		palchi[i].l = l;
		palchi[i].a = a;
		return;
	}
	if (libero < 0) {
		/* ⛔ Il ripiego si DICHIARA (`CODER.md` §4.2), e una volta sola: senza
		 *    questa riga il nono utente perdeva la cura del ri-attacco in
		 *    silenzio, e il sintomo sarebbe stato «a me il desktop al riattacco
		 *    non torna» per quel solo utente. */
		if (!palchi_pieni_detto) {
			palchi_pieni_detto = true;
			registro_dice(REG_RCP,
			              "⚠ RIPIEGO DICHIARATO: la tabella delle tele dei palchi "
			              "e' piena (%d): «%s» non ci sta, e al suo ri-attacco la "
			              "tela verra' concessa come la chiede il client invece "
			              "che come il palco ce l'ha",
			              WT_PALCHI, utente);
		}
		return;
	}
	snprintf(palchi[libero].utente, sizeof palchi[libero].utente, "%s", utente);
	palchi[libero].l = l;
	palchi[libero].a = a;
}

/* ⛔⭐ IL PALCO E' MORTO: la sua misura non e' piu' un fatto, e' un ricordo.
 *
 * ⚠ Difetto trovato refutando: senza questa riga la voce restava, e al
 *   ri-attacco `SESSIONE` concedeva **la misura di ieri** — quella di un palco
 *   che non esiste piu'.  Il palco nuovo ne consegna un'altra, la sessione nasce
 *   in disaccordo, e la cura del ri-attacco si ritorceva contro se stessa.
 * ⛔ «Non lo so» e «era 1920x1080» sono due fatti diversi, e il secondo, quando
 *    e' falso, e' peggio del primo. */
void wt_palco_dimentica(const char *utente)
{
	if (!utente || !utente[0])
		return;
	for (int i = 0; i < WT_PALCHI; i++) {
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		registro_dice(REG_RCP,
		              "la tela del palco di «%s» (%ux%u) si dimentica: quel palco "
		              "non c'e' piu', e un numero vecchio spacciato per fatto e' "
		              "peggio di nessun numero",
		              utente, palchi[i].l, palchi[i].a);
		memset(&palchi[i], 0, sizeof palchi[i]);
		palchi_pieni_detto = false;
		return;
	}
}

/* ⭐⭐ LA RISPOSTA DEL PALCO SULLA TELA — §7.1, e arriva dal FIGLIO.
 *
 * ⛔ Va a TUTTE le sessioni di quell'utente, e non solo a chi ha chiesto: la
 *    tela del palco e' una sola, e una sessione che non lo sapesse continuerebbe
 *    a scartare ogni fotogramma per misura sbagliata.  ⚠ `rcp.c` decide da se'
 *    se quel messaggio risponde a una SUA richiesta — qui non si sceglie. */
void wt_tela_dal_palco(const char *utente, uint32_t voluta_l, uint32_t voluta_a,
                       uint32_t avuta_l, uint32_t avuta_a)
{
	/* ⛔ E la tabella si aggiorna QUI e non solo dai fotogrammi: questa e' la
	 *    notizia piu' fresca che il padre abbia sulla misura del palco, e arriva
	 *    anche quando nessun fotogramma parte. */
	palco_misura_segna(utente, avuta_l, avuta_a);
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		rcp_tela_dal_palco(w->rcp, voluta_l, voluta_a, avuta_l, avuta_a,
		                   w->conn ? ngtcp2_conn_get_timestamp(w->conn)
		                                 / NGTCP2_MILLISECONDS
		                           : 0);
	}
}

static bool wt_palco_misura(const char *utente, uint32_t *l, uint32_t *a)
{
	if (!utente || !utente[0])
		return false;
	for (int i = 0; i < WT_PALCHI; i++) {
		if (strcmp(palchi[i].utente, utente) != 0)
			continue;
		if (!palchi[i].l || !palchi[i].a)
			return false;
		if (l)
			*l = palchi[i].l;
		if (a)
			*a = palchi[i].a;
		return true;
	}
	return false;
}

/* ⛔ Il gancio che `rcp.c` chiama in `ATTACCA`.  ⚠ L'utente e' quello che PAM ha
 *    ammesso su QUESTA sessione: chiedere il palco di un altro sarebbe dire a
 *    questo client la misura del desktop di qualcun altro. */
static bool gancio_tela_del_palco(void *ctx, uint32_t *l, uint32_t *a)
{
	wt *w = (wt *)ctx;
	const char *mio;

	if (!w->rcp)
		return false;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0])
		return false;
	return wt_palco_misura(mio, l, a);
}

size_t wt_sorveglia_locali(void)
{
	size_t congedate = 0;

	if (!gancio_locale)
		return 0;

	/* ⛔ Si guarda la lista a ogni giro invece di tenere un elenco di utenti:
	 *    una sessione puo' nascere e morire fra due ripassi, e un elenco che si
	 *    aggiorna da solo e' un secondo stato da tenere d'accordo col primo —
	 *    cioe' il modo in cui due verita' entrano in un programma. */
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		char quale[160];
		const char *mio;

		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !mio[0])
			continue;

		quale[0] = '\0';
		if (!gancio_locale(gancio_locale_ctx, mio, quale, sizeof quale))
			continue;

		/* ⛔⭐ §5.1: «ha una sessione grafica REMOTA attiva e ne apre una
		 *     LOCALE ⇒ **la locale vince**: la remota viene chiusa».
		 *
		 * ⭐ Ed e' l'unico punto del prodotto in cui il server porta via una
		 *    sessione SANA — `DECISIONI.md` §4.1-bis lo ammette **solo** con un
		 *    motivo dicibile, ed e' per questo che `0x04` esiste. */
		registro_dice(REG_WT,
		              "⛔ «%s» ha aperto una sessione grafica LOCALE (%s): la "
		              "sessione remota viene chiusa — §5.1, motivo 0x04",
		              mio, quale[0] ? quale : "senza dettaglio");
		wt_congeda(w, RCP_SESSIONE_LOCALE_PREVALSA,
		           "e' stata aperta una sessione grafica locale su questa "
		           "macchina");
		congedate++;
	}
	return congedate;
}

void wt_tela_rimanda(const char *utente, uint32_t voluta_l, uint32_t voluta_a)
{
	uint64_t ora = registro_ora_ms();

	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		rcp_tela_rimanda(w->rcp, voluta_l, voluta_a, ora);
	}
}

size_t wt_congeda_utente(const char *utente, uint8_t motivo, const char *dettaglio,
                         const wt *tranne)
{
	size_t quante = 0;

	if (!utente || !utente[0])
		return 0;
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;

		if (w == tranne || !w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || strcmp(mio, utente) != 0)
			continue;
		wt_congeda(w, motivo, dettaglio);
		quante++;
	}
	return quante;
}

void wt_video_diffondi(const char *utente, uint8_t codec, bool chiave,
                       const uint8_t *dati, size_t byte, uint32_t larghezza,
                       uint32_t altezza, uint64_t istante_us, uint32_t input)
{
	/* ⛔⛔ QUESTA RIGA HA BUTTATO IN SILENZIO OGNI FOTOGRAMMA H.264 — 20 agosto
	 *     2026, e ci e' voluto mezz'ora per trovarla.
	 *
	 * Il codec 3 e' entrato in `RCP.md` §6.2 e questa guardia ne conosceva due:
	 * il figlio codificava (5 940 byte, CHIAVE, 1,6 ms in hardware), il padre
	 * riceveva («fotogramma da «prova»: codec 3»), e qui **il fotogramma
	 * spariva senza una riga**.  ⇒ Sessione viva, contatori a zero, e nessun
	 * registro che nominasse la causa.
	 *
	 * ⭐ Adesso il numero massimo viene da UN posto — `RCP_CODEC_VIDEO_MAX` —
	 *    e il rifiuto **si dichiara** (una riga sola, non una per fotogramma:
	 *    a sessanta al secondo sarebbe il difetto dei 30,8 GB). */
	if (codec < 1 || codec > RCP_CODEC_VIDEO_MAX) {
		static uint8_t detto;

		if (detto != codec) {
			detto = codec;
			registro_dice(REG_WT,
			              "⛔ fotogramma con codec %u BUTTATO: §6.2 ne definisce "
			              "%u (1 = HEVC, 2 = AV1, 3 = H.264).  ⚠ La riga si "
			              "scrive una volta per numero, non una per fotogramma",
			              codec, (unsigned) RCP_CODEC_VIDEO_MAX);
		}
		return;
	}
	/* ⛔ Si segna PRIMA di consegnare, e vale anche se non c'e' nessuna sessione
	 *    a cui consegnare: e' un fatto del palco, non della connessione — ed e'
	 *    esattamente il caso del ri-attacco, dove la sessione che vedra' quel
	 *    numero **non esiste ancora**. */
	palco_misura_segna(utente, larghezza, altezza);
	for (wt *w = vive_prima; w; w = w->viva_dopo)
		video_a_una(w, utente, codec, chiave, dati, byte, larghezza, altezza,
		            istante_us, input);
}

/* ------------------------------------------------------------------------ */
/* ⭐ IL BLOCCO D'AUDIO CHE ARRIVA DALLA SESSIONE, CONSEGNATO A UNA SESSIONE. */

static void audio_a_una(wt *w, const char *utente, uint8_t codec,
                        uint64_t istante_us, const uint8_t *dati, size_t byte)
{
	uint8_t buf[WT_DGRAM_BYTE];
	size_t p = 0;
	uint64_t tetto;
	const char *mio;

	if (!w->audio_acceso || w->audio_codec != codec)
		return;
	if (!w->rcp || !w->conn || w->chiusura >= 0)
		return;

	/* ⛔⭐ INVARIANTE I3, E VALE PER IL SUONO ESATTAMENTE COME PER I PIXEL.
	 *
	 *     `[M]` 12 agosto 2026 il difetto si presento' sul video: «prova» ricevette
	 *     un fotogramma conforme, e il fotogramma era il desktop di «nicfio».
	 *     ⛔ Sull'audio lo stesso difetto e' PEGGIO da accorgersene: un desktop
	 *     sbagliato si riconosce guardandolo, una telefonata sbagliata no. */
	mio = rcp_utente(w->rcp);
	if (!mio || !utente || strcmp(mio, utente) != 0)
		return;

	tetto = dgram_tetto_del_pari(w);
	if (tetto == 0) {
		if (!w->dgram_negati_detto) {
			w->dgram_negati_detto = true;
			registro_dice(REG_RCP,
			              "⛔ %s: il pari NON accetta datagram "
			              "(`max_datagram_frame_size` = 0) — questa sessione non "
			              "avra' audio.  ⚠ `RCP.md` §2.2 li PRETENDE, ma §6.3 "
			              "vieta di chiudere per un fatto dei datagram: si "
			              "dichiara e si tace",
			              w->provenienza);
		}
		return;
	}

	/* Il prefisso di RFC 9297: il quarto dell'identificativo dello stream su
	 * cui vive la sessione WebTransport.  ⛔ Senza, il browser scarta il
	 * datagram **senza un errore**: non e' un nostro campo, e' l'involucro. */
	p = varint_scrivi(buf, (uint64_t)w->sessione / 4);

	/* L'inquadratura di `RCP.md` §6.3, in ordine di rete. */
	if (p + 12 + byte > sizeof buf || (uint64_t)(p + 12 + byte) > tetto) {
		w->audio_buttati++;
		if (w->audio_buttati == 1 || w->audio_buttati % 100 == 0)
			registro_dice(REG_WT,
			              "⛔ %s: blocco d'audio di %zu byte troppo grande "
			              "(prefisso %zu + 12 + %zu, tetto del pari %llu) — "
			              "buttato.  Buttati %llu",
			              w->provenienza, byte, p, byte,
			              (unsigned long long)tetto,
			              (unsigned long long)w->audio_buttati);
		return;
	}
	buf[p++] = 0x04;
	buf[p++] = 0x01; /* tipo `0x0401`, l'unico definito in RCP/1 */
	buf[p++] = 0x00;
	buf[p++] = codec; /* `codec` u16: 1 = Opus, 2 = PCM */
	for (int i = 7; i >= 0; i--)
		buf[p++] = (uint8_t)(istante_us >> (8 * i)); /* `istante` u64 */
	memcpy(buf + p, dati, byte);
	p += byte;

	dgram_accoda(w, buf, p);
}

/* ------------------------------------------------------------------------ */
/* ⭐ IL TONO DI PROVA — la sorgente che certifica il filo, e NIENT'ALTRO.    */
/*
 * ⛔⭐ PERCHE' ESISTE, E PERCHE' NON E' UNA SCORCIATOIA
 *
 *     La catena dell'audio ha cinque anelli: il sink nella sessione, la
 *     cattura del monitor, il codificatore, il datagram, il browser che suona.
 *     Accenderli tutti insieme e poi non sentire niente lascia **cinque
 *     imputati** — ed e' esattamente il modo in cui questo progetto ha perso
 *     le sue giornate peggiori (`LEZIONI.md` §10).
 *
 *     Questa sorgente ne mette in prova **tre soli** — codificatore, datagram,
 *     browser — con un segnale di cui si conosce **ogni campione in anticipo**.
 *     ⇒ Se il tono esce a 440 Hz dall'altra parte, il filo e' assolto e quel
 *     che resta e' la cattura.  Se non esce, la cattura non c'entra.
 *
 * ⛔ E' SPENTO se nessuno lo accende (`--audio-prova`), ed e' l'invariante I6:
 *    quel che cambia cio' che l'utente sente sta dietro un interruttore spento
 *    finche' non l'ha guardato.  ⚠ Quando e' acceso lo SCRIVE, a ogni sessione:
 *    un server che suonasse un tono senza dirlo sarebbe un difetto travestito
 *    da funzione.
 *
 * ⚠ E quel che questa sorgente NON prova, dichiarato: il ritmo.  I blocchi
 *   escono a raffica quando il battito e' lungo, invece che uno ogni 20 ms —
 *   e' il difetto che v1 pago' su `SendSamples2` (`altoparlante.h`, «il client
 *   BUTTA i blocchi corti»).  Il ritmo lo dara' la cattura, che ha un orologio
 *   suo; qui si guarda il CONTENUTO, non la cadenza.
 */
void wt_audio_gancio(wt_audio_richiesta f, void *ctx)
{
	gancio_audio = f;
	gancio_audio_ctx = ctx;
}

void wt_audio_prova(uint32_t hz)
{
	audio_prova_hz = hz;
	if (hz)
		registro_dice(REG_WT,
		              "⚠ TONO DI PROVA ACCESO a %u Hz — ogni sessione ammessa "
		              "sentira' un tono invece del desktop.  ⛔ E' una funzione "
		              "di banco (I6): in un'installazione normale non si accende",
		              hz);
}

static void tono_passo(wt *w, ngtcp2_tstamp ts)
{
	/* ⛔ Un tetto per passata: senza, un battito lungo genererebbe cento
	 *    blocchi in un colpo, la coda ne butterebbe novantadue e il registro
	 *    direbbe «buttati» per un difetto che non e' della rete. */
	int quanti = 0;
	uint64_t ora_us;
	const char *utente;

	if (!audio_prova_hz || !w->audio_acceso || w->chiusura >= 0 || !w->rcp)
		return;

	utente = rcp_utente(w->rcp);
	if (!utente || !utente[0])
		return;

	if (!w->tono_cod) {
		w->tono_cod = audio_cod_apri(w->audio_codec);
		if (!w->tono_cod) {
			/* ⛔ Si spegne questa sessione, non il server: il registro l'ha
			 *    gia' detto dentro `audio_cod_apri`. */
			w->audio_acceso = false;
			return;
		}
	}

	ora_us = ts / NGTCP2_MICROSECONDS;
	if (w->tono_prossimo_us == 0)
		w->tono_prossimo_us = ora_us;

	while (ora_us >= w->tono_prossimo_us && quanti < WT_DGRAM_MAX) {
		int16_t campioni[AUDIO_BLOCCO_OPUS * AUDIO_CANALI];
		uint8_t fuori[AUDIO_FUORI_MAX];
		size_t n = 0;
		uint32_t blocco = audio_cod_blocco(w->tono_cod);

		for (uint32_t i = 0; i < blocco; i++) {
			/* ⭐ La fase e' CONTINUA fra un blocco e l'altro (`tono_i` non si
			 *    azzera): ripartire da zero a ogni blocco produrrebbe uno
			 *    scatto ogni 20 ms, cioe' un difetto udibile fabbricato dal
			 *    banco e attribuito al codificatore. */
			double t = (double)(w->tono_i + i) / (double)AUDIO_FREQUENZA;
			double v = 0.5 * sin(2.0 * M_PI * (double)audio_prova_hz * t);
			int16_t s = (int16_t)(v * 32767.0);
			campioni[i * AUDIO_CANALI] = s;
			campioni[i * AUDIO_CANALI + 1] = s;
		}
		w->tono_i += blocco;

		if (audio_cod_passa(w->tono_cod, campioni, fuori, &n))
			audio_a_una(w, utente, w->audio_codec, w->tono_prossimo_us, fuori, n);

		w->tono_prossimo_us += (uint64_t)blocco * 1000000ULL / AUDIO_FREQUENZA;
		quanti++;
	}
}

void wt_audio_diffondi(const char *utente, uint8_t codec, uint64_t istante_us,
                       const uint8_t *dati, size_t byte)
{
	if (codec != 1 && codec != 2)
		return;
	for (wt *w = vive_prima; w; w = w->viva_dopo)
		audio_a_una(w, utente, codec, istante_us, dati, byte);
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ E LE DUE PORTE DAL FIGLIO VERSO IL FILO.                               */

static void appunti_a_una(wt *w, const char *utente, const char *testo,
                          size_t byte)
{
	const char *mio;

	if (!w->rcp)
		return;
	mio = rcp_utente(w->rcp);
	if (!mio || !mio[0] || strcmp(mio, utente) != 0)
		return;
	rcp_appunti_dalla_sessione(w->rcp, testo, byte);
}

void wt_appunti_dalla_sessione(const char *utente, const char *testo,
                               size_t byte)
{
	if (!utente || !testo)
		return;
	for (wt *w = vive_prima; w; w = w->viva_dopo)
		appunti_a_una(w, utente, testo, byte);
}

bool wt_appunti_richiesta(const char *utente, uint32_t serial)
{
	if (!utente)
		return false;
	/* ⛔ Si ferma al PRIMO che risponde di si', e non e' un'ottimizzazione: per
	 *    l'invariante I2 un utente ha **una sola** connessione remota viva alla
	 *    volta (§5.1, `GIA_ATTIVA_REMOTA`), quindi il primo e' l'unico.  ⚠ Se
	 *    un giorno I2 cambiasse, questa riga sarebbe il posto in cui si decide
	 *    A CHI si chiede — e allora la scelta andrebbe scritta, non lasciata
	 *    all'ordine di una lista. */
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		uint64_t ora;

		if (!w->rcp || !w->conn)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !mio[0] || strcmp(mio, utente) != 0)
			continue;
		/* ⛔ L'orologio si chiede a ngtcp2, che e' quello con cui `rcp_tempo()`
		 *    misurera' il fondo: due orologi diversi sulla stessa grandezza
		 *    darebbero un fondo che scade prima o dopo di quel che dice. */
		ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
		if (rcp_appunti_chiedi(w->rcp, serial, ora))
			return true;
	}
	return false;
}

bool wt_audio_qualcuno_ascolta(const char *utente, uint8_t *codec)
{
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->audio_acceso || !w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		if (codec)
			*codec = w->audio_codec;
		return true;
	}
	return false;
}

void wt_audio_conti(const wt *w, uint64_t *spediti, uint64_t *buttati,
                    uint64_t *rifiutati, size_t *in_coda)
{
	if (spediti)
		*spediti = w ? w->audio_spediti : 0;
	if (buttati)
		*buttati = w ? w->audio_buttati : 0;
	if (rifiutati)
		*rifiutati = w ? w->audio_rifiutati : 0;
	if (in_coda)
		*in_coda = w ? w->ndgram : 0;
}

bool wt_video_qualcuno_guarda(const char *utente, uint8_t *codec)
{
	for (wt *w = vive_prima; w; w = w->viva_dopo) {
		const char *mio;
		if (!w->video_acceso || !w->rcp || w->chiusura >= 0)
			continue;
		mio = rcp_utente(w->rcp);
		if (!mio || !utente || strcmp(mio, utente) != 0)
			continue;
		if (codec)
			*codec = w->video_codec;
		return true;
	}
	return false;
}

void wt_video_conti(const wt *w, uint32_t *diffusi, uint32_t *saltati,
                    uint32_t *spediti, uint32_t *abbandonati,
                    uint32_t *ritmo_scesi)
{
	if (diffusi)
		*diffusi = w ? w->video_diffusi : 0;
	if (saltati)
		*saltati = w ? w->video_saltati : 0;
	/* ⭐ FASE 9 — il quinto numero, e sta qui e non in `rcp.c` perche' e' una
	 *    decisione del TRASPORTO: rcp non sa niente di questo fotogramma, non
	 *    gli e' mai stato offerto. */
	if (ritmo_scesi)
		*ritmo_scesi = w ? w->video_ritmo_scesi : 0;
	rcp_video_conti(w ? w->rcp : NULL, spediti, abbandonati);
}

static void rcp_avvia(wt *w, int64_t stream_id)
{
	rcp_ganci g;

	w->rcp_stream = stream_id;

	memset(&g, 0, sizeof g);
	g.ctx = w;
	g.manda = gancio_manda;
	g.chiudi = gancio_chiudi;
	g.registra = gancio_registra;
	g.verifica = gancio_verifica;
	/* ⛔ E si collega SOLO se l'aiutante c'e': `rcp.c` guarda questo puntatore
	 *    per decidere quale delle due strade percorrere, e collegarlo a vuoto
	 *    vorrebbe dire dirgli «chiedi a nessuno». */
	if (w->aiuto)
		g.chiedi_verifica = gancio_chiedi;

	/* ⛔ §2.5: il canale video vive su stream unidirezionali del server.
	 *
	 * ⚠ E si collegano TUTTI E QUATTRO: `rcp.c` rifiuta di aprire se ne manca
	 *   uno, perche' un ospite che sapesse aprire e non azzerare non potrebbe
	 *   onorare §5.1 — e se ne accorgerebbe a meta' di un fotogramma.
	 * ⭐ La compatibilita' con l'innesto di `banchi/rcp/` e' gratis: li' il
	 *   `memset` di sopra li lascia a NULL, e `rcp_video_apri()` restituisce
	 *   `RCP_VIDEO_NIENTE_CANALE` invece di tacere. */
	g.video_apri = gancio_video_apri;
	g.video_scrivi = gancio_video_scrivi;
	g.video_fin = gancio_video_fin;
	g.video_azzera = gancio_video_azzera;

	/* ⭐⭐ §7.4 — IL CANALE APPUNTI, e si collegano TUTTI E CINQUE o nessuno.
	 *
	 * ⛔ E la condizione e' il ponte verso il palco, come per l'input: senza,
	 *    `rcp.c` convaliderebbe i messaggi (quello e' protocollo) e poi
	 *    dichiarerebbe di non aver servito niente.  ⚠ Ma i tre del FILO
	 *    dipendono solo dal trasporto, non dal palco: agganciarli tutti insieme
	 *    e' una scelta, e la ragione e' che meta' canale non serve a nessuno —
	 *    annunciare al client un testo che poi non si puo' spedire, o spedirgli
	 *    quel che ha copiato la sessione senza poter servire chi incolla, sono
	 *    due meta' che l'utente vede come «gli appunti non funzionano». */
	if (gancio_palco_appunti_offri && gancio_palco_appunti_risposta) {
		g.appunti_apri = gancio_appunti_apri;
		g.appunti_scrivi = gancio_appunti_scrivi;
		g.appunti_fin = gancio_appunti_fin;
		g.appunti_offri = gancio_appunti_offri;
		g.appunti_risposta = gancio_appunti_risposta;
	}

	/* ⭐⭐ §7.3 — IL CANALE DI INPUT.  ⛔ E si collegano TUTTI E SEI o nessuno:
	 *     `rcp.c` guarda il primo e se c'e' pretende gli altri, perche' un
	 *     canale che sapesse muovere il puntatore e non sapesse rilasciare un
	 *     pulsante lascerebbe il desktop **peggio di come l'ha trovato**.
	 * ⚠ E si collegano solo se il ponte verso il palco c'e': senza,
	 *   `rcp.c` convalida lo stesso il messaggio (quello e' protocollo) e
	 *   scrive che non l'ha iniettato.  «Non ho un canale di input» e «il
	 *   client ha sbagliato» sono due fatti diversi. */
	if (gancio_palco_input) {
		g.input_puntatore = gancio_input_puntatore;
		g.input_pulsante = gancio_input_pulsante;
		g.input_rotella = gancio_input_rotella;
		g.input_lettera = gancio_input_lettera;
		g.disposizione = gancio_disposizione;
		g.disposizione_esiste = gancio_disposizione_esiste;
		g.input_posizione = gancio_input_posizione;
		g.input_rilascia_tutto = gancio_input_rilascia_tutto;
	}

	/* ⭐⭐ §7.1 — IL GANCIO DELLA TELA, e si collega DA SOLO: non appartiene ai
	 *     sei dell'input, e la ragione e' che senza di lui `rcp.c` ha una
	 *     risposta giusta da dare — `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)` —
	 *     mentre senza i sei dell'input non ce l'ha.
	 * ⚠ E come quelli, si collega solo se il ponte verso il palco c'e': un
	 *   gancio collegato a vuoto direbbe a `rcp.c` «so ridimensionare» e poi
	 *   lascerebbe il client ad aspettare un fotogramma che nessuno ha chiesto a
	 *   nessuno. */
	if (gancio_palco_ritela)
		g.ritela = gancio_ritela;

	/* ⛔⭐ E QUESTO SI COLLEGA SEMPRE, anche senza il ponte verso il palco: non
	 *     chiede niente a nessuno — legge un numero che questo modulo ha gia',
	 *     l'ultima misura consegnata dal palco di quell'utente.  ⚠ Se non c'e'
	 *     ancora (primo attacco, nessun fotogramma) risponde `false`, e `rcp.c`
	 *     concede quel che il client chiede: il comportamento di prima. */
	g.tela_del_palco = gancio_tela_del_palco;

	/* ⛔⭐ §5.1 — e si collega SOLO se il guardiano c'e', come tutti gli altri:
	 *     un gancio collegato a vuoto direbbe a `rcp.c` «ho guardato, non c'e'
	 *     nessuna sessione locale», che e' la bugia peggiore delle due — perche'
	 *     e' indistinguibile dalla verita'. */
	if (gancio_locale)
		g.sessione_locale = gancio_sessione_locale;

	/* ⭐ §7.6 — e si collega solo se c'e' chi puo' davvero terminare la
	 *    sessione: senza, `rcp.c` congeda con `0x10` e scrive che il desktop
	 *    non e' stato toccato, invece di far credere che sia finito. */
	if (gancio_termina)
		g.termina_sessione = gancio_termina_sessione;

	/* ⛔ E il tetto di §7.17 si SPEGNE qui: il canale e' stato aperto, che e'
	 *    la cosa che quell'orologio aspettava.  ⚠ Zero e non «passato»: un
	 *    orologio disarmato e uno scaduto non devono avere la stessa faccia. */
	w->canale_entro = 0;

	w->rcp = rcp_apri(&g, w->provenienza,
	                  ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);

	/* ⛔ E QUI SI ARMA L'OROLOGIO DEL PRIMO TETTO — §4.6 riga 1.  `rcp_apri`
	 *    mette lo stato a `attesa-ciao` e fa partire il cronometro: il
	 *    cronometro e l'orologio che lo fara' scadere partono dalla stessa
	 *    riga.  Nell'innesto questo mancava, e un client che apriva il canale
	 *    e poi taceva restava appeso per sempre (`[M]` B6). */
	regola_battito(w);
	registro_dice(REG_RCP, "canale di controllo = stream %ld", (long)stream_id);
}

static void rcp_passa(wt *w, const uint8_t *dati, size_t len)
{
	uint64_t ora;
	if (!w->rcp)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi(w->rcp, dati, len, ora)) {
		/* La sessione e' finita.  Il battito che fa maturare la capsula
		 * di chiusura lo ha gia' armato `chiudi_sessione()`, che e'
		 * l'unico punto attraversato da TUTTE le strade della chiusura —
		 * comprese le due che da qui non passano affatto. */
		return;
	}
	/* ⭐ E QUI, non un giro dopo: `rcp_ricevi()` e' la riga che puo' aver
	 *    appena spedito `SESSIONE`, e aspettare il battito costerebbe fino a un
	 *    secondo intero prima che il desktop compaia — cioe' il numero che
	 *    l'utente guarda. */
	video_regola(w, ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);
	audio_regola(w);
	regola_battito(w);
}

/* ⭐⭐ IL CANALE DI INPUT — la cucitura della fase 4, 14 agosto 2026.
 *
 * ⛔ Prima di oggi i byte dell'input arrivavano davvero e finivano in
 *    `conta_credito()` **e basta**: il canale era lecito, la riga di registro
 *    lo dichiarava («questa fase non lo serve»), e il client poteva muovere il
 *    mouse per un'ora senza che al desktop arrivasse niente.  ⇒ Qui quella
 *    tolleranza dichiarata si CHIUDE.
 *
 * ⚠ `stream` viaggia con i byte e non e' un di piu': `RCP.md` §2.5 ammette
 *   **un solo** stream di input, e senza l'identificatore `rcp.c` non puo'
 *   distinguere il secondo stream dalla continuazione del primo.  ⛔ E chi
 *   ospita non lo puo' giudicare al posto suo: vede gli stream, ma non sa che
 *   cosa sia «di input» finche' non ha letto i primi due byte del carico.
 *
 * ⚠ E il ritorno `false` si tratta come in `rcp_passa()`: la sessione e'
 *   finita, e la capsula di chiusura l'ha gia' armata `chiudi_sessione()`. */
static void rcp_passa_input(wt *w, int64_t stream, const uint8_t *dati,
                            size_t len)
{
	uint64_t ora;
	if (!w->rcp || len == 0)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi_input(w->rcp, stream, dati, len, ora))
		return;
	/* ⛔ E il battito si rimette in riga anche di qui: un input puo' aver
	 *    fatto scattare un congedo (una violazione di §7.3), e aspettare il
	 *    giro dopo lascerebbe il motivo fermo in coda. */
	regola_battito(w);
}

/* ⭐⭐ FASE 7 — i byte del canale APPUNTI (0x02), §2.5 e §7.4.
 *
 * ⛔ E `fin` arriva fin qui, mentre per l'input non arrivava: la' lo stream e'
 *    uno solo e resta aperto, qui e' **uno per trasferimento** e la sua fine
 *    e' l'unico modo che `rcp.c` ha di liberare il posto in tabella.  ⚠ Senza,
 *    il canale funzionerebbe per i primi otto trasferimenti e poi smetterebbe
 *    — cioe' il difetto peggiore da diagnosticare: quello che compare dopo. */
static void rcp_passa_appunti(wt *w, int64_t stream, const uint8_t *dati,
                              size_t len, bool fin)
{
	uint64_t ora;
	if (!w->rcp)
		return;
	if (len == 0 && !fin)
		return;
	ora = ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS;
	if (!rcp_ricevi_appunti(w->rcp, stream, dati, len, fin, ora))
		return;
	regola_battito(w);
}

/* ------------------------------------------------------------------------ */
/* La chiusura della sessione WebTransport.                                  */

static void chiudi_adesso(wt *w, uint8_t motivo)
{
	uint8_t b[16];
	size_t n = 0;

	/* ⛔⭐ LA CAPSULA VA DENTRO UN FRAME `DATA`, E NELL'INNESTO USCIVA NUDA.
	 *
	 *    Il corpo di una CONNECT estesa e' un flusso di capsule (RFC 9297),
	 *    ma in HTTP/3 il corpo di un messaggio viaggia dentro frame `DATA`:
	 *    la capsula NON sta nuda sullo stream.  ⭐ E che il client le
	 *    incapsuli lo dimostra il nostro stesso lato di LETTURA: la capsula
	 *    ci arriva da `recv_data`, che nghttp3 invoca soltanto sul carico
	 *    utile di un `DATA`.
	 *
	 * ⛔ Scritti nudi, i sette byte `68 43 04 00 00 00 mm` il browser li
	 *    legge col proprio strato HTTP/3: `0x68` ha i due bit alti a `01`,
	 *    quindi e' un intero variabile di due byte, e il tipo di frame
	 *    diventa `0x2843` — che non e' un tipo di frame HTTP/3 noto, e RFC
	 *    9114 §9 impone di IGNORARLO.  La pagina non vedeva nessuna capsula:
	 *    vedeva solo il FIN che arriva subito dietro, e un FIN sullo stream
	 *    della CONNECT senza `CLOSE_WEBTRANSPORT_SESSION` chiude la sessione
	 *    con codice 0 — cioe' il solo valore che `RCP.md` §3.1 vieta. */
	b[n++] = 0x00; /* frame DATA */
	b[n++] = 7;    /* 2 byte di tipo + 1 di lunghezza + 4 di codice */
	b[n++] = 0x68; /* 0x2843, primo byte dell'intero variabile */
	b[n++] = 0x43;
	b[n++] = 4; /* la lunghezza della capsula: solo il codice */
	b[n++] = 0;
	b[n++] = 0;
	b[n++] = 0;
	b[n++] = motivo;

	if (!coda_metti(w, w->sessione, b, n, true)) {
		registro_dice(REG_WT, "⛔ la capsula di chiusura non entra in coda");
		return;
	}
	registro_dice(REG_WT,
	              "chiusa la sessione WebTransport, codice 0x%02x (%zu byte: "
	              "2 di frame DATA + 7 di capsula)",
	              motivo, n);
}

static void chiudi_sessione(wt *w, uint8_t motivo)
{
	/* ⛔ `RCP.md` §3.1 punto 3: si chiude la SESSIONE WebTransport con il
	 *    codice d'errore applicativo pari al codice del motivo — non la
	 *    connessione QUIC, che puo' reggere altro. */
	if (w->sessione == -1)
		return;

	/* ⛔⭐ E LA CAPSULA SI RIMANDA, invece di accodarla adesso — trovato da
	 *     B11 il 10 agosto 2026, con browser veri.
	 *
	 *     `respingi()` manda `RESPINTO` sul canale di controllo e chiude la
	 *     sessione nella riga dopo.  I due finivano nella stessa passata di
	 *     scrittura, cioe' spesso nello stesso volo di pacchetti — e il
	 *     browser processa la capsula `CLOSE_WEBTRANSPORT_SESSION` PRIMA dei
	 *     byte dello stream, che a quel punto butta.  ⛔ La pagina non ha
	 *     mai visto `RESPINTO`: ha visto silenzio.
	 *
	 * ⛔ E ACCODARE LA CAPSULA DIETRO AL `CONGEDO`, NELLA STESSA CODA, NON E'
	 *    LA CURA: l'ordine sul filo ci sarebbe, ⚠ ma l'ordine sul filo non e'
	 *    quel che manca.  Quel che serve e' TEMPO fra i due. */
	w->chiusura = motivo;
	/* ⛔⭐ L'ATTESA PARTE ADESSO, non «quando un battito vedra' la coda vuota»
	 *     — misurato dal banco B7 l'11 agosto 2026, caso `server-in-chiusura`.
	 *
	 *     Qui c'era `w->chiusura_da = 0`, cioe' «non armato»: ad armarlo era
	 *     il ramo di `wt_batti` che trova la coda gia' vuota.  ⛔ Allo
	 *     spegnimento quel ramo non veniva percorso mai — il registro del
	 *     server lo ha detto con queste parole: «capsula di chiusura non
	 *     ancora matura (coda vuota) — chiusura_da = MAI ARMATO» dopo 200
	 *     giri, quando ne bastavano cinquanta.
	 *
	 * ⛔ Che cosa vedeva il client: il `CONGEDO 0x0c` arrivava, e la sessione
	 *    si chiudeva SENZA codice — QUIC terminato con `codice 0, nessun
	 *    motivo`.  Cioe' mancava la SECONDA strada di §3.1 punto 3, che le
	 *    decisioni dell'11 agosto (§7.14, §7.15) rendono l'unica che arrivi
	 *    sempre — su Firefox, che azzera il canale, era l'UNICA.
	 *
	 * ⚠ E il senso non cambia: se la coda NON e' vuota, il ramo `!coda_vuota`
	 *   di `wt_batti` riazzera questo campo e l'attesa riparte da capo, come
	 *   prima.  Quel che cambia e' che adesso l'attesa esiste anche quando
	 *   nessuno ripassa a dire «la coda e' vuota». */
	w->chiusura_da = ngtcp2_conn_get_timestamp(w->conn)
	                 + WT_ATTESA_CHIUSURA_NS;
	/* ⛔ E L'ATTESA HA UN FONDO — rilievo B-3.  «Quando la coda si sara'
	 *    svuotata» e' una condizione che qualcun altro deve far avvenire; se
	 *    non avviene, il punto 3 di §3.1 non si esegue mai e il motivo resta
	 *    dentro il server.  Tre secondi sono sei volte l'attesa normale. */
	w->chiusura_scadenza =
	    ngtcp2_conn_get_timestamp(w->conn) + 3ULL * NGTCP2_SECONDS;
	/* ⛔ E chi rimanda un lavoro deve accendere anche cio' che lo fara'
	 *    maturare: senza questo battito, su una violazione trovata al primo
	 *    messaggio il client tace, nessuno ripassa di qui e la capsula non
	 *    parte mai.  ⚠ E' il difetto misurato da B5 — 22 su 36. */
	batti_fra(w, 100);
	registro_dice(REG_WT,
	              "chiusura della sessione RIMANDATA, codice 0x%02x (in coda: "
	              "%zu elementi ancora da spedire)",
	              motivo, coda_da_spedire(w));
}

static void manda_controllo(wt *w, const uint8_t *dati, size_t len)
{
	if (w->rcp_stream == -1)
		return;
	(void)accoda(w, w->rcp_stream, dati, len);
}

/* ⛔⭐ I BYTE DI UNO STREAM DI TROPPO SI BUTTANO, E NON SI RIMANDANO INDIETRO
 *     — rilievo B-3, 10 agosto 2026 notte.
 *
 *     Qui c'era `accoda(w, stream_id, dati, len)`, cioe' il server rispediva
 *     al client i suoi stessi byte su uno stream che due righe piu' su aveva
 *     appena giudicato una **violazione di §2.5**.  ⛔ Un'eco che nessuna riga
 *     di `RCP.md` prevede, e tre conseguenze una peggiore dell'altra:
 *
 *       1. `coda_vuota()` non tornava mai vera, quindi la capsula di chiusura
 *          di §3.1 punto 3 non partiva mai (vedi `chiusura_scadenza`);
 *       2. `conta_credito()` riapriva la finestra a ogni giro, quindi il
 *          client poteva scrivere senza fine — e l'inattivita' di 30 s non
 *          scattava, perche' stava scrivendo;
 *       3. la coda cresceva quanto il client voleva, su una sessione gia'
 *          dichiarata morta (vedi `WT_CODA_MAX`).
 *
 * ⭐ Quel che si fa invece: si butta, NON si riapre il credito, e §3 lo impone
 *    — «e ogni tolleranza va scritta nel registro».  ⚠ Le righe sono contate e
 *    non una per pacchetto: un client che scrive senza fine riempirebbe il
 *    registro, che e' un altro modo di perdere l'informazione. */
static void scarta_stream_di_troppo(wt *w, int64_t stream_id, size_t len)
{
	w->scartati_stream++;
	w->scartati_byte += len;
	if (w->scartati_stream <= 3 || (w->scartati_stream % 256) == 0)
		registro_dice(REG_WT,
		              "⛔ %zu byte BUTTATI dallo stream %ld: non e' il canale "
		              "di controllo (§2.5, la violazione e' gia' a verbale) — "
		              "%llu blocchi, %llu byte in tutto, e il credito NON si "
		              "riapre",
		              len, (long)stream_id,
		              (unsigned long long)w->scartati_stream,
		              (unsigned long long)w->scartati_byte);
}

/* ------------------------------------------------------------------------ */
/* Le capsule che arrivano dal client.                                       */

static void chiusa_dal_client(wt *w, uint32_t codice)
{
	bool valido;
	uint8_t motivo;

	/* ⛔⭐ E PRIMA DI TUTTO SI GUARDA SE QUEL CODICE ESISTE.
	 *
	 *    `RCP.md` §3.1: il codice 0 significa «chiusura senza motivo» e NON
	 *    DEVE essere usato — ogni chiusura ha un motivo di §8.2.  E §3 — la
	 *    regola di rigore — chiede di scrivere NEL REGISTRO che cosa non si
	 *    e' capito, non di supplire in silenzio.
	 *
	 * ⛔ E IL CODICE ARRIVA SU 32 BIT, NON SU 8: troncarlo al byte basso
	 *    faceva entrare a verbale `0x0100` come `0x00`, cioe' come il solo
	 *    valore che §3.1 vieta, e i due registri della STESSA chiusura si
	 *    contraddicevano a due righe di distanza. */
	valido = codice >= (uint32_t)RCP_CHIUSO_DALL_UTENTE &&
	         codice <= (uint32_t)RCP_GIA_ATTIVA_REMOTA;
	if (!valido)
		registro_dice(REG_RCP,
		              "⛔ VIOLAZIONE §3.1 — la pagina ha chiuso la sessione "
		              "col codice 0x%x, che non e' un motivo di §8.2 "
		              "(0 = «senza motivo», ed e' vietato).  A verbale va "
		              "ERRORE_PROTOCOLLO",
		              codice);
	motivo = (uint8_t)(valido ? codice : (uint32_t)RCP_ERRORE_PROTOCOLLO);

	if (w->rcp && rcp_e_finita(w->rcp))
		registro_dice(REG_RCP,
		              "⭐ il motivo e' arrivato per la seconda strada di "
		              "§3.1 (il codice di chiusura): 0x%02x — i byte sul "
		              "canale non erano piu' spedibili",
		              motivo);
	/* ⛔ E il POSTO si lascia adesso: §4.2, la sessione e' finita perche' lo
	 *    dice il client.  Aspettare lo smontaggio del trasporto vuol dire
	 *    tenerlo occupato addosso a chi si ricollega subito. */
	if (w->rcp)
		rcp_chiusa_dal_client(w->rcp, motivo);
}

/* ⛔⭐ Il corpo di una CONNECT estesa e' un flusso di capsule (RFC 9297):
 * varint tipo, varint lunghezza, corpo.  Di tutte, qui se ne guarda UNA:
 * `CLOSE_WEBTRANSPORT_SESSION` (0x2843).  ⚠ Si accumula, perche' una capsula
 * puo' arrivare a pezzi; e si scarta il resto senza rumore, perche' un flusso
 * di capsule sconosciute non e' un errore (RFC 9297 §3.2). */
static void capsula(wt *w, int64_t stream_id, const uint8_t *dati, size_t len)
{
	if (stream_id != w->sessione || len == 0)
		return;

	/* ⛔ I byte di una capsula gia' giudicata troppo grande si buttano
	 *    MENTRE PASSANO, senza tenerli: e' l'unico modo di non farsi
	 *    riempire la memoria da chi sa scrivere due interi variabili. */
	if (w->capsalta > 0) {
		uint64_t n = w->capsalta < len ? w->capsalta : (uint64_t)len;
		w->capsalta -= n;
		dati += n;
		len -= (size_t)n;
		if (len == 0)
			return;
	}
	if (!bytes_aggiungi(&w->capsbuf, dati, len))
		return;

	for (;;) {
		uint64_t tipo = 0, lung = 0;
		size_t a, b;
		const uint8_t *corpo;

		/* ⚠ Qui il buffer non puo' crescere senza fine: un intero
		 *   variabile e' al massimo 8 byte, quindi con 16 byte tipo e
		 *   lunghezza si leggono sempre. */
		a = varint_leggi(&tipo, w->capsbuf.d, w->capsbuf.n);
		if (a == 0)
			return;
		b = varint_leggi(&lung, w->capsbuf.d + a, w->capsbuf.n - a);
		if (b == 0)
			return;

		/* ⛔⭐ E LA LUNGHEZZA SI CONTROLLA QUI, PRIMA DI ASPETTARE I BYTE.
		 *
		 *    L'ingresso che questo chiude: la pagina manda, sullo stream
		 *    della CONNECT, un tipo di capsula sconosciuto e una
		 *    lunghezza di 2^62-1, poi manda dati all'infinito.  Nessuna
		 *    capsula si completava mai, il buffer cresceva di ogni byte
		 *    che arrivava — e il credito continuava ad allargarsi, quindi
		 *    il client poteva spedire senza fine.  ⛔ Su una connessione
		 *    che non ha ancora superato la stretta di mano di RCP. */
		if (lung > WT_CAPSULA_MAX) {
			uint64_t qui = w->capsbuf.n - a - b;
			uint64_t presi = qui < lung ? qui : lung;
			registro_dice(REG_WT,
			              "capsula 0x%llx lunga %llu byte, oltre il "
			              "tetto di %d: si SALTA senza tenerla (RFC "
			              "9297 §3.2; RCP.md §6.1)",
			              (unsigned long long)tipo,
			              (unsigned long long)lung, WT_CAPSULA_MAX);
			w->capsalta = lung - presi;
			bytes_togli_testa(&w->capsbuf, a + b + (size_t)presi);
			if (w->capsalta > 0)
				return;
			continue;
		}
		if (w->capsbuf.n < a + b + lung)
			return; /* sta sotto il tetto: si puo' aspettare */

		corpo = w->capsbuf.d + a + b;
		if (tipo == 0x2843 && lung >= 4) {
			uint32_t codice = ((uint32_t)corpo[0] << 24) |
			                  ((uint32_t)corpo[1] << 16) |
			                  ((uint32_t)corpo[2] << 8) |
			                  (uint32_t)corpo[3];
			registro_dice(REG_WT,
			              "la pagina ha CHIUSO la sessione "
			              "WebTransport: codice 0x%x",
			              codice);
			chiusa_dal_client(w, codice);
		}
		bytes_togli_testa(&w->capsbuf, a + b + (size_t)lung);
	}
}

/* ------------------------------------------------------------------------ */
/* Lo smistamento: che cosa e' WebTransport e che cosa e' di nghttp3.        */

/* ⛔ `RCP.md` §4.2: «un FIN su quello stream, da una qualunque delle due parti,
 *    chiude la sessione.  Chi lo riceve DEVE considerarla finita».  ⚠ Era
 *    l'unica delle due direzioni che nessuno aveva percorso: la pagina che
 *    chiude la parte scrivente del canale e tiene viva la connessione lasciava
 *    il posto del registro occupato finche' non moriva la connessione — e una
 *    connessione un browser la tiene viva. */
static void fin_dal_client(wt *w, int64_t stream_id)
{
	if (!w->rcp || stream_id != w->rcp_stream)
		return;
	registro_dice(REG_RCP,
	              "⛔ FIN del CLIENT sul canale di controllo (stream %ld): "
	              "§4.2, la sessione e' finita",
	              (long)stream_id);
	rcp_canale_chiuso(w->rcp);
}

static void conta_credito(wt *w, int64_t stream_id, size_t n)
{
	if (n == 0)
		return;
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, n);
	ngtcp2_conn_extend_max_offset(w->conn, n);
}

enum esito { E_MIO, E_ATTENDI, E_HTTP3 };

/* ⛔ `RCP.md` §2.5 — gli stream unidirezionali aperti dal CLIENT.
 *
 * ⭐ Come si riconosce il canale: «si leggono i primi due byte dello stream,
 *    che sono in ogni caso un campo `tipo`».  Il byte alto dice il canale, e di
 *    cinque valori leciti TRE sono violazioni quando arrivano di qui:
 *
 *    0x00  controllo  ⛔ il controllo vive solo sul primo bidirezionale
 *    0x01  input      ✓  legale: e' l'unico unidirezionale che il client apre
 *    0x02  appunti    ✓  legale, uno per trasferimento
 *    0x03  video      ⛔ verso sbagliato: il video va dal server al client
 *    0x04  audio      ⛔ «solo su datagram.  Su uno stream e' ERRORE_PROTOCOLLO»
 *
 * ⚠ E prima ancora bisogna sapere se lo stream e' NOSTRO: fra gli
 *   unidirezionali del client ci sono il canale di controllo di HTTP/3 e i due
 *   di QPACK, che sono di nghttp3.  Uno stream WebTransport si riconosce dal
 *   suo tipo, 0x54 — che come 0x41 non sta in un byte: sul filo sono 0x40 0x54. */
static enum esito smista_uni(wt *w, int64_t stream_id, const uint8_t *dati,
                             size_t len, bool fin, bytes *riunito)
{
	stream_giudizio *g = giudizio_trova(w, stream_id);
	uint64_t sessione = 0;
	size_t n, consumati;
	uint16_t tipo;
	uint8_t canale;
	const uint8_t *carico = NULL;
	size_t carico_n = 0;
	const char *guasto = NULL;

	if (g) {
		switch (g->genere) {
		case G_NONWT:
			return E_HTTP3;
		case G_UNI_OK:
		case G_UNI_KO:
			/* ⚠ I due giudizi NON sono la stessa cosa:
			 *   G_UNI_KO  violazione, la sessione e' gia' caduta;
			 *   G_UNI_OK  canale LECITO di §2.5 che questa fase non
			 *             serve ancora (l'input arriva alla fase 4,
			 *             gli appunti alla 7).
			 *   ⛔ Nell'innesto entrambi erano segnati «violazione»,
			 *      e un client conforme che apriva il canale di input
			 *      si vedeva scartare OGNI byte per sempre, senza una
			 *      riga di registro.
			 *   In tutt'e due i casi i byte si contano nel credito:
			 *   non contarli lascerebbe il client senza credito su
			 *   una connessione viva (§2.3). */
			conta_credito(w, stream_id, len);
			return E_MIO;
		case G_UNI_INPUT:
			/* ⭐ Il canale di input, gia' riconosciuto: i byte si
			 *    contano nel credito **e si consegnano**.  ⛔ Il
			 *    credito prima della consegna: se la consegna facesse
			 *    cadere la sessione, quei byte sono comunque arrivati
			 *    e il conto di §2.3 non deve restare indietro. */
			conta_credito(w, stream_id, len);
			rcp_passa_input(w, stream_id, dati, len);
			return E_MIO;
		case G_UNI_APPUNTI:
			/* ⭐ Il canale appunti, gia' riconosciuto.  ⛔ Il credito PRIMA
			 *    della consegna, come per l'input, e per la stessa ragione: se
			 *    la consegna facesse cadere la sessione, quei byte sono
			 *    comunque arrivati e il conto di §2.3 non deve restare
			 *    indietro. */
			conta_credito(w, stream_id, len);
			rcp_passa_appunti(w, stream_id, dati, len, fin);
			return E_MIO;
		default:
			break;
		}
	} else {
		g = giudizio_crea(w, stream_id);
		if (!g)
			return E_HTTP3;
	}

	if (!bytes_aggiungi(&g->pref, dati, len))
		return E_HTTP3;
	if (g->pref.n < 2)
		return E_ATTENDI;

	if (!(g->pref.d[0] == 0x40 && g->pref.d[1] == 0x54)) {
		/* Non e' WebTransport: e' di nghttp3, e i byte vanno consegnati
		 * interi — compresi quelli che abbiamo trattenuto. */
		bytes_aggiungi(riunito, g->pref.d, g->pref.n);
		bytes_libera(&g->pref);
		g->genere = G_NONWT;
		return E_HTTP3;
	}
	n = varint_leggi(&sessione, g->pref.d + 2, g->pref.n - 2);
	if (n == 0 || g->pref.n < 2 + n + 2)
		return E_ATTENDI; /* il campo `tipo` non e' ancora tutto arrivato */

	consumati = g->pref.n;
	tipo = (uint16_t)((g->pref.d[2 + n] << 8) | g->pref.d[2 + n + 1]);
	canale = (uint8_t)(tipo >> 8);
	/* ⛔ IL CARICO RCP COMINCIA QUI, e comincia **col `tipo`**: i due byte che
	 *    abbiamo appena sbirciato per sapere di che canale si tratta sono del
	 *    messaggio, non del preambolo.  ⚠ Sbirciarli e poi non consegnarli
	 *    darebbe a `rcp.c` un messaggio senza intestazione — e il sintomo
	 *    sarebbe «il primo input di ogni sessione e' malformato».
	 * ⚠ E `bytes_libera()` e' stato spostato in fondo apposta: fino a quel
	 *   momento `carico` punta dentro `g->pref`. */
	carico = g->pref.d + 2 + n;
	carico_n = g->pref.n - (2 + n);
	conta_credito(w, stream_id, consumati);

	switch (canale) {
	case 0x00:
		guasto = "il canale di CONTROLLO su uno stream unidirezionale: il "
		         "controllo vive solo sul primo stream bidirezionale (§2.5)";
		break;
	case 0x03:
		guasto = "il canale VIDEO dal client: e' del server, verso sbagliato "
		         "(§2.5)";
		break;
	case 0x04:
		guasto = "il canale AUDIO su uno stream: l'audio vive solo sui "
		         "datagram (§2.5, §6.3)";
		break;
	case 0x01:
	case 0x02:
		break;
	default:
		guasto = "byte alto del tipo sconosciuto su uno stream "
		         "unidirezionale (§2.5)";
		break;
	}
	g->genere = guasto           ? G_UNI_KO
	            : canale == 0x01 ? G_UNI_INPUT
	            : canale == 0x02 ? G_UNI_APPUNTI
	                             : G_UNI_OK;
	registro_dice(REG_WT,
	              "stream unidirezionale %ld del client, sessione %llu, tipo "
	              "0x%04x, canale 0x%02x — %s",
	              (long)stream_id, (unsigned long long)sessione, tipo, canale,
	              guasto ? "VIOLAZIONE"
	              : canale == 0x01
	                     ? "⭐ INPUT, e da oggi si SERVE: i byte vanno a "
	                       "rcp_ricevi_input() (§7.3)"
	              : canale == 0x02
	                     ? "⭐ APPUNTI, e dalla fase 7 si SERVONO: i byte vanno "
	                       "a rcp_ricevi_appunti() (§7.4).  ⚠ Uno stream per "
	                       "trasferimento, quindi di questi ce n'e' piu' d'uno"
	                     : "lecito (§2.5).  ⚠ Ma questa fase non lo serve: i "
	                       "byte si contano nel credito e si scartano, e "
	                       "questa riga e' la tolleranza dichiarata (§3)");
	if (guasto) {
		if (w->rcp) {
			rcp_violazione(w->rcp, guasto);
		} else {
			/* ⚠ Nessun canale di controllo ancora aperto: il `CONGEDO`
			 *   non ha una strada, e resta il punto 3 di §3.1 — il
			 *   motivo dentro la chiusura della sessione.  ⭐ E' il
			 *   secondo condizionale di §3.1 all'opera: pretendere
			 *   tutt'e tre i punti sempre darebbe rosso sul codice
			 *   giusto. */
			registro_dice(REG_WT,
			              "⚠ nessun canale di controllo: il motivo "
			              "viaggia solo nella chiusura della sessione");
			chiudi_sessione(w, RCP_ERRORE_PROTOCOLLO);
		}
	} else if (canale == 0x01) {
		/* ⭐ Il primo pezzo del canale di input arriva insieme al
		 *    preambolo che l'ha fatto riconoscere: si consegna SUBITO.
		 *    ⛔ Aspettare il pacchetto dopo perderebbe il primo
		 *    messaggio di ogni sessione — e il primo messaggio e'
		 *    proprio quello che l'utente sente come «il primo clic non
		 *    ha fatto niente». */
		rcp_passa_input(w, stream_id, carico, carico_n);
	} else if (canale == 0x02) {
		/* ⭐ Come per l'input: il primo pezzo arriva insieme al preambolo che
		 *    l'ha fatto riconoscere, e si consegna SUBITO.  ⛔ Aspettare il
		 *    pacchetto dopo perderebbe il primo messaggio di ogni
		 *    trasferimento — e su questo canale un trasferimento e' spesso UN
		 *    messaggio solo, quindi si perderebbe il trasferimento intero.
		 * ⚠ E il `fin` viaggia con lui: uno stream che porta un messaggio corto
		 *   puo' arrivare tutto insieme, preambolo e FIN compresi. */
		rcp_passa_appunti(w, stream_id, carico, carico_n, fin);
	}
	bytes_libera(&g->pref);
	return E_MIO;
}

static enum esito smista(wt *w, int64_t stream_id, const uint8_t *dati,
                         size_t len, bool fin, bytes *riunito)
{
	stream_giudizio *g;
	uint64_t sessione = 0;
	size_t n, consumati;

	/* ⛔ Gli unidirezionali APERTI DAL CLIENT (§2.5) passano di qui prima di
	 *    tutto: fra loro c'e' il canale di controllo di HTTP/3 e i due di
	 *    QPACK, che sono di nghttp3 e non nostri. */
	if ((stream_id & 0x03) == 0x02)
		return smista_uni(w, stream_id, dati, len, fin, riunito);

	/* Solo gli stream bidirezionali aperti dal client: la CONNECT estesa e
	 * gli stream WebTransport arrivano tutti di li'. */
	if ((stream_id & 0x03) != 0x00)
		return E_HTTP3;

	g = giudizio_trova(w, stream_id);
	if (g && g->genere == G_NONWT)
		return E_HTTP3;

	if (g && g->genere == G_WT) {
		/* ⭐ Uno stream WebTransport gia' riconosciuto. */
		if (len > 0) {
			if (stream_id == w->rcp_stream) {
				rcp_passa(w, dati, len);
				conta_credito(w, stream_id, len);
			} else {
				/* ⛔ NON si rimandano indietro e NON si riapre il
				 *    credito: vedi `scarta_stream_di_troppo()`. */
				scarta_stream_di_troppo(w, stream_id, len);
			}
		}
		/* ⛔ E IL FIN SI GUARDA DOPO I BYTE, non prima: gli ultimi byte
		 *    sono arrivati INSIEME a lui e vanno consegnati mentre la
		 *    sessione e' ancora viva, o chi li riceve li leggerebbe come
		 *    byte spediti dopo la fine — cioe' come una violazione del
		 *    client che non c'e' stata. */
		if (fin)
			fin_dal_client(w, stream_id);
		return E_MIO;
	}

	if (!g) {
		g = giudizio_crea(w, stream_id);
		if (!g)
			return E_HTTP3;
	}
	if (!bytes_aggiungi(&g->pref, dati, len))
		return E_HTTP3;
	if (g->pref.n < 2) {
		/* ⚠ E NON si allarga la finestra: quei byte non li ha ancora
		 *   presi nessuno, e contarli adesso e poi di nuovo falserebbe il
		 *   credito. */
		return E_ATTENDI;
	}

	/* ⛔ Il tipo di frame WEBTRANSPORT_STREAM e' 0x41 — ma un intero
	 *    variabile non lo scrive in un byte: 0x41 vale 65, e in un byte ce
	 *    ne stanno 63.  Sul filo sono DUE byte, 0x40 0x41, ed e' per questo
	 *    che due bastano a decidere.  Un frame HEADERS comincia per 0x01,
	 *    uno DATA per 0x00. */
	if (!(g->pref.d[0] == 0x40 && g->pref.d[1] == 0x41)) {
		bytes_aggiungi(riunito, g->pref.d, g->pref.n);
		bytes_libera(&g->pref);
		g->genere = G_NONWT;
		return E_HTTP3;
	}

	n = varint_leggi(&sessione, g->pref.d + 2, g->pref.n - 2);
	if (n == 0)
		return E_ATTENDI;

	consumati = g->pref.n;
	g->genere = G_WT;

	/* ⭐ `RCP.md` §4.2: il PRIMO stream bidirezionale che il client apre
	 *    nella sessione e' il canale di controllo.
	 *
	 * ⚠ E «il primo» QUI e' il primo RICONOSCIUTO, non il primo APERTO: i
	 *   due stream viaggiano in pacchetti diversi, e fra stream diversi la
	 *   rete non promette nessun ordine. */
	if (w->rcp_stream == -1) {
		rcp_avvia(w, stream_id);
	} else {
		/* ⛔ `RCP.md` §2.5: «il client NON DEVE aprire stream
		 *    bidirezionali oltre lo 0».  Un secondo bidirezionale non e'
		 *    un canale nuovo: e' una violazione.
		 *
		 * ⛔ E LA DIAGNOSI NON DEVE INCOLPARE L'ORDINE D'ARRIVO.  Se
		 *    questo stream ha un numero PIU' BASSO di quello eletto, il
		 *    primo aperto era lui, e a scambiarli e' stata la rete: gli
		 *    stream restano due — e due e' la violazione, comunque siano
		 *    arrivati — ma «un secondo stream» detto del numero piu'
		 *    basso manda a cercare il difetto nel client, che li' non ha
		 *    sbagliato niente. */
		if (stream_id < w->rcp_stream)
			registro_dice(REG_WT,
			              "⛔ due stream bidirezionali dal client dentro "
			              "la sessione: %ld e %ld — e il PRIMO APERTO "
			              "era il %ld, arrivato per secondo: il canale "
			              "di controllo e' stato eletto per ordine "
			              "d'arrivo, non per numero",
			              (long)w->rcp_stream, (long)stream_id,
			              (long)stream_id);
		else
			registro_dice(REG_WT,
			              "⛔ due stream bidirezionali dal client dentro "
			              "la sessione: il controllo e' il %ld, e il %ld "
			              "e' di troppo",
			              (long)w->rcp_stream, (long)stream_id);
		if (w->rcp)
			rcp_violazione(w->rcp,
			               "due stream bidirezionali dal client dentro "
			               "la sessione (§2.5)");
	}
	registro_dice(REG_WT, "stream %ld e' WebTransport, sessione %llu",
	              (long)stream_id, (unsigned long long)sessione);

	if (consumati > 2 + n) {
		const uint8_t *resto = g->pref.d + 2 + n;
		size_t rn = consumati - 2 - n;
		if (stream_id == w->rcp_stream)
			rcp_passa(w, resto, rn);
		else
			scarta_stream_di_troppo(w, stream_id, rn);
	}
	bytes_libera(&g->pref);
	/* ⚠ Il credito dei byte del PREFISSO si riapre comunque: quei byte li
	 *   abbiamo consumati noi per giudicare lo stream, e non contarli
	 *   bloccherebbe anche il canale di controllo legittimo.  ⛔ Quel che NON
	 *   si riapre e' il credito dei byte di un canale di troppo — vedi il
	 *   ramo qui sopra e `scarta_stream_di_troppo()`. */
	conta_credito(w, stream_id, consumati);

	/* ⛔ Anche qui: lo stream puo' essere riconosciuto e finito nello stesso
	 *    pacchetto (§4.2, il FIN da una qualunque delle due parti). */
	if (fin)
		fin_dal_client(w, stream_id);
	return E_MIO;
}

/* ------------------------------------------------------------------------ */
/* I richiami di nghttp3.                                                    */

static int cb_acked(nghttp3_conn *conn, int64_t stream_id, uint64_t datalen,
                    void *cud, void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)datalen;
	(void)cud;
	(void)sud;
	return 0;
}

static int cb_recv_data(nghttp3_conn *conn, int64_t stream_id,
                        const uint8_t *data, size_t datalen, void *cud,
                        void *sud)
{
	wt *w = cud;
	(void)sud;
	(void)conn;
	/* ⭐ Il corpo della CONNECT e' un flusso di capsule. */
	capsula(w, stream_id, data, datalen);
	/* I byte del corpo si contano nel credito: senza, il client resta senza
	 * finestra su una connessione viva (§2.3). */
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, datalen);
	ngtcp2_conn_extend_max_offset(w->conn, datalen);
	return 0;
}

static int cb_deferred_consume(nghttp3_conn *conn, int64_t stream_id,
                               size_t consumed, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_extend_max_stream_offset(w->conn, stream_id, consumed);
	ngtcp2_conn_extend_max_offset(w->conn, consumed);
	return 0;
}

static int cb_begin_headers(nghttp3_conn *conn, int64_t stream_id, void *cud,
                            void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	if (!richiesta_trova(w, stream_id, true))
		return NGHTTP3_ERR_CALLBACK_FAILURE;
	return 0;
}

static void copia(char *fuori, size_t cap, nghttp3_rcbuf *v)
{
	nghttp3_vec b = nghttp3_rcbuf_get_buf(v);
	size_t n = b.len < cap - 1 ? b.len : cap - 1;
	memcpy(fuori, b.base, n);
	fuori[n] = 0;
}

static int cb_recv_header(nghttp3_conn *conn, int64_t stream_id, int32_t token,
                          nghttp3_rcbuf *name, nghttp3_rcbuf *value,
                          uint8_t flags, void *cud, void *sud)
{
	wt *w = cud;
	richiesta *r = richiesta_trova(w, stream_id, true);
	(void)conn;
	(void)name;
	(void)flags;
	(void)sud;
	if (!r)
		return 0;
	switch (token) {
	case NGHTTP3_QPACK_TOKEN__PATH:
		copia(r->uri, sizeof r->uri, value);
		break;
	case NGHTTP3_QPACK_TOKEN__METHOD:
		copia(r->metodo, sizeof r->metodo, value);
		break;
	/* ⭐ L'intestazione che distingue una CONNECT estesa da una CONNECT
	 *    normale (RFC 9220). */
	case NGHTTP3_QPACK_TOKEN__PROTOCOL:
		copia(r->protocollo, sizeof r->protocollo, value);
		break;
	default:
		break;
	}
	return 0;
}

/* Lo stream della CONNECT estesa NON si chiude: E' la sessione.  Un lettore che
 * dicesse «ho finito» ci metterebbe sopra il FIN, e la sessione morirebbe
 * nell'istante in cui si apre. */
static nghttp3_ssize cb_niente_dati(nghttp3_conn *conn, int64_t stream_id,
                                    nghttp3_vec *vec, size_t veccnt,
                                    uint32_t *pflags, void *cud, void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)vec;
	(void)veccnt;
	(void)pflags;
	(void)cud;
	(void)sud;
	return NGHTTP3_ERR_WOULDBLOCK;
}

static int risposta_secca(wt *w, int64_t stream_id, const char *stato)
{
	nghttp3_nv nv[2];
	int rv;

	nv[0].name = (uint8_t *)":status";
	nv[0].namelen = 7;
	nv[0].value = (uint8_t *)stato;
	nv[0].valuelen = strlen(stato);
	nv[0].flags = NGHTTP3_NV_FLAG_NONE;
	nv[1].name = (uint8_t *)"server";
	nv[1].namelen = 6;
	nv[1].value = (uint8_t *)"remotix";
	nv[1].valuelen = 7;
	nv[1].flags = NGHTTP3_NV_FLAG_NONE;

	rv = nghttp3_conn_submit_response(w->h3, stream_id, nv, 2, NULL);
	if (rv != 0)
		registro_dice(REG_WT, "⛔ nghttp3_conn_submit_response: %s",
		              nghttp3_strerror(rv));
	return rv;
}

static int apri_sessione(wt *w, richiesta *r)
{
	nghttp3_nv nv[2];
	nghttp3_data_reader dr;
	int rv;

	/* ⛔ `RCP.md` §2.2: il server NON DEVE accettare una sessione
	 *    WebTransport su un percorso diverso, e il rifiuto e' 404 (rilievo
	 *    R1.24, che ha scelto uno dei tre stati che erano tutti leciti).  E
	 *    si scrive nel registro: e' §3 applicata al primo byte, prima ancora
	 *    che RCP cominci. */
	if (strcmp(r->uri, "/rcp/1") != 0) {
		registro_dice(REG_WT,
		              "⛔ sessione WebTransport RIFIUTATA, percorso «%s» "
		              "(atteso /rcp/1 — §2.2): 404",
		              r->uri);
		return risposta_secca(w, r->id, "404");
	}

	nv[0].name = (uint8_t *)":status";
	nv[0].namelen = 7;
	nv[0].value = (uint8_t *)"200";
	nv[0].valuelen = 3;
	nv[0].flags = NGHTTP3_NV_FLAG_NONE;
	nv[1].name = (uint8_t *)"server";
	nv[1].namelen = 6;
	nv[1].value = (uint8_t *)"remotix";
	nv[1].valuelen = 7;
	nv[1].flags = NGHTTP3_NV_FLAG_NONE;

	memset(&dr, 0, sizeof dr);
	dr.read_data = cb_niente_dati;

	rv = nghttp3_conn_submit_response(w->h3, r->id, nv, 2, &dr);
	if (rv != 0) {
		registro_dice(REG_WT, "⛔ nghttp3_conn_submit_response: %s",
		              nghttp3_strerror(rv));
		return rv;
	}

	w->sessione = r->id;

	/* ⛔⭐ E QUI PARTE IL TETTO DI §4.6 PER L'APERTURA DEL CANALE — 5 s.
	 *
	 * ✅ `DECISIONI.md` §7.17, dall'utente l'11 agosto 2026.  Chi apre la
	 *    sessione e non apre mai il canale di controllo non aveva addosso
	 *    NESSUN tetto: `[M]` B6, 20 014 ms senza che succedesse niente.
	 *
	 * ⛔ E si arma anche cio' che lo fara' scadere, nello stesso istante — e'
	 *    la lezione piu' cara dell'innesto, scritta trenta righe piu' sotto in
	 *    `rcp_avvia`: un tetto senza battito e' un tetto che non scade. */
	w->canale_entro = ngtcp2_conn_get_timestamp(w->conn)
	                  + WT_TETTO_CANALE_NS;
	batti_fra(w, 100);

	registro_dice(REG_WT, "⭐ sessione WebTransport APERTA su %s (stream %ld) — "
	              "il canale di controllo va aperto entro %llu ms (§4.6, "
	              "DECISIONI.md §7.17)",
	              r->uri, (long)r->id,
	              (unsigned long long)(WT_TETTO_CANALE_NS / NGTCP2_MILLISECONDS));
	return 0;
}

static int cb_end_headers(nghttp3_conn *conn, int64_t stream_id, int fin,
                          void *cud, void *sud)
{
	wt *w = cud;
	richiesta *r = richiesta_trova(w, stream_id, false);
	(void)conn;
	(void)fin;
	(void)sud;
	if (!r)
		return 0;
	/* ⭐ E' qui che nasce la sessione WebTransport. */
	if (strcmp(r->metodo, "CONNECT") == 0 &&
	    strcmp(r->protocollo, "webtransport") == 0)
		return apri_sessione(w, r) == 0 ? 0 : NGHTTP3_ERR_CALLBACK_FAILURE;

	/* ⚠ Tutto il resto NON e' servito da questo ascoltatore: la pagina la
	 *   serve il TCP (`RCP.md` §2.4).  Un 404 e' la risposta esatta, e si
	 *   dichiara invece di lasciare la richiesta appesa. */
	registro_dice(REG_WT,
	              "richiesta HTTP/3 %s %s sullo stream %ld: 404 (su UDP si "
	              "serve solo la sessione WebTransport)",
	              r->metodo, r->uri, (long)stream_id);
	return risposta_secca(w, stream_id, "404") == 0
	         ? 0
	         : NGHTTP3_ERR_CALLBACK_FAILURE;
}

static int cb_stop_sending(nghttp3_conn *conn, int64_t stream_id,
                           uint64_t app_error_code, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_shutdown_stream_read(w->conn, 0, stream_id, app_error_code);
	return 0;
}

static int cb_reset_stream(nghttp3_conn *conn, int64_t stream_id,
                           uint64_t app_error_code, void *cud, void *sud)
{
	wt *w = cud;
	(void)conn;
	(void)sud;
	ngtcp2_conn_shutdown_stream_write(w->conn, 0, stream_id, app_error_code);
	return 0;
}

static int cb_end_stream(nghttp3_conn *conn, int64_t stream_id, void *cud,
                         void *sud)
{
	(void)conn;
	(void)stream_id;
	(void)cud;
	(void)sud;
	return 0;
}

static void cb_rand(uint8_t *dest, size_t destlen)
{
	for (size_t i = 0; i < destlen; i++)
		dest[i] = (uint8_t)(rand() & 0xff);
}

/* ------------------------------------------------------------------------ */

static int apri_http3(wt *w)
{
	static const nghttp3_callbacks callbacks = {
		.acked_stream_data = cb_acked,
		.recv_data = cb_recv_data,
		.deferred_consume = cb_deferred_consume,
		.begin_headers = cb_begin_headers,
		.recv_header = cb_recv_header,
		.end_headers = cb_end_headers,
		.stop_sending = cb_stop_sending,
		.end_stream = cb_end_stream,
		.reset_stream = cb_reset_stream,
		.rand = cb_rand,
	};
	nghttp3_settings settings;
	const ngtcp2_transport_params *params;
	int64_t ctrl, enc, dec;
	int rv;

	if (w->h3)
		return 0;
	if (ngtcp2_conn_get_streams_uni_left2(w->conn) < 3) {
		registro_dice(REG_WT,
		              "⛔ il client non concede nemmeno 3 stream "
		              "unidirezionali: HTTP/3 non si apre");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	nghttp3_settings_default(&settings);
	settings.qpack_max_dtable_capacity = 4096;
	settings.qpack_blocked_streams = 100;
	/* ⭐ Le due che nghttp3 sa fare da se', e sono negli RFC. */
	settings.enable_connect_protocol = 1; /* RFC 9220, l'extended CONNECT */
	settings.h3_datagram = 1;             /* RFC 9297 (RCP.md §2.2) */

	rv = nghttp3_conn_server_new(&w->h3, &callbacks, &settings,
	                             nghttp3_mem_default(), w);
	if (rv != 0) {
		registro_dice(REG_WT, "⛔ nghttp3_conn_server_new: %s",
		              nghttp3_strerror(rv));
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	params = ngtcp2_conn_get_local_transport_params2(w->conn);
	nghttp3_conn_set_max_client_streams_bidi(w->h3,
	                                         params->initial_max_streams_bidi);

	if (ngtcp2_conn_open_uni_stream(w->conn, &ctrl, NULL) != 0 ||
	    ngtcp2_conn_open_uni_stream(w->conn, &enc, NULL) != 0 ||
	    ngtcp2_conn_open_uni_stream(w->conn, &dec, NULL) != 0) {
		registro_dice(REG_WT, "⛔ non apro i tre stream di servizio di HTTP/3");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}

	/* ⭐ Si tiene il numero: quando nghttp3 scrivera' il suo SETTINGS su
	 *    questo stream sara' l'unica occasione di aggiungerci le due
	 *    dichiarazioni di WebTransport. */
	w->ctrl_id = ctrl;

	if (nghttp3_conn_bind_control_stream(w->h3, ctrl) != 0 ||
	    nghttp3_conn_bind_qpack_streams(w->h3, enc, dec) != 0) {
		registro_dice(REG_WT, "⛔ non lego gli stream di servizio a nghttp3");
		return NGTCP2_ERR_CALLBACK_FAILURE;
	}
	registro_dettaglio(REG_WT, "HTTP/3 aperto: controllo=%ld qpack=%ld/%ld",
	                   (long)ctrl, (long)enc, (long)dec);
	return 0;
}

/* ------------------------------------------------------------------------ */

wt *wt_nuovo(ngtcp2_conn *conn, ngtcp2_ccerr *ultimo_errore,
             const char *provenienza, aiutante *aiuto)
{
	wt *w = calloc(1, sizeof *w);
	if (!w)
		return NULL;
	w->conn = conn;
	w->ultimo_errore = ultimo_errore;
	w->aiuto = aiuto;
	w->ctrl_id = -1;
	w->sessione = -1;
	w->rcp_stream = -1;
	w->chiusura = -1;
	w->video_stream_ultimo = -1;
	snprintf(w->provenienza, sizeof w->provenienza, "%s",
	         provenienza ? provenienza : "");
	/* ⛔ Nell'elenco delle vive PRIMA di restituire: un fotogramma puo'
	 *    arrivare dal palco fra due giri di `poll`, e una sessione che non e'
	 *    nell'elenco non lo riceve — senza che nessuno se ne accorga. */
	w->viva_dopo = vive_prima;
	vive_prima = w;
	return w;
}

void wt_libera(wt *w)
{
	if (!w)
		return;
	/* ⛔ Fuori dall'elenco delle vive PRIMA di liberare qualunque cosa: da qui
	 *    in poi `wt_video_diffondi()` non deve piu' trovarla. */
	if (vive_prima == w) {
		vive_prima = w->viva_dopo;
	} else {
		for (wt *p = vive_prima; p; p = p->viva_dopo)
			if (p->viva_dopo == w) {
				p->viva_dopo = w->viva_dopo;
				break;
			}
	}
	/* ⛔⭐ E SI SPEGNE IL PALCO SE NESSUNO GUARDA PIU'.
	 *
	 *     Il figlio cattura e codifica solo perche' qualcuno guarda: un palco
	 *     lasciato acceso su una sessione chiusa spenderebbe una GPU e una CPU
	 *     per nessuno, per sempre.  ⚠ E non e' l'invariante I1 al contrario —
	 *     I1 vieta di calare il ritmo **per prudenza mentre qualcuno guarda**;
	 *     qui non guarda piu' nessuno, e il palco (I4) resta in piedi: si ferma
	 *     solo il ciclo dei fotogrammi. */
	/* ⛔⭐ I CONTI DELL'AUDIO SI SCRIVONO, e prima non li leggeva NESSUNO —
	 *     rilievo 6 della revisione del 17 agosto 2026: `wt_audio_conti()` non
	 *     aveva un solo chiamante in tutto `src/`, quindi `audio_spediti`,
	 *     `audio_buttati` e `audio_rifiutati` non raggiungevano mai una riga.
	 *     ⚠ Su un server normale «l'audio buttato» e «l'audio mai arrivato»
	 *     avevano esattamente la stessa faccia — che e' il difetto che quei
	 *     contatori esistono per togliere.
	 * ⭐ Si scrive alla fine della sessione perche' e' l'istante in cui il
	 *    conto e' completo, e con dentro gli ZERO: `CODER.md` §3.10. */
	if (w->audio_acceso) {
		uint64_t sp, bu, ri;
		size_t coda;
		wt_audio_conti(w, &sp, &bu, &ri, &coda);
		registro_dice(REG_RCP,
		              "audio di %s, conto finale: %llu blocchi spediti, %llu "
		              "buttati (coda piena o troppo grandi), %llu rifiutati da "
		              "ngtcp2, %llu RIMANDATI dal pacer e poi partiti, %zu "
		              "ancora in coda — codec %u",
		              w->provenienza, (unsigned long long)sp,
		              (unsigned long long)bu, (unsigned long long)ri,
		              (unsigned long long)w->audio_rimandati, coda,
		              w->audio_codec);
	}
	/* ⛔⛔⭐ E I CONTI DEL VIDEO, CHE NON LI LEGGEVA NESSUNO — 22 agosto 2026,
	 *       trovato da B2, ed e' **lo stesso difetto del riquadro qui sopra sul
	 *       gemello**: `wt_video_conti()` era definita, dichiarata in
	 *       `webtransport.h`, e senza **un solo chiamante in tutto `src/`**.
	 *
	 *       ⚠ La cura dell'audio fu scritta il 17 agosto, cinque giorni prima,
	 *       per la funzione gemella e con queste stesse parole.  ⇒ E' §1.20: la
	 *       cura era stata applicata a **uno dei due gemelli**, e nessuno aveva
	 *       guardato l'altro.  La lezione non e' sui contatori, e' che una cura
	 *       si cerca **dovunque valga**, non dove e' stata trovata.
	 *
	 * ⛔⛔ E IL PREZZO DI QUEL SILENZIO ERA UN NUMERO CHE MENTIVA.  `[M]` B2:
	 *      **799 fotogrammi scartati** e **un solo annuncio** nel registro; chi
	 *      contava le righe leggeva **1** e lo chiamava «non spediti».  Il
	 *      valore era 1, il nome prometteva 799: forma **E2**, e invisibile
	 *      perche' **1 e' un numero che sembra sano**.
	 *
	 * ⇒ Qui escono TUTTI E CINQUE, e con dentro gli ZERO (`CODER.md` §3.10):
	 *   uno zero scritto e un conto mai scritto devono avere due facce diverse.
	 *
	 * ⚠ `saltati` somma **tre** cause — la tela che non combacia, il credito di
	 *   stream finito (§2.3) e il rifiuto di `rcp.c`.  ⏳ Spezzarlo in tre e'
	 *   possibile e NON e' stato fatto: sarebbe una seconda cura, e questa
	 *   riga esiste per farne uscire una.  Il nome pero' non mente: sono
	 *   davvero i fotogrammi che non sono partiti.
	 *
	 * ⛔ E non si tocca niente del comportamento del video: qui si aggiunge
	 *    un'uscita di diagnosi, non si sposta una politica.
	 *
	 * ───────────────────────────────────────────────────────────────────────
	 * ⭐ LA PROVA CHE I DUE NUMERI SONO DAVVERO DUE — `[M]` 22 agosto 2026
	 * ───────────────────────────────────────────────────────────────────────
	 *
	 * Stessa scena in tutt'e due i giri: sessione di `provar8` sulla 7802,
	 * `04-b30-scena` in movimento sul monitor catturato, 16 s, tre `ADATTA_TELA`
	 * (1264x800 → 1920x1080 → 1264x800).  ⛔ E il guasto e' INNESTATO apposta
	 * nel solo albero di costruzione — la tela dichiarata discorde per ogni
	 * fotogramma — perche' su un prodotto sano questa strada non si percorre:
	 * il compositore riconfigura in 44-67 ms e nessun fotogramma fa in tempo a
	 * portare la misura vecchia.
	 *
	 * | binario | consegnati | NON SPEDITI | spediti | ANNUNCI |
	 * |---|---|---|---|---|
	 * | sano                | 1016 | **0**    | 1016 | **0** |
	 * | guasto innestato    | 0    | **1017** | 0    | **4** |
	 *
	 * ⇒ **1017 contro 4: un fattore 254.**  Prima della chiamata qui sotto il
	 *   solo numero che un banco poteva leggere era quello degli annunci, e lo
	 *   chiamava «non spediti».
	 *
	 * ⚠ E l'atteso scritto prima diceva «ANNUNCI = 1», come nel giro di B2: ne
	 *   sono usciti **4**, ed e' giusto cosi' — il fondo si riarma a ogni
	 *   coppia (tela, misura) nuova, e questa scena la cambia tre volte.  ⇒ Il
	 *   numero degli annunci segue le MISURE DISTINTE, non i fotogrammi: che e'
	 *   esattamente la ragione per cui non poteva fare da conto. */
	if (w->video_acceso) {
		uint32_t diffusi = 0, saltati = 0, spediti = 0, abbandonati = 0;
		uint32_t ritmo_scesi = 0;
		wt_video_conti(w, &diffusi, &saltati, &spediti, &abbandonati,
		               &ritmo_scesi);
		registro_dice(REG_RCP,
		              "video di %s, conto finale: %u fotogrammi consegnati a "
		              "RCP, %u NON SPEDITI (tela che non combacia + credito "
		              "finito + rifiuto di rcp), %u spediti sul filo, %u "
		              "abbandonati a valle (§5.1) — ⚠ e %u ANNUNCI di tela "
		              "discorde, che e' un NUMERO DIVERSO dai non spediti: il "
		              "registro ne scrive uno per ogni misura nuova, non uno "
		              "per fotogramma (§E2, B2 22 ago 2026) — codec %u",
		              w->provenienza, diffusi, saltati, spediti, abbandonati,
		              w->video_annunci_tela, w->video_codec);
		/* ⛔⭐ FASE 9 — e il conto della SOGLIA sta a parte, per la ragione di
		 *     tutta questa fase: «zero abbandoni» e «la cura e' spenta» non
		 *     devono avere la stessa faccia.  ⚠ E i tre numeri contano tre
		 *     fatti diversi: i delta TENUTI dicono che la cura ha lavorato,
		 *     quelli abbandonati per soglia che non e' bastata, e quelli senza
		 *     credito che il debito di §5.2 lo teneva acceso un'ALTRA causa —
		 *     la 4, invisibile al ricevente.  Senza il terzo, una cura che gira
		 *     a vuoto somiglia in tutto a una cura che non serve. */
		registro_dice(REG_RCP,
		              "⭐ FASE 9, la soglia della coda video: %s (%llu ms) — "
		              "delta TENUTI %u, abbandonati per soglia %u, e NON "
		              "ACCETTATI per credito mancato %u (§2.3, causa 4: la "
		              "forma che il ricevente non vede)",
		              sgombra_soglia_ms ? "ACCESA (predefinito dal 24 ago 2026)"
		                                : "SPENTA a mano (--sgombra-soglia-ms 0)",
		              (unsigned long long)sgombra_soglia_ms,
		              w->sgombra_tenuti, w->sgombra_abbandoni,
		              w->sgombra_credito);
		/* ⛔⭐ FASE 9 — E IL CONTO DEL REGOLATORE DEL RITMO, che sta a parte
		 *     dagli altri due per la ragione di tutta questa fase: «zero
		 *     discese» e «il regolatore e' spento» non devono avere la stessa
		 *     faccia.  ⚠ E il fondo della scala si DICHIARA qui invece di essere
		 *     dedotto: `DECISIONI.md` §2.1 dice 480p·25, e sotto i 25/s su una
		 *     linea da 20 Mbit/s e' un DIFETTO — non una degradazione riuscita.
		 *     ⛔ Il regolatore non ha nessun pavimento da far rispettare, perche'
		 *     forzare un fotogramma dentro una coda che non si svuota peggiora
		 *     la coda: qui si scrivono i due numeri accanto e chi legge
		 *     giudica. */
		registro_dice(REG_RCP,
		              "⭐ FASE 9, il regolatore del ritmo: %s — %u fotogrammi NON "
		              "PARTITI perche' l'arretrato aveva raggiunto i %u posti, su "
		              "%u consegnati a RCP.  ⚠ E' un numero SUO: non e' fra i «non "
		              "spediti» qui sopra.  ⛔ Fondo della scala dichiarato: 480p "
		              "25/s su 20 Mbit/s (DECISIONI.md §2.1) — sotto quello e' un "
		              "DIFETTO da guardare, non una degradazione riuscita",
		              ritmo_adattivo ? "ACCESO (predefinito dal 24 ago 2026)"
		                             : "SPENTO a mano (--niente-ritmo-adattivo)",
		              ritmo_scesi, (unsigned)WT_RITMO_POSTI, diffusi);
	}
	/* ⛔⛔⭐ FASE 9 — IL PREZZO DELLA CURA DELL'USO-DOPO-LA-LIBERAZIONE, E IL
	 *      CONTROLLO CHE LA FA CADERE.
	 *
	 *      Si scrive SEMPRE, anche senza video: i byte tenuti per la
	 *      ritrasmissione sono di tutti gli stream, non solo dei fotogrammi.
	 *
	 * ⭐ COME SI LEGGE, e sono due numeri con due mestieri diversi:
	 *
	 *    · la PUNTA e' il prezzo in memoria.  Deve stare nell'ordine della
	 *      finestra di congestione — decine o centinaia di KB, al peggio un
	 *      fotogramma intero (525 KB misurati il 23 agosto) — e con sedici
	 *      sessioni si moltiplica per sedici.  ⛔ Se cresce per tutta la
	 *      sessione invece di oscillare, la cura sta TRATTENENDO memoria: e'
	 *      esattamente il guasto che la farebbe cadere.
	 *
	 *    · il RESIDUO alla chiusura deve essere **zero o quasi**.  Se non lo
	 *      e', c'e' uno stream che si e' chiuso senza passare da
	 *      `wt_stream_chiuso()`, cioe' il fondo della cura non ha tenuto e
	 *      abbiamo barattato un uso dopo la liberazione con una perdita di
	 *      memoria.  ⚠ Un residuo non nullo qui NON e' una perdita vera — la
	 *      memoria la riprende `wt_libera()` venti righe piu' sotto — ma e' il
	 *      segnale che il fondo non ha lavorato, e va guardato.
	 *
	 * ⭐⭐ E COME SI RIPRODUCE IL DIFETTO CURATO, perche' il banco lo possa fare
	 *     (`fasi/09-la-qualita-e-la-degradazione.md` §4.5-4.6), su un binario SENZA questa cura:
	 *
	 *       1. `Environment=MALLOC_MMAP_THRESHOLD_=32768` nell'unita'.  ⭐
	 *          Impostarla dall'ambiente SPEGNE l'adattamento dinamico di glibc
	 *          (`no_dyn_threshold`): da quel momento ogni blocco sopra i 32 KiB
	 *          e' `mmap`/`munmap` e il difetto smette di essere silenzioso PER
	 *          SEMPRE, non solo la prima volta.  ⛔ Senza questa riga il difetto
	 *          si nasconde da solo: dopo il primo blocco grosso liberato la
	 *          soglia si alza e la corruzione torna muta.
	 *       2. un fotogramma grosso (film con la grana, a schermo intero), e
	 *          perdita di pacchetti: `tc qdisc add dev X root netem loss 5%`,
	 *          oppure `kill -STOP` al browser per un secondo (nessun ack ⇒ PTO
	 *          ⇒ ritrasmissione).
	 *       3. previsione sul binario malato: `SEGV`, `error 4`, `ip` dentro
	 *          `libc`, in `__memmove_avx_unaligned_erms`.  Con
	 *          `-fsanitize=address -g -fno-omit-frame-pointer` esce
	 *          `heap-use-after-free READ` con DUE pile: quella che legge (dentro
	 *          `ngtcp2_pkt_encode_stream_frame`) e quella che ha liberato.
	 *       4. con questa cura, lo stesso banco deve reggere e questa riga deve
	 *          dire residuo zero.  ⛔ Se muore lo stesso, la cura e' sbagliata. */
	registro_dice(REG_WT,
	              "⭐ FASE 9, i byte TENUTI per la ritrasmissione (contratto di "
	              "ngtcp2_conn_writev_stream): punta %zu byte, residuo alla "
	              "chiusura %zu, e %zu byte ancora da spedire in coda",
	              w->byte_in_volo_max, w->byte_in_volo, w->byte_in_coda);
	/* ⛔⛔ E SI SPEGNE LA CATTURA DELL'AUDIO SE NESSUNO ASCOLTA PIU'.
	 *
	 *     `[M]` 17 agosto 2026, prima accensione dell'audio vero: la sessione si
	 *     era chiusa alle 07:49:58 — «conto finale: 397 blocchi» — e il figlio
	 *     alle **07:50:10 stava ancora catturando e codificando**, 50 blocchi al
	 *     secondo, per nessuno.  ⚠ Non lo diceva nessun errore: lo diceva la
	 *     riga di riassunto del figlio, che esiste apposta.
	 *
	 * ⛔ E' la stessa forma dello spegnimento del palco qui sotto, per la stessa
	 *    ragione: cattura e codifica esistono solo perche' qualcuno guarda o
	 *    ascolta.  ⚠ E come li', il SINK resta in piedi (I4): a spegnersi e' il
	 *    consumo del monitor, non il dispositivo su cui le applicazioni suonano.
	 *
	 * ⭐ Sta DOPO l'uscita dall'elenco delle vive, in cima a questa funzione, o
	 *    `wt_audio_qualcuno_ascolta()` troverebbe se stessa e non spegnerebbe
	 *    mai — che e' il difetto che il palco ha gia' evitato cosi'. */
	if (w->audio_acceso && w->rcp && gancio_audio) {
		const char *mio = rcp_utente(w->rcp);
		if (mio && mio[0] && !wt_audio_qualcuno_ascolta(mio, NULL)) {
			registro_dice(REG_RCP,
			              "l'ultima sessione di «%s» se ne va: la cattura "
			              "dell'audio si ferma (il sink resta, e' l'invariante "
			              "I4)",
			              mio);
			gancio_audio(gancio_audio_ctx, mio, 0);
		}
	}
	/* Il codificatore del tono di prova, se questa sessione ne aveva uno. */
	if (w->tono_cod) {
		/* ⭐ E i conti del CODIFICATORE, che rispondono a una domanda che i
		 *    contatori del filo non fanno: `RCP.md` §6.3 dice che l'`istante`
		 *    e' quello del primo campione del blocco, e `audio.h` dichiara che
		 *    Opus «puo' non produrre un pacchetto per ogni blocco offerto».
		 *    ⛔ Se le due cose fossero vere insieme, l'istante scritto sul filo
		 *    apparterrebbe a un blocco diverso da quello spedito.  Questi due
		 *    numeri lo dicono. */
		uint64_t entrati = 0, usciti = 0;
		audio_cod_conti(w->tono_cod, &entrati, &usciti);
		registro_dice(REG_RCP,
		              "codificatore audio di %s: %llu blocchi entrati, %llu "
		              "usciti%s",
		              w->provenienza, (unsigned long long)entrati,
		              (unsigned long long)usciti,
		              entrati == usciti
		                  ? " — ⭐ uno per uno: l'`istante` di §6.3 appartiene "
		                    "al blocco che parte"
		                  : " — ⛔ NON uno per uno: l'`istante` scritto sul filo "
		                    "puo' non essere quello del blocco spedito");
		audio_cod_chiudi(w->tono_cod);
		w->tono_cod = NULL;
	}
	if (w->video_acceso && w->rcp && gancio_palco) {
		const char *mio = rcp_utente(w->rcp);
		if (mio && mio[0] && !wt_video_qualcuno_guarda(mio, NULL)) {
			registro_dice(REG_RCP,
			              "l'ultima sessione di «%s» se ne va: il palco smette "
			              "di catturare (il figlio resta, e' l'invariante I4)",
			              mio);
			/* ⚠ «Smetti di catturare»: il codec e' 0, e la profondita' con
			 *   lui non vuol dire niente. */
			gancio_palco(gancio_palco_ctx, mio, 0, 0, 0, false);
		}
	}
	if (w->rcp)
		rcp_libera(w->rcp);
	if (w->h3)
		nghttp3_conn_del(w->h3);
	for (size_t i = 0; i < w->ngiudizi; i++)
		bytes_libera(&w->giudizi[i].pref);
	free(w->giudizi);
	for (size_t i = 0; i < w->ncoda; i++)
		bytes_libera(&w->coda[i].dati);
	free(w->coda);
	bytes_libera(&w->capsbuf);
	free(w->richieste);
	free(w);
}

int wt_app_pronta(wt *w) { return apri_http3(w); }

int wt_ricevi_stream(wt *w, uint32_t flags, int64_t stream_id,
                     const uint8_t *dati, size_t len)
{
	bytes riunito = {0};
	nghttp3_ssize nconsumed;
	bool fin = (flags & NGTCP2_STREAM_DATA_FLAG_FIN) != 0;
	int esito = 0;

	if (!w->h3)
		return 0;

	/* ⛔ Gli stream WebTransport non sono affari di nghttp3: leggerebbe 0x41
	 *    come un tipo di frame sconosciuto e poi il numero della sessione
	 *    come una LUNGHEZZA, sballando tutto il resto.
	 *    ⛔ E il FIN viaggia con loro: §4.2 lo rende la fine della sessione,
	 *       e per uno stream che gestiamo noi qui e' l'ULTIMO posto in cui si
	 *       puo' vedere — sotto si torna prima di `nghttp3_conn_read_stream2`,
	 *       quindi nemmeno nghttp3 lo incontra. */
	switch (smista(w, stream_id, dati, len, fin, &riunito)) {
	case E_MIO:
	case E_ATTENDI:
		bytes_libera(&riunito);
		return 0;
	case E_HTTP3:
		break;
	}

	if (riunito.n > 0) {
		dati = riunito.d;
		len = riunito.n;
	}

	nconsumed = nghttp3_conn_read_stream2(w->h3, stream_id, dati, len, fin,
	                                      ngtcp2_conn_get_timestamp(w->conn));
	if (nconsumed < 0) {
		registro_dice(REG_WT, "⛔ nghttp3_conn_read_stream2: %s",
		              nghttp3_strerror((int)nconsumed));
		ngtcp2_ccerr_set_application_error(
			w->ultimo_errore,
			nghttp3_err_infer_quic_app_error_code((int)nconsumed), NULL, 0);
		esito = NGTCP2_ERR_CALLBACK_FAILURE;
	} else {
		conta_credito(w, stream_id, (size_t)nconsumed);
	}
	bytes_libera(&riunito);
	return esito;
}

int wt_stream_chiuso(wt *w, int64_t stream_id, uint64_t codice, bool con_codice)
{
	richiesta *r;

	/* ⛔⛔⭐ FASE 9 — E QUI SI LIBERANO I BYTE TENUTI PER LA RITRASMISSIONE.
	 *
	 *      E' l'ALTRA META' del contratto di `ngtcp2_conn_writev_stream()`
	 *      («... or the stream is closed»), e `ngtcp2.h` la scrive per esteso
	 *      sotto `acked_stream_data_offset`: «After stream_close is called for a
	 *      particular stream, conn does not touch data for the closed stream
	 *      again, and application can free all unacknowledged stream data».
	 *
	 * ⛔⛔ ED E' IL FONDO CHE DECIDE SE LA CURA E' UN PROGRESSO O UN BARATTO.
	 *      Senza questa riga, gli ultimi byte di ogni stream chiuso di netto —
	 *      un `STOP_SENDING`, un reset del client, uno stream che finisce prima
	 *      che l'ack arrivi — non riceverebbero MAI il loro riscontro: la stessa
	 *      pagina di `ngtcp2.h` dice che «if a stream is closed prematurely, and
	 *      stream data is still in-flight, this callback function is not called
	 *      for those data».  ⇒ Resterebbero allocati fino alla morte della
	 *      connessione, e una perdita di memoria al posto di un uso dopo la
	 *      liberazione **non e' un progresso**.
	 *
	 * ⚠ Vale anche per i byte NON ancora spediti di quello stream, e va bene
	 *   cosi': lo stream e' chiuso, non usciranno mai piu'.  Prima li buttava
	 *   la passata dopo, sul ramo `NGTCP2_ERR_STREAM_SHUT_WR` di `wt_scrivi()`.
	 *
	 * ⛔ E sta PRIMA di tutto il resto, perche' venti righe piu' sotto
	 *    `w->sessione` diventa `-1`: dopo, l'identificatore da cercare in coda
	 *    non ci sarebbe piu' — ed e' proprio lo stream della CONNECT quello che
	 *    `coda_conferma()` lascia apposta a questa funzione. */
	coda_butta_stream(w, stream_id);

	/* ⛔⭐ `RCP.md` §4.2: il canale di controllo si chiude, e IL SUO
	 *     CHIUDERSI E' LA FINE DELLA SESSIONE.  Il posto nel registro (§8.2
	 *     motivo 0x0F) va liberato QUI — e anche quando a chiudersi e' lo
	 *     stream della CONNECT estesa, che PORTA la sessione WebTransport.
	 *
	 * ⚠ Nell'innesto il posto si liberava solo alla morte della CONNESSIONE.
	 *   Con un cliente di prova i due istanti coincidono, e B3 e' rimasto
	 *   verde per cinque giri.  ⛔ Un BROWSER no: chiude la sessione e tiene
	 *   viva la connessione, e da quel momento il posto resta occupato da una
	 *   sessione che non esiste piu' — SETTE `posto NEGATO` su nove
	 *   tentativi, `[M]` B11 con Chrome. */
	if (w->rcp && (stream_id == w->rcp_stream || stream_id == w->sessione)) {
		registro_dice(REG_RCP,
		              "chiuso lo stream %ld: la sessione e' finita, il posto "
		              "si libera",
		              (long)stream_id);
		rcp_libera(w->rcp);
		w->rcp = NULL;
		w->rcp_stream = -1;
		regola_battito(w);
	}
	if (stream_id == w->sessione)
		w->sessione = -1;

	r = richiesta_trova(w, stream_id, false);
	if (r)
		r->usato = false;

	if (!w->h3)
		return 0;
	if (con_codice) {
		int rv = nghttp3_conn_close_stream(w->h3, stream_id, codice);
		if (rv != 0 && rv != NGHTTP3_ERR_STREAM_NOT_FOUND) {
			registro_dice(REG_WT, "⛔ nghttp3_conn_close_stream: %s",
			              nghttp3_strerror(rv));
			ngtcp2_ccerr_set_application_error(
				w->ultimo_errore,
				nghttp3_err_infer_quic_app_error_code(rv), NULL, 0);
			return NGTCP2_ERR_CALLBACK_FAILURE;
		}
	}
	return 0;
}

int wt_stream_reset(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_shutdown_stream_read(w->h3, stream_id);
	return 0;
}

int wt_stream_stop_sending(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_shutdown_stream_read(w->h3, stream_id);
	return 0;
}

/* ⛔⛔⭐ FASE 9 — PRIMA I NOSTRI BYTE, POI nghttp3.
 *
 *      Questa funzione inoltrava a nghttp3 **e basta**, ed e' li' che si vede
 *      tutto il difetto del 23 agosto 2026 in due righe: il riscontro serviva a
 *      LORO — nghttp3 i suoi buffer li tiene fino all'ack, come il contratto di
 *      `ngtcp2_conn_writev_stream()` pretende — e a NOI no, perche' i nostri li
 *      liberavamo alla serializzazione.  Due politiche opposte per lo stesso
 *      contratto, nello stesso modulo, sulla stessa chiamata.
 *
 * ⚠ E `!w->h3` non torna piu' subito: i NOSTRI elementi vanno confermati anche
 *   quando lo strato HTTP/3 non c'e' (o non c'e' piu'), o gli ultimi byte di
 *   una sessione in chiusura non verrebbero liberati da nessuno. */
int wt_ack_stream_data(wt *w, int64_t stream_id, uint64_t len)
{
	coda_conferma(w, stream_id, len);
	if (!w->h3)
		return 0;
	nghttp3_conn_add_ack_offset(w->h3, stream_id, len);
	return 0;
}

int wt_estendi_max_stream_data(wt *w, int64_t stream_id)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_unblock_stream(w->h3, stream_id);
	return 0;
}

int wt_estendi_max_streams_bidi(wt *w, uint64_t max_streams)
{
	if (!w->h3)
		return 0;
	nghttp3_conn_set_max_client_streams_bidi(w->h3, max_streams);
	return 0;
}

/* ------------------------------------------------------------------------ */

/* ⛔⭐ §8.1 — «MAI CON UN SILENZIO».  Rilievo B-7, 10 agosto 2026 notte.
 *
 *     La chiama `trasporto_congeda_tutte()` quando il server si spegne.  Le due
 *     strade di §3.1 le percorre `rcp_congeda()`: `CONGEDO(0x0C)` sul canale di
 *     controllo, e lo stesso `0x0C` nel codice della chiusura della sessione.
 *
 * ⚠ E se la sessione RCP non c'e' ancora — una connessione QUIC aperta ma senza
 *   canale di controllo — resta la seconda strada, che e' proprio il caso per
 *   cui §3.1 ne ha volute due. */
void wt_congeda(wt *w, uint8_t motivo, const char *dettaglio)
{
	if (!w)
		return;
	if (w->rcp && !rcp_e_finita(w->rcp)) {
		rcp_congeda(w->rcp, motivo, dettaglio);
		return;
	}
	if (w->sessione != -1 && w->chiusura < 0) {
		registro_dice(REG_RCP,
		              "⚠ %s: nessuna sessione RCP viva, il motivo %#04x "
		              "viaggia solo nel codice di chiusura della sessione "
		              "(§3.1, seconda strada)",
		              w->provenienza, motivo);
		chiudi_sessione(w, motivo);
	}
}

/* ⭐ IL VERDETTO DI PAM CHE RIENTRA — `DECISIONI.md` §1.10.
 *
 * ⛔ Il trasporto lo passa a tutte le connessioni vive e una sola lo prende:
 *    la pratica e' un numero del PROCESSO, e chi la riconosce e' `rcp.c`.  ⚠ E
 *    se non la prende nessuno va bene cosi' — vuol dire che la connessione e'
 *    morta mentre PAM rispondeva, e non c'e' piu' nessuno da ammettere. */
bool wt_verdetto(wt *w, uint64_t pratica, bool ammesso)
{
	if (!w || !w->rcp)
		return false;
	return rcp_verdetto(w->rcp, pratica, ammesso,
	                    ngtcp2_conn_get_timestamp(w->conn) / NGTCP2_MILLISECONDS);
}

/* ⛔⭐ §5.3 — il segno di vita che viene dal filo.  Una riga di ponte, e la
 *     ragione per cui esiste sta su `rcp_segno_di_vita()`.
 *
 * ⚠ Passa PRIMA che la sessione RCP esista (la connessione QUIC c'e', il canale
 *   di controllo no): allora non c'e' niente da segnare e va bene cosi' — chi
 *   non e' ancora attaccato non tiene nessun posto. */
void wt_segno_di_vita(wt *w, ngtcp2_tstamp ts)
{
	if (w && w->rcp)
		rcp_segno_di_vita(w->rcp, ts / NGTCP2_MILLISECONDS);
}

void wt_batti(wt *w, ngtcp2_tstamp ts)
{
	if (w->rcp)
		rcp_tempo(w->rcp, ts / NGTCP2_MILLISECONDS);

	/* ⭐ La seconda delle due strade: `SESSIONE` puo' partire anche da
	 *    `rcp_tempo()` — il ritardo fisso di §4.4-bis la fa maturare qui, non
	 *    all'arrivo delle credenziali.  ⛔ Con la sola chiamata in `rcp_passa`
	 *    il fotogramma sarebbe partito solo per le sessioni che dicono ancora
	 *    qualcosa dopo, e su un client che tace dopo le credenziali non sarebbe
	 *    partito mai. */
	video_regola(w, ts / NGTCP2_MILLISECONDS);
	audio_regola(w);
	tono_passo(w, ts);

	/* ⛔⭐ FASE 9 — la riga al secondo del regolatore, e gira col BATTITO
	 *     apposta: a scena ferma i fotogrammi non arrivano, e una riga che
	 *     uscisse solo coi fotogrammi lascerebbe «l'anello non e' stato
	 *     percorso» con la stessa faccia di «l'arretrato era zero». */
	ritmo_ciclo(w, ts / NGTCP2_MILLISECONDS);

	/* ⛔⭐ FASE 9 — e accanto a quella del ritmo, quella della RETE: le due
	 *     meta' della stessa domanda.  `ritmo_ciclo()` dice quel che abbiamo
	 *     fatto NOI, `rete_ciclo()` quel che ha fatto la LINEA — e girano tutte
	 *     e due col battito, per la stessa ragione: a scena ferma i fotogrammi
	 *     non arrivano, ma i pacchetti si possono perdere lo stesso. */
	rete_ciclo(w, ts / NGTCP2_MILLISECONDS);

	/* ⛔⭐ §4.6 — LA SESSIONE CHE NON APRE MAI IL CANALE DI CONTROLLO.
	 *
	 * ✅ `DECISIONI.md` §7.17, 11 agosto 2026: 5 s, poi `TEMPO_SCADUTO`.
	 *
	 * ⚠ E il `CONGEDO` NON si manda: il canale di controllo non e' mai nato,
	 *   quindi non c'e' dove spedirlo.  E' la condizione decisa lo stesso
	 *   giorno in §7.15 — «se il canale e' ancora utilizzabile» — e qui non lo
	 *   e'.  Il motivo viaggia SOLO nel codice di chiusura della sessione, che
	 *   e' la seconda strada di §3.1 punto 3.
	 *
	 * ⭐ Le due decisioni si incastrano proprio qui, ed e' il primo posto in
	 *    cui succede: senza §7.15 questa riga dovrebbe spedire un byte su un
	 *    canale mai nato. */
	if (w->canale_entro && ts >= w->canale_entro && w->chiusura < 0) {
		registro_dice(REG_RCP,
		              "⛔ %s: sessione WebTransport aperta e canale di "
		              "controllo MAI aperto entro %llu ms — congedo "
		              "%#04x TEMPO_SCADUTO (§4.6, DECISIONI.md §7.17).  "
		              "⚠ nessun CONGEDO sul canale: il canale non esiste, "
		              "il motivo viaggia nel codice di chiusura (§3.1 punto "
		              "3, e §7.15 lo consente)",
		              w->provenienza,
		              (unsigned long long)(WT_TETTO_CANALE_NS
		                                   / NGTCP2_MILLISECONDS),
		              RCP_TEMPO_SCADUTO);
		w->canale_entro = 0;
		chiudi_sessione(w, RCP_TEMPO_SCADUTO);
	}

	/* ⛔ La capsula di chiusura parte SOLO quando la coda d'uscita e' vuota:
	 *    il `CONGEDO` deve essere gia' partito, o il browser lo butta insieme
	 *    alla sessione.  ⚠ E non basta che sia vuota: «consegnato a ngtcp2»
	 *    non e' «uscito sul filo», quindi si aspetta ancora mezzo secondo. */
	if (w->chiusura >= 0) {
		/* ⛔ La scadenza si guarda PRIMA della coda — rilievo B-3.  Se si
		 *    guardasse dopo, il ramo «coda non vuota» riazzererebbe
		 *    `chiusura_da` per sempre e non si arriverebbe mai qui: e'
		 *    esattamente il difetto che questa riga toglie. */
		if (w->chiusura_scadenza && ts >= w->chiusura_scadenza) {
			uint8_t m = (uint8_t)w->chiusura;
			registro_dice(REG_WT,
			              "⛔ la coda d'uscita non si e' svuotata in 3 s "
			              "(%zu elementi da spedire, %zu byte; e %zu byte "
			              "consegnati a ngtcp2 in attesa di riscontro): la "
			              "capsula di chiusura parte LO STESSO col codice "
			              "0x%02x — §3.1 punto 3 e' il motivo che salva le "
			              "diagnosi, e aspettare per sempre vuol dire non "
			              "eseguirlo mai",
			              coda_da_spedire(w), w->byte_in_coda,
			              w->byte_in_volo, m);
			w->chiusura = -1;
			w->chiusura_da = 0;
			w->chiusura_scadenza = 0;
			chiudi_adesso(w, m);
		} else if (!coda_vuota(w)) {
			w->chiusura_da = 0;
		} else if (w->chiusura_da == 0) {
			w->chiusura_da = ts + WT_ATTESA_CHIUSURA_NS;
		} else if (ts >= w->chiusura_da) {
			uint8_t m = (uint8_t)w->chiusura;
			w->chiusura = -1;
			w->chiusura_da = 0;
			w->chiusura_scadenza = 0;
			chiudi_adesso(w, m);
		}
	}

	regola_battito(w);
	if (w->battito_ms && w->battito <= ts) {
		/* Il tempo non e' avanzato quanto serve: si rimanda comunque in
		 * avanti, o il ciclo girerebbe a vuoto. */
		w->battito = ts + w->battito_ms * NGTCP2_MILLISECONDS;
	}
}

/* ------------------------------------------------------------------------ */
/* ⭐ La scrittura: e' qui che le due cose che nghttp3 non sa fare si fanno.   */

ngtcp2_ssize wt_scrivi(wt *w, ngtcp2_path *path, ngtcp2_pkt_info *pi,
                       uint8_t *dest, size_t destlen, ngtcp2_tstamp ts)
{
	nghttp3_vec vec[16];

	/* ⭐ Una passata di scrittura comincia qui, e gli stream ripartono tutti
	 *    SBLOCCATI: l'elenco vale per una passata sola.  ⚠ Sta fuori dal ciclo
	 *    apposta — azzerarlo dentro rimetterebbe in gioco lo stesso elemento a
	 *    ogni giro, che e' precisamente il ciclo che non avanza. */
	w->nbloccati = 0;
	w->troppi_bloccati = false;

	/* ⭐ I DATAGRAM PRIMA DEGLI STREAM, e la ragione e' il ritardo.
	 *
	 * ⛔ Un blocco d'audio che aspetta la coda del video arriva in ritardo di
	 *    un fotogramma, e in ritardo non serve (§6.3).  ⚠ E non affama gli
	 *    stream: la coda dei datagram e' lunga otto, quindi al massimo otto
	 *    pacchetti passano davanti — poi `w->ndgram` e' zero e si prosegue. */
	{
		ngtcp2_ssize ndg = 0;
		if (dgram_scrivi_uno(w, path, pi, dest, destlen, ts, &ndg))
			return ndg;
	}

	for (;;) {
		int64_t stream_id = -1;
		int fin = 0;
		nghttp3_ssize sveccnt = 0;
		nghttp3_vec wtvec[1];
		size_t wt_orig = 0;
		bool wt_mio = false;
		size_t mio_i = 0;
		ngtcp2_ssize ndatalen = -1, nwrite;
		const nghttp3_vec *v;
		size_t vcnt;
		uint32_t flags;

		/* ⭐ Se la riscrittura delle impostazioni ha perso il conto, ci si
		 *    ferma: uno stream di controllo sfasato e' peggio di una
		 *    connessione chiusa.  ⚠ NON e' il caso della scrittura
		 *    PARZIALE, che e' un esito normale e si riprende dopo. */
		if (w->guasto)
			return NGTCP2_ERR_CALLBACK_FAILURE;

		if (w->h3 && ngtcp2_conn_get_max_data_left2(w->conn)) {
			sveccnt = nghttp3_conn_writev_stream(w->h3, &stream_id, &fin,
			                                     vec, 16);
			if (sveccnt < 0) {
				registro_dice(REG_WT, "⛔ nghttp3_conn_writev_stream: %s",
				              nghttp3_strerror((int)sveccnt));
				ngtcp2_ccerr_set_application_error(
					w->ultimo_errore,
					nghttp3_err_infer_quic_app_error_code((int)sveccnt),
					NULL, 0);
				return NGTCP2_ERR_CALLBACK_FAILURE;
			}
		}

		/* ── 1. le impostazioni ─────────────────────────────────────── */
		if (sveccnt > 0 && stream_id == w->ctrl_id && !w->impostazioni_scritte) {
			/* ⛔ La riscrittura si fa UNA VOLTA SOLA.  Se la passata di
			 *    prima ne ha spedito solo un pezzo, nghttp3 ci rioffre
			 *    gli stessi byte — non gli abbiamo ancora detto di
			 *    averli consumati — e ricomporre il buffer da capo
			 *    rispedirebbe il pezzo gia' uscito. */
			if (w->impbuf_off == 0)
				w->impbuf_orig =
					riscrivi_impostazioni(w, vec, (size_t)sveccnt);
			wt_orig = w->impbuf_orig;
		}

		/* ── 2. la coda nostra ──────────────────────────────────────── */
		/* ⛔ `coda_scegli()` e non «la testa»: la testa puo' appartenere a uno
		 *    stream bloccato, e fermarsi li' rifarebbe il blocco di testa che
		 *    §5.1 esiste per togliere. */
		if (sveccnt <= 0 && !w->troppi_bloccati) {
			uscita *u = coda_scegli(w, &mio_i);
			if (u) {
				stream_id = u->id;
				fin = u->fin ? 1 : 0;
				wtvec[0].base = u->dati.d + u->off;
				wtvec[0].len = u->dati.n - u->off;
				wt_mio = true;
			}
		}

		v = vec;
		vcnt = (size_t)(sveccnt > 0 ? sveccnt : 0);

		if (wt_orig) {
			/* ⭐ FASE 9 — e neanche qui c'e' il difetto del 23 agosto:
			 *    `impbuf` e' un array FISSO dentro `wt` (256 byte), scritto
			 *    UNA VOLTA SOLA (`impostazioni_scritte`) e vivo quanto la
			 *    connessione.  ⛔ Se un giorno le impostazioni si
			 *    riscrivessero, riscriverlo mentre ngtcp2 tiene ancora questo
			 *    puntatore sarebbe la stessa corruzione silenziosa. */
			wtvec[0].base = w->impbuf + w->impbuf_off;
			wtvec[0].len = w->impbuf_len - w->impbuf_off;
			v = wtvec;
			vcnt = 1;
		} else if (wt_mio) {
			v = wtvec;
			vcnt = 1;
		}

		flags = NGTCP2_WRITE_STREAM_FLAG_MORE |
		        NGTCP2_WRITE_STREAM_FLAG_PADDING;
		if (fin)
			flags |= NGTCP2_WRITE_STREAM_FLAG_FIN;

		nwrite = ngtcp2_conn_writev_stream(w->conn, path, pi, dest, destlen,
		                                   &ndatalen, flags, stream_id,
		                                   (const ngtcp2_vec *)v, vcnt, ts);
		if (nwrite < 0) {
			switch (nwrite) {
			case NGTCP2_ERR_STREAM_DATA_BLOCKED:
				/* ⛔⭐ E I BYTE NON SI BUTTANO: QUESTO E' UN CANALE
				 *     AFFIDABILE.  Nell'innesto qui si scartava
				 *     l'elemento INTERO — compreso il caso in cui una
				 *     parte era gia' uscita sul filo: il messaggio dopo
				 *     si saldava a quei byte monchi e il client leggeva
				 *     un `tipo`/`lunghezza` inventato.  ⛔ Era il
				 *     SERVER a fabbricare la violazione del client.
				 *
				 * ⚠ E STREAM_DATA_BLOCKED non e' un guasto: e' la
				 *   condizione normale e transitoria che si scioglie col
				 *   primo MAX_STREAM_DATA. */
				if (wt_mio) {
					uscita *u = &w->coda[mio_i];
					registro_dettaglio(
						REG_WT,
						"stream %ld bloccato: %zu byte RESTANO in "
						"coda (%zu gia' usciti) — ⭐ gli ALTRI stream "
						"continuano (§5.1)",
						(long)stream_id, u->dati.n - u->off, u->off);
					/* ⛔⭐ SI BLOCCA LO STREAM, NON LA CODA — ed e' la
					 *     cura del punto 5 della fase 3.  Fino alla fase 2
					 *     qui si alzava `coda_bloccata`, che fermava
					 *     TUTTA la coda per la passata: un fotogramma
					 *     lento bloccava in testa i successivi **a
					 *     livello applicativo**, annullando esattamente il
					 *     beneficio che §5.1 compra al livello di QUIC. */
					if (w->nbloccati < WT_BLOCCATI_MAX) {
						w->bloccati[w->nbloccati++] = stream_id;
					} else {
						/* ⚠ Il tetto si dichiara invece di scivolare:
						 *   da qui in poi la passata si ferma davvero, e
						 *   chi legge sa che non e' §5.1 a non
						 *   funzionare, e' questa tabella a essere
						 *   piena. */
						w->troppi_bloccati = true;
						registro_dice(REG_WT,
						              "⚠ %u stream bloccati nella stessa "
						              "passata: la coda si ferma qui.  Non "
						              "e' §5.1 che non vale, e' il tetto "
						              "di WT_BLOCCATI_MAX",
						              WT_BLOCCATI_MAX);
					}
					continue;
				}
				nghttp3_conn_block_stream(w->h3, stream_id);
				continue;
			case NGTCP2_ERR_STREAM_SHUT_WR:
				if (wt_mio) {
					/* Lo stream e' gia' chiuso in scrittura — di norma
					 * perche' lo abbiamo AZZERATO noi (§5.1): i byte che
					 * restavano non partono, che e' quel che si voleva. */
					coda_uccidi(w, mio_i);
					continue;
				}
				nghttp3_conn_shutdown_stream_write(w->h3, stream_id);
				continue;
			case NGTCP2_ERR_WRITE_MORE:
				break;
			default:
				registro_dice(REG_WT, "⛔ ngtcp2_conn_writev_stream: %s",
				              ngtcp2_strerror((int)nwrite));
				ngtcp2_ccerr_set_liberr(w->ultimo_errore, (int)nwrite,
				                        NULL, 0);
				return NGTCP2_ERR_CALLBACK_FAILURE;
			}
		}

		if (nwrite == NGTCP2_ERR_WRITE_MORE || ndatalen >= 0) {
			/* Quanti byte DI NGHTTP3 sono stati consumati.  Se il suo
			 * buffer e' stato sostituito, il numero che ngtcp2
			 * restituisce e' il NOSTRO, e dirglielo sfaserebbe i suoi
			 * conti. */
			if (wt_mio) {
				uscita *u = &w->coda[mio_i];
				u->off += (size_t)ndatalen;
				if (u->off >= u->dati.n) {
					/* ⛔⭐ `RCP.md` §4.2: il canale di controllo
					 *     che si chiude e' la fine della sessione,
					 *     ANCHE dal lato nostro.  Il posto va
					 *     lasciato QUI, perche' da adesso in poi non
					 *     arrivera' piu' un byte che lo liberi. */
					if (u->fin && w->rcp &&
					    (u->id == w->rcp_stream || u->id == w->sessione))
						rcp_canale_chiuso(w->rcp);
					/* ⛔⛔⭐ FASE 9 — QUI C'ERA `coda_uccidi()`, ED E' LA RIGA
					 *      CHE HA UCCISO IL SERVER IL 23 AGOSTO 2026 alle
					 *      08:28:09.
					 *
					 *      `ndatalen` dice quanti byte sono finiti **in un
					 *      pacchetto**, non quanti sono stati **confermati**.
					 *      Liberarli qui e' liberarli mentre ngtcp2 tiene
					 *      ancora il nostro puntatore per l'eventuale
					 *      ritrasmissione: `fasi/09-la-qualita-e-la-degradazione.md` §4.2 segue la
					 *      catena riga per riga fino al `ngtcp2_cpymem()` che
					 *      rilegge la sorgente liberata.
					 *
					 * ⭐ Adesso si CONSEGNA e basta: l'elemento esce dalla
					 *    scelta e dall'arretrato, i byte restano.  A liberarli
					 *    e' l'ack (`coda_conferma()`) o la chiusura dello
					 *    stream (`wt_stream_chiuso()`) — le due sole condizioni
					 *    che il contratto di ngtcp2 ammette. */
					coda_consegna(w, mio_i);
				}
			} else if (wt_orig) {
				uint64_t c = (uint64_t)ndatalen;
				/* ⛔⭐ E UNA SCRITTURA PARZIALE NON E' UN GUASTO.
				 *
				 *    `ndatalen` minore della lunghezza offerta e' un
				 *    esito NORMALE: nello stream frame ci va quel che
				 *    avanza nel pacchetto.  I ~24 byte del SETTINGS
				 *    riscritto viaggiano nel primo volo dopo la
				 *    stretta di mano, quello che porta anche
				 *    HANDSHAKE_DONE e i NEW_CONNECTION_ID: li' dentro
				 *    24 byte possono non starci.
				 *
				 * ⛔ Nell'innesto qui MORIVA LA CONNESSIONE, mentre
				 *    dieci righe piu' sopra la coda nostra la stessa
				 *    scrittura parziale la gestiva con `off`.  Due
				 *    politiche opposte per lo stesso esito, nello
				 *    stesso modulo. */
				if (c > w->impbuf_len - w->impbuf_off) {
					registro_dice(REG_WT,
					              "⛔ impostazioni, conto impossibile "
					              "(%llu presi su %zu offerti)",
					              (unsigned long long)c,
					              w->impbuf_len - w->impbuf_off);
					w->guasto = true;
					return NGTCP2_ERR_CALLBACK_FAILURE;
				}
				w->impbuf_off += (size_t)c;
				if (w->impbuf_off < w->impbuf_len) {
					registro_dettaglio(
						REG_WT,
						"impostazioni, %zu byte su %zu — il resto "
						"alla passata dopo",
						w->impbuf_off, w->impbuf_len);
				} else {
					w->impostazioni_scritte = true;
					if (nghttp3_conn_add_write_offset(
						    w->h3, stream_id, w->impbuf_orig) != 0) {
						w->guasto = true;
						return NGTCP2_ERR_CALLBACK_FAILURE;
					}
				}
			} else if (stream_id >= 0) {
				int rv = nghttp3_conn_add_write_offset(w->h3, stream_id,
				                                       (uint64_t)ndatalen);
				if (rv != 0) {
					registro_dice(REG_WT,
					              "⛔ nghttp3_conn_add_write_offset: %s",
					              nghttp3_strerror(rv));
					ngtcp2_ccerr_set_application_error(
						w->ultimo_errore,
						nghttp3_err_infer_quic_app_error_code(rv), NULL,
						0);
					return NGTCP2_ERR_CALLBACK_FAILURE;
				}
			}
		}

		if (nwrite == NGTCP2_ERR_WRITE_MORE)
			continue;

		return nwrite;
	}
}
