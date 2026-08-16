/*
 * rcp.c — la stretta di mano di RCP/1, lato server.
 *
 * Le regole che seguono hanno tutte un numero di paragrafo accanto: chi le
 * cambia deve cambiare `RCP.md` per primo, o i due si separano in silenzio.
 */
#include "rcp.h"

#include <errno.h> /* §4.4-bis: «non c'e' ancora nessun file» e «non ho potuto
                    * leggerlo» sono due fatti diversi, e a distinguerli e' il
                    * solo `errno` (`LEZIONI.md` §1.9 regola 1) */
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h> /* §4.4-bis: il file dei ban porta un'ora ASSOLUTA,
                    * perche' `ora` e' monotona e riparte a ogni processo */

/* ------------------------------------------------------------------------ */
/* I tipi del canale di controllo — §7.1                                     */
enum {
	T_CIAO = 0x0001,
	T_ECCOMI = 0x0002,
	T_CREDENZIALI = 0x0003,
	T_AMMESSO = 0x0004,
	T_RESPINTO = 0x0005,
	T_ATTACCA = 0x0006,
	T_SESSIONE = 0x0007,
	/* §7.2 — la FORMA del cursore, server → client, sul canale di controllo
	 * (§5).  ⚠ La POSIZIONE non viaggia mai in questo verso: e' del client, che
	 * disegna il puntatore da se' (`SPECIFICHE.md` §7.1). */
	T_CURSORE_FORMA = 0x000A,
	T_CONGEDO = 0x000C,
	/* ⭐ §5.2, §7.1: «il client chiede una chiave».  Servito dal 12 agosto
	 * 2026, insieme al canale video: finche' il video non c'era, questo tipo
	 * cadeva nel `default` e faceva **perdere la sessione** a un client
	 * conforme che avesse visto un buco — il prezzo che il registro dichiarava
	 * («la fase 1 non lo serve ancora»). */
	T_RICHIEDI_CHIAVE = 0x000D,
	/* ⭐ §7.6, 15 agosto 2026: «l'utente vuole uscire».  ⛔ Non e' il
	 * `CONGEDO`, che lascia la sessione viva: questo la FINISCE. */
	T_TERMINA_SESSIONE = 0x0011,
	/* ⭐ §7.1 — «il client chiede una tela di un'altra misura», e la risposta
	 * `TELA` che ne dichiara l'esito.  ⛔ Serviti dal 14 agosto 2026: prima
	 * `ADATTA_TELA` cadeva nel `default` e faceva **perdere la sessione** a un
	 * client conforme, e `TELA` non veniva spedito **da nessuna riga** —
	 * `rcp_tela_adattata_ora()` cambiava lo stato e scriveva nel registro, ma sul
	 * filo non usciva niente.  E' la coppia che `DECISIONI.md` §5.0-sexies
	 * accende. */
	T_ADATTA_TELA = 0x000B,
	T_TELA = 0x000E,
	T_BANCO_MARCA = 0x000F,
	T_BANCO_ESITO = 0x0010,
};

/* ------------------------------------------------------------------------ */
/* ⭐ I TIPI DEL CANALE DI INPUT — §7.3, e il byte alto e' 0x01 (§2.5)        */
enum {
	T_PUNTATORE = 0x0101,
	T_PULSANTE = 0x0102,
	T_ROTELLA = 0x0103,
	T_LETTERA = 0x0104,
	T_POSIZIONE_TASTO = 0x0105,
};

/* ⛔ QUANTO OCCUPA IL CORPO DI CIASCUNO — §7.3, e i due campi comuni davanti.
 *
 *   u32 id + u64 istante                              = 12  (tutti)
 *   PUNTATORE       + u32 x + u32 y                   = 20
 *   PULSANTE        + u16 codice + u8 premuto         = 15
 *   ROTELLA         + i32 asse_x + i32 asse_y         = 20
 *   LETTERA         + u32 carattere                   = 16
 *   POSIZIONE_TASTO + u16 codice + u8 premuto         = 15
 *
 * ⛔ §6.0: nessun campo e' allineato e nessun riempimento e' ammesso — quindi
 *    15 e' quindici, non sedici.  E' esattamente la forma del difetto corretto
 *    in §6.2 il 9 agosto 2026 (i «quattro byte che fanno tornare i conti»), e
 *    su un messaggio di quindici byte una `struct` C ne conterebbe sedici su
 *    ogni compilatore che questo progetto usa. */
#define I_COMUNI 12u
#define I_PUNTATORE (I_COMUNI + 8u)
#define I_PULSANTE (I_COMUNI + 3u)
#define I_ROTELLA (I_COMUNI + 8u)
#define I_LETTERA (I_COMUNI + 4u)
#define I_POSIZIONE (I_COMUNI + 3u)

/* ⛔⭐ L'ACCUMULO DELL'INPUT E' PICCOLO **PER COSTRUZIONE**, e non e' una
 *     scorciatoia: e' §6.1 applicata prima di allocare, portata all'estremo che
 *     questo canale permette.
 *
 *     Sul canale di controllo la lunghezza dichiarata si puo' conoscere solo
 *     leggendo il corpo (le capacita' di `CIAO` sono un elenco), quindi
 *     l'accumulo cresce fino a 1 MiB.  ⛔ Qui no: i cinque tipi di §7.3 hanno
 *     tutti una lunghezza FISSA e nota dal solo `tipo`.  ⇒ Appena i sei byte
 *     dell'intestazione sono arrivati si sa gia' se la lunghezza e' quella
 *     giusta, e una lunghezza sbagliata e' `ERRORE_PROTOCOLLO` PRIMA che un
 *     solo byte di corpo venga accumulato (§6.1: «la lunghezza si controlla
 *     prima di allocare»).
 *
 * ⭐ Da cui: 6 + 20 = 26 byte bastano per sempre, e stanno nella sessione senza
 *    una `malloc`.  Chi annuncia un megabyte su questo stream non ottiene un
 *    megabyte: ottiene un congedo dopo sei byte. */
#define I_ACCUMULO 32u

/* §7.1 — il secondo di grazia dopo un cambio di tela, in millisecondi.
 * ⚠ Il confronto e' `<=`: «per un secondo» comprende il millesimo 1000. */
#define TELA_GRAZIA 1000

/* §7.5 — l'esito della funzione di banco. */
enum {
	BANCO_ACCETTATA = 1,
	BANCO_RIFIUTATA = 2,
	BANCO_FUNZIONE_SPENTA = 1,
	BANCO_RITARDO_FUORI_LIMITI = 2,
};

/* ⛔ §7.5 regola 1: la funzione di banco e' SPENTA salvo che l'amministratore
 * non l'accenda — invariante I6, e qui letteralmente dipinge sopra il desktop
 * di qualcuno.  In fase 1 non esiste ancora una configurazione, quindi e'
 * spenta e basta: e' lo stato predefinito di ogni server, ed e' quello che B5
 * mette alla prova. */
#define BANCO_ACCESO 0
/* §7.5 regola 4: `ritardo_ms` DEVE stare fra 0 e 10 000. */
#define BANCO_RITARDO_MAX 10000

/* I tetti di §4.6, in millisecondi. */
#define TETTO_CIAO 5000
#define TETTO_CREDENZIALI 60000
/* ⛔ DIECI secondi, non sessanta — rilievo R9.9, 10 agosto 2026.
 *
 * §4.6, tabella, terza riga: «`AMMESSO` spedito → `ATTACCA` ricevuto → 10 s».
 * Qui c'era 60 000, cioe' lo stesso numero della riga sopra: la forma del
 * difetto che si copia dalla riga precedente e non si rilegge.
 *
 * ⚠ Il tetto esiste perche' «una connessione che si ferma a meta' stretta di
 *   mano tiene un posto e non lo dichiara a nessuno» (§4.6): a 60 000 quel
 *   posto — quello di §4.4-bis e quello del registro delle sessioni non ancora
 *   preso — si teneva SEI VOLTE piu' a lungo di quel che il documento concede.
 *
 * ⛔ E nessun banco lo vedeva: B6 (i tre tetti) non e' ancora scritto, e in
 *    `01-b5-violazioni.py` non c'e' nessun caso sui tetti.  Il difetto stava
 *    esattamente dove il banco non guarda. */
#define TETTO_ATTACCA 10000
/* §4.4-bis: il ritardo fisso, e vale ANCHE per AMMESSO. */
#define RITARDO_FISSO 1000

/* ⛔⭐ IL TETTO DEL VERDETTO — 12 agosto 2026, `DECISIONI.md` §1.10.
 *
 * Non e' un tetto di `RCP.md` §4.6: quei tre misurano il CLIENT, e questo
 * misura NOI.  ⛔ Esiste perche' dal 12 agosto la risposta di PAM arriva da un
 * altro processo, e un altro processo puo' morire: senza questo numero una
 * sessione resterebbe in `attesa-verdetto` per sempre, cioe' un client appeso
 * a un silenzio — precisamente cio' che §8.1 vieta.
 *
 * ⚠ E' la SECONDA rete, non la prima: l'aiutante ha gia' la sua scadenza a 8 s
 *   (`aiutante.c`).  ⛔ Sono due apposta, e vivono in due processi diversi: la
 *   prima non puo' scattare se a essere guasto e' proprio chi la tiene.
 *   Dodici secondi, cioe' piu' della sua, cosi' nel caso normale il no arriva
 *   da li' — con la sua riga di registro — e questo tetto resta l'ultima
 *   parola invece che la prima.
 *
 * ⛔ E la scadenza vale NO: `cred_buone` non viene toccata, e parte da false. */
#define TETTO_VERDETTO 12000

/* ⛔ L'OROLOGIO DEL SILENZIO — `SPECIFICHE.md` §5.3, `DECISIONI.md` §4.4.
 *
 * Trenta secondi senza un byte DAL CLIENT e il client «si considera staccato»:
 * non occupa piu' il posto, e chi arriva entra.  E' la regola che fa sparire
 * il caso «il telefono e' morto in galleria e ora non posso rientrare».
 *
 * ⛔⛔⭐ E QUI SOTTO C'ERA SCRITTO IL CONTRARIO DI QUEL CHE IL CODICE FA — 16
 *      agosto 2026, corretto insieme alla riparazione dell'orologio.
 *
 *      Diceva: ~~«si misura sui byte di RCP, non su quelli di QUIC: il
 *      trasporto manda riscontri e battiti per conto suo, e un orologio
 *      appoggiato a quelli direbbe "vivo" di un client che non parla da
 *      un'ora»~~.  ⚠ Il timore era vero e va guardato in faccia, non cancellato:
 *      **un client vivo sul filo ma con la pagina morta adesso tiene il posto.**
 *
 * ⭐ Ma la scelta si e' rovesciata su una misura, non su un'opinione: contando i
 *    byte di RCP, **un utente che LEGGEVA perdeva il posto dopo trenta
 *    secondi** — non tocca niente, non manda niente — e un secondo dispositivo
 *    glielo portava via.  `[M]` 16 agosto: `STACCATO per silenzio` a 30013 ms
 *    con la connessione viva, e poi `posto PRESO` da una seconda scheda mentre
 *    la prima guardava.  ⇒ Contare i byte non misurava «il client c'e'»:
 *    misurava «l'utente sta digitando», che e' l'ALTRO orologio di §5.3, quello
 *    da trenta MINUTI.
 *
 * ⭐ E il rilievo R3.19 resta soddisfatto, perche' non si e' appaltato l'orologio
 *    a QUIC: il tetto dei trenta secondi resta NOSTRO, e quel che si guarda e'
 *    l'ultimo pacchetto **decifrato e autenticato** (`ultima_vita`).  Con
 *    `max_idle_timeout` a 120 secondi questo server stacca lo stesso a 30.
 *
 * ⚠ E che cosa succede alla connessione di chi tace, il documento NON lo dice.
 *   Qui si sceglie di **lasciarla aperta** e liberare solo il posto: chiuderla
 *   sarebbe un congedo, e §8.2 non ha un motivo che voglia dire «taci da un
 *   po'».  La scelta e' dichiarata in `fasi/01-filo-nudo.md`, perche' e' un
 *   punto in cui RCP.md ammette due letture. */
#define SILENZIO 30000

/* ⛔⭐ IL SECONDO OROLOGIO DI §5.3 — «inattivita' dell'utente», e fino al 16
 *     agosto 2026 NON ESISTEVA.
 *
 *     `SPECIFICHE.md` §5.3: *«30 minuti senza input ⇒ REMOTIX **stacca** il
 *     client: per rientrare servono utente e password»*, e *«"input" e' quel
 *     che l'utente manda, non quel che guarda: chi resta mezz'ora a guardare un
 *     video senza toccare nulla viene staccato.  Il costo e' piccolo —
 *     riattaccarsi e' rapido»*.  `RCP.md` §8.2 gli da' gia' il motivo `0x02`.
 *
 * ⛔ E `RCP_INATTIVITA = 0x02` stava in `rcp.h` **senza una riga che lo usasse**:
 *    la forma E1, «scritto non e' in vigore».  Un motivo di congedo dichiarato
 *    nel protocollo e mai spedito e' una promessa che un'altra implementazione
 *    avrebbe dovuto gestire per niente.
 *
 * ⭐ QUESTO si misura sui byte di RCP (`ultimo_byte`), ed e' il mestiere per cui
 *    quel campo esiste — liberato lo stesso giorno da quello che non era suo.
 *
 * ⚠ CONFIGURABILE, e §5.3 lo pretende: *«il secondo e il terzo sono
 *   configurabili, con quei valori come predefiniti»*.  ⛔ E il valore in vigore
 *   si SCRIVE nel registro all'avvio: cosi' il numero si legge invece di
 *   aspettarlo mezz'ora — che e' anche l'unico modo di provarlo senza tenere
 *   occupata una macchina. */
#define INATTIVITA_PREDEFINITA 1800000u /* 30 minuti */
static uint64_t inattivita_ms = INATTIVITA_PREDEFINITA;

void rcp_inattivita_imposta(uint64_t ms)
{
	/* ⛔ Zero vuol dire SPENTA, ed e' un valore lecito: chi guarda un video per
	 *    ore su una macchina sua non vuole essere buttato fuori.  ⚠ Si dichiara
	 *    a chi cuce, che lo scrive nel registro. */
	inattivita_ms = ms;
}

uint64_t rcp_inattivita(void) { return inattivita_ms; }

/* ⛔⭐ IL TETTO DI §6.1 E' DEL **MESSAGGIO**, NON DEL CORPO — rilievo B-14,
 *     10 agosto 2026 notte.
 *
 *     §6.1 dice «nessun **messaggio** DEVE superare 1 MiB», e che «messaggio»
 *     comprenda i sei byte d'inquadratura lo stabilisce §5.4, che per gli
 *     appunti sceglie 1 000 000 e non 1 MiB **proprio perche'** «il messaggio
 *     che lo porta ha sei byte di inquadratura e quattro di lunghezza, e un
 *     tetto uguale a quello del messaggio (§6.1) renderebbe illegale il testo
 *     grande esattamente quanto il tetto».
 *
 * ⛔ Fino a stanotte il confronto era `lung > MAX_MESSAGGIO` con `lung` =
 *    lunghezza del **corpo**: un `CIAO` da 1 048 576 byte di corpo era
 *    accettato, cioe' **1 048 582 byte sul filo**, sei oltre il tetto.  ⚠ Sei
 *    byte non fanno danno; le due letture che danno byte diversi per lo stesso
 *    ingresso si': un validatore scritto leggendo §6.1 marcherebbe rosso un
 *    messaggio che questo server accetta, ed e' quel che §0 esiste per
 *    impedire.
 *
 * ⭐ Da qui i due nomi, invece di uno: `MAX_MESSAGGIO` e' il tetto del
 *    documento, `MAX_CORPO` e' quel che ne resta per il corpo.  Il numero del
 *    documento resta scritto una volta sola. */
#define MAX_MESSAGGIO (1024u * 1024u) /* §6.1, INQUADRATURA COMPRESA */
#define MAX_CORPO (MAX_MESSAGGIO - 6u)

/* ⛔ L'ACCUMULO E' IL TETTO DI §6.1, NON UN NUMERO SUO — rilievo R9.13.
 *
 * Qui c'erano 64 KiB, e §6.1 dice «nessun messaggio DEVE superare 1 MiB» —
 * cioe' **fino a 1 MiB e' conforme**.  I due numeri stavano a due righe di
 * distanza e non concordavano: ogni messaggio fra 64 KiB e 1 MiB moriva con
 * `ERRORE_PROTOCOLLO` e il dettaglio «troppi byte in attesa di un corpo»,
 * prima ancora che la sua intestazione venisse guardata.  ⚠ Un `CIAO` con
 * quattrocento capacita' dal nome lecito e sconosciuto (≈ 82 KiB) e' conforme
 * a §6.1 e a §4.3 in ogni sua parte, e §3 eccezione 1 impone di ignorare i
 * nomi sconosciuti e **proseguire**: il server lo congedava.
 *
 * ⚠ E c'era un secondo effetto: il controllo `lung > MAX_MESSAGGIO` era
 *   raggiungibile SOLO dalla lunghezza dichiarata nell'intestazione, mai dai
 *   byte — il tetto di §6.1 non era il tetto di questo server.
 *
 * ⭐ Ma un megabyte per connessione preso all'apertura sarebbe un regalo a chi
 *    apre mille connessioni: il buffer **cresce a richiesta** e solo fino a
 *    questo tetto (vedi `accumula()`).
 *
 * ⚠ E dal 10 agosto 2026 notte vale `MAX_MESSAGGIO` **esatto**, non
 *   `6 + MAX_MESSAGGIO`: il messaggio piu' lungo che questo server accetta e'
 *   di 1 MiB inquadratura compresa (rilievo B-14), quindi non c'e' niente da
 *   accumulare oltre quel numero. */
#define MAX_ACCUMULO MAX_MESSAGGIO

enum stato {
	S_ATTESA_CIAO,
	S_ATTESA_CREDENZIALI,
	S_ATTESA_VERDETTO, /* CREDENZIALI ricevute, il ritardo fisso scorre */
	S_ATTESA_ATTACCA,
	S_ATTIVA,
	/* ⛔ ATTIVA MA SENZA POSTO: ha taciuto trenta secondi — rilievo R9.2.
	 * Lo stato esiste perche' «non occupa piu' il posto» e «e' ancora attiva»
	 * sono due cose diverse, e tenerle sotto la stessa etichetta lasciava DUE
	 * sessioni `attiva` per lo stesso utente — quel che I2 vieta.  Vedi il
	 * riquadro sopra `rcp_tempo()`. */
	S_STACCATA,
	S_FINITA,
};

static const char *NOMI_STATO[] = {"attesa-ciao",   "attesa-credenziali",
                                   "attesa-verdetto", "attesa-attacca",
                                   "attiva", "staccata-per-silenzio",
                                   "finita"};

struct rcp_sessione {
	rcp_ganci g;
	enum stato stato;
	char provenienza[64];
	/* ⛔ L'INDIRIZZO SENZA LA PORTA, e non e' un dettaglio: vedi il riquadro
	 * sopra `rcp_chiave_indirizzo()`. */
	char indirizzo[64];
	char utente[257];
	uint64_t da_quando;   /* quando e' cominciato lo stato corrente */
	/* ⛔⛔⭐ DUE OROLOGI, NON UNO — e fino al 16 agosto 2026 ce n'era uno solo
	 *      che faceva il mestiere di tutt'e due.
	 *
	 *      `SPECIFICHE.md` §5.3 ne tiene DUE, con due significati diversi:
	 *
	 *        · «silenzio del CLIENT», 30 SECONDI — «un client che tace e' un
	 *          client che si e' staccato», e il paragrafo dice perche': *«i 30
	 *          secondi coprono solo le interruzioni vere»*;
	 *        · «inattivita' dell'UTENTE», 30 MINUTI — «chi resta mezz'ora a
	 *          guardare un video senza toccare nulla viene staccato».
	 *
	 *      ⛔ `ultimo_byte` misura il SECONDO e veniva usato per il PRIMO: un
	 *         client che guarda e non tocca non manda niente, e trenta secondi
	 *         senza toccare la tastiera valevano «il client e' sparito».
	 *
	 *      `[M]` 16 agosto, col browser: sessione aperta, nessun input, e a
	 *      30013 ms «STACCATO per silenzio, posti occupati: 0» — mentre la
	 *      connessione era viva (QUIC non ha fiatato per 111 s, e un solo tasto
	 *      ha ripreso il posto sulla STESSA connessione).  ⛔ E il prezzo si e'
	 *      pagato: una seconda scheda e' entrata e ha preso il desktop del
	 *      primo, che si e' congelato.  E' I2 rotta nel caso che `RCP.md` §8.2
	 *      nomina per iscritto — *«un client vivo occupa, e il nuovo e'
	 *      rifiutato»*. */
	uint64_t ultimo_byte; /* l'ultimo byte di RCP dal client: l'UTENTE (§5.3) */
	uint64_t ultima_vita; /* l'ultimo pacchetto autenticato: il CLIENT (§5.3) */
	uint64_t cred_arrivo; /* quando e' arrivato CREDENZIALI */
	bool cred_buone;      /* il verdetto, gia' calcolato ma non ancora detto */
	uint8_t cred_motivo;  /* se non buone */
	/* ⭐ LA VERIFICA CHIESTA A UN ALTRO PROCESSO — `DECISIONI.md` §1.10.
	 *
	 * ⛔ `verdetto_atteso` e' vero fra la domanda e la risposta, ed e' la
	 *    ragione per cui `cred_buone` non basta piu' da solo: prima del 12
	 *    agosto 2026 il verdetto era gia' pronto quando lo stato diventava
	 *    `attesa-verdetto`, perche' PAM aveva bloccato il filo.  ⚠ Adesso
	 *    `attesa-verdetto` aspetta DUE cose: il secondo fisso di §4.4-bis e la
	 *    risposta dell'aiutante — e l'ordine fra le due non e' garantito.
	 *
	 * ⛔ E finche' `verdetto_atteso` e' vero, `cred_buone` vale **false**: se
	 *    qualcosa saltasse via nel mezzo, quel che si legge e' un no
	 *    (invariante I3). */
	bool verdetto_atteso;
	uint64_t pratica;     /* il numero con cui la risposta si riconosce */
	/* ⛔ `true` quando il no NON viene da PAM ma da noi (aiutante spento,
	 * pratica scaduta): non conta come tentativo fallito di §4.4-bis.  Un
	 * difetto del server che bannasse l'utente per dodici ore sarebbe «la
	 * peggiore diagnosi che questo progetto possa produrre» (§4.4-bis). */
	bool no_e_nostro;
	bool attaccata;       /* occupa un posto nel registro delle sessioni */
	/* ⛔ L'accumulo e' allocato a richiesta, e si azzera prima di liberarlo:
	 * ci passa la `CREDENZIALI`, cioe' la parola d'ordine in chiaro (§4.4).
	 * Vedi `accumula()` e `rcp_libera()` — rilievi R9.8 e R9.13. */
	uint8_t *acc;
	size_t acc_len, acc_cap;
	/* le capacita' negoziate, per il registro (§4.3: la scelta si scrive) */
	char codec[32];
	char profondita[32];
	char audio[32];
	/* ⛔ IL TETTO DEL DECODIFICATORE — `video.misura_massima` di §4.3.
	 *
	 * `0` vuol dire «il client non l'ha dichiarata», e non e' la stessa cosa
	 * di «l'ha dichiarata zero»: §4.5 vincola la tela concessa **solo se il
	 * client l'ha dichiarata**.  ⚠ Prima del 10 agosto 2026 (notte) questi due
	 * campi non esistevano: il nome era riconosciuto come lecito in
	 * `NOMI_NOTI` e il valore veniva buttato — rilievo B-1. */
	uint32_t max_l, max_a;

	/* ==================================================================== */
	/* ⭐ IL CANALE VIDEO — §2.5, §5.1, §5.2, §6.2                          */

	/* ⛔⭐ «`SESSIONE` E' STATA SPEDITA», E NON «LO STATO E' ATTIVA».
	 *
	 * §2.5 scrive la regola con queste parole: «nessuno stream video prima di
	 * aver spedito `SESSIONE`».  ⚠ Lo stato `attiva` e' vicinissimo e NON e'
	 * la stessa cosa — e' una **grandezza sostitutiva**: cambia con
	 * `S_STACCATA` (una sessione che ha taciuto trenta secondi ha spedito
	 * `SESSIONE` da un pezzo), e non cambierebbe affatto se un giorno lo stato
	 * si mettesse a `attiva` una riga prima di spedire il messaggio.
	 *
	 * ⛔ Questa riga si accende NELLA STESSA riga che spedisce `SESSIONE`, e
	 *    solo se il messaggio e' partito davvero (`if (!w.pieno)`).
	 *
	 * ⭐ `LEZIONI.md` §1.13, applicata mentre si scriveva: *«si nomina la
	 *    grandezza vera del fenomeno, e si guarda se il protocollo la porta
	 *    gia'»*.  Qui il fenomeno e' «il client sa la tela e il codec», e il
	 *    fatto che glielo dice e' `SESSIONE` — non uno stato del server. */
	bool sessione_spedita;

	/* ⛔ §6.2: LA TELA **IN VIGORE**, che e' quella concessa in `SESSIONE`
	 * (§4.5) **oppure** l'ultima concessa da `TELA(ADATTATA)` (§7.1).  ⚠ `0`
	 * qui non e' una misura: e' «non c'e' ancora nessuna tela», e `sessione_
	 * spedita` e' il fatto che lo dice. */
	uint32_t tela_l, tela_a;

	/* ⛔ §6.2: il contatore dei fotogrammi.  `0` = **nessuno spedito**, ed e'
	 * il significato che §7.1 da' allo zero in `RICHIEDI_CHIAVE`: qui non e'
	 * un sentinella implicito (§6.0), e' quello dichiarato. */
	uint32_t video_numero;

	/* ⛔ §5.2: «il prossimo fotogramma DEVE essere una chiave».  Vero:
	 *   · appena `SESSIONE` e' partita           (primo punto delle regole)
	 *   · dopo un `TELA(ADATTATA)` che CAMBIA la misura  (secondo punto)
	 *   · quando il client manda `RICHIEDI_CHIAVE`       (§5.2, §7.1) */
	bool serve_chiave;
	/* Perche' serve, per il registro: le tre ragioni non sono la stessa cosa
	 * e chi diagnostica deve poterle distinguere. */
	const char *serve_chiave_perche;

	/* ⛔ §5.2, eccezione 5 di §3: «il server PUO' ignorare una
	 * `RICHIEDI_CHIAVE` che arrivi entro 200 ms **dall'ultima chiave che ha
	 * spedito**» — ⛔ non dall'ultima richiesta ricevuta, e la differenza non
	 * e' una sfumatura: contando dalle richieste, due client insistenti
	 * spostano l'orologio all'infinito e la chiave non parte mai. */
	uint64_t ultima_chiave_ms;
	bool mai_spedita_una_chiave;

	/* Il fotogramma aperto adesso — §5.1, uno stream per fotogramma.
	 * ⛔ `video_aperto` e non «`stream` vale -1»: `0` e' un identificatore di
	 *    stream legittimo, e un sentinella preso da un valore valido e' quel
	 *    che §6.0 vieta ai campi del protocollo.  Non lo si fa nemmeno qui. */
	bool video_aperto;
	int64_t video_stream;
	bool video_e_chiave;      /* §5.2: una chiave NON si abbandona */
	uint32_t video_suo_numero;
	size_t video_da_scrivere; /* i byte di dati DICHIARATI in `apri` */
	size_t video_scritti;     /* quelli usciti finora */
	uint64_t video_aperto_ms; /* l'ora della sessione quando si e' aperto */
	/* Il conto degli abbandoni, per il registro: §5.1 vuole che ogni
	 * abbandono si veda, e un conteggio senza denominatore non e' una misura
	 * (`LEZIONI.md` §1.9). */
	uint32_t video_spediti, video_abbandonati;

	/* ==================================================================== */
	/* ⭐ IL CANALE DI INPUT — §2.5, §7.1, §7.3                             */

	/* §2.5: lo stream di input e' **uno solo**.  ⛔ `inp_stream_noto` e non
	 * «`inp_stream` vale -1»: uno stream 0 e' un identificatore legittimo, e
	 * un sentinella preso da un valore valido e' quel che §6.0 vieta. */
	bool inp_stream_noto;
	int64_t inp_stream;
	/* L'accumulo, fisso: vedi il riquadro di `I_ACCUMULO`. */
	uint8_t inp_acc[I_ACCUMULO];
	size_t inp_acc_len;

	/* ⛔ §7.3: «l'`id` cresce di **almeno uno** a ogni messaggio, **su tutto
	 *    il canale di input** — non uno per tipo».  ⇒ UN contatore, e uno
	 *    solo: cinque contatori per tipo accetterebbero
	 *    `PUNTATORE(4)` dopo `PULSANTE(9)`, e allora il campo `input` dei
	 *    fotogrammi (§6.2) non tornerebbe piu' indietro coerente con niente.
	 * ⚠ `0` = nessuno ancora, ed e' il valore che §7.3 riserva. */
	uint32_t inp_ultimo_id;
	/* ⛔ §6.2: quello che torna nel campo `input` dei fotogrammi — e avanza
	 * SOLO quando il gancio ha risposto 0.  Vedi `rcp_input_ultimo_iniettato()`. */
	uint32_t inp_ultimo_iniettato;
	/* Il conto, e sono TRE numeri perche' i fatti sono tre: quanti arrivati,
	 * quanti iniettati, quanti rifiutati da chi inietta.  ⛔ «Zero iniettati»
	 * detto da solo non distingue un compositore muto da un client fermo. */
	uint32_t inp_arrivati, inp_iniettati, inp_non_iniettati;
	/* ⚠ §7.3: l'`istante` del client, in microsecondi.  ⛔ E NON LO CONSUMA
	 *   NESSUNA REGOLA di questo modulo: «in una pagina l'orologio monotono e'
	 *   in millisecondi e la sua grana e' deliberatamente ingrossata — il
	 *   client scrive `millisecondi × 1000` e NON DEVE far credere a una
	 *   precisione che non ha» (rilievo R1.27).  Sta qui per il registro e per
	 *   la diagnosi — «quando l'utente ha mosso la mano» invece di «quando il
	 *   byte e' arrivato» — e ⛔ nessuna misura si costruisce su di lui: il
	 *   ritardo lo misura l'anello chiuso di `DECISIONI.md` §2.6, e il
	 *   fotogramma porta indietro l'`id`, non l'istante. */
	uint64_t inp_ultimo_istante_us;

	/* ⛔ §7.1 / §3 eccezione 3 — IL SECONDO DI GRAZIA.  La tela PRECEDENTE e
	 * il momento in cui e' stata sostituita: per un secondo una coordinata
	 * valida su quella si SATURA alla nuova invece di chiudere la sessione.
	 * ⚠ `tela_prec_l == 0` vuol dire «nessuna grazia in corso», ed e' lecito
	 *   perche' una tela di larghezza zero non e' mai stata concessa (§4.5). */
	uint32_t tela_prec_l, tela_prec_a;
	uint64_t tela_grazia_da;
	/* Quante coordinate ha salvato la grazia: §3 vuole che «ogni tolleranza
	 * vada scritta nel registro», e un conteggio permette di accorgersi che
	 * una tolleranza si e' messa a coprire il caso normale. */
	uint32_t inp_grazie;
	/* ⛔ §7.3, ultimo capoverso: il rilascio al distacco si fa **una volta
	 * sola**.  Le tre strade che finiscono una connessione — congedo,
	 * silenzio, errore — possono percorrersi in fila, e chiamare il gancio
	 * due volte non fa danno ma scrive due righe che dicono cose diverse
	 * sullo stesso fatto. */
	bool inp_rilasciato;

	/* ⛔⭐⭐ L'`ADATTA_TELA` GIRATA AL PALCO E NON ANCORA RISPOSTA — §7.1, e la
	 *     catena `figli_ritela()` → `cattura_ridimensiona()` (`DECISIONI.md`
	 *     §5.0-sexies).
	 *
	 * ⛔ ESISTE PERCHE' LA RISPOSTA NON TORNA DA DOVE PARTE LA DOMANDA.  Il
	 *    palco sta in un altro processo, e l'unico modo di sapere che il
	 *    compositore ha obbedito e' **vedere arrivare un fotogramma alla misura
	 *    nuova**: puo' volerci qualche decina di millisecondi (`[M]` Mutter 41,6
	 *    ms, labwc 5,1 ms), puo' arrivarne uno di misura DIVERSA da quella
	 *    chiesta (§4.5 lo permette), e puo' non arrivarne nessuno.
	 *
	 * ⛔ E QUESTO E' PRECISAMENTE IL MOTIVO PER CUI SERVE UN'ATTESA CON UN
	 *    FONDO: §7.1 impone che *«a ogni `ADATTA_TELA` il server DEVE rispondere
	 *    con un `TELA`, riuscito o no.  Un silenzio lascia il client ad
	 *    aspettare per sempre»* — e sul client quel silenzio non e' solo
	 *    un'attesa: §6.2 gli fa TRATTENERE i fotogrammi finche' una richiesta e'
	 *    senza risposta, cioe' gli fa crescere la coda in memoria.
	 *
	 * ⚠ `tela_volo_da == 0` insieme a `tela_volo` falso: nessuna richiesta in
	 *   volo.  E se ne arriva una seconda mentre la prima e' in volo, la seconda
	 *   SOSTITUISCE la prima e il `TELA` che uscira' vale per tutt'e due: il
	 *   conto sul client scenderebbe di uno solo — ⛔ per questo la prima si
	 *   RISPONDE prima di accettare la seconda (vedi `T_ADATTA_TELA`). */
	bool tela_volo;
	uint32_t tela_volo_l, tela_volo_a;
	uint64_t tela_volo_da;
	/* ⛔ DA QUANDO il palco consegna una misura diversa dalla tela in vigore
	 *    SENZA che nessuno gliel'abbia chiesto.  ⚠ Zero = sono d'accordo.
	 *
	 * ⛔ Non e' un doppione di `tela_volo_da`, ed e' l'altro caso della stessa
	 *    famiglia: li' il disaccordo lo abbiamo voluto noi e si aspetta che
	 *    finisca; qui non lo ha voluto nessuno, e la prima mossa e' **chiedere
	 *    al palco di tornare** alla tela in vigore.  Se dopo
	 *    `RCP_TELA_ATTESA_MS` non e' tornato, si adotta la sua misura: una
	 *    sessione con una tela inattesa vale piu' di una sessione che non vede
	 *    un pixel (`SPECIFICHE.md` §8.3, e I1 — «una sessione brutta vale piu'
	 *    di una sessione chiusa»). */
	uint64_t tela_disaccordo_da;
	/* Quanto si aspetta prima di richiedere al palco di tornare: raddoppia a
	 * ogni tentativo andato a vuoto, fino a `RCP_TELA_RICHIAMO_MAX_MS`. */
	uint64_t tela_disaccordo_attesa;
};

/* Dichiarata qui perche' il limitatore dei tentativi, qui sotto, DEVE poter
 * scrivere nel registro: un limite raggiunto in silenzio e' un limite che non
 * esiste (§3, e rilievo R9.1). */
static void reg(rcp_sessione *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));

/* ⛔⭐ §7.3 — «Al distacco si rilascia tutto».  Dichiarata qui perche' la
 *     chiamano TRE strade che stanno piu' in su di dove e' definita — il
 *     congedo, il silenzio di §5.3 e la fine della sessione — e le tre sono
 *     esattamente le tre che §7.3 nomina: «per congedo, per silenzio, per
 *     errore».  Definita nella sezione del canale di input, dov'e' il resto. */
static void rilascia_al_distacco(rcp_sessione *s, const char *perche);

/* ⛔ §5.3 / rilievo R9.2 — il posto ripreso da chi torna a parlare.  Dichiarata
 * qui perche' i byte del client entrano da DUE porte (`rcp_ricevi()` e
 * `rcp_ricevi_input()`) e la seconda sta piu' in su della definizione. */
static bool torna_a_parlare(rcp_sessione *s);

/* ------------------------------------------------------------------------ */
/* ⛔ IL REGISTRO DELLE SESSIONI ATTACCATE — §8.2 motivo 0x0F
 *
 * «Chi viene rifiutato e' chi arriva, non chi c'era»: nessun client attaccato
 * e vivo viene mai spodestato.  Qui basta un elenco piccolo: il banco ne apre
 * due o tre, e un server vero lo sostituira' con la sua tabella delle sessioni
 * — ma la REGOLA sta qui, non li'.                                          */
#define MAX_ATTACCATE 16
static struct {
	char utente[257];
	bool usato;
} attaccate[MAX_ATTACCATE];

static bool posto_occupato(const char *utente)
{
	for (int i = 0; i < MAX_ATTACCATE; i++)
		if (attaccate[i].usato && strcmp(attaccate[i].utente, utente) == 0)
			return true;
	return false;
}

/* ⛔⭐ DUE FATTI DIVERSI NON POSSONO AVERE LO STESSO ESITO — rilievo R9.3.
 *
 * `posto_prendi()` restituiva `false` per due cose che non si somigliano
 * nemmeno: «il posto di questo utente e' occupato» e «la tabella e' piena».
 * Il chiamante ne deduceva una sola, e congedava con `GIA_ATTIVA_REMOTA`.
 *
 * ⛔ Il diciassettesimo utente di una macchina multi-tenant (`SPECIFICHE.md`
 *    §5.5) — che non ha mai aperto niente da nessuna parte — riceveva
 *    `CONGEDO(0x0F)`, e il client, come §8.2 gli impone, ne costruiva la frase
 *    «hai gia' una sessione attiva altrove».  **E' falsa.**  E' letteralmente
 *    il sintomo che il riquadro sopra `rcp_chiusa_dal_client()` dichiara di
 *    essere andato a curare: «mi dice che sono gia' collegato, e non e' vero».
 *    La cura di allora ha tolto una delle due strade; questa era l'altra.
 *
 * ⭐ Il motivo giusto per la tabella piena e' §8.2 `0x0E`
 *    SESSIONE_NON_SERVIBILE: «l'attacco e' ben formato ma non si puo'
 *    servire», e DEVE portare il dettaglio nel corpo — che e' esattamente
 *    questo caso. */
enum esito_posto {
	POSTO_PRESO,
	POSTO_OCCUPATO,       /* c'e' gia' un client attaccato a QUESTA sessione */
	POSTO_NIENTE_PIU_POSTI /* il registro delle sessioni e' pieno */
};

static enum esito_posto posto_prendi(const char *utente)
{
	if (posto_occupato(utente))
		return POSTO_OCCUPATO;
	for (int i = 0; i < MAX_ATTACCATE; i++) {
		if (!attaccate[i].usato) {
			attaccate[i].usato = true;
			snprintf(attaccate[i].utente, sizeof attaccate[i].utente, "%s",
			         utente);
			return POSTO_PRESO;
		}
	}
	return POSTO_NIENTE_PIU_POSTI;
}

static int posti_occupati(void)
{
	int n = 0;
	for (int i = 0; i < MAX_ATTACCATE; i++)
		if (attaccate[i].usato)
			n++;
	return n;
}

