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
 *   la chiave ne' il codificatore. */
static void video_chiedi(void *ctx, const char *utente, uint8_t codec,
                         bool chiave)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return;
	figli_video(p->f, utente, codec, chiave);
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
static bool input_al_figlio(void *ctx, const char *utente, uint32_t id,
                            uint8_t azione, uint16_t codice, int premuto,
                            int32_t a, int32_t b)
{
	struct ponte *p = (struct ponte *)ctx;
	if (!p || !p->f)
		return false;
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
}

/* ⭐⭐ LA RISPOSTA DEL PALCO SULLA TELA — §7.1, e attraversa il confine nel verso
 *     del cursore: la domanda e' uscita con `figli_ritela()`, questa rientra.
 *
 * ⛔ E il padre non la INDOVINA piu' dai fotogrammi: il figlio dice a quale
 *    richiesta risponde (`voluta`) e che cosa il palco ha davvero (`avuta`, con
 *    `0x0` = non ce l'ha fatta).  ⚠ Senza, due `ADATTA_TELA` incatenate — un
 *    utente che trascina il bordo — facevano prendere il fotogramma della prima
 *    per la risposta della seconda. */
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
	time_t ultimo_controllo_cert;
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
