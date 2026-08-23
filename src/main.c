/*
 * main.c — REMOTIX_V2, il server.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COS'E' QUESTO PROGRAMMA, E CHE COSA NON E' ANCORA
 *
 * E' il server di `SPECIFICHE.md` §1 alla FASE 1: la stretta di mano di RCP su
 * WebTransport, dai due lati, e la pagina servita dal server stesso.  ⛔ Niente
 * video, niente audio, niente input: quelli sono le fasi da 2 in poi.
 *
 * ⚠ Quel che l'utente vede e giudica: apre `https://indirizzo:7447`, clicca
 *   l'avviso la prima volta su quel dispositivo, digita utente e parola, e la
 *   pagina dice «ammesso, sessione nuova, tela 1920×1080, desktop GNOME» —
 *   oppure dice PERCHE' no, con una frase e non con un numero (`RCP.md` §8.2).
 *
 * ---------------------------------------------------------------------------
 * ⛔ I DUE ASCOLTATORI, CON LO STESSO NUMERO DI PORTA
 *
 * `RCP.md` §2.4: **7447**, UDP per HTTP/3 e WebTransport, TCP per il primo
 * caricamento della pagina.  ⚠ E le due cose sono INDIPENDENTI: WebTransport
 * non usa `Alt-Svc`, apre la sua connessione da se' (misura S1).  ⛔ Il ripiego
 * silenzioso su TCP dichiarato come pericolo in `PIANO.md` fase 1 non puo'
 * accadere — quella riga e' anteriore alla misura.
 *
 * ---------------------------------------------------------------------------
 * ⛔ UN SOLO FILO, E ADESSO NON E' PIU' UN PROBLEMA — 12 agosto 2026
 *
 * Tutto gira in un ciclo `poll` solo, e resta cosi'.  ⛔ Quel che e' cambiato
 * e' che **il ciclo non chiama piu' PAM**: `DECISIONI.md` §1.10, dall'utente,
 * alla chiusura della fase 1.
 *
 * ⚠ Quel che questo riquadro diceva fino a ieri — «la verifica PAM BLOCCA quel
 *   filo, quindi la stretta di mano di un utente ritarda i pacchetti di
 *   chiunque altro» — era vero e MISURATO: `[M]` B8, sera dell'11 agosto, **da
 *   1,0 a 2,2 secondi per tentativo**, e a metterceli era PAM (+1034 ms oltre
 *   il secondo fisso sui respinti contro +84 ms sugli ammessi, la firma di
 *   `pam_faildelay`).
 *
 * ⭐ Adesso PAM la interroga un **processo aiutante** (`aiutante.c`), e la
 *    forma e' quella decisa dall'utente: un processo, non un filo, perche' PAM
 *    non e' affidabilmente rientrante.  Qui dentro restano tre righe: il
 *    descrittore dell'aiutante entra nel `poll` insieme agli altri, le risposte
 *    si consegnano, e le domande senza risposta scadono.
 *
 * ⛔ E la ragione per cui si e' curato PRIMA della fase 2, che non e' di
 *    eleganza: senza video il sintomo era «l'ultimo dei dieci aspetta dieci
 *    secondi»; con il video sarebbe stato **lo schermo di tutti quelli
 *    collegati che si pianta ogni volta che qualcun altro entra** — e chi lo
 *    vede da' la colpa al video, perche' e' li' che si vede.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ E DAL 12 AGOSTO 2026 QUESTO PROCESSO NON CATTURA PIU' NIENTE — §1.10-bis
 *
 * `DECISIONI.md` §1.10-bis: il server resta **privilegiato**, e per ogni utente
 * ammesso genera un **figlio che gira come lui**, che tiene il bus di sessione,
 * la cattura e i dispositivi.  ⛔ La ragione e' una misura, non una preferenza:
 * `[M]` root non si collega al bus di sessione dell'utente, e `[M]` solo root
 * puo' verificare con PAM la parola d'ordine di un altro.
 *
 * ⇒ Da qui sono uscite `sessione_assicura()` e `primo_fotogramma()`, che fino a
 *   ieri stavano proprio in questo file: adesso vivono in `figlio.c`, dall'altra
 *   parte del calo di privilegio.  ⭐ E non e' solo una questione di permessi:
 *   **questo processo non tocca piu' ne' GLib ne' PipeWire ne' D-Bus**, quindi
 *   il `fork()` che genera un figlio parte da un processo a un filo solo — che
 *   e' l'unica condizione in cui un `fork` da una libreria con thread non e'
 *   una scommessa.
 */
#include "aiutante.h"
#include "certificati.h"
#include "comando.h"
#include "figlio.h"
#include "sentinella.h"
#include "pagina.h"
#include "rcp.h"
#include "registro.h"
#include "tls.h"
#include "trasporto.h"
#include "webtransport.h"

#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>

#include <openssl/ssl.h>

#define PORTA_PREDEFINITA "7447" /* RCP.md §2.4 */

/* ⛔⭐ LA TELA, IN UN POSTO SOLO — e fino al 12 agosto 2026 erano tre.
 *
 *     `PIANO.md` fase 1 dichiara «tela 1920×1080»; `src/pagina.html` la chiede
 *     nel `CIAO` (riga 1503); `P2-1-sessione.md` §6.3 scriveva `1920, 1080` a
 *     mano dentro `main.c` e lo dichiarava un debito: *«chi innesta li leghi a
 *     una costante sola, o fra due settimane saranno tre posti»*.
 *
 * ⭐ Qui la costante e' una, e la usano tutte e tre le cose che devono
 *    combaciare: il monitor virtuale che si chiede alla sessione, la misura con
 *    cui si apre la cattura, e la misura con cui si codifica.  ⛔ Se non
 *    combaciassero il sintomo NON sarebbe un errore: sarebbe un'intestazione di
 *    §6.2 che dichiara una misura mentre i pixel ne portano un'altra, e il
 *    client non ha modo di accorgersene.
 *
 * ⚠ Quel che resta fuori, e va detto: la tela che il client CHIEDE nel `CIAO`.
 *   Quella e' sua, §4.5 permette al server di ridurla, e `video_forse()` in
 *   `webtransport.c` rifiuta di spedire se non combacia con questa — invece di
 *   spedire un fotogramma che mente. */
#define TELA_L 1920u
#define TELA_A 1080u

/* 1 per l'UDP, 1 per l'ascoltatore TCP, il resto per le connessioni TCP. */
#define MAX_POLL 64

/* ⭐ §5.1 — ogni quanto si ripassano le sessioni grafiche locali.
 *
 * ⚠ Due secondi, e i due numeri che li giustificano sono uno per verso: e' il
 *   RITARDO massimo fra «l'utente si e' seduto davanti alla macchina» e «la
 *   sessione remota cade» — che nessuno guarda col cronometro — ed e' anche il
 *   COSTO, perche' ogni ripasso e' una chiamata sincrona a logind dentro il
 *   ciclo che consegna i fotogrammi (`LEZIONI.md` §6.2-bis). */
#define RIPASSO_LOCALI_MS 2000

static volatile sig_atomic_t si_ferma;

static void al_segnale(int s)
{
	(void)s;
	si_ferma = 1;
}

static void aiuto(const char *nome)
{
	fprintf(stderr,
	        "REMOTIX_V2 — il server (fase 1: il filo nudo)\n"
	        "\n"
	        "  %s [opzioni]\n"
	        "\n"
	        "  --indirizzo IND   su che cosa ascoltare (predefinito: 0.0.0.0)\n"
	        "  --nome NOME       il nome o l'indirizzo che va nel certificato\n"
	        "                    (predefinito: quello di --indirizzo, e se e'\n"
	        "                     0.0.0.0 va dichiarato: un subjectAltName\n"
	        "                     sbagliato fa comparire un avviso DIVERSO)\n"
	        "  --porta N         predefinito: %s  (RCP.md §2.4)\n"
	        "  --certificati DIR dove stanno i due certificati\n"
	        "  --pagina FILE     la pagina da servire in TCP\n"
	        "  --ban-file FILE   dove si conserva il ban degli indirizzi\n"
	        "                    (RCP.md §4.4-bis: sopravvive al riavvio)\n"
	        "                    ⚠ `--ban` e' lo stesso nome, tenuto perche' e'\n"
	        "                      quello che questo server usava prima\n"
	        "  --comando-socket PATH\n"
	        "                    il socket Unix 0600 del comando di sblocco:\n"
	        "                    «SBLOCCA <indirizzo>» oppure «PING».  Senza,\n"
	        "                    dal ban si esce solo con le 12 ore\n"
	        "  --rilievo DIR     ⭐ fase 2: ci scrive il fotogramma catturato\n"
	        "                    (cattura.bgrx) e i due flussi codificati.\n"
	        "                    Senza, non scrive niente.  Serve al confronto\n"
	        "                    a pixel di F2.6\n"
	        "  --parlantina      registro di dettaglio\n"
	        "\n"
	        "  ⭐ FASE 9 — le tre cure della taratura.  Nascono SPENTE tutte\n"
	        "     e tre (invariante I6: cambiano quel che si VEDE), e il\n"
	        "     valore in vigore finisce nel registro acceso E spento.\n"
	        "  --sgombra-soglia-ms N\n"
	        "                    §5.1: un delta fermo in coda si abbandona\n"
	        "                    solo se la coda non si svuota entro N ms;\n"
	        "                    sotto la soglia si TIENE.  0 = spenta (si\n"
	        "                    abbandona a ogni fotogramma piu' recente,\n"
	        "                    com'e' oggi).  Consigliato quando si accende:\n"
	        "                    100.  La riga la scrive webtransport.c\n"
	        "  --qualita-risale  la qualita' torna su di uno scalino dopo un\n"
	        "                    po' di fotogrammi comodi sotto il tetto di\n"
	        "                    §6.2.  Senza, scesa una volta resta giu' per\n"
	        "                    tutta la sessione.  ⛔ Vive nel FIGLIO: la\n"
	        "                    riga la scrive codificatore.c all'apertura\n"
	        "  --tetto-banda-mbit N\n"
	        "                    N e' il PAVIMENTO in Mbit/s (20, §3.1-bis),\n"
	        "                    non il tetto: filo, punto di lavoro e\n"
	        "                    serbatoio si derivano da li'.  0 = spento, e\n"
	        "                    allora nessuno dice di no alla banda.  ⛔ Vive\n"
	        "                    nel FIGLIO, e vale solo in hardware\n"
	        "\n"
	        "  ⛔ `--figlio-interno` NON si batte a mano: e' la riga con cui\n"
	        "     questo stesso binario riparte come figlio di un utente\n"
	        "     ammesso (DECISIONI.md §1.10-bis).  Se la vedi in `ps`, quello\n"
	        "     e' un figlio, non un secondo server.\n",
	        nome, PORTA_PREDEFINITA);
}

/* ⛔⭐ IL FILE DEL SERVIZIO PAM, GUARDATO ALL'AVVIO — rilievo B-11.
 *
 *     `SPECIFICHE.md` §4.2 vuole il servizio `remotix`.  Se
 *     `/etc/pam.d/remotix` non c'e', Linux-PAM ripiega sul servizio `other`,
 *     che su Debian e' `pam_deny`: **ogni** parola d'ordine giusta viene
 *     rifiutata, e quel che l'utente legge e' «utente o parola d'ordine non
 *     corretti» — cioe' una diagnosi che punta sulla parola d'ordine mentre il
 *     difetto e' un file mancante.
 *
 * ⚠ NON si rifiuta di partire: senza PAM il server non serve a niente, ma il
 *   ban di §4.4-bis, la pagina e i certificati funzionano lo stesso, e
 *   spegnere tutto metterebbe il rosso sull'imputato sbagliato.  ⛔ La riga
 *   pero' si scrive, ed e' la protezione che l'invariante I7 chiede: sta nel
 *   programma, non in una nota di installazione che si perde. */