static void posto_lascia(const char *utente)
{
	for (int i = 0; i < MAX_ATTACCATE; i++)
		if (attaccate[i].usato && strcmp(attaccate[i].utente, utente) == 0)
			attaccate[i].usato = false;
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ IL BAN DELL'INDIRIZZO — §4.4-bis, riscritto il 10 agosto 2026
 *
 * `DECISIONI.md` §1.9, deciso dall'utente: **tre autenticazioni fallite
 * consecutive dallo stesso indirizzo, e quell'indirizzo e' fuori per 12 ore.**
 *
 * ⛔ CHE COSA E' SPARITO, E VA SAPUTO LEGGENDO QUESTO FILE.  La forma
 *    precedente — 5 tentativi in 5 minuti, finestra da 30 s che raddoppiava
 *    fino a 15 minuti, **due** contatori (uno per nome utente e uno per
 *    indirizzo), scadenza a 30 minuti di quiete — era 🔸, cioe' scritta da noi e
 *    mai pronunciata.  Ne resta **un contatore solo**, sull'indirizzo.
 *
 *    ⭐ E con essa sparisce per costruzione il difetto che B5 ha trovato: la
 *       chiave conteneva la PORTA, e con un solo tentativo per connessione
 *       (§4.4) la porta cambia ogni volta — quel contatore valeva sempre 1.
 *       Qui la chiave e' `s->indirizzo`, che `rcp_chiave_indirizzo()` ha gia'
 *       normalizzato.
 *
 * ⛔ IL NOME UTENTE NON CONTA.  Tre nomi diversi contano tre: e' la decisione,
 *    ed e' anche l'unica forma che un contatore per indirizzo puo' avere senza
 *    mentire.  Chi cerca qui il contatore per nome non lo trova perche' non c'e'.
 *
 * ⛔ I TRE FALLIMENTI DEVONO STARE DENTRO CINQUE MINUTI, o il ban non scatta
 *    (regola dell'utente, 10 agosto 2026).  Due errori di lunedi' e uno di
 *    venerdi' NON bannano: chi sbaglia a digitare ogni tanto non e' chi prova
 *    parole d'ordine.  E un'autenticazione **riuscita** azzera comunque tutto.
 *
 *    ⚠ La finestra e' SCORREVOLE, e non ancorata al primo fallimento: si tiene
 *      **l'ora degli ultimi tre**, e si guarda se stanno tutti e tre in cinque
 *      minuti.  Con la finestra ancorata al primo, tre fallimenti a 0:00, 4:59 e
 *      5:01 farebbero ripartire il conto da UNO — buttando via anche quello di
 *      4:59, che dista due secondi dall'ultimo.  ⛔ Chi prova parole d'ordine a
 *      un ritmo appena piu' lento della finestra non verrebbe mai fermato, ed e'
 *      esattamente la forma di difetto che «il codice c'era e non faceva
 *      niente» ha gia' prodotto una volta in questo file.
 *
 * ⛔ IL BAN SOPRAVVIVE AL RIAVVIO (`DECISIONI.md` §1.9, invariante I7): un ban
 *    che si azzera riavviando e' una protezione che si perde da se', e chi
 *    riavvia per un altro motivo non sa di averla tolta.  Il file lo scrive
 *    `salva_ban()`; `rcp_ban_carica()` lo rilegge all'avvio.
 *
 *    ⚠ E il file porta un'ora **assoluta**, non `ora`: `ora` e' un orologio
 *      MONOTONO che riparte da un punto qualunque a ogni processo, quindi
 *      scriverlo sul disco produrrebbe scadenze senza senso al riavvio.  Si
 *      scrive l'epoch dei secondi e si riconverte al caricamento.
 *
 * ⛔ E SI ESCE IN DUE MODI (`DECISIONI.md` §1.9): le 12 ore che passano, oppure
 *    `rcp_sblocca()` — che e' il comando di sblocco, e chiede l'accesso alla
 *    macchina.  ⭐ **E' anche quel che rende B8 possibile**: senza, un banco che
 *    misura i tempi dell'autenticazione avrebbe tre campioni e poi mezza
 *    giornata di silenzio.  Ogni sblocco si scrive nel registro.
 *
 * ⚠ LA TABELLA HA UN FONDO, e il rilievo R9.1 vale identico: se `trova_o_crea()`
 *   potesse fallire, un fallimento non contato sarebbe un limitatore che non
 *   c'e'.  Quindi non fallisce: sfratta, e lo dichiara.  ⛔ La vittima non e' mai
 *   una voce BANNATA se ce n'e' una che non lo e' — altrimenti riempire la
 *   tabella di indirizzi inventati sarebbe il modo di cancellarsi un ban.
 *   ⚠ Con dodici ore i posti si liberano molto piu' lentamente di prima: da qui
 *     i 256 posti al posto di 64.  `[?]` Che bastino non e' misurato — un
 *     attaccante con piu' di 256 indirizzi si spinge fuori i ban da solo, e la
 *     riga di registro dello sfratto e' l'unico posto in cui lo si vedrebbe.
 *
 * ⛔ E NON C'E' PIU' NESSUNA SCADENZA PER QUIETE.  La forma vecchia ne aveva una
 *    (30 minuti) e serviva a restituire i posti alla tabella; qui restituirebbe
 *    anche i **tentativi**, cioe' contraddirebbe «consecutive».  I posti li
 *    restituiscono la scadenza del ban e lo sfratto.                          */
#define SOGLIA 3
#define FINESTRA 300000u     /* 5 minuti: i tre fallimenti devono starci dentro */
#define BAN_DURATA 43200000u /* 12 ore, in millisecondi */
#define MAX_TENTATIVI 256

static struct {
	char indirizzo[64];
	bool usato;
	/* ⛔ L'ora degli ULTIMI TRE fallimenti, non il loro numero: e' quel che
	 * serve per rispondere a «tre entro cinque minuti» senza ancorare la
	 * finestra al primo.  `quanti` dice quanti slot sono pieni. */
	uint64_t falliti_t[SOGLIA];
	int quanti;
	uint64_t bannato_fino; /* monotono, come `ora`; 0 = non bannato */
	uint64_t ultimo_tocco;
} tentativi[MAX_TENTATIVI];

static char percorso_ban[512]; /* vuoto = non si persiste (il banco, di solito) */

/* ⛔⭐ L'INDIRIZZO SENZA LA PORTA — trovato da B5 il 10 agosto 2026
 *
 * §4.4-bis vuole «un contatore per **indirizzo di provenienza**».  La prima
 * stesura di questo modulo gli passava `s->provenienza`, che e'
 * `192.168.0.2:44661` — **con la porta**.  E §4.4 ammette **un solo tentativo
 * per connessione**, quindi la porta cambia a ogni tentativo: quel contatore
 * valeva **sempre 1**, e non ha mai bloccato nessuno.
 *
 * ⚠ E' la forma peggiore di difetto: il codice c'era, sembrava giusto, si
 *   leggeva bene, e **non faceva niente**.  Nessuna prova a connessione
 *   singola lo vede; nessun registro lo nomina; il sintomo — «si puo' provare
 *   una parola d'ordine all'infinito» — non arriva mai da solo.
 *
 * ⭐ L'ha trovato il controllo di B5 che prova SETTE tentativi falliti con
 *    SETTE NOMI DIVERSI dallo stesso indirizzo: coi nomi uguali il contatore
 *    per **nome** copriva il buco, e il banco sarebbe stato verde.  ⛔ Da oggi
 *    quel contatore non esiste piu', quindi la prova a sette nomi e' l'unica
 *    forma possibile — ed e' quel che B8 pretende.
 *
 * ⚠ Si taglia agli ULTIMI due punti, non ai primi: un indirizzo IPv6 e'
 *   `[fe80::1]:44661`, e tagliare al primo produrrebbe `[fe80`.
 *
 * ⛔ E LA CHIAVE PORTA LE PARENTESI QUADRE ANCHE PER IPv4 — `[M]` 10 agosto
 *    2026, letto nel registro del server e non dedotto: `util::straddr()`
 *    dell'esempio di ngtcp2 scrive **sempre** `[127.0.0.1]:55680`, quindi la
 *    chiave che questo modulo conta e' `[127.0.0.1]`, con le quadre, ed e'
 *    quella che finisce nel file dei ban.  ⚠ Chi chiama da fuori — il comando
 *    di sblocco, che riceve un indirizzo digitato da una persona — deve
 *    passare per `rcp_chiave_indirizzo()`, o cerchera' `192.168.0.2` dove sta
 *    scritto `[192.168.0.2]` e si sentira' rispondere «non era bannato».
 *
 * ⛔ E QUI C'ERA UN'ASSUNZIONE CHE IL COMANDO DI SBLOCCO ROMPE: che la porta ci
 *    sia sempre.  Fino a oggi l'unico chiamante era la sessione, che porta
 *    `[fe80::1]:44661`; il comando di sblocco porta `[fe80::1]` e basta, e
 *    tagliare agli ultimi due punti lo riduceva a `[fe80:`.  ⭐ La guardia e'
 *    una riga: se finisce con `]` la porta non c'e', quindi non c'e' niente da
 *    tagliare.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ E IL 10 AGOSTO 2026 (NOTTE) QUESTA FUNZIONE E' STATA TOLTA — rilievo B-8
 *
 * Si chiamava `solo_indirizzo()` e toglieva la porta **senza mettere le
 * quadre**.  La chiamavano tre posti: `rcp_apri()`, `rcp_bannato()` e
 * `rcp_sblocca()`.  Sui primi non faceva danno **per caso** — l'ospite le
 * quadre gliele metteva gia' lui — ma sulle due funzioni PUBBLICHE il danno
 * era misurabile:
 *
 *     rcp_bannato("192.168.0.2")   = 0     ⛔ «non e' bannato»
 *     rcp_bannato("[192.168.0.2]") = 1
 *
 * ⚠ E la forma che rispondeva **falso** e' esattamente quella che
 *   `pagina.c` costruisce per IPv4 (`getnameinfo` + `"%s:%s"`).  Oggi non fa
 *   danno solo perche' chi chiama normalizza **prima**, cioe' perche' la
 *   normalizzazione era di **chi chiama** — che e' precisamente quel che
 *   §4.4-bis vieta con un ⛔ e quel che `rcp.h` promette di fare **qui
 *   dentro**.
 *
 * ⭐ La cura non e' aggiungere le quadre a `solo_indirizzo()`: e' non avere
 *    **due** funzioni che fanno la chiave.  Ne resta una — quella qui sotto —
 *    e la usano tutti e tre i posti.  ⚠ E' idempotente per costruzione, quindi
 *    chi normalizza due volte ottiene la stessa chiave e nessun chiamante
 *    esistente cambia comportamento.
 * ------------------------------------------------------------------------ */

/* ⛔ La CHIAVE del ban, nella forma esatta in cui §4.4-bis la conta — e la
 * ragione per cui e' pubblica sta tutta in una misura.
 *
 * L'ospite ha due strade che arrivano qui, e portano l'indirizzo in due forme
 * diverse:
 *
 *   la sessione        `util::straddr()`, cioe' `[127.0.0.1]:55680` — quadre e
 *                      porta, e questa e' la forma che ha fatto la chiave;
 *   il comando         quel che una persona digita: `127.0.0.1`, senza niente.
 *
 * ⛔ Se l'ospite se la costruisse da se', il giorno in cui `straddr()` cambiasse
 *    forma il comando di sblocco comincerebbe a rispondere «non era bannato» a
 *    ogni indirizzo, per sempre e in silenzio: un comando che dice sempre la
 *    stessa cosa non ha nessun sintomo.  Il formato della chiave lo sa questo
 *    file, ed e' l'unico che lo deve sapere.
 *
 * ⚠ La regola sui due punti, e vale la riga che costa: con le quadre la porta
 *   si riconosce sempre; senza, `127.0.0.1:53` ha UN due punti (host e porta) e
 *   `fe80::1` ne ha due o piu' (ed e' tutto indirizzo).  E' esattamente la
 *   ragione per cui le quadre esistono.
 *
 * ⭐ E DAL 10 AGOSTO 2026 (NOTTE) E' L'UNICA che fa la chiave, dentro e fuori:
 *    la chiamano `rcp_apri()`, `rcp_bannato()` e `rcp_sblocca()`.  Vedi il
 *    riquadro qui sopra, rilievo B-8. */
void rcp_chiave_indirizzo(const char *testo, char *fuori, size_t cap)
{
	char nudo[64];
	if (!testo)
		testo = "?";
	if (testo[0] == '[') {
		const char *fine = strchr(testo, ']');
		size_t n = fine ? (size_t)(fine - testo) - 1 : strlen(testo) - 1;
		if (n >= sizeof nudo)
			n = sizeof nudo - 1;
		memcpy(nudo, testo + 1, n);
		nudo[n] = 0;
	} else {
		const char *primo = strchr(testo, ':');
		const char *ultimo = strrchr(testo, ':');
		/* un solo due punti = host:porta; due o piu' = IPv6 nudo */
		size_t n = (primo && primo == ultimo) ? (size_t)(primo - testo)
		                                      : strlen(testo);
		if (n >= sizeof nudo)
			n = sizeof nudo - 1;
		memcpy(nudo, testo, n);
		nudo[n] = 0;
	}
	snprintf(fuori, cap, "[%s]", nudo);
}

/* Cerca e basta: ⛔ interrogare la guardia NON deve consumare un posto. */
static int trova(const char *indirizzo)
{
	for (int i = 0; i < MAX_TENTATIVI; i++)
		if (tentativi[i].usato &&
		    strcmp(tentativi[i].indirizzo, indirizzo) == 0)
			return i;
	return -1;
}

/* Restituisce la voce, creandola se serve.  ⛔ Non fallisce mai (R9.1): se la
 * tabella e' piena sfratta, e in `*sfrattata` lascia il nome della voce buttata
 * via perche' il chiamante lo SCRIVA nel registro. */
static int trova_o_crea(const char *indirizzo, uint64_t ora, const char **sfrattata)
{
	static char nome_sfrattato[64];
	*sfrattata = NULL;
	int i = trova(indirizzo);
	if (i >= 0)
		return i;
	int libero = -1, vittima = -1;
	for (int k = 0; k < MAX_TENTATIVI; k++) {
		if (!tentativi[k].usato) {
			libero = k;
			break;
		}
		bool k_bannata = ora < tentativi[k].bannato_fino;
		if (vittima < 0) {
			vittima = k;
			continue;
		}
		bool v_bannata = ora < tentativi[vittima].bannato_fino;
		if (v_bannata && !k_bannata) {
			vittima = k;
		} else if (v_bannata == k_bannata &&
		           tentativi[k].ultimo_tocco < tentativi[vittima].ultimo_tocco) {
			vittima = k;
		}
	}
	if (libero < 0) {
		libero = vittima; /* c'e' sempre: MAX_TENTATIVI > 0 */
		snprintf(nome_sfrattato, sizeof nome_sfrattato, "%s",
		         tentativi[libero].indirizzo);
		*sfrattata = nome_sfrattato;
	}
	memset(&tentativi[libero], 0, sizeof tentativi[libero]);
	tentativi[libero].usato = true;
	tentativi[libero].ultimo_tocco = ora;
	snprintf(tentativi[libero].indirizzo, sizeof tentativi[libero].indirizzo,
	         "%s", indirizzo);
	return libero;
}

/* ⛔ Scrive su file i soli indirizzi BANNATI, con la scadenza in secondi
 * dall'epoch.  Si chiama a ogni cambiamento — ban nuovo, sblocco — perche' un
 * ban che vive solo in memoria fino al prossimo salvataggio periodico e' un ban
 * che un riavvio improvviso porta via (I7).
 *
 * ⚠ Si scrive su un file temporaneo e si rinomina: un `rename()` e' atomico, e
 *   un file dei ban troncato a meta' da un riavvio sarebbe peggio di nessun
 *   file — direbbe «questi indirizzi non erano bannati». */
static void salva_ban(rcp_sessione *s, uint64_t ora)
{
	if (percorso_ban[0] == 0)
		return;
	char tmp[sizeof percorso_ban + 8];
	snprintf(tmp, sizeof tmp, "%s.nuovo", percorso_ban);
	FILE *f = fopen(tmp, "w");
	if (!f) {
		if (s)
			reg(s, "⛔ non ho potuto scrivere il file dei ban «%s»: il ban "
			       "vive solo in memoria e un riavvio lo toglie (§4.4-bis)",
			    tmp);
		return;
	}
	time_t adesso = time(NULL);
	int quanti = 0;
	for (int i = 0; i < MAX_TENTATIVI; i++) {
		if (!tentativi[i].usato || ora >= tentativi[i].bannato_fino)
			continue;
		uint64_t restano = tentativi[i].bannato_fino - ora;
		fprintf(f, "%s %lld\n", tentativi[i].indirizzo,
		        (long long)(adesso + (time_t)(restano / 1000)));
		quanti++;
	}
	fclose(f);
	if (rename(tmp, percorso_ban) != 0 && s)
		reg(s, "⛔ non ho potuto rinominare il file dei ban su «%s»",
		    percorso_ban);
	else if (s)
		reg(s, "il file dei ban e' aggiornato: %d indirizzi in «%s»", quanti,
		    percorso_ban);
}

static bool bannato(const char *indirizzo, uint64_t ora, uint64_t *restano)
{
	if (restano)
		*restano = 0;
	int i = trova(indirizzo);
	if (i < 0)
		return false; /* mai fallito niente: e' un fatto, non un posto finito */
	if (ora >= tentativi[i].bannato_fino)
		return false;
	if (restano)
		*restano = tentativi[i].bannato_fino - ora;
	return true;
}

static void segna_fallito(rcp_sessione *s, const char *indirizzo, uint64_t ora)
{
	const char *sfrattata = NULL;
	int i = trova_o_crea(indirizzo, ora, &sfrattata);
	if (sfrattata)
		reg(s, "⚠ tabella dei tentativi piena (%d voci): sfrattata la voce "
		       "«%s» per far posto a «%s» — §4.4-bis",
		    MAX_TENTATIVI, sfrattata, indirizzo);
	tentativi[i].ultimo_tocco = ora;
	/* Il ring degli ultimi SOGLIA fallimenti: si scorre di uno e si scrive in
	 * coda.  ⚠ Piu' vecchi di cosi' non servono a nessuna domanda. */
	if (tentativi[i].quanti < SOGLIA) {
		tentativi[i].falliti_t[tentativi[i].quanti++] = ora;
	} else {
		memmove(tentativi[i].falliti_t, tentativi[i].falliti_t + 1,
		        (SOGLIA - 1) * sizeof tentativi[i].falliti_t[0]);
		tentativi[i].falliti_t[SOGLIA - 1] = ora;
	}
	int dentro = 0;
	for (int k = 0; k < tentativi[i].quanti; k++)
		if (ora - tentativi[i].falliti_t[k] <= FINESTRA)
			dentro++;
	reg(s, "tentativo fallito da %s: %d di %d dentro i %u minuti (§4.4-bis)",
	    indirizzo, dentro, SOGLIA, FINESTRA / 60000u);
	if (dentro >= SOGLIA) {
		tentativi[i].bannato_fino = ora + BAN_DURATA;
		reg(s, "⛔ BANNATO l'indirizzo %s per %u ore: %d autenticazioni "
		       "fallite dentro %u minuti (§4.4-bis, DECISIONI.md §1.9)",
		    indirizzo, BAN_DURATA / 3600000u, dentro, FINESTRA / 60000u);
		salva_ban(s, ora);
	}
}

/* ⛔ Solo un'autenticazione RIUSCITA azzera, ed e' quel che «consecutive» vuol
 * dire.  Si azzera la voce intera: un indirizzo che entra non ha piu' storia. */
static void azzera_falliti(rcp_sessione *s, const char *indirizzo, uint64_t ora)
{
	int i = trova(indirizzo);
	if (i < 0)
		return;
	if (tentativi[i].quanti > 0)
		reg(s, "accesso riuscito da %s: il conto dei falliti torna a zero "
		       "(erano %d) — §4.4-bis",
		    indirizzo, tentativi[i].quanti);
	memset(&tentativi[i], 0, sizeof tentativi[i]);
	(void)ora;
}

/* ------------------------------------------------------------------------ */
/* Quel che il PADRONE DI CASA chiama: la pagina in TCP e il comando di sblocco.
 *
 * ⛔ La pagina si serve LO STESSO a un indirizzo bannato, e dice che i tentativi
 *    sono esauriti (`DECISIONI.md` §1.9): chi e' bannato per errore e' quasi
 *    sempre il proprietario, e un errore di rete non gli direbbe niente.  Chi
 *    serve la pagina chiama `rcp_bannato()` e scrive la frase.               */
bool rcp_bannato(const char *provenienza, uint64_t ora, uint64_t *restano_ms)
{
	char ind[64];
	/* ⛔ La chiave la fa `rcp_chiave_indirizzo()`, non un taglio della porta:
	 *    `rcp.h` promette che «`provenienza` puo' portare la porta: viene
	 *    tagliata qui dentro», e chi crede all'intestazione passa
	 *    `192.168.0.2` senza quadre — rilievo B-8. */
	rcp_chiave_indirizzo(provenienza, ind, sizeof ind);
	return bannato(ind, ora, restano_ms);
}

/* ⛔ Il comando di sblocco.  Restituisce `true` se qualcosa e' stato tolto:
 * «non era bannato» e «l'ho sbloccato» sono due fatti diversi, e chi comanda
 * deve poterli distinguere.  ⚠ E lo sblocco si scrive nel registro dal
 * chiamante, che ha il contesto: qui non c'e' una sessione a cui appenderlo. */
bool rcp_sblocca(const char *indirizzo, uint64_t ora)
{
	char ind[64];
	/* ⛔ §4.4-bis: «chi digita `192.168.0.2` al comando di sblocco DEVE
	 *    arrivare alla stessa chiave: la normalizzazione e' del server, non di
	 *    chi comanda» — rilievo B-8. */
	rcp_chiave_indirizzo(indirizzo, ind, sizeof ind);
	int i = trova(ind);
	if (i < 0)
		return false;
	bool era_bannato = ora < tentativi[i].bannato_fino;
	memset(&tentativi[i], 0, sizeof tentativi[i]);
	salva_ban(NULL, ora);
	return era_bannato;
}

/* ⛔ Si dichiara dove sta il file dei ban e lo si rilegge: un ban che non
 * sopravvive al riavvio e' una protezione che si perde (I7).  Restituisce
 * quanti ne ha caricati, o -1 se il file c'era e non si e' potuto leggere —
 * ⚠ «zero ban» e «non ho potuto guardare» sono due fatti diversi
 * (`LEZIONI.md` §1.9 regola 1), e il chiamante li deve stampare diversi. */
int rcp_ban_carica(const char *percorso, uint64_t ora)
{
	percorso_ban[0] = 0;
	if (!percorso || !*percorso)
		return 0;
	snprintf(percorso_ban, sizeof percorso_ban, "%s", percorso);
	FILE *f = fopen(percorso_ban, "r");
	if (!f) {
		/* ⛔ QUI STAVA LA SETTIMA VESTE DEL DIFETTO, DENTRO LA FUNZIONE CHE
		 *    L'INTESTAZIONE DICHIARA IMMUNE.  `rcp.h` promette «-1 se il file
		 *    c'era e non si e' potuto leggere», e questa riga restituiva `0` a
		 *    QUALUNQUE fallimento di `fopen()`: un file senza permessi, un
		 *    percorso il cui genitore non e' una directory, un disco che non
		 *    risponde — tutti «zero ban», cioe' **la protezione spenta con
		 *    l'aria di non avere niente da proteggere** (`LEZIONI.md` §1.9
		 *    regola 1, e I7).
		 *
		 * ⭐ A distinguere i due fatti c'e' un dato solo, ed e' `errno`:
		 *    `ENOENT` vuol dire che il file non e' ancora nato — nessun ban, e
		 *    non e' un errore — e ogni altro valore vuol dire che il file c'e'
		 *    (o che non si e' potuto nemmeno chiedere) e non si e' potuto
		 *    guardare.  ⚠ Il chiamante DEVE trattare `-1` come un guasto e non
		 *    come uno zero: chi serve la pagina lo dice, e chi accende il
		 *    server si ferma. */
		return errno == ENOENT ? 0 : -1;
	}
	time_t adesso = time(NULL);
	char riga[128];
	int quanti = 0;
	while (fgets(riga, sizeof riga, f)) {
		char ind[64];
		long long scad = 0;
		if (sscanf(riga, "%63s %lld", ind, &scad) != 2)
			continue;
		if (scad <= (long long)adesso)
			continue; /* scaduto mentre il server era spento */
		const char *sfrattata = NULL;
		int i = trova_o_crea(ind, ora, &sfrattata);
		/* ⛔ Non si ricostruisce nessun conteggio: quel che sopravvive al
		 * riavvio e' il BAN, non i tentativi che l'hanno prodotto. */
		tentativi[i].bannato_fino =
		    ora + (uint64_t)(scad - (long long)adesso) * 1000u;
		quanti++;
	}
	/* ⚠ E anche una lettura che si interrompe a meta' e' «non ho potuto
	 *   guardare»: `fgets` restituisce NULL sia alla fine del file sia su un
	 *   errore, e i due si distinguono solo con `ferror()`.  Un file dei ban
	 *   letto per meta' direbbe «questi indirizzi non erano bannati». */
	int rotto = ferror(f);
	fclose(f);
	return rotto ? -1 : quanti;
}

/* ⛔ Solo per il banco: fra una prova e l'altra si riparte da zero.  In un
 * server vero non la chiama nessuno, ed e' scritto nell'intestazione. */
void rcp_azzera_registro_sessioni(void)
{
	memset(attaccate, 0, sizeof attaccate);
	memset(tentativi, 0, sizeof tentativi);
}

/* ------------------------------------------------------------------------ */
/* Scrittura dei tipi di §6.0, big-endian, senza allineamento e senza
 * riempimento.                                                              */
typedef struct {
	uint8_t *b;
	size_t cap, len;
	bool pieno;
} scrittore;

static void sc_byte(scrittore *s, uint8_t v)
{
	if (s->len + 1 > s->cap) {
		s->pieno = true;
		return;
	}
	s->b[s->len++] = v;
}
static void sc_u16(scrittore *s, uint16_t v)
{
	sc_byte(s, (uint8_t)(v >> 8));
	sc_byte(s, (uint8_t)v);
}
static void sc_u32(scrittore *s, uint32_t v)
{
	sc_byte(s, (uint8_t)(v >> 24));
	sc_byte(s, (uint8_t)(v >> 16));
	sc_byte(s, (uint8_t)(v >> 8));
	sc_byte(s, (uint8_t)v);
}
/* ⛔ §6.0: `u64` big-endian, e serve al solo campo `istante` di §6.2 — l'unico
 * intero a otto byte che RCP/1 mette sul filo. */
static void sc_u64(scrittore *s, uint64_t v)
{
	for (int i = 7; i >= 0; i--)
		sc_byte(s, (uint8_t)(v >> (i * 8)));
}
static void sc_str(scrittore *s, const char *t)
{
	size_t n = strlen(t);
	sc_u16(s, (uint16_t)n);
	for (size_t i = 0; i < n; i++)
		sc_byte(s, (uint8_t)t[i]);
}

/* Lettura, con il controllo dei limiti PRIMA di prendere i byte. */
typedef struct {
	const uint8_t *b;
	size_t len, i;
	bool corto;
} lettore;

static uint8_t le_u8(lettore *l)
{
	if (l->i + 1 > l->len) {
		l->corto = true;
		return 0;
	}
	return l->b[l->i++];
}
static uint16_t le_u16(lettore *l)
{
	uint16_t a = le_u8(l);
	return (uint16_t)((a << 8) | le_u8(l));
}
static uint32_t le_u32(lettore *l)
{
	uint32_t a = le_u16(l);
	return (a << 16) | le_u16(l);
}
/* Copia una stringa in `fuori` (che deve avere spazio per n+1 byte).
 * ⛔ Non convalida l'UTF-8: quello lo fa `utf8_valido`, chiamato dove serve. */
static size_t le_str(lettore *l, char *fuori, size_t cap)
{
	uint16_t n = le_u16(l);
	if (l->corto || l->i + n > l->len) {
		l->corto = true;
		return 0;
	}
	if (n + 1u > cap) {
		/* piu' lunga di quel che il campo ammette: lo dira' chi chiama */
		l->i += n;
		return (size_t)n;
	}
	memcpy(fuori, l->b + l->i, n);
	fuori[n] = 0;
	l->i += n;
	return n;
}

/* §6.0: UTF-8 non valido e' ERRORE_PROTOCOLLO. */
static bool utf8_valido(const char *s, size_t n)
{
	size_t i = 0;
	while (i < n) {
		uint8_t c = (uint8_t)s[i];
		size_t extra;
		if (c < 0x80)
			extra = 0;
		else if ((c & 0xE0) == 0xC0 && c >= 0xC2)
			extra = 1;
		else if ((c & 0xF0) == 0xE0)
			extra = 2;
		else if ((c & 0xF8) == 0xF0 && c <= 0xF4)
			extra = 3;
		else
			return false;
		/* ⚠ I byte di continuazione devono ESSERCI tutti: senza questo
		 * controllo una sequenza troncata in fondo alla stringa passerebbe. */
		if (i + extra >= n)
			return false;
		for (size_t k = 1; k <= extra; k++)
			if ((((uint8_t)s[i + k]) & 0xC0) != 0x80)
				return false;
		i += extra + 1;
	}
	return true;
}

/* ⛔⭐ UN BYTE NULLO IN MEZZO A UNA STRINGA — rilievo R9.11.
 *
 * §6.0 dice che una stringa e' «esattamente `lunghezza` byte».  Tutte le
 * convalide di questo modulo lavorano sulla LUNGHEZZA DICHIARATA; tutti gli
 * usi lavorano sulla STRINGA C che `le_str` termina con uno zero (`%s`,
 * `strcmp`, `voce_presente`, `strchr`, e PAM).  Un `0x00` in mezzo separa le
 * due letture, e `utf8_valido()` lo accetta perche' `c < 0x80`:
 *
 *   `audio.codec` con valore `opus\0pcm` — otto byte, dentro il limite —
 *   faceva congedare con `NIENTE_IN_COMUNE` un client che aveva dichiarato
 *   `pcm`, cioe' negava il ripiego a chi non l'aveva rifiutato;
 *   un utente `root\0nemo` — nove byte sul filo — mandava a PAM `root`, e il
 *   registro e la chiave di §4.4-bis dicevano `root`.  Cio' che e' arrivato e
 *   cio' che si e' giudicato erano due stringhe diverse, e nessuna riga lo
 *   diceva.
 *
 * ⭐ §4.3 lo chiude gia' per le capacita': «un valore e' testo UTF-8
 *    **stampabile**».  Qui si applica alla lettera — e vale anche per il nome
 *    utente, per una seconda ragione: il registro e' un file che si conserva
 *    (§11.1), e un ritorno a capo dentro un nome ci scrive righe che nessuno
 *    ha mandato. */
static bool testo_stampabile(const char *s, size_t n)
{
	if (!utf8_valido(s, n))
		return false;
	for (size_t i = 0; i < n; i++) {
		uint8_t c = (uint8_t)s[i];
		if (c < 0x20 || c == 0x7F) /* i comandi C0 e DEL: 0x00 compreso */
			return false;
	}
	return true;
}

/* §8.2: i motivi sono quindici, da 0x01 a 0x0F.  ⛔ E §3.1: «il codice 0
 * significa chiusura senza motivo e NON DEVE essere usato». */
static bool motivo_di_82(uint8_t m) { return m >= 0x01 && m <= 0x0F; }

/* ------------------------------------------------------------------------ */
/* (la dichiarazione sta in cima, sopra il limitatore dei tentativi) */
static void reg(rcp_sessione *s, const char *fmt, ...)
{
	char riga[512];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(riga, sizeof riga, fmt, ap);
	va_end(ap);
	if (s->g.registra)
		s->g.registra(s->g.ctx, riga);
}

static void manda_messaggio(rcp_sessione *s, uint16_t tipo, const uint8_t *corpo,
                            size_t n)
{
	uint8_t testa[6];
	scrittore w = {testa, sizeof testa, 0, false};
	sc_u16(&w, tipo);
	sc_u32(&w, (uint32_t)n);
	uint8_t *tutto = (uint8_t *)malloc(6 + n);
	if (!tutto)
		return;
	memcpy(tutto, testa, 6);
	if (n)
		memcpy(tutto + 6, corpo, n);
	s->g.manda(s->g.ctx, tutto, 6 + n);
	free(tutto);
}

/* ⛔ §3.1, nell'ordine: si scrive nel registro CHE COSA, si manda CONGEDO se
 * il canale e' ancora utilizzabile, si chiude la sessione col codice del
 * motivo.  Le due strade esistono perche' se una si rompe l'altra porta
 * comunque il motivo — in v1 il server scriveva «congedo» e il client leggeva
 * «errore di rete» per tre fasi.                                            */
static void congeda(rcp_sessione *s, uint8_t motivo, const char *dettaglio)
{
	if (s->stato == S_FINITA)
		return;
	reg(s, "congedo motivo=%#04x dettaglio=%s stato=%s", motivo, dettaglio,
	    NOMI_STATO[s->stato]);
	/* ⛔⭐ §7.3 — E PRIMA DI TUTTO IL RESTO SI RILASCIA QUEL CHE E' PREMUTO.
	 *
	 *     «Quando una connessione finisce — per congedo, per silenzio, per
	 *     errore — il server DEVE rilasciare ogni tasto e ogni pulsante che
	 *     risultano premuti».  ⛔ Sta QUI, dentro `congeda()`, e non accanto a
	 *     ciascuna delle sue trenta chiamate: `RCP.md` §11 la chiama «la regola
	 *     col rapporto danno/costo piu' alto del documento», e una regola con
	 *     quel rapporto non si affida alla disciplina di chi scrive la
	 *     trentunesima.  E' l'invariante I7 letta da dentro — la protezione sta
	 *     nel programma, non in una riga che si puo' perdere.
	 *
	 * ⚠ Il sintomo che si compra: un Ctrl rimasto giu' in una sessione che
	 *   sopravvive al client rende il desktop inservibile al riattacco, e
	 *   nessuno collega le due cose. */
	rilascia_al_distacco(s, "congedo");
	uint8_t corpo[512];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_byte(&w, motivo);
	sc_str(&w, dettaglio);
	if (!w.pieno)
		manda_messaggio(s, T_CONGEDO, corpo, w.len);
	if (s->attaccata) {
		posto_lascia(s->utente);
		s->attaccata = false;
	}
	s->stato = S_FINITA;
	s->g.chiudi(s->g.ctx, motivo);
}

/* ⛔ `RESPINTO` e' il congedo dell'autenticazione: dopo di lui si chiude con
 * lo stesso motivo, e NON si manda anche CONGEDO (§4.4).                    */
static void respingi(rcp_sessione *s, uint8_t motivo)
{
	reg(s, "respinto motivo=%#04x utente=%s da=%s", motivo, s->utente,
	    s->provenienza);
	uint8_t corpo[1];
	corpo[0] = motivo;
	manda_messaggio(s, T_RESPINTO, corpo, 1);
	s->stato = S_FINITA;
	s->g.chiudi(s->g.ctx, motivo);
}

/* ------------------------------------------------------------------------ */
/* §4.3 — le capacita'                                                       */
static bool nome_lecito(const char *n, size_t len)
{
	if (len < 1 || len > 64)
		return false;
	for (size_t i = 0; i < len; i++) {
		char c = n[i];
		if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '.' ||
		      c == '_'))
			return false;
	}
	return true;
}

/* Una voce dentro un elenco separato da virgole. */
static bool voce_presente(const char *elenco, const char *voce)
{
	size_t n = strlen(voce);
	const char *p = elenco;
	while (*p) {
		const char *virgola = strchr(p, ',');
		size_t m = virgola ? (size_t)(virgola - p) : strlen(p);
		if (m == n && strncmp(p, voce, n) == 0)
			return true;
		p = virgola ? virgola + 1 : p + m;
	}
	return false;
}

/* Interseca due elenchi separati da virgole, nell'ordine del CLIENT (§4.3:
 * «chi sceglie e' il server, dentro l'intersezione, seguendo l'ordine di
 * preferenza del client»).  Restituisce la prima voce comune, o NULL.
 *
 * ⛔ `scarti` raccoglie le voci che si buttano perche' non le conosciamo.  §4.3
 *    dice che si scartano; ⚠ ma uno scarto che non si scrive e' una
 *    negoziazione riuscita con dentro il contrario di quel che si voleva —
 *    trappola 4 di `LEZIONI.md` §4 — e il sintomo arriva mesi dopo, sotto forma
 *    di «va piano e non si capisce perche'».
 *
 * ⛔⭐ E TRE SCARTI NON PASSAVANO DA `scarti` — rilievo R9.12, cioe' tre
 *    tolleranze silenziose dentro la funzione che il registro lo cura:
 *
 *      una voce lunga ≥ 31 byte: `n + 1 < cap` era falso, perche' `cap` e'
 *      `sizeof s->codec` = 32 — e quella condizione governava la
 *      CLASSIFICAZIONE, non solo la scelta.  La voce non veniva confrontata,
 *      non veniva scelta e non finiva negli scarti;
 *      una voce vuota (`hevc,,av1`): idem;
 *      le voci che non entravano nel buffer degli scarti: scartate due volte,
 *      e la seconda in silenzio.
 *
 *    `video.codec = av1,questo.codec.ha.un.nome.lunghissimo` sceglieva `av1` e
 *    scriveva `negoziato video.codec=av1` **senza** la riga degli scarti: il
 *    giorno in cui un client di domani offrira' un codec dal nome lungo, il
 *    registro — che §4.3 dichiara «l'unico posto in cui quel fatto compare» —
 *    non lo conterrebbe.  §3: «una tolleranza silenziosa e' indistinguibile da
 *    un difetto».
 *
 * ⭐ `*quanti` conta TUTTI gli scarti, anche quelli che nel buffer non ci
 *    stanno: il numero dice il vero anche quando l'elenco e' troncato. */
