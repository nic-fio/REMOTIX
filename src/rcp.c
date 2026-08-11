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
	T_CONGEDO = 0x000C,
	T_BANCO_MARCA = 0x000F,
	T_BANCO_ESITO = 0x0010,
};

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

/* ⛔ L'OROLOGIO DEL SILENZIO — `SPECIFICHE.md` §5.3, `DECISIONI.md` §4.4.
 *
 * Trenta secondi senza un byte DAL CLIENT e il client «si considera staccato»:
 * non occupa piu' il posto, e chi arriva entra.  E' la regola che fa sparire
 * il caso «il telefono e' morto in galleria e ora non posso rientrare».
 *
 * ⭐ E si misura **sui byte di RCP**, non su quelli di QUIC: il trasporto manda
 *    riscontri e battiti per conto suo, e un orologio appoggiato a quelli
 *    direbbe «vivo» di un client che non parla da un'ora.  E' esattamente la
 *    distinzione che il banco di B3 esiste per fare (rilievo R3.19): con
 *    `max_idle_timeout` a 120 secondi, un server SENZA questa nozione
 *    resterebbe verde perche' a chiudere sarebbe QUIC.
 *
 * ⚠ E che cosa succede alla connessione di chi tace, il documento NON lo dice.
 *   Qui si sceglie di **lasciarla aperta** e liberare solo il posto: chiuderla
 *   sarebbe un congedo, e §8.2 non ha un motivo che voglia dire «taci da un
 *   po'».  La scelta e' dichiarata in `fasi/01-filo-nudo.md`, perche' e' un
 *   punto in cui RCP.md ammette due letture. */
#define SILENZIO 30000

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
	uint64_t ultimo_byte; /* l'ultimo byte arrivato DAL CLIENT (§5.3) */
	uint64_t cred_arrivo; /* quando e' arrivato CREDENZIALI */
	bool cred_buone;      /* il verdetto, gia' calcolato ma non ancora detto */
	uint8_t cred_motivo;  /* se non buone */
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
};

/* Dichiarata qui perche' il limitatore dei tentativi, qui sotto, DEVE poter
 * scrivere nel registro: un limite raggiunto in silenzio e' un limite che non
 * esiste (§3, e rilievo R9.1). */