static void guarda_il_servizio_pam(void)
{
	static const char *dove = "/etc/pam.d/remotix";
	struct stat st;
	if (stat(dove, &st) == 0) {
		registro_dice(REG_AVVIO,
		              "servizio PAM «remotix»: %s c'e' (SPECIFICHE.md §4.2)",
		              dove);
		return;
	}
	registro_dice(REG_AVVIO,
	              "⛔ %s NON C'E' (%s): PAM ripieghera' sul servizio «other», "
	              "che su Debian e' pam_deny — OGNI parola d'ordine giusta "
	              "verra' rifiutata e l'utente leggera' «utente o parola "
	              "d'ordine non corretti».  Si installa src/remotix.pam.",
	              dove, strerror(errno));
}

/* ⛔ Le due cose che il ciclo `poll` deve poter raggiungere quando arriva un
 * verdetto di PAM, e non una sola: il trasporto (per far uscire `AMMESSO`) e la
 * tabella dei figli (per generare il palco di chi e' entrato).  ⚠ Sta in una
 * struttura e non in due globali: una globale e' un secondo posto in cui una
 * cosa puo' essere viva o morta. */
struct ponte {
	trasporto *t;
	figli *f;
};

/* ⛔⭐ IL PONTE FRA L'AIUTANTE, IL TRASPORTO E IL FIGLIO.
 *
 *     `DECISIONI.md` §1.10-bis: il figlio nasce **quando PAM ha detto si'**, e
 *     questa e' l'unica riga del programma in cui quel fatto esiste con accanto
 *     il NOME dell'utente.  ⛔ Non un istante prima: un figlio generato su
 *     `CREDENZIALI` girerebbe come un utente che non ha ancora dimostrato di
 *     essere lui — invariante I3.
 *
 * ⚠ E l'ordine delle due righe conta: prima il figlio, poi il verdetto sul
 *   filo.  Il figlio deve cominciare a collegarsi al bus e a catturare
 *   **mentre** scorre il secondo fisso di §4.4-bis, che e' l'unico tempo
 *   garantito dal protocollo prima che la sessione arrivi a `SESSIONE`.
 *   ⛔ Nessuna delle due aspetta l'altra: `figli_assicura()` fa un `fork` e
 *   torna, `trasporto_verdetto()` fa scorrere lo stato.  Il ciclo non si ferma. */
static void consegna_verdetto(void *ctx, uint64_t pratica, bool ammesso,
                              const char *utente)
{
	struct ponte *p = (struct ponte *)ctx;

	if (ammesso && utente && utente[0]) {
		/* ⛔ «C'era gia'» e «l'ho appena generato» sono due fatti diversi, e la
		 *    differenza serve una riga piu' sotto: a un figlio appena nato NON
		 *    si chiede di rimandare il palco — lo sta prendendo adesso, e la
		 *    domanda produrrebbe un fotogramma doppio. */
		bool c_era = figli_pid_di(p->f, utente) > 0;

		if (!figli_assicura(p->f, utente))
			/* ⚠ Il RIPIEGO SI DICHIARA (`CODER.md` §4.2): la sessione resta
			 *   buona — la stretta di mano finisce, la pagina funziona — e
			 *   semplicemente non c'e' nessun palco da mostrare.  ⛔ Il verdetto
			 *   NON cambia: negare l'accesso perche' il palco non si e' montato
			 *   vorrebbe dire far pagare a chi entra un difetto nostro. */
			registro_dice(REG_FIGLIO,
			              "⚠ «%s» e' AMMESSO ma non ha un figlio: entra e non "
			              "vede un pixel.  Il perche' e' nella riga qui sopra, e "
			              "il verdetto di PAM non si tocca",
			              utente);
		else if (c_era) {
			/* ⛔ Un figlio che c'era gia' puo' avere il ciclo SPENTO — l'ultima
			 *    sessione di quell'utente se n'era andata e il palco aveva
			 *    smesso di catturare.  ⚠ Gli si chiede il fotogramma tenuto
			 *    (l'ultima CHIAVE) cosi' chi rientra vede subito qualcosa,
			 *    mentre `video_regola()` riaccende il ciclo appena `SESSIONE`
			 *    parte.  ⛔ A un figlio APPENA NATO no: lo sta gia' prendendo, e
			 *    la domanda gli farebbe spedire lo stesso fotogramma due
			 *    volte. */
			figli_chiedi_palco(p->f, utente);
		}
	}
	trasporto_verdetto(p->t, pratica, ammesso);
}

/* ⛔⭐ IL FOTOGRAMMA CHE ARRIVA DAL PALCO, E DOVE FINISCE.
 *
 *     Fino alla fase 2 finiva in un DEPOSITO DI PROCESSO — una copia per
 *     codec, con un PADRONE — e il riquadro che stava qui dichiarava il prezzo:
 *     «due utenti collegati insieme non possono vedere tutt'e due il proprio
 *     desktop; la cura vera e' un deposito **per sessione** in
 *     `webtransport.c`».
 *
 * ⭐ LA CURA VERA E' STATA FATTA, ed e' meglio di un deposito per sessione: non
 *    c'e' piu' nessun deposito.  Il figlio cattura di continuo e ogni
 *    fotogramma viene consegnato **subito** alle sessioni di quell'utente —
 *    `wt_video_diffondi()` confronta il nome dell'utente che ha catturato con
 *    quello che PAM ha ammesso su ciascuna sessione, e sono due fatti diversi
 *    chiesti tutt'e due a chi li sa.
 *
 * ⛔ Quindi la guardia dell'invariante I3 non e' sparita: si e' spostata dove
 *    serviva.  Il difetto misurato il 12 agosto 2026 — «prova» che riceve il
 *    desktop di «nicfio» — non e' piu' possibile perche' non c'e' piu' nessun
 *    posto in cui i pixel di un utente aspettino una sessione qualunque.
 *
 * ⚠ E il prezzo dichiarato allora e' PAGATO: due utenti collegati insieme
 *   vedono ciascuno il proprio, e nessuno dei due deve rientrare.  ⭐ Vale la
 *   pena scriverlo, perche' era il difetto che il documento chiamava «brutto e
 *   non curabile qui». */
static void deposita_fotogramma(void *ctx, const char *utente, uid_t uid,
                                uint8_t codec, bool chiave, const uint8_t *dati,
                                size_t byte, uint32_t larghezza,
                                uint32_t altezza, uint64_t istante_us,
                                uint32_t input)
{
	(void)ctx;
	(void)uid;
	/* ⭐⭐ FASE 4 — E QUI `input` NON E' PIU' ZERO.
	 *
	 * ⚠ Questa riga diceva: «`input` e' 0 … quando l'input arrivera' (fase 5)
	 *   qui passera' il suo identificatore».  ⛔ Due cose erano sbagliate: la
	 *   fase e' la **4**, e soprattutto il numero **non nasce qui**.
	 *
	 * ⛔ Lo timbra IL FIGLIO, nell'istante della cattura, e arriva fin qui
	 *    dentro il fotogramma.  Il padre sa che cosa ha **mandato** al palco;
	 *    solo il figlio sa che cosa il compositore ha **preso** e quando ha
	 *    catturato.  ⇒ Riempirlo qui direbbe «l'ultimo input spedito prima
	 *    della spedizione», un numero piu' alto: e l'anello del ritardo
	 *    (`DECISIONI.md` §2.6) misurerebbe un ritardo piu' corto del vero, in
	 *    nostro favore.  `CODER.md` §1-bis: il confine si sposta nella
	 *    direzione **scomoda**.
	 * ⚠ E lo zero resta legittimo: §6.2 lo riserva a «nessuno», ed e' quel che
	 *   vale finche' il client non ha aperto il suo canale di input. */
	wt_video_diffondi(utente, codec, chiave, dati, byte, larghezza, altezza,
	                  istante_us, input);
}

/* ⭐⭐ LA FORMA DEL CURSORE, dal palco al filo — il terzo tubo che attraversa il
 *     confine di processo, e l'unico che lo attraversa **all'incontrario**.
 *
 * ⛔ Il metadato del cursore arriva da PipeWire, cioe' nel figlio; il canale
 *    `CURSORE_FORMA` (`RCP.md` §7.2) vive nel padre.  ⚠ E la POSIZIONE non
 *    viaggia: e' del client, che disegna il puntatore da se' — qui passa solo la
 *    forma, e il ritardo di un giro di rete sulla forma e' il compromesso
 *    accettato (`DECISIONI.md` §5-bis.4). */
static void cursore_dal_palco(void *ctx, const char *utente, uid_t uid,
                              uint16_t larghezza, uint16_t altezza,
                              int16_t attivo_x, int16_t attivo_y,
                              const uint8_t *immagine, size_t byte)
{
	(void)ctx;
	(void)uid;
	wt_cursore_diffondi(utente, larghezza, altezza, attivo_x, attivo_y, immagine,
	                    byte);
}

/* ⛔⭐ LA CUCITURA FRA LA CHIAVE CHIESTA E IL CODIFICATORE — punto 4 della
 *     fase 3, e attraversa DUE confini di modulo e uno di processo.
 *
 *     Chi sa che serve una chiave: `rcp.c` (§5.2 — primo dopo `SESSIONE`, tela
 *     cambiata, `RICHIEDI_CHIAVE` del client, delta abbandonato).
 *     Chi sa a quale sessione appartiene: `webtransport.c`.
 *     Chi ha il codificatore: il FIGLIO, che e' un altro processo.
 *     ⇒ `main.c` e' l'unico che conosce tutt'e tre, e non decide niente: passa.
 *
 * ⚠ Senza questa riga, `rcp_video_serve_chiave()` restava LETTA e inutile e
 *   `codificatore_chiedi_chiave()` non aveva **nessun chiamante nel prodotto**:
 *   il sintomo era «il desktop si ferma e non riparte piu'», e non nominava ne'
 *   la chiave ne' il codificatore.
 *
 * ⛔⭐ E DA QUI PASSANO TRE FATTI DELLA SESSIONE, non uno: il codec, la
 *     PROFONDITA' (17 agosto 2026) e da stasera il LIVELLO (§4.3 riga 701).
 *     ⚠ Tutti e tre sono del CLIENT e non del server — cambiano da sessione a
 *     sessione — ed e' la ragione per cui viaggiano di qui e non sulla riga di
 *     comando del figlio, che il figlio la legge una volta alla nascita. */
static void video_chiedi(void *ctx, const char *utente, uint8_t codec,
                         uint8_t profondita, uint8_t livello_x10, bool chiave)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return;
	figli_video(p->f, utente, codec, profondita, livello_x10, chiave);
}

/* ⭐⭐ LA CUCITURA DELL'AUDIO — fase 7, ed e' la terza della stessa famiglia.
 *
 *     Chi sa che una sessione ha negoziato un codec audio: `rcp.c` (§4.3).
 *     Chi sa a quale sessione appartiene: `webtransport.c`.
 *     ⛔ Chi ha PipeWire: il FIGLIO, che gira come l'utente — un altro processo.
 *     ⇒ `main.c` e' l'unico che conosce tutt'e tre, e **non decide niente**.
 */
static void audio_chiedi(void *ctx, const char *utente, uint8_t codec)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return;
	figli_audio(p->f, utente, codec);
}

/* Il verso di ritorno: un blocco gia' codificato, dalla sessione al filo.
 *
 * ⛔ E qui NON si controlla niente e non si sceglie niente: la guardia I3 — che
 *    l'utente che ha PRODOTTO il suono sia quello che PAM ha ammesso su quella
 *    sessione — sta dentro `wt_audio_diffondi`, accanto a quella dei pixel.
 *    ⚠ Rifarla qui vorrebbe dire due posti che dicono la stessa cosa, e un
 *    giorno uno dei due la direbbe diversa. */