static const char *prima_comune(const char *elenco_client, const char *nostro,
                                char *fuori, size_t cap, char *scarti,
                                size_t cap_scarti, int *quanti)
{
	if (scarti && cap_scarti)
		scarti[0] = 0;
	*quanti = 0;
	const char *scelta = NULL;
	const char *p = elenco_client;
	while (*p) {
		const char *virgola = strchr(p, ',');
		size_t n = virgola ? (size_t)(virgola - p) : strlen(p);
		/* ⚠ 257 e non 64: un valore di capacita' arriva fino a 256 byte (§4.3),
		 *   e una voce che non ci sta nel buffer del confronto e' proprio la
		 *   voce che spariva. */
		char voce[257];
		const char *da_scartare = NULL;
		if (n == 0) {
			/* `hevc,,av1`: §4.3 vuole le voci separate da virgole, e una voce
			 * vuota non e' una voce.  Non si chiude — non cambia niente di
			 * quel che si negozia — ma si SCRIVE. */
			da_scartare = "(vuota)";
		} else if (n >= sizeof voce) {
			da_scartare = "(voce piu' lunga del valore ammesso)";
		} else {
			memcpy(voce, p, n);
			voce[n] = 0;
			/* ⛔ Una voce sconosciuta DENTRO un elenco si scarta, come si
			 * scarta un nome sconosciuto: e' il meccanismo con cui un
			 * client di domani parlera' a un server di oggi. */
			if (voce_presente(nostro, voce)) {
				/* ⚠ Si tiene la PRIMA comune, ma non si esce: le voci dopo
				 *   vanno comunque classificate, o lo scarto che si scrive
				 *   sarebbe solo quello che precede la scelta. */
				if (!scelta) {
					if (n + 1 > cap) {
						/* ⚠ Non puo' capitare: `nostro` e' una nostra costante
						 *   e le nostre voci sono corte.  Se capitasse, la
						 *   voce non si perde in silenzio — si scarta e si
						 *   scrive, che e' il punto di questo rilievo. */
						da_scartare = voce;
					} else {
						/* ⚠ `%.*s` e non `%s`: al compilatore la lunghezza di
						 *   `voce` e' ignota, e con `%s` avverte di una
						 *   troncatura che la guardia qui sopra ha gia'
						 *   escluso.  Un avviso che si sa innocuo e' un avviso
						 *   che il giorno dopo si smette di leggere. */
						snprintf(fuori, cap, "%.*s", (int)n, voce);
						scelta = fuori;
					}
				}
			} else {
				da_scartare = voce;
			}
		}
		if (da_scartare) {
			(*quanti)++;
			if (scarti && cap_scarti) {
				size_t g = strlen(scarti);
				size_t m = strlen(da_scartare);
				if (g + m + 2 < cap_scarti)
					snprintf(scarti + g, cap_scarti - g, "%s%s", g ? "," : "",
					         da_scartare);
			}
		}
		p = virgola ? virgola + 1 : p + n;
	}
	return scelta;
}

/* Quel che questo server dichiara. */
#define NOSTRO_CODEC "hevc,av1"
#define NOSTRA_PROFONDITA "8,10"
#define NOSTRO_AUDIO "opus,pcm"

static void manda_eccomi(rcp_sessione *s)
{
	uint8_t corpo[1024];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_u16(&w, RCP_VERSIONE);
	sc_u16(&w, 5); /* quante capacita' */
	sc_str(&w, "video.codec");
	sc_str(&w, NOSTRO_CODEC);
	sc_str(&w, "video.profondita");
	sc_str(&w, NOSTRA_PROFONDITA);
	sc_str(&w, "audio.codec");
	sc_str(&w, NOSTRO_AUDIO);
	sc_str(&w, "appunti.testo");
	sc_str(&w, "si");
	/* ⛔ §4.3: `banco.marca` vale `no` in ogni installazione normale, e un
	 * server che la dichiarasse `si` per errore lo scrive nel registro a ogni
	 * avvio.
	 *
	 * ⛔⭐ E LA DICHIARAZIONE SI LEGGE DALL'INTERRUTTORE, NON DA UNA COSTANTE —
	 *    rilievo R9.14.  Qui c'era la stringa `"no"` scritta a mano: portando
	 *    `BANCO_ACCESO` a 1 — l'unico modo previsto oggi per accendere la
	 *    funzione — il server ACCETTAVA `BANCO_MARCA` e dipingeva sul desktop
	 *    di qualcuno mentre il suo `ECCOMI` continuava a dichiarare `no`.  Due
	 *    luoghi che devono cambiare insieme e nessun legame fra i due: §7.5
	 *    regola 3 («il server DEVE dichiararla»), e l'invariante I6.
	 *    ⚠ La riga di registro dell'accensione sta in `rcp_apri()`, che e'
	 *      l'unico «avvio» che questo modulo conosce. */
	sc_str(&w, "banco.marca");
	sc_str(&w, BANCO_ACCESO ? "si" : "no");
	if (!w.pieno)
		manda_messaggio(s, T_ECCOMI, corpo, w.len);
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐ `video.misura_massima` — IL TETTO DEL DECODIFICATORE (§4.3, §4.5)
 *
 * Legge `LARGHEZZAxALTEZZA` in **pixel**, cioe' due interi decimali separati da
 * una `x` minuscola e nient'altro.  Restituisce `false` se la stringa non ha
 * quella forma.
 *
 * ⛔ E la forma si controlla per intero, cifra per cifra, invece di fidarsi di
 *    `sscanf("%ux%u")`: quello accetta `1080.75x2340.25` leggendo `1080` e
 *    fermandosi al punto, cioe' prenderebbe per buono un tetto che il client
 *    non ha dichiarato.  ⚠ E' esattamente il valore che la nostra pagina
 *    spediva prima del 10 agosto 2026 notte (rilievo B-6): un telefono a
 *    fattore 2,75 manda `1080.75x2340.25`.
 *
 * ⚠ Zero non e' una misura: un tetto di 0 pixel non e' rispettabile da nessuna
 *   tela legale, e trattarlo come un numero farebbe congedare ogni `ATTACCA`
 *   con `SESSIONE_NON_SERVIBILE` senza che niente nomini il campo. */
static bool misura_massima_legge(const char *v, uint32_t *l, uint32_t *a)
{
	unsigned long long n[2] = {0, 0};
	int quante[2] = {0, 0};
	int i = 0;

	for (const char *p = v; *p; p++) {
		if (*p == 'x' && i == 0) {
			i = 1;
			continue;
		}
		if (*p < '0' || *p > '9')
			return false;
		if (quante[i] > 9) /* piu' di dieci cifre: fuori da qualunque schermo */
			return false;
		n[i] = n[i] * 10u + (unsigned)(*p - '0');
		quante[i]++;
	}
	if (i != 1 || quante[0] == 0 || quante[1] == 0)
		return false;
	if (n[0] == 0 || n[1] == 0 || n[0] > 0xffffffffull || n[1] > 0xffffffffull)
		return false;
	*l = (uint32_t)n[0];
	*a = (uint32_t)n[1];
	return true;
}

/* ------------------------------------------------------------------------ */
/* Quanti nomi di capacita' SCONOSCIUTI questo server sa ricordare per il
 * controllo dei duplicati di §4.3 — vedi il riquadro dentro `tratta_ciao()`. */
#define MAX_VISTI 64

static bool tratta_ciao(rcp_sessione *s, lettore *l)
{
	uint16_t versione = le_u16(l);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "CIAO senza versione");
		return false;
	}
	/* ⛔ §2.4: «le due DEVONO coincidere» — il percorso `/rcp/1` dice 1, e un
	 * `CIAO(2)` su quel percorso e' VERSIONE_INCOMPATIBILE, **non una
	 * negoziazione da risolvere**.
	 *
	 * ⚠ E qui `RCP.md` si contraddice, ed e' la seconda contraddizione trovata
	 *   in questo documento da un banco (la prima fu il trattino basso di §4.3,
	 *   trovata dal validatore di B4).  §9 dice: *«il server sceglie la piu'
	 *   alta che sa parlare e che non superi quella del CIAO»* — cioe' 1, e un
	 *   `ECCOMI(1)`.  §2.4 dice `VERSIONE_INCOMPATIBILE`.  Le due regole danno
	 *   **byte diversi sul filo per lo stesso ingresso**, e nessuna delle due
	 *   cita l'altra.
	 *
	 * ⭐ Vince §2.4, perche' e' la piu' specifica e perche' e' quella scritta
	 *    per risolvere proprio questo caso (rilievo R1.24).  ⚠ Il primo giro di
	 *    questo modulo aveva applicato §9 alla lettera e ACCETTAVA un CIAO(2):
	 *    lo ha trovato B5.  Sta in `fasi/01-filo-nudo.md`.
	 *
	 * ⚠ E il confronto e' con la versione del PERCORSO, che qui e' l'unica che
	 *   il server serve.  Un server che servisse `/rcp/1` e `/rcp/2` passerebbe
	 *   di qui la versione del percorso, non una costante. */
	if (versione != RCP_VERSIONE) {
		congeda(s, RCP_VERSIONE_INCOMPATIBILE,
		        "la versione del CIAO non e' quella del percorso");
		return false;
	}
	uint16_t quante = le_u16(l);
	/* ⛔⭐ LA MEMORIA DEI NOMI GIA' VISTI AVEVA UN FONDO, E OLTRE IL FONDO
	 *    «VINCEVA L'ULTIMO» — rilievo R9.6.
	 *
	 *    §4.3: «un nome ripetuto due volte e' ERRORE_PROTOCOLLO.  "Vince
	 *    l'ultimo" e "vince il primo" sono due implementazioni diverse dello
	 *    stesso documento».  `quante` e' un `u16`: il client puo' dichiarare
	 *    fino a 65 535 capacita', e qui se ne ricordavano 32 — con un `if`
	 *    senza `else` e senza una riga di registro.  Un `CIAO` con 32 capacita'
	 *    dal nome lecito e sconosciuto seguite da `video.codec=hevc` e
	 *    `video.codec=av1` non veniva congedato: `snprintf` girava due volte e
	 *    **vinceva la seconda**.  ⚠ Il caso `capacita-ripetuta` di B5 usa TRE
	 *    capacita': resta verde per sempre.
	 *
	 * ⭐ La cura ha due meta', perche' i due casi non pesano uguale:
	 *
	 *    i nomi CONOSCIUTI — i nove di §4.3 — si ricordano **tutti, sempre**,
	 *    in una maschera di bit.  Sono quelli che cambiano il comportamento, e
	 *    il duplicato che fa danno e' il loro;
	 *
	 *    i nomi SCONOSCIUTI si ricordano fino a `MAX_VISTI`, e oltre quel
	 *    numero ⛔ **si scrive nel registro** che da li' in poi la ripetizione
	 *    di un nome sconosciuto non e' piu' rilevabile.  §3: «ogni tolleranza
	 *    va scritta nel registro; una tolleranza silenziosa e' indistinguibile
	 *    da un difetto».
	 *
	 * ⚠ Perche' non si chiude e basta quando la memoria finisce: un `CIAO` con
	 *   quattrocento capacita' sconosciute e' CONFORME (§6.1), e §3 eccezione 1
	 *   impone di ignorarle e proseguire.  Chiudere sarebbe un rosso sul codice
	 *   giusto del client di domani — il difetto opposto, e costa di piu'. */
	static const char *const NOMI_NOTI[] = {
	    "video.codec",   "video.profondita", "video.livello",
	    "video.misura_massima", "audio.codec", "input.tocco",
	    "appunti.testo", "client.nome",      "banco.marca",
	    NULL};
	char visti[MAX_VISTI][65];
	int n_visti = 0;
	uint16_t visti_noti = 0;
	bool detta_la_memoria_finita = false;
	char c_codec[257] = "", c_prof[257] = "", c_audio[257] = "";
	char c_misura[257] = "";
	for (uint16_t k = 0; k < quante; k++) {
		char nome[65], valore[257];
		size_t ln = le_str(l, nome, sizeof nome);
		size_t lv = le_str(l, valore, sizeof valore);
		if (l->corto) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "elenco delle capacita' troncato");
			return false;
		}
		if (!nome_lecito(nome, ln)) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "nome di capacita' fuori forma");
			return false;
		}
		if (lv == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "capacita' con valore vuoto");
			return false;
		}
		/* ⚠ L'ordine dei due termini del `||` non e' indifferente e non si
		 *   tocca: `lv > 256` PRIMA impedisce a `testo_stampabile` di leggere
		 *   oltre il buffer quando la stringa non ci sta (vedi il commento di
		 *   `le_str`, e il sospetto R9.18 che resta aperto). */
		if (lv > 256 || !testo_stampabile(valore, lv)) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "valore di capacita' non valido");
			return false;
		}
		/* ⛔ Un nome ripetuto e' ERRORE_PROTOCOLLO: «vince l'ultimo» e «vince
		 * il primo» sono due implementazioni dello stesso documento. */
		bool ripetuto = false;
		int noto = -1;
		for (int i = 0; NOMI_NOTI[i]; i++)
			if (strcmp(NOMI_NOTI[i], nome) == 0) {
				noto = i;
				break;
			}
		if (noto >= 0) {
			ripetuto = (visti_noti >> noto) & 1u;
			visti_noti |= (uint16_t)(1u << noto);
		} else {
			for (int i = 0; i < n_visti; i++)
				if (strcmp(visti[i], nome) == 0) {
					ripetuto = true;
					break;
				}
			if (n_visti < MAX_VISTI) {
				snprintf(visti[n_visti++], sizeof visti[0], "%s", nome);
			} else if (!detta_la_memoria_finita) {
				detta_la_memoria_finita = true;
				reg(s, "⚠ oltre %d capacita' dal nome sconosciuto: da qui in "
				       "poi la RIPETIZIONE di un nome sconosciuto non e' piu' "
				       "rilevabile (§4.3), e i nomi di §4.3 lo restano tutti",
				    MAX_VISTI);
			}
		}
		if (ripetuto) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "capacita' ripetuta");
			return false;
		}
		/* ⛔ Una capacita' del lato sbagliato e' ERRORE_PROTOCOLLO: il nome e'
		 * conosciuto, quindi l'eccezione dei nomi sconosciuti non la copre. */
		if (strcmp(nome, "banco.marca") == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "banco.marca non arriva dal client");
			return false;
		}
		if (strcmp(nome, "video.codec") == 0)
			snprintf(c_codec, sizeof c_codec, "%s", valore);
		else if (strcmp(nome, "video.profondita") == 0)
			snprintf(c_prof, sizeof c_prof, "%s", valore);
		else if (strcmp(nome, "audio.codec") == 0)
			snprintf(c_audio, sizeof c_audio, "%s", valore);
		else if (strcmp(nome, "video.misura_massima") == 0)
			snprintf(c_misura, sizeof c_misura, "%s", valore);
	}
	/* ⛔⭐ IL TETTO DEL DECODIFICATORE SI CONSERVA — rilievo B-1, 10 agosto
	 *     2026 notte.  §4.5: «la tela concessa DEVE rispettare
	 *     `video.misura_massima` se il client l'ha dichiarata», e §4.3: «non
	 *     cambia la tela: e' un tetto […] perche' il decodificatore di un
	 *     telefono ha limiti che il suo schermo non dichiara».
	 *
	 * ⛔ Prima di oggi questo valore veniva riconosciuto come nome lecito e poi
	 *    **buttato**: il server concedeva esattamente quel che il client
	 *    chiedeva, anche il doppio di quel che aveva dichiarato di saper
	 *    decodificare.  ⚠ E il sintomo non e' un errore di rete: e' «il browser
	 *    non apre il flusso» alla fase 2, con la diagnosi puntata sul
	 *    codificatore.
	 *
	 * ⛔ E un valore FUORI FORMA non si prende per buono e non si butta in
	 *    silenzio: §3 eccezione 1 permette di ignorare un valore che non si
	 *    capisce, e la riga sotto quella tabella impone di **scriverlo nel
	 *    registro** — «una tolleranza silenziosa e' indistinguibile da un
	 *    difetto». */
	if (c_misura[0]) {
		if (misura_massima_legge(c_misura, &s->max_l, &s->max_a)) {
			reg(s, "il client dichiara video.misura_massima=%ux%u: e' il tetto "
			       "che la tela concessa DEVE rispettare (§4.5)",
			    s->max_l, s->max_a);
		} else {
			s->max_l = s->max_a = 0;
			reg(s, "⚠ TOLLERANZA (§3 eccezione 1): video.misura_massima=«%s» "
			       "non ha la forma LARGHEZZAxALTEZZA di §4.3 (pixel interi) — "
			       "il valore si ignora, e la tela NON avra' nessun tetto",
			    c_misura);
		}
	}

	/* ⛔ §4.3: `pcm` e `8` DEVONO essere dichiarati da ENTRAMBI — `pcm` e' la
	 * base sempre disponibile, e serve da controllo positivo quando Opus non si
	 * negozia.  ⚠ E chi non li dichiara si congeda con NIENTE_IN_COMUNE, **non**
	 * con ERRORE_PROTOCOLLO: non ha sbagliato a scrivere, non ha di che
	 * parlare.  Senza questo controllo l'intersezione basta a se stessa — un
	 * client che offre solo `opus` passa — e la riga di §4.3 non la applica
	 * nessuno. */
	if (!voce_presente(c_audio, "pcm")) {
		congeda(s, RCP_NIENTE_IN_COMUNE,
		        "il client non dichiara pcm in audio.codec");
		return false;
	}
	if (!voce_presente(c_prof, "8")) {
		congeda(s, RCP_NIENTE_IN_COMUNE,
		        "il client non dichiara 8 in video.profondita");
		return false;
	}
	/* ⛔ Se l'intersezione e' vuota si congeda con NIENTE_IN_COMUNE, non con
	 * ERRORE_PROTOCOLLO: non ha sbagliato a scrivere, non ha di che parlare. */
	char sc_codec[257], sc_prof[257], sc_audio[257];
	int n_codec = 0, n_prof = 0, n_audio = 0;
	if (!prima_comune(c_codec, NOSTRO_CODEC, s->codec, sizeof s->codec,
	                  sc_codec, sizeof sc_codec, &n_codec) ||
	    !prima_comune(c_prof, NOSTRA_PROFONDITA, s->profondita,
	                  sizeof s->profondita, sc_prof, sizeof sc_prof, &n_prof) ||
	    !prima_comune(c_audio, NOSTRO_AUDIO, s->audio, sizeof s->audio,
	                  sc_audio, sizeof sc_audio, &n_audio)) {
		congeda(s, RCP_NIENTE_IN_COMUNE, "nessun codec condiviso");
		return false;
	}
	/* ⛔ La scelta si SCRIVE: una negoziazione riuscita con dentro il
	 * contrario di quel che si voleva si vede solo se qualcuno la scrive. */
	reg(s, "negoziato video.codec=%s video.profondita=%s audio.codec=%s",
	    s->codec, s->profondita, s->audio);
	/* ⛔ E lo SCARTO si scrive a sua volta: «ho scelto hevc» non dice che vp9
	 * e' stato buttato, e il giorno in cui il client di domani offrira' un
	 * codec che questo server non conosce, il registro e' l'unico posto in cui
	 * quel fatto compare. */
	/* ⚠ E si scrive anche QUANTE sono, non solo quali: l'elenco puo' essere
	 *   troncato dal buffer, il numero no (rilievo R9.12). */
	if (n_codec || n_prof || n_audio)
		reg(s, "scartate voci sconosciute: video.codec=[%s] (%d) "
		       "video.profondita=[%s] (%d) audio.codec=[%s] (%d)",
		    sc_codec, n_codec, sc_prof, n_prof, sc_audio, n_audio);
	manda_eccomi(s);
	s->stato = S_ATTESA_CREDENZIALI;
	return true;
}

static bool tratta_credenziali(rcp_sessione *s, lettore *l, uint64_t ora)
{
	char utente[257], parola[1025];
	size_t lu = le_str(l, utente, sizeof utente);
	size_t lp = le_str(l, parola, sizeof parola);
	/* ⛔ LA COPIA LOCALE SI AZZERA SU OGNI STRADA, NON SOLO SU QUELLA BUONA —
	 * rilievo R9.8.  Il `memset` stava in fondo, dopo la risposta di PAM: su
	 * ogni cammino d'errore che congeda qui sotto — utente non UTF-8, utente o
	 * parola fuori intervallo — la parola restava sullo stack.  Il caso
	 * `utente-vuoto` di B5 e' proprio questo: parola di 1024 byte, utente di
	 * zero, e si esce da qui.  ⚠ Le tre righe ripetute sono volute: un `goto`
	 * di uscita comune si legge peggio di tre righe che dicono la stessa cosa
	 * dove capita di guardare. */
	if (l->corto) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO, "CREDENZIALI troncate");
		return false;
	}
	/* §4.4: gli intervalli.  Una stringa vuota e' legale per §6.0, e senza
	 * questi limiti `CREDENZIALI` con due stringhe di zero byte sarebbe
	 * conforme — e un attaccante non incrementerebbe nessun contatore. */
	if (lu < 1 || lu > 256 || lp < 1 || lp > 1024) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO, "utente o parola fuori intervallo");
		return false;
	}
	/* ⛔ §4.3 vale per le capacita', ma la ragione di `testo_stampabile` vale
	 * qui piu' che altrove (rilievo R9.11): un `root\0nemo` di nove byte
	 * passava gli intervalli, passava `utf8_valido`, e mandava a PAM `root`.
	 * Quel che e' arrivato e quel che si giudica devono essere la stessa
	 * stringa, o il registro e la chiave di §4.4-bis nominano un utente che
	 * sul filo non c'era. */
	if (!testo_stampabile(utente, lu)) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "l'utente non e' testo UTF-8 stampabile");
		return false;
	}
	/* ⚠ Della parola si controlla SOLO il byte nullo, e la ragione e' la
	 *   stessa: con uno zero in mezzo PAM giudicherebbe un prefisso di quel
	 *   che e' arrivato.  ⛔ Non si pretende che sia stampabile: §4.4 non lo
	 *   chiede, e una parola d'ordine puo' contenere quel che vuole. */
	if (strlen(parola) != lp) {
		memset(parola, 0, sizeof parola);
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "la parola contiene un byte nullo: quel che arriva e quel che "
		        "si giudicherebbe sarebbero due cose diverse");
		return false;
	}
	snprintf(s->utente, sizeof s->utente, "%s", utente);
	/* ⛔ Tre righe di strumentazione, e non sono di passaggio: il 10 agosto
	 * 2026 la stretta di mano si fermava qui e «CREDENZIALI non e' arrivato»
	 * e «PAM non risponde» avevano lo stesso aspetto — cioe' nessuno.
	 * ⚠ La parola NON compare, a nessun livello (§4.4) — e da oggi nemmeno la
	 *   sua LUNGHEZZA ESATTA, che qui c'era: §11.1 tratta il registro come un
	 *   file che si conserva, e la lunghezza di ogni parola d'ordine provata,
	 *   riuscita o no, non e' una cosa da conservare (rilievo R9.8).  Per
	 *   distinguere «non e' arrivato» da «PAM non risponde» basta questa
	 *   riga. */
	reg(s, "CREDENZIALI ricevute utente=%s (con parola)", s->utente);

	/* ⛔ Il limitatore PRIMA di PAM, e il rifiuto e' subito: §4.4-bis dice che
	 * l'attesa e' una FINESTRA in cui si rifiuta, non un ritardo — con un solo
	 * tentativo per connessione, un server che ritardasse di quindici minuti
	 * non consegnerebbe mai il rifiuto. */
	uint64_t restano = 0;
	/* ⛔⭐ E DA QUI IN GIU' SI PARTE DA NEGATO, SEMPRE — invariante I3.
	 *
	 * Prima del 12 agosto 2026 `cred_buone` prendeva il suo valore dentro
	 * l'unico `else` qui sotto, e non c'era nessun'altra strada: PAM aveva
	 * gia' risposto quando questa funzione tornava.  ⚠ Adesso le strade sono
	 * quattro — bannato, aiutante che non prende la domanda, verifica
	 * sincrona di ripiego, e la strada buona che ASPETTA — e tre di esse
	 * escono da qui senza nessun verdetto in mano.  Un campo lasciato al suo
	 * valore precedente su una di quelle strade sarebbe un «si'» arrivato per
	 * inerzia. */
	s->cred_buone = false;
	s->cred_motivo = RCP_CREDENZIALI_ERRATE;
	s->verdetto_atteso = false;
	s->no_e_nostro = false;
	if (bannato(s->indirizzo, ora, &restano)) {
		/* ⛔ Il ban rifiuta SENZA interrogare PAM, e va saputo leggendo il
		 * motivo sul filo: `TROPPI_TENTATIVI` e `CREDENZIALI_ERRATE` non
		 * possono venire dalla stessa strada.  ⭐ E' il byte che il 10 agosto
		 * 2026 ha separato i due imputati di B8 — chi legge un
		 * `CREDENZIALI_ERRATE` sta guardando PAM, non questa riga. */
		s->cred_buone = false;
		s->cred_motivo = RCP_TROPPI_TENTATIVI;
		reg(s, "⛔ indirizzo %s BANNATO: restano %llu minuti, PAM non viene "
		       "interrogata (§4.4-bis)",
		    s->indirizzo, (unsigned long long)(restano / 60000u));
	} else if (s->g.chiedi_verifica) {
		/* ⭐⭐ LA STRADA BUONA — `DECISIONI.md` §1.10, 12 agosto 2026.
		 *
		 * ⛔ Qui NON si aspetta PAM.  Si chiede a un processo aiutante e si
		 *    torna subito a chi ospita, che torna al suo `poll`: e' l'unico
		 *    modo per cui «mentre uno si autentica, gli altri non se ne
		 *    accorgono» possa essere vero su un server a un filo solo.
		 *
		 * ⚠ E il conto di §4.4-bis NON si muove qui: adesso si sa che si e'
		 *   chiesto, non che cosa e' stato risposto.  Si muove in
		 *   `rcp_verdetto()`, che e' il punto in cui il fatto esiste. */
		if (s->g.chiedi_verifica(s->g.ctx, utente, parola, &s->pratica)) {
			s->verdetto_atteso = true;
			reg(s, "PAM chiesta all'aiutante, pratica %llu: il filo resta "
			       "libero (DECISIONI.md §1.10)",
			    (unsigned long long)s->pratica);
		} else {
			/* ⛔ LA DOMANDA NON E' PARTITA ⇒ NO, subito.  E' I3 alla lettera:
			 *    «progetta perche' il fallimento sia un no, non un forse».
			 * ⚠ E non conta come tentativo fallito: il difetto e' NOSTRO, e
			 *   §4.4-bis elenca fra le cose che non bannano proprio quelle che
			 *   «bannerebbero qualcuno che non ha sbagliato niente». */
			s->no_e_nostro = true;
			reg(s, "⛔ la domanda a PAM non e' partita: RESPINTO senza appello "
			       "(invariante I3).  ⚠ E NON conta come tentativo fallito di "
			       "§4.4-bis: il difetto e' nostro, e un ban per un difetto "
			       "nostro sarebbe la peggiore diagnosi possibile");
		}
	} else {
		/* ⚠ IL RIPIEGO DICHIARATO (`CODER.md` §4.2), e blocca chi lo chiama:
		 *   e' la strada dei banchi in-processo, dove non c'e' nessun ciclo da
		 *   liberare — e il GUASTO che `banchi/02-pam-*` innesta per
		 *   certificarsi, perche' e' esattamente com'era il server prima. */
		bool ok = s->g.verifica && s->g.verifica(s->g.ctx, utente, parola);
		reg(s, "PAM ha risposto: %s  ⚠ (per via SINCRONA: nessun gancio "
		       "asincrono collegato — il filo e' rimasto fermo)",
		    ok ? "ammesso" : "respinto");
		s->cred_buone = ok;
		s->cred_motivo = RCP_CREDENZIALI_ERRATE;
		/* ⛔ Il conto e' sull'INDIRIZZO e basta: il nome utente non conta
		 * (`DECISIONI.md` §1.9).  Tre nomi diversi contano tre. */
		if (ok)
			azzera_falliti(s, s->indirizzo, ora);
		else
			segna_fallito(s, s->indirizzo, ora);
	}
	/* ⛔ La parola si azzera appena PAM ha risposto, e non compare in nessun
	 * registro a nessun livello (§4.4).
	 * ⚠ Questo azzera la COPIA locale.  L'originale e' arrivato dentro `s->acc`
	 *   e ci resta finche' il messaggio non viene consumato: la coda
	 *   dell'accumulo si azzera in `drena()`, e quel che avanza in
	 *   `rcp_libera()`.  Erano tutti e due scoperti (rilievo R9.8).
	 * `[?]` ⚠ E un compilatore che ottimizza e' AUTORIZZATO a togliere questo
	 *   `memset`, perche' `parola` non viene piu' letta: la cura conosciuta e'
	 *   `explicit_bzero()`, ma prima si guarda l'assembly del binario che gira
	 *   (sospetto R9.20 — e' una misura, non una riscrittura sulla parola). */
	memset(parola, 0, sizeof parola);

	s->cred_arrivo = ora;
	s->stato = S_ATTESA_VERDETTO;
	s->da_quando = ora;
	return true;
}

static bool disposizione_ben_formata(const char *d, size_t n)
{
	/* §4.5: un nome XKB, eventualmente con la variante fra parentesi. */
	if (n < 1 || n > 64)
		return false;
	size_t i = 0;
	while (i < n && ((d[i] >= 'a' && d[i] <= 'z') || (d[i] >= '0' && d[i] <= '9')))
		i++;
	if (i == 0)
		return false;
	if (i == n)
		return true;
	if (d[i] != '(' || d[n - 1] != ')')
		return false;
	for (size_t k = i + 1; k + 1 < n; k++)
		if (!((d[k] >= 'a' && d[k] <= 'z') || (d[k] >= '0' && d[k] <= '9') ||
		      d[k] == '_' || d[k] == '-'))
			return false;
	return true;
}

/* ⛔ §4.5 distingue DUE guasti, e vuole due motivi diversi:
 *
 *   fuori forma            ERRORE_PROTOCOLLO     — ha sbagliato a scrivere
 *   ben formata, ignota    SESSIONE_NON_SERVIBILE — ha scritto bene una cosa
 *                                                   che questa macchina non ha
 *
 * ⚠ Un server che li unisse darebbe `ERRORE_PROTOCOLLO` a chi ha una tastiera
 *   svedese su una macchina senza il pacchetto XKB svedese, e il sintomo
 *   sarebbe «il client e' rotto» invece di «alla macchina manca una
 *   disposizione».
 *
 * `[?]` ⚠ **E l'elenco qui sotto e' della fase 1, e va dichiarato.** «Che cosa
 *   il sistema conosce» lo sa il sistema, non RCP: un server vero lo chiede a
 *   XKB.  In fase 1 non c'e' nessun compositore (`SESSIONE` dichiara
 *   `desktop=sconosciuto`), quindi non c'e' nessuno a cui chiedere, e la
 *   scelta e' un elenco fisso.  ⛔ Quel che il banco prova e' **che i due
 *   guasti siano distinti**, non quali disposizioni esistano: il giorno in cui
 *   la domanda andra' a XKB, questa funzione cambia e B5 resta com'e'. */
static bool disposizione_conosciuta(const char *d)
{
	static const char *NOTE[] = {"it", "us", "gb", "de", "fr", "es", "pt",
	                             "ru", "se", "no", "dk", "fi", "pl", "cz",
	                             "ch", "at", "be", "nl", "br", "jp", NULL};
	/* La variante fra parentesi non cambia la disposizione: `de(neo)` e' `de`
	 * con un'altra mappa, e chi ha `de` ha le due. */
	size_t n = 0;
	while (d[n] && d[n] != '(')
		n++;
	for (int i = 0; NOTE[i]; i++)
		if (strlen(NOTE[i]) == n && strncmp(NOTE[i], d, n) == 0)
			return true;
	return false;
}

static bool tratta_attacca(rcp_sessione *s, lettore *l)
{
	uint32_t tl = le_u32(l), ta = le_u32(l);
	/* ⛔ §7.1: la vista NON ha i vincoli della tela — «qualunque misura da 1x1
	 * in su e' legale, dispari compresa» (rilievo R1.17).  Qui non si controlla
	 * NIENTE, ed e' voluto.
	 *
	 * ⚠ Chi scrive `ATTACCA` in C scrive UNA `valida_misura()` e la chiama
	 *   quattro volte: e' la cosa naturale da fare, e produce un server che
	 *   **chiude la sessione perche' l'utente ha stretto la finestra**.  Su un
	 *   telefono a fattore 2,75 la vista e' dispari quasi sempre — 393 pixel
	 *   logici valgono 1080,75 fisici (rilievo R4.10).  B5 lo prova con
	 *   `300x801` e `1x1`, che DEVONO passare. */
	uint32_t vl = le_u32(l), va = le_u32(l);
	char disp[65];
	size_t ld = le_str(l, disp, sizeof disp);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "ATTACCA troncato");
		return false;
	}
	/* ⛔ I limiti e la parita' sono normativi: una misura dispari la
	 * arrotonda il codificatore, in silenzio — due misure diverse sotto la
	 * stessa etichetta, che e' la forma E2. */
	if (tl < 320 || tl > 7680 || ta < 240 || ta > 4320 || (tl % 2) || (ta % 2)) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "tela fuori dai limiti o dispari");
		return false;
	}
	if (!disposizione_ben_formata(disp, ld)) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "disposizione fuori forma");
		return false;
	}
	if (!disposizione_conosciuta(disp)) {
		/* ⛔ §8.2: SESSIONE_NON_SERVIBILE «DEVE portare il dettaglio nel
		 * corpo», e `congeda()` ce lo mette.  Il dettaglio NON si mostra
		 * all'utente (§8.2): la frase la costruisce il client dal codice. */
		char d[128];
		snprintf(d, sizeof d, "disposizione sconosciuta a questa macchina: %s",
		         disp);
		congeda(s, RCP_SESSIONE_NON_SERVIBILE, d);
		return false;
	}

	/* ⛔⭐ §5.1 di `SPECIFICHE.md`, motivo `0x05 GIA_ATTIVA_LOCALE` — e viene
	 *     PRIMA del posto, di proposito.
	 *
	 * ⛔ Chiedere il posto e poi rilasciarlo avrebbe lo stesso esito per questo
	 *    client e uno DIVERSO per il registro: per un istante il posto
	 *    risulterebbe occupato da chi sta per essere respinto, e un altro
	 *    client dello stesso utente che arrivasse in quell'istante leggerebbe
	 *    `0x0F` — «hai gia' una sessione attaccata» — che e' falso.
	 *
	 * ⚠ E il gancio e' opzionale: se non c'e', la regola NON e' applicata, e la
	 *   riga di registro lo dice.  «Nessuna sessione locale» e «nessuno ha
	 *   guardato» sono due fatti diversi (`LEZIONI.md` §1.9 regola 1). */
	if (s->g.sessione_locale) {
		char quale[160];

		quale[0] = '\0';
		if (s->g.sessione_locale(s->g.ctx, s->utente, quale, sizeof quale)) {
			reg(s, "⛔ attacco NEGATO a %s da %s: ha gia' una sessione "
			       "grafica LOCALE (%s) — §5.1, motivo 0x05",
			    s->utente, s->provenienza,
			    quale[0] ? quale : "senza dettaglio");
			/* ⛔ Il dettaglio del corpo NON nomina la sessione altrui:
			 * §8.2 dice che cosa il client puo' sapere. */
			congeda(s, RCP_GIA_ATTIVA_LOCALE,
			        "c'e' gia' una sessione grafica locale di questo "
			        "utente");
			return false;
		}
	} else {
		reg(s, "⚠ nessun gancio «sessione_locale»: la regola di §5.1 (motivo "
		       "0x05) NON e' applicata su questo server");
	}

	/* ⛔ §8.2 motivo 0x0F: chi viene rifiutato e' chi ARRIVA, non chi c'era. */
	/* ⛔ Il posto si CHIEDE, e l'esito si scrive con quanti erano occupati.
	 * ⚠ Il 10 agosto 2026 il terzo giro di B3 non riusciva a distinguere «il
	 *   server non guarda il registro» da «il posto era gia' stato liberato»:
	 *   sono due difetti opposti, e senza questa riga danno lo stesso rosso. */
	/* ⛔ E i due modi di non avere un posto NON hanno lo stesso motivo — vedi
	 * il riquadro sopra `posto_prendi()`, rilievo R9.3. */
	switch (posto_prendi(s->utente)) {
	case POSTO_PRESO:
		break;
	case POSTO_OCCUPATO:
		reg(s, "posto NEGATO a %s da %s: lo occupa un altro client di questo "
		       "stesso utente (occupati: %d)",
		    s->utente, s->provenienza, posti_occupati());
		congeda(s, RCP_GIA_ATTIVA_REMOTA,
		        "c'e' gia' un client attaccato a questa sessione");
		return false;
	case POSTO_NIENTE_PIU_POSTI:
		/* ⛔ §8.2 `0x0E`: «ben formato ma non si puo' servire», e DEVE portare
		 * il dettaglio nel corpo — che `congeda()` ci mette.  ⚠ Dire `0x0F` a
		 * quest'utente sarebbe dirgli «hai gia' una sessione altrove», che e'
		 * falso: non ne ha nessuna, e' il server a non avere piu' posti. */
		reg(s, "⛔ posto NEGATO a %s da %s: il registro delle sessioni di "
		       "questo server e' PIENO (%d su %d) — NON e' 0x0F, quest'utente "
		       "non ha nessuna sessione altrove",
		    s->utente, s->provenienza, posti_occupati(), MAX_ATTACCATE);
		congeda(s, RCP_SESSIONE_NON_SERVIBILE,
		        "il registro delle sessioni di questo server e' pieno");
		return false;
	}
	s->attaccata = true;
	reg(s, "posto PRESO da %s via %s (occupati adesso: %d)", s->utente,
	    s->provenienza, posti_occupati());

	/* ⛔⭐ LA TELA CONCESSA RISPETTA `video.misura_massima` — §4.5, rilievo B-1
	 *
	 *     «La tela concessa DEVE rispettare `video.misura_massima` se il client
	 *     l'ha dichiarata, e rispettare comunque i limiti e la parita' di
	 *     sopra.»  Sono due vincoli, e vanno soddisfatti tutti e due: non basta
	 *     dividere.
	 *
	 * ⚠ Si riduce mantenendo le PROPORZIONI, e non si taglia ogni lato al suo
	 *   tetto: tagliare i lati indipendentemente cambierebbe il rapporto della
	 *   tela e il desktop remoto arriverebbe schiacciato — un difetto che si
	 *   VEDE e che nessun codice d'errore nomina.  §4.5 lo permette
	 *   esplicitamente: «la tela concessa puo' essere diversa da quella
	 *   chiesta […] il client DEVE adattarsi riscalando».
	 *
	 * ⛔ E il ripiego SI SCRIVE NEL REGISTRO — la stessa riga di §4.5 lo impone
	 *    per il ripiego di KDE, e vale identica qui: una tela diversa da quella
	 *    chiesta, senza una riga che dica perche', e' indistinguibile da un
	 *    errore di calcolo.
	 *
	 * ⚠ E se nemmeno la tela MINIMA legale (320x240) sta sotto il tetto, non si
	 *   concede una tela illegale e non si tace: §4.5 «se l'attacco non si puo'
	 *   servire, il server congeda con uno dei motivi di §8.2 — mai con un
	 *   silenzio». */
	if (s->max_l && (tl > s->max_l || ta > s->max_a)) {
		uint32_t cl = tl, ca = ta;
		uint32_t chiesta_l = tl, chiesta_a = ta;
		/* Il lato che limita di piu': confronto incrociato, senza divisioni
		 * in virgola mobile. */
		if ((uint64_t)tl * s->max_a <= (uint64_t)ta * s->max_l) {
			ca = s->max_a;
			cl = (uint32_t)(((uint64_t)tl * s->max_a) / ta);
		} else {
			cl = s->max_l;
			ca = (uint32_t)(((uint64_t)ta * s->max_l) / tl);
		}
		cl -= cl % 2; /* §4.5: entrambe PARI */
		ca -= ca % 2;
		if (cl < 320)
			cl = 320;
		if (ca < 240)
			ca = 240;
		if (cl > s->max_l || ca > s->max_a) {
			char d[160];
			snprintf(d, sizeof d,
			         "video.misura_massima=%ux%u e' sotto la tela minima "
			         "legale di 320x240 (§4.5)",
			         s->max_l, s->max_a);
			reg(s, "⛔ tela NON concessa a %s: chiesta %ux%u, tetto %ux%u — "
			       "nemmeno 320x240 ci sta sotto",
			    s->utente, chiesta_l, chiesta_a, s->max_l, s->max_a);
			congeda(s, RCP_SESSIONE_NON_SERVIBILE, d);
			return false;
		}
		tl = cl;
		ta = ca;
		reg(s, "⚠ RIPIEGO DICHIARATO (§4.5): tela chiesta %ux%u, tetto del "
		       "decodificatore %ux%u (video.misura_massima) — CONCESSA %ux%u, "
		       "proporzioni tenute, entrambe pari",
		    chiesta_l, chiesta_a, s->max_l, s->max_a, tl, ta);
	}

	/* ⛔⭐⭐ E PRIMA DI CONCEDERE, SI CHIEDE CHE MISURA HA IL PALCO — la cura
	 *     del RI-ATTACCO, `DECISIONI.md` §5.0-sexies («⏳ per quando si
	 *     affrontera' il ri-attacco: la soluzione e' gia' misurata»).
	 *
	 * ⛔ Il caso: il palco sopravvive al client (invariante I4), la tela nasce a
	 *    ogni attacco (§5.0).  Chi si stacca dal DeX con la tela a 1912x1044 e si
	 *    riattacca dal portatile chiede 1920x1080 — e il palco continua a
	 *    consegnare 1912x1044.  §6.2 vieta di spedire un fotogramma la cui misura
	 *    non e' la tela in vigore ⇒ **zero pixel**, e la sola riga che lo direbbe
	 *    sarebbe «tela in vigore X ma il fotogramma e' Y», detta una volta.
	 *
	 * ⇒ Si concede quel che il palco HA, e §4.5 lo permette per iscritto: «la
	 *   tela concessa puo' essere diversa da quella chiesta».  ⭐ Poi la pagina
	 *   manda il suo `ADATTA_TELA` e si arriva dove si voleva — ma passando per
	 *   uno stato in cui i pixel arrivano invece che per uno in cui non arrivano.
	 *
	 * ⚠ E i limiti si ricontrollano TUTTI, perche' la misura del palco non e'
	 *   passata da questo cancello: §4.5 (320..7680 x 240..4320, pari) e il tetto
	 *   del decodificatore di QUESTO client.  ⛔ Se non li passa non si concede e
	 *   non si tace: se ne occupa `rcp_tela_concessa()`, che al primo fotogramma
	 *   chiedera' al palco di tornare. */
	if (s->g.tela_del_palco) {
		uint32_t pl = 0, pa = 0;
		if (s->g.tela_del_palco(s->g.ctx, &pl, &pa) && pl && pa
		    && (pl != tl || pa != ta)) {
			if (pl < 320 || pl > 7680 || pa < 240 || pa > 4320 || (pl % 2)
			    || (pa % 2))
				reg(s, "⚠ il palco ha la tela %ux%u, che §4.5 non ammette in "
				       "`SESSIONE` (320..7680 x 240..4320, pari): concedo %ux%u "
				       "come chiesto, e al primo fotogramma si chiedera' al "
				       "palco di venire qui",
				    pl, pa, tl, ta);
			else if (s->max_l && (pl > s->max_l || pa > s->max_a))
				reg(s, "⚠ il palco ha la tela %ux%u, oltre il "
				       "video.misura_massima di questo client (%ux%u): concedo "
				       "%ux%u, e al primo fotogramma si chiedera' al palco di "
				       "venire qui",
				    pl, pa, s->max_l, s->max_a, tl, ta);
			else {
				reg(s, "⚠ RIPIEGO DICHIARATO (§4.5): chiesta la tela %ux%u, ma "
				       "il palco di %s ne ha gia' una — %ux%u — e sopravvive al "
				       "client (I4).  CONCESSA quella del palco: cosi' i "
				       "fotogrammi arrivano da subito, e la pagina puo' chiedere "
				       "la sua misura con `ADATTA_TELA`",
				    tl, ta, s->utente, pl, pa);
				tl = pl;
				ta = pa;
			}
		}
	}

	uint8_t corpo[128];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_byte(&w, 1); /* 1 = NUOVA */
	sc_u32(&w, tl);
	sc_u32(&w, ta);
	sc_str(&w, "sconosciuto"); /* il desktop: in fase 1 non c'e' compositore */
	if (!w.pieno) {
		manda_messaggio(s, T_SESSIONE, corpo, w.len);
		/* ⛔⭐ IL CANALE VIDEO SI APRE **QUI**, E NON UNA RIGA PIU' SU.
		 *
		 * §2.5: «uno per fotogramma, ⛔ e **nessuno prima di aver spedito
		 * `SESSIONE`**: chi ne riceve uno prima chiude con
		 * `ERRORE_PROTOCOLLO`».  E' l'invariante **I3** sul filo — *chi non
		 * passa dal validatore non riceve un pixel*.
		 *
		 * ⛔ Le tre righe stanno DENTRO il `if`: se il corpo non fosse entrato
		 *    nel buffer, `SESSIONE` non sarebbe partita, e un canale video
		 *    aperto lo stesso spedirebbe fotogrammi a un client che non sa ne'
		 *    la tela ne' il codec.  ⚠ Fuori dal `if` sembrerebbero uguali e
		 *    non lo sono. */
		s->tela_l = tl;
		s->tela_a = ta;
		s->sessione_spedita = true;
		/* ⛔ §5.2, primo punto: «il primo fotogramma che il server spedisce
		 * dopo `SESSIONE` DEVE essere una chiave». */
		s->serve_chiave = true;
		s->serve_chiave_perche = "e' il primo dopo SESSIONE (§5.2)";
		s->mai_spedita_una_chiave = true;
	}
	reg(s, "sessione aperta utente=%s via=%s tela=%ux%u vista=%ux%u "
	       "disposizione=%s",
	    s->utente, s->provenienza, tl, ta, vl, va, disp);
	s->stato = S_ATTIVA;

	/*
	 * ⭐⭐⭐ E IL PALCO LO SA SUBITO — 16 agosto 2026, e senza questa riga il
	 *      palco nasceva a una misura che nessuno aveva chiesto.
	 *
	 * ⛔ IL DIFETTO, e ha tre facce che sembravano tre difetti: il figlio nasce
	 *    con una tela predefinita (1920x1080) e la cambia solo quando arriva un
	 *    `ADATTA_TELA`.  Finche' la pagina chiedeva 1920x1080 all'`ATTACCA` e si
	 *    correggeva subito dopo, quel messaggio arrivava sempre — ⛔ ma era un
	 *    ballo: ogni sessione nasceva sbagliata e si ridimensionava, e il
	 *    ridimensionamento e' una gara (il fondo di §7.1, il palco che monta,
	 *    `libei` che ricrea i dispositivi).  `[M]` si perdeva una volta su tre.
	 *
	 * ⇒ Curata la pagina — che adesso chiede la finestra fin dall'`ATTACCA`,
	 *   come §5.0-sexies dice dal 14 agosto — il ballo e' sparito **e con lui
	 *   il messaggio**: non c'e' piu' niente da correggere, quindi nessuno
	 *   diceva piu' al figlio quanto e' grande la tela.  ⭐ Il palco nasceva a
	 *   1920x1080 e i fotogrammi si buttavano tutti.
	 *
	 * ⇒ ⭐ Lo dice il SERVER, qui, nell'istante in cui la tela e' decisa.  E'
	 *   il posto giusto per una ragione che vale oltre questo caso: **chi
	 *   decide un numero e' chi deve dirlo a chi lo usa**.  Prima lo diceva il
	 *   client di rimbalzo, e funzionava per accidente.
	 *
	 * ⚠ E non e' un `ADATTA_TELA` mascherato: non risponde a nessun messaggio e
	 *   non manda niente sul filo.  Se il palco quella misura ce l'ha gia' — il
	 *   ri-attacco — il figlio risponde «ce l'ho gia'» e non succede niente.
	 */
	if (s->g.ritela) {
		reg(s, "⭐ §4.5: dico al palco che la tela di questa sessione e' %ux%u — "
		       "cosi' nasce gia' cosi' invece di nascere a una misura sua e "
		       "doverla cambiare (e il cambio e' una gara)",
		    tl, ta);
		s->g.ritela(s->g.ctx, tl, ta);
	}
	return true;
}