static void reg(rcp_sessione *s, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));

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
	} else {
		bool ok = s->g.verifica && s->g.verifica(s->g.ctx, utente, parola);
		reg(s, "PAM ha risposto: %s", ok ? "ammesso" : "respinto");
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

	uint8_t corpo[128];
	scrittore w = {corpo, sizeof corpo, 0, false};
	sc_byte(&w, 1); /* 1 = NUOVA */
	sc_u32(&w, tl);
	sc_u32(&w, ta);
	sc_str(&w, "sconosciuto"); /* il desktop: in fase 1 non c'e' compositore */
	if (!w.pieno)
		manda_messaggio(s, T_SESSIONE, corpo, w.len);
	reg(s, "sessione aperta utente=%s via=%s tela=%ux%u vista=%ux%u "
	       "disposizione=%s",
	    s->utente, s->provenienza, tl, ta, vl, va, disp);
	s->stato = S_ATTIVA;
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
			s->stato = S_FINITA;
			if (s->attaccata) {
				posto_lascia(s->utente);
				s->attaccata = false;
			}
			/* ⭐ Lo stesso numero che il registro ha appena scritto: una sola
			 * verita' sul fatto, su tutt'e due le strade di §3.1. */
			s->g.chiudi(s->g.ctx, motivo);
			return false;
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
			                  tipo == 0x000A /* CURSORE_FORMA */ ||
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
			case 0x000B:
				del_client = "ADATTA_TELA";
				break;
			case 0x000D:
				del_client = "RICHIEDI_CHIAVE";
				break;
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
	/* ⭐ L'orologio del silenzio si azzera QUI, sui byte di RCP. */
	s->ultimo_byte = ora;

	/* ⛔⭐ CHI HA TACIUTO TRENTA SECONDI NON E' PIU' ATTACCATO, E QUANDO TORNA
	 *    A PARLARE LO DEVE SAPERE — rilievo R9.2.
	 *
	 *    Il ramo del silenzio di `rcp_tempo()` lasciava il posto e metteva
	 *    `attaccata = false`, ma lo stato restava `S_ATTIVA`: da li' in poi il
	 *    server aveva DUE sessioni «attiva» per lo stesso utente — quel che I2
	 *    vieta — e la prima continuava a essere servita come se niente fosse,
	 *    senza aver mai ricevuto un `CONGEDO`, un motivo o un codice di
	 *    chiusura.  §8.2: «nessun client attaccato e vivo viene mai
	 *    spodestato», e quello veniva spodestato in silenzio.
	 *
	 * ⭐ Il posto si puo' RIPRENDERE, e non e' una concessione: §8.2 dice che
	 *    «il discrimine e' l'orologio del silenzio, non l'intenzione di chi
	 *    arriva», e il caso che l'orologio esiste per servire e' il telefono
	 *    tornato dalla galleria.  Se nessuno ha occupato il posto, quel client
	 *    riprende esattamente da dove era.
	 *
	 * ⛔ Se invece il posto e' stato preso, il congedo e' `GIA_ATTIVA_REMOTA` e
	 *    la frase che il client ne costruira' — «hai gia' una sessione attiva
	 *    altrove» — questa volta e' VERA.  ⚠ E resta vero che «chi viene
	 *    rifiutato e' chi arriva»: qui chi arriva e' lui, chi c'era e' l'altro.
	 *
	 * ⚠ La connessione non si chiude per il solo silenzio — quella scelta e'
	 *   dichiarata nel riquadro in cima e non cambia.  Quel che cambia e' che
	 *   lo STATO dice il vero. */
	if (s->stato == S_STACCATA) {
		if (posto_prendi(s->utente) == POSTO_PRESO) {
			s->attaccata = true;
			s->stato = S_ATTIVA;
			reg(s, "⭐ posto RIPRESO da %s via %s dopo il silenzio: nessun "
			       "altro lo aveva occupato (occupati adesso: %d)",
			    s->utente, s->provenienza, posti_occupati());
		} else {
			reg(s, "⛔ %s torna a parlare dopo il silenzio, ma il suo posto e' "
			       "di un altro client: §8.2 0x0F, e questa volta e' vero",
			    s->utente);
			congeda(s, RCP_GIA_ATTIVA_REMOTA,
			        "il posto di questa sessione e' stato preso da un altro "
			        "client mentre questa taceva");
			return false;
		}
	}

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
	if (s->attaccata) {
		posto_lascia(s->utente);
		s->attaccata = false;
		reg(s, "posto LASCIATO da %s via %s (occupati adesso: %d)", s->utente,
		    s->provenienza, posti_occupati());
	}
	s->stato = S_FINITA;
}

bool rcp_tempo(rcp_sessione *s, uint64_t ora)
{
	if (s->stato == S_FINITA)
		return false;

	/* ⛔ §4.4-bis: il ritardo fisso vale ANCHE per AMMESSO.  Applicarlo solo
	 * ai rifiuti rimetterebbe il tempismo dall'altra parte, e la distinzione
	 * che §4.4 vieta di scrivere nel motivo si leggerebbe col cronometro. */
	if (s->stato == S_ATTESA_VERDETTO) {
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
	if (s->stato == S_ATTIVA && s->attaccata &&
	    ora - s->ultimo_byte > SILENZIO) {
		posto_lascia(s->utente);
		s->attaccata = false;
		s->stato = S_STACCATA;
		reg(s, "STACCATO per silenzio: %llu ms senza un byte da %s "
		       "(posti occupati adesso: %d; stato: %s)",
		    (unsigned long long)(ora - s->ultimo_byte), s->provenienza,
		    posti_occupati(), NOMI_STATO[s->stato]);
	}

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