static void audio_blocco(void *ctx, const char *utente, uid_t uid, uint8_t codec,
                         uint64_t istante_us, const uint8_t *dati, size_t byte)
{
	(void)ctx;
	(void)uid;
	wt_audio_diffondi(utente, codec, istante_us, dati, byte);
}

/* ⭐⭐ LA CUCITURA DEGLI APPUNTI — fase 7, ed e' la QUARTA della stessa
 *     famiglia (video, input, audio, appunti).
 *
 *     Chi sa che una sessione ha negoziato `appunti.testo`: `rcp.c` (§4.3).
 *     Chi sa a quale sessione appartiene: `webtransport.c`.
 *     ⛔ Chi parla col compositore: il FIGLIO — la clipboard e' di Mutter
 *        (`STUDI.md` §gnome §10), e Mutter parla con la sessione dell'utente.
 *     ⇒ `main.c` e' l'unico che conosce tutt'e tre, e **non decide niente**.
 */
static bool appunti_offri_al_figlio(void *ctx, const char *utente)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return false;
	return figli_appunti_offri(p->f, utente);
}

static bool appunti_risposta_al_figlio(void *ctx, const char *utente,
                                       uint32_t serial, const char *testo,
                                       size_t byte)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return false;
	return figli_appunti_risposta(p->f, utente, serial, testo, byte);
}

/* I due versi di ritorno, dal desktop al filo.
 *
 * ⛔ E anche qui NON si controlla niente: la guardia I3 — che il testo vada
 *    alla connessione di CHI l'ha copiato — sta dentro `webtransport.c`,
 *    accanto a quella dei pixel e a quella del suono. */
static void appunti_dalla_sessione(void *ctx, const char *utente, uid_t uid,
                                   const char *testo, size_t byte)
{
	(void)ctx;
	(void)uid;
	wt_appunti_dalla_sessione(utente, testo, byte);
}

static void appunti_richiesta_dalla_sessione(void *ctx, const char *utente,
                                             uid_t uid, uint32_t serial)
{
	struct ponte *p = (struct ponte *)ctx;

	(void)uid;
	/* ⛔⛔ E SE NON C'E' NESSUNO A CUI CHIEDERE SI RISPONDE SUBITO, a mani
	 *      vuote.  Il figlio ha un fondo di tempo che lo coprirebbe comunque,
	 *      ⚠ ma qui la risposta si sa GIA': far aspettare quattro secondi chi
	 *      incolla quando la risposta e' certa e' un desktop che sembra
	 *      piantato per una cosa che avevamo capito subito. */
	if (wt_appunti_richiesta(utente, serial))
		return;
	if (p && p->f)
		figli_appunti_risposta(p->f, utente, serial, NULL, 0);
}

/* ⭐⭐ LA CUCITURA DELL'INPUT — fase 4, ed e' la gemella di quella qui sopra.
 *
 *     Chi sa che l'utente ha premuto: `rcp.c`, che ha convalidato il messaggio
 *     secondo `RCP.md` §7.3 — intervalli, surrogati, coordinate sulla tela,
 *     `id` crescente.
 *     Chi sa a quale sessione appartiene: `webtransport.c`.
 *     ⛔ Chi puo' davvero iniettarlo: il FIGLIO, che gira come l'utente ed e'
 *     l'unico ad avere la sessione grafica — cioe' un altro processo.
 *     ⇒ `main.c` e' l'unico che conosce tutt'e tre, e **non decide niente**:
 *       passa.
 *
 * ⛔ E QUESTA RIGA E' LA RAGIONE PER CUI LA FASE 4 ESISTE.  Senza, tutto il
 *    resto sarebbe scritto e non collegato: `rcp.c` convaliderebbe i messaggi,
 *    `input.c` saprebbe iniettare, e fra i due non passerebbe un byte — che e'
 *    esattamente la forma di difetto che la fase 3 ha pagato due volte (la
 *    chiave chiesta senza chiamante, e il monitor catturato che non era quello
 *    su cui stava la shell).  ⚠ Le cuciture non hanno un proprietario, e per
 *    questo nessun banco le guarda: questa ce l'ha. */
/* ⛔⛔⭐ IL TERZO OROLOGIO DI §5.3, E NON E' PIU' QUELLO DELLE SEI ORE.
 *
 *     ✅ Deciso dall'utente il 16 agosto 2026, su misure prese apposta:
 *
 *       > *«niente timeout delle 6 ore: se dopo 60 minuti non c'e' traccia di
 *       > input la sessione viene killata»*
 *
 *     `SPECIFICHE.md` §5.3 diceva «6 ore senza alcun attacco ⇒ la sessione si
 *     chiude».  ⚠ Cambiano DUE cose, non una: il tetto (6 ore → 60 minuti) e
 *     **il criterio** — non piu' «nessuno si e' attaccato», ma «nessuno ha
 *     toccato niente».
 *
 * ⭐ E la decisione e' venuta da un numero, non da un'idea: `[M]` una sessione
 *    abbandonata costa **477 MB** (PSS) e **~0,017 % di un nucleo**, e in quattro
 *    minuti di osservazione non cresce di un megabyte — 477 · 476 · 476 · 477 ·
 *    477 · 477 · 477 · 477 · 477.  ⇒ Non e' una perdita, e' un costo fisso; e
 *    l'utente ha scelto di non pagarlo per un'ora invece che per sei.
 *
 * ⛔ CHE COSA CONTA COME «INPUT», e la distinzione e' tutta qui: i cinque gesti
 *    veri.  ⚠ NON il rilascio al distacco (§7.3), che arriva proprio quando
 *    l'utente se ne va e azzererebbe l'orologio nell'istante sbagliato; non la
 *    ritela, che parte da sola al riattacco; non la richiesta di uscire.
 *
 * ⚠ E si e' considerato — e SCARTATO, con l'utente — di azzerare l'orologio
 *   anche al riaggancio: *«la tua ipotesi comporta il fatto che l'utente in 10
 *   minuti non fa nemmeno un clic col mouse, alquanto improbabile»*.  ⇒ Si conta
 *   l'input e basta, che e' anche la regola piu' semplice da spiegare. */
#define ABBANDONO_PREDEFINITO_MS 3600000u /* 60 minuti */
static uint64_t abbandono_ms = ABBANDONO_PREDEFINITO_MS;
/* ⛔ Il tono di prova della fase 7: `0` = spento, ed e' il valore di ogni
 *    installazione normale (invariante I6). */
static uint32_t audio_prova_hz;

/* ⛔⭐⭐ I TRE INTERRUTTORI DELLA FASE 9, E NASCONO TUTT'E TRE SPENTI.
 *
 *      Invariante I6: cio' che cambia quel che si VEDE sta dietro un
 *      interruttore spento finche' l'utente non l'ha guardato sul desktop
 *      vero.  ⚠ Fino al 23 agosto 2026 le tre cure esistevano ma **nessuno le
 *      chiamava**: un interruttore che non si puo' accendere non e' un
 *      interruttore, e' codice morto — e la fase 9 non poteva misurare ne' il
 *      prima ne' il dopo.
 *
 * ⛔ E DUE DELLE TRE NON VIVONO QUI.  La soglia della coda video e' del
 *    trasporto, che sta in questo processo; la risalita della qualita' e il
 *    tetto di banda sono del **codificatore**, che sta nel FIGLIO — un altro
 *    programma, nato con `execve` e ambiente composto da zero.  ⇒ Non si
 *    passano con una variabile d'ambiente (non arriverebbe): si passano nella
 *    riga di comando del figlio, come `--parlantina` (`figlio.c`, il riquadro
 *    in `diventa_ed_esegui()`), e `figli_fase9()` e' la porta. */
static uint64_t sgombra_soglia_ms;  /* --sgombra-soglia-ms, 0 = spenta   */
static bool qualita_risale;         /* --qualita-risale, assente = spenta */
static uint32_t tetto_banda_mbit;   /* --tetto-banda-mbit, 0 = spento    */
/* ⛔⭐ La QUARTA, ed e' la sola che sta nel TRASPORTO come la prima: il ritmo
 *     lo decide chi vede la coda d'uscita.  ⚠ E dipende dalla prima — con
 *     `--sgombra-soglia-ms 0` non scatta mai, e il server lo SCRIVE all'avvio
 *     invece di lasciar misurare un anello morto (`webtransport.c`,
 *     `wt_ritmo_adattivo()`). */
static bool ritmo_adattivo;         /* --ritmo-adattivo, assente = spento */

/* ⛔ Uno per utente, e non per sessione RCP: l'orologio DEVE sopravvivere al
 *    client che se ne va — e' proprio il caso per cui esiste.  ⚠ Sedici bastano:
 *    §5.1 vuole un utente remoto per volta (I2), e il multi-tenant e' della
 *    fase 10. */
#define QUANTI_PRESENTI 16
static struct {
	char utente[257];
	uint64_t ultimo_input_ms;
} presenti[QUANTI_PRESENTI];

/* ⭐ «Qui c'e' stato un gesto adesso.»  Se l'utente non c'e' in tabella lo si
 *    aggiunge: il primo gesto e' anche il primo segno di presenza. */
static void presenza_segna(const char *utente, uint64_t ora_ms)
{
	int libero = -1;
	if (!utente || !utente[0])
		return;
	for (int i = 0; i < QUANTI_PRESENTI; i++) {
		if (presenti[i].utente[0] == '\0') {
			if (libero < 0)
				libero = i;
			continue;
		}
		if (strcmp(presenti[i].utente, utente) == 0) {
			presenti[i].ultimo_input_ms = ora_ms;
			return;
		}
	}
	if (libero < 0)
		return; /* ⛔ Non e' un guasto da fermare tutto: al peggio quell'utente
		         *    non ha l'orologio dell'abbandono, e la sessione resta. */
	snprintf(presenti[libero].utente, sizeof presenti[libero].utente, "%s",
	         utente);
	presenti[libero].ultimo_input_ms = ora_ms;
}

static void presenza_dimentica(const char *utente)
{
	if (!utente)
		return;
	for (int i = 0; i < QUANTI_PRESENTI; i++)
		if (strcmp(presenti[i].utente, utente) == 0)
			presenti[i].utente[0] = '\0';
}

static bool input_al_figlio(void *ctx, const char *utente, uint32_t id,
                            uint8_t azione, uint16_t codice, int premuto,
                            int32_t a, int32_t b)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return false;
	/* ⛔ SOLO i cinque gesti veri: la ragione sta sul riquadro qui sopra. */
	if (azione == FIGLI_INPUT_PUNTATORE || azione == FIGLI_INPUT_PULSANTE ||
	    azione == FIGLI_INPUT_ROTELLA || azione == FIGLI_INPUT_LETTERA ||
	    azione == FIGLI_INPUT_POSIZIONE)
		presenza_segna(utente, registro_ora_ms());
	return figli_input(p->f, utente, id, azione, codice, premuto, a, b);
}

/* ⭐⭐ LA CUCITURA DELLA TELA — e chiude la catena che il mandato della fase 4
 *     chiamava per nome: `figli_ritela()` → `cattura_ridimensiona()`.
 *
 *     Chi sa che l'utente ha chiesto un'altra misura: `rcp.c`, che ha applicato
 *     §7.1 e `rcp_misura_ammessa()` — intervallo, parita', e il tetto che tiene
 *     in vita il compositore di chi ci ospita.
 *     Chi sa a quale sessione appartiene: `webtransport.c`.
 *     ⛔ Chi puo' davvero cambiarla: il FIGLIO, che ha il flusso PipeWire.
 *     ⇒ `main.c` e' l'unico che conosce tutt'e tre, e **non decide niente**.
 *
 * ⛔ E questa riga vale quattro sintomi, non uno (`DECISIONI.md` §5.0-sexies):
 *    le bande nere laterali, il testo interpolato, il ri-attacco a misura
 *    diversa, e ⭐ **i quattro secondi fra il login e il desktop** — perche'
 *    `pw_stream_update_params()` e' un riavvio del flusso, e un riavvio
 *    consegna un buffer anche a scena ferma. */