/* ========================================================================= */
/* ⭐⛔ IL CANALE VIDEO — §2.5, §5.1, §5.2, §6.2                              */
/*                                                                           */
/* ⛔ LE UNDICI REGOLE, E DOVE STA CIASCUNA IN QUESTE RIGHE                   */
/*                                                                           */
/*  P1  §2.5   nessuno stream video prima di aver SPEDITO `SESSIONE`          */
/*             ⇒ `s->sessione_spedita`, accesa dalla riga che lo spedisce     */
/*  P2  §6.2   `numero` parte da 1, lo 0 e' riservato, e AL GIRO si salta     */
/*             ⇒ `numero_prossimo()`                                          */
/*  P3  §2.5   il video vive SOLO su uno stream unidirezionale del server     */
/*             ⇒ `g.video_apri`, e mai `g.manda` (che e' il controllo)        */
/*  P4  §6.2   FIN prima dei 28 byte e' `ERRORE_PROTOCOLLO`                   */
/*             ⇒ i 28 byte escono in UNA scrittura, e se non escono si AZZERA */
/*  P5  §6.2   `largh.`/`altezza` valgono la tela IN VIGORE                   */
/*             ⇒ `s->tela_l/tela_a`, che chi chiama non puo' passare          */
/*  P6  §5.2   il primo fotogramma dopo `SESSIONE` DEVE essere una chiave     */
/*  P9  §5.2   e lo stesso a ogni cambio di tela                              */
/*             ⇒ `s->serve_chiave`, acceso in CINQUE punti e spento in uno    */
/*             ⚠ Diceva «tre» e i punti erano quattro; il quinto e' §2.3, il  */
/*               delta saltato per mancanza di posto (difetto B-18)           */
/*  §6.2       il tetto di 16 MiB vincola PRIMA chi spedisce                  */
/*             ⇒ il controllo sta prima di aprire lo stream: non parte un byte*/
/*  §6.2       FIN ⇒ completo · `RESET_STREAM` ⇒ si butta                     */
/*             ⇒ `rcp_video_finisci()` contro `rcp_video_abbandona()`         */
/*  §6.2       `codec` DEVE essere quello negoziato in §4.3                   */
/*             ⇒ `rcp_codec_negoziato()`, e nemmeno questo e' un parametro    */
/*  §5.1/§5.2  ogni abbandono nel registro, e una CHIAVE non si abbandona     */
/*                                                                           */
/* ⛔ E LA FORMA DI TUTTE E TRE LE REGOLE «PER COSTRUZIONE»: `largh.`,        */
/*    `altezza`, `codec` e `numero` **non sono parametri di nessuna funzione  */
/*    pubblica**.  Chi codifica non li puo' sbagliare perche' non li puo'     */
/*    toccare.  ⚠ La strada alternativa — passarli e controllarli — sarebbe   */
/*    stata piu' corta e avrebbe messo la protezione dove si puo' perdere     */
/*    (invariante I7, letta da dentro il programma).                          */

/* §6.2 — i due valori del campo `tipo`. */
#define V_CHIAVE 0x0301
#define V_DELTA 0x0302
/* §6.2 — l'intestazione e' di 28 byte esatti, senza riempimento. */
#define V_INTESTAZIONE 28
/* ⛔ §6.2 — «il server NON DEVE produrre un fotogramma piu' lungo di 16 MiB».
 * ⚠ E il tetto e' del FOTOGRAMMA, cioe' intestazione compresa: e' cosi' che lo
 *   conta chi riceve, che vede uno stream solo e non sa dove finisce la
 *   nostra struttura.  Un tetto contato sui soli dati lascerebbe passare 28
 *   byte di troppo, e la differenza si vede solo al limite — dove i banchi
 *   mettono i loro casi apposta. */
#define V_TETTO (16u * 1024u * 1024u)
/* ⛔ §5.2, eccezione 5 di §3: 200 ms dall'ultima CHIAVE SPEDITA. */
#define V_GRAZIA_CHIAVE 200

/* ⛔ §6.2 — IL CONTATORE, E LE DUE RIGHE CHE LO GOVERNANO.
 *
 *   «Il primo fotogramma di una sessione porta `numero = 1`, e lo `0` e'
 *    riservato»  —  «E al giro del contatore lo `0` si salta: l'aritmetica e'
 *    modulo 2^32 […] e da `0xFFFFFFFF` si passa a `1`».
 *
 * ⚠ La seconda riga e' entrata due ore dopo la prima, il 12 agosto 2026,
 *   perche' senza di essa il valore riservato tornava in circolo da solo dopo
 *   due anni e due mesi di sessione — una volta sola nella vita, e nessuno
 *   l'avrebbe collegato a `RICHIEDI_CHIAVE`.  ⛔ Le due righe sono qui una
 *   sotto l'altra apposta: separarle e' il modo in cui la seconda si perde. */
static uint32_t numero_prossimo(uint32_t ultimo)
{
	uint32_t n = ultimo + 1; /* modulo 2^32, per definizione del tipo */
	if (n == 0)
		n = 1;
	return n;
}

uint8_t rcp_codec_negoziato(const rcp_sessione *s)
{
	if (!s)
		return 0;
	/* §6.2: «`codec`: 1 = HEVC, 2 = AV1.  DEVE essere quello negoziato in
	 * §4.3».  ⛔ La stringa la sceglie `prima_comune()` sul `CIAO` del client,
	 * e la traduzione sta QUI e in nessun altro posto: due tabelle che
	 * mappano gli stessi nomi divergono, ed e' la stessa forma del difetto che
	 * §0 di `RCP.md` esiste per togliere. */
	if (strcmp(s->codec, "hevc") == 0)
		return 1;
	if (strcmp(s->codec, "av1") == 0)
		return 2;
	return 0; /* non ancora negoziato, o un nome che RCP/1 non definisce */
}

bool rcp_tela_in_vigore(const rcp_sessione *s, uint32_t *lar, uint32_t *alt)
{
	if (!s || !s->sessione_spedita)
		return false;
	if (lar)
		*lar = s->tela_l;
	if (alt)
		*alt = s->tela_a;
	return true;
}

bool rcp_video_serve_chiave(const rcp_sessione *s)
{
	return s && s->serve_chiave;
}

uint32_t rcp_video_ultimo_numero(const rcp_sessione *s)
{
	return s ? s->video_numero : 0;
}

/* ⛔ §7.1 — la tela e' cambiata, e §5.2 apre il debito SOLO se e' cambiata
 * davvero.  Vedi il riquadro in `rcp.h`.
 *
 * ⚠ RIPIEGO DICHIARATO (`CODER.md` §4.2): questa forma non ha un orologio,
 *   quindi NON puo' aprire il secondo di grazia di §7.1 sulle coordinate in
 *   volo — e un ripiego silenzioso produce due comportamenti sotto la stessa
 *   etichetta.  La riga di registro lo dice; chi serve `ADATTA_TELA` sul filo
 *   usa `rcp_tela_adattata_ora()`. */
void rcp_tela_adattata(rcp_sessione *s, uint32_t lar, uint32_t alt)
{
	if (!s || !s->sessione_spedita)
		return;
	if (lar != s->tela_l || alt != s->tela_a)
		reg(s, "⚠ RIPIEGO DICHIARATO: `rcp_tela_adattata()` senza l'ora — il "
		       "SECONDO DI GRAZIA di §7.1 sulle coordinate della tela vecchia "
		       "NON si apre, e un `PUNTATORE` in volo verra' rifiutato con "
		       "`ERRORE_PROTOCOLLO`.  Chi serve `ADATTA_TELA` sul filo chiami "
		       "`rcp_tela_adattata_ora()`");
	rcp_tela_adattata_ora(s, lar, alt, 0);
}

/* La dichiarazione, il perche' e le due misure che uccidono stanno in `rcp.h`:
 * qui c'e' solo la regola. */
bool rcp_misura_ammessa(uint32_t larghezza, uint32_t altezza, uint32_t *fuori_l,
                        uint32_t *fuori_a)
{
	uint32_t l, a;

	if (fuori_l)
		*fuori_l = 0;
	if (fuori_a)
		*fuori_a = 0;
	/* ⛔ Il tetto si controlla PRIMA di troncare: troncare 100000 al pari darebbe
	 * 100000, cioe' un numero ancora capace di uccidere il compositore.
	 *
	 * ⛔⭐ E I LIMITI SONO QUELLI DI §4.5, PER LATO — corretti la notte del 15
	 *     agosto 2026, refutando.  La prima stesura usava 200..8192 **su
	 *     entrambi i lati**, e `RCP.md` §4.5 e' normativo: *«larghezza e altezza
	 *     della tela DEVONO stare fra 320x240 e 7680x4320»*.  ⚠ Le due regole
	 *     erano gia' divergenti — `ATTACCA` applicava §4.5 e `ADATTA_TELA` no —
	 *     ed era **irraggiungibile** finche' `ADATTA_TELA` rispondeva sempre
	 *     `COMPOSITORE_INCAPACE`.  ⛔ Il caso concreto: si stringe il bordo
	 *     inferiore della finestra, `ADATTA_TELA(1600, 230)` veniva concessa, e
	 *     al RI-ATTACCO la stessa misura veniva rifiutata da `ATTACCA` — il
	 *     server che non concede in `SESSIONE` una tela che aveva concesso lui
	 *     stesso in `TELA`.
	 *
	 * ⚠ E il tetto vero del compositore resta sotto: `[M]` oltre 16384 per lato
	 *   `gnome-shell` muore, e 7680 e' molto sotto — vedi il riquadro in `rcp.h`. */
	if (larghezza < RCP_TELA_L_MINIMA || altezza < RCP_TELA_A_MINIMA ||
	    larghezza > RCP_TELA_L_MASSIMA || altezza > RCP_TELA_A_MASSIMA)
		return false;
	/* ⚠ In GIU', sempre: verso l'alto si uscirebbe dalla finestra del browser, e
	 * il pixel di troppo tornerebbe come banda o come scala — cioe' come la cosa
	 * che questa decisione toglie. */
	l = larghezza & ~1u;
	a = altezza & ~1u;
	/* ⛔ E il troncamento non puo' far scendere sotto il minimo: 321 -> 320 e'
	 * ancora ammesso, ma la regola si scrive invece di fidarsi che i numeri
	 * tornino. */
	if (l < RCP_TELA_L_MINIMA || a < RCP_TELA_A_MINIMA)
		return false;
	if (fuori_l)
		*fuori_l = l;
	if (fuori_a)
		*fuori_a = a;
	return true;
}

/* ⛔⭐ IL MESSAGGIO `TELA` SUL FILO — §7.1.
 *
 * ⚠ Fino al 14 agosto 2026 questo pezzo NON esisteva: `rcp_tela_adattata_ora()`
 *   cambiava la tela in vigore, apriva la grazia e scriveva nel registro, ma il
 *   client non riceveva **niente**.  ⇒ Un client che avesse chiesto una misura
 *   sarebbe rimasto ad aspettare una risposta che nessuno spediva, e il difetto
 *   si sarebbe visto come «l'adattamento non funziona» invece che come «non e'
 *   scritto».  E' la forma di guasto che questo progetto paga piu' spesso: il
 *   pezzo che manca **fra** due pezzi che ci sono.
 *
 * `esito`  1 = ADATTATA, 2 = RIFIUTATA
 * `motivo` 0 se adattata; 1 = COMPOSITORE_INCAPACE, 2 = MISURA_FUORI_LIMITI,
 *          3 = NON_ORA
 * ⛔ E i due campi di misura sono **la tela IN VIGORE DOPO questo messaggio**,
 *    non quella chiesta: su un rifiuto valgono quella di prima, ed e' l'unica
 *    riga che dice al client con che cosa continuare. */
static void manda_tela(rcp_sessione *s, uint8_t esito, uint8_t motivo,
                       uint32_t lar, uint32_t alt)
{
	uint8_t corpo[10];
	scrittore w = {corpo, sizeof corpo, 0, false};

	sc_byte(&w, esito);
	sc_byte(&w, motivo);
	sc_u32(&w, lar);
	sc_u32(&w, alt);
	if (w.pieno) {
		reg(s, "⛔ TELA non spedita: il corpo non ci sta (difetto nostro)");
		return;
	}
	manda_messaggio(s, T_TELA, corpo, w.len);
	reg(s, "TELA spedita: esito %u, motivo %u, tela in vigore %ux%u (§7.1)",
	    esito, motivo, lar, alt);
}

/* ⛔ §7.1 / §3 eccezione 3 — la forma che sa QUANDO, e apre la grazia. */
void rcp_tela_adattata_ora(rcp_sessione *s, uint32_t lar, uint32_t alt,
                           uint64_t ora_ms)
{
	if (!s || !s->sessione_spedita)
		return;
	if (lar == s->tela_l && alt == s->tela_a) {
		/* ⛔ §7.1 risponde `TELA` anche a un `ADATTA_TELA` che chiede la
		 * misura che c'e' gia': li' non c'e' nessuna «misura nuova», e aprire
		 * il debito della chiave fermerebbe il video su una sessione sana —
		 * il rosso all'imputato sbagliato che questa famiglia di regole ha
		 * gia' pagato quattro volte (P8 → P11 → P13 → P14). */
		reg(s, "TELA(ADATTATA) alla misura che c'era gia' (%ux%u): la tela in "
		       "vigore non cambia e §5.2 NON apre il debito della chiave",
		    lar, alt);
		/* ⛔ Si risponde LO STESSO: §7.1 vuole un `TELA` per ogni `ADATTA_TELA`,
		 *    e un client che non ricevesse niente aspetterebbe per sempre. */
		manda_tela(s, 1 /* ADATTATA */, 0, s->tela_l, s->tela_a);
		return;
	}
	reg(s, "tela IN VIGORE cambiata da %ux%u a %ux%u (§7.1): da qui §6.2 lega "
	       "largh./altezza alla nuova, e §5.2 vuole una CHIAVE alla misura "
	       "nuova",
	    s->tela_l, s->tela_a, lar, alt);
	/* ⛔ §7.1, terza eccezione di §3 — LA GRAZIA SI APRE QUI, e la tela
	 * precedente si tiene PRIMA di sostituirla: «gli input partiti prima che la
	 * risposta arrivasse non sono un difetto del client».  ⚠ Un secondo, e non
	 * di piu': oltre, il DEVE di §7.3 torna intero. */
	s->tela_prec_l = s->tela_l;
	s->tela_prec_a = s->tela_a;
	s->tela_grazia_da = ora_ms;
	s->tela_l = lar;
	s->tela_a = alt;
	s->serve_chiave = true;
	s->serve_chiave_perche = "e' il primo alla misura nuova dopo TELA (§5.2)";
	/* ⛔ E il messaggio esce DOPO che lo stato e' cambiato, non prima: i due
	 *    campi di misura devono dire la tela **in vigore dopo**, ed e' l'unico
	 *    ordine in cui possono dirla senza copiarla in una variabile a parte. */
	manda_tela(s, 1 /* ADATTATA */, 0, s->tela_l, s->tela_a);
}

/* ⛔⭐⭐ «IL PALCO DEVE SERVIRE LA TELA IN VIGORE» — e quando non lo fa, glielo si
 *     RICHIEDE, con un'attesa che cresce.
 *
 * ⛔ E' l'unica uscita onesta dal disaccordo, e la ragione e' del protocollo:
 *    §6.2 vieta di spedire un fotogramma la cui misura non e' la tela in vigore,
 *    e §7.1 non da' al server nessun modo di cambiare la tela **di sua
 *    iniziativa** — un `TELA` non richiesto e' `ERRORE_PROTOCOLLO` per il
 *    client.  ⇒ Delle due parti in disaccordo, quella che deve muoversi e' il
 *    palco, che e' nostro.
 *
 * ⚠ E l'attesa cresce perche' il caso in cui non si muove esiste (un compositore
 *   che non sa ridimensionare): senza, questa riga chiederebbe la stessa cosa a
 *   ogni fotogramma — sessanta rinegoziazioni al secondo, che e' la forma dei
 *   30,8 GB di registro del 14 agosto in un altro punto della catena.
 *
 * ⚠ Nel frattempo la sessione mostra l'ultima immagine buona: brutta e viva
 *   (I1).  Il registro lo dice a ogni tentativo, cosi' chi guarda distingue «il
 *   desktop e' fermo» da «il desktop non c'e' piu'». */
static void tela_richiama_il_palco(rcp_sessione *s, uint64_t ora_ms)
{
	/* ⛔⛔⛔ CHI NON HA IL POSTO NON COMANDA IL PALCO — e senza questa riga due
	 *      sessioni dello stesso utente si CONTENDONO la tela, per sempre.
	 *
	 * `[M]` 15 agosto 2026, mattina, sessione VERA dell'utente — ed e' un difetto
	 * che ho introdotto io stanotte, trovato dal suo «su Android il mouse non
	 * prende piu' i click»:
	 *
	 *   05:10  il portatile attacca, tela 2544x926
	 *   05:12  tace trenta secondi ⇒ STACCATO per silenzio, lascia il posto —
	 *          ⛔ ma la sessione resta viva, col suo canale video acceso e la
	 *          sua tela in vigore
	 *   05:14  il telefono attacca, tela 2560x926
	 *   05:14  da qui **diciassette richieste al secondo**: il portatile richiede
	 *          2544, il telefono 2560, il portatile 2544 … per sempre
	 *
	 * ⇒ E ogni giro **riavvia il flusso PipeWire**, che su Mutter distrugge e
	 *   ricrea i dispositivi di `libei`: `[M]` 640 «ricambi» del puntatore, e la
	 *   regione dell'input mai d'accordo con la tela («⚠ la regione 2560x926 NON
	 *   e' grande come la tela 2544x926: scalo le coordinate»).  ⛔ Il sintomo per
	 *   l'utente non nomina niente di tutto questo: **i clic non prendono piu'**.
	 *
	 * ⛔ E l'attesa che cresce NON bastava, per una ragione che va detta: si
	 *    azzera quando il palco arriva dove questa sessione lo vuole — che nel
	 *    ping-pong succede a ogni giro.  Un fondo temporale non cura due padroni:
	 *    cura un padrone insistente.
	 *
	 * ⇒ ⭐ La cura e' l'invariante che c'era gia': I2 dice **una sola sessione
	 *   grafica per utente**, e il posto (§8.2 `0x0F`) e' il modo in cui questo
	 *   modulo lo fa rispettare.  Chi il posto non ce l'ha **guarda** — non
	 *   comanda.  ⚠ E quando torna a parlare il posto se lo riprende, e da quel
	 *   momento comanda lui. */
	if (!s->attaccata) {
		if (!s->tela_disaccordo_da) {
			s->tela_disaccordo_da = ora_ms;
			reg(s, "⚠ il palco non e' alla tela in vigore %ux%u, ma questa "
			       "sessione NON ha il posto (I2): non gli chiedo niente — "
			       "comanda chi e' attaccato.  ⛔ Due sessioni che comandassero "
			       "lo stesso palco se lo contenderebbero a ogni fotogramma",
			    s->tela_l, s->tela_a);
		}
		return;
	}
	if (!s->g.ritela) {
		if (!s->tela_disaccordo_da) {
			s->tela_disaccordo_da = ora_ms;
			reg(s, "⛔ il palco non e' alla tela in vigore %ux%u e non ho un "
			       "gancio per chiedergli di venirci: da qui i fotogrammi si "
			       "scartano tutti (§6.2), e questa riga e' l'unica che lo dice",
			    s->tela_l, s->tela_a);
		}
		return;
	}
	if (s->tela_disaccordo_da
	    && ora_ms - s->tela_disaccordo_da < s->tela_disaccordo_attesa)
		return; /* si e' gia' chiesto da poco: non si insiste a ogni fotogramma */

	if (!s->tela_disaccordo_da) {
		s->tela_disaccordo_attesa = RCP_TELA_RICHIAMO_MS;
		reg(s, "⛔ il palco non e' alla tela in vigore %ux%u: §6.2 vieta di "
		       "spedire un fotogramma di misura diversa, quindi da qui non parte "
		       "piu' niente.  Gli richiedo %ux%u — e insistero' con un'attesa che "
		       "cresce, perche' un `TELA` che nessuno ha chiesto farebbe chiudere "
		       "la sessione al client (§6.2)",
		    s->tela_l, s->tela_a, s->tela_l, s->tela_a);
	} else {
		s->tela_disaccordo_attesa *= 2;
		if (s->tela_disaccordo_attesa > RCP_TELA_RICHIAMO_MAX_MS)
			s->tela_disaccordo_attesa = RCP_TELA_RICHIAMO_MAX_MS;
		reg(s, "⛔ il palco non e' ancora alla tela in vigore %ux%u: richiesta "
		       "ripetuta, prossima fra %llu ms",
		    s->tela_l, s->tela_a,
		    (unsigned long long)s->tela_disaccordo_attesa);
	}
	s->tela_disaccordo_da = ora_ms;
	s->g.ritela(s->g.ctx, s->tela_l, s->tela_a);
}

/* ⭐⭐ LA RISPOSTA DEL PALCO — vedi `rcp.h`, e i tre casi sono tre.
 *
 * ⛔⛔ E QUEL CHE QUESTA FUNZIONE **NON FA PIU'**, perche' era il difetto piu'
 *     grave della prima stesura: **non manda mai un `TELA` che nessuno ha
 *     chiesto.**
 *
 *     La prima stesura, quando il palco cambiava misura da solo, adottava la sua
 *     e spediva `TELA` per non lasciare la sessione senza pixel.  ⚠ Sembrava la
 *     scelta gentile e ⛔ era fatale: §6.2 dice che il client trattiene una
 *     misura mai annunciata **solo finche' ha una `ADATTA_TELA` senza risposta**,
 *     e li' non ne ha nessuna ⇒ `ERRORE_PROTOCOLLO`, sessione chiusa.  E il
 *     fotogramma viaggia su uno stream suo, quindi puo' arrivare **prima** del
 *     `TELA` che lo giustificherebbe: la meta' delle volte.
 *
 * ⇒ Il palco deve servire la tela in vigore, e se non ci sta gli si RICHIEDE,
 *   con un'attesa che cresce.  ⚠ Nel frattempo la sessione mostra l'ultima
 *   immagine buona: e' brutta e viva, che e' quel che I1 impone. */
void rcp_tela_dal_palco(rcp_sessione *s, uint32_t voluta_l, uint32_t voluta_a,
                        uint32_t avuta_l, uint32_t avuta_a, uint64_t ora_ms)
{
	if (!s || !s->sessione_spedita)
		return;

	/* --- 1. il palco non ce l'ha fatta --------------------------------- */
	/* ⛔ `0x0` non e' una misura: e' «non ce l'ho fatta», e va distinto dal
	 *    silenzio (`CODER.md` §3.10).  ⇒ Se stava rispondendo a una richiesta
	 *    NOSTRA, si risponde `NON_ORA` **adesso** invece di far scadere il fondo:
	 *    tre secondi di attesa per una notizia che c'e' gia'. */
	if (!avuta_l || !avuta_a) {
		if (s->tela_volo && voluta_l == s->tela_volo_l
		    && voluta_a == s->tela_volo_a) {
			reg(s, "il palco non ha potuto dare la tela %ux%u: NON_ORA subito, "
			       "senza aspettare il fondo di %u ms (§7.1).  La tela resta "
			       "%ux%u",
			    voluta_l, voluta_a, (unsigned)RCP_TELA_ATTESA_MS, s->tela_l,
			    s->tela_a);
			s->tela_volo = false;
			manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
			           s->tela_a);
		}
		return;
	}

	/* --- 2. il palco e' dove deve essere -------------------------------- */
	if (avuta_l == s->tela_l && avuta_a == s->tela_a) {
		if (s->tela_disaccordo_da) {
			reg(s, "⭐ il palco e' tornato alla tela in vigore %ux%u: il "
			       "disaccordo e' finito",
			    avuta_l, avuta_a);
			s->tela_disaccordo_da = 0;
			s->tela_disaccordo_attesa = 0;
		}
		/* ⛔ E se la richiesta in volo chiedeva PROPRIO questa misura, e' una
		 *    risposta: il palco ce l'aveva gia'.  ⚠ Senza questa riga, chiedere
		 *    la misura che c'e' gia' mentre un'altra e' in volo non si chiuderebbe
		 *    con nessun fotogramma — e si finirebbe sul fondo dei tre secondi. */
		if (s->tela_volo && voluta_l == s->tela_volo_l
		    && voluta_a == s->tela_volo_a) {
			s->tela_volo = false;
			reg(s, "TELA(ADATTATA) %ux%u: il palco quella misura ce l'aveva gia'",
			    avuta_l, avuta_a);
			manda_tela(s, 1 /* ADATTATA */, 0, s->tela_l, s->tela_a);
		}
		return;
	}

	/* --- 3. il palco e' altrove ----------------------------------------- */
	/* ⛔⭐ E SI ADOTTA **SOLO** SE RISPONDE ALLA NOSTRA RICHIESTA, cioe' se
	 *     `voluta` e' quella che abbiamo chiesto.  ⚠ La misura AVUTA puo' essere
	 *     un'altra ancora — §4.5 lo permette, e su KWin < 6.8 e' la strada
	 *     normale — ma il RICONOSCIMENTO si fa sulla domanda, non sulla risposta.
	 *     ⛔ Riconoscere sulla risposta era il difetto delle due richieste
	 *     incatenate: il fotogramma della prima veniva preso per la risposta
	 *     della seconda, e il desktop si assestava sulla misura sbagliata. */
	if (s->tela_volo && voluta_l == s->tela_volo_l
	    && voluta_a == s->tela_volo_a) {
		if (avuta_l != voluta_l || avuta_a != voluta_a)
			reg(s, "⚠ il palco ha concesso %ux%u dove si era chiesto %ux%u: §4.5 "
			       "lo permette, e il `TELA` che parte adesso porta la misura "
			       "VERA",
			    avuta_l, avuta_a, voluta_l, voluta_a);
		/* ⛔ Il tetto del decodificatore NON si scavalca nemmeno qui (§4.5): una
		 *    tela che il client non sa decodificare e' uno schermo nero
		 *    dichiarato invece che taciuto — ma pur sempre nero. */
		if (s->max_l && (avuta_l > s->max_l || avuta_a > s->max_a)) {
			reg(s, "⛔ il palco ha dato %ux%u, oltre il video.misura_massima di "
			       "questo client (%ux%u): NON la adotto, e rispondo NON_ORA.  "
			       "La tela resta %ux%u e al palco si richiede quella",
			    avuta_l, avuta_a, s->max_l, s->max_a, s->tela_l, s->tela_a);
			s->tela_volo = false;
			manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
			           s->tela_a);
			tela_richiama_il_palco(s, ora_ms);
			return;
		}
		s->tela_volo = false;
		s->tela_disaccordo_da = 0;
		s->tela_disaccordo_attesa = 0;
		/* ⛔ E il resto lo fa la funzione che c'era gia': cambia la tela in
		 *    vigore, apre il secondo di grazia sulle coordinate, segna il debito
		 *    della chiave (§5.2) e spedisce `TELA(ADATTATA)`. */
		rcp_tela_adattata_ora(s, avuta_l, avuta_a, ora_ms);
		return;
	}

	/* ⛔ Nessuna richiesta nostra, o una richiesta diversa: il palco e' altrove
	 *    di suo.  ⚠ Puo' essere un rimontaggio dopo una caduta della sessione
	 *    grafica, o il fotogramma in ritardo di una richiesta gia' scaduta.  ⇒ Si
	 *    RICHIEDE la tela in vigore, e non si adotta niente. */
	tela_richiama_il_palco(s, ora_ms);
}

bool rcp_tela_rimanda(rcp_sessione *s, uint32_t voluta_l, uint32_t voluta_a,
                      uint64_t ora_ms)
{
	if (!s || !s->tela_volo)
		return false;
	if (voluta_l != s->tela_volo_l || voluta_a != s->tela_volo_a)
		return false;
	/* ⭐ Si sposta l'inizio, non si allunga il fondo: cosi' il tetto di §7.1
	 *    resta quello, e vale da quando c'e' davvero qualcuno che prova. */
	s->tela_volo_da = ora_ms;
	reg(s, "§7.1: il palco non c'e' ANCORA per la tela %ux%u — il fondo di %u ms "
	       "si RIMANDA invece di rispondere NON_ORA a una domanda che sta per "
	       "avere una risposta vera",
	    voluta_l, voluta_a, (unsigned)RCP_TELA_ATTESA_MS);
	return true;
}

bool rcp_tela_in_volo(const rcp_sessione *s, uint32_t *lar, uint32_t *alt)
{
	if (!s || !s->tela_volo)
		return false;
	if (lar)
		*lar = s->tela_volo_l;
	if (alt)
		*alt = s->tela_volo_a;
	return true;
}

/* ⛔ §7.1 — IL FONDO DELL'ATTESA: «a ogni `ADATTA_TELA` il server DEVE rispondere
 *    con un `TELA`, riuscito o no».  Chiamata da `rcp_tempo()`, cioe' dall'unico
 *    posto che vede scorrere il tempo anche quando non arriva un byte.
 *
 * ⚠ E il ritardo NON si misura da quando e' arrivato il messaggio ma da quando
 *   la domanda e' PARTITA verso il palco: sono lo stesso istante oggi, e il
 *   giorno in cui in mezzo ci fosse una coda non lo sarebbero piu'. */
static void tela_scade(rcp_sessione *s, uint64_t ora_ms)
{
	if (!s->tela_volo)
		return;
	if (ora_ms - s->tela_volo_da < RCP_TELA_ATTESA_MS)
		return;
	reg(s, "⛔ ADATTA_TELA %ux%u: il palco non ha consegnato un fotogramma a "
	       "quella misura entro %u ms — rispondo NON_ORA (§7.1: un silenzio "
	       "lascerebbe il client ad aspettare per sempre, e §6.2 gli fa "
	       "TRATTENERE i fotogrammi finche' aspetta).  La tela resta %ux%u",
	    s->tela_volo_l, s->tela_volo_a, (unsigned)RCP_TELA_ATTESA_MS, s->tela_l,
	    s->tela_a);
	s->tela_volo = false;
	manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l, s->tela_a);
}

void rcp_video_conti(const rcp_sessione *s, uint32_t *spediti,
                     uint32_t *abbandonati)
{
	if (spediti)
		*spediti = s ? s->video_spediti : 0;
	if (abbandonati)
		*abbandonati = s ? s->video_abbandonati : 0;
}

/* ⛔⭐ §5.1 — L'ABBANDONO DECISO A VALLE, E PERCHE' NON BASTAVA QUELLO DI SOPRA.
 *
 * `rcp_video_abbandona()` qui sotto sa abbandonare **il fotogramma aperto**,
 * cioe' uno a cui manca ancora un pezzo da scrivere.  ⛔ Ma la scena che §5.1
 * descrive con le sue stesse parole — «il server PUO' chiamare `RESET_STREAM`
 * su un fotogramma che non serve piu', **perche' ne e' gia' partito uno piu'
 * recente**» — non e' quella: li' il fotogramma vecchio e' stato scritto TUTTO
 * e chiuso con FIN, e sta fermo nella coda d'uscita del trasporto perche' la
 * linea non lo porta via.  Per RCP quel fotogramma e' gia' finito
 * (`video_aperto` e' falso), e `rcp_video_abbandona()` restituirebbe `false`
 * senza scrivere una riga.
 *
 * ⇒ Chi tiene la coda — `webtransport.c` — e' l'unico che sa quali fotogrammi
 *   sono ancora **sul filo o prima del filo**, e quindi l'unico che puo'
 *   decidere l'abbandono di §5.1.  ⛔ Ma le tre conseguenze di quell'abbandono
 *   sono di RCP e non sue: la riga di registro obbligatoria (§5.1), il conto
 *   degli abbandonati, e ⛔ **il debito della chiave** (§5.2 — «quando il
 *   server abbandona un delta DEVE mandare un fotogramma chiave appena puo'»).
 *   Lasciarle a chi tiene la coda vorrebbe dire due copie dello stesso stato,
 *   che e' la forma che `RCP.md` §0 esiste per togliere.
 *
 * ⛔ E LA CHIAVE NON SI ABBANDONA NEMMENO DA VALLE: §5.2 lo vieta senza
 *    distinguere chi decide.  Qui si RIFIUTA e si scrive, come sopra —
 *    altrimenti la regola varrebbe per una strada e non per l'altra, e quale
 *    delle due si percorra dipenderebbe da quanto e' veloce la linea. */
bool rcp_video_abbandonato_a_valle(rcp_sessione *s, uint32_t numero, bool chiave,
                                   size_t byte_non_usciti, const char *perche)
{
	if (!s)
		return false;
	if (chiave) {
		reg(s, "⛔ NON abbandono il fotogramma %u nella coda: e' una CHIAVE, e "
		       "§5.2 lo vieta anche a valle (motivo chiesto: %s) — restavano "
		       "%zu byte da far uscire",
		    numero, perche ? perche : "non dichiarato", byte_non_usciti);
		return false;
	}
	s->video_abbandonati++;
	/* ⛔ §5.1: «ogni abbandono DEVE essere scritto nel registro: un fotogramma
	 * perso in silenzio e uno abbandonato di proposito hanno lo stesso aspetto
	 * dal lato che riceve».  ⚠ E si dice quanti byte NON sono usciti: e' la
	 * differenza fra «l'ho buttato prima di spendere banda» e «l'avevo gia'
	 * quasi spedito», che sono due fatti diversi per chi regola il ritmo. */
	reg(s, "fotogramma %u ABBANDONATO NELLA CODA (§5.1, RESET_STREAM): %zu byte "
	       "non sono usciti, perche': %s — spediti %u, abbandonati %u",
	    numero, byte_non_usciti, perche ? perche : "non dichiarato",
	    s->video_spediti, s->video_abbandonati);
	/* ⛔ §5.2: «quando il server abbandona un delta, DEVE mandare un fotogramma
	 * chiave appena puo' — senza aspettare che il client lo chieda». */
	s->serve_chiave = true;
	s->serve_chiave_perche = "un delta e' stato abbandonato nella coda (§5.1)";
	return true;
}

/* ⛔ §2.3 — IL CREDITO DI STREAM MANCATO, SCRITTO NEL REGISTRO DA UN POSTO SOLO.
 *
 * §2.3 chiude cosi': «e in tutt'e due i casi **si scrive nel registro**», dove
 * i due casi sono il delta buttato e la chiave che aspetta.  ⛔ La riga esiste
 * perche' senza di essa il sintomo e' *«schermo fermo, e nessuna riga nel
 * registro che dica perche'»* — il rilievo R1.9 la nomina parola per parola.
 *
 * ⚠ E il contatore degli abbandonati NON si tocca: qui lo stream non e' mai
 *   nato, quindi non c'e' niente da azzerare sul filo e il `numero` non e'
 *   stato consumato (§6.2: «NON per quelli che non spedisce affatto»).  Sono
 *   due grandezze diverse e tenerle insieme confonderebbe chi diagnostica. */
void rcp_video_niente_credito(rcp_sessione *s, bool chiave, uint64_t restano)
{
	if (!s)
		return;
	if (chiave) {
		reg(s, "⛔ §2.3: nessuno stream unidirezionale per una CHIAVE (il client "
		       "ne concede ancora %llu).  ⚠ La chiave NON si butta: §5.2 la "
		       "vuole, il debito resta acceso e si riprova al prossimo "
		       "fotogramma — «aspettare un posto libero» e' esattamente quel "
		       "che §2.3 prescrive per le chiavi",
		    (unsigned long long)restano);
		return;
	}
	reg(s, "⚠ §2.3: nessuno stream unidirezionale per il delta che veniva dopo "
	       "il %u (il client ne concede ancora %llu): il delta si BUTTA — «un "
	       "delta vecchio non serve piu', ne sta gia' arrivando uno nuovo».  ⛔ "
	       "E non e' un errore fatale: la sessione regge (§2.3)",
	    s->video_numero, (unsigned long long)restano);
	/* ⛔⭐ E SI ACCENDE IL DEBITO DI CHIAVE — mancava, ed e' il difetto B-18.
	 *
	 *   §5.2: «quando il server abbandona un delta, DEVE mandare un fotogramma
	 *   chiave appena puo', senza aspettare che il client lo chieda».  I due
	 *   gemelli che abbandonano un delta lo fanno gia' — l'abbandono nella coda
	 *   (piu' su, §5.1) e `rcp_video_abbandona()` (piu' giu', §5.2) — e QUI il
	 *   danno visto dal lato che riceve e' lo stesso: al decodificatore manca un
	 *   delta, e da li' in poi produce immagini via via piu' sfasciate.
	 *
	 * ⛔ E QUI SERVE PIU' CHE NEI DUE GEMELLI, perche' il client non se ne
	 *    accorge MAI da solo:
	 *      · il `numero` NON e' stato consumato (il riquadro qui sopra, §6.2),
	 *        quindi nei numeri non resta **nessun buco** — ed e' l'unico segnale
	 *        su cui §5.2 fa chiedere una chiave al client;
	 *      · il codificatore gira a GOP infinito (`chiavi_ogni = 0`,
	 *        `src/figlio.c:1568`), quindi un'altra chiave non arriverebbe **mai
	 *        piu'** da sola.
	 *    ⇒ Senza questa riga, UN SOLO delta saltato per mancanza di posto
	 *      sfascia l'immagine **per sempre e in silenzio**: nessun errore,
	 *      nessuna riga, e il client che non ha modo di chiedere la cura.
	 *
	 * ⚠ E se il posto manca ancora quando la chiave sara' pronta, non si ricade
	 *   nel caso vietato da R1.9: il ramo `chiave` qui sopra NON la butta —
	 *   tiene il debito acceso e riprova al fotogramma dopo, che e' quel che
	 *   §2.3 prescrive per le chiavi. */
	s->serve_chiave = true;
	s->serve_chiave_perche = "un delta e' stato saltato per mancanza di posto "
	                         "(§2.3), e nei numeri non resta nessun buco";
}

/* ⛔ §5.1 — l'abbandono, e §5.2 vieta di abbandonare una CHIAVE. */
bool rcp_video_abbandona(rcp_sessione *s, const char *perche)
{
	if (!s || !s->video_aperto)
		return false;
	if (s->video_e_chiave) {
		/* ⛔ §5.2: «il server NON DEVE abbandonare un fotogramma chiave.
		 * Abbandonare la cura non e' una cura».  ⚠ E il rifiuto si SCRIVE: un
		 * divieto che si fa rispettare in silenzio e' indistinguibile da un
		 * divieto che nessuno ha applicato. */
		reg(s, "⛔ NON abbandono il fotogramma %u: e' una CHIAVE, e §5.2 lo "
		       "vieta (motivo chiesto: %s)",
		    s->video_suo_numero, perche ? perche : "non dichiarato");
		return false;
	}
	s->g.video_azzera(s->g.ctx, s->video_stream);
	s->video_aperto = false;
	s->video_abbandonati++;
	/* ⛔ §5.1: «ogni abbandono DEVE essere scritto nel registro: un fotogramma
	 * perso in silenzio e uno abbandonato di proposito hanno lo stesso aspetto
	 * dal lato che riceve». */
	reg(s, "fotogramma %u ABBANDONATO (§5.1) dopo %zu byte su %zu, stream %lld, "
	       "perche': %s — spediti %u, abbandonati %u",
	    s->video_suo_numero, s->video_scritti, s->video_da_scrivere,
	    (long long)s->video_stream, perche ? perche : "non dichiarato",
	    s->video_spediti, s->video_abbandonati);
	/* ⛔ §5.2: «quando il server abbandona un delta, DEVE mandare un
	 * fotogramma chiave appena puo' — senza aspettare che il client lo
	 * chieda, perche' il client se ne accorge un giro di rete piu' tardi».
	 * ⭐ E' l'unica cura che abbiamo: a un delta mancante il decodificatore
	 * non solleva nessun errore, si limita a produrre immagini via via piu'
	 * sfasciate. */
	s->serve_chiave = true;
	s->serve_chiave_perche = "un delta e' stato abbandonato (§5.2)";
	return true;
}

int rcp_video_apri(rcp_sessione *s, bool chiave, size_t lunghezza,
                   uint64_t istante_us, uint32_t input, uint64_t ora_ms)
{
	if (!s)
		return RCP_VIDEO_NIENTE_CANALE;

	/* ⛔ I QUATTRO GANCI O NESSUNO.  Un ospite che sapesse aprire e non
	 * azzerare non potrebbe onorare §5.1, e se ne accorgerebbe a meta' di un
	 * fotogramma: qui la cosa si dice prima di aprire qualunque cosa. */
	if (!s->g.video_apri || !s->g.video_scrivi || !s->g.video_fin ||
	    !s->g.video_azzera)
		return RCP_VIDEO_NIENTE_CANALE;

	if (s->video_aperto)
		return RCP_VIDEO_GIA_APERTO;

	/* ⛔ P1 / §2.5 / invariante I3 — «nessuno prima di aver spedito
	 * `SESSIONE`».  ⚠ E la sessione FINITA vale come «non piu'»: dopo un
	 * congedo il canale di controllo non c'e' piu', e un fotogramma che
	 * partisse adesso arriverebbe a nessuno. */
	if (!s->sessione_spedita || s->stato == S_FINITA) {
		reg(s, "⛔ NIENTE VIDEO: `SESSIONE` non e' stata spedita (stato %s) — "
		       "§2.5 vieta di aprire uno stream video prima, ed e' "
		       "l'invariante I3 sul filo",
		    NOMI_STATO[s->stato]);
		return RCP_VIDEO_PRIMA_DI_SESSIONE;
	}

	/* ⛔ P6 e P9 / §5.2 — il primo dopo `SESSIONE`, e il primo alla misura
	 * nuova dopo un `TELA`, DEVONO essere una chiave.  ⚠ Qui si RIFIUTA
	 * invece di promuovere il delta a chiave: promuoverlo sarebbe mentire sul
	 * campo `tipo`, e il fotogramma non diventerebbe decodificabile da solo.
	 * Chi codifica ha la risposta giusta — `rcp_video_serve_chiave()` — e la
	 * puo' chiedere PRIMA di codificare. */
	if (!chiave && s->serve_chiave) {
		reg(s, "⛔ FOTOGRAMMA NON SPEDITO: e' un delta e §5.2 vuole una CHIAVE "
		       "(%s).  ⚠ Chiedere `rcp_video_serve_chiave()` prima di "
		       "codificare costa zero; qui il fotogramma si butta",
		    s->serve_chiave_perche ? s->serve_chiave_perche : "§5.2");
		return RCP_VIDEO_SERVE_UNA_CHIAVE;
	}

	/* ⛔ §6.2 — IL TETTO VINCOLA PRIMA DI TUTTO CHI SPEDISCE, e per questo il
	 * controllo sta QUI: prima di aprire lo stream, prima che parta un byte.
	 * «Se la codifica ne producesse uno piu' grande, DEVE ricodificarlo a
	 * qualita' inferiore e scriverlo nel registro — mai spedirlo».
	 *
	 * ⚠ E il confronto e' `>` e non `>=`: 16 MiB esatti sono legali, il tetto
	 *   e' un massimo.  La differenza si vede su un caso solo, ed e' il caso
	 *   che i banchi mettono apposta. */
	if (lunghezza > (size_t)(V_TETTO - V_INTESTAZIONE)) {
		reg(s, "⛔ FOTOGRAMMA NON SPEDITO: %zu byte di dati + %d di "
		       "intestazione superano i %u del tetto di §6.2 — si RICODIFICA a "
		       "qualita' inferiore, non si spedisce",
		    lunghezza, V_INTESTAZIONE, V_TETTO);
		return RCP_VIDEO_TROPPO_GRANDE;
	}

	uint8_t codec = rcp_codec_negoziato(s);
	if (codec == 0) {
		/* §6.2: «DEVE essere quello negoziato in §4.3».  Se non c'e' una
		 * negoziazione non c'e' un valore lecito da scrivere, e inventarne uno
		 * sarebbe la forma E2 — due comportamenti sotto la stessa etichetta. */
		reg(s, "⛔ NIENTE VIDEO: nessun codec negoziato in §4.3 (codec=«%s»), e "
		       "§6.2 vuole quello negoziato",
		    s->codec);
		return RCP_VIDEO_NIENTE_CANALE;
	}

	int64_t stream = 0;
	/* ⛔ P3 / §2.5 — «solo su uno stream unidirezionale aperto dal server: un
	 * `0x03` sul canale di controllo e' `ERRORE_PROTOCOLLO`».  ⭐ Il canale di
	 * controllo in questo modulo si scrive con `s->g.manda`, e da qui in giu'
	 * quella funzione non compare: e' l'unico modo di rendere la regola
	 * impossibile da violare invece che facile da rispettare. */
	uint64_t restano = 0;
	if (!s->g.video_apri(s->g.ctx, &stream, &restano)) {
		/* ⛔ §2.3 — e i due casi NON sono lo stesso caso: un delta si butta,
		 * una chiave si aspetta.  La riga la scrive una funzione sola, perche'
		 * due righe scritte in due posti divergono. */
		rcp_video_niente_credito(s, chiave, restano);
		return RCP_VIDEO_STREAM_NON_APERTO;
	}

	uint32_t num = numero_prossimo(s->video_numero);

	/* ⛔ §6.2 — I 28 BYTE, IN QUEST'ORDINE E SENZA UN BYTE DI RIEMPIMENTO.
	 *
	 *   0  tipo u16 · 2 codec u16 · 4 largh. u32 · 8 altezza u32 ·
	 *   12 numero u32 · 16 istante u64 · 24 input u32 · 28 dati
	 *
	 * ⚠ Il disegno diceva «… 24 │ 32» fino al 9 agosto 2026: quattro byte di
	 *   riempimento mai dichiarati, che due implementazioni potevano indovinare
	 *   uguali senza che nessuno se ne accorgesse.  ⛔ `scrittore` scrive byte
	 *   per byte in ordine di rete apposta: una `struct` C con `memcpy` qui
	 *   rimetterebbe quel difetto, e nemmeno un banco lo vedrebbe finche' i due
	 *   lati non girassero su due architetture diverse. */
	uint8_t testa[V_INTESTAZIONE];
	scrittore w = {testa, sizeof testa, 0, false};
	sc_u16(&w, chiave ? V_CHIAVE : V_DELTA);
	sc_u16(&w, codec);
	/* ⛔ P5 / §6.2: la tela IN VIGORE — quella di `SESSIONE` (§4.5) oppure
	 * l'ultima concessa da `TELA` (§7.1).  Non un parametro. */
	sc_u32(&w, s->tela_l);
	sc_u32(&w, s->tela_a);
	sc_u32(&w, num);
	/* ⚠ §6.2: microsecondi dell'orologio MONOTONO del server alla cattura.
	 *   Non e' un'ora, e il client NON DEVE confrontarlo col proprio. */
	sc_u64(&w, istante_us);
	/* §6.2, §7.3: l'ultimo input iniettato prima della cattura, 0 se nessuno. */
	sc_u32(&w, input);

	/* ⛔ P4 / §6.2 — «uno stream chiuso con FIN prima dei 28 byte
	 * dell'intestazione e' `ERRORE_PROTOCOLLO`: non e' un fotogramma corto, e'
	 * una lunghezza che non torna».
	 *
	 * ⭐ Da cui la forma di queste sei righe: i 28 byte escono in **una sola**
	 *    scrittura, e se non escono si AZZERA.  Uno stream azzerato a zero
	 *    byte e' un fotogramma abbandonato — §5.1, legale, la sessione regge —
	 *    mentre un FIN a zero byte sarebbe `ERRORE_PROTOCOLLO` e farebbe
	 *    cadere una sessione in cui a sbagliare siamo stati noi.
	 *    ⛔ Le due chiusure NON sono intercambiabili, ed e' tutto §6.2. */
	if (w.pieno || !s->g.video_scrivi(s->g.ctx, stream, testa, sizeof testa)) {
		s->g.video_azzera(s->g.ctx, stream);
		reg(s, "⛔ i 28 byte dell'intestazione del fotogramma %u non sono "
		       "usciti: stream %lld AZZERATO (§6.2) — ⚠ mai chiuso con FIN, o "
		       "sarebbe stato «una lunghezza che non torna»",
		    num, (long long)stream);
		/* Il numero e' stato consumato: §6.2 dice che il contatore cresce
		 * «compresi quelli che poi abbandona», e un buco «significa qualcosa». */
		s->video_numero = num;
		return RCP_VIDEO_ROTTO_A_META;
	}

	s->video_aperto = true;
	s->video_stream = stream;
	s->video_e_chiave = chiave;
	s->video_suo_numero = num;
	s->video_da_scrivere = lunghezza;
	s->video_scritti = 0;
	s->video_numero = num;
	/* ⛔ L'ora si tiene DA QUI, e non si va a chiederla al campo `istante`:
	 * `istante` e' l'orologio della CATTURA in microsecondi (§6.2) e `ora_ms`
	 * quello della sessione in millisecondi.  Che siano lo stesso orologio e'
	 * probabile e non e' scritto da nessuna parte — e derivarne uno dall'altro
	 * sarebbe indicizzare i 200 ms di §5.2 su una grandezza sostitutiva
	 * (`LEZIONI.md` §1.13). */
	s->video_aperto_ms = ora_ms;
	return RCP_VIDEO_SPEDITO;
}

int rcp_video_pezzo(rcp_sessione *s, const uint8_t *dati, size_t len)
{
	if (!s || !s->video_aperto)
		return RCP_VIDEO_STREAM_NON_APERTO;
	if (len == 0)
		return RCP_VIDEO_SPEDITO;
	/* ⛔ Piu' byte di quanti se ne erano dichiarati vorrebbe dire che il tetto
	 * di §6.2 e' stato controllato su un numero e il filo ne porta un altro:
	 * il controllo diventerebbe una formalita'.  Si azzera. */
	if (len > s->video_da_scrivere - s->video_scritti) {
		reg(s, "⛔ il fotogramma %u vuole scrivere %zu byte oltre i %zu "
		       "dichiarati: stream AZZERATO — il tetto di §6.2 era stato "
		       "controllato sui byte dichiarati",
		    s->video_suo_numero, len, s->video_da_scrivere);
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		s->video_abbandonati++;
		s->serve_chiave = true;
		s->serve_chiave_perche = "un fotogramma si e' rotto a meta' (§5.2)";
		return RCP_VIDEO_ROTTO_A_META;
	}
	if (!s->g.video_scrivi(s->g.ctx, s->video_stream, dati, len)) {
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		s->video_abbandonati++;
		reg(s, "⛔ il fotogramma %u si e' rotto a %zu byte su %zu: stream "
		       "AZZERATO (§6.2) — il client lo butta e lo tratta come un buco, "
		       "che e' vero; con un FIN lo avrebbe consegnato al "
		       "decodificatore, che e' falso",
		    s->video_suo_numero, s->video_scritti, s->video_da_scrivere);
		s->serve_chiave = true;
		s->serve_chiave_perche = "un fotogramma si e' rotto a meta' (§5.2)";
		return RCP_VIDEO_ROTTO_A_META;
	}
	s->video_scritti += len;
	return RCP_VIDEO_SPEDITO;
}

int rcp_video_finisci(rcp_sessione *s)
{
	if (!s || !s->video_aperto)
		return RCP_VIDEO_STREAM_NON_APERTO;
	/* ⛔ §6.2 — «uno stream chiuso con FIN porta un fotogramma COMPLETO».  Il
	 * FIN e' un'affermazione, non un modo di chiudere: se mancano byte si
	 * azzera, e il client trattera' il fotogramma come un buco invece di
	 * consegnare mezza immagine al decodificatore (rilievo R1.7, 9 agosto
	 * 2026 — «un fotogramma abbandonato e uno completo avevano lo stesso
	 * aspetto», la forma d'errore E8). */
	if (s->video_scritti != s->video_da_scrivere) {
		reg(s, "⛔ il fotogramma %u ha %zu byte sui %zu dichiarati: stream "
		       "AZZERATO invece che chiuso con FIN — FIN vuol dire COMPLETO "
		       "(§6.2)",
		    s->video_suo_numero, s->video_scritti, s->video_da_scrivere);
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		s->video_abbandonati++;
		s->serve_chiave = true;
		s->serve_chiave_perche = "un fotogramma si e' rotto a meta' (§5.2)";
		return RCP_VIDEO_ROTTO_A_META;
	}
	s->g.video_fin(s->g.ctx, s->video_stream);
	s->video_aperto = false;
	s->video_spediti++;
	if (s->video_e_chiave) {
		/* ⛔ §5.2: il debito si paga UNA volta.  ⚠ E si spegne QUI e non
		 * all'apertura: un fotogramma aperto e poi rotto non ha pagato niente,
		 * e spegnere il debito li' avrebbe lasciato il client senza chiave con
		 * il server convinto di avergliela mandata. */
		s->serve_chiave = false;
		s->serve_chiave_perche = NULL;
		s->mai_spedita_una_chiave = false;
		/* ⛔ §5.2 / §3 eccezione 5 — l'orologio dei 200 ms parte da QUI, cioe'
		 * dalla chiave SPEDITA.  ⚠ E «spedita» vuol dire «i byte sono usciti
		 * da noi», non «e' arrivata»: vedi il rilievo P17 nel rapporto, che
		 * dichiara la differenza invece di correggerla di testa propria. */
		s->ultima_chiave_ms = s->video_aperto_ms;
	}
	reg(s, "fotogramma %u SPEDITO: %s, codec %u, %ux%u, %zu byte di dati, "
	       "stream %lld, FIN (§6.2: completo) — spediti %u, abbandonati %u",
	    s->video_suo_numero, s->video_e_chiave ? "CHIAVE 0x0301" : "delta 0x0302",
	    rcp_codec_negoziato(s), s->tela_l, s->tela_a, s->video_scritti,
	    (long long)s->video_stream, s->video_spediti, s->video_abbandonati);
	return RCP_VIDEO_SPEDITO;
}

int rcp_video_spedisci(rcp_sessione *s, bool chiave, const uint8_t *dati,
                       size_t len, uint64_t istante_us, uint32_t input,
                       uint64_t ora_ms)
{
	int e = rcp_video_apri(s, chiave, len, istante_us, input, ora_ms);
	if (e != RCP_VIDEO_SPEDITO)
		return e;
	if (len) {
		e = rcp_video_pezzo(s, dati, len);
		if (e != RCP_VIDEO_SPEDITO)
			return e;
	}
	return rcp_video_finisci(s);
}

/* ========================================================================= */
/* ⭐ IL CANALE DI INPUT — `RCP.md` §2.5, §3, §3.1, §6.0, §6.1, §7.1, §7.3   */
/*                                                                           */
/* ⛔ QUEL CHE QUESTA SEZIONE NON SA, ED E' LA META' DEL SUO MESTIERE:        */
/*    non sa che cosa sia `libei`, non sa che cosa sia una disposizione di    */
/*    tastiera, non sa che cosa sia un dispositivo.  Legge byte, li giudica   */
/*    contro §7.3 riga per riga, e chiama uno dei cinque ganci.  L'altra      */
/*    meta' — quella che tocca il desktop vero — sta in `src/input.c`.        */
/*                                                                           */
/* ⛔ E LA REGOLA DI RIGORE (§3) VALE QUI COME ALTROVE: un tipo che non si    */
/*    conosce, una lunghezza che non torna, un campo fuori intervallo, un     */
/*    messaggio nello stato sbagliato ⇒ `ERRORE_PROTOCOLLO`, col motivo, per  */
/*    tutt'e due le strade di §3.1.  ⚠ Con UNA eccezione dichiarata, ed e' la */
/*    terza dell'elenco di §3: il secondo di grazia di §7.1.                  */

/* ⛔⭐ §7.3 — «Al distacco si rilascia tutto», e le quattro strade che
 *     finiscono una connessione passano tutte di qui.
 *
 * ⚠ E il ripiego si DICHIARA (`CODER.md` §4.2): se il gancio non c'e', questa
 *   funzione scrive che non c'e' invece di tacere — perche' «nessun tasto era
 *   premuto» e «non ho potuto rilasciare niente» hanno lo stesso aspetto, ed e'
 *   `LEZIONI.md` §1.9 regola 1 sul campo in cui costa di piu': il sintomo di
 *   tutt'e due e' un desktop che al riattacco non risponde. */
static void rilascia_al_distacco(rcp_sessione *s, const char *perche)
{
	if (!s || s->inp_rilasciato)
		return;
	s->inp_rilasciato = true;
	if (!s->g.input_rilascia_tutto) {
		/* ⛔ Si scrive SOLO se questo canale ha visto passare qualcosa: su una
		 * sessione senza input — i banchi in-processo, l'innesto di ngtcp2 —
		 * la riga sarebbe rumore a ogni congedo, e il rumore fa smettere di
		 * leggere il registro proprio dove serve. */
		if (s->inp_arrivati)
			reg(s, "⚠ RIPIEGO DICHIARATO (§7.3): la connessione finisce (%s) e "
			       "questo server NON ha il gancio del rilascio — %u input erano "
			       "arrivati e %u iniettati.  Se qualcosa e' rimasto premuto, "
			       "resta premuto",
			    perche, s->inp_arrivati, s->inp_iniettati);
		return;
	}
	int quanti = s->g.input_rilascia_tutto(s->g.ctx);
	/* ⛔⛔⭐ TRE ESITI, TRE RIGHE DIVERSE — 16 agosto 2026, e prima ce n'era
	 *      una sola che stampava `quanti` come se fosse sempre un conto.
	 *
	 *      Nel prodotto vero non lo e' MAI: chi tiene la mappa dei tasti
	 *      premuti e' il figlio, e la sua risposta non torna indietro.  ⇒ La
	 *      riga diceva «0 erano premuti» a ogni distacco, compresi i quattro
	 *      in cui il figlio, subito sotto, scriveva `2`.
	 *
	 *      ⚠ Un numero inventato e' peggio di nessun numero, e qui era il
	 *        peggiore possibile: uno ZERO su una regola il cui unico modo di
	 *        fallire e' non rilasciare niente.  `LEZIONI.md` §1.9 — «vuoto» e
	 *        «giusto» con la stessa faccia. */
	if (quanti == RCP_RILASCIO_IMPOSSIBILE) {
		reg(s, "⛔ §7.3 — RILASCIO AL DISTACCO (%s): NON si e' potuto chiedere "
		       "il rilascio al palco.  ⚠ Se qualcosa era premuto, RESTA "
		       "premuto: al riattacco il desktop puo' essere inservibile, e "
		       "questa e' la riga che lo collega",
		    perche);
		return;
	}
	if (quanti == RCP_RILASCIO_SENZA_CONTO) {
		reg(s, "⭐ §7.3 — RILASCIO AL DISTACCO (%s): richiesta MANDATA al palco. "
		       " ⚠ Questa riga NON porta il numero, perche' chi lo sa e' il "
		       "figlio: il conto vero e' la riga «rilascio al distacco: N fra "
		       "tasti e pulsanti», qualche millisecondo piu' sotto",
		    perche);
		return;
	}
	reg(s, "⭐ §7.3 — RILASCIO AL DISTACCO (%s): %d fra tasti e pulsanti erano "
	       "premuti e sono stati rilasciati.  ⚠ Zero e' un esito normale e NON "
	       "e' un fallimento: vuol dire che non c'era niente giu'",
	    perche, quanti);
}

/* ⛔ §3.1 applicata a questo canale: si scrive CHE COSA — il tipo, il campo, il
 * valore, lo stato — e poi si congeda per tutt'e due le strade.  ⭐ Il `CONGEDO`
 * esce sul canale di CONTROLLO anche quando la violazione e' arrivata sullo
 * stream di input, ed e' §3.1 punto 2 alla lettera: «sul canale di controllo,
 * **se il canale di controllo e' ancora utilizzabile**» — e qui di solito lo e'. */
static void viola_input(rcp_sessione *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));
static void viola_input(rcp_sessione *s, const char *fmt, ...)
{
	char d[224];
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(d, sizeof d, fmt, ap);
	va_end(ap);
	congeda(s, RCP_ERRORE_PROTOCOLLO, d);
}

/* Quanti byte di corpo prevede questo tipo di §7.3.  ⛔ `0` = tipo che questo
 * canale non conosce, e allora e' `ERRORE_PROTOCOLLO` (§3): nessuno dei cinque
 * ha corpo vuoto, quindi lo zero non e' ambiguo. */
static uint32_t misura_input(uint16_t tipo)
{
	switch (tipo) {
	case T_PUNTATORE:
		return I_PUNTATORE;
	case T_PULSANTE:
		return I_PULSANTE;
	case T_ROTELLA:
		return I_ROTELLA;
	case T_LETTERA:
		return I_LETTERA;
	case T_POSIZIONE_TASTO:
		return I_POSIZIONE;
	default:
		return 0;
	}
}

static const char *nome_input(uint16_t tipo)
{
	switch (tipo) {
	case T_PUNTATORE:
		return "PUNTATORE";
	case T_PULSANTE:
		return "PULSANTE";
	case T_ROTELLA:
		return "ROTELLA";
	case T_LETTERA:
		return "LETTERA";
	case T_POSIZIONE_TASTO:
		return "POSIZIONE_TASTO";
	default:
		return "?";
	}
}

/* ⛔ I cinque ganci o nessuno — la stessa regola dei quattro del video, e per la
 * stessa ragione: un canale che sapesse muovere il puntatore e non sapesse
 * rilasciare un pulsante lascerebbe il desktop peggio di come l'ha trovato. */
static bool ha_canale_input(const rcp_sessione *s)
{
	return s->g.input_puntatore && s->g.input_pulsante && s->g.input_rotella &&
	       s->g.input_lettera && s->g.input_posizione;
}

/* ⛔⭐ IL SEGNAPUNTI DELL'INIEZIONE — e i tre esiti sono TRE, non due.
 *
 *   0  consegnato al compositore  ⇒ l'`id` avanza nel campo `input` di §6.2
 *  -1  non consegnato             ⇒ NON avanza, e si scrive
 *   1  (solo `LETTERA`) il carattere non e' producibile con la disposizione
 *      della sessione ⇒ NON avanza, e §7.3 OBBLIGA a scriverlo: «il server DEVE
 *      scriverlo nel registro e NON DEVE mandare un carattere diverso ne'
 *      tacere».
 *
 * ⛔ Nessuno dei tre e' una violazione del CLIENT: il messaggio era valido, e
 *    chiudere la sessione perche' il nostro compositore ha detto di no
 *    punirebbe chi non ha sbagliato niente — «una sessione brutta vale piu' di
 *    una sessione chiusa» (`CODER.md` §1). */
static void segna_iniezione(rcp_sessione *s, uint16_t tipo, uint32_t id,
                            int esito, const char *cosa)
{
	if (esito == 0) {
		s->inp_iniettati++;
		/* ⛔ §6.2: e' QUI che il numero che tornera' nei fotogrammi avanza —
		 * nell'unico punto in cui «iniettato» e' un fatto e non una speranza. */
		s->inp_ultimo_iniettato = id;
		return;
	}
	s->inp_non_iniettati++;
	if (esito == 1 && tipo == T_LETTERA)
		reg(s, "⛔ §7.3: la LETTERA %s (input id=%u) NON e' producibile con la "
		       "disposizione di questa sessione.  ⚠ Non si manda un carattere "
		       "diverso e non si tace: la riga e' questa, e il campo `input` dei "
		       "fotogrammi resta a %u perche' non e' stato iniettato niente",
		    cosa, id, s->inp_ultimo_iniettato);
	else
		reg(s, "⚠ %s (input id=%u, %s) NON e' stato consegnato al compositore "
		       "(esito %d): la sessione REGGE — il client non ha sbagliato "
		       "niente — e il campo `input` di §6.2 resta a %u",
		    nome_input(tipo), id, cosa, esito, s->inp_ultimo_iniettato);
}

/* ⛔ §7.3 — LE COORDINATE, e questa e' la funzione che ha gia' un rilievo
 *    (R1.16) scritto contro di se'.
 *
 *   «`0 ≤ x < tela_larghezza`, `0 ≤ y < tela_altezza`.  Su una tela 1920×1080
 *    l'angolo in basso a destra e' **1919, 1079**.»
 *
 * ⭐ Da cui i due casi che vanno tenuti separati, e sbagliarli e' costato un
 *    rilievo: **1919 su una tela 1920 PASSA** — e' l'ultimo pixel, non un
 *    errore — mentre **1920 su una tela 1920 NON passa**.  Il primo dei due e'
 *    quello che un controllo scritto con `>` invece di `>=` rovina in silenzio,
 *    e il sintomo sarebbe una colonna di pixel a destra che non si puo'
 *    cliccare.
 *
 * ⛔ E IL SECONDO DI GRAZIA (§7.1, terza eccezione di §3) e' l'altra meta':
 *    «una pagina che divide la posizione del mouse per il fattore di scala e
 *    arrotonda per eccesso produce 1920 su una tela di 1920: una lettura lo
 *    inietta, l'altra CHIUDE LA SESSIONE — e chiudere la sessione per un
 *    arrotondamento e' la cosa che `SPECIFICHE.md` §8.3 vieta».  ⇒ Per un
 *    secondo dopo un cambio di tela una coordinata valida sulla PRECEDENTE si
 *    SATURA all'ultimo pixel valido invece di uccidere la sessione.
 *
 * ⚠ Fuori da quel secondo, e fuori da un cambio di tela, il DEVE di §7.3 resta
 *   intero: chiudere.  ⛔ La grazia NON e' una tolleranza generale sulle
 *   coordinate — sarebbe l'indulgenza che §3 esiste per togliere — ed e' per
 *   questo che ha una data d'inizio e una durata.
 *
 * Restituisce `true` se si puo' iniettare; riempie `*sx`/`*sy` con quel che va
 * iniettato (uguale all'ingresso, salvo saturazione). */
static bool coordinate_ammesse(rcp_sessione *s, uint32_t id, uint32_t x,
                               uint32_t y, uint64_t ora, uint32_t *sx,
                               uint32_t *sy)
{
	*sx = x;
	*sy = y;
	/* ⛔ Il caso normale, e il confronto e' `<` perche' sono INDICI DI PIXEL. */
	if (x < s->tela_l && y < s->tela_a)
		return true;

	bool grazia_aperta = s->tela_prec_l != 0 && s->tela_prec_a != 0 &&
	                     ora >= s->tela_grazia_da &&
	                     ora - s->tela_grazia_da <= TELA_GRAZIA;
	if (grazia_aperta && x < s->tela_prec_l && y < s->tela_prec_a) {
		*sx = x < s->tela_l ? x : s->tela_l - 1;
		*sy = y < s->tela_a ? y : s->tela_a - 1;
		s->inp_grazie++;
		/* ⛔ §3: «ogni tolleranza va scritta nel registro.  Una tolleranza
		 * silenziosa e' indistinguibile da un difetto». */
		reg(s, "⭐ §7.1 SECONDO DI GRAZIA (%u-esima volta): input id=%u porta "
		       "(%u,%u), valida sulla tela precedente %ux%u e fuori dalla tela "
		       "in vigore %ux%u — SATURATA a (%u,%u) invece di chiudere.  Sono "
		       "passati %llu ms su %d dal cambio di tela",
		    s->inp_grazie, id, x, y, s->tela_prec_l, s->tela_prec_a, s->tela_l,
		    s->tela_a, *sx, *sy,
		    (unsigned long long)(ora - s->tela_grazia_da), TELA_GRAZIA);
		return true;
	}

	/* ⛔ §3.1 punto 1: si dice CHE COSA, e si dice anche perche' la grazia non
	 * copriva — «fuori intervallo» da solo manderebbe a cercare il difetto nel
	 * client anche quando il difetto e' un secondo scaduto di un millisecondo. */
	if (s->tela_prec_l && !grazia_aperta)
		viola_input(s, "PUNTATORE id=%u a (%u,%u): fuori dalla tela in vigore "
		               "%ux%u (§7.3: 0<=x<%u, 0<=y<%u), e il secondo di grazia "
		               "di §7.1 e' scaduto da %llu ms",
		            id, x, y, s->tela_l, s->tela_a, s->tela_l, s->tela_a,
		            (unsigned long long)(ora > s->tela_grazia_da + TELA_GRAZIA
		                                     ? ora - s->tela_grazia_da -
		                                           TELA_GRAZIA
		                                     : 0));
	else if (grazia_aperta)
		viola_input(s, "PUNTATORE id=%u a (%u,%u): fuori dalla tela in vigore "
		               "%ux%u E fuori dalla precedente %ux%u — la grazia di §7.1 "
		               "copre le coordinate della tela vecchia, non le "
		               "coordinate sbagliate",
		            id, x, y, s->tela_l, s->tela_a, s->tela_prec_l,
		            s->tela_prec_a);
	else
		viola_input(s, "PUNTATORE id=%u a (%u,%u): fuori dalla tela %ux%u — "
		               "§7.3 vuole 0<=x<%u e 0<=y<%u, e l'angolo in basso a "
		               "destra e' (%u,%u)",
		            id, x, y, s->tela_l, s->tela_a, s->tela_l, s->tela_a,
		            s->tela_l - 1, s->tela_a - 1);
	return false;
}