/*
 * ⭐⭐ §7.6 di `RCP.md` — «L'UTENTE HA CHIESTO DI USCIRE».
 *
 * ⛔ DUE COSE, E IN QUEST'ORDINE:
 *
 *   1. si congedano **gli altri client di quell'utente** con `0x10`.  La
 *      sessione grafica e' UNA (I2): chi la stesse guardando da un secondo
 *      dispositivo resterebbe con uno schermo fermo per sempre, e nessuna riga
 *      gli direbbe perche'.  ⚠ Chi ha chiesto e' gia' stato congedato da
 *      `rcp.c`, e infatti si salta (`tranne`);
 *   2. **poi** si chiede al figlio di terminare la sessione.
 *
 * ⛔ L'ordine e' normativo e non e' una preferenza: quando il compositore cade,
 *    il palco cade con lui e i canali non servono piu'.  Un `0x10` spedito dopo
 *    e' un motivo che esiste e che nessuno riceve — il rilievo B-7 con un nome
 *    nuovo.
 */
static void termina_al_figlio(void *ctx, const char *utente)
{
	struct ponte *p = (struct ponte *)ctx;
	size_t altri;

	if (!p || !p->f || !utente)
		return;

	altri = wt_congeda_utente(utente, RCP_SESSIONE_TERMINATA,
	                          "un altro client di questo utente ha chiuso la "
	                          "sessione", NULL);
	if (altri)
		registro_dice(REG_WT,
		              "⭐ §7.6: congedati con 0x10 anche %zu altri client di «%s» "
		              "— la sessione grafica e' una sola (I2), e chi la stava "
		              "guardando deve saperlo adesso, non fra trenta secondi",
		              altri, utente);

	if (!figli_termina_sessione(p->f, utente, FIGLI_USCITA_UTENTE))
		registro_dice(REG_AVVIO,
		              "⛔ §7.6: la richiesta di terminare la sessione di «%s» NON "
		              "e' partita verso il figlio: i client sono stati congedati "
		              "con 0x10 e il desktop e' ancora li'.  ⚠ Due verita' sullo "
		              "stesso fatto, e questa riga e' l'unico posto in cui si vede",
		              utente);
}

/* ⛔⛔⭐ §5.3 — L'ABBANDONO SCADE, e la sessione si chiude.
 *
 *     ⚠ E l'ordine e' lo STESSO di §7.6 e per la stessa ragione normativa:
 *     prima si dice a chi guarda PERCHE', poi si chiude.  Quando il compositore
 *     cade il palco cade con lui, e un motivo spedito dopo e' un motivo che
 *     nessuno riceve (rilievo B-7).
 *
 * ⭐ E il motivo e' `0x03 SESSIONE_ABBANDONATA`, che §8.2 aveva gia' e che
 *    **nessuna riga di codice aveva mai spedito** — la stessa forma E1 di
 *    `0x02` fino a stamattina.  ⚠ Di solito non lo ricevera' nessuno: se
 *    l'orologio scade e' perche' non c'era piu' nessuno.  Ma «di solito» non e'
 *    «mai», e chi c'e' deve leggere una frase invece di guardare uno schermo
 *    fermo. */
static void abbandono_scaduto(struct ponte *p, const char *utente,
                              uint64_t fermo_ms)
{
	size_t quanti;

	registro_dice(REG_AVVIO,
	              "⭐ §5.3 — ABBANDONO: «%s» non tocca niente da %llu ms (tetto "
	              "%llu).  ⛔ CHIUDO la sessione grafica, e con lei i suoi "
	              "programmi: e' la decisione dell'utente del 16 agosto 2026, "
	              "«se dopo 60 minuti non c'e' traccia di input la sessione "
	              "viene killata»",
	              utente, (unsigned long long)fermo_ms,
	              (unsigned long long)abbandono_ms);

	quanti = wt_congeda_utente(utente, RCP_SESSIONE_ABBANDONATA,
	                           "sessione abbandonata: nessun input entro il "
	                           "tetto di §5.3",
	                           NULL);
	if (quanti)
		registro_dice(REG_WT,
		              "⚠ §5.3: c'erano ANCORA %zu client attaccati a «%s», "
		              "congedati con 0x03 prima di chiudere — guardavano senza "
		              "toccare niente da %llu ms (tetto %llu).  ⛔ E il numero si "
		              "SCRIVE invece di dirlo a parole: il tetto e' configurabile, "
		              "e «un'ora» sarebbe vero solo col valore predefinito",
		              quanti, utente, (unsigned long long)fermo_ms,
		              (unsigned long long)abbandono_ms);

	if (!figli_termina_sessione(p->f, utente, FIGLI_USCITA_ABBANDONO))
		registro_dice(REG_AVVIO,
		              "⛔ §5.3: la richiesta di chiudere la sessione abbandonata "
		              "di «%s» NON e' partita verso il figlio: i client sono "
		              "stati congedati con 0x03 e il desktop e' ancora li'",
		              utente);
	/* ⛔ Si dimentica COMUNQUE: se la chiusura non e' passata, riprovare ogni
	 *    giro riempirebbe il registro di una riga al secondo per un guasto che
	 *    la prima riga ha gia' detto.  ⚠ E se una sessione nuova nascera', il
	 *    suo primo gesto la rimettera' in tabella. */
	presenza_dimentica(utente);
}

/* ⭐ Il giro dell'orologio.  ⚠ Chiamato a ogni passata del ciclo: non costa
 *    niente (sedici confronti) e una scadenza che aspetta un evento e' una
 *    scadenza che non scatta mai — la lezione di `regola_battito`. */
static void abbandono_giro(struct ponte *p, uint64_t ora_ms)
{
	if (!abbandono_ms || !p || !p->f)
		return;
	for (int i = 0; i < QUANTI_PRESENTI; i++) {
		if (presenti[i].utente[0] == '\0')
			continue;
		if (ora_ms <= presenti[i].ultimo_input_ms)
			continue;
		if (ora_ms - presenti[i].ultimo_input_ms > abbandono_ms) {
			/* ⛔ Una COPIA, non il puntatore: `abbandono_scaduto()` finisce
			 *    chiamando `presenza_dimentica()`, che azzera proprio quella
			 *    casella — e il nome serve fino all'ultima riga.
			 * ⚠ `memcpy` e non `snprintf`: la sorgente ha la stessa misura
			 *   della destinazione, e il compilatore non puo' saperlo. */
			char chi[sizeof presenti[0].utente];
			memcpy(chi, presenti[i].utente, sizeof chi);
			chi[sizeof chi - 1] = '\0';
			abbandono_scaduto(p, chi, ora_ms - presenti[i].ultimo_input_ms);
		}
	}
}

/*
 * ⭐ §7.6, il gemello: la sessione grafica e' finita e non l'ha chiesta nessun
 *    client — l'utente e' uscito dal menu del desktop.
 *
 * ⛔ Chi guarda viene congedato con `0x10` ADESSO.  Tacendo, resterebbe su uno
 *    schermo fermo fino ai trenta secondi del silenzio e poi leggerebbe «errore
 *    di rete»: e' il rilievo B-7, e questa e' la riga che lo impedisce.
 */
static void sessione_finita_dal_figlio(void *ctx, const char *utente, uid_t uid)
{
	size_t quanti;

	(void)ctx;
	(void)uid;
	quanti = wt_congeda_utente(utente, RCP_SESSIONE_TERMINATA,
	                           "la sessione grafica e' terminata", NULL);
	registro_dice(REG_WT,
	              "⭐ §7.6: la sessione di «%s» e' finita dal desktop — congedati "
	              "%zu client con 0x10 (⚠ zero e' normale: puo' non guardare "
	              "nessuno)",
	              utente, quanti);
}

/* ⭐ §7.1: il palco non c'e' ancora — si rimanda il fondo invece di rispondere
 *    `NON_ORA` a una domanda che sta per avere una risposta vera. */
static void tela_attendi_dal_figlio(void *ctx, const char *utente, uid_t uid,
                                    uint32_t voluta_l, uint32_t voluta_a)
{
	(void)ctx;
	(void)uid;
	wt_tela_rimanda(utente, voluta_l, voluta_a);
}

/* ⭐ §5-bis.7 — e delega a `figli_disposizione()` come `ritela_al_figlio()`
 *    delega a `figli_ritela()`: questo file e' il ponte, non la regola. */
static bool disposizione_al_figlio(void *ctx, const char *utente,
                                   const char *nome)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return false;
	return figli_disposizione(p->f, utente, nome);
}

static bool ritela_al_figlio(void *ctx, const char *utente, uint32_t larghezza,
                             uint32_t altezza)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return false;
	return figli_ritela(p->f, utente, larghezza, altezza);
}

/* ⛔ Il figlio se n'e' andato.  ⚠ Non c'e' piu' nessun deposito da svuotare —
 * era la cura della fase 2 — ma la riga resta perche' il fatto e' un fatto: da
 * adesso quell'utente non ha piu' un palco, e le sue sessioni non vedranno piu'
 * arrivare fotogrammi.  ⛔ E NON si chiude niente: `SPECIFICHE.md` §8.3, «mai
 * staccare» — una sessione senza fotogrammi vale piu' di una sessione chiusa. */
static void congeda_figlio(void *ctx, const char *utente, uid_t uid)
{
	(void)ctx;
	registro_dice(REG_VIDEO,
	              "⛔ il palco di «%s» (uid %ld) se n'e' andato: da adesso le sue "
	              "sessioni non ricevono piu' fotogrammi.  ⚠ NON si chiude "
	              "niente (I1, SPECIFICHE.md §8.3): una sessione ferma vale piu' "
	              "di una sessione staccata, e il palco puo' rinascere",
	              utente, (long)uid);
	/* ⛔⭐ E LA MISURA DEL SUO PALCO SI DIMENTICA — difetto trovato refutando, la
	 *     notte del 15 agosto 2026: quel numero serve al RI-ATTACCO
	 *     (`SESSIONE` concede la tela che il palco ha gia'), e un numero di un
	 *     palco morto e' peggio di nessun numero — fa concedere una tela che
	 *     nessun fotogramma avra' mai. */
	wt_palco_dimentica(utente);

	/*
	 * ⭐⭐⭐ §7.6, IL GEMELLO — E STA QUI, NON NEL FIGLIO.  Difetto trovato dal
	 *      banco del logout, 15 agosto 2026.
	 *
	 * ⛔ Il figlio aveva il codice per accorgersi che la sessione grafica era
	 *    finita («c'era e adesso non c'e' piu'»), e `[M]` non e' mai scattato:
	 *    **al logout il figlio muore col segnale 15**.  E' lui il processo
	 *    GUIDA della sessione logind — la apre lui con `pam_open_session` — e
	 *    quando la sessione finisce se lo porta via.  ⇒ Non puo' riferire un
	 *    fatto che lo uccide.
	 *
	 * ⭐ Ma il padre lo RACCOGLIE, ed e' esattamente questa riga.  ⇒ Figlio
	 *    morto = sessione grafica finita, sempre: il palco vive nel figlio, e
	 *    la sessione logind pure.
	 *
	 * ⚠ E vale anche se il figlio e' morto per un guasto invece che per una
	 *   scelta dell'utente: da qui non si distinguono, ⛔ e il comportamento
	 *   giusto e' lo stesso — dirlo a chi guarda invece di lasciarlo davanti a
	 *   uno schermo fermo per i trenta secondi del silenzio, che e' il rilievo
	 *   B-7.  Il motivo `0x10` dice «la sessione e' terminata», che in tutt'e
	 *   due i casi e' vero.
	 *
	 * ⛔ MA NON QUANDO SI STA SPEGNENDO IL SERVER: li' il motivo giusto e'
	 *    `0x0C SERVER_IN_CHIUSURA`, e lo manda `main()` a tutte le sessioni.
	 *    Dire `0x10` a chi sta per ricevere `0x0C` sarebbe dirgli che la sua
	 *    sessione e' finita quando invece la ritrovera'.
	 */
	if (!si_ferma) {
		size_t quanti = wt_congeda_utente(utente, RCP_SESSIONE_TERMINATA,
		                                  "la sessione grafica e' terminata",
		                                  NULL);
		if (quanti)
			registro_dice(REG_WT,
			              "⭐ §7.6: il palco di «%s» se n'e' andato ⇒ la sessione "
			              "grafica e' finita: congedati %zu client con 0x10 invece "
			              "di lasciarli su uno schermo fermo",
			              utente, quanti);
	}
}