/* Un messaggio di input intero, gia' inquadrato.  `false` = sessione finita. */
static bool tratta_input(rcp_sessione *s, uint16_t tipo, const uint8_t *corpo,
                         uint32_t lung, uint64_t ora)
{
	lettore l = {corpo, lung, 0, false};
	uint32_t id = le_u32(&l);
	uint64_t istante = 0;
	for (int i = 0; i < 8; i++)
		istante = (istante << 8) | le_u8(&l);

	/* ⛔ §7.3: «⛔ 0 e' riservato e vuol dire "nessun input"».  E' il valore che
	 * §6.2 mette nel campo `input` dei fotogrammi quando non c'e' stato niente:
	 * accettarlo qui vorrebbe dire che un fotogramma non puo' piu' dire «non e'
	 * stato iniettato niente» senza dire anche «e' stato iniettato il primo» —
	 * cioe' il valore sentinella implicito che §6.0 vieta. */
	if (id == 0) {
		viola_input(s, "%s con id=0: §7.3 riserva lo zero e gli da' il "
		               "significato «nessun input» nel campo `input` dei "
		               "fotogrammi (§6.2)",
		            nome_input(tipo));
		return false;
	}
	/* ⛔⭐ §7.3: «cresce di ALMENO UNO a ogni messaggio, SU TUTTO IL CANALE DI
	 *     INPUT — non uno per tipo.  E' quello che torna nel campo `input` dei
	 *     fotogrammi (§6.2), e con contatori separati non tornerebbe niente».
	 *
	 * ⚠ «Almeno uno» e non «esattamente uno»: i salti sono leciti — un client
	 *   che scarta un evento suo non deve mentire sul numero — e quel che non e'
	 *   lecito e' tornare indietro o ripetersi.
	 *
	 * ⛔ E il caso che smaschera i contatori separati e' uno solo, e va messo nel
	 *    banco: `PULSANTE(9)` e poi `PUNTATORE(4)`.  Con un contatore per tipo
	 *    quel 4 e' un legittimo «primo PUNTATORE» e passa; con la regola scritta
	 *    e' una violazione.  Un banco che mandasse solo id crescenti dentro
	 *    ciascun tipo non distinguerebbe le due implementazioni. */
	if (id <= s->inp_ultimo_id) {
		viola_input(s, "%s con id=%u, e l'ultimo id di QUESTO CANALE era %u: "
		               "§7.3 vuole che cresca di almeno uno su tutto il canale, "
		               "non uno per tipo",
		            nome_input(tipo), id, s->inp_ultimo_id);
		return false;
	}

	uint32_t precedente = s->inp_ultimo_id;
	int esito = -1;
	char cosa[96];

	switch (tipo) {
	case T_PUNTATORE: {
		uint32_t x = le_u32(&l), y = le_u32(&l);
		uint32_t sx = 0, sy = 0;
		if (!coordinate_ammesse(s, id, x, y, ora, &sx, &sy))
			return false;
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		snprintf(cosa, sizeof cosa, "(%u,%u)", sx, sy);
		esito = ha_canale_input(s) ? s->g.input_puntatore(s->g.ctx, sx, sy) : -1;
		break;
	}
	case T_PULSANTE:
	case T_POSIZIONE_TASTO: {
		uint16_t codice = le_u16(&l);
		uint8_t premuto = le_u8(&l);
		/* ⛔ §7.3: «1 = premuto, 0 = rilasciato», e §3 chiude su «un campo fuori
		 * intervallo».  ⚠ Un 2 letto come «vero» sarebbe la forma esatta del
		 * parser indulgente: due implementazioni che si comportano uguale
		 * finche' una delle due non manda 2 per sbaglio, e allora il tasto resta
		 * giu' per sempre e nessuno sa perche'. */
		if (premuto > 1) {
			viola_input(s, "%s id=%u codice=%u con premuto=%u: §7.3 ammette 1 "
			               "(premuto) e 0 (rilasciato), e nient'altro",
			            nome_input(tipo), id, codice, premuto);
			return false;
		}
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		snprintf(cosa, sizeof cosa, "codice evdev %u (%#x) %s", codice, codice,
		         premuto ? "premuto" : "rilasciato");
		if (!ha_canale_input(s))
			esito = -1;
		else if (tipo == T_PULSANTE)
			esito = s->g.input_pulsante(s->g.ctx, codice, premuto);
		else
			esito = s->g.input_posizione(s->g.ctx, codice, premuto);
		break;
	}
	case T_ROTELLA: {
		/* ⛔ §6.0: `i32` in complemento a due.  Il cast da `uint32_t` a
		 * `int32_t` e' definito dall'implementazione fino a C17; qui si fa a
		 * mano, cosi' il valore non dipende dal compilatore. */
		uint32_t ux = le_u32(&l), uy = le_u32(&l);
		int32_t ax = (int32_t)(ux <= 0x7FFFFFFFu ? (int64_t)ux
		                                         : (int64_t)ux - 4294967296LL);
		int32_t ay = (int32_t)(uy <= 0x7FFFFFFFu ? (int64_t)uy
		                                         : (int64_t)uy - 4294967296LL);
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		/* ⛔⛔ E QUI NON SI TOCCA NIENTE: ne' il segno, ne' l'arrotondamento.
		 *
		 *     Il segno dell'asse verticale lo inverte `input_rotella()`, UNA
		 *     VOLTA SOLA e in un posto solo — sta scritto in `src/input.h` e in
		 *     `RCP.md` §7.3, riquadro «Il segno della rotella», `[M]` 10 agosto
		 *     2026.  ⛔ Invertirlo anche qui lo ANNULLA, e il sintomo — «la
		 *     rotella va al contrario» — e' la forma d'errore E11 che quel
		 *     riquadro esiste per evitare.
		 *
		 * ⚠ E i mezzi scatti esistono: 120 e' uno scatto, **60 e' mezzo scatto e
		 *   NON si arrotonda a zero**.  `STUDI.md` §gnome §9 dice che
		 *   `ei_device_scroll_discrete` fa una divisione intera per 120 e se li
		 *   mangia — ma quella e' una scelta di `input.c`, non di qui: da questo
		 *   lato il numero passa intero, com'e' arrivato. */
		snprintf(cosa, sizeof cosa, "asse_x=%ld asse_y=%ld (120 = uno scatto)",
		         (long)ax, (long)ay);
		esito = ha_canale_input(s) ? s->g.input_rotella(s->g.ctx, ax, ay) : -1;
		break;
	}
	case T_LETTERA: {
		uint32_t car = le_u32(&l);
		/* ⛔ §7.3: «un VALORE SCALARE UNICODE: da 0 a 0x10FFFF, esclusi i
		 * surrogati 0xD800-0xDFFF.  Fuori intervallo e' `ERRORE_PROTOCOLLO`».
		 *
		 * ⚠ «Valore scalare» e' il termine tecnico, e i surrogati sono
		 *   precisamente quel che lo distingue da «punto di codice»: un
		 *   controllo che si fermasse a `car > 0x10FFFF` lascerebbe passare
		 *   0xD800, che in UTF-8 non si puo' nemmeno scrivere.  ⛔ E' il caso
		 *   che una pagina produce da sola: JavaScript conta in UTF-16, e
		 *   `charCodeAt` su un'emoji restituisce **meta' coppia surrogata**.
		 *   Chi scrive il client con `charCodeAt` invece di `codePointAt` manda
		 *   0xD83D, e il difetto va visto qui — non iniettato come se fosse una
		 *   lettera.
		 *
		 * ⚠ E lo ZERO E' LECITO: U+0000 e' un valore scalare valido, e §7.3 dice
		 *   «da 0».  ⛔ Non e' un doppione della regola sull'`id`, dove lo zero e'
		 *   riservato: sono due campi diversi con due regole diverse, e
		 *   ricopiare la prima sulla seconda rifiuterebbe un carattere che
		 *   l'arbitro ammette. */
		if (car > 0x10FFFFu) {
			viola_input(s, "LETTERA id=%u con carattere U+%X: §7.3 vuole un "
			               "valore scalare Unicode, da 0 a 0x10FFFF",
			            id, car);
			return false;
		}
		if (car >= 0xD800u && car <= 0xDFFFu) {
			viola_input(s, "LETTERA id=%u con carattere U+%04X: e' meta' di una "
			               "coppia surrogata, e §7.3 li esclude — un valore "
			               "scalare Unicode non comprende 0xD800-0xDFFF",
			            id, car);
			return false;
		}
		s->inp_ultimo_id = id;
		s->inp_ultimo_istante_us = istante;
		snprintf(cosa, sizeof cosa, "U+%04X", car);
		esito = ha_canale_input(s) ? s->g.input_lettera(s->g.ctx, car) : -1;
		break;
	}
	default:
		/* Non ci si arriva: `misura_input()` ha gia' rifiutato i tipi che non
		 * conosce, prima di accumulare un byte.  La riga sta qui perche' il
		 * giorno in cui i due elenchi si separassero lo dicesse qualcuno. */
		viola_input(s, "tipo %#06x sul canale di input: §7.3 ne definisce cinque, "
		               "da 0x0101 a 0x0105",
		            tipo);
		return false;
	}

	s->inp_arrivati++;
	if (!ha_canale_input(s)) {
		/* ⛔ «Non ho un canale di input» NON e' «il client ha sbagliato».  Il
		 * messaggio era valido in ogni sua parte — l'abbiamo appena giudicato —
		 * e chiudere qui punirebbe chi non ha sbagliato niente.  ⚠ E' la stessa
		 * distinzione di `RCP_VIDEO_NIENTE_CANALE`, e il ripiego si DICHIARA
		 * (`CODER.md` §4.2): la riga e' questa. */
		s->inp_non_iniettati++;
		reg(s, "⚠ %s id=%u %s: VALIDO e NON iniettato — questo server non ha i "
		       "cinque ganci del canale di input (§7.3).  La sessione REGGE",
		    nome_input(tipo), id, cosa);
	} else {
		segna_iniezione(s, tipo, id, esito, cosa);
	}

	/* ⚠ L'`istante` compare nel registro e in nessun conto: §7.3 dice che
	 *   «nessuna regola di questo documento lo consuma», e che in una pagina la
	 *   grana e' deliberatamente ingrossata — `millisecondi × 1000` (rilievo
	 *   R1.27).  ⛔ Chi ne ricavasse un ritardo misurerebbe la grana del
	 *   `performance.now()` di un browser, non il nostro anello. */
	reg(s, "input id=%u (era %u) %s %s · istante del client %llu us ⚠ grana "
	       "ingrossata, §7.3: nessuna misura ci si costruisce sopra",
	    id, precedente, nome_input(tipo), cosa,
	    (unsigned long long)istante);
	return true;
}

/* ========================================================================= */
/* ⭐ IL CURSORE — `RCP.md` §7.2, §5.5, §5, §6.1                             */
/*                                                                           */
/* ⛔ CHI CONTROLLA CHE COSA, e la riga si legge una volta sola:              */
/*                                                                           */
/*    · i limiti di **§5.5** — 256 per lato, il punto attivo dentro           */
/*      l'immagine, `0×0` con `0,0` per il nascosto — li fa rispettare        */
/*      `src/cursore.c` (A6), e QUI NON SI RICONTROLLANO.  Due controlli      */
/*      sulla stessa regola in due posti diventano due regole diverse il      */
/*      giorno in cui una cambia, ed e' la forma di difetto che `RCP.md` §0   */
/*      esiste per impedire;                                                  */
/*    · la **lunghezza del messaggio** e' di questo modulo, e §7.2 la scrive  */
/*      con un DEVE: «la lunghezza del messaggio DEVE valere esattamente      */
/*      `8 + larghezza × altezza × 4`».                                       */
/*                                                                           */
/* ⛔⭐ E LA CONSEGUENZA DI SBAGLIARLA E' NOSTRA, NON DEL CLIENT: §7.2 dice   */
/*     che una lunghezza che non torna e' `ERRORE_PROTOCOLLO` — ma a          */
/*     rilevarla e' CHI RICEVE.  ⇒ Un messaggio storto spedito da qui fa      */
/*     chiudere la sessione **alla pagina**, e il registro del server non ne  */
/*     saprebbe niente.  «Un cursore fatto di memoria altrui» e' il sintomo   */
/*     che §7.2 nomina; la sessione persa e' quello che vede l'utente.        */
/*                                                                           */
/* ⇒ Da cui la regola di questa funzione: **nel dubbio non si manda**, e si   */
/*   scrive perche' (`CODER.md` §4.2 — il ripiego si DICHIARA).  Un cursore   */
/*   che non si aggiorna e' brutto; una sessione che cade e' rotta.           */

int rcp_cursore_forma(rcp_sessione *s, uint16_t larghezza, uint16_t altezza,
                      int16_t attivo_x, int16_t attivo_y,
                      const uint8_t *immagine, size_t immagine_n)
{
	if (!s)
		return -1;
	/* §5: il cursore vive sul canale di CONTROLLO, e prima di `SESSIONE` non
	 * c'e' nessuno che lo disegni — il client non e' ancora attaccato (§4.5).
	 * ⚠ Non e' una violazione di nessuno: e' una forma arrivata troppo presto
	 *   dalla cattura, che parte prima che il client si attacchi. */
	if (s->stato == S_FINITA || !s->sessione_spedita) {
		reg(s, "⚠ CURSORE_FORMA %ux%u NON spedita: `SESSIONE` non e' partita "
		       "(stato %s) — §5, e non e' un errore di nessuno: la cattura "
		       "comincia prima che il client si attacchi",
		    larghezza, altezza, NOMI_STATO[s->stato]);
		return -1;
	}

	/* ⛔⭐ §5.5 — «UNA SOLA DELLE DUE A ZERO E' `ERRORE_PROTOCOLLO`», e questo
	 *     controllo sta QUI ANCHE SE STA GIA' IN `cursore.c` — deciso dal
	 *     coordinatore il 14 agosto 2026, dopo che questo rapporto lo aveva
	 *     segnalato come buco aperto.
	 *
	 * ⛔ E NON e' tornare a duplicare i limiti di §5.5: la divisione e' un'altra,
	 *    e va letta perche' e' la ragione per cui questa riga non contraddice il
	 *    riquadro qui sopra —
	 *
	 *      `cursore.c` decide **che cos'e'** quel cursore: quanto e' grande,
	 *                  dov'e' il punto attivo, se e' nascosto o non pervenuto;
	 *      `rcp.c`     ⛔ non deve **EMETTERE** un messaggio che la specifica
	 *                  vieta, MAI, da nessuna strada.
	 *
	 * ⛔⭐ E QUESTO E' L'UNICO CASO IN CUI IL CONTROLLO DI LUNGHEZZA — che e'
	 *     giusto — **NON BASTA**: `0×5` da' `0 × 5 × 4 = 0` byte d'immagine,
	 *     cioe' un messaggio di **otto byte** la cui lunghezza **TORNA**.  Il
	 *     valore malformato passa proprio il controllo che dovrebbe fermarlo, e
	 *     nessuna delle altre righe di questa funzione lo guarda.
	 *
	 * ⚠ Il prezzo di non averlo: se un domani qualcuno chiamasse questa funzione
	 *   da una strada che non passa da `cursore.c`, il client riceverebbe un
	 *   messaggio che §5.5 gli ORDINA di rifiutare ⇒ **cadrebbe la sessione per
	 *   colpa nostra**, e il registro del server non ne saprebbe niente.
	 *
	 * ⛔ E la coppia si distingue solo con tutt'e due i casi nel banco: `0×0` e'
	 *    il cursore NASCOSTO e **deve passare**, `0×5` e `5×0` no.  Un controllo
	 *    che rifiutasse tutti gli zeri sarebbe verde col solo `0×0` — e farebbe
	 *    sparire per sempre il cursore nascosto, cioe' il sintomo «il puntatore
	 *    resta fermo quando entro in un campo di testo». */
	if ((larghezza == 0) != (altezza == 0)) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NON spedita: §5.5 vuole le due misure a "
		       "zero INSIEME per il cursore nascosto, e «una sola delle due a "
		       "zero e' ERRORE_PROTOCOLLO».  ⚠ La lunghezza TORNEREBBE (8 byte, "
		       "nessun pixel): e' l'unico caso in cui il controllo di lunghezza "
		       "non basta, e spedirla farebbe chiudere la sessione ALLA PAGINA",
		    larghezza, altezza);
		return -1;
	}

	/* ⛔ §7.2 — LA LUNGHEZZA, e si CALCOLA in un posto solo.
	 *
	 * ⚠ `(size_t)` sui fattori, e non e' pedanteria: `larghezza` e `altezza`
	 *   sono `uint16_t` e in C promuovono a `int`.  `65535 * 65535 * 4` in
	 *   `int` e' **traboccamento con segno**, cioe' comportamento indefinito —
	 *   il compilatore e' libero di dare qualunque cosa, e con `-O2` di solito
	 *   da' un numero piccolo.  E' lo stesso difetto che la certificazione del
	 *   banco ha trovato il 14 agosto 2026 su `6u + lung`, in un altro campo e
	 *   con lo stesso meccanismo: l'aritmetica stretta che nessuno guarda. */
	size_t pixel = (size_t)larghezza * (size_t)altezza;
	size_t byte_immagine = pixel * 4u;

	/* ⛔ La lunghezza dichiarata dal chiamante e quella che §7.2 impone devono
	 * combaciare.  ⭐ E il confronto NON e' una formalita': senza `immagine_n`
	 * questa funzione leggerebbe `larghezza × altezza × 4` byte **sulla fiducia**
	 * — cioe' farebbe esattamente quel che §7.2 descrive come «leggo quel che
	 * c'e' e vado avanti», solo dal lato del mittente, dove il cursore fatto di
	 * memoria altrui lo confezioniamo noi. */
	if (byte_immagine != immagine_n) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NON spedita: §7.2 vuole %zu byte "
		       "d'immagine (8 + %ux%ux4 nel messaggio) e chi chiama ne porta "
		       "%zu.  ⚠ Spedirla farebbe chiudere la sessione ALLA PAGINA per "
		       "ERRORE_PROTOCOLLO, e questo registro non lo saprebbe",
		    larghezza, altezza, byte_immagine, larghezza, altezza, immagine_n);
		return -1;
	}
	/* ⛔ «Zero byte» e «nessun puntatore» sono due fatti diversi: il cursore
	 * NASCOSTO di §5.5 e' `0×0` **e** nessun byte, e li' `NULL` e' giusto.  Con
	 * una misura addosso, invece, un `NULL` e' un difetto di chi chiama — e
	 * leggerlo sarebbe la fine del processo. */
	if (byte_immagine && !immagine) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NON spedita: la misura vuole %zu byte e "
		       "il puntatore all'immagine e' NULL",
		    larghezza, altezza, byte_immagine);
		return -1;
	}

	/* ⛔ §6.1 — «nessun messaggio DEVE superare 1 MiB», inquadratura compresa
	 * (rilievo B-14).  ⭐ QUESTA regola e' di questo modulo, non di `cursore.c`:
	 * la' vive §5.5 (256 per lato), qui §6.1 — e sono due paragrafi diversi con
	 * due numeri diversi.  ⚠ Al massimo che §5.5 concede, 256×256, il messaggio
	 * pesa 262 158 byte: **passa**, e deve passare.  Un tetto messo male qui
	 * ucciderebbe il cursore piu' grande che l'arbitro ammette. */
	if (byte_immagine + 8u + 6u > MAX_MESSAGGIO) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NON spedita: il messaggio peserebbe %zu "
		       "byte e §6.1 ne ammette %u, inquadratura compresa.  ⚠ §5.5 ferma "
		       "a 256 per lato e a quella misura sono 262 158: se si arriva qui, "
		       "il limite di §5.5 non e' stato fatto rispettare a monte",
		    larghezza, altezza, byte_immagine + 8u + 6u, MAX_MESSAGGIO);
		return -1;
	}

	/* ⛔ §7.2 — GLI OTTO BYTE, IN QUEST'ORDINE E SENZA RIEMPIMENTO (§6.0):
	 *   0 larghezza u16 · 2 altezza u16 · 4 attivo_x i16 · 6 attivo_y i16 · 8 …
	 *
	 * ⚠ `serie` di `CursoreForma` NON viaggia: e' il numero con cui `cursore.c`
	 *   riconosce che la forma non e' cambiata, e §7.2 non lo prevede.  Metterlo
	 *   sul filo sarebbe un campo che due implementazioni indovinano diverso.
	 * ⚠ E la POSIZIONE non c'e', perche' §7.2 dice che «non viaggia mai in
	 *   questo verso»: qui viaggia solo la forma. */
	size_t n = 8u + byte_immagine;
	uint8_t *corpo = (uint8_t *)malloc(n);
	if (!corpo) {
		reg(s, "⛔ CURSORE_FORMA %ux%u NON spedita: memoria esaurita (%zu byte)",
		    larghezza, altezza, n);
		return -1;
	}
	scrittore w = {corpo, n, 0, false};
	sc_u16(&w, larghezza);
	sc_u16(&w, altezza);
	/* §6.0: `i16` in complemento a due, big-endian.  La conversione verso
	 * `uint16_t` e' definita dal linguaggio e da' esattamente quei bit. */
	sc_u16(&w, (uint16_t)attivo_x);
	sc_u16(&w, (uint16_t)attivo_y);
	if (byte_immagine)
		memcpy(corpo + 8, immagine, byte_immagine);
	/* ⛔⭐ E SI SPEDISCE `n`, NON `w.len` — trovato dal banco al primo giro, il
	 *     14 agosto 2026.
	 *
	 *     `scrittore` conta i byte che sono passati DA LUI, e l'immagine ci
	 *     arriva con una `memcpy` che `w.len` non vede: dopo i quattro `sc_u16`
	 *     vale **8**, e mandare `w.len` spediva un `CURSORE_FORMA` che dichiara
	 *     `larghezza=16, altezza=16` con **otto byte di corpo**.
	 *
	 * ⛔ Cioe' esattamente la lunghezza che non torna, prodotta da noi: la pagina
	 *    avrebbe chiuso con `ERRORE_PROTOCOLLO` a ogni cambio di forma del
	 *    cursore, e il sintomo per l'utente sarebbe stato «la sessione cade
	 *    quando muovo il mouse su un bordo».  ⚠ Il registro del server scriveva
	 *    la riga giusta — «%zu byte di corpo = 8 + 16x16x4» — perche' la
	 *    calcolava da `n`: **il registro diceva il vero e il filo un'altra
	 *    cosa**, che e' la forma di difetto per cui `CODER.md` §3.8 vuole che si
	 *    verifichi dal lato che riceve.
	 *
	 * ⭐ A vederlo non e' stata una rilettura: e' stato il giudice, che riapre i
	 *    byte usciti e rifa' il conto di §7.2 su quelli. */
	if (w.pieno || w.len != 8u) {
		/* Non ci si arriva: `corpo` e' grande `n` e i campi sono otto byte.  La
		 * riga c'e' perche' il giorno in cui non fosse piu' vero lo dicesse
		 * qualcuno, invece di spedire un messaggio storto. */
		reg(s, "⛔ CURSORE_FORMA NON spedita: gli otto byte dei campi non sono "
		       "usciti (scritti %zu)",
		    w.len);
		free(corpo);
		return -1;
	}

	/* ⛔⭐ L'IMMAGINE SI COPIA QUI DENTRO, E LA CHIAMATA NON LA TIENE.
	 *
	 *     `src/cursore.h` lo dice: «vive fino al richiamo successivo: chi la
	 *     vuole tenere la copia».  ⇒ Quando questa funzione torna, questo modulo
	 *     non ha piu' nessun puntatore a quei byte.
	 *
	 * ⚠ Il prezzo, dichiarato: i byte si copiano DUE volte — qui dentro
	 *   `corpo`, e poi in `manda_messaggio()` che ci mette davanti i sei byte
	 *   d'inquadratura.  ⛔ Si paga apposta: l'inquadratura di §6.1 si scrive in
	 *   UN posto solo, e ricopiarla qui per risparmiare una `memcpy` metterebbe
	 *   due lettori sullo stesso campo.  Al massimo di §5.5 sono 256 KiB su un
	 *   evento che accade quando la FORMA cambia — non a ogni fotogramma, perche'
	 *   `cursore.c` toglie i ripetuti. */
	manda_messaggio(s, T_CURSORE_FORMA, corpo, n);
	free(corpo);

	if (larghezza == 0 && altezza == 0)
		reg(s, "⭐ CURSORE_FORMA: cursore NASCOSTO (§5.5), 8 byte di corpo");
	else
		reg(s, "⭐ CURSORE_FORMA %ux%u spedita, punto attivo (%d,%d): %zu byte "
		       "di corpo = 8 + %ux%ux4 (§7.2)",
		    larghezza, altezza, attivo_x, attivo_y, n, larghezza, altezza);
	return 0;
}

uint32_t rcp_input_ultimo_iniettato(const rcp_sessione *s)
{
	return s ? s->inp_ultimo_iniettato : 0;
}

uint32_t rcp_input_ultimo_id(const rcp_sessione *s)
{
	return s ? s->inp_ultimo_id : 0;
}

bool rcp_ricevi_input(rcp_sessione *s, int64_t stream, const uint8_t *dati,
                      size_t len, uint64_t ora)
{
	if (!s)
		return false;
	if (s->stato == S_FINITA) {
		/* ⚠ Come in `rcp_ricevi()`: e' l'unico posto da cui si osserva un
		 *   client che spedisce dopo la fine (§4.2), e tacere renderebbe
		 *   indistinguibile chi insiste da chi si e' fermato.  ⛔ Ma qui non si
		 *   giudica «commiato o tentativo»: §8.1 il commiato lo vuole sul canale
		 *   di CONTROLLO, e un `CONGEDO` su questo stream sarebbe comunque un
		 *   canale nel verso sbagliato. */
		reg(s, "⛔ %zu byte sullo stream di input %lld DOPO la fine della "
		       "sessione da %s: §4.2 vieta di spedire su qualunque canale",
		    len, (long long)stream, s->provenienza);
		return false;
	}

	/* ⛔⭐ §2.5 — «lo stream di input si apre DOPO aver ricevuto `SESSIONE`».
	 *
	 *     ⚠ E la grandezza da guardare e' «`SESSIONE` E' PARTITA», non «lo stato
	 *       e' attiva»: e' la stessa scelta gia' fatta per il video, e per la
	 *       stessa ragione (vedi il campo `sessione_spedita`).
	 *
	 * ⛔⭐ E QUESTA VOLTA IL GIUDIZIO E' LEGITTIMO, mentre il gemello di P20 non
	 *     lo era, e vale la pena dire perche': la' il CLIENT non poteva misurare
	 *     l'ordine fra due stream indipendenti; qui il SERVER misura una cosa
	 *     che ha fatto LUI — se ha spedito `SESSIONE` o no.  E' la «grandezza
	 *     locale, monotona, indipendente dalla consegna» di P20, dal lato
	 *     giusto: se `SESSIONE` non e' partita, il client non l'ha ricevuta, e
	 *     nessuna perdita di pacchetti puo' cambiarlo. */
	if (!s->sessione_spedita) {
		viola_input(s, "byte sullo stream di input (%lld) prima che `SESSIONE` "
		               "sia partita: §2.5 lo apre DOPO averla ricevuta (stato: "
		               "%s)",
		            (long long)stream, NOMI_STATO[s->stato]);
		return false;
	}

	/* ⛔ §2.5: «**uno solo**, e tenuto aperto». */
	if (!s->inp_stream_noto) {
		s->inp_stream_noto = true;
		s->inp_stream = stream;
		reg(s, "⭐ canale di INPUT aperto sullo stream %lld (§2.5: uno solo, "
		       "dopo `SESSIONE`, e tenuto aperto).  I ganci d'iniezione: %s",
		    (long long)stream,
		    ha_canale_input(s) ? "collegati" : "⚠ NON collegati");
	} else if (stream != s->inp_stream) {
		viola_input(s, "un SECONDO stream di input (%lld) mentre il primo (%lld) "
		               "e' ancora quello: §2.5 ne ammette uno solo",
		            (long long)stream, (long long)s->inp_stream);
		return false;
	}

	/* ⛔ L'orologio del silenzio (§5.3) si azzera anche sui byte dell'input, e
	 * non e' una comodita': senza questa riga chi usa il desktop **senza
	 * scrivere niente sul canale di controllo** — cioe' chiunque stia solo
	 * muovendo il mouse — perde il posto dopo trenta secondi mentre sta
	 * lavorando.  §5.3 dice «senza un byte DAL CLIENT», e questi sono byte del
	 * client. */
	s->ultimo_byte = ora;
	/* ⛔⭐ E ANCHE IL SEGNO DI VITA, per una ragione che viene prima della
	 *     comodita': **un byte di RCP e' arrivato dentro un pacchetto**.  Se
	 *     il byte c'e', il pacchetto c'era — dirlo qui non e' una scorciatoia,
	 *     e' la stessa cosa detta dove si vede.
	 *
	 * ⚠ E rende `rcp_segno_di_vita()` una PURA AGGIUNTA: copre il caso in cui
	 *   arrivano pacchetti SENZA byte di RCP — cioe' l'utente che guarda e non
	 *   tocca, che e' il caso per cui e' nata.  ⛔ Senza questa riga i banchi
	 *   in processo (`04-b31`, `01-b12`) non avrebbero nessun segno di vita:
	 *   non passano dal trasporto, e si staccherebbero trenta secondi dopo
	 *   l'apertura qualunque cosa facessero. */
	s->ultima_vita = ora;
	if (!torna_a_parlare(s))
		return false;

	while (len) {
		/* ⛔⭐ LA LUNGHEZZA SI CONTROLLA SUI SEI BYTE DELL'INTESTAZIONE, PRIMA DI
		 *     ACCUMULARE UN BYTE DI CORPO — §6.1: «la lunghezza si controlla
		 *     prima di allocare.  Un ricevente che alloca `lunghezza` byte e poi
		 *     verifica ha gia' regalato un megabyte a chiunque sappia scrivere
		 *     sei byte».
		 *
		 * ⭐ Su questo canale si puo' fare fino in fondo, e sul controllo no: i
		 *    cinque tipi di §7.3 hanno una lunghezza FISSA, nota dal solo
		 *    `tipo`.  ⇒ L'accumulo non supera mai 26 byte, e chi annuncia un
		 *    megabyte ne ottiene sei e un congedo. */
		size_t spazio = I_ACCUMULO - s->inp_acc_len;
		size_t quanti = len < spazio ? len : spazio;
		if (quanti == 0) {
			/* Non ci si arriva finche' la potatura qui sotto funziona: la riga
			 * c'e' perche' il giorno in cui non funzionasse lo dicesse qualcuno,
			 * invece di girare in tondo. */
			viola_input(s, "accumulo dello stream di input pieno (%zu byte) "
			               "senza un messaggio intero: e' un difetto NOSTRO",
			            s->inp_acc_len);
			return false;
		}
		memcpy(s->inp_acc + s->inp_acc_len, dati, quanti);
		s->inp_acc_len += quanti;
		dati += quanti;
		len -= quanti;

		for (;;) {
			if (s->inp_acc_len < 6)
				break;
			lettore intest = {s->inp_acc, s->inp_acc_len, 0, false};
			uint16_t tipo = le_u16(&intest);
			uint32_t lung = le_u32(&intest);

			/* ⛔ §2.5: su questo stream il byte alto e' 0x01.  Un `0x00` qui e'
			 * «il canale di controllo su uno stream unidirezionale», un `0x03`
			 * e' «il video dal client»: sono violazioni con nomi diversi, e §3.1
			 * punto 1 vuole il nome. */
			if ((tipo >> 8) != 0x01) {
				const char *chi = (tipo >> 8) == 0x00   ? "il CONTROLLO, che vive "
				                                          "solo sul primo stream "
				                                          "bidirezionale"
				                  : (tipo >> 8) == 0x02 ? "gli APPUNTI, che "
				                                          "vogliono uno stream "
				                                          "loro per trasferimento"
				                  : (tipo >> 8) == 0x03 ? "il VIDEO, che e' del "
				                                          "server e va nell'altro "
				                                          "verso"
				                  : (tipo >> 8) == 0x04 ? "l'AUDIO, che vive solo "
				                                          "sui datagram"
				                                        : "un canale che §2.5 non "
				                                          "definisce";
				/* ⚠ `0x%02x` e non `%#04x`: quest'ultimo, sul valore ZERO, non
				 *   stampa il prefisso — scrive `0000` — e il canale di
				 *   controllo e' proprio lo `0x00`.  Il byte alto piu'
				 *   importante di tutti sarebbe stato l'unico illeggibile. */
				viola_input(s, "tipo %#06x sullo stream di input: il byte alto "
				               "0x%02x e' %s (§2.5)",
				            tipo, (unsigned)(tipo >> 8), chi);
				return false;
			}

			uint32_t attesa = misura_input(tipo);
			if (attesa == 0) {
				viola_input(s, "tipo %#06x sul canale di input: §7.3 ne "
				               "definisce CINQUE — 0x0101 PUNTATORE, 0x0102 "
				               "PULSANTE, 0x0103 ROTELLA, 0x0104 LETTERA, 0x0105 "
				               "POSIZIONE_TASTO",
				            tipo);
				return false;
			}
			/* ⛔ §6.1: «`lunghezza` DEVE essere il numero esatto dei byte del
			 * corpo.  Un ricevente che legge una lunghezza incoerente con quel
			 * che il tipo prevede DEVE chiudere».  ⚠ E si dice da che parte
			 * sbaglia: «in piu'» e «in meno» mandano a cercare due difetti
			 * diversi nel client. */
			if (lung != attesa) {
				if (lung > MAX_CORPO)
					viola_input(s, "%s (%#06x) annuncia %u byte di corpo: oltre "
					               "il tetto di 1 MiB di §6.1, e §7.3 ne vuole "
					               "%u esatti",
					            nome_input(tipo), tipo, lung, attesa);
				else
					viola_input(s, "%s (%#06x) annuncia %u byte di corpo e §7.3 "
					               "ne prevede %u (%u di id+istante piu' %u "
					               "suoi): %s",
					            nome_input(tipo), tipo, lung, attesa, I_COMUNI,
					            attesa - I_COMUNI,
					            lung > attesa ? "byte in PIU', e §6.0 non ammette "
					                            "riempimento"
					                          : "byte in MENO");
				return false;
			}
			/* ⛔⭐ `(size_t)6u`, E NON `6u` — trovato dalla certificazione del
			 *     banco il 14 agosto 2026, innestando il guasto
			 *     `lunghezza-tardiva`.
			 *
			 *     `lung` e' `uint32_t`: `6u + lung` si calcola a **32 bit**, e
			 *     con `lung = 0xFFFFFFFF` il risultato non e' 4 294 967 301 —
			 *     e' **5**.  ⇒ Un confronto `inp_acc_len < 6u + lung` direbbe
			 *     «il corpo e' tutto arrivato» dopo sei byte, e si leggerebbero
			 *     quattro gigabyte di memoria altrui a partire da un accumulo di
			 *     32.
			 *
			 * ⚠ Qui NON e' raggiungibile — il controllo `lung != attesa` sta
			 *   sopra e chiude prima — ma «non raggiungibile oggi» e «non
			 *   pericoloso» sono due fatti diversi: chi domani spostasse quel
			 *   controllo di tre righe rimetterebbe la lettura fuori dai limiti
			 *   senza che niente cambiasse colore.  ⭐ E' l'invariante I7 letta
			 *   da dentro: la protezione sta nel programma, non nell'ordine in
			 *   cui qualcuno ha lasciato due `if`. */
			if (s->inp_acc_len < (size_t)6u + lung)
				break; /* il corpo non e' tutto arrivato */

			if (!tratta_input(s, tipo, s->inp_acc + 6, lung, ora))
				return false;

			size_t consumati = (size_t)6u + lung;
			memmove(s->inp_acc, s->inp_acc + consumati,
			        s->inp_acc_len - consumati);
			s->inp_acc_len -= consumati;
		}
	}
	return true;
}

/* ⛔ §5.2 e §7.1 — `RICHIEDI_CHIAVE`, servito dal 12 agosto 2026.
 *
 * ⚠ Fino a oggi questo tipo cadeva nel `default` dello switch e faceva
 *   **perdere la sessione** a un client conforme che avesse visto un buco: il
 *   registro lo dichiarava («la fase 1 non lo serve ancora»), e il prezzo era
 *   dichiarato ma reale.  Con il canale video quel prezzo non si puo' piu'
 *   pagare, perche' §5.2 obbliga il client a mandarlo.
 *
 * ⛔ E l'ORLOGIO SI CONTA DALL'ULTIMA CHIAVE SPEDITA, non dall'ultima richiesta
 *    ricevuta: «contando dalle richieste, due client insistenti spostano
 *    l'orologio all'infinito e la chiave non parte mai».                     */
static bool tratta_richiedi_chiave(rcp_sessione *s, lettore *l, uint64_t ora)
{
	uint32_t ultimo = le_u32(l);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "RICHIEDI_CHIAVE senza `ultimo_numero`");
		return false;
	}
	/* §5.2: la si serve solo a sessione aperta — prima non ci sono fotogrammi
	 * di cui accorgersi. */
	if (!s->sessione_spedita) {
		congeda(s, RCP_ERRORE_PROTOCOLLO,
		        "RICHIEDI_CHIAVE prima di SESSIONE: non c'e' nessun fotogramma");
		return false;
	}
	/* ⛔ §7.1: «`ultimo_numero`: l'ultimo fotogramma decodificato, **0 se
	 * nessuno**».  E' il significato che P2 ha riservato allo zero in §6.2:
	 * qui si legge, non si indovina. */
	if (!s->mai_spedita_una_chiave && ora - s->ultima_chiave_ms < V_GRAZIA_CHIAVE) {
		/* ⛔ §3: «ogni tolleranza va scritta nel registro.  Una tolleranza
		 * silenziosa e' indistinguibile da un difetto».  E' l'eccezione 5. */
		reg(s, "⚠ TOLLERANZA DICHIARATA (§3 eccezione 5, §5.2): "
		       "RICHIEDI_CHIAVE(ultimo_numero=%u) ignorata — sono passati %llu "
		       "ms dall'ultima CHIAVE spedita, meno dei %d ammessi",
		    ultimo, (unsigned long long)(ora - s->ultima_chiave_ms),
		    V_GRAZIA_CHIAVE);
		return true;
	}
	reg(s, "RICHIEDI_CHIAVE(ultimo_numero=%u) accolta (§5.2): il prossimo "
	       "fotogramma sara' una CHIAVE — ultimo spedito da noi: %u",
	    ultimo, s->video_numero);
	s->serve_chiave = true;
	s->serve_chiave_perche = "il client ne ha chiesta una (§5.2)";
	return true;
}

/* ------------------------------------------------------------------------ */
/* ⭐ §7.5 — LA FUNZIONE DI BANCO, E IL CASO CHE NON DEVE FAR CADERE NIENTE
 *
 * ⛔ Questo e' l'unico messaggio del canale di controllo a cui un server
 *    conforme risponde **rifiutando senza chiudere**.  Le due regole:
 *
 *    regola 2  spenta -> `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`.  ⛔ NON
 *              DEVE tacere e NON DEVE chiudere: «un client che chiede una
 *              funzione spenta non ha violato niente», e un silenzio lascia il
 *              banco della fase 3 ad aspettare per sempre — il sintomo sarebbe
 *              «il banco si e' piantato», che non nomina ne' la funzione ne'
 *              l'interruttore;
 *    regola 4  `ritardo_ms` fuori da 0..10 000 -> `RITARDO_FUORI_LIMITI`, e
 *              ⛔ **non** `ERRORE_PROTOCOLLO`: far cadere la sessione al banco
 *              che si sta tarando e' la stessa cattiva idea che §7.1 evita per
 *              le misure fuori limite.
 *
 * ⚠ E l'ORDINE fra le due `RCP.md` non lo dice: con la funzione spenta E il
 *   ritardo fuori limite, i motivi difendibili sono due.  ⭐ Qui si controlla
 *   PRIMA il parametro, perche' e' quello che il banco puo' correggere: dirgli
 *   «spenta» quando ha anche sbagliato il numero gli fa accendere la funzione e
 *   ritrovarsi lo stesso rifiuto, con un motivo diverso, al secondo giro.  La
 *   scelta e' dichiarata in `fasi/01-filo-nudo.md`.
 *
 * ⛔ Regola 5: ogni `BANCO_MARCA` si scrive nel registro — anche i rifiuti.
 *    «Una sessione che dipinge quadratini colorati sul desktop di una persona
 *    deve poterlo dimostrare dal registro.» */
static bool tratta_banco_marca(rcp_sessione *s, lettore *l)
{
	uint32_t id = le_u32(l), colore = le_u32(l), ritardo = le_u32(l);
	if (l->corto) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "BANCO_MARCA troncato");
		return false;
	}
	/* ⛔ §7.5: «0 e' riservato».  Un id zero non e' un parametro di banco
	 * sbagliato, e' un messaggio malformato: qui la sessione cade.
	 * ⚠ Scelta nostra — il documento dice «riservato» e non dice l'esito. */
	if (id == 0) {
		congeda(s, RCP_ERRORE_PROTOCOLLO, "BANCO_MARCA con id 0, che e' riservato");
		return false;
	}

	uint8_t esito = BANCO_RIFIUTATA, motivo;
	if (ritardo > BANCO_RITARDO_MAX) {
		motivo = BANCO_RITARDO_FUORI_LIMITI;
	} else if (!BANCO_ACCESO) {
		motivo = BANCO_FUNZIONE_SPENTA;
	} else {
		/* In fase 1 non c'e' nessun fotogramma su cui dipingere: la funzione
		 * resta spenta, e questo ramo esiste per non far dimenticare che
		 * l'accensione va scritta nel registro (regola 5). */
		esito = BANCO_ACCETTATA;
		motivo = 0;
	}
	reg(s, "BANCO_MARCA id=%u colore=%#08x ritardo=%u ms -> %s motivo=%u",
	    id, colore, ritardo,
	    esito == BANCO_ACCETTATA ? "ACCETTATA" : "RIFIUTATA", motivo);

	uint8_t corpo[32];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_u32(&w, id);
	sc_byte(&w, esito);
	sc_byte(&w, motivo);
	/* ⛔ `istante`: 0 se rifiutata, «ed e' l'unico significato di *assente*
	 * per questo campo» (§6.0). */
	for (int i = 0; i < 8; i++)
		sc_byte(&w, 0);
	if (!w.pieno)
		manda_messaggio(s, T_BANCO_ESITO, corpo, w.len);
	/* ⭐ E la sessione RESTA APERTA. */
	return true;
}

/* ------------------------------------------------------------------------ */
rcp_sessione *rcp_apri(const rcp_ganci *g, const char *provenienza,
                       uint64_t ora_ms)
{
	rcp_sessione *s = (rcp_sessione *)calloc(1, sizeof *s);
	if (!s)
		return NULL;
	s->g = *g;
	s->stato = S_ATTESA_CIAO;
	s->da_quando = ora_ms;
	s->ultimo_byte = ora_ms;
	/* ⛔ E ANCHE QUESTO parte da adesso, non da zero: una sessione appena
	 *    aperta non ha ancora visto passare un pacchetto per le mani di questo
	 *    modulo, e uno zero la farebbe staccare per silenzio al primo giro. */
	s->ultima_vita = ora_ms;
	snprintf(s->provenienza, sizeof s->provenienza, "%s",
	         provenienza ? provenienza : "?");
	rcp_chiave_indirizzo(s->provenienza, s->indirizzo, sizeof s->indirizzo);
	reg(s, "canale di controllo aperto da %s (indirizzo per §4.4-bis: %s)",
	    s->provenienza, s->indirizzo);
	/* ⛔ §7.5 regola 5 e §4.3: «un server che la dichiarasse `si` per errore lo
	 * scrive nel registro a ogni avvio».  Questo modulo non ha un avvio — non
	 * apre socket e non legge configurazioni — e il primo momento che vede e'
	 * l'apertura di un canale: la riga sta qui (rilievo R9.14).  ⚠ Chi
	 * diagnostica un quadratino colorato sul desktop di qualcuno deve poter
	 * risalire alla riga che dice che la funzione era accesa. */
	if (BANCO_ACCESO)
		reg(s, "⛔ la FUNZIONE DI BANCO e' ACCESA (§7.5): questo server accetta "
		       "BANCO_MARCA e dipinge sopra il desktop, e `ECCOMI` dichiara "
		       "banco.marca=si");
	return s;
}

void rcp_libera(rcp_sessione *s)
{
	if (!s)
		return;
	/* ⛔ §7.3 — l'ultima delle strade, e la rete di sicurezza di tutte le altre:
	 * qualunque cosa sia successa, di qui si passa.  ⚠ `inp_rilasciato` impedisce
	 * da solo di rilasciare due volte. */
	rilascia_al_distacco(s, "la sessione si libera");
	/* ⛔ §6.2 — UNO STREAM VIDEO LASCIATO A META' SI AZZERA, NON SI ABBANDONA
	 * AL TRASPORTO.  Un fotogramma aperto quando la sessione finisce e' per
	 * definizione incompleto: azzerarlo lo dice, ed e' l'unica chiusura che
	 * significa «buttalo».  ⚠ E si passa dal gancio, non da
	 * `rcp_video_abbandona()`: quello rifiuta le chiavi (§5.2) e ha ragione
	 * finche' la sessione vive — qui non c'e' piu' niente da proteggere, e una
	 * chiave lasciata aperta resterebbe aperta per sempre. */
	if (s->video_aperto && s->g.video_azzera) {
		s->g.video_azzera(s->g.ctx, s->video_stream);
		s->video_aperto = false;
		reg(s, "⚠ il fotogramma %u era ancora aperto alla fine della sessione: "
		       "stream %lld AZZERATO (§6.2), %zu byte su %zu",
		    s->video_suo_numero, (long long)s->video_stream, s->video_scritti,
		    s->video_da_scrivere);
	}
	if (s->attaccata) {
		posto_lascia(s->utente);
		reg(s, "posto LASCIATO da %s via %s (occupati adesso: %d)", s->utente,
		    s->provenienza, posti_occupati());
	}
	/* ⛔ L'accumulo si azzera PRIMA di liberarlo — rilievo R9.8.  Ci e' passata
	 * la `CREDENZIALI`, e su ogni strada che congeda prima di consumare il
	 * messaggio la parola d'ordine in chiaro e' ancora li'.  `free()` non
	 * azzera niente: quei byte finivano nel mucchio liberato, disponibili a
	 * qualunque allocazione successiva di un processo che serve TUTTI gli
	 * utenti della macchina (`SPECIFICHE.md` §5.5). */
	if (s->acc) {
		memset(s->acc, 0, s->acc_cap);
		free(s->acc);
	}
	memset(s, 0, sizeof *s);
	free(s);
}

bool rcp_e_finita(const rcp_sessione *s) { return s && s->stato == S_FINITA; }

/* ⛔⭐ §4.2 — LA SESSIONE E' FINITA PERCHE' LO DICE IL CLIENT, E IL POSTO SI
 * LASCIA ADESSO, NON QUANDO IL TRASPORTO AVRA' FINITO DI SMONTARSI.
 *
 * Il client chiude la sessione WebTransport con una capsula che porta il
 * motivo (§3.1 punto 3).  ⚠ Aspettare la chiusura degli stream per liberare il
 * posto (§8.2 motivo 0x0F) significa tenerlo occupato per tutto il tempo dello
 * smontaggio — e chi si ricollega **subito** si sente rispondere che c'e' gia'
 * una sessione.
 *
 * ⭐ Trovato da B11 il 10 agosto 2026: due casi consecutivi, il secondo
 *    respinto con `GIA_ATTIVA_REMOTA` perche' il primo non aveva ancora finito
 *    di andarsene.  ⛔ Sul banco e' un caso rosso ogni tanto; per chi usa il
 *    prodotto e' «mi dice che sono gia' collegato, e non e' vero».            */
void rcp_chiusa_dal_client(rcp_sessione *s, uint8_t codice)
{
	/* ⚠ Nessuna guardia sullo stato: il posto lo si lascia anche se la
	 *   sessione era gia' finita per altra via — `attaccata` impedisce da
	 *   sola di lasciarlo due volte, ed e' l'unica cosa che conta. */
	if (!s)
		return;
	reg(s, "la pagina ha chiuso la sessione, motivo %#04x: §4.2, la sessione "
	       "e' finita (stato: %s)",
	    codice, NOMI_STATO[s->stato]);
	/* ⛔ §7.3: la terza strada — la pagina se ne va senza passare da
	 * `congeda()`.  Un browser chiuso con la crocetta arriva di qui. */
	rilascia_al_distacco(s, "la pagina ha chiuso la sessione");
	if (s->attaccata) {
		posto_lascia(s->utente);
		s->attaccata = false;
		reg(s, "posto LASCIATO da %s via %s (occupati adesso: %d)", s->utente,
		    s->provenienza, posti_occupati());
	}
	s->stato = S_FINITA;
}

const char *rcp_stato_nome(const rcp_sessione *s)
{
	return s ? NOMI_STATO[s->stato] : "?";
}

const char *rcp_utente(const rcp_sessione *s) { return s ? s->utente : ""; }

/* ⛔⭐ §5.3 — «IL CLIENT E' ANCORA LI'», e lo dice il TRASPORTO, non RCP.
 *
 *     La chiama `trasporto.c` dopo ogni pacchetto che `ngtcp2_conn_read_pkt()`
 *     ha accettato: cioe' **decifrato e autenticato**.  ⛔ Non basta che un
 *     datagram UDP arrivi — chiunque puo' spedirne uno con l'indirizzo di un
 *     altro, e terrebbe occupato il posto di qualcun altro.
 *
 * ⭐ E' l'unico segno di vita che esiste quando l'utente guarda e non tocca, ed
 *    e' quello GIUSTO: nella prova del 16 agosto il filo e' stato tagliato alle
 *    13:33:13 e questo orologio l'ha dichiarato alle 13:33:43 — **trenta
 *    secondi netti**, mentre quello dei byte di RCP l'aveva dichiarato 36
 *    secondi PRIMA, e a torto.
 *
 * ⚠ Nessun messaggio nuovo, nessun battito da aggiungere alla pagina: il
 *   segnale c'era gia' e nessuno lo passava di qui. */
void rcp_segno_di_vita(rcp_sessione *s, uint64_t ora_ms)
{
	if (!s || s->stato == S_FINITA)
		return;
	/* ⛔⭐⭐ E IL BUCO FRA DUE PACCHETTI SI SORVEGLIA, perche' questa
	 *      riparazione POGGIA SU UN'ASSUNZIONE: che fra un pacchetto e l'altro
	 *      passi meno del tetto di §5.3.
	 *
	 * ⛔ Nessuno la garantisce.  I PING del trasporto sono accesi SOLO nella
	 *    finestra delle credenziali, e per una ragione scritta
	 *    (`webtransport.c`, `regola_tienila_viva()`: tenerli sempre accesi
	 *    cambierebbe il significato dei 30 s di §2.2).  ⇒ Durante la sessione
	 *    i pacchetti arrivano perche' QUALCOSA si muove — fotogrammi, cursore,
	 *    riscontri — e su una scena ferma con nessuno che tocca niente non e'
	 *    detto che si muova abbastanza spesso.
	 *
	 * ⚠ Quindi quando il buco supera META' del tetto lo si SCRIVE.  E' l'unico
	 *   modo di vedere ARRIVARE il giorno in cui non basta piu', invece di
	 *   scoprirlo da un utente buttato fuori mentre leggeva — cioe' di non
	 *   rifare, nella cura, il difetto che la cura e' venuta a togliere: una
	 *   protezione che poggia su qualcosa che nessuno puo' guardare.
	 *
	 * ⛔⭐ `[M]` E ALLA PRIMA CORSA QUESTA RIGA HA GIA' PARLATO, 16 agosto 2026:
	 *      sessione ferma per 260 s, il posto ha tenuto — ⛔ ma il buco fra due
	 *      pacchetti e' **15004, 15005, 15002 ms**, cioe' QUINDICI SECONDI
	 *      ESATTI, meta' netta del tetto.
	 *
	 *      ⇒ Il margine e' 2x, ed e' regolarissimo perche' NON E' NOSTRO: e' il
	 *      keep-alive del browser.  ⚠ Un browser diverso, o Chrome che cambia
	 *      quel numero, e i posti ricominciano a cadere.  ⛔ La cura vera —
	 *      mandare i PING anche a sessione attiva — e' una DECISIONE, non una
	 *      riparazione: cambia il significato dei 30 s di §2.2 per la scheda
	 *      CONGELATA, che `SPECIFICHE.md` §5.3 dice doversi staccare.  E' scritta
	 *      in `fasi/05-la-sessione.md` §6-bis e aspetta l'utente. */
	if (ora_ms > s->ultima_vita && ora_ms - s->ultima_vita > SILENZIO / 2)
		reg(s, "⚠ §5.3: fra due pacchetti da %s sono passati %llu ms, e il "
		       "tetto del silenzio e' %u — il margine si sta assottigliando",
		    s->provenienza, (unsigned long long)(ora_ms - s->ultima_vita),
		    (unsigned)SILENZIO);
	s->ultima_vita = ora_ms;
}

/* ⛔ L'accumulo cresce a richiesta fino al tetto di §6.1 (vedi MAX_ACCUMULO).
 *
 * ⚠ E NON si usa `realloc`: quel buffer contiene la `CREDENZIALI` in chiaro, e
 *   `realloc` che sposta lascia la copia vecchia nel mucchio senza azzerarla —
 *   cioe' rimetterebbe il difetto che R9.8 e' venuto a togliere.  Si alloca, si
 *   copia, si AZZERA il vecchio, si libera.
 *
 * Restituisce: 1 fatto · 0 non ci sta (il chiamante congeda) · -1 memoria. */
static int accumula(rcp_sessione *s, const uint8_t *dati, size_t n)
{
	if (s->acc_len + n > MAX_ACCUMULO)
		return 0;
	if (s->acc_len + n > s->acc_cap) {
		size_t nuova = s->acc_cap ? s->acc_cap : 8192u;
		while (nuova < s->acc_len + n)
			nuova *= 2;
		if (nuova > MAX_ACCUMULO)
			nuova = MAX_ACCUMULO;
		uint8_t *p = (uint8_t *)malloc(nuova);
		if (!p)
			return -1;
		if (s->acc) {
			memcpy(p, s->acc, s->acc_len);
			memset(s->acc, 0, s->acc_cap);
			free(s->acc);
		}
		s->acc = p;
		s->acc_cap = nuova;
	}
	memcpy(s->acc + s->acc_len, dati, n);
	s->acc_len += n;
	return 1;
}

/* ⛔⭐ QUANTO OCCUPANO I CAMPI DI QUESTO TIPO — rilievo R9.4, e il difetto era
 *    l'ORDINE, non il controllo.
 *
 * §6.1: «un ricevente che legge una lunghezza incoerente con quel che il tipo
 * prevede DEVE chiudere con `ERRORE_PROTOCOLLO`», e §3: «NON DEVE proseguire».
 * Il controllo `l.i != lung` c'era, ed era scritto giusto — ma stava DOPO
 * `avanti = tratta_*()`, cioe' dopo che il messaggio era stato eseguito per
 * intero, con tutti i suoi effetti sul filo e sullo stato:
 *
 *   un `CIAO` con quattro byte di riempimento in coda — il caso
 *   `lunghezza-in-piu` di B5 — riceveva `ECCOMI` e SOLO POI il congedo;
 *   un `ATTACCA` con un byte in coda prendeva il posto, spediva `SESSIONE`,
 *   scriveva «sessione aperta» e poi congedava: sul filo, in quest'ordine,
 *   `SESSIONE` e `CONGEDO(0x0B)`.  ⛔ Un client che ha ricevuto `SESSIONE` e'
 *   autorizzato da §2.5 ad aprire il suo stream di input, e lo apriva su una
 *   sessione che stava morendo;
 *   una `CREDENZIALI` con un byte in coda faceva interrogare PAM e MUOVEVA i
 *   contatori di §4.4-bis — cioe' proprio la proprieta' che B5 verifica con
 *   `malformati-non-contano`, e la verificava sull'altra meta' dei malformati.
 *
 * ⚠ Questa funzione e' un SECONDO lettore degli stessi campi, e i due si
 *   possono separare: chi cambia un corpo in `tratta_*()` cambia anche qui.  Il
 *   controllo che resta DOPO lo switch non e' un doppione — e' quel che se ne
 *   accorge.
 *
 * ⭐ E restituisce `false` quando il corpo e' piu' CORTO dei campi: quel caso
 *    lo lascia a `tratta_*()`, che sa dire quale campo mancava.  §3.1 punto 1
 *    vuole «che cosa» non si e' capito, e «CIAO senza versione» vale piu' di
 *    «la lunghezza non torna». */
static bool misura_campi(uint16_t tipo, const uint8_t *corpo, uint32_t lung,
                         size_t *quanti)
{
	lettore l = {corpo, lung, 0, false};
	char buf[1025];
	switch (tipo) {
	case T_CIAO: {
		le_u16(&l);
		uint16_t quante = le_u16(&l);
		for (uint16_t k = 0; k < quante && !l.corto; k++) {
			le_str(&l, buf, sizeof buf);
			le_str(&l, buf, sizeof buf);
		}
		break;
	}
	case T_CREDENZIALI:
		le_str(&l, buf, sizeof buf);
		le_str(&l, buf, sizeof buf);
		break;
	case T_ATTACCA:
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		le_str(&l, buf, sizeof buf);
		break;
	case T_BANCO_MARCA:
		le_u32(&l);
		le_u32(&l);
		le_u32(&l);
		break;
	case T_CONGEDO:
		le_u8(&l);
		le_str(&l, buf, sizeof buf);
		break;
	/* §7.1: `RICHIEDI_CHIAVE` ├── u32 ultimo_numero.  Quattro byte, e non uno
	 * di piu': un corpo piu' lungo e' `ERRORE_PROTOCOLLO` come per gli altri
	 * (§6.1), e questa riga e' quel che lo fa succedere. */
	case T_RICHIEDI_CHIAVE:
		le_u32(&l);
		break;
	/* ⭐ §7.6: `TERMINA_SESSIONE` ha il corpo VUOTO — non c'e' niente da dire
	 * oltre al fatto.  ⚠ E un corpo piu' lungo e' `ERRORE_PROTOCOLLO` come per
	 * tutti gli altri (§6.1): non «si ignora quel che avanza». */
	case T_TERMINA_SESSIONE:
		break;
	default:
		/* un tipo che non arriveremo comunque a trattare: decide lo switch, e
		 * la sua riga di registro e' piu' precisa di questa */
		return false;
	}
	if (l.corto)
		return false;
	*quanti = l.i;
	return true;
}

/* Il filo si e' fermato al confine fra due messaggi?  Serve a `giudica_dopo_la_
 * fine()`: se il server ha chiuso mentre un corpo era a meta', i byte che
 * arrivano dopo NON cominciano con un'intestazione, e leggerli come tale
 * significa dare un nome a due byte di corpo. */
static bool a_confine(const rcp_sessione *s)
{
	if (s->acc_len == 0)
		return true;
	if (s->acc_len < 6)
		return false;
	lettore l = {s->acc, s->acc_len, 0, false};
	le_u16(&l);
	uint32_t lung = le_u32(&l);
	return s->acc_len >= 6u + (size_t)lung;
}

/* ⛔⭐ DOPO LA FINE SI GIUDICA SUI MESSAGGI, NON SUI PRIMI SEI BYTE DEL PEZZO —
 *    rilievo R9.15.
 *
 * §4.4 vieta al client UNA cosa: **riprovare**.  §8.1 gliene impone un'altra:
 * chi chiude DEVE mandare `CONGEDO` col motivo.  ⭐ Le due si incontrano quando
 * il server sbaglia DOPO `RESPINTO` — il caso `respinto-poi-congedo` di B11: la
 * pagina vede un messaggio che non doveva arrivare, chiude come impone §3, e il
 * suo `CONGEDO` parte quando per noi la sessione e' gia' finita.
 *
 * ⚠ Il 10 agosto 2026 quel `CONGEDO` di 69 byte e' stato contato come «spedito
 *   dopo la fine», e il rosso e' andato sulla pagina che stava facendo
 *   esattamente quel che §8.1 le impone.  ⛔ La cura di quel giorno leggeva pero'
 *   **i primi due byte di `dati`** e assolveva TUTTO il pezzo: chi scriveva in
 *   una sola volta `CONGEDO` **piu'** una seconda `CREDENZIALI` si portava via
 *   l'assoluzione, e la violazione che B11 esiste per accusare non compariva in
 *   nessuna riga.  Il falso rosso era diventato un falso verde, che e' la stessa
 *   forma — e il documento su cui ci si appoggia, §4.4, parla di MESSAGGI. */
static void giudica_dopo_la_fine(rcp_sessione *s, const uint8_t *dati,
                                 size_t len)
{
	if (!a_confine(s)) {
		reg(s, "⚠ %zu byte arrivati DOPO la fine della sessione da %s, e NON "
		       "sono giudicabili: il filo si era fermato a meta' di un corpo, "
		       "quindi questi byte non cominciano con un'intestazione",
		    len, s->provenienza);
		return;
	}
	size_t off = 0;
	int quanti = 0;
	uint16_t primo = 0;
	while (off + 6 <= len) {
		lettore l = {dati + off, len - off, 0, false};
		uint16_t tipo = le_u16(&l);
		uint32_t lung = le_u32(&l);
		if (lung > MAX_CORPO || (size_t)6 + lung > len - off)
			break; /* l'ultimo e' troncato: `off < len` lo dira' */
		if (quanti == 0)
			primo = tipo;
		quanti++;
		off += 6 + lung;
	}
	if (quanti == 1 && primo == T_CONGEDO && off == len) {
		reg(s, "⭐ CONGEDO di commiato da %s a sessione gia' finita: §8.1 lo "
		       "IMPONE a chi chiude, e §4.4 vieta i tentativi, non i commiati "
		       "— %zu byte, un messaggio solo, e non sono di troppo",
		    s->provenienza, len);
		return;
	}
	if (quanti >= 1 && primo == T_CONGEDO) {
		reg(s, "⛔ da %s un CONGEDO di commiato E POI dell'altro: %d messaggi "
		       "in %zu byte (%zu byte oltre l'ultimo intero).  §8.1 impone il "
		       "commiato, §4.4 vieta tutto il resto",
		    s->provenienza, quanti, len, len - off);
		return;
	}
	reg(s, "⛔ %zu byte arrivati DOPO la fine della sessione da %s: %d messaggi "
	       "interi, il primo di tipo %#06x",
	    len, s->provenienza, quanti, primo);
}

/* Estrae dall'accumulo tutti i messaggi interi che ci sono.  `false` = la
 * sessione e' finita, e il chiamante non deve accumulare altro. */
static bool drena(rcp_sessione *s, uint64_t ora)
{
	for (;;) {
		if (s->acc_len < 6)
			return true;
		lettore intest = {s->acc, s->acc_len, 0, false};
		uint16_t tipo = le_u16(&intest);
		uint32_t lung = le_u32(&intest);
		/* ⛔ La lunghezza si controlla PRIMA di allocare: chi alloca e poi
		 * verifica ha gia' regalato un megabyte a chi sa scrivere sei byte. */
		/* ⛔ E il tetto e' del MESSAGGIO, inquadratura compresa (§6.1 letta
		 * insieme a §5.4) — rilievo B-14: qui `lung` e' il CORPO, e il corpo
		 * piu' lungo ammesso e' `MAX_MESSAGGIO - 6`. */
		if (lung > MAX_CORPO) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "messaggio oltre 1 MiB");
			return false;
		}
		if (s->acc_len < 6u + lung)
			return true; /* il corpo non e' tutto arrivato */

		/* §2.5: sul canale di controllo il byte alto del tipo e' 0x00. */
		if ((tipo >> 8) != 0x00) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "byte alto del tipo non e' controllo");
			return false;
		}
		/* ⛔ E QUI, PRIMA DI QUALUNQUE EFFETTO: la lunghezza dichiarata deve
		 * essere quella dei campi del tipo (§6.1).  Vedi `misura_campi()`. */
		size_t attesa = 0;
		if (misura_campi(tipo, s->acc + 6, lung, &attesa) && attesa != lung) {
			char d[128];
			snprintf(d, sizeof d,
			         "tipo %#06x: la lunghezza dichiara %u byte e i campi che "
			         "il tipo prevede ne occupano %zu",
			         tipo, lung, attesa);
			congeda(s, RCP_ERRORE_PROTOCOLLO, d);
			return false;
		}
		lettore l = {s->acc + 6, lung, 0, false};
		bool avanti = true;
		switch (tipo) {
		case T_CIAO:
			if (s->stato != S_ATTESA_CIAO) {
				congeda(s, RCP_ERRORE_PROTOCOLLO, "CIAO nello stato sbagliato");
				return false;
			}
			avanti = tratta_ciao(s, &l);
			break;
		case T_CREDENZIALI:
			if (s->stato != S_ATTESA_CREDENZIALI) {
				congeda(s, RCP_ERRORE_PROTOCOLLO, "CREDENZIALI nello stato sbagliato");
				return false;
			}
			avanti = tratta_credenziali(s, &l, ora);
			break;
		case T_ATTACCA:
			if (s->stato != S_ATTESA_ATTACCA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO, "ATTACCA nello stato sbagliato");
				return false;
			}
			avanti = tratta_attacca(s, &l);
			break;
		case T_BANCO_MARCA:
			/* §7.5: la marca si dipinge su un fotogramma, e i fotogrammi
			 * cominciano con `SESSIONE`.  Prima, e' un messaggio nello stato
			 * sbagliato come tutti gli altri. */
			if (s->stato != S_ATTIVA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "BANCO_MARCA nello stato sbagliato");
				return false;
			}
			avanti = tratta_banco_marca(s, &l);
			break;
		case T_RICHIEDI_CHIAVE:
			/* ⛔ §5.2: si chiede una chiave perche' c'e' un buco fra i
			 * fotogrammi, e i fotogrammi cominciano con `SESSIONE`.  Prima e'
			 * un messaggio nello stato sbagliato come tutti gli altri (§1, §3).
			 * ⚠ `S_STACCATA` va bene: quella sessione ha spedito `SESSIONE` da
			 *   un pezzo, ha solo lasciato il posto per silenzio (R9.2) — e
			 *   rifiutarle una chiave sarebbe punire il client per un tetto
			 *   del server. */
			if (s->stato != S_ATTIVA && s->stato != S_STACCATA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "RICHIEDI_CHIAVE nello stato sbagliato");
				return false;
			}
			avanti = tratta_richiedi_chiave(s, &l, ora);
			break;
		case T_TERMINA_SESSIONE:
			/*
			 * ⭐⭐ §7.6 — «HO FINITO», ed e' l'altra uscita di
			 *     `DECISIONI.md` §4.1-ter.
			 *
			 * ⛔ SOLO A SESSIONE ATTACCATA: prima dell'`ATTACCA` non c'e'
			 *    nessuna sessione grafica da terminare, e §3 non fa sconti.
			 * ⚠ `S_STACCATA` va bene per la stessa ragione di
			 *   `RICHIEDI_CHIAVE`: quel client la sessione ce l'ha, ha solo
			 *   lasciato il posto per silenzio.
			 */
			if (s->stato != S_ATTIVA && s->stato != S_STACCATA) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "TERMINA_SESSIONE nello stato sbagliato");
				return false;
			}
			reg(s, "⭐ §7.6: %s ha chiesto di USCIRE — la sessione grafica "
			       "finisce e i suoi programmi si chiudono.  ⛔ NON e' un "
			       "distacco: al prossimo attacco ne nascera' una NUOVA",
			    s->utente);
			/*
			 * ⛔⛔ L'ORDINE E' NORMATIVO, e non e' una preferenza: il congedo
			 *     PRIMA, la richiesta di terminare DOPO.  Quando il
			 *     compositore cade il palco cade con lui e il canale non
			 *     serve piu' — un `0x10` spedito dopo e' un motivo che
			 *     esiste e che nessuno riceve, cioe' il rilievo B-7.
			 */
			congeda(s, RCP_SESSIONE_TERMINATA,
			        "l'utente ha chiesto di uscire dalla sessione");
			if (s->g.termina_sessione)
				s->g.termina_sessione(s->g.ctx);
			else
				reg(s, "⚠ nessun gancio «termina_sessione»: il client e' "
				       "stato congedato con 0x10 ma la sessione grafica NON "
				       "e' stata toccata.  ⛔ Le due verita' non combaciano, "
				       "e questa riga e' l'unico posto in cui si vede");
			return false;
		case T_CONGEDO: {
			/* ⛔⭐ QUATTRO COSE IN NOVE RIGHE — rilievo R9.5.
			 *
			 *   1. `lung` non si guardava mai: `le_u8()` su un corpo vuoto
			 *      mette `corto` e restituisce 0, e nessuno leggeva `corto`;
			 *   2. quello zero veniva TAPPATO (`motivo ? motivo : 0x01`): il
			 *      server INVENTAVA `CHIUSO_DALL_UTENTE` per un motivo che il
			 *      client non aveva mandato.  ⛔ Il registro scriveva
			 *      `motivo=0x00` e la sessione si chiudeva con `0x01`: due
			 *      verita' sullo stesso fatto, che e' la forma per cui §3.1
			 *      punto 3 esiste;
			 *   3. il `dettaglio` non si leggeva — ne' come stringa, ne' come
			 *      UTF-8, ne' come lunghezza — ed e' esattamente quel che §8.2
			 *      destina al REGISTRO;
			 *   4. il motivo si rispediva senza convalida dentro il codice di
			 *      chiusura della sessione, dove §3.1 punto 3 vuole «il codice
			 *      del motivo DI §8.2».
			 *
			 * ⛔ E §3.1: «il codice 0 significa chiusura senza motivo e NON
			 *    DEVE essere usato».  Un `CONGEDO(0x00)` e' una violazione del
			 *    client, non un motivo da indovinare — ed e' lo stesso caso che
			 *    B11 pretende dalla PAGINA quando a sbagliare e' il server. */
			uint8_t motivo = le_u8(&l);
			size_t p = l.i;
			char dett[257];
			size_t ld = le_str(&l, dett, sizeof dett);
			if (l.corto) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "CONGEDO senza motivo o senza dettaglio");
				return false;
			}
			/* ⚠ Il dettaglio si convalida sui BYTE ARRIVATI, non sulla copia:
			 *   §7.1 non gli mette un tetto e `le_str` non copia quel che non
			 *   ci sta (vedi il suo commento).  Cosi' anche un dettaglio piu'
			 *   lungo del nostro campo viene giudicato invece che ignorato. */
			if (!utf8_valido((const char *)(l.b + p + 2), ld)) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "il dettaglio del CONGEDO non e' UTF-8 valido (§6.0)");
				return false;
			}
			if (!motivo_di_82(motivo)) {
				char d[96];
				snprintf(d, sizeof d,
				         "CONGEDO con motivo %#04x, che non e' un motivo di "
				         "§8.2 (e il codice 0 §3.1 lo vieta)",
				         motivo);
				congeda(s, RCP_ERRORE_PROTOCOLLO, d);
				return false;
			}
			reg(s, "il client si congeda, motivo=%#04x dettaglio=%s", motivo,
			    ld < sizeof dett ? dett
			                     : "(piu' lungo del campo: non riportato)");
			/* ⛔ §7.3: e questa e' la strada PIU' BATTUTA di tutte quando il
			 * prodotto e' sano — il client che se ne va per bene.  Se il
			 * rilascio stesse solo in `congeda()` mancherebbe proprio qui. */
			rilascia_al_distacco(s, "congedo del client");
			s->stato = S_FINITA;
			/* ⛔⭐ E IL POSTO LASCIATO SI SCRIVE, come negli altri tre punti —
			 * cura della tarda serata dell'11 agosto 2026.
			 *
			 * Questo era l'unico dei quattro luoghi che liberano il posto a NON
			 * chiamare `reg()`: `rcp_libera`, `rcp_pagina_ha_chiuso` e
			 * `rcp_canale_chiuso` lo scrivono tutti.  ⛔ E il buco stava
			 * precisamente sulla strada che §8.1 IMPONE — il client che si
			 * congeda — cioe' la piu' battuta di tutte quando il prodotto e'
			 * sano.
			 *
			 * ⚠ Il posto si liberava davvero: `[M]` 11 agosto 2026, dodici
			 *   sessioni di fila nei registri di `01-p5-ff-*`, e ogni «posto
			 *   PRESO» successivo dice «occupati adesso: 1».  Il difetto non era
			 *   una perdita, era che **l'invariante §8.2 `0x0F` non si poteva
			 *   piu' osservare**: P5 giudica il numero finale di «occupati
			 *   adesso», e su questa strada nessuna riga lo portava. ⇒ Il banco
			 *   avrebbe scritto «IL POSTO NON SI E' LIBERATO» su un server che
			 *   aveva fatto il suo mestiere — un rosso all'imputato sbagliato,
			 *   che e' la settima veste di `LEZIONI.md` §1.9.
			 *
			 * ⛔ E prima della cura del congedo era INVISIBILE: il client non si
			 *    congedava mai, quindi questa riga non veniva mai percorsa e il
			 *    posto se ne andava sempre per il tetto d'inattivita', che la
			 *    sua riga la scrive. */
			if (s->attaccata) {
				posto_lascia(s->utente);
				s->attaccata = false;
				reg(s, "posto LASCIATO da %s via %s (occupati adesso: %d)",
				    s->utente, s->provenienza, posti_occupati());
			}
			/* ⭐ Lo stesso numero che il registro ha appena scritto: una sola
			 * verita' sul fatto, su tutt'e due le strade di §3.1. */
			s->g.chiudi(s->g.ctx, motivo);
			return false;
		}
		case T_ADATTA_TELA: {
			/* ⛔⭐⭐ §7.1 — «il client chiede una tela di un'altra misura».
			 *
			 * ⚠ Fino al 14 agosto 2026 questo tipo cadeva nel `default` e faceva
			 *   **perdere la sessione** a un client conforme, con la riga «la
			 *   fase 1 non lo serve ancora».  ⛔ Ed era una violazione nostra:
			 *   `RCP.md:483` punto 4 dice che una misura fuori limiti si rifiuta
			 *   con `TELA(MISURA_FUORI_LIMITI)` **invece di chiudere**, e la
			 *   ragione e' scritta accanto — «l'utente che trascina male una
			 *   finestra non deve perdere la sessione».
			 *
			 * ⇒ Adesso si risponde sempre, e il client sa **con che cosa
			 *   continuare**: i due campi di `TELA` portano la tela in vigore
			 *   DOPO la risposta, che su un rifiuto e' quella di prima. */
			uint32_t chiesta_l = le_u32(&l);
			uint32_t chiesta_a = le_u32(&l);
			uint32_t buona_l = 0, buona_a = 0;

			if (l.corto) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "ADATTA_TELA corto: §7.1 vuole due u32");
				return false;
			}
			if (!s->sessione_spedita) {
				congeda(s, RCP_ERRORE_PROTOCOLLO,
				        "ADATTA_TELA prima di SESSIONE: §7.1 lo ammette solo a "
				        "sessione aperta");
				return false;
			}
			/* ⛔⭐ E QUI NON SERVE UNA GUARDIA SUL POSTO, e va detto perche' la
			 *     prima stesura di questa cura ce l'aveva messa: sarebbe stata
			 *     **codice morto che sembra vivo**.
			 *
			 * `torna_a_parlare()` gira in cima a `rcp_ricevi()`, prima di
			 * qualunque messaggio: una sessione staccata per silenzio o si
			 * riprende il posto (e allora comanda a pieno diritto) o viene
			 * congedata con §8.2 `0x0F`.  ⇒ Chi arriva fin qui il posto ce l'ha
			 * **sempre**, e un `if` che non puo' essere falso e' peggio di
			 * niente: il giorno in cui quella regola cambiasse, nessuno saprebbe
			 * che questa riga la stava duplicando.
			 * ⚠ La guardia VIVA e' l'altra, in `tela_richiama_il_palco()`: li' la
			 * sessione senza posto ci arriva davvero, perche' i FOTOGRAMMI le
			 * arrivano anche quando tace (banco `04-b31`, caso 18). */
			/* ⛔ Il tetto e la parita' stanno in UN posto solo, e non qui:
			 *    `rcp_misura_ammessa()` (`rcp.h`).  Riscrivere qui la
			 *    stessa regola vorrebbe dire averne due, e il giorno in cui una
			 *    cambia il difetto e' «il server accetta una misura che il
			 *    compositore non regge» — cioe' la sessione di chi ci ospita che
			 *    muore in silenzio. */
			if (!rcp_misura_ammessa(chiesta_l, chiesta_a, &buona_l, &buona_a)) {
				reg(s, "ADATTA_TELA %ux%u RIFIUTATA: fuori dai limiti di §4.5 "
				       "(%ux%u .. %ux%u) — la tela resta %ux%u",
				    chiesta_l, chiesta_a, RCP_TELA_L_MINIMA, RCP_TELA_A_MINIMA,
				    RCP_TELA_L_MASSIMA, RCP_TELA_A_MASSIMA, s->tela_l, s->tela_a);
				manda_tela(s, 2 /* RIFIUTATA */, 2 /* MISURA_FUORI_LIMITI */,
				           s->tela_l, s->tela_a);
				break;
			}
			/* ⛔⛔ E IL TETTO DEL DECODIFICATORE SI RISPETTA ANCHE QUI — §4.5:
			 *     *«la tela concessa DEVE rispettare `video.misura_massima` se il
			 *     client l'ha dichiarata»*.  ⚠ Difetto trovato refutando: questo
			 *     controllo c'era in `ATTACCA` — dove riduce in proporzione, coi
			 *     lati pari, e lo dichiara — e **non** qui.  ⇒ Un client hi-dpi
			 *     che chiedesse la misura della propria finestra in pixel fisici
			 *     poteva far concedere una tela che il suo decodificatore non
			 *     regge, e da li' non si tornava indietro: lo schermo si ferma e
			 *     non riparte.
			 *
			 * ⚠ Si RIDUCE invece di rifiutare, perche' il client non ha sbagliato
			 *   niente — ha chiesto la misura della sua finestra — e `TELA` gli
			 *   dira' che cosa ha ottenuto.  E' la stessa scelta di §4.5 in
			 *   `ATTACCA`, con lo stesso conto. */
			if (s->max_l && (buona_l > s->max_l || buona_a > s->max_a)) {
				uint32_t prima_l = buona_l, prima_a = buona_a;
				uint32_t cl, ca;
				/* Il lato che limita di piu': confronto incrociato, senza
				 * divisioni in virgola mobile. */
				if ((uint64_t)buona_l * s->max_a <= (uint64_t)buona_a * s->max_l) {
					ca = s->max_a;
					cl = (uint32_t)(((uint64_t)buona_l * s->max_a) / buona_a);
				} else {
					cl = s->max_l;
					ca = (uint32_t)(((uint64_t)buona_a * s->max_l) / buona_l);
				}
				/* ⛔ E il risultato ripassa dalla stessa regola: la riduzione
				 *    puo' aver prodotto un dispari o un numero sotto il minimo, e
				 *    riscrivere qui la parita' vorrebbe dire averla in due
				 *    posti. */
				if (!rcp_misura_ammessa(cl, ca, &buona_l, &buona_a)) {
					reg(s, "ADATTA_TELA %ux%u RIFIUTATA: ridotta al "
					       "video.misura_massima (%ux%u) darebbe %ux%u, che §4.5 "
					       "non ammette — la tela resta %ux%u",
					    chiesta_l, chiesta_a, s->max_l, s->max_a, cl, ca,
					    s->tela_l, s->tela_a);
					manda_tela(s, 2 /* RIFIUTATA */, 2 /* MISURA_FUORI_LIMITI */,
					           s->tela_l, s->tela_a);
					break;
				}
				reg(s, "⚠ RIPIEGO DICHIARATO (§4.5): ADATTA_TELA %ux%u supera il "
				       "video.misura_massima di questo client (%ux%u) — ridotta a "
				       "%ux%u, proporzioni tenute, entrambe pari",
				    prima_l, prima_a, s->max_l, s->max_a, buona_l, buona_a);
			}
			/* ⭐⭐ E QUI COMINCIA LA CATENA CHE IL 14 AGOSTO 2026 MANCAVA.
			 *
			 * ⚠ Fino a ieri questo punto rispondeva `COMPOSITORE_INCAPACE`
			 *   NOMINANDO il pezzo mancante — *«manca `figli_ritela()` →
			 *   `cattura_ridimensiona()`»* — ed era vero.  Adesso i due pezzi ci
			 *   sono, e la risposta non e' piu' una riga: e' un giro fino al
			 *   compositore e ritorno.
			 *
			 * ⛔ IL PRIMO CASO E' QUELLO CHE NON DEVE MUOVERE NIENTE: la misura
			 *    chiesta e' gia' quella in vigore.  ⚠ Non e' un caso di scuola —
			 *    e' il piu' frequente di tutti: il client manda la misura della
			 *    sua finestra a ogni ridimensionamento, e chi trascina un bordo
			 *    ne manda venti al secondo.  Girarla al palco vorrebbe dire
			 *    riavviare il flusso per niente, cioe' **perdere un fotogramma a
			 *    ogni richiesta inutile** (`STUDI.md` §kde §8.2-bis).
			 *
			 * ⚠ Ma solo se non c'e' gia' una richiesta in volo: se ce n'e' una, il
			 *   palco sta andando ALTROVE, e questa e' un ripensamento che va
			 *   girato per davvero. */
			if (buona_l == s->tela_l && buona_a == s->tela_a && !s->tela_volo) {
				/* ⛔ Risponde `TELA(ADATTATA)` e NON apre il debito della chiave:
				 *    lo fa la forma «misura che c'era gia'» di
				 *    `rcp_tela_adattata_ora()`, che esiste per questo. */
				rcp_tela_adattata_ora(s, buona_l, buona_a, ora);
				break;
			}

			/* ⛔ NESSUN GANCIO = COMPOSITORE_INCAPACE, ed e' la risposta VERA per
			 *    chi ci ospita senza un palco: i banchi in-processo della fase 1
			 *    e l'innesto di `banchi/01-b3-rcp-innesta.py`.  §7.1: «se il
			 *    compositore non sa ridimensionare, il server DEVE rispondere con
			 *    `TELA(RIFIUTATA, COMPOSITORE_INCAPACE)`, e il client DEVE
			 *    mostrare la voce come spenta.  NON DEVE fingere che sia
			 *    riuscito». */
			if (!s->g.ritela) {
				reg(s, "ADATTA_TELA %ux%u → %ux%u ammessa, ma questo ospite non ha "
				       "un palco da ridimensionare (gancio `ritela` non "
				       "collegato): COMPOSITORE_INCAPACE, e la tela resta %ux%u",
				    chiesta_l, chiesta_a, buona_l, buona_a, s->tela_l, s->tela_a);
				manda_tela(s, 2 /* RIFIUTATA */, 1 /* COMPOSITORE_INCAPACE */,
				           s->tela_l, s->tela_a);
				break;
			}

			/* ⛔⭐ UNA RICHIESTA IN VOLO SI RISPONDE PRIMA DI ACCETTARNE UN'ALTRA
			 *     — §7.1: «l'n-esimo `TELA` risponde all'n-esima `ADATTA_TELA`».
			 *
			 * ⚠ Il client TIENE IL CONTO delle richieste senza risposta (§6.2, e
			 *   ci decide se trattenere un fotogramma o chiudere la sessione).
			 *   Se due `ADATTA_TELA` ricevessero un `TELA` solo, quel conto non
			 *   tornerebbe piu' a zero e il client tratterrebbe fotogrammi per
			 *   sempre — cioe' la sua memoria.  ⛔ Chi trascina un bordo ne manda
			 *   proprio due di fila: non e' un caso raro, e' IL caso. */
			if (s->tela_volo) {
				reg(s, "ADATTA_TELA %ux%u arrivata mentre %ux%u era ancora in volo "
				       "verso il palco: rispondo NON_ORA alla PRIMA (§7.1 vuole un "
				       "TELA per ciascuna) e giro la seconda",
				    buona_l, buona_a, s->tela_volo_l, s->tela_volo_a);
				manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
				           s->tela_a);
				s->tela_volo = false;
			}

			/* ⛔ E il gancio dice se la DOMANDA e' partita, non se la tela e'
			 *    cambiata: la prova arriva con un fotogramma, e la porta qui
			 *    dentro `rcp_tela_concessa()`. */
			if (!s->g.ritela(s->g.ctx, buona_l, buona_a)) {
				reg(s, "⛔ ADATTA_TELA %ux%u → %ux%u: la richiesta NON e' partita "
				       "verso il palco (nessun figlio, o il socket non l'ha "
				       "presa).  NON_ORA, e la tela resta %ux%u",
				    chiesta_l, chiesta_a, buona_l, buona_a, s->tela_l, s->tela_a);
				manda_tela(s, 2 /* RIFIUTATA */, 3 /* NON_ORA */, s->tela_l,
				           s->tela_a);
				break;
			}
			s->tela_volo = true;
			s->tela_volo_l = buona_l;
			s->tela_volo_a = buona_a;
			s->tela_volo_da = ora;
			/* ⛔ E il disaccordo di prima si CHIUDE: da adesso il palco ha una
			 *    richiesta nuova, e datare il fondo su un disaccordo vecchio lo
			 *    farebbe scadere all'indietro. */
			s->tela_disaccordo_da = 0;
			s->tela_disaccordo_attesa = 0;
			reg(s, "⭐ ADATTA_TELA %ux%u → %ux%u GIRATA al palco (`figli_ritela()` "
			       "→ `cattura_ridimensiona()`).  ⚠ Nessun `TELA` adesso: la "
			       "risposta e' il primo fotogramma alla misura nuova, e se non "
			       "arriva entro %u ms si risponde NON_ORA (§7.1)",
			    chiesta_l, chiesta_a, buona_l, buona_a,
			    (unsigned)RCP_TELA_ATTESA_MS);
			break;
		}
		default: {
			/* §7.1 + §3: un tipo sconosciuto sul canale di controllo non si
			 * ignora — la connessione cade.
			 *
			 * ⛔ Ma §3.1 punto 1 chiede di scrivere CHE COSA non si e' capito,
			 * e «sconosciuto» sarebbe falso per meta' dei casi: `ECCOMI`,
			 * `AMMESSO`, `RESPINTO`, `SESSIONE`, `CURSORE_FORMA`, `TELA` e
			 * `BANCO_ESITO` sono tipi CONOSCIUTI che viaggiano nell'altro verso
			 * (§7.1).  Un client che ne manda uno ha un difetto diverso da chi
			 * inventa un tipo, e il registro deve distinguerli.
			 *
			 * ⛔⭐ E I QUATTRO CHE RESTANO NON SONO «SCONOSCIUTI» — rilievo
			 *    R9.7.  §7.1 li numera e li assegna al CLIENT: `0x0008 VISTA`,
			 *    `0x0009 DISPOSIZIONE`, `0x000B ADATTA_TELA`,
			 *    `0x000D RICHIEDI_CHIAVE`.  Scrivere «sconosciuto» su un tipo
			 *    che l'arbitro definisce e' dire il falso nel registro, ed e' lo
			 *    stesso difetto che il capoverso qui sopra dichiara di aver
			 *    corretto per i tipi del server.
			 *
			 * ⭐ E DAL 12 AGOSTO 2026 SONO **TRE**, non quattro: `0x000D
			 *    RICHIEDI_CHIAVE` e' servito insieme al canale video, perche'
			 *    §5.2 obbliga il client a mandarlo appena vede un buco — e
			 *    farlo cadere qui vorrebbe dire chiudere la sessione di un
			 *    client che sta facendo quel che l'arbitro gli impone.  ⛔ Gli
			 *    altri tre restano fuori, e il prezzo resta quello scritto qui
			 *    sotto: `ADATTA_TELA` vuole un compositore che sappia
			 *    ridimensionare, e non e' di questo anello.
			 *
			 * ⚠ SERVIRLI e' un'altra cosa, e non e' di questa fase:
			 *   `fasi/01-filo-nudo.md` dice «niente video, niente audio, niente
			 *   input».  ⛔ Ma il prezzo va detto per intero, perche' non e'
			 *   piccolo: finche' restano fuori, un client conforme che stringe
			 *   la finestra (`VISTA`) o che vede un buco (`RICHIEDI_CHIAVE`,
			 *   §5.2) o che chiede di adattare la tela (`ADATTA_TELA`, a cui
			 *   §7.1 impone un `TELA` con un DEVE) **perde la sessione** — ed e'
			 *   alla lettera il sintomo che il riquadro R1.17 di §7.1 e' stato
			 *   scritto per rendere impossibile.  ⭐ Il registro adesso lo
			 *   NOMINA: chi legge «non ancora servito in fase 1» sa che il
			 *   difetto e' nostro e sa in quale fase sparisce; chi leggeva
			 *   «sconosciuto» andava a cercare un difetto del client. */
			bool del_server = tipo == T_ECCOMI || tipo == T_AMMESSO ||
			                  tipo == T_RESPINTO || tipo == T_SESSIONE ||
			                  tipo == T_CURSORE_FORMA ||
			                  tipo == 0x000E /* TELA */ ||
			                  tipo == T_BANCO_ESITO;
			const char *del_client = NULL;
			switch (tipo) {
			case 0x0008:
				del_client = "VISTA";
				break;
			case 0x0009:
				del_client = "DISPOSIZIONE";
				break;
			/* ⚠ `0x000B ADATTA_TELA` non compare piu' qui: dal 14 agosto 2026 ha
			 *   un caso suo e non arriva mai al `default`.  Tolto invece di
			 *   lasciato «per sicurezza»: un ramo irraggiungibile che nomina un
			 *   tipo servito e' una riga che mente a chi legge. */
			default:
				break;
			}
			char d[160];
			if (del_server)
				snprintf(d, sizeof d, "tipo %#06x: e' del server, non del client",
				         tipo);
			else if (del_client)
				snprintf(d, sizeof d,
				         "tipo %#06x %s: e' del client e §7.1 lo definisce, ma "
				         "la fase 1 non lo serve ancora",
				         tipo, del_client);
			else
				snprintf(d, sizeof d, "tipo %#06x sconosciuto sul controllo",
				         tipo);
			congeda(s, RCP_ERRORE_PROTOCOLLO, d);
			return false;
		}
		}
		if (!avanti)
			return false;
		/* ⛔ §6.0: si avanza della lunghezza DICHIARATA, non di quanto si e'
		 * letto.  ⚠ Il controllo qui non e' un doppione di quello che sta prima
		 * dello switch: quello parla PRIMA degli effetti ed e' il controllo di
		 * §6.1; questo scatta solo se `misura_campi()` e `tratta_*()` si sono
		 * separati, cioe' se qualcuno ha cambiato un corpo in un posto solo. */
		if (l.i != lung) {
			congeda(s, RCP_ERRORE_PROTOCOLLO,
			        "il corpo ha byte in piu' dei campi previsti");
			return false;
		}
		size_t prima = s->acc_len;
		memmove(s->acc, s->acc + 6 + lung, s->acc_len - 6 - lung);
		s->acc_len -= 6 + lung;
		/* ⛔ E LA CODA SI AZZERA — rilievo R9.8.  Il `memmove` faceva scorrere
		 * in giu' il residuo e lasciava dov'erano i byte del messaggio appena
		 * consumato: quelli di una `CREDENZIALI` sono la parola d'ordine in
		 * chiaro, e restavano nella sessione fino alla fine della connessione.
		 * §4.4: «va azzerata appena PAM ha risposto». */
		memset(s->acc + s->acc_len, 0, prima - s->acc_len);
		s->da_quando = ora;
	}
}