/* ⭐⭐ LA RISPOSTA DEL PALCO SULLA TELA — §7.1, e attraversa il confine nel verso
 *     del cursore: la domanda e' uscita con `figli_ritela()`, questa rientra.
 *
 * ⛔ E il padre non la INDOVINA piu' dai fotogrammi: il figlio dice a quale
 *    richiesta risponde (`voluta`) e che cosa il palco ha davvero (`avuta`, con
 *    `0x0` = non ce l'ha fatta).  ⚠ Senza, due `ADATTA_TELA` incatenate — un
 *    utente che trascina il bordo — facevano prendere il fotogramma della prima
 *    per la risposta della seconda. */
/* ⭐ §5.1 — l'adattatore fra il gancio di `webtransport.c` e `sentinella.c`.
 *
 * ⛔ E' qui e non la' perche' `webtransport.c` non conosce logind e non deve:
 *    quel modulo sa **quali sessioni sono di quell'utente**, questo sa **chi
 *    chiedere**.  Sono due mestieri, e tenerli separati e' quel che permette al
 *    banco di innestare un guardiano finto senza toccare il trasporto. */
static bool chiedi_sessione_locale(void *ctx, const char *utente, char *quale,
                                   size_t quanto)
{
	return sentinella_locale((sentinella *)ctx, utente, quale, quanto);
}

static void tela_dal_palco(void *ctx, const char *utente, uid_t uid,
                           uint32_t voluta_l, uint32_t voluta_a, uint32_t avuta_l,
                           uint32_t avuta_a)
{
	(void)ctx;
	(void)uid;
	wt_tela_dal_palco(utente, voluta_l, voluta_a, avuta_l, avuta_a);
}

int main(int argc, char **argv)
{
	const char *indirizzo = "0.0.0.0";
	const char *nome = NULL;
	const char *porta = PORTA_PREDEFINITA;
	const char *dir_cert = "/var/lib/remotix/certificati";
	const char *file_html = "pagina.html";
	const char *file_ban = "/var/lib/remotix/ban";
	const char *socket_comando = NULL;
	const char *dir_rilievo = NULL;
	certificati cert;
	SSL_CTX *ctx_quic = NULL, *ctx_pagina = NULL;
	trasporto *t = NULL;
	pagina *p = NULL;
	comando *k = NULL;
	aiutante *pam_aiuto = NULL;  /* ⚠ non «aiuto»: quel nome e' gia' della funzione che stampa l'uso */
	figli *prole = NULL;
	struct ponte ponte;
	sentinella *guardiano = NULL;
	time_t ultimo_controllo_cert;
	uint64_t ultimo_ripasso_locali = 0;
	int esito = 1;

	/* ⛔⭐ E QUESTA E' LA PRIMA RIGA DEL PROGRAMMA, PRIMA DI QUALUNQUE ALTRA
	 *     COSA: se siamo il figlio, non siamo un server.
	 *
	 *     `figli_assicura()` ci ha gia' fatto scendere all'uid dell'utente e ha
	 *     fatto `exec` di questo stesso binario (`figlio.c`, riquadro in testa:
	 *     senza `exec` il figlio avrebbe in memoria la chiave privata TLS del
	 *     server, e la memoria di un processo appartiene al suo proprietario).
	 *     ⛔ Qui non si apre niente, non si legge nessun certificato e non si
	 *     tocca il file dei ban: si va dritti a `figlio_vive()`, che non torna. */
	if (argc >= 2 && strcmp(argv[1], "--figlio-interno") == 0) {
		figlio_vive(argc, argv);
		return 1; /* non ci si arriva */
	}

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (strcmp(a, "--indirizzo") == 0 && v)
			indirizzo = argv[++i];
		else if (strcmp(a, "--nome") == 0 && v)
			nome = argv[++i];
		else if (strcmp(a, "--porta") == 0 && v)
			porta = argv[++i];
		else if (strcmp(a, "--certificati") == 0 && v)
			dir_cert = argv[++i];
		else if (strcmp(a, "--pagina") == 0 && v)
			file_html = argv[++i];
		/* ⛔ DUE NOMI PER LA STESSA OPZIONE, E SI ACCETTANO TUTT'E DUE —
		 *    rilievo R12.9a, 10 agosto 2026 notte.  Questo server diceva
		 *    `--ban`; l'ospite dei banchi (`01-b3-rcp-innesta.py`) e i loro
		 *    script di lancio dicono `--ban-file`.  ⚠ Chi porta al prodotto la
		 *    riga di comando che i banchi usano otteneva `aiuto()` e uscita 2
		 *    — un fallimento chiaro, che e' il modo giusto di sbagliare, ma un
		 *    fallimento che nessuno dei due documenti spiegava.  Nessun `.md`
		 *    nomina l'uno o l'altro: finche' non lo fa, li si accetta
		 *    entrambi e l'aiuto dichiara quale dei due e' il nome buono. */
		else if ((strcmp(a, "--ban-file") == 0 || strcmp(a, "--ban") == 0) && v)
			file_ban = argv[++i];
		else if (strcmp(a, "--comando-socket") == 0 && v)
			socket_comando = argv[++i];
		/* ⭐ FASE 2 — dove scrivere il fotogramma catturato e i due flussi.
		 *
		 * ⛔ Serve al banco del giudizio a pixel (F2.6): senza, il confronto
		 *    fra CATTURATO e DIPINTO non ha il primo dei due termini, e
		 *    l'unico modo di prenderlo sarebbe ricatturare con un altro
		 *    programma — cioe' confrontare il dipinto con un fotogramma
		 *    DIVERSO, preso un istante dopo.
		 * ⚠ E' spento di suo: senza questa opzione il server non scrive un
		 *   byte in piu' di prima. */
		else if (strcmp(a, "--rilievo") == 0 && v)
			dir_rilievo = argv[++i];
		else if (strcmp(a, "--parlantina") == 0)
			registro_parlantina(true);
		/* ⛔⭐ §5.3 — il secondo dei tre orologi, e il documento vuole che sia
		 *     configurabile: *«il secondo e il terzo sono configurabili, con
		 *     quei valori come predefiniti»*.
		 *
		 * ⚠ IN SECONDI, non in minuti, e la ragione e' che un tetto da
		 *   mezz'ora **non si puo' provare** se il minimo e' un minuto: si
		 *   aspetta mezz'ora ogni volta, cioe' non lo si prova mai.  ⭐ Coi
		 *   secondi il meccanismo si esercita in dieci, e il NUMERO
		 *   predefinito si legge nella riga che il server scrive all'avvio.
		 *
		 * ⛔ `0` = spenta, ed e' un valore lecito e dichiarato. */
		else if (strcmp(a, "--inattivita-s") == 0 && v)
			rcp_inattivita_imposta((uint64_t)strtoull(argv[++i], NULL, 10) * 1000);
		/* ⛔⭐ §5.3, il terzo: «se dopo 60 minuti non c'e' traccia di input la
		 *     sessione viene killata» (decisione dell'utente, 16 agosto 2026).
		 *     ⚠ `0` = spento, e allora nessuna sessione viene mai chiusa da se'. */
		else if (strcmp(a, "--abbandono-s") == 0 && v)
			abbandono_ms = (uint64_t)strtoull(argv[++i], NULL, 10) * 1000;
		/* ⛔⭐ FUNZIONE DI BANCO — fase 7: un tono di prova al posto dell'audio
		 *     della sessione.  ⚠ Serve a mettere in prova il codificatore, il
		 *     datagram e il browser con un segnale noto **campione per
		 *     campione**, invece di accendere cinque anelli e restare con
		 *     cinque imputati.
		 *
		 * ⛔ Spento se nessuno lo accende — invariante I6 — e quando e' acceso
		 *    il server lo SCRIVE nel registro a ogni sessione. */
		else if (strcmp(a, "--audio-prova") == 0 && v)
			audio_prova_hz = (uint32_t)strtoul(argv[++i], NULL, 10);
		/* ⛔⭐⭐ LE TRE CURE DELLA FASE 9, e valgono tutte la stessa regola dei
		 *      tre orologi qui sopra: il MECCANISMO si esercita a valori corti
		 *      dalla riga di comando, il NUMERO in vigore si legge nella riga
		 *      che il server (o il figlio) scrive all'avvio.
		 *
		 * ⚠ In MILLISECONDI e non in fotogrammi: la soglia e' un ritardo che
		 *   si VEDE, e chi la accende sceglie quanto vecchia puo' essere
		 *   l'immagine per una frazione di secondo (`webtransport.h`, il
		 *   riquadro sopra `wt_sgombra_soglia`).  ⛔ `0` = spenta, ed e' il
		 *   comportamento di oggi byte per byte. */
		else if (strcmp(a, "--sgombra-soglia-ms") == 0 && v)
			sgombra_soglia_ms = (uint64_t)strtoull(argv[++i], NULL, 10);
		/* ⛔ Senza argomento, come `--parlantina`: e' un si'/no, e un numero
		 *    accanto suggerirebbe una taratura che non c'e' (i tre numeri della
		 *    risalita stanno in `codificatore.c` e li tara il banco). */
		else if (strcmp(a, "--qualita-risale") == 0)
			qualita_risale = true;
		/* ⛔ L'argomento e' il PAVIMENTO in Mbit/s (20, quello di
		 *    `DECISIONI.md` §3.1-bis), non il tetto: filo, punto di lavoro e
		 *    serbatoio si derivano da li' in un posto solo (`codificatore.c`).
		 *    ⚠ `0` = spento, e allora nessuno dice di no alla banda. */
		else if (strcmp(a, "--tetto-banda-mbit") == 0 && v)
			tetto_banda_mbit = (uint32_t)strtoul(argv[++i], NULL, 10);
		/* ⛔⭐⭐ FASE 9 — IL REGOLATORE DEL RITMO.  Senza argomento, come
		 *      `--qualita-risale`: e' un si'/no, e un numero accanto
		 *      suggerirebbe una taratura che non sta qui (i posti sono
		 *      `WT_RITMO_POSTI` in `webtransport.c`, e li tara il banco).
		 *
		 * ⛔ Nasce SPENTO (I6) perche' cambia QUEL CHE SI VEDE: meno fotogrammi
		 *    quando la linea non porta.  L'utente lo giudica sul desktop vero
		 *    prima che diventi il comportamento normale — e' la lezione pagata
		 *    con l'azzeramento della fase 10 di v1.
		 *
		 * ⚠⚠ E NON BASTA DA SOLO: senza `--sgombra-soglia-ms N` la coda dei
		 *    delta si svuota a ogni fotogramma, l'arretrato non supera 1 e
		 *    questo regolatore non scatta MAI.  Il server lo SCRIVE all'avvio,
		 *    cosi' nessuno misura un anello morto credendolo vivo. */
		else if (strcmp(a, "--ritmo-adattivo") == 0)
			ritmo_adattivo = true;
		else if (strcmp(a, "--sblocca") == 0) {
			/* ⛔⭐ E QUESTA OPZIONE NON C'E' PIU', E NON SI TACE SUL PERCHE'
			 *     — rilievo R12.1, 10 agosto 2026 notte.
			 *
			 *     `remotix --sblocca IND` era un SECONDO PROCESSO: caricava il
			 *     file dei ban, toglieva la voce dalla tabella **del processo
			 *     nuovo**, riscriveva il file, stampava «era bannato, adesso
			 *     e' libero» e usciva **0**.  ⛔ Il processo che SERVE non
			 *     vedeva niente: la sua `tentativi[]` restava intatta, il
			 *     quarto tentativo riceveva ancora `TROPPI_TENTATIVI`, e al
			 *     primo ban successivo di chiunque altro `salva_ban()`
			 *     riscriveva il file dalla memoria stantia — **il ban tolto
			 *     tornava anche su disco**.
			 *
			 *     ⚠ Il danno non era che non funzionava: era che **usciva 0
			 *       dicendo che aveva funzionato**.
			 *
			 * ⛔ Un messaggio, e non `aiuto()`: chi ha in mano un comando che
			 *    per un giorno e' esistito deve leggere PERCHE' non c'e' piu',
			 *    o cerchera' l'errore di battitura. */
			fprintf(stderr,
			        "⛔ --sblocca non esiste piu', e non e' un cambio di nome.\n"
			        "   Il ban vive nella memoria del processo che serve: un "
			        "secondo processo puo' solo\n"
			        "   riscrivere il file, e il server continuerebbe a "
			        "rispondere TROPPI_TENTATIVI fino\n"
			        "   al riavvio — uscendo 0 come se avesse funzionato "
			        "(RCP.md §4.4-bis).\n"
			        "\n"
			        "   Si accende il server con --comando-socket PATH e si "
			        "sblocca cosi':\n"
			        "       python3 banchi/01-b8-sblocca.py --socket PATH "
			        "192.168.0.2\n"
			        "   oppure, senza strumenti:\n"
			        "       printf 'SBLOCCA 192.168.0.2\\n' | nc -U PATH\n");
			return 2;
		} else {
			aiuto(argv[0]);
			return 2;
		}
	}
	if (!nome)
		nome = indirizzo;

	if (!nome[0] || strcmp(nome, "0.0.0.0") == 0 || strcmp(nome, "::") == 0) {
		/* ⛔ `RCP.md` §4.1: «il certificato DEVE portare come
		 *    `subjectAltName` l'indirizzo su cui il server risponde».  Un
		 *    SAN `0.0.0.0` non combacia con NIENTE, e ⚠ «un browser che
		 *    trova un SAN che non combacia mostra un avviso DIVERSO, e
		 *    alcuni non offrono nemmeno il clic per proseguire».  Non si
		 *    indovina: si chiede. */
		fprintf(stderr,
		        "⛔ serve --nome: il certificato deve portare l'indirizzo su "
		        "cui il server risponde (RCP.md §4.1), e «%s» non e' un "
		        "indirizzo.\n",
		        nome);
		return 2;
	}

	signal(SIGINT, al_segnale);
	signal(SIGTERM, al_segnale);
	signal(SIGPIPE, SIG_IGN);

	registro_dice(REG_AVVIO, "REMOTIX_V2 — fase 1, il filo nudo");

	/* ⛔⭐ I TRE OROLOGI DI §5.3 SI SCRIVONO ALL'AVVIO, e non e' decorazione.
	 *
	 *     Un tetto da mezz'ora si prova in due modi: aspettando mezz'ora, o
	 *     leggendo il numero.  ⚠ Il primo non lo fa nessuno — «significa tenere
	 *     il PC occupato», parole dell'utente il 16 agosto 2026 — quindi senza
	 *     questa riga il valore in vigore non lo verifica MAI nessuno, ed e'
	 *     esattamente la forma E1 («scritto non e' in vigore») che ci e' gia'
	 *     costata cara.
	 *
	 * ⭐ Cosi' il MECCANISMO si prova a valori corti (`--inattivita-s 10`) e il
	 *    NUMERO si legge qui.  Sono due verifiche diverse, e nessuna delle due
	 *    tiene occupata una macchina. */
	registro_dice(REG_AVVIO,
	              "⭐ §5.3, i tre orologi in vigore: silenzio del client 30 s "
	              "(fisso) · inattivita' dell'utente %llu s%s · ⛔ abbandono "
	              "della sessione %llu s%s — e allo scadere la sessione grafica "
	              "si CHIUDE, coi programmi aperti dentro",
	              (unsigned long long)(rcp_inattivita() / 1000),
	              rcp_inattivita() ? "" : " (SPENTA)",
	              (unsigned long long)(abbandono_ms / 1000),
	              abbandono_ms ? "" : " (SPENTO)");

	/* ⛔ E il tono di prova si dichiara QUI, prima di ogni sessione: un server
	 *    che suonasse un tono senza dirlo sarebbe un difetto travestito da
	 *    funzione.  ⚠ `wt_audio_prova()` scrive la sua riga solo quando e'
	 *    acceso, ed e' voluto: un registro che ripete «spento» a ogni avvio
	 *    non si legge piu'. */
	wt_audio_prova(audio_prova_hz);

	/* ⛔⭐ E LA SOGLIA DELLA CODA VIDEO SI DICHIARA SEMPRE, accesa **e** spenta
	 *     — al contrario del tono di prova qui sopra, e la differenza non e'
	 *     un capriccio: un tono che non suona non lo cerca nessuno, ma una
	 *     soglia spenta e una soglia che non e' mai scattata producono lo
	 *     stesso registro (zero abbandoni per soglia), e chi rilegge un banco
	 *     non saprebbe quale dei due ha misurato.  ⇒ La riga la scrive
	 *     `webtransport.c`, cioe' **chi il numero lo usa davvero**, e non
	 *     questo file che l'ha solo letto dalla riga di comando. */
	wt_sgombra_soglia(sgombra_soglia_ms);

	/* ⛔⭐⭐ E IL REGOLATORE DEL RITMO SUBITO DOPO, E L'ORDINE NON E' UN CASO.
	 *
	 *      `wt_ritmo_adattivo()` scrive la sua riga d'avvio guardando la soglia
	 *      GIA' IN VIGORE: se e' spenta, dichiara che il regolatore non potra'
	 *      mai scattare — l'arretrato non supera 1 e i posti sono 2.  Invertire
	 *      le due chiamate farebbe leggere zero, e quella riga direbbe il falso
	 *      proprio nel giro in cui serve.
	 *
	 * ⛔ E la riga esce ACCESO E SPENTO che sia, come per la soglia e per la
	 *    stessa ragione: un regolatore spento e un regolatore che non ha mai
	 *    dovuto scattare producono lo stesso registro, cioe' nessuna riga. */
	wt_ritmo_adattivo(ritmo_adattivo);

	/* ⛔ §4.4-bis: «il ban sopravvive al riavvio», ed e' l'invariante I7 — la
	 *    protezione di un difetto noto sta nel programma, non in una riga di
	 *    configurazione che si puo' perdere. */
	{
		int n = rcp_ban_carica(file_ban, registro_ora_ms());
		if (n < 0) {
			/* ⛔ «zero ban» e «non ho potuto guardare» sono due fatti
			 *    diversi (`rcp.h`, `LEZIONI.md` §1.9 regola 1): il
			 *    secondo e' la protezione spenta con l'aria di non avere
			 *    niente da proteggere, cioe' l'invariante I7 rotta in
			 *    silenzio.  Non si parte. */
			registro_dice(REG_AVVIO,
			              "⛔ il file dei ban %s c'e' e NON si e' potuto "
			              "leggere: non e' «zero ban», e' la protezione di "
			              "§4.4-bis spenta.  Non si parte.",
			              file_ban);
			return 1;
		}
		registro_dice(REG_AVVIO, "ban: %s, %d indirizzi caricati", file_ban, n);
	}

	/* ⭐ «Come si esce: le 12 ore che passano, oppure un comando di sblocco sul
	 *    server — che chiede l'accesso alla macchina, cioe' l'unica chiave che
	 *    quel caso ammette» (`SPECIFICHE.md` §4.2, `RCP.md` §4.4-bis).  ⛔ E il
	 *    comando parla col processo VIVO, che e' l'unico che ha in mano la
	 *    tabella dei ban: vedi il riquadro di `comando.h`, rilievo R12.1.
	 *
	 * ⚠ `comando_apri()` restituisce NULL anche quando il socket non e' stato
	 *   chiesto, e in tutt'e due i casi scrive PERCHE': il server va avanti,
	 *   perche' senza comando la protezione di §4.4-bis c'e' ancora — si esce
	 *   solo con le dodici ore. */
	/* ⛔⭐ L'AIUTANTE SI ACCENDE QUI, E IL «QUI» E' MEZZA CURA — §1.10.
	 *
	 *     Un `fork()` regala al figlio tutti i descrittori aperti.  ⛔ Acceso
	 *     dopo `trasporto_apri()` o `pagina_apri()`, l'aiutante si porterebbe
	 *     dietro il socket UDP e l'ascoltatore TCP della 7447: il server
	 *     muore, la porta resta occupata da un processo che non la usa, e chi
	 *     riavvia legge «indirizzo gia' in uso» senza vedere nessun server.
	 *     ⚠ E' la forma di difetto peggiore — il sintomo non nomina la causa.
	 *
	 * ⭐ Acceso qui eredita: i tre descrittori standard e il file dei ban, che
	 *    e' gia' chiuso.  E NON eredita il socket del comando di sblocco, che
	 *    si apre nella riga sotto.
	 *
	 * ⚠ E se non si accende, il server parte lo stesso e lo dice: senza
	 *   aiutante ogni autenticazione e' un NO (invariante I3), il che e'
	 *   sgradevole ma e' la direzione giusta in cui sbagliare. */
	/* ⛔⭐ E IL PALCO NON SI PRENDE PIU' QUI — §1.10-bis, 12 agosto 2026.
	 *
	 *     Fino a ieri, in questo punto, il server chiamava `sessione_assicura()`
	 *     e `primo_fotogramma()`: prendeva **la sessione grafica dentro cui
	 *     girava lui**, e la mostrava a chiunque entrasse.  ⛔ `[M]` sulla
	 *     macchina di prova il server girava come `nicfio` e l'utente entrava
	 *     come `prova`: quel che si vedeva nella scheda era il desktop di
	 *     `nicfio` — cioe' il palco era del PROCESSO, non dell'utente.
	 *
	 * ⇒ Adesso il palco e' del **figlio**, che nasce quando PAM dice si' e gira
	 *   come quell'utente (`figlio.h`).  ⚠ La tabella si accende qui perche'
	 *   `consegna_verdetto()` la vuole gia' pronta; i figli, no: quelli nascono
	 *   uno per utente ammesso.
	 *
	 * ⚠ E il ripiego si DICHIARA (`CODER.md` §4.2): se la tabella non si accende
	 *   il server parte lo stesso — pagina e autenticazione funzionano — e
	 *   nessuno vede un pixel. */
	pam_aiuto = aiutante_accendi();
	if (!pam_aiuto)
		registro_dice(REG_AVVIO,
		              "⛔ nessun aiutante di PAM: si ripiega sulla verifica "
		              "SINCRONA, che ferma il ciclo per 1-2 s a ogni tentativo "
		              "(DECISIONI.md §1.10).  Il ripiego e' dichiarato, non "
		              "silenzioso (CODER.md §4.2).");

	prole = figli_accendi(TELA_L, TELA_A, dir_rilievo, deposita_fotogramma,
	                      congeda_figlio, cursore_dal_palco, tela_dal_palco,
	                      NULL);
	if (!prole)
		registro_dice(REG_AVVIO,
		              "⛔ la tabella dei figli non si accende: NESSUN utente "
		              "avra' un palco, e la fase 2 non ha oggetto.  Il server "
		              "parte lo stesso (la fase 1 funziona), e il perche' e' "
		              "nella riga qui sopra");
	/* ⛔⭐⭐ LE DUE CURE CHE VIVONO NEL FIGLIO — e questa riga e' l'unica che
	 *      le fa esistere.  ⚠ Qui NON si accende niente: si consegna alla
	 *      tabella dei figli quel che ogni figlio dovra' ripetere a se stesso
	 *      dopo l'`execve`, perche' il codificatore sta di la' e questo
	 *      processo non lo apre mai.  ⛔ E chi dichiarera' il valore in vigore
	 *      sara' `codificatore.c`, all'apertura di ogni codificatore: se
	 *      l'opzione si perdesse per strada, quelle righe direbbero «spento»
	 *      e il difetto si vedrebbe subito (forma D5). */
	figli_fase9(prole, qualita_risale, tetto_banda_mbit);

	/* ⛔ Chi possiede questo processo, scritto una volta e non dedotto dal
	 *    lettore: da qui dipende se i figli potranno DAVVERO scendere a un
	 *    altro utente.  ⚠ Un server non privilegiato genera figli che restano
	 *    lui — `setuid()` fallisce, e `figli_assicura()` lo dichiara. */
	registro_dice(REG_AVVIO,
	              "%s questo processo e' uid %ld: %s",
	              geteuid() == 0 ? "⭐" : "⚠", (long)geteuid(),
	              geteuid() == 0
	                      ? "puo' verificare con PAM la parola di chiunque e "
	                        "far scendere i figli all'utente giusto "
	                        "(DECISIONI.md §1.10-bis)"
	                      : "NON e' root — PAM potra' verificare solo il suo "
	                        "utente, e un figlio potra' nascere solo per lui");

	k = comando_apri(socket_comando);

	guarda_il_servizio_pam();

	if (!certificati_prepara(&cert, dir_cert, nome))
		goto fine;

	ctx_quic = tls_contesto_quic(cert.sessione_pem, cert.sessione_key);
	ctx_pagina = tls_contesto_pagina(cert.pagina_pem, cert.pagina_key);
	if (!ctx_quic || !ctx_pagina)
		goto fine;

	t = trasporto_apri(indirizzo, porta, ctx_quic, pam_aiuto);
	if (!t)
		goto fine;
	ponte.t = t;
	ponte.f = prole;
	/* ⛔ Il gancio si collega QUI, dopo che la tabella dei figli c'e' e prima
	 *    che il primo pacchetto arrivi: collegarlo dopo lascerebbe la prima
	 *    sessione senza la richiesta della sua chiave, cioe' con lo schermo
	 *    fermo e nessuna riga che dica perche'. */
	wt_video_gancio(video_chiedi, &ponte);
	wt_audio_gancio(audio_chiedi, &ponte);
	/* ⭐ E con lui quello dell'input, per la stessa ragione e nello stesso
	 *    istante: collegarlo dopo lascerebbe la prima sessione con un desktop
	 *    che si vede e non si comanda, e nessuna riga che dica perche'. */
	wt_input_gancio(input_al_figlio, &ponte);
	/* ⭐⭐ E quello della TELA, nello stesso istante e per una ragione in piu':
	 *     il client chiede la sua misura **all'attacco**, cioe' nel primo mezzo
	 *     secondo di ogni sessione.  Un gancio collegato dopo il primo pacchetto
	 *     farebbe rispondere `COMPOSITORE_INCAPACE` proprio alla richiesta che
	 *     conta — e il client mostrerebbe «adatta il desktop» come spento su un
	 *     server che sa farlo. */
	wt_ritela_gancio(ritela_al_figlio, &ponte);
	wt_disposizione_gancio(disposizione_al_figlio, &ponte);

	/* ⭐⭐ §5.1 — IL GUARDIANO DELLE SESSIONI LOCALI, e si collega PRIMA della
	 *     pagina per la stessa ragione degli altri: la domanda `0x05` si fa
	 *     all'`ATTACCA`, cioe' nel primo mezzo secondo di ogni sessione.  Un
	 *     gancio collegato dopo il primo pacchetto lascerebbe entrare
	 *     **proprio** la sessione che questa regola deve tenere fuori.
	 *
	 * ⛔ E se logind non c'e', `sentinella_apri()` ha gia' scritto nel registro
	 *    che la regola NON e' in vigore: qui non si collega niente, e `rcp.c`
	 *    lo dira' a ogni attacco.  ⚠ Non e' un motivo per non partire — I1: una
	 *    sessione senza una regola vale piu' di nessuna sessione. */
	guardiano = sentinella_apri();
	if (guardiano)
		wt_locale_gancio(chiedi_sessione_locale, guardiano);

	/* ⭐ §7.6 — e si collega qui con gli altri: la scorciatoia `Ctrl+Alt+Fine`
	 *    puo' arrivare col primo pacchetto utile della sessione, e un gancio
	 *    collegato dopo lascerebbe l'utente a premere una combinazione che non
	 *    fa niente — che e' peggio di non averla. */
	wt_termina_gancio(termina_al_figlio, &ponte);
	/* ⭐ E il gemello: il fatto che arriva dal desktop invece che dal filo. */
	figli_gancio_sessione_finita(prole, sessione_finita_dal_figlio, &ponte);
	figli_gancio_tela_attendi(prole, tela_attendi_dal_figlio, &ponte);
	/* ⭐ FASE 7: i blocchi d'audio salgono di qui.  ⚠ DOPO `figli_accendi`,
	 *    come tutti gli altri ganci: prima non c'e' una tabella a cui
	 *    agganciarli. */
	figli_gancio_blocco(prole, audio_blocco, NULL);
	/* ⭐⭐ FASE 7 — GLI APPUNTI, nei due versi, e i due ganci si agganciano
	 *     insieme: `webtransport.c` non collega il canale se ne manca uno, e
	 *     `figli_gancio_appunti` rifiuta di agganciarne uno solo.  ⚠ Meta'
	 *     canale l'utente la vede come «gli appunti non funzionano», che e' la
	 *     stessa faccia di «gli appunti non ci sono». */
	wt_appunti_gancio(appunti_offri_al_figlio, appunti_risposta_al_figlio,
	                  &ponte);
	figli_gancio_appunti(prole, appunti_dalla_sessione,
	                     appunti_richiesta_dalla_sessione, &ponte);

	p = pagina_apri(indirizzo, porta, ctx_pagina, file_html, &cert);
	if (!p)
		goto fine;

	registro_dice(REG_AVVIO,
	              "⭐ pronto: https://%s:%s  —  la sessione WebTransport vive "
	              "su /rcp/1 (RCP.md §2.2)",
	              nome, porta);

	ultimo_controllo_cert = time(NULL);

	while (!si_ferma) {
		struct pollfd fds[MAX_POLL];
		size_t n = 0, npagina, ncomando, naiuto, nfigli;
		uint64_t adesso;
		int attesa;

		fds[n].fd = trasporto_fd(t);
		fds[n].events = POLLIN;
		fds[n].revents = 0;
		n++;

		npagina = pagina_descrittori(p, fds + n, MAX_POLL - n);
		ncomando = comando_descrittori(k, fds + n + npagina,
		                               MAX_POLL - n - npagina);

		/* ⭐ L'aiutante di PAM entra nel `poll` come tutti gli altri, ed e'
		 *    tutto quel che serve perche' il ciclo non aspetti piu' nessuno
		 *    (`DECISIONI.md` §1.10).  ⛔ In coda, dopo la pagina e il comando,
		 *    perche' i loro conti sono relativi e infilarlo in mezzo
		 *    sposterebbe gli indici di due chiamate. */
		naiuto = 0;
		if (aiutante_descrittore(pam_aiuto) >= 0
		    && n + npagina + ncomando < MAX_POLL) {
			size_t i = n + npagina + ncomando;
			fds[i].fd = aiutante_descrittore(pam_aiuto);
			fds[i].events = POLLIN;
			fds[i].revents = 0;
			naiuto = 1;
		}

		/* ⭐ E i figli dopo l'aiutante, per la stessa ragione: i conti di chi
		 *    sta prima sono relativi, e infilarli in mezzo sposterebbe gli
		 *    indici di tre chiamate.  ⛔ E sono l'ultimo blocco anche per una
		 *    ragione di verita': se `MAX_POLL` finisse, a restare fuori sono i
		 *    figli — cioe' il video — e non la pagina o l'autenticazione.  Una
		 *    sessione brutta vale piu' di una sessione chiusa (invariante I1). */
		nfigli = figli_descrittori(prole, fds + n + npagina + ncomando + naiuto,
		                           MAX_POLL - n - npagina - ncomando - naiuto);

		attesa = trasporto_attesa_ms(t);
		if (attesa < 0 || attesa > 1000)
			attesa = 1000;
		/* ⛔ Col tono di prova acceso il ciclo si sveglia ogni 10 ms, perche' i
		 *    blocchi li genera `wt_batti()` e con un'attesa da un secondo ne
		 *    uscirebbero cinquanta in un colpo — cioe' una raffica che la coda
		 *    dei datagram butterebbe, e il registro direbbe «buttati» per un
		 *    difetto fabbricato dal banco.
		 * ⚠ NON serve all'audio vero: quello lo ritma PipeWire, che nel `poll`
		 *   ci sta con un descrittore suo.  ⇒ Questa riga muore con la
		 *   sorgente di prova, e non e' un debito nascosto. */
		if (audio_prova_hz && attesa > 10)
			attesa = 10;

		if (poll(fds, n + npagina + ncomando + naiuto + nfigli, attesa) < 0) {
			if (errno == EINTR)
				continue;
			registro_dice(REG_AVVIO, "⛔ poll: %s", strerror(errno));
			break;
		}

		if (fds[0].revents & POLLIN)
			trasporto_leggi(t);
		/* ⛔ Le risposte di PAM PRIMA di `trasporto_scaduti()`: il verdetto
		 *    puo' rendere maturo un `AMMESSO`, e consegnarlo dopo aggiungerebbe
		 *    un giro di ciclo a chi si autentica — cioe' peggiorerebbe proprio
		 *    il numero che questa cura non deve toccare.
		 * ⚠ E si chiama anche quando il descrittore NON e' leggibile: e' li'
		 *   dentro che le pratiche scadono, e una scadenza che aspetta un byte
		 *   e' una scadenza che non scatta mai — proprio nel caso per cui e'
		 *   stata scritta (la lezione di `regola_battito`, pagata l'11 agosto
		 *   con B6). */
		adesso = registro_ora_ms();
		/* ⛔ §5.3, il terzo orologio: si guarda a OGNI passata, non quando
		 *    arriva qualcosa.  Il caso che conta e' proprio quello in cui non
		 *    arriva piu' niente. */
		abbandono_giro(&ponte, adesso);
		if (naiuto && (fds[n + npagina + ncomando].revents & POLLIN))
			aiutante_muovi(pam_aiuto, consegna_verdetto, &ponte);
		aiutante_scaduti(pam_aiuto, adesso, consegna_verdetto, &ponte);
		/* ⛔ I figli PRIMA di `trasporto_scaduti()`, e per lo stesso motivo per
		 *    cui ci stanno le risposte di PAM: un fotogramma appena arrivato dal
		 *    palco puo' entrare in deposito **in questo giro**, e rimandarlo al
		 *    prossimo costerebbe un giro intero a chi sta aspettando di vedere
		 *    il proprio desktop.
		 * ⚠ E si chiama SEMPRE, anche quando nessun figlio e' leggibile: qui
		 *   dentro si raccolgono i morti (`waitpid(WNOHANG)`) e scadono le
		 *   presentazioni, e una scadenza che aspetta un byte non scatta mai. */
		figli_muovi(prole, fds + n + npagina + ncomando + naiuto, nfigli, adesso);
		figli_ricontrolla(prole, adesso);
		trasporto_scaduti(t);
		pagina_muovi(p, fds + 1, npagina);
		comando_muovi(k, fds + 1 + npagina, ncomando);

		/* ⛔ LA ROTAZIONE, e si guarda una volta al minuto invece che a
		 *    ogni giro: «prima che scada», non «quando e' scaduto»
		 *    (§4.1-bis).  ⚠ Un minuto e' abbondante per un margine di due
		 *    giorni, e non costa niente. */
		/* ⭐⭐ §5.1 — IL RIPASSO DELLE SESSIONI LOCALI, ogni RIPASSO_LOCALI_MS.
		 *
		 * ⛔ Non e' l'`ATTACCA`: quella domanda la fa `rcp.c` una volta e
		 *    basta.  Questa e' l'altra meta' della regola — «apre una sessione
		 *    LOCALE mentre la remota e' viva» — e non la chiede nessuno: o la
		 *    si guarda, o `0x04` resta un codice che nessuno spedisce.
		 *
		 * ⚠ Due secondi e non ogni giro: la domanda costa una chiamata sincrona
		 *   a logind, e questo e' lo stesso ciclo che consegna i fotogrammi
		 *   (`LEZIONI.md` §6.2-bis).  ⚠ E due secondi sono il ritardo massimo
		 *   fra «l'utente si e' seduto davanti alla macchina» e «la sessione
		 *   remota cade»: e' un'attesa che nessuno guarda col cronometro. */
		if (guardiano && adesso - ultimo_ripasso_locali >= RIPASSO_LOCALI_MS) {
			ultimo_ripasso_locali = adesso;
			wt_sorveglia_locali();
		}

		if (time(NULL) - ultimo_controllo_cert >= 60) {
			ultimo_controllo_cert = time(NULL);
			if (certificati_ruota_se_serve(&cert)) {
				SSL_CTX *nuovo =
					tls_contesto_quic(cert.sessione_pem, cert.sessione_key);
				if (nuovo) {
					/* ⚠ Le connessioni gia' aperte tengono il vecchio
					 *   contesto: TLS e' gia' fatto, e cambiarlo sotto
					 *   non ha senso.  ⛔ Le NUOVE prendono questo, e
					 *   la pagina pubblica gia' l'impronta nuova. */
					trasporto_contesto(t, nuovo);
					SSL_CTX_free(ctx_quic);
					ctx_quic = nuovo;
					registro_dice(REG_CERT,
					              "⭐ il contesto QUIC usa il certificato "
					              "ruotato; la pagina pubblica gia' la "
					              "nuova impronta e /impronta la serve");
				} else {
					registro_dice(REG_CERT,
					              "⛔ certificato ruotato ma il contesto "
					              "TLS non si rifa': le nuove sessioni "
					              "userebbero un certificato di cui la "
					              "pagina non pubblica l'impronta");
				}
			}
		}
	}

	registro_dice(REG_AVVIO, "chiusura richiesta: %zu connessioni QUIC vive",
	              trasporto_quante(t));

	/* ⛔⭐ E CHI CHIUDE LO DICE — §8.1, §8.2 motivo `0x0C SERVER_IN_CHIUSURA`.
	 *     Rilievo B-7, 10 agosto 2026 notte.
	 *
	 *     Prima di stanotte qui il ciclo usciva e `trasporto_chiudi()` liberava
	 *     tutto: nessun `CONGEDO`, nessun codice di chiusura, nemmeno un
	 *     `CONNECTION_CLOSE`.  Chi era collegato aspettava trenta secondi e
	 *     leggeva «errore di rete» — il difetto di `LEZIONI.md` §1.7 che §3.1
	 *     esiste per togliere, e qui il server non scriveva nemmeno «congedo».
	 *
	 * ⛔ E si ASPETTA che i byte escano, invece di contare i giri: la capsula di
	 *    §3.1 punto 3 matura mezzo secondo dopo che la coda si e' svuotata
	 *    (vedi `wt_batti`), quindi uscire subito sarebbe scrivere il congedo e
	 *    buttarlo.  ⚠ Ma l'attesa ha un fondo — due secondi — o un client che
	 *    non legge piu' terrebbe in piedi lo spegnimento del servizio.  ⛔ La
	 *    rinuncia si scrive: chi spegne deve poter distinguere «l'hanno saputo
	 *    tutti» da «non ho fatto in tempo». */
	{
		size_t restano = trasporto_congeda_tutte(
			t, RCP_SERVER_IN_CHIUSURA, "il server si sta spegnendo");
		int giri = 0;
		/* ⛔⭐ IL BUDGET SI CONTA IN TEMPO, NON IN GIRI — e l'11 agosto 2026
		 *     e' stato misurato che la differenza e' di un fattore quattordici.
		 *
		 *     Qui c'era `giri < 200`, con accanto scritto «due secondi»: il
		 *     conto assumeva che ogni giro costasse i 10 ms del `poll`.  ⛔ Ma
		 *     `poll` ritorna SUBITO quando c'e' qualcosa da leggere, e allo
		 *     spegnimento c'e' sempre qualcosa: **400 giri sono durati 293 ms**
		 *     — letto nel registro del server, 08:17:08.756 → 08:17:09.049.
		 *
		 * ⛔ Da cui il difetto vero: `chiudi_sessione()` arma un fondo di
		 *    sicurezza a **3 s** per la capsula di §3.1 punto 3, e chi spegne
		 *    rinunciava dopo tre decimi.  La rete di sicurezza esisteva e non
		 *    poteva scattare **proprio nel momento per cui era stata scritta**.
		 *
		 * ⚠ E un contatore di giri che si crede un orologio non sbaglia di
		 *   poco: sbaglia di quanto e' veloce la macchina, cioe' di un numero
		 *   che cambia da un ferro all'altro.  E' la forma peggiore, perche' il
		 *   banco resta verde dove il ferro e' lento. */
		struct timespec t0, tn;
		clock_gettime(CLOCK_MONOTONIC, &t0);
		while (restano > 0) {
			clock_gettime(CLOCK_MONOTONIC, &tn);
			{
				long long trascorsi =
				    (long long)(tn.tv_sec - t0.tv_sec) * 1000
				    + (tn.tv_nsec - t0.tv_nsec) / 1000000;
				if (trascorsi >= 4000)
					break;
			}
			struct pollfd fds[MAX_POLL];
			int attesa = trasporto_attesa_ms(t);
			fds[0].fd = trasporto_fd(t);
			fds[0].events = POLLIN;
			fds[0].revents = 0;
			if (attesa < 0 || attesa > 10)
				attesa = 10;
			if (poll(fds, 1, attesa) > 0 && (fds[0].revents & POLLIN))
				trasporto_leggi(t);
			trasporto_scaduti(t);
			restano = trasporto_congeda_tutte(t, RCP_SERVER_IN_CHIUSURA,
			                                  "il server si sta spegnendo");
			giri++;
		}
		/* ⛔⭐ E POI SI ASPETTA ANCORA — misurato dal banco B7 l'11 agosto 2026,
		 *     caso `server-in-chiusura`, ed e' il difetto che il caso e' nato
		 *     per trovare.
		 *
		 *     `wt_ha_da_dire()` diventa falsa quando la capsula di chiusura di
		 *     §3.1 punto 3 e' stata CONSEGNATA A NGTCP2.  ⛔ Ma «consegnato a
		 *     ngtcp2» non e' «uscito sul filo» — e' la stessa distinzione che
		 *     `wt_batti` fa per il `CONGEDO`, curata li' e non qui.  Il ciclo
		 *     usciva, `trasporto_chiudi()` abbatteva QUIC, e quei byte non
		 *     partivano piu'.
		 *
		 * ⛔ Che cosa vedeva il client, misurato: il `CONGEDO 0x0c` arrivava
		 *    sul canale, e la sessione si chiudeva **senza codice** — QUIC
		 *    terminato con `codice 0 · nessun motivo`.  Cioe' la SECONDA
		 *    strada di §3.1 mancava.
		 *
		 * ⚠ E la seconda strada e' quella che conta: `DECISIONI.md` §7.14 e
		 *   §7.15, decise oggi, la rendono l'unica che arrivi sempre — su
		 *   Firefox, che azzera il canale e butta quei byte, era l'UNICA.
		 *   Un utente di Firefox avrebbe visto il servizio sparire **senza
		 *   nessun motivo**, che e' esattamente cio' che §8.1 vieta.
		 *
		 * ⭐ Mezzo secondo, e si scrive quanto si e' aspettato: la cura non
		 *    deve poter diventare «aspetta e spera» senza che nessuno lo veda. */
		if (restano == 0) {
			int coda = 0;
			while (coda < 50) {
				struct pollfd fds[MAX_POLL];
				fds[0].fd = trasporto_fd(t);
				fds[0].events = POLLIN;
				fds[0].revents = 0;
				if (poll(fds, 1, 10) > 0 && (fds[0].revents & POLLIN))
					trasporto_leggi(t);
				trasporto_scaduti(t);
				coda++;
			}
			registro_dice(REG_AVVIO,
			              "⭐ congedo 0x0c mandato a tutte le sessioni e uscito "
			              "sul filo in %d giri, piu' %d giri di coda perche' la "
			              "capsula di chiusura (§3.1 punto 3) esca davvero "
			              "(§8.1: mai con un silenzio)",
			              giri, coda);
		}
		else
			registro_dice(REG_AVVIO,
			              "⛔ %zu sessioni non hanno finito dopo 4 s (%d giri) — "
			              "«%s».  Il congedo 0x0c e' stato scritto ma non e' "
			              "detto che sia uscito, e ⛔ §3.1 punto 3 — il motivo "
			              "nel codice di chiusura — potrebbe non essere "
			              "partito affatto.  Si chiude lo stesso. "
			              "⚠ B7 `server-in-chiusura` misura esattamente questo.",
			              restano, giri, trasporto_perche_restano(t));
	}
	esito = 0;