/* ⛔⭐ CHI HA TACIUTO TRENTA SECONDI NON E' PIU' ATTACCATO, E QUANDO TORNA A
 *    PARLARE LO DEVE SAPERE — rilievo R9.2.
 *
 *    Il ramo del silenzio di `rcp_tempo()` lasciava il posto e metteva
 *    `attaccata = false`, ma lo stato restava `S_ATTIVA`: da li' in poi il
 *    server aveva DUE sessioni «attiva» per lo stesso utente — quel che I2
 *    vieta — e la prima continuava a essere servita come se niente fosse, senza
 *    aver mai ricevuto un `CONGEDO`, un motivo o un codice di chiusura.  §8.2:
 *    «nessun client attaccato e vivo viene mai spodestato», e quello veniva
 *    spodestato in silenzio.
 *
 * ⭐ Il posto si puo' RIPRENDERE, e non e' una concessione: §8.2 dice che «il
 *    discrimine e' l'orologio del silenzio, non l'intenzione di chi arriva», e
 *    il caso che l'orologio esiste per servire e' il telefono tornato dalla
 *    galleria.  Se nessuno ha occupato il posto, quel client riprende
 *    esattamente da dove era.
 *
 * ⛔ Se invece il posto e' stato preso, il congedo e' `GIA_ATTIVA_REMOTA` e la
 *    frase che il client ne costruira' — «hai gia' una sessione attiva altrove»
 *    — questa volta e' VERA.  ⚠ E resta vero che «chi viene rifiutato e' chi
 *    arriva»: qui chi arriva e' lui, chi c'era e' l'altro.
 *
 * ⛔⭐ ED E' UNA FUNZIONE, dal 14 agosto 2026, perche' adesso i byte del client
 *     entrano da DUE porte — `rcp_ricevi()` e `rcp_ricevi_input()`.  ⚠ Lasciarla
 *     scritta a mano dentro la prima avrebbe voluto dire che chi torna a parlare
 *     **muovendo il mouse** non riprende il posto, e il sintomo sarebbe stato:
 *     il video riparte se scrivi, non se muovi la mano.  Due copie di uno stato
 *     divergono, e questa e' la copia che non si e' fatta.
 *
 * Restituisce `false` se la sessione e' stata congedata. */
static bool torna_a_parlare(rcp_sessione *s)
{
	if (s->stato != S_STACCATA)
		return true;
	if (posto_prendi(s->utente) == POSTO_PRESO) {
		s->attaccata = true;
		s->stato = S_ATTIVA;
		/* ⛔ §7.3: il rilascio del distacco e' gia' avvenuto (il silenzio l'ha
		 * fatto scattare), e questa sessione ricomincia con le mani libere: se
		 * tacesse una seconda volta, il rilascio deve poter riscattare. */
		s->inp_rilasciato = false;
		reg(s, "⭐ posto RIPRESO da %s via %s dopo il silenzio: nessun "
		       "altro lo aveva occupato (occupati adesso: %d)",
		    s->utente, s->provenienza, posti_occupati());
		return true;
	}
	reg(s, "⛔ %s torna a parlare dopo il silenzio, ma il suo posto e' "
	       "di un altro client: §8.2 0x0F, e questa volta e' vero",
	    s->utente);
	congeda(s, RCP_GIA_ATTIVA_REMOTA,
	        "il posto di questa sessione e' stato preso da un altro "
	        "client mentre questa taceva");
	return false;
}

bool rcp_ricevi(rcp_sessione *s, const uint8_t *dati, size_t len, uint64_t ora)
{
	if (s->stato == S_FINITA) {
		/* ⛔ E si SCRIVE.  §4.4 dice che dopo `RESPINTO` il client non deve
		 * riprovare sulla stessa connessione, e §4.2 che dopo la fine della
		 * sessione non si spedisce piu' niente: sono due DEVE del CLIENT, e
		 * l'unico posto da cui si possono osservare e' qui.  ⚠ Senza questa
		 * riga un client che riprova e' indistinguibile da uno che si e'
		 * fermato — B11 misurerebbe il silenzio del server invece del
		 * comportamento della pagina.
		 *
		 * ⛔⭐ MA NON TUTTO QUEL CHE ARRIVA DOPO LA FINE E' UNA VIOLAZIONE, e
		 *    contarlo tutto insieme ha puntato un rosso sull'imputato
		 *    sbagliato — la settima veste di `LEZIONI.md` §1.9.
		 *
		 * §4.4 vieta al client UNA cosa: **riprovare**.  §8.1 gliene impone
		 * un'altra: chi chiude **DEVE** mandare `CONGEDO` col motivo.  ⭐ Le
		 * due si incontrano quando il server sbaglia DOPO `RESPINTO` — il caso
		 * `respinto-poi-congedo` di B11: la pagina vede un messaggio che non
		 * doveva arrivare, chiude come impone §3, e il suo `CONGEDO` parte
		 * quando per noi la sessione e' gia' finita.
		 *
		 * ⚠ Il 10 agosto 2026 quel `CONGEDO` di 69 byte e' stato contato come
		 *   «spedito dopo la fine», e il rosso e' andato sulla pagina che stava
		 *   facendo **esattamente** quel che §8.1 le impone.  ⛔ Il canale di
		 *   controllo non aveva nessun FIN: §4.2 non c'entrava, e la sola
		 *   regola in gioco — §4.4 — parla di tentativi, non di commiati.
		 *
		 * ⭐ Quindi si distingue, e si distingue **sui messaggi**, non sui primi
		 *    sei byte del pezzo: vedi `giudica_dopo_la_fine()`, rilievo R9.15. */
		giudica_dopo_la_fine(s, dati, len);
		return false;
	}
	/* ⭐ L'orologio dell'INATTIVITA' dell'utente si azzera qui, sui byte di RCP
	 *    — e con lui il segno di vita, perche' un byte arrivato e' un pacchetto
	 *    arrivato.  ⚠ La ragione lunga sta sull'altra delle due chiamate, in
	 *    `rcp_ricevi_input()`. */
	s->ultimo_byte = ora;
	s->ultima_vita = ora;

	/* ⚠ La connessione non si chiude per il solo silenzio — quella scelta e'
	 *   dichiarata nel riquadro in cima e non cambia.  Quel che cambia e' che
	 *   lo STATO dice il vero.  Vedi `torna_a_parlare()`, rilievo R9.2. */
	if (!torna_a_parlare(s))
		return false;

	/* ⛔ Si accumula A PEZZI e si drena dopo ciascuno: cosi' il tetto e' quello
	 * di §6.1 e non quello di un buffer, e un pezzo grande non muore perche'
	 * dentro ci stanno piu' messaggi (rilievo R9.13). */
	while (len) {
		size_t spazio = MAX_ACCUMULO - s->acc_len;
		if (spazio == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "troppi byte in attesa di un corpo");
			return false;
		}
		size_t quanti = len < spazio ? len : spazio;
		int esito = accumula(s, dati, quanti);
		if (esito == 0) {
			congeda(s, RCP_ERRORE_PROTOCOLLO, "troppi byte in attesa di un corpo");
			return false;
		}
		if (esito < 0) {
			/* ⚠ §8.2 non ha un motivo che voglia dire «la memoria e' finita»:
			 *   `SESSIONE_NON_SERVIBILE` e' il piu' vicino — «non si puo'
			 *   servire» — e porta il dettaglio nel corpo.  Scelta nostra, e
			 *   dichiarata qui perche' non venga letta come una regola. */
			congeda(s, RCP_SESSIONE_NON_SERVIBILE,
			        "memoria esaurita nell'accumulo del canale di controllo");
			return false;
		}
		dati += quanti;
		len -= quanti;
		if (!drena(s, ora))
			return false;
	}
	return true;
}

/* ⛔ §2.5 — la violazione che NON arriva dal canale di controllo.
 *
 * Chi apre uno stream in piu', o ci mette dentro il canale sbagliato, non ha
 * mandato nessun messaggio di controllo: la violazione la rileva l'OSPITE, che
 * e' l'unico a vedere gli stream.  ⛔ Ma la chiusura deve restare quella di
 * §3.1 — registro, `CONGEDO` sul canale di controllo se e' ancora utilizzabile,
 * e il codice del motivo nella chiusura della sessione — e quelle tre cose le
 * sa fare solo questo modulo.
 *
 * ⚠ E' il **secondo condizionale di §3.1** a rendere il caso interessante: qui
 *   il canale di controllo di solito e' ancora buono, quindi il `CONGEDO`
 *   parte davvero.  Un banco che pretendesse tutt'e tre i punti SEMPRE darebbe
 *   rosso sul codice giusto il giorno in cui non lo fosse (rilievo R3.3).
 *
 * ⛔⭐ E A SESSIONE FINITA NON SI TACE — rilievo R9.16.  Questa funzione passava
 *    tutta e sola per `congeda()`, che se lo stato e' `S_FINITA` esce alla
 *    prima riga: niente registro, niente `CONGEDO`, niente codice di chiusura.
 *    Un client che si congeda regolarmente e POI apre uno stream nel verso
 *    sbagliato (§2.5) non lasciava **nessuna** traccia — e l'ospite, che quello
 *    stream lo ha visto, non ha altro posto dove dirlo.
 *
 * ⚠ Il confronto e' interno a questo file: `rcp_ricevi()` scrive «byte arrivati
 *   DOPO la fine della sessione» proprio perche' «l'unico posto da cui si
 *   possono osservare e' qui».  Per gli STREAM quel posto e' questa funzione. */
/* ⛔⭐ IL CONGEDO CHE VIENE DA FUORI — §8.1, e il caso per cui e' stato scritto
 *     e' `SERVER_IN_CHIUSURA` (§8.2, `0x0C`).  Rilievo B-7, 10 agosto 2026
 *     notte.
 *
 *     `0x0C` era definito in `rcp.h` e **non lo emetteva nessuna riga del
 *     prodotto**: a un `systemctl stop` con una sessione attiva il server
 *     liberava tutto e taceva.  Il client restava ad aspettare i 30 s
 *     dell'inattivita' e mostrava «errore di rete» — cioe' alla lettera il
 *     difetto di `LEZIONI.md` §1.7 che §3.1 esiste per togliere.
 *
 * ⚠ Chi chiude DEVE mandare `CONGEDO` col motivo **e** ripetere il motivo nel
 *   codice della chiusura: le due strade le percorre `congeda()`, ed e' per
 *   questo che questa funzione non fa altro che chiamarla.  ⛔ Il motivo lo
 *   sceglie chi ospita, perche' solo lui sa perche' sta chiudendo. */
void rcp_congeda(rcp_sessione *s, uint8_t motivo, const char *dettaglio)
{
	if (!s || s->stato == S_FINITA)
		return;
	congeda(s, motivo, dettaglio ? dettaglio : "");
}

void rcp_violazione(rcp_sessione *s, const char *dettaglio)
{
	if (!s)
		return;
	if (s->stato == S_FINITA) {
		/* ⛔ §3.1 punto 1 vale lo stesso: si scrive CHE COSA.  I punti 2 e 3
		 * no, ed e' giusto — la sessione e' gia' chiusa col suo motivo, e
		 * mandarne un secondo direbbe due verita' sullo stesso fatto. */
		reg(s, "⛔ violazione rilevata DOPO la fine della sessione da %s: %s "
		       "— la sessione era gia' chiusa, quindi niente CONGEDO e niente "
		       "codice di chiusura (§3.1), ma il registro la nomina",
		    s->provenienza, dettaglio);
		return;
	}
	congeda(s, RCP_ERRORE_PROTOCOLLO, dettaglio);
}

/* ⛔⭐ §4.2 — IL CANALE DI CONTROLLO CHE SI CHIUDE E' LA FINE DELLA SESSIONE,
 * E VALE ANCHE QUANDO A CHIUDERLO E' IL SERVER.
 *
 * Da quell'istante nessun messaggio del client puo' piu' arrivare — §4.2 gli
 * vieta di spedire su qualunque canale — quindi il posto (§8.2 motivo 0x0F)
 * non lo libererebbe piu' NESSUNO fino alla morte della connessione.  E una
 * connessione, un browser, la tiene viva.
 *
 * ⭐ Trovato da B11 il 10 agosto 2026, e solo su Chrome: dopo il caso in cui
 *    il server chiude il canale con un FIN, i tre casi successivi ricevevano
 *    `GIA_ATTIVA_REMOTA`.  Su Firefox no — li' il trasporto chiudeva lo stream
 *    in tempo e `rcp_libera()` arrivava lo stesso.  ⛔ Il difetto viveva nella
 *    differenza fra due motori, e nessun cliente di prova poteva vederlo.
 *
 * ⚠ La sessione non si libera e non si congeda: mandare un `CONGEDO` su un
 *   canale che abbiamo appena chiuso non ha senso, e il motivo — se ce n'era
 *   uno — e' gia' viaggiato nel codice di chiusura (§3.1 punto 3).  Resta viva
 *   perche' e' l'unico punto da cui si osserva un client che spedisce dopo la
 *   fine, che e' il DEVE di §4.2.                                            */
void rcp_canale_chiuso(rcp_sessione *s)
{
	if (!s || s->stato == S_FINITA)
		return;
	reg(s, "il canale di controllo si e' chiuso dal lato del server: "
	       "§4.2, la sessione e' finita (stato: %s)",
	    NOMI_STATO[s->stato]);
	/* ⛔ §7.3: la quarta strada — il canale muore e non passa da `congeda()`. */
	rilascia_al_distacco(s, "il canale di controllo si e' chiuso");
	if (s->attaccata) {
		posto_lascia(s->utente);
		s->attaccata = false;
		reg(s, "posto LASCIATO da %s via %s (occupati adesso: %d)", s->utente,
		    s->provenienza, posti_occupati());
	}
	s->stato = S_FINITA;
}

/* ⭐ L'ESITO DELLA VERIFICA ASINCRONA RIENTRA DA QUI — `DECISIONI.md` §1.10.
 *
 * ⛔ E CI SONO QUATTRO MURI PRIMA DI TOCCARE `cred_buone`, uno per ciascuna
 *    strada per cui un «si'» potrebbe entrare dove non deve (invariante I3):
 *
 *   1. la sessione dev'essere viva e in `attesa-verdetto` — un verdetto che
 *      arriva su una sessione gia' `attiva` non la puo' riaprire;
 *   2. dev'essere STATA CHIESTA (`verdetto_atteso`) — cosi' una pratica
 *      inventata non trova nessuno che l'aspetti;
 *   3. il numero dev'essere il SUO — la pratica e' del processo, non della
 *      sessione, e senza questo confronto la risposta di un utente potrebbe
 *      ammetterne un altro.  ⛔ E' il muro che vale di piu';
 *   4. `verdetto_atteso` si spegne QUI: una seconda risposta per la stessa
 *      pratica non entra, e «ho ricevuto due verdetti» non diventa «vince
 *      l'ultimo».
 *
 * ⚠ E non manda niente sul filo: ci pensa `rcp_tempo()`, quando anche il
 *   secondo fisso di §4.4-bis sara' passato. */
bool rcp_verdetto(rcp_sessione *s, uint64_t pratica, bool ammesso,
                  uint64_t ora)
{
	if (!s || s->stato != S_ATTESA_VERDETTO || !s->verdetto_atteso)
		return false;
	if (s->pratica != pratica)
		return false;

	s->verdetto_atteso = false;
	s->cred_buone = ammesso;
	s->cred_motivo = RCP_CREDENZIALI_ERRATE;
	reg(s, "PAM ha risposto (pratica %llu): %s  ⭐ e il filo non si e' mai "
	       "fermato (DECISIONI.md §1.10)",
	    (unsigned long long)pratica, ammesso ? "ammesso" : "respinto");

	/* ⛔ IL CONTO DI §4.4-bis SI MUOVE QUI, ed e' l'unico posto in cui adesso
	 *    esiste il fatto «un tentativo e' fallito».  ⚠ Portarlo qui e' la sola
	 *    cosa che il ban ha dovuto subire da questa cura: la regola non
	 *    cambia — tre falliti dallo stesso indirizzo in cinque minuti, dodici
	 *    ore — cambia il momento in cui si sa. */
	if (ammesso)
		azzera_falliti(s, s->indirizzo, ora);
	else
		segna_fallito(s, s->indirizzo, ora);
	return true;
}

bool rcp_tempo(rcp_sessione *s, uint64_t ora)
{
	if (s->stato == S_FINITA)
		return false;

	/* ⛔ §4.4-bis: il ritardo fisso vale ANCHE per AMMESSO.  Applicarlo solo
	 * ai rifiuti rimetterebbe il tempismo dall'altra parte, e la distinzione
	 * che §4.4 vieta di scrivere nel motivo si leggerebbe col cronometro. */
	if (s->stato == S_ATTESA_VERDETTO) {
		/* ⛔⭐ ADESSO SI ASPETTANO DUE COSE, E L'ORDINE NON E' GARANTITO —
		 *     `DECISIONI.md` §1.10, 12 agosto 2026.
		 *
		 *     Il secondo fisso di §4.4-bis e la risposta dell'aiutante.  Fino
		 *     a ieri la seconda era gia' arrivata quando questo stato
		 *     cominciava — PAM aveva bloccato il filo — e qui bastava
		 *     guardare l'orologio.
		 *
		 * ⭐ E il tempo di chi si autentica NON cambia: PAM ci mette da 1,0 a
		 *    2,2 s (`[M]` B8), quindi il verdetto arriva quasi sempre DOPO il
		 *    secondo fisso ed e' lui a dettare il ritmo — esattamente come
		 *    prima.  Quel che cambia e' che nel frattempo il filo lavora.
		 *
		 * ⛔ E il secondo fisso resta un PAVIMENTO, non un soffitto: una
		 *    risposta arrivata in 10 ms non fa uscire `AMMESSO` in 10 ms,
		 *    perche' §4.4-bis vuole che il cronometro non distingua quel che
		 *    il motivo non distingue. */
		if (s->verdetto_atteso && ora - s->cred_arrivo > TETTO_VERDETTO) {
			/* ⛔ La rete di sicurezza, e vale NO.  `cred_buone` e' false da
			 *    quando `CREDENZIALI` e' arrivata: qui non si tocca niente,
			 *    si smette di aspettare. */
			s->verdetto_atteso = false;
			s->no_e_nostro = true;
			reg(s, "⛔ nessun verdetto dall'aiutante dopo %llu ms (tetto %d): "
			       "RESPINTO.  ⚠ E' un difetto NOSTRO, non una parola "
			       "sbagliata — e per questo NON conta come tentativo fallito "
			       "di §4.4-bis",
			    (unsigned long long)(ora - s->cred_arrivo), TETTO_VERDETTO);
		}
		if (s->verdetto_atteso)
			return true; /* PAM sta ancora rispondendo, e il filo intanto gira */
		if (ora - s->cred_arrivo < RITARDO_FISSO)
			return true;
		reg(s, "il secondo fisso e' passato (%llu ms)",
		    (unsigned long long)(ora - s->cred_arrivo));
		if (s->cred_buone) {
			manda_messaggio(s, T_AMMESSO, NULL, 0);
			s->stato = S_ATTESA_ATTACCA;
			s->da_quando = ora;
			reg(s, "ammesso utente=%s da=%s", s->utente, s->provenienza);
			return true;
		}
		/* ⛔⭐ E SUL FILO IL MOTIVO E' LO STESSO, ma nel registro no — e' la
		 *     stessa distinzione che `autenticazione.c` fa fra «PAM ha
		 *     rifiutato» e «PAM non ha potuto giudicare».  §4.4 vieta di dire
		 *     al client perche', perche' sarebbe un oracolo; ⛔ ma chi
		 *     diagnostica deve poter distinguere mille parole sbagliate da un
		 *     aiutante morto, o cerchera' nella parola d'ordine per ore. */
		if (s->no_e_nostro)
			reg(s, "⛔ e questo RESPINTO e' NOSTRO, non di PAM: la verifica non "
			       "e' stata fatta.  ⚠ Sul filo il motivo e' lo stesso (§4.4 "
			       "vieta di distinguerli), e il conto di §4.4-bis NON e' stato "
			       "toccato");
		respingi(s, s->cred_motivo);
		return false;
	}

	/* ⛔ Il silenzio: chi tace da trenta secondi non occupa piu' il posto.
	 * ⚠ La connessione resta aperta — vedi il riquadro in cima.
	 *
	 * ⛔⭐ E LO STATO CAMBIA CON IL POSTO — rilievo R9.2.  Qui si lasciava il
	 *    posto e si metteva `attaccata = false`, ma lo stato restava
	 *    `S_ATTIVA`: `rcp_stato_nome()` continuava a rispondere «attiva» — ed
	 *    e' quel che l'ospite interroga — e `s->stato != S_ATTIVA` e' la sola
	 *    guardia di `BANCO_MARCA`.  Dopo che un secondo client fosse entrato,
	 *    il server aveva DUE sessioni «attiva» per lo stesso utente, che e'
	 *    precisamente cio' che I2 vieta.
	 *
	 *    ⚠ Il riquadro in cima dichiara una scelta — lasciare la connessione
	 *      aperta — ed e' difendibile.  ⛔ Ma «non chiudere la connessione» e
	 *      «restare attiva» sono due cose diverse, e la seconda non era
	 *      dichiarata da nessuna parte.  Il ritorno da qui sta in
	 *      `rcp_ricevi()`: il posto si riprende se e' libero. */
	/* ⛔⭐ E SI GUARDA `ultima_vita`, NON `ultimo_byte` — la riparazione del 16
	 *     agosto 2026, e la ragione lunga sta sul campo, in cima al file.
	 *
	 * ⚠ `ultimo_byte` non sparisce: e' l'orologio dell'INATTIVITA' DELL'UTENTE
	 *   (30 minuti, §5.3), che questo modulo non ha ancora e che adesso ha il
	 *   suo campo pronto e giusto.  ⛔ Tenerne uno solo per due mestieri e' il
	 *   difetto che abbiamo appena pagato: non si rifa'. */
	if (s->stato == S_ATTIVA && s->attaccata &&
	    ora - s->ultima_vita > SILENZIO) {
		posto_lascia(s->utente);
		s->attaccata = false;
		s->stato = S_STACCATA;
		reg(s, "STACCATO per silenzio: %llu ms senza un PACCHETTO da %s — e "
		       "l'ultimo byte di RCP e' di %llu ms fa (§5.3: qui conta il "
		       "client che tace, non l'utente che non tocca) "
		       "(posti occupati adesso: %d; stato: %s)",
		    (unsigned long long)(ora - s->ultima_vita), s->provenienza,
		    (unsigned long long)(ora - s->ultimo_byte),
		    posti_occupati(), NOMI_STATO[s->stato]);
		/* ⛔⭐ §7.3 NOMINA IL SILENZIO PER PRIMO fra i tre modi in cui «una
		 *     connessione finisce», ed e' il caso peggiore dei tre: qui il
		 *     client non ha detto niente e non dira' piu' niente — e' il
		 *     telefono morto in galleria — mentre la SESSIONE GRAFICA
		 *     sopravvive (invariante I4).  Un Ctrl premuto un attimo prima
		 *     che la linea cadesse resterebbe premuto sul desktop vero, e
		 *     l'utente lo troverebbe cosi' al riattacco.
		 * ⚠ E la sessione RCP non e' finita: qui si e' solo lasciato il
		 *   posto.  Se torna a parlare, `inp_rilasciato` si riaccende in
		 *   `rcp_ricevi()`/`rcp_ricevi_input()` insieme al posto ripreso. */
		rilascia_al_distacco(s, "silenzio di §5.3");
	}

	/* ⛔⭐ §5.3 — L'INATTIVITA' DELL'UTENTE, il secondo dei tre orologi.
	 *
	 *     «30 minuti senza input ⇒ REMOTIX stacca il client: per rientrare
	 *     servono utente e password.»  ⇒ E' un CONGEDO, non uno stacco per
	 *     silenzio: la connessione si chiude col motivo `0x02`, e la pagina
	 *     torna al modulo d'accesso.
	 *
	 * ⛔ E l'ordine con l'orologio di sopra NON e' indifferente: prima il
	 *    silenzio.  Un client che ha smesso di rispondere sul filo dev'essere
	 *    dichiarato staccato — cosi' chi arriva entra (§8.2) — e non
	 *    congedato per inattivita', che vorrebbe dire «l'utente c'era e non
	 *    toccava niente».  ⚠ Sono due cose diverse e producono due frasi
	 *    diverse per chi legge.
	 *
	 * ⚠ E si guarda `s->attaccata`: una sessione che il posto non ce l'ha non
	 *   ha un utente da dichiarare inattivo.  ⭐ La SESSIONE GRAFICA sopravvive
	 *   comunque (I4): questo congedo stacca il client, non chiude il desktop —
	 *   quello e' il TERZO orologio, ed e' un'altra cosa. */
	if (inattivita_ms && s->stato == S_ATTIVA && s->attaccata &&
	    ora - s->ultimo_byte > inattivita_ms) {
		char d[192];
		snprintf(d, sizeof d,
		         "%llu ms senza input dell'utente (tetto %llu): §5.3, e per "
		         "rientrare servono utente e parola d'ordine",
		         (unsigned long long)(ora - s->ultimo_byte),
		         (unsigned long long)inattivita_ms);
		reg(s, "⭐ §5.3 — INATTIVITA': %s.  ⚠ La sessione grafica RESTA (I4): "
		       "si stacca il client, non si chiude il desktop",
		    d);
		congeda(s, RCP_INATTIVITA, d);
		/* ⛔ `false` come per gli altri tetti: la sessione e' finita, e chi
		 *    chiama non deve continuare a lavorarci sopra. */
		return false;
	}

	/* ⛔ §7.1 — il fondo dell'attesa dell'`ADATTA_TELA`.  ⚠ Sta QUI, e non dove
	 *    arrivano i fotogrammi, per la lezione di `regola_battito` (pagata
	 *    l'11 agosto con B6): una scadenza che scatta solo quando arriva
	 *    qualcosa e' una scadenza che non scatta mai — e il caso che conta e'
	 *    proprio quello in cui non arriva niente. */
	tela_scade(s, ora);

	uint64_t tetto = 0;
	const char *quale = NULL;
	if (s->stato == S_ATTESA_CIAO) {
		tetto = TETTO_CIAO;
		quale = "CIAO";
	} else if (s->stato == S_ATTESA_CREDENZIALI) {
		tetto = TETTO_CREDENZIALI;
		quale = "CREDENZIALI";
	} else if (s->stato == S_ATTESA_ATTACCA) {
		tetto = TETTO_ATTACCA;
		quale = "ATTACCA";
	}
	if (tetto && ora - s->da_quando > tetto) {
		char d[64];
		snprintf(d, sizeof d, "scaduto il tetto per %s", quale);
		congeda(s, RCP_TEMPO_SCADUTO, d);
		return false;
	}
	return true;
}