fine:
	/* ⛔ L'aiutante si spegne per primo: da qui in poi non c'e' piu' nessuno a
	 *    cui consegnare un verdetto, e un figlio che scrive su un socket che
	 *    nessuno legge e' un processo che resta.  ⚠ E `aiutante_spegni()`
	 *    ASPETTA il figlio — ma fuori dal ciclo asincrono, che e' gia' finito:
	 *    `CODER.md` §4.4 vieta l'attesa DENTRO il ciclo, e questa e' la riga
	 *    dopo l'ultimo giro. */
	aiutante_spegni(pam_aiuto);
	/* ⚠ Il guardiano prima della pagina e del trasporto: da qui in poi nessuno
	 *   fa piu' domande su chi e' collegato, e tenere aperto un bus di sistema
	 *   mentre si chiude non serve a niente. */
	sentinella_chiudi(guardiano);
	comando_chiudi(k);
	pagina_chiudi(p);
	trasporto_chiudi(t);
	/* ⛔ I figli si spengono DOPO il trasporto: finche' una connessione e' viva
	 *    puo' esserci un fotogramma in coda, e i suoi byte stanno nel deposito.
	 * ⚠ E si spengono all'uscita del PROCESSO, non a quella di una connessione:
	 *   e' l'invariante I4 — il palco appartiene alla sessione, e chi muore
	 *   quando cade la rete non e' lui.  ⛔ `figli_spegni()` ASPETTA che siano
	 *   morti, perche' il monitor virtuale sparisce quando sparisce il
	 *   consumatore: uscire prima lascerebbe un monitor attaccato alla sessione
	 *   dell'utente senza nessuno che lo guardi. */
	figli_spegni(prole);
	if (ctx_quic)
		SSL_CTX_free(ctx_quic);
	if (ctx_pagina)
		SSL_CTX_free(ctx_pagina);
	return esito;
}
